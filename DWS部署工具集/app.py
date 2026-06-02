"""
DWS 部署工具集 - Web UI (Flask)
面向 GaussDB(DWS) MPP 数仓集群部署
管理平台: FusionInsight Manager
"""

import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("dws_dashboard.html")

@app.route("/flow")
def flow():
    return render_template("dws_flow.html")

@app.route("/checklist")
def checklist():
    return render_template("dws_checklist.html")

if __name__ == "__main__":
    print("=" * 50)
    print("  DWS 部署工具集 - Web UI")
    print("=" * 50)
    print("  访问地址: http://127.0.0.1:5013")
    print("=" * 50)
    app.run(debug=False, host="127.0.0.1", port=5013)
