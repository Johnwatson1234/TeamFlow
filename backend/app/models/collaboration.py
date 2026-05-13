from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey, Numeric, JSON
from app.core.database import Base


class CollaborationEvent(Base):
    __tablename__ = "collaboration_event"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    # event_type: TaskCreated, TaskStatusChanged, DocEdited, FileUploaded, MsgSent, etc.
    event_type = Column(String(64), nullable=False)
    target_type = Column(String(32), nullable=True)
    target_id = Column(Integer, nullable=True)
    parent_event_id = Column(Integer, ForeignKey("collaboration_event.id"), nullable=True)
    branch_name = Column(String(128), nullable=True)
    summary = Column(String(512), nullable=True)
    payload = Column(JSON, nullable=True)
    evidence_level = Column(String(32), nullable=True, default="medium")
    contribution_weight = Column(Numeric(6, 2), nullable=False, default=1.0)
    created_at = Column(DateTime, nullable=False, server_default=func.now(), index=True)


class ContributionScore(Base):
    __tablename__ = "contribution_score"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    task_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    document_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    code_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    response_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    stability_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    peer_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    total_score = Column(Numeric(6, 2), nullable=False, default=0.0)
    calculated_at = Column(DateTime, nullable=False, server_default=func.now())


class ContributionEvidence(Base):
    __tablename__ = "contribution_evidence"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    score_id = Column(Integer, ForeignKey("contribution_score.id"), nullable=True)
    evidence_type = Column(String(32), nullable=False)
    evidence_ref_id = Column(Integer, nullable=True)
    contribution_value = Column(Numeric(6, 2), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class RiskAlert(Base):
    __tablename__ = "risk_alert"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=True)
    target_type = Column(String(32), nullable=True)
    target_id = Column(Integer, nullable=True)
    risk_type = Column(String(64), nullable=False)
    risk_level = Column(String(16), nullable=False)  # Low, Medium, High, Critical
    risk_score = Column(Integer, nullable=False, default=0)
    reason = Column(Text, nullable=True)
    suggestion = Column(Text, nullable=True)
    status = Column(String(32), nullable=False, default="open")  # open, resolved, ignored
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class PeerEvaluation(Base):
    __tablename__ = "peer_evaluation"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    evaluator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    evaluatee_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    score = Column(Integer, nullable=False)
    comment = Column(Text, nullable=True)
    anomaly_flag = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class FileResource(Base):
    __tablename__ = "file_resource"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    uploader_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    file_name = Column(String(256), nullable=False)
    file_url = Column(String(512), nullable=False)
    file_type = Column(String(64), nullable=True)
    file_size = Column(Integer, nullable=False)
    related_task_id = Column(Integer, nullable=True)
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class GitRepository(Base):
    __tablename__ = "git_repository"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    repo_name = Column(String(128), nullable=False)
    repo_url = Column(String(512), nullable=True)
    provider = Column(String(32), nullable=False, default="local")
    default_branch = Column(String(64), nullable=False, default="main")
    sync_status = Column(String(32), nullable=False, default="active")
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class GitCommit(Base):
    __tablename__ = "git_commit"

    id = Column(Integer, primary_key=True, autoincrement=True)
    repository_id = Column(Integer, ForeignKey("git_repository.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    commit_hash = Column(String(64), nullable=False)
    commit_message = Column(String(512), nullable=False)
    branch_name = Column(String(64), nullable=False)
    changed_files = Column(Text, nullable=True)
    added_lines = Column(Integer, nullable=False, default=0)
    deleted_lines = Column(Integer, nullable=False, default=0)
    quality_score = Column(Integer, nullable=False, default=0)
    commit_time = Column(DateTime, nullable=False, server_default=func.now())


class AITaskSuggestion(Base):
    __tablename__ = "ai_task_suggestion"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    requester_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    input_prompt = Column(Text, nullable=False)
    output_json = Column(JSON, nullable=True)
    status = Column(String(32), nullable=False, default="pending")  # pending, adopted, discarded
    created_at = Column(DateTime, nullable=False, server_default=func.now())


class AIReportHistory(Base):
    __tablename__ = "ai_report_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False)
    report_type = Column(String(32), nullable=False)  # weekly, defense, contribution, risk
    generated_by = Column(Integer, ForeignKey("user.id"), nullable=False)
    content = Column(Text, nullable=True)
    file_url = Column(String(512), nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
