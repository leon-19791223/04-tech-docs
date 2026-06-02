# DWS 部署工具集

> **产品范围**: GaussDB(DWS) 数据仓库 MPP 集群部署  
> **管理平台**: FusionInsight Manager  
> **适用版本**: DWS 8.x / 9.x  
> **与 Z-DBMate 的区别**: Z-DBMate 面向 GaussDB OLTP（TPOPS管理），此工具面向 DWS MPP 数仓（FusionInsight管理）

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

## 目录结构

```
DWS部署工具集/
├── README.md                   ← 本文件
├── scripts/
│   ├── preinstall_check.sh     ← FusionInsight 安装前检查脚本
│   └── dws_postcheck.sh        ← DWS 部署后验证脚本
├── conf/
│   └── preinstall.ini.template ← FusionInsight 配置模板
└── docs/
    └── DWS_DEPLOY_FLOW.md      ← DWS 部署流程文档
```

## 使用方式

```bash
# 1. 安装前检查
bash scripts/preinstall_check.sh node1 node2 node3

# 2. 配置 preinstall.ini
cp conf/preinstall.ini.template conf/preinstall.ini
vi conf/preinstall.ini

# 3. 执行 FusionInsight 安装
# 参考 docs/DWS_DEPLOY_FLOW.md
```

## 与迁移评估系统联动

```bash
# Step 1: 评估源库到 DWS 的兼容性
cd 迁移智能评估系统
python main.py --path oracle_dws -o Oracle到DWS评估报告.docx

# Step 2: DWS 环境部署（本工具集）
cd ../DWS部署工具集
bash scripts/preinstall_check.sh 192.168.x.x
# 部署过程参考 docs/DWS_DEPLOY_FLOW.md

# Step 3: 数据迁移
# DRS/DataX 从源库迁移数据到 DWS

# Step 4: 应用割接
gsql -d postgres -h 192.168.x.x -p 40080 -U root
```
