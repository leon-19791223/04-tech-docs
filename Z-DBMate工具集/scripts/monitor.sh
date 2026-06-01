#!/bin/bash
# ============================================================
# Z-DBMate 部署进度监控脚本
# 实时监控标记文件 + 日志异常告警
#
# 用法:
#   bash monitor.sh                          # 监控当前部署进度
#   bash monitor.sh /data/Z-DBMate/deploy.log # 指定日志文件
#   bash monitor.sh --tail                   # 持续监控
#   bash monitor.sh --once                   # 一次性检查
# ============================================================

set -e

MARKER_DIR="/data/Z-DBMate/temp/markerFile"
LOG_FILE="${1:-/data/Z-DBMate/deploy.log}"
WATCH_MODE="tail"
REFRESH_INTERVAL=5

# ---- 解析参数 ----
for arg in "$@"; do
    case "$arg" in
        --tail) WATCH_MODE="tail" ;;
        --once) WATCH_MODE="once" ;;
    esac
done

# ---- 标记文件映射 ----
declare -A MARKER_MAP=(
    ["deploy_yum_done"]="yum仓库配置完成"
    ["install_lib_done"]="依赖包安装完成"
    ["modify_config_done"]="系统配置修改完成"
    ["build_python3_done"]="Python 3.7.9 安装完成"
)

MARKER_ORDER=("deploy_yum_done" "install_lib_done" "modify_config_done" "build_python3_done")

# ---- 颜色 ----
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; NC='\033[0m'

draw_dashboard() {
    clear
    echo ""
    echo "============================================"
    echo -e "  ${BOLD}Z-DBMate 部署进度监控${NC}"
    echo "  日志: $LOG_FILE"
    echo "  $(date '+%Y-%m-%d %H:%M:%S')"
    echo "============================================"
    echo ""

    # ---- 标记文件进度 ----
    echo "━━━ 执行进度 ━━━"
    current_step=0
    total_steps=${#MARKER_ORDER[@]}

    for marker in "${MARKER_ORDER[@]}"; do
        if [ -f "$MARKER_DIR/$marker" ]; then
            echo -e "  ${GREEN}✅${NC} ${MARKER_MAP[$marker]}"
            ((current_step++))
        else
            echo -e "  ⏳ ${MARKER_MAP[$marker]}"
            break
        fi
    done

    # ---- 进度条 ----
    pct=$(( current_step * 100 / total_steps ))
    bar_len=30
    filled=$(( pct * bar_len / 100 ))
    empty=$(( bar_len - filled ))

    printf "\n  ["
    for i in $(seq 1 $filled); do printf "${GREEN}█${NC}"; done
    for i in $(seq 1 $empty); do printf "░"; done
    printf "] %d%%\n\n" $pct

    # ---- 错误检测 ----
    if [ -f "$LOG_FILE" ]; then
        errors=$(grep -c -i "error\|fatal\|fail\|traceback" "$LOG_FILE" 2>/dev/null || echo 0)
        warnings=$(grep -c -i "warn\|注意\|异常" "$LOG_FILE" 2>/dev/null || echo 0)

        echo "━━━ 日志统计 ━━━"
        echo -e "  错误: ${RED}$errors${NC}"
        echo -e "  警告: ${YELLOW}$warnings${NC}"

        if [ "$errors" -gt 0 ]; then
            echo ""
            echo -e "${RED}  最近错误:${NC}"
            grep -i "error\|fatal\|fail\|traceback" "$LOG_FILE" | tail -3 | \
                while IFS= read -r line; do
                    echo -e "    ${RED}->${NC} ${line:0:120}"
                done
        fi
    fi

    # ---- 磁盘与内存 ----
    echo ""
    echo "━━━ 系统资源 ━━━"
    df -h /data 2>/dev/null | tail -1 | awk '{printf "  /data: 已用 %s / 总量 %s (%s)\n", $3, $2, $5}'
    free -h 2>/dev/null | grep Mem | awk '{printf "  内存: 已用 %s / 总量 %s\n", $3, $2}'
}

# ---- 主循环 ----
case "$WATCH_MODE" in
    once)
        draw_dashboard
        ;;
    tail)
        while true; do
            draw_dashboard

            # 检查是否全部完成
            all_done=true
            for marker in "${MARKER_ORDER[@]}"; do
                if [ ! -f "$MARKER_DIR/$marker" ]; then
                    all_done=false
                    break
                fi
            done

            if $all_done; then
                echo ""
                echo -e "${GREEN}━━━ 所有步骤已完成！━━━${NC}"
                echo ""
                exit 0
            fi

            sleep "$REFRESH_INTERVAL"
        done
        ;;
esac
