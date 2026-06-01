"""
通用迁移分析引擎
与源/目标类型解耦，接收任意元数据+规则集进行分析
"""

from dataclasses import dataclass, field, asdict
from typing import Optional, Callable
from core.models import (
    MigrationMetadata, AssessmentResult, CategoryResult, CheckResult
)


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
        """执行完整分析"""
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
                    description=rule.get("description", ""),
                    source_pattern=rule.get("source_pattern", rule.get("gp_pattern", "")),
                    target_solution=rule.get(
                        "target_solution",
                        rule.get("dws_solution", rule.get("alternative", ""))
                    ),
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
                    description=rule.get("description", ""),
                    target_solution=rule.get("target_solution", rule.get("dws_solution", "")),
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
        """生成迁移建议（可被子类覆盖以增加特定建议）"""
        recs = []
        udf = self.metadata.udf_languages

        if udf.get("plpythonu", 0) > 0:
            recs.append(
                f"plpythonu函数({udf['plpythonu']}个)需改造为plpgsql或Java UDF，"
                f"建议在POC阶段选取10+个复杂函数进行验证"
            )
        if udf.get("plperl", 0) > 0 or udf.get("plperlu", 0) > 0:
            total_perl = udf.get("plperl", 0) + udf.get("plperlu", 0)
            recs.append(
                f"plperl/plperlu函数({total_perl}个)需完全重写为plpgsql"
            )

        if "TB" in self.metadata.total_capacity:
            import re
            nums = re.findall(r'\d+', self.metadata.total_capacity)
            if nums and int(nums[0]) >= 20:
                recs.append(
                    f"数据量较大({self.metadata.total_capacity})，建议分批迁移"
                )

        if "Kettle" in self.metadata.etl_tool:
            recs.append(
                f"ETL工具({self.metadata.etl_tool})建议逐步迁移到DataX"
            )
        if "iControl" in self.metadata.scheduler_tool or "TaskCTL" in self.metadata.scheduler_tool:
            recs.append(
                f"调度工具({self.metadata.scheduler_tool})建议迁移到DolphinScheduler"
            )

        if self.metadata.table_count > 2000:
            recs.append(
                f"表数量较大({self.metadata.table_count}张)，建议按优先级分批次迁移"
            )

        recs.append("建议在POC阶段搭建测试环境，选取50+代表性SQL和20+典型UDF进行兼容性验证")
        recs.append("源端环境保留至少1个月，确保在迁移异常时可快速回切")

        return recs

    def _estimate_workload(self, result: AssessmentResult) -> dict:
        tbl = self.metadata.table_count
        func = self.metadata.function_count
        udf = self.metadata.udf_languages

        ddl_days = round(tbl / 200) + 2
        data_days = 7
        udf_days = round(func / 50) + 1
        difficult_udf = udf.get("plpythonu", 0) + udf.get("plperl", 0) + udf.get("plperlu", 0)
        if difficult_udf > 0:
            udf_days += round(difficult_udf * 0.5)
        etl_days = 15 if "Kettle" in self.metadata.etl_tool else 10
        test_days = round(tbl / 100) + 5
        total_days = ddl_days + data_days + udf_days + etl_days + test_days

        return {
            "ddl_conversion_days": ddl_days,
            "data_migration_days": data_days,
            "udf_migration_days": udf_days,
            "etl_migration_days": etl_days,
            "testing_days": test_days,
            "total_estimated_days": total_days,
            "total_estimated_months": round(total_days / 22, 1),
            "note": "以上为纯技术工作量估算，不含项目管理、审批、上线窗口等"
        }

    def _estimate_phases(self, result: AssessmentResult) -> dict:
        return {
            "phase1_survey": {
                "name": "调研评估", "weeks": "2-4",
                "description": "源端环境调研、元数据采集、兼容性评估、方案设计", "order": 1
            },
            "phase2_poc": {
                "name": "POC验证", "weeks": "4-8",
                "description": "目标端环境搭建、DDL迁移验证、UDF兼容性验证、性能测试", "order": 2
            },
            "phase3_migration": {
                "name": "正式迁移", "weeks": "8-12",
                "description": "DDL批量迁移、数据全量+增量、UDF改造、ETL迁移、应用联调", "order": 3
            },
            "phase4_go_live": {
                "name": "上线割接", "weeks": "1-2",
                "description": "割接演练、正式上线、业务验证、回切预案、运行保障", "order": 4
            },
            "total_months": "4-6个月",
        }
