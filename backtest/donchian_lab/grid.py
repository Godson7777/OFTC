import itertools, time, numpy as np, pandas as pd, multiprocessing as mp
from core import load, simulate
from features import Feat, build
from metrics import metrics
ENTRIES = [('brk_stop', 0.5), ('brk_close', 0.5), ('pullback', 0.5), ('pullback', 0.25), ('fade', 0.5)]
LENS = [10, 20, 30, 40, 55, 83, 120, 200]
SLS = [('atr', 1.0), ('atr', 1.5), ('atr', 2.0), ('atr', 3.0), ('chan', 10)]
EXITS = [('rr', 1.0), ('rr', 1.5), ('rr', 2.0), ('rr', 2.5), ('rr', 3.0), ('rr', 4.0), ('trail', 10), ('mid', 0)]
TRENDS = ['none', 'ema', 'd1']; SESS = ['all', '08-21', '14-21']; VOLS = ['all', 'hi']; REVS = [False, True]
F = None
def init():
    global F
    F = Feat(load())
def job(L):
    out = []
    for (e, f), sl, ex, tr, ss, vo, rv in itertools.product(ENTRIES, SLS, EXITS, TRENDS, SESS, VOLS, REVS):
        a = build(F, e, L, sl, ex, tr, ss, vo, f)
        t = simulate(F.O, F.H, F.L, F.C, F.SP, *a[:8], a[8], rv, 0, 0.05, 0.07)
        m = metrics(t, F.d.index)
        if m: out.append(dict(entry=e, f=f, L=L, sl=f'{sl[0]}{sl[1]}', exit=f'{ex[0]}{ex[1]}', trend=tr, sess=ss, vol=vo, rev=rv, **m))
    return out
if __name__ == '__main__':
    t0 = time.time()
    with mp.Pool(4, initializer=init) as p:
        res = p.map(job, LENS)
    g = pd.DataFrame([r for part in res for r in part]); g.to_parquet('grid.parquet') if False else g.to_csv('grid.csv.gz', index=False)
    print(len(g), 'configs in', round(time.time() - t0), 's')
