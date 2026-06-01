# -*- coding: utf-8 -*-
import requests, pandas as pd, numpy as np, concurrent.futures
import warnings; warnings.filterwarnings('ignore')
import sys; sys.stdout.reconfigure(encoding='utf-8')

def build_pool():
    sectors = {
        "汽车": ["600066宇通客车","000957中通客车","600686金龙汽车","000868安凯客车","600213亚星客车","600166福田汽车","002594比亚迪","600418江淮汽车","601238广汽集团","601633长城汽车","600104上汽集团","000625长安汽车","601127赛力斯","600741华域汽车","601689拓普集团","002920德赛西威","002050三花智控","600660福耀玻璃","002074国轩高科","000338潍柴动力","601799星宇股份","601966玲珑轮胎"],
        "电子": ["002371北方华创","688981中芯国际","688012中微公司","603986兆易创新","002049紫光国微","600703三安光电","002185华天科技","600584长电科技","300661圣邦股份","300782卓胜微","603501韦尔股份","002475立讯精密","000725京东方A"],
        "新能源": ["300750宁德时代","300274阳光电源","601012隆基绿能","600438通威股份","002459晶澳科技","688599天合光能","300014亿纬锂能","002850科达利","300124汇川技术"],
        "医药": ["600276恒瑞医药","300760迈瑞医疗","300015爱尔眼科","603259药明康德","000661长春高新","300122智飞生物","000538云南白药","600436片仔癀","300347泰格医药","300896爱美客","002007华兰生物","300003乐普医疗"],
        "消费": ["600519贵州茅台","000858五粮液","000568泸州老窖","002304洋河股份","600809山西汾酒","600887伊利股份","603288海天味业","000895双汇发展","000333美的集团","000651格力电器","600690海尔智家"],
        "金融": ["601318中国平安","600036招商银行","600030中信证券","601688华泰证券","300059东方财富","601398工商银行","601939建设银行","601166兴业银行","002142宁波银行"],
        "周期": ["601857中国石油","601088中国神华","600585海螺水泥","600900长江电力","600309万华化学","601225陕西煤业","002466天齐锂业","002460赣锋锂业","601899紫金矿业","600547山东黄金"],
        "机械军工": ["600031三一重工","601100恒立液压","300450先导智能","600150中国船舶","600893航发动力","600760中航沈飞"],
        "科技通信": ["002230科大讯飞","300033同花顺","600570恒生电子","688111金山办公","000063中兴通讯","600941中国移动","300502新易盛","300308中际旭创"],
        "地产基建": ["000002万科A","600048保利发展","601668中国建筑","601390中国中铁","600019宝钢股份"],
        "其他": ["002714牧原股份","300498温氏股份","002352顺丰控股","601919中远海控","600009上海机场","600029南方航空","601111中国国航","300413芒果超媒","002555三七互娱"],
    }
    pool = {}
    for sector, stocks in sectors.items():
        for s in stocks:
            pool[s[:6]] = s[6:]
    print(f"Stock pool: {len(pool)} stocks across {len(sectors)} sectors")
    return pool

STOCK_POOL = build_pool()

def fetch(code):
    sym = f"sh{code}" if code[0] in "69" else f"sz{code}"
    tried = [sym]
    for s in tried:
        try:
            r = requests.get("https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
                params={"param": f"{s},day,,,120,qfq"},
                headers={"User-Agent":"Mozilla/5.0"}, timeout=8).json()
            kls = r["data"][s]["qfqday"]
            closes = [float(k[2]) for k in kls]
            dates = [k[0] for k in kls]
            return dates, np.array(closes)
        except:
            alt = f"sz{code}" if code[0] in "69" else f"sh{code}"
            if alt not in tried:
                tried.append(alt)
    return None, None

print("Fetching Yutong Bus(600066) baseline...")
yt_dates, yt_close = fetch("600066")
yt_ret = {}
for i in range(1, len(yt_dates)):
    yt_ret[yt_dates[i]] = (yt_close[i]/yt_close[i-1]-1)*100

print(f"Yutong Bus: close={yt_close[-1]:.2f}, 3m_ret={(yt_close[-1]/yt_close[0]-1)*100:+.2f}%, vol={np.std(list(yt_ret.values()))*np.sqrt(252):.2f}%")
print(f"\nScanning {len(STOCK_POOL)-1} stocks with 15 threads...")

results = []
codes = [c for c in STOCK_POOL if c != "600066"]
total = len(codes)

def scan(code):
    name = STOCK_POOL[code]
    dates, closes = fetch(code)
    if dates is None or len(dates) < 20: return None
    rets = {}
    for i in range(1, len(dates)):
        rets[dates[i]] = (closes[i]/closes[i-1]-1)*100
    common = sorted(set(yt_ret.keys()) & set(rets.keys()))
    if len(common) < 15: return None
    ya = np.array([yt_ret[d] for d in common])
    sa = np.array([rets[d] for d in common])
    corr = np.corrcoef(ya, sa)[0,1]
    same = np.mean(((ya>0)&(sa>0))|((ya<0)&(sa<0)))*100
    r3 = (closes[-1]/closes[0]-1)*100
    return {"code":code,"name":name,"corr":round(corr,4),"same%":round(same,1),"ret%":round(r3,2),"days":len(common)}

with concurrent.futures.ThreadPoolExecutor(max_workers=15) as exe:
    fs = {exe.submit(scan, c): c for c in codes}
    done = 0
    for f in concurrent.futures.as_completed(fs):
        done += 1
        r = f.result()
        if r: results.append(r)
        if done % 60 == 0:
            print(f"  progress: {done}/{total}, found={len(results)}")

results.sort(key=lambda x: x["corr"], reverse=True)

print(f"\n{'='*70}")
print(f"Total found: {len(results)} stocks correlated with Yutong Bus(600066)")
print(f"{'='*70}")

if results:
    print(f"\n{'Rank':<6}{'Code':<10}{'Name':<14}{'Corr':<10}{'SameDir%':<10}{'SelfRet%':<12}{'Days':<6}")
    print("-" * 68)
    for i, r in enumerate(results, 1):
        print(f"{i:<6}{r['code']:<10}{r['name']:<14}{r['corr']:<10.4f}{r['same%']:<10.1f}{r['ret%']:<+12.2f}{r['days']:<6}")

    # Tier summary
    high = [r for r in results if r['corr']>=0.55]
    mid = [r for r in results if 0.45<=r['corr']<0.55]
    mod = [r for r in results if 0.35<=r['corr']<0.45]
    low = [r for r in results if r['corr']<0.35]

    print(f"\n>> High (r>=0.55): {len(high)}")
    for r in high:
        print(f"  {r['code']} {r['name']} r={r['corr']:.4f} ret={r['ret%']:+.2f}%")
    print(f">> Medium (0.45-0.55): {len(mid)}")
    for r in mid:
        print(f"  {r['code']} {r['name']} r={r['corr']:.4f} ret={r['ret%']:+.2f}%")
    print(f">> Moderate (0.35-0.45): {len(mod)}")
    for r in mod:
        print(f"  {r['code']} {r['name']} r={r['corr']:.4f} ret={r['ret%']:+.2f}%")
    print(f">> Low (<0.35): {len(low)}")

    pd.DataFrame(results).to_csv(r"C:\Users\52985\.claude\scripts\sim_stocks_v2.csv", index=False, encoding='utf-8-sig')
else:
    print("No correlated stocks found.")

print(f"\nDisclaimer: Statistical analysis only, not investment advice.")
