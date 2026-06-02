# Z-DBMate 工具集 — 产品定位与能力边界

> **版本**: v0.2 (修正版)  
> **日期**: 2026-06-02  
> **背景**: 澄清 Z-DBMate 与 DWS 的产品边界，纠正此前混淆两者的错误分析

---

## ⚠️ 重要声明：产品区分

| 产品 | 全称 | 架构 | 适用场景 | 管理平台 | 对应版本 |
|------|------|------|---------|---------|---------|
| **GaussDB (OLTP)** | 云数据库 GaussDB 轻量化部署 | **单机/主备** | OLTP 交易型负载 | **TPOPS** | 24.x / 25.x |
| **DWS (MPP)** | GaussDB(DWS) 数据仓库 | **MPP 分布式** (CN/DN/GTM) | OLAP 分析型数仓 | **FusionInsight Manager** | 8.x / 9.x |

### Z-DBMate 的定位

**Z-DBMate 是 GaussDB OLTP（轻量化部署形态）的自动化部署工具集**，不是 DWS 的部署工具。

- ✅ 覆盖: TPOPS 安装 → GaussDB 单机/主备部署 → 生产验收


---

## Z-DBMate 当前能力边界

| 模块 | 内容 | 状态 |
|------|------|:----:|
| precheck.sh | 16项环境预检（面向 GaussDB OLTP 安装要求） | ✅ 当前 |
| deploy.sh | 5种场景（单/HA TPOPS + GaussDB OLTP） | ✅ 当前 |
| monitor.sh | 标记文件追踪 + 日志告警 | ✅ 当前 |
| PROD_CHECKLIST.md | GaussDB OLTP 生产检查 | ✅ 当前 |
| app.py (Web UI) | Flask 可视化 | ✅ 当前 |
| 配置模板 | GaussDB OLTP 配置字段 | ✅ 当前 |

### 可复用的共性能力

尽管 DWS 和 GaussDB OLTP 是不同产品，但在**OS 基础环境层面**有一些可复用的预检项：

| OS 层面检查项 | GaussDB OLTP | DWS | 说明 |
|-------------|:------------:|:---:|------|
| 磁盘数量/挂载 | ✅ | ✅ | 路径不同 |
| 时钟同步 | ✅ | ✅ | 通用 |
| 防火墙/SELinux | ✅ | ✅ | 通用 |
| ARM 架构支持 | ✅ | ✅ | 通用 |
| RAID 检查 | ✅ | ✅ | 通用 |
| BIOS 参数 | ❌ 缺 | ✅ | 可参考 |
| 磁盘/网络压测 | ❌ 缺 | ✅ | 可参考 |
| 内核参数调优 | ❌ 缺 | ✅ | 场景不同需区分 |

---

## 程曦 DWS 材料的处理建议

程曦发送的材料（DWS部署-V2.0.docx 等）是 **DWS MPP 产品** 的安装部署文档，与 Z-DBMate 的 GaussDB OLTP 定位不同。

**建议**：
1. **不直接整合到 Z-DBMate** — DWS 的安装方法论（FusionInsight Manager、preinstall.ini、手动分区等）与 TPOPS + GaussDB OLTP 差异很大
2. **作为独立的知识库参考** — 其中的 OS 参数调优、内核参数、RAID/BIOS 检查等底层部分可供借鉴
3. **预检脚本可参考** — DWS 要求的内核参数检查、swap 检查、IPv6 检查等也可在 GaussDB OLTP 侧增加

---

## 结论


1. ✅ GaussDB OLTP 预检项的完善（借鉴 DWS 的 OS 层面检查经验）
2. ✅ 多环境配置管理（DEV/TEST/PREPROD/PROD 配置切换）
3. ✅ ARM/x86 双架构兼容
4. ✅ 硬件预检增强（RAID/BIOS/磁盘健康度）
5. ❌ 不涉及 DWS MPP 集群部署

---

*修正版。如有其他需要明确的边界问题，请指正。*
