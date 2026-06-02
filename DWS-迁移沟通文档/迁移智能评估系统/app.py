"""
迁移智能评估系统 - Web UI (Flask)
支持多源-目标迁移路径选择
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file

from rules.registry import get_rules, list_registered
from rules import gp_to_dws, oracle_to_dws, mysql_to_dws, mssql_to_dws
from scanners.gp_scanner import GPScanner
from scanners.oracle_scanner import OracleScanner
from scanners.mysql_scanner import MySQLScanner
from scanners.mssql_scanner import MSSQLScanner
from scanners.sample_scanner import SampleScanner
from core.engine import MigrationAnalyzer
from core.models import MigrationMetadata, AssessmentResult

app = Flask(__name__)

# 迁移路径配置
MIGRATION_PATHS = {
    "gp_dws": {
        "label": "Greenplum -> DWS", "source": "gp", "target": "dws",
        "rules_module": gp_to_dws, "scanner": GPScanner,
        "icon": "&#x1F7E2;"
    },
    "oracle_dws": {
        "label": "Oracle -> DWS", "source": "oracle", "target": "dws",
        "rules_module": oracle_to_dws, "scanner": OracleScanner,
        "icon": "&#x1F534;"
    },
    "mysql_dws": {
        "label": "MySQL -> DWS", "source": "mysql", "target": "dws",
        "rules_module": mysql_to_dws, "scanner": MySQLScanner,
        "icon": "&#x1F431;"
    },
    "mssql_dws": {
        "label": "SQL Server -> DWS", "source": "mssql", "target": "dws",
        "rules_module": mssql_to_dws, "scanner": MSSQLScanner,
        "icon": "&#x1F4CB;"
    },
}

# 全局缓存
_current_result: AssessmentResult = None
_metadata: MigrationMetadata = None
_current_path: str = "gp_dws"  # 当前选中的迁移路径


def get_or_create_result(path_key: str = None):
    global _current_result, _metadata, _current_path

    if path_key and path_key != _current_path:
        _current_path = path_key
        _current_result = None

    if _current_result is None:
        cfg = MIGRATION_PATHS[_current_path]
        scanner_cls = cfg["scanner"]
        if scanner_cls == GPScanner:
            scanner = scanner_cls()
        else:
            scanner = scanner_cls()

        _metadata = scanner.scan()
        rules = get_rules(cfg["source"], cfg["target"])
        weights = cfg["rules_module"].load_weights()
        analyzer = MigrationAnalyzer(
            metadata=_metadata, rules=rules,
            category_weights=weights,
            source_type=cfg["source"], target_type=cfg["target"],
        )
        _current_result = analyzer.analyze()
    return _current_result


@app.route("/")
def index():
    path_key = request.args.get("path", _current_path)
    result = get_or_create_result(path_key=path_key if path_key in MIGRATION_PATHS else None)
    return render_template("dashboard.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/environment")
def environment():
    result = get_or_create_result()
    return render_template("environment.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/compatibility")
def compatibility():
    result = get_or_create_result()
    return render_template("compatibility.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/issues")
def issues():
    result = get_or_create_result()
    return render_template("issues.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/workload")
def workload():
    result = get_or_create_result()
    return render_template("workload.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/recommendations")
def recommendations():
    result = get_or_create_result()
    return render_template("recommendations.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/switch-path/<path_key>")
def switch_path(path_key):
    if path_key in MIGRATION_PATHS:
        get_or_create_result(path_key=path_key)
    return index()


@app.route("/api/data")
def api_data():
    result = get_or_create_result()
    paths = MIGRATION_PATHS
    return jsonify({
        "migration_path": _current_path,
        "available_paths": {k: v["label"] for k, v in paths.items()},
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
    output_path = os.path.join(os.path.dirname(__file__), "迁移智能评估报告.docx")
    gen = ReportGenerator(result, output_path)
    gen.generate()
    return send_file(output_path, as_attachment=True)


@app.route("/reanalyze", methods=["POST"])
def reanalyze():
    global _current_result, _metadata, _current_path

    path_key = request.form.get("path", _current_path)
    if path_key in MIGRATION_PATHS:
        _current_path = path_key

    cfg = MIGRATION_PATHS[_current_path]
    scanner_cls = cfg["scanner"]
    scanner = scanner_cls()
    _metadata = scanner.scan()

    for field in ["table_count", "view_count", "function_count", "total_capacity",
                   "etl_tool", "scheduler_tool"]:
        if request.form.get(field):
            val = request.form.get(field)
            if field in ("table_count", "view_count", "function_count"):
                val = int(val)
            setattr(_metadata, field, val)

    rules = get_rules(cfg["source"], cfg["target"])
    weights = cfg["rules_module"].load_weights()
    analyzer = MigrationAnalyzer(
        metadata=_metadata, rules=rules,
        category_weights=weights,
        source_type=cfg["source"], target_type=cfg["target"],
    )
    _current_result = analyzer.analyze()
    return jsonify({"status": "ok", "score": _current_result.overall_score,
                    "path": _current_path})


if __name__ == "__main__":
    print("=" * 50)
    print("  迁移智能评估系统 - Web UI")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5000")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5000)
