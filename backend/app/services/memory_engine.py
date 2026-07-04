"""
P0-G: 三层记忆系统 — 记忆引擎

自动写入 + 容量衰减 + 按需注入。
"""

import uuid
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.memory import UserProfile, TopicMemory, SessionContext


class MemoryEngine:
    """三层记忆引擎。

    自动写入：M2/M3/M5/M6 服务调用 record_* 方法。
    容量衰减：定时任务触发 decay_old_contexts / archive_topic。
    按需注入：对话开始时调用 get_user_context / get_topic_context。
    """

    # P2-08: 条目数上限
    MAX_RESEARCH_DOMAINS: int = 20
    MAX_KEY_PAPERS: int = 100
    MAX_SESSION_RETENTION_DAYS: int = 365  # 超过此天数永久清理

    # ── P2-09: 统一 session 管理 ──────────────────────

    @classmethod
    def _ensure_db(cls, db: Optional[AsyncSession]):
        """返回一个异步上下文管理器，外部传入则直通，否则创建新 session。"""
        if db is not None:
            from contextlib import asynccontextmanager
            @asynccontextmanager
            async def _pass():
                yield db
            return _pass()
        return AsyncSessionLocal()

    # ── 自动写入 ──────────────────────────────────────

    @staticmethod
    async def _get_or_create_profile(
        db: AsyncSession, user_id: uuid.UUID
    ) -> UserProfile:
        """获取或创建用户画像。"""
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        if profile is None:
            profile = UserProfile(user_id=user_id)
            db.add(profile)
            await db.flush()
        return profile

    @staticmethod
    async def _get_today_context(
        db: AsyncSession, user_id: uuid.UUID
    ) -> SessionContext:
        """获取或创建今日会话上下文。"""
        today = date.today()
        result = await db.execute(
            select(SessionContext).where(
                SessionContext.user_id == user_id,
                SessionContext.session_date == today,
            )
        )
        ctx = result.scalar_one_or_none()
        if ctx is None:
            ctx = SessionContext(user_id=user_id, session_date=today)
            db.add(ctx)
            await db.flush()
        return ctx

    @classmethod
    async def record_search(
        cls,
        user_id: uuid.UUID,
        query: str,
        source: str,
        result_count: int,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """M2 每次检索后自动调用。"""
        try:
            if db is None:
                async with AsyncSessionLocal() as db:
                    await cls._record_search_impl(db, user_id, query, source, result_count)
            else:
                await cls._record_search_impl(db, user_id, query, source, result_count)
        except Exception:
            pass  # 静默失败，不影响主流程

    @staticmethod
    async def _record_search_impl(
        db: AsyncSession, user_id: uuid.UUID,
        query: str, source: str, result_count: int,
    ) -> None:
        ctx = await MemoryEngine._get_today_context(db, user_id)
        queries = list(ctx.search_queries or [])
        queries.append(
            {
                "query": query,
                "source": source,
                "result_count": result_count,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
        )
        ctx.search_queries = queries
        await db.commit()

    @classmethod
    async def record_paper_read(
        cls,
        user_id: uuid.UUID,
        paper_id: str,
        title: str,
        duration: int = 0,
        notes: str = "",
        db: Optional[AsyncSession] = None,
    ) -> None:
        """M3 阅读论文后自动调用。"""
        try:
            async with cls._ensure_db(db) as session:
                ctx = await cls._get_today_context(session, user_id)
                papers = list(ctx.papers_read or [])
                papers.append(
                    {
                        "paper_id": paper_id,
                        "title": title,
                        "duration": duration,
                        "notes": notes,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                ctx.papers_read = papers
                await session.commit()
        except Exception:
            pass

    @classmethod
    async def record_writing(
        cls,
        user_id: uuid.UUID,
        document_id: str,
        words: int,
        sections: int = 0,
        db: Optional[AsyncSession] = None,
    ) -> None:
        """M5 写作后自动调用。"""
        try:
            async with cls._ensure_db(db) as session:
                ctx = await cls._get_today_context(session, user_id)
                writings = list(ctx.writing_sessions or [])
                writings.append(
                    {
                        "document_id": document_id,
                        "words_written": words,
                        "sections": sections,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                ctx.writing_sessions = writings
                await session.commit()
        except Exception:
            pass

    @classmethod
    async def record_sandbox_run(
        cls,
        user_id: uuid.UUID,
        job_id: str,
        algorithm: str,
        status: str = "completed",
        db: Optional[AsyncSession] = None,
    ) -> None:
        """M6 沙箱执行后自动调用。"""
        try:
            async with cls._ensure_db(db) as session:
                ctx = await cls._get_today_context(session, user_id)
                runs = list(ctx.sandbox_runs or [])
                runs.append(
                    {
                        "job_id": job_id,
                        "algorithm": algorithm,
                        "status": status,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    }
                )
                ctx.sandbox_runs = runs
                await session.commit()
        except Exception:
            pass

    # ── 课题记忆 ──────────────────────────────────────

    @classmethod
    async def create_topic(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        topic_name: str,
        workspace_id: Optional[int] = None,
        conventions: Optional[dict] = None,
    ) -> TopicMemory:
        """创建课题记忆。"""
        topic = TopicMemory(
            user_id=user_id,
            topic_name=topic_name,
            workspace_id=workspace_id,
            conventions=conventions or {},
        )
        db.add(topic)
        await db.flush()
        return topic

    @classmethod
    async def record_topic_pitfall(
        cls,
        db: AsyncSession,
        topic_id: int,
        description: str,
    ) -> Optional[TopicMemory]:
        """记录课题踩坑。"""
        result = await db.execute(
            select(TopicMemory).where(TopicMemory.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if topic is None:
            return None
        pitfalls = list(topic.pitfalls or [])
        pitfalls.append(
            {
                "description": description,
                "date": datetime.now(timezone.utc).isoformat(),
            }
        )
        topic.pitfalls = pitfalls
        await db.flush()
        return topic

    @classmethod
    async def archive_topic(cls, db: AsyncSession, topic_id: int) -> bool:
        """归档课题。"""
        result = await db.execute(
            select(TopicMemory).where(TopicMemory.id == topic_id)
        )
        topic = result.scalar_one_or_none()
        if topic is None:
            return False
        topic.status = "archived"
        await db.flush()
        return True

    # ── 容量衰减 ──────────────────────────────────────

    @classmethod
    async def decay_old_contexts(cls, user_id: Optional[uuid.UUID] = None, keep_days: int = 90, db: Optional[AsyncSession] = None) -> int:
        """归档超过 keep_days 天的会话上下文。

        将旧的 session_contexts 合并为月度摘要并删除原始记录。

        Args:
            user_id: 限定用户，None 表示全部用户。
            keep_days: 保留天数，超过此天数的记录被归档。
            db: 可选外部 session，不传则自动创建。

        Returns:
            int: 归档的记录数。
        """
        cutoff = date.today() - timedelta(days=keep_days)
        async with cls._ensure_db(db) as session:
            filters = [SessionContext.session_date < cutoff]
            if user_id is not None:
                filters.append(SessionContext.user_id == user_id)

            result = await session.execute(
                select(SessionContext).where(*filters)
            )
            old_contexts = result.scalars().all()

            count = len(old_contexts)
            for ctx in old_contexts:
                # 合并为 daily_summary 文本
                parts = []
                n_queries = len(ctx.search_queries or [])
                n_papers = len(ctx.papers_read or [])
                n_writing = len(ctx.writing_sessions or [])
                n_sandbox = len(ctx.sandbox_runs or [])
                total_words = sum(
                    w.get("words_written", 0)
                    for w in (ctx.writing_sessions or [])
                )
                parts.append(
                    f"{ctx.session_date}: 检索{n_queries}次, "
                    f"阅读{n_papers}篇论文, 写作{total_words}字, "
                    f"沙箱运行{n_sandbox}次"
                )
                ctx.daily_summary = "\n".join(parts)
                # 清空详细数据以节省空间
                ctx.search_queries = []
                ctx.papers_read = []
                ctx.writing_sessions = []
                ctx.sandbox_runs = []

            await session.commit()
            return count

    @classmethod
    async def purge_expired_contexts(cls, user_id: Optional[uuid.UUID] = None, db: Optional[AsyncSession] = None) -> int:
        """P2-08: 永久清理超过 MAX_SESSION_RETENTION_DAYS 天的会话上下文。

        Args:
            user_id: 限定用户，None 表示全部用户。

        Returns:
            int: 清理的记录数。
        """
        cutoff = date.today() - timedelta(days=cls.MAX_SESSION_RETENTION_DAYS)
        async with cls._ensure_db(db) as session:
            filters = [SessionContext.session_date < cutoff]
            if user_id is not None:
                filters.append(SessionContext.user_id == user_id)

            result = await session.execute(
                select(SessionContext).where(*filters)
            )
            expired = result.scalars().all()
            count = len(expired)
            for ctx in expired:
                await session.delete(ctx)
            await session.commit()
            return count

    # ── 按需注入 ──────────────────────────────────────

    @classmethod
    async def get_user_context(cls, db: AsyncSession, user_id: uuid.UUID) -> Dict[str, Any]:
        """获取轻量用户上下文（注入到每次对话开头）。"""
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()

        # 活跃课题
        result2 = await db.execute(
            select(TopicMemory.topic_name)
            .where(
                TopicMemory.user_id == user_id,
                TopicMemory.status == "active",
            )
            .limit(5)
        )
        active_topics = [row[0] for row in result2.all()]

        return {
            "research_domains": (profile.research_domains or []) if profile else [],
            "preferred_journals": (profile.preferred_journals or []) if profile else [],
            "citation_format": profile.citation_format if profile else "gbt7714",
            "writing_style": profile.writing_style if profile else "academic/strict",
            "preferred_language": profile.preferred_language if profile else "zh",
            "active_topics": active_topics,
        }

    @classmethod
    async def get_topic_context(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        topic_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """获取课题级上下文。"""
        filters = [TopicMemory.user_id == user_id, TopicMemory.status == "active"]
        if topic_name:
            filters.append(TopicMemory.topic_name == topic_name)

        result = await db.execute(
            select(TopicMemory).where(*filters).order_by(TopicMemory.updated_at.desc())
        )
        topics = result.scalars().all()

        return {
            "topics": [
                {
                    "id": t.id,
                    "topic_name": t.topic_name,
                    "conventions": t.conventions,
                    "key_papers_count": len(t.key_papers or []),
                    "pitfalls_count": len(t.pitfalls or []),
                    "status": t.status,
                }
                for t in topics
            ]
        }

    @classmethod
    async def get_recent_context(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        days: int = 7,
    ) -> Dict[str, Any]:
        """获取最近 N 天研学摘要。"""
        since = date.today() - timedelta(days=days)
        result = await db.execute(
            select(SessionContext)
            .where(
                SessionContext.user_id == user_id,
                SessionContext.session_date >= since,
            )
            .order_by(SessionContext.session_date.desc())
        )
        contexts = result.scalars().all()

        total_papers = sum(len(c.papers_read or []) for c in contexts)
        total_queries = sum(len(c.search_queries or []) for c in contexts)
        total_words = sum(
            w.get("words_written", 0)
            for c in contexts
            for w in (c.writing_sessions or [])
        )
        total_sandbox = sum(len(c.sandbox_runs or []) for c in contexts)

        summaries = []
        for c in contexts:
            if c.daily_summary:
                summaries.append(c.daily_summary)
            else:
                n_papers = len(c.papers_read or [])
                n_queries = len(c.search_queries or [])
                words = sum(
                    w.get("words_written", 0)
                    for w in (c.writing_sessions or [])
                )
                n_sandbox = len(c.sandbox_runs or [])
                summaries.append(
                    f"{c.session_date}: 检索{n_queries}次, "
                    f"阅读{n_papers}篇, 写作{words}字, 沙箱{n_sandbox}次"
                )

        return {
            "daily_summaries": summaries,
            "total_papers_read": total_papers,
            "total_search_queries": total_queries,
            "total_words_written": total_words,
            "total_sandbox_runs": total_sandbox,
        }

    @classmethod
    async def search_memory(
        cls,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
    ) -> List[Dict[str, Any]]:
        """按需搜索记忆库。

        搜索范围：topic_memories.key_papers + session_contexts.daily_summary
        """
        results = []

        # 搜索课题记忆的 key_papers
        topics_result = await db.execute(
            select(TopicMemory).where(
                TopicMemory.user_id == user_id,
                TopicMemory.status == "active",
            )
        )
        for topic in topics_result.scalars().all():
            for paper in topic.key_papers or []:
                title = paper.get("title", "")
                if query.lower() in title.lower():
                    results.append(
                        {
                            "type": "key_paper",
                            "source": f"课题「{topic.topic_name}」",
                            "title": title,
                            "note": paper.get("note", ""),
                            "id": paper.get("id", ""),
                        }
                    )
            # 搜索课题名称
            if query.lower() in (topic.topic_name or "").lower():
                results.append(
                    {
                        "type": "topic",
                        "source": "课题记忆",
                        "title": topic.topic_name,
                        "note": f"状态: {topic.status}, 核心论文: {len(topic.key_papers or [])}篇",
                    }
                )

        # 搜索会话上下文摘要
        ctx_result = await db.execute(
            select(SessionContext).where(
                SessionContext.user_id == user_id,
                SessionContext.daily_summary.isnot(None),
            )
        )
        for ctx in ctx_result.scalars().all():
            if ctx.daily_summary and query.lower() in ctx.daily_summary.lower():
                results.append(
                    {
                        "type": "session",
                        "source": f"会话上下文 ({ctx.session_date})",
                        "title": ctx.daily_summary,
                    }
                )

        return results


# 全局单例
memory_engine = MemoryEngine()
