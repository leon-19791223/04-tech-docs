"""
DWS 智能部署系统 - Web UI (Flask)
面向 GaussDB(DWS) MPP 数仓 FusionInsight 部署

双模式:
  demo  (默认) — Mock 预检数据 + 引擎架构数据，无需 SSH
  engine       — 真实引擎驱动（需 SSH 执行器）

架构:
  engine/core_engine.py  — ⚠️ VENDOR: 嘉兴银行 DWS-POC（一字不改）
  core/precheck_engine.py — 预检规则（42项）
  core/verifier.py        — 部署后验证（10项）

集成: 预检 / 配置生成 / 部署引导 / 架构图 / 设备清单 / 审计日志 / 交付报告 / 会话管理
生产化改造: B-0 ~ B-7 全部完成 (参见 DEVELOPMENT_PLAN.md)
版本: v2.0
"""

import os, sys, json
from datetime import datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, redirect, url_for
from functools import wraps

# ── 自有规则模块 ──
from core.precheck_engine import PRECHECK_ITEMS, PRECHECK_PHASES
from core.config_generator import (
    DWSConfig, ClusterConfig, NodeSpec, OMSConfig,
    generate_preinstall_ini, generate_host_inis,
    generate_install_oms_ini, generate_cluster_install_template
)
from core.verifier import VERIFY_ITEMS

# ── SSH 执行器（含安全策略） ──
from engine.ssh_executor import SSHExecutor, SSHHostKeyPolicy

# ── 凭据管理器 ──
from engine.credential_manager import get_credential_manager, CredentialManager

# ── 报告生成器 ──
from engine.report_generator import (
    ReportContext, DeliveryMetadata,
    generate_deliverable_bundle
)

# ── 配置校验器 ──
from engine.config_validator import get_validator
from engine.report_generator import (
    ReportContext, DeliveryMetadata,
    generate_deliverable_bundle
)

# ── 嘉兴引擎（vendor 代码，一字不改） ──
from engine.core_engine import (
    get_or_create_session, reset_session, _init_phases,
    get_architecture_data, switch_environment,
    DEPLOY_TOPOLOGIES,
)

# ── 供应商数据加载器（JSON 优先，fallback 到 vendor） ──
_VENDOR_DATA_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf", "environment_presets.json")
_vendor_data = None

def _load_vendor_data(key: str, default=None):
    """加载供应商预设数据

    优先级: conf/environment_presets.json > core_engine.py (vendor fallback)
    这样新增银行预设只需编辑 JSON 文件，无需修改 vendor 代码。
    """
    global _vendor_data
    if _vendor_data is None:
        if os.path.exists(_VENDOR_DATA_PATH):
            try:
                with open(_VENDOR_DATA_PATH, "r", encoding="utf-8") as f:
                    _vendor_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                _vendor_data = {}
        else:
            _vendor_data = {}
    if key in _vendor_data:
        return _vendor_data[key]
    # fallback: 从 vendor 引擎获取
    return _fallback_vendor_data(key, default)

def _fallback_vendor_data(key, default=None):
    """JSON 加载失败时的 fallback 到 vendor 引擎"""
    try:
        if key == "ENV_PRESETS":
            from engine.core_engine import ENV_PRESETS
            return ENV_PRESETS
        elif key == "ARCH_SCENARIOS":
            from engine.core_engine import ARCH_SCENARIOS
            return ARCH_SCENARIOS
        elif key == "ARCH_ENV_MAP":
            from engine.core_engine import ARCH_ENV_MAP
            return ARCH_ENV_MAP
        elif key == "ROLE_META":
            from engine.core_engine import ROLE_META
            return ROLE_META
        elif key == "EQUIPMENT_LIST":
            from engine.core_engine import EQUIPMENT_LIST
            return EQUIPMENT_LIST
        elif key == "RACK_LAYOUT":
            from engine.core_engine import RACK_LAYOUT
            return RACK_LAYOUT
        else:
            return default
    except (ImportError, AttributeError):
        return default

# 导出供路由使用（优先 JSON，fallback vendor）
ENV_PRESETS = _load_vendor_data("ENV_PRESETS", {})
ARCH_SCENARIOS = _load_vendor_data("ARCH_SCENARIOS", {})
ARCH_ENV_MAP = _load_vendor_data("ARCH_ENV_MAP", {})
ROLE_META = _load_vendor_data("ROLE_META", {})
EQUIPMENT_LIST = _load_vendor_data("EQUIPMENT_LIST", {})
RACK_LAYOUT = _load_vendor_data("RACK_LAYOUT", [])

app = Flask(__name__)
app.jinja_env.auto_reload = True

# ─── Mock 场景管理 ──────────────────────────────────────
_SCENARIOS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "conf", "scenarios.json")
_scenarios_data = None
_current_scenario = "typical_issues"

def _load_scenarios():
    global _scenarios_data
    if _scenarios_data is None:
        if os.path.exists(_SCENARIOS_PATH):
            try:
                with open(_SCENARIOS_PATH, "r", encoding="utf-8") as f:
                    _scenarios_data = json.load(f)
            except Exception:
                _scenarios_data = {"scenarios": {"all_pass": {"label": "全部通过"}}}
        else:
            _scenarios_data = {"scenarios": {"all_pass": {"label": "全部通过"}}}
    return _scenarios_data

def _get_scenario_overrides(scenario_key=None):
    sc = _load_scenarios()
    key = scenario_key or _current_scenario
    scenario = sc.get("scenarios", {}).get(key, {})
    return scenario.get("overrides", {})

# ─── 鉴权配置（可选） ─────────────────────────────────────
app.config['AUTH_ENABLED'] = os.environ.get('DWS_AUTH_ENABLED', 'false').lower() == 'true'
app.config['AUTH_TOKEN'] = os.environ.get('DWS_AUTH_TOKEN', 'dws-default-token')

def require_auth(f):
    """可选鉴权中间件 — 仅 SSH 模式受保护，demo 模式开放"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not app.config['AUTH_ENABLED']:
            return f(*args, **kwargs)
        token = request.headers.get('X-Auth-Token') or request.args.get('token')
        if token != app.config['AUTH_TOKEN']:
            return jsonify({"error": "未授权访问，请提供有效 Token"}), 401
        return f(*args, **kwargs)
    return decorated

# ─── 凭据管理器（全局单例） ──────────────────────────────
credential_manager: CredentialManager = get_credential_manager(ttl=300)
_source_ip = "127.0.0.1"

# ─── 会话持久化（SQLite，重启不丢失） ──────────────────
from engine.session_store import SessionStore
session_store = SessionStore()
_last_session_id = "default"

def _save_current_session():
    """持久化当前会话到 SQLite"""
    try:
        session = get_or_create_session()
        data = {
            "summary": {
                "environment": session.config.get("environment", "UAT"),
                "cluster_name": session.config.get("cluster_name", ""),
                "node_count": len(session.config.get("nodes", [])),
            },
            "config": {k: v for k, v in session.config.items()
                       if k != "nodes"},
            "environment": session.config.get("environment", "UAT"),
            "audit_log": getattr(session, 'audit_log', [])[-100:],
            "templates": getattr(session, 'templates', {}),
        }
        session_store.save(_last_session_id, data)
    except Exception:
        pass  # 持久化失败不阻塞业务  # 将在请求上下文中更新

@app.before_request
def _update_source_ip():
    global _source_ip
    _source_ip = request.remote_addr or "127.0.0.1"

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
    """预检结果 API（已考虑当前 Mock 场景）"""
    import copy
    results = copy.deepcopy(MOCK_PRECHECK)
    # 应用场景 override
    overrides = _get_scenario_overrides()
    for item_id, override in overrides.items():
        if item_id in results:
            results[item_id].update(override)
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
    """执行预检 — 三模式（demo/ssh/hybrid）+ 安全策略

    POST JSON:
      mode: "demo" | "ssh" | "hybrid"
      nodes: ["10.134.21.190", "10.134.21.191", ...]
      host_key_policy: "strict" | "warn" | "insecure"（仅ssh/hybrid模式）
      credential_id: "xxx"       （推荐：通过 /api/credential/store 获取）
      username/password/key_file （兼容旧接口：直接传凭据）
      port: 22
      items: ["hw-raid", ...]    （可选：指定检查项）

    返回:
      results: [{item_id, node, mode, status, detail, ...}]
      summary: {pass, warn, fail, total}
      mode: "demo" | "ssh"
      security_warning: "..."    （安全策略警告文本）
    """
    data = request.get_json() or {}
    mode = data.get("mode", "demo")
    nodes = data.get("nodes", [])
    item_ids = data.get("items", None)

    if not nodes:
        return jsonify({"error": "请提供节点列表 (nodes)"}), 400

    # 筛选要执行的检查项
    items = PRECHECK_ITEMS
    if item_ids:
        id_set = set(item_ids)
        items = [i for i in PRECHECK_ITEMS if i["id"] in id_set]

    if mode == "ssh":
        # SSH 模式：使用安全策略 + 凭据管理
        host_key_policy = data.get("host_key_policy", "warn")
        credential_id = data.get("credential_id", "")
        port = int(data.get("port", 22))
        executor = SSHExecutor(
            mode="ssh",
            host_key_policy=host_key_policy,
            credential_id=credential_id,
            username=data.get("username", "root"),
            port=port,
            source_ip=_source_ip,
            operator=data.get("operator", "admin"),
        )
        # 兼容旧接口：直接传 password/key_file（无 credential_id 时生效）
        if not credential_id:
            executor._password = data.get("password", "")
            executor._key_file = data.get("key_file", "")
    else:
        # demo/hybrid 模式
        executor = SSHExecutor(mode=mode)

    results = executor.run_checks(items, nodes, parallel=(mode == "ssh"))

    # 统计
    summary = {"pass": 0, "warn": 0, "fail": 0, "pending": 0, "total": len(results)}
    for r in results:
        s = r.get("status", "pending")
        if s in summary:
            summary[s] += 1

    return jsonify({
        "results": results,
        "summary": summary,
        "mode": mode,
        "security_warning": executor.security_warning,
        "audit_count": len(executor.audit_log),
    })

# ================================================================
# Mock 场景管理
# ================================================================
@app.route("/api/scenarios")
def api_scenarios():
    """获取可用 Mock 场景列表和当前场景"""
    sc = _load_scenarios()
    scenarios = {
        k: {"label": v.get("label", k), "desc": v.get("desc", "")}
        for k, v in sc.get("scenarios", {}).items()
    }
    return jsonify({
        "scenarios": scenarios,
        "current": _current_scenario,
    })

@app.route("/api/scenarios/switch/<scenario_key>")
def api_scenario_switch(scenario_key):
    """切换 Mock 场景"""
    global _current_scenario
    sc = _load_scenarios()
    if scenario_key in sc.get("scenarios", {}):
        _current_scenario = scenario_key
        return jsonify({"ok": True, "current": scenario_key})
    return jsonify({"error": f"未知场景: {scenario_key}"}), 400

# ================================================================
# 预检统计 API（供雷达图使用）
# ================================================================
@app.route("/api/precheck/summary")
def api_precheck_summary():
    """预检结果分类统计（供前端雷达图渲染）

    返回:
      categories: [{name, key, pass, warn, fail, total}]
      total: {pass, warn, fail}
    """
    results = MOCK_PRECHECK
    categories = {
        "hardware": {"name": "硬件", "key": "hardware", "pass": 0, "warn": 0, "fail": 0, "total": 0},
        "os": {"name": "OS系统", "key": "os", "pass": 0, "warn": 0, "fail": 0, "total": 0},
        "network": {"name": "网络", "key": "network", "pass": 0, "warn": 0, "fail": 0, "total": 0},
        "storage": {"name": "存储", "key": "storage", "pass": 0, "warn": 0, "fail": 0, "total": 0},
        "software": {"name": "软件", "key": "software", "pass": 0, "warn": 0, "fail": 0, "total": 0},
    }
    cat_map = {}
    for item in PRECHECK_ITEMS:
        cat_map[item["id"]] = item.get("category", "os")

    for item_id, result in results.items():
        cat = cat_map.get(item_id, "os")
        if cat in categories:
            categories[cat][result["status"]] += 1
            categories[cat]["total"] += 1

    return jsonify({
        "categories": list(categories.values()),
        "total": {
            "pass": sum(c["pass"] for c in categories.values()),
            "warn": sum(c["warn"] for c in categories.values()),
            "fail": sum(c["fail"] for c in categories.values()),
        }
    })

# ================================================================
# SSE 实时进度流
# ================================================================
@app.route("/api/stream")
def api_stream():
    """SSE 实时进度推送（用于部署步骤执行监控）

    使用 Server-Sent Events 推送引擎状态。
    前端使用 EventSource 接收。
    """
    from flask import Response
    def event_stream():
        import time
        for i in range(60):
            session = get_or_create_session()
            env = session.config.get("environment", "UAT")
            data = {
                "type": "heartbeat",
                "environment": env,
                "mode": "demo",
                "timestamp": time.time(),
                "precheck": len(PRECHECK_ITEMS),
                "verify": len(VERIFY_ITEMS),
                "phases": len(session.phases),
            }
            yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"
            time.sleep(2)
    return Response(event_stream(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})

# ================================================================
# 凭据管理（安全加固）
# ================================================================
@app.route("/api/credential/store", methods=["POST"])
@require_auth
def api_credential_store():
    """加密存储 SSH 凭据，返回一次性的 credential_id

    POST JSON:
      type: "password" | "key_file"
      username: "root"
      password: "xxx"        （type=password 时）
      key_file: "内容..."     （type=key_file 时）
      passphrase: "..."      （可选，key_file 加密时）

    返回:
      credential_id: "abc123..."  （一次性，TTL=300秒）
      expires_in: 300
    """
    data = request.get_json() or {}
    cred_type = data.get("type", "password")
    username = data.get("username", "root")

    credential = {"username": username}
    if cred_type == "password":
        password = data.get("password", "")
        if not password:
            return jsonify({"error": "password 不能为空"}), 400
        credential["password"] = password
    elif cred_type == "key_file":
        key_file = data.get("key_file", "")
        if not key_file:
            return jsonify({"error": "key_file 不能为空"}), 400
        credential["key_file"] = key_file
        if data.get("passphrase"):
            credential["passphrase"] = data["passphrase"]
    else:
        return jsonify({"error": f"不支持的凭据类型: {cred_type}"}), 400

    credential_id = credential_manager.store(
        credential_type=cred_type,
        credential=credential,
        source_ip=_source_ip,
    )

    return jsonify({
        "credential_id": credential_id,
        "expires_in": 300,
        "warning": "凭据一次性使用，TTL=300秒。请立即用于 SSH 执行。"
    })

@app.route("/api/credential/status")
def api_credential_status():
    """查询凭据管理器状态（不泄露凭据内容）"""
    return jsonify({
        "active_count": credential_manager.active_count,
        "ttl_seconds": 300,
        "mode": "加密存储",
    })

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
    """生成配置文件 — 支持三种模式

    POST JSON:
      mode: "official" | "simple" (default) | "engine"
      official: 生成 FusionInsight 标准格式 preinstall.ini + host.ini + install_oms.ini
      simple:   旧版简单生成（向后兼容）
      engine:   嘉兴引擎完整 LLD 配置
    """
    data = request.get_json() or {}
    mode = data.get("mode", "simple")
    use_engine = data.get("use_engine", False)

    if mode == "official":
        from core.config_generator import (
            ClusterConfig, NodeSpec, OMSConfig,
            generate_preinstall_ini, generate_host_inis,
            generate_install_oms_ini, generate_cluster_install_template
        )
        oms = OMSConfig(
            oms_ip1=data.get("oms_ip1", ""),
            oms_ip2=data.get("oms_ip2", ""),
            oms_float_ip=data.get("oms_float_ip", ""),
            ws_float_ip=data.get("ws_float_ip", ""),
            gateway=data.get("gateway", ""),
        )
        nodes_raw = data.get("nodes", [])
        nodes = []
        for i, n in enumerate(nodes_raw):
            nodes.append(NodeSpec(
                hostname=n.get("hostname", f"node{i+1}"),
                mgmt_ip=n.get("mgmt_ip", ""),
                biz_ip=n.get("biz_ip", n.get("mgmt_ip", "")),
            ))
        cfg = ClusterConfig(
            cluster_name=data.get("cluster_name", "dws_cluster"),
            oms=oms, nodes=nodes,
            chip_type=data.get("chip_type", "aarch64"),
            os_type=data.get("os_type", "kylin-V10-SP2"),
            os_user=data.get("os_user", "root"),
        )
        ini = generate_preinstall_ini(cfg)
        host_inis = generate_host_inis(cfg.nodes)
        oms_ini = generate_install_oms_ini(cfg, is_primary=True)
        cluster_tpl = generate_cluster_install_template(cfg)
        result = {
            "content": ini,
            "all_templates": {
                "preinstall.ini": ini,
                "install_oms.ini": oms_ini,
                "cluster_install_template.txt": cluster_tpl,
            }
        }
        for name, content in host_inis.items():
            result["all_templates"][name] = content
        return jsonify(result)

    # 参数校验（非 engine 模式）
    if not use_engine:
        validator = get_validator()
        errors = validator.validate(data)
        if errors:
            return jsonify({
                "error": "配置参数校验失败",
                "errors": [e.to_dict() for e in errors],
            }), 400

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

    # 构建物理节点分组（按物理机器分组，合设角色归入同一节点）
    nodes = result.get("nodes", [])
    physical_map = {}
    for n in nodes:
        co_host = n.get("co_host")
        if co_host:
            # 这是合设的虚拟角色，找到物理节点
            if co_host in physical_map:
                physical_map[co_host]["virtual_roles"].append({
                    "id": n["id"], "role": n["role"]
                })
                physical_map[co_host]["roles_raw"].append(n["role"])
        else:
            # 物理节点
            key = n["id"]
            # 使用 n["roles"] 完整角色列表（n["role"] 只是主角色）
            full_roles = n.get("roles", [n["role"]])
            physical_map[key] = {
                "id": key,
                "hostname": n.get("hostname", key),
                "mgmt_ip": n.get("mgmt_ip", ""),
                "biz_ip": n.get("biz_ip", ""),
                "is_primary": n.get("is_primary", False),
                "is_control": "OM" in full_roles,
                "roles_raw": list(full_roles),
                "virtual_roles": [],
            }

    physical_nodes = []
    for key, pn in physical_map.items():
        pn["roles"] = sorted(set(pn["roles_raw"]))
        pn["role_count"] = len(pn["roles"])
        pn["role_labels"] = [ROLE_META.get(r, {}).get("label", r) for r in pn["roles"]]
        pn["role_colors"] = [ROLE_META.get(r, {}).get("color", "#666") for r in pn["roles"]]
        physical_nodes.append(pn)

    # 按管控节点→数据节点排序
    physical_nodes.sort(key=lambda x: (0 if x["is_control"] else 1, x["hostname"]))

    return jsonify({
        **result,
        "physical_nodes": physical_nodes,
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
# 交付报告
# ================================================================
@app.route("/deliverables")
def deliverables_page():
    """交付物生成页面"""
    session = get_or_create_session()
    metadata = session.config.get("delivery", {})
    return render_template("dws_deliverables.html",
                           data=session.to_dict(),
                           metadata=metadata)

@app.route("/api/report/generate", methods=["POST"])
def api_report_generate():
    """生成全部交付物并返回下载链接"""
    data = request.get_json() or {}
    session = get_or_create_session()
    cfg = session.config
    delivery = cfg.get("delivery", {})

    md = DeliveryMetadata(
        project_name=data.get("project_name", delivery.get("project_name", "")),
        customer=data.get("customer", delivery.get("customer", "")),
        site=data.get("site", delivery.get("site", "")),
        deploy_engineer=data.get("engineer", delivery.get("deploy_engineer", "")),
        deploy_date=data.get("date", datetime.now().strftime("%Y-%m-%d")),
        acceptance_criteria=data.get("acceptance", delivery.get("acceptance_criteria", "")),
    )

    # 保存到 session
    cfg.setdefault("delivery", {}).update({
        "project_name": md.project_name,
        "customer": md.customer,
        "site": md.site,
        "deploy_engineer": md.deploy_engineer,
        "deploy_date": md.deploy_date,
        "acceptance_criteria": md.acceptance_criteria,
    })

    session.generate_templates()

    # 构建 ReportContext
    context = ReportContext(
        session_id=session.session_id,
        cluster_name=cfg.get("cluster_name", ""),
        environment=cfg.get("environment", "UAT"),
        metadata=md,
        precheck_results=[],       # 实际部署时从 SSH 执行结果获取
        precheck_items=[],          # 从 PRECHECK_ITEMS 获取
        audit_log=session.audit_log,
        config_templates=session.templates,
        verify_results=[],          # 实际部署时从验证 API 获取
        phases=session.phases,
        config=cfg,
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 从 core/precheck_engine 导入
    from core.precheck_engine import PRECHECK_ITEMS
    context.precheck_items = PRECHECK_ITEMS

    from core.verifier import VERIFY_ITEMS
    context.verify_results = [
        {"item_id": v["id"], "name": v["name"], "status": "pass", "detail": v["description"]}
        for v in VERIFY_ITEMS
    ]

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "deliverables")
    result = generate_deliverable_bundle(context, output_dir)

    return jsonify({
        "ok": True,
        "session_id": result["session_id"],
        "bundle_name": result["bundle_name"],
        "files": result["files"],
        "size_bytes": result["size_bytes"],
        "download_url": f"/api/report/download/{result['session_id']}",
    })

@app.route("/api/report/download/<session_id>")
def api_report_download(session_id):
    """下载交付物压缩包"""
    bundle_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "deliverables", session_id, f"dws_deliverables_{session_id}.tar.gz"
    )
    alt_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "deliverables", f"dws_deliverables_{session_id}.tar.gz"
    )
    if os.path.exists(bundle_path):
        return send_file(bundle_path, as_attachment=True,
                         download_name=f"dws_deliverables_{session_id}.tar.gz")
    if os.path.exists(alt_path):
        return send_file(alt_path, as_attachment=True,
                         download_name=f"dws_deliverables_{session_id}.tar.gz")
    return jsonify({"error": "交付物未找到，请先生成"}), 404

# ================================================================
# 全局上下文（注入当前环境等变量到模板）
# ================================================================
@app.context_processor
def inject_globals():
    try:
        session = get_or_create_session()
        return {
            "current_env": session.config.get("environment", "UAT"),
        }
    except Exception:
        return {"current_env": "UAT"}

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


# ================================================================
# 会话管理（B-2: 数据持久化）
# ================================================================
@app.route("/sessions")
def sessions_page():
    """会话管理页面"""
    sessions = session_store.list_sessions(limit=20)
    return render_template("dws_sessions.html",
                           sessions=sessions,
                           current_session=_last_session_id,
                           total_count=session_store.session_count)


@app.route("/api/sessions")
def api_sessions():
    """获取会话列表"""
    sessions = session_store.list_sessions(limit=20)
    return jsonify({
        "sessions": sessions,
        "current": _last_session_id,
        "total": session_store.session_count,
    })


@app.route("/api/sessions/load/<session_id>")
def api_session_load(session_id):
    """加载历史会话（恢复配置到当前会话）"""
    data = session_store.load(session_id)
    if not data:
        return jsonify({"error": "会话不存在"}), 404
    try:
        session = get_or_create_session()
        env = data.get("environment", "UAT")
        from engine.core_engine import switch_environment, _init_phases
        cfg = switch_environment(env)
        if cfg:
            session.config = cfg
            session.phases = _init_phases(cfg)
            session.generate_templates()
        if "audit_log" in data:
            session.audit_log = data["audit_log"]
        config_data = data.get("config", {})
        if "delivery" in config_data:
            session.config["delivery"] = config_data["delivery"]
        _save_current_session()
        return jsonify({"ok": True, "session_id": session_id, "environment": env})
    except Exception as e:
        return jsonify({"error": f"恢复失败: {e}"}), 500


@app.route("/api/sessions/delete/<session_id>", methods=["POST"])
def api_session_delete(session_id):
    """删除历史会话"""
    ok = session_store.delete(session_id)
    return jsonify({"ok": ok})


# 每次请求后自动保存会话
@app.after_request
def _auto_save_session(response):
    if response.status_code < 400:
        try:
            _save_current_session()
        except Exception:
            pass
    return response


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
