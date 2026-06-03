"""
DWS 智能部署系统 - Web UI (Flask)
面向 GaussDB(DWS) MPP 数仓 FusionInsight 部署
集成: 预检 / 配置生成 / 部署引导 / 验证
"""

import os, sys, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file

from core.precheck_engine import PRECHECK_ITEMS, PRECHECK_PHASES
from core.config_generator import DWSConfig, generate_preinstall_ini
from core.verifier import VERIFY_ITEMS

app = Flask(__name__)

# 模拟预检数据
MOCK_PRECHECK = {
    "hw-raid": {"status": "pass", "detail": "storcli64可用, RAID策略已配置"},
    "hw-disk-count": {"status": "pass", "detail": "8块盘/节点 (满足生产≥6)"},
    "hw-network-card": {"status": "pass", "detail": "25GE, MTU=1500, Hi1822已配置"},
    "hw-ssd-check": {"status": "pass", "detail": "全部为SSD(ROTA=0)"},
    "hw-bios-numa": {"status": "pass", "detail": "numa_balancing=0, 节能模式关闭"},
    "os-audit": {"status": "pass", "detail": "auditd已关闭"},
    "os-firewall": {"status": "warn", "detail": "firewalld已关闭, iptables未开启"},
    "os-selinux": {"status": "pass", "detail": "SELinux=disabled"},
    "os-swap": {"status": "pass", "detail": "swap已关闭"},
    "os-hugepage": {"status": "pass", "detail": "透明大页已关闭"},
    "os-timezone": {"status": "pass", "detail": "Asia/Shanghai"},
    "os-charset": {"status": "pass", "detail": "en_US.UTF-8"},
    "os-kernel-params": {"status": "warn", "detail": "watermark=100 ✅, numa=0 ✅, OOM需确认"},
    "stor-mount": {"status": "pass", "detail": "4个目录全部挂载"},
    "stor-fstab": {"status": "pass", "detail": "/etc/fstab已配置"},
    "sw-python": {"status": "pass", "detail": "Python 3.8.5 已安装"},
    "sw-yum": {"status": "pass", "detail": "yum源可用, ISO已挂载"},
}

# ================================================================
# Route: 首页 - 仪表盘
# ================================================================
@app.route("/")
def index():
    return render_template("dws_dashboard.html",
                           precheck_items=PRECHECK_ITEMS,
                           phases=PRECHECK_PHASES)

# ================================================================
# Route: 预检页面
# ================================================================
@app.route("/precheck")
def precheck():
    return render_template("dws_precheck.html",
                           items=PRECHECK_ITEMS,
                           phases=PRECHECK_PHASES,
                           mock_data=MOCK_PRECHECK)

@app.route("/api/precheck")
def api_precheck():
    results = MOCK_PRECHECK
    summary = {"pass": 0, "warn": 0, "fail": 0, "total": len(results)}
    for v in results.values():
        summary[v["status"]] += 1
    return jsonify({"items": PRECHECK_ITEMS, "results": results, "summary": summary})

# ================================================================
# Route: 配置生成
# ================================================================
@app.route("/config")
def config():
    return render_template("dws_config.html")

@app.route("/api/config/generate", methods=["POST"])
def api_config_generate():
    data = request.get_json() or {}
    cfg = DWSConfig(
        cluster_name=data.get("cluster_name", "dws_cluster"),
        master_node1_ip=data.get("master_node1_ip", ""),
        master_node2_ip=data.get("master_node2_ip", ""),
        data_node_ips=data.get("data_node_ips", ""),
        cn_num=int(data.get("cn_num", 3)),
        dn_num=int(data.get("dn_num", 3)),
        db_port=int(data.get("db_port", 40080)),
        timezone=data.get("timezone", "Asia/Shanghai"),
    )
    ini_content = generate_preinstall_ini(cfg)
    return jsonify({"content": ini_content})

# ================================================================
# Route: 部署引导
# ================================================================
@app.route("/deploy")
def deploy():
    return render_template("dws_deploy.html")

@app.route("/api/deploy/plan")
def api_deploy_plan():
    """根据预检结果生成部署计划"""
    results = MOCK_PRECHECK
    all_pass = all(v["status"] != "fail" for v in results.values())
    return jsonify({
        "ready": all_pass,
        "phases": [
            {"name": "环境准备", "status": "done", "steps": 5},
            {"name": "OS配置", "status": "done", "steps": 8},
            {"name": "磁盘分区", "status": "ready", "steps": 6},
            {"name": "软件安装", "status": "ready", "steps": 4},
            {"name": "集群部署", "status": "pending", "steps": 5},
            {"name": "性能测试", "status": "pending", "steps": 4},
            {"name": "验收交付", "status": "pending", "steps": 5},
        ]
    })

# ================================================================
# Route: 验证
# ================================================================
@app.route("/verify")
def verify():
    return render_template("dws_verify.html",
                           items=VERIFY_ITEMS)

@app.route("/api/verify")
def api_verify():
    mock = {}
    for item in VERIFY_ITEMS:
        mock[item["id"]] = {
            "status": "pass" if item["phase"] != "perf_test" else "warn",
            "detail": f"检查: {item['description']}"
        }
    return jsonify({"items": VERIFY_ITEMS, "results": mock})

# ================================================================
# Route: 检查清单
# ================================================================
@app.route("/checklist")
def checklist():
    return render_template("dws_checklist.html")

if __name__ == "__main__":
    print("=" * 50)
    print("  DWS 智能部署系统 - Web UI")
    print(f"  预检: {len(PRECHECK_ITEMS)}项 | 验证: {len(VERIFY_ITEMS)}项")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5013")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5013)
