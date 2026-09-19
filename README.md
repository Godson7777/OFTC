# Momentum Candle — Pine Script v6 Strategy

Implementasi penuh SOP *High-Precision Rules* (Tahap 1–7) untuk TradingView.

File: [`momentum_candle.pine`](momentum_candle.pine)

---

## Prinsip desain

Setiap angka di SOP dipetakan 1:1 ke sebuah `input()`. Tidak ada konstanta yang
di-hardcode diam-diam, dan setiap titik yang di SOP masih ambigu diangkat menjadi
pilihan eksplisit — sehingga hasil backtest selalu dapat direproduksi.

---

## Temuan matematis yang mengubah default

SOP asli menempatkan:

```
Entry = Sig_High − 0.236 · R          (R = Sig_High − Sig_Low)
SL    = Sig_Low  − 0.5   · ATR
TP    = Sig_High + 0.27  · R
```

Untuk posisi BUY:

```
Reward = TP − Entry  = 0.27R + 0.236R      = 0.506 · R
Risk   = Entry − SL  = 0.764R + 0.5 · ATR
```

Tahap 3 mensyaratkan `R > 1.5 · ATR`, maka `0.5 · ATR < 0.333 · R`, sehingga:

| Kondisi | Risk | RR |
|---|---|---|
| Batas terbaik (ATR → 0) | 0.764 · R | **1 : 0.662** |
| Batas terburuk (ATR = R / 1.5) | 1.097 · R | **1 : 0.461** |

**RR terkunci di rentang 0.46 – 0.66 untuk semua simbol, timeframe, dan kondisi
market.** Filter RR 1:1.5 di Tahap 7 karena itu akan memblokir 100% sinyal.

Agar syarat minimal 1:2 dapat dipenuhi, `TP Mode` default diubah menjadi
**RR Target**: `TP = Entry ± (Target RR × Risk)`, dengan `Target RR = 2.0`.
Mode `Fibo Extension (SOP)` tetap tersedia untuk replikasi harfiah.

---

## Pengaturan default

| Input | Default | Sumber |
|---|---|---|
| Timeframe wajib | `15` (dikunci) | Tahap 1 |
| Lookback | `20` | Tahap 1 |
| Body_Min | `0.75` | Tahap 1 |
| Wick_Max | `0.10` | Tahap 1 |
| Vol_Multiplier | `1.5` | Tahap 1 |
| Size_Multiplier | `1.5` | Tahap 1 |
| EMA Tren | `50` | Tahap 1 |
| Exp_Candles | `5` | Tahap 1 |
| Metode ATR | `High-Low (literal SOP)` | Tahap 2 (ambigu — lihat di bawah) |
| Fibo Entry | `0.236` | Tahap 5 |
| Metode SL | `Sig_Low/High ± ATR (SOP)`, pengali `0.5` | Tahap 5 |
| Metode TP | `RR Target`, target `2.0` | **diubah** — lihat temuan di atas |
| Fibo Extension TP | `0.27` | Tahap 5 (mode alternatif) |
| Risiko per transaksi | `1.0 %` | Tahap 7 |
| Filter RR minimum | `2.0` | **diubah** dari 1.5 sesuai permintaan |

---

## Ambiguitas SOP dan cara penyelesaiannya

### 1. Definisi "ATR" (Tahap 2)

SOP mendefinisikan `TR = High − Low`, lalu menyebut rata-ratanya sebagai *Average
True Range*. True Range yang sebenarnya ikut memperhitungkan gap terhadap close
sebelumnya, sehingga kedua definisi menghasilkan angka berbeda — dan nilai ini
dipakai di filter ukuran candle **dan** di perhitungan Stop Loss.

Diselesaikan lewat input `Metode perhitungan ATR`. Default mengikuti teks SOP
secara harfiah (`High-Low`); opsi `True Range (ta.atr)` tersedia.

### 2. SL tertembus sebelum Entry (Tahap 6 rule 3)

Untuk Buy Limit, SL selalu berada **di bawah** Entry. Harga tidak dapat mencapai
SL tanpa melewati Entry lebih dulu, sehingga skenario ini secara geometris hanya
mungkin terjadi melalui **gap**. Aturan diimplementasikan sebagai: pending order
belum terisi **dan** bar menyentuh level SL.

### 3. Urutan intrabar Entry vs TP (Tahap 6 rule 2)

Pine Script tidak mengetahui urutan pergerakan di dalam satu bar. Penyelesaian
dibuat deterministik tanpa asumsi tambahan:

* Pembatalan "TP duluan" hanya aktif bila bar menyentuh TP **dan tidak pernah**
  menyentuh Entry.
* Bila keduanya tersentuh dalam bar yang sama, broker emulator TradingView
  mengisi Entry lebih dulu (Entry selalu lebih dekat ke harga berjalan daripada
  TP), sehingga `strategy.position_size != 0` dan blok pembatalan dilewati.

---

## Arsitektur

State machine berbasis `var`, tiga status:

```
MENUNGGU SINYAL  →  PENDING ORDER  →  POSISI TERBUKA  →  MENUNGGU SINYAL
                         │
                         └── dibatalkan (timeout / TP duluan / gap SL)
```

Selama `tradeActive = true`, semua candle momentum baru diabaikan (Tahap 4).
Order masuk lewat `strategy.entry(..., limit=)`; TP dan SL dipasang simultan
lewat `strategy.exit(stop=, limit=)` yang otomatis membentuk grup OCA.

---

## Cara pakai

1. Buka TradingView → **Pine Editor** → tempel isi `momentum_candle.pine`.
2. **Add to chart**, lalu pindahkan chart ke timeframe **M15**.
3. Buka **Settings** untuk menyesuaikan parameter.
4. Panel kanan atas menampilkan status, level aktif, RR aktual, sisa candle
   sebelum kedaluwarsa, dan jumlah sinyal yang dilewati filter RR.

### Matikan `Kunci strategi ke timeframe wajib` bila ingin uji di timeframe lain.

### Untuk mereplikasi SOP asli secara harfiah

Set `Metode Take Profit` = `Fibo Extension (SOP)` **dan** `Filter RR minimum` = `0`.
Tanpa menurunkan filter RR, hasilnya akan 0 trade — itu perilaku yang benar.

---

## Catatan risiko

Dengan `Target RR = 2.0` dan SL mode SOP, jarak TP menjadi sekitar 2.2 × R dari
Entry (R = panjang candle sinyal yang sudah ≥ 1.5 × ATR). Target sejauh itu wajar
menurunkan win rate. Bila hasil backtest menunjukkan terlalu banyak trade
kedaluwarsa atau kena SL, coba `Metode Stop Loss` = `Entry ± ATR (ketat)`, yang
memperkecil Risk sehingga TP 1:2 berada jauh lebih dekat.

Angka breakeven win rate pada RR 1:2 adalah **33.3 %** sebelum biaya.
