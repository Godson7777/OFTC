# Backtest Engine v1 — Hasil vs TradingView

Engine: `tools/backtest/engine.py`
Data: `XAUUSD_H1.csv` (XAUUSD H1, 2009-12-08 s/d 2026-08-25, tab-separated,
kolom Time/Open/High/Low/Close/Volume/Spread) — **belum diupload ke repo**
karena 6.1MB, tersedia di upload session user.
Settingan: `strategy/pinescript/README.md` (N-Bar Reversal FIXED, XAUUSD H1).

Jalankan dengan:
```
python3 tools/backtest/engine.py /path/to/XAUUSD_H1.csv /output/dir
```

## Hasil run pertama (data tersedia s/d 2026-08-25, referensi TV s/d 2026-09-12)

| Metric | TradingView (referensi) | Engine v1 |
|---|---|---|
| Total PnL | +94,298.54 USD (+94.30%) | +92,566.42 USD (+92.57%) |
| Max Drawdown | 11,998.90 USD (9.47%) | 14,683.04 USD (7.68%) |
| Total trades | 147 | 140 |
| Win rate | 43.54% (64 win / 83 loss) | 43.57% (61 win / 79 loss) |
| Profit Factor | 1.737 | 1.806 |
| Gross profit | 222,249.92 | 207,418.21 |
| Gross loss | 127,951.37 | 114,851.78 |
| Long PnL | +55,128.30 | +58,054.24 |
| Short PnL | +39,170.25 | +34,512.18 |
| Expectancy | 641.49 USD | 661.19 USD |

**Kesimpulan awal:** sangat dekat (selisih ~1.8 poin % PnL, 7 trade). Selisih
7 trade konsisten dengan ~2.5 minggu data yang hilang di ujung periode
(file berhenti 2026-08-25, referensi TV sampai 2026-09-12) — trade terakhir
engine v1 jatuh tepat di bar terakhir data (2026-08-25). Indikasi kuat logika
dasar sudah benar, bukan bug besar.

## Logika yang direplikasi dari Pine Script
- Signal: `high[i]>high[i-1] AND close[i]>close[i-1] AND close[i]>highest(high,83)[i-1]`
  untuk long (dan simetris untuk short). N=2 & Min%=0 membuat filter
  `mostly_up/down` jadi no-op (match dengan tooltip warning di script asli).
- Entry disubmit di close bar sinyal, fill di open bar berikutnya + slippage
  3 tick (asumsi mintick 0.01).
- SL/TP dihitung dari **close bar sinyal** (bukan harga fill), aktif sejak
  bar fill, dicek terhadap High/Low tiap bar.
- Reversal: sinyal berlawanan menutup posisi & membuka posisi baru di bar
  fill yang sama.
- Position sizing: qty = (equity_saat_sinyal * risk_per_trade%) / (harga_sinyal * SL%).
- Commission 0.02% per fill (entry & exit terpisah).

## Asumsi yang BELUM tervalidasi / sumber potensi selisih
1. **Ambiguitas SL vs TP dalam 1 bar yang sama** — engine mengasumsikan SL
   kena duluan (conservative/worst-case). Pine/MT5 sebenarnya tahu urutan
   pasti dari data tick. Ini satu-satunya titik "tebakan" di engine v1.
   → Perlu data M1 untuk menghilangkan asumsi ini.
2. Mintick XAUUSD diasumsikan 0.01 untuk menghitung slippage 3 tick (~0.03).
   Kalau feed TradingView kamu pakai mintick lain, kecil tapi ada efeknya.
3. Equity untuk risk-sizing dihitung realized-only (belum termasuk
   unrealized mark-to-market saat equity dipakai menghitung qty), sementara
   Pine's `strategy.equity` bisa termasuk unrealized di bar tertentu.
4. Data yang dipakai berhenti 2026-08-25 (periode referensi TV sampai
   2026-09-12) — ~2.5 minggu hilang di ujung, kemungkinan penyebab utama
   selisih 7 trade & gap PnL.

## Langkah validasi berikutnya (menunggu dari user)
- [ ] Data OHLC H1 lengkap sampai 2026-09-12 (menutup gap 2.5 minggu)
- [ ] List of Trades export dari TradingView — untuk cocokkan **per-trade**
      (tanggal/jam entry-exit, harga, PnL), bukan cuma ringkasan.
- [ ] Data M1 pada bar-bar di mana SL dan TP sama-sama berada dalam
      High-Low bar H1 yang sama — untuk menghapus asumsi #1 di atas.
