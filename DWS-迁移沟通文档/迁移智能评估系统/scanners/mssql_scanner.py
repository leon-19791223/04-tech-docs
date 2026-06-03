"""SQL Server 源端扫描器

支持从调研数据或样本数据采集SQL Server元数据
"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class MSSQLScanner(BaseScanner):
    """SQL Server 扫描器"""

    def __init__(self, metadata: dict = None):
        super().__init__(source_type="mssql")
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
        """返回典型SQL Server客户样本数据"""
        return MigrationMetadata(
            db_version="SQL Server 2019 Enterprise",
            kernel_version="15.0.2000.5",
            cluster_scale="AlwaysOn: 2节点 + 1监听器",
            hardware_info="主节点: 32Core 128G; 备节点: 32Core 128G; 共享存储: All-Flash 5TB",
            total_capacity="5TB",
            table_count=2000,
            view_count=400,
            function_count=600,
            sequence_count=50,
            schema_count=20,
            user_count=60,
            database_count=15,
            partition_table_count=300,
            compression_table_count=500,
            has_realtime_data=True,
            udf_languages={
                "tsql": 600,
            },
            data_types_used=[
                "INT", "BIGINT", "VARCHAR", "NVARCHAR", "DATETIME",
                "DATETIME2", "DECIMAL", "MONEY", "UNIQUEIDENTIFIER",
                "XML", "VARBINARY", "BIT",
            ],
            etl_tool="SSIS 2019 + Kettle",
            etl_task_count=400,
            source_db_types="SQL Server, Oracle, 文件系统",
            source_system_count=8,
            scheduler_tool="SQL Server Agent + TaskCTL",
            scheduler_task_count=600,
            scheduler_frequency="每日凌晨批量 + 每小时增量",
            api_tool="SQL Server REST API + 自研接口",
            api_count=120,
            app_count=4,
            bi_tools=["SSRS", "Power BI", "FineReport"],
            # 补充字段
            security_model="SQL Server RBAC + Schema权限分离",
            encryption_method="TDE + Always Encrypted + 列级加密",
            audit_capability="SQL Server Audit",
            tls_version="TLS 1.2",
            uses_filesystem_access=False,
            uses_lbac=False,
            has_superuser_privileges=True,
            source_charset="Chinese_PRC_CI_AS",
            has_multibyte_chars=True,
            collation_name="Chinese_PRC_CI_AS",
            jdbc_driver_version="Microsoft JDBC Driver 9.x",
            connection_pool="HikariCP + Druid",
            orm_framework="Entity Framework + MyBatis",
            app_language=".NET + Java",
            default_isolation_level="READ COMMITTED",
            supports_xa=True,
            lock_timeout_seconds=-1,
            has_long_transactions=True,
            uses_autonomous_transaction=False,
            cdc_tool="SQL Server CDC + Replication",
            has_cdc_active=True,
            daily_data_growth_gb=10.0,
            max_table_size_gb=600.0,
            has_data_skew=False,
            workload_type="混合(OLTP+OLAP)",
            peak_concurrent_queries=300,
            avg_query_response_seconds=1.5,
        )
