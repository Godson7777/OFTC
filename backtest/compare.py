import engine
from dataclasses import replace

CSV = '/root/.claude/uploads/531b72a7-242d-5297-9bd1-d07ca8f87be4/018f30b3-XAUUSD_H1.csv'
bars = engine.load(CSV)
base = engine.Config()

variants = [
    ('BASELINE (default script)',        {}),
    ('-- biaya --',                       None),
    ('Tanpa komisi & slippage',          dict(commission_pct=0.0, slippage=0.0)),
    ('-- Take Profit --',                 None),
    ('TP Fibo 0.27 (SOP), minRR=0',      dict(tp_mode='fib', min_rr=0.0)),
    ('TP RR 1.5',                        dict(rr_target=1.5, min_rr=1.5)),
    ('TP RR 3.0',                        dict(rr_target=3.0, min_rr=3.0)),
    ('TP Terjauh (RR2 vs Fibo)',         dict(tp_mode='farthest')),
    ('-- Stop Loss --',                   None),
    ('SL ketat (Entry +/- 0.5 ATR)',     dict(sl_mode='tight')),
    ('SL ketat + RR 3',                  dict(sl_mode='tight', rr_target=3.0, min_rr=3.0)),
    ('SL buffer 1.0 ATR',                dict(sl_atr=1.0)),
    ('-- Entry --',                       None),
    ('Entry Fibo 0.5',                   dict(fib_entry=0.5)),
    ('Entry Fibo 0.0 (market di high)',  dict(fib_entry=0.0)),
    ('-- Filter dilonggarkan --',         None),
    ('Tanpa filter volume',              dict(use_vol=False)),
    ('Vol_Multiplier 1.2',               dict(vol_mult=1.2)),
    ('Wick_Max 0.20',                    dict(wick_max=0.20)),
    ('Body_Min 0.60',                    dict(body_min=0.60)),
    ('Size_Multiplier 1.2',              dict(size_mult=1.2)),
    ('Tanpa filter EMA',                 dict(use_ema=False)),
    ('SEMUA dilonggarkan',               dict(use_vol=False, wick_max=0.20, body_min=0.60, size_mult=1.2)),
    ('-- Arah & kedaluwarsa --',          None),
    ('Hanya LONG',                       dict(direction='long')),
    ('Hanya SHORT',                      dict(direction='short')),
    ('Exp_Candles 10',                   dict(exp_bars=10)),
    ('Exp_Candles 3',                    dict(exp_bars=3)),
    ('-- ATR --',                         None),
    ('ATR True Range (ta.atr)',          dict(atr_mode='truerange')),
]

hdr = f"{'Varian':<34}{'Trd':>5}{'Win%':>7}{'PF':>7}{'Net$':>10}{'Ret%':>8}{'MaxDD%':>8}{'avgR':>7}{'Streak':>7}"
print(hdr); print('=' * len(hdr))
for name, over in variants:
    if over is None:
        print(f'\n{name}')
        continue
    cfg = replace(base, **over)
    m = engine.metrics(engine.run(bars, cfg), cfg)
    if m['trades'] == 0:
        print(f'{name:<34}{"0":>5}{"-":>7}{"-":>7}{"-":>10}{"-":>8}{"-":>8}{"-":>7}{"-":>7}')
        continue
    pf = 'inf' if m['profit_factor'] == float('inf') else f"{m['profit_factor']:.2f}"
    print(f"{name:<34}{m['trades']:>5}{m['win_rate']*100:>7.1f}{pf:>7}"
          f"{m['net']:>10.0f}{m['return_pct']:>8.1f}{m['max_dd_pct']:>8.1f}"
          f"{m['avg_r']:>7.2f}{m['worst_streak']:>7}")
