from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: str = "medium"
    difficulty: int = 2
    parent_id: Optional[int] = None
    start_time: Optional[datetime] = None
    due_time: Optional[datetime] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    priority: Optional[str] = None
    difficulty: Optional[int] = None
    status: Optional[str] = None
    progress: Optional[int] = None
    start_time: Optional[datetime] = None
    due_time: Optional[datetime] = None


class TaskOut(BaseModel):
    id: int
    project_id: int
    parent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    assignee_id: Optional[int] = None
    creator_id: int
    priority: str
    difficulty: int
    status: str
    progress: int
    progress_confidence: int
    start_time: Optional[datetime] = None
    due_time: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    assignee: Optional[dict] = None

    class Config:
        from_attributes = True


class MilestoneCreate(BaseModel):
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None


class MilestoneOut(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: str
    created_by_ai: int
    created_at: datetime

    class Config:
        from_attributes = True
