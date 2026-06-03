"""
DWS FusionInsight 配置生成器
通过Web表单输入自动生成 preinstall.ini
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DWSConfig:
    """DWS集群配置"""
    # 集群
    cluster_name: str = "dws_cluster"
    master_node1_ip: str = ""
    master_node2_ip: str = ""
    data_node_ips: str = ""  # 逗号分隔

    # 实例
    cn_num: int = 3
    dn_num: int = 3

    # 安装
    install_path: str = "/opt/huawei/Bigdata"
    data_path: str = "/srv/BigData/mppdb"
    db_user: str = "omm"
    db_port: int = 40080

    # OS
    timezone: str = "Asia/Shanghai"
    python_version: str = "3.8.5"


TEMPLATES = {
    "standard": """# DWS FusionInsight 安装配置 (自动生成)
# 生成时间: {{time}}

[CLUSTER]
cluster_name = {{cfg.cluster_name}}
master_node1_ip = {{cfg.master_node1_ip}}
{% if cfg.master_node2_ip %}master_node2_ip = {{cfg.master_node2_ip}}{% endif %}
data_node_ips = {{cfg.data_node_ips}}

[INSTALL]
install_path = {{cfg.install_path}}
data_path = {{cfg.data_path}}
db_user = {{cfg.db_user}}
db_port = {{cfg.db_port}}
cn_num = {{cfg.cn_num}}
dn_num = {{cfg.dn_num}}

[OS]
timezone = {{cfg.timezone}}
python_version = {{cfg.python_version}}
locale = en_US.UTF-8
kernel_params =
  net.ipv4.ip_local_port_range = 26000 65535
  net.ipv4.tcp_tw_reuse = 1
  net.core.somaxconn = 1024
  vm.watermark_scale_factor = 100
  kernel.numa_balancing = 0
"""
}


def generate_preinstall_ini(cfg: DWSConfig) -> str:
    """生成 preinstall.ini 内容"""
    from datetime import datetime
    text = TEMPLATES["standard"]
    text = text.replace("{{time}}", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    text = text.replace("{{cfg.cluster_name}}", cfg.cluster_name)
    text = text.replace("{{cfg.master_node1_ip}}", cfg.master_node1_ip)
    text = text.replace("{{cfg.master_node2_ip}}", cfg.master_node2_ip or "")
    text = text.replace("{{cfg.data_node_ips}}", cfg.data_node_ips)
    text = text.replace("{{cfg.install_path}}", cfg.install_path)
    text = text.replace("{{cfg.data_path}}", cfg.data_path)
    text = text.replace("{{cfg.db_user}}", cfg.db_user)
    text = text.replace("{{cfg.db_port}}", str(cfg.db_port))
    text = text.replace("{{cfg.cn_num}}", str(cfg.cn_num))
    text = text.replace("{{cfg.dn_num}}", str(cfg.dn_num))
    text = text.replace("{{cfg.timezone}}", cfg.timezone)
    text = text.replace("{{cfg.python_version}}", cfg.python_version)
    # Clean empty lines
    lines = [l for l in text.split('\n') if not l.strip().startswith('{%') and not l.strip().endswith('%}')]
    return '\n'.join(lines)
