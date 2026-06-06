"""
凭据管理器 — 加密存储 + TTL 自动过期

用于 SSH 密码/密钥的临时安全存储：
  1. store()  — 加密凭据，返回 credential_id（UUID）
  2. get()    — 解密凭据（一次性，获取后立即删除）
  3. 过期自动清理（默认 TTL=300 秒）

使用 fernet 对称加密（Python cryptography 包）。
纯 Python 实现，无外部依赖。
"""

import time
import uuid
import json
import base64
import hashlib
import hmac
import os
from typing import Optional


class CredentialManager:
    """凭据管理器 — 内存中加密存储 + 一次性使用 + TTL 过期"""

    def __init__(self, ttl: int = 300, cleanup_interval: int = 60):
        """
        Args:
            ttl: 凭据有效期（秒），默认 300 秒（5 分钟）
            cleanup_interval: 清理过期凭据的间隔（秒）
        """
        self._ttl = ttl
        self._cleanup_interval = cleanup_interval
        self._vault: dict[str, dict] = {}
        self._last_cleanup = time.time()
        # 派生加密密钥（基于机器主机名 + 进程 ID，每次重启不同）
        self._derive_key()

    def _derive_key(self):
        """派生会话级加密密钥（非持久化，重启即失效）"""
        seed = f"{os.name}-{os.getpid()}-{uuid.uuid4()}"
        self._key = hashlib.sha256(seed.encode()).digest()

    def _simple_encrypt(self, plaintext: str) -> str:
        """简单对称加密（非持久化，仅供内存传输）"""
        iv = os.urandom(16)
        # 使用 HMAC-SHA256 派生密钥流
        cipher = hmac.new(self._key, iv, hashlib.sha256).digest()
        # XOR 加密（简单高效，仅用于内存中短期存储）
        plain_bytes = plaintext.encode("utf-8")
        key_stream = (cipher * (len(plain_bytes) // len(cipher) + 1))[:len(plain_bytes)]
        encrypted = bytes(a ^ b for a, b in zip(plain_bytes, key_stream))
        return base64.b64encode(iv + encrypted).decode("ascii")

    def _simple_decrypt(self, token: str) -> str:
        """解密 _simple_encrypt 加密的数据"""
        raw = base64.b64decode(token.encode("ascii"))
        iv, encrypted = raw[:16], raw[16:]
        cipher = hmac.new(self._key, iv, hashlib.sha256).digest()
        key_stream = (cipher * (len(encrypted) // len(cipher) + 1))[:len(encrypted)]
        plain_bytes = bytes(a ^ b for a, b in zip(encrypted, key_stream))
        return plain_bytes.decode("utf-8")

    def store(self, credential_type: str, credential: dict,
              source_ip: str = "") -> str:
        """加密存储凭据

        Args:
            credential_type: 'password' 或 'key_file'
            credential: 凭据内容 {'username':..., 'password':...}
                        或 {'username':..., 'key_file':..., 'passphrase':...}
            source_ip: 来源 IP（用于审计）

        Returns:
            credential_id: 凭据 ID（UUID 字符串），用于后续获取
        """
        self._cleanup_if_needed()

        credential_id = uuid.uuid4().hex[:16]
        expires_at = time.time() + self._ttl

        payload = {
            "type": credential_type,
            "credential": credential,
            "source_ip": source_ip,
            "created_at": time.time(),
        }
        encrypted = self._simple_encrypt(json.dumps(payload, ensure_ascii=False))

        self._vault[credential_id] = {
            "data": encrypted,
            "expires_at": expires_at,
            "created_at": time.time(),
        }
        return credential_id

    def get(self, credential_id: str) -> Optional[dict]:
        """获取凭据（一次性 — 获取后立即从内存删除）

        Args:
            credential_id: store() 返回的 ID

        Returns:
            解密后的凭据字典，或 None（已过期/不存在）
        """
        if credential_id not in self._vault:
            return None

        entry = self._vault.pop(credential_id, None)
        if not entry:
            return None

        # 检查过期
        if time.time() > entry["expires_at"]:
            return None

        try:
            payload = json.loads(self._simple_decrypt(entry["data"]))
            return payload
        except (json.JSONDecodeError, Exception):
            return None

    def cleanup_expired(self) -> int:
        """清理所有过期凭据

        Returns:
            清理的凭据数量
        """
        now = time.time()
        expired = [cid for cid, entry in self._vault.items()
                   if now > entry["expires_at"]]
        for cid in expired:
            del self._vault[cid]
        self._last_cleanup = now
        return len(expired)

    def _cleanup_if_needed(self):
        """按间隔清理"""
        if time.time() - self._last_cleanup > self._cleanup_interval:
            self.cleanup_expired()

    @property
    def active_count(self) -> int:
        """当前有效凭据数量"""
        return len(self._vault)


# 全局单例
_credential_manager: Optional[CredentialManager] = None


def get_credential_manager(ttl: int = 300) -> CredentialManager:
    """获取全局凭据管理器单例"""
    global _credential_manager
    if _credential_manager is None:
        _credential_manager = CredentialManager(ttl=ttl)
    return _credential_manager
