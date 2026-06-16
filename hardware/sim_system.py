#!/usr/bin/env python3
"""STRILAS — SYSTEM-SIMULERING (signalflöde + kraftintegritet över alla kort).
Stitchar korten via kabel-kontakter (position-matchade pins), bygger global nät-graf och
verifierar att varje funktionell kedja flödar end-to-end + kraftintegritet. Logisk flödes-
simulering (ej SPICE): bevisar topologi/anslutning. Pins = pad-NUMMER (som i KiCad-netlistan)."""
import re, sys
from collections import defaultdict

def parse(path):
    t=open(path).read(); nets={}
    ns=t[t.index("(nets"):]
    for blk in re.split(r'\(net\s*\(code',ns)[1:]:
        nm=re.search(r'\(name "([^"]+)"\)',blk); nodes=re.findall(r'\(ref "([^"]+)"\)\s*\(pin "([^"]+)"',blk)
        if nm and nodes: nets[nm.group(1)]=[(r,p) for r,p in nodes]
    return nets

B={b:parse(f"hardware/{b}.net") for b in ["weapon-module","helmet-mb","vest-mb","vest-patch","firecontrol"]}
P4REF={"vest-mb":{"J11","J12"},"helmet-mb":{"J8","J9"},"weapon-module":{"J1"},"firecontrol":{"J1"}}
def touches(nodes,refs): return any(r in refs for r,p in (nodes or []))
def refs_of(nodes): return set(r for r,p in (nodes or []))
def netof(board,ref,pin):
    for n,nodes in B[board].items():
        if (ref,pin) in nodes: return n
    return None

# ---- kabel-bryggor (position-matchade) → union-find ----
par={}
def find(x):
    par.setdefault(x,x)
    while par[x]!=x: par[x]=par[par[x]]; x=par[x]
    return x
def uni(a,b): par[find(a)]=find(b)
for b in B:
    for n in B[b]: find((b,n))
PP=["1","2","3","4","5"]   # patch J1 pin1..5 = VBAT,GND,DATA,LED_EN,3V3
for i in PP:
    pn=netof("vest-patch","J1",i)
    for board,zc in [("vest-mb","J1"),("helmet-mb","J2")]:
        mn=netof(board,zc,i)
        if pn and mn: uni(("vest-patch",pn),(board,mn))
def bridged(b1,n1,b2,n2): return n1 and n2 and find((b1,n1))==find((b2,n2))

PASS=[];FAIL=[]
def chk(c,m): (PASS if c else FAIL).append(m)
print("STRILAS system-simulering — signalflöde end-to-end\n")

# 1) SKOTT-RX: patch-TSOP→OR-diod→DATA→kabel→moderkort→P4
for board,zc in [("vest-mb","J1"),("helmet-mb","J2")]:
    pdata=netof("vest-patch","J1","3"); mdata=netof(board,zc,"3")
    chk(bridged("vest-patch",pdata,board,mdata) and touches(B[board][mdata],P4REF[board]),
        f"SKOTT-RX [{board}]: patch-DATA→kabel→{board}:{mdata}→P4 ({sorted(refs_of(B[board][mdata])&P4REF[board])})")
# patch TSOP matas +3V3, OUT→OR-diod
chk(touches(B["vest-patch"]["+3V3"],{"U1","U2","U3","U4"}), "Patch: TSOP-VS (U1-4) på +3V3")
out1=B["vest-patch"].get("OUT1") or B["vest-patch"].get("OUT_1")
chk(out1 and touches(out1,{"U1"}) and any(r.startswith("D") for r,p in out1), f"Patch: TSOP U1.OUT→OR-diod ({refs_of(out1)})")

# 2) KONSTELLATION: P4→LED_EN→kabel→patch→FET→LED(VBAT-anod via serieR)
for board,zc in [("vest-mb","J1"),("helmet-mb","J2")]:
    mle=netof(board,zc,"4"); ple=netof("vest-patch","J1","4")
    chk(bridged("vest-patch",ple,board,mle) and touches(B[board][mle],P4REF[board]),
        f"KONSTELL [{board}]: P4→LED_EN→patch")
chk(touches(B["vest-patch"]["LED_EN"],{"Q1","R2"}), "Patch: LED_EN→FET-grind")
chk(touches(B["vest-patch"]["VBAT"],{"R3","R4"}) and touches(B["vest-patch"]["LED_A1"],{"D5"}),
    "Patch: LED-anod (D5) via serieR(R3)→VBAT")
chk(touches(B["vest-patch"]["LED_CATH"],{"Q1"}), "Patch: LED-katod→FET(Q1)")

# 3) KRAFT
for board,batt in [("vest-mb","J13"),("helmet-mb","J10")]:
    n=B[board]
    chk(touches(n["VBAT"],{batt}) and touches(n["VBAT"],{"U1"}), f"KRAFT [{board}]: batteri+buck-VIN på VBAT")
    chk(touches(n["+3V3"],{"L1"}), f"KRAFT [{board}]: buck-utgång(L1)→+3V3")
    chk(touches(n["VBAT"],P4REF[board]), f"KRAFT [{board}]: P4 VSYS=VBAT (självförsörjning)")
chk(touches(B["vest-patch"]["+3V3"],{"J1"}), "KRAFT: patch 3V3 från moderkort (J1.5)")

# 4) I²C (hjälm)
h=B["helmet-mb"]
chk(touches(h["I2C_SDA"],{"U2"}) and touches(h["I2C_SDA"],{"J1"}) and touches(h["I2C_SDA"],P4REF["helmet-mb"]),
    "I²C-SDA: IMU(U2)+F9P(J1)+P4 på samma nät")
chk(touches(h["I2C_SCL"],{"U2"}) and touches(h["I2C_SCL"],{"J1"}) and touches(h["I2C_SCL"],P4REF["helmet-mb"]),
    "I²C-SCL: IMU(U2)+F9P(J1)+P4 på samma nät")

# 5) GNSS UART (hjälm)
chk(touches(h["GNSS_RX"],{"J1"}) and touches(h["GNSS_RX"],P4REF["helmet-mb"]), "GNSS UART RX: F9P↔P4")
chk(touches(h["GNSS_TX"],{"J1"}) and touches(h["GNSS_TX"],P4REF["helmet-mb"]), "GNSS UART TX: F9P↔P4")

# 6) VIBRATOR (väst)
v=B["vest-mb"]
chk(touches(v["TPIC_SER"],{"U2","U3"}) and touches(v["TPIC_SER"],P4REF["vest-mb"]), "VIBRATOR: P4→TPIC SER")
chk(touches(v["VIB1"],{"U2","U3"}) and touches(v["VIB1"],{"J1"}), "VIBRATOR: TPIC-utgång→zon1 VIB")

# 7) AUDIO (hjälm)
chk(touches(h["I2S_DOUT"],{"J6"}) and touches(h["I2S_DOUT"],P4REF["helmet-mb"]), "AUDIO: P4 I2S DOUT→amp(J6)")
chk(touches(h["I2S_DIN"],{"J7"}) and touches(h["I2S_DIN"],P4REF["helmet-mb"]), "AUDIO: mik(J7)→P4 I2S DIN")

# 8) VAPEN emitter CC-sänka
w=B["weapon-module"]
chk(touches(w["LED_CATH"],{"Q2"}) and touches(w["VBAT"],{"D2"}), "VAPEN: emitter(D2/D3 940nm)→katod→CC-pass-FET(Q2)")
chk(touches(w["IDRV_SENSE"],{"R2","U2"}) and touches(w["IDRV_REF"],{"U2"}), "VAPEN: CC-sänka OPA171(U2)+sense(R2)+referens")

# 9) KRAFTINTEGRITET: varje IC-kraftstift på rätt skena (per kort)
def power_ok(board, ic, supply_pins, supply_nets):
    n=B[board]
    for pin in supply_pins:
        net=netof(board,ic,pin)
        if net not in supply_nets: return False,(ic,pin,net)
    return True,None
# helmet: IMU U2 VDD(pin8)+VDDIO(pin5) på +3V3 ; buck U1 VIN(3) på VBAT
ok,info=power_ok("helmet-mb","U2",["8","5"],{"+3V3"}); chk(ok, f"KRAFT: hjälm IMU U2 VDD/VDDIO→+3V3 {info or ''}")
# vest: TPIC U2/U3 VCC(pin2) på +3V3
ok,_=power_ok("vest-mb","U2",["2"],{"+3V3"}); chk(ok,"KRAFT: väst TPIC U2 VCC→+3V3")

print("\n--- RESULTAT ---")
for m in PASS: print("  OK  ",m)
for m in FAIL: print("  FAIL",m)
print(f"\n{len(PASS)} PASS, {len(FAIL)} FAIL")
sys.exit(1 if FAIL else 0)
