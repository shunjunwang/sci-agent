"""
M6 - Docker仿真沙箱 Schemas

交付物来源: task-pc3-m6
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SandboxExecuteRequest(BaseModel):
    """提交代码执行"""
    language: Literal["python", "r"] = Field(..., description="编程语言")
    code: str = Field(..., min_length=1, max_length=50000, description="代码内容")
    timeout: Optional[int] = Field(default=300, ge=1, le=600, description="超时秒数")
    env_vars: Optional[dict] = Field(default={}, description="环境变量")


class SandboxStopRequest(BaseModel):
    """终止任务请求"""
    job_uid: str = Field(..., description="任务唯一标识")
