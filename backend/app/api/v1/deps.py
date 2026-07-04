"""
API 依赖注入模块。

提供认证与数据库会话的可复用 FastAPI 依赖。
"""

from typing import Optional
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db as _get_db
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_token
from app.models.user import User


async def get_current_user(
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(_get_db),
) -> User:
    """从 Authorization Header 提取 Bearer Token 并验证用户身份。

    验证流程：解码 Token → 检查黑名单 → 查询用户。

    Args:
        authorization: HTTP Authorization 头。
        db: 数据库会话（由 get_db 注入）。

    Returns:
        User: 当前已认证的用户 ORM 实例。

    Raises:
        UnauthorizedError: Token 缺失、无效、已撤销或用户不存在。
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError(message="缺少有效的认证 Token")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise UnauthorizedError(message="Token 不能为空")

    payload = await decode_token(token)
    if payload is None:
        raise UnauthorizedError(message="Token 无效或已过期")

    # 检查黑名单
    jti = payload.get("jti")
    if jti:
        from app.models.token_blacklist import TokenBlacklist

        stmt = select(TokenBlacklist).where(
            TokenBlacklist.token_jti == jti,
            TokenBlacklist.revoked == True,  # noqa: E712
        )
        result = await db.execute(stmt)
        if result.scalar_one_or_none() is not None:
            raise UnauthorizedError(message="Token 已被撤销")

    user_id_str: Optional[str] = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="Token 载荷无效")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(message="Token 中的用户标识无效")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthorizedError(message="用户不存在或已被删除")

    return user  # type: ignore[return-value]


# 导出数据库依赖的别名，便于统一从 deps 中引用
get_db = _get_db
