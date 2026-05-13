from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List
from datetime import datetime, timezone, timedelta

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task
from app.models.document import DocumentVersion
from app.models.message import Message
from app.models.collaboration import (
    CollaborationEvent, ContributionScore, ContributionEvidence,
    RiskAlert, PeerEvaluation, GitRepository, GitCommit
)

router = APIRouter(prefix="/api", tags=["collaboration"])


def _check_member(db, project_id, user_id):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    return member


@router.get("/projects/{project_id}/graph")
def get_collaboration_graph(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    events = db.query(CollaborationEvent).filter(
        CollaborationEvent.project_id == project_id
    ).order_by(CollaborationEvent.created_at.asc()).all()

    nodes = []
    edges = []
    user_cache = {}
    for e in events:
        if e.actor_id not in user_cache:
            u = db.query(User).filter(User.id == e.actor_id).first()
            user_cache[e.actor_id] = u
        actor = user_cache[e.actor_id]
        nodes.append({
            "id": str(e.id),
            "event_type": e.event_type,
            "summary": e.summary,
            "actor": {"id": actor.id, "nickname": actor.nickname, "avatar_url": actor.avatar_url} if actor else None,
            "target_type": e.target_type,
            "target_id": e.target_id,
            "branch_name": e.branch_name or f"user-{e.actor_id}",
            "evidence_level": e.evidence_level,
            "contribution_weight": float(e.contribution_weight),
            "created_at": e.created_at.isoformat(),
        })
        if e.parent_event_id:
            edges.append({"source": str(e.parent_event_id), "target": str(e.id)})
    return {"nodes": nodes, "edges": edges}


@router.get("/projects/{project_id}/contribution")
def get_contribution(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").all()
    result = []
    for m in members:
        score = db.query(ContributionScore).filter(
            ContributionScore.project_id == project_id, ContributionScore.user_id == m.user_id
        ).first()
        user = db.query(User).filter(User.id == m.user_id).first()
        event_count = db.query(CollaborationEvent).filter(
            CollaborationEvent.project_id == project_id, CollaborationEvent.actor_id == m.user_id
        ).count()
        completed_tasks = db.query(Task).filter(
            Task.project_id == project_id, Task.assignee_id == m.user_id, Task.status == "DONE"
        ).count()
        evidence_list = db.query(ContributionEvidence).filter(
            ContributionEvidence.project_id == project_id, ContributionEvidence.user_id == m.user_id
        ).order_by(ContributionEvidence.created_at.desc()).limit(10).all()
        evidences = [{"evidence_type": e.evidence_type, "description": e.description,
                      "contribution_value": float(e.contribution_value), "created_at": e.created_at.isoformat()} for e in evidence_list]
        result.append({
            "user_id": m.user_id, "nickname": user.nickname if user else "", "avatar_url": user.avatar_url if user else None,
            "role": m.role,
            "total_score": float(score.total_score) if score else 0,
            "task_score": float(score.task_score) if score else 0,
            "document_score": float(score.document_score) if score else 0,
            "code_score": float(score.code_score) if score else 0,
            "response_score": float(score.response_score) if score else 0,
            "stability_score": float(score.stability_score) if score else 0,
            "event_count": event_count, "completed_tasks": completed_tasks, "evidences": evidences,
        })
    result.sort(key=lambda x: x["total_score"], reverse=True)
    return result


@router.post("/projects/{project_id}/contribution/recalculate")
def recalculate_contribution(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    _do_recalculate(db, project_id)
    return {"message": "Contribution scores recalculated"}


def _do_recalculate(db: Session, project_id: int):
    """Refined rule-based contribution score calculation for process audit."""
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").all()

    for m in members:
        evidences_to_add = []

        # 1. Task Score: Difficulty weighted completion
        tasks = db.query(Task).filter(Task.project_id == project_id, Task.assignee_id == m.user_id, Task.status == "DONE").all()
        # Each difficulty point counts as 10 base points. Max 100.
        task_raw = sum(t.difficulty * 10 for t in tasks)
        task_score = min(task_raw, 100)
        for t in tasks[:10]:
            evidences_to_add.append({
                "evidence_type": "task",
                "evidence_ref_id": t.id,
                "contribution_value": min(t.difficulty * 10, 20),
                "description": f"完成任务《{t.title}》",
            })

        # 2. Document Score: Based on actual words added in versions
        doc_versions = db.query(DocumentVersion).filter(DocumentVersion.creator_id == m.user_id).all()
        total_words = sum(v.valid_added_words for v in doc_versions)
        # 100 words = 10 points. Max 100.
        doc_score = min(total_words / 10, 100)
        for v in sorted(doc_versions, key=lambda item: item.valid_added_words, reverse=True)[:10]:
            if v.valid_added_words <= 0:
                continue
            evidences_to_add.append({
                "evidence_type": "document",
                "evidence_ref_id": v.id,
                "contribution_value": min(v.valid_added_words / 10, 15),
                "description": f"保存文档版本 {v.version_no}，新增 {v.valid_added_words} 字",
            })

        # 3. Code Score: Based on commits and lines changed
        commits = db.query(GitCommit).filter(GitCommit.project_id == project_id, GitCommit.author_id == m.user_id).all()
        code_raw = sum(5 + (c.added_lines / 50) for c in commits)
        code_score = min(code_raw, 100)
        for c in commits[:10]:
            evidences_to_add.append({
                "evidence_type": "code",
                "evidence_ref_id": c.id,
                "contribution_value": min(5 + (c.added_lines / 50), 20),
                "description": f"代码提交 {c.commit_hash}: {c.commit_message}",
            })

        # 4. Response Score: Participation in communication
        msg_count = db.query(Message).filter(Message.project_id == project_id, Message.sender_id == m.user_id).count()
        # Participation in threads (replies) gives more weight
        threads_involved = db.query(Message.thread_id).filter(
            Message.project_id == project_id, Message.sender_id == m.user_id
        ).distinct().count()
        response_score = min(msg_count * 2 + threads_involved * 5, 100)
        recent_messages = db.query(Message).filter(
            Message.project_id == project_id, Message.sender_id == m.user_id, Message.is_deleted == 0
        ).order_by(Message.created_at.desc()).limit(10).all()
        for msg in recent_messages:
            evidences_to_add.append({
                "evidence_type": "message",
                "evidence_ref_id": msg.id,
                "contribution_value": min(2 + len(msg.content) / 100, 8),
                "description": f"参与讨论：{msg.content[:40]}",
            })

        # 5. Stability Score: How evenly distributed are the events?
        # Detect "Sprint" behavior (last minute rush)
        events = db.query(CollaborationEvent).filter(
            CollaborationEvent.project_id == project_id, CollaborationEvent.actor_id == m.user_id
        ).order_by(CollaborationEvent.created_at.asc()).all()
        
        if len(events) < 5:
            stability_score = 60.0 # Not enough data
        else:
            # Simple heuristic: variance of intervals between events
            intervals = []
            for i in range(1, len(events)):
                diff = (events[i].created_at - events[i-1].created_at).total_seconds() / 3600 # hours
                intervals.append(min(diff, 72)) # Cap at 3 days to avoid outliers
            
            # If events are too clustered or too sparse, stability drops
            stability_score = 80.0 # Start high
            if len(intervals) > 0:
                avg_interval = sum(intervals) / len(intervals)
                if avg_interval < 0.5: stability_score -= 20 # Too clustered (spamming)
                if avg_interval > 48: stability_score -= 20 # Too sparse (inactive)

        # 6. Peer score
        peer_evals = db.query(PeerEvaluation).filter(
            PeerEvaluation.project_id == project_id, PeerEvaluation.evaluatee_id == m.user_id
        ).all()
        peer_score = sum(e.score for e in peer_evals) / len(peer_evals) if peer_evals else 70.0

        # Weighted Total
        total = (task_score * 0.35 + doc_score * 0.20 + code_score * 0.15 + 
                 response_score * 0.10 + stability_score * 0.10 + peer_score * 0.10)

        score = db.query(ContributionScore).filter(
            ContributionScore.project_id == project_id, ContributionScore.user_id == m.user_id
        ).first()
        if score:
            score.task_score = task_score
            score.document_score = doc_score
            score.code_score = code_score
            score.response_score = response_score
            score.stability_score = stability_score
            score.peer_score = peer_score
            score.total_score = total
        else:
            db.add(ContributionScore(
                project_id=project_id, user_id=m.user_id,
                task_score=task_score, document_score=doc_score, code_score=code_score,
                response_score=response_score, stability_score=stability_score,
                peer_score=peer_score, total_score=total
            ))
            db.flush()
            score = db.query(ContributionScore).filter(
                ContributionScore.project_id == project_id, ContributionScore.user_id == m.user_id
            ).first()

        db.query(ContributionEvidence).filter(
            ContributionEvidence.project_id == project_id,
            ContributionEvidence.user_id == m.user_id,
        ).delete()

        for item in sorted(evidences_to_add, key=lambda evidence: evidence["contribution_value"], reverse=True)[:12]:
            db.add(ContributionEvidence(
                project_id=project_id,
                user_id=m.user_id,
                score_id=score.id if score else None,
                evidence_type=item["evidence_type"],
                evidence_ref_id=item["evidence_ref_id"],
                contribution_value=item["contribution_value"],
                description=item["description"],
            ))

    db.commit()


@router.get("/projects/{project_id}/risk-alerts")
def get_risk_alerts(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    alerts = db.query(RiskAlert).filter(RiskAlert.project_id == project_id, RiskAlert.status == "open").order_by(RiskAlert.risk_score.desc()).all()
    return [{"id": a.id, "risk_type": a.risk_type, "risk_level": a.risk_level, "risk_score": a.risk_score,
             "reason": a.reason, "suggestion": a.suggestion, "status": a.status,
             "created_at": a.created_at.isoformat()} for a in alerts]


@router.post("/projects/{project_id}/risk-alerts/scan")
def scan_risks(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    now = datetime.now(timezone.utc).replace(tzinfo=None)

    db.query(RiskAlert).filter(
        RiskAlert.project_id == project_id,
        RiskAlert.status == "open",
        RiskAlert.risk_type.in_(["deadline", "blocked", "review_backlog"]),
    ).delete(synchronize_session=False)

    overdue_tasks = db.query(Task).filter(
        Task.project_id == project_id, Task.due_time < now, Task.status.notin_(["DONE", "ARCHIVED"])
    ).all()
    for t in overdue_tasks:
        db.add(RiskAlert(project_id=project_id, target_type="task", target_id=t.id,
                         risk_type="deadline", risk_level="high", risk_score=80,
                         reason=f"任务【{t.title}】已超过截止时间", suggestion="建议组长介入，重新评估任务进度"))

    blocked_tasks = db.query(Task).filter(Task.project_id == project_id, Task.status == "BLOCKED").all()
    for t in blocked_tasks:
        db.add(RiskAlert(project_id=project_id, target_type="task", target_id=t.id,
                         risk_type="blocked", risk_level="high", risk_score=75,
                         reason=f"任务【{t.title}】处于阻塞状态", suggestion="建议尽快明确阻塞原因并安排协助处理"))

    review_backlog = db.query(Task).filter(Task.project_id == project_id, Task.status == "REVIEW").count()
    if review_backlog >= 3:
        db.add(RiskAlert(project_id=project_id, target_type="project", target_id=project_id,
                         risk_type="review_backlog", risk_level="medium", risk_score=55,
                         reason=f"当前有 {review_backlog} 个任务等待评审", suggestion="建议组长集中处理待评审任务，避免交付堆积"))

    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").all()
    cutoff = now - timedelta(days=3)
    for m in members:
        recent = db.query(CollaborationEvent).filter(
            CollaborationEvent.project_id == project_id, CollaborationEvent.actor_id == m.user_id,
            CollaborationEvent.created_at > cutoff
        ).first()
        if not recent:
            user = db.query(User).filter(User.id == m.user_id).first()
            existing = db.query(RiskAlert).filter(
                RiskAlert.project_id == project_id, RiskAlert.user_id == m.user_id,
                RiskAlert.risk_type == "low_active", RiskAlert.status == "open"
            ).first()
            if not existing:
                db.add(RiskAlert(project_id=project_id, user_id=m.user_id,
                                 risk_type="low_active", risk_level="medium", risk_score=50,
                                 reason=f"成员【{user.nickname if user else m.user_id}】3天内无操作",
                                 suggestion="建议组长主动联系该成员"))
    db.commit()
    return {"message": "Risk scan completed"}


@router.put("/risk-alerts/{alert_id}/resolve")
def resolve_alert(alert_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    alert = db.query(RiskAlert).filter(RiskAlert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404)
    _check_member(db, alert.project_id, current_user.id)
    alert.status = "resolved"
    db.commit()
    return {"message": "Alert resolved"}


@router.get("/projects/{project_id}/git/commits")
def list_commits(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    repos = db.query(GitRepository).filter(GitRepository.project_id == project_id).all()
    result = []
    for repo in repos:
        commits = db.query(GitCommit).filter(GitCommit.repository_id == repo.id).order_by(GitCommit.commit_time.desc()).limit(50).all()
        for c in commits:
            author = db.query(User).filter(User.id == c.author_id).first()
            result.append({
                "id": c.id, "commit_hash": c.commit_hash, "commit_message": c.commit_message,
                "branch_name": c.branch_name, "added_lines": c.added_lines, "deleted_lines": c.deleted_lines,
                "quality_score": c.quality_score, "commit_time": c.commit_time.isoformat(),
                "author": {"id": author.id, "nickname": author.nickname, "avatar_url": author.avatar_url} if author else None,
                "repo_name": repo.repo_name,
            })
    return result


@router.post("/projects/{project_id}/git/commits")
def add_commit(project_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    repo = db.query(GitRepository).filter(GitRepository.project_id == project_id).first()
    if not repo:
        repo = GitRepository(project_id=project_id, repo_name=f"project-{project_id}", provider="simulated")
        db.add(repo)
        db.flush()
    import hashlib, time
    commit_hash = hashlib.sha1(f"{current_user.id}{time.time()}".encode()).hexdigest()[:8]
    commit = GitCommit(
        repository_id=repo.id, project_id=project_id, author_id=current_user.id,
        commit_hash=commit_hash, commit_message=data.get("commit_message", "Update"),
        branch_name=data.get("branch_name", "main"),
        added_lines=data.get("added_lines", 0), deleted_lines=data.get("deleted_lines", 0),
        changed_files=data.get("changed_files", ""),
    )
    db.add(commit)
    event = CollaborationEvent(
        project_id=project_id, actor_id=current_user.id,
        event_type="CodeCommitted", target_type="code", target_id=None,
        summary=f"代码提交: {data.get('commit_message', 'Update')[:50]}", contribution_weight=1.5,
    )
    db.add(event)
    db.commit()
    return {"commit_hash": commit_hash, "message": "Commit recorded"}


@router.post("/projects/{project_id}/peer-evaluations")
def submit_peer_eval(project_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    evaluatee_id = data.get("evaluatee_id")
    score = data.get("score", 70)
    if evaluatee_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot evaluate yourself")
    existing = db.query(PeerEvaluation).filter(
        PeerEvaluation.project_id == project_id, PeerEvaluation.evaluator_id == current_user.id,
        PeerEvaluation.evaluatee_id == evaluatee_id
    ).first()
    if existing:
        existing.score = score
        existing.comment = data.get("comment", "")
    else:
        db.add(PeerEvaluation(project_id=project_id, evaluator_id=current_user.id,
                              evaluatee_id=evaluatee_id, score=score, comment=data.get("comment", "")))
    db.commit()
    return {"message": "Evaluation submitted"}


@router.get("/projects/{project_id}/peer-evaluations")
def get_peer_evals(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    evals = db.query(PeerEvaluation).filter(PeerEvaluation.project_id == project_id).all()
    result = []
    for e in evals:
        evaluator = db.query(User).filter(User.id == e.evaluator_id).first()
        evaluatee = db.query(User).filter(User.id == e.evaluatee_id).first()
        result.append({
            "id": e.id,
            "evaluator": {"id": evaluator.id, "nickname": evaluator.nickname} if evaluator else None,
            "evaluatee": {"id": evaluatee.id, "nickname": evaluatee.nickname} if evaluatee else None,
            "score": e.score, "comment": e.comment, "anomaly_flag": e.anomaly_flag,
            "created_at": e.created_at.isoformat(),
        })
    return result
