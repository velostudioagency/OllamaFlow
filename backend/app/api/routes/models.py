import time
import asyncio
import requests
from fastapi import APIRouter
from app.core.config import OLLAMA_BASE, MODEL_CACHE_TTL

router = APIRouter()
_model_cache = {"data": None, "timestamp": 0}


@router.get("/api/models")
async def get_models():
    global _model_cache
    now = time.time()
    if _model_cache["data"] and (now - _model_cache["timestamp"]) < MODEL_CACHE_TTL:
        return _model_cache["data"]
    try:
        def _fetch():
            return requests.get(f"{OLLAMA_BASE}/api/tags", timeout=5).json()
        data = await asyncio.to_thread(_fetch)
        models = [m["name"] for m in data.get("models", [])]
        result = {"models": models, "status": "connected"}
    except Exception:
        result = {"models": [], "status": "disconnected"}
    _model_cache["data"] = result
    _model_cache["timestamp"] = now
    return result


@router.get("/api/providers")
async def get_providers():
    from app.services.settings import settings_manager
    groq_key = settings_manager.get("groq_api_key", "")
    return {
        "providers": {
            "ollama": {"name": "Ollama (Local)", "requires_key": False},
            "groq": {"name": "Groq (Cloud)", "requires_key": True, "has_key": bool(groq_key)}
        }
    }
