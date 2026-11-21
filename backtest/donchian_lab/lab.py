"""Shared helpers: run a named config, monthly series, Monte Carlo, prop-firm simulation."""
import numpy as np, pandas as pd
from core import load, simulate
from features import Feat, build
_F = None
def F():
    global _F
    if _F is None: _F = Feat(load())
    return _F
def parse(row):
    sl = (row['sl'][:3], float(row['sl'][3:])) if row['sl'].startswith('atr') else ('chan', float(row['sl'][4:]))
    ex = row['exit']
    exit_ = ('rr', float(ex[2:])) if ex.startswith('rr') else (('trail', float(ex[5:])) if ex.startswith('trail') else ('mid', 0))
    return dict(entry=row['entry'], L=int(row['L']), sl=sl, exit_=exit_, trend=row['trend'], sess=row['sess'], vol=row['vol'], f=float(row['f']), rev=bool(row['rev']))
def run(cfg, slip=0.05, comm=0.07):
    f = F(); a = build(f, cfg['entry'], cfg['L'], cfg['sl'], cfg['exit_'], cfg['trend'], cfg['sess'], cfg['vol'], cfg['f'])
    t = simulate(f.O, f.H, f.L, f.C, f.SP, *a[:8], a[8], cfg['rev'], 0, slip, comm)
    idx = f.d.index
    return pd.DataFrame(dict(tin=idx[t[:, 0].astype(int)], tout=idx[t[:, 1].astype(int)], side=t[:, 2].astype(int), R=t[:, 3], why=t[:, 4].astype(int), ei=t[:, 0].astype(int), xi=t[:, 1].astype(int)))
def monthly(tr, col='R'):
    idx = F().d.index
    m = tr.set_index('tout')[col].resample('MS').sum()
    return m.reindex(pd.date_range(idx[0].to_period('M').to_timestamp(), idx[-1], freq='MS'), fill_value=0.0)
def label(cfg):
    ex = cfg['exit_']; exs = f"TP {ex[1]:g}R" if ex[0] == 'rr' else (f"trail {int(ex[1])}-bar" if ex[0] == 'trail' else 'trail midline')
    sl = f"SL {cfg['sl'][1]:g}xATR" if cfg['sl'][0] == 'atr' else 'SL struktur 10-bar'
    en = {'brk_stop': 'Breakout (stop order)', 'brk_close': 'Breakout (close)', 'pullback': f"Pullback {int(cfg['f']*100)}%", 'fade': 'Fade band'}[cfg['entry']]
    tr = {'none': '', 'ema': ' + EMA200', 'd1': ' + tren D1'}[cfg['trend']]
    ss = {'all': '', '08-21': ' + jam 08-21', '14-21': ' + jam 14-21'}[cfg['sess']]
    vv = ' + ATR tinggi' if cfg['vol'] == 'hi' else ''
    rv = ' + reverse' if cfg['rev'] else ''
    return f"{en} DC{cfg['L']}, {sl}, {exs}{tr}{ss}{vv}{rv}"
