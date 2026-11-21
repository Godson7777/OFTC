import itertools, time, numpy as np, pandas as pd, multiprocessing as mp
from core import load, simulate
from features import Feat, build
from metrics import metrics
LENS=[10,20,30,55,83,120,200,300]
SLS=[('atr',1.5),('atr',2.0),('atr',2.5),('atr',3.0),('atr',4.0),('chan',10),('chan',20)]
EXITS=[('rr',x) for x in (1,1.5,2,3,4)]+[('trail',10),('trail',20),('mid',0)]
TR=['none','ema','d1']; SS=['all','08-21','14-21']; VO=['all','hi']; EN=['brk_stop','brk_close']
F=None
def init():
    global F; F=Feat(load())
def job(L):
    out=[]
    for en,sl,ex,tr,ss,vo in itertools.product(EN,SLS,EXITS,TR,SS,VO):
        a=build(F,en,L,sl,ex,tr,ss,vo)
        row=dict(entry=en,f=0.5,L=L,sl=f'{sl[0]}{sl[1]}',exit=f'{ex[0]}{ex[1]}',trend=tr,sess=ss,vol=vo,rev=False)
        res={}
        for pess in (False,True):
            t=simulate(F.O,F.H,F.L,F.C,F.SP,*a[:8],a[8],False,0,0.05,0.07,pess)
            m=metrics(t,F.d.index)
            if not m: break
            res.update({(k+('_P' if pess else '')):v for k,v in m.items()})
        if len(res)>20:
            same_bar=None
            out.append({**row,**res})
    return out
if __name__=='__main__':
    t0=time.time()
    with mp.Pool(4,initializer=init) as p: res=p.map(job,LENS)
    g=pd.DataFrame([r for x in res for r in x]); g.to_csv('grid3.csv.gz',index=False); print(len(g),'in',round(time.time()-t0),'s')
