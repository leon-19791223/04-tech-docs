"""DB2 -> DWS ETL/调度/BI等通用工具兼容性规则"""

ETL_RULES = [
    {
        "id": "DB2-ETL-001", "name": "DataX",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX", "compatible": True,
        "note": "DataX支持DB2 Reader + DWS Writer"
    },
    {
        "id": "DB2-ETL-002", "name": "Kettle对接DB2",
        "severity": "info", "score_deduction": 0,
        "tool": "Kettle", "compatible": True,
        "note": "Kettle可通过JDBC连接DB2和DWS"
    },
    {
        "id": "DB2-ETL-003", "name": "华为DRS (Data Replication Service)",
        "severity": "info", "score_deduction": 0,
        "tool": "DRS", "compatible": True,
        "note": "华为DRS支持DB2 LUW -> DWS全量+增量迁移，推荐使用",
        "suggestion": "DRS是生产环境推荐方案，支持结构迁移、全量迁移和增量同步"
    },
    {
        "id": "DB2-ETL-004", "name": "GDS (General Data Service) 并行导入",
        "severity": "info", "score_deduction": 0,
        "tool": "GDS", "compatible": True,
        "note": "GDS适合百GB级以上大数据量迁移，支持外表并行导入",
        "suggestion": "数百GB+数据量推荐使用GDS并行导入方案: 导出CSV->创建外表->INSERT INTO SELECT"
    },
    {
        "id": "DB2-ETL-005", "name": "IBM DataStage",
        "severity": "warning", "score_deduction": 3,
        "tool": "IBM DataStage", "compatible": True,
        "note": "DataStage可通过JDBC/ODBC连接DWS，需配置DWS驱动",
        "suggestion": "DataStage连接DWS需安装PostgreSQL JDBC驱动，部分作业需调整"
    },
    {
        "id": "DB2-ETL-006", "name": "Informatica",
        "severity": "info", "score_deduction": 0,
        "tool": "Informatica", "compatible": True,
        "note": "Informatica支持DB2源端和DWS目标端"
    },
    {
        "id": "DB2-ETL-007", "name": "DB2 EXPORT/IMPORT工具",
        "severity": "error", "score_deduction": 4,
        "tool": "DB2 EXPORT/IMPORT", "compatible": False,
        "note": "DB2 IXF/PC格式不兼容DWS",
        "migration_difficulty": "低",
        "migration_suggestion": "使用DRS方案迁移; 如已导出IXF文件，转为CSV后用DWS COPY/GDS导入"
    },
    {
        "id": "DB2-ETL-008", "name": "DB2 CDC (变更数据捕获)",
        "severity": "warning", "score_deduction": 3,
        "tool": "DB2 CDC", "compatible": True,
        "note": "DB2 CDC表可作为增量数据源，通过Kafka/Flink对接DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "使用Debezium/Kafka Connect + DB2 CDC -> Kafka -> Flink/DataX -> DWS"
    },
]

SCHEDULER_RULES = [
    {
        "id": "DB2-SCH-001", "name": "IBM Tivoli Workload Scheduler (TWS)",
        "severity": "warning", "score_deduction": 3,
        "tool": "TWS", "compatible": True,
        "note": "TWS可通过JDBC调度DWS作业",
        "suggestion": "确认TWS版本对PostgreSQL JDBC驱动的支持"
    },
    {
        "id": "DB2-SCH-002", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler", "compatible": True,
        "note": "完全支持DWS，推荐使用",
        "suggestion": "推荐作为DB2调度任务的目标调度系统"
    },
    {
        "id": "DB2-SCH-003", "name": "TaskCTL",
        "severity": "info", "score_deduction": 0,
        "tool": "TaskCTL", "compatible": True,
        "note": "通过JDBC/ODBC接口兼容DWS"
    },
    {
        "id": "DB2-SCH-004", "name": "Apache Airflow",
        "severity": "info", "score_deduction": 0,
        "tool": "Airflow", "compatible": True,
        "note": "通过DWS Hook支持"
    },
    {
        "id": "DB2-SCH-005", "name": "DB2 Task Scheduler (db2sch)",
        "severity": "error", "score_deduction": 5,
        "tool": "DB2 Task Scheduler", "compatible": False,
        "note": "DB2内置任务调度器需迁移到外部调度系统",
        "migration_difficulty": "中",
        "migration_suggestion": "DB2定时任务迁移到DolphinScheduler: 分析任务依赖->创建DWS SQL/DataX任务->配置调度周期"
    },
]

BI_RULES = [
    {
        "id": "DB2-BI-001", "name": "FineReport/FineBI",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport/FineBI", "compatible": True,
        "note": "通过DWS JDBC驱动完全兼容"
    },
    {
        "id": "DB2-BI-002", "name": "Tableau",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau", "compatible": True,
        "note": "DWS提供Tableau连接器"
    },
    {
        "id": "DB2-BI-003", "name": "Power BI",
        "severity": "info", "score_deduction": 0,
        "tool": "Power BI", "compatible": True,
        "note": "通过DWS ODBC驱动兼容"
    },
    {
        "id": "DB2-BI-004", "name": "Cognos Analytics",
        "severity": "warning", "score_deduction": 3,
        "tool": "IBM Cognos", "compatible": True,
        "note": "Cognos可通过JDBC/ODBC连接DWS，需配置DWS驱动",
        "migration_difficulty": "中",
        "migration_suggestion": "替换Cognos内容库中的DB2连接为DWS JDBC连接"
    },
    {
        "id": "DB2-BI-005", "name": "Smartbi",
        "severity": "info", "score_deduction": 0,
        "tool": "Smartbi", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]
