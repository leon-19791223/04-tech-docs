# Vendor 代码声明

> 最后更新: 2026-06-06

---

## `engine/core_engine.py`

| 项目 | 内容 |
|:-----|:------|
| **来源** | 嘉兴银行 DWS-POC (`02-POC与售前/DWS-POC/嘉兴银行DWS-POC/dws_engine.py`) |
| **导入版本** | Step 1 (`dws-v1-engine-import`, commit `b7c052e`) |
| **当前对应** | 嘉兴 POC 仓库 `dws_engine.py` (1177行, MD5 已验证一致) |
| **修改规则** | **此文件不予修改** — 所有扩展在 app.py 层包装或通过配置文件覆盖 |
| **同步策略** | 嘉兴 POC 有更新时，git diff 对比后整体替换 |

## 部署工具集 vs 嘉兴 POC 的职责划分

| 能力 | 部署工具集实现 | 嘉兴 POC 提供 |
|:-----|:-------------|:-------------|
| SSH 执行引擎 | `engine/ssh_executor.py` (自有) | — |
| 预检规则 | `core/precheck_engine.py` (自有) | — |
| 部署验证 | `core/verifier.py` (自有) | — |
| 配置生成 | `core/config_generator.py` (自有) | — |
| 交付报告 | `engine/report_generator.py` (自有) | — |
| 8阶段部署流程 | — | `engine/core_engine.py` (vendor) |
| 架构图生成 | — | `engine/core_engine.py` (vendor) |
| 环境预设(嘉兴) | — | `engine/core_engine.py` → `conf/environment_presets.json` |
| 设备清单(嘉兴) | — | `engine/core_engine.py` → `conf/environment_presets.json` |

## 数据覆盖层

部署工具集通过以下机制扩展 vendor 代码的能力：

```
app.py (业务逻辑)
   │
   ├── conf/environment_presets.json  (扩展预设，优先级高)
   │      │
   │      └── engine/core_engine.py   (嘉兴预设，fallback)
   │
   ├── engine/ssh_executor.py         (自有模块)
   ├── core/precheck_engine.py        (自有模块)
   └── ...                            (自有模块)
```

## 版本跟踪

| 日期 | 操作 | 说明 |
|:-----|:------|:------|
| 2026-06-06 | 初始导入(dws-v1-engine-import) | 从嘉兴 POC `dws_engine.py` 复制为 `engine/core_engine.py` |
| 2026-06-06 | B-0 vendor 隔离 | 创建 VENDOR_NOTICE.md + 导出预设到 JSON |
