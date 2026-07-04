"""
P0-I: SciX 加密封装 & 分享模式 — Schema 定义
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# ── SciX 加密 ──────────────────────────────────────────


class EncryptRequest(BaseModel):
    """加密导出为 .scix 请求。"""

    document_id: int = Field(..., description="写作文档 ID")
    password: Optional[str] = Field(None, description="加密密码（不提供则生成随机密码）")
    include_assets: bool = Field(default=True, description="是否包含附件")


class EncryptResponse(BaseModel):
    """加密导出响应。"""

    password: str = Field(..., description="加密密码（为 None 时自动生成的）")
    scix_size: int = Field(..., description=".scix 文件大小（字节）")


class DecryptRequest(BaseModel):
    """解密 .scix 文件请求。"""

    password: str = Field(..., min_length=1, description="加密密码")


class KeypairResponse(BaseModel):
    """密钥对响应。"""

    private_key: str = Field(..., description="Ed25519 私钥 PEM")
    public_key: str = Field(..., description="Ed25519 公钥 PEM")


class DecryptResponse(BaseModel):
    """解密响应。"""

    title: str
    author: str
    content: str
    created_at: Optional[str] = None


# ── 分享模式 ──────────────────────────────────────────


class ShareCreateRequest(BaseModel):
    """创建分享链接请求。"""

    document_id: int = Field(..., description="文档 ID")
    expires_hours: int = Field(default=24, ge=1, le=720, description="有效期（小时）")
    max_access_count: int = Field(default=5, ge=1, le=100, description="最大访问次数")
    allow_download: bool = Field(default=False, description="允许下载")
    allow_print: bool = Field(default=False, description="允许打印")
    watermark_text: Optional[str] = Field(None, description="水印文本")


class ShareLinkResponse(BaseModel):
    """分享链接响应。"""

    token: str
    url: str
    expires_at: datetime
    max_access_count: int
    access_count: int
    allow_download: bool
    allow_print: bool
    is_revoked: bool
    created_at: Optional[datetime] = None
    document_id: Optional[int] = None


class ShareVerifyResponse(BaseModel):
    """分享验证响应。"""

    valid: bool
    document_id: Optional[int] = None
    permissions: Optional[dict] = None
    watermark: Optional[str] = None
    access_count: Optional[int] = None
    max_access_count: Optional[int] = None
    error: Optional[str] = None
