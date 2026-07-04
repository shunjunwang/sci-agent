"""
加密工具模块 — 双后端设计。

Fernet (AES-128-CBC + HMAC-SHA256) 提供认证加密，适用于大多数场景。
若 SPEC 合规要求 AES-256-GCM，设置 ENCRYPTION_BACKEND=aes256gcm。

后端切换通过配置项 ENCRYPTION_BACKEND（"fernet" / "aes256gcm"）控制。
"""

import os
from base64 import b64encode, b64decode

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.config import settings


class ConfigError(Exception):
    """配置错误异常。"""
    pass


def _get_key_bytes() -> bytes:
    """获取并验证加密密钥。

    Returns:
        bytes: 加密密钥的字节表示。

    Raises:
        ConfigError: ENCRYPTION_KEY 未配置。
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ConfigError(
            "ENCRYPTION_KEY 未配置，请设置环境变量或 .env 文件中的 ENCRYPTION_KEY"
        )
    return key.encode("utf-8")


# ── Fernet 后端（默认）───────────────────────────────

def _get_fernet() -> Fernet:
    """获取 Fernet 加密实例。"""
    return Fernet(_get_key_bytes())


def generate_key() -> str:
    """生成新的 Fernet 密钥。

    Returns:
        str: Base64 编码的 32 字节密钥。
    """
    return Fernet.generate_key().decode("utf-8")


def _fernet_encrypt(plaintext: str) -> str:
    """Fernet 加密。"""
    fernet = _get_fernet()
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return b64encode(token).decode("utf-8")


def _fernet_decrypt(ciphertext_b64: str) -> str:
    """Fernet 解密。"""
    fernet = _get_fernet()
    token = b64decode(ciphertext_b64.encode("utf-8"))
    plaintext = fernet.decrypt(token)
    return plaintext.decode("utf-8")


# ── AES-256-GCM 后端 ────────────────────────────────

def _get_aesgcm() -> AESGCM:
    """获取 AES-256-GCM 实例。

    ENCRYPTION_KEY 需为 32 字节（AES-256）的 base64 编码。
    """
    key_bytes = _get_key_bytes()
    # AES-256 需要 32 字节密钥
    if len(key_bytes) < 32:
        raise ConfigError(
            "ENCRYPTION_KEY 长度不足：AES-256-GCM 需要 32 字节密钥 "
            f"(当前 {len(key_bytes)} 字节)"
        )
    return AESGCM(key_bytes[:32])


def _aesgcm_encrypt(plaintext: str) -> str:
    """AES-256-GCM 加密。

    Returns:
        str: Base64 编码的 nonce(12B) + ciphertext。
    """
    aesgcm = _get_aesgcm()
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    combined = nonce + ciphertext
    return b64encode(combined).decode("utf-8")


def _aesgcm_decrypt(ciphertext_b64: str) -> str:
    """AES-256-GCM 解密。"""
    aesgcm = _get_aesgcm()
    combined = b64decode(ciphertext_b64.encode("utf-8"))
    nonce = combined[:12]
    ciphertext = combined[12:]
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    return plaintext.decode("utf-8")


# ── 统一入口 ─────────────────────────────────────────

def encrypt_api_key(plaintext: str) -> str:
    """加密 API Key（根据 ENCRYPTION_BACKEND 选择后端）。

    Args:
        plaintext: 明文的 API Key。

    Returns:
        str: Base64 编码的密文。
    """
    if settings.ENCRYPTION_BACKEND == "aes256gcm":
        return _aesgcm_encrypt(plaintext)
    return _fernet_encrypt(plaintext)


def decrypt_api_key(ciphertext_b64: str) -> str:
    """解密 API Key（根据 ENCRYPTION_BACKEND 选择后端）。

    Args:
        ciphertext_b64: Base64 编码的密文。

    Returns:
        str: 解密后的明文 API Key。

    Raises:
        cryptography.fernet.InvalidToken: Fernet 模式下密文无效或密钥不匹配。
        cryptography.exceptions.InvalidTag: AES-256-GCM 模式下认证失败。
    """
    if settings.ENCRYPTION_BACKEND == "aes256gcm":
        return _aesgcm_decrypt(ciphertext_b64)
    return _fernet_decrypt(ciphertext_b64)
