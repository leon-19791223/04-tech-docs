"""
Teradata -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""

# ============================================================
# 迁移路径元信息 (用于Web UI自动发现)
# ============================================================
MIGRATION_INFO = {'label': 'Teradata -> DWS', 'icon': '&#x1F4E6;', 'description': 'Teradata到DWS迁移兼容性评估 (65条规则)'}

from rules.registry import register

from .ddl_rules import DDL_RULES
from .function_rules import FUNCTION_RULES
from .data_type_rules import DATA_TYPE_RULES
from .common_rules import (
    EXTENSION_RULES, ETL_RULES, SCHEDULER_RULES, BI_RULES,
    GUC_PARAMS,
)


_CATEGORY_WEIGHTS = {
    "ddl": 20,           # DDL: PI/分区/Volatile等
    "function": 25,      # 函数: QUALIFY/GROUP BY序号/NULL处理等
    "data_type": 10,     # 数据类型: BYTEINT/PERIOD等
    "extension": 10,     # 扩展: STATS/MACRO/HASH*等
    "etl_tool": 5,       # ETL: FastExport/FastLoad等
    "scheduler": 3,      # 调度
    "bi_tool": 2,        # BI
}


def load_rules() -> dict:
    """加载Teradata->DWS完整规则集"""
    return {
        "ddl": DDL_RULES,
        "function": FUNCTION_RULES,
        "data_type": DATA_TYPE_RULES,
        "extension": EXTENSION_RULES,
        "etl_tool": ETL_RULES,
        "scheduler": SCHEDULER_RULES,
        "bi_tool": BI_RULES,
    }


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


def get_guc_params() -> list:
    """获取Teradata兼容GUC参数建议"""
    return GUC_PARAMS


# 自动注册到规则注册表
register("teradata", "dws", load_rules, info=MIGRATION_INFO)
register("td", "dws", load_rules, info=MIGRATION_INFO)
