from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, date


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    course_name: Optional[str] = None
    teacher_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deadline: Optional[datetime] = None


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    cover_url: Optional[str] = None
    course_name: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deadline: Optional[datetime] = None
    status: Optional[str] = None


class ProjectOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    cover_url: Optional[str] = None
    owner_id: int
    course_name: Optional[str] = None
    teacher_id: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    deadline: Optional[datetime] = None
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectMemberOut(BaseModel):
    id: int
    project_id: int
    user_id: int
    role: str
    skill_tags: Optional[str] = None
    joined_at: datetime
    status: str
    user: Optional[dict] = None

    class Config:
        from_attributes = True


class InviteMember(BaseModel):
    user_id: int
    role: str = "member"
    skill_tags: Optional[str] = None


class ProjectDashboard(BaseModel):
    project: ProjectOut
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    overdue_tasks: int
    completion_rate: float
    member_count: int
    doc_count: int
    message_count: int
    event_count: int
    recent_events: List[dict] = []
    risk_alerts: List[dict] = []
    member_contributions: List[dict] = []
