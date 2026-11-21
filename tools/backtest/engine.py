#!/usr/bin/env python3
"""
Backtest engine mirroring N-Bar Reversal Strategy (FIXED) Pine Script logic,
for XAUUSD H1, fixed settings per strategy/pinescript/README.md.

Assumptions / approximations (no M1/tick data used yet):
- mintick = 0.01 (XAUUSD), slippage = 3 ticks = 0.03 applied on every fill
  (entries AND stop/limit exits), matching Pine's global slippage setting.
- commission = 0.02% of notional, charged on both entry and exit fill.
- Entry signal computed at bar close i; order fills at Open[i+1] (next bar).
- SL/TP (stop/limit) become active the same bar the entry fills, checked
  against that bar's High/Low.
- If BOTH SL and TP are inside the same bar's High/Low range, SL is assumed
  to hit first (conservative / worst case) -- this is the single biggest
  source of possible mismatch vs a tick-accurate engine (MT5 "every tick
  based on real ticks" mode). Needs M1 data to resolve precisely.
- strategy.equity used for risk-sizing is realized equity as of the last
  closed trade (ignoring open-position mark-to-market), a simplification.
"""
import pandas as pd
import numpy as np
import sys

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else "XAUUSD_H1.csv"

# ---- Fixed strategy settings (strategy/pinescript/README.md) ----
N_VALUE = 2
DC_LEN = 83
SL_PCT = 0.01
RISK_REWARD = 2.5
TP_PCT = SL_PCT * RISK_REWARD
RISK_PER_TRADE = 0.01
INITIAL_CAPITAL = 100_000.0
COMMISSION_PCT = 0.0002
MINTICK = 0.01
SLIPPAGE = 3 * MINTICK

BT_START = pd.Timestamp("2025-01-02 00:00:00")
BT_END = pd.Timestamp("2026-09-12 23:59:59")

# ---- Load data ----
df = pd.read_csv(CSV_PATH, sep="\t", header=0,
                  names=["Time", "Open", "High", "Low", "Close", "Volume", "Spread"])
df["Time"] = pd.to_datetime(df["Time"])
df = df.sort_values("Time").reset_index(drop=True)

high = df["High"].values
low = df["Low"].values
close = df["Close"].values
openp = df["Open"].values
n = len(df)

# ---- Donchian (previous-bar, i.e. shifted by 1) ----
dc_upper_prev = pd.Series(high).rolling(DC_LEN).max().shift(1).values
dc_lower_prev = pd.Series(low).rolling(DC_LEN).min().shift(1).values

enough_bars_idx = N_VALUE + 2  # bar_index >= n_value+2 (0-based)

long_signal = np.zeros(n, dtype=bool)
short_signal = np.zeros(n, dtype=bool)
for i in range(enough_bars_idx, n):
    if np.isnan(dc_upper_prev[i]) or np.isnan(dc_lower_prev[i]):
        continue
    hb = high[i] > high[i - 1]
    cc_up = close[i] > close[i - 1]
    lb = low[i] < low[i - 1]
    cc_down = close[i] < close[i - 1]
    dc_bull = close[i] > dc_upper_prev[i]
    dc_bear = close[i] < dc_lower_prev[i]
    long_signal[i] = hb and cc_up and dc_bull
    short_signal[i] = lb and cc_down and dc_bear

# ---- Simulation ----
side = 0          # 0 flat, +1 long, -1 short
qty = 0.0
sl_price = None
tp_price = None
entry_price = None
equity = INITIAL_CAPITAL          # realized equity
pending_order = None              # ('long'|'short', est_price, signal_equity)

trades = []        # dicts: side, entry_time, entry_price, exit_time, exit_price, qty, pnl, reason
equity_curve = []   # (time, equity_mark_to_market)

start_i = None
for i in range(n):
    if df["Time"].iloc[i] >= BT_START:
        start_i = i
        break

for i in range(start_i, n):
    t = df["Time"].iloc[i]
    if t > BT_END:
        break

    # 1) process pending order from previous bar -> fills at this bar's open
    if pending_order is not None:
        order_side, est_price, sig_equity = pending_order
        pending_order = None

        if order_side == "long":
            fill_price = openp[i] + SLIPPAGE
        else:
            fill_price = openp[i] - SLIPPAGE

        # reversal: close existing opposite position first, same bar/price
        if side != 0 and side != (1 if order_side == "long" else -1):
            exit_price = fill_price
            gross = (exit_price - entry_price) * qty * side
            comm_exit = exit_price * qty * COMMISSION_PCT
            pnl = gross - comm_exit
            equity += pnl
            trades.append(dict(side="Long" if side == 1 else "Short",
                                entry_time=entry_time, entry_price=entry_price,
                                exit_time=t, exit_price=exit_price, qty=qty,
                                pnl=pnl, reason="Reversal"))
            side = 0

        if side == 0:
            new_side = 1 if order_side == "long" else -1
            risk_cash = sig_equity * RISK_PER_TRADE
            risk_per_unit = est_price * SL_PCT
            new_qty = risk_cash / risk_per_unit if risk_per_unit > 0 else 0.0
            comm_entry = fill_price * new_qty * COMMISSION_PCT
            equity -= comm_entry
            side = new_side
            qty = new_qty
            entry_price = fill_price
            entry_time = t
            if side == 1:
                sl_price = est_price * (1 - SL_PCT)
                tp_price = est_price * (1 + TP_PCT)
            else:
                sl_price = est_price * (1 + SL_PCT)
                tp_price = est_price * (1 - TP_PCT)

    # 2) check SL/TP intrabar for current position (same bar as fill included)
    if side != 0:
        hit_tp = False
        hit_sl = False
        if side == 1:
            hit_tp = high[i] >= tp_price
            hit_sl = low[i] <= sl_price
        else:
            hit_tp = low[i] <= tp_price
            hit_sl = high[i] >= sl_price

        if hit_tp or hit_sl:
            # conservative: if both hit in same bar, assume SL first
            if hit_sl:
                raw_exit = sl_price
                reason = "SL"
            else:
                raw_exit = tp_price
                reason = "TP"
            exit_price = raw_exit - SLIPPAGE if side == 1 else raw_exit + SLIPPAGE
            gross = (exit_price - entry_price) * qty * side
            comm_exit = exit_price * qty * COMMISSION_PCT
            pnl = gross - comm_exit
            equity += pnl
            trades.append(dict(side="Long" if side == 1 else "Short",
                                entry_time=entry_time, entry_price=entry_price,
                                exit_time=t, exit_price=exit_price, qty=qty,
                                pnl=pnl, reason=reason))
            side = 0
            qty = 0.0

    # 3) evaluate signal at this bar's close -> queue order for next bar
    can_long = (side == 0) or (side == -1)
    can_short = (side == 0) or (side == 1)
    if long_signal[i] and can_long:
        pending_order = ("long", close[i], equity)
    elif short_signal[i] and can_short:
        pending_order = ("short", close[i], equity)

    # mark-to-market equity curve
    if side != 0:
        unreal = (close[i] - entry_price) * qty * side
        equity_curve.append((t, equity + unreal))
    else:
        equity_curve.append((t, equity))

# ---- close any open position at last bar close (TV does this at range end) ----
if side != 0:
    t = df["Time"].iloc[i]
    exit_price = close[i]
    gross = (exit_price - entry_price) * qty * side
    comm_exit = exit_price * qty * COMMISSION_PCT
    pnl = gross - comm_exit
    equity += pnl
    trades.append(dict(side="Long" if side == 1 else "Short",
                        entry_time=entry_time, entry_price=entry_price,
                        exit_time=t, exit_price=exit_price, qty=qty,
                        pnl=pnl, reason="EndOfRange"))

# ---- Stats ----
tr = pd.DataFrame(trades)
print(f"Bars simulated: {n - start_i}, range {df['Time'].iloc[start_i]} .. {df['Time'].iloc[i]}")
print(f"Total trades: {len(tr)}")
if len(tr) == 0:
    sys.exit(0)

winners = tr[tr.pnl > 0]
losers = tr[tr.pnl <= 0]
total_pnl = tr.pnl.sum()
gross_profit = winners.pnl.sum()
gross_loss = -losers.pnl.sum()
profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")
win_rate = len(winners) / len(tr) * 100

long_pnl = tr[tr.side == "Long"].pnl.sum()
short_pnl = tr[tr.side == "Short"].pnl.sum()

ec = pd.DataFrame(equity_curve, columns=["time", "equity"])
running_max = ec.equity.cummax()
dd = ec.equity - running_max
max_dd = -dd.min()
max_dd_pct = max_dd / running_max[dd.idxmin()] * 100 if len(dd) else 0

print(f"Total PnL: {total_pnl:,.2f} USD ({total_pnl/INITIAL_CAPITAL*100:.2f}%)")
print(f"Max Drawdown: {max_dd:,.2f} USD ({max_dd_pct:.2f}%)")
print(f"Win rate: {win_rate:.2f}% ({len(winners)}/{len(tr)})")
print(f"Profit Factor: {profit_factor:.3f}")
print(f"Gross profit: {gross_profit:,.2f} | Gross loss: {gross_loss:,.2f}")
print(f"Long PnL: {long_pnl:,.2f} | Short PnL: {short_pnl:,.2f}")
print(f"Avg win: {winners.pnl.mean():,.2f} | Avg loss: {losers.pnl.mean():,.2f}")
print(f"Expectancy: {tr.pnl.mean():,.2f}")

out_dir = sys.argv[2] if len(sys.argv) > 2 else "."
tr.to_csv(f"{out_dir}/trades.csv", index=False)
ec.to_csv(f"{out_dir}/equity_curve.csv", index=False)
