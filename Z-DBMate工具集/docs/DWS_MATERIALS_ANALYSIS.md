# 程曦 DWS 安装部署材料 — 独立分析报告

> **分析日期**: 2026-06-02  
> **材料来源**: 程曦（邮件/微信发送）  
> **说明**: 以下材料属于 **DWS (MPP数仓)** 产品线，与 **Z-DBMate（GaussDB OLTP）** 为不同产品，本报告仅作独立分析与知识储备。

---

## ⚠️ 产品边界声明

| | 本报告分析对象 | 非适用范围 |
|--|---------------|-----------|
| **产品** | DWS (MPP 数据仓库) | GaussDB OLTP 轻量化部署 |
| **部署方式** | FusionInsight Manager + SetupTool | TPOPS |
| **架构** | 分布式 (CN/DN/GTM) | 单机/主备 |
| **适用工具** | 程曦提供的操作手册 | **Z-DBMate** 工具集 |

**本报告独立于 Z-DBMate 工具集存在**，程曦的 DWS 材料与 Z-DBMate 不应直接融合。

---

## 一、材料清单

| # | 文件 | 类型 | 内容侧重 | 质量评估 |
|---|------|------|---------|:--------:|
| 1 | DWS部署-V2.0.docx | 操作手册 | 全流程安装操作 | ⭐⭐⭐⭐ |
| 2 | DWS安装v1.0.docx | 操作手册 | 安装步骤+问题记录 | ⭐⭐⭐⭐ |
| 3 | GaussDB集群安装步骤.docx | 专项指导 | 网卡Bond+手动分区 | ⭐⭐⭐ |
| 4 | DWS部署配置参考.xlsx | 配置模板 | 硬件规格/分区/IP规划 | ⭐⭐⭐⭐⭐ |
| 5 | 大数据平台DWS&MRS-DEV,SIT,UAT规划..xlsx | 环境规划 | 多环境设备/网络/机柜 | ⭐⭐⭐⭐⭐ |
| 6 | dws_job--安装流程.xls | 流程表格 | 安装工序分解 | ⭐⭐⭐ |
| 7 | dws_setup-安装流程.xls | 流程表格 | 设置工序分解 | ⭐⭐⭐ |

---

## 二、逐项内容分析

### 1. DWS部署-V2.0.docx ⭐⭐⭐⭐

**内容结构**：较为完整的 DWS 安装操作手册，流程如下：

```
安装前检查 → OS配置 → BIOS优化 → 网卡配置 → RAID策略 
→ 内核参数 → 磁盘分区/挂载 → 性能压测 → Python3.8 
→ 参数调优 → Manager安装 → 集群安装
```

**核心价值**：
- ✅ 安装前检查清单（磁盘/网卡/ISO/连通性/密码一致性）
- ✅ OS 层完整配置项（audit/防火墙/SELinux/swap/字符集）
- ✅ BIOS 优化参数（NUMA均衡/透明大页/节能模式/C-state）
- ✅ 网卡 Hi1822 中断优化
- ✅ RAID 策略（Read Ahead + Write Back With BBU）
- ✅ **fio 磁盘压测 + 网络压测（speed_test + sar + gsar）** 脚本完整，可直接使用
- ✅ 内存参数推荐值（256GB→cstore_buffers CN=1GB/DN=8GB；512GB→CN=2GB/DN=16GB）
- ✅ 性能测试需关闭的参数清单（autovacuum/audit/ssl/log）
- ✅ preinstall.ini 配置示例（`g_parted=3` 手动分区、ARM 平台标识）
- ✅ 磁盘 parted + mkfs.xfs + blkid + fstab 完整命令链

**不足**：
- ❌ 无版本号标注（跨 DWS 8.2.1 / 9.1.0，部分命令不通用）
- ❌ 无测试/生产环境参数差异说明
- ❌ 无回滚/卸载步骤
- ❌ 步骤顺序可优化（先装 Python3.8 后又改 yum 源）

---

### 2. DWS安装v1.0.docx ⭐⭐⭐⭐

**核心价值** — 实战排坑记录是最大亮点：

**文档中的实际踩坑问题**：

| 问题 | 根因 | 解决方法 |
|------|------|---------|
| 浮动IP报错 | 网卡未释放 | `ifdown/ifup` 重新获取 |
| Excel 模板报错 | 模板与版本不匹配 | 手动安装，不选模板 |
| sudoExecute.sh 报错 | 未更新 sudo 脚本 | 执行 `optimization_patch.sh install` |
| 磁盘权限问题 | 数据目录 owner 为 root | `chown omm:wheel` |
| Manager 重装报错 | omm.keytab not created | 检查浮动IP状态 |
| krb5kdc port 21701 | 端口被占用 | `netstat -nltp` 排查 |
| 安装卡住不报错 | 时区不一致 | 检查时区，统一为 Asia/Shanghai |

**日志目录汇总**（DWS 运维参考）：

```
/tmp/fi-preinstall.log                              → Preinstall 日志
/opt/FusionInsight_SetupTool/precheck/log/          → Precheck 日志
/var/log/Bigdata/controller/scriptlog/install.log   → Manager 安装日志
/var/log/Bigdata/mpp/scriptlog/postinstall.log      → 集群安装日志
/var/log/Bigdata/mpp/omm/pg_log/                    → CN/DN 实例日志
/var/log/Bigdata/mpp/omm/cm/                        → CM 集群日志
```

**不足**：
- 文档结构较乱，有重复内容和跳跃
- 分区部分只有 mkdir，缺少 parted/fdisk 命令
- 无自动化封装

---

### 3. GaussDB集群安装步骤.docx ⭐⭐⭐

**专项解决方法**：

**问题1**: TAISHAN200 ARM 服务器不支持 bond mode=4
- 解决: 改用 `mode=802.3ad`
- 完整 bond 配置脚本（可作独立脚本使用）

**问题2**: 3节点管理/控制/数据合一场景的手动分区
- RAID 异构处理（各节点 RAID 类型不同时配置 `preinstall.ini`）
- 手动 parted 分区示例（600G raid1 拆 2×278G 给元数据）
- 挂载脚本 + fstab 配置

---

### 4. DWS部署配置参考.xlsx ⭐⭐⭐⭐⭐

**DWS 生产环境的可直接参考模板**：

| 表 | 内容 |
|----|------|
| 硬件规格 | 管控节点(2台): 2*32C/256G/2*480G+4*960G SSD；数据节点(5台): 2*48C/512G/2*960G+20*3.84T SSD |
| 操作系统 | 银河麒麟 V10 SP2（20210524） |
| 分区规划 | 管理节点 /dbdata_om(≥300G) + /LocalBackup(≥300G)，数据节点 /mppdb/data(≥500G×4) |
| IP 规划 | 管理平面 10.141.45.x + 业务平面 10.141.44.x |
| 浮动IP | OMSServer / OMWebService / LVS |

---

### 5. 大数据平台规划..xlsx ⭐⭐⭐⭐⭐

完整 DWS+MRS 混合架构硬件规划（20台服务器 + 8台交换机 + 2台防火墙）：

| 设备类型 | 用途 | 配置 | 数量 |
|---------|------|------|:----:|
| 管控/流计算节点 | MRS管控+流计算 | 2*32C/256G/2*480G+4*960G | 8 |
| 离线计算节点 | MRS批处理 | 2*32C/512G/2*480G+12*8T | 3 |
| 数仓管理节点 | DWS管控 | 2*32C/256G | 2 |
| 数仓数据节点 | DWS计算 | 2*48C/512G/2*480G+12*3.84T SSD | 3 |
| 数据治理节点 | 数据治理平台 | 2*24C/128G/960G | 4 |

---

## 三、可作为独立工具脚本的产出

下列内容可以从 DWS 材料中抽离为**独立工具脚本**（不依赖 DWS/Z-DBMate 任何产品）：

| 脚本 | 来源 | 用途 |
|------|------|------|
| `benchmark_disk.sh` | DWS部署-V2.0.docx | fio 磁盘压测 |
| `benchmark_net.sh` | DWS部署-V2.0.docx | speed_test 网络压测 |
| `net_tune.sh` | GaussDB集群安装步骤.docx | ARM 网卡 bond 配置 |
| `os_check.sh` | DWS部署-V2.0.docx | OS 参数检查（内核/numa/大页/swap） |
| `gen_partition.sh` | DWS部署-V2.0.docx | parted 分区+fstab 生成 |

---

## 四、总体评价

### 优势
1. **实战性强** — 文档来自嘉兴银行现场实施，踩坑记录真实可靠
2. **覆盖度好** — 硬件→OS→网络→BIOS→磁盘→安装→调优→排错全流程
3. **配置模板价值高** — 可直接复用于其他 DWS 项目

### 不足
1. **标准化低** — 笔记风格，结构随意，多版本混用
2. **纯手工** — 无自动化，不适合重复部署
3. **场景单一** — 仅适用于 DWS MPP，非通用数据库部署方案

---

*本报告仅对程曦发送的 DWS 安装部署材料做独立内容分析，不涉及与 Z-DBMate（GaussDB OLTP）的融合或迁移建议。*
