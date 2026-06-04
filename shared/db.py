"""
掌数科技 · 共享数据持久化层
SQLite 数据库，存储项目/评估/部署记录
"""

import os
import sqlite3
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'toolchain.db')


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            customer TEXT DEFAULT '',
            source_type TEXT DEFAULT '',
            target_type TEXT DEFAULT '',
            description TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS assessments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id),
            source_type TEXT NOT NULL,
            target_type TEXT NOT NULL,
            overall_score REAL DEFAULT 0,
            risk_level TEXT DEFAULT '',
            rules_count INTEGER DEFAULT 0,
            critical_issues INTEGER DEFAULT 0,
            metadata TEXT DEFAULT '{}',
            report_path TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS deployments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER REFERENCES projects(id),
            system_type TEXT NOT NULL,
            environment TEXT DEFAULT '',
            status TEXT DEFAULT 'pending',
            nodes_count INTEGER DEFAULT 0,
            notes TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
    """)
    conn.commit()
    conn.close()


# ---- Project CRUD ----
def create_project(name, customer="", source_type="", target_type="", description=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO projects (name, customer, source_type, target_type, description) VALUES (?,?,?,?,?)",
        (name, customer, source_type, target_type, description)
    )
    conn.commit()
    pid = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    conn.close()
    return pid


def list_projects():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM projects ORDER BY updated_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_project(pid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM projects WHERE id=?", (pid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_project(pid, **kwargs):
    conn = get_conn()
    fields = ", ".join([f"{k}=?" for k in kwargs.keys()])
    values = list(kwargs.values()) + [pid]
    conn.execute(f"UPDATE projects SET {fields}, updated_at=datetime('now','localtime') WHERE id=?", values)
    conn.commit()
    conn.close()


# ---- Assessment CRUD ----
def save_assessment(project_id, source_type, target_type, overall_score, risk_level,
                    rules_count, critical_issues, metadata=None, report_path=""):
    conn = get_conn()
    conn.execute(
        """INSERT INTO assessments
           (project_id, source_type, target_type, overall_score, risk_level,
            rules_count, critical_issues, metadata, report_path)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (project_id, source_type, target_type, overall_score, risk_level,
         rules_count, critical_issues, json.dumps(metadata or {}), report_path)
    )
    conn.commit()
    conn.close()


def list_assessments(project_id=None):
    conn = get_conn()
    if project_id:
        rows = conn.execute(
            "SELECT * FROM assessments WHERE project_id=? ORDER BY created_at DESC", (project_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM assessments ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Deployments CRUD ----
def save_deployment(project_id, system_type, environment="", status="pending", nodes_count=0, notes=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO deployments (project_id, system_type, environment, status, nodes_count, notes) VALUES (?,?,?,?,?,?)",
        (project_id, system_type, environment, status, nodes_count, notes)
    )
    conn.commit()
    conn.close()


def list_deployments(project_id=None):
    conn = get_conn()
    if project_id:
        rows = conn.execute(
            "SELECT * FROM deployments WHERE project_id=? ORDER BY created_at DESC", (project_id,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM deployments ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---- Init ----
init_db()
