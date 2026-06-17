#!/usr/bin/env python3
"""STRILAS — ALT-MONTERING optik: spegla HELA kortets placering om mittlinjen (x=150) så att
J1 (P4 edge B, 14-pin) + de 4 P4-standoff-hålen hamnar på MOTSATTA kanten. Krävs när P4 monteras
med komponentsidan UTÅT (ESP/USB-C bort från optik) — då vetter edge B mot optikens andra kant.

Spegling av ALLA footprints bevarar alla inbördes avstånd → garanterat krockfritt (enda undantag
J2:s asymmetriska JST-courtyard, som knuffas några mm). Pin-Y-höjder bevaras (spegling om vertikal
axel) → J1:s GPIO-mappning oförändrad. Emittrarna byter plats (symmetriska, optik oförändrad);
termiska vior läggs på de speglade lägena vid omroutning. Backup: weapon-module-backup-p4-inward.

Kör EN gång på det routade kortet; därefter omroutning (freerouting) + finish. EJ idempotent."""
import pcbnew
b=pcbnew.LoadBoard("hardware/weapon-module.kicad_pcb")
AXIS_NM=int(2*150.0*1e6)
UNFLIP={"J1":True,"J2":False,"J3":False}
# 1) spegla ALLA footprints om x=150 (behåll y/rot/lager/nät) -> krockfritt (avstånd bevaras)
for fp in b.GetFootprints():
    p=fp.GetPosition()
    fp.SetPosition(pcbnew.VECTOR2I(AXIS_NM-p.x, p.y))
# 2) vänd tillbaka kontakter till FRAM inför routning (paddar är THT -> bevaras)
for fp in b.GetFootprints():
    r=fp.GetReference()
    if r in UNFLIP and fp.IsFlipped():
        fp.Flip(fp.GetPosition(), UNFLIP[r])
# 3) nollställ routning (samla innan borttagning)
for it in list(b.GetTracks())+list(b.Zones()):
    b.Remove(it)
pcbnew.SaveBoard("hardware/weapon-module.kicad_pcb", b)
print("speglat + nollställt")
