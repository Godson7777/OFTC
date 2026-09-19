"""Apakah candle momentum punya daya prediksi arah sama sekali?

Dua uji, keduanya lepas dari aturan Entry/SL/TP:
  1. Return ke depan setelah sinyal vs baseline seluruh bar.
  2. MFE / MAE dalam satuan R: seberapa jauh harga bergerak mendukung
     dibanding melawan, sehingga terlihat apakah ADA kombinasi TP/SL
     yang bisa profit.
"""
import engine
from statistics import mean, median

CSV = '/root/.claude/uploads/531b72a7-242d-5297-9bd1-d07ca8f87be4/018f30b3-XAUUSD_H1.csv'
bars = engine.load(CSV)
cfg = engine.Config()
n = len(bars)
o=[b['open'] for b in bars]; h=[b['high'] for b in bars]
l=[b['low'] for b in bars]; c=[b['close'] for b in bars]; v=[b['volume'] for b in bars]

atr = engine.sma([h[i]-l[i] for i in range(n)], cfg.lookback)
av  = engine.sma(v, cfg.lookback); em = engine.ema(c, cfg.ema_len)

def signal(i):
    if atr[i] is None or av[i] is None or em[i] is None: return 0
    tr = h[i]-l[i]
    if tr <= 0 or atr[i] <= 0: return 0
    body = abs(c[i]-o[i]); up = h[i]-max(c[i],o[i]); lo = min(c[i],o[i])-l[i]
    base = tr > atr[i]*cfg.size_mult and body >= tr*cfg.body_min and v[i] > av[i]*cfg.vol_mult
    if not base: return 0
    if c[i] > o[i] and c[i] > em[i] and lo <= tr*cfg.wick_max: return 1
    if c[i] < o[i] and c[i] < em[i] and up <= tr*cfg.wick_max: return -1
    return 0

start = max(cfg.lookback, cfg.ema_len)
sigs = [(i, signal(i)) for i in range(start, n-30)]
bull = [i for i,s in sigs if s == 1]; bear = [i for i,s in sigs if s == -1]
allb = [i for i,s in sigs]

print('=== UJI 1: return ke depan (dalam ATR, searah sinyal) ===\n')
print(f'{"Horizon":<12}{"Bullish":>14}{"Bearish":>14}{"Gabungan":>14}{"Baseline":>14}')
print('-'*68)
for hz in (1, 4, 8, 12, 24):
    fb = [(c[i+hz]-c[i])/atr[i] for i in bull]
    fs = [(c[i]-c[i+hz])/atr[i] for i in bear]
    base_up = [(c[i+hz]-c[i])/atr[i] for i in allb if atr[i] and atr[i] > 0]
    print(f'{str(hz)+" bar":<12}{mean(fb):>+14.4f}{mean(fs):>+14.4f}'
          f'{mean(fb+fs):>+14.4f}{mean(base_up):>+14.4f}')

print(f'\n  n bullish = {len(bull)}, n bearish = {len(bear)}, n baseline = {len(allb):,}\n')

print('=== UJI 2: MFE / MAE dalam satuan R (R = jarak Entry->SL default) ===\n')
print(f'{"Horizon":<12}{"MFE avg":>10}{"MAE avg":>10}{"MFE med":>10}{"MAE med":>10}{"% MFE>2R":>10}{"% MAE>1R":>10}')
print('-'*72)
for hz in (5, 10, 20, 30):
    mfes, maes = [], []
    for i, s in sigs:
        if s == 0: continue
        sh, sl_ = h[i], l[i]; rg = sh - sl_
        e = sh - cfg.fib_entry*rg if s == 1 else sl_ + cfg.fib_entry*rg
        anc = sl_ if s == 1 else sh
        st = anc - cfg.sl_atr*atr[i] if s == 1 else anc + cfg.sl_atr*atr[i]
        R = abs(e - st)
        if R <= 0: continue
        seg = range(i+1, min(i+1+hz, n))
        if s == 1:
            mfes.append((max(h[j] for j in seg) - e)/R); maes.append((e - min(l[j] for j in seg))/R)
        else:
            mfes.append((e - min(l[j] for j in seg))/R); maes.append((max(h[j] for j in seg) - e)/R)
    p2 = sum(1 for x in mfes if x >= 2.0)/len(mfes)*100
    p1 = sum(1 for x in maes if x >= 1.0)/len(maes)*100
    print(f'{str(hz)+" bar":<12}{mean(mfes):>10.2f}{mean(maes):>10.2f}'
          f'{median(mfes):>10.2f}{median(maes):>10.2f}{p2:>10.1f}{p1:>10.1f}')
