"""GP -> DWS UDF语言兼容性规则"""

UDF_LANGUAGE_RULES = [
    {
        "id": "UDF-001", "name": "SQL语言函数",
        "severity": "info", "score_deduction": 0,
        "language": "sql", "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "UDF-002", "name": "PL/pgSQL语言函数",
        "severity": "info", "score_deduction": 0,
        "language": "plpgsql", "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "UDF-003", "name": "PL/Pythonu语言函数",
        "severity": "error", "score_deduction": 10,
        "language": "plpythonu", "compatible": False,
        "note": "DWS不支持plpythonu语言，需改造为plpgsql或Java UDF/FGC",
        "migration_difficulty": "高",
        "migration_suggestion": "分析函数逻辑，重写为plpgsql; 复杂逻辑可使用DWS的FGC功能"
    },
    {
        "id": "UDF-004", "name": "PL/Perl语言函数",
        "severity": "error", "score_deduction": 10,
        "language": "plperl", "compatible": False,
        "note": "DWS不支持plperl/plperlu语言",
        "migration_difficulty": "高",
        "migration_suggestion": "需完全重写为plpgsql或Java UDF"
    },
    {
        "id": "UDF-005", "name": "PL/Java语言函数",
        "severity": "error", "score_deduction": 10,
        "language": "pljava", "compatible": False,
        "note": "DWS不支持pljava语言，但支持Java UDF",
        "migration_difficulty": "中",
        "migration_suggestion": "可迁移为DWS的Java UDF(FGC)方式，需调整接口规范"
    },
    {
        "id": "UDF-006", "name": "PL/R语言函数",
        "severity": "error", "score_deduction": 10,
        "language": "plr", "compatible": False,
        "note": "DWS不支持plr语言",
        "migration_difficulty": "高",
        "migration_suggestion": "建议迁移到Spark MLlib或Python UDF替代"
    },
    {
        "id": "UDF-007", "name": "C语言函数",
        "severity": "warning", "score_deduction": 5,
        "language": "c", "compatible": False,
        "note": "DWS不支持C语言自定义函数",
        "migration_difficulty": "高",
        "migration_suggestion": "将C函数逻辑迁移到应用层或使用plpgsql重构"
    },
]
