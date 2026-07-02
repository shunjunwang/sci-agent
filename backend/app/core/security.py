"""
安全模块 — JWT Token 生成/验证与密码哈希。

使用 python-jose 实现 JWT，passlib + bcrypt 实现密码哈希。
"""

from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from uuid import UUID

from jose import JWTError, jwt
from passlib.context import CryptContext

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
    return pwd_context.verify(plain_password, hashed_password)


def hash_password(password: str) -> str:
    """对明文密码进行 bcrypt 哈希。

    Args:
        password: 明文密码。

    Returns:
        str: bcrypt 哈希字符串。
    """
    return pwd_context.hash(password)


def _build_token(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
) -> str:
    """构建 JWT Token 的内部方法。

    Args:
        subject: Token 主题（通常为 user_id）。
        token_type: Token 类型（access 或 refresh）。
        expires_delta: 过期时间增量。

    Returns:
        str: 编码后的 JWT 字符串。
    """
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": now + expires_delta,
        "iat": now,
        "type": token_type,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(user_id: UUID) -> str:
    """生成访问令牌 (Access Token)。

    Args:
        user_id: 用户 UUID。

    Returns:
        str: JWT access token。
    """
    return _build_token(
        subject=str(user_id),
        token_type="access",
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: UUID) -> str:
    """生成刷新令牌 (Refresh Token)。

    Args:
        user_id: 用户 UUID。

    Returns:
        str: JWT refresh token。
    """
    return _build_token(
        subject=str(user_id),
        token_type="refresh",
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> Optional[dict[str, Any]]:
    """解码并验证 JWT Token。

    Args:
        token: JWT 字符串。

    Returns:
        Optional[dict]: 解码后的 payload；验证失败返回 None。
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[ALGORITHM],
        )
        return payload
    except JWTError:
        return None
