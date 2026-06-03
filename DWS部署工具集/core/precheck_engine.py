"""
DWS 部署预检引擎
基于嘉兴银行 DWS 部署实践 + DWS 9.1.0 产品文档规范
"""

PRECHECK_ITEMS = [
    # ================================================================
    # 硬件环境 (5项)
    # ================================================================
    {
        "id": "hw-raid",
        "name": "RAID策略",
        "category": "hardware",
        "severity": "error",
        "description": "读策略=Read Ahead, 写策略=Write Back With BBU",
        "check_cmd": "storcli64 /c0 show | grep -E 'Read|Write' 2>/dev/null || echo '未安装RAID管理工具'",
        "solution": "IBMC界面 -> 存储管理 -> RAID策略配置",
    },
    {
        "id": "hw-disk-count",
        "name": "磁盘数量",
        "category": "hardware",
        "severity": "error",
        "description": "生产≥6块, 测试≥2块",
        "check_cmd": "lsblk -d -o NAME | grep -cP '^sd|^nvme|^vd'",
        "solution": "确认物理盘数量满足要求",
    },
    {
        "id": "hw-network-card",
        "name": "网卡检查",
        "category": "hardware",
        "severity": "warning",
        "description": "25GE网卡(Hi1822需单独处理), MTU=1500",
        "check_cmd": "ethtool $(ls /sys/class/net | grep -v lo | head -1) 2>/dev/null | grep -E 'Speed|Duplex'",
        "solution": "Hi1822需使用hinicconfig增加中断个数",
    },
    {
        "id": "hw-ssd-check",
        "name": "SSD确认",
        "category": "hardware",
        "severity": "warning",
        "description": "数据盘必须为SSD(ROTA=0)",
        "check_cmd": "lsblk -d -o NAME,ROTA | grep -v sr0",
        "solution": "HDD盘不满足DWS性能要求，需更换SSD",
    },
    {
        "id": "hw-bios-numa",
        "name": "BIOS/NUMA配置",
        "category": "hardware",
        "severity": "warning",
        "description": "关闭节能模式, NUMA平衡关闭",
        "check_cmd": "cat /proc/sys/vm/numa_balancing",
        "solution": "BIOS设置关闭节能; sysctl -w kernel.numa_balancing=0",
    },

    # ================================================================
    # OS配置 (6项)
    # ================================================================
    {
        "id": "os-audit",
        "name": "audit服务",
        "category": "os",
        "severity": "error",
        "description": "DWS要求关闭auditd",
        "check_cmd": "systemctl is-active auditd 2>/dev/null",
        "solution": "systemctl stop auditd; systemctl disable auditd",
    },
    {
        "id": "os-firewall",
        "name": "防火墙",
        "category": "os",
        "severity": "error",
        "description": "关闭firewalld和iptables",
        "check_cmd": "systemctl is-active firewalld 2>/dev/null; systemctl is-active iptables 2>/dev/null",
        "solution": "systemctl stop firewalld iptables; systemctl disable firewalld iptables",
    },
    {
        "id": "os-selinux",
        "name": "SELinux",
        "category": "os",
        "severity": "error",
        "description": "必须为disabled",
        "check_cmd": "getenforce",
        "solution": "sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config",
    },
    {
        "id": "os-swap",
        "name": "swap关闭",
        "category": "os",
        "severity": "error",
        "description": "必须关闭swap",
        "check_cmd": "swapon --show | wc -l",
        "solution": "swapoff -a; 注释/etc/fstab中swap行",
    },
    {
        "id": "os-hugepage",
        "name": "透明大页",
        "category": "os",
        "severity": "error",
        "description": "必须关闭透明大页(transparent_hugepage=never)",
        "check_cmd": "cat /sys/kernel/mm/transparent_hugepage/enabled | grep -o '\\[never\\]' || echo 'not disabled'",
        "solution": "grub2-mkconfig; 在GRUB_CMDLINE_LINUX追加transparent_hugepage=never",
    },
    {
        "id": "os-timezone",
        "name": "时区",
        "category": "os",
        "severity": "error",
        "description": "DWS要求Asia/Shanghai时区(注意:GaussDB OLTP要求UTC)",
        "check_cmd": "timedatectl | grep 'Time zone'",
        "solution": "timedatectl set-timezone Asia/Shanghai",
    },
    {
        "id": "os-charset",
        "name": "字符集",
        "category": "os",
        "severity": "warning",
        "description": "en_US.UTF-8",
        "check_cmd": "echo $LANG",
        "solution": "echo 'LANG=\"en_US.UTF-8\"' > /etc/locale.conf; source /etc/locale.conf",
    },
    {
        "id": "os-kernel-params",
        "name": "内核参数",
        "category": "os",
        "severity": "warning",
        "description": "vm.watermark_scale_factor=100, kernel.numa_balancing=0, OOM配置",
        "check_cmd": "sysctl vm.watermark_scale_factor kernel.numa_balancing",
        "solution": "echo 'vm.watermark_scale_factor=100' >> /etc/sysctl.conf; sysctl -p",
    },

    # ================================================================
    # 存储 (2项)
    # ================================================================
    {
        "id": "stor-mount",
        "name": "磁盘挂载",
        "category": "storage",
        "severity": "error",
        "description": "/srv/BigData/dbdata_om, LocalBackup, mppdb/data1, mppdb/data2 需挂载",
        "check_cmd": "df -h | grep /srv/BigData",
        "solution": "parted GPT分区 -> mkfs.xfs -> /etc/fstab -> mount -a",
    },
    {
        "id": "stor-fstab",
        "name": "fstab持久化",
        "category": "storage",
        "severity": "error",
        "description": "/etc/fstab 需配置XFS挂载项",
        "check_cmd": "grep /srv/BigData /etc/fstab 2>/dev/null || echo '未配置'",
        "solution": "blkid获取UUID -> 写入/etc/fstab -> mount -a验证",
    },

    # ================================================================
    # 软件环境 (2项)
    # ================================================================
    {
        "id": "sw-python",
        "name": "Python 3.8.5",
        "category": "software",
        "severity": "error",
        "description": "DWS 8.x必须使用Python 3.8.5",
        "check_cmd": "python3.8 --version 2>/dev/null || python3 --version",
        "solution": "编译安装: ./configure --enable-optimizations --prefix=/usr/local && make -j4 && make altinstall",
    },
    {
        "id": "sw-yum",
        "name": "yum源/ISO",
        "category": "software",
        "severity": "error",
        "description": "需要挂载Kylin ISO并配置yum源",
        "check_cmd": "yum list installed gcc 2>/dev/null | head -1 || echo 'yum不可用'",
        "solution": "mount /opt/Kylin-*.iso /media -o loop; 配置local repo",
    },
]

PRECHECK_PHASES = {
    "hardware": {"name": "硬件环境", "icon": "🖥️", "count": 5},
    "os": {"name": "OS配置", "icon": "💿", "count": 8},
    "storage": {"name": "存储配置", "icon": "💾", "count": 2},
    "software": {"name": "软件环境", "icon": "📦", "count": 2},
}
