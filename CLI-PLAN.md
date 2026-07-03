# OllamaFlow Interactive CLI Plan

> Transform the argparse CLI into a Claude Code / OpenCode-style interactive REPL
> with full workflow creation capabilities.

---

## Overview

Running `ollamaflow` starts a rich interactive session where users can chat, run,
and **build workflows entirely from the terminal**. No browser required.

### New Dependencies

| Package | Purpose |
|---------|---------|
| `rich` | Beautiful terminal output — colors, panels, tables, markdown |
| `prompt_toolkit` | Interactive input — tab completion, history, multi-line editing |

### Files to Create

| File | Purpose | Est. Lines |
|------|---------|-----------|
| `backend/ollamaflow/ui.py` | Banner, colors, panels, tables, markdown rendering | ~200 |
| `backend/ollamaflow/server.py` | Auto-server management — health check, background start, PID tracking | ~120 |
| `backend/ollamaflow/builder.py` | Interactive workflow builder — wizard, node config, ASCII diagram, validate | ~450 |
| `backend/ollamaflow/commands.py` | All slash command handlers | ~500 |
| `backend/ollamaflow/repl.py` | Main REPL loop — prompt_toolkit session, shortcuts, state persistence | ~250 |

### Files to Modify

| File | Change |
|------|--------|
| `backend/ollamaflow/__main__.py` | Add REPL as default when no args; add `--no-server`, `--port` flags |
| `backend/requirements.txt` | Add `rich` and `prompt_toolkit` |

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands with descriptions |
| `/list [filter]` | List saved workflows, optional filter by name |
| `/search <query>` | Full-text search across workflow names + configs |
| `/use <name>` | Set active workflow for chat |
| `/run [name] [--input "text"]` | Run a workflow (default: active) |
| `/new [name]` | Create a new workflow interactively (prompt if no name) |
| `/edit <name>` | Edit an existing workflow (add/remove/connect/rename/duplicate/config) |
| `/show [name]` | ASCII diagram + key-value node details |
| `/validate [name]` | Check structure, warn on issues but allow saving |
| `/delete <name>` | Delete a workflow |
| `/versions <name>` | List workflow version history |
| `/import <file\|url\|json>` | Import from file path, URL, or raw JSON paste |
| `/export <name> <file>` | Export workflow to JSON file |
| `/models` | List available Ollama models |
| `/tools` | List available tools with descriptions |
| `/serve` | Start the server (if not running) |
| `/stop` | Stop the server |
| `/status` | Show server status, active workflow, Ollama connection |
| `/clear` | Clear the terminal |
| `/banner` | Show full ASCII art banner |
| `/exit` or `/quit` | Exit the REPL (server stays running) |

---

## Interactive Workflow Builder

### Entry Points

**`/new [name]`** — Create from scratch:

```
> /new my_agent

  Creating workflow: my_agent

  Node 1 — What type?
    Triggers:  1. input    2. webhook
    AI:        3. llm      4. guardrails
    Tools:     5. tool     6. transform   7. variable   8. custom
    Logic:     9. condition  10. switch   11. loop      12. merge
               13. delay    14. subworkflow  15. batch
    Memory:   16. memory
    Output:   17. output   18. webhook_output

  Type (number or name): > 3

  Configure 'llm' node:
    model [llama3.1:8b]: > codellama:13b
    system_prompt: > You are a code reviewer
    temperature [0.7]: > 0.3

  Node 2 — What type? > 17 (output)

  Connect nodes:
    Connect llm_1 → output_2? [Y/n]: > Y

  ┌─────────┐     ┌─────────┐     ┌──────────┐
  │ input_1 │────▶│  llm_1  │────▶│output_2  │
  └─────────┘     └─────────┘     └──────────┘

  ✓ Saved 'my_agent' (2 nodes, 1 edge)
```

**`/edit <name>`** — Modify existing:

```
> /edit my_agent

  Editing: my_agent (3 nodes, 2 edges)

  Actions:
    add       — Add a node
    remove    — Remove a node
    connect   — Connect two nodes
    disconnect — Remove a connection
    rename    — Rename a node
    duplicate — Duplicate a node
    config    — Reconfigure a node (opens $EDITOR)
    json      — Edit raw node JSON (opens $EDITOR)
    done      — Finish editing and save

  Action > add
  Node type? > tool
  Configure 'tool' node:
    tool_name [web_search]: > web_scraper

  Connect 'web_scraper' after which node? > llm_1

  Action > done
  ✓ Saved 'my_agent' (4 nodes, 3 edges)
```

### Builder Rules

- **Auto-generate IDs**: `input_1`, `llm_2`, `output_3`, etc.
- **Smart defaults**: after first node of a type, skip non-essential fields
- **Node selection**: numbered list with tab-completion on type names
- **Multi-line input**: Shift+Enter for newlines in system prompts/templates, Enter submits
- **Ctrl+C during build**: ask "Discard unsaved changes? [Y/n]"
- **Validation**: warn on issues (missing I/O, orphans), allow saving anyway
- **Auto-save**: after each successful edit action

### Node Configuration Wizard

Each node type prompts for relevant fields with sensible defaults:

| Node | Prompts |
|------|---------|
| `input` | prompt, input_type (text/file/scheduled), file_path |
| `llm` | model (shows available), system_prompt, temperature, max_tokens, provider |
| `tool` | tool_name (shows available tools), params (key=value prompts) |
| `memory` | namespace, memory_type, action, search_query |
| `condition` | condition expression |
| `loop` | max_iterations, stop_condition |
| `transform` | transform_type, pattern, replacement, template |
| `merge` | merge_mode, separator |
| `guardrails` | validation_type, pattern, max_length, retry_on_fail |
| `variable` | variable_name, variable_value, variable_type, mode |
| `switch` | switch_field, cases, default_case |
| `delay` | delay_seconds |
| `webhook` | webhook_url, method, auth_token |
| `webhook_output` | webhook_url, method, content_type, retry_count |
| `subworkflow` | subworkflow_json, pass_input |
| `batch` | subworkflow_json, batch_mode |
| `custom` | custom_code, handler_name |
| `output` | (no config) |

### ASCII Workflow Diagram (`/show`)

```
> /show my_agent

  my_agent (3 nodes, 2 edges)

  ┌─────────┐     ┌─────────┐     ┌──────────┐
  │ input_1 │────▶│  llm_1  │────▶│output_2  │
  │ (input) │     │  (llm)  │     │ (output) │
  └─────────┘     └─────────┘     └──────────┘

  Node Details:
    input_1:
      prompt = "Research AI"
      input_type = "text"
    llm_1:
      model = "codellama:13b"
      system_prompt = "You are a code reviewer"
      temperature = 0.3
    output_2:
      (terminal node)
```

### Validation (`/validate`)

```
> /validate my_agent

  Validating: my_agent

  ✓ All nodes have valid types
  ✓ No orphan nodes (every node is reachable)
  ✓ All edges connect valid nodes
  ✓ Workflow has at least one input and output
  ⚠ Node 'tool_3' has no outgoing edges (not connected to output)
  ✓ No cycles detected

  1 warning — workflow can still be saved
```

---

## Chat Without Workflow

When user types natural language with no workflow active, auto-create a temporary
single LLM node workflow on the fly, run it, discard it. Seamless.

```
> What is the capital of France?

  (no active workflow — using temporary LLM session)

  The capital of France is Paris.
```

---

## Auto-Server Management

- On REPL start, ping `/api/health`
- If server is down, ask: "Server not running. Start it? [Y/n]"
- Start via `subprocess.Popen` with `uvicorn main:app --port 8000`
- Track PID in `~/.ollamaflow/server.pid`
- On `/exit`, server stays running (user can `/stop` manually)
- `/serve` and `/stop` for manual control

---

## Output Formatting

- `/run` output: markdown rendered via `rich.markdown`
- `/show`: ASCII boxes + arrows + key-value config per node
- `/list`: rich table with name, saved date, node count
- `/models` / `/tools`: rich table with details
- Errors: red text + suggestion ("Try /list to see available workflows")
- Success: green text
- Info: cyan text

---

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+L` | Clear terminal |
| `Ctrl+C` | Cancel current input / confirm discard in builder |
| `Ctrl+D` | Exit |
| `Ctrl+S` | Save active workflow |
| `Ctrl+R` | Search command history (fuzzy) |
| `Tab` | Autocomplete commands, node types, workflow names |
| `Up/Down` | Navigate command history |

---

## Session State

Stored in `~/.ollamaflow/` directory:

| File | Contents |
|------|----------|
| `state.json` | Active workflow, server URL, last model used |
| `history.json` | Last 50 commands |
| `completions_cache.json` | Workflow names, models, tools (fetched on startup) |
| `server.pid` | Server process ID for tracking |

---

## Startup Banner

Minimal 3-line on startup:

```
OllamaFlow CLI v0.1.0
Server: :8000 | Ollama: connected | Models: 3
Type /help for commands
```

Full ASCII art available via `/banner`.

---

## Edge Cases

| Scenario | Behavior |
|----------|----------|
| Ctrl+C mid-build | "Discard unsaved changes? [Y/n]" |
| No workflow + natural language | Auto-create temp LLM workflow, run, discard |
| Server down | Offer to start, or continue offline (list/import only) |
| Duplicate workflow name | "Workflow 'x' already exists. Overwrite? [Y/n]" |
| Invalid JSON on import | "Invalid JSON: {error}. Check format and retry." |
| Missing $EDITOR for /edit json | Fall back to inline terminal editing |
| Node has no config fields | Skip config prompts, save immediately |
| Workflow with no output node | Warn: "No output node — result won't be captured" |
| Connect to self | "Cannot connect a node to itself" |
| Circular connection | "Warning: this creates a cycle. Proceed? [Y/n]" |

---

## Implementation Order

1. **`ui.py`** — banner, colors, panels, tables, markdown helpers
2. **`server.py`** — health check, background start, PID tracking
3. **`builder.py`** — interactive wizard, node config prompts, ASCII diagram, validate
4. **`commands.py`** — all slash commands wired to client + builder
5. **`repl.py`** — main loop, prompt_toolkit session, shortcuts, state persistence
6. **`__main__.py`** — add `--no-server`, `--port`, default to REPL
7. **`requirements.txt`** — add `rich`, `prompt_toolkit`

---

## UX Flow Example (Full Session)

```
$ ollamaflow

  OllamaFlow CLI v0.1.0
  Server: :8000 | Ollama: connected | Models: 3
  Type /help for commands

> /list
  ┌──────────────────┬────────────────────┬───────┐
  │ Name             │ Saved              │ Nodes │
  ├──────────────────┼────────────────────┼───────┤
  │ research_agent   │ 2026-07-01 14:30   │ 6     │
  │ code_reviewer    │ 2026-07-02 09:15   │ 4     │
  └──────────────────┴────────────────────┴───────┘

> /new summarizer
  Creating workflow: summarizer

  Node 1 — Type? > input
  prompt: > Enter text to summarize

  Node 2 — Type? > llm
  model [llama3.1:8b]: >
  system_prompt: > Summarize in 3 bullet points

  Node 3 — Type? > output

  Connect: input_1 → llm_2? > Y
  Connect: llm_2 → output_3? > Y

  ┌─────────┐     ┌─────────┐     ┌──────────┐
  │ input_1 │────▶│  llm_2  │────▶│ output_3 │
  └─────────┘     └─────────┘     └──────────┘

  ✓ Saved 'summarizer' (3 nodes, 2 edges)

> /use summarizer
  ✓ Active workflow: summarizer

> The quick brown fox jumps over the lazy dog.
  Streaming...

  • A quick brown fox leaps over a lazy dog
  • This sentence is a well-known pangram
  • It is being used as a test input

> /show summarizer
  [ASCII diagram + node details]

> /models
  ┌────────────────────┬──────────┐
  │ Model              │ Size     │
  ├────────────────────┼──────────┤
  │ llama3.1:8b        │ 4.7 GB   │
  │ codellama:13b      │ 7.4 GB   │
  │ mistral:7b         │ 4.1 GB   │
  └────────────────────┴──────────┘

> /exit
  Goodbye!
```
