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
