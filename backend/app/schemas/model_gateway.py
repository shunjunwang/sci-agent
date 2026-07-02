"""
Model Gateway Schema 模块。

定义模型提供商和用户模型配置的 Pydantic 请求/响应模型，
以及 Chat 对话相关的请求与响应结构。
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


# ── Provider ──────────────────────────────────────────────

class ProviderCreate(BaseModel):
    """创建模型提供商的请求体。

    Attributes:
        name: 内部标识名（如 "openai", "deepseek"）。
        display_name: 显示名称（如 "OpenAI", "DeepSeek"）。
        base_url: API 基础地址。
        api_type: API 类型，默认 "openai"。
        is_enabled: 是否启用，默认 True。
    """

    name: str = Field(..., min_length=1, max_length=50, description="内部标识名")
    display_name: str = Field(..., min_length=1, max_length=100, description="显示名称")
    base_url: str = Field(..., min_length=1, max_length=500, description="API 基础地址")
    api_type: str = Field(default="openai", max_length=20, description="API 类型")
    is_enabled: bool = Field(default=True, description="是否启用")


class ProviderUpdate(BaseModel):
    """更新模型提供商的请求体。

    Attributes:
        display_name: 显示名称。
        base_url: API 基础地址。
        api_type: API 类型。
        is_enabled: 是否启用。
    """

    display_name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="显示名称")
    base_url: Optional[str] = Field(default=None, min_length=1, max_length=500, description="API 基础地址")
    api_type: Optional[str] = Field(default=None, max_length=20, description="API 类型")
    is_enabled: Optional[bool] = Field(default=None, description="是否启用")


class ProviderResponse(BaseModel):
    """模型提供商的响应模型。

    Attributes:
        id: 提供商 UUID。
        name: 内部标识名。
        display_name: 显示名称。
        base_url: API 基础地址。
        api_type: API 类型。
        is_builtin: 是否为系统内置。
        is_enabled: 是否启用。
        created_at: 创建时间。
    """

    id: UUID
    name: str
    display_name: str
    base_url: str
    api_type: str
    is_builtin: bool
    is_enabled: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── User Model Config ─────────────────────────────────────

class UserModelConfigCreate(BaseModel):
    """创建用户模型配置的请求体。

    Attributes:
        provider_id: 模型提供商 ID。
        api_key: 明文 API Key（存储前加密）。
        model_name: 模型名称（如 "gpt-4o"）。
        is_default: 是否设为默认。
        priority: 优先级。
    """

    provider_id: UUID = Field(..., description="模型提供商 ID")
    api_key: str = Field(..., min_length=1, description="API Key（明文，将加密存储）")
    model_name: str = Field(..., min_length=1, max_length=100, description="模型名称")
    is_default: bool = Field(default=False, description="是否设为默认配置")
    priority: int = Field(default=0, ge=0, description="优先级")


class UserModelConfigUpdate(BaseModel):
    """更新用户模型配置的请求体。

    Attributes:
        api_key: 明文 API Key（更新时重新加密存储）。
        model_name: 模型名称。
        is_default: 是否设为默认。
        priority: 优先级。
    """

    api_key: Optional[str] = Field(default=None, min_length=1, description="API Key（明文）")
    model_name: Optional[str] = Field(default=None, min_length=1, max_length=100, description="模型名称")
    is_default: Optional[bool] = Field(default=None, description="是否设为默认配置")
    priority: Optional[int] = Field(default=None, ge=0, description="优先级")


class UserModelConfigResponse(BaseModel):
    """用户模型配置的响应模型。

    Attributes:
        id: 配置 UUID。
        user_id: 用户 UUID。
        provider_id: 提供商 UUID。
        provider_name: 提供商名称（冗余，方便前端展示）。
        model_name: 模型名称。
        is_default: 是否为默认配置。
        priority: 优先级。
        created_at: 创建时间。
    """

    id: UUID
    user_id: UUID
    provider_id: UUID
    provider_name: str
    model_name: str
    is_default: bool
    priority: int
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Chat ──────────────────────────────────────────────────

class ChatMessage(BaseModel):
    """聊天消息。

    Attributes:
        role: 角色（system / user / assistant）。
        content: 消息内容。
    """

    role: str = Field(..., description="角色：system / user / assistant")
    content: str = Field(..., description="消息内容")


class ChatRequest(BaseModel):
    """Chat 请求体。

    Attributes:
        messages: 对话消息列表。
        model: 模型名称（可选，不传则使用默认模型）。
        temperature: 采样温度，默认 0.7。
        max_tokens: 最大生成 Token 数，默认 4096。
        stream: 是否流式返回，默认 False。
    """

    messages: list[ChatMessage] = Field(..., min_length=1, description="对话消息列表")
    model: Optional[str] = Field(default=None, description="模型名称，不传使用默认模型")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="采样温度")
    max_tokens: int = Field(default=4096, ge=1, le=131072, description="最大生成 Token 数")
    stream: bool = Field(default=False, description="是否流式返回")


class ChatUsage(BaseModel):
    """Chat Token 用量。

    Attributes:
        prompt_tokens: 提示词 Token 数。
        completion_tokens: 生成 Token 数。
        total_tokens: 总 Token 数。
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatResponse(BaseModel):
    """Chat 响应模型。

    Attributes:
        id: 响应唯一标识。
        model: 使用的模型名称。
        content: 模型回复内容。
        usage: Token 用量信息。
    """

    id: str
    model: str
    content: str
    usage: ChatUsage = Field(default_factory=ChatUsage)


# ── Aggregated ────────────────────────────────────────────

class AvailableModel(BaseModel):
    """可用模型条目。

    Attributes:
        provider_id: 提供商 UUID。
        provider_name: 提供商显示名称。
        model_name: 模型名称。
        is_default: 是否为当前用户默认模型。
        priority: 优先级。
    """

    provider_id: UUID
    provider_name: str
    model_name: str
    is_default: bool
    priority: int


class ModelListResponse(BaseModel):
    """可用模型列表响应。

    Attributes:
        models: 可用模型列表。
        total: 可用模型总数。
    """

    models: list[AvailableModel] = Field(default_factory=list, description="可用模型列表")
    total: int = Field(default=0, description="可用模型总数")
