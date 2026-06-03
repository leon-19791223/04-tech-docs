"""SQL Server -> DWS 扩展/功能兼容性规则"""

EXTENSION_RULES = [
    {
        "id": "MSSQL-EXT-001", "name": "SQL Server CLR集成",
        "severity": "error", "score_deduction": 8,
        "extension": "CLR Integration",
        "compatible": False,
        "note": "SQL Server CLR集成(.NET代码在数据库内运行)在DWS中不支持",
        "alternative": "将CLR存储过程/函数逻辑迁移到应用层或使用plpgsql/Java UDF重写",
        "migration_difficulty": "高",
        "migration_suggestion": "1) CLR函数->plpgsql重写; 2) 外部API调用->应用层处理; 3) 复杂逻辑->Java UDF(FGC)"
    },
    {
        "id": "MSSQL-EXT-002", "name": "SQL Server Linked Server",
        "severity": "error", "score_deduction": 6,
        "extension": "Linked Server",
        "compatible": False,
        "note": "SQL Server Linked Server跨库查询在DWS中使用FDW(外部表)替代",
        "alternative": "DWS支持Foreign Data Wrapper(FDW): CREATE FOREIGN TABLE ... SERVER ...",
        "migration_difficulty": "中",
        "migration_suggestion": "Linked Server查询改为DWS外部表(FDW): 1)创建SERVER; 2)创建FOREIGN TABLE; 3)通过SQL访问"
    },
    {
        "id": "MSSQL-EXT-003", "name": "SQL Server Service Broker",
        "severity": "error", "score_deduction": 8,
        "extension": "Service Broker",
        "compatible": False,
        "note": "SQL Server Service Broker(异步消息队列)在DWS中不支持",
        "alternative": "使用独立消息中间件(Kafka/RabbitMQ)替代",
        "migration_difficulty": "高",
        "migration_suggestion": "Service Broker消息队列迁移到Kafka/RabbitMQ; DWS专注数据存储和分析"
    },
    {
        "id": "MSSQL-EXT-004", "name": "SQL Server Full-Text Search",
        "severity": "error", "score_deduction": 6,
        "extension": "Full-Text Search",
        "compatible": False,
        "note": "SQL Server全文索引在DWS中有限支持",
        "alternative": "简单文本搜索使用ILIKE; 复杂搜索集成Elasticsearch",
        "migration_difficulty": "高",
        "migration_suggestion": "1)简单LIKE模式->ILIKE; 2)全文查询->Elasticsearch; 3)混合查询->DWS+ES联合方案"
    },
    {
        "id": "MSSQL-EXT-005", "name": "SQL Server Policy-Based Management",
        "severity": "info", "score_deduction": 0,
        "extension": "Policy-Based Management",
        "compatible": True,
        "note": "功能对等，DWS使用数据库配置参数+安全策略实现",
        "migration_difficulty": "低"
    },
    {
        "id": "MSSQL-EXT-006", "name": "SQL Server Change Tracking / Change Data Capture",
        "severity": "warning", "score_deduction": 3,
        "extension": "Change Tracking / CDC",
        "compatible": True,
        "note": "DWS不支持CDC但可通过DRS或第三方工具实现增量同步",
        "alternative": "华为DRS / Debezium + Kafka + Flink → DWS",
        "migration_difficulty": "中",
        "migration_suggestion": "使用华为DRS实现SQL Server→DWS全量+增量同步; CDC表清理策略需在DRS中配置"
    },
    {
        "id": "MSSQL-EXT-007", "name": "SQL Server SQLCLR (自定义类型/聚合)",
        "severity": "error", "score_deduction": 6,
        "extension": "SQLCLR",
        "compatible": False,
        "note": "SQL Server SQLCLR支持自定义类型和聚合函数，DWS不支持",
        "alternative": "自定义类型用DWS复合类型或JSONB; 自定义聚合用plpgsql + CREATE AGGREGATE",
        "migration_difficulty": "高",
        "migration_suggestion": "1)自定义类型->DWS复合类型(CREATE TYPE); 2)自定义聚合->CREATE AGGREGATE + plpgsql; 3) 复杂逻辑迁移到应用层"
    },
    {
        "id": "MSSQL-EXT-008", "name": "SQL Server Data Encryption (Always Encrypted)",
        "severity": "error", "score_deduction": 6,
        "extension": "Always Encrypted",
        "compatible": False,
        "note": "SQL Server Always Encrypted应用层加密在DWS中需使用不同方案",
        "alternative": "DWS支持集群级TDE(华为云KMS) + pgcrypto扩展(列级加密)",
        "migration_difficulty": "高",
        "migration_suggestion": "Always Encrypted列: 1)解密数据; 2)使用TDE代替库级加密; 3)列级敏感数据使用pgcrypto加密函数"
    },
]
