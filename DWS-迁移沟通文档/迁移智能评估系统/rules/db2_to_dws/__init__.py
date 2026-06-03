"""
DB2 -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""
from rules.registry import register

from .data_type_rules import DATA_TYPE_RULES
from .ddl_rules import DDL_RULES
from .function_rules import FUNCTION_RULES
from .sqlpl_rules import SQLPL_RULES
from .common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES
from .supplement_rules import SUPPLEMENT_RULES
from .extension_rules import EXTENSION_RULES

_CATEGORY_WEIGHTS = {
    "ddl": 13, "data_type": 13, "function": 13,
    "sqlpl": 13, "extension": 5,  # DB2扩展
    "etl_tool": 5, "scheduler": 5, "bi_tool": 4,
    "security": 7, "charset": 6,
    "app_layer": 4, "transaction": 3, "cdc": 4, "performance": 3,
}


def load_rules() -> dict:
    """加载DB2->DWS完整规则集"""
    rules = {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "sqlpl": SQLPL_RULES,
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
    "sql_pl": ("DB2 SQL PL存储过程迁移为plpgsql，重点关注异常处理(HANDLER→EXCEPTION)和游标语义的改造", "高"),
}


# 自动注册到规则注册表
register("db2", "dws", load_rules)
register("db2_luw", "dws", load_rules)
