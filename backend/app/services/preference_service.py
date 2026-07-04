"""
科研偏好配置服务 — 提供偏好读取、更新和默认引用格式查询。

供 M3（知识库）和 M5（AI写作）模块引用。
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.preference import ResearchPreference
from app.schemas.preference import PreferenceResponse, PreferenceUpdateRequest


_DEFAULT_STYLE = "gbt7714"


class PreferenceService:
    """科研偏好配置服务。"""

    @staticmethod
    async def get_preferences(
        db: AsyncSession, user_id: str,
    ) -> PreferenceResponse:
        """获取用户偏好配置；不存在时返回默认值。

        Args:
            db: 数据库会话。
            user_id: 用户 UUID 字符串。

        Returns:
            PreferenceResponse: 偏好配置。
        """
        user_uuid = uuid.UUID(user_id)
        stmt = select(ResearchPreference).where(
            ResearchPreference.user_id == user_uuid,
        )
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref is None:
            return PreferenceResponse(
                user_id=user_id,
                default_citation_style=_DEFAULT_STYLE,
            )

        return PreferenceResponse(
            user_id=str(pref.user_id),
            default_citation_style=pref.default_citation_style,
            preferred_journals=pref.preferred_journals,
            research_keywords=pref.research_keywords,
            writing_language=pref.writing_language,
            auto_save_interval=pref.auto_save_interval,
            created_at=pref.created_at.isoformat() if pref.created_at else None,
            updated_at=pref.updated_at.isoformat() if pref.updated_at else None,
        )

    @staticmethod
    async def update_preferences(
        db: AsyncSession, user_id: str, data: PreferenceUpdateRequest,
    ) -> PreferenceResponse:
        """更新或创建用户偏好配置。

        Args:
            db: 数据库会话。
            user_id: 用户 UUID 字符串。
            data: 更新请求（字段可选）。

        Returns:
            PreferenceResponse: 更新后的偏好配置。
        """
        user_uuid = uuid.UUID(user_id)
        stmt = select(ResearchPreference).where(
            ResearchPreference.user_id == user_uuid,
        )
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref is None:
            pref = ResearchPreference(user_id=user_uuid)
            db.add(pref)

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(pref, key, value)

        await db.commit()
        await db.refresh(pref)

        return PreferenceResponse(
            user_id=str(pref.user_id),
            default_citation_style=pref.default_citation_style,
            preferred_journals=pref.preferred_journals,
            research_keywords=pref.research_keywords,
            writing_language=pref.writing_language,
            auto_save_interval=pref.auto_save_interval,
            created_at=pref.created_at.isoformat() if pref.created_at else None,
            updated_at=pref.updated_at.isoformat() if pref.updated_at else None,
        )

    @staticmethod
    async def get_default_citation_style(
        db: AsyncSession, user_id: str,
    ) -> str:
        """获取用户默认引用格式（供 M3/M5 调用）。

        Args:
            db: 数据库会话。
            user_id: 用户 UUID 字符串。

        Returns:
            str: 引用格式标识（gbt7714 / apa 等）。
        """
        try:
            user_uuid = uuid.UUID(user_id)
            stmt = select(ResearchPreference.default_citation_style).where(
                ResearchPreference.user_id == user_uuid,
            )
            result = await db.execute(stmt)
            style = result.scalar_one_or_none()
            return style if style else _DEFAULT_STYLE
        except Exception:
            return _DEFAULT_STYLE


preference_service = PreferenceService()
