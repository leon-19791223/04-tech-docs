#!/bin/bash
# ============================================================
# Z-DBMate 部署前预检脚本
# 在正式部署前统一排查环境问题，避免运行时故障
# 用法: bash precheck.sh [node1 node2 node3 ...]
#       如不传节点，默认读取 user_edit_file.conf 中的 IP
# ============================================================

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

PASS=0
FAIL=0
WARN=0

log_pass()  { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail()  { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_warn()  { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }
log_info()  { echo -e "  ${BLUE}[INFO]${NC} $1"; }

# ---- 解析节点列表 ----
if [ $# -eq 0 ]; then
    if [ -f "../conf/user_edit_file.conf" ]; then
        log_info "从 user_edit_file.conf 读取节点IP..."
        NODES=$(grep -E "^tpops_ip|^gaussdb_ip" ../conf/user_edit_file.conf \
                | grep -oP '=\s*\K[0-9.]+' | sort -u)
    else
        echo "用法: bash precheck.sh <node1> [node2] [node3] ..."
        echo "  或: cd conf/ 目录下存在 user_edit_file.conf 时无需传参"
        exit 1
    fi
else
    NODES=("$@")
fi

echo ""
echo "============================================"
echo "  Z-DBMate 部署前环境预检"
echo "  检查节点: $(echo $NODES | tr '\n' ' ')"
echo "============================================"
echo ""

# ---- 1. 本地环境检查 ----
echo "━━━ 1. 本地环境检查 ━━━"
for tool in ssh ping scp; do
    command -v $tool >/dev/null 2>&1 \
        && log_pass "$tool 可用" \
        || log_fail "$tool 未安装"
done

# ---- 2. 节点可达性 ----
echo ""
echo "━━━ 2. 节点网络可达性 ━━━"
for node in $NODES; do
    ping -c1 -W3 $node >/dev/null 2>&1 \
        && log_pass "$node 可达" \
        || log_fail "$node 不可达"
done

# ---- 3. SSH免密登录 ----
echo ""
echo "━━━ 3. SSH免密登录 ━━━"
for node in $NODES; do
    ssh -o BatchMode=yes -o ConnectTimeout=5 $node "echo OK" 2>/dev/null \
        && log_pass "$node SSH免密登录成功" \
        || log_warn "$node SSH免密登录失败（可能需手动输入密码）"
done

# ---- 4. 操作系统版本 ----
echo ""
echo "━━━ 4. 操作系统版本 ━━━"
for node in $NODES; do
    os_info=$(ssh $node "cat /etc/os-release 2>/dev/null | grep -E '^ID=|^VERSION=' | head -2" 2>/dev/null)
    if echo "$os_info" | grep -qi "kylin"; then
        log_pass "$node 系统: $(echo $os_info | tr '\n' ' ')"
    else
        log_warn "$node 可能不是Kylin系统: $(echo $os_info | tr '\n' ' ')"
    fi
done

# ---- 5. 磁盘检查 ----
echo ""
echo "━━━ 5. 磁盘挂载与空间 ━━━"
for node in $NODES; do
    data_mounted=$(ssh $node "df -h /data 2>/dev/null | tail -1" 2>/dev/null)
    if [ -n "$data_mounted" ]; then
        log_pass "$node /data 已挂载: $data_mounted"
    else
        log_fail "$node /data 未挂载或不存在"
    fi

    disk_count=$(ssh $node "lsblk -d -o NAME 2>/dev/null | grep -cP '^\w+$'" 2>/dev/null)
    if [ "$disk_count" -ge 6 ]; then
        log_pass "$node 磁盘数量: $disk_count (满足生产环境≥6要求)"
    elif [ "$disk_count" -ge 2 ]; then
        log_warn "$node 磁盘数量: $disk_count (仅满足测试环境≥2要求)"
    else
        log_fail "$node 磁盘数量: $disk_count (不满足最低要求)"
    fi
done

# ---- 6. 时钟同步 ----
echo ""
echo "━━━ 6. 时钟同步状态 ━━━"
for node in $NODES; do
    sync_status=$(ssh $node "timedatectl show 2>/dev/null | grep ClockSynchronized" 2>/dev/null)
    if echo "$sync_status" | grep -q "yes"; then
        log_pass "$node 时钟已同步"
    else
        log_fail "$node 时钟未同步"
    fi
done

# ---- 7. 内存 ----
echo ""
echo "━━━ 7. 内存检查 ━━━"
for node in $NODES; do
    mem_total=$(ssh $node "free -g 2>/dev/null | grep Mem | awk '{print \$2}'" 2>/dev/null)
    if [ "$mem_total" -ge 16 ]; then
        log_pass "$node 内存: ${mem_total}GB"
    elif [ "$mem_total" -ge 8 ]; then
        log_warn "$node 内存: ${mem_total}GB (建议≥16GB)"
    else
        log_fail "$node 内存: ${mem_total}GB (不满足需求)"
    fi
done

# ---- 8. CPU ----
echo ""
echo "━━━ 8. CPU检查 ━━━"
for node in $NODES; do
    cpu_cores=$(ssh $node "nproc 2>/dev/null" 2>/dev/null)
    if [ "$cpu_cores" -ge 16 ]; then
        log_pass "$node CPU核心数: $cpu_cores"
    else
        log_warn "$node CPU核心数: $cpu_cores"
    fi
done

# ---- 9. yum源 ----
echo ""
echo "━━━ 9. yum源检查 ━━━"
for node in $NODES; do
    if ssh $node "yum makecache -q --timeout 10" >/dev/null 2>&1; then
        log_pass "$node yum源可用"
    else
        log_fail "$node yum源不可用（部署前需解决）"
    fi
done

# ---- 10. SELinux & Firewall ----
echo ""
echo "━━━ 10. 系统配置检查 ━━━"
for node in $NODES; do
    selinux=$(ssh $node "getenforce 2>/dev/null" 2>/dev/null)
    if [ "$selinux" = "Disabled" ] || [ "$selinux" = "Permissive" ]; then
        log_pass "$node SELinux: $selinux"
    else
        log_fail "$node SELinux: $selinux (需设置为Disabled或Permissive)"
    fi

    firewall=$(ssh $node "systemctl is-active firewalld 2>/dev/null" 2>/dev/null)
    if [ "$firewall" = "inactive" ] || [ "$firewall" = "unknown" ]; then
        log_pass "$node firewalld: $firewall"
    else
        log_warn "$node firewalld: $firewall（建议关闭或开放所需端口）"
    fi
done

# ---- 汇总 ----
echo ""
echo "============================================"
echo -e "  预检结果汇总"
echo "============================================"
echo -e "  ${GREEN}通过: $PASS${NC}"
echo -e "  ${YELLOW}警告: $WARN${NC}"
echo -e "  ${RED}失败: $FAIL${NC}"
echo "============================================"

if [ "$FAIL" -gt 0 ]; then
    echo -e "${RED}  存在 $FAIL 项失败，请在部署前修复！${NC}"
    exit 1
else
    echo -e "${GREEN}  全部通过，可以开始部署！${NC}"
fi
echo "============================================"
echo ""
