"""
迁移智能评估系统 - Web UI (Flask)
提供可视化仪表盘、兼容性分析和报告查看
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file

# 新架构导入
from rules.registry import get_rules
from rules.gp_to_dws import load_weights
from scanners.gp_scanner import GPScanner
from scanners.sample_scanner import SampleScanner
from core.engine import MigrationAnalyzer
from core.models import MigrationMetadata, AssessmentResult

app = Flask(__name__)

# 全局缓存
_current_result: AssessmentResult = None
_metadata: MigrationMetadata = None


def get_or_create_result():
    global _current_result, _metadata
    if _current_result is None:
        # 采集元数据（优先使用模板文件）
        template_dir = os.path.dirname(os.path.abspath(__file__))
        parent_dir = os.path.dirname(template_dir)
        template_path = None
        for d in [template_dir, parent_dir]:
            for f in os.listdir(d):
                if "调研模板" in f and f.endswith('.xlsx'):
                    template_path = os.path.join(d, f)
                    break
            if template_path:
                break

        if template_path:
            print(f"[INFO] 使用模板: {template_path}")
            scanner = GPScanner(excel_path=template_path)
        else:
            print(f"[INFO] 使用样本数据")
            scanner = SampleScanner()

        _metadata = scanner.scan()
        rules = get_rules("gp", "dws")
        weights = load_weights()
        analyzer = MigrationAnalyzer(
            metadata=_metadata,
            rules=rules,
            category_weights=weights,
            source_type="gp",
            target_type="dws",
        )
        _current_result = analyzer.analyze()
    return _current_result


@app.route("/")
def index():
    result = get_or_create_result()
    return render_template("dashboard.html", result=result)


@app.route("/environment")
def environment():
    result = get_or_create_result()
    return render_template("environment.html", result=result)


@app.route("/compatibility")
def compatibility():
    result = get_or_create_result()
    return render_template("compatibility.html", result=result)


@app.route("/issues")
def issues():
    result = get_or_create_result()
    return render_template("issues.html", result=result)


@app.route("/workload")
def workload():
    result = get_or_create_result()
    return render_template("workload.html", result=result)


@app.route("/recommendations")
def recommendations():
    result = get_or_create_result()
    return render_template("recommendations.html", result=result)


@app.route("/api/data")
def api_data():
    result = get_or_create_result()
    return jsonify({
        "overall_score": result.overall_score,
        "risk_level": result.risk_level,
        "category_scores": [
            {"name": c.category_name, "score": c.actual_score,
             "passed": c.passed, "warnings": c.warnings,
             "errors": c.errors, "total": c.total_rules}
            for c in result.category_results
        ],
        "critical_issues": [
            {"name": i["name"], "category": i["category"],
             "description": i.get("description", ""), "difficulty": i.get("difficulty", "")}
            for i in result.critical_issues
        ],
        "table_count": result.table_count,
        "view_count": result.view_count,
        "function_count": result.function_count,
        "total_capacity": result.total_capacity,
        "db_version": result.db_version,
    })


@app.route("/report/download")
def download_report():
    result = get_or_create_result()
    from report_generator import ReportGenerator
    output_path = os.path.join(os.path.dirname(__file__), "GP_to_DWS_Assessment_Report.docx")
    gen = ReportGenerator(result, output_path)
    gen.generate()
    return send_file(output_path, as_attachment=True)


@app.route("/reanalyze", methods=["POST"])
def reanalyze():
    global _current_result, _metadata
    scanner = SampleScanner()
    _metadata = scanner.scan()
    # 支持表单参数覆盖
    for field in ["table_count", "view_count", "function_count", "total_capacity",
                   "etl_tool", "scheduler_tool"]:
        if request.form.get(field):
            val = request.form.get(field)
            if field in ("table_count", "view_count", "function_count"):
                val = int(val)
            setattr(_metadata, field, val)

    rules = get_rules("gp", "dws")
    weights = load_weights()
    analyzer = MigrationAnalyzer(
        metadata=_metadata, rules=rules,
        category_weights=weights,
        source_type="gp", target_type="dws",
    )
    _current_result = analyzer.analyze()
    return jsonify({"status": "ok", "score": _current_result.overall_score})


if __name__ == "__main__":
    print("=" * 50)
    print("  迁移智能评估系统 - Web UI")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5000)
