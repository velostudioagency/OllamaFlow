<div align="center">

# OllamaFlow

**Visual AI Workflow Builder — Drag, Connect, Run.**

Build local AI agents by connecting nodes on a canvas. No cloud required.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![React 18](https://img.shields.io/badge/React-18-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)

</div>

---

OllamaFlow is a local-first, visual workflow builder for creating AI agents powered by [Ollama](https://ollama.com) and [Groq](https://groq.com). Drag nodes onto a canvas, connect them, configure each step, and run — all from your machine with zero cloud dependency.

It ships with both a **web UI** (React + ReactFlow) and an **interactive CLI** (REPL) for building and running workflows entirely from the terminal.

---

## Table of Contents

- [Features](#features)
- [Quick Start](#quick-start)
- [CLI Usage](#cli-usage)
  - [Starting the REPL](#starting-the-repl)
  - [Commands Reference](#commands-reference)
  - [Interactive Workflow Builder](#interactive-workflow-builder)
  - [Chat Without a Workflow](#chat-without-a-workflow)
  - [Keyboard Shortcuts](#keyboard-shortcuts)
- [Web UI](#web-ui)
- [Node Types](#node-types)
- [Built-in Tools](#built-in-tools)
- [API Reference](#api-reference)
- [Tech Stack](#tech-stack)
- [Configuration](#configuration)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **8 Node Types** — Input, LLM, Tool, Memory, Condition, Loop, Transform, Output
- **18+ Built-in Tools** — Web search, file I/O, code execution, browser automation, HTTP requests, and more
- **Interactive CLI** — Full-featured REPL with tab completion, command history, and rich terminal output
- **Multi-Engine Web Search** — Parallel search across DuckDuckGo, Bing, Brave, and SearXNG with auto-fallback
- **Dual AI Providers** — Ollama (local) and Groq (cloud) with live switching
- **Real-time Streaming** — Token-by-token output via WebSocket as workflows execute
- **Visual Canvas** — Drag-and-drop ReactFlow interface with minimap and controls
- **Persistent Memory** — Short-term and long-term memory backed by ChromaDB vector search
- **Save & Load** — Export/import workflows as JSON files
- **Version History** — Automatic versioning with rollback support

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+ (for web UI)
- [Ollama](https://ollama.com) running locally

### 1. Install Ollama

Download from [ollama.com](https://ollama.com) and pull a model:

```bash
ollama pull llama3.1:8b
```

### 2. One-Click Install (Windows)

```bash
install.bat
```

### 3. Manual Install

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt

# Frontend (optional, for web UI)
cd ../frontend
npm install
```

### 4. Start

```bash
# Windows
start.bat

# macOS/Linux
cd backend && uvicorn main:app --reload --port 8000 &
cd frontend && npm run dev
```

Open **http://localhost:5173** for the web UI, or launch the CLI directly:

```bash
python ollamaflow_cli.py
```

---

## CLI Usage

OllamaFlow includes a full interactive CLI (REPL) for building, managing, and running workflows without opening a browser.

### Starting the REPL

```bash
# From the project root
python ollamaflow_cli.py

# Or via the module
cd backend
python -m ollamaflow

# Skip auto-starting the server
python -m ollamaflow --no-server

# Use a custom port
python -m ollamaflow --port 9000

# Connect to a remote server
python -m ollamaflow --url http://192.168.1.100:8000
```

On startup, the REPL will:

1. Display a compact status banner
2. Ping the server health endpoint
3. Offer to start the server if it is not running
4. Pre-fetch available models and tools for tab completion

### Commands Reference

| Command | Description |
|---------|-------------|
| `/help` | Show all commands with descriptions |
| `/list [filter]` | List saved workflows, optional filter by name |
| `/search <query>` | Full-text search across workflow names |
| `/use <name>` | Set the active workflow for chat |
| `/run [name] [--input "text"]` | Run a workflow (defaults to the active one) |
| `/new [name]` | Create a new workflow interactively |
| `/edit <name>` | Edit an existing workflow (add/remove/connect/rename nodes) |
| `/show [name]` | Display an ASCII diagram + node configuration details |
| `/validate [name]` | Check workflow structure for issues |
| `/delete <name>` | Delete a workflow |
| `/versions <name>` | List version history for a workflow |
| `/import <file\|url\|json>` | Import a workflow from a file, URL, or raw JSON |
| `/export <name> <file>` | Export a workflow to a JSON file |
| `/models` | List available Ollama models |
| `/tools` | List available tools with descriptions |
| `/serve` | Start the server (if not running) |
| `/stop` | Stop the server |
| `/status` | Show server status, active workflow, Ollama connection |
| `/clear` | Clear the terminal |
| `/banner` | Show the full ASCII art banner |
| `/exit` or `/quit` | Exit the REPL (server stays running) |

### Interactive Workflow Builder

The `/new` command launches a step-by-step wizard for building workflows from scratch:

```
> /new summarizer

  Creating workflow: summarizer

  Node 1 — Type?
    Triggers:  1. input    2. webhook
    AI:        3. llm      4. guardrails
    Tools:     5. tool     6. transform   7. variable   8. custom
    Logic:     9. condition  10. switch   11. loop      12. merge
               13. delay    14. subworkflow  15. batch
    Memory:   16. memory
    Output:   17. output   18. webhook_output

  Type (number or name): > 1

  Configure 'input' node:
    Goal / Prompt: > Enter text to summarize

  Node 2 — Type? > 3 (llm)
    Model [llama3.1:8b]: >
    System Prompt: > Summarize in 3 bullet points

  Node 3 — Type? > 17 (output)

  Connect: input_1 → llm_2? [Y/n]: > Y
  Connect: llm_2 → output_3? [Y/n]: > Y

  ┌─────────┐     ┌─────────┐     ┌──────────┐
  │ input_1 │────▶│  llm_2  │────▶│ output_3 │
  └─────────┘     └─────────┘     └──────────┘

  ✓ Saved 'summarizer' (3 nodes, 2 edges)
```

The `/edit` command modifies existing workflows:

```
> /edit summarizer

  Editing: 3 nodes, 2 edges

  Actions:
    add       — Add a node
    remove    — Remove a node
    connect   — Connect two nodes
    disconnect — Remove a connection
    rename    — Rename a node
    done      — Finish editing and save

  Action > add
  Node type? > tool
  Configure 'tool' node:
    Tool: > web_search

  Connect 'web_search_4' after which node? > llm_2

  Action > done
  ✓ Saved 'summarizer' (4 nodes, 3 edges)
```

### Chat Without a Workflow

Type natural language at the prompt when no workflow is active. The CLI automatically creates a temporary single-node LLM workflow, runs it, and discards it:

```
> What is the capital of France?

  (no active workflow — using temporary LLM session)

  The capital of France is Paris.
```

When a workflow is active via `/use`, all input is routed through that workflow:

```
> /use summarizer
  ✓ Active workflow: summarizer

> The quick brown fox jumps over the lazy dog.
  Streaming...

  • A quick brown fox leaps over a lazy dog
  • This sentence is a well-known pangram
  • It is being used as a test input
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Tab` | Autocomplete commands, workflow names, node types |
| `Up/Down` | Navigate command history |
| `Ctrl+L` | Clear terminal |
| `Ctrl+C` | Cancel current input |
| `Ctrl+D` | Exit |

---

## Web UI

The web interface provides a visual drag-and-drop canvas for building workflows:

- **Canvas** — Drag nodes from the sidebar, connect them with edges
- **Node Configuration** — Click any node to configure its parameters
- **Real-time Streaming** — Watch token-by-token output as workflows execute
- **Dark Theme** — Full dark UI with node status animations
- **Toolbar** — Save, load, export, import, and example workflows

Access the web UI at **http://localhost:5173** after starting the server.

---

## Node Types

| Node | Category | Purpose |
|------|----------|---------|
| **Input** | Trigger | Starting point — text prompt, file upload, or schedule trigger |
| **Webhook** | Trigger | Receive data via HTTP webhook |
| **LLM** | AI | Send input to an Ollama or Groq model with custom system prompts |
| **Guardrails** | AI | Validate LLM output and route to valid/invalid paths |
| **Tool** | Tools | Execute tools: search, files, code, HTTP, email, browser |
| **Transform** | Tools | Regex, substring, case changes, JSON path, or templates |
| **Variable** | Tools | Store, retrieve, or modify reusable variables |
| **Custom** | Tools | Define custom Python logic |
| **Condition** | Logic | If/else branching with True/False output handles |
| **Switch** | Logic | Multi-way routing based on input value matching |
| **Loop** | Logic | Repeat an action N times or until a condition is met |
| **Merge** | Logic | Combine outputs from multiple upstream branches |
| **Delay** | Logic | Pause execution for a set number of seconds |
| **Sub-Workflow** | Logic | Nest another workflow inside this node |
| **Batch** | Logic | Process lists of inputs through a sub-pipeline |
| **Memory** | Memory | Remember, recall, search, or clear agent memory |
| **Output** | Output | End of workflow — displays the final result |
| **Webhook Output** | Output | Send workflow result to an external API |

---

## Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | Multi-engine search — DuckDuckGo, Bing, Brave, SearXNG with parallel fallback |
| `web_scraper` | Scrape a webpage and return clean text |
| `read_file` | Read txt, md, py, json, csv, pdf, docx, xlsx |
| `write_file` | Write content to files in the workspace |
| `run_code` | Execute Python code with timeout |
| `run_command` | Run shell commands (cross-platform) |
| `send_email` | Send emails via SMTP |
| `http_request` | REST API calls (GET, POST, PUT, DELETE, PATCH) |
| `calculate` | Evaluate math expressions |
| `get_datetime` | Get formatted current date/time |
| `playwright_browser` | Full browser automation (Chrome, Firefox, Safari, Edge) |
| `list_directory` | List files and folders with sizes |
| `search_files` | Search files by name or grep content |
| `json_query` | Extract values from JSON using dot-notation paths |
| `csv_analyze` | Analyze CSV files — summary stats, filter, sort, group |
| `database_query` | Execute SQL queries against SQLite databases |
| `random_generate` | Generate UUIDs, passwords, numbers, or strings |
| `diff_texts` | Compare two texts and show unified diff |
| `hash_data` | Generate SHA256, SHA1, or MD5 hashes |
| `rss_read` | Read and parse RSS feeds |

---

## API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/models` | GET | List available Ollama models |
| `/api/tools` | GET | List available tools |
| `/api/node-types` | GET | List node type definitions |
| `/api/run` | POST | Execute a workflow |
| `/ws/run` | WS | WebSocket for streaming execution logs |
| `/api/save` | POST | Save a workflow |
| `/api/load/{name}` | GET | Load a workflow |
| `/api/workflows` | GET | List saved workflows |
| `/api/workflows/{name}` | DELETE | Delete a workflow |
| `/api/workflows/{name}/versions` | GET | List version history |
| `/api/upload` | POST | Upload a file |
| `/api/schedule` | POST | Create a workflow schedule |
| `/api/settings` | GET/POST | Get or update settings |
| `/api/search/status` | GET | Check search provider configuration |
| `/api/search/test` | POST | Test search with a query |

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, FastAPI, LangChain, ChromaDB |
| **Frontend** | React, ReactFlow, TailwindCSS, Vite |
| **CLI** | Python, Rich, prompt_toolkit |
| **AI Engine** | Ollama (local), Groq (cloud), OpenAI, Anthropic |
| **Web Search** | DuckDuckGo, Bing, Brave API, SearXNG |
| **Real-time** | WebSocket streaming |
| **Memory** | JSON + ChromaDB vector search |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMAFLOW_URL` | `http://localhost:8000` | Server URL |
| `OLLAMAFLOW_API_TOKEN` | (empty) | API authentication token |
| `OLLAMAFLOW_CORS_ORIGINS` | `http://localhost:5173,...` | Allowed CORS origins |

### Web Search Configuration

OllamaFlow includes a multi-engine web search system with automatic fallback. Configure in **Settings** (gear icon) in the web UI:

| Provider | Free Quota | API Key | Notes |
|----------|-----------|---------|-------|
| **Auto** | Unlimited | No | Tries Brave → SearXNG → DuckDuckGo → Bing (parallel) |
| **Brave** | 2,000/month | Optional | Independent index, high quality |
| **SearXNG** | Unlimited | No | Self-hosted meta-search (Google + Bing + DDG) |
| **DuckDuckGo** | Unlimited | No | Default fallback, no setup needed |

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

---

## License

[MIT](LICENSE)
