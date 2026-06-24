#!/usr/bin/env python3
"""STRILAS — 10R 2512-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

10R 2512 är LED-serie-effektmotståndet för 860 nm-konstellationen (helmet-mb 6×, vest-mb-patch 6×).
Nuvarande Vishay CRCW251210R0FKEGHP (2W HP) ligger på 7–18 d lead + ~$0,95/st → vill hitta en
IN STOCK-ersättare. EFFEKT-KRAV: ~2,5 W topp @0,5 A, ~50% duty → ~1,25 W medel → **2W krävs**
(1W-jellybean = marginellt, bara om duty hålls lågt). Detta kort bär 2W-HP- OCH 1W-standard-
kandidater så NextPCB-lagret avgör vad vi kan välja (effekt vs tillgänglighet).

Ladda upp `r2512-sampler-bom.xls` → se In Stock → välj (helst 2W In Stock; annars billig 1W
In Stock + sänkt duty, eller 2× parallell). **Kortet beställs/tillverkas EJ** — bara lager-koll.

Kör: python3 hardware/r2512_sampler.py
"""
import os, csv, subprocess, pcbnew, xlwt

MM = pcbnew.FromMM
OX, OY = 150.0, 100.0
KI = "/usr/share/kicad/footprints"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
R25 = (f"{KI}/Resistor_SMD.pretty", "R_2512_6332Metric")

# (ref, etikett, MPN, tillverkare, beskrivning)  — alla 10R 2512, footprint R_2512_6332Metric
CANDS = [
    ("R1", "2W HP 1%", "CRCW251210R0FKEGHP", "Vishay", "Res 10R 1% 2W 2512 HP — NUVARANDE (7-18 d lead, byts)"),
    ("R2", "2W HP 5%", "CRCW251210R0JNEGHP", "Vishay", "Res 10R 5% 2W 2512 HP (billigare tol, samma effekt)"),
    ("R3", "2W HP 1%", "RCV2512100RJNEA", "Vishay", "Res 10R 5% 2W 2512 (RCV power, alt-serie)"),
    ("R4", "2W 1%", "PA2512FKF7W10R0L", "Yageo", "Res 10R 1% 2W 2512 (PA power-serie)"),
    ("R5", "2W 1%", "ERJ1TRQF10R0U", "Panasonic", "Res 10R 1% 2W 2512 anti-surge"),
    ("R6", "2W 1%", "CRM2512-FX-10R0ELF", "Bourns", "Res 10R 1% 2W 2512 (CRM power)"),
    ("R7", "1W 1%", "RC2512FK-0710RL", "Yageo", "Res 10R 1% 1W 2512 jellybean (in-stock-trolig; OBS 1W < 1,25W medel)"),
    ("R8", "1W 5%", "RC2512JK-0710RL", "Yageo", "Res 10R 5% 1W 2512 billigast jellybean (1W)"),
    ("R9", "1W 1%", "2512WGF10R0T5E", "Uniroyal", "Res 10R 1% 1W 2512 (kinesisk basic-lib, billig; 1W)"),
    ("R10", "1W 1%", "WR12X10R0FTL", "Walsin", "Res 10R 1% 1W 2512 (basic-lib; 1W)"),
    ("R11", "1W 1%", "ESR25JZPF10R0", "ROHM", "Res 10R 1% 1W 2512 (1W)"),
]

COLS, COLP, ROWP = 6, 18.0, 22.0
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
    lib, fpn = R25
    for i, (ref, lbl, mpn, mfr, desc) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = pcbnew.FootprintLoad(lib, fpn)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.SetPosition(V(x, y))
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 4.5, ref, 1.0, bold=True)
        text(b, x, y - 4.2, lbl, 0.85, bold=True)
        text(b, x, y - 5.7, mfr, 0.7)

    W, H = COLS * COLP + 6, ROWS * ROWP + 18
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  10R 2512-SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - 10R 2512 effekt-R (LED-serie) for NextPCB lager-koll", 0.95)
    text(b, 0, y0 + 4, "Ladda upp BOM -> valj IN-STOCK. Effektkrav ~1,25W medel -> helst 2W; 1W bara vid lag duty", 0.9)
    text(b, 0, y0 + 2, "R1 = nuvarande (7-18 d). Sok 2W In Stock; annars billig 1W In Stock + sankt duty / 2x parallell", 0.82)

    pcbnew.SaveBoard(f"{ROOT}/hardware/r2512-sampler.kicad_pcb", b)
    print(f"hardware/r2512-sampler.kicad_pcb: {len(CANDS)} delar, board {W:.0f}x{H:.0f} mm")
    return b


HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]


def write_bom(path):
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR):
        ws.write(0, c, h, bold)
    for row, (ref, lbl, mpn, mfr, desc) in enumerate(CANDS, start=1):
        ws.write(row, 0, ref); ws.write(row, 1, 1)
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, "R_2512_6332Metric")
        ws.write(row, 5, desc); ws.write(row, 6, "")
        ws.write(row, 7, "LAGER-KOLL: bekrafta In Stock + ledtid + pris + effekt-rating (kortet bestalls EJ)")
    wb.save(path)
    print(f"{path}: {len(CANDS)} rader")


def write_centroid(board, path):
    aux = board.GetDesignSettings().GetAuxOrigin()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
        for f in board.GetFootprints():
            p = f.GetPosition()
            x = (p.x - aux.x) / 1e6; y = -(p.y - aux.y) / 1e6
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
    out = f"{ROOT}/leverans/r2512-sampler"
    os.makedirs(out, exist_ok=True)
    pcb = f"{ROOT}/hardware/r2512-sampler.kicad_pcb"
    write_bom(f"{out}/r2512-sampler-bom.xls")
    write_centroid(board, f"{out}/r2512-sampler-centroid.csv")
    export_gerbers(pcb, "/tmp/gbr2512", f"{out}/r2512-sampler-gerbers.zip")


if __name__ == "__main__":
    main()
