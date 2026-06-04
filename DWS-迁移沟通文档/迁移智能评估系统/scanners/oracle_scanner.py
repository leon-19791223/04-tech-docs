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
            db_version="Oracle 19c Enterprise Edition (Exadata)",
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
                "plsql": 450,
                "java": 20,
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
            # 架构全视角字段
            logical_layers="ODS→EDW→DM→APP",
            data_model_type="3NF + 星型混合",
            has_logical_data_model=True,
            source_platform="Oracle Exadata 一体机",
            storage_type="全闪存 + 分层存储",
            network_bandwidth_gbps=100,
            has_standby=True,
            app_systems_count=4,
            report_count=440,
            data_file_outputs=50,
            has_realtime_api=True,
            monitoring_tool="Oracle Enterprise Manager + Zabbix",
            backup_strategy="每日全量RMAN + 归档日志",
            ops_team_size=3,
            has_runbook=True,
            # 安全字段
            security_model="RBAC + VPD行级安全",
            encryption_method="TDE (Transparent Data Encryption)",
            audit_capability="Oracle Unified Audit",
            tls_version="TLS 1.2",
            uses_filesystem_access=True,
            uses_lbac=False,
            has_superuser_privileges=True,
            source_charset="AL32UTF8",
            has_multibyte_chars=True,
            collation_name="BINARY",
            jdbc_driver_version="Oracle JDBC Thin Driver 19.x",
            connection_pool="HikariCP + UCP",
            orm_framework="MyBatis + Hibernate",
            app_language="Java",
            default_isolation_level="READ COMMITTED",
            supports_xa=True,
            lock_timeout_seconds=0,
            has_long_transactions=True,
            uses_autonomous_transaction=True,
            cdc_tool="Oracle GoldenGate + LogMiner",
            has_cdc_active=True,
            daily_data_growth_gb=20.0,
            max_table_size_gb=800.0,
            has_data_skew=True,
            workload_type="OLAP",
            peak_concurrent_queries=200,
            avg_query_response_seconds=3.0,
            # 新增业务场景字段
            business_scenarios=["监管报表报送", "风控指标计算", "客户信息披露"],
            pain_points=["Exadata一体机扩容成本高", "月末跑批窗口紧张", "信创合规要求"],
            data_source_types=["Oracle", "MySQL", "文件系统", "MQ"],
            ingestion_frequency="每日批量 + OGG实时同步",
            incremental_data_daily_gb=20.0,
            sample_sql_count=35,
            has_data_link_diagram=True,
            network_architecture="双平面25GE(业务+管理隔离)",
            server_hardware="Oracle Exadata X8-2 一体机",
        )
