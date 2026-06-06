# B-0: vendor 边界声明与数据隔离

## 1. 现状分析

`engine/core_engine.py` 是 Step 1 从「嘉兴银行 DWS-POC」(dws_engine.py) 直接复制的 1177 行代码，当前存在两个问题：

| 问题 | 描述 | 风险 |
|:-----|:------|:------|
| **边界模糊** | 无任何标注说明这是第三方供应商代码 | 后续开发可能误改,破坏嘉兴 POC 独立性 |
| **数据耦合** | 嘉兴特有数据（环境预设/设备清单/机柜布线）与通用引擎逻辑混在同一文件 | 部署工具集新增银行预设必须改 core_engine.py |

## 2. 改造目标

| 维度 | 当前状态 | 目标状态 |
|:-----|:---------|:---------|
| vendor 标注 | 无 | 文件头注明来源、版本、不应修改 |
| 嘉兴特有数据 | 硬编码在 core_engine.py 中 | 导出到独立 JSON 配置文件 |
| 数据读取 | app.py 直接从 core_engine.py import | 优先读 JSON → fallback 到 core_engine.py |
| 升级跟踪 | 无 | VENDOR_NOTICE.md 记录版本差异 |

## 3. 技术方案

### 3.1 VENDOR_NOTICE.md

记录 core_engine.py 的来源、版本、与上游的差异跟踪信息。

### 3.2 core_engine.py 文件头

添加 vendor 声明注释块，标注来源和修改规则。

### 3.3 conf/environment_presets.json

将嘉兴特有数据导出为 JSON，结构：

```json
{
  "_vendor": "嘉兴银行 DWS-POC",
  "ENV_PRESETS": { ... },
  "ARCH_SCENARIOS": { ... },
  "ARCH_ENV_MAP": { ... },
  "ROLE_META": { ... },
  "EQUIPMENT_LIST": { ... },
  "RACK_LAYOUT": { ... },
  "HARDWARE_BATCHES": { ... },
  "VERSION_SELECTION": { ... }
}
```

### 3.4 app.py 新增 fallback 函数

```python
def _load_vendor_data(key: str, default=None):
    """加载供应商数据：优先读 environment_presets.json，fallback 到 core_engine.py"""
    ...
```

## 4. 改动文件清单

| 文件 | 操作 | 内容 |
|:-----|:------|:------|
| `VENDOR_NOTICE.md` | **新增** | vendor 代码跟踪文档 |
| `conf/environment_presets.json` | **新增** | 嘉兴特有数据的 JSON 导出 |
| `engine/core_engine.py` | **修改** | 仅添加文件头 vendor 注释，不改变任何逻辑 |
| `app.py` | **修改** | 新增 _load_vendor_data() fallback 函数 |
| `docs/design/B0-vendor边界声明与数据隔离.md` | **新增** | 本设计文档 |

## 5. 影响范围

| 模式 | 影响 | 说明 |
|:-----|:------|:------|
| demo 模式 | 无影响 | 数据读取路径不变，只是加载方式多了一层 fallback |
| SSH 模式 | 无影响 | 同上 |
| 嘉兴 POC | **零影响** | 部署工具集目录内的修改不影响独立 Git 仓库的嘉兴项目 |
| 后续开发 | **正向** | 新增银行预设只需编辑 JSON 文件，无需修改 core_engine.py |

## 6. 测试方案

- **TC-B0-01**: environment_presets.json 加载后数据与原有 core_engine.py 一致
- **TC-B0-02**: core_engine.py 删除后（模拟 JSON fallback），系统仍可运行（使用 fallback）
- **TC-B0-03**: 回归：环境切换/架构图/设备清单/审计日志全部功能正常
- **TC-B0-04**: 回归：python app.py 启动正常，/api/health 返回 200
