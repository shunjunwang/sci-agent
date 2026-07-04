"""
P0-I: .scix 加密格式 — AES-256-GCM + Ed25519 签名

ZIP 容器结构：
    manifest.json     — 元数据
    content.enc       — 加密正文
    assets/*.enc      — 加密附件
    signature.sig     — Ed25519 签名
"""

import base64
import io
import json
import zipfile
from datetime import datetime, timezone
from typing import Dict, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class SciXCryptoError(Exception):
    """.scix 加密/解密异常。"""

    pass


class SciXCrypto:
    """.scix 格式加密/解密引擎。"""

    PBKDF2_ITERATIONS = 100_000
    KEY_LENGTH = 32  # AES-256
    SALT_LENGTH = 16
    NONCE_LENGTH = 12  # GCM 推荐

    # ── 密钥派生 ───────────────────────────────────

    @staticmethod
    def _derive_key(password: str, salt: bytes) -> bytes:
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=SciXCrypto.KEY_LENGTH,
            salt=salt,
            iterations=SciXCrypto.PBKDF2_ITERATIONS,
        )
        return kdf.derive(password.encode("utf-8"))

    # ── 密钥对生成 ─────────────────────────────────

    @staticmethod
    def generate_keypair() -> Tuple[str, str]:
        """生成 Ed25519 密钥对，返回 (private_pem, public_pem)。"""
        private_key = ed25519.Ed25519PrivateKey.generate()
        public_key = private_key.public_key()

        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        ).decode("utf-8")

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        return private_pem, public_pem

    # ── 加密 ───────────────────────────────────────

    @staticmethod
    def encrypt(
        data: Dict,
        password: str,
        private_key_pem: str,
    ) -> bytes:
        """加密打包为 .scix 文件，返回 ZIP 字节流。

        data = {
            "title": "论文标题",
            "author": "作者",
            "content": "正文 Markdown/HTML",
            "assets": {"fig1.png": b"...", "table1.csv": b"..."}
        }
        """
        # 1. 生成 salt + 派生密钥
        salt = os.urandom(SciXCrypto.SALT_LENGTH)
        key = SciXCrypto._derive_key(password, salt)

        # 2. 构建 manifest
        content_raw = data.get("content", "").encode("utf-8")
        manifest = {
            "title": data.get("title", ""),
            "author": data.get("author", ""),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "content_sha256": hashlib.sha256(content_raw).hexdigest(),
            "asset_names": list(data.get("assets", {}).keys()),
            "pbkdf2_salt": base64.b64encode(salt).decode(),
            "pbkdf2_iterations": SciXCrypto.PBKDF2_ITERATIONS,
        }

        # 3. 加密正文
        nonce = os.urandom(SciXCrypto.NONCE_LENGTH)
        aesgcm = AESGCM(key)
        content_enc = nonce + aesgcm.encrypt(nonce, content_raw, None)

        # 4. 加密附件
        encrypted_assets: Dict[str, bytes] = {}
        for name, asset_bytes in data.get("assets", {}).items():
            asset_nonce = os.urandom(SciXCrypto.NONCE_LENGTH)
            encrypted_assets[name] = (
                asset_nonce + aesgcm.encrypt(asset_nonce, asset_bytes, None)
            )

        # 5. 签名
        manifest_bytes = json.dumps(manifest, sort_keys=True).encode("utf-8")
        manifest_and_content_hash = hashlib.sha256(
            manifest_bytes + content_enc
        ).digest()

        private_key = serialization.load_pem_private_key(
            private_key_pem.encode(), password=None
        )
        signature = private_key.sign(manifest_and_content_hash)  # type: ignore[union-attr,call-arg]

        # 6. 打包 ZIP（manifest 写入签名时所用的紧凑格式）
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", manifest_bytes)
            zf.writestr("content.enc", content_enc)
            for name, enc_data in encrypted_assets.items():
                zf.writestr(f"assets/{name}.enc", enc_data)
            zf.writestr("signature.sig", signature)

        return zip_buffer.getvalue()

    # ── 解密 ───────────────────────────────────────

    @staticmethod
    def decrypt(
        scix_bytes: bytes,
        password: str,
        public_key_pem: str,
    ) -> Dict:
        """解密 .scix 文件，返回原始 data dict。

        步骤：解压 ZIP → PBKDF2 派生密钥 → 解密 → 签名验证。
        """
        # 1. 解压 ZIP
        zip_buffer = io.BytesIO(scix_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            # 检查必要文件
            required = ["manifest.json", "content.enc", "signature.sig"]
            for name in required:
                if name not in zf.namelist():
                    raise SciXCryptoError(f"无效的 .scix 文件：缺少 {name}")

            manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
            content_enc = zf.read("content.enc")
            _ = zf.read("signature.sig")

            # 读取加密附件
            encrypted_assets: Dict[str, bytes] = {}
            for name in zf.namelist():
                if name.startswith("assets/") and name.endswith(".enc"):
                    asset_name = name[len("assets/"):-len(".enc")]
                    encrypted_assets[asset_name] = zf.read(name)

        # 2. 派生密钥
        salt = base64.b64decode(manifest["pbkdf2_salt"])
        key = SciXCrypto._derive_key(password, salt)

        # 3. 解密正文
        nonce = content_enc[:SciXCrypto.NONCE_LENGTH]
        ciphertext = content_enc[SciXCrypto.NONCE_LENGTH:]
        aesgcm = AESGCM(key)
        try:
            content_raw = aesgcm.decrypt(nonce, ciphertext, None)
        except Exception:
            raise SciXCryptoError("密码错误或文件已损坏")

        # 4. 解密附件
        assets: Dict[str, bytes] = {}
        for name, enc_data in encrypted_assets.items():
            asset_nonce = enc_data[:SciXCrypto.NONCE_LENGTH]
            asset_ciphertext = enc_data[SciXCrypto.NONCE_LENGTH:]
            try:
                assets[name] = aesgcm.decrypt(asset_nonce, asset_ciphertext, None)
            except Exception:
                raise SciXCryptoError(f"附件 {name} 解密失败：密码错误或文件已损坏")

        # 5. 验证签名
        if not SciXCrypto.verify_signature(scix_bytes, public_key_pem):
            raise SciXCryptoError("签名验证失败：文件可能被篡改")

        # 6. 验证内容哈希
        actual_sha256 = hashlib.sha256(content_raw).hexdigest()
        if actual_sha256 != manifest["content_sha256"]:
            raise SciXCryptoError("内容完整性校验失败")

        return {
            "title": manifest.get("title", ""),
            "author": manifest.get("author", ""),
            "content": content_raw.decode("utf-8"),
            "assets": assets,
            "created_at": manifest.get("created_at"),
        }

    # ── 签名验证（不解密） ──────────────────────────

    @staticmethod
    def verify_signature(scix_bytes: bytes, public_key_pem: str) -> bool:
        """仅验证 .scix 文件签名，不解密。"""
        zip_buffer = io.BytesIO(scix_bytes)
        with zipfile.ZipFile(zip_buffer, "r") as zf:
            if "manifest.json" not in zf.namelist():
                return False
            if "content.enc" not in zf.namelist():
                return False
            if "signature.sig" not in zf.namelist():
                return False

            manifest_bytes = zf.read("manifest.json")
            content_enc = zf.read("content.enc")
            signature_data = zf.read("signature.sig")

        manifest_and_content_hash = hashlib.sha256(
            manifest_bytes + content_enc
        ).digest()

        public_key = serialization.load_pem_public_key(
            public_key_pem.encode()
        )
        try:
            public_key.verify(signature_data, manifest_and_content_hash)  # type: ignore[union-attr,call-arg]
            return True
        except InvalidSignature:
            return False


# 为了避免在函数体内 import os 和 hashlib 导致 linter 警告
import hashlib  # noqa: E402
import os  # noqa: E402

# 全局单例
scix_crypto = SciXCrypto()
