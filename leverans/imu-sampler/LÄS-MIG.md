# STRILAS — IMU-SAMPLER (DEMO · EJ FÖR TILLVERKNING)

**Syfte:** hitta vilken IMU NextPCB har i lager **direkt**. Kortet bär 18 olika IMU-kandidater
(samma klass som vår planerade IIM-42653 eller **bättre** — högre dps, lägre brus, hög-g,
hög-vibration, samt 9-axel). Ladda upp BOM:en till NextPCB:s offert/lager-system → se vilka som
är **tillgängliga** → välj en och beställ den på de riktiga korten (weapon-module / firecontrol /
helmet-mb). **Detta kort tillverkas inte** — det är bara ett urvals-/lagerkoll-verktyg.

> Footprints är korrekta paket. Inom en familj (TDK 42xxx/45xxx, ST LSM6DS, Bosch BMI) är
> pinouten kompatibel, så **byter du IMU i den valda familjen behöver de riktiga korten inte
> omdesignas** — samma footprint, bara ny MPN i BOM. (IIM-42653 sitter idag på TDK-familjens
> `strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx` → alla TDK-kandidater nedan är drop-in.)

## Filer
`imu-sampler-gerbers.zip` · `imu-sampler-bom.xls` (18 MPN) · `imu-sampler-centroid.csv/.xls`.
(Ingen STEP — kortet är ej mekaniskt.)

## Kandidater (alla I²C + SPI, ≥6-axel)

| Ref | MPN | Tillv. | Paket / footprint | Axlar | Gyro | Accel | Varför / not |
|---|---|---|---|---|---|---|---|
| U1 | **IIM-42653** | TDK | LGA-14 2.5×3 (TDK) | 6 | ±4000 dps | ±32 g | **baslinje** (industri −40..+105 °C) |
| U2 | IIM-42652 | TDK | LGA-14 (TDK) | 6 | ±2000 dps | ±16 g | industri |
| U3 | ICM-42688-P | TDK | LGA-14 (TDK) | 6 | ±2000 dps | ±16 g | **lägsta gyro-brus** → precision |
| U4 | ICM-42670-P | TDK | LGA-14 (TDK) | 6 | ±2000 dps | ±16 g | låg-effekt (datablad i repo) |
| U5 | ICM-40609-D | TDK | LGA-14 (TDK) | 6 | ±2000 dps | ±32 g | hög-g |
| U6 | **ICM-45686** | TDK | LGA-14 (TDK) | 6 | ±4000 dps | ±32 g | ny-gen, lägre brus än 426xx |
| U7 | ICM-42688-V | TDK | LGA-14 (TDK) | 6 | ±2000 dps | ±16 g | brett lager |
| U8 | BMI270 | Bosch | LGA-14 3×2.5 (Bosch) | 6 | ±2000 dps | ±16 g | låg-effekt, brett lager |
| U9 | BMI323 | Bosch | LGA-14 (Bosch) | 6 | ±2000 dps | ±16 g | ny-gen |
| U10 | BMI160 | Bosch | LGA-14 (Bosch) | 6 | ±2000 dps | ±16 g | legacy, brett lager |
| U11 | **BMI088** | Bosch | LGA-16 (~3×4.5) | 6 | ±2000 dps | ±24 g | **hög-vibration** (drone/robot) → bra för vapen-rekyl. *Footprint approx (LGA-16 3×3) — verifiera mått om vald* |
| U12 | **LSM6DSR** | ST | LGA-14 2.5×3 (ST) | 6 | ±4000 dps | ±16 g | matchar IIM-42653 dps |
| U13 | LSM6DSO32 | ST | LGA-14 (ST) | 6 | ±2000 dps | ±32 g | låg-effekt |
| U14 | LSM6DSV16X | ST | LGA-14 (ST) | 6 | ±4000 dps | ±16 g | inbyggd sensor-fusion (MLC) |
| U15 | **ISM330DHCX** | ST | LGA-14 (ST) | 6 | ±4000 dps | ±16 g | industri (maskin/robot) |
| U16 | ASM330LHHX | ST | LGA-14 (ST) | 6 | ±4000 dps | ±16 g | fordon AEC-Q100 (robustast) |
| U17 | **ICM-20948** | TDK | QFN-24 3×3 | **9** | ±2000 dps | ±16 g | +magnetometer → bäring utan GNSS |
| U18 | MPU-9250 | TDK | QFN-24 3×3 | **9** | ±2000 dps | ±16 g | 9-ax legacy (EOL — verifiera) |

## Val-kriterier för STRILAS
Vapnet/hjälmen behöver: hög dynamik (rekyl-transienter, snabba huvudrörelser), lågt brus
(GNSS/INS-fusion, världsfast skottlinje), I²C+SPI, helst industri-temp.
- **Vill du matcha/överträffa nuvarande ±4000 dps:** U1, U6, U12, U14, U15, U16.
- **Bäst precision (lägst brus):** U3, U6.
- **Tål mest vibration/g (vapen):** U11 (BMI088), U5/U1 (±32 g).
- **Lägg till magnetometer (9-axel):** U17 (ICM-20948).

## Efter lager-kollen
1. Notera vilka MPN NextPCB har i lager.
2. Välj en lämplig (helst i TDK-familjen → noll ändring på de riktiga korten; annars byt footprint
   till ST/Bosch-familjens i `*_netlist.py` + omplacera/route den lilla IMU:n).
3. Uppdatera `gen_nextpcb.py` (ta IMU:n ur prototyp-DNP) och regenerera leverans.
