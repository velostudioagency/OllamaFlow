import json
import asyncio
import uuid
import os
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import requests
from node_registry import NODE_TYPES, TOOL_DEFINITIONS
from agent_runner import WorkflowRunner
from memory_manager import memory_manager
from workflow_store import workflow_store
from scheduler import scheduler_manager

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
        def _fetch():
            resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
            return resp.json()
        data = await asyncio.to_thread(_fetch)
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
    runner = WorkflowRunner()
    result = await runner.run(workflow)
    return result


active_connections: List[WebSocket] = []


@app.websocket("/ws/run")
async def websocket_run(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    runner = None
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

        async def send_stream(stream_data):
            try:
                await websocket.send_json({
                    "type": "stream",
                    "data": stream_data
                })
            except Exception:
                pass

        runner = WorkflowRunner()
        result = await runner.run(workflow, log_callback=send_log, stream_callback=send_stream)
        await websocket.send_json({
            "type": "complete",
            "data": result
        })
    except WebSocketDisconnect:
        if runner:
            runner.stop()
    except Exception as e:
        if runner:
            runner.stop()
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
        await asyncio.to_thread(lambda: requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3))
    except Exception:
        ollama_status = "disconnected"
    return {
        "status": "ok",
        "ollama": ollama_status
    }


UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


@app.post("/api/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        file_id = f"{uuid.uuid4().hex[:12]}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, file_id)
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
        return {"file_path": file_path, "filename": file.filename, "size": len(content)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


class ScheduleCreateRequest(BaseModel):
    workflow: Dict
    name: str
    schedule_type: str = "interval"
    interval_minutes: int = 60
    cron_expression: str = ""
    enabled: bool = True


@app.post("/api/schedule")
async def create_schedule(request: ScheduleCreateRequest):
    schedule_id = uuid.uuid4().hex[:8]
    result = scheduler_manager.add_schedule(
        schedule_id=schedule_id,
        workflow=request.workflow,
        name=request.name,
        schedule_type=request.schedule_type,
        interval_minutes=request.interval_minutes,
        cron_expression=request.cron_expression,
        enabled=request.enabled
    )
    return {"message": result, "schedule_id": schedule_id}


@app.get("/api/schedules")
async def list_schedules():
    return {"schedules": scheduler_manager.list_schedules()}


@app.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    result = scheduler_manager.remove_schedule(schedule_id)
    return {"message": result}


@app.post("/api/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    result = scheduler_manager.toggle_schedule(schedule_id)
    return {"message": result}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
