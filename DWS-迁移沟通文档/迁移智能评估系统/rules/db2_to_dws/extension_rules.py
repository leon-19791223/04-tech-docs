"""DB2 -> DWS 扩展/功能兼容性规则"""

EXTENSION_RULES = [
    {
        "id": "DB2-EXT-001", "name": "DB2 Text Search",
        "severity": "error", "score_deduction": 6,
        "extension": "DB2 Text Search",
        "compatible": False,
        "note": "DB2 Text Search全文检索在DWS中有限支持",
        "alternative": "简单搜索使用ILIKE; 复杂全文搜索集成Elasticsearch",
        "migration_difficulty": "高",
        "migration_suggestion": "1)简单文本匹配->ILIKE; 2)全文索引需求->Elasticsearch; 3)混合方案->DWS+ES联合查询"
    },
    {
        "id": "DB2-EXT-002", "name": "DB2 Spatial Extender",
        "severity": "error", "score_deduction": 8,
        "extension": "DB2 Spatial Extender",
        "compatible": False,
        "note": "DB2空间数据类型和函数在DWS中不支持原生空间功能",
        "alternative": "DWS PostGIS扩展(基本空间功能) / JSONB存储坐标",
        "migration_difficulty": "高",
        "migration_suggestion": "DB2空间函数: 1)检查使用的具体空间函数; 2)基础空间功能使用DWS PostGIS扩展; 3)复杂空间计算在应用层实现"
    },
    {
        "id": "DB2-EXT-003", "name": "DB2 Net Search Extender",
        "severity": "error", "score_deduction": 7,
        "extension": "Net Search Extender",
        "compatible": False,
        "note": "DB2 Net Search Extender(网络搜索)在DWS中不支持",
        "alternative": "使用Elasticsearch或ILIKE替代",
        "migration_difficulty": "高",
        "migration_suggestion": "1)简单搜索->ILIKE; 2)高级搜索->Elasticsearch; 3)存储过程内搜索逻辑->应用层改造"
    },
    {
        "id": "DB2-EXT-004", "name": "DB2 Federation / Homogenous Federation",
        "severity": "error", "score_deduction": 6,
        "extension": "DB2 Federation",
        "compatible": False,
        "note": "DB2 Federation(跨库联邦查询)在DWS中使用FDW替代",
        "alternative": "DWS支持Foreign Data Wrapper: CREATE FOREIGN TABLE ... SERVER ...",
        "migration_difficulty": "中",
        "migration_suggestion": "DB2 Federation查询改为DWS外部表: 1)创建SERVER; 2)创建FOREIGN TABLE映射; 3)通过SQL直接查询"
    },
    {
        "id": "DB2-EXT-005", "name": "DB2 Replication Center",
        "severity": "error", "score_deduction": 5,
        "extension": "Replication Center",
        "compatible": False,
        "note": "DB2 Replication Center(复制管理)在DWS中使用DRS替代",
        "alternative": "华为DRS / GDS并行导入 / OBS外表导入",
        "migration_difficulty": "中",
        "migration_suggestion": "DB2复制任务: 迁移前使用DRS全量+增量同步; 迁移后通过ETL调度同步"
    },
    {
        "id": "DB2-EXT-006", "name": "DB2 BLU Acceleration (内存计算)",
        "severity": "error", "score_deduction": 6,
        "extension": "BLU Acceleration",
        "compatible": False,
        "note": "DB2 BLU列存储引擎+内存计算在DWS中使用列存+MPP并行替代",
        "alternative": "DWS列存表(ORIENTATION=COLUMN) + 内存参数优化",
        "migration_difficulty": "中",
        "migration_suggestion": "BLU优化的表改为DWS列存表: WITH (ORIENTATION=COLUMN, COMPRESSION=HIGH); 大查询通过query_dop参数开启并行"
    },
    {
        "id": "DB2-EXT-007", "name": "DB2 Warehouse (OLAP分析)",
        "severity": "info", "score_deduction": 0,
        "extension": "DB2 Warehouse",
        "compatible": True,
        "note": "DB2 Warehouse的分析功能在DWS中原生支持，DWS本身就是MPP数据仓库",
        "migration_difficulty": "低"
    },
    {
        "id": "DB2-EXT-008", "name": "DB2 pureXML",
        "severity": "error", "score_deduction": 8,
        "extension": "pureXML",
        "compatible": False,
        "note": "DB2 pureXML原生XML存储和XQuery查询在DWS中不支持",
        "alternative": "XML转为JSON/JSONB; 改为SQL查询; 应用层解析XML",
        "migration_difficulty": "高",
        "migration_suggestion": "1)仅存储: XML->TEXT; 2)需结构化查询: XML->JSON/JSONB; 3)XQuery查询->应用层解析; 4)XML索引->JSONB GIN索引"
    },
    {
        "id": "DB2-EXT-009", "name": "DB2 Instance Configuration (db2set/db2conf)",
        "severity": "info", "score_deduction": 0,
        "extension": "DB2 Instance Config",
        "compatible": True,
        "note": "DB2实例配置参数需在DWS中对应设置(参数名和值不同)",
        "migration_difficulty": "低",
        "migration_suggestion": "核心DB2配置参数(缓冲池大小/排序内存等)映射到DWS的GUC参数"
    },
]
