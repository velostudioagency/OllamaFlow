import json
import asyncio
import uuid
import os
import time
import hashlib
from typing import Dict, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import requests
from node_registry import NODE_TYPES, TOOL_DEFINITIONS
from agent_runner import WorkflowRunner
from memory_manager import memory_manager
from workflow_store import workflow_store
from scheduler import scheduler_manager
from settings_manager import settings_manager
from plugin_loader import PluginManager

app = FastAPI(title="OllamaFlow", version="1.0.0")

# Load plugins at startup
_plugin_manager = PluginManager()
try:
    _plugin_manager.load_all()
    _plugin_manager.apply_to_registry()
except Exception as e:
    print(f"[Plugin] Plugin loading error: {e}")

_cors_from_settings = settings_manager.get("cors_origins", "")
_cors_from_env = os.environ.get("OLLAMAFLOW_CORS_ORIGINS", "")
_cors_str = _cors_from_env or _cors_from_settings or "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173"
allowed_origins = [o.strip() for o in _cors_str.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

OLLAMA_BASE = "http://localhost:11434"

AUTH_EXEMPT_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}

_model_cache = {"data": None, "timestamp": 0}
MODEL_CACHE_TTL = 30


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    if request.url.path in AUTH_EXEMPT_PATHS or request.url.path.startswith("/ws/"):
        return await call_next(request)
    api_token = settings_manager.get("api_token", "") or os.environ.get("OLLAMAFLOW_API_TOKEN", "")
    if not api_token:
        return await call_next(request)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer ") and auth_header[7:] == api_token:
        return await call_next(request)
    return JSONResponse(status_code=401, content={"detail": "Invalid or missing API token"})


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
    global _model_cache
    now = time.time()
    if _model_cache["data"] and (now - _model_cache["timestamp"]) < MODEL_CACHE_TTL:
        return _model_cache["data"]
    try:
        def _fetch():
            resp = requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5)
            return resp.json()
        data = await asyncio.to_thread(_fetch)
        models = [m["name"] for m in data.get("models", [])]
        result = {"models": models, "status": "connected"}
        _model_cache["data"] = result
        _model_cache["timestamp"] = now
        return result
    except Exception:
        result = {"models": [], "status": "disconnected"}
        _model_cache["data"] = result
        _model_cache["timestamp"] = now
        return result


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


@app.get("/api/plugins")
async def get_plugins():
    """List loaded plugins."""
    plugins = _plugin_manager.registry.get_loaded_plugins()
    return {"plugins": plugins}


@app.post("/api/plugins/reload")
async def reload_plugins():
    """Reload all plugins."""
    _plugin_manager._loaded = False
    _plugin_manager.registry = PluginManager().registry
    try:
        _plugin_manager.load_all()
        _plugin_manager.apply_to_registry()
        return {"status": "ok", "plugins": _plugin_manager.registry.get_loaded_plugins()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin reload failed: {e}")


@app.post("/api/plugins/create-template")
async def create_plugin_template(request: Request):
    """Create a new plugin template."""
    body = await request.json()
    plugin_name = body.get("name", "my_plugin")
    from plugin_loader import create_plugin_template
    path = create_plugin_template(plugin_name)
    return {"status": "ok", "path": path}


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
    stop_received = asyncio.Event()
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

        async def listen_for_stop():
            try:
                while not stop_received.is_set():
                    msg = await websocket.receive_text()
                    parsed = json.loads(msg)
                    if parsed.get("type") == "stop":
                        runner.stop()
                        stop_received.set()
                        return
            except (WebSocketDisconnect, Exception):
                stop_received.set()

        listener = asyncio.create_task(listen_for_stop())
        result = await runner.run(workflow, log_callback=send_log, stream_callback=send_stream)
        listener.cancel()
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


class SettingsUpdateRequest(BaseModel):
    settings: Dict


@app.get("/api/settings")
async def get_settings():
    return {"settings": settings_manager.get_all()}


@app.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    result = settings_manager.update(request.settings)
    return {"message": result}


@app.get("/api/providers")
async def get_providers():
    groq_key = settings_manager.get("groq_api_key", "")
    return {
        "providers": {
            "ollama": {"name": "Ollama (Local)", "requires_key": False},
            "groq": {"name": "Groq (Cloud)", "requires_key": True, "has_key": bool(groq_key)}
        }
    }


@app.get("/api/search/status")
async def search_status():
    search_settings = settings_manager.get_search_settings()
    return {
        "provider": search_settings["search_provider"],
        "brave_configured": bool(search_settings["brave_api_key"]),
        "searxng_configured": bool(search_settings["searxng_url"]),
    }


class SearchTestRequest(BaseModel):
    query: str = "What is artificial intelligence?"


@app.post("/api/search/test")
async def search_test(request: SearchTestRequest):
    from tool_library import web_search
    result = web_search(request.query, num_results=3)
    return {"results": result}


@app.websocket("/ws/chat/run")
async def websocket_chat_run(websocket: WebSocket):
    await websocket.accept()
    runner = None
    stop_received = asyncio.Event()
    try:
        data = await websocket.receive_text()
        payload = json.loads(data)
        workflow = payload.get("workflow", {})
        text = payload.get("text", "")
        file_path = payload.get("file_path")

        if not workflow.get("nodes"):
            await websocket.send_json({"type": "error", "message": "No workflow loaded. Build a workflow on the canvas first."})
            return

        input_text = text
        if file_path:
            try:
                from tool_library import read_file
                content = await asyncio.to_thread(read_file, file_path)
                input_text = f"File content:\n\n{content}\n\nUser request: {text}"
            except Exception:
                input_text = f"File: {file_path}\nUser request: {text}"

        if input_text:
            input_nodes = [n for n in workflow["nodes"] if n.get("type") == "input"]
            for node in input_nodes:
                node.setdefault("config", {})
                node["config"]["prompt"] = input_text

        start_time = time.time()
        runner = WorkflowRunner()

        async def send_log(log_entry):
            try:
                await websocket.send_json({"type": "log", "data": log_entry})
            except Exception:
                pass

        async def send_stream(stream_data):
            try:
                await websocket.send_json({"type": "stream", "data": stream_data})
            except Exception:
                pass

        async def listen_for_stop():
            try:
                while not stop_received.is_set():
                    msg = await websocket.receive_text()
                    parsed = json.loads(msg)
                    if parsed.get("type") == "stop":
                        runner.stop()
                        stop_received.set()
                        return
            except (WebSocketDisconnect, Exception):
                stop_received.set()

        listener = asyncio.create_task(listen_for_stop())
        result = await runner.run(workflow, log_callback=send_log, stream_callback=send_stream)
        listener.cancel()
        elapsed = round(time.time() - start_time, 1)
        result["duration"] = elapsed
        await websocket.send_json({"type": "complete", "data": result})
    except WebSocketDisconnect:
        if runner:
            runner.stop()
    except Exception as e:
        if runner:
            runner.stop()
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


@app.get("/api/versions/{name}")
async def list_versions(name: str):
    return {"versions": workflow_store.list_versions(name)}


class VersionActionRequest(BaseModel):
    timestamp: str


@app.get("/api/versions/{name}/{timestamp}")
async def load_version(name: str, timestamp: str):
    data = workflow_store.load_version(name, timestamp)
    if data is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"workflow": data}


@app.post("/api/versions/{name}/rollback")
async def rollback_version(name: str, request: VersionActionRequest):
    result = workflow_store.rollback(name, request.timestamp)
    return {"message": result}


class DiffRequest(BaseModel):
    timestamp1: str
    timestamp2: str


@app.post("/api/versions/{name}/diff")
async def diff_versions(name: str, request: DiffRequest):
    diff = workflow_store.diff_versions(name, request.timestamp1, request.timestamp2)
    return {"diff": diff}


class ImportUrlRequest(BaseModel):
    url: str


@app.post("/api/import-url")
async def import_from_url(request: ImportUrlRequest):
    try:
        resp = requests.get(request.url, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if "nodes" in data and "edges" in data:
            return {"workflow": data, "name": data.get("name", "Imported Workflow")}
        elif "name" in data and "workflow" in data:
            return {"workflow": data["workflow"], "name": data["name"]}
        else:
            raise HTTPException(status_code=400, detail="URL does not contain a valid workflow")
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch: {str(e)}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Response is not valid JSON")


class ExportRequest(BaseModel):
    workflow: Dict


@app.post("/api/export")
async def export_workflow(request: ExportRequest):
    wf = request.workflow
    wf_json = json.dumps(wf, sort_keys=True, default=str)
    checksum = hashlib.sha256(wf_json.encode()).hexdigest()[:16]
    return {
        "workflow": wf,
        "checksum": checksum,
        "size_bytes": len(wf_json)
    }


@app.get("/api/history")
async def get_execution_history(limit: int = 50):
    history_path = os.path.join(os.path.dirname(__file__), "data", "execution_history.json")
    if not os.path.exists(history_path):
        return {"history": []}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        return {"history": history[:limit]}
    except Exception:
        return {"history": []}


@app.delete("/api/history")
async def clear_execution_history():
    history_path = os.path.join(os.path.dirname(__file__), "data", "execution_history.json")
    if os.path.exists(history_path):
        os.remove(history_path)
    return {"message": "Execution history cleared."}


@app.get("/api/history/{run_id}")
async def get_run_detail(run_id: str):
    history_path = os.path.join(os.path.dirname(__file__), "data", "execution_history.json")
    if not os.path.exists(history_path):
        raise HTTPException(status_code=404, detail="No history found")
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        for run in history:
            if run.get("id") == run_id:
                return {"run": run}
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading history")


@app.get("/api/logs/export")
async def export_logs(format: str = "json"):
    history_path = os.path.join(os.path.dirname(__file__), "data", "execution_history.json")
    if not os.path.exists(history_path):
        return {"logs": []}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        all_logs = []
        for run in history:
            for log in run.get("logs", []):
                all_logs.append({
                    "run_id": run.get("id", ""),
                    "workflow": run.get("workflow_name", ""),
                    **log
                })
        if format == "json":
            return JSONResponse(content=all_logs)
        elif format == "csv":
            lines = ["timestamp,run_id,workflow,node_id,node_type,status,message"]
            for log in all_logs:
                msg = log.get("message", "").replace('"', '""')
                lines.append(f'"{log.get("timestamp","")}","{log.get("run_id","")}","{log.get("workflow","")}","{log.get("node_id","")}","{log.get("node_type","")}","{log.get("status","")}","{msg}"')
            csv_content = "\n".join(lines)
            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=logs.csv"}
            )
        return {"logs": all_logs}
    except Exception:
        return {"logs": []}


class GeneratePdfRequest(BaseModel):
    content: str


@app.post("/api/generate-pdf")
async def generate_pdf(request: GeneratePdfRequest):
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.units import inch
        import io

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                topMargin=0.5 * inch, bottomMargin=0.5 * inch,
                                leftMargin=0.75 * inch, rightMargin=0.75 * inch)
        styles = getSampleStyleSheet()
        body_style = ParagraphStyle("Body", parent=styles["Normal"], fontSize=10, leading=14)
        story = []

        for line in request.content.split("\n"):
            if not line.strip():
                story.append(Spacer(1, 6))
            else:
                safe = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                story.append(Paragraph(safe, body_style))

        if not story:
            story = [Paragraph("Empty document", body_style)]

        doc.build(story)
        buffer.seek(0)
        return StreamingResponse(buffer, media_type="application/pdf",
                                 headers={"Content-Disposition": "attachment; filename=output.pdf"})
    except ImportError:
        raise HTTPException(status_code=500, detail="reportlab not installed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
