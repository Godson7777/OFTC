import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
from dataclasses import replace
from datetime import datetime
import engine

CSV = '/root/.claude/uploads/531b72a7-242d-5297-9bd1-d07ca8f87be4/018f30b3-XAUUSD_H1.csv'
bars = engine.load(CSV)
free = engine.Config(commission_pct=0.0, slippage=0.0)
loose = dict(use_vol=False, wick_max=0.20, body_min=0.60, size_mult=1.2)

def curve(cfg):
    r = engine.run(bars, cfg)
    xs = [datetime.strptime(t, "%Y-%m-%d %H:%M:%S") for t, _ in r.equity_curve]
    return xs, [e for _, e in r.equity_curve]

BG, FG, GRID = "#12151c", "#e6e9ef", "#2a3040"
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(13, 10), facecolor=BG,
                               gridspec_kw={"height_ratios": [1, 1], "hspace": 0.32})

# --- Panel 1: sinyal momentum vs kontrol acak, tanpa biaya -------------------
for sd in range(1, 11):
    xs, ys = curve(replace(free, random_p=0.03, seed=sd))
    ax1.plot(xs, ys, color="#5a6478", lw=0.9, alpha=0.55,
             label="Kontrol entry acak (10 seed)" if sd == 1 else None)
xs, ys = curve(replace(free, **loose))
ax1.plot(xs, ys, color="#4da3ff", lw=2.2, label="Sinyal Momentum Candle (n=2.609)")
ax1.axhline(10000, color="#8a93a6", lw=1, ls="--", alpha=0.8)
ax1.set_title("Sinyal momentum tidak dapat dibedakan dari entry acak\n"
              "XAUUSD H1 2009-2026  ·  tanpa biaya transaksi  ·  risiko 1% per trade",
              color=FG, fontsize=13, pad=14, loc="left")

# --- Panel 2: dampak biaya pada konfigurasi default --------------------------
for label, over, col in [
    ("Tanpa biaya",                    dict(commission_pct=0.0,  slippage=0.0),  "#4dd4a0"),
    ("Spread emas realistis (0.30)",   dict(commission_pct=0.0,  slippage=0.15), "#ffc861"),
    ("Default script (0.04% + 1 tick)",dict(commission_pct=0.04, slippage=0.01), "#ff6b6b"),
]:
    xs, ys = curve(replace(engine.Config(), **over))
    ax2.plot(xs, ys, color=col, lw=2.0, label=label)
ax2.axhline(10000, color="#8a93a6", lw=1, ls="--", alpha=0.8)
ax2.set_title("Konfigurasi default SOP (53 trade dalam 17 tahun) pada tiga asumsi biaya",
              color=FG, fontsize=13, pad=14, loc="left")

for ax in (ax1, ax2):
    ax.set_facecolor(BG)
    ax.grid(color=GRID, lw=0.7)
    ax.set_axisbelow(True)
    ax.tick_params(colors="#98a2b8", labelsize=9)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    ax.set_ylabel("Ekuitas (USD)", color="#98a2b8", fontsize=10)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:,.0f}"))
    lg = ax.legend(facecolor="#1a1f2b", edgecolor=GRID, labelcolor=FG, fontsize=9, loc="best")
    lg.get_frame().set_alpha(0.95)

fig.savefig("equity.png", dpi=140, facecolor=BG, bbox_inches="tight")
print("equity.png ditulis")
