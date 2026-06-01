#!/bin/bash
# ============================================================
# Z-DBMate 一键部署封装脚本
# 支持 root / service 两种模式，免交互自动化部署
#
# 用法:
#   bash deploy.sh -m root -r "YourRootPass" -s "单节点TPOPS+三节点GaussDB"
#   bash deploy.sh -m service -s "服务名" -u service -g servicegroup -p "ServicePass"
#   bash deploy.sh -m root -s "仅TPOPS" -r "YourRootPass"
#   bash deploy.sh -m service -s "仅GaussDB" -p "ServicePass"
#   bash deploy.sh --check                # 仅预检
# ============================================================

set -e

# ---- 颜色 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; NC='\033[0m'
log_info()  { echo -e "${BLUE}[INFO]${NC} $1"; }
log_ok()    { echo -e "${GREEN}[OK]${NC} $1"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_err()   { echo -e "${RED}[ERR]${NC} $1"; }

# ---- 配置默认值 ----
Z_DBMATE_DIR="/data/Z-DBMate"
MODE="root"
ROOT_PASS=""
SERVICE_PASS=""
SERVICE_USER="service"
SERVICE_GROUP="servicegroup"
SERVICE_UID="1010"
SERVICE_GID="1010"
SCENARIO="main_install"  # main_install | install_tpops | prepare_gaussdb

# ---- 参数解析 ----
usage() {
    echo "用法: bash deploy.sh [选项]"
    echo "  -m <root|service>     执行模式 (默认: root)"
    echo "  -r <password>         root密码"
    echo "  -p <password>         service用户密码"
    echo "  -u <username>         service用户名 (默认: service)"
    echo "  -g <groupname>        service用户组 (默认: servicegroup)"
    echo "  -s <场景>              部署场景:"
    echo "       '单节点TPOPS+三节点GaussDB' (默认)"
    echo "       'HA TPOPS+三节点GaussDB'"
    echo "       '仅TPOPS'"
    echo "       '仅HA TPOPS'"
    echo "       '仅GaussDB'"
    echo "  --check               仅执行预检"
    echo "  -h                    帮助"
    exit 0
}

while [ $# -gt 0 ]; do
    case "$1" in
        -m) MODE="$2"; shift 2 ;;
        -r) ROOT_PASS="$2"; shift 2 ;;
        -p) SERVICE_PASS="$2"; shift 2 ;;
        -u) SERVICE_USER="$2"; shift 2 ;;
        -g) SERVICE_GROUP="$2"; shift 2 ;;
        -s) SCENARIO_INPUT="$2"; shift 2 ;;
        --check) bash precheck.sh; exit $? ;;
        -h|--help) usage ;;
        *) log_err "未知参数: $1"; usage ;;
    esac
done

# ---- 确定场景与配置文件 ----
case "$SCENARIO_INPUT" in
    "单节点TPOPS+三节点GaussDB"|"")
        CONF_TEMPLATE="single_tpops_gaussdb_user_edit_file.conf"
        CMD="./Z-DBMate main_install"
        ;;
    "HA TPOPS+三节点GaussDB")
        CONF_TEMPLATE="ha_tpops_gaussdb_user_edit_file.conf"
        CMD="./Z-DBMate main_install"
        ;;
    "仅TPOPS")
        CONF_TEMPLATE="single_tpops_user_edit_file.conf"
        CMD="./Z-DBMate install_tpops"
        ;;
    "仅HA TPOPS")
        CONF_TEMPLATE="ha_tpops_user_edit_file.conf"
        CMD="./Z-DBMate install_tpops"
        ;;
    "仅GaussDB")
        CONF_TEMPLATE="prepare_gaussdb_user_edit_file.conf"
        CMD="./Z-DBMate prepare_gaussdb"
        ;;
    *)
        log_err "未知场景: $SCENARIO_INPUT"
        usage
        ;;
esac

# ---- 前置预检 ----
echo ""
echo "============================================"
echo "  Z-DBMate 一键部署"
echo "  模式: $MODE | 场景: $SCENARIO_INPUT"
echo "============================================"
echo ""

# 检查 Z-DBMate 目录
if [ ! -d "$Z_DBMATE_DIR" ]; then
    log_err "未找到 Z-DBMate 目录: $Z_DBMATE_DIR"
    log_info "请先上传并解压 Z-DBMate 工具包"
    exit 1
fi
cd "$Z_DBMATE_DIR"

# ---- 复制配置文件 ----
log_info "使用模板: $CONF_TEMPLATE"
cp "conf/$CONF_TEMPLATE" "conf/user_edit_file.conf"
log_ok "配置文件已就绪: conf/user_edit_file.conf"
echo "  请先编辑配置文件中的IP地址: vi conf/user_edit_file.conf"
read -p "  是否已完成配置？(y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    log_warn "请先完成配置后再运行"
    exit 1
fi

# ---- 执行预检 ----
log_info "执行部署前预检..."
bash "$(dirname $0)/precheck.sh" || {
    log_err "预检未通过，请修复后重试"
    exit 1
}

# ---- 执行部署 ----
deploy_root() {
    log_info "root模式部署中..."
    if [ -n "$ROOT_PASS" ]; then
        echo "$ROOT_PASS" | $CMD
    else
        log_info "等待输入root密码..."
        $CMD
    fi
}

deploy_service() {
    log_info "service模式部署中..."

    # 创建 service 用户
    for node in $(grep -E "^tpops_ip|^gaussdb_ip" conf/user_edit_file.conf \
                  | grep -oP '=\s*\K[0-9.]+' | sort -u); do
        log_info "配置 $node service用户..."
        ssh "$node" "
            groupadd -g $SERVICE_GID $SERVICE_GROUP 2>/dev/null || true
            useradd -u $SERVICE_UID -g $SERVICE_GID $SERVICE_USER 2>/dev/null || true
        " 2>/dev/null || log_warn "无法远程配置 $node（可能是root模式下无需此步）"
    done

    if [ -n "$SERVICE_PASS" ]; then
        echo "$SERVICE_PASS" | $CMD
    else
        log_info "等待输入service密码..."
        $CMD
    fi
}

case "$MODE" in
    root)   deploy_root ;;
    service) deploy_service ;;
    *)      log_err "未知模式: $MODE"; exit 1 ;;
esac

# ---- 后续指引 ----
echo ""
echo "============================================"
echo -e "  ${GREEN}部署完成！${NC}"
echo "============================================"

case "$SCENARIO_INPUT" in
    *GaussDB*|"")
        echo "  后续步骤:"
        echo "  1. 登录 TPOPS: https://<Web-ip>:8002/gaussdb/"
        echo "  2. 添加主机 → 安装实例"
        ;;
    "仅TPOPS"|"仅HA TPOPS")
        echo "  TPOPS 安装完毕"
        echo "  如需安装 GaussDB，请运行:"
        echo "    bash deploy.sh -m $MODE -s '仅GaussDB'"
        ;;
    "仅GaussDB")
        echo "  GaussDB 环境已准备"
        echo "  请登录 TPOPS 安装实例"
        ;;
esac
echo "============================================"
echo ""
