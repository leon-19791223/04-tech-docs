"""MySQL 源端扫描器

支持从调研数据或样本数据采集MySQL元数据
"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class MySQLScanner(BaseScanner):
    """MySQL 扫描器"""

    def __init__(self, metadata: dict = None):
        super().__init__(source_type="mysql")
        self._custom_data = metadata or {}

    def scan(self) -> MigrationMetadata:
        meta = MigrationMetadata()
        for k, v in self._custom_data.items():
            if hasattr(meta, k):
                setattr(meta, k, v)

        if not self._custom_data:
            return self._sample_data()
        return meta

    @staticmethod
    def _sample_data() -> MigrationMetadata:
        """返回典型MySQL客户样本数据"""
        return MigrationMetadata(
            db_version="MySQL 8.0.32",
            kernel_version="InnoDB",
            cluster_scale="主从复制: 1主2从",
            hardware_info="主库: 16Core 64G SSD 1TB; 从库: 16Core 64G SSD 1TB",
            total_capacity="2TB",
            table_count=1200,
            view_count=80,
            function_count=200,
            sequence_count=0,
            schema_count=8,
            user_count=30,
            database_count=12,
            partition_table_count=150,
            compression_table_count=0,
            has_realtime_data=True,
            udf_languages={
                "sql": 200,
            },
            data_types_used=[
                "INT", "BIGINT", "VARCHAR", "TEXT", "DATETIME",
                "TIMESTAMP", "DECIMAL", "JSON", "ENUM", "BLOB",
            ],
            etl_tool="Kettle 8.x + Canal",
            etl_task_count=300,
            source_db_types="MySQL, Oracle",
            source_system_count=6,
            scheduler_tool="XXL-JOB + MySQL Event",
            scheduler_task_count=500,
            scheduler_frequency="每日凌晨批量 + 实时Canal同步",
            api_tool="自研REST API",
            api_count=80,
            app_count=3,
            bi_tools=["FineReport 10.x", "Metabase"],
        )
