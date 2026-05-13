from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.core.database import get_db, SessionLocal
from app.core.security import get_current_user, verify_token
from app.models.user import User
from app.models.project import ProjectMember
from app.models.message import Message
from app.models.collaboration import CollaborationEvent
from app.schemas.communication import MessageCreate, MessageOut

router = APIRouter(prefix="/api", tags=["messages"])

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        # project_id -> list of (websocket, user_id)
        self.connections: dict[int, list] = {}

    async def connect(self, websocket: WebSocket, project_id: int, user_id: int):
        await websocket.accept()
        if project_id not in self.connections:
            self.connections[project_id] = []
        self.connections[project_id].append((websocket, user_id))

    def disconnect(self, websocket: WebSocket, project_id: int):
        if project_id in self.connections:
            self.connections[project_id] = [
                (ws, uid) for ws, uid in self.connections[project_id] if ws != websocket
            ]

    async def broadcast(self, project_id: int, data: dict, exclude_ws=None):
        if project_id not in self.connections:
            return
        dead = []
        for ws, uid in self.connections[project_id]:
            if ws == exclude_ws:
                continue
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws, project_id)

    def get_online_users(self, project_id: int) -> List[int]:
        if project_id not in self.connections:
            return []
        return [uid for _, uid in self.connections[project_id]]


manager = ConnectionManager()


@router.get("/projects/{project_id}/messages", response_model=List[MessageOut])
def get_messages(project_id: int, thread_id: Optional[int] = None, limit: int = 50, offset: int = 0,
                 db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    q = db.query(Message).filter(Message.project_id == project_id, Message.is_deleted == 0)
    if thread_id is not None:
        q = q.filter(Message.thread_id == thread_id)
    else:
        q = q.filter(Message.thread_id == None)
    msgs = q.order_by(Message.created_at.desc()).offset(offset).limit(limit).all()
    result = []
    for m in msgs:
        m_dict = MessageOut.model_validate(m).model_dump()
        sender = db.query(User).filter(User.id == m.sender_id).first()
        if sender:
            m_dict["sender"] = {"id": sender.id, "nickname": sender.nickname, "avatar_url": sender.avatar_url}
        result.append(m_dict)
    return result


@router.post("/projects/{project_id}/messages", response_model=MessageOut)
def send_message(project_id: int, data: MessageCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    msg = Message(project_id=project_id, sender_id=current_user.id, **data.model_dump())
    db.add(msg)
    # Emit event
    event = CollaborationEvent(
        project_id=project_id,
        actor_id=current_user.id,
        event_type="CommentAdded",
        target_type="message",
        target_id=None,
        summary=f"发送消息: {data.content[:50]}",
        contribution_weight=0.3,
    )
    db.add(event)
    db.commit()
    db.refresh(msg)
    return MessageOut.model_validate(msg)


@router.delete("/messages/{message_id}")
def delete_message(message_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    msg = db.query(Message).filter(Message.id == message_id).first()
    if not msg:
        raise HTTPException(status_code=404)
    if msg.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your message")
    msg.is_deleted = 1
    db.commit()
    return {"message": "Deleted"}


@router.websocket("/ws/{project_id}")
async def websocket_endpoint(websocket: WebSocket, project_id: int, token: str = ""):
    # Verify token
    payload = verify_token(token) if token else None
    if not payload:
        await websocket.close(code=1008)
        return

    user_id = int(payload.get("sub", 0))
    db = SessionLocal()
    try:
        member = db.query(ProjectMember).filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == "active"
        ).first()
        if not member:
            await websocket.close(code=1008)
            return
    finally:
        db.close()

    await manager.connect(websocket, project_id, user_id)
    try:
        # Notify join
        await manager.broadcast(project_id, {
            "type": "user_online",
            "user_id": user_id,
            "online_users": manager.get_online_users(project_id)
        })
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            msg_type = data.get("type")

            if msg_type == "message":
                # Save message
                db = SessionLocal()
                try:
                    msg = Message(
                        project_id=project_id,
                        sender_id=user_id,
                        content=data.get("content", ""),
                        message_type=data.get("message_type", "text"),
                        thread_id=data.get("thread_id"),
                    )
                    db.add(msg)
                    db.commit()
                    db.refresh(msg)
                    user = db.query(User).filter(User.id == user_id).first()
                    broadcast_data = {
                        "type": "message",
                        "data": {
                            "id": msg.id,
                            "project_id": project_id,
                            "sender_id": user_id,
                            "content": msg.content,
                            "message_type": msg.message_type,
                            "thread_id": msg.thread_id,
                            "created_at": msg.created_at.isoformat(),
                            "sender": {
                                "id": user.id,
                                "nickname": user.nickname,
                                "avatar_url": user.avatar_url
                            } if user else None
                        }
                    }
                finally:
                    db.close()
                await manager.broadcast(project_id, broadcast_data)

            elif msg_type == "task_update":
                await manager.broadcast(project_id, {"type": "task_update", "data": data.get("data", {})})

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id)
        await manager.broadcast(project_id, {
            "type": "user_offline",
            "user_id": user_id,
            "online_users": manager.get_online_users(project_id)
        })


def _check_member(db, project_id, user_id):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    return member
