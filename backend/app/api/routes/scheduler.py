import uuid
from fastapi import APIRouter
from app.api.schemas import ScheduleCreateRequest
from app.services.scheduler import scheduler_manager

router = APIRouter()


@router.post("/api/schedule")
async def create_schedule(request: ScheduleCreateRequest):
    schedule_id = uuid.uuid4().hex[:8]
    result = scheduler_manager.add_schedule(
        schedule_id=schedule_id,
        workflow=request.workflow,
        name=request.name,
        schedule_type=request.schedule_type,
        interval_minutes=request.interval_minutes,
        cron_expression=request.cron_expression,
        enabled=request.enabled
    )
    return {"message": result, "schedule_id": schedule_id}


@router.get("/api/schedules")
async def list_schedules():
    return {"schedules": scheduler_manager.list_schedules()}


@router.delete("/api/schedules/{schedule_id}")
async def delete_schedule(schedule_id: str):
    result = scheduler_manager.remove_schedule(schedule_id)
    return {"message": result}


@router.post("/api/schedules/{schedule_id}/toggle")
async def toggle_schedule(schedule_id: str):
    result = scheduler_manager.toggle_schedule(schedule_id)
    return {"message": result}
