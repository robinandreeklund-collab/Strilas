#!/usr/bin/env python3
"""STRILAS — FC v2: lägg till OLED (J9) + lägesväljare (J10/R3/R4) + utöka J1 till 15-pin.

Modifierar det BEFINTLIGA mirrored-kortet direkt:
  1. J1: PinSocket_1x12 → PinSocket_1x15 (pin13=GND, pin14=MODE_A, pin15=MODE_B)
  2. J9: OLED I²C JST-PH 4-pin vid (168, 114)  [GND/3V3/SCL/SDA]
  3. J10: lägesväljare JST-PH 3-pin vid (161, 114) [MODE_A/MODE_B/GND]
  4. R3, R4: 4k7 pull-ups MODE_A/MODE_B vid (161,117) resp (167,117)
  5. Strips all tracks → redo via route_firecontrol.py

Kör: python3 hardware/fc_add_ports_v2.py && python3 hardware/route_firecontrol.py
"""
import pcbnew, os, shutil

PCB   = "hardware/firecontrol.kicad_pcb"
FPDIR = "/usr/share/kicad/footprints"
MM    = pcbnew.FromMM

shutil.copy(PCB, "/tmp/_fc_pre_v2.kicad_pcb")
b = pcbnew.LoadBoard(PCB)


def load_fp(lib_dir_name, fp_name):
    return pcbnew.FootprintLoad(f"{FPDIR}/{lib_dir_name}.pretty", fp_name)


def get_or_add_net(board, name):
    n = board.FindNet(name)
    if n and n.GetNetname() == name:
        return n
    ni = pcbnew.NETINFO_ITEM(board, name, 0)
    board.Add(ni)
    return board.FindNet(name)


# ---------- 1. Add new nets ----------
net_gnd = b.FindNet("GND")
net_3v3 = b.FindNet("+3V3")
net_sda = b.FindNet("NFC_SDA")
net_scl = b.FindNet("NFC_SCL")
net_ma  = get_or_add_net(b, "MODE_A")
net_mb  = get_or_add_net(b, "MODE_B")

# ---------- 2. Replace J1: 1x12 → 1x15 ----------
# Original placement by receiver_place.py: rot=90 at (-18.31, 8.89) in pre-mirror frame
# → board (131.69, 128.89) after mirror. Flip applied by firecontrol_flip.py.
# Use rot=90 (pre-mirror value) — NOT GetOrientationDegrees() which returns -90 post-mirror.
old_j1 = [f for f in b.GetFootprints() if f.GetReference() == "J1"][0]
j1_pos = old_j1.GetPosition()

pad_nets_12 = {}
for pad in old_j1.Pads():
    pad_nets_12[pad.GetName()] = pad.GetNet()

b.Remove(old_j1)

new_j1 = load_fp("Connector_PinSocket_2.54mm", "PinSocket_1x15_P2.54mm_Vertical")
new_j1.SetReference("J1")
new_j1.SetValue("P4-socket edge A pin6-20")
new_j1.SetPosition(j1_pos)
new_j1.SetOrientationDegrees(90)       # same as original receiver_place.py
b.Add(new_j1)
new_j1.Flip(j1_pos, False)             # face down toward P4 (same as original)

for pad in new_j1.Pads():
    nm = pad.GetName()
    if nm in pad_nets_12:
        pad.SetNet(pad_nets_12[nm])
    elif nm == "13":
        pad.SetNet(net_gnd)
    elif nm == "14":
        pad.SetNet(net_ma)
    elif nm == "15":
        pad.SetNet(net_mb)

for pad in sorted(new_j1.Pads(), key=lambda p: int(p.GetName())):
    pn = int(pad.GetName())
    if pn >= 13:
        p = pad.GetPosition()
        print(f"  J1.{pn}  x={p.x/1e6:.3f}  net={pad.GetNetname()}")
print(f"J1 → PinSocket_1x15  flipped={new_j1.IsFlipped()} layer={new_j1.GetLayerName()}")

# ---------- helper: place a footprint and assign nets ----------
def add_fp(lib_dir, fp_name, ref, value, x_mm, y_mm, rot_deg, nets):
    """nets = {pad_name_str: net_object}"""
    f = load_fp(lib_dir, fp_name)
    f.SetReference(ref)
    f.SetValue(value)
    pos = pcbnew.VECTOR2I(MM(x_mm), MM(y_mm))
    f.SetPosition(pos)
    f.SetOrientationDegrees(rot_deg)
    b.Add(f)
    for pad in f.Pads():
        n = nets.get(pad.GetName())
        if n:
            pad.SetNet(n)
    return f

# Placering vald för 0 courtyard-krock på det trånga 71×21-kortet: överkanten (y114) är full
# (J2..J6 + H4 + J8), så J9 (bred 4-pin) hamnar i nedre högra hörnet och J10 (3-pin) i luckan
# J6→H4 (J3..J6 skjuts 1 mm vänster i receiver_place för att luckan ska räcka). R3/R4 i
# cap-radens (y123.5) luckor C3-C4 resp C5-C6.
# ---------- 3. J9 — OLED I²C JST-PH 4-pin, nedre högra hörnet ----------
# Pin order: 1=GND / 2=3V3 / 3=SCL / 4=SDA  (standard SSD1306 4-pin module order)
add_fp("Connector_JST", "JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical",
       "J9", "OLED SSD1306 I2C",
       176.5, 127.0, 0,
       {"1": net_gnd, "2": net_3v3, "3": net_scl, "4": net_sda})
print("J9 OLED at (176.5,127)  1=GND 2=3V3 3=SCL 4=SDA")

# ---------- 4. J10 — mode selector JST-PH 3-pin, luckan J6→H4 ----------
# Pin order: 1=MODE_A / 2=MODE_B / 3=GND
add_fp("Connector_JST", "JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",
       "J10", "4-laedes rotarykopplare",
       162.2, 114.0, 0,
       {"1": net_ma, "2": net_mb, "3": net_gnd})
print("J10 mode selector at (162.2,114)  1=MODE_A 2=MODE_B 3=GND")

# ---------- 5. R3 — MODE_A pull-up 4k7, cap-radens lucka C3-C4 ----------
add_fp("Resistor_SMD", "R_0805_2012Metric",
       "R3", "4k7",
       158.0, 123.5, 0,
       {"1": net_3v3, "2": net_ma})
print("R3 MODE_A pull-up at (158,123.5)")

# ---------- 6. R4 — MODE_B pull-up 4k7, cap-radens lucka C5-C6 ----------
add_fp("Resistor_SMD", "R_0805_2012Metric",
       "R4", "4k7",
       171.0, 123.5, 0,
       {"1": net_3v3, "2": net_mb})
print("R4 MODE_B pull-up at (171,123.5)")

# ---------- 7. Strip all tracks + zones ----------
to_remove = list(b.GetTracks()) + list(b.Zones())
n_removed = len(to_remove)
for it in to_remove:
    b.Remove(it)
print(f"Stripped {n_removed} tracks/zones")

pcbnew.SaveBoard(PCB, b)
print(f"Saved {PCB}. Run: python3 hardware/route_firecontrol.py")
