import os
import json
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from app.core.config import DATA_DIR
from app.api.schemas import VersionActionRequest, DiffRequest

router = APIRouter()


def _get_history_path():
    return DATA_DIR / "execution_history.json"


@router.get("/api/history")
async def get_execution_history(limit: int = 50):
    history_path = _get_history_path()
    if not history_path.exists():
        return {"history": []}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        return {"history": history[:limit]}
    except Exception:
        return {"history": []}


@router.delete("/api/history")
async def clear_execution_history():
    history_path = _get_history_path()
    if history_path.exists():
        os.remove(history_path)
    return {"message": "Execution history cleared."}


@router.get("/api/history/{run_id}")
async def get_run_detail(run_id: str):
    history_path = _get_history_path()
    if not history_path.exists():
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


@router.get("/api/versions/{name}")
async def list_versions(name: str):
    from app.services.workflow_store import workflow_store
    return {"versions": workflow_store.list_versions(name)}


@router.get("/api/versions/{name}/{timestamp}")
async def load_version(name: str, timestamp: str):
    from app.services.workflow_store import workflow_store
    data = workflow_store.load_version(name, timestamp)
    if data is None:
        raise HTTPException(status_code=404, detail="Version not found")
    return {"workflow": data}


@router.post("/api/versions/{name}/rollback")
async def rollback_version(name: str, request: VersionActionRequest):
    from app.services.workflow_store import workflow_store
    result = workflow_store.rollback(name, request.timestamp)
    return {"message": result}


@router.post("/api/versions/{name}/diff")
async def diff_versions(name: str, request: DiffRequest):
    from app.services.workflow_store import workflow_store
    diff = workflow_store.diff_versions(name, request.timestamp1, request.timestamp2)
    return {"diff": diff}


@router.get("/api/logs/export")
async def export_logs(format: str = "json"):
    history_path = _get_history_path()
    if not history_path.exists():
        return {"logs": []}
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
        all_logs = []
        for run in history:
            for log in run.get("logs", []):
                all_logs.append({"run_id": run.get("id", ""), "workflow": run.get("workflow_name", ""), **log})
        if format == "json":
            return JSONResponse(content=all_logs)
        elif format == "csv":
            lines = ["timestamp,run_id,workflow,node_id,node_type,status,message"]
            for log in all_logs:
                msg = log.get("message", "").replace('"', '""')
                lines.append(f'"{log.get("timestamp","")}","{log.get("run_id","")}","{log.get("workflow","")}","{log.get("node_id","")}","{log.get("node_type","")}","{log.get("status","")}","{msg}"')
            csv_content = "\n".join(lines)
            return StreamingResponse(iter([csv_content]), media_type="text/csv",
                                     headers={"Content-Disposition": "attachment; filename=logs.csv"})
        return {"logs": all_logs}
    except Exception:
        return {"logs": []}
