"""
竞品对比评估
DWS vs 金山云KDW / OushuDB / Cloudberry 等功能对比
"""


class CompetitorCompare:
    """竞品对比分析引擎"""

    COMPETITOR_INFO = {
        "kingsoft_kdw": {
            "name": "金山云KDW",
            "type": "MPP数据仓库(存算分离)",
            "strengths": [
                "存算分离架构，计算和存储独立扩缩容",
                "秒级扩缩容不涉及数据重新分布",
                "对象存储可无限扩展",
                "计算节点无状态，故障自愈分钟级",
                "支持物理机/虚拟机/容器部署",
                "KSQL支持SQL 2003+",
            ],
            "weaknesses": [
                "生态成熟度不如华为DWS(PostgreSQL生态)",
                "社区资源和文档不如华为丰富",
                "信创认证和案例数量少于华为",
                "企业级运维工具链待完善",
            ],
        },
        "oushu_db": {
            "name": "OushuDB",
            "type": "MPP数据仓库(新一代云原生)",
            "strengths": [
                "性能优秀，TPC-H测试表现突出",
                "对Greenplum兼容度高",
                "支持多种存储格式",
            ],
            "weaknesses": [
                "信创合规认证不如华为全面",
                "大企业案例和生态支持待加强",
                "华为全栈解决方案优势(数仓+大数据+AI)",
            ],
        },
        "cloudberry": {
            "name": "Apache Cloudberry",
            "type": "开源MPP数据库(Greenplum分支)",
            "strengths": [
                "开源社区版，无需商业许可",
                "与GP完全兼容",
                "社区活跃度较高",
            ],
            "weaknesses": [
                "开源版缺乏企业级支持",
                "信创认证有限",
                "不适合核心生产系统",
                "缺少华为全栈生态集成(DataArts/MRS等)",
            ],
        },
    }

    DWS_STRENGTHS = [
        "华为全栈生态(DataArts/MRS/IoT等深度集成)",
        "信创合规认证最全面(国资委/金融信创目录)",
        "PostgreSQL生态兼容(JDBC/ODBC/ORM)",
        "企业级运维工具(CloudEye/DAS/巡检)",
        "1+8+N生态: 华为云Stack全栈",
        "全球最大的信创数据库社区",
        "华为原厂服务保障",
        "TPC-H性能领先",
        "支持2048节点集群，PB级容量",
        "行存/列存/混合存储灵活选择",
    ]

    DWS_WEAKNESSES = [
        "存算分离架构相对金山云KDW不够彻底",
        "扩缩容涉及数据重分布(MPP架构限制)",
        "价格可能高于开源方案Cloudberry",
    ]

    @classmethod
    def compare(cls, source_type: str, competitor: str = "",
                total_capacity: str = "", table_count: int = 0) -> dict:
        """生成DWS vs 竞品的对比评估"""
        result = {
            "source_type": source_type,
            "target": "华为DWS(GaussDB)",
            "competitor": None,
            "dws_recommend_score": 0,
            "comparison_matrix": [],
            "recommendation": "",
        }

        if competitor and competitor in cls.COMPETITOR_INFO:
            comp = cls.COMPETITOR_INFO[competitor]
            result["competitor"] = comp

            # 对比矩阵
            matrix = [
                {"dimension": "架构类型", "dws": "MPP Share-Nothing", competitor: "存算分离(金山云)" if competitor == "kingsoft_kdw" else "MPP"},
                {"dimension": "信创认证", "dws": "✅ 最全面(金融信创目录)", competitor: "⚠️ 部分"},
                {"dimension": "PostgreSQL生态", "dws": "✅ 原生兼容", competitor: "✅ 兼容(金山云)" if competitor == "kingsoft_kdw" else "⚠️ 部分"},
                {"dimension": "华为全栈集成", "dws": "✅ 深度集成(DataArts/MRS)", competitor: "❌ 无"},
                {"dimension": "企业级运维", "dws": "✅ CloudEye/DAS/Automation", competitor: "⚠️ 基础"},
                {"dimension": "扩缩容灵活性", "dws": "⚠️ 需重分布", competitor: "✅ 秒级(存算分离)" if competitor == "kingsoft_kdw" else "⚠️ 类似"},
                {"dimension": "案例规模", "dws": "✅ 金融行业最大装机量", competitor: "⚠️ 有限"},
                {"dimension": "原厂支持", "dws": "✅ 华为原厂", competitor: "⚠️ 有限"},
            ]
            result["comparison_matrix"] = matrix

            # 综合推荐评分
            import re
            nums = re.findall(r'\d+', total_capacity) if total_capacity else [0]
            capacity_tb = float(nums[0]) if nums else 0

            dws_score = 85
            if capacity_tb > 50:
                dws_score += 5  # 大容量场景DWS更有优势
            if competitor in ("kingsoft_kdw",):
                dws_score -= 5  # 金山云的存算分离在某些场景有吸引力

            result["dws_recommend_score"] = dws_score
            result["recommendation"] = cls._generate_recommendation(
                competitor, dws_score, capacity_tb
            )

        return result

    @classmethod
    def list_competitors(cls) -> list:
        """列出可对比的竞品"""
        return [{"key": k, "name": v["name"], "type": v["type"]}
                for k, v in cls.COMPETITOR_INFO.items()]

    @classmethod
    def _generate_recommendation(cls, competitor: str, score: int, capacity_tb: float) -> str:
        """生成推荐建议"""
        if score >= 85:
            base = "华为DWS是推荐选择，信创合规最全面、金融行业案例最丰富"
        elif score >= 70:
            base = "华为DWS适合大部分场景，建议根据具体需求选型"
        else:
            base = "建议结合具体场景进行POC对比测试"

        if competitor == "kingsoft_kdw" and capacity_tb > 100:
            base += "。金山云KDW存算分离架构在大容量场景有弹性优势，建议在POC中加入弹性扩缩容专项验证"
        return base
