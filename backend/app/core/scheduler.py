"""
# mypy: disable-error-code="no-untyped-def"
定时任务调度器 — 基于 APScheduler。

提供 BackgroundScheduler 单例 + 任务管理封装。
支持 SQLAlchemyJobStore 持久化 job（通过 _build_jobstores() 工厂）。
"""

import logging
import warnings
from datetime import datetime, timezone
from typing import Callable, Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.job import Job

from app.config import settings

logger = logging.getLogger(__name__)


def _build_jobstores() -> dict:
    """构建 APScheduler jobstores 配置。

    默认使用 SQLAlchemyJobStore 持久化 job 到数据库（与主库同库）。
    若 SQLAlchemyJobStore 不可用或 DATABASE_URL 为 SQLite + 异步驱动，
    则降级为内存存储并记录警告。

    Returns:
        dict: jobstores 配置字典。
    """
    db_url = settings.DATABASE_URL

    # 异步驱动 URL 转同步驱动 URL（SQLAlchemyJobStore 需要同步驱动）
    if "+aiosqlite" in db_url:
        db_url_sync = db_url.replace("+aiosqlite", "")
    elif "+asyncpg" in db_url:
        db_url_sync = db_url.replace("+asyncpg", "").replace("postgresql+", "postgresql://")
    else:
        db_url_sync = db_url

    try:
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

        return {
            "default": SQLAlchemyJobStore(url=db_url_sync)
        }
    except ImportError:
        logger.warning(
            "SQLAlchemyJobStore 不可用（需安装 apscheduler[sqlalchemy]），"
            "job 将存储在内存中，服务重启后丢失"
        )
        return {"default": {}}


class SchedulerManager:
    """定时任务调度管理器。

    管理 AsyncIOScheduler 实例，提供任务 CRUD 封装。
    默认使用 SQLAlchemyJobStore 持久化到数据库。
    """

    def __init__(self):
        self._scheduler: Optional[AsyncIOScheduler] = None

    @property
    def scheduler(self) -> AsyncIOScheduler:
        """获取调度器实例（懒加载）。"""
        if self._scheduler is None:
            self._scheduler = AsyncIOScheduler(
                timezone="Asia/Shanghai",
                jobstores=_build_jobstores(),
                job_defaults={
                    "coalesce": True,
                    "max_instances": 1,
                    "misfire_grace_time": 300,
                },
            )
        return self._scheduler

    def start(self) -> None:
        """启动调度器。"""
        self.scheduler.start()

    def shutdown(self) -> None:
        """关闭调度器。"""
        if self._scheduler is not None:
            self._scheduler.shutdown(wait=False)

    def add_job(
        self,
        func: Callable,
        cron_expr: str,
        job_id: Optional[str] = None,
        description: str = "",
        **kwargs,
    ) -> str:
        """添加定时任务。

        Args:
            func: 要执行的异步函数。
            cron_expr: cron 表达式（分 时 日 月 周）。
            job_id: 任务标识（不传则自动生成）。
            description: 任务描述。
            **kwargs: 传递给 func 的关键词参数。

        Returns:
            str: 任务 ID。
        """
        parts = cron_expr.strip().split()
        if len(parts) != 5:
            raise ValueError("cron 表达式必须为 5 段：分 时 日 月 周")

        trigger = CronTrigger(
            minute=parts[0],
            hour=parts[1],
            day=parts[2],
            month=parts[3],
            day_of_week=parts[4],
            timezone="Asia/Shanghai",
        )

        job = self.scheduler.add_job(
            func,
            trigger=trigger,
            id=job_id,
            name=description,
            kwargs=kwargs,
            replace_existing=True,
        )
        return job.id  # type: ignore[no-any-return]

    def remove_job(self, job_id: str) -> bool:
        """删除定时任务。

        Args:
            job_id: 任务 ID。

        Returns:
            bool: 是否成功删除。
        """
        try:
            self.scheduler.remove_job(job_id)
            return True
        except Exception:
            return False

    def list_jobs(self) -> list[dict]:
        """列出所有定时任务。

        Returns:
            list[dict]: 任务信息列表。
        """
        jobs: list[Job] = self.scheduler.get_jobs()
        return [
            {
                "id": job.id,
                "name": job.name or "",
                "next_run_time": (
                    job.next_run_time.isoformat()
                    if job.next_run_time
                    else None
                ),
                "trigger": str(job.trigger),
            }
            for job in jobs
        ]


# ── 预置任务模板函数 ──────────────────────────────

async def _literature_reminder():
    """文献检索提醒（TODO: 未实现）。"""
    warnings.warn("文献检索提醒功能未实现", stacklevel=2)
    logger.warning(
        "[Scheduler] 文献检索提醒触发 @ %s — 功能未实现(TODO)",
        datetime.now(timezone.utc).isoformat(),
    )


async def _knowledge_backup():
    """知识库备份（TODO: 未实现）。"""
    warnings.warn("知识库备份功能未实现", stacklevel=2)
    logger.warning(
        "[Scheduler] 知识库备份触发 @ %s — 功能未实现(TODO)",
        datetime.now(timezone.utc).isoformat(),
    )


# ── 全局单例 ──────────────────────────────────────

scheduler_manager = SchedulerManager()
