"""
DWS 智能部署系统 - Web UI (Flask)
面向 GaussDB(DWS) MPP 数仓 FusionInsight 部署

双模式:
  demo  (默认) — Mock 预检数据 + 引擎架构数据，无需 SSH
  engine       — 真实引擎驱动（需 SSH 执行器）

架构:
  engine/core_engine.py  — 嘉兴银行 DWS-POC 引擎（一字不改，1177行）
  core/precheck_engine.py — 预检规则（17项→逐步扩展）
  core/verifier.py        — 部署后验证（10项）

集成: 预检 / 配置生成 / 部署引导 / 架构图 / 设备清单 / 审计日志
"""

import os, sys, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, redirect, url_for

# ── 原有规则模块 ──
from core.precheck_engine import PRECHECK_ITEMS, PRECHECK_PHASES
from core.config_generator import DWSConfig, generate_preinstall_ini
from core.verifier import VERIFY_ITEMS

# ── SSH 执行器 ──
from engine.ssh_executor import SSHExecutor

# ── 嘉兴引擎（一字不改） ──
from engine.core_engine import (
    get_or_create_session, reset_session, _init_phases,
    get_architecture_data, ARCH_SCENARIOS, ROLE_META,
    switch_environment, ENV_PRESETS, EQUIPMENT_LIST, RACK_LAYOUT,
    ARCH_ENV_MAP, DEPLOY_TOPOLOGIES,
)

app = Flask(__name__)
app.jinja_env.auto_reload = True

# ─── 模拟预检数据（demo 模式用, 40项） ───
MOCK_PRECHECK = {
    # 硬件 (12项)
    "hw-raid":          {"status": "pass", "detail": "storcli64可用, RAID策略已配置"},
    "hw-disk-count":    {"status": "pass", "detail": "8块盘/节点 (满足生产≥6)"},
    "hw-network-card":  {"status": "pass", "detail": "25GE, MTU=1500, Hi1822已配置"},
    "hw-ssd-check":     {"status": "pass", "detail": "全部为SSD(ROTA=0)"},
    "hw-bios-numa":     {"status": "pass", "detail": "numa_balancing=0, 节能模式关闭"},
    "hw-bios-version":  {"status": "pass", "detail": "BIOS V158 (Kunpeng)"},
    "hw-uefi-mode":     {"status": "pass", "detail": "UEFI模式"},
    "hw-cpu-freq":      {"status": "pass", "detail": "2400MHz"},
    "hw-mem-freq":      {"status": "pass", "detail": "2933MT/s"},
    "hw-pcie-link":     {"status": "pass", "detail": "PCIe Gen3 x8 正常"},
    "hw-raid-cache":    {"status": "pass", "detail": "RAID缓存=2GB, Read Ahead已启用"},
    "hw-bbu-status":    {"status": "pass", "detail": "BBU状态正常, 电量100%"},
    # OS (15项)
    "os-audit":         {"status": "pass", "detail": "auditd已关闭"},
    "os-firewall":      {"status": "warn", "detail": "firewalld已关闭, iptables未开启"},
    "os-selinux":       {"status": "pass", "detail": "SELinux=disabled"},
    "os-swap":          {"status": "pass", "detail": "swap已关闭"},
    "os-hugepage":      {"status": "pass", "detail": "透明大页已关闭"},
    "os-timezone":      {"status": "pass", "detail": "Asia/Shanghai"},
    "os-charset":       {"status": "pass", "detail": "en_US.UTF-8"},
    "os-kernel-params": {"status": "warn", "detail": "watermark=100 ✅, numa=0 ✅, OOM待确认"},
    "os-umask":         {"status": "pass", "detail": "umask=0022"},
    "os-file-max":      {"status": "pass", "detail": "fs.file-max=1000000"},
    "os-tcp-params":    {"status": "warn", "detail": "tcp_tw_reuse=1, somaxconn=65535 ✅, ip_local_port_range=20000-60999(需调整)"},
    "os-arp-filter":    {"status": "pass", "detail": "arp_filter=0, arp_ignore=0, arp_announce=2"},
    "os-ntp-offset":    {"status": "pass", "detail": "NTP已同步, 偏移<1ms"},
    "os-ssh-config":    {"status": "pass", "detail": "MaxSessions=1024, UseDNS=no"},
    "os-password-policy": {"status": "warn", "detail": "PASS_MAX_DAYS=99999(需调整为90天)"},
    # 网络 (8项)
    "net-switch-mtu":       {"status": "pass", "detail": "MTU=1500 全网一致"},
    "net-vlan-config":      {"status": "warn", "detail": "管理平面VLAN=101, 业务平面VLAN=102"},
    "net-route-reach":      {"status": "pass", "detail": "3节点全部可达"},
    "net-bandwidth-test":   {"status": "pass", "detail": "iperf3: 950MB/s(满足≥800MB/s)"},
    "net-retrans":          {"status": "pass", "detail": "重传率≈0.002%(满足<0.01%)"},
    "net-port-negotiation": {"status": "pass", "detail": "所有端口=10000Mb/s"},
    "net-stp-status":       {"status": "pass", "detail": "STP边缘端口已配置"},
    "net-mac-table":        {"status": "pass", "detail": "MAC学习正常"},
    # 存储 (5项)
    "stor-mount":       {"status": "pass", "detail": "4个目录全部挂载"},
    "stor-fstab":       {"status": "pass", "detail": "/etc/fstab已配置"},
    "stor-striping":    {"status": "pass", "detail": "RAID5条带=256KB"},
    "stor-alignment":   {"status": "pass", "detail": "分区2048s对齐, 4K对齐确认"},
    "stor-readahead":   {"status": "pass", "detail": "readahead=4096 (2MB)"},
    # 软件 (2项)
    "sw-python":        {"status": "pass", "detail": "Python 3.8.5 已安装"},
    "sw-yum":           {"status": "pass", "detail": "yum源可用, ISO已挂载"},
}

# ================================================================
# 仪表盘
# ================================================================
@app.route("/")
def index():
    """仪表盘：显示 7 阶段部署流程 + 工具链联动 + 引擎会话信息"""
    session = get_or_create_session()
    return render_template("dws_dashboard.html",
                           precheck_items=PRECHECK_ITEMS,
                           phases=PRECHECK_PHASES,
                           engine_data=session.to_dict())

# ================================================================
# 预检（保留原实现，双模式返回）
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

@app.route("/api/precheck/commands")
def api_precheck_commands():
    """获取预检命令文本（demo 模式：复制粘贴执行）"""
    nodes = request.args.get("nodes", "").split(",")
    nodes = [n.strip() for n in nodes if n.strip()]
    if not nodes:
        nodes = ["node1", "node2", "node3"]
    executor = SSHExecutor(mode="demo")
    text = executor.format_node_commands(PRECHECK_ITEMS, nodes)
    return jsonify({"commands": text, "mode": "demo", "node_count": len(nodes)})

@app.route("/api/precheck/run", methods=["POST"])
def api_precheck_run():
    """执行预检 — 双模式（demo/ssh）

    POST JSON:
      mode: "demo" | "ssh"
      nodes: ["10.134.21.190", "10.134.21.191", ...]
      username: "root" (ssh模式)
      password: "xxx"  (ssh模式)

    返回:
      results: [{item_id, node, mode, status, detail, ...}]
      summary: {pass, warn, fail, total}
    """
    data = request.get_json() or {}
    mode = data.get("mode", "demo")
    nodes = data.get("nodes", [])
    item_ids = data.get("items", None)  # 可选：指定检查项ID列表

    if not nodes:
        return jsonify({"error": "请提供节点列表 (nodes)"}), 400

    # 筛选要执行的检查项
    items = PRECHECK_ITEMS
    if item_ids:
        id_set = set(item_ids)
        items = [i for i in PRECHECK_ITEMS if i["id"] in id_set]

    if mode == "ssh":
        username = data.get("username", "root")
        password = data.get("password", "")
        key_file = data.get("key_file", "")
        port = int(data.get("port", 22))
        executor = SSHExecutor(mode="ssh", username=username,
                               password=password, key_file=key_file, port=port)
    else:
        executor = SSHExecutor(mode="demo")

    results = executor.run_checks(items, nodes, parallel=(mode == "ssh"))

    # 统计
    summary = {"pass": 0, "warn": 0, "fail": 0, "pending": 0, "total": len(results)}
    for r in results:
        s = r.get("status", "pending")
        if s in summary:
            summary[s] += 1

    return jsonify({"results": results, "summary": summary, "mode": mode})

# ================================================================
# LLD 配置生成（增强版：接入嘉兴引擎 + 保留原有生成器）
# ================================================================
@app.route("/config")
def config():
    """配置页：嘉兴引擎的完整 60+ 参数表单"""
    session = get_or_create_session()
    return render_template("dws_config.html", data=session.to_dict())

@app.route("/api/config/generate", methods=["POST"])
def api_config_generate():
    """生成 preinstall.ini — 双模式：简单/引擎"""
    data = request.get_json() or {}
    use_engine = data.get("use_engine", False)

    if use_engine:
        # 使用嘉兴引擎生成完整 LLD 配置
        session = get_or_create_session()
        session.generate_templates()
        tmpls = session.templates
        return jsonify({
            "content": tmpls.get("preinstall.ini", ""),
            "all_templates": {
                k: v[:500] + "..." if len(v) > 500 else v
                for k, v in tmpls.items()
            }
        })
    else:
        # 原有简单生成
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
# 模板预览（嘉兴引擎）
# ================================================================
@app.route("/templates")
def view_templates():
    session = get_or_create_session()
    session.generate_templates()
    return render_template("dws_templates.html", data=session.to_dict())

# ================================================================
# 部署引导
# ================================================================
@app.route("/deploy")
def deploy():
    return render_template("dws_deploy.html")

@app.route("/flow")
def flow():
    return render_template("dws_flow.html")

@app.route("/api/deploy/plan")
def api_deploy_plan():
    """部署计划 — 双模式：demo 返回 Mock，engine 返回真实阶段"""
    results = MOCK_PRECHECK
    all_pass = all(v["status"] != "fail" for v in results.values())
    return jsonify({
        "ready": all_pass,
        "phases": [
            {"name": "环境准备", "status": "done", "steps": 5},
            {"name": "OS配置",   "status": "done", "steps": 8},
            {"name": "磁盘分区", "status": "ready", "steps": 6},
            {"name": "软件安装", "status": "ready", "steps": 4},
            {"name": "集群部署", "status": "pending", "steps": 5},
            {"name": "性能测试", "status": "pending", "steps": 4},
            {"name": "验收交付", "status": "pending", "steps": 5},
        ]
    })

# ================================================================
# 步骤执行（嘉兴引擎）
# ================================================================
@app.route("/phase/<int:phase_id>")
def phase_detail(phase_id):
    session = get_or_create_session()
    phase = next((p for p in session.phases if p["id"] == phase_id), None)
    if not phase:
        return redirect(url_for("index"))
    return render_template("dws_phase.html", phase=phase, data=session.to_dict())

@app.route("/execute", methods=["POST"])
def execute_step():
    d = request.get_json() or {}
    phase_id = int(d.get("phase_id", 0))
    step_id = d.get("step_id", "")
    skip = d.get("skip", False)
    return jsonify(get_or_create_session().execute_step(phase_id, step_id, skip=skip))

# ================================================================
# 部署验证（保留原实现）
# ================================================================
@app.route("/verify")
def verify():
    return render_template("dws_verify.html", items=VERIFY_ITEMS)

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
# 检查清单（保留原实现）
# ================================================================
@app.route("/checklist")
def checklist():
    return render_template("dws_checklist.html")

# ================================================================
# 审计日志（嘉兴引擎）
# ================================================================
@app.route("/audit_log")
def audit_log():
    return render_template("dws_audit.html", data=get_or_create_session().to_dict())

@app.route("/reset")
def reset():
    reset_session()
    return redirect(url_for("index"))

# ================================================================
# 架构图（嘉兴引擎）
# ================================================================
@app.route("/architecture")
def architecture_page():
    return render_template("dws_architecture.html",
                          scenarios=ARCH_SCENARIOS,
                          data=get_or_create_session().to_dict())

@app.route("/api/architecture")
def api_architecture():
    scenario = request.args.get("scenario", "uat")
    cn = request.args.get("cn", type=int)
    dn = request.args.get("dn", type=int)
    co = request.args.get("co_deploy", "").lower() == "true"

    if scenario in ARCH_SCENARIOS and not cn and not dn:
        result = get_architecture_data(scenario)
    else:
        s = ARCH_SCENARIOS.get(scenario, ARCH_SCENARIOS["uat"])
        from engine.core_engine import build_architecture_nodes
        result = build_architecture_nodes(
            total_cn=cn or s["cn"],
            total_dn=dn or s["dn"],
            om_nodes=s["om"],
            gtm_nodes=s["gtm"],
            co_deploy=co,
        )

    hw = ARCH_SCENARIOS.get(scenario, {}).get("hw") or ARCH_SCENARIOS.get(scenario, {}).get("hw_data")
    hw_ctrl = ARCH_SCENARIOS.get(scenario, {}).get("hw_ctrl")
    hw_data = ARCH_SCENARIOS.get(scenario, {}).get("hw_data")
    current_env = get_or_create_session().config.get("environment", "UAT")
    default_scenario = ARCH_ENV_MAP.get(current_env, "uat")

    return jsonify({
        **result,
        "scenarios": {k: {"name": v["name"], "desc": v["desc"]} for k, v in ARCH_SCENARIOS.items()},
        "role_meta": {k: v for k, v in ROLE_META.items()},
        "hardware": {"common": hw, "ctrl": hw_ctrl, "data": hw_data},
        "default_scenario": default_scenario,
    })

# ================================================================
# 环境切换（嘉兴引擎）
# ================================================================
@app.route("/env/switch/<env_key>")
def switch_env(env_key):
    cfg = switch_environment(env_key)
    if not cfg:
        return jsonify({"ok": False, "error": f"未知环境: {env_key}"})
    session = get_or_create_session()
    session.config = cfg
    session.phases = _init_phases(cfg)
    session.generate_templates()
    return redirect(url_for("index"))

@app.route("/api/env")
def api_env():
    return jsonify({
        "current": get_or_create_session().config.get("environment", "UAT"),
        "presets": {k: {"name": v["name"], "desc": v["desc"]} for k, v in ENV_PRESETS.items()},
    })

# ================================================================
# 设备清单（嘉兴引擎）
# ================================================================
@app.route("/equipment")
def equipment_page():
    env = get_or_create_session().config.get("environment", "UAT")
    env_servers = []
    for s in EQUIPMENT_LIST["servers"]:
        if "DWS" not in s["type"]:
            continue
        env_s = dict(s)
        if env == "DEV":
            env_s["qty"] = 3
            env_s["type"] = "DWS 合设节点 (OM+CN+DN+GTM)"
            env_s["hosts"] = "dwsdev0001, dwsdev0002, dwsdev0003"
            env_s["rack"] = "8号柜/9号柜"
            env_s["ram"] = "512GB (8×64G DDR4)"
            env_s["disk"] = "2×960G SSD + 12×4T HDD (RAID5)"
            env_servers = [env_s]
            break
        elif env == "SIT":
            env_s["qty"] = 3
            env_s["type"] = "DWS 合设节点 (OM+CN+DN+GTM)"
            env_s["hosts"] = "dwssit0001, dwssit0002, dwssit0003"
            env_s["rack"] = "8号柜/9号柜"
            env_s["ram"] = "512GB (8×64G DDR4)"
            env_s["disk"] = "2×960G SSD + 12×4T HDD (RAID5)"
            env_servers = [env_s]
            break
        elif env == "UAT":
            env_s["qty"] = 3
            env_s["type"] = "DWS 合设节点 (OM+CN+DN+GTM)"
            env_s["hosts"] = "dwsuat0001, dwsuat0002, dwsuat0003"
            env_s["rack"] = "8号柜/9号柜"
            env_s["ram"] = "512GB (8×64G DDR4)"
            env_s["disk"] = "2×960G SSD + 24×4T HDD (RAID5)"
            env_servers = [env_s]
            break
        elif env == "PREPROD":
            if "管控" in s["type"]:
                env_s["qty"] = 2
                env_s["hosts"] = "dws-preprod-mn-01, dws-preprod-mn-02"
                env_s["rack"] = "8号柜/9号柜"
            else:
                env_s["qty"] = 5
                env_s["hosts"] = "dws-preprod-dn-01~05"
                env_s["rack"] = "8号柜×2, 9号柜×3"
        env_servers.append(env_s)

    env_equipment = {
        "servers": env_servers,
        "network": EQUIPMENT_LIST["network"],
        "security": EQUIPMENT_LIST["security"],
    }
    return render_template("dws_equipment.html",
                          equipment=env_equipment,
                          racks=RACK_LAYOUT,
                          data=get_or_create_session().to_dict())


# ================================================================
# API 健康检查
# ================================================================
@app.route("/api/health")
def api_health():
    session = get_or_create_session()
    env = session.config.get("environment", "UAT")
    return jsonify({
        "status": "ok",
        "version": "2.0-dev",
        "mode": "demo",
        "environment": env,
        "precheck_items": len(PRECHECK_ITEMS),
        "verify_items": len(VERIFY_ITEMS),
        "phases": len(session.phases),
        "nodes": len(session.config.get("nodes", [])),
    })


if __name__ == "__main__":
    print("=" * 60)
    print("  DWS 智能部署系统 v2.0-dev")
    print("  引擎: 嘉兴银行 DWS-POC (engine/core_engine.py)")
    print(f"  预检: {len(PRECHECK_ITEMS)}项 | 验证: {len(VERIFY_ITEMS)}项")
    print(f"  部署阶段: {len(get_or_create_session().phases)}个")
    print("=" * 60)
    print("  访问地址: http://127.0.0.1:5053")
    print("  环境切换: http://127.0.0.1:5053/env/switch/DEV|SIT|UAT|PREPROD")
    print("  架构图:   http://127.0.0.1:5053/architecture")
    print("  审计日志: http://127.0.0.1:5053/audit_log")
    print("=" * 60)
    app.run(debug=False, host="127.0.0.1", port=5053)
