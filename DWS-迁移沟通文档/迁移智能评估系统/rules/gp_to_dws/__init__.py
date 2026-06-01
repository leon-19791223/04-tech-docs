"""
GP -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""
from rules.registry import register

from .ddl_rules import DDL_RULES
from .data_type_rules import DATA_TYPE_RULES
from .function_rules import FUNCTION_RULES
from .udf_rules import UDF_LANGUAGE_RULES
from .extension_rules import EXTENSION_RULES
from .common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES


_CATEGORY_WEIGHTS = {
    "ddl": 25, "data_type": 15, "function": 20,
    "udf_language": 20, "extension": 10,
    "etl_tool": 5, "scheduler": 3, "bi_tool": 2,
}


def load_rules() -> dict:
    """加载GP->DWS完整规则集"""
    return {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "udf_language": UDF_LANGUAGE_RULES,
        "extension": EXTENSION_RULES,
        "etl_tool": ETL_RULES,
        "scheduler": SCHEDULER_RULES,
        "bi_tool": BI_RULES,
    }


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


# 自动注册到规则注册表
register("gp", "dws", load_rules)
register("greenplum", "dws", load_rules)

