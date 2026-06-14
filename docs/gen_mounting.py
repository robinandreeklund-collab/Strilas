#!/usr/bin/env python3
"""Genererar STRILAS Fas 1 monteringsritning (vapen) som PNG.
Stiliserad M4-carbine i sidovy med numrerade monteringspunkter + teckenförklaring."""
from PIL import Image, ImageDraw, ImageFont

W, H = 1560, 860
img = Image.new("RGB", (W, H), (247, 247, 244))
d = ImageDraw.Draw(img)

def font(sz, bold=False):
    try:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans%s.ttf" % ("-Bold" if bold else ""), sz)
    except Exception:
        try:
            return ImageFont.load_default(size=sz)
        except TypeError:
            return ImageFont.load_default()

F_TITLE = font(30, True)
F_SUB = font(17)
F_LEG = font(17)
F_LEGB = font(17, True)
F_NUM = font(16, True)
F_SMALL = font(14)

TAN = (199, 168, 120)
TAN_D = (171, 140, 96)
BLK = (46, 46, 50)
BLK_L = (74, 74, 80)
GRY = (110, 110, 116)
RED = (198, 42, 42)
LINE = (120, 120, 126)

# ---- Titel ----
d.text((40, 28), "STRILAS — Fas 1: Monteringsritning (vapen)", font=F_TITLE, fill=(30, 30, 34))
d.text((42, 68), "Self-contained vapenenhet på M4-carbine-plattform. Väst/hjälm = separat enhet (ESP-NOW).",
        font=F_SUB, fill=(90, 90, 96))

cy = 320  # vapnets centerlinje

# ===================== RITA VAPNET (mynning vänster) =====================
# Flash hider / mynning
d.rectangle([60, cy-16, 104, cy+16], fill=BLK)
for sx in range(66, 100, 9):
    d.rectangle([sx, cy-16, sx+3, cy+16], fill=(20, 20, 22))
d.rectangle([104, cy-9, 120, cy+9], fill=GRY)
# Yttre pipa
d.rectangle([120, cy-7, 176, cy+7], fill=(95, 95, 100))
# Top rail (genomgående)
d.rectangle([176, cy-46, 690, cy-36], fill=BLK_L)
for rx in range(180, 688, 11):
    d.line([rx, cy-46, rx, cy-36], fill=(40, 40, 44), width=1)
# Handskydd M-LOK (fram tan, bak svart)
d.rectangle([176, cy-36, 340, cy+34], fill=TAN)        # främre tan
d.rectangle([340, cy-36, 470, cy+34], fill=BLK)        # bakre svart
# M-LOK-slots
for sx in range(196, 320, 30):
    d.rounded_rectangle([sx, cy-6, sx+16, cy+22], radius=6, fill=TAN_D)
# Övre mottagare/receiver
d.rectangle([470, cy-40, 700, cy+40], fill=BLK)
# Ejektionsport
d.rounded_rectangle([520, cy-26, 595, cy-4], radius=4, fill=BLK_L)
# Forward assist
d.ellipse([598, cy-22, 616, cy-4], fill=BLK_L)
# Flip-up sikten (fram + bak)
d.polygon([(214, cy-46), (224, cy-78), (234, cy-46)], fill=BLK)
d.polygon([(648, cy-46), (660, cy-82), (672, cy-46)], fill=BLK)
# Laddhandtag (bak top)
d.rectangle([686, cy-30, 712, cy-18], fill=BLK_L)
# Magwell + magasin (böjt, tan)
d.polygon([(500, cy+34), (590, cy+34), (600, cy+90), (516, cy+96)], fill=BLK)  # magwell
mag = [(512, cy+92), (600, cy+88), (612, cy+150), (560, cy+210), (498, cy+205),
       (470, cy+150)]
d.polygon(mag, fill=TAN)
d.line([(498, cy+205), (470, cy+150)], fill=TAN_D, width=3)
for my in range(cy+110, cy+190, 16):
    d.line([(486, my+8), (596, my)], fill=TAN_D, width=2)
# Trigger guard + trigger
d.arc([548, cy+34, 612, cy+92], start=0, end=180, fill=BLK, width=7)
d.line([580, cy+40, 580, cy+66], fill=BLK, width=6)  # trigger
# Pistolgrepp (tan)
d.polygon([(600, cy+40), (640, cy+40), (664, cy+150), (628, cy+158), (600, cy+70)], fill=TAN)
# Buffert-rör + carbine-stock (tan)
d.rectangle([700, cy-12, 884, cy+12], fill=TAN_D)        # buffertrör
d.polygon([(792, cy-44), (936, cy-50), (944, cy+58), (792, cy+52)], fill=TAN)  # stock-kropp
d.rectangle([928, cy-50, 948, cy+58], fill=BLK)          # buttplate
d.polygon([(820, cy+12), (900, cy+12), (884, cy+50), (812, cy+50)], fill=TAN_D)  # underkam

# ===================== MONTERINGSPUNKTER (numrerade) =====================
# (nummer, x, y) — placerade på/vid sin del
pts = {
    1:  (86,  cy-40),   # IR-emitter @ mynning
    2:  (455, cy-58),   # IMU @ rail/receiver-front (styvt mot lopp)
    3:  (250, cy+60),   # Huvudelektronik (PEQ-box på handskydd)
    4:  (628, cy-66),   # HUD micro-OLED @ topprail/optikplats
    5:  (724, cy-48),   # Rack-sensor @ laddhandtag
    6:  (580, cy+86),   # Avtryckar-sensor
    7:  (676, cy+34),   # Mag-release-sensor (höger om magwell)
    8:  (505, cy+58),   # NFC-läsare PN532 @ magwell
    9:  (540, cy+150),  # Magasin: NFC-tag + rekyl-LiPo + kontakter >25A
    10: (840, cy-30),   # Rekylenhet (reciprok. massa) i buffertrör/stock
    11: (660, cy+58),   # Rekyl load-switch + cap-bank @ receiver
    12: (888, cy+30),   # Logikbatteri 2S @ stock
    13: (300, cy+30),   # Ljud (valfritt) @ handskydd
}
# nudge för etikett-markörer (offset från punkt till nummercirkel)
nudge = {
    1: (0, -70), 2: (0, -96), 3: (-70, 70), 4: (0, -116), 5: (96, -86),
    6: (-30, 110), 7: (96, -10), 8: (-118, 70), 9: (-150, 70), 10: (0, -120),
    11: (170, 70), 12: (60, 120), 13: (-130, 70),
}
R = 16
for n, (px, py) in pts.items():
    ox, oy = nudge[n]
    mx, my = px+ox, py+oy
    d.line([(px, py), (mx, my)], fill=LINE, width=2)
    d.ellipse([px-4, py-4, px+4, py+4], fill=RED)
    d.ellipse([mx-R, my-R, mx+R, my+R], fill=RED, outline=(255, 255, 255), width=2)
    tw = d.textlength(str(n), font=F_NUM)
    d.text((mx-tw/2, my-9), str(n), font=F_NUM, fill=(255, 255, 255))

# ===================== TECKENFÖRKLARING =====================
LX, LY = 992, 150
d.rounded_rectangle([LX-14, LY-30, W-30, 832], radius=12, outline=(200, 200, 204),
                    width=2, fill=(255, 255, 255))
d.text((LX, LY-22), "Teckenförklaring — monteringsplats", font=F_LEGB, fill=(30, 30, 34))
legend = [
    (1,  "IR-emitter (SFH 4715AS + lins)", "mynning, borrlinjerad ~±15°"),
    (2,  "IMU (ICM-45686)", "receiver/rail, styvt mot loppet"),
    (3,  "Huvudelektronik (ESP32-S3 + PCB)", "PEQ-box på handskyddsrail"),
    (4,  "HUD micro-OLED", "topprail bak (optikplats)"),
    (5,  "Rack-sensor (chamber)", "laddhandtag"),
    (6,  "Avtryckar-sensor", "avtryckare"),
    (7,  "Mag-release-sensor", "höger om magwell"),
    (8,  "NFC-läsare (PN532)", "magwell (läser vid insert)"),
    (9,  "MAGASIN: NFC-tag + rekyl-LiPo", "+ kall-mate-kontakter >25 A"),
    (10, "Rekylenhet (reciprok. massa)", "i buffertrör / stock"),
    (11, "Rekyl load-switch + cap-bank", "receiver (TPS25983, soft-start)"),
    (12, "Logikbatteri 2S Li-ion + buck", "i stocken"),
    (13, "Ljud I²S (valfritt)", "handskydd"),
]
ry = LY + 10
for n, title, sub in legend:
    d.ellipse([LX, ry, LX+26, ry+26], fill=RED, outline=(255, 255, 255), width=1)
    tw = d.textlength(str(n), font=F_NUM)
    d.text((LX+13-tw/2, ry+5), str(n), font=F_NUM, fill=(255, 255, 255))
    d.text((LX+38, ry-1), title, font=F_LEGB, fill=(30, 30, 34))
    d.text((LX+38, ry+20), sub, font=F_SMALL, fill=(110, 110, 116))
    ry += 50

# Säkerhetsnot
d.text((42, 800), "⚠ IR-strömgräns i HÅRDVARA (resistor) = Class 1-tak.  "
        "Rekylskena ENABLE endast mellan rack och mag-release (kalla kontakter).",
        font=F_SMALL, fill=(150, 60, 60))

img.save("/home/user/Strilas/docs/phase1-mounting.png")
print("saved", img.size)
