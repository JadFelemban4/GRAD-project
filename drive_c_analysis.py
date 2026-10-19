"""drive_c_analysis.py -- drive C's agreed decision rule, as one script, blind by construction.

    python drive_c_analysis.py stage-a --c2 <csv...> [--c1 <csv...>] [--out results/drive_c]
    python drive_c_analysis.py stage-b [--out results/drive_c] [--logs DIR]
    python drive_c_analysis.py stage-c --frozen results/drive_c/frozen.json
                                       --hash results/drive_c/frozen.sha256 [--logs DIR]
    python drive_c_analysis.py dry-run-spark

Written 19 October 2026, the day Jad and Ghassan agreed drive C's rule
(results/DRIVE_C_RULE.md; decisions 14-23 of results/VALIDATION_DECISIONS.md),
and committed before the repeat drive, as the rule's preamble asks. Nothing here
was tuned on a drive C log: none had been read when it was written, its stages B
and C were exercised on synthetic logs only (test_drive_c_analysis.py), and stage
A only on drive B, which logs no ignition angle. The rule is the specification;
where this file and the rule disagree, the rule wins and this file is wrong.
Revised the same day after three independent reviews (fidelity, blindness and
robustness, statistics), still before any drive C log was read: IC36-IC41 are
new; IC1, IC7, IC10, IC13, IC15-IC19, IC21, IC22, IC24, IC26-IC28, IC30 and IC33
changed; every behavioural fix has its regression test.

WHY THREE STAGES. The rule must stay blind until it has run (its guard 4):

  stage A  reads ONLY Time, engine speed, air mass, coolant and ambient: the
           ignition columns are never loaded (read_csv's usecols names the four
           blind columns by index; the header line alone gives every column's
           poll position). The file's bytes pass once through SHA-256, which
           reveals no value, so the later stages can refuse a changed file. It
           finds every load step (item 1), scores V1-V8, the sham anchors, the C1
           segments (section 4), the provisional blocks, and chooses item 8's cell
           from blind counts. -> stage_a.json
  stage B  runs only on the committed script (IC39). It recomputes stage A from
           the logs and refuses a stage_a.json that differs (IC33), then reads the
           two ignition columns as TEXT. Only cells inside the step and sham
           pre-windows P are ever converted to numbers, and none of those rows may
           lie in a response window (IC36: it refuses before converting anything if
           one does); every other cell stays NaN, so no arithmetic can touch it
           (asserted). Elsewhere it counts pairs by poll position: which rows were
           polled, from the phase and the header, and whether the cell holds text at
           all. It computes B and n_B, the realised blocks, the cuts
           (drive_c_rule_numbers.cuts, imported, never copied) and writes the
           frozen list with its SHA-256. -> frozen.json, frozen.sha256
  stage C  refuses unless the frozen list's SHA-256 equals the committed hash
           file, both are tracked by git and unchanged against HEAD, the script is
           committed and is the code that froze the list, the plant is X1's, every
           log is the file that was frozen, no stage C has run on any of them, the
           list holds at least 16 valid primary steps, and stages A and B
           recomputed from the logs give the frozen list back. Then it marks its
           folder (guard 5), reads the response windows, once, writes the result
           beside the frozen list and only then shows it.
           -> DRIVE_C_RESULT.json and .txt
  dry-run-spark  the legacy check item 8 asks for first: -3.81 / 2.07 and -1.78
           on car_spark_boost.py's committed readings (car spark minus model
           spark under boost, already published).

Every stage asserts plant_sha 3c48890dd15bc116 and derived_sha 326c0835548975e2
(X1's plant: results/PREREGISTRATION_X1.md, x2_score.py) before anything else.

IMPLEMENTATION CHOICES, FIXED BEFORE DATA (19 October 2026). The rule leaves the
details below open. Each is the reading that can only add a miss, an exclusion,
"inconclusive" or "untested", never a pull or a retune, unless it says otherwise;
the clause it reads is named first. Where the rule's own text settles a point the
first draft of this file had read otherwise (IC13, IC17, IC40), the text is
followed and the entry says so.

  IC1  D1 "estimated per run between logger breaks": a break is a row gap above
       3x the file's median row interval, or a time that does not increase
       (mistake 8's logger-gap measure), or a persistent change of the
       round-robin phase (9 of the next 10 single-change rows on a new phase: a
       dropped row shifts every later poll and leaves no time gap). The rows
       between the old phase's last single-change row and the new one's first
       form a run of their own, flagged. A pair, a step, a sham or a segment
       never spans a break, and stage B's rows are built run by run (a time that
       resets never widens a pre-window into another run).
  IC2  D1, the phase: estimated from the four channels stage A may read; the
       ignition channels' poll rows follow from it and the header, so the phase
       never needs an ignition value. A run with fewer than 20 single-change rows
       is flagged like one under 99 %.
  IC3  D1, a flagged run: value changes give the four blind channels' readings
       there, but its steps, shams and segments are excluded (reason D1): their
       ignition readings could only be found from value changes, which stage B
       cannot see blind.
  IC4  D1, placeholders and blanks: an ignition cell is a reading only if it holds
       text; a leading placeholder is a zero literal before the channel's first
       non-zero cell, found from the text without converting any angle. Stage C
       also drops a cell whose text is not a number.
  IC5  D1, ranges: the rule gives none for the angles; any finite value at a poll
       row is a reading (the 12 deg unreadable rule bounds what can decide).
  IC6  D2 / V8, "polled 1-2 rows after": the poll lag (target position - actual
       position) mod N, the number of channels, is 1 or 2.
  IC7  D3: angles are compared with the rule's thresholds exactly. Every reading is
       a count of 0.75 deg, exact in binary floating point, so a tolerance could
       only turn a near miss into a pull (or a near quiet pair into a quiet one).
       Times carry a 1e-6 s tolerance for float error only (the logs' times have
       1 ms resolution). No value is rounded to the grid.
  IC8  D4: coolant and ambient are interpolated between genuine readings like
       engine speed and air mass; outside a channel's first and last reading in
       the run there is no value, so nothing is extrapolated.
  IC9  D5: MAP_pre is inverted from the pre-window medians of air (= M), engine
       speed, ambient and coolant; T_ch and T_cool for KI1 are the pre-window
       medians; the spark is clipped to BaselineECU's limits, as its step() does.
  IC10 item 1: a departure without a trigger or a confirmation is no step, and
       scanning resumes at the next reading; with no fall before the run ends,
       tau_(f-1) is the run's last air reading. "Scanning resumes at" reading j
       means j is the next departure candidate k. A departure whose t0 lies before
       the previous step's fall (or after a step that never fell) is kept and
       flagged a re-detection: the previous roll-on found again, scanned while
       still held after the 10 s resumption, or rising again from a wobble the
       fall rule read as a fall. IC36 fails every re-detection on V3. On drive B
       (no ignition channel) the detector finds 36 departures: 22 first
       detections, 12 of them in a held gear with a held step (V4, V5), the
       rule's twelve held-gear roll-ons; and 14 re-detections, 5 of them of
       held-gear roll-ons, which the rule's "each once" does not mention. None
       can count.
  IC11 V1 / V3 / V6: V1's speed test needs a genuine engine-speed reading in the
       pre-window; V3 fails when the 40 s before t0 begin before the run (the
       spacing cannot be seen); "ambient was logged" needs a genuine ambient
       reading in the pre-window.
  IC12 V4: a gear flag counts if its pair of engine-speed readings overlaps
       [t0 - 20 s, t_W] at all, the pairs straddling either end included.
  IC13 V7, the rule's text: "a pinned air reading counts as high". A step whose
       first genuine air reading after t1 is pinned (>= 1019.9 kg/h, mistake 7)
       is in the primary set whatever the KI1 computed from that reading, which is
       flagged as a lower bound (on X1's plant it is 17-48 at 1500-2600 rpm from a
       60 kg/h cruise, so the text and the value agree). A KI1 that cannot be computed leaves the
       step out.
  IC14 stage B, n_B: every stage-A-valid primary step with at least 10
       pre-window pairs whose B is outside +-0.75 deg, whatever its late-window
       count (the wider count is the stricter robustness test); the side set gets
       B and counts too, for the report.
  IC15 item 3: "any (retard - B) above 12 deg" is read over L, where the step is
       read (no reading is conservative in both directions here: E holds the
       pairing artefacts the rule keeps out of the verdict). A frozen-valid step
       whose late window holds fewer than 3 genuine pairs in stage C (a cell the
       positional count could not see was blank or not a number) is unreadable
       too, and counts toward the 1-in-4 rule.
  IC16 item 4, after unreadable steps leave: "pulls" needs K at or above the
       larger of the frozen cut and the cut for the blocks that remain, "does
       not" K at or below the smaller (likewise for the n_B cut, on the blocks
       frozen for N + n_B); fewer than 16 readable steps leaves C2 untested.
  IC17 item 5, the rule's text: "below 16: untested, and stage C is not run". With
       fewer than 16 valid primary steps in the frozen list stage C refuses before
       reading anything beyond the pre-windows; C1 is not analysed either, and the
       single run of guard 5 is not spent: the shortfall is made up by more
       driving, then stages A and B again. (The first draft offered a flag to run
       C1 alone; the rule has no such case, and it is gone.)
  IC18 shams, anchors: anchor (a) is the first air reading >= 40 s after a step's
       fall, in that step's run; a step with no fall gives none. Anchor (b)'s
       excluded zone is (t0 - 25 s, tau_f + 50 s] for every step detected in the
       file, all runs ("any fall", "any step's t0"); the grid runs from the file's
       first row that has a time. An anchor (a) within 30 s of another anchor (a),
       and an anchor (b) within 30 s of an anchor (a), are dropped (no two shams
       closer than the grid; a re-detection shares its step's fall).
  IC19 shams, scoring: the window is (a, a + l], l the median late-window length
       of the stage-A-valid primary steps (4.0 s if there is none), fixed in
       stage A because the blind checks need it (no reading is conservative in
       both directions; this one is fixed blind); "no air reading above 1.3 M*
       across" covers (a - 40 s, a + l], V4 runs to a + l, and the window must end
       inside the run.
  IC20 shams, validity and counting: a sham needs >= 10 pre-window and >= 3
       window pairs, as a step does (a sham short of genuine pairs in stage C is
       not scored); an unreadable sham (above 12 deg) counts as a sham pull;
       fewer than 24 scored shams makes any C2 verdict inconclusive (shams),
       "does not" included.
  IC21 blocks: the 5-minute breaks are found over every stage-A-valid step,
       primary or side set, whether or not it passed stage B (driving a step is
       driving, whatever its set), and only the steps the count is for are
       counted: the valid primary steps, or for the n_B test those and the steps
       excluded for B. Merging blocks can only make the cuts stricter. A step with
       no fall uses its run's last air reading as its fall; a new file is a new
       block.
  IC22 step-specific comparison: the C1 window is the first n in-band pairs at
       tau >= s0 + 10 s of a counting segment, n the rounded-up median late-window
       pair count of the valid steps (frozen); its baseline is min(0, the lower
       median of the valid steps' B) (no reading is conservative in both
       directions: this one leans toward remedy (b), the rule's default); a C1
       window with any value at or above 2.25 deg (above 12 included) counts as a
       C1 pull; a C2 step is on its side if its late window holds an in-band pair;
       the median ambients are the in-band steps' pre-window medians and the
       windowed segments' medians.
  IC23 remedy (d): "L says no" is the verdict "does not"; an early pull is
       2.25 deg <= max over E of (retard - B) <= 12 deg.
  IC24 item 6b, the ambient secondary the rule names but does not define: the
       steps split at their median pre-window ambient (ties cool), one-sided
       Fisher (warm pulls more often); Holm over the two secondaries (IC41).
  IC25 section 4, segments: a segment ends at its first fall or at the last
       reading of its run of qualifying readings, whichever comes first, minus
       0.6 s; readings after a fall inside the run start no new segment; a
       reading carries a gear flag if a flagged engine-speed pair spans its time;
       a reading needs ambient to be inverted; only counting segments (>= 7 s
       after s0) enter items 7 and 8 and the step-specific comparison.
  IC26 item 7, the scan: "the first pair ... with retard >= B_seg + 2.25" is read
       literally. The pairs at <= 3300 rpm are scanned in time order from
       s0 + 5 s, and the first candidate ends the scan, confirmed or not: an
       unconfirmed one leaves the segment with no confirmed onset, never skipped
       as jitter (skipping could only add onsets). A pair at >= 2.25 deg where no
       quiet window exists (fewer than 3 pairs, or one above 0.75 deg, in the
       10 s before it) also ends the scan (a retard arriving in two counts):
       confirmed, the segment is "retarded without a quiet baseline",
       (-inf, its KI], counted toward neither the 8 nor the channel check. The
       quiet baseline uses every in-segment pair in [max(s0, tau - 10 s), tau),
       and the confirming pairs are the next in-segment pairs at any speed.
  IC27 item 7, the intervals: "retarded from its first pairs" is a pair before
       s0 + 5 s (where no onset can be read) at <= 3300 rpm with retard
       >= 2.25 deg, confirmed by one of the next 2 pairs at >= 1.5 deg; its
       interval is (-inf, KI of that pair], the rule's (-inf, KI of its first
       in-cell pair] when it is the first. A segment with no confirmed onset is
       right-censored at the highest KI over its quiet pairs (retard <= 0.75 deg,
       <= 3300 rpm, anywhere from s0) before its first pair at >= 2.25 deg and
       before the pair that ended the scan: after a pull reading the engine may be
       knocking on a cylinder the channel does not show (m 0.45), so a later
       quiet reading is no evidence of quiet; the bound can only fall, never
       claim more. A pair's KI uses "that pair's TARGET angle", D2's
       min(target before, target after), the literal reading: where the target
       moves between its two reads the KI sits low by at most that move (under one
       count, about 0.04 KI, on a held segment), declared rather than corrected.
       An onset whose last quiet KI is not below K* gives the interval between the
       two values. A KI that cannot be computed (a pair outside a channel's
       readings) gives no interval, and such an onset counts neither toward the 8
       nor toward the channel check. No reading of these clauses moves the knee one
       way only (a narrower or a wider interval can shift the median either way);
       these are chosen because each interval contains the onset whenever the
       channel shows it, where the first draft's could exclude it. In the
       statistics review's simulation (true knee 0.80, 25 segments, 200 drives, one
       cylinder of six retarded) 59 % of the first draft's right-censored intervals
       lay above the car's first visible knock and none do now; the median of the
       medians moved 0.993 -> 0.875, identified on 20 % -> 84 % of drives (two
       cylinders: 0.893 -> 0.821; every cylinder: 0.800 -> 0.795). They keep the
       rule's estimator, which still reads high under partial knock: a high knee, or
       "onset above x", is no evidence that the car's knee is high.
  IC28 item 7, the median: interpolated inside its innermost Turnbull interval
       (mass spread evenly there). Where the EM's F comes within 0.001 of one half
       at the end of an innermost interval (a flat at one half, which the EM only
       approaches: up to about 2e-4 off at its stopping point), the median set is
       that interval, the gap and the next interval together, and the point is
       the gap's midpoint; beside an open interval the median is then not
       identified. A retune needs the whole median set beyond max(0.10, 2 u_val)
       on one side; a bootstrap resample whose median is not identified counts as
       -inf or +inf, so h is infinite and nothing retunes.
  IC29 item 7, the halves: a segment belongs to the half of the pair that sets
       its interval (2650 rpm is the lower half); if either half's median is not
       identified, the knee is limited, no retune.
  IC30 item 8: E per segment is the ordinary median; a session is one C1 file.
       One session: u_D = SD / sqrt(n_seg), the variance floored at the 0.75 deg
       grid's (0.75^2 / 12 per segment), so identical segment values do not give
       u_D = 0. Several sessions: E and u_D are DerSimonian-Laird random-effects
       values, each session's variance floored the same way, and a retune also
       needs the pooled mean of the segment values to call for it. The in-cell
       readings are genuine polls of the actual angle; the target is not needed.
  IC31 item 8, u_al: for each in-cell reading, the model schedule at the genuine
       engine-speed and air readings just before it and just after it; half the
       absolute difference; RMS over every in-cell reading of the counting
       segments.
  IC32 dry run: results/car_spark_boost.json's committed readings, with the
       model recomputed by this script's own schedule (model_spark); stage C
       computes no spark row unless it passes.
  IC33 the freeze and the single run (guards 4 and 5): every SHA-256 is over the
       bytes with CRLF turned to LF (this repository is core.autocrlf=true, as
       fingerprint._sha_files says); the frozen list carries the code hash of this
       script and of drive_c_rule_numbers.py (fingerprint._code_only: comments and
       docstrings do not count), and stage C refuses if either moved. Stage B
       recomputes stage A from the logs and refuses a stage_a.json that differs;
       stage C recomputes stages A and B (blind, and the pre-windows) and refuses
       a frozen list that differs, before it reads a response window: a list
       edited by hand is refused even with a new hash. Stage C always writes
       beside the frozen list it reads. Before its first response window it
       creates STAGE_C_STARTED.json there, exclusively, naming every log's
       SHA-256; it refuses if that folder holds a marker or a result, or if any
       marker or result under results/ names one of its logs (once on every drive
       C file, finished or not: a run that dies is not run again). Stages A and B
       refuse in a folder that holds either, and stage B also refuses logs that a
       marker under results/ names. The result is written before any of it is
       shown.
  IC34 stage C, the phase check: if an ignition channel's value changes fall on
       its predicted poll rows less than 99 % of the time in a run holding a
       valid step, sham or counting segment, C2 is inconclusive (poll phase), or
       the C1 rows untested (poll phase).
  IC35 stage B reads no C1 ignition value: guard 4 names the pre-windows only,
       and nothing the frozen list holds needs one (every C1 count in it is by
       poll position). Item 7's quiet baselines are computed in stage C.
  IC36 guard 4 against overlaps. Stage B reads every stage-A-valid pre-window, so
       none may hold a response window (a step's early and late windows, a valid
       sham's window). V3 is read as spacing from every other detected step: a
       step fails V3 when another detected step's span [t0', end'] (end' its fall,
       or its run's last air reading, never before its own windows end) meets
       (t0 - 40 s, t0]. The literal V3 compares air readings with 1.3 M, and M is
       lifted when the 20 s before t0 hold an earlier step still held (a
       re-detection) or held long; that step's late window would then be read
       into the next step's baseline. A sham fails V3 likewise over
       (a - 40 s, a + l], and fails P when its window lies in a stage-A-valid
       step's or sham's pre-window: under the rule's own plan (a full minute
       before each press) anchor (a) lands in the next press's pre-window. Stage B
       builds its rows run by run and refuses, before converting any value, if a
       pre-window still meets a response window. Steps and shams are removed
       only, from blind information.
  IC37 D2, "the target polled just before / just after": the target's own polls
       of the previous and of the same round-robin cycle, rows actual + lag - N
       and actual + lag (lag 1-2, V8). If either poll gave no genuine reading the
       pair is dropped: the next genuine target would be a cycle later, and a
       target dip between the two reads could create a pull.
  IC38 the logs' paths and form: a log inside the repository is recorded by its
       path relative to it (portable, no user folder committed), else by its
       absolute path; stages B and C look for it there, then by name in
       --logs DIR, and accept a file only if its SHA-256 is the recorded one (the
       SHA-256 is its identity, the path only where to look). A data row with a
       trailing delimiter reads as the header says (read_csv's index_col=False); a
       file that is not a UTF-8, comma-separated export is refused with that
       reason. Console output escapes what the console cannot encode.
  IC39 the code, guard 1 and duplicates: stages B and C run only when this script
       and drive_c_rule_numbers.py are tracked and unchanged against HEAD (the
       rule's preamble commits the script before the repeat drive); the commit is
       recorded beside the freeze and the result. Guard 1: a log holding either
       ignition column is refused inside logs/raw/ by every stage (move it out:
       its SHA-256 does not change); one holding neither (drive B, the smoke test)
       cannot leak an angle and is read. The same log under two names (identical
       SHA-256) is refused: its steps and segments would count twice.
  IC40 item 7's secondary, the rule's text "over all pairs": the logistic fit uses
       every in-segment pair of the counting segments with a computable KI, at
       any speed (the first draft kept only pairs at <= 3300 rpm); it decides
       nothing.
  IC41 item 6b, Holm over both secondaries always: a p that cannot be computed
       counts as a test that is not significant, so the family stays two and the
       other test still needs p <= 0.025.
"""
import argparse
import contextlib
import csv
import hashlib
import io
import json
import math
import os
import re
import subprocess
import sys
from datetime import datetime

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import drive_c_rule_numbers as RN  # noqa: E402  -- the cuts, imported, never copied

SCHEMA = 1
OUT_DEFAULT = os.path.join(HERE, "results", "drive_c")
RESULTS_ROOT = os.path.join(HERE, "results")      # IC33: where an earlier stage C is looked for
RAW_DIR = os.path.join(HERE, "logs", "raw")       # guard 1
MARKER, RESULT = "STAGE_C_STARTED.json", "DRIVE_C_RESULT.json"

# ---- the plant this rule was fixed on ----------------------------------------
PLANT_SHA = "3c48890dd15bc116"          # results/PREREGISTRATION_X1.md, x2_score.py
DERIVED_SHA = "326c0835548975e2"        # data/derived_params.json's values, same record

# ---- channels (matched case-insensitively) -------------------------------------
KEYS = {"rpm": "engine speed", "air": "air mass flow", "act": "actual ignition angle",
        "tgt": "target ignition angle from torque intervention",
        "cool": "coolant temperature", "amb": "ambient temperature"}
BLIND = ("rpm", "air", "cool", "amb")
IGN = ("act", "tgt")
IGN_NAMES = frozenset(KEYS[k] for k in IGN)
RANGE = {"rpm": (500.0, 7000.0), "air": (4.0, 1020.0),            # D1
         "cool": (40.0, 130.0), "amb": (2.0, 55.0)}
BREAK_X = 3.0                     # IC1
PHASE_LOOK, PHASE_AGREE = 10, 0.9          # IC1: a persistent phase change
PHASE_SHARE, PHASE_MIN_ROWS = 0.99, 20     # D1, IC2
PAIR_BEFORE_S = 1.25              # D2
COUNT = 0.75                      # D3
EPS = 1e-6                        # IC7: times only, in seconds; angles are compared exactly
PIN_KGH = 1019.9                  # mistake 7 (new_drive.MAF_CEILING_KGH)
GEAR_RATE = 0.17                  # D6, 1/s
COLD_K, COLD_DEG = 340.0, 5.0     # BaselineECU.step's cold retard

# ---- C2, item 1 and the validity table ----------------------------------------
MEDIAN_S, DEPART_X, TRIGGER_X, CONFIRM_ADD = 20.0, 1.2, 1.5, 25.0
FALL_DROP, FALL_X, RESUME_S = 0.85, 1.3, 10.0
V1_N, V1_LO, V1_HI, V1_RPM_RATIO, V1_RPM = 10, 0.7, 1.3, 1.05, (1400.0, 2600.0)
V2_M = 100.0
V3_S, V3_X = 40.0, 1.3
V5_X, V5_MIN_S = 1.3, 2.5
V6_COOL = 80.0
V7_PRIMARY, V7_SIDE = 1.0, 0.85
# ---- C2, items 2-6 -----------------------------------------------------------
P_S, L_START, L_MAX, GUARD_S = 20.0, 1.0, 5.0, 0.6
P_MIN_PAIRS, L_MIN_PAIRS, B_ABS = 10, 3, 0.75
PULL, UNREADABLE, UNREADABLE_SHARE = 2.25, 12.0, 0.25
BLOCK_GAP_S, ALPHA, CI_LEVEL = 300.0, 0.05, 0.90
Q_RULE, M_RULE, ICC_RULE = 0.075, 0.45, 0.10      # item 4's design values, passed to RN.cuts explicitly
N_MIN = 16
SHAM_A_S, SHAM_GRID_S, SHAM_B_FALL_S, SHAM_B_T0_S, SHAMS_MIN = 40.0, 30.0, 50.0, 25.0, 24
SHAM_L_DEFAULT = 4.0              # IC19
CHAN_ONSETS, CHAN_PERSIST, CONFIRM_DEG = 3, 2, 1.5
LARGE_KPA = 120.0
SS_START_S, SS_RPM, SS_MAP, SS_AMB_K, SS_MIN = 10.0, (2000.0, 3300.0), 160.0, 5.0, 10
# ---- C1, section 4 and items 7-8 ----------------------------------------------
SEG_MAP, SEG_RPM, SEG_AIR_MAX, SEG_COOL, SEG_SPOOL_S, SEG_MIN_S = 140.0, (2000.0, 3500.0), 1019.0, 80.0, 3.0, 7.0
ONSET_AFTER_S, ONSET_RPM_MAX, QUIET_S, QUIET_MIN, QUIET_MAX = 5.0, 3300.0, 10.0, 3, 0.75
KNEE, ECU_KNEE, R_K, U_INPUT_KI, ONSETS_MIN = 0.85, 1.0, 0.10, 0.032, 8
HALF_SPLIT, HALVES_MAX = 2650.0, 0.10
BOOT_N, BOOT_SEED = 2000, 20261019
TB_TOL = 1e-3                     # IC28: how close to 1/2 the EM's F must come to be read as a flat
CELL_PRIMARY = {"rpm": (2400.0, 3000.0), "map": (165.0, 185.0)}     # car_spark_boost.CLIMB
CELL_FALLBACK = {"rpm": (2000.0, 3500.0), "map": (160.0, 200.0)}
CELL_MIN_READINGS, SEGS_MIN = 5, 15
R_SPARK, PLAN_R_SPARK, U_CHARGE_DEG, RETUNE_KPA = 0.85, 1.3, 0.86, 140.0
LEGACY_EXPECT = (-3.81, 2.07, -1.78)
LEGACY_JSON = os.path.join(HERE, "results", "car_spark_boost.json")


# ==== small tools ==============================================================
def echo(s=""):
    """Print what the console can show: a character it cannot encode is escaped, never fatal
    (build_dataset.py's lambda and verify_docs.py's tick, CLAUDE.md mistake 16)."""
    enc = getattr(sys.stdout, "encoding", None) or "utf-8"
    print(str(s).encode(enc, "backslashreplace").decode(enc, "replace"), flush=True)


def say(lines, s=""):
    echo(s)
    lines.append(s)


def lower_median(x):
    """D3: the lower median, so a baseline is an observed value."""
    x = sorted(float(v) for v in x)
    return x[(len(x) - 1) // 2] if x else None


def clean(o):
    """JSON-safe: numpy scalars to Python, NaN to None, infinities to strings."""
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    if isinstance(o, np.ndarray):
        return [clean(v) for v in o.tolist()]
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        f = float(o)
        if math.isnan(f):
            return None
        if math.isinf(f):
            return "inf" if f > 0 else "-inf"
        return f
    return o


def sha256_file(path):
    """IC33: over the bytes with CRLF normalised to LF."""
    with open(path, "rb") as fh:
        raw = fh.read().replace(b"\r\n", b"\n")
    return hashlib.sha256(raw).hexdigest()


def code_sha():
    """IC33: the code of this script and of drive_c_rule_numbers.py, comments and
    docstrings removed (fingerprint._code_only)."""
    import fingerprint as F
    h = hashlib.sha256()
    for name in ("drive_c_analysis.py", "drive_c_rule_numbers.py"):
        with open(os.path.join(HERE, name), "rb") as fh:
            raw = fh.read().replace(b"\r\n", b"\n").decode("utf-8")
        code = F._code_only(raw)
        h.update((code if code is not None else raw).encode("utf-8"))
    return h.hexdigest()[:16]


def plant_check():
    """Guard 3: the plant this rule was fixed on, or nothing runs."""
    import fingerprint as F
    live = F._sha_files(F.PLANT_FILES)
    der = F.derived_sha()
    if live != PLANT_SHA or der != DERIVED_SHA:
        raise SystemExit(f"REFUSED: the live plant is plant_sha {live}, derived_sha {der}; drive C's "
                         f"rule was fixed on plant_sha {PLANT_SHA}, derived_sha {DERIVED_SHA} "
                         "(results/DRIVE_C_RULE.md, guard 3)")
    return {"plant_sha": live, "derived_sha": der}


# ==== the physics the rule names (D4, D5, item 8) ==============================
_ECU = []
_KI = {}


def ecu():
    if not _ECU:
        from engine_env import BaselineECU
        _ECU.append(BaselineECU())
    return _ECU[0]


def t_charge(amb_c, cool_c):
    import plant
    return plant.charge_temperature(amb_c + 273.15, cool_c + 273.15)


def inv_map(air_kgh, rpm, amb_c, cool_c):
    """D4: inverted MAP (mistake 2), as car_spark_boost.py and build_dataset.py."""
    import plant
    if not all(np.isfinite([air_kgh, rpm, amb_c, cool_c])) or rpm <= 0:
        return float("nan")
    return float(plant.map_from_airflow(air_kgh / 3.6, rpm, t_charge(amb_c, cool_c)))


def model_spark(rpm, map_kpa, amb_c, cool_c):
    """The model ECU's schedule with no knock retard: base_spark + the intake-temperature
    compensation at plant.charge_temperature, -5 deg below 340 K coolant, clipped as
    BaselineECU.step clips (car_spark_boost.model_spark, the same expression)."""
    if not all(np.isfinite([rpm, map_kpa, amb_c, cool_c])):
        return float("nan")
    e = ecu()
    s = e.base_spark(rpm, map_kpa) + e.iat_compensation(t_charge(amb_c, cool_c))
    if cool_c + 273.15 < COLD_K:
        s -= COLD_DEG
    return float(np.clip(s, e.SPARK_MIN, e.SPARK_MAX))


def knock_integral(rpm, map_kpa, amb_c, cool_c, spark):
    """plant.predict(...)["knock_integral"] at lambda 1, cached on its inputs."""
    import plant
    if not all(np.isfinite([rpm, map_kpa, amb_c, cool_c, spark])):
        return float("nan")
    key = (round(rpm, 3), round(map_kpa, 4), round(amb_c, 3), round(cool_c, 3), round(spark, 4))
    if key not in _KI:
        _KI[key] = float(plant.predict(rpm, map_kpa, t_charge(amb_c, cool_c), cool_c + 273.15,
                                       spark, 1.0)["knock_integral"])
    return _KI[key]


# ==== the logs (D1) ============================================================
NOT_EXPORT = "is not a UTF-8, comma-separated BimmerLink export (a Time column, then one column per channel)"


def read_header(path):
    try:
        with open(path, encoding="utf-8-sig", newline="") as fh:
            first = fh.readline()
    except UnicodeDecodeError:
        raise SystemExit(f"REFUSED: {os.path.basename(path)} {NOT_EXPORT}")
    return [h.strip() for h in next(csv.reader([first]))] if first.strip() else []


def is_under(path, folder):
    """True if path lies inside folder (any depth)."""
    a, b = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(folder))
    try:
        return os.path.commonpath([a, b]) == b
    except ValueError:            # another drive
        return False


def recorded_path(path):
    """IC38: the path written into stage_a.json and frozen.json, relative to the repository when the
    file lies inside it (portable, no user folder committed), else absolute."""
    p = os.path.abspath(path)
    return os.path.relpath(p, HERE).replace(os.sep, "/") if is_under(p, HERE) else p


class LogFile:
    """One BimmerLink export: its header, every channel's poll position, V8."""

    def __init__(self, path, role):
        self.path = os.path.abspath(path)
        self.role = role
        self.name = os.path.basename(path)
        self.header = read_header(self.path)
        low = [h.lower() for h in self.header]
        if "time" not in low:
            sep = " (its first line holds ';': another separator)" if any(";" in h for h in self.header) else ""
            raise SystemExit(f"REFUSED: {self.name} has no Time column{sep}; it {NOT_EXPORT}")
        self.time_idx = low.index("time")
        self.chan_idx = [i for i, h in enumerate(low) if h != "time"]     # header indices, poll order
        self.N = len(self.chan_idx)
        self.idx, self.pos = {}, {}
        for k, name in KEYS.items():
            i = low.index(name) if name in low else None
            self.idx[k] = i
            self.pos[k] = self.chan_idx.index(i) if i is not None else None
        self.v8 = v8_check(self.pos, self.N)

    @property
    def logs_ignition(self):
        return self.idx["act"] is not None or self.idx["tgt"] is not None

    def describe(self):
        return dict(path=recorded_path(self.path), name=self.name, role=self.role, sha256=sha256_file(self.path),
                    header=self.header, n_channels=self.N,
                    positions={k: self.pos[k] for k in KEYS}, v8=self.v8)


def v8_check(pos, n):
    """V8 from the header's column order only (IC6)."""
    a, t = pos.get("act"), pos.get("tgt")
    if a is None or t is None:
        return dict(ok=False, lag_rows=None, reason="no actual or no target ignition column")
    lag = (t - a) % n
    ok = lag in (1, 2)
    return dict(ok=ok, lag_rows=int(lag),
                reason="" if ok else f"the target is polled {lag} rows after the actual (V8 needs 1-2)")


def load_blind(lf):
    """Stage A's only reader: Time and the four blind channels, by column index. The two
    ignition columns are never named in usecols, so they are never loaded."""
    cols = [lf.time_idx] + [lf.idx[k] for k in BLIND if lf.idx[k] is not None]
    bad = [i for i in cols if lf.header[i].lower() in IGN_NAMES]
    assert not bad, "stage A must never load an ignition column"
    cols = sorted(cols)
    try:          # index_col=False: a trailing delimiter on the data rows never shifts a column (IC38)
        df = pd.read_csv(lf.path, usecols=cols, index_col=False, encoding="utf-8-sig", low_memory=False)
    except (ValueError, UnicodeDecodeError) as e:
        raise SystemExit(f"REFUSED: {lf.name} {NOT_EXPORT} ({type(e).__name__}: {str(e)[:80]})")
    pick = lambda i: pd.to_numeric(df.iloc[:, cols.index(i)], errors="coerce").to_numpy(float)
    t = pick(lf.time_idx)
    vals = {k: (pick(lf.idx[k]) if lf.idx[k] is not None else None) for k in BLIND}
    return t, vals


def load_ignition_text(lf):
    """Stages B and C: the two ignition columns as TEXT. Nothing is converted here."""
    if lf.idx["act"] is None or lf.idx["tgt"] is None:
        return None
    cols = sorted([lf.idx["act"], lf.idx["tgt"]])
    try:
        df = pd.read_csv(lf.path, usecols=cols, dtype=str, keep_default_na=False, index_col=False,
                         encoding="utf-8-sig", low_memory=False)
    except (ValueError, UnicodeDecodeError) as e:
        raise SystemExit(f"REFUSED: {lf.name} {NOT_EXPORT} ({type(e).__name__}: {str(e)[:80]})")
    return {k: np.char.strip(df.iloc[:, cols.index(lf.idx[k])].to_numpy(dtype=str)) for k in IGN}


def find_runs(t):
    """IC1: rows between logger breaks."""
    n = len(t)
    if n == 0:
        return [], float("nan")
    dt = np.diff(t)
    good = dt[np.isfinite(dt) & (dt > 0)]
    med = float(np.median(good)) if len(good) else 1.0
    brk = np.flatnonzero(~np.isfinite(dt) | (dt <= 0) | (dt > BREAK_X * med))
    starts = np.r_[0, brk + 1]
    ends = np.r_[brk, n - 1]
    return [(int(s), int(e)) for s, e in zip(starts, ends)], med


def single_change_phases(vals, lf, s, e):
    """The single-change rows of rows s..e (only one blind channel changed from the row
    before) and the phase each implies: (row - position of the changed channel) mod N."""
    keys = [k for k in BLIND if vals[k] is not None]
    if e <= s or not keys:
        return np.array([], int), np.array([], int)
    X = np.column_stack([vals[k][s:e + 1] for k in keys])
    prev, cur = X[:-1], X[1:]
    chg = ~((prev == cur) | (np.isnan(prev) & np.isnan(cur)))
    one = np.flatnonzero(chg.sum(1) == 1)
    which = chg[one].argmax(1)
    p = np.array([lf.pos[keys[j]] for j in which], dtype=int)
    rows = s + 1 + one
    return rows, (rows - p) % lf.N


def estimate_phase(vals, lf, s, e):
    """D1: the round-robin phase phi of one run, from the single-change rows of the blind
    channels (IC2): row r polls position p when (r - p) mod N == phi."""
    _, ph = single_change_phases(vals, lf, s, e)
    if len(ph) == 0:
        return dict(phase=None, share=None, n_single=0, flagged=True)
    counts = np.bincount(ph, minlength=lf.N)
    mode = int(counts.argmax())
    share = float(counts[mode] / len(ph))
    return dict(phase=mode, share=share, n_single=int(len(ph)),
                flagged=bool(share < PHASE_SHARE or len(ph) < PHASE_MIN_ROWS))


def split_on_phase(vals, lf, s, e):
    """IC1: a persistent change of the round-robin phase is a logger break too (a dropped
    row shifts every later poll by one row and leaves no time gap). A change counts when at
    least 9 of the 10 single-change rows from it on share the new phase; the rows between
    the last single-change row of the old phase and the first of the new one become a run
    of their own, which has no single-change row and is therefore flagged."""
    rows, ph = single_change_phases(vals, lf, s, e)
    if len(ph) < PHASE_LOOK:
        return [(s, e)]
    cur = int(np.bincount(ph[:PHASE_LOOK], minlength=lf.N).argmax())
    out, start = [], s
    for i in range(len(ph)):
        if ph[i] == cur:
            continue
        win = ph[i:i + PHASE_LOOK]
        if len(win) == PHASE_LOOK and np.mean(win == ph[i]) >= PHASE_AGREE:
            last_old = int(rows[i - 1]) if i else start - 1
            if last_old >= start:
                out.append((start, last_old))
            if rows[i] - 1 >= last_old + 1:
                out.append((last_old + 1, int(rows[i]) - 1))
            start, cur = int(rows[i]), int(ph[i])
    out.append((start, e))
    return out


def runs_info_of(t, vals, lf):
    bounds, med = find_runs(t)
    out = []
    for s0, e0 in bounds:
        for s, e in split_on_phase(vals, lf, s0, e0):
            ri = dict(start=s, end=e, t_start=float(t[s]), t_end=float(t[e]))
            ri.update(estimate_phase(vals, lf, s, e))
            out.append(ri)
    return out, med


def poll_mask(n_rows, runs_info, pos, n_ch):
    """Rows at which the channel at header position `pos` was polled, in unflagged runs."""
    m = np.zeros(n_rows, bool)
    if pos is None:
        return m
    for ri in runs_info:
        if ri["flagged"] or ri["phase"] is None:
            continue
        r = np.arange(ri["start"], ri["end"] + 1)
        m[r[(r - pos - ri["phase"]) % n_ch == 0]] = True
    return m


def change_mask(v, runs_info):
    """D1's fallback in a flagged run: only value changes count (never a run's first row)."""
    m = np.zeros(len(v), bool)
    for ri in runs_info:
        if not ri["flagged"]:
            continue
        a = v[ri["start"]:ri["end"] + 1]
        if len(a) < 2:
            continue
        d = ~((a[1:] == a[:-1]) | (np.isnan(a[1:]) & np.isnan(a[:-1])))
        m[ri["start"] + 1:ri["end"] + 1] = d
    return m


def blind_genuine(v, lf, key, runs_info):
    """D1 for a blind channel: poll rows (or value changes in a flagged run), minus blanks,
    leading placeholder zeros (AUDIT.md M8) and values outside the channel's range."""
    m = poll_mask(len(v), runs_info, lf.pos[key], lf.N) | change_mask(v, runs_info)
    lo, hi = RANGE[key]
    ok = m & np.isfinite(v) & (v >= lo) & (v <= hi)
    nz = np.flatnonzero(np.isfinite(v) & (v != 0))
    lead = int(nz[0]) if len(nz) else len(v)
    ok[:lead] &= (v[:lead] != 0)
    return ok


_ZERO = re.compile(r"^[+-]?(0+(\.0*)?|\.0+)$")


def leading_placeholder_end(text):
    """IC4: the first row whose cell holds text that is not a zero literal."""
    for i, s in enumerate(text):
        if s and not _ZERO.match(s):
            return i
    return len(text)


def to_float(text):
    return pd.to_numeric(pd.Series(text, dtype=object), errors="coerce").to_numpy(float)


class Readings:
    """Genuine readings of one channel in one run: rows, times, values (NaN = not read)."""

    def __init__(self, rows=(), t=(), v=()):
        self.rows = np.asarray(rows, dtype=int)
        self.t = np.asarray(t, dtype=float)
        self.v = np.asarray(v, dtype=float)

    def __len__(self):
        return len(self.t)

    def within(self, lo, hi, left_open=True):
        lo_ok = (self.t > lo) if left_open else (self.t >= lo)
        return lo_ok & (self.t <= hi)

    def at(self, tq):
        """D4 / IC8: linear between genuine readings, NaN outside them."""
        tq = np.atleast_1d(np.asarray(tq, float))
        if len(self.t) == 0:
            return np.full(tq.shape, np.nan)
        out = np.interp(tq, self.t, self.v)
        return np.where((tq < self.t[0]) | (tq > self.t[-1]) | ~np.isfinite(tq), np.nan, out)


class Gear:
    """D6: consecutive genuine engine-speed readings and their |ln(n2/n1)|/dt."""

    def __init__(self, rpm):
        if len(rpm) < 2:
            self.t1 = self.t2 = self.rate = np.array([])
            self.flag = np.array([], bool)
            return
        self.t1, self.t2 = rpm.t[:-1], rpm.t[1:]
        self.rate = np.abs(np.log(rpm.v[1:] / rpm.v[:-1])) / (self.t2 - self.t1)
        self.flag = self.rate > GEAR_RATE

    def between(self, lo, hi):
        """IC12: any flagged pair overlapping [lo, hi]."""
        return bool(np.any(self.flag & (self.t2 >= lo) & (self.t1 <= hi)))

    def at(self, tq):
        """IC25: a flagged pair spans the time."""
        tq = np.atleast_1d(np.asarray(tq, float))
        if len(self.t1) == 0:
            return np.zeros(tq.shape, bool)
        f = self.flag
        return np.array([bool(np.any(f & (self.t1 <= x) & (self.t2 >= x))) for x in tq])


class Run:
    """One run of one file: its rows, its phase, its genuine readings."""

    def __init__(self, lf, index, info, t, readings):
        self.lf, self.index, self.info, self.t_rows = lf, index, info, t
        self.r = readings
        self.gear = Gear(readings["rpm"])

    @property
    def t_start(self):
        return float(self.t_rows[self.info["start"]])

    @property
    def t_end(self):
        return float(self.t_rows[self.info["end"]])

    @property
    def flagged(self):
        return bool(self.info["flagged"])

    def rows(self, mask):
        s, e = self.info["start"], self.info["end"]
        return np.flatnonzero(mask[s:e + 1]) + s


def build_runs(lf, t, vals, runs_info):
    gm = {k: (blind_genuine(vals[k], lf, k, runs_info) if vals[k] is not None else None) for k in BLIND}
    runs = []
    for j, ri in enumerate(runs_info):
        rd = {}
        s, e = ri["start"], ri["end"]
        for k in BLIND:
            if gm[k] is None:
                rd[k] = Readings()
                continue
            rows = np.flatnonzero(gm[k][s:e + 1]) + s
            rd[k] = Readings(rows, t[rows], vals[k][rows])
        runs.append(Run(lf, j, ri, t, rd))
    return runs


def ignition_genuine(lf, runs_info, text, allowed=None):
    """IC4: genuine ignition readings by poll position. `allowed` (stage B) is the row mask
    whose cells may be converted to numbers; every other value stays NaN. Stage C passes
    None and converts every genuine cell, dropping text that is not a number."""
    out = {}
    n = len(text["act"])
    for k in IGN:
        s = text[k]
        present = s != ""
        gen = poll_mask(n, runs_info, lf.pos[k], lf.N) & present
        gen[:leading_placeholder_end(s)] = False
        vals = np.full(n, np.nan)
        conv = gen.copy() if allowed is None else (gen & allowed)
        vals[conv] = to_float(s[conv])
        if allowed is None:
            gen &= np.isfinite(vals)
        else:
            gen &= ~allowed | np.isfinite(vals)
            assert not np.any(np.isfinite(vals[~allowed])), "an ignition value outside the allowed windows"
        out[k] = (gen, vals)
    return out


# ==== D2: pairs ==================================================================
class Pairs:
    """retard = min(target polled just before, target polled just after) - actual."""

    def __init__(self, tb=(), ta=(), tc=(), target=None, actual=None):
        self.tb, self.ta, self.tc = (np.asarray(x, float) for x in (tb, ta, tc))
        self.target = None if target is None else np.asarray(target, float)
        self.actual = None if actual is None else np.asarray(actual, float)
        self.retard = None if target is None else self.target - self.actual

    def __len__(self):
        return len(self.ta)

    def inside(self, lo, hi, left_open=True, right_open=False):
        """D2: a pair is in a window only if both targets and the actual are."""
        a = (self.tb > lo) if left_open else (self.tb >= lo)
        b = (self.tc < hi) if right_open else (self.tc <= hi)
        return a & b

    def take(self, m):
        m = np.asarray(m, bool)
        if self.target is None:
            return Pairs(self.tb[m], self.ta[m], self.tc[m])
        return Pairs(self.tb[m], self.ta[m], self.tc[m], self.target[m], self.actual[m])


def make_pairs(act, tgt, lag, n_ch, with_values=True):
    """D2 inside one run (IC1: a pair never spans a break): for each genuine actual reading,
    the target polled just before it (no more than 1.25 s earlier) and the target polled just
    after it. IC37: "polled just before / after" are the target's own polls of the previous and
    the same round-robin cycle, rows actual + lag - N and actual + lag (lag 1-2, V8). If either
    poll gave no genuine reading the pair is dropped: taking the next genuine target instead (a
    cycle later) could put a target dip between the two reads and create a pull."""
    empty = Pairs(target=[] if with_values else None, actual=[] if with_values else None)
    if len(act) == 0 or len(tgt) < 2 or lag not in (1, 2) or not n_ch:
        return empty
    after = np.searchsorted(tgt.rows, act.rows, side="right")
    before = after - 1
    ok = (before >= 0) & (after < len(tgt.rows))
    ai = np.flatnonzero(ok)
    b, c = before[ok], after[ok]
    keep = ((tgt.rows[c] == act.rows[ai] + lag) & (tgt.rows[b] == act.rows[ai] + lag - n_ch)
            & ((act.t[ai] - tgt.t[b]) <= PAIR_BEFORE_S + 1e-9))
    ai, b, c = ai[keep], b[keep], c[keep]
    if not with_values:
        return Pairs(tgt.t[b], act.t[ai], tgt.t[c])
    target = np.minimum(tgt.v[b], tgt.v[c])
    actual = act.v[ai]
    fin = np.isfinite(target) & np.isfinite(actual)
    return Pairs(tgt.t[b][fin], act.t[ai][fin], tgt.t[c][fin], target[fin], actual[fin])


def run_ign(run, ign):
    """The genuine ignition readings of one run, as Readings."""
    out = {}
    for k in IGN:
        gen, vals = ign[k]
        rows = run.rows(gen)
        out[k] = Readings(rows, run.t_rows[rows], vals[rows])
    return out


def run_pairs(run, ign, with_values=True):
    """D2 / IC37 for one run of one file: the actual and target genuine readings, paired."""
    ri = run_ign(run, ign)
    return make_pairs(ri["act"], ri["tgt"], run.lf.v8["lag_rows"], run.lf.N, with_values=with_values)


# ==== C2, item 1: the step detector ============================================
def rolling_median(t, a, span):
    m = np.empty(len(a))
    j = 0
    for i in range(len(a)):
        while t[j] <= t[i] - span:
            j += 1
        m[i] = np.median(a[j:i + 1])
    return m


def detect_steps(air):
    """Item 1 on one run's genuine air readings."""
    t, a = air.t, air.v
    n = len(a)
    if n < 4:
        return []
    M = rolling_median(t, a, MEDIAN_S)
    steps, i = [], 1
    while i < n:
        k = i
        if not a[k] > DEPART_X * M[k - 1]:
            i += 1
            continue
        mst, t0 = float(M[k - 1]), float(t[k - 1])
        trig = next((j for j in (k, k + 1) if j < n and a[j] >= TRIGGER_X * mst), None)
        if trig is None or trig + 2 >= n:
            i = k + 1
            continue
        c1, c2 = a[trig + 1], a[trig + 2]
        if not (c1 >= TRIGGER_X * mst and c1 >= mst + CONFIRM_ADD and c2 >= TRIGGER_X * mst):
            i = k + 1
            continue
        f = next((j for j in range(trig + 1, n) if a[j] < FALL_DROP * a[j - 1] or a[j] < FALL_X * mst), None)
        t1 = float(t[trig])
        tf_prev = float(t[f - 1]) if f is not None else float(t[n - 1])
        after10 = next((j for j in range(trig + 1, n) if t[j] > t1 + RESUME_S), n)
        resume = min(f if f is not None else n, after10)
        # IC10: a departure whose t0 lies before the previous step's fall (or after a step that
        # never fell) finds the previous roll-on again: scanned while still held after the 10 s
        # resumption, or rising again from a wobble the fall rule read as a fall. IC36 fails it on V3.
        last = steps[-1] if steps else None
        redet = bool(last is not None and t0 < (last["tau_f"] if last["tau_f"] is not None else last["tau_f_prev"]))
        steps.append(dict(k=int(k), trig=int(trig), f=None if f is None else int(f), t0=t0, t1=t1, M=mst,
                          redetection=redet,
                          trigger="k" if trig == k else "k+1",
                          departure=float(a[k]), trigger_air=float(a[trig]),
                          confirm=[float(c1), float(c2)],
                          tau_f=None if f is None else float(t[f]), tau_f_prev=tf_prev,
                          fall_found=f is not None,
                          t_W=float(min(t1 + L_MAX, tf_prev - GUARD_S))))
        i = max(resume, k + 1)
    return steps


def pre_window(run, t0):
    """Readings in P = (t0 - 20 s, t0] and their medians."""
    r = run.r
    w = {k: r[k].v[r[k].within(t0 - P_S, t0)] for k in BLIND}
    med = {k: (float(np.median(w[k])) if len(w[k]) else float("nan")) for k in BLIND}
    return w, med


def assess_step(st, run, lf):
    """V1-V8 (stage A, no ignition channel), KI1 (D5) and the 6b size."""
    air, rpm = run.r["air"], run.r["rpm"]
    t0, t1, tw, m = st["t0"], st["t1"], st["t_W"], st["M"]
    w, med = pre_window(run, t0)
    why = {}
    v = []
    if len(w["air"]) < V1_N:
        v.append(f"{len(w['air'])} air readings in the 20 s before t0 (needs {V1_N})")
    elif np.any(w["air"] < V1_LO * m) or np.any(w["air"] > V1_HI * m):
        v.append("an air reading outside 0.7-1.3 M in the 20 s before t0")
    if len(w["rpm"]) == 0:
        v.append("no engine-speed reading in the 20 s before t0")
    else:
        if w["rpm"].max() / w["rpm"].min() > V1_RPM_RATIO:
            v.append(f"engine speed max/min {w['rpm'].max() / w['rpm'].min():.3f} above 1.05")
        if not V1_RPM[0] <= med["rpm"] <= V1_RPM[1]:
            v.append(f"median engine speed {med['rpm']:.0f} outside 1400-2600 rpm")
    why["V1"] = v
    why["V2"] = [] if m <= V2_M else [f"M {m:.1f} kg/h above 100"]
    v = []
    if t0 - V3_S < run.t_start:
        v.append("the 40 s before t0 begin before the run")
    if np.any(air.v[air.within(t0 - V3_S, t0)] > V3_X * m):
        v.append("an air reading above 1.3 M in the 40 s before t0")
    why["V3"] = v
    why["V4"] = (["a gear flag between t0 - 20 s and t_W"] if run.gear.between(t0 - P_S, tw) else [])
    v = []
    held = air.v[(air.t >= t1) & (air.t <= tw)]
    if np.any(held < V5_X * m):
        v.append("an air reading under 1.3 M between t1 and t_W")
    if tw < t1 + V5_MIN_S - EPS:
        v.append(f"t_W is {tw - t1:.2f} s after t1 (needs 2.5)")
    why["V5"] = v
    v = []
    if len(w["cool"]) == 0:
        v.append("no coolant reading in the 20 s before t0")
    elif med["cool"] < V6_COOL:
        v.append(f"coolant median {med['cool']:.1f} C under 80")
    if lf.idx["amb"] is None:
        v.append("ambient not logged")
    elif len(w["amb"]) == 0:
        v.append("no ambient reading in the 20 s before t0")
    why["V6"] = v
    # D5, the model's own spike, on the frozen plant
    j1, j2 = st["trig"] + 1, st["trig"] + 2
    tau1, a1 = float(air.t[j1]), float(air.v[j1])
    tau2, a2 = float(air.t[j2]), float(air.v[j2])
    rpm1 = float(rpm.at(tau1)[0])
    amb, cool = med["amb"], med["cool"]
    map_pre = inv_map(m, med["rpm"], amb, cool)
    map1 = inv_map(a1, rpm1, amb, cool)
    spark_pre = model_spark(rpm1, map_pre, amb, cool)
    ki1 = knock_integral(rpm1, map1, amb, cool, spark_pre)
    map2 = inv_map(a2, float(rpm.at(tau2)[0]), amb, cool)
    if not np.isfinite(ki1):
        why["V7"] = ["KI1 could not be computed (a missing reading)"]
        kind = "out"
    elif a1 >= PIN_KGH:           # V7: "a pinned air reading counts as high" (IC13)
        why["V7"], kind = [], "primary"
    elif ki1 > V7_PRIMARY:
        why["V7"], kind = [], "primary"
    elif ki1 > V7_SIDE:
        why["V7"], kind = [f"KI1 {ki1:.3f}: side set (0.85-1.0), reported, never in the verdict"], "side"
    else:
        why["V7"], kind = [f"KI1 {ki1:.3f} at or under 0.85"], "out"
    why["V8"] = [] if lf.v8["ok"] else [lf.v8["reason"]]
    why["D1"] = (["the run's poll phase is flagged (IC3)"] if run.flagged else [])
    flags = {k: not why[k] for k in ("V1", "V2", "V3", "V4", "V5", "V6", "V8", "D1")}
    flags["V7"] = kind in ("primary", "side")
    valid = all(flags.values())
    st.update(dict(
        L=[t1 + L_START, tw], E=[t0, t1 + L_START], P=[t0 - P_S, t0],
        late_len_s=float(tw - t1 - L_START),
        rpm_pre=med["rpm"], amb_pre=amb, cool_pre=cool, map_pre=map_pre,
        tau1=tau1, air1=a1, rpm1=rpm1, map1=map1, spark_pre=spark_pre, KI1=ki1,
        KI1_lower_bound=bool(a1 >= PIN_KGH), map2=map2, large=bool(np.isfinite(map2) and map2 >= LARGE_KPA),
        set=kind, flags=flags, reasons={k: why[k] for k in why if why[k]},
        stage_a_valid=bool(valid), stage_a_valid_primary=bool(valid and kind == "primary")))
    return st


def assess_sham(a, kind, run, lf, ell, source=None):
    """A sham window scored like a step (IC19, IC20): B* in (a - 20, a]; window (a, a + l]."""
    air = run.r["air"]
    w, med = pre_window(run, a)
    why = {}
    ms = float(np.median(w["air"])) if len(w["air"]) else float("nan")
    v = []
    if not np.isfinite(ms) or len(w["air"]) < V1_N:
        v.append(f"{len(w['air'])} air readings in the 20 s before (needs {V1_N})")
    elif np.any(w["air"] < V1_LO * ms) or np.any(w["air"] > V1_HI * ms):
        v.append("an air reading outside 0.7-1.3 M* in the 20 s before")
    if len(w["rpm"]) == 0:
        v.append("no engine-speed reading in the 20 s before")
    else:
        if w["rpm"].max() / w["rpm"].min() > V1_RPM_RATIO:
            v.append("engine speed max/min above 1.05")
        if not V1_RPM[0] <= med["rpm"] <= V1_RPM[1]:
            v.append(f"median engine speed {med['rpm']:.0f} outside 1400-2600 rpm")
    why["V1"] = v
    why["V2"] = [] if (np.isfinite(ms) and ms <= V2_M) else ["M* above 100 kg/h"]
    v = []
    if a - V3_S < run.t_start:
        v.append("the 40 s before begin before the run")
    if np.isfinite(ms) and np.any(air.v[air.within(a - V3_S, a)] > V3_X * ms):
        v.append("an air reading above 1.3 M* in the 40 s before")
    why["V3"] = v
    why["V4"] = (["a gear flag between a - 20 s and a + l"] if run.gear.between(a - P_S, a + ell) else [])
    v = []
    if len(w["cool"]) == 0:
        v.append("no coolant reading in the 20 s before")
    elif med["cool"] < V6_COOL:
        v.append("coolant median under 80 C")
    if lf.idx["amb"] is None:
        v.append("ambient not logged")
    elif len(w["amb"]) == 0:
        v.append("no ambient reading in the 20 s before")
    why["V6"] = v
    v = []
    if np.isfinite(ms) and np.any(air.v[air.within(a, a + ell)] > V3_X * ms):
        v.append("an air reading above 1.3 M* in the window")
    if a + ell > (air.t[-1] if len(air) else -np.inf):
        v.append("the window ends after the run's last air reading")
    why["across"] = v
    why["V8"] = [] if lf.v8["ok"] else [lf.v8["reason"]]
    why["D1"] = (["the run's poll phase is flagged (IC3)"] if run.flagged else [])
    flags = {k: not why[k] for k in why}
    return dict(a=float(a), anchor=kind, from_step=source, window=[float(a), float(a + ell)],
                P=[float(a - P_S), float(a)], M=ms, amb_pre=med["amb"], flags=flags,
                reasons={k: why[k] for k in why if why[k]}, stage_a_valid=bool(all(flags.values())))


def sham_anchors(run_steps, file_steps, run, lf, first_row_t):
    """Anchors (a) and (b), from one run of a C2 file (IC18). Anchor (a) comes from this run's
    steps; anchor (b)'s zones come from every step detected in the file, all runs ("any fall",
    "any step's t0"), and the grid runs from the file's first row with a time (IC18)."""
    air = run.r["air"]
    out = []
    a_times = []
    for st in sorted(run_steps, key=lambda s: s["t0"]):
        if st["tau_f"] is None:
            continue
        j = np.flatnonzero(air.t >= st["tau_f"] + SHAM_A_S)
        if len(j):
            x = float(air.t[j[0]])
            if any(abs(x - y) < SHAM_GRID_S for y, _ in a_times):
                continue          # IC18: a re-detection shares its step's fall; no two shams closer than 30 s
            a_times.append((x, st["id"]))
    zones = [(st["t0"] - SHAM_B_T0_S, (st["tau_f"] if st["tau_f"] is not None else st["tau_f_prev"]) + SHAM_B_FALL_S)
             for st in file_steps]
    for x, sid in a_times:
        out.append(("a", x, sid))
    g = first_row_t + SHAM_GRID_S
    while g <= run.t_end:
        if g >= run.t_start and not any(lo < g <= hi for lo, hi in zones) \
                and not any(abs(g - x) < SHAM_GRID_S for x, _ in a_times):
            out.append(("b", float(g), None))
        g += SHAM_GRID_S
    return out


# ==== C1, section 4: the segments ==============================================
def segment_rows(run):
    """Per genuine air reading: speed, MAP, coolant, ambient, and whether it qualifies."""
    r = run.r
    t, a = r["air"].t, r["air"].v
    rpm = r["rpm"].at(t)
    cool = r["cool"].at(t)
    amb = r["amb"].at(t)
    mp = np.array([inv_map(x, n, ta, tc) for x, n, ta, tc in zip(a, rpm, amb, cool)]) if len(t) else np.array([])
    gear = run.gear.at(t) if len(t) else np.array([], bool)
    with np.errstate(invalid="ignore"):
        ok = (np.isfinite(mp) & (mp >= SEG_MAP) & (rpm >= SEG_RPM[0]) & (rpm <= SEG_RPM[1])
              & (a < SEG_AIR_MAX) & (cool >= SEG_COOL) & ~gear)
    return dict(t=t, a=a, rpm=rpm, cool=cool, amb=amb, map=mp, ok=ok)


def find_segments(run):
    """Section 4 (IC25): maximal runs of qualifying air readings, ended at their own fall."""
    d = segment_rows(run)
    t, a, mp, ok = d["t"], d["a"], d["map"], d["ok"]
    n = len(t)
    segs, i = [], 0
    while i < n:
        if not ok[i]:
            i += 1
            continue
        j = i
        while j + 1 < n and ok[j + 1]:
            j += 1
        f = next((x for x in range(i + 1, min(j + 2, n))
                  if a[x] < FALL_DROP * a[x - 1] or not (np.isfinite(mp[x]) and mp[x] >= SEG_MAP)), None)
        e = (f - 1) if f is not None else j
        s0, end = float(t[i] + SEG_SPOOL_S), float(t[e] - GUARD_S)
        sel = (t >= s0) & (t <= end)
        segs.append(dict(first_t=float(t[i]), s0=s0, end=end, last_reading_t=float(t[e]),
                         fall_found=f is not None, counting=bool(end - s0 >= SEG_MIN_S - EPS),
                         n_air=int(sel.sum()),
                         rpm_median=float(np.median(d["rpm"][i:e + 1])),
                         amb_median=float(np.nanmedian(d["amb"][i:e + 1])) if np.any(np.isfinite(d["amb"][i:e + 1])) else None))
        i = j + 1
    return segs, d


def in_cell(rpm, mp, cell):
    with np.errstate(invalid="ignore"):
        return ((rpm >= cell["rpm"][0]) & (rpm <= cell["rpm"][1])
                & (mp >= cell["map"][0]) & (mp <= cell["map"][1]))


def cell_state(run, times):
    """Speed, MAP, coolant and ambient at arbitrary times (D4)."""
    r = run.r
    rpm, air, cool, amb = (r[k].at(times) for k in ("rpm", "air", "cool", "amb"))
    mp = np.array([inv_map(x, n, ta, tc) for x, n, ta, tc in zip(air, rpm, amb, cool)]) if len(times) else np.array([])
    return rpm, mp, cool, amb


def act_positions(run, lf):
    """The actual angle's poll rows in one run, from the phase and the header alone."""
    if lf.pos["act"] is None or run.flagged:
        return np.array([], int)
    m = poll_mask(len(run.t_rows), [run.info], lf.pos["act"], lf.N)
    return run.rows(m)


def cell_counts(seg, run, lf, act_rows):
    """Stage A's blind counts per segment: air and speed readings in each cell, and the actual
    angle's poll positions in each cell (item 8: coolant >= 80, ambient logged)."""
    out = {}
    r = run.r
    ta = run.t_rows[act_rows] if len(act_rows) else np.array([])
    ta = ta[(ta >= seg["s0"]) & (ta <= seg["end"])]
    for name, cell in (("primary", CELL_PRIMARY), ("fallback", CELL_FALLBACK)):
        air_t = r["air"].t[(r["air"].t >= seg["s0"]) & (r["air"].t <= seg["end"])]
        n_air = 0
        if len(air_t):
            rpm, mp, _, _ = cell_state(run, air_t)
            n_air = int(in_cell(rpm, mp, cell).sum())
        rp_t = r["rpm"].t[(r["rpm"].t >= seg["s0"]) & (r["rpm"].t <= seg["end"])]
        n_rpm = 0
        if len(rp_t):
            rpm, mp, _, _ = cell_state(run, rp_t)
            n_rpm = int(in_cell(rpm, mp, cell).sum())
        n_act = 0
        if len(ta):
            rpm, mp, cool, amb = cell_state(run, ta)
            with np.errstate(invalid="ignore"):
                n_act = int((in_cell(rpm, mp, cell) & (cool >= SEG_COOL) & np.isfinite(amb)).sum())
        out[name] = dict(air=n_air, rpm=n_rpm, actual_positions=n_act)
    return out


# ==== IC36: no pre-window may hold a response window ===========================
def response_end(s):
    """The end of a detected step's span: its fall (its run's last air reading if it never
    fell), and never before its early and late windows end."""
    fall = s["tau_f"] if s["tau_f"] is not None else s["tau_f_prev"]
    return max(fall, s["t1"] + L_START, s["t_W"])


def response_window(s):
    """A detected step's early and late windows together, E + L = (t0, max(t1 + 1 s, t_W)]."""
    return (s["t0"], max(s["t1"] + L_START, s["t_W"]))


def _meets(a, b):
    """Two windows (lo, hi] share a moment."""
    return a[0] < b[1] and b[0] < a[1]


def _fail(x, key, why):
    x["flags"][key] = False
    x["reasons"].setdefault(key, []).append(why)
    x["stage_a_valid"] = False
    if "stage_a_valid_primary" in x:
        x["stage_a_valid_primary"] = False


def ic36_steps(steps):
    """IC36, V3 read as spacing from every other step: a step whose (t0 - 40 s, t0] meets another
    detected step's span [t0', end'] (same file and run) fails V3. The literal V3 compares air
    readings with 1.3 M, and M is lifted when the 20 s before t0 hold an earlier step that is still
    held (a re-detection, IC10) or held long: its pre-window would then hold that step's early or
    late window, which stage B would read before the freeze (guard 4)."""
    for s in steps:
        near = [o["id"] for o in steps if o is not s and o["file"] == s["file"] and o["run"] == s["run"]
                and o["t0"] <= s["t0"] and response_end(o) > s["t0"] - V3_S]
        if near:
            _fail(s, "V3", f"another detected step ({', '.join(near)}) in the 40 s before t0 (IC36)")


def ic36_shams(shams, steps):
    """IC36 for shams: no detected step within (a - 40 s, a + l] (the sham's spacing, as for a
    step); and its window (a, a + l] lies in no stage-A-valid pre-window, a step's or another
    sham's, because stage B reads those (under the rule's own plan, a full minute before each
    press, anchor (a) lands in the next press's pre-window)."""
    for h in shams:
        same = [s for s in steps if s["file"] == h["file"] and s["run"] == h["run"]]
        near = [o["id"] for o in same if o["t0"] <= h["window"][1] and response_end(o) > h["a"] - V3_S]
        if near:
            _fail(h, "V3", f"a detected step ({', '.join(near)}) within (a - 40 s, a + l] (IC36)")
        inside = [o["id"] for o in same if o["stage_a_valid"] and _meets(h["window"], o["P"])]
        if inside:
            _fail(h, "P", f"its window lies in the pre-window of {', '.join(inside)}, which stage B reads (IC36)")
    for h in shams:
        if h["stage_a_valid"]:
            inside = [g["id"] for g in shams if g is not h and g["stage_a_valid"] and g["file"] == h["file"]
                      and g["run"] == h["run"] and _meets(h["window"], g["P"])]
            if inside:
                _fail(h, "P", f"its window lies in the pre-window of sham {', '.join(inside)} (IC36)")


# ==== blocks ===================================================================
def blocks_of(steps, counted=None):
    """Item 4 (IC21): a new block at a step in a new file, or one starting at least 5 min after
    the previous step's fall. The breaks are found over `steps`, every stage-A-valid step (side
    set and stage-B failures included: driving them is driving); only the ids in `counted`
    (default: all) are counted. Returns (id -> block, sizes), empty blocks dropped."""
    def fall(x):
        return x["tau_f"] if x["tau_f"] is not None else x["tau_f_prev"]

    counted = {s["id"] for s in steps} if counted is None else set(counted)
    order = sorted(steps, key=lambda s: (s["file"], s["t0"]))
    raw, bid, prev = {}, -1, None
    for s in order:
        if prev is None or s["file"] != prev["file"] or s["t0"] >= fall(prev) + BLOCK_GAP_S - EPS:
            bid += 1
        raw[s["id"]] = bid
        prev = s
    used = sorted({raw[i] for i in raw if i in counted})
    renum = {b: j for j, b in enumerate(used)}
    of = {i: renum[raw[i]] for i in raw if i in counted}
    sizes = [sum(1 for i in of if of[i] == j) for j in range(len(used))]
    return of, sizes


def cut_pair(sizes):
    """drive_c_rule_numbers.cuts for these block sizes, or None if no cut exists. Item 4's
    design values are passed explicitly, and RN's own must be the same numbers."""
    assert (RN.Q_DESIGN, RN.M_DESIGN, RN.ICC, RN.ALPHA) == (Q_RULE, M_RULE, ICC_RULE, ALPHA), \
        "drive_c_rule_numbers.py's design values are not the rule's (q 0.075, m 0.45, ICC 0.1, alpha 0.05)"
    sizes = [int(b) for b in sizes if b > 0]
    if not sizes:
        return None
    try:
        ky, kn, fy, fn = RN.cuts(sizes, q=Q_RULE, m=M_RULE, icc=ICC_RULE, alpha=ALPHA)
    except StopIteration:
        return None
    return dict(blocks=sizes, k_yes=int(ky), k_no=int(kn), false_pulls=fy, false_does_not=fn)


# ==== stage A ==================================================================
def guard1(path, logs_ignition):
    """Guard 1 (IC39): a file that logs the ignition angles is never read from logs/raw/ before
    stage C has run (build_dataset.py would write both angles into data/master_samples.csv)."""
    if logs_ignition and is_under(path, RAW_DIR):
        raise SystemExit(f"REFUSED: {os.path.basename(path)} lies in logs/raw/ and logs the ignition angles. "
                         "Guard 1 keeps drive C files out of logs/raw/ until stage C and the C1 analysis have "
                         "run: move it out (its SHA-256 does not change) and run again.")


def stage_c_started(folder):
    """Guard 5: a stage C marker or result in this folder."""
    return [n for n in (MARKER, RESULT) if os.path.exists(os.path.join(folder, n))]


def stage_a_files(specs):
    """The LogFiles of (path, role) pairs, after guard 1 and the duplicate checks (IC39)."""
    files = [LogFile(p, role) for p, role in specs]
    if len({os.path.normcase(f.path) for f in files}) != len(files):
        raise SystemExit("REFUSED: a file is listed twice (or as both C1 and C2)")
    for f in files:
        guard1(f.path, f.logs_ignition)
    shas = [sha256_file(f.path) for f in files]
    if len(set(shas)) != len(shas):
        raise SystemExit("REFUSED: the same log is listed twice under different names (identical SHA-256): "
                         "its steps and segments would count twice")
    return files


def stage_a(c2_paths, c1_paths, out_dir):
    lines = []
    plant = plant_check()
    if stage_c_started(out_dir):
        raise SystemExit(f"REFUSED: stage C has run in {out_dir} (guard 5); a later drive is a new test "
                         "with its own freeze: use a new --out")
    say(lines, "DRIVE C, STAGE A -- blind: Time, engine speed, air mass, coolant and ambient only")
    res = compute_stage_a([(p, "C2") for p in c2_paths] + [(p, "C1") for p in c1_paths], plant)
    res["created"] = datetime.now().isoformat(timespec="seconds")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "stage_a.json")
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(clean(res), fh, indent=1, sort_keys=True)
        fh.write("\n")
    report_a(lines, res)
    say(lines, f"\nwrote {path}")
    return res


def compute_stage_a(specs, plant):
    """Stage A on (path, role) pairs, C2 first: everything but the timestamp. Stage B and stage C
    run it again and refuse a stage_a.json or frozen.json that differs (IC33)."""
    files = stage_a_files(specs)
    steps, shams, segments, fdesc = [], [], [], []
    data = []
    for fi, lf in enumerate(files):
        t, vals = load_blind(lf)
        runs_info, med_dt = runs_info_of(t, vals, lf)
        runs = build_runs(lf, t, vals, runs_info)
        d = lf.describe()
        d.update(index=fi, n_rows=int(len(t)), median_row_s=med_dt, runs=runs_info,
                 n_genuine={k: int(sum(len(r.r[k]) for r in runs)) for k in BLIND},
                 missing=[KEYS[k] for k in KEYS if lf.idx[k] is None])
        fdesc.append(d)
        data.append((lf, t, runs))
    # C2: steps, then the late-window length the shams need, then the shams
    for fi, (lf, t, runs) in enumerate(data):
        if lf.role != "C2":
            continue
        for run in runs:
            for st in detect_steps(run.r["air"]):
                st.update(id=f"S{len(steps) + 1:03d}", file=fi, run=run.index)
                steps.append(assess_step(st, run, lf))
    ic36_steps(steps)
    valid_primary = [s for s in steps if s["stage_a_valid_primary"]]
    ell = float(np.median([s["late_len_s"] for s in valid_primary])) if valid_primary else SHAM_L_DEFAULT
    for fi, (lf, t, runs) in enumerate(data):
        if lf.role != "C2":
            continue
        ft = t[np.isfinite(t)]
        first_t = float(ft[0]) if len(ft) else float("nan")       # IC18: the file's first row with a time
        fsteps = [s for s in steps if s["file"] == fi]
        for run in runs:
            rs = [s for s in fsteps if s["run"] == run.index]
            for kind, a, sid in sham_anchors(rs, fsteps, run, lf, first_t):
                sh = assess_sham(a, kind, run, lf, ell, sid)
                sh.update(id=f"H{len(shams) + 1:03d}", file=fi, run=run.index)
                shams.append(sh)
    ic36_shams(shams, steps)
    # C1: segments and their blind cell counts
    for fi, (lf, t, runs) in enumerate(data):
        if lf.role != "C1":
            continue
        for run in runs:
            segs, _ = find_segments(run)
            act_rows = act_positions(run, lf)
            for sg in segs:
                sg.update(id=f"G{len(segments) + 1:03d}", file=fi, run=run.index,
                          D1_flagged=run.flagged, v8_ok=bool(lf.v8["ok"]))
                sg["cells"] = cell_counts(sg, run, lf, act_rows)
                segments.append(sg)
    cell, cell_why = choose_cell(segments, "actual_positions")
    of, sizes = blocks_of([s for s in steps if s["stage_a_valid"]], [s["id"] for s in valid_primary])
    for s in steps:
        s["block_provisional"] = of.get(s["id"])
    counting = [g for g in segments if g["counting"] and not g["D1_flagged"] and g["v8_ok"]]
    n_cell = {c: sum(1 for g in counting if g["cells"][c]["actual_positions"] >= CELL_MIN_READINGS)
              for c in ("primary", "fallback")}
    counts = dict(valid_primary_steps=len(valid_primary),
                  side_set_steps=sum(1 for s in steps if s["stage_a_valid"] and s["set"] == "side"),
                  detected_steps=len(steps),
                  valid_shams_stage_a=sum(1 for h in shams if h["stage_a_valid"]),
                  sham_anchors=len(shams),
                  segments=len(segments), counting_segments=len(counting),
                  item8_counting_segments=n_cell, sham_window_s=ell)
    needs = dict(
        valid_primary_steps=max(0, N_MIN - len(valid_primary)),
        valid_shams=max(0, SHAMS_MIN - counts["valid_shams_stage_a"]),
        item8_counting_segments=max(0, SEGS_MIN - n_cell[cell]),
        note=("Stage A's counts are upper bounds: stage B still needs >= 10 pre-window and >= 3 "
              "late-window pairs and a baseline within +-0.75 deg for each step and sham. The 8 "
              "confirmed C1 onsets the knee needs, and the 3 the channel check needs, cannot be "
              "known blind: they are counted only in stage C."))
    return dict(schema=SCHEMA, stage="A", code_sha=code_sha(), rule="results/DRIVE_C_RULE.md", **plant,
                constants=constants(), files=fdesc, steps=steps, shams=shams, segments=segments,
                blocks_provisional=sizes, sham_window_s=ell, cell=cell, cell_reason=cell_why,
                counts=counts, needs=needs)


def choose_cell(segments, field):
    """Item 8: the fallback cell only if the primary has fewer than 15 counting segments."""
    counting = [g for g in segments if g["counting"] and not g["D1_flagged"] and g["v8_ok"]]
    n = sum(1 for g in counting if g["cells"]["primary"][field] >= CELL_MIN_READINGS)
    if n >= SEGS_MIN:
        return "primary", f"{n} counting segments with >= 5 in-cell positions in the primary cell"
    return "fallback", (f"{n} counting segments with >= 5 in-cell positions in the primary cell "
                        f"(fewer than {SEGS_MIN}): the fallback 2000-3500 rpm x 160-200 kPa")


def constants():
    """The rule's numbers as this script holds them (folders and messages left out: they are not
    numbers, and a folder differs between machines)."""
    return {k: v for k, v in globals().items() if k.isupper() and isinstance(v, (int, float, tuple, dict, str))
            and k not in ("HERE", "OUT_DEFAULT", "LEGACY_JSON", "RESULTS_ROOT", "RAW_DIR", "MARKER", "RESULT",
                          "NOT_EXPORT")}


def report_a(lines, res):
    c = res["counts"]
    say(lines, f"plant_sha {res['plant_sha']}  derived_sha {res['derived_sha']}  code {res['code_sha']}")
    for f in res["files"]:
        rr = f["runs"]
        say(lines, f"  {f['role']} {f['name']}: {f['n_rows']} rows, {f['n_channels']} channels, "
                   f"{len(rr)} run(s), phase share "
                   + ", ".join("flagged" if r["flagged"] else f"{r['share']:.3f}" for r in rr)
                   + f"; V8 {'ok' if f['v8']['ok'] else 'FAILS: ' + f['v8']['reason']}")
    say(lines, f"\nC2: {c['detected_steps']} steps detected; {c['valid_primary_steps']} valid primary "
               f"(KI1 > 1.0), {c['side_set_steps']} in the side set")
    for s in res["steps"]:
        bad = "; ".join(f"{k}: {', '.join(v)}" for k, v in s["reasons"].items()) or "valid"
        ki1 = fmt(s["KI1"] if s["KI1"] is not None and np.isfinite(s["KI1"]) else None)
        say(lines, f"  {s['id']} t0 {s['t0']:8.1f}  t1 {s['t1']:8.1f}  t_W {s['t_W']:8.1f}  M {s['M']:6.1f}"
                   f"  KI1 {ki1:>6s}  {s['set']:7s}  {bad}")
    say(lines, f"shams: {c['sham_anchors']} anchors, {c['valid_shams_stage_a']} valid at stage A "
               f"(window {c['sham_window_s']:.2f} s)")
    say(lines, f"C1: {c['segments']} segments, {c['counting_segments']} counting; item 8 counting segments "
               f"primary {c['item8_counting_segments']['primary']}, fallback "
               f"{c['item8_counting_segments']['fallback']} -> cell {res['cell']}")
    n = res["needs"]
    say(lines, f"\nstill needed: {n['valid_primary_steps']} valid primary steps (16), {n['valid_shams']} valid "
               f"shams (24), {n['item8_counting_segments']} item-8 counting segments (15)")
    say(lines, "  " + n["note"])


# ==== stage B ==================================================================
VOLATILE = ("created", "stage_a_sha256", "stage_a_created", "git_head")
CODE_FILES = ("drive_c_analysis.py", "drive_c_rule_numbers.py")


def load_stage(path, stage):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    if d.get("stage") != stage or d.get("schema") != SCHEMA:
        raise SystemExit(f"{path} is not a stage {stage} file of schema {SCHEMA}")
    return d


def resolve_log(fd, logs_dir=None):
    """IC38: the file a record names, found at its recorded path (relative to the repository when
    it lies inside it), else by name in --logs DIR, and accepted only if its SHA-256 is the recorded
    one: the SHA-256 is the file's identity, the path only where to look. Guard 1 is checked again
    where it is found."""
    p = fd["path"]
    cands = [p if os.path.isabs(p) else os.path.join(HERE, *p.split("/"))]
    if logs_dir:
        cands.append(os.path.join(os.path.abspath(logs_dir), fd["name"]))
    seen = []
    for c in cands:
        if not os.path.exists(c):
            seen.append(f"{c} is missing")
            continue
        if sha256_file(c) != fd["sha256"]:
            seen.append(f"{c} is not the file stage A read (SHA-256 differs)")
            continue
        pos = fd.get("positions", {})
        guard1(c, pos.get("act") is not None or pos.get("tgt") is not None)
        return c
    raise SystemExit(f"REFUSED: {fd['name']}: " + "; ".join(seen) + " (pass --logs DIR if the log has moved)")


def reopen(fd, path):
    """A recorded file at its resolved path: header, blind columns, the recorded runs."""
    lf = LogFile(path, fd["role"])
    t, vals = load_blind(lf)
    runs_info = fd["runs"]
    return lf, t, vals, runs_info, build_runs(lf, t, vals, runs_info)


def canon(d):
    """A record as its JSON holds it, minus what two honest runs may differ in: the timestamps,
    the commit and where each log was found (its SHA-256 stays). IC33's recomputation compares these."""
    x = json.loads(json.dumps(clean(d), sort_keys=True))
    for k in VOLATILE:
        x.pop(k, None)
    for f in x.get("files", []):
        f.pop("path", None)
    return x


def first_difference(a, b, where=""):
    """Where two canonical records first differ (for the refusal message); "" if nowhere."""
    if type(a) is not type(b):
        return where or "/"
    if isinstance(a, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                return f"{where}/{k}"
            w = first_difference(a[k], b[k], f"{where}/{k}")
            if w:
                return w
        return ""
    if isinstance(a, list):
        if len(a) != len(b):
            return f"{where} (length {len(a)} against {len(b)})"
        for i, (x, y) in enumerate(zip(a, b)):
            w = first_difference(x, y, f"{where}[{i}]")
            if w:
                return w
        return ""
    return "" if a == b else (where or "/")


def git_head():
    """The commit checked out (read-only git), recorded beside the freeze."""
    try:
        r = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE, capture_output=True, text=True, timeout=30)
        return r.stdout.strip() if r.returncode == 0 else None
    except (OSError, subprocess.SubprocessError):
        return None


def require_committed_code(stage):
    """IC39: the rule's script is committed before the repeat drive (the rule's preamble); stages B
    and C run only on code that is tracked and unchanged against HEAD, so that the freeze and the
    result can be traced to a commit."""
    bad = [n for n in CODE_FILES if not committed(os.path.join(HERE, n))]
    if bad:
        raise SystemExit(f"REFUSED: {', '.join(bad)} not committed (tracked and unchanged against HEAD); "
                         f"{stage} runs only on the committed script")


def earlier_stage_c(roots, shas):
    """Guard 5: every stage C marker or result under these folders that names one of these logs by
    SHA-256. One that cannot be read counts: it cannot show that it does not."""
    hits = []
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dp, _, fn in os.walk(root):
            for name in (MARKER, RESULT):
                if name not in fn:
                    continue
                p = os.path.join(dp, name)
                try:
                    with open(p, encoding="utf-8") as fh:
                        named = set(json.load(fh).get("log_sha256") or [])
                except (OSError, ValueError, AttributeError, TypeError):
                    named = None
                if named is None or named & set(shas):
                    hits.append(p)
    return sorted(set(hits))


def rows_between(ri, t, lo, hi):
    """The rows of one run whose time lies in (lo, hi] (IC1: never another run's rows)."""
    r = np.arange(ri["start"], ri["end"] + 1)
    return r[(t[r] > lo) & (t[r] <= hi)]


def pre_window_rows(t, runs_info, file_steps, read_steps, read_shams):
    """Stage B's rows: `allowed`, the pre-windows it reads, each inside its own run; `forbid`, every
    detected step's early and late windows and every stage-A-valid sham's window (IC36)."""
    allowed, forbid = np.zeros(len(t), bool), np.zeros(len(t), bool)
    for x in read_steps + read_shams:
        allowed[rows_between(runs_info[x["run"]], t, *x["P"])] = True
    for s in file_steps:
        forbid[rows_between(runs_info[s["run"]], t, *response_window(s))] = True
    for h in read_shams:
        forbid[rows_between(runs_info[h["run"]], t, *h["window"])] = True
    return allowed, forbid


def stage_b(out_dir, logs_dir=None):
    lines = []
    plant = plant_check()
    require_committed_code("stage B")
    if stage_c_started(out_dir):
        raise SystemExit(f"REFUSED: stage C has already run in {out_dir}; a freeze after it would be made "
                         "unblinded. A later drive is a new test with its own freeze (guard 5): use a new --out.")
    sa_path = os.path.join(out_dir, "stage_a.json")
    sa = load_stage(sa_path, "A")
    if sa["code_sha"] != code_sha():
        raise SystemExit("REFUSED: drive_c_analysis.py or drive_c_rule_numbers.py changed since stage A")
    paths = [resolve_log(fd, logs_dir) for fd in sa["files"]]
    earlier = earlier_stage_c([RESULTS_ROOT], [fd["sha256"] for fd in sa["files"]])
    if earlier:
        raise SystemExit("REFUSED: stage C has already run on one of these logs (guard 5: it runs once, and a "
                         "later test freezes new drives): " + ", ".join(earlier))
    say(lines, "DRIVE C, STAGE B -- ignition values read inside the pre-windows only; the rest by poll position")
    again = compute_stage_a([(p, fd["role"]) for p, fd in zip(paths, sa["files"])], plant)
    diff = first_difference(canon(again), canon(sa))
    if diff:
        raise SystemExit(f"REFUSED: stage_a.json is not what this code computes from these logs (first difference "
                         f"at {diff}); run stage A again (IC33)")
    frozen = compute_stage_b(sa, paths, plant)
    frozen.update(created=datetime.now().isoformat(timespec="seconds"), stage_a_sha256=sha256_file(sa_path),
                  stage_a_created=sa.get("created"), git_head=git_head())
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "frozen.json")
    if os.path.exists(path):
        say(lines, f"note: replacing {path}; no stage C result exists beside it")
    raw = (json.dumps(clean(frozen), indent=1, sort_keys=True) + "\n").encode("utf-8")
    with open(path, "wb") as fh:
        fh.write(raw)
    digest = hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()
    with open(os.path.join(out_dir, "frozen.sha256"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(f"{digest}  frozen.json\n")
    report_b(lines, frozen)
    say(lines, f"\nwrote {path}\nwrote {os.path.join(out_dir, 'frozen.sha256')}  ({digest})")
    say(lines, "Commit both files before stage C (guard 4). Stage C refuses otherwise.")
    return frozen


def compute_stage_b(sa, paths, plant):
    """Stage B on a stage A record whose logs lie at `paths`: B, the pair counts, the frozen sets,
    the blocks and the cuts; everything but the timestamps. Stage C runs it again (IC33)."""
    steps, shams, segs = sa["steps"], sa["shams"], sa["segments"]
    ell = sa["sham_window_s"]
    for fi, (fd, path) in enumerate(zip(sa["files"], paths)):
        lf, t, _, runs_info, runs = reopen(fd, path)
        text = load_ignition_text(lf)
        fs = [s for s in steps if s["file"] == fi and s["stage_a_valid"]]
        fhs = [h for h in shams if h["file"] == fi and h["stage_a_valid"]]
        fg = [g for g in segs if g["file"] == fi]
        if text is None:
            for x in fs + fhs:
                x["stage_b"] = dict(n_P=0, n_L=0, n_E=0, B=None, B_ok=False, reason="no ignition columns")
            for g in fg:
                g["stage_b"] = dict(n_pairs=0, actual_in_cell={"primary": 0, "fallback": 0})
            continue
        allowed, forbid = pre_window_rows(t, runs_info, [s for s in steps if s["file"] == fi], fs, fhs)
        if np.any(allowed & forbid):
            raise SystemExit(f"REFUSED: in {fd['name']} a pre-window holds a response window (IC36); "
                             "no ignition value was converted")
        ign = ignition_genuine(lf, runs_info, text, allowed)
        for run in runs:
            ri = run_ign(run, ign)
            pos = run_pairs(run, ign, with_values=False)
            val = run_pairs(run, ign, with_values=True)
            for x in [s for s in fs if s["run"] == run.index] + [h for h in fhs if h["run"] == run.index]:
                p = val.take(val.inside(*x["P"]))
                b = lower_median(p.retard) if len(p) else None
                if "L" in x:      # a step
                    n_l = int(pos.inside(*x["L"]).sum())
                    n_e = int(pos.inside(*x["E"]).sum())
                else:             # a sham: its window
                    n_l = int(pos.inside(*x["window"]).sum())
                    n_e = None
                x["stage_b"] = dict(n_P=int(len(p)), n_L=n_l, n_E=n_e, B=b,
                                    B_ok=bool(b is not None and -B_ABS <= b <= B_ABS))
            for g in [g for g in fg if g["run"] == run.index]:
                g["stage_b"] = dict(n_pairs=int(pos.inside(g["s0"], g["end"], left_open=False).sum()),
                                    actual_in_cell=act_in_cell(g, run, ri["act"]))
    # the frozen sets
    for s in steps:
        b = s.get("stage_b")
        s["stage_b_valid"] = bool(s["stage_a_valid"] and b is not None and b["n_P"] >= P_MIN_PAIRS
                                  and b["n_L"] >= L_MIN_PAIRS and b["B_ok"])
        s["excluded_for_B"] = bool(s["stage_a_valid_primary"] and b is not None and b["n_P"] >= P_MIN_PAIRS
                                   and not b["B_ok"])
        s["valid_primary"] = bool(s["stage_b_valid"] and s["set"] == "primary")
    for h in shams:
        b = h.get("stage_b")
        h["valid"] = bool(h["stage_a_valid"] and b is not None and b["n_P"] >= P_MIN_PAIRS
                          and b["n_L"] >= L_MIN_PAIRS and b["B_ok"])
    vp = [s for s in steps if s["valid_primary"]]
    nb = [s for s in steps if s["excluded_for_B"]]
    boundary = [s for s in steps if s["stage_a_valid"]]
    of, sizes = blocks_of(boundary, [s["id"] for s in vp])
    of_b, sizes_b = blocks_of(boundary, [s["id"] for s in vp + nb])
    for s in steps:
        s["block"] = of.get(s["id"])
        s["block_with_B"] = of_b.get(s["id"])
    n_l_med = int(math.ceil(float(np.median([s["stage_b"]["n_L"] for s in vp])))) if vp else None
    for g in segs:
        g.setdefault("stage_b", dict(n_pairs=0, actual_in_cell={"primary": 0, "fallback": 0}))
    return dict(
        schema=SCHEMA, stage="B", code_sha=code_sha(), rule="results/DRIVE_C_RULE.md", **plant,
        constants=constants(), files=sa["files"], steps=steps, shams=shams, segments=segs,
        N=len(vp), n_B=len(nb), blocks=sizes, cuts=cut_pair(sizes) if vp else None,
        blocks_with_B=sizes_b, cuts_with_B=cut_pair(sizes_b) if (vp or nb) else None,
        valid_shams=sum(1 for h in shams if h["valid"]), sham_window_s=ell,
        late_pairs_median=n_l_med, cell=sa["cell"], cell_reason=sa["cell_reason"],
        cell_stage_b_check=choose_cell([dict(g, cells={c: {"actual_positions": g["stage_b"]["actual_in_cell"][c]}
                                                       for c in ("primary", "fallback")}) for g in segs],
                                       "actual_positions")[0],
        c2_testable=len(vp) >= N_MIN)


def act_in_cell(g, run, act):
    """Stage B's count of the actual angle's genuine positions in each cell (presence only)."""
    sel = (act.t >= g["s0"]) & (act.t <= g["end"])
    ta = act.t[sel]
    out = {}
    for name, cell in (("primary", CELL_PRIMARY), ("fallback", CELL_FALLBACK)):
        if not len(ta):
            out[name] = 0
            continue
        rpm, mp, cool, amb = cell_state(run, ta)
        with np.errstate(invalid="ignore"):
            out[name] = int((in_cell(rpm, mp, cell) & (cool >= SEG_COOL) & np.isfinite(amb)).sum())
    return out


def report_b(lines, fz):
    say(lines, f"valid primary steps N {fz['N']} in blocks {fz['blocks']}; excluded for B (n_B) {fz['n_B']}")
    if fz["cuts"]:
        c = fz["cuts"]
        say(lines, f"cuts (drive_c_rule_numbers.cuts, frozen): pulls if K >= {c['k_yes']}, does not if "
                   f"K <= {c['k_no']} (false pulls {100 * c['false_pulls']:.1f} %, false does-not "
                   f"{100 * c['false_does_not']:.1f} %)")
    if fz["cuts_with_B"]:
        say(lines, f"cut for N + n_B, blocks {fz['blocks_with_B']}: does not if K + n_B <= {fz['cuts_with_B']['k_no']}")
    say(lines, f"valid shams {fz['valid_shams']} (24 needed); late-window pairs median {fz['late_pairs_median']}")
    say(lines, f"item 8 cell: {fz['cell']} ({fz['cell_reason']}); stage B's own count picks "
               f"{fz['cell_stage_b_check']}")
    if not fz["c2_testable"]:
        say(lines, f"C2 IS UNTESTED SO FAR: {fz['N']} valid primary steps, 16 needed. Stage C will refuse.")


# ==== statistics ===============================================================
def cp_interval(k, n, level=CI_LEVEL):
    from scipy.stats import beta
    if n == 0:
        return None, None
    a = (1 - level) / 2
    lo = 0.0 if k == 0 else float(beta.ppf(a, k, n - k + 1))
    hi = 1.0 if k == n else float(beta.ppf(1 - a, k + 1, n - k))
    return lo, hi


def fisher_greater(k1, n1, k2, n2):
    """One-sided Fisher exact: the first group pulls more often than the second."""
    from scipy.stats import fisher_exact
    if n1 == 0 or n2 == 0:
        return None
    return float(fisher_exact([[k1, n1 - k1], [k2, n2 - k2]], alternative="greater")[1])


def holm(ps, alpha=ALPHA):
    """Holm over the whole family (IC41): a p that could not be computed still counts as one test,
    never significant, so the family does not shrink and the other test keeps alpha / 2."""
    m = len(ps)
    items = sorted((p, name) for name, p in ps.items() if p is not None)
    out, stop = {}, False
    for i, (p, name) in enumerate(items):
        thr = alpha / (m - i)
        sig = (not stop) and p <= thr
        stop = stop or not sig
        out[name] = dict(p=p, threshold=thr, significant=sig)
    for name, p in ps.items():
        if p is None:
            out[name] = dict(p=None, threshold=None, significant=False)
    return out


def turnbull(intervals, tol=1e-9, max_iter=20000):
    """The NPMLE for interval-censored data (L, R], by self-consistency over Turnbull's
    innermost intervals. Returns the innermost intervals and their masses."""
    L = np.array([float(x[0]) for x in intervals])
    R = np.array([float(x[1]) for x in intervals])
    ev = sorted([(x, 1) for x in L] + [(x, 0) for x in R], key=lambda e: (e[0], e[1]))
    inner = [(p[0], q[0]) for p, q in zip(ev, ev[1:]) if p[1] == 1 and q[1] == 0]
    if not inner:
        return [], np.array([])
    qs = np.array([x[0] for x in inner])
    ps = np.array([x[1] for x in inner])
    A = ((L[:, None] <= qs[None, :]) & (ps[None, :] <= R[:, None])).astype(float)
    s = np.full(len(inner), 1.0 / len(inner))
    for _ in range(max_iter):
        d = A @ s
        new = s * (A.T @ (1.0 / d)) / len(L)
        if np.max(np.abs(new - s)) < tol:
            s = new
            break
        s = new
    return inner, s


def turnbull_median(intervals):
    """IC28: the median, interpolated inside its innermost interval, with that interval. Where the
    estimated F comes within TB_TOL of 1/2 at the end of an innermost interval (a flat at one half,
    which the EM approaches slowly and never reaches exactly), the median set is that interval, the
    gap and the next one together, and the point is the gap's midpoint."""
    if not intervals:
        return dict(identified=False, point=None, lo=None, hi=None, reason="no segment")
    inner, s = turnbull(intervals)
    cum = np.cumsum(s)
    j = min(int(np.searchsorted(cum, 0.5 - TB_TOL)), len(inner) - 1)       # first F >= 1/2 - tol
    k = j
    while k + 1 < len(inner) and cum[k] <= 0.5 + TB_TOL:                      # last whose F before is <= 1/2 + tol
        k += 1
    q, p = inner[j]
    prev = float(cum[j - 1]) if j else 0.0
    if k > j:
        lo, hi = q, inner[k][1]
        a, b = p, inner[k][0]
        point = 0.5 * (a + b) if np.isfinite(a) and np.isfinite(b) else None
    else:
        lo, hi = q, p
        point = (q + (0.5 - prev) / s[j] * (p - q)) if np.isfinite(q) and np.isfinite(p) else None
    ident = bool(np.isfinite(lo) and np.isfinite(hi))
    reason = ""
    if not ident:
        reason = (f"onset above {lo:.3f}" if not np.isfinite(hi) else f"onset below {hi:.3f}")
    return dict(identified=ident, point=None if point is None else float(point), lo=float(lo), hi=float(hi),
                reason=reason)


def boot_median(intervals, n=BOOT_N, seed=BOOT_SEED):
    """Item 7: whole segments resampled; an unidentified resample counts as +-inf (IC28)."""
    rng = np.random.default_rng(seed)
    k = len(intervals)
    meds = np.empty(n)
    for b in range(n):
        idx = rng.integers(0, k, k)
        m = turnbull_median([intervals[i] for i in idx])
        if m["identified"]:
            meds[b] = m["point"]
        else:
            meds[b] = np.inf if not np.isfinite(m["hi"]) else -np.inf
    lo = float(np.quantile(meds, 0.025, method="lower"))
    hi = float(np.quantile(meds, 0.975, method="higher"))
    h = (hi - lo) / 2 if np.isfinite(lo) and np.isfinite(hi) else float("inf")
    return dict(n=n, seed=seed, lo=lo, hi=hi, h=h)


def logistic(x, y, iters=100):
    """Item 7's secondary: P(retard >= 2.25 deg) against KI, by Newton-Raphson."""
    x, y = np.asarray(x, float), np.asarray(y, float)
    if len(x) < 3 or y.min() == y.max():
        return dict(fitted=False, reason="every pair on one side", n=int(len(x)))
    X = np.column_stack([np.ones_like(x), x])
    b = np.zeros(2)
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ b, -50, 50)))
        w = p * (1 - p)
        H = X.T @ (X * w[:, None]) + 1e-9 * np.eye(2)
        step = np.linalg.solve(H, X.T @ (y - p))
        b = b + step
        if np.max(np.abs(b)) > 1e3:
            return dict(fitted=False, reason="separated: the pairs split cleanly by KI", n=int(len(x)))
        if np.max(np.abs(step)) < 1e-9:
            break
    ki50 = float(-b[0] / b[1]) if b[1] > 0 else None
    return dict(fitted=True, b0=float(b[0]), b1=float(b[1]), ki50=ki50, n=int(len(x)))


def dersimonian_laird(groups):
    """IC30: random effects across sessions; each group a list of segment values."""
    means = np.array([np.mean(g) for g in groups])
    ns = np.array([len(g) for g in groups], float)
    floor = COUNT ** 2 / 12.0
    pooled = [v - np.mean(g) for g in groups for v in g]
    pooled_var = float(np.var(pooled, ddof=len(groups))) if len(pooled) > len(groups) else floor
    var = np.array([max(np.var(g, ddof=1) if len(g) > 1 else pooled_var, floor) for g in groups]) / ns
    w = 1.0 / var
    mw = float(np.sum(w * means) / np.sum(w))
    q = float(np.sum(w * (means - mw) ** 2))
    c = float(np.sum(w) - np.sum(w ** 2) / np.sum(w))
    tau2 = max(0.0, (q - (len(groups) - 1)) / c) if c > 0 else 0.0
    ws = 1.0 / (var + tau2)
    return dict(E=float(np.sum(ws * means) / np.sum(ws)), u_D=float(math.sqrt(1.0 / np.sum(ws))),
                tau2=tau2, sessions=[dict(E=float(m), n=int(n)) for m, n in zip(means, ns)])


def plan_label(e, two_u, r):
    """results/VALIDATION_PLAN.md section 7, k = 2, in its order (off, untested, validated, limited)."""
    if abs(e) - two_u > r:
        return "off"
    if two_u > r:
        return "untested"
    if abs(e) + two_u <= r:
        return "validated"
    return "limited"


def knee_decision(med, n_confirmed, h, halves):
    """Item 7's rule, as a function of its inputs."""
    two_u = math.sqrt(h ** 2 + (2 * U_INPUT_KI) ** 2) if np.isfinite(h) else float("inf")
    thr = max(R_K, two_u)
    out = dict(two_u_val=two_u, threshold=thr, retune=False, new_knee=None)
    if n_confirmed < ONSETS_MIN:
        out.update(status="untested", why=f"{n_confirmed} confirmed onsets, {ONSETS_MIN} needed")
        return out
    if not med["identified"]:
        out.update(status="untested", why=f"the median is not identified inside the observed range: {med['reason']}")
        return out
    if halves.get("limited"):
        out.update(status="limited", why=halves["why"])
        return out
    lo, hi = med["lo"], med["hi"]
    beyond = (lo - KNEE > thr) or (KNEE - hi > thr)
    if beyond:
        out.update(status="retune", retune=True, new_knee=round(med["point"], 2),
                   why=f"|median - 0.85| beyond max(0.10, 2 u_val) = {thr:.3f} over the whole median interval")
    else:
        out.update(status="no retune", why=f"the median interval [{lo:.3f}, {hi:.3f}] is not beyond "
                                           f"0.85 +- {thr:.3f} on one side")
    ecu_off = (lo - ECU_KNEE > thr) or (ECU_KNEE - hi > thr)
    out["ecu_threshold_off"] = bool(ecu_off)
    return out


def spark_decision(e_main, u_d, u_al, n_seg, e_pooled=None, dry_ok=True):
    """Item 8's action rule (separate from the label)."""
    u_input = math.sqrt(u_al ** 2 + U_CHARGE_DEG ** 2)
    two_u = 2 * math.sqrt(u_d ** 2 + u_input ** 2)
    thr = max(R_SPARK, two_u)
    out = dict(u_input=u_input, two_u_val=two_u, threshold=thr,
               label=plan_label(e_main, two_u, R_SPARK), label_plan_1p3=plan_label(e_main, two_u, PLAN_R_SPARK),
               action_plan_1p3=bool(abs(e_main) > max(PLAN_R_SPARK, two_u)), retune=False, offset=None)
    if not dry_ok:
        out.update(status="untested", why="the legacy dry run did not reproduce -3.81 / 2.07 / -1.78")
        return out
    if n_seg < SEGS_MIN:
        out.update(status="untested", why=f"{n_seg} counting segments, {SEGS_MIN} needed")
        return out
    ok = abs(e_main) > thr
    if e_pooled is not None:
        ok = ok and abs(e_pooled) > thr and np.sign(e_pooled) == np.sign(e_main)
    if ok:
        out.update(status="retune", retune=True, offset=round(float(e_main), 2),
                   why=f"|E| {abs(e_main):.2f} > max(0.85, 2 u_val) = {thr:.2f}: add E to base_spark at >= 140 kPa")
    else:
        out.update(status="no retune", why=f"|E| {abs(e_main):.2f} <= max(0.85, 2 u_val) = {thr:.2f}")
    return out


# ==== the legacy dry run (item 8) ================================================
def legacy_spark(readings):
    """car_spark_boost.py's per-reading statistics, through this script's model schedule."""
    rpm = np.array([r["rpm"] for r in readings], float)
    mp = np.array([r["map_kpa"] for r in readings], float)
    model = np.array([model_spark(r["rpm"], r["map_kpa"], r["t_amb"], r["ect_c"]) for r in readings])
    car = np.array([r["spark"] for r in readings], float)
    win = (rpm >= 2000.0) & (rpm <= 4000.0) & (mp >= 140.0) & (mp <= 240.0)
    d = (car - model)[win]
    cell = in_cell(rpm, mp, CELL_PRIMARY)[win]
    se = 1.2533 * d.std(ddof=1) / math.sqrt(len(d)) if len(d) > 1 else float("nan")
    return dict(n=int(len(d)), median=round(float(np.median(d)), 2), se=round(float(se), 2),
                cell_n=int(cell.sum()), cell_median=round(float(np.median(d[cell])), 2) if cell.any() else None,
                max_model_vs_committed=float(np.max(np.abs(model - np.array([r.get("model", np.nan) for r in readings])))))


def dry_run_spark(lines=None):
    lines = [] if lines is None else lines
    if not os.path.exists(LEGACY_JSON):
        say(lines, f"dry run: {LEGACY_JSON} missing")
        return dict(ok=False, reason="car_spark_boost.json missing")
    with open(LEGACY_JSON, encoding="utf-8") as fh:
        readings = json.load(fh)["readings"]
    r = legacy_spark(readings)
    got = (r["median"], r["se"], r["cell_median"])
    ok = got == LEGACY_EXPECT
    say(lines, f"dry run (legacy, car_spark_boost.py's committed readings): {r['median']:+.2f} / "
               f"{r['se']:.2f} over {r['n']} readings, {r['cell_median']:+.2f} in the climb's cell "
               f"({r['cell_n']}); expected -3.81 / 2.07 and -1.78 -> {'REPRODUCED' if ok else 'NOT REPRODUCED'}")
    r.update(ok=bool(ok), expected=list(LEGACY_EXPECT))
    return r


# ==== stage C ==================================================================
def committed(path):
    """Guard 4: the file is tracked by git and unchanged against HEAD (read-only git)."""
    try:
        rel = os.path.relpath(os.path.abspath(path), HERE)
        a = subprocess.run(["git", "ls-files", "--error-unmatch", "--", rel], cwd=HERE,
                           capture_output=True, text=True, timeout=30)
        b = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", rel], cwd=HERE,
                           capture_output=True, text=True, timeout=30)
        return a.returncode == 0 and b.returncode == 0
    except (OSError, subprocess.SubprocessError, ValueError):
        return False


def read_hash(path):
    with open(path, encoding="utf-8") as fh:
        tok = fh.read().split()
    return tok[0].lower() if tok else ""


def stage_c(frozen_path, hash_path, logs_dir=None):
    """Stage C: every check first, then the marker, then the response windows, once (guard 5).
    It always writes beside the frozen list it reads (IC33)."""
    lines = []
    plant = plant_check()
    for p in (frozen_path, hash_path):
        if not os.path.exists(p):
            raise SystemExit(f"REFUSED: {p} does not exist; stage C reads the committed frozen list and its hash file")
    got = sha256_file(frozen_path)
    want = read_hash(hash_path)
    if got != want:
        raise SystemExit(f"REFUSED: the frozen list's SHA-256 is {got}; the hash file says {want}")
    for p in (frozen_path, hash_path):
        if not committed(p):
            raise SystemExit(f"REFUSED: {p} is not committed (tracked and unchanged against HEAD); "
                             "guard 4 commits the frozen list and its hash before stage C")
    require_committed_code("stage C")
    fz = load_stage(frozen_path, "B")
    if fz["code_sha"] != code_sha():
        raise SystemExit("REFUSED: drive_c_analysis.py or drive_c_rule_numbers.py changed since the freeze")
    if fz["plant_sha"] != PLANT_SHA or fz["derived_sha"] != DERIVED_SHA:
        raise SystemExit("REFUSED: the frozen list was made on another plant")
    out_dir = os.path.dirname(os.path.abspath(frozen_path))
    here = stage_c_started(out_dir)
    if here:
        raise SystemExit(f"REFUSED: {out_dir} holds {', '.join(here)}; stage C runs once (guard 5)")
    paths = [resolve_log(fd, logs_dir) for fd in fz["files"]]       # every frozen log, read or not
    shas = [fd["sha256"] for fd in fz["files"]]
    earlier = earlier_stage_c([RESULTS_ROOT, out_dir], shas)
    if earlier:
        raise SystemExit("REFUSED: stage C has already run on one of these logs (guard 5: it runs once on every "
                         "drive C file): " + ", ".join(earlier))
    if fz["N"] < N_MIN:
        raise SystemExit(f"REFUSED: {fz['N']} valid primary steps, {N_MIN} needed. Item 5: below 16 C2 is "
                         "untested and stage C is not run (C1 included); a shortfall is made up by more "
                         "driving, then stages A and B again (guard 5)")
    # IC33: the frozen list is what this code computes from these logs, checked before any response window
    sa_now = compute_stage_a([(p, fd["role"]) for p, fd in zip(paths, fz["files"])], plant)
    fz_now = compute_stage_b(sa_now, paths, plant)
    diff = first_difference(canon(fz_now), canon(fz))
    if diff:
        raise SystemExit(f"REFUSED: the frozen list is not what this code computes from these logs (first "
                         f"difference at {diff}); nothing was read beyond the pre-windows")
    marker = os.path.join(out_dir, MARKER)
    try:          # guard 5: from here on a second run is refused, whether or not this one finishes
        with open(marker, "x", encoding="utf-8", newline="\n") as fh:
            json.dump(dict(frozen_sha256=got, log_sha256=shas, code_sha=fz["code_sha"],
                           started=datetime.now().isoformat(timespec="seconds")), fh, indent=1, sort_keys=True)
            fh.write("\n")
    except FileExistsError:
        raise SystemExit(f"REFUSED: {marker} exists; stage C runs once (guard 5)")
    say(lines, "DRIVE C RESULT -- results/DRIVE_C_RULE.md, stage C (python drive_c_analysis.py stage-c)")
    say(lines, f"frozen list sha256 {got}; plant_sha {plant['plant_sha']}; derived_sha {plant['derived_sha']}; "
               f"code {fz['code_sha']}")
    shown = io.StringIO()
    with contextlib.redirect_stdout(shown):       # the result is written before any of it is shown
        loaded = []
        for fd, path in zip(fz["files"], paths):
            lf, t, _, runs_info, runs = reopen(fd, path)
            text = load_ignition_text(lf)
            ign = ignition_genuine(lf, runs_info, text, None) if text is not None else None
            phase_bad = phase_check(lf, runs_info, text) if text is not None else {}
            loaded.append(dict(lf=lf, t=t, runs=runs, ign=ign, phase_bad=phase_bad))
        c1 = c1_analysis(fz, loaded)
        c2 = c2_analysis(fz, loaded, c1)
        dry = dry_run_spark([])
        spark = spark_analysis(fz, loaded, dry)
        out = dict(schema=SCHEMA, stage="C", created=datetime.now().isoformat(timespec="seconds"),
                   frozen_sha256=got, log_sha256=shas, **plant, code_sha=fz["code_sha"], git_head=git_head(),
                   C2=c2, C1_knee=c1["knee"], C1_spark=spark, dry_run=dry)
        out["combined"] = combined(out, fz)
        report_c(lines, out, fz)
    res_path = os.path.join(out_dir, RESULT)
    with open(res_path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(clean(out), fh, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(out_dir, "DRIVE_C_RESULT.txt"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    for s in shown.getvalue().splitlines():
        echo(s)
    echo(f"\nwrote {res_path}")
    return out


def phase_check(lf, runs_info, text):
    """IC34: per run, the share of each ignition channel's value changes on its poll rows."""
    bad = {}
    for k in IGN:
        s = text[k]
        poll = poll_mask(len(s), runs_info, lf.pos[k], lf.N)
        for j, ri in enumerate(runs_info):
            if ri["flagged"]:
                continue
            a = s[ri["start"]:ri["end"] + 1]
            ch = np.flatnonzero(a[1:] != a[:-1]) + ri["start"] + 1
            if len(ch) and np.mean(poll[ch]) < PHASE_SHARE:
                bad[j] = True
    return bad


def run_of(loaded, x):
    d = loaded[x["file"]]
    return d, d["runs"][x["run"]]


def pairs_for(d, run, cache):
    key = (id(d), run.index)
    if key not in cache:
        cache[key] = run_pairs(run, d["ign"], with_values=True)
    return cache[key]


def step_result(x, pr, b):
    """Item 3 for one step: the late window decides, the early window is reported."""
    late = pr.take(pr.inside(*x["L"]))
    early = pr.take(pr.inside(*x["E"]))
    dl = late.retard - b if len(late) else np.array([])
    de = early.retard - b if len(early) else np.array([])
    max_l = float(dl.max()) if len(dl) else None
    max_e = float(de.max()) if len(de) else None
    unreadable = bool(len(dl) and max_l > UNREADABLE)                  # IC7: angles compared exactly
    short = len(late) < L_MIN_PAIRS
    pull = bool(not unreadable and not short and max_l >= PULL)
    early_pull = bool(max_e is not None and PULL <= max_e <= UNREADABLE)
    if unreadable or short:
        timing = "unreadable"
    elif pull and early_pull:
        timing = "early and late"
    elif pull:
        timing = "late"
    elif early_pull:
        timing = "early only"
    else:
        timing = "none"
    return dict(n_L=int(len(late)), n_E=int(len(early)), max_L=max_l, max_E=max_e, pull=pull,
                unreadable=bool(unreadable or short), short=bool(short), early_pull=early_pull, timing=timing)


def c2_analysis(fz, loaded, c1):
    steps = [s for s in fz["steps"] if s.get("valid_primary")]
    side = [s for s in fz["steps"] if s.get("stage_b_valid") and s["set"] == "side"]
    cache = {}
    bad_phase = False
    per = []
    for s in steps + side:
        d, run = run_of(loaded, s)
        if d["phase_bad"].get(run.index):
            bad_phase = True
        pr = pairs_for(d, run, cache)
        p = pr.take(pr.inside(*s["P"]))
        b = lower_median(p.retard) if len(p) else None
        if b is None or abs(b - s["stage_b"]["B"]) > 1e-9:
            raise SystemExit(f"REFUSED: step {s['id']}'s baseline differs from the frozen one")
        r = step_result(s, pr, b)
        late = pr.take(pr.inside(*s["L"]))
        rpm, mp, _, _ = cell_state(run, late.ta) if len(late) else (np.array([]),) * 4
        with np.errstate(invalid="ignore"):
            band = (rpm >= SS_RPM[0]) & (rpm <= SS_RPM[1]) & (mp >= SS_MAP) if len(late) else np.array([], bool)
        r["n_L_band"] = int(band.sum())
        r["pull_band"] = bool(band.any() and float((late.retard[band] - b).max()) >= PULL)
        r.update(id=s["id"], file=s["file"], block=s.get("block"), set=s["set"], B=b, t0=s["t0"], t1=s["t1"],
                 amb_pre=s["amb_pre"], large=s["large"], KI1=s["KI1"])
        per.append(r)
    prim = [r for r in per if r["set"] == "primary"]
    readable = [r for r in prim if not r["unreadable"]]
    n_frozen, u = len(prim), sum(1 for r in prim if r["unreadable"])
    k = sum(1 for r in readable if r["pull"])
    n = len(readable)
    k_e = sum(1 for r in readable if r["early_pull"])
    # the cuts: frozen, and for what remains (IC16)
    of = {s["id"]: s["block"] for s in steps}
    rem = [0] * len(fz["blocks"])
    for r in readable:
        rem[of[r["id"]]] += 1
    cut_f, cut_r = fz["cuts"], cut_pair(rem)
    k_yes = max(cut_f["k_yes"], cut_r["k_yes"]) if cut_r else cut_f["k_yes"]
    k_no = min(cut_f["k_no"], cut_r["k_no"]) if cut_r else -1
    # n_B robustness, on the blocks frozen for N + n_B
    nb_steps = [s for s in fz["steps"] if s.get("excluded_for_B")]
    nb = len(nb_steps)
    rem_b = [0] * len(fz["blocks_with_B"])
    for s in nb_steps:
        rem_b[s["block_with_B"]] += 1
    for r in readable:
        rem_b[next(s for s in steps if s["id"] == r["id"])["block_with_B"]] += 1
    cut_bf = fz["cuts_with_B"]
    cut_br = cut_pair(rem_b)
    k_no_b = min(cut_bf["k_no"], cut_br["k_no"]) if (cut_bf and cut_br) else -1
    robust = (k + nb) <= k_no_b
    # shams
    shams = [h for h in fz["shams"] if h.get("valid")]
    sres = []
    for h in shams:
        d, run = run_of(loaded, h)
        if d["phase_bad"].get(run.index):
            bad_phase = True
        pr = pairs_for(d, run, cache)
        p = pr.take(pr.inside(*h["P"]))
        b = lower_median(p.retard) if len(p) else None
        if b is None or abs(b - h["stage_b"]["B"]) > 1e-9:
            raise SystemExit(f"REFUSED: sham {h['id']}'s baseline differs from the frozen one")
        w = pr.take(pr.inside(*h["window"]))
        dw = w.retard - b if len(w) else np.array([])
        mx = float(dw.max()) if len(dw) else None
        short = len(w) < L_MIN_PAIRS
        unread = bool(mx is not None and mx > UNREADABLE)
        sres.append(dict(id=h["id"], anchor=h["anchor"], B=b, n=int(len(w)), max=mx, short=bool(short),
                         unreadable=unread, pull=bool(not short and (unread or mx >= PULL))))
    sv = [x for x in sres if not x["short"]]
    ks, ns = sum(1 for x in sv if x["pull"]), len(sv)
    p_sham = fisher_greater(k, n, ks, ns)
    chan = c1["channel"]
    ci = cp_interval(k, n)
    # the verdict (item 4)
    reasons = []
    if bad_phase:
        verdict, reasons = "inconclusive (poll phase)", ["an ignition channel's changes are off its poll rows (IC34)"]
    elif u > UNREADABLE_SHARE * n_frozen:
        verdict, reasons = "inconclusive (unreadable)", [f"{u} of {n_frozen} valid steps unreadable (more than 1 in 4)"]
    elif n < N_MIN:
        verdict, reasons = "untested", [f"{n} readable valid steps, {N_MIN} needed (IC16)"]
    elif ns < SHAMS_MIN:
        verdict, reasons = "inconclusive (shams)", [f"{ns} valid shams, {SHAMS_MIN} needed (IC20)"]
    elif k >= k_yes:
        if p_sham is not None and p_sham <= ALPHA:
            verdict = "pulls"
        else:
            verdict, reasons = "inconclusive (shams)", [f"K {k} reaches the cut {k_yes} but the steps do not pull "
                                                        f"more often than the shams (Fisher p {p_sham})"]
    elif k <= k_no:
        tags = []
        if not chan["passes"]:
            tags.append("channel")
            reasons.append(chan["why"])
        if not robust:
            tags.append("baseline")
            reasons.append(f"with the {nb} steps excluded for B counted as pulls, K + n_B = {k + nb} "
                           f"exceeds the cut {k_no_b} for N + n_B")
        verdict = "does not" if not tags else f"inconclusive ({', '.join(tags)})"
    else:
        verdict = "inconclusive"
        reasons = [f"K {k} lies between the cuts {k_no} and {k_yes}"]
    # K per block
    per_block = {}
    for r in prim:
        bl = per_block.setdefault(r["block"], dict(block=r["block"], steps=0, readable=0, pulls=0))
        bl["steps"] += 1
        bl["readable"] += 0 if r["unreadable"] else 1
        bl["pulls"] += 1 if r["pull"] else 0
    # what the verdict triggers
    ss = step_specific(readable, c1, fz)
    remedy = None
    if verdict == "does not":
        remedy = "d" if k_e >= k_yes else "a"
    elif verdict == "pulls":
        remedy = "c" if ss["step_specific"] else "b"
    early_vals = [r["max_E"] for r in readable if r["early_pull"]]
    sec_size = secondary(readable, "large")
    sec_amb = secondary_ambient(readable)
    hm = holm({"size": sec_size.get("p"), "ambient": sec_amb.get("p")})
    ambs = [r["amb_pre"] for r in readable]
    return dict(
        verdict=verdict, reasons=[x for x in reasons if x], N_frozen=n_frozen, unreadable=u, N=n, K=k,
        K_over_N=(k / n) if n else None, ci90=ci, K_early=k_e,
        cuts_frozen=cut_f, cuts_remaining=cut_r, k_yes=k_yes, k_no=k_no,
        n_B=nb, cuts_with_B_frozen=cut_bf, cuts_with_B_remaining=cut_br, k_no_with_B=k_no_b, robust_to_B=robust,
        shams=dict(valid=len(shams), scored=ns, pulls=ks, rate=(ks / ns) if ns else None, fisher_p=p_sham,
                   per=sres, false_pulls_at_day_q=(       # the blocks that remain and the cut applied (S7)
                       float(RN.pmf_k([b for b in rem if b], RN.p_step(0.0, ks / ns, M_RULE), ICC_RULE)[k_yes:].sum())
                       if ns and any(rem) else None)),
        channel=chan, per_block=[per_block[i] for i in sorted(per_block)], steps=per,
        step_specific=ss, remedy=remedy, remedy_text=REMEDY.get(remedy),
        median_early_pull=float(np.median(early_vals)) if early_vals else None,
        secondary=dict(size=sec_size, ambient=sec_amb, holm=hm),
        ambient_range=[min(ambs), max(ambs)] if ambs else None)


REMEDY = {
    "a": "schedule the baseline ECU's spark on the current step's load",
    "b": "the same remedy as (a); C2's late readings are reported beside C1's knee",
    "c": "keep a load-step knock cost, sized with C1's knee",
    "d": "current-load spark plus at most a brief protective retard (the median early pull, for at most 1 s); "
         "never knock damage",
}


def secondary(rows, field):
    """Item 6b: a one-sided Fisher test, "large" against "moderate" steps."""
    a = [r for r in rows if r[field]]
    b = [r for r in rows if not r[field]]
    ka, kb = sum(r["pull"] for r in a), sum(r["pull"] for r in b)
    return dict(n_large=len(a), pulls_large=ka, n_moderate=len(b), pulls_moderate=kb,
                p=fisher_greater(ka, len(a), kb, len(b)))


def secondary_ambient(rows):
    """IC24: warm against cool, split at the median pre-window ambient."""
    if not rows:
        return dict(p=None)
    med = float(np.median([r["amb_pre"] for r in rows]))
    w = [r for r in rows if r["amb_pre"] > med]
    c = [r for r in rows if r["amb_pre"] <= med]
    kw, kc = sum(r["pull"] for r in w), sum(r["pull"] for r in c)
    return dict(split_c=med, n_warm=len(w), pulls_warm=kw, n_cool=len(c), pulls_cool=kc,
                p=fisher_greater(kw, len(w), kc, len(c)))


def step_specific(readable, c1, fz):
    """What each verdict triggers: C2's in-band late pull rate against C1 windows (IC22)."""
    c2_side = [r for r in readable if r["n_L_band"] > 0]
    k2 = sum(1 for r in c2_side if r["pull_band"])
    bs = [r["B"] for r in readable]
    b_c1 = min(0.0, lower_median(bs)) if bs else 0.0
    n_med = fz["late_pairs_median"]
    wins = []
    for w in c1["windows_raw"]:
        if n_med is None or len(w["retard"]) < n_med:
            continue
        r = np.asarray(w["retard"][:n_med]) - b_c1
        wins.append(dict(segment=w["segment"], amb=w["amb"], max=float(r.max()),
                         pull=bool(float(r.max()) >= PULL)))         # above 12 deg is >= 2.25 too (IC22)
    k1 = sum(1 for w in wins if w["pull"])
    amb2 = float(np.median([r["amb_pre"] for r in c2_side])) if c2_side else None
    amb1 = float(np.median([w["amb"] for w in wins if w["amb"] is not None])) if wins else None
    p = fisher_greater(k2, len(c2_side), k1, len(wins))
    ok_n = len(c2_side) >= SS_MIN and len(wins) >= SS_MIN
    ok_amb = amb1 is not None and amb2 is not None and abs(amb1 - amb2) <= SS_AMB_K
    spec = bool(ok_n and ok_amb and p is not None and p <= ALPHA)
    return dict(c2_steps=len(c2_side), c2_pulls=k2, c1_windows=len(wins), c1_pulls=k1, baseline_c1=b_c1,
                pairs_per_window=n_med, amb_c2=amb2, amb_c1=amb1, fisher_p=p, enough=ok_n, ambient_match=ok_amb,
                step_specific=spec, windows=wins)


def segment_pairs(d, run, g, cache):
    """A segment's pairs (readings inside [s0, end]), with speed, MAP and temperatures at the actual."""
    pr = pairs_for(d, run, cache)
    p = pr.take(pr.inside(g["s0"], g["end"], left_open=False))
    rpm, mp, cool, amb = cell_state(run, p.ta) if len(p) else (np.array([]),) * 4
    return p, rpm, mp, cool, amb


def c1_analysis(fz, loaded):
    """Item 7 and the channel check; also the C1 windows the step-specific test needs."""
    segs = [g for g in fz["segments"] if g["counting"] and not g["D1_flagged"] and g["v8_ok"]]
    cache = {}
    rows, windows, onsets = [], [], []
    bad_phase = False
    logit_x, logit_y = [], []
    for g in segs:
        d, run = run_of(loaded, g)
        if d is None or d["ign"] is None:
            continue
        if d["phase_bad"].get(run.index):
            bad_phase = True
        p, rpm, mp, cool, amb = segment_pairs(d, run, g, cache)
        if not len(p):
            rows.append(dict(id=g["id"], cls="no pairs", interval=None))
            continue
        ki = lambda i: knock_integral(float(rpm[i]), float(mp[i]), float(amb[i]), float(cool[i]), float(p.target[i]))
        elig = np.flatnonzero(rpm <= ONSET_RPM_MAX)
        for i in range(len(p)):                   # item 7's secondary: over all pairs (IC40)
            v = ki(i)
            if np.isfinite(v):
                logit_x.append(v)
                logit_y.append(1.0 if p.retard[i] >= PULL else 0.0)
        # the C1 window for the step-specific comparison (IC22)
        with np.errstate(invalid="ignore"):
            band = np.flatnonzero((p.ta >= g["s0"] + SS_START_S) & (rpm >= SS_RPM[0]) & (rpm <= SS_RPM[1])
                                  & (mp >= SS_MAP))
        windows.append(dict(segment=g["id"], amb=g.get("amb_median"), retard=p.retard[band].tolist()))
        rows.append(knee_segment(g, p, rpm, ki, elig, onsets))
    usable = [r for r in rows if r.get("interval") is not None and not any(np.isnan(x) for x in r["interval"])]
    inter = [r["interval"] for r in usable]
    med = turnbull_median(inter)
    boot = boot_median(inter) if inter else dict(h=float("inf"))
    conf = confirmed_onsets(onsets)
    lows = [r["interval"] for r in usable if r["rpm"] <= HALF_SPLIT]
    highs = [r["interval"] for r in usable if r["rpm"] > HALF_SPLIT]
    m_lo, m_hi = turnbull_median(lows), turnbull_median(highs)
    halves = dict(low=m_lo, high=m_hi, n_low=len(lows), n_high=len(highs))
    if not (m_lo["identified"] and m_hi["identified"]):
        halves.update(limited=True, why="the two speed halves cannot both be estimated (IC29)")
    elif abs(m_lo["point"] - m_hi["point"]) > HALVES_MAX:
        halves.update(limited=True, why=f"2000-2650 and 2650-3300 rpm medians {m_lo['point']:.3f} and "
                                        f"{m_hi['point']:.3f} differ by more than 0.10")
    else:
        halves.update(limited=False, why="")
    dec = knee_decision(med, len(conf), boot["h"], halves)
    if bad_phase:
        dec.update(status="untested", retune=False, new_knee=None, why="poll phase (IC34)")
    persist = [o for o in conf if o["persists"]]
    v_hat = visibility(conf)
    n_med = fz.get("late_pairs_median")
    amb = [g.get("amb_median") for g in segs if g.get("amb_median") is not None]
    chan_pass = len(conf) >= CHAN_ONSETS and len(persist) >= CHAN_PERSIST
    knee = dict(segments=len(segs), rows=rows, onsets=onsets, confirmed=len(conf),
                confirmed_any=sum(1 for o in onsets if o["confirmed"]), persisting=len(persist),
                median=med, bootstrap=boot, u_D=boot["h"] / 2 if np.isfinite(boot["h"]) else float("inf"),
                u_input=U_INPUT_KI, u_num=0.0, halves=halves, decision=dec,
                logistic=logistic(logit_x, logit_y), visibility=v_hat,
                miss_rate_implied=((1 - v_hat) ** n_med) if (v_hat is not None and n_med) else None,
                ambient_range=[min(amb), max(amb)] if amb else None)
    chan = dict(passes=bool(chan_pass and not bad_phase), confirmed=len(conf), persisting=len(persist),
                why=f"{len(conf)} confirmed C1 onsets ({CHAN_ONSETS} needed), {len(persist)} persisting "
                    f"({CHAN_PERSIST} needed)")
    return dict(knee=knee, channel=chan, windows_raw=windows)


def confirmed_onsets(onsets):
    """IC27: a confirmed onset counts, toward the 8 and toward the channel check alike, only when
    its K* and the KI of its last quiet pair can be computed."""
    return [o for o in onsets if o["confirmed"] and np.isfinite(o.get("K_star", np.nan))
            and np.isfinite(o.get("KI_last_quiet", np.nan))]


def visibility(conf):
    """Section 6.2's v-hat: the share of the pairs after each confirmed onset (up to 3) that show
    it, over the pairs that exist (a segment may end sooner)."""
    n = sum(o["n_next3"] for o in conf)
    return float(sum(o["visible_next3"] for o in conf) / n) if n else None


def knee_segment(g, p, rpm, ki, elig, onsets):
    """Item 7 for one segment (IC26, IC27): the first evidence of retard decides it.
      * a pair before s0 + 5 s (no onset can be read there) at >= 2.25 deg, confirmed by one of the
        next 2 pairs at >= 1.5 deg: retarded from its first pairs, (-inf, KI of that pair];
      * from s0 + 5 s, in time order, the first pair that is a candidate (a quiet window of >= 3
        pairs, all <= 0.75 deg, and retard >= B_seg + 2.25 deg) or that reaches 2.25 deg where no
        quiet window exists ends the scan: a confirmed candidate is the onset (KI of the last quiet
        pair, K*]; a confirmed retard without a quiet window is (-inf, its KI]; unconfirmed, either
        leaves the segment with no confirmed onset;
      * with no confirmed onset, (the highest KI of a quiet pair, anywhere from s0, before the
        first pair at >= 2.25 deg and before the scan's last pair, +inf): after a pull reading the
        engine may be knocking on a cylinder the channel does not show (m 0.45), so a later quiet
        reading proves nothing.
    Angles are compared exactly (IC7); a KI that cannot be computed gives no interval."""
    s0 = g["s0"]
    ta, ret = p.ta, p.retard
    n = len(ta)
    out = dict(id=g["id"], cls="none", interval=None, rpm=None)
    if not len(elig):
        return out
    t_on = s0 + ONSET_AFTER_S - EPS

    def nxt(i, k):
        return list(range(i + 1, min(i + 1 + k, n)))

    def left(i, cls):
        k = ki(i)
        out.update(cls=cls if np.isfinite(k) else cls + " (KI not computable)",
                   interval=(float("-inf"), float(k)) if np.isfinite(k) else None, rpm=float(rpm[i]))
        return out

    for i in elig:                                          # the rule's "retarded from its first pairs"
        if ta[i] >= t_on:
            break
        if ret[i] >= PULL and any(ret[j] >= CONFIRM_DEG for j in nxt(i, 2)):
            return left(int(i), "retarded from its first pairs")
    stop = None
    for i in elig:                                          # the onset scan
        if ta[i] < t_on:
            continue
        lo = max(s0, ta[i] - QUIET_S)
        win = np.flatnonzero((p.tb >= lo - EPS) & (p.tc < ta[i]) & (np.arange(n) < i))
        quiet_win = len(win) >= QUIET_MIN and not np.any(ret[win] > QUIET_MAX)
        if quiet_win:
            b = lower_median(ret[win])
            if not ret[i] >= b + PULL:
                continue
            confirmed = any(ret[j] >= b + CONFIRM_DEG for j in nxt(i, 2))
            n3 = nxt(i, 3)
            vis = sum(1 for j in n3 if ret[j] >= b + CONFIRM_DEG)
            o = dict(segment=g["id"], t=float(ta[i]), rpm=float(rpm[i]), B_seg=b, retard=float(ret[i]),
                     confirmed=bool(confirmed), persists=bool(confirmed and vis >= 2), visible_next3=int(vis),
                     n_next3=len(n3))
            onsets.append(o)
            if confirmed:
                k_star, k_lq = ki(int(i)), ki(int(win[-1]))
                o.update(K_star=k_star, KI_last_quiet=k_lq)
                if not (np.isfinite(k_star) and np.isfinite(k_lq)):
                    out.update(cls="onset (KI not computable)", interval=None, rpm=float(rpm[i]))
                    return out
                a, b2 = (k_lq, k_star) if k_lq < k_star else (min(k_lq, k_star) - 1e-9, max(k_lq, k_star))
                out.update(cls="onset", interval=(float(a), float(b2)), rpm=float(rpm[i]), K_star=k_star)
                return out
            stop = int(i)
            break
        if ret[i] >= PULL:
            if any(ret[j] >= CONFIRM_DEG for j in nxt(i, 2)):
                return left(int(i), "retarded without a quiet baseline")
            stop = int(i)
            break
    pulls = [int(i) for i in elig if ret[i] >= PULL]
    limit = min([ta[x] for x in ([stop] if stop is not None else []) + pulls[:1]], default=float("inf"))
    quiet = [int(i) for i in elig if ta[i] < limit and ret[i] <= QUIET_MAX]
    kis = [(v, i) for v, i in ((ki(i), i) for i in quiet) if np.isfinite(v)]
    if kis:
        v, i = max(kis)
        out.update(cls="no onset" if stop is None else "no confirmed onset",
                   interval=(float(v), float("inf")), rpm=float(rpm[i]))
    return out


def pooled_u(vals):
    """Item 8's u_D for one session, SD / sqrt(n_seg), the variance floored at the 0.75 deg
    grid's (0.75^2 / 12 per segment) as each session's is under random effects (IC30)."""
    n = len(vals)
    if n < 2:
        return float("inf")
    return float(math.sqrt(max(float(np.var(vals, ddof=1)), COUNT ** 2 / 12.0) / n))


def spark_analysis(fz, loaded, dry):
    """Item 8 in the frozen cell."""
    cell = CELL_PRIMARY if fz["cell"] == "primary" else CELL_FALLBACK
    segs = [g for g in fz["segments"] if g["counting"] and not g["D1_flagged"] and g["v8_ok"]]
    per, al, by_file = [], [], {}
    bad_phase = False
    for g in segs:
        d, run = run_of(loaded, g)
        if d is None or d["ign"] is None:
            continue
        if d["phase_bad"].get(run.index):
            bad_phase = True
        act = run_ign(run, d["ign"])["act"]
        sel = (act.t >= g["s0"]) & (act.t <= g["end"])
        ta, av = act.t[sel], act.v[sel]
        if not len(ta):
            continue
        rpm, mp, cool, amb = cell_state(run, ta)
        with np.errstate(invalid="ignore"):
            keep = in_cell(rpm, mp, cell) & (cool >= SEG_COOL) & np.isfinite(amb)
        if keep.sum() < CELL_MIN_READINGS:
            per.append(dict(id=g["id"], n=int(keep.sum()), counts=False))
            continue
        model = np.array([model_spark(float(n), float(m), float(a), float(c))
                          for n, m, a, c in zip(rpm[keep], mp[keep], amb[keep], cool[keep])])
        dev = av[keep] - model
        val = float(np.median(dev))
        per.append(dict(id=g["id"], file=g["file"], n=int(keep.sum()), counts=True, E=val))
        by_file.setdefault(g["file"], []).append(val)
        for x, a_, c_ in zip(ta[keep], amb[keep], cool[keep]):
            al.append(align_term(run, float(x), float(a_), float(c_)))
    vals = [r["E"] for r in per if r.get("counts")]
    n = len(vals)
    al = [x for x in al if np.isfinite(x)]
    u_al = float(math.sqrt(np.mean(np.square(al)))) if al else 0.0
    out = dict(cell=fz["cell"], segments=per, n_segments=n, u_al=u_al, u_charge=U_CHARGE_DEG, u_num=0.0)
    if n == 0:
        out.update(decision=spark_decision(0.0, float("inf"), u_al, 0, dry_ok=dry.get("ok", False)), E=None)
        return out
    e_pool, u_pool = float(np.mean(vals)), pooled_u(vals)
    out.update(E_pooled=e_pool, u_D_pooled=u_pool)
    if len(by_file) > 1:
        re_ = dersimonian_laird([by_file[k] for k in sorted(by_file)])
        out.update(random_effects=re_, E=re_["E"], u_D=re_["u_D"])
        dec = spark_decision(re_["E"], re_["u_D"], u_al, n, e_pooled=e_pool, dry_ok=dry.get("ok", False))
    else:
        out.update(E=e_pool, u_D=u_pool)
        dec = spark_decision(e_pool, u_pool, u_al, n, dry_ok=dry.get("ok", False))
    if bad_phase:
        dec.update(status="untested", retune=False, offset=None, why="poll phase (IC34)")
    out["decision"] = dec
    amb = [g.get("amb_median") for g in segs if g.get("amb_median") is not None]
    out["ambient_range"] = [min(amb), max(amb)] if amb else None
    return out


def align_term(run, x, amb, cool):
    """IC31: half the change in model spark between the neighbouring genuine readings."""
    r = run.r
    vals = []
    for side in ("before", "after"):
        out = []
        for k in ("rpm", "air"):
            t = r[k].t
            j = (np.searchsorted(t, x, side="right") - 1) if side == "before" else np.searchsorted(t, x, side="left")
            out.append(float(r[k].v[j]) if 0 <= j < len(t) else float("nan"))
        rpm, air = out
        vals.append(model_spark(rpm, inv_map(air, rpm, amb, cool), amb, cool))
    return abs(vals[1] - vals[0]) / 2.0


def combined(out, fz):
    c2, knee, sp = out["C2"], out["C1_knee"], out["C1_spark"]
    s = []
    s.append(f"C2: {c2['verdict']}" + (f" ({'; '.join(c2.get('reasons', []))})" if c2.get("reasons") else ""))
    if c2.get("remedy"):
        s.append(f"C2 remedy ({c2['remedy']}): {c2['remedy_text']}")
    if c2.get("ambient_range"):
        s.append(f"C2 covers ambient {c2['ambient_range'][0]:.1f}-{c2['ambient_range'][1]:.1f} C only; "
                 "neither verdict extends to hotter air; 42 C stays untested")
    kd = knee["decision"]
    s.append(f"knee: {kd['status']} -- {kd.get('why', '')}")
    if kd.get("ecu_threshold_off"):
        s.append("the model ECU's own threshold (KI 1.0) is off as well: moving it is a separate, later plant step")
    sd = sp["decision"]
    s.append(f"spark in the climb's cell: {sd['status']} -- {sd.get('why', '')}; the plan's label (k = 2, "
             f"R 0.85 deg) reads {sd['label']}; the 1.3 deg reading ({sd['label_plan_1p3']}) decides nothing")
    if c2.get("remedy") or kd.get("retune") or sd.get("retune"):
        s.append("order: C2's remedy first, then the spark offset, then the knee, each measured on its own "
                 "(premise_split.py style) with test_reward.py, check_roads.py and the three app suites")
        s.append("a retuned row is labelled 'fitted, held-out check pending' until a later drive logs both "
                 "angles in the cell")
    rng = knee.get("ambient_range") or sp.get("ambient_range")
    if rng:
        s.append(f"C1's labels carry 'extrapolated in ambient from [{rng[0]:.1f}, {rng[1]:.1f}] C to 42 C' and "
                 "'in duration' (20-30 s segments against the twelve-minute climb)")
    s.append("damage keeps being reported with and without the knock term until the knee's held-out label is "
             "validated or limited")
    s.append("under 'nothing is wrong' the three binding decisions together act wrongly about 8-10 % of the time")
    return s


def fmt(x, f="{:.3f}"):
    if x is None:
        return "n/a"
    if isinstance(x, float) and not np.isfinite(x):
        return "inf" if x > 0 else "-inf"
    return f.format(x)


def report_c(lines, out, fz):
    c2 = out["C2"]
    say(lines, "\nC2 -- does the car pull timing on a sudden load step?")
    if c2["verdict"] == "untested" and "N" not in c2:
        say(lines, f"  UNTESTED: {c2['reason']}")
    else:
        say(lines, f"  valid primary steps (frozen) {c2['N_frozen']}, unreadable {c2['unreadable']}, readable N "
                   f"{c2['N']}, pulls K {c2['K']}; K/N {fmt(c2['K_over_N'])}, exact 90 % interval "
                   f"[{fmt(c2['ci90'][0])}, {fmt(c2['ci90'][1])}]")
        say(lines, f"  cuts: frozen blocks {c2['cuts_frozen']['blocks']} -> pulls if K >= "
                   f"{c2['cuts_frozen']['k_yes']}, does not if K <= {c2['cuts_frozen']['k_no']}; applied "
                   f"{c2['k_yes']} / {c2['k_no']}")
        sh = c2["shams"]
        say(lines, f"  shams: {sh['scored']} scored of {sh['valid']} valid, {sh['pulls']} pull (rate "
                   f"{fmt(sh['rate'])}); one-sided Fisher, steps above shams: p {fmt(sh['fisher_p'], '{:.4f}')}")
        say(lines, f"  channel check: {c2['channel']['why']} -> {'passes' if c2['channel']['passes'] else 'fails'}")
        say(lines, f"  baseline robustness (decides only a 'does not'): n_B {c2['n_B']}, K + n_B = "
                   f"{c2['K'] + c2['n_B']} against {c2['k_no_with_B']} -> "
                   f"{'holds' if c2['robust_to_B'] else 'does not hold'}")
        say(lines, f"  VERDICT: {c2['verdict']}" + (f" -- {'; '.join(c2['reasons'])}" if c2["reasons"] else ""))
        say(lines, "  K per block: " + ", ".join(f"block {b['block']}: {b['pulls']}/{b['readable']}"
                                                  for b in c2["per_block"]))
        for r in c2["steps"]:
            say(lines, f"    {r['id']} {r['set']:7s} B {r['B']:+.2f}  late max {fmt(r['max_L'], '{:+.2f}')} "
                       f"({r['n_L']} pairs)  early max {fmt(r['max_E'], '{:+.2f}')}  {r['timing']}")
        ss = c2["step_specific"]
        say(lines, f"  step-specific: C2 {ss['c2_pulls']}/{ss['c2_steps']} in band against C1 windows "
                   f"{ss['c1_pulls']}/{ss['c1_windows']}; Fisher p {fmt(ss['fisher_p'], '{:.4f}')}; ambients "
                   f"{fmt(ss['amb_c2'], '{:.1f}')} / {fmt(ss['amb_c1'], '{:.1f}')} C -> "
                   f"{'step-specific' if ss['step_specific'] else 'not step-specific'}")
        say(lines, f"  remedy: {c2['remedy'] or 'none'}" + (f" -- {c2['remedy_text']}" if c2["remedy"] else ""))
        sec = c2["secondary"]
        say(lines, f"  secondary (descriptive): large {sec['size']['pulls_large']}/{sec['size']['n_large']} against "
                   f"moderate {sec['size']['pulls_moderate']}/{sec['size']['n_moderate']}, p "
                   f"{fmt(sec['size']['p'], '{:.4f}')}; warm against cool p {fmt(sec['ambient'].get('p'), '{:.4f}')}; "
                   "Holm: " + ", ".join(f"{k} {'significant' if v['significant'] else 'not'}"
                                        for k, v in sec["holm"].items()))
        if c2["ambient_range"]:
            say(lines, f"  ambient covered: {c2['ambient_range'][0]:.1f}-{c2['ambient_range'][1]:.1f} C")
    k = out["C1_knee"]
    say(lines, "\nC1 -- the knee")
    say(lines, f"  counting segments {k['segments']}; confirmed onsets {k['confirmed']} (8 needed), persisting "
               f"{k['persisting']}")
    m = k["median"]
    say(lines, f"  Turnbull median {fmt(m.get('point'))} in [{fmt(m.get('lo'))}, {fmt(m.get('hi'))}] "
               f"{'' if m.get('identified') else '(' + m.get('reason', '') + ')'}; bootstrap h "
               f"{fmt(k['bootstrap'].get('h'))} ({BOOT_N} resamples, seed {BOOT_SEED}); 2 u_val "
               f"{fmt(k['decision']['two_u_val'])}")
    say(lines, f"  halves: {k['halves'].get('why') or 'within 0.10'}")
    say(lines, f"  DECISION: {k['decision']['status']} -- {k['decision'].get('why', '')}")
    lg = k["logistic"]
    if not lg.get("fitted"):
        say(lines, f"  logistic secondary: not fitted ({lg.get('reason')}), {lg['n']} pairs")
    elif lg.get("ki50") is None:
        say(lines, f"  logistic secondary: slope {lg['b1']:+.3f} per KI is not positive, so no KI at P = 0.5 "
                   f"({lg['n']} pairs)")
    else:
        say(lines, f"  logistic secondary: KI at P = 0.5 is {lg['ki50']:.3f} over {lg['n']} pairs")
    s = out["C1_spark"]
    d = s["decision"]
    say(lines, f"\nC1 -- the spark in the climb's cell ({s['cell']})")
    say(lines, f"  counting segments {s['n_segments']} (15 needed); E {fmt(s.get('E'), '{:+.2f}')} deg, u_D "
               f"{fmt(s.get('u_D'), '{:.2f}')}, u_al {s['u_al']:.2f}, u_input {d['u_input']:.2f}, 2 u_val "
               f"{fmt(d['two_u_val'], '{:.2f}')}")
    say(lines, f"  ACTION: {d['status']} -- {d.get('why', '')}")
    say(lines, f"  label (k = 2, R 0.85): {d['label']}; the plan's 1.3 deg reading: {d['label_plan_1p3']} "
               "(decides nothing)")
    say(lines, "\nCOMBINED")
    for x in out["combined"]:
        say(lines, "  " + x)


# ==== the command line ===========================================================
def main(argv=None):
    ap = argparse.ArgumentParser(description="Drive C's decision rule (results/DRIVE_C_RULE.md)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("stage-a")
    a.add_argument("--c2", nargs="*", default=[])
    a.add_argument("--c1", nargs="*", default=[])
    a.add_argument("--out", default=OUT_DEFAULT)
    b = sub.add_parser("stage-b")
    b.add_argument("--out", default=OUT_DEFAULT)
    b.add_argument("--logs", default=None, help="where to look for a log not at its recorded path (IC38)")
    c = sub.add_parser("stage-c", help="writes beside the frozen list, once (guard 5)")
    c.add_argument("--frozen", required=True)
    c.add_argument("--hash", required=True)
    c.add_argument("--logs", default=None, help="where to look for a log not at its recorded path (IC38)")
    sub.add_parser("dry-run-spark")
    args = ap.parse_args(argv)
    if args.cmd == "stage-a":
        if not args.c2 and not args.c1:
            ap.error("stage-a needs at least one --c2 or --c1 file")
        stage_a(args.c2, args.c1, args.out)
    elif args.cmd == "stage-b":
        stage_b(args.out, args.logs)
    elif args.cmd == "stage-c":
        stage_c(args.frozen, args.hash, args.logs)
    else:
        plant_check()
        r = dry_run_spark()
        return 0 if r["ok"] else 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
