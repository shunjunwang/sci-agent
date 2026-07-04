"""
P0-B: 流式进度反馈 — SSE 端点

GET /api/v1/progress/{task_id}
  订阅任务进度流，返回 text/event-stream。
"""

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.services.progress_manager import ProgressStage, progress_manager

router = APIRouter(prefix="/progress", tags=["v1-流式进度"], dependencies=[Depends(get_current_user)])


class TaskCreatedResponse(BaseModel):
    """创建任务后的响应体。"""

    task_id: str = Field(..., description="任务 ID，前端用此 ID 连接 SSE")
    message: str = Field(default="任务已创建，请连接 SSE 获取进度")


@router.post("/tasks", response_model=TaskCreatedResponse)
async def create_task() -> TaskCreatedResponse:
    """创建异步任务，返回 task_id 供前端连接 SSE。

    前端流程：
    1. POST /api/v1/progress/tasks → 获取 task_id
    2. GET  /api/v1/progress/{task_id} → 连接 SSE 流
    3. POST /api/v1/...（实际任务端点，携带 X-Task-ID header）
    """
    task_id = progress_manager.create_task_id()
    return TaskCreatedResponse(task_id=task_id, message="任务已创建，请连接 SSE 获取进度")


@router.get("/{task_id}")
async def stream_progress(task_id: str, request: Request) -> StreamingResponse:
    """SSE 端点：流式推送任务进度。

    Args:
        task_id: 任务唯一标识。
        request: FastAPI Request 对象。

    Returns:
        StreamingResponse: text/event-stream 流。
    """

    async def event_generator():
        queue = await progress_manager.subscribe(task_id)
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=120)
                except asyncio.TimeoutError:
                    yield "data: {}\n\n".format(
                        json.dumps(
                            {
                                "task_id": task_id,
                                "stage": "timeout",
                                "step": "任务超时",
                                "detail": "长时间未收到进度更新",
                                "progress": 0.0,
                                "timestamp": "",
                            },
                            ensure_ascii=False,
                        )
                    )
                    break

                yield "data: {}\n\n".format(json.dumps(event, ensure_ascii=False))

                if event.get("stage") in (
                    ProgressStage.COMPLETED.value,
                    ProgressStage.FAILED.value,
                    ProgressStage.CANCELLED.value,
                ):
                    break
        finally:
            await progress_manager.unsubscribe(task_id, queue)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
