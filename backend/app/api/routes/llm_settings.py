from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.entities import User, UserLLMConfig
from app.services.llm_service import (
    LLMServiceError,
    PROVIDER_PRESETS,
    complete_text,
    env_llm_config,
    get_llm_config,
    mask_api_key,
)


router = APIRouter()


class LLMConfigPayload(BaseModel):
    provider: str = "mimo"
    base_url: str = ""
    api_key: str = ""
    model: str = ""


def _serialize(row: UserLLMConfig | None, db: Session, user_id: int) -> dict[str, Any]:
    effective = get_llm_config(db, user_id)
    return {
        "provider": effective.provider,
        "base_url": effective.base_url,
        "api_key_masked": mask_api_key(effective.api_key),
        "model": effective.model,
        "has_user_override": bool(row and (row.api_key or row.base_url or row.model)),
        "providers": [
            {"key": key, "base_url": preset["base_url"], "model": preset["model"]}
            for key, preset in PROVIDER_PRESETS.items()
        ],
    }


@router.get("/me/llm-config")
def get_config(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    row = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current_user.id).first()
    return _serialize(row, db, current_user.id)


@router.put("/me/llm-config")
def update_config(
    payload: LLMConfigPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    row = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current_user.id).first()
    if not row:
        row = UserLLMConfig(user_id=current_user.id)
        db.add(row)
    row.provider = (payload.provider or "custom").strip() or "custom"
    row.base_url = (payload.base_url or "").strip()
    row.api_key = (payload.api_key or "").strip()
    row.model = (payload.model or "").strip()
    db.commit()
    db.refresh(row)
    return _serialize(row, db, current_user.id)


@router.post("/me/llm-config/test")
def test_config(
    payload: LLMConfigPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """用候选配置发一次最小请求，验证连通性与鉴权。"""
    from app.services.llm_service import LLMConfig

    preset = PROVIDER_PRESETS.get((payload.provider or "").strip() or "custom", {})
    base = env_llm_config()
    # 候选配置中 api_key 若为空，则沿用用户已保存的或服务端默认值，方便只改 model 时测试
    existing = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == current_user.id).first()
    api_key = (payload.api_key or (existing.api_key if existing else "") or base.api_key).strip()
    config = LLMConfig(
        provider=(payload.provider or base.provider).strip(),
        base_url=(payload.base_url or preset.get("base_url") or base.base_url).strip(),
        api_key=api_key,
        model=(payload.model or preset.get("model") or base.model).strip(),
        timeout=base.timeout,
    )
    try:
        reply = complete_text(
            [{"role": "user", "content": "回复两个字：可用"}],
            config=config,
            temperature=0.1,
            max_tokens=16,
        )
        return {"ok": True, "message": "连接成功", "reply": reply[:80]}
    except LLMServiceError as exc:
        return {"ok": False, "message": str(exc)}
    except Exception as exc:  # pragma: no cover - defensive
        raise HTTPException(status_code=500, detail=f"测试失败：{exc}") from exc
