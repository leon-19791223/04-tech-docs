# 04-技术文档 项目 Monorepo

> 这是华为 GaussDB/DWS 生态的技术文档、工具集和认证资料的 Monorepo。
> **注意**：本项目是一个聚合仓库，内部每个子项目有独立的 CLAUDE.md。
> 进入子目录工作前，建议先阅读对应子项目的 CLAUDE.md。

## 目录结构

```
04-技术文档/
├── DWS部署工具集/          # ⭐ 核心：DWS 自动化部署 CLI 工具（Python/Click）
├── DWS部署助手/            # DWS 部署 Web 图形化辅助工具
├── DWS-迁移沟通文档/
│   └── 迁移智能评估系统/    # ⭐ 核心：多源数据库到 DWS 的迁移评估引擎
├── Z-DBMate工具集/         # 数据库运维配套工具
├── 文档生成工具集/          # 自动化文档生成
├── 股票分析系统/            # 股票行情分析
├── SalesGPT/               # AI 辅助销售系统
├── portal/                 # Web portal
├── gaussdb_doc_extract/    # GaussDB 文档提取
├── HCCDE-GaussDB题库系统/   # 认证考试刷题系统（Python 桌面应用）
├── HCCDE-GaussDB考题理论参考文档/
├── DRS安装文档/
├── RPS 安装包/
└── shared/                 # 公共共享模块
```

## 快速开始

```bash
# 进入具体子项目
cd DWS部署工具集
# 阅读该子项目的 CLAUDE.md 获取具体启动方式
```

## 隔离说明

- 整个目录是一个 Git 仓库
- 每个子项目通过独立的 `CLAUDE.md` 实现上下文隔离
- 子项目间无代码依赖（shared 除外）
