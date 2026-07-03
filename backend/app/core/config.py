import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BACKEND_DIR / "data"
UPLOAD_DIR = BACKEND_DIR / "uploads"
WORKSPACE_DIR = BACKEND_DIR.parent / "workspace"
PLUGINS_DIR = BACKEND_DIR / "plugins"

OLLAMA_BASE = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMAFLOW_API_TOKEN = os.environ.get("OLLAMAFLOW_API_TOKEN", "")
OLLAMAFLOW_CORS_ORIGINS = os.environ.get("OLLAMAFLOW_CORS_ORIGINS", "")

MODEL_CACHE_TTL = 30

DATA_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
