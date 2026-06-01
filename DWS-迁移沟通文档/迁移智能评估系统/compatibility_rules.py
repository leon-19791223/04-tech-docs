"""
[DEPRECATED] 兼容性规则库 - 请使用 rules/gp_to_dws/ 子模块

保留此文件作为向后兼容的转发层。
"""

import warnings
warnings.warn(
    "compatibility_rules.py 已废弃，请使用 rules.gp_to_dws 子模块",
    DeprecationWarning, stacklevel=2
)

from rules.gp_to_dws.ddl_rules import DDL_RULES
from rules.gp_to_dws.data_type_rules import DATA_TYPE_RULES
from rules.gp_to_dws.function_rules import FUNCTION_RULES
from rules.gp_to_dws.udf_rules import UDF_LANGUAGE_RULES
from rules.gp_to_dws.extension_rules import EXTENSION_RULES
from rules.gp_to_dws.common_rules import ETL_RULES, SCHEDULER_RULES, BI_RULES
from rules.gp_to_dws import load_rules, _CATEGORY_WEIGHTS as CATEGORY_WEIGHTS


def get_all_rules():
    """保持与原API兼容"""
    return load_rules()


def get_category_name(category):
    names = {
        "ddl": "DDL兼容性", "data_type": "数据类型兼容性",
        "function": "函数兼容性", "udf_language": "UDF语言兼容性",
        "extension": "扩展兼容性", "etl_tool": "ETL工具兼容性",
        "scheduler": "调度工具兼容性", "bi_tool": "BI工具兼容性",
    }
    return names.get(category, category)


def get_severity_label(severity):
    labels = {"info": "信息", "warning": "警告", "error": "不兼容"}
    return labels.get(severity, severity)


def get_severity_color(severity):
    colors = {"info": "#2E7D32", "warning": "#F57F17", "error": "#C62828"}
    return colors.get(severity, "#666666")
