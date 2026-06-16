#!/usr/bin/env python3
"""STRILAS → NextPCB tillverknings-underlag (BOM + centroid) per tillverkat kort.
Skriver, för optik och fire-control (P4 = köpt Waveshare, EJ tillverkad):
  nextpcb/<kort>-bom.xls       — NextPCB-BOM (8 mall-kolumner)
  nextpcb/<kort>-centroid.csv  — pick-and-place (Designator,Mid X,Mid Y,Layer,Rotation)
Monteringshål exkluderas (kort-feature, ej placerad komponent).
MPN = riktiga, beställbara delar; generiska passiva får representativa MPN att
verifiera/byta mot NextPCB:s basbibliotek. Spänning/effekt verifieras (se NOTE)."""
import re, csv, pcbnew, xlwt
from collections import defaultdict

# (value) -> (MPN, Manufacturer, Description, ProcurementType, CustomerNote)
MPN = {
    # --- passiva (representativa; verifiera basbibliotek) ---
    "100nF": ("CL05B104KO5NNNC", "Samsung", "MLCC 100nF 50V X7R", "", ""),
    "1uF":   ("CL21B105KBFNNNE", "Samsung", "MLCC 1uF 50V X7R 0805", "", ""),
    "1uF@0402":("CL05A105KP5NNNC", "Samsung", "MLCC 1uF 10V X5R 0402", "", ""),
    "10uF":  ("CL31A106KBHNNNE", "Samsung", "MLCC 10uF 25V X5R 1206", "", ""),
    "100uF": ("GRM32ER61E107ME20L", "Murata", "MLCC 100uF 25V X5R 1210", "", ""),
    "100k":  ("RC0805FR-07100KL", "Yageo", "Res 100k 1% 1/8W 0805", "", ""),
    "220R":  ("RC0805FR-07220RL", "Yageo", "Res 220R 1% 1/8W 0805", "", ""),
    "4k7":   ("RC0805FR-074K7L", "Yageo", "Res 4.7k 1% 1/8W 0805", "", ""),
    "3R3_2W":("CRCW25123R30FKEGHP", "Vishay", "Res 3.3R 1% 2W 2512 (HP)", "", "NOTE: 2W-rating krävs (IR-strömtak)"),
    # --- halvledare ---
    "AO3401":      ("AO3401A", "Alpha & Omega", "P-MOSFET -30V SOT-23 (rev-pol-skydd)", "", ""),
    "AO3400":      ("AO3400A", "Alpha & Omega", "N-MOSFET 30V SOT-23 (IR-driver 56kHz)", "", ""),
    "SMBJ12A":     ("SMBJ12A", "Littelfuse", "TVS unidir 12V SMB", "", ""),
    "SFH4725S_940nm":("SFH 4725S", "ams OSRAM", "IR-emitter 940nm OSLON Black", "", "Bestyckas av NextPCB (matchad, ~10 dgr)"),
    "PTC_1A":      ("MF-MSMF075/16X-2", "Bourns", "PTC resättbar 0.75A-hold 16V 1206", "", "NOTE: verifiera hold-ström mot systemtopp"),
    "ICM-42670-P": ("ICM-42670-P", "TDK InvenSense", "6-axlig IMU (SPI/I2C) LGA-14, IN-STOCK", "", ""),
    # --- kontakter (genomplåt → selektiv/handlödning) ---
    "P4-socket (edge B)":      ("PPTC141LFBN-RC", "Sullins", "Stiftsockel 1x14 2.54mm THT", "", "TH: P4-stack"),
    "P4-socket (edge A)":      ("PPTC121LFBN-RC", "Sullins", "Stiftsockel 1x12 2.54mm THT", "", "TH: P4-stack"),
    "edge-B kraft-tapp 3V3+GND":("PPTC031LFBN-RC", "Sullins", "Stiftsockel 1x03 2.54mm THT", "", "TH: kraft-tapp"),
    "2S batteri (JST-XH)":     ("S2B-XH-A(LF)(SN)", "JST", "JST-XH 2-pol header 2.5mm THT", "", "TH"),
    "TRIGGER":     ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "RACK_SW":     ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "MAG_REL_SW":  ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "MAGWELL_SW":  ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "recoil-styrning":("B3B-PH-K-S(LF)(SN)", "JST", "JST-PH 3-pol header 2.0mm THT", "", "TH"),
    "NFC PN532 (I²C)":("B4B-PH-K-S(LF)(SN)", "JST", "JST-PH 4-pol header 2.0mm THT", "", "TH"),
}

def netvals(path):
    t = open(path).read(); seg = t[t.find("(components"):t.find("(libparts")]
    out = {}
    for blk in re.split(r"\(comp\b", seg)[1:]:
        r = re.search(r'\(ref "([^"]+)"\)', blk); v = re.search(r'\(value "([^"]*)"\)', blk)
        if r: out[r.group(1)] = v.group(1) if v else ""
    return out

def refkey(r):
    m = re.match(r'([A-Za-z]+)(\d+)', r); return (m.group(1), int(m.group(2))) if m else (r, 0)

HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]

def build(board_pcb, board_net, out_xls):
    vals = netvals(board_net)
    b = pcbnew.LoadBoard(board_pcb)
    groups = defaultdict(list)   # (value) -> [(ref, package)]
    pkg_of = {}
    for f in b.GetFootprints():
        ref = f.GetReference()
        fp = str(f.GetFPID().GetLibItemName())
        if "MountingHole" in fp:        # kort-feature, ej placerad komponent
            continue
        val = vals.get(ref, f.GetValue())
        groups[val].append(ref); pkg_of[ref] = fp
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR): ws.write(0, c, h, bold)
    row = 1
    for val in sorted(groups, key=lambda v: groups[v][0] if False else v):
        refs = sorted(groups[val], key=refkey)
        pkg = pkg_of[refs[0]]
        key = val
        if val == "1uF" and "0402" in pkg: key = "1uF@0402"   # paket-specifik MPN
        mpn, mfr, desc, proc, note = MPN.get(key, ("", "", val, "", "SAKNAR MPN — fyll i"))
        ws.write(row, 0, ",".join(refs)); ws.write(row, 1, len(refs))
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, pkg)
        ws.write(row, 5, desc); ws.write(row, 6, proc); ws.write(row, 7, note)
        row += 1
    wb.save(out_xls)
    print(f"  {out_xls}: {row-1} BOM-rader ({sum(len(v) for v in groups.values())} komponenter)")

def centroid(board_pcb, out_csv):
    b = pcbnew.LoadBoard(board_pcb)
    ox, oy = b.GetDesignSettings().GetAuxOrigin()
    rows = []
    for f in b.GetFootprints():
        if "MountingHole" in str(f.GetFPID().GetLibItemName()): continue
        p = f.GetPosition()
        x = (p.x - ox) / 1e6; y = -(p.y - oy) / 1e6   # mm, Y upp (EDA-konvention)
        rows.append([f.GetReference(), f"{x:.4f}", f"{y:.4f}",
                     "Bottom" if f.IsFlipped() else "Top", f"{f.GetOrientationDegrees():.2f}"])
    rows.sort(key=lambda r: refkey(r[0]))
    head = ["Designator", "Mid X(mm)", "Mid Y(mm)", "Layer", "Rotation"]
    with open(out_csv, "w", newline="") as fh:
        w = csv.writer(fh); w.writerow(head); w.writerows(rows)
    # NextPCB-uppladdning kräver zip/rar/xls/xlsx → skriv även .xls
    out_xls = out_csv.rsplit(".", 1)[0] + ".xls"
    wb = xlwt.Workbook(); ws = wb.add_sheet("Centroid")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(head): ws.write(0, c, h, bold)
    for i, r in enumerate(rows, 1):
        ws.write(i, 0, r[0])
        for c in (1, 2, 4): ws.write(i, c, float(r[c]))
        ws.write(i, 3, r[3])
    wb.save(out_xls)
    print(f"  {out_csv} + {out_xls}: {len(rows)} placeringar")

if __name__ == "__main__":
    import os; os.makedirs("nextpcb", exist_ok=True)
    print("OPTIK:"); build("weapon-module.kicad_pcb", "weapon-module.net", "nextpcb/optik-bom.xls")
    centroid("weapon-module.kicad_pcb", "nextpcb/optik-centroid.csv")
    print("FIRE-CONTROL:"); build("firecontrol.kicad_pcb", "firecontrol.net", "nextpcb/firecontrol-bom.xls")
    centroid("firecontrol.kicad_pcb", "nextpcb/firecontrol-centroid.csv")
