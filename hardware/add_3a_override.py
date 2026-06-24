#!/usr/bin/env python3
"""STRILAS — applicera 3A-override på det routade optikkortet (sense-sidan, DNP-motstånd):
R3 = Rp(0R1, 0805, DNP) parallellt DIREKT över Rsense(R2,0R2) → montera = 3A, obestyckat = 1A (fail-safe).
Kopplar bara IDRV_SENSE↔GND (lokalt vid R2) → ingen op-amp-referens-routing (IDRV_REF är inmurad i det
mättade delarområdet → sense-sidan valdes). Default DNP = säker 1A; kortet levereras som 1A. R3 ligger
>4,6 mm från linshålskanten (Ø16 @150,126) och täcker inte kamera-aperturen. Byter F1→PTC_3A, emitter
→SFH4725AS. Bevarar all befintlig routning. Kör EN gång på c644fcf-kortet; därefter weapon_finish.
(Optikkortet är för tätt för en separat bygel vid sense-noden → ett DNP-motstånd är platsfritt + precist.)"""
import pcbnew
b = pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb"); MM = pcbnew.FromMM
def Vec(x, y): return pcbnew.VECTOR2I(MM(x), MM(y))
def suff(n): return n.split('/')[-1]
def netobj(s):
    for f in b.GetFootprints():
        for p in f.Pads():
            if suff(p.GetNetname()) == s: return p.GetNet()
def pp(ref, pad):
    for f in b.GetFootprints():
        if f.GetReferenceAsString() == ref:
            for p in f.Pads():
                if p.GetName() == pad: return (p.GetPosition().x/1e6, p.GetPosition().y/1e6)

# BOM-värden: 3A-skalan
for f in b.GetFootprints():
    fid = f.GetFPIDAsString()
    if 'Fuse_1206' in fid: f.SetValue("PTC_3A")
    if 'IR_Emitter' in fid: f.SetValue("SFH4725AS_940nm_bin13")

isense = netobj("IDRV_SENSE"); gnd = netobj("GND")

def add_fp(ld, nm, ref, val, x, y, nets, rot=0):
    fp = pcbnew.FootprintLoad(f"/usr/share/kicad/footprints/{ld}.pretty", nm)
    fp.SetReference(ref); fp.SetValue(val); fp.SetPosition(Vec(x, y))
    if rot: fp.SetOrientationDegrees(rot)
    for pd, nt in zip(list(fp.Pads()), nets): pd.SetNet(nt)
    b.Add(fp); return fp

# Rp-override (0805, DNP). pad1→GND, pad2→IDRV_SENSE → parallellt över R2 (Rsense).
# Läggs först med tillfälligt unikt ref (Rxx) — slutligt ref sätts i normaliseringen nedan.
add_fp("Resistor_SMD", "R_0805_2012Metric", "Rxx", "0R1 DNP=1A/montera=3A", 146.0, 114.0, [gnd, isense])
(g1x, g1y) = pp('Rxx', '1')                     # GND-pad
(s2x, s2y) = pp('Rxx', '2')                     # IDRV_SENSE-pad
(r21x, r21y) = pp('R2', '1')                    # Rsense IDRV_SENSE-pad

# GND-via vid Rp.1 (sticker ner i GND-gjutningarna — undviker trångt sense-nodsspår)
via = pcbnew.PCB_VIA(b); via.SetPosition(Vec(g1x, g1y))
via.SetDrill(MM(0.3)); via.SetWidth(MM(0.6)); via.SetNet(gnd); b.Add(via)

# IDRV_SENSE: kort spår Rp.2 -> R2.1 (parallellkoppling lokalt vid sense-noden)
t = pcbnew.PCB_TRACK(b); t.SetStart(Vec(s2x, s2y)); t.SetEnd(Vec(r21x, r21y))
t.SetWidth(MM(0.5)); t.SetLayer(pcbnew.F_Cu); t.SetNet(isense); b.Add(t)

# --- normalisera motstånds-ref mot netlistan (SKiDL-ordning) via nät-signatur ---
# (BOM:en slår upp värden ur .net per ref → board-ref MÅSTE matcha netlistans ref.)
def rsig(f):
    return (str(f.GetFPID().GetLibItemName()),
            frozenset((p.GetName(), suff(p.GetNetname())) for p in f.Pads()))
TARGET = {
    ("R_0805_2012Metric", frozenset({("1", "GND"), ("2", "IDRV_SENSE")})): "R3",    # Rp_ovr
    ("R_0805_2012Metric", frozenset({("1", "N$1"), ("2", "GND")})):        "R1",    # Rg2
    ("R_0805_2012Metric", frozenset({("1", "N$2"), ("2", "DRV_GATE")})):   "R6",    # Rgate
    ("R_2512_6332Metric", frozenset({("1", "IDRV_SENSE"), ("2", "GND")})): "R2",    # Rsense
    ("R_0805_2012Metric", frozenset({("1", "IR_MOD"), ("2", "IDRV_REF")})):"R4",    # Rdiv_a
    ("R_0805_2012Metric", frozenset({("1", "IDRV_REF"), ("2", "GND")})):   "R5",    # Rdiv_b
}
for f in b.GetFootprints():
    if f.GetReference().startswith("R") or f.GetReference() == "Rxx":
        tgt = TARGET.get(rsig(f))
        if tgt: f.SetReference(tgt)

# fyll om gjutningar så GND/IDRV_SENSE-rensningen kring Rp löses
pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
print("DNP-Rp override klar; R3@(%.1f,%.1f) GND-via@(%.4f,%.4f) sense-spår R3.2->R2.1 %.2fmm"
      % (146.0, 114.0, g1x, g1y, ((s2x-r21x)**2+(s2y-r21y)**2)**0.5))
