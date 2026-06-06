# DWS 部署工具集 · 统一视觉修复方案

## 一、问题根因

审查 14 个模板后发现，视觉问题的**根本原因不是设计风格不好，而是 CSS 体系严重割裂**：

### 1.1 CSS 变量三套体系互不兼容

| 体系 | 范围 | 示例变量 | 说明 |
|:-----|:------|:---------|:------|
| **base.html 官方变量** | `:root` | `--accent`, `--gray`, `--text`, `--bg`, `--card` | 正确定义，但只有架构图页和会话页正确使用 |
| **g- 系列灰色变量** | 仪表盘/预检/部署/流程/检查清单 | `--g50`, `--g100`, `--g500` | **不存在**，页面显示为默认黑色 |
| **tx/ac/bd 变量** | 配置/设备/审计/模板 | `--tx`, `--t2`, `--ac`, `--bd` | **不存在**，页面显示为透明/黑色 |

### 1.2 未定义 CSS 类导致页面无样式

| 页面 | 严重程度 | 使用的未定义类 |
|:-----|:--------:|:---------------|
| **设备清单** | 🔴 完全无样式 | `.stats`, `.eq-grid`, `.eq-card`, `.tbl`, `.rack-grid`, `.net-label` 等 20+ 类 |
| **审计日志** | 🔴 完全无样式 | `.badge`, `.bg-*`, `.tbl` |
| **配置模板** | 🔴 完全无样式 | `.badge`, `.bg-*`, `.code`, `btn-s`, `btn-p` |
| **仪表盘** | 🟡 布局错乱 | `.two`, `.fsb`, `.ti`, `btn-pri` |
| **预检** | 🟡 按钮无样式 | `btn-pri` |
| **交付物** | 🟡 按钮无样式 | `btn-pri` |

### 1.3 按钮类名不统一

| 当前写法 | 应改为 | 出现页数 |
|:---------|:-------|:--------:|
| `btn-pri` | `btn-primary` | 3 页 |
| `btn-p` | `btn-primary` | 2 页 |
| `btn-s` | `btn-ghost` | 1 页 |
| `tg-gry` | `tg-blu` 或新增 `tg-gry` | 3 页 |

---

## 二、修复策略

### 核心原则

1. **不新增全局变量**——只在 base.html 补充必要的缺失变量和类
2. **所有页面统一使用 base.html 的 CSS 体系**——删除各页面自定义变量
3. **逐步修复，每步可验证**

### 修复步骤

#### Step 1：base.html 补充缺失变量和类（0.5天）

在 base.html 的 `:root` 中补充被广泛引用但缺失的变量：

```css
/* g-系列灰色（兼容过渡） */
--g50: #F9FAFB; --g100: #F3F4F6; --g200: #E5E7EB;
--g300: #D1D5DB; --g400: #9CA3AF; --g500: #6B7280;

/* 兼容变量（映射到标准变量） */
--tx: var(--text); --t2: var(--gray); --t3: var(--gray2);
--ac: var(--accent); --ac-bg: var(--accent-bg);
--bd: var(--gray3); --rs: var(--radius);
--pr: #6366f1; --pr-bg: #EEF2FF;
--gr: #10b981; --gr-bg: #ECFDF5;
```

补充通用 CSS 类：

```css
/* 布局工具 */
.two{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.fsb,.sb{display:flex;justify-content:space-between;align-items:center}
.sbc{display:flex;align-items:center;gap:8px}

/* 统计卡片 */
.stats{display:flex;gap:12px;flex-wrap:wrap}
.stat{flex:1;min-width:100px;padding:14px 18px;background:var(--card);border:1px solid var(--gray3);border-radius:var(--radius);text-align:center}
.si{width:32px;height:32px;border-radius:8px;display:flex;align-items:center;justify-content:center;font-size:16px;margin:0 auto 6px}
.sn{font-size:22px;font-weight:700;color:var(--primary)}
.sl{font-size:11px;color:var(--gray2)}

/* 标签/徽章（补充） */
.tg-gry{background:var(--g100);color:var(--g500)}
.badge{display:inline-block;padding:2px 8px;border-radius:4px;font-size:11px;font-weight:600}
.bg-info{background:#EFF6FF;color:#1d4ed8}
.bg-ok{background:#ECFDF5;color:#065f46}
.bg-warn{background:#FFFBEB;color:#92400e}
.bg-err{background:#FEF2F2;color:#991b1b}
.bg-dim{background:var(--g100);color:var(--g500)}

/* 表格 */
.tbl{width:100%;border-collapse:collapse;font-size:13px}
.tbl th{padding:10px 14px;font-weight:600;font-size:11px;color:var(--gray);text-transform:uppercase;background:#F8F9FA;border-bottom:1px solid var(--gray3);text-align:left}
.tbl td{padding:11px 14px;border-bottom:1px solid var(--g100)}

/* 代码块 */
.code{background:var(--g100);padding:12px 16px;border-radius:8px;font-size:12px;font-family:monospace;overflow-x:auto;white-space:pre-wrap}

/* 设备清单 */
.eq-grid{display:grid;gap:12px}
.eq-card{background:var(--card);border:1px solid var(--gray3);border-radius:var(--radius);padding:16px}
.eq-title{font-size:13px;font-weight:600;color:var(--primary);margin-bottom:6px}
.eq-specs{font-size:11px;color:var(--gray);line-height:1.6}
.net-label{font-size:10px;text-transform:uppercase;letter-spacing:.5px;color:var(--gray2);font-weight:600;margin-bottom:4px}
.net-row{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:8px}

/* 验证项 */
.vf-item{display:flex;align-items:center;gap:12px;padding:10px 0;border-bottom:1px solid var(--g100)}

/* 检查清单 */
.cl-item{display:flex;align-items:center;gap:10px;padding:8px 0;cursor:pointer}

/* 空状态 */
.empty-state{text-align:center;padding:60px 20px;color:var(--gray2);font-size:14px}

/* 机柜 */
.rack-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:16px}
.rack-panel{background:var(--card);border:1px solid var(--gray3);border-radius:var(--radius);padding:14px}
.rack-slot{display:flex;align-items:center;gap:6px;padding:4px 0;font-size:12px}
```

#### Step 2-6：逐页修复

| Step | 页面 | 主要问题 | 工时 |
|:-----|:------|:---------|:----:|
| **2** | 仪表盘(dws_dashboard) | 替换 `--g*` → 标准变量, `btn-pri`→`btn-primary`, 修复 `.two`, `.fsb`, `.ti` | 0.3天 |
| **3** | 预检(dws_precheck) | `btn-pri`→`btn-primary`, `--g*`→标准变量, 修复比例严格 | 0.2天 |
| **4** | 配置(dws_config) | 删除本页自定义CSS变量, 全部用base.html变量, `btn-p`→`btn-primary` | 0.3天 |
| **5** | 设备清单(dws_equipment) | 全面清理 `--t2`/`--ac`→标准变量, 硬编码色→变量 | 0.3天 |
| **6** | 审计(dws_audit) + 模板(dws_templates) | `badge`→标准, `--tx`→`--text`, 统一按钮 | 0.2天 |
| **7** | 部署+验证+流程+清单 | 替换 `--g*`→标准变量, 统一按钮 | 0.2天 |
| **8** | 交付物+会话 | 微调, `btn-pri`→`btn-primary` | 0.1天 |
| | **合计** | | **~2天** |

---

## 三、改动文件清单

| 文件 | Step | 操作 |
|:-----|:-----|:------|
| `templates/base.html` | 1 | 补充缺失变量+通用CSS类 |
| `templates/dws_dashboard.html` | 2 | CSS变量统一+按钮修复 |
| `templates/dws_precheck.html` | 3 | `btn-pri`+`--g*` 修复 |
| `templates/dws_config.html` | 4 | 删除自有变量+统一 |
| `templates/dws_equipment.html` | 5 | 变量统一+硬编码色修复 |
| `templates/dws_audit.html` | 6 | badge+tbl修复 |
| `templates/dws_templates.html` | 6 | badge+code+按钮修复 |
| `templates/dws_deploy.html` | 7 | 变量统一 |
| `templates/dws_verify.html` | 7 | 变量统一 |
| `templates/dws_flow.html` | 7 | 变量统一 |
| `templates/dws_checklist.html` | 7 | 变量统一 |
| `templates/dws_deliverables.html` | 8 | 按钮修复+微调 |

## 四、不动的内容

| 内容 | 理由 |
|:-----|:------|
| 架构图模板(刚重写完) | 变量使用正确，无需修改 |
| 会话管理模板 | 变量使用正确 |
| 侧边栏结构 | 符合深蓝主题设计意图 |
| 仪表盘布局意图 | 两列+统计卡片的设计方向正确 |

## 五、验证方式

每步修复后：
1. 用 `test_client` 渲染页面，确认 200
2. 检查 HTML 中无 `var(--g50)` 等不存在变量
3. 检查所有按钮有样式（`btn-primary` 的蓝色背景可见）
4. 浏览器打开页面对比修复前后视觉效果
