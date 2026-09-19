# Hasil Backtest - Momentum Candle

**Data:** XAUUSD H1, 100.000 bar, 8 Des 2009 - 25 Agu 2026 (16,7 tahun)
**Modal awal:** $10.000 · **Risiko:** 1% per transaksi · **Pyramiding:** 0

---

## Ringkasan

Strategi ini **tidak memiliki edge** pada XAUUSD H1. Setelah biaya transaksi
yang wajar, hasilnya negatif. Sebelum biaya, kinerjanya tidak dapat dibedakan
secara statistik dari entry acak.

Ini adalah kesimpulan tentang **data XAUUSD H1**, bukan vonis atas seluruh
strategi. Keterbatasannya dijelaskan di bagian akhir.

---

## 1. Konfigurasi default

| Metrik | Nilai |
|---|---|
| Sinyal valid | 61 |
| Order terpasang | 59 |
| Terisi (fill) | 53 (89,8%) |
| Dibatalkan - kedaluwarsa | 6 |
| Dilewati filter RR | 1 |
| **Total transaksi** | **53** |
| Win rate | 30,2% |
| Profit Factor | 0,73 |
| Net P&L | -$1.098 (-11,0%) |
| Max drawdown | 17,3% |
| Rata-rata R | -0,21 R |
| Kalah beruntun terpanjang | 12 |

**53 transaksi dalam 16,7 tahun = ~3 transaksi per tahun.** Sampel sekecil ini
tidak cukup untuk menyimpulkan apa pun secara statistik. Itulah sebabnya
analisis di bawah menggunakan filter yang dilonggarkan untuk memperbesar sampel.

---

## 2. Filter mana yang paling membatasi

Dari 99.600 bar yang dianalisis (sisi bullish saja):

| Syarat | Lolos sendiri | Sisa kumulatif |
|---|---|---|
| Arah (close > open) | 50,5% | 50,533% |
| Tren EMA 50 | 53,1% | 30,192% |
| Ledakan ukuran (TR > 1,5 x ATR) | 16,4% | 5,743% |
| **Ledakan volume (V > 1,5 x AV)** | **4,6%** | **0,188%** |
| Dominasi body (>= 75%) | 13,8% | 0,051% |
| Ekor bawah (<= 10%) | 23,0% | 0,040% |

Filter volume adalah penyaring terbesar: memangkas 5.720 kandidat menjadi 187
(-97%). Volume tick XAUUSD H1 jauh lebih rata daripada yang diasumsikan SOP,
jadi syarat 150% jarang terpenuhi bersamaan dengan candle raksasa.

---

## 3. Uji edge: apakah sinyalnya lebih baik dari acak?

Kontrol: entry acak dengan geometri Entry/SL/TP yang **identik**, 10 seed,
tanpa biaya transaksi.

| | n | Profit Factor | Rata-rata R |
|---|---|---|---|
| Sinyal Momentum Candle (filter longgar) | 2.609 | 1,019 | +0,0222 |
| Entry acak (rata-rata 10 seed) | ~1.870 | ~1,009 | +0,0185 |
| Simpangan baku kontrol | | | 0,0271 |

**Jarak sinyal momentum dari entry acak: +0,14 simpangan baku.** Secara
statistik, nol. Filter momentum tidak menambahkan informasi apa pun di luar
apa yang sudah dihasilkan geometri level Entry/SL/TP itu sendiri.

Kontrol acak yang menghasilkan PF ~1,00 tanpa biaya juga berfungsi sebagai
validasi engine: simulator yang bias akan memberi angka yang menyimpang jauh
dari 1,00.

---

## 4. Dampak biaya transaksi

Inilah yang menentukan hasil akhir.

| Strategi | Asumsi biaya | n | PF | Rata-rata R | Return |
|---|---|---|---|---|---|
| Filter longgar | Tanpa biaya | 2.609 | 1,02 | +0,022 | +37,4% |
| Filter longgar | Spread emas 0,30 | 2.609 | 0,96 | -0,016 | -50,7% |
| Filter longgar | 0,04% + 1 tick | 2.609 | 0,82 | -0,144 | -98,2% |
| Default SOP | Tanpa biaya | 53 | 0,86 | -0,094 | -5,4% |
| Default SOP | Spread emas 0,30 | 53 | 0,83 | -0,117 | -6,6% |
| Default SOP | 0,04% + 1 tick | 53 | 0,73 | -0,210 | -11,0% |

Rata-rata ukuran R adalah $23,85/oz (karena SL ditaruh di bawah seluruh candle
raksasa + 0,5 ATR), pada harga emas rata-rata $2.277. Komisi 0,04% per sisi
memakan **0,115 R per transaksi** - setiap transaksi dimulai dari minus 12%
risiko. Edge kotornya hanya +0,022 R, jadi biaya menelannya beberapa kali lipat.

> **Koreksi:** angka 0,04% adalah default yang saya pasang di script dan itu
> lazim untuk crypto, bukan emas. Default tersebut sudah saya ubah menjadi 0
> agar tidak diam-diam mendistorsi hasil; isi biaya sesuai broker kamu lewat
> tab Properties.

---

## 5. Grid 29 varian parameter

Semua negatif dengan asumsi biaya default. Yang paling dekat breakeven:

| Varian | n | Win% | PF | Return |
|---|---|---|---|---|
| Hanya LONG | 34 | 35,3 | 0,90 | -2,7% |
| ATR True Range | 52 | 34,6 | 0,89 | -4,1% |
| SL buffer 1,0 ATR | 54 | 33,3 | 0,86 | -5,4% |
| Exp_Candles 10 | 56 | 33,9 | 0,86 | -5,8% |
| TP Fibo 0,27 (SOP), minRR=0 | 50 | **58,0** | 0,49 | -11,4% |
| Hanya SHORT | 20 | 20,0 | 0,43 | -9,6% |
| Tanpa filter volume | 1.392 | 34,1 | 0,82 | -86,1% |

TP Fibo 0,27 memang menghasilkan win rate tertinggi (58%), tepat seperti yang
diperkirakan dari RR 0,46-0,66. Tetapi PF-nya justru terburuk kedua: win rate
tinggi tidak menutup reward yang terlalu kecil. Ini mengonfirmasi perhitungan
RR di awal secara empiris.

Membalik arah sinyal (fade momentum) juga rugi: PF 0,97 tanpa biaya pada
n=1.964. Tidak ada edge yang bisa dipanen di kedua arah.

---

## 6. Apa yang sebenarnya terjadi setelah candle momentum

Return ke depan dalam satuan ATR, searah sinyal, konfigurasi default (n=61):

| Horizon | Bullish | Bearish | Gabungan | Baseline seluruh bar |
|---|---|---|---|---|
| 1 bar | -0,168 | -0,182 | -0,173 | +0,007 |
| 4 bar | -0,358 | -0,684 | -0,470 | +0,029 |
| 8 bar | -0,510 | -1,015 | -0,684 | +0,058 |
| 12 bar | -0,808 | -0,777 | -0,798 | +0,091 |
| 24 bar | -0,328 | -0,558 | -0,407 | +0,168 |

Angka ini terlihat seperti mean reversion yang kuat, tetapi **n hanya 61**.
Pada sampel besar (n=2.609) edge-nya kembali ke nol, jadi pembacaan "harga
selalu berbalik setelah candle momentum" itu tidak didukung data - itu
kebisingan sampel kecil.

MFE/MAE dalam satuan R (n=61) lebih informatif:

| Horizon | MFE rata-rata | MAE rata-rata | % MFE >= 2R | % MAE >= 1R |
|---|---|---|---|---|
| 5 bar | 0,54 | 0,49 | 0,0% | 14,8% |
| 10 bar | 0,70 | 0,70 | 3,3% | 24,6% |
| 20 bar | 1,05 | 1,18 | 6,6% | 49,2% |
| 30 bar | 1,19 | 1,34 | 13,1% | 54,1% |

Hanya 13% sinyal yang pernah mencapai 2R bahkan setelah 30 bar, sementara 54%
sudah menyentuh 1R melawan. Dengan profil seperti ini, target 1:2 memang tidak
realistis - bukan karena SOP-nya salah, tetapi karena R-nya (seluruh candle
raksasa + 0,5 ATR) terlalu besar untuk dijangkau dua kali lipat.

---

## 7. Keterbatasan - baca sebelum menyimpulkan

1. **Timeframe salah.** SOP dirancang untuk M15; data ini H1. Karakteristik
   candle momentum di M15 bisa berbeda. Kesimpulan ini belum diuji di M15.
2. **Satu instrumen.** Hanya XAUUSD. Emas terkenal mean-reverting di
   intraday; hasilnya bisa berbeda di indeks atau crypto.
3. **Volume tick, bukan volume sebenarnya.** Data forex/CFD tidak punya
   volume terpusat. Filter volume SOP mungkin bekerja lebih baik di instrumen
   dengan volume bursa asli (saham, futures).
4. **Asumsi intrabar.** Engine memakai jalur TradingView (bar naik: O-L-H-C).
   Itu asumsi, bukan tick sebenarnya.
5. **Tanpa spread variabel.** Biaya dimodelkan datar; spread emas melebar saat
   rollover dan rilis berita, justru saat candle momentum sering muncul. Jadi
   hasil sebenarnya kemungkinan lebih buruk, bukan lebih baik.

---

## Cara menjalankan ulang

```bash
cd backtest
python3 compare.py       # grid 29 varian
python3 attribution.py   # kontribusi tiap filter
python3 edge_test.py     # uji daya prediksi
python3 chart.py         # grafik equity -> equity.png
```

Engine ada di `engine.py`. Semua parameter ada di dataclass `Config` dan
namanya sama persis dengan input di `momentum_candle.pine`.
