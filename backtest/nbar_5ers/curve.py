from engine2 import *
import warnings; warnings.filterwarnings('ignore')
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt, matplotlib.dates as mdates
d=load(); ind=indicators(d)
LV=[250e3,500e3,1e6,2e6,4e6]
cfgs=[('C: stop order, N5','#2a78d6',dict(mode='stop',n=5,minpct=0,filt='none')),
      ('D: bar close, N4, MA Cloud','#eb6834',dict(mode='close',n=4,minpct=0,filt='ma')),
      ('Settinganmu (N2, 0%) + TP 2R','#1baf7a',dict(mode='close',n=2,minpct=0,filt='none'))]
fig,(a1,a2)=plt.subplots(2,1,figsize=(11,8.5),sharex=True,gridspec_kw=dict(height_ratios=[1.3,1]))
start=pd.Timestamp('2026-01-01')
for name,col,kw in cfgs:
    t=trades(d,ind,**kw)[start:]
    lvl=0; e=0.0; earned=0.0; xs=[start]; ys=[0.0]; ps=[0.0]; ups=[]; status='aktif'
    for ts,r in zip(t.index,t.R):
        bal=LV[lvl]; e+=r*bal*0.002
        xs.append(ts); ys.append(earned+e); ps.append(e/bal*100)
        if e<=-0.04*bal: status=f'GAGAL di {int(bal/1e3)}K ({ts:%d %b})'; break
        if e>=0.05*bal:
            earned+=e; ups.append((ts,earned,LV[lvl+1])); lvl+=1; e=0.0; ps.append(0.0); xs.append(ts); ys.append(earned)
            if lvl==4: status='SAMPAI 4JT'; break
    a1.plot(xs,ys,color=col,lw=2,label=f'{name}  —  {status}, akun sekarang {int(LV[lvl]/1e3)}K')
    for ts,v,nl in ups:
        a1.scatter([ts],[v],s=60,color=col,edgecolor='white',linewidth=2,zorder=5)
        a1.annotate(f'naik ke {int(nl/1e3)}K',(ts,v),textcoords='offset points',xytext=(6,8),fontsize=9,color='#52514e')
    a2.plot(xs,ps,color=col,lw=2)
    print(name,status,'| trade:',len(t),'| profit total $%.0f'%ys[-1],'| level:',int(LV[lvl]/1e3),'K | naik level:',[(f'{u[0]:%d %b}',int(u[2]/1e3)) for u in ups])
a1.axhline(0,color='#c3c2b7',lw=1)
a1.set_ylabel('Profit terkumpul (USD)'); a1.yaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda v,_: f'${v/1e3:,.0f}K'))
a1.set_title('Simulasi akun funded 5%ers $250K, risiko 0,2% dari akun, XAUUSD H1, 1 Jan – 9 Nov 2026',loc='left',fontsize=12,color='#0b0b0b')
a1.legend(loc='upper left',frameon=False,fontsize=9)
a2.axhline(5,color='#008300',lw=1,ls='--'); a2.text(xs[0],5.2,'target +5% → naik level',fontsize=9,color='#52514e')
a2.axhline(-4,color='#e34948',lw=1,ls='--'); a2.text(xs[0],-3.8,'max loss −4% → akun hangus',fontsize=9,color='#52514e')
a2.axhline(0,color='#c3c2b7',lw=1)
a2.set_ylabel('Posisi di level saat ini (%)'); a2.set_ylim(-5,6)
a2.xaxis.set_major_formatter(mdates.DateFormatter('%b'))
for a in (a1,a2):
    a.grid(axis='y',color='#ecebe8'); [a.spines[s].set_visible(False) for s in ('top','right')]
    a.tick_params(colors='#52514e')
fig.patch.set_facecolor('#fcfcfb'); [a.set_facecolor('#fcfcfb') for a in (a1,a2)]
plt.tight_layout(); plt.savefig('equity_2026.png',dpi=150)
