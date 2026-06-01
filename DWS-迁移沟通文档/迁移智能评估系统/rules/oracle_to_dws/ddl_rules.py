"""Oracle -> DWS DDL兼容性规则
涵盖: 表空间、分区表、索引、物化视图、同义词、簇表等
"""

DDL_RULES = [
    # ================================================================
    # 表空间
    # ================================================================
    {
        "id": "ORA-DDL-001",
        "name": "表空间语法",
        "severity": "info",
        "score_deduction": 0,
        "description": "Oracle表空间(TABLESPACE)概念在DWS中转化为Schema或直接省略",
        "source_pattern": "CREATE TABLE ... TABLESPACE ts_name",
        "target_solution": "DWS中移除TABLESPACE子句，使用默认表空间",
        "compatible": True,
        "note": "DWS有表空间概念但使用方式不同，Oracle表空间可映射为Schema"
    },
    {
        "id": "ORA-DDL-002",
        "name": "临时表语法",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Oracle全局临时表(GTT)与DWS临时表语法不同",
        "source_pattern": "CREATE GLOBAL TEMPORARY TABLE ... ON COMMIT {DELETE|PRESERVE} ROWS",
        "target_solution": "CREATE TEMPORARY TABLE ... ON COMMIT {DELETE ROWS|PRESERVE ROWS}",
        "compatible": True,
        "note": "DWS支持临时表，但语法略有不同，全局行为有差异",
        "migration_difficulty": "低",
        "migration_suggestion": "批量替换DDL语法即可"
    },

    # ================================================================
    # 分区表
    # ================================================================
    {
        "id": "ORA-DDL-003",
        "name": "范围分区语法差异",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Oracle范围分区(PARTITION BY RANGE)语法与DWS不同",
        "source_pattern": "PARTITION BY RANGE (col) (PARTITION p1 VALUES LESS THAN (maxval))",
        "target_solution": "DWS分区语法: PARTITION BY RANGE(col) (PARTITION p1 VALUES LESS THAN (maxval))",
        "compatible": True,
        "note": "基本语法相似，但DWS分区键类型限制更多(不支持boolean/blob等)",
        "migration_difficulty": "低",
        "migration_suggestion": "主要检查分区键类型是否兼容"
    },
    {
        "id": "ORA-DDL-004",
        "name": "列表分区",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Oracle LIST分区语法与DWS不同",
        "source_pattern": "PARTITION BY LIST (col) (PARTITION p1 VALUES ('val1','val2'))",
        "target_solution": "DWS支持LIST分区但语法有差异: PARTITION p1 VALUES ('val1','val2')",
        "compatible": True,
        "note": "DWS 8.2.1+支持LIST分区，旧版本需改为RANGE分区+CASE WHEN",
        "migration_difficulty": "中",
        "migration_suggestion": "检查DWS版本是否支持LIST分区，否则改为RANGE分区"
    },
    {
        "id": "ORA-DDL-005",
        "name": "哈希分区",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Oracle HASH分区语法在DWS中不完全兼容",
        "source_pattern": "PARTITION BY HASH (col) (PARTITION p1, PARTITION p2)",
        "target_solution": "DWS支持HASH分区但需要指定分区数: PARTITION BY HASH(col) (PARTITION p1, PARTITION p2)",
        "compatible": True,
        "note": "DWS分区语法接近，但分区数需显式指定",
        "migration_difficulty": "低",
        "migration_suggestion": "脚本批量转换分区语法"
    },
    {
        "id": "ORA-DDL-006",
        "name": "子分区(复合分区)",
        "severity": "error",
        "score_deduction": 8,
        "description": "Oracle支持子分区(SUBPARTITION)，DWS不支持",
        "source_pattern": "PARTITION BY RANGE(col) SUBPARTITION BY HASH(col2)",
        "target_solution": "拆分为两张表或使用视图关联，DWS不支持复合分区",
        "compatible": False,
        "note": "需要重新设计分区策略，将子分区表拆分为单层分区",
        "migration_difficulty": "高",
        "migration_suggestion": "评估子分区使用场景: 1) 仅查询: 创建视图; 2) 有DML: 拆为多张表并用视图联合"
    },
    {
        "id": "ORA-DDL-007",
        "name": "分区维护操作差异",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Oracle分区维护(ADD/DROP/MERGE/SPLIT/TRUNCATE)语法差异",
        "source_pattern": "ALTER TABLE t ADD PARTITION ... / DROP PARTITION / MERGE PARTITIONS",
        "target_solution": "DWS支持ADD/DROP/TRUNCATE/EXCHANGE分区，MERGE和SPLIT语法不同",
        "compatible": True,
        "note": "大部分操作DWS支持，但MOVE/SPLIT语法有差异，建议统一通过ETL调度维护",
        "migration_difficulty": "中",
        "migration_suggestion": "检查ETL和调度脚本中的分区维护DDL，替换为DWS语法"
    },

    # ================================================================
    # 索引
    # ================================================================
    {
        "id": "ORA-DDL-008",
        "name": "BITMAP位图索引",
        "severity": "error",
        "score_deduction": 8,
        "description": "Oracle BITMAP索引在DWS中不支持",
        "source_pattern": "CREATE BITMAP INDEX idx_name ON table(col)",
        "target_solution": "DWS使用列存+分区替代：建表时WITH (ORIENTATION=COLUMN)，低基数列会自动优化",
        "compatible": False,
        "note": "DWS列存表本身具有类似位图索引的压缩和过滤能力，无需显式创建BITMAP索引",
        "migration_difficulty": "低",
        "migration_suggestion": "评估BITMAP索引列: 若表已改为列存，直接删除BITMAP索引DDL"
    },
    {
        "id": "ORA-DDL-009",
        "name": "函数索引(Function-Based Index)",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Oracle函数索引在DWS中支持有限",
        "source_pattern": "CREATE INDEX idx_name ON table(UPPER(col))",
        "target_solution": "DWS支持表达式索引: CREATE INDEX idx_name ON table(UPPER(col))",
        "compatible": True,
        "note": "DWS支持表达式索引但函数支持范围比Oracle窄，需逐一验证",
        "migration_difficulty": "中",
        "migration_suggestion": "检查函数索引中使用的函数，确保DWS支持; 否则通过冗余列+普通索引替代"
    },
    {
        "id": "ORA-DDL-010",
        "name": "反向键索引(Reverse Index)",
        "severity": "error",
        "score_deduction": 6,
        "description": "Oracle REVERSE索引在DWS中不支持",
        "source_pattern": "CREATE INDEX idx_name ON table(col) REVERSE",
        "target_solution": "DWS不支持REVERSE索引，改用普通索引或调整分布键",
        "compatible": False,
        "note": "REVERSE索引主要用于RAC环境避免热块冲突，DWS共享存储架构无需此功能",
        "migration_difficulty": "低",
        "migration_suggestion": "直接删除REVERSE关键字，改为普通B-tree索引"
    },
    {
        "id": "ORA-DDL-011",
        "name": "索引组织表(IOT)",
        "severity": "error",
        "score_deduction": 8,
        "description": "Oracle索引组织表在DWS中不支持",
        "source_pattern": "CREATE TABLE t (col1 INT PRIMARY KEY, col2 TEXT) ORGANIZATION INDEX",
        "target_solution": "改为普通堆表+主键索引; 或列存表",
        "compatible": False,
        "note": "IOT在Oracle中用于减少存储空间和快速主键访问，DWS中使用列存+分区替代",
        "migration_difficulty": "中",
        "migration_suggestion": "评估IOT使用场景: 主键访问频繁->改为普通表+主键索引; 批量分析->列存表"
    },
    {
        "id": "ORA-DDL-012",
        "name": "聚簇表(Cluster)",
        "severity": "error",
        "score_deduction": 8,
        "description": "Oracle聚簇表在DWS中不支持",
        "source_pattern": "CREATE CLUSTER cluster_name ... CREATE TABLE t CLUSTER cluster_name",
        "target_solution": "将聚簇表中的多张表分别创建为独立表，基于分布键关联",
        "compatible": False,
        "note": "Oracle聚簇表用于降低多表关联的I/O，DWS中可改为Hash分布+合理分区",
        "migration_difficulty": "高",
        "migration_suggestion": "将聚簇表拆分为独立表，通过分布键设计保证关联性能"
    },

    # ================================================================
    # 物化视图
    # ================================================================
    {
        "id": "ORA-DDL-013",
        "name": "物化视图语法差异",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Oracle物化视图(MATERIALIZED VIEW)与DWS语法有差异",
        "source_pattern": "CREATE MATERIALIZED VIEW mv_name REFRESH {FAST|COMPLETE} ON DEMAND AS ...",
        "target_solution": "CREATE MATERIALIZED VIEW mv_name AS ... (DWS不支持自动刷新)",
        "compatible": True,
        "note": "DWS支持物化视图但语法不同，且仅支持手动刷新(REFRESH MATERIALIZED VIEW)",
        "migration_difficulty": "中",
        "migration_suggestion": "改为DWS语法创建MV，将刷新任务集成到调度系统中"
    },
    {
        "id": "ORA-DDL-014",
        "name": "物化视图日志(MV Log)",
        "severity": "error",
        "score_deduction": 6,
        "description": "Oracle物化视图日志在DWS中不支持",
        "source_pattern": "CREATE MATERIALIZED VIEW LOG ON table",
        "target_solution": "废弃MV Log，改为全量刷新或通过ETL增量更新",
        "compatible": False,
        "note": "Oracle的FAST REFRESH依赖MV Log，DWS仅支持COMPLETE REFRESH",
        "migration_difficulty": "低",
        "migration_suggestion": "MV Log语法直接删除，MV全量定期刷新; 如需增量，通过ETL实现"
    },
    {
        "id": "ORA-DDL-015",
        "name": "物化视图刷新方式",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Oracle支持多种刷新方式(FAST/COMPLETE/FORCE)，DWS仅COMPLETE",
        "source_pattern": "REFRESH FAST ON DEMAND / REFRESH FORCE / START WITH ... NEXT ...",
        "target_solution": "改为调度系统定期执行: REFRESH MATERIALIZED VIEW mv_name",
        "compatible": True,
        "note": "DWS仅支持手动全量刷新，刷新频率和时机由外部调度控制",
        "migration_difficulty": "低",
        "migration_suggestion": "在DolphinScheduler/TaskCTL中创建定期刷新任务"
    },

    # ================================================================
    # 同义词与DBLINK
    # ================================================================
    {
        "id": "ORA-DDL-016",
        "name": "同义词(Synonym)",
        "severity": "error",
        "score_deduction": 6,
        "description": "Oracle同义词(SYNONYM)在DWS中不支持",
        "source_pattern": "CREATE {PUBLIC} SYNONYM syn_name FOR schema.table",
        "target_solution": "使用视图(view)或搜索路径(search_path)替代",
        "compatible": False,
        "note": "Oracle同义词用于跨Schema/DB透明访问，DWS通过Schema权限+视图实现",
        "migration_difficulty": "低",
        "migration_suggestion": "1) 跨Schema: 使用schema.table方式访问; 2) 大量使用: 创建同名视图"
    },
    {
        "id": "ORA-DDL-017",
        "name": "数据库链接(DBLINK)",
        "severity": "warning",
        "score_deduction": 4,
        "description": "Oracle DBLINK在DWS中支持但语法和功能有差异",
        "source_pattern": "CREATE DATABASE LINK link_name CONNECT TO ...",
        "target_solution": "CREATE FOREIGN TABLE ... SERVER ... (使用DWS的Foreign Data Wrapper)",
        "compatible": True,
        "note": "DWS通过FDW实现跨库访问，语法完全不同，但功能对等",
        "migration_difficulty": "中",
        "migration_suggestion": "将DBLINK查询改写为FDW方式，或通过ETL工具同步数据"
    },

    # ================================================================
    # 序列
    # ================================================================
    {
        "id": "ORA-DDL-018",
        "name": "序列语法差异",
        "severity": "warning",
        "score_deduction": 2,
        "description": "Oracle序列(CREATE SEQUENCE)与DWS语法有差异",
        "source_pattern": "CREATE SEQUENCE seq_name START WITH 1 INCREMENT BY 1 CACHE 20",
        "target_solution": "CREATE SEQUENCE seq_name START 1 INCREMENT BY 1 CACHE 20",
        "compatible": True,
        "note": "基本功能一致，DWS不支持ORDER/NOCYCLE/MAXVALUE等Oracle特有参数",
        "migration_difficulty": "低",
        "migration_suggestion": "脚本替换语法，移除Oracle特有参数"
    },
    {
        "id": "ORA-DDL-019",
        "name": "序列伪列语法",
        "severity": "warning",
        "score_deduction": 2,
        "description": "Oracle序列调用 seq_name.NEXTVAL/CURRVAL 与DWS不同",
        "source_pattern": "seq_name.NEXTVAL, seq_name.CURRVAL",
        "target_solution": "nextval('seq_name'), currval('seq_name') (函数形式)",
        "compatible": True,
        "note": "DWS使用函数形式调用序列，需要全局替换SQL",
        "migration_difficulty": "低",
        "migration_suggestion": "批量正则替换: xxx.NEXTVAL -> nextval('xxx')"
    },
    {
        "id": "ORA-DDL-020",
        "name": "标识列(Identity Column)",
        "severity": "warning",
        "score_deduction": 3,
        "description": "Oracle 12c+标识列(GENERATED AS IDENTITY)与DWS语法不同",
        "source_pattern": "col INT GENERATED {ALWAYS|BY DEFAULT} AS IDENTITY",
        "target_solution": "col INT DEFAULT nextval('seq_name') -- 需手动创建序列",
        "compatible": True,
        "note": "DWS不支持IDENTITY语法，需转换为SEQUENCE+DEFAULT方式",
        "migration_difficulty": "低",
        "migration_suggestion": "为每个IDENTITY列自动创建序列，改DEFAULT为nextval方式"
    },
]
