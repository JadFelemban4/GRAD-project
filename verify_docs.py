"""verify_docs.py — checks that the numbers in the documents are still true.

    python verify_docs.py

WHY THIS EXISTS
---------------
On 8 September a cross-check found five figures in the documents that the data
no longer supported. Four of them had the same cause: a number computed on ONE
drive and then quoted as if it were pooled over all of them.

CLAUDE.md's mistake 4 already says "one drive is not evidence". That lesson was
learned in the CODE and then broken in the DOCUMENTS.

WHAT CHANGED ON 11 SEPTEMBER, AND WHY IT MATTERS MORE THAN ANY FIGURE BELOW
---------------------------------------------------------------------------
Until today this file had a hole big enough to drive the entire v17 document
set through. Every check looked like this:

    chk("samples pinned at the ceiling", int(S.maf_pinned.sum()), 517)

It compared THE DATA to a constant typed into THIS FILE. It never opened
validation_table.md. So validation_table.md could say "192 samples" while the
data said 517, and this script printed `ok` and exited 0. That is exactly what
happened: on 11 September a review found 55 figures wrong across the shipped
documents while this file reported 26 of 27 green.

A checker that cannot see the documents it is named after is not a checker.

So every figure now carries THREE things instead of one:

    1. a value computed from the shipped data          (as before)
    2. the value the author expects                    (as before -- catches
                                                        data drift)
    3. a set of regexes and the files that must agree  (NEW -- catches a
                                                        document that has
                                                        drifted away from the
                                                        data)

`figure()` runs all three off ONE computed number, so there is no way to update
the data check and forget the documents. If a document states a different value,
this fails and NAMES THE FILE AND LINE.

The other half of the same lesson is the RETIRED list. It is pattern-based, and
on 11 September it missed "seven drives and 113.0 minutes" because the pattern
had been written for "seven drives, 113 minutes, five carrying" -- the same
false claim, one comma away, silent pass. Patterns here are now written as
loosely as they can be without false positives, and a pattern that matches
NOTHING anywhere is reported as a warning, so a rotted pattern cannot sit
silently forever.

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

from plant import charge_temperature  # noqa: E402

RESULTS = []
DOC_FAILURES = []
DOC_UNMATCHED = []
DOC_HITS = 0
HERE = os.path.dirname(os.path.abspath(__file__))

# Documents whose numbers must agree with the data. These are the files a
# reader or an examiner actually meets. Code files are included because their
# docstrings publish figures too -- base_lambda()'s table and
# charge_temperature()'s evidence table are both cited in the thesis.
TRACKED_DOCS = [
    "CLAUDE.md",
    "README.md",
    "validation_table.md",
    "CHECKPOINT.md",
    "handoff.md",
    "logs/CHANNEL_SET_FINAL.md",
    "plant.py",
    "engine_env.py",
    "compare_log.py",
    "build_dataset.py",
]

# A number as documents actually write it: "517", "43 853", "30 534", "1.4",
# "-0.56", "+0.23". Thousands may be separated by a space or a non-breaking
# space, which is how the markdown in this repo is written.
NUM = r"([-−+]?\d[\d   ,]*(?:\.\d+)?)"

# Documents write small counts as words -- "eight drives", "six carrying
# samples", "seventeen pooled points". A scanner that only understands digits
# would skip exactly the sentences that went wrong, so spell them out.
WORDS = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6,
    "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
    "thirteen": 13, "fourteen": 14, "fifteen": 15, "sixteen": 16,
    "seventeen": 17, "eighteen": 18, "nineteen": 19, "twenty": 20,
    "twenty-two": 22,
}
WORDNUM = (r"([-−+]?\d[\d   ,]*(?:\.\d+)?|"
           + "|".join(sorted(WORDS, key=len, reverse=True)) + r")")


def as_number(txt):
    """Parse a number as a document writes it -- digits or an English word."""
    t = txt.strip().lower()
    if t in WORDS:
        return float(WORDS[t])
    t = t.replace("−", "-").replace(" ", "").replace(" ", "")
    t = t.replace(",", "").replace(" ", "")
    try:
        return float(t)
    except ValueError:
        return None


def chk(label, got, claim, tol=0.0, unit=""):
    """Compare a value computed from the data with what the author expects."""
    good = abs(got - claim) <= tol if isinstance(claim, (int, float)) else got == claim
    RESULTS.append(good)
    mark = "ok  " if good else "WRONG"
    print(f"  {mark}  {label:50s} data {got!r:>10}   docs {claim!r}{unit}")


def _historical_lines(block, is_md):
    """1-based line numbers a RETIRED-OK marker legitimately covers.

    WHY THIS IS NARROW, AND WHY IT DID NOT USED TO BE
    -------------------------------------------------
    The first version of this rule ran BACKWARD from the line under test to the
    last heading: if a RETIRED-OK appeared anywhere above it in the same
    section, the line was exempt. That meant one marker near the top of a long
    section silently switched the checker off for everything below it. Measured
    on 11 September, it exempted **17 % of the tracked prose and 36 % of
    CLAUDE.md** -- a third of the most important file in the repo was not being
    checked, by a mechanism nobody could see.

    That is the same failure this whole file exists to prevent, one more level
    down: a check that quietly does not run still prints green.

    So a marker now covers a BOUNDED scope, and a whole-section exemption has to
    be asked for explicitly:

        <!-- RETIRED-OK -->            covers from the marker to the end of its
                                       own paragraph (the next blank line).
        <!-- RETIRED-OK: section -->   covers to the end of the section. Use it
                                       for a mistake-log entry that quotes its
                                       own superseded figures throughout.

    In Python the paragraph form covers the marker's line and the eight after
    it, which is the length of a comment block in this repo.
    """
    covered = set()
    for i, line in enumerate(block):
        if RETIRED_OK not in line:
            continue
        after = line.split(RETIRED_OK, 1)[1][:24].lower()
        whole_section = "section" in after
        j = i
        if whole_section and is_md:
            j = i + 1
            while j < len(block) and not block[j].startswith("#"):
                j += 1
            j -= 1
        elif is_md:
            j = i + 1
            while j < len(block) and block[j].strip() != "":
                j += 1
            j -= 1
        else:
            j = min(len(block) - 1, i + 8)
        for k in range(i, j + 1):
            covered.add(k + 1)
    return covered


def _paragraph_is_historical(block, n, is_md):
    """True if line n sits inside a passage marked as a historical record.

    Recomputed per call rather than cached: caching on id(block) looked cheap
    and is wrong, because CPython reuses an id once the old list is collected,
    so one file's exemptions could silently answer for another's.
    """
    return n in _historical_lines(block, is_md)


def scan_documents(label, value, patterns, files, tol):
    """Fail if any named document states a DIFFERENT value for this figure.

    `value` is the number computed from the shipped data -- the same one the
    data check used. Documents are compared against the DATA, never against a
    constant in this file, which is the whole point of the rework.
    """
    global DOC_HITS
    hits = 0
    for rel in files:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            continue
        with open(path, encoding="utf-8") as fh:
            block = fh.read().splitlines()
        is_md = path.endswith(".md")
        for n, line in enumerate(block, 1):
            # Documents wrap. The MAF sentence that went wrong -- "1020.0
            # kg/h, the same number on four separate drives, 192 samples" --
            # is ONE claim spread over two lines, and a line-at-a-time scanner
            # reads neither half as a figure.
            #
            # But join ALWAYS and you break every pattern anchored to the end of
            # a line: a table row joined to the row below it ends in the NEXT
            # row's number. So try the line on its own first, and fall back to
            # the joined window only when the line alone says nothing.
            nxt = block[n] if n < len(block) else ""
            window = line + " " + nxt.strip()
            for pat in patterns:
                found = list(re.finditer(pat, line))
                used_window = False
                if not found:
                    found = list(re.finditer(pat, window))
                    used_window = True
                for m in found:
                    got = as_number(m.group(1))
                    if got is None:
                        continue
                    hits += 1
                    DOC_HITS += 1
                    # Report the line the NUMBER is written on. When the match
                    # came from the joined window and the capture starts past
                    # the end of the first line, the figure is on the second.
                    lineno = n + 1 if (used_window and m.start(1) >= len(line)) else n
                    src = block[lineno - 1] if lineno <= len(block) else line
                    if abs(got - value) > tol:
                        if _paragraph_is_historical(block, lineno, is_md):
                            continue
                        # A wrapped claim is still seen twice, once from each of
                        # its lines. Report it once.
                        if any(r[0] == rel and r[2] == label and r[3] == got
                               and abs(r[1] - lineno) <= 1 for r in DOC_FAILURES):
                            continue
                        DOC_FAILURES.append(
                            (rel, lineno, label, got, value, src.strip()[:100]))
    if hits == 0:
        DOC_UNMATCHED.append(label)
    return hits


def figure(label, value, expect, tol=0.0, unit="", patterns=(), files=(), dtol=None):
    """One figure, checked three ways off ONE computed number.

        1. the data against what the author expects   (catches data drift)
        2. every tracked document against the DATA    (catches document drift)
        3. a pattern that matches nothing is reported (catches a rotted regex)

    `dtol` is the tolerance for the document comparison, which is usually
    looser than the data tolerance because documents round.
    """
    chk(label, value, expect, tol, unit)
    if patterns:
        scan_documents(label, value, list(patterns), list(files),
                       tol if dtol is None else dtol)


def dwell_column(S, thr=180.0):
    """Seconds of unbroken running above ENR_LOAD, per drive.

    The threshold was 200 kPa until 10 September. It moved with the manifold
    pressure DEFINITION, not with the physics: 180 kPa on the corrected charge
    temperature selects the same 1055 samples that 200 kPa selected on the old
    compressor-outlet scale. See engine_env.ENR_LOAD.
    """
    out = []
    for _, d in S.groupby("source"):
        d = d.sort_values("t").reset_index(drop=True)
        acc, run = 0.0, np.zeros(len(d))
        for i, v in enumerate((d.map_kpa > thr).fillna(False)):
            acc = acc + 1 if v else 0
            run[i] = acc
        d["dwell"] = run / 4.6
        out.append(d)
    return pd.concat(out)


# ---------------------------------------------------------------------------
# RETIRED FIGURES
# ---------------------------------------------------------------------------
# A figure this project has superseded, and a pattern matching it AS WRITTEN.
#
# WRITE THE LOOSEST PATTERN THAT DOES NOT FALSE-POSITIVE. On 11 September the
# entry for the seven-drive dataset size was written as
#
#     r"seven drives, 113 minutes, five carrying"
#
# and validation_table.md said "seven drives and 113.0 minutes". Same false
# claim, different commas, silent pass, and it shipped. Match the FACT, not the
# sentence someone happened to write it in.
RETIRED = [
    # --- dataset size, before the eighth drive -----------------------------
    (r"seven drives|drives,\s*113|\b113(?:\.0)?\s*min",
     "dataset size before 7475b5d7", "eight drives, 168.1 minutes, six carrying"),
    (r"five carry|five carrying", "drives carrying samples, before 7475b5d7", "six"),
    (r"seventeen pooled|\b17 pooled", "the 17-point dataset", "22 pooled points"),
    # --- enrichment, before the eighth drive and before the temp correction --
    (r"\b118 seconds?\b|\b198 seconds?\b", "seconds above the dwell threshold",
     "178 s above 207 kPa"),
    (r"\b230 kPa\b(?![^\n]*RETIRED)", "230 kPa as the dwell threshold", "207 kPa"),
    (r"corr\([^)]{0,24}\)\s*[-−+]0\.0[25]|\+0\.02\s*[—-]\s*none at all",
     "corr(lambda, MAP) = +0.02 or -0.05", "+0.23"),
    (r"[-−]0\.60|[-−]0\.52|[-−]0\.38",
     "enrichment correlations from 7 drives", "-0.56 / -0.49 / -0.47"),
    (r"\bn\s*=\s*29\b", "3500-4500 rpm cell at 29 samples", "n=47"),
    # --- the charge-temperature correction, 10 September --------------------
    (r"31\.4\s*[-–]\s*81\.6|31\s*[-–]\s*82 kPa|31\s*[-–]\s*79 kPa",
     "the point span with the sensor as charge temp", "30-74 kPa"),
    (r"\b0\.783\b|\b0\.784\b", "k derived/fitted on the sensor temperature",
     "derived 0.829, fitted 0.837"),
    (r"\b0\.840\b", "the 20 C reference on the sensor temperature", "0.890"),
    (r"2\.8\s*%|2\.3\s*%", "load residual before the correction",
     "1.4 % derived, 1.1 % fitted"),
    (r"volumetric_efficiency\(\)[^.]{0,80}(?:understat|over-predict|fitted at part load)",
     "the boost gap blamed on the breathing model", "it was the charge temperature"),
    (r"agree inside the 4\.4", "a sub-80 kPa agreement no script prints",
     "both pressure channels are pre-throttle; there is no such agreement"),
    # --- MAF saturation, before the eighth drive ----------------------------
    (r"\b192 samples\b|four separate\s+drives", "MAF ceiling before 7475b5d7",
     "517 samples on five drives"),
    (r"\b1\.163\b", "combustion/MAF ratio before 7475b5d7", "1.095"),
    (r"30[\s ]*534", "quasi-steady samples before 7475b5d7", "43 853"),
    # --- thermal ------------------------------------------------------------
    (r"\b6\.5 g/s\b", "hardest sustained fuel flow before 7475b5d7", "8.7 g/s"),
    (r"above 103\s*°?C|\b103 °C\b", "hottest logged oil before 7475b5d7",
     "107 C"),
    (r"\b39\.5 s\b", "turbine tau from the 4-cylinder", "48.0 s"),
    # --- results ------------------------------------------------------------
    (r"33\.9\s*%", "reactive damage reduction, unsupported by the printed column",
     "33.8 %"),
    (r"\b527\.2 . 356\.8 . 198\.7\b", "premise figures from the 4-cylinder",
     "829.2 / 548.6 / 437.6 / 548.6"),
    (r"reports 0\.8\s*%", "the fitted residual on a four-cylinder", "1.1 %"),
    (r"26 of 26", "the verify_docs check count before the document scan",
     "run it and read the printed total"),
    (r"n_cyl\s*=\s*4\b", "the 2.0 L inline-four geometry", "n_cyl = 6 (B58)"),
]

# Files whose whole job is to record what changed, so they are expected to
# contain retired values throughout. Exempting them is deliberate.
RETIRED_EXEMPT = {"DOCUMENT_STATUS.md", "CHANGELOG.md",
                  "DRIVE_1_card_v1.md", "DRIVE_1_card_v2.md"}

# A line that names a retired figure ON PURPOSE -- "the old 39.5 s figure is
# void", the mistake log's was/should-say tables -- carries this marker. It is
# deliberately explicit: an automatic rule would eventually skip a line that IS
# a live claim, and the point of this check is that nothing gets skipped by
# accident. If you add the marker, you are asserting the line is history.
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
            for pat, was, now in RETIRED:
                if re.search(pat, line):
                    if _paragraph_is_historical(block, n, is_md):
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


def report_documents():
    """Print the result of the document scan -- the 11 September rework."""
    print("\nDOCUMENTS vs DATA  (every figure above, as the documents state it)")
    for rel, n, label, got, want, line in DOC_FAILURES:
        print(f"  WRONG  {rel}:{n}")
        print(f"         says {got!r} for '{label}', data gives {want!r}")
        print(f"         | {line}")
    RESULTS.append(not DOC_FAILURES)
    if not DOC_FAILURES:
        print(f"  ok     {DOC_HITS} figure mentions across {len(TRACKED_DOCS)} "
              f"tracked files all agree with the data")
    if DOC_UNMATCHED:
        print(f"  note   {len(DOC_UNMATCHED)} pattern(s) matched nothing anywhere "
              f"-- check the regex has not rotted:")
        for lab in DOC_UNMATCHED:
            print(f"           - {lab}")


# Which files must agree about what. Kept as short names so the check table
# below reads as a specification rather than as path handling.
MD = ["CLAUDE.md", "README.md", "validation_table.md"]
MD_CH = MD + ["logs/CHANNEL_SET_FINAL.md"]
ALL = TRACKED_DOCS
ENV = ["engine_env.py"]


def main():
    here = HERE
    S = pd.read_csv(os.path.join(here, "data/master_samples.csv"))
    M = pd.read_csv(os.path.join(here, "data/manifest.csv"))
    P = pd.read_csv(os.path.join(here, "data/master_points.csv"))

    print("\nDATASET SIZE  (CLAUDE.md, validation_table.md B)")
    figure("total minutes", round(float(M.duration_min.sum()), 1), 168.1, 0.15,
           " min",
           # Anchored to a DATASET-SCALE drive count. validation_table.md says
           # "three drives (80 minutes)" about the thermal fit, which is a
           # different quantity; a looser pattern reports it as a wrong total.
           patterns=[NUM + r"\s*min(?:ute)?s?\b[^.\n]{0,30}?"
                     r"(?:pooled|dataset|manifest|\b(?:6|7|8|six|seven|eight)\b\s*drives)",
                     r"\b(?:6|7|8|six|seven|eight)\s+drives[^.\n]{0,30}?\b" + NUM
                     + r"\s*min(?:ute)?s?\b"],
           files=ALL, dtol=0.15)
    figure("drives in the manifest", len(M), 8, 0,
           patterns=[WORDNUM + r"\s+drives,?\s+(?:and\s+)?\d+(?:\.\d+)?\s*min",
                     r"\d+(?:\.\d+)?\s*min(?:ute)?s?\s+(?:over|across|pooled across)\s+"
                     + WORDNUM + r"\s+drives"],
           files=ALL)
    figure("drives that carry samples", S.source.nunique(), 6, 0,
           patterns=[WORDNUM + r"\s+carrying\b", WORDNUM + r"\s+(?:drives\s+)?carry\b"],
           files=ALL)
    figure("distinct operating points", len(P), 22, 0,
           patterns=[WORDNUM + r"\s+distinct operating points",
                     WORDNUM + r"\s+pooled points"],
           files=ALL)
    chk("every point spans a real 60 s window",
        bool((P.t_span.between(48, 72)).all()), True)
    chk("no point straddles a logger gap",
        round(float(P.max_gap.max()), 2), 0.45, 0.02, " s")
    figure("operating-point span, low end", round(float(P.map_kpa.min())), 30, 0.6,
           " kPa",
           # "validated/covers/sit at", NOT "spanning": engine_env's spark fit
           # legitimately spans 43-79 kPa over its own 11 points.
           patterns=[r"(?:validation|covers|sit at)[^.\n]{0,26}?\b" + NUM
                     + r"\s*[-\u2013]\s*\d+\s*kPa"],
           files=ALL, dtol=0.6)
    figure("operating-point span, high end", round(float(P.map_kpa.max())), 74, 0.6,
           " kPa",
           patterns=[r"(?:validation|covers|sit at)[^.\n]{0,26}?\b\d+"
                     r"\s*[-\u2013]\s*" + NUM + r"\s*kPa"],
           files=ALL, dtol=0.6)

    print("\nMAF SATURATION  (CLAUDE.md mistake 7)")
    figure("samples pinned at the 1020 kg/h ceiling", int(S.maf_pinned.sum()), 517, 0,
           patterns=[r"(?:1020(?:\.0)?\s*kg/h|ceiling|pinned)[^.\n]{0,70}?\b" + NUM
                     + r"\s+samples",
                     NUM + r"\s+samples[^.\n]{0,50}?(?:pinned|ceiling|1020)"],
           files=ALL)
    hits = sum(
        1
        for f in sorted(glob.glob(os.path.join(here, "logs/raw/*.csv")))
        if (pd.to_numeric(pd.read_csv(f).get("Air mass flow"), errors="coerce")
            >= 1019.9).any()
    )
    figure("drives showing that exact ceiling", hits, 5, 0,
           patterns=[WORDNUM + r"\s+separate\s+drives",
                     r"1020\s*kg/h on\s+" + WORDNUM + r"\s+drives"],
           files=ALL)

    print("\nCOMPRESSOR ENVELOPE  (validation_table.md D)")
    st = S[S.stable == 1]
    figure("quasi-steady samples behind the fit", len(st), 43853, 0,
           patterns=[NUM + r"\s+quasi-steady",
                     r"refitted[^.\n]{0,30}?on\s+" + NUM],
           files=ALL)
    f = st[np.isfinite(st.corr_flow) & np.isfinite(st.press_ratio)
           & (st.corr_flow > 0.01) & st.press_ratio.between(0.8, 3.0)]
    figure("highest pressure ratio observed", round(float(f.press_ratio.max()), 2),
           2.52, 0.005,
           patterns=[r"highest pressure ratio[^\n]{0,24}?" + NUM],
           files=ALL, dtol=0.005)

    print("\nENRICHMENT v4  (engine_env.BaselineECU.base_lambda)")
    S2 = dwell_column(S)
    h = S2[(S2.map_kpa > 180) & S2.lam.between(0.5, 1.3)]
    bands = ((1000, 3500, 422), (3500, 4500, 168), (4500, 7000, 465))
    for lo, hi, claim in bands:
        figure(f"samples, {lo}-{hi} rpm above 180 kPa",
               int(((h.rpm > lo) & (h.rpm <= hi)).sum()), claim, 0,
               # A TABLE ROW, anchored at line start. Prose that mentions an rpm
               # band and a lambda value is a different claim.
               patterns=[rf"^\s*\|?\s*{lo}\s*[-\u2013]\s*{hi}\b[^\n]*?\s" + NUM
                         + r"\s*\|?\s*$"],
               files=ALL)
    hh = S2[(S2.map_kpa > 207) & S2.lam.between(0.5, 1.3)]
    figure("seconds above 207 kPa", round(len(hh) / 4.6), 178, 1, " s",
           # Only the "took that to N seconds" claim. "fitted to 17 seconds" and
           # "spanned 42.8 to 73.7 seconds" are different quantities.
           patterns=[r"took that to\s*\*{0,2}" + NUM + r"\s*\*{0,2}\s*seconds",
                     NUM + r"\s*s(?:econds)?\b[^.\n]{0,30}?above 207"],
           files=ALL, dtol=1)
    v = h[["lam", "rpm", "air_gps", "dwell", "map_kpa"]].dropna()
    CORR = (("rpm", -0.56, [r"engine speed\)\s*" + NUM, r"speed\s*\(" + NUM + r"\)"]),
            ("air_gps", -0.49, [r"air mass flow\)\s*" + NUM,
                                r"air mass flow \(" + NUM + r"\)"]),
            ("dwell", -0.47, [r"dwell[^)\n]{0,32}\)\s*" + NUM,
                              r"dwell \(" + NUM + r"\)"]),
            ("map_kpa", +0.23, [r"MANIFOLD PRESSURE\)\s*" + NUM,
                                r"corr\(.{0,18}MAP.{0,6}\)\s*(?:is\s*)?" + NUM,
                                r"manifold\s+pressure is\s*\*{0,2}" + NUM]))
    for col, claim, pats in CORR:
        figure(f"corr(lambda, {col})",
               round(float(np.corrcoef(v[col], v.lam)[0, 1]), 2), claim, 0.02,
               patterns=pats, files=ALL, dtol=0.02)

    print("\nTHERMAL CALIBRATION  (thermal.py, validation_table.md C)")
    FIT = ["cb67b01f-20260908_084142.csv", "3aca2ec1-20260907_072817.csv",
           "683640a0-20260907_070212.csv"]
    g = (S[S.source.isin(FIT)].oil_c - S[S.source.isin(FIT)].ect_c).dropna()
    chk("oil-coolant median gap, fitted drives",
        round(float(g.median()), 1), -1.2, 0.06, " K")
    chk("oil-coolant p95 gap, fitted drives",
        round(float(g.quantile(0.95)), 1), 5.4, 0.06, " K")
    figure("hottest oil anywhere in the logs", round(float(S.oil_c.max())), 107, 0.5,
           " C",
           patterns=[r"[Oo]il above\s*\*{0,2}" + NUM
                     + r"[^\n]{0,44}?extrapolation",
                     r"hottest oil[^\n]{0,36}?" + NUM + r"\s*\u00b0?\s*C"],
           files=ALL, dtol=0.5)

    rates = dict(zip(M.file, M.rate_hz))
    worst = 0.0
    for src, d in S.groupby("source"):
        w = max(5, int(round(60 * rates.get(src, 4.6))))
        d = d.sort_values("t")
        fu = (d.air_gps / (14.7 * d.lam)).replace([np.inf, -np.inf], np.nan)
        m = fu.rolling(w, min_periods=int(0.8 * w)).mean().max()
        if np.isfinite(m):
            worst = max(worst, float(m))
    figure("hardest sustained 60 s fuel flow", round(worst, 1), 8.7, 0.06, " g/s",
           patterns=[r"(?:sustained|hardest|ceiling is)[^.\n]{0,44}?\*{0,2}" + NUM
                     + r"\s*\*{0,2}\s*g/s"],
           files=ALL, dtol=0.06)

    print("\nLOAD NORMALISATION  (compare_log.py, validation_table.md)")
    # k is a ratio of air densities, so it is DERIVED, not fitted. T here is the
    # MODELLED charge temperature from plant.charge_temperature -- not the
    # pre-throttle sensor, which is a compressor outlet (mistake 13).
    din = 100.0 * 273.15 / 101.3
    chk("DIN reference constant, 100*273.15/101.3", round(din, 1), 269.6, 0.05, " K")
    t_ch = charge_temperature(P["t_amb"].fillna(25.0) + 273.15,
                              P["ect"].fillna(90.0) + 273.15)
    figure("derived k = 269.6 / T_charge, mean over the 22 points",
           round(float(np.mean(din / t_ch)), 3), 0.829, 0.002,
           # k is always written as 0.8xx. Anchoring on the SHAPE keeps this off
           # "1.4 % load residual with k derived, 2.8 % with k fitted", where the
           # nearby numbers are residuals, not constants.
           patterns=[r"[Dd]erived[^\n]{0,26}?k[^\n]{0,14}?\b(0\.\d{3})\b",
                     r"k,?\s*derived[^\n]{0,22}?\b(0\.\d{3})\b"],
           files=ALL, dtol=0.002)
    figure("the 20 C reference the fit excludes",
           round(float((100.0 * 293.15 / 101.3) / np.mean(t_ch)), 3), 0.890, 0.002,
           # "the same arithmetic gives 0.890" -- anchored to the k value, not to
           # any digit that happens to follow the words "20 C".
           patterns=[r"20\s*\u00b0?\s*C[^\n]{0,60}?\b(0\.\d{3})\b"],
           files=ALL, dtol=0.002)

    print("\nCHARGE TEMPERATURE  (plant.charge_temperature -- the 10 Sep correction)")
    # THE number that justifies modelling the charge temperature instead of
    # reading the sensor. Guard it: if someone reverts the temperature, this
    # fails loudly instead of hiding inside a 1.4 % that cannot see it.
    #
    # THE GATE IS 200 kPa AND THAT IS NOT ARBITRARY. The logged side is filtered
    # at `Boost pressure > 15 psi` gauge, and (15 + 14.23) * 6.894757 = 201.5 kPa
    # absolute, so a 200 kPa gate on the model side selects the same operating
    # region BY CONSTRUCTION. Gating the model at 180 admits samples 20 kPa below
    # anything the logged set contains, which drags the model median down and
    # flatters the gap to +2.3 %. Quote the matched-gate figure, +3.0 %.
    hi = S[(S.map_kpa > 200) & (~S.maf_pinned.astype(bool))]
    logged = []
    for f in sorted(glob.glob(os.path.join(here, "logs/raw/*.csv"))):
        if os.path.basename(f) not in set(hi.source):
            continue
        d = pd.read_csv(f)
        bc = [c for c in d.columns if c.lower() == "boost pressure"]
        ac = [c for c in d.columns if "ambient" in c.lower() and "press" in c.lower()]
        if not bc:
            continue
        b = pd.to_numeric(d[bc[0]], errors="coerce").dropna()
        a = pd.to_numeric(d[ac[0]], errors="coerce").median() if ac else 14.23
        logged += list((b[b > 15.0] + a) * 6.894757)
    chk("boosted model samples (gate >200 kPa)", len(hi), 587)
    chk("logged boost readings behind the comparison", len(logged), 887)
    gap = 100.0 * (hi.map_kpa.median() - np.median(logged)) / np.median(logged)
    figure("boosted model vs the car's own boost channel",
           round(float(gap), 1), 3.0, 0.4, " %  (was +23.7 with the sensor)",
           patterns=[r"charge_temperature\(\)[^\n]*?\|[^\n|]*?\|\s*\*{0,2}"
                     + NUM + r"\s*%"],
           files=ALL, dtol=0.4)

    print("\nBASELINE ECU CONSTANTS  (engine_env.py)")
    figure("ENR_LOAD, the enrichment gate", 180.0, 180.0, 0.0, " kPa",
           patterns=[r"ENR_LOAD\s*=\s*" + NUM], files=ENV)

    report_documents()
    check_retired(here)

    bad = RESULTS.count(False)
    print("\n" + "=" * 72)
    if bad:
        print(f"{bad} of {len(RESULTS)} checks failed.")
        print("Fix the DOCUMENT or the CODE, never this file's expected value.")
        raise SystemExit(1)
    print(f"All {len(RESULTS)} checks pass "
          f"({DOC_HITS} figure mentions scanned in the documents).")


if __name__ == "__main__":
    main()
