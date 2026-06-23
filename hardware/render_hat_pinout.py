import pcbnew, matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from matplotlib.patches import Rectangle, Circle
b=pcbnew.LoadBoard('hardware/weapon-hat.kicad_pcb'); OX,OY=150.0,120.0
def xy(f): p=f.GetPosition(); return p.x/1e6-OX, OY-p.y/1e6
def pads(f):
    d={}
    for p in f.Pads(): d[p.GetName()]=(p.GetNetname().lstrip('/'), p.GetPosition().x/1e6-OX, OY-p.GetPosition().y/1e6)
    return d
fps={f.GetReference():f for f in b.GetFootprints()}; val={r:fps[r].GetValue() for r in fps}
def isjst(r): return str(fps[r].GetFPID().GetLibItemName()).startswith('JST')
RAIL={'+5V':'#e8451f','VBAT':'#c01010','VBAT_IN':'#c01010','+3V3':'#1769d6','GND':'#222'}
def col(n): return RAIL.get(n,'#138a3e' if n else '#9aa')
def fn(n):  # kort funktionsnamn
    return {'I2C_SDA':'SDA','I2C_SCL':'SCL','IMU_INT':'INT1','IMU2_INT':'INT2','IMU3_INT':'INT3',
      'RECOIL_PWM':'REC_PWM','RECOIL_FAULT':'REC_FLT','nCS':'CS','VBAT_IN':'VBAT','EMIT_HI':'EMIT_HI',
      '+5V':'5V','+3V3':'3V3','MOSI':'MOSI','MISO':'MISO','SCK':'SCK','IR_MOD':'IR_MOD','ID_SD':'ID_SD',
      'ID_SC':'ID_SC','MODE0':'MODE0','MODE1':'MODE1','PTT':'PTT','TRIG':'TRIG','RACK':'RACK',
      'MAGREL':'MAGREL','MAGWELL':'MAGWELL'}.get(n, n if n else 'NC')
RPI={1:'3V3',2:'5V',3:'GPIO2',4:'5V',5:'GPIO3',6:'GND',7:'GPIO4',8:'GPIO14',9:'GND',10:'GPIO15',11:'GPIO17',
 12:'GPIO18',13:'GPIO27',14:'GND',15:'GPIO22',16:'GPIO23',17:'3V3',18:'GPIO24',19:'GPIO10',20:'GND',21:'GPIO9',
 22:'GPIO25',23:'GPIO11',24:'GPIO8',25:'GND',26:'GPIO7',27:'GPIO0',28:'GPIO1',29:'GPIO5',30:'GND',31:'GPIO6',
 32:'GPIO12',33:'GPIO13',34:'GND',35:'GPIO19',36:'GPIO16',37:'GPIO26',38:'GPIO20',39:'GND',40:'GPIO21'}
mono=lambda s,w='normal': fm.FontProperties(family='monospace',size=s,weight=w)
FUNC={'2S batteri':'BATTERI 2S','TRIGGER':'TRIGGER','RACK':'RACK','MAGREL':'MAG-REL','MAGWELL':'MAGWELL',
      'recoil':'RECOIL','NFC':'NFC','optik':'→OPTIK'}

fig,ax=plt.subplots(figsize=(20,13)); BW,BH=28.0,20.5
ax.add_patch(Rectangle((-BW,-BH),2*BW,2*BH,fill=True,fc='#0c6342',ec='k',lw=2,zorder=0))
ax.text(0,BH+1.0,'STRILAS VAPEN-HAT — PINOUT (framsida)',ha='center',fontsize=17,weight='bold')

# ---- 40-pin header: pads + vertikal label per stift ----
jp=pads(fps['J1'])                      # {pin: (net,x,y)}
ys=sorted(set(round(v[2],1) for v in jp.values())); ytop=max(ys); ybot=min(ys)
for k,(n,px,py) in jp.items():
    p=int(k); ax.add_patch(Circle((px,py),0.95,fc=col(n),ec='k',lw=0.5,zorder=5))
    ax.text(px,py,str(p),ha='center',va='center',fontsize=5,color='w',weight='bold',zorder=6)
    top = py>0
    ty = py + (2.2 if top else -2.2)
    gpio=RPI[p]; ff=fn(n)
    lab=f"{p}  {gpio}" if (gpio==ff or ff=='NC') else f"{p}  {gpio} · {ff}"
    ax.text(px,ty,lab,ha='left' if top else 'right',va='center',rotation=90,
            fontproperties=mono(9.5,'bold'),color=col(n),zorder=6,
            rotation_mode='anchor')
ax.text(0, 0, '', zorder=4)
ax.text(-BW+0.5, ytop+0.2, 'J1  40-PIN HONA  → CM5-carrier  (på baksidan, centrerad)', fontsize=9,
        style='italic', va='bottom', color='#dff')

# ---- JST-kontakter: ram + funktionsnamn + per-pin ----
for r in sorted(fps):
    if not isjst(r): continue
    x,y=xy(f:=fps[r]); bb=f.GetBoundingBox(); w=min(bb.GetWidth()/1e6,9); h=min(bb.GetHeight()/1e6,9)
    ax.add_patch(Rectangle((x-w/2,y-h/2),w,h,fc='#f2c200',ec='#6b4e00',lw=1.2,zorder=3))
    name=next((FUNC[k] for k in FUNC if k in (val[r] or '')),r)
    d=pads(f); plist=[(k,d[k][0]) for k in sorted(d,key=lambda z:int(z))]
    top=y>0
    ly=y+(4.0 if top else -4.0)
    txt=f"{r} {name}\n"+"  ".join(f"{k}:{fn(n)}" for k,n in plist)
    ax.text(x,ly,txt,ha='center',va='center',fontsize=8,weight='bold',color='#3a2a00',zorder=7,
            bbox=dict(boxstyle='round,pad=0.3',fc='#fff6cf',ec='#6b4e00',lw=0.8))
    ax.plot([x,x],[y+(h/2 if top else -h/2), ly-(1.7 if top else -1.7)],color='#6b4e00',lw=0.9,zorder=4)

# legend
for i,(lab,c) in enumerate([('VBAT','#c01010'),('+5V','#e8451f'),('+3V3','#1769d6'),('GND','#222'),('signal','#138a3e'),('NC','#9aa')]):
    ax.add_patch(Circle((-BW+2+i*4.4,-BH-2.3),0.8,fc=c,ec='k',lw=0.4,clip_on=False))
    ax.text(-BW+2+i*4.4+0.9,-BH-2.3,lab,fontsize=8,va='center')
ax.set_xlim(-BW-1,BW+1); ax.set_ylim(-BH-3.5,BH+2); ax.set_aspect('equal'); ax.axis('off')
plt.savefig('leverans/renders/weapon-hat-pinout.png',dpi=150,bbox_inches='tight',facecolor='white')
print("wrote")
