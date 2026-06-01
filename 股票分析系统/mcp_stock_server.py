# -*- coding: utf-8 -*-
"""
MCP Stock Data Server - 提供股票数据查询的 MCP 服务器
通过 Model Context Protocol 让 Claude 直接调用股票数据
"""
import requests, json, sys, os, numpy as np, pandas as pd
from datetime import datetime, timedelta

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_kline(code, days=120):
    sym = "sh" + code if code[0] in "69" else "sz" + code
    for s in [sym, "sz" + code if code[0] in "69" else "sh" + code]:
        try:
            r = requests.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                params={"param": s + ",day,,," + str(days) + ",qfq"},
                headers=HEADERS, timeout=8).json()
            kls = r["data"][s]["qfqday"]
            rows = [{"date": k[0], "open": float(k[1]), "close": float(k[2]),
                     "high": float(k[3]), "low": float(k[4]), "vol": float(k[5])} for k in kls]
            df = pd.DataFrame(rows)
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            df["ret"] = df["close"].pct_change() * 100
            df["ma5"] = df["close"].rolling(5).mean()
            df["ma20"] = df["close"].rolling(20).mean()
            return df
        except:
            continue
    return None

# MCP 工具函数
MCP_TOOLS = {}

def tool(name, desc):
    def dec(f):
        MCP_TOOLS[name] = {"fn": f, "desc": desc}
        return f
    return dec

@tool("stock_quote", "Get current stock price and basic stats")
def stock_quote(args):
    code = args.get("code", "600066")
    df = fetch_kline(code)
    if df is None:
        return {"error": "cannot fetch data"}
    c = df["close"].values
    ret = (c[-1] / c[0] - 1) * 100
    dr = np.diff(c) / c[:-1]
    vol = np.std(dr, ddof=1) * np.sqrt(252) * 100
    peak = np.maximum.accumulate(c)
    mdd = np.min((c - peak) / peak) * 100
    return {
        "code": code, "close": round(c[-1], 2),
        "return_3m": round(ret, 2), "volatility": round(vol, 2),
        "max_drawdown": round(mdd, 2), "high": round(np.max(c), 2),
        "low": round(np.min(c), 2), "ma5": round(df["ma5"].iloc[-1], 2),
        "ma20": round(df["ma20"].iloc[-1], 2), "data_days": len(df)
    }

@tool("stock_kline", "Get daily K-line data for a stock")
def stock_kline(args):
    code = args.get("code", "600066")
    days = args.get("days", 120)
    df = fetch_kline(code, days)
    if df is None:
        return {"error": "cannot fetch data"}
    return {"code": code, "data": df.tail(30).to_dict("records")}

@tool("stock_compare", "Compare multiple stocks performance")
def stock_compare(args):
    codes = args.get("codes", ["600066", "000333", "300750"])
    results = {}
    for code in codes:
        df = fetch_kline(code)
        if df is not None:
            c = df["close"].values
            ret = (c[-1] / c[0] - 1) * 100
            dr = np.diff(c) / c[:-1]
            vol = np.std(dr, ddof=1) * np.sqrt(252) * 100
            peak = np.maximum.accumulate(c)
            mdd = np.min((c - peak) / peak) * 100
            results[code] = {"close": round(c[-1], 2), "ret_3m": round(ret, 2),
                             "vol": round(vol, 2), "mdd": round(mdd, 2)}
    return results

# MCP 服务器入口 (stdio 模式)
def handle_request(req):
    req_id = req.get("id", 0)
    method = req.get("method", "")
    params = req.get("params", {})

    if method == "mcp.list_tools":
        return {"jsonrpc": "2.0", "id": req_id, "result": {
            "tools": [{"name": k, "description": v["desc"]} for k, v in MCP_TOOLS.items()]
        }}
    elif method == "mcp.call_tool":
        tool_name = params.get("name", "")
        args = params.get("arguments", {})
        if tool_name in MCP_TOOLS:
            result = MCP_TOOLS[tool_name]["fn"](args)
            return {"jsonrpc": "2.0", "id": req_id, "result": {"content": [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}]}}
        else:
            return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Tool not found"}}
    else:
        return {"jsonrpc": "2.0", "id": req_id, "result": {}}

if __name__ == "__main__":
    # stdio 模式: 逐行读取 JSON-RPC 请求并响应
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            resp = handle_request(req)
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
        except json.JSONDecodeError:
            continue
        except Exception as e:
            sys.stderr.write("Error: " + str(e) + "\n")
            sys.stderr.flush()
