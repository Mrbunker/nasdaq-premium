"""Cross-check all available exchange closes against a second provider."""
import json
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlencode
from project import ROOT, RAW, download, write_csv

path = ROOT / "data/history.json"
bundle = json.loads(path.read_text())


def check(fund):
    code = fund["code"]
    params = {"secid": ("1." if code.startswith("5") else "0.") + code,
              "klt": 101, "fqt": 0, "beg": "0", "end": bundle["cutoff"].replace("-", ""),
              "fields1": "f1,f2,f3,f4,f5,f6", "fields2": "f51,f52,f53,f54,f55,f56,f57", "lmt": 10000}
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get?" + urlencode(params)
    data = json.loads(download(url, RAW / f"{code}_em_price_full_check.json"))["data"]
    full = [row.split(",") for row in data["klines"]]
    full = [row for row in full if row[0] <= bundle["cutoff"]]
    second = {row[0]: float(row[2]) for row in full}
    primary = {r["date"]: r["close"] for r in fund["series"] if r["close"] is not None}
    common = sorted(primary.keys() & second.keys())
    mismatch = [{"date": date, "tencent": primary[date], "eastmoney": second[date]}
                for date in common if abs(primary[date] - second[date]) > 0.00051]
    fund["price_cross_check"] = {"source": url, "common_dates": len(common),
                                 "mismatches": mismatch, "eastmoney_total": data["dktotal"],
                                 "second_count": len(second),
                                 "tencent_only_dates": sorted(primary.keys() - second.keys()),
                                 "eastmoney_only_dates": sorted(second.keys() - primary.keys())}
    if not full or set(primary) != set(second):
        raise ValueError(code + ": inconsistent price coverage")
    # Use one provider uniformly, retain every discrepancy rather than averaging or mixing sources.
    nav = {r["date"]: r["nav"] for r in fund["series"] if r["nav"] is not None}
    records = []
    for date in sorted(nav.keys() | second.keys()):
        n, p = nav.get(date), second.get(date)
        records.append({"date": date, "nav": n, "close": p,
                        "premium_pct": (p / n - 1) * 100 if n and p else None})
    fund["series"] = records
    matched = [r for r in records if r["nav"] and r["close"]]
    fund.update(price_first=min(second), price_last=max(second), price_count=len(second),
                matched_count=len(matched), latest_matched=matched[-1],
                price_source=url,
                missing_nav_on_price_dates=len(second.keys() - nav.keys()))
    write_csv(ROOT / f"data/{code}.csv", records, ["date", "nav", "close", "premium_pct"])
    ohlcv = [{"date": r[0], "open": float(r[1]), "close": float(r[2]), "high": float(r[3]),
              "low": float(r[4]), "volume_lots": float(r[5]), "amount_cny": float(r[6])} for r in full]
    if any(not (0 < r["low"] <= r["close"] <= r["high"]) for r in ohlcv):
        raise ValueError(code + ": invalid final OHLC")
    write_csv(ROOT / f"data/{code}_ohlcv.csv", ohlcv, list(ohlcv[0]))
    print(code, "cross-check", len(common), "mismatches", len(mismatch), "EM", len(second),
          "total", data["dktotal"], flush=True)
    return fund


with ThreadPoolExecutor(max_workers=3) as pool:
    bundle["funds"] = list(pool.map(check, bundle["funds"]))
bundle["methodology"]["price_source"] = "东方财富历史日线为主，腾讯交叉核验；差异保留在各基金price_cross_check中。"
bundle["methodology"]["cutoff"] = f"仅保留截至{bundle['cutoff']}的完整日线，剔除其后记录。"
path.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")))
all_rows = [{"code": f["code"], "name": f["name"], "index": f["index"], **r}
            for f in bundle["funds"] for r in f["series"]]
write_csv(ROOT / "data/all_funds_history.csv", all_rows,
          ["code", "name", "index", "date", "nav", "close", "premium_pct"])
summary = []
for fund in bundle["funds"]:
    r = fund["latest_matched"]
    summary.append({"code": fund["code"], "name": fund["name"], "index": fund["index"],
                    "price_first": fund["price_first"], "price_last": fund["price_last"],
                    "nav_last": fund["nav_last"], "matched_count": fund["matched_count"],
                    "latest_matched_date": r["date"], "nav": r["nav"], "close": r["close"],
                    "premium_pct": r["premium_pct"],
                    "price_cross_checked_dates": fund["price_cross_check"]["common_dates"],
                    "price_mismatches": len(fund["price_cross_check"]["mismatches"])})
write_csv(ROOT / "data/summary.csv", summary, list(summary[0]))
discrepancies = [{"code": f["code"], **r} for f in bundle["funds"]
                 for r in f["price_cross_check"]["mismatches"]]
write_csv(ROOT / "data/source_discrepancies.csv", discrepancies,
          ["code", "date", "tencent", "eastmoney"])
print("Final price provider: Eastmoney; retained discrepancies:", len(discrepancies), flush=True)
