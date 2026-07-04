"""
PC2 M2 缓存模块
支持内存缓存和 Redis 缓存
"""

import json
import time
from typing import Any, Optional
from app.core.config import get_settings

_settings = get_settings()

# 内存缓存存储
_memory_cache: dict[str, tuple[Any, float]] = {}


class Cache:
    """缓存管理器"""

    def __init__(self):
        self._redis = None
        if _settings.CACHE_TYPE == "redis":
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(_settings.REDIS_URL)
            except Exception:
                pass

    async def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if self._redis:
            try:
                data = await self._redis.get(key)
                if data:
                    return json.loads(data)
            except Exception:
                pass
        # 回退到内存缓存
        if key in _memory_cache:
            value, expire_at = _memory_cache[key]
            if time.time() < expire_at:
                return value
            else:
                del _memory_cache[key]
        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """设置缓存"""
        ttl = ttl or _settings.CACHE_TTL
        if self._redis:
            try:
                await self._redis.setex(key, ttl, json.dumps(value, default=str))
                return
            except Exception:
                pass
        # 回退到内存缓存
        _memory_cache[key] = (value, time.time() + ttl)

    async def delete(self, key: str) -> None:
        """删除缓存"""
        if self._redis:
            try:
                await self._redis.delete(key)
            except Exception:
                pass
        _memory_cache.pop(key, None)

    async def clear(self) -> None:
        """清空缓存"""
        if self._redis:
            try:
                await self._redis.flushdb()
            except Exception:
                pass
        _memory_cache.clear()


# 全局缓存实例
cache = Cache()


def make_cache_key(prefix: str, *parts: str) -> str:
    """生成缓存键"""
    return f"{prefix}:{':'.join(parts)}"
