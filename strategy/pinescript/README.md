# N-Bar Reversal Strategy (FIXED) — XAUUSD H1

Settingan tetap (fixed) yang menghasilkan backtest TradingView di
`backtests/2026-11-21_xauusd_h1_tradingview.md`. Jangan diubah tanpa mencatat
versi baru — settingan ini adalah baseline untuk validasi engine backtest.

## Symbol & Timeframe
- Pair: **XAUUSD only**
- Timeframe: **H1 only**

## 1. Pattern
| Input | Value |
|---|---|
| N Value | 2 |
| Min Percentage | 0 |
| Pattern Type | Enhanced |
| Accuracy Mode | Standard |
| Use Volume Confirmation | false |
| Volume confirm hanya di mode High | true |

## 2. Trend Filter
| Input | Value |
|---|---|
| Use Trend Filter | true |
| Trend Filter Type | Donchian Channels |
| Filter Mode | With Trend |
| Fast MA Length | 9 |
| Slow MA Length | 21 |
| Supertrend Period | 10 |
| Supertrend Multiplier | 3 |
| Donchian Length | 83 |
| RSI Length | 14 |
| RSI Filter Logic | Directional (50 line) |
| RSI Oversold (legacy, unused) | 30 |
| RSI Overbought (legacy, unused) | 70 |

## 3. Risk Management
| Input | Value |
|---|---|
| Use Stop Loss | true |
| Stop Loss % | 1 |
| Use Take Profit | true |
| Take Profit Source | From R:R Ratio |
| Risk/Reward Ratio | 2.5 |
| Fixed Take Profit % (unused, source = R:R) | 2.5 |
| Reverse on Opposite Signal | true |

## 4. Position Sizing
| Input | Value |
|---|---|
| Risk-based sizing | true |
| Risk per Trade % | 1 |

## 5. Visual
| Input | Value |
|---|---|
| Show Entry Signals | true |
| Show Dynamic S/R Lines | true |
| Max S/R Lines | 10 |

## Strategy properties (dari header script)
- initial_capital = 10000 (catatan: hasil backtest acuan memakai 100,000 USD — lihat `backtests/`)
- commission_type = percent, commission_value = 0.02%
- slippage = 3
- pyramiding = 0
- calc_on_every_tick = false
- process_orders_on_close = false

## Tujuan jangka panjang
Settingan di atas (H1, fixed) BUKAN target optimasi — ini baseline validasi.
Misi sebenarnya: membangun engine backtest custom yang mereplikasi persis
mesin backtest MT5, lalu memvalidasi engine itu dengan mencocokkan hasilnya
terhadap backtest Pine Script ini (trade-by-trade, bukan cuma summary).
Setelah engine tervalidasi, baru dipakai untuk mencari parameter Donchian +
R:R (minimal 1:2) yang optimal di timeframe lebih kecil dari H1.
