"""GP -> DWS 补充评估规则

补充: 安全/字符集/应用层/事务/CDC同步/性能
"""

SECURITY_RULES = [
    {
        "id": "GP-SEC-001", "name": "GP角色与权限模型",
        "severity": "info", "score_deduction": 0,
        "description": "Greenplum与DWS都基于PostgreSQL权限模型，基本兼容",
        "compatible": True, "note": "基于相同PG内核，权限模型高度兼容"
    },
    {
        "id": "GP-SEC-002", "name": "GP超级用户权限",
        "severity": "warning", "score_deduction": 3,
        "description": "GP的超级用户权限在DWS托管环境中受限",
        "source_pattern": "gpadmin / ALTER SYSTEM / pg_catalog元数据直接修改",
        "target_solution": "DWS SYSADMIN由华为云管理，部分超级用户操作受限",
        "compatible": True,
        "note": "需检查SQL中是否依赖超级用户权限",
        "migration_difficulty": "低",
        "migration_suggestion": "检查存储过程/SQL中是否使用超级用户特有操作"
    },
    {
        "id": "GP-SEC-003", "name": "GP加密扩展(pgcrypto)",
        "severity": "info", "score_deduction": 0,
        "description": "GP的pgcrypto扩展在DWS中完全兼容",
        "compatible": True, "note": "完全兼容"
    },
]

CHARSET_RULES = [
    {
        "id": "GP-CSET-001", "name": "GP/PostgreSQL字符集",
        "severity": "info", "score_deduction": 0,
        "description": "GP和DWS都基于PostgreSQL，字符集处理兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "GP-CSET-002", "name": "VARCHAR长度语义",
        "severity": "warning", "score_deduction": 3,
        "description": "GP中VARCHAR(n)的n是字符数，DWS中VARCHAR(n)的n是字节数",
        "source_pattern": "VARCHAR(100) — GP和DWS行为相同(PG内核一致)",
        "compatible": True,
        "note": "注意: PG/DWS中VARCHAR(n)的n是字符数(不是字节数)，这是PG与其他DB(MySQL/DB2)的关键差异",
        "migration_difficulty": "低",
        "migration_suggestion": "GP→DWS的VARCHAR长度无需调整(两者行为一致)"
    },
]

APP_LAYER_RULES = [
    {
        "id": "GP-APP-001", "name": "JDBC驱动兼容性",
        "severity": "info", "score_deduction": 0,
        "description": "GP和DWS都使用PostgreSQL JDBC驱动，完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "GP-APP-002", "name": "连接池验证查询",
        "severity": "info", "score_deduction": 0,
        "description": "GP和DWS都使用SELECT 1作为连接验证，兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "GP-APP-003", "name": "ORM框架兼容性",
        "severity": "info", "score_deduction": 0,
        "description": "GP和DWS都兼容PostgreSQL生态，ORM框架无需修改",
        "compatible": True, "note": "完全兼容"
    },
]

TRANSACTION_RULES = [
    {
        "id": "GP-TXN-001", "name": "事务隔离级别",
        "severity": "info", "score_deduction": 0,
        "description": "GP和DWS都基于PG，隔离级别行为一致",
        "compatible": True, "note": "完全兼容"
    },
]

CDC_RULES = [
    {
        "id": "GP-CDC-001", "name": "GP到DWS迁移策略",
        "severity": "info", "score_deduction": 0,
        "description": "GP到DWS的数据迁移通常使用全量迁移+停机窗口",
        "compatible": True,
        "note": "GP没有原生CDC工具，建议使用全量导出(GPDUMP)+DWS COPY导入"
    },
    {
        "id": "GP-CDC-002", "name": "GP实时同步方案",
        "severity": "warning", "score_deduction": 3,
        "description": "GP原生不支持CDC实时同步到DWS",
        "tool": "GP没有原生CDC", "compatible": True,
        "note": "可通过GP的外部表+ETL实现准实时; 或使用批处理窗口",
        "migration_difficulty": "中",
        "migration_suggestion": "1)非实时场景: 停机窗口全量迁移; 2)准实时场景: Kettle/DataX分批抽取"
    },
]

PERFORMANCE_RULES = [
    {
        "id": "GP-PERF-001", "name": "分布键语法微调",
        "severity": "info", "score_deduction": 0,
        "description": "GP的DISTRIBUTED BY -> DWS的DISTRIBUTE BY HASH",
        "compatible": True, "note": "已在DDL规则中覆盖"
    },
    {
        "id": "GP-PERF-002", "name": "列存选择建议",
        "severity": "info", "score_deduction": 0,
        "description": "GP的APPENDONLY→DWS列存，功能对等",
        "compatible": True, "note": "已在DDL规则中覆盖"
    },
]

SUPPLEMENT_RULES = {
    "security": SECURITY_RULES,
    "charset": CHARSET_RULES,
    "app_layer": APP_LAYER_RULES,
    "transaction": TRANSACTION_RULES,
    "cdc": CDC_RULES,
    "performance": PERFORMANCE_RULES,
}
