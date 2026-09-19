"""new_drive.py — what is a candidate drive actually WORTH, before you add it?

    python new_drive.py logs/raw/<new>.csv

WHY THIS EXISTS
---------------
CLAUDE.md's "when a new drive CSV arrives" routine tells you to rebuild the
dataset and re-score the model. That answers "did anything break". It does not
answer the question people actually ask, which is **did this drive buy us
anything**, and the honest answer is usually "no, and here is what would."

Nine drives in, the things this project still needs are specific and short:

  1. INDEPENDENT READINGS at high flow. AUDIT.md H4: a row count is not a
     measurement count, because the exporter polls one channel per row and
     forward-fills the rest. The top of the compressor envelope currently rests
     on FOUR readings. A drive that adds ten is worth more than one that adds
     ten thousand rows.
  2. THE KNOCK QUESTION. AUDIT.md H5: the model's knock integral and the car's
     own retard channel correlate at -0.149 -- no relationship at all. Settling
     that needs a drive carrying BOTH ignition-angle channels at a rate fast
     enough to resolve them.
  3. OPERATING POINTS ABOVE 74 kPa. Everything the model says above that is
     extrapolation, and steady points need steady driving, which is light-load
     driving. This is the hardest one to get and the most valuable.
  4. THE EMPTY COMPRESSOR BIN, 0.33-0.36 kg/s corrected. Probably unreachable:
     the MAF channel saturates at 1020 kg/h. Cold dense air is the only chance.

This script scores a candidate against those four and says plainly whether it
helps. It does NOT modify anything -- run it before build_dataset.py, decide,
then follow the routine in CLAUDE.md.

READ-ONLY, like everything else here. It opens the CSV and prints.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

MAF_CEILING_KGH = 1019.9       # mistake 7
VALID_LO, VALID_HI = 30.0, 74.0    # the validated manifold-pressure span


def fresh(series: pd.Series) -> int:
    """Independent readings: one per genuine poll. AUDIT.md H4."""
    return int((series.diff().fillna(1.0) != 0).sum())


def col(df, *names):
    for n in names:
        if n in df.columns:
            return pd.to_numeric(df[n], errors="coerce")
    return None


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    path = sys.argv[1]
    df = pd.read_csv(path, encoding="utf-8-sig", low_memory=False)
    name = os.path.basename(path)

    t = col(df, "Time")
    rows = len(df)
    span = float(t.iloc[-1] - t.iloc[0]) if t is not None and rows else 0.0
    n_ch = sum(1 for c in df.columns if c != "Time")
    per_ch = span / max(rows, 1) * n_ch

    print("=" * 74)
    print(f"  {name}")
    print("=" * 74)
    print(f"  {rows} rows over {span/60:.1f} min, {n_ch} channels")
    print(f"  per-channel interval ~{per_ch:.2f} s  "
          f"(26 channels gave 7.5 s, 7 gave 1.45 s -- CLAUDE.md mistake 13b)")

    # ---- does it contribute samples at all? --------------------------------
    ect = col(df, "Coolant temperature")
    warm = None
    if ect is None:
        print("\n  NO COOLANT CHANNEL -> contributes ZERO samples and ZERO")
        print("  operating points, by design. That is fine for a purpose-built")
        print("  drive (pull01 was), but it cannot change any calibration.")
    else:
        warm = ect > 70
        print(f"\n  coolant present; {int(warm.sum())} of {rows} rows are warm (>70 C)")

    verdict = []

    # ---- 1. independent readings at high flow ------------------------------
    air = col(df, "Air mass flow")
    print("\n" + "-" * 74)
    print("  1. INDEPENDENT READINGS  (AUDIT.md H4 -- the binding constraint)")
    print("-" * 74)
    if air is None:
        print("  no air-mass channel; cannot judge")
    else:
        a = air.copy()
        pinned = int((a >= MAF_CEILING_KGH).sum())
        hi = a > 600
        print(f"  air mass: {fresh(a)} independent readings in {rows} rows "
              f"({rows/max(fresh(a),1):.0f}x inflation)")
        print(f"  above 600 kg/h: {int(hi.sum())} rows, "
              f"{fresh(a[hi]) if hi.any() else 0} readings")
        print(f"  pinned at the {MAF_CEILING_KGH:.0f} kg/h ceiling: {pinned} rows")
        if hi.any() and fresh(a[hi]) >= 10:
            verdict.append(("HELPS", f"{fresh(a[hi])} independent high-flow readings "
                                     "-- the envelope's top bins have 4-5 each"))
        elif hi.any():
            verdict.append(("marginal", f"only {fresh(a[hi])} high-flow readings"))
        else:
            verdict.append(("no", "never goes above 600 kg/h"))

    # ---- 2. the knock question ---------------------------------------------
    tgt = col(df, "Target ignition angle from torque intervention")
    act = col(df, "Actual ignition angle")
    print("\n" + "-" * 74)
    print("  2. THE KNOCK QUESTION  (AUDIT.md H5 -- the biggest open one)")
    print("-" * 74)
    if tgt is None or act is None:
        print("  MISSING one or both ignition-angle channels.")
        print("  Needs BOTH 'Target ignition angle from torque intervention'")
        print("  and 'Actual ignition angle' to say anything.")
        verdict.append(("no", "cannot address the knock question"))
    else:
        retard = (tgt - act)
        ok = retard.between(-5, 45)
        r = retard[ok]
        print(f"  retard: median {r.median():.2f} deg, p95 {r.quantile(.95):.2f}, "
              f"max {r.max():.2f}")
        print(f"  {fresh(act)} independent ignition-angle readings")
        print(f"  retarding >1 deg on {100*(r>1).mean():.1f} % of rows")
        if fresh(act) >= 100 and (r > 1).mean() > 0.05:
            verdict.append(("HELPS", f"{fresh(act)} ignition readings with real "
                                     "retard -- can test the knock model"))
        else:
            verdict.append(("marginal", "ignition channels present but thin"))

    # ---- 3. load coverage ---------------------------------------------------
    print("\n" + "-" * 74)
    print("  3. OPERATING RANGE  (validated span is 30-74 kPa)")
    print("-" * 74)
    try:
        from plant import map_from_airflow, charge_temperature, b58
        rpm = col(df, "Engine speed")
        amb = col(df, "Ambient temperature")
        if air is not None and rpm is not None:
            geo = b58()
            m = warm if warm is not None else pd.Series(True, index=df.index)
            sel = m & rpm.gt(600) & air.gt(0) & air.lt(MAF_CEILING_KGH)
            mp = []
            for a_, n_, ta in zip(air[sel], rpm[sel],
                                  (amb[sel] if amb is not None else [25.0]*int(sel.sum()))):
                tc = charge_temperature((ta if ta == ta else 25.0) + 273.15, 363.0)
                mp.append(map_from_airflow(a_ * 1000.0 / 3600.0, n_, tc, geo=geo))
            mp = np.array([x for x in mp if np.isfinite(x)])
            if len(mp):
                above = int((mp > VALID_HI).sum())
                print(f"  inverted manifold pressure: {np.percentile(mp,5):.0f}"
                      f" - {np.percentile(mp,95):.0f} kPa (p5-p95), max {mp.max():.0f}")
                print(f"  rows above the validated {VALID_HI:.0f} kPa: {above}")
                if above > 200:
                    verdict.append(("HELPS", f"{above} rows above 74 kPa -- could "
                                             "extend the validated span IF steady"))
                else:
                    verdict.append(("no", "adds nothing above the validated span"))
            else:
                print("  could not invert")
    except Exception as e:
        print(f"  (skipped: {type(e).__name__}: {e})")

    # ---- 4. steadiness, which decides whether any of it becomes a point -----
    print("\n" + "-" * 74)
    print("  4. IS IT STEADY?  (AUDIT.md M3 -- decides if rows become POINTS)")
    print("-" * 74)
    v = col(df, "Vehicle speed")
    ld = col(df, "Relative air filling")
    if v is not None and t is not None:
        # crude 60 s windows on wall clock
        good = 0
        i = 0
        tv = t.to_numpy()
        while i < len(tv):
            j = np.searchsorted(tv, tv[i] + 60.0)
            if j >= len(tv):
                break
            vs = v.iloc[i:j].to_numpy()
            if np.isfinite(vs).all() and np.ptp(vs) < 3.0 and vs.mean() > 5:
                if ld is not None:
                    ls = ld.iloc[i:j].to_numpy()
                    if np.isfinite(ls).all() and ls.mean() > 1e-6 \
                            and np.ptp(ls) / ls.mean() <= 0.25:
                        good += 1
                else:
                    good += 1
            i = j
        print(f"  60 s windows steady in speed AND load (<=25 % spread): {good}")
        if good == 0:
            print("  -> likely contributes ZERO operating points. That is a driving")
            print("     problem, not a code one (CLAUDE.md, new-drive routine).")

    # ---- the verdict --------------------------------------------------------
    print("\n" + "=" * 74)
    print("  VERDICT")
    print("=" * 74)
    helps = [w for w in verdict if w[0] == "HELPS"]
    for tag, why in verdict:
        mark = {"HELPS": " ++ ", "marginal": "  ~ ", "no": "  -  "}[tag]
        print(f"  {mark} {why}")
    print()
    if helps:
        print(f"  This drive HELPS on {len(helps)} of the four things the project")
        print("  still needs. Add it, then follow the routine in CLAUDE.md.")
    else:
        print("  This drive changes nothing the project is short of. Adding it is")
        print("  harmless -- more minutes in the manifest -- but do not expect a")
        print("  figure to move, and do not report it as new evidence.")
    print("""
  Whatever it does, remember what a new drive CANNOT fix: the standard scenario
  not binding the protection trigger (AUDIT.md C2) is a property of the
  SIMULATOR, not of the data. No log will restore the preview result.""")


if __name__ == "__main__":
    main()
