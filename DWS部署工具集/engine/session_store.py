"""
DWS 会话持久化存储 — SQLite 后端

自动保存最近会话，重启不丢失。
支持列表/切换/删除，每个会话保留配置、环境、审计日志。

零外部依赖（使用 Python 内置 sqlite3）。
"""

import os
import json
import sqlite3
import threading
from datetime import datetime
from typing import Optional


class SessionStore:
    """SQLite 会话持久化存储

    使用场景:
      store = SessionStore("sessions.db")
      store.save("session-001", {"env": "UAT", "config": {...}})
      data = store.load("session-001")
      sessions = store.list_sessions()
    """

    def __init__(self, db_path: str = ""):
        if not db_path:
            db_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "dws_sessions.db"
            )
        self._db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        """获取数据库连接（确保目录存在）"""
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """初始化数据库表结构"""
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS sessions (
                        session_id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)
                conn.commit()
            finally:
                conn.close()

    def save(self, session_id: str, data: dict) -> bool:
        """保存会话数据（插入或更新）

        Args:
            session_id: 会话 ID
            data: 会话数据（必须 JSON 可序列化）

        Returns:
            True 成功, False 失败
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        try:
            data_json = json.dumps(data, ensure_ascii=False, default=str)
        except (TypeError, ValueError) as e:
            return False

        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute("""
                    INSERT INTO sessions (session_id, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id) DO UPDATE SET
                        data = excluded.data,
                        updated_at = excluded.updated_at
                """, (session_id, data_json, now, now))
                conn.commit()
                return True
            except sqlite3.Error:
                return False
            finally:
                conn.close()

    def load(self, session_id: str) -> Optional[dict]:
        """加载会话数据

        Args:
            session_id: 会话 ID

        Returns:
            会话数据 dict，或 None（不存在）
        """
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT data FROM sessions WHERE session_id = ?",
                    (session_id,)
                ).fetchone()
                if row:
                    return json.loads(row["data"])
                return None
            except (sqlite3.Error, json.JSONDecodeError):
                return None
            finally:
                conn.close()

    def list_sessions(self, limit: int = 10) -> list:
        """列出最近 N 个会话

        Args:
            limit: 返回数量（默认 10）

        Returns:
            [{"session_id": ..., "created_at": ..., "updated_at": ..., "summary": ...}, ...]
        """
        with self._lock:
            conn = self._get_conn()
            try:
                rows = conn.execute("""
                    SELECT session_id, data, created_at, updated_at
                    FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT ?
                """, (limit,)).fetchall()

                result = []
                for row in rows:
                    try:
                        data = json.loads(row["data"])
                    except json.JSONDecodeError:
                        data = {}
                    summary = data.get("summary", {})
                    result.append({
                        "session_id": row["session_id"],
                        "environment": summary.get("environment", "—"),
                        "cluster": summary.get("cluster_name", "—"),
                        "nodes": summary.get("node_count", 0),
                        "created_at": row["created_at"],
                        "updated_at": row["updated_at"],
                    })
                return result
            except sqlite3.Error:
                return []
            finally:
                conn.close()

    def delete(self, session_id: str) -> bool:
        """删除指定会话

        Args:
            session_id: 会话 ID

        Returns:
            True 成功
        """
        with self._lock:
            conn = self._get_conn()
            try:
                conn.execute(
                    "DELETE FROM sessions WHERE session_id = ?",
                    (session_id,)
                )
                conn.commit()
                return True
            except sqlite3.Error:
                return False
            finally:
                conn.close()

    def cleanup_old(self, max_sessions: int = 20) -> int:
        """清理超过 max_sessions 的旧会话

        Args:
            max_sessions: 保留的最大会话数

        Returns:
            清理的会话数
        """
        with self._lock:
            conn = self._get_conn()
            try:
                # 获取需要删除的会话列表
                rows = conn.execute("""
                    SELECT session_id FROM sessions
                    ORDER BY updated_at DESC
                    LIMIT -1 OFFSET ?
                """, (max_sessions,)).fetchall()
                deleted = 0
                for row in rows:
                    conn.execute(
                        "DELETE FROM sessions WHERE session_id = ?",
                        (row["session_id"],)
                    )
                    deleted += 1
                conn.commit()
                return deleted
            except sqlite3.Error:
                return 0
            finally:
                conn.close()

    @property
    def session_count(self) -> int:
        """当前数据库中会话总数"""
        with self._lock:
            conn = self._get_conn()
            try:
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM sessions"
                ).fetchone()
                return row["cnt"] if row else 0
            except sqlite3.Error:
                return 0
            finally:
                conn.close()
