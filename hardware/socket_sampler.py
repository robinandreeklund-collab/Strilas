#!/usr/bin/env python3
"""STRILAS — 2.54 HONA-SOCKEL-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Sista kontakt-kategorin som ännu handlöds: 2.54 mm hona-socklar (P4-WIFI6 edge-socklar + kraft-
tapp + XIAO/breakout). I kontakt-samplern kom Sullins-MPN tillbaka Pending (ej i NextPCB auto-lib).
Detta kort bär samma footprints i FLERA märken (Ckmtw / Sullins / Samtec) och pinantal (1x03,
1x07, 1x14, 1x15, 1x20 — de som faktiskt sitter på korten) → ladda upp BOM, se vilket märke som
är In Stock, så kan NextPCB montera även dessa (då slipper vi handlöda P4-socklarna med).

Kortet beställs/tillverkas EJ.

Kör: python3 hardware/socket_sampler.py
"""
import os, csv, subprocess, pcbnew, xlwt

MM = pcbnew.FromMM
OX, OY = 150.0, 120.0
KI = "/usr/share/kicad/footprints"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = f"{KI}/Connector_PinSocket_2.54mm.pretty"

# (ref, kort-etikett, footprint, MPN, tillverkare, beskrivning)
CANDS = [
    ("J1", "1x3 hona", "PinSocket_1x03_P2.54mm_Vertical", "DS1023-1x3SF11", "Ckmtw", "Hona 1x3 2.54 THT — kraft-tapp (kinesisk basic-lib)"),
    ("J2", "1x3 hona", "PinSocket_1x03_P2.54mm_Vertical", "PPTC031LFBN-RC", "Sullins", "Hona 1x3 2.54 THT — kraft-tapp (kontroll: Sullins var Pending)"),
    ("J3", "1x7 hona", "PinSocket_1x07_P2.54mm_Vertical", "DS1023-1x7SF11", "Ckmtw", "Hona 1x7 2.54 THT — XIAO/breakout"),
    ("J4", "1x7 hona", "PinSocket_1x07_P2.54mm_Vertical", "PPTC071LFBN-RC", "Sullins", "Hona 1x7 2.54 THT — XIAO/breakout (kontroll)"),
    ("J5", "1x14 hona", "PinSocket_1x14_P2.54mm_Vertical", "DS1023-1x14SF11", "Ckmtw", "Hona 1x14 2.54 THT — P4 edge A (optik)"),
    ("J6", "1x14 hona", "PinSocket_1x14_P2.54mm_Vertical", "PPTC141LFBN-RC", "Sullins", "Hona 1x14 2.54 THT — P4 edge A (kontroll)"),
    ("J7", "1x15 hona", "PinSocket_1x15_P2.54mm_Vertical", "DS1023-1x15SF11", "Ckmtw", "Hona 1x15 2.54 THT — P4 edge (firecontrol)"),
    ("J8", "1x15 hona", "PinSocket_1x15_P2.54mm_Vertical", "PPTC151LFBN-RC", "Sullins", "Hona 1x15 2.54 THT — P4 edge (kontroll)"),
    ("J9", "1x20 hona", "PinSocket_1x20_P2.54mm_Vertical", "DS1023-1x20SF11", "Ckmtw", "Hona 1x20 2.54 THT — P4-WIFI6 edge A/B (helmet/vest-mb, 4 st)"),
    ("J10", "1x20 hona", "PinSocket_1x20_P2.54mm_Vertical", "PPTC201LFBN-RC", "Sullins", "Hona 1x20 2.54 THT — P4-WIFI6 edge (kontroll)"),
    ("J11", "1x20 hona", "PinSocket_1x20_P2.54mm_Vertical", "SSW-120-01-T-S", "Samtec", "Hona 1x20 2.54 THT — P4-WIFI6 edge (premium-referens)"),
]

COLS, COLP, ROWP = 2, 64.0, 20.0
X0 = -(COLS - 1) * COLP / 2
ROWS = (len(CANDS) + COLS - 1) // COLS
Y0 = (ROWS - 1) * ROWP / 2 + 4


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def text(b, x, y, s, h=1.0, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.2 if bold else 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); b.Add(t)


def place(b, fpn, x, y, rot=90):
    fp = pcbnew.FootprintLoad(PS, fpn)
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    pads = list(fp.Pads())
    cx = sum(p.GetPosition().x for p in pads) // len(pads)
    cy = sum(p.GetPosition().y for p in pads) // len(pads)
    tgt = V(x, y)
    fp.Move(pcbnew.VECTOR2I(tgt.x - cx, tgt.y - cy))   # centrera pad-tyngdpunkt
    return fp


def build_board():
    b = pcbnew.BOARD()
    for i, (ref, lbl, fpn, mpn, mfr, desc) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = place(b, fpn, x, y)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 6.6, f"{ref}  {lbl}", 1.0, bold=True)
        text(b, x, y - 7.0, f"{mfr}  {mpn}", 0.7)

    W, H = COLS * COLP + 8, ROWS * ROWP + 20
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  2.54 HONA-SOCKEL-SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - P4-edge/kraft-tapp/breakout 2.54 hona for NextPCB lager-koll", 0.92)
    text(b, 0, y0 + 4, "Ladda upp BOM -> se vilket marke (Ckmtw/Sullins/Samtec) ar In Stock -> da monteras P4-socklarna med", 0.88)
    text(b, 0, y0 + 2, "Sullins var Pending i kontakt-samplern. Soker auto-matchad In-Stock-hona i 1x3/1x7/1x14/1x15/1x20", 0.82)

    pcbnew.SaveBoard(f"{ROOT}/hardware/socket-sampler.kicad_pcb", b)
    print(f"hardware/socket-sampler.kicad_pcb: {len(CANDS)} socklar, board {W:.0f}x{H:.0f} mm")
    return b


HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]


def write_bom(path):
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR):
        ws.write(0, c, h, bold)
    for row, (ref, lbl, fpn, mpn, mfr, desc) in enumerate(CANDS, start=1):
        ws.write(row, 0, ref); ws.write(row, 1, 1)
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, fpn)
        ws.write(row, 5, desc); ws.write(row, 6, "")
        ws.write(row, 7, "LAGER-KOLL: vilket marke ar In Stock + kan THT-monteras (kortet bestalls EJ)")
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
    out = f"{ROOT}/leverans/socket-sampler"
    os.makedirs(out, exist_ok=True)
    pcb = f"{ROOT}/hardware/socket-sampler.kicad_pcb"
    write_bom(f"{out}/socket-sampler-bom.xls")
    write_centroid(board, f"{out}/socket-sampler-centroid.csv")
    export_gerbers(pcb, "/tmp/gbsock", f"{out}/socket-sampler-gerbers.zip")


if __name__ == "__main__":
    main()
