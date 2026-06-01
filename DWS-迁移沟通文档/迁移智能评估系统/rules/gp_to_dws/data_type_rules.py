"""GP -> DWS 数据类型兼容性规则"""

DATA_TYPE_RULES = [
    {
        "id": "DT-001", "name": "TEXT类型",
        "severity": "info", "score_deduction": 0,
        "source_type": "TEXT", "target_type": "TEXT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DT-002", "name": "VARCHAR(n) 语义差异",
        "severity": "warning", "score_deduction": 2,
        "source_type": "VARCHAR(n)", "target_type": "VARCHAR(n)",
        "compatible": True,
        "note": "GP中n是字符数，DWS中n是字节数，中文场景需调整长度"
    },
    {
        "id": "DT-003", "name": "NUMERIC/DECIMAL",
        "severity": "info", "score_deduction": 0,
        "source_type": "NUMERIC(p,s)", "target_type": "NUMERIC(p,s)",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DT-004", "name": "SERIAL伪类型",
        "severity": "warning", "score_deduction": 3,
        "source_type": "SERIAL / BIGSERIAL",
        "target_type": "INT DEFAULT nextval('seq')",
        "compatible": False,
        "note": "需转换为INT+SEQUENCE方式",
        "migration_difficulty": "低",
        "migration_suggestion": "通过DDL脚本批量转换"
    },
    {
        "id": "DT-005", "name": "JSON/JSONB",
        "severity": "info", "score_deduction": 0,
        "source_type": "JSON / JSONB", "target_type": "JSON / JSONB",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DT-006", "name": "几何数据类型",
        "severity": "error", "score_deduction": 8,
        "source_type": "POINT / LINE / LSEG / BOX / PATH / POLYGON / CIRCLE",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持的几何类型，需在应用层处理或转换成JSON存储",
        "migration_difficulty": "高",
        "migration_suggestion": "在应用层处理或使用JSONB存储"
    },
    {
        "id": "DT-007", "name": "网络地址类型",
        "severity": "warning", "score_deduction": 3,
        "source_type": "INET / CIDR / MACADDR",
        "target_type": "INET / CIDR（部分限制）",
        "compatible": True,
        "note": "DWS支持INET/CIDR但有部分功能限制"
    },
    {
        "id": "DT-008", "name": "位串类型",
        "severity": "warning", "score_deduction": 3,
        "source_type": "BIT(n) / BIT VARYING(n)",
        "target_type": "BIT(n) / BIT VARYING(n)",
        "compatible": True, "note": "DWS支持但有长度限制"
    },
    {
        "id": "DT-009", "name": "UUID类型",
        "severity": "info", "score_deduction": 0,
        "source_type": "UUID", "target_type": "UUID",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DT-010", "name": "枚举类型(ENUM)",
        "severity": "warning", "score_deduction": 4,
        "source_type": "CREATE TYPE ... AS ENUM",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持自定义枚举类型，需使用TEXT+CHECK约束替代",
        "migration_difficulty": "低",
        "migration_suggestion": "替换为TEXT类型并添加CHECK约束"
    },
    {
        "id": "DT-011", "name": "范围类型",
        "severity": "warning", "score_deduction": 4,
        "source_type": "INT4RANGE / DATERANGE / TSRANGE等",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持范围类型，需使用起止字段替代",
        "migration_difficulty": "中",
        "migration_suggestion": "将范围类型拆分为起始和结束两个字段"
    },
    {
        "id": "DT-012", "name": "数组类型",
        "severity": "warning", "score_deduction": 3,
        "source_type": "INT[] / TEXT[] 等数组类型",
        "target_type": "部分支持",
        "compatible": True,
        "note": "DWS支持一维数组但有功能限制"
    },
]
