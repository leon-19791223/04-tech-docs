"""Teradata -> DWS DDL兼容性规则
涵盖: 主索引(PI)/分区/Volatile表/MULTISET/SET/列存储等
"""

DDL_RULES = [
    # ================================================================
    # 主索引与分布键
    # ================================================================
    {
        "id": "TD-DDL-001",
        "name": "主索引(PI)与分布键",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Teradata主索引(Primary Index)是数据分布策略，DWS使用DISTRIBUTE BY HASH替代",
        "source_pattern": "CREATE TABLE t (col1 INT, col2 VARCHAR(10)) PRIMARY INDEX (col1)",
        "target_solution": "CREATE TABLE t (col1 INT, col2 VARCHAR(10)) DISTRIBUTE BY HASH (col1)",
        "compatible": True,
        "note": "功能对等，但Teradata PI支持单表最多64列复合索引，DWS分布键建议选高基数列",
        "migration_difficulty": "低",
        "migration_suggestion": "PI(col) -> DISTRIBUTE BY HASH(col); 复合PI选基数最高的列"
    },
    {
        "id": "TD-DDL-002",
        "name": "唯一主索引(UPI)",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Teradata UPI=UNIQUE PRIMARY INDEX，DWS用UNIQUE约束+HASH分布替代",
        "source_pattern": "CREATE TABLE t (col1 INT NOT NULL) UNIQUE PRIMARY INDEX (col1)",
        "target_solution": "CREATE TABLE t (col1 INT NOT NULL) DISTRIBUTE BY HASH(col1); 添加UNIQUE约束",
        "compatible": True,
        "note": "DWS的UNIQUE约束在列存表有限制，行存表完全兼容",
        "migration_difficulty": "低",
        "migration_suggestion": "分解UPI为UNIQUE约束+DISTRIBUTE BY"
    },
    {
        "id": "TD-DDL-003",
        "name": "非唯一主索引(NUPI)",
        "severity": "info",
        "score_deduction": 0,
        "description": "Teradata NUPI无需UNIQUE限制，对应DWS普通DISTRIBUTE BY",
        "source_pattern": "CREATE TABLE t (col1 INT) PRIMARY INDEX (col1)",
        "target_solution": "CREATE TABLE t (col1 INT) DISTRIBUTE BY HASH(col1)",
        "compatible": True,
        "note": "完全对等"
    },
    {
        "id": "TD-DDL-004",
        "name": "次级索引(SI/JI)",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Teradata次级索引(Secondary Index/Join Index)在DWS中用普通索引替代",
        "source_pattern": "CREATE INDEX idx_name ON table(col) / CREATE JOIN INDEX ji_name AS SELECT ...",
        "target_solution": "CREATE INDEX idx_name ON table(col) USING BTREE",
        "compatible": True,
        "note": "Join Index在DWS中使用物化视图替代",
        "migration_difficulty": "中",
        "migration_suggestion": "SI->普通B-tree索引; Join Index->物化视图或列存"
    },

    # ================================================================
    # SET/MULTISET 表
    # ================================================================
    {
        "id": "TD-DDL-005",
        "name": "SET表(去重)",
        "severity": "info",
        "score_deduction": 0,
        "description": "Teradata SET表自动去重，DWS默认允许重复行，需显式去重",
        "source_pattern": "CREATE SET TABLE t (col1 INT) PRIMARY INDEX (col1)",
        "target_solution": "CREATE TABLE t (col1 INT) DISTRIBUTE BY HASH(col1); 使用DISTINCT去重",
        "compatible": True,
        "note": "DWS无SET表概念，查询时使用SELECT DISTINCT实现"
    },
    {
        "id": "TD-DDL-006",
        "name": "MULTISET表(允许重复)",
        "severity": "info",
        "score_deduction": 0,
        "description": "Teradata MULTISET表对应DWS普通表，行为一致",
        "source_pattern": "CREATE MULTISET TABLE t (col1 INT) PRIMARY INDEX (col1)",
        "target_solution": "CREATE TABLE t (col1 INT) DISTRIBUTE BY HASH(col1)",
        "compatible": True,
        "note": "完全兼容"
    },

    # ================================================================
    # Volatile 表
    # ================================================================
    {
        "id": "TD-DDL-007",
        "name": "Volatile临时表",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Teradata Volatile表在DWS中使用TEMPORARY表替代",
        "source_pattern": "CREATE VOLATILE TABLE vt AS (SELECT * FROM t) WITH DATA PRIMARY INDEX (col1)",
        "target_solution": "CREATE TEMPORARY TABLE vt AS SELECT * FROM t DISTRIBUTE BY HASH(col1)",
        "compatible": True,
        "note": "功能对等，Teradata Volatile表仅当前会话可见且自动删除，DWS TEMPORARY表同",
        "migration_difficulty": "低",
        "migration_suggestion": "CREATE VOLATILE TABLE -> CREATE TEMPORARY TABLE"
    },
    {
        "id": "TD-DDL-008",
        "name": "Volatile表WITH DATA",
        "severity": "warning",
        "score_deduction": 2,
        "description": "Teradata Volatile表支持ON COMMIT PRESERVE ROWS，DWS默认为DELETE ROWS",
        "source_pattern": "CREATE VOLATILE TABLE vt AS (...) WITH DATA ON COMMIT PRESERVE ROWS",
        "target_solution": "CREATE TEMPORARY TABLE vt AS SELECT ... DISTRIBUTE BY HASH(col1);",
        "compatible": True,
        "note": "DWS临时表在事务结束默认清空，若需跨事务请评估业务场景",
        "migration_difficulty": "低"
    },

    # ================================================================
    # 分区表
    # ================================================================
    {
        "id": "TD-DDL-009",
        "name": "Teradata分区(PARTITION BY)",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Teradata分区列(RANGE_N/PARTITION BY RANGE_N)与DWS分区语法差异",
        "source_pattern": "PARTITION BY RANGE_N(transaction_date BETWEEN DATE '2024-01-01' AND '2025-12-31' EACH INTERVAL '1' MONTH)",
        "target_solution": "PARTITION BY RANGE(transaction_date) (PARTITION p202401 VALUES LESS THAN ('2024-02-01'), ...)",
        "compatible": True,
        "note": "功能对等但语法差异大，Teradata的RANGE_N语法需改写",
        "migration_difficulty": "中",
        "migration_suggestion": "将RANGE_N语法改写为DWS的标准RANGE分区语法"
    },
    {
        "id": "TD-DDL-010",
        "name": "Teradata RANGE_N/PARTITION BY 表达式",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Teradata支持分区表达式(RANGE_N/CASE_N)，DWS不支持",
        "source_pattern": "PARTITION BY CASE_N(x BETWEEN 1 AND 10)",
        "target_solution": "重建为RANGE分区或列表分区",
        "compatible": True,
        "note": "DWS 9.1.0已支持部分分区表达式功能",
        "migration_difficulty": "中"
    },

    # ================================================================
    # 数据类型相关DDL
    # ================================================================
    {
        "id": "TD-DDL-011",
        "name": "Teradata BYTEINT/SMALLINT",
        "severity": "info",
        "score_deduction": 0,
        "description": "BYTEINT(1字节)与DWS SMALLINT(2字节)精度不同",
        "source_pattern": "col1 BYTEINT",
        "target_solution": "col1 SMALLINT (或更严格的col1 INTEGER)",
        "compatible": True,
        "note": "BYTEINT范围0-255，SMALLINT范围-32768~32767，存储空间略增"
    },
    {
        "id": "TD-DDL-012",
        "name": "Teradata PERIOD数据类型",
        "severity": "error",
        "score_deduction": 8,
        "description": "Teradata PERIOD(时间周期)数据类型在DWS中不支持",
        "source_pattern": "CREATE TABLE t (period_col PERIOD(DATE))",
        "target_solution": "拆分为起止时间字段: start_date DATE, end_date DATE",
        "compatible": False,
        "note": "DWS不支持PERIOD类型，需拆分为两个字段",
        "migration_difficulty": "中",
        "migration_suggestion": "将PERIOD(DATE)拆为start_date和end_date两个字段，使用BETWEEN查询"
    },
    {
        "id": "TD-DDL-013",
        "name": "VARBYTE类型",
        "severity": "info",
        "score_deduction": 0,
        "description": "Teradata VARBYTE对应DWS BYTEA",
        "source_pattern": "col1 VARBYTE(n)",
        "target_solution": "col1 BYTEA",
        "compatible": True,
        "note": "完全兼容"
    },
]
