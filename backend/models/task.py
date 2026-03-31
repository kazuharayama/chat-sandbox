from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TaskInfo(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    status: str  # todo, in_progress, done
    sort_order: int = 0
    created_at: datetime
    updated_at: datetime


class TaskCreateRequest(BaseModel):
    title: str
    description: Optional[str] = None
    status: str = "todo"


class TaskUpdateRequest(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    sort_order: Optional[int] = None
