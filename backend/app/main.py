from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

from app.core.config import settings
from app.core.database import Base, engine
from app.api import auth, projects, tasks, messages, documents, collaboration, ai_service

# Create all tables
Base.metadata.create_all(bind=engine)

# Create upload directories
for d in ["avatars", "project-files", "document-exports", "reports"]:
    Path(settings.UPLOAD_DIR, d).mkdir(parents=True, exist_ok=True)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="AI-Driven Collaborative Process Audit Platform for University Course Design",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for uploads
if Path(settings.UPLOAD_DIR).exists():
    app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(tasks.router)
app.include_router(messages.router)
app.include_router(documents.router)
app.include_router(collaboration.router)
app.include_router(ai_service.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "version": settings.VERSION, "app": settings.APP_NAME}
