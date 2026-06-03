"""MySQL -> DWS 补充评估规则

补充: 安全/字符集/应用层/事务/CDC同步/性能
"""

SECURITY_RULES = [
    {
        "id": "MYSQL-SEC-001", "name": "MySQL权限模型差异",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL权限模型(用户@主机+全局/库级/表级权限)与DWS(RBAC角色)不同",
        "source_pattern": "GRANT SELECT, INSERT ON db.* TO 'user'@'%' IDENTIFIED BY 'pwd'",
        "target_solution": "DWS使用角色+权限: CREATE USER user WITH PASSWORD 'pwd'; GRANT SELECT, INSERT ON ALL TABLES IN SCHEMA schema TO user",
        "compatible": True,
        "note": "MySQL的GRANT+IDENTIFIED组合语法不再支持; 需分步创建用户+授权",
        "migration_difficulty": "中",
        "migration_suggestion": "将MySQL授权语句转换为DWS的分步授权: CREATE USER → GRANT … ON SCHEMA … TO user"
    },
    {
        "id": "MYSQL-SEC-002", "name": "MySQL加密和SSL连接",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL SSL/TLS配置需在DWS端重新配置",
        "compatible": True, "note": "DWS支持TLS 1.2+加密连接，需重新配置证书"
    },
    {
        "id": "MYSQL-SEC-003", "name": "MySQL AES_ENCRYPT/DES_DECRYPT加密",
        "severity": "error", "score_deduction": 5,
        "description": "MySQL AES_ENCRYPT/AES_DECRYPT等内置加密函数在DWS中不支持",
        "source_pattern": "AES_ENCRYPT(str, key_str) / AES_DECRYPT(cipher, key) / OLD_PASSWORD",
        "target_solution": "使用DWS pgcrypto扩展: encrypt(data, key, 'aes') / decrypt(data, key, 'aes')",
        "compatible": False,
        "note": "MySQL内置加密函数与DWS pgcrypto扩展的函数名和参数不同",
        "migration_difficulty": "中",
        "migration_suggestion": "AES_ENCRYPT(str,key) -> encrypt(str::bytea, key, 'aes'); AES_DECRYPT(cipher, key) -> decrypt(cipher, key, 'aes')"
    },
]

CHARSET_RULES = [
    {
        "id": "MYSQL-CSET-001", "name": "MySQL utf8mb4字符集",
        "severity": "info", "score_deduction": 0,
        "description": "MySQL utf8mb4(4字节UTF-8)到DWS UTF-8(最大4字节)完全兼容",
        "compatible": True, "note": "完全兼容"
    },
    {
        "id": "MYSQL-CSET-002", "name": "MySQL VARCHAR长度语义差异",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL VARCHAR(n)的n是字符数，DWS的n是字节数",
        "source_pattern": "VARCHAR(100) 含中文→实际可存100个中文字符(MySQL)",
        "target_solution": "VARCHAR(100) -> VARCHAR(300) (UTF-8下中文占3字节/字符)",
        "compatible": False,
        "note": "这是MySQL迁移到DWS中最常见的截断问题源",
        "migration_difficulty": "中",
        "migration_suggestion": "对含中文VARCHAR列进行数据抽样，按实际最大字符数×3扩充分配"
    },
    {
        "id": "MYSQL-CSET-003", "name": "MySQL排序规则(COLLATE)差异",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL支持丰富的COLLATE(如utf8mb4_general_ci, utf8mb4_unicode_ci)，DWS使用LC_COLLATE",
        "source_pattern": "ORDER BY col COLLATE utf8mb4_unicode_ci",
        "target_solution": "DWS排序规则由LC_COLLATE决定，不支持MySQL自定义Collation",
        "compatible": True,
        "note": "中文排序可能在DWS中表现不同",
        "migration_difficulty": "中",
        "migration_suggestion": "测试DWS默认排序是否满足业务要求; 涉及COLLATE的查询需评估改写"
    },
    {
        "id": "MYSQL-CSET-004", "name": "CHAR定长字段截断风险",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL CHAR(n)是字符数，DWS是字节数，纯ASCII字段可直接映射",
        "source_pattern": "CHAR(10) 纯ASCII字符 → CHAR(10) 直接映射",
        "compatible": True,
        "note": "含中文的CHAR字段需扩展(与VARCHAR同理)",
        "migration_difficulty": "低",
        "migration_suggestion": "纯字母数字CHAR字段直接映射; 含中文CHAR字段按3倍扩展"
    },
]

APP_LAYER_RULES = [
    {
        "id": "MYSQL-APP-001", "name": "JDBC驱动替换",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL JDBC驱动(com.mysql.cj.jdbc.Driver)需替换为DWS PostgreSQL驱动",
        "source_pattern": "jdbc:mysql://host:3306/dbname / com.mysql.cj.jdbc.Driver",
        "target_solution": "jdbc:postgresql://host:8000/dbname / org.postgresql.Driver",
        "compatible": True,
        "note": "默认端口变化: MySQL=3306, DWS=8000",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换JDBC连接URL: mysql→postgresql, 端口3306→8000"
    },
    {
        "id": "MYSQL-APP-002", "name": "MyBatis MySQL方言适配",
        "severity": "warning", "score_deduction": 2,
        "description": "MyBatis中MySQL分页(LIMIT/OFFSET)与DWS兼容",
        "source_pattern": "LIMIT #{limit} OFFSET #{offset}",
        "target_solution": "兼容，DWS支持LIMIT/OFFSET语法",
        "compatible": True, "note": "MySQL分页语法在DWS中兼容",
        "migration_difficulty": "低",
        "migration_suggestion": "MySQL分页语法(LIMIT/OFFSET)在DWS中可直接使用"
    },
    {
        "id": "MYSQL-APP-003", "name": "Hibernate方言(MySQL→PostgreSQL)",
        "severity": "warning", "score_deduction": 2,
        "description": "Hibernate方言从MySQLDialect改为PostgreSQLDialect",
        "source_pattern": "hibernate.dialect=org.hibernate.dialect.MySQL8Dialect",
        "target_solution": "hibernate.dialect=org.hibernate.dialect.PostgreSQL95Dialect",
        "compatible": True,
        "note": "影响标识符生成策略、分页语法等",
        "migration_difficulty": "低",
        "migration_suggestion": "替换方言并测试所有CRUD操作"
    },
]

TRANSACTION_RULES = [
    {
        "id": "MYSQL-TXN-001", "name": "MySQL隔离级别差异",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL REPEATABLE READ(默认)在DWS中对应READ COMMITTED(默认)",
        "source_pattern": "默认 REPEATABLE READ",
        "target_solution": "DWS默认为READ COMMITTED; 可用SET TRANSACTION ISOLATION LEVEL调整",
        "compatible": True,
        "note": "MySQL默认RR, DWS默认RC。RR下的GAP锁行为在DWS中不存在",
        "migration_difficulty": "中",
        "migration_suggestion": "检查业务是否依赖MySQL RR的GAP锁保证一致性; 如有则必须保底使用可串行化隔离级别"
    },
    {
        "id": "MYSQL-TXN-002", "name": "MySQL锁等待超时",
        "severity": "warning", "score_deduction": 2,
        "description": "MySQL innodb_lock_wait_timeout在DWS中对应lock_timeout",
        "source_pattern": "innodb_lock_wait_timeout = 50 (秒)",
        "target_solution": "SET lock_timeout = '50s';",
        "compatible": True,
        "note": "功能对等，配置方式不同",
        "migration_difficulty": "低",
        "migration_suggestion": "在DWS中设置对应的lock_timeout参数"
    },
    {
        "id": "MYSQL-TXN-003", "name": "MySQL XA分布式事务",
        "severity": "error", "score_deduction": 6,
        "description": "MySQL XA事务在DWS中不支持",
        "source_pattern": "XA START / XA END / XA PREPARE / XA COMMIT / XA ROLLBACK",
        "target_solution": "DWS不支持XA协议",
        "compatible": False, "note": "需重新架构分布式事务方案",
        "migration_difficulty": "高",
        "migration_suggestion": "评估XA使用场景; 应用层SAGA或TCC模式替代"
    },
]

CDC_RULES = [
    {
        "id": "MYSQL-CDC-001", "name": "Canal/Kafka CDC兼容性",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL Binlog+Canal+Kafka CDC方案对接DWS需额外工具",
        "tool": "Canal", "compatible": True,
        "note": "Canal捕获MySQL变更→Kafka→Flink/DataX→DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "Canal+Kafka+Flink实时写入DWS; 或Canal+Kafka+DataX批量写入"
    },
    {
        "id": "MYSQL-CDC-002", "name": "华为DRS for MySQL",
        "severity": "info", "score_deduction": 0,
        "description": "华为DRS支持MySQL→DWS全量+增量实时同步",
        "tool": "DRS", "compatible": True,
        "note": "推荐使用DRS实现MySQL→DWS增量同步"
    },
    {
        "id": "MYSQL-CDC-003", "name": "Debezium CDC兼容性",
        "severity": "warning", "score_deduction": 3,
        "description": "Debezium捕获MySQL变更对接DWS",
        "tool": "Debezium", "compatible": True,
        "note": "需要额外配置Kafka Connect接收器",
        "migration_difficulty": "中",
        "migration_suggestion": "Debezium+Kafka Connect+Kafka->Flink/DataX->DWS"
    },
]

PERFORMANCE_RULES = [
    {
        "id": "MYSQL-PERF-001", "name": "MySQL索引Hint差异",
        "severity": "warning", "score_deduction": 3,
        "description": "MySQL USE INDEX/FORCE INDEX在DWS中不支持",
        "source_pattern": "SELECT * FROM t USE INDEX (idx) / FORCE INDEX (idx)",
        "target_solution": "DWS不支持强制索引Hint; 通过更新统计信息和调整查询优化",
        "compatible": False, "note": "需移除所有索引Hint",
        "migration_difficulty": "中",
        "migration_suggestion": "移除USE INDEX/FORCE INDEX; 通过ANALYZE/分布键优化查询"
    },
    {
        "id": "MYSQL-PERF-002", "name": "分布键选择建议",
        "severity": "warning", "score_deduction": 4,
        "description": "MySQL无分布键概念，DWS需每表指定分布键",
        "compatible": True,
        "note": "MySQL的主键列通常是好的分布键候选",
        "migration_difficulty": "高",
        "migration_suggestion": "选择主键或高频JOIN列作为分布键"
    },
]

SUPPLEMENT_RULES = {
    "security": SECURITY_RULES,
    "charset": CHARSET_RULES,
    "app_layer": APP_LAYER_RULES,
    "transaction": TRANSACTION_RULES,
    "cdc": CDC_RULES,
    "performance": PERFORMANCE_RULES,
}
