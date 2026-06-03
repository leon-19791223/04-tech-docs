"""Oracle -> DWS 补充评估规则

补充: 安全/字符集/应用层/事务/CDC同步/性能
基于行业最佳实践和华为UGO评估维度
"""

# ================================================================
# 安全与权限兼容性
# ================================================================
SECURITY_RULES = [
    {
        "id": "ORA-SEC-001", "name": "角色与权限模型差异",
        "severity": "warning", "score_deduction": 4,
        "description": "Oracle使用角色+系统权限+对象权限体系，DWS使用基于角色的访问控制(RBAC)",
        "source_pattern": "GRANT DBA / CONNECT / RESOURCE / SELECT ANY TABLE 等权限",
        "target_solution": "DWS使用GRANT/REVOKE语法兼容，但Oracle特权角色(CONNECT/RESOURCE/DBA)需映射为DWS角色组合",
        "compatible": True,
        "note": "Oracle的SELECT ANY TABLE等ANY权限需逐个对象授权替代",
        "migration_difficulty": "中",
        "migration_suggestion": "分析Oracle权限分配，最小权限原则创建DWS角色"
    },
    {
        "id": "ORA-SEC-002", "name": "虚拟专用数据库(VPD/RLS)",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle VPD(行级安全策略)在DWS中需使用RLS替代",
        "source_pattern": "DBMS_RLS.ADD_POLICY / SYS_CONTEXT 行级访问控制",
        "target_solution": "DWS使用Row-Level Security: ALTER TABLE ... ENABLE ROW LEVEL SECURITY + CREATE POLICY",
        "compatible": False,
        "note": "功能对等但实现机制完全不同",
        "migration_difficulty": "高",
        "migration_suggestion": "将Oracle VPD策略转换为DWS RLS: CREATE POLICY name ON table USING (条件)"
    },
    {
        "id": "ORA-SEC-003", "name": "Oracle审计(AUDIT/UNIFIED AUDIT)",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle统一审计在DWS中使用AUDIT POLICY语法不同",
        "source_pattern": "AUDIT SELECT ON schema.table BY ACCESS / CREATE AUDIT POLICY",
        "target_solution": "DWS使用AUDIT语法: AUDIT TABLE t ACCESS INSERT; 需重新配置审计策略",
        "compatible": True,
        "note": "功能对等但策略定义方式不同",
        "migration_difficulty": "中",
        "migration_suggestion": "将Oracle审计策略逐项映射到DWS AUDIT对象"
    },
    {
        "id": "ORA-SEC-004", "name": "TDE透密数据加密",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle TDE(Transparent Data Encryption)在DWS中支持集群级加密",
        "source_pattern": "ADMINISTER KEY MANAGEMENT / CREATE TABLE ... ENCRYPT",
        "target_solution": "DWS支持TDE(华为云KMS管理密钥)，但加密粒度不同",
        "compatible": True,
        "note": "功能对等但密钥管理方式不同，Oracle使用Wallet，DWS使用KMS",
        "migration_difficulty": "中",
        "migration_suggestion": "评估迁移后是否需要TDE; 如需则使用华为云KMS+DWS集群级加密"
    },
    {
        "id": "ORA-SEC-005", "name": "数据库文件系统访问包",
        "severity": "error", "score_deduction": 6,
        "description": "Oracle UTL_FILE/DBMS_FILE_TRANSFER等文件系统包在DWS中不支持",
        "source_pattern": "UTL_FILE.FOPEN / UTL_FILE.FPUT / DBMS_FILE_TRANSFER",
        "target_solution": "文件I/O操作迁移到应用层或ETL层",
        "compatible": False,
        "note": "DWS在数据库内不支持文件系统读写",
        "migration_difficulty": "高",
        "migration_suggestion": "识别所有文件操作存储过程，将I/O逻辑抽取到应用/ETL层"
    },
]

# ================================================================
# 字符集与编码兼容性
# ================================================================
CHARSET_RULES = [
    {
        "id": "ORA-CSET-001", "name": "Oracle字符集映射(AL32UTF8/ZHS16GBK)",
        "severity": "warning", "score_deduction": 4,
        "description": "Oracle字符集(常见AL32UTF8/ZHS16GBK)到DWS UTF-8的转换",
        "source_pattern": "AL32UTF8(UTF-8) / ZHS16GBK(GBK) / WE8MSWIN1252",
        "target_solution": "DWS统一UTF-8编码; GBK→UTF-8时VARCHAR长度需扩展1.5-3倍",
        "compatible": True,
        "note": "ZHS16GBK转UTF-8时中文从2字节变3字节，VARCHAR长度需扩展",
        "migration_difficulty": "低",
        "migration_suggestion": "确认Oracle字符集: SELECT * FROM nls_database_parameters WHERE parameter='NLS_CHARACTERSET'"
    },
    {
        "id": "ORA-CSET-002", "name": "Oracle VARCHAR长度语义",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle VARCHAR2(n)中n是字节数(默认BYTE)还是字符数取决于设置",
        "source_pattern": "VARCHAR2(100) — n可能是BYTE或CHAR(取决于NLS_LENGTH_SEMANTICS)",
        "target_solution": "DWS VARCHAR(n)中n为字节数，需要确认Oracle设置后调整",
        "compatible": False,
        "note": "Oracle的VARCHAR2语义不确定(可能BYTE或CHAR)，是Oracle迁移中最常见的问题",
        "migration_difficulty": "中",
        "migration_suggestion": "确认Oracle设置: SHOW PARAMETER NLS_LENGTH_SEMANTICS; 若为BYTE则直接映射; 若为CHAR则需扩展3倍"
    },
    {
        "id": "ORA-CSET-003", "name": "NVARCHAR2/NCLOB Unicode处理",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle NVARCHAR2/NCLOB存储Unicode与DWS UTF-8的映射",
        "source_pattern": "NVARCHAR2(n) / NCLOB",
        "target_solution": "NVARCHAR2(n) -> VARCHAR(n*3); NCLOB -> TEXT",
        "compatible": True,
        "note": "DWS统一UTF-8编码，不需要独立的NVARCHAR类型",
        "migration_difficulty": "低",
        "migration_suggestion": "NVARCHAR2(n) -> VARCHAR(n*3); NCLOB -> TEXT"
    },
    {
        "id": "ORA-CSET-004", "name": "Oracle排序规则(NLSSORT)",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle NLSSORT/BINARY排序规则在DWS中行为不同",
        "source_pattern": "NLSSORT(col, 'NLS_SORT=SCHINESE_PINYIN_M')",
        "target_solution": "DWS排序规则由LC_COLLATE决定，可以使用COLLATE子句",
        "compatible": True,
        "note": "中文排序可能在DWS中表现不同",
        "migration_difficulty": "中",
        "migration_suggestion": "测试DWS默认排序是否满足要求; 中文排序问题可通过COLLATE子句微调"
    },
]

# ================================================================
# 应用层兼容性
# ================================================================
APP_LAYER_RULES = [
    {
        "id": "ORA-APP-001", "name": "JDBC驱动替换",
        "severity": "warning", "score_deduction": 3,
        "description": "Oracle JDBC驱动(ojdbc)需替换为DWS PostgreSQL JDBC驱动",
        "source_pattern": "jdbc:oracle:thin:@host:1521/sid / oracle.jdbc.OracleDriver",
        "target_solution": "jdbc:postgresql://host:8000/dbname / org.postgresql.Driver",
        "compatible": True,
        "note": "默认端口变化: Oracle=1521, DWS=8000",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换JDBC连接URL和驱动类名"
    },
    {
        "id": "ORA-APP-002", "name": "连接池配置差异",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle连接检测SQL(select 1 from dual)需替换为DWS的SELECT 1",
        "source_pattern": "validationQuery=SELECT 1 FROM DUAL",
        "target_solution": "validationQuery=SELECT 1",
        "compatible": True,
        "note": "DWS不需要from dual(PostgreSQL风格)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换连接检测SQL"
    },
    {
        "id": "ORA-APP-003", "name": "Hibernate方言(OracleDialect→PostgreSQLDialect)",
        "severity": "warning", "score_deduction": 3,
        "description": "Hibernate方言需从OracleDialect改为PostgreSQLDialect",
        "source_pattern": "hibernate.dialect=org.hibernate.dialect.Oracle12cDialect",
        "target_solution": "hibernate.dialect=org.hibernate.dialect.PostgreSQL95Dialect",
        "compatible": True,
        "note": "影响序列访问、分页、IDENTITY策略",
        "migration_difficulty": "低",
        "migration_suggestion": "替换方言并测试所有数据库操作"
    },
    {
        "id": "ORA-APP-004", "name": "MyBatis分页语法差异",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle MyBatis ROWNUM分页需改为DWS LIMIT/OFFSET",
        "source_pattern": "SELECT * FROM (SELECT a.*, ROWNUM rn FROM ( ... ) a WHERE ROWNUM <= #{end}) WHERE rn > #{start}",
        "target_solution": "SELECT * FROM ... LIMIT #{limit} OFFSET #{offset}",
        "compatible": True,
        "note": "ROWNUM伪列分页需改写",
        "migration_difficulty": "中",
        "migration_suggestion": "全局替换Oracle ROWNUM分页为LIMIT/OFFSET语法"
    },
]

# ================================================================
# 事务与并发兼容性
# ================================================================
TRANSACTION_RULES = [
    {
        "id": "ORA-TXN-001", "name": "事务隔离级别映射",
        "severity": "info", "score_deduction": 0,
        "description": "Oracle隔离级别(READ COMMITTED/SERIALIZABLE)与DWS行为基本一致",
        "compatible": True, "note": "基本兼容。注意Oracle默认READ COMMITTED，DWS也是"
    },
    {
        "id": "ORA-TXN-002", "name": "Oracle自治事务(PRAGMA AUTONOMOUS_TRANSACTION)",
        "severity": "error", "score_deduction": 8,
        "description": "Oracle自治事务在DWS中不支持",
        "source_pattern": "PRAGMA AUTONOMOUS_TRANSACTION; ... COMMIT;",
        "target_solution": "DWS不支持自治事务，需通过dblink或应用层实现独立事务",
        "compatible": False,
        "note": "需重点识别并改造",
        "migration_difficulty": "高",
        "migration_suggestion": "1)拆分函数在应用层控制事务; 2)使用dblink到自身模拟"
    },
    {
        "id": "ORA-TXN-003", "name": "分布式事务(XA)支持",
        "severity": "error", "score_deduction": 6,
        "description": "Oracle XA事务在DWS中不支持",
        "source_pattern": "XA START / XA END / XA PREPARE / XA COMMIT / XA ROLLBACK",
        "target_solution": "DWS不支持XA协议，需在应用层通过SAGA或TCC实现",
        "compatible": False,
        "note": "需重新架构分布式事务方案",
        "migration_difficulty": "高",
        "migration_suggestion": "评估XA使用场景: 1)最终一致性→异步补偿; 2)强一致性→SAGA/TCC"
    },
]

# ================================================================
# CDC增量同步兼容性
# ================================================================
CDC_RULES = [
    {
        "id": "ORA-CDC-001", "name": "Oracle GoldenGate (OGG) 兼容性",
        "severity": "warning", "score_deduction": 3,
        "description": "OGG可对接DWS，但需安装DWS适配器",
        "tool": "GoldenGate", "compatible": True,
        "note": "需升级OGG版本以支持DWS目标端",
        "migration_difficulty": "中",
        "migration_suggestion": "确认OGG版本是否支持PostgreSQL/DWS目标端; 不支持则升级"
    },
    {
        "id": "ORA-CDC-002", "name": "华为DRS for Oracle",
        "severity": "info", "score_deduction": 0,
        "description": "华为DRS支持Oracle→DWS全量+增量实时同步",
        "tool": "DRS", "compatible": True,
        "note": "推荐使用DRS进行Oracle→DWS增量同步"
    },
    {
        "id": "ORA-CDC-003", "name": "LogMiner/Redo日志捕获限制",
        "severity": "warning", "score_deduction": 3,
        "description": "基于LogMiner的CDC工具对Oracle重做日志大小和归档策略有要求",
        "tool": "LogMiner", "compatible": True,
        "note": "建议开启归档日志+补充日志(Supplemental Log)",
        "migration_difficulty": "低",
        "migration_suggestion": "确认Oracle归档日志已开启: ARCHIVE LOG LIST; 开启补充日志: ALTER DATABASE ADD SUPPLEMENTAL LOG DATA"
    },
]

# ================================================================
# 性能与容量兼容性
# ================================================================
PERFORMANCE_RULES = [
    {
        "id": "ORA-PERF-001", "name": "分布键选择建议",
        "severity": "warning", "score_deduction": 4,
        "description": "Oracle无分布键概念，DWS需每表指定分布键",
        "compatible": True,
        "note": "选择均匀分布的JOIN/GROUP BY列作为分布键",
        "migration_difficulty": "高",
        "migration_suggestion": "分析JOIN和GROUP BY模式，使用高基数列作为分布键"
    },
    {
        "id": "ORA-PERF-002", "name": "Oracle Hint到DWS执行计划",
        "severity": "warning", "score_deduction": 4,
        "description": "Oracle优化器Hint(/ *+ INDEX(t) */)在DWS中不支持",
        "source_pattern": "SELECT /*+ INDEX(t idx_name) */ / /*+ FULL(t) */ / /*+ PARALLEL(t,4) */",
        "target_solution": "DWS不支持Oracle风格Hint; 通过统计信息分析和分布键设计优化",
        "compatible": False, "note": "Oracle Hint需重写为DWS可理解的执行计划控制",
        "migration_difficulty": "高",
        "migration_suggestion": "移除所有Oracle Hint; 通过更新统计信息、调整分布键、Workload级别参数优化查询"
    },
    {
        "id": "ORA-PERF-003", "name": "并行查询设置",
        "severity": "warning", "score_deduction": 2,
        "description": "Oracle PARALLEL DEGREE在DWS中通过query_dop参数控制",
        "source_pattern": "ALTER SESSION SET PARALLEL_DEGREE=4 / SELECT /*+ PARALLEL(t,4) */",
        "target_solution": "SET query_dop = 4; — DWS通过数据库级/会话级参数控制并行度",
        "compatible": True,
        "note": "功能对等但实现方式不同",
        "migration_difficulty": "低",
        "migration_suggestion": "分析Oracle并行度设置，在DWS会话层/数据库层设置query_dop"
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
