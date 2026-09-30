"""fit_envelope.py -- the compressor envelope the plant uses, printed from the data.

    python fit_envelope.py

WHAT IT PRINTS, SINCE 28 SEPTEMBER 2026. plant.boost_ceiling_kpa no longer
evaluates a fitted formula: it interpolates the measured envelope itself (the
binned p95, made monotone, capped at the highest stable pressure ratio), which
derive_params.py computes from data/master_samples.csv and stores in
data/derived_params.json. This script prints that envelope from the SAME code
(derive_params.envelope_bins), so the table here and the ceiling in the plant
cannot disagree.

WHY IT WAS REWRITTEN. AUDIT.md M5 found the envelope published in two versions
that no script produced; this file was written to fix that -- and then fitted
PR = 1 + A*flow**B, a different form from the PR = 1 + A*m/(1 + B*m) the plant
shipped, so it could never regenerate the plant's constants either. One code
path now does both jobs.

READ THE READINGS COLUMN, NOT THE ROWS (AUDIT.md H4). Rows are forward-filled;
readings are genuine polls. The top bins rest on a handful.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import derive_params as D          # noqa: E402


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    S = pd.read_csv(os.path.join(here, "data", "master_samples.csv"), low_memory=False)
    bins, pr_max = D.envelope_bins(S)
    if not bins:
        print("no bins survived the filters")
        raise SystemExit(2)
    m = np.array([b[0] for b in bins])
    pr = np.array([b[1] for b in bins])
    env = np.maximum.accumulate(pr)
    a, b, rms = D.fit_ceiling(m, pr)

    print(f"Compressor envelope: p{D.PCTL:.0f} pressure ratio per {D.BIN_KGS:.2f} kg/s corrected-flow bin")
    print(f"stable, not MAF-pinned, bins with >= {D.MIN_ROWS} rows\n")
    print(f"{'flow kg/s':>10}{'PR p95':>9}{'ceiling':>9}{'rows':>8}{'readings':>10}")
    print("-" * 46)
    for (c, p, n, fresh), e in zip(bins, env):
        print(f"{c:>10.3f}{p:>9.3f}{e:>9.3f}{n:>8d}{fresh:>10d}")
    print("-" * 46)
    print(f"cap (highest stable pressure ratio in the logs): {pr_max:.3f}")
    print(f"the ceiling interpolates the 'ceiling' column; RMS against the bins "
          f"{np.sqrt(np.mean((pr - env) ** 2)):.3f}")
    print(f"for comparison, PR = 1 + A m/(1 + B m) at A {a:.3f}, B {b:.3f} would leave RMS {rms:.3f}")
    if "t_amb_assumed" in S and (S.t_amb_assumed == 1).any():
        print("\nrows from a drive with no ambient channel use build_dataset.AMB_FALLBACK_C for"
              "\ncorrected flow; derive_params.py records the ceiling re-derived at the coolest"
              "\nand hottest ambient ever logged (boost_ceiling.sensitivity_to_assumed_ambient).")


if __name__ == "__main__":
    main()
