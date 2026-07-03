import json
import time
import hashlib
from typing import Dict
from fastapi import APIRouter, HTTPException
from app.api.schemas import WorkflowRunRequest, WorkflowSaveRequest, ImportUrlRequest, ExportRequest
from app.services.workflow_store import workflow_store
import requests

router = APIRouter()


@router.post("/api/run")
async def run_workflow(request: WorkflowRunRequest):
    workflow = request.workflow
    if not workflow.get("nodes"):
        raise HTTPException(status_code=400, detail="Workflow has no nodes")
    from app.core.runner import WorkflowRunner
    runner = WorkflowRunner()
    result = await runner.run(workflow)
    return result


@router.post("/api/save")
async def save_workflow(request: WorkflowSaveRequest):
    result = workflow_store.save(request.name, request.workflow)
    return {"message": result}


@router.get("/api/workflows")
async def list_workflows():
    return {"workflows": workflow_store.list_workflows()}


@router.get("/api/load/{name}")
async def load_workflow(name: str):
    workflow = workflow_store.load(name)
    if workflow is None:
        raise HTTPException(status_code=404, detail=f"Workflow '{name}' not found")
    return {"workflow": workflow}


@router.delete("/api/workflows/{name}")
async def delete_workflow(name: str):
    result = workflow_store.delete(name)
    return {"message": result}


@router.post("/api/import-url")
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


@router.post("/api/export")
async def export_workflow(request: ExportRequest):
    wf = request.workflow
    wf_json = json.dumps(wf, sort_keys=True, default=str)
    checksum = hashlib.sha256(wf_json.encode()).hexdigest()[:16]
    return {"workflow": wf, "checksum": checksum, "size_bytes": len(wf_json)}
