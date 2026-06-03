"""
规则注册与发现机制
支持按 (source, target) 注册和查询规则集
支持自动发现所有已注册迁移路径
"""

_registry = {}  # (source, target) -> callable returning rules dict
_infos = {}     # (source, target) -> dict of metadata


def register(source: str, target: str, loader_fn, info: dict = None):
    """注册规则加载函数

    Args:
        source: 源端数据库类型 (如 "gp", "oracle")
        target: 目标端数据库类型 (如 "dws")
        loader_fn: 返回规则 dict 的函数
        info: 路径元信息, 包含 label, icon, description
    """
    key = (source.lower(), target.lower())
    _registry[key] = loader_fn
    if info:
        _infos[key] = info


def get_rules(source: str, target: str) -> dict:
    """获取指定源-目标的规则集"""
    key = (source.lower(), target.lower())
    if key in _registry:
        return _registry[key]()
    raise KeyError(f"未注册规则集: {source} -> {target}")


def list_registered() -> list:
    """列出所有已注册的规则集"""
    return [f"{s} -> {t}" for s, t in _registry.keys()]


def get_registered_paths() -> dict:
    """获取所有已注册迁移路径的元信息 (去重，用于Web UI自动渲染)

    每个迁移路径只保留一个主入口（按注册顺序取第一个）
    返回: { "gp_dws": {"label": "Greenplum -> DWS", "icon": "...", ...}, ... }
    """
    seen_labels = {}
    paths = {}
    # 按注册顺序遍历，同一 label 只取第一个（主别名优先注册）
    for (source, target), info in _infos.items():
        label = info.get("label", f"{source} -> {target}")
        # 同一 label 只保留第一个注册的路径
        if label not in seen_labels:
            seen_labels[label] = True
            path_key = f"{source}_{target}"
            paths[path_key] = {
                "key": path_key,
                "source": source,
                "target": target,
                "label": label,
                "icon": info.get("icon", "&#x1F310;"),
                "description": info.get("description", ""),
            }
    return paths


def get_path_info(source: str, target: str) -> dict:
    """获取指定路径的元信息"""
    key = (source.lower(), target.lower())
    if key in _infos:
        return dict(_infos[key])
    return {}


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
        "plsql": "PL/SQL语法兼容性",
        "trigger": "触发器兼容性",
        "sqlpl": "SQL PL存储过程兼容性",
        "exadata": "Oracle Exadata特性兼容性",
        "security": "安全与权限兼容性",
        "charset": "字符集与编码兼容性",
        "app_layer": "应用层兼容性",
        "transaction": "事务与并发兼容性",
        "cdc": "CDC增量同步兼容性",
        "performance": "性能与容量兼容性",
    }
    return names.get(category, category)
