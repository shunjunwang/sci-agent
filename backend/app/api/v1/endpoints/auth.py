"""用户认证 API"""
from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.core.exceptions import BadRequestError, UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_user_sessions,
    hash_password,
    is_token_revoked,
    revoke_token,
    verify_password,
)
from app.models.user import User
from app.schemas.user import (
    PasswordChange,
    ResetPasswordConfirm,
    ResetPasswordRequest,
    Token,
    UserCreate,
    UserLogin,
    UserPublic,
    UserUpdate,
)

router = APIRouter()
security = HTTPBearer(auto_error=False)


@router.post("/register", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """用户注册"""
    result = await db.execute(select(User).where(User.email == user_in.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise BadRequestError(message="该邮箱已被注册")

    user = User(
        email=user_in.email,
        full_name=user_in.full_name,
        institution=user_in.institution or "",
        hashed_password=hash_password(user_in.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.post("/login", response_model=Token)
async def login(
    login_in: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """用户登录"""
    result = await db.execute(select(User).where(User.email == login_in.email))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError(message="邮箱或密码错误")

    if not verify_password(login_in.password, user.hashed_password):
        raise UnauthorizedError(message="邮箱或密码错误")

    if not user.is_active:
        raise UnauthorizedError(message="账号已被禁用")

    user.last_login_at = datetime.now(timezone.utc)
    await db.commit()

    access_token, access_jti, access_exp = create_access_token(user.id)
    refresh_token, refresh_jti, refresh_exp = create_refresh_token(user.id)

    # 将 refresh token 登记为活跃 session
    await _register_active_token(
        db, user.id, refresh_jti, "refresh", refresh_exp
    )

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """刷新访问令牌 — 撤销旧 refresh token，签发新的 token 对。

    需要在 Authorization header 中传入当前的 refresh token。
    """
    if not credentials or not credentials.credentials:
        raise UnauthorizedError(message="缺少刷新令牌")

    token = credentials.credentials

    payload = await decode_token(token)
    if not payload or payload.get("type") != "refresh":
        raise UnauthorizedError(message="无效的刷新令牌")

    # 检查黑名单
    jti = payload.get("jti")
    if jti and await is_token_revoked(db, jti):
        raise UnauthorizedError(message="刷新令牌已被撤销")

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedError(message="令牌载荷无效")

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise UnauthorizedError(message="令牌中的用户标识无效")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise UnauthorizedError(message="用户不存在或已被禁用")

    # 撤销旧的 refresh token
    if jti:
        old_exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        await revoke_token(db, jti, user_id, "refresh", old_exp)

    new_access_token, access_jti, access_exp = create_access_token(user.id)
    new_refresh_token, refresh_jti, refresh_exp = create_refresh_token(user.id)

    # 登记新的 refresh token
    await _register_active_token(
        db, user_id, refresh_jti, "refresh", refresh_exp
    )

    return Token(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserPublic)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> Any:
    """获取当前用户信息"""
    return current_user


@router.put("/me", response_model=UserPublic)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """更新当前用户信息"""
    update_data = user_update.dict(exclude_unset=True)

    for field, value in update_data.items():
        setattr(current_user, field, value)

    current_user.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(current_user)

    return current_user


@router.post("/me/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """修改密码"""
    if not verify_password(password_change.current_password, current_user.hashed_password):
        raise BadRequestError(message="当前密码错误")

    current_user.hashed_password = hash_password(password_change.new_password)
    current_user.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {"message": "密码修改成功"}


@router.post("/reset-password-request")
async def reset_password_request(
    reset_request: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """请求重置密码（发送重置邮件）"""
    result = await db.execute(select(User).where(User.email == reset_request.email))
    user = result.scalar_one_or_none()

    if user and user.is_active:
        pass

    return {"message": "如果邮箱存在，重置链接已发送"}


@router.post("/reset-password-confirm")
async def reset_password_confirm(
    reset_confirm: ResetPasswordConfirm,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """确认重置密码"""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="重置密码功能暂未实现",
    )


@router.post("/logout")
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """用户登出 — 撤销当前 access token。

    需要在 Authorization header 中传入当前的 access token。
    """
    if not credentials or not credentials.credentials:
        return {"message": "登出成功"}

    payload = await decode_token(credentials.credentials)
    if payload:
        jti = payload.get("jti")
        token_type = payload.get("type", "access")
        user_id_str = payload.get("sub")
        exp_ts = payload.get("exp")

        if jti and user_id_str and exp_ts:
            try:
                user_id = UUID(user_id_str)
                expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc)
                await revoke_token(db, jti, user_id, token_type, expires_at)
            except (ValueError, OSError):
                pass

    return {"message": "登出成功"}


@router.get("/sessions")
async def list_sessions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """列出当前用户的所有活跃 Token 会话。"""
    sessions = await get_user_sessions(db, current_user.id)
    return {"sessions": sessions, "count": len(sessions)}


# ── 内部辅助 ─────────────────────────────────────────

async def _register_active_token(
    db: AsyncSession,
    user_id: UUID,
    token_jti: str,
    token_type: str,
    expires_at: datetime,
) -> None:
    """在 DB 中登记一个活跃 Token 记录（用于 session 追踪）。

    此函数直接插入一条 revoked=False 的记录，
    与 revoke_token（revoked=True）互补。
    """
    from app.models.token_blacklist import TokenBlacklist

    entry = TokenBlacklist(
        token_jti=token_jti,
        user_id=user_id,
        token_type=token_type,
        expires_at=expires_at,
        revoked=False,
    )
    db.add(entry)
    await db.commit()
