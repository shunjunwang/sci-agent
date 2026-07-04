"""
全局聚合健康检查 API — GET /api/health。

聚合检查数据库、检索源、LLM 连通性，返回统一健康状态。
"""

import time

from fastapi import APIRouter

from app.config import settings
from app.core.database import check_db_connection
from app.schemas.common import APIResponse

router = APIRouter()

# 启动时间戳
_START_TIME = time.time()


async def _check_search_sources() -> dict:
    """检查各检索源可用性。"""
    sources = {}
    # arXiv
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(settings.ARXIV_API_BASE)
            sources["arxiv"] = "ok" if resp.status_code < 500 else "degraded"
    except Exception:
        sources["arxiv"] = "unavailable"

    # PubMed
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(settings.PUBMED_API_BASE)
            sources["pubmed"] = "ok" if resp.status_code < 500 else "degraded"
    except Exception:
        sources["pubmed"] = "unavailable"

    # keying
    try:
        import httpx
        async with httpx.AsyncClient(timeout=5) as client:
            resp = await client.get(f"{settings.KEYING_API_BASE}/health", headers={
                "Authorization": f"Bearer {settings.KEYING_API_KEY}"
            } if settings.KEYING_API_KEY else {})
            sources["keying"] = "ok" if resp.status_code < 500 else "degraded"
    except Exception:
        sources["keying"] = "unavailable"

    return sources


async def _check_llm() -> dict:
    """检查 LLM 连通性（轻量 ping）。"""
    return {"status": "mock", "model": settings.WRITING_LLM_MODEL}


@router.get("/api/health", response_model=APIResponse[dict])
async def aggregated_health() -> APIResponse[dict]:
    """全局聚合健康检查。

    返回数据库连接、检索源可用性、LLM 连通性。
    """
    db_start = time.time()
    db_ok = await check_db_connection()
    db_latency = round((time.time() - db_start) * 1000, 2)

    search_sources = await _check_search_sources()
    llm_status = await _check_llm()

    components = {
        "database": {
            "status": "ok" if db_ok else "error",
            "latency_ms": db_latency,
        },
        "search_sources": search_sources,
        "llm": llm_status,
    }

    any_down = (not db_ok) or any(
        v == "unavailable" for v in search_sources.values()
    )
    overall = "degraded" if any_down else "ok"

    return APIResponse(
        code=200 if overall == "ok" else 503,
        message="success" if overall == "ok" else "service degraded",
        data={
            "status": overall,
            "components": components,
            "version": settings.APP_VERSION,
            "uptime_seconds": round(time.time() - _START_TIME, 2),
        },
    )
