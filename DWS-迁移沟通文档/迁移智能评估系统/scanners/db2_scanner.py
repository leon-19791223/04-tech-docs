"""DB2 LUW 源端扫描器

支持从调研数据或样本数据采集DB2元数据
基于DB2_DWS_迁移解决方案_证券基金资管行业_展开版 中的行业数据特征
"""

from core.models import MigrationMetadata
from scanners.base import BaseScanner


class DB2Scanner(BaseScanner):
    """DB2 LUW 扫描器"""

    def __init__(self, metadata: dict = None):
        super().__init__(source_type="db2")
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
        """返回典型证券基金行业DB2客户样本数据"""
        return MigrationMetadata(
            db_version="IBM DB2 LUW 11.5",
            kernel_version="DB2 v11.5.8",
            cluster_scale="PureScale: 2节点 + HADR备库",
            hardware_info="主节点: 32Core 256G; 备节点: 32Core 256G; 全闪存储: 10TB",
            total_capacity="8TB",
            table_count=2500,
            view_count=800,
            function_count=600,
            sequence_count=200,
            schema_count=30,
            user_count=50,
            database_count=10,
            partition_table_count=400,
            compression_table_count=600,
            has_realtime_data=True,
            udf_languages={
                "sql_pl": 600,  # SQL PL 存储过程是DB2最大迁移工作量
            },
            data_types_used=[
                "INTEGER", "BIGINT", "DECIMAL", "VARCHAR", "CHAR",
                "CLOB", "BLOB", "XML", "TIMESTAMP", "DATE",
                "GRAPHIC", "VARGRAPHIC", "REAL", "DOUBLE",
            ],
            etl_tool="IBM DataStage + Kettle",
            etl_task_count=350,
            source_db_types="DB2, Oracle, 文件系统",
            source_system_count=10,
            scheduler_tool="TWS (Tivoli) + DB2 Task Scheduler",
            scheduler_task_count=700,
            scheduler_frequency="每日凌晨批量 + 每15分钟增量",
            api_tool="DB2 REST API + 自研接口",
            api_count=100,
            app_count=3,
            bi_tools=["Cognos Analytics", "FineReport", "Tableau"],
            # 补充字段
            security_model="RBAC + LBAC行级安全",
            encryption_method="TDE + 内置加密函数(ENCRYPT/DECRYPT)",
            audit_capability="DB2 AUDIT细粒度审计",
            tls_version="TLS 1.2",
            uses_filesystem_access=True,
            uses_lbac=True,
            has_superuser_privileges=True,
            source_charset="GBK (Code Set 1386)",
            has_multibyte_chars=True,
            collation_name="SYSTEM_814_ZH_CN",
            jdbc_driver_version="DB2 JCC Driver 4.x",
            connection_pool="HikariCP",
            orm_framework="MyBatis + Hibernate",
            app_language="Java",
            default_isolation_level="CS (Cursor Stability)",
            supports_xa=True,
            lock_timeout_seconds=30,
            has_long_transactions=True,
            uses_autonomous_transaction=False,
            cdc_tool="DB2 CDC",
            has_cdc_active=True,
            daily_data_growth_gb=15.0,
            max_table_size_gb=500.0,
            has_data_skew=False,
            workload_type="OLAP",
            peak_concurrent_queries=100,
            avg_query_response_seconds=2.5,
        )
