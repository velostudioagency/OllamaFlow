"""
OllamaFlow CLI - All slash command handlers.
"""

import json
import os
import sys
import asyncio
from typing import Optional

from ollamaflow.ui import (
    console, print_success, print_error, print_info, print_warning,
    print_markdown, print_table, print_workflow_table, print_models_table,
    print_tools_table, print_versions_table, print_ascii_diagram,
    print_validation_result, prompt_confirm, prompt_input,
)
from ollamaflow.builder import (
    build_workflow_interactive, edit_workflow_interactive,
    validate_workflow, get_all_node_types,
)
from ollamaflow import server as server_mod


def get_command_list():
    """Return list of (name, description) for all commands."""
    return [
        ("help", "Show all commands with descriptions"),
        ("list", "List saved workflows, optional filter by name"),
        ("search", "Full-text search across workflow names + configs"),
        ("use", "Set active workflow for chat"),
        ("run", "Run a workflow (default: active)"),
        ("new", "Create a new workflow interactively"),
        ("edit", "Edit an existing workflow"),
        ("show", "ASCII diagram + key-value node details"),
        ("validate", "Check structure, warn on issues but allow saving"),
        ("delete", "Delete a workflow"),
        ("versions", "List workflow version history"),
        ("import", "Import from file path, URL, or raw JSON paste"),
        ("export", "Export workflow to JSON file"),
        ("models", "List available Ollama models"),
        ("tools", "List available tools with descriptions"),
        ("serve", "Start the OllamaFlow API server (if not running)"),
        ("stop", "Stop the OllamaFlow API server"),
        ("status", "Show API server status, active workflow, Ollama connection"),
        ("clear", "Clear the terminal"),
        ("banner", "Show full ASCII art banner"),
        ("exit", "Exit the REPL (API server stays running)"),
        ("quit", "Exit the REPL (API server stays running)"),
    ]


class CommandHandler:
    """Handles all slash commands for the REPL."""

    def __init__(self, client, state):
        self.client = client
        self.state = state  # dict: active_workflow, server_url, last_model, tools_cache, models_cache

    async def handle(self, command_str: str) -> bool:
        """
        Handle a slash command string. Returns True if REPL should continue,
        False if it should exit.
        """
        parts = command_str.strip().split(None, 1)
        cmd = parts[0].lower().lstrip("/")
        args = parts[1] if len(parts) > 1 else ""

        handler = getattr(self, f"cmd_{cmd}", None)
        if handler:
            try:
                return await handler(args)
            except Exception as e:
                print_error(f"Command error: {e}")
                return True
        else:
            print_error(f"Unknown command: /{cmd}. Type /help for available commands.")
            return True

    async def cmd_help(self, args: str) -> bool:
        """Show help."""
        from rich.table import Table
        from rich import box
        table = Table(title="Commands", box=box.ROUNDED)
        table.add_column("Command", style="cyan", no_wrap=True)
        table.add_column("Description")
        for name, desc in get_command_list():
            table.add_row(f"/{name}", desc)
        console.print(table)
        return True

    async def cmd_list(self, args: str) -> bool:
        """List saved workflows."""
        try:
            workflows = await self.client.list_workflows()
            if not workflows:
                print_info("No saved workflows found.")
                return True

            # Fetch full details
            detailed = []
            for name in workflows:
                try:
                    wf = await self.client.load_workflow(name)
                    detailed.append({
                        "name": name,
                        "saved_at": wf.get("saved_at", "Unknown"),
                        "node_count": len(wf.get("nodes", [])),
                    })
                except Exception:
                    detailed.append({
                        "name": name,
                        "saved_at": "Unknown",
                        "node_count": 0,
                    })

            # Apply filter
            if args:
                detailed = [w for w in detailed if args.lower() in w["name"].lower()]

            print_workflow_table(detailed)
        except Exception as e:
            print_error(f"Failed to list workflows: {e}")
        return True

    async def cmd_search(self, args: str) -> bool:
        """Search workflows by name."""
        if not args:
            print_error("Usage: /search <query>")
            return True
        try:
            workflows = await self.client.list_workflows()
            matches = [w for w in workflows if args.lower() in w.lower()]
            if matches:
                console.print(f"  [cyan]Search results for '{args}':[/]")
                for m in matches:
                    console.print(f"    - {m}")
            else:
                print_info(f"No workflows matching '{args}'.")
        except Exception as e:
            print_error(f"Search failed: {e}")
        return True

    async def cmd_use(self, args: str) -> bool:
        """Set active workflow."""
        if not args:
            print_error("Usage: /use <workflow_name>")
            return True
        try:
            wf = await self.client.load_workflow(args)
            self.state["active_workflow"] = args
            self.state["active_workflow_data"] = wf
            print_success(f"Active workflow: [cyan]{args}[/]")
        except Exception as e:
            print_error(f"Workflow '{args}' not found: {e}")
        return True

    async def cmd_run(self, args: str) -> bool:
        """Run a workflow."""
        # Parse args: [name] [--input "text"] [--stream]
        parts = args.split()
        workflow_name = None
        input_text = ""
        use_stream = False

        i = 0
        while i < len(parts):
            if parts[i] == "--input" and i + 1 < len(parts):
                input_text = parts[i + 1].strip('"').strip("'")
                i += 2
            elif parts[i] == "--stream":
                use_stream = True
                i += 1
            elif not parts[i].startswith("--"):
                workflow_name = parts[i]
                i += 1
            else:
                i += 1

        if not workflow_name:
            workflow_name = self.state.get("active_workflow")
        if not workflow_name:
            print_error("No workflow specified. Use: /run <name> [--input text]")
            return True

        try:
            if use_stream:
                print_info(f"Streaming workflow: {workflow_name}")
                async for event in self.client.run_stream(
                    workflow_name, input_text=input_text, timeout=300
                ):
                    if event.type == "log":
                        prefix = f"[{event.node_type}] " if event.node_type else ""
                        console.print(f"  [dim]{prefix}{event.data}[/]")
                    elif event.type == "stream":
                        console.print(event.data, end="", highlight=False)
                    elif event.type == "token_usage":
                        usage = event.token_usage or {}
                        prompt = usage.get("prompt_tokens", 0)
                        completion = usage.get("completion_tokens", 0)
                        total = usage.get("total_tokens", 0)
                        console.print(f"\n  [dim]Tokens: {prompt} prompt + {completion} completion = {total} total[/]")
                    elif event.type == "complete":
                        console.print()
                        print_markdown(event.data)
                    elif event.type == "error":
                        print_error(event.data)
            else:
                print_info(f"Running workflow: {workflow_name}")
                result = await self.client.run(workflow_name, input_text=input_text, timeout=300)
                console.print()
                print_markdown(result.output)
                if result.token_usage:
                    usage = result.token_usage
                    prompt = usage.get("prompt_tokens", 0)
                    completion = usage.get("completion_tokens", 0)
                    total = usage.get("total_tokens", 0)
                    cost = usage.get("estimated_cost", 0)
                    console.print(f"\n  [dim]Tokens: {prompt} prompt + {completion} completion = {total} total[/]")
                    if cost > 0:
                        console.print(f"  [dim]Estimated cost: ${cost:.4f}[/]")
                console.print(f"  [dim]Duration: {result.duration_ms:.0f}ms | Status: {result.status}[/]")
        except Exception as e:
            print_error(f"Run failed: {e}")
        return True

    async def cmd_new(self, args: str) -> bool:
        """Create a new workflow interactively."""
        name = args.strip()
        if not name:
            name = prompt_input("  Workflow name")
        if not name:
            print_error("Workflow name is required.")
            return True

        console.print(f"\n  [bold]Creating workflow: [cyan]{name}[/][/]")

        # Check for overwrite
        try:
            existing = await self.client.list_workflows()
            if name in existing:
                if not prompt_confirm(f"Workflow '{name}' already exists. Overwrite?", default=False):
                    print_info("Cancelled.")
                    return True
        except Exception:
            pass

        # Get tools for builder
        available_tools = self.state.get("tools_cache", [])
        if not available_tools:
            try:
                available_tools = await self.client.list_tools()
                self.state["tools_cache"] = available_tools
            except Exception:
                available_tools = []

        workflow = build_workflow_interactive(available_tools=available_tools)
        if workflow is None:
            print_info("Cancelled.")
            return True

        # Validate
        results = validate_workflow(workflow)
        print_validation_result(results)

        # Save
        try:
            await self.client.save_workflow(name, workflow)
            node_count = len(workflow.get("nodes", []))
            edge_count = len(workflow.get("edges", []))
            print_success(f"Saved '[cyan]{name}[/]' ({node_count} nodes, {edge_count} edges)")
            self.state["active_workflow"] = name
            self.state["active_workflow_data"] = workflow
        except Exception as e:
            print_error(f"Failed to save: {e}")
        return True

    async def cmd_edit(self, args: str) -> bool:
        """Edit an existing workflow."""
        name = args.strip()
        if not name:
            name = self.state.get("active_workflow")
        if not name:
            print_error("Usage: /edit <workflow_name>")
            return True

        try:
            workflow = await self.client.load_workflow(name)
        except Exception as e:
            print_error(f"Workflow '{name}' not found: {e}")
            return True

        console.print(f"\n  [bold]Editing: [cyan]{name}[/][/] ({len(workflow.get('nodes', []))} nodes, {len(workflow.get('edges', []))} edges)")

        available_tools = self.state.get("tools_cache", [])
        if not available_tools:
            try:
                available_tools = await self.client.list_tools()
                self.state["tools_cache"] = available_tools
            except Exception:
                available_tools = []

        updated = edit_workflow_interactive(workflow, available_tools)
        if updated is None:
            print_info("Cancelled.")
            return True

        try:
            await self.client.save_workflow(name, updated)
            node_count = len(updated.get("nodes", []))
            edge_count = len(updated.get("edges", []))
            print_success(f"Saved '[cyan]{name}[/]' ({node_count} nodes, {edge_count} edges)")
            self.state["active_workflow_data"] = updated
        except Exception as e:
            print_error(f"Failed to save: {e}")
        return True

    async def cmd_show(self, args: str) -> bool:
        """Show ASCII diagram of a workflow."""
        name = args.strip()
        if not name:
            name = self.state.get("active_workflow")
        if not name:
            print_error("Usage: /show <workflow_name>")
            return True

        try:
            workflow = await self.client.load_workflow(name)
        except Exception as e:
            print_error(f"Workflow '{name}' not found: {e}")
            return True

        nodes = workflow.get("nodes", [])
        edges = workflow.get("edges", [])
        console.print(f"\n  [bold][cyan]{name}[/][/] ({len(nodes)} nodes, {len(edges)} edges)\n")
        print_ascii_diagram(workflow)

        # Node details
        if nodes:
            console.print("\n  [bold]Node Details:[/]")
            for n in nodes:
                nid = n["id"]
                ntype = n["type"]
                config = n.get("config", {})
                console.print(f"    [cyan]{nid}[/] ([dim]{ntype}[/]):")
                if config:
                    for k, v in config.items():
                        val = str(v)
                        if len(val) > 60:
                            val = val[:60] + "..."
                        console.print(f"      {k} = [dim]{val}[/]")
                else:
                    console.print("      [dim](no config)[/]")
        return True

    async def cmd_validate(self, args: str) -> bool:
        """Validate a workflow."""
        name = args.strip()
        if not name:
            name = self.state.get("active_workflow")
        if not name:
            print_error("Usage: /validate <workflow_name>")
            return True

        try:
            workflow = await self.client.load_workflow(name)
        except Exception as e:
            print_error(f"Workflow '{name}' not found: {e}")
            return True

        console.print(f"\n  [bold]Validating: [cyan]{name}[/][/]")
        results = validate_workflow(workflow)
        print_validation_result(results)
        return True

    async def cmd_delete(self, args: str) -> bool:
        """Delete a workflow."""
        name = args.strip()
        if not name:
            print_error("Usage: /delete <workflow_name>")
            return True

        if not prompt_confirm(f"Delete workflow '{name}'?", default=False):
            print_info("Cancelled.")
            return True

        try:
            # Use the server's delete endpoint
            import httpx
            url = f"{self.client.base_url}/api/workflows/{name}"
            headers = self.client._headers()
            async with httpx.AsyncClient() as c:
                resp = await c.delete(url, headers=headers)
                resp.raise_for_status()
            print_success(f"Deleted '[cyan]{name}[/]'")
            if self.state.get("active_workflow") == name:
                self.state["active_workflow"] = None
                self.state["active_workflow_data"] = None
        except Exception as e:
            print_error(f"Failed to delete: {e}")
        return True

    async def cmd_versions(self, args: str) -> bool:
        """List workflow version history."""
        name = args.strip()
        if not name:
            print_error("Usage: /versions <workflow_name>")
            return True

        try:
            import httpx
            url = f"{self.client.base_url}/api/workflows/{name}/versions"
            headers = self.client._headers()
            async with httpx.AsyncClient() as c:
                resp = await c.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                versions = data.get("versions", [])
            if versions:
                print_versions_table(versions, name)
            else:
                print_info(f"No versions found for '{name}'.")
        except Exception as e:
            print_error(f"Failed to get versions: {e}")
        return True

    async def cmd_import(self, args: str) -> bool:
        """Import a workflow from file, URL, or JSON."""
        source = args.strip()
        if not source:
            print_error("Usage: /import <file|url|json>")
            return True

        workflow = None

        # Try as URL
        if source.startswith("http://") or source.startswith("https://"):
            try:
                import httpx
                async with httpx.AsyncClient() as c:
                    resp = await c.get(source, timeout=30)
                    resp.raise_for_status()
                    workflow = resp.json()
            except Exception as e:
                print_error(f"Failed to fetch URL: {e}")
                return True
        # Try as file path
        elif os.path.isfile(source):
            try:
                with open(source, "r", encoding="utf-8") as f:
                    workflow = json.load(f)
            except Exception as e:
                print_error(f"Failed to read file: {e}")
                return True
        # Try as raw JSON
        else:
            try:
                workflow = json.loads(source)
            except json.JSONDecodeError as e:
                print_error(f"Invalid JSON: {e}. Check format and retry.")
                return True

        if not workflow:
            print_error("No workflow data found.")
            return True

        name = prompt_input("  Workflow name", default=workflow.get("name", "imported"))
        if not name:
            print_error("Name is required.")
            return True

        try:
            await self.client.save_workflow(name, workflow)
            node_count = len(workflow.get("nodes", []))
            print_success(f"Imported '[cyan]{name}[/]' ({node_count} nodes)")
        except Exception as e:
            print_error(f"Failed to import: {e}")
        return True

    async def cmd_export(self, args: str) -> bool:
        """Export a workflow to a JSON file."""
        parts = args.split()
        if len(parts) < 2:
            print_error("Usage: /export <workflow_name> <file_path>")
            return True

        name = parts[0]
        filepath = parts[1]

        try:
            workflow = await self.client.load_workflow(name)
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(workflow, f, indent=2)
            print_success(f"Exported '[cyan]{name}[/]' to [dim]{filepath}[/]")
        except Exception as e:
            print_error(f"Failed to export: {e}")
        return True

    async def cmd_models(self, args: str) -> bool:
        """List available Ollama models."""
        try:
            models = await self.client.list_models()
            self.state["models_cache"] = models
            if models:
                print_models_table(models)
            else:
                print_info("No models found. Is Ollama running?")
        except Exception as e:
            print_error(f"Failed to list models: {e}")
        return True

    async def cmd_tools(self, args: str) -> bool:
        """List available tools."""
        try:
            tools = await self.client.list_tools()
            self.state["tools_cache"] = tools
            if tools:
                print_tools_table(tools)
            else:
                print_info("No tools available.")
        except Exception as e:
            print_error(f"Failed to list tools: {e}")
        return True

    async def cmd_serve(self, args: str) -> bool:
        """Start the OllamaFlow API server."""
        port = 8000
        if args.strip().isdigit():
            port = int(args.strip())

        if server_mod.is_server_running(port=port):
            print_info(f"OllamaFlow API server already running on port {port}.")
            return True

        from rich.status import Status
        with Status(f"[cyan]Starting OllamaFlow API server on port {port}...[/]", console=console, spinner="dots"):
            success, pid = server_mod.start_server(port=port)
        if success:
            print_success(f"OllamaFlow API server started (PID {pid}) on port {port}")
        else:
            # pid is actually an error message here
            print_error(f"OllamaFlow API server failed to start: {pid}")
        return True

    async def cmd_stop(self, args: str) -> bool:
        """Stop the OllamaFlow API server."""
        success, msg = server_mod.stop_server()
        if success:
            print_success(msg)
        else:
            print_info(msg)
        return True

    async def cmd_status(self, args: str) -> bool:
        """Show server status."""
        port = int(args.strip()) if args.strip().isdigit() else 8000
        info = server_mod.get_server_info(port=port)
        active = self.state.get("active_workflow", None)

        from rich.panel import Panel
        from rich.table import Table as RichTable
        from rich import box

        table = box=RichTable(box=None, show_header=False)
        table.add_column("Key", style="cyan")
        table.add_column("Value")
        table.add_row("OllamaFlow API", "[green]Running[/]" if info["running"] else "[red]Stopped[/]")
        table.add_row("Port", str(info["port"]))
        table.add_row("PID", str(info["pid"]) if info["pid"] else "N/A")
        table.add_row("Active Workflow", active or "[dim]None[/]")
        table.add_row("Log File", info["log_file"])

        # Check Ollama
        try:
            import httpx
            resp = httpx.get("http://localhost:11434/api/tags", timeout=3)
            models = resp.json().get("models", [])
            table.add_row("Ollama", f"[green]Connected[/] ({len(models)} models)")
        except Exception:
            table.add_row("Ollama", "[red]Disconnected[/]")

        console.print(Panel(table, title="Status", border_style="cyan"))
        return True

    async def cmd_clear(self, args: str) -> bool:
        """Clear the terminal."""
        os.system("cls" if os.name == "nt" else "clear")
        return True

    async def cmd_banner(self, args: str) -> bool:
        """Show full ASCII art banner."""
        from ollamaflow.ui import print_banner
        print_banner(full=True)
        return True

    async def cmd_exit(self, args: str) -> bool:
        """Exit the REPL."""
        print_info("Goodbye!")
        return False

    async def cmd_quit(self, args: str) -> bool:
        """Exit the REPL."""
        return await self.cmd_exit(args)
