from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
import os
import uuid
import aiofiles
from pathlib import Path

from app.core.database import get_db
from app.core.security import get_current_user
from app.core.config import settings
from app.models.user import User
from app.models.project import ProjectMember
from app.models.document import Document, DocumentVersion
from app.models.collaboration import CollaborationEvent, FileResource
from app.schemas.communication import (
    DocumentCreate, DocumentUpdate, DocumentOut,
    DocumentVersionCreate, DocumentVersionOut
)

router = APIRouter(prefix="/api", tags=["documents", "files"])


def _check_member(db, project_id, user_id):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    return member


# ========== Documents ==========

@router.get("/projects/{project_id}/documents", response_model=List[DocumentOut])
def list_documents(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    docs = db.query(Document).filter(Document.project_id == project_id, Document.is_deleted == 0).order_by(Document.updated_at.desc()).all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.post("/projects/{project_id}/documents", response_model=DocumentOut)
def create_document(project_id: int, data: DocumentCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    doc = Document(project_id=project_id, creator_id=current_user.id, **data.model_dump())
    db.add(doc)
    db.flush()

    # Create initial version
    ver = DocumentVersion(
        document_id=doc.id,
        version_no="v0.1",
        snapshot="{}",
        creator_id=current_user.id,
    )
    db.add(ver)
    db.flush()
    doc.current_version_id = ver.id

    # Emit event
    event = CollaborationEvent(
        project_id=project_id, actor_id=current_user.id,
        event_type="DocEdited", target_type="document", target_id=doc.id,
        summary=f"创建文档：{doc.title}", contribution_weight=0.5
    )
    db.add(event)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.get("/documents/{doc_id}", response_model=DocumentOut)
def get_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id, Document.is_deleted == 0).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _check_member(db, doc.project_id, current_user.id)
    return DocumentOut.model_validate(doc)


@router.put("/documents/{doc_id}", response_model=DocumentOut)
def update_document(doc_id: int, data: DocumentUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _check_member(db, doc.project_id, current_user.id)
    for key, val in data.model_dump(exclude_none=True).items():
        setattr(doc, key, val)
    db.commit()
    db.refresh(doc)
    return DocumentOut.model_validate(doc)


@router.delete("/documents/{doc_id}")
def delete_document(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    _check_member(db, doc.project_id, current_user.id)
    doc.is_deleted = 1
    db.commit()
    return {"message": "Document deleted"}


@router.get("/documents/{doc_id}/versions", response_model=List[DocumentVersionOut])
def list_versions(doc_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404)
    _check_member(db, doc.project_id, current_user.id)
    vers = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id).order_by(DocumentVersion.created_at.desc()).all()
    return [DocumentVersionOut.model_validate(v) for v in vers]


@router.post("/documents/{doc_id}/versions", response_model=DocumentVersionOut)
def create_version(doc_id: int, data: DocumentVersionCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == doc_id).first()
    if not doc:
        raise HTTPException(status_code=404)
    _check_member(db, doc.project_id, current_user.id)

    # Auto version number
    count = db.query(DocumentVersion).filter(DocumentVersion.document_id == doc_id).count()
    version_no = f"v{(count // 10) + 1}.{count % 10}"

    ver = DocumentVersion(
        document_id=doc_id,
        version_no=version_no,
        creator_id=current_user.id,
        **data.model_dump()
    )
    db.add(ver)
    db.flush()
    doc.current_version_id = ver.id

    event = CollaborationEvent(
        project_id=doc.project_id, actor_id=current_user.id,
        event_type="DocEdited", target_type="document", target_id=doc_id,
        summary=f"保存文档版本 {version_no}：{doc.title}",
        contribution_weight=min(1.0 + (data.valid_added_words or 0) / 200, 3.0)
    )
    db.add(event)
    db.commit()
    db.refresh(ver)
    return DocumentVersionOut.model_validate(ver)


# ========== Files ==========

@router.get("/projects/{project_id}/files")
def list_files(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    files = db.query(FileResource).filter(FileResource.project_id == project_id, FileResource.is_deleted == 0).order_by(FileResource.created_at.desc()).all()
    result = []
    for f in files:
        uploader = db.query(User).filter(User.id == f.uploader_id).first()
        result.append({
            "id": f.id,
            "file_name": f.file_name,
            "file_url": f.file_url,
            "file_type": f.file_type,
            "file_size": f.file_size,
            "related_task_id": f.related_task_id,
            "created_at": f.created_at.isoformat(),
            "uploader": {"id": uploader.id, "nickname": uploader.nickname} if uploader else None,
        })
    return result


@router.post("/projects/{project_id}/files/upload")
async def upload_file(project_id: int, file: UploadFile = File(...),
                      related_task_id: Optional[int] = None,
                      db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)

    # Save file
    ext = Path(file.filename).suffix
    saved_name = f"{uuid.uuid4().hex}{ext}"
    save_path = Path(settings.UPLOAD_DIR) / "project-files" / saved_name
    save_path.parent.mkdir(parents=True, exist_ok=True)

    content = await file.read()
    async with aiofiles.open(save_path, "wb") as f_out:
        await f_out.write(content)

    file_url = f"/uploads/project-files/{saved_name}"
    fr = FileResource(
        project_id=project_id,
        uploader_id=current_user.id,
        file_name=file.filename,
        file_url=file_url,
        file_type=file.content_type,
        file_size=len(content),
        related_task_id=related_task_id,
    )
    db.add(fr)
    event = CollaborationEvent(
        project_id=project_id, actor_id=current_user.id,
        event_type="FileUploaded", target_type="file", target_id=None,
        summary=f"上传文件：{file.filename}", contribution_weight=0.5
    )
    db.add(event)
    db.commit()
    db.refresh(fr)
    return {"id": fr.id, "file_name": fr.file_name, "file_url": fr.file_url, "file_size": fr.file_size}


@router.delete("/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    fr = db.query(FileResource).filter(FileResource.id == file_id).first()
    if not fr:
        raise HTTPException(status_code=404)
    _check_member(db, fr.project_id, current_user.id)
    fr.is_deleted = 1
    db.commit()
    return {"message": "File deleted"}
