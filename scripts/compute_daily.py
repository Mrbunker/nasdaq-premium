"""Calculate price-change comparisons against the immediately preceding exchange session."""
import json
from project import ROOT, write_csv

FIELDS = ["date", "nav", "close", "premium_pct", "prev_trade_date", "daily_nav_pct",
          "daily_close_pct", "premium_contribution_pp", "prev_premium_pct", "premium_change_pp",
          "daily_status"]


def compute(fund):
    events = {r["date"] for r in fund["nav_events"]}
    previous = None
    for row in fund["series"]:
        row.update({key: None for key in FIELDS[4:]})
        date = row["date"]
        if date in events:
            row["premium_pct"] = None  # NAV and exchange shares may change units on different dates.
            row["daily_status"] = "份额折算日，不比较涨跌或溢价"
        if row["close"] is None:
            row["daily_status"] = row["daily_status"] or "当日无场内收盘价"
            continue
        if previous is None:
            row["daily_status"] = row["daily_status"] or "首个场内交易日，无前日价格"
        else:
            prev_date = previous["date"]
            row["prev_trade_date"] = prev_date
            if any(prev_date <= event <= date for event in events):
                row["daily_status"] = "跨越份额折算，不计算原始单位价格涨跌"
            else:
                row["daily_close_pct"] = (row["close"] / previous["close"] - 1) * 100
                row["prev_premium_pct"] = previous["premium_pct"]
                if row["nav"] is None:
                    row["daily_status"] = "当日净值未公布，净值涨跌和溢价贡献留空"
                elif previous["nav"] is None:
                    row["daily_status"] = "上一场内交易日净值缺失，不跨日补算"
                else:
                    row["daily_nav_pct"] = (row["nav"] / previous["nav"] - 1) * 100
                    row["premium_contribution_pp"] = row["daily_close_pct"] - row["daily_nav_pct"]
                    if row["premium_pct"] is not None and previous["premium_pct"] is not None:
                        row["premium_change_pp"] = row["premium_pct"] - previous["premium_pct"]
                    row["daily_status"] = "正常"
        previous = row
    return fund


def main():
    path = ROOT / "data/history.json"
    bundle = json.loads(path.read_text())
    bundle["funds"] = [compute(fund) for fund in bundle["funds"]]
    bundle["methodology"]["daily_changes"] = {
        "baseline": "上一有场内收盘价的交易日；月初首日使用筛选前的前一交易日，不在筛选后重新计算。",
        "daily_nav_pct": "(当日单位净值 / 上一场内交易日单位净值 - 1) × 100，单位%",
        "daily_close_pct": "(当日场内收盘价 / 上一场内交易日收盘价 - 1) × 100，单位%",
        "premium_contribution_pp": "场内日涨跌幅 - 净值日涨跌幅，单位百分点；正值放大收益，负值拖累收益。",
        "premium_change_pp": "当日事后溢价率 - 上一场内交易日事后溢价率，单位百分点，区别于溢价贡献。",
        "missing": "净值缺失时只保留可计算的场内涨跌；不跳过缺失交易日来补算净值涨跌。",
        "corporate_actions": "份额折算日和跨越折算的价格区间不计算日涨跌；折算日事后溢价也留空，以免净值与价格份额口径错位。",
        "timing": "QDII同日净值和场内价格收盘时间不同；每日差额属于事后对比，不是当时可知的实时套利收益。",
    }
    all_rows = []
    for fund in bundle["funds"]:
        write_csv(ROOT / f"data/{fund['code']}.csv", fund["series"], FIELDS)
        for row in fund["series"]:
            all_rows.append({"code": fund["code"], "name": fund["name"], "index": fund["index"], **row})
    write_csv(ROOT / "data/all_funds_history.csv", all_rows, ["code", "name", "index", *FIELDS])
    write_csv(ROOT / "data/daily_returns.csv", [r for r in all_rows if r["close"] is not None],
              ["code", "name", "index", *FIELDS])
    path.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")))
    valid = sum(r["premium_contribution_pp"] is not None for r in all_rows)
    print("Daily paired comparisons:", valid)


if __name__ == "__main__":
    main()
