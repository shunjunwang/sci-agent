"""
M7 - 四级协作空间 Schemas

交付物来源: task-pc2-m7
"""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class WorkspaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    level: Literal["school", "college", "lab", "class", "friends"]
    parent_id: Optional[int] = None
    description: Optional[str] = None


class WorkspaceUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None


class MemberRoleUpdateRequest(BaseModel):
    role: Literal["admin", "leader", "member", "viewer"]


class InvitationCreateRequest(BaseModel):
    invitee_email: Optional[str] = None
    invitee_phone: Optional[str] = None
    role: str = "member"


class InvitationAcceptRequest(BaseModel):
    invitation_code: str
