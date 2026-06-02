# Z-DBMate 部署配套工具集

## 概述

Z-DBMate 是 **GaussDB OLTP（轻量化部署形态）** 的自动化安装部署工具集。它基于华为 TPOPS + GaussDB 产品线，提供了 **预检、一键部署、进度监控、生产标准** 等配套能力，形成完整的部署流水线。

> ⚠️ **产品边界**：Z-DBMate 面向 **GaussDB OLTP（单机/主备）** 的轻量化部署场景，通过 TPOPS 管理平台安装。它与 **DWS (MPP 数据仓库)** 是不同产品线（DWS 使用 FusionInsight Manager，面向 OLAP 分析场景），请勿混淆。

```
┌────────────────────────────────────────────────────┐
│              Z-DBMate 部署流水线                    │
│           GaussDB OLTP 轻量化部署                   │
├──────────┬──────────┬──────────┬───────────────────┤
│ precheck  │ deploy   │ monitor  │ PROD_CHECKLIST   │
│ 部署前预检 │ 一键部署  │ 进度监控  │ 生产标准          │
└──────────┴──────────┴──────────┴───────────────────┘
```

## 目录结构

```
Z-DBMate工具集/
├── README.md                   ← 本文件
├── scripts/
│   ├── precheck.sh             ← 部署前预检脚本
│   ├── deploy.sh               ← 一键部署封装脚本
│   └── monitor.sh              ← 进度监控脚本
├── conf/
│   ├── user_edit_file.template.conf  ← 配置模板
│   └── environments            ← 环境配置示例
└── docs/
    └── PROD_CHECKLIST.md       ← 生产环境检查清单
```

## 快速使用

### Step 1: 环境预检

```bash
cd Z-DBMate工具集/scripts

# 方式一：从配置文件自动读取IP
bash precheck.sh

# 方式二：手动指定节点IP
bash precheck.sh 26.x.x.41 26.x.x.44 26.x.x.45 26.x.x.46
```

### Step 2: 一键部署

```bash
# root模式（自动）
bash deploy.sh -m root -r "YourRootPass" -s "单节点TPOPS+三节点GaussDB"

# service模式
bash deploy.sh -m service -p "ServicePass" -s "单节点TPOPS+三节点GaussDB"

# 仅预检
bash deploy.sh --check
```

### Step 3: 监控进度

```bash
# 持续监控（每5秒刷新）
bash monitor.sh --tail

# 一次性检查
bash monitor.sh --once
```

### Step 4: 生产验收

参考 `docs/PROD_CHECKLIST.md` 逐项确认。

> **产品边界提醒**：Z-DBMate 是 **GaussDB OLTP（轻量化部署）** 工具集。DWS (MPP数仓) 和 MRS (大数据平台) 是另外的产品线，不在此工具集覆盖范围内。

## 场景速查

| 场景 | 配置文件 | 部署命令 |
|------|----------|---------|
| **单节点TPOPS + 三节点GaussDB (OLTP)** | `single_tpops_gaussdb_user_edit_file.conf` | `deploy.sh -s "单节点TPOPS+三节点GaussDB"` |
| **HA TPOPS + 三节点GaussDB** | `ha_tpops_gaussdb_user_edit_file.conf` | `deploy.sh -s "HA TPOPS+三节点GaussDB"` |
| **仅单节点TPOPS** | `single_tpops_user_edit_file.conf` | `deploy.sh -s "仅TPOPS"` |
| **仅HA TPOPS** | `ha_tpops_user_edit_file.conf` | `deploy.sh -s "仅HA TPOPS"` |
| **仅准备GaussDB环境** | `prepare_gaussdb_user_edit_file.conf` | `deploy.sh -s "仅GaussDB"` |

## 执行模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **root** | 全程使用 root 用户执行 | 所有机器root密码一致、安全策略允许 |
| **service** | root准备环境 → service用户安装 | 安全要求高、需控制权限 |

## 与迁移评估系统集成

Z-DBMate 部署工具集可与迁移智能评估系统联动，形成完整的"评估→迁移→部署"工具链：

```
迁移智能评估系统                  Z-DBMate工具集
┌─────────────────┐           ┌─────────────────┐
│ Phase 1-2       │           │ precheck.sh     │
│ 调研评估 + 兼容性 │──────────→│ 环境预检         │
└─────────────────┘           └─────────────────┘
         │                             │
         ▼                             ▼
┌─────────────────┐           ┌─────────────────┐
│ Phase 3-4       │           │ deploy.sh       │
│ POC验证 + 迁移   │──────────→│ TPOPS+GaussDB   │
└─────────────────┘           │ 一键部署         │
         │                    └─────────────────┘
         ▼                             │
┌─────────────────┐           ┌─────────────────┐
│ Phase 5-6       │           │ monitor.sh      │
│ 测试 + 割接上线  │──────────→│ 部署监控+验证    │
└─────────────────┘           └─────────────────┘
```

### 典型场景联动

```bash
# 1. 先评估源数据库到目标数据库的迁移兼容性
#    迁移评估系统 → 生成评估报告

# 2. 部署 GaussDB 目标环境（如未部署）
bash scripts/deploy.sh -m root -r "密码" -s "单节点TPOPS+三节点GaussDB"

# 3. 监控部署进度
bash scripts/monitor.sh --tail

# 4. 部署完成后，在 TPOPS 上安装 GaussDB 实例
#    https://IP:8002/gaussdb/ → 添加主机 → 安装实例

# 5. 回到迁移评估系统，执行正式迁移
#    使用 DRS/DataX 将数据从源数据库迁移到 GaussDB
```

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v2.1 | 2026-06 | 明确产品定位（GaussDB OLTP 轻量化部署，≠ DWS MPP）；修正分析文档 |
| v2.0 | 2026-06 | 适配 GaussDB 25.1.32 官方规范: 配置模板20+字段、预检16项、部署指南 |
| v1.0 | 2026-06 | 初始版本：预检 + 部署 + 监控 + 检查清单 |
