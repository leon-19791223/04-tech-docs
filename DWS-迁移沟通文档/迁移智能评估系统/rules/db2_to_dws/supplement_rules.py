"""DB2 -> DWS 补充评估规则

补充: 安全/字符集/应用层/事务/CDC同步/性能
基于行业最佳实践和华为UGO评估维度
"""

# ================================================================
# 安全与权限兼容性
# ================================================================
SECURITY_RULES = [
    {
        "id": "DB2-SEC-001", "name": "角色与权限模型差异",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2使用GROUP/ROLE+LBAC权限模型，DWS使用基于角色的访问控制(RBAC)",
        "source_pattern": "GRANT DBADM / SECADM / LOAD 等权限",
        "target_solution": "DWS使用GRANT/REVOKE语法兼容，但DB2特有权限(DBADM/SECADM)需映射为DWS角色组合",
        "compatible": True,
        "note": "需将DB2权限分类映射: DBADM→SYSADMIN, DATAACCESS→对象级GRANT",
        "migration_difficulty": "中",
        "migration_suggestion": "分析DB2权限分配，在DWS中创建对应角色并分配等效权限"
    },
    {
        "id": "DB2-SEC-002", "name": "超级用户权限(SYSADM)",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 SYSADM权限在DWS托管环境中可能受限",
        "source_pattern": "SYSADM / DBADM 超级用户权限",
        "target_solution": "DWS SYSADMIN权限由华为云管理，用户无法获得完全超级用户权限",
        "compatible": True,
        "note": "需检查SQL/存储过程中是否依赖超级用户权限才能执行的操作",
        "migration_difficulty": "低",
        "migration_suggestion": "将依赖超级用户的操作提前识别，改为普通用户+特定对象权限"
    },
    {
        "id": "DB2-SEC-003", "name": "LBAC行级安全标签",
        "severity": "error", "score_deduction": 8,
        "description": "DB2 LBAC(Label-Based Access Control)行级安全在DWS中不支持",
        "source_pattern": "SECURITY POLICY / LBAC 安全标签",
        "target_solution": "使用DWS行级安全策略(RLS)替代: ALTER TABLE ... ENABLE ROW LEVEL SECURITY",
        "compatible": False,
        "note": "LBAC是DB2独有的安全特性，需完全重写为DWS RLS策略",
        "migration_difficulty": "高",
        "migration_suggestion": "将LBAC安全策略转换为DWS RLS: CREATE POLICY ... USING (条件表达式)"
    },
    {
        "id": "DB2-SEC-004", "name": "审计策略(AUDIT)",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 AUDIT审计策略在DWS中使用AUDIT POLICY语法不同",
        "source_pattern": "AUDIT CHECK ... / CREATE AUDIT POLICY",
        "target_solution": "DWS使用AUDIT语法: AUDIT TABLE t ACCESS INSERT; 需重新配置",
        "compatible": True,
        "note": "功能对等，但审计策略的定义和管理方式完全不同",
        "migration_difficulty": "中",
        "migration_suggestion": "将DB2审计策略逐项映射到DWS AUDIT对象"
    },
    {
        "id": "DB2-SEC-005", "name": "TLS/SSL传输加密",
        "severity": "info", "score_deduction": 0,
        "description": "DB2 TLS/SSL配置需在DWS端重新配置",
        "source_pattern": "SSL Server/Client 证书配置",
        "target_solution": "DWS支持TLS 1.2+加密连接，需配置SSL证书",
        "compatible": True, "note": "功能完全支持，需重新配置证书"
    },
    {
        "id": "DB2-SEC-006", "name": "加密函数与TDE",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2内置加密函数(ENCRYPT/DECRYPT/GETHINT)和TDE在DWS中需不同方案",
        "source_pattern": "ENCRYPT(data, password) / DECRYPT_BIN / TDE表空间加密",
        "target_solution": "DWS支持pgcrypto扩展(兼容)和集群级TDE，但函数名和用法不同",
        "compatible": True,
        "note": "DB2的ENCRYPT/DECRYPT函数需改为pgcrypto的encrypt/decrypt",
        "migration_difficulty": "中",
        "migration_suggestion": "检查加密使用场景: 1)列级加密→pgcrypto扩展; 2)TDE→DWS集群级加密"
    },
    {
        "id": "DB2-SEC-007", "name": "文件系统访问权限(UTL_FILE等)",
        "severity": "error", "score_deduction": 6,
        "description": "DB2存储过程可访问文件系统，DWS不支持",
        "source_pattern": "CALL SYSPROC.UTL_FILE.Open / 存储过程读文件",
        "target_solution": "文件操作迁移到应用层或ETL层处理",
        "compatible": False,
        "note": "DWS在数据库内不支持文件系统读写",
        "migration_difficulty": "高",
        "migration_suggestion": "识别所有文件操作存储过程，将其I/O逻辑抽取到应用/ETL层"
    },
]

# ================================================================
# 字符集与编码兼容性
# ================================================================
CHARSET_RULES = [
    {
        "id": "DB2-CSET-001", "name": "源库字符集检测与映射",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2可能使用GBK/GB18030/UTF-8等多种编码，DWS统一UTF-8",
        "source_pattern": "DB2 Code Set = 1386(GBK) / 1208(UTF-8) / 54937(GB18030)",
        "target_solution": "DWS统一UTF-8编码，非UTF-8编码转UTF-8时VARCHAR长度需1.5-3倍扩展",
        "compatible": True,
        "note": "GBK→UTF-8转换时VARCHAR长度建议按1.5倍(英数混合)到3倍(纯中文)扩展",
        "migration_difficulty": "低",
        "migration_suggestion": "迁移前确认DB2编码: db2 get db cfg show detail | grep 'code set'"
    },
    {
        "id": "DB2-CSET-002", "name": "中文等宽字符处理",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2中VARCHAR(n)的n为字符数，DWS中为字节数，中文场景差异显著",
        "source_pattern": "VARCHAR(50) 含中文→实际存储25个中文字符",
        "target_solution": "VARCHAR(50) -> VARCHAR(150) (UTF-8下中文占3字节/字符)",
        "compatible": True,
        "note": "这是DB2迁移中最常见的截断问题来源",
        "migration_difficulty": "中",
        "migration_suggestion": "对含中文VARCHAR列进行数据抽样，按实际最大字符数×3扩充分配"
    },
    {
        "id": "DB2-CSET-003", "name": "GRAPHIC/VARGRAPHIC双字节类型",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 GRAPHIC存储双字节字符(中文/日文/韩文)，DWS无对应类型",
        "source_pattern": "GRAPHIC(n) / VARGRAPHIC(n)",
        "target_solution": "GRAPHIC(n) -> CHAR(n*3); VARGRAPHIC(n) -> VARCHAR(n*3) (UTF-8编码)",
        "compatible": True,
        "note": "UTF-8下每个双字节字符最多占3字节",
        "migration_difficulty": "低",
        "migration_suggestion": "批量替换DDL: GRAPHIC(n)->CHAR(n*3), VARGRAPHIC(n)->VARCHAR(n*3)"
    },
    {
        "id": "DB2-CSET-004", "name": "排序规则(Collation)差异",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2支持自定义排序规则(System/Identity/CLDR)，DWS使用数据库默认LC_COLLATE",
        "source_pattern": "ORDER BY name COLLATE SYSTEM_814_ZH_CN / COLLATE CLDR1401_ZH",
        "target_solution": "DWS排序规则由数据库级别LC_COLLATE决定，不支持自定义Collation",
        "compatible": True,
        "note": "中文排序可能在DWS中表现不同，需验证关键业务排序",
        "migration_difficulty": "中",
        "migration_suggestion": "测试DWS默认排序是否满足业务要求; 如需特定排序，使用ORDER BY ... COLLATE子句"
    },
    {
        "id": "DB2-CSET-005", "name": "特殊字符与数据截断风险",
        "severity": "warning", "score_deduction": 3,
        "description": "VARCHAR长度扩展不足可能导致数据迁移时截断",
        "compatible": True,
        "note": "建议在迁移前对每个VARCHAR/CHAR字段进行MAX(LENGTH(column))分析，确认实际长度分布",
        "migration_difficulty": "低",
        "migration_suggestion": "迁移前执行: SELECT col, MAX(LENGTH(col)) FROM t GROUP BY col; 根据结果调整DDL长度"
    },
]

# ================================================================
# 应用层兼容性
# ================================================================
APP_LAYER_RULES = [
    {
        "id": "DB2-APP-001", "name": "JDBC驱动兼容性",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 Type4驱动(com.ibm.db2.jcc)需替换为DWS PostgreSQL JDBC驱动",
        "source_pattern": "jdbc:db2://host:50000/dbname / com.ibm.db2.jcc.Driver",
        "target_solution": "jdbc:postgresql://host:8000/dbname / org.postgresql.Driver",
        "compatible": True,
        "note": "连接URL、驱动类名、默认端口(DB2=50000, DWS=8000)完全不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换JDBC连接配置: jdbc:db2:// → jdbc:postgresql://, 端口50000→8000"
    },
    {
        "id": "DB2-APP-002", "name": "连接池配置差异",
        "severity": "warning", "score_deduction": 2,
        "description": "DB2连接池配置参数(连接检测SQL、超时等)需适配DWS",
        "source_pattern": "validationQuery=SELECT 1 FROM SYSIBM.SYSDUMMY1",
        "target_solution": "DWS连接检测SQL: validationQuery=SELECT 1 (更简洁)",
        "compatible": True,
        "note": "DB2常用连接检测SQL是SELECT 1 FROM SYSIBM.SYSDUMMY1，DWS使用SELECT 1即可",
        "migration_difficulty": "低",
        "migration_suggestion": "替换连接检测SQL为SELECT 1; 检查连接池配置中的DB2特有参数"
    },
    {
        "id": "DB2-APP-003", "name": "ORM框架适配-MyBatis",
        "severity": "warning", "score_deduction": 3,
        "description": "MyBatis应用中DB2分页语法(<foreach>/OFFSET)需适配DWS",
        "source_pattern": "OFFSET #{offset} ROWS FETCH NEXT #{limit} ROWS ONLY",
        "target_solution": "DWS两种语法都支持: LIMIT #{limit} OFFSET #{offset} 或 FETCH语法",
        "compatible": True,
        "note": "MyBatis映射文件中的数据库方言需调整",
        "migration_difficulty": "低",
        "migration_suggestion": "建议全局统一使用LIMIT/OFFSET语法，DB2的FETCH语法在DWS也兼容"
    },
    {
        "id": "DB2-APP-004", "name": "ORM框架适配-Hibernate",
        "severity": "warning", "score_deduction": 3,
        "description": "Hibernate方言(DB2Dialect)需改为PostgreSQL方言(PostgreSQLDialect)",
        "source_pattern": "hibernate.dialect=org.hibernate.dialect.DB2Dialect",
        "target_solution": "hibernate.dialect=org.hibernate.dialect.PostgreSQLDialect 或 PostgreSQL95Dialect",
        "compatible": True,
        "note": "Hibernate方言影响SQL生成策略、序列访问方式、分页语法",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换Hibernate方言配置; 测试所有数据库操作接口的兼容性"
    },
    {
        "id": "DB2-APP-005", "name": "ODBC驱动及.NET兼容性",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 ODBC/.NET应用需替换为DWS ODBC驱动",
        "source_pattern": "DRIVER={IBM DB2 ODBC DRIVER} / IBM.Data.DB2",
        "target_solution": "DRIVER={PostgreSQL ODBC Driver(UNICODE)} / Npgsql",
        "compatible": True,
        "note": ".NET应用需将IBM.Data.DB2替换为Npgsql库",
        "migration_difficulty": "中",
        "migration_suggestion": ".NET应用: 安装Npgsql NuGet包，替换连接字符串和类型映射"
    },
]

# ================================================================
# 事务与并发兼容性
# ================================================================
TRANSACTION_RULES = [
    {
        "id": "DB2-TXN-001", "name": "事务隔离级别映射",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2隔离级别(UR/CS/RS/RR)与DWS(READ COMMITTED/REPEATABLE READ/SERIALIZABLE)映射需确认",
        "source_pattern": "WITH UR (Uncommitted Read) / CS (Cursor Stability) / RS (Read Stability) / RR (Repeatable Read)",
        "target_solution": "UR→READ UNCOMMITTED; CS→READ COMMITTED(默认); RS→REPEATABLE READ; RR→SERIALIZABLE",
        "compatible": True,
        "note": "DB2的UR级别在DWS中可能不直接支持，需改为READ UNCOMMITTED",
        "migration_difficulty": "中",
        "migration_suggestion": "检查应用中WITH UR的使用，改为DWS等效隔离级别; 注意行为差异"
    },
    {
        "id": "DB2-TXN-002", "name": "锁超时与死锁处理",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2 LOCK TIMEOUT在DWS中对应lock_timeout配置",
        "source_pattern": "CURRENT LOCK TIMEOUT = 30 (默认-1=无限等待)",
        "target_solution": "SET lock_timeout = '30s'; DWS不等待锁默认行为与DB2不同",
        "compatible": True,
        "note": "DB2默认锁等待行为是永不等(dlzTimeOut=-1)，DWS默认是永不等(lock_timeout=0)",
        "migration_difficulty": "低",
        "migration_suggestion": "在会话/应用层设置lock_timeout匹配原DB2行为"
    },
    {
        "id": "DB2-TXN-003", "name": "长事务与批量作业",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2支持大规模批量作业长事务，DWS对长事务有资源限制",
        "compatible": True,
        "note": "DWS长事务可能导致快照过旧(OLD SNAPSHOT)或磁盘膨胀",
        "migration_difficulty": "中",
        "migration_suggestion": "评估批量作业的事务粒度: 拆分为小事务批量提交; 监控长事务的持锁时间"
    },
    {
        "id": "DB2-TXN-004", "name": "XA分布式事务支持",
        "severity": "error", "score_deduction": 6,
        "description": "DB2支持XA分布式事务(transaction manager)，DWS不支持外部XA",
        "source_pattern": "XA START / XA END / XA PREPARE / XA COMMIT",
        "target_solution": "DWS不支持XA协议，需在应用层通过SAGA或TCC模式实现分布式事务",
        "compatible": False,
        "note": "金融行业分布式事务场景需重新架构",
        "migration_difficulty": "高",
        "migration_suggestion": "评估XA使用场景: 1)业务可容忍最终一致性→异步补偿; 2)需强一致性→应用层SAGA模式"
    },
]

# ================================================================
# CDC增量同步兼容性
# ================================================================
CDC_RULES = [
    {
        "id": "DB2-CDC-001", "name": "DB2 CDC原生同步",
        "severity": "warning", "score_deduction": 3,
        "description": "DB2原生CDC可通过DRS实现DB2→DWS全量+增量同步",
        "tool": "DRS / DB2 CDC", "compatible": True,
        "note": "华为DRS支持DB2 LUW 9.7-11.5到DWS的增量同步",
        "migration_difficulty": "中",
        "migration_suggestion": "使用华为DRS的DB2→DWS实时同步链路，减少手动增量处理"
    },
    {
        "id": "DB2-CDC-002", "name": "DB2 CDC限制-大对象",
        "severity": "error", "score_deduction": 5,
        "description": "DRS增量同步时CLOB/BLOB有大小限制: BLOB<10MB; CLOB尾部空格可能被截断",
        "tool": "DRS", "compatible": False,
        "note": "DRS增量同步对大对象支持有限",
        "migration_difficulty": "中",
        "migration_suggestion": "超大LOB提前迁移(全量); 增量期间LOB限制使用文件引用+OBS存储"
    },
    {
        "id": "DB2-CDC-003", "name": "无主键表增量同步风险",
        "severity": "error", "score_deduction": 5,
        "description": "DB2中无主键表(含LOB的)增量同步可能导致数据不一致",
        "tool": "DRS", "compatible": False,
        "note": "DRS增量同步依赖主键确认变更行; 无主键表的UPDATE/DELETE可能异常",
        "migration_difficulty": "中",
        "migration_suggestion": "为无主键表添加主键(或唯一索引+NOT NULL); 无法加主键的表使用全量重新同步"
    },
    {
        "id": "DB2-CDC-004", "name": "DB2分布式集群CDC限制",
        "severity": "error", "score_deduction": 6,
        "description": "DRS不支持分布式DB2集群(PureScale多节点)作为CDC源",
        "tool": "DRS", "compatible": False,
        "note": "分布式DB2集群的LSN可能乱序，DRS无法保证增量数据顺序",
        "migration_difficulty": "高",
        "migration_suggestion": "1)通过备份+还原到单节点DB2再迁移; 2)使用第三方CDC工具+DataX批同步"
    },
    {
        "id": "DB2-CDC-005", "name": "CDC增量同步延迟监控",
        "severity": "warning", "score_deduction": 3,
        "description": "增量同步延迟超过30秒需触发告警",
        "tool": "DRS", "compatible": True,
        "note": "建议设置DRS延迟告警阈值30秒，监控CPU利用率(<70%)和网络带宽(<85%)",
        "migration_difficulty": "低",
        "migration_suggestion": "配置DRS任务告警: 延迟阈值30秒, CPU>70%告警"
    },
]

# ================================================================
# 性能与容量兼容性
# ================================================================
PERFORMANCE_RULES = [
    {
        "id": "DB2-PERF-001", "name": "分布键选择建议",
        "severity": "warning", "score_deduction": 4,
        "description": "DB2无分布键概念，DWS需为每张表选择合适分布键，直接影响查询性能",
        "compatible": True,
        "note": "分布键选择原则: 1)高频JOIN的表使用相同分布键; 2)GROUP BY列与分布键一致; 3)选择值分布均匀的列",
        "migration_difficulty": "高",
        "migration_suggestion": "分析应用JOIN和GROUP BY模式，按业务优先级选择分布键: 事实表按账号/客户ID分布"
    },
    {
        "id": "DB2-PERF-002", "name": "数据倾斜风险",
        "severity": "warning", "score_deduction": 3,
        "description": "分布键选择不当导致数据倾斜，部分节点成为性能瓶颈",
        "compatible": True,
        "note": "建议先分析源库数据分布特征，选择分布均匀的列; 高并发场景考虑REPLICATION分布",
        "migration_difficulty": "中",
        "migration_suggestion": "分析表主键和值分布; 倾斜风险高时使用多个列的组合分布在迁移前评估: SELECT col, COUNT(*) FROM t GROUP BY col"
    },
    {
        "id": "DB2-PERF-003", "name": "批量导入性能(COPY vs INSERT)",
        "severity": "info", "score_deduction": 0,
        "description": "DWS COPY命令批量导入性能是INSERT的5-10倍",
        "compatible": True,
        "note": "推荐使用COPY或GDS并行导入; 避免逐行INSERT",
        "migration_difficulty": "低",
        "migration_suggestion": "批量数据加载优先使用COPY; 百GB级使用GDS外表并行导入"
    },
    {
        "id": "DB2-PERF-004", "name": "列存表压缩优势",
        "severity": "info", "score_deduction": 0,
        "description": "DWS列存表压缩比可达10:1，大幅降低存储成本",
        "compatible": True,
        "note": "建议事实表(交易流水/估值数据)使用列存; 维度表(频繁UPDEL)使用行存",
        "migration_difficulty": "低",
        "migration_suggestion": "分析表访问模式: 大批量查询→列存; 频繁单行操作→行存"
    },
]

# 聚合导出
SUPPLEMENT_RULES = {
    "security": SECURITY_RULES,
    "charset": CHARSET_RULES,
    "app_layer": APP_LAYER_RULES,
    "transaction": TRANSACTION_RULES,
    "cdc": CDC_RULES,
    "performance": PERFORMANCE_RULES,
}
