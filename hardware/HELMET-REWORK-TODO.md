# HJÄLM-MB — pågående omläggning (WIP, EJ klar)

> **Status:** `helmet_mb_netlist.py` + `helmet-mb.net` är UPPDATERADE (ES8388 + alt-puck + side-entry),
> men **`helmet-mb.kicad_pcb` + `leverans/helmet-mb/` är fortfarande den gamla Ø97-versionen** (återställd
> till HEAD för att inte checka in ett trasigt/oroutat kort). **TILLVERKA INTE hjälmen från nuvarande
> leverans** förrän omläggningen nedan är klar och kortet är omplacerat + omroutat + DRC-rent.

## Vad som redan är gjort i källan (netlist)
- **ES8388 audio-codec** (QFN-28 0,5 mm, `strilas:ES8388_QFN-28_4x4mm_P0.5mm`) — analog bom-mik + I²S DAC/ADC
  ↔ P4 + I²C (0x10) + PAM8302A klass-D → öronhögtalare + PTT. Pinout verifierad mot Everest UG. Anslutning verifierad.
- **Side-entry-footprints** på alla JST-PH (patch S5B, headset S2B) — `JST_PH_S?B-PH-K..._Horizontal`.
- **Alt-RTK-puck (J12)**: 6-pol JST-GH (`SM06B-GHS-TB` horisontell) PARALLELLT med 8-pol ZED-F9P (J1).
  Pinout alt-puck: 1=VCC 2=RX 3=TX 4=SCL 5=SDA 6=GND → kopplat VBAT/GNSS_RX/GNSS_TX/I2C_SCL/I2C_SDA/GND.
  Montera ENDERA pucken (delar fästhål). PPS/RSV saknas på alt-pucken (ej kritiskt för RTK-pos).

## Återstående PLACERINGS-omläggning (receiver_place.py `helmet_mb_pos`)
Drivs av: **RTK-puck monteras på BAKSIDAN, Ø86 mm** (r43). Optik (TSOP/LED) + P4 på FRONTEN.
- **Förstora kortet till Ø108** (outline `("circle", 54)` i BOARDS; uppdatera även zon-radien i
  `route_helmet_mb.py finish()` från 47.5 → ~53). Skäl: Ø86-pucken (r43) på baksidan kräver att
  kontakterna ligger på en YTTRE ring (r~48) UTANFÖR pucken; Ø97 ger bara 5,5 mm ring (för smalt).
- **FRONT:** optik-ring (4 TSOP + 6 LED) flyttas UT till kanten (r~49–50 centrum) så domen/benen aimar
  ut förbi kanten (på Ø97-pos r40 skulle Ø108-kantmaterialet skugga). P4/codec(U7)/amp(U8)/buck/IMU i centrum.
- **BAK:** Ø86-puck i centrum (på standoffs, via fästhålen). ALLA kontakter på en yttre ring r~48 (utanför
  puck-r43), öppning radiellt UT (använd `_se(theta, 48, npin, "out", flip=True)`): 4 patch (S5B) + 3 headset
  (S2B) + J1 8-pol GH + J12 6-pol GH + batteri J10. Använd `render_place.py` för att verifiera öppningar UT
  + 0 courtyard-krock + 0 past-edge på BÅDA sidor.
- Puck-fästhålen H5–H8 är satta till **medelmönstret (±10,2 × ±17,0)** så både ZED-F9P (20,80×33,90) och
  alt-pucken (~20,0×34,1) passar (M2.5-hål; verifiera mot fysisk puck).

## Sedan
`python3 hardware/route_helmet_mb.py` (efter att zon-radien uppdaterats) → DRC 0/0 → regenerera
`leverans/helmet-mb/` (gerbers/STEP/BOM/centroid) → uppdatera system-guiden (rad om hjälm-ljud = ES8388,
Ø108, puck-på-baksida) → commit.
