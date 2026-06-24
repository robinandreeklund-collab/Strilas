#!/usr/bin/env python3
"""
STRILAS — Class 1-ögonsäkerhets-strömbudget för skott-emittern (940 nm).

INGENJÖRSESTIMAT för att sätta en konservativ design-/startström + HW-tak.
Detta ERSÄTTER INTE en formell IEC 60825-1-mätning: den slutliga Class 1-
bedömningen kräver uppmätt accessible emission (AE) vid aperturen med kalibrerad
utrustning, vid det LÅSTA pulsformatet. Här beräknas radiometrin exakt och jämförs
mot en KONSERVATIV punktkälle-MPE; den verkliga marginalen beror på källans
SKENBARA storlek (extended-source-faktorn C6) som MÅSTE MÄTAS.

Alla antaganden är explicita nedan. Wavelength = 940 nm.
"""
import math

# ---------- emitter-radiometri (vår modell) ----------
PHI_PER_A   = 1.08      # W radiant flöde per A (SFH 4715AS-klass; 940 nm-syskon ~likn.)
LENS_EFF    = 0.80      # Carclo TIR-effektivitet
BEAM_HALF   = 7.5       # grader (Carclo 10195 "medium spot"); narrow ±5° ger MER Ie (värre)
N_EMIT      = 2         # 2 emittrar (delar lasten; OBS: 2 separata skenbara källor – se not)

def derate(I):          # LED-effektivitet sjunker med ström
    return max(1.0 - 0.05*(I-1.0), 0.80)

def omega(half_deg):
    return 2*math.pi*(1-math.cos(math.radians(half_deg)))

def Ie_total(I):        # W/sr on-axis, kombinerat
    phi = PHI_PER_A*I*derate(I)
    return LENS_EFF*phi/omega(BEAM_HALF)*N_EMIT

# ---------- exponeringsgeometri (IEC 60825-1 Condition 3) ----------
D_EVAL   = 0.10         # m (7 mm-apertur @ 100 mm)
PUPIL_A  = math.pi*(3.5e-3)**2   # m^2 (7 mm pupill)

# ---------- pulsformat (MilesTag II @ 56 kHz) ----------
CARRIER_DUTY = 0.50     # bärvågens on-tid
PKT_MS       = 14.0     # paketlängd
RATE_SEMI    = 2.0      # paket/s (halvautomat)
RATE_FULL    = 13.0     # paket/s (helautomat ~780 rpm)
duty_semi = CARRIER_DUTY*PKT_MS*1e-3*RATE_SEMI
duty_full = CARRIER_DUTY*PKT_MS*1e-3*RATE_FULL

# ---------- MPE (700–1050 nm, retinal termisk) ----------
LAMBDA = 940
C4 = 10**(0.002*(LAMBDA-700))           # = 3.02 @ 940 nm
# Termisk MPE, punktkälla, lång exponering (~10 s, plateau): radiant exponering
# H = 1.8*C4*t^0.75 mJ/cm^2  →  medel-irradians vid hornhinnan:
def E_mpe_pt(t=10.0):                    # W/m^2 (punktkälla, KONSERVATIV)
    H_mJcm2 = 1.8*C4*t**0.75             # mJ/cm^2
    H_Jm2 = H_mJcm2*1e-3*1e4             # → J/m^2
    return H_Jm2/t                       # medel-irradians
E_MPE_PT = E_mpe_pt(10.0)               # ~30.6 W/m^2

# extended-source-faktor C6 = alpha/alpha_min, alpha_min=1.5 mrad, alpha_max=100 mrad
# Skenbar källa = ? (die liten → C6≈1; linsöppning Ø20@100mm=200mrad → C6=max)
C6_MAX = 100/1.5                         # = 66.7 (om skenbar källa ≥ alpha_max)

def report():
    print(f"== STRILAS skott-emitter — Class 1-strömbudget (940 nm) ==")
    print(f"Antaganden: {N_EMIT}×LED, {LENS_EFF:.0%} lins, ±{BEAM_HALF}° kon, eval @ {D_EVAL*1000:.0f} mm, 7 mm pupill")
    print(f"Pulsduty: semi {duty_semi*100:.1f}%  full-auto {duty_full*100:.1f}%   C4={C4:.2f}")
    print(f"MPE (punktkälla, konservativ) ≈ {E_MPE_PT:.1f} W/m²   |   ×C6_max({C6_MAX:.0f}) ≈ {E_MPE_PT*C6_MAX:.0f} W/m²\n")
    print(f"{'I [A]':>6} {'Ie[W/sr]':>9} {'E@100mm':>9} {'Eavg full':>10} {'Eavg semi':>10} {'Peye full':>10}  verdikt(punktkälla)")
    for I in (0.25, 0.5, 1.0, 2.0, 3.0):
        Ie = Ie_total(I)
        E100 = Ie/D_EVAL**2
        Ef, Es = E100*duty_full, E100*duty_semi
        Peye_full_mW = Ef*PUPIL_A*1e3
        ok_pt = "OK" if Ef <= E_MPE_PT else f"{Ef/E_MPE_PT:.1f}× ÖVER"
        print(f"{I:>6.2f} {Ie:>9.1f} {E100:>9.0f} {Ef:>10.0f} {Es:>10.0f} {Peye_full_mW:>9.2f}m  {ok_pt}")

    # max ström för Class 1 (punktkälla) — full-auto & semi
    def max_I(duty):
        lo, hi = 0.0, 5.0
        for _ in range(60):
            mid = (lo+hi)/2
            if Ie_total(mid)/D_EVAL**2*duty <= E_MPE_PT: lo = mid
            else: hi = mid
        return lo
    print(f"\nMax ström för Class 1 (KONSERVATIV punktkälla, C6=1):")
    print(f"   full-auto: {max_I(duty_full):.2f} A   |   semi-auto: {max_I(duty_semi):.2f} A")
    print(f"Om skenbar källa ≥ α_max (uppmätt): taket ×{C6_MAX:.0f} →")
    print(f"   full-auto: {max_I(duty_full)*C6_MAX:.1f} A   |   semi-auto: {max_I(duty_semi)*C6_MAX:.1f} A  (≫ vårt 1–3 A → OK)")

if __name__ == "__main__":
    report()
    print("""
SLUTSATS (ärlig):
• Punktkälle-antagandet (worst case) är RESTRIKTIVT → max ~0.1 A full-auto, vilket dödar räckvidd.
• MEN en LED+lins är en UTSTRÄCKT källa; om uppmätt skenbar källa ≥ α_max relaxeras taket ~67× →
  då är 1–3 A Class 1 med marginal. SVARET HÄNGER HELT PÅ DEN SKENBARA KÄLLSTORLEKEN.
• => DESIGN-REGLER: (1) HW-strömtak via U6 sense-resistor; (2) börja 0.5–1 A; (3) cap full-auto-duty
  i firmware; (4) 2 separata emittrar = 2 skenbara källor (var och en lägre); (5) MÄT AE + skenbar
  källa per IEC 60825-1 INNAN modulen riktas mot människor. Halvautomat är ~6–7× snällare än full-auto.
• Enkelpuls- & pulståg-villkoren (N^-1/4) ska också verifieras vid mätningen.
""")
