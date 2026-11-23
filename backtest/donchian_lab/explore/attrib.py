"""Which conditions at entry separate winners from losers in System A? IS = 2015-2022, OOS = 2023-2026."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import numpy as np, pandas as pd
from core import simulate; from features import build; from lab import F
from feat2 import extra
f = F(); idx = f.d.index; X = extra(f)
a = build(f, 'brk_stop', 30, ('chan', 10), ('mid', 0), 'ema', '08-21', 'all', 0.5)
t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], a[8], False, 0, 0.05, 0.07, True)
T = pd.DataFrame(dict(ei=t[:, 0].astype(int), side=t[:, 2], R=t[:, 3])); T['tin'] = idx[T.ei]; T['is'] = T.tin < '2023'
for k, v in X.items(): T[k] = v[T.ei]
# direction-aware versions
for k in ['di_diff', 'ema_dist', 'ema_slope', 'ema50_200', 'mom24', 'body_prev']: T[k + '_s'] = T[k] * T.side
T['rsi_s'] = np.where(T.side > 0, T.rsi, 100 - T.rsi); T['d1_al'] = np.where(T.side > 0, T.d1 == 1, T.d1 == 0).astype(float)
T['w1_al'] = np.where(T.side > 0, T.w1 == 1, T.w1 == 0).astype(float)
pd.set_option('display.width', 220)
print('ALL  IS avgR %.3f n=%d | OOS avgR %.3f n=%d' % (T[T['is']].R.mean(), T['is'].sum(), T[~T['is']].R.mean(), (~T['is']).sum()))
print('side:', T.groupby(['side', 'is']).R.agg(['count', 'mean']).round(3).to_dict('index'))
rows = []
for k in ['atr_ratio', 'adx', 'di_diff_s', 'rsi_s', 'ema_dist_s', 'ema_slope_s', 'ema50_200_s', 'chan_w', 'mom24_s', 'body_prev_s', 'range_prev', 'hour', 'dow', 'd1_al', 'w1_al']:
    if k in ('hour', 'dow', 'd1_al', 'w1_al'): q = T[k]
    else:
        edges = np.nanquantile(T[T['is']][k], [0, .2, .4, .6, .8, 1]); edges[0] -= 1e9; edges[-1] += 1e9
        q = pd.cut(T[k], np.unique(edges), labels=False)
    g = T.assign(q=q).groupby(['q', 'is']).R.mean().unstack()
    rows.append((k, g))
    print(f'\n{k}  (kolom: OOS / IS avgR)'); print(g.round(3).rename(columns={True: 'IS', False: 'OOS'})[['IS', 'OOS']].T.to_string())
T.to_pickle('explore/A_trades_feat.pkl')
