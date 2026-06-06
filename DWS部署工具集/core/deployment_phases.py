"""
DWS 部署阶段定义（完整版 v2）

基于官方文档补充完善：
  - DWS部署-V2.0.docx
  - GaussDB(DWS)测试集群标准实施交付文档.docx
  - GaussDB(DWS) 9.1.0-ESL 配置规划工具

阶段数: 8 → 10
新增: Phase 8 OMS安装(主备), Phase 9 集群部署+参数优化
补充: Hi1822网卡, cstore_buffers, sudo脚本, License, 验收验证
"""


def build_phases(config=None):
    """构建完整 10 阶段部署流程"""
    nodes = []
    cluster = "dws_cluster"
    if config:
        nodes = config.get("nodes", [])
        cluster = config.get("cluster_name", "dws_cluster")

    ntp_ip = nodes[0]["mgmt_ip"] if nodes else "10.0.0.1"
    bw_test_ip = nodes[1]["mgmt_ip"] if len(nodes) > 1 else ntp_ip
    first_hostname = nodes[0]["hostname"] if nodes else "dws-node-1"

    hostlist_items = [n["hostname"] for n in nodes]
    hostlist_cmd = "echo -e '" + "\\n".join(hostlist_items) + "' > /opt/hostlist"

    return [
        {
            "id": 1, "name": "环境准备",
            "icon": "🔧",
            "steps": [
                {"id": "hosts", "name": "配置 /etc/hosts", "cmd": f"echo '{first_hostname}' > /etc/hostname && hostnamectl set-hostname {first_hostname}",
                 "desc": "设置主机名并写入hosts映射"},
                {"id": "python", "name": "验证 Python3.8.5", "cmd": "python3 --version && python3 -c 'import sqlite3, ssl'",
                 "desc": "确认 Python3.8.5 及关键模块可用（DWS 8.x/9.x 必需）"},
                {"id": "yum", "name": "挂载 ISO 配置 yum 源", "cmd": "mount /opt/Kylin-*.iso /media -o loop && mkdir -p /etc/yum.repos.d/bak && mv /etc/yum.repos.d/kylin*.repo /etc/yum.repos.d/bak/",
                 "desc": "挂载 KylinOS ISO 并配置本地 yum 源"},
                {"id": "chrony", "name": "配置 chrony/NTP", "cmd": f"echo 'server {ntp_ip} iburst' >> /etc/chrony.conf && systemctl restart chronyd && chronyc sources",
                 "desc": "以节点1为 NTP 服务器，其余节点指向节点1"},
                {"id": "deps", "name": "安装系统依赖包", "cmd": "yum install -y gcc patch libffi-devel python-devel zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel readline-devel tk-devel",
                 "desc": "安装 GaussDB 编译安装所需的系统依赖包"},
            ]
        },
        {
            "id": 2, "name": "OS 调优",
            "icon": "⚙️",
            "steps": [
                {"id": "disable_audit", "name": "关闭 audit 服务", "cmd": "systemctl stop auditd && systemctl disable auditd",
                 "desc": "关闭审计服务以提升 I/O 性能"},
                {"id": "disable_firewall", "name": "关闭防火墙", "cmd": "systemctl stop firewalld && systemctl disable firewalld && systemctl stop iptables && systemctl disable iptables",
                 "desc": "同时关闭 firewalld 和 iptables"},
                {"id": "selinux", "name": "关闭 SELinux", "cmd": "sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config && setenforce 0",
                 "desc": "关闭 SELinux 避免权限干扰"},
                {"id": "disable_swap", "name": "关闭 swap", "cmd": "swapoff -a && sed -i '/swap/s/^/#/' /etc/fstab",
                 "desc": "关闭 swap，注释 /etc/fstab 中的 swap 行"},
                {"id": "disable_thp", "name": "关闭透明大页", "cmd": "cp /etc/default/grub /etc/default/grub.bak && sed -i '/GRUB_CMDLINE_LINUX/s/\"$/ transparent_hugepage=never\"/' /etc/default/grub && grub2-mkconfig -o /boot/efi/EFI/kylin/grub.cfg",
                 "desc": "备份grub → 追加 transparent_hugepage=never → 重新生成 grub.cfg"},
                {"id": "timezone", "name": "时区设置", "cmd": "timedatectl set-timezone Asia/Shanghai && date +'%Z %z'",
                 "desc": "DWS 要求 Asia/Shanghai 时区（CST +0800）"},
                {"id": "charset", "name": "字符集设置", "cmd": "echo 'LANG=en_US.UTF-8' > /etc/locale.conf && source /etc/locale.conf",
                 "desc": "DWS 要求 en_US.UTF-8 字符集"},
                {"id": "watermark", "name": "OS 内存水位线", "cmd": "cp /etc/sysctl.conf /etc/sysctl.conf.bak && sed -i 's/vm.watermark_scale_factor.*=.*/vm.watermark_scale_factor = 100/' /etc/sysctl.conf && sysctl -p",
                 "desc": "DWS部署V2.0：vm.watermark_scale_factor=100，POC性能关键参数"},
                {"id": "numa_config", "name": "NUMA 参数", "cmd": "echo 'kernel.numa_balancing = 0' >> /etc/sysctl.conf && sysctl -p",
                 "desc": "关闭 NUMA 平衡，DWS 部署必配参数"},
                {"id": "oom_config", "name": "OOM 策略", "cmd": "echo 0 > /proc/sys/vm/panic_on_oom && echo 0 > /proc/sys/vm/oom_kill_allocating_task && echo 'vm.overcommit_memory=0' >> /etc/sysctl.conf && sysctl -p",
                 "desc": "panic_on_oom=0, oom_kill_allocating_task=0，防止部署被 OOM 终结"},
                {"id": "io_scheduler", "name": "IO 调度器", "cmd": "echo 'elevator=mq-deadline' | grubby --update-kernel=ALL --args",
                 "desc": "DWS 推荐 mq-deadline 调度器"},
                {"id": "vm_min_free", "name": "vm.min_free_kbytes", "cmd": "a=$(free -k|grep Mem|awk '{print $2}'); echo \"vm.min_free_kbytes=$((a*5/100))\" >> /etc/sysctl.conf && sysctl -p",
                 "desc": "设置为物理内存的 5%（标准实施文档规范）"},
                {"id": "omm_cron", "name": "omm 用户 cron 权限", "cmd": "echo 'omm' >> /etc/cron.allow",
                 "desc": "将 omm 用户加入 /etc/cron.allow（FusionInsight 预检查要求）"},
            ]
        },
        {
            "id": 3, "name": "硬件验证",
            "icon": "🖥️",
            "steps": [
                {"id": "nic_check", "name": "Hi1822 网卡检测", "cmd": "lspci | grep Hi1822 && ethtool -i eth0",
                 "desc": "确认 Hi1822 智能网卡正常识别，若存在需用 hinicconfig 增加中断数"},
                {"id": "nic_irq", "name": "Hi1822 中断配置", "cmd": "hinicconfig eth0 -c INT_CFG 2>/dev/null || echo '非Hi1822网卡或无hinicconfig工具'",
                 "desc": "⚠️ Hi1822 默认中断16个需增加，否则影响业务性能"},
                {"id": "raid_check", "name": "RAID 策略验证", "cmd": "storcli64 /c0 show && storcli64 /c0 /vall show | grep -E 'RAID|State'",
                 "desc": "验证 RAID 卡状态，读策略=Read Ahead，写策略=Write Back With BBU"},
                {"id": "ssd_detect", "name": "SSD/HDD 识别", "cmd": "lsblk -d -o NAME,ROTA",
                 "desc": "ROTA=0 为 SSD，ROTA=1 为 HDD。数据盘必须使用 SSD"},
                {"id": "bios_check", "name": "BIOS 配置检查", "cmd": "echo '检查项: Power Policy=Performance / Die Interleaving=Disable / NUMA=Enable / SMMU=Disabled'",
                 "desc": "华为 DWS 官方验收规范：7项 BIOS 配置检查"},
                {"id": "fio_test", "name": "FIO 磁盘压测", "cmd": "fio --name=test --iodepth=16 --rw=randwrite --bs=64k --size=10G --numjobs=4 --runtime=60 --group_reporting --directory=/srv/BigData/mppdb/data1",
                 "desc": "随机写压测验收磁盘基准性能，目录为 /srv/BigData/mppdb/data1"},
            ]
        },
        {
            "id": 4, "name": "磁盘规划",
            "icon": "💾",
            "steps": [
                {"id": "os_part", "name": "OS 盘分区", "cmd": "echo '标准分区: /=20GB /tmp=30GB /var=30GB /var/log=400GB /srv/BigData=60GB /opt=420GB'",
                 "desc": "华为 DWS 验收规范：OS盘RAID1，6个标准分区，/opt≥300GB"},
                {"id": "parted", "name": "数据盘 parted 分区", "cmd": "parted -s /dev/sdb mklabel gpt && parted -s /dev/sdb mkpart primary 2048s 100%",
                 "desc": "创建 GPT 分区表，起始扇区 2048s 对齐（4K对齐）"},
                {"id": "mkfs", "name": "mkfs.xfs 格式化", "cmd": "mkfs.xfs -f -n ftype=1 -L data1 /dev/sdb1",
                 "desc": "格式化为 XFS，ftype=1 为 Docker overlay2 必需"},
                {"id": "fstab", "name": "配置 /etc/fstab", "cmd": "UUID=$(blkid -s UUID -o value /dev/sdb1) && echo 'UUID=$UUID /srv/BigData/data1 xfs defaults,noatime 0 0' >> /etc/fstab",
                 "desc": "写入 fstab 确保重启后自动挂载"},
                {"id": "mount_data", "name": "挂载验证", "cmd": "mkdir -p /srv/BigData/data1 && mount -a && df -h /srv/BigData",
                 "desc": "创建挂载点并验证挂载成功"},
            ]
        },
        {
            "id": 5, "name": "网络验证",
            "icon": "🌐",
            "steps": [
                {"id": "bond_mgmt", "name": "管理平面 Bond 配置", "cmd": "echo '管理平面 bond1 mode=1(active-backup); IP: mgmt_ip; MTU=1500'",
                 "desc": "管理平面使用 bond1，主备模式，用于运维管理"},
                {"id": "bond_biz", "name": "业务平面 Bond 配置", "cmd": "echo '业务平面 bond4 mode=4(802.3ad); IP: biz_ip; MTU=1500'",
                 "desc": "业务平面使用 bond4，动态链路聚合，用于数据交换"},
                {"id": "speed_test", "name": "节点间带宽测试", "cmd": f"sar -n DEV 1 10 && speed_test send {bw_test_ip} 10001 tcp",
                 "desc": "节点间实测带宽应 >800MB/s（10GE 线速80%）"},
                {"id": "gsar_check", "name": "网络重传率检查", "cmd": "sh gsar.sh 2>/dev/null || echo '需执行: sar -n DEV 1 观察 drop/retrans 比例'",
                 "desc": "重传率应 <0.01%，检查 drop 和 resend 比例"},
            ]
        },
        {
            "id": 6, "name": "软件部署",
            "icon": "📦",
            "steps": [
                {"id": "unzip_gaussdb", "name": "解压 GaussDB 软件包", "cmd": "unzip -o /opt/GaussDB_MPPDB_9.1.0.zip -d /opt/ && chmod +x /opt/GaussDB_MPPDB_9.1.0/*.run",
                 "desc": "解压 GaussDB MPPDB 安装包到 /opt"},
                {"id": "unzip_fi", "name": "解压 FusionInsight 工具包", "cmd": "tar zxf /opt/FusionInsight_Manager.tar.gz -C /opt/ && tar zxf /opt/FusionInsight_SetupTool.tar.gz -C /opt/",
                 "desc": "解压 FusionInsight Manager 和 SetupTool"},
                {"id": "copy_packages", "name": "分发软件包", "cmd": hostlist_cmd + " && for host in $(cat /opt/hostlist); do scp -r /opt/GaussDB_MPPDB_9.1.0 $host:/opt/; done",
                 "desc": "将 GaussDB 和 FI 包分发到集群所有节点"},
                {"id": "install_deps", "name": "安装 GaussDB 依赖 RPM", "cmd": "cd /opt/FusionInsight_SetupTool/rpm && rpm -ivh *.rpm --nodeps 2>&1 | grep -E 'installing|already'",
                 "desc": "安装 haveged/sdparm/libatomic 等必需 RPM"},
            ]
        },
        {
            "id": 7, "name": "预检查",
            "icon": "🔍",
            "steps": [
                {"id": "preinstall_ini", "name": "配置 preinstall.ini", "cmd": "cd /opt/FusionInsight_SetupTool && ./setuptool.sh preinstall -f /opt/preinstall.ini",
                 "desc": "使用配置中心生成的 preinstall.ini 执行预安装配置"},
                {"id": "gs_precheck", "name": "GaussDB 预检查", "cmd": "cd /opt/FusionInsight_SetupTool && ./setuptool.sh precheck -f /opt/preinstall.ini",
                 "desc": "执行 FusionInsight 预检查，ERROR 级必须处理"},
                {"id": "sudo_script", "name": "更新 sudo 脚本", "cmd": "cd /opt/FusionInsight_SetupTool/os_optimization_tool && sh optimization_patch.sh install && sh optimization_patch.sh commit",
                 "desc": "⚠️ 官方必须步骤：更新 sudo 脚本，否则后续安装可能失败"},
            ]
        },
        {
            "id": 8, "name": "OMS 安装",
            "icon": "🚀",
            "steps": [
                {"id": "install_oms_primary", "name": "安装主管理节点 OMS", "cmd": "cd /opt/FusionInsight_Manager/software && ./install.sh -f /opt/FusionInsight_Manager/software/install_oms/<oms_ip1>.ini",
                 "desc": "在主管理节点执行 OMS 安装，IP 为 oms_ip1"},
                {"id": "install_oms_standby", "name": "安装备管理节点 OMS", "cmd": "cd /opt/FusionInsight_Manager/software && ./install.sh -f /opt/FusionInsight_Manager/software/install_oms/<oms_ip2>.ini",
                 "desc": "在备管理节点执行 OMS 安装，需先修改 local_ip1 和 peer_ip1"},
                {"id": "verify_oms", "name": "验证 OMS 服务", "cmd": "echo '浏览器访问: https://<oms_float_ip>:28443/web 验证，admin/Admin@123'",
                 "desc": "首次登录需修改默认密码，确认 OMS 服务正常"},
            ]
        },
        {
            "id": 9, "name": "集群部署",
            "icon": "🌐",
            "steps": [
                {"id": "create_cluster", "name": "创建集群", "cmd": "echo '1. 登录 Manager GUI → 创建集群 → 模板安装\n2. 上传安装模板 xml → 发现节点 → 确认配置\n3. 勾选\"安装后启动集群\" → 提交'",
                 "desc": "通过 Manager Web GUI 创建集群，参见配置规划工具生成的模板"},
                {"id": "load_license", "name": "加载 License", "cmd": "echo '1. 登录 Manager → 系统 → License\n2. 记录 ESN 号 → 申请 License → 导入 → 激活'",
                 "desc": "生产环境必须加载 License，测试环境可跳过"},
                {"id": "numa_bind", "name": "NUMA 绑核", "cmd": "source /opt/huawei/Bigdata/mppdb/.mppdbgs_profile && gs_guc reload -Z coordinator -Z datanode -N all -I all -c \"enable_numa_bind=on\"",
                 "desc": "DWS部署V2.0 标准：启用 NUMA 绑核，提升 MPP 查询性能"},
                {"id": "cstore_buffers", "name": "列存缓存参数", "cmd": "source /opt/huawei/Bigdata/mppdb/.mppdbgs_profile && gs_guc set -N all -I all -Z coordinator -c \"cstore_buffers=2GB\" && gs_guc set -N all -I all -Z datanode -c \"cstore_buffers=16GB\" && cm_ctl stop && cm_ctl start",
                 "desc": "512GB 内存推荐值：coordinator=2GB, datanode=16GB；256G 则 1GB/8GB"},
                {"id": "query_dop", "name": "并行参数设置", "cmd": "source /opt/huawei/Bigdata/mppdb/.mppdbgs_profile && gs_guc reload -Z coordinator -Z datanode -N all -I all -c \"query_dop=0\" -c \"insert_dop=0\"",
                 "desc": "POC 环境开启并行查询（query_dop=0 表示自动并行）"},
            ]
        },
        {
            "id": 10, "name": "验收交付",
            "icon": "🏁",
            "steps": [
                {"id": "gsql_verify", "name": "gsql 连接验证", "cmd": "gsql -d postgres -p 25308 -c 'SELECT version();' -U root",
                 "desc": "验证数据库可达性，确认版本号正确"},
                {"id": "sql_func_test", "name": "SQL 功能验证", "cmd": "gsql -d postgres -p 25308 -c \"CREATE TABLE t(id int); INSERT INTO t VALUES(1); SELECT * FROM t; DROP TABLE t;\"",
                 "desc": "建表/插入/查询/删除功能验证"},
                {"id": "backup_verify", "name": "备份验证", "cmd": "gs_dump -U root -f /srv/BigData/LocalBackup/init.sql postgres",
                 "desc": "执行手动备份，确认备份文件生成于 LocalBackup"},
                {"id": "param_optimize", "name": "性能参数优化", "cmd": "echo '检查项: cstore_buffers/autovacuum/audit_enabled/query_dop\n性能测试建议关闭: autovacuum=off, audit_enabled=off, ssl=off'",
                 "desc": "性能测试前关闭 autovacuum/audit/ssl，测试完成后恢复"},
                {"id": "export_report", "name": "导出部署报告", "cmd": "echo '使用交付物页面导出: 预检报告 + 审计日志 + 验证报告 + 配置文件'",
                 "desc": "导出完整部署审计报告并打包交付物"},
            ]
        },
    ]
