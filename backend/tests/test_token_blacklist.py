"""
P0-1: JWT Token 黑名单与刷新机制 — 测试套件。

5 个核心测试：
  - test_login_returns_jti: 登录返回 token 含 jti
  - test_protected_route_requires_valid_token: 访问保护接口需有效 token
  - test_revoked_token_access_denied: 撤销后 token 被拒绝
  - test_refresh_rotation: 刷新轮转（旧 refresh 失效）
  - test_logout_invalidates_token: 登出后 token 失效
"""

from uuid import UUID

import pytest
from httpx import AsyncClient

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    is_token_revoked,
    revoke_token,
)


class TestTokenBlacklist:
    """P0-1 Token 黑名单集成测试。"""

    @pytest.mark.asyncio
    async def test_login_returns_tokens_with_jti(self, test_client: AsyncClient):
        """登录返回的 access/refresh token 均包含 jti 字段。"""
        # 注册新用户
        await test_client.post("/api/v1/auth/register", json={
            "email": "jitest@example.com",
            "full_name": "JTI Tester",
            "password": "testpass123",
            "institution": "Test Lab",
        })

        # 登录
        resp = await test_client.post("/api/v1/auth/login", json={
            "email": "jitest@example.com",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # 验证 access token 含 jti
        access_payload = await decode_token(access_token)
        assert access_payload is not None
        assert "jti" in access_payload
        assert access_payload["type"] == "access"
        assert len(access_payload["jti"]) == 32  # UUID hex

        # 验证 refresh token 含 jti
        refresh_payload = await decode_token(refresh_token)
        assert refresh_payload is not None
        assert "jti" in refresh_payload
        assert refresh_payload["type"] == "refresh"
        assert len(refresh_payload["jti"]) == 32

    @pytest.mark.asyncio
    async def test_protected_route_requires_valid_token(self, test_client: AsyncClient):
        """访问 /auth/me 需要有效 token，无效 token 返回 401。"""
        # 无 token 访问
        resp = await test_client.get("/api/v1/auth/me")
        assert resp.status_code == 401

        # 无效 token 访问
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_revoked_token_access_denied(self, test_client: AsyncClient):
        """已撤销的 access token 无法访问受保护接口。"""
        # 注册 + 登录
        await test_client.post("/api/v1/auth/register", json={
            "email": "revoke_test@example.com",
            "full_name": "Revoke Tester",
            "password": "testpass123",
            "institution": "Test Lab",
        })
        login_resp = await test_client.post("/api/v1/auth/login", json={
            "email": "revoke_test@example.com",
            "password": "testpass123",
        })
        access_token = login_resp.json()["access_token"]

        # token 应能正常访问
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200

        # 登出撤销 token
        await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )

        # 撤销后应被拒绝
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_rotation(self, test_client: AsyncClient):
        """刷新 token 后旧 refresh token 应失效（轮转安全）。"""
        # 注册 + 登录
        await test_client.post("/api/v1/auth/register", json={
            "email": "rotation_test@example.com",
            "full_name": "Rotation Tester",
            "password": "testpass123",
            "institution": "Test Lab",
        })
        login_resp = await test_client.post("/api/v1/auth/login", json={
            "email": "rotation_test@example.com",
            "password": "testpass123",
        })
        old_refresh_token = login_resp.json()["refresh_token"]

        # 使用旧 refresh token 刷新
        refresh_resp = await test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert refresh_resp.status_code == 200
        new_data = refresh_resp.json()
        assert new_data["access_token"]
        assert new_data["refresh_token"]
        assert new_data["refresh_token"] != old_refresh_token

        # 旧 refresh token 应失效
        second_refresh = await test_client.post(
            "/api/v1/auth/refresh",
            headers={"Authorization": f"Bearer {old_refresh_token}"},
        )
        assert second_refresh.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_invalidates_token(self, test_client: AsyncClient):
        """登出后 access token 立即失效，/me 返回 401。"""
        # 注册 + 登录
        await test_client.post("/api/v1/auth/register", json={
            "email": "logout_test@example.com",
            "full_name": "Logout Tester",
            "password": "testpass123",
            "institution": "Test Lab",
        })
        login_resp = await test_client.post("/api/v1/auth/login", json={
            "email": "logout_test@example.com",
            "password": "testpass123",
        })
        access_token = login_resp.json()["access_token"]

        # 登出前应能访问
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200

        # 登出
        logout_resp = await test_client.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert logout_resp.status_code == 200
        assert logout_resp.json()["message"] == "登出成功"

        # 登出后应被拒绝
        resp = await test_client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 401
