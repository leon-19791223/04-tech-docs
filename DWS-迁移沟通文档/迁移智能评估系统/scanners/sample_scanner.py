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

        return meta
