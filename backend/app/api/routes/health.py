import asyncio
import requests
from fastapi import APIRouter
from app.core.config import OLLAMA_BASE

router = APIRouter()


@router.get("/api/health")
async def health():
    ollama_status = "connected"
    try:
        await asyncio.to_thread(lambda: requests.get(f"{OLLAMA_BASE}/api/tags", timeout=3))
    except Exception:
        ollama_status = "disconnected"
    return {"status": "ok", "ollama": ollama_status}
