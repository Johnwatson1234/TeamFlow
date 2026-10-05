from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import ensure_project_member, get_current_user
from app.db.session import get_db
from app.models.entities import (
    CollaborationEvent,
    Notification,
    Project,
    ProjectInvitation,
    ProjectMember,
    RiskAlert,
    User,
)
from app.services.member_insights import build_contribution_payload, get_cached_contribution_payload
from app.services.presenters import (
    build_dashboard_payload,
    build_git_payload,
    build_graph_payload,
    build_reminder_payload,
    build_user_map,
    serialize_invitation,
    serialize_member,
    serialize_project,
    serialize_risk,
)


router = APIRouter()


class ProjectPayload(BaseModel):
    name: str
    course_name: str
    description: str = ""
    category: str = "课程设计"
    start_date: str = ""
    due_date: str = ""
    repo_url: str = ""
    advisor_name: str = ""
    advisor_email: str = ""
    tags: list[str] = []


class MemberUpdatePayload(BaseModel):
    role: str
    permission_level: str = "编辑权限"


class InvitationPayload(BaseModel):
    invitee_id: int
    role: str = "成员"
    message: str = ""


@router.get("")
def list_projects(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    member_rows = db.query(ProjectMember).filter(ProjectMember.user_id == current_user.id).all()
    project_ids = [item.project_id for item in member_rows]
    projects = db.query(Project).filter(Project.id.in_(project_ids)).all() if project_ids else []
    return [serialize_project(item, db, current_user.id) for item in projects]


@router.post("")
def create_project(payload: ProjectPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.utils.serializers import dump_json

    project = Project(
        name=payload.name,
        course_name=payload.course_name,
        description=payload.description,
        category=payload.category,
        start_date=payload.start_date,
        due_date=payload.due_date,
        repo_url=payload.repo_url,
        advisor_name=payload.advisor_name,
        advisor_email=payload.advisor_email,
        tags_json=dump_json(payload.tags),
        owner_id=current_user.id,
        status="进行中",
    )
    db.add(project)
    db.flush()
    member = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role="组长",
        permission_level="全部权限",
        workload=50,
        online_status="在线",
    )
    db.add(member)
    db.add(
        CollaborationEvent(
            project_id=project.id,
            actor_id=current_user.id,
            event_type="project",
            title=f"{current_user.display_name} 创建了项目",
            content=payload.name,
            related_type="project",
            related_id=project.id,
            score_value=5.0,
        )
    )
    db.commit()
    db.refresh(project)
    return serialize_project(project, db, current_user.id)


@router.get("/me/invitations")
def my_invitations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    users = build_user_map(db)
    projects = {item.id: item for item in db.query(Project).all()}
    rows = db.query(ProjectInvitation).filter(ProjectInvitation.invitee_id == current_user.id).order_by(ProjectInvitation.created_at.desc()).all()
    return [serialize_invitation(item, users, projects) for item in rows]


@router.post("/invitations/{invitation_id}/accept")
def accept_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = db.query(ProjectInvitation).filter(ProjectInvitation.id == invitation_id, ProjectInvitation.invitee_id == current_user.id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="邀请不存在")
    invitation.status = "accepted"
    invitation.responded_at = datetime.utcnow()
    exists = db.query(ProjectMember).filter(ProjectMember.project_id == invitation.project_id, ProjectMember.user_id == current_user.id).first()
    if not exists:
        db.add(
            ProjectMember(
                project_id=invitation.project_id,
                user_id=current_user.id,
                role=invitation.role,
                permission_level="编辑权限",
                workload=20,
                online_status="在线",
            )
        )
    db.add(
        Notification(
            user_id=invitation.inviter_id,
            project_id=invitation.project_id,
            type="project_invite",
            title="成员已接受邀请",
            content=f"{current_user.display_name} 已加入项目",
            ref_type="project",
            ref_id=invitation.project_id,
        )
    )
    db.commit()
    return {"message": "已接受邀请"}


@router.post("/invitations/{invitation_id}/reject")
def reject_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = db.query(ProjectInvitation).filter(ProjectInvitation.id == invitation_id, ProjectInvitation.invitee_id == current_user.id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="邀请不存在")
    invitation.status = "rejected"
    invitation.responded_at = datetime.utcnow()
    db.commit()
    return {"message": "已拒绝邀请"}


@router.get("/{project_id}")
def project_detail(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    return serialize_project(project, db, current_user.id)


@router.put("/{project_id}")
def update_project(project_id: int, payload: ProjectPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.utils.serializers import dump_json

    ensure_project_member(project_id, current_user.id, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    for field in ["name", "course_name", "description", "category", "start_date", "due_date", "repo_url", "advisor_name", "advisor_email"]:
        setattr(project, field, getattr(payload, field))
    project.tags_json = dump_json(payload.tags)
    db.commit()
    db.refresh(project)
    return serialize_project(project, db, current_user.id)


@router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    project = db.query(Project).filter(Project.id == project_id).first()
    db.delete(project)
    db.commit()
    return {"message": "项目已删除"}


@router.get("/{project_id}/dashboard")
def dashboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return build_dashboard_payload(project_id, db)


@router.get("/{project_id}/members")
def members(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    users = build_user_map(db)
    rows = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    return [serialize_member(item, users) for item in rows]


@router.put("/{project_id}/members/{user_id}")
def update_member(project_id: int, user_id: int, payload: MemberUpdatePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    row = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="成员不存在")
    row.role = payload.role
    row.permission_level = payload.permission_level
    db.commit()
    return {"message": "成员信息已更新"}


@router.delete("/{project_id}/members/{user_id}")
def remove_member(project_id: int, user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    row = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="成员不存在")
    db.delete(row)
    db.commit()
    return {"message": "成员已移除"}


@router.get("/{project_id}/invitations")
def list_invitations(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    users = build_user_map(db)
    projects = {item.id: item for item in db.query(Project).all()}
    rows = db.query(ProjectInvitation).filter(ProjectInvitation.project_id == project_id).order_by(ProjectInvitation.created_at.desc()).all()
    return [serialize_invitation(item, users, projects) for item in rows]


@router.post("/{project_id}/invitations")
def create_invitation(project_id: int, payload: InvitationPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    invitation = ProjectInvitation(
        project_id=project_id,
        inviter_id=current_user.id,
        invitee_id=payload.invitee_id,
        role=payload.role,
        message=payload.message,
        status="pending",
    )
    db.add(invitation)
    db.add(
        Notification(
            user_id=payload.invitee_id,
            project_id=project_id,
            type="project_invite",
            title="收到新的项目邀请",
            content=payload.message or "请处理项目邀请",
            ref_type="invitation",
            ref_id=project_id,
        )
    )
    db.commit()
    return {"message": "邀请已发送"}


@router.delete("/invitations/{invitation_id}")
def delete_invitation(invitation_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    invitation = db.query(ProjectInvitation).filter(ProjectInvitation.id == invitation_id).first()
    if not invitation:
        raise HTTPException(status_code=404, detail="邀请不存在")
    ensure_project_member(invitation.project_id, current_user.id, db)
    db.delete(invitation)
    db.commit()
    return {"message": "邀请已撤回"}


@router.get("/{project_id}/graph")
def graph(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return build_graph_payload(project_id, db)


@router.get("/{project_id}/contribution")
def contribution(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    cached = get_cached_contribution_payload(db, project_id)
    if cached:
        return cached
    return build_contribution_payload(db, project_id, prefer_llm=False, persist=False, user_id=current_user.id)


@router.post("/{project_id}/contribution/recalculate")
def recalc_contribution(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    payload = build_contribution_payload(db, project_id, prefer_llm=True, persist=True, user_id=current_user.id)
    db.commit()
    return payload


@router.get("/{project_id}/risk-alerts")
def risk_alerts(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    rows = db.query(RiskAlert).filter(RiskAlert.project_id == project_id).order_by(RiskAlert.score.desc()).all()
    return [serialize_risk(item) for item in rows]


@router.post("/{project_id}/risk-alerts/scan")
def scan_risks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    row = RiskAlert(
        project_id=project_id,
        title="新扫描结果：接口联调存在阻塞趋势",
        level="中",
        score=58,
        reason="最近两天任务评论增加但状态推进缓慢",
        suggestion="组织一次接口联调专题同步，明确负责人和截止时间。",
        status="open",
        risk_type="协作风险",
        due_at="05-19",
    )
    db.add(row)
    db.commit()
    return {"message": "风险扫描已完成"}


@router.put("/risk-alerts/{risk_id}/resolve")
def resolve_risk(risk_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = db.query(RiskAlert).filter(RiskAlert.id == risk_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="风险不存在")
    ensure_project_member(row.project_id, current_user.id, db)
    row.status = "resolved"
    db.commit()
    return {"message": "风险已处理"}


@router.get("/{project_id}/git/commits")
def git_dashboard(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return build_git_payload(project_id, db)


@router.post("/{project_id}/git/commits")
def add_commit(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return {"message": "已预留提交记录接口"}


@router.get("/{project_id}/peer-evaluations")
def peer_evaluations(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return []


@router.post("/{project_id}/peer-evaluations")
def create_peer_evaluation(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return {"message": "已提交互评"}


@router.get("/{project_id}/workspace")
def workspace(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return build_reminder_payload(project_id, current_user.id, db)
