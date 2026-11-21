import json, numpy as np, pandas as pd
from core import simulate
from features import build
from lab import F
from analyze import SYS
f = F(); idx = f.d.index
g1 = pd.read_csv('grid.csv.gz'); g2 = pd.read_csv('grid2.csv.gz'); g3 = pd.read_csv('grid3.csv.gz')
ex_order = ['rr1.0', 'rr1.5', 'rr2.0', 'rr3.0', 'rr4.0', 'trail10.0', 'trail20.0', 'mid0.0']
g3['exit'] = g3['exit'].astype(str)
def exn(e):
    e = str(e); return {'rr1': 'rr1.0', 'rr2': 'rr2.0', 'rr3': 'rr3.0', 'rr4': 'rr4.0', 'trail10': 'trail10.0', 'trail20': 'trail20.0', 'mid0': 'mid0.0'}.get(e, e)
g3['exit'] = g3['exit'].map(exn)
h = g3[(g3.entry == 'brk_stop') & (g3.sl == 'chan10') & (g3.trend == 'ema') & (g3.sess == '08-21') & (g3.vol == 'all')].copy()
h['score'] = h[['is_sh', 'is_sh_P']].min(axis=1); h['oscore'] = h[['oos_sh', 'oos_sh_P']].min(axis=1)
hm = dict(L=sorted(h.L.unique().tolist()), exits=ex_order,
          is_=[[float(h[(h.L == L) & (h.exit == e)].score.iloc[0]) if len(h[(h.L == L) & (h.exit == e)]) else None for e in ex_order] for L in sorted(h.L.unique())],
          oos=[[float(h[(h.L == L) & (h.exit == e)].oscore.iloc[0]) if len(h[(h.L == L) & (h.exit == e)]) else None for e in ex_order] for L in sorted(h.L.unique())],
          nyr=[[float(h[(h.L == L) & (h.exit == e)].n_yr.iloc[0]) if len(h[(h.L == L) & (h.exit == e)]) else None for e in ex_order] for L in sorted(h.L.unique())])
# fragile trap: DC200 SL atr x exit, normal vs pess avgR
t2 = g2[(g2.L == 200) & (g2.trend == 'none') & (g2.sess == 'all') & (g2.vol == 'all')]
trap = dict(sls=['atr0.5', 'atr0.75', 'atr1.0', 'atr1.25', 'atr1.5'], exits=['rr1.5', 'rr2.0', 'rr3.0', 'rr4.0', 'rr5.0'])
def cell(sl, e, p):
    r = t2[(t2.sl == sl) & (t2.exit.astype(str).map(exn) == e) & (t2.pess == p)]
    return float(r.avgR.iloc[0]) if len(r) else None
trap['normal'] = [[cell(s, e, False) for e in trap['exits']] for s in trap['sls']]
trap['pess'] = [[cell(s, e, True) for e in trap['exits']] for s in trap['sls']]
# scatter (grid3 worst-case expectancy vs frequency)
sc = g3[g3.n_yr <= 400].sample(2600, random_state=1)
scatter = dict(stop=[[round(a, 1), round(b, 3)] for a, b, e in zip(sc.n_yr, sc.avgR_P, sc.entry) if e == 'brk_stop'],
               close=[[round(a, 1), round(b, 3)] for a, b, e in zip(sc.n_yr, sc.avgR_P, sc.entry) if e == 'brk_close'])
# entry family summary from grid 1 (normal mode)
fam = []
for (e, fr), gg in g1[g1.n_yr >= 60].groupby(['entry', 'f']):
    nm = {'brk_stop': 'Breakout stop order', 'brk_close': 'Breakout close', 'pullback': f'Pullback {int(fr*100)}%', 'fade': 'Fade di band'}[e]
    fam.append(dict(name=nm, n=len(gg), pos=float((gg.is_avgR > 0).mean() * 100), best_is=float(gg.is_sh.max()), med=float(gg.avgR.median())))
# candle example for system A, Sep-Nov 2026
c = SYS['A']; a = build(f, c['entry'], c['L'], c['sl'], c['exit_'], c['trend'], c['sess'], c['vol'], c['f'])
t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], a[8], False, 0, 0.05, 0.07, True)
up, lo = f.chan(30); ema = pd.Series(f.C).ewm(span=200, adjust=False).mean().values
i0 = idx.searchsorted(pd.Timestamp('2026-01-01')); tA = t[t[:, 0] >= i0]
best = None
for s in range(i0, len(idx) - 170, 10):
    n = ((tA[:, 0] >= s) & (tA[:, 1] < s + 170)).sum()
    if best is None or n > best[0]: best = (n, s)
s0 = best[1]; s1 = s0 + 170
bars = [[idx[i].strftime('%d %b %H:%M'), round(f.O[i], 2), round(f.H[i], 2), round(f.L[i], 2), round(f.C[i], 2), round(up[i], 2), round(lo[i], 2), round(ema[i], 2)] for i in range(s0, s1)]
trs = [dict(ei=int(r[0]) - s0, xi=int(r[1]) - s0, side=int(r[2]), R=round(float(r[3]), 2), why=int(r[4]), ep=round(float(r[5]), 2), xp=round(float(r[6]), 2)) for r in tA if r[0] >= s0 and r[1] < s1]
json.dump(dict(hm=hm, trap=trap, scatter=scatter, fam=fam, candles=dict(bars=bars, trades=trs),
               counts=dict(g1=len(g1), g2=len(g2), g3=len(g3))), open('charts.json', 'w'))
print('candles window', idx[s0], '->', idx[s1], 'trades', len(trs)); print(trs[:3]); print(fam)
