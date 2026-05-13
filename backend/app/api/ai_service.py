from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
import json

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.project import ProjectMember
from app.models.task import Task, Milestone
from app.models.collaboration import AITaskSuggestion, AIReportHistory
from app.core.config import settings

router = APIRouter(prefix="/api/ai", tags=["ai"])


def _check_member(db, project_id, user_id, roles=None):
    member = db.query(ProjectMember).filter(
        ProjectMember.project_id == project_id,
        ProjectMember.user_id == user_id,
        ProjectMember.status == "active"
    ).first()
    if not member:
        raise HTTPException(status_code=403, detail="Not a project member")
    if roles and member.role not in roles:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    return member


def _call_ai(prompt: str) -> Optional[str]:
    """Call AI API if configured, else return None."""
    if not settings.AI_API_KEY:
        return None
    try:
        import httpx
        headers = {"Authorization": f"Bearer {settings.AI_API_KEY}", "Content-Type": "application/json"}
        payload = {
            "model": settings.AI_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 2000,
        }
        resp = httpx.post(f"{settings.AI_API_BASE}/chat/completions", json=payload, headers=headers, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception:
        return None


def _template_planning(project_name: str, members: list, deadline: str, tech_stack: str) -> dict:
    """Rule-based template for task planning when AI API is not available."""
    return {
        "milestones": [
            {"name": "需求分析完成", "dueDate": "待设定"},
            {"name": "系统设计完成", "dueDate": "待设定"},
            {"name": "功能开发完成", "dueDate": "待设定"},
            {"name": "测试与提交", "dueDate": deadline},
        ],
        "tasks": [
            {"title": "需求分析文档", "assigneeRole": "文档负责人", "priority": "high",
             "dependsOn": [], "subtasks": ["用户角色分析", "功能需求描述", "用例图"]},
            {"title": "系统架构设计", "assigneeRole": "技术负责人", "priority": "high",
             "dependsOn": ["需求分析文档"], "subtasks": ["架构图", "技术选型", "接口规范"]},
            {"title": "数据库设计", "assigneeRole": "后端开发", "priority": "high",
             "dependsOn": ["系统架构设计"], "subtasks": ["ER图", "建表SQL", "索引设计"]},
            {"title": "后端接口开发", "assigneeRole": "后端开发", "priority": "high",
             "dependsOn": ["数据库设计"], "subtasks": ["用户模块", "核心业务模块", "接口测试"]},
            {"title": "前端界面开发", "assigneeRole": "前端开发", "priority": "high",
             "dependsOn": ["系统架构设计"], "subtasks": ["页面原型", "组件开发", "联调测试"]},
            {"title": "测试报告", "assigneeRole": "测试负责人", "priority": "medium",
             "dependsOn": ["后端接口开发", "前端界面开发"], "subtasks": ["功能测试", "接口测试", "问题修复"]},
            {"title": "答辩材料准备", "assigneeRole": "全组", "priority": "medium",
             "dependsOn": ["测试报告"], "subtasks": ["PPT制作", "演示脚本", "答辩准备"]},
        ],
        "risks": [
            "前后端联调时间不足，建议提前冻结接口定义",
            "数据库设计需在开发前确定，避免频繁修改",
            "测试时间可能压缩，建议开发过程中同步测试",
        ]
    }


@router.post("/planning")
def ai_planning(project_id: int, data: dict, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id, roles=["leader"])

    project_name = data.get("project_name", "未命名项目")
    members = data.get("members", [])
    deadline = data.get("deadline", "待确定")
    tech_stack = data.get("tech_stack", "")

    prompt = f"""你是一个软件项目经理。请为以下课程设计项目生成详细的任务拆解计划。
项目名称：{project_name}
截止时间：{deadline}
成员：{json.dumps(members, ensure_ascii=False)}
技术栈：{tech_stack}

请返回JSON格式，包含：milestones(里程碑列表，每项含name和dueDate), tasks(任务列表，每项含title/assigneeRole/priority/dependsOn/subtasks), risks(风险列表)。
直接返回JSON，不要加任何说明。"""

    ai_response = _call_ai(prompt)
    if ai_response:
        try:
            result = json.loads(ai_response)
        except Exception:
            result = _template_planning(project_name, members, deadline, tech_stack)
    else:
        result = _template_planning(project_name, members, deadline, tech_stack)

    # Save suggestion
    suggestion = AITaskSuggestion(
        project_id=project_id,
        requester_id=current_user.id,
        input_prompt=prompt,
        output_json=result,
        status="pending"
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    result["suggestion_id"] = suggestion.id
    return result


@router.post("/planning/{suggestion_id}/confirm")
def confirm_planning(suggestion_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    suggestion = db.query(AITaskSuggestion).filter(AITaskSuggestion.id == suggestion_id).first()
    if not suggestion:
        raise HTTPException(status_code=404)
    _check_member(db, suggestion.project_id, current_user.id, roles=["leader"])

    output = suggestion.output_json or {}
    project_id = suggestion.project_id
    created_tasks = 0

    # Create milestones
    for ms in output.get("milestones", []):
        milestone = Milestone(
            project_id=project_id,
            name=ms.get("name", "未命名里程碑"),
            description=ms.get("description", ""),
            created_by_ai=1,
        )
        db.add(milestone)

    # Create tasks
    for t in output.get("tasks", []):
        task = Task(
            project_id=project_id,
            creator_id=current_user.id,
            title=t.get("title", "未命名任务"),
            description=f"负责人角色: {t.get('assigneeRole', '')}\n子任务: {', '.join(t.get('subtasks', []))}",
            priority=t.get("priority", "medium"),
        )
        db.add(task)
        created_tasks += 1

    suggestion.status = "adopted"
    db.commit()
    return {"message": f"已创建 {created_tasks} 个任务和里程碑"}


@router.post("/reports/weekly")
def generate_weekly_report(project_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    _check_member(db, project_id, current_user.id)
    from app.models.project import Project
    from app.models.collaboration import CollaborationEvent
    from app.models.document import Document

    project = db.query(Project).filter(Project.id == project_id).first()
    members = db.query(ProjectMember).filter(ProjectMember.project_id == project_id, ProjectMember.status == "active").all()

    # Gather stats
    done_tasks = db.query(Task).filter(Task.project_id == project_id, Task.status == "DONE").count()
    in_progress = db.query(Task).filter(Task.project_id == project_id, Task.status == "IN_PROGRESS").count()

    member_summaries = []
    for m in members:
        user = db.query(User).filter(User.id == m.user_id).first()
        tasks = db.query(Task).filter(Task.project_id == project_id, Task.assignee_id == m.user_id, Task.status == "DONE").count()
        member_summaries.append(f"- {user.nickname if user else m.user_id}：完成任务 {tasks} 个")

    report_content = f"""# {project.name if project else '项目'} 周报

## 本周完成情况

{chr(10).join(member_summaries)}

## 项目整体进度

- 已完成任务：{done_tasks} 个
- 进行中任务：{in_progress} 个

## 当前风险

请查看项目风险雷达了解详情。

## 下周计划

根据当前进度，建议优先推进进行中的任务并完成评审流程。

---
*报告由 TeamFlow AI 系统自动生成*
"""

    report = AIReportHistory(
        project_id=project_id,
        report_type="weekly",
        generated_by=current_user.id,
        content=report_content,
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return {"report_id": report.id, "content": report_content}
