# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

TeamFlow is a course-project team collaboration platform: a FastAPI + SQLAlchemy backend serving a Vue 3 + TypeScript + Vite frontend. It centers on projects, tasks, conversations, documents, contribution/risk analytics, and an integrated LLM "TeamFlow AI" assistant. The design docs (`要求.md`, `开发文档.md`, `通信方案.md`, `现有功能清单.md`) are written in Chinese and define the product intent — `通信方案.md` in particular lays out the "project-centered, task-mainline, message-triggered, audit-backed" collaboration model the code implements.

## Commands

Backend (run from `backend/`):
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000      # starts FastAPI; main.py auto-creates tables and seeds on import
python seed_all.py                              # generates additional rich mock data on top of the seed
```

Frontend (run from `frontend/`):
```bash
npm install
npm run dev        # vite dev server
npm run build      # vue-tsc -b && vite build
npm run preview    # serve built dist
```

There is no test runner or linter configured in either half of the repo. Type-checking happens via `vue-tsc -b` during `npm run build`.

## Architecture

### Backend (`backend/app/`)

Layered FastAPI app, all routes mounted under `/api` via `app/api/router.py`. Route modules live in `app/api/routes/` (auth, projects, tasks, conversations, documents, files, notifications, ai, websocket). Each route file declares its own `pydantic` request models inline rather than from `app/schemas/` (which only holds generic shared shapes).

- **`main.py`** — on import: `Base.metadata.create_all(bind=engine)` then `seed_database()`. Both run on every startup; the seed is idempotent (checks for existing users/projects before inserting). There is no Alembic migration layer — schema changes propagate by editing `models/entities.py` and relying on `create_all` (existing columns/tables are NOT altered, so manual DB recreation may be needed for schema changes). The SQLite file lives at `backend/data/teamflow.db` (gitignored).
- **`core/config.py`** — loads `.env` and `.env.local` from `backend/` via a hand-rolled parser (no python-dotenv). Reads `TEAMFLOW_LLM_API_KEY` / `TEAMFLOW_LLM_BASE_URL` / `TEAMFLOW_LLM_MODEL` / `TEAMFLOW_LLM_TIMEOUT_SECONDS`. Note: `backend/.env.example` documents `BIGMODEL_*` keys, but the code reads `TEAMFLOW_LLM_*` — the `.env.example` is stale; use the `TEAMFLOW_LLM_*` names. Defaults point at a Mimo endpoint, not BigModel.
- **`core/security.py`** — passlib `pbkdf2_sha256` password hashing (despite `requirements.txt` listing `passlib[bcrypt]`) and JWT issue/verify. `core/realtime.py` holds the in-memory `ConnectionManager` for project-scoped WebSocket fan-out.
- **`api/deps.py`** — `get_current_user` (JWT from `Authorization: Bearer`) and `ensure_project_member` (membership gate). Most project-scoped routes depend on these.
- **`models/entities.py`** — single file defining all ~25 SQLAlchemy ORM tables. JSON-ish fields are stored as `Text` and round-tripped through `app/utils/serializers.py` (`parse_json`/`dump_json`), not native JSON columns.
- **`services/`** — the business logic layer:
  - `presenters.py` — serialization/dashboard/graph/contribution payload builders shared by routes. Routes tend to be thin and delegate here.
  - `ai_service.py` — the TeamFlow AI assistant: planning, weekly reports, chat, file/document analysis, and `execute_actions` (an allow-listed action dispatcher — see `ALLOWED_ACTIONS`).
  - `llm_service.py` — thin OpenAI-compatible chat-completions client over `httpx` (`complete_text` / `complete_json`, with a tolerant JSON extractor for fenced/precede-follower model output). Raises `LLMServiceError` on missing config or upstream failure; routes translate these to HTTP responses.
  - `member_insights.py` — contribution scoring + career/member insight payloads, also calls the LLM directly.

### Frontend (`frontend/src/`)

Vue 3 `<script setup>` SFCs, Pinia stores, Vue Router, Element Plus, axios. Path alias `@` → `src`.

- **`api/http.ts`** — axios instance with `baseURL` from `VITE_API_BASE_URL` (default `http://127.0.0.1:8000/api`); attaches `teamflow-token` from `localStorage` as `Authorization: Bearer`. **`api/index.ts`** — single export surface (`authApi`, `projectApi`, `taskApi`, `conversationApi`, `documentApi`, `fileApi`, `notificationApi`, `aiApi`) used by all views/stores; add new endpoints here, not by importing `http` directly from views.
- **`router/index.ts`** — `ProjectLayout.vue` wraps all per-project views under `/projects/:id/*` (dashboard, tasks, milestones, messages, documents, files, graph, contribution, career, risk, git, ai, settings, reminders, audit). `router.beforeEach` fetches `/auth/me` once when a token exists but the user object is missing, and redirects unauthenticated users to `/login`.
- **`stores/`** — Pinia: `user.ts` (auth + token in `localStorage`), `project.ts`, `ai.ts`, `notification.ts`.
- **`components/common/`** — shared widgets including `GraphCanvas.vue` (AntV G6 5.x graph), `LineChart.vue`/`RadarChart.vue` (ECharts 6), `AIAssistantDock.vue` (the floating AI assistant UI that talks to `/ai/...`).
- Visualization libs are heavy (`@antv/g6`, `echarts`); both are imported where needed.

### Realtime

WebSocket endpoint `/api/ws/{project_id}` (prefix comes from `app.include_router(api_router, prefix="/api")`). The server only handles `ping`/`pong` from clients and uses `ConnectionManager.broadcast(project_id, payload)` to push project events to connected members. Connection state is in-process memory (lost on restart).

### Auth flow

JWT (HS256, `SECRET_KEY` in config) with `sub` = user id, 7-day expiry. Frontend stores token under `teamflow-token`. `get_current_user` decodes and loads the `User` row on every protected request.

## Conventions

- Route files declare their Pydantic payloads inline. Validation/business logic lives in `services/`; keep routes thin and delegate to `presenters.py` / `ai_service.py` / `member_insights.py`.
- JSON fields on models are `Text` columns named `*_json`; always read them via `parse_json(field, default)` and write via `dump_json(value)` (see `app/utils/serializers.py`).
- Chinese is the working language for user-facing strings, comments, and the design docs. Match surrounding copy.
- The seed runs on every server start; do not put destructive logic in `core/seed.py`. New mock data generators go in `seed_all.py` (run manually).
- Frontend API calls go through `src/api/index.ts` API objects; do not call `http` ad-hoc from components.
