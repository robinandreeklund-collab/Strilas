#!/usr/bin/env python3
"""STRILAS — GEMENSAM-KOMPONENT-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Bär alla återkommande passiva/diskreta/jellybean-delar som korten delar, i de paket vi använder
(+ alternativa paket för de som idag är inkonsekventa: 100nF & 1uF finns i BÅDE 0402 och 0805).
Syfte: ladda upp BOM:en till NextPCB → se vilka som finns i lager (basic-bibliotek) → standardisera
ALLA kort på samma in-stock-delar (ett paket per värde, inga one-offs). Tillverkas EJ.

Kör: python3 hardware/common_sampler.py  → hardware/common-sampler.kicad_pcb
"""
import pcbnew
MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
KI = "/usr/share/kicad/footprints"

def F(lib, name):
    return (f"{KI}/{lib}.pretty", name)

R08 = F("Resistor_SMD", "R_0805_2012Metric")
R25 = F("Resistor_SMD", "R_2512_6332Metric")
C04 = F("Capacitor_SMD", "C_0402_1005Metric")
C08 = F("Capacitor_SMD", "C_0805_2012Metric")
C12 = F("Capacitor_SMD", "C_1206_3216Metric")
C13 = F("Capacitor_SMD", "C_1210_3225Metric")

# (ref, etikett, paket, footprint, MPN, tillverkare, beskrivning)  — ★ = används på ≥3 kort
CANDS = [
    # --- MOTSTÅND (standard 0805, 1%) ---
    ("R1", "10k", "0805", R08, "RC0805FR-0710KL", "Yageo", "Res 10k 1% 0805 ★gemensam"),
    ("R2", "4k7", "0805", R08, "RC0805FR-074K7L", "Yageo", "Res 4.7k 1% 0805 (I2C-pullup)"),
    ("R3", "100R", "0805", R08, "RC0805FR-07100RL", "Yageo", "Res 100R 1% 0805"),
    ("R4", "220R", "0805", R08, "RC0805FR-07220RL", "Yageo", "Res 220R 1% 0805 (gate)"),
    ("R5", "1k", "0805", R08, "RC0805FR-071KL", "Yageo", "Res 1k 1% 0805"),
    ("R6", "2.2k", "0805", R08, "RC0805FR-072K2L", "Yageo", "Res 2.2k 1% 0805 (mik-bias)"),
    ("R7", "15k", "0805", R08, "RC0805FR-0715KL", "Yageo", "Res 15k 1% 0805 (CC-delare)"),
    ("R8", "31.6k", "0805", R08, "RC0805FR-0731K6L", "Yageo", "Res 31.6k 1% 0805 (buck-FB)"),
    ("R9", "100k", "0805", R08, "RC0805FR-07100KL", "Yageo", "Res 100k 1% 0805"),
    ("R10", "10R", "2512", R25, "CRCW251210R0FKEGHP", "Vishay", "Res 10R 1% 2W 2512 (LED-serie, EFFEKT)"),
    ("R11", "0R2", "2512", R25, "PE2512FKE070R200L", "Yageo", "Res 0.2R 1% 2W 2512 (CC-sense)"),
    # --- KONDENSATORER (★ standardisera 100nF & 1uF till ETT paket) ---
    ("C1", "100nF", "0402", C04, "CL05B104KO5NNNC", "Samsung", "MLCC 100nF 50V X7R 0402 ★ (vs 0805 -> VÄLJ ETT)"),
    ("C2", "100nF", "0805", C08, "CL21B104KBCNNNC", "Samsung", "MLCC 100nF 50V X7R 0805 ★ (vs 0402 -> VÄLJ ETT)"),
    ("C3", "1uF", "0402", C04, "CL05A105KP5NNNC", "Samsung", "MLCC 1uF 10V X5R 0402 (vs 0805 -> VÄLJ ETT)"),
    ("C4", "1uF", "0805", C08, "GRM21BR61E105KA99L", "Murata", "MLCC 1uF 25V X5R 0805 (high-runner, in-stock-alt)"),
    ("C5", "100pF", "0805", C08, "CL21C101JBANNNC", "Samsung", "MLCC 100pF 50V C0G 0805 (slingkomp)"),
    ("C6", "10uF", "1206", C12, "CL31A106KBHNNNE", "Samsung", "MLCC 10uF 25V X5R 1206 ★gemensam"),
    ("C7", "22uF", "1206", C12, "CL31A226KAHNNNE", "Samsung", "MLCC 22uF 25V X5R 1206 (buck-ut)"),
    ("C8", "100uF", "1210", C13, "CL32A107MQVNNNE", "Samsung", "MLCC 100uF 25V X5R 1210 (bulk, in-stock-alt)"),
    # --- DISKRETA / JELLYBEAN ---
    ("D1", "BAT54", "SOD-123", F("Diode_SMD", "D_SOD-123"), "BAT54-7-F", "Diodes", "Schottky (diod-OR TSOP)"),
    ("D2", "SMBJ12A", "SMB", F("Diode_SMD", "D_SMB"), "SMBJ12A", "Littelfuse", "TVS 12V (matningsskydd)"),
    ("Q1", "AO3400", "SOT-23", F("Package_TO_SOT_SMD", "SOT-23"), "AO3400A", "AOS", "N-FET 30V (LED-driver)"),
    ("Q2", "AO3401", "SOT-23", F("Package_TO_SOT_SMD", "SOT-23"), "AO3401A", "AOS", "P-FET -30V (rev-skydd)"),
    ("Q3", "AOD4184A", "TO-252", F("Package_TO_SOT_SMD", "TO-252-2"), "AOD4184A", "AOS", "N-FET DPAK (CC pass)"),
    ("L1", "4.7uH", "FNR5040", F("Inductor_SMD", "L_Changjiang_FNR5040S"), "FNR5040320R47M", "Changjiang", "Induktor 4.7uH (buck)"),
    # --- AKTIVA REGULATORER / OP-AMP (delade/kritiska) ---
    ("U1", "AP63203", "TSOT23-6", F("Package_TO_SOT_SMD", "SOT-23-6"), "AP63203WU-7", "Diodes", "Buck 2A (2S->3V3)"),
    ("U2", "HT7333", "SOT-89", F("Package_TO_SOT_SMD", "SOT-89-3"), "HT7333-A", "Holtek", "LDO 3.3V 250mA (patch)"),
    ("U3", "OPA171", "SOT23-5", F("Package_TO_SOT_SMD", "SOT-23-5"), "OPA171AIDBVR", "TI", "Op-amp (CC-regulator)"),
]

COLS, COLP, ROWP = 7, 16.5, 21.0
X0 = -(COLS - 1) * COLP / 2
ROWS = (len(CANDS) + COLS - 1) // COLS
Y0 = (ROWS - 1) * ROWP / 2 + 5


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def text(b, x, y, s, h=1.0, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.2 if bold else 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); b.Add(t)


def main():
    b = pcbnew.BOARD()
    for i, (ref, val, pkg, (lib, fpn), mpn, mfr, desc) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = pcbnew.FootprintLoad(lib, fpn)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.SetPosition(V(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 4.8, ref, 1.0, bold=True)
        text(b, x, y - 4.6, val, 1.0, bold=True)
        text(b, x, y - 6.2, pkg, 0.7)

    W, H = COLS * COLP + 6, ROWS * ROWP + 18
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  GEMENSAM-KOMPONENT-SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - R/C/diskret/regulator for NextPCB lager-koll", 0.95)
    text(b, 0, y0 + 4, "Ladda upp BOM -> valj in-stock (basic-lib) -> standardisera ALLA kort pa samma delar", 0.9)
    text(b, 0, y0 + 2, "OBS 100nF & 1uF: valj ETT paket (0402 vs 0805) for hela projektet", 0.85)

    pcbnew.SaveBoard("hardware/common-sampler.kicad_pcb", b)
    print(f"hardware/common-sampler.kicad_pcb: {len(CANDS)} delar, board {W:.0f}x{H:.0f} mm")


if __name__ == "__main__":
    main()
