"""Teradata -> DWS 数据类型兼容性规则"""

DATA_TYPE_RULES = [
    {
        "id": "TD-DT-001", "name": "BYTEINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "BYTEINT (1字节, 0~255)",
        "target_type": "SMALLINT (2字节, -32768~32767)",
        "compatible": True,
        "note": "存储空间略增，数据范围兼容"
    },
    {
        "id": "TD-DT-002", "name": "SMALLINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "SMALLINT",
        "target_type": "SMALLINT",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "TD-DT-003", "name": "INTEGER/INT",
        "severity": "info", "score_deduction": 0,
        "source_type": "INTEGER/INT",
        "target_type": "INTEGER/INT",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "TD-DT-004", "name": "BIGINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "BIGINT",
        "target_type": "BIGINT",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "TD-DT-005", "name": "DECIMAL/NUMERIC",
        "severity": "info", "score_deduction": 0,
        "source_type": "DECIMAL(p,s)/NUMERIC(p,s)",
        "target_type": "NUMERIC(p,s)",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "TD-DT-006", "name": "FLOAT/REAL/DOUBLE",
        "severity": "info", "score_deduction": 0,
        "source_type": "FLOAT/REAL/DOUBLE PRECISION",
        "target_type": "FLOAT4/FLOAT8",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-DT-007", "name": "CHAR(n)/VARCHAR(n)",
        "severity": "info", "score_deduction": 0,
        "source_type": "CHAR(n), VARCHAR(n)",
        "target_type": "CHAR(n), VARCHAR(n)",
        "compatible": True,
        "note": "兼容; 注意TD中n是字节数, DWS中n是字符数(UTF-8)",
        "migration_difficulty": "低",
        "migration_suggestion": "CHAR(n)/VARCHAR(n)长度一般无需调整; 确认有中文时长度是否足够"
    },
    {
        "id": "TD-DT-008", "name": "CLOB",
        "severity": "info", "score_deduction": 0,
        "source_type": "CLOB",
        "target_type": "TEXT",
        "compatible": True,
        "note": "CLOB->TEXT功能对等"
    },
    {
        "id": "TD-DT-009", "name": "BLOB",
        "severity": "info", "score_deduction": 0,
        "source_type": "BLOB",
        "target_type": "BYTEA",
        "compatible": True,
        "note": "BLOB->BYTEA功能对等"
    },
    {
        "id": "TD-DT-010", "name": "VARBYTE(n)",
        "severity": "info", "score_deduction": 0,
        "source_type": "VARBYTE(n)",
        "target_type": "BYTEA",
        "compatible": True,
        "note": "VARBYTE->BYTEA功能对等"
    },
    {
        "id": "TD-DT-011", "name": "DATE",
        "severity": "info", "score_deduction": 0,
        "source_type": "DATE",
        "target_type": "DATE",
        "compatible": True,
        "note": "兼容; TD模式下DATE转TIMESTAMP行为差异见函数规则"
    },
    {
        "id": "TD-DT-012", "name": "TIME/TIMESTAMP",
        "severity": "info", "score_deduction": 0,
        "source_type": "TIME, TIMESTAMP",
        "target_type": "TIME, TIMESTAMP",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-DT-013", "name": "TIMESTAMP WITH TIME ZONE",
        "severity": "info", "score_deduction": 0,
        "source_type": "TIMESTAMP WITH TIME ZONE",
        "target_type": "TIMESTAMPTZ",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-DT-014", "name": "INTERVAL",
        "severity": "info", "score_deduction": 0,
        "source_type": "INTERVAL",
        "target_type": "INTERVAL",
        "compatible": True,
        "note": "兼容"
    },
    {
        "id": "TD-DT-015", "name": "PERIOD(时间周期类型)",
        "severity": "error", "score_deduction": 8,
        "source_type": "PERIOD(DATE), PERIOD(TIMESTAMP)",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持PERIOD类型，需拆分为起止字段",
        "migration_difficulty": "中",
        "migration_suggestion": "PERIOD(DATE)->start_date DATE, end_date DATE; 查询改用BETWEEN"
    },
]
