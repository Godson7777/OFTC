import pandas as pd, numpy as np
F="/root/.claude/uploads/9e77afca-e137-59cc-854a-90daae465dd9/7b295ea6-XAUUSD_H1_201501020900_202611091700.csv"
def load():
    d=pd.read_csv(F,sep='\t'); d.columns=[c.strip('<>') for c in d.columns]
    d['dt']=pd.to_datetime(d.DATE+' '+d.TIME,format='%Y.%m.%d %H:%M:%S')
    return d.set_index('dt')[['OPEN','HIGH','LOW','CLOSE','SPREAD']]
def signals(d):
    h,l,c=d.HIGH,d.LOW,d.CLOSE
    lo=(h>h.shift(1))&(c>c.shift(1)); sh=(l<l.shift(1))&(c<c.shift(1))
    return lo.values, sh.values
def run(d, sl_pct=10.0, rr=2.0, sizer=None, comm_per_unit=0.0, use_spread=True, slip=0.0):
    """On-bar-close: signal at close of bar i -> fill at open of bar i+1.
    SL/TP checked intrabar from the fill bar; if both hit in one bar, SL first (worst case).
    sizer(equity, entry, stop_dist) -> qty"""
    O,H,L,C=d.OPEN.values,d.HIGH.values,d.LOW.values,d.CLOSE.values
    sp=d.SPREAD.values*0.01 if use_spread else np.zeros(len(d))
    lo,sh=signals(d); idx=d.index
    eq=0.0; pos=0; qty=0; ep=0; sl=tp=0; trades=[]; pend=0
    def close(i,px,why):
        nonlocal pos,qty,eq
        pnl=(px-ep)*pos*qty - comm_per_unit*qty
        eq+=pnl; trades.append((idx[i],pos,ep,px,qty,pnl,why)); pos=0
    for i in range(1,len(d)):
        if pend!=0:
            if pos!=0: close(i,O[i]-slip*pos,'flip')
            pos=pend; cost=sp[i]/2+slip
            ep=O[i]+cost*pos; dist=ep*sl_pct/100
            qty=sizer(eq,ep,dist) if sizer else 2
            eq-=comm_per_unit*qty
            sl=ep-pos*dist; tp=ep+pos*dist*rr; pend=0
        if pos!=0:
            if pos>0:
                if L[i]<=sl: close(i,min(sl,O[i]),'SL')
                elif H[i]>=tp: close(i,max(tp,O[i]) if O[i]>=tp else tp,'TP')
            else:
                if H[i]>=sl: close(i,max(sl,O[i]),'SL')
                elif L[i]<=tp: close(i,tp if O[i]>tp else O[i],'TP')
        if lo[i] and pos<=0: pend=1
        elif sh[i] and pos>=0: pend=-1
    if pos!=0: close(len(d)-1,C[-1],'end')
    return pd.DataFrame(trades,columns=['t','side','entry','exit','qty','pnl','why']).set_index('t')
def stats(t,cap=10000):
    w=t.pnl[t.pnl>0]; l=t.pnl[t.pnl<=0]
    eqc=cap+t.pnl.cumsum(); dd=(eqc.cummax()-eqc).max()
    return dict(trades=len(t),net=round(t.pnl.sum(),0),ret_pct=round(t.pnl.sum()/cap*100,1),win=round(len(w)/len(t)*100,1),
                pf=round(w.sum()/-l.sum(),2),maxdd=round(dd,0),why=t.why.value_counts().to_dict())
