from engine2 import *
import warnings; warnings.filterwarnings('ignore')
d=load(); ind=indicators(d)
def step(R,ts,start,risk,target,maxloss):
    e=0.0
    for j in range(start,len(R)):
        e+=R[j]*risk
        if e<=-maxloss: return 'fail',j
        if e>=target: return 'pass',j
    return 'open',len(R)-1
def boot(t,risk):
    R=t.R.values; ts=t.index; res=[]
    for m in pd.date_range('2015-03-01','2025-11-01',freq='MS'):
        s=ts.searchsorted(m); log=[]; j=s
        for tg,ml in [(6,5)]*3+[(5,4)]:
            if j>=len(R): log.append(('open',0)); break
            r,e=step(R,ts,j,risk,tg,ml); log.append((r,(ts[e]-ts[j]).days)); j=e+1
            if r!='pass': break
        res.append(log)
    n=len(res); P=lambda k: sum(1 for r in res if len(r)>=k and r[k-1][0]=='pass')
    tdays=[sum(x[1] for x in r) for r in res if len(r)==4 and r[3][0]=='pass']
    return f"S1 {P(1)/n*100:3.0f}% | S2 {P(2)/n*100:3.0f}% | S3 {P(3)/n*100:3.0f}% | funded+5% {P(4)/n*100:3.0f}% | median hari s/d payout {np.median(tdays) if tdays else float('nan'):.0f}"
cfgs={'Settinganmu (close,N2,0%,none)':dict(mode='close',n=2,minpct=0,filt='none'),
      'A close,N4,80%,Supertrend,minSL 1ATR':dict(mode='close',n=4,minpct=80,filt='st',minsl_atr=1.0),
      'B stop,N7,0%,Supertrend':dict(mode='stop',n=7,minpct=0,filt='st'),
      'C stop,N5,0%,none':dict(mode='stop',n=5,minpct=0,filt='none'),
      'D close,N4,0%,MA cloud':dict(mode='close',n=4,minpct=0,filt='ma')}
for name,kw in cfgs.items():
    t=trades(d,ind,**kw); print(name, rstats(t), 'trades/bulan %.1f'%(len(t)/142))
    for risk in [0.25,0.5,1.0]:
        print(f"   risk {risk}%: "+boot(t,risk))
    yr=t.R.groupby(t.index.year).sum().round(1); print('   R per tahun:',dict(yr))
