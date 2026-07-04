"""
M9 - 算法商城 Schemas

交付物来源: task-pc3-m9
定义算法模板的上传、搜索、执行和评价相关的 Pydantic 模型。
"""
from typing import Any, Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ── 算法 CRUD ────────────────────────────────────

class AlgorithmCreate(BaseModel):
    """注册新算法"""
    name: str = Field(..., min_length=1, max_length=255, description="算法名称")
    description: Optional[str] = Field(default=None, description="算法描述")
    category: str = Field(..., min_length=1, max_length=100, description="算法分类，如 GNN / CV / NLP")
    docker_image: str = Field(..., min_length=1, max_length=255, description="Docker 镜像名")
    input_schema: Optional[dict] = Field(default_factory=dict, description="输入参数 JSON Schema")
    output_schema: Optional[dict] = Field(default_factory=dict, description="输出结果 JSON Schema")
    default_params: Optional[dict] = Field(default_factory=dict, description="默认运行参数")
    is_public: bool = Field(default=True, description="是否对全平台公开")


class AlgorithmUpdate(BaseModel):
    """更新算法信息（仅作者）"""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, min_length=1, max_length=100)
    docker_image: Optional[str] = Field(default=None, min_length=1, max_length=255)
    input_schema: Optional[dict] = None
    output_schema: Optional[dict] = None
    default_params: Optional[dict] = None
    is_public: Optional[bool] = None


class AlgorithmResponse(BaseModel):
    """算法详情响应"""
    id: UUID
    name: str
    description: Optional[str]
    category: str
    author_id: UUID
    docker_image: str
    input_schema: Optional[dict]
    output_schema: Optional[dict]
    default_params: Optional[dict]
    is_public: bool
    usage_count: int
    rating_avg: float
    rating_count: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlgorithmListItem(BaseModel):
    """算法列表项（精简）"""
    id: UUID
    name: str
    category: str
    author_id: UUID
    is_public: bool
    usage_count: int
    rating_avg: float
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlgorithmSearchRequest(BaseModel):
    """算法搜索请求"""
    keyword: Optional[str] = Field(default=None, description="关键词搜索")
    category: Optional[str] = Field(default=None, description="按分类筛选")
    sort_by: Optional[str] = Field(
        default="newest",
        description="排序方式: rating / usage / newest",
    )
    skip: int = Field(default=0, ge=0, description="跳过条数")
    limit: int = Field(default=20, ge=1, le=100, description="返回上限")


# ── 算法执行 ──────────────────────────────────────

class AlgorithmExecuteRequest(BaseModel):
    """执行算法请求"""
    params: Optional[dict] = Field(default_factory=dict, description="运行参数")
    input_data: Optional[dict] = Field(default_factory=dict, description="输入数据")
    timeout: Optional[int] = Field(default=300, ge=1, le=3600, description="超时秒数")


class AlgorithmExecutionResponse(BaseModel):
    """算法执行记录响应"""
    id: UUID
    algorithm_id: UUID
    user_id: UUID
    sandbox_job_id: Optional[str] = None
    params: Optional[dict]
    output_data: Optional[dict]
    status: str
    execution_time: Optional[float] = None
    cost: Optional[float] = None
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AlgorithmExecutionResult(BaseModel):
    """执行结果详情（含 stdout/stderr）"""
    id: UUID
    algorithm_id: UUID
    status: str
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    output_data: Optional[dict]
    execution_time: Optional[float] = None
    cost: Optional[float] = None
    created_at: Optional[datetime] = None


# ── 评价 ──────────────────────────────────────────

class AlgorithmReviewCreate(BaseModel):
    """提交评价"""
    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    comment: Optional[str] = Field(default=None, description="评价内容")

    @field_validator("rating")
    @classmethod
    def rating_in_range(cls, v: int) -> int:
        if v < 1 or v > 5:
            raise ValueError("评分必须在 1-5 之间")
        return v


class AlgorithmReviewResponse(BaseModel):
    """评价响应"""
    id: UUID
    algorithm_id: UUID
    user_id: UUID
    rating: int
    comment: Optional[str]
    created_at: Optional[datetime] = None

    model_config = {"from_attributes": True}
