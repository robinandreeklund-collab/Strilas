#!/usr/bin/env python3
"""STRILAS — spegelvänd J1:s nät-tilldelning på det FÄRDIGA optikkortet och nollställ
routningen INFÖR omroutning, UTAN att röra placeringen (P4-standoff-hålen HP1-4, C2, Q2
m.m. som finjusterats direkt på kortet, ej i receiver_place.py — se commit 169eb9e).

Bakgrund: P4 monteras stackad bakom optiken (ansikte-mot-ansikte) → kontaktens pinout
MÅSTE speglas (pad k = forna pad 15-k) så att BÅDE kontaktstiften OCH de 4 standoff-hålen
möts fysiskt. Tidigare satt näten i ospeglad ordning → hålen passade bara i den orientering
där kontakten gick baklänges (nCS→VSYS m.fl.). Varje signal hamnar nu på SAMMA P4-GPIO som
förr (GPIO32/27/26/23/22) men på den fysiskt rätta paden.

Körs på det incheckade (routade) kortet; därefter: thermal_vias → DSN → power_class →
freerouting → ses_apply → weapon_stitch → flip_j1_back → weapon_finish → gerbers/STEP."""
import pcbnew

PCB = "hardware/weapon-module.kicad_pcb"
# board-pad -> nät (spegelvänt mot tidigare); None = NC
NEW = {1: "VBAT", 2: "GND", 3: None, 4: "+3V3", 5: "IR_MOD", 6: None, 7: "GND",
       8: "MISO", 9: "SCK", 10: None, 11: "IMU_INT", 12: "GND", 13: "MOSI", 14: "nCS"}
# flip_j1_back-axlar (för att vända tillbaka kontakterna till FRAM inför routning)
UNFLIP = {"J1": True, "J2": False}


def main():
    b = pcbnew.LoadBoard(PCB)
    nonet = b.FindNet("")
    for f in b.GetFootprints():
        r = f.GetReference()
        if r in UNFLIP and f.IsFlipped():
            f.Flip(f.GetPosition(), UNFLIP[r])           # tillbaka till FRAM (flip är sin egen invers)
        if r == "J1":
            for pd in f.Pads():
                k = int(pd.GetName()); nm = NEW[k]
                pd.SetNet(b.FindNet(nm) if nm else nonet)
    # nollställ routning (spår + vior + zoner) — placeringen rörs ej.
    # samla ALLT innan borttagning (att läsa b.Zones() efter b.Remove(track) kraschar)
    to_remove = list(b.GetTracks()) + list(b.Zones())
    for it in to_remove:
        b.Remove(it)
    pcbnew.SaveBoard(PCB, b)
    sides = {f.GetReference(): ("BAK" if f.IsFlipped() else "FRAM")
             for f in b.GetFootprints() if f.GetReference() in UNFLIP}
    print(f"  J1 spegelvänd, kontakter {sides}, routning nollställd (placering bevarad)")


if __name__ == "__main__":
    main()
