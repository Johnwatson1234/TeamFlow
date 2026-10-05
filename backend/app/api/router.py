from fastapi import APIRouter

from app.api.routes import ai, auth, conversations, documents, files, llm_settings, notifications, projects, tasks, websocket


api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(tasks.router, tags=["tasks"])
api_router.include_router(conversations.router, tags=["conversations"])
api_router.include_router(documents.router, tags=["documents"])
api_router.include_router(files.router, tags=["files"])
api_router.include_router(notifications.router, tags=["notifications"])
api_router.include_router(ai.router, prefix="/ai", tags=["ai"])
api_router.include_router(llm_settings.router, tags=["llm-settings"])
api_router.include_router(websocket.router, tags=["websocket"])
