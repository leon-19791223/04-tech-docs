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
from .supplement_rules import SUPPLEMENT_RULES
from .exadata_rules import EXADATA_RULES


_CATEGORY_WEIGHTS = {
    "ddl": 15,           # DDL: 分区/索引等差异
    "data_type": 12,     # 数据类型: VARCHAR2/CLOB/NUMBER等
    "function": 12,      # SQL函数: DECODE/NVL/CONNECT BY等
    "plsql": 15,         # PL/SQL: 包/游标/异常/动态SQL
    "trigger": 8,       # 触发器
    "extension": 8,      # 扩展包: DBMS_*/UTL_*/Oracle Text等
    "etl_tool": 4,       # ETL工具
    "scheduler": 3,      # 调度工具
    "bi_tool": 2,        # BI工具
    # 新增
    "exadata": 5,        # Oracle Exadata特性
    "security": 8,       # 安全与权限
    "charset": 5,        # 字符集与编码
    "app_layer": 3,      # 应用层兼容性
    "transaction": 3,    # 事务与并发
    "cdc": 3,            # CDC增量同步
    "performance": 2,    # 性能与容量
}


def load_rules() -> dict:
    """加载Oracle -> DWS完整规则集"""
    rules = {
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
    rules.update(SUPPLEMENT_RULES)
    rules["exadata"] = EXADATA_RULES
    return rules


def load_weights() -> dict:
    return dict(_CATEGORY_WEIGHTS)


# ============================================================
# UDF语言映射表(引擎依赖此生成建议和工作量估算)
# ============================================================
UDF_LANGUAGE_MAP = {
    "plsql": ("PL/SQL包/函数/过程迁移为plpgsql，重点关注包(PACKAGE)和游标语法的改造", "高"),
    "java": ("Java存储过程迁移为DWS Java UDF(FGC)方式", "中"),
}


# 自动注册到规则注册表
register("oracle", "dws", load_rules)
register("oracle", "gaussdb", load_rules)
