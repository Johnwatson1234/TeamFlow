import json
from collections import defaultdict
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.entities import (
    AIReportHistory,
    ContributionEvidence,
    ContributionScore,
    Document,
    DocumentVersion,
    GitCommit,
    Message,
    ProjectMember,
    Task,
    TaskActivity,
)
from app.services.llm_service import LLMConfig, LLMServiceError, complete_json, get_llm_config
from app.services.presenters import build_user_map, fmt_dt, user_brief
from app.utils.serializers import dump_json, parse_json


IDEA_KEYWORDS = [
    "建议",
    "可以",
    "方案",
    "思路",
    "优化",
    "改成",
    "不如",
    "要不",
    "是否",
    "应该",
    "考虑",
    "idea",
]
COORDINATION_KEYWORDS = [
    "同步",
    "联调",
    "对接",
    "评审",
    "一起",
    "麻烦",
    "辛苦",
    "确认",
    "跟进",
    "配合",
]
RISK_KEYWORDS = [
    "风险",
    "阻塞",
    "bug",
    "异常",
    "问题",
    "延期",
    "超时",
    "失败",
    "缺少",
    "未定义",
]
ACTION_KEYWORDS = [
    "完成",
    "已开发",
    "已更新",
    "已处理",
    "已修复",
    "已提交",
    "已对接",
    "实现",
    "上线",
]
PRIORITY_WEIGHT = {"高": 1.4, "中": 1.1, "低": 0.8}
ROLE_LIBRARY = {
    "执行推进型": ["后端开发", "前端开发", "实施交付"],
    "协调沟通型": ["项目经理助理", "产品经理", "测试协调"],
    "技术攻坚型": ["后端开发", "架构预研", "算法/平台开发"],
    "方案策划型": ["产品策划", "需求分析", "解决方案工程师"],
    "沉淀整理型": ["测试开发", "技术文档", "数据运营"],
}


def get_cached_contribution_payload(db: Session, project_id: int):
    row = (
        db.query(AIReportHistory)
        .filter(AIReportHistory.project_id == project_id, AIReportHistory.report_type == "member_insights")
        .first()
    )
    if not row:
        return None
    payload = parse_json(row.content, None)
    return payload if isinstance(payload, dict) else None


def build_contribution_payload(db: Session, project_id: int, *, prefer_llm: bool, persist: bool, user_id: int | None = None):
    users = build_user_map(db)
    member_rows = db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()
    member_ids = [
        row.user_id
        for row in member_rows
        if row.user_id in users and users[row.user_id].system_role != "teacher"
    ]
    messages = (
        db.query(Message)
        .filter(Message.project_id == project_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    tasks = db.query(Task).filter(Task.project_id == project_id, Task.archived == False).all()  # noqa: E712
    activities = db.query(TaskActivity).filter(TaskActivity.project_id == project_id).all()
    documents = db.query(Document).filter(Document.project_id == project_id, Document.is_deleted == False).all()  # noqa: E712
    versions = db.query(DocumentVersion).join(Document, Document.id == DocumentVersion.document_id).filter(Document.project_id == project_id).all()
    commits = db.query(GitCommit).filter(GitCommit.project_id == project_id).all()

    messages_by_user = defaultdict(list)
    tasks_by_assignee = defaultdict(list)
    tasks_by_creator = defaultdict(list)
    activities_by_user = defaultdict(list)
    docs_by_author = defaultdict(list)
    versions_by_author = defaultdict(list)
    commits_by_user = defaultdict(list)

    for row in messages:
        messages_by_user[row.sender_id].append(row)
    for row in tasks:
        if row.assignee_id:
            tasks_by_assignee[row.assignee_id].append(row)
        tasks_by_creator[row.created_by].append(row)
    for row in activities:
        activities_by_user[row.actor_id].append(row)
    for row in documents:
        docs_by_author[row.author_id].append(row)
    for row in versions:
        versions_by_author[row.author_id].append(row)
    for row in commits:
        commits_by_user[row.user_id].append(row)

    ranking = []
    profiles = []
    evidence_rows = []
    llm_used = False

    for user_id in member_ids:
        metrics = _build_member_metrics(
            messages_by_user[user_id],
            tasks_by_assignee[user_id],
            tasks_by_creator[user_id],
            activities_by_user[user_id],
            docs_by_author[user_id],
            versions_by_author[user_id],
            commits_by_user[user_id],
        )
        score_row = _build_score_row(users[user_id], metrics)
        profile = _build_profile(users[user_id], metrics)
        if prefer_llm:
            llm_profile = _build_profile_with_llm(users[user_id], metrics, get_llm_config(db, user_id))
            if llm_profile:
                profile.update(llm_profile)
                profile["traits"] = profile["strengths"][:3]
                score_row["profile_label"] = profile["profile_label"]
                llm_used = True
        ranking.append(score_row)
        profiles.append(profile)
        evidence_rows.extend(_build_evidence_payload(users[user_id], metrics))

    ranking.sort(key=lambda item: item["total_score"], reverse=True)
    profiles.sort(key=lambda item: item["total_score"], reverse=True)
    evidence_rows.sort(key=lambda item: item["score"], reverse=True)

    payload = {
        "summary": {
            "member_count": len(member_ids),
            "message_count": len(messages),
            "idea_message_count": sum(item["idea_count"] for item in ranking),
            "completed_task_count": sum(item["completed_tasks"] for item in ranking),
            "analysis_mode": "llm" if llm_used else "heuristic",
            "generated_at": fmt_dt(datetime.now()),
            "description": "基于项目消息、任务进展、文档沉淀与协作活动生成个人贡献画像。",
        },
        "ranking": ranking,
        "evidence": [
            {
                "id": index + 1,
                "user": item["user"],
                "evidence_type": item["evidence_type"],
                "summary": item["summary"],
                "score": item["score"],
                "related_type": item["related_type"],
                "related_id": item["related_id"],
                "created_at": fmt_dt(datetime.now()),
            }
            for index, item in enumerate(evidence_rows[:24])
        ],
        "member_profiles": profiles,
    }

    if persist:
        _persist_analysis(db, project_id, payload)
    return payload


def _build_member_metrics(messages, assigned_tasks, created_tasks, activities, documents, versions, commits):
    text_like_messages = [item for item in messages if item.message_type in {"text", "task"}]
    code_messages = [item for item in messages if item.message_type == "code"]
    task_reference_count = len([item for item in messages if item.message_type == "task"])
    message_lengths = [len((item.content or "").strip()) for item in text_like_messages if (item.content or "").strip()]
    avg_message_length = round(sum(message_lengths) / len(message_lengths), 1) if message_lengths else 0

    idea_count = 0
    useful_idea_count = 0
    coordination_count = 0
    risk_count = 0
    action_count = 0
    mention_count = 0
    for item in text_like_messages:
        content = (item.content or "").strip()
        if not content:
            continue
        lowered = content.lower()
        has_idea = _contains_keyword(content, IDEA_KEYWORDS)
        has_coordination = "@" in content or _contains_keyword(content, COORDINATION_KEYWORDS)
        has_risk = _contains_keyword(content, RISK_KEYWORDS)
        has_action = _contains_keyword(content, ACTION_KEYWORDS)
        if has_idea:
            idea_count += 1
            useful_idea_count += 1 if len(content) >= 18 else 0
            useful_idea_count += 1 if has_action or has_risk or "任务" in content or "接口" in content else 0
        if has_coordination:
            coordination_count += 1
        if has_risk:
            risk_count += 1
        if has_action:
            action_count += 1
        mention_count += content.count("@")
        if "idea" in lowered and not has_idea:
            idea_count += 1

    completed_tasks = len([task for task in assigned_tasks if task.status == "DONE"])
    in_progress_tasks = len([task for task in assigned_tasks if task.status == "IN_PROGRESS"])
    review_tasks = len([task for task in assigned_tasks if task.status == "REVIEW"])
    blocked_tasks = len([task for task in assigned_tasks if task.status == "BLOCKED"])
    avg_task_progress = round(sum(task.progress for task in assigned_tasks) / len(assigned_tasks), 1) if assigned_tasks else 0
    weighted_progress = sum(PRIORITY_WEIGHT.get(task.priority, 1.0) * (task.progress / 100) for task in assigned_tasks)
    completed_activities = len([item for item in activities if item.activity_type == "completed"])
    blocked_activities = len([item for item in activities if item.activity_type == "blocked"])
    created_task_count = len(created_tasks)

    document_count = len(documents)
    document_version_count = len(versions)
    total_versions = sum(getattr(item, "modified_words", 0) + getattr(item, "added_words", 0) for item in versions)
    commit_count = len(commits)
    added_lines = sum(item.added_lines for item in commits)

    sample_messages = []
    for item in text_like_messages[:4]:
        prefix = "[任务]" if item.message_type == "task" else "[讨论]"
        sample_messages.append(f"{prefix}{(item.content or '').strip()[:120]}")
    for item in code_messages[:1]:
        sample_messages.append(f"[代码]{(item.content or '').strip()[:80]}")

    task_score = _clamp(
        completed_tasks * 13
        + in_progress_tasks * 5
        + review_tasks * 4
        + weighted_progress * 6
        + completed_activities * 2,
        0,
        35,
    )
    document_score = _clamp(document_count * 4 + document_version_count * 2 + min(total_versions / 200, 2), 0, 10)
    code_score = _clamp(len(code_messages) * 3 + commit_count * 4 + min(added_lines / 120, 4), 0, 15)
    response_score = _clamp(
        useful_idea_count * 4.5
        + coordination_count * 2
        + risk_count * 2
        + task_reference_count * 2.5
        + min(avg_message_length / 18, 3),
        0,
        25,
    )
    stability_score = _clamp(
        5 + completed_tasks * 2 + review_tasks * 1.5 + min(len(activities) * 0.6, 4) - blocked_tasks * 2 - blocked_activities,
        0,
        15,
    )

    return {
        "message_count": len(messages),
        "text_message_count": len(text_like_messages),
        "code_message_count": len(code_messages),
        "task_reference_count": task_reference_count,
        "avg_message_length": avg_message_length,
        "idea_count": idea_count,
        "useful_idea_count": useful_idea_count,
        "coordination_count": coordination_count,
        "risk_count": risk_count,
        "action_count": action_count,
        "mention_count": mention_count,
        "assigned_task_count": len(assigned_tasks),
        "created_task_count": created_task_count,
        "completed_tasks": completed_tasks,
        "in_progress_tasks": in_progress_tasks,
        "review_tasks": review_tasks,
        "blocked_tasks": blocked_tasks,
        "avg_task_progress": avg_task_progress,
        "activity_count": len(activities),
        "completed_activities": completed_activities,
        "document_count": document_count,
        "document_version_count": document_version_count,
        "commit_count": commit_count,
        "added_lines": added_lines,
        "sample_messages": sample_messages,
        "task_score": round(task_score, 1),
        "document_score": round(document_score, 1),
        "code_score": round(code_score, 1),
        "response_score": round(response_score, 1),
        "stability_score": round(stability_score, 1),
    }


def _build_score_row(user, metrics):
    total_score = round(
        metrics["task_score"]
        + metrics["document_score"]
        + metrics["code_score"]
        + metrics["response_score"]
        + metrics["stability_score"],
        1,
    )
    profile_label = _select_profile_label(metrics)
    return {
        "user": user_brief(user),
        "total_score": total_score,
        "task_score": metrics["task_score"],
        "document_score": metrics["document_score"],
        "code_score": metrics["code_score"],
        "response_score": metrics["response_score"],
        "stability_score": metrics["stability_score"],
        "completed_tasks": metrics["completed_tasks"],
        "collaboration_events": metrics["activity_count"] + metrics["message_count"] + metrics["document_count"],
        "message_count": metrics["message_count"],
        "idea_count": metrics["idea_count"],
        "profile_label": profile_label,
    }


def _build_profile(user, metrics):
    profile_label = _select_profile_label(metrics)
    strengths = _build_strengths(profile_label, metrics)
    risks = _build_risks(metrics)
    recommended_roles = ROLE_LIBRARY.get(profile_label, ROLE_LIBRARY["执行推进型"])
    communication_style = _build_communication_style(metrics)
    contribution_summary = _build_contribution_summary(metrics)
    personality_summary = _build_personality_summary(profile_label, metrics)
    return {
        "user": user_brief(user),
        "total_score": round(
            metrics["task_score"]
            + metrics["document_score"]
            + metrics["code_score"]
            + metrics["response_score"]
            + metrics["stability_score"],
            1,
        ),
        "profile_label": profile_label,
        "traits": strengths[:3],
        "communication_style": communication_style,
        "personality_summary": personality_summary,
        "contribution_summary": contribution_summary,
        "strengths": strengths,
        "risks": risks,
        "recommended_roles": recommended_roles,
        "career_recommendation": f"从当前协作轨迹看，更适合优先尝试 {recommended_roles[0]}，中期可向 {recommended_roles[1]} 延展。",
        "metrics": {
            "message_count": metrics["message_count"],
            "idea_count": metrics["idea_count"],
            "task_reference_count": metrics["task_reference_count"],
            "completed_tasks": metrics["completed_tasks"],
            "document_count": metrics["document_count"],
            "document_version_count": metrics["document_version_count"],
            "code_message_count": metrics["code_message_count"],
            "commit_count": metrics["commit_count"],
            "avg_task_progress": metrics["avg_task_progress"],
        },
        "radar": [
            {"name": "讨论活跃", "value": _radar_value(metrics["message_count"] * 14 + metrics["coordination_count"] * 10)},
            {"name": "想法贡献", "value": _radar_value(metrics["idea_count"] * 22 + metrics["useful_idea_count"] * 16)},
            {"name": "任务落地", "value": _radar_value(metrics["completed_tasks"] * 30 + metrics["avg_task_progress"] * 0.6)},
            {"name": "技术输出", "value": _radar_value(metrics["code_message_count"] * 26 + metrics["commit_count"] * 18)},
            {"name": "文档沉淀", "value": _radar_value(metrics["document_count"] * 30 + metrics["document_version_count"] * 14)},
        ],
    }


def _build_profile_with_llm(user, metrics, config: LLMConfig):
    if not (config.api_key and config.base_url and config.model):
        return None

    prompt = {
        "member": user.display_name,
        "metrics": {
            "message_count": metrics["message_count"],
            "idea_count": metrics["idea_count"],
            "useful_idea_count": metrics["useful_idea_count"],
            "coordination_count": metrics["coordination_count"],
            "risk_count": metrics["risk_count"],
            "completed_tasks": metrics["completed_tasks"],
            "avg_task_progress": metrics["avg_task_progress"],
            "document_count": metrics["document_count"],
            "code_message_count": metrics["code_message_count"],
            "commit_count": metrics["commit_count"],
        },
        "sample_messages": metrics["sample_messages"],
        "required_keys": [
            "profile_label",
            "communication_style",
            "personality_summary",
            "contribution_summary",
            "strengths",
            "risks",
            "recommended_roles",
            "career_recommendation",
        ],
    }
    messages = [
        {
            "role": "system",
            "content": "你是课程设计协作分析助手。请根据成员讨论内容和任务轨迹输出简洁、客观、可解释的中文 JSON，不要输出 Markdown。",
        },
        {
            "role": "user",
            "content": (
                "请根据以下成员协作数据，生成成员画像和就业方向建议。"
                "输出必须是 JSON 对象，strengths/risks/recommended_roles 必须是字符串数组，"
                "内容要结合软件工程团队协作场景，避免空话。\n"
                f"{json.dumps(prompt, ensure_ascii=False)}"
            ),
        },
    ]
    try:
        parsed = complete_json(messages, config=config, temperature=0.4, max_tokens=1200, retries=1)
        if not parsed:
            return None
        return {
            "profile_label": parsed.get("profile_label") or _select_profile_label(metrics),
            "communication_style": parsed.get("communication_style") or _build_communication_style(metrics),
            "personality_summary": parsed.get("personality_summary") or _build_personality_summary(_select_profile_label(metrics), metrics),
            "contribution_summary": parsed.get("contribution_summary") or _build_contribution_summary(metrics),
            "strengths": _normalize_text_list(parsed.get("strengths"), _build_strengths(_select_profile_label(metrics), metrics)),
            "risks": _normalize_text_list(parsed.get("risks"), _build_risks(metrics)),
            "recommended_roles": _normalize_text_list(parsed.get("recommended_roles"), ROLE_LIBRARY.get(_select_profile_label(metrics), ROLE_LIBRARY["执行推进型"])),
            "career_recommendation": parsed.get("career_recommendation") or f"更适合优先尝试 {ROLE_LIBRARY.get(_select_profile_label(metrics), ROLE_LIBRARY['执行推进型'])[0]}。",
        }
    except LLMServiceError:
        return None


def _persist_analysis(db: Session, project_id: int, payload: dict):
    db.query(ContributionEvidence).filter(ContributionEvidence.project_id == project_id).delete()
    db.query(ContributionScore).filter(ContributionScore.project_id == project_id).delete()

    for row in payload["ranking"]:
        db.add(
            ContributionScore(
                project_id=project_id,
                user_id=row["user"]["id"],
                total_score=row["total_score"],
                task_score=row["task_score"],
                document_score=row["document_score"],
                code_score=row["code_score"],
                response_score=row["response_score"],
                stability_score=row["stability_score"],
                completed_tasks=row["completed_tasks"],
                collaboration_events=row["collaboration_events"],
            )
        )

    for row in payload["evidence"]:
        db.add(
            ContributionEvidence(
                project_id=project_id,
                user_id=row["user"]["id"],
                evidence_type=row["evidence_type"],
                summary=row["summary"],
                score=row["score"],
                related_type=row["related_type"],
                related_id=row["related_id"],
            )
        )

    snapshot = (
        db.query(AIReportHistory)
        .filter(AIReportHistory.project_id == project_id, AIReportHistory.report_type == "member_insights")
        .first()
    )
    if not snapshot:
        snapshot = AIReportHistory(project_id=project_id, report_type="member_insights")
        db.add(snapshot)
    snapshot.content = dump_json(payload)


def _build_evidence_payload(user, metrics):
    evidence = []
    if metrics["completed_tasks"]:
        evidence.append(
            {
                "user": user_brief(user),
                "evidence_type": "任务",
                "summary": f"完成 {metrics['completed_tasks']} 项任务，推动实际交付落地。",
                "score": round(min(18, metrics["completed_tasks"] * 4.5 + metrics["avg_task_progress"] * 0.05), 1),
                "related_type": "task",
                "related_id": None,
            }
        )
    if metrics["useful_idea_count"]:
        evidence.append(
            {
                "user": user_brief(user),
                "evidence_type": "讨论",
                "summary": f"提出 {metrics['useful_idea_count']} 条有效想法/建议，能把讨论推进到方案层。",
                "score": round(min(16, metrics["useful_idea_count"] * 3.8 + metrics["risk_count"] * 1.2), 1),
                "related_type": "message",
                "related_id": None,
            }
        )
    if metrics["coordination_count"]:
        evidence.append(
            {
                "user": user_brief(user),
                "evidence_type": "协作",
                "summary": f"在讨论中出现 {metrics['coordination_count']} 次主动同步/对接信号，协作参与度较高。",
                "score": round(min(12, metrics["coordination_count"] * 2 + metrics["mention_count"] * 0.5), 1),
                "related_type": "message",
                "related_id": None,
            }
        )
    if metrics["document_count"]:
        evidence.append(
            {
                "user": user_brief(user),
                "evidence_type": "文档",
                "summary": f"沉淀 {metrics['document_count']} 份项目文档，并参与 {metrics['document_version_count']} 次版本演进。",
                "score": round(min(10, metrics["document_count"] * 3 + metrics["document_version_count"] * 1.2), 1),
                "related_type": "document",
                "related_id": None,
            }
        )
    if metrics["code_message_count"] or metrics["commit_count"]:
        evidence.append(
            {
                "user": user_brief(user),
                "evidence_type": "技术",
                "summary": f"输出 {metrics['code_message_count']} 条代码讨论，关联 {metrics['commit_count']} 次代码产出记录。",
                "score": round(min(12, metrics["code_message_count"] * 2.5 + metrics["commit_count"] * 2.5), 1),
                "related_type": "commit",
                "related_id": None,
            }
        )
    return evidence


def _select_profile_label(metrics):
    scored_dimensions = {
        "执行推进型": metrics["task_score"] + metrics["stability_score"] * 0.6,
        "协调沟通型": metrics["response_score"] + metrics["coordination_count"] * 0.8,
        "技术攻坚型": metrics["code_score"] + metrics["code_message_count"] * 1.2 + metrics["commit_count"] * 1.5,
        "方案策划型": metrics["idea_count"] * 3 + metrics["risk_count"] * 1.5,
        "沉淀整理型": metrics["document_score"] + metrics["document_version_count"] * 1.2,
    }
    return max(scored_dimensions, key=scored_dimensions.get)


def _build_strengths(profile_label, metrics):
    strength_map = {
        "执行推进型": [
            f"任务闭环意识较强，已形成 {metrics['completed_tasks']} 项完成记录。",
            "更偏向把讨论快速落到具体执行动作上。",
            "在项目推进节奏上相对稳定，适合承担主线交付工作。",
        ],
        "协调沟通型": [
            f"消息中出现 {metrics['coordination_count']} 次同步/对接信号，说明协作主动性强。",
            "善于把多人讨论重新拉回到同一目标上。",
            "能够在讨论中承担提醒、确认、推进的角色。",
        ],
        "技术攻坚型": [
            f"有 {metrics['code_message_count']} 条代码型输出，技术表达更具体。",
            "偏好直接给出接口、实现方案或代码片段。",
            "适合处理复杂实现或联调中的技术问题。",
        ],
        "方案策划型": [
            f"能持续提出想法与优化建议，当前识别到 {metrics['idea_count']} 条方案型发言。",
            "对风险点、流程改进和结构性问题更敏感。",
            "适合站在整体视角组织方案，而不只盯着单点执行。",
        ],
        "沉淀整理型": [
            f"在文档和资料沉淀上更突出，当前关联 {metrics['document_count']} 份文档。",
            "更擅长把分散信息整理成可复用材料。",
            "适合承担规范、记录、测试与验收配套工作。",
        ],
    }
    return strength_map[profile_label]


def _build_risks(metrics):
    risks = []
    if metrics["message_count"] <= 1:
        risks.append("当前在讨论中的可见度偏低，后续最好补充更多同步信息。")
    if metrics["idea_count"] > metrics["completed_tasks"] * 2 and metrics["completed_tasks"] == 0:
        risks.append("想法输出多于落地证据，建议增加任务承接或完成记录。")
    if metrics["blocked_tasks"] > 0:
        risks.append("名下存在阻塞任务，说明推进过程中还需要更强的风险清理能力。")
    if metrics["document_count"] == 0 and metrics["code_message_count"] == 0 and metrics["completed_tasks"] == 0:
        risks.append("当前留在系统里的直接贡献证据还不够丰富。")
    if not risks:
        risks.append("整体表现较稳，后续可继续加强跨模块协同或复盘沉淀。")
    return risks[:3]


def _build_communication_style(metrics):
    fragments = []
    if metrics["coordination_count"] >= 2:
        fragments.append("会主动同步和推进对接")
    if metrics["risk_count"] >= 1:
        fragments.append("对风险和问题点比较敏感")
    if metrics["avg_message_length"] >= 18:
        fragments.append("表达相对完整，愿意交代背景和方案")
    if metrics["task_reference_count"] >= 1:
        fragments.append("讨论时会把内容和具体任务绑定")
    if not fragments:
        fragments.append("发言更简洁，倾向于按需回应")
    return "；".join(fragments) + "。"


def _build_contribution_summary(metrics):
    return (
        f"本阶段共记录 {metrics['message_count']} 条消息、{metrics['completed_tasks']} 项已完成任务，"
        f"其中 {metrics['idea_count']} 条发言带有明显方案/建议特征，说明贡献不只体现在工作量，也体现在讨论推动力。"
    )


def _build_personality_summary(profile_label, metrics):
    summary_map = {
        "执行推进型": "做事倾向偏务实，关注结果和交付，适合承担明确目标下的核心执行任务。",
        "协调沟通型": "在团队里更像连接器，擅长对齐信息、推进协作、减少沟通损耗。",
        "技术攻坚型": "技术表达更直接，遇到问题时倾向先给方案或实现，适合攻克关键功能点。",
        "方案策划型": "更容易从全局看问题，喜欢先梳理思路、比较方案，再推动团队达成共识。",
        "沉淀整理型": "做事细致，重视结构化和可复用性，适合把项目过程沉淀成标准成果。",
    }
    detail = summary_map[profile_label]
    if metrics["risk_count"] >= 2:
        detail += " 同时具备一定的风险预警意识。"
    return detail


def _contains_keyword(text, keywords):
    return any(keyword in text for keyword in keywords)


def _clamp(value, lower, upper):
    return max(lower, min(upper, value))


def _radar_value(value):
    return int(_clamp(round(value), 10, 100))


def _normalize_text_list(value, default):
    if not isinstance(value, list):
        return default
    cleaned = [str(item).strip() for item in value if str(item).strip()]
    return cleaned[:3] or default
