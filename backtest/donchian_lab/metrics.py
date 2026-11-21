import numpy as np, pandas as pd
SPLIT = pd.Timestamp('2023-01-01')
def metrics(t, idx):
    """t: trades array from core.simulate; idx: DatetimeIndex of bars."""
    if len(t) < 30:
        return None
    R = t[:, 3]; te = idx[t[:, 0].astype(int)]; tx = idx[t[:, 1].astype(int)]
    yrs = (idx[-1] - idx[0]).days / 365.25
    m = pd.Series(R, index=tx).resample('MS').sum()
    m = m.reindex(pd.date_range(idx[0].to_period('M').to_timestamp(), idx[-1], freq='MS'), fill_value=0.0)
    cum = np.cumsum(R); dd = (np.maximum.accumulate(cum) - cum).max()
    isn = te < SPLIT
    def part(mask, mm):
        r = R[mask]
        if len(r) < 15: return np.nan, np.nan, np.nan
        pf = r[r > 0].sum() / max(-r[r < 0].sum(), 1e-9)
        sh = mm.mean() / mm.std() if mm.std() > 0 else np.nan
        return r.mean(), pf, sh
    mi, mo = m[m.index < SPLIT], m[m.index >= SPLIT]
    ia, ipf, ish = part(isn, mi); oa, opf, osh = part(~isn, mo)
    yr = pd.Series(R, index=tx).groupby(tx.year).sum()
    return dict(n_yr=len(R) / yrs, win=(R > 0).mean() * 100, avgR=R.mean(),
                pf=R[R > 0].sum() / max(-R[R < 0].sum(), 1e-9), R_yr=R.sum() / yrs, ddR=dd,
                m_mean=m.mean(), m_std=m.std(), m_pos=(m > 0).mean() * 100,
                is_avgR=ia, is_pf=ipf, is_sh=ish, oos_avgR=oa, oos_pf=opf, oos_sh=osh,
                yrs_pos=int((yr > 0).sum()), yrs_tot=len(yr))
