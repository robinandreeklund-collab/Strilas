# STRILAS prototyp — koppla IMU-breakout (GY-601N1) → ESP32-P4

> Figur: [`imu-breakout-koppling.png`](imu-breakout-koppling.png)
> Mappningen är härledd ur **vårt** kort: optikens SPI-nät → optik-J1 → P4 edge-B-GPIO
> (verifierat 0.000 mm mot `_pads_z`). Optik-IMU:n är **DNP** → du kör breakouten på samma
> GPIO:er som firmware redan väntar IMU:n på → **ingen mjukvaruändring**.

## Koppling (GY-601N1 i SPI-läge, välj ICM-42688-varianten)
| GY-601N1-stift | funktion | → ESP32-P4 | (vårt nät) |
|---|---|---|---|
| **VCC** | matning | **3V3** | mata 3,3 V — **EJ 5V** (P4 är 3,3 V-logik) |
| **GND** | jord | **GND** | — |
| **SCL/SCLK** | SPI-klocka | **GPIO23** | SCK |
| **SDA/SDI** | MOSI (in t. IMU) | **GPIO27** | MOSI |
| **SA0/SDO** | MISO (ut fr. IMU) | **GPIO22** | MISO |
| **CS** | chip-select | **GPIO32** | nCS |
| **INT1** | data-ready avbrott | **GPIO26** | IMU_INT |
| INT2 · RX/CL · TX/DA · PS | — | — | **ej anslutna** (raw SPI, ej UART/MCU-läge) |

## Var sitter GPIO:erna på P4?
GPIO22/23/26/27/32 ligger på **P4 edge B** (samma stiftrad som optik-J1 pluggar i). Hitta dem på
Waveshare-modulens silk/pinout. Du kan koppla breakouten **direkt till P4:ans edge-B-stift**.

## Varför ingen krock
De här linjerna går även till optik-J1 → optikens **U1-footprint (IMU)**, men den är **DNP**
(obestyckad) → ingen annan SPI-enhet finns på SCK/MOSI/MISO → breakouten är ensam på bussen.

## Att tänka på
- **Matning 3,3 V**, inte 5 V: breakouten tål 3–5 V, men dess logiknivåer ut (MISO/INT) ska matcha
  P4:ans 3,3 V. Med VCC=3,3 V blir I/O 3,3 V = säkert. (Vid 5 V finns risk för 5 V-logik → skadar P4.)
- **SPI-läge:** se till att breakouten pratar SPI mot chipet (SCL/SDA/SA0/CS = chipets egna SPI-stift,
  inte MCU/UART-utgången). PS/RX/TX lämnas.
- **ODR:** kör hög utdatatakt (1–8 kHz) i SPI för recoil-transienten; lågt SPI-klockval (≤8–10 MHz)
  räcker och är robust över bygelkablar.
- Detta är prototypens IMU; i produktion sätts IMU:n (IIM-42653) tillbaka **på optikkortet**,
  stelt mot optiska axeln (bättre kamera-IMU-extrinsics).
