"""verify_docs.py — checks that the numbers in the documents are still true.

    python verify_docs.py

WHY THIS EXISTS
---------------
On 8 September a cross-check found five figures in the documents that the data
no longer supported. Four of them had the same cause: a number computed on ONE
drive and then quoted as if it were pooled over all of them. The hottest logged
oil was written as 95 C (true of `cb67b01f`, but 103 C across the set); the
hardest sustained load as 5.1 g/s (true of `cb67b01f`, 6.5 g/s across the set);
the oil-coolant gap as -1.4 K (-1.2 K pooled); and two correlations quoted from
a 230 kPa subset next to a table built on a 200 kPa one.

None of those changed a conclusion. All of them would have been quoted in a
thesis and defended in a viva.

CLAUDE.md's mistake 4 already says "one drive is not evidence". That lesson was
learned in the CODE and then broken in the DOCUMENTS. This file closes that gap:
every figure below is recomputed from the shipped data and compared with what
the documents claim.

Run it after `build_dataset.py`, and before quoting anything.

Exit code is 1 if any check fails, so it can go in CI.
"""
import os
import re
import sys
import glob

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RESULTS = []


def chk(label, got, claim, tol=0.0, unit=""):
    good = abs(got - claim) <= tol if isinstance(claim, (int, float)) else got == claim
    RESULTS.append(good)
    mark = "ok  " if good else "WRONG"
    print(f"  {mark}  {label:50s} data {got!r:>10}   docs {claim!r}{unit}")


def dwell_column(S):
    """Seconds of unbroken running above 200 kPa, per drive."""
    out = []
    for _, d in S.groupby("source"):
        d = d.sort_values("t").reset_index(drop=True)
        acc, run = 0.0, np.zeros(len(d))
        for i, v in enumerate((d.map_kpa > 200).fillna(False)):
            acc = acc + 1 if v else 0
            run[i] = acc
        d["dwell"] = run / 4.6
        out.append(d)
    return pd.concat(out)


# ---------------------------------------------------------------------------
# RETIRED FIGURES
# ---------------------------------------------------------------------------
# Everything above asks "is this number still true?". That is not enough, and
# mistake 11 is the proof: every figure above passed while SIX stale figures
# sat in CLAUDE.md and README.md, because a checker only ever looks at the
# numbers it was handed. Nothing was watching for the OLD value still being
# quoted somewhere else.
#
# So: each entry is a value this project has retired, the value that replaced
# it, and a regex that matches the retired one as it was actually written. If
# any of them reappears in a tracked document, this file fails.
#
# When you retire a figure, ADD IT HERE. That is the whole maintenance cost,
# and it is what stops the next person quoting a superseded number in a viva.
RETIRED = [
    # (pattern, what it was, what replaced it)
    (r"\b118 seconds?\b", "118 s above 230 kPa (7 drives)", "198 s"),
    (r"\+0\.02\s*[—-]\s*none at all", "corr(lambda, MAP) = +0.02", "-0.05"),
    (r"[-−]0\.60\)?,\s*air mass flow \([-−]0\.52",
     "enrichment correlations from 7 drives", "-0.56 / -0.49 / -0.47"),
    (r"\bn=29\b", "3500-4500 rpm cell at 29 samples", "n=47"),
    (r"seven drives, 113 minutes, five carrying",
     "dataset size before 7475b5d7", "eight drives, 168.1 minutes, six carrying"),
    (r"\b527\.2 · 356\.8 · 198\.7\b", "premise figures from the 4-cylinder",
     "829.2 / 548.6 / 437.6 / 548.6"),
    (r"\b39\.5 s\b", "turbine tau from the 4-cylinder", "48.0 s"),
    (r"n_cyl\s*=\s*4\b", "the 2.0 L inline-four geometry", "n_cyl = 6 (B58)"),
]

# Files whose whole job is to record what changed, so they are expected to
# contain retired values throughout. Exempting them is deliberate.
RETIRED_EXEMPT = {"DOCUMENT_STATUS.md", "CHANGELOG.md",
                  "DRIVE_1_card_v1.md", "DRIVE_1_card_v2.md"}

# A line that names a retired figure ON PURPOSE -- "the old 39.5 s figure is
# void", the mistake log's was/should-say tables -- carries this marker. It is
# deliberately explicit: an automatic rule ("skip table rows", "skip lines
# containing 'old'") would eventually skip a line that IS a live claim, and the
# whole point of this check is that nothing gets skipped by accident. If you
# add the marker, you are asserting the line is a historical record.
RETIRED_OK = "RETIRED-OK"


def check_retired(here):
    """Fail if any document still quotes a figure this project has retired."""
    print("\nRETIRED FIGURES  (mistake 11 -- the old value must not survive)")
    docs = [p for p in glob.glob(os.path.join(here, "**", "*.md"), recursive=True)
            if os.path.basename(p) not in RETIRED_EXEMPT]
    docs += [p for p in glob.glob(os.path.join(here, "*.py"))
             if os.path.basename(p) != os.path.basename(__file__)]

    found, n_marked = [], 0
    for path in sorted(docs):
        with open(path, encoding="utf-8") as fh:
            block = fh.read().splitlines()
        is_md = path.endswith(".md")
        for n, line in enumerate(block, 1):
            # The marker may sit on the line itself or open the block it
            # belongs to, so a wrapped aside does not need it on every line.
            # In markdown that block is the whole section back to the last
            # heading, which lets one marker cover a mistake-log entry that
            # quotes its own retired figures throughout. In Python it is the
            # preceding few lines, because there are no sections to anchor to.
            if is_md:
                start = 0
                for j in range(n - 1, -1, -1):
                    if block[j].startswith("#"):
                        start = j
                        break
            else:
                start = max(0, n - 6)
            para = "\n".join(block[start:n])
            for pat, was, now in RETIRED:
                if re.search(pat, line):
                    if RETIRED_OK in para:
                        n_marked += 1
                    else:
                        found.append((os.path.relpath(path, here), n, was, now))

    for rel, n, was, now in found:
        print(f"  WRONG  {rel}:{n}  still quotes {was}  -> should be {now}")
    RESULTS.append(not found)
    if not found:
        print(f"  ok     none of the {len(RETIRED)} retired figures appear as a "
              f"live claim in {len(docs)} tracked files")
        print(f"         ({n_marked} historical mentions marked {RETIRED_OK})")


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    S = pd.read_csv(os.path.join(here, "data/master_samples.csv"))
    M = pd.read_csv(os.path.join(here, "data/manifest.csv"))
    P = pd.read_csv(os.path.join(here, "data/master_points.csv"))

    print("\nDATASET SIZE  (CLAUDE.md, validation_table.md B)")
    chk("total minutes", round(float(M.duration_min.sum()), 1), 168.1, 0.15, " min")
    chk("drives in the manifest", len(M), 8)
    chk("drives that carry samples", S.source.nunique(), 6)
    chk("distinct operating points", len(P), 22)
    chk("every point spans a real 60 s window",
        bool((P.t_span.between(48, 72)).all()), True)
    chk("no point straddles a logger gap", round(float(P.max_gap.max()), 2), 0.45, 0.02, " s")

    print("\nMAF SATURATION  (CLAUDE.md mistake 7)")
    chk("samples pinned at the 1020 kg/h ceiling", int(S.maf_pinned.sum()), 517)
    hits = sum(
        1
        for f in sorted(glob.glob(os.path.join(here, "logs/raw/*.csv")))
        if (pd.to_numeric(pd.read_csv(f).get("Air mass flow"), errors="coerce")
            >= 1019.9).any()
    )
    chk("drives showing that exact ceiling", hits, 5)

    print("\nCOMPRESSOR ENVELOPE  (validation_table.md D)")
    st = S[S.stable == 1]
    chk("quasi-steady samples behind the fit", len(st), 43853)
    f = st[np.isfinite(st.corr_flow) & np.isfinite(st.press_ratio)
           & (st.corr_flow > 0.01) & st.press_ratio.between(0.8, 3.0)]
    chk("highest pressure ratio observed", round(float(f.press_ratio.max()), 2),
        2.52, 0.005)

    print("\nENRICHMENT v4  (engine_env.BaselineECU.base_lambda)")
    S2 = dwell_column(S)
    h = S2[(S2.map_kpa > 200) & S2.lam.between(0.5, 1.3)]
    for lo, hi, claim in ((1000, 3500, 422), (3500, 4500, 168), (4500, 7000, 465)):
        chk(f"samples, {lo}-{hi} rpm above 200 kPa",
            int(((h.rpm > lo) & (h.rpm <= hi)).sum()), claim)
    hh = S2[(S2.map_kpa > 230) & S2.lam.between(0.5, 1.3)]
    chk("seconds above 230 kPa", round(len(hh) / 4.6), 198, 1, " s")
    v = h[["lam", "rpm", "air_gps", "dwell", "map_kpa"]].dropna()
    # The docstring quotes the >200 kPa subset, matching ENR_LOAD. Keep it that way.
    for col, claim in (("rpm", -0.56), ("air_gps", -0.49),
                       ("dwell", -0.47), ("map_kpa", -0.05)):
        chk(f"corr(lambda, {col})",
            round(float(np.corrcoef(v[col], v.lam)[0, 1]), 2), claim, 0.02)

    print("\nTHERMAL CALIBRATION  (thermal.py, validation_table.md C)")
    FIT = ["cb67b01f-20260908_084142.csv", "3aca2ec1-20260907_072817.csv",
           "683640a0-20260907_070212.csv"]
    g = (S[S.source.isin(FIT)].oil_c - S[S.source.isin(FIT)].ect_c).dropna()
    chk("oil-coolant median gap, fitted drives",
        round(float(g.median()), 1), -1.2, 0.06, " K")
    chk("oil-coolant p95 gap, fitted drives",
        round(float(g.quantile(0.95)), 1), 5.4, 0.06, " K")
    chk("hottest oil anywhere in the logs",
        round(float(S.oil_c.max())), 107, 0.5, " C")

    # Window sized from EACH drive's own rate. A fixed sample count gives a
    # 41 s window on the 6.63 Hz drives and a 74 s window on the 3.52 Hz one,
    # which is how 6.5 g/s was first mis-read as 9.2.
    rates = dict(zip(M.file, M.rate_hz))
    worst = 0.0
    for src, d in S.groupby("source"):
        w = max(5, int(round(60 * rates.get(src, 4.6))))
        d = d.sort_values("t")
        fu = (d.air_gps / (14.7 * d.lam)).replace([np.inf, -np.inf], np.nan)
        m = fu.rolling(w, min_periods=int(0.8 * w)).mean().max()
        if np.isfinite(m):
            worst = max(worst, float(m))
    chk("hardest sustained 60 s fuel flow", round(worst, 1), 8.7, 0.06, " g/s")

    print("\nLOAD NORMALISATION  (compare_log.py, validation_table.md)")
    # k is a ratio of air densities, so it is DERIVED, not fitted. The three
    # numbers below are the whole argument: the DIN constant is defined, the
    # derived k matches the fitted one, and the 20 C alternative does not.
    din = 100.0 * 273.15 / 101.3
    chk("DIN reference constant, 100*273.15/101.3", round(din, 1), 269.6, 0.05, " K")
    t_in = P["iat_pre"] + 273.15
    chk("derived k = 269.6 / T_intake, mean over the 22 points",
        round(float(np.mean(din / t_in)), 3), 0.783, 0.002)
    chk("the 20 C reference the fit excludes",
        round(float((100.0 * 293.15 / 101.3) / np.mean(t_in)), 3), 0.840, 0.002)

    check_retired(here)

    bad = RESULTS.count(False)
    print("\n" + "=" * 72)
    if bad:
        print(f"{bad} of {len(RESULTS)} figures no longer match the documents.")
        print("Fix the DOCUMENT, not this file, unless the data genuinely changed.")
        raise SystemExit(1)
    print(f"All {len(RESULTS)} figures match the documents.")


if __name__ == "__main__":
    main()
