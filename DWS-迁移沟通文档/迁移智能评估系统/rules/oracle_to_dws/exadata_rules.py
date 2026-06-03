"""Oracle Exadata 一体机特有功能兼容性规则

Exadata的特殊功能在迁移到DWS时需特别关注
"""

EXADATA_RULES = [
    {
        "id": "EXA-001", "name": "Smart Scan (智能扫描)",
        "severity": "error", "score_deduction": 8,
        "description": "Exadata Smart Scan将查询条件下推到存储节点执行，DWS不支持",
        "source_pattern": "Oracle Exadata Smart Scan — 存储端谓词过滤/列投影",
        "target_solution": "DWS通过MPP架构的并行扫描+分布键过滤实现类似效果",
        "compatible": False,
        "note": "Smart Scan是Exadata一体机的核心性能特性，在DWS中无需等效功能(MPP架构的计算下推机制不同)",
        "migration_difficulty": "低",
        "migration_suggestion": "DWS的MPP并行架构天然支持数据本地化计算，不需要单独实现Smart Scan。\n迁移后需关注: 1)分布键选择直接影响扫描效率; 2)列存表减少I/O量"
    },
    {
        "id": "EXA-002", "name": "Storage Index (存储索引)",
        "severity": "error", "score_deduction": 6,
        "description": "Exadata Storage Index在存储层自动过滤数据块，DWS无直接等效",
        "source_pattern": "Exadata存储索引 — 自动跳过不符合条件的数据块",
        "target_solution": "DWS依赖分区裁剪(Partition Pruning)和列存min/max统计信息实现类似跳过扫描",
        "compatible": False,
        "note": "DWS的列存表自动维护每一列的min/max值，查询时自动跳过不符合条件的数据块",
        "migration_difficulty": "低",
        "migration_suggestion": "设计合理的分区策略(时间/地区等维度)，充分利用分区裁剪;\n事实表使用列存表，利用min/max跳过扫描提升性能"
    },
    {
        "id": "EXA-003", "name": "Hybrid Columnar Compression (HCC)",
        "severity": "error", "score_deduction": 6,
        "description": "Exadata HCC混合列压缩在DWS中使用列存压缩替代",
        "source_pattern": "COMPRESS FOR QUERY HIGH / COMPRESS FOR ARCHIVE HIGH",
        "target_solution": "DWS使用列存表 + COMPRESSION=MIDDLE/HIGH 参数控制压缩比",
        "compatible": False,
        "note": "HCC是Exadata独有的存储级压缩，DWS列存压缩达到类似效果但算法和压缩比不同",
        "migration_difficulty": "低",
        "migration_suggestion": "QUERY HIGH -> ORIENTATION=COLUMN, COMPRESSION=MIDDLE;\nARCHIVE HIGH -> ORIENTATION=COLUMN, COMPRESSION=HIGH"
    },
    {
        "id": "EXA-004", "name": "Exadata Flash Cache",
        "severity": "warning", "score_deduction": 3,
        "description": "Exadata智能闪存缓存在DWS中使用DWS本地缓存+OBS分层",
        "source_pattern": "Exadata闪存缓存 — 自动缓存热数据",
        "target_solution": "DWS使用节点本地SSD做热数据缓存 + OBS对象存储做冷数据分层",
        "compatible": True,
        "note": "功能对等，实现机制不同。DWS支持冷热数据分层策略",
        "migration_difficulty": "低",
        "migration_suggestion": "热数据(3个月内): 列存表+DWS本地缓存;\n冷数据(3个月以上): OBS外表存储"
    },
    {
        "id": "EXA-005", "name": "Exadata IORM (I/O资源管理)",
        "severity": "error", "score_deduction": 5,
        "description": "Exadata IORM在存储层管理I/O优先级，DWS使用workload级别资源管理",
        "source_pattern": "IORM — 数据库/用户/会话级别I/O资源管理",
        "target_solution": "DWS通过资源池(Resource Pool)+workload级别参数管理查询优先级",
        "compatible": False,
        "note": "功能对等但实现方式不同: IORM在存储层控制，DWS在计算层控制",
        "migration_difficulty": "中",
        "migration_suggestion": "使用DWS资源管理功能: CREATE RESOURCE POOL + 关联用户;\n需要根据业务优先级重新设计资源池划分"
    },
    {
        "id": "EXA-006", "name": "Exadata AWR/SQL Monitor",
        "severity": "info", "score_deduction": 0,
        "description": "Exadata AWR性能报告在DWS中使用CloudEye/DAS替代",
        "compatible": True,
        "note": "功能对等，换成DWS的通用性能监控工具"
    },
    {
        "id": "EXA-007", "name": "Exadata特性依赖评估(总体)",
        "severity": "warning", "score_deduction": 5,
        "description": "Exadata深度依赖的应用(利用了Smart Scan/Storage Index进行性能优化)需评估迁移后性能",
        "compatible": True,
        "note": "应用若深度依赖Exadata特有特性，在POC阶段必须进行详细的性能对比测试",
        "migration_difficulty": "高",
        "migration_suggestion": "1) 选取5-10个代表性复杂SQL对比执行计划;\n2) 在DWS上执行全量性能回归测试;\n3) 关注SQL执行时间差异，针对性优化分布键"
    },
]
