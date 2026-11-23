"""Grid around System A: channel, SL, exit, time stop, session, trend-confirmation filters.
No hedging (one position per system), no martingale (fixed risk). Pessimistic intrabar mode is the ranking basis."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import itertools, time, numpy as np, pandas as pd, multiprocessing as mp
from core import simulate, load; from features import Feat, build; from feat2 import extra
F = X = None
def init():
    global F, X; F = Feat(load()); X = extra(F)
FILTERS = ['ema', 'ema+d1', 'ema+e50', 'ema+slope', 'ema+d1+e50', 'd1', 'ema|long', 'ema+d1|long', 'long:ema / short:ema+d1+e50']
def masks(name):
    n = len(F.O); d1L = X['d1'] == 1; d1S = X['d1'] == 0
    e50L = X['ema50_200'] > 0; e50S = X['ema50_200'] < 0; slL = X['ema_slope'] > 0; slS = X['ema_slope'] < 0
    eL, eS = F.ema_bull, F.ema_bear; one = np.ones(n, bool); zero = np.zeros(n, bool)
    m = {'ema': (eL, eS), 'ema+d1': (eL & d1L, eS & d1S), 'ema+e50': (eL & e50L, eS & e50S), 'ema+slope': (eL & slL, eS & slS),
         'ema+d1+e50': (eL & d1L & e50L, eS & d1S & e50S), 'd1': (d1L, d1S), 'ema|long': (eL, zero), 'ema+d1|long': (eL & d1L, zero),
         'long:ema / short:ema+d1+e50': (eL, eS & d1S & e50S)}[name]
    return m
LENS = [20, 30, 40, 55]; SLS = [('chan', 5), ('chan', 10), ('chan', 15), ('atr', 1.5), ('atr', 2.0)]
EXITS = [('mid', 0, 0), ('trail', 10, 0), ('trail', 20, 0), ('rr', 0, 2.0), ('rr', 0, 3.0), ('mid', 0, 3.0), ('mid', 0, 5.0)]
MAXB = [0, 48, 120]; SESS = ['08-21', 'all']
SPLIT = pd.Timestamp('2023-01-01')
def met(t, idx):
    if len(t) < 40: return None
    R = t[:, 3]; te = idx[t[:, 0].astype(int)]; isn = te < SPLIT
    def pf(r): return r[r > 0].sum() / max(-r[r < 0].sum(), 1e-9)
    yrs = (idx[-1] - idx[0]).days / 365.25
    ys = pd.Series(R, index=te).groupby(te.year).sum()
    cum = np.cumsum(R); dd = (np.maximum.accumulate(cum) - cum).max()
    return dict(n_mo=len(R) / yrs / 12, avgR=R.mean(), pf=pf(R), dd=dd, R_mo=R.sum() / yrs / 12, is_pf=pf(R[isn]), oos_pf=pf(R[~isn]),
                is_avg=R[isn].mean(), oos_avg=R[~isn].mean(), yrs_pos=int((ys > 0).sum()), win=(R > 0).mean() * 100)
def job(L):
    out = []; idx = F.d.index
    for fl, sl, ex, mb, ss in itertools.product(FILTERS, SLS, EXITS, MAXB, SESS):
        kind = 'mid' if ex[0] == 'mid' else ex[0]
        a = list(build(F, 'brk_stop', L, sl, (kind, ex[1]) if kind != 'rr' else ('rr', ex[2]), 'none', ss, 'all'))
        mL, mS = masks(fl); a[1] = np.where(mL, a[1], 0); a[4] = np.where(mS, a[4], 0)
        rr = ex[2] if ex[2] else 0.0
        row = dict(L=L, sl=f'{sl[0]}{sl[1]:g}', exit=f'{ex[0]}{ex[1] or ""}' + (f'+tp{ex[2]:g}' if ex[2] and ex[0] != 'rr' else (f'{ex[2]:g}R' if ex[0] == 'rr' else '')),
                   maxbars=mb, sess=ss, filt=fl)
        ok = True
        for pess, slip, tag in [(True, 0.05, 'P'), (True, 0.20, 'S'), (False, 0.05, 'N')]:
            t = simulate(F.O, F.H, F.L, F.C, F.SP, *a[:8], rr, False, mb, slip, 0.07, pess)
            m = met(t, idx)
            if m is None: ok = False; break
            row.update({f'{k}_{tag}': v for k, v in m.items()})
        if ok: out.append(row)
    return out
if __name__ == '__main__':
    t0 = time.time()
    with mp.Pool(4, initializer=init) as p: res = p.map(job, LENS)
    g = pd.DataFrame([r for x in res for r in x]); g.to_csv('explore/grid_x.csv.gz', index=False); print(len(g), 'configs', round(time.time() - t0), 's')
