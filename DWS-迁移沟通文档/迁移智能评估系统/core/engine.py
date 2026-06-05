"""
通用迁移分析引擎
与源/目标类型解耦，接收任意元数据+规则集进行分析
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
import importlib
from core.models import (
    MigrationMetadata, AssessmentResult, CategoryResult, CheckResult
)

# 源类型 -> 规则模块路径映射(用于加载UDF_LANGUAGE_MAP等路径自定义配置)
UDF_MODULE_PATHS = {
    "gp": "rules.gp_to_dws", "greenplum": "rules.gp_to_dws",
    "oracle": "rules.oracle_to_dws",
    "mysql": "rules.mysql_to_dws",
    "mssql": "rules.mssql_to_dws", "sqlserver": "rules.mssql_to_dws", "sql_server": "rules.mssql_to_dws",
    "db2": "rules.db2_to_dws", "db2_luw": "rules.db2_to_dws",
}


def get_udf_language_map(source_type: str) -> dict:
    """从路径的规则模块加载UDF_LANGUAGE_MAP"""
    mod_path = UDF_MODULE_PATHS.get(source_type.lower(), "")
    if not mod_path:
        return {}
    try:
        mod = importlib.import_module(mod_path)
        return getattr(mod, "UDF_LANGUAGE_MAP", {})
    except (ImportError, AttributeError):
        return {}


class MigrationAnalyzer:
    """通用迁移分析引擎

    用法:
        rules = get_rules("gp", "dws")  # 从规则注册表获取
        meta = scanner.scan()           # 从扫描器获取元数据
        analyzer = MigrationAnalyzer(meta, rules)
        result = analyzer.analyze()
    """

    def __init__(self, metadata: MigrationMetadata, rules: dict,
                 category_weights: Optional[dict] = None,
                 source_type: str = "", target_type: str = ""):
        self.metadata = metadata
        self.rules = rules
        self.category_weights = category_weights or {
            "ddl": 25, "data_type": 15, "function": 20,
            "udf_language": 20, "extension": 10,
            "etl_tool": 5, "scheduler": 3, "bi_tool": 2,
        }
        self.source_type = source_type
        self.target_type = target_type

    def analyze(self) -> AssessmentResult:
        """执行完整分析(含容量规划/竞品对比/分批策略)"""
        result = AssessmentResult(
            source_type=self.source_type,
            target_type=self.target_type,
            db_version=self.metadata.db_version,
            kernel_version=self.metadata.kernel_version,
            cluster_scale=self.metadata.cluster_scale,
            total_capacity=self.metadata.total_capacity,
            table_count=self.metadata.table_count,
            view_count=self.metadata.view_count,
            function_count=self.metadata.function_count,
            partition_table_count=self.metadata.partition_table_count,
            udf_languages=self.metadata.udf_languages,
            etl_tool=self.metadata.etl_tool,
            scheduler_tool=self.metadata.scheduler_tool,
            bi_tools=self.metadata.bi_tools,
        )

        total_weighted_score = 0.0
        for category, rules_list in self.rules.items():
            cat_result = self._check_category(category, rules_list)
            result.category_results.append(cat_result)
            total_weighted_score += cat_result.weighted_score

        result.overall_score = round(total_weighted_score, 1)

        if result.overall_score >= 85:
            result.risk_level = "低"
        elif result.overall_score >= 65:
            result.risk_level = "中"
        else:
            result.risk_level = "高"

        result.critical_issues = self._get_critical_issues(result.category_results)
        result.recommendations = self._generate_recommendations(result)
        result.workload_estimate = self._estimate_workload(result)
        result.estimated_phases = self._estimate_phases(result)

        # 容量规划
        from core.capacity_planner import CapacityPlanner
        result.capacity_planning = CapacityPlanner.recommend_config(
            total_capacity=self.metadata.total_capacity,
            workload_type=self.metadata.workload_type,
            peak_concurrent=self.metadata.peak_concurrent_queries,
        )
        # 分批策略
        result.batch_strategy = CapacityPlanner.phase_migration_strategy(
            total_capacity=self.metadata.total_capacity,
            table_count=self.metadata.table_count,
            schema_count=self.metadata.schema_count,
            etl_task_count=self.metadata.etl_task_count,
        )

        # POC测试建议
        from core.poc_planner import PocTestPlanner
        result.poc_recommendations = PocTestPlanner.recommend(
            metadata=self.metadata,
            assessment_result=result,
        )

        return result

    def _check_category(self, category: str, rules: list) -> CategoryResult:
        """检查一个分类下的所有规则"""
        from rules.registry import get_category_name
        cat_result = CategoryResult(
            category=category,
            category_name=get_category_name(category, self.source_type, self.target_type),
            weight=self.category_weights.get(category, 10),
        )

        for rule in rules:
            if not rule.get("compatible", True):
                cat_result.errors += 1
                cat_result.total_rules += 1
                cat_result.details.append(CheckResult(
                    rule_id=rule.get("id", ""),
                    name=rule.get("name", ""),
                    category=category,
                    severity=rule.get("severity", "error"),
                    compatible=False,
                    score_deduction=rule.get("score_deduction", 5),
                    description=rule.get("description") or rule.get("note", ""),
                    source_pattern=rule.get("source_pattern", ""),
                    target_solution=rule.get("target_solution") or rule.get("alternative") or rule.get("migration_suggestion") or rule.get("note", ""),
                    note=rule.get("note", ""),
                    migration_difficulty=rule.get("migration_difficulty", ""),
                    suggestion=rule.get(
                        "migration_suggestion",
                        rule.get("suggestion", "")
                    ),
                ))
            elif rule.get("severity") == "warning":
                cat_result.warnings += 1
                cat_result.total_rules += 1
                cat_result.details.append(CheckResult(
                    rule_id=rule.get("id", ""),
                    name=rule.get("name", ""),
                    category=category,
                    severity="warning",
                    compatible=True,
                    score_deduction=rule.get("score_deduction", 2),
                    description=rule.get("description") or rule.get("note", ""),
                    target_solution=rule.get("target_solution") or rule.get("alternative") or rule.get("migration_suggestion") or rule.get("note", ""),
                    note=rule.get("note", ""),
                    suggestion=rule.get("migration_suggestion", rule.get("suggestion", "")),
                ))
            else:
                cat_result.passed += 1
                cat_result.total_rules += 1

        # 通过率比例评分: passed=100%, warning=50%, error=0%
        total = cat_result.total_rules if cat_result.total_rules > 0 else 1
        effective = cat_result.passed + (cat_result.warnings * 0.5)
        score = round((effective / total) * 100, 1)
        cat_result.max_score = 100
        cat_result.actual_score = score
        cat_result.deduction = 100 - score
        cat_result.weighted_score = score * (cat_result.weight / 100.0)

        return cat_result

    def _get_critical_issues(self, category_results: list) -> list:
        issues = []
        for cat in category_results:
            for d in cat.details:
                if d.severity == "error" and not d.compatible:
                    issues.append({
                        "rule_id": d.rule_id,
                        "name": d.name,
                        "category": cat.category_name,
                        "description": d.description,
                        "solution": d.target_solution,
                        "difficulty": d.migration_difficulty,
                    })
        return issues

    def _generate_recommendations(self, result: AssessmentResult) -> list:
        """生成迁移建议(含安全/字符集/应用层/事务/CDC/性能)"""
        recs = []
        udf = self.metadata.udf_languages
        src = self.source_type
        meta = self.metadata

        # UDF语言建议 — 从路径的UDF_LANGUAGE_MAP动态生成(只输出不兼容或需改造的语言)
        lang_map = get_udf_language_map(src)
        for lang_key, count in udf.items():
            if count <= 0:
                continue
            if lang_key in lang_map:
                target_solution, difficulty = lang_map[lang_key]
                if difficulty in ("高", "中"):
                    recs.append(
                        f"{lang_key}语言函数/存储过程({count}个)需改造: {target_solution} [难度:{difficulty}]"
                    )
            else:
                recs.append(
                    f"{lang_key}语言函数/存储过程({count}个)未在映射表中，需评估并迁移为plpgsql"
                )

        # 自动扫描关键问题，生成特定语法改造建议(不限路径)
        for cat in result.category_results:
            for d in cat.details:
                desc = d.description or ""
                if "CONNECT BY" in desc:
                    recs.append(
                        "CONNECT BY层级查询需改为WITH RECURSIVE递归CTE，"
                        "建议在POC阶段选取5+个复杂查询进行验证"
                    )
                    break
            if any("CONNECT BY" in (dd.description or "") for dd in cat.details):
                break

        # 安全建议
        if meta.uses_filesystem_access:
            recs.append(
                "源库使用了文件系统访问功能(UTL_FILE等)，需将所有文件I/O逻辑迁移到应用层或ETL层，"
                "DWS不支持数据库内文件操作"
            )
        if meta.security_model and "LBAC" in meta.security_model:
            recs.append("源库使用了行级安全标签(LBAC)，需重写为DWS行级安全策略(RLS)")
        if meta.tls_version and meta.tls_version < "TLS 1.2":
            recs.append(f"当前TLS版本({meta.tls_version})低于DWS支持的TLS 1.2，需升级加密配置")

        # 字符集建议
        if meta.source_charset and meta.source_charset.upper() != "UTF-8":
            recs.append(
                f"源库字符集({meta.source_charset})与DWS(UTF-8)不同，"
                f"迁移时需进行编码转换，VARCHAR/TEXT字段长度需按1.5-3倍扩展以防止截断"
            )

        # 应用层建议
        if meta.jdbc_driver_version:
            recs.append(
                f"源端JDBC驱动需从当前版本替换为PostgreSQL JDBC驱动(org.postgresql.Driver)，"
                f"连接URL格式从jdbc:{src}://调整为jdbc:postgresql://"
            )
        if meta.orm_framework:
            recs.append(
                f"ORM框架({meta.orm_framework})需配置对应数据库方言，"
                f"建议在测试环境验证所有CRUD操作和分页查询"
            )

        # 事务建议
        if meta.supports_xa:
            recs.append(
                "源库使用了XA分布式事务，DWS不支持外部XA协议，"
                "需在应用层使用SAGA/TCC模式或最终一致性方案替代"
            )
        if meta.uses_autonomous_transaction:
            recs.append(
                "源库使用了自治事务(Autonomous Transaction)，DWS不支持此特性，"
                "需通过应用层独立事务或dblink模拟"
            )

        # CDC/增量建议
        if meta.has_cdc_active:
            recs.append(
                f"源库已启用CDC({meta.cdc_tool})，建议迁移期间保持CDC运行，"
                f"使用全量+增量同步策略，确保数据一致性"
            )
        if meta.daily_data_growth_gb > 10:
            recs.append(
                f"源库日均数据增长约{meta.daily_data_growth_gb}GB，建议在迁移计划中预留增量同步窗口，"
                f"使用DRS或CDC工具持续同步增量数据"
            )

        # 数据量建议
        if "TB" in meta.total_capacity:
            import re
            nums = re.findall(r'\d+', meta.total_capacity)
            if nums and int(nums[0]) >= 20:
                recs.append(f"数据量较大({meta.total_capacity})，建议分批迁移，使用GDS并行导入提升效率")

        # ETL工具建议
        if "Kettle" in meta.etl_tool:
            recs.append(f"ETL工具({meta.etl_tool})建议逐步迁移到DataX，性能更优、维护更简单")
        if "GoldenGate" in meta.etl_tool:
            recs.append(f"OGG({meta.etl_tool})可保留对接DWS，需安装DWS适配器")
        if "iControl" in meta.scheduler_tool or "TaskCTL" in meta.scheduler_tool:
            recs.append(f"调度工具({meta.scheduler_tool})建议迁移到DolphinScheduler")

        if meta.table_count > 2000:
            recs.append(f"表数量较大({meta.table_count}张)，建议按优先级分批次迁移")

        # 性能建议
        if meta.workload_type == "OLTP":
            recs.append("OLTP负载建议关注分布键设计和行存选择，避免跨节点数据移动过多")
        elif meta.workload_type == "OLAP":
            recs.append("OLAP负载建议使用列存表+分区表，并选择合适分布键优化JOIN性能")
        if meta.has_data_skew:
            recs.append("源库存在数据倾斜现象，迁移后需关注分布键选择和倾斜监控")

        # ==== Exadata特有建议(基于元数据，不硬编码路径) ====
        has_exadata = ("Exadata" in meta.db_version or
                       (meta.source_platform and "Exadata" in meta.source_platform))
        if has_exadata:
            recs.append(
                "源库为Oracle Exadata一体机，Smart Scan/Storage Index/HCC等一体机特性在DWS中无直接对应，"
                "但DWS的MPP并行+列存min/max跳过扫描可达到类似性能效果。"
                "建议在POC阶段选取5+个Exadata优化SQL进行执行计划对比测试"
            )

        # ==== 架构评估建议 ====
        if meta.source_platform and "Exadata" in meta.source_platform:
            recs.append(
                "源平台为Exadata一体机，建议迁移前评估Exadata特定功能依赖，"
                "在POC阶段进行性能基准对比测试"
            )
        if meta.report_count > 200:
            recs.append(
                f"源库涉及{meta.report_count}张报表，建议优先迁移报表相关数据模型，"
                f"确保报表系统平滑过渡"
            )
        if meta.has_standby:
            recs.append(
                "源库有灾备配置，迁移后需要在DWS侧重新配置容灾方案"
            )

        # ==== 分批迁移策略建议 ====
        from core.capacity_planner import CapacityPlanner
        bs = CapacityPlanner.phase_migration_strategy(
            total_capacity=meta.total_capacity,
            table_count=meta.table_count,
            schema_count=meta.schema_count,
            etl_task_count=meta.etl_task_count,
        )
        recs.append(f"【分批迁移策略】{bs['strategy']}")
        for b in bs.get("batches", []):
            recs.append(f"  第{b['batch']}批: {b['scope']} | 窗口: {b['window']}")

        # ==== 硬件配置建议 ====
        cap = CapacityPlanner.recommend_config(
            total_capacity=meta.total_capacity,
            workload_type=meta.workload_type,
            peak_concurrent=meta.peak_concurrent_queries,
        )
        recs.append(
            f"【硬件配置建议】推荐{cap['spec']}: {cap['data_nodes']}数据节点+{cap['manager_nodes']}管理节点"
            f"+{cap['standby_nodes']}备用节点, 共{cap['total_nodes']}节点"
        )

        # ---- GUC 参数兼容性建议 ----
        if self.source_type == "teradata":
            try:
                from rules.teradata_to_dws import get_guc_params
                gucs = get_guc_params()
                guc_recs = [g for g in gucs if g.get("recommend") == "是"]
                if guc_recs:
                    guc_text = "; ".join([f"{g['guc']}={g['td_value']}({g['description']})" for g in guc_recs])
                    recs.append(f"【GUC参数建议】建议在DWS中设置TD兼容GUC参数: {guc_text}")
                    recs.append("【兼容模式】建议创建数据库时指定 DBCOMPATIBILITY='TD' 以获得最佳Teradata兼容性")
                    recs.append("【行为兼容选项】建议在创建数据库后执行 SET behavior_compat_options='strict_text_concat_td,td_compatible_truncation';")
            except ImportError:
                pass
        elif self.source_type == "oracle":
            recs.append("【GUC参数建议】建议创建数据库时指定 DBCOMPATIBILITY='ORA' 以获得Oracle语法兼容性")
        elif self.source_type == "mysql":
            recs.append("【GUC参数建议】建议创建数据库时指定 DBCOMPATIBILITY='MySQL' 以获得MySQL语法兼容性")

        # 通用建议
        recs.append("建议在POC阶段搭建测试环境，选取50+代表性SQL和20+典型UDF进行兼容性验证")
        recs.append("源端环境保留至少1个月，确保在迁移异常时可快速回切")
        recs.append("【L1-L4数据一致性校验】建议按四级校验体系逐层验证: L1结构→L2数据量→L3内容(MD5)→L4业务逻辑")

        return recs

    def _estimate_workload(self, result: AssessmentResult) -> dict:
        tbl = self.metadata.table_count
        func = self.metadata.function_count
        udf = self.metadata.udf_languages
        meta = self.metadata

        ddl_days = round(tbl / 200) + 2
        data_days = 7
        if "TB" in meta.total_capacity:
            import re
            nums = re.findall(r'\d+', meta.total_capacity)
            if nums and int(nums[0]) >= 20:
                data_days = 14
        udf_days = round(func / 50) + 1
        # 从UDF_LANGUAGE_MAP动态识别困难语言，不再硬编码
        lang_map = get_udf_language_map(self.source_type)
        difficult_udf = 0
        for lang_key, count in udf.items():
            if count > 0 and lang_key in lang_map:
                _, difficulty = lang_map[lang_key]
                if difficulty in ("高",):
                    difficult_udf += count
        if difficult_udf > 0:
            udf_days += round(difficult_udf * 0.5)

        # 安全/权限改造工作量
        security_days = 3 if meta.uses_filesystem_access else 1
        if meta.uses_lbac:
            security_days += 5

        # 字符集改造工作量
        charset_days = 3 if meta.source_charset and meta.source_charset.upper() != "UTF-8" else 1

        # 应用层改造工作量
        app_days = 3 if meta.orm_framework else 1

        # 事务改造工作量
        txn_days = 5 if meta.supports_xa else 1
        if meta.uses_autonomous_transaction:
            txn_days += 4

        # CDC/增量同步工作量
        cdc_days = 5 if meta.has_cdc_active else 2

        etl_days = 15 if "Kettle" in meta.etl_tool else 10
        if "SSIS" in meta.etl_tool:
            etl_days = 20
        if "DataStage" in meta.etl_tool:
            etl_days = 18

        test_days = round(tbl / 100) + 5
        total_days = (ddl_days + data_days + udf_days + etl_days + test_days +
                      security_days + charset_days + app_days + txn_days + cdc_days)

        # 阶段级人月明细
        total_months = round(total_days / 22, 1)
        phase_breakdown = {
            "phase1_survey": {
                "name": "调研评估", "pct": 8,
                "days": round(total_days * 0.08), "detail": "源端调研/元数据采集/兼容性评估/安全字符集评估"
            },
            "phase2_poc": {
                "name": "POC验证", "pct": 15,
                "days": round(total_days * 0.15),
                "detail": "环境搭建/DDL验证/UDF验证/Exadata特性验证/性能测试"
            },
            "phase3_structure": {
                "name": "结构迁移", "pct": 10,
                "days": round(total_days * 0.10), "detail": "DDL转换/数据类型/索引/约束迁移"
            },
            "phase4_program": {
                "name": "程序迁移", "pct": 20,
                "days": round(total_days * 0.20), "detail": "存储过程/函数/触发器/SQL适配改造"
            },
            "phase5_data": {
                "name": "数据迁移", "pct": 15,
                "days": round(total_days * 0.15), "detail": "全量迁移/增量同步/分批迁移执行"
            },
            "phase6_verification": {
                "name": "数据校验", "pct": 12,
                "days": round(total_days * 0.12), "detail": "L1结构/L2数据量/L3内容/L4业务逻辑校验"
            },
            "phase7_app": {
                "name": "应用适配", "pct": 8,
                "days": round(total_days * 0.08), "detail": "JDBC驱动/ORM方言/连接池/报表适配"
            },
            "phase8_parallel": {
                "name": "双系统并行", "pct": 7,
                "days": round(total_days * 0.07), "detail": "并行运行/差异分析/业务验证"
            },
            "phase9_go_live": {
                "name": "割接交付", "pct": 5,
                "days": round(total_days * 0.05), "detail": "演练/正式割接/回滚预案/验收"
            },
        }

        return {
            "ddl_conversion_days": ddl_days,
            "data_migration_days": data_days,
            "udf_migration_days": udf_days,
            "etl_migration_days": etl_days,
            "testing_days": test_days,
            "security_audit_days": security_days,
            "charset_conversion_days": charset_days,
            "app_layer_adapt_days": app_days,
            "transaction_adapt_days": txn_days,
            "cdc_sync_days": cdc_days,
            "total_estimated_days": total_days,
            "total_estimated_months": total_months,
            "phase_breakdown": phase_breakdown,
            "note": "以上为纯技术工作量估算，不含项目管理、审批、上线窗口等"
        }

    def _estimate_phases(self, result: AssessmentResult) -> dict:
        meta = self.metadata
        # 根据数据量自适应时间估算
        capacity_value = 0
        if "TB" in meta.total_capacity:
            import re
            nums = re.findall(r'\d+', meta.total_capacity)
            if nums:
                capacity_value = int(nums[0])

        total_months = f"{round(capacity_value/10+3, 1)}-{round(capacity_value/8+5, 1)}个月"

        return {
            "phase1_survey": {
                "name": "调研评估", "weeks": "2-4",
                "description": "源端环境调研、元数据采集、兼容性评估、安全/字符集/应用层评估、方案设计", "order": 1
            },
            "phase2_poc": {
                "name": "POC验证", "weeks": "4-8",
                "description": "目标端环境搭建、DDL迁移验证、UDF兼容性验证、安全/字符集验证、性能测试", "order": 2
            },
            "phase3_migration": {
                "name": "正式迁移", "weeks": "8-12",
                "description": "DDL批量迁移、数据全量+增量、UDF改造、安全审计迁移、字符集转换、应用接口适配、ETL迁移", "order": 3
            },
            "phase4_parallel": {
                "name": "双系统并行", "weeks": "2-4",
                "description": "源端和目标端双系统并行运行、数据差异监控、业务功能验证、性能对比", "order": 4
            },
            "phase5_go_live": {
                "name": "上线割接", "weeks": "1-2",
                "description": "L1-L4数据一致性校验、割接演练、正式上线、业务验证、回切预案、运行保障", "order": 5
            },
            "total_months": total_months,
        }

    def get_verification_framework(self) -> dict:
        """生成L1-L4四级数据一致性校验框架"""
        meta = self.metadata
        return {
            "L1_STRUCTURE": {
                "name": "L1-结构校验",
                "description": "验证表数量、字段数量、数据类型、约束、索引一致性",
                "method": "自动化DDL比对工具 + 人工复核",
                "scope": "全部对象",
                "timing": "全量迁移后立即执行",
                "tolerance": "0差异",
            },
            "L2_DATA_VOLUME": {
                "name": "L2-数据量校验",
                "description": "验证行数对比、空值率、主键唯一性、去重校验",
                "method": "SELECT COUNT(*), COUNT(DISTINCT pk) FROM t",
                "scope": "全部表",
                "timing": "全量+每次增量同步后",
                "tolerance": "0差异",
            },
            "L3_DATA_CONTENT": {
                "name": "L3-数据内容校验",
                "description": "数值字段SUM/AVG/MIN/MAX对比、MD5抽样校验、按ID范围分块校验",
                "method": "数值字段聚合对比 + MD5(GROUP_CONCAT)分块校验",
                "scope": "核心业务表(资产金额类字段必验)",
                "timing": "全量+定期增量后(建议每百万行抽样10%)",
                "tolerance": "数值差异<0.01元(金融场景)",
            },
            "L4_BUSINESS_LOGIC": {
                "name": "L4-业务逻辑校验",
                "description": "行业特定业务规则验证",
                "method": "资产总值核对/份额勾稽/交易流水T+1验证/净值一致性",
                "scope": "按业务场景定制",
                "timing": "业务验证阶段(试运行1-2周)",
                "tolerance": "0差异",
            },
        }
