"""Oracle -> DWS 数据类型兼容性规则"""

DATA_TYPE_RULES = [
    # ================================================================
    # 字符类型
    # ================================================================
    {
        "id": "ORA-DT-001", "name": "VARCHAR2",
        "severity": "warning", "score_deduction": 2,
        "source_type": "VARCHAR2(n CHAR/BYTE)",
        "target_type": "VARCHAR(n)",
        "compatible": True,
        "note": "Oracle默认BYTE语义，DWS为字符语义; 长度可能需要调整(n*3)",
        "migration_difficulty": "低",
        "migration_suggestion": "CHAR->CHAR长度不变; VARCHAR2(n)一般直接转为VARCHAR(n)"
    },
    {
        "id": "ORA-DT-002", "name": "CHAR/NCHAR",
        "severity": "info", "score_deduction": 0,
        "source_type": "CHAR(n), NCHAR(n)",
        "target_type": "CHAR(n), NCHAR(n)",
        "compatible": True,
        "note": "完全兼容"
    },
    {
        "id": "ORA-DT-003", "name": "NVARCHAR2",
        "severity": "info", "score_deduction": 0,
        "source_type": "NVARCHAR2(n)",
        "target_type": "VARCHAR(n)",
        "compatible": True,
        "note": "NVARCHAR2在DWS中没有直接对应，用VARCHAR替代即可"
    },
    {
        "id": "ORA-DT-004", "name": "CLOB",
        "severity": "warning", "score_deduction": 3,
        "source_type": "CLOB",
        "target_type": "TEXT",
        "compatible": True,
        "note": "功能对等，但DWS中TEXT长度限制与Oracle CLOB不同，超大CLOB需拆分",
        "migration_difficulty": "低",
        "migration_suggestion": "CLOB->TEXT直接转换; 超大型CLOB(>1GB)需评估存储方案"
    },
    {
        "id": "ORA-DT-005", "name": "NCLOB",
        "severity": "warning", "score_deduction": 3,
        "source_type": "NCLOB",
        "target_type": "TEXT",
        "compatible": True,
        "note": "处理方式同CLOB->TEXT，Unicode字符无额外处理"
    },
    {
        "id": "ORA-DT-006", "name": "LONG / LONG RAW",
        "severity": "error", "score_deduction": 8,
        "source_type": "LONG, LONG RAW",
        "target_type": "TEXT / BYTEA",
        "compatible": False,
        "note": "Oracle已废弃类型，建议在迁移前转换为CLOB/BLOB",
        "migration_difficulty": "中",
        "migration_suggestion": "迁移前先转换为CLOB/BLOB; LONG->CLOB->TEXT; LONG RAW->BLOB->BYTEA"
    },

    # ================================================================
    # 数值类型
    # ================================================================
    {
        "id": "ORA-DT-007", "name": "NUMBER / DECIMAL",
        "severity": "info", "score_deduction": 0,
        "source_type": "NUMBER(p,s), NUMBER",
        "target_type": "NUMERIC(p,s), NUMERIC",
        "compatible": True,
        "note": "完全兼容，Oracle NUMBER(p,s) 可直接转为 NUMERIC(p,s)"
    },
    {
        "id": "ORA-DT-008", "name": "FLOAT / BINARY_FLOAT",
        "severity": "info", "score_deduction": 0,
        "source_type": "FLOAT(n), BINARY_FLOAT",
        "target_type": "FLOAT(n), FLOAT4",
        "compatible": True,
        "note": "兼容，精度映射需确认: Oracle FLOAT->DWS FLOAT"
    },
    {
        "id": "ORA-DT-009", "name": "BINARY_DOUBLE",
        "severity": "info", "score_deduction": 0,
        "source_type": "BINARY_DOUBLE",
        "target_type": "FLOAT8 / DOUBLE PRECISION",
        "compatible": True,
        "note": "兼容，精度一致"
    },
    {
        "id": "ORA-DT-010", "name": "PLS_INTEGER / BINARY_INTEGER",
        "severity": "info", "score_deduction": 0,
        "source_type": "PLS_INTEGER, BINARY_INTEGER",
        "target_type": "INTEGER / INT",
        "compatible": True,
        "note": "PL/SQL中的类型，DDL中不出现，函数内使用时替换为INTEGER"
    },

    # ================================================================
    # 日期时间类型
    # ================================================================
    {
        "id": "ORA-DT-011", "name": "DATE含时间部分",
        "severity": "warning", "score_deduction": 3,
        "source_type": "DATE (Oracle含时分秒)",
        "target_type": "TIMESTAMP(0) WITHOUT TIME ZONE",
        "compatible": True,
        "note": "Oracle DATE包含时间，DWS DATE仅日期; 需改为TIMESTAMP",
        "migration_difficulty": "中",
        "migration_suggestion": "涉及DATE的SQL中若使用时间运算，需改为TIMESTAMP并调整函数"
    },
    {
        "id": "ORA-DT-012", "name": "TIMESTAMP WITH TIME ZONE",
        "severity": "info", "score_deduction": 0,
        "source_type": "TIMESTAMP WITH TIME ZONE",
        "target_type": "TIMESTAMP WITH TIME ZONE",
        "compatible": True,
        "note": "兼容，时区处理基本一致"
    },
    {
        "id": "ORA-DT-013", "name": "TIMESTAMP WITH LOCAL TIME ZONE",
        "severity": "warning", "score_deduction": 3,
        "source_type": "TIMESTAMP WITH LOCAL TIME ZONE",
        "target_type": "TIMESTAMP WITH TIME ZONE",
        "compatible": True,
        "note": "Oracle的LTZ在DWS中没有直接对应，用TIMESTAMPTZ替代，需调整时区转换逻辑",
        "migration_difficulty": "中",
        "migration_suggestion": "改为TIMESTAMPTZ，在查询层使用AT TIME ZONE实现本地时区转换"
    },
    {
        "id": "ORA-DT-014", "name": "INTERVAL数据类型",
        "severity": "info", "score_deduction": 0,
        "source_type": "INTERVAL DAY TO SECOND, INTERVAL YEAR TO MONTH",
        "target_type": "INTERVAL",
        "compatible": True,
        "note": "兼容"
    },

    # ================================================================
    # 大对象与二进制
    # ================================================================
    {
        "id": "ORA-DT-015", "name": "BLOB",
        "severity": "warning", "score_deduction": 3,
        "source_type": "BLOB",
        "target_type": "BYTEA",
        "compatible": True,
        "note": "功能对等，但DWS BYTEA大小限制需确认(<1GB)",
        "migration_difficulty": "低",
        "migration_suggestion": "BLOB->BYTEA; 超大BLOB对象建议改为对象存储+DB存路径"
    },
    {
        "id": "ORA-DT-016", "name": "BFILE",
        "severity": "error", "score_deduction": 8,
        "source_type": "BFILE",
        "target_type": "不支持",
        "compatible": False,
        "note": "BFILE是Oracle外部文件引用，DWS不支持",
        "migration_difficulty": "中",
        "migration_suggestion": "将BFILE引用的外部文件迁移到对象存储，DB中存文件路径"
    },

    # ================================================================
    # 特殊类型
    # ================================================================
    {
        "id": "ORA-DT-017", "name": "RAW",
        "severity": "info", "score_deduction": 0,
        "source_type": "RAW(n)",
        "target_type": "BYTEA",
        "compatible": True,
        "note": "兼容，Oracle RAW是变长十六进制，DWS BYTEA对等"
    },
    {
        "id": "ORA-DT-018", "name": "ROWID / UROWID",
        "severity": "error", "score_deduction": 8,
        "source_type": "ROWID, UROWID",
        "target_type": "不支持",
        "compatible": False,
        "note": "Oracle物理行标识，DWS中无对应类型",
        "migration_difficulty": "高",
        "migration_suggestion": "使用主键或唯一标识符替代ROWID; 检查代码中是否有ROWID用法"
    },
    {
        "id": "ORA-DT-019", "name": "XMLTYPE",
        "severity": "error", "score_deduction": 6,
        "source_type": "XMLTYPE",
        "target_type": "不支持",
        "compatible": False,
        "note": "Oracle XMLTYPE在DWS中无直接对应",
        "migration_difficulty": "中",
        "migration_suggestion": "改为TEXT/CLOB存储XML文本; 或使用JSONB（如果XML结构可转JSON）"
    },
    {
        "id": "ORA-DT-020", "name": "SYS_GUID() / RAW(16)",
        "severity": "info", "score_deduction": 0,
        "source_type": "RAW(16) with SYS_GUID()",
        "target_type": "UUID with gen_random_uuid()",
        "compatible": True,
        "note": "功能对等，生成全局唯一标识符，语法替换即可",
        "migration_difficulty": "低",
        "migration_suggestion": "列类型: RAW(16)->UUID; 生成函数: SYS_GUID()->gen_random_uuid()"
    },
    {
        "id": "ORA-DT-021", "name": "用户自定义类型(UDT/ADT)",
        "severity": "error", "score_deduction": 10,
        "source_type": "CREATE TYPE ... AS OBJECT / AS TABLE / VARRAY",
        "target_type": "不支持",
        "compatible": False,
        "note": "DWS不支持用户自定义类型/对象/集合类型",
        "migration_difficulty": "高",
        "migration_suggestion": "对象类型: 拆为多列; 嵌套表/VARRAY: 改为关联表 + JSONB"
    },
    {
        "id": "ORA-DT-022", "name": "VARRAY嵌套表",
        "severity": "error", "score_deduction": 8,
        "source_type": "TYPE type_name IS VARRAY(n) OF ...",
        "target_type": "JSONB / 关联子表",
        "compatible": False,
        "note": "DWS不支持VARRAY集合类型",
        "migration_difficulty": "中",
        "migration_suggestion": "数组长度小且固定->JSONB; 长度不确定->创建关联子表"
    },
    {
        "id": "ORA-DT-023", "name": "ANYDATA / ANYTYPE",
        "severity": "error", "score_deduction": 10,
        "source_type": "ANYDATA, ANYTYPE, ANYDATASET",
        "target_type": "不支持",
        "compatible": False,
        "note": "Oracle动态类型系统，DWS不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "评估实际使用场景，使用JSONB或应用层多态替代"
    },
]
