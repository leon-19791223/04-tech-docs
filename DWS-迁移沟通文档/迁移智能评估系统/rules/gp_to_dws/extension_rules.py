"""GP -> DWS 扩展兼容性规则"""

EXTENSION_RULES = [
    {
        "id": "EXT-001", "name": "Madlib机器学习库",
        "severity": "error", "score_deduction": 10,
        "extension": "madlib", "compatible": False,
        "note": "DWS不支持madlib扩展",
        "alternative": "DWS ML (内置机器学习) / Spark MLlib / 自定义Python UDF",
        "migration_difficulty": "高",
        "migration_suggestion": "简单统计改用SQL窗口函数; 复杂模型迁移到Spark MLlib"
    },
    {
        "id": "EXT-002", "name": "PostGIS空间扩展",
        "severity": "warning", "score_deduction": 5,
        "extension": "postgis", "compatible": False,
        "note": "DWS通过DWS PostGIS扩展支持基本空间功能",
        "alternative": "DWS PostGIS扩展（功能子集）",
        "migration_difficulty": "中",
        "migration_suggestion": "检查使用的PostGIS函数清单，部分函数需替换为DWS兼容版本"
    },
    {
        "id": "EXT-003", "name": "pgcrypto加密扩展",
        "severity": "info", "score_deduction": 0,
        "extension": "pgcrypto", "compatible": True, "note": "完全兼容"
    },
    {
        "id": "EXT-004", "name": "uuid-ossp扩展",
        "severity": "info", "score_deduction": 0,
        "extension": "uuid-ossp", "compatible": True, "note": "完全兼容"
    },
    {
        "id": "EXT-005", "name": "hstore键值对扩展",
        "severity": "warning", "score_deduction": 4,
        "extension": "hstore", "compatible": False,
        "note": "DWS不支持hstore扩展",
        "alternative": "JSONB类型替代",
        "migration_difficulty": "低",
        "migration_suggestion": "hstore替换为JSONB: hstore->'key' -> jsonb->>'key'"
    },
    {
        "id": "EXT-006", "name": "fuzzystrmatch模糊匹配",
        "severity": "info", "score_deduction": 0,
        "extension": "fuzzystrmatch", "compatible": True, "note": "兼容"
    },
    {
        "id": "EXT-007", "name": "pg_trgm文本相似度",
        "severity": "info", "score_deduction": 0,
        "extension": "pg_trgm", "compatible": True, "note": "兼容"
    },
    {
        "id": "EXT-008", "name": "tablefunc交叉表",
        "severity": "warning", "score_deduction": 5,
        "extension": "tablefunc", "compatible": False,
        "note": "DWS不支持tablefunc扩展",
        "alternative": "使用CASE WHEN + 聚合函数替代",
        "migration_difficulty": "中",
        "migration_suggestion": "crosstab功能可通过CASE WHEN + 聚合函数替代"
    },
]
