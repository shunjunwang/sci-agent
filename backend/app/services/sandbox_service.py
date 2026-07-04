"""
M6 - Docker仿真沙箱 业务服务

交付物来源: task-pc3-m6
核心逻辑: 代码提交 → 数据库记录 → Docker 容器创建 → 执行 → 清理 → 结果持久化

P0-2 安全强化:
  - network_mode="none" (网络隔离)
  - mem_limit + cpu 硬限制
  - timeout 超时强制 kill
  - privileged=False
  - read_only=True (只读文件系统)
  - 禁止宿主机 volumes 挂载
  - cap_drop=["ALL"] (移除所有 Linux capabilities)
  - 非 root 用户运行
  - 日志大小限制

P0-C: 沙箱失败降级 — Docker 不可用/超时时返回部分输出 + 建议
"""
import asyncio
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.sandbox_job import SandboxJob
from app.services.degradation import degradation_service


class SandboxService:
    """沙箱执行服务 — P0-2 安全强化版"""

    DOCKER_HOST = "unix:///var/run/docker.sock"
    DOCKER_API_VERSION = "auto"
    DOCKER_DEFAULT_IMAGE = "sci-agent/sandbox:latest"
    DOCKER_NETWORK_MODE = "none"
    SANDBOX_CPU_LIMIT = 2.0
    SANDBOX_MEMORY_LIMIT_MB = 2048
    SANDBOX_MEMORY_SWAP_MB = 2048
    SANDBOX_TIMEOUT_SECONDS = 300
    SANDBOX_WORKSPACE = "/sandbox/workspace"

    # P0-2: 安全强化
    SANDBOX_SECURITY_OPTIONS = ["no-new-privileges:true"]
    SANDBOX_CAP_DROP = ["ALL"]
    SANDBOX_READ_ONLY = True
    SANDBOX_PRIVILEGED = False
    SANDBOX_USER = "1000:1000"
    SANDBOX_LOG_MAX_SIZE = "10m"
    SANDBOX_LOG_MAX_FILE = "3"

    def __init__(self, docker_client=None):
        self._client = docker_client

    @property
    def client(self):
        if self._client is None:
            import docker
            self._client = docker.DockerClient(
                base_url=self.DOCKER_HOST,
                version=self.DOCKER_API_VERSION,
            )
        return self._client

    @staticmethod
    def generate_job_uid(user_id: str) -> str:
        raw = f"{user_id}:{uuid.uuid4()}:{datetime.now(timezone.utc).isoformat()}"
        return f"job_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"

    def build_container_config(self, job_uid: str, language: str, code: str, timeout: int) -> dict:
        """构建安全强化的容器配置。"""
        if language == "python":
            entrypoint = ["python3", "-c", code]
        elif language == "r":
            entrypoint = ["Rscript", "-e", code]
        else:
            raise ValueError(f"不支持的语言: {language}")

        return {
            "image": self.DOCKER_DEFAULT_IMAGE,
            "command": entrypoint,
            "name": f"sandbox-{job_uid}",
            "network_mode": self.DOCKER_NETWORK_MODE,
            "working_dir": self.SANDBOX_WORKSPACE,
            "mem_limit": f"{self.SANDBOX_MEMORY_LIMIT_MB}m",
            "memswap_limit": f"{self.SANDBOX_MEMORY_SWAP_MB}m",
            "nano_cpus": int(self.SANDBOX_CPU_LIMIT * 1e9),
            "privileged": self.SANDBOX_PRIVILEGED,
            "read_only": self.SANDBOX_READ_ONLY,
            "cap_drop": self.SANDBOX_CAP_DROP,
            "user": self.SANDBOX_USER,
            "security_opt": self.SANDBOX_SECURITY_OPTIONS,
            "tmpfs": {self.SANDBOX_WORKSPACE: "rw,noexec,nosuid,size=256m"},
            "log_config": {
                "type": "json-file",
                "config": {
                    "max-size": self.SANDBOX_LOG_MAX_SIZE,
                    "max-file": self.SANDBOX_LOG_MAX_FILE,
                },
            },
            "auto_remove": True,
            "detach": False,
        }

    @staticmethod
    async def create_job(
        db: AsyncSession, user_id: str, language: str, code: str, image: str
    ) -> SandboxJob:
        job = SandboxJob(
            job_uid=SandboxService.generate_job_uid(user_id),
            user_id=user_id,
            language=language,
            code=code,
            image=image,
            status="queued",
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)
        return job

    @staticmethod
    async def get_job(db: AsyncSession, job_uid: str) -> Optional[SandboxJob]:
        stmt = select(SandboxJob).where(SandboxJob.job_uid == job_uid)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_job_status(
        db: AsyncSession, job_uid: str, status: str, **kwargs
    ) -> Optional[SandboxJob]:
        job = await SandboxService.get_job(db, job_uid)
        if not job:
            return None
        job.status = status
        for key, value in kwargs.items():
            setattr(job, key, value)
        if status == "running":
            job.started_at = datetime.now(timezone.utc)
        if status in ("completed", "failed", "timeout", "killed"):
            job.finished_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(job)
        return job

    async def execute(
        self,
        db: AsyncSession,
        user_id: str,
        language: str,
        code: str,
        timeout: int = 300,
    ) -> SandboxJob:
        actual_timeout = min(timeout, self.SANDBOX_TIMEOUT_SECONDS)
        job = await self.create_job(db, user_id, language, code, self.DOCKER_DEFAULT_IMAGE)
        config = self.build_container_config(job.job_uid, language, code, actual_timeout)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(
                None, self._run_container_sync, config, actual_timeout, job.job_uid
            )
        except Exception as exc:
            # P0-C: Docker 完全不可用 → 降级
            degraded = await degradation_service.sandbox_degraded(
                job_uid=job.job_uid,
                partial_output=None,
                error_msg=str(exc),
                language=language,
            )
            await self.update_job_status(
                db, job.job_uid, "degraded",
                error_message=str(exc),
            )
            return await self.get_job(db, job.job_uid)

        # P0-C: 超时 → 降级返回部分输出
        if result["status"] in ("timeout", "failed"):
            degraded = await degradation_service.sandbox_degraded(
                job_uid=job.job_uid,
                partial_output=result.get("stdout"),
                error_msg=result.get("error_message"),
                language=language,
            )
            # 仍然记录原始状态 + 降级警告
            result["degraded_warnings"] = degraded.warnings

        await self.update_job_status(
            db, job.job_uid, result["status"],
            stdout=result.get("stdout"),
            stderr=result.get("stderr"),
            exit_code=result.get("exit_code"),
            error_message=result.get("error_message"),
            container_id=result.get("container_id"),
        )

        return await self.get_job(db, job.job_uid)

    def _force_kill_container(self, container_name: str) -> None:
        try:
            container = self.client.containers.get(container_name)
            container.kill()
        except Exception:
            pass

    def _run_container_sync(self, config: dict, timeout: int, job_uid: str) -> dict:
        try:
            import docker
            from docker.errors import ImageNotFound, ContainerError, APIError
        except ImportError:
            return {
                "status": "failed", "stdout": "", "stderr": "docker 模块未安装",
                "exit_code": -1, "error_message": "docker 模块未安装",
                "container_id": config["name"],
            }

        container_name = config["name"]
        container_logs = ""

        try:
            try:
                self.client.images.get(config["image"])
            except ImageNotFound:
                self.client.images.pull(config["image"])

            container = self.client.containers.run(
                image=config["image"],
                command=config["command"],
                name=container_name,
                network_mode=config["network_mode"],
                working_dir=config["working_dir"],
                mem_limit=config["mem_limit"],
                memswap_limit=config["memswap_limit"],
                nano_cpus=config["nano_cpus"],
                privileged=config.get("privileged", False),
                read_only=config.get("read_only", True),
                cap_drop=config.get("cap_drop", ["ALL"]),
                user=config.get("user", "1000:1000"),
                security_opt=config.get("security_opt", []),
                tmpfs=config.get("tmpfs"),
                log_config=config.get("log_config"),
                auto_remove=config["auto_remove"],
                detach=False,
                timeout=timeout,
            )

            return {
                "status": "completed",
                "stdout": container.decode("utf-8") if container else "",
                "stderr": "", "exit_code": 0, "error_message": None,
                "container_id": container_name,
            }
        except ContainerError as e:
            return self._classify_container_error(e, container_name)
        except APIError as e:
            return self._classify_api_error(e, container_name)
        except Exception as e:
            # Attempt to inspect container state for OOM / exit code
            container_state = self._inspect_container_state(container_name)
            if container_state is not None:
                oom = container_state.get("OOMKilled", False)
                exit_code = container_state.get("ExitCode", -1)
                if oom:
                    return {
                        "status": "timeout", "stdout": "", "stderr": str(e),
                        "exit_code": exit_code, "error_message": "OOM: 内存不足被系统杀死",
                        "container_id": container_name,
                    }
                if exit_code == 137:
                    return {
                        "status": "timeout", "stdout": "", "stderr": str(e),
                        "exit_code": exit_code, "error_message": "执行超时 (SIGKILL)",
                        "container_id": container_name,
                    }
                if exit_code == 143:
                    return {
                        "status": "killed", "stdout": "", "stderr": str(e),
                        "exit_code": exit_code, "error_message": "进程被终止 (SIGTERM)",
                        "container_id": container_name,
                    }
            return {
                "status": "failed", "stdout": "", "stderr": str(e),
                "exit_code": -1, "error_message": str(e),
                "container_id": container_name,
            }

    def _classify_container_error(self, e, container_name: str) -> dict:
        """根据 ContainerError 的退出码精确分类。"""
        exit_code = e.exit_status if hasattr(e, "exit_status") else -1
        container_state = self._inspect_container_state(container_name)
        oom = container_state.get("OOMKilled", False) if container_state else False

        if oom:
            return {
                "status": "timeout", "stdout": "",
                "stderr": str(e.stderr) if e.stderr else "",
                "exit_code": exit_code,
                "error_message": "OOM: 内存不足被系统杀死",
                "container_id": container_name,
            }
        if exit_code == 137:
            return {
                "status": "timeout", "stdout": "",
                "stderr": str(e.stderr) if e.stderr else "",
                "exit_code": exit_code,
                "error_message": "执行超时 (SIGKILL)",
                "container_id": container_name,
            }
        if exit_code == 143:
            return {
                "status": "killed", "stdout": "",
                "stderr": str(e.stderr) if e.stderr else "",
                "exit_code": exit_code,
                "error_message": "进程被终止 (SIGTERM)",
                "container_id": container_name,
            }
        return {
            "status": "failed",
            "stdout": "", "stderr": str(e.stderr) if e.stderr else "",
            "exit_code": exit_code,
            "error_message": str(e), "container_id": container_name,
        }

    def _classify_api_error(self, e, container_name: str) -> dict:
        """根据容器状态精确分类 API 错误（替代脆弱的字符串匹配）。"""
        container_state = self._inspect_container_state(container_name)
        if container_state is not None:
            oom = container_state.get("OOMKilled", False)
            exit_code = container_state.get("ExitCode", -1)
            if oom:
                self._force_kill_container(container_name)
                return {
                    "status": "timeout", "stdout": "", "stderr": str(e),
                    "exit_code": exit_code, "error_message": "OOM: 内存不足被系统杀死",
                    "container_id": container_name,
                }
            if exit_code == 137:
                self._force_kill_container(container_name)
                return {
                    "status": "timeout", "stdout": "", "stderr": str(e),
                    "exit_code": exit_code, "error_message": "执行超时 (SIGKILL)",
                    "container_id": container_name,
                }
            if exit_code == 143:
                return {
                    "status": "killed", "stdout": "", "stderr": str(e),
                    "exit_code": exit_code, "error_message": "进程被终止 (SIGTERM)",
                    "container_id": container_name,
                }

        # Fallback: string matching only if container state unavailable
        err_msg = str(e).lower()
        if "timeout" in err_msg or "timed out" in err_msg:
            self._force_kill_container(container_name)
            return {
                "status": "timeout", "stdout": "", "stderr": str(e),
                "exit_code": -1, "error_message": "执行超时",
                "container_id": container_name,
            }
        return {
            "status": "failed", "stdout": "", "stderr": str(e),
            "exit_code": -1, "error_message": str(e),
            "container_id": container_name,
        }

    def _inspect_container_state(self, container_name: str) -> dict | None:
        """安全地检查容器状态，返回 attrs['State'] 或 None。"""
        try:
            container = self.client.containers.get(container_name)
            return container.attrs.get("State", {})
        except Exception:
            return None


sandbox_service = SandboxService()
