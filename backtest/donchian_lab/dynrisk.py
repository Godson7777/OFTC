import json, numpy as np, pandas as pd
T = pd.read_pickle('trades.pkl')
port = pd.concat([T[k] for k in ['A', 'B', 'D']]).sort_values('tout'); port['m'] = port.tout.dt.to_period('M')
months = [g.R.values for _, g in port.groupby('m')]; tpm = len(port) / (port.m.max() - port.m.min()).n
rng = np.random.default_rng(7)
def step(flat, j, r0, tg, ml, rule):
    e = 0.0; peak = 0.0
    while j < len(flat):
        dd = peak - e
        r = r0
        if rule == 'half2' and dd >= 2: r = r0 / 2
        if rule == 'ladder':  # cut risk as the account nears max loss, add a little once ahead
            room = e + ml
            r = r0 * (0.5 if room < 3 else 1.0) * (1.25 if e > 3 else 1.0)
        e += flat[j] * r; j += 1; peak = max(peak, e)
        if e <= -ml or e >= tg: break
    return e >= tg, j
def boot(r_eval, rule, N=4000):
    ok = 0; tm = []
    for _ in range(N):
        flat = np.concatenate([months[i] for i in rng.integers(0, len(months), 400)]); j = 0; good = True
        for _s in range(3):
            p, j = step(flat, j, r_eval, 6, 5, rule)
            if not p: good = False; break
        if good: ok += 1; tm.append(j / tpm)
    return ok / N * 100, float(np.median(tm)) if tm else None
res = []
for r in [0.25, 0.3, 0.4, 0.5, 0.75]:
    row = dict(risk=r)
    for rule in ['flat', 'half2', 'ladder']:
        p, m = boot(r, rule); row[rule] = round(p, 1); row[rule + '_mo'] = round(m, 1) if m else None
    res.append(row); print(row)
json.dump(res, open('dynrisk.json', 'w'))
