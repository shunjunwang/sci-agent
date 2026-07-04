"""
PC2 M2 文献检索 - FastAPI 入口
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v2 import papers, health
from app.core.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    await init_db()
    yield
    # 关闭时清理资源
    pass


app = FastAPI(
    title="SciAgent 文献检索 API",
    description="PC2 M2 任务：科应 API 对接 + 多源文献检索",
    version="0.2.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(health.router, prefix="/api/v2", tags=["健康检查"])
app.include_router(papers.router, prefix="/api/v2/papers", tags=["文献检索"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)