from sqlalchemy import Column, Integer, String, Text, DateTime, func, ForeignKey
from app.core.database import Base


class Document(Base):
    __tablename__ = "document"

    id = Column(Integer, primary_key=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("project.id"), nullable=False, index=True)
    title = Column(String(256), nullable=False)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    current_version_id = Column(Integer, ForeignKey("document_version.id"), nullable=True)
    permission = Column(String(32), nullable=False, default="editable")
    is_deleted = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())


class DocumentVersion(Base):
    __tablename__ = "document_version"

    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("document.id"), nullable=False, index=True)
    version_no = Column(String(32), nullable=False)
    snapshot = Column(Text, nullable=True)
    diff_summary = Column(Text, nullable=True)
    valid_added_words = Column(Integer, nullable=False, default=0)
    valid_modified_words = Column(Integer, nullable=False, default=0)
    summary = Column(String(256), nullable=True)
    creator_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
