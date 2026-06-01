"""GP -> DWS ETL/调度/BI等通用工具兼容性规则"""

# ============================================================
# ETL 工具兼容性规则
# ============================================================
ETL_RULES = [
    {
        "id": "ETL-001", "name": "Kettle (Pentaho Data Integration)",
        "severity": "warning", "score_deduction": 3,
        "tool": "Kettle", "compatible": True,
        "note": "Kettle可通过JDBC/ODBC连接DWS，性能可能下降",
        "suggestion": "建议逐步迁移到DataX，性能更优、维护更简单"
    },
    {
        "id": "ETL-002", "name": "DataX",
        "severity": "info", "score_deduction": 0,
        "tool": "DataX", "compatible": True,
        "note": "DataX完全支持DWS Reader/Writer"
    },
    {
        "id": "ETL-003", "name": "Informatica PowerCenter",
        "severity": "info", "score_deduction": 0,
        "tool": "Informatica", "compatible": True,
        "note": "DWS提供Informatica Pushdown优化"
    },
    {
        "id": "ETL-004", "name": "Oracle Data Integrator (ODI)",
        "severity": "info", "score_deduction": 0,
        "tool": "ODI", "compatible": True,
        "note": "DWS提供ODI Knowledge Module"
    },
    {
        "id": "ETL-005", "name": "Talend",
        "severity": "info", "score_deduction": 0,
        "tool": "Talend", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]

# ============================================================
# 调度工具兼容性规则
# ============================================================
SCHEDULER_RULES = [
    {
        "id": "SCH-001", "name": "TaskCTL",
        "severity": "warning", "score_deduction": 3,
        "tool": "TaskCTL", "compatible": True,
        "note": "TaskCTL可通过JDBC/ODBC接口调度DWS",
        "suggestion": "建议升级到支持DWS原生调度的版本"
    },
    {
        "id": "SCH-002", "name": "DolphinScheduler",
        "severity": "info", "score_deduction": 0,
        "tool": "DolphinScheduler", "compatible": True,
        "note": "完全支持DWS，推荐使用"
    },
    {
        "id": "SCH-003", "name": "Apache Airflow",
        "severity": "info", "score_deduction": 0,
        "tool": "Airflow", "compatible": True,
        "note": "通过DWS Hook支持"
    },
    {
        "id": "SCH-004", "name": "Control-M",
        "severity": "info", "score_deduction": 0,
        "tool": "Control-M", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]

# ============================================================
# BI 工具兼容性规则
# ============================================================
BI_RULES = [
    {
        "id": "BI-001", "name": "FineBI",
        "severity": "info", "score_deduction": 0,
        "tool": "FineBI", "compatible": True,
        "note": "通过DWS JDBC驱动完全兼容"
    },
    {
        "id": "BI-002", "name": "FineReport",
        "severity": "info", "score_deduction": 0,
        "tool": "FineReport", "compatible": True,
        "note": "通过DWS JDBC驱动完全兼容"
    },
    {
        "id": "BI-003", "name": "Tableau",
        "severity": "info", "score_deduction": 0,
        "tool": "Tableau", "compatible": True,
        "note": "DWS提供Tableau连接器"
    },
    {
        "id": "BI-004", "name": "Power BI",
        "severity": "info", "score_deduction": 0,
        "tool": "Power BI", "compatible": True,
        "note": "通过DWS ODBC驱动兼容"
    },
    {
        "id": "BI-005", "name": "Smartbi",
        "severity": "info", "score_deduction": 0,
        "tool": "Smartbi", "compatible": True,
        "note": "通过JDBC接口兼容"
    },
]
