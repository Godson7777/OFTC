# Backtest Reference — TradingView — XAUUSD H1

Source: TradingView Strategy Tester, script `strategy/pinescript/n_bar_reversal_fixed.pine`
dengan settingan di `strategy/pinescript/README.md`.

- Symbol: XAUUSD
- Timeframe: H1
- Period: Jan 2, 2025 – Sep 12, 2026
- Initial capital: 100,000 USD
- Detalization: Default detalization
- Script execution: 1 (bar-close, `calc_on_every_tick=false`)

Catatan: ini adalah **angka target** untuk validasi engine backtest custom
(lihat tujuan di `strategy/pinescript/README.md`). Engine custom harus bisa
mereproduksi angka-angka ini (idealnya trade-by-trade, bukan cuma ringkasan)
sebelum dipakai untuk eksplorasi parameter/timeframe lain.

## Key stats
| Metric | Value |
|---|---|
| Total PnL | +94,298.54 USD (+94.30%) |
| Max Drawdown | 11,998.90 USD (9.47%) |
| Profitable trades | 43.54% (64/147) |
| Profit Factor | 1.737 |

## Breakdown
| Metric | Value |
|---|---|
| Gross profit | 222,249.92 USD (+222.25%) |
| Gross loss | 127,951.37 USD (127.95%) |
| Commission load | (locked/unavailable in UI) |
| Long PnL | +55,128.30 USD |
| Short PnL | +39,170.25 USD |

## Trades analysis — Distribution
| Metric | Value |
|---|---|
| Expectancy | 641.49 USD (0.47%) |
| Outliers PnL | 0 USD (0.00%) |
| Largest profit | (locked in UI) |
| Largest loss | (locked in UI) |
| Average loss | -1.01% |
| Average profit | +2.39% |
| Total trades | 147 |
| Winners | 64 (43.54%) |
| Losers | 83 (56.46%) |
| Breakevens | 0 (0.00%) |

## Periodical
| Metric | Value |
|---|---|
| Annualized return (CAGR) | +48.05% |
| Total return | +94.30% |
| Sharpe ratio | (locked in UI) |
| Sortino ratio | (locked in UI) |

### Quarterly PnL (approx, dari chart)
| Quarter | Realized PnL |
|---|---|
| Q1 '25 | positive (~+8-10K, net dari chart) |
| Q2 '25 | positive (~+10K) |
| Q3 '25 | negative (~-5K) |
| Q4 '25 | positive (~+10K) |
| Q1 '26 | positive, largest (~+42-44K) |
| Q2 '26 | slightly positive (~+2-4K net, ada adverse excursion besar) |
| Q3 '26 | negative (~-5 to -8K) |

> Catatan: nilai quarterly di atas dibaca dari chart (approximate), bukan angka
> presisi dari tabel — kalau butuh presisi, export ulang ke CSV dari tab
> "Periodical" TradingView.

## Benchmarking
| Metric | Value |
|---|---|
| Strategy return | +94.30% |
| Buy and hold return | +62.80% |
| Strategy outperformance | +31.50% |
| Correlation | (locked in UI) |

## Data yang masih diperlukan untuk validasi engine (lihat permintaan sebelumnya)
1. **List of Trades** (export CSV dari TradingView Strategy Tester → "List of trades") — WAJIB, untuk validasi trade-by-trade.
2. **Data OHLC historis XAUUSD H1** periode Jan 2, 2025 – Sep 12, 2026 (dari TradingView export atau MT5 History Center) — WAJIB.
3. Data M1 periode yang sama — opsional, untuk presisi intrabar fill (SL vs TP dalam bar yang sama).
4. Spesifikasi symbol XAUUSD di broker MT5 (contract size, point value, spread, commission per lot, swap) — untuk tahap live/forward test.

File-file ini belum diupload ke repo — akan ditambahkan begitu tersedia.
