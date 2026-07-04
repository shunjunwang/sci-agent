"""
P0-I: 分享模式 — API 端点
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.share import (
    ShareCreateRequest,
    ShareLinkResponse,
    ShareVerifyResponse,
)
from app.services.share_service import share_service

router = APIRouter(prefix="/share", tags=["分享模式"])


# ── 创建分享链接 ──────────────────────────────────


@router.post("/create", response_model=APIResponse[ShareLinkResponse])
async def create_share(
    req: ShareCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ShareLinkResponse]:
    """创建受控分享链接。"""
    share = await share_service.create_share_link(
        db=db,
        user_id=current_user.id,  # type: ignore[arg-type]
        document_id=req.document_id,
        expires_hours=req.expires_hours,
        max_access_count=req.max_access_count,
        allow_download=req.allow_download,
        allow_print=req.allow_print,
        watermark_text=req.watermark_text,
    )
    return APIResponse(
        code=201,
        message="分享链接已创建",
        data=ShareLinkResponse(
            token=share.token,
            url=f"/api/v1/share/{share.token}",
            expires_at=share.expires_at,
            max_access_count=share.max_access_count,
            access_count=share.access_count,
            allow_download=share.allow_download,
            allow_print=share.allow_print,
            is_revoked=share.is_revoked,
            document_id=share.document_id,
        ),
    )


# ── 验证分享链接（公共端点） ───────────────────────


@router.get("/{token}", response_model=APIResponse[ShareVerifyResponse])
async def verify_share(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> APIResponse[ShareVerifyResponse]:
    """验证分享令牌并返回受控内容元信息。"""
    result = await share_service.verify_share_access(db, token)

    if not result["valid"]:
        error_msg = result.get("error", "denied")
        if error_msg == "链接不存在":
            raise HTTPException(status_code=404, detail="分享链接不存在")
        raise HTTPException(status_code=403, detail=error_msg)

    # 记录访问
    await share_service.record_access(db, token)

    return APIResponse(
        code=200,
        message="success",
        data=ShareVerifyResponse(**result),
    )


# ── 我的分享列表 ──────────────────────────────────


@router.get("/", response_model=APIResponse[list])
async def list_my_shares(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list]:
    """获取当前用户的分享链接列表。"""
    shares = await share_service.list_my_shares(db, current_user.id)  # type: ignore[arg-type]
    items = [
        {
            "token": s.token,
            "url": f"/api/v1/share/{s.token}",
            "document_id": s.document_id,
            "expires_at": s.expires_at.isoformat() if s.expires_at else None,
            "max_access_count": s.max_access_count,
            "access_count": s.access_count,
            "allow_download": s.allow_download,
            "allow_print": s.allow_print,
            "is_revoked": s.is_revoked,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in shares
    ]
    return APIResponse(code=200, message="success", data=items)


# ── 撤销分享 ──────────────────────────────────────


@router.delete("/{token}", response_model=APIResponse[dict])
async def revoke_share(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """撤销分享链接。"""
    ok = await share_service.revoke_share(db, token, current_user.id)  # type: ignore[arg-type]
    if not ok:
        raise HTTPException(status_code=404, detail="分享链接不存在")
    return APIResponse(code=200, message="已撤销", data={"revoked": True})
