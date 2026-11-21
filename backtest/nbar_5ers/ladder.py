from engine2 import *
import warnings; warnings.filterwarnings('ignore')
d=load(); ind=indicators(d); rng=np.random.default_rng(7)
LEVELS=[250e3,500e3,1e6,2e6,4e6]
def climb(R,start,risk_mode):
    """risk_mode 'pct': risk 0.2% of current level (=$500 on 250k). 'fixed': always $500."""
    j=start; lvl=0; ntr=0
    while lvl<4:
        bal=LEVELS[lvl]; risk=bal*0.002 if risk_mode=='pct' else 500
        e=0
        while True:
            if j>=len(R): return lvl,'data habis',ntr
            e+=R[j]*risk; j+=1; ntr+=1
            if e<=-0.04*bal: return lvl,'gagal',ntr
            if e>=0.05*bal: lvl+=1; break
    return 4,'SAMPAI 4JT',ntr
cfgs={'Settinganmu (N2,0%,none)':dict(mode='close',n=2,minpct=0,filt='none'),
      'C stop,N5':dict(mode='stop',n=5,minpct=0,filt='none'),
      'D close,N4,MA':dict(mode='close',n=4,minpct=0,filt='ma'),
      'B stop,N7,ST':dict(mode='stop',n=7,minpct=0,filt='st'),
      'A close,N4,80%,ST':dict(mode='close',n=4,minpct=80,filt='st',minsl_atr=1.0)}
for name,kw in cfgs.items():
    t=trades(d,ind,**kw); R=t.R.values; tpm=len(t)/142
    print(f"\n== {name}: {len(t)} trade, {tpm:.1f}/bulan, avgR {R.mean():+.3f}")
    # historical rolling starts
    starts=[t.index.searchsorted(m) for m in pd.date_range('2015-03-01','2024-01-01',freq='MS')]
    h=[climb(R,s,'pct') for s in starts]
    lv=pd.Series([x[0] for x in h]).value_counts().sort_index()
    print('  Historis (mulai tiap bulan 2015-2023), level tertinggi tercapai:',
          {f"{int(LEVELS[k]/1e3)}k":int(v) for k,v in lv.items()}, ' dari',len(h))
    # bootstrap: resample months of trades (keeps streak clustering), long horizon
    months=[g.R.values for _,g in t.groupby(t.index.to_period('M'))]
    for mode in ['pct','fixed']:
        res=[]
        for _ in range(4000):
            seq=np.concatenate([months[i] for i in rng.integers(0,len(months),600)])
            res.append(climb(seq,0,mode))
        lv=np.array([r[0] for r in res]); won=lv==4
        yrs=np.array([r[2] for r in res])[won]/tpm/12
        p_lvl=[(lv>k).mean()/max((lv>=k).mean(),1e-9) for k in range(4)]
        print(f"  Monte Carlo risk {'0.2% (naik ikut akun)' if mode=='pct' else '$500 tetap'}: P(sampai 4jt)={won.mean()*100:.1f}%"
              f" | peluang lolos tiap level {[round(p*100) for p in p_lvl]}%"
              f" | median waktu jika sukses {np.median(yrs) if won.any() else float('nan'):.1f} th")
