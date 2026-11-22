"""Backtest of the user's manual rules (reconstructed from 47 manual trades, Aug 2026):
1. XAUUSD H1. Pattern on 3 closed candles: green-green-red = BUY, red-red-green = SELL.
2. Reference candle = largest High-Low of the 3 (tie -> latest).
3. Entry = pending order at the reference candle's close (stop or limit depending on where price is).
4. SL = reference candle's open if the candle points in the trade direction, otherwise its wick
   (low for buy, high for sell), plus a buffer of $0.50 beyond it.
5. TP = 3R. No trade management.
6. One trade at a time: while a position is open (floating + or -) patterns are ignored; wait for TP or SL.
7. A newer pattern replaces a pending order that has not been triggered.
8. Risk 0.25% per trade."""
import pandas as pd, numpy as np, bt
idx = bt.idx
def report(t, name):
    t = t.copy(); t['tin'] = idx[t.ei]; yrs = (idx[-1] - idx[0]).days / 365.25
    mon = t.groupby(t.tin.dt.to_period('M')).R.sum(); cum = t.R.cumsum(); dd = (cum.cummax() - cum).max()
    streak = max(len(x) for x in ''.join('L' if r < 0 else 'W' for r in t.R).split('W'))
    print(f"{name}: {len(t)} trade ({len(t)/yrs/12:.1f}/bln) | win {100*(t.R>0).mean():.1f}% | avg {t.R.mean():+.3f}R | PF {t.R[t.R>0].sum()/-t.R[t.R<0].sum():.2f} "
          f"| total {t.R.sum():+.0f}R | DD {dd:.0f}R | kalah beruntun maks {streak} | bulan positif {100*(mon>0).mean():.0f}%")
    return t, mon
if __name__ == '__main__':
    base = dict(sl_mode='open_or_wick', buf=0.5)
    print('== Aturan manual, biaya nyata (spread data + komisi $0.07 + slip $0.05 di stop order)')
    tn, mn = report(bt.run('normal', **base), 'Normal (4-tick)')
    tp, mp = report(bt.run('pess', **base), 'Pesimis        ')
    print('   R per tahun (normal):', {y: round(v, 1) for y, v in tn.groupby(tn.tin.dt.year).R.sum().items()})
    print('   R per tahun (pesimis):', {y: round(v, 1) for y, v in tp.groupby(tp.tin.dt.year).R.sum().items()})
    print('   2026 per bulan (normal):', {str(k): round(v, 1) for k, v in mn['2026-01':].items()})
    print('\n== Tanpa biaya sama sekali (edge murni pola)')
    report(bt.run('normal', comm=0.0, slip=0.0, **base), 'Normal, biaya 0 kecuali spread')

