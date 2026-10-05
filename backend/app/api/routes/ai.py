import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import ensure_project_member, get_current_user
from app.db.session import get_db
from app.models.entities import AIReportHistory, AITaskSuggestion, Conversation, Task, User
from app.services.ai_service import (
    LLMServiceError,
    analyze_document,
    analyze_file,
    build_chat_completion,
    execute_actions,
    generate_project_plan,
    generate_weekly_report,
    get_or_create_ai_conversation,
    get_or_create_ai_user,
    list_ai_conversation_payload,
    persist_message,
)
from app.services.presenters import build_user_map, serialize_message
from app.utils.serializers import dump_json, parse_json


router = APIRouter()


class PlanningPayload(BaseModel):
    project_id: int
    user_prompt: str
    project_name: str = ""
    members: list[dict[str, Any]] = []
    deadline: str = ""
    tech_stack: str = ""


class AIChatPayload(BaseModel):
    prompt: str
    route_name: str = ""
    route_path: str = ""
    route_params: dict[str, Any] = Field(default_factory=dict)
    query: dict[str, Any] = Field(default_factory=dict)
    page_context: dict[str, Any] = Field(default_factory=dict)
    auto_execute: bool = True


class AIActionPayload(BaseModel):
    actions: list[dict[str, Any]]


class AIFileAnalysisPayload(BaseModel):
    conversation_id: int | None = None
    document_id: int | None = None
    file_id: int | None = None
    prompt: str = ""


def _sse_event(event: str, payload: dict[str, Any]) -> bytes:
    return f"event: {event}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n".encode("utf-8")


@router.post("/planning")
def planning(payload: PlanningPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(payload.project_id, current_user.id, db)
    try:
        result = generate_project_plan(db, payload.project_id, payload.user_prompt, user_id=current_user.id)
    except (ValueError, LLMServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    suggestion = AITaskSuggestion(
        project_id=payload.project_id,
        title=f"{payload.project_name or '项目'} AI 任务规划",
        input_payload=dump_json(payload.model_dump()),
        output_payload=dump_json(result),
        status="draft",
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return {"id": suggestion.id, "result": result}


@router.post("/planning/{suggestion_id}/confirm")
def confirm_plan(suggestion_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    suggestion = db.query(AITaskSuggestion).filter(AITaskSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404, detail="规划不存在")
    ensure_project_member(suggestion.project_id, current_user.id, db)

    suggestion.status = "confirmed"
    output = parse_json(suggestion.output_payload, {})
    tasks = output.get("tasks", []) if isinstance(output, dict) else []
    for item in tasks[:6]:
        name = str(item.get("name") or item.get("title") or "").strip()
        if not name:
            continue
        db.add(
            Task(
                project_id=suggestion.project_id,
                title=name,
                description=str(item.get("description") or f"由 AI 自动生成的任务：{name}").strip(),
                status="TODO",
                response_status="待接收",
                priority=str(item.get("priority") or "中").strip(),
                progress=0,
                due_date=str(item.get("deadline") or "").strip(),
                created_by=current_user.id,
            )
        )
    db.commit()
    return {"message": "AI 规划已写入项目"}


@router.post("/reports/weekly")
def weekly_report(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    try:
        content = generate_weekly_report(db, project_id, user_id=current_user.id)
    except (ValueError, LLMServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    report = AIReportHistory(project_id=project_id, report_type="weekly", content=content)
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"id": report.id, "content": content}


@router.get("/projects/{project_id}/ai/conversation")
def ai_conversation(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    return list_ai_conversation_payload(db, project_id, current_user.id)


@router.post("/projects/{project_id}/ai/file-analysis")
def file_analysis(project_id: int, payload: AIFileAnalysisPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    if not payload.document_id and not payload.file_id:
        raise HTTPException(status_code=400, detail="缺少 document_id 或 file_id")

    try:
        if payload.document_id:
            result = analyze_document(db, project_id=project_id, document_id=payload.document_id, prompt=payload.prompt, user_id=current_user.id)
            file_name = result.get("source_name") or f"document-{payload.document_id}"
        else:
            result = analyze_file(db, project_id=project_id, file_id=payload.file_id or 0, prompt=payload.prompt, user_id=current_user.id)
            file_name = result.get("source_name") or f"file-{payload.file_id}"
    except (ValueError, LLMServiceError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    conversation: Conversation
    if payload.conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == payload.conversation_id, Conversation.project_id == project_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="会话不存在")
    else:
        conversation = get_or_create_ai_conversation(db, project_id, current_user.id)

    ai_user = get_or_create_ai_user(db)
    message = persist_message(
        db,
        project_id=project_id,
        conversation_id=conversation.id,
        sender_id=ai_user.id,
        message_type="file_analysis",
        content=str(result.get("summary") or ""),
        metadata={
            "file_name": file_name,
            "scale": result.get("scale", ""),
            "grade": result.get("grade", ""),
            "workload": result.get("workload", ""),
            "risks": result.get("risks", []),
            "suggestions": result.get("suggestions", []),
            "excerpt": result.get("extracted_excerpt", ""),
        },
    )
    return {"result": result, "message": serialize_message(message, build_user_map(db))}


@router.post("/projects/{project_id}/ai/actions/execute")
def action_execute(project_id: int, payload: AIActionPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)
    results = execute_actions(db, project_id=project_id, current_user=current_user, actions=payload.actions)
    return {"results": results}


@router.post("/projects/{project_id}/ai/chat/stream")
def chat_stream(project_id: int, payload: AIChatPayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ensure_project_member(project_id, current_user.id, db)

    conversation = get_or_create_ai_conversation(db, project_id, current_user.id)
    persist_message(
        db,
        project_id=project_id,
        conversation_id=conversation.id,
        sender_id=current_user.id,
        message_type="text",
        content=payload.prompt,
        metadata={
            "route_name": payload.route_name,
            "route_path": payload.route_path,
            "route_params": payload.route_params,
            "query": payload.query,
            "page_context": payload.page_context,
        },
    )
    ai_user = get_or_create_ai_user(db)

    def event_stream():
        yield _sse_event("status", {"message": "AI 正在分析当前页面与项目上下文"})
        try:
            completed = build_chat_completion(
                db,
                project_id=project_id,
                prompt=payload.prompt,
                route_name=payload.route_name,
                route_path=payload.route_path,
                route_params=payload.route_params,
                query=payload.query,
                page_context=payload.page_context,
                user_id=current_user.id,
            )
            action_results = execute_actions(db, project_id=project_id, current_user=current_user, actions=completed["actions"]) if payload.auto_execute else []

            assistant_message = persist_message(
                db,
                project_id=project_id,
                conversation_id=conversation.id,
                sender_id=ai_user.id,
                message_type="ai",
                content=completed["reply"],
                metadata={
                    "route_name": payload.route_name,
                    "actions": completed["actions"],
                    "auto_execute": payload.auto_execute,
                },
            )
            for item in action_results:
                persist_message(
                    db,
                    project_id=project_id,
                    conversation_id=conversation.id,
                    sender_id=ai_user.id,
                    message_type="ai_action",
                    content=item["result"].get("message", ""),
                    metadata=item,
                )

            yield _sse_event("conversation", {"conversation_id": conversation.id, "message_id": assistant_message.id})
            for item in action_results:
                yield _sse_event("action", item)

            chunks = _chunk_text(completed["reply"])
            for chunk in chunks:
                yield _sse_event("chunk", {"content": chunk})

            yield _sse_event(
                "done",
                {
                    "reply": completed["reply"],
                    "actions": completed["actions"],
                    "action_results": action_results,
                },
            )
        except Exception as exc:
            persist_message(
                db,
                project_id=project_id,
                conversation_id=conversation.id,
                sender_id=ai_user.id,
                message_type="ai",
                content=f"本次 AI 处理失败：{exc}",
                metadata={"error": True},
            )
            yield _sse_event("error", {"message": str(exc)})

    return StreamingResponse(event_stream(), media_type="text/event-stream")


def _chunk_text(text: str, size: int = 30) -> list[str]:
    clean = text or ""
    if not clean:
        return []
    return [clean[index : index + size] for index in range(0, len(clean), size)]
