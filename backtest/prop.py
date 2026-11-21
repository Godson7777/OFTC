from engine import *
d=load(); O,H,L,C=d.OPEN.values,d.HIGH.values,d.LOW.values,d.CLOSE.values
sp=d.SPREAD.values*0.01; lo,sh=signals(d); days=d.index.normalize().values
def account(start,bal,target,maxloss,risk_pct,sl_pct,rr=2.0,daily_pause=None,comm=0.0,lev=30):
    """returns ('pass'|'fail'|'open', end_index). maxloss static from start balance; equity incl. floating (worst intrabar)."""
    eq=bal; pos=0; pend=0; floor=bal*(1-maxloss/100); goal=bal*(1+target/100)
    day=None; dstart=bal; paused=False
    for i in range(start,len(d)):
        if days[i]!=day: day=days[i]; dstart=eq; paused=False
        if pend!=0 and not paused:
            if pos!=0: eq+=(O[i]-ep)*pos*q-comm*q; pos=0
            pos=pend; ep=O[i]+sp[i]/2*pos; dist=ep*sl_pct/100
            q=min(bal*risk_pct/100/dist, eq*lev/ep); eq-=comm*q
            sl=ep-pos*dist; tp=ep+pos*dist*rr
        pend=0
        if pos!=0:
            worst=L[i] if pos>0 else H[i]
            if eq+(worst-ep)*pos*q<=floor: return 'fail',i
            if daily_pause and eq+(worst-ep)*pos*q<=dstart*(1-daily_pause/100):
                px=dstart*(1-daily_pause/100); eq=px; pos=0; paused=True; continue
            hit=None
            if (pos>0 and L[i]<=sl) or (pos<0 and H[i]>=sl): hit=sl
            elif (pos>0 and H[i]>=tp) or (pos<0 and L[i]<=tp): hit=tp
            if hit is not None: eq+=(hit-ep)*pos*q-comm*q; pos=0
        if pos!=0 and eq+(C[i]-ep)*pos*q>=goal: return 'pass',i
        if pos==0 and eq>=goal: return 'pass',i
        if not paused:
            if lo[i] and pos<=0: pend=1
            elif sh[i] and pos>=0: pend=-1
    return 'open',len(d)-1
def bootcamp(start,**kw):
    i=start; log=[]
    for step,(bal,tg,ml,dp) in enumerate([(100000,6,5,None)]*3+[(250000,5,4,3)],1):
        r,j=account(i,bal,tg,ml,daily_pause=dp,**kw)
        log.append((step,r,(d.index[j]-d.index[i]).days)); i=j+1
        if r!='pass': break
    return log
if __name__=='__main__':
    starts=[d.index.get_indexer([t],method='bfill')[0] for t in pd.date_range('2015-02-01','2025-11-01',freq='MS')]
    for risk,sl in [(2,10),(2,1),(1,1),(2,0.5)]:
        res=[bootcamp(s,risk_pct=risk,sl_pct=sl) for s in starts]
        n=len(res); reach=lambda k: sum(1 for r in res if len(r)>=k and r[k-1][1]=='pass')
        failstep=pd.Series([r[-1][0] for r in res if r[-1][1]=='fail']).value_counts().sort_index().to_dict()
        open_=sum(1 for r in res if r[-1][1]=='open')
        days_s1=np.median([r[0][2] for r in res])
        print(f"risk {risk}%/trade, SL {sl}%: lulus step1 {reach(1)}/{n}, step2 {reach(2)}, step3 {reach(3)}, funded +5% {reach(4)} | gagal di step {failstep}, belum selesai {open_} | median hari step1 {days_s1:.0f}")
