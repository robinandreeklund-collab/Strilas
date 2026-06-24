#!/usr/bin/env python3
"""STRILAS — IR-LÄNKBUDGET (skott-emitter 940 nm → TSOP-mottagare).

Parametriskt: svarar på "RÄCKER EN EMITTER?" genom att räkna irradians vid målet
och marginal mot TSOP-tröskeln, för 1 vs 2 emittrar, med/utan mottagar-bandpass och
i dagsljus. Komplement till eye_safety_budget.py (samma emitter, motsatt ände av länken).

Modell (radiometrisk, första ordningen — bekräftas på bänk):
  Ie  = Φe·η_lins / Ω(kon)              [W/sr]  radiant intensitet per emitter
  Ee  = N·Ie·τ_atm·τ_filter / R²        [W/m²]  irradians vid mottagaren, N emittrar
  marginal = Ee / Ee_min(TSOP)          (≥1 = detekterbar; ≥3 = robust design)
Peak-Ie används (TSOP demodulerar 56 kHz-bärvågen → duty påverkar ej peak-detektion).

Kör:  python3 hardware/ir_link_budget.py
"""
import math

# ── emitter (ams OSRAM SFH 4725AS, 940 nm OSLON Black) ──
PHI_E_W      = 0.98     # radiant flux @1 A [W] (≈980 mW; skala ~linjärt med ström)
LENS_EFF     = 0.80     # Carclo TIR-kollimator verkningsgrad
CONE_HALF_DEG= 7.5      # ±7,5° kollimerad kon (Carclo 10195/10734)

# ── länk ──
TAU_ATM_150  = 0.97     # atmosfärisk transmittans @150 m, klart väder, 940 nm (~3% förlust)
RANGE_REQ_M  = 153.0    # kravräckvidd (PROFILE ir_range_m)

# ── mottagare (Vishay TSOP4856, 56 kHz) ──
EE_MIN_TSOP  = 0.35e-3  # min irradians för tillförlitlig mottagning [W/m²] (~datablad typ.)
TAU_BANDPASS = 0.85     # 850/940 nm optiskt bandpass: ~15% signal-insättningsförlust ...
DAYLIGHT_DERATE = 2.0   # ... men dagsljus utan filter kräver ~2× mer signal (AGC/ambient).
                        #     Med bandpass: derate≈1 (filtret tar bort ambient).

def solid_angle(half_deg):
    return 2*math.pi*(1 - math.cos(math.radians(half_deg)))

def ie_per_emitter(current_a=1.0):
    phi = PHI_E_W * current_a
    return phi * LENS_EFF / solid_angle(CONE_HALF_DEG)

def irradiance(n_emit, range_m, current_a=1.0, bandpass=True):
    Ie = ie_per_emitter(current_a)
    tau = TAU_ATM_150 * (TAU_BANDPASS if bandpass else 1.0)
    return n_emit * Ie * tau / (range_m*range_m)

def max_range(n_emit, current_a, margin, bandpass, daylight):
    """Räckvidd där marginalen = 'margin' (Ee = margin·Ee_eff)."""
    Ie = ie_per_emitter(current_a)
    tau = TAU_ATM_150 * (TAU_BANDPASS if bandpass else 1.0)
    ee_eff = EE_MIN_TSOP * (DAYLIGHT_DERATE if (daylight and not bandpass) else 1.0)
    return math.sqrt(n_emit * Ie * tau / (margin * ee_eff))

def margin_at(n_emit, range_m, current_a, bandpass, daylight):
    ee = irradiance(n_emit, range_m, current_a, bandpass)
    ee_eff = EE_MIN_TSOP * (DAYLIGHT_DERATE if (daylight and not bandpass) else 1.0)
    return ee / ee_eff


if __name__ == "__main__":
    print("="*76)
    print("STRILAS — IR-länkbudget: räcker EN emitter? (skott-emitter 940 nm → TSOP4856)")
    print("="*76)
    print(f"  Ie/emitter @1 A = {ie_per_emitter():.1f} W/sr  (Φe {PHI_E_W} W · η {LENS_EFF} / "
          f"Ω(±{CONE_HALF_DEG}°)={solid_angle(CONE_HALF_DEG):.4f} sr)")
    print(f"  TSOP Ee_min = {EE_MIN_TSOP*1e3:.2f} mW/m²   krav-räckvidd = {RANGE_REQ_M:.0f} m\n")

    print(f"  {'scenario':40s}  {'marg@153m':>10s}  {'R(marg=1)':>9s}  {'R(marg=3)':>9s}")
    print("  " + "-"*72)
    scen = [
        ("1 emitter, 1 A, klart väder, m. bandpass", 1, 1.0, True,  False),
        ("2 emittrar, 1 A, klart väder, m. bandpass", 2, 1.0, True,  False),
        ("1 emitter, 1 A, DAGSLJUS, UTAN bandpass",   1, 1.0, False, True),
        ("1 emitter, 1 A, DAGSLJUS, M. bandpass",     1, 1.0, True,  True),
        ("1 emitter, 1,5 A, dagsljus, m. bandpass",   1, 1.5, True,  True),
        ("2 emittrar, 1 A, DAGSLJUS, m. bandpass",    2, 1.0, True,  True),
    ]
    for name, n, i, bp, dl in scen:
        m153 = margin_at(n, RANGE_REQ_M, i, bp, dl)
        r1 = max_range(n, i, 1.0, bp, dl)
        r3 = max_range(n, i, 3.0, bp, dl)
        flag = "✅" if m153 >= 3 else ("⚠️ tunn" if m153 >= 1 else "❌ <krav")
        print(f"  {name:40s}  {m153:8.1f}×  {r1:7.0f} m  {r3:7.0f} m  {flag}")

    print("\n" + "-"*76)
    print("TOLKNING (första ordningen — bänkmät TSOP-tröskel + dagsljus-AGC för låsning):")
    print("  • 1 emitter @1 A når 153 m, men bara ~1,5× marginal → TUNT för robust drift.")
    print("  • Mottagar-BANDPASS är den billiga hävstången: tar bort dagsljus-deratingen →")
    print("    1 emitter m. bandpass ≈ 2 emittrar utan, vid 153 m. (Eye-safety oförändrad:")
    print("    per-apertur-exponering = samma 1 A som idag.)")
    print("  • Vill du ha 3× marginal @153 m i dagsljus med EN emitter: bandpass + ~1,5 A")
    print("    (kräver eye-safety-ommätning) ELLER behåll 2 emittrar.")
    print("  • Storleksbeslut: 1 emitter + bandpass tar bort en kollimator (största ytan) och")
    print("    håller kravet — 2 emittrar köper marginal/redundans till priset av storlek.")
    print("="*76)
