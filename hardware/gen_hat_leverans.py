#!/usr/bin/env python3
"""STRILAS — VAPEN-HAT tillverknings-underlag (BOM + centroid) ur routat kort + netlista.
Centroid = endast SMT (NextPCB placerar); THT-kontakter (40-pin HONA-header J1 + alla JST) är
KUND-handlödda → ej i centroid (DNP i BOM, med som beställningsreferens). Gerbers/STEP görs av
route_weapon_hat3.py. Kör:  python3 hardware/gen_hat_leverans.py
"""
import os, csv, re, pcbnew, xlwt
OX, OY = 150.0, 120.0
PCB = "hardware/weapon-hat.kicad_pcb"; NET = "hardware/weapon-hat.net"

# ref → (värde, footprint) ur netlistan
comps = {}
txt = open(NET).read()
for m in re.finditer(r'\(comp\s+\(ref "([^"]+)"\)\s+\(value "([^"]*)"\)(.*?)(?=\(comp\s+\(ref|\(libparts|\Z)', txt, re.S):
    ref, val, rest = m.groups()
    fm = re.search(r'\(footprint "([^"]+)"', rest)
    comps[ref] = (val, fm.group(1) if fm else "")

b = pcbnew.LoadBoard(PCB)
THT = lambda fp: fp.startswith(("Connector_JST", "Connector_PinSocket", "Connector_PinHeader"))
SKIP = lambda ref, fp: ref.startswith("MH") or "MountingHole" in fp   # monteringshål → ej i centroid/BOM

# ---- centroid: SMT-delar på framsidan (THT-kontakter exkluderas, handlödda) ----
os.makedirs("leverans/weapon-hat", exist_ok=True)
rows = []
for f in b.GetFootprints():
    ref = f.GetReference(); fp = comps.get(ref, ("", ""))[1]
    if THT(fp) or SKIP(ref, f.GetFPID().GetUniStringLibId()): continue
    p = f.GetPosition()
    rows.append((ref, p.x/1e6-OX, OY-p.y/1e6, "bottom" if f.IsFlipped() else "top", f.GetOrientationDegrees()))
rows.sort(key=lambda r: (r[0][0], int(re.sub(r"\D", "", r[0]) or 0)))
with open("leverans/weapon-hat/weapon-hat-centroid.csv", "w", newline="") as fh:
    w = csv.writer(fh); w.writerow(["Designator", "Mid X", "Mid Y", "Layer", "Rotation"])
    for ref, x, y, lay, rot in rows:
        w.writerow([ref, f"{x:.3f}", f"{y:.3f}", lay, f"{rot:.1f}"])
print(f"centroid: {len(rows)} SMT-delar (THT-kontakter exkluderade)")

# ---- BOM: gruppera per (värde, footprint) ----
COLS = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
        "Package/Footprint", "Description", "Procurement Type", "Customer Note"]
DESC = {  # värde → (MPN, tillv, beskrivning)
 "ICM-42688-P": ("ICM-42688-P", "TDK InvenSense", "6-axlig IMU (SPI)"),
 "IIM-42653": ("IIM-42653", "TDK InvenSense", "6-axlig industri-IMU (I²C, 0x68/0x69)"),
 "ADS1115": ("ADS1115IDGSR", "TI", "16-bit I²C-ADC (batteri-sense)"),
 "OPA171": ("OPA171", "TI", "op-amp"),
 "AOD4185": ("AOD4185", "AOS", "P-FET 40V/40A 15mΩ DPAK (omvänd-polaritetsskydd, delad VBAT-väg)"),
 "AP63203WU 2S→5V 3A": ("AP63203WU", "Diodes", "2S→5V 3A synkron buck (FB-delare 52k3/10k)"),
 "3.3uH/4A": ("MD-5050-3R3", "Taiyo-Yuden", "buck-induktor 3,3µH 4A (5×5)"),
 "SMBJ12A": ("SMBJ12A", "Littelfuse", "TVS 12 V (VBAT)"),
 "SMAJ5.0A": ("SMAJ5.0A", "Littelfuse", "TVS 5 V (5V-rail/back-feed-skydd)"),
 "AT24C32 HAT-ID EEPROM 0x50": ("AT24C32D-SSHM-T", "Microchip", "HAT-ID EEPROM 32 kbit I²C @0x50"),
 "PTC_3A": ("MF-MSMF...", "Bourns", "PTC-säkring ~3 A (1812)"),
}
grp = {}
for ref, (val, fp) in comps.items():
    grp.setdefault((val, fp), []).append(ref)
def rk(r): return (r[0], int(re.sub(r"\D", "", r) or 0))
wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
for c, h in enumerate(COLS): ws.write(0, c, h)
r = 1
for (val, fp), refs in sorted(grp.items(), key=lambda kv: rk(sorted(kv[1], key=rk)[0])):
    refs = sorted(refs, key=rk)
    pkg = fp.split(":")[-1]
    mpn, mfr, desc = DESC.get(val, ("", "", ""))
    if not desc: desc = val
    note = ""
    if THT(fp):
        note = "Kund handlöder (THT) — DNP: NextPCB monterar EJ, ej i centroid. Med i BOM som referens."
        if "PinSocket" in fp: desc = "40-pin 2x20 HONA-sockel (baksida, centrum) → CM5-carrier"
    ws.write(r, 0, ",".join(refs)); ws.write(r, 1, str(len(refs)))
    ws.write(r, 2, mpn); ws.write(r, 3, mfr); ws.write(r, 4, pkg)
    ws.write(r, 5, desc); ws.write(r, 6, ""); ws.write(r, 7, note)
    r += 1
wb.save("leverans/weapon-hat/weapon-hat-bom.xls")
print(f"BOM: {r-1} rader → leverans/weapon-hat/")
