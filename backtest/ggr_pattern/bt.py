"""Backtest: GGR -> BUY, RRG -> SELL on XAUUSD H1.
Biggest candle (High-Low) of the 3 (ties -> latest). Entry = its close.
SL = its open when the open is on the losing side, otherwise its low (buy) / high (sell). TP = 3R.
Pending order type from where price is at the 3rd candle's close: below entry -> buy stop, above -> buy limit
(sell: above -> sell stop, below -> sell limit). A newer pattern replaces an untriggered order.
New patterns are ignored while a position is open; a filled order is consumed.
Intrabar: 'normal' = 4-tick path (O -> nearer extreme -> other -> C), 'pess' = after a fill, adverse extreme first.
Costs: real spread + commission $0.07/oz + slippage $0.05 on stop fills."""
import sys, numpy as np, pandas as pd
sys.path.insert(0, '../donchian_lab'); from core import load
d = load(); O, H, L, C, SP = [d[c].values for c in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'SP']]; idx = d.index

def cross(p0, p1, lvl, kind):
    """price moves p0->p1. kind: 'up' (triggered when price >= lvl) or 'dn'. returns fill or None"""
    if kind == 'up':
        if p0 >= lvl: return p0
        if p1 >= lvl: return lvl
    else:
        if p0 <= lvl: return p0
        if p1 <= lvl: return lvl
    return None

def run(mode='normal', rr=3.0, slip=0.05, comm=0.07, min_risk=0.0):
    out = []; order = None; pos = None
    for i in range(3, len(d)):
        if (H[i] - O[i]) <= (O[i] - L[i]): path = [O[i], H[i], L[i], C[i]]
        else:                              path = [O[i], L[i], H[i], C[i]]
        seg = 0; p0 = path[0]
        while seg < 3:
            p1 = path[seg + 1]
            if pos is None and order is not None:
                s, ent, sl, tp, typ = order
                kind = ('up' if s > 0 else 'dn') if typ == 'stop' else ('dn' if s > 0 else 'up')
                f = cross(p0, p1, ent, kind)
                if f is None: p0 = p1; seg += 1; continue
                ep = f + (slip * s if typ == 'stop' else 0)
                pos = dict(s=s, ep=ep, sl=sl, tp=tp, risk=abs(ent - sl), ei=i, typ=typ, cost=SP[i] + comm + (slip if typ == 'stop' else 0)); order = None
                p0 = f
                if mode == 'pess':   # rest of this bar: adverse extreme first
                    adverse = L[i] if s > 0 else H[i]
                    if (s > 0 and adverse <= sl) or (s < 0 and adverse >= sl):
                        out.append((i, i, s, ((sl - slip * s - ep) * s - pos['cost']) / pos['risk'], 'SL', typ)); pos = None
                    break            # no same-bar TP in pessimistic mode
                continue
            if pos is not None:
                s = pos['s']
                fs = cross(p0, p1, pos['sl'], 'dn' if s > 0 else 'up'); ft = cross(p0, p1, pos['tp'], 'up' if s > 0 else 'dn')
                cand = [(abs(f - p0), f, w) for f, w in ((fs, 'SL'), (ft, 'TP')) if f is not None]
                if cand:
                    _, f, w = min(cand)
                    px = f - (slip * s if w == 'SL' else 0)
                    out.append((pos['ei'], i, s, ((px - pos['ep']) * s - pos['cost']) / pos['risk'], w, pos['typ'])); pos = None
                    break            # SOP: nothing else on the exit bar
            p0 = p1; seg += 1
        if mode == 'pess' and pos is not None and pos['ei'] < i:
            pass
        # pattern at the close of bar i
        if pos is None:
            g = [C[i - k] > O[i - k] for k in (2, 1, 0)]; r = [C[i - k] < O[i - k] for k in (2, 1, 0)]
            s = 1 if (g[0] and g[1] and r[2]) else (-1 if (r[0] and r[1] and g[2]) else 0)
            if s:
                k = i - 2
                for j in (i - 1, i):
                    if H[j] - L[j] >= H[k] - L[k]: k = j
                ent = C[k]
                sl = (O[k] if O[k] < C[k] else L[k]) if s > 0 else (O[k] if O[k] > C[k] else H[k])
                risk = abs(ent - sl)
                if risk > max(0.01, min_risk):
                    typ = ('stop' if C[i] < ent else 'limit') if s > 0 else ('stop' if C[i] > ent else 'limit')
                    order = (s, ent, sl, ent + s * rr * risk, typ)
    return pd.DataFrame(out, columns=['ei', 'xi', 'side', 'R', 'why', 'typ'])

def stats(t, name, show=True):
    t = t.copy(); t['tout'] = idx[t.xi]; yrs = (idx[-1] - idx[0]).days / 365.25
    m = t.set_index('tout').R.resample('MS').sum(); cum = t.R.cumsum(); dd = (cum.cummax() - cum).max()
    a, b = t[t.tout < '2023'], t[t.tout >= '2023']
    res = dict(n_mo=len(t) / yrs / 12, win=100 * (t.R > 0).mean(), avgR=t.R.mean(), pf=t.R[t.R > 0].sum() / -t.R[t.R < 0].sum(),
               R_mo=m.mean(), dd=dd, is_avgR=a.R.mean(), oos_avgR=b.R.mean())
    if show:
        print(f"{name}: {len(t)} trade ({res['n_mo']:.1f}/bln) win {res['win']:.1f}% avgR {res['avgR']:+.3f} PF {res['pf']:.2f} R/bln {res['R_mo']:+.2f} DD {dd:.0f}R | 2015-22 {res['is_avgR']:+.3f} | 2023-26 {res['oos_avgR']:+.3f}")
        print('   per order:', t.groupby('typ').R.agg(['count', 'mean']).round(3).to_dict('index'), '| exit:', t.why.value_counts().to_dict())
    return res
if __name__ == '__main__':
    # risk size vs cost
    t = run('normal'); risk = []
    print('median spread $%.2f' % np.median(SP))
    stats(t, 'NORMAL'); stats(run('pess'), 'PESIMIS')
    for mr in [1, 2, 3, 5]:
        stats(run('normal', min_risk=mr), f'normal, skip SL < ${mr}'); stats(run('pess', min_risk=mr), f'pess,   skip SL < ${mr}')
