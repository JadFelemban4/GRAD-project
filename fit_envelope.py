"""fit_envelope.py — the compressor envelope, regenerated from the shipped data.

    python fit_envelope.py

WHY THIS FILE EXISTS
--------------------
AUDIT.md M5 and M6. The compressor envelope is published in two places that
disagree with each other, and **no script in the repository produced either**:

    plant.py                 RMS 0.129, top bins 0.280 -> 2.515, 0.301 -> 2.333
    validation_table.md §D   RMS 0.135, top bins 0.289 -> 2.515, 0.303 -> 2.395

and the measured top of range is quoted as both 0.303 and 0.314 kg/s in
different sections of the same document. A figure that no script prints is a
figure nobody can check, which is the rule CLAUDE.md states and this table broke.

This prints the table from `data/master_samples.csv` with the method the
documents describe, so the numbers can be regenerated rather than trusted.

WHAT THE METHOD IS, STATED RATHER THAN IMPLIED
----------------------------------------------
  * rows flagged `stable` and not `maf_pinned` -- the MAF ceiling at 1020 kg/h
    would drag the top bins down (mistake 7);
  * corrected mass flow binned at 0.03 kg/s;
  * the 95th percentile of pressure ratio in each bin, not the maximum, so one
    decode glitch cannot define the envelope;
  * bins with fewer than 15 rows dropped.

READ THE BIN COUNTS. They are counts of FORWARD-FILLED ROWS, and per AUDIT.md
H4 the independent readings behind them are 15-30x fewer. A bin of 300 rows may
rest on ten genuine measurements.
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BIN_KGS = 0.03
MIN_ROWS = 15
PCTL = 95.0


def fit_ab(flow, pr):
    """Least-squares fit of PR = 1 + A * flow**B, without scipy.

    scipy is not a dependency of this project -- AUDIT.md M7 found it listed in
    requirements.txt and imported nowhere, and it has since been removed. Taking
    logs makes the model linear, which numpy can solve directly:

        log(PR - 1) = log A + B * log(flow)

    The RMS reported is on the ORIGINAL scale, not the log scale, so it is
    comparable with the 0.129 and 0.135 the two published versions quote.
    """
    y = pr - 1.0
    ok = (y > 0) & (flow > 0)
    if ok.sum() < 2:
        return float("nan"), float("nan"), float("nan")
    coef = np.polyfit(np.log(flow[ok]), np.log(y[ok]), 1)
    B, A = float(coef[0]), float(np.exp(coef[1]))
    resid = pr - (1.0 + A * flow ** B)
    return A, B, float(np.sqrt(np.mean(resid ** 2)))


def envelope(S: pd.DataFrame):
    """(bin centre, p95 pressure ratio, rows, independent readings) per bin."""
    use = S[(S.get("stable", 0) == 1) & (S.get("maf_pinned", 0) == 0)]
    use = use[np.isfinite(use.corr_flow) & np.isfinite(use.press_ratio)
              & (use.corr_flow > 0.01)]
    out = []
    edges = np.arange(0.0, use.corr_flow.max() + BIN_KGS, BIN_KGS)
    for lo in edges:
        b = use[(use.corr_flow >= lo) & (use.corr_flow < lo + BIN_KGS)]
        if len(b) < MIN_ROWS:
            continue
        fresh = 0
        for _, d in b.groupby("source"):
            v = d.sort_values("t").corr_flow
            fresh += int((v.diff().fillna(1.0) != 0).sum())
        out.append((lo + BIN_KGS / 2.0, float(np.percentile(b.press_ratio, PCTL)),
                    len(b), fresh))
    return out


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    S = pd.read_csv(os.path.join(here, "data", "master_samples.csv"))
    rows = envelope(S)
    if not rows:
        print("no bins survived the filters")
        raise SystemExit(2)

    print(f"Compressor envelope, {PCTL:.0f}th percentile pressure ratio per "
          f"{BIN_KGS:.2f} kg/s bin")
    print(f"stable & not MAF-pinned, bins with >= {MIN_ROWS} rows\n")
    print(f"{'flow kg/s':>10}{'PR p95':>9}{'rows':>8}{'readings':>10}")
    print("-" * 37)
    for c, pr, n, fresh in rows:
        print(f"{c:>10.3f}{pr:>9.3f}{n:>8d}{fresh:>10d}")
    print("-" * 37)

    flow = np.array([r[0] for r in rows])
    pr = np.array([r[1] for r in rows])
    A, B, rms = fit_ab(flow, pr)
    print(f"\nPR = 1 + A * flow**B     A = {A:.4f}   B = {B:.4f}   RMS = {rms:.4f}")
    print(f"highest bin: {flow[-1]:.3f} kg/s at PR {pr[-1]:.3f}")
    print(f"highest stable corrected flow anywhere: "
          f"{S[(S.get('stable', 0) == 1)].corr_flow.max():.3f} kg/s")
    print("""
Quote the bin table with its READINGS column, not just its rows (AUDIT.md H4),
and quote the highest-flow figure with the filter that produced it -- "0.303"
and "0.314" in the documents are the same quantity under two different filters.""")


if __name__ == "__main__":
    main()
