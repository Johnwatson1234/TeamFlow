from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, index=True, nullable=False)
    phone = Column(String(30), default="")
    avatar = Column(String(255), default="")
    system_role = Column(String(30), default="student")
    status = Column(String(30), default="active")
    title = Column(String(50), default="")
    bio = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    course_name = Column(String(120), nullable=False)
    description = Column(Text, default="")
    status = Column(String(30), default="active")
    category = Column(String(50), default="course")
    start_date = Column(String(30), default="")
    due_date = Column(String(30), default="")
    repo_url = Column(String(255), default="")
    advisor_name = Column(String(100), default="")
    advisor_email = Column(String(120), default="")
    tags_json = Column(Text, default="[]")
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    permission_level = Column(String(50), default="edit")
    workload = Column(Integer, default=0)
    online_status = Column(String(30), default="online")
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class ProjectInvitation(Base):
    __tablename__ = "project_invitations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(50), default="member")
    message = Column(Text, default="")
    status = Column(String(30), default="pending")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    responded_at = Column(DateTime(timezone=True), nullable=True)


class Milestone(Base):
    __tablename__ = "milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    due_date = Column(String(30), default="")
    status = Column(String(30), default="pending")
    order_index = Column(Integer, default=0)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_id = Column(Integer, ForeignKey("milestones.id"), nullable=True)
    title = Column(String(160), nullable=False)
    description = Column(Text, default="")
    status = Column(String(30), default="TODO")
    response_status = Column(String(30), default="未分配")
    priority = Column(String(30), default="中")
    progress = Column(Integer, default=0)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(String(30), default="")
    start_date = Column(String(30), default="")
    blocker_reason = Column(String(255), default="")
    related_requirement = Column(String(120), default="")
    related_document = Column(String(120), default="")
    related_commit = Column(String(120), default="")
    archived = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class TaskActivity(Base):
    __tablename__ = "task_activities"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    activity_type = Column(String(50), default="commented")
    from_value = Column(String(120), default="")
    to_value = Column(String(120), default="")
    content = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    conversation_type = Column(String(30), default="project_group")
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    name = Column(String(120), nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_pinned = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ConversationMember(Base):
    __tablename__ = "conversation_members"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    last_read_message_id = Column(Integer, nullable=True)
    last_read_at = Column(DateTime(timezone=True), nullable=True)
    mute_flag = Column(Boolean, default=False)
    joined_at = Column(DateTime(timezone=True), server_default=func.now())


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    reply_to_message_id = Column(Integer, ForeignKey("messages.id"), nullable=True)
    message_type = Column(String(30), default="text")
    content = Column(Text, default="")
    code_language = Column(String(30), default="")
    metadata_json = Column(Text, default="{}")
    client_msg_id = Column(String(100), default="")
    status = Column(String(30), default="sent")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    type = Column(String(50), default="system")
    title = Column(String(120), nullable=False)
    content = Column(Text, default="")
    ref_type = Column(String(50), default="")
    ref_id = Column(Integer, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True), nullable=True)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(160), nullable=False)
    content = Column(Text, default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    updated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version_count = Column(Integer, default=1)
    permission_status = Column(String(30), default="团队可编辑")
    tags_json = Column(Text, default="[]")
    related_task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class DocumentVersion(Base):
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_label = Column(String(30), default="v1.0")
    summary = Column(String(255), default="")
    content = Column(Text, default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    added_words = Column(Integer, default=0)
    modified_words = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class FileResource(Base):
    __tablename__ = "file_resources"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(160), nullable=False)
    file_type = Column(String(30), default="文档")
    related_task = Column(String(120), default="")
    uploader_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    version_label = Column(String(30), default="v1.0")
    review_status = Column(String(30), default="待评审")
    download_count = Column(Integer, default=0)
    category = Column(String(50), default="需求")
    storage_path = Column(String(255), default="")
    size_label = Column(String(30), default="0 KB")
    description = Column(Text, default="")
    comments_json = Column(Text, default="[]")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class CollaborationEvent(Base):
    __tablename__ = "collaboration_events"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    event_type = Column(String(50), default="task")
    title = Column(String(160), nullable=False)
    content = Column(Text, default="")
    related_type = Column(String(50), default="")
    related_id = Column(Integer, nullable=True)
    score_value = Column(Float, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ContributionScore(Base):
    __tablename__ = "contribution_scores"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    total_score = Column(Float, default=0)
    task_score = Column(Float, default=0)
    document_score = Column(Float, default=0)
    code_score = Column(Float, default=0)
    response_score = Column(Float, default=0)
    stability_score = Column(Float, default=0)
    completed_tasks = Column(Integer, default=0)
    collaboration_events = Column(Integer, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class ContributionEvidence(Base):
    __tablename__ = "contribution_evidence"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    evidence_type = Column(String(50), default="任务")
    summary = Column(String(255), nullable=False)
    score = Column(Float, default=0)
    related_type = Column(String(50), default="")
    related_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class RiskAlert(Base):
    __tablename__ = "risk_alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(160), nullable=False)
    level = Column(String(30), default="低")
    score = Column(Float, default=0)
    reason = Column(Text, default="")
    suggestion = Column(Text, default="")
    status = Column(String(30), default="open")
    risk_type = Column(String(50), default="进度")
    due_at = Column(String(30), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class GitRepository(Base):
    __tablename__ = "git_repositories"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(120), nullable=False)
    url = Column(String(255), default="")
    default_branch = Column(String(50), default="main")
    sync_status = Column(String(30), default="success")
    webhook_status = Column(String(30), default="configured")
    last_synced_at = Column(String(30), default="")
    ci_status = Column(String(30), default="通过")
    total_commits = Column(Integer, default=0)


class GitCommit(Base):
    __tablename__ = "git_commits"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    commit_hash = Column(String(40), nullable=False)
    branch_name = Column(String(60), default="main")
    message = Column(String(255), nullable=False)
    changed_files_json = Column(Text, default="[]")
    added_lines = Column(Integer, default=0)
    deleted_lines = Column(Integer, default=0)
    risk_score = Column(Float, default=0)
    quality_score = Column(Float, default=0)
    related_task = Column(String(60), default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class PullRequest(Base):
    __tablename__ = "pull_requests"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(160), nullable=False)
    branch_name = Column(String(60), default="")
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(String(30), default="待审核")
    reviewers_json = Column(Text, default="[]")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AITaskSuggestion(Base):
    __tablename__ = "ai_task_suggestions"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String(160), nullable=False)
    input_payload = Column(Text, default="{}")
    output_payload = Column(Text, default="{}")
    status = Column(String(30), default="draft")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class AIReportHistory(Base):
    __tablename__ = "ai_report_history"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_type = Column(String(50), default="weekly")
    content = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class UserLLMConfig(Base):
    __tablename__ = "user_llm_configs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False, index=True)
    provider = Column(String(30), default="mimo")
    base_url = Column(String(255), default="")
    api_key = Column(String(255), default="")
    model = Column(String(120), default="")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
