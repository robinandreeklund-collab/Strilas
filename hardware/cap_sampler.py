#!/usr/bin/env python3
"""STRILAS — KONDENSATOR/LAGER-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Bakgrund: efter paket-unifieringen till 0402 ligger **100nF 0402** (Samsung CL05B104KO5NNNC)
på 12–20 dagars lager-lead hos NextPCB → det är schemaflaskhalsen för de 4 mb-korten. Lösning
"A": byt till en ANNAN in-stock 100nF-0402-MPN (annat märke; 0402-100nF finns hos massor av
tillverkare, någon ligger i NextPCB:s basic-bibliotek i lager). Behåll 0402-footprinten, kapa
leadet — påverkar alla 4 kort positivt utan omroutning.

Detta kort bär MÅNGA 100nF-0402-kandidater (olika märken/spänningar) + de övriga delarna som
idag kräver manuell offert / har lång lead (0R2 2512, PTC-säkring, 4.7µH FNR5040, 10R 2512).
Ladda upp `cap-sampler-bom.xls` till NextPCB → se vilka som är **In Stock** i basic-lib → välj
in-stock-MPN och uppdatera `gen_nextpcb.py`. **Kortet beställs/tillverkas EJ** — bara lager-koll.

Kör: python3 hardware/cap_sampler.py
  → hardware/cap-sampler.kicad_pcb + leverans/cap-sampler/{gerbers.zip,bom.xls,centroid.csv}
"""
import os, csv, subprocess, pcbnew, xlwt

MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
KI = "/usr/share/kicad/footprints"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def F(lib, name):
    return (f"{KI}/{lib}.pretty", name)


C04 = F("Capacitor_SMD", "C_0402_1005Metric")
C08 = F("Capacitor_SMD", "C_0805_2012Metric")
R25 = F("Resistor_SMD", "R_2512_6332Metric")
L50 = F("Inductor_SMD", "L_Changjiang_FNR5040S")
PTC18 = F("Fuse", "Fuse_1812_4532Metric")

# (ref, etikett, paket, footprint, MPN, tillverkare, beskrivning)
# === HUVUDSYFTE: 100nF 0402 — många märken/spänningar, hitta en IN STOCK i NextPCB basic-lib ===
CANDS = [
    ("C1", "100nF 0402", "0402", C04, "CL05B104KO5NNNC", "Samsung", "MLCC 100nF 50V X7R 0402 — NUVARANDE (12-20 d lead, byts)"),
    ("C2", "100nF 0402", "0402", C04, "CL05B104KA5NNNC", "Samsung", "MLCC 100nF 25V X7R 0402 (lagre V = ofta mer i lager)"),
    ("C3", "100nF 0402", "0402", C04, "CL05B104KP5NNNC", "Samsung", "MLCC 100nF 10V X7R 0402 (basic-lib high-runner)"),
    ("C4", "100nF 0402", "0402", C04, "GRM155R71H104KE14D", "Murata", "MLCC 100nF 50V X7R 0402"),
    ("C5", "100nF 0402", "0402", C04, "GRM155R71C104KA88D", "Murata", "MLCC 100nF 16V X7R 0402 (high-runner)"),
    ("C6", "100nF 0402", "0402", C04, "CC0402KRX7R7BB104", "Yageo", "MLCC 100nF 16V X7R 0402"),
    ("C7", "100nF 0402", "0402", C04, "CC0402KRX7R9BB104", "Yageo", "MLCC 100nF 6.3V X7R 0402 (billigast)"),
    ("C8", "100nF 0402", "0402", C04, "0402B104K500CT", "Walsin", "MLCC 100nF 50V X7R 0402 (basic-lib)"),
    ("C9", "100nF 0402", "0402", C04, "C1005X7R1H104K050BB", "TDK", "MLCC 100nF 50V X7R 0402"),
    ("C10", "100nF 0402", "0402", C04, "C0402C104K4RACTU", "Kemet", "MLCC 100nF 16V X7R 0402"),
    ("C11", "100nF 0402", "0402", C04, "0402B104K500NT", "Fenghua", "MLCC 100nF 50V X7R 0402 (kinesisk basic-lib, billig)"),
    ("C12", "100nF 0402", "0402", C04, "GRM155R61A104KA01D", "Murata", "MLCC 100nF 10V X5R 0402 (litet/billigt)"),
    ("C13", "100nF 0402", "0402", C04, "04025C104KAT2A", "Kyocera AVX", "MLCC 100nF 50V X7R 0402"),
    ("C14", "100nF 0402", "0402", C04, "CL05F104ZO5NNNC", "Samsung", "MLCC 100nF 16V Y5V 0402 (sist-utvag, los tol)"),
    # referens-baslinje: 100nF 0805 (redan IN STOCK) — jamfor lager/pris mot 0402
    ("C15", "100nF 0805", "0805", C08, "CL21B104KBCNNNC", "Samsung", "MLCC 100nF 50V X7R 0805 — REDAN IN STOCK (referens)"),
    # === Ovriga lang-lead / manuellt-offererade delar — passa pa att lager-kolla ===
    ("R1", "0R2 2512", "2512", R25, "PE2512FKE070R200L", "Yageo", "Res 0.2R 1% 2W 2512 (CC-sense) — manuell offert idag"),
    ("R2", "0R2 2512", "2512", R25, "WSL2512R2000FEA", "Vishay", "Res 0.2R 1% 1W 2512 (Kelvin) — in-stock-alt"),
    ("R3", "0R2 2512", "2512", R25, "CRL2512-FW-R200ELF", "Bourns", "Res 0.2R 1% 2W 2512 — in-stock-alt"),
    ("R4", "10R 2512", "2512", R25, "CRCW251210R0FKEGHP", "Vishay", "Res 10R 1% 2W 2512 (LED-serie effekt)"),
    ("L1", "4.7uH FNR5040", "FNR5040", L50, "FNR5040320R47M", "Changjiang", "Induktor 4.7uH 5x5 (buck) — manuell offert idag"),
    ("L2", "4.7uH FNR5040", "FNR5040", L50, "SWPA5040S4R7MT", "Sunlord", "Induktor 4.7uH 5x5 (buck) — in-stock-alt"),
    ("FB1", "PTC 3A 1812", "1812", PTC18, "MF-MSMF300/16-2", "Bourns", "Aterstallb. sakring 3A-hold 16V 1812 — manuell offert"),
    ("FB2", "PTC 3A 1812", "1812", PTC18, "1812L300/16MR", "Littelfuse", "Aterstallb. sakring 3A-hold 16V 1812 — in-stock-alt"),
]

COLS, COLP, ROWP = 7, 17.0, 22.0
X0 = -(COLS - 1) * COLP / 2
ROWS = (len(CANDS) + COLS - 1) // COLS
Y0 = (ROWS - 1) * ROWP / 2 + 5


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def text(b, x, y, s, h=1.0, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.2 if bold else 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); b.Add(t)


def build_board():
    b = pcbnew.BOARD()
    for i, (ref, val, pkg, (lib, fpn), mpn, mfr, desc) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = pcbnew.FootprintLoad(lib, fpn)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.SetPosition(V(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 4.3, ref, 1.0, bold=True)
        text(b, x, y - 3.8, pkg, 0.75)
        text(b, x, y - 5.2, mfr, 0.7)

    W, H = COLS * COLP + 6, ROWS * ROWP + 18
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  KONDENSATOR / LAGER-SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - 14x 100nF 0402 + lang-lead-delar for NextPCB lager-koll", 0.95)
    text(b, 0, y0 + 4, "Ladda upp BOM -> valj IN-STOCK 100nF 0402 (basic-lib) -> uppdatera gen_nextpcb.py -> kapa lead", 0.9)
    text(b, 0, y0 + 2, "C1 = nuvarande (12-20 d lead). Sok en C2-C14 som ar In Stock. Aven 0R2/10R/4.7uH/PTC.", 0.85)

    pcbnew.SaveBoard(f"{ROOT}/hardware/cap-sampler.kicad_pcb", b)
    print(f"hardware/cap-sampler.kicad_pcb: {len(CANDS)} delar, board {W:.0f}x{H:.0f} mm")
    return b


HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]


def write_bom(path):
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR):
        ws.write(0, c, h, bold)
    for row, (ref, val, pkg, (lib, fpn), mpn, mfr, desc) in enumerate(CANDS, start=1):
        ws.write(row, 0, ref); ws.write(row, 1, 1)
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, fpn)
        ws.write(row, 5, desc); ws.write(row, 6, "")
        ws.write(row, 7, "LAGER-KOLL: bekrafta In Stock + ledtid + pris (kortet bestalls EJ)")
    wb.save(path)
    print(f"{path}: {len(CANDS)} rader")


def write_centroid(board, path):
    aux = board.GetDesignSettings().GetAuxOrigin()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for f in board.GetFootprints():
            p = f.GetPosition()
            x = (p.x - aux.x) / 1e6
            y = -(p.y - aux.y) / 1e6
            w.writerow([f.GetReference(), f"{x:.4f}", f"{y:.4f}", "Top", f"{f.GetOrientationDegrees():.4f}"])
    print(f"{path}: centroid")


def export_gerbers(pcb, outdir, zippath):
    os.system(f"rm -rf {outdir} && mkdir -p {outdir}")
    subprocess.run(["kicad-cli", "pcb", "export", "gerbers", "-o", outdir + "/", pcb],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["kicad-cli", "pcb", "export", "drill", "-o", outdir + "/", pcb],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    subprocess.run(["bash", "-c", f"cd {outdir} && zip -q -r - . > {zippath}"])
    print(f"{zippath}: gerbers")


def main():
    board = build_board()
    out = f"{ROOT}/leverans/cap-sampler"
    os.makedirs(out, exist_ok=True)
    pcb = f"{ROOT}/hardware/cap-sampler.kicad_pcb"
    write_bom(f"{out}/cap-sampler-bom.xls")
    write_centroid(board, f"{out}/cap-sampler-centroid.csv")
    export_gerbers(pcb, "/tmp/gbcap", f"{out}/cap-sampler-gerbers.zip")


if __name__ == "__main__":
    main()
