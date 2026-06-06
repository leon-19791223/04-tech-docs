"""
DWS FusionInsight 配置生成器（官方格式 v2）

生成华为 FusionInsight SetupTool 标准格式的配置文件：
  1. preinstall.ini     — FusionInsight 预安装配置（g_ 键值对格式）
  2. host0/1/2.ini      — 各节点分区配置
  3. install_oms.ini    — OMS Manager 安装配置

官方格式参考: 嘉兴银行 DWS 部署 V2.0 文档 + GaussDB 9.1.0 配置规划工具
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class NodeSpec:
    """节点规格"""
    hostname: str = ""
    mgmt_ip: str = ""
    biz_ip: str = ""
    cpu_cores: int = 96
    memory_gb: int = 512
    disk_count: int = 6
    min_disk_gb: int = 6440
    roles: list = field(default_factory=lambda: ["MN&CN&DN"])
    # 分区配置
    root_gb: int = 20
    tmp_gb: int = 10
    var_gb: int = 10
    var_log_gb: int = 130
    bigdata_gb: int = 330
    opt_gb: int = 392
    meta_disk_count: int = 1
    meta_mounts: list = field(default_factory=lambda: ["/srv/BigData/dbdata_om", "/srv/BigData/LocalBackup"])
    data_disk_count: int = 4


@dataclass
class OMSConfig:
    """OMS Manager 配置"""
    oms_ip1: str = ""
    oms_ip2: str = ""
    oms_float_ip: str = ""
    ws_float_ip: str = ""
    subnet_mask: str = "255.255.255.0"
    gateway: str = ""
    bond_interface: str = "bond4"


@dataclass
class ClusterConfig:
    """集群配置（完整参数）"""
    # 基础信息
    cluster_name: str = "dws_cluster"
    product: str = "GaussDB_DWS"
    version: str = "GaussDB 9.1.0"
    install_mode: str = "新集群安装"
    auth_mode: str = "普通模式"
    install_path: str = "/opt/huawei"
    data_path: str = "/srv/BigData"

    # 系统
    os_user: str = "root"
    omm_password: str = "Huawei12#$"
    ntp_server: str = ""
    timezone: str = "Asia/Shanghai"
    chip_type: str = "aarch64"
    os_type: str = "kylin-V10-SP2"
    iso_mount: str = "/media"
    host_arch: str = "aarch64"

    # 网络
    bond_mgmt_name: str = "bond1"
    bond_biz_name: str = "bond4"
    bond_mgmt_mode: str = "1"
    bond_biz_mode: str = "4"
    mtu: int = 1500
    dns_servers: list = field(default_factory=list)

    # 节点
    oms: OMSConfig = field(default_factory=OMSConfig)
    nodes: list = field(default_factory=lambda: [NodeSpec(), NodeSpec(), NodeSpec()])

    # GaussDB
    db_port: int = 25308
    pooler_port: int = 25309
    cm_port: int = 25310
    gtm_port: int = 25311
    max_connections: int = 5000
    cstore_buffers_coord: str = "2GB"
    cstore_buffers_dn: str = "16GB"

    # 部署套餐
    deploy_plan: str = "套餐3：MN&CN&DN"  # 合设模式
    co_deploy: bool = True
    om_count: int = 2
    cn_count: int = 3
    dn_count: int = 3

    # 容量规划
    total_data_gb: int = 150000
    retention_days: int = 365
    daily_increment_gb: int = 1200
    compression_ratio: float = 1.093
    disk_threshold: float = 0.7

    # 安全
    selinux: str = "disabled"
    firewall: str = "disabled"
    swap: str = "disabled"
    thp: str = "disabled"
    numa_balancing: str = "disabled"
    ipv6: str = "disabled"

    # 交付
    project_name: str = ""
    customer: str = ""
    site: str = ""
    deploy_engineer: str = ""


# ═══════════════════════════════════════════════════════════════
# 生成器
# ═══════════════════════════════════════════════════════════════

def generate_preinstall_ini(cfg: ClusterConfig) -> str:
    """生成 FusionInsight 标准 preinstall.ini（g_ 键值对格式）"""
    ips = [n.mgmt_ip for n in cfg.nodes if n.mgmt_ip]
    hosts_conf = ";".join([f"{n.mgmt_ip}#{n.mgmt_ip}#{n.hostname}" for n in cfg.nodes if n.mgmt_ip])
    parted_conf = ";".join([f"{n.mgmt_ip}#host{nodes_index}.ini" for nodes_index, n in enumerate(cfg.nodes) if n.mgmt_ip])

    lines = []
    if cfg.oms.oms_ip1:
        lines.append(f"oms_ip1={cfg.oms.oms_ip1}")
    if cfg.oms.oms_ip2:
        lines.append(f"oms_ip2={cfg.oms.oms_ip2}")
    lines.append(f"g_hosts=\"{','.join(ips)}\"")
    lines.append(f"g_user_name=\"{cfg.os_user}\"")
    lines.append(f"g_port=22")
    lines.append(f"g_parted={3 if cfg.co_deploy else 2}")
    lines.append(f"g_parted_conf=\"{parted_conf}\"")
    lines.append(f"g_add_pkg=1")
    lines.append(f"g_pkgs_dir=\"{cfg.os_type}:/media\"")
    lines.append(f"g_log_file=\"/tmp/fi-preinstall.log\"")
    lines.append(f"g_debug=0")
    lines.append(f"g_hostname_conf=\"{hosts_conf}\"")
    lines.append(f"g_swap_off=1")
    lines.append(f"g_platform=\"{cfg.chip_type}\"")
    lines.append(f"g_core_dump=1")
    lines.append(f"g_core_dump_dir=\"/var/log/core\"")
    return "\n".join(lines)


def generate_host_ini(node: NodeSpec, index: int) -> str:
    """生成单节点分区配置 host{N}.ini"""
    meta_str = ";".join(node.meta_mounts) if node.meta_disk_count > 0 else ""
    lines = [
        f"[host_{index}]",
        f"  HostName = {node.mgmt_ip}",
        f"  OSDisk =",
        f"    root = {node.root_gb}GB",
        f"    tmp = {node.tmp_gb}GB",
        f"    var = {node.var_gb}GB",
        f"    \"var/log\" = {node.var_log_gb}GB",
        f"    \"srv/BigData\" = {node.bigdata_gb}GB",
        f"    opt = {node.opt_gb}GB",
        f"  MetaDataDisk = ",
        f"    Count = {node.meta_disk_count}",
    ]
    if node.meta_disk_count > 0:
        lines.append(f"    MountPoints = {meta_str}")
    lines.append(f"  DataDisk =")
    lines.append(f"    Count = {node.data_disk_count}")
    return "\n".join(lines)


def generate_host_inis(nodes: list) -> dict:
    """生成全部节点的 host.ini 配置"""
    return {f"host{i}.ini": generate_host_ini(n, i) for i, n in enumerate(nodes) if n.mgmt_ip}


def generate_install_oms_ini(cfg: ClusterConfig, is_primary: bool = True) -> str:
    """生成 OMS Manager 安装配置"""
    oms = cfg.oms
    if is_primary:
        local_ip = oms.oms_ip1
        peer_ip = oms.oms_ip2
        node_name = "主管理节点"
    else:
        local_ip = oms.oms_ip2
        peer_ip = oms.oms_ip1
        node_name = "备管理节点"
    return f"""# OMS Manager 安装配置 ({node_name})
# 生成时间: {{生成时间}}

[OMSServer]
local_ip1 = {local_ip}
peer_ip1 = {peer_ip}
oms_float_ip = {oms.oms_float_ip}
ws_float_ip = {oms.ws_float_ip}
subnet_mask = {oms.subnet_mask}
gateway = {oms.gateway}
bond_interface = {oms.bond_interface}
install_path = {cfg.install_path}

[Cluster]
cluster_name = {cfg.cluster_name}
data_path = {cfg.data_path}
chip_type = {cfg.chip_type}
node_count = {len(cfg.nodes)}

[Auth]
admin_password = Admin@123
"""


def generate_cluster_install_template(cfg: ClusterConfig) -> str:
    """生成 Web GUI 集群安装模板 XML 概要"""
    lines = [
        f"<!-- GaussDB(DWS) 集群安装模板 -->",
        f"<!-- 集群名称: {cfg.cluster_name} -->",
        f"<!-- 产品: {cfg.product} {cfg.version} -->",
        f"<!-- 安装模式: {cfg.install_mode} -->",
        f"<!-- 认证模式: {cfg.auth_mode} -->",
        f"<!-- 节点数: {len(cfg.nodes)} -->",
        f"<!-- 部署套餐: {cfg.deploy_plan} -->",
        f"<!-- CN数: {cfg.cn_count}, DN数: {cfg.dn_count} -->",
        f"<!-- 使用方法: 登录 Manager → 创建集群 → 模板安装 → 上传此文件 -->",
        "",
        f"使用华为配置规划工具(XLSM)生成完整 XML 模板。",
        f"临时方案: 登录 Manager Web GUI → 手动创建集群。",
    ]
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# 兼容旧接口
# ═══════════════════════════════════════════════════════════════

@dataclass
class DWSConfig:
    """兼容旧版 DWSConfig（保持向后兼容）"""
    cluster_name: str = "dws_cluster"
    master_node1_ip: str = ""
    master_node2_ip: str = ""
    data_node_ips: str = ""
    cn_num: int = 3
    dn_num: int = 3
    install_path: str = "/opt/huawei/Bigdata"
    data_path: str = "/srv/BigData/mppdb"
    db_user: str = "omm"
    db_port: int = 40080
    timezone: str = "Asia/Shanghai"
    python_version: str = "3.8.5"


TEMPLATES = {
    "standard": """# DWS FusionInsight 安装配置 (自动生成，旧版格式)
# 注意: 推荐使用新版 generate_preinstall_ini()
"""
}


def _legacy_generate(cfg: DWSConfig) -> str:
    """旧版生成器（保持向后兼容）"""
    from datetime import datetime
    text = TEMPLATES["standard"]
    text = text.replace("{{time}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    return text
