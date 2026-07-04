"""用户相关 Pydantic 模型"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, validator

from app.models.user import SubscriptionPlan, UserRole


class UserBase(BaseModel):
    """用户基础模型"""
    email: EmailStr = Field(..., description="邮箱地址")
    full_name: str = Field(..., min_length=1, max_length=128, description="用户全名")
    institution: Optional[str] = Field(None, max_length=256, description="所属机构")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")


class UserCreate(UserBase):
    """用户创建模型"""
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class UserUpdate(BaseModel):
    """用户更新模型"""
    full_name: Optional[str] = Field(None, min_length=1, max_length=128, description="用户全名")
    institution: Optional[str] = Field(None, max_length=256, description="所属机构")
    phone: Optional[str] = Field(None, max_length=20, description="手机号")
    preferred_language: Optional[str] = Field(None, pattern="^[a-z]{2}(-[A-Z]{2})?$", description="首选语言代码")
    
    @validator("preferred_language")
    def validate_language(cls, v):
        if v and v not in ["zh-CN", "en-US", "ja-JP", "ko-KR"]:
            raise ValueError("不支持的语言代码")
        return v


class UserLogin(BaseModel):
    """用户登录模型"""
    email: EmailStr = Field(..., description="邮箱地址")
    password: str = Field(..., min_length=8, max_length=128, description="密码")


class UserInDB(UserBase):
    """数据库中的用户模型"""
    id: UUID = Field(..., description="用户ID")
    subscription_plan: SubscriptionPlan = Field(..., description="订阅计划")
    trial_ends_at: Optional[datetime] = Field(None, description="试用期结束时间")
    preferred_language: str = Field(..., description="首选语言代码")
    role: UserRole = Field(..., description="用户角色")
    is_active: bool = Field(..., description="账号是否启用")
    is_verified: bool = Field(..., description="邮箱是否已验证")
    last_login_at: Optional[datetime] = Field(None, description="最后登录时间")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: datetime = Field(..., description="最后更新时间")
    
    class Config:
        from_attributes = True


class UserPublic(UserInDB):
    """公开的用户信息（不含敏感字段）"""
    pass


class Token(BaseModel):
    """Token 响应模型"""
    access_token: str = Field(..., description="访问令牌")
    refresh_token: str = Field(..., description="刷新令牌")
    token_type: str = Field(default="bearer", description="令牌类型")


class TokenPayload(BaseModel):
    """Token 载荷模型"""
    sub: str = Field(..., description="用户ID")
    exp: int = Field(..., description="过期时间戳")
    iat: int = Field(..., description="签发时间戳")
    type: str = Field(..., description="令牌类型")


class PasswordChange(BaseModel):
    """密码修改模型"""
    current_password: str = Field(..., min_length=8, max_length=128, description="当前密码")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")


class EmailVerification(BaseModel):
    """邮箱验证模型"""
    token: str = Field(..., description="验证令牌")


class ResetPasswordRequest(BaseModel):
    """重置密码请求模型"""
    email: EmailStr = Field(..., description="邮箱地址")


class ResetPasswordConfirm(BaseModel):
    """重置密码确认模型"""
    token: str = Field(..., description="重置令牌")
    new_password: str = Field(..., min_length=8, max_length=128, description="新密码")