"""
P0-I: 分享模式 — 受控分享链接 + 水印 + 权限控制
"""

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.share import ShareLink


class ShareServiceError(Exception):
    """分享服务异常。"""

    pass


class ShareService:
    """受控分享服务。"""

    # ── 创建分享链接 ──────────────────────────────────

    async def create_share_link(
        self,
        db: AsyncSession,
        user_id: int,
        document_id: int,
        expires_hours: int = 24,
        max_access_count: int = 5,
        allow_download: bool = False,
        allow_print: bool = False,
        watermark_text: Optional[str] = None,
        require_sms: bool = False,
    ) -> ShareLink:
        """创建受控分享链接。"""
        token = secrets.token_urlsafe(24)
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)

        share = ShareLink(
            user_id=user_id,
            document_id=document_id,
            token=token,
            expires_at=expires_at,
            max_access_count=max_access_count,
            access_count=0,
            allow_download=allow_download,
            allow_print=allow_print,
            watermark_text=watermark_text,
            require_sms=require_sms,
        )
        db.add(share)
        await db.flush()
        await db.refresh(share)
        return share

    # ── 验证分享 ──────────────────────────────────────

    async def verify_share_access(
        self,
        db: AsyncSession,
        token: str,
    ) -> Dict:
        """验证分享令牌是否有效。

        返回：{valid, document_id, permissions, watermark, error}
        """
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == token)
        )
        share = result.scalar_one_or_none()

        if share is None:
            return {"valid": False, "error": "链接不存在"}

        if share.is_revoked:
            return {"valid": False, "error": "链接已被撤销"}

        if share.expires_at and share.expires_at < datetime.now(timezone.utc):
            return {"valid": False, "error": "链接已过期"}

        if share.access_count >= share.max_access_count:
            return {"valid": False, "error": "已达到最大访问次数"}

        return {
            "valid": True,
            "document_id": share.document_id,
            "permissions": {
                "allow_download": share.allow_download,
                "allow_print": share.allow_print,
            },
            "watermark": share.watermark_text,
            "access_count": share.access_count,
            "max_access_count": share.max_access_count,
        }

    # ── 记录访问 ──────────────────────────────────────

    async def record_access(
        self,
        db: AsyncSession,
        token: str,
    ):
        """记录访问次数。"""
        result = await db.execute(
            select(ShareLink).where(ShareLink.token == token)
        )
        share = result.scalar_one_or_none()
        if share:
            share.access_count += 1
            await db.flush()

    # ── 撤销分享 ──────────────────────────────────────

    async def revoke_share(
        self,
        db: AsyncSession,
        token: str,
        user_id: int,
    ) -> bool:
        """撤销分享链接（仅创建者可撤销）。"""
        result = await db.execute(
            select(ShareLink).where(
                ShareLink.token == token,
                ShareLink.user_id == user_id,
            )
        )
        share = result.scalar_one_or_none()
        if share is None:
            return False
        share.is_revoked = True
        await db.flush()
        return True

    # ── 获取我的分享列表 ──────────────────────────────

    async def list_my_shares(
        self,
        db: AsyncSession,
        user_id: int,
    ) -> list:
        """获取用户的分享链接列表。"""
        result = await db.execute(
            select(ShareLink)
            .where(ShareLink.user_id == user_id)
            .order_by(ShareLink.created_at.desc())
        )
        return list(result.scalars().all())


# 全局单例
share_service = ShareService()
