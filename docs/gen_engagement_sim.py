#!/usr/bin/env python3
"""STRILAS — komplex engagemangssimulering som bevisar träffmodellen.
Producerar:
  docs/sim-precision.png   (sikt-moment, headshot-upplösning, Monte Carlo)
  docs/sim-fairness.png    (rörligt mål, flygtid, Fas1 vs Fas2-adjudikation, latens)
  docs/sim-engagement.gif  (top-down replay där allt hänger ihop)
Kör: python3 docs/gen_engagement_sim.py
"""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, Wedge, FancyArrow
from matplotlib.animation import FuncAnimation, PillowWriter
rng = np.random.default_rng(42)

# ---------------- BALLISTIK (M4 / 5.56) ----------------
g, v0, kd = 9.81, 880.0, 0.001277
def _traj(rmax=320, dt=1e-4):
    x=y=t=0.0; vx=v0; vy=0.0; X=[0];Y=[0];T=[0]
    while x<rmax:
        s=np.hypot(vx,vy); vx+=-kd*s*vx*dt; vy+=(-g-kd*s*vy)*dt
        x+=vx*dt; y+=vy*dt; t+=dt; X.append(x);Y.append(-y);T.append(t)
    return np.array(X),np.array(Y),np.array(T)
Xb,Yb,Tb=_traj()
TOF = lambda R: float(np.interp(R,Xb,Tb))
DROP= lambda R: float(np.interp(R,Xb,Yb))

# ---------------- MÅL-SILHUETT (zoner, framifrån) ----------------
# (namn, z_low, z_high, halvbredd[m], skademult, färg)
ZONES = [
    ("Huvud", 1.60, 1.80, 0.105, 3.0, "#ff5c5c"),
    ("Bröst", 1.25, 1.60, 0.24,  1.0, "#ffb000"),
    ("Mage",  0.95, 1.25, 0.20,  0.8, "#ffd35c"),
    ("Ben",   0.00, 0.95, 0.165, 0.5, "#4aa3ff"),
]
BODY_H = 1.80
def zone_of(z, y):
    for name,zl,zh,hw,mult,c in ZONES:
        if zl<=z<=zh and abs(y)<=hw: return name,mult,c
    return None,0.0,None

BEAM_HALF_DEG = 1.0                      # smal gevärsstråle
beam_r = lambda R: R*np.tan(np.radians(BEAM_HALF_DEG))

def shoot(R, aim_y, aim_z, sigma_deg):
    """Ett skott mot mål på avstånd R, sikte (aim_y,aim_z), spridning sigma."""
    off = R*np.tan(np.radians(rng.normal(0, sigma_deg, 2)))
    cy, cz = aim_y+off[0], aim_z+off[1]   # strålcentrum på målplanet
    r = beam_r(R)
    # träff på person? (stråldisk överlappar kropp)
    hit_y = abs(cy) <= 0.25 + r
    hit_z = -r <= cz <= BODY_H + r
    hit = hit_y and hit_z
    # exakt zon (Fas 2: server använder strålcentrum/siktvektor)
    z2,m2,c2 = zone_of(cz, cy)
    if hit and z2 is None:                # överlappar kropp men centrum utanför zon → närmaste
        z2 = min(ZONES, key=lambda Z: min(abs(cz-Z[1]),abs(cz-Z[2])))[0]
    # Fas 1: stråle+zon. Headshot bara om fläcken får plats på huvudet
    head_clean = (1.60<=cz<=1.80) and abs(cy)<=0.105 and r<0.13
    return dict(hit=hit, cy=cy, cz=cz, r=r, zone2=z2 if hit else None,
                head_f2=(z2=="Huvud" and hit), head_f1=(head_clean and hit))

# ============================================================
# FIGUR 1 — PRECISION / SIKT-MOMENT / HEADSHOT
# ============================================================
fig1, ax = plt.subplots(2,2, figsize=(16,11)); fig1.patch.set_facecolor("white")
fig1.suptitle("STRILAS — BEVIS 1: precision, sikt-moment & headshot-upplösning",
              fontsize=15, fontweight="bold")

# (A) Mål-silhuett med zoner + strålfläck @10m och @40m
a=ax[0,0]
for name,zl,zh,hw,mult,c in ZONES:
    a.add_patch(Rectangle((-hw,zl),2*hw,zh-zl,color=c,alpha=.55,ec="k",lw=.5))
    a.text(hw+0.04, (zl+zh)/2, f"{name} ×{mult}", va="center", fontsize=9)
for R,c,dx in [(10,"#1b7",0.0),(40,"#b30",0.0)]:
    a.add_patch(Circle((dx,1.45), beam_r(R), fill=False, ec=c, lw=2.2, ls="--"))
    a.text(dx, 1.45, f"±1° @{R}m\nØ{2*beam_r(R):.1f} m", color=c, ha="center", va="center", fontsize=8, fontweight="bold")
a.set_title("A. Strålfläck vs kroppszoner\n(nära = liten fläck → ren headshot · långt = täcker överkropp)", fontsize=10, fontweight="bold")
a.set_xlim(-1.6,1.6); a.set_ylim(-0.1,2.0); a.set_aspect("equal"); a.set_xlabel("sidled [m]"); a.set_ylabel("höjd [m]"); a.grid(alpha=.25)

# (B) Vinkelstorlek mål vs strålbredd → sikt-moment
b=ax[0,1]; Rr=np.linspace(3,60,200)
b.plot(Rr, np.degrees(2*np.arctan(0.25/Rr)), color="#ffb000", lw=2.2, label="0,5 m torso (vinkelbredd)")
b.plot(Rr, np.degrees(2*np.arctan(0.105/Rr)), color="#ff5c5c", lw=2.2, label="0,21 m huvud")
b.axhline(2*BEAM_HALF_DEG, color="#1b7", lw=2, ls="--", label="strålbredd ±1° (2° full)")
b.set_title("B. Sikt-momentet: du måste rikta inom målets vinkelstorlek", fontsize=10, fontweight="bold")
b.set_xlabel("avstånd [m]"); b.set_ylabel("vinkel [°]"); b.set_ylim(0,6); b.legend(fontsize=8); b.grid(alpha=.3)
b.annotate("torso ~1° @30 m → spray-and-pray missar", (30,1.0), (33,3.2),
           arrowprops=dict(arrowstyle="->",color="#888"), fontsize=8, color="#555")

# (C) Monte Carlo: P(träffa person) vs siktfel, per avstånd
c=ax[1,0]; sig=np.linspace(0,4,40); N=4000
for R,col in [(10,"#1b7"),(30,"#ffb000"),(50,"#b30")]:
    P=[np.mean([shoot(R,0,1.4,s)["hit"] for _ in range(N//40)]) for s in sig]
    c.plot(sig,P,color=col,lw=2.2,label=f"{R} m")
c.set_title("C. Skicklighet avgör: P(träff) vs siktfel\n(smal stråle → aim spelar roll)", fontsize=10, fontweight="bold")
c.set_xlabel("siktfel σ [°]"); c.set_ylabel("träffsannolikhet"); c.set_ylim(0,1.02); c.legend(title="avstånd",fontsize=8); c.grid(alpha=.3)

# (D) Headshot-upplösning: Fas1 (stråle+zon) vs Fas2 (server) vs avstånd
d=ax[1,1]; Rh=np.linspace(5,50,30); N2=2500; sigma_good=0.5
f1=[];f2=[]
for R in Rh:
    res=[shoot(R,0,1.70,sigma_good) for _ in range(N2)]
    hits=[r for r in res if r["hit"]]
    f1.append(np.mean([r["head_f1"] for r in hits]) if hits else 0)
    f2.append(np.mean([r["head_f2"] for r in hits]) if hits else 0)
d.plot(Rh,f1,color="#b30",lw=2.2,marker="s",ms=3,label="Fas 1: stråle+zon")
d.plot(Rh,f2,color="#1b7",lw=2.2,marker="o",ms=3,label="Fas 2: server-geometri")
d.axvline(7.4,color="#888",ls=":",lw=1); d.text(7.6,0.1,"Fas1-fläcken blir\nstörre än huvudet",fontsize=7,color="#555")
d.set_title("D. Headshot när du siktar på huvudet (σ=0,5°)\nFas2 bevarar precisionen på alla avstånd", fontsize=10, fontweight="bold")
d.set_xlabel("avstånd [m]"); d.set_ylabel("andel korrekta headshots"); d.set_ylim(0,1.02); d.legend(fontsize=8); d.grid(alpha=.3)

plt.tight_layout(rect=[0,0,1,0.96])
plt.savefig("/home/user/Strilas/docs/sim-precision.png", dpi=110, facecolor="white"); plt.close(fig1)

# ============================================================
# FIGUR 2 — FLYGTID, LEAD & NÄR BALLISTIKEN SPELAR ROLL (ärlig bild)
# ============================================================
fig2, ax = plt.subplots(2,2, figsize=(16,11)); fig2.patch.set_facecolor("white")
fig2.suptitle("STRILAS — BEVIS 2: flygtid, lead & när ballistiken faktiskt spelar roll",
              fontsize=15, fontweight="bold")
Rr=np.linspace(5,300,200); LED_MAX=75

# (A) Lead vs avstånd per målfart, med LED-band + strålradie som referens
a=ax[0,0]
a.axvspan(0,LED_MAX,color="#39d98a",alpha=.10)
a.text(LED_MAX/2,2.6,"LED-räckvidd\n(Fas 1-spel)",color="#1b7",ha="center",fontsize=9,fontweight="bold")
for vt,col in [(2,"#1b7"),(4,"#ffb000"),(6,"#b30")]:
    a.plot(Rr,[TOF(R)*vt for R in Rr],color=col,lw=2.2,label=f"mål {vt} m/s")
a.plot(Rr,[beam_r(R) for R in Rr],"--",color="#444",lw=2,label="strålradie ±1° (förlåtande zon)")
a.set_title("A. Lead vs avstånd: inom LED-räckvidd är lead < strålradien\n→ liten korrektion; ballistiken biter först på långt håll", fontsize=10, fontweight="bold")
a.set_xlabel("avstånd [m]"); a.set_ylabel("lead / radie [m]"); a.set_ylim(0,3); a.legend(fontsize=8); a.grid(alpha=.3)

# (B) "Måste du leda?" — lead / strålradie vs avstånd
b=ax[0,1]
for vt,col in [(2,"#1b7"),(4,"#ffb000"),(6,"#b30")]:
    b.plot(Rr,[TOF(R)*vt/beam_r(R) for R in Rr],color=col,lw=2.2,label=f"{vt} m/s")
b.axhline(1,color="#b30",ls="--",lw=1.5)
b.axvspan(0,LED_MAX,color="#39d98a",alpha=.10)
b.text(150,0.45,"strålen förlåter\n(lead < radie)",color="#1b7",fontsize=9)
b.text(150,2.4,"måste leda aktivt\n(lead > radie)",color="#b30",fontsize=9)
b.set_title("B. När måste du leda?  (lead ÷ strålradie)\nKvot >1 = ballistik/lead avgör; inom LED-räckvidd mest <1", fontsize=10, fontweight="bold")
b.set_xlabel("avstånd [m]"); b.set_ylabel("lead / strålradie"); b.set_ylim(0,3.5); b.legend(title="målfart",fontsize=8); b.grid(alpha=.3)

# (C) Flygtid & drop vs avstånd
c=ax[1,0]
c.plot(Rr,[TOF(R)*1000 for R in Rr],color="#ffb000",lw=2.2,label="flygtid [ms]")
c.axvspan(0,LED_MAX,color="#39d98a",alpha=.10)
c.set_xlabel("avstånd [m]"); c.set_ylabel("flygtid [ms]",color="#ffb000"); c.grid(alpha=.3)
c2=c.twinx(); c2.plot(Rr,[DROP(R)*100 for R in Rr],color="#4aa3ff",lw=2,label="drop [cm]")
c2.set_ylabel("drop [cm]",color="#4aa3ff")
c.set_title("C. Flygtid & drop vs avstånd (M4-profil, Fas 2-adjudikation)", fontsize=10, fontweight="bold")
l1,la=c.get_legend_handles_labels(); l2,lb=c2.get_legend_handles_labels(); c.legend(l1+l2,la+lb,fontsize=8,loc="upper left")

# (D) Latensbudget — staplad tidslinje
d=ax[1,1]
stages=[("IR-paket\n(MilesTag II)",24,"#ffb000"),("TSOP",0.3,"#ff5c5c"),
        ("MCU-avkod",1.0,"#ffd35c"),("ESP-NOW",5.0,"#4aa3ff"),("Server\n(Fas 2)",3.0,"#1b7")]
left=0
for name,dur,col in stages:
    d.barh(0,dur,left=left,color=col,ec="white")
    d.text(left+dur/2,0,f"{name}\n{dur:g}ms",ha="center",va="center",fontsize=7.5)
    left+=dur
d.axvline(50,color="#b30",ls="--",lw=1.5); d.text(50.5,0.35,"50 ms = 'känns direkt'",color="#b30",fontsize=8)
d.set_title(f"D. Latensbudget: ~{left:.0f} ms end-to-end (< 50 ms)", fontsize=10, fontweight="bold")
d.set_xlim(0,60); d.set_ylim(-0.6,0.6); d.set_yticks([]); d.set_xlabel("tid [ms]")

plt.tight_layout(rect=[0,0,1,0.96])
plt.savefig("/home/user/Strilas/docs/sim-fairness.png", dpi=110, facecolor="white"); plt.close(fig2)

# ============================================================
# ANIMATION — TOP-DOWN ENGAGEMANGSREPLAY
# ============================================================
DT=0.05; FRAMES=150
# målbana: korsar + närmar sig
def target_pos(t):
    x=45-1.5*t                          # närmar sig
    y=12*np.sin(0.9*t)                  # strafe i sidled
    return np.array([max(x,12), y])
def target_vel(t):
    d=1e-3; return (target_pos(t+d)-target_pos(t-d))/(2*d)

state=dict(health=100.0, ammo=30, hits=[], shots=[], last_shot=-1, dead_t=None, fired=[])
PN_lead=1.0; sigma_shoot=0.7

fig,(axM,axH)=plt.subplots(1,2,figsize=(15,7.2),gridspec_kw={"width_ratios":[2.4,1]})
fig.patch.set_facecolor("#0e1116")
for a in (axM,axH): a.set_facecolor("#0e1116")

def draw(frame):
    t=frame*DT; axM.clear(); axH.clear()
    for a in (axM,axH): a.set_facecolor("#0e1116")
    tp=target_pos(t); tv=target_vel(t); R=np.hypot(*tp);
    # --- karta ---
    axM.set_xlim(0,52); axM.set_ylim(-16,16); axM.set_aspect("equal")
    axM.set_title("STRILAS — engagemangsreplay (top-down)  ·  allt i ett system",
                  color="#e6edf3", fontsize=12, fontweight="bold")
    axM.set_xlabel("downrange [m]",color="#8b949e"); axM.set_ylabel("sidled [m]",color="#8b949e")
    axM.tick_params(colors="#8b949e")
    axM.scatter([0],[0],marker="^",s=240,color="#39d98a",zorder=6)
    axM.text(0,-2.2,"SKYTT\n(UWB-tag)",color="#39d98a",ha="center",fontsize=8)
    # mål
    dead = state["dead_t"] is not None
    tcol = "#6e7681" if dead else "#ff5c5c"
    axM.scatter(*tp,s=200,color=tcol,zorder=6,marker="o")
    axM.text(tp[0],tp[1]+1.6,("MÅL ☠" if dead else "MÅL"),color=tcol,ha="center",fontsize=8)
    axM.text(tp[0],tp[1]-2.4,f"{R:.0f} m\nUWB",color="#8b949e",ha="center",fontsize=7)
    # avfyrning var ~0.45 s om levande & ammo
    if (not dead) and state["ammo"]>0 and t-state["last_shot"]>=0.45:
        state["last_shot"]=t; state["ammo"]-=1
        tof=TOF(R); lead_pt=target_pos(t+PN_lead*tof)   # skytt leder mot framtida pos
        aim=lead_pt.copy()
        off=R*np.tan(np.radians(rng.normal(0,sigma_shoot,2)))
        aim_xy=aim+np.array([0,off[0]])
        # server: var är målet när kulan anländer
        arr=target_pos(t+tof)
        cy=aim_xy[1]-arr[1]; cz=1.4+off[1]; r=beam_r(R)
        hit=abs(cy)<=0.25+r and -r<=cz<=BODY_H+r
        zname,zmult,_=zone_of(cz if hit else -9, cy if hit else 9)
        if hit and zname is None: zname,zmult="Bröst",1.0
        state["fired"].append((t,tp.copy(),aim_xy.copy(),arr.copy(),hit,zname,zmult))
        if hit:
            dmg=18*zmult; state["health"]=max(0,state["health"]-dmg)
            state["hits"].append((t,zname))
            if state["health"]<=0 and state["dead_t"] is None: state["dead_t"]=t
    # rita nyligen avfyrade skott (0.25s glow)
    for (ts,tpz,aim_xy,arr,hit,zname,zmult) in state["fired"][-12:]:
        age=t-ts
        if age<0.25:
            al=1-age/0.25
            axM.plot([0,aim_xy[0]],[0,aim_xy[1]],color=("#39d98a" if hit else "#ffb000"),
                     lw=1.6,alpha=al*0.9,zorder=4)
            if hit:
                axM.scatter(*arr,s=80,color="#39d98a",alpha=al,zorder=5,marker="x")
    # beam cone (riktning mot lead)
    if not dead:
        ang=np.degrees(np.arctan2(target_pos(t+0.3)[1],target_pos(t+0.3)[0]))
        axM.add_patch(Wedge((0,0),R+3,ang-BEAM_HALF_DEG,ang+BEAM_HALF_DEG,
                            color="#39d98a",alpha=0.10,zorder=1))
    # --- HUD-panel ---
    axH.set_xlim(0,10); axH.set_ylim(0,10); axH.axis("off")
    axH.text(0.3,9.4,"WEAPON HUD",color="#39d98a",fontsize=13,fontweight="bold",family="monospace")
    axH.text(0.3,8.4,f"AMMO   {state['ammo']:2d}/30",color="#e6edf3",fontsize=12,family="monospace")
    axH.text(0.3,7.6,f"RANGE  {R:4.0f} m",color="#e6edf3",fontsize=12,family="monospace")
    axH.text(0.3,6.8,f"TOF    {TOF(R)*1000:4.0f} ms",color="#8b949e",fontsize=11,family="monospace")
    axH.text(0.3,6.0,f"HITS   {len(state['hits'])}",color="#e6edf3",fontsize=12,family="monospace")
    # target health bar
    axH.text(0.3,4.9,"MÅL HÄLSA",color="#8b949e",fontsize=10,family="monospace")
    axH.add_patch(Rectangle((0.3,4.0),9,0.7,ec="#30363d",fc="#161b22"))
    hp=state["health"]/100
    axH.add_patch(Rectangle((0.3,4.0),9*hp,0.7,color=("#39d98a" if hp>.5 else "#ffb000" if hp>.2 else "#ff5c5c")))
    axH.text(4.8,4.35,f"{state['health']:.0f}%",color="#e6edf3",ha="center",va="center",fontsize=10,family="monospace")
    # last hit zone log
    axH.text(0.3,3.1,"TRÄFFLOGG",color="#8b949e",fontsize=10,family="monospace")
    for i,(ts,zn) in enumerate(state["hits"][-5:][::-1]):
        cc="#ff5c5c" if zn=="Huvud" else "#e6edf3"
        axH.text(0.3,2.5-i*0.5,f" {ts:4.1f}s  {zn}{' ★HEADSHOT' if zn=='Huvud' else ''}",
                 color=cc,fontsize=9,family="monospace")
    if state["dead_t"] is not None:
        axH.text(5,1.0,"☠ TARGET DOWN",color="#ff5c5c",ha="center",fontsize=15,fontweight="bold",family="monospace")
    axM.text(40,15,f"t = {t:4.1f} s",color="#8b949e",fontsize=10,family="monospace")
    return []

anim=FuncAnimation(fig,draw,frames=FRAMES,interval=50,blit=False)
try:
    anim.save("/home/user/Strilas/docs/sim-engagement.gif",writer=PillowWriter(fps=20),dpi=80)
    print("saved sim-engagement.gif")
except Exception as e:
    print("GIF-fel:",e)
plt.close(fig)

# ---------------- NYCKELTAL ----------------
print("\n=== PRECISIONSBEVIS ===")
for R in (10,30,50):
    print(f"  Stråle ±1° @{R}m: fläck Ø{2*beam_r(R):.2f} m | torso vinkel {np.degrees(2*np.arctan(0.25/R)):.2f}° | huvud {np.degrees(2*np.arctan(0.105/R)):.2f}°")
print(f"  → Fas1-headshot kräver fläck<huvud → bara <~7.4 m. Fas2 (server) klarar alla avstånd.")
print("\n=== RÖRLIGT MÅL @40m ===")
for vt in (2,4,6):
    print(f"  {vt} m/s: flygtid {TOF(40)*1000:.0f} ms → lead {TOF(40)*vt:.1f} m  (utan lead = bom)")
print(f"\nslutfört: sim-precision.png, sim-fairness.png, sim-engagement.gif")
