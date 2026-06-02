"""SQL Server -> DWS DDL兼容性规则"""

DDL_RULES = [
    # ================================================================
    # 表选项
    # ================================================================
    {
        "id": "MSSQL-DDL-001", "name": "IDENTITY属性",
        "severity": "error", "score_deduction": 8,
        "description": "SQL Server IDENTITY(seed, increment)在DWS中需改为SEQUENCE+nextval",
        "source_pattern": "id INT IDENTITY(1,1) PRIMARY KEY",
        "target_solution": "id INT DEFAULT nextval('seq_name') PRIMARY KEY -- 需手动创建SEQUENCE",
        "compatible": False, "note": "需为每个IDENTITY列创建SEQUENCE",
        "migration_difficulty": "中",
        "migration_suggestion": "通过脚本为每个IDENTITY列生成SEQUENCE(含seed, increment映射到START WITH, INCREMENT BY)"
    },
    {
        "id": "MSSQL-DDL-002", "name": "IDENTITY_INSERT",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server SET IDENTITY_INSERT ON/OFF在DWS中无对应",
        "source_pattern": "SET IDENTITY_INSERT table ON",
        "target_solution": "DWS中使用OVERRIDING SYSTEM VALUE或直接指定序列值",
        "compatible": False, "note": "DWS使用SEQUENCE方式，直接指定值即可",
        "migration_difficulty": "低",
        "migration_suggestion": "移除 SET IDENTITY_INSERT，DWS序列值可通过OVERRIDING SYSTEM VALUE覆盖"
    },
    {
        "id": "MSSQL-DDL-003", "name": "CLUSTERED/NONCLUSTERED",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server CLUSTERED/NONCLUSTERED在DWS中需移除关键字",
        "source_pattern": "PRIMARY KEY CLUSTERED (col) / CREATE NONCLUSTERED INDEX",
        "target_solution": "移除CLUSTERED/NONCLUSTERED关键字，DWS无此概念",
        "compatible": True,
        "note": "DWS索引默认为非聚集，移除关键字即可",
        "migration_difficulty": "低",
        "migration_suggestion": "全局正则替换 CLUSTERED 和 NONCLUSTERED"
    },
    {
        "id": "MSSQL-DDL-004", "name": "ON [PRIMARY] / ON filegroup",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server ON PRIMARY和ON文件组在DWS中需移除",
        "source_pattern": "CREATE TABLE t (col INT) ON [PRIMARY]",
        "target_solution": "移除ON [PRIMARY]子句",
        "compatible": True, "note": "DWS无文件组概念"
    },
    {
        "id": "MSSQL-DDL-005", "name": "TEXTIMAGE_ON",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server TEXTIMAGE_ON在DWS中需移除",
        "source_pattern": "CREATE TABLE t (...) TEXTIMAGE_ON [PRIMARY]",
        "target_solution": "移除TEXTIMAGE_ON子句",
        "compatible": True, "note": "DWS无对应概念"
    },
    {
        "id": "MSSQL-DDL-006", "name": "WITH (FILLFACTOR/PAD_INDEX等)",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server索引选项FILLFACTOR/PAD_INDEX/IGNORE_DUP_KEY等需移除",
        "source_pattern": "CREATE INDEX idx ON t(col) WITH (FILLFACTOR=80, PAD_INDEX=ON)",
        "target_solution": "移除WITH子句，保留CREATE INDEX ... ON t(col)",
        "compatible": True,
        "note": "DWS索引选项与SQL Server不同，使用DWS原生索引选项"
    },
    {
        "id": "MSSQL-DDL-007", "name": "SPARSE COLUMN",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server SPARSE列在DWS中不支持",
        "source_pattern": "col VARCHAR(100) SPARSE",
        "target_solution": "移除SPARSE关键字，DWS列存表本身就压缩NULL值",
        "compatible": False,
        "note": "DWS列存表默认对NULL值进行压缩，无需SPARSE",
        "migration_difficulty": "低",
        "migration_suggestion": "移除SPARSE关键字"
    },
    {
        "id": "MSSQL-DDL-008", "name": "COLUMN_SET",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server COLUMN_SET在DWS中不支持",
        "source_pattern": "CREATE TABLE t (...) col_set XML COLUMN_SET FOR ALL_SPARSE_COLUMNS",
        "target_solution": "DWS不支持COLUMN_SET功能",
        "compatible": False, "note": "需重新设计表结构",
        "migration_difficulty": "高",
        "migration_suggestion": "使用JSON/JSONB聚合所有稀疏列"
    },
    {
        "id": "MSSQL-DDL-009", "name": "FILESTREAM / FILETABLE",
        "severity": "error", "score_deduction": 10,
        "description": "SQL Server FILESTREAM/FILETABLE在DWS中不支持",
        "source_pattern": "CREATE TABLE t (doc VARBINARY(MAX)) FILESTREAM_ON fs",
        "target_solution": "文件数据存储在对象存储或文件系统中，DWS存储路径引用",
        "compatible": False, "note": "需重构文件存储架构",
        "migration_difficulty": "高",
        "migration_suggestion": "文件迁移到OBS/HDFS，数据库仅存储文件路径或FileID"
    },
    {
        "id": "MSSQL-DDL-010", "name": "COMPRESSION (ROW/PAGE)",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server ROW/PAGE压缩在DWS中由列存压缩自动实现",
        "source_pattern": "CREATE TABLE t (...) WITH (DATA_COMPRESSION = PAGE)",
        "target_solution": "DWS使用列存ORIENTATION=COLUMN + COMPRESSION=HIGH替代",
        "compatible": True, "note": "DWS列存自动压缩效果更好",
        "migration_difficulty": "低",
        "migration_suggestion": "移除DATA_COMPRESSION选项，设置ORIENTATION=COLUMN"
    },
    # ================================================================
    # 分区表
    # ================================================================
    {
        "id": "MSSQL-DDL-011", "name": "分区函数+分区方案",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server分区函数(PARTITION FUNCTION)+分区方案(PARTITION SCHEME)与DWS完全不同",
        "source_pattern": "CREATE PARTITION FUNCTION pf (int) AS RANGE LEFT FOR VALUES (1,100,1000)",
        "target_solution": "在CREATE TABLE时直接指定分区: PARTITION BY RANGE(col) (PARTITION p1 VALUES LESS THAN(1))",
        "compatible": False, "note": "SQL Server的分区体系复杂，DWS直接在表上定义分区",
        "migration_difficulty": "中",
        "migration_suggestion": "将PARTITION FUNCTION + SCHEME合并为DWS表级分区DDL"
    },
    {
        "id": "MSSQL-DDL-012", "name": "RANGE LEFT/RANGE RIGHT",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server RANGE LEFT/RIGHT与DWS VALUES LESS THAN语义对应",
        "source_pattern": "RANGE LEFT FOR VALUES (100) -- 包含100",
        "target_solution": "RANGE LEFT -> VALUES LESS THAN (101); RANGE RIGHT -> VALUES LESS THAN (100)",
        "compatible": True,
        "note": "需理解边界语义进行转换: LEFT包含边界值，RIGHT不包含",
        "migration_difficulty": "中",
        "migration_suggestion": "RANGE LEFT (n) -> VALUES LESS THAN (n+1); RANGE RIGHT (n) -> VALUES LESS THAN (n)"
    },
    # ================================================================
    # 索引
    # ================================================================
    {
        "id": "MSSQL-DDL-013", "name": "FILTERED索引",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server FILTERED索引(WHERE条件)在DWS中不支持",
        "source_pattern": "CREATE INDEX idx ON t(col) WHERE col IS NOT NULL",
        "target_solution": "DWS不支持条件索引，可考虑分区表替代",
        "compatible": False, "note": "DWS索引不支持WHERE过滤条件",
        "migration_difficulty": "中",
        "migration_suggestion": "移除条件过滤，改为全量索引; 或通过分区表实现类似效果"
    },
    {
        "id": "MSSQL-DDL-014", "name": "INCLUDE索引",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server INCLUDE列索引在DWS中不支持",
        "source_pattern": "CREATE INDEX idx ON t(key_col) INCLUDE (col1, col2)",
        "target_solution": "改为复合索引: CREATE INDEX idx ON t(key_col, col1, col2)",
        "compatible": False,
        "note": "MPP架构下复合索引和INCLUDE效果不同，需评估",
        "migration_difficulty": "中",
        "migration_suggestion": "将INCLUDE列合并到索引定义中成为复合索引"
    },
    {
        "id": "MSSQL-DDL-015", "name": "COLUMNSTORE索引",
        "severity": "warning", "score_depuction": 3,
        "description": "SQL Server COLUMNSTORE索引在DWS中通过列存表实现",
        "source_pattern": "CREATE CLUSTERED COLUMNSTORE INDEX idx ON t",
        "target_solution": "建表时指定ORIENTATION=COLUMN，行存改为列存",
        "compatible": True, "note": "概念对等: DWS列存表等效于SQL Server的CCI",
        "migration_difficulty": "低",
        "migration_suggestion": "将COLUMNSTORE索引方案改为DWS列存表"
    },
    {
        "id": "MSSQL-DDL-016", "name": "PRIMARY XML索引",
        "severity": "error", "score_deduction": 8,
        "description": "SQL Server XML索引在DWS中不支持",
        "source_pattern": "CREATE PRIMARY XML INDEX xml_idx ON t(xml_col)",
        "target_solution": "DWS不支持XML索引，XML改为JSON或TEXT",
        "compatible": False, "note": "XML索引为SQL Server特有",
        "migration_difficulty": "高",
        "migration_suggestion": "XML字段迁移到JSON，使用JSON操作符查询"
    },
    {
        "id": "MSSQL-DDL-017", "name": "PRIMARY KEY / UNIQUE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server PRIMARY KEY和UNIQUE在DWS中兼容",
        "source_pattern": "ALTER TABLE t ADD CONSTRAINT pk PRIMARY KEY (col)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DDL-018", "name": "FOREIGN KEY外键",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server外键在DWS中语法兼容但建议在应用层保证",
        "source_pattern": "ALTER TABLE t ADD CONSTRAINT fk FOREIGN KEY (col) REFERENCES t2(id)",
        "target_solution": "DWS语法兼容，但MPP架构中外键约束影响性能",
        "compatible": True,
        "note": "语法兼容但建议在ETL/应用层控制数据一致性，DDL保留做文档参考",
        "migration_difficulty": "低",
        "migration_suggestion": "DDL脚本可保留外键定义; 实际数据一致性由ETL/应用层保证"
    },
    {
        "id": "MSSQL-DDL-019", "name": "DEFAULT约束",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server DEFAULT约束在DWS中兼容",
        "source_pattern": "col INT DEFAULT 0",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DDL-020", "name": "CHECK约束",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server CHECK约束在DWS中兼容",
        "source_pattern": "col INT CHECK (col > 0)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # 视图与同义词
    # ================================================================
    {
        "id": "MSSQL-DDL-021", "name": "CREATE VIEW语法",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server CREATE VIEW在DWS中兼容",
        "source_pattern": "CREATE VIEW v AS SELECT ...",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DDL-022", "name": "SCHEMABINDING视图",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server WITH SCHEMABINDING视图在DWS中不支持",
        "source_pattern": "CREATE VIEW v WITH SCHEMABINDING AS SELECT ...",
        "target_solution": "移除WITH SCHEMABINDING，DWS无此功能",
        "compatible": False, "note": "DWS不支持SCHEMABINDING",
        "migration_difficulty": "低",
        "migration_suggestion": "移除SCHEMABINDING选项"
    },
    {
        "id": "MSSQL-DDL-023", "name": "CREATE SYNONYM同义词",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server同义词在DWS中不支持",
        "source_pattern": "CREATE SYNONYM syn FOR schema.table",
        "target_solution": "使用VARCHAR或search_path替代",
        "compatible": False, "note": "DWS无同义词功能",
        "migration_difficulty": "低",
        "migration_suggestion": "1) 跨Schema: 使用schema.table; 2) 大量访问: 创建同名VIEW"
    },
    {
        "id": "MSSQL-DDL-024", "name": "SEQUENCE语法差异",
        "severity": "warning", "score_deduction": 2,
        "description": "SQL Server CREATE SEQUENCE与DWS语法差异",
        "source_pattern": "CREATE SEQUENCE seq START WITH 1 INCREMENT BY 1 CACHE 10 NO CYCLE",
        "target_solution": "CREATE SEQUENCE seq START 1 INCREMENT BY 1 CACHE 10",
        "compatible": True,
        "note": "移除NO CYCLE/NO CACHE等DWS不支持的关键字",
        "migration_difficulty": "低",
        "migration_suggestion": "批量转换SEQUENCE DDL，移除SQL Server特有选项"
    },
    {
        "id": "MSSQL-DDL-025", "name": "SEQUENCE NEXT VALUE FOR",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server NEXT VALUE FOR在DWS中使用nextval函数",
        "source_pattern": "NEXT VALUE FOR seq_name / seq_name.NEXTVAL",
        "target_solution": "nextval('seq_name')",
        "compatible": False, "note": "语法完全不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 NEXT VALUE FOR seq -> nextval('seq')"
    },
    # ================================================================
    # DML差异
    # ================================================================
    {
        "id": "MSSQL-DDL-026", "name": "OUTPUT子句",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server INSERT/DELETE/UPDATE OUTPUT在DWS中使用RETURNING",
        "source_pattern": "DELETE FROM t OUTPUT DELETED.* WHERE ...",
        "target_solution": "DELETE FROM t WHERE ... RETURNING *",
        "compatible": False,
        "note": "功能对等，语法不同: OUTPUT -> RETURNING",
        "migration_difficulty": "低",
        "migration_suggestion": "OUTPUT DELETED.* -> RETURNING *; OUTPUT INSERTED.* -> RETURNING *"
    },
    {
        "id": "MSSQL-DDL-027", "name": "MERGE语法差异",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server MERGE与DWS语法略有差异",
        "source_pattern": "MERGE target USING source ON cond WHEN MATCHED THEN UPDATE ...",
        "target_solution": "DWS支持MERGE但WHEN NOT MATCHED BY SOURCE等扩展不支持",
        "compatible": True,
        "note": "基础MERGE语法兼容，SQL Server扩展子句需移除",
        "migration_difficulty": "低",
        "migration_suggestion": "移除SQL Server特有的WHEN MATCHED AND条件、WHEN NOT MATCHED BY SOURCE等"
    },
    {
        "id": "MSSQL-DDL-028", "name": "TRUNCATE TABLE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server TRUNCATE在DWS中兼容",
        "source_pattern": "TRUNCATE TABLE t",
        "target_solution": "TRUNCATE TABLE t -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DDL-029", "name": "临时表 #temp / ##temp",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server本地/全局临时表在DWS中使用CREATE TEMPORARY TABLE",
        "source_pattern": "CREATE TABLE #temp (col INT) / CREATE TABLE ##temp (col INT)",
        "target_solution": "CREATE TEMPORARY TABLE temp (col INT)",
        "compatible": True,
        "note": "功能对等，语法不同。全局临时表(##temp)需改为普通表",
        "migration_difficulty": "低",
        "migration_suggestion": "将#temp和##temp改为DWS临时表，注意会话级临时表的生命周期差异"
    },
    {
        "id": "MSSQL-DDL-030", "name": "表变量 @table",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server表变量在DWS中不支持",
        "source_pattern": "DECLARE @t TABLE (col INT); INSERT INTO @t VALUES (1)",
        "target_solution": "使用临时表或数组替代",
        "compatible": False,
        "note": "DWS T-SQL兼容性中不支持表变量",
        "migration_difficulty": "中",
        "migration_suggestion": "表变量替换为临时表: DECLARE @t TABLE ... -> CREATE TEMPORARY TABLE t (...)"
    },
    {
        "id": "MSSQL-DDL-031", "name": "CTE (公用表表达式)",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server WITH CTE在DWS中兼容",
        "source_pattern": "WITH cte AS (SELECT ...) SELECT * FROM cte",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MSSQL-DDL-032", "name": "递归CTE",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server递归CTE在DWS中兼容",
        "source_pattern": "WITH cte AS (SELECT ... UNION ALL SELECT ... FROM cte WHERE ...)",
        "target_solution": "语法兼容",
        "compatible": True, "note": "完全兼容"
    },
]
