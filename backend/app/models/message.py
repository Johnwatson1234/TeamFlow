from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from app.core.database import Base


class Message(Base):
    __tablename__ = "message"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    thread_id = Column(Integer, nullable=True, index=True)
    sender_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    # text, mention, file, code, task_ref, doc_ref, commit_ref, system, reaction
    message_type = Column(String(32), nullable=False, default="text")
    content = Column(Text, nullable=False)
    ref_type = Column(String(32), nullable=True)
    ref_id = Column(Integer, nullable=True)
    quality_score = Column(Integer, nullable=False, default=100)
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
