import os
from fastapi import Request
from fastapi.responses import JSONResponse
from app.services.settings import settings_manager

AUTH_EXEMPT_PATHS = {"/api/health", "/docs", "/openapi.json", "/redoc"}


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


def get_cors_origins():
    _cors_from_settings = settings_manager.get("cors_origins", "")
    _cors_from_env = os.environ.get("OLLAMAFLOW_CORS_ORIGINS", "")
    _cors_str = _cors_from_env or _cors_from_settings or "http://localhost:5173,http://localhost:3000,127.0.0.1:5173"
    return [o.strip() for o in _cors_str.split(",") if o.strip()]
