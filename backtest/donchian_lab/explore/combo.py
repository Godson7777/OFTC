"""Portfolios: A+ with H4 DC55 and PDH/PDL breakout. Compare profit/month per unit drawdown and prop-firm timing."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import io, contextlib, numpy as np, pandas as pd
from core import load, simulate; from features import Feat, build; from feat2 import extra
with contextlib.redirect_stdout(io.StringIO()):
    from aplus import run, APLUS
d = load(); F = Feat(d); X = extra(F); idx = d.index; n = len(d); YRS = (idx[-1] - idx[0]).days / 365.25
def df(t, ix): return pd.DataFrame(dict(ei=t[:, 0].astype(int), xi=t[:, 1].astype(int), R=t[:, 3], tin=ix[t[:, 0].astype(int)], tout=ix[t[:, 1].astype(int)]))
# H4 DC55 SL chan3 trail20 d1
d4 = d.resample('4h').agg(dict(OPEN='first', HIGH='max', LOW='min', CLOSE='last', SPREAD='mean', SP='mean')).dropna(); F4 = Feat(d4); X4 = extra(F4)
a = list(build(F4, 'brk_stop', 55, ('chan', 3), ('trail', 20), 'none', 'all', 'all')); a[1] = np.where(X4['d1'] == 1, a[1], 0); a[4] = np.where(X4['d1'] == 0, a[4], 0)
H4 = df(simulate(F4.O, F4.H, F4.L, F4.C, F4.SP, *a[:8], a[8], False, 0, 0.05, 0.07, True), d4.index)
# PDH/PDL 8-17, SL chan10, trail20, d1+e50
day = idx.normalize(); hr = idx.hour.values
dd_ = d.resample('1D').agg(dict(HIGH='max', LOW='min')).dropna(); pdh = dd_.HIGH.shift(1).reindex(day).values; pdl = dd_.LOW.shift(1).reindex(day).values
act = (hr >= 8) & (hr <= 17) & ~np.isnan(pdh); typL = act.astype(np.int64); typS = typL.copy()
typL[~((X['d1'] == 1) & (X['ema50_200'] > 0))] = 0; typS[~((X['d1'] == 0) & (X['ema50_200'] < 0))] = 0
ux, lx = F.chan(10); atr = F.atr; dL = np.clip(pdh - lx, 0.5 * atr, 4 * atr); dS = np.clip(ux - pdl, 0.5 * atr, 4 * atr)
typL[np.isnan(dL)] = 0; typS[np.isnan(dS)] = 0; u20, l20 = F.chan(20)
PD = df(simulate(F.O, F.H, F.L, F.C, F.SP, np.where(act, pdh, np.nan), typL, np.nan_to_num(dL, nan=1.0), np.where(act, pdl, np.nan), typS, np.nan_to_num(dS, nan=1.0), l20, u20, 0.0, False, 0, 0.05, 0.07, True), idx)
AP = run(*APLUS); D20 = run(20, ('chan', 15), ('mid', 0, 0), 'ema+d1+e50')
S = {'A+': AP, 'DC20': D20, 'H4': H4, 'PDH': PD}
M = pd.DataFrame({k: v.groupby(v.tout.dt.to_period('M')).R.sum() for k, v in S.items()}).fillna(0)
print('korelasi bulanan\n', M.corr().round(2))
def stats(t, name):
    t = t.sort_values('tout'); cum = t.R.cumsum(); dd = (cum.cummax() - cum).max(); rmo = t.R.sum() / YRS / 12
    runs = [len(x) for x in ''.join('L' if r < 0 else 'W' for r in t.R).split('W') if x]
    ys = t.groupby(t.tout.dt.year).R.sum()
    print(f"{name:24s} {len(t)/YRS/12:5.1f} tr/bln | PF {t.R[t.R>0].sum()/-t.R[t.R<0].sum():.2f} | {rmo:+.2f}R/bln | DD {dd:5.1f}R | R/bln per DD {rmo/dd:.3f} | kalah beruntun {max(runs)} | tahun+ {(ys>0).sum()}/{len(ys)}")
    return t
combos = {'A+': ['A+'], 'A++ (A+ + DC20)': ['A+', 'DC20'], 'A+ + H4': ['A+', 'H4'], 'A+ + PDH': ['A+', 'PDH'], 'A+ + H4 + PDH': ['A+', 'H4', 'PDH'], 'A++ + H4 + PDH': ['A+', 'DC20', 'H4', 'PDH']}
T = {k: stats(pd.concat([S[x] for x in v]), k) for k, v in combos.items()}
# prop: probability of first funded payout within 4 / 6 / 12 months, by risk (fixed risk, +half rule)
STEPS = [(6, 5)] * 3 + [(5, 4)]
rng = np.random.default_rng(11)
def prop(t, r, N=4000):
    t = t.sort_values('tout'); g = t.groupby(t.tout.dt.to_period('M')); allm = pd.period_range(t.tout.min().to_period('M'), t.tout.max().to_period('M'), freq='M')
    months = [g.get_group(p).R.values if p in g.groups else np.array([]) for p in allm]
    hit = {4: 0, 6: 0, 12: 0}; passed = 0
    for _ in range(N):
        pick = rng.integers(0, len(months), 40); lvl = 0; e = 0.0; pk = 0.0; done = False
        for mi, p in enumerate(pick):
            for x in months[p]:
                tg, ml = STEPS[lvl]; rr = r * (0.5 if pk - e >= 2 else 1.0); e += x * rr; pk = max(pk, e)
                if e <= -ml: done = True; break
                if e >= tg:
                    lvl += 1; e = 0.0; pk = 0.0
                    if lvl == 4:
                        for h in hit:
                            if mi + 1 <= h: hit[h] += 1
                        passed += 1; done = True; break
            if done: break
    return {h: round(v / N * 100, 1) for h, v in hit.items()}, round(passed / N * 100, 1)
print('\nPeluang sampai PAYOUT funded pertama (3 step + funded 5%) dalam <=4 / 6 / 12 bulan, aturan potong ½ saat turun 2%:')
for k in ['A+', 'A++ (A+ + DC20)', 'A+ + H4 + PDH', 'A++ + H4 + PDH']:
    for r in [0.25, 0.5, 0.75, 1.0, 1.5]:
        h, p = prop(T[k], r); print(f'  {k:18s} risk {r:4}% -> <=4 bln {h[4]:5.1f}% | <=6 bln {h[6]:5.1f}% | <=12 bln {h[12]:5.1f}% | payout kapan pun (<=40 bln) {p}%')
for k, v in {'H4': H4, 'PDH': PD}.items(): v.to_csv(f'explore/trades_{k}.csv', index=False)
