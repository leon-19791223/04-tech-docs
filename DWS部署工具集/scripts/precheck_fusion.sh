#!/bin/bash
# ============================================================
# DWS FusionInsight 部署预检脚本
# 基于 DWS 9.1.0 / Kylin V10 SP3 / ARM (鲲鹏920)
# 检查项: 15项 (硬件5 + OS6 + 存储2 + 软件2)
#
# 用法: bash precheck_fusion.sh [node1 node2 ...]
# ============================================================

set -e
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0
log_pass() { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail() { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_warn() { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }
log_info() { echo -e "  ${BLUE}[INFO]${NC} $1"; }

NODES=("$@")
[ $# -eq 0 ] && echo "用法: bash precheck_fusion.sh <node1> [node2] ..." && exit 1

echo "============================================"
echo "  DWS FusionInsight 预检 (${#NODES[@]}节点)"
echo "============================================"

# 1. RAID策略
echo ""; echo "━━━ 1. RAID策略 ━━━"
for node in "${NODES[@]}"; do
    raid_tool=$(ssh $node "which storcli64 2>/dev/null | head -1" 2>/dev/null)
    [ -n "$raid_tool" ] && log_pass "$node RAID工具已安装" || log_warn "$node 未安装RAID管理工具"
done

# 2. 磁盘数量
echo ""; echo "━━━ 2. 磁盘数量 ━━━"
for node in "${NODES[@]}"; do
    dc=$(ssh $node "lsblk -d -o NAME 2>/dev/null | grep -cP '^sd|^nvme|^vd'" 2>/dev/null)
    [ "$dc" -ge 6 ] && log_pass "$node ${dc}块盘" || log_warn "$node ${dc}块盘(建议≥6)"
done

# 3. 网卡
echo ""; echo "━━━ 3. 网卡检查 ━━━"
for node in "${NODES[@]}"; do
    speed=$(ssh $node "ethtool \$(ls /sys/class/net | grep -v lo | head -1) 2>/dev/null | grep Speed" 2>/dev/null)
    mtu=$(ssh $node "ip link | grep -o 'mtu [0-9]*' | head -1" 2>/dev/null)
    log_pass "$node $speed, $mtu"
done

# 4. SSD
echo ""; echo "━━━ 4. SSD检查 ━━━"
for node in "${NODES[@]}"; do
    rota=$(ssh $node "lsblk -d -o NAME,ROTA | grep -v sr0 | grep '1$' | wc -l" 2>/dev/null)
    [ "$rota" -eq 0 ] && log_pass "$node 全部SSD" || log_warn "$node 有${rota}块HDD"
done

# 5. audit
echo ""; echo "━━━ 5. audit服务 ━━━"
for node in "${NODES[@]}"; do
    s=$(ssh $node "systemctl is-active auditd 2>/dev/null" 2>/dev/null)
    [ "$s" = "inactive" ] || [ "$s" = "unknown" ] && log_pass "$node audit已关闭" || log_fail "$node audit运行中"
done

# 6. 防火墙
echo ""; echo "━━━ 6. 防火墙 ━━━"
for node in "${NODES[@]}"; do
    fw=$(ssh $node "systemctl is-active firewalld 2>/dev/null" 2>/dev/null)
    ip=$(ssh $node "systemctl is-active iptables 2>/dev/null" 2>/dev/null)
    [ "$fw" = "inactive" ] && log_pass "$node firewalld关闭" || log_fail "$node firewalld运行中"
    [ "$ip" = "active" ] && log_pass "$node iptables运行中" || log_warn "$node iptables未开启"
done

# 7. SELinux
echo ""; echo "━━━ 7. SELinux ━━━"
for node in "${NODES[@]}"; do
    se=$(ssh $node "getenforce 2>/dev/null" 2>/dev/null)
    [ "$se" = "Disabled" ] && log_pass "$node SELinux已关闭" || log_warn "$node SELinux=$se"
done

# 8. swap
echo ""; echo "━━━ 8. swap ━━━"
for node in "${NODES[@]}"; do
    sw=$(ssh $node "swapon --show | wc -l" 2>/dev/null)
    [ "$sw" -eq 0 ] && log_pass "$node swap已关闭" || log_fail "$node swap未关闭"
done

# 9. 透明大页
echo ""; echo "━━━ 9. 透明大页 ━━━"
for node in "${NODES[@]}"; do
    thp=$(ssh $node "cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null" 2>/dev/null)
    echo "$thp" | grep -q "never" && log_pass "$node 透明大页已关闭" || log_fail "$node 透明大页未关闭"
done

# 10. 时区
echo ""; echo "━━━ 10. 时区 ━━━"
for node in "${NODES[@]}"; do
    tz=$(ssh $node "timedatectl | grep 'Time zone' | awk '{print \$3}'" 2>/dev/null)
    [ "$tz" = "Asia/Shanghai" ] && log_pass "$node 时区=$tz" || log_fail "$node 时区=$tz(需Asia/Shanghai)"
done

# 11. 内核参数
echo ""; echo "━━━ 11. 内核参数 ━━━"
for node in "${NODES[@]}"; do
    wm=$(ssh $node "sysctl -n vm.watermark_scale_factor 2>/dev/null" 2>/dev/null)
    nm=$(ssh $node "sysctl -n kernel.numa_balancing 2>/dev/null" 2>/dev/null)
    [ "$wm" = "100" ] && log_pass "$node watermark_scale_factor=$wm" || log_warn "$node watermark_scale_factor=$wm(需100)"
    [ "$nm" = "0" ] && log_pass "$node numa_balancing=$nm" || log_warn "$node numa_balancing=$nm(需0)"
done

# 12. 磁盘挂载
echo ""; echo "━━━ 12. 磁盘挂载 ━━━"
for node in "${NODES[@]}"; do
    for dir in /srv/BigData/dbdata_om /srv/BigData/LocalBackup /srv/BigData/mppdb/data1 /srv/BigData/mppdb/data2; do
        ssh $node "df $dir" >/dev/null 2>&1 && log_pass "$node $dir 已挂载" || log_warn "$node $dir 未挂载"
    done
done

# 13. /etc/fstab
echo ""; echo "━━━ 13. fstab持久化 ━━━"
for node in "${NODES[@]}"; do
    ssh $node "grep -q /srv/BigData /etc/fstab 2>/dev/null" && log_pass "$node fstab已配置" || log_fail "$node fstab未配置"
done

# 14. Python
echo ""; echo "━━━ 14. Python ━━━"
for node in "${NODES[@]}"; do
    py=$(ssh $node "python3.8 --version 2>/dev/null || python3 --version 2>/dev/null" 2>/dev/null)
    log_pass "$node $py"
done

# 15. yum源
echo ""; echo "━━━ 15. yum源 ━━━"
for node in "${NODES[@]}"; do
    ssh $node "yum list installed gcc" >/dev/null 2>&1 && log_pass "$node yum可用" || log_fail "$node yum不可用"
done

echo ""; echo "============================================"
echo "  汇总: 通过=$PASS 警告=$WARN 失败=$FAIL"
echo "============================================"
[ "$FAIL" -gt 0 ] && exit 1 || echo -e "${GREEN}全部通过${NC}"
