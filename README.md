# OllamaFlow

A visual, node-based workflow builder for creating and running local Ollama AI agents.

## Prerequisites

- Python 3.10+
- Node.js 18+
- Ollama running locally on port 11434

## Quick Start

### 1. Install Ollama

Download from [ollama.ai](https://ollama.ai) and pull a model:

```bash
ollama pull llama3.1:8b
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### 4. Open

Visit http://localhost:5173

## Usage

1. **Drag nodes** from the left sidebar onto the canvas
2. **Connect nodes** by dragging from one handle to another
3. **Configure nodes** by clicking them and editing the right panel
4. **Run workflows** with the green Run button in the toolbar
5. **Save/Load** workflows as JSON files
6. **Try examples** from the Examples dropdown

## Node Types

| Node | Color | Description |
|------|-------|-------------|
| Input | Blue | Starting point - provides initial prompt |
| LLM | Purple | Sends input to an Ollama model |
| Tool | Orange | Web search, file I/O, code execution |
| Memory | Green | Short-term or long-term agent memory |
| Condition | Yellow | If/else branching logic |
| Loop | Pink | Repeat action N times |
| Agent | Red | Full autonomous agent with tools |
| Output | Gray | End of workflow - shows result |

## API Endpoints

- `GET /api/models` - List available Ollama models
- `GET /api/tools` - List available tools
- `POST /api/run` - Execute a workflow
- `WS /ws/run` - WebSocket for streaming execution logs
- `POST /api/save` - Save workflow
- `GET /api/load/{name}` - Load workflow
- `GET /api/workflows` - List saved workflows

## Tech Stack

- **Backend**: Python, FastAPI, LangChain, ChromaDB
- **Frontend**: React, ReactFlow, TailwindCSS, Axios
- **AI Engine**: Ollama (local LLM inference)
