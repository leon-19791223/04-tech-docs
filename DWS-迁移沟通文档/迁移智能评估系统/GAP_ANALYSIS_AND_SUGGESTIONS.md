# 迁移智能评估系统 vs DWS资料 — 对比分析与完善建议

> **日期**: 2026-06-04  
> **对比参照**: D:\BaiduNetdiskDownload 中 10+ 份 DWS 相关文档  
> **现有系统**: 迁移智能评估系统（规则引擎+Flask Web）

---

## 一、现有迁移评估系统能力总览

### 1.1 已支持迁移路径

| 源端 | 目标端 | 规则覆盖 |
|------|:------:|:--------:|
| Greenplum (GP) | DWS | ✅ DDL/数据类型/函数/UDF/扩展/ETL/调度/BI |
| Oracle | DWS | ✅ DDL/数据类型/PLSQL/扩展/**Exadata**/安全/字符集/应用层/事务/CDC |
| MySQL | DWS | ✅ DDL/数据类型/函数/扩展/通用/PSM |
| SQL Server (MSSQL) | DWS | ✅ DDL/数据类型/函数/扩展/通用/TSQL |
| DB2 (LUW) | DWS | ✅ DDL/数据类型/函数/扩展/通用/SQLPL |
| Teradata | DWS | ✅ DDL/数据类型/函数/通用 |

### 1.2 核心能力

| 模块 | 能力 | 成熟度 |
|------|------|:------:|
| **规则引擎** | 6个源端→DWS的兼容性规则，按DDL/数据类型/函数等分类 | ★★★★☆ |
| **扫描器** | 从Excel调研模板解析源端元数据 | ★★★☆☆ |
| **容量规划** | 基于数据量推荐DWS集群规格（鲲鹏/X86/VM三种规格） | ★★★☆☆ |
| **竞品对比** | DWS vs KDW/OushuDB/Cloudberry | ★★★☆☆ |
| **分批迁移** | 按容量自动建议迁移批次（1/3/5批） | ★★★☆☆ |
| **评估报告** | Word文档输出+Web UI | ★★★☆☆ |
| **安全/字符集/应用层** | Oracle方向新增字段 | ★★★★☆ |

### 1.3 架构示意图

```
用户调研表/Excel
     │
     ▼
Scanner层 ──→ MigrationMetadata (统一元数据模型)
     │
     ▼
Rule Engine ──→ 各类兼容性规则 (DDL/数据类型/函数/...)
     │
     ▼
Analyzer ──→ AssessmentResult (评分+发现+建议)
     │
     ├── CapacityPlanner (容量规划)
     ├── CompetitorCompare (竞品对比)
     └── ReportGenerator (报告输出)
```

---

## 二、D盘DWS材料的可用价值分析

在 `D:\BaiduNetdiskDownload` 中发现的 DWS 相关文件，可以分为以下5类进行对比：

### 2.1 高价值直接可用素材

| 文件 | 位置 | 可补充到评估系统的内容 |
|------|------|----------------------|
| **某券商GaussDB(DWS)测试报告v1.docx** | D盘根目录 | **POC 验证用例库** — 10大类60+项测试用例 |
| **DWS集群规划及环境配置.docx** | D盘根目录 | **目标端部署基线** — 网络/RAID/OS/分区规划标准 |
| **DWS客户业务调研表 - 前期调研.xlsx** | D盘根目录 | **调研模板** — 已有平台/新建平台/数据链路三张表 |
| **DWS交付checklist套件.rar** | D盘根目录 | **交付验收清单** |

### 2.2 可参考的案例素材

| 文件 | 用途 |
|------|------|
| 中金财富证券DWS迁移项目方案沟通-1120.pptx | 券商DWS迁移方案结构参考 |
| 稠州银行GaussDB(DWS)数据库迁移解决方案.pptx | 银行DWS迁移方案结构参考 |
| 某金融机构GaussDB(DWS)测试成果分享-20231020.pptx | DWS实际测试数据 |
| 某证券数据仓库迁移案例.pdf | 券商数仓迁移案例 |
| 金融数据仓库Greenplum迁移案例.pdf | Greenplum迁移实战 |

### 2.3 评估系统当前缺失（但D盘资料可补）

| 缺失项 | D盘资料 | 补充价值 |
|--------|---------|:--------:|
| **POC验证用例库** | 某券商测试报告的60+用例 | 评估报告可增加"POC验证建议"章节 |
| **目标端部署规划** | DWS集群规划文档 | 容量规划可参考实际部署参数 |
| **交付验收清单** | DWS交付checklist | 评估→部署→验收全流程闭环 |
| **迁移案例库** | 4份券商/银行案例 | 评估报告可引用相似案例 |
| **硬件配置模板** | 鲲鹏920/960G+3.84T SSD 规格 | 容量规划可增加实际配置 |

---

## 三、差距分析

### 差距1 [严重]：缺少 POC 验证用例库

**现状**: 评估系统输出"兼容性评分"和"风险项"，但不包含POC阶段应验证的具体测试用例。

**DWS测试报告价值**: 包含完整的10大类测试用例：

| 测试大类 | 子项数 | 可补充到评估系统的价值 |
|---------|:------:|----------------------|
| 基本功能（DDL/DML/DCL/数据类型/序列/运算/函数） | 20+ | 列为"L1基础验证"用例 |
| 高级功能（兼容模式/全文检索/视图/存储过程/Hint） | 10+ | 列为"L2高级特性"用例 |
| 安全性（加密/脱敏/三权分立/行级访问控制） | 6 | 列为"L3安全验证"用例 |
| TPCH Benchmark | 1 | 列为"L4性能基准" |
| 资源管理（隔离/异常/空间管控） | 3 | 列为"运维验证" |
| 可靠性（硬件故障/事务/锁） | 3 | 列为"高可用验证" |
| 业务适配（报表/大表查询/采集工具） | 6 | **最重要的业务验证** |

**建议**: 如果在评估报告中增加"POC测试建议"章节，根据源端特征自动推荐所需测试用例。

---

### 差距2 [中]：调研模板不统一

**现状**: 评估系统有 `DWS客户业务调研表 - 前期调研.xlsx`（D盘找到的），但系统自身的扫描器(GPScanner/OracleScanner)是各自独立解析Excel，没有统一的调研模板标准。

**调研表包含**：
- ✅ Hadoop信息收集（组件/节点/存储/计算）
- ✅ 已有平台业务调研（数据来源/接入/数仓/业务场景/容灾）
- ✅ 新建平台调研（未来规划）
- ✅ 已有平台数据链路图

**两者对比**:

| 评估项 | 现有评估系统 | DWS调研表 | 差距 |
|--------|:-----------:|:---------:|:----:|
| 源端数据库版本 | ✅ | ✅ | — |
| 表/视图/函数数量 | ✅ | ❌ | 调研表缺此字段 |
| 集群规模/容量 | ✅ | ✅ | — |
| ETL工具 | ✅ | ✅ | — |
| BI工具 | ✅ | ✅ | — |
| 业务场景描述 | ❌ | ✅ | **系统缺此字段** |
| 数据链路图 | ❌ | ✅ | **系统缺此字段** |
| 数据接入频率/方式 | ❌ | ✅ | **系统缺此字段** |
| 存量/增量数据量 | ❌ | ✅ | **系统缺此字段** |
| 典型SQL样例 | ❌ | ✅ | **系统缺此字段** |
| 业务痛点 | ❌ | ✅ | **系统缺此字段** |

**建议**: 将DWS调研表整合为评估系统的统一调研模板，补充业务场景、数据链路、典型SQL等字段。

---

### 差距3 [中]：缺失硬件配置参考

**现状**: 容量规划器的 `SERVER_SPECS` 硬编码了3种规格（鲲鹏基础型/增强型/x86通用型），规格参数与实际项目有差异。

**DWS规划文档的实际配置**:

```
管控+数据节点: 2*960GB SSD(RAID1 OS) + 12*3.84TB SSD(RAID0 数据)
纯数据节点:    2*960GB SSD(RAID1 OS) + 12*3.84TB SSD(RAID0 数据)
网络: 双平面(业务bond4 + 管理bond1)
OS:  Kylin V10 SP2 aarch64
```

**系统当前规格对比**:

| 维度 | 评估系统容量规划器 | DWS实际部署 | 差距 |
|------|:-----------------:|:----------:|:----:|
| 节点角色拆分 | 仅分管理/数据/备用 | 管控+数据合一的混合节点 | 系统未考虑混合节点模式 |
| RAID策略 | 假设RAID5 | OS盘RAID1 + 数据盘RAID0 | **系统RAID假设不一致** |
| 网络规划 | 无 | 双平面Bond4+Bond1 | 系统完全缺失 |
| OS分区 | 无 | / /tmp /var /srv/BigData 详细规划 | 系统完全缺失 |
| 3节点最小部署 | 无 | DWS测试集群标配 | 系统未覆盖 |

---

### 差距4 [中]：竞品对比不够全面

**现状**: 竞品对比只有3家（金山云KDW/OushuDB/Cloudberry）。

**应增加**:

| 竞品 | 来源依据 | 对比价值 |
|------|---------|---------|
| **达梦8** | D盘"5-达梦数据同步软件DMHS.pdf" | 国产数据库主要竞品 |
| **Goldilocks** | — | 证券行业真实竞品 |
| **K-DB / TiDB** | — | OLTP/HTAP场景竞品 |
| **Greenplum (开源)** | D盘丰富资料 | GP已有客户如何选择升级路径 |

---

### 差距5 [低]：缺少交付验收闭环

**现状**: 评估系统输出评估报告即结束，没有与后续的部署/验收环节打通。

**DWS交付checklist套件** 包含：
- 部署前环境检查清单
- 安装过程记录表
- 功能验证确认表
- 性能测试记录表
- 交付签字确认表

**建议**: 评估报告末尾增加"后续行动清单"，引导用户进入部署和验收阶段。

---

## 四、完善建议方案

### 优先级 P0（对评估质量影响最大）

**1. 整合调研模板** ⭐⭐⭐⭐⭐

将 `DWS客户业务调研表 - 前期调研.xlsx` 纳入评估系统的统一调研流程：

```
用户填写调研表（标准化模板）
    │
    ▼
Scanner解析 → MigrationMetadata（补充业务场景/典型SQL/数据链路字段）
    │
    ▼
规则引擎评估 → 更准确的兼容性判定
```

**改动量**: 小。修改 `MigrationMetadata` 增加字段 + 统一 Scanner 解析逻辑。

---

**2. 增加 POC 测试建议模块** ⭐⭐⭐⭐⭐

基于 DWS测试报告 的60+用例，在评估结果中增加"POC验证建议"：

```
评估结果
  ├── 兼容性评分
  ├── 风险项
  ├── 容量规划
  ├── POC测试建议  ← 新增
  │    ├── L1基础验证 (必选)
  │    ├── L2业务适配 (根据源端特征推荐)
  │    ├── L3性能基准 (需要基准数据时)
  │    └── L4高可用验证 (生产环境必须)
  └── 迁移策略
```

**改动量**: 中。新增一个 `PocTestPlanner` 模块，联动规则引擎的结果来自动推荐测试用例。

---

### 优先级 P1（提升专业度）

**3. 容量规划器升级** ⭐⭐⭐⭐

基于 DWS规划文档 的实际部署参数：

- 增加节点角色: 管控+数据混合模式
- 修正RAID策略: OS盘RAID1 + 数据盘RAID0
- 增加网络规划建议（双平面Bond4+Bond1）
- 增加OS分区建议
- 增加3节点最小测试集群场景

**改动量**: 中。修改 `CapacityPlanner` 类的 `SERVER_SPECS` 和 `recommend_config` 方法。

**4. 竞品对比扩展** ⭐⭐⭐⭐

- 增加达梦8、K-DB、TiDB、Greenplum升级路径
- 增加对比维度: 信创认证等级、迁移难度、运维成本
- 基于D盘案例库增加行业客户分布统计

**改动量**: 小。修改 `CompetitorCompare` 类。

---

### 优先级 P2（持续完善）

**5. 交付验收闭环** ⭐⭐⭐

- 评估报告增加"后续行动清单"
- 参考 DWS交付checklist 生成部署前检查项
- 接入 Z-DBMate 预检结果（联动）

**改动量**: 大，涉及跨工具集联动。

**6. 迁移案例库** ⭐⭐⭐

- 从 D盘资料 提取典型迁移案例
- 按行业（证券/银行/基金）分类
- 评估报告中自动匹配相似案例

**改动量**: 中，新增案例数据模块。

---

## 五、具体改进行动项

### 5.1 调研模板统一

```python
# core/models.py 需补充的字段
@dataclass
class MigrationMetadata:
    # ... (已有字段)
    
    # === 新增: 来自DWS调研表 ===
    # 业务场景
    business_scenarios: list = field(default_factory=list)  # 业务场景描述
    has_data_link_diagram: bool = False     # 是否有数据链路图
    pain_points: list = field(default_factory=list)  # 当前痛点
    
    # 数据接入
    source_system_count: int = 0           # 源系统数量
    data_source_types: list = field(default_factory=list)  # 源端数据库类型列表
    data_ingestion_tool: str = ""          # 数据接入工具
    ingestion_frequency: str = ""          # 接入频率
    incremental_data_daily_gb: float = 0.0 # 日增量数据量(GB)
    
    # 典型SQL
    sample_sql_count: int = 0              # 典型SQL数量
    has_typical_sql: bool = False          # 是否提供了典型SQL
    
    # 网络与硬件
    network_architecture: str = ""         # 网络架构
    server_hardware: str = ""              # 服务器硬件规格
```

### 5.2 POC测试建议模块

```python
class PocTestPlanner:
    """POC测试用例推荐器"""
    
    # 从DWS测试报告提取的测试用例库
    TEST_CASES = {
        "basic_ddl_dml": {
            "name": "DDL/DML基础功能",
            "level": "L1",
            "always_required": True,
            "estimated_hours": 2,
        },
        "data_type_compat": {
            "name": "数据类型兼容性",
            "level": "L1",
            "always_required": True,
            "estimated_hours": 1,
        },
        "business_adaptation": {
            "name": "业务SQL适配",
            "level": "L2",
            "always_required": True,
            "estimated_hours": 8,  # 业务SQL验证通常需要1天
        },
        "etl_tool_test": {
            "name": "ETL工具迁移验证",
            "level": "L2",
            "trigger_on_tool": ["Kettle", "Informatica", "ODI"],
            "estimated_hours": 4,
        },
        "concurrent_test": {
            "name": "并发压力测试",
            "level": "L3",
            "trigger_on_capacity_tb": 10,  # >10TB建议做
            "estimated_hours": 8,
        },
        "high_availability": {
            "name": "高可用/故障切换",
            "level": "L4",
            "trigger_on_production": True,
            "estimated_hours": 4,
        },
        "disaster_recovery": {
            "name": "容灾切换演练",
            "level": "L4",
            "trigger_on_production": True,
            "estimated_hours": 8,
        },
    }
    
    @classmethod
    def recommend(cls, metadata: MigrationMetadata, 
                  assessment: AssessmentResult) -> list:
        """根据源端特征和评估结果推荐POC测试用例"""
        pass
```

### 5.3 容量规划器修正

```python
# 根据DWS实际部署基线修正
SERVER_SPECS = {
    "dws_3node_test": {  # 新增: 3节点测试集群
        "name": "DWS 标准测试集群",
        "cpu": "2*32Core Kunpeng 920",
        "memory": "256GB",
        "disk_os": "2*960GB SSD (RAID1)",
        "disk_data": "12*3.84TB SATA SSD (RAID0)",
        "os_partition": "/20G /tmp10G /var30G /var/log130G /srv/BigData60G",
        "network": "双平面25GE (业务bond4+管理bond1)",
        "nodes": "2管控+数据 + 1数据 = 3节点",
        "scenario": "POC/测试环境最小配置",
    },
    # ... 保留原有的规格，补充OS分区和网络参数
}
```

---

## 六、总结

| # | 改进项 | 来源 | 优先级 | 改动量 |
|---|--------|------|:------:|:------:|
| 1 | 整合DWS调研模板 | DWS客户业务调研表.xlsx | 🔴 P0 | 小 |
| 2 | 增加POC测试建议模块 | 某券商DWS测试报告 | 🔴 P0 | 中 |
| 3 | 容量规划器升级（RAID/网络/分区） | DWS集群规划及环境配置.docx | 🟡 P1 | 中 |
| 4 | 竞品对比扩展（达梦/TiDB/GP升级） | D盘多份竞品资料 | 🟡 P1 | 小 |
| 5 | 交付验收闭环 | DWS交付checklist套件 | 🟢 P2 | 大 |
| 6 | 迁移案例库 | 券商/银行案例文件 | 🟢 P2 | 中 |

**最关键建议**: 先做 #1 和 #2 — 统一调研模板 + 增加POC测试建议，这两项对提升评估报告的专业度和实用性最直接。

---

*本报告基于迁移智能评估系统 v2.x 源码与 D:\BaiduNetdiskDownload 中的 DWS 相关文档对比生成。*
