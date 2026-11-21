"""Donchian R&D lab - core engine.
Every order is decided with information available BEFORE it can fill (no look-ahead).
Intrabar path = 4-tick model (TradingView default): O -> nearer extreme -> other extreme -> C.
Costs: real spread from the data (per round trip) + slippage on stop/market fills + commission."""
import numpy as np, pandas as pd
from numba import njit

DATA = "/root/.claude/uploads/9e77afca-e137-59cc-854a-90daae465dd9/7b295ea6-XAUUSD_H1_201501020900_202611091700.csv"

def load(path=DATA):
    d = pd.read_csv(path, sep='\t'); d.columns = [c.strip('<>') for c in d.columns]
    d['dt'] = pd.to_datetime(d.DATE + ' ' + d.TIME, format='%Y.%m.%d %H:%M:%S')
    d = d.set_index('dt')[['OPEN', 'HIGH', 'LOW', 'CLOSE', 'SPREAD']]
    d['SP'] = d.SPREAD * 0.01          # spread in USD
    return d

@njit(cache=True)
def _fill_check(p0, p1, lvl, typ, side):
    """Does an order at lvl trigger while price moves p0->p1? returns fill price or nan.
    typ 1=stop, 2=limit. side +1 buy, -1 sell."""
    if np.isnan(lvl):
        return np.nan
    if typ == 1:  # stop
        if side > 0:
            if p0 >= lvl: return p0          # already through (gap)
            if p1 >= lvl: return lvl
        else:
            if p0 <= lvl: return p0
            if p1 <= lvl: return lvl
    elif typ == 2:  # limit
        if side > 0:
            if p0 <= lvl: return p0
            if p1 <= lvl: return lvl
        else:
            if p0 >= lvl: return p0
            if p1 >= lvl: return lvl
    return np.nan

@njit(cache=True)
def simulate(O, H, L, C, SP, lvlL, typL, dL, lvlS, typS, dS, trailL, trailS,
             rr, reverse, maxbars, slip, comm, pess=False):
    """Generic single-position engine.
    lvlL/typL : long entry order for bar i (typ 0 none, 1 stop, 2 limit, 3 market at open)
    dL        : stop-loss distance (USD) applied to the real fill price of a long filled on bar i
    trailL    : trailing stop level for a long held during bar i (nan = none), only ratchets in favour
    rr        : take profit in R (0 = none)
    Returns trades: entry_i, exit_i, side, R, reason(1 SL,2 TP,3 trail,4 reverse,5 time)"""
    n = len(O)
    out = np.zeros((n, 8))
    k = 0
    pos = 0; ep = 0.0; sl = 0.0; trl = False; lastx = -1; tp = 0.0; risk = 1.0; ei = 0; cost = 0.0
    for i in range(1, n):
        # market orders at open
        if pos == 0 or reverse:
            if typL[i] == 3 and pos <= 0:
                if pos < 0:
                    px = O[i] + slip
                    out[k, 0] = ei; out[k, 1] = i; out[k, 2] = -1; out[k, 3] = ((ep - px) - cost) / risk; out[k, 4] = 4; out[k, 5] = ep; out[k, 6] = px; k += 1
                pos = 1; ep = O[i] + slip; risk = dL[i]; sl = ep - risk; trl = False; tp = ep + rr * risk if rr > 0 else np.nan
                ei = i; cost = SP[i] + comm + slip
            elif typS[i] == 3 and pos >= 0:
                if pos > 0:
                    px = O[i] - slip
                    out[k, 0] = ei; out[k, 1] = i; out[k, 2] = 1; out[k, 3] = ((px - ep) - cost) / risk; out[k, 4] = 4; out[k, 5] = ep; out[k, 6] = px; k += 1
                pos = -1; ep = O[i] - slip; risk = dS[i]; sl = ep + risk; trl = False; tp = ep - rr * risk if rr > 0 else np.nan
                ei = i; cost = SP[i] + comm + slip
        # time stop at open
        if pos != 0 and maxbars > 0 and i - ei >= maxbars:
            px = O[i] - slip * pos
            out[k, 0] = ei; out[k, 1] = i; out[k, 2] = pos; out[k, 3] = ((px - ep) * pos - cost) / risk; out[k, 4] = 5; out[k, 5] = ep; out[k, 6] = px; k += 1
            pos = 0; lastx = i
        # ratchet trailing stop
        if pos > 0 and not np.isnan(trailL[i]) and trailL[i] > sl:
            sl = trailL[i]; trl = True
        if pos < 0 and not np.isnan(trailS[i]) and trailS[i] < sl:
            sl = trailS[i]; trl = True
        # pessimistic stress mode: an open position always meets its adverse extreme first
        if pess and pos != 0:
            if pos > 0:
                path = (O[i], L[i], H[i], C[i])
            else:
                path = (O[i], H[i], L[i], C[i])
        elif (H[i] - O[i]) <= (O[i] - L[i]):
            path = (O[i], H[i], L[i], C[i])
        else:
            path = (O[i], L[i], H[i], C[i])
        for sgm in range(3):
            p0 = path[sgm]; p1 = path[sgm + 1]
            guard = 0
            while guard < 6:
                guard += 1
                best = np.nan; act = 0; dist = 1e18
                if pos == 0:
                    if lastx == i:
                        break          # SOP: no new entry on the bar where a trade was closed
                    if typL[i] == 1 or typL[i] == 2:
                        f = _fill_check(p0, p1, lvlL[i], typL[i], 1)
                        if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 1
                    if typS[i] == 1 or typS[i] == 2:
                        f = _fill_check(p0, p1, lvlS[i], typS[i], -1)
                        if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 2
                else:
                    f = _fill_check(p0, p1, sl, 1, -pos)                   # stop loss / trail
                    if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 3
                    if rr > 0:
                        f = _fill_check(p0, p1, tp, 2, -pos)               # take profit
                        if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 4
                    if reverse:
                        if pos > 0 and (typS[i] == 1 or typS[i] == 2):
                            f = _fill_check(p0, p1, lvlS[i], typS[i], -1)
                            if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 5
                        if pos < 0 and (typL[i] == 1 or typL[i] == 2):
                            f = _fill_check(p0, p1, lvlL[i], typL[i], 1)
                            if not np.isnan(f) and abs(f - p0) < dist: dist = abs(f - p0); best = f; act = 6
                if act == 0:
                    break
                if act == 1 or act == 6 or act == 2 or act == 5:
                    if act == 5 or act == 6:   # close current then reverse
                        px = best - slip * pos
                        out[k, 0] = ei; out[k, 1] = i; out[k, 2] = pos; out[k, 3] = ((px - ep) * pos - cost) / risk; out[k, 4] = 4; out[k, 5] = ep; out[k, 6] = px; k += 1
                    s = 1 if (act == 1 or act == 6) else -1
                    ty = typL[i] if s > 0 else typS[i]
                    sp_ = slip if ty == 1 else 0.0
                    ep = best + sp_ * s
                    risk = dL[i] if s > 0 else dS[i]
                    sl = ep - s * risk; trl = False
                    tp = ep + s * rr * risk if rr > 0 else np.nan
                    pos = s; ei = i; cost = SP[i] + comm + sp_
                    p0 = best
                    if pess and ((s > 0 and L[i] <= sl) or (s < 0 and H[i] >= sl)):
                        px = sl - slip * s
                        out[k, 0] = ei; out[k, 1] = i; out[k, 2] = s; out[k, 3] = ((px - ep) * s - cost) / risk; out[k, 4] = 1; out[k, 5] = ep; out[k, 6] = px; k += 1
                        pos = 0; lastx = i
                        break
                    # an order that fills cannot fill again this segment from the same level
                else:
                    reason = 1.0
                    if act == 4: reason = 2.0
                    elif trl: reason = 3.0
                    px = best - (slip * pos if act == 3 else 0.0)
                    out[k, 0] = ei; out[k, 1] = i; out[k, 2] = pos; out[k, 3] = ((px - ep) * pos - cost) / risk; out[k, 4] = reason; out[k, 5] = ep; out[k, 6] = px; k += 1
                    pos = 0; p0 = best; lastx = i
                    break   # flat: no new entry in the remaining part of this bar segment (avoid churn)
    return out[:k]
