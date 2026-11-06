"""Download actual historical NAV and unadjusted exchange closes; no credentials needed."""
import argparse
import os
import datetime as dt
import json
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.parse import urlencode

from project import ROOT, RAW, DATA, download, write_csv, latest_complete_day

CUTOFF = latest_complete_day().isoformat()
FUNDS = [tuple(f[key] for key in ['code','name','index'])
         for f in json.loads((ROOT/'config/funds.json').read_text())]


def fetch_fund(item):
    code, name, index = item
    nav_url = f"https://fund.eastmoney.com/pingzhongdata/{code}.js"
    text = download(nav_url, RAW / f"{code}_pingzhongdata.js")
    match = re.search(r"var Data_netWorthTrend\s*=\s*(\[.*?\]);", text)
    if not match:
        raise ValueError(f"{code}: NAV missing")
    source = json.loads(match.group(1))
    nav = {}
    full_nav = {}
    events = []
    tz = dt.timezone(dt.timedelta(hours=8))
    for record in source:
        date = dt.datetime.fromtimestamp(record["x"] / 1000, tz).date().isoformat()
        value = record.get("y")
        if value is not None and value > 0:
            full_nav[date] = float(value)
        if date <= CUTOFF and value is not None and value > 0:
            nav[date] = float(value)
            if record.get("unitMoney"):
                events.append({"date": date, "description": record["unitMoney"]})
    if not nav:
        raise ValueError(f"{code}: empty NAV")

    # Independently check latest NAV entries against the site's history table API.
    check_url = "https://api.fund.eastmoney.com/f10/lsjz?" + urlencode(
        {"fundCode": code, "pageIndex": 1, "pageSize": 5})
    check = json.loads(download(check_url, RAW / f"{code}_nav_check.json",
                                "https://fundf10.eastmoney.com/"))
    check_rows = (check.get("Data") or {}).get("LSJZList", [])
    if len(source) != check.get("TotalCount"):
        raise ValueError(f"{code}: NAV count mismatch {len(source)} vs {check.get('TotalCount')}")
    for record in check_rows:
        if abs(full_nav[record["FSRQ"]] - float(record["DWJZ"])) > 1e-8:
            raise ValueError(f"{code}: latest NAV mismatch")

    market_code = ("sh" if code.startswith("5") else "sz") + code
    closes = {}
    first_year = int(min(nav)[:4])
    quote_urls = []
    for year in range(first_year, int(CUTOFF[:4]) + 1):
        end = min(f"{year}-12-31", CUTOFF)
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get?" + urlencode(
            {"param": f"{market_code},day,{year}-01-01,{end},640,"})
        quote_urls.append(url)
        response = json.loads(download(url, RAW / f"{code}_price_{year}.json"))
        if response.get("code") != 0:
            raise ValueError(f"{code}: price API error")
        payload = response.get("data", {}).get(market_code, {})
        rows = payload.get("day", [])
        # Only 'day', never qfqday/hfqday: actual traded prices are required for NAV comparison.
        if not rows and ("qfqday" in payload or "hfqday" in payload):
            raise ValueError(f"{code}: adjusted prices returned unexpectedly")
        for row in rows:
            date = row[0]
            if f"{year}-01-01" <= date <= end:
                val = {"date": date, "open": float(row[1]), "close": float(row[2]),
                       "high": float(row[3]), "low": float(row[4]), "volume_lots": float(row[5])}
                if not 0 < val["low"] <= val["close"] <= val["high"]:
                    raise ValueError(f"{code}: invalid OHLC {row}")
                if date in closes and closes[date] != val:
                    raise ValueError(f"{code}: conflicting duplicate {date}")
                closes[date] = val
    if not closes:
        raise ValueError(f"{code}: no exchange prices")

    records = []
    for date in sorted(nav.keys() | closes.keys()):
        n = nav.get(date)
        p = closes.get(date, {}).get("close")
        records.append({"date": date, "nav": n, "close": p,
                        "premium_pct": (p / n - 1) * 100 if n and p else None})
    matched = [r for r in records if r["nav"] and r["close"]]
    meta = {
        "code": code, "name": name, "index": index, "market": market_code[:2],
        "nav_first": min(nav), "nav_last": max(nav), "nav_count": len(nav),
        "price_first": min(closes), "price_last": max(closes), "price_count": len(closes),
        "matched_count": len(matched), "latest_matched": matched[-1],
        "missing_nav_on_price_dates": len(closes.keys() - nav.keys()),
        "nav_events": events, "nav_source": nav_url,
        "nav_check_source": check_url, "price_sources": quote_urls,
        "nav_check_passed": True,
    }
    write_csv(DATA / f"{code}.csv", records, ["date", "nav", "close", "premium_pct"])
    write_csv(DATA / f"{code}_ohlcv.csv", sorted(closes.values(), key=lambda r: r["date"]),
              ["date", "open", "close", "high", "low", "volume_lots"])
    print(f"{code} {name}: NAV {len(nav)} / price {len(closes)} / matched {len(matched)} "
          f"({min(closes)} .. {max(closes)})", flush=True)
    return {**meta, "series": records}


def main():
    global CUTOFF
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cutoff',default=CUTOFF)
    parser.add_argument('--cached',action='store_true')
    args = parser.parse_args()
    day = dt.date.fromisoformat(args.cutoff)
    if day > latest_complete_day():
        parser.error('cutoff must not include an unfinished Chinese session')
    CUTOFF = day.isoformat()
    os.environ['NAQD_REFRESH'] = '0' if args.cached else '1'
    DATA.mkdir(exist_ok=True)
    results = {}
    errors = []
    with ThreadPoolExecutor(max_workers=3) as pool:
        futures = {pool.submit(fetch_fund, fund): fund for fund in FUNDS}
        for future in as_completed(futures):
            try:
                fund = future.result()
                results[fund["code"]] = fund
            except Exception as exc:
                errors.append({"code": futures[future][0], "error": str(exc)})
                print("ERROR", futures[future][0], str(exc), flush=True)
    if errors:
        RAW.mkdir(parents=True,exist_ok=True)
        (RAW/'fetch_errors.json').write_text(json.dumps(errors,ensure_ascii=False,indent=2))
        raise SystemExit(f'{len(errors)} funds failed; the previous snapshot was preserved')
    bundle = {
        "fetched_at": dt.datetime.now(dt.timezone(dt.timedelta(hours=8))).isoformat(),
        "cutoff": CUTOFF,
        "cache_reused": args.cached,
        "methodology": {
            "nav": "基金公布的人民币单位净值 DWJZ，不使用累计净值，也不使用盘中估值",
            "close": "交易所日线未复权收盘价，人民币/份",
            "premium_pct": "(同一日期场内收盘价 / 同一估值日期公布单位净值 - 1) × 100",
            "timing": "事后同日期比较。QDII净值含中国收盘之后的海外市场信息，不代表中国收盘时可知的溢价或IOPV溢价。",
            "missing": "缺失日期留空，不前向填充，不插值，不用最新净值替代当日净值。",
            "corporate_actions": "原始单位价格保留份额折算和分红影响；图表不是含分红总回报图。",
        },
        "funds": [results[code] for code, _, _ in FUNDS if code in results], "errors": errors,
    }
    (DATA / "history.json").write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    all_rows = []
    for fund in bundle["funds"]:
        for row in fund["series"]:
            all_rows.append({"code": fund["code"], "name": fund["name"], "index": fund["index"], **row})
    write_csv(DATA / "all_funds_history.csv", all_rows,
              ["code", "name", "index", "date", "nav", "close", "premium_pct"])
    if errors:
        raise SystemExit(f"{len(errors)} funds failed; see data/history.json")


if __name__ == "__main__":
    main()
