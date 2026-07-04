"""
定时任务调度器 单元测试 — 测试创建 / 删除 / 列出任务。

使用 pytest 并发安全模式：每个测试创建独立事件循环和调度器。
"""

import asyncio

import pytest

from app.core.scheduler import SchedulerManager


async def _dummy_task():
    pass


@pytest.mark.asyncio
async def test_add_job_returns_job_id():
    mgr = SchedulerManager()
    mgr.start()
    try:
        job_id = mgr.add_job(
            func=_dummy_task,
            cron_expr="0 9 * * 1",
            description="测试任务",
        )
        assert job_id is not None
        assert isinstance(job_id, str)
    finally:
        mgr.shutdown()


@pytest.mark.asyncio
async def test_list_jobs_includes_added_job():
    mgr = SchedulerManager()
    mgr.start()
    try:
        job_id = mgr.add_job(
            func=_dummy_task,
            cron_expr="0 8 * * 2",
            description="文献提醒",
        )
        jobs = mgr.list_jobs()
        assert len(jobs) >= 1
        job_ids = [j["id"] for j in jobs]
        assert job_id in job_ids
    finally:
        mgr.shutdown()


@pytest.mark.asyncio
async def test_remove_job_works():
    mgr = SchedulerManager()
    mgr.start()
    try:
        job_id = mgr.add_job(
            func=_dummy_task,
            cron_expr="0 2 * * *",
            description="备份任务",
        )
        assert mgr.remove_job(job_id) is True
        jobs = mgr.list_jobs()
        job_ids = [j["id"] for j in jobs]
        assert job_id not in job_ids
    finally:
        mgr.shutdown()


@pytest.mark.asyncio
async def test_remove_nonexistent_job_returns_false():
    mgr = SchedulerManager()
    mgr.start()
    try:
        assert mgr.remove_job("nonexistent_job_id") is False
    finally:
        mgr.shutdown()


@pytest.mark.asyncio
async def test_invalid_cron_raises_value_error():
    mgr = SchedulerManager()
    mgr.start()
    try:
        with pytest.raises(ValueError, match="cron"):
            mgr.add_job(func=_dummy_task, cron_expr="invalid")
    finally:
        mgr.shutdown()


@pytest.mark.asyncio
async def test_list_jobs_has_expected_fields():
    mgr = SchedulerManager()
    mgr.start()
    try:
        mgr.add_job(
            func=_dummy_task,
            cron_expr="0 10 * * 5",
            description="周五提醒",
        )
        jobs = mgr.list_jobs()
        assert len(jobs) >= 1
        job = jobs[0]
        for field in ["id", "name", "trigger"]:
            assert field in job, f"job 缺少字段 {field}"
    finally:
        mgr.shutdown()
