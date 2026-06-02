# DWS 部署流程文档

> 适用于 DWS 8.x / 9.x MPP 集群，基于 FusionInsight Manager

## 一、部署流程图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DWS 部署流程（7阶段）                            │
├─────────┬─────────┬─────────┬─────────┬─────────┬─────────┬───────────┤
│ 环境准备 │ OS配置  │ 磁盘分区 │ 软件安装 │ 集群部署 │ 性能测试 │ 验收交付  │
│ RAID/BIOS│ 内核参数 │ LVM分区  │ Python  │ F.I.Setup│ fio/dd  │ 功能验证  │
│ 网络检查 │ 时钟同步 │ 格式化   │ 依赖包   │ 初始化   │ 网络压测 │ 备份配置  │
│ 主机名   │ SELinux  │ 挂载点   │ ISO镜像  │ 安装集群 │ 参数调优 │ 交付文档  │
└─────────┴─────────┴─────────┴─────────┴─────────┴─────────┴───────────┘
```

## 二、各阶段要点

### Phase 1: 环境准备

| 检查项 | 要求 | 验证命令 |
|--------|------|---------|
| RAID策略 | Read Ahead + Write Back With BBU | IBMC界面查看 |
| 网卡 | 25GE, Hi1822需单独处理 | `ethtool <网卡名>` |
| MTU | 1500 | `ip link` |
| 主机名 | 每节点唯一 | `hostname` |
| /etc/hosts | FusionInsight自动生成 | 无需手工配 |
| ISO镜像 | Kylin-Server-V10-SP2-aarch64 | `ls /Kylin-*.iso` |
| root密码 | 所有节点一致 | SSH测试 |

### Phase 2: OS 配置

```bash
# 关闭 audit
systemctl stop auditd.service
systemctl disable auditd.service

# 关闭防火墙
systemctl stop firewalld iptables
systemctl disable firewalld iptables

# 关闭 SELinux
sed -i 's/SELINUX=enforcing/SELINUX=disabled/' /etc/selinux/config

# 关闭 swap
swapoff -a
# 注释 /etc/fstab 中 swap 行

# 关闭透明大页
vi /etc/default/grub  # 追加 transparent_hugepage=never
grub2-mkconfig -o /boot/efi/EFI/kylin/grub.cfg

# 设置时区 (注意: DWS 需 Asia/Shanghai)
timedatectl set-timezone Asia/Shanghai

# 字符集
echo 'LANG="en_US.UTF-8"' > /etc/locale.conf

# 内核参数
sysctl -w vm.watermark_scale_factor=100
sysctl -w kernel.numa_balancing=0

# 内存水位线优化
echo 'vm.watermark_scale_factor = 100' >> /etc/sysctl.conf
echo 'kernel.numa_balancing = 0' >> /etc/sysctl.conf
```

### Phase 3: 磁盘分区

```bash
# 查看磁盘
lsblk

# parted 分区
parted -s /dev/sdb mklabel gpt
parted -s /dev/sdb mkpart logic xfs 100M 320GB
parted -s /dev/sdb mkpart logic xfs 320GB 100%

# 格式化
mkfs.xfs -f /dev/sdb1
mkfs.xfs -f /dev/sdb2

# 挂载目录
mkdir -p /srv/BigData/dbdata_om
mkdir -p /srv/BigData/LocalBackup
mkdir -p /srv/BigData/mppdb/data1
mkdir -p /srv/BigData/mppdb/data2

# /etc/fstab 配置 (使用 blkid 获取 UUID)
UUID=xxx /srv/BigData/dbdata_om xfs defaults,noatime,nodiratime 1 0
UUID=xxx /srv/BigData/LocalBackup xfs defaults,noatime,nodiratime 1 0
UUID=xxx /srv/BigData/mppdb/data1 xfs defaults,noatime,nodiratime 1 0
UUID=xxx /srv/BigData/mppdb/data2 xfs defaults,noatime,nodiratime 1 0

mount -a
```

### Phase 4: 软件环境

```bash
# Python 3.8.5 (DWS 8.x 必需)
./configure --enable-optimizations --prefix=/usr/local
make -j4 && make altinstall

# 依赖包
yum install -y gcc patch libffi-devel python-devel zlib-devel \
  bzip2-devel openssl-devel ncurses-devel sqlite-devel \
  readline-devel tk-devel gdbm-devel libpcap-devel xz-devel

# 挂载 ISO
mount /opt/Kylin-*.iso /media -o loop
# 配置 local yum 源
```

### Phase 5: 集群安装

按 FusionInsight_SetupTool 向导执行。

### Phase 6: 性能测试

```bash
# fio 磁盘测试
./fio_arm -directory=/srv/BigData/mppdb/data1 -direct=1 \
  -thread -rw=write -ioengine=psync -bs=8k -size=6G \
  -numjobs=10 -runtime=120 -group_reporting -name=etcdiotest

# 网络压测
./speed_test send <接收端ip> 10001 tcp
# 带宽应 ≥800MB/s (10GE)，重传率 <0.01%
```

### Phase 7: 验收交付

参考 `DWS_DELIVERY_CHECKLIST.md` 逐项确认。

## 三、常见问题

### Q1: 时区检查失败
DWS 要求 Asia/Shanghai 时区，GaussDB OLTP 要求 UTC。  
`timedatectl set-timezone Asia/Shanghai`

### Q2: Hi1822 网卡性能问题  
需用 hinicconfig 增加中断个数

### Q3: audit 必须关闭  
`systemctl disable auditd.service`

### Q4: 磁盘 SSD 检查  
`lsblk -d -o name,rota` → ROTA=0 才是 SSD
