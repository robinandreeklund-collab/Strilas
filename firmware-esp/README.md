# STRILAS — ESP-IDF nod-firmware (Fas 3)

Porten av nod-logiken till riktig firmware för de tre P4-noderna (**optik/vapen, väst, hjälm**),
enligt planen i `firmware/README.md`: nodernas hot-path → C; **servern (`adjudicator`/`engine`)
stannar i Python** på laptop/gateway. Samma kodbas + roll-flagga ger alla tre noderna.

## Vad som är VERIFIERAT vs SCAFFOLDING

| Lager | Status | Hur |
|---|---|---|
| `components/strilas_core/` — **portabel algoritm-kärna** (blob-CCL O(n), pose, fire-control, ballistik, rullande kod) | ✅ **host-kompilerad + paritetstestad mot Python** | `make -C test` → 17 checkar, ALLA OK |
| `components/hal/hal_msg.c` — JSON-packning (matchar `protocol.py`) | ✅ host-länkad | ingår i nod-bygget |
| `main/node_*.c` — nod-logiken (optik/mål) wirad mot core+HAL | ✅ **hela trädet länkar koherent på host** | `cc ... -o strilas_node` (se nedan) |
| `components/hal/hal_esp.c` — **HW-drivrutiner** (kamera/IMU/TSOP/IR/TPIC/radio) | 🔧 **integrations-stubbar** med TODO → ESP-IDF-driver + pinout | fylls vid bänk-bringup (HIL) |
| ESP-IDF-bygge (`idf.py build`) | ⏳ kräver ESP-IDF-toolchain + kisel | scaffolding klar |

Kärnan kompileras och testas **utan ESP-IDF och utan hårdvara** — det är beviset att matematiken
portar rent. HW-stubbarna är den enda fil som rör kisel och fylls i när korten finns på bänk.

## Bygg & test

```bash
# 1) Host-paritetstest av C-kärnan mot Python-referensen (ingen ESP-IDF):
make -C firmware-esp/test
#    → ballistik/fire-control/pose/rullande-kod = Python; O(n)-CCL hittar alla 5 LED.

# 2) Host-länkkoll av hela nod-firmware-trädet (struktur-sanity, ingen ESP-IDF):
cc -O2 -Icomponents/strilas_core -Icomponents/hal/include \
   main/*.c components/hal/*.c components/strilas_core/strilas_core.c -lm -o /tmp/strilas_node

# 3) Riktigt nod-bygge (kräver ESP-IDF + ESP32-P4):
idf.py -DSTRILAS_ROLE=0 set-target esp32p4 build   # 0=optik, 1=väst, 2=hjälm
```

## Arkitektur

```
main/strilas_main.c     roll-väljare (-DSTRILAS_ROLE) → app_main()
main/node_optik.c       kamera→CCL→pose; avtryck→fire-control→signerad FireEvent→mesh
main/node_target.c      TSOP→IRHit→mesh; verdict→vibrera; 10 Hz PlayerState (lag-komp)
components/strilas_core  PORTABEL matematik (= Python-referensen, paritetstestad)
components/hal           hal.h (gränssnitt) · hal_esp.c (HW-stubbar) · hal_msg.c (JSON)
```

Nod ↔ server: ESP-NOW/WiFi6-mesh (C6-coprocessorn), topics `fire`/`irhit`/`pstate`/`verdict`.
Gateway bryggar topics → MQTT till Python-`engine.py`. Mesh-semantiken (latens/jitter/loss/
tidssynk) är redan utvärderad i Fas 1 (`firmware/run_mesh.py`).

## Återstår till skarp drift (HIL — Fas 2:s checklista)

Fyll `hal_esp.c` vid bänk-bringup och mät: kamera-grab-fps (MIPI-CSI vs USB-UVC + ROI),
CCL µs på PPA vs CPU, PnP µs, end-to-end fyr→FireEvent, ström per läge (→ drifttid),
dagsljus-SNR @150 m. HMAC i säkert element (ATECC608/eFuse). Då är porten skarp.
