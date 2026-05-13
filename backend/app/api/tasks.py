from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import ProjectMember
from app.models.task import Task, TaskDependency, Milestone
from app.models.collaboration import CollaborationEvent
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut, MilestoneCreate, MilestoneOut

router = APIRouter(prefix="/api", tags=["tasks"])


def _check_member(db, project_id, user_id, roles=None):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    if roles and member.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return member


def _emit_event(db, project_id, actor_id, event_type, target_type, target_id, summary, weight=1.0):
    event = CollaborationEvent(
        project_id=project_id,
        actor_id=actor_id,
        event_type=event_type,
        target_type="task",
        target_id=target_id,
        summary=summary,
        contribution_weight=weight,
    )
    db.add(event)


@router.get("/projects/{project_id}/tasks", response_model=List[TaskOut])
def list_tasks(project_id: int, status: Optional[str] = None, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    q = db.query(Task).filter(Task.project_id == project_id)
    if status:
        q = q.filter(Task.status == status)
    tasks = q.order_by(Task.created_at.desc()).all()
    result = []
    for t in tasks:
        t_dict = TaskOut.model_validate(t).model_dump()
        if t.assignee_id:
            assignee = db.query(User).filter(User.id == t.assignee_id).first()
            if assignee:
                t_dict["assignee"] = {"id": assignee.id, "nickname": assignee.nickname, "avatar_url": assignee.avatar_url}
        result.append(t_dict)
    return result


@router.post("/projects/{project_id}/tasks", response_model=TaskOut)
def create_task(project_id: int, data: TaskCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    task = Task(project_id=project_id, creator_id=current_user.id, **data.model_dump())
    db.add(task)
    db.flush()
    _emit_event(db, project_id, current_user.id, "TaskCreated", "task", task.id, f"创建任务：{task.title}", 0.5)
    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.get("/tasks/{task_id}", response_model=TaskOut)
def get_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _check_member(db, task.project_id, current_user.id)
    t_dict = TaskOut.model_validate(task).model_dump()
    if task.assignee_id:
        assignee = db.query(User).filter(User.id == task.assignee_id).first()
        if assignee:
            t_dict["assignee"] = {"id": assignee.id, "nickname": assignee.nickname, "avatar_url": assignee.avatar_url}
    return t_dict


@router.put("/tasks/{task_id}", response_model=TaskOut)
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _check_member(db, task.project_id, current_user.id)

    old_status = task.status
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(task, key, val)

    # Set completed_at when done
    if data.status == "DONE" and old_status != "DONE":
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
        _emit_event(db, task.project_id, current_user.id, "ReviewPassed", "task", task.id, f"完成任务：{task.title}", 2.0)
    elif data.status and data.status != old_status:
        _emit_event(db, task.project_id, current_user.id, "ProgressUpdated", "task", task.id,
                    f"任务 [{task.title}] 状态更新为 {data.status}", 0.8)
    elif data.progress is not None:
        _emit_event(db, task.project_id, current_user.id, "ProgressUpdated", "task", task.id,
                    f"任务 [{task.title}] 进度更新为 {data.progress}%", 0.5)

    db.commit()
    db.refresh(task)
    return TaskOut.model_validate(task)


@router.delete("/tasks/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _check_member(db, task.project_id, current_user.id, roles=["leader"])
    task.status = "ARCHIVED"
    db.commit()
    return {"message": "Task archived"}


@router.put("/tasks/{task_id}/status")
def update_task_status(task_id: int, status: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    _check_member(db, task.project_id, current_user.id)
    task.status = status
    if status == "DONE":
        task.completed_at = datetime.now(timezone.utc).replace(tzinfo=None)
    db.commit()
    return {"message": "Status updated", "status": status}


@router.get("/projects/{project_id}/milestones", response_model=List[MilestoneOut])
def list_milestones(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    return [MilestoneOut.model_validate(m) for m in db.query(Milestone).filter(Milestone.project_id == project_id).all()]


@router.post("/projects/{project_id}/milestones", response_model=MilestoneOut)
def create_milestone(project_id: int, data: MilestoneCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])
    ms = Milestone(project_id=project_id, **data.model_dump())
    db.add(ms)
    db.commit()
    db.refresh(ms)
    return MilestoneOut.model_validate(ms)
