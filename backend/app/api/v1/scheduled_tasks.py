"""
定时任务管理 API — GET / POST / DELETE。
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from app.api.v1.deps import get_current_user
from app.core.exceptions import BadRequestError
from app.core.scheduler import scheduler_manager, _literature_reminder, _knowledge_backup
from app.models.user import User
from app.schemas.common import APIResponse

router = APIRouter()


class ScheduleTaskCreate(BaseModel):
    """创建定时任务请求。"""

    cron_expr: str = Field(
        default="0 9 * * 1",
        description="cron 表达式（分 时 日 月 周），默认每周一 09:00",
    )
    description: str = Field(default="", description="任务描述")
    action: str = Field(
        default="literature_reminder",
        description="预置动作：literature_reminder / knowledge_backup",
    )


_ACTION_MAP = {
    "literature_reminder": _literature_reminder,
    "knowledge_backup": _knowledge_backup,
}


@router.get("/scheduled-tasks", response_model=APIResponse[list])
async def list_scheduled_tasks() -> APIResponse[list]:
    """列出所有定时任务。"""
    jobs = scheduler_manager.list_jobs()
    return APIResponse(code=200, message="success", data=jobs)


@router.post("/scheduled-tasks", response_model=APIResponse[dict])
async def create_scheduled_task(
    data: ScheduleTaskCreate,
    current_user: User = Depends(get_current_user),
) -> APIResponse[dict]:
    """创建定时任务。"""
    func = _ACTION_MAP.get(data.action)
    if func is None:
        valid = list(_ACTION_MAP.keys())
        raise BadRequestError(message=f"无效动作 '{data.action}'，有效值: {valid}")

    try:
        job_id = scheduler_manager.add_job(
            func=func,
            cron_expr=data.cron_expr,
            description=data.description,
        )
        return APIResponse(
            code=0,
            message="success",
            data={"job_id": job_id, "description": data.description},
        )
    except ValueError as e:
        raise BadRequestError(message=str(e))


@router.delete("/scheduled-tasks/{task_id}", response_model=APIResponse[dict])
async def delete_scheduled_task(task_id: str) -> APIResponse[dict]:
    """删除定时任务。"""
    ok = scheduler_manager.remove_job(task_id)
    if ok:
        return APIResponse(code=200, message="success", data={"job_id": task_id, "deleted": True})
    return APIResponse(code=404, message="task not found", data={"job_id": task_id, "deleted": False})
