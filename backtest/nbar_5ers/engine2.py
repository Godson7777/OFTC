import pandas as pd, numpy as np
from engine import load
def rma(x,n):
    out=np.full(len(x),np.nan); a=1/n; s=np.nanmean(x[1:n+1]); out[n]=s
    for i in range(n+1,len(x)): s=a*x[i]+(1-a)*s; out[i]=s
    return out
def indicators(d):
    H,L,C=d.HIGH.values,d.LOW.values,d.CLOSE.values
    pc=np.r_[np.nan,C[:-1]]; tr=np.nanmax(np.c_[H-L,abs(H-pc),abs(L-pc)],axis=1)
    atr14=rma(tr,14); atr10=rma(tr,10)
    # supertrend(3,10)
    hl2=(H+L)/2; up=hl2-3*atr10; dn=hl2+3*atr10; dirn=np.ones(len(C)); fu=up.copy(); fd=dn.copy()
    for i in range(1,len(C)):
        fu[i]=max(up[i],fu[i-1]) if C[i-1]>fu[i-1] else up[i]
        fd[i]=min(dn[i],fd[i-1]) if C[i-1]<fd[i-1] else dn[i]
        dirn[i]=-1 if (dirn[i-1]==1 and C[i]>fd[i-1]) else (1 if (dirn[i-1]==-1 and C[i]<fu[i-1]) else dirn[i-1])
    ma=(pd.Series(C).rolling(9).mean()+pd.Series(C).rolling(21).mean()).values/2
    return dict(atr=atr14,st_bull=dirn<0,st_bear=dirn>0,ma_bull=C>ma,ma_bear=C<ma)
def trades(d,ind,n=2,minpct=0,enhanced=True,mode='close',filt='none',rr=2.0,flip=False,minsl_atr=0.0,buf_atr=0.0):
    """Returns list of trades in R units. mode 'close': signal on bar close -> market at next open.
    mode 'stop': buy-stop at pivot high / sell-stop at pivot low placed before bar opens (no look-ahead)."""
    O,H,L,C=d.OPEN.values,d.HIGH.values,d.LOW.values,d.CLOSE.values; sp=d.SPREAD.values*0.01
    atr=ind['atr']; N=len(C)
    dn_=(np.r_[np.nan,C[:-1]]>C).astype(float); up_=(np.r_[np.nan,C[:-1]]<C).astype(float)
    k=n-1
    # count of down/up closes among bars i-1..i-k (known before bar i opens)
    cd=pd.Series(dn_).rolling(k).sum().shift(1).values; cu=pd.Series(up_).rolling(k).sum().shift(1).values
    setdn=cd/k*100>=minpct; setup=cu/k*100>=minpct
    fb={'none':np.ones(N,bool),'st':ind['st_bull'],'ma':ind['ma_bull']}[filt]
    fs={'none':np.ones(N,bool),'st':ind['st_bear'],'ma':ind['ma_bear']}[filt]
    out=[]; pos=0; pend=0
    for i in range(n+20,N):
        a=atr[i-1]
        # ---- entries
        if pos==0 or flip:
            if mode=='close' and pend!=0:
                s=pend; pend=0
                if pos!=0: out.append((ts,pos,((O[i]-ep)*pos-sp[i]/2)/risk,'flip')); pos=0
                ep=O[i]+sp[i]/2*s; ext=sl_ref
                dist=max(abs(ep-ext)+buf_atr*a, minsl_atr*a, 0.05)
                pos=s; risk=dist; sl=ep-s*dist; tp=ep+s*dist*rr; ts=d.index[i]; fresh=True
            elif mode=='stop':
                ph=H[i-k]; pl=L[i-k]
                lb=setdn[i] and fb[i-1] and pos<=0 and H[i]>ph
                sb=setup[i] and fs[i-1] and pos>=0 and L[i]<pl
                if lb and sb:  # both touched: 4-tick path O->nearer extreme first
                    if (H[i]-O[i])<(O[i]-L[i]): sb=False
                    else: lb=False
                if lb or sb:
                    s=1 if lb else -1; trig=ph if lb else pl
                    fill=(max(trig,O[i]) if s>0 else min(trig,O[i]))+sp[i]/2*s
                    if pos!=0: out.append((ts,pos,((fill-ep)*pos)/risk,'flip')); pos=0
                    ep=fill; ext=(L[i-k:i].min() if s>0 else H[i-k:i].max())
                    dist=max(abs(ep-ext)+buf_atr*a, minsl_atr*a, 0.05)
                    pos=s; risk=dist; sl=ep-s*dist; tp=ep+s*dist*rr; ts=d.index[i]; fresh=True
        # ---- exits (SL first if both touched)
        if pos!=0:
            if (pos>0 and L[i]<=sl) or (pos<0 and H[i]>=sl):
                px=sl if not ((pos>0 and O[i]<sl) or (pos<0 and O[i]>sl)) or fresh else O[i]
                out.append((ts,pos,((px-ep)*pos)/risk,'SL')); pos=0
            elif (pos>0 and H[i]>=tp) or (pos<0 and L[i]<=tp):
                out.append((ts,pos,rr,'TP')); pos=0
            fresh=False
        # ---- bar-close signals (mode close)
        if mode=='close':
            if pos==0 or flip:
                lc=setdn[i] and H[i]>H[i-k] and (C[i]>C[i-k] or not enhanced) and fb[i]
                sc=setup[i] and L[i]<L[i-k] and (C[i]<C[i-k] or not enhanced) and fs[i]
                if lc and pos<=0: pend=1; sl_ref=L[i-k:i+1].min()
                elif sc and pos>=0: pend=-1; sl_ref=H[i-k:i+1].max()
    return pd.DataFrame(out,columns=['t','side','R','why']).set_index('t')
def rstats(t):
    w=t.R[t.R>0].sum(); l=-t.R[t.R<=0].sum(); eq=t.R.cumsum(); dd=(eq.cummax()-eq).max()
    return dict(n=len(t),win=round((t.R>0).mean()*100,1),avgR=round(t.R.mean(),3),pf=round(w/l,2) if l else 0,totR=round(t.R.sum(),1),maxddR=round(dd,1))
