import itertools, time, numpy as np, pandas as pd, multiprocessing as mp
from core import load, simulate
from features import Feat, build
from metrics import metrics
LENS=[55,83,120,150,200,250,300,400]; SLS=[('atr',0.5),('atr',0.75),('atr',1.0),('atr',1.25),('atr',1.5)]
EXITS=[('rr',x) for x in (1.5,2,2.5,3,3.5,4,5)]+[('trail',10),('trail',20),('mid',0)]
TR=['none','ema','d1']; SS=['all','08-21','14-21']; VO=['all','hi']
F=None
def init():
    global F; F=Feat(load())
def job(L):
    out=[]
    for sl,ex,tr,ss,vo in itertools.product(SLS,EXITS,TR,SS,VO):
        a=build(F,'brk_stop',L,sl,ex,tr,ss,vo)
        for pess in (False,True):
            t=simulate(F.O,F.H,F.L,F.C,F.SP,*a[:8],a[8],False,0,0.05,0.07,pess)
            m=metrics(t,F.d.index)
            if m: out.append(dict(entry='brk_stop',f=0.5,L=L,sl=f'{sl[0]}{sl[1]}',exit=f'{ex[0]}{ex[1]}',trend=tr,sess=ss,vol=vo,rev=False,pess=pess,**m))
    return out
if __name__=='__main__':
    t0=time.time()
    with mp.Pool(4,initializer=init) as p: res=p.map(job,LENS)
    g=pd.DataFrame([r for x in res for r in x]); g.to_csv('grid2.csv.gz',index=False); print(len(g),'in',round(time.time()-t0),'s')
