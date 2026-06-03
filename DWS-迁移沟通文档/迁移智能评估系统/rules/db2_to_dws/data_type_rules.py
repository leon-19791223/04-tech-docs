"""DB2 -> DWS 数据类型兼容性规则

基于 DB2_DWS_迁移解决方案_证券基金资管行业_展开版 第2章
"""

DATA_TYPE_RULES = [
    {
        "id": "DB2-DT-001", "name": "SMALLINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "SMALLINT", "target_type": "SMALLINT",
        "compatible": True, "note": "直接映射，范围一致"
    },
    {
        "id": "DB2-DT-002", "name": "INTEGER / INT",
        "severity": "info", "score_deduction": 0,
        "source_type": "INTEGER / INT", "target_type": "INTEGER / INT",
        "compatible": True, "note": "直接映射"
    },
    {
        "id": "DB2-DT-003", "name": "BIGINT",
        "severity": "info", "score_deduction": 0,
        "source_type": "BIGINT", "target_type": "BIGINT",
        "compatible": True, "note": "直接映射"
    },
    {
        "id": "DB2-DT-004", "name": "DECIMAL(p,s)",
        "severity": "info", "score_deduction": 0,
        "source_type": "DECIMAL(p,s)", "target_type": "NUMERIC(p,s)",
        "compatible": True,
        "note": "推荐使用NUMERIC，精度完全兼容。注意: 资产类字段精度必须严格匹配，差异不可超过0.01元"
    },
    {
        "id": "DB2-DT-005", "name": "REAL / DOUBLE",
        "severity": "info", "score_deduction": 0,
        "source_type": "REAL / DOUBLE", "target_type": "FLOAT4 / FLOAT8",
        "compatible": True, "note": "直接映射"
    },
    {
        "id": "DB2-DT-006", "name": "VARCHAR(n) 长度语义差异",
        "severity": "error", "score_deduction": 10,
        "source_type": "VARCHAR(n) — n=字符数",
        "target_type": "VARCHAR(n) — n=字节数(UTF-8)",
        "compatible": False,
        "note": "DB2中n是字符数，DWS中n是字节数。UTF-8下中文占3字节，需按3倍扩展: VARCHAR(50)→VARCHAR(150)",
        "migration_difficulty": "中",
        "migration_suggestion": "对所有VARCHAR字段进行数据抽样分析，确认实际字符分布。含中文列统一按3倍扩充分配"
    },
    {
        "id": "DB2-DT-007", "name": "CHAR(n) 长度语义差异",
        "severity": "warning", "score_deduction": 4,
        "source_type": "CHAR(n) — n=字符数",
        "target_type": "CHAR(n) — n=字节数",
        "compatible": True,
        "note": "与VARCHAR类似但CHAR是定长。若列仅存字母数字（如证券代码），可直接映射",
        "migration_difficulty": "低",
        "migration_suggestion": "字母数字列直接映射; 含中文列按3倍扩展"
    },
    {
        "id": "DB2-DT-008", "name": "CLOB",
        "severity": "warning", "score_deduction": 3,
        "source_type": "CLOB", "target_type": "TEXT",
        "compatible": True,
        "note": "建议转换为TEXT类型; 超大型CLOB(>1GB)建议使用OBS对象存储",
        "migration_difficulty": "低",
        "migration_suggestion": "CLOB -> TEXT; 超大对象 -> OBS存储路径引用"
    },
    {
        "id": "DB2-DT-009", "name": "BLOB",
        "severity": "warning", "score_deduction": 3,
        "source_type": "BLOB", "target_type": "BYTEA",
        "compatible": True,
        "note": "二进制数据转换为BYTEA; 超大型BLOB(>1GB)建议使用OBS对象存储",
        "migration_difficulty": "低",
        "migration_suggestion": "BLOB -> BYTEA; 超大对象 -> OBS"
    },
    {
        "id": "DB2-DT-010", "name": "XML (pureXML)",
        "severity": "error", "score_deduction": 6,
        "source_type": "XML (pureXML)", "target_type": "TEXT / JSON",
        "compatible": False,
        "note": "DB2对XML有原生支持(pureXML)，DWS XML支持有限",
        "migration_difficulty": "中",
        "migration_suggestion": "场景一：仅存储不做XQuery→TEXT; 场景二：需结构化查询→JSON/JSONB; 场景三：保留完整语义→TEXT+应用层解析"
    },
    {
        "id": "DB2-DT-011", "name": "TIMESTAMP(p) 精度差异",
        "severity": "warning", "score_deduction": 4,
        "source_type": "TIMESTAMP(p) — p最大12",
        "target_type": "TIMESTAMP(p) — p最大6",
        "compatible": True,
        "note": "DB2支持最高12位小数秒精度，DWS最高6位(微秒)。超6位精度应用需改造",
        "migration_difficulty": "中",
        "migration_suggestion": "检查TIMESTAMP定义精度p: p<=6直接映射; p>6需改造应用逻辑"
    },
    {
        "id": "DB2-DT-012", "name": "DATE / TIME",
        "severity": "info", "score_deduction": 0,
        "source_type": "DATE / TIME", "target_type": "DATE / TIME",
        "compatible": True, "note": "直接映射"
    },
    {
        "id": "DB2-DT-013", "name": "GRAPHIC / VARGRAPHIC",
        "severity": "warning", "score_deduction": 5,
        "source_type": "GRAPHIC(n) / VARGRAPHIC(n)",
        "target_type": "VARCHAR(n*3)",
        "compatible": True,
        "note": "DB2双字节类型(存储中文/日文等)，按UTF-8转换为VARCHAR，长度按3倍扩展",
        "migration_difficulty": "低",
        "migration_suggestion": "GRAPHIC(n) -> CHAR(n*3); VARGRAPHIC(n) -> VARCHAR(n*3)"
    },
    {
        "id": "DB2-DT-014", "name": "DBCLOB",
        "severity": "warning", "score_deduction": 5,
        "source_type": "DBCLOB", "target_type": "TEXT",
        "compatible": True,
        "note": "DB2双字节大对象，映射为TEXT类型",
        "migration_difficulty": "低",
        "migration_suggestion": "DBCLOB -> TEXT"
    },
    {
        "id": "DB2-DT-015", "name": "BOOLEAN",
        "severity": "info", "score_deduction": 0,
        "source_type": "BOOLEAN", "target_type": "BOOLEAN",
        "compatible": True, "note": "直接映射(DWS原生支持BOOLEAN)"
    },
    {
        "id": "DB2-DT-016", "name": "ROWID",
        "severity": "error", "score_deduction": 5,
        "source_type": "ROWID", "target_type": "不支持",
        "compatible": False,
        "note": "DB2 ROWID为物理行标识符，DWS无对应类型",
        "migration_difficulty": "低",
        "migration_suggestion": "移除ROWID列引用; 如需唯一标识，使用UUID或自增序列替代"
    },
    {
        "id": "DB2-DT-017", "name": "REFCURSOR",
        "severity": "error", "score_deduction": 6,
        "source_type": "REFCURSOR (游标返回类型)",
        "target_type": "REFCURSOR (功能受限)",
        "compatible": False,
        "note": "DB2存储过程中REFCURSOR作为OUT参数返回结果集，DWS中REFCURSOR使用方式不同",
        "migration_difficulty": "高",
        "migration_suggestion": "DWS存储过程使用REF CURSOR: CREATE FUNCTION ... RETURNS SETOF record / TABLE"
    },
    {
        "id": "DB2-DT-018", "name": "特殊货币/金额精度要求",
        "severity": "warning", "score_deduction": 3,
        "source_type": "DECIMAL(18,2) / DECIMAL(18,4) 等资产金额字段",
        "target_type": "NUMERIC(18,2) / NUMERIC(18,4)",
        "compatible": True,
        "note": "证券基金行业对金额精度要求极高，必须确保DECIMAL→NUMERIC映射无精度损失。建议迁移后逐字段进行SUM比对",
        "migration_difficulty": "低",
        "migration_suggestion": "DECIMAL(p,s) -> NUMERIC(p,s) 精度严格一致; 迁移后进行SUM/MIN/MAX全量校验"
    },
]
