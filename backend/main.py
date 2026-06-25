import json
import asyncio
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from node_registry import NODE_TYPES, TOOL_DEFINITIONS
from agent_runner import workflow_runner
from memory_manager import memory_manager
from workflow_store import workflow_store

app = FastAPI(title="OllamaFlow", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OLLAMA_BASE = "http://localhost:11434"


class WorkflowRunRequest(BaseModel):
    workflow: Dict


class WorkflowSaveRequest(BaseModel):
    name: str
    workflow: Dict


class MemorySaveRequest(BaseModel):
    namespace: str
    text: str
    memory_type: str = "long_term"


class MemoryRecallRequest(BaseModel):
    namespace: str
    memory_type: str = "long_term"


class MemoryClearRequest(BaseModel):
    namespace: str


@app.get("/api/models")
async def get_models():
    try:
        resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
        data = resp.json()
        models = [m["name"] for m in data.get("models", [])]
        return {"models": models, "status": "connected"}
    except Exception:
        return {"models": [], "status": "disconnected"}


@app.get("/api/tools")
async def get_tools():
    tools_list = []
    details = {}
    for name, t in TOOL_DEFINITIONS.items():
        tools_list.append(name)
        details[name] = {
            "description": t["description"],
            "params": t["params"]
        }
    return {"tools": tools_list, "details": details}


@app.get("/api/node-types")
async def get_node_types():
    return {"node_types": NODE_TYPES}


@app.post("/api/run")
async def run_workflow(request: WorkflowRunRequest):
    workflow = request.workflow
    if not workflow.get("nodes"):
        raise HTTPException(status_code=400, detail="Workflow has no nodes")
    result = await workflow_runner.run(workflow)
    return result


active_connections: List[WebSocket] = []


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        data = await websocket.receive_text()
        workflow = json.loads(data)
        if not workflow.get("nodes"):
            await websocket.send_json({"type": "error", "message": "Workflow has no nodes"})
            return

        async def send_log(log_entry):
            try:
                await websocket.send_json({
                    "type": "log",
                    "data": log_entry
                })
            except Exception:
                pass

        result = await workflow_runner.run(workflow, log_callback=send_log)
        await websocket.send_json({
            "type": "complete",
            "data": result
        })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e)
            })
        except Exception:
            pass
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)


@app.post("/api/save")
async def save_workflow(request: WorkflowSaveRequest):
    result = workflow_store.save(request.name, request.workflow)
    return {"message": result}


@app.get("/api/workflows")
async def list_workflows():
    return {"workflows": workflow_store.list_workflows()}


@app.get("/api/load/{name}")
async def load_workflow(name: str):
    workflow = workflow_store.load(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
    return {"workflow": workflow}


@app.delete("/api/workflows/{name}")
async def delete_workflow(name: str):
    result = workflow_store.delete(name)
    return {"message": result}


@app.post("/api/memory/save")
async def save_memory(request: MemorySaveRequest):
    result = memory_manager.save(request.namespace, request.text, request.memory_type)
    return {"message": result}


@app.post("/api/memory/recall")
async def recall_memory(request: MemoryRecallRequest):
    result = memory_manager.recall(request.namespace, request.memory_type)
    return {"result": result}


@app.delete("/api/memory/clear")
async def clear_memory(namespace: str = "default"):
    result = memory_manager.clear(namespace)
    return {"message": result}


@app.get("/api/health")
async def health():
    ollama_status = "connected"
    try:
        requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3)
    except Exception:
        ollama_status = "disconnected"
    return {
        "status": "ok",
        "ollama": ollama_status
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
