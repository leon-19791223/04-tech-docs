"""Teradata 源端扫描器"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class TeradataScanner(BaseScanner):
    """Teradata 扫描器"""

    def __init__(self, metadata: dict = None):
        super().__init__(source_type="teradata")
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
        return MigrationMetadata(
            db_version="Teradata 16.20",
            kernel_version="16.20.xx.xx",
            cluster_scale="4节点 (2+2 AMP集群)",
            hardware_info="节点: 32Core/256G; 存储: All-Flash 5TB",
            total_capacity="15TB",
            table_count=3200,
            view_count=900,
            function_count=200,
            sequence_count=0,
            schema_count=150,
            user_count=60,
            database_count=10,
            partition_table_count=800,
            compression_table_count=600,
            has_realtime_data=True,
            udf_languages={
                "sql": 150,
                "stored_proc": 50,
            },
            data_types_used=[
                "INTEGER", "BIGINT", "SMALLINT", "BYTEINT", "DECIMAL",
                "CHAR", "VARCHAR", "CLOB", "BLOB", "VARBYTE",
                "DATE", "TIMESTAMP", "PERIOD",
            ],
            etl_tool="Teradata FastExport + Kettle",
            etl_task_count=400,
            source_db_types="Teradata, Oracle",
            source_system_count=6,
            scheduler_tool="Teradata Viewpoint",
            scheduler_task_count=600,
            scheduler_frequency="每日批量",
            api_tool="",
            api_count=0,
            app_count=2,
            bi_tools=["Tableau", "FineReport"],
        )
