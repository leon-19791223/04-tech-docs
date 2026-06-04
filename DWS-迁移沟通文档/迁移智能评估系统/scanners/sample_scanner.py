"""通用样本数据扫描器 - 用于演示或模板解析失败时回退"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class SampleScanner(BaseScanner):
    """返回内置样本数据"""

    def __init__(self, source_type: str = "gp", metadata: dict = None):
        super().__init__(source_type=source_type)
        self._custom_data = metadata or {}

    def scan(self) -> MigrationMetadata:
        meta = MigrationMetadata()
        for k, v in self._custom_data.items():
            if hasattr(meta, k):
                setattr(meta, k, v)

        if not self._custom_data:
            meta.db_version = "Greenplum 5.23"
            meta.kernel_version = "PostgreSQL 8.3.23"
            meta.cluster_scale = "2 Master + 6 Segment"
            meta.total_capacity = "35TB"
            meta.table_count = 2700
            meta.view_count = 1100
            meta.function_count = 1300
            meta.partition_table_count = 850
            meta.etl_tool = "Kettle 7.x"
            meta.scheduler_tool = "iControl"
            meta.bi_tools = ["FineReport 9.x"]
            meta.udf_languages = {"plpgsql": 1027, "plpythonu": 18, "plperl": 247}
            # 新增业务场景字段
            meta.business_scenarios = ["BI报表分析", "风控数据报送", "监管报表生成"]
            meta.pain_points = ["IO高导致ETL延迟", "月末结算时性能瓶颈", "扩容成本高"]
            meta.data_source_types = ["Oracle", "文件系统", "Kafka"]
            meta.ingestion_frequency = "每日批量(T+1) + 近实时(Kafka)"
            meta.incremental_data_daily_gb = 50.0
            meta.sample_sql_count = 25
            meta.has_data_link_diagram = True
            meta.network_architecture = "双平面万兆(业务Bond4+管理Bond1)"
            meta.server_hardware = "鲲鹏920 32C/256G + 12*3.84T SSD"

        return meta
