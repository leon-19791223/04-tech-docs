"""Oracle -> DWS 扩展/工具/ETL/调度兼容性规则"""

# ================================================================
# Oracle扩展和内置包
# ================================================================
EXTENSION_RULES = [
    {
        "id": "ORA-EXT-001", "name": "DBMS_OUTPUT",
        "severity": "warning", "score_deduction": 2,
        "extension": "DBMS_OUTPUT",
        "compatible": True,
        "note": "替换为RAISE NOTICE，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 DBMS_OUTPUT.PUT_LINE -> RAISE NOTICE"
    },
    {
        "id": "ORA-EXT-002", "name": "DBMS_SQL",
        "severity": "error", "score_deduction": 6,
        "extension": "DBMS_SQL",
        "compatible": False,
        "note": "Oracle动态SQL包，DWS不支持",
        "migration_difficulty": "中",
        "migration_suggestion": "改为EXECUTE ... USING方式(plpgsql原生动态SQL)"
    },
    {
        "id": "ORA-EXT-003", "name": "DBMS_LOB",
        "severity": "warning", "score_deduction": 3,
        "extension": "DBMS_LOB",
        "compatible": True,
        "note": "LOB操作在DWS中使用字符串函数替代",
        "migration_difficulty": "中",
        "migration_suggestion": "DBMS_LOB.GETLENGTH -> LENGTH; DBMS_LOB.SUBSTR -> SUBSTR; DBMS_LOB.INSTR -> INSTR"
    },
    {
        "id": "ORA-EXT-004", "name": "DBMS_CRYPTO",
        "severity": "error", "score_deduction": 6,
        "extension": "DBMS_CRYPTO",
        "compatible": False,
        "note": "Oracle加密包，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "使用DWS内置加密函数(如MD5/SHA2)或应用层加密替代"
    },
    {
        "id": "ORA-EXT-005", "name": "DBMS_SCHEDULER",
        "severity": "error", "score_deduction": 8,
        "extension": "DBMS_SCHEDULER",
        "compatible": False,
        "note": "Oracle任务调度器，DWS中需使用外部调度工具",
        "migration_difficulty": "中",
        "migration_suggestion": "DBMS_SCHEDULER任务迁移到DolphinScheduler或TaskCTL"
    },
    {
        "id": "ORA-EXT-006", "name": "DBMS_FLASHBACK",
        "severity": "error", "score_deduction": 8,
        "extension": "DBMS_FLASHBACK",
        "compatible": False,
        "note": "Oracle闪回功能，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "无需迁移; 数据库级恢复使用DWS备份恢复功能"
    },
    {
        "id": "ORA-EXT-007", "name": "DBMS_STATS",
        "severity": "error", "score_deduction": 6,
        "extension": "DBMS_STATS",
        "compatible": False,
        "note": "Oracle统计信息管理包，DWS不支持",
        "migration_difficulty": "低",
        "migration_suggestion": "DWS自动管理统计信息(ANALYZE自动执行)，无需手动调用DBMS_STATS"
    },
    {
        "id": "ORA-EXT-008", "name": "DBMS_XMLGEN / DBMS_XMLDOM",
        "severity": "error", "score_deduction": 8,
        "extension": "DBMS_XMLGEN",
        "compatible": False,
        "note": "Oracle XML生成包，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "在应用层生成XML，或使用SQL字符串拼接替代"
    },
    {
        "id": "ORA-EXT-009", "name": "UTL_FILE",
        "severity": "error", "score_deduction": 8,
        "extension": "UTL_FILE",
        "compatible": False,
        "note": "Oracle文件读写包，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "文件操作迁移到ETL层或应用层处理"
    },
    {
        "id": "ORA-EXT-010", "name": "UTL_MAIL / UTL_SMTP",
        "severity": "error", "score_deduction": 8,
        "extension": "UTL_MAIL",
        "compatible": False,
        "note": "Oracle邮件发送包，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "邮件通知功能迁移到应用层或调度工具"
    },
    {
        "id": "ORA-EXT-011", "name": "UTL_HTTP",
        "severity": "error", "score_deduction": 8,
        "extension": "UTL_HTTP",
        "compatible": False,
        "note": "Oracle HTTP请求包，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "HTTP调用迁移到应用层"
    },
    {
        "id": "ORA-EXT-012", "name": "Oracle Text (CONTEXT索引)",
        "severity": "error", "score_deduction": 10,
        "extension": "Oracle Text",
        "compatible": False,
        "note": "Oracle全文检索功能，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "1) 简单搜索: 使用LIKE/ILIKE; 2) 复杂搜索: 集成Elasticsearch"
    },
    {
        "id": "ORA-EXT-013", "name": "Oracle Spatial (SDO_GEOMETRY)",
        "severity": "error", "score_deduction": 8,
        "extension": "Oracle Spatial",
        "compatible": False,
        "note": "Oracle空间数据类型和函数，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "替换为PostGIS兼容API(DWS PostGIS扩展支持基本空间功能)"
    },
    {
        "id": "ORA-EXT-014", "name": "高级队列(AQ)",
        "severity": "error", "score_deduction": 10,
        "extension": "Oracle AQ",
        "compatible": False,
        "note": "Oracle高级队列消息系统，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "替换为消息中间件(Kafka/RabbitMQ)或DWS的NOTIFY/LISTEN"
    },
    {
        "id": "ORA-EXT-015", "name": "管道函数(Pipelined Function)",
        "severity": "error", "score_deduction": 6,
        "extension": "Pipelined Function",
        "compatible": False,
        "note": "Oracle管道函数返回多行，DWS中不支持",
        "migration_difficulty": "中",
        "migration_suggestion": "改为返回SETOF的plpgsql函数，或使用RETURN TABLE"
    },
    {
        "id": "ORA-EXT-016", "name": "MATERIALIZED VIEW刷新",
        "severity": "warning", "score_deduction": 3,
        "extension": "MV Refresh",
        "compatible": True,
        "note": "仅支持全量刷新(COMPLETE)，FAST/ON COMMIT不支持",
        "migration_difficulty": "中",
        "migration_suggestion": "改为定时全量刷新，由外部调度触发"
    },
]

# ================================================================
# ETL 工具兼容性
# ================================================================
ETL_RULES = [
    {
        "id": "ORA-ETL-001", "name": "Oracle GoldenGate (OGG)",
        "severity": "warning", "score_deduction": 3,
        "tool": "GoldenGate",
        "compatible": True,
        "note": "OGG可对接DWS作为目标端，但需安装DWS适配器",
        "migration_difficulty": "中",
        "migration_suggestion": "升级OGG版本以支持DWS目标端"
    },
    {
        "id": "ORA-ETL-002", "name": "Oracle Data Pump (expdp/impdp)",
        "severity": "error", "score_deduction": 5,
        "tool": "Data Pump",
        "compatible": False,
        "note": "Oracle数据泵专用格式，DWS不可读",
        "migration_difficulty": "低",
        "migration_suggestion": "使用DRS或DataX从Oracle迁移数据到DWS"
    },
    {
        "id": "ORA-ETL-003", "name": "Kettle对接Oracle",
        "severity": "info", "score_deduction": 0,
        "tool": "Kettle",
        "compatible": True,
        "note": "Kettle可通过JDBC同时连接Oracle和DWS，无需替换工具"
    },
    {
        "id": "ORA-ETL-004", "name": "DataX对接Oracle",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX",
        "compatible": True,
        "note": "DataX支持Oracle Reader和DWS Writer"
    },
    {
        "id": "ORA-ETL-005", "name": "Oracle SQL*Loader",
        "severity": "error", "score_deduction": 5,
        "tool": "SQL*Loader",
        "compatible": False,
        "note": "Oracle专用批量加载工具，DWS不可用",
        "migration_difficulty": "低",
        "migration_suggestion": "使用DWS的COPY命令或DataX替代批量加载"
    },
    {
        "id": "ORA-ETL-006", "name": "Informatica Oracle连接",
        "severity": "info", "score_deduction": 0,
        "tool": "Informatica",
        "compatible": True,
        "note": "Informatica同时支持Oracle源端和DWS目标端"
    },
]

# ================================================================
# 调度工具兼容性
# ================================================================
SCHEDULER_RULES = [
    {
        "id": "ORA-SCH-001", "name": "Oracle DBMS_SCHEDULER任务",
        "severity": "error", "score_deduction": 6,
        "tool": "DBMS_SCHEDULER",
        "compatible": False,
        "note": "Oracle内部调度器，需迁移到外部调度系统",
        "migration_difficulty": "中",
        "migration_suggestion": "迁移到DolphinScheduler: 创建DWS SQL任务 + DataX任务"
    },
    {
        "id": "ORA-SCH-002", "name": "Oracle Job (DBMS_JOB)",
        "severity": "error", "score_deduction": 6,
        "tool": "DBMS_JOB",
        "compatible": False,
        "note": "Oracle旧版作业系统，需迁移",
        "migration_difficulty": "中",
        "migration_suggestion": "迁移到DolphinScheduler或TaskCTL"
    },
    {
        "id": "ORA-SCH-003", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler",
        "compatible": True,
        "note": "推荐使用"
    },
    {
        "id": "ORA-SCH-004", "name": "TaskCTL",
        "severity": "info", "score_deduction": 0,
        "tool": "TaskCTL",
        "compatible": True,
        "note": "兼容"
    },
]

# ================================================================
# BI工具兼容性
# ================================================================
BI_RULES = [
    {
        "id": "ORA-BI-001", "name": "FineReport/FineBI对接DWS",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport",
        "compatible": True,
        "note": "通过DWS JDBC驱动兼容"
    },
    {
        "id": "ORA-BI-002", "name": "Tableau对接DWS",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau",
        "compatible": True,
        "note": "DWS提供Tableau连接器"
    },
    {
        "id": "ORA-BI-003", "name": "Power BI对接DWS",
        "severity": "info", "score_deduction": 0,
        "tool": "Power BI",
        "compatible": True,
        "note": "通过ODBC驱动兼容"
    },
]
