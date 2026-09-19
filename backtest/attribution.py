"""Berapa bar yang lolos tiap syarat Tahap 3, sendiri-sendiri dan kumulatif."""
import engine

CSV = '/root/.claude/uploads/531b72a7-242d-5297-9bd1-d07ca8f87be4/018f30b3-XAUUSD_H1.csv'
bars = engine.load(CSV)
cfg = engine.Config()
n = len(bars)
o = [b['open'] for b in bars]; h = [b['high'] for b in bars]
l = [b['low'] for b in bars]; c = [b['close'] for b in bars]; v = [b['volume'] for b in bars]

atr = engine.sma([h[i]-l[i] for i in range(n)], cfg.lookback)
av  = engine.sma(v, cfg.lookback)
em  = engine.ema(c, cfg.ema_len)

names = ['Arah (close>open)', 'Tren EMA50', 'Ledakan ukuran (TR>1.5xATR)',
         'Ledakan volume (V>1.5xAV)', 'Dominasi body (>=75%)', 'Ekor bawah (<=10%)']
solo = [0]*6; cum = [0]*6; total = 0

for i in range(max(cfg.lookback, cfg.ema_len), n):
    if atr[i] is None or av[i] is None or em[i] is None: continue
    tr = h[i]-l[i]
    if tr <= 0: continue
    total += 1
    body = abs(c[i]-o[i]); lower = min(c[i],o[i]) - l[i]
    ck = [c[i] > o[i],
          c[i] > em[i],
          tr > atr[i]*cfg.size_mult,
          v[i] > av[i]*cfg.vol_mult,
          body >= tr*cfg.body_min,
          lower <= tr*cfg.wick_max]
    alive = True
    for j, ok in enumerate(ck):
        if ok: solo[j] += 1
        alive = alive and ok
        if alive: cum[j] += 1

print(f'Total bar dianalisis: {total:,}  (hanya sisi BULLISH)\n')
print(f'{"Syarat":<32}{"Lolos sendiri":>16}{"Lolos kumulatif":>18}{"% sisa":>10}')
print('-'*76)
for j in range(6):
    print(f'{names[j]:<32}{solo[j]:>10,} ({solo[j]/total*100:4.1f}%){cum[j]:>12,}{cum[j]/total*100:>9.3f}%')
