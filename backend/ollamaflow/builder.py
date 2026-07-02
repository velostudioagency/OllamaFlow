"""
OllamaFlow CLI - Interactive workflow builder: wizard, node config, ASCII diagram, validate.
"""

import json
import re
from typing import Dict, List, Optional, Tuple

from ollamaflow.ui import (
    console, print_success, print_error, print_info, print_warning,
    prompt_choice, prompt_input, prompt_confirm, print_ascii_diagram,
    print_validation_result,
)

# Node type categories for the builder
NODE_CATEGORIES = {
    "Triggers": ["input", "webhook"],
    "AI": ["llm", "guardrails"],
    "Tools": ["tool", "transform", "variable", "custom"],
    "Logic": ["condition", "switch", "loop", "merge", "delay", "subworkflow", "batch"],
    "Memory": ["memory"],
    "Output": ["output", "webhook_output"],
}

# Config prompts per node type: (field_name, label, default, field_type)
NODE_CONFIGS = {
    "input": [
        ("prompt", "Goal / Prompt", "", "string"),
        ("input_type", "Input Type", "text", "select", ["text", "file_upload", "scheduled"]),
        ("file_path", "File Path", "", "string"),
    ],
    "llm": [
        ("model", "Model", "llama3.1:8b", "string"),
        ("system_prompt", "System Prompt", "You are a helpful assistant.", "textarea"),
        ("temperature", "Temperature", "0.7", "number"),
        ("max_tokens", "Max Tokens", "2000", "number"),
        ("provider", "Provider", "ollama", "select", ["ollama", "groq", "openai", "anthropic"]),
    ],
    "tool": [
        ("tool_name", "Tool", "web_search", "select_tool"),
    ],
    "memory": [
        ("namespace", "Namespace", "default", "string"),
        ("memory_type", "Memory Type", "long_term", "select", ["short_term", "long_term"]),
        ("action", "Action", "remember", "select", ["remember", "recall", "search", "clear"]),
        ("search_query", "Search Query", "", "string"),
    ],
    "condition": [
        ("condition", "Condition", "if output contains error", "string"),
    ],
    "loop": [
        ("max_iterations", "Max Iterations", "5", "number"),
        ("stop_condition", "Stop Condition", "", "string"),
    ],
    "transform": [
        ("transform_type", "Transform Type", "trim", "select",
         ["regex_extract", "regex_replace", "substring", "uppercase", "lowercase", "trim", "replace", "json_path", "template"]),
        ("pattern", "Pattern / Path", "", "string"),
        ("replacement", "Replacement", "", "string"),
        ("template", "Template (use {{input}})", "{{input}}", "textarea"),
    ],
    "merge": [
        ("merge_mode", "Merge Mode", "concat", "select",
         ["concat", "newline", "json_merge", "first", "non_empty"]),
        ("separator", "Separator", "\n\n", "string"),
    ],
    "guardrails": [
        ("validation_type", "Validation", "not_empty", "select",
         ["not_empty", "json_valid", "contains", "regex", "max_length", "min_length", "custom"]),
        ("pattern", "Pattern / Required Text", "", "string"),
        ("max_length", "Max/Min Length", "5000", "number"),
        ("retry_on_fail", "Retry on Fail", "false", "select", ["true", "false"]),
    ],
    "variable": [
        ("variable_name", "Variable Name", "my_var", "string"),
        ("variable_value", "Value / Expression", "", "textarea"),
        ("variable_type", "Type", "string", "select", ["string", "number", "boolean", "json"]),
        ("mode", "Mode", "set", "select", ["set", "get", "increment", "append"]),
    ],
    "switch": [
        ("switch_field", "Context Key (blank = use input)", "", "string"),
        ("cases", "Cases (one per line: value: label)", "", "textarea"),
        ("default_case", "Default Label", "default", "string"),
    ],
    "delay": [
        ("delay_seconds", "Delay (seconds)", "5", "number"),
    ],
    "webhook": [
        ("webhook_url", "Webhook URL", "", "string"),
        ("method", "Method", "POST", "select", ["POST", "GET", "PUT"]),
        ("auth_token", "Auth Token (optional)", "", "string"),
    ],
    "webhook_output": [
        ("webhook_url", "Webhook URL", "", "string"),
        ("method", "Method", "POST", "select", ["POST", "GET", "PUT", "PATCH"]),
        ("content_type", "Content Type", "application/json", "select",
         ["application/json", "text/plain"]),
        ("retry_count", "Retry Count", "3", "number"),
    ],
    "subworkflow": [
        ("subworkflow_json", "Sub-Workflow JSON", "", "textarea"),
        ("pass_input", "Pass Current Input", "true", "select", ["true", "false"]),
    ],
    "batch": [
        ("subworkflow_json", "Sub-Workflow JSON", "", "textarea"),
        ("batch_mode", "Split Mode", "split_newline", "select",
         ["split_newline", "split_comma", "json_array"]),
    ],
    "custom": [
        ("custom_code", "Python Code", "def process(input, context):\n    return input", "textarea"),
        ("handler_name", "Handler Function", "process", "string"),
    ],
    "output": [],
}


def get_all_node_types():
    """Return flat list of all node type names."""
    types = []
    for cats in NODE_CATEGORIES.values():
        types.extend(cats)
    return types


def generate_node_id(node_type: str, existing_ids: List[str]) -> str:
    """Generate a unique node ID like 'llm_1', 'tool_2'."""
    counter = 1
    while f"{node_type}_{counter}" in existing_ids:
        counter += 1
    return f"{node_type}_{counter}"


def prompt_node_type() -> Optional[str]:
    """Prompt user to select a node type. Returns type name or None to cancel."""
    console.print("\n  [bold]Node type?[/]")
    idx = 1
    type_map = {}
    for cat, types in NODE_CATEGORIES.items():
        console.print(f"    [dim]{cat}:[/]", end="")
        parts = []
        for t in types:
            parts.append(f" {idx}. {t}")
            type_map[str(idx)] = t
            idx += 1
        console.print("  ".join(parts))

    choice = prompt_input("  Type (number or name)", allow_empty=True)
    if not choice:
        return None
    if choice in type_map:
        return type_map[choice]
    # Try matching by name
    for t in get_all_node_types():
        if choice.lower() == t:
            return t
    print_error(f"Unknown node type: {choice}")
    return None


def configure_node(node_type: str, available_tools: List[str] = None) -> Dict:
    """Interactively configure a node. Returns config dict."""
    config = {}
    prompts = NODE_CONFIGS.get(node_type, [])

    if not prompts:
        return config

    console.print(f"\n  [bold]Configure '[cyan]{node_type}[/]' node:[/]")
    existing_ids = []

    for prompt_def in prompts:
        field_name = prompt_def[0]
        label = prompt_def[1]
        default = prompt_def[2]
        field_type = prompt_def[3]

        if field_type == "select" and len(prompt_def) > 4:
            options = prompt_def[4]
            value = prompt_choice(f"    {label}", options)
            if value is None:
                value = default
        elif field_type == "select_tool":
            if available_tools:
                tool_names = [t.get("name", "") if isinstance(t, dict) else str(t) for t in available_tools]
                value = prompt_choice(f"    {label}", tool_names)
            else:
                value = prompt_input(f"    {label}", default=default)
        elif field_type == "textarea":
            console.print(f"    [dim]{label}[/] [dim](enter text, empty line to finish):[/]")
            lines = []
            while True:
                try:
                    line = console.input("    > ")
                    if not line and lines:
                        break
                    lines.append(line)
                except (EOFError, KeyboardInterrupt):
                    break
            value = "\n".join(lines) if lines else default
        else:
            value = prompt_input(f"    {label}", default=default)

        if value is None:
            value = default

        # Type conversion
        if field_type == "number":
            try:
                value = int(value)
            except ValueError:
                try:
                    value = float(value)
                except ValueError:
                    pass
        elif field_type == "select" and value in ("true", "false"):
            value = value == "true"

        config[field_name] = value

    return config


def build_workflow_interactive(existing_workflow: Dict = None, available_tools: List[str] = None) -> Optional[Dict]:
    """Interactive workflow builder. Returns workflow dict or None if cancelled."""
    nodes = []
    edges = []
    existing_ids = []

    if existing_workflow:
        nodes = list(existing_workflow.get("nodes", []))
        edges = list(existing_workflow.get("edges", []))
        existing_ids = [n["id"] for n in nodes]
        if nodes:
            console.print(f"\n  [dim]Starting with {len(nodes)} existing node(s)[/]")

    step = len(nodes) + 1

    while True:
        console.print(f"\n  [bold]Node {step}[/] — What type?")
        node_type = prompt_node_type()

        if node_type is None:
            if not nodes:
                print_warning("No nodes created. Discarding.")
                return None
            break

        # Generate ID
        node_id = generate_node_id(node_type, existing_ids)
        existing_ids.append(node_id)

        # Configure
        config = configure_node(node_type, available_tools)

        # Create node
        node = {
            "id": node_id,
            "type": node_type,
            "config": config,
        }
        nodes.append(node)
        print_success(f"Added node [cyan]{node_id}[/]")

        step += 1

        # Prompt to connect
        if len(nodes) > 1:
            # Show available source nodes (not output-only)
            source_nodes = [n for n in nodes[:-1] if n["type"] not in ("output", "webhook_output")]
            target_node = nodes[-1]

            if source_nodes and target_node["type"] not in ("input", "webhook"):
                console.print()
                # Auto-connect suggestion
                last_source = source_nodes[-1]
                connect = prompt_confirm(
                    f"  Connect [cyan]{last_source['id']}[/] → [cyan]{target_node['id']}[/]?",
                    default=True,
                )
                if connect:
                    edges.append({"source": last_source["id"], "target": target_node["id"]})
                    print_success(f"Connected {last_source['id']} → {target_node['id']}")

        # Continue?
        console.print()
        continue_adding = prompt_confirm("  Add another node?", default=False)
        if not continue_adding:
            break

    # Build workflow dict
    workflow = {
        "nodes": nodes,
        "edges": edges,
    }

    return workflow


def edit_workflow_interactive(workflow: Dict, available_tools: List[str] = None) -> Optional[Dict]:
    """Interactively edit an existing workflow. Returns updated workflow or None."""
    nodes = list(workflow.get("nodes", []))
    edges = list(workflow.get("edges", []))

    while True:
        console.print(f"\n  [bold]Editing:[/] {len(nodes)} nodes, {len(edges)} edges\n")
        actions = ["add", "remove", "connect", "disconnect", "rename", "done"]
        console.print("    [dim]Actions:[/]")
        for a in actions:
            console.print(f"      [cyan]{a}[/]")

        action = prompt_input("  Action", allow_empty=True)
        if not action or action == "done":
            break

        if action == "add":
            node_type = prompt_node_type()
            if node_type is None:
                continue
            node_id = generate_node_id(node_type, [n["id"] for n in nodes])
            config = configure_node(node_type, available_tools)
            node = {"id": node_id, "type": node_type, "config": config}
            nodes.append(node)
            print_success(f"Added [cyan]{node_id}[/]")

            # Connect?
            source_nodes = [n for n in nodes[:-1] if n["type"] not in ("output", "webhook_output")]
            if source_nodes and node_type not in ("input", "webhook"):
                last = source_nodes[-1]
                if prompt_confirm(f"  Connect [cyan]{last['id']}[/] → [cyan]{node_id}[/]?", default=True):
                    edges.append({"source": last["id"], "target": node_id})

        elif action == "remove":
            node_ids = [n["id"] for n in nodes]
            if not node_ids:
                print_warning("No nodes to remove.")
                continue
            target = prompt_choice("  Remove node", node_ids)
            if target:
                nodes = [n for n in nodes if n["id"] != target]
                edges = [e for e in edges if e["source"] != target and e["target"] != target]
                print_success(f"Removed [cyan]{target}[/]")

        elif action == "connect":
            node_ids = [n["id"] for n in nodes]
            if len(node_ids) < 2:
                print_warning("Need at least 2 nodes to connect.")
                continue
            src = prompt_choice("  Source node", node_ids)
            tgt = prompt_choice("  Target node", node_ids)
            if src and tgt and src != tgt:
                edges.append({"source": src, "target": tgt})
                print_success(f"Connected {src} → {tgt}")
            elif src == tgt:
                print_error("Cannot connect a node to itself.")

        elif action == "disconnect":
            if not edges:
                print_warning("No connections to remove.")
                continue
            edge_strs = [f"{e['source']} → {e['target']}" for e in edges]
            choice = prompt_choice("  Disconnect", edge_strs)
            if choice:
                parts = choice.split(" → ")
                if len(parts) == 2:
                    edges = [e for e in edges if not (e["source"] == parts[0] and e["target"] == parts[1])]
                    print_success(f"Disconnected {choice}")

        elif action == "rename":
            node_ids = [n["id"] for n in nodes]
            if not node_ids:
                continue
            old = prompt_choice("  Rename node", node_ids)
            if old:
                new_name = prompt_input("  New ID", default=old)
                if new_name and new_name != old:
                    for n in nodes:
                        if n["id"] == old:
                            n["id"] = new_name
                    for e in edges:
                        if e["source"] == old:
                            e["source"] = new_name
                        if e["target"] == old:
                            e["target"] = new_name
                    print_success(f"Renamed {old} → {new_name}")

    return {"nodes": nodes, "edges": edges}


def validate_workflow(workflow: Dict) -> List[Tuple[bool, str]]:
    """Validate a workflow. Returns list of (passed, message) tuples."""
    results = []
    nodes = workflow.get("nodes", [])
    edges = workflow.get("edges", [])

    if not nodes:
        results.append((False, "Workflow has no nodes"))
        return results

    node_ids = {n["id"] for n in nodes}
    node_types = {n["type"] for n in nodes}

    # Check all nodes have valid types
    valid_types = set(get_all_node_types())
    invalid = [n for n in nodes if n["type"] not in valid_types]
    if invalid:
        results.append((False, f"Invalid node types: {', '.join(n['type'] for n in invalid)}"))
    else:
        results.append((True, "All nodes have valid types"))

    # Check for orphan nodes
    has_incoming = {e["target"] for e in edges}
    has_outgoing = {e["source"] for e in edges}
    entry_nodes = [n for n in nodes if n["id"] not in has_incoming and n["type"] not in ("webhook",)]
    orphans = [n for n in nodes if n["id"] not in has_incoming and n["id"] not in has_outgoing and len(nodes) > 1]

    if orphans and len(nodes) > 1:
        results.append((False, f"Orphan nodes (not connected): {', '.join(n['id'] for n in orphans)}"))
    else:
        results.append((True, "No orphan nodes"))

    # Check edges connect valid nodes
    bad_edges = [e for e in edges if e["source"] not in node_ids or e["target"] not in node_ids]
    if bad_edges:
        results.append((False, f"{len(bad_edges)} edge(s) connect invalid nodes"))
    else:
        results.append((True, "All edges connect valid nodes"))

    # Check for input and output nodes
    has_input = "input" in node_types or "webhook" in node_types
    has_output = "output" in node_types or "webhook_output" in node_types
    if has_input and has_output:
        results.append((True, "Workflow has at least one input and output"))
    elif not has_input:
        results.append((False, "No input node found"))
    else:
        results.append((False, "No output node — result won't be captured"))

    # Check for nodes with no outgoing edges (except output types)
    for n in nodes:
        if n["type"] not in ("output", "webhook_output") and n["id"] not in has_outgoing:
            results.append((False, f"Node '{n['id']}' has no outgoing edges (not connected to output)"))

    # Check for cycles (simple DFS)
    adj = {}
    for e in edges:
        adj.setdefault(e["source"], []).append(e["target"])

    def has_cycle_dfs(node_id, visited, stack):
        visited.add(node_id)
        stack.add(node_id)
        for neighbor in adj.get(node_id, []):
            if neighbor not in visited:
                if has_cycle_dfs(neighbor, visited, stack):
                    return True
            elif neighbor in stack:
                return True
        stack.discard(node_id)
        return False

    visited = set()
    cycle_found = False
    for n in nodes:
        if n["id"] not in visited:
            if has_cycle_dfs(n["id"], visited, set()):
                cycle_found = True
                break

    if cycle_found:
        results.append((False, "Cycle detected in workflow"))
    else:
        results.append((True, "No cycles detected"))

    return results
