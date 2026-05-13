"""
TeamFlow 示例数据填充脚本
为管理员账户填充完整的示例数据，确保登录后可以看到完整的前端效果。
运行方式: cd backend && .venv/bin/python seed_data.py
"""

import sys
import os
import random
from datetime import datetime, timedelta, date

sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal, engine, Base
from app.core.security import get_password_hash, verify_password
from app.models.user import User
from app.models.project import Project, ProjectMember
from app.models.task import Task, TaskDependency, Milestone
from app.models.message import Message
from app.models.document import Document, DocumentVersion
from app.models.collaboration import (
    CollaborationEvent, ContributionScore, ContributionEvidence,
    RiskAlert, PeerEvaluation, GitRepository, GitCommit,
    AITaskSuggestion, AIReportHistory, FileResource,
)

db = SessionLocal()

# ============================================================
# 0. 确保表存在
# ============================================================
Base.metadata.create_all(bind=engine)

# ============================================================
# 1. 创建用户
# ============================================================
print("=== 创建用户 ===")

ADMIN_ID = 2

def make_hash(pw):
    return get_password_hash(pw)

users_data = [
    {"id": 1, "username": "qa_user_auto", "nickname": "QA测试", "role": "user", "email": "qa@teamflow.com", "password": "test123"},
    {"id": 2, "username": "admin", "nickname": "张伟", "role": "admin", "email": "admin@teamflow.com", "password": "admin123"},
    {"id": 3, "username": "lisi", "nickname": "李思", "role": "user", "email": "lisi@teamflow.com", "password": "123456"},
    {"id": 4, "username": "wangwu", "nickname": "王武", "role": "user", "email": "wangwu@teamflow.com", "password": "123456"},
    {"id": 5, "username": "zhaoliu", "nickname": "赵六", "role": "user", "email": "zhaoliu@teamflow.com", "password": "123456"},
    {"id": 6, "username": "sunqi", "nickname": "孙琪", "role": "user", "email": "sunqi@teamflow.com", "password": "123456"},
    {"id": 7, "username": "teacher_chen", "nickname": "陈老师", "role": "teacher", "email": "chen@teamflow.com", "password": "123456"},
]

for u in users_data:
    existing = db.query(User).filter(User.id == u["id"]).first()
    if existing:
        existing.username = u["username"]
        existing.nickname = u["nickname"]
        existing.role = u["role"]
        existing.email = u["email"]
        existing.password_hash = make_hash(u["password"])
        existing.status = 1
        print(f"  更新用户: {u['username']} ({u['nickname']})")
    else:
        user = User(
            id=u["id"],
            username=u["username"],
            password_hash=make_hash(u["password"]),
            nickname=u["nickname"],
            role=u["role"],
            email=u["email"],
            status=1,
        )
        db.add(user)
        print(f"  创建用户: {u['username']} ({u['nickname']})")

db.commit()

# ============================================================
# 2. 创建项目
# ============================================================
print("\n=== 创建项目 ===")

now = datetime.now()
today = date.today()

# 清理旧数据
db.query(FileResource).delete()
db.query(AIReportHistory).delete()
db.query(AITaskSuggestion).delete()
db.query(GitCommit).delete()
db.query(GitRepository).delete()
db.query(PeerEvaluation).delete()
db.query(ContributionEvidence).delete()
db.query(ContributionScore).delete()
db.query(RiskAlert).delete()
db.query(CollaborationEvent).delete()
db.query(DocumentVersion).delete()
db.query(Document).delete()
db.query(Message).delete()
db.query(TaskDependency).delete()
db.query(Milestone).delete()
db.query(Task).delete()
db.query(ProjectMember).delete()
db.query(Project).delete()
db.commit()
print("  清理旧数据完成")

project = Project(
    id=1,
    name="智能协作课设管家",
    description="一个面向高校课程设计的AI驱动团队协作平台，支持任务管理、文档协作、代码集成、贡献度分析和风险预警。",
    owner_id=ADMIN_ID,
    course_name="软件工程",
    teacher_id=7,
    start_date=today - timedelta(days=45),
    end_date=today + timedelta(days=15),
    deadline=datetime.now() + timedelta(days=15),
    status="active",
)
db.add(project)
print(f"  创建项目: {project.name}")
db.commit()

# ============================================================
# 3. 项目成员
# ============================================================
print("\n=== 创建项目成员 ===")

members_data = [
    {"user_id": ADMIN_ID, "role": "leader", "skill_tags": "项目管理,全栈开发,需求分析"},
    {"user_id": 3, "role": "member", "skill_tags": "前端开发,Vue,React,UI设计"},
    {"user_id": 4, "role": "member", "skill_tags": "后端开发,Python,FastAPI,数据库"},
    {"user_id": 5, "role": "member", "skill_tags": "文档撰写,测试,质量管理"},
    {"user_id": 6, "role": "member", "skill_tags": "前端开发,TypeScript,图表可视化"},
    {"user_id": 7, "role": "teacher", "skill_tags": "软件工程,项目管理"},
]

for m in members_data:
    pm = ProjectMember(
        project_id=1,
        user_id=m["user_id"],
        role=m["role"],
        skill_tags=m["skill_tags"],
        status="active",
    )
    db.add(pm)
    print(f"  添加成员: user_id={m['user_id']} role={m['role']}")
db.commit()

# ============================================================
# 4. 任务
# ============================================================
print("\n=== 创建任务 ===")

def dt(days_ago, hour=9, minute=0):
    return now - timedelta(days=days_ago, hours=now.hour - hour, minutes=now.minute - minute)

tasks_data = [
    # --- 已完成的任务 (DONE) ---
    {
        "id": 1, "title": "需求分析文档编写", "description": "完成项目需求分析，梳理功能模块和非功能需求，输出需求规格说明书。",
        "assignee_id": 5, "priority": "high", "difficulty": 3, "status": "DONE", "progress": 100,
        "completed_at": dt(40), "created_at": dt(43), "due_time": dt(38),
    },
    {
        "id": 2, "title": "系统架构设计", "description": "设计前后端分离架构，确定技术栈（FastAPI + Vue3 + SQLite），绘制架构图。",
        "assignee_id": ADMIN_ID, "priority": "critical", "difficulty": 4, "status": "DONE", "progress": 100,
        "completed_at": dt(38), "created_at": dt(41), "due_time": dt(36),
    },
    {
        "id": 3, "title": "数据库表结构设计", "description": "设计17张核心数据表，包括用户、项目、任务、消息、文档、协作事件、贡献评分等。",
        "assignee_id": 4, "priority": "high", "difficulty": 4, "status": "DONE", "progress": 100,
        "completed_at": dt(35), "created_at": dt(38), "due_time": dt(33),
    },
    {
        "id": 4, "title": "用户认证模块开发", "description": "实现用户注册、登录、JWT Token认证、密码修改等功能。",
        "assignee_id": 4, "priority": "high", "difficulty": 3, "status": "DONE", "progress": 100,
        "completed_at": dt(30), "created_at": dt(34), "due_time": dt(28),
    },
    {
        "id": 5, "title": "前端基础框架搭建", "description": "搭建Vue3 + TypeScript + Vite + Element Plus + Pinia前端工程，配置路由和全局状态。",
        "assignee_id": 3, "priority": "high", "difficulty": 3, "status": "DONE", "progress": 100,
        "completed_at": dt(32), "created_at": dt(36), "due_time": dt(30),
    },
    {
        "id": 6, "title": "项目管理CRUD", "description": "实现项目的创建、编辑、归档、成员邀请、成员管理等API和前端页面。",
        "assignee_id": 4, "priority": "high", "difficulty": 3, "status": "DONE", "progress": 100,
        "completed_at": dt(25), "created_at": dt(30), "due_time": dt(23),
    },
    {
        "id": 7, "title": "看板任务管理", "description": "实现任务的拖拽式看板，支持TODO/IN_PROGRESS/BLOCKED/REVIEW/DONE状态流转。",
        "assignee_id": 3, "priority": "high", "difficulty": 4, "status": "DONE", "progress": 100,
        "completed_at": dt(22), "created_at": dt(28), "due_time": dt(20),
    },
    # --- 进行中的任务 (IN_PROGRESS) ---
    {
        "id": 8, "title": "实时消息系统", "description": "基于WebSocket实现实时群聊，支持文本、代码片段、任务引用、文件分享等消息类型。",
        "assignee_id": 4, "priority": "high", "difficulty": 4, "status": "IN_PROGRESS", "progress": 70,
        "created_at": dt(20), "due_time": dt(-3),
    },
    {
        "id": 9, "title": "文档协作编辑", "description": "实现文档的在线编辑、版本管理、差异对比、协作记录等功能。",
        "assignee_id": 3, "priority": "medium", "difficulty": 4, "status": "IN_PROGRESS", "progress": 55,
        "created_at": dt(18), "due_time": dt(-5),
    },
    {
        "id": 10, "title": "贡献度分析算法", "description": "实现多维度贡献评分算法，包括任务完成度、文档贡献、代码提交、响应速度、稳定性等。",
        "assignee_id": ADMIN_ID, "priority": "critical", "difficulty": 5, "status": "IN_PROGRESS", "progress": 40,
        "created_at": dt(15), "due_time": dt(-2),
    },
    {
        "id": 11, "title": "仪表盘数据可视化", "description": "使用ECharts实现项目仪表盘，包括任务状态统计、贡献度雷达图、活动趋势图。",
        "assignee_id": 6, "priority": "high", "difficulty": 4, "status": "IN_PROGRESS", "progress": 65,
        "created_at": dt(16), "due_time": dt(-4),
    },
    # --- 已阻塞的任务 (BLOCKED) ---
    {
        "id": 12, "title": "前后端联调", "description": "前后端接口对接与联调，解决跨域、数据格式、异常处理等问题。",
        "assignee_id": 3, "priority": "critical", "difficulty": 4, "status": "BLOCKED", "progress": 30,
        "created_at": dt(12), "due_time": dt(-1),
    },
    # --- 评审中的任务 (REVIEW) ---
    {
        "id": 13, "title": "风险预警模块", "description": "实现项目风险评估引擎，自动检测任务延期、成员活跃度低、文档审查积压等风险。",
        "assignee_id": 4, "priority": "high", "difficulty": 4, "status": "REVIEW", "progress": 90,
        "created_at": dt(14), "due_time": dt(-6),
    },
    {
        "id": 14, "title": "Git集成与代码提交记录", "description": "实现Git仓库绑定、commit记录同步、代码质量评分等功能。",
        "assignee_id": 4, "priority": "medium", "difficulty": 3, "status": "REVIEW", "progress": 85,
        "created_at": dt(12), "due_time": dt(-4),
    },
    # --- 待办任务 (TODO) ---
    {
        "id": 15, "title": "单元测试编写", "description": "为后端核心API编写单元测试，确保代码质量。覆盖认证、项目、任务等模块。",
        "assignee_id": 5, "priority": "medium", "difficulty": 3, "status": "TODO", "progress": 0,
        "created_at": dt(10), "due_time": dt(-8),
    },
    {
        "id": 16, "title": "部署文档编写", "description": "编写项目部署文档，包括环境配置、依赖安装、数据库初始化、启动命令等。",
        "assignee_id": 5, "priority": "low", "difficulty": 2, "status": "TODO", "progress": 0,
        "created_at": dt(8), "due_time": dt(-10),
    },
    {
        "id": 17, "title": "AI智能规划功能", "description": "接入AI大模型，实现基于自然语言的任务自动分解和项目规划建议。",
        "assignee_id": ADMIN_ID, "priority": "medium", "difficulty": 5, "status": "TODO", "progress": 0,
        "created_at": dt(6), "due_time": dt(-12),
    },
    {
        "id": 18, "title": "匿名同行评价功能", "description": "实现团队成员间的匿名互评功能，支持评分和文字评价，检测异常评价。",
        "assignee_id": 6, "priority": "medium", "difficulty": 3, "status": "TODO", "progress": 0,
        "created_at": dt(5), "due_time": dt(-14),
    },
    {
        "id": 19, "title": "项目归档与导出", "description": "支持项目归档、数据导出（Word报告、Excel数据表），项目复盘总结。",
        "assignee_id": ADMIN_ID, "priority": "low", "difficulty": 2, "status": "TODO", "progress": 0,
        "created_at": dt(4), "due_time": dt(-16),
    },
    {
        "id": 20, "title": "答辩PPT自动生成", "description": "根据项目数据自动生成答辩演示文稿，包括项目概述、进度展示、贡献对比等。",
        "assignee_id": 3, "priority": "low", "difficulty": 3, "status": "TODO", "progress": 0,
        "created_at": dt(3), "due_time": dt(-18),
    },
]

for t in tasks_data:
    task = Task(
        id=t["id"],
        project_id=1,
        parent_id=None,
        title=t["title"],
        description=t["description"],
        assignee_id=t["assignee_id"],
        creator_id=ADMIN_ID,
        priority=t["priority"],
        difficulty=t["difficulty"],
        status=t["status"],
        progress=t["progress"],
        progress_confidence=100,
        start_time=t.get("created_at"),
        due_time=t.get("due_time"),
        completed_at=t.get("completed_at"),
        created_at=t.get("created_at", now),
        updated_at=t.get("completed_at", now),
    )
    db.add(task)
    print(f"  创建任务: [{t['status']}] {t['title']}")
db.commit()

# ============================================================
# 5. 任务依赖关系
# ============================================================
print("\n=== 创建任务依赖 ===")

deps = [
    (2, 1),    # 系统架构设计 依赖 需求分析文档
    (3, 2),    # 数据库设计 依赖 系统架构设计
    (4, 3),    # 用户认证模块 依赖 数据库设计
    (5, 2),    # 前端框架搭建 依赖 系统架构设计
    (6, 4),    # 项目管理CRUD 依赖 用户认证模块
    (7, 5),    # 看板任务管理 依赖 前端框架搭建
    (8, 6),    # 实时消息系统 依赖 项目管理CRUD
    (9, 5),    # 文档协作 依赖 前端框架搭建
    (12, 8),   # 前后端联调 依赖 实时消息系统
    (12, 9),   # 前后端联调 依赖 文档协作
]

for task_id, dep_id in deps:
    td = TaskDependency(
        task_id=task_id,
        depends_on_task_id=dep_id,
        dependency_type="finish_to_start",
    )
    db.add(td)
print(f"  创建 {len(deps)} 条依赖关系")
db.commit()

# ============================================================
# 6. 里程碑
# ============================================================
print("\n=== 创建里程碑 ===")

milestones_data = [
    {"name": "需求分析完成", "description": "完成项目需求规格说明书，通过教师评审", "due_date": dt(38), "status": "completed"},
    {"name": "系统设计完成", "description": "完成架构设计、数据库设计、接口设计", "due_date": dt(33), "status": "completed"},
    {"name": "核心功能开发完成", "description": "完成任务管理、消息系统、文档协作等核心功能", "due_date": dt(-5), "status": "in_progress"},
    {"name": "测试与答辩准备", "description": "完成系统测试、编写测试报告、准备答辩材料", "due_date": dt(-15), "status": "pending"},
]

for m in milestones_data:
    ms = Milestone(
        project_id=1,
        name=m["name"],
        description=m["description"],
        due_date=m["due_date"],
        status=m["status"],
        created_by_ai=0,
    )
    db.add(ms)
    print(f"  创建里程碑: {m['name']} ({m['status']})")
db.commit()

# ============================================================
# 7. 消息
# ============================================================
print("\n=== 创建消息 ===")

messages_data = [
    {"sender_id": ADMIN_ID, "content": "大家好！我们的课设项目正式启动了，先同步一下需求分析的结果。", "days_ago": 40, "type": "text"},
    {"sender_id": 5, "content": "需求文档已经写好了，主要分为用户管理、项目管理、任务管理、消息系统、文档协作、贡献分析、风险预警七大模块。", "days_ago": 39, "type": "text"},
    {"sender_id": 3, "content": "收到！我先搭前端框架，Vue3 + TypeScript + Vite，大家有意见吗？", "days_ago": 38, "type": "text"},
    {"sender_id": 4, "content": "后端用FastAPI + SQLAlchemy + SQLite，和前端完全分离，RESTful API。", "days_ago": 38, "type": "text"},
    {"sender_id": ADMIN_ID, "content": "很好，我来协调整体进度。架构设计我来做，其他人先熟悉技术栈。", "days_ago": 37, "type": "text"},
    {"sender_id": 6, "content": "我负责数据可视化部分，ECharts图表我已经研究过了，没问题。", "days_ago": 36, "type": "text"},
    {"sender_id": 4, "content": "数据库设计完成！17张表，涵盖了用户、项目、任务、消息、文档、协作事件、贡献评分、风险预警等全部功能。", "days_ago": 33, "type": "text"},
    {"sender_id": 3, "content": "前端框架搭好了，路由配置完毕，Pinia状态管理也接好了。", "days_ago": 32, "type": "text"},
    {"sender_id": 5, "content": "用户认证模块后端API已经完成，注册登录JWT Token都通了。", "days_ago": 28, "type": "text"},
    {"sender_id": ADMIN_ID, "content": "进度不错！提醒一下大家注意代码规范，每次提交前检查一下。", "days_ago": 25, "type": "text"},
    {"sender_id": 3, "content": "看板功能基本做完了，支持拖拽切换状态，交互效果还行。", "days_ago": 20, "type": "text"},
    {"sender_id": 6, "content": "仪表盘的ECG趋势图和雷达图初版出来了，效果不错！", "days_ago": 15, "type": "text"},
    {"sender_id": 4, "content": "消息系统WebSocket对接完成了，支持文本和代码片段。", "days_ago": 10, "type": "text"},
    {"sender_id": 5, "content": "有个问题，文档协作模块的版本对比功能还在开发中，可能需要延两天。", "days_ago": 8, "type": "text"},
    {"sender_id": ADMIN_ID, "content": "好的，文档协作优先级可以适当放低，先把核心的消息和看板稳定下来。", "days_ago": 7, "type": "text"},
    {"sender_id": 3, "content": "前后端联调遇到了一些CORS问题，正在排查。", "days_ago": 5, "type": "text"},
    {"sender_id": 4, "content": "CORS配置已经修好了，在main.py加了CORSMiddleware。联调可以继续了。", "days_ago": 4, "type": "text"},
    {"sender_id": 6, "content": "贡献度分析的雷达图和柱状图已经完成，数据接口也在对接中。", "days_ago": 3, "type": "text"},
    {"sender_id": ADMIN_ID, "content": "很好！下周开始准备答辩材料，大家辛苦了！", "days_ago": 1, "type": "text"},
    {"sender_id": 5, "content": "收到！我先整理测试用例和文档。", "days_ago": 0, "type": "text"},
]

for m in messages_data:
    msg = Message(
        project_id=1,
        thread_id=None,
        sender_id=m["sender_id"],
        message_type=m["type"],
        content=m["content"],
        quality_score=100,
        created_at=dt(m["days_ago"], hour=random.randint(9, 21), minute=random.randint(0, 59)),
    )
    db.add(msg)
print(f"  创建 {len(messages_data)} 条消息")
db.commit()

# ============================================================
# 8. 文档与版本
# ============================================================
print("\n=== 创建文档 ===")

docs_data = [
    {
        "title": "需求规格说明书",
        "creator_id": 5,
        "versions": [
            {"version_no": "v1.0", "snapshot": "# 需求规格说明书 v1.0\n\n## 1. 项目概述\n智能协作课设管家是一个面向高校课程设计的AI驱动团队协作平台。\n\n## 2. 功能需求\n- 用户管理\n- 项目管理\n- 任务管理\n- 消息系统", "diff_summary": "初始版本", "words_added": 2500, "words_modified": 0},
            {"version_no": "v1.1", "snapshot": "# 需求规格说明书 v1.1\n\n## 1. 项目概述\n智能协作课设管家是一个面向高校课程设计的AI驱动团队协作平台，旨在让每个任务、文档、代码变更和讨论都可追溯。\n\n## 2. 功能需求\n- 用户管理（注册/登录/权限）\n- 项目管理（创建/编辑/归档/成员）\n- 任务管理（看板/依赖/里程碑）\n- 消息系统（实时聊天/文件分享）\n- 文档协作（编辑/版本管理）\n- 贡献分析（多维度评分）\n- 风险预警（自动检测）", "diff_summary": "补充项目愿景，细化功能模块", "words_added": 1800, "words_modified": 600},
            {"version_no": "v2.0", "snapshot": "# 需求规格说明书 v2.0\n\n## 1. 项目概述\n智能协作课设管家是一个面向高校课程设计的AI驱动团队协作平台...\n\n## 2. 功能需求\n（完整内容）\n\n## 3. 非功能需求\n- 性能：支持50人同时在线\n- 安全：JWT认证，密码加密\n- 可用性：响应式设计\n\n## 4. 数据流图\n（架构描述）", "diff_summary": "增加非功能需求，完善数据流描述", "words_added": 3200, "words_modified": 400},
        ],
    },
    {
        "title": "数据库设计文档",
        "creator_id": 4,
        "versions": [
            {"version_no": "v1.0", "snapshot": "# 数据库设计文档\n\n## 表结构\n1. user - 用户表\n2. project - 项目表\n3. project_member - 项目成员表\n4. task - 任务表", "diff_summary": "初始表结构设计", "words_added": 1500, "words_modified": 0},
            {"version_no": "v1.1", "snapshot": "# 数据库设计文档 v1.1\n\n## 表结构\n1. user - 用户表\n2. project - 项目表\n3. project_member - 项目成员表\n4. task - 任务表\n5. task_dependency - 任务依赖表\n6. milestone - 里程碑表\n7. message - 消息表\n8. document - 文档表\n9. document_version - 文档版本表\n10. collaboration_event - 协作事件表\n11. contribution_score - 贡献评分表\n12. contribution_evidence - 贡献证据表\n13. risk_alert - 风险预警表\n14. peer_evaluation - 同行评价表\n15. file_resource - 文件资源表\n16. git_repository - Git仓库表\n17. git_commit - Git提交表", "diff_summary": "扩展全部17张表设计", "words_added": 4200, "words_modified": 800},
        ],
    },
    {
        "title": "系统设计报告",
        "creator_id": ADMIN_ID,
        "versions": [
            {"version_no": "v1.0", "snapshot": "# 系统设计报告\n\n## 1. 系统架构\n采用前后端分离架构：\n- 前端：Vue3 + TypeScript + Vite + Element Plus\n- 后端：FastAPI + SQLAlchemy + SQLite\n\n## 2. 技术选型\n...", "diff_summary": "初始架构设计", "words_added": 2000, "words_modified": 0},
        ],
    },
    {
        "title": "测试计划",
        "creator_id": 5,
        "versions": [
            {"version_no": "v0.1", "snapshot": "# 测试计划（草稿）\n\n## 1. 测试范围\n- 单元测试\n- 集成测试\n- UI测试\n\n## 2. 测试用例\n...", "diff_summary": "测试计划初稿", "words_added": 800, "words_modified": 0},
        ],
    },
]

for d in docs_data:
    doc = Document(
        project_id=1,
        title=d["title"],
        creator_id=d["creator_id"],
        permission="editable",
        is_deleted=0,
    )
    db.add(doc)
    db.flush()

    latest_version = None
    for v in d["versions"]:
        dv = DocumentVersion(
            document_id=doc.id,
            version_no=v["version_no"],
            snapshot=v["snapshot"],
            diff_summary=v["diff_summary"],
            valid_added_words=v["words_added"],
            valid_modified_words=v["words_modified"],
            summary=v["diff_summary"],
            creator_id=d["creator_id"],
            created_at=dt(40 - len(d["versions"]) + d["versions"].index(v) * 5),
        )
        db.add(dv)
        db.flush()
        latest_version = dv

    doc.current_version_id = latest_version.id
    print(f"  创建文档: {d['title']} ({len(d['versions'])} 个版本)")
db.commit()

# ============================================================
# 9. 协作事件 (Git Graph)
# ============================================================
print("\n=== 创建协作事件 ===")

event_types = [
    ("TaskCreated", "task"),
    ("TaskStatusChanged", "task"),
    ("ProgressUpdated", "task"),
    ("DocEdited", "document"),
    ("MsgSent", "message"),
    ("FileUploaded", "file"),
    ("CodeCommitted", "commit"),
    ("ReviewPassed", "review"),
    ("CommentAdded", "message"),
]

event_branches = ["main", "feature/auth", "feature/task", "feature/message", "feature/doc", "feature/viz", "fix/cors"]
actor_ids = [ADMIN_ID, 3, 4, 5, 6]

events_data = []
for i in range(35):
    et = random.choice(event_types)
    days = random.randint(0, 42)
    events_data.append({
        "actor_id": random.choice(actor_ids),
        "event_type": et[0],
        "target_type": et[1],
        "target_id": random.randint(1, 20),
        "branch_name": random.choice(event_branches),
        "summary": f"{et[0]} on {et[1]} #{random.randint(1,20)}",
        "evidence_level": random.choice(["low", "medium", "high"]),
        "contribution_weight": round(random.uniform(0.5, 3.0), 2),
        "days_ago": days,
    })

events_data.sort(key=lambda x: -x["days_ago"])

for e in events_data:
    ce = CollaborationEvent(
        project_id=1,
        actor_id=e["actor_id"],
        event_type=e["event_type"],
        target_type=e["target_type"],
        target_id=e["target_id"],
        branch_name=e["branch_name"],
        summary=e["summary"],
        evidence_level=e["evidence_level"],
        contribution_weight=e["contribution_weight"],
        created_at=dt(e["days_ago"], hour=random.randint(9, 21), minute=random.randint(0, 59)),
    )
    db.add(ce)
print(f"  创建 {len(events_data)} 条协作事件")
db.commit()

# ============================================================
# 10. 贡献评分
# ============================================================
print("\n=== 创建贡献评分 ===")

scores_data = [
    {"user_id": ADMIN_ID, "task": 92, "doc": 45, "code": 60, "response": 95, "stability": 90, "peer": 88, "total": 85},
    {"user_id": 3, "task": 85, "doc": 30, "code": 78, "response": 82, "stability": 85, "peer": 80, "total": 78},
    {"user_id": 4, "task": 88, "doc": 55, "code": 92, "response": 78, "stability": 88, "peer": 82, "total": 82},
    {"user_id": 5, "task": 70, "doc": 88, "code": 20, "response": 75, "stability": 72, "peer": 75, "total": 65},
    {"user_id": 6, "task": 65, "doc": 25, "code": 72, "response": 80, "stability": 78, "peer": 72, "total": 62},
]

for s in scores_data:
    cs = ContributionScore(
        project_id=1,
        user_id=s["user_id"],
        task_score=s["task"],
        document_score=s["doc"],
        code_score=s["code"],
        response_score=s["response"],
        stability_score=s["stability"],
        peer_score=s["peer"],
        total_score=s["total"],
    )
    db.add(cs)
print(f"  创建 {len(scores_data)} 条贡献评分")
db.commit()

# ============================================================
# 11. 贡献证据
# ============================================================
print("\n=== 创建贡献证据 ===")

evidence_data = [
    {"user_id": ADMIN_ID, "type": "task_completed", "value": 5.0, "desc": "完成系统架构设计、贡献度分析算法等多个高难度任务"},
    {"user_id": ADMIN_ID, "type": "coordination", "value": 3.0, "desc": "协调团队进度，组织代码评审"},
    {"user_id": 3, "type": "task_completed", "value": 4.5, "desc": "完成看板任务管理、前端框架搭建等前端核心功能"},
    {"user_id": 3, "type": "code_review", "value": 2.0, "desc": "审查前端代码质量"},
    {"user_id": 4, "type": "task_completed", "value": 5.0, "desc": "完成用户认证、项目管理、消息系统等多个后端API"},
    {"user_id": 4, "type": "code_committed", "value": 4.0, "desc": "高质量代码提交，覆盖核心业务逻辑"},
    {"user_id": 5, "type": "document_written", "value": 4.5, "desc": "编写需求规格说明书、测试计划等关键文档"},
    {"user_id": 5, "type": "bug_found", "value": 2.5, "desc": "发现并报告3个关键缺陷"},
    {"user_id": 6, "type": "task_completed", "value": 3.5, "desc": "完成仪表盘可视化初版"},
    {"user_id": 6, "type": "ui_design", "value": 2.0, "desc": "设计仪表盘图表布局"},
]

for ev in evidence_data:
    ce = ContributionEvidence(
        project_id=1,
        user_id=ev["user_id"],
        evidence_type=ev["type"],
        contribution_value=ev["value"],
        description=ev["desc"],
    )
    db.add(ce)
print(f"  创建 {len(evidence_data)} 条贡献证据")
db.commit()

# ============================================================
# 12. 风险预警
# ============================================================
print("\n=== 创建风险预警 ===")

risks_data = [
    {
        "user_id": None, "target_type": "task", "target_id": 8,
        "risk_type": "task_overdue", "risk_level": "High",
        "risk_score": 75,
        "reason": "任务「实时消息系统」已超过截止日期3天，当前进度仅70%",
        "suggestion": "建议增加人手协助完成WebSocket模块的联调，或调整截止日期",
    },
    {
        "user_id": None, "target_type": "task", "target_id": 12,
        "risk_type": "task_blocked", "risk_level": "Critical",
        "risk_score": 90,
        "reason": "任务「前后端联调」处于BLOCKED状态超过5天，影响后续多个任务",
        "suggestion": "立即召开会议排查阻塞原因，确认CORS和接口对接问题是否已解决",
    },
    {
        "user_id": 6, "target_type": "member", "target_id": None,
        "risk_type": "low_activity", "risk_level": "Medium",
        "risk_score": 55,
        "reason": "成员「孙琪」近7天仅有1条消息发送，活跃度低于团队平均水平",
        "suggestion": "了解成员工作状态，确认是否遇到技术困难或任务分配不合理",
    },
    {
        "user_id": None, "target_type": "task", "target_id": 15,
        "risk_type": "test_coverage_low", "risk_level": "Medium",
        "risk_score": 60,
        "reason": "项目目前无单元测试覆盖，存在质量风险",
        "suggestion": "尽快启动单元测试编写，优先覆盖核心认证和任务管理模块",
    },
]

for r in risks_data:
    ra = RiskAlert(
        project_id=1,
        user_id=r["user_id"],
        target_type=r["target_type"],
        target_id=r["target_id"],
        risk_type=r["risk_type"],
        risk_level=r["risk_level"],
        risk_score=r["risk_score"],
        reason=r["reason"],
        suggestion=r["suggestion"],
        status="open",
    )
    db.add(ra)
print(f"  创建 {len(risks_data)} 条风险预警")
db.commit()

# ============================================================
# 13. 同行评价
# ============================================================
print("\n=== 创建同行评价 ===")

peers_data = [
    {"evaluator": ADMIN_ID, "evaluatee": 3, "score": 85, "comment": "前端开发能力强，任务完成质量高，但需要加强文档意识。"},
    {"evaluator": ADMIN_ID, "evaluatee": 4, "score": 90, "comment": "后端架构清晰，代码质量好，响应速度快，是团队的技术核心。"},
    {"evaluator": ADMIN_ID, "evaluatee": 5, "score": 78, "comment": "文档撰写认真细致，但任务完成速度可以再快一些。"},
    {"evaluator": ADMIN_ID, "evaluatee": 6, "score": 75, "comment": "可视化方面有专长，但主动性有待提高。"},
    {"evaluator": 3, "evaluatee": 4, "score": 88, "comment": "后端接口设计合理，文档齐全，联调时配合度高。"},
    {"evaluator": 3, "evaluatee": 5, "score": 80, "comment": "文档写得很好，测试用例覆盖全面。"},
    {"evaluator": 4, "evaluatee": 3, "score": 82, "comment": "前端组件化做得不错，交互设计有想法。"},
    {"evaluator": 4, "evaluatee": 6, "score": 78, "comment": "图表可视化效果不错，但进度需要加快。"},
    {"evaluator": 5, "evaluatee": 3, "score": 80, "comment": "前端代码规范，组件复用率高。"},
    {"evaluator": 5, "evaluatee": 4, "score": 85, "comment": "后端API设计RESTful规范，异常处理完善。"},
]

for p in peers_data:
    pe = PeerEvaluation(
        project_id=1,
        evaluator_id=p["evaluator"],
        evaluatee_id=p["evaluatee"],
        score=p["score"],
        comment=p["comment"],
        anomaly_flag=0,
    )
    db.add(pe)
print(f"  创建 {len(peers_data)} 条同行评价")
db.commit()

# ============================================================
# 14. Git仓库与提交记录
# ============================================================
print("\n=== 创建 Git 仓库与提交记录 ===")

repo = GitRepository(
    project_id=1,
    repo_name="teamflow",
    repo_url="https://github.com/team/teamflow",
    provider="github",
    default_branch="main",
    sync_status="active",
)
db.add(repo)
db.flush()
print(f"  创建仓库: {repo.repo_name}")

commits_data = [
    {"author_id": ADMIN_ID, "hash": "a1b2c3d", "msg": "feat: 初始化项目结构，配置FastAPI框架", "branch": "main", "files": "README.md,requirements.txt,main.py", "added": 120, "deleted": 0, "days": 43},
    {"author_id": 3, "hash": "e4f5g6h", "msg": "feat: 搭建Vue3前端工程，配置路由和Pinia", "branch": "main", "files": "package.json,vite.config.ts,src/router/index.ts", "added": 350, "deleted": 0, "days": 36},
    {"author_id": 4, "hash": "i7j8k9l", "msg": "feat: 设计数据库表结构，创建17张核心表", "branch": "main", "files": "models/*.py", "added": 280, "deleted": 0, "days": 33},
    {"author_id": 4, "hash": "m0n1o2p", "msg": "feat: 实现用户注册、登录、JWT认证API", "branch": "feature/auth", "files": "api/auth.py,core/security.py,schemas/user.py", "added": 220, "deleted": 30, "days": 30},
    {"author_id": 3, "hash": "q3r4s5t", "msg": "feat: 实现项目列表页和项目详情页", "branch": "feature/project", "files": "views/ProjectList.vue,views/ProjectDetail.vue", "added": 450, "deleted": 0, "days": 28},
    {"author_id": 4, "hash": "u6v7w8x", "msg": "feat: 实现任务CRUD API和看板视图", "branch": "feature/task", "files": "api/tasks.py,views/TasksView.vue", "added": 580, "deleted": 45, "days": 24},
    {"author_id": 3, "hash": "y9z0a1b", "msg": "feat: 实现任务拖拽看板，支持状态流转", "branch": "feature/task", "files": "components/TaskBoard.vue", "added": 320, "deleted": 60, "days": 22},
    {"author_id": 6, "hash": "c2d3e4f", "msg": "feat: 实现仪表盘ECG趋势图和雷达图", "branch": "feature/viz", "files": "views/DashboardView.vue,utils/charts.ts", "added": 480, "deleted": 0, "days": 18},
    {"author_id": 4, "hash": "g5h6i7j", "msg": "feat: 实现WebSocket实时消息系统", "branch": "feature/message", "files": "api/messages.py,views/MessagesView.vue", "added": 650, "deleted": 80, "days": 14},
    {"author_id": 3, "hash": "k8l9m0n", "msg": "fix: 修复CORS跨域配置问题", "branch": "fix/cors", "files": "main.py", "added": 15, "deleted": 5, "days": 6},
    {"author_id": 4, "hash": "o1p2q3r", "msg": "feat: 实现贡献度多维度评分算法", "branch": "feature/collaboration", "files": "api/collaboration.py,models/collaboration.py", "added": 420, "deleted": 30, "days": 10},
    {"author_id": 6, "hash": "s4t5u6v", "msg": "feat: 实现贡献度柱状图和成员卡片组件", "branch": "feature/viz", "files": "views/ContributionView.vue,components/MemberCard.vue", "added": 380, "deleted": 20, "days": 8},
    {"author_id": 3, "hash": "w7x8y9z", "msg": "feat: 实现文档在线编辑和版本管理", "branch": "feature/doc", "files": "views/DocumentsView.vue,components/VersionHistory.vue", "added": 520, "deleted": 40, "days": 10},
    {"author_id": 4, "hash": "a0b1c2d", "msg": "feat: 实现Git Graph协作事件可视化", "branch": "feature/collaboration", "files": "views/GraphView.vue", "added": 450, "deleted": 0, "days": 6},
    {"author_id": 5, "hash": "e3f4g5h", "msg": "docs: 更新需求规格说明书至v2.0", "branch": "main", "files": "docs/需求规格说明书.md", "added": 200, "deleted": 50, "days": 3},
]

for c in commits_data:
    gc = GitCommit(
        repository_id=repo.id,
        project_id=1,
        author_id=c["author_id"],
        commit_hash=c["hash"],
        commit_message=c["msg"],
        branch_name=c["branch"],
        changed_files=c["files"],
        added_lines=c["added"],
        deleted_lines=c["deleted"],
        quality_score=random.randint(70, 95),
        commit_time=dt(c["days"], hour=random.randint(9, 21), minute=random.randint(0, 59)),
    )
    db.add(gc)
print(f"  创建 {len(commits_data)} 条提交记录")
db.commit()

# ============================================================
# 15. AI 建议和报告
# ============================================================
print("\n=== 创建 AI 数据 ===")

ai_suggestion = AITaskSuggestion(
    project_id=1,
    requester_id=ADMIN_ID,
    input_prompt="请根据当前项目进度，分析后续需要优先完成的任务",
    output_json={
        "suggestions": [
            {"title": "优先完成前后端联调", "priority": "critical", "reason": "阻塞多个后续任务"},
            {"title": "完成风险预警模块评审", "priority": "high", "reason": "已进入REVIEW状态"},
            {"title": "启动单元测试编写", "priority": "medium", "reason": "项目测试覆盖率为0"},
        ]
    },
    status="adopted",
)
db.add(ai_suggestion)

report = AIReportHistory(
    project_id=1,
    report_type="weekly",
    generated_by=ADMIN_ID,
    content="# 周报 - 智能协作课设管家\n\n## 本周进展\n- 实时消息系统完成70%\n- 文档协作编辑完成55%\n- 仪表盘可视化完成65%\n\n## 风险项\n- 前后端联调阻塞\n- 测试覆盖率为0\n\n## 下周计划\n- 完成联调\n- 启动单元测试\n- 推进贡献度分析",
)
db.add(report)
print("  创建 AI 建议和周报")
db.commit()

# ============================================================
# 完成
# ============================================================
print("\n" + "=" * 60)
print("示例数据填充完成！")
print("=" * 60)
print("\n登录账户:")
print("  管理员: admin / admin123 (项目负责人)")
print("  成员1: lisi / 123456 (前端开发)")
print("  成员2: wangwu / 123456 (后端开发)")
print("  成员3: zhaoliu / 123456 (文档/测试)")
print("  成员4: sunqi / 123456 (前端可视化)")
print("  教师: teacher_chen / 123456")
print("\n项目: 智能协作课设管家")
print("\n数据统计:")
print(f"  用户: {db.query(User).count()} 个")
print(f"  项目: {db.query(Project).count()} 个")
print(f"  任务: {db.query(Task).count()} 个")
print(f"  里程碑: {db.query(Milestone).count()} 个")
print(f"  消息: {db.query(Message).count()} 条")
print(f"  文档: {db.query(Document).count()} 个")
print(f"  协作事件: {db.query(CollaborationEvent).count()} 条")
print(f"  贡献评分: {db.query(ContributionScore).count()} 条")
print(f"  风险预警: {db.query(RiskAlert).count()} 条")
print(f"  同行评价: {db.query(PeerEvaluation).count()} 条")
print(f"  Git提交: {db.query(GitCommit).count()} 条")

db.close()
