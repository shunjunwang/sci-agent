"""
Model Gateway 模块单元测试。

测试 Provider 列表、用户配置创建、Chat 模拟、可用模型列表等。
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.model_gateway import ModelProvider, UserModelConfig
from app.schemas.model_gateway import (
    AvailableModel,
    ChatRequest,
    ChatResponse,
    ModelListResponse,
    ProviderCreate,
    ProviderResponse,
    UserModelConfigCreate,
    UserModelConfigResponse,
)
from app.services.model_gateway import ModelGatewayService


# ── Fixtures ──────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """创建 mock 数据库会话。

    Returns:
        AsyncMock: 模拟的 AsyncSession。
    """
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def sample_provider() -> ModelProvider:
    """创建示例 ModelProvider 实例。

    Returns:
        ModelProvider: 示例提供商对象。
    """
    return ModelProvider(
        id=uuid.uuid4(),
        name="openai",
        display_name="OpenAI",
        base_url="https://api.openai.com/v1",
        api_type="openai",
        is_builtin=True,
        is_enabled=True,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def sample_config(sample_provider) -> UserModelConfig:
    """创建示例 UserModelConfig 实例。

    Args:
        sample_provider: 示例提供商。

    Returns:
        UserModelConfig: 示例配置对象。
    """
    return UserModelConfig(
        id=uuid.uuid4(),
        user_id=uuid.uuid4(),
        provider_id=sample_provider.id,
        api_key_encrypted="encrypted-key-placeholder",
        model_name="gpt-4o",
        is_default=True,
        priority=100,
    )


@pytest.fixture
def service():
    """创建 ModelGatewayService 实例。

    Returns:
        ModelGatewayService: 服务实例。
    """
    return ModelGatewayService()


# ── Test: list_available_models ───────────────────────────

class TestListAvailableModels:
    """测试列出可用模型。"""

    @pytest.mark.asyncio
    async def test_list_available_models_returns_results(
        self, service, mock_db, sample_provider, sample_config
    ):
        """有可用模型时应返回非空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = [(sample_config, sample_provider)]
        mock_db.execute.return_value = mock_result

        models = await service.list_available_models(mock_db, sample_config.user_id)

        assert len(models) == 1
        assert models[0].model_name == "gpt-4o"
        assert models[0].provider_name == "OpenAI"
        assert models[0].is_default is True

    @pytest.mark.asyncio
    async def test_list_available_models_empty(self, service, mock_db):
        """无可用模型时应返回空列表。"""
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        models = await service.list_available_models(mock_db, uuid.uuid4())

        assert models == []


# ── Test: get_default_model ───────────────────────────────

class TestGetDefaultModel:
    """测试获取默认模型。"""

    @pytest.mark.asyncio
    async def test_get_default_model_exists(
        self, service, mock_db, sample_provider, sample_config
    ):
        """默认模型存在时应返回正确结果。"""
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = (sample_config, sample_provider)
        mock_db.execute.return_value = mock_result

        model = await service.get_default_model(mock_db, sample_config.user_id)

        assert model is not None
        assert model.model_name == "gpt-4o"
        assert model.is_default is True

    @pytest.mark.asyncio
    async def test_get_default_model_none(self, service, mock_db):
        """无默认模型时应返回 None。"""
        mock_result = MagicMock()
        mock_result.one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        model = await service.get_default_model(mock_db, uuid.uuid4())

        assert model is None


# ── Test: Chat Mock ───────────────────────────────────────

class TestChatMock:
    """测试 Chat 转发（mock）。"""

    @pytest.fixture
    def chat_request(self) -> ChatRequest:
        """创建示例 ChatRequest。

        Returns:
            ChatRequest: 示例请求对象。
        """
        from app.schemas.model_gateway import ChatMessage

        return ChatRequest(
            messages=[
                ChatMessage(role="user", content="Hello"),
            ],
            model="gpt-4o",
            temperature=0.7,
            max_tokens=1024,
        )

    @pytest.mark.asyncio
    async def test_chat_mock_success(
        self, service, mock_db, sample_provider, sample_config, chat_request
    ):
        """模拟 Chat 成功响应。"""
        # Mock _resolve_model
        with patch.object(
            service,
            "_resolve_model",
            new_callable=AsyncMock,
            return_value=(sample_provider, sample_config, "sk-test-key"),
        ):
            # Mock httpx
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "id": "chatcmpl-123",
                "model": "gpt-4o",
                "choices": [{"message": {"content": "Hello, how can I help?"}}],
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 5,
                    "total_tokens": 15,
                },
            }

            with patch("httpx.AsyncClient") as mock_client_cls:
                mock_client = mock_client_cls.return_value.__aenter__.return_value
                mock_client.post.return_value = mock_response

                result = await service.chat(
                    mock_db, sample_config.user_id, chat_request
                )

                assert isinstance(result, ChatResponse)
                assert result.model == "gpt-4o"
                assert "Hello" in result.content
                assert result.usage.total_tokens == 15

    @pytest.mark.asyncio
    async def test_chat_mock_no_api_key(self, service, mock_db, chat_request):
        """API Key 缺失时应抛出 ValueError。"""
        with patch.object(
            service,
            "_resolve_model",
            new_callable=AsyncMock,
            side_effect=ValueError("模型 'gpt-4o' 未配置 API Key"),
        ):
            with pytest.raises(ValueError, match="API Key"):
                await service.chat(mock_db, uuid.uuid4(), chat_request)

    @pytest.mark.asyncio
    async def test_chat_mock_no_model_found(self, service, mock_db, chat_request):
        """模型不存在时应抛出 ValueError。"""
        with patch.object(
            service,
            "_resolve_model",
            new_callable=AsyncMock,
            side_effect=ValueError("未找到可用模型: gpt-4o"),
        ):
            with pytest.raises(ValueError, match="未找到可用模型"):
                await service.chat(mock_db, uuid.uuid4(), chat_request)


# ── Schema 验证测试 ───────────────────────────────────────

class TestSchemas:
    """测试 Pydantic Schema 校验。"""

    def test_provider_create_valid(self):
        """合法的 ProviderCreate 应通过校验。"""
        body = ProviderCreate(
            name="deepseek",
            display_name="DeepSeek",
            base_url="https://api.deepseek.com/v1",
        )
        assert body.name == "deepseek"
        assert body.api_type == "openai"
        assert body.is_enabled is True

    def test_provider_create_invalid_name_too_long(self):
        """name 超长应拒绝。"""
        with pytest.raises(Exception):
            ProviderCreate(
                name="a" * 51,
                display_name="Test",
                base_url="https://api.example.com",
            )

    def test_config_create_api_key_required(self):
        """api_key 为空应拒绝。"""
        with pytest.raises(Exception):
            UserModelConfigCreate(
                provider_id=uuid.uuid4(),
                api_key="",
                model_name="gpt-4o",
            )

    def test_chat_request_empty_messages(self):
        """messages 为空应拒绝。"""
        from app.schemas.model_gateway import ChatRequest

        with pytest.raises(Exception):
            ChatRequest(messages=[])


# ── ProviderResponse model_validate 测试 ──────────────────

class TestProviderResponse:
    """测试 ProviderResponse 的 from_attributes 模式。"""

    def test_from_attributes(self, sample_provider):
        """应从 ORM 对象正确构建响应。"""
        resp = ProviderResponse.model_validate(sample_provider)
        assert resp.id == sample_provider.id
        assert resp.name == sample_provider.name
        assert resp.display_name == "OpenAI"
        assert resp.is_builtin is True
