from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from app.core.database import Base


class Task(Base):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("task.id"), nullable=True)
    title = Column(String(256), nullable=False)
    description = Column(Text, nullable=True)
    assignee_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    priority = Column(String(16), nullable=False, default="medium")  # low, medium, high, critical
    difficulty = Column(Integer, nullable=False, default=2)  # 1-5
    # TODO, IN_PROGRESS, BLOCKED, REVIEW, DONE, ARCHIVED
    status = Column(String(32), nullable=False, default="TODO")
    progress = Column(Integer, nullable=False, default=0)  # 0-100
    progress_confidence = Column(Integer, nullable=False, default=100)
    start_time = Column(DateTime, nullable=True)
    due_time = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class TaskDependency(Base):
    __tablename__ = "task_dependency"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    depends_on_task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    dependency_type = Column(String(32), nullable=False, default="finish_to_start")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class Milestone(Base):
    __tablename__ = "milestone"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime, nullable=True)
    status = Column(String(32), nullable=False, default="pending")
    created_by_ai = Column(Integer, nullable=False, default=0)  # 0=manual, 1=ai
    created_at = Column(DateTime, nullable=False, server_default=func.now())
