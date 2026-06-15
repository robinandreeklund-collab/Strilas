#!/usr/bin/env python3
"""STRILAS — teknisk blueprint: vapen → 150 m → mottagare + beräkningskedja.
Visualiserar den verifierade fysiken (system_physics_verification.py)."""
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, FancyArrowPatch
import numpy as np

BG="#0b0e12"; FG="#e6edf3"; MUT="#9aa4b0"; GRID="#1b2230"
GRN="#39d98a"; CYAN="#00bcd4"; ORANGE="#ffb000"; RED="#ff5c5c"; BLUE="#6fb3ff"
fig,ax=plt.subplots(figsize=(17,10.5)); ax.set_xlim(0,100); ax.set_ylim(0,62)
ax.set_facecolor(BG); fig.patch.set_facecolor(BG); ax.axis("off")

def box(x,y,w,h,fc="#11161d",ec=GRID,lw=1.5):
    ax.add_patch(FancyBboxPatch((x,y),w,h,boxstyle="round,pad=0.3,rounding_size=0.6",fc=fc,ec=ec,lw=lw,zorder=2));
def T(x,y,s,c=FG,fs=9,w="normal",ha="left",va="center"):
    ax.text(x,y,s,color=c,fontsize=fs,fontweight=w,ha=ha,va=va,zorder=4)
def arrow(x1,y1,x2,y2,c=FG,lw=2,ls="-",style="-|>"):
    ax.add_patch(FancyArrowPatch((x1,y1),(x2,y2),arrowstyle=style,color=c,lw=lw,ls=ls,
                 mutation_scale=18,zorder=3,shrinkA=0,shrinkB=0))

T(50,60,"STRILAS — teknisk blueprint: vapen → 150 m → mottagare + beräkning (verifierad fysik)",FG,15,"bold","center")

# ---------------- VAPEN-NOD ----------------
box(2,34,25,22,ec=GRN)
T(14.5,54,"VAPEN-NOD",GRN,12,"bold","center")
for i,(s) in enumerate([
    "ESP32-P4 (+C6 WiFi6) — hjärna",
    "OV5647 NoIR + M12 6mm (~33°) + 860nm BP",
    "  → sikteskamera (PRECISION)",
    "2× SFH47xx 940nm + Carclo 10195 (±7.5°)",
    "  → kodat skott (LOS+ID)",
    "1× ICM-45686 IMU (SPI)",
    "Buck-CC-driver + L1 + HW-strömtak",
    "Trigger → P4-GPIO",
]):
    T(3.4,51.5-i*2.05,("• "+s) if not s.startswith("  ") else s,FG if not s.startswith("  ") else MUT,8.2)

# ---------------- MOTTAGARE / KROPP @150m ----------------
bx=80
# kropp
ax.add_patch(Circle((bx,49),2.2,fc="#1a2230",ec=RED,lw=1.6,zorder=2))           # huvud
ax.add_patch(FancyBboxPatch((bx-3,38),6,9,boxstyle="round,pad=0.2",fc="#1a2230",ec=ORANGE,lw=1.6,zorder=2)) # torso
ax.add_patch(Rectangle((bx-2.2,30),1.7,8,fc="#1a2230",ec=BLUE,lw=1.2,zorder=2)) # ben
ax.add_patch(Rectangle((bx+0.5,30),1.7,8,fc="#1a2230",ec=BLUE,lw=1.2,zorder=2))
# hjälm-halo + GNSS
ax.add_patch(Circle((bx,51.3),2.7,fc="none",ec=GRN,lw=1.4,zorder=3))
for a in (60,120,180,0,240,300): ax.add_patch(Circle((bx+2.7*np.cos(np.radians(a)),51.3+2.7*np.sin(np.radians(a))),0.3,fc=GRN,zorder=4))
ax.add_patch(Circle((bx,51.3),0.7,fc=CYAN,zorder=4)); T(bx,53.0,"GNSS",CYAN,6.5,"bold","center")
# konstellation 860nm (cyan dots)
for (cx,cy) in [(bx,49),(bx-1.6,44),(bx+1.6,44),(bx-1.4,40),(bx+1.4,40)]:
    ax.add_patch(Circle((cx,cy),0.45,fc=CYAN,ec=FG,lw=0.4,zorder=5))
# TSOP (orange ticks)
for (cx,cy) in [(bx-3,45),(bx+3,45),(bx-3,41),(bx+3,41)]:
    ax.add_patch(Rectangle((cx-0.3,cy-0.3),0.6,0.6,fc=ORANGE,zorder=5))
box(72,24,17,4.5,ec=CYAN); T(80.5,26.2,"MOTTAGARE (väst+hjälm)",CYAN,9.5,"bold","center")
T(80.5,24.9,"TSOP 940nm-filter | 860nm-konstellation : GNSS-patch",MUT,7,"normal","center")

# ---------------- LÄNKAR mellan vapen och kropp ----------------
# 940nm skott (vid → cone) framåt
arrow(27,46,73,48,ORANGE,2.2,"-")
ax.add_patch(plt.Polygon([(27,46),(73,52),(73,44)],closed=True,fc=ORANGE,alpha=0.10,zorder=1))
T(50,52.5,"940 nm kodad stråle  →  LOS + skott-ID  (±7.5° = ~40 m spot @150 m, EJ hitbox)",ORANGE,8.5,"bold","center")
# 860nm konstellation tillbaka till kamera
arrow(73,42,27,42,CYAN,2.2,"-")
T(50,40.6,"860 nm konstellation  ←  kamera mäter bäring via solvePnP",CYAN,8.5,"bold","center")
# ballistik-arc
xs=np.linspace(27,73,50); ys=44-0.9*((xs-27)/46)**2*4
ax.plot(xs,ys,color=RED,lw=1.6,ls=(0,(4,2)),zorder=3)
T(50,36.8,"5.56 ballistik: flygtid 188 ms · drop 16 cm · lead(3 m/s) 56 cm",RED,8,"normal","center")
# 150m bar
arrow(27,32.5,73,32.5,MUT,1.2,"-","<|-|>"); T(50,33.6,"150 m",FG,11,"bold","center")

# ---------------- BERÄKNINGSKEDJA (botten) ----------------
T(50,28.5,"BERÄKNINGSKEDJA (verifierad @150 m — Monte Carlo + radiometri + länkbudget)",BLUE,11,"bold","center")
chain=[
 (2 ,"1· KAMERA-DETEKTION","SNR 30 @ 30µs exp\n(mättar → kort exp,\ningen rolling-smet)",GRN),
 (21,"2· PnP-BÄRING","σ = 0.0008°\n(krav 0.076° huvud)\nrange σ = 0.49 m",GRN),
 (40,"3· IMU + IR-LÄNK","drift 0.0005°/frame\nIR medium 2A→153 m\n(940nm+bandpass)",GRN),
]
for x,h,b,c in chain:
    box(x,9,17,11.5,ec=c); T(x+8.5,18.8,h,c,9,"bold","center")
    for j,ln in enumerate(b.split("\n")): T(x+8.5,16.5-j*1.7,ln,FG,8,"normal","center")
# server
box(60,9,17,11.5,ec=ORANGE); T(68.5,18.8,"4· SERVER-FUSION",ORANGE,9,"bold","center")
for j,ln in enumerate(["ballistik (drop+lead)","+ geometri × IR-grind","server-auktoritativt"]):
    T(68.5,16.5-j*1.7,ln,FG,8,"normal","center")
box(80,9,18,11.5,ec=RED); T(89,18.8,"5· TRÄFF-VERDIKT",RED,9,"bold","center")
for j,ln in enumerate(["100% torso (MC)","aim-RMS 0.1 cm @150 m","zon: huvud/torso/…"]):
    T(89,16.5-j*1.7,ln,FG,8,"normal","center")
for x1,x2 in [(19,21),(38,40),(57,60),(77,80)]: arrow(x1,14.7,x2,14.7,MUT,1.6)

# ---------------- HITBOX-callout + status ----------------
box(2,1.5,60,6,ec=GRID,fc="#0e131a")
T(3.4,5.7,"HITBOX @150 m (= riktiga kroppen, ej IR-strålen):",FG,9,"bold")
T(3.4,3.9,"torso Ø0.5 m = 0.19°  ·  huvud Ø0.2 m = 0.076°   |   vår aim-RMS = 0.1 cm  → vi pekar inom kroppen på mm-nivå",MUT,8.3)

box(64,1.5,34,6,ec=GRN,fc="#0e1a12")
T(65.5,5.7,"VERIFIERAT: precisionskedjan håller m. marginal",GRN,8.5,"bold")
T(65.5,3.9,"⚠️ enda mätpunkt kvar: Class 1-ström (bänk)",ORANGE,8.3)
plt.tight_layout(); plt.savefig("hardware/system-blueprint.png",dpi=140,facecolor=BG)
print("wrote hardware/system-blueprint.png")
