"""
硬件容量规划器
基于源端数据量和特征，推荐DWS集群配置
"""


class CapacityPlanner:
    """容量规划推荐引擎"""

    # 华为鲲鹏服务器规格模板
    SERVER_SPECS = {
        "kunpeng_small": {
            "name": "鲲鹏-基础型",
            "cpu": "2*32Core Kunpeng 920",
            "memory": "256GB",
            "disk": "2*960GB SSD(system) + 12*3.84T SATA SSD(data)",
            "usable_per_node_gb": 9600,  # 8*3.84*0.9*0.7*0.5  raid5+系统开销
            "nodes_per_rack": 22,
            "scenario": "海通期货200TB级别",
        },
        "kunpeng_medium": {
            "name": "鲲鹏-增强型",
            "cpu": "2*48Core Kunpeng 920",
            "memory": "512GB",
            "disk": "2*960GB SSD(system) + 12*7.68T SATA SSD(data)",
            "usable_per_node_gb": 19200,
            "nodes_per_rack": 22,
            "scenario": "百TB级别高性能场景",
        },
        "x86_large": {
            "name": "X86-通用型",
            "cpu": "2*24Core Intel Xeon",
            "memory": "256GB",
            "disk": "2*600GB SAS(system) + 8*4T SATA(data)",
            "usable_per_node_gb": 7200,
            "nodes_per_rack": 20,
            "scenario": "通用场景",
        },
        "vm_standard": {
            "name": "虚拟机-标准型",
            "cpu": "8 vCPU",
            "memory": "32GB",
            "disk": "500GB SAS + 对象存储",
            "usable_per_node_gb": 400,
            "nodes_per_rack": 0,
            "scenario": "开发/测试环境或小型场景",
        },
    }

    @classmethod
    def estimate_storage(cls, total_capacity_tb: float,
                         growth_yearly_pct: float = 15,
                         retention_years: int = 5,
                         compression_ratio: float = 5.0) -> dict:
        """
        估算存储需求

        Args:
            total_capacity_tb: 源端当前数据量(TB)
            growth_yearly_pct: 年增长率(%)
            retention_years: 数据保留年限
            compression_ratio: 列存压缩比(默认5:1)
        """
        current_tb = total_capacity_tb
        future_tb = current_tb * ((1 + growth_yearly_pct / 100) ** retention_years)
        compressed_tb = future_tb / compression_ratio
        # 加上系统开销(副本+元数据+临时空间)约30%
        total_with_overhead = compressed_tb * 1.3

        return {
            "current_tb": round(current_tb, 1),
            "future_5yr_tb": round(future_tb, 1),
            "annual_growth_pct": growth_yearly_pct,
            "compression_ratio": compression_ratio,
            "compressed_tb": round(compressed_tb, 1),
            "total_with_overhead_tb": round(total_with_overhead, 1),
            "retention_years": retention_years,
        }

    @classmethod
    def recommend_config(cls, total_capacity: str,
                         workload_type: str = "OLAP",
                         peak_concurrent: int = 50,
                         high_availability: bool = True) -> dict:
        """
        推荐DWS集群配置

        Args:
            total_capacity: 总数据容量描述 e.g. "200TB", "70TB"
            workload_type: 负载类型 "OLAP" / "OLTP" / "混合"
            peak_concurrent: 峰值并发查询数
            high_availability: 是否需要高可用
        """
        import re
        nums = re.findall(r'\d+', total_capacity)
        if not nums:
            return {"error": "无法解析数据容量", "recommended_spec": "—"}
        capacity_tb = float(nums[0])
        if "G" in total_capacity.upper() and "T" not in total_capacity.upper():
            capacity_tb = capacity_tb / 1024

        # 根据容量推荐服务器规格
        if capacity_tb >= 100:
            spec_key = "kunpeng_small"
            spec = cls.SERVER_SPECS[spec_key]
        elif capacity_tb >= 20:
            spec_key = "x86_large"
            spec = cls.SERVER_SPECS[spec_key]
        else:
            spec_key = "vm_standard"
            spec = cls.SERVER_SPECS[spec_key]

        # 计算节点数
        storage = cls.estimate_storage(capacity_tb)
        required_gb = storage["total_with_overhead_tb"] * 1024

        data_nodes = max(3, round(required_gb / spec["usable_per_node_gb"]) + 1)
        # 管理节点: HA需要3个, 非HA需要2个
        if high_availability:
            manager_nodes = 3
            standby_nodes = 2
        else:
            manager_nodes = 2
            standby_nodes = 1

        total_nodes = data_nodes + manager_nodes + standby_nodes

        # 并发建议
        if peak_concurrent <= 50:
            concurrency_advice = "基础并发能力满足需求"
        elif peak_concurrent <= 200:
            concurrency_advice = "建议启用查询排队(queuing)机制，增加2-4个计算节点应对并发峰值"
        else:
            extra_nodes = round(peak_concurrent / 100)
            concurrency_advice = f"高并发场景建议增加{extra_nodes}个计算节点，启用资源池隔离"

        return {
            "spec": spec["name"],
            "cpu": spec["cpu"],
            "memory": spec["memory"],
            "disk": spec["disk"],
            "data_nodes": data_nodes,
            "manager_nodes": manager_nodes,
            "standby_nodes": standby_nodes,
            "total_nodes": total_nodes,
            "usable_per_node_gb": spec["usable_per_node_gb"],
            "capacity_tb": capacity_tb,
            "compressed_tb": storage["compressed_tb"],
            "future_5yr_tb": storage["future_5yr_tb"],
            "storage_detail": storage,
            "concurrency_advice": concurrency_advice,
            "ha_enabled": high_availability,
            "notes": [
                "以上为初步估算，实际配置需结合业务场景、并发数、性能要求等综合评估",
                "建议在POC阶段进行性能基准测试，验证配置是否满足SLA要求",
                "列存压缩比5:1为典型值，实际效果取决于数据类型和分布",
                "数据盘使用RAID5，已预留系统开销(约30%)",
            ],
        }

    @classmethod
    def phase_migration_strategy(cls, total_capacity: str,
                                 table_count: int,
                                 schema_count: int = 1,
                                 etl_task_count: int = 0) -> dict:
        """
        建议分批迁移策略

        Returns:
            分批建议，每批范围和时间窗口
        """
        import re
        nums = re.findall(r'\d+', total_capacity)
        capacity_tb = float(nums[0]) if nums else 0

        if capacity_tb < 10:
            return {
                "strategy": "全量一次性迁移",
                "batches": [{"batch": 1, "scope": "全部对象", "window": "周末窗口(2-3天)"}],
                "total_window": "2-3天",
            }

        batches = []
        total_window_days = 0

        if capacity_tb >= 100:
            # 超大容量: 分5批
            per_batch_tb = capacity_tb / 5
            batch_tables = round(table_count / 5)
            for i in range(5):
                if i == 0:
                    scope = f"首批(速赢): 非核心/报表类({batch_tables}张表，约{per_batch_tb}TB)"
                elif i == 4:
                    scope = f"末批: 核心交易/清算({batch_tables}张表，约{per_batch_tb}TB) — 需较长停机窗口"
                else:
                    scope = f"第{i+1}批: 中间层({batch_tables}张表，约{per_batch_tb}TB)"
                batches.append({
                    "batch": i + 1,
                    "scope": scope,
                    "window": f"3-5天(含增量追平)",
                    "parallel_run_days": 7,
                })
            total_window_days = 45
            strategy = "分5批迁移: 先导速赢→中间层分批→核心业务最后迁移"
        elif capacity_tb >= 30:
            per_batch_tb = capacity_tb / 3
            batch_tables = round(table_count / 3)
            for i in range(3):
                scope = f"第{i+1}批: 约{batch_tables}张表({per_batch_tb}TB)"
                if i == 0:
                    scope = f"速赢批(首批): 报表/非核心({batch_tables}张表)"
                batches.append({"batch": i + 1, "scope": scope, "window": "2-3天"})
            total_window_days = 25
            strategy = "分3批: 先导速赢→批量迁移→核心表迁移"
        else:
            batches.append({"batch": 1, "scope": "全量迁移", "window": "周末窗口(2-3天)"})
            total_window_days = 10
            strategy = "一次性全量迁移+增量追平"

        return {
            "strategy": strategy,
            "batches": batches,
            "total_window_days": total_window_days,
            "schema_count": schema_count,
            "etl_task_count": etl_task_count,
            "precheck": [
                "每批迁移前完成L1-L3数据一致性校验",
                "每批迁移后安排1-2周并行观察期",
                "核心业务迁移前需完成至少2次演练",
                "建议每批迁移预留20%的缓冲时间",
            ],
        }
