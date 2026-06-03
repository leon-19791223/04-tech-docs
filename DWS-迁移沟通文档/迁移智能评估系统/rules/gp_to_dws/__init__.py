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
from .supplement_rules import SUPPLEMENT_RULES


_CATEGORY_WEIGHTS = {
    "ddl": 20, "data_type": 12, "function": 15,
    "udf_language": 15, "extension": 8,
    "etl_tool": 4, "scheduler": 3, "bi_tool": 2,
    # 新增
    "security": 5,
    "charset": 3,
    "app_layer": 3,
    "transaction": 2,
    "cdc": 5,
    "performance": 3,
}


def load_rules() -> dict:
    """加载GP->DWS完整规则集"""
    rules = {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "udf_language": UDF_LANGUAGE_RULES,
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
# key=udf_languages字典中的key, value=(目标方案, 难度)
# ============================================================
UDF_LANGUAGE_MAP = {
    "sql": ("完全兼容(DWS支持SQL语言函数)", "低"),
    "plpgsql": ("完全兼容(DWS支持plpgsql语言函数)", "低"),
    "plpythonu": ("重写为plpgsql或Java UDF(FGC)", "高"),
    "plperl": ("完全重写为plpgsql", "高"),
    "plperlu": ("完全重写为plpgsql", "高"),
    "pljava": ("迁移为DWS Java UDF(FGC)方式", "中"),
    "plr": ("迁移到Spark MLlib或Python UDF替代", "高"),
    "c": ("将C函数逻辑迁移到应用层或使用plpgsql重构", "高"),
}


# 自动注册到规则注册表
register("gp", "dws", load_rules)
register("greenplum", "dws", load_rules)

