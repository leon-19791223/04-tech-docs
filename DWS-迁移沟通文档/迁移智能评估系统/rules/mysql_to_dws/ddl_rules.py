"""MySQL -> DWS DDL兼容性规则"""

DDL_RULES = [
    # ================================================================
    # 表选项
    # ================================================================
    {
        "id": "MYSQL-DDL-001", "name": "ENGINE引擎指定",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL ENGINE=InnoDB/MyISAM在DWS中无对应概念，需移除",
        "source_pattern": "ENGINE=InnoDB / ENGINE=MyISAM",
        "target_solution": "直接移除该子句，DWS默认列存存储",
        "compatible": True, "note": "DWS无存储引擎概念，移除即可"
    },
    {
        "id": "MYSQL-DDL-002", "name": "AUTO_INCREMENT",
        "severity": "error", "score_deduction": 8,
        "description": "MySQL AUTO_INCREMENT在DWS中需改为SEQUENCE+nextval",
        "source_pattern": "id INT AUTO_INCREMENT PRIMARY KEY",
        "target_solution": "id INT DEFAULT nextval('seq_name') PRIMARY KEY -- 需手动创建SEQUENCE",
        "compatible": False, "note": "需为每个自增列创建SEQUENCE并设置DEFAULT nextval",
        "migration_difficulty": "中",
        "migration_suggestion": "通过脚本自动为每个AUTO_INCREMENT列生成SEQUENCE并改写DDL"
    },
    {
        "id": "MYSQL-DDL-003", "name": "AUTO_INCREMENT偏移量",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL AUTO_INCREMENT=n偏移量在DWS中由SEQUENCE的START WITH控制",
        "source_pattern": "AUTO_INCREMENT = 1000",
        "target_solution": "CREATE SEQUENCE seq_name START WITH 1000",
        "compatible": True, "note": "偏移量逻辑映射到SEQUENCE的起始值",
        "migration_difficulty": "低",
        "migration_suggestion": "提取AUTO_INCREMENT值注入到SEQUENCE的START WITH参数"
    },
    {
        "id": "MYSQL-DDL-004", "name": "字符集指定(CHARSET/CHARACTER SET)",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL CHARSET/CHARACTER SET在DWS中需移除",
        "source_pattern": "DEFAULT CHARSET=utf8mb4 / CHARACTER SET utf8",
        "target_solution": "移除该子句，DWS在数据库/集群级别设置字符集",
        "compatible": True, "note": "DWS统一字符集编码，无需在表级别指定"
    },
    {
        "id": "MYSQL-DDL-005", "name": "排序规则(COLLATE)",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL COLLATE在DWS中需移除",
        "source_pattern": "COLLATE=utf8mb4_general_ci / COLLATE utf8_bin",
        "target_solution": "移除该子句",
        "compatible": True, "note": "DWS排序规则由数据库/集群设置决定"
    },
    {
        "id": "MYSQL-DDL-006", "name": "ROW_FORMAT",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL ROW_FORMAT在DWS中不支持，需移除",
        "source_pattern": "ROW_FORMAT=DYNAMIC / ROW_FORMAT=COMPRESSED",
        "target_solution": "移除该子句，DWS列存默认压缩",
        "compatible": True, "note": "DWS列存表自动处理行格式和压缩"
    },
    # ================================================================
    # 分区表
    # ================================================================
    {
        "id": "MYSQL-DDL-007", "name": "RANGE COLUMNS分区",
        "severity": "warning", "score_deduction": 4,
        "description": "MySQL RANGE COLUMNS分区语法与DWS RANGE分区不同",
        "source_pattern": "PARTITION BY RANGE COLUMNS(col) (PARTITION p1 VALUES LESS THAN (10))",
        "target_solution": "PARTITION BY RANGE(col) (PARTITION p1 VALUES LESS THAN (10))",
        "compatible": True,
        "note": "移除COLUMNS关键字即可，功能对等",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 PARTITION BY RANGE COLUMNS -> PARTITION BY RANGE"
    },
    {
        "id": "MYSQL-DDL-008", "name": "LIST COLUMNS分区",
        "severity": "warning", "score_deduction": 4,
        "description": "MySQL LIST COLUMNS分区与DWS LIST分区语法不同",
        "source_pattern": "PARTITION BY LIST COLUMNS(col) (PARTITION p1 VALUES IN (1,2))",
        "target_solution": "PARTITION BY LIST(col) (PARTITION p1 VALUES (1,2))",
        "compatible": True,
        "note": "移除COLUMNS且VALUES IN改为VALUES",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换 LIST COLUMNS -> LIST, VALUES IN -> VALUES"
    },
    {
        "id": "MYSQL-DDL-009", "name": "KEY/HASH分区",
        "severity": "warning", "score_deduction": 4,
        "description": "MySQL KEY分区在DWS中不支持，HASH分区语法有差异",
        "source_pattern": "PARTITION BY KEY(col) / PARTITION BY HASH(col)",
        "target_solution": "PARTITION BY HASH(col) (PARTITION p1, PARTITION p2)",
        "compatible": True,
        "note": "KEY分区需改为HASH分区，HASH分区语法需调整",
        "migration_difficulty": "中",
        "migration_suggestion": "KEY分区改为HASH分区; HASH分区语法调整为DWS格式: PARTITION BY HASH(col) (PARTITION p1, PARTITION p2)"
    },
    {
        "id": "MYSQL-DDL-010", "name": "子分区(SUBPARTITION)",
        "severity": "error", "score_deduction": 8,
        "description": "MySQL子分区在DWS中不支持",
        "source_pattern": "SUBPARTITION BY HASH(col) SUBPARTITIONS 4",
        "target_solution": "拆分为单层分区表，或使用两张表+视图",
        "compatible": False,
        "note": "需要重新设计分区策略",
        "migration_difficulty": "高",
        "migration_suggestion": "评估子分区使用场景: 1) 仅查询 -> 创建视图; 2) 有DML -> 拆为多张表"
    },
    # ================================================================
    # 索引
    # ================================================================
    {
        "id": "MYSQL-DDL-011", "name": "FULLTEXT全文索引",
        "severity": "error", "score_deduction": 8,
        "description": "MySQL FULLTEXT全文索引在DWS中不支持",
        "source_pattern": "CREATE FULLTEXT INDEX idx_name ON table(col)",
        "target_solution": "DWS不支持全文索引，使用LIKE/ILIKE或集成Elasticsearch",
        "compatible": False, "note": "DWS无全文索引功能",
        "migration_difficulty": "高",
        "migration_suggestion": "简单搜索使用LIKE/ILIKE; 复杂全文搜索需集成Elasticsearch等搜索引擎"
    },
    {
        "id": "MYSQL-DDL-012", "name": "SPATIAL空间索引",
        "severity": "error", "score_deduction": 8,
        "description": "MySQL SPATIAL空间索引在DWS中不支持",
        "source_pattern": "CREATE SPATIAL INDEX idx_name ON table(col)",
        "target_solution": "DWS不支持空间索引",
        "compatible": False, "note": "DWS无空间索引功能",
        "migration_difficulty": "高",
        "migration_suggestion": "在应用层处理空间查询，或使用PostGIS扩展(GaussDB特有)"
    },
    {
        "id": "MYSQL-DDL-013", "name": "索引前缀(prefix)",
        "severity": "error", "score_deduction": 5,
        "description": "MySQL支持索引前缀(INDEX(col(10)))，DWS不支持",
        "source_pattern": "INDEX idx_name (col(10))",
        "target_solution": "移除前缀长度，改为全列索引",
        "compatible": False, "note": "DWS索引不支持前缀长度限定",
        "migration_difficulty": "低",
        "migration_suggestion": "索引前缀col(n)改为col，全列索引"
    },
    {
        "id": "MYSQL-DDL-014", "name": "USING BTREE/HASH",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL USING BTREE/HASH在DWS中忽略",
        "source_pattern": "USING BTREE / USING HASH",
        "target_solution": "移除该子句，DWS默认B-tree索引",
        "compatible": True, "note": "移除即可"
    },
    {
        "id": "MYSQL-DDL-015", "name": "VISIBLE/INVISIBLE索引",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL VISIBLE/INVISIBLE索引在DWS中不支持",
        "source_pattern": "ALTER INDEX idx_name VISIBLE / INVISIBLE",
        "target_solution": "移除该语法，DWS索引始终可见",
        "compatible": True, "note": "DWS不支持索引可见性控制"
    },
    # ================================================================
    # 约束
    # ================================================================
    {
        "id": "MYSQL-DDL-016", "name": "外键约束(FOREIGN KEY)",
        "severity": "warning", "score_deduction": 4,
        "description": "MySQL外键约束在DWS中语法兼容但建议移除(性能考虑)",
        "source_pattern": "FOREIGN KEY (col) REFERENCES other_table(id)",
        "target_solution": "DWS语法兼容，但MPP架构中外键影响导入性能，建议在应用层保证",
        "compatible": True,
        "note": "DWS支持外键但不强制检查，保留语法但实际由应用层保证一致性",
        "migration_difficulty": "低",
        "migration_suggestion": "保留外键DDL供文档参考，实际数据一致性由ETL/应用层保证"
    },
    {
        "id": "MYSQL-DDL-017", "name": "ON UPDATE CURRENT_TIMESTAMP",
        "severity": "error", "score_deduction": 5,
        "description": "MySQL ON UPDATE CURRENT_TIMESTAMP在DWS中不支持",
        "source_pattern": "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP",
        "target_solution": "使用触发器实现: CREATE TRIGGER ... BEFORE UPDATE ... SET NEW.updated_at = now()",
        "compatible": False, "note": "DWS不支持列级别的ON UPDATE自动刷新",
        "migration_difficulty": "低",
        "migration_suggestion": "创建BEFORE UPDATE触发器实现自动更新时间戳"
    },
    {
        "id": "MYSQL-DDL-018", "name": "PRIMARY KEY",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL主键语法在DWS中兼容",
        "source_pattern": "PRIMARY KEY (col)",
        "target_solution": "PRIMARY KEY (col) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-DDL-019", "name": "UNIQUE约束",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL UNIQUE约束在DWS中兼容",
        "source_pattern": "UNIQUE KEY (col) / UNIQUE INDEX (col)",
        "target_solution": "UNIQUE (col) -- 兼容",
        "compatible": True, "note": "完全兼容"
    },
    # ================================================================
    # DML差异
    # ================================================================
    {
        "id": "MYSQL-DDL-020", "name": "INSERT ... ON DUPLICATE KEY UPDATE",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL INSERT ... ON DUPLICATE KEY在DWS中不支持",
        "source_pattern": "INSERT INTO t VALUES (...) ON DUPLICATE KEY UPDATE col=val",
        "target_solution": "使用MERGE INTO: MERGE INTO t USING ... ON ... WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT",
        "compatible": False, "note": "需改写为MERGE INTO语法",
        "migration_difficulty": "中",
        "migration_suggestion": "将INSERT ... ON DUPLICATE KEY UPDATE改写为MERGE INTO"
    },
    {
        "id": "MYSQL-DDL-021", "name": "INSERT IGNORE",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL INSERT IGNORE在DWS中不支持",
        "source_pattern": "INSERT IGNORE INTO t VALUES (...)",
        "target_solution": "使用MERGE INTO WHEN NOT MATCHED THEN INSERT，或先检查再插入",
        "compatible": False, "note": "需改写",
        "migration_difficulty": "低",
        "migration_suggestion": "改为MERGE INTO或添加WHERE NOT EXISTS条件"
    },
    {
        "id": "MYSQL-DDL-022", "name": "REPLACE INTO",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL REPLACE INTO在DWS中不支持",
        "source_pattern": "REPLACE INTO t VALUES (...) -- 先删后插",
        "target_solution": "使用MERGE INTO: MERGE INTO t USING ... ON ... WHEN MATCHED THEN UPDATE WHEN NOT MATCHED THEN INSERT",
        "compatible": False, "note": "需改写为MERGE INTO",
        "migration_difficulty": "中",
        "migration_suggestion": "REPLACE INTO改写为MERGE INTO，注意DELETE+INSERT vs UPDATE语义差异"
    },
    # ================================================================
    # 其他
    # ================================================================
    {
        "id": "MYSQL-DDL-023", "name": "临时表语法差异",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL CREATE TEMPORARY TABLE与DWS语法有差异",
        "source_pattern": "CREATE TEMPORARY TABLE ... ENGINE=Memory",
        "target_solution": "CREATE TEMPORARY TABLE ... (无ENGINE子句)",
        "compatible": True,
        "note": "移除ENGINE子句即可，DWS临时表存储在内存+磁盘",
        "migration_difficulty": "低",
        "migration_suggestion": "移除ENGINE=Memory/MyISAM等子句"
    },
    {
        "id": "MYSQL-DDL-024", "name": "CREATE TABLE ... SELECT",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL CREATE TABLE ... SELECT在DWS中支持但约束会丢失",
        "source_pattern": "CREATE TABLE t AS SELECT * FROM source",
        "target_solution": "CREATE TABLE t (LIKE source INCLUDING ALL) + INSERT INTO t SELECT * FROM source",
        "compatible": True,
        "note": "DWS的CREATE TABLE AS不会复制约束和默认值，建议分两步",
        "migration_difficulty": "低",
        "migration_suggestion": "先CREATE TABLE再INSERT INTO SELECT，确保约束完整"
    },
    {
        "id": "MYSQL-DDL-025", "name": "SHOW CREATE TABLE",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL SHOW CREATE TABLE在DWS中对应\\\\d+ tablename",
        "source_pattern": "SHOW CREATE TABLE t",
        "target_solution": "\\d+ t (gsql) 或 INFORMATION_SCHEMA查询",
        "compatible": True, "note": "功能对等，命令不同"
    },
]
