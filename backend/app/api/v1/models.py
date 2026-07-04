"""
Model Gateway API 路由。

提供模型提供商和用户模型配置的 CRUD 端点，
以及可用模型查询和 Chat 对话转发。
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, delete as sa_delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.encryption import encrypt_api_key
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.model_gateway import ModelProvider, UserModelConfig
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.model_gateway import (
    ChatRequest,
    ChatResponse,
    ModelListResponse,
    ProviderCreate,
    ProviderResponse,
    ProviderUpdate,
    UserModelConfigCreate,
    UserModelConfigResponse,
    UserModelConfigUpdate,
)
from app.services.model_gateway import gateway_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Model Gateway"], dependencies=[Depends(get_current_user)])


# ── Provider 端点 ──────────────────────────────────────────

@router.get("/providers", response_model=APIResponse[list[ProviderResponse]])
async def list_providers(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[list[ProviderResponse]]:
    """获取所有已启用的模型提供商列表。

    Args:
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 提供商列表。
    """
    stmt = select(ModelProvider).where(ModelProvider.is_enabled == True).order_by(ModelProvider.created_at)  # noqa: E712
    result = await db.execute(stmt)
    providers = result.scalars().all()
    return APIResponse(
        code=200,
        message="success",
        data=[ProviderResponse.model_validate(p) for p in providers],
    )


@router.post("/providers", response_model=APIResponse[ProviderResponse])
async def create_provider(
    body: ProviderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ProviderResponse]:
    """创建新的模型提供商。

    Args:
        body: 创建请求体。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 创建后的提供商信息。

    Raises:
        ConflictError: 同名提供商已存在。
    """
    existing = await db.execute(
        select(ModelProvider).where(ModelProvider.name == body.name)
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(message=f"提供商 '{body.name}' 已存在")

    provider = ModelProvider(
        name=body.name,
        display_name=body.display_name,
        base_url=body.base_url,
        api_type=body.api_type,
        is_enabled=body.is_enabled,
    )
    db.add(provider)
    await db.flush()
    await db.refresh(provider)

    logger.info("创建模型提供商: name=%s, display_name=%s", provider.name, provider.display_name)
    return APIResponse(
        code=201,
        message="提供商创建成功",
        data=ProviderResponse.model_validate(provider),
    )


@router.put("/providers/{provider_id}", response_model=APIResponse[ProviderResponse])
async def update_provider(
    provider_id: UUID,
    body: ProviderUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ProviderResponse]:
    """更新模型提供商信息。

    Args:
        provider_id: 提供商 UUID。
        body: 更新请求体。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 更新后的提供商信息。

    Raises:
        NotFoundError: 提供商不存在。
        ForbiddenError: 尝试修改系统内置提供商。
    """
    result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise NotFoundError(message="提供商不存在")

    if provider.is_builtin:
        raise ForbiddenError(message="无法修改系统内置提供商")

    update_data = body.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(provider, field, value)

    await db.flush()
    await db.refresh(provider)

    logger.info("更新模型提供商: id=%s", str(provider_id))
    return APIResponse(
        code=200,
        message="提供商更新成功",
        data=ProviderResponse.model_validate(provider),
    )


@router.delete("/providers/{provider_id}", response_model=APIResponse[None])
async def delete_provider(
    provider_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[None]:
    """删除模型提供商。

    同时级联删除关联的用户配置。

    Args:
        provider_id: 提供商 UUID。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 删除结果。

    Raises:
        NotFoundError: 提供商不存在。
        ForbiddenError: 尝试删除系统内置提供商。
    """
    result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == provider_id)
    )
    provider = result.scalar_one_or_none()
    if provider is None:
        raise NotFoundError(message="提供商不存在")

    if provider.is_builtin:
        raise ForbiddenError(message="无法删除系统内置提供商")

    await db.delete(provider)
    await db.flush()

    logger.info("删除模型提供商: id=%s, name=%s", str(provider_id), provider.name)
    return APIResponse(
        code=200,
        message="提供商已删除",
        data=None,
    )


# ── User Model Config 端点 ────────────────────────────────

@router.get("/configs", response_model=APIResponse[list[UserModelConfigResponse]])
async def list_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[list[UserModelConfigResponse]]:
    """获取当前用户的所有模型配置。

    Args:
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 用户模型配置列表。
    """
    stmt = (
        select(UserModelConfig, ModelProvider)
        .join(ModelProvider, UserModelConfig.provider_id == ModelProvider.id)
        .where(UserModelConfig.user_id == current_user.id)
        .order_by(UserModelConfig.created_at.desc())
    )
    result = await db.execute(stmt)
    rows = result.all()

    configs: list[UserModelConfigResponse] = []
    for config, provider in rows:
        configs.append(
            UserModelConfigResponse(
                id=config.id,
                user_id=config.user_id,
                provider_id=config.provider_id,
                provider_name=provider.display_name,
                model_name=config.model_name,
                is_default=config.is_default,
                priority=config.priority,
                created_at=config.created_at,
            )
        )
    return APIResponse(
        code=200,
        message="success",
        data=configs,
    )


@router.post("/configs", response_model=APIResponse[UserModelConfigResponse])
async def create_config(
    body: UserModelConfigCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserModelConfigResponse]:
    """为用户创建模型配置。

    API Key 在存储前加密。

    Args:
        body: 创建请求体（含明文 API Key）。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 创建后的配置信息。

    Raises:
        NotFoundError: 提供商不存在。
        ConflictError: 同名配置已存在。
    """
    # 验证提供商存在
    provider_result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == body.provider_id)
    )
    provider = provider_result.scalar_one_or_none()
    if provider is None:
        raise NotFoundError(message="提供商不存在")

    # 唯一性检查
    existing = await db.execute(
        select(UserModelConfig).where(
            UserModelConfig.user_id == current_user.id,
            UserModelConfig.provider_id == body.provider_id,
            UserModelConfig.model_name == body.model_name,
        )
    )
    if existing.scalar_one_or_none() is not None:
        raise ConflictError(message=f"模型 '{body.model_name}' 的配置已存在")

    # 如果设为默认，先将其他配置取消默认
    if body.is_default:
        await _unset_user_defaults(db, current_user.id)

    encrypted_key = encrypt_api_key(body.api_key)
    config = UserModelConfig(
        user_id=current_user.id,
        provider_id=body.provider_id,
        api_key_encrypted=encrypted_key,
        model_name=body.model_name,
        is_default=body.is_default,
        priority=body.priority,
    )
    db.add(config)
    await db.flush()
    await db.refresh(config)

    logger.info(
        "创建用户模型配置: user=%s, provider=%s, model=%s",
        str(current_user.id),
        provider.name,
        body.model_name,
    )
    return APIResponse(
        code=201,
        message="模型配置创建成功",
        data=UserModelConfigResponse(
            id=config.id,
            user_id=config.user_id,
            provider_id=config.provider_id,
            provider_name=provider.display_name,
            model_name=config.model_name,
            is_default=config.is_default,
            priority=config.priority,
            created_at=config.created_at,
        ),
    )


@router.put("/configs/{config_id}", response_model=APIResponse[UserModelConfigResponse])
async def update_config(
    config_id: UUID,
    body: UserModelConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserModelConfigResponse]:
    """更新用户模型配置。

    API Key 更新时重新加密存储。

    Args:
        config_id: 配置 UUID。
        body: 更新请求体。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 更新后的配置信息。

    Raises:
        NotFoundError: 配置不存在或不属于当前用户。
    """
    result = await db.execute(
        select(UserModelConfig).where(
            UserModelConfig.id == config_id,
            UserModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundError(message="模型配置不存在")

    if body.api_key is not None:
        config.api_key_encrypted = encrypt_api_key(body.api_key)
    if body.model_name is not None:
        config.model_name = body.model_name
    if body.priority is not None:
        config.priority = body.priority
    if body.is_default is True:
        await _unset_user_defaults(db, current_user.id)
        config.is_default = True
    elif body.is_default is False:
        config.is_default = False

    await db.flush()
    await db.refresh(config)

    provider_result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == config.provider_id)
    )
    provider = provider_result.scalar_one()

    logger.info("更新用户模型配置: id=%s", str(config_id))
    return APIResponse(
        code=200,
        message="模型配置更新成功",
        data=UserModelConfigResponse(
            id=config.id,
            user_id=config.user_id,
            provider_id=config.provider_id,
            provider_name=provider.display_name,
            model_name=config.model_name,
            is_default=config.is_default,
            priority=config.priority,
            created_at=config.created_at,
        ),
    )


@router.delete("/configs/{config_id}", response_model=APIResponse[None])
async def delete_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[None]:
    """删除用户模型配置。

    Args:
        config_id: 配置 UUID。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 删除结果。

    Raises:
        NotFoundError: 配置不存在或不属于当前用户。
    """
    result = await db.execute(
        select(UserModelConfig).where(
            UserModelConfig.id == config_id,
            UserModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundError(message="模型配置不存在")

    await db.delete(config)
    await db.flush()

    logger.info("删除用户模型配置: id=%s, model=%s", str(config_id), config.model_name)
    return APIResponse(
        code=200,
        message="模型配置已删除",
        data=None,
    )


@router.put("/configs/{config_id}/default", response_model=APIResponse[UserModelConfigResponse])
async def set_default_config(
    config_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[UserModelConfigResponse]:
    """将指定配置设为默认模型。

    Args:
        config_id: 配置 UUID。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 更新后的配置信息。

    Raises:
        NotFoundError: 配置不存在或不属于当前用户。
    """
    result = await db.execute(
        select(UserModelConfig).where(
            UserModelConfig.id == config_id,
            UserModelConfig.user_id == current_user.id,
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        raise NotFoundError(message="模型配置不存在")

    await _unset_user_defaults(db, current_user.id)
    config.is_default = True
    await db.flush()
    await db.refresh(config)

    provider_result = await db.execute(
        select(ModelProvider).where(ModelProvider.id == config.provider_id)
    )
    provider = provider_result.scalar_one()

    logger.info("设置默认模型: user=%s, model=%s", str(current_user.id), config.model_name)
    return APIResponse(
        code=200,
        message="默认模型设置成功",
        data=UserModelConfigResponse(
            id=config.id,
            user_id=config.user_id,
            provider_id=config.provider_id,
            provider_name=provider.display_name,
            model_name=config.model_name,
            is_default=config.is_default,
            priority=config.priority,
            created_at=config.created_at,
        ),
    )


# ── 可用模型查询 ─────────────────────────────────────────

@router.get("/available", response_model=APIResponse[ModelListResponse])
async def list_available_models(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ModelListResponse]:
    """列出当前用户所有可用的模型。

    Args:
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 包含可用模型的列表。
    """
    models = await gateway_service.list_available_models(db, current_user.id)
    return APIResponse(
        code=200,
        message="success",
        data=ModelListResponse(models=models, total=len(models)),
    )


# ── Chat 端点 ────────────────────────────────────────────

@router.post("/chat", response_model=APIResponse[ChatResponse])
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> APIResponse[ChatResponse]:
    """发起 Chat 对话（非流式）。

    由 Model Gateway 将请求转发到对应的第三方 API。

    Args:
        body: Chat 请求体。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        APIResponse: 包含模型回复和用量信息。

    Raises:
        ValueError: 无可用模型或 API 配置无效。
    """
    if body.stream:
        # 流式请求不应走此端点，返回错误
        return APIResponse(
            code=400,
            message="流式请求请使用 SSE 端点",
            data=None,
        )

    response = await gateway_service.chat(db, current_user.id, body)
    return APIResponse(
        code=200,
        message="success",
        data=response,
    )


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """发起 Chat 对话（流式 SSE）。

    Args:
        body: Chat 请求体（stream 将自动覆写为 True）。
        db: 数据库会话。
        current_user: 当前认证用户。

    Returns:
        StreamingResponse: SSE 流式响应。
    """
    body.stream = True  # 强制覆盖
    return StreamingResponse(
        gateway_service.chat_stream(db, current_user.id, body),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ── 内部辅助函数 ─────────────────────────────────────────

async def _unset_user_defaults(db: AsyncSession, user_id: UUID) -> None:
    """将用户所有配置的 is_default 设为 False。

    Args:
        db: 数据库会话。
        user_id: 用户 UUID。
    """
    from sqlalchemy import update

    await db.execute(
        update(UserModelConfig)
        .where(UserModelConfig.user_id == user_id)
        .values(is_default=False)
    )
