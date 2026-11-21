import numpy as np, pandas as pd
from core import load

def rma(x, n):
    out = np.full(len(x), np.nan); a = 1.0 / n; s = np.nanmean(x[1:n + 1]); out[n] = s
    for i in range(n + 1, len(x)): s = a * x[i] + (1 - a) * s; out[i] = s
    return out

class Feat:
    """Pre-computed series. Index convention: value[i] uses only bars <= i-1 (known at open of bar i)."""
    def __init__(self, d):
        self.d = d; self.O, self.H, self.L, self.C, self.SP = [d[c].values.astype(float) for c in ['OPEN', 'HIGH', 'LOW', 'CLOSE', 'SP']]
        H, L, C = self.H, self.L, self.C
        pc = np.r_[np.nan, C[:-1]]
        tr = np.nanmax(np.c_[H - L, np.abs(H - pc), np.abs(L - pc)], axis=1)
        atr = rma(tr, 14)
        self.atr = np.r_[np.nan, atr[:-1]]                                   # known at open
        med = pd.Series(atr).rolling(480, min_periods=100).median().values
        self.volhi = np.r_[False, (atr > med)[:-1]]
        ema200 = pd.Series(C).ewm(span=200, adjust=False).mean().values
        self.ema_bull = np.r_[False, (C > ema200)[:-1]]; self.ema_bear = np.r_[False, (C < ema200)[:-1]]
        dc = d.CLOSE.resample('1D').last().dropna(); de = dc.ewm(span=20, adjust=False).mean()
        bull_d = (dc > de).shift(1)                                         # previous completed day
        m = bull_d.reindex(d.index.normalize()).values
        self.d1_bull = (m == True); self.d1_bear = (m == False)
        hr = d.index.hour.values
        self.sess = {'all': np.ones(len(d), bool), '08-21': (hr >= 8) & (hr <= 21), '14-21': (hr >= 14) & (hr <= 21)}
        self._ch = {}

    def chan(self, n):
        """highest high / lowest low of the n bars BEFORE bar i."""
        if n not in self._ch:
            up = pd.Series(self.H).rolling(n).max().shift(1).values
            lo = pd.Series(self.L).rolling(n).min().shift(1).values
            self._ch[n] = (up, lo)
        return self._ch[n]

def build(F, entry, L, sl, exit_, trend, sess, vol, f=0.5):
    """Return arrays for core.simulate.
    entry: 'brk_stop' | 'brk_close' | 'pullback' | 'fade'
    sl:    ('atr', k) | ('chan', X)
    exit_: ('rr', r) | ('trail', X) | ('mid', 0)"""
    n = len(F.O); O, C, atr = F.O, F.C, F.atr
    up, lo = F.chan(L)
    lvlL = np.full(n, np.nan); lvlS = np.full(n, np.nan); typL = np.zeros(n, np.int64); typS = np.zeros(n, np.int64)
    if entry == 'brk_stop':
        lvlL[:] = up; lvlS[:] = lo; typL[:] = 1; typS[:] = 1
    elif entry == 'brk_close':
        sigL = np.r_[False, (C > up)[:-1]]; sigS = np.r_[False, (C < lo)[:-1]]
        typL[sigL] = 3; typS[sigS] = 3; lvlL[:] = O; lvlS[:] = O
    elif entry in ('pullback', 'fade'):
        if entry == 'pullback':
            st = np.zeros(n); brk = np.where(C > up, 1, np.where(C < lo, -1, 0)); cur = 0
            for i in range(n):
                st[i] = cur
                if brk[i] != 0: cur = brk[i]
            lvL = lo + f * (up - lo); lvS = up - f * (up - lo)
            okL = st > 0; okS = st < 0
        else:
            lvL = lo.copy(); lvS = up.copy(); okL = np.ones(n, bool); okS = np.ones(n, bool)
        lvlL[okL] = lvL[okL]; typL[okL] = 2; lvlS[okS] = lvS[okS]; typS[okS] = 2
    # filters
    if trend == 'ema':  aL, aS = F.ema_bull, F.ema_bear
    elif trend == 'd1': aL, aS = F.d1_bull, F.d1_bear
    else:               aL = aS = np.ones(n, bool)
    s = F.sess[sess]; v = F.volhi if vol == 'hi' else np.ones(n, bool)
    okL = aL & s & v; okS = aS & s & v
    if entry == 'fade' and trend != 'none':   # fade: buy dips only in uptrend, sell rips only in downtrend
        pass
    typL[~okL] = 0; typS[~okS] = 0
    base = np.where(typL == 3, O, lvlL); baseS = np.where(typS == 3, O, lvlS)
    if sl[0] == 'atr':
        dL = sl[1] * atr; dS = dL.copy()
    else:   # structure: distance from the order level to the opposite X-bar extreme, clipped to [0.5, 4] ATR
        ux, lx = F.chan(int(sl[1]))
        dL = np.clip(base - lx, 0.5 * atr, 4 * atr); dS = np.clip(ux - baseS, 0.5 * atr, 4 * atr)
    dL = np.where(np.isnan(dL), np.nan, dL); slL, slS = dL, dS
    trailL = np.full(n, np.nan); trailS = np.full(n, np.nan); rr = 0.0
    if exit_[0] == 'rr':
        rr = float(exit_[1])
    elif exit_[0] == 'trail':
        ux, lx = F.chan(int(exit_[1])); trailL, trailS = lx, ux
    elif exit_[0] == 'mid':
        trailL = (up + lo) / 2; trailS = trailL.copy()
    bad = np.isnan(atr) | np.isnan(up)
    typL[bad] = 0; typS[bad] = 0
    return lvlL, typL, slL, lvlS, typS, slS, trailL, trailS, rr
