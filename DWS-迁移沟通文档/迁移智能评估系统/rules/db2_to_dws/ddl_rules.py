"""DB2 -> DWS DDL兼容性规则

基于 DB2_DWS_迁移解决方案_证券基金资管行业_展开版 第3章
"""

DDL_RULES = [
    # ================================================================
    # 自增列与序列
    # ================================================================
    {
        "id": "DB2-DDL-001", "name": "GENERATED AS IDENTITY",
        "severity": "error", "score_deduction": 8,
        "description": "DB2 GENERATED ALWAYS/BY DEFAULT AS IDENTITY在DWS中需改为SEQUENCE+nextval",
        "source_pattern": "id BIGINT GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1)",
        "target_solution": "CREATE SEQUENCE seq_tablename START WITH 1 INCREMENT BY 1 CACHE 100; id BIGINT DEFAULT nextval('seq_tablename')",
        "compatible": False, "note": "需为每个自增列创建SEQUENCE，迁移后设置起始值: SELECT setval('seq', (SELECT MAX(id) FROM table))",
        "migration_difficulty": "中",
        "migration_suggestion": "通过脚本自动为每个IDENTITY列生成SEQUENCE并改写DDL；迁移后使用setval设置起始值"
    },
    {
        "id": "DB2-DDL-002", "name": "GENERATED AS 生成列",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2 GENERATED ALWAYS AS (expression) 生成列在DWS中兼容",
        "source_pattern": "col TYPE GENERATED ALWAYS AS (expr)",
        "target_solution": "col TYPE GENERATED ALWAYS AS (expr) STORED -- DWS语法兼容但需加STORED关键字",
        "compatible": True,
        "note": "DWS支持生成列但需加STORED关键字",
        "migration_difficulty": "低",
        "migration_suggestion": "在GENERATED ALWAYS AS表达式后追加STORED关键字"
    },
    # ================================================================
    # 分区表
    # ================================================================
    {
        "id": "DB2-DDL-003", "name": "RANGE分区语法差异",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2与DWS的分区DDL语法存在差异",
        "source_pattern": "PARTITION BY RANGE (col) (PARTITION p1 STARTING FROM '2024-01-01' ENDING AT '2024-12-31')",
        "target_solution": "PARTITION BY RANGE(col) (PARTITION p1 START('2024-01-01') END('2025-01-01'))",
        "compatible": True,
        "note": "功能对等，语法微调。DB2使用STARTING FROM/ENDING AT，DWS使用START/END或VALUES LESS THAN",
        "migration_difficulty": "低",
        "migration_suggestion": "脚本批量转换分区定义语法"
    },
    {
        "id": "DB2-DDL-004", "name": "哈希分区(HASH)",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 HASH分区与DWS HASH分区语法不同",
        "source_pattern": "PARTITION BY HASH (col) (PARTITION p1, PARTITION p2)",
        "target_solution": "DWS支持HASH分区但需指定分区数: PARTITION BY HASH(col) (PARTITION p1, PARTITION p2)",
        "compatible": True, "note": "语法接近，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "脚本批量转换分区语法"
    },
    {
        "id": "DB2-DDL-005", "name": "分布键设计(DISTRIBUTE BY)",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2无分布键概念，DWS需为每张表指定分布键",
        "source_pattern": "CREATE TABLE t (col INT) (DB2无分布键)",
        "target_solution": "CREATE TABLE t (col INT) DISTRIBUTE BY HASH(col) -- 必须指定分布键",
        "compatible": True,
        "note": "MPP架构核心差异。分布键选择直接影响查询性能，高频关联的表使用相同分布键",
        "migration_difficulty": "高",
        "migration_suggestion": "根据业务分析选择分布键: 1) JOIN亲和性—关联表使用相同分布键; 2) GROUP BY亲和性—与分组列一致; 3) 业务优先—最常用的JOIN条件"
    },
    {
        "id": "DB2-DDL-006", "name": "存储模型选择(行存/列存)",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2支持BLU列存，DWS需显式指定ORIENTATION",
        "source_pattern": "DB2表创建无行列存区分(或BLU)",
        "target_solution": "事实表(交易流水/行情/估值): WITH (ORIENTATION=COLUMN); 维度表/频繁UPDEL表: WITH (ORIENTATION=ROW)",
        "compatible": True,
        "note": "DWS行列混合存储，列存压缩比可达10:1，OLAP查询性能更优",
        "migration_difficulty": "中",
        "migration_suggestion": "交易流水/行情数据->列存; 产品信息/客户信息->行存; 每日快照表->列存"
    },
    # ================================================================
    # 约束
    # ================================================================
    {
        "id": "DB2-DDL-007", "name": "PRIMARY KEY / UNIQUE约束",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 PRIMARY KEY和UNIQUE约束在DWS中兼容",
        "source_pattern": "PRIMARY KEY (col) / UNIQUE (col)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-DDL-008", "name": "FOREIGN KEY外键约束",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2外键约束在DWS中语法兼容但MPP架构下建议在应用层保证",
        "source_pattern": "FOREIGN KEY (col) REFERENCES other(id)",
        "target_solution": "语法兼容但建议在ETL/应用层控制数据一致性",
        "compatible": True,
        "note": "DWS支持外键但不强制检查，MPP架构中外键影响导入性能",
        "migration_difficulty": "低",
        "migration_suggestion": "DDL可保留外键定义供文档参考; 生产环境建议在ETL/应用层保证一致性"
    },
    {
        "id": "DB2-DDL-009", "name": "CHECK约束",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 CHECK约束在DWS中兼容",
        "source_pattern": "col INT CHECK (col > 0)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-DDL-010", "name": "业务枚举值 CHECK 约束",
        "severity": "info", "score_deduction": 0,
        "description": "DB2中的CHECK约束枚举值直接映射到DWS",
        "source_pattern": "fund_type VARCHAR(10) CHECK (fund_type IN ('EQ','HY','BD','MM'))",
        "target_solution": "语法兼容，或改为引用维度表",
        "compatible": True,
        "note": "DWS不支持ENUM类型但CHECK约束完全兼容，推荐使用CHECK或维度表"
    },
    # ================================================================
    # 索引
    # ================================================================
    {
        "id": "DB2-DDL-011", "name": "CREATE INDEX语法",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 CREATE INDEX基本语法在DWS中兼容",
        "source_pattern": "CREATE INDEX idx ON t(col)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-DDL-012", "name": "唯一索引(UNIQUE INDEX)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2唯一索引在DWS中兼容",
        "source_pattern": "CREATE UNIQUE INDEX idx ON t(col)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 视图与同义词
    # ================================================================
    {
        "id": "DB2-DDL-013", "name": "CREATE VIEW",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 CREATE VIEW在DWS中兼容",
        "source_pattern": "CREATE VIEW v AS SELECT ...",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-DDL-014", "name": "CREATE ALIAS (别名/同义词)",
        "severity": "error", "score_deduction": 5,
        "description": "DB2 CREATE ALIAS在DWS中不支持",
        "source_pattern": "CREATE ALIAS alias_name FOR schema.table",
        "target_solution": "使用VIEW或search_path替代",
        "compatible": False, "note": "DWS无别名/Aliaz概念",
        "migration_difficulty": "低",
        "migration_suggestion": "CREATE ALIAS -> 创建同名VIEW访问实际表"
    },
    # ================================================================
    # DML差异
    # ================================================================
    {
        "id": "DB2-DDL-015", "name": "MERGE INTO语法差异",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 MERGE INTO与DWS语法略有差异",
        "source_pattern": "MERGE INTO target t USING source s ON cond WHEN MATCHED THEN UPDATE ...",
        "target_solution": "DWS支持MERGE INTO语法兼容，或使用INSERT...ON CONFLICT(PostgreSQL优写语法)",
        "compatible": True,
        "note": "两种语法都支持: 1)标准MERGE INTO兼容; 2)POSTGRES优写: INSERT...ON CONFLICT(col) DO UPDATE",
        "migration_difficulty": "低",
        "migration_suggestion": "可保留MERGE INTO; 简单upsert场景可改为INSERT...ON CONFLICT DO UPDATE"
    },
    {
        "id": "DB2-DDL-016", "name": "FETCH FIRST / LIMIT",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 FETCH FIRST n ROWS ONLY与DWS兼容",
        "source_pattern": "FETCH FIRST 10 ROWS ONLY",
        "target_solution": "FETCH FIRST 10 ROWS ONLY 或 LIMIT 10",
        "compatible": True, "note": "两种语法都兼容"
    },
    {
        "id": "DB2-DDL-017", "name": "分页查询(OFFSET/FETCH)",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 OFFSET m ROWS FETCH NEXT n ROWS ONLY与DWS兼容",
        "source_pattern": "OFFSET 10 ROWS FETCH NEXT 20 ROWS ONLY",
        "target_solution": "OFFSET 10 LIMIT 20 或 OFFSET 10 ROWS FETCH NEXT 20 ROWS ONLY",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "DB2-DDL-018", "name": "WITH RECURSIVE CTE",
        "severity": "info", "score_deduction": 0,
        "description": "DB2递归CTE与DWS兼容",
        "source_pattern": "WITH ... (col1, col2) AS (SELECT ... UNION ALL SELECT ... FROM cte WHERE ...)",
        "target_solution": "WITH RECURSIVE ... AS (SELECT ... UNION ALL SELECT ... FROM cte WHERE ...)",
        "compatible": True,
        "note": "DB2可省略RECURSIVE关键字，DWS需要RECURSIVE关键字，追加即可"
    },
    # ================================================================
    # 注释
    # ================================================================
    {
        "id": "DB2-DDL-019", "name": "COMMENT ON",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 COMMENT ON语法与DWS兼容",
        "source_pattern": "COMMENT ON TABLE t IS 'comment'",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
]
