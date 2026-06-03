"""Teradata -> DWS 扩展/ETL/调度/BI 兼容性规则"""

EXTENSION_RULES = [
    {
        "id": "TD-EXT-001", "name": "Teradata STATS(统计信息)",
        "severity": "error", "score_deduction": 6,
        "extension": "Teradata STATS (COLLECT STATISTICS)",
        "compatible": False,
        "note": "Teradata的COLLECT STATISTICS用于优化器统计信息收集，DWS使用ANALYZE替代",
        "migration_difficulty": "低",
        "migration_suggestion": "COLLECT STATISTICS -> ANALYZE table_name"
    },
    {
        "id": "TD-EXT-002", "name": "MACRO(宏)",
        "severity": "error", "score_deduction": 8,
        "extension": "MACRO",
        "compatible": False,
        "note": "Teradata MACRO是预编译SQL集合，DWS使用存储过程/函数替代",
        "migration_difficulty": "中",
        "migration_suggestion": "MACRO -> 存储过程(CREATE PROCEDURE)或函数(CREATE FUNCTION)"
    },
    {
        "id": "TD-EXT-003", "name": "Teradata HASH函数(HASHAMP/HASHBUCKET)",
        "severity": "error", "score_deduction": 6,
        "extension": "HASHAMP/HASHBUCKET/HASHROW",
        "compatible": False,
        "note": "Teradata特有哈希函数用于数据分布诊断，DWS无对应",
        "migration_difficulty": "高",
        "migration_suggestion": "检查SQL中是否使用HASH*函数; 如有需要分析其功能并用DWS视图替代"
    },
    {
        "id": "TD-EXT-004", "name": "Teradata SAMPLE(抽样)",
        "severity": "warning", "score_deduction": 3,
        "extension": "SAMPLE",
        "compatible": True,
        "note": "SAMPLE子句在DWS 9.1.0中兼容",
        "migration_difficulty": "低"
    },
    {
        "id": "TD-EXT-005", "name": "Teradata TOP n",
        "severity": "info", "score_deduction": 0,
        "extension": "TOP n",
        "compatible": True,
        "note": "DWS支持TOP n同义词(兼容TD语法)"
    },
    {
        "id": "TD-EXT-006", "name": "Teradata HELP/SHOW/EXPLAIN",
        "severity": "info", "score_deduction": 0,
        "extension": "HELP DATABASE/SHOW TABLE",
        "compatible": True,
        "note": "DWS兼容部分Teradata HELP/SHOW语法"
    },
]

ETL_RULES = [
    {
        "id": "TD-ETL-001", "name": "Teradata FastExport",
        "severity": "error", "score_deduction": 5,
        "tool": "FastExport",
        "compatible": False,
        "note": "Teradata专用导出工具，DWS使用GDS/COPY替代",
        "migration_difficulty": "中",
        "migration_suggestion": "改用DWS GDS并行导出或COPY命令"
    },
    {
        "id": "TD-ETL-002", "name": "Teradata FastLoad",
        "severity": "error", "score_deduction": 5,
        "tool": "FastLoad",
        "compatible": False,
        "note": "Teradata专用批量加载工具，DWS使用GDS/COPY替代",
        "migration_difficulty": "中",
        "migration_suggestion": "改用DWS GDS并行导入或COPY命令"
    },
    {
        "id": "TD-ETL-003", "name": "Teradata MultiLoad",
        "severity": "error", "score_deduction": 5,
        "tool": "MultiLoad",
        "compatible": False,
        "note": "Teradata批量upsert工具，DWS使用MERGE INTO替代",
        "migration_difficulty": "中",
        "migration_suggestion": "改用DWS MERGE INTO或INSERT ON CONFLICT"
    },
    {
        "id": "TD-ETL-004", "name": "Teradata TPT(并行传输)",
        "severity": "error", "score_deduction": 5,
        "tool": "TPT",
        "compatible": False,
        "note": "Teradata并行传输框架，DWS使用DataX/GDS替代",
        "migration_difficulty": "高",
        "migration_suggestion": "评估TPT作业逻辑，改用DataX或GDS实现"
    },
    {
        "id": "TD-ETL-005", "name": "Kettle对接Teradata",
        "severity": "info", "score_deduction": 0,
        "tool": "Kettle",
        "compatible": True,
        "note": "Kettle可通过JDBC连接Teradata和DWS，作业修改目标端即可"
    },
    {
        "id": "TD-ETL-006", "name": "DataX对接Teradata",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX",
        "compatible": True,
        "note": "DataX提供Teradata Reader，支持批量抽取"
    },
]

SCHEDULER_RULES = [
    {
        "id": "TD-SCH-001", "name": "Teradata Viewpoint/Task Scheduler",
        "severity": "error", "score_deduction": 6,
        "tool": "Teradata Viewpoint",
        "compatible": False,
        "note": "Teradata调度任务需迁移到DolphinScheduler/TaskCTL",
        "migration_difficulty": "中",
        "migration_suggestion": "在DolphinScheduler中重建调度任务"
    },
    {
        "id": "TD-SCH-002", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler",
        "compatible": True,
        "note": "推荐使用"
    },
    {
        "id": "TD-SCH-003", "name": "Tivoli/Control-M",
        "severity": "info", "score_deduction": 0,
        "tool": "Tivoli/Control-M",
        "compatible": True,
        "note": "通过JDBC兼容"
    },
]

BI_RULES = [
    {
        "id": "TD-BI-001", "name": "FineReport/FineBI",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport",
        "compatible": True,
        "note": "通过JDBC驱动兼容"
    },
    {
        "id": "TD-BI-002", "name": "Tableau/Power BI",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau",
        "compatible": True,
        "note": "通过DWS驱动兼容"
    },
]

# GUC参数兼容性表 (用于报告生成)
GUC_PARAMS = [
    {
        "guc": "behavior_compat_options",
        "td_value": "'strict_text_concat_td'",
        "description": "控制NULL字符串拼接行为为TD模式",
        "impact": "字符串函数行为",
        "recommend": "是",
    },
    {
        "guc": "td_compatible_truncation",
        "td_value": "ON",
        "description": "VARCHAR超长时TD模式的截断行为",
        "impact": "数据插入/更新",
        "recommend": "是",
    },
    {
        "guc": "transform_null_equals",
        "td_value": "ON",
        "description": "控制expr=NULL是否转为expr IS NULL",
        "impact": "查询语义",
        "recommend": "按需",
    },
    {
        "guc": "convert_empty_str_to_null_td",
        "td_value": "ON",
        "description": "控制空字符串是否转为NULL(TD模式)",
        "impact": "函数行为",
        "recommend": "是",
    },
]
