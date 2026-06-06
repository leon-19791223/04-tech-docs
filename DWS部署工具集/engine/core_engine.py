"""DWS 部署交互助手 — 核心引擎"""
import json
import time
import uuid
from datetime import datetime
from pathlib import Path

# ─── 8 大部署阶段定义 ───
def build_phases(config=None):
    """根据环境配置动态生成 8 大部署阶段，确保每个环境的 IP/主机名正确同步"""
    if config is None:
        config = DEFAULT_CONFIG

    nodes = config.get("nodes", [])
    cluster = config.get("cluster_name", "uatdws")

    # 动态生成 /etc/hosts 内容
    hosts_lines = ["cat >> /etc/hosts << 'EOF'"]
    for n in nodes:
        hosts_lines.append(f"{n['mgmt_ip']}  {n['hostname']}")
    hosts_lines.append("EOF")
    hosts_cmd = "\n".join(hosts_lines)

    # 节点1 作为 NTP 服务器
    ntp_ip = nodes[0]["mgmt_ip"] if nodes else "10.134.21.190"
    # 带宽测试目标 IP
    bw_test_ip = nodes[1]["mgmt_ip"] if len(nodes) > 1 else (nodes[0]["mgmt_ip"] if nodes else "10.134.21.191")
    # 节点1 主机名
    first_hostname = nodes[0]["hostname"] if nodes else "uatdws0001"
    # 主机列表
    hostlist_items = [n["hostname"] for n in nodes]
    hostlist_cmd = "echo -e '" + "\\n".join(hostlist_items) + "' > /opt/hostlist"

    return [
        {
            "id": 1, "name": "环境准备",
            "icon": "🔧",
            "steps": [
                {"id": "hosts", "name": "配置 /etc/hosts", "cmd": hosts_cmd, "desc": f"写入所有节点的主机名映射（{cluster} 环境）"},
                {"id": "hostname", "name": "设置主机名", "cmd": f"hostnamectl set-hostname {first_hostname}", "desc": f"设置当前节点主机名，{len(nodes)}节点分别执行"},
                {"id": "python", "name": "验证 Python3.8.5", "cmd": "python3 --version && python3 -c 'import sqlite3, ssl'", "desc": "确认 Python3.8.5 及关键模块可用"},
                {"id": "yum", "name": "挂载 ISO 配置 yum 源", "cmd": "mount /opt/Kylin-V10-SP2-aarch64.iso /mnt/iso && cp /mnt/iso/media.repo /etc/yum.repos.d/kylin.repo && sed -i 's|baseurl=.*|baseurl=file:///mnt/iso|' /etc/yum.repos.d/kylin.repo", "desc": "挂载 KylinOS ISO 并配置本地 yum 源"},
                {"id": "chrony", "name": "配置 chrony/NTP", "cmd": f"sed -i 's/pool.*/server {ntp_ip} iburst/' /etc/chrony.conf && systemctl restart chronyd && chronyc sources", "desc": f"以节点1（{ntp_ip}）为 NTP 服务器，其余节点指向节点1"},
            ]
        },
        {
            "id": 2, "name": "OS 调优",
            "icon": "⚙️",
            "steps": [
                {"id": "disable_audit", "name": "关闭 audit 服务", "cmd": "systemctl stop auditd && systemctl disable auditd", "desc": "关闭审计服务以提升 I/O 性能"},
                {"id": "disable_firewall", "name": "关闭防火墙 (firewalld+iptables)", "cmd": "systemctl stop firewalld && systemctl disable firewalld && systemctl stop iptables && systemctl disable iptables", "desc": "实际部署需同时关闭 firewalld 和 iptables"},
                {"id": "disable_thp", "name": "关闭透明大页", "cmd": "cp /etc/default/grub /etc/default/grub.bak && cp /boot/efi/EFI/kylin/grub.cfg /boot/efi/EFI/kylin/grub.cfg.bak && sed -i '/GRUB_CMDLINE_LINUX/s/\"$/ transparent_hugepage=never\"/' /etc/default/grub && grub2-mkconfig -o /boot/efi/EFI/kylin/grub.cfg", "desc": "备份grub → 追加 transparent_hugepage=never → 重新生成grub.cfg（DWS部署V2.0 标准流程）"},
                {"id": "watermark", "name": "OS 内存水位线（POC必需）", "cmd": "cp /etc/sysctl.conf /etc/sysctl.conf.bak && sed -i 's/vm.watermark_scale_factor.*=.*/vm.watermark_scale_factor = 100/' /etc/sysctl.conf && sysctl -p", "desc": "DWS部署V2.0：vm.watermark_scale_factor=100，POC性能关键参数"},
                {"id": "numa_config", "name": "配置 NUMA 参数", "cmd": "echo 'kernel.numa_balancing = 0' >> /etc/sysctl.conf && sysctl -p", "desc": "实际部署使用 kernel.numa_balancing=0（非 grubby numa=on）"},
                {"id": "oom_config", "name": "配置 OOM 策略", "cmd": "echo 0 > /proc/sys/vm/panic_on_oom && echo 0 > /proc/sys/vm/oom_kill_allocating_task && echo 'vm.overcommit_memory=0' >> /etc/sysctl.conf && echo 'vm.min_free_kbytes=262144' >> /etc/sysctl.conf && sysctl -p", "desc": "官方验收规范：panic_on_oom=0, oom_kill_allocating_task=0，防止部署被 OOM Killer 终结"},
                {"id": "io_scheduler", "name": "设置 IO 调度器", "cmd": "echo 'elevator=deadline' | grubby --update-kernel=ALL --args", "desc": "SSD 环境推荐 deadline 调度器"},
                {"id": "selinux", "name": "关闭 SELinux", "cmd": "sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config && setenforce 0", "desc": "关闭 SELinux 避免权限干扰"},
                {"id": "swap_ipv6", "name": "关闭 swap 和 IPv6", "cmd": "swapoff -a && sed -i '/swap/s/^/#/' /etc/fstab && echo 'net.ipv6.conf.all.disable_ipv6=1' >> /etc/sysctl.conf", "desc": "关闭 swap 和 IPv6"},
            ]
        },
        {
            "id": 3, "name": "硬件验证",
            "icon": "🖥️",
            "steps": [
                {"id": "nic_check", "name": "Hi1822 网卡检测", "cmd": "lspci | grep Hi1822 && ethtool -i eth0", "desc": "确认华为 Hi1822 智能网卡正常识别"},
                {"id": "raid_check", "name": "RAID 配置验证", "cmd": "storcli64 /c0 show && storcli64 /c0 /vall show | grep -E 'RAID|State'", "desc": "验证 RAID 卡及虚拟磁盘状态"},
                {"id": "ssd_detect", "name": "SSD/HDD 识别检测", "cmd": "for dev in sdb sdc sdd; do echo \"=== /dev/$dev ===\"; smartctl -i /dev/$dev 2>/dev/null | grep -E 'Model|Rotation|SATA'; done", "desc": "确认数据盘型号及类型（SSD/HDD）"},
                {"id": "bios_check", "name": "BIOS 配置检查（DWS 官方要求）", "cmd": "# 检查以下BIOS配置项:\n# 1. Power Policy=Performance\n# 2. Die Interleaving=Disable\n# 3. Channel Interleaving 3Way=Disable\n# 4. NUMA=Enable\n# 5. One Numa Per Socket=Enable\n# 6. Support Smmu=Disabled\n# 7. Memory Test=Enable\necho 'BIOS检查完成：请手动验证以上7项配置（DWS验收规范要求）'", "desc": "华为 DWS 官方验收规范：7项BIOS配置检查，确保服务器以最佳性能运行"},
                {"id": "fio_test", "name": "FIO 磁盘压测", "cmd": "fio --name=test --iodepth=16 --rw=randwrite --bs=64k --size=10G --numjobs=4 --runtime=60 --group_reporting --filename=/dev/sdb", "desc": "随机写压测验收磁盘基准性能"},
                {"id": "dd_io", "name": "dd I/O 基准测试", "cmd": "dd if=/dev/zero of=/data/test bs=1M count=10240 oflag=direct 2>&1 | tail -1", "desc": "连续写 10GB 验证磁盘写带宽"},
            ]
        },
        {
            "id": 4, "name": "磁盘规划",
            "icon": "💾",
            "steps": [
                {"id": "os_part", "name": "OS 盘分区规划（官方验收规范）", "cmd": "# DWS 验收规范 — OS盘分区 (960GB/RAID1):\n# / = 20GB, /tmp = 30GB, /var = 30GB,\n# /var/log = 400GB, /srv/BigData = 60GB,\n# /opt = 420GB (剩余全部)\necho 'OS分区标准: /=20G /tmp=30G /var=30G /var/log=400G /srv/BigData=60G /opt=420G'", "desc": "华为 DWS 验收规范：OS盘RAID1，6个标准分区，/opt 容量≥300GB"},
                {"id": "parted", "name": "数据盘 parted 分区", "cmd": "parted -s /dev/sdb mklabel gpt && parted -s /dev/sdb mkpart primary 0% 100%", "desc": "创建 GPT 分区表并划分全盘分区"},
                {"id": "mkfs", "name": "mkfs.xfs 格式化", "cmd": "mkfs.xfs -f -n ftype=1 -L data1 /dev/sdb1", "desc": "格式化为 XFS（ftype=1 为 Docker overlay2 必需）"},
                {"id": "uuid", "name": "获取 UUID 并配置 fstab", "cmd": "UUID=$(blkid -s UUID -o value /dev/sdb1) && echo \"UUID=$UUID /srv/BigData/data1 xfs defaults,noatime,nodiratime 0 0\" >> /etc/fstab", "desc": "写入 fstab 确保重启后自动挂载（挂载点为 /srv/BigData/data1）"},
                {"id": "mount_data", "name": "挂载数据盘", "cmd": "mkdir -p /srv/BigData/data1 && mount -a && df -h /srv/BigData", "desc": "创建挂载点并验证挂载成功"},
            ]
        },
        {
            "id": 5, "name": "网络验证",
            "icon": "🌐",
            "steps": [
                {"id": "check_net", "name": "网络连通性检查", "cmd": "check_net --hosts /opt/FusionInsight_SetupTool/conf/host.ini", "desc": "FusionInsight 自带网络检查工具"},
                {"id": "speed_test", "name": "网卡速率测试", "cmd": "ethtool eth0 | grep Speed && ethtool eth1 | grep Speed", "desc": "确认业务网卡速率≥25Gbps"},
                {"id": "bandwidth_test", "name": "节点间带宽测试", "cmd": f"sar -n DEV 1 10 && gsar --send {bw_test_ip} --recv {bw_test_ip} --port 12345", "desc": f"节点间实测带宽应 >800MB/s（测试目标：{bw_test_ip}）"},
            ]
        },
        {
            "id": 6, "name": "软件部署",
            "icon": "📦",
            "steps": [
                {"id": "unzip_gaussdb", "name": "解压 GaussDB 软件包", "cmd": "unzip -o /opt/GaussDB_MPPDB_9.1.0.zip -d /opt/ && chmod +x /opt/GaussDB_MPPDB_9.1.0/*.run", "desc": "解压 GaussDB MPPDB 安装包到 /opt"},
                {"id": "unzip_fi", "name": "解压 FusionInsight 工具包", "cmd": "tar zxf /opt/FusionInsight_Manager.tar.gz -C /opt/ && tar zxf /opt/FusionInsight_SetupTool.tar.gz -C /opt/", "desc": "解压 FusionInsight Manager 和 SetupTool"},
                {"id": "gen_hostlist", "name": "生成主机列表文件", "cmd": hostlist_cmd, "desc": f"生成节点主机名列表（{cluster} 环境 {len(nodes)}节点），供后续 gs_* 工具使用"},
                {"id": "copy_packages", "name": "分发软件包到所有节点", "cmd": "for host in $(cat /opt/hostlist); do scp -r /opt/GaussDB_MPPDB_9.1.0 $host:/opt/; done", "desc": "将 GaussDB 和依赖包分发到集群所有节点"},
            ]
        },
        {
            "id": 7, "name": "预检查",
            "icon": "🔍",
            "steps": [
                {"id": "preinstall_ini", "name": "生成 preinstall.ini", "cmd": "cd /opt/FusionInsight_SetupTool && ./setuptool.sh preinstall -f /opt/preinstall.ini", "desc": "使用配置中心生成的 preinstall.ini 执行预安装配置"},
                {"id": "gs_precheck", "name": "GaussDB 预检查", "cmd": "cd /opt/FusionInsight_SetupTool && ./setuptool.sh precheck -f /opt/preinstall.ini", "desc": "执行 FusionInsight 预检查，验证所有前置条件"},
                {"id": "gs_checkos", "name": "操作系统兼容性检查", "cmd": "gs_checkos -i A -h $(cat /opt/hostlist) --detail", "desc": "GaussDB 操作系统兼容性全面检查（gs_checkos -i A）"},
                {"id": "rpm_install", "name": "安装依赖 RPM 包", "cmd": "cd /opt/FusionInsight_SetupTool/rpm && rpm -ivh *.rpm --nodeps 2>&1 | grep -E 'installing|already'", "desc": "安装 GaussDB 必需的 OS 依赖包"},
            ]
        },
        {
            "id": 8, "name": "部署 OMS",
            "icon": "🚀",
            "steps": [
                {"id": "install_oms", "name": "安装 OMS 服务", "cmd": "cd /opt/FusionInsight_Manager && ./install.sh -f /opt/preinstall.ini", "desc": "安装 FusionInsight Manager OMS 管理服务"},
                {"id": "verify_manager", "name": "验证 Manager 启动", "cmd": "source /opt/huawei/Bigdata/mppdb/.mppdbgs_profile && gs_om -t status --detail", "desc": "确认 OMS 与 GaussDB 实例均处于 Normal 状态"},
                {"id": "gs_checkperf", "name": "集群性能基线", "cmd": "gs_checkperf -h $(cat /opt/hostlist)", "desc": "集群磁盘 I/O 和网络性能基线测试"},
                {"id": "numa_bind", "name": "集群 NUMA 绑核优化", "cmd": "source /opt/huawei/Bigdata/mppdb/.mppdbgs_profile && gs_guc reload -Z coordinator -Z datanode -N all -I all -c \"enable_numa_bind=on\"", "desc": "DWS部署V2.0 标准：启用NUMA绑核，提升MPP查询性能"},
                {"id": "create_db", "name": "创建业务数据库", "cmd": "gsql -d postgres -p 25308 -c \"CREATE DATABASE dwsdb ENCODING 'UTF8' LC_COLLATE='zh_CN.UTF-8'\"", "desc": "创建业务数据库，完成部署验收"},
                {"id": "export_report", "name": "导出部署报告", "cmd": "python3 dws_assistant.py --export-report --format html && tar czf dws_deploy_$(date +%%Y%%m%%d).tar.gz audit_logs/ config_snapshot/ templates/", "desc": "导出完整部署审计报告并打包交付物"},
            ]
        },
    ]


# 向后兼容：保持 PHASES 全局变量（使用默认 UAT 配置）
# 注意: PHASES = build_phases() 放置在 DEFAULT_CONFIG 定义之后

# ─── 嘉兴银行实际环境配置 ───

# 各环境节点定义
_JX_ENV_NODES = {
    "DEV": {
        "cluster_name": "dwsdev",
        "mgmt_subnet": "10.134.91",
        "hostnames": ["dwsdev0001", "dwsdev0002", "dwsdev0003"],
        "cpu_cores": 96, "memory_gb": 512,
        "oms_ip": "10.134.91.203", "omweb_ip": "10.134.91.204", "lvs_ip": "10.134.91.205",
    },
    "SIT": {
        "cluster_name": "dwssit",
        "mgmt_subnet": "10.134.134",
        "hostnames": ["dwssit0001", "dwssit0002", "dwssit0003"],
        "cpu_cores": 96, "memory_gb": 512,
        "oms_ip": "10.134.134.203", "omweb_ip": "10.134.134.204", "lvs_ip": "10.134.134.205",
    },
    "UAT": {
        "cluster_name": "dwsuat",
        "mgmt_subnet": "10.134.21",
        "hostnames": ["dwsuat0001", "dwsuat0002", "dwsuat0003"],
        "cpu_cores": 96, "memory_gb": 512,
        "oms_ip": "10.134.21.202", "omweb_ip": "10.134.21.203", "lvs_ip": "10.134.21.204",
    },
    "PREPROD": {
        "cluster_name": "dws-preprod",
        "mgmt_subnet_a": "10.134.49", "mgmt_subnet_b": "10.134.50",
        "cpu_cores": 96, "memory_gb": 512, "control_mem_gb": 256, "control_cpu": 64,
        "oms_ip": "10.134.50.5", "omweb_ip": "10.134.49.12", "lvs_ip": "10.134.49.48",
    },
}

# 环境预设（含节点角色区分）
ENV_PRESETS = {
    "DEV": {
        "name": "DEV 开发环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.91.x · 鲲鹏920 96C/512GB · 24×4T HDD",
        "nodes": [
            {"hostname": "dwsdev0001", "roles": ["OM","CN","DN","GTM"], "mgmt_ip": "10.134.91.194", "cpu": 96, "mem": 512},
            {"hostname": "dwsdev0002", "roles": ["CN","DN"], "mgmt_ip": "10.134.91.195", "cpu": 96, "mem": 512},
            {"hostname": "dwsdev0003", "roles": ["CN","DN"], "mgmt_ip": "10.134.91.196", "cpu": 96, "mem": 512},
        ],
        "oms": {"ip": "10.134.91.203", "omweb": "10.134.91.204", "lvs": "10.134.91.205"},
        "co_deploy": True, "om_count": 2, "cn_count": 3, "dn_count": 3, "gtm_count": 2,
    },
    "SIT": {
        "name": "SIT 测试环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.134.x · 鲲鹏920 96C/512GB · 12×4T HDD",
        "nodes": [
            {"hostname": "dwssit0001", "roles": ["OM","CN","DN","GTM"], "mgmt_ip": "10.134.134.194", "cpu": 96, "mem": 512},
            {"hostname": "dwssit0002", "roles": ["CN","DN"], "mgmt_ip": "10.134.134.195", "cpu": 96, "mem": 512},
            {"hostname": "dwssit0003", "roles": ["CN","DN"], "mgmt_ip": "10.134.134.196", "cpu": 96, "mem": 512},
        ],
        "oms": {"ip": "10.134.134.203", "omweb": "10.134.134.204", "lvs": "10.134.134.205"},
        "co_deploy": True, "om_count": 2, "cn_count": 3, "dn_count": 3, "gtm_count": 2,
    },
    "UAT": {
        "name": "UAT 验收环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.21.x · 鲲鹏920 96C/509GB · 24×4T HDD",
        "nodes": [
            {"hostname": "dwsuat0001", "roles": ["OM","CN","DN","GTM"], "mgmt_ip": "10.134.21.190", "cpu": 96, "mem": 509},
            {"hostname": "dwsuat0002", "roles": ["CN","DN"], "mgmt_ip": "10.134.21.191", "cpu": 96, "mem": 509},
            {"hostname": "dwsuat0003", "roles": ["CN","DN"], "mgmt_ip": "10.134.21.192", "cpu": 96, "mem": 509},
        ],
        "oms": {"ip": "10.134.21.202", "omweb": "10.134.21.203", "lvs": "10.134.21.204"},
        "co_deploy": True, "om_count": 2, "cn_count": 3, "dn_count": 3, "gtm_count": 2,
    },
    "PREPROD": {
        "name": "生产环境 (2+5)",
        "desc": "2管控(64C/256G)+5数据(96C/512G) · 双平面 · 全闪存20×3.84T SSD",
        "nodes": [
            {"hostname": "dws-preprod-mn-01", "roles": ["OM"], "mgmt_ip": "10.134.49.10", "biz_ip": "10.134.50.10", "cpu": 64, "mem": 256},
            {"hostname": "dws-preprod-mn-02", "roles": ["OM","GTM"], "mgmt_ip": "10.134.49.11", "biz_ip": "10.134.50.11", "cpu": 64, "mem": 256},
            {"hostname": "dws-preprod-dn-01", "roles": ["CN","DN"], "mgmt_ip": "10.134.49.49", "biz_ip": "10.134.50.49", "cpu": 96, "mem": 512},
            {"hostname": "dws-preprod-dn-02", "roles": ["CN","DN"], "mgmt_ip": "10.134.49.50", "biz_ip": "10.134.50.50", "cpu": 96, "mem": 512},
            {"hostname": "dws-preprod-dn-03", "roles": ["DN"], "mgmt_ip": "10.134.49.51", "biz_ip": "10.134.50.51", "cpu": 96, "mem": 512},
            {"hostname": "dws-preprod-dn-04", "roles": ["DN"], "mgmt_ip": "10.134.49.52", "biz_ip": "10.134.50.52", "cpu": 96, "mem": 512},
            {"hostname": "dws-preprod-dn-05", "roles": ["DN"], "mgmt_ip": "10.134.49.53", "biz_ip": "10.134.50.53", "cpu": 96, "mem": 512},
        ],
        "co_deploy": False, "om_count": 2, "cn_count": 2, "dn_count": 5, "gtm_count": 2,
    },
}

def _build_nodes_from_preset(preset):
    """从环境预设构建节点列表（兼容原 DEFAULT_CONFIG 格式）"""
    nodes = []
    for n in preset["nodes"]:
        roles = n["roles"]
        nodes.append({
            "hostname": n["hostname"],
            "role": roles[0],           # 主角色
            "roles": roles,              # 全部角色
            "mgmt_ip": n["mgmt_ip"],
            "mgmt_netmask": "255.255.255.0",
            "mgmt_gateway": n["mgmt_ip"].rsplit(".",1)[0] + ".1",
            "biz_ip": n.get("biz_ip", n["mgmt_ip"]),
            "biz_netmask": "255.255.255.0",
            "biz_gateway": n.get("biz_ip", n["mgmt_ip"]).rsplit(".",1)[0] + ".1",
            "cpu_cores": n["cpu"],
            "memory_gb": n["mem"],
        })
    return nodes

# ─── 默认配置（嘉兴银行 UAT 环境）───
def _get_uat_config():
    preset = ENV_PRESETS["UAT"]
    env = _JX_ENV_NODES["UAT"]
    return {
        "environment": "UAT",
        "cluster_name": env["cluster_name"],
        "cluster_id": "DWS-UAT-001",
        "deploy_mode": "Single_Cluster",
        "az_mode": "Single_AZ",
        "nodes": _build_nodes_from_preset(preset),
        "float_ips": {
            "mgmt_float": "",
            "biz_float": "",
        },
        "os_version": "Kylin-V10-SP3",
        "os_arch": "ARM64",
        "kernel_version": "4.19.90-52.40.v2207.ky10.aarch64",
        "iso_path": "/opt/Kylin-V10-SP2-aarch64.iso",
        "python_version": "3.8.5",
        "network": {
            "mgmt_bond_name": "bond1",
            "mgmt_bond_mode": "1",
            "biz_bond_name": "bond4",
            "biz_bond_mode": "4",
            "mtu": 1500,
            "dns_servers": [env["mgmt_subnet"] + ".1"],
            "ntp_servers": [preset["nodes"][0]["mgmt_ip"]],
            "domain": "jxbank.local",
            "bandwidth_required_mbps": 800,
        },
        "storage": {
            "data_disks": ["/dev/sdb", "/dev/sdc", "/dev/sdd", "/dev/sde", "/dev/sdf", "/dev/sdg"],
            "disk_type": "HDD",
            "raid_level": "RAID5",
            "raid_controller": "SP686C",
            "partition_scheme": "GPT",
            "filesystem": "xfs",
            "xfs_ftype": 1,
            "disk_size_gb": 6440,
            "logical_disks": 6,
        },
        "gaussdb": {
            "version": "9.1.0",
            "package_path": "/opt/GaussDB_MPPDB_9.1.0.zip",
            "install_path": "/opt/huawei/Bigdata",
            "data_path": "/data/gaussdb/data",
            "wal_path": "/data/gaussdb/wal",
            "tmp_path": "/data/gaussdb/tmp",
            "port": 25308,
            "pooler_port": 25309,
            "cm_server_port": 25310,
            "gtm_port": 25311,
            "encoding": "UTF8",
            "locale": "zh_CN.UTF-8",
            "max_connections": 5000,
            "shared_buffers_gb": 64,
            "wal_level": "hot_standby",
            "max_wal_senders": 16,
            "coordinator_count": 3,
        },
        "fi_manager": {
            "version": "9.1.0",
            "install_path": "/opt/huawei/Bigdata/Manager",
            "admin_user": "admin",
            "admin_password": "Huawei12#$",
            "db_user": "omm",
            "db_password": "GaussDB_2024",
            "ssh_port": 22,
            "web_port": 20009,
        },
        "resource": {
            "memory_limit_percent": 80,
            "cpu_affinity": "0-95",
            "io_nice": 0,
            "oom_score_adj": -500,
            "cpu_cores_total": 96,
            "memory_total_gb": 509,
        },
        "security": {
            "selinux_mode": "disabled",
            "firewall": "disabled",
            "audit": "disabled",
            "ipv6": "disabled",
            "swap": "disabled",
            "thp": "disabled",
            "numa": "enabled",
        },
        # ── 容量规划（GaussDB 配置工具）──
        "capacity": {
            "total_data_gb": 150000,
            "retention_days": 365,
            "daily_increment_gb": 1200,
            "disks_per_node": 6,
            "memory_per_node_gb": 509,
            "cpu_per_node": 96,
            "disk_format_ratio": 1.093,
            "compression_threshold": 0.7,
        },
        # ── 部署参数（GaussDB 配置工具基本参数）──
        "deploy_params": {
            "product_name": "GaussDB_DWS",
            "install_mode": "new_cluster",
            "auth_mode": "normal",
            "deploy_mode": "normal",
            "system_user": "root",
            "software_path": "/opt/huawei",
            "data_path": "/srv/BigData",
            "topology": "topo2",
        },
        # ── OMS 浮动 IP（DWS 平台规划）──
        "oms_float_ips": {
            "oms_server": "10.134.21.202",
            "oms_web": "10.134.21.203",
            "lvs": "10.134.21.204",
        },
        "delivery": {
            "project_name": "嘉兴银行 DWS 数据仓库部署",
            "customer": "嘉兴银行",
            "site": "嘉兴银行数据中心",
            "deploy_engineer": "",
            "deploy_date": "",
            "acceptance_criteria": "TPC-H 10GB <300s，集群状态 Normal，无 ABRT 告警",
        },
    }

# 部署拓扑选项
DEPLOY_TOPOLOGIES = {
    "topo1": {"name": "拓扑1：管理+控制合设，数据分离", "mgmt_ctrl_together": True, "dn_separate": True},
    "topo2": {"name": "拓扑2：管理+控制+数据全分离", "mgmt_ctrl_together": False, "dn_separate": True},
    "topo3": {"name": "拓扑3：管理+控制+数据全合设", "mgmt_ctrl_together": True, "dn_separate": False},
    "topo4": {"name": "拓扑4：管理独立，控制+数据合设", "mgmt_ctrl_together": False, "dn_separate": False},
    "topo5": {"name": "拓扑5：管理+数据合设，控制独立", "mgmt_ctrl_together": False, "dn_separate": False},
    "topo6": {"name": "拓扑6：最小化部署（单节点）", "mgmt_ctrl_together": True, "dn_separate": False},
}

DEFAULT_CONFIG = _get_uat_config()

# 初始化 PHASES（需在 DEFAULT_CONFIG 定义之后执行）
PHASES = build_phases()
def switch_environment(env_key):
    """切换到指定环境配置"""
    if env_key not in ENV_PRESETS:
        return None
    preset = ENV_PRESETS[env_key]
    env = _JX_ENV_NODES.get(env_key)
    if not env:
        return None
    config = _get_uat_config()  # 复制 UAT 结构
    config["environment"] = env_key
    config["cluster_name"] = env["cluster_name"]
    config["cluster_id"] = f"DWS-{env_key}-001"
    config["nodes"] = _build_nodes_from_preset(preset)
    # 更新 OMS VIP（每个环境不同）
    if env_key == "DEV":
        config["oms_float_ips"] = {"oms_server": "10.134.91.203", "oms_web": "10.134.91.204", "lvs": "10.134.91.205"}
        config["network"]["dns_servers"] = [env["mgmt_subnet"] + ".1"]
    elif env_key == "SIT":
        config["oms_float_ips"] = {"oms_server": "10.134.134.203", "oms_web": "10.134.134.204", "lvs": "10.134.134.205"}
        config["network"]["dns_servers"] = [env["mgmt_subnet"] + ".1"]
    elif env_key == "PREPROD":
        config["oms_float_ips"] = {"oms_server": "10.134.50.5", "oms_web": "10.134.49.12", "lvs": "10.134.49.48"}
        config["network"]["dns_servers"] = [env["mgmt_subnet_a"] + ".1"]
    else:  # UAT
        config["oms_float_ips"] = {"oms_server": "10.134.21.202", "oms_web": "10.134.21.203", "lvs": "10.134.21.204"}
        config["network"]["dns_servers"] = [env["mgmt_subnet"] + ".1"]
    config["network"]["ntp_servers"] = [preset["nodes"][0]["mgmt_ip"]]
    return config


def generate_templates(config):
    """基于 LLD 配置数据生成完整部署配置文件"""
    nodes = config.get("nodes", [])
    cluster = config.get("cluster_name", "uatdws")
    storage = config.get("storage", {})
    disks = storage.get("data_disks", ["/dev/sdb"])
    gaussdb = config.get("gaussdb", {})
    fi = config.get("fi_manager", {})
    net = config.get("network", {})
    security = config.get("security", {})
    resource = config.get("resource", {})
    delivery = config.get("delivery", {})
    float_ips = config.get("float_ips", {})

    templates = {}

    # ═══ /etc/hosts ═══
    hosts = ["127.0.0.1   localhost localhost.localdomain"]
    for n in nodes:
        hosts.append(f"{n['mgmt_ip']}  {n['hostname']}  {n['hostname']}.{net.get('domain','dws.local')}")
    hosts.append("")
    templates["/etc/hosts"] = "\n".join(hosts) + "\n"

    # ═══ /etc/fstab ═══
    fstab = ["# /etc/fstab — Generated by DWS Assistant"]
    for i, disk in enumerate(disks, 1):
        fstab.append(f"UUID=<{disk}1_UUID>  {gaussdb.get('data_path','/data')}/disk{i}  xfs  defaults,noatime,nodiratime,inode64  0  2")
    fstab.append("")
    templates["/etc/fstab"] = "\n".join(fstab) + "\n"

    # ═══ preinstall.ini（FusionInsight 标准格式）═══
    ini = f""";===========================================================================
;; FusionInsight DWS {gaussdb.get('version','9.1.0')} — preinstall.ini
;; 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
;; 会话 ID：{config.get('cluster_id','')}
;;===========================================================================

; ========== 产品标识 ==========
[Product]
product_name          = {config.get('deploy_params',{}).get('product_name','GaussDB_DWS')}
cluster_name          = {cluster}
version               = {gaussdb.get('version','9.1.0')}

; ========== 部署配置 ==========
[DeployConfig]
install_mode          = {config.get('deploy_params',{}).get('install_mode','new_cluster')}
auth_mode             = {config.get('deploy_params',{}).get('auth_mode','normal')}
deploy_mode           = {config.get('deploy_params',{}).get('deploy_mode','normal')}
system_user           = {config.get('deploy_params',{}).get('system_user','root')}
software_path         = {config.get('deploy_params',{}).get('software_path','/opt/huawei')}
data_path             = {config.get('deploy_params',{}).get('data_path','/srv/BigData')}
topology              = {config.get('deploy_params',{}).get('topology','topo2')}
cluster_deploy_mode   = {config.get('deploy_mode','Single_Cluster')}
az_mode               = {config.get('az_mode','Single_AZ')}

; ========== 容量规划 ==========
[Capacity]
total_data_gb         = {config.get('capacity',{}).get('total_data_gb',150000)}
retention_days        = {config.get('capacity',{}).get('retention_days',365)}
daily_increment_gb    = {config.get('capacity',{}).get('daily_increment_gb',1200)}
disks_per_node        = {config.get('capacity',{}).get('disks_per_node',6)}
memory_per_node_gb    = {config.get('capacity',{}).get('memory_per_node_gb',509)}
cpu_per_node          = {config.get('capacity',{}).get('cpu_per_node',96)}
disk_format_ratio     = {config.get('capacity',{}).get('disk_format_ratio',1.093)}
compression_threshold = {config.get('capacity',{}).get('compression_threshold',0.7)}

; ========== OMS 浮动 IP ==========
[OMSFloatIP]
oms_server            = {config.get('oms_float_ips',{}).get('oms_server','')}
oms_web               = {config.get('oms_float_ips',{}).get('oms_web','')}
lvs                   = {config.get('oms_float_ips',{}).get('lvs','')}

; ========== 节点列表 ==========
[Nodes]
node_count            = {len(nodes)}
"""

    for n in nodes:
        ini += f"""
; --- {n['hostname']} ({n['role']}) ---
{n['hostname']}.role              = {n['role']}
{n['hostname']}.mgmt_ip           = {n['mgmt_ip']}
{n['hostname']}.mgmt_netmask      = {n.get('mgmt_netmask','255.255.255.0')}
{n['hostname']}.mgmt_gateway      = {n.get('mgmt_gateway','')}
{n['hostname']}.biz_ip            = {n['biz_ip']}
{n['hostname']}.biz_netmask       = {n.get('biz_netmask','255.255.255.0')}
{n['hostname']}.biz_gateway       = {n.get('biz_gateway','')}
{n['hostname']}.om_ip             = {n.get('om_ip','')}
{n['hostname']}.om_netmask        = {n.get('om_netmask','255.255.255.0')}
{n['hostname']}.cpu_cores         = {n.get('cpu_cores','')}
{n['hostname']}.memory_gb         = {n.get('memory_gb','')}
"""

    # OS
    ini += f"""
; ========== 操作系统 ==========
[OS]
version               = {config.get('os_version','')}
arch                  = {config.get('os_arch','ARM64')}
kernel_version        = {config.get('kernel_version','')}
python_version        = {config.get('python_version','3.8.5')}
iso_path              = {config.get('iso_path','')}
"""

    # 网络
    ini += f"""
; ========== 网络规划 ==========
[Network]
mgmt_bond             = {net.get('mgmt_bond_name','bond1')} (mode={net.get('mgmt_bond_mode','1')})
biz_bond              = {net.get('biz_bond_name','bond4')} (mode={net.get('biz_bond_mode','4')})
mtu                   = {net.get('mtu',1500)}
dns_servers           = {','.join(net.get('dns_servers',[]))}
ntp_servers           = {','.join(net.get('ntp_servers',[]))}
domain                = {net.get('domain','dws.local')}
bandwidth_required    = {net.get('bandwidth_required_mbps',800)}
"""

    # 存储
    ini += f"""
; ========== 存储规划 ==========
[Storage]
data_disks            = {','.join(disks)}
disk_type             = {storage.get('disk_type','SSD')}
raid_level            = {storage.get('raid_level','RAID0')}
raid_controller       = {storage.get('raid_controller','')}
partition_scheme      = {storage.get('partition_scheme','GPT')}
filesystem            = {storage.get('filesystem','xfs')}
xfs_ftype             = {storage.get('xfs_ftype',1)}
"""

    # GaussDB
    ini += f"""
; ========== GaussDB MPPDB ==========
[GaussDB]
version               = {gaussdb.get('version','9.1.0')}
package_path          = {gaussdb.get('package_path','')}
install_path          = {gaussdb.get('install_path','/opt/huawei/Bigdata')}
data_path             = {gaussdb.get('data_path','/data/gaussdb/data')}
wal_path              = {gaussdb.get('wal_path','/data/gaussdb/wal')}
tmp_path              = {gaussdb.get('tmp_path','/data/gaussdb/tmp')}
port                  = {gaussdb.get('port',25308)}
pooler_port           = {gaussdb.get('pooler_port',25309)}
cm_server_port        = {gaussdb.get('cm_server_port',25310)}
gtm_port              = {gaussdb.get('gtm_port',25311)}
encoding              = {gaussdb.get('encoding','UTF8')}
locale                = {gaussdb.get('locale','zh_CN.UTF-8')}
max_connections       = {gaussdb.get('max_connections',5000)}
shared_buffers_gb     = {gaussdb.get('shared_buffers_gb',64)}
wal_level             = {gaussdb.get('wal_level','hot_standby')}
max_wal_senders       = {gaussdb.get('max_wal_senders',16)}
"""

    # FusionInsight Manager
    ini += f"""
; ========== FusionInsight Manager ==========
[FusionInsightManager]
version               = {fi.get('version','9.1.0')}
install_path          = {fi.get('install_path','/opt/huawei/Bigdata/Manager')}
admin_user            = {fi.get('admin_user','admin')}
db_user               = {fi.get('db_user','omm')}
ssh_port              = {fi.get('ssh_port',22)}
web_port              = {fi.get('web_port',20009)}
"""

    # 资源管理
    ini += f"""
; ========== 资源管理 ==========
[Resource]
memory_limit_pct      = {resource.get('memory_limit_percent',80)}
cpu_affinity          = {resource.get('cpu_affinity','')}
io_nice               = {resource.get('io_nice',0)}
oom_score_adj         = {resource.get('oom_score_adj',-500)}
"""

    # 安全
    ini += f"""
; ========== 安全配置 ==========
[Security]
selinux_mode          = {security.get('selinux_mode','disabled')}
firewall              = {security.get('firewall','disabled')}
audit                 = {security.get('audit','disabled')}
ipv6                  = {security.get('ipv6','disabled')}
swap                  = {security.get('swap','disabled')}
thp                   = {security.get('thp','disabled')}
numa                  = {security.get('numa','disabled')}
"""

    templates["preinstall.ini"] = ini

    # ═══ grub 内核参数 ═══
    grub = ["# GRUB 内核参数 — Generated by DWS Assistant"]
    if security.get("thp") == "disabled":
        grub.append('transparent_hugepage=never')
    if security.get("numa") == "disabled":
        grub.append('numa=off')
    grub.append(f'elevator={"deadline" if storage.get("disk_type")=="SSD" else "cfq"}')
    if security.get("selinux_mode") == "disabled":
        grub.append('selinux=0')
    grub.append('quiet')
    templates["grub 内核参数"] = "\n".join(grub) + "\n"

    # ═══ 批量分区脚本 ═══
    part = [
        "#!/bin/bash",
        "# Auto-generated partition script by DWS Assistant",
        "# WARNING: This will erase all data on target disks!",
        f"# Cluster: {cluster} — Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "set -e",
        "",
    ]
    for disk in disks:
        part.append(f"echo '=== Partitioning {disk} ==='")
        part.append(f"parted -s {disk} mklabel gpt")
        part.append(f"parted -s {disk} mkpart primary 0% 100%")
        part.append(f"mkfs.xfs -f -n ftype={storage.get('xfs_ftype',1)} -L data{disks.index(disk)+1} {disk}1")
        part.append("")
    templates["分区脚本 (parted_mkfs.sh)"] = "\n".join(part) + "\n"

    # ═══ 网络配置脚本 ═══
    net_script = [
        "#!/bin/bash",
        "# Auto-generated network configuration script by DWS Assistant",
        f"# Cluster: {cluster}",
        "",
    ]
    for n in nodes:
        net_script.append(f"# --- {n['hostname']} ---")
        mgmt_bond = net.get('mgmt_bond_name','bond1')
        biz_bond = net.get('biz_bond_name','bond4')
        net_script.append(f"ssh {n['hostname']} 'nmcli con mod {mgmt_bond} ipv4.addresses {n['mgmt_ip']}/{n.get('mgmt_netmask','255.255.255.0').count('255')*8}'")
        net_script.append(f"ssh {n['hostname']} 'nmcli con mod {biz_bond} ipv4.addresses {n['biz_ip']}/{n.get('biz_netmask','255.255.255.0').count('255')*8}'")
        net_script.append("")
    templates["网络配置脚本 (setup_network.sh)"] = "\n".join(net_script) + "\n"

    # ═══ sysctl 参数 ═══
    sysctl = [
        "# /etc/sysctl.d/99-dws.conf — Generated by DWS Assistant",
        "",
        f"vm.min_free_kbytes = {256 * 1024 * 1024 // 100}",  # Rough estimate
        "vm.overcommit_memory = 0",
        "vm.overcommit_ratio = 80",
        "vm.swappiness = 0",
        "vm.dirty_ratio = 10",
        "vm.dirty_background_ratio = 5",
        f"net.ipv6.conf.all.disable_ipv6 = {1 if security.get('ipv6') == 'disabled' else 0}",
        f"net.ipv6.conf.default.disable_ipv6 = {1 if security.get('ipv6') == 'disabled' else 0}",
        "net.core.somaxconn = 65535",
        "net.ipv4.tcp_tw_reuse = 1",
        "net.ipv4.tcp_max_syn_backlog = 65535",
        "",
    ]
    templates["sysctl 参数 (99-dws.conf)"] = "\n".join(sysctl) + "\n"

    # ═══ 部署拓扑摘要 (LLD 概览) ═══
    oms = config.get("oms_float_ips", {})
    net_cfg = config.get("network", {})
    mgmt_subnet = ".".join(nodes[0]["mgmt_ip"].split(".")[:3]) if nodes else "10.134.21"
    biz_subnet = ".".join(nodes[0]["biz_ip"].split(".")[:3]) if nodes else "192.168.1"
    has_biz = any(n.get("biz_ip") and n["biz_ip"] != n["mgmt_ip"] for n in nodes)

    topo = [
        "╔══════════════════════════════════════════════════════════════╗",
        "║            DWS 集群部署拓扑 — LLD 参数总览                  ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  集群名称 : {cluster:<48} ║",
        f"║  环境标识 : {config.get('environment','UAT'):<48} ║",
        f"║  节点数量 : {len(nodes)} 物理节点 · {config.get('deploy_mode','Single_Cluster'):<32} ║",
        f"║  OS 版本  : {config.get('os_version','Kylin-V10-SP3'):<48} ║",
        f"║  数据库   : GaussDB DWS {gaussdb.get('version','9.1.0'):<38} ║",
        f"║  存储类型 : {storage.get('disk_type','SSD')} · {storage.get('raid_level','RAID5'):<41} ║",
        "╠══════════════════════════════════════════════════════════════╣",
        "║  网络地址分配                                                ║",
        "╠══════════════════════════════════════════════════════════════╣",
        f"║  管理平面 : {mgmt_subnet}.0/24 · bond1 · mode=1                     ║",
    ]
    for n in nodes:
        topo.append(f"║    {n['hostname']:<20} → {n['mgmt_ip']:<18} (掩码 {n.get('mgmt_netmask','255.255.255.0')}) ║")
    if has_biz:
        topo.append(f"║  业务平面 : {biz_subnet}.0/24 · bond4 · mode=4                     ║")
        for n in nodes:
            if n.get("biz_ip") and n["biz_ip"] != n["mgmt_ip"]:
                topo.append(f"║    {n['hostname']:<20} → {n['biz_ip']:<18} (掩码 {n.get('biz_netmask','255.255.255.0')}) ║")
    topo.append(f"║  BMC 带外 : CE5855-48T4XS ×2 · GE 管理交换机                    ║")
    topo.append("╠══════════════════════════════════════════════════════════════╣")
    topo.append("║  OMS 浮动 IP（FusionInsight Manager）                         ║")
    topo.append("╠══════════════════════════════════════════════════════════════╣")
    topo.append(f"║  OMS Server     : {oms.get('oms_server','N/A'):<42} ║")
    topo.append(f"║  OMWeb Service  : {oms.get('oms_web','N/A'):<42} ║")
    topo.append(f"║  LVS 负载均衡   : {oms.get('lvs','N/A'):<42} ║")
    topo.append("╠══════════════════════════════════════════════════════════════╣")
    topo.append("║  端口规划                                                    ║")
    topo.append("╠══════════════════════════════════════════════════════════════╣")
    topo.append(f"║  GaussDB Port        : {gaussdb.get('port',25308):<38} ║")
    topo.append(f"║  Pooler Port         : {gaussdb.get('pooler_port',25309):<38} ║")
    topo.append(f"║  CM Server Port      : {gaussdb.get('cm_server_port',25310):<38} ║")
    topo.append(f"║  GTM Port            : {gaussdb.get('gtm_port',25311):<38} ║")
    topo.append(f"║  Manager Web Port    : {fi.get('web_port',20009):<38} ║")
    topo.append(f"║  SSH Port            : {fi.get('ssh_port',22):<38} ║")
    topo.append("╚══════════════════════════════════════════════════════════════╝")
    templates["LLD 拓扑总览"] = "\n".join(topo) + "\n"

    # ─── 官方 preinstall.ini（平铺格式，可直接用于 gs_preinstall）───
    templates["preinstall.ini (官方格式·机器可执行)"] = _generate_official_preinstall(config, nodes)

    return templates


def _generate_official_preinstall(config, nodes):
    """生成官方平铺格式 preinstall.ini，可直接用于 FusionInsight gs_preinstall 工具"""
    net = config.get("network", {})
    storage = config.get("storage", {})
    gaussdb = config.get("gaussdb", {})
    fi = config.get("fi_manager", {})
    deploy = config.get("deploy_params", {})
    cap = config.get("capacity", {})

    # 管理IP列表（范围语法）
    mgmt_ips = [n["mgmt_ip"] for n in nodes]
    if len(set(ip.rsplit(".", 1)[0] for ip in mgmt_ips)) == 1:
        last_octets = sorted(int(ip.rsplit(".", 1)[1]) for ip in mgmt_ips)
        g_hosts = f'"{mgmt_ips[0].rsplit(".",1)[0]}.[{last_octets[0]}-{last_octets[-1]}]"'
    else:
        g_hosts = '"' + ",".join(mgmt_ips) + '"'

    # hostname_conf: 管理IP:业务IP:主机名
    hostname_entries = []
    for n in nodes:
        biz = n.get("biz_ip", n["mgmt_ip"])
        hostname_entries.append(f'{n["mgmt_ip"]}:{biz}:{n["hostname"]}')
    g_hostname_conf = '"' + ";".join(hostname_entries) + '"'

    # parted_conf: IP:hostN.ini
    parted_entries = []
    for i, n in enumerate(nodes):
        parted_entries.append(f'{n["mgmt_ip"]}:host{i}.ini')
    g_parted_conf = '"' + ";".join(parted_entries) + '"'

    lines = [
        "; ================================================================",
        f"; FusionInsight DWS {gaussdb.get('version','9.1.0')} — preinstall.ini",
        "; 官方格式：平铺 key=value，可直接用于 gs_preinstall 工具",
        f"; 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"; 集群：{config.get('cluster_name','')} · 嘉兴银行",
        "; ================================================================",
        "",
        "; ─── 主机配置 ───",
        f'g_hosts={g_hosts}',
        f'g_user_name="{deploy.get("system_user","root")}"',
        f'g_port={fi.get("ssh_port",22)}',
        "",
        "; ─── 分区格式化 ───",
        f'g_parted=2',
        f'g_parted_conf={g_parted_conf}',
        "",
        "; ─── RPM 包安装 ───",
        f'g_add_pkg=1',
        f'g_pkgs_dir="{config.get("os_version","Kylin-V10-SP3")}:/media/"',
        "",
        "; ─── 日志 ───",
        f'g_log_file="/tmp/fi-preinstall.log"',
        f'g_debug=0',
        "",
        "; ─── 主机名映射 ───",
        f'g_hostname_conf={g_hostname_conf}',
        "",
        "; ─── 系统优化 ───",
        f'g_swap_off=1',
        f'g_wce_conf=0',
        "",
        "; ─── 平台信息 ───",
        f'g_platform="{config.get("os_arch","aarch64")}"',
        "",
        "; ─── 故障诊断 ───",
        f'g_core_dump=1',
        f'g_core_dump_dir="/var/log/core"',
        "",
    ]

    return "\n".join(lines) + "\n"


class DeploymentSession:
    """一次部署会话"""

    def __init__(self, config=None):
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.config = config or DEFAULT_CONFIG.copy()
        self.phases = _init_phases(self.config)
        self.current_phase = 1
        self.audit_log = []
        self.created_at = datetime.now().isoformat()
        self.templates = {}

    def get_progress(self):
        total = sum(len(p["steps"]) for p in self.phases)
        completed = sum(
            sum(1 for s in p["steps"] if s["status"] in ("passed", "skipped"))
            for p in self.phases
        )
        failed = sum(
            sum(1 for s in p["steps"] if s["status"] == "failed") for p in self.phases
        )
        return {
            "total": total, "completed": completed, "failed": failed,
            "pct": int(completed / total * 100) if total else 0,
            "current_phase": self.current_phase,
        }

    def execute_step(self, phase_id, step_id, skip=False):
        """执行（或跳过）一个部署步骤"""
        phase = next((p for p in self.phases if p["id"] == phase_id), None)
        if not phase:
            return {"ok": False, "error": "阶段不存在"}

        step = next((s for s in phase["steps"] if s["id"] == step_id), None)
        if not step:
            return {"ok": False, "error": "步骤不存在"}

        if skip:
            step["status"] = "skipped"
            step["output"] = "[SKIPPED] 用户选择跳过"
            step["duration"] = 0
        else:
            start = time.time()
            step["status"] = "passed"
            step["output"] = f"[SIMULATED] 命令:\n{step['cmd']}\n\n执行成功 (模拟模式)"
            step["duration"] = round(time.time() - start, 1)

        # 记录审计日志
        entry = {
            "session": self.session_id,
            "cluster": self.config.get("cluster_name", ""),
            "phase": phase_id,
            "step": step_id,
            "status": step["status"],
            "cmd": step["cmd"],
            "output": step["output"][:500],
            "duration_sec": step.get("duration", 0),
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        }
        self.audit_log.append(entry)

        # 检查该阶段是否全部完成，自动推进
        if all(s["status"] in ("passed", "skipped") for s in phase["steps"]):
            phase["status"] = "done"
            if phase_id < len(self.phases):
                self.current_phase = phase_id + 1
                self.phases[phase_id]["status"] = "active"  # next phase

        return {"ok": True, "step": step, "entry": entry}

    def generate_templates(self):
        self.templates = generate_templates(self.config)
        return self.templates

    def to_dict(self):
        return {
            "session_id": self.session_id,
            "config": self.config,
            "phases": self.phases,
            "current_phase": self.current_phase,
            "progress": self.get_progress(),
            "audit_log": self.audit_log,
            "templates": self.templates,
        }


def _init_phases(config=None):
    """初始化阶段数据（根据配置动态生成）"""
    phases = build_phases(config)
    for p in phases:
        p["status"] = "pending"
        for s in p["steps"]:
            s["status"] = "pending"
            s["output"] = ""
            s["duration"] = 0
    phases[0]["status"] = "active"
    return phases


# ═══════════════════════════════════════════════════════════════
# DWS 架构图 — 场景定义 & 动态布局引擎
# ═══════════════════════════════════════════════════════════════

# DWS 节点角色说明
ROLE_META = {
    "OM":  {"label": "OM 管理",   "color": "#1a73e8", "shape": "hexagon"},
    "CN":  {"label": "Coordinator", "color": "#10b981", "shape": "rounded"},
    "DN":  {"label": "DataNode",    "color": "#6366f1", "shape": "rounded"},
    "GTM": {"label": "GTM",       "color": "#f59e0b", "shape": "diamond"},
}


def build_architecture_nodes(total_cn, total_dn, om_nodes=2, gtm_nodes=2,
                              co_deploy=False, cluster_name="uatdws",
                              physical_nodes=None, node_data=None):
    """根据参数构建节点列表，返回标准化架构数据。

    co_deploy=True时，physical_nodes指定实际物理节点数。
    node_data若提供则使用实际主机名和IP，否则生成示例数据。
    """
    if physical_nodes is None:
        physical_nodes = om_nodes if not co_deploy else max(om_nodes, total_dn)
    nodes = []

    # 使用实际节点数据或生成示例数据
    def _host(i, role_prefix=""):
        if node_data and i < len(node_data):
            return node_data[i].get("hostname", f"{cluster_name}{role_prefix}{i+1:02d}")
        return f"{cluster_name}{role_prefix}{i+1:02d}"
    def _mgmt(i):
        if node_data and i < len(node_data):
            return node_data[i].get("mgmt_ip", f"10.134.21.{190+i}")
        return f"10.134.21.{190+i}"
    def _biz(i):
        if node_data and i < len(node_data):
            return node_data[i].get("biz_ip", _mgmt(i))
        return f"192.168.1.{10+i}"

    # 物理节点
    for i in range(physical_nodes):
        is_primary = (i == 0 and i < om_nodes)
        nodes.append({
            "id": f"OM{i+1}" if i < om_nodes else f"WRK{i+1}",
            "role": "OM" if i < om_nodes else "DN",
            "roles": ["OM"] if i < om_nodes else [],
            "hostname": _host(i, "om"),
            "mgmt_ip": _mgmt(i), "biz_ip": _biz(i),
            "is_primary": is_primary,
        })

    # 角色分配
    if co_deploy:
        for i in range(min(gtm_nodes, om_nodes)):
            host = nodes[i]
            host.setdefault("roles", []).append("GTM")
            nodes.append({"id": f"GTM{i+1}", "role": "GTM", "hostname": host["hostname"], "mgmt_ip": host["mgmt_ip"], "biz_ip": host["biz_ip"], "co_host": host["id"]})
        for i in range(total_cn):
            host = nodes[i % physical_nodes]
            host.setdefault("roles", []).append("CN")
            nodes.append({"id": f"CN{i+1}", "role": "CN", "hostname": host["hostname"], "mgmt_ip": host["mgmt_ip"], "biz_ip": host["biz_ip"], "co_host": host["id"]})
        for i in range(total_dn):
            host = nodes[i % physical_nodes]
            host.setdefault("roles", []).append("DN")
            nodes.append({"id": f"DN{i+1}", "role": "DN", "hostname": host["hostname"], "mgmt_ip": host["mgmt_ip"], "biz_ip": host["biz_ip"], "co_host": host["id"]})
    else:
        offset = physical_nodes
        for i in range(gtm_nodes):
            nodes.append({"id": f"GTM{i+1}", "role": "GTM", "hostname": _host(offset+i, "gtm"), "mgmt_ip": _mgmt(offset+i), "biz_ip": _biz(offset+i)})
        offset += gtm_nodes
        for i in range(total_cn):
            nodes.append({"id": f"CN{i+1}", "role": "CN", "hostname": _host(offset+i, "cn"), "mgmt_ip": _mgmt(offset+i), "biz_ip": _biz(offset+i)})
        offset += total_cn
        for i in range(total_dn):
            nodes.append({"id": f"DN{i+1}", "role": "DN", "hostname": _host(offset+i, "dn"), "mgmt_ip": _mgmt(offset+i), "biz_ip": _biz(offset+i)})

    # Recalculate roles
    for n in nodes:
        if "co_host" in n: continue
        roles = set()
        for cn in nodes:
            if cn.get("co_host") == n["id"]: roles.add(cn["role"])
        roles.add(n["role"])
        n["roles"] = sorted(roles)
        n["role"] = n["roles"][0]

    return {
        "nodes": nodes,
        "om_count": om_nodes, "gtm_count": gtm_nodes,
        "cn_count": total_cn, "dn_count": total_dn,
        "co_deploy": co_deploy,
        "total_nodes": len(set(n["hostname"] for n in nodes)),
        "cluster_name": cluster_name,
    }


# 预设部署场景
ARCH_SCENARIOS = {
    "dev": {
        "name": "DEV 开发环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.91.x · 鲲鹏920 96C/512GB · 12×4T HDD",
        "om": 2, "gtm": 2, "cn": 3, "dn": 3, "co_deploy": True, "physical_nodes": 3,
        "hw": {"cpu": "2×鲲鹏920 48C", "ram": "512GB (8×64G)", "disk": "2×960G SSD + 12×4T HDD", "nic": "4×10GE", "raid": "RAID5 · 2逻辑盘"},
    },
    "sit": {
        "name": "SIT 测试环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.134.x · 鲲鹏920 96C/512GB · 12×4T HDD RAID5",
        "om": 2, "gtm": 2, "cn": 3, "dn": 3, "co_deploy": True, "physical_nodes": 3,
        "hw": {"cpu": "2×鲲鹏920 48C", "ram": "512GB (8×64G)", "disk": "2×960G SSD + 12×4T HDD", "nic": "4×10GE", "raid": "RAID5 · 2逻辑盘"},
    },
    "uat": {
        "name": "UAT 验收环境 (3合设)",
        "desc": "3节点全角色合设 · 10.134.21.x · 鲲鹏920 96C/509GB · 24×4T HDD RAID5",
        "om": 2, "gtm": 2, "cn": 3, "dn": 3, "co_deploy": True, "physical_nodes": 3,
        "hw": {"cpu": "2×鲲鹏920 48C", "ram": "512GB (8×64G)", "disk": "2×960G SSD + 24×4T HDD", "nic": "4×10GE", "raid": "RAID5 · 4逻辑盘"},
    },
    "preprod": {
        "name": "生产环境 (2+5 分离)",
        "desc": "2管控(64C/256G RAID1)+5数据(96C/512G RAID5) · 双平面 · 全闪存20×3.84T SSD",
        "om": 2, "gtm": 2, "cn": 2, "dn": 5, "co_deploy": False,
        "hw_ctrl": {"cpu": "2×鲲鹏920 32C", "ram": "256GB (4×64G)", "disk": "2×480G SSD + 4×960G SSD", "nic": "4×10GE", "raid": "RAID1"},
        "hw_data": {"cpu": "2×鲲鹏920 48C", "ram": "512GB (8×64G)", "disk": "2×960G SSD + 20×3.84T SSD", "nic": "4×10GE", "raid": "RAID5 · 4逻辑盘"},
    },
    "expand": {
        "name": "扩容场景 (2+8 大规模)",
        "desc": "2管控+8数据 · 未来大规模扩容 · 全闪存",
        "om": 2, "gtm": 2, "cn": 3, "dn": 8, "co_deploy": False,
        "hw_ctrl": {"cpu": "2×鲲鹏920 32C", "ram": "256GB (4×64G)", "disk": "2×480G SSD + 4×960G SSD", "nic": "4×10GE", "raid": "RAID1"},
        "hw_data": {"cpu": "2×鲲鹏920 48C", "ram": "512GB (8×64G)", "disk": "2×960G SSD + 20×3.84T SSD", "nic": "4×10GE", "raid": "RAID5"},
    },
    "custom": {
        "name": "自定义规模",
        "desc": "自由调整 OM/CN/DN 数量",
        "om": 2, "gtm": 2, "cn": 2, "dn": 3, "co_deploy": False,
    },
}

# 默认架构图场景（与当前环境联动）
ARCH_ENV_MAP = {"DEV": "dev", "SIT": "sit", "UAT": "uat", "PREPROD": "preprod"}


def get_architecture_data(scenario_key="uat"):
    """获取指定架构场景的节点数据，优先使用环境预设中的实际主机名和IP"""
    scenario = ARCH_SCENARIOS.get(scenario_key, ARCH_SCENARIOS["uat"])
    # 尝试从环境预设中获取实际节点数据
    env_key = scenario_key.upper() if scenario_key != "expand" else "PREPROD"
    env_preset = ENV_PRESETS.get(env_key, ENV_PRESETS.get("UAT"))
    node_data = env_preset.get("nodes") if env_preset else None
    cluster = env_preset.get("cluster_name", "uatdws") if env_preset else "uatdws"

    return build_architecture_nodes(
        total_cn=scenario["cn"],
        total_dn=scenario["dn"],
        om_nodes=scenario["om"],
        gtm_nodes=scenario["gtm"],
        co_deploy=scenario.get("co_deploy", False),
        physical_nodes=scenario.get("physical_nodes"),
        node_data=node_data,
        cluster_name=cluster,
    )


# ═══════════════════════════════════════════════════════════════
# 设备清单 & 机柜布线（嘉兴银行生产环境实际规划）
# ═══════════════════════════════════════════════════════════════

# 版本选型（PPT Slide 8）
VERSION_SELECTION = {
    "mrs": {"version": "3.5.1-LTS", "reason": "实际部署版本（PPT原规划3.6.0，最终采用3.5.1稳定版）"},
    "dws": {"version": "9.1.0", "reason": "稳定版本，POC验证通过，项目实际交付版本"},
    "upgrade_path": "MRS 3.5.1→3.6.0 (后续升级), DWS 9.1.0→9.1.1 (后续升级)",
    "os": "Kylin-V10-SP3 (20221125)",
}

# 完整硬件批次（PPT Slide 11）
HARDWARE_BATCHES = [
    {"batch": "1", "type": "生产/准生产 MRS", "qty": 6, "cpu": "2×鲲鹏920 32C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 14×8T HDD", "note": "管理+HDFS+Yarn+Hive+Spark+Flink"},
    {"batch": "2", "type": "生产/准生产 DWS", "qty": 6, "cpu": "2×鲲鹏920 48C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 12×4T HDD", "note": "管控+数据合设"},
    {"batch": "3", "type": "UAT MRS", "qty": 3, "cpu": "2×鲲鹏920 32C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 24×8T HDD", "note": "用户验收测试"},
    {"batch": "4", "type": "UAT DWS", "qty": 3, "cpu": "2×鲲鹏920 48C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 24×4T HDD", "note": "用户验收测试"},
    {"batch": "5", "type": "MRS+DWS 管控节点", "qty": 10, "cpu": "2×鲲鹏920 32C", "ram": "4×64G DDR4",
     "disk": "2×480G SSD + 4×960G SSD", "note": "管控节点，低配内存"},
    {"batch": "6", "type": "MRS ES+Kafka", "qty": 6, "cpu": "2×鲲鹏920 32C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 12×1.92T SSD", "note": "实时数据总线"},
    {"batch": "7", "type": "MRS 数据节点", "qty": 8, "cpu": "2×鲲鹏920 32C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 24×7.68T SSD", "note": "大容量数据存储"},
    {"batch": "8", "type": "DWS 生产数据节点", "qty": 10, "cpu": "2×鲲鹏920 48C", "ram": "8×64G DDR4",
     "disk": "2×960G SSD + 20×3.84T SSD", "note": "全闪存高性能MPP"},
]

EQUIPMENT_LIST = {
    "servers": [
        {"type": "DWS管控节点", "model": "鲲鹏920 2×32C", "qty": 2, "ram": "256GB (8×32GB)",
         "disk": "2×480GB SSD + 4×960GB SSD", "nic": "4×10GE", "hosts": "DWS-MN-01, DWS-MN-02", "rack": "9号柜/8号柜"},
        {"type": "DWS数据节点", "model": "鲲鹏920 2×32C", "qty": 3, "ram": "512GB (16×32GB)",
         "disk": "2×480GB SSD + 12×3.84TB SSD", "nic": "4×10GE", "hosts": "DWS-DN-01, DWS-DN-02, DWS-DN-03", "rack": "8号柜×2, 9号柜×1"},
        {"type": "MRS管控节点", "model": "鲲鹏920 2×32C", "qty": 2, "ram": "256GB (8×32GB)",
         "disk": "2×480GB SSD + 4×960GB SSD", "nic": "4×10GE", "hosts": "MRS-MN-01, MRS-MN-02", "rack": "8号柜/9号柜"},
        {"type": "MRS控制节点", "model": "鲲鹏920 2×32C", "qty": 3, "ram": "256GB (8×32GB)",
         "disk": "2×480GB SSD + 4×960GB SSD", "nic": "4×10GE", "hosts": "MRS-CN-01~03", "rack": "8号柜×2, 9号柜×1"},
        {"type": "MRS流处理节点", "model": "鲲鹏920 2×32C", "qty": 3, "ram": "256GB (8×32GB)",
         "disk": "2×480GB SSD + 4×960GB SSD", "nic": "4×10GE", "hosts": "MRS-Flink-01~03", "rack": "9号柜"},
        {"type": "MRS计算节点", "model": "鲲鹏920 2×32C", "qty": 3, "ram": "512GB (16×32GB)",
         "disk": "2×480GB SSD + 12×8TB HDD", "nic": "4×10GE", "hosts": "MRS-Spark-01~03", "rack": "9号柜×1, 8号柜×2"},
        {"type": "DataArk节点", "model": "鲲鹏920 2×24C", "qty": 4, "ram": "128GB (8×16GB)",
         "disk": "1×960GB SSD", "nic": "2×10GE", "hosts": "DataArk-01~04", "rack": "9号柜/8号柜/7号柜/6号柜"},
    ],
    "network": [
        {"type": "核心交换机", "model": "CE8850-64CQ-EI", "qty": 2, "ports": "64×100GE QSFP28", "role": "Core-1/2",
         "rack": "8号柜2U / 4号柜2U"},
        {"type": "管理汇聚交换机", "model": "CE6881H-48S6CQ-B", "qty": 2, "ports": "48×10GE SFP+ + 6×100GE", "role": "管理平面",
         "rack": "9号柜31U / 10号柜31U"},
        {"type": "业务汇聚交换机", "model": "CE6881H-48S6CQ-B", "qty": 2, "ports": "48×10GE SFP+ + 6×100GE", "role": "业务平面",
         "rack": "9号柜33U / 10号柜33U"},
        {"type": "BMC管理交换机", "model": "CE5855-48T4XS", "qty": 2, "ports": "48×GE + 4×10GE SFP+", "role": "BMC带外管理",
         "rack": "9号柜29U / 10号柜29U"},
    ],
    "security": [
        {"type": "防火墙", "model": "USG6635F", "qty": 2, "ports": "8×GE + 4×GE RJ45 + 10×10GE SFP+", "role": "FW-1/2",
         "rack": "8号柜5U / 4号柜5U", "features": "IPS+AV+URL过滤, 240G SSD"},
    ],
    "cabling": {
        "management": [
            {"from": "Core-1 100GE1/0/1", "to": "管理汇聚-1 100G1/0/5", "type": "100GE MPO"},
            {"from": "Core-1 100GE1/0/2", "to": "管理汇聚-2 100G1/0/5", "type": "100GE MPO"},
            {"from": "Core-2 100GE1/0/1", "to": "管理汇聚-1 100G1/0/6", "type": "100GE MPO"},
            {"from": "Core-2 100GE1/0/2", "to": "管理汇聚-2 100G1/0/6", "type": "100GE MPO"},
            {"from": "管理汇聚-1 100GE1/0/3", "to": "管理汇聚-2 100GE1/0/3", "type": "40GE MPO peerlink"},
            {"from": "管理汇聚-1 100GE1/0/4", "to": "管理汇聚-2 100GE1/0/4", "type": "40GE MPO peerlink"},
        ],
        "service": [
            {"from": "Core-1 100GE1/0/3", "to": "业务汇聚-1 100G1/0/5", "type": "100GE MPO"},
            {"from": "Core-1 100GE1/0/4", "to": "业务汇聚-2 100G1/0/5", "type": "100GE MPO"},
            {"from": "Core-2 100GE1/0/3", "to": "业务汇聚-1 100G1/0/6", "type": "100GE MPO"},
            {"from": "Core-2 100GE1/0/4", "to": "业务汇聚-2 100G1/0/6", "type": "100GE MPO"},
            {"from": "业务汇聚-1 100GE1/0/3", "to": "业务汇聚-2 100GE1/0/3", "type": "40GE MPO peerlink"},
            {"from": "业务汇聚-1 100GE1/0/4", "to": "业务汇聚-2 100GE1/0/4", "type": "40GE MPO peerlink"},
        ],
    },
}

# 机柜设备分布
RACK_LAYOUT = [
    {"rack": "9号柜 (IT)", "u_start": 42, "devices": [
        {"u": 33, "name": "业务汇聚交换机-1", "h": 1},
        {"u": 31, "name": "管理汇聚交换机-1", "h": 1},
        {"u": 29, "name": "BMC交换机-1", "h": 1},
        {"u": 27, "name": "DataArk-01", "h": 2},
        {"u": 24, "name": "MRS-MN-02", "h": 2},
        {"u": 21, "name": "MRS-CN-03", "h": 2},
        {"u": 18, "name": "MRS-Spark-01", "h": 2},
        {"u": 15, "name": "MRS-Flink-01", "h": 2},
        {"u": 12, "name": "MRS-Flink-02", "h": 2},
        {"u": 9,  "name": "MRS-Flink-03", "h": 2},
        {"u": 6,  "name": "DWS-DN-03", "h": 2},
        {"u": 3,  "name": "DWS-MN-02", "h": 2},
    ]},
    {"rack": "8号柜 (IT)", "u_start": 42, "devices": [
        {"u": 33, "name": "业务汇聚交换机-2", "h": 1},
        {"u": 31, "name": "管理汇聚交换机-2", "h": 1},
        {"u": 29, "name": "BMC交换机-2", "h": 1},
        {"u": 27, "name": "DataArk-02", "h": 2},
        {"u": 24, "name": "MRS-MN-01", "h": 2},
        {"u": 21, "name": "MRS-CN-01", "h": 2},
        {"u": 18, "name": "MRS-CN-02", "h": 2},
        {"u": 15, "name": "MRS-Spark-02", "h": 2},
        {"u": 12, "name": "MRS-Spark-03", "h": 2},
        {"u": 9,  "name": "DWS-DN-02", "h": 2},
        {"u": 6,  "name": "DWS-DN-01", "h": 2},
        {"u": 3,  "name": "DWS-MN-01", "h": 2},
    ]},
]


# ─── 全局会话管理 ───
_sessions = {}


def get_or_create_session(force_new=False):
    key = "default"
    if force_new or key not in _sessions:
        _sessions[key] = DeploymentSession()
    return _sessions[key]


def reset_session():
    _sessions.pop("default", None)
    return get_or_create_session(force_new=True)
