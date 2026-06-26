# Contributing to OllamaFlow

Thanks for your interest in contributing to OllamaFlow! Here's how to get started.

## Development Setup

1. **Fork and clone the repo**
   ```bash
   git clone https://github.com/YOUR_USERNAME/OllamaFlow.git
   cd OllamaFlow
   ```

2. **Install dependencies**
   ```bash
   # Windows
   install.bat

   # macOS / Linux
   cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
   cd ../frontend && npm install
   ```

3. **Start development servers**
   ```bash
   # Windows
   start.bat

   # macOS / Linux
   cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000 &
   cd frontend && npm run dev
   ```

4. **Open** http://localhost:5173

## Project Structure

```
ollamaflow/
├── backend/
│   ├── main.py              # FastAPI app + API routes
│   ├── agent_runner.py      # Workflow execution engine
│   ├── node_registry.py     # Node type definitions
│   ├── tool_library.py      # Tool implementations
│   ├── memory_manager.py    # Short/long-term memory
│   ├── workflow_store.py    # Save/load workflows
│   ├── scheduler.py         # Workflow scheduling
│   └── settings_manager.py  # App settings
└── frontend/
    └── src/
        ├── App.jsx           # Main ReactFlow canvas
        └── components/       # UI components
```

## Adding a New Node Type

1. Define the node in `backend/node_registry.py` under `NODE_TYPES`
2. Add the handler in `node_registry.py` or `agent_runner.py`
3. Create a React component in `frontend/src/components/nodes/`
4. Register it in `frontend/src/App.jsx`

## Adding a New Tool

1. Implement the function in `backend/tool_library.py`
2. Register it in `TOOL_DEFINITIONS` in `backend/node_registry.py`
3. Add it to the `TOOL_HANDLERS` dict

## Code Style

- **Python**: Follow PEP 8, use type hints
- **JavaScript/JSX**: Use functional components, hooks, and modern ES6+ syntax
- Keep node handlers async where possible
- Use the existing logging pattern for execution output

## Pull Requests

1. Create a feature branch from `main`
2. Make your changes
3. Test with a workflow that exercises your changes
4. Submit a PR with a clear description

## Issues

Found a bug or have a feature request? Open an issue on GitHub with:
- Steps to reproduce (for bugs)
- Expected vs actual behavior
- Your environment (OS, Python version, Ollama version)
