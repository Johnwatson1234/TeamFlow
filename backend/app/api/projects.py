from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.document import Document
from app.models.message import Message
from app.models.collaboration import CollaborationEvent, RiskAlert, ContributionScore
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectOut, ProjectMemberOut,
    InviteMember, ProjectDashboard
)

router = APIRouter(prefix="/api/projects", tags=["projects"])


def _check_member(db, project_id, user_id, roles=None):
    q = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    )
    member = q.first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    if roles and member.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return member


@router.post("", response_model=ProjectOut)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    project = Project(owner_id=current_user.id, **data.model_dump())
    db.add(project)
    db.flush()
    # Add creator as leader
    member = ProjectMember(project_id=project.id, user_id=current_user.id, role="leader")
    db.add(member)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.get("", response_model=List[ProjectOut])
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    memberships = db.query(ProjectMember).filter(
        ProjectMember.user_id == current_user.id,
        ProjectMember.status == "active"
    ).all()
    project_ids = [m.project_id for m in memberships]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).order_by(Project.updated_at.desc()).all()
    return [ProjectOut.model_validate(p) for p in projects]


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut.model_validate(project)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, data: ProjectUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(project, key, val)
    db.commit()
    db.refresh(project)
    return ProjectOut.model_validate(project)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    project.status = "archived"
    db.commit()
    return {"message": "Project archived"}


@router.get("/{project_id}/members")
def list_members(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    members = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.status == "active"
    ).all()
    result = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        result.append({
            "id": m.id,
            "project_id": m.project_id,
            "user_id": m.user_id,
            "role": m.role,
            "skill_tags": m.skill_tags,
            "joined_at": m.joined_at.isoformat(),
            "status": m.status,
            "user": {
                "id": user.id,
                "username": user.username,
                "nickname": user.nickname,
                "avatar_url": user.avatar_url,
                "email": user.email,
            } if user else None
        })
    return result


@router.post("/{project_id}/members")
def invite_member(project_id: int, data: InviteMember, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])
    # Check if already member
    existing = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == data.user_id
    ).first()
    if existing:
        existing.status = "active"
        existing.role = data.role
        db.commit()
        return {"message": "Member re-activated"}
    member = ProjectMember(
        project_id=project_id,
        user_id=data.user_id,
        role=data.role,
        skill_tags=data.skill_tags,
    )
    db.add(member)
    db.commit()
    return {"message": "Member invited"}


@router.delete("/{project_id}/members/{user_id}")
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id
    ).first()
    if member:
        member.status = "inactive"
        db.commit()
    return {"message": "Member removed"}


@router.get("/{project_id}/dashboard")
def get_dashboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Task stats
    all_tasks = db.query(Task).filter(Task.project_id == project_id, Task.parent_id == None).all()
    total = len(all_tasks)
    completed = sum(1 for t in all_tasks if t.status == "DONE")
    in_progress = sum(1 for t in all_tasks if t.status == "IN_PROGRESS")
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    overdue = sum(1 for t in all_tasks if t.due_time and t.due_time < now and t.status not in ("DONE", "ARCHIVED"))

    # Counts
    doc_count = db.query(Document).filter(Document.project_id == project_id, Document.is_deleted == 0).count()
    msg_count = db.query(Message).filter(Message.project_id == project_id, Message.is_deleted == 0).count()
    event_count = db.query(CollaborationEvent).filter(CollaborationEvent.project_id == project_id).count()
    member_count = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").count()

    # Recent events (last 20)
    recent_events = db.query(CollaborationEvent).filter(
        CollaborationEvent.project_id == project_id
    ).order_by(CollaborationEvent.created_at.desc()).limit(20).all()

    events_data = []
    for e in recent_events:
        actor = db.query(User).filter(User.id == e.actor_id).first()
        events_data.append({
            "id": e.id,
            "event_type": e.event_type,
            "summary": e.summary,
            "actor": {"id": actor.id, "nickname": actor.nickname, "avatar_url": actor.avatar_url} if actor else None,
            "created_at": e.created_at.isoformat(),
            "target_type": e.target_type,
            "target_id": e.target_id,
        })

    # Risk alerts
    risks = db.query(RiskAlert).filter(
        RiskAlert.project_id == project_id, RiskAlert.status == "open"
    ).order_by(RiskAlert.risk_score.desc()).limit(5).all()
    risk_data = [{"id": r.id, "risk_type": r.risk_type, "risk_level": r.risk_level, "reason": r.reason, "suggestion": r.suggestion} for r in risks]

    # Member contributions
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").all()
    contrib_data = []
    for m in members:
        score = db.query(ContributionScore).filter(
            ContributionScore.project_id == project_id,
            ContributionScore.user_id == m.user_id
        ).first()
        user = db.query(User).filter(User.id == m.user_id).first()
        contrib_data.append({
            "user_id": m.user_id,
            "nickname": user.nickname if user else "",
            "avatar_url": user.avatar_url if user else None,
            "role": m.role,
            "total_score": float(score.total_score) if score else 0,
        })

    completion_rate = round((completed / total * 100) if total > 0 else 0, 1)

    return {
        "project": ProjectOut.model_validate(project),
        "total_tasks": total,
        "completed_tasks": completed,
        "in_progress_tasks": in_progress,
        "overdue_tasks": overdue,
        "completion_rate": completion_rate,
        "member_count": member_count,
        "doc_count": doc_count,
        "message_count": msg_count,
        "event_count": event_count,
        "recent_events": events_data,
        "risk_alerts": risk_data,
        "member_contributions": contrib_data,
    }
