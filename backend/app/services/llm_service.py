import json
from dataclasses import dataclass
from typing import Any

import httpx
from sqlalchemy.orm import Session

from app.core.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT_SECONDS
from app.models.entities import UserLLMConfig


class LLMServiceError(RuntimeError):
    pass


# 主流 OpenAI 兼容模型提供商预设。所有提供商均走标准 /chat/completions 协议，
# 只需替换 base_url + api_key + model 即可复用同一客户端。
PROVIDER_PRESETS: dict[str, dict[str, str]] = {
    "mimo": {"base_url": "https://token-plan-cn.xiaomimimo.com/v1", "model": "mimo-v2.5-pro"},
    "openai": {"base_url": "https://api.openai.com/v1", "model": "gpt-4o-mini"},
    "deepseek": {"base_url": "https://api.deepseek.com/v1", "model": "deepseek-chat"},
    "qwen": {"base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1", "model": "qwen-plus"},
    "glm": {"base_url": "https://open.bigmodel.cn/api/paas/v4", "model": "glm-4-flash"},
    "moonshot": {"base_url": "https://api.moonshot.cn/v1", "model": "moonshot-v1-8k"},
    "custom": {"base_url": "", "model": ""},
}


@dataclass
class LLMConfig:
    provider: str
    base_url: str
    api_key: str
    model: str
    timeout: float


def env_llm_config() -> LLMConfig:
    """服务端默认配置（来自 .env 的 TEAMFLOW_LLM_*）。"""
    return LLMConfig(
        provider="mimo",
        base_url=LLM_BASE_URL,
        api_key=LLM_API_KEY,
        model=LLM_MODEL,
        timeout=LLM_TIMEOUT_SECONDS,
    )


def get_llm_config(db: Session, user_id: int | None) -> LLMConfig:
    """解析生效配置：用户自配置优先，缺失字段回退到服务端默认与 provider 预设。"""
    base = env_llm_config()
    if not user_id:
        return base
    row = db.query(UserLLMConfig).filter(UserLLMConfig.user_id == user_id).first()
    if not row or not (row.api_key or row.base_url or row.model or row.provider):
        return base
    preset = PROVIDER_PRESETS.get((row.provider or "").strip() or "custom", {})
    return LLMConfig(
        provider=(row.provider or base.provider).strip(),
        base_url=(row.base_url or preset.get("base_url") or base.base_url).strip(),
        api_key=(row.api_key or base.api_key).strip(),
        model=(row.model or preset.get("model") or base.model).strip(),
        timeout=base.timeout,
    )


def mask_api_key(key: str) -> str:
    if not key:
        return ""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}****{key[-4:]}"


def _chat_endpoint(base_url: str) -> str:
    endpoint = base_url.rstrip("/")
    if not endpoint.endswith("/chat/completions"):
        endpoint = f"{endpoint}/chat/completions"
    return endpoint


def _extract_json_object(content: str) -> dict[str, Any] | None:
    if not content:
        return None
    content = content.strip()
    try:
        parsed = json.loads(content)
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        pass

    start = content.find("{")
    end = content.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    try:
        parsed = json.loads(content[start : end + 1])
        return parsed if isinstance(parsed, dict) else None
    except json.JSONDecodeError:
        return None


def _request_chat(
    messages: list[dict[str, str]],
    *,
    config: LLMConfig,
    temperature: float,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    if not (config.api_key and config.base_url and config.model):
        raise LLMServiceError("未配置模型 API Key / Base URL / Model，请在「设置 → AI 模型配置」中填写")

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": temperature,
    }
    if max_tokens is not None:
        payload["max_tokens"] = max_tokens

    try:
        response = httpx.post(
            _chat_endpoint(config.base_url),
            headers={"Authorization": f"Bearer {config.api_key}"},
            json=payload,
            timeout=config.timeout,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:  # pragma: no cover - depends on remote service
        raise LLMServiceError(f"模型服务返回错误: {exc.response.status_code}") from exc
    except httpx.HTTPError as exc:  # pragma: no cover - depends on remote service
        raise LLMServiceError("无法连接模型服务，请检查 base_url 或网络") from exc


def complete_text(
    messages: list[dict[str, str]],
    *,
    config: LLMConfig | None = None,
    temperature: float = 0.4,
    max_tokens: int | None = None,
) -> str:
    data = _request_chat(messages, config=config or env_llm_config(), temperature=temperature, max_tokens=max_tokens)
    try:
        return str(data["choices"][0]["message"]["content"]).strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise LLMServiceError("模型返回内容格式异常") from exc


def complete_json(
    messages: list[dict[str, str]],
    *,
    config: LLMConfig | None = None,
    temperature: float = 0.3,
    max_tokens: int | None = None,
    retries: int = 1,
) -> dict[str, Any]:
    last_error: Exception | None = None
    attempts = max(1, retries + 1)
    for _ in range(attempts):
        try:
            content = complete_text(messages, config=config, temperature=temperature, max_tokens=max_tokens)
            parsed = _extract_json_object(content)
            if parsed is None:
                raise LLMServiceError("模型返回了非 JSON 结果")
            return parsed
        except Exception as exc:
            last_error = exc
    if isinstance(last_error, LLMServiceError):
        raise last_error
    raise LLMServiceError("模型响应解析失败") from last_error
