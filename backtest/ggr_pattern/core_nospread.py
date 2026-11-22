"""Same rules with zero trading costs: shows whether the pattern itself has an edge."""
import numpy as np, bt, rules_manual
bt.SP = np.zeros_like(bt.SP)
rules_manual.report(bt.run('normal', sl_mode='open_or_wick', buf=0.5, comm=0.0, slip=0.0), 'Normal, TANPA biaya ')
rules_manual.report(bt.run('pess', sl_mode='open_or_wick', buf=0.5, comm=0.0, slip=0.0), 'Pesimis, TANPA biaya')
