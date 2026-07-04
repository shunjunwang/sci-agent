"""
P0-G: 三层记忆系统 — 记忆引擎单元测试

至少 15 个测试。
"""
import uuid
from datetime import date, datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.memory import UserProfile, TopicMemory, SessionContext
from app.services.memory_engine import MemoryEngine

USER_UUID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _profile(user_id=USER_UUID, domains=None, journals=None):
    return UserProfile(
        id=1,
        user_id=user_id,
        research_domains=domains or [],
        preferred_journals=journals or [],
        citation_format="gbt7714",
        writing_style="academic/strict",
        preferred_language="zh",
    )


def _topic(id=1, user_id=USER_UUID, name="测试", status="active",
           key_papers=None, pitfalls=None, conventions=None):
    return TopicMemory(
        id=id, user_id=user_id, topic_name=name,
        conventions=conventions if conventions is not None else {},
        key_papers=key_papers or [], pitfalls=pitfalls or [],
        experiment_templates={}, status=status,
    )


def _ctx(user_id=USER_UUID, dt=None):
    return SessionContext(
        id=1, user_id=user_id, session_date=dt or date.today(),
        daily_summary=None, search_queries=[], papers_read=[],
        writing_sessions=[], sandbox_runs=[],
    )


def _scalar_one_or_none(item=None):
    m = MagicMock()
    m.scalar_one_or_none.return_value = item
    return m


def _scalars_all(items=None):
    scalars = MagicMock()
    scalars.all.return_value = items or []
    result = MagicMock()
    result.scalars.return_value = scalars
    return result


class TestUserProfile:

    @pytest.mark.asyncio
    async def test_get_user_context_existing(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.side_effect = [
            _scalar_one_or_none(_profile(domains=["机器学习"], journals=["Nature"])),
            MagicMock(all=lambda: [("联邦学习",), ("CV",)]),
        ]
        ctx = await eng.get_user_context(db, USER_UUID)
        assert ctx["research_domains"] == ["机器学习"]
        assert ctx["preferred_journals"] == ["Nature"]
        assert ctx["citation_format"] == "gbt7714"
        assert "联邦学习" in ctx["active_topics"]

    @pytest.mark.asyncio
    async def test_get_user_context_empty(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.side_effect = [
            _scalar_one_or_none(None),
            MagicMock(all=lambda: []),
        ]
        ctx = await eng.get_user_context(db, USER_UUID)
        assert ctx["research_domains"] == []
        assert ctx["active_topics"] == []

    @pytest.mark.asyncio
    async def test_get_or_create_profile_new(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one_or_none(None))
        db.add = MagicMock()
        db.flush = AsyncMock()
        profile = await MemoryEngine._get_or_create_profile(db, USER_UUID)
        assert profile.user_id == USER_UUID
        db.add.assert_called_once()


class TestTopicMemory:

    @pytest.mark.asyncio
    async def test_create_topic(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        topic = await eng.create_topic(db, USER_UUID, "联邦学习研究")
        assert topic.topic_name == "联邦学习研究"
        assert topic.user_id == USER_UUID

    @pytest.mark.asyncio
    async def test_create_topic_with_conventions(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.add = MagicMock()
        db.flush = AsyncMock()
        topic = await eng.create_topic(
            db, USER_UUID, "实验001",
            conventions={"naming": "exp001", "format": "IEEE"},
        )
        assert topic.conventions == {"naming": "exp001", "format": "IEEE"}

    @pytest.mark.asyncio
    async def test_archive_topic(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute.return_value = _scalar_one_or_none(_topic(status="active"))
        db.flush = AsyncMock()
        ok = await eng.archive_topic(db, 1)
        assert ok is True

    @pytest.mark.asyncio
    async def test_archive_topic_not_found(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute.return_value = _scalar_one_or_none(None)
        ok = await eng.archive_topic(db, 999)
        assert ok is False

    @pytest.mark.asyncio
    async def test_record_pitfall(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute.return_value = _scalar_one_or_none(_topic(name="课题A", pitfalls=[]))
        db.flush = AsyncMock()
        topic = await eng.record_topic_pitfall(db, 1, "梯度裁剪阈值过大")
        assert topic is not None
        assert len(topic.pitfalls) == 1
        assert topic.pitfalls[0]["description"] == "梯度裁剪阈值过大"

    @pytest.mark.asyncio
    async def test_get_topic_context(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute.return_value = _scalars_all([
            _topic(id=1, name="课题A", status="active"),
            _topic(id=2, name="课题B", status="active"),
        ])
        ctx = await eng.get_topic_context(db, USER_UUID)
        assert len(ctx["topics"]) == 2


class TestSessionAutoRecord:

    @pytest.mark.asyncio
    async def test_record_search(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one_or_none(_ctx()))
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            await MemoryEngine.record_search(USER_UUID, "深度学习", "arxiv", 42)
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_paper_read(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one_or_none(_ctx()))
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            await MemoryEngine.record_paper_read(USER_UUID, "p-1", "Attention", 3600, "notes")
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_writing(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one_or_none(_ctx()))
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            await MemoryEngine.record_writing(USER_UUID, "doc-1", 500, 3)
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_sandbox_run(self):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_scalar_one_or_none(_ctx()))
        db.add = MagicMock()
        db.flush = AsyncMock()
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            await MemoryEngine.record_sandbox_run(USER_UUID, "job-001", "SGD")
            db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_record_failure_not_block_main(self):
        """record_search 不应阻塞主流程（异常被内部捕获，不向上抛出）"""
        try:
            await MemoryEngine.record_search(USER_UUID, "test", "test", 0)
        except Exception as e:
            pytest.fail(f"record_search 不应抛出异常，实际抛出: {e}")


class TestDecay:

    @pytest.mark.asyncio
    async def test_decay_old_contexts(self):
        old_date = date.today() - timedelta(days=100)
        ctx = _ctx(dt=old_date)
        ctx.search_queries = [{"query": "old", "source": "arxiv", "result_count": 10}]
        ctx.papers_read = [{"paper_id": "p1", "title": "Old"}]
        db = AsyncMock()
        db.execute.return_value = _scalars_all([ctx])
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            count = await MemoryEngine.decay_old_contexts(user_id=None, keep_days=90)
            assert count == 1
            assert ctx.daily_summary is not None
            assert len(ctx.daily_summary) > 0

    @pytest.mark.asyncio
    async def test_decay_no_old_contexts(self):
        db = AsyncMock()
        db.execute.return_value = _scalars_all([])
        db.commit = AsyncMock()
        with patch("app.services.memory_engine.AsyncSessionLocal") as m:
            m.return_value.__aenter__.return_value = db
            count = await MemoryEngine.decay_old_contexts()
            assert count == 0


class TestRecentContext:

    @pytest.mark.asyncio
    async def test_get_recent_context_empty(self):
        eng = MemoryEngine()
        db = AsyncMock()
        db.execute.return_value = _scalars_all([])
        ctx = await eng.get_recent_context(db, USER_UUID, days=7)
        assert ctx["total_papers_read"] == 0

    @pytest.mark.asyncio
    async def test_get_recent_context_with_data(self):
        eng = MemoryEngine()
        c = _ctx()
        c.papers_read = [{"paper_id": "p1", "title": "T1"}]
        c.writing_sessions = [{"document_id": "d1", "words_written": 1000}]
        c.sandbox_runs = [{"job_id": "j1", "algorithm": "SGD", "status": "ok"}]
        c.search_queries = [{"query": "q1", "source": "arxiv", "result_count": 5}]
        db = AsyncMock()
        db.execute.return_value = _scalars_all([c])
        ctx = await eng.get_recent_context(db, USER_UUID, days=7)
        assert ctx["total_papers_read"] == 1
        assert ctx["total_words_written"] == 1000


class TestSearchMemory:

    @pytest.mark.asyncio
    async def test_search_memory_match_paper(self):
        eng = MemoryEngine()
        t = _topic(name="联邦学习", key_papers=[
            {"id": "p1", "title": "Federated Averaging", "note": "经典"}
        ])
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.side_effect = [
            _scalars_all([t]),           # topics
            _scalars_all([]),             # session contexts (empty)
        ]
        results = await eng.search_memory(db, USER_UUID, "Federated")
        assert len(results) == 1
        assert results[0]["type"] == "key_paper"

    @pytest.mark.asyncio
    async def test_search_memory_match_topic_name(self):
        eng = MemoryEngine()
        t = _topic(name="深度学习优化", key_papers=[])
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.side_effect = [
            _scalars_all([t]),           # topics
            _scalars_all([]),             # session contexts (empty)
        ]
        results = await eng.search_memory(db, USER_UUID, "优化")
        assert len(results) >= 1

    @pytest.mark.asyncio
    async def test_search_memory_no_match(self):
        eng = MemoryEngine()
        t = _topic(name="联邦学习", key_papers=[
            {"id": "p1", "title": "Federated Averaging", "note": ""}
        ])
        db = AsyncMock()
        db.execute = AsyncMock()
        db.execute.side_effect = [
            _scalars_all([t]),
            _scalars_all([]),
        ]
        results = await eng.search_memory(db, USER_UUID, "量子纠缠")
        assert len(results) == 0
