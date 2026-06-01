# -*- coding: utf-8 -*-
"""
股票分析工具箱 - 通用可复用版本
Usage:
  python stock_analyzer.py analyze 600066   单只股票分析
  python stock_analyzer.py scan 600066      全市场寻找相似股票
  python stock_analyzer.py compare 600066 000333  多股对比
"""
import requests, numpy as np, pandas as pd, os, sys, time, concurrent.futures
from datetime import datetime, timedelta
import warnings; warnings.filterwarnings('ignore')

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
            df["ma10"] = df["close"].rolling(10).mean()
            df["ma20"] = df["close"].rolling(20).mean()
            df["ma60"] = df["close"].rolling(60).mean()
            return df
        except:
            continue
    return None

def analyze(code, name=""):
    df = fetch_kline(code)
    if df is None:
        return None
    c = df["close"].values
    ret = (c[-1] / c[0] - 1) * 100
    dr = np.diff(c) / c[:-1]
    vol = np.std(dr, ddof=1) * np.sqrt(252) * 100
    peak = np.maximum.accumulate(c)
    mdd = np.min((c - peak) / peak) * 100

    ma5_v = df["ma5"].iloc[-1]
    ma20_v = df["ma20"].iloc[-1]
    ma60_v = df["ma60"].iloc[-1]
    if not pd.isna(ma60_v) and c[-1] > ma60_v and ma5_v > ma20_v:
        trend = "UP"
    elif not pd.isna(ma60_v) and c[-1] < ma60_v and ma5_v < ma20_v:
        trend = "DOWN"
    else:
        trend = "SIDEWAYS"

    return {"code": code, "name": name, "df": df, "close": c[-1], "ret_3m": ret,
            "vol": vol, "mdd": mdd, "high": np.max(c), "low": np.min(c),
            "ma5": ma5_v, "ma20": ma20_v, "ma60": ma60_v, "trend": trend,
            "data_days": len(df)}

def scan(target_code, stock_pool, threshold=0.3):
    target = fetch_kline(target_code)
    if target is None:
        return []
    target_ret = target.set_index("date")["ret"]
    results = []

    def _scan(code, name):
        df = fetch_kline(code)
        if df is None or len(df) < 20:
            return None
        dr = df.set_index("date")["ret"]
        common = target_ret.index.intersection(dr.index)
        if len(common) < 15:
            return None
        ya = target_ret.loc[common]
        sa = dr.loc[common]
        corr = ya.corr(sa)
        if corr > threshold:
            same_dir = ((ya > 0) & (sa > 0)) | ((ya < 0) & (sa < 0))
            same_pct = round(same_dir.sum() / len(common) * 100, 1)
            ret = (df["close"].iloc[-1] / df["close"].iloc[0] - 1) * 100
            return {"code": code, "name": name, "corr": round(corr, 4),
                    "same_dir": same_pct, "ret": round(ret, 2), "days": len(common)}
        return None

    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futures = {ex.submit(_scan, c, n): c for c, n in stock_pool.items() if c != target_code}
        for f in concurrent.futures.as_completed(futures):
            r = f.result()
            if r:
                results.append(r)
    results.sort(key=lambda x: x["corr"], reverse=True)
    return results

def print_report(a):
    if a is None:
        print("Error: no data"); return
    print("=" * 65)
    print("  {} ({})".format(a["name"] or a["code"], a["code"]))
    print("=" * 65)
    print("  Close:      {:>10.2f}".format(a["close"]))
    print("  3M Return:  {:>+10.2f}%".format(a["ret_3m"]))
    print("  Volatility: {:>10.2f}%".format(a["vol"]))
    print("  Max DD:     {:>10.2f}%".format(a["mdd"]))
    print("  Range:      {:.2f} ~ {:.2f}".format(a["low"], a["high"]))
    print("  Trend:      {}  (MA5={:.2f} MA20={:.2f} MA60={:.2f})".format(
        a["trend"], a["ma5"], a["ma20"], a["ma60"]))
    print("  Data:       {} days".format(a["data_days"]))
    print("\n  Timeline:")
    df = a["df"]; step = max(1, len(df) // 6)
    for i in range(0, len(df), step):
        r = df.iloc[i]; chg = r["ret"] if i > 0 else 0
        print("    {}  {:>8.2f}  {:>+6.2f}%".format(str(r["date"])[:10], r["close"], chg))
    r = df.iloc[-1]
    print("    {}  {:>8.2f}  {:>+6.2f}%".format(str(r["date"])[:10], r["close"], r["ret"]))

BUILTIN_POOL = {
    "600066": "Yutong Bus", "600741": "Huayu Auto", "000957": "Zhongtong Bus",
    "600686": "King Long", "600166": "Foton Motor", "002594": "BYD",
    "600418": "JAC Motors", "601238": "GAC Group", "601633": "Great Wall",
    "600104": "SAIC", "000625": "Changan Auto", "601127": "Seres",
    "601689": "Tuopu Group", "002920": "Desay SV", "600660": "Fuyao Glass",
    "300750": "CATL", "000338": "Weichai Power", "002850": "Kedali",
    "002475": "Luxshare", "603501": "Will Semi", "002049": "Unigroup",
    "002371": "NAURA", "688981": "SMIC", "000333": "Midea",
    "000651": "Gree", "600519": "Kweichow Moutai", "000858": "Wuliangye",
    "600036": "CMB", "601318": "Ping An", "600030": "CITIC Sec",
    "300059": "East Money", "300274": "Sungrow", "601012": "LONGi Green",
    "600438": "Tongwei", "600276": "Hengrui", "300760": "Mindray",
    "603259": "WuXi AppTec", "300015": "Aier Eye", "600900": "Yangtze Power",
    "600031": "SANY", "600585": "Conch Cement", "002352": "SF Holding",
    "601899": "Zijin Mining", "002230": "iFLYTEK", "000063": "ZTE",
    "600941": "China Mobile", "603259": "WuXi AppTec",
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage:")
        print("  analyze <code> [name]    - Analyze single stock")
        print("  scan <code> [threshold]  - Find similar stocks")
        print("  compare <c1> <c2> ...    - Compare multiple stocks")
        sys.exit(1)

    cmd = sys.argv[1]; args = sys.argv[2:]

    if cmd == "analyze":
        code = args[0] if args else "600066"
        name = args[1] if len(args) > 1 else BUILTIN_POOL.get(code, "")
        print_report(analyze(code, name))
    elif cmd == "scan":
        code = args[0] if args else "600066"
        th = float(args[1]) if len(args) > 1 else 0.3
        name = BUILTIN_POOL.get(code, "")
        print("Scanning {} stocks for {} ({})...".format(len(BUILTIN_POOL), name or code, code))
        results = scan(code, BUILTIN_POOL, th)
        print("\nFound {} stocks with corr > {}:".format(len(results), th))
        if results:
            print("{:<5} {:<8} {:<16} {:<10} {:<10} {:<10}".format(
                "Rank","Code","Name","Corr","SameDir%","Ret%"))
            print("-" * 60)
            for i, r in enumerate(results[:20], 1):
                print("{:<5} {:<8} {:<16} {:<10.4f} {:<10.1f} {:<+10.2f}".format(
                    i, r["code"], r["name"], r["corr"], r["same_dir"], r["ret"]))
    elif cmd == "compare":
        codes = args if args else ["600066", "000333"]
        results = {}
        for code in codes:
            r = analyze(code, BUILTIN_POOL.get(code, ""))
            if r:
                results[code] = r
        if results:
            print("\n{:<8} {:<14} {:<10} {:<12} {:<10} {:<10} {:<8}".format(
                "Code","Name","Close","3M Ret%","MaxDD%","Vol%","Trend"))
            print("-" * 75)
            for code, d in results.items():
                print("{:<8} {:<14} {:<10.2f} {:<+12.2f} {:<10.2f} {:<10.2f} {:<8}".format(
                    code, d["name"] or "", d["close"], d["ret_3m"], d["mdd"], d["vol"], d["trend"]))
            if len(results) >= 2:
                print("\nCorrelation Matrix:")
                cl = list(results.keys())
                rets_m = {c: results[c]["df"].set_index("date")["ret"] for c in cl}
                print("{:<10}".format(""), end="")
                for c in cl:
                    print(" {:<10}".format(c), end="")
                print()
                for c1 in cl:
                    print("{:<10}".format(c1), end="")
                    for c2 in cl:
                        common = rets_m[c1].index.intersection(rets_m[c2].index)
                        if len(common) > 10:
                            corr = rets_m[c1].loc[common].corr(rets_m[c2].loc[common])
                            print(" {:<10.4f}".format(corr), end="")
                        else:
                            print(" {:<10}".format("-"), end="")
                    print()
    else:
        print("Unknown command:", cmd)