"""
P0-J: 预编排工作流 — API 端点
# mypy: disable-error-code="no-untyped-def"
"""


from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.models.workflow import WorkflowInstance
from app.schemas.common import APIResponse
from app.services.workflow_engine import (
    WorkflowType,
    StepStatus,
    workflow_engine,
)

router = APIRouter(prefix="/workflow", tags=["预编排工作流"])


# ── 工作流定义 ───────────────────────────────────


@router.get("/list", response_model=APIResponse[list])
async def list_workflows() -> APIResponse[list]:
    """获取 5 个预编排工作流定义。"""
    wfs = workflow_engine.get_all_workflows()
    return APIResponse(
        code=200,
        message="success",
        data=[workflow_engine.workflow_to_dict(wf) for wf in wfs],
    )


@router.get("/{wf_type}", response_model=APIResponse[dict])
async def get_workflow_detail(wf_type: str) -> APIResponse[dict]:
    """获取单个工作流详情（含 DAG 结构）。"""
    try:
        wf = workflow_engine.get_workflow(WorkflowType(wf_type))
    except ValueError:
        raise HTTPException(status_code=404, detail=f"未知工作流: {wf_type}")

    is_valid = workflow_engine.validate_dag(wf)
    data = workflow_engine.workflow_to_dict(wf)
    data["dag_valid"] = is_valid
    return APIResponse(code=200, message="success", data=data)


# ── 启动工作流 ───────────────────────────────────


@router.post("/{wf_type}/start", response_model=APIResponse[dict])
async def start_workflow(
    wf_type: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """启动一个工作流实例。"""
    try:
        wf = workflow_engine.get_workflow(WorkflowType(wf_type))
    except ValueError:
        raise HTTPException(status_code=404, detail=f"未知工作流: {wf_type}")

    # 初始化步骤状态
    steps_json = [
        {
            "step_id": s.step_id,
            "name": s.name,
            "status": StepStatus.PENDING.value,
            "result": None,
            "started_at": None,
            "completed_at": None,
        }
        for s in wf.steps
    ]

    instance = WorkflowInstance(
        user_id=current_user.id,
        workflow_type=wf_type,
        status="running",
        steps_json=steps_json,
        current_step=wf.steps[0].step_id if wf.steps else None,
    )
    db.add(instance)
    await db.flush()
    await db.refresh(instance)

    return APIResponse(
        code=201,
        message="工作流已启动",
        data={
            "id": instance.id,
            "workflow_type": instance.workflow_type,
            "status": instance.status,
            "steps": instance.steps_json,
            "created_at": instance.created_at.isoformat() if instance.created_at else None,
        },
    )


# ── 实例管理 ─────────────────────────────────────


@router.get("/instances", response_model=APIResponse[list])
async def list_instances(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[list]:
    """获取当前用户的工作流实例列表。"""
    result = await db.execute(
        select(WorkflowInstance)
        .where(WorkflowInstance.user_id == current_user.id)
        .order_by(WorkflowInstance.created_at.desc())
    )
    instances = result.scalars().all()
    items = [
        {
            "id": inst.id,
            "workflow_type": inst.workflow_type,
            "status": inst.status,
            "current_step": inst.current_step,
            "steps": inst.steps_json,
            "created_at": inst.created_at.isoformat() if inst.created_at else None,
            "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        }
        for inst in instances
    ]
    return APIResponse(code=200, message="success", data=items)


@router.get("/instances/{instance_id}", response_model=APIResponse[dict])
async def get_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> APIResponse[dict]:
    """获取工作流实例详情。"""
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.user_id == current_user.id,
        )
    )
    inst = result.scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail="实例不存在")

    return APIResponse(
        code=200,
        message="success",
        data={
            "id": inst.id,
            "workflow_type": inst.workflow_type,
            "status": inst.status,
            "current_step": inst.current_step,
            "steps": inst.steps_json,
            "created_at": inst.created_at.isoformat() if inst.created_at else None,
            "updated_at": inst.updated_at.isoformat() if inst.updated_at else None,
        },
    )


@router.post("/instances/{instance_id}/pause", response_model=APIResponse[dict])
async def pause_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.user_id == current_user.id,
        )
    )
    inst = result.scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail="实例不存在")
    inst.status = "paused"
    await db.flush()
    return APIResponse(code=200, message="已暂停", data={"status": "paused"})


@router.post("/instances/{instance_id}/resume", response_model=APIResponse[dict])
async def resume_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.user_id == current_user.id,
        )
    )
    inst = result.scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail="实例不存在")
    inst.status = "running"
    await db.flush()
    return APIResponse(code=200, message="已恢复", data={"status": "running"})


@router.post("/instances/{instance_id}/cancel", response_model=APIResponse[dict])
async def cancel_instance(
    instance_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(WorkflowInstance).where(
            WorkflowInstance.id == instance_id,
            WorkflowInstance.user_id == current_user.id,
        )
    )
    inst = result.scalar_one_or_none()
    if inst is None:
        raise HTTPException(status_code=404, detail="实例不存在")
    inst.status = "cancelled"
    await db.flush()
    return APIResponse(code=200, message="已取消", data={"status": "cancelled"})
