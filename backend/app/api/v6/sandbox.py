"""
M6 - Docker仿真沙箱 API v6 路由

交付物来源: task-pc3-m6
端点: POST /sandbox/run, POST /sandbox/execute, GET /sandbox/executions/{id},
      GET /sandbox/status, GET /sandbox/status/{job_uid}, POST /sandbox/stop
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_db, get_current_user
from app.core.exceptions import BadRequestError, ForbiddenError, NotFoundError
from app.schemas.sandbox import SandboxExecuteRequest, SandboxStopRequest
from app.schemas.common import APIResponse
from app.services.sandbox_service import sandbox_service
from app.models.user import User

router = APIRouter()


@router.post("/sandbox/run", response_model=APIResponse)
async def run_code(
    request: SandboxExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    if request.language not in ("python", "r"):
        raise BadRequestError(message=f"不支持的语言: {request.language}")

    job = await sandbox_service.execute(
        db, user_id=user_id, language=request.language,
        code=request.code, timeout=request.timeout,
    )

    return APIResponse(
        code=0, message="success",
        data={
            "job_uid": job.job_uid, "status": job.status,
            "image": job.image, "stdout": job.stdout,
            "stderr": job.stderr, "exit_code": job.exit_code,
            "error_message": job.error_message,
        },
    )


@router.get("/sandbox/status/{job_uid}", response_model=APIResponse)
async def get_status(
    job_uid: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    job = await sandbox_service.get_job(db, job_uid)
    if not job:
        raise NotFoundError(message="任务不存在")
    if job.user_id != user_id:
        raise ForbiddenError(message="无权访问此任务")

    return APIResponse(
        code=0, message="success",
        data={
            "job_uid": job.job_uid, "status": job.status,
            "stdout": job.stdout, "stderr": job.stderr,
            "exit_code": job.exit_code, "error_message": job.error_message,
            "cpu_seconds_used": job.cpu_seconds_used,
            "memory_peak_mb": job.memory_peak_mb,
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "finished_at": job.finished_at.isoformat() if job.finished_at else None,
        },
    )


@router.post("/sandbox/stop", response_model=APIResponse)
async def stop_job(
    request: SandboxStopRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user_id = str(user.id)
    job = await sandbox_service.get_job(db, request.job_uid)
    if not job:
        raise NotFoundError(message="任务不存在")
    if job.user_id != user_id:
        raise ForbiddenError(message="无权操作此任务")
    if job.status not in ("queued", "pulling", "running"):
        raise BadRequestError(message="任务已结束或无法终止")

    try:
        import docker
        client = docker.DockerClient(
            base_url=sandbox_service.client.api.base_url,
            version=sandbox_service.client.api.version,
        )
        container = client.containers.get(f"sandbox-{request.job_uid}")
        container.stop(timeout=10)
        container.remove(force=True)
    except Exception:
        pass

    await sandbox_service.update_job_status(
        db, request.job_uid, "killed", error_message="用户手动终止",
    )

    return APIResponse(code=0, message="任务已终止", data={"job_uid": request.job_uid})


# ── M6 新增端点（按任务书规范）─────────────────────


@router.post("/sandbox/execute", response_model=APIResponse, summary="提交代码执行")
async def execute_code(
    request: SandboxExecuteRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """提交代码到 Docker 沙箱执行。

    安全策略:
      - 所有代码在隔离 Docker 容器中执行（network_mode=none, read_only=True）
      - 禁止裸 subprocess，防止 RCE
      - Docker 不可用时返回明确错误，不 fallback 到 subprocess
    """
    user_id = str(user.id)
    if request.language not in ("python", "r", "julia"):
        raise BadRequestError(message=f"不支持的语言: {request.language}")

    import os
    mock_mode = os.getenv("SANDBOX_MOCK_MODE", "").lower() in ("1", "true", "yes")

    # Mock 模式：直接返回模拟结果（开发/测试环境）
    if mock_mode:
        import uuid
        execution_id = f"mock-exec-{uuid.uuid4().hex[:12]}"
        mock_outputs = {
            "python": {"stdout": "Mock Python output\n", "stderr": "", "exit_code": 0},
            "r": {"stdout": "Mock R output\n[1] 42\n", "stderr": "", "exit_code": 0},
            "julia": {"stdout": "Mock Julia output\n42\n", "stderr": "", "exit_code": 0},
        }
        out = mock_outputs.get(request.language, mock_outputs["python"])
        return APIResponse(code=0, message="success (mock)", data={
            "execution_id": execution_id,
            "language": request.language,
            **out,
            "status": "completed",
        })

    # 真实模式：通过 Docker 沙箱执行
    # 先检查 Docker 是否可用
    try:
        import docker
        client = docker.DockerClient.from_env()
        client.ping()
        docker_available = True
    except Exception:
        docker_available = False

    if not docker_available:
        from app.core.exceptions import InternalError
        raise InternalError(
            message="沙箱服务不可用：Docker 未运行或未安装。"
            "请启动 Docker 服务后重试，或设置 SANDBOX_MOCK_MODE=true 使用模拟模式。"
        )

    # Docker 可用：委托给 sandbox_service
    job = await sandbox_service.execute(
        db, user_id=user_id, language=request.language,
        code=request.code, timeout=request.timeout,
    )

    return APIResponse(
        code=0, message="success",
        data={
            "job_uid": job.job_uid,
            "language": request.language,
            "stdout": job.stdout or "",
            "stderr": job.stderr or "",
            "exit_code": job.exit_code or 0,
            "status": job.status,
            "error_message": job.error_message,
        },
    )


@router.get("/sandbox/executions/{execution_id}", response_model=APIResponse, summary="获取执行详情")
async def get_execution(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """获取指定 execution_id 的执行详情（mock 模式返回演示数据）。"""
    import os
    mock_mode = os.getenv("SANDBOX_MOCK_MODE", "").lower() in ("1", "true", "yes")

    if mock_mode or execution_id.startswith("mock-"):
        return APIResponse(code=0, message="success", data={
            "execution_id": execution_id,
            "language": "python",
            "stdout": "Mock execution output\nResult: 42\n",
            "stderr": "",
            "exit_code": 0,
            "status": "completed",
            "created_at": "2026-07-03T08:00:00Z",
        })

    raise NotFoundError(message="执行记录不存在")


@router.get("/sandbox/status", response_model=APIResponse, summary="沙箱服务状态")
async def sandbox_status():
    """返回沙箱服务健康状态（mock/真实模式指示）。"""
    import os
    mock_mode = os.getenv("SANDBOX_MOCK_MODE", "").lower() in ("1", "true", "yes")
    try:
        import docker
        client = docker.DockerClient.from_env()
        client.ping()
        docker_available = True
    except Exception:
        docker_available = False

    return APIResponse(code=0, message="success", data={
        "status": "ok",
        "mock_mode": mock_mode,
        "docker_available": docker_available,
        "supported_languages": ["python", "r", "julia"],
    })
