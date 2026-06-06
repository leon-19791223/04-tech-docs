# 迁移智能评估系统

> 多源数据库到华为 DWS 的迁移评估引擎。支持 Oracle、MySQL、DB2、Teradata、Greenplum、SQL Server 六大源端。
> **独立项目**，与其他子项目无依赖。

## 技术栈

- **语言**：Python 3
- **架构**：规则引擎 + Scanner 扫描器
- **用途**：评估源数据库迁移到 DWS 的兼容性、改造工作量、风险点

## 目录结构

```
迁移智能评估系统/
├── core/               # 核心引擎
├── rules/              # 迁移规则（按源端分类）
│   ├── oracle_to_dws/
│   ├── mysql_to_dws/
│   ├── db2_to_dws/
│   ├── teradata_to_dws/
│   ├── gp_to_dws/      # Greenplum
│   └── mssql_to_dws/   # SQL Server
├── scanners/           # 数据库扫描器
└── templates/          # 报告模板
```

## 快速开始

```bash
python -m core.scanner --help
```

## 支持的目标

| 源数据库 | 规则目录 |
|---------|---------|
| Oracle | `rules/oracle_to_dws/` |
| MySQL | `rules/mysql_to_dws/` |
| DB2 | `rules/db2_to_dws/` |
| Teradata | `rules/teradata_to_dws/` |
| Greenplum | `rules/gp_to_dws/` |
| SQL Server | `rules/mssql_to_dws/` |

## 隔离说明

- 完整独立的规则引擎
- 不依赖 `04-技术文档` 下其他子项目
