"""
安全模块 — JWT Token 生成/验证/撤销与密码哈希。

使用 python-jose 实现 JWT，passlib + bcrypt 实现密码哈希。
支持 Token 黑名单机制，登出/刷新后立即失效。
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings

# ── 密码上下文 ───────────────────────────────────────
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ── JWT 算法 ─────────────────────────────────────────
ALGORITHM = "HS256"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """校验明文密码与哈希值是否匹配。

    Args:
        plain_password: 明文密码。
        hashed_password: bcrypt 哈希后的密码。

    Returns:
        bool: 匹配返回 True。
    """
    return pwd_context.verify(plain_password, hashed_password)  # type: ignore[no-any-return]


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希。

    Args:
        password: 明文密码。

    Returns:
        str: bcrypt 哈希字符串。
    """
    return pwd_context.hash(password)  # type: ignore[no-any-return]


def _generate_jti() -> str:
    """生成 JWT Token 唯一标识符 (JWT ID)。

    Returns:
        str: 32 字符的 hex UUID。
    """
    return uuid.uuid4().hex


def _build_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    jti: Optional[str] = None,
    role: str = "user",
) -> tuple[str, str, datetime]:
    """构建 JWT Token 的内部方法。

    Args:
        subject: Token 主题（通常为 user_id）。
        token_type: Token 类型（access 或 refresh）。
        expires_delta: 过期时间增量。
        jti: JWT ID，不传则自动生成。
        role: 用户角色，写入 JWT payload。

    Returns:
        tuple: (编码后的 JWT 字符串, jti, 过期时间)。
    """
    now = datetime.now(timezone.utc)
    exp = now + expires_delta
    _jti = jti or _generate_jti()
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": exp,
        "iat": now,
        "type": token_type,
        "jti": _jti,
        "role": role,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM), _jti, exp


def create_access_token(user_id: uuid.UUID, role: str = "user") -> tuple[str, str, datetime]:
    """生成访问令牌 (Access Token)。

    Args:
        user_id: 用户 UUID。
        role: 用户角色，写入 JWT payload。

    Returns:
        tuple: (JWT access token, jti, 过期时间)。
    """
    return _build_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        role=role,
    )


def create_refresh_token(user_id: uuid.UUID) -> tuple[str, str, datetime]:
    """生成刷新令牌 (Refresh Token)。

    Args:
        user_id: 用户 UUID。

    Returns:
        tuple: (JWT refresh token, jti, 过期时间)。
    """
    return _build_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


async def decode_token(
    token: str,
    db: Optional[AsyncSession] = None,
) -> Optional[dict[str, Any]]:
    """解码并验证 JWT Token，可选集成黑名单检查。

    Args:
        token: JWT 字符串。
        db: 数据库会话（传入则自动检查 Token 是否已撤销）。

    Returns:
        Optional[dict]: 解码后的 payload；验证失败返回 None。

    Raises:
        TokenRevokedError: Token 已被撤销（仅当 db 参数传入时）。
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
    except JWTError:
        return None

    if db is not None:
        jti = payload.get("jti")
        if jti and await is_token_revoked(db, jti):
            from app.core.exceptions import TokenRevokedError
            raise TokenRevokedError()

    return payload  # type: ignore[no-any-return]


async def revoke_token(
    db: AsyncSession,
    token_jti: str,
    user_id: uuid.UUID,
    token_type: str,
    expires_at: datetime,
) -> None:
    """将 Token 加入黑名单。

    Args:
        db: 数据库会话。
        token_jti: Token 的 JWT ID。
        user_id: 用户 UUID。
        token_type: Token 类型。
        expires_at: Token 过期时间。
    """
    from app.models.token_blacklist import TokenBlacklist

    # 查找已有记录——若存在则设为 revoked，否则新建
    stmt = select(TokenBlacklist).where(TokenBlacklist.token_jti == token_jti)
    result = await db.execute(stmt)
    existing = result.scalar_one_or_none()
    if existing is not None:
        if not existing.revoked:
            existing.revoked = True
            await db.commit()
        return

    entry = TokenBlacklist(
        token_jti=token_jti,
        user_id=user_id,
        token_type=token_type,
        expires_at=expires_at,
    )
    db.add(entry)
    await db.commit()


async def is_token_revoked(db: AsyncSession, token_jti: str) -> bool:
    """检查 Token 是否已被撤销。

    Args:
        db: 数据库会话。
        token_jti: Token 的 JWT ID。

    Returns:
        bool: 已撤销返回 True。
    """
    from app.models.token_blacklist import TokenBlacklist

    stmt = select(TokenBlacklist).where(
        TokenBlacklist.token_jti == token_jti,
        TokenBlacklist.revoked == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none() is not None


async def revoke_all_user_tokens(
    db: AsyncSession,
    user_id: uuid.UUID,
    token_type: Optional[str] = None,
) -> int:
    """撤销用户的所有（或指定类型）Token。

    Args:
        db: 数据库会话。
        user_id: 用户 UUID。
        token_type: 可选，指定 Token 类型。

    Returns:
        int: 已撤销的 Token 数量。
    """
    from app.models.token_blacklist import TokenBlacklist

    conditions = [TokenBlacklist.user_id == user_id]
    if token_type:
        conditions.append(TokenBlacklist.token_type == token_type)

    stmt = select(TokenBlacklist).where(*conditions)
    result = await db.execute(stmt)
    entries = result.scalars().all()

    count = 0
    for entry in entries:
        if not entry.revoked:
            entry.revoked = True
            count += 1

    if count > 0:
        await db.commit()

    return count


async def get_user_sessions(
    db: AsyncSession,
    user_id: uuid.UUID,
) -> list[dict[str, Any]]:
    """获取用户的活跃 Token 列表。

    仅返回未过期且未被撤销的 Token。

    Args:
        db: 数据库会话。
        user_id: 用户 UUID。

    Returns:
        list[dict]: 活跃 Token 列表。
    """
    from app.models.token_blacklist import TokenBlacklist

    now = datetime.now(timezone.utc)
    stmt = select(TokenBlacklist).where(
        TokenBlacklist.user_id == user_id,
        TokenBlacklist.revoked == False,  # noqa: E712
        TokenBlacklist.expires_at > now,
    )
    result = await db.execute(stmt)
    entries = result.scalars().all()

    return [
        {
            "jti": e.token_jti,
            "token_type": e.token_type,
            "expires_at": e.expires_at.isoformat(),
            "created_at": e.created_at.isoformat(),
        }
        for e in entries
    ]
