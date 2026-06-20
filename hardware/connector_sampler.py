#!/usr/bin/env python3
"""STRILAS — KONTAKT/HEADER-SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Inventerar de gemensamma kontakterna över alla kort (2.54 mm headers/socklar, JST-PH/XH/GH,
XT30) i de EXAKTA footprints korten använder. Två syften:
  1) lager-koll: ladda upp BOM → se vilka NextPCB har i lager,
  2) MONTERINGSTEST: här är de markerade för montering (INTE DNP) → ser om NextPCB kan
     sourca + montera (våg/selektiv THT-lödning) kontakterna åt oss, så vi slipper handlöda
     dem på de riktiga korten.

Footprint-inventering (från *.net): se tabell i leverans/kontakt-sampler/LÄS-MIG.md.
Kortet beställs/tillverkas EJ.

Kör: python3 hardware/connector_sampler.py
"""
import os, csv, subprocess, pcbnew, xlwt

MM = pcbnew.FromMM
OX, OY = 150.0, 120.0
KI = "/usr/share/kicad/footprints"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PS = f"{KI}/Connector_PinSocket_2.54mm.pretty"
PH = f"{KI}/Connector_PinHeader_2.54mm.pretty"
JS = f"{KI}/Connector_JST.pretty"
AM = f"{KI}/Connector_AMASS.pretty"

# (ref, kort-etikett, lib, footprint, MPN, tillverkare, beskrivning, rot)
# rot=90 för de långa 2.54-listerna (padrad ligger längs Y → roteras till liggande)
CANDS = [
    # --- 2.54 mm hona-socklar (P4-kantsocklar, kraft-tapp, breakout) ---
    ("J1", "Hona 1x3", PS, "PinSocket_1x03_P2.54mm_Vertical", "PPTC031LFBN-RC", "Sullins", "Hona 1x3 2.54 THT — kraft-tapp 3V3/GND", 90),
    ("J2", "Hona 1x7", PS, "PinSocket_1x07_P2.54mm_Vertical", "PPTC071LFBN-RC", "Sullins", "Hona 1x7 2.54 THT — XIAO-S3 / amp-/mik-breakout", 90),
    ("J3", "Hona 1x14", PS, "PinSocket_1x14_P2.54mm_Vertical", "PPTC141LFBN-RC", "Sullins", "Hona 1x14 2.54 THT — P4 edge A", 90),
    ("J4", "Hona 1x15", PS, "PinSocket_1x15_P2.54mm_Vertical", "PPTC151LFBN-RC", "Sullins", "Hona 1x15 2.54 THT — P4 edge", 90),
    ("J5", "Hona 1x20", PS, "PinSocket_1x20_P2.54mm_Vertical", "PPTC201LFBN-RC", "Sullins", "Hona 1x20 2.54 THT — P4-WIFI6 edge A/B (4 st/kort)", 90),
    # --- 2.54 mm stift-headers (breakout-moduler) ---
    ("J6", "Stift 1x6", PH, "PinHeader_1x06_P2.54mm_Vertical", "PREC006SAAN-RC", "Sullins", "Stift 1x6 2.54 THT — I2S MEMS-mik-breakout", 90),
    ("J7", "Stift 1x7", PH, "PinHeader_1x07_P2.54mm_Vertical", "PREC007SAAN-RC", "Sullins", "Stift 1x7 2.54 THT — MAX98357A-amp-breakout", 90),
    # --- JST-PH 2.0 mm vertikal (B-typ) ---
    ("J8", "PH 2p vert", JS, "JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical", "B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2p vertikal — trigger/rack/mag-switchar", 0),
    ("J9", "PH 3p vert", JS, "JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical", "B3B-PH-K-S(LF)(SN)", "JST", "JST-PH 3p vertikal — recoil-styrning", 0),
    ("J10", "PH 4p vert", JS, "JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical", "B4B-PH-K-S(LF)(SN)", "JST", "JST-PH 4p vertikal — NFC PN532 I2C", 0),
    # --- JST-PH 2.0 mm sido (S-typ, låg bygghöjd) ---
    ("J11", "PH 2p sido", JS, "JST_PH_S2B-PH-K_1x02_P2.00mm_Horizontal", "S2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2p sido (S) — högtalare/PTT/bom-mik", 0),
    ("J12", "PH 5p sido", JS, "JST_PH_S5B-PH-K_1x05_P2.00mm_Horizontal", "S5B-PH-K-S(LF)(SN)", "JST", "JST-PH 5p sido (S) — aim-patch", 0),
    ("J13", "PH 6p sido", JS, "JST_PH_S6B-PH-K_1x06_P2.00mm_Horizontal", "S6B-PH-K-S(LF)(SN)", "JST", "JST-PH 6p sido (S) — zon/patch (10 st)", 0),
    # --- JST-XH 2.5 mm (batteri) ---
    ("J14", "XH 2p sido", JS, "JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal", "S2B-XH-A(LF)(SN)", "JST", "JST-XH 2p sido — 2S-batteri", 0),
    # --- JST-GH 1.25 mm SMD (finpitch — redan SMT-placerad) ---
    ("J15", "GH 6p SMD", JS, "JST_GH_SM06B-GHS-TB_1x06-1MP_P1.25mm_Horizontal", "SM06B-GHS-TB(LF)(SN)", "JST", "JST-GH 6p SMD — RTK-puck (helmet J1)", 0),
    ("J16", "GH 8p SMD", JS, "JST_GH_SM08B-GHS-TB_1x08-1MP_P1.25mm_Horizontal", "SM08B-GHS-TB(LF)(SN)", "JST", "JST-GH 8p SMD — ZED-F9P RTK", 0),
    # --- XT30 kraft (batteri-in) ---
    ("J17", "XT30 kraft", AM, "AMASS_XT30PW-M_1x02_P2.50mm_Horizontal", "XT30PW-M", "AMASS", "XT30PW-M kraftkontakt — batteri-in", 0),
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


def place(b, lib, fpn, x, y, rot):
    fp = pcbnew.FootprintLoad(lib, fpn)
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(rot)
    pads = list(fp.Pads())
    cx = sum(p.GetPosition().x for p in pads) // len(pads)
    cy = sum(p.GetPosition().y for p in pads) // len(pads)
    tgt = V(x, y)
    fp.Move(pcbnew.VECTOR2I(tgt.x - cx, tgt.y - cy))   # centrera pad-tyngdpunkt på (x,y)
    return fp


def build_board():
    b = pcbnew.BOARD()
    for i, (ref, lbl, lib, fpn, mpn, mfr, desc, rot) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = place(b, lib, fpn, x, y, rot)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 6.6, f"{ref}  {lbl}", 1.0, bold=True)
        text(b, x, y - 7.0, mpn, 0.7)

    W, H = COLS * COLP + 8, ROWS * ROWP + 20
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  KONTAKT / HEADER-SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - gemensamma 2.54-headers + JST-PH/XH/GH + XT30", 0.95)
    text(b, 0, y0 + 4, "MONTERINGSTEST: kontakterna ar markerade FOR montering (ej DNP) -> ser om NextPCB", 0.9)
    text(b, 0, y0 + 2, "kan sourca + montera dem -> da slipper vi handloda dem pa de riktiga korten", 0.9)

    pcbnew.SaveBoard(f"{ROOT}/hardware/connector-sampler.kicad_pcb", b)
    print(f"hardware/connector-sampler.kicad_pcb: {len(CANDS)} kontakter, board {W:.0f}x{H:.0f} mm")
    return b


HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]


def write_bom(path):
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR):
        ws.write(0, c, h, bold)
    for row, (ref, lbl, lib, fpn, mpn, mfr, desc, rot) in enumerate(CANDS, start=1):
        ws.write(row, 0, ref); ws.write(row, 1, 1)
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, fpn)
        ws.write(row, 5, desc); ws.write(row, 6, "")   # EJ DNP — NextPCB ska montera (test)
        ws.write(row, 7, "MONTERAS av NextPCB (kontakt-monteringstest) — bekrafta In Stock + att THT-montering gar")
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
    print(f"{path}: centroid ({board.GetFootprints().GetCount() if hasattr(board.GetFootprints(),'GetCount') else len(list(board.GetFootprints()))} placeringar)")


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
    out = f"{ROOT}/leverans/kontakt-sampler"
    os.makedirs(out, exist_ok=True)
    pcb = f"{ROOT}/hardware/connector-sampler.kicad_pcb"
    write_bom(f"{out}/kontakt-sampler-bom.xls")
    write_centroid(board, f"{out}/kontakt-sampler-centroid.csv")
    export_gerbers(pcb, "/tmp/gbconn", f"{out}/kontakt-sampler-gerbers.zip")


if __name__ == "__main__":
    main()
