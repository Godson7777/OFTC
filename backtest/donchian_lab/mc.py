import json, numpy as np, pandas as pd
from lab import F, label
from features import build
f = F(); idx = f.d.index
T = pd.read_pickle('trades.pkl')
port = pd.concat([T[k].assign(sys=k) for k in ['A', 'B', 'D']]).sort_values('tout').reset_index(drop=True)
port['m'] = port.tout.dt.to_period('M')
months = [g.R.values for _, g in port.groupby('m')]
allm = pd.period_range(port.m.min(), port.m.max(), freq='M')
mR = port.groupby('m').R.sum().reindex(allm, fill_value=0.0)
# max simultaneous open risk (how many positions open at once)
ev = pd.concat([pd.DataFrame(dict(t=port.ei, d=1)), pd.DataFrame(dict(t=port.xi, d=-1))]).sort_values(['t', 'd'])
maxopen = int(ev.d.cumsum().max())
cum = port.R.cumsum().values; ddR = float((np.maximum.accumulate(cum) - cum).max())
rng = np.random.default_rng(42)
RISKS = [0.1, 0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0, 1.5]
def paths(nm, N=5000):
    # month-block bootstrap of trade sequences; returns list of trade-R arrays per month
    pick = rng.integers(0, len(months), (N, nm))
    return pick
PICK = paths(12)
risk_tab = []
fan = {}
for r in RISKS:
    mon = mR.values * r
    # 12-month MC with intramonth trade order and a static -5% max loss from start (challenge-like)
    end = []; breach = 0; hit5 = 0
    eq_paths = []
    for p in PICK:
        e = 0.0; low = 0.0; dead = False; path = [0.0]
        for mi in p:
            for x in months[mi]:
                e += x * r
                if e <= -5: dead = True; break
            path.append(e)
            if dead: break
        while len(path) < 13: path.append(path[-1])
        breach += dead; end.append(e); eq_paths.append(path)
    eq = np.array(eq_paths)
    risk_tab.append(dict(risk=r, mean_month=float(mon.mean()), median_month=float(np.median(mon)), p_month5=float((mon >= 5).mean() * 100),
                         p_month_m4=float((mon <= -4).mean() * 100), worst_month=float(mon.min()), best_month=float(mon.max()),
                         hist_dd=ddR * r, mc_p_breach12=breach / len(PICK) * 100, mc_median12=float(np.median(end)),
                         mc_p_avg5=float((np.array(end) >= 60).mean() * 100)))
    fan[str(r)] = {q: [round(float(v), 2) for v in np.percentile(eq, q, axis=0)] for q in (5, 25, 50, 75, 95)}
# ---- 5%ers bootcamp: 3 steps +6/-5 (static), then funded +5/-4 (daily pause ignored; checked on closed trades)
def bootcamp(seq_months, r_eval, r_fund):
    j = 0; lvl = 0; n_tr = 0; t_ch = None; flat = np.concatenate(seq_months)
    for k, (tg, ml) in enumerate([(6, 5)] * 3 + [(5, 4)]):
        r = r_eval if k < 3 else r_fund; e = 0
        while j < len(flat):
            e += flat[j] * r; j += 1
            if e <= -ml or e >= tg: break
        if e < tg: return lvl, j, t_ch
        lvl += 1
        if lvl == 3: t_ch = j
    return lvl, j, t_ch
tpm = len(port) / len(allm)
boot = []
for re_ in [0.15, 0.2, 0.25, 0.3, 0.4, 0.5, 0.75, 1.0]:
    res = [bootcamp([months[i] for i in rng.integers(0, len(months), 400)], re_, 0.25) for _ in range(4000)]
    lv = np.array([x[0] for x in res]); tch = np.array([x[2] for x in res if x[2]]) / tpm
    boot.append(dict(risk=re_, pass_ch=float((lv >= 3).mean() * 100), payout=float((lv >= 4).mean() * 100), med_months=float(np.median(tch)) if len(tch) else None,
                     p25=float(np.percentile(tch, 25)) if len(tch) else None, p75=float(np.percentile(tch, 75)) if len(tch) else None))
# ---- per-system monthly risk needed for 5%
need = {k: 5 / max(v, 1e-9) for k, v in dict(port=mR.mean()).items()}
json.dump(dict(risk_tab=risk_tab, fan=fan, boot=boot, port_stats=dict(R_mo=float(mR.mean()), R_mo_std=float(mR.std()), trades_mo=float(tpm), maxopen=maxopen, ddR=ddR,
               pos_months=float((mR > 0).mean() * 100), need_risk_for_5=need['port'], win=float((port.R > 0).mean() * 100), avgR=float(port.R.mean())),
               port_monthly=[round(float(x), 2) for x in mR.values], port_months=[str(p) for p in allm],
               port_yearly={int(y): round(float(v), 2) for y, v in port.groupby(port.tout.dt.year).R.sum().items()}), open('mc.json', 'w'))
for x in risk_tab: print({k: round(v, 2) for k, v in x.items()})
print(boot); print('maxopen', maxopen, 'ddR', ddR, 'R/mo', mR.mean(), 'need risk', need)
