"""SQL Server -> DWS 数据类型兼容性规则"""

DATA_TYPE_RULES = [
    {
        "id": "MSSQL-DT-001", "name": "TINYINT",
        "severity": "warning", "score_deduction": 2,
        "source_type": "TINYINT", "target_type": "SMALLINT",
        "compatible": True,
        "note": "SQL Server TINYINT(0-255) 映射为 DWS SMALLINT，注意范围差异",
        "migration_difficulty": "低",
        "migration_suggestion": "因SQL Server TINYINT范围仅为0-255，可直接映射为DWS SMALLINT"
    },
    {
        "id": "MSSQL-DT-002", "name": "SMALLINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "SMALLINT", "target_type": "SMALLINT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-003", "name": "INT",
        "severity": "info", "score_deduction": 0,
        "source_type": "INT", "target_type": "INT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-004", "name": "BIGINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "BIGINT", "target_type": "BIGINT",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-005", "name": "BIT (布尔)",
        "severity": "info", "score_deduction": 0,
        "source_type": "BIT", "target_type": "BOOLEAN",
        "compatible": True, "note": "语义对等，DWS BIT也可用"
    },
    {
        "id": "MSSQL-DT-006", "name": "DECIMAL/NUMERIC",
        "severity": "info", "score_deduction": 0,
        "source_type": "DECIMAL(p,s)/NUMERIC(p,s)", "target_type": "NUMERIC(p,s)",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-007", "name": "MONEY / SMALLMONEY",
        "severity": "warning", "score_deduction": 2,
        "source_type": "MONEY/SMALLMONEY", "target_type": "NUMERIC(19,4)",
        "compatible": True,
        "note": "映射为NUMERIC(19,4)，功能对等，精度无损失",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 MONEY -> NUMERIC(19,4), SMALLMONEY -> NUMERIC(10,4)"
    },
    {
        "id": "MSSQL-DT-008", "name": "FLOAT/REAL",
        "severity": "info", "score_deduction": 0,
        "source_type": "FLOAT/REAL", "target_type": "FLOAT8/FLOAT4",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-009", "name": "DATE",
        "severity": "info", "score_deduction": 0,
        "source_type": "DATE", "target_type": "DATE",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DT-010", "name": "DATETIME / DATETIME2",
        "severity": "warning", "score_deduction": 2,
        "source_type": "DATETIME/DATETIME2", "target_type": "TIMESTAMP",
        "compatible": True,
        "note": "映射为DWS TIMESTAMP(无时区)，精度差异注意: DATETIME约1/300秒, DATETIME2最高100ns",
        "migration_difficulty": "低",
        "migration_suggestion": "DATETIME -> TIMESTAMP; DATETIME2(n) -> TIMESTAMP(n)"
    },
    {
        "id": "MSSQL-DT-011", "name": "SMALLDATETIME",
        "severity": "warning", "score_deduction": 2,
        "source_type": "SMALLDATETIME", "target_type": "TIMESTAMP",
        "compatible": True,
        "note": "SQL Server SMALLDATETIME(分钟精度) 映射为DWS TIMESTAMP(无精度损失)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 SMALLDATETIME -> TIMESTAMP"
    },
    {
        "id": "MSSQL-DT-012", "name": "DATETIMEOFFSET",
        "severity": "warning", "score_deduction": 3,
        "source_type": "DATETIMEOFFSET", "target_type": "TIMESTAMPTZ 或 VARCHAR",
        "compatible": True,
        "note": "DWS无原生DATETIMEOFFSET类型，使用TIMESTAMPTZ或TEXT存储偏移量",
        "migration_difficulty": "中",
        "migration_suggestion": "使用TIMESTAMP WITH TIME ZONE或拆分为时间+偏移量两字段"
    },
    {
        "id": "MSSQL-DT-013", "name": "TIME",
        "severity": "warning", "score_deduction": 3,
        "source_type": "TIME(n)", "target_type": "INTERVAL 或 TIME",
        "compatible": True,
        "note": "DWS支持TIME类型，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "直接映射为DWS TIME类型"
    },
    {
        "id": "MSSQL-DT-014", "name": "CHAR/VARCHAR",
        "severity": "info", "score_deduction": 0,
        "source_type": "CHAR(n)/VARCHAR(n)", "target_type": "CHAR(n)/VARCHAR(n)",
        "compatible": True,
        "note": "基本兼容。注意SQL Server中n是字符数，DWS中n是字节数，中文场景需调整长度"
    },
    {
        "id": "MSSQL-DT-015", "name": "NCHAR/NVARCHAR",
        "severity": "warning", "score_deduction": 2,
        "source_type": "NCHAR(n)/NVARCHAR(n)", "target_type": "CHAR(n)/VARCHAR(n)",
        "compatible": True,
        "note": "统一为CHAR/VARCHAR，DWS内部使用UTF-8编码处理Unicode",
        "migration_difficulty": "低",
        "migration_suggestion": "NCHAR(n)/NVARCHAR(n) -> VARCHAR(n)"
    },
    {
        "id": "MSSQL-DT-016", "name": "TEXT / NTEXT",
        "severity": "warning", "score_deduction": 2,
        "source_type": "TEXT/NTEXT", "target_type": "TEXT",
        "compatible": True,
        "note": "映射为DWS TEXT类型，兼容",
        "migration_difficulty": "低",
        "migration_suggestion": "TEXT/NTEXT -> TEXT"
    },
    {
        "id": "MSSQL-DT-017", "name": "BINARY/VARBINARY",
        "severity": "warning", "score_deduction": 2,
        "source_type": "BINARY(n)/VARBINARY(n)", "target_type": "BYTEA",
        "compatible": True,
        "note": "二进制类型映射为BYTEA，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "BINARY/VARBINARY -> BYTEA"
    },
    {
        "id": "MSSQL-DT-018", "name": "IMAGE",
        "severity": "warning", "score_deduction": 2,
        "source_type": "IMAGE", "target_type": "BYTEA",
        "compatible": True,
        "note": "IMAGE(已废弃但兼容) 映射为 BYTEA",
        "migration_difficulty": "低",
        "migration_suggestion": "IMAGE -> BYTEA"
    },
    {
        "id": "MSSQL-DT-019", "name": "UNIQUEIDENTIFIER",
        "severity": "warning", "score_deduction": 2,
        "source_type": "UNIQUEIDENTIFIER", "target_type": "UUID",
        "compatible": True,
        "note": "DWS支持UUID类型(需uuid-ossp扩展)",
        "migration_difficulty": "低",
        "migration_suggestion": "UNIQUEIDENTIFIER -> UUID; NEWID() -> UUID_GENERATE_V4()"
    },
    {
        "id": "MSSQL-DT-020", "name": "XML",
        "severity": "warning", "score_deduction": 4,
        "source_type": "XML", "target_type": "TEXT 或 JSON",
        "compatible": True,
        "note": "DWS不支持原生XML类型，使用TEXT存储或JSON处理",
        "migration_difficulty": "中",
        "migration_suggestion": "XML类型改为TEXT，XML查询函数(xml.value, xml.exist等)需重写"
    },
    {
        "id": "MSSQL-DT-021", "name": "HIERARCHYID",
        "severity": "error", "score_deduction": 8,
        "source_type": "HIERARCHYID", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server HIERARCHYID层级类型，DWS不直接支持",
        "migration_difficulty": "高",
        "migration_suggestion": "使用路径编码(VARCHAR + 层级编码)或闭包表(Closure Table)替代"
    },
    {
        "id": "MSSQL-DT-022", "name": "GEOGRAPHY / GEOMETRY",
        "severity": "error", "score_deduction": 8,
        "source_type": "GEOGRAPHY/GEOMETRY", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server空间数据类型，DWS原生不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "使用JSONB存储坐标数据，或在应用层处理空间计算"
    },
    {
        "id": "MSSQL-DT-023", "name": "SQL_VARIANT",
        "severity": "error", "score_deduction": 6,
        "source_type": "SQL_VARIANT", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server SQL_VARIANT类似动态类型，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "根据实际数据选择最合适的固定类型，或使用TEXT+应用层解析"
    },
    {
        "id": "MSSQL-DT-024", "name": "ROWVERSION / TIMESTAMP",
        "severity": "error", "score_deduction": 5,
        "source_type": "ROWVERSION/TIMESTAMP", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server ROWVERSION是数据库级版本号，DWS无对应类型",
        "migration_difficulty": "中",
        "migration_suggestion": "移除或改为应用层实现乐观锁(使用时间戳+条件更新)"
    },
    {
        "id": "MSSQL-DT-025", "name": "CURSOR类型",
        "severity": "error", "score_deduction": 6,
        "source_type": "CURSOR (变量/参数)", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server CURSOR数据类型，DWS存储过程中不支持游标变量",
        "migration_difficulty": "高",
        "migration_suggestion": "改为基于集合的操作(SET-based)避免使用游标"
    },
    {
        "id": "MSSQL-DT-026", "name": "TABLE类型(表值参数)",
        "severity": "error", "score_deduction": 6,
        "source_type": "TABLE (用户定义表类型)", "target_type": "不支持",
        "compatible": False,
        "note": "SQL Server表值参数(TVP)，DWS存储过程中不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "改用临时表或数组参数替代"
    },
]
