"""GP -> DWS DDL兼容性规则"""

DDL_RULES = [
    {
        "id": "DDL-001",
        "name": "存储模型 - APPENDONLY表",
        "severity": "warning",
        "score_deduction": 5,
        "description": "Greenplum的APPENDONLY堆表在DWS中需使用ORIENTATION=COLUMN列存表替代",
        "source_pattern": "WITH (APPENDONLY=true)",
        "target_solution": "CREATE TABLE ... WITH (ORIENTATION=COLUMN)",
        "detail": "GP的AO表主要用于批量写入场景，DWS的列存表(COLUMN)功能对等，但语法不兼容"
    },
    {
        "id": "DDL-002",
        "name": "存储模型 - 压缩表",
        "severity": "warning",
        "score_deduction": 3,
        "description": "GP压缩语法(COMPRESSTYPE/COMPRESSLEVEL)与DWS不同",
        "source_pattern": "COMPRESSTYPE=zlib COMPRESSLEVEL=5",
        "target_solution": "WITH (ORIENTATION=COLUMN, COMPRESSION=HIGH)",
        "detail": "GP支持行存和列存压缩，DWS列存默认支持压缩但压缩级别参数不同"
    },
    {
        "id": "DDL-003",
        "name": "分布键语法差异",
        "severity": "info",
        "score_deduction": 1,
        "description": "Greenplum DISTRIBUTED BY -> DWS DISTRIBUTE BY HASH，语法微调",
        "source_pattern": "DISTRIBUTED BY (column)",
        "target_solution": "DISTRIBUTE BY HASH (column)",
        "detail": "差异较小，仅关键字调整，可通过脚本批量替换"
    },
    {
        "id": "DDL-004",
        "name": "随机分布",
        "severity": "warning",
        "score_deduction": 5,
        "description": "DISTRIBUTED RANDOMLY在DWS中需指定分布键",
        "source_pattern": "DISTRIBUTED RANDOMLY",
        "target_solution": "DISTRIBUTE BY HASH (column) -- 需选择合适的分布列",
        "detail": "DWS不支持RANDOMLY分布，必须指定分布键，需分析数据特征选择合适列"
    },
    {
        "id": "DDL-005",
        "name": "分区表语法差异",
        "severity": "warning",
        "score_deduction": 4,
        "description": "GP与DWS分区DDL语法存在差异",
        "source_pattern": "PARTITION BY RANGE(ts) (START '2020-01-01' END '2025-12-31')",
        "target_solution": "PARTITION BY RANGE(ts) (PARTITION p0 VALUES LESS THAN ('2025-01-01'))",
        "detail": "GP支持START/END便捷语法，DWS需使用VALUES LESS THAN方式"
    },
    {
        "id": "DDL-006",
        "name": "列默认值 - 序列/自增",
        "severity": "error",
        "score_deduction": 8,
        "description": "SERIAL/BIGSERIAL伪类型在DWS中不完全兼容",
        "source_pattern": "id SERIAL PRIMARY KEY",
        "target_solution": "id INT DEFAULT nextval('seq_name') -- 需手动创建SEQUENCE",
        "migration_difficulty": "中",
        "migration_suggestion": "建议统一转换为SEQUENCE+nextval方式"
    },
]
