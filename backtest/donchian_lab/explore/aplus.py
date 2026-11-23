"""System A+ yearly + portfolios of filtered Donchian systems (pessimistic mode)."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import numpy as np, pandas as pd
from core import simulate; from features import build; from lab import F
from feat2 import extra
import grid_x
f = F(); grid_x.F = f; grid_x.X = extra(f); idx = f.d.index
def run(L, sl, ex, filt, sess='08-21', slip=0.05, pess=True, mb=0):
    kind = ex[0]
    a = list(build(f, 'brk_stop', L, sl, (kind, ex[1]) if kind != 'rr' else ('rr', ex[2]), 'none', sess, 'all'))
    mL, mS = grid_x.masks(filt); a[1] = np.where(mL, a[1], 0); a[4] = np.where(mS, a[4], 0)
    t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], ex[2], False, mb, slip, 0.07, pess)
    return pd.DataFrame(dict(ei=t[:, 0].astype(int), xi=t[:, 1].astype(int), side=t[:, 2], R=t[:, 3], tin=idx[t[:, 0].astype(int)], tout=idx[t[:, 1].astype(int)]))
def pf(r): return r[r > 0].sum() / -r[r < 0].sum()
def summary(t, name):
    yrs = (idx[-1] - idx[0]).days / 365.25; cum = t.sort_values('tout').R.cumsum(); dd = (cum.cummax() - cum).max()
    m = t.groupby(t.tout.dt.to_period('M')).R.sum()
    ys = t.groupby(t.tout.dt.year).R.sum()
    print(f"{name}: {len(t)/yrs/12:.1f} trade/bln | win {100*(t.R>0).mean():.1f}% | avg {t.R.mean():+.3f}R | PF {pf(t.R):.2f} | {t.R.sum()/yrs/12:+.2f}R/bln | DD {dd:.1f}R | tahun+ {(ys>0).sum()}/{len(ys)} | bulan+ {100*(m>0).mean():.0f}%")
    return ys
APLUS = (30, ('chan', 5), ('trail', 20, 0), 'ema+d1+e50')
t = run(*APLUS); ys = summary(t, 'A+ pesimis')
print('   per tahun R:', {k: round(v, 1) for k, v in ys.items()})
print('   per tahun PF:', {y: round(pf(g.R), 2) for y, g in t.groupby(t.tout.dt.year)})
print('   long %.1fR (PF %.2f) | short %.1fR (PF %.2f)' % (t[t.side > 0].R.sum(), pf(t[t.side > 0].R), t[t.side < 0].R.sum(), pf(t[t.side < 0].R)))
summary(run(*APLUS, slip=0.20), 'A+ pesimis + slip $0.20')
summary(run(*APLUS, pess=False), 'A+ normal')
# portfolios to raise frequency: same filter, different channel/exit combos (each its own single position)
cands = {
 'A+ DC30 s5 tr20': APLUS,
 'DC20 s5 tr20': (20, ('chan', 5), ('trail', 20, 0), 'ema+d1+e50'),
 'DC55 s10 tr20': (55, ('chan', 10), ('trail', 20, 0), 'ema+d1+e50'),
 'DC30 s10 mid': (30, ('chan', 10), ('mid', 0, 0), 'ema+d1+e50'),
 'DC40 s15 mid': (40, ('chan', 15), ('mid', 0, 0), 'ema+d1+e50'),
 'DC20 s15 mid': (20, ('chan', 15), ('mid', 0, 0), 'ema+d1+e50'),
}
T = {k: run(*v) for k, v in cands.items()}
for k, v in T.items(): summary(v, '  ' + k)
M = pd.DataFrame({k: v.groupby(v.tout.dt.to_period('M')).R.sum() for k, v in T.items()}).fillna(0)
print('\nkorelasi bulanan:\n', M.corr().round(2))
for combo in [['A+ DC30 s5 tr20', 'DC55 s10 tr20'], ['A+ DC30 s5 tr20', 'DC20 s15 mid'], ['A+ DC30 s5 tr20', 'DC20 s15 mid', 'DC55 s10 tr20'],
              ['A+ DC30 s5 tr20', 'DC20 s5 tr20', 'DC40 s15 mid', 'DC55 s10 tr20']]:
    P = pd.concat([T[k] for k in combo]); summary(P, 'PORTO ' + ' + '.join(combo))
    ev = pd.concat([pd.DataFrame(dict(t=P.ei, d=1)), pd.DataFrame(dict(t=P.xi, d=-1))]).sort_values(['t', 'd']); print('      posisi bersamaan maks', ev.d.cumsum().max())
t.to_csv('explore/aplus_trades.csv', index=False)
