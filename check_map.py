"""Derive the knock-limited and MBT spark maps from the plant, and check they
look like a real ignition calibration.

TWO THINGS THIS FILE USED TO GET WRONG, FIXED 9 SEPTEMBER 2026
--------------------------------------------------------------
1. FAIL-OPEN KNOCK LIMIT. `klsa` started at None and the caller fell back to
   `min(mbt, klsa) if klsa is not None else mbt`. In a cell that knocks at
   EVERY spark in the search range, klsa stayed None and the table printed
   MBT -- the single most knock-prone advance in the row -- as if it were the
   calibration. That is why the 1200 rpm row read 11, 3, 21, 22: the 180 and
   220 kPa cells knock at 0 degrees BTDC and the fallback published 21 and 22.
   A knock limiter that publishes MBT when it cannot find a safe advance is
   worse than no limiter. Those cells are now marked `knk`.

2. LAST KNOCK-FREE, NOT LARGEST SAFE. `klsa = sp` with no break records the
   last advance seen below the threshold. The knock integral is not monotonic
   in spark -- it turns over near 42 degrees as combustion finishes too early
   to dwell at peak temperature -- so a cell whose integral dipped back under
   1.0 at extreme advance would have published that extreme advance as safe.
   No cell in the current map does this, but the search now stops at the first
   knocking advance, which is what "knock limit" means.

The compressor cannot reach every cell in the grid. At 1200 rpm the wastegate
is irrelevant because the turbine has nothing to work with: the highest MAP
that closes on itself against boost_ceiling_kpa is 148 kPa. Cells above their
speed's ceiling are marked `--` rather than filled with numbers from an
operating point this engine cannot occupy.
"""
import numpy as np
from plant import Operating, run_cycle, b58, boost_ceiling_kpa

GEO = b58()          # the one engine; never rely on run_cycle's default

RPMS = [1200, 1600, 2000, 2500, 3000, 4000, 5000, 6000]
MAPS = [40, 60, 80, 100, 140, 180, 220]

KI_LIMIT = 1.0


def reachable(rpm, map_kpa, lam=1.0):
    """Can the compressor actually sustain this MAP at this speed?

    Self-consistent, not a lookup: run the cycle AT the requested MAP, take the
    airflow it implies, and ask the fitted compressor envelope whether it can
    deliver that flow at that pressure ratio. If not, the cell is off the map.
    """
    r = run_cycle(Operating(rpm=rpm, map_kpa=float(map_kpa), spark_btdc=15.0, lam=lam),
                  geo=GEO)
    return boost_ceiling_kpa(r.mdot_air_gps) >= map_kpa


def sweep(rpm, map_kpa, lam, iat_k=298.0):
    """Return (MBT advance, knock-limited advance).

    klsa is the largest advance for which EVERY advance up to and including it
    is knock-free -- so the search stops at the first knocking cell. klsa is
    None when the point knocks even at 0 degrees BTDC, which means there is no
    safe spark and the caller must say so rather than substitute MBT.
    """
    best_t, mbt, klsa = -1e9, None, None
    knocked = False
    for sp in np.arange(0.0, 46.0, 1.0):
        r = run_cycle(Operating(rpm=rpm, map_kpa=map_kpa, spark_btdc=float(sp), lam=lam,
                                iat_k=iat_k, p_exh_kpa=max(105.0, map_kpa * 1.12)),
                      geo=GEO)
        if r.torque_nm > best_t:
            best_t, mbt = r.torque_nm, sp
        if not knocked:
            if r.knock_integral < KI_LIMIT:
                klsa = sp
            else:
                knocked = True          # first knock defines the limit
    return mbt, klsa


def lam_for(m):
    return 1.0 if m <= 120 else (0.92 if m <= 180 else 0.85)


print("Final spark map = min(MBT, knock limit).  lambda scheduled by load.")
print("  --  = above the compressor ceiling at that speed, not an operating point")
print("  knk = knocks at 0 deg BTDC; no knock-free spark exists, retard cannot fix it\n")
print("  MAP kPa |" + "".join(f"{m:>7d}" for m in MAPS))
print("  " + "-" * (10 + 7 * len(MAPS)))

n_unreach = n_knk = 0
for rpm in RPMS:
    cells = []
    for m in MAPS:
        if not reachable(rpm, m):
            cells.append("--")
            n_unreach += 1
            continue
        mbt, klsa = sweep(rpm, m, lam_for(m))
        if klsa is None:
            cells.append("knk")
            n_knk += 1
        else:
            cells.append(f"{min(mbt, klsa):.0f}")
    print(f"  {rpm:5d}   |" + "".join(f"{c:>7s}" for c in cells))

print(f"\n  {n_unreach} cells above the compressor ceiling, "
      f"{n_knk} reachable cells with no knock-free spark.")

print("\nSpot checks at the final map:")
for rpm, m in [(2000, 60), (2500, 100), (3000, 180), (5000, 220)]:
    lam = lam_for(m)
    mbt, klsa = sweep(rpm, m, lam)
    if klsa is None:
        print(f"  {rpm:5d} rpm {m:4d} kPa  NO KNOCK-FREE SPARK -- not a valid cell")
        continue
    sp = min(mbt, klsa)
    r = run_cycle(Operating(rpm=rpm, map_kpa=m, spark_btdc=float(sp), lam=lam,
                            p_exh_kpa=max(105.0, m * 1.12)), geo=GEO)
    lim = "knock" if klsa < mbt else "MBT"
    print(f"  {rpm:5d} rpm {m:4d} kPa  spark {sp:4.0f} ({lim}-limited)  "
          f"T {r.torque_nm:6.1f} Nm  BSFC {r.bsfc_gpkwh:6.1f}  EGT {r.egt_c:4.0f} C  "
          f"Pmax {r.p_max_bar:5.1f} bar  MFB50 {r.mfb50_deg:5.1f}")
