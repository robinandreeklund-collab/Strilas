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
1. **C2 (optik) 100µF 1210** — välj ≥16 V (VBAT = 2S ≈ 8.4 V). Föreslagen TDK 25 V.
2. **R2 (optik) 3R3 2W 2512** — effektresistor (IR-strömtak). MPN är 2 W-variant (Vishay HP); bekräfta effekt.
3. **F1 (optik) PTC** — hold-ström/spänning mot VBAT; föreslagen Bourns 0.75 A/16 V.
4. **Genomplåtskontakter (TH):** JST-PH/-XH + stiftssocklar → selektiv-/handlödning,
   kan offereras separat. Sätt `C` om du själv lödder/levererar dem.
5. Generiska passiva (R/C) MPN = representativa — byt gärna mot NextPCB:s basbibliotek
   (lägre pris); paket/värde är det som måste stämma.

## Centroid-format
`Designator, Mid X(mm), Mid Y(mm), Layer, Rotation` — samma origo som Gerbers
(KiCad absolut/sidorigo). Rotation enligt KiCad/IPC-konvention; granska vid DFM.
J1/J2 sitter på **Bottom** (stack-kontakter flippade till baksidan).

Regenereras: `python3 gen_nextpcb.py` (i `vapen-stack/`).
