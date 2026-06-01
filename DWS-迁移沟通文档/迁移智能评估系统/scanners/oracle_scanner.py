"""Oracle 源端扫描器

支持从调研数据或样本数据采集Oracle元数据
"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class OracleScanner(BaseScanner):
    """Oracle 扫描器"""

    def __init__(self, metadata: dict = None):
        super().__init__(source_type="oracle")
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
        """返回典型Oracle客户样本数据"""
        return MigrationMetadata(
            db_version="Oracle 19c Enterprise Edition",
            kernel_version="19.0.0.0.0",
            cluster_scale="2节点 RAC + 1台备库",
            hardware_info="RAC: 2*32Core 256G; 存储: All-Flash 10TB",
            total_capacity="8TB",
            table_count=1800,
            view_count=600,
            function_count=450,
            sequence_count=300,
            schema_count=35,
            user_count=80,
            database_count=5,
            partition_table_count=500,
            compression_table_count=300,
            has_realtime_data=True,
            udf_languages={
                "plsql": 450,       # 存储过程+函数
                "java": 20,         # Java存储过程
            },
            data_types_used=[
                "VARCHAR2", "NUMBER", "DATE", "CLOB", "BLOB",
                "TIMESTAMP", "CHAR", "NVARCHAR2", "RAW", "XMLTYPE"
            ],
            etl_tool="Kettle 8.x + Oracle GoldenGate",
            etl_task_count=500,
            source_db_types="Oracle, 文件系统",
            source_system_count=8,
            scheduler_tool="TaskCTL + DBMS_SCHEDULER",
            scheduler_task_count=800,
            scheduler_frequency="每日凌晨批量 + 近实时(OGG)",
            api_tool="Oracle ORDS + 自研接口",
            api_count=150,
            app_count=3,
            bi_tools=["FineReport 10.x", "Tableau"],
        )
