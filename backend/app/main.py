from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.middleware import auth_middleware, get_cors_origins
from app.api.routes import health, models, workflows, tools_and_nodes, memory, scheduler, settings, plugins, files, history, pdf
from app.websocket.handlers import websocket_run, websocket_chat_run

app = FastAPI(title="OllamaFlow", version="1.0.0")

# Middleware
app.middleware("http")(auth_middleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

# API Routes
app.include_router(health.router)
app.include_router(models.router)
app.include_router(workflows.router)
app.include_router(tools_and_nodes.router)
app.include_router(memory.router)
app.include_router(scheduler.router)
app.include_router(settings.router)
app.include_router(plugins.router)
app.include_router(files.router)
app.include_router(history.router)
app.include_router(pdf.router)

# WebSocket Routes
app.websocket("/ws/run")(websocket_run)
app.websocket("/ws/chat/run")(websocket_chat_run)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
