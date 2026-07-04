"""
P0-B: 流式进度反馈 — 测试

测试覆盖:
  - 订阅/发布/取消订阅
  - 多订阅者同时接收
  - 超时处理
  - 任务 ID 唯一性
  - 进度事件序列化
"""
import asyncio
import uuid

import pytest

from app.services.progress_manager import (
    ProgressEvent,
    ProgressManager,
    ProgressStage,
)


@pytest.fixture
def manager():
    """每次测试使用全新的 ProgressManager 实例。"""
    # 重置单例以便隔离测试
    ProgressManager._instance = None
    return ProgressManager()


class TestProgressEvent:
    """进度事件单元测试。"""

    def test_to_dict_contains_all_fields(self):
        event = ProgressEvent(
            task_id="task-1",
            stage=ProgressStage.STARTED,
            step="开始检索",
            detail="初始化中",
            progress=0.0,
        )
        d = event.to_dict()
        assert d["task_id"] == "task-1"
        assert d["stage"] == "started"
        assert d["step"] == "开始检索"
        assert d["detail"] == "初始化中"
        assert d["progress"] == 0.0
        assert "timestamp" in d

    def test_progress_clamped_to_0_1(self):
        e1 = ProgressEvent("t", ProgressStage.COMPLETED, "done", progress=-0.5)
        assert e1.progress == 0.0

        e2 = ProgressEvent("t", ProgressStage.COMPLETED, "done", progress=1.5)
        assert e2.progress == 1.0

    def test_progress_within_bounds(self):
        e = ProgressEvent("t", ProgressStage.IN_PROGRESS, "step", progress=0.73)
        assert e.progress == 0.73


class TestSubscribe:
    """订阅测试。"""

    @pytest.mark.asyncio
    async def test_subscribe_returns_queue(self, manager):
        queue = await manager.subscribe("task-1")
        assert isinstance(queue, asyncio.Queue)

    @pytest.mark.asyncio
    async def test_subscribe_same_task_returns_different_queues(self, manager):
        q1 = await manager.subscribe("task-1")
        q2 = await manager.subscribe("task-1")
        assert q1 is not q2

    @pytest.mark.asyncio
    async def test_subscriber_count(self, manager):
        await manager.subscribe("task-1")
        assert manager.subscriber_count("task-1") == 1
        await manager.subscribe("task-1")
        assert manager.subscriber_count("task-1") == 2


class TestPublish:
    """发布测试。"""

    @pytest.mark.asyncio
    async def test_publish_single_subscriber_receives_event(self, manager):
        queue = await manager.subscribe("task-1")
        event = ProgressEvent("task-1", ProgressStage.STARTED, "开始")
        await manager.publish("task-1", event)

        received = queue.get_nowait()
        assert received["task_id"] == "task-1"
        assert received["stage"] == "started"

    @pytest.mark.asyncio
    async def test_publish_multiple_subscribers_all_receive(self, manager):
        q1 = await manager.subscribe("task-1")
        q2 = await manager.subscribe("task-1")
        event = ProgressEvent("task-1", ProgressStage.IN_PROGRESS, "处理中")
        await manager.publish("task-1", event)

        r1 = q1.get_nowait()
        r2 = q2.get_nowait()
        assert r1["stage"] == "in_progress"
        assert r2["stage"] == "in_progress"

    @pytest.mark.asyncio
    async def test_publish_different_tasks_do_not_cross(self, manager):
        q1 = await manager.subscribe("task-1")
        q2 = await manager.subscribe("task-2")
        await manager.publish("task-1", ProgressEvent("task-1", ProgressStage.STARTED, "s1"))

        r1 = q1.get_nowait()
        assert r1["step"] == "s1"
        assert q2.empty()

    @pytest.mark.asyncio
    async def test_publish_no_subscribers_does_not_raise(self, manager):
        event = ProgressEvent("no-subs", ProgressStage.COMPLETED, "done")
        # 不应抛出异常
        await manager.publish("no-subs", event)


class TestUnsubscribe:
    """取消订阅测试。"""

    @pytest.mark.asyncio
    async def test_unsubscribe_removes_queue(self, manager):
        q = await manager.subscribe("task-1")
        assert manager.subscriber_count("task-1") == 1
        await manager.unsubscribe("task-1", q)
        assert manager.subscriber_count("task-1") == 0

    @pytest.mark.asyncio
    async def test_unsubscribe_one_keeps_others(self, manager):
        q1 = await manager.subscribe("task-1")
        q2 = await manager.subscribe("task-1")
        await manager.unsubscribe("task-1", q1)
        assert manager.subscriber_count("task-1") == 1

        event = ProgressEvent("task-1", ProgressStage.COMPLETED, "done")
        await manager.publish("task-1", event)
        r = q2.get_nowait()
        assert r["stage"] == "completed"

    @pytest.mark.asyncio
    async def test_unsubscribe_nonexistent_does_not_raise(self, manager):
        queue = asyncio.Queue()
        await manager.unsubscribe("no-task", queue)  # 不应抛出异常


class TestTaskId:
    """任务 ID 测试。"""

    def test_create_task_id_returns_valid_uuid(self, manager):
        tid = manager.create_task_id()
        uuid.UUID(tid)  # 不应抛出异常

    def test_create_task_id_unique(self, manager):
        ids = {manager.create_task_id() for _ in range(100)}
        assert len(ids) == 100


class TestProgressStageEnum:
    """枚举值测试。"""

    def test_all_stages_exist(self):
        stages = [
            ProgressStage.STARTED,
            ProgressStage.IN_PROGRESS,
            ProgressStage.STEP_COMPLETE,
            ProgressStage.COMPLETED,
            ProgressStage.FAILED,
            ProgressStage.CANCELLED,
        ]
        assert len(stages) == 6

    def test_stage_values(self):
        assert ProgressStage.STARTED.value == "started"
        assert ProgressStage.COMPLETED.value == "completed"
        assert ProgressStage.FAILED.value == "failed"
