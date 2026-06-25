import json
import time
import asyncio
from typing import Any, Dict, List, Optional, Callable, Awaitable
from tool_library import execute_tool, TOOL_DEFINITIONS
from memory_manager import memory_manager


class NodeResult:
    def __init__(self, output: str, status: str = "success", error: str = ""):
        self.output = output
        self.status = status
        self.error = error


async def handle_input(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    prompt = config.get("prompt", "")
    input_type = config.get("input_type", "text")
    if input_type == "file_upload" and config.get("file_path"):
        from tool_library import read_file
        content = read_file(config["file_path"])
        prompt = f"File content:\n\n{content}\n\nUser goal: {prompt}"
    context["current_input"] = prompt
    return NodeResult(output=prompt)


async def handle_llm(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    model = config.get("model", "llama3.1:8b")
    system_prompt = config.get("system_prompt", "You are a helpful assistant.")
    temperature = config.get("temperature", 0.7)
    max_tokens = config.get("max_tokens", 2000)
    user_input = context.get("current_input", "")
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        llm = ChatOllama(
            model=model,
            temperature=temperature,
            num_predict=max_tokens
        )
        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
        response = await asyncio.to_thread(llm.invoke, messages)
        output = response.content
        context["current_input"] = output
        return NodeResult(output=output)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"LLM error: {str(e)}")


async def handle_tool(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    tool_name = config.get("tool_name", "web_search")
    tool_params = config.get("params", {})
    if isinstance(tool_params, str):
        try:
            tool_params = json.loads(tool_params)
        except Exception:
            tool_params = {}
    if not tool_params:
        tool_params = {}
    current_input = context.get("current_input", "")
    if tool_name in ["web_search"] and "query" not in tool_params:
        tool_params["query"] = current_input
    elif tool_name in ["read_file"] and "file_path" not in tool_params:
        tool_params["file_path"] = current_input
    elif tool_name in ["write_file"] and "content" not in tool_params:
        tool_params["content"] = current_input
    elif tool_name in ["calculate"] and "expression" not in tool_params:
        tool_params["expression"] = current_input
    elif tool_name in ["run_code"] and "code" not in tool_params:
        tool_params["code"] = current_input
    if tool_name == "http_request":
        if "url" not in tool_params and current_input:
            tool_params["url"] = current_input
    if tool_name == "send_email":
        for key in ["to", "subject", "body"]:
            if key not in tool_params or not tool_params[key]:
                tool_params[key] = current_input if key == "body" else ""
    result = execute_tool(tool_name, tool_params)
    context["current_input"] = result
    return NodeResult(output=result)


async def handle_memory(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    namespace = config.get("namespace", "default")
    action = config.get("action", "remember")
    memory_type = config.get("memory_type", "long_term")
    current_input = context.get("current_input", "")
    try:
        if action == "remember":
            result = memory_manager.save(namespace, current_input, memory_type)
        elif action == "recall":
            result = memory_manager.recall(namespace, memory_type)
        elif action == "search":
            query = config.get("search_query", current_input)
            if memory_type == "long_term":
                result = memory_manager.search_long_term(namespace, query)
            else:
                result = memory_manager.recall_short_term(namespace)
        elif action == "clear":
            result = memory_manager.clear(namespace)
        else:
            result = f"Unknown memory action: {action}"
        context["current_input"] = result
        return NodeResult(output=result)
    except Exception as e:
        return NodeResult(output="", status="error", error=f"Memory error: {str(e)}")


async def handle_condition(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    condition = config.get("condition", "")
    current_input = context.get("current_input", "")
    try:
        condition_lower = condition.lower()
        input_lower = current_input.lower()
        if "contains" in condition_lower:
            parts = condition_lower.split("contains")
            if len(parts) == 2:
                check_text = parts[1].strip().strip('"').strip("'")
                result = check_text in input_lower
            else:
                result = bool(current_input.strip())
        elif "equals" in condition_lower:
            parts = condition_lower.split("equals")
            if len(parts) == 2:
                check_text = parts[1].strip().strip('"').strip("'")
                result = check_text in input_lower
            else:
                result = bool(current_input.strip())
        elif "not empty" in condition_lower or "has content" in condition_lower:
            result = bool(current_input.strip())
        elif "empty" in condition_lower:
            result = not bool(current_input.strip())
        elif "error" in condition_lower:
            result = "error" in input_lower or "Error" in current_input
        elif "number" in condition_lower:
            import re
            result = bool(re.search(r'\d', current_input))
        else:
            try:
                safe_dict = {"input": current_input}
                result = bool(eval(condition, {"__builtins__": {}}, safe_dict))
            except Exception:
                result = bool(current_input.strip())
        context["condition_result"] = result
        branch = "true" if result else "false"
        output = f"Condition '{condition}' evaluated to {result} (branch: {branch})"
        context["branch"] = branch
        return NodeResult(output=output)
    except Exception as e:
        context["branch"] = "false"
        return NodeResult(output="", status="error", error=f"Condition error: {str(e)}")


async def handle_loop(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    max_iterations = config.get("max_iterations", 5)
    stop_condition = config.get("stop_condition", "")
    current_input = context.get("current_input", "")
    iterations = 0
    output = current_input
    for i in range(max_iterations):
        iterations = i + 1
        if stop_condition:
            try:
                safe_dict = {"input": output, "iteration": i}
                should_stop = bool(eval(stop_condition, {"__builtins__": {}}, safe_dict))
                if should_stop:
                    break
            except Exception:
                pass
        context["current_input"] = output
        context["loop_iteration"] = i
    result = f"Loop completed: {iterations} iterations. Last output: {output[:500]}"
    context["current_input"] = output
    return NodeResult(output=result)


def _parse_action_params(action_line: str) -> Dict:
    """Parse parameters from action lines like tool_name(key1='val1', key2='val2')"""
    params = {}
    try:
        paren_start = action_line.index("(")
        paren_end = action_line.rindex(")")
        args_str = action_line[paren_start + 1:paren_end].strip()
        if not args_str:
            return params
        import re
        pattern = r"(\w+)\s*=\s*(?:'([^']*)'|\"([^\"]*)\"|(\S+))"
        matches = re.findall(pattern, args_str)
        for key, single_q, double_q, unquoted in matches:
            value = single_q or double_q or unquoted
            if value.lower() == "true":
                value = True
            elif value.lower() == "false":
                value = False
            else:
                try:
                    value = int(value)
                except ValueError:
                    try:
                        value = float(value)
                    except ValueError:
                        pass
            params[key] = value
    except (ValueError, AttributeError):
        pass
    return params


def _fix_param_names(tool_name: str, params: Dict) -> Dict:
    """Map generic/wrong param names to correct ones based on tool definition."""
    if tool_name not in TOOL_DEFINITIONS:
        return params
    tool_params = TOOL_DEFINITIONS[tool_name]["params"]
    if not tool_params:
        return params
    generic_names = ["param1", "param2", "param3", "arg1", "arg2", "arg3",
                     "argument1", "argument2", "input", "value", "data"]
    fixed = {}
    param_index = 0
    for key, value in params.items():
        if key in [p["name"] for p in tool_params]:
            fixed[key] = value
        elif key in generic_names and param_index < len(tool_params):
            correct_name = tool_params[param_index]["name"]
            fixed[correct_name] = value
            param_index += 1
        else:
            fixed[key] = value
            param_index += 1
    return fixed


async def handle_agent(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    model = config.get("model", "llama3.1:8b")
    tools_list = config.get("tools", [])
    system_prompt = config.get("system_prompt", "You are a helpful AI agent.")
    max_steps = config.get("max_steps", 10)
    use_memory = config.get("memory", False)
    user_input = context.get("current_input", "")
    agent_context = f"User request: {user_input}\n\n"
    agent_context += "Available tools (use EXACT parameter names as shown):\n"
    for tool_name in tools_list:
        if tool_name in TOOL_DEFINITIONS:
            tool_def = TOOL_DEFINITIONS[tool_name]
            param_parts = []
            for p in tool_def["params"]:
                req = "required" if p["required"] else "optional"
                param_parts.append(f"{p['name']} ({req})")
            agent_context += f"- {tool_name}: {tool_def['description']}\n"
            agent_context += f"  Parameters: {', '.join(param_parts)}\n"
    agent_context += f"\nYou have up to {max_steps} steps to complete the task."
    agent_context += "\nIMPORTANT: Use the EXACT parameter names listed above."
    agent_context += "\nExamples:"
    agent_context += "\n  ACTION: web_search(query='search terms here')"
    agent_context += "\n  ACTION: read_file(file_path='path/to/file.txt')"
    agent_context += "\n  ACTION: calculate(expression='2 + 2')"
    agent_context += "\n  ACTION: get_datetime()"
    agent_context += "\nWhen done, respond with: ANSWER: <your final answer>"
    accumulated_output = []
    try:
        from langchain_ollama import ChatOllama
        from langchain_core.messages import HumanMessage, SystemMessage
        llm = ChatOllama(model=model, temperature=0.7)
        messages = [
            SystemMessage(content=system_prompt + "\n\n" + agent_context),
            HumanMessage(content=user_input)
        ]
        for step in range(max_steps):
            response = await asyncio.to_thread(llm.invoke, messages)
            content = response.content
            if "ACTION:" in content:
                action_line = content.split("ACTION:")[-1].split("\n")[0].strip()
                tool_name = action_line.split("(")[0].strip()
                params = _parse_action_params(action_line)
                if tool_name in TOOL_DEFINITIONS:
                    params = _fix_param_names(tool_name, params)
                    tool_result = await asyncio.to_thread(execute_tool, tool_name, params)
                    accumulated_output.append(f"[Step {step+1}] Used {tool_name}: {tool_result[:500]}")
                    messages.append(HumanMessage(content=f"Tool result: {tool_result[:2000]}"))
                else:
                    accumulated_output.append(f"[Step {step+1}] Unknown tool: {tool_name}")
                    messages.append(HumanMessage(content=f"Error: Tool '{tool_name}' not found. Available: {', '.join(tools_list)}"))
            elif "ANSWER:" in content:
                answer = content.split("ANSWER:")[-1].strip()
                accumulated_output.append(f"[Final Answer] {answer}")
                if use_memory:
                    memory_manager.save("agent_session", answer, "short_term")
                context["current_input"] = answer
                return NodeResult(output="\n".join(accumulated_output))
            else:
                accumulated_output.append(f"[Step {step+1}] {content[:500]}")
                messages.append(HumanMessage(content="Please continue using ACTION: tool_name() or ANSWER: final answer"))
        final_output = "\n".join(accumulated_output)
        context["current_input"] = final_output
        return NodeResult(output=final_output)
    except Exception as e:
        error_output = f"Agent error: {str(e)}\n\nAccumulated steps:\n" + "\n".join(accumulated_output)
        return NodeResult(output=error_output, status="error", error=str(e))


async def handle_output(node: Dict, context: Dict) -> NodeResult:
    config = node.get("config", {})
    current_input = context.get("current_input", "")
    context["final_output"] = current_input
    return NodeResult(output=current_input)


NODE_HANDLERS = {
    "input": handle_input,
    "llm": handle_llm,
    "tool": handle_tool,
    "memory": handle_memory,
    "condition": handle_condition,
    "loop": handle_loop,
    "agent": handle_agent,
    "output": handle_output
}


NODE_TYPES = {
    "input": {
        "type": "input",
        "label": "Input Node",
        "color": "#3B82F6",
        "category": "trigger",
        "icon": "📥",
        "description": "Starting point of the workflow. Provides the initial input/goal.",
        "config_schema": {
            "prompt": {"type": "string", "label": "Goal / Prompt", "default": ""},
            "input_type": {"type": "select", "label": "Input Type",
                          "options": ["text", "file_upload", "scheduled"],
                          "default": "text"},
            "file_path": {"type": "string", "label": "File Path", "default": ""}
        },
        "inputs": 0,
        "outputs": 1
    },
    "llm": {
        "type": "llm",
        "label": "LLM Node",
        "color": "#8B5CF6",
        "category": "ai",
        "icon": "🧠",
        "description": "AI brain node. Sends input to an Ollama LLM and returns the response.",
        "config_schema": {
            "model": {"type": "string", "label": "Model", "default": "llama3.1:8b"},
            "system_prompt": {"type": "textarea", "label": "System Prompt",
                             "default": "You are a helpful assistant."},
            "temperature": {"type": "slider", "label": "Temperature", "min": 0, "max": 1,
                           "step": 0.1, "default": 0.7},
            "max_tokens": {"type": "slider", "label": "Max Tokens", "min": 100, "max": 4000,
                          "step": 100, "default": 2000}
        },
        "inputs": 1,
        "outputs": 1
    },
    "tool": {
        "type": "tool",
        "label": "Tool Node",
        "color": "#F97316",
        "category": "tools",
        "icon": "🛠️",
        "description": "Gives the agent an ability/action like web search, file I/O, or code execution.",
        "config_schema": {
            "tool_name": {"type": "select", "label": "Tool",
                         "options": list(TOOL_DEFINITIONS.keys()),
                         "default": "web_search"}
        },
        "inputs": 1,
        "outputs": 1
    },
    "memory": {
        "type": "memory",
        "label": "Memory Node",
        "color": "#22C55E",
        "category": "memory",
        "icon": "💾",
        "description": "Gives the agent memory capabilities - short-term or long-term.",
        "config_schema": {
            "namespace": {"type": "string", "label": "Namespace", "default": "default"},
            "memory_type": {"type": "select", "label": "Memory Type",
                           "options": ["short_term", "long_term"],
                           "default": "long_term"},
            "action": {"type": "select", "label": "Action",
                      "options": ["remember", "recall", "search", "clear"],
                      "default": "remember"},
            "search_query": {"type": "string", "label": "Search Query", "default": ""}
        },
        "inputs": 1,
        "outputs": 1
    },
    "condition": {
        "type": "condition",
        "label": "Condition Node",
        "color": "#EAB308",
        "category": "logic",
        "icon": "🔀",
        "description": "If/else branching logic. Routes workflow based on conditions.",
        "config_schema": {
            "condition": {"type": "string", "label": "Condition",
                         "default": "if output contains error"}
        },
        "inputs": 1,
        "outputs": 2
    },
    "loop": {
        "type": "loop",
        "label": "Loop Node",
        "color": "#EC4899",
        "category": "logic",
        "icon": "🔁",
        "description": "Repeat an action N times or until a condition is met.",
        "config_schema": {
            "max_iterations": {"type": "number", "label": "Max Iterations", "default": 5},
            "stop_condition": {"type": "string", "label": "Stop Condition", "default": ""}
        },
        "inputs": 1,
        "outputs": 1
    },
    "agent": {
        "type": "agent",
        "label": "Agent Node",
        "color": "#EF4444",
        "category": "ai",
        "icon": "🤖",
        "description": "Full autonomous agent combining LLM + tools + reasoning loop.",
        "config_schema": {
            "model": {"type": "string", "label": "Model", "default": "llama3.1:8b"},
            "tools": {"type": "multiselect", "label": "Tools",
                     "options": list(TOOL_DEFINITIONS.keys()),
                     "default": []},
            "system_prompt": {"type": "textarea", "label": "Agent Persona",
                             "default": "You are a helpful AI agent."},
            "max_steps": {"type": "slider", "label": "Max Steps", "min": 1, "max": 20,
                         "step": 1, "default": 10},
            "memory": {"type": "boolean", "label": "Enable Memory", "default": False}
        },
        "inputs": 1,
        "outputs": 1
    },
    "output": {
        "type": "output",
        "label": "Output Node",
        "color": "#6B7280",
        "category": "output",
        "icon": "📤",
        "description": "End of the workflow. Displays the final result.",
        "config_schema": {},
        "inputs": 1,
        "outputs": 0
    }
}
