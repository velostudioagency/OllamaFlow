from fastapi import APIRouter
from app.api.schemas import SettingsUpdateRequest, SearchTestRequest
from app.services.settings import settings_manager

router = APIRouter()


@router.get("/api/settings")
async def get_settings():
    return {"settings": settings_manager.get_all()}


@router.post("/api/settings")
async def update_settings(request: SettingsUpdateRequest):
    result = settings_manager.update(request.settings)
    return {"message": result}


@router.get("/api/search/status")
async def search_status():
    search_settings = settings_manager.get_search_settings()
    return {
        "provider": search_settings["search_provider"],
        "brave_configured": bool(search_settings["brave_api_key"]),
        "searxng_configured": bool(search_settings["searxng_url"]),
    }


@router.post("/api/search/test")
async def search_test(request: SearchTestRequest):
    from app.tools.search import web_search
    result = web_search(request.query, num_results=3)
    return {"results": result}
