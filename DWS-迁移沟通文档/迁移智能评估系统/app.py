"""
迁移智能评估系统 - Web UI (Flask)
迁移路径自动发现: 只需 import 规则模块，自动注册到侧边栏
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify, send_file

# ================================================================
# 1. 导入规则包（自动注册所有迁移路径到规则注册表）
# ================================================================
import rules
from rules.registry import get_rules, get_registered_paths
from scanners.gp_scanner import GPScanner
from scanners.oracle_scanner import OracleScanner
from scanners.mysql_scanner import MySQLScanner
from scanners.mssql_scanner import MSSQLScanner
from scanners.db2_scanner import DB2Scanner
from scanners.teradata_scanner import TeradataScanner
from scanners.sample_scanner import SampleScanner
from core.engine import MigrationAnalyzer
from core.models import MigrationMetadata, AssessmentResult

app = Flask(__name__)
app.jinja_env.auto_reload = True

# ================================================================
# 2. 扫描器映射 (source -> scanner_class)
#    只需在此维护，加新的迁移路径只需加一行
# ================================================================
SCANNER_MAP = {
    "gp": GPScanner,
    "greenplum": GPScanner,
    "oracle": OracleScanner,
    "mysql": MySQLScanner,
    "mssql": MSSQLScanner,
    "sqlserver": MSSQLScanner,
    "sql_server": MSSQLScanner,
    "db2": DB2Scanner,
    "db2_luw": DB2Scanner,
    "teradata": TeradataScanner,
    "td": TeradataScanner,
}

# ================================================================
# 3. 自动发现所有已注册迁移路径
#    get_registered_paths() 读取各规则模块的 MIGRATION_INFO
# ================================================================
MIGRATION_PATHS = get_registered_paths()
AVAILABLE_KEYS = set(MIGRATION_PATHS.keys())

# 全局缓存
_current_result: AssessmentResult = None
_metadata: MigrationMetadata = None
_current_path: str = next(iter(AVAILABLE_KEYS)) if AVAILABLE_KEYS else "gp_dws"


def get_or_create_result(path_key: str = None):
    global _current_result, _metadata, _current_path

    if path_key and path_key in AVAILABLE_KEYS and path_key != _current_path:
        _current_path = path_key
        _current_result = None

    if _current_result is None:
        cfg = MIGRATION_PATHS[_current_path]
        source = cfg["source"]
        target = cfg["target"]

        scanner_cls = SCANNER_MAP.get(source, SampleScanner)
        scanner = scanner_cls() if scanner_cls != GPScanner else scanner_cls()
        _metadata = scanner.scan()

        rules = get_rules(source, target)
        rules_mod_name = f"rules.{source}_to_dws" if source != "sqlserver" else "rules.mssql_to_dws"
        try:
            mod = __import__(rules_mod_name, fromlist=["load_weights"])
            weights = mod.load_weights()
        except (ImportError, AttributeError):
            weights = {}

        analyzer = MigrationAnalyzer(
            metadata=_metadata, rules=rules,
            category_weights=weights,
            source_type=source, target_type=target,
        )
        _current_result = analyzer.analyze()
    return _current_result


@app.route("/")
def index():
    path_key = request.args.get("path", _current_path)
    if path_key not in AVAILABLE_KEYS:
        path_key = _current_path
    result = get_or_create_result(path_key=path_key)
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


@app.route("/poc")
def poc():
    result = get_or_create_result()
    return render_template("poc.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)

@app.route("/recommendations")
def recommendations():
    result = get_or_create_result()
    return render_template("recommendations.html", result=result,
                           current_path=_current_path, paths=MIGRATION_PATHS)


@app.route("/switch-path/<path_key>")
def switch_path(path_key):
    if path_key in AVAILABLE_KEYS:
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
        "capacity_planning": result.capacity_planning,
        "batch_strategy": result.batch_strategy,
        "workload_estimate": result.workload_estimate,
        "poc_recommendations": {
            "summary": {
                "total_cases": result.poc_recommendations.get("summary", {}).get("total_cases", 0),
                "total_hours": result.poc_recommendations.get("summary", {}).get("total_estimated_hours", 0),
                "timeline": result.poc_recommendations.get("summary", {}).get("timeline_estimate", ""),
            },
            "levels": {
                k: {"case_count": v.get("case_count", 0), "hours": v.get("level_hours", 0)}
                for k, v in result.poc_recommendations.get("levels", {}).items()
            },
        } if result.poc_recommendations else {},
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
    if path_key in AVAILABLE_KEYS:
        _current_path = path_key

    cfg = MIGRATION_PATHS[_current_path]
    source = cfg["source"]
    target = cfg["target"]
    scanner_cls = SCANNER_MAP.get(source, SampleScanner)
    scanner = scanner_cls()
    _metadata = scanner.scan()

    for field in ["table_count", "view_count", "function_count", "total_capacity",
                   "etl_tool", "scheduler_tool"]:
        if request.form.get(field):
            val = request.form.get(field)
            if field in ("table_count", "view_count", "function_count"):
                val = int(val)
            setattr(_metadata, field, val)

    rules = get_rules(source, target)
    rules_mod_name = f"rules.{source}_to_dws" if source != "sqlserver" else "rules.mssql_to_dws"
    try:
        mod = __import__(rules_mod_name, fromlist=["load_weights"])
        weights = mod.load_weights()
    except (ImportError, AttributeError):
        weights = {}

    analyzer = MigrationAnalyzer(
        metadata=_metadata, rules=rules,
        category_weights=weights,
        source_type=source, target_type=target,
    )
    _current_result = analyzer.analyze()
    return jsonify({"status": "ok", "score": _current_result.overall_score,
                    "path": _current_path})


# ================================================================

# 持久化: 保存评估结果

# ================================================================

import json

import sys as _sys

_sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))

try:

    from shared.db import save_assessment, create_project, list_projects

    DB_AVAILABLE = True

except Exception:

    DB_AVAILABLE = False



@app.route("/api/save-assessment", methods=["POST"])

def api_save_assessment():

    """保存评估结果到项目"""

    if not DB_AVAILABLE:

        return jsonify({"status": "error", "msg": "数据库未就绪"})

    data = request.get_json() or {}

    project_name = data.get("project_name", "")

    if not project_name:

        return jsonify({"status": "error", "msg": "请提供项目名称"})

    # Find or create project

    projects = list_projects()

    pid = None

    for p in projects:

        if p["name"] == project_name:

            pid = p["id"]

            break

    if not pid:

        pid = create_project(

            name=project_name,

            source_type=data.get("source_type", ""),

            target_type=data.get("target_type", ""),

        )

    save_assessment(

        project_id=pid,

        source_type=data.get("source_type", ""),

        target_type=data.get("target_type", ""),

        overall_score=data.get("overall_score", 0),

        risk_level=data.get("risk_level", ""),

        rules_count=data.get("rules_count", 0),

        critical_issues=data.get("critical_issues", 0),

        metadata=data.get("metadata"),

    )

    return jsonify({"status": "ok", "project_id": pid})


if __name__ == "__main__":
    print("=" * 50)
    print("  迁移智能评估系统 - Web UI")
    print(f"  自动发现 {len(AVAILABLE_KEYS)} 条迁移路径")
    for key, cfg in sorted(MIGRATION_PATHS.items()):
        print(f"    {cfg.get('icon', '')} {cfg['label']}")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5010")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5010)
