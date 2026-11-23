"""A vs A+ vs A++ (A+ plus DC20 s15 midline): equity curve, drawdown, consecutive losses. Pessimistic mode, risk 0.25%/trade (fixed, non-compounded)."""
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'explore')
import json, numpy as np, pandas as pd
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.dates as mdates
from aplus import run, APLUS, f, idx
RISK = 0.25
A = run(30, ('chan', 10), ('mid', 0, 0), 'ema')                      # System A (filter: EMA200 only)
AP = run(*APLUS)
D20 = run(20, ('chan', 15), ('mid', 0, 0), 'ema+d1+e50')
APP = pd.concat([AP, D20])
def analyse(t, name):
    t = t.sort_values(['tout', 'tin']).reset_index(drop=True)
    eq = t.R.cumsum() * RISK; peak = eq.cummax(); dd = peak - eq
    i = dd.idxmax(); pk = eq[:i + 1].idxmax()
    rec = eq[i:][eq[i:] >= peak[i]]; rec_i = rec.index[0] if len(rec) else None
    # underwater durations
    uw = []; start = None
    for k in range(len(eq)):
        if dd[k] > 1e-9 and start is None: start = k
        if dd[k] <= 1e-9 and start is not None: uw.append((t.tout[start], t.tout[k])); start = None
    if start is not None: uw.append((t.tout[start], t.tout.iloc[-1]))
    longest = max(uw, key=lambda x: x[1] - x[0])
    s = ''.join('L' if r < 0 else 'W' for r in t.R); runs = [len(x) for x in s.split('W') if x]
    yrs = (idx[-1] - idx[0]).days / 365.25
    m = t.groupby(t.tout.dt.to_period('M')).R.sum() * RISK
    # top 5 drawdown episodes
    eps = []; k = 0; e = eq.values; p = peak.values
    while k < len(e):
        if p[k] - e[k] > 1e-9:
            j = k
            while j < len(e) and p[j] - e[j] > 1e-9: j += 1
            seg = slice(k, j); low = k + int(np.argmax(p[seg] - e[seg]))
            eps.append(dict(start=str(t.tout[k - 1].date()) if k else str(t.tout[0].date()), bottom=str(t.tout[low].date()),
                            end=str(t.tout[j].date()) if j < len(e) else 'belum pulih', depth=round(float(p[low] - e[low]), 2), trades=j - k))
            k = j
        else: k += 1
    eps = sorted(eps, key=lambda x: -x['depth'])[:5]
    res = dict(name=name, trades=len(t), per_mo=round(len(t) / yrs / 12, 1), win=round(100 * (t.R > 0).mean(), 1), pf=round(t.R[t.R > 0].sum() / -t.R[t.R < 0].sum(), 2),
               total_pct=round(eq.iloc[-1], 1), per_mo_pct=round(eq.iloc[-1] / yrs / 12, 2), maxdd_pct=round(dd.max(), 2), maxdd_R=round(dd.max() / RISK, 1),
               dd_peak=str(t.tout[pk].date()), dd_bottom=str(t.tout[i].date()), dd_recovered=str(t.tout[rec_i].date()) if rec_i is not None else 'belum',
               longest_uw_days=(longest[1] - longest[0]).days, longest_uw=f"{longest[0].date()} s/d {longest[1].date()}",
               max_losses=max(runs), loss_runs_ge8=sum(r >= 8 for r in runs), loss_runs_ge10=sum(r >= 10 for r in runs),
               worst_month=round(m.min(), 2), best_month=round(m.max(), 2), pos_months=round(100 * (m > 0).mean()), eps=eps,
               run_hist={k: int(v) for k, v in pd.Series(runs).value_counts().sort_index().items()})
    return res, t.tout, eq, dd
out = {}; curves = {}
for name, t in [('A', A), ('A+', AP), ('A++', APP)]:
    r, x, eq, dd = analyse(t, name); out[name] = r; curves[name] = (x, eq, dd)
    print({k: v for k, v in r.items() if k not in ('eps', 'run_hist')}); print('   top DD:', r['eps']); print('   loss runs:', r['run_hist'])
json.dump(out, open('explore/compare_app.json', 'w'), indent=1)
# ---- chart
col = {'A': '#8a8f98', 'A+': '#2a78d6', 'A++': '#eb6834'}
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 8.2), sharex=True, gridspec_kw=dict(height_ratios=[2.2, 1]))
for n in ['A', 'A+', 'A++']:
    x, eq, dd = curves[n]; r = out[n]
    a1.plot(x, eq, color=col[n], lw=2.2 if n != 'A' else 1.6, label=f"{n}: {r['per_mo']} trade/bln, PF {r['pf']}, total +{r['total_pct']}%, max DD {r['maxdd_pct']}%")
    a2.plot(x, -dd, color=col[n], lw=1.6)
a1.axhline(0, color='#c3c2b7', lw=1); a1.set_ylabel('Akumulasi profit (% akun, risiko 0,25%/trade)')
a1.set_title('Equity curve XAUUSD H1 2015–2026 (asumsi pesimis, termasuk spread/komisi/slippage)', loc='left', fontsize=12)
a1.legend(loc='upper left', frameon=False, fontsize=10)
for v, lab in [(-5, 'max loss 5%ers (−5%)'), (-4, 'max loss funded (−4%)')]:
    a2.axhline(v, color='#e34948', lw=1, ls='--'); a2.text(curves['A'][0].iloc[0], v + 0.15, lab, fontsize=9, color='#52514e')
a2.set_ylabel('Drawdown dari puncak (%)'); a2.xaxis.set_major_locator(mdates.YearLocator()); a2.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
for a in (a1, a2):
    a.grid(axis='y', color='#ecebe8'); [a.spines[s].set_visible(False) for s in ('top', 'right')]; a.tick_params(colors='#52514e')
fig.patch.set_facecolor('#fcfcfb'); [a.set_facecolor('#fcfcfb') for a in (a1, a2)]
plt.tight_layout(); plt.savefig('explore/equity_A_Aplus_Aplusplus.png', dpi=150)
