"""
P0-I: 分享模式 — ShareService 单元测试

至少 8 个测试。
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.share_service import ShareService

USER_ID = 1
DOC_ID = 42


@pytest.fixture
def db():
    db = AsyncMock()
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.execute = AsyncMock()
    return db


@pytest.fixture
def svc():
    return ShareService()


def _make_share_link(token="tok-abc", user_id=USER_ID, doc_id=DOC_ID,
                     expires_hours=24, max_count=5, access_count=0,
                     revoked=False, allow_download=False, allow_print=False,
                     watermark=None, require_sms=False):
    from app.models.share import ShareLink
    link = MagicMock(spec=ShareLink)
    link.id = 1
    link.user_id = user_id
    link.document_id = doc_id
    link.token = token
    link.expires_at = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    link.max_access_count = max_count
    link.access_count = access_count
    link.allow_download = allow_download
    link.allow_print = allow_print
    link.is_revoked = revoked
    link.watermark_text = watermark
    link.require_sms = require_sms
    link.created_at = datetime.now(timezone.utc)
    return link


class TestCreateShareLink:

    @pytest.mark.asyncio
    async def test_create_basic(self, svc, db):
        share = await svc.create_share_link(
            db, user_id=USER_ID, document_id=DOC_ID,
        )
        assert share is not None
        assert len(share.token) == 32  # secrets.token_urlsafe(24) → 32 chars
        db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_with_options(self, svc, db):
        share = await svc.create_share_link(
            db, user_id=USER_ID, document_id=DOC_ID,
            expires_hours=48,
            max_access_count=10,
            allow_download=True,
            watermark_text="Confidential",
        )
        assert len(share.token) == 32


class TestVerifyShareAccess:

    @pytest.mark.asyncio
    async def test_verify_valid(self, svc, db):
        link = _make_share_link()
        m = MagicMock()
        m.scalar_one_or_none.return_value = link
        db.execute.return_value = m

        result = await svc.verify_share_access(db, "tok-abc")
        assert result["valid"] is True
        assert result["document_id"] == DOC_ID

    @pytest.mark.asyncio
    async def test_verify_expired(self, svc, db):
        link = _make_share_link(expires_hours=-1)  # already expired
        m = MagicMock()
        m.scalar_one_or_none.return_value = link
        db.execute.return_value = m

        result = await svc.verify_share_access(db, "expired-token")
        assert result["valid"] is False
        assert "过期" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_revoked(self, svc, db):
        link = _make_share_link(revoked=True)
        m = MagicMock()
        m.scalar_one_or_none.return_value = link
        db.execute.return_value = m

        result = await svc.verify_share_access(db, "revoked-token")
        assert result["valid"] is False
        assert "撤销" in result["error"]

    @pytest.mark.asyncio
    async def test_verify_access_limit_exceeded(self, svc, db):
        link = _make_share_link(max_count=3, access_count=3)
        m = MagicMock()
        m.scalar_one_or_none.return_value = link
        db.execute.return_value = m

        result = await svc.verify_share_access(db, "full-token")
        assert result["valid"] is False

    @pytest.mark.asyncio
    async def test_revoke_share(self, svc, db):
        link = _make_share_link()
        m = MagicMock()
        m.scalar_one_or_none.return_value = link
        db.execute.return_value = m

        ok = await svc.revoke_share(db, "token-x", USER_ID)
        assert ok is True
        assert link.is_revoked is True

    @pytest.mark.asyncio
    async def test_revoke_share_wrong_user(self, svc, db):
        """revoke 用 WHERE token AND user_id 过滤，不匹配时 scalar 返回 None。"""
        m = MagicMock()
        m.scalar_one_or_none.return_value = None
        db.execute.return_value = m

        ok = await svc.revoke_share(db, "token-x", USER_ID)
        assert ok is False

    @pytest.mark.asyncio
    async def test_list_my_shares(self, svc, db):
        s1 = _make_share_link(token="tok1")
        s2 = _make_share_link(token="tok2")

        scalars = MagicMock()
        scalars.all.return_value = [s1, s2]
        result_mock = MagicMock()
        result_mock.scalars.return_value = scalars
        db.execute.return_value = result_mock

        shares = await svc.list_my_shares(db, USER_ID)
        assert len(shares) == 2
        assert shares[0].token == "tok1"
