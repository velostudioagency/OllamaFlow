from typing import Dict
from pydantic import BaseModel


class WorkflowRunRequest(BaseModel):
    workflow: Dict


class WorkflowSaveRequest(BaseModel):
    name: str
    workflow: Dict


class MemorySaveRequest(BaseModel):
    namespace: str
    text: str
    memory_type: str = "long_term"


class MemoryRecallRequest(BaseModel):
    namespace: str
    memory_type: str = "long_term"


class MemoryClearRequest(BaseModel):
    namespace: str


class ScheduleCreateRequest(BaseModel):
    workflow: Dict
    name: str
    schedule_type: str = "interval"
    interval_minutes: int = 60
    cron_expression: str = ""
    enabled: bool = True


class SettingsUpdateRequest(BaseModel):
    settings: Dict


class SearchTestRequest(BaseModel):
    query: str = "What is artificial intelligence?"


class VersionActionRequest(BaseModel):
    timestamp: str


class DiffRequest(BaseModel):
    timestamp1: str
    timestamp2: str


class ImportUrlRequest(BaseModel):
    url: str


class ExportRequest(BaseModel):
    workflow: Dict


class GeneratePdfRequest(BaseModel):
    content: str
