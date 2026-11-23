"""Year-by-year test of Donchian System A (both intrabar assumptions, plus slippage stress)."""
import numpy as np, pandas as pd
from core import simulate
from features import build
from lab import F
f = F(); idx = f.d.index
A = dict(entry='brk_stop', L=30, sl=('chan', 10), exit_=('mid', 0), trend='ema', sess='08-21', vol='all', f=0.5)
def trades(pess, slip=0.05):
    a = build(f, A['entry'], A['L'], A['sl'], A['exit_'], A['trend'], A['sess'], A['vol'], A['f'])
    t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], a[8], False, 0, slip, 0.07, pess)
    return pd.DataFrame(dict(tin=idx[t[:, 0].astype(int)], tout=idx[t[:, 1].astype(int)], side=t[:, 2].astype(int), R=t[:, 3], why=t[:, 4].astype(int)))
def yearly(t):
    rows = []
    for y, g in t.groupby(t.tout.dt.year):
        cum = g.R.cumsum(); dd = (np.maximum.accumulate(np.r_[0, cum]) - np.r_[0, cum]).max()
        streak = max(len(x) for x in ''.join('L' if r < 0 else 'W' for r in g.R).split('W'))
        mon = g.groupby(g.tout.dt.month).R.sum()
        rows.append(dict(tahun=y, trade=len(g), per_bln=round(len(g) / g.tout.dt.month.nunique(), 1), win=round(100 * (g.R > 0).mean(), 1),
                         avgR=round(g.R.mean(), 3), PF=round(g.R[g.R > 0].sum() / -g.R[g.R < 0].sum(), 2), totalR=round(g.R.sum(), 1),
                         ddR=round(dd, 1), kalah_beruntun=streak, bln_plus=f"{(mon > 0).sum()}/{len(mon)}",
                         long_R=round(g.R[g.side > 0].sum(), 1), short_R=round(g.R[g.side < 0].sum(), 1)))
    return pd.DataFrame(rows)
pd.set_option('display.width', 250)
out = {}
for name, pess, slip in [('NORMAL', False, 0.05), ('PESIMIS', True, 0.05), ('PESIMIS + slip $0.20', True, 0.20)]:
    t = trades(pess, slip); y = yearly(t); out[name] = y
    tot = t.R; cum = tot.cumsum(); dd = (cum.cummax() - cum).max()
    print(f"\n=== {name}: {len(t)} trade | win {100*(tot>0).mean():.1f}% | avg {tot.mean():+.3f}R | PF {tot[tot>0].sum()/-tot[tot<0].sum():.2f} | total {tot.sum():+.1f}R | DD {dd:.1f}R")
    print(y.to_string(index=False))
    y.to_csv(f"yearly_A_{name.split()[0].lower()}{'_slip' if slip > 0.1 else ''}.csv", index=False)
