"""
P0-I: .scix 加密格式 — API 端点
# mypy: disable-error-code="no-untyped-def"
"""

import secrets
import string

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.deps import get_current_user, get_db
from app.models.user import User
from app.models.writing import WritingDocument
from app.schemas.common import APIResponse
from app.schemas.share import (
    EncryptRequest,
    KeypairResponse,
    DecryptResponse,
)
from app.services.scix_crypto import scix_crypto, SciXCryptoError

router = APIRouter(prefix="/scix", tags=["SciX 加密格式"])


def _generate_password(length: int = 16) -> str:
    """生成随机密码。"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return "".join(secrets.choice(alphabet) for _ in range(length))


async def _get_user_keypair(
    db: AsyncSession, user_id: int
) -> tuple[str, str] | None:
    """获取用户密钥对（简化：从数据库读取；不存在则生成）。"""
    # 简化实现：每次调用 generate_keypair
    # 实际产品中应存储到 users 表
    return scix_crypto.generate_keypair()


# ── 加密导出 ──────────────────────────────────────


@router.post("/encrypt")
async def encrypt_document(
    req: EncryptRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """将文档加密导出为 .scix 文件。"""
    # 1. 查询文档
    result = await db.execute(
        select(WritingDocument).where(
            WritingDocument.id == str(req.document_id),
            WritingDocument.user_id == current_user.id,
        )
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        raise HTTPException(status_code=404, detail="文档不存在")

    # 2. 生成密钥对
    private_pem, public_pem = scix_crypto.generate_keypair()

    # 3. 准备密码
    password = req.password or _generate_password()

    # 4. 加密
    data = {
        "title": doc.title or "",
        "author": current_user.email or "",
        "content": doc.content or "",
        "assets": {},
    }
    try:
        scix_bytes = scix_crypto.encrypt(data, password, private_pem)
    except SciXCryptoError as e:
        raise HTTPException(status_code=500, detail=str(e))

    return Response(
        content=scix_bytes,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": 'attachment; filename="document.scix"',
            "X-SciX-Password": password,
            "X-SciX-Public-Key": public_pem[:64] + "...",
        },
    )


# ── 解密 ──────────────────────────────────────────


@router.post("/decrypt", response_model=APIResponse[DecryptResponse])
async def decrypt_document(
    password: str = Depends(lambda: ""),
    public_key_pem: str = Depends(lambda: ""),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
):
    """解密 .scix 文件。"""
    if not password:
        raise HTTPException(status_code=400, detail="缺少密码参数")

    scix_bytes = await file.read()
    try:
        result = scix_crypto.decrypt(scix_bytes, password, public_key_pem)
    except SciXCryptoError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return APIResponse(
        code=200,
        message="success",
        data=DecryptResponse(
            title=result["title"],
            author=result["author"],
            content=result["content"],
            created_at=result.get("created_at"),
        ),
    )


# ── 密钥对生成 ────────────────────────────────────


@router.post("/keypair", response_model=APIResponse[KeypairResponse])
async def generate_keypair(
    current_user: User = Depends(get_current_user),
):
    """生成用户的 Ed25519 密钥对。"""
    private_pem, public_pem = scix_crypto.generate_keypair()
    return APIResponse(
        code=200,
        message="success",
        data=KeypairResponse(private_key=private_pem, public_key=public_pem),
    )


# ── 签名验证 ──────────────────────────────────────


@router.post("/verify", response_model=APIResponse[dict])
async def verify_scix_signature(
    public_key_pem: str = Depends(lambda: ""),
    file: UploadFile = File(...),
):
    """验证 .scix 文件签名（不解密）。"""
    if not public_key_pem:
        raise HTTPException(status_code=400, detail="缺少公钥参数")

    scix_bytes = await file.read()
    valid = scix_crypto.verify_signature(scix_bytes, public_key_pem)
    return APIResponse(
        code=200,
        message="success",
        data={"valid": valid},
    )
