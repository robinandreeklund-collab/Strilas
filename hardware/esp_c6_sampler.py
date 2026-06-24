#!/usr/bin/env python3
"""STRILAS — ESP32-C6-MINI-1U SAMPLER (DEMO, EJ FÖR TILLVERKNING).

Vapnet (CM5) ska prata med väst/hjälm (ESP32-P4 + C6) över ESP-NOW. CM5:ans Broadcom-radio kan EJ
tala ESP-NOW → vi lägger en ESP32-C6 som UART-brygga på HAT:en (samma radio-familj som väst/hjälm).
Detta kort bär kandidat-ESP32-C6-modulerna i de FOOTPRINTS vi vill montera (MINI-1U/-1 + WROOM-1U/-1
som större reserv) över flash-/temp-varianter → ladda upp BOM, se vilken MPN NextPCB har In Stock +
kan SMT-montera, så monteras C6:an direkt på HAT:en (slipper handlöda / USB-dongle).

Footprints: strilas:ESP32-C6-MINI-1U / -MINI-1 (genererade ur databladet av gen_esp_c6_footprint.py),
WROOM = KiCad RF_Module:ESP32-S3-WROOM-1(U) (land-pattern-kompatibel med C6-WROOM-1(U)).

Kortet beställs/tillverkas EJ. Kör: python3 hardware/esp_c6_sampler.py
"""
import os, csv, subprocess, pcbnew, xlwt

MM = pcbnew.FromMM
OX, OY = 150.0, 120.0
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STRILAS = f"{ROOT}/hardware/strilas.pretty"
RFMOD = "/usr/share/kicad/footprints/RF_Module.pretty"

# (ref, etikett, lib, footprint, MPN, antenn, beskrivning)
CANDS = [
    ("U1", "MINI-1U N4", STRILAS, "ESP32-C6-MINI-1U", "ESP32-C6-MINI-1U-N4", "U.FL", "4 MB, -40~85C, U.FL extern antenn — STRILAS PRIMÄRVAL (antenn ut ur vapenhus)"),
    ("U2", "MINI-1U H4", STRILAS, "ESP32-C6-MINI-1U", "ESP32-C6-MINI-1U-H4", "U.FL", "4 MB, -40~105C, U.FL — hög-temp-variant"),
    ("U3", "MINI-1U H8", STRILAS, "ESP32-C6-MINI-1U", "ESP32-C6-MINI-1U-H8", "U.FL", "8 MB, -40~105C, U.FL — mer flash"),
    ("U4", "MINI-1 N4", STRILAS, "ESP32-C6-MINI-1", "ESP32-C6-MINI-1-N4", "PCB", "4 MB, -40~85C, on-board PCB-antenn — reserv om modulen får sitta vid kortkant"),
    ("U5", "MINI-1 H4", STRILAS, "ESP32-C6-MINI-1", "ESP32-C6-MINI-1-H4", "PCB", "4 MB, -40~105C, PCB-antenn — hög-temp"),
    ("U6", "MINI-1 H8", STRILAS, "ESP32-C6-MINI-1", "ESP32-C6-MINI-1-H8", "PCB", "8 MB, -40~105C, PCB-antenn — mer flash"),
    ("U7", "WROOM-1U N4", RFMOD, "ESP32-S3-WROOM-1U", "ESP32-C6-WROOM-1U-N4", "U.FL", "4 MB, U.FL — STÖRRE reserv-footprint om MINI ej i lager (18x25.5 mm)"),
    ("U8", "WROOM-1 N8", RFMOD, "ESP32-S3-WROOM-1", "ESP32-C6-WROOM-1-N8", "PCB", "8 MB, PCB-antenn — större reserv-footprint (18x25.5 mm)"),
]

COLS, COLP, ROWP = 2, 46.0, 36.0
X0 = -(COLS - 1) * COLP / 2
ROWS = (len(CANDS) + COLS - 1) // COLS
Y0 = (ROWS - 1) * ROWP / 2 + 2


def V(x, y):
    return pcbnew.VECTOR2I(int((OX + x) * 1e6), int((OY - y) * 1e6))


def text(b, x, y, s, h=1.0, bold=False):
    t = pcbnew.PCB_TEXT(b); t.SetText(s); t.SetLayer(pcbnew.F_SilkS); t.SetPosition(V(x, y))
    t.SetTextSize(pcbnew.VECTOR2I(MM(h), MM(h))); t.SetTextThickness(MM(0.2 if bold else 0.15))
    t.SetHorizJustify(pcbnew.GR_TEXT_H_ALIGN_CENTER); t.SetVertJustify(pcbnew.GR_TEXT_V_ALIGN_CENTER); b.Add(t)


def place(b, lib, fpn, x, y):
    fp = pcbnew.FootprintLoad(lib, fpn)
    fp.SetPosition(V(x, y)); fp.SetOrientationDegrees(0)
    pads = list(fp.Pads())
    cx = sum(p.GetPosition().x for p in pads) // len(pads)
    cy = sum(p.GetPosition().y for p in pads) // len(pads)
    tgt = V(x, y)
    fp.Move(pcbnew.VECTOR2I(tgt.x - cx, tgt.y - cy))   # centrera pad-tyngdpunkt
    return fp


def build_board():
    b = pcbnew.BOARD()
    for i, (ref, lbl, lib, fpn, mpn, ant, desc) in enumerate(CANDS):
        c, r = i % COLS, i // COLS
        x, y = X0 + c * COLP, Y0 - r * ROWP
        fp = place(b, lib, fpn, x, y)
        fp.SetReference(ref); fp.SetValue(mpn)
        fp.Reference().SetVisible(False); fp.Value().SetVisible(False)
        b.Add(fp)
        text(b, x, y + 14.5, f"{ref}  {lbl}", 1.1, bold=True)
        text(b, x, y - 14.5, mpn, 0.75)

    W, H = COLS * COLP + 10, ROWS * ROWP + 22
    x0, x1, y0, y1 = -W / 2, W / 2, -H / 2, H / 2
    for (ax, ay, bx, by) in ((x0, y0, x1, y0), (x1, y0, x1, y1), (x1, y1, x0, y1), (x0, y1, x0, y0)):
        s = pcbnew.PCB_SHAPE(b); s.SetShape(pcbnew.SHAPE_T_SEGMENT)
        s.SetStart(V(ax, ay)); s.SetEnd(V(bx, by)); s.SetLayer(pcbnew.Edge_Cuts); s.SetWidth(MM(0.15)); b.Add(s)
    text(b, 0, y1 - 4, "STRILAS  ESP32-C6  SAMPLER", 2.0, bold=True)
    text(b, 0, y1 - 7, "DEMO - EJ FOR TILLVERKNING - C6 ESP-NOW-brygga CM5<->vast/hjalm, monteras pa HAT", 0.9)
    text(b, 0, y0 + 4, "Ladda upp BOM -> se vilken ESP32-C6-MPN NextPCB har In Stock + kan SMT-montera -> da monteras C6 pa HAT", 0.85)
    text(b, 0, y0 + 2, "MINI-1U (U.FL) = primarval; MINI-1 (PCB-ant) reserv; WROOM = storre reserv-footprint", 0.82)

    pcbnew.SaveBoard(f"{ROOT}/hardware/esp-c6-sampler.kicad_pcb", b)
    print(f"hardware/esp-c6-sampler.kicad_pcb: {len(CANDS)} moduler, board {W:.0f}x{H:.0f} mm")
    return b


HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]


def write_bom(path):
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR):
        ws.write(0, c, h, bold)
    for row, (ref, lbl, lib, fpn, mpn, ant, desc) in enumerate(CANDS, start=1):
        ws.write(row, 0, ref); ws.write(row, 1, 1)
        ws.write(row, 2, mpn); ws.write(row, 3, "Espressif Systems"); ws.write(row, 4, fpn)
        ws.write(row, 5, desc); ws.write(row, 6, "")
        ws.write(row, 7, "LAGER-KOLL: vilken C6-MPN ar In Stock + SMT-monterbar (kortet bestalls EJ)")
    wb.save(path)
    print(f"{path}: {len(CANDS)} rader")


def write_centroid(board, path):
    aux = board.GetDesignSettings().GetAuxOrigin()
    with open(path, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Designator", "Mid X(mm)", "Mid Y(mm)", "Layer", "Rotation"])
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
    out = f"{ROOT}/leverans/esp-c6-sampler"
    os.makedirs(out, exist_ok=True)
    pcb = f"{ROOT}/hardware/esp-c6-sampler.kicad_pcb"
    write_bom(f"{out}/esp-c6-sampler-bom.xls")
    write_centroid(board, f"{out}/esp-c6-sampler-centroid.csv")
    export_gerbers(pcb, "/tmp/gbespc6", f"{out}/esp-c6-sampler-gerbers.zip")


if __name__ == "__main__":
    main()
