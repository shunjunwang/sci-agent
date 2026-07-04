"""
限流模块 — 内存 + Redis 双后端令牌桶。

- 内存后端（默认）：单 worker 开发环境
- Redis 后端：Lua 原子脚本，多 worker 生产环境

区分登录接口（5次/min，burst=10）和通用 API（60次/min，burst=120）。
限流失败统一返回 SPEC 格式：{code: 1004, message: "...", data: {"retry_after": N}}
"""

import time
from typing import Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from app.config import settings

# ── 内存令牌桶 ───────────────────────────────────────
# IP -> (tokens, last_refill_time)
_memory_bucket: dict[str, tuple[float, float]] = {}


def _memory_allow_request(
    client_ip: str, rate_per_min: int, burst: int
) -> tuple[bool, float]:
    """内存令牌桶：判断是否允许请求。

    Returns:
        (allowed, retry_after_seconds)
    """
    now = time.time()
    capacity = float(burst)
    refill_rate = rate_per_min / 60.0

    tokens, last_time = _memory_bucket.get(client_ip, (capacity, now))
    elapsed = now - last_time
    tokens = min(capacity, tokens + elapsed * refill_rate)

    if tokens >= 1:
        tokens -= 1
        _memory_bucket[client_ip] = (tokens, now)
        return True, 0.0

    _memory_bucket[client_ip] = (tokens, now)
    retry_after = max(0.0, (1.0 - tokens) / refill_rate)
    return False, retry_after


# ── Redis Lua 令牌桶 ─────────────────────────────────

_REDIS_LUA_SCRIPT = """
local key = KEYS[1]
local rate = tonumber(ARGV[1])
local capacity = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = capacity
    last_refill = now
end

local elapsed = math.max(0, now - last_refill)
local refill_rate = rate / 60.0
tokens = math.min(capacity, tokens + elapsed * refill_rate)

if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return {1, 0}
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    local retry_after = math.ceil((requested - tokens) / refill_rate)
    return {0, retry_after}
end
"""


class RedisRateLimiter:
    """Redis 分布式令牌桶限流器。"""

    def __init__(self):
        self._redis = None
        self._lua_sha: Optional[str] = None

    async def _get_redis(self):
        if self._redis is None:
            import redis.asyncio as aioredis

            self._redis = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def _load_script(self) -> str:
        if self._lua_sha is None:
            r = await self._get_redis()
            self._lua_sha = await r.script_load(_REDIS_LUA_SCRIPT)
        return self._lua_sha

    async def allow_request(
        self, client_ip: str, rate_per_min: int, burst: int
    ) -> tuple[bool, float]:
        """Redis 令牌桶：判断是否允许请求。

        Returns:
            (allowed, retry_after_seconds)
        """
        try:
            r = await self._get_redis()
            sha = await self._load_script()
            key = f"rate_limit:{client_ip}"
            result = await r.evalsha(
                sha, 1, key,
                str(rate_per_min), str(burst),
                str(time.time()), "1",
            )
            allowed = bool(result[0])
            retry_after = float(result[1])
            return allowed, retry_after
        except Exception:
            # Redis 不可用时降级为放行（优先可用性）
            return True, 0.0


_redis_limiter = RedisRateLimiter()


# ── 中间件 ───────────────────────────────────────────

def _make_rate_limit_response(retry_after: float) -> JSONResponse:
    """构造统一限流响应。"""
    return JSONResponse(
        status_code=429,
        content={
            "code": 1004,
            "message": "请求过于频繁，请稍后再试",
            "data": {"retry_after": int(retry_after)},
        },
    )


class RateLimitMiddleware(BaseHTTPMiddleware):
    """统一限流中间件，自动区分登录接口与通用接口。"""

    LOGIN_PATHS = {"/api/v1/auth/login", "/api/v1/auth/token"}

    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if path in ("/api/v2/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        is_login = path.rstrip("/") in self.LOGIN_PATHS
        rate_per_min = (
            settings.RATE_LIMIT_LOGIN_PER_MINUTE if is_login
            else settings.RATE_LIMIT_API_PER_MINUTE
        )
        burst = (
            settings.RATE_LIMIT_LOGIN_BURST if is_login
            else settings.RATE_LIMIT_API_BURST
        )

        client_ip = self._get_client_ip(request)

        if settings.RATE_LIMIT_BACKEND == "redis":
            allowed, retry_after = await _redis_limiter.allow_request(
                client_ip, rate_per_min, burst
            )
        else:
            allowed, retry_after = _memory_allow_request(
                client_ip, rate_per_min, burst
            )

        if not allowed:
            return _make_rate_limit_response(retry_after)

        return await call_next(request)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        if request.client and request.client.host:
            return request.client.host
        return "unknown"


# ── 装饰器（兼容旧接口）───────────────────────────────

def rate_limit(rate: int = None, capacity: int = None):
    """装饰器风格限流（兼容旧代码）。

    注意：多 worker 下仅内存后端有效。生产环境建议使用中间件 + Redis 后端。
    """
    _rate = rate if rate is not None else settings.RATE_LIMIT_API_PER_MINUTE
    _capacity = capacity if capacity is not None else settings.RATE_LIMIT_API_BURST

    def decorator(func):
        from functools import wraps

        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            if request is None:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            if request is not None:
                client_ip = RateLimitMiddleware._get_client_ip(
                    RateLimitMiddleware(None), request
                )
                if settings.RATE_LIMIT_BACKEND == "redis":
                    allowed, retry_after = await _redis_limiter.allow_request(
                        client_ip, _rate, _capacity
                    )
                else:
                    allowed, retry_after = _memory_allow_request(
                        client_ip, _rate, _capacity
                    )
                if not allowed:
                    return _make_rate_limit_response(retry_after)
            return await func(*args, **kwargs)

        return wrapper

    return decorator
