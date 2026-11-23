"""Extra features, all known at the OPEN of bar i (computed from bars <= i-1)."""
import numpy as np, pandas as pd
from features import rma
def shift1(x): return np.r_[np.nan, x[:-1]]
def extra(F):
    d = F.d; H, L, C, O = F.H, F.L, F.C, F.O; n = len(C)
    pc = np.r_[np.nan, C[:-1]]
    tr = np.nanmax(np.c_[H - L, np.abs(H - pc), np.abs(L - pc)], axis=1); atr = rma(tr, 14)
    up = H - np.r_[np.nan, H[:-1]]; dn = np.r_[np.nan, L[:-1]] - L
    pdm = np.where((up > dn) & (up > 0), up, 0.0); ndm = np.where((dn > up) & (dn > 0), dn, 0.0)
    pdi = 100 * rma(pdm, 14) / atr; ndi = 100 * rma(ndm, 14) / atr
    dx = 100 * np.abs(pdi - ndi) / (pdi + ndi); adx = rma(np.nan_to_num(dx), 14)
    delta = np.diff(C, prepend=C[0]); g = rma(np.maximum(delta, 0), 14); l = rma(np.maximum(-delta, 0), 14); rsi = 100 - 100 / (1 + g / l)
    ema200 = pd.Series(C).ewm(span=200, adjust=False).mean().values
    ema50 = pd.Series(C).ewm(span=50, adjust=False).mean().values
    med = pd.Series(atr).rolling(480, min_periods=100).median().values
    up30 = pd.Series(H).rolling(30).max().values; lo30 = pd.Series(L).rolling(30).min().values
    dc = d.CLOSE.resample('1D').last().dropna(); de = dc.ewm(span=20, adjust=False).mean(); d1 = (dc > de).astype(float).shift(1)
    d1v = d1.reindex(d.index.normalize()).values
    wc = d.CLOSE.resample('W').last().dropna(); we = wc.ewm(span=10, adjust=False).mean(); w1 = (wc > we).astype(float).shift(1)
    w1v = w1.reindex(d.index.to_period('W').to_timestamp('W'), method=None).values if False else w1.reindex(d.index, method='ffill').values
    f = dict(
        atr_ratio=shift1(atr / med), adx=shift1(adx), di_diff=shift1(pdi - ndi), rsi=shift1(rsi),
        ema_dist=shift1((C - ema200) / atr), ema_slope=shift1((ema200 - np.r_[np.full(24, np.nan), ema200[:-24]]) / atr),
        ema50_200=shift1((ema50 - ema200) / atr), chan_w=shift1((up30 - lo30) / atr), d1=d1v, w1=w1v,
        hour=d.index.hour.values.astype(float), dow=d.index.dayofweek.values.astype(float),
        body_prev=shift1((C - O) / atr), range_prev=shift1((H - L) / atr),
        mom24=shift1((C - np.r_[np.full(24, np.nan), C[:-24]]) / atr))
    return f
