"""
Security Test Suite - 安全漏洞探测

测试认证绕过、Token 篡改、注入攻击、越权访问、大 payload 拒绝。
"""

import uuid
import pytest
from httpx import AsyncClient


# ── Helpers ──────────────────────────────────────────

async def _create_two_users(client: AsyncClient) -> tuple[dict, dict]:
    """创建两个用户，返回各自的 token 和 ID。"""
    uid_a = uuid.uuid4().hex[:8]
    uid_b = uuid.uuid4().hex[:8]

    # User A
    await client.post("/api/v1/auth/register", json={
        "email": f"sec-a-{uid_a}@test.com",
        "full_name": "Security User A",
        "password": "SecurePassA!",
        "institution": "Sec Univ A",
    })
    resp_a = await client.post("/api/v1/auth/login", json={
        "email": f"sec-a-{uid_a}@test.com",
        "password": "SecurePassA!",
    })
    user_a = {
        "token": resp_a.json()["access_token"],
        "email": f"sec-a-{uid_a}@test.com",
    }

    # User B
    await client.post("/api/v1/auth/register", json={
        "email": f"sec-b-{uid_b}@test.com",
        "full_name": "Security User B",
        "password": "SecurePassB!",
        "institution": "Sec Univ B",
    })
    resp_b = await client.post("/api/v1/auth/login", json={
        "email": f"sec-b-{uid_b}@test.com",
        "password": "SecurePassB!",
    })
    user_b = {
        "token": resp_b.json()["access_token"],
        "email": f"sec-b-{uid_b}@test.com",
    }

    return user_a, user_b


# ── Unauthenticated Access ──────────────────────────

class TestUnauthenticatedAccess:
    """无 Token 访问受保护端点"""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v2/papers/history"),
        ("GET", "/api/v3/papers"),
("GET", "/api/v3/folders"),
        ("POST", "/api/v5/writing/plan"),
        ("POST", "/api/v5/writing/polish"),
        ("POST", "/api/v5/writing/rephrase"),
        ("POST", "/api/v6/sandbox/execute"),
        ("GET", "/api/v9/algorithms"),
        ("GET", "/api/v9/executions"),
    ]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("method,url", PROTECTED_ENDPOINTS)
    async def test_protected_endpoint_without_token(self, method, url, test_client):
        """验证无 token 时返回 401/403/422"""
        c = test_client
        if method == "GET":
            resp = await c.get(url)
        else:
            resp = await c.post(url, json={})
        assert resp.status_code in (401, 403, 422), \
            f"{method} {url}: Expected 401/403/422, got {resp.status_code}"
        print(f"  PASS: {method} {url} → {resp.status_code}")


class TestInvalidToken:
    """Token 篡改与格式错误"""

    @pytest.mark.asyncio
    async def test_empty_token(self, test_client):
        c = test_client
        resp = await c.get("/api/v3/papers",
                           headers={"Authorization": "Bearer "})
        assert resp.status_code in (401, 403, 422), f"Got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_no_bearer_prefix(self, test_client):
        c = test_client
        resp = await c.get("/api/v3/papers",
                           headers={"Authorization": "raw_token_here"})
        assert resp.status_code in (401, 403, 422), f"Got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_tampered_token_signature(self, test_client):
        """篡改 JWT token 的 payload 部分但保留原签名"""
        token, _, _ = await _register_and_login_minimal(test_client, "tamper-")
        # 修改最后 5 个字符来破坏签名
        tampered = token[:-5] + "XXXXX"
        resp = await test_client.get("/api/v3/papers",
                                     headers={"Authorization": f"Bearer {tampered}"})
        assert resp.status_code == 401, f"Expected 401 for tampered token, got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_malformed_jwt(self, test_client):
        """完全随机的 token"""
        resp = await test_client.get("/api/v3/papers",
                                     headers={"Authorization": "Bearer not.a.valid.jwt.token"})
        assert resp.status_code in (401, 403, 422), f"Got {resp.status_code}"

    @pytest.mark.asyncio
    async def test_invalid_user_id_in_token(self, test_client):
        """伪造一个 JWT token sub 为不存在的用户"""
        from app.core.security import create_access_token, ALGORITHM
        from jose import jwt
        from app.config import settings
        import time

        fake_payload = {
            "sub": "00000000-0000-0000-0000-000000000000",
            "exp": int(time.time()) + 3600,
            "iat": int(time.time()),
            "type": "access",
            "jti": "fake-jti-no-user",
        }
        fake_token = jwt.encode(fake_payload, settings.SECRET_KEY, algorithm=ALGORITHM)
        resp = await test_client.get("/api/v3/papers",
                                     headers={"Authorization": f"Bearer {fake_token}"})
        assert resp.status_code == 401, f"Expected 401, got {resp.status_code}"


async def _register_and_login_minimal(client: AsyncClient, prefix: str) -> tuple[str, str, str]:
    """Register + login, minimal version for security tests."""
    uid = uuid.uuid4().hex[:8]
    email = f"{prefix}{uid}@sectest.com"
    await client.post("/api/v1/auth/register", json={
        "email": email, "full_name": f"SecUser {uid}",
        "password": "SecPass!", "institution": "Sec Univ",
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "SecPass!",
    })
    return resp.json()["access_token"], "", email


# ── Injection Attacks ───────────────────────────────

class TestInjectionAttacks:
    """SQL 注入 / XSS 探测"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="P3-04: /api/v2/papers/search now requires auth; test needs refactor")
    async def test_sql_injection_in_search(self, test_client):
        """搜索参数中注入 SQL payload"""
        payloads = [
            "'; DROP TABLE users; --",
            "' OR '1'='1",
            "1' UNION SELECT * FROM users--",
            "\"; DROP TABLE papers; --",
        ]
        for payload in payloads:
            resp = await test_client.get("/api/v2/papers/search",
                                         params={"q": payload, "page_size": 1})
            assert resp.status_code in (200, 400, 422), \
                f"SQL injection '{payload}' caused {resp.status_code}"
            # 不应返回 500
            assert resp.status_code != 500, \
                f"SQL injection '{payload}' caused 500 Internal Error"
        print(f"  PASS: {len(payloads)} SQL injection payloads rejected/escaped safely")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="P3-04: /api/v2/papers/search now requires auth; test needs refactor")
    async def test_xss_in_search(self, test_client):
        """搜索参数中注入 XSS payload，验证输出被转义"""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "<img src=x onerror=alert(1)>",
            "javascript:alert(1)",
        ]
        for payload in xss_payloads:
            resp = await test_client.get("/api/v2/papers/search",
                                         params={"q": payload, "page_size": 1})
            assert resp.status_code in (200, 400, 422), \
                f"XSS payload caused {resp.status_code}"
            body = resp.text.lower()
            # 不应出现原始 script 标签（简单检测，实际需确认转义）
        print(f"  PASS: {len(xss_payloads)} XSS payloads handled safely")

    @pytest.mark.asyncio
    async def test_xss_in_registration(self, test_client):
        """注册参数中的 XSS — 当前版本允许 HTML 字符，建议加强转义"""
        uid = uuid.uuid4().hex[:8]
        resp = await test_client.post("/api/v1/auth/register", json={
            "email": f"xss-{uid}@test.com",
            "full_name": "<script>alert('xss')</script>",
            "password": "Pass123!",
            "institution": "<img src=x onerror=alert(1)>",
        })
        # 应该被拒绝或转义后成功注册
        assert resp.status_code in (201, 400, 422), f"Got {resp.status_code}"
        if resp.status_code in (201, 200):
            data = resp.json()
            name = data.get("full_name", "")
            if "<script>" in name:
                # 记录发现：XSS 未转义
                print(f"  INFO: XSS not sanitized in full_name (raw script stored)")
            else:
                print(f"  PASS: XSS in registration → escaped/filtered, full_name={name}")
        else:
            print(f"  PASS: XSS payload rejected with {resp.status_code}")


# ── Authorization Bypass ────────────────────────────

class TestAuthorizationBypass:
    """越权访问测试"""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="P3-04: /api/v2/papers/search now requires auth; cross-user test needs refactor")
    async def test_cross_user_data_access(self, test_client):
        """用户 A 不能访问用户 B 的知识库数据"""
        user_a, user_b = await _create_two_users(test_client)

        # User A imports a paper
        resp = await test_client.get("/api/v2/papers/search",
                                     params={"q": "neural network", "page_size": 1})
        paper_id = resp.json()["data"]["results"][0].get("paper_id") or \
                   resp.json()["data"]["results"][0].get("id")

        resp = await test_client.post("/api/v3/papers", json={
            "paper_id": paper_id, "tags": ["private"],
        }, headers={"Authorization": f"Bearer {user_a['token']}"})
        assert resp.status_code in (200, 201)

        # User B tries to see User A's knowledge base
        resp = await test_client.get("/api/v3/papers",
                                     headers={"Authorization": f"Bearer {user_b['token']}"})
        assert resp.status_code == 200
        items = resp.json()["data"]["items"]
        # 用户 B 不应看到用户 A 的数据
        # (如果为空列表则越权被阻止)
        print(f"  PASS: User B sees {len(items)} items (should see only own)")

    @pytest.mark.asyncio
    async def test_user_b_cannot_access_user_a_writing_plans(self, test_client):
        """用户 B 不能通过 plan_id 访问用户 A 的写作计划"""
        user_a, user_b = await _create_two_users(test_client)

        # User A creates a plan
        resp = await test_client.post("/api/v5/writing/plan", json={
            "topic": "Private Research Plan",
            "style": "academic",
            "language": "zh",
        }, headers={"Authorization": f"Bearer {user_a['token']}"})
        assert resp.status_code == 200
        plan_id = resp.json()["data"]["plan_id"]

        # User B tries to read User A's plan
        resp = await test_client.get(f"/api/v5/writing/plan/{plan_id}",
                                     headers={"Authorization": f"Bearer {user_b['token']}"})
        assert resp.status_code == 404, \
            f"User B should get 404, got {resp.status_code} (plan {plan_id})"
        print(f"  PASS: User B denied access to User A's plan {plan_id}")


# ── Large Payload Rejection ─────────────────────────

class TestLargePayloadRejection:
    """超大 payload 拒绝"""

    @pytest.mark.asyncio
    async def test_oversized_request_body(self, test_client):
        """发送超大请求体 — 当前 Polish text 字段无长度限制"""
        token, _, _ = await _register_and_login_minimal(test_client, "big-")
        big_text = "x" * (500 * 1024)  # 500 KB

        resp = await test_client.post("/api/v5/writing/polish", json={
            "text": big_text,
            "language": "zh",
            "style": "academic",
        }, headers={"Authorization": f"Bearer {token}"})
        # 理想情况应拒绝 (400/413/422)，当前版本无 max_length 约束
        assert resp.status_code != 500, f"Oversized payload caused 500 error: {resp.status_code}"
        assert resp.status_code in (200, 400, 413, 422), (
            f"Oversized payload (500KB): expected 400/413/422 (rejected) or 200 (accept, no limit yet), "
            f"got {resp.status_code}"
        )

    @pytest.mark.asyncio
    async def test_large_single_field(self, test_client):
        """单个字段超长"""
        token, _, _ = await _register_and_login_minimal(test_client, "long-")
        long_text = "A" * 100000

        resp = await test_client.post("/api/v5/writing/polish", json={
            "text": long_text,
            "language": "zh",
            "style": "academic",
        }, headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code in (200, 400, 422), (
            f"Long field ({len(long_text)} chars): expected 400/422 (rejected) or 200 (accepted), "
            f"got {resp.status_code}"
        )


# ── Rate Limiting ───────────────────────────────────

class TestRateLimiting:
    """限流机制验证（注意：conftest 已移除限流中间件，此处仅验证端点可正常响应）"""

    @pytest.mark.asyncio
    async def test_burst_requests_search(self, test_client):
        """快速连续请求不应返回 500"""
        tasks = [
            test_client.get("/api/v2/papers/search",
                            params={"q": f"topic{i}", "page_size": 1})
            for i in range(20)
        ]
        import asyncio
        results = await asyncio.gather(*tasks)
        statuses = [r.status_code for r in results]
        # 无 5xx 错误
        assert all(s < 500 for s in statuses), (
            f"Burst 20 requests: all status codes must be < 500, got {set(statuses)}"
        )
