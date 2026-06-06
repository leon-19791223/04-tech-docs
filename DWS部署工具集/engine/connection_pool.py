"""
SSH 连接池 — 复用连接减少握手开销

限制最大并发连接数，防止 SSH 风暴。
支持连接健康检查和自动重连。

零外部依赖（基于 paramiko）。
"""

import time
import threading
from typing import Optional


class ConnectionPool:
    """SSH 连接池

    用法:
        pool = ConnectionPool(max_size=10)
        conn = pool.get("host", 22, "root", password="xxx")
        # 使用 conn
        pool.release("host", conn)  # 归还连接
    """

    def __init__(self, max_size: int = 10, idle_timeout: int = 300):
        """
        Args:
            max_size: 最大连接数
            idle_timeout: 空闲超时（秒），超时后自动关闭
        """
        self.max_size = max_size
        self.idle_timeout = idle_timeout
        self._pool: dict[str, list] = {}  # {key: [conn, ...]}
        self._active: dict[str, int] = {}  # {key: active_count}
        self._lock = threading.Lock()
        self._last_cleanup = time.time()

    def _make_key(self, host: str, port: int, username: str) -> str:
        return f"{username}@{host}:{port}"

    def get(self, host: str, port: int, username: str,
            password: str = "", key_file: str = "") -> Optional[object]:
        """从池中获取连接（如无可用则新建）

        Returns:
            paramiko.SSHClient 或 None（连接失败/超出上限）
        """
        key = self._make_key(host, port, username)
        self._cleanup_if_needed()

        with self._lock:
            # 检查活跃数上限
            active = self._active.get(key, 0)
            if active >= self.max_size:
                return None

            # 从池中取空闲连接
            if key in self._pool and self._pool[key]:
                conn = self._pool[key].pop(0)
                if self._is_connected(conn):
                    self._active[key] = active + 1
                    return conn
                # 连接已断开，丢弃
                self._close_conn(conn)

        # 新建连接
        try:
            import paramiko
            conn = paramiko.SSHClient()
            conn.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if key_file:
                conn.connect(host, port=port, username=username,
                             key_filename=key_file, timeout=10)
            else:
                conn.connect(host, port=port, username=username,
                             password=password, timeout=10)
            with self._lock:
                self._active[key] = self._active.get(key, 0) + 1
            return conn
        except Exception:
            return None

    def release(self, host: str, port: int, username: str, conn) -> bool:
        """归还连接到池中

        Returns:
            True 归还成功, False 连接已关闭
        """
        key = self._make_key(host, port, username)
        if not self._is_connected(conn):
            self._close_conn(conn)
            with self._lock:
                self._active[key] = max(0, self._active.get(key, 0) - 1)
            return False

        with self._lock:
            if key not in self._pool:
                self._pool[key] = []
            self._pool[key].append(conn)
            self._active[key] = max(0, self._active.get(key, 0) - 1)
        return True

    def close_all(self):
        """关闭池中所有连接"""
        with self._lock:
            for key in list(self._pool.keys()):
                for conn in self._pool[key]:
                    self._close_conn(conn)
                self._pool[key] = []
            self._active.clear()

    def _is_connected(self, conn) -> bool:
        """检查连接是否有效"""
        try:
            if conn is None:
                return False
            transport = conn.get_transport()
            if transport is None or not transport.is_active():
                return False
            return True
        except Exception:
            return False

    def _close_conn(self, conn):
        """安全关闭连接"""
        try:
            if conn:
                conn.close()
        except Exception:
            pass

    def _cleanup_if_needed(self):
        """清理过期空闲连接"""
        now = time.time()
        if now - self._last_cleanup < 60:
            return
        self._last_cleanup = now
        with self._lock:
            for key in list(self._pool.keys()):
                self._pool[key] = [
                    c for c in self._pool[key] if self._is_connected(c)
                ]

    @property
    def stats(self) -> dict:
        """连接池统计"""
        with self._lock:
            total_pooled = sum(len(v) for v in self._pool.values())
            total_active = sum(self._active.values())
            return {
                "pooled": total_pooled,
                "active": total_active,
                "total": total_pooled + total_active,
                "keys": len(self._pool),
            }


# 全局单例
_pool: Optional[ConnectionPool] = None


def get_pool(max_size: int = 10) -> ConnectionPool:
    global _pool
    if _pool is None:
        _pool = ConnectionPool(max_size=max_size)
    return _pool
