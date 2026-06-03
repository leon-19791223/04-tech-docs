"""MySQL -> DWS 扩展/插件兼容性规则"""

EXTENSION_RULES = [
    {
        "id": "MYSQL-EXT-001", "name": "MySQL HeatWave (OLAP加速)",
        "severity": "error", "score_deduction": 8,
        "extension": "HeatWave",
        "compatible": False,
        "note": "HeatWave是MySQL专用OLAP加速引擎，DWS中无直接等效",
        "alternative": "DWS MPP架构原生支持OLAP加速，无需安装额外插件",
        "migration_difficulty": "低",
        "migration_suggestion": "HeatWave加速的查询迁移到DWS后直接执行即可；DWS的列存+MPP架构本身即为OLAP设计"
    },
    {
        "id": "MYSQL-EXT-002", "name": "MySQL Document Store / X Plugin",
        "severity": "error", "score_deduction": 6,
        "extension": "X Plugin / Document Store",
        "compatible": False,
        "note": "MySQL X Plugin支持NoSQL文档存储接口，DWS不支持",
        "alternative": "DWS支持JSON/JSONB类型存储文档数据，需通过SQL操作",
        "migration_difficulty": "中",
        "migration_suggestion": "1) X Plugin NoSQL API需改为通过PostgreSQL JDBC使用SQL; 2) Collection->JSONB表; 3) X DevAPI改为应用层SDK"
    },
    {
        "id": "MYSQL-EXT-003", "name": "MySQL Group Replication",
        "severity": "warning", "score_deduction": 4,
        "extension": "Group Replication",
        "compatible": False,
        "note": "MySQL Group Replication是MySQL高可用方案，DWS集群HA机制不同",
        "alternative": "DWS使用集群级HA(Manager节点+数据多副本+AZ容灾)，无需Group Replication",
        "migration_difficulty": "低",
        "migration_suggestion": "DWS原生支持集群HA，无需迁移Group Replication配置"
    },
    {
        "id": "MYSQL-EXT-004", "name": "MySQL memcached插件",
        "severity": "error", "score_deduction": 5,
        "extension": "memcached",
        "compatible": False,
        "note": "MySQL memcached插件提供Key-Value缓存接口，DWS不支持",
        "alternative": "缓存需求建议使用独立缓存服务(Redis/Memcached)，与DWS分离",
        "migration_difficulty": "低",
        "migration_suggestion": "将K-V缓存需求迁移到Redis; DWS专注分析型查询"
    },
    {
        "id": "MYSQL-EXT-005", "name": "MySQL Thread Pool插件",
        "severity": "info", "score_deduction": 0,
        "extension": "Thread Pool",
        "compatible": True,
        "note": "DWS通过资源池(Resource Pool)+workload管理实现连接管理，功能对等",
        "migration_difficulty": "低"
    },
    {
        "id": "MYSQL-EXT-006", "name": "MySQL Enterprise Audit / Firewall",
        "severity": "warning", "score_deduction": 3,
        "extension": "Enterprise Audit / Firewall",
        "compatible": True,
        "note": "DWS支持AUDIT和数据库安全策略，功能对等但配置方式不同",
        "migration_difficulty": "中",
        "migration_suggestion": "DWS使用AUDIT POLICY审计，安全策略通过行级安全(RLS)实现"
    },
    {
        "id": "MYSQL-EXT-007", "name": "MySQL Keyring(加密密钥管理)",
        "severity": "warning", "score_deduction": 3,
        "extension": "Keyring",
        "compatible": True,
        "note": "DWS使用华为云KMS服务管理密钥，功能对等",
        "alternative": "华为云KMS + DWS TDE集群级加密",
        "migration_difficulty": "中",
        "migration_suggestion": "将Keyring密钥迁移到华为云KMS; DWS集群启用TDE"
    },
    {
        "id": "MYSQL-EXT-008", "name": "MySQL Event Scheduler",
        "severity": "error", "score_deduction": 5,
        "extension": "Event Scheduler",
        "compatible": False,
        "note": "MySQL Event Scheduler定时任务在DWS中需使用外部调度工具",
        "alternative": "DolphinScheduler / TaskCTL 替代",
        "migration_difficulty": "中",
        "migration_suggestion": "MySQL Event迁移到DolphinScheduler: 分析事件逻辑->创建DWS SQL任务->配置调度周期"
    },
]
