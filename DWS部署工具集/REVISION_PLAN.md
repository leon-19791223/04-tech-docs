# DWS 部署工具集 · 修订路线图与回滚指南

> **创建日期**: 2026-06-06  
> **状态**: ✅ **已完成** — 7 步修订计划全部实施完毕，参见 `DEVELOPMENT_PLAN.md` 继续 v2.0 生产化改造  
> **原始目标**: 将嘉兴银行 DWS-POC 引擎（1187行 `dws_engine.py`）整合到本工具集，实现"可视化 Web UI + 真实部署引擎 + 双模式执行"

---

## 一、仓库结构说明

本工具集是 `04-技术文档` 父仓库的一个**子目录**，与迁移评估系统、Z-DBMate 等共享同一个 Git 仓库：

```
父仓库: C:\Users\52985\Desktop\04-技术文档\  (Git根目录)
  ├── DWS部署工具集/          ← 本项目
  ├── DWS-迁移沟通文档/        ← 迁移评估系统
  ├── Z-DBMate工具集/          ← 另一个项目
  └── ...
```

> ⚠️ 由于共享仓库，**禁止使用 `git reset --hard` 回滚**（会连带影响其他项目）。

---

## 二、最佳实践：推荐的 Git 工作流

### 2.1 每次提交只 add 本项目文件

```bash
# ✅ 正确：只添加 DWS部署工具集 目录下的变更
git add DWS部署工具集/

# ❌ 错误：不要用 git add -A（会连带添加其他项目的修改）
```

### 2.2 提交信息规范

```
dws: step N - 简短说明
```

示例：`dws: step 0 - git init baseline`、`dws: step 1 - import dws_engine`

### 2.3 每个里程碑打 Tag

用 `dws-` 前缀区分，避免与父仓库其他项目的标签冲突。

### 2.4 回滚方式（三种方案按需选择）

| 方案 | 命令 | 适用场景 | 风险 |
|:-----|:-----|:---------|:----:|
| **方案A ⭐推荐** | `git restore --source=<tag> -- DWS部署工具集/` | 只恢复DWS目录文件到某个里程碑 | ✅ 完全不影响其他项目 |
| **方案B** | `git checkout <tag>` | 查看整个仓库在里程碑时的状态 | ⚠️ 分离HEAD，查看完记得切回来 |
| **方案C** | `git revert <commit>` | 撤销某次特定提交 | ⚠️ 会生成新的反向提交，需留意冲突 |

#### 推荐的完整回滚流程

```bash
# 场景：Step 3 改坏了，想回到 Step 2 的状态

# 1. 查看当前状态
git status

# 2. 如果有未提交的修改，先 stash
git stash push -m "dws: temp save before rollback"

# 3. 用 tag 恢复 DWS 目录到 Step 2
git restore --source=dws-v2-templates -- DWS部署工具集/

# 4. 确认恢复后的文件
git diff DWS部署工具集/ --stat

# 5. 如果没问题，提交恢复结果
git add DWS部署工具集/
git commit -m "dws: rollback to v2-templates (step 2)"

# 6. 如果需要找回 stash 的内容
git stash pop
```

---

## 三、修订路线图（共 7 步）

### Step 0：Git 初始化 + Baseline 快照

| 项目 | 内容 |
|:-----|:------|
| **目的** | 记录当前版本的完整状态，作为回滚的绝对原点 |
| **操作** | git init → git add DWS部署工具集/ → git commit → git tag |
| **Tag 名** | `dws-v0-baseline` |
| **涉及文件** | 所有已有文件（4个py + 1个sh + 2个conf + 7个html + md） |
| **验证标准** | `python app.py` → http://127.0.0.1:5053 仪表盘正常显示 |

**回滚命令**：
```bash
git restore --source=dws-v0-baseline -- DWS部署工具集/
```

---

### Step 1：导入嘉兴银行引擎（核心步骤）

| 项目 | 内容 |
|:-----|:------|
| **目的** | 将嘉兴银行 DWS-POC 的完整引擎（dws_engine.py 1187行）导入本工具集，建立 engine/ 目录 |
| **Tag 名** | `dws-v1-engine-import` |
| **新增文件** | `engine/__init__.py`、`engine/core_engine.py` |
| **修改文件** | `app.py`（重写，从 Mock 模式改为双模式：demo/engine） |
| **保留文件** | `core/precheck_engine.py`、`core/verifier.py`、`scripts/precheck_fusion.sh` |

**目录结构变更**：
```
Before:                            After:
DWS部署工具集/                      DWS部署工具集/
├── app.py         (155行,Mock)      ├── app.py         (重写,双模式)
├── core/                           ├── core/           (保留)
│   ├── precheck_engine.py          │   ├── precheck_engine.py
│   └── verifier.py                 │   └── verifier.py
├── scripts/                        ├── engine/         ⭐ 新增
│   └── precheck_fusion.sh          │   ├── __init__.py
├── templates/ (7个)                │   └── core_engine.py  (1187行)
└── ...                             ├── scripts/
                                    │   └── precheck_fusion.sh
                                    └── templates/ (7个)
```

**如何保留嘉兴银行 POC 独立性**：
- `engine/core_engine.py` **一字不改**直接从嘉兴银行项目复制
- 后续如果嘉兴银行项目有更新，只需要替换这个文件
- 如果要自定义引擎行为，在 `app.py` 中包装，不修改 `core_engine.py`

**验证标准**：
```bash
# demo 模式（默认，无需SSH）
curl http://127.0.0.1:5053/api/architecture?scenario=uat
# 应返回 JSON 格式的节点拓扑数据

# 环境切换
curl http://127.0.0.1:5053/env/switch/PREPROD
# 应切换到生产环境2+5配置
```

**回滚命令**：
```bash
git restore --source=dws-v0-baseline -- DWS部署工具集/
```

---

### Step 2：模板合并与 UI 升级

| 项目 | 内容 |
|:-----|:------|
| **目的** | 将嘉兴银行 POC 的 8 个模板合并进来，保留本工具集原有的预检/验证/清单模板 |
| **Tag 名** | `dws-v2-templates` |
| **新增模板** | `dws_config.html`（60+参数配置表单）、`dws_phase.html`（步骤执行交互）、`dws_templates.html`（8种模板预览）、`dws_audit.html`（审计日志）、`dws_architecture.html`（动态架构图）、`dws_equipment.html`（设备清单+机柜图） |
| **保留模板** | `base.html`、`dws_dashboard.html`（升级）、`dws_precheck.html`、`dws_verify.html`、`dws_checklist.html`、`dws_deploy.html`、`dws_flow.html` |

**模板对照表**：
```
嘉兴银行 DWS-POC 的模板 (8个)     →  本工具集合并后 (12个)
dws_base.html                    →  (不导入，保留本工具集的base.html)
dws_index.html                   →  dws_dashboard.html (融合升级)
dws_config.html                  →  dws_config.html (新增)
dws_phase.html                   →  dws_phase.html (新增)
dws_templates.html               →  dws_templates.html (新增)
dws_audit.html                   →  dws_audit.html (新增)
dws_architecture.html             →  dws_architecture.html (新增)
dws_equipment.html               →  dws_equipment.html (新增)
```

**回滚命令**：
```bash
git restore --source=dws-v1-engine-import -- DWS部署工具集/
```

---

### Step 3：SSH 执行引擎

| 项目 | 内容 |
|:-----|:------|
| **目的** | 将 `precheck_fusion.sh` 的 SSH 多节点执行逻辑封装为 Python 模块，实现双模式（demo/真实SSH） |
| **Tag 名** | `dws-v3-ssh-executor` |
| **新增文件** | `engine/ssh_executor.py` |
| **修改文件** | `app.py`（增加 demo/ssh 模式切换，预检接口改为双模式） |
| **依赖** | `pip install paramiko` |

**ssh_executor.py 核心设计**：
```python
class SSHExecutor:
    MODE_DEMO = "demo"      # 显示命令文本（Copy-Paste）
    MODE_SSH = "ssh"        # 真实 SSH 执行（paramiko）

    def connect(self, host, user, key_or_pwd=None): ...
    def run_command(self, cmd) -> CommandResult: ...
    def run_on_nodes(self, nodes, cmds, parallel=True) -> List[CommandResult]: ...
    def check_precheck(self, item, node) -> CheckResult: ...
```

**回滚命令**：
```bash
git restore --source=dws-v2-templates -- DWS部署工具集/
```

---

### Step 4：预检扩展 17→40 项

| 项目 | 内容 |
|:-----|:------|
| **目的** | 按华为 DWS 官方规范，将预检项从 17 项扩展到 40 项 |
| **Tag 名** | `dws-v4-precheck-ext` |
| **修改文件** | `core/precheck_engine.py` |

**扩展对照表**：
```
类别   当前    目标    新增项
──── ───── ───── ────────────────────────
硬件     5     12    BIOS版本/UEFI模式/CPU频率/内存频率/
                     PCIe链路/RAID缓存/BBU状态/硬盘健康
OS       8     15    umask/file-max/TCP参数/ARP/NTP偏移/
                     SSH配置/密码策略/ulimit/coredump
网络     0      8    交换机MTU/VLAN/路由可达/带宽测试/
                     重传率/端口协商/STP状态/MAC表
存储     2      5     条带化/对齐/预读/IO调度器/writeback
```

**回滚命令**：
```bash
git restore --source=dws-v3-ssh-executor -- DWS部署工具集/
```

---

### Step 5：交付报告自动生成

| 项目 | 内容 |
|:-----|:------|
| **目的** | 自动生成部署预检报告、审计日志、验证报告，一键打包交付物 |
| **Tag 名** | `dws-v5-report-gen` |
| **新增文件** | `engine/report_generator.py` |
| **修改文件** | `app.py`（增加 /api/report 和 /deliverables 路由） |

**报告生成物**：
```
deliverables/<session_id>/
├── 01-预检报告.html          ← 预检结果+修复建议
├── 02-部署审计日志.json       ← 每步执行记录+耗时
├── 03-部署后验证报告.html     ← 验证结果+性能基线
├── 04-LLD拓扑总览.txt        ← 环境配置概览
├── 05-preinstall.ini         ← FusionInsight配置
├── 06-sysctl.conf            ← 内核参数
├── 07-分区脚本.sh             ← 磁盘分区脚本
└── deliverables.tar.gz       ← 以上全部打包
```

**回滚命令**：
```bash
git restore --source=dws-v4-precheck-ext -- DWS部署工具集/
```

---

### Step 6：统一门户集成

| 项目 | 内容 |
|:-----|:------|
| **目的** | 在仪表盘加入与迁移评估系统、Z-DBMate 的工具链联动 |
| **Tag 名** | `dws-v6-portal` |
| **修改文件** | `templates/dws_dashboard.html`、`app.py` |

**集成内容**：
```
仪表盘新增 ┌─ 工具链联动 ─────────────────────┐
           │  ① 迁移智能评估系统 → 评估→DWS兼容   │
           │  ② DWS部署工具集    → 当前            │
           │  ③ Z-DBMate工具集   → GaussDB OLTP   │
           └──────────────────────────────────────┘
```

**回滚命令**：
```bash
git restore --source=dws-v5-report-gen -- DWS部署工具集/
```

---

## 四、完整可视化路线图

```
时间线（预计 7.5 天）
──────────────────────────────────────────────────────────────────
Step 0    ██░░░░░░░░░░░░░░░░░░░░  5min    Git init + baseline
Step 1    ██████████████░░░░░░░░  1天     引擎导入 (核心)
Step 2    ██████████████░░░░░░░░  1天     模板合并
Step 3    ████████████████████░░  2天     SSH执行引擎
Step 4    ██████████████░░░░░░░░  1天     预检扩展
Step 5    ██████████████░░░░░░░░  1天     报告生成
Step 6    ████████░░░░░░░░░░░░░░  0.5天   门户集成
──────────────────────────────────────────────────────────────────
          ████████████████████████████████████████████████████
          合计约 6.5 天有效工时 + 1 天缓冲 = 7.5 天
```

---

## 五、Tag 生命周期管理

### Tag 命名规范

```
dws-v{序号}-{短横线描述}
```

| Tag | 对应步骤 | 描述 |
|:----|:---------|:-----|
| `dws-v0-baseline` | Step 0 | 修订前原始版本 |
| `dws-v1-engine-import` | Step 1 | 导入嘉兴引擎 |
| `dws-v2-templates` | Step 2 | 模板合并完成 |
| `dws-v3-ssh-executor` | Step 3 | SSH 执行引擎 |
| `dws-v4-precheck-ext` | Step 4 | 预检扩展 |
| `dws-v5-report-gen` | Step 5 | 报告生成 |
| `dws-v6-portal` | Step 6 | 门户集成 |

### 常用操作

```bash
# 查看所有 DWS 相关标签
git tag -l "dws-*"

# 查看标签详情（含提交信息）
git show dws-v0-baseline --stat

# 在两个里程碑之间对比差异（只看DWS目录）
git diff dws-v0-baseline..dws-v2-templates -- DWS部署工具集/

# 查看某个里程碑的完整文件列表
git ls-tree --name-only -r dws-v1-engine-import | grep DWS部署工具集/

# 错误地打错了标签 → 删除本地标签
git tag -d dws-vX-wrong-tag

# 推送标签到远程
git push origin dws-v0-baseline
git push origin --tags

# 删除远程标签
git push origin :refs/tags/dws-vX-wrong-tag
```

---

## 六、故障场景恢复指南

### 场景 1：Step 3 改坏了，想回到 Step 2

```bash
# 安全回滚（只影响DWS目录）
git restore --source=dws-v2-templates -- DWS部署工具集/
git add DWS部署工具集/
git commit -m "dws: rollback to v2-templates"

# 如果需要放弃本次rollback提交
git revert HEAD --no-edit
```

### 场景 2：父仓库有其他人的提交，我只想回退 DWS 目录

```bash
# 查看DWS目录的提交历史
git log --oneline -- DWS部署工具集/

# 恢复到指定提交（只恢复DWS目录）
git restore --source=<commit-hash> -- DWS部署工具集/
```

### 场景 3：想对比当前版本与 baseline 的差异

```bash
git diff dws-v0-baseline -- DWS部署工具集/ | less
```

### 场景 4：想从 baseline 分支一个新实验版本

```bash
git checkout -b dws-experiment dws-v0-baseline
# 在新分支上做实验，不影响 main 分支
```

---

## 七、前提条件与依赖

```bash
# Python 依赖
pip install flask paramiko  # paramiko 在 Step 3 才需要

# 验证当前环境
python --version  # 需要 >= 3.8
python -c "import flask; print('flask ok')"
```

---

## 八、完成后的最终架构

```
DWS部署工具集/
├── app.py                      # Flask 主入口（14+ 路由）
├── engine/                     # ⭐ 核心引擎
│   ├── __init__.py
│   ├── core_engine.py          # 嘉兴银行 DWS-POC 引擎（1187行，一字不改）
│   ├── ssh_executor.py         # SSH 执行器（双模式：demo/ssh）
│   └── report_generator.py     # 交付报告生成器
├── core/                       # 规则模块（保留）
│   ├── precheck_engine.py      # 40 项预检规则
│   └── verifier.py             # 10 项验证规则
├── scripts/
│   └── precheck_fusion.sh      # SSH 预检脚本（保留）
├── templates/                  # 12 个模板
│   ├── base.html               # 深蓝主题（保留）
│   ├── dws_dashboard.html      # 仪表盘（融合升级）
│   ├── dws_precheck.html       # 预检页（保留）
│   ├── dws_config.html         # 配置表单（新增 from 嘉兴）
│   ├── dws_phase.html          # 步骤执行（新增 from 嘉兴）
│   ├── dws_templates.html      # 模板预览（新增 from 嘉兴）
│   ├── dws_audit.html          # 审计日志（新增 from 嘉兴）
│   ├── dws_architecture.html   # 架构图（新增 from 嘉兴）
│   ├── dws_equipment.html      # 设备清单（新增 from 嘉兴）
│   ├── dws_verify.html         # 验证页（保留）
│   ├── dws_deploy.html         # 部署引导（保留）
│   ├── dws_flow.html           # 部署流程（保留）
│   └── dws_checklist.html      # 检查清单（保留）
├── docs/
│   └── DWS_DEPLOY_FLOW.md      # 部署流程文档（保留）
├── conf/
│   └── preinstall.ini.template # 配置模板（保留）
├── REVISION_PLAN.md            ← 本文件（修订路线图）
└── README.md                   ← 项目说明（已更新）
```

---

> **维护提示**：本文件本身应纳入版本控制。如果修订过程中路线图发生变更，请同步更新本文档并提交。
