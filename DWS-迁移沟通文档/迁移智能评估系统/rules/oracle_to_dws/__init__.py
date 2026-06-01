"""
Oracle -> DWS 规则集
聚合所有子模块规则并注册到规则注册表
"""
from rules.registry import register

from .ddl_rules import DDL_RULES
from .data_type_rules import DATA_TYPE_RULES
from .plsql_rules import FUNCTION_RULES, PLSQL_RULES, TRIGGER_RULES
from .extension_rules import (
    EXTENSION_RULES, ETL_RULES, SCHEDULER_RULES, BI_RULES
)


_CATEGORY_WEIGHTS = {
    "ddl": 20,           # DDL: 分区/索引等差异
    "data_type": 15,     # 数据类型: VARCHAR2/CLOB/NUMBER等
    "function": 15,      # SQL函数: DECODE/NVL/CONNECT BY等
    "plsql": 20,         # PL/SQL: 包/游标/异常/动态SQL
    "trigger": 10,       # 触发器
    "extension": 10,     # 扩展包: DBMS_*/UTL_*/Oracle Text等
    "etl_tool": 5,       # ETL工具
    "scheduler": 3,      # 调度工具
    "bi_tool": 2,        # BI工具
}


def load_rules() -> dict:
    """加载Oracle -> DWS完整规则集"""
    return {
        "ddl": DDL_RULES,
        "data_type": DATA_TYPE_RULES,
        "function": FUNCTION_RULES,
        "plsql": PLSQL_RULES,
        "trigger": TRIGGER_RULES,
        "extension": EXTENSION_RULES,
        "etl_tool": ETL_RULES,
        "scheduler": SCHEDULER_RULES,
        "bi_tool": BI_RULES,
    }


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


# 自动注册到规则注册表
register("oracle", "dws", load_rules)
register("oracle", "gaussdb", load_rules)
