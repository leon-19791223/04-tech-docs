"""
SQL Server -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""

# ============================================================
# 迁移路径元信息 (用于Web UI自动发现)
# ============================================================
MIGRATION_INFO = {'label': 'SQL Server -> DWS', 'icon': '&#x1F4CB;', 'description': 'SQL Server到DWS迁移兼容性评估'}

from rules.registry import register

from .data_type_rules import DATA_TYPE_RULES
from .ddl_rules import DDL_RULES
from .function_rules import FUNCTION_RULES
from .common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES
from .supplement_rules import SUPPLEMENT_RULES
from .tsql_rules import TSQL_RULES
from .extension_rules import EXTENSION_RULES

_CATEGORY_WEIGHTS = {
    "ddl": 12, "data_type": 10, "function": 16,
    "udf_language": 6, "extension": 5,  # T-SQL + SQL Server扩展
    "etl_tool": 6, "scheduler": 6, "bi_tool": 5,
    "security": 7, "charset": 5,
    "app_layer": 5, "transaction": 4, "cdc": 5, "performance": 4,
}


def load_rules() -> dict:
    """加载SQL Server->DWS完整规则集"""
    rules = {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "udf_language": TSQL_RULES,
        "extension": EXTENSION_RULES,
        "etl_tool": ETL_RULES,
        "scheduler": SCHEDULER_RULES,
        "bi_tool": BI_RULES,
    }
    rules.update(SUPPLEMENT_RULES)
    return rules


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


# ============================================================
# UDF语言映射表(引擎依赖此生成建议和工作量估算)
# ============================================================
UDF_LANGUAGE_MAP = {
    "tsql": ("T-SQL存储过程迁移为PL/pgSQL，重点关注游标、异常处理(TRY..CATCH)和动态SQL差异", "高"),
}


# 自动注册到规则注册表
register("mssql", "dws", load_rules, info=MIGRATION_INFO)
register("sqlserver", "dws", load_rules, info=MIGRATION_INFO)
register("sql_server", "dws", load_rules, info=MIGRATION_INFO)
