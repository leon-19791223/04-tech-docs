"""MySQL -> DWS ETL/调度/BI等通用工具兼容性规则"""

ETL_RULES = [
    {
        "id": "MYSQL-ETL-001", "name": "DataX",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX", "compatible": True,
        "note": "DataX完全支持MySQL Reader + DWS Writer"
    },
    {
        "id": "MYSQL-ETL-002", "name": "Kettle对接MySQL",
        "severity": "info", "score_deduction": 0,
        "tool": "Kettle", "compatible": True,
        "note": "Kettle可通过JDBC同时连接MySQL和DWS"
    },
    {
        "id": "MYSQL-ETL-003", "name": "Canal (CDC同步)",
        "severity": "error", "score_deduction": 6,
        "tool": "Canal", "compatible": False,
        "note": "Canal仅支持MySQL->Kafka，需额外开发DWS写入端",
        "migration_difficulty": "中",
        "migration_suggestion": "Canal数据接入Kafka后，使用Flink/DataX写入DWS"
    },
    {
        "id": "MYSQL-ETL-004", "name": "Debezium (CDC同步)",
        "severity": "warning", "score_deduction": 3,
        "tool": "Debezium", "compatible": True,
        "note": "Debezium可捕获MySQL变更写入Kafka，对接DWS需额外工具",
        "migration_difficulty": "中",
        "migration_suggestion": "Debezium + Kafka + Flink -> DWS 实时入仓方案"
    },
    {
        "id": "MYSQL-ETL-005", "name": "MySQL mysqldump导出",
        "severity": "error", "score_deduction": 4,
        "tool": "mysqldump", "compatible": False,
        "note": "mysqldump格式不兼容DWS，需转换",
        "migration_difficulty": "低",
        "migration_suggestion": "使用DataX或DRS从MySQL迁移到DWS"
    },
    {
        "id": "MYSQL-ETL-006", "name": "DRS (华为数据复制服务)",
        "severity": "info", "score_deduction": 0,
        "tool": "DRS", "compatible": True,
        "note": "华为DRS支持MySQL->DWS全量+增量迁移，推荐使用"
    },
]

SCHEDULER_RULES = [
    {
        "id": "MYSQL-SCH-001", "name": "MySQL Event Scheduler",
        "severity": "error", "score_deduction": 5,
        "tool": "MySQL Event Scheduler", "compatible": False,
        "note": "MySQL内置事件调度器需迁移到外部调度系统",
        "migration_difficulty": "中",
        "migration_suggestion": "MySQL Event迁移到DolphinScheduler或TaskCTL"
    },
    {
        "id": "MYSQL-SCH-002", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler", "compatible": True,
        "note": "完全支持DWS，推荐使用"
    },
    {
        "id": "MYSQL-SCH-003", "name": "TaskCTL",
        "severity": "info", "score_deduction": 0,
        "tool": "TaskCTL", "compatible": True,
        "note": "通过JDBC/ODBC接口兼容"
    },
    {
        "id": "MYSQL-SCH-004", "name": "Apache Airflow",
        "severity": "info", "score_deduction": 0,
        "tool": "Airflow", "compatible": True,
        "note": "通过DWS Hook支持"
    },
    {
        "id": "MYSQL-SCH-005", "name": "XXL-JOB",
        "severity": "info", "score_deduction": 0,
        "tool": "XXL-JOB", "compatible": True,
        "note": "通过JDBC接口兼容DWS"
    },
]

BI_RULES = [
    {
        "id": "MYSQL-BI-001", "name": "FineReport/FineBI",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport/FineBI", "compatible": True,
        "note": "通过DWS JDBC驱动完全兼容"
    },
    {
        "id": "MYSQL-BI-002", "name": "Tableau",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau", "compatible": True,
        "note": "DWS提供Tableau连接器"
    },
    {
        "id": "MYSQL-BI-003", "name": "Power BI",
        "severity": "info", "score_deduction": 0,
        "tool": "Power BI", "compatible": True,
        "note": "通过DWS ODBC驱动兼容"
    },
    {
        "id": "MYSQL-BI-004", "name": "Superset",
        "severity": "info", "score_deduction": 0,
        "tool": "Apache Superset", "compatible": True,
        "note": "通过SQLAlchemy/DWS Dialect兼容"
    },
    {
        "id": "MYSQL-BI-005", "name": "Smartbi",
        "severity": "info", "score_deduction": 0,
        "tool": "Smartbi", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]
