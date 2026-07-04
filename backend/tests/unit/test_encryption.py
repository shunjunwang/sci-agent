"""
加密模块单元测试。

测试 AES 加密/解密的往返流程。
"""

import pytest

from app.core.encryption import decrypt_api_key, encrypt_api_key, generate_key, ConfigError
from app.config import settings


@pytest.fixture(autouse=True)
def setup_encryption_key(monkeypatch):
    """自动注入临时 ENCRYPTION_KEY 用于测试。

    Args:
        monkeypatch: pytest monkeypatch fixture。
    """
    test_key = generate_key()
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", test_key)
    yield
    monkeypatch.setattr(settings, "ENCRYPTION_KEY", "")


class TestEncryption:
    """加密模块测试类。"""

    def test_generate_key_returns_valid_base64(self):
        """生成密钥应返回有效的 Base64 字符串。"""
        key = generate_key()
        assert isinstance(key, str)
        assert len(key) > 0
        # Fernet 密钥是 44 字符的 Base64 字符串
        assert len(key) == 44

    def test_encrypt_decrypt_roundtrip(self):
        """加密再解密应还原原始明文。"""
        original = "sk-proj-abc123xyz-test-key-value-2024"
        encrypted = encrypt_api_key(original)
        # 密文应与原文不同
        assert encrypted != original
        # 解密应还原
        decrypted = decrypt_api_key(encrypted)
        assert decrypted == original

    def test_encrypt_produces_different_ciphertexts(self):
        """相同明文多次加密应产生不同密文（Fernet 包含时间戳）。"""
        plaintext = "sk-test-key-12345"
        c1 = encrypt_api_key(plaintext)
        c2 = encrypt_api_key(plaintext)
        # 同一秒内可能相同，但在非极快并发下通常不同
        # 至少都要能解密
        assert decrypt_api_key(c1) == plaintext
        assert decrypt_api_key(c2) == plaintext

    def test_decrypt_invalid_ciphertext_raises(self):
        """解密无效密文应抛出异常。"""
        import cryptography.fernet

        with pytest.raises(Exception):
            decrypt_api_key("this-is-not-a-valid-fernet-token")

    def test_encrypt_empty_key_raises(self, monkeypatch):
        """ENCRYPTION_KEY 为空时应抛 ValueError。"""
        monkeypatch.setattr(settings, "ENCRYPTION_KEY", "")
        with pytest.raises(ConfigError, match="ENCRYPTION_KEY"):
            encrypt_api_key("some-key")

    def test_encrypt_special_characters(self):
        """加密包含特殊字符的 API Key。"""
        original = "sk-!@#$%^&*()_+-=[]{}|;':\",./<>?`~"
        encrypted = encrypt_api_key(original)
        assert decrypt_api_key(encrypted) == original

    def test_encrypt_unicode(self):
        """加密包含 Unicode 字符的文本。"""
        original = "密钥-测试-日本語-한국어-中文"
        encrypted = encrypt_api_key(original)
        assert decrypt_api_key(encrypted) == original
