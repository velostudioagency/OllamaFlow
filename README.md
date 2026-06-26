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

## Features

- **8 Node Types** — Input, LLM, Tool, Memory, Condition, Loop, Agent, Output
- **10 Built-in Tools** — Web search, file I/O, code execution, browser automation, HTTP requests, and more
- **Multi-Engine Web Search** — Parallel search across DuckDuckGo, Bing, Brave, and SearXNG with auto-fallback
- **Dual AI Providers** — Ollama (local) and Groq (cloud) with live switching
- **Real-time Streaming** — Token-by-token output via WebSocket as workflows execute
- **Visual Canvas** — Drag-and-drop ReactFlow interface with minimap and controls
- **Persistent Memory** — Short-term and long-term memory backed by ChromaDB vector search
- **Save & Load** — Export/import workflows as JSON files
- **Schedule Workflows** — Run workflows on intervals automatically
- **File Upload** — Attach files directly to workflow inputs
- **Dark Theme** — Full dark UI with node status animations

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+
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

# Frontend
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

Open **http://localhost:5173**

## Node Types

| Node | Color | Purpose |
|------|-------|---------|
| **Input** | Blue | Starting point — text prompt, file upload, or schedule trigger |
| **LLM** | Purple | Send input to an Ollama or Groq model with custom system prompts |
| **Tool** | Orange | Execute tools: search, files, code, HTTP, email, browser automation |
| **Memory** | Green | Remember, recall, search, or clear agent memory |
| **Condition** | Yellow | If/else branching with True/False output handles |
| **Loop** | Pink | Repeat an action N times with optional stop conditions |
| **Agent** | Red | Full autonomous agent — LLM + tools + multi-step reasoning loop |
| **Output** | Gray | End of workflow — displays the final result |

## Built-in Tools

| Tool | Description |
|------|-------------|
| `web_search` | Multi-engine search — DuckDuckGo, Bing, Brave, SearXNG with parallel fallback |
| `read_file` | Read txt, md, py, json, csv, pdf, docx, xlsx |
| `write_file` | Write content to files in the workspace |
| `run_code` | Execute Python code with timeout |
| `run_command` | Run shell commands (cross-platform) |
| `send_email` | Send emails via SMTP |
| `http_request` | REST API calls (GET, POST, PUT, DELETE, PATCH) |
| `calculate` | Evaluate math expressions |
| `get_datetime` | Get formatted current date/time |
| `playwright_browser` | Full browser automation (Chrome, Firefox, Safari, etc.) |

## Example Workflows

OllamaFlow ships with example workflows you can load from the toolbar:

- **Web Research Agent** — Search the web, extract info, and summarize findings
- **File Summarizer** — Read a file and generate a summary
- **Multi-Step Research Report** — End-to-end research pipeline with web search + LLM analysis

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/models` | GET | List available Ollama models |
| `/api/tools` | GET | List available tools |
| `/api/node-types` | GET | List node type definitions |
| `/api/run` | POST | Execute a workflow |
| `/ws/run` | WS | WebSocket for streaming execution logs |
| `/api/save` | POST | Save a workflow |
| `/api/load/{name}` | GET | Load a workflow |
| `/api/workflows` | GET | List saved workflows |
| `/api/upload` | POST | Upload a file |
| `/api/schedule` | POST | Create a workflow schedule |
| `/api/settings` | GET/POST | Get or update settings |
| `/api/search/status` | GET | Check search provider configuration |
| `/api/search/test` | POST | Test search with a query |
| `/api/health` | GET | Health check |

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python, FastAPI, LangChain, ChromaDB |
| **Frontend** | React, ReactFlow, TailwindCSS, Vite |
| **AI Engine** | Ollama (local), Groq (cloud) |
| **Web Search** | DuckDuckGo, Bing RSS, Brave API, SearXNG |
| **Real-time** | WebSocket streaming |
| **Memory** | JSON + ChromaDB vector search |

## Web Search Configuration

OllamaFlow includes a multi-engine web search system with automatic fallback. Configure in **Settings** (gear icon):

| Provider | Free Quota | API Key | Notes |
|----------|-----------|---------|-------|
| **Auto** | Unlimited | No | Tries Brave → SearXNG → DuckDuckGo → Bing (parallel) |
| **Brave** | 2,000/month | Optional | Independent index, high quality |
| **SearXNG** | Unlimited | No | Self-hosted meta-search (Google + Bing + DDG) |
| **DuckDuckGo** | Unlimited | No | Default fallback, no setup needed |

**Auto mode** runs all available engines in parallel, deduplicates results by URL, and returns the top matches. No configuration required — it works out of the box.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for setup instructions and guidelines.

## License

[MIT](LICENSE)
