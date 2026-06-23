import pcbnew, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle, Circle, FancyArrow
b=pcbnew.LoadBoard('hardware/weapon-hat.kicad_pcb'); OX,OY=150.0,120.0
def xy(f): p=f.GetPosition(); return p.x/1e6-OX, OY-p.y/1e6
def padnet(f):
    d={}
    for p in f.Pads():
        d[p.GetName()]=(p.GetNetname().lstrip('/'), p.GetPosition().x/1e6-OX, OY-p.GetPosition().y/1e6)
    return d
fps={f.GetReference():f for f in b.GetFootprints()}; val={r:fps[r].GetValue() for r in fps}
def isjst(r): return str(fps[r].GetFPID().GetLibItemName()).startswith('JST')
RAIL={'+5V':'#e8451f','VBAT':'#c01010','VBAT_IN':'#c01010','VBAT_F':'#c01010','+3V3':'#1769d6','GND':'#111'}
def col(n): return RAIL.get(n,'#16a34a' if n else '#666')
def short(n): return {'I2C_SDA':'SDA','I2C_SCL':'SCL','IMU_INT':'INT1','IMU2_INT':'INT2','IMU3_INT':'INT3',
  'RECOIL_PWM':'R_PWM','RECOIL_FAULT':'R_FLT','nCS':'CS','VBAT_IN':'VBAT','EMIT_HI':'EMIT_HI'}.get(n,n or '—')
mono=lambda s,w='normal': fm.FontProperties(family='monospace',size=s,weight=w)
FUNC={'2S batteri':'BATTERI 2S','TRIGGER':'TRIGGER','RACK':'RACK','MAGREL':'MAG-REL','MAGWELL':'MAGWELL',
      'recoil':'RECOIL-DRV','NFC':'NFC (I²C)','optik':'→ OPTIK'}

fig=plt.figure(figsize=(19,12))
axb=fig.add_axes([0.015,0.05,0.55,0.9]); axt=fig.add_axes([0.585,0.0,0.41,1.0]); axt.axis('off')
BW,BH=28.0,20.5
axb.add_patch(Rectangle((-BW,-BH),2*BW,2*BH,fill=True,fc='#0b5d3b',ec='k',lw=2,zorder=0))
axb.text(0,BH+1.4,'STRILAS VAPEN-HAT — FRAMSIDA',ha='center',fontsize=15,weight='bold')
axb.text(0,BH+0.4,'(komponenter uppåt; 40-pin HONA på baksidan, centrerad)',ha='center',fontsize=8.5,style='italic')
ICN={'AP63203':'BUCK 2S→5V','ICM-42688-P':'IMU','ADS1115':'ADC','AT24C32':'EEPROM','AOD4185':'REV-FET','OPA171':'—'}
for r,f in fps.items():
    if r=='J1' or r.startswith('MH'): continue
    x,y=xy(f); bb=f.GetBoundingBox(); w=min(bb.GetWidth()/1e6,9); h=min(bb.GetHeight()/1e6,9)
    if isjst(r):
        axb.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc='#f2c200',ec='#7a5b00',lw=1,zorder=2))
        name=next((FUNC[k] for k in FUNC if k in (val[r] or '')),'')
        ly = y+ (3.5 if y>0 else -3.5)
        axb.text(x,ly,name,ha='center',va='center',fontsize=7.5,weight='bold',color='#5a3d00',zorder=6,
                 bbox=dict(boxstyle='round,pad=0.15',fc='#fff3c0',ec='#7a5b00',lw=0.5))
        axb.plot([x,x],[y+ (h/2 if y>0 else -h/2), ly-(0.9 if y>0 else -0.9)],color='#7a5b00',lw=0.7,zorder=5)
        axb.text(x,y,r,ha='center',va='center',fontsize=5,zorder=3)
    else:
        axb.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc='#d7ded8',ec='#333',lw=0.6,zorder=2))
        tag=next((ICN[k] for k in ICN if k in (val[r] or '')),'')
        axb.text(x,y+0.0,r,ha='center',va='center',fontsize=5.5,zorder=3)
        if tag and tag!='—': axb.text(x,y-1.4,tag,ha='center',va='center',fontsize=4.8,color='#055',zorder=3)
# header pins
for k,(n,px,py) in padnet(fps['J1']).items():
    axb.add_patch(Circle((px,py),0.72,fc=col(n),ec='k',lw=0.4,zorder=4))
    axb.text(px,py,k,ha='center',va='center',fontsize=3.0,color='w',zorder=5)
axb.text(0,0,'40-PIN HONA\n→ CM5',ha='center',va='center',fontsize=7,weight='bold',color='w',
         bbox=dict(boxstyle='round',fc='#000',alpha=0.5),zorder=7)
# legend
lx,ly=-BW+1,-BH+1
for i,(lab,c) in enumerate([('VBAT','#c01010'),('+5V','#e8451f'),('+3V3','#1769d6'),('GND','#111'),('signal','#16a34a')]):
    axb.add_patch(Circle((lx+i*5.6,ly),0.7,fc=c,ec='k',lw=0.4)); axb.text(lx+i*5.6+0.9,ly,lab,fontsize=6.5,va='center')
axb.set_xlim(-BW-1,BW+1); axb.set_ylim(-BH-2,BH+2.5); axb.set_aspect('equal'); axb.axis('off')

# right tables
T=axt.text; y=0.995
T(0.5,y,'40-PIN HEADER  (CM5-carrier ↔ HAT)',fontsize=12,weight='bold',va='top',ha='center'); y-=0.03
pin={int(k):v[0] for k,v in padnet(fps['J1']).items()}
RPI={1:'3V3',2:'5V',3:'GPIO2',4:'5V',5:'GPIO3',6:'GND',7:'GPIO4',8:'GPIO14',9:'GND',10:'GPIO15',11:'GPIO17',
 12:'GPIO18',13:'GPIO27',14:'GND',15:'GPIO22',16:'GPIO23',17:'3V3',18:'GPIO24',19:'GPIO10',20:'GND',21:'GPIO9',
 22:'GPIO25',23:'GPIO11',24:'GPIO8',25:'GND',26:'GPIO7',27:'GPIO0',28:'GPIO1',29:'GPIO5',30:'GND',31:'GPIO6',
 32:'GPIO12',33:'GPIO13',34:'GND',35:'GPIO19',36:'GPIO16',37:'GPIO26',38:'GPIO20',39:'GND',40:'GPIO21'}
T(0.0,y,' pin  GPIO    funktion',fontproperties=mono(7.5,'bold'),va='top')
T(0.5,y,' pin  GPIO    funktion',fontproperties=mono(7.5,'bold'),va='top'); y-=0.02
for i in range(1,41,2):
    yy=y-0.0182*((i-1)//2)
    for p,xx in ((i,0.0),(i+1,0.5)):
        n=pin.get(p,'')
        T(xx,yy,f"{p:>2}  {RPI[p]:<6} {short(n)}",fontproperties=mono(7.2),va='top',color=col(n))
y-=0.0182*20+0.025
T(0.5,y,'JST-KONTAKTER  (på kant, kabel ut)',fontsize=11,weight='bold',va='top',ha='center'); y-=0.028
for r in sorted(fps):
    if not isjst(r): continue
    name=next((FUNC[k] for k in FUNC if k in (val[r] or '')),val[r][:12])
    d=padnet(fps[r]); ps='  '.join(f"{k}={short(d[k][0])}" for k in sorted(d,key=lambda z:int(z)))
    T(0.0,y,f"{r} {name}",fontproperties=mono(7.6,'bold'),va='top')
    T(0.30,y,ps,fontproperties=mono(7.0),va='top',color='#222'); y-=0.0205
y-=0.012
T(0.5,y,'KRAFT',fontsize=11,weight='bold',va='top',ha='center'); y-=0.026
for s in ["2S → JST-XH(J2) → PTC 4A → P-FET(omvänd-skydd) → VBAT",
          "VBAT → AP63203-buck → +5V → header pin2/4 (BACK-FEED → CM5)",
          "VBAT → emitter-JST(→optik 1A/3A) + recoil-JST",
          "+3V3 FRÅN carrier (pin1/17) → 3×IMU+ADC+EEPROM+pullups",
          "+5V → NFC (egen LDO). TVS: D1=VBAT, D2=5V. Allt SMT = framsida."]:
    T(0.0,y,'• '+s,fontproperties=mono(6.9),va='top'); y-=0.02
plt.savefig('leverans/renders/weapon-hat-pinout.png',dpi=150,bbox_inches='tight',facecolor='white')
print("wrote")
