"""
POC测试用例推荐器
基于 DWS POC 测试报告（某券商GaussDB(DWS)测试报告v1.docx）提取的60+测试用例
按L1-L4四级分类，根据源端特征自动推荐所需测试项目
"""

from dataclasses import dataclass, field
from typing import Optional


# ================================================================
# 测试用例定义
# ================================================================
@dataclass
class PocTestCase:
    """单个POC测试用例"""
    id: str = ""
    name: str = ""
    level: str = "L1"                      # L1基础 / L2业务 / L3性能 / L4高可用
    category: str = ""                     # 测试分类
    description: str = ""                  # 测试目的
    preconditions: str = ""                # 预置条件
    steps: list = field(default_factory=list)  # 测试步骤
    expected_result: str = ""              # 预期结果
    always_required: bool = True           # 是否必选
    trigger_on_source: list = field(default_factory=list)  # 仅特定源端触发
    trigger_on_capacity_tb: float = 0      # 数据量超过此值触发
    trigger_on_production: bool = False    # 生产环境触发
    trigger_on_tool: list = field(default_factory=list)    # 特定工具触发
    estimated_hours: float = 1.0           # 预计耗时(小时)
    priority: str = "中"                   # 高/中/低


# ================================================================
# 测试用例库 (来自DWS POC测试报告)
# ================================================================
TEST_CASES = [
    # ======================== L1: 基础功能验证 ========================
    PocTestCase(
        id="POC-L1-001", name="DDL数据定义语言", level="L1",
        category="基本功能",
        description="验证CREATE/ALTER/DROP DATABASE/USER/TABLE/VIEW/存储过程",
        preconditions="DWS集群正常启动",
        steps=["创建数据库和用户", "创建表和视图", "创建存储过程", "删除所有对象"],
        expected_result="全部DDL操作成功",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-002", name="DML数据操作语言", level="L1",
        category="基本功能",
        description="验证INSERT/SELECT/UPDATE/DELETE基本操作",
        preconditions="DDL验证通过",
        steps=["插入数据验证", "查询数据验证", "修改数据验证", "删除数据验证", "视图查询验证"],
        expected_result="全部DML操作正确",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-003", name="DCL数据控制语言", level="L1",
        category="基本功能",
        description="验证GRANT/REVOKE权限控制",
        preconditions="用户已创建",
        steps=["GRANT建表权限", "GRANT查询权限", "REVOKE权限", "验证权限隔离"],
        expected_result="权限控制符合预期",
        always_required=True, estimated_hours=0.5, priority="高",
    ),
    PocTestCase(
        id="POC-L1-004", name="基本数据类型兼容", level="L1",
        category="基本功能",
        description="验证字符型/数值型/日期型/大对象/布尔型",
        preconditions="DWS集群正常启动",
        steps=["创建包含全部字段类型的表", "插入各类数据", "查询验证"],
        expected_result="全部数据类型支持",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-005", name="基本运算与表达式", level="L1",
        category="基本功能",
        description="验证逻辑表达式/条件表达式/算术运算(共25项)",
        preconditions="测试表已创建",
        steps=["等于/不等于/大于/小于/介于", "AND/OR/NOT", "加/减/乘/除"],
        expected_result="全部运算结果正确",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-006", name="表连接与子查询", level="L1",
        category="基本功能",
        description="验证INNER/LEFT/RIGHT JOIN和子查询",
        preconditions="多张测试表已创建并含数据",
        steps=["内连接查询", "左外连接", "右外连接", "自连接", "嵌套子查询"],
        expected_result="全部连接和子查询结果正确",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-007", name="聚合函数与分组", level="L1",
        category="基本功能",
        description="验证MIN/MAX/SUM/COUNT/AVG/GROUP BY/HAVING/DISTINCT/UNION",
        preconditions="测试表含足够数据",
        steps=["聚合函数验证", "分组统计验证", "集合操作验证"],
        expected_result="全部聚合结果正确",
        always_required=True, estimated_hours=0.5, priority="高",
    ),
    PocTestCase(
        id="POC-L1-008", name="日期与字符串函数", level="L1",
        category="基本功能",
        description="验证日期加减/字符串操作/EXTRACT/CAST",
        preconditions="测试表已创建",
        steps=["日期加减计算", "字符串连接/截取/定位", "EXTRACT函数", "CAST类型转换"],
        expected_result="全部函数执行正确",
        always_required=True, estimated_hours=1.0, priority="高",
    ),
    PocTestCase(
        id="POC-L1-009", name="事务与并发控制", level="L1",
        category="基本功能",
        description="验证事务提交/回滚/读已提交/行级锁",
        preconditions="集群正常",
        steps=["事务提交验证", "事务回滚验证", "MVCC读一致性验证", "行级锁验证"],
        expected_result="事务行为符合ACID",
        always_required=True, estimated_hours=1.5, priority="高",
    ),

    # ======================== L2: 业务功能验证 ========================
    PocTestCase(
        id="POC-L2-001", name="业务SQL适配性验证", level="L2",
        category="业务适配",
        description="选取实际业务系统中的代表性SQL在DWS上执行",
        preconditions="源端业务SQL样例已收集(建议10-20条)",
        steps=["收集典型SQL(含复杂查询)", "在DWS上逐条执行", "比对执行结果和耗时", "记录不兼容SQL"],
        expected_result="关键业务SQL可在DWS上正确执行",
        always_required=True, estimated_hours=8.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-002", name="存储过程/函数迁移验证", level="L2",
        category="业务适配",
        description="验证源端存储过程和函数在DWS中的兼容性",
        preconditions="源端存储过程清单已收集",
        steps=["选取代表性存储过程(10+)", "逐条迁移到DWS语法", "执行验证结果一致性", "记录改造工作量"],
        expected_result="存储过程可迁移并在DWS上正确执行",
        always_required=True, estimated_hours=4.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-003", name="ETL工具对接验证", level="L2",
        category="生态兼容",
        description="验证ETL工具通过JDBC/ODBC对接DWS",
        preconditions="ETL工具可访问DWS集群",
        steps=["配置DWS JDBC/ODBC连接", "创建数据同步任务", "执行增量同步", "验证数据一致性"],
        expected_result="ETL工具可正常对接DWS",
        always_required=True, estimated_hours=4.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-004", name="BI工具对接验证", level="L2",
        category="生态兼容",
        description="验证BI工具(帆软/Tableau/PowerBI)对接DWS",
        preconditions="BI工具可访问DWS",
        steps=["配置DWS数据源", "打开已有报表", "验证数据刷新", "验证报表渲染"],
        expected_result="BI工具报表正常展示",
        always_required=True, estimated_hours=2.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-005", name="全文检索功能", level="L2",
        category="高级功能",
        description="验证DWS全文检索能力(tsvector/tsquery)",
        preconditions="含文本数据的测试表",
        steps=["创建tsvector索引", "执行全文检索查询", "验证结果相关性"],
        expected_result="全文检索功能正常",
        always_required=False, estimated_hours=1.0, priority="中",
    ),
    PocTestCase(
        id="POC-L2-006", name="Oracle兼容模式验证", level="L2",
        category="高级功能",
        description="验证Oracle兼容模式下SQL语法",
        preconditions="创建兼容ORA格式的数据库",
        steps=["创建ORA兼容数据库", "验证Oracle特有语法", "验证PL/SQL迁移效果"],
        expected_result="Oracle兼容模式正常",
        trigger_on_source=["oracle"], estimated_hours=2.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-007", name="MySQL兼容模式验证", level="L2",
        category="高级功能",
        description="验证MySQL兼容模式下SQL语法",
        preconditions="创建兼容MySQL格式的数据库",
        steps=["创建MySQL兼容数据库", "验证MySQL特有语法"],
        expected_result="MySQL兼容模式正常",
        trigger_on_source=["mysql"], estimated_hours=2.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-008", name="TD兼容模式验证", level="L2",
        category="高级功能",
        description="验证Teradata兼容模式下SQL语法",
        preconditions="创建兼容TD格式的数据库",
        steps=["创建TD兼容数据库", "验证TD特有语法(QUALIFY/MAKE_DATE等)"],
        expected_result="TD兼容模式正常",
        trigger_on_source=["teradata", "td"], estimated_hours=2.0, priority="高",
    ),
    PocTestCase(
        id="POC-L2-009", name="数据脱敏与安全", level="L2",
        category="安全性",
        description="验证数据脱敏/加密/行级访问控制/三权分立",
        preconditions="DWS已开启安全特性",
        steps=["创建脱敏策略", "验证加密解密函数", "验证行级访问控制", "验证三权分立"],
        expected_result="安全特性符合预期",
        always_required=True, estimated_hours=2.0, priority="中",
    ),
    PocTestCase(
        id="POC-L2-010", name="分区表与分区裁剪", level="L2",
        category="业务适配",
        description="验证分区表创建和分区裁剪效率",
        preconditions="源端有使用分区表",
        steps=["按源端分区策略建表", "导入数据", "验证分区裁剪是否生效", "比对查询效率"],
        expected_result="分区表功能正常，分区裁剪生效",
        always_required=False, estimated_hours=2.0, priority="中",
    ),
    PocTestCase(
        id="POC-L2-011", name="视图与同义词", level="L2",
        category="高级功能",
        description="验证视图(含视图更新)和同义词功能",
        preconditions="基表已创建",
        steps=["创建视图", "通过视图更新数据", "创建同义词", "通过同义词访问"],
        expected_result="视图和同义词功能正常",
        always_required=True, estimated_hours=1.0, priority="中",
    ),

    # ======================== L3: 性能测试 ========================
    PocTestCase(
        id="POC-L3-001", name="TPCH基准测试", level="L3",
        category="性能基准",
        description="执行TPCH 22条SQL验证DWS分析型查询性能",
        preconditions="TPCH数据已加载(建议100GB-1TB)",
        steps=["加载TPCH测试数据", "串行执行22条查询", "记录每条SQL耗时", "与SLA要求对比"],
        expected_result="TPCH总耗时在可接受范围内",
        always_required=False, trigger_on_capacity_tb=5, estimated_hours=4.0, priority="高",
    ),
    PocTestCase(
        id="POC-L3-002", name="并发压力测试", level="L3",
        category="性能基准",
        description="模拟业务并发查询场景，验证DWS并发处理能力",
        preconditions="业务SQL样例已收集",
        steps=["配置并发客户端", "逐步增加并发数(50/100/200)", "监控响应时间和成功率", "确定最大并发阈值"],
        expected_result="并发场景下响应时间在SLA范围内",
        always_required=False, trigger_on_capacity_tb=10, estimated_hours=8.0, priority="高",
    ),
    PocTestCase(
        id="POC-L3-003", name="大表聚合查询效率", level="L3",
        category="性能基准",
        description="验证大表(千万级以上)的聚合查询性能",
        preconditions="大表已创建并加载数据",
        steps=["执行COUNT/GROUP BY查询", "执行SUM/AVG聚合", "执行多表JOIN", "记录执行时间"],
        expected_result="大表聚合性能满足SLA要求",
        always_required=False, trigger_on_capacity_tb=5, estimated_hours=3.0, priority="中",
    ),
    PocTestCase(
        id="POC-L3-004", name="数据导入性能测试", level="L3",
        category="性能基准",
        description="验证GDS/INSERT批量导入性能",
        preconditions="GDS服务已配置",
        steps=["准备100GB测试数据", "使用GDS并行导入", "使用INSERT逐条导入", "比对导入速率"],
        expected_result="导入速率满足迁移窗口要求",
        always_required=False, trigger_on_capacity_tb=10, estimated_hours=4.0, priority="中",
    ),
    PocTestCase(
        id="POC-L3-005", name="资源隔离与管控", level="L3",
        category="运维管理",
        description="验证资源池隔离和空间管控能力",
        preconditions="DWS集群正常",
        steps=["创建资源池并分配用户", "执行资源密集型查询", "验证资源隔离效果", "验证临时/永久空间管控"],
        expected_result="资源隔离生效，空间管控正常",
        always_required=False, estimated_hours=2.0, priority="低",
    ),
    PocTestCase(
        id="POC-L3-006", name="AWR性能报告", level="L3",
        category="运维管理",
        description="验证DWS的AWR性能报告功能",
        preconditions="集群已运行一段时间",
        steps=["生成AWR快照", "生成AWR报告", "分析报告内容"],
        expected_result="AWR报告生成正常，可辅助性能分析",
        always_required=False, estimated_hours=1.0, priority="低",
    ),
    PocTestCase(
        id="POC-L3-007", name="磁盘IO与网络带宽测试", level="L3",
        category="运维管理",
        description="验证fio磁盘压测和网络带宽满足要求",
        preconditions="fio工具已安装",
        steps=["执行fio磁盘读写测试(4K/8K/128K/1M)", "执行节点间网络带宽测试", "记录结果并与基线对比"],
        expected_result="磁盘IO和网络带宽满足DWS运行要求",
        always_required=False, trigger_on_production=True, estimated_hours=2.0, priority="中",
    ),

    # ======================== L4: 高可用与容灾 ========================
    PocTestCase(
        id="POC-L4-001", name="节点故障切换验证", level="L4",
        category="高可用",
        description="模拟单个数据节点故障，验证集群自动切换能力",
        preconditions="DWS集群三节点以上",
        steps=["正在执行业务查询", "模拟数据节点断网/断电", "观察查询是否中断/自动恢复", "验证数据完整性"],
        expected_result="集群自动切换，查询不中断或短时中断后自动恢复",
        always_required=False, trigger_on_production=True, estimated_hours=4.0, priority="高",
    ),
    PocTestCase(
        id="POC-L4-002", name="主备切换验证", level="L4",
        category="高可用",
        description="验证cm_ctl switchover主备切换功能",
        preconditions="主备架构已部署",
        steps=["执行cm_ctl switchover -a", "观察切换时间", "验证数据一致性", "验证业务连续性"],
        expected_result="主备切换成功，数据零丢失",
        always_required=False, trigger_on_production=True, estimated_hours=2.0, priority="高",
    ),
    PocTestCase(
        id="POC-L4-003", name="数据备份恢复验证", level="L4",
        category="高可用",
        description="验证gs_dump/gs_restore备份恢复功能",
        preconditions="DWS集群正常",
        steps=["导出全量数据(gs_dump)", "清理测试数据", "导入数据(gs_restore)", "验证数据完整性"],
        expected_result="备份恢复功能正常，数据完整",
        always_required=False, trigger_on_production=True, estimated_hours=3.0, priority="中",
    ),
    PocTestCase(
        id="POC-L4-004", name="容灾切换演练", level="L4",
        category="高可用",
        description="模拟主集群整体故障，验证容灾切换",
        preconditions="容灾集群已部署",
        steps=["停止主集群服务", "触发容灾切换", "验证备集群业务可用", "执行反向恢复"],
        expected_result="容灾切换在规定RTO/RPO内完成",
        always_required=False, trigger_on_production=True, estimated_hours=8.0, priority="高",
    ),
]


class PocTestPlanner:
    """POC测试用例推荐器"""

    # L1-L4按阶段分类
    LEVEL_INFO = {
        "L1": {
            "name": "L1 - 基础功能验证",
            "description": "验证DWS基本功能是否正常，所有迁移项目必选",
            "time_estimate": "约 0.5-1 天",
            "mandatory": True,
        },
        "L2": {
            "name": "L2 - 业务适配验证",
            "description": "验证业务系统和周边工具的兼容性，根据源端特征自动推荐",
            "time_estimate": "约 3-5 天",
            "mandatory": False,
        },
        "L3": {
            "name": "L3 - 性能基准测试",
            "description": "验证性能是否满足SLA要求，数据量大或生产环境建议执行",
            "time_estimate": "约 2-4 天",
            "mandatory": False,
        },
        "L4": {
            "name": "L4 - 高可用与容灾验证",
            "description": "验证集群高可用和容灾能力，仅生产环境建议执行",
            "time_estimate": "约 2-3 天",
            "mandatory": False,
        },
    }

    @classmethod
    def recommend(cls, metadata, assessment_result=None) -> dict:
        """
        根据源端特征推荐POC测试用例

        Args:
            metadata: MigrationMetadata 源端元数据
            assessment_result: AssessmentResult (可选，用于联动兼容性评估结果)

        Returns:
            dict: {
                "summary": {...},
                "levels": {"L1": [...], "L2": [...], ...},
                "total_estimated_hours": 0,
                "timeline_estimate": "",
            }
        """
        import re
        recommended = {"L1": [], "L2": [], "L3": [], "L4": []}
        total_hours = 0

        # 解析数据量
        capacity_tb = 0
        if metadata.total_capacity and "TB" in metadata.total_capacity:
            nums = re.findall(r'\d+', metadata.total_capacity)
            if nums:
                capacity_tb = float(nums[0])

        # 遍历所有用例，按条件匹配
        for case in TEST_CASES:
            matched = False

            # L1: 必选
            if case.level == "L1" and case.always_required:
                matched = True

            # L2: 业务适配 — 判断触发条件
            elif case.level == "L2":
                if case.always_required:
                    matched = True
                elif case.trigger_on_source and metadata.source_type:
                    src = metadata.source_type.lower()
                    for trigger in case.trigger_on_source:
                        if src.startswith(trigger) or trigger.startswith(src):
                            matched = True
                            break
                elif not case.trigger_on_source:
                    # 无特定触发条件的L2用例默认不推荐（由用户按需选择）
                    pass

            # L3: 性能 — 按数据量触发
            elif case.level == "L3":
                if case.trigger_on_capacity_tb > 0 and capacity_tb >= case.trigger_on_capacity_tb:
                    matched = True
                elif case.always_required:
                    matched = True
                elif case.trigger_on_production:
                    # 由用户指定是否为生产环境
                    pass

            # L4: 高可用 — 仅生产环境
            elif case.level == "L4":
                if case.trigger_on_production and metadata.source_platform and "生产" in metadata.source_platform:
                    matched = True
                elif case.always_required:
                    matched = True

            if matched:
                recommended[case.level].append({
                    "id": case.id,
                    "name": case.name,
                    "category": case.category,
                    "level": case.level,
                    "description": case.description,
                    "estimated_hours": case.estimated_hours,
                    "priority": case.priority,
                    "steps": case.steps,
                    "expected_result": case.expected_result,
                })
                total_hours += case.estimated_hours

        # 计算各层级汇总
        level_summary = {}
        for level in ["L1", "L2", "L3", "L4"]:
            cases = recommended[level]
            level_info = cls.LEVEL_INFO.get(level, {})
            level_summary[level] = {
                "name": level_info.get("name", level),
                "description": level_info.get("description", ""),
                "time_estimate": level_info.get("time_estimate", ""),
                "mandatory": level_info.get("mandatory", False),
                "case_count": len(cases),
                "level_hours": sum(c["estimated_hours"] for c in cases),
            }

        # 根据总耗时估算POC周数
        if total_hours <= 16:
            timeline = "1周(简单场景，纯功能验证)"
        elif total_hours <= 40:
            timeline = "1-2周(中等场景，含业务适配)"
        elif total_hours <= 80:
            timeline = "2-3周(复杂场景，含性能测试)"
        else:
            timeline = "3-4周(完整场景，含高可用验证)"

        return {
            "summary": {
                "total_cases": sum(len(v) for v in recommended.values()),
                "total_estimated_hours": round(total_hours, 1),
                "timeline_estimate": timeline,
                "note": "以上为POC测试时间和用例建议，实际安排可根据项目情况调整。"
                        "L1为必选，L2-L4按需选择。",
            },
            "levels": level_summary,
            "recommended_cases": recommended,
            "all_cases": [
                {
                    "id": c.id,
                    "name": c.name,
                    "level": c.level,
                    "category": c.category,
                    "description": c.description,
                    "estimated_hours": c.estimated_hours,
                    "priority": c.priority,
                }
                for c in TEST_CASES
            ],
        }
