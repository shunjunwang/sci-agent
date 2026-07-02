"""
AES 加密工具模块。

使用 Fernet（来自 cryptography 库）对用户 API Key 进行对称加密存储。
"""

from base64 import b64encode, b64decode

from cryptography.fernet import Fernet

from app.config import settings


def _get_fernet() -> Fernet:
    """获取 Fernet 加密实例。

    Returns:
        Fernet: 使用 settings.ENCRYPTION_KEY 初始化的 Fernet 实例。

    Raises:
        ValueError: ENCRYPTION_KEY 未配置。
    """
    key = settings.ENCRYPTION_KEY
    if not key:
        raise ValueError("ENCRYPTION_KEY 未配置，请设置环境变量或 .env 文件中的 ENCRYPTION_KEY")
    return Fernet(key.encode("utf-8"))


def generate_key() -> str:
    """生成新的 Fernet 密钥。

    Returns:
        str: Base64 编码的 32 字节密钥，可直接用于 ENCRYPTION_KEY 配置。
    """
    return Fernet.generate_key().decode("utf-8")


def encrypt_api_key(plaintext: str) -> str:
    """加密 API Key。

    Args:
        plaintext: 明文的 API Key。

    Returns:
        str: Base64 编码的密文。
    """
    fernet = _get_fernet()
    token = fernet.encrypt(plaintext.encode("utf-8"))
    return token.decode("utf-8")


def decrypt_api_key(ciphertext_b64: str) -> str:
    """解密 API Key。

    Args:
        ciphertext_b64: Base64 编码的密文。

    Returns:
        str: 解密后的明文 API Key。

    Raises:
        cryptography.fernet.InvalidToken: 密文无效或密钥不匹配。
    """
    fernet = _get_fernet()
    plaintext = fernet.decrypt(ciphertext_b64.encode("utf-8"))
    return plaintext.decode("utf-8")
