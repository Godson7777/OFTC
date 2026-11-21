import json, numpy as np, pandas as pd
from core import simulate
from features import build
from lab import F, run, monthly, label
from baseline import baseline_trades
from metrics import metrics
f = F(); idx = f.d.index
def cfg(entry, L, sl, ex, trend, sess, vol, rev=False, fr=0.5):
    return dict(entry=entry, L=L, sl=sl, exit_=ex, trend=trend, sess=sess, vol=vol, f=fr, rev=rev)
def runp(c, pess=False, slip=0.05):
    a = build(f, c['entry'], c['L'], c['sl'], c['exit_'], c['trend'], c['sess'], c['vol'], c['f'])
    t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], a[8], c['rev'], 0, slip, 0.07, pess)
    return pd.DataFrame(dict(tin=idx[t[:, 0].astype(int)], tout=idx[t[:, 1].astype(int)], side=t[:, 2].astype(int), R=t[:, 3], why=t[:, 4].astype(int), ei=t[:, 0].astype(int), xi=t[:, 1].astype(int))), t
SYS = {
 'A': cfg('brk_stop', 30, ('chan', 10), ('mid', 0), 'ema', '08-21', 'all'),
 'B': cfg('brk_stop', 10, ('chan', 10), ('trail', 20), 'none', '08-21', 'all'),
 'C': cfg('brk_stop', 30, ('chan', 10), ('trail', 20), 'ema', '08-21', 'all'),
 'D': cfg('brk_close', 10, ('atr', 2.5), ('rr', 1.5), 'ema', '08-21', 'hi'),
 'X': cfg('brk_stop', 200, ('atr', 1.0), ('rr', 3.0), 'none', 'all', 'all'),   # fragile H1 "champion"
}
out = {'systems': {}}
bt = baseline_trades(f.d); bdf = pd.DataFrame(dict(tout=idx[bt[:, 1].astype(int)], R=bt[:, 3], tin=idx[bt[:, 0].astype(int)]))
def summ(df, t):
    m = metrics(t, idx); mm = monthly(df)
    yr = df.set_index('tout').R.groupby(lambda x: x.year).sum()
    return dict(n_yr=m['n_yr'], n_mo=m['n_yr'] / 12, win=m['win'], avgR=m['avgR'], pf=m['pf'], ddR=m['ddR'], m_mean=mm.mean(), m_std=mm.std(),
                m_pos=(mm > 0).mean() * 100, is_sh=m['is_sh'], oos_sh=m['oos_sh'], is_avgR=m['is_avgR'], oos_avgR=m['oos_avgR'],
                yrs_pos=int((yr > 0).sum()), yrs=len(yr), yearly={int(k): round(v, 2) for k, v in yr.items()},
                cum=[round(x, 2) for x in mm.cumsum().values], months=[d.strftime('%Y-%m') for d in mm.index], monthly=[round(x, 2) for x in mm.values])
out['systems']['BASE'] = dict(label='Strategi kamu sekarang (N2 + DC83 filter, SL 1%, TP 2.5R)', normal=summ(bdf, bt))
for k, c in SYS.items():
    dn, tn = runp(c); dp, tp = runp(c, True)
    out['systems'][k] = dict(label=label(c), cfg={**c, 'sl': list(c['sl']), 'exit_': list(c['exit_'])}, normal=summ(dn, tn), pess=summ(dp, tp),
                             slip={str(s): float(runp(c, True, s)[0].R.mean()) for s in (0.05, 0.2, 0.5, 1.0)})
    print(k, out['systems'][k]['label'], {kk: round(v, 3) for kk, v in out['systems'][k]['pess'].items() if isinstance(v, float)}, 'slip', {s: round(v, 3) for s, v in out['systems'][k]['slip'].items()})
    if k == 'A': A_tr = dp
    if k == 'B': B_tr = dp
    if k == 'D': D_tr = dp
# ---- portfolio (pessimistic trades), each system risks the same r per trade
port = {k: monthly(runp(SYS[k], True)[0]) for k in ['A', 'B', 'C', 'D']}
P = pd.DataFrame(port); print('monthly corr\n', P.corr().round(2))
for combo in [['A'], ['A', 'B'], ['A', 'B', 'D'], ['A', 'B', 'C', 'D'], ['B', 'D']]:
    s = P[combo].sum(axis=1); print(combo, 'R/mo %.2f std %.2f sharpe %.3f trades/mo %.1f pos %.0f%%' % (s.mean(), s.std(), s.mean() / s.std(), sum(out['systems'][k]['pess']['n_mo'] for k in combo), (s > 0).mean() * 100))
json.dump(out, open('analysis.json', 'w'))
pd.to_pickle(dict(A=A_tr, B=B_tr, D=D_tr, P=P), 'trades.pkl')
