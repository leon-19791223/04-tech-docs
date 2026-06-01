"""
规则注册与发现机制
支持按 (source, target) 注册和查询规则集
"""

_registry = {}  # (source, target) -> callable returning rules dict


def register(source: str, target: str, loader_fn):
    """注册规则加载函数"""
    key = (source.lower(), target.lower())
    _registry[key] = loader_fn


def get_rules(source: str, target: str) -> dict:
    """获取指定源-目标的规则集"""
    key = (source.lower(), target.lower())
    if key in _registry:
        return _registry[key]()
    raise KeyError(f"未注册规则集: {source} -> {target}")


def list_registered() -> list:
    """列出所有已注册的规则集"""
    return [f"{s} -> {t}" for s, t in _registry.keys()]


def get_category_name(category: str, source: str = "", target: str = "") -> str:
    """获取分类的中文名称"""
    names = {
        "ddl": "DDL兼容性",
        "data_type": "数据类型兼容性",
        "function": "函数兼容性",
        "udf_language": "UDF语言兼容性",
        "extension": "扩展兼容性",
        "etl_tool": "ETL工具兼容性",
        "scheduler": "调度工具兼容性",
        "bi_tool": "BI工具兼容性",
    }
    return names.get(category, category)
