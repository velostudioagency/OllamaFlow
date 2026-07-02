"""
OllamaFlow CLI - Main REPL loop with prompt_toolkit session, shortcuts, state persistence.
"""

import os
import json
import asyncio
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout

from ollamaflow.client import OllamaFlow
from ollamaflow.ui import (
    console, print_banner, print_server_status, print_info,
    print_success, print_error, print_markdown,
)
from ollamaflow.commands import CommandHandler, get_command_list
from ollamaflow import server as server_mod

# State directory
OLLAMAFLOW_DIR = Path.home() / ".ollamaflow"
STATE_FILE = OLLAMAFLOW_DIR / "state.json"
HISTORY_FILE = OLLAMAFLOW_DIR / "history.json"

# Prompt style
STYLE = Style.from_dict({
    "prompt": "bold cyan",
})


class CommandCompleter(Completer):
    """Auto-complete slash commands, node type names, and workflow names."""

    def __init__(self, workflow_names=None, command_names=None):
        self.workflow_names = workflow_names or []
        self.command_names = command_names or [c[0] for c in get_command_list()]

    def update_workflows(self, names):
        self.workflow_names = names

    def get_completions(self, document, complete_event):
        text = document.text_before_cursor
        word = document.get_word_before_cursor(WORD=True)

        # Slash commands
        if text.startswith("/"):
            cmd_part = text[1:]
            for cmd in self.command_names:
                if cmd.startswith(cmd_part):
                    yield Completion(cmd, start_position=-len(cmd_part))

        # Workflow names after /use, /run, /edit, etc.
        parts = text.split()
        if len(parts) >= 2 and parts[0] in ("/use", "/run", "/edit", "/show", "/validate", "/delete", "/versions", "/export"):
            partial = parts[-1]
            for wf in self.workflow_names:
                if wf.startswith(partial):
                    yield Completion(wf, start_position=-len(partial))


def create_key_bindings(handler_ref):
    """Create key bindings for the REPL."""
    kb = KeyBindings()

    @kb.add("c-l")
    def clear_screen(event):
        os.system("cls" if os.name == "nt" else "clear")

    @kb.add("c-d")
    def exit_repl(event):
        event.app.exit()

    return kb


def load_state() -> dict:
    """Load persisted state."""
    default = {
        "active_workflow": None,
        "server_url": "http://localhost:8000",
        "last_model": None,
    }
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                saved = json.load(f)
            default.update(saved)
        except Exception:
            pass
    return default


def save_state(state: dict):
    """Persist state to disk."""
    OLLAMAFLOW_DIR.mkdir(parents=True, exist_ok=True)
    to_save = {
        "active_workflow": state.get("active_workflow"),
        "server_url": state.get("server_url"),
        "last_model": state.get("last_model"),
    }
    with open(STATE_FILE, "w") as f:
        json.dump(to_save, f, indent=2)


def load_command_history() -> list:
    """Load command history."""
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return []


def save_command_history(history: list):
    """Save last 50 commands."""
    OLLAMAFLOW_DIR.mkdir(parents=True, exist_ok=True)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history[-50:], f)


async def run_repl(url: str = None, token: str = None, no_server: bool = False, port: int = 8000):
    """Main REPL entry point."""
    state = load_state()

    if url:
        state["server_url"] = url

    client = OllamaFlow(
        base_url=state.get("server_url", "http://localhost:8000"),
        api_token=token,
    )

    # Banner
    print_banner(full=False)

    # Server management
    if not no_server:
        server_running = server_mod.is_server_running(port=port)
        if server_running:
            print_server_status(port, True, 0)
        else:
            from ollamaflow.ui import prompt_confirm
            if prompt_confirm("OllamaFlow API server not running. Start it?", default=True):
                print_info("Starting OllamaFlow API server...")
                success, pid = server_mod.start_server(port=port)
                if success:
                    print_success(f"OllamaFlow API server started (PID {pid})")
                    print_server_status(port, True, 0)
                else:
                    print_error("OllamaFlow API server failed to start. Continuing offline.")
            else:
                print_info("Continuing offline (list/import only).")
    else:
        print_server_status(port, server_mod.is_server_running(port=port), 0)

    # Pre-fetch tools and models
    tools_cache = []
    models_cache = []
    try:
        tools_cache = await client.list_tools()
        state["tools_cache"] = tools_cache
    except Exception:
        pass
    try:
        models_cache = await client.list_models()
        state["models_cache"] = models_cache
    except Exception:
        pass

    # Command handler
    handler = CommandHandler(client, state)

    # Completer
    completer = CommandCompleter()
    try:
        wf_names = await client.list_workflows()
        completer.update_workflows(wf_names)
    except Exception:
        pass

    # Key bindings
    kb = create_key_bindings(None)

    # Prompt session
    session = PromptSession(
        completer=completer,
        history=InMemoryHistory(),
        key_bindings=kb,
        style=STYLE,
        multiline=False,
    )

    # Command history
    cmd_history = load_command_history()

    # Main loop
    with patch_stdout():
        while True:
            try:
                # Build prompt
                active = state.get("active_workflow")
                if active:
                    prompt_str = f"[{active}] > "
                else:
                    prompt_str = "> "

                user_input = await session.prompt_async(prompt_str)

                text = user_input.strip()
                if not text:
                    continue

                # Save to history
                cmd_history.append(text)
                save_command_history(cmd_history)

                # Handle slash commands
                if text.startswith("/"):
                    should_continue = await handler.handle(text)
                    if not should_continue:
                        break
                    # Refresh completer
                    try:
                        wf_names = await client.list_workflows()
                        completer.update_workflows(wf_names)
                    except Exception:
                        pass
                    continue

                # Natural language — auto-create temp LLM workflow and run
                active_workflow = state.get("active_workflow")
                if active_workflow:
                    # Run with active workflow
                    try:
                        result = await client.run(active_workflow, input_text=text, timeout=300)
                        console.print()
                        print_markdown(result.output)
                    except Exception as e:
                        print_error(f"Run failed: {e}")
                else:
                    # Create temporary LLM workflow
                    temp_workflow = {
                        "nodes": [
                            {"id": "input_1", "type": "input", "config": {"prompt": text}},
                            {"id": "llm_1", "type": "llm", "config": {
                                "model": state.get("last_model") or "llama3.1:8b",
                                "system_prompt": "You are a helpful assistant.",
                                "temperature": 0.7,
                            }},
                            {"id": "output_1", "type": "output", "config": {}},
                        ],
                        "edges": [
                            {"source": "input_1", "target": "llm_1"},
                            {"source": "llm_1", "target": "output_1"},
                        ],
                    }
                    console.print("[dim](no active workflow — using temporary LLM session)[/]\n")
                    try:
                        result = await client.run(temp_workflow, input_text=text, timeout=300)
                        print_markdown(result.output)
                    except Exception as e:
                        print_error(f"Failed: {e}")

            except KeyboardInterrupt:
                continue
            except EOFError:
                break
            except Exception as e:
                print_error(f"Error: {e}")
                continue

    # Save state on exit
    save_state(state)
    print_info("Goodbye!")
