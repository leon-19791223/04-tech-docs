"""
MySQL -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""
from rules.registry import register

from .data_type_rules import DATA_TYPE_RULES
from .ddl_rules import DDL_RULES
from .function_rules import FUNCTION_RULES
from .common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES

_CATEGORY_WEIGHTS = {
    "ddl": 25, "data_type": 20, "function": 25,
    "etl_tool": 10, "scheduler": 10, "bi_tool": 10,
}


def load_rules() -> dict:
    """加载MySQL->DWS完整规则集"""
    return {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "etl_tool": ETL_RULES,
        "scheduler": SCHEDULER_RULES,
        "bi_tool": BI_RULES,
    }


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


# 自动注册到规则注册表
register("mysql", "dws", load_rules)
