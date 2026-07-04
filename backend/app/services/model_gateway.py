"""
Model Gateway 服务模块。

提供模型列表查询、默认模型获取、Chat 转发（含流式）等核心业务逻辑。
"""

import logging
import uuid
from typing import Any, AsyncGenerator, Optional

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.config import settings
from app.core.encryption import decrypt_api_key
from app.models.model_gateway import ModelProvider, UserModelConfig
from app.schemas.model_gateway import (
    AvailableModel,
    ChatRequest,
    ChatResponse,
    ChatUsage,
)

logger = logging.getLogger(__name__)

# 重试参数
_RETRY_ATTEMPTS = 3
_RETRY_MIN_WAIT = 1
_RETRY_MAX_WAIT = 10


def _is_model_retryable(exc: BaseException) -> bool:
    """判断模型网关异常是否可重试：仅对 5xx 和 TimeoutException 重试。"""
    if isinstance(exc, httpx.TimeoutException):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        return 500 <= exc.response.status_code < 600
    return False


# 模型网关重试装饰器
_model_retry = retry(
    stop=stop_after_attempt(_RETRY_ATTEMPTS),
    wait=wait_exponential(multiplier=1, min=_RETRY_MIN_WAIT, max=_RETRY_MAX_WAIT),
    retry=retry_if_exception_type((httpx.HTTPStatusError, httpx.TimeoutException)),
    reraise=True,
    before_sleep=lambda retry_state: logger.warning(
        "模型网关调用失败（第 %d/%d 次），%s 后重试...",
        retry_state.attempt_number,
        _RETRY_ATTEMPTS,
        f"{retry_state.next_action.sleep:.0f}s" if retry_state.next_action else "即将",
    ),
)


class ModelGatewayService:
    """Model Gateway 服务类。

    负责模型发现的业务逻辑和第三方 API 的请求转发。
    """

    # ── 查询方法 ──────────────────────────────────────────

    async def list_available_models(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[AvailableModel]:
        """列出用户所有可用模型。

        基于用户已配置 API Key 的模型和系统启用的提供商做交集。

        Args:
            db: 数据库异步会话。
            user_id: 当前用户 UUID。

        Returns:
            list[AvailableModel]: 可用模型列表，按优先级降序排列。
        """
        stmt = (
            select(UserModelConfig, ModelProvider)
            .join(ModelProvider, UserModelConfig.provider_id == ModelProvider.id)
            .where(UserModelConfig.user_id == user_id)
            .where(ModelProvider.is_enabled == True)  # noqa: E712
            .order_by(UserModelConfig.priority.desc(), UserModelConfig.created_at.desc())
        )
        result = await db.execute(stmt)
        rows = result.all()

        models: list[AvailableModel] = []
        for config, provider in rows:
            models.append(
                AvailableModel(
                    provider_id=provider.id,
                    provider_name=provider.display_name,
                    model_name=config.model_name,
                    is_default=config.is_default,
                    priority=config.priority,
                )
            )
        return models

    async def get_default_model(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> Optional[AvailableModel]:
        """获取用户默认模型。

        Args:
            db: 数据库异步会话。
            user_id: 当前用户 UUID。

        Returns:
            Optional[AvailableModel]: 默认模型；无默认配置时返回 None。
        """
        stmt = (
            select(UserModelConfig, ModelProvider)
            .join(ModelProvider, UserModelConfig.provider_id == ModelProvider.id)
            .where(UserModelConfig.user_id == user_id)
            .where(UserModelConfig.is_default == True)  # noqa: E712
            .where(ModelProvider.is_enabled == True)  # noqa: E712
            .limit(1)
        )
        result = await db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            return None
        config, provider = row
        return AvailableModel(
            provider_id=provider.id,
            provider_name=provider.display_name,
            model_name=config.model_name,
            is_default=config.is_default,
            priority=config.priority,
        )

    # ── Chat 转发 ─────────────────────────────────────────

    async def chat(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: ChatRequest,
    ) -> ChatResponse:
        """非流式 Chat 转发。

        选定模型 → 解密 API Key → 构建 OpenAI 兼容请求 → httpx 转发。

        Args:
            db: 数据库异步会话。
            user_id: 当前用户 UUID。
            request: Chat 请求体。

        Returns:
            ChatResponse: 包含模型回复和 Token 用量。

        Raises:
            ValueError: 无可用模型或 API Key 未配置。
            httpx.HTTPError: 上游 API 请求失败。
        """
        provider, config, api_key = await self._resolve_model(db, user_id, request.model)
        resolved_model = request.model or config.model_name

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": False,
        }

        logger.info(
            "转发 Chat 请求: provider=%s, model=%s, messages=%d",
            provider.display_name,
            resolved_model,
            len(request.messages),
        )

        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        @_model_retry
        async def _do_chat():
            async with httpx.AsyncClient(timeout=settings.DEFAULT_MODEL_TIMEOUT) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                return response.json()

        data = await _do_chat()

        choice = data["choices"][0]
        usage_data = data.get("usage", {})
        return ChatResponse(
            id=data.get("id", str(uuid.uuid4())),
            model=data.get("model", resolved_model),
            content=choice["message"]["content"],
            usage=ChatUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
        )

    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: ChatRequest,
    ) -> AsyncGenerator[str, None]:
        """流式 Chat 转发。

        以 SSE（Server-Sent Events）格式逐块返回 upstream 响应。

        Args:
            db: 数据库异步会话。
            user_id: 当前用户 UUID。
            request: Chat 请求体。

        Yields:
            str: SSE 格式的数据块（"data: {...}\n\n"）。

        Raises:
            ValueError: 无可用模型或 API Key 未配置。
            httpx.HTTPError: 上游 API 请求失败。
        """
        provider, config, api_key = await self._resolve_model(db, user_id, request.model)
        resolved_model = request.model or config.model_name

        payload: dict[str, Any] = {
            "model": resolved_model,
            "messages": [m.model_dump() for m in request.messages],
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "stream": True,
        }

        logger.info(
            "转发流式 Chat: provider=%s, model=%s, messages=%d",
            provider.display_name,
            resolved_model,
            len(request.messages),
        )

        url = f"{provider.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        @_model_retry
        async def _connect_stream():
            """建立流式连接（含重试），返回已检查状态码的 response。"""
            client = httpx.AsyncClient(timeout=settings.DEFAULT_MODEL_TIMEOUT)
            response = await client.send(
                client.build_request("POST", url, json=payload, headers=headers),
                stream=True,
            )
            response.raise_for_status()
            return client, response

        client, response = await _connect_stream()
        try:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield f"{line}\n\n"
                elif line.strip() == "data: [DONE]":
                    yield "data: [DONE]\n\n"
                    break
        finally:
            await client.aclose()

    # ── 内部方法 ──────────────────────────────────────────

    async def _resolve_model(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        model_name: Optional[str] = None,
    ) -> tuple[ModelProvider, UserModelConfig, str]:
        """解析用户请求的模型，返回 provider、config 和明文 API Key。

        优先按 model_name 精确匹配；未指定则取用户默认模型。

        Args:
            db: 数据库异步会话。
            user_id: 用户 UUID。
            model_name: 请求指定的模型名称，为 None 时使用默认。

        Returns:
            tuple[ModelProvider, UserModelConfig, str]: (提供商, 用户配置, 明文 API Key)。

        Raises:
            ValueError: 无匹配模型或 API Key 缺失。
        """
        if model_name:
            stmt = (
                select(UserModelConfig, ModelProvider)
                .join(ModelProvider, UserModelConfig.provider_id == ModelProvider.id)
                .where(UserModelConfig.user_id == user_id)
                .where(UserModelConfig.model_name == model_name)
                .where(ModelProvider.is_enabled == True)  # noqa: E712
                .limit(1)
            )
        else:
            stmt = (
                select(UserModelConfig, ModelProvider)
                .join(ModelProvider, UserModelConfig.provider_id == ModelProvider.id)
                .where(UserModelConfig.user_id == user_id)
                .where(UserModelConfig.is_default == True)  # noqa: E712
                .where(ModelProvider.is_enabled == True)  # noqa: E712
                .limit(1)
            )

        result = await db.execute(stmt)
        row = result.one_or_none()
        if row is None:
            if model_name:
                raise ValueError(f"未找到可用模型: {model_name}")
            raise ValueError("未设置默认模型，请先配置并设置默认模型")

        config, provider = row
        if not config.api_key_encrypted:
            raise ValueError(f"模型 '{config.model_name}' 未配置 API Key")

        try:
            api_key = decrypt_api_key(config.api_key_encrypted)
        except Exception:
            raise ValueError(f"模型 '{config.model_name}' 的 API Key 解密失败，请重新配置")

        return provider, config, api_key


# 全局单例
gateway_service = ModelGatewayService()
