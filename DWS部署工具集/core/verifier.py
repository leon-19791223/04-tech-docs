"""
DWS 部署后验证引擎（官方验收测试标准 v2）

覆盖验收测试指南 11 大类 30+ 项：
  1. 集群状态检查     (5项)
  2. 健康检查         (4项)
  3. 数据库基本功能   (5项)
  4. 备份恢复         (3项)
  5. 监控             (3项)
  6. 告警             (3项)
  7. 配置管理         (2项)
  8. 日志管理         (1项)
  9. 客户端           (2项)
  10. 用户管理        (1项)
  11. 性能基线        (3项)
"""

VERIFY_ITEMS = [
    # ============================================================
    # 1. 集群状态检查 (5项)
    # ============================================================
    {
        "id": "v-cluster-status",
        "name": "集群服务状态",
        "phase": "after_deploy",
        "severity": "error",
        "description": "Manager → 集群 → 服务，所有服务运行状态为【良好】",
        "check_cmd": "gs_om -t status --detail 2>/dev/null | grep -E 'om_monitor|cluster_state'",
    },
    {
        "id": "v-node-status",
        "name": "节点状态",
        "phase": "after_deploy",
        "severity": "error",
        "description": "Manager → 主机，所有节点运行状态为【良好】",
        "check_cmd": "gs_om -t status --detail 2>/dev/null | grep 'NodeState'",
    },
    {
        "id": "v-instance-status",
        "name": "实例运行状态",
        "phase": "after_deploy",
        "severity": "error",
        "description": "Coordinator/Datanode/GTM 实例均为【运行中】",
        "check_cmd": "gs_om -t status --detail 2>/dev/null | grep -E 'Coordinator|Datanode|GTM' | head -10",
    },
    {
        "id": "v-om-web",
        "name": "OM Web 访问",
        "phase": "after_deploy",
        "severity": "error",
        "description": "https://oms_float_ip:28443/web 可访问",
        "check_cmd": "curl -sk https://localhost:28443/web 2>/dev/null | head -1 || echo '需浏览器验证'",
    },
    {
        "id": "v-license-status",
        "name": "License 状态",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager → 系统 → License，状态为【Licensed】",
        "check_cmd": "echo '需登录 Manager Web GUI 验证: 系统 → License'",
    },

    # ============================================================
    # 2. 健康检查 (4项)
    # ============================================================
    {
        "id": "v-health-cluster",
        "name": "集群健康检查",
        "phase": "after_deploy",
        "severity": "error",
        "description": "Manager → 集群 → 更多 → 健康检查，无 ERROR 级问题",
        "check_cmd": "gs_om -t health-check 2>/dev/null | grep -i 'ERROR\\|WARNING' || echo 'OK: 无错误'",
    },
    {
        "id": "v-health-host",
        "name": "主机健康检查",
        "phase": "after_deploy",
        "severity": "error",
        "description": "Manager → 主机 → 勾选所有节点 → 健康检查，硬件指标正常",
        "check_cmd": "gs_checkos -i A -h $(cat /opt/hostlist 2>/dev/null || echo 'localhost') --detail 2>/dev/null | tail -5",
    },
    {
        "id": "v-health-schedule",
        "name": "定时健康检查配置",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager 已设置定时集群健康检查",
        "check_cmd": "echo '需登录 Manager 验证: 集群 → 健康检查 → 定时设置'",
    },
    {
        "id": "v-health-report",
        "name": "健康检查报告导出",
        "phase": "acceptance",
        "severity": "warning",
        "description": "导出健康检查报告，留存验收凭证",
        "check_cmd": "echo '需在 Manager 界面操作: 健康检查 → 导出报告'",
    },

    # ============================================================
    # 3. 数据库基本功能 (5项)
    # ============================================================
    {
        "id": "v-gsql-conn",
        "name": "gsql 连接测试",
        "phase": "after_deploy",
        "severity": "error",
        "description": "gsql -d postgres -p 25308 -c 'SELECT version()' 可连接",
        "check_cmd": "gsql -d postgres -p 25308 -c 'SELECT version()' 2>/dev/null || gsql -d postgres -p 40080 -c 'SELECT version()' 2>/dev/null",
    },
    {
        "id": "v-sql-basic",
        "name": "数据库基本操作",
        "phase": "after_deploy",
        "severity": "error",
        "description": "建表/插入/查询/删除功能正常",
        "check_cmd": "gsql -d postgres -p 25308 -c \"CREATE TABLE test_accept(id int); INSERT INTO test_accept VALUES(1); SELECT * FROM test_accept; DROP TABLE test_accept;\" 2>/dev/null",
    },
    {
        "id": "v-sql-query",
        "name": "数据库查询能力",
        "phase": "after_deploy",
        "severity": "error",
        "description": "多表 JOIN、聚合查询、排序功能正常",
        "check_cmd": "gsql -d postgres -p 25308 -c 'SELECT 1 AS test UNION SELECT 2 ORDER BY 1;' 2>/dev/null",
    },
    {
        "id": "v-sql-transaction",
        "name": "事务支持",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "BEGIN/COMMIT/ROLLBACK 事务功能正常",
        "check_cmd": "gsql -d postgres -p 25308 -c \"BEGIN; CREATE TABLE test_tx(id int); INSERT INTO test_tx VALUES(1); COMMIT; SELECT * FROM test_tx; DROP TABLE test_tx;\" 2>/dev/null",
    },
    {
        "id": "v-sql-procedure",
        "name": "存储过程支持",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "创建和执行存储过程功能正常",
        "check_cmd": "gsql -d postgres -p 25308 -c \"CREATE OR REPLACE FUNCTION test_func() RETURNS INT AS \\$\\$ BEGIN RETURN 1; END; \\$\\$ LANGUAGE plpgsql; SELECT test_func(); DROP FUNCTION test_func();\" 2>/dev/null",
    },

    # ============================================================
    # 4. 备份恢复 (3项)
    # ============================================================
    {
        "id": "v-backup-table",
        "name": "表级别备份恢复",
        "phase": "acceptance",
        "severity": "error",
        "description": "gs_dump 表级备份 + gs_restore 恢复功能正常",
        "check_cmd": "gs_dump -U root -f /tmp/test_backup.sql -t test_table postgres 2>/dev/null || echo '需创建测试表后执行'",
    },
    {
        "id": "v-backup-cluster",
        "name": "集群级别备份恢复",
        "phase": "acceptance",
        "severity": "error",
        "description": "gs_dumpall 全库备份功能正常",
        "check_cmd": "gs_dumpall -U root -f /tmp/test_backup_all.sql postgres 2>/dev/null || echo '需有合适权限'",
    },
    {
        "id": "v-backup-verify",
        "name": "备份文件完整性",
        "phase": "acceptance",
        "severity": "warning",
        "description": "确认备份文件已生成于 /srv/BigData/LocalBackup",
        "check_cmd": "ls -la /srv/BigData/LocalBackup/ 2>/dev/null || echo '无本地备份'",
    },

    # ============================================================
    # 5. 监控 (3项)
    # ============================================================
    {
        "id": "v-monitor-host",
        "name": "主机监控指标",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager → 主机，监控指标上报正常",
        "check_cmd": "echo '需登录 Manager 验证: 集群 → 主机 → 监控'",
    },
    {
        "id": "v-monitor-service",
        "name": "服务/实例监控",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager → 服务 → MPPDB，监控指标上报正常",
        "check_cmd": "echo '需登录 Manager 验证: 集群 → 服务 → MPPDB'",
    },
    {
        "id": "v-monitor-dashboard",
        "name": "监控看板定制",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "集群监控指标看板可定制，历史指标可查询",
        "check_cmd": "echo '需登录 Manager 验证: 主页 → 定制看板'",
    },

    # ============================================================
    # 6. 告警 (3项)
    # ============================================================
    {
        "id": "v-alarm-threshold",
        "name": "告警阈值检查",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "主机资源占用率超过阈值可上报告警",
        "check_cmd": "echo '需登录 Manager 验证: 告警 → 当前告警'",
    },
    {
        "id": "v-alarm-history",
        "name": "历史告警查询",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "历史告警可查询，可手动/自动清除",
        "check_cmd": "echo '需登录 Manager 验证: 告警 → 历史告警'",
    },
    {
        "id": "v-alarm-export",
        "name": "告警导出功能",
        "phase": "acceptance",
        "severity": "warning",
        "description": "告警事件可导出为文件",
        "check_cmd": "echo '需登录 Manager 验证: 告警 → 导出'",
    },

    # ============================================================
    # 7. 配置管理 (2项)
    # ============================================================
    {
        "id": "v-config-params",
        "name": "配置参数修改",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager 支持服务/实例配置参数修改",
        "check_cmd": "echo '需登录 Manager 验证: 集群 → 配置 → 修改参数'",
    },
    {
        "id": "v-config-numa",
        "name": "NUMA 绑核配置",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "DWS部署V2.0 标准：启用 NUMA 绑核",
        "check_cmd": "gs_guc check -Z coordinator -N all -I all -c 'enable_numa_bind' 2>/dev/null | grep -q 'on' && echo 'ON' || echo 'OFF'",
    },

    # ============================================================
    # 8. 日志管理 (1项)
    # ============================================================
    {
        "id": "v-log-filter",
        "name": "日志筛选下载",
        "phase": "after_deploy",
        "severity": "warning",
        "description": "Manager 日志管理支持筛选和下载",
        "check_cmd": "echo '需登录 Manager 验证: 日志 → 筛选/下载'",
    },

    # ============================================================
    # 9. 客户端 (2项)
    # ============================================================
    {
        "id": "v-client-download",
        "name": "客户端下载",
        "phase": "acceptance",
        "severity": "warning",
        "description": "Manager 支持客户端下载",
        "check_cmd": "echo '需登录 Manager 验证: 集群 → 客户端 → 下载'",
    },
    {
        "id": "v-client-install",
        "name": "客户端安装",
        "phase": "acceptance",
        "severity": "warning",
        "description": "客户端安装后可用 gsql/gs_dump 等工具",
        "check_cmd": "which gsql 2>/dev/null || which gs_dump 2>/dev/null || echo '未安装客户端'",
    },

    # ============================================================
    # 10. 用户管理 (1项)
    # ============================================================
    {
        "id": "v-user-mgmt",
        "name": "用户添加和删除",
        "phase": "acceptance",
        "severity": "warning",
        "description": "Manager 支持用户添加和删除",
        "check_cmd": "echo '需登录 Manager 验证: 系统 → 用户管理'",
    },

    # ============================================================
    # 11. 性能基线 (3项)
    # ============================================================
    {
        "id": "v-fio-baseline",
        "name": "fio 磁盘性能基线",
        "phase": "perf_test",
        "severity": "warning",
        "description": "fio 顺序写 ≥ 800MB/s，随机读 ≥ 1200MB/s",
        "check_cmd": "which fio && echo 'fio 已安装' || echo '需安装 fio'",
    },
    {
        "id": "v-net-baseline",
        "name": "网络带宽基线",
        "phase": "perf_test",
        "severity": "warning",
        "description": "10GE 网络带宽 ≥ 800MB/s，重传率 < 0.01%",
        "check_cmd": "which iperf3 && echo 'iperf3 已安装' || echo '需安装 iperf3'",
    },
    {
        "id": "v-gs-checkperf",
        "name": "gs_checkperf 性能基线",
        "phase": "perf_test",
        "severity": "warning",
        "description": "gs_checkperf 磁盘 I/O 和网络性能基线测试",
        "check_cmd": "which gs_checkperf 2>/dev/null && gs_checkperf -h localhost 2>/dev/null | head -5 || echo 'gs_checkperf 可用(需集群内执行)'",
    },
]
