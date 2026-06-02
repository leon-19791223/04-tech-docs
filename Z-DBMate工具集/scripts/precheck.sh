#!/bin/bash
# ============================================================
# Z-DBMate 部署前预检脚本 v2.0
# 适配 GaussDB 25.1.32 官方安装规范
#
# 检查项: 16项 (覆盖官方预检 + 新增6项)
#  基础: 1网络 2SSH 3OS 4磁盘数量 5磁盘挂载 6磁盘空间
#  系统: 7时钟 8内存 9CPU 10SELinux 11防火墙
#  增强: 12MD5校验 13audit版本 14runc 15libstdc++ 16MTU
#
# 用法: bash precheck.sh [node1 node2 node3 ...]
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

log_pass()  { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail()  { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_warn()  { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }
log_info()  { echo -e "  ${BLUE}[INFO]${NC} $1"; }

CONF_FILE="../conf/user_edit_file.conf"

if [ $# -eq 0 ]; then
    if [ -f "$CONF_FILE" ]; then
        log_info "从 $CONF_FILE 读取节点IP..."
        NODES=$(grep -E "^tpops_node|^gaussdb_node" "$CONF_FILE" \
                | grep -oP '=\s*\K[0-9.]+' | sort -u)
    else
        echo "用法: bash precheck.sh <node1> [node2] ..."
        echo "  或确保 conf/user_edit_file.conf 存在"
        exit 1
    fi
else
    NODES=("$@")
fi

echo ""
echo "============================================"
echo "  Z-DBMate 部署前环境预检 v2.0"
echo "  检查项: 16项 | 节点: $(echo $NODES | tr '\n' ' ')"
echo "============================================"
echo ""

# ============================================================
# 1. 本地工具检查
# ============================================================
echo "━━━ 1. 本地环境工具检查 ━━━"
for tool in ssh ping scp rsync; do
    command -v $tool >/dev/null 2>&1 \
        && log_pass "$tool 可用" \
        || log_fail "$tool 未安装"
done

# ============================================================
# 2. 节点网络可达性
# ============================================================
echo ""; echo "━━━ 2. 节点网络可达性 ━━━"
for node in $NODES; do
    ping -c1 -W3 $node >/dev/null 2>&1 \
        && log_pass "$node 可达" \
        || log_fail "$node 不可达"
done

# ============================================================
# 3. SSH免密登录
# ============================================================
echo ""; echo "━━━ 3. SSH免密登录 ━━━"
for node in $NODES; do
    ssh -o BatchMode=yes -o ConnectTimeout=5 $node "echo OK" 2>/dev/null \
        && log_pass "$node SSH免密登录成功" \
        || log_warn "$node 可能需要手动输入密码"
done

# ============================================================
# 4. 操作系统版本
# ============================================================
echo ""; echo "━━━ 4. 操作系统版本 ━━━"
for node in $NODES; do
    os_info=$(ssh $node "cat /etc/os-release 2>/dev/null | grep -E '^ID=|^VERSION=' | head -2" 2>/dev/null)
    if echo "$os_info" | grep -qi "kylin"; then
        log_pass "$node Kylin: $(echo $os_info | tr '\n' ' ')"
    else
        log_warn "$node 可能不是Kylin: $(echo $os_info | tr '\n' ' ')"
    fi
done

# ============================================================
# 5. 磁盘数量 (新增)
# ============================================================
echo ""; echo "━━━ 5. 磁盘数量 ━━━"
for node in $NODES; do
    disk_count=$(ssh $node "lsblk -d -o NAME 2>/dev/null | grep -cP '^sd|^nvme|^vd'" 2>/dev/null)
    if [ "$disk_count" -ge 6 ]; then
        log_pass "$node ${disk_count}块盘 (满足生产≥6要求)"
    elif [ "$disk_count" -ge 2 ]; then
        log_warn "$node ${disk_count}块盘 (仅满足测试≥2)"
    else
        log_fail "$node ${disk_count}块盘 (不满足最低需求)"
    fi
done

# ============================================================
# 6. 磁盘挂载检查 (适配官方9个目录)
# ============================================================
echo ""; echo "━━━ 6. 关键目录挂载检查 ━━━"
REQUIRED_DIRS=("/data /opt/cloud /opt/gaussdb /opt/sftphome /opt/backup /opt/docker /opt/influxdb /opt/cloud/logs")
for node in $NODES; do
    for dir in "${REQUIRED_DIRS[@]}"; do
        if ssh $node "df $dir" >/dev/null 2>&1; then
            mount_info=$(ssh $node "df -h $dir 2>/dev/null | tail -1" 2>/dev/null)
            log_pass "$node $dir 已挂载: $mount_info"
        else
            # 如果是/opt/下的目录，可能挂在同一个/opt下，降级为警告
            if echo "$dir" | grep -q "^/opt/"; then
                log_warn "$node $dir 未单独挂载（若在/opt下可忽略）"
            else
                log_fail "$node $dir 未挂载"
            fi
        fi
    done
done

# ============================================================
# 7. 时钟同步
# ============================================================
echo ""; echo "━━━ 7. 时钟同步 ━━━"
for node in $NODES; do
    sync_status=$(ssh $node "timedatectl show 2>/dev/null | grep ClockSynchronized" 2>/dev/null)
    if echo "$sync_status" | grep -q "yes"; then
        log_pass "$node 时钟已同步"
    else
        log_fail "$node 时钟未同步"
    fi
    # 检查时区是否为UTC
    tz=$(ssh $node "timedatectl | grep 'Time zone' | awk '{print \$3}'" 2>/dev/null)
    if [ "$tz" = "UTC" ] || [ "$tz" = "Etc/UTC" ]; then
        log_pass "$node 时区: UTC"
    else
        log_warn "$node 时区: $tz (推荐UTC)"
    fi
done

# ============================================================
# 8. 内存
# ============================================================
echo ""; echo "━━━ 8. 内存检查 ━━━"
for node in $NODES; do
    mem_total=$(ssh $node "free -g 2>/dev/null | grep Mem | awk '{print \$2}'" 2>/dev/null)
    if [ "$mem_total" -ge 32 ]; then
        log_pass "$node ${mem_total}GB (满足生产≥32GB)"
    elif [ "$mem_total" -ge 16 ]; then
        log_warn "$node ${mem_total}GB (仅满足测试≥16GB)"
    else
        log_fail "$node ${mem_total}GB (不满足≥16GB)"
    fi
done

# ============================================================
# 9. CPU
# ============================================================
echo ""; echo "━━━ 9. CPU检查 ━━━"
for node in $NODES; do
    cpu_cores=$(ssh $node "nproc 2>/dev/null" 2>/dev/null)
    if [ "$cpu_cores" -ge 16 ]; then
        log_pass "$node ${cpu_cores}核"
    else
        log_warn "$node ${cpu_cores}核 (推荐≥16核)"
    fi
done

# ============================================================
# 10. SELinux
# ============================================================
echo ""; echo "━━━ 10. SELinux ━━━"
for node in $NODES; do
    selinux=$(ssh $node "getenforce 2>/dev/null" 2>/dev/null)
    if [ "$selinux" = "Disabled" ] || [ "$selinux" = "Permissive" ]; then
        log_pass "$node SELinux: $selinux"
    else
        log_fail "$node SELinux: $selinux (需设置为Disabled/Permissive)"
    fi
done

# ============================================================
# 11. 防火墙
# ============================================================
echo ""; echo "━━━ 11. 防火墙 ━━━"
for node in $NODES; do
    firewall=$(ssh $node "systemctl is-active firewalld 2>/dev/null" 2>/dev/null)
    if [ "$firewall" = "inactive" ] || [ "$firewall" = "unknown" ]; then
        log_pass "$node firewalld: $firewall"
    else
        log_warn "$node firewalld active (需开放8002/40080端口)"
    fi
    # 检查iptables
    iptables_active=$(ssh $node "systemctl is-active iptables 2>/dev/null" 2>/dev/null)
    if [ "$iptables_active" = "active" ]; then
        log_pass "$node iptables: active"
    else
        log_warn "$node iptables: $iptables_active (官方要求开启)"
    fi
done

# ============================================================
# 12. MD5校验检查 (新增-官方重点要求)
# ============================================================
echo ""; echo "━━━ 12. 安装包MD5校验 ━━━"
if [ -f "$CONF_FILE" ]; then
    MD5_FILE=$(grep "^md5_checksum_file" "$CONF_FILE" 2>/dev/null | grep -oP '=\s*\K.*')
    if [ -n "$MD5_FILE" ] && [ -f "$MD5_FILE" ]; then
        log_info "找到MD5校验文件: $MD5_FILE"
        md5_result=$(cd $(dirname "$MD5_FILE") && md5sum -c $(basename "$MD5_FILE") 2>&1 | tail -5)
        if echo "$md5_result" | grep -qi "FAILED"; then
            log_fail "存在MD5校验失败的文件!"
            echo "$md5_result" | head -5 | while IFS= read -r line; do
                echo "    $line"
            done
        else
            log_pass "所有安装包MD5校验通过"
        fi
    else
        log_warn "未找到MD5校验文件 (跳过，但官方强烈建议执行此检查)"
    fi
fi

# ============================================================
# 13. audit版本检查 (新增-官方要求升级至.se.08)
# ============================================================
echo ""; echo "━━━ 13. audit版本检查 ━━━"
for node in $NODES; do
    audit_ver=$(ssh $node "rpm -qa audit 2>/dev/null | grep -v python" 2>/dev/null)
    if echo "$audit_ver" | grep -q "se.08"; then
        log_pass "$node audit: $audit_ver"
    elif echo "$audit_ver" | grep -q "se.06"; then
        log_fail "$node audit: $audit_ver (需升级到.se.08)"
    else
        log_info "$node audit: $audit_ver (确认状态)"
        # 检查是否开启
        audit_enabled=$(ssh $node "systemctl is-active auditd 2>/dev/null" 2>/dev/null)
        if [ "$audit_enabled" = "active" ]; then
            log_warn "$node auditd active (建议关闭)"
        fi
    fi
done

# ============================================================
# 14. runc检查 (新增-官方要求删除)
# ============================================================
echo ""; echo "━━━ 14. runc服务检查 ━━━"
for node in $NODES; do
    runc_path=$(ssh $node "which runc 2>/dev/null" 2>/dev/null)
    if [ -n "$runc_path" ]; then
        log_fail "$node 已安装runc: $runc_path (需删除: yum -y remove runc)"
    else
        log_pass "$node 未安装runc"
    fi
done

# ============================================================
# 15. libstdc++版本检查 (新增-麒麟OS特有)
# ============================================================
echo ""; echo "━━━ 15. libstdc++版本 ━━━"
for node in $NODES; do
    libstdcpp=$(ssh $node "yum list installed 2>/dev/null | grep libstdc++ | head -3" 2>/dev/null)
    if echo "$libstdcpp" | grep -q "7.3.0"; then
        log_pass "$node libstdc++: 7.3.0 (推荐版本)"
    else
        log_warn "$node libstdc++可能非7.3.0: $(echo "$libstdcpp" | head -1)"
        log_warn "  如安装GaussDB报错, 需降级: yum downgrade libstdc++"
    fi
done

# ============================================================
# 16. 网卡MTU检查 (新增)
# ============================================================
echo ""; echo "━━━ 16. 网卡MTU检查 ━━━"
for node in $NODES; do
    mtu=$(ssh $node "ip link | grep -E 'mtu' | head -3" 2>/dev/null)
    if echo "$mtu" | grep -q "mtu 1500"; then
        log_pass "$node MTU=1500"
    else
        log_warn "$node 部分网卡MTU非1500: $(echo "$mtu" | head -1)"
    fi
done

# ============================================================
# 汇总
# ============================================================
echo ""
echo "============================================"
echo -e "  预检结果汇总 (16项)"
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
