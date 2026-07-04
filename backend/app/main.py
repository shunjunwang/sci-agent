"""
FastAPI 应用入口。

配置 CORS、异常处理器、路由注册和 lifespan 事件。
"""

import uuid
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import router as api_v1_router
from app.api.health import router as global_health_router
from app.api.v1.health import router as health_router
from app.api.v1.models import router as models_router
from app.api.v1.workspace import router as v1_workspace_router
from app.api.v1.audit import router as v1_audit_router
from app.api.v1.preferences import router as v1_preferences_router
from app.api.v1.scheduled_tasks import router as v1_scheduled_tasks_router
from app.api.v2 import papers as v2_papers, health as v2_health, sources as v2_sources
from app.api.v3.knowledge import router as v3_knowledge_router
from app.api.v5.writing import router as v5_writing_router
from app.api.v6.sandbox import router as v6_sandbox_router
from app.api.v9.algorithm import router as v9_algorithm_router
from app.api.v1.academic_checker import router as v1_academic_checker_router
from app.api.v1.progress import router as v1_progress_router
from app.api.v1.conversation_manager import router as v1_conversation_manager_router
from app.api.v1.memory import router as v1_memory_router
from app.api.v1.plot import router as v1_plot_router
from app.api.v1.scix import router as v1_scix_router
from app.api.v1.share import router as v1_share_router
from app.api.v1.workflow import router as v1_workflow_router
from app.config import load_env_to_os, settings
from app.core.database import dispose_engine
from app.core.exceptions import AppException
from app.core.rate_limit import RateLimitMiddleware
from app.core.scheduler import scheduler_manager
from app.schemas.common import APIResponse

# ── 启动时注入环境变量（供 keying-cli 等外部工具）────────
load_env_to_os()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # noqa: ARG001
    """应用生命周期管理。

    启动时不主动连接数据库（由 SQLAlchemy 连接池懒加载），
    关闭时释放连接池。

    Args:
        app: FastAPI 应用实例。
    """
    # 启动时不做额外初始化，数据库连接由 SQLAlchemy 引擎懒加载
    scheduler_manager.start()
    yield
    # 关闭时释放数据库连接池 + 调度器
    scheduler_manager.shutdown()
    await dispose_engine()


def _register_exception_handlers(app: FastAPI) -> None:
    """注册全局异常处理器，将 AppException 转换为统一响应格式。

    Args:
        app: FastAPI 应用实例。
    """

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request,  # noqa: ARG001
        exc: AppException,
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=APIResponse[None](
                code=exc.error_code,
                message=exc.message,
                data=None,
                detail=exc.detail,
                request_id=str(uuid.uuid4()),
            ).model_dump(),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request,  # noqa: ARG001
        exc: Exception,  # noqa: ARG001
    ) -> JSONResponse:
        """兜底处理器：捕获所有未处理的异常。"""
        return JSONResponse(
            status_code=500,
            content=APIResponse[None](
                code=5000,
                message="服务器内部错误",
                data=None,
                request_id=str(uuid.uuid4()),
            ).model_dump(),
        )


def create_app() -> FastAPI:
    """创建并配置 FastAPI 应用实例。

    Returns:
        FastAPI: 已配置的应用实例。
    """
    app = FastAPI(
        title="SciAgent API",
        version="1.0",
        description="科研全流程 AI 助手 — 文献检索 / 知识库 / AI写作 / 沙箱执行",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ── CORS ─────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 限流中间件 (PC2 M2) ─────────────────────
    app.add_middleware(RateLimitMiddleware)

    # ── 异常处理器 ───────────────────────────────
    _register_exception_handlers(app)

    # ── 路由注册 ─────────────────────────────────
    app.include_router(global_health_router, tags=["全局健康检查"])

    app.include_router(api_v1_router, prefix="/api/v1")

    # ── P0-14 科研偏好 ──────────────────────────
    app.include_router(v1_preferences_router, prefix="/api/v1", tags=["v1-科研偏好"])

    # ── P0-12 定时任务 ──────────────────────────
    app.include_router(v1_scheduled_tasks_router, prefix="/api/v1", tags=["v1-定时任务"])

    # ── M7 协作空间 ────────────────────────────
    app.include_router(v1_workspace_router, prefix="/api/v1", tags=["v1-协作空间"])

    # ── M8 审计日志 ────────────────────────────
    app.include_router(v1_audit_router, prefix="/api/v1", tags=["v1-审计"])

    # ── PC2 M2 v2 路由 ───────────────────────────
    app.include_router(v2_health.router, prefix="/api/v2", tags=["v2-健康检查"])
    app.include_router(v2_sources.router, prefix="/api/v2", tags=["v2-数据源"])
    app.include_router(v2_papers.router, prefix="/api/v2/papers", tags=["v2-文献检索"])

    # ── PC2 M3 v3 路由 ───────────────────────────
    app.include_router(v3_knowledge_router, prefix="/api/v3", tags=["v3-知识库"])

    # ── M5 AI写作辅助 v5 路由 ──────────────────
    app.include_router(v5_writing_router, prefix="/api/v5/writing", tags=["v5-写作辅助"])

    # ── M6 Docker仿真沙箱 v6 路由 ──────────────
    app.include_router(v6_sandbox_router, prefix="/api/v6", tags=["v6-沙箱"])

    # ── M9 算法商城 v9 路由 ────────────────────
    app.include_router(v9_algorithm_router, prefix="/api/v9", tags=["v9-算法商城"])

    # ── P0-K 学术规范自查 ─────────────────────
    app.include_router(v1_academic_checker_router, prefix="/api/v1", tags=["v1-学术规范自查"])

    # ── P0-B 流式进度 ────────────────────────
    app.include_router(v1_progress_router, prefix="/api/v1", tags=["v1-流式进度"])

    # ── P0-E 对话管理 ────────────────────────
    app.include_router(v1_conversation_manager_router, prefix="/api/v1", tags=["v1-对话管理"])

    # ── P0-G 三层记忆 ──────────────────────────
    app.include_router(v1_memory_router, prefix="/api/v1", tags=["v1-记忆系统"])

    # ── P0-H 科研绘图 ──────────────────────────
    app.include_router(v1_plot_router, prefix="/api/v1", tags=["v1-科研绘图"])

    # ── P0-I SciX 加密 + 分享 ─────────────────
    app.include_router(v1_scix_router, prefix="/api/v1", tags=["v1-SciX加密"])
    app.include_router(v1_share_router, prefix="/api/v1", tags=["v1-分享模式"])

    # ── P0-J 预编排工作流 ────────────────────
    app.include_router(v1_workflow_router, prefix="/api/v1", tags=["v1-预编排工作流"])

    # ── P0-G 定时归档任务 ──────────────────────
    from app.services.memory_engine import memory_engine
    scheduler_manager.add_job(
        func=memory_engine.decay_old_contexts,
        cron_expr="0 3 * * *",
        description="每日凌晨 3:00 归档过期会话上下文（>90天）",
    )

    return app


app = create_app()
