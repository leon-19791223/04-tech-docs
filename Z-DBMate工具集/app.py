"""
Z-DBMate 部署工具集 - Web UI (Flask)
提供预检可视化、一键部署、进度监控和检查清单
"""

import os
import sys
import json
import subprocess
from datetime import datetime

from flask import Flask, render_template, request, jsonify, send_file

app = Flask(__name__)

# ================================================================
# 数据模型
# ================================================================
PRECHECK_ITEMS = [
    {"id": "network", "name": "节点网络可达性", "category": "network", "description": "ping检测所有节点是否可达"},
    {"id": "ssh", "name": "SSH免密登录", "category": "network", "description": "SSH免密登录各节点"},
    {"id": "os_version", "name": "操作系统版本", "category": "system", "description": "检查是否为Kylin V10"},
    {"id": "disk_count", "name": "磁盘数量", "category": "storage", "description": "生产≥6块，测试≥2块"},
    {"id": "disk_mount", "name": "数据盘挂载", "category": "storage", "description": "/data 分区已挂载"},
    {"id": "disk_space", "name": "磁盘空间", "category": "storage", "description": "生产≥1000GB，测试≥300GB"},
    {"id": "clock_sync", "name": "时钟同步", "category": "system", "description": "chronyd时钟同步状态"},
    {"id": "memory", "name": "内存", "category": "system", "description": "生产≥32GB，测试≥8GB"},
    {"id": "cpu", "name": "CPU核心数", "category": "system", "description": "生产≥16核"},
    {"id": "yum", "name": "yum源可用性", "category": "system", "description": "yum makecache无报错"},
    {"id": "selinux", "name": "SELinux状态", "category": "system", "description": "Disabled或Permissive"},
    {"id": "firewall", "name": "防火墙状态", "category": "system", "description": "关闭或已开放端口"},
]

SCENARIOS = [
    {"id": "main_install_single", "label": "单节点TPOPS+三节点GaussDB", "conf": "single_tpops_gaussdb_user_edit_file.conf"},
    {"id": "main_install_ha", "label": "HA TPOPS+三节点GaussDB", "conf": "ha_tpops_gaussdb_user_edit_file.conf"},
    {"id": "tpops_only", "label": "仅单节点TPOPS", "conf": "single_tpops_user_edit_file.conf"},
    {"id": "tpops_only_ha", "label": "仅HA TPOPS", "conf": "ha_tpops_user_edit_file.conf"},
    {"id": "gaussdb_only", "label": "仅准备GaussDB环境", "conf": "prepare_gaussdb_user_edit_file.conf"},
]

MODES = [
    {"id": "root", "label": "root模式", "desc": "全程使用root用户执行"},
    {"id": "service", "label": "service模式", "desc": "root准备环境 + service用户安装"},
]

CHECKLIST_CATEGORIES = [
    {"id": "hardware", "label": "硬件环境", "icon": "🖥️"},
    {"id": "software", "label": "软件环境", "icon": "💿"},
    {"id": "packages", "label": "安装包", "icon": "📦"},
    {"id": "config", "label": "配置文件", "icon": "⚙️"},
    {"id": "pre_deploy", "label": "部署前确认", "icon": "🚀"},
]

CHECKLIST_ITEMS = {
    "hardware": [
        {"id": "hw-1", "label": "磁盘数量 ≥6块/节点", "prod": True, "test": True},
        {"id": "hw-2", "label": "系统盘RAID1", "prod": True, "test": False},
        {"id": "hw-3", "label": "数据盘RAID10", "prod": True, "test": False},
        {"id": "hw-4", "label": "数据盘单盘 ≥1000GB", "prod": True, "test": False},
        {"id": "hw-5", "label": "数据盘挂载 /data", "prod": True, "test": True},
        {"id": "hw-6", "label": "文件系统 ext4", "prod": True, "test": True},
        {"id": "hw-7", "label": "CPU ≥16核", "prod": True, "test": False},
        {"id": "hw-8", "label": "内存 ≥32GB", "prod": True, "test": False},
        {"id": "hw-9", "label": "万兆网络", "prod": True, "test": False},
    ],
    "software": [
        {"id": "sw-1", "label": "操作系统 Kylin V10", "prod": True, "test": True},
        {"id": "sw-2", "label": "yum源可用", "prod": True, "test": True},
        {"id": "sw-3", "label": "SSH免密互信", "prod": True, "test": True},
        {"id": "sw-4", "label": "SELinux Disabled/Permissive", "prod": True, "test": True},
        {"id": "sw-5", "label": "防火墙关闭或开放端口", "prod": True, "test": True},
        {"id": "sw-6", "label": "时钟同步(chronyd)", "prod": True, "test": True},
        {"id": "sw-7", "label": "Python ≥3.6", "prod": True, "test": True},
    ],
    "packages": [
        {"id": "pkg-1", "label": "Z-DBMate包已上传解压", "prod": True, "test": True},
        {"id": "pkg-2", "label": "TPOPS安装包已上传", "prod": True, "test": True},
        {"id": "pkg-3", "label": "GaussDB安装包已上传", "prod": True, "test": True},
        {"id": "pkg-4", "label": "系统镜像ISO已上传", "prod": True, "test": True},
        {"id": "pkg-5", "label": "ISO版本与OS一致", "prod": True, "test": True},
    ],
    "config": [
        {"id": "cfg-1", "label": "选择正确模板", "prod": True, "test": True},
        {"id": "cfg-2", "label": "TPOPS IP地址正确", "prod": True, "test": True},
        {"id": "cfg-3", "label": "GaussDB IP地址正确", "prod": True, "test": True},
        {"id": "cfg-4", "label": "路径有足够空间", "prod": True, "test": True},
        {"id": "cfg-5", "label": "端口8002/40080未被占用", "prod": True, "test": True},
        {"id": "cfg-6", "label": "service用户ID与配置一致", "prod": True, "test": True},
    ],
    "pre_deploy": [
        {"id": "pre-1", "label": "precheck.sh全部通过", "prod": True, "test": True},
        {"id": "pre-2", "label": "数据已备份", "prod": True, "test": False},
        {"id": "pre-3", "label": "已通知相关人员", "prod": True, "test": True},
        {"id": "pre-4", "label": "回退方案已准备", "prod": True, "test": True},
        {"id": "pre-5", "label": "root密码已确认", "prod": True, "test": True},
    ],
}

# ================================================================
# 模拟预检数据（用于UI展示，实际部署时对接precheck.sh）
# ================================================================
MOCK_PRECHECK = {
    "network": {"status": "pass", "detail": "4节点全部可达 (0.5ms-1.2ms)"},
    "ssh": {"status": "pass", "detail": "所有节点免密登录成功"},
    "os_version": {"status": "pass", "detail": "Kylin Linux Advanced Server V10 (Sword)"},
    "disk_count": {"status": "warn", "detail": "节点1: 8块 / 节点2: 6块 / 节点3: 4块(⚠️)"},
    "disk_mount": {"status": "pass", "detail": "/data 已挂载, 2.4TB可用"},
    "disk_space": {"status": "warn", "detail": "单盘1.2TB(满足测试要求, 生产需≥1000GB)"},
    "clock_sync": {"status": "pass", "detail": "chronyd已同步, 偏移<1ms"},
    "memory": {"status": "pass", "detail": "节点1: 64GB / 节点2: 64GB / 节点3: 32GB"},
    "cpu": {"status": "pass", "detail": "32核/节点"},
    "yum": {"status": "fail", "detail": "节点3 yum源不可用（需要检查仓库配置）"},
    "selinux": {"status": "pass", "detail": "Permissive"},
    "firewall": {"status": "warn", "detail": "firewalld active（需确认8002/40080端口已开放）"},
}


# ================================================================
# Flask Routes
# ================================================================

@app.route("/")
def index():
    """Z-DBMate 仪表盘"""
    return render_template("zd_dashboard.html",
                           precheck_items=PRECHECK_ITEMS,
                           scenarios=SCENARIOS,
                           modes=MODES)


@app.route("/precheck")
def precheck():
    """预检可视化"""
    return render_template("zd_precheck.html",
                           precheck_items=PRECHECK_ITEMS,
                           mock_data=MOCK_PRECHECK)


@app.route("/deploy")
def deploy():
    """部署控制台"""
    return render_template("zd_deploy.html",
                           scenarios=SCENARIOS,
                           modes=MODES)


@app.route("/monitor")
def monitor():
    """监控看板"""
    return render_template("zd_monitor.html")


@app.route("/checklist")
def checklist():
    """检查清单"""
    return render_template("zd_checklist.html",
                           categories=CHECKLIST_CATEGORIES,
                           items=CHECKLIST_ITEMS)


@app.route("/api/precheck")
def api_precheck():
    """API: 返回预检数据"""
    return jsonify({"items": PRECHECK_ITEMS, "results": MOCK_PRECHECK,
                    "summary": {
                        "pass": sum(1 for v in MOCK_PRECHECK.values() if v["status"] == "pass"),
                        "warn": sum(1 for v in MOCK_PRECHECK.values() if v["status"] == "warn"),
                        "fail": sum(1 for v in MOCK_PRECHECK.values() if v["status"] == "fail"),
                        "total": len(MOCK_PRECHECK),
                    }})


@app.route("/api/deploy/run", methods=["POST"])
def api_deploy_run():
    """API: 执行部署（模拟）"""
    data = request.get_json() or {}
    scenario = data.get("scenario", "main_install_single")
    mode = data.get("mode", "root")
    return jsonify({
        "status": "started",
        "message": f"部署已启动: mode={mode}, scenario={scenario}",
        "pid": 12345,
        "log_file": "/data/Z-DBMate/deploy.log",
    })


@app.route("/api/monitor/status")
def api_monitor_status():
    """API: 监控状态"""
    # 模拟数据
    steps = [
        {"name": "yum仓库配置", "file": "deploy_yum_done", "done": True},
        {"name": "依赖包安装", "file": "install_lib_done", "done": True},
        {"name": "系统配置修改", "file": "modify_config_done", "done": True},
        {"name": "Python安装", "file": "build_python3_done", "done": False},
    ]
    pct = sum(1 for s in steps if s["done"]) * 100 // len(steps)
    return jsonify({
        "steps": steps,
        "progress": pct,
        "errors": 2,
        "warnings": 5,
        "recent_errors": [
            "[WARN] 节点3 yum源超时，重试中...",
            "[INFO] 文件分发完成: node1 node2 node3",
        ],
        "disk_used": "45%",
        "mem_used": "62%",
        "running_time": "00:23:15",
    })


if __name__ == "__main__":
    print("=" * 50)
    print("  Z-DBMate 部署工具集 - Web UI")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5001")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5001)
