"""SQL Server -> DWS ETL/调度/BI等通用工具兼容性规则"""

ETL_RULES = [
    {
        "id": "MSSQL-ETL-001", "name": "DataX",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX", "compatible": True,
        "note": "DataX支持SQL Server Reader + DWS Writer"
    },
    {
        "id": "MSSQL-ETL-002", "name": "Kettle对接SQL Server",
        "severity": "info", "score_deduction": 0,
        "tool": "Kettle", "compatible": True,
        "note": "Kettle可通过JDBC连接SQL Server和DWS"
    },
    {
        "id": "MSSQL-ETL-003", "name": "SQL Server Integration Services (SSIS)",
        "severity": "error", "score_deduction": 6,
        "tool": "SSIS", "compatible": False,
        "note": "SSIS是SQL Server专有ETL工具，无法直接连接DWS",
        "migration_difficulty": "高",
        "migration_suggestion": "SSIS包需迁移到DataX/Kettle; 使用DRS做全量+增量数据同步"
    },
    {
        "id": "MSSQL-ETL-004", "name": "SQL Server Replication",
        "severity": "error", "score_deduction": 6,
        "tool": "SQL Server Replication", "compatible": False,
        "note": "SQL Server复制功能(快照/事务/合并)不能直接复制到DWS",
        "migration_difficulty": "高",
        "migration_suggestion": "使用DRS或CDC工具(Kafka Connect)替代复制功能"
    },
    {
        "id": "MSSQL-ETL-005", "name": "DRS (华为数据复制服务)",
        "severity": "info", "score_deduction": 0,
        "tool": "DRS", "compatible": True,
        "note": "华为DRS支持SQL Server(部分版本)->DWS全量+增量迁移"
    },
    {
        "id": "MSSQL-ETL-006", "name": "CDC (SQL Server变更数据捕获)",
        "severity": "warning", "score_deduction": 3,
        "tool": "SQL Server CDC", "compatible": True,
        "note": "CDC表可作为数据源由ETL工具增量读取，需对接DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "使用Debezium/Kafka Connect订阅SQL Server CDC -> Kafka -> Flink/DataX -> DWS"
    },
    {
        "id": "MSSQL-ETL-007", "name": "bcp/bulk insert",
        "severity": "error", "score_deduction": 4,
        "tool": "bcp", "compatible": False,
        "note": "SQL Server专用批量导入导出工具",
        "migration_difficulty": "低",
        "migration_suggestion": "使用DWS COPY命令或DataX替代"
    },
]

SCHEDULER_RULES = [
    {
        "id": "MSSQL-SCH-001", "name": "SQL Server Agent (作业调度)",
        "severity": "error", "score_deduction": 6,
        "tool": "SQL Server Agent", "compatible": False,
        "note": "SQL Server Agent作业需迁移到外部调度系统",
        "migration_difficulty": "中",
        "migration_suggestion": "SQL Server Agent作业迁移到DolphinScheduler或TaskCTL"
    },
    {
        "id": "MSSQL-SCH-002", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler", "compatible": True,
        "note": "完全支持DWS，推荐使用"
    },
    {
        "id": "MSSQL-SCH-003", "name": "TaskCTL",
        "severity": "info", "score_deduction": 0,
        "tool": "TaskCTL", "compatible": True,
        "note": "通过JDBC/ODBC接口兼容"
    },
    {
        "id": "MSSQL-SCH-004", "name": "Apache Airflow",
        "severity": "info", "score_deduction": 0,
        "tool": "Airflow", "compatible": True,
        "note": "通过DWS Hook支持"
    },
    {
        "id": "MSSQL-SCH-005", "name": "Tivoli Workload Scheduler (TWS)",
        "severity": "info", "score_deduction": 0,
        "tool": "TWS", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]

BI_RULES = [
    {
        "id": "MSSQL-BI-001", "name": "FineReport/FineBI",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport/FineBI", "compatible": True,
        "note": "通过DWS JDBC驱动完全兼容"
    },
    {
        "id": "MSSQL-BI-002", "name": "Power BI",
        "severity": "info", "score_deduction": 0,
        "tool": "Power BI", "compatible": True,
        "note": "通过DWS ODBC驱动兼容，需安装DWS ODBC驱动"
    },
    {
        "id": "MSSQL-BI-003", "name": "Tableau",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau", "compatible": True,
        "note": "DWS提供Tableau连接器"
    },
    {
        "id": "MSSQL-BI-004", "name": "SSRS (SQL Server Reporting Services)",
        "severity": "error", "score_deduction": 4,
        "tool": "SSRS", "compatible": False,
        "note": "SSRS报表服务依赖SQL Server，不能直接连接DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "SSRS报表迁移到FineReport或Power BI"
    },
    {
        "id": "MSSQL-BI-005", "name": "Smartbi",
        "severity": "info", "score_deduction": 0,
        "tool": "Smartbi", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]
