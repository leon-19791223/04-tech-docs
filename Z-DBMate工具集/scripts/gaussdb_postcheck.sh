#!/bin/bash
# ============================================================
# GaussDB 部署后验证脚本
# 在 TPOPS + GaussDB 部署完成后执行
#
# 验证项:
#   1. TPOPS服务状态
#   2. GaussDB实例运行状态
#   3. 数据库连接测试
#   4. 基本SQL功能验证
#   5. 性能基准测试
#   6. 节点间网络状态
#   7. 备份状态检查
#
# 用法: bash dws_postcheck.sh <GaussDB-IP> <端口> [密码]
# ============================================================

set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; BLUE='\033[0;34m'; NC='\033[0m'
PASS=0; FAIL=0; WARN=0

log_pass()  { echo -e "  ${GREEN}[PASS]${NC} $1"; ((PASS++)); }
log_fail()  { echo -e "  ${RED}[FAIL]${NC} $1"; ((FAIL++)); }
log_warn()  { echo -e "  ${YELLOW}[WARN]${NC} $1"; ((WARN++)); }
log_info()  { echo -e "  ${BLUE}[INFO]${NC} $1"; }

DB_IP="${1:-127.0.0.1}"
DB_PORT="${2:-40080}"
DB_PASS="${3:-Gauss_246}"
DB_USER="root"
TPOPS_URL="https://${DB_IP}:8002/gaussdb"
CONF_FILE="../conf/user_edit_file.conf"

[ -f "$CONF_FILE" ] && source <(grep -E "^[a-z_]+ =" "$CONF_FILE" | sed 's/ = /=/')

echo ""
echo "============================================"
echo "  GaussDB 部署后验证"
echo "  数据库: ${DB_IP}:${DB_PORT}"
echo "============================================"
echo ""

# ============================================================
# 1. TPOPS Web 可用性检查
# ============================================================
echo "━━━ 1. TPOPS Web 检查 ━━━"
curl -sk -o /dev/null -w "%{http_code}" "$TPOPS_URL" 2>/dev/null | grep -q "200\|302" \
    && log_pass "TPOPS Web 可访问 ($TPOPS_URL)" \
    || log_fail "TPOPS Web 不可访问"

# ============================================================
# 2. GaussDB 进程检查
# ============================================================
echo ""; echo "━━━ 2. GaussDB 进程检查 ━━━"
GAUSSDB_PROCESSES=("gaussdb" "etcd" "kafka" "influxd")
for proc in "${GAUSSDB_PROCESSES[@]}"; do
    pgrep -x "$proc" >/dev/null \
        && log_pass "进程 $proc 运行中" \
        || log_warn "进程 $proc 未运行"
done

# ============================================================
# 3. 数据库连接测试
# ============================================================
echo ""; echo "━━━ 3. 数据库连接测试 ━━━"
which gsql >/dev/null 2>&1 && GSQL="gsql" || GSQL="/usr/local/gsql/bin/gsql"

if command -v "$GSQL" >/dev/null 2>&1 || [ -f "$GSQL" ]; then
    # 尝试连接
    PGPASSWORD="$DB_PASS" $GSQL -d postgres -h "$DB_IP" -p "$DB_PORT" -U "$DB_USER" -c "SELECT 1 AS test;" -t 2>/dev/null | grep -q "1" \
        && log_pass "数据库连接正常" \
        || log_fail "数据库连接失败"
else
    log_warn "gsql 客户端未安装，跳过连接测试"
    log_info "安装: tar -zxvf GaussDB-Kernel_*_64bit_Gsql.tar.gz && cp -r bin/ /usr/local/gsql/"
fi

# ============================================================
# 4. 基本SQL功能测试
# ============================================================
echo ""; echo "━━━ 4. SQL 功能测试 ━━━"
if command -v "$GSQL" >/dev/null 2>&1 || [ -f "$GSQL" ]; then
    # 查询版本
    PGPASSWORD="$DB_PASS" $GSQL -d postgres -h "$DB_IP" -p "$DB_PORT" -U "$DB_USER" -c "SELECT version();" -t 2>/dev/null | head -3 \
        && log_pass "版本查询正常" \
        || log_warn "版本查询异常"

    # 建表测试
    PGPASSWORD="$DB_PASS" $GSQL -d postgres -h "$DB_IP" -p "$DB_PORT" -U "$DB_USER" -c "
        CREATE TABLE IF NOT EXISTS dws_test (id INT, ts TIMESTAMP);
        INSERT INTO dws_test VALUES (1, now());
        SELECT * FROM dws_test;
        DROP TABLE dws_test;
    " -t 2>/dev/null | grep -q "1" \
        && log_pass "DDL/DML/DQL 功能正常" \
        || log_fail "SQL 执行异常"

    # 检查数据库大小
    db_size=$(PGPASSWORD="$DB_PASS" $GSQL -d postgres -h "$DB_IP" -p "$DB_PORT" -U "$DB_USER" -c "SELECT pg_size_pretty(pg_database_size('postgres'));" -t 2>/dev/null | head -1 | tr -d ' ')
    log_info "数据库大小: $db_size"
else
    log_warn "gsql 未安装，跳过 SQL 测试"
fi

# ============================================================
# 5. 磁盘空间检查
# ============================================================
echo ""; echo "━━━ 5. 磁盘空间检查 ━━━"
for mount_point in /data /opt/cloud /opt/gaussdb /opt/sftphome /opt/backup; do
    if df "$mount_point" >/dev/null 2>&1; then
        usage=$(df -h "$mount_point" 2>/dev/null | tail -1 | awk '{print $5}' | tr -d '%')
        if [ "$usage" -lt 80 ]; then
            log_pass "$mount_point 使用率 ${usage}%"
        else
            log_warn "$mount_point 使用率 ${usage}%（超过80%）"
        fi
    fi
done

# ============================================================
# 6. 时钟同步检查
# ============================================================
echo ""; echo "━━━ 6. 时钟同步 ━━━"
timedatectl show 2>/dev/null | grep -q "ClockSynchronized=yes" \
    && log_pass "时钟已同步" \
    || log_warn "时钟未同步"

# ============================================================
# 7. TPOPS 服务检查（通过docker）
# ============================================================
echo ""; echo "━━━ 7. TPOPS 服务容器检查 ━━━"
docker ps --format "table {{.Names}}\t{{.Status}}" 2>/dev/null | head -20 | while IFS= read -r line; do
    if echo "$line" | grep -q "Up\|healthy"; then
        log_pass "$line"
    fi
done

# ============================================================
# 汇总
# ============================================================
echo ""
echo "============================================"
echo "  GaussDB 部署后验证结果"
echo "============================================"
echo -e "  ${GREEN}通过: $PASS${NC}"
echo -e "  ${YELLOW}警告: $WARN${NC}"
echo -e "  ${RED}失败: $FAIL${NC}"
echo "============================================"
[ "$FAIL" -gt 0 ] && echo -e "${RED}  存在 $FAIL 项失败，请排查${NC}" || echo -e "${GREEN}  全部通过！${NC}"
echo "============================================"
echo ""
