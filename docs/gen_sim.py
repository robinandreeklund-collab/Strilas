#!/usr/bin/env python3
"""STRILAS Fas 1 — fysik-/genomförbarhetssimulering med vald hårdvara.
Emitter SFH 4715AS, detektor TSOP4856, IMU ICM-45686, M4-ballistikprofil.
Genererar docs/phase1-sim.png + skriver nyckeltal till stdout."""
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ===================== 1. IR-LÄNKBUDGET =====================
def omega(theta_deg):                      # konvinkel för kon med halvvinkel theta
    return 2*np.pi*(1-np.cos(np.radians(theta_deg)))

# SFH 4715AS: ~0.9 W/sr on-axis @1A över ±45° (bar LED)
I_axis_1A_bare, theta_bare = 0.9, 45.0
Phi_1A = I_axis_1A_bare*omega(theta_bare)  # ~1.66 W total radiant flux @1A

def emitter_Ie(I_f, half_deg, n_led=1, lens_eff=0.6):
    """On-axis radiant intensity [W/sr] vid pulsström I_f, halvvinkel, n LED."""
    derate = max(1.0-0.03*(I_f-1), 0.7)    # mild sublinjär vid hög ström
    Phi = Phi_1A*I_f*derate*n_led
    return lens_eff*Phi/omega(half_deg)

Emin_ideal = 0.35e-3                        # W/m^2 TSOP4856 tröskel-irradians (lab/mörker)
ENVS = {                                    # multiplikator på tröskeln (AGC-desens + förluster)
    "Inomhus / mörker":            (1,   "#39d98a"),
    "Utomhus / molnigt-skugga":    (10,  "#4aa3ff"),
    "Utomhus / starkt solljus":    (30,  "#ffb000"),
    "Direkt sol mot sensor":       (100, "#ff5c5c"),
}
FILTER_GAIN = 4.0                           # 860 nm bandpass på TSOP: tröskel-förbättring i sol

def rng(I_f, half_deg, env_mult, n_led=2, filt=False, lens_eff=0.6):
    Emin = Emin_ideal*env_mult/(FILTER_GAIN if filt else 1.0)
    return np.sqrt(emitter_Ie(I_f, half_deg, n_led, lens_eff)/Emin)

# ===================== 2. BALLISTIK (M4 / 5.56) =====================
g, v0, kd = 9.81, 880.0, 0.001277           # kd kalibrerad: v(300m)≈600 m/s
def trajectory(rmax=320.0, dt=1e-4):
    x=y=t=0.0; vx=v0; vy=0.0
    X=[0];Y=[0];T=[0];V=[v0]
    while x < rmax:
        s=np.hypot(vx,vy)
        ax=-kd*s*vx; ay=-g-kd*s*vy
        vx+=ax*dt; vy+=ay*dt; x+=vx*dt; y+=vy*dt; t+=dt
        X.append(x);Y.append(-y);T.append(t);V.append(np.hypot(vx,vy))
    return map(np.array,(X,Y,T,V))
Xb,Yb,Tb,Vb=trajectory()
def at_range(R):
    i=np.searchsorted(Xb,R); return Tb[i],Yb[i],Vb[i]

# ===================== 3. IMU / MYNNINGSKLÄTTRING =====================
def climb_rate(t, A=160.0, f=22.0, tau=0.018):   # °/s, en rekylcykel ~40 ms
    return A*np.sin(2*np.pi*f*t)*np.exp(-t/tau)

# ===================== FIGUR =====================
fig,axs=plt.subplots(2,3,figsize=(17,10)); fig.patch.set_facecolor("white")
fig.suptitle("STRILAS Fas 1 — genomförbarhetssimulering  (SFH 4715AS · TSOP4856 · ICM-45686 · M4-profil)",
             fontsize=15,fontweight="bold")

# --- A: räckvidd vs pulsström, per miljö (2×LED, ±10°) ---
ax=axs[0,0]; I=np.linspace(1,3,50)
for name,(m,c) in ENVS.items():
    ax.plot(I,[rng(i,10,m) for i in I],color=c,lw=2,label=name)
ax.plot(I,[rng(i,10,30,filt=True) for i in I],"--",color="#ff8c00",lw=2,label="Starkt solljus + 860 nm-filter")
ax.axhline(30,color="#888",ls=":",lw=1); ax.text(1.02,31,"30 m mål",color="#888",fontsize=8)
ax.set_title("A. Räckvidd vs pulsström  (2×SFH4715AS, ±10°)",fontweight="bold")
ax.set_xlabel("LED-pulsström [A]"); ax.set_ylabel("Max räckvidd [m]"); ax.set_ylim(0,160)
ax.legend(fontsize=7); ax.grid(alpha=.3)

# --- B: räckvidd vs strålvinkel + naiva fallet ---
ax=axs[0,1]; H=np.linspace(4,30,60)
ax.plot(H,[rng(3,h,10) for h in H],color="#4aa3ff",lw=2,label="Skugga (2×LED @3A)")
ax.plot(H,[rng(3,h,30) for h in H],color="#ffb000",lw=2,label="Starkt solljus (2×LED @3A)")
ax.plot(H,[rng(3,h,30,filt=True) for h in H],"--",color="#ff8c00",lw=2,label="Solljus + 860 nm-filter")
naive=rng(1,45,30,n_led=1,lens_eff=1.0)
ax.scatter([45 if False else 28],[naive],color="#ff5c5c",zorder=5)
ax.annotate(f"naivt: 1 bar LED @1A i sol ≈ {naive:.0f} m",(20,naive+3),color="#ff5c5c",fontsize=8)
ax.axhline(naive,color="#ff5c5c",ls=":",lw=1)
ax.set_title("B. Räckvidd vs strålvinkel  — varför lins + 2 LED behövs",fontweight="bold")
ax.set_xlabel("Emitter halvvinkel [°]"); ax.set_ylabel("Max räckvidd [m]"); ax.set_ylim(0,120)
ax.legend(fontsize=7); ax.grid(alpha=.3)

# --- C: stråldiameter (hit-cone) vs avstånd ---
ax=axs[0,2]; D=np.linspace(2,60,60)
for h,c in [(5,"#39d98a"),(10,"#4aa3ff"),(20,"#ffb000")]:
    ax.plot(D,2*D*np.tan(np.radians(h)),color=c,lw=2,label=f"±{h}° stråle")
ax.axhline(0.5,color="#888",ls=":",lw=1); ax.text(2,0.7,"~0.5 m torso",color="#888",fontsize=8)
ax.axhline(1.8,color="#bbb",ls=":",lw=1); ax.text(2,2.0,"~1.8 m spelare",color="#bbb",fontsize=8)
ax.set_title("C. Strålfläck (hit-cone) vs avstånd",fontweight="bold")
ax.set_xlabel("Avstånd [m]"); ax.set_ylabel("Stråldiameter [m]"); ax.set_ylim(0,25)
ax.legend(fontsize=8); ax.grid(alpha=.3)

# --- D: ballistik drop + flygtid ---
ax=axs[1,0]; m=Xb<=300
ax.plot(Xb[m],Yb[m]*100,color="#4aa3ff",lw=2,label="Drop [cm]")
ax.set_xlabel("Avstånd [m]"); ax.set_ylabel("Drop [cm]",color="#4aa3ff"); ax.invert_yaxis()
ax2=ax.twinx(); ax2.plot(Xb[m],Tb[m]*1000,color="#ffb000",lw=2,label="Flygtid [ms]")
ax2.set_ylabel("Flygtid [ms]",color="#ffb000")
ax.set_title("D. Simulerad ballistik M4 (880 m/s) — Fas 2-adjudikation",fontweight="bold")
ax.grid(alpha=.3)
for R in (100,200,300):
    t,d,v=at_range(R); ax.scatter([R],[d*100],color="#4aa3ff",s=15,zorder=5)

# --- E: nödvändig förhållning (lead) vs avstånd ---
ax=axs[1,1]
for vt,c in [(1,"#39d98a"),(3,"#4aa3ff"),(5,"#ffb000")]:
    ax.plot(Xb[m],Tb[m]*vt*100,color=c,lw=2,label=f"mål {vt} m/s i sidled")
ax.set_title("E. Nödvändig lead (rörligt mål) — därför central adjudikation",fontweight="bold")
ax.set_xlabel("Avstånd [m]"); ax.set_ylabel("Lead [cm]"); ax.legend(fontsize=8); ax.grid(alpha=.3)

# --- F: IMU mynningsklättring, sampling 1000 vs 200 Hz ---
ax=axs[1,2]; tt=np.linspace(0,0.08,2000)
ax.plot(tt*1000,climb_rate(tt),color="#ccc",lw=1.5,label="sann klättringshastighet")
for ode,c,mk in [(1000,"#39d98a","o"),(200,"#ff5c5c","s")]:
    ts=np.arange(0,0.08,1/ode); ax.plot(ts*1000,climb_rate(ts),mk,color=c,ms=4,label=f"{ode} Hz ODR")
ax.set_title("F. IMU-fångst av mynningsklättring (ICM-45686)",fontweight="bold")
ax.set_xlabel("Tid [ms]"); ax.set_ylabel("Pitch-hastighet [°/s]"); ax.legend(fontsize=8); ax.grid(alpha=.3)

plt.tight_layout(rect=[0,0,1,0.97])
plt.savefig("/home/user/Strilas/docs/phase1-sim.png",dpi=110,facecolor="white")

# ===================== NYCKELTAL =====================
print("=== IR-LÄNKBUDGET (2×SFH4715AS @3A, ±10° lins, lens_eff 0.6) ===")
for name,(mm,_) in ENVS.items():
    print(f"  {name:30s}: {rng(3,10,mm):6.1f} m   (+860nm-filter: {rng(3,10,mm,filt=True):6.1f} m)")
print(f"  NAIVT 1 bar LED @1A, ±45°, sol(30x): {rng(1,45,30,n_led=1,lens_eff=1.0):.1f} m  <-- din tvivel, korrekt")
print(f"  Emitter Ie (2×LED@3A,±10°): {emitter_Ie(3,10,2,0.6):.1f} W/sr")
print("\n=== BALLISTIK M4 (880 m/s) ===")
for R in (50,100,200,300):
    t,d,v=at_range(R); print(f"  {R:3d} m: flygtid {t*1000:5.1f} ms | drop {d*100:5.1f} cm | restfart {v:4.0f} m/s | lead@3m/s {t*3*100:4.0f} cm")
print("\n=== IMU ===")
peak=max(climb_rate(np.linspace(0,0.08,5000)))
ang=np.trapezoid(np.clip(climb_rate(np.linspace(0,0.04,4000)),0,None),np.linspace(0,0.04,4000))
print(f"  Peak pitch-rate ~{peak:.0f}°/s, klättring/cykel ~{ang:.1f}°  | @1kHz: ~{int(0.04*1000)} sampel/cykel  @200Hz: ~{int(0.04*200)} sampel")
print(f"  Obekämpad full-auto, ~{ang:.1f}°/skott → vertikal avvikelse @30m = {30*np.tan(np.radians(ang))*100:.0f} cm/skott")
print("\n=== LATENSBUDGET (engagemangsloop) ===")
airtime=2.4+0.6+14*(0.9+0.6)
print(f"  MilesTag II skott-airtime ~{airtime:.0f} ms + TSOP-demod ~0.3 ms + ESP-NOW ~1-10 ms => ~{airtime+8:.0f} ms (<50 ms, känns direkt)")
print("saved docs/phase1-sim.png")
