"""5%ers Bootcamp: 3 steps (+6% target, -5% static max loss), then funded (+5% first target, -4%).
Systems A+ and A++ (pessimistic trades). Risk fixed per trade, optional 'half' rule: risk x0.5 while >=2% below the step's peak.
Historical rolling starts (every month 2015-01..2024-06, real calendar time) + Monte Carlo (month blocks)."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import io, contextlib, numpy as np, pandas as pd
with contextlib.redirect_stdout(io.StringIO()):
    from aplus import run, APLUS
AP = run(*APLUS); APP = pd.concat([AP, run(20, ('chan', 15), ('mid', 0, 0), 'ema+d1+e50')])
STEPS = [(6, 5)] * 3 + [(5, 4)]
def journey(R, T, j, r, half):
    t0 = T[j] if j < len(R) else None; out = []
    for tg, ml in STEPS:
        e = 0.0; pk = 0.0
        while True:
            if j >= len(R): return out, 'data'
            rr = r * (0.5 if half and pk - e >= 2 else 1.0)
            e += R[j] * rr; pk = max(pk, e); j += 1
            if e <= -ml: return out, 'fail'
            if e >= tg: out.append((T[j - 1] - t0).days); break
    return out, 'ok'
def hist(t, r, half):
    t = t.sort_values('tout'); R = t.R.values; T = t.tout.reset_index(drop=True)
    res = [journey(R, T, T.searchsorted(m), r, half) for m in pd.date_range('2015-01-01', '2024-06-01', freq='MS')]
    done = [x for x in res if x[1] != 'data' or len(x[0]) >= 3]
    ch = [x for x in res if len(x[0]) >= 3]; pay = [x for x in res if len(x[0]) == 4]
    return len(res), len(ch), np.median([x[0][2] for x in ch]) / 30.4 if ch else np.nan, len(pay), np.median([x[0][3] for x in pay]) / 30.4 if pay else np.nan, sum(x[1] == 'fail' for x in res)
def mc(t, r, half, N=4000, seed=3):
    t = t.sort_values('tout'); g = t.groupby(t.tout.dt.to_period('M')); allm = pd.period_range(t.tout.min().to_period('M'), t.tout.max().to_period('M'), freq='M')
    months = [g.get_group(p).R.values if p in g.groups else np.array([]) for p in allm]
    rng = np.random.default_rng(seed); ch = []; pay = []; nch = npay = 0
    for _ in range(N):
        pick = rng.integers(0, len(months), 600); R = np.concatenate([months[i] for i in pick])
        mon_of = np.concatenate([np.full(len(months[i]), k) for k, i in enumerate(pick)])
        T = pd.Series(mon_of * 30.4).astype(float).values
        j = 0; e_res = []; ok = True
        for k, (tg, ml) in enumerate(STEPS):
            e = 0.0; pk = 0.0
            while j < len(R):
                rr = r * (0.5 if half and pk - e >= 2 else 1.0); e += R[j] * rr; pk = max(pk, e); j += 1
                if e <= -ml or e >= tg: break
            if e < tg: ok = False; break
            e_res.append(T[j - 1] / 30.4)
        if len(e_res) >= 3: nch += 1; ch.append(e_res[2])
        if len(e_res) == 4: npay += 1; pay.append(e_res[3])
    q = lambda a: (np.percentile(a, 25), np.median(a), np.percentile(a, 75)) if a else (np.nan,) * 3
    return nch / N * 100, q(ch), npay / N * 100, q(pay)
rows = []
for name, t, settings in [('A+', AP, [(0.2, False), (0.25, False), (0.25, True), (0.4, True), (0.5, True)]),
                          ('A++', APP, [(0.12, False), (0.15, False), (0.2, True), (0.25, True), (0.4, True)])]:
    for r, half in settings:
        n, nch, mch, npay, mpay, nfail = hist(t, r, half)
        pch, qch, ppay, qpay = mc(t, r, half)
        rows.append(dict(sistem=name, risiko=f"{r}%" + (' +½' if half else ''), hist_lulus=f"{nch}/{n}", hist_bln=round(mch, 1),
                         mc_lulus=round(pch), mc_bln_25_50_75='/'.join(f'{x:.0f}' for x in qch), mc_payout=round(ppay), payout_bln='/'.join(f'{x:.0f}' for x in qpay)))
        print(rows[-1])
pd.DataFrame(rows).to_csv('explore/prop_app.csv', index=False)
