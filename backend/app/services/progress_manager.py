"""
P0-B: 流式进度反馈 — 进度事件管理器

异步事件总线，管理 SSE 进度推送的订阅/发布/取消订阅。
"""

import asyncio
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Set


class ProgressStage(str, Enum):
    STARTED = "started"
    IN_PROGRESS = "in_progress"
    STEP_COMPLETE = "step_complete"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressEvent:
    """进度事件数据类。"""

    def __init__(
        self,
        task_id: str,
        stage: ProgressStage,
        step: str,
        detail: str = "",
        progress: float = 0.0,
    ) -> None:
        self.task_id = task_id
        self.stage = stage.value
        self.step = step
        self.detail = detail
        self.progress = max(0.0, min(1.0, progress))
        self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "stage": self.stage,
            "step": self.step,
            "detail": self.detail,
            "progress": self.progress,
            "timestamp": self.timestamp,
        }


class ProgressManager:
    """管理 SSE 进度推送的异步事件总线。

    单例模式，通过 progress_manager 全局实例访问。
    """

    _instance: "ProgressManager | None" = None

    def __new__(cls) -> "ProgressManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = {}
            cls._instance._lock = asyncio.Lock()
        return cls._instance

    def __init__(self) -> None:
        # __new__ 已初始化，此处仅为类型标注占位
        pass

    @property
    def _subscribers(self) -> Dict[str, Set[asyncio.Queue]]:
        return self.__dict__["_subscribers"]

    @_subscribers.setter
    def _subscribers(self, value: Dict[str, Set[asyncio.Queue]]) -> None:
        self.__dict__["_subscribers"] = value

    @property
    def _lock(self) -> asyncio.Lock:
        return self.__dict__["_lock"]

    @_lock.setter
    def _lock(self, value: asyncio.Lock) -> None:
        self.__dict__["_lock"] = value

    async def subscribe(self, task_id: str) -> asyncio.Queue:
        """订阅某个任务的进度流。

        Args:
            task_id: 任务唯一标识。

        Returns:
            asyncio.Queue: 异步队列，SSE 端点可从中消费事件。
        """
        queue: asyncio.Queue = asyncio.Queue()
        async with self._lock:
            if task_id not in self._subscribers:
                self._subscribers[task_id] = set()
            self._subscribers[task_id].add(queue)
        return queue

    async def publish(self, task_id: str, event: ProgressEvent) -> None:
        """向所有订阅者推送进度事件。

        Args:
            task_id: 任务唯一标识。
            event: 进度事件。
        """
        async with self._lock:
            subscribers = self._subscribers.get(task_id, set()).copy()

        for queue in subscribers:
            try:
                queue.put_nowait(event.to_dict())
            except asyncio.QueueFull:
                pass  # 订阅者消费过慢，丢弃事件避免阻塞发布者

    async def unsubscribe(self, task_id: str, queue: asyncio.Queue) -> None:
        """取消订阅。

        Args:
            task_id: 任务唯一标识。
            queue: 要移除的队列。
        """
        async with self._lock:
            if task_id in self._subscribers:
                self._subscribers[task_id].discard(queue)
                if not self._subscribers[task_id]:
                    del self._subscribers[task_id]

    @staticmethod
    def create_task_id() -> str:
        """生成唯一任务 ID。"""
        return str(uuid.uuid4())

    def subscriber_count(self, task_id: str) -> int:
        """返回某个任务的订阅者数量（用于测试）。"""
        return len(self._subscribers.get(task_id, set()))


# 全局单例
progress_manager = ProgressManager()
