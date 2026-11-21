import time, numpy as np, pandas as pd
from core import load, simulate
from features import Feat, build
d = load(); F = Feat(d)
def run(entry, L, sl, ex, trend='none', sess='all', vol='all', reverse=False, slip=0.05, comm=0.07):
    a = build(F, entry, L, sl, ex, trend, sess, vol)
    t = simulate(F.O, F.H, F.L, F.C, F.SP, *a[:8], a[8], reverse, 0, slip, comm)
    return t
t0 = time.time(); t = run('brk_stop', 20, ('atr', 2), ('rr', 2)); print('first (compile)', round(time.time()-t0, 2), 's')
t0 = time.time()
for _ in range(20): t = run('brk_stop', 20, ('atr', 2), ('rr', 2))
print('per run', round((time.time()-t0)/20*1000, 1), 'ms')
for args in [('brk_stop', 20, ('atr', 2), ('rr', 2)), ('brk_close', 83, ('atr', 1.5), ('rr', 2.5)), ('pullback', 55, ('atr', 1.5), ('rr', 2)), ('fade', 20, ('atr', 1.5), ('rr', 1)), ('brk_stop', 55, ('chan', 20), ('trail', 20))]:
    t = run(*args); R = t[:, 3]
    print(args, 'n/yr', round(len(t)/11.85), 'win', round((R > 0).mean()*100, 1), 'avgR', round(R.mean(), 3), 'reasons', np.unique(t[:, 4], return_counts=True))
# sanity: no trade exits before entry, R of SL ~ -1 - cost
sl = R[t[:, 4] == 1]; print('SL R median', np.median(sl).round(3), ' exits>=entries', (t[:, 1] >= t[:, 0]).all())
