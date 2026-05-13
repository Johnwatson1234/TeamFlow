from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageCreate(BaseModel):
    content: str
    message_type: str = "text"
    thread_id: Optional[int] = None
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None


class MessageOut(BaseModel):
    id: int
    project_id: int
    thread_id: Optional[int] = None
    sender_id: int
    message_type: str
    content: str
    ref_type: Optional[str] = None
    ref_id: Optional[int] = None
    quality_score: int
    created_at: datetime
    sender: Optional[dict] = None

    class Config:
        from_attributes = True


class DocumentCreate(BaseModel):
    title: str
    permission: str = "editable"


class DocumentUpdate(BaseModel):
    title: Optional[str] = None
    permission: Optional[str] = None


class DocumentVersionCreate(BaseModel):
    snapshot: Optional[str] = None
    summary: Optional[str] = None
    diff_summary: Optional[str] = None
    valid_added_words: int = 0
    valid_modified_words: int = 0


class DocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    creator_id: int
    current_version_id: Optional[int] = None
    permission: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentVersionOut(BaseModel):
    id: int
    document_id: int
    version_no: str
    snapshot: Optional[str] = None
    diff_summary: Optional[str] = None
    valid_added_words: int
    valid_modified_words: int
    summary: Optional[str] = None
    creator_id: int
    created_at: datetime

    class Config:
        from_attributes = True
