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

WHAT CHANGED ON 16 SEPTEMBER
----------------------------
Three things, and two of them were defects in this file rather than in a
document it checks.

1. **It crashed while reporting a finding.** `report_documents()` echoes the
   offending line back; CHECKPOINT.md line 54 contains a tick emoji; on a cp1252
   console that raised UnicodeEncodeError and killed the run AFTER every check
   had already been computed correctly. That is the character-encoding bug
   CLAUDE.md records against build_dataset.py, for the third time, in the one
   script whose whole job is to be trusted. Output is now encoded defensively --
   see `_console_safe`.

2. **Two neighbouring checks were counting different populations.** "samples
   pinned at the 1020 kg/h ceiling" counted the warm-filtered dataset while
   "drives showing that exact ceiling" counted raw files in logs/raw/. `pull01`
   pins 56 times in its raw log and contributes zero samples, so the two drifted
   apart the moment it arrived: 6 drives against 517 samples over 5. Both were
   true and the sentence a document builds from them was not. Both now count the
   same set.

3. **The dataset grew to nine drives** and the expectations moved with it, which
   is the one legitimate reason to edit an expected value in this file: the data
   genuinely changed. `app/alerts.py`, `app/estimator.py` and `app/reader.py`
   joined TRACKED_DOCS at the same time, because they publish figures in their
   docstrings exactly the way plant.py does.

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
EXEMPTED = {}          # rel path -> how many lines a RETIRED-OK marker covered
BARE_MARKERS = {}      # rel path -> markers that name no figure at all
HERE = os.path.dirname(os.path.abspath(__file__))

# Documents whose numbers must agree with the data. These are the files a
# reader or an examiner actually meets. Code files are included because their
# docstrings publish figures too -- base_lambda()'s table and
# charge_temperature()'s evidence table are both cited in the thesis.
# REFERENCES.md is tracked so that the figures it quotes from our own logs
# (its section 5) cannot drift from the data any more than the others can.
TRACKED_DOCS = [
    "CLAUDE.md",
    "README.md",
    "validation_table.md",
    "REFERENCES.md",
    "CHECKPOINT.md",
    "handoff.md",
    "logs/CHANNEL_SET_FINAL.md",
    "plant.py",
    "engine_env.py",
    "compare_log.py",
    "build_dataset.py",
    # The live app publishes figures in its docstrings too -- alerts.py carries
    # the whole mismatch investigation and every threshold's justification, and
    # estimator.py carries the turbine time constants. Added 16 September 2026
    # after alerts.py was found still quoting the pre-correction +2.3 % charge
    # temperature that plant.py had already been moved off. Same failure as
    # mistake 11: the number was right in one file and stale in its neighbour.
    "app/alerts.py",
    "app/estimator.py",
    "app/reader.py",
    # AUDIT.md L11: this checker scanned .md and .py only, so the briefing page
    # -- which hard-codes the premise figures dozens of times -- was invisible
    # to it and drifted all the way to void. A page shown to an examiner is a
    # document whatever its extension.
    "presentation/index.html",
]

# ---------------------------------------------------------------------------
# ONE FILE LIST FOR BOTH SCANS   (AUDIT2.md C2-2, C2-3, M2-7d)
# ---------------------------------------------------------------------------
# Until 21 September there were two, and they disagreed:
#
#   the figure scan   read the 15 hand-maintained names in TRACKED_DOCS above
#   the retired scan  globbed **/*.md plus ROOT-LEVEL *.py, non-recursively
#
# So `app/alerts.py`, `app/estimator.py`, `app/reader.py` and
# `presentation/index.html` were figure-scanned and retired-UNscanned, while
# `presentation/plan.html`, `presentation/data.js`, `app/server.py` and
# everything under `results/`, `DOC/` and `team/` were in neither. The audit
# measured the cost: the deck a supervisor is shown carries the void premise
# set on more than a hundred lines and the checker printed green over it.
#
# One list now, built from `git ls-files` so that a file which is IN THE
# REPOSITORY cannot be outside the checker by accident. That is the property
# the two hand-maintained lists could not have.
#
# What is deliberately excluded, and why each one:
#   data/, logs/raw/   measurements. Every figure in this project appears
#                      somewhere in a timestamp column; scanning them turns
#                      every check into noise. `build_dataset.py` guards these.
#   *.csv, *.json      generated. Regenerate, do not edit -- and sweeps.json is
#                      a numeric dump where every retired figure occurs by
#                      coincidence.
#   binaries           .docx/.pdf/.pptx cannot be grepped. DOCUMENT_STATUS.md
#                      records which of them carry void numbers; that is the
#                      only handle this checker has on them and it is a real
#                      coverage limit, so say it in the thesis.
SCAN_EXT = (".md", ".py", ".html", ".js", ".txt")
SCAN_SKIP_DIRS = ("data/", "logs/raw/", "runs/", "runs_sixspeed_18sep/",
                  ".venv/", "node_modules/")
_FILE_CACHE = {}


def tracked_files(here):
    """Every file either scan reads, as repo-relative paths, sorted.

    From `git ls-files` when there is a checkout, because "tracked by git" is
    the definition a reader assumes and a hand-kept list cannot hold. Falls
    back to a glob so the checker still runs from an unpacked archive -- which
    is the exact situation CLAUDE.md mistake 16 says to run it in.
    """
    if "files" in _FILE_CACHE:
        return _FILE_CACHE["files"]
    out = []
    try:
        import subprocess
        r = subprocess.run(["git", "ls-files"], cwd=here, capture_output=True,
                           text=True, timeout=20)
        if r.returncode == 0 and r.stdout.strip():
            out = r.stdout.splitlines()
    except (OSError, subprocess.SubprocessError):
        out = []
    if not out:
        for ext in SCAN_EXT:
            out += [os.path.relpath(p, here).replace("\\", "/")
                    for p in glob.glob(os.path.join(here, "**", "*" + ext),
                                       recursive=True)]
    keep = sorted({
        f.replace("\\", "/") for f in out
        if f.endswith(SCAN_EXT)
        and not f.replace("\\", "/").startswith(SCAN_SKIP_DIRS)
    })
    _FILE_CACHE["files"] = keep
    return keep


_TAG = re.compile(r"<[^>\n]*>")
# A RETIRED-OK marker written as an HTML comment. `_TAG` strips `<!-- ... -->`
# along with every other tag, so until 22 September 2026 EVERY marker in
# `presentation/*.html` was invisible to both scans -- decorative, not
# functional -- while the deck's own authors were told to use them. Found
# during the fix-3 sweep. The comment's content is kept as plain text, ending
# in " --> " so `_historical_lines` still finds where the annotation stops.
_MARKER_COMMENT = re.compile(r"<!--\s*(RETIRED-OK\b.*?)\s*-->")
_ENTITY = {"&nbsp;": " ", "&amp;": "&", "&lt;": "<", "&gt;": ">",
           "&quot;": '"', "&#39;": "'", "&deg;": "deg", "&minus;": "-",
           "&ndash;": "-", "&mdash;": "--", "&times;": "x"}


def read_lines(path):
    """A file's lines as the SCANNER should see them, one entry per real line.

    HTML and JS are stripped of tags and entities, so that
    `<td><strong>548.6</strong></td>` reads as a number in prose. AUDIT2.md
    M2-7b: `presentation/index.html` was inside the figure scan and only 8 of
    25 figures could reach it, because every pattern in this file is anchored
    to words and the words were on the other side of a tag.

    Stripping is per line and never joins lines, so a reported line number is
    still the line number in the file the reader will open.
    """
    try:
        with open(path, encoding="utf-8") as fh:
            block = fh.read().splitlines()
    except (OSError, UnicodeDecodeError):
        return [], []
    if not path.endswith((".html", ".js")):
        return block, block
    clean = []
    for line in block:
        s = _MARKER_COMMENT.sub(lambda m: " " + m.group(1) + " --> ", line)
        s = _TAG.sub(" ", s)
        for k, v in _ENTITY.items():
            s = s.replace(k, v)
        clean.append(s)
    return block, clean

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


_FIGTOKEN = re.compile(r"[-+]?\d+(?:\.\d+)?%?")


def _marker_figures(annotation):
    """The figures a RETIRED-OK marker names, as a set of number strings.

    AUDIT2.md H2-6. A marker used to exempt its whole paragraph -- or its whole
    SECTION -- from EVERY check, including the comparison against the live data.
    Measured: 267 of README.md's 522 lines, 251 of CHECKPOINT.md's 1101. An
    "8 of 11 -> 9 of 11" edit inside an exempt paragraph passed; the same edit
    one line outside it failed.

    So the marker now carries the figures it is excusing:

        <!-- RETIRED-OK: 168.1, 113 -->   excuses ONLY those two numbers, in
                                          this paragraph, in both scans.
        <!-- RETIRED-OK: section 829.2 -->  the same, to the end of the section.

    A marker that names NO figure keeps its old paragraph or section scope, but
    only over the RETIRED scan -- the historical-record case it was written for.
    It can no longer switch off the comparison against the data, because that
    comparison is about what is TRUE TODAY and no marker should be able to
    silence it. Bare markers are counted and printed per file so the remaining
    blunt instrument is visible rather than invisible.
    """
    return {t.rstrip("%") for t in _FIGTOKEN.findall(annotation)}


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
    covered = {}
    for i, line in enumerate(block):
        if RETIRED_OK not in line:
            continue
        # A MENTION IS NOT A MARKER. Five passages in this repository discuss
        # the mechanism -- "a passage must carry `<!-- RETIRED-OK -->`", "the
        # marker exempts its whole paragraph" -- and every one of them was
        # switching the checker off for the paragraph it appeared in, including
        # one whose next sentence states a live and wrong dwell figure. An
        # occurrence inside an inline code span (an odd number of backticks
        # before it) is prose about the marker, not a marker.
        if line[:line.index(RETIRED_OK)].count("`") % 2:
            continue
        annotation = line.split(RETIRED_OK, 1)[1]
        annotation = annotation.split("-->")[0].lstrip(": \t")
        # THE FIGURES ARE THE LIST, NOT THE EXPLANATION. Markers here are
        # written "RETIRED-OK: 900.9 -- the baseline at dt 0.2, not the
        # protocol step of dt 1.0", and `_marker_figures` used to pull EVERY
        # number out of that whole string -- so the marker also excused 0.2
        # and 1.0 in its scope, figures nobody meant to retire. Found by the
        # 22 September sweep review ("RETIRED-OK: 0.837, 46 -- figures of
        # 16 September" excused 16). The list ends at the first spaced
        # double dash, em dash or en dash; the explanation after it names
        # nothing. A marker whose figures are all IN the explanation is now,
        # correctly, a bare marker.
        annotation = re.split(r"\s(?:--|\u2014|\u2013)\s", annotation + " ", maxsplit=1)[0]
        # AUDIT2.md H2-6: the section form used to trigger on the SUBSTRING
        # "section" anywhere in the first 24 characters, so a marker whose
        # explanation happened to use the word took the whole section with it.
        # It is a word now, and it has to be one of the comma-separated tokens.
        tokens = [t.strip().lower() for t in re.split(r"[,;]", annotation)]
        whole_section = any(t == "section" or t.startswith("section ")
                            or t.startswith("section:") for t in tokens)
        figures = _marker_figures(annotation)
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
            prev = covered.get(k + 1)
            covered[k + 1] = figures if prev is None else (prev | figures)
    return covered


def _num_token(value):
    """A number as a marker would write it: '1.4', '168.1', '11', '-0.47'."""
    if isinstance(value, float) and value == int(value):
        return str(int(value))
    return f"{value:g}" if isinstance(value, float) else str(value)


def _paragraph_is_historical(block, n, is_md, figure=None, rel=None):
    """True if line n is inside a passage marked historical FOR THIS FIGURE.

    Recomputed per call rather than cached: caching on id(block) looked cheap
    and is wrong, because CPython reuses an id once the old list is collected,
    so one file's exemptions could silently answer for another's.

    `figure` is the value the scanner found written on the line. When the
    marker names figures, only a matching one is excused. When it names none,
    the exemption applies only where `figure is None` -- the RETIRED scan --
    and never to the comparison against the live data. See `_marker_figures`.
    """
    covered = _historical_lines(block, is_md)
    if n not in covered:
        return False
    named = covered[n]
    if not named:
        if rel is not None:
            BARE_MARKERS[rel] = BARE_MARKERS.get(rel, 0) + 1
        return figure is None
    if figure is None:
        return True
    return _num_token(figure) in named or str(figure) in named


def scan_documents(label, value, patterns, files, tol):
    """Fail if any named document states a DIFFERENT value for this figure.

    `value` is the number computed from the shipped data -- the same one the
    data check used. Documents are compared against the DATA, never against a
    constant in this file, which is the whole point of the rework.
    """
    global DOC_HITS
    hits = 0
    # PER-PATTERN, not per-figure. The module docstring promises that "a
    # pattern that matches NOTHING anywhere is reported as a warning, so a
    # rotted pattern cannot sit silently forever" -- and the counter only
    # checked the TOTAL across a figure's patterns, so one living pattern hid
    # any number of dead ones beside it. Found the hard way: a \b in the
    # novel-alert pattern was written as a literal backspace character and the
    # figure still reported hits, from its sibling.
    per_pattern = [0] * len(patterns)
    for rel in files:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            continue
        raw, block = read_lines(path)
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
            for _pi, pat in enumerate(patterns):
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
                    per_pattern[_pi] += 1
                    DOC_HITS += 1
                    # Report the line the NUMBER is written on. When the match
                    # came from the joined window and the capture starts past
                    # the end of the first line, the figure is on the second.
                    lineno = n + 1 if (used_window and m.start(1) >= len(line)) else n
                    src = raw[lineno - 1] if lineno <= len(raw) else line
                    if abs(got - value) > tol:
                        # Figure-specific: a marker has to NAME this number to
                        # excuse it (AUDIT2.md H2-6).
                        if _paragraph_is_historical(block, lineno, is_md,
                                                    figure=got, rel=rel):
                            EXEMPTED[rel] = EXEMPTED.get(rel, 0) + 1
                            continue
                        if _known_stale(rel, label, (rel, lineno, label, round(got, 4)), value=got):
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
    elif len(patterns) > 1:
        for _pi, _n in enumerate(per_pattern):
            if _n == 0:
                DOC_UNMATCHED.append(f"{label}  [pattern {_pi + 1} of "
                                     f"{len(patterns)} matched nothing]")
    return hits


def scan_allowed(label, allowed, patterns, files, tol=0.05):
    """Fail if a document states a value for `label` that is not in `allowed`.

    For a figure that legitimately has MORE THAN ONE correct value. The app's
    peak estimated turbine is the case that forced it: `app/test_replay.py`
    pins 890.6 C for `7475b5d7` and 608.0 C for `pull01`, both are written the
    same way ("peak estimated turbine 890.6 C"), and no pattern separates them
    -- so a single-valued check reports every correct mention of one of them as
    a drift away from the other.

    The claim this makes is the right one anyway: **any estimated-turbine peak
    a document quotes must be one of the two the suite pins.** A drift to 895.1
    fails, and so does the superseded 593.7, which is what should happen.
    """
    global DOC_HITS
    hits = 0
    # PER-PATTERN, not per-figure. The module docstring promises that "a
    # pattern that matches NOTHING anywhere is reported as a warning, so a
    # rotted pattern cannot sit silently forever" -- and the counter only
    # checked the TOTAL across a figure's patterns, so one living pattern hid
    # any number of dead ones beside it. Found the hard way: a \b in the
    # novel-alert pattern was written as a literal backspace character and the
    # figure still reported hits, from its sibling.
    per_pattern = [0] * len(patterns)
    for rel in files:
        path = os.path.join(HERE, rel)
        if not os.path.exists(path):
            continue
        raw, block = read_lines(path)
        is_md = path.endswith(".md")
        for n, line in enumerate(block, 1):
            nxt = block[n] if n < len(block) else ""
            window = line + " " + nxt.strip()
            for _pi, pat in enumerate(patterns):
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
                    per_pattern[_pi] += 1
                    DOC_HITS += 1
                    lineno = n + 1 if (used_window and m.start(1) >= len(line)) else n
                    if any(abs(got - a) <= tol for a in allowed):
                        continue
                    if _paragraph_is_historical(block, lineno, is_md,
                                                figure=got, rel=rel):
                        EXEMPTED[rel] = EXEMPTED.get(rel, 0) + 1
                        continue
                    if _known_stale(rel, label, (rel, lineno, label, round(got, 4)), value=got):
                        continue
                    src = raw[lineno - 1] if lineno <= len(raw) else line
                    if any(r[0] == rel and r[2] == label and r[3] == got
                           and abs(r[1] - lineno) <= 1 for r in DOC_FAILURES):
                        continue
                    DOC_FAILURES.append(
                        (rel, lineno, label, got,
                         " or ".join(str(a) for a in allowed), src.strip()[:100]))
    if hits == 0:
        DOC_UNMATCHED.append(label)
    elif len(patterns) > 1:
        for _pi, _n in enumerate(per_pattern):
            if _n == 0:
                DOC_UNMATCHED.append(f"{label}  [pattern {_pi + 1} of "
                                     f"{len(patterns)} matched nothing]")
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
        # AUDIT.md H3: dwell used to be `run / 4.6` -- a RUN OF ROWS divided by
        # an assumed 4.6 Hz, for every drive. The drives log at 4.34-6.63 Hz,
        # so dwell was overstated by up to 44 % on the fast ones and understated
        # on 7475b5d7, and ENR_DWELL_LO/HI were fitted against that distorted
        # axis. The timestamps are right there in the column; use them.
        dt = d["t"].diff().fillna(0.0).clip(lower=0.0, upper=5.0).to_numpy()
        acc, run = 0.0, np.zeros(len(d))
        for i, v in enumerate((d.map_kpa > thr).fillna(False)):
            acc = acc + dt[i] if v else 0.0
            run[i] = acc
        d["dwell"] = run
        d["dt_s"] = dt          # carried so callers need not re-derive it
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
     "dataset size before 7475b5d7", "nine drives, 175.5 minutes, six carrying"),
    # Added 14 September, after pull01. The sweep that renamed eight -> nine
    # missed five lines and nothing was guarding the old total, so the same
    # figure could have come back a fourth time. Match 168.1 only: "eight
    # drives" on its own is still TRUE of the enrichment map and the
    # compressor fit, because pull01 contributes zero samples to either.
    (r"\b168\.1\b", "dataset size before pull01, the ninth drive",
     "175.5 minutes over nine drives, six carrying samples"),
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

    # --- added 19 Sep 2026, when the TAIF drive entered the replay table.
    # drive10 is Jeddah -> Taif -> Jeddah, 119.4 min, and it contributes ZERO
    # seconds above the trigger, so the numerator did not move and only the
    # denominator did: 36 s of 172.6 min -> 36 s of 292.0 min. Both halves are
    # guarded, because the 14 September lesson was that a retired total comes
    # back through whichever half nothing is watching.
    (r"\b172\.6\b", "replayed minutes before drive10, the Taif climb",
     "292.0 replayed minutes over ten drives"),
    (r"0\.351\s*%", "fraction of replayed time above the trigger, before Taif",
     "0.206 %"),

    # --- added 14 Sep 2026. ALL THREE OF THESE HAD ALREADY BEEN CORRECTED
    # ONCE, in v17, and came back in the v19 release archive. Nothing was
    # guarding them, which is the entire argument for this list: a correction
    # that is not asserted somewhere is a correction with a short half-life.
    (r"reactive cuts damage 33\.9|[-−]33\.9 %", "33.9 %, which the printed "
     "damage figures do not support at any rounding (1 - 548.6/829.2 = 33.84)",
     "33.8 %"),
    (r"four\s+separate drives, 192 samples", "MAF-ceiling count from 7 drives",
     "five separate drives, 517 samples -- the figure this file itself asserts"),
    (r"median ratio 1\.163", "combustion-air ratio from 7 drives", "1.095"),

    # --- added 16 September 2026, from the AUDIT.md pass. Each of these was
    # measured on an axis that turned out to be wrong, or against a baseline
    # that turned out not to be neutral. The replacement is named beside it.
    (r"\b178 seconds\b", "dwell seconds from rows over an assumed 4.6 Hz (H3)",
     "184 s, summed from the timestamps"),
    (r"dwell[^)\n]{0,32}\)\s*[-−]0\.47",
     "corr(lambda, dwell) on the 4.6 Hz axis (H3)", "-0.41 on real timestamps"),
    (r"\b829\.2\b", "premise baseline with its cooling disabled (C1)",
     "674.1 with the true neutral -- and C2 means the scenario no longer binds"),
    (r"\b548\.6\b", "premise reactive against a cooling-disabled baseline (C1)",
     "529.5, and see C2"),
    (r"\b437\.6\b", "premise predictive against a cooling-disabled baseline (C1)",
     "434.6, and see C2"),
    (r"13\.4\s*(?:points|pts)", "preview edge built on the C1 and C3 artefacts",
     "run check_premise.py -- preview over CURRENT GRADE is the honest figure"),
    (r"16\.5\s*(?:->|→)\s*18\.0\s*(?:->|→)\s*26\.0",
     "the H2 table measured against a cooling-disabled baseline (C1)",
     "run generality_test.py"),

    # --- added 17 September 2026. NOT a figure -- the university's name.
    # CLAUDE.md line 13 read "King Abdulaziz University, Jeddah" until commit
    # d57f3da (14 Sep), where it was corrected to "University of Jeddah" INSIDE
    # a commit whose subject was "docs: add REFERENCES.md" -- so the change is
    # invisible from the log, and any copy taken from `main` before the
    # 17 September merge still carries the wrong name. The two are genuinely
    # confusable: the University of Jeddah was split out of King Abdulaziz
    # University in 2014. Confirmed with the team on 17 September: it is the
    # University of Jeddah.
    #
    # This guard covers the tracked .md and .py files only. It CANNOT see
    # DOC/*.docx, DOC/*.pdf or presentation/index.html -- all three were checked
    # by hand on 17 September and none carries a university name at all, which
    # is its own open question if the submission template requires one.
    (r"King\s+Abdul\s*[aA]ziz", "the wrong university, corrected in d57f3da",
     "University of Jeddah / جامعة جدة"),

    # --- added 21 September 2026, from AUDIT2.md C2-1. THIS ONE GUARDS A CLAIM
    # SHAPE, NOT A VALUE, and that is the whole point of it.
    #
    # `results/phase_d_seed0.txt` says "SIGHTED over BLINDED: +11.7 points <-
    # THE ABLATION. This is the project's result." Those agents were trained on
    # an invented six-speed gearbox that commit 27e720c replaced seven hours
    # later; re-scored on this tree the same pair gives +7.5, and the +11.7
    # cannot be regenerated here at all because the engine_env.py it needs no
    # longer exists. The audit's verdict on which of the two is the result is
    # "Neither."
    #
    # Retiring the NUMBER 11.7 would let 13.7 through -- and the auditor's own
    # drift test did exactly that edit. So the pattern matches ANY sighted-over-
    # blinded margin quoted in points. There is no correct value for it on this
    # tree, and the honest guard is one that says so rather than one that
    # blesses whatever number replaces the void one.
    # --- THREE SHAPE PATTERNS WERE HERE AND WERE REMOVED ON 22 SEPTEMBER,
    # because the condition they guarded has been MET.
    #
    # They matched ANY sighted-over-blinded margin quoted in points, on the
    # ground that no such figure was quotable on this tree: the only pair that
    # existed had been trained on a gearbox the branch had replaced. Their own
    # replacement text said so -- "Retrain both agents on the current plant
    # first."
    #
    # That was done. Sixteen agents, eight seeds per arm, trained on the ZF
    # plant under results/PREREGISTRATION.md, which was committed before any of
    # them started. `results/phase_d_seed*.txt` now print a sighted-over-blinded
    # margin that IS quotable, and the shape patterns flagged all eight of them.
    #
    # A guard whose stated precondition has been satisfied and which then fires
    # on the work that satisfied it is not protecting anything -- it is the
    # 14 September lesson ("a retired-value list has to be swept when the value
    # that replaced it moves on") arriving on a rule written the day before.
    #
    # The VALUE pattern below stays, because 11.7 is still void whatever else
    # is now true, and it is what makes the audit's own drift row -- editing
    # +11.7 to +13.7 -- fail: that pattern's count drops, and the known-stale
    # ledger reports a row that shrank.
    # AND THE VALUE ITSELF, beside the shape. The shape pattern above cannot
    # tell +11.7 from +13.7 -- it is written not to -- so on its own it counts
    # a mention rather than watching it. This one matches only the void figure,
    # so editing 11.7 to anything else makes its count DROP, which the
    # known-stale ledger reports as a change. Shape catches a new claim; value
    # catches an old claim being quietly rewritten. Both are needed.
    #
    # `points|pts` is required: CLAUDE.md mistake 13b carries a live and correct
    # "+11.7 K" heat-soak offset that must not be touched.
    (r"[-−+]?11\.7\s*(?:points|pts|-point)",
     "the void +11.7 Phase D ablation margin (C2-1)",
     "NOTHING -- it was produced on a gearbox this branch replaced seven hours "
     "later, and re-scoring the same pair here gives a different number that is "
     "not a result either"),
]

# Files whose whole job is to record what changed, so they are expected to
# contain retired values throughout. Exempting them is deliberate.
#
# AUDIT2.md C2-2 moved the figure scan onto the same file list as the retired
# scan, so this set now governs BOTH. That is the right reading of what it has
# always meant: a review or a changelog quotes the figure it found wrong, and
# a checker that flags it is flagging the finding rather than the fault.
# AUDIT2.md M2-4 says so explicitly about `AUDIT_FIXES.md` -- "do NOT add the
# whole file to TRACKED_DOCS; split the live table into its own tracked file".
#
# THE COST IS REAL AND IS STATED WHERE THE AUDIT STATES IT: a file in here is
# unguarded in full, so a LIVE wrong figure inside one passes. None of them is
# a source of truth and nothing should be quoted from one without running the
# script it cites.
RETIRED_EXEMPT = {"DOCUMENT_STATUS.md", "CHANGELOG.md",
                  "DRIVE_1_card_v1.md", "DRIVE_1_card_v2.md",
                  # AUDIT.md is a review: quoting the figures it found wrong is
                  # the whole of its content. Exempting it is the same call as
                  # DOCUMENT_STATUS.md above.
                  "AUDIT.md",
                  # The response to the audit: every row names the figure it
                  # replaced. Same call as DOCUMENT_STATUS.md and AUDIT.md.
                  "AUDIT_FIXES.md",
                  # The SECOND audit, 21 September 2026. Same call again: it
                  # quotes the void premise set dozens of times because naming
                  # what the presentation still ships IS its finding C2-3.
                  # Note what this exemption costs, because AUDIT2.md's own
                  # finding M2-7 is about exactly this blunt instrument: the
                  # file is now unguarded in full, so a LIVE wrong figure in it
                  # would pass. It is a report, not a source of truth, and
                  # nothing should ever be quoted from it without running the
                  # script it cites.
                  "AUDIT2.md",
                  # The acceptance test for this file. Its whole content is
                  # pairs of (correct figure, deliberately wrong figure) to
                  # inject -- "959.8 at 884 C" beside "959.8 at 870 C" -- so a
                  # scanner reading it finds the wrong half of every pair and
                  # reports the test as the fault. Same call as AUDIT.md.
                  "drift_test.py",
                  # The transcript of a full run. It is a RECORDING of other
                  # programs' output -- including this checker's own ledger
                  # lines and drift_test.py's deliberately wrong injections
                  # ("8 of 11" -> "9 of 11") -- so scanning it reports the
                  # recording as a claim. Regenerate it with full_run.py; never
                  # quote a figure from it that the block above it did not
                  # print.
                  "FULL_RUN.txt"}

# Exempt by DIRECTORY, where a basename rule would be wrong. `results/void/`
# holds result files this project has declared void, beside a README whose
# whole content is why they are void -- so every figure in it is a quotation of
# something retired, on purpose. Exempting it by basename is not available:
# one of the files is called README.md, and that would exempt every README in
# the repository.
RETIRED_EXEMPT_DIRS = ("results/void/",)

# A line that names a retired figure ON PURPOSE -- "the old 39.5 s figure is
# void", the mistake log's was/should-say tables -- carries this marker. It is
# deliberately explicit: an automatic rule would eventually skip a line that IS
# a live claim, and the point of this check is that nothing gets skipped by
# accident. If you add the marker, you are asserting the line is history.
RETIRED_OK = "RETIRED-OK"

# ---------------------------------------------------------------------------
# THE KNOWN-STALE LEDGER   (AUDIT2.md H2-1, H2-4, C2-3 -- fix 3, not yet done)
# ---------------------------------------------------------------------------
# Turning the guard on over the whole repository surfaced roughly two hundred
# and fifty stale figures in one run. Every one of them is ALREADY a written
# finding in AUDIT2.md with a fix scheduled: the document sweep (its fix 3).
#
# Three things could have been done with them and two are wrong.
#
#   1. Leave the checker red. A checker that is red for a week is a checker
#      nobody reads, and this project's house rule is to run it before quoting
#      any number. Red-by-default destroys the only signal it has.
#   2. Exempt the files. That is the blunt instrument AUDIT2.md H2-6 is about,
#      one level up, and it is how `presentation/index.html` drifted to void
#      while sitting inside the figure scan.
#   3. Count them. This.
#
# Each row is (file-or-prefix, figure label, AUDIT2 finding, exact count). The
# hits are reported under KNOWN with the finding id beside them, and the COUNT
# IS ASSERTED. One more occurrence fails -- the rot cannot grow. One fewer
# fails too, and that is deliberate: when the sweep lands, the ledger row has
# to be lowered in the same commit, which is the 14 September lesson ("a
# retired-value list has to be swept when the value that replaced it moves
# on") applied to the ledger itself.
#
# A row here is a DEBT with a named creditor. It is not an exemption: nothing
# is hidden, the count is printed every run, and the total is printed at the
# end so that "how much document rot is outstanding" is one number instead of
# an afternoon's grepping.
# SWEPT 22 September 2026 -- AUDIT2.md fix 3. Every one of the 78 rows that
# stood here (187 stale mentions across 19 files) reached ZERO in one sweep:
# live claims corrected to the figures this file computes, dated history kept
# and marked with figure-naming RETIRED-OK markers, presentation/data.js
# regenerated by presentation/dump_traces.py rather than edited. Seven file
# units, each swept and then adversarially reviewed against the same truth
# sheet; 13 blockers found by review were fixed before this ledger was lowered.
#
# THE LEDGER IS NOW EMPTY AND SHOULD STAY EMPTY. An empty list means nothing
# is excused as known rot: a stale figure anywhere now fails the DOCUMENTS vs
# DATA or RETIRED check outright. If a future sweep has to be staged again,
# re-add rows with exact counts -- never to silence a failure nobody has
# written down as a finding.
KNOWN_STALE = []







_STALE_SEEN = {}


_STALE_KEYS = set()
_STALE_VALUES = {}


def _known_stale(rel, label, key=None, value=None):
    """True if (file, figure) is a ledgered, already-reported staleness.

    `key` identifies the MENTION, so that one claim is counted once however
    many patterns match it. Two patterns routinely hit the same figure on the
    same line, and a claim that wraps is seen once from each of its two lines --
    the same reason `scan_documents` de-duplicates its own failures. Counting
    calls instead of mentions made every ledger row read double.

    `value` is what the document actually said. IT IS RECORDED AND COMPARED,
    because a count alone cannot see a stale line CHANGE. CLAUDE.md says the
    premise baseline is "294.2 at 812 C"; both numbers are wrong and ledgered;
    edit the 812 to 799 and the count does not move. A quarantine that watches
    only how MANY wrong figures a file has is a quarantine a new wrong figure
    can hide inside -- which is mistake 11's shape one more level down.
    """
    for row in KNOWN_STALE:
        pref, lab, _finding, _spec = row
        if lab == label and (rel == pref or rel.startswith(pref)):
            if key is not None:
                if key in _STALE_KEYS:
                    return True
                _STALE_KEYS.add(key)
            _STALE_SEEN[(pref, lab)] = _STALE_SEEN.get((pref, lab), 0) + 1
            if value is not None:
                _STALE_VALUES.setdefault((pref, lab), []).append(round(value, 4))
            return True
    return False


# ---------------------------------------------------------------------------
# PINNED HISTORY   (22 September 2026 -- what the empty ledger used to catch)
# ---------------------------------------------------------------------------
# The KNOWN_STALE ledger counted every mention of the void +11.7 Phase D margin
# in the files that record it, and that COUNT is what made drift_test.py row 7
# CAUGHT: turn "+11.7" into "+13.7" and the count fell. Sweeping the ledger to
# zero removed that protection by accident -- drift_test went 16/16 -> 14/16.
#
# A marker cannot replace it: the drift rewrites the figure INSIDE the marker
# too, so the marker simply names the new number. What is being protected is
# the historical record itself -- the void figure, quoted as history, must stay
# the figure it was. So its TEXT mentions (marker annotations excluded) are
# pinned, per file, by exact count. A deliberate change to that history
# updates the pin in the same commit; an accidental one fails here.
#
# (pattern, what it is, {file: exact count of text mentions})
PINNED_HISTORY = [
    (r"(?<![\d.])11\.7(?!\d)(?!\s*K\b)",
     "the void +11.7 Phase D margin (C2-1) -- not the +11.7 K sensor offset",
     {"results/README.md": 2, "CHECKPOINT.md": 7,
      "DOC/SESSION_REPORT_2026-09-18.md": 7, "CLAUDE.md": 3}),
]
_MARKER_TEXT = re.compile(r"RETIRED-OK[^\n]*?(?:-->|\*/|$)")


def check_pinned_history(here):
    """Fail if a pinned historical figure's text mentions changed in number."""
    print("\nPINNED HISTORY  (void figures quoted as history must stay the figure they were)")
    bad = 0
    for pat, what, want in PINNED_HISTORY:
        for rel, n_want in sorted(want.items()):
            path = os.path.join(here, rel)
            try:
                lines = open(path, encoding="utf-8").read().splitlines()
            except OSError:
                lines = []
            got = sum(len(re.findall(pat, _MARKER_TEXT.sub(" ", ln))) for ln in lines)
            if got == n_want:
                print(f"  ok     {rel:<34} {what[:44]:<44} {got:>3}")
            else:
                bad += 1
                print(f"  WRONG  {rel:<34} {what[:44]:<44} {got:>3}  pinned at {n_want}")
    if bad:
        print("  A pinned count moved: a quoted void figure was edited into a")
        print("  different number, or a mention was added or removed. If that was")
        print("  deliberate, update PINNED_HISTORY in the same commit.")
    RESULTS.append(not bad)


def report_known_stale():
    """Print the ledger and fail if any row's count OR values have moved."""
    if not KNOWN_STALE:
        return
    print("\nKNOWN STALE  (already-reported rot; AUDIT2.md fix 3 sweeps it)")
    bad = 0
    total = 0
    for pref, lab, finding, spec in KNOWN_STALE:
        got = _STALE_SEEN.get((pref, lab), 0)
        total += got
        want = len(spec) if isinstance(spec, (tuple, list)) else spec
        seen = sorted(_STALE_VALUES.get((pref, lab), []))
        mismatch = None
        if got != want:
            mismatch = f"count {got}, ledger says {want}"
        elif isinstance(spec, (tuple, list)) and seen != sorted(spec):
            mismatch = f"values {seen}, ledger says {sorted(spec)}"
        if mismatch is None:
            print(f"  known  {pref:<34} {lab:<34} {got:>4}  ({finding})")
            continue
        bad += 1
        print(f"  WRONG  {pref:<34} {lab:<34} {got:>4}  {mismatch} ({finding})")
    if bad:
        print("  A row that GREW, or whose values moved, is NEW rot: fix the "
              "document.")
        print("  A row that SHRANK means the sweep landed: lower it here in the "
              "same commit.")
    RESULTS.append(not bad)
    print(f"  {total} stale figure mentions outstanding across "
          f"{len(KNOWN_STALE)} ledger rows")


def check_simulation(here):
    """Figures the SIMULATOR produces, checked against the documents.

    AUDIT.md H2, and it is the most useful thing in this file that was missing.
    Every `figure()` above recomputes a DATASET statistic from data/*.csv. Not
    one of them could see a simulation-derived number, so the checker printed
    green while the headline drifted. The reviewer demonstrated it by editing a
    scratch copy of the documents:

        README: 548.6 -> 561.2, 437.6 -> 402.9, 13.4 -> 19.1 points  -> all pass
        validation_table: tau 48.0 -> 61.0 s, "8 of 11" -> "10 of 11" -> all pass
        README: residual 1.4 % -> 2.9 %                              -> all pass

    Three sentences a thesis rests on, any of which could have been wrong by a
    factor, and nothing in the repository would have said so.

    This runs validate.py's own rows and compares them against the documents.
    The premise rollout is NOT run here -- it takes minutes and the figures it
    produces are currently VOID anyway (C1/C2/C3), so they live in RETIRED
    instead, which is the stronger check while they have no replacement.
    """
    import validate as V

    print("\nSIMULATION FIGURES  (AUDIT.md H2 -- these were unchecked entirely)")
    rows = V.rows() if hasattr(V, "rows") else None
    if rows is None:
        print("  note   validate.py exposes no importable row list; skipped")
        return

    inside = sum(1 for r in rows if r.get("inside"))
    figure("validate.py rows inside the published band", inside, 8, 0,
           patterns=[r"\b" + NUM + r"\s*\*{0,2}\s*of\s+\*{0,2}\s*11\b"],
           files=ALL)

    by_name = {r["name"]: r for r in rows}

    # ONLY "N of 11" is scanned in the prose. The other simulation figures are
    # asserted as VALUES and deliberately not pattern-matched, because every
    # pattern loose enough to catch a drifted one also flags a legitimate
    # sentence:
    #
    #   turbine tau 48 s   -- collides with oil 16 s, coolant 9.5 s, the IAT
    #                         sensor lag 10 s, the C/UA derivation 50.3 s and
    #                         the published band 40-120 s
    #   displacement       -- collides with mistake 1's historical 1998 cc and
    #                         "2.0 L inline-four", with the band's 2990, and
    #                         with "2.997 L" in a citation
    #
    # That is the trade AUDIT.md H2 and M15 name, and the honest answer here is
    # that a value assertion catches the drift that matters (the MODEL moving)
    # while a prose scan would mostly catch the documents being correct.
    for name, label, expect, tol in (
        ("Turbine housing time constant", "turbine time constant", 48.0, 1.0),
        ("Displacement", "displacement", 2997.5, 1.0),
    ):
        r = by_name.get(name)
        if r is not None:
            chk(label, round(float(r["model"]), 1), expect, tol)

    # The crank-angle step is now a studied number; assert it has not been
    # quietly rounded back to something convenient.
    from plant import DTHETA_DEG
    chk("crank-angle step is the studied one", DTHETA_DEG, 0.25, 0.0)
    chk("cycle model converges when the step is halved",
        bool(V.test_convergence()), True)


def check_scenario(here):
    """The constants that DECIDE the experiment, and the figures they produce.

    AUDIT2.md C2-2, and it is the finding this whole file exists to have caught
    and did not. Until 21 September the only `engine_env` constant asserted
    anywhere was `ENR_LOAD`. The auditor injected fourteen realistic drifts into
    a copy of the tree and twelve went through green, including these two:

        make_grade_climb(v_kmh=130.0) -> 120.0      the Phase D scenario
        TURB_PROTECT_K = 1123.0       -> 1100.0     the protection trigger

    Either one re-bases every damage figure, every peak and every "cuts N %" in
    the repository, while every document goes on saying 130 km/h and 850 C. That
    is not hypothetical: `results/phase_d_seed0.txt` says +11.7 points and was
    produced on a gearbox this branch replaced seven hours later, and nothing
    failed. CLAUDE.md's own rule is that "a preview advantage quoted without the
    limit it was measured against is not a result" -- so the limit has to be a
    checked number, not a remembered one.

    WHAT IS ASSERTED HERE AND WHAT IS NOT. Everything below is read from the
    LIVE object at the moment of the call -- `inspect.signature`, the class
    attribute, the module constant, the script's own printed output. Nothing is
    compared against a second copy of itself. Where a figure cannot be
    recomputed cheaply it is said so in the label rather than quietly pinned.
    """
    import inspect
    import subprocess

    import engine_env as E
    import evaluate as V
    from app import test_replay as TR

    print("\nTHE EXPERIMENT'S OWN CONSTANTS  (AUDIT2.md C2-2)")

    # ---- the locked scenario, read from the function that defines it -------
    sig = inspect.signature(E.make_grade_climb).parameters
    grade = float(sig["grade"].default)
    v_kmh = float(sig["v_kmh"].default)
    t_amb = float(sig["t_amb"].default)

    # "12 % at 130 km/h" and "12 % / 130 km/h" are how every document writes it.
    # Anchored to the grade on the left so a bare speed elsewhere cannot match.
    # THE AMBIENT IS PART OF THE ANCHOR, and it has to be. "12 % at 90 km/h"
    # is a real and correct row of the grade-by-speed sweep that CHOSE this
    # scenario (CLAUDE.md, 18 September), so a pattern keyed on the grade alone
    # reports the sweep that justifies the row as a drift away from it. The
    # scenario is written as a triple -- "12 % at 130 km/h, 42 C" / "12 % grade
    # at 110 km/h in 42 C air" -- and the sweep rows never carry the ambient.
    #
    # EACH OF THOSE IS ANCHORED ON THE OTHER AXIS'S CORRECT VALUE, so a document
    # that drifts BOTH -- "16 % at 110 km/h, 42 C", which is a real row of the
    # sweep that chose the scenario and so the likeliest way to miscopy it --
    # matches neither. The third pattern below keys on the words only the
    # locked scenario carries and validates the speed with the grade free.
    _AMB = r"\s*km/h[,\s]+(?:in\s+)?4[0-9]\s*°?\s*C"
    V_PAT = [r"12\s*%\s*(?:grade\s*)?(?:at|/)\s*\*{0,2}" + NUM + r"\s*\*{0,2}" + _AMB,
             r"(?:locked|standard|evaluation|Phase D)[^.\n]{0,40}?scenario"
             r"[^.\n]{0,30}?\d+\s*%[^.\n]{0,12}?(?:at|/)\s*\*{0,2}" + NUM
             + r"\s*\*{0,2}\s*km/h"]
    G_PAT = [NUM + r"\s*%\s*(?:grade\s*)?(?:at|/)\s*\*{0,2}130\s*\*{0,2}" + _AMB]
    figure("scenario speed, make_grade_climb(v_kmh=)", v_kmh, 130.0, 0.0, " km/h",
           patterns=V_PAT, files=ALL, dtol=0.5)
    figure("scenario grade, make_grade_climb(grade=)", round(100 * grade, 1), 12.0,
           0.0, " %", patterns=G_PAT, files=ALL, dtol=0.5)
    # 42 C and 315 K collide with far too much prose to scan for -- the ambient
    # appears in the thermal fit, the J2807 table and every drive card. Asserted
    # as a VALUE only, and that is the assertion that matters: a changed default
    # is what re-bases the experiment.
    chk("scenario ambient, make_grade_climb(t_amb=)", t_amb, 315.0, 0.0, " K")
    chk("training episode length, make_grade_climb(duration=)",
        float(sig["duration"].default), 900.0, 0.0, " s")
    chk("training step, make_grade_climb(dt=)", float(sig["dt"].default), 0.2, 0.0, " s")

    # ---- the protection trigger -------------------------------------------
    # A VALUE ASSERTION, and it says so instead of dressing up as a document
    # scan. This used to pass `patterns=[TURB_PROTECT_K = NUM]` over `ENV`,
    # which is `["engine_env.py"]` -- the module the value had been read from
    # two lines earlier. The "document" it scanned was the assignment statement
    # that produced the number, so the comparison was 1123.0 against 1123.0 and
    # could not fail, and DOC_UNMATCHED could never fire for it either. The
    # Celsius form below is the one that actually asks the documents.
    chk("TURB_PROTECT_K, the damage knee", float(E.TURB_PROTECT_K), 1123.0, 0.0, " K")
    chk("OIL_PROTECT_K", float(E.OIL_PROTECT_K), 408.0, 0.0, " K")
    figure("the trigger in Celsius, as the documents write it",
           round(float(E.TURB_PROTECT_K) - 273.15), 850, 0.0, " C",
           # ANCHORED HARD ON PURPOSE. A 26-character window around the word
           # "trigger" also captures the neighbouring number in "the 850 C
           # trigger sits inside the 825-925 C band" -- a correct sentence --
           # and, through the wrapped-line window, an unrelated EGT band row.
           # One pattern, not two: the "trigger of/is/at N C" form matched
           # nothing anywhere, and the new per-pattern rot warning said so.
           patterns=[r"\b" + NUM + r"\s*°?\s*C\s+(?:trigger|protection limit)\b"],
           files=ALL, dtol=0.6)

    # ---- the gearbox -------------------------------------------------------
    # AUDIT2.md C2-1: the six-speed that produced +11.7 differed from the ZF in
    # nothing a document could see. The ratios are a VALUE assertion because a
    # prose pattern loose enough to find a ratio table also finds every other
    # decimal in the repository; the value is what actually moved.
    chk("Vehicle.gears, the ZF 8HP51 ratio set",
        [round(float(g), 3) for g in E.Vehicle.gears],
        [5.25, 3.36, 2.172, 1.72, 1.316, 1.0, 0.822, 0.64])
    # Same tautology as TURB_PROTECT_K above: `final_drive = 3.150` is the line
    # the value came from. A value assertion, honestly labelled.
    chk("Vehicle.final_drive", float(E.Vehicle.final_drive), 3.150, 0.0)
    chk("the gearbox has eight forward ratios", len(E.Vehicle.gears), 8)

    # ---- the evaluation protocol ------------------------------------------
    chk("evaluate.DT", float(V.DT), 1.0, 0.0, " s")
    chk("evaluate.DURATION", float(V.DURATION), 720.0, 0.0, " s")
    chk("evaluate.EPISODES, the frozen set", len(V.EPISODES), 20)
    # The hash is the guard the file's own docstring asks for: "THE TWENTY
    # EPISODES ARE FROZEN. DO NOT EDIT EPISODES." Nothing enforced that. A
    # single weight changing in the fourteenth tuple moves every median in
    # Phase D and leaves no trace anywhere else.
    #
    # YES, THIS IS A CONSTANT COMPARED AGAINST ITSELF, which is the failure this
    # file's docstring is named after -- so say why it is the right shape here
    # and not an exception being smuggled in. Every other check recomputes a
    # figure from the shipped data, because the data is the authority and the
    # document is the copy. A FROZEN SET HAS NO SUCH AUTHORITY: its whole
    # content is "these twenty pairs, unchanged since 18 September 2026". There
    # is nothing to recompute it from, and the literal below IS the record that
    # it has not moved. The test to apply is the one this project uses for
    # everything else -- could this check fail? It can, on any edit to any of
    # the sixty numbers, which is precisely the event it exists to stop.
    import fingerprint as FP
    chk("evaluate.EPISODES hash (frozen 18 Sep 2026)",
        FP.episodes_sha(), "05a598a574268b20")

    # ---- the BASELINE ROW of check_premise.py, RUN, not remembered ---------
    #
    # SAY WHAT IS AND IS NOT COVERED. This runs ONE of the script's five
    # policies. `check_premise.py` prints a five-row table and three "cuts
    # damage N %" lines; two of those ten numbers are asserted here and the
    # eight produced by the reactive, current-grade and predictive rows are
    # NOT -- change `_protect`'s spark trim and every protecting row moves
    # while this stays green.
    #
    # The baseline row is the one chosen because it is the row the binding
    # question turns on, and because it is what the three entry-point documents
    # get wrong today (H2-4). Asserting the other three costs about 190 s more.
    # Until that is spent, the honest label is "the baseline row", which is why
    # it is written that way below rather than as "what check_premise prints".
    # AUDIT2.md H2-4: CLAUDE.md, README.md and handoff.md all tell a reader the
    # constraint does NOT bind and the baseline is 294.2 at 812 C. On this tree
    # the script prints 959.8 at 884 C and the constraint binds by 34 K. The
    # binding question is the one the whole experiment turns on, and it was the
    # one figure in the repository with no check of any kind on it.
    #
    # This costs about 35 seconds, which is most of this script's runtime. It is
    # one 720 s episode of the neutral policy -- the same rollout check_premise
    # runs first -- and it is worth the wait for the reason above.
    import time as _time
    import check_premise as CP
    _t0 = _time.time()
    r = CP.rollout(CP.p_neutral)
    # THE PREMISE FIGURES DESCRIBE THE LOCKED SCENARIO, and Phase D2's result
    # files record a DIFFERENT one -- a randomised 12-16 % climb, on which the
    # baseline ECU's median damage is 1118.0, not 959.8. The "baseline <3 digits
    # .1 digit>" pattern cannot read 1118.0 (four digits) and so landed on the
    # next number on that row -- the IQR, 715.9 -- and reported eight false
    # contradictions on 23 September 2026. The pattern is right for every
    # document that talks about the locked scenario; these files do not, so
    # they are taken out of THESE TWO figures only, by name. Every other check
    # still reads them.
    PREMISE_FILES = [f for f in ALL
                     if not re.match(r"results/d2_seed\d+\.txt$", f)]
    print(f"  note   one neutral premise rollout, {_time.time() - _t0:.0f} s")
    figure("check_premise baseline damage", round(float(r["damage"]), 1), 959.8, 0.3,
           # THREE DIGITS AND ONE DECIMAL. Every damage figure this project has
           # ever published is written that way (959.8, 572.8, 294.2, 414.4),
           # and a bare NUM after the word "baseline" reads the 1.0 out of
           # "coolant pump | baseline at 1.0" and "the baseline fan never
           # reaches 1.0".
           # THREE FORMS, because this project writes results three ways and the
           # prose form alone was blind to two of them. `[^.\n|]` stops dead at
           # a markdown pipe, so `| baseline ECU (true neutral) | 3620 | 294.2 |
           # 812 C |` -- the void table in the PUBLIC README -- matched nothing;
           # and a pasted console block puts more than 26 characters of padding
           # between the word and the number.
           patterns=[r"baseline[^.\n|]{0,26}?\b(\d{3}\.\d)\b",
                     r"\b(\d{3}\.\d)\s+at\s+\d{3}\s*°?\s*C",
                     r"^[>\s]*\|[^|\n]*baseline[^|\n]*\|[^|\n]*\|\s*\*{0,2}"
                     r"(\d{3}\.\d)\s*\*{0,2}\s*\|",
                     r"^[>\s]*baseline[^|\n]{0,40}?\s(\d{3}\.\d)\s"],
           files=PREMISE_FILES, dtol=0.3)
    figure("check_premise baseline peak turbine",
           round(float(r["peak_turb"])), 884, 0.6, " C",
           # ANY "baseline <damage> at <peak> C" sentence, not just one that
           # already carries the right damage. CLAUDE.md says "baseline 294.2 at
           # 812 C" -- both halves wrong -- and a pattern anchored on 959.8
           # cannot see the 812 at all, so the peak could drift again inside an
           # already-wrong line without anything moving.
           patterns=[r"baseline[^.\n|]{0,26}?\d{3}\.\d\s*(?:at|/|\|)\s*\*{0,2}"
                     + NUM + r"\s*\*{0,2}\s*°?\s*C",
                     r"\b(?:959\.8|960)\b[^.\n|]{0,14}?(?:at|/|\|)\s*\*{0,2}" + NUM
                     + r"\s*\*{0,2}\s*°?\s*C",
                     # the pipe-table form, as the README writes it
                     r"^[>\s]*\|[^|\n]*baseline[^|\n]*\|[^|\n]*\|[^|\n]*\|\s*\*{0,2}"
                     + NUM + r"\s*\*{0,2}\s*°?\s*C\s*\*{0,2}\s*\|"],
           files=PREMISE_FILES, dtol=0.6)
    binds = float(r["peak_turb"]) > float(E.TURB_PROTECT_K) - 273.15
    chk("the constraint BINDS on the locked scenario", binds, True)

    # ---- Phase B's headline residual, read off compare_log's own output ----
    # AUDIT2.md M2-1 and drift row 4: "1.4 % with zero fitted parameters" is the
    # sentence Phase B rests on and nothing asserted it. Rather than duplicate
    # the arithmetic here -- which would be a checker checking itself -- run the
    # script and read what it prints, which is the project's own rule.
    rc, text, err = None, "", ""
    try:
        out = subprocess.run([sys.executable, "compare_log.py",
                              "data/master_points.csv"], cwd=here,
                             capture_output=True, text=True, timeout=300,
                             encoding="utf-8", errors="replace")
        rc, text, err = out.returncode, out.stdout, out.stderr
    except (OSError, subprocess.SubprocessError) as exc:
        err = str(exc)
    # THE EXIT CODE IS PART OF THE READING. compare_log.py prints the residual
    # block two thirds of the way through its output and can die in any of the
    # twenty lines after it -- including `raise SystemExit(2)` on its own
    # "too few points, NOT A PASS" path. Reading only stdout would then find
    # both regexes on already-printed text and report three green checks for a
    # script that failed. That is mistake 9's shape: a check that fails open
    # still prints a number.
    chk("compare_log.py exited 0", rc, 0)
    if rc != 0:
        print(f"  note   compare_log.py returned {rc}; "
              f"stderr tail: {_console_safe(err.strip()[-160:]) or '(empty)'}")
    m_fit = re.search(r"FITTED\s+k\s*=\s*([\d.]+)\s+residual MAPE\s+([\d.]+)", text)
    m_der = re.search(r"DERIVED[^\n]*?residual MAPE\s+([\d.]+)", text)
    if m_fit and m_der:
        figure("load residual, k DERIVED, zero free parameters",
               float(m_der.group(1)), 1.4, 0.05, " %",
               # ONE pattern, on ONE line. The "derived ... residual ... N %"
               # form matched compare_log.py's own explanation of what this
               # residual does on the WRONG engine (48.1 %) -- which is the
               # subject of that paragraph and of CLAUDE.md mistake 12.
               patterns=[r"\b" + NUM + r"\s*%\s*(?:with\s+)?(?:the\s+)?"
                         r"(?:derived|zero fitted|with zero)"],
               files=ALL, dtol=0.05)
        # BOTH OF THESE SCAN THE DOCUMENTS NOW, and they did not on the first
        # pass -- they were `chk`s, so the value was read out of compare_log and
        # compared with a literal here, and no document was ever consulted.
        # AUDIT2.md M2-1 names exactly this: the script prints 0.839 and the
        # fitted k is written 0.837 in eleven places. Reading the script and
        # then not asking the documents is half of this file's job.
        figure("load residual, k FITTED, one free parameter",
               float(m_fit.group(2)), 1.1, 0.05, " %",
               patterns=[r"\b" + NUM + r"\s*%\s*(?:with\s+)?(?:the\s+)?"
                         r"(?:one fitted|fitted k|with the one)"],
               files=ALL, dtol=0.05)
        figure("fitted k, as compare_log prints it", float(m_fit.group(1)),
               0.839, 0.001,
               # The window must not step over the word "derived": CLAUDE.md
               # writes both constants in one sentence -- "1.4 % with zero
               # FITTED parameters (DERIVED k = 0.831), 1.1 % with the one
               # fitted k (0.837)" -- and a plain window reads the derived
               # constant as the fitted one.
               patterns=[r"[Ff]itted(?:(?!derived)[^\n]){0,26}?k"
                         r"(?:(?!derived)[^\n]){0,14}?\b(0\.\d{3})\b",
                         r"k,?\s*fitted[^\n]{0,22}?\b(0\.\d{3})\b"],
               files=ALL, dtol=0.001)
    else:
        chk("compare_log.py printed its residual block", False, True)

    # ---- the live app's pinned regression numbers --------------------------
    # AUDIT2.md C2-2. `app/test_replay.py` is the only place these exist, and
    # CLAUDE.md quotes the peak in three sentences that nothing compares against
    # it. They are NOT measurements -- the peak is a model output whose heat
    # capacity is assumed, and the alert counts are a property of thresholds
    # this project chose. They are pinned so a regression is visible, and the
    # documents that repeat them have to move when the pin does.
    chk("app peak 7475b5d7 (MODEL OUTPUT; a pin, not a run of the suite)",
        float(TR.EXPECT_FULL["peak_turb_c"]), 890.6, 0.0, " C")
    chk("app peak pull01 (MODEL OUTPUT; a pin, not a run of the suite)",
        float(TR.EXPECT_FAST["peak_turb_c"]), 608.0, 0.0, " C")
    # The two drives' peaks are written identically, so the documents are
    # checked against BOTH pinned values at once -- see scan_allowed(). The word
    # TURBINE has to be in the sentence: `7475b5d7` is also the drive behind the
    # 45 C ambient, the 111 C oil peak and the 55-minute duration, and
    # "estimated turbine ... 850 C" is the trigger, not a peak.
    scan_allowed("app peak estimated turbine (either pinned drive)",
                 [float(TR.EXPECT_FULL["peak_turb_c"]),
                  float(TR.EXPECT_FAST["peak_turb_c"])],
                 [r"(?:peak\s+)?estimated turbine[^.\n|]{0,30}?\*{0,2}" + NUM
                  + r"\s*\*{0,2}\s*\u00b0?\s*C\b(?!\s*trigger)",
                  r"7475b5d7[^.\n|]{0,34}?turbine[^.\n|]{0,26}?\*{0,2}" + NUM
                  + r"\s*\*{0,2}\s*\u00b0?\s*C\b(?!\s*trigger)"],
                 ALL)

    # THE TRIO IS THE ANCHOR. Documents always write these three together --
    # "13 thermal / 0 mismatch / 19 novel" -- and a bare "N thermal" also reads
    # pull01's 1 thermal and 4 novel, which are correct figures for that drive.
    figure("app thermal alerts on 7475b5d7 (a THRESHOLD CHOICE)",
           int(TR.EXPECT_FULL["thermal"]), 15, 0,
           patterns=[r"\b" + NUM + r"\s+thermal\s*[/\u00b7]\s*\d+\s+mismatch"],
           files=ALL)
    # The third leg of the trio. The comment above says "documents always write
    # these three together" and then only two of the three were ever captured:
    # the thermal pattern swallowed the mismatch count as bare context and the
    # novel pattern used it as a literal anchor, so a document could say
    # "15 thermal / 3 mismatch / 19 novel" and pass.
    figure("app mismatch alerts on 7475b5d7", int(TR.EXPECT_FULL["mismatch"]), 0,
           patterns=[r"thermal\s*[/·]\s*" + NUM + r"\s+mismatch\b"],
           files=ALL)
    figure("app novel-operating-point alerts on 7475b5d7",
           int(TR.EXPECT_FULL["novel"]), 19, 0,
           patterns=[r"mismatch\s*[/·]\s*" + NUM + r"\s+novel\b"], files=ALL)

    # ---- the replay coverage figure ----------------------------------------
    # 36 seconds above the trigger in 292.0 replayed minutes. Both inputs are
    # pinned prose from CLAUDE.md's ten-drive replay table, NOT recomputed here
    # -- replaying ten drives takes an hour. So this asserts the ARITHMETIC and
    # the documents' agreement with it, and says so rather than implying more.
    #
    # THE THIRD DECIMAL IS NOT DETERMINED BY THOSE INPUTS, and the tolerance
    # says so instead of hiding it. 36 / (292.0 x 60) is 0.2055 %, which rounds
    # to 0.205; the documents say 0.206, which is what 36 s over 291.4 minutes
    # gives. Both are consistent with prose rounded to one decimal minute, so
    # pinning either to three decimals would be false precision -- the check is
    # sized to catch a drift (0.206 -> 0.306 was one of the audit's injected
    # ones) and not to adjudicate the last digit.
    figure("fraction of replayed time above the trigger "
           "(36 s / 292.0 min, both pinned prose; last digit undetermined)",
           round(100.0 * 36.0 / (292.0 * 60.0), 3), 0.205, 0.002, " %",
           # "N % of ... trigger" reached across a wrapped line into a grade
           # table and into "80 % of the run". Require the claim's own words.
           # The capture requires a DECIMAL POINT. This figure is always written
           # to three places (0.206 %, 0.351 %); an integer percentage in the
           # same sentence is a grade or a duty cycle, and "12 % maximum for
           # 80 % of the run" was being read as a drifted 0.205.
           # FIVE FORMS, because the three written first matched none of the
           # three places CLAUDE.md actually states this figure, and the
           # acceptance test reported the row MISSED. The repository writes it
           # as a table cell ("36 s = 0.206 %"), as a sentence opener ("0.206 %
           # is itself a result about H/tau") and as a comparison ("0.351 % over
           # 172.6 minutes to 0.206 % over 292.0 minutes").
           # Three forms, kept because each one matches somewhere. Two more were
           # written and deleted the same hour: "N % above the trigger" and
           # "N % of replayed" match nothing in this repository, and the
           # per-pattern rot warning is what said so.
           patterns=[r"above the (?:trigger|limit)[^.\n]{0,26}?\b(\d+\.\d+)\s*%",
                     r"\b\d+\s*s\s*=\s*\*{0,2}(\d+\.\d+)\s*\*{0,2}\s*%",
                     r"\*{0,2}(\d+\.\d+)\s*%\*{0,2}\s+over\s+\d+\.\d+\s*(?:min|replayed)"],
           files=ALL, dtol=0.002)


def check_retired(here):
    """Fail if any document still quotes a figure this project has retired.

    AUDIT2.md C2-3 and M2-7d: this used to glob `**/*.md` plus ROOT-LEVEL
    `*.py`, so `app/*.py`, every `.html` and `presentation/*.js` were outside
    it -- which is why the examiner-facing deck could carry the void premise
    set on a hundred lines under a green run. It reads `tracked_files()` now,
    the same list the figure scan reads.
    """
    print("\nRETIRED FIGURES  (mistake 11 -- the old value must not survive)")
    docs = [f for f in tracked_files(here)
            if os.path.basename(f) not in RETIRED_EXEMPT
            and not f.startswith(RETIRED_EXEMPT_DIRS)
            and os.path.basename(f) != os.path.basename(__file__)]

    found, n_marked = [], 0
    for rel in docs:
        path = os.path.join(here, rel)
        raw, block = read_lines(path)
        is_md = path.endswith(".md")
        for n, line in enumerate(block, 1):
            for pat, was, now in RETIRED:
                if re.search(pat, line):
                    if _paragraph_is_historical(block, n, is_md, rel=rel):
                        n_marked += 1
                        EXEMPTED[rel] = EXEMPTED.get(rel, 0) + 1
                    elif _known_stale(rel, was, (rel, n, was)):
                        pass
                    else:
                        found.append((rel, n, was, now))

    for rel, n, was, now in found:
        print(f"  WRONG  {rel}:{n}  still quotes {was}  -> should be {now}")
    RESULTS.append(not found)
    if found:
        # AUDIT2.md M2-7e: every document drift used to collapse into the
        # single line "1 of 38 checks failed", so a run that found one stale
        # figure and a run that found ninety read identically.
        by_file = {}
        for rel, _n, _was, _now in found:
            by_file[rel] = by_file.get(rel, 0) + 1
        print(f"  {len(found)} live retired-figure mention(s) in "
              f"{len(by_file)} file(s): "
              + ", ".join(f"{k} x{v}" for k, v in sorted(by_file.items())))
    else:
        print(f"  ok     none of the {len(RETIRED)} retired figures appear as a "
              f"live claim in {len(docs)} tracked files")
        print(f"         ({n_marked} historical mentions marked {RETIRED_OK})")


def report_exemptions():
    """Print how much of each file a RETIRED-OK marker switched off.

    AUDIT2.md H2-6 asked for exactly this line and it is the point of the whole
    mechanism: an exemption nobody can see is indistinguishable from a check
    that does not exist. The measured figures that prompted it were README.md
    267 lines of 522 and CHECKPOINT.md 251 of 1101 -- half the public README,
    exempted by a marker whose scope nobody had counted.
    """
    if not EXEMPTED and not BARE_MARKERS:
        return
    print("\nEXEMPTIONS  (what RETIRED-OK switched off, and where)")
    for rel in sorted(set(EXEMPTED) | set(BARE_MARKERS)):
        n_fig = EXEMPTED.get(rel, 0)
        n_bare = BARE_MARKERS.get(rel, 0)
        print(f"  note   {rel:<44} {n_fig:>4} mention(s) excused"
              + (f", {n_bare} by a marker naming no figure" if n_bare else ""))
    total_bare = sum(BARE_MARKERS.values())
    if total_bare:
        print(f"  A marker that names no figure can only excuse the RETIRED scan, "
              f"never the\n  comparison against live data (H2-6). {total_bare} "
              f"such mention(s) this run; annotate\n  them "
              f"'{RETIRED_OK}: <figures>' as they are touched.")


def _console_safe(text):
    """Drop characters a Windows console cannot encode.

    This function exists because this checker CRASHED on the very failure it
    was written to report. `report_documents` echoes the offending line back,
    and CHECKPOINT.md line 54 contains a tick emoji, so on a cp1252 console
    printing the finding raised UnicodeEncodeError and took the whole run down
    -- after every check had already been computed correctly.

    That is precisely the bug CLAUDE.md records against build_dataset.py: "the
    character is the bug, not the data". A checker that dies while reporting is
    worse than one that stays quiet, because the traceback looks like a data
    problem and hides the real finding underneath it.
    """
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    try:
        text.encode(enc)
        return text
    except (UnicodeEncodeError, LookupError):
        return text.encode(enc, errors="replace").decode(enc, errors="replace")


def report_documents():
    """Print the result of the document scan -- the 11 September rework."""
    print("\nDOCUMENTS vs DATA  (every figure above, as the documents state it)")
    for rel, n, label, got, want, line in DOC_FAILURES:
        print(f"  WRONG  {rel}:{n}")
        print(f"         says {got!r} for '{label}', data gives {want!r}")
        print(_console_safe(f"         | {line}"))
    RESULTS.append(not DOC_FAILURES)
    if not DOC_FAILURES:
        print(f"  ok     {DOC_HITS} figure mentions across {len(ALL)} "
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
# AUDIT2.md C2-2: `ALL` was the 15-name TRACKED_DOCS list. It is now every
# tracked document, so `ABSTRACT.md`, `CONTROL_SCOPE.md`, `results/`, `DOC/`,
# `team/`, `presentation/plan.html` and `presentation/data.js` -- each of which
# the audit found carrying a wrong figure -- are inside the scan by default
# rather than by somebody remembering to add them.
ALL = [f for f in tracked_files(HERE)
       if os.path.basename(f) not in RETIRED_EXEMPT
       and not f.startswith(RETIRED_EXEMPT_DIRS)
       and os.path.basename(f) != os.path.basename(__file__)]
ENV = ["engine_env.py"]


def main():
    here = HERE
    S = pd.read_csv(os.path.join(here, "data/master_samples.csv"))
    M = pd.read_csv(os.path.join(here, "data/manifest.csv"))
    P = pd.read_csv(os.path.join(here, "data/master_points.csv"))

    print("\nDATASET SIZE  (CLAUDE.md, validation_table.md B)")
    # 168.1 over eight drives until 14 September, when pull01 -- the ninth,
    # the purpose-built 7-channel drive of mistake 13b -- joined logs/raw/.
    # It adds 7.5 minutes and ZERO samples and ZERO operating points, by
    # design: it carries no coolant channel, so the warm filter excludes it.
    figure("total minutes", round(float(M.duration_min.sum()), 1), 295.0, 0.15,
           " min",
           # Anchored to a DATASET-SCALE drive count. validation_table.md says
           # "three drives (80 minutes)" about the thermal fit, which is a
           # different quantity; a looser pattern reports it as a wrong total.
           # `(?<!adds )` because CLAUDE.md's "`pull01` adds 7.5 minutes and zero
           # samples" wraps onto the line below "...rest on eight drives of
           # samples:", and the joined window then reads 7.5 as the pooled
           # total. It is a CORRECT sentence about one drive's contribution.
           # THE DRIVE ALTERNATION INCLUDES THE CURRENT COUNT, and until
           # 21 September it did not. It ran `6|7|8|six|seven|eight`, written
           # when eight was the total, so every one of CLAUDE.md's five LIVE
           # "295.0 minutes ... ten drives" sentences matched nothing and the
           # figure the whole dataset rests on was unguarded in the file that
           # matters most. AUDIT2.md M2-7(a); it was also one of two rows the
           # acceptance test still reported MISSED.
           #
           # Keep the old numbers in the alternation: a sentence that says
           # "eight drives, 295.0 minutes" is wrong in a way worth catching.
           patterns=[r"(?<!adds )" + NUM + r"\s*min(?:ute)?s?\b[^.\n]{0,30}?"
                     r"(?:pooled|dataset|manifest|"
                     r"\b(?:6|7|8|9|10|six|seven|eight|nine|ten)\b\s*drives)",
                     r"\b(?:6|7|8|9|10|six|seven|eight|nine|ten)\s+drives"
                     r"[^.\n]{0,30}?(?<!adds )\b" + NUM + r"\s*min(?:ute)?s?\b"],
           files=ALL, dtol=0.15)
    figure("drives in the manifest", len(M), 10, 0,
           patterns=[WORDNUM + r"\s+drives,?\s+(?:and\s+)?\d+(?:\.\d+)?\s*min",
                     r"\d+(?:\.\d+)?\s*min(?:ute)?s?\s+(?:over|across|pooled across)\s+"
                     + WORDNUM + r"\s+drives"],
           files=ALL)
    figure("drives that carry samples", S.source.nunique(), 7, 0,
           # The number must be the SUBJECT of 'carry'. Without the lookbehind,
           # 'Six of the nine drives carry usable samples' -- a correct sentence
           # -- reports nine. A false positive of exactly the kind AUDIT.md H2
           # and M15 name: the patterns are the weak half of this checker.
           patterns=[r"(?<!of the )" + WORDNUM + r"\s+carrying\b",
                     r"(?<!of the )" + WORDNUM + r"\s+(?:drives\s+)?carry\b"],
           files=ALL)
    # AUDIT.md H7: 22 was a property of FILE ORDER. The greedy
    # first-match merge ran over glob order and gave 20-23 points
    # under shuffles. Windows are sorted before merging now, so
    # the count is a property of the data: 23, stable in 8 orders.
    figure("distinct operating points", len(P), 26, 0,
           patterns=[WORDNUM + r"\s+distinct operating points",
                     WORDNUM + r"\s+pooled points"],
           files=ALL)
    chk("every point spans a real 60 s window",
        bool((P.t_span.between(48, 72)).all()), True)
    chk("no point straddles a logger gap",
        # AUDIT.md H7: this used to read an AVERAGED max_gap (0.453 s).
        # max_gap is a worst case and averaging it hid the true member
        # maximum of 0.481 s. It carries the maximum now, so this is a
        # real bound rather than a mean wearing the word 'max'.
        round(float(P.max_gap.max()), 2), 0.48, 0.02, " s")
    figure("operating-point span, low end", round(float(P.map_kpa.min())), 30, 0.6,
           " kPa",
           # "validated/covers/sit at", NOT "spanning": engine_env's spark fit
           # legitimately spans 43-79 kPa over its own 11 points.
           patterns=[r"(?:validation|covers|sit at)[^.\n]{0,26}?\b" + NUM
                     + r"\s*[-\u2013]\s*\d+\s*kPa"],
           files=ALL, dtol=0.6)
    figure("operating-point span, high end", round(float(P.map_kpa.max())), 75, 0.6,
           " kPa",
           patterns=[r"(?:validation|covers|sit at)[^.\n]{0,26}?\b\d+"
                     r"\s*[-\u2013]\s*" + NUM + r"\s*kPa"],
           files=ALL, dtol=0.6)

    print("\nMAF SATURATION  (CLAUDE.md mistake 7)")
    figure("samples pinned at the 1020 kg/h ceiling", int(S.maf_pinned.sum()), 547, 0,
           patterns=[r"(?:1020(?:\.0)?\s*kg/h|ceiling|pinned)[^.\n]{0,70}?\b" + NUM
                     + r"\s+samples",
                     NUM + r"\s+samples[^.\n]{0,50}?(?:pinned|ceiling|1020)"],
           files=ALL)
    # Counted over the SAME population as the 517 above -- the warm-filtered
    # dataset -- because the two numbers are quoted in one sentence and must
    # describe one set of samples.
    #
    # This used to count raw files in logs/raw/ instead, and `pull01` broke it
    # on 14 September: that drive does hit the ceiling 56 times in its raw log,
    # so the raw count became 6 while the sample count stayed 517 across 5. Both
    # were true and the sentence built from them was not. pull01 carries no
    # coolant channel, so the warm-sample filter excludes it outright and it
    # contributes zero samples by design (CLAUDE.md mistake 13b) -- exactly the
    # behaviour a purpose-built drive is supposed to have.
    #
    # The raw-log figure, for the record: 573 pinned samples across 6 of the
    # 9 drives; 517 across 5 once the warm filter has run.
    hits = int(S.loc[S.maf_pinned.astype(bool), "source"].nunique())
    figure("drives showing that exact ceiling", hits, 6, 0,
           patterns=[WORDNUM + r"\s+separate\s+drives",
                     r"1020\s*kg/h on\s+" + WORDNUM + r"\s+drives"],
           files=ALL)

    print("\nCOMPRESSOR ENVELOPE  (validation_table.md D)")
    st = S[S.stable == 1]
    figure("quasi-steady samples behind the fit", len(st), 74013, 0,
           patterns=[NUM + r"\s+quasi-steady",
                     r"refitted[^.\n]{0,30}?on\s+" + NUM],
           files=ALL)
    # AUDIT.md L13: the upper bound used to be 3.0, so a future drive reaching
    # a HIGHER pressure ratio would be silently excluded from "highest pressure
    # ratio observed" -- the check would keep reporting the old maximum and
    # pass. The filter is there to drop decode garbage, so the ceiling is now
    # well clear of anything physical and a violation is reported, not dropped.
    f = st[np.isfinite(st.corr_flow) & np.isfinite(st.press_ratio)
           & (st.corr_flow > 0.01) & st.press_ratio.between(0.8, 6.0)]
    _above = int((st.press_ratio > 6.0).sum())
    if _above:
        print(f"  note   {_above} sample(s) above a pressure ratio of 6.0 were "
              f"excluded as implausible -- check the decode")
    figure("highest pressure ratio observed", round(float(f.press_ratio.max()), 2),
           2.52, 0.005,
           patterns=[r"highest pressure ratio[^\n]{0,24}?" + NUM],
           files=ALL, dtol=0.005)

    print("\nENRICHMENT v4  (engine_env.BaselineECU.base_lambda)")
    S2 = dwell_column(S)
    h = S2[(S2.map_kpa > 180) & S2.lam.between(0.5, 1.3)]
    bands = ((1000, 3500, 441), (3500, 4500, 235), (4500, 7000, 665))
    for lo, hi, claim in bands:
        figure(f"samples, {lo}-{hi} rpm above 180 kPa",
               int(((h.rpm > lo) & (h.rpm <= hi)).sum()), claim, 0,
               # A TABLE ROW, anchored at line start. Prose that mentions an rpm
               # band and a lambda value is a different claim.
               patterns=[rf"^\s*\|?\s*{lo}\s*[-\u2013]\s*{hi}\b[^\n]*?\s" + NUM
                         + r"\s*\|?\s*$"],
               files=ALL)
    hh = S2[(S2.map_kpa > 207) & S2.lam.between(0.5, 1.3)]
    # AUDIT.md H3: seconds from the timestamps, not rows over an assumed 4.6 Hz.
    # dwell_column re-indexes per drive, so this uses the carried column rather
    # than indexing by label -- duplicate labels across drives would multiply
    # the sum (measured: 731 s instead of 164).
    _secs = float(hh["dt_s"].sum())
    figure("seconds above 207 kPa", round(_secs), 208, 2, " s",
           # Only the "took that to N seconds" claim. "fitted to 17 seconds" and
           # "spanned 42.8 to 73.7 seconds" are different quantities.
           patterns=[r"took that to\s*\*{0,2}" + NUM + r"\s*\*{0,2}\s*seconds",
                     NUM + r"\s*s(?:econds)?\b[^.\n]{0,30}?above 207"],
           files=ALL, dtol=1)
    v = h[["lam", "rpm", "air_gps", "dwell", "map_kpa"]].dropna()
    CORR = (("rpm", -0.47, [r"engine speed\)\s*" + NUM, r"speed\s*\(" + NUM + r"\)"]),
            ("air_gps", -0.41, [r"air mass flow\)\s*" + NUM,
                                r"air mass flow \(" + NUM + r"\)"]),
            # AUDIT.md H3: -0.47 was measured on a dwell axis built from
            # row counts over an assumed 4.6 Hz. On real timestamps: -0.41.
            ("dwell", -0.44, [r"dwell[^)\n]{0,32}\)\s*" + NUM,
                              r"dwell \(" + NUM + r"\)"]),
            ("map_kpa", +0.11, [r"MANIFOLD PRESSURE\)\s*" + NUM,
                                r"corr\(.{0,18}MAP.{0,6}\)\s*(?:is\s*)?" + NUM,
                                r"manifold\s+pressure is\s*\*{0,2}" + NUM]))
    # AUDIT.md H4: report the INDEPENDENT reading count beside the row count,
    # because a correlation quoted to two decimals on 1150 forward-filled rows
    # actually rests on of order 70 readings.
    from build_dataset import fresh_readings
    _n_rows = len(v)
    _n_fresh = min(fresh_readings(h, "lam"), fresh_readings(h, "air_gps"))
    import math as _math
    _se = 1.0 / _math.sqrt(max(_n_fresh - 3, 1))
    print(f"  note   these correlations rest on {_n_rows} forward-filled rows but "
          f"only ~{_n_fresh} independent readings")
    print(f"         standard error is about {_se:.2f}, so do NOT read them to two "
          f"decimals (AUDIT.md H4)")

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
    figure("hottest oil anywhere in the logs", round(float(S.oil_c.max())), 117, 0.5,
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
    figure("derived k = 269.6 / T_charge, mean over the 26 points",
           round(float(np.mean(din / t_ch)), 3), 0.831, 0.002,
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
    chk("boosted model samples (gate >200 kPa)", len(hi), 762)
    chk("logged boost readings behind the comparison", len(logged), 1097)
    gap = 100.0 * (hi.map_kpa.median() - np.median(logged)) / np.median(logged)
    figure("boosted model vs the car's own boost channel",
           round(float(gap), 1), 1.9, 0.4, " %  (was +23.7 with the sensor)",
           patterns=[r"charge_temperature\(\)[^\n]*?\|[^\n|]*?\|\s*\*{0,2}"
                     + NUM + r"\s*%"],
           files=ALL, dtol=0.4)

    print("\nBASELINE ECU CONSTANTS  (engine_env.py)")
    figure("ENR_LOAD, the enrichment gate", 180.0, 180.0, 0.0, " kPa",
           patterns=[r"ENR_LOAD\s*=\s*" + NUM], files=ENV)

    # check_simulation() must run BEFORE report_documents(), or its
    # DOC_FAILURES are appended after the report has already been
    # printed and its RESULTS entry recorded -- computed, then thrown
    # away. Found by re-running the auditor's own drift test and
    # watching it pass with the drift injected.
    check_simulation(here)
    check_scenario(here)
    report_documents()
    check_retired(here)
    check_pinned_history(here)
    report_known_stale()
    report_exemptions()

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
