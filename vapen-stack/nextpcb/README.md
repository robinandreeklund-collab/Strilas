# STRILAS — NextPCB tillverknings-underlag (PCB + SMT-montering)

Två tillverkade kort. **P4 (Waveshare ESP32-P4-WIFI6) köps separat — tillverkas ej.**

För varje kort, ladda upp på nextpcb.com:

| Steg | Optik | Fire-control |
|---|---|---|
| **PCB (Gerber)** | `optik-gerbers.zip` | `firecontrol-gerbers.zip` |
| **BOM** | `optik-bom.xls` | `firecontrol-bom.xls` |
| **Centroid (pick&place)** | `optik-centroid.csv` | `firecontrol-centroid.csv` |

## Kort-data (för PCB-formuläret)
- **Lager:** 4 (F.Cu signal · In1=GND · In2=VBAT · B.Cu=GND) — bägge korten.
- **Optik:** ~54 × 74 mm. **Fire-control:** ~71 × 21 mm.
- Koppar 1 oz, FR-4, HASL eller ENIG. Min spår/gap 0.2 mm, min via 0.3 mm (håller marginal).

## BOM — kolumnstruktur (NextPCB-mall)
`Designator* · Quantity* · Manufacturer Part Number* · Manufacturer ·
Package/Footprint · Description · Procurement Type · Customer Note`
- **Procurement Type:** tom = NextPCB sourcar · `DNP` = montera ej · `C` = du levererar delen.
- Monteringshål (H*) och Carclo-linsben är **kort-features, ej komponenter** → ej i BOM.

## Att VERIFIERA före beställning (`Customer Note`-flaggor)
1. **U1/U2 IMU = TDK ICM-42670-P** — vald för att den är **IN-STOCK** hos LCSC/NextPCB (C3288646),
   till skillnad från ICM-42688-P/45686 (~285–327 dgr ledtid). Pinout verifierad mot databladet
   DS-000451 (`../../datasheet/`): pin 7 = FSYNC ("connect to GND if not used" → vår koppling).
   **Drop-in i SAMMA footprint** som hela ICM-426xx/456xx-familjen → vill du senare ha lägre
   gyrobrus kan ICM-42688-P bestyckas på exakt samma kort utan ändring.
2. **D2/D3 SFH 4725S** (IR-emitter) — bestyckas av NextPCB (matchad, ~10 dgr). INTE kund-levererad
   → kortet kommer komplett bestyckat. (Linser/kamera tillkommer separat, se huvud-README.)
3. **R2 (optik) 3R3 2W 2512** — effektresistor (IR-strömtak). MPN är 2 W-variant (Vishay HP); bekräfta effekt.
4. **F1 (optik) PTC** — bekräfta hold-ström mot systemets toppmedelström (16 V-variant vald för 2S).
5. **C2 (optik) 100 µF 25 V 1210** — bytt till in-stock Murata (matchar direkt).
6. **Genomplåtskontakter (TH):** JST-PH/-XH + stiftssocklar → selektiv-/handlödning,
   kan offereras separat. Sätt `C` om du själv lödder/levererar dem.
7. Generiska passiva (R/C) MPN = representativa — byt gärna mot NextPCB:s basbibliotek
   (lägre pris); paket/värde är det som måste stämma.

## Centroid-format
`Designator, Mid X(mm), Mid Y(mm), Layer, Rotation` — samma origo som Gerbers
(KiCad absolut/sidorigo). Rotation enligt KiCad/IPC-konvention; granska vid DFM.
J1/J2 sitter på **Bottom** (stack-kontakter flippade till baksidan).

Regenereras: `python3 gen_nextpcb.py` (i `vapen-stack/`).
