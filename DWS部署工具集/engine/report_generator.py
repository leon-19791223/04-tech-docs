"""
DWS 交付报告生成器
生成物: 预检报告HTML / 审计日志JSON / 验证报告HTML / 交付物压缩包

用法:
    from engine.report_generator import ReportContext, generate_deliverable_bundle
    context = ReportContext(session_id=..., cluster_name=..., ...)
    result = generate_deliverable_bundle(context, "deliverables/")
    # → {"bundle_path": "...", "files": [...], "size_bytes": 12345}
"""

import os
import json
import tarfile
import io
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class DeliveryMetadata:
    """交付元数据"""
    project_name: str = ""
    customer: str = ""
    site: str = ""
    deploy_engineer: str = ""
    deploy_date: str = ""
    acceptance_criteria: str = ""


@dataclass
class ReportContext:
    """报告生成上下文"""
    session_id: str
    cluster_name: str
    environment: str
    metadata: DeliveryMetadata
    precheck_results: list = field(default_factory=list)
    precheck_items: list = field(default_factory=list)
    audit_log: list = field(default_factory=list)
    config_templates: dict = field(default_factory=dict)
    verify_results: list = field(default_factory=list)
    phases: list = field(default_factory=list)
    config: dict = field(default_factory=dict)
    generated_at: str = ""


def _build_header_style() -> str:
    """返回报告通用的 CSS 样式块"""
    return """
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,'PingFang SC','Microsoft YaHei',sans-serif;background:#f0f2f5;color:#1a1d26;line-height:1.6;font-size:14px}
.header{background:linear-gradient(135deg,#1A3C6E,#2A5A9E);color:#fff;padding:40px 48px}
.header h1{font-size:24px;font-weight:700;margin-bottom:6px}
.header .meta{font-size:13px;color:rgba(255,255,255,0.75);margin-top:4px}
.header .meta span{margin-right:24px}
.summary-row{display:flex;gap:16px;padding:24px 48px;background:#fff;border-bottom:1px solid #e6eaf0}
.summary-card{flex:1;padding:20px;border-radius:10px;text-align:center}
.summary-card.pass{background:#e6f6f0;border:1px solid #b2dfc8}
.summary-card.warn{background:#fff3e0;border:1px solid #ffcc80}
.summary-card.fail{background:#ffebee;border:1px solid #ef9a9a}
.summary-card .num{font-size:32px;font-weight:700}
.summary-card .label{font-size:12px;color:#666;margin-top:4px}
.summary-card.pass .num{color:#0e7c4b}
.summary-card.warn .num{color:#e67e22}
.summary-card.fail .num{color:#c62828}
.content{padding:24px 48px}
.section{margin-bottom:24px}
.section h2{font-size:16px;font-weight:600;margin-bottom:16px;padding-bottom:8px;border-bottom:2px solid #1A3C6E;color:#1A3C6E}
.section h3{font-size:14px;font-weight:600;margin:12px 0 8px;color:#2d2d2d}
table{width:100%;border-collapse:collapse;font-size:13px;margin-bottom:16px}
table th{padding:10px 14px;font-weight:600;font-size:11px;color:#6b7285;text-transform:uppercase;background:#f8f9fa;border-bottom:1px solid #e6eaf0;text-align:left}
table td{padding:10px 14px;border-bottom:1px solid #f0f2f5}
.tag{display:inline-block;padding:2px 10px;border-radius:5px;font-size:12px;font-weight:500}
.tag-pass{background:#e6f6f0;color:#0e7c4b}
.tag-warn{background:#fff3e0;color:#e67e22}
.tag-fail{background:#ffebee;color:#c62828}
.solution-box{background:#fff8e1;padding:12px;border-radius:6px;border-left:3px solid #e67e22;margin:8px 0;font-size:13px}
.footer{text-align:center;padding:24px;color:#9ca0af;font-size:12px;border-top:1px solid #e6eaf0}
"""


def _summary_block(pass_count: int, warn_count: int, fail_count: int, total: int) -> str:
    """生成统计卡片 HTML"""
    return f"""
<div class="summary-row">
  <div class="summary-card pass"><div class="num">{pass_count}</div><div class="label">通过</div></div>
  <div class="summary-card warn"><div class="num">{warn_count}</div><div class="label">警告</div></div>
  <div class="summary-card fail"><div class="num">{fail_count}</div><div class="label">失败</div></div>
  <div class="summary-card" style="background:#e8eaf6;border:1px solid #c5cae9">
    <div class="num" style="color:#1A3C6E">{total}</div>
    <div class="label">总计</div>
  </div>
</div>"""


def _category_name(cat_id: str) -> str:
    names = {"hardware": "硬件环境", "os": "OS配置", "network": "网络环境",
             "storage": "存储配置", "software": "软件环境"}
    return names.get(cat_id, cat_id)


def generate_precheck_report(context: ReportContext) -> str:
    """生成预检报告 (HTML)"""
    items = context.precheck_items
    results = context.precheck_results
    meta = context.metadata
    now = context.generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Build result lookup
    result_map = {}
    for r in results:
        key = f"{r.get('item_id')}_{r.get('node')}"
        result_map[key] = r

    # Count by status
    pass_count = sum(1 for r in results if r.get("status") == "pass")
    warn_count = sum(1 for r in results if r.get("status") == "warn")
    fail_count = sum(1 for r in results if r.get("status") == "fail")
    total = len(results) if results else len(items)

    # Group items by category
    cats = {}
    for item in items:
        cat = item.get("category", "other")
        cats.setdefault(cat, []).append(item)

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>预检报告 - {context.cluster_name}</title>
<style>{_build_header_style()}</style></head>
<body>
<div class="header">
  <h1>DWS 集群部署预检报告</h1>
  <div class="meta">
    <span>项目: {meta.project_name or '—'}</span>
    <span>客户: {meta.customer or '—'}</span>
    <span>集群: {context.cluster_name}</span>
    <span>环境: {context.environment}</span>
    <span>生成: {now}</span>
  </div>
</div>
{_summary_block(pass_count, warn_count, fail_count, total)}
<div class="content">
  <div class="section">
    <h2>检查详情</h2>"""

    for cat in ["hardware", "os", "network", "storage", "software"]:
        cat_items = cats.get(cat, [])
        if not cat_items:
            continue
        html += f'<h3>{_category_name(cat)} ({len(cat_items)}项)</h3><table>'
        html += '<tr><th>检查项</th><th>状态</th><th>结果</th><th>修复建议</th></tr>'
        for item in cat_items:
            iid = item.get("id", "")
            name = item.get("name", iid)
            # Find first matching result
            status = "pending"
            detail = ""
            sol = item.get("solution", "")
            for r in results:
                if r.get("item_id") == iid:
                    status = r.get("status", "pending")
                    detail = r.get("detail", "")
                    break
            if status == "pending":
                detail = "未检查"
            tag_cls = {"pass": "tag-pass", "warn": "tag-warn", "fail": "tag-fail", "pending": "tag-warn"}.get(status, "tag-warn")
            tag_text = {"pass": "通过", "warn": "警告", "fail": "失败", "pending": "未检"}.get(status, status)
            html += f'<tr><td>{name}</td><td><span class="tag {tag_cls}">{tag_text}</span></td><td>{detail[:80]}</td><td style="font-size:12px;color:#666">{sol[:60] if status != "pass" else "—"}</td></tr>'
        html += '</table>'

    # Failed items with full solutions
    fail_items = [r for r in results if r.get("status") in ("fail", "warn")]
    if fail_items:
        html += '<h3>需关注项及修复建议</h3>'
        for r in fail_items[:10]:
            iid = r.get("item_id", "")
            item = next((i for i in items if i.get("id") == iid), None)
            sol = item.get("solution", "") if item else ""
            html += f'<div class="solution-box"><strong>{r.get("item_name", iid)}</strong> [{r.get("status")}]: {r.get("detail", "")}'
            if sol:
                html += f'<div style="margin-top:4px;font-size:12px;">→ {sol}</div>'
            html += '</div>'

    html += f"""
  </div>
  <div class="section">
    <h2>交付信息</h2>
    <table>
      <tr><td>项目名称</td><td>{meta.project_name or '—'}</td></tr>
      <tr><td>客户</td><td>{meta.customer or '—'}</td></tr>
      <tr><td>部署地点</td><td>{meta.site or '—'}</td></tr>
      <tr><td>部署工程师</td><td>{meta.deploy_engineer or '—'}</td></tr>
      <tr><td>部署日期</td><td>{meta.deploy_date or '—'}</td></tr>
      <tr><td>验收标准</td><td>{meta.acceptance_criteria or '—'}</td></tr>
    </table>
  </div>
</div>
<div class="footer">DWS 智能部署系统 · {now}</div>
</body>
</html>"""
    return html


def generate_verify_report(context: ReportContext) -> str:
    """生成部署后验证报告 (HTML)"""
    items = context.verify_results
    meta = context.metadata
    now = context.generated_at or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    pass_count = sum(1 for i in items if i.get("status") == "pass")
    warn_count = sum(1 for i in items if i.get("status") == "warn")
    fail_count = sum(1 for i in items if i.get("status") == "fail")
    total = len(items) or 0

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><title>验证报告 - {context.cluster_name}</title>
<style>{_build_header_style()}</style></head>
<body>
<div class="header">
  <h1>DWS 集群部署后验证报告</h1>
  <div class="meta">
    <span>集群: {context.cluster_name}</span>
    <span>环境: {context.environment}</span>
    <span>生成: {now}</span>
  </div>
</div>
{_summary_block(pass_count, warn_count, fail_count, total)}
<div class="content">
  <div class="section">
    <h2>验证详情</h2>
    <table>
      <tr><th>验证项</th><th>状态</th><th>结果</th></tr>"""
    for r in items:
        name = r.get("name", r.get("item_id", ""))
        status = r.get("status", "pending")
        detail = r.get("detail", "")
        tag_cls = {"pass": "tag-pass", "warn": "tag-warn", "fail": "tag-fail"}.get(status, "tag-warn")
        tag_text = {"pass": "通过", "warn": "警告", "fail": "失败"}.get(status, status)
        html += f'<tr><td>{name}</td><td><span class="tag {tag_cls}">{tag_text}</span></td><td>{detail[:80]}</td></tr>'
    html += """</table>
  </div>
</div>
<div class="footer">DWS 智能部署系统 · """ + now + """</div>
</body>
</html>"""
    return html


def generate_audit_json(context: ReportContext) -> str:
    """生成审计日志 JSON"""
    logs = context.audit_log if context.audit_log else [
        {"session": context.session_id, "cluster": context.cluster_name,
         "phase": 0, "step": "init", "status": "info",
         "cmd": "", "output": "部署会话已创建（模拟模式）",
         "duration_sec": 0, "timestamp": context.generated_at}
    ]
    data = {
        "session_id": context.session_id,
        "cluster_name": context.cluster_name,
        "environment": context.environment,
        "metadata": {
            "project_name": context.metadata.project_name,
            "customer": context.metadata.customer,
            "engineer": context.metadata.deploy_engineer,
            "date": context.metadata.deploy_date,
        },
        "generated_at": context.generated_at,
        "audit_log": logs,
    }
    return json.dumps(data, ensure_ascii=False, indent=2, default=str)


def generate_deliverable_bundle(context: ReportContext, output_dir: str) -> dict:
    """生成全部交付物并打包为 tar.gz

    Args:
        context: ReportContext
        output_dir: 输出目录

    Returns: {"bundle_path": "...", "files": [...], "size_bytes": N}
    """
    os.makedirs(output_dir, exist_ok=True)
    session_dir = os.path.join(output_dir, context.session_id)
    os.makedirs(session_dir, exist_ok=True)

    # Generate individual files
    files = []

    # 1. Precheck report
    precheck_html = generate_precheck_report(context)
    p1 = os.path.join(session_dir, "01-预检报告.html")
    with open(p1, "w", encoding="utf-8") as f:
        f.write(precheck_html)
    files.append(p1)

    # 2. Audit log JSON
    audit_json = generate_audit_json(context)
    p2 = os.path.join(session_dir, "02-部署审计日志.json")
    with open(p2, "w", encoding="utf-8") as f:
        f.write(audit_json)
    files.append(p2)

    # 3. Verify report
    verify_html = generate_verify_report(context)
    p3 = os.path.join(session_dir, "03-部署后验证报告.html")
    with open(p3, "w", encoding="utf-8") as f:
        f.write(verify_html)
    files.append(p3)

    # 4-8. Configuration templates
    tmpl_files = [
        ("04-LLD拓扑总览.txt", context.config_templates.get("LLD 拓扑总览", "")),
        ("05-preinstall.ini", context.config_templates.get("preinstall.ini", "")),
        ("06-sysctl-99-dws.conf", context.config_templates.get("sysctl 参数 (99-dws.conf)", "")),
        ("07-分区脚本-parted_mkfs.sh", context.config_templates.get("分区脚本 (parted_mkfs.sh)", "")),
        ("08-网络配置脚本-setup_network.sh", context.config_templates.get("网络配置脚本 (setup_network.sh)", "")),
    ]
    for fname, content in tmpl_files:
        if content:
            fp = os.path.join(session_dir, fname)
            with open(fp, "w", encoding="utf-8") as f:
                f.write(content)
            files.append(fp)

    # 9. Delivery metadata JSON
    meta_json = json.dumps({
        "project_name": context.metadata.project_name,
        "customer": context.metadata.customer,
        "site": context.metadata.site,
        "engineer": context.metadata.deploy_engineer,
        "date": context.metadata.deploy_date,
        "acceptance_criteria": context.metadata.acceptance_criteria,
        "cluster_name": context.cluster_name,
        "environment": context.environment,
        "generated_at": context.generated_at,
    }, ensure_ascii=False, indent=2)
    p9 = os.path.join(session_dir, "09-交付元数据.json")
    with open(p9, "w", encoding="utf-8") as f:
        f.write(meta_json)
    files.append(p9)

    # Create tar.gz
    bundle_name = f"dws_deliverables_{context.session_id}.tar.gz"
    bundle_path = os.path.join(output_dir, bundle_name)
    with tarfile.open(bundle_path, "w:gz") as tar:
        for fp in files:
            arcname = os.path.relpath(fp, output_dir)
            tar.add(fp, arcname=arcname)

    total_bytes = os.path.getsize(bundle_path)
    file_list = [os.path.basename(f) for f in files]

    return {
        "bundle_path": bundle_path,
        "bundle_name": bundle_name,
        "files": file_list,
        "size_bytes": total_bytes,
        "session_id": context.session_id,
    }
