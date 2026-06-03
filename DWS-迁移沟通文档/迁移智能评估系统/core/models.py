"""
通用数据模型
所有迁移场景共享的数据结构定义
"""

from dataclasses import dataclass, field
from typing import Optional


# ================================================================
# 源端元数据基类
# ================================================================
@dataclass
class MigrationMetadata:
    """源端数据库元数据（所有数据库通用）"""
    # 基本信息
    db_version: str = ""
    kernel_version: str = ""
    cluster_scale: str = ""
    hardware_info: str = ""
    total_capacity: str = ""

    # 对象统计
    table_count: int = 0
    view_count: int = 0
    function_count: int = 0
    sequence_count: int = 0
    schema_count: int = 0
    user_count: int = 0
    database_count: int = 0
    partition_table_count: int = 0
    compression_table_count: int = 0
    has_realtime_data: bool = False

    # UDF语言分布  e.g. {"plpgsql": 500, "plpythonu": 18}
    udf_languages: dict = field(default_factory=dict)
    # 数据类型使用情况
    data_types_used: list = field(default_factory=list)

    # ETL
    etl_tool: str = ""
    etl_task_count: int = 0
    source_db_types: str = ""
    source_system_count: int = 0

    # 调度
    scheduler_tool: str = ""
    scheduler_task_count: int = 0
    scheduler_frequency: str = ""

    # 数据服务
    api_tool: str = ""
    api_count: int = 0

    # BI/应用层
    app_count: int = 0
    bi_tools: list = field(default_factory=list)

    # ============================================================
    # 新增字段: 安全与权限
    # ============================================================
    security_model: str = ""           # 安全模型描述 e.g. "RBAC + 行级安全"
    encryption_method: str = ""        # 加密方式 e.g. "TDE / 列级加密 / 无"
    audit_capability: str = ""         # 审计能力 e.g. "细粒度审计 / 基本日志"
    tls_version: str = ""              # TLS版本 e.g. "TLS 1.2"
    uses_filesystem_access: bool = False  # 是否使用文件系统访问功能
    uses_lbac: bool = False             # 是否使用行级安全标签
    has_superuser_privileges: bool = True  # 是否有超级用户权限

    # ============================================================
    # 新增字段: 字符集与编码
    # ============================================================
    source_charset: str = ""           # 源库字符集 e.g. "GBK / UTF-8 / AL32UTF8"
    target_charset: str = "UTF-8"      # 目标库字符集
    has_multibyte_chars: bool = True    # 是否含多字节字符(中文/日文等)
    collation_name: str = ""           # 排序规则名称

    # ============================================================
    # 新增字段: 应用层
    # ============================================================
    jdbc_driver_version: str = ""      # JDBC驱动版本
    connection_pool: str = ""          # 连接池 e.g. "HikariCP / Druid / DBCP"
    orm_framework: str = ""            # ORM框架 e.g. "MyBatis / Hibernate / EF"
    app_language: str = ""             # 应用语言 e.g. "Java / .NET / Python"

    # ============================================================
    # 新增字段: 事务与并发
    # ============================================================
    default_isolation_level: str = ""  # 默认隔离级别 e.g. "READ COMMITTED"
    supports_xa: bool = False          # 是否支持XA分布式事务
    lock_timeout_seconds: int = 0      # 锁超时时间(秒)
    has_long_transactions: bool = False  # 是否有长事务
    uses_autonomous_transaction: bool = False  # 是否使用自治事务

    # ============================================================
    # 新增字段: CDC与增量同步
    # ============================================================
    cdc_tool: str = ""                 # CDC工具 e.g. "DB2 CDC / Oracle GoldenGate / Canal"
    has_cdc_active: bool = False       # 是否已启用CDC
    daily_data_growth_gb: float = 0.0  # 日均数据增长(GB)
    max_table_size_gb: float = 0.0     # 最大表大小(GB)

    # ============================================================
    # 新增字段: 性能
    # ============================================================
    has_data_skew: bool = False        # 是否存在数据倾斜
    workload_type: str = ""            # 负载类型 e.g. "OLAP / OLTP / 混合"
    peak_concurrent_queries: int = 0   # 峰值并发查询数
    avg_query_response_seconds: float = 0.0  # 平均查询响应时间(秒)

    # ============================================================
    # 新增字段: 架构全视角
    # ============================================================
    # 逻辑架构
    logical_layers: str = ""          # 分层 e.g. "ODS→EDW→DM→APP"
    data_model_type: str = ""         # 数据模型 e.g. "3NF / 星型 / 雪花"
    has_logical_data_model: bool = False  # 是否有独立LDM

    # 物理架构
    source_platform: str = ""         # 源平台类型 e.g. "Oracle Exadata / 一体机 / 自建"
    storage_type: str = ""            # 存储类型 e.g. "全闪存 / SAS / 混合"
    network_bandwidth_gbps: int = 0   # 网络带宽
    has_standby: bool = False         # 是否有灾备库

    # 应用架构
    app_systems_count: int = 0        # 依赖的应用系统数
    report_count: int = 0             # 报表数量
    data_file_outputs: int = 0        # 对外数据文件输出数
    has_realtime_api: bool = False    # 是否有实时API接口

    # 运维架构
    monitoring_tool: str = ""         # 监控工具
    backup_strategy: str = ""         # 备份策略 e.g. "每日全量 / 增量"
    ops_team_size: int = 0            # 运维团队规模
    has_runbook: bool = False         # 是否有运维手册


# ================================================================
# 兼容性检查结果
# ================================================================
@dataclass
class CheckResult:
    """单条规则检查结果"""
    rule_id: str = ""
    name: str = ""
    category: str = ""
    severity: str = "info"       # info / warning / error
    compatible: bool = True
    score_deduction: int = 0
    description: str = ""
    source_pattern: str = ""     # 源端特征
    target_solution: str = ""    # 目标端解决方案
    note: str = ""
    migration_difficulty: str = ""  # 低 / 中 / 高
    suggestion: str = ""


@dataclass
class CategoryResult:
    """分类检查结果"""
    category: str = ""
    category_name: str = ""
    total_rules: int = 0
    passed: int = 0
    warnings: int = 0
    errors: int = 0
    max_score: int = 100
    actual_score: int = 100
    deduction: int = 0
    weight: int = 0
    weighted_score: float = 0.0
    details: list = field(default_factory=list)


@dataclass
class AssessmentResult:
    """完整评估结果"""
    # 基本信息
    source_type: str = ""        # "gp", "oracle", "mysql" ...
    target_type: str = ""        # "dws", "hologres" ...
    db_version: str = ""
    kernel_version: str = ""
    cluster_scale: str = ""
    total_capacity: str = ""
    table_count: int = 0
    view_count: int = 0
    function_count: int = 0
    partition_table_count: int = 0
    udf_languages: dict = field(default_factory=dict)
    etl_tool: str = ""
    scheduler_tool: str = ""
    bi_tools: list = field(default_factory=list)

    # 评分
    overall_score: float = 0.0
    risk_level: str = ""         # 低 / 中 / 高
    category_results: list = field(default_factory=list)

    # 关键发现
    critical_issues: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    workload_estimate: dict = field(default_factory=dict)
    estimated_phases: dict = field(default_factory=dict)

    # 扩展输出
    capacity_planning: dict = field(default_factory=dict)  # 容量规划建议
    batch_strategy: dict = field(default_factory=dict)     # 分批迁移策略
    competitor_compare: dict = field(default_factory=dict)  # 竞品对比
