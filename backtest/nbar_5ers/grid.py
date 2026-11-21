from engine2 import *
import itertools, warnings; warnings.filterwarnings('ignore')
d=load(); ind=indicators(d)
rows=[]
for mode,n,mp,filt,minsl in itertools.product(['close','stop'],[2,3,4,5,7],[0,60,80],['none','st','ma'],[0,0.5,1.0]):
    t=trades(d,ind,n=n,minpct=mp,mode=mode,filt=filt,minsl_atr=minsl)
    if len(t)<200: continue
    a=t[:'2022']; b=t['2023':]
    rows.append(dict(mode=mode,n=n,minpct=mp,filt=filt,minsl=minsl,**{'all_'+k:v for k,v in rstats(t).items()},
                     is_pf=rstats(a)['pf'],oos_pf=rstats(b)['pf'],oos_avgR=rstats(b)['avgR']))
g=pd.DataFrame(rows); g.to_csv('grid.csv',index=False)
pd.set_option('display.width',250)
print(g.sort_values('all_avgR',ascending=False).head(20).to_string(index=False))
print(); print('user setting (close,n2,0%,none,minsl0):'); print(g[(g['mode']=='close')&(g.n==2)&(g.minpct==0)&(g.filt=='none')].to_string(index=False))
print(); print('stop, n2, 0%, none:'); print(g[(g['mode']=='stop')&(g.n==2)&(g.minpct==0)&(g.filt=='none')].to_string(index=False))
