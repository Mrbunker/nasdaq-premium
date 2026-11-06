"""Export a 16-page PDF of daily paired bars and the premium contribution."""
import datetime as dt
import json
import math
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR", str(ROOT / ".cache" / "matplotlib"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from matplotlib.font_manager import FontProperties, fontManager

candidates = [os.environ.get('NAQD_FONT_PATH',''),
              '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
              '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc']
font_path = next((p for p in candidates if p and Path(p).is_file()),None)
font = FontProperties(fname=font_path) if font_path else FontProperties(family='DejaVu Sans')
if font_path:
    fontManager.addfont(font_path)
plt.rcParams.update({"font.family": font.get_name(), "axes.unicode_minus": False,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.spines.left": False, "axes.spines.bottom": False,
                     "text.color": "#1f2937", "xtick.color": "#6b7280", "ytick.color": "#6b7280"})
bundle = json.loads((ROOT / "data/history.json").read_text())
end = dt.date.fromisoformat(bundle["cutoff"])
start = (end - dt.timedelta(days=30)).isoformat()
colors = ["#cf4d4a", "#218765"]
def change_color(value):
    return colors[0] if value > 0 else colors[1] if value < 0 else '#87939f'
(ROOT / "charts").mkdir(exist_ok=True)
with PdfPages(ROOT / "charts/daily_returns_all16.pdf") as pdf:
    for number, fund in enumerate(bundle["funds"]):
        rows = [r for r in fund["series"] if r["date"] >= start and r["close"] is not None]
        x = list(range(len(rows)))
        nav = [r["daily_nav_pct"] if r["daily_nav_pct"] is not None else math.nan for r in rows]
        close = [r["daily_close_pct"] if r["daily_close_pct"] is not None else math.nan for r in rows]
        contribution = [r["premium_contribution_pp"] if r["premium_contribution_pp"] is not None else math.nan for r in rows]
        fig, axes = plt.subplots(2, 1, figsize=(12, 7.8), sharex=True, gridspec_kw={"height_ratios": [1.5, 1]}, facecolor="#f8f9fb")
        axes[0].bar([i-.13 for i in x], nav, .22, facecolor='none', edgecolor=[change_color(v) for v in nav], linewidth=1.3, label="净值日涨跌 · 空心柱")
        axes[0].bar([i+.13 for i in x], close, .22, color=[change_color(v) for v in close], label="场内日涨跌 · 实心柱")
        axes[1].bar(x, contribution, .30, color=[change_color(v) for v in contribution])
        for i, ax in enumerate(axes):
            values = nav + close if i == 0 else contribution
            limit = max(.5 if i == 0 else .25, *[abs(v) for v in values if math.isfinite(v)]) * 1.15
            ax.set_ylim(-limit, limit)
            ax.set_facecolor("#f8f9fb"); ax.grid(axis="y", color="#e5e9ef"); ax.set_axisbelow(True)
            ax.axhline(0, color="#aeb8c4", lw=1)
            ax.tick_params(length=0, labelsize=9)
        axes[0].set_title("每日涨跌幅 · %", loc="left", fontsize=12)
        axes[0].legend(loc="upper right", frameon=False, ncol=2, fontsize=10)
        axes[1].set_title("溢价贡献 · 百分点（场内涨跌幅 − 净值涨跌幅）", loc="left", fontsize=12)
        ticks = list(range(0, len(rows), max(1, math.ceil(len(rows)/10))))
        axes[1].set_xticks(ticks, [rows[i]["date"][5:] for i in ticks])
        fig.suptitle(f"{fund['code']}  {fund['name']}", x=.07, ha="left", fontsize=22)
        fig.text(.07, .91, f"{fund['index']}  ·  {start} — {end}  ·  红涨绿跌；下排正值放大收益、负值拖累收益", color="#6b7280", fontsize=11)
        fig.text(.07, .035, "日涨跌相对上一交易日；缺失净值与份额折算区间留空。净值未公布时，仅展示可计算的场内涨跌。\nQDII净值与场内价格收盘时间不同，本图为事后比较，不是实时套利收益或含分红总回报。", color="#6b7280", fontsize=9, linespacing=1.6)
        fig.subplots_adjust(left=.07, right=.97, top=.83, bottom=.14, hspace=.35)
        pdf.savefig(fig)
        if number == 0:
            fig.savefig(ROOT / "charts/daily_returns_example.png", dpi=170)
        plt.close(fig)
print("Exported daily bars PDF: 16 pages")
