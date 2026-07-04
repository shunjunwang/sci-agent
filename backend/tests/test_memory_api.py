"""
P0-G: 三层记忆系统 — API 端点单元测试

测试策略：直接调用路由处理函数，注入 mock db + current_user。
项目其他测试（test_conversation_manager.py 等）也采用此模式。
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import pytest
from fastapi import HTTPException

from app.api.v1.memory import (
    get_context,
    update_preferences,
    list_topics,
    create_topic,
    update_topic,
    archive_topic,
    get_recent_context,
    search_memory,
)
from app.models.memory import UserProfile, TopicMemory
from app.models.user import User
from app.schemas.memory import UserProfileUpdate, TopicCreate, TopicUpdate

USER_A_UUID = uuid.UUID("aaaaaaaa-0000-0000-0000-000000000001")
USER_B_UUID = uuid.UUID("bbbbbbbb-0000-0000-0000-000000000002")


def _make_user(uuid_val=USER_A_UUID):
    u = MagicMock(spec=User)
    type(u).id = PropertyMock(return_value=uuid_val)
    u.email = "a@test.com"
    u.is_active = True
    return u


def _profile(user_id=USER_A_UUID, domains=None, journals=None):
    p = MagicMock(spec=UserProfile)
    p.id = 1
    type(p).user_id = PropertyMock(return_value=user_id)
    p.research_domains = domains or []
    p.preferred_journals = journals or []
    p.citation_format = "gbt7714"
    p.writing_style = "academic/strict"
    p.preferred_language = "zh"
    p.institution = "Test"
    p.role = "phd_student"
    p.updated_at = None
    return p


def _topic_mock(id=1, user_id=USER_A_UUID, name="test", status="active"):
    t = MagicMock(spec=TopicMemory)
    t.id = id
    type(t).user_id = PropertyMock(return_value=user_id)
    t.topic_name = name
    t.conventions = {}
    t.key_papers = []
    t.pitfalls = []
    t.experiment_templates = {}
    t.status = status
    t.workspace_id = None
    t.created_at = None
    t.updated_at = None
    return t


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


@pytest.fixture
def db():
    async def _refresh(obj):
        if obj.id is None:
            obj.id = 999
        if obj.updated_at is None:
            obj.updated_at = datetime.now(timezone.utc)
        if getattr(obj, "created_at", None) is None and hasattr(obj, "created_at"):
            obj.created_at = datetime.now(timezone.utc)
        if getattr(obj, "preferred_language", None) is None and hasattr(obj, "preferred_language"):
            obj.preferred_language = "zh"

    db = AsyncMock()
    db.execute = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock(side_effect=_refresh)
    return db


@pytest.fixture
def user_a():
    return _make_user(USER_A_UUID)


@pytest.fixture
def user_b():
    return _make_user(USER_B_UUID)


# ── 用户画像 ──────────────────────────────────────


class TestPreferencesAPI:

    @pytest.mark.asyncio
    async def test_update_preferences_new_profile(self, db, user_a):
        """新建画像。"""
        db.execute.return_value = _scalar_one_or_none(None)

        resp = await update_preferences(
            data=UserProfileUpdate(
                research_domains=["深度学习"],
                citation_format="ieee",
            ),
            current_user=user_a,
            db=db,
        )
        assert resp.code == 200
        assert resp.data.research_domains == ["深度学习"]
        assert resp.data.citation_format == "ieee"

    @pytest.mark.asyncio
    async def test_update_preferences_existing(self, db, user_a):
        """更新已有画像。"""
        db.execute.return_value = _scalar_one_or_none(
            _profile(domains=["ML"], journals=["Nature"])
        )

        resp = await update_preferences(
            data=UserProfileUpdate(research_domains=["ML", "DL"]),
            current_user=user_a,
            db=db,
        )
        assert resp.code == 200

    @pytest.mark.asyncio
    async def test_get_context(self, db, user_a):
        """获取用户上下文。"""
        with patch("app.api.v1.memory.memory_engine.get_user_context") as mgc:
            mgc.return_value = {
                "research_domains": ["ML"],
                "preferred_journals": [],
                "citation_format": "gbt7714",
                "writing_style": "academic/strict",
                "preferred_language": "zh",
                "active_topics": ["课题A"],
            }
            resp = await get_context(current_user=user_a, db=db)
            assert resp.code == 200
            assert resp.data["active_topics"] == ["课题A"]


# ── 课题 CRUD ──────────────────────────────────


class TestTopicAPI:

    @pytest.mark.asyncio
    async def test_create_topic(self, db, user_a):
        """创建课题。"""
        with patch("app.api.v1.memory.memory_engine.create_topic") as mock_ct:
            t = _topic_mock(1, USER_A_UUID, "联邦学习", "active")
            t.created_at = MagicMock()
            t.created_at.isoformat.return_value = "2026-01-01T00:00:00Z"
            t.updated_at = MagicMock()
            t.updated_at.isoformat.return_value = "2026-01-01T00:00:00Z"

            async def _create(*args, **kwargs):
                return t
            mock_ct.side_effect = _create

            resp = await create_topic(
                data=TopicCreate(topic_name="联邦学习", conventions={"naming": "exp001"}),
                current_user=user_a,
                db=db,
            )
            assert resp.code == 201
            assert resp.data["topic_name"] == "联邦学习"

    @pytest.mark.asyncio
    async def test_list_topics(self, db, user_a):
        """课题列表。"""
        t1 = _topic_mock(1, USER_A_UUID, "课题A", "active")
        t2 = _topic_mock(2, USER_A_UUID, "课题B", "active")
        t1.created_at = MagicMock()
        t1.created_at.isoformat.return_value = "2026-01-01T00:00:00Z"
        t1.updated_at = MagicMock()
        t1.updated_at.isoformat.return_value = "2026-01-01T00:00:00Z"
        t2.created_at = MagicMock()
        t2.created_at.isoformat.return_value = "2026-02-01T00:00:00Z"
        t2.updated_at = MagicMock()
        t2.updated_at.isoformat.return_value = "2026-02-01T00:00:00Z"

        db.execute.return_value = _scalars_all([t1, t2])

        resp = await list_topics(current_user=user_a, db=db)
        assert resp.code == 200
        assert len(resp.data) == 2
        assert resp.data[0]["topic_name"] == "课题A"

    @pytest.mark.asyncio
    async def test_update_topic(self, db, user_a):
        """更新课题。"""
        t = _topic_mock(1, USER_A_UUID, "课题A", "active")
        t.key_papers = []
        db.execute.return_value = _scalar_one_or_none(t)

        resp = await update_topic(
            topic_id=1,
            data=TopicUpdate(
                key_papers=[{"id": "p1", "title": "Paper1", "note": ""}]
            ),
            current_user=user_a,
            db=db,
        )
        assert resp.code == 200
        assert len(resp.data["key_papers"]) == 1

    @pytest.mark.asyncio
    async def test_archive_topic(self, db, user_a):
        """归档课题。"""
        t = _topic_mock(1, USER_A_UUID, "课题A", "active")
        db.execute.return_value = _scalar_one_or_none(t)

        resp = await archive_topic(topic_id=1, current_user=user_a, db=db)
        assert resp.code == 200
        assert resp.data["status"] == "archived"

    @pytest.mark.asyncio
    async def test_update_archived_topic_rejected(self, db, user_a):
        """归档后不可修改。"""
        t = _topic_mock(1, USER_A_UUID, "课题A", "archived")
        db.execute.return_value = _scalar_one_or_none(t)

        with pytest.raises(HTTPException) as exc_info:
            await update_topic(
                topic_id=1,
                data=TopicUpdate(key_papers=[{"id": "p", "title": "T", "note": ""}]),
                current_user=user_a,
                db=db,
            )
        assert exc_info.value.status_code == 400


# ── 权限隔离 ──────────────────────────────────────


class TestPermissionIsolation:

    @pytest.mark.asyncio
    async def test_user_a_cannot_access_user_b_topic(self, db, user_a):
        """用户 A 访问用户 B 的课题返回 404（因 user_id 过滤）。"""
        db.execute.return_value = _scalar_one_or_none(None)

        with pytest.raises(HTTPException) as exc_info:
            await update_topic(
                topic_id=99999,
                data=TopicUpdate(key_papers=[{"id": "p", "title": "T", "note": ""}]),
                current_user=user_a,
                db=db,
            )
        assert exc_info.value.status_code == 404


# ── 最近上下文 ────────────────────────────────────


class TestRecentAPI:

    @pytest.mark.asyncio
    async def test_get_recent_context(self, db, user_a):
        """最近 N 天上下文。"""
        with patch("app.api.v1.memory.memory_engine.get_recent_context") as mrc:
            mrc.return_value = {
                "daily_summaries": ["2026-01-01: 检索1次"],
                "total_papers_read": 3,
                "total_search_queries": 5,
                "total_words_written": 2000,
                "total_sandbox_runs": 1,
            }
            resp = await get_recent_context(days=7, current_user=user_a, db=db)
            assert resp.code == 200
            assert resp.data["total_papers_read"] == 3


# ── 搜索记忆 ──────────────────────────────────────


class TestSearchMemoryAPI:

    @pytest.mark.asyncio
    async def test_search_memory(self, db, user_a):
        """搜索记忆。"""
        with patch("app.api.v1.memory.memory_engine.search_memory") as ms:
            ms.return_value = [
                {"type": "key_paper", "title": "Federated Averaging",
                 "source": "课题「联邦学习」"}
            ]
            resp = await search_memory(q="Federated", current_user=user_a, db=db)
            assert resp.code == 200
            assert len(resp.data) == 1
