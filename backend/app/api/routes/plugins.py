from fastapi import APIRouter, HTTPException, Request
from app.services.plugins import PluginManager

router = APIRouter()
_plugin_manager = PluginManager()

try:
    _plugin_manager.load_all()
    _plugin_manager.apply_to_registry()
except Exception as e:
    print(f"[Plugin] Plugin loading error: {e}")


@router.get("/api/plugins")
async def get_plugins():
    plugins = _plugin_manager.registry.get_loaded_plugins()
    return {"plugins": plugins}


@router.post("/api/plugins/reload")
async def reload_plugins():
    _plugin_manager._loaded = False
    _plugin_manager.registry = PluginManager().registry
    try:
        _plugin_manager.load_all()
        _plugin_manager.apply_to_registry()
        return {"status": "ok", "plugins": _plugin_manager.registry.get_loaded_plugins()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Plugin reload failed: {e}")


@router.post("/api/plugins/create-template")
async def create_plugin_template(request: Request):
    body = await request.json()
    plugin_name = body.get("name", "my_plugin")
    from app.services.plugins import create_plugin_template
    path = create_plugin_template(plugin_name)
    return {"status": "ok", "path": path}
