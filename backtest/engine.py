"""Backtest engine for the Momentum Candle strategy.

Replicates momentum_candle.pine bar by bar, including TradingView's
intrabar path assumption: an up bar is walked open -> low -> high -> close,
a down bar open -> high -> low -> close. That assumption is what the Pine
broker emulator uses to fill limit orders and to decide which of stop loss
and take profit is reached first when both sit inside the same bar, so
reproducing it here is what makes these results comparable to the
TradingView Strategy Tester.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field, replace


# --------------------------------------------------------------------------
# Configuration - mirrors the input() block of the Pine script
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Config:
    # Tahap 1 - filter sinyal
    lookback: int = 20
    size_mult: float = 1.5
    body_min: float = 0.75
    wick_max: float = 0.10
    use_vol: bool = True
    vol_mult: float = 1.5
    use_ema: bool = True
    ema_len: int = 50
    direction: str = "both"                  # both | long | short

    # Tahap 2 - definisi ATR
    atr_mode: str = "highlow"                # highlow | truerange

    # Tahap 5 - level harga
    fib_entry: float = 0.236
    sl_mode: str = "sop"                     # sop | tight
    sl_atr: float = 0.5
    tp_mode: str = "rr"                      # rr | fib | farthest
    rr_target: float = 2.0
    fib_tp: float = 0.27

    # Tahap 6 - pembatalan
    exp_bars: int = 5
    cancel_tp: bool = True
    cancel_sl: bool = True

    # Mode eksplorasi (bukan bagian dari SOP)
    reverse: bool = False                    # balik arah sinyal (fade momentum)
    random_p: float = 0.0                    # kontrol: entry acak, geometri level sama
    seed: int = 7
    entry_mode: str = "limit"                # limit | market (isi di open bar berikutnya)

    # Tahap 7 - money management
    risk_pct: float = 1.0
    min_rr: float = 2.0

    # Biaya transaksi
    initial_capital: float = 10_000.0
    commission_pct: float = 0.04             # per sisi, persen dari notional
    slippage: float = 0.01                   # harga absolut, per sisi


# --------------------------------------------------------------------------
# Indikator
# --------------------------------------------------------------------------

def sma(values: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    running = 0.0
    for i, v in enumerate(values):
        running += v
        if i >= length:
            running -= values[i - length]
        if i >= length - 1:
            out[i] = running / length
    return out


def ema(values: list[float], length: int) -> list[float | None]:
    out: list[float | None] = [None] * len(values)
    alpha = 2.0 / (length + 1.0)
    seed = None
    for i, v in enumerate(values):
        if i == length - 1:
            seed = sum(values[:length]) / length
            out[i] = seed
        elif seed is not None:
            seed = alpha * v + (1 - alpha) * seed
            out[i] = seed
    return out


def rma(values: list[float], length: int) -> list[float | None]:
    """Wilder smoothing, the average ta.atr() uses."""
    out: list[float | None] = [None] * len(values)
    seed = None
    for i, v in enumerate(values):
        if i == length - 1:
            seed = sum(values[:length]) / length
            out[i] = seed
        elif seed is not None:
            seed = (seed * (length - 1) + v) / length
            out[i] = seed
    return out


# --------------------------------------------------------------------------
# Jalur intrabar
# --------------------------------------------------------------------------

def bar_path(o: float, h: float, l: float, c: float) -> list[float]:
    return [o, l, h, c] if c >= o else [o, h, l, c]


def first_touch(levels: dict[float, str], a: float, b: float) -> tuple[float, str] | None:
    """Level pertama yang tersentuh saat harga bergerak dari a ke b."""
    if b >= a:
        hit = [(lv, tag) for lv, tag in levels.items() if a <= lv <= b]
        return min(hit, key=lambda x: x[0]) if hit else None
    hit = [(lv, tag) for lv, tag in levels.items() if b <= lv <= a]
    return max(hit, key=lambda x: x[0]) if hit else None


# --------------------------------------------------------------------------
# Hasil
# --------------------------------------------------------------------------

@dataclass
class Trade:
    direction: int
    signal_time: str
    entry_time: str
    exit_time: str
    entry: float
    stop: float
    target: float
    exit_price: float
    qty: float
    rr_planned: float
    outcome: str                 # tp | sl
    pnl: float
    equity_after: float
    bars_held: int


@dataclass
class Result:
    trades: list[Trade] = field(default_factory=list)
    equity_curve: list[tuple[str, float]] = field(default_factory=list)
    signals: int = 0
    armed: int = 0
    skipped_rr: int = 0
    cancel_timeout: int = 0
    cancel_tp: int = 0
    cancel_sl: int = 0


# --------------------------------------------------------------------------
# Engine
# --------------------------------------------------------------------------

def run(bars: list[dict], cfg: Config) -> Result:
    import random as _random
    _rng = _random.Random(cfg.seed)
    n = len(bars)
    o = [b["open"] for b in bars]
    h = [b["high"] for b in bars]
    l = [b["low"] for b in bars]
    c = [b["close"] for b in bars]
    v = [b["volume"] for b in bars]
    t = [b["time"] for b in bars]

    if cfg.atr_mode == "truerange":
        tr = [h[0] - l[0]] + [
            max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])) for i in range(1, n)
        ]
        atr = rma(tr, cfg.lookback)
    else:
        atr = sma([h[i] - l[i] for i in range(n)], cfg.lookback)

    avg_vol = sma(v, cfg.lookback)
    ema_val = ema(c, cfg.ema_len)

    res = Result()
    equity = cfg.initial_capital
    res.equity_curve.append((t[0], equity))

    # state machine
    trade_active = False
    pending = False
    direction = 0
    lvl_entry = lvl_stop = lvl_target = rr_planned = 0.0
    qty = 0.0
    sig_bar = -1
    sig_time = ""
    entry_bar = -1
    entry_time = ""
    entry_fill = 0.0

    warmup = max(cfg.lookback, cfg.ema_len)

    for i in range(n):
        # -- 1. broker emulator: jalankan jalur intrabar -------------------
        if (pending and i > sig_bar) or trade_active and entry_bar >= 0 and entry_bar <= i:
            pts = bar_path(o[i], h[i], l[i], c[i])
            in_position = entry_bar >= 0 and entry_bar <= i and not pending
            seg = 0
            while seg < len(pts) - 1:
                a, b = pts[seg], pts[seg + 1]
                while True:
                    if not in_position and pending and i > sig_bar and cfg.entry_mode == "market":
                        ev = (o[i], "fill")
                    elif not in_position and pending and i > sig_bar:
                        ev = first_touch({lvl_entry: "fill"}, a, b)
                    elif in_position:
                        ev = first_touch({lvl_stop: "sl", lvl_target: "tp"}, a, b)
                    else:
                        ev = None
                    if ev is None:
                        break
                    price, tag = ev
                    if tag == "fill":
                        slip = cfg.slippage * direction
                        entry_fill = price + slip
                        entry_bar = i
                        entry_time = t[i]
                        pending = False
                        in_position = True
                        a = price
                        continue
                    # exit
                    slip = -cfg.slippage * direction
                    exit_price = price + slip
                    gross = (exit_price - entry_fill) * direction * qty
                    fees = (abs(entry_fill) + abs(exit_price)) * qty * cfg.commission_pct / 100.0
                    pnl = gross - fees
                    equity += pnl
                    res.trades.append(Trade(
                        direction=direction, signal_time=sig_time, entry_time=entry_time,
                        exit_time=t[i], entry=entry_fill, stop=lvl_stop, target=lvl_target,
                        exit_price=exit_price, qty=qty, rr_planned=rr_planned, outcome=tag,
                        pnl=pnl, equity_after=equity, bars_held=i - entry_bar))
                    res.equity_curve.append((t[i], equity))
                    trade_active = pending = False
                    direction = 0
                    entry_bar = -1
                    in_position = False
                    break
                if not trade_active:
                    break
                seg += 1

        # -- 2. Tahap 6: pembatalan, dievaluasi saat bar close -------------
        if pending and i > sig_bar:
            bars_elapsed = i - sig_bar
            touched_entry = l[i] <= lvl_entry if direction == 1 else h[i] >= lvl_entry
            touched_tp = h[i] >= lvl_target if direction == 1 else l[i] <= lvl_target
            touched_sl = l[i] <= lvl_stop if direction == 1 else h[i] >= lvl_stop
            r_timeout = bars_elapsed >= cfg.exp_bars
            market = cfg.entry_mode == "market"
            r_tp = (not market) and cfg.cancel_tp and touched_tp and not touched_entry
            r_sl = (not market) and cfg.cancel_sl and touched_sl
            if r_timeout or r_tp or r_sl:
                if r_sl:
                    res.cancel_sl += 1
                elif r_tp:
                    res.cancel_tp += 1
                else:
                    res.cancel_timeout += 1
                trade_active = pending = False
                direction = 0

        # -- 3. Tahap 3: validasi sinyal ------------------------------------
        if i < warmup or atr[i] is None or avg_vol[i] is None or ema_val[i] is None:
            continue
        total_range = h[i] - l[i]
        if total_range <= 0 or atr[i] <= 0:
            continue

        body = abs(c[i] - o[i])
        upper = h[i] - max(c[i], o[i])
        lower = min(c[i], o[i]) - l[i]

        base = (total_range > atr[i] * cfg.size_mult
                and body >= total_range * cfg.body_min
                and (not cfg.use_vol or v[i] > avg_vol[i] * cfg.vol_mult))

        bull = (base and cfg.direction in ("both", "long") and c[i] > o[i]
                and (not cfg.use_ema or c[i] > ema_val[i])
                and lower <= total_range * cfg.wick_max)
        bear = (base and cfg.direction in ("both", "short") and c[i] < o[i]
                and (not cfg.use_ema or c[i] < ema_val[i])
                and upper <= total_range * cfg.wick_max)

        if cfg.random_p > 0.0:
            bull = bear = False
            if _rng.random() < cfg.random_p:
                bull, bear = (True, False) if _rng.random() < 0.5 else (False, True)

        if not (bull or bear):
            continue
        res.signals += 1
        if trade_active:
            continue

        # -- 4. Tahap 4 + 5: pemetaan harga --------------------------------
        d = 1 if bull else -1
        if cfg.reverse:
            d = -d
        sig_high, sig_low = h[i], l[i]
        rng = sig_high - sig_low
        if cfg.entry_mode == "market":
            entry = c[i]
        else:
            entry = sig_high - cfg.fib_entry * rng if d == 1 else sig_low + cfg.fib_entry * rng
        anchor = entry if cfg.sl_mode == "tight" else (sig_low if d == 1 else sig_high)
        stop = anchor - cfg.sl_atr * atr[i] if d == 1 else anchor + cfg.sl_atr * atr[i]
        risk_unit = abs(entry - stop)
        tp_fib = sig_high + cfg.fib_tp * rng if d == 1 else sig_low - cfg.fib_tp * rng
        tp_rr = entry + cfg.rr_target * risk_unit * d
        if cfg.tp_mode == "rr":
            target = tp_rr
        elif cfg.tp_mode == "fib":
            target = tp_fib
        else:
            target = max(tp_fib, tp_rr) if d == 1 else min(tp_fib, tp_rr)

        if risk_unit <= 0 or rng <= 0:
            continue
        rr = abs(target - entry) / risk_unit
        geometry_ok = (target > entry and stop < entry) if d == 1 else (target < entry and stop > entry)
        if not geometry_ok:
            continue
        if rr < cfg.min_rr:
            res.skipped_rr += 1
            continue

        size = (equity * cfg.risk_pct / 100.0) / risk_unit
        if size <= 0:
            continue

        trade_active = True
        pending = True
        direction = d
        lvl_entry, lvl_stop, lvl_target, rr_planned = entry, stop, target, rr
        qty = size
        sig_bar = i
        sig_time = t[i]
        entry_bar = -1
        res.armed += 1

    return res


# --------------------------------------------------------------------------
# Metrik
# --------------------------------------------------------------------------

def metrics(res: Result, cfg: Config) -> dict:
    tr = res.trades
    if not tr:
        return {"trades": 0}

    wins = [x for x in tr if x.pnl > 0]
    losses = [x for x in tr if x.pnl <= 0]
    gross_win = sum(x.pnl for x in wins)
    gross_loss = -sum(x.pnl for x in losses)
    net = sum(x.pnl for x in tr)

    peak = cfg.initial_capital
    max_dd = 0.0
    for _, eq in res.equity_curve:
        peak = max(peak, eq)
        max_dd = max(max_dd, (peak - eq) / peak)

    # rangkaian kalah beruntun
    streak = worst_streak = 0
    for x in tr:
        streak = streak + 1 if x.pnl <= 0 else 0
        worst_streak = max(worst_streak, streak)

    risk_amounts = [x.qty * abs(x.entry - x.stop) for x in tr]
    r_multiples = [x.pnl / r if r > 0 else 0.0 for x, r in zip(tr, risk_amounts)]

    return {
        "trades": len(tr),
        "signals": res.signals,
        "armed": res.armed,
        "skipped_rr": res.skipped_rr,
        "cancel_timeout": res.cancel_timeout,
        "cancel_tp": res.cancel_tp,
        "cancel_sl": res.cancel_sl,
        "fill_rate": len(tr) / res.armed if res.armed else 0.0,
        "wins": len(wins),
        "losses": len(losses),
        "win_rate": len(wins) / len(tr),
        "profit_factor": gross_win / gross_loss if gross_loss > 0 else math.inf,
        "net": net,
        "return_pct": net / cfg.initial_capital * 100.0,
        "final_equity": cfg.initial_capital + net,
        "max_dd_pct": max_dd * 100.0,
        "avg_r": sum(r_multiples) / len(r_multiples),
        "expectancy": net / len(tr),
        "avg_bars": sum(x.bars_held for x in tr) / len(tr),
        "worst_streak": worst_streak,
        "long": sum(1 for x in tr if x.direction == 1),
        "short": sum(1 for x in tr if x.direction == -1),
    }


# --------------------------------------------------------------------------
# Data loader
# --------------------------------------------------------------------------

def load(path: str) -> list[dict]:
    """Kolom: Time, Open, High, Low, Close, <durasi bar>, Volume (tab-separated)."""
    bars = []
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh, delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) < 7:
                continue
            bars.append({
                "time": row[0],
                "open": float(row[1]),
                "high": float(row[2]),
                "low": float(row[3]),
                "close": float(row[4]),
                "volume": float(row[6]),
            })
    return bars
