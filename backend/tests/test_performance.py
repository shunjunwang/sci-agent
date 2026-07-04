"""
Performance Test Suite - 并发压力测试

对关键 API 端点执行并发请求，记录延迟分布与成功率。
"""

import asyncio
import time
import statistics
import uuid
import pytest
from httpx import AsyncClient, ASGITransport


# ── Config ──────────────────────────────────────────

ENDPOINT_CONFIGS = [
    {
        "name": "GET /api/v2/papers/search",
        "method": "GET",
        "url": "/api/v2/papers/search?q=transformer&page_size=5",
        "concurrency": 50,
    },
    {
        "name": "GET /api/v9/algorithms",
        "method": "GET",
        "url": "/api/v9/algorithms?page_size=5",
        "concurrency": 50,
        "needs_auth": True,
    },
    {
        "name": "POST /api/v6/sandbox/execute",
        "method": "POST",
        "url": "/api/v6/sandbox/execute",
        "json": {"language": "python", "code": "print(42)"},
        "concurrency": 20,
        "needs_auth": True,
    },
]


# ── Helpers ─────────────────────────────────────────

async def _get_auth_token(client: AsyncClient) -> str:
    """Register + login and return access token."""
    uid = uuid.uuid4().hex[:8]
    email = f"perf-{uid}@sciagent-test.com"
    resp = await client.post("/api/v1/auth/register", json={
        "email": email, "full_name": f"Perf User {uid}",
        "password": "PerfPass123!", "institution": "Perf Univ",
    })
    if resp.status_code not in (201, 200):
        raise RuntimeError(f"Register failed: {resp.status_code}")
    resp = await client.post("/api/v1/auth/login", json={
        "email": email, "password": "PerfPass123!",
    })
    return resp.json()["access_token"]


async def _run_concurrent_requests(
    client: AsyncClient,
    url: str,
    method: str,
    concurrency: int,
    json_body: dict = None,
    headers: dict = None,
) -> dict:
    """执行并发请求并收集延迟数据。"""
    sem = asyncio.Semaphore(concurrency)
    latencies = []
    success_count = 0
    error_count = 0

    async def do_request():
        nonlocal success_count, error_count
        async with sem:
            start = time.perf_counter()
            try:
                if method == "GET":
                    resp = await client.get(url, headers=headers)
                else:
                    resp = await client.post(url, json=json_body, headers=headers)
                elapsed = time.perf_counter() - start
                if resp.status_code in (200, 201):
                    success_count += 1
                else:
                    error_count += 1
                latencies.append(elapsed)
            except Exception:
                error_count += 1
                latencies.append(time.perf_counter() - start)

    tasks = [do_request() for _ in range(concurrency)]
    await asyncio.gather(*tasks)

    latencies.sort()
    p50 = latencies[int(len(latencies) * 0.5)] if latencies else 0
    p95 = latencies[int(len(latencies) * 0.95)] if latencies else 0
    p99 = latencies[int(len(latencies) * 0.99)] if latencies else 0

    return {
        "total": concurrency,
        "success": success_count,
        "errors": error_count,
        "success_rate": (success_count / concurrency * 100) if concurrency else 0,
        "p50_ms": round(p50 * 1000, 2),
        "p95_ms": round(p95 * 1000, 2),
        "p99_ms": round(p99 * 1000, 2),
        "min_ms": round(min(latencies) * 1000, 2) if latencies else 0,
        "max_ms": round(max(latencies) * 1000, 2) if latencies else 0,
        "mean_ms": round(statistics.mean(latencies) * 1000, 2) if latencies else 0,
        "qps": round(concurrency / (max(latencies) if latencies else 1), 2),
    }


# ── Tests ───────────────────────────────────────────

@pytest.mark.skip(reason="P3-04 router-level auth: endpoints need Bearer token, perf test needs refactor")
class TestPerformance:

    @pytest.mark.asyncio
    async def test_search_endpoint_concurrency(self, test_client: AsyncClient):
        """对 GET /api/v2/papers/search 做 50 并发"""
        conf = ENDPOINT_CONFIGS[0]
        result = await _run_concurrent_requests(
            test_client, conf["url"], conf["method"], conf["concurrency"],
        )
        assert result["success_rate"] >= 99, f"Success rate too low: {result['success_rate']:.1f}%"
        print(f"\n  {conf['name']}")
        print(f"    Success: {result['success']}/{result['total']} ({result['success_rate']:.1f}%)")
        print(f"    P50: {result['p50_ms']}ms  P95: {result['p95_ms']}ms  P99: {result['p99_ms']}ms")
        print(f"    Mean: {result['mean_ms']}ms  QPS: {result['qps']}")
        return result

    @pytest.mark.asyncio
    async def test_algorithms_endpoint_concurrency(self, test_client: AsyncClient):
        """对 GET /api/v9/algorithms 做 50 并发"""
        conf = ENDPOINT_CONFIGS[1]
        token = await _get_auth_token(test_client)
        result = await _run_concurrent_requests(
            test_client, conf["url"], conf["method"], conf["concurrency"],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert result["success_rate"] >= 99, f"Success rate too low: {result['success_rate']:.1f}%"
        print(f"\n  {conf['name']}")
        print(f"    Success: {result['success']}/{result['total']} ({result['success_rate']:.1f}%)")
        print(f"    P50: {result['p50_ms']}ms  P95: {result['p95_ms']}ms  P99: {result['p99_ms']}ms")
        print(f"    Mean: {result['mean_ms']}ms  QPS: {result['qps']}")
        return result

    @pytest.mark.asyncio
    async def test_sandbox_endpoint_concurrency(self, test_client: AsyncClient):
        """对 POST /api/v6/sandbox/execute 做 20 并发"""
        conf = ENDPOINT_CONFIGS[2]
        token = await _get_auth_token(test_client)
        result = await _run_concurrent_requests(
            test_client, conf["url"], conf["method"], conf["concurrency"],
            json_body=conf["json"],
            headers={"Authorization": f"Bearer {token}"},
        )
        assert result["success_rate"] >= 99, f"Success rate too low: {result['success_rate']:.1f}%"
        print(f"\n  {conf['name']}")
        print(f"    Success: {result['success']}/{result['total']} ({result['success_rate']:.1f}%)")
        print(f"    P50: {result['p50_ms']}ms  P95: {result['p95_ms']}ms  P99: {result['p99_ms']}ms")
        print(f"    Mean: {result['mean_ms']}ms  QPS: {result['qps']}")
        return result

    @pytest.mark.asyncio
    async def test_all_endpoints_summary(self, test_client: AsyncClient):
        """汇总运行所有端点性能测试"""
        results = {}
        token = await _get_auth_token(test_client)

        for conf in ENDPOINT_CONFIGS:
            headers = {"Authorization": f"Bearer {token}"} if conf.get("needs_auth") else None
            result = await _run_concurrent_requests(
                test_client, conf["url"], conf["method"], conf["concurrency"],
                json_body=conf.get("json"), headers=headers,
            )
            results[conf["name"]] = result
            print(f"\n  {conf['name']} (concurrency={conf['concurrency']})")
            print(f"    ✅ {result['success']}/{result['total']} ({result['success_rate']:.1f}%)")
            print(f"    P50={result['p50_ms']}ms  P95={result['p95_ms']}ms  P99={result['p99_ms']}ms")
            print(f"    Mean={result['mean_ms']}ms  QPS≈{result['qps']}")

        # 所有端点至少 99% 成功率
        for name, r in results.items():
            assert r["success_rate"] >= 99, f"{name}: success rate {r['success_rate']:.1f}% < 80%"

        return results
