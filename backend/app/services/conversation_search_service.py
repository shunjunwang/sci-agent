"""
P0-E: 对话搜索服务

支持两种搜索模式：
- title: 标题模糊搜索（SQL LIKE）
- global: 标题 + content_vector 全局搜索

适配 SQLite 后端（不使用 pg_trgm / FTS，使用 LIKE 实现）。
"""

import uuid
from typing import List, Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation


class ConversationSearchService:
    """对话搜索服务。"""

    @staticmethod
    async def search_by_title(
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 20,
    ) -> List[Conversation]:
        """标题模糊搜索。

        使用 SQL LIKE 对标题进行模糊匹配，排除已软删除的对话。

        Args:
            db: 数据库会话。
            user_id: 用户 UUID。
            query: 搜索关键词。
            limit: 返回数量上限。

        Returns:
            匹配的 Conversation 列表（按更新时间倒序）。
        """
        pattern = f"%{query}%"
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
                func.lower(Conversation.title).like(func.lower(pattern)),
            )
            .order_by(
                Conversation.pinned.desc(),
                Conversation.updated_at.desc(),
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def search_global(
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        limit: int = 20,
    ) -> List[Conversation]:
        """全局搜索：标题 + content_vector 全文检索。

        搜索范围：
        - 标题 LIKE 匹配
        - content_vector JSON 文本 LIKE 匹配（语义向量存储的文本片段）

        Args:
            db: 数据库会话。
            user_id: 用户 UUID。
            query: 搜索关键词。
            limit: 返回数量上限。

        Returns:
            匹配的 Conversation 列表（按更新时间倒序）。
        """
        pattern = f"%{query}%"
        stmt = (
            select(Conversation)
            .where(
                Conversation.user_id == user_id,
                Conversation.deleted_at.is_(None),
                (
                    func.lower(Conversation.title).like(func.lower(pattern))
                    | func.lower(func.cast(Conversation.content_vector, func.String)).like(
                        func.lower(pattern)
                    )
                ),
            )
            .order_by(
                Conversation.pinned.desc(),
                Conversation.updated_at.desc(),
            )
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())
