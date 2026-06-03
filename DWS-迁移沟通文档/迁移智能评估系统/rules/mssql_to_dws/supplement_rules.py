"""SQL Server -> DWS 补充评估规则

补充: 安全/字符集/应用层/事务/CDC同步/性能
"""

SECURITY_RULES = [
    {
        "id": "MSSQL-SEC-001", "name": "SQL Server权限模型差异",
        "severity": "warning", "score_deduction": 4,
        "description": "SQL Server用户/角色/架构分离的权限模型与DWS RBAC不同",
        "source_pattern": "GRANT SELECT, INSERT ON SCHEMA::schema TO user / sp_addrolemember",
        "target_solution": "DWS使用GRANT ON schema/table TO user; SQL Server的架构(SCHEMA OWNER)在DWS中对应Schema所有者",
        "compatible": True,
        "note": "SQL Server的Fixed Database Roles(db_owner/db_datareader等)需映射为DWS自定义角色",
        "migration_difficulty": "中",
        "migration_suggestion": "将SQL Server固定角色映射为DWS角色组合; 使用GRANT ON ALL TABLES IN SCHEMA批量授权"
    },
    {
        "id": "MSSQL-SEC-002", "name": "SQL Server加密体系",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server TDE/列级加密/Always Encrypted在DWS中需不同方案",
        "source_pattern": "CREATE DATABASE ENCRYPTION KEY / Always Encrypted / Column Master Key",
        "target_solution": "DWS使用集群级TDE(华为云KMS)+ pgcrypto扩展; 不支持Always Encrypted",
        "compatible": True,
        "note": "Always Encrypted应用层加密需特别处理",
        "migration_difficulty": "高",
        "migration_suggestion": "Always Encrypted: 解密后迁移到DWS，使用应用层加密+DWS TDE替代"
    },
    {
        "id": "MSSQL-SEC-003", "name": "SQL Server行级安全(RLS)",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server行级安全(SECURITY POLICY)在DWS中对应RLS",
        "source_pattern": "CREATE SECURITY POLICY / FILTER PREDICATE / BLOCK PREDICATE",
        "target_solution": "DWS使用Row-Level Security: ALTER TABLE ... ENABLE ROW LEVEL SECURITY + CREATE POLICY",
        "compatible": False,
        "note": "功能对等但语法完全不同; SQL Server的BLOCK PREDICATE在DWS中不支持",
        "migration_difficulty": "高",
        "migration_suggestion": "将SECURITY POLICY转换为DWS RLS: CREATE POLICY … USING(条件); BLOCK操作由应用层控制"
    },
    {
        "id": "MSSQL-SEC-004", "name": "SQL Server审核(AUDIT)",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server审核(SERVER AUDIT/DB AUDIT)在DWS中使用AUDIT POLICY",
        "source_pattern": "CREATE SERVER AUDIT / CREATE DATABASE AUDIT SPECIFICATION",
        "target_solution": "DWS使用AUDIT语法: AUDIT TABLE t ACCESS INSERT; 需重新配置",
        "compatible": True,
        "note": "功能对等但配置和管理方式不同",
        "migration_difficulty": "中",
        "migration_suggestion": "分析SQL Server审核策略，在DWS中创建等效AUDIT对象"
    },
]

CHARSET_RULES = [
    {
        "id": "MSSQL-CSET-001", "name": "SQL Server字符集映射",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server Latin1/Chinese_PRC_CI_AS等字符集映射到DWS UTF-8",
        "source_pattern": "Latin1_General_CI_AS / Chinese_PRC_CI_AS / Japanese_XJIS_CI_AS",
        "target_solution": "DWS统一UTF-8编码; 源库字符集非UTF-8时需转换",
        "compatible": True,
        "note": "Chinese_PRC_CI_AS到UTF-8转换影响排序和比较行为",
        "migration_difficulty": "中",
        "migration_suggestion": "检查COLLATION: SELECT SERVERPROPERTY('Collation'); 非UTF-8转UTF-8时VARCHAR长度需扩展"
    },
    {
        "id": "MSSQL-CSET-002", "name": "NVARCHAR/NCHAR Unicode处理",
        "severity": "info", "score_deduction": 0,
        "description": "SQL Server NVARCHAR(N)存储Unicode(UCS-2/UTF-16)，映射到DWS UTF-8 VARCHAR",
        "compatible": True,
        "note": "NVARCHAR(n) -> VARCHAR(n*3): UTF-16→UTF-8可能扩容; 纯英文场景不需扩展",
        "migration_difficulty": "低",
        "migration_suggestion": "含中文的NVARCHAR列按3倍扩展; 纯ASCII的直接映射为相同长度VARCHAR"
    },
    {
        "id": "MSSQL-CSET-003", "name": "VARCHAR长度语义差异",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server VARCHAR(n)的n是字符数(非Unicode)，DWS的n是字节数",
        "source_pattern": "VARCHAR(100) 含中文→实际可存100个中文字符(SQL Server)",
        "target_solution": "VARCHAR(100) -> VARCHAR(300) (UTF-8下中文占3字节/字符)",
        "compatible": False,
        "note": "与MySQL/DB2相同的问题: 字符数→字节数",
        "migration_difficulty": "中",
        "migration_suggestion": "对含中文VARCHAR列按3倍扩展; 纯ASCII/VARCHAR(MAX)不受此限制"
    },
]

APP_LAYER_RULES = [
    {
        "id": "MSSQL-APP-001", "name": "JDBC驱动替换",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server JDBC驱动(com.microsoft.sqlserver.jdbc.SQLServerDriver)需替换为PostgreSQL驱动",
        "source_pattern": "jdbc:sqlserver://host:1433;databaseName=db / com.microsoft.sqlserver.jdbc.SQLServerDriver",
        "target_solution": "jdbc:postgresql://host:8000/dbname / org.postgresql.Driver",
        "compatible": True,
        "note": "端口变化: SQL Server=1433, DWS=8000; 连接串格式也不同",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换JDBC连接配置: sqlserver→postgresql, 端口1433→8000, 参数格式调整"
    },
    {
        "id": "MSSQL-APP-002", "name": ".NET Npgsql适配",
        "severity": "warning", "score_deduction": 3,
        "description": ".NET应用使用System.Data.SqlClient需替换为Npgsql",
        "source_pattern": "System.Data.SqlClient.SqlConnection / connectionString=Server=host;Database=db",
        "target_solution": "Npgsql.NpgsqlConnection / connectionString=Host=host;Database=db",
        "compatible": True,
        "note": ".NET生态中SQL Server的原生客户端需替换为Npgsql",
        "migration_difficulty": "中",
        "migration_suggestion": "通过NuGet安装Npgsql; 替换using System.Data.SqlClient→Npgsql; 调整连接字符串格式"
    },
    {
        "id": "MSSQL-APP-003", "name": "Entity Framework适配",
        "severity": "warning", "score_deduction": 3,
        "description": "Entity Framework SQL Server Provider需替换为PostgreSQL Provider",
        "source_pattern": "UseSqlServer(connectionString) / EntityFramework.SqlServer",
        "target_solution": "UseNpgsql(connectionString) / Npgsql.EntityFrameworkCore.PostgreSQL",
        "compatible": True,
        "note": "需替换EF Provider并调整数据类型映射",
        "migration_difficulty": "中",
        "migration_suggestion": "安装Npgsql.EntityFrameworkCore.PostgreSQL包; 替换UseSqlServer为UseNpgsql; 测试所有LINQ查询"
    },
    {
        "id": "MSSQL-APP-004", "name": "MyBatis SQL Server分页",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server OFFSET/FETCH分页在DWS中兼容",
        "source_pattern": "OFFSET #{offset} ROWS FETCH NEXT #{limit} ROWS ONLY",
        "target_solution": "LIMIT #{limit} OFFSET #{offset} 或 FETCH语法兼容",
        "compatible": True, "note": "两种语法都兼容",
        "migration_difficulty": "低",
        "migration_suggestion": "可保留FETCH语法或简化使用LIMIT/OFFSET"
    },
]

TRANSACTION_RULES = [
    {
        "id": "MSSQL-TXN-001", "name": "事务隔离级别映射",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server隔离级别(READ UNCOMMITTED/READ COMMITTED/REPEATABLE READ/SERIALIZABLE/SNAPSHOT)与DWS差异",
        "source_pattern": "SET TRANSACTION ISOLATION LEVEL READ UNCOMMITTED / SNAPSHOT",
        "target_solution": "DWS不支持SNAPSHOT隔离级别; READ UNCOMMITTED行为不同",
        "compatible": True,
        "note": "SQL Server SNAPSHOT隔离在DWS中无直接对应; READ UNCOMMITTED在PG/DWS中相当于READ COMMITTED",
        "migration_difficulty": "中",
        "migration_suggestion": "SNAPSHOT隔离改为REPEATABLE READ; READ UNCOMMITTED改为READ COMMITTED"
    },
    {
        "id": "MSSQL-TXN-002", "name": "长事务与锁超时",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server锁超时(SET LOCK_TIMEOUT)在DWS中对应lock_timeout参数",
        "source_pattern": "SET LOCK_TIMEOUT 5000 (毫秒)",
        "target_solution": "SET lock_timeout = '5s'; DWS以秒为单位",
        "compatible": True,
        "note": "功能对等，单位不同(SQL Server毫秒, DWS秒)",
        "migration_difficulty": "低",
        "migration_suggestion": "全局替换锁超时参数，注意毫秒→秒的换算"
    },
    {
        "id": "MSSQL-TXN-003", "name": "SQL Server分布式事务(MSDTC)",
        "severity": "error", "score_deduction": 6,
        "description": "SQL Server MSDTC分布式事务在DWS中不支持",
        "source_pattern": "BEGIN DISTRIBUTED TRANSACTION / MSDTC两阶段提交",
        "target_solution": "DWS不支持分布式事务协调器",
        "compatible": False, "note": "需重新架构分布式事务方案",
        "migration_difficulty": "高",
        "migration_suggestion": "应用层SAGA/TCC模式替代MSDTC; 或解耦为独立事务+补偿机制"
    },
]

CDC_RULES = [
    {
        "id": "MSSQL-CDC-001", "name": "SQL Server CDC变更数据捕获",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server原生CDC可对接DWS，需通过ETL/Kafka中转",
        "tool": "SQL Server CDC", "compatible": True,
        "note": "CDC表作为数据源由ETL工具增量读取到DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "SQL Server CDC + Kettle/DataX增量抽取→DWS; 或Debezium+Kafka+Flink→DWS"
    },
    {
        "id": "MSSQL-CDC-002", "name": "DRS for SQL Server",
        "severity": "info", "score_deduction": 0,
        "description": "华为DRS支持SQL Server→DWS全量+增量同步",
        "tool": "DRS", "compatible": True,
        "note": "推荐使用DRS进行SQL Server→DWS增量同步"
    },
    {
        "id": "MSSQL-CDC-003", "name": "SQL Server复制功能迁移",
        "severity": "error", "score_deduction": 5,
        "description": "SQL Server事务复制/合并复制在DWS中不支持",
        "tool": "SQL Server Replication", "compatible": False,
        "note": "需使用DRS或CDC+Kafka替代",
        "migration_difficulty": "中",
        "migration_suggestion": "SQL Server Replication功能由DRS全量+增量同步替代"
    },
]

PERFORMANCE_RULES = [
    {
        "id": "MSSQL-PERF-001", "name": "SQL Server索引Hint(INDEX/NOLOCK)",
        "severity": "warning", "score_deduction": 3,
        "description": "SQL Server索引Hint(WITH(NOLOCK)/INDEX(idx))在DWS中不支持",
        "source_pattern": "SELECT * FROM t WITH (NOLOCK) / WITH (INDEX(idx))",
        "target_solution": "移除NOLOCK(DWS无脏读); 索引提示不支持",
        "compatible": False,
        "note": "DWS不支持锁Hint和索引Hint",
        "migration_difficulty": "中",
        "migration_suggestion": "移除WITH(NOLOCK)(DWS MVCC无脏读问题); 索引提示通过统计信息优化"
    },
    {
        "id": "MSSQL-PERF-002", "name": "分布键选择建议",
        "severity": "warning", "score_deduction": 4,
        "description": "SQL Server无分布键概念，DWS需每表指定",
        "compatible": True,
        "note": "SQL Server主键/聚集索引列是好的分布键候选",
        "migration_difficulty": "高",
        "migration_suggestion": "分析JOIN模式，选择高频关联列作为分布键"
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
