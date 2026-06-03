"""
MySQL -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""

# ============================================================
# 迁移路径元信息 (用于Web UI自动发现)
# ============================================================
MIGRATION_INFO = {'label': 'MySQL -> DWS', 'icon': '&#x1F431;', 'description': 'MySQL到DWS迁移兼容性评估'}

from rules.registry import register

from .data_type_rules import DATA_TYPE_RULES
from .ddl_rules import DDL_RULES
from .function_rules import FUNCTION_RULES
from .common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES
from .supplement_rules import SUPPLEMENT_RULES
from .sql_psm_rules import SQL_PSM_RULES
from .extension_rules import EXTENSION_RULES

_CATEGORY_WEIGHTS = {
    "ddl": 16, "data_type": 12, "function": 16,
    "udf_language": 5, "extension": 5,  # MySQL扩展插件
    "etl_tool": 7, "scheduler": 6, "bi_tool": 5,
    "security": 7, "charset": 7,
    "app_layer": 3, "transaction": 3, "cdc": 4, "performance": 3,
}


def load_rules() -> dict:
    """加载MySQL->DWS完整规则集"""
    rules = {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "udf_language": SQL_PSM_RULES,
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
    "sql": ("MySQL存储过程/函数迁移为PL/pgSQL，重点关注异常处理和动态SQL语法差异", "中"),
}


# 自动注册到规则注册表
register("mysql", "dws", load_rules, info=MIGRATION_INFO)
