# DWS 部署工具集

> **产品范围**: GaussDB(DWS) 数据仓库 MPP 集群部署  
> **管理平台**: FusionInsight Manager  
> **适用版本**: DWS 8.x / 9.x  
> **访问地址**: http://127.0.0.1:5053  
> **项目状态**: 正在整合嘉兴银行 DWS-POC 引擎，升级为"可视化部署向导 + 可执行引擎"

---

## 三系统联动

```
迁移智能评估系统              Z-DBMate (OLTP)              DWS 部署工具 (MPP)
┌──────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│ 评估兼容性        │        │ GaussDB OLTP部署  │        │ DWS 数仓部署      │
│ GP/Oracle/MySQL  │        │ TPOPS管理        │        │ FusionInsight    │
│ → DWS            │        │ 单机/主备         │        │ MPP集群          │
│ → GaussDB OLTP   │        │ OLTP场景          │        │ OLAP场景          │
└──────────────────┘        └──────────────────┘        └──────────────────┘
         ↓ 评估通过                 ↓ 环境就绪                 ↓ 环境就绪
    ────────────  DRS/DataX 数据迁移 ────────────
```

---

## 目录结构

```
DWS部署工具集/
├── app.py                     # Flask 主入口
├── engine/                    # ⭐ 核心引擎
│   ├── core_engine.py         # 嘉兴银行 DWS-POC 引擎（8阶段部署流+环境预设+LLD模板）
│   ├── ssh_executor.py        # SSH 执行器（双模式：demo/ssh）
│   └── report_generator.py    # 交付报告生成器
├── core/                      # 规则模块
│   ├── precheck_engine.py     # 预检规则（17项→持续扩展中）
│   └── verifier.py            # 部署后验证规则（10项）
├── scripts/
│   ├── precheck_fusion.sh     # FusionInsight 安装前检查脚本
│   └── (更多脚本待添加)
├── templates/                 # 12个模板
│   ├── base.html              # 布局骨架（深蓝主题）
│   ├── dws_dashboard.html     # 仪表盘
│   ├── dws_precheck.html      # 环境预检
│   ├── dws_config.html        # LLD配置生成（60+参数表单）
│   ├── dws_phase.html         # 步骤执行交互
│   ├── dws_templates.html     # 8种配置模板预览
│   ├── dws_audit.html         # 部署审计日志
│   ├── dws_architecture.html  # 动态架构图
│   ├── dws_equipment.html     # 设备清单+机柜布线
│   ├── dws_deploy.html        # 部署引导
│   ├── dws_verify.html        # 部署验证
│   ├── dws_flow.html          # 部署流程
│   └── dws_checklist.html     # 检查清单
├── conf/
│   └── preinstall.ini.template # FusionInsight 配置模板
├── docs/
│   └── DWS_DEPLOY_FLOW.md      # DWS 部署流程文档
├── REVISION_PLAN.md            # 修订路线图与回滚指南
└── README.md                   # 本文件
```

---

## 架构说明

### 数据流

```
用户 (Browser)
    │
    ▼
Flask Web UI (app.py)
    │
    ├── demo 模式（默认）── 模拟数据，展示界面
    │      └── 适用于：演示、培训、POC 展示
    │
    └── engine 模式（可选）── 真实数据，驱动执行
           ├── precheck_engine.py    → 17~40项环境预检
           ├── core_engine.py        → 8阶段部署流 + 环境切换
           ├── ssh_executor.py       → SSH 多节点执行
           ├── verifier.py           → 部署后验证
           └── report_generator.py   → 交付报告打包
```

### 执行模式

| 模式 | 说明 | 适用场景 |
|:-----|:------|:---------|
| **demo**（默认） | 数据显示、命令文本展示，无需 SSH | 演示/培训/界面预览 |
| **ssh** | 通过 paramiko 真实 SSH 执行命令 | 实际部署/预检执行 |
| **hybrid** | 能 SSH 的节点自动执行，不能的显示命令文本 | 混合环境/部分可达 |

---

## 核心能力

| 能力 | 说明 | 状态 |
|:-----|:------|:----:|
| **环境预检** | 17~40项检查（硬件/OS/网络/存储），双模式执行 | 🟡 扩展中 |
| **LLD配置生成** | 60+参数表单 → preinstall.ini / hosts / fstab / sysctl / grub / 分区脚本 | ✅ 可用 |
| **8阶段部署流** | 环境准备→OS调优→硬件验证→磁盘规划→网络验证→软件部署→预检查→部署OMS | ✅ 可用 |
| **环境切换** | 内置 DEV/SIT/UAT/PREPROD 四套预设，一键切换 | ✅ 可用 |
| **动态架构图** | 根据参数动态生成节点拓扑图（OM/CN/DN/GTM角色布局） | ✅ 可用 |
| **设备清单** | 按环境过滤显示服务器/网络/安全设备 + 机柜布线图 | ✅ 可用 |
| **审计日志** | 步骤级操作记录，时间戳+状态+输出 | ✅ 可用 |
| **SSH执行** | paramiko 驱动，多节点并行 | 🟡 开发中 |
| **交付报告** | 预检报告/审计日志/验证报告一键打包 | 🟡 计划中 |
| **工具链联动** | 与迁移评估系统、Z-DBMate 互相跳转 | 🟡 计划中 |

---

## 使用方式

```bash
# 启动
cd DWS部署工具集
python app.py
# → http://127.0.0.1:5053

# 环境切换（浏览器）
# http://127.0.0.1:5053/env/switch/DEV
# http://127.0.0.1:5053/env/switch/SIT
# http://127.0.0.1:5053/env/switch/UAT
# http://127.0.0.1:5053/env/switch/PREPROD

# 预检脚本（SSH直接执行）
bash scripts/precheck_fusion.sh node1 node2 node3
```

---

## 与迁移评估系统联动

```bash
# Step 1: 评估源库到 DWS 的兼容性
cd 迁移智能评估系统
python main.py --path oracle_dws -o Oracle到DWS评估报告.docx

# Step 2: DWS 环境部署（本工具集）
cd ../DWS部署工具集
python app.py
# → 打开 http://127.0.0.1:5053 → 配置→部署→验证

# Step 3: 数据迁移
# DRS/DataX 从源库迁移数据到 DWS

# Step 4: 应用割接
gsql -d postgres -h 192.168.x.x -p 40080 -U root
```

---

## 版本历史

| 版本 | 日期 | 说明 |
|:-----|:------|:------|
| v2.0 (规划中) | 2026-06 | 整合嘉兴引擎、SSH执行、预检扩展、交付报告 |
| v1.0 | 2026-06 | 初始版本：Web UI + Mock数据 + 17项预检 |

---

## 修订路线图

详细的 7 步修订计划和每步的回滚指南请参阅 [REVISION_PLAN.md](REVISION_PLAN.md)。

快速概览：

| 步骤 | 内容 | 预计工时 | Tag |
|:-----|:------|:--------:|:----|
| Step 0 | Git init + baseline | 5min | `dws-v0-baseline` |
| Step 1 | 导入嘉兴引擎 | 1天 | `dws-v1-engine-import` |
| Step 2 | 模板合并 | 1天 | `dws-v2-templates` |
| Step 3 | SSH执行引擎 | 2天 | `dws-v3-ssh-executor` |
| Step 4 | 预检扩展17→40项 | 1天 | `dws-v4-precheck-ext` |
| Step 5 | 交付报告生成 | 1天 | `dws-v5-report-gen` |
| Step 6 | 统一门户集成 | 0.5天 | `dws-v6-portal` |
| **合计** | | **约7.5天** | |
