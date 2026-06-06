# DWS 部署工具集

> 华为 DWS 数据库自动化部署 CLI 工具。
> **独立项目**，与 04-技术文档 下其他子项目无依赖。

## 技术栈

- **语言**：Python 3
- **框架**：Click（CLI 框架）
- **用途**：自动化完成 DWS 集群的部署、配置、校验全流程

## 目录结构

```
DWS部署工具集/
├── app.py              # 入口
├── conf/               # 配置文件
├── core/               # 核心逻辑
├── engine/             # 部署引擎
├── scripts/            # 脚本
├── templates/          # 模板
├── deliverables/       # 交付物输出
└── docs/
    └── design/         # 设计文档
```

## 快速开始

```bash
python app.py --help
```

## 关键文档

- `README.md` — 项目说明
- `DEVELOPMENT_PLAN.md` — 开发计划
- `REVISION_PLAN.md` — 修订计划
- `VENDOR_NOTICE.md` — 供应商注意事项

## 隔离说明

- 本目录的所有代码和配置完全独立
- 不依赖 `04-技术文档` 下其他子项目
