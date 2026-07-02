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

from app.api.v1.health import router as health_router
from app.api.v1.models import router as models_router
from app.config import settings
from app.core.database import dispose_engine
from app.core.exceptions import AppException
from app.schemas.common import APIResponse


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:  # noqa: ARG001
    """应用生命周期管理。

    启动时不主动连接数据库（由 SQLAlchemy 连接池懒加载），
    关闭时释放连接池。

    Args:
        app: FastAPI 应用实例。
    """
    # 启动时不做额外初始化，数据库连接由 SQLAlchemy 引擎懒加载
    yield
    # 关闭时释放数据库连接池
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
                code=exc.status_code,
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
                code=500,
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
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )

    # ── CORS ─────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── 异常处理器 ───────────────────────────────
    _register_exception_handlers(app)

    # ── 路由注册 ─────────────────────────────────
    app.include_router(health_router, prefix="/api/v1")
    app.include_router(models_router)

    return app


app = create_app()
