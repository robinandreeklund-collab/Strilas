# STRILAS vapen-stack — komplett BOM

Stack: **optik (weapon-module) → ESP32-P4 → fire-control**. 3V3 matas batteri→VSYS→P4-reg→3V3 (FC via edge-B-tapp).

## Optik (weapon-module)  (37 st)

| Antal | Referenser | Värde | Footprint | Typ |
|---|---|---|---|---|
| 1 | R1 | 100k | `Resistor_SMD:R_0805_2012Metric` | elektrisk |
| 2 | C3,C4 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | elektrisk |
| 1 | C2 | 100uF | `Capacitor_SMD:C_1210_3225Metric` | elektrisk |
| 1 | C1 | 10uF | `Capacitor_SMD:C_1206_3216Metric` | elektrisk |
| 1 | C5 | 1uF | `Capacitor_SMD:C_0805_2012Metric` | elektrisk |
| 1 | R3 | 220R | `Resistor_SMD:R_0805_2012Metric` | elektrisk |
| 1 | J2 | 2S batteri (JST-XH) | `Connector_JST:JST_XH_S2B-XH-A_1x02_P2.50mm_Horizontal` | elektrisk |
| 1 | R2 | 3R3_2W | `Resistor_SMD:R_2512_6332Metric` | elektrisk |
| 1 | Q2 | AO3400 | `Package_TO_SOT_SMD:SOT-23` | elektrisk |
| 1 | Q1 | AO3401 | `Package_TO_SOT_SMD:SOT-23` | elektrisk |
| 1 | U1 | ICM-42670-P | `strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx` | elektrisk |
| 1 | J1 | P4-socket (edge B) | `Connector_PinSocket_2.54mm:PinSocket_1x14_P2.54mm_Vertical` | elektrisk |
| 1 | F1 | PTC_1A | `Fuse:Fuse_1206_3216Metric` | elektrisk |
| 2 | D2,D3 | SFH4725S_940nm | `strilas:IR_Emitter_OSRAM_OSLON_Black_SFH4725S` | elektrisk |
| 1 | D1 | SMBJ12A | `Diode_SMD:D_SMB` | elektrisk |
| 8 | H12,H13,H14,H15,H16,H17,H18,H19 | Carclo10734-ben_Ø2.1 | `MountingHole:MountingHole_2.1mm` | mekanik |
| 8 | H1,H2,H20,H3,H4,H5,H6,H7 | M2.5 | `MountingHole:MountingHole_2.5mm` | mekanik |
| 4 | H10,H11,H8,H9 | M2_kamera | `MountingHole:MountingHole_2.2mm_M2` | mekanik |

## Fire-control  (22 st)

| Antal | Referenser | Värde | Footprint | Typ |
|---|---|---|---|---|
| 5 | C1,C3,C4,C5,C6 | 100nF | `Capacitor_SMD:C_0402_1005Metric` | elektrisk |
| 1 | C2 | 1uF | `Capacitor_SMD:C_0402_1005Metric` | elektrisk |
| 2 | R1,R2 | 4k7 | `Resistor_SMD:R_0805_2012Metric` | elektrisk |
| 2 | U1,U2 | ICM-42670-P | `strilas:InvenSense_LGA-14_2.5x3mm_ICM-456xx` | elektrisk |
| 1 | J6 | MAGWELL_SW | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | elektrisk |
| 1 | J5 | MAG_REL_SW | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | elektrisk |
| 1 | J8 | NFC PN532 (I²C) | `Connector_JST:JST_PH_B4B-PH-K_1x04_P2.00mm_Vertical` | elektrisk |
| 1 | J1 | P4-socket (edge A) | `Connector_PinSocket_2.54mm:PinSocket_1x12_P2.54mm_Vertical` | elektrisk |
| 1 | J4 | RACK_SW | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | elektrisk |
| 1 | J3 | TRIGGER | `Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical` | elektrisk |
| 1 | J2 | edge-B kraft-tapp 3V3+GND | `Connector_PinSocket_2.54mm:PinSocket_1x03_P2.54mm_Vertical` | elektrisk |
| 1 | J7 | recoil-styrning | `Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical` | elektrisk |
| 4 | H1,H2,H3,H4 | M2 | `MountingHole:MountingHole_2.2mm_M2` | mekanik |

## P4-carrier (lödbara headers på Waveshare-modulen)  (8 st)

| Antal | Referenser | Värde | Footprint | Typ |
|---|---|---|---|---|
| 1 | J_CAM | PinHeader_1x04_P2.54mm_Vertical | `PinHeader_1x04_P2.54mm_Vertical` | elektrisk |
| 1 | J_A | PinHeader_1x12_P2.54mm_Vertical | `PinHeader_1x12_P2.54mm_Vertical` | elektrisk |
| 1 | J_B | PinHeader_1x14_P2.54mm_Vertical | `PinHeader_1x14_P2.54mm_Vertical` | elektrisk |
| 1 | USBC | USB_C_Receptacle_HRO_TYPE-C-31-M-12 | `USB_C_Receptacle_HRO_TYPE-C-31-M-12` | elektrisk |
| 4 | MP1,MP2,MP3,MP4 | MountingHole_2.2mm_M2 | `MountingHole_2.2mm_M2` | mekanik |

## Externa moduler (kabelanslutna)

| Antal | Artikel | Variant | Not |
|---|---|---|---|
| 1 | ESP32-P4-WIFI6 | Waveshare | Huvudprocessor (Pico-format). Edge B→optik, edge A→FC. |
| 1 | PN532 NFC-modul | modul | Magasin-NFC. Kabel → FC J8 (I²C, 3V3). |
| 1 | USB-kamera (OV9281/B0332) | modul | Kabel → P4 J_CAM (USB 2.0). |
| 1 | LiPo-batteri | — | Kabel → optik J2 (VBAT). |
| 1 | Recoil-effektkort | separat PCB | eFuse+aktuator. Kabel → FC J7 (PWM/FAULT/GND). |
| 4 | Mikrobrytare | — | Trigger/rack/mag-release/magwell. Kabel → FC J3–J6. |
| 4 | M2-standoff + skruv | 15 mm | Genomgående stack: optik–P4–FC. |

**PCB-komponenter totalt: 67 st** (exkl. externa moduler).
