"""
P0-I: .scix 加密格式 — SciXCrypto 单元测试

至少 8 个测试。
"""
import pytest

from app.services.scix_crypto import SciXCrypto

SCI_X = SciXCrypto()


@pytest.fixture(scope="module")
def keypair():
    return SCI_X.generate_keypair()


class TestEncryptDecrypt:

    def test_encrypt_decrypt_roundtrip(self, keypair):
        priv, pub = keypair
        data = {
            "title": "Test Paper",
            "author": "Alice",
            "content": "# Hello\n\nThis is **markdown** content.",
            "assets": {},
        }
        password = "secure-pw-123"
        scix_bytes = SCI_X.encrypt(data, password, priv)
        assert scix_bytes is not None
        assert len(scix_bytes) > 100

        decrypted = SCI_X.decrypt(scix_bytes, password, pub)
        assert decrypted["title"] == "Test Paper"
        assert decrypted["content"] == data["content"]

    def test_encrypt_decrypt_with_assets(self, keypair):
        priv, pub = keypair
        data = {
            "title": "Paper with Figures",
            "author": "Bob",
            "content": "Some content",
            "assets": {
                "fig1.png": b"\x89PNG\r\n\x1a\n" + b"\x00" * 100,
                "table1.csv": b"col1,col2\n1,2\n3,4\n",
            },
        }
        password = "pw12345"
        scix_bytes = SCI_X.encrypt(data, password, priv)
        decrypted = SCI_X.decrypt(scix_bytes, password, pub)
        assert decrypted["title"] == "Paper with Figures"
        assert "fig1.png" in decrypted["assets"]
        assert decrypted["assets"]["fig1.png"] == data["assets"]["fig1.png"]
        assert decrypted["assets"]["table1.csv"] == data["assets"]["table1.csv"]

    def test_wrong_password_rejected(self, keypair):
        priv, pub = keypair
        data = {"title": "X", "author": "X", "content": "x", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "correct", priv)
        with pytest.raises(Exception):
            SCI_X.decrypt(scix_bytes, "wrong", pub)

    def test_tampered_data_signature_fails(self, keypair):
        priv, pub = keypair
        data = {"title": "X", "author": "X", "content": "x", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw", priv)
        tampered = bytearray(scix_bytes)
        # Corrupt a byte in the middle (may hit signature or encrypted payload)
        tampered[50] = (tampered[50] + 1) % 256
        with pytest.raises(Exception):
            SCI_X.decrypt(bytes(tampered), "pw", pub)

    def test_encrypt_empty_content(self, keypair):
        priv, pub = keypair
        data = {"title": "Empty", "author": "A", "content": "", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw", priv)
        decrypted = SCI_X.decrypt(scix_bytes, "pw", pub)
        assert decrypted["content"] == ""
        assert decrypted["assets"] == {}

    def test_generate_keypair_non_empty(self):
        priv, pub = SCI_X.generate_keypair()
        assert "BEGIN" in priv
        assert "BEGIN" in pub
        assert priv != pub

    def test_verify_signature_valid(self, keypair):
        priv, pub = keypair
        data = {"title": "T", "author": "A", "content": "c", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw", priv)
        valid = SCI_X.verify_signature(scix_bytes, pub)
        assert valid is True

    def test_verify_signature_invalid(self, keypair):
        priv, pub = keypair
        data = {"title": "T", "author": "A", "content": "c", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw", priv)
        # Use a different public key
        _, other_pub = SCI_X.generate_keypair()
        valid = SCI_X.verify_signature(scix_bytes, other_pub)
        assert valid is False

    def test_decrypt_unknown_keypair(self):
        """使用生成的而非匹配的密钥对也应当失败。"""
        _, pub = SCI_X.generate_keypair()
        priv0, _ = SCI_X.generate_keypair()
        data = {"title": "T", "author": "A", "content": "c", "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw", priv0)
        with pytest.raises(Exception):
            SCI_X.decrypt(scix_bytes, "pw", pub)


class TestLargeContent:

    def test_large_content_encrypt_decrypt(self, keypair):
        priv, pub = keypair
        large_content = "x" * 500_000  # 500KB of text
        data = {"title": "Large", "author": "A", "content": large_content, "assets": {}}
        scix_bytes = SCI_X.encrypt(data, "pw123", priv)
        decrypted = SCI_X.decrypt(scix_bytes, "pw123", pub)
        assert decrypted["content"] == large_content
        assert len(scix_bytes) > 500_000
