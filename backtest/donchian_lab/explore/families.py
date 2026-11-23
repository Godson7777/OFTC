"""New edge families on XAUUSD, pessimistic intrabar mode, IS 2015-2022 / OOS 2023-2026.
1) Asian-range breakout  2) previous-day high/low breakout  3) H4 Donchian (A+ logic on H4)."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import itertools, numpy as np, pandas as pd
from core import load, simulate; from features import Feat, build
from feat2 import extra
d = load(); F = Feat(d); X = extra(F); idx = d.index; n = len(d)
O, H, L, C, SP, atr = F.O, F.H, F.L, F.C, F.SP, F.atr
SPLIT = pd.Timestamp('2023-01-01'); YRS = (idx[-1] - idx[0]).days / 365.25
def met(t, ix=idx):
    if len(t) < 60: return None
    R = t[:, 3]; te = ix[t[:, 0].astype(int)]; isn = te < SPLIT; pf = lambda r: r[r > 0].sum() / max(-r[r < 0].sum(), 1e-9)
    cum = np.cumsum(R); dd = (np.maximum.accumulate(cum) - cum).max(); ys = pd.Series(R, index=te).groupby(te.year).sum()
    return dict(n_mo=len(R) / YRS / 12, avgR=R.mean(), pf=pf(R), is_pf=pf(R[isn]), oos_pf=pf(R[~isn]), R_mo=R.sum() / YRS / 12, dd=dd,
                calmar=(R.sum() / YRS / 12) / max(dd, 1e-9), yrs_pos=int((ys > 0).sum()))
day = idx.normalize(); hr = idx.hour.values
d1L, d1S = X['d1'] == 1, X['d1'] == 0
rows = []
# ---------- 1) Asian range breakout
for a_end, act_to, slm, rr, mb, filt in itertools.product([7, 8, 9], [14, 17, 20], ['opp', 'mid'], [1.0, 1.5, 2.0, 3.0], [0, 12], ['none', 'd1']):
    g = pd.DataFrame(dict(H=H, L=L, day=day, hr=hr))
    asia = g[(g.hr >= 1) & (g.hr < a_end)].groupby('day').agg(ah=('H', 'max'), al=('L', 'min'))
    ah = asia.ah.reindex(day).values; al = asia.al.reindex(day).values
    act = (hr >= a_end) & (hr <= act_to) & ~np.isnan(ah)
    lvlL = np.where(act, ah, np.nan); lvlS = np.where(act, al, np.nan)
    typL = np.where(act, 1, 0).astype(np.int64); typS = typL.copy()
    if filt == 'd1': typL[~d1L] = 0; typS[~d1S] = 0
    width = ah - al
    dL = width if slm == 'opp' else width / 2; dL = np.clip(dL, 0.3 * atr, 6 * atr); dS = dL.copy()
    bad = np.isnan(dL) | (width < 0.5 * atr); typL[bad] = 0; typS[bad] = 0
    nanv = np.full(n, np.nan)
    t = simulate(O, H, L, C, SP, lvlL, typL, dL, lvlS, typS, dS, nanv, nanv, rr, False, mb, 0.05, 0.07, True)
    m = met(t)
    if m: rows.append(dict(fam='Asia range', cfg=f'asia 01-{a_end:02d}, aktif s/d {act_to}, SL {slm}, TP {rr}R, time {mb}, {filt}', **m))
# ---------- 2) previous-day high/low breakout
dd_ = d.resample('1D').agg(dict(HIGH='max', LOW='min')).dropna(); pdh = dd_.HIGH.shift(1).reindex(day).values; pdl = dd_.LOW.shift(1).reindex(day).values
for act_from, act_to, sl, ex, filt in itertools.product([1, 8], [17, 21], [('chan', 5), ('chan', 10), ('atr', 2.0)], [('rr', 2.0), ('rr', 3.0), ('trail', 20), ('trail', 10)], ['d1', 'd1+e50']):
    act = (hr >= act_from) & (hr <= act_to) & ~np.isnan(pdh)
    lvlL = np.where(act, pdh, np.nan); lvlS = np.where(act, pdl, np.nan); typL = act.astype(np.int64); typS = typL.copy()
    mL = d1L & (X['ema50_200'] > 0) if filt == 'd1+e50' else d1L; mS = d1S & (X['ema50_200'] < 0) if filt == 'd1+e50' else d1S
    typL[~mL] = 0; typS[~mS] = 0
    if sl[0] == 'chan':
        ux, lx = F.chan(sl[1]); dL = np.clip(lvlL - lx, 0.5 * atr, 4 * atr); dS = np.clip(ux - lvlS, 0.5 * atr, 4 * atr)
    else: dL = sl[1] * atr; dS = dL.copy()
    bad = np.isnan(dL) | np.isnan(dS); typL[np.isnan(dL)] = 0; typS[np.isnan(dS)] = 0
    tr = np.full(n, np.nan); trS = tr.copy(); rr = 0.0
    if ex[0] == 'rr': rr = ex[1]
    else: ux, lx = F.chan(ex[1]); tr, trS = lx, ux
    t = simulate(O, H, L, C, SP, lvlL, typL, np.nan_to_num(dL, nan=1.0), lvlS, typS, np.nan_to_num(dS, nan=1.0), tr, trS, rr, False, 0, 0.05, 0.07, True)
    m = met(t)
    if m: rows.append(dict(fam='PDH/PDL', cfg=f'jam {act_from}-{act_to}, SL {sl[0]}{sl[1]}, exit {ex[0]}{ex[1]}, {filt}', **m))
# ---------- 3) H4 Donchian (A+ style)
d4 = d.resample('4h').agg(dict(OPEN='first', HIGH='max', LOW='min', CLOSE='last', SPREAD='mean', SP='mean')).dropna()
F4 = Feat(d4); X4 = extra(F4); i4 = d4.index
for L_, sl, ex, filt in itertools.product([10, 20, 30, 55], [('chan', 3), ('chan', 5), ('chan', 10)], [('mid', 0), ('trail', 10), ('trail', 20), ('rr', 3.0)], ['ema', 'ema+d1+e50', 'd1']):
    a = list(build(F4, 'brk_stop', L_, sl, ex, 'none', 'all', 'all'))
    mL = {'ema': F4.ema_bull, 'd1': X4['d1'] == 1, 'ema+d1+e50': F4.ema_bull & (X4['d1'] == 1) & (X4['ema50_200'] > 0)}[filt]
    mS = {'ema': F4.ema_bear, 'd1': X4['d1'] == 0, 'ema+d1+e50': F4.ema_bear & (X4['d1'] == 0) & (X4['ema50_200'] < 0)}[filt]
    a[1] = np.where(mL, a[1], 0); a[4] = np.where(mS, a[4], 0)
    t = simulate(F4.O, F4.H, F4.L, F4.C, F4.SP, *a[:8], a[8], False, 0, 0.05, 0.07, True)
    m = met(t, i4)
    if m: rows.append(dict(fam='H4 Donchian', cfg=f'DC{L_} SL {sl[0]}{sl[1]} exit {ex[0]}{ex[1]} {filt}', **m))
g = pd.DataFrame(rows); g.to_csv('explore/families.csv', index=False)
pd.set_option('display.width', 250); pd.set_option('display.max_colwidth', 70)
g['score'] = g[['is_pf']].min(axis=1)
for fam, gg in g.groupby('fam'):
    print(f'\n== {fam}: {len(gg)} konfigurasi, IS PF>1.15 & OOS PF>1.15: {((gg.is_pf>1.15)&(gg.oos_pf>1.15)).sum()}')
    print(gg.sort_values('is_pf', ascending=False).head(6)[['cfg', 'n_mo', 'avgR', 'pf', 'is_pf', 'oos_pf', 'R_mo', 'dd', 'calmar', 'yrs_pos']].round(3).to_string(index=False))
