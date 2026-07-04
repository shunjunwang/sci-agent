"""
PC2 M2 限流中间件测试
"""

import pytest
from fastapi import Request
from unittest.mock import MagicMock
from app.core.rate_limit import RateLimitMiddleware, rate_limit


@pytest.fixture(autouse=True)
def clear_bucket():
    """每个测试前清空限流桶，避免状态污染"""
    from app.core import rate_limit as rl
    rl._memory_bucket.clear()
    yield


class FakeApp:
    pass


def test_rate_limit_allow():
    """测试正常请求通过限流"""
    from app.core.rate_limit import _memory_allow_request
    ip = "127.0.0.1"
    for _ in range(3):
        allowed, retry = _memory_allow_request(ip, rate_per_min=60, burst=120)
        assert allowed is True
        assert retry == 0.0


def test_rate_limit_exceed():
    """测试超过限制后被拒绝"""
    from app.core.rate_limit import _memory_allow_request
    ip = "192.168.1.1"
    allowed, _ = _memory_allow_request(ip, rate_per_min=1, burst=1)
    assert allowed is True
    allowed, retry = _memory_allow_request(ip, rate_per_min=1, burst=1)
    assert allowed is False
    assert retry > 0


def test_rate_limit_per_ip():
    """测试不同 IP 独立限流"""
    from app.core.rate_limit import _memory_allow_request
    # burst=1 使每个 IP 最多 1 次请求
    allowed, _ = _memory_allow_request("10.0.0.1", rate_per_min=60, burst=1)
    assert allowed is True
    allowed, _ = _memory_allow_request("10.0.0.1", rate_per_min=60, burst=1)
    assert allowed is False
    # 另一个 IP 不受影响
    allowed, _ = _memory_allow_request("10.0.0.2", rate_per_min=60, burst=1)
    assert allowed is True


def test_rate_limit_get_client_ip():
    """测试获取客户端 IP"""
    middleware = RateLimitMiddleware(FakeApp())
    req = MagicMock(spec=Request)
    req.headers = {"x-forwarded-for": "1.2.3.4, 5.6.7.8"}
    req.client = MagicMock()
    req.client.host = "127.0.0.1"
    assert middleware._get_client_ip(req) == "1.2.3.4"

    req.headers = {}
    assert middleware._get_client_ip(req) == "127.0.0.1"

    req.client = None
    assert middleware._get_client_ip(req) == "unknown"


@pytest.mark.asyncio
async def test_rate_limit_decorator_allow():
    """测试限流装饰器通过"""

    @rate_limit(rate=60, capacity=60)
    async def dummy_endpoint(request):
        return {"ok": True}

    req = MagicMock(spec=Request)
    req.headers = {}
    req.client = MagicMock()
    req.client.host = "127.0.0.1"

    result = await dummy_endpoint(request=req)
    # 装饰器在通过时直接返回被装饰函数的返回值（FastAPI 端点会自动序列化）
    assert result == {"ok": True}


@pytest.mark.asyncio
async def test_rate_limit_decorator_block():
    """测试限流装饰器拒绝"""

    @rate_limit(rate=60, capacity=0)
    async def dummy_endpoint(request):
        return {"ok": True}

    req = MagicMock(spec=Request)
    req.headers = {}
    req.client = MagicMock()
    req.client.host = "127.0.0.1"

    result = await dummy_endpoint(request=req)
    # 拒绝时返回 JSONResponse
    assert hasattr(result, "status_code")
    assert result.status_code == 429
