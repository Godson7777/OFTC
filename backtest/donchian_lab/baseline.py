"""Baseline = the user's current TradingView strategy 'N-Bar Rev FIXED' with their inputs:
N=2, Min%=0, Enhanced, Donchian 83 'With Trend' filter, SL 1% of price, TP = 2.5R, reverse on opposite.
Signal on bar close -> market fill next open. Real spread + slippage + commission."""
import numpy as np, pandas as pd
from core import load
def baseline_trades(d, slip=0.05, comm=0.07):
    O, H, L, C, SP = [d[c].values for c in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'SP']]
    up = pd.Series(H).rolling(83).max().shift(1).values; lo = pd.Series(L).rolling(83).min().shift(1).values
    out = []; pos = 0; pend = 0
    for i in range(86, len(d)):
        if pend:
            s, sigc = pend; pend = 0
            if pos:
                px = O[i] - slip * pos; out.append((ei, i, pos, ((px - ep) * pos - cost) / risk, 4)); pos = 0
            ep = O[i] + slip * s; risk = sigc * 0.01; slp = sigc * (1 - s * 0.01); tpp = sigc * (1 + s * 0.025)
            pos = s; ei = i; cost = SP[i] + comm + slip
        if pos:
            first_low = (O[i] - L[i]) < (H[i] - O[i])
            hs = (L[i] <= slp) if pos > 0 else (H[i] >= slp); ht = (H[i] >= tpp) if pos > 0 else (L[i] <= tpp)
            hit = None
            if hs and ht: hit = 'SL' if (first_low if pos > 0 else not first_low) else 'TP'
            elif hs: hit = 'SL'
            elif ht: hit = 'TP'
            if hit == 'SL':
                px = (min(slp, O[i]) if pos > 0 else max(slp, O[i])) - slip * pos
                out.append((ei, i, pos, ((px - ep) * pos - cost) / risk, 1)); pos = 0
            elif hit == 'TP':
                px = max(tpp, O[i]) if pos > 0 else min(tpp, O[i])
                out.append((ei, i, pos, ((px - ep) * pos - cost) / risk, 2)); pos = 0
        lc = H[i] > H[i - 1] and C[i] > C[i - 1] and C[i] > up[i]
        sc = L[i] < L[i - 1] and C[i] < C[i - 1] and C[i] < lo[i]
        if lc and pos <= 0: pend = (1, C[i])
        elif sc and pos >= 0: pend = (-1, C[i])
    return np.array(out, float)
if __name__ == '__main__':
    from metrics import metrics
    d = load(); t = baseline_trades(d); m = metrics(t, d.index)
    print({k: round(v, 3) if isinstance(v, float) else v for k, v in m.items()})
