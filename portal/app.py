"""
掌数科技 · 数据库工具链统一门户
集成: 迁移评估系统 / Z-DBMate / DWS部署工具 / 投标系统 / HCCDE题库
"""

import os, sys, subprocess, webbrowser
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
from flask import Flask, render_template, send_from_directory, request, jsonify

# Add shared db to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
from shared import db

app = Flask(__name__)
app.jinja_env.auto_reload = True

# Serve shared static files (brand.css, etc.) for all products
SHARED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'shared', 'static')

@app.route('/shared/<path:filename>')
def shared_static(filename):
    return send_from_directory(SHARED_DIR, filename)

SYSTEMS = [
    {
        "id": "assessment",
        "name": "迁移智能评估系统",
        "desc": "异构数据库迁移兼容性评估 · 7条迁移路径 (GP/Oracle/MySQL/TD等) · DOCX报告",
        "url": "http://127.0.0.1:5030",
        "icon": "🔍",
        "category": "迁移评估",
        "port": 5030,
        "version": "v2.0",
        "tag": "核心产品",
    },
    {
        "id": "zdmate",
        "name": "Z-DBMate 部署助手",
        "desc": "GaussDB OLTP 轻量化部署 · TPOPS管理 · 预检/部署/监控一体化",
        "url": "http://127.0.0.1:5012",
        "icon": "⚙️",
        "category": "部署工具(OLTP)",
        "port": 5012,
        "version": "v2.0",
        "tag": "推荐",
    },
    {
        "id": "dws",
        "name": "DWS 智能部署系统",
        "desc": "GaussDB(DWS) MPP 数仓 · FusionInsight管理 · 预检/配置/验证",
        "url": "http://127.0.0.1:5023",
        "icon": "🏗️",
        "category": "部署工具(MPP)",
        "port": 5023,
        "version": "v1.0",
        "tag": "",
    },
    {
        "id": "bid",
        "name": "投标系统",
        "desc": "投标文档管理与生成 · 资质模板 · 方案自动生成",
        "url": "http://127.0.0.1:5000",
        "icon": "📋",
        "category": "业务系统",
        "port": 5000,
        "version": "v1.0",
        "tag": "",
    },
    {
        "id": "hccde",
        "name": "HCCDE-GaussDB题库",
        "desc": "华为高斯认证考试练习 · 122题覆盖6章 · 离线EXE",
        "url": "",
        "icon": "📚",
        "category": "学习认证",
        "port": None,
        "version": "v2.0",
        "tag": "离线",
    },
]

@app.route("/")
def index():
    # Check which systems are running
    import socket
    checked = []
    for s in SYSTEMS:
        item = dict(s)
        if s["port"]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.5)
            result = sock.connect_ex(("127.0.0.1", s["port"]))
            sock.close()
            item["status"] = "running" if result == 0 else "stopped"
        checked.append(item)
    return render_template("portal.html", systems=checked, now=datetime.now())

# ================================================================
# 项目管理
# ================================================================
@app.route("/projects")
def projects():
    project_list = db.list_projects()
    return render_template("projects.html", projects=project_list)

@app.route("/api/projects", methods=["GET", "POST"])
def api_projects():
    if request.method == "POST":
        data = request.get_json() or {}
        pid = db.create_project(
            name=data.get("name", ""),
            customer=data.get("customer", ""),
            source_type=data.get("source_type", ""),
            target_type=data.get("target_type", ""),
        )
        return jsonify({"id": pid, "status": "ok"})
    return jsonify(db.list_projects())

@app.route("/api/projects/<int:pid>")
def api_project_detail(pid):
    project = db.get_project(pid)
    assessments = db.list_assessments(pid)
    deployments = db.list_deployments(pid)
    return jsonify({"project": project, "assessments": assessments, "deployments": deployments})

@app.route("/api/assessments", methods=["POST"])
def api_save_assessment():
    data = request.get_json() or {}
    db.save_assessment(
        project_id=data.get("project_id", 0),
        source_type=data.get("source_type", ""),
        target_type=data.get("target_type", ""),
        overall_score=data.get("overall_score", 0),
        risk_level=data.get("risk_level", ""),
        rules_count=data.get("rules_count", 0),
        critical_issues=data.get("critical_issues", 0),
        metadata=data.get("metadata"),
    )
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("=" * 50)
    print("  掌数科技 · 数据库工具链门户")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:8080")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=8080)
