from fastapi import APIRouter
from app.api.schemas import MemorySaveRequest, MemoryRecallRequest
from app.services.memory import memory_manager

router = APIRouter()


@router.post("/api/memory/save")
async def save_memory(request: MemorySaveRequest):
    result = memory_manager.save(request.namespace, request.text, request.memory_type)
    return {"message": result}


@router.post("/api/memory/recall")
async def recall_memory(request: MemoryRecallRequest):
    result = memory_manager.recall(request.namespace, request.memory_type)
    return {"result": result}


@router.delete("/api/memory/clear")
async def clear_memory(namespace: str = "default"):
    result = memory_manager.clear(namespace)
    return {"message": result}
