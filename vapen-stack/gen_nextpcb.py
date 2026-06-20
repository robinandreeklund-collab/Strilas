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
    # --- passiva: MPN bekräftade mot NextPCB lager-koll (common-sampler). Paket-specifika nycklar
    #     val@<paketstorlek> (0402/0805/1206/1210); build() väljer rätt. IN STOCK där ej annat anges. ---
    "100nF@0805": ("CL21B104KBCNNNC", "Samsung", "MLCC 100nF 50V X7R 0805 — IN STOCK", "", ""),
    "100nF@0402": ("GRM155R71H104KE14D", "Murata", "MLCC 100nF 50V X7R 0402 — IN STOCK (byt fr Samsung CL05B104KO5NNNC: 4-20 d lead → kapat; samma 50V X7R-spec, billigare). Lager-koll cap-sampler", "", ""),
    "100nF": ("CL21B104KBCNNNC", "Samsung", "MLCC 100nF 50V X7R 0805 — IN STOCK (default)", "", ""),
    "1uF@0805": ("GRM21BR61E105KA99L", "Murata", "MLCC 1uF 25V X5R 0805 (high-runner, byt fr utgången CL21A105KAFNNNG)", "", ""),
    "1uF@0402": ("CL05A105KP5NNNC", "Samsung", "MLCC 1uF 10V X5R 0402 — IN STOCK", "", ""),
    "1uF":   ("GRM21BR61E105KA99L", "Murata", "MLCC 1uF 25V X5R 0805 (default)", "", ""),
    "10uF":  ("CL31A106KBHNNNE", "Samsung", "MLCC 10uF 25V X5R 1206 — IN STOCK", "", ""),
    "100uF": ("CL32A107MQVNNNE", "Samsung", "MLCC 100uF 25V X5R 1210 (byt fr ej-matchad GRM32ER61E107ME20L)", "", "verifiera vid manuell offert"),
    "100k":  ("RC0805FR-07100KL", "Yageo", "Res 100k 1% 1/8W 0805", "", ""),
    "220R":  ("RC0805FR-07220RL", "Yageo", "Res 220R 1% 1/8W 0805", "", ""),
    "4k7":   ("RC0805FR-074K7L", "Yageo", "Res 4.7k 1% 1/8W 0805", "", ""),
    "3R3_2W":("CRCW25123R30FKEGHP", "Vishay", "Res 3.3R 1% 2W 2512 (HP) — (legacy, ej i CC-driver)", "", ""),
    "0R2":   ("WSL2512R2000FEA", "Vishay", "Res 0.2R 1% 1W 2512 Kelvin-sense (lågt TCR) — CC-driver sätter ~1A (Vref/Rs)", "", "Sourcebar 4-7 d (byt fr Yageo PE2512FKE070R200L som krävde manuell offert). Precisions-sense → bättre ström-/ögonsäkerhetsstabilitet. P=I²R≈0,2W ≪ 1W"),
    "15k":   ("RC0805FR-0715KL", "Yageo", "Res 15k 1% 0805 — CC-referensdelare (övre)", "", ""),
    "1k":    ("RC0805FR-071KL", "Yageo", "Res 1k 1% 0805 — CC-referensdelare (undre)", "", ""),
    "100pF": ("CL21C101JBANNNC", "Samsung", "MLCC 100pF 50V C0G 0805 — slingkomp", "", ""),
    # --- halvledare ---
    "AO3401":      ("AO3401A", "Alpha & Omega", "P-MOSFET -30V SOT-23 (rev-pol-skydd)", "", ""),
    "AO3400":      ("AO3400A", "Alpha & Omega", "N-MOSFET 30V SOT-23 (väst LED-driver 56kHz)", "", ""),
    "AOD4184A":    ("AOD4184A", "Alpha & Omega", "N-MOSFET 40V logic-level DPAK (TO-252) — CC pass-FET (linjär)", "", ""),
    "OPA171":      ("OPA171AIDBVR", "Texas Instruments", "Op-amp 36V 3MHz SOT-23-5 — CC-sänkans regulator", "", ""),
    "SMBJ12A":     ("SMBJ12A", "Littelfuse", "TVS unidir 12V SMB", "", ""),
    "AOD4185A":    ("AOD4185A", "Alpha & Omega", "P-MOSFET -40V DPAK (TO-252) — rev-pol-skydd + lastbrytare (gate-styrd av/på)", "", ""),
    "47k":         ("RC0805FR-0747KL", "Yageo", "Res 47k 1% 0805 — batteri-sense-delare (undre)", "", ""),
    "Strombrytare (extern SPST -> gate)": ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol vertikal — extern strömbrytare (SPST → P-FET-gate)", "", "TH; brytare köps separat"),
    "SFH4725S_940nm":("SFH 4725S", "ams OSRAM", "IR-emitter 940nm OSLON Black (980mW@1A)", "", "UTGÅENDE/EOL (databl. 2023) men lagerförs ännu (RS/Farnell/DigiKey, last-time-buy). NextPCB sourcar + SMT-placerar (verifiera lager/aktuell 940nm OSLON-ersättare inför produktion, t.ex. SFH4725AS bin13)"),
    "PTC_1A":      ("MF-MSMF075/16X-2", "Bourns", "PTC resättbar 0.75A-hold 16V 1206", "", "NOTE: verifiera hold-ström mot systemtopp"),
    "PTC_3A":      ("MF-MSMF300/16-2", "Bourns", "PTC resättbar 3A-hold 16V 1812 — matningsskydd (matar P4+IR, 3A-skala)", "", "alltid-i-lager jellybean; 2S 8.4V kräver 1812 f. 3A@16V"),
    "IIM-42653": ("IIM-42653", "TDK InvenSense", "6-axlig industri-IMU LGA-14, ±4000dps, -40..+105C", "", ""),
    "ICM-42688-P": ("ICM-42688-P", "TDK InvenSense", "6-axlig hög-precisions-IMU LGA-14 2.5×3mm — ultralågt gyro-brus ~2.8 mdps/√Hz, ±2000dps/±16g; pin-kompatibel drop-in mot IIM-42653", "", "Vald för prototyp (i lager hos NextPCB, lägst brus → bäst INS-fusion)"),
    # --- kontakter (genomplåt → selektiv/handlödning) ---
    "P4-socket (edge B)":      ("DS1023-1X14SF11", "Ckmtw", "Stiftsockel 1x14 2.54mm THT (hona) — P4 edge B", "", "socket-sampler: 4-6 d"),
    "P4-socket (edge A)":      ("DS1023-1X15SF11", "Ckmtw", "Stiftsockel 1x15 2.54mm THT (hona) — P4 edge A", "", "1x15 manuell offert (mindre vanlig längd); Sullins PPTC151LFBN-RC = backup"),
    "edge-B kraft-tapp 3V3+GND":("DS1023-1X3SF11", "Ckmtw", "Stiftsockel 1x03 2.54mm THT (hona) — kraft-tapp", "", "socket-sampler: 4-7 d"),
    "2S batteri (JST-XH)":     ("S2B-XH-A(LF)(SN)", "JST", "JST-XH 2-pol header 2.5mm THT", "", "TH"),
    "TRIGGER":     ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "RACK_SW":     ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "MAG_REL_SW":  ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "MAGWELL_SW":  ("B2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT", "", "TH"),
    "recoil-styrning":("B3B-PH-K-S(LF)(SN)", "JST", "JST-PH 3-pol header 2.0mm THT", "", "TH"),
    "NFC PN532 (I²C)":("B4B-PH-K-S(LF)(SN)", "JST", "JST-PH 4-pol header 2.0mm THT", "", "TH"),
    # --- väst-patch ---
    "TSOP4856":    ("TSOP4856", "Vishay", "IR-mottagare 56 kHz (940 nm), LEDAD MOLD-3 (genomplåt/THT)", "", "KUND monterar: böjs 40° för sikte + handlöds (THT, ej SMT) → ej i centroid"),
    "BAT54":       ("BAT54-7-F", "Diodes Inc", "Schottky SOD-123 (OR av TSOP-utgångar)", "", ""),
    "SFH4715AS_860nm": ("SFH 4715AS", "ams OSRAM", "IR-LED 860 nm OSLON Black SMD, Ie 780 mW/sr@1A (konstellation)", "", "NextPCB sourcar + SMT-placerar (precision). Matcha kamerans 860 nm IR-pass (verifiera lager)"),
    "10R":         ("CRCW251210R0JNEGHP", "Vishay", "Res 10R 5% 2W 2512 HP — LED-serieR konstellation (byt fr ...FKEGHP: 31-42 d lead → 4-6 d, −58% pris; samma 2W-HP-familj, 5% tol OK för LED-serie). Lager-koll r2512-sampler", "", "OBS max ~50% duty (2,5W topp @0,5A); 2W HP-rating bibehållen"),
    "HT7333-A":    ("HT7333-A", "Holtek", "LDO 3.3V 250mA SOT-89, Vin<=12V — matar TSOP+DATA (TSOP abs-max 6V)", "", ""),
    # --- hjälm-nod ---
    "AP63203":     ("AP63203WU-7", "Diodes Inc", "Synk-buck 3.8-32Vin 2A TSOT23-6 — 2S→3V3 @1A", "", ""),
    # --- hjälm-headset: ES8388-codec + PAM8302A-amp (analog bom-mik + I²S + I²C, 3,3V) ---
    "ES8388":      ("ES8388", "Everest Semiconductor", "Stereo audio-codec QFN-28 (analog mik-preamp + I²S DAC/ADC, I²C 0x10) — 3,3V", "", "NextPCB SMT-placerar; pinout verifierad mot Everest ES8388-UG"),
    "PAM8302A":    ("PAM8302AASCR", "Diodes Inc", "2,5W mono klass-D-amp (öronhögtalare) — SO-8", "", "verifiera SO-8-SKU mot footprint"),
    "2.2k":        ("RC0805FR-072K2L", "Yageo", "Res 2.2k 1% 0805 — electret-mik-bias", "", ""),
    "MIC_BOOM":    ("S2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT SIDOMONTERAD (S-typ, låg bygghöjd) — analog bom-electret-mik", "", "TH; headset-element kund-kablas"),
    "SPEAKER":     ("S2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT SIDOMONTERAD (S-typ) — öronhögtalare (mono)", "", "TH; headset-element kund-kablas"),
    "PTT_BTN":     ("S2B-PH-K-S(LF)(SN)", "JST", "JST-PH 2-pol header 2.0mm THT SIDOMONTERAD (S-typ) — PTT-knapp", "", "TH; knapp kund-kablas"),
    "4.7uH":       ("SWPA5040S4R7MT", "Sunlord", "Effektinduktor 4.7uH 5x5mm (buck) — IN STOCK (byt fr Changjiang FNR5040320R47M som krävde manuell offert; samma FNR5040-footprint)", "", "Isat≈2.8A > 2A buck-topp ✓ (verifierad mot AP63203)"),
    "31.6k":       ("RC0805FR-0731K6L", "Yageo", "Res 31.6k 1% 0805 — buck FB (övre, 3.33V)", "", ""),
    "22uF":        ("CL31A226KAHNNNE", "Samsung", "MLCC 22uF 25V X5R 1206 — buck-utgång", "", ""),
    "XIAO-S3 1x7 sockel": ("DS1023-1X7SF11", "Ckmtw", "Sockel 1x07 2.54mm hona (XIAO ESP32-S3 stack, 2 st)", "", "socket-sampler: 4-6 d; XIAO köps separat"),
    "ZED-F9P RTK (UART+I²C)": ("SM08B-GHS-TB(LF)(SN)", "JST", "JST GH 8-pol SMD-sockel → kabel till ZED-F9P RTK-puck", "", "ZED-F9P-puck köps separat (komplett: F9P+antenn+IST8310-kompass, centrum-monterad); VERIFIERA kabel-pinout"),
    "AMP: 3V3·GND·SD·GAIN·DIN·BCLK·LRC": ("2.54-1x07-FH", "generisk", "Header 1x07 → MAX98357A-amp-breakout", "", "TH; amp+högtalare köps separat"),
    "MIC: 3V3·GND·SD·WS·SCK·LR": ("2.54-1x06-FH", "generisk", "Header 1x06 → I²S MEMS-mik-breakout", "", "TH; mik köps separat"),
    "2S batteri":  ("S2B-XH-A(LF)(SN)", "JST", "JST-XH 2-pol header 2.5mm THT (2S-batteri)", "", "TH"),
    "2S batteri XT30 (≥15A)": ("XT30PW-M", "AMASS", "XT30PW-M kraftkontakt genomplåt (2S-batteri in, ≥15A) — IN STOCK (kontakt-sampler)", "", ""),
    # --- väst-moderkort ---
    "74HC165":     ("SN74HC165DR", "Texas Instruments", "8-bit PISO shift-register SOIC-16 (läs 10 DATA via SPI)", "", ""),
    "TPIC6B595":   ("TPIC6B595DWR", "Texas Instruments", "Power 8-bit shift-register SOIC-20W, 150mA/kanal open-drain (vibrator-driver)", "", ""),
    "Zon: VBAT·GND·DATA·LED_EN·3V3·VIB": ("S6B-PH-K-S(LF)(SN)", "JST", "JST-PH 6-pol header 2.0mm THT SIDOMONTERAD (S-typ, låg bygghöjd) → väst-patch (pin1-5) + zon-vibrator (pin6)", "", "TH; patch-kabel + ERM-motor kund-kablas"),
    "Patch: VBAT·GND·DATA·LED_EN·3V3": ("S5B-PH-K-S(LF)(SN)", "JST", "JST-PH 5-pol header 2.0mm THT SIDOMONTERAD (S-typ) → dubbel-aim-patch (hjälm-moderkort)", "", "TH; kund-lödd. Matchar patchens JST-PH-kontakt"),
    "100R":        ("RC0805FR-07100RL", "Yageo", "Res 100R 1% 0805", "", ""),
    "10k":         ("RC0805FR-0710KL", "Yageo", "Res 10k 1% 0805", "", ""),
    "VBAT·GND·DATA·LED_EN·3V3":("S5B-PH-K-S(LF)(SN)", "JST", "JST-PH 5-pol header 2.0mm THT SIDOMONTERAD (S-typ, horisontell, låg bygghöjd) på patchens BAKSIDA → kabel ut i kant", "", "TH; kund-lödd. Side-entry (bygger ej på höjden under domen)"),
    # --- P4-WIFI6 kant-socklar (moderkort: ESP32-P4-WIFI6 stackas i 2× 1x20 hona) ---
    "P4-WIFI6 edge B": ("DS1023-1X20SF11", "Ckmtw", "Stiftsockel 1x20 2.54mm THT (hona) — P4-WIFI6 edge B (kraft)", "", "socket-sampler: 4-7 d. ESP32-P4-WIFI6 köps separat (Waveshare)"),
    "P4-WIFI6 edge A": ("DS1023-1X20SF11", "Ckmtw", "Stiftsockel 1x20 2.54mm THT (hona) — P4-WIFI6 edge A (signaler)", "", "socket-sampler: 4-7 d. ESP32-P4-WIFI6 köps separat (Waveshare)"),
    "SFH4725S_940nm": ("SFH 4725S", "ams OSRAM", "IR-emitter 940nm OSLON Black SMD (980mW@1A)", "", "UTGÅENDE/EOL men lagerförs ännu (last-time-buy); NextPCB sourcar + SMT-placerar (precision UNDER LINSEN). Verifiera lager/ersättare SFH4725AS bin13 inför produktion"),
    "SFH4725AS_940nm_bin13": ("SFH 4725AS", "ams OSRAM", "IR-emitter 940nm OSLON Black SMD, bin 13 (aktiv drop-in för utgångna 4725S; samma paket C63062-A4141/footprint/optik)", "", "NextPCB sourcar + SMT-placerar (precision UNDER LINSEN)"),
}

# Inköpta optik-delar UTAN PCB-footprint (köps separat, monteras manuellt över emittrarna).
# Tas med i BOM:en som DNP-referens (NextPCB monterar EJ) — designator/antal/MPN dokumenteras.
OPTIK_EXTRA = [
    # (designator, antal, MPN, tillverkare, paket, beskrivning, not)
    ("LENS1,LENS2", 2, "10195", "Carclo", "Ø20 TIR-kollimator",
     "IR-kollimatorlins (medium TIR ≤±7,5°) över varje emitter", "Köps separat, monteras manuellt — ej PCB-monterad"),
    ("LHOLD1,LHOLD2", 2, "10734", "Carclo", "20mm-hållare (ritn. 60575)",
     "Lins-hållare (4 ben/lins) för Carclo 10195 över emittern", "Köps separat, monteras manuellt — ej PCB-monterad"),
]

def netvals(path):
    t = open(path).read(); seg = t[t.find("(components"):t.find("(libparts")]
    out = {}
    for blk in re.split(r"\(comp\b", seg)[1:]:
        r = re.search(r'\(ref "([^"]+)"\)', blk); v = re.search(r'\(value "([^"]*)"\)', blk)
        if r: out[r.group(1)] = v.group(1) if v else ""
    return out

def refkey(r):
    m = re.match(r'([A-Za-z]+)(\d+)', r); return (m.group(1), int(m.group(2))) if m else (r, 0)

def is_conn(pkg):   # THT-stiftlistar/socklar/JST-PH/XH = kund handlöder (DNP, ej i centroid).
    # OBS: JST-GH (1.25 mm SMD, finpitch) är EJ handlödbar → NextPCB SMT-placerar (ej DNP, med i centroid).
    return any(s in pkg for s in ("PinHeader", "PinSocket", "JST_PH", "JST_XH", "JST_EH"))

# Kontakt-monteringskoll (kontakt-sampler): NextPCB sourcar + genomplåts-monterar alla JST-PH/XH +
# XT30 till rimligt pris → maskin-monteras (ej handlödd). PinSocket/PinHeader (2.54 P4-socklar/
# breakout) + JST-GH undantas: 2.54 stannar handlödd (generisk MPN ej i NextPCB-lib ännu), GH är
# redan SMD-placerad (ej DNP). conn_refs() läser dessa refs ur .net per kort.
MOUNT_NEEDLES = ("JST_PH", "JST_XH", "JST_EH", "AMASS", "PinSocket")   # +2.54 hona-socklar (Ckmtw DS1023 in-stock, socket-sampler)

def conn_refs(board_net, *needles):
    t = open(board_net).read(); seg = t[t.find("(components"):t.find("(libparts")]
    out = set()
    for blk in re.split(r"\(comp\b", seg)[1:]:
        r = re.search(r'\(ref "([^"]+)"\)', blk); fp = re.search(r'\(footprint "([^"]+)"\)', blk)
        if r and fp and any(n in fp.group(1) for n in needles):
            out.add(r.group(1))
    return out

def mount_set(board_pcb, board_net):
    """Kontakter att maskin-montera, med SINGLE-SIDED-skydd: en baksides-placerad kontakt
    maskin-monteras BARA om kortet redan är double-sided (har baksides-SMD). Annars handlöds
    den (annars skulle den lägga till en baksides-montering → onödig double-sided-kostnad på
    optik/FC). Top-kontakter monteras alltid (THT från top = ändå single-sided placering)."""
    refs = conn_refs(board_net, *MOUNT_NEEDLES)
    b = pcbnew.LoadBoard(board_pcb)
    bottom, bottom_smd = set(), False
    for f in b.GetFootprints():
        if f.IsFlipped():
            bottom.add(f.GetReference())
            if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in f.Pads()):
                bottom_smd = True          # baksides-SMD → kortet redan double-sided
    return refs if bottom_smd else (refs - bottom)

HDR = ["Designator*", "Quantity*", "Manufacturer Part Number*", "Manufacturer",
       "Package/Footprint", "Description", "Procurement Type", "Customer Note"]

def build(board_pcb, board_net, out_xls, dnp_refs=frozenset(), cust_refs=frozenset(), ovr_refs=frozenset(), extra=(), mount_refs=frozenset()):
    vals = netvals(board_net)
    b = pcbnew.LoadBoard(board_pcb)
    groups = defaultdict(list)   # (value, footprint) -> [ref]  (gruppera på BÅDE värde och paket)
    for f in b.GetFootprints():
        ref = f.GetReference()
        fp = str(f.GetFPID().GetLibItemName())
        if any(k in fp for k in ("MountingHole","Fiducial","TestPoint")):  # kort-feature, ej placerad komponent
            continue
        if f.Pads() and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in f.Pads()):
            continue                    # mekaniskt hål (NPTH) — ej komponent
        val = vals.get(ref, f.GetValue())
        groups[(val, fp)].append(ref)
    wb = xlwt.Workbook(); ws = wb.add_sheet("BOM")
    bold = xlwt.easyxf("font: bold on")
    for c, h in enumerate(HDR): ws.write(0, c, h, bold)
    row = 1
    for (val, pkg) in sorted(groups):
        refs = sorted(groups[(val, pkg)], key=refkey)
        m = re.search(r'_(\d{4})_', pkg)                      # paket-storlek (0402/0805/1206/1210/2512)
        size = m.group(1) if m else ""
        key = f"{val}@{size}" if f"{val}@{size}" in MPN else val   # paket-specifik MPN om sådan finns
        mpn, mfr, desc, proc, note = MPN.get(key, ("", "", val, "", "SAKNAR MPN — fyll i"))
        if refs and all(r in mount_refs for r in refs):
            # kontakt-monteringstest: NextPCB sourcar + genomplåts-monterar (ej DNP, ej handlödd)
            proc = ""; note = "MONTERAS av NextPCB (kontakt-test) — sourcas + THT-monteras, ej handlödd"
        elif refs and all(r in ovr_refs for r in refs):
            proc = "DNP"; note = ("3A-override (Rp): DNP = säker 1A fail-safe default; "
                                  "montera för 3A (medvetet labbeslut, kräver förnyad ögonsäkerhetsmätning)")
        elif refs and all(r in dnp_refs for r in refs):
            proc = "DNP"; note = "Prototyp: monteras EJ (körs på breakout först)"
        elif is_conn(pkg) or (refs and all(r in cust_refs for r in refs)):
            # THT/handlödda delar (kontakter, headers, ledade TSOP, LED-tab-socklar): kund köper +
            # löder själv hemma. Markeras DNP → NextPCB monterar EJ. Står ändå kvar som BOM-rad
            # (designator/antal/MPN) = beställningsreferens. Hålls ute ur CENTROID (ej maskin-placerad).
            proc = "DNP"
            note = "Kund handlöder själv (THT/ledad) — DNP: NextPCB monterar EJ, ej i centroid. Med i BOM som beställningsreferens."
        ws.write(row, 0, ",".join(refs)); ws.write(row, 1, len(refs))
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, pkg)
        ws.write(row, 5, desc); ws.write(row, 6, proc); ws.write(row, 7, note)
        row += 1
    # inköpta delar utan PCB-footprint (lins/hållare) — alltid DNP (monteras manuellt)
    for desig, qty, mpn, mfr, pkg, desc, note in extra:
        ws.write(row, 0, desig); ws.write(row, 1, qty)
        ws.write(row, 2, mpn); ws.write(row, 3, mfr); ws.write(row, 4, pkg)
        ws.write(row, 5, desc); ws.write(row, 6, "DNP"); ws.write(row, 7, note)
        row += 1
    wb.save(out_xls)
    print(f"  {out_xls}: {row-1} BOM-rader ({sum(len(v) for v in groups.values())} komponenter)")

def centroid(board_pcb, out_csv, exclude=frozenset(), mount_refs=frozenset()):
    b = pcbnew.LoadBoard(board_pcb)
    ox, oy = b.GetDesignSettings().GetAuxOrigin()
    rows = []
    for f in b.GetFootprints():
        fp = str(f.GetFPID().GetLibItemName())
        if any(k in fp for k in ("MountingHole","Fiducial","TestPoint")): continue
        if is_conn(fp) and f.GetReference() not in mount_refs: continue   # handlödda kontakter → ej i SMT-centroid (mount_refs = NextPCB-monterade → med)
        # mekaniska hål (alla paddar NPTH / inga kopparpaddar) → ej en placerad komponent
        if f.Pads() and all(p.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH for p in f.Pads()): continue
        if f.GetReference() in exclude: continue   # DNP → ej i centroid
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
    # KONTAKT-MONTERING AKTIV: alla JST-PH/XH + XT30 maskin-monteras av NextPCB (pris bekräftat
    # rimligt via vest-mb-test). conn_refs() plockar dem per kort. PinSocket/PinHeader (2.54) +
    # JST-GH undantas (handlödd resp. redan SMD).
    # OPTIK: IMU (U1=ICM-42688-P) bestyckad. R3 = DNP (3A-override). J2 (XH) maskin-monteras; J1 (1x14) handlödd.
    OPTIK_MOUNT = mount_set("weapon-module.kicad_pcb", "weapon-module.net")  # baksides J1(P4)/J2(XH) → handlöds (single-sided)
    print("OPTIK (IMU ICM-42688-P bestyckad):"); build("weapon-module.kicad_pcb", "weapon-module.net", "nextpcb/optik-bom.xls",
          ovr_refs={"R3"}, extra=OPTIK_EXTRA, mount_refs=OPTIK_MOUNT)
    centroid("weapon-module.kicad_pcb", "nextpcb/optik-centroid.csv", exclude={"R3"}, mount_refs=OPTIK_MOUNT)
    # FIRE-CONTROL: avkoppling bestyckad. JST-PH J3-J10 + 2.54-socklar J1(1x15)/J2(1x03) maskin-monteras (Ckmtw).
    FC_MOUNT = mount_set("firecontrol.kicad_pcb", "firecontrol.net")  # baksides J1(P4)/J2(kraft) → handlöds; top-JST monteras
    print("FIRE-CONTROL (2× IMU U1/U2 = ICM-42688-P bestyckade):")
    build("firecontrol.kicad_pcb", "firecontrol.net", "nextpcb/firecontrol-bom.xls", mount_refs=FC_MOUNT)
    centroid("firecontrol.kicad_pcb", "nextpcb/firecontrol-centroid.csv", mount_refs=FC_MOUNT)
    # VÄST-PATCH: J1 (S5B-PH) maskin-monteras; U1-U4 (ledade TSOP) + D7-D10 (LED-tab) kund-handlödda.
    PATCH_MOUNT = mount_set("vest-patch.kicad_pcb", "vest-patch.net")
    PATCH_CUST = {"U1","U2","U3","U4","D7","D8","D9","D10"}
    print("VÄST-PATCH:"); build("vest-patch.kicad_pcb", "vest-patch.net", "nextpcb/vest-patch-bom.xls",
          cust_refs=PATCH_CUST | {"J1"}, mount_refs=PATCH_MOUNT)
    centroid("vest-patch.kicad_pcb", "nextpcb/vest-patch-centroid.csv", exclude=PATCH_CUST, mount_refs=PATCH_MOUNT)
    # Prototyp-optik: J1 (1x14 P4-carrier) kund-lödd (TH) i denna variant → uteslut J1 ur mount
    # (annars säger BOM 'monteras' men centroid utesluter J1 → motsägelse). Övrigt = som optik.
    PROTO_MOUNT = OPTIK_MOUNT - {"J1"}
    print("OPTIK-PROTOTYP (IMU bestyckad, J1 kund-lödd):"); build("weapon-module.kicad_pcb", "weapon-module.net",
          "nextpcb/optik-PROTOTYP-bom.xls", cust_refs={"J1"}, ovr_refs={"R3"}, extra=OPTIK_EXTRA, mount_refs=PROTO_MOUNT)
    centroid("weapon-module.kicad_pcb", "nextpcb/optik-PROTOTYP-centroid.csv", exclude={"J1","R3"}, mount_refs=PROTO_MOUNT)
    # HJÄLM-MODERKORT (ESP32-P4-WIFI6, Ø100): JST-PH/XH (headset/patch/batteri J2-J7,J10,J11) +
    # J8/J9 (1x20 P4-socklar, Ckmtw) maskin-monteras; J1/J12 = RTK-puck GH redan SMD. ES8388/PAM8302A SMD.
    # cust = ledade optik-delar (4 TSOP U3-U6 + 6 LED-tab D5-D10) som kund handlöder.
    HMB_MOUNT = mount_set("helmet-mb.kicad_pcb", "helmet-mb.net")  # redan double-sided (GH-SMD baksida) → montera allt
    HMB_CUST = {"U3","U4","U5","U6","D5","D6","D7","D8","D9","D10"}
    print("HJÄLM-MB (IMU U2 ICM-42688-P bestyckad):")
    build("helmet-mb.kicad_pcb", "helmet-mb.net", "nextpcb/helmet-mb-bom.xls", cust_refs=HMB_CUST, mount_refs=HMB_MOUNT)
    centroid("helmet-mb.kicad_pcb", "nextpcb/helmet-mb-centroid.csv", exclude=HMB_CUST, mount_refs=HMB_MOUNT)
    # VÄST-MODERKORT (ESP32-P4-WIFI6): JST-PH J1-J10 + XT30 J13 maskin-monteras; J11/J12 (1x20 P4-socklar) handlödda.
    VMB_MOUNT = mount_set("vest-mb.kicad_pcb", "vest-mb.net")  # allt Top → single-sided
    VMB_CUST = {f"J{i}" for i in range(1, 14)}
    print("VÄST-MB:"); build("vest-mb.kicad_pcb", "vest-mb.net", "nextpcb/vest-mb-bom.xls", cust_refs=VMB_CUST, mount_refs=VMB_MOUNT)
    centroid("vest-mb.kicad_pcb", "nextpcb/vest-mb-centroid.csv", exclude=VMB_CUST - VMB_MOUNT, mount_refs=VMB_MOUNT)
