"""MySQL -> DWS 数据类型兼容性规则"""

DATA_TYPE_RULES = [
    {
        "id": "MYSQL-DT-001", "name": "TINYINT",
        "severity": "warning", "score_deduction": 2,
        "source_type": "TINYINT", "target_type": "SMALLINT",
        "compatible": True,
        "note": "MySQL TINYINT(1字节) 映射为 DWS SMALLINT(2字节)，存储空间略有增加",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 TINYINT -> SMALLINT，注意TINYINT(1)被ORM映射为boolean的情况"
    },
    {
        "id": "MYSQL-DT-002", "name": "SMALLINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "SMALLINT", "target_type": "SMALLINT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-003", "name": "MEDIUMINT",
        "severity": "warning", "score_deduction": 2,
        "source_type": "MEDIUMINT", "target_type": "INT",
        "compatible": True,
        "note": "MySQL MEDIUMINT(3字节) 映射为 DWS INT(4字节) 或 INTEGER",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 MEDIUMINT -> INT"
    },
    {
        "id": "MYSQL-DT-004", "name": "INT/INTEGER",
        "severity": "info", "score_deduction": 0,
        "source_type": "INT/INTEGER", "target_type": "INT/INTEGER",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-005", "name": "BIGINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "BIGINT", "target_type": "BIGINT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-006", "name": "UNSIGNED属性",
        "severity": "error", "score_deduction": 5,
        "source_type": "INT UNSIGNED / BIGINT UNSIGNED",
        "target_type": "不支持UNSIGNED",
        "compatible": False,
        "note": "DWS不支持UNSIGNED属性，需调整字段类型或增加CHECK约束",
        "migration_difficulty": "中",
        "migration_suggestion": "移除UNSIGNED并将类型提升一级: TINYINT UNSIGNED->SMALLINT, INT UNSIGNED->BIGINT"
    },
    {
        "id": "MYSQL-DT-007", "name": "FLOAT/DOUBLE",
        "severity": "info", "score_deduction": 0,
        "source_type": "FLOAT/DOUBLE", "target_type": "FLOAT4/FLOAT8",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-008", "name": "DECIMAL/NUMERIC",
        "severity": "info", "score_deduction": 0,
        "source_type": "DECIMAL(p,s)", "target_type": "NUMERIC(p,s)",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-009", "name": "DATE",
        "severity": "info", "score_deduction": 0,
        "source_type": "DATE", "target_type": "DATE",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DT-010", "name": "DATETIME",
        "severity": "warning", "score_deduction": 2,
        "source_type": "DATETIME", "target_type": "TIMESTAMP",
        "compatible": True,
        "note": "MySQL DATETIME(无时区) 映射为 DWS TIMESTAMP(无时区)，精度相同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 DATETIME -> TIMESTAMP"
    },
    {
        "id": "MYSQL-DT-011", "name": "TIMESTAMP",
        "severity": "warning", "score_deduction": 3,
        "source_type": "TIMESTAMP", "target_type": "TIMESTAMPTZ",
        "compatible": True,
        "note": "MySQL TIMESTAMP有时区转换，DWS需使用TIMESTAMPTZ或应用层处理时区",
        "migration_difficulty": "低",
        "migration_suggestion": "确认时区处理逻辑: MySQL自动转换会话时区，DWS需在连接参数或查询中指定"
    },
    {
        "id": "MYSQL-DT-012", "name": "TIME",
        "severity": "warning", "score_deduction": 4,
        "source_type": "TIME", "target_type": "INTERVAL",
        "compatible": True,
        "note": "MySQL TIME 映射为 DWS INTERVAL 类型，语义基本对等",
        "migration_difficulty": "中",
        "migration_suggestion": "TIME -> INTERVAL 类型转换，应用代码中的TIME处理逻辑需调整"
    },
    {
        "id": "MYSQL-DT-013", "name": "YEAR",
        "severity": "warning", "score_deduction": 2,
        "source_type": "YEAR", "target_type": "SMALLINT",
        "compatible": True,
        "note": "MySQL YEAR 映射为 DWS SMALLINT，应用层处理年份显示",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 YEAR -> SMALLINT"
    },
    {
        "id": "MYSQL-DT-014", "name": "CHAR/VARCHAR",
        "severity": "info", "score_deduction": 0,
        "source_type": "CHAR(n)/VARCHAR(n)", "target_type": "CHAR(n)/VARCHAR(n)",
        "compatible": True,
        "note": "基本兼容。注意MySQL中n是字符数，DWS中n是字节数(UTF-8中文占3字节)，长度需调整为3倍"
    },
    {
        "id": "MYSQL-DT-015", "name": "BINARY/VARBINARY",
        "severity": "warning", "score_deduction": 3,
        "source_type": "BINARY/VARBINARY", "target_type": "BYTEA",
        "compatible": True,
        "note": "MySQL二进制类型映射为DWS BYTEA，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 BINARY(n) -> BYTEA, VARBINARY(n) -> BYTEA"
    },
    {
        "id": "MYSQL-DT-016", "name": "TINYTEXT/TEXT/MEDIUMTEXT/LONGTEXT",
        "severity": "info", "score_deduction": 0,
        "source_type": "TINYTEXT/TEXT/MEDIUMTEXT/LONGTEXT",
        "target_type": "TEXT",
        "compatible": True,
        "note": "所有MySQL TEXT变体统一映射为DWS TEXT，无长度限制差异"
    },
    {
        "id": "MYSQL-DT-017", "name": "TINYBLOB/BLOB/MEDIUMBLOB/LONGBLOB",
        "severity": "warning", "score_deduction": 2,
        "source_type": "TINYBLOB/BLOB/MEDIUMBLOB/LONGBLOB",
        "target_type": "BYTEA",
        "compatible": True,
        "note": "所有MySQL BLOB类型统一映射为DWS BYTEA",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 BLOB类型 -> BYTEA"
    },
    {
        "id": "MYSQL-DT-018", "name": "ENUM",
        "severity": "error", "score_deduction": 5,
        "source_type": "ENUM('val1','val2',...)", "target_type": "VARCHAR + CHECK",
        "compatible": False,
        "note": "DWS不支持ENUM类型，需改为VARCHAR+CHECK约束或引用表",
        "migration_difficulty": "低",
        "migration_suggestion": "CREATE TABLE ... col VARCHAR(20) CHECK (col IN ('val1','val2'))"
    },
    {
        "id": "MYSQL-DT-019", "name": "SET类型",
        "severity": "error", "score_deduction": 6,
        "source_type": "SET('val1','val2',...)", "target_type": "VARCHAR或关联表",
        "compatible": False,
        "note": "DWS不支持SET类型，需拆分为多对多关联表或使用VARCHAR存储",
        "migration_difficulty": "中",
        "migration_suggestion": "SET字段拆分为关联表，或使用VARCHAR+应用层解析"
    },
    {
        "id": "MYSQL-DT-020", "name": "JSON",
        "severity": "info", "score_deduction": 0,
        "source_type": "JSON", "target_type": "JSON",
        "compatible": True, "note": "DWS支持JSON类型，基本功能兼容"
    },
    {
        "id": "MYSQL-DT-021", "name": "GEOMETRY类型",
        "severity": "error", "score_deduction": 8,
        "source_type": "GEOMETRY/POINT/LINESTRING/POLYGON",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持空间数据类型",
        "migration_difficulty": "高",
        "migration_suggestion": "使用JSONB存储坐标数据，或集成PostGIS扩展(GaussDB特有)"
    },
    {
        "id": "MYSQL-DT-022", "name": "BIT(n)",
        "severity": "warning", "score_deduction": 3,
        "source_type": "BIT(n)", "target_type": "BIT(n)",
        "compatible": True,
        "note": "DWS支持BIT类型但n不能超过64",
        "migration_difficulty": "低",
        "migration_suggestion": "BIT(1)常用作boolean，建议改为BOOLEAN"
    },
]
