"""b58h_beside.py -- the B58 preview study's descriptive rows beside d (AB's routes of rows 150 (i), 150 (v) and
151): sections 9.5 (i), 9.5 (v) and 9.6 of results/PREREGISTRATION_B58H.md (PR-B below).

    python -B b58h_beside.py --list
    python -B b58h_beside.py core --scores results/B58H_RESULT/scores_b58h.json --records DIR --out DIR --jobs N

PR-B:630 runs the second line, at section 6.9 (c), with --records "$OUT/records", --out "$OUT/beside" and --jobs 14
(PR-B:1813). PR-B:1790 runs the first, which prints the routes present: one name per line. At AB's commit the only
route is `core`; settle, flat, road0 and cturb (PR-B:1817-1820) are added by later commits and are not listed here.
--list writes nothing and needs no subcommand; a call with neither --list nor a route is refused by argparse
(exit 2), and so is --list with a route.

WHAT IT IS. Descriptive: "It decides nothing: no verdict, band, status, test or Delta reads it, and it is reported
beside d at each H" (PR-B:818, :918). None of it enters a verdict, the band, the status, Delta or the context
(PR-B:707-708). Every damage number is in both readings, the no-knock reading (damage_thermal) primary and the
with-knock reading (damage) beside it, labelled four_engine_analysis.WITH_KNOCK_LABEL (PR-B:517-520, :819-820,
:1101, :1111); a row the knock term cannot change says so. The code is AB's, row 149 (3); evaluate.py is not
edited (PR-B:823-824). Where this docstring and PR-B differ, PR-B governs (PR-B:488).

CORE LOADS NO AGENT. It has no --set, --engine or --reward-knock: 9.5 (i) runs current-grade, a hand-written
policy; 9.5 (v) reads the scores' delivery block; 9.6 reads the per-step records the primary scoring wrote. The
engine is the scores' one engine (b58h_analysis.ENGINE, which load_scores requires), and the knock option is the
scores' provenance.reward_knock, False (load_scores requires it; PR-B:821-822, "the reward without the knock
term"). Nothing here calls evaluate.load_agent, read_agents, average_lines or any loader of a checkpoint.

THE INPUTS, and the checks made first (PR-B:923-924 "committed index", "committed scores"; DESIGN G27):
  the scores         --scores, read by b58h_analysis.load_scores (four_engine_analysis.validate_scores, the B58
                     alone, both ratios, the three arms, seeds 0..B58H_N-1, variant null, provenance d34, version
                     6, the knock option false and roads.json's roads_sha). Its sha_text (CRLF read as LF) binds;
                     its raw sha256 is printed beside it and binds nothing (PR-B:461-463).
  the records index  evaluate.records_index_path(--scores) (evaluate.py:1554-1556), scores_b58h.records.json.
  the text report    os.path.splitext(--scores)[0] + ".txt", the d34 route's --out copied beside the scores
                     (PR-B:455, :1800).
  roads.json         results/EPA_ROADS/roads.json; only ceilings.readings, ceilings.per_engine.b58.by,
                     ceilings.per_engine.b58.per_road and report.knee_shares.b58.turb_knee_k are read, and
                     nothing of commit_reveal, attempts, steps_log or roads_seed is printed or written.
  hw_opt's report    results/B58H_DESIGN/hw_opt/hw_opt_report.txt (row 153 (1); PR-B:839-840), CRLF read as LF.
  the grids print    results/B58H_DESIGN/grids_b58.txt (PR-B:1142-1146), CRLF read as LF.
Each must be committed at HEAD (epa_freeze.committed_at_head: a CRLF checkout of an LF blob counts).

REFUSALS OF THE WHOLE COMMAND (SystemExit "REFUSING core: ...", nothing written): a scores document load_scores
refuses; the scores or roads.json not committed at HEAD; the scores' D_base not one list (not exactly equal across
every arm and seed: the baseline ECU's damage per road does not depend on the agent, evaluate.py:1118, :1128);
a roads.json without the keys named above or with ceilings.readings other than READING_RJ's; --out inside the
repository (the outputs are written outside it first, PR-B:1804-1806, as b58h_descriptive.py does); --out holding
any of OUT_FILES (each is written once, PR-B:1159-1160; every file is also opened "x"); --jobs below 1. A failed
check of the index affects only 9.6; a failed check of the report affects only control 2; hw_opt's report or the
grids print not committed, not UTF-8 text or not in their committed shape: their lines read "not read: <reason>",
and the rest runs. Inside a descriptive row, a refusal, a failed control, a run that fails, or a record, index or
report that does not read does not stop core: that row reads "not computed" (or "not read") with its reason, and
the other rows run (PR-B:1182, :1184).

THE OUTPUTS, under --out, each written once: b58h_core.json, b58h_core.txt (also printed), b58h_core_s.png,
b58h_core_delivery.png, b58h_core_temps.png (matplotlib, the Agg backend) and current_grade.npz. PR-B:457 names
b58h_core.json and .txt "each with its printed .txt and its figure"; PR-B 9.5 (i), (v) and 9.6 name the three
figures. b58h_core.json: schema SCHEMA, json.dumps(indent=1, sort_keys=True, allow_nan=False) + LF, a value not
computed is null with its reason beside it. The .json and the .txt are written UTF-8 with LF line ends on every
platform (evaluate.write_once_json's rule), so each written file's raw sha256 equals its sha_text: that is the
"b58h_core.json sha256" printed and the .txt's report_sha256 kept in the JSON (PR-B:461-463).

9.5 (i), AGAINST CURRENT-GRADE AND THE HAND-WRITTEN STRATEGIES (PR-B:827-841; row 150 (i)).
- Current-grade's run (PR-B:829-831): check_premise.p_grade_now through evaluate.run_road_episode, use_preview True
  and H = evaluate.PREVIEW_H_S (engine_env's 30 s), "at the default H, as score_set runs it" (evaluate.py:1070-1071),
  reward_knock the scores' (False), plant engines.get(<the scores' engine>), on evaluate.decision34_roads(root=...)'s
  twenty roads (which refuses unless the re-verification record is current and EQUAL, evaluate.py:683-708). The
  policy's name in the scores is the one evaluate.HAND_POLICIES gives p_grade_now ("current-grade"). In parallel
  over the roads at --jobs: a top-level worker (run_cg) in a spawn pool whose initializer sets one OMP/MKL/torch
  thread (the b58h_descriptive.py pattern, :416-438); at --jobs 1 in this process, without torch, as score_set
  runs hand-written policies alone (evaluate.py:1077-1080). A refusal of decision34_roads, a road count other than
  the scores' n_roads, the roads check failing, a failure of the run on any road (any exception, in this process
  or a worker, printed with its type and text) or roads that ran different step counts makes 9.5 (i) read "not
  computed: <why>", and 9.6's current-grade row "not computed"; 9.5 (v) and the rest of 9.6 still run (PR-B:1182,
  "that row is reported 'not computed', with the refusal's text or the failure"). An exception's or a refusal's
  text is printed on one line: its lines stripped, blank ones dropped, joined by a space, at every break
  str.splitlines knows (LF, CR alone, CRLF, VT, FF, U+2028 ...; evaluate's refusals begin with one).
- The roads check (mistake 25; not in PR-B's words, a guard that cannot move a number): epa_roads.arrays_sha256 of
  the roads run equals the scores' provenance.arrays_sha256 (evaluate.py:713), so current-grade runs on the roads
  the agents were scored on. It records its own outcome only: PASS or FAIL when it ran, NOT RUN (passed null in
  the JSON, with the reason) when decision34_roads refused or returned another count of roads; a run that fails
  after it passed leaves it PASS, and 9.5 (i) names the run's failure.
- Its trace (PR-B:830-831, :922-923, "kept outside the repository the same way"): current_grade.npz under --out, in
  evaluate.write_records' format (evaluate.py:1206-1211): dt float64 0-d (the roads' dt), t_turb, t_oil and ki
  float64 of shape (roads, steps) in road k order; written once whenever the run completed, whatever the controls
  read; its raw sha256 is in b58h_core.json and the .txt.
- Control 1 (PR-B:832; D1): its fuel equals the scores' provenance.delivery.hand["current-grade"].fuel road by road,
  exact float equality (the block stores float(x["fuel"]) through json.dumps, which round-trips a double,
  evaluate.py:1101, :1187). A refused delivery block fails control 1 with the refusal's text.
- Control 2 (PR-B:832-833; D2): its cut in evaluate.py's form against the scores' D_base, in both readings, printed
  as evaluate.py:1323 prints it, f"    {name:<28} {no_knock:+8.2f} [{with_knock:+8.2f}]", equals the text report's
  line, compared as the whole line: the line is the one (exactly one) after the header CUT_HEADER
  (evaluate.py:1315) that starts with four spaces and the policy's name; CRLF is read as LF. A report absent, not
  committed or not UTF-8 text fails control 2. On a mismatch its detail quotes both lines and names their readings
  with the label, since 9.5 (i)'s status and 9.6's current-grade row print it.
- If control 1 or 2 fails, 9.5 (i) reads "not computed: control <n> failed: <detail>" (every failing control named,
  PR-B:913-914; DESIGN G22) and 9.6's current-grade row reads "not computed"; the controls' own lines still print.
- Control 3 (PR-B:833-835; D3): roads.json ceilings.per_engine.b58.per_road[k].D.neutral.{noknock, knock}, the
  baseline ECU's own run, against the scores' D_base road by road, ABSOLUTE difference at most 1e-6 (PR-B's "to
  1e-6"), in both readings; the largest absolute and relative difference and its road are printed whatever it
  reads. On a mismatch 9.5 (i) still runs, and the hand-written savings are printed with the differences beside
  them and "control 3 FAILED" (PR-B:835), never "not computed". roads.json's reading keys are noknock and knock
  (roads_ceiling.READINGS, roads_ceiling.py:145), READING_RJ maps them to the scores' no_knock and with_knock.
- s(agent) = cut(agent) - cut(current-grade), evaluate.py's form (evaluate.median_cut, 100 x (1 - median D / median
  D_base)), against the scores' D_base, both readings (PR-B:828-829); the mean form beside it, mean_k 100 x (D_cg,k -
  D_agent,k) / D_base,k (PR-B:1111). Per arm and for each reading and form (PR-B:836): n, the count of s < 0
  (strictly below current-grade), the median, the sd (ddof 1), and the range printed as its min and max.
- Beside (PR-B:837-840): hand-written (a) at the arm's r, (b) and (a_b), read from roads.json
  ceilings.per_engine.b58.by[r].<policy>.<noknock|knock>.evaluate_form; for the blinded arm all three at both r (by
  roads.json's construction (b) and (a_b) do not depend on r, so their two entries agree: they are printed, not
  chosen between). Their mean form is RECOMPUTED as mean_k 100 x (D_cg,k - D_x,k) / D_neutral,k from
  per_road[k].D (cg, a@<r>, b, a_b, neutral): roads.json's own `mean` field divides by the parallel baseline network
  on current-grade's run (roads_ceiling.py:811-820), another denominator, and is not printed (critic R6).
- Row 153 (1)'s tuned bests "as its committed report prints them" (PR-B:839-840, undefined there; DESIGN G20, fixed
  here before any score): for each reading section of hw_opt_report.txt ("=== reading: noknock" and "knock") and
  each family block ("blind", "sighted r=0.5", "sighted r=1.5"), every setting line whose saving in evaluate.py's
  form (its third number) is the family's largest (ties: every tied line), verbatim; and under "frontier,
  evaluate_form, <reading>" the two lines "r=<r>: largest sighted-minus-blind saving at equal extra fuel", verbatim.
  The fronts and the mean-form frontier lines are not printed. Printed with 9.8 item 1's label verbatim, HW_LABEL
  (PR-B:1039-1040; hw_opt.py.txt:202-203).
- Decision 13's count (PR-B:1142-1146; critic R5): grids_b58.txt lines 99 and 100, verbatim, labelled D13_LABEL;
  "not read" unless line 99 starts "  rule:" and line 100 starts "  b58: ". It is a different rule from 9.1's short
  step (torque_req > 40 Nm, evaluate.py:424-428), and the label says so.
- Figure b58h_core_s.png: one panel, the three arms along x; each seed's s (no knock, evaluate.py's form) as a dot;
  current-grade as the solid line at 0; over each arm, its hand-written savings as short horizontal lines, (a)
  dashed, (b) dotted, (a_b) dash-dot, one line per policy and value, labelled with the policy and every r it
  stands for (labels closer than 3.5 % of the axis staggered upwards); the legend below the panel. A part not
  computed draws its figure as a panel holding its "not computed" line, so the six files always exist.

9.5 (v), FUEL AND TORQUE PER SEED (PR-B:901-907; row 150 (v)). From the scores' delivery block (evaluate.py:1097-
1112) and section 9.1's definitions (PR-B:756-759): per seed, the fuel figure, mean_k 100 x (fuel_k / the baseline
ECU's fuel_k - 1); the mean short share over the roads with a demand step; and the pooled short share, the seed's
short steps over its demand steps over the roads. Per seed and r, sighted minus blinded for each of the three (G23:
both shares, the mean one first), with the mean over seeds, the two-sided 95 % t interval (b58h_analysis.t_interval:
mean +- t_0.975,n-1 x sd / sqrt(n), sd ddof 1, scipy's t; PR-B:536-538) and the sign count printed as positive /
negative / zero (G24). A seed whose either arm has no demand step on any road is dropped from the share differences
and named (G23); fewer than two seeds left: the interval reads "not computed". Beside: current-grade's and the
baseline ECU's own figures (the baseline's fuel figure is 0 by definition, computed and printed). Reactive is not
printed (G29). Statement: KNOCK_STATEMENT_V; "This row has no reading" (PR-B:761, :1112). The delivery block is
checked first (DESIGN 1.7's rules: keys rule, hand, arms, each an object; hand holds the baseline ECU and
current-grade; the arms and seeds are the scores'; every list holds n_roads entries; fuel finite, the baseline
ECU's above 0 on every road; demand and short steps integers with short <= demand; short_share None exactly when
demand is 0, else short/demand to 1e-12: the rules b58h_analysis.validate_delivery applies for 9.1, written here
because core reports the refusal's text per part). A refused block makes 9.5 (v) read "not computed: the delivery
block is refused: <reason>". Figure b58h_core_delivery.png: three panels (the fuel figure, the mean short share
and the pooled short share differences), each seed along x, r = 0.5 and r = 1.5 as two marker series, a line at 0.

9.6, THE TEMPERATURE ROWS (PR-B:916-951; row 151).
- Integrity first (PR-B:640-642, :923-924; D4): 9.6 reads "not computed: <reason>" (PR-B:1184), and 9.5 (i) and (v)
  still run, unless: the index is committed at HEAD and holds `files` and `scores_sha256`; its scores_sha256 is the
  scores file's sha_text (G26: write_once_json hashes the LF text it wrote, evaluate.py:1187-1194, so the sha_text
  of a CRLF or an LF checkout equals it, and the raw sha256 of a CRLF one does not); its files are exactly
  <engine>/baseline.npz and <engine>/<arm>_seed<S>.npz for every arm and seed of the scores (critic R7); each file
  exists under --records and its raw sha256 is the index's (binary files, evaluate.py:1212-1213); each npz
  loads (np.load, allow_pickle False) and holds dt, a 0-d float64 (write_records writes np.float64(dt),
  evaluate.py:1211) equal to evaluate.DT (1 s; PR-B:922, "at the records' dt (1 s)"), and t_turb, float64, finite,
  of shape (n_roads, steps), one shape for every file. A dt of another dtype (a str, bytes, complex, bool or int) is
  refused before it is read as a number, and named by its dtype and shape, never numpy's repr. An index that does
  not read as JSON (nested too deep for json too), or a record that does not load, is a record that "does not
  match" (PR-B:1184): 9.6 reads "not computed" with the reason, on one line, never a crash of core.
- Per policy and road (PR-B:925-927): the peak, max(t_turb) - 273.15 (deg C; PR-B's own conversion, evaluate.py:435
  prints peak_turb so), and the seconds above each limit L, dt x the count of steps with t_turb - 273.15 > L
  (strictly above, PR-B's "above"). The limits are typed here because no code constant holds them: 778 deg C (a 900
  deg C load-spectrum parameter carried to the housing) and 804 deg C (Conway's 930 deg C gas limit), decision 9 of
  21 October, results/VALIDATION_DECISIONS.md:116 (PR-B:929 cites VD:113, the table's header; critic W4) and
  REFERENCES.md:651-661 (PR-B:927-930).
- Reported (PR-B:931-934; DESIGN G25): per agent, the mean over the roads of the peak and of each limit's seconds,
  and its highest single peak (the four quantities); per arm, the mean over its seeds of each of the four, and the
  arm's highest single peak; per seed and r, sighted minus blinded for each of the four, with the mean, the 95 % t
  interval and the sign count (positive / negative / zero); beside each arm, the baseline ECU's row from
  baseline.npz, and current-grade's from 9.5 (i)'s trace (unless 9.5 (i)'s run or control 1 or 2 failed). Every
  recorded policy's highest peak is printed (PR-B:942).
- 850 deg C (PR-B:938-943; point P10). PR-B's "If any reaches 850 deg C, the seconds above 850 deg C are reported"
  allows two readings, since PR-B:939-940 calls roads.json's 1123 K "the 850 deg C knee", which lies just below 850
  deg C in degrees: the knee, K - 273.15 with K = roads.json report.knee_shares.b58.turb_knee_k (read), and 850 deg
  C itself (ABOVE_850_C, PR-B's words). Both are reported, each by its own trigger: if any recorded policy's highest
  peak (every agent, the baseline ECU, and current-grade when its row is computed) reaches a threshold (>=), the
  seconds strictly above that threshold are reported for every arm, the baseline ECU and current-grade, by the same
  rule as 778 and 804. A highest peak at or above the knee and below 850 deg C so reports the knee's seconds and not
  850's. Else the block says that no recorded peak reaches either. (DESIGN 2.4 takes the knee alone; PR-B governs.)
- Statement once (PR-B:935-937): TEMPS_STATEMENT.
- Figure b58h_core_temps.png: two panels (seconds above 778 and above 804 deg C, each agent's mean over the roads),
  the three arms along x, one dot per seed, the baseline ECU dashed and current-grade dotted across each panel.

PRINTED DECIMALS (descriptive choices, fixed before any score): cuts and s at 4 decimals (each arm's per-seed s
too); control 2's line as evaluate.py prints it; the fuel figure at 4 decimals (percent); shares at 6;
temperatures at 2 (deg C; the limits, the knee in K and in deg C, every peak); seconds at 2 (a policy's mean over
twenty roads of dt x a count is a multiple of 0.05 s at dt 1 s, which 2 decimals print exactly; the arms' means are
rounded to 2), the sighted-minus-blinded summaries of 9.6 likewise (peaks and seconds at 2); t at 4; control 1's
fuel in grams at 6 and control 3's differences in e-notation with 3 decimals. The JSON holds full precision. The
.txt is ASCII. Every printed line that holds a with-knock number names the reading with
four_engine_analysis.WITH_KNOCK_LABEL beside it (PR-B:1101, :819); control 2's expected and found lines are
evaluate.py's own line, under a heading that names both readings with the label, and its failing detail, which
9.5 (i) and 9.6 quote again, names them itself.

Every choice above is a descriptive detail PR-B leaves to AB's docstring (PR-B:481-485): none can move d, Delta,
the band, the status or any verdict, and section 15 records them at AB's commit. Tests: test_b58h_beside.py.
"""
import argparse
import hashlib
import json
import math
import os
import platform
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from b58h_analysis import (ARMS, ENGINE, ROADS, B58HError, load_scores, sha256_file, sign_counts,  # noqa: E402
                           t_interval)
import check_premise as CP             # noqa: E402  p_grade_now, current-grade's rule
import engines                         # noqa: E402  engines.get, the plant by its name (mistake 1)
import epa_freeze as EF                # noqa: E402  committed_at_head, versions, git_head
import epa_roads as ER                 # noqa: E402  arrays_sha256
import evaluate as V                   # noqa: E402  run_road_episode, decision34_roads, median_cut, ...
import four_engine_analysis as FEA     # noqa: E402  READINGS, WITH_KNOCK_LABEL
from thresholds import common as TC    # noqa: E402  sha_text, CRLF read as LF

ROUTES = ("core",)
SCHEMA = "b58h-core/1"
OUT_FILES = ("b58h_core.json", "b58h_core.txt", "b58h_core_s.png", "b58h_core_delivery.png",
             "b58h_core_temps.png", "current_grade.npz")
READINGS = FEA.READINGS                                          # ("no_knock", "with_knock"), no knock first
READING_RJ = {"no_knock": "noknock", "with_knock": "knock"}      # roads.json's names (roads_ceiling.py:145)
BASE = V.BASELINE                                                # "baseline ECU"
CG = {fn: name for name, fn in V.HAND_POLICIES}["p_grade_now"]   # "current-grade", the scores' name for it
HW_POLICIES = ("a", "b", "a_b")                                  # PR-B 9.5 (i): (a), (b) and (a_b)
HW_OPT_REPORT = "results/B58H_DESIGN/hw_opt/hw_opt_report.txt"
GRIDS = "results/B58H_DESIGN/grids_b58.txt"
GRIDS_LINES = (99, 100)                                          # PR-B:1145-1146, critic R5
CUT_HEADER = "  cut against the baseline ECU, 100 x (1 - median D / median D_base): no knock [with knock]"
LIMITS_C = (778.0, 804.0)       # decision 9, VALIDATION_DECISIONS.md:116; REFERENCES.md:651-661 (PR-B:925-930)
ABOVE_850_C = 850.0             # PR-B:942-943's words, reported beside the knee read from roads.json
ABOVE_850 = f"{ABOVE_850_C:g}"  # its label, "850"
KELVIN = 273.15                 # PR-B:925, "t_turb - 273.15"
CONTROL_3_ABS = 1e-6            # PR-B:833-835, "to 1e-6"
SHARE_ABS = 1e-12               # DESIGN 1.7: short_share equals short/demand
HW_LABEL = ("hand-written lambda strategies tuned over two settings; savings over current-grade on decision 34's "
            "twenty roads, B58 frozen plant; describes the model, never a bound on d")
D13_LABEL = ("decision 13's count (torque < 0.95 x torque_req after the 20 s ramp), a different rule from 9.1's "
             "short step")
KNOCK_STATEMENT_V = ("the knock term cannot change them: the knock option changes only the return "
                     "(evaluate.py:372-374)")
TEMPS_STATEMENT = ("these numbers are the same in both readings: the knock option changes only the return, and the "
                   "trace is the same run (evaluate.py:372-374); modelled temperatures of the unvalidated housing, "
                   "never a measurement on the car")
DESCRIPTIVE = ("descriptive: it decides nothing; no verdict, band, status, test or Delta reads it, and it is "
               "reported beside d at each H (PR-B 9.5, 9.6)")
TRACE_KEYS = ("t_turb", "t_oil", "ki")
KEEP = ("damage_thermal", "damage", "fuel", "demand_steps", "short_steps", "steps", "peak_turb")
DELIVERY_PER = ("demand_steps", "fuel", "short_share", "short_steps")


def refuse(why):
    raise SystemExit(f"\nREFUSING core: {why}")


def _one_line(text):
    """An exception's or a refusal's text as one printed line: its lines stripped and joined by a space (evaluate's
    refusals begin with a line break, which would otherwise split every line that prints the reason)."""
    return " ".join(part.strip() for part in str(text).splitlines() if part.strip())


# ------------------------------------------------------------------------------------------ small readers
def commit_problem(path, *, root):
    """None when `path` is committed at HEAD in `root` (epa_freeze.committed_at_head), else the reason."""
    if not os.path.isfile(path):
        return "absent"
    try:
        ok = EF.committed_at_head(os.path.abspath(path), root=root)
    except (ValueError, TypeError, EF.GitError) as exc:
        return f"cannot be checked against HEAD ({_one_line(exc)})"
    return None if ok else "not committed at HEAD (untracked, changed, or absent from HEAD's tree)"


def read_text_lf(path):
    """A committed text file's text with every CRLF read as LF (thresholds.common.sha_text's rule)."""
    with open(path, "rb") as fh:
        return fh.read().replace(b"\r\n", b"\n").decode("utf-8")


def inside(path, root):
    a, r = os.path.normcase(os.path.abspath(path)), os.path.normcase(os.path.abspath(root))
    return a == r or a.startswith(r + os.sep)


def one_base(checked):
    """The scores' D_base per reading as one list: exactly equal for every arm and seed, else refused."""
    eng = checked["engines"][ENGINE]
    out = {}
    for reading in READINGS:
        lists = [eng["arms"][arm][s][reading]["D_base"] for arm in ARMS for s in eng["seeds"]]
        if any(not np.array_equal(x, lists[0]) for x in lists):
            refuse(f"the scores' D_base ({reading}) differs between arms or seeds: the baseline ECU's damage per "
                   "road is one list (evaluate.py:1118, :1128)")
        out[reading] = [float(v) for v in lists[0]]
    return out


def _finite(v):
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)


def _count(v):
    return isinstance(v, int) and not isinstance(v, bool) and v >= 0


# ------------------------------------------------------------------------------------------ the delivery block
def _per_problem(per, n):
    if not isinstance(per, dict) or sorted(per) != sorted(DELIVERY_PER):
        return f"keys {sorted(per) if isinstance(per, dict) else type(per).__name__}, not {sorted(DELIVERY_PER)}"
    for key in DELIVERY_PER:
        if not isinstance(per[key], list) or len(per[key]) != n:
            return f"{key} is not a list of {n} roads"
    for k in range(n):
        fuel, dem, short, share = (per["fuel"][k], per["demand_steps"][k], per["short_steps"][k],
                                   per["short_share"][k])
        if not _finite(fuel):
            return f"fuel[{k}] {fuel!r} is not a finite number"
        if not _count(dem) or not _count(short):
            return f"road {k}: demand_steps {dem!r} and short_steps {short!r} are not counts"
        if short > dem:
            return f"road {k}: {short} short steps exceed its {dem} demand steps"
        if dem == 0:
            if share is not None:
                return f"road {k}: no demand step, and short_share {share!r} is not null"
        elif not _finite(share) or abs(share - short / dem) > SHARE_ABS:
            return f"road {k}: short_share {share!r} is not short / demand = {short / dem!r}"
    return None


def delivery_problem(doc, *, seeds):
    """None when the scores' provenance.delivery is evaluate.delivery_block's form for these scores (DESIGN 1.7),
    else the reason it is refused."""
    n = doc["n_roads"]
    d = (doc.get("provenance") or {}).get("delivery")
    if not isinstance(d, dict):
        return "provenance.delivery is absent"
    if sorted(d) != ["arms", "hand", "rule"]:
        return f"provenance.delivery holds {sorted(d)}, not arms, hand and rule"
    hand, arms = d["hand"], d["arms"]
    if not isinstance(hand, dict) or not isinstance(arms, dict) or not isinstance(d["rule"], dict):
        return "delivery.rule, delivery.hand and delivery.arms are not all objects"
    for name in (BASE, CG):
        if name not in hand:
            return f"delivery.hand has no {name!r}"
    if sorted(arms) != sorted(ARMS):
        return f"delivery.arms holds {sorted(arms)}, the scores {list(ARMS)}"
    for arm in ARMS:
        if not isinstance(arms[arm], dict) or set(arms[arm]) != set(seeds):
            return f"delivery.arms.{arm}'s seeds are not the scores' {seeds[0]}-{seeds[-1]}"
    entries = [(f"hand[{name!r}]", hand[name]) for name in sorted(hand)]
    entries += [(f"arms.{arm}[{s!r}]", arms[arm][s]) for arm in ARMS for s in seeds]
    for where, per in entries:
        p = _per_problem(per, n)
        if p:
            return f"delivery.{where}: {p}"
    if any(f <= 0 for f in hand[BASE]["fuel"]):
        return "the baseline ECU's fuel is not above 0 on every road (the fuel figure divides by it)"
    return None


def seed_delivery(per, base_fuel):
    """Section 9.1's per-seed figures (PR-B:756-759): the fuel figure, the mean short share over the roads with a
    demand step (None without one), the pooled short share (None without a demand step)."""
    fuel, bf = np.asarray(per["fuel"], dtype=float), np.asarray(base_fuel, dtype=float)
    shares = [s for s, dem in zip(per["short_share"], per["demand_steps"]) if dem]
    demand = sum(per["demand_steps"])
    return {"fuel_figure": float(np.mean(100.0 * (fuel / bf - 1.0))),
            "mean_short_share": float(np.mean(shares)) if shares else None,
            "pooled_short_share": sum(per["short_steps"]) / demand if demand else None,
            "roads_with_demand": len(shares)}


def summary(seeds, values):
    """Mean over seeds, the two-sided 95 % t interval and the sign count of per-seed values."""
    out = {"seeds": [int(s) for s in seeds], "values": [float(v) for v in values], "signs": sign_counts(values),
           "interval": None, "interval_note": None}
    try:
        out["interval"] = t_interval(values)
    except B58HError as exc:
        out["interval_note"] = f"not computed: {exc}"
    return out


# ------------------------------------------------------------------------------------------ current-grade's run
def _one_thread():
    try:
        import torch
    except ImportError:
        return
    torch.set_num_threads(1)


def _worker_init():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    _one_thread()


def run_cg(task):
    """Current-grade on one road, as evaluate.score_set runs a hand-written policy (evaluate.py:1070-1071,
    :1044-1045): its damage in both readings, fuel, steps, peak and per-step trace. A refusal (SystemExit) becomes
    a RuntimeError, which a pool carries back; current_grade turns any failure into 9.5 (i)'s "not computed"."""
    eid, road, knock = task
    try:
        out = V.run_road_episode(CP.p_grade_now, road, plant=engines.get(eid), use_preview=True,
                                 preview_h_s=V.PREVIEW_H_S, reward_knock=knock)
    except SystemExit as exc:
        raise RuntimeError(f"current-grade on road {road.get('k')}: {_one_line(exc)}") from None
    row = {k: out[k] for k in KEEP}
    row["trace"] = {k: [float(x) for x in out["trace"][k]] for k in TRACE_KEYS}
    return row


def run_roads(tasks, *, n_jobs):
    """Every task in road order: in this process at n_jobs 1, else in a spawn pool, one road per chunk."""
    if n_jobs <= 1:
        return [run_cg(t) for t in tasks]
    import multiprocessing as mp
    import b58h_beside as _self         # pickled by this module's name, as a script too
    with mp.get_context("spawn").Pool(min(int(n_jobs), len(tasks)), initializer=_self._worker_init) as pool:
        return pool.map(_self.run_cg, tasks, chunksize=1)


def current_grade(doc, *, jobs, root):
    """(run, None, check) with current-grade's rows, or (None, why, check) when decision 34's roads are refused or
    are not the scored ones, or the run fails on any road (PR-B:1182: that row reads "not computed" with the
    failure's text, and the rest of core runs). `check` is the roads check's own outcome, {"passed", "detail"}:
    passed True or False when it ran, None (not run, the reason in detail) when decision34_roads refused or
    returned another count of roads; a run that fails after the check passed leaves it True."""
    try:
        roads, _ = V.decision34_roads(root=root)
    except SystemExit as exc:
        why = f"decision 34's roads refused: {_one_line(exc)}"
        return None, why, {"passed": None, "detail": why}
    if len(roads) != doc["n_roads"]:
        why = f"decision 34's roads are {len(roads)}, the scores' {doc['n_roads']}"
        return None, why, {"passed": None, "detail": why}
    want = (doc.get("provenance") or {}).get("arrays_sha256")
    got = ER.arrays_sha256(roads)
    if got != want:
        detail = (f"epa_roads.arrays_sha256 of decision 34's roads ({got[:12]}) is not the scores' "
                  f"provenance.arrays_sha256 ({str(want)[:12]})")
        return None, f"the roads check failed: {detail}", {"passed": False, "detail": detail}
    check = {"passed": True, "detail": "arrays_sha256 equal"}
    knock = doc["provenance"]["reward_knock"]
    try:
        rows = run_roads([(ENGINE, road, knock) for road in roads], n_jobs=jobs)
    except Exception as exc:            # any failure of the run, in this process or a worker: reported, not raised
        return None, f"current-grade's run failed: {type(exc).__name__}: {_one_line(exc)}", check
    steps = {len(r["trace"]["t_turb"]) for r in rows}
    if len(steps) != 1:
        return None, f"current-grade's roads ran {sorted(steps)} steps; write_records' arrays need one count", check
    trace = {k: np.asarray([r["trace"][k] for r in rows], dtype=np.float64) for k in TRACE_KEYS}
    return {"rows": rows, "trace": trace, "dt": float(roads[0]["dt"]), "arrays_sha256": got,
            "D": {reading: [float(r[key]) for r in rows] for reading, key in V.READING_KEYS.items()},
            "fuel": [float(r["fuel"]) for r in rows], "demand_steps": [int(r["demand_steps"]) for r in rows],
            "short_steps": [int(r["short_steps"]) for r in rows], "steps": steps.pop(),
            "call": {"policy": "check_premise.p_grade_now", "runner": "evaluate.run_road_episode",
                     "use_preview": True, "preview_h_s": V.PREVIEW_H_S, "reward_knock": knock,
                     "plant": f"engines.get({ENGINE!r})", "roads": "evaluate.decision34_roads",
                     "jobs": int(jobs)}}, None, check


# ------------------------------------------------------------------------------------------ the controls
def cuts_of(D, D_base):
    """{reading: {evaluate_form, mean_form}}: 100 x (1 - median D / median D_base), and the mean of the roads'
    100 x (1 - D_k / D_base,k)."""
    return {rd: {"evaluate_form": V.median_cut(D[rd], D_base[rd]),
                 "mean_form": float(np.mean(100.0 * (1.0 - np.asarray(D[rd], float) / np.asarray(D_base[rd], float))))}
            for rd in READINGS}


def report_line(name, no_knock, with_knock):
    """evaluate.py:1323's line of a policy's cut, no knock [with knock], at two decimals."""
    return f"    {name:<28} {no_knock:+8.2f} [{with_knock:+8.2f}]"


def control_1(cg_fuel, doc, delivery_why):
    if delivery_why:
        return {"passed": False, "detail": f"the delivery block is refused: {delivery_why}"}
    block = doc["provenance"]["delivery"]["hand"][CG]["fuel"]
    if len(block) != len(cg_fuel):
        return {"passed": False, "detail": f"{len(cg_fuel)} roads run, {len(block)} in the delivery block"}
    bad = [k for k, (a, b) in enumerate(zip(cg_fuel, block)) if float(a) != float(b)]
    if bad:
        k = bad[0]
        return {"passed": False, "detail": f"fuel differs on {len(bad)} road(s), first road {k}: run "
                                           f"{cg_fuel[k]:.6f} g, delivery block {block[k]:.6f} g, difference "
                                           f"{cg_fuel[k] - block[k]:+.3e} g"}
    return {"passed": True, "detail": f"equal on all {len(block)} roads"}


def control_2(report_path, cut, *, root):
    want = report_line(CG, cut["no_knock"]["evaluate_form"], cut["with_knock"]["evaluate_form"])
    out = {"passed": False, "expected": want, "found": None}
    why = commit_problem(report_path, root=root)
    if why:
        return dict(out, detail=f"the text report {report_path}: {why}")
    try:
        lines = read_text_lf(report_path).split("\n")
    except (OSError, UnicodeDecodeError) as exc:    # control 2 fails, core does not crash (PR-B:1182)
        return dict(out, detail=f"the text report {report_path} does not read as UTF-8 text ({type(exc).__name__})")
    if CUT_HEADER not in lines:
        return dict(out, detail=f"the text report has no line {CUT_HEADER.strip()!r} (evaluate.py:1315)")
    after = lines[lines.index(CUT_HEADER) + 1:]
    hits = [ln for ln in after if ln.startswith(f"    {CG} ")]
    if len(hits) != 1:
        return dict(out, detail=f"{len(hits)} lines of {CG} after the cut header, not one")
    out["found"] = hits[0]
    if hits[0] != want:                 # 9.5 (i) and 9.6 quote this detail: it names the readings itself
        return dict(out, detail=f"the report reads {hits[0].strip()!r}, the run gives {want.strip()!r} (no knock "
                                f"[with knock, {FEA.WITH_KNOCK_LABEL}], evaluate.py's line)")
    return dict(out, passed=True, detail="equal at the report's two decimals, both readings")


def control_3(per_road, D_base):
    n = len(D_base[READINGS[0]])
    if len(per_road) != n or [int(p["k"]) for p in per_road] != list(range(n)):
        return {"passed": False, "detail": f"roads.json's per_road is not roads 0-{n - 1} in order", "by": None}
    by = {}
    for rd in READINGS:
        nd = np.asarray([float(p["D"]["neutral"][READING_RJ[rd]]) for p in per_road])
        sb = np.asarray(D_base[rd], dtype=float)
        diff = np.abs(nd - sb)
        k = int(np.argmax(diff))
        by[rd] = {"max_abs": float(diff[k]), "road": k, "max_rel": float(np.max(diff / np.abs(sb)))}
    passed = all(by[rd]["max_abs"] <= CONTROL_3_ABS for rd in READINGS)
    return {"passed": passed, "by": by,
            "detail": ("equal to 1e-6 on every road, both readings" if passed else
                       "roads.json's neutral D differs from the scores' D_base by more than 1e-6")}


# ------------------------------------------------------------------------------------------ 9.5 (i)
def arm_stats(values):
    x = np.asarray(values, dtype=float)
    return {"n": int(x.size), "below_0": int(np.count_nonzero(x < 0)), "median": float(np.median(x)),
            "sd": float(x.std(ddof=1)), "min": float(x.min()), "max": float(x.max())}


def savings(checked, cg_D, D_base):
    """s per arm, seed, reading and form, and each arm's statistics (PR-B:828-829, :836)."""
    eng = checked["engines"][ENGINE]
    cg = cuts_of(cg_D, D_base)
    s, per_arm = {}, {}
    for arm in ARMS:
        s[arm] = {}
        for seed in eng["seeds"]:
            e = eng["arms"][arm][seed]
            s[arm][str(seed)] = {
                rd: {"evaluate_form": V.median_cut(e[rd]["D"], e[rd]["D_base"]) - cg[rd]["evaluate_form"],
                     "mean_form": float(np.mean(100.0 * (np.asarray(cg_D[rd], float) - e[rd]["D"])
                                                / np.asarray(D_base[rd], float)))}
                for rd in READINGS}
        per_arm[arm] = {rd: {form: arm_stats([s[arm][x][rd][form] for x in s[arm]])
                             for form in ("evaluate_form", "mean_form")} for rd in READINGS}
    return {"current_grade_cut": cg, "s": s, "per_arm": per_arm}


def _arm_r(arm, ratios):
    return list(ratios) if arm == "blind" else [arm[len("sighted_r"):]]


def hand_written(ceil, ratios):
    """The hand-written savings over current-grade per reading: (a), (b) and (a_b) at each r, evaluate_form read
    from by[r], the mean form recomputed from per_road (module docstring)."""
    by, per_road = ceil["by"], ceil["per_road"]
    table = {}
    for rd in READINGS:
        rows = []
        for r in ratios:
            for pol in HW_POLICIES:
                key = f"a@{r}" if pol == "a" else pol
                cg = np.asarray([float(p["D"]["cg"][READING_RJ[rd]]) for p in per_road])
                x = np.asarray([float(p["D"][key][READING_RJ[rd]]) for p in per_road])
                neutral = np.asarray([float(p["D"]["neutral"][READING_RJ[rd]]) for p in per_road])
                rows.append({"policy": pol, "r": r,
                             "evaluate_form": float(by[r][pol][READING_RJ[rd]]["evaluate_form"]),
                             "mean_form": float(np.mean(100.0 * (cg - x) / neutral))})
        table[rd] = rows
    return {"table": table, "by_arm": {arm: _arm_r(arm, ratios) for arm in ARMS}}


SETTING = re.compile(r"^  (?P<label>\S.*?)\s+(?P<mean>-?\d+\.\d+)\s+(?P<ev>-?\d+\.\d+)\s+(?P<fuel>[+-]\d+\.\d+)"
                     r"\s+(?P<peak>-?\d+\.\d+)$")


def tuned_bests(text, ratios):
    """Row 153 (1)'s tuned bests from hw_opt_report.txt's text (module docstring): {reading: {"best": {family:
    [verbatim lines]}, "frontier": [verbatim lines]}}. Raises B58HError when the text is not in that shape."""
    families = ["blind"] + [f"sighted r={r}" for r in ratios]
    fam_re = re.compile(r"^(" + "|".join(re.escape(f) for f in families)
                        + r"): setting, saving \(mean form\), saving \(evaluate\.py's form\), extra fuel %, peak C$")
    front_re = re.compile(r"^frontier, (mean|evaluate_form), (\w+): ")
    gap_re = re.compile(r"^  r=(" + "|".join(re.escape(r) for r in ratios)
                        + r"): largest sighted-minus-blind saving at equal extra fuel: ")
    out, reading, fam, front = {}, None, None, False
    for line in text.split("\n"):
        m = re.match(r"^=== reading: (\w+)\b", line)
        if m:
            reading, fam, front = m.group(1), None, False
            out[reading] = {"settings": {f: [] for f in families}, "frontier": []}
            continue
        if not line.strip():
            fam, front = None, False
            continue
        if reading is None:
            raise B58HError(f"a line before the first '=== reading:' heading: {line!r}")
        m = fam_re.match(line)
        if m:
            fam, front = m.group(1), False
            continue
        m = front_re.match(line)
        if m:
            fam, front = None, (m.group(1) == "evaluate_form" and m.group(2) == reading)
            continue
        if fam is not None:
            s = SETTING.match(line)
            if not s:
                raise B58HError(f"a line of {fam} under {reading} is not a setting line: {line!r}")
            out[reading]["settings"][fam].append((float(s.group("ev")), line))
        elif front and gap_re.match(line):
            out[reading]["frontier"].append(line)
    res = {}
    for rd in READING_RJ.values():
        if rd not in out:
            raise B58HError(f"no '=== reading: {rd}' section")
        best = {}
        for f in families:
            rows = out[rd]["settings"][f]
            if not rows:
                raise B58HError(f"no setting line of {f!r} under {rd}")
            top = max(v for v, _ in rows)
            best[f] = [line for v, line in rows if v == top]
        if len(out[rd]["frontier"]) != len(ratios):
            raise B58HError(f"{len(out[rd]['frontier'])} 'largest sighted-minus-blind saving' lines under "
                            f"'frontier, evaluate_form, {rd}', not {len(ratios)}")
        res[rd] = {"best": best, "frontier": out[rd]["frontier"]}
    return res


def decision13(text):
    """grids_b58.txt lines 99 and 100, verbatim (PR-B:1145-1146)."""
    lines = text.split("\n")
    if len(lines) < GRIDS_LINES[1]:
        raise B58HError(f"{len(lines)} lines, not at least {GRIDS_LINES[1]}")
    rule, count = lines[GRIDS_LINES[0] - 1], lines[GRIDS_LINES[1] - 1]
    if not rule.startswith("  rule:") or not count.startswith(f"  {ENGINE}: "):
        raise B58HError(f"lines {GRIDS_LINES[0]}-{GRIDS_LINES[1]} are not decision 13's rule and the "
                        f"{ENGINE}'s count: {rule!r}, {count!r}")
    return [rule, count]


def read_beside(rel, *, root, parse):
    """(value, None) or (None, "not read: <reason>") for a committed text record read through `parse`."""
    path = os.path.join(root, *rel.split("/"))
    why = commit_problem(path, root=root)
    if why:
        return None, f"not read: {rel}: {why}"
    try:
        return parse(read_text_lf(path)), None
    except B58HError as exc:
        return None, f"not read: {rel}: {exc}"
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"not read: {rel}: it does not read as UTF-8 text ({type(exc).__name__})"


# ------------------------------------------------------------------------------------------ 9.5 (v)
def part_v(doc, *, ratios, seeds, problem):
    if problem:
        return {"status": f"not computed: the delivery block is refused: {problem}"}
    d = doc["provenance"]["delivery"]
    bf = d["hand"][BASE]["fuel"]
    per = {arm: {s: seed_delivery(d["arms"][arm][s], bf) for s in seeds} for arm in ARMS}
    diffs = {}
    for r in ratios:
        sig = FEA.arm_name(r)
        fuel = [per[sig][s]["fuel_figure"] - per["blind"][s]["fuel_figure"] for s in seeds]
        diffs[r] = {"fuel_figure": dict(summary(seeds, fuel), dropped=[])}
        for q in ("mean_short_share", "pooled_short_share"):
            kept = [s for s in seeds if per[sig][s][q] is not None and per["blind"][s][q] is not None]
            vals = [per[sig][s][q] - per["blind"][s][q] for s in kept]
            diffs[r][q] = dict(summary(kept, vals), dropped=[int(s) for s in seeds if s not in kept])
    return {"status": "computed", "per_seed": per, "differences": diffs,
            "beside": {name: seed_delivery(d["hand"][name], bf) for name in (BASE, CG)},
            "no_demand_seeds": {arm: [int(s) for s in seeds if per[arm][s]["roads_with_demand"] == 0]
                                for arm in ARMS},
            "statement": KNOCK_STATEMENT_V, "reading": "none: fuel and torque hold no damage (PR-B:761, :1112)"}


# ------------------------------------------------------------------------------------------ 9.6
def read_records(index_path, records_dir, *, sha_text, seeds, n_roads, root):
    """The index and every record's t_turb and dt, after the integrity checks of the module docstring; raises
    B58HError naming the first that fails."""
    why = commit_problem(index_path, root=root)
    if why:
        raise B58HError(f"the records index {index_path}: {why}")
    try:
        with open(index_path, encoding="utf-8") as fh:
            index = json.load(fh)
    except (OSError, ValueError, RecursionError) as exc:    # JSONDecodeError and UnicodeDecodeError are ValueErrors;
        raise B58HError(f"the records index {index_path} does not read as JSON ({type(exc).__name__}: "
                        f"{_one_line(exc)})") from None     # a nesting too deep for json raises RecursionError
    if not isinstance(index, dict) or not isinstance(index.get("files"), dict) or "scores_sha256" not in index:
        raise B58HError("the records index holds no files and scores_sha256")
    if index["scores_sha256"] != sha_text:
        raise B58HError(f"the records index's scores_sha256 ({str(index['scores_sha256'])[:12]}) is not the "
                        f"committed scores file's sha_text ({sha_text[:12]})")
    want = {f"{ENGINE}/baseline.npz"} | {f"{ENGINE}/{arm}_seed{s}.npz" for arm in ARMS for s in seeds}
    if set(index["files"]) != want:
        missing, extra = sorted(want - set(index["files"])), sorted(set(index["files"]) - want)
        raise B58HError(f"the records index's files are not the baseline ECU's and every agent's: missing "
                        f"{missing[:4]}{' ...' if len(missing) > 4 else ''}, extra {extra[:4]}")
    arrays, shape = {}, None
    for rel in sorted(want):
        path = os.path.join(records_dir, *rel.split("/"))
        if not os.path.isfile(path):
            raise B58HError(f"the record {rel} is missing under {records_dir}")
        if sha256_file(path) != index["files"][rel]:
            raise B58HError(f"the record {rel}'s sha256 is not the index's")
        names, dt, tt = _load_record(path, rel)
        if dt is None:
            raise B58HError(f"the record {rel} holds {names}, not dt and t_turb")
        if dt.shape != () or dt.dtype != np.float64:    # before float(): a str, bytes or complex dt raises there
            raise B58HError(f"the record {rel}'s dt is {dt.dtype} {dt.shape}, not a 0-d float64 (write_records' "
                            "np.float64(dt))")          # dtype and shape, not numpy's repr, which wraps lines
        if float(dt) != V.DT:
            raise B58HError(f"the record {rel}'s dt is {float(dt)!r} s, not the records' {V.DT:g} s")
        if tt.dtype != np.float64 or tt.ndim != 2 or tt.shape[0] != n_roads or not np.all(np.isfinite(tt)):
            raise B58HError(f"the record {rel}'s t_turb is {tt.dtype} {tt.shape}, not finite float64 "
                            f"({n_roads}, steps)")
        if shape is None:
            shape = tt.shape
        elif tt.shape != shape:
            raise B58HError(f"the record {rel}'s t_turb is {tt.shape}, the others {shape}")
        arrays[rel] = (float(dt), tt)
    return index, arrays


def _load_record(path, rel):
    """A record's member names, and copies of its dt and t_turb (None, None when either is absent); B58HError
    when the file does not load as an npz without pickles (PR-B:1184: 9.6 then reads "not computed")."""
    try:                                # the handle is ours: np.load leaves its own open when a truncated zip raises
        with open(path, "rb") as fh, np.load(fh, allow_pickle=False) as z:
            names = sorted(z.files)
            if "dt" not in names or "t_turb" not in names:
                return names, None, None
            return names, np.array(z["dt"]), np.array(z["t_turb"])
    except Exception as exc:            # a corrupt zip, a pickle, a bare .npy: reported, not raised
        raise B58HError(f"the record {rel} does not load as an npz ({type(exc).__name__}: "
                        f"{_one_line(exc)})") from None


def temps_of(t_turb, dt, limits):
    """Per road: the peak, max(t_turb) - 273.15 deg C, and per limit dt x the count of steps with
    t_turb - 273.15 strictly above it."""
    c = np.asarray(t_turb, dtype=float) - KELVIN
    return {"peak": [float(v) for v in c.max(axis=1)],
            "above": {lab: [float(dt * v) for v in np.count_nonzero(c > lim, axis=1)] for lab, lim in limits}}


def quantities(limits):
    return ["peak_mean", "peak_max"] + [f"above_{lab}" for lab, _ in limits]


def policy_summary(rows, limits):
    """The four quantities of one policy (more with the knee): the mean over the roads of the peak and of each
    limit's seconds, and the highest single peak."""
    out = {"peak_mean": float(np.mean(rows["peak"])), "peak_max": float(np.max(rows["peak"]))}
    for lab, _ in limits:
        out[f"above_{lab}"] = float(np.mean(rows["above"][lab]))
    return out


def part_96(index_path, records_dir, *, sc, seeds, ratios, n_roads, knee_k, cg_trace, cg_dt, cg_note, root):
    try:
        index, arrays = read_records(index_path, records_dir, sha_text=sc["sha_text"], seeds=seeds,
                                     n_roads=n_roads, root=root)
    except B58HError as exc:                # one line whatever a reason holds (R2-2); each reason is one line too
        return {"status": f"not computed: {_one_line(exc)}"}
    shape = arrays[f"{ENGINE}/baseline.npz"][1].shape
    if cg_trace is not None and cg_trace["t_turb"].shape != shape:
        cg_trace, cg_note = None, (f"its trace is {cg_trace['t_turb'].shape}, the records {shape}")
    knee_c = float(knee_k) - KELVIN
    base_limits = [(f"{lim:g}", lim) for lim in LIMITS_C]

    def of_record(name, limits):
        dt, tt = arrays[f"{ENGINE}/{name}.npz"]
        return policy_summary(temps_of(tt, dt, limits), limits)

    def summarise(limits):
        agents = {arm: {s: of_record(f"{arm}_seed{s}", limits) for s in seeds} for arm in ARMS}
        cg = None if cg_trace is None else policy_summary(temps_of(cg_trace["t_turb"], cg_dt, limits), limits)
        return agents, of_record("baseline", limits), cg
    agents, base, cg = summarise(base_limits)
    peaks = [agents[a][s]["peak_max"] for a in ARMS for s in seeds] + [base["peak_max"]]
    peaks += [] if cg is None else [cg["peak_max"]]
    highest = max(peaks)
    readings_850 = (("knee", knee_c), (ABOVE_850, ABOVE_850_C))     # PR-B:942-943's "850 deg C", both readings
    reached = {lab: highest >= lim for lab, lim in readings_850}    # each reading by its own threshold
    limits = base_limits + [(lab, lim) for lab, lim in readings_850 if reached[lab]]
    if len(limits) > len(base_limits):
        agents, base, cg = summarise(limits)
    qs = quantities(limits)
    per_arm = {arm: dict({q: float(np.mean([agents[arm][s][q] for s in seeds])) for q in qs},
                         highest_peak=float(max(agents[arm][s]["peak_max"] for s in seeds))) for arm in ARMS}
    diffs = {r: {q: summary(seeds, [agents[FEA.arm_name(r)][s][q] - agents["blind"][s][q] for s in seeds])
                 for q in qs} for r in ratios}
    return {"status": "computed", "limits_c": {lab: lim for lab, lim in limits},
            "knee": {"turb_knee_k": float(knee_k), "threshold_c": knee_c, "reached": bool(reached["knee"]),
                     "reached_850": bool(reached[ABOVE_850]), "highest_recorded_peak_c": float(highest),
                     "above_850_c": ABOVE_850_C},
            "agents": agents, "per_arm": per_arm, "differences": diffs, "baseline": base,
            "current_grade": cg, "current_grade_note": None if cg is not None else f"not computed: {cg_note}",
            "index": {"path": index_path, "sha_text": TC.sha_text(index_path), "files": len(index["files"]),
                      "command": index.get("command")},
            "records": records_dir, "shape": list(shape), "statement": TEMPS_STATEMENT}


# ------------------------------------------------------------------------------------------ the whole route
def compute(*, scores, records, jobs, root):
    """Everything core prints and writes but the files: (result, current-grade's trace or None, its dt)."""
    scores = os.path.abspath(scores)
    try:
        sc = load_scores(scores, root=root)
    except B58HError as exc:
        refuse(str(exc))
    why = commit_problem(scores, root=root)
    if why:
        refuse(f"the scores {scores}: {why}")
    roads_path = os.path.join(root, *ROADS.split("/"))
    why = commit_problem(roads_path, root=root)
    if why:
        refuse(f"{ROADS}: {why}")
    doc, checked = sc["doc"], sc["checked"]
    ratios, n_roads = list(doc["ratios"]), int(doc["n_roads"])
    seeds = [str(s) for s in checked["engines"][ENGINE]["seeds"]]
    D_base = one_base(checked)
    with open(roads_path, encoding="utf-8") as fh:
        rec = json.load(fh)
    try:
        if list(rec["ceilings"]["readings"]) != list(READING_RJ.values()):
            refuse(f"{ROADS}: ceilings.readings {rec['ceilings']['readings']}, not {list(READING_RJ.values())}")
        ceil = rec["ceilings"]["per_engine"][ENGINE]
        ceil = {"by": ceil["by"], "per_road": ceil["per_road"]}
        knee_k = float(rec["report"]["knee_shares"][ENGINE]["turb_knee_k"])
        hw = hand_written(ceil, ratios)
    except (KeyError, TypeError, ValueError) as exc:
        refuse(f"{ROADS}: a key core reads is not there ({exc!r})")
    del rec
    report_path = os.path.splitext(scores)[0] + ".txt"
    index_path = V.records_index_path(scores)
    inputs = {"scores": {"path": scores, "sha_text": sc["sha_text"], "sha256": sc["sha256"]},
              "report": {"path": report_path}, "index": {"path": index_path},
              "roads": {"path": ROADS, "sha_text": TC.sha_text(roads_path)}, "records": records}
    for key, rel in (("hw_opt_report", HW_OPT_REPORT), ("grids", GRIDS)):
        path = os.path.join(root, *rel.split("/"))
        inputs[key] = {"path": rel, "sha_text": TC.sha_text(path) if os.path.isfile(path) else None}
    for key in ("report", "index"):
        p = inputs[key]["path"]
        inputs[key]["sha_text"] = TC.sha_text(p) if os.path.isfile(p) else None

    dwhy = delivery_problem(doc, seeds=seeds)
    run, run_why, roads_check = current_grade(doc, jobs=jobs, root=root)
    controls = {"roads": roads_check}                       # the check's own outcome, not the run's (D1)
    c3 = control_3(ceil["per_road"], D_base)
    if run is None:
        status_i = f"not computed: {run_why}"
        cg_note = run_why
    else:
        cut = cuts_of(run["D"], D_base)
        controls["1"] = control_1(run["fuel"], doc, dwhy)
        controls["2"] = control_2(report_path, cut, root=root)
        failed = [n for n in ("1", "2") if not controls[n]["passed"]]
        status_i = ("computed" if not failed else "not computed: " + "; ".join(
            f"control {n} failed: {controls[n]['detail']}" for n in failed))
        cg_note = None if not failed else status_i[len("not computed: "):]
    controls["3"] = c3
    part_i = {"status": status_i, "label": DESCRIPTIVE}
    if status_i == "computed":
        part_i.update(savings(checked, run["D"], D_base))
        part_i["hand_written"] = hw
        part_i["control_3_beside"] = None if c3["passed"] else c3["by"]
        part_i["tuned_bests"], part_i["tuned_bests_note"] = read_beside(
            HW_OPT_REPORT, root=root, parse=lambda t: tuned_bests(t, ratios))
        part_i["tuned_bests_label"] = HW_LABEL
        part_i["decision13"], part_i["decision13_note"] = read_beside(GRIDS, root=root, parse=decision13)
        part_i["decision13_label"] = D13_LABEL
    pv = part_v(doc, ratios=ratios, seeds=seeds, problem=dwhy)
    cg_trace = run["trace"] if (run is not None and cg_note is None) else None
    p96 = part_96(index_path, records, sc=sc, seeds=seeds, ratios=ratios, n_roads=n_roads, knee_k=knee_k,
                  cg_trace=cg_trace, cg_dt=None if run is None else run["dt"], cg_note=cg_note, root=root)
    cg_block = {"run": "not completed: " + run_why} if run is None else {
        "run": "completed", "call": run["call"], "roads": n_roads, "steps": run["steps"], "dt": run["dt"],
        "arrays_sha256": run["arrays_sha256"], "D": run["D"], "fuel": run["fuel"],
        "demand_steps": run["demand_steps"], "short_steps": run["short_steps"],
        "npz": None}
    try:
        head = EF.git_head(root=root)[:7]
    except (EF.GitError, TypeError, ValueError):
        head = None
    result = {"schema": SCHEMA, "route": "core", "inputs": inputs, "ratios": ratios, "seeds": [int(s) for s in seeds],
              "n_roads": n_roads, "engine": ENGINE, "reward_knock": doc["provenance"]["reward_knock"],
              "with_knock_label": FEA.WITH_KNOCK_LABEL, "delivery_block": dwhy or "checked",
              "current_grade": cg_block, "controls": controls, "part_9_5_i": part_i, "part_9_5_v": pv,
              "part_9_6": p96,
              "provenance": {"versions": EF.versions(), "platform": platform.platform(), "git_head": head,
                             "command": " ".join(sys.argv)}}
    return result, (None if run is None else run["trace"]), (None if run is None else run["dt"])


# ------------------------------------------------------------------------------------------ the report
def _f(x, nd=4, sign=True):
    if x is None:
        return "n/a"
    return f"{x:+.{nd}f}" if sign else f"{x:.{nd}f}"


def _summary_line(name, sm, nd):
    sg = sm["signs"]
    signs = f"sign count positive {sg['positive']} / negative {sg['negative']} / zero {sg['zero']}"
    iv = sm["interval"]
    if iv is None:
        return f"      {name}: n {len(sm['values'])}; interval {sm['interval_note']}; {signs}"
    return (f"      {name}: n {iv['n']}, mean {_f(iv['mean'], nd)}, 95 % t interval [{_f(iv['lo'], nd)}, "
            f"{_f(iv['hi'], nd)}] (t {iv['t']:.4f}, sd {_f(iv['sd'], nd, False)}, unadjusted); {signs}")


def render(res):
    say = ["B58H CORE -- PR-B 9.5 (i), 9.5 (v) and 9.6 (rows 150 (i), 150 (v), 151; b58h_beside.py core)",
           f"  {DESCRIPTIVE}", "", "INPUTS"]
    inp = res["inputs"]
    say.append(f"  scores         {inp['scores']['path']}: sha_text {inp['scores']['sha_text']} (binds); raw sha256 "
               f"{inp['scores']['sha256']} (binds nothing, PR-B 5.2)")
    for key, name in (("report", "text report"), ("index", "records index"), ("roads", "roads.json"),
                      ("hw_opt_report", "hw_opt report"), ("grids", "grids print")):
        say.append(f"  {name:<14} {inp[key]['path']}: sha_text {inp[key]['sha_text']}")
    say.append(f"  records        {inp['records']}")
    say.append(f"  HEAD {res['provenance']['git_head']}; reward without the knock term "
               f"(provenance.reward_knock {res['reward_knock']}); core loads no agent")
    say.append(f"  delivery block: {res['delivery_block']}")
    say.append("")
    cg = res["current_grade"]
    say.append("CURRENT-GRADE'S RUN (PR-B 9.5 (i)): check_premise.p_grade_now through evaluate.run_road_episode, "
               "use_preview True, H = engine_env.PREVIEW_H_S, as score_set runs the hand-written policies "
               "(evaluate.py:1070-1071), on evaluate.decision34_roads' roads")
    if cg["run"] != "completed":
        say.append(f"  {cg['run']}")
    else:
        call = cg["call"]
        say.append(f"  {cg['roads']} roads, {cg['steps']} steps each at dt {cg['dt']:g} s; "
                   f"H {call['preview_h_s']:g} s; plant {call['plant']}; jobs {call['jobs']}")
        npz = cg["npz"] or {}
        say.append(f"  trace kept for 9.6: {npz.get('path')}, sha256 {npz.get('sha256')}")
    c = res["controls"]
    rc = c["roads"]
    say.append(f"  the roads check (epa_roads.arrays_sha256 against the scores' provenance.arrays_sha256): "
               f"{'PASS' if rc['passed'] else ('NOT RUN' if rc['passed'] is None else 'FAIL')}: {rc['detail']}")
    if "1" in c:
        say.append(f"  control 1 (its fuel equals the scores' delivery block, road by road, exactly): "
                   f"{'PASS' if c['1']['passed'] else 'FAIL'}: {c['1']['detail']}")
        say.append(f"  control 2 (its cut equals the text report's to two decimals, both readings, no knock [with "
                   f"knock, {FEA.WITH_KNOCK_LABEL}]): {'PASS' if c['2']['passed'] else 'FAIL'}: {c['2']['detail']}")
        say.append(f"    expected {c['2']['expected']!r}")
        say.append(f"    found    {c['2']['found']!r}")
    c3 = c["3"]
    say.append(f"  control 3 (roads.json per_road[k].D.neutral equals the scores' D_base, both readings, to 1e-6 "
               f"absolute): {'PASS' if c3['passed'] else 'FAIL'}: {c3['detail']}")
    if c3["by"]:
        for rd in READINGS:
            b = c3["by"][rd]
            say.append(f"    {_reading(rd)}: largest absolute difference {b['max_abs']:.3e} (road {b['road']}), "
                       f"largest relative {b['max_rel']:.3e}")
    say.append("")
    say += _render_i(res)
    say += _render_v(res)
    say += _render_96(res)
    return say


def _reading(rd):
    """A reading's name as printed: the with-knock reading always carries its label (PR-B:1101, :819)."""
    return "no knock" if rd == "no_knock" else f"with knock ({FEA.WITH_KNOCK_LABEL})"


def _render_i(res):
    p = res["part_9_5_i"]
    say = ["9.5 (i) EACH AGENT'S SAVING OVER CURRENT-GRADE, s = cut(agent) - cut(current-grade) (row 150 (i))"]
    if p["status"] != "computed":
        return say + [f"  {p['status']}", ""]
    lab = FEA.WITH_KNOCK_LABEL
    cut = p["current_grade_cut"]
    say.append(f"  current-grade's cut against the baseline ECU: evaluate.py's form "
               f"{_f(cut['no_knock']['evaluate_form'])} [with knock {_f(cut['with_knock']['evaluate_form'])}, {lab}]; "
               f"mean form "
               f"{_f(cut['no_knock']['mean_form'])} [with knock {_f(cut['with_knock']['mean_form'])}, {lab}]")
    for arm in ARMS:
        say.append(f"  {arm}:")
        for rd in READINGS:
            for form in ("evaluate_form", "mean_form"):
                st = p["per_arm"][arm][rd][form]
                tag = ("evaluate.py's form" if form == "evaluate_form" else "mean form") + (
                    ", no knock" if rd == "no_knock" else f", with knock ({lab})")
                say.append(f"    {tag}: {st['below_0']} of {st['n']} agents with s < 0; median {_f(st['median'])}, sd "
                           f"{_f(st['sd'], 4, False)} (ddof 1), range {_f(st['min'])} to {_f(st['max'])}")
        seeds = sorted(p["s"][arm], key=int)
        ev = {s: (p["s"][arm][s]["no_knock"]["evaluate_form"], p["s"][arm][s]["with_knock"]["evaluate_form"])
              for s in seeds}
        say.append(f"    per seed, s no knock [with knock, {lab}], evaluate.py's form: " + ", ".join(
            f"{s} {_f(ev[s][0])} [{_f(ev[s][1])}]" for s in seeds))
        rs = p["hand_written"]["by_arm"][arm]
        for rd in READINGS:
            parts = [f"({h['policy']}) at r = {h['r']} {_f(h['evaluate_form'])} [mean form {_f(h['mean_form'])}]"
                     for h in p["hand_written"]["table"][rd] if h["r"] in rs]
            tag = "no knock" if rd == "no_knock" else f"with knock ({lab})"
            say.append(f"    beside, hand-written savings over current-grade, evaluate.py's form, {tag}: "
                       + "; ".join(parts))
    if p["control_3_beside"]:
        say.append("  control 3 FAILED: the hand-written savings above are against roads.json's own runs; the "
                   "differences of its neutral D from the scores' D_base, beside them: " + "; ".join(
                       f"{_reading(rd)} largest absolute {b['max_abs']:.3e} (road {b['road']}), relative "
                       f"{b['max_rel']:.3e}"
                       for rd, b in p["control_3_beside"].items()))
    say.append(f"  row 153 (1)'s tuned bests, as its committed report prints them ({p['tuned_bests_label']}):")
    if p["tuned_bests"] is None:
        say.append(f"    {p['tuned_bests_note']}")
    else:
        for rd, block in p["tuned_bests"].items():
            tag = "" if rd == "noknock" else f", with knock ({lab})"
            say.append(f"    reading {rd}" + ("" if rd == "noknock" else f" ({lab})") + ":")
            for fam, lines in block["best"].items():
                for line in lines:
                    say.append(f"      {fam}, largest saving in evaluate.py's form{tag}: {line.strip()}")
            for line in block["frontier"]:
                say.append(f"      frontier, evaluate_form{tag}: {line.strip()}")
    say.append(f"  {p['decision13_label']}, grids_b58.txt:{GRIDS_LINES[0]}-{GRIDS_LINES[1]}:")
    if p["decision13"] is None:
        say.append(f"    {p['decision13_note']}")
    else:
        say += [f"    {line}" for line in p["decision13"]]
    return say + [""]


def _render_v(res):
    p = res["part_9_5_v"]
    say = ["9.5 (v) FUEL AND TORQUE PER SEED, sighted minus blinded at each r (row 150 (v); 9.1's definitions)"]
    if p["status"] != "computed":
        return say + [f"  {p['status']}", ""]
    say.append(f"  {p['statement']}; no reading (fuel and torque hold no damage)")
    names = {"fuel_figure": "fuel figure, % points", "mean_short_share": "mean short share (roads with a demand step)",
             "pooled_short_share": "pooled short share"}
    for r, block in p["differences"].items():
        say.append(f"  r = {r}:")
        for q, sm in block.items():
            nd = 4 if q == "fuel_figure" else 6
            say.append(_summary_line(names[q], sm, nd))
            if sm["dropped"]:
                say.append(f"        dropped (no demand step on any road in either arm): seeds {sm['dropped']}")
    for name, fig in p["beside"].items():
        say.append(f"  beside, {name}'s own: fuel figure {_f(fig['fuel_figure'])} %, mean short share "
                   f"{_f(fig['mean_short_share'], 6, False)}, pooled {_f(fig['pooled_short_share'], 6, False)}")
    for arm, ss in p["no_demand_seeds"].items():
        if ss:
            say.append(f"  {arm}: seeds with no demand step on any road: {ss}")
    return say + [""]


def _render_96(res):
    p = res["part_9_6"]
    say = ["9.6 THE TEMPERATURE ROWS, the modelled housing (row 151)"]
    if p["status"] != "computed":
        return say + [f"  {p['status']}", ""]
    say.append(f"  {p['statement']}")
    say.append(f"  records {p['records']}: {p['index']['files']} files, t_turb {tuple(p['shape'])}; index "
               f"{p['index']['path']}, sha_text {p['index']['sha_text']}, command {p['index']['command']!r}")
    labs = [lab for lab in p["limits_c"]]
    say.append("  limits, deg C (seconds strictly above, dt x steps): " + ", ".join(
        f"{lab} = {p['limits_c'][lab]:.2f}" for lab in labs))
    k = p["knee"]
    hit = [name for name, flag in (("the knee", k["reached"]), (f"{k['above_850_c']:g} deg C", k["reached_850"]))
           if flag]
    say.append(f"  850 deg C, both readings (PR-B 9.6): the knee, turb_knee_k {k['turb_knee_k']:.2f} K = "
               f"{k['threshold_c']:.2f} deg C (roads.json report.knee_shares), and {k['above_850_c']:.2f} deg C; "
               f"highest recorded peak {k['highest_recorded_peak_c']:.2f} deg C: "
               + (f"it reaches {' and '.join(hit)}, so the seconds above {' and above '.join(hit)} are reported"
                  if hit else "no recorded peak reaches either"))

    def row(x, highest="highest"):
        return (f"peak mean {x['peak_mean']:.2f}, {highest} {x['peak_max']:.2f} deg C; "
                + ", ".join(f"s above {lab} {x['above_' + lab]:.2f}" for lab in labs))
    cg = p["current_grade"]
    for arm in ARMS:
        say.append(f"  {arm}: mean over its seeds of each agent's {row(p['per_arm'][arm], 'highest peak')}; "
                   f"the arm's highest single peak {p['per_arm'][arm]['highest_peak']:.2f} deg C")
        say.append(f"    beside, {BASE}: {row(p['baseline'])}")
        say.append(f"    beside, {CG}: " + (row(cg) if cg is not None else p["current_grade_note"]))
        for s in sorted(p["agents"][arm], key=int):
            say.append(f"    seed {s}: {row(p['agents'][arm][s])}")
    for r, block in p["differences"].items():
        say.append(f"  r = {r}, sighted minus blinded per seed:")
        for q, sm in block.items():
            say.append(_summary_line(q, sm, 2))
    return say + [""]


# ------------------------------------------------------------------------------------------ the files
def _open_once(path, mode):
    """A new file ("x" or "xb"); a text file is UTF-8 with LF line ends on every platform (evaluate.write_once_json's
    rule), so its raw sha256 is the sha256 of the text written, which is what b58h_core.json records."""
    kw = {} if "b" in mode else {"encoding": "utf-8", "newline": "\n"}
    try:
        return open(path, mode, **kw)
    except FileExistsError:
        refuse(f"{path} exists: each output is written once")


def write_json_once(path, obj):
    text = json.dumps(obj, indent=1, sort_keys=True, allow_nan=False) + "\n"
    with _open_once(path, "x") as fh:
        fh.write(text)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_npz_once(path, trace, dt):
    with _open_once(path, "xb") as fh:
        np.savez(fh, dt=np.float64(dt), **{k: np.asarray(trace[k], dtype=np.float64) for k in TRACE_KEYS})
    return sha256_file(path)


INK, MUTED, GRID = "#0b0b0b", "#52514e", "#d9d8d4"
ARM_COLOUR = {"blind": "#2a78d6", "sighted_r0.5": "#eb6834", "sighted_r1.5": "#1baf7a"}
R_STYLE = {0: ("#2a78d6", "o"), 1: ("#eb6834", "s")}


def _figure(ncols, width, height=4.2):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, ncols, figsize=(width, height), squeeze=False)
    for ax in axes[0]:
        ax.set_facecolor("#fcfcfb")
        ax.grid(True, axis="y", color=GRID, linewidth=0.6)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
    fig.patch.set_facecolor("#fcfcfb")
    return plt, fig, axes[0]


def _save(plt, fig, path, legend_from=None, ncol=1):
    if legend_from is None:
        fig.tight_layout()
    else:
        handles, labels = legend_from.get_legend_handles_labels()
        fig.legend(handles, labels, loc="lower center", ncol=ncol, frameon=False, fontsize=8)
        fig.tight_layout(rect=(0.0, 0.03 + 0.055 * math.ceil(len(labels) / ncol), 1.0, 1.0))
    with _open_once(path, "xb") as fh:
        fig.savefig(fh, format="png", dpi=120)
    plt.close(fig)


def _not_computed_figure(path, title, status):
    plt, fig, axes = _figure(1, 8.0)
    axes[0].axis("off")
    import textwrap
    axes[0].text(0.02, 0.6, title + "\n\n" + "\n".join(textwrap.wrap(status, 90)), va="top", ha="left",
                 fontsize=9, color=INK, transform=axes[0].transAxes)
    _save(plt, fig, path)


def _jitter(i, n):
    return (i - (n - 1) / 2.0) / max(n, 1) * 0.5


def figure_s(res, path):
    p = res["part_9_5_i"]
    title = "9.5 (i): each agent's saving over current-grade, s (evaluate.py's form, no knock)"
    if p["status"] != "computed":
        return _not_computed_figure(path, title, p["status"])
    plt, fig, axes = _figure(1, 9.0, height=5.0)
    ax = axes[0]
    ax.axhline(0.0, color=MUTED, linewidth=1.5, label="current-grade (s = 0)")
    styles = {"a": "--", "b": ":", "a_b": "-."}
    notes = []
    for x, arm in enumerate(ARMS):
        seeds = sorted(p["s"][arm], key=int)
        ys = [p["s"][arm][s]["no_knock"]["evaluate_form"] for s in seeds]
        xs = [x + _jitter(i, len(seeds)) for i in range(len(seeds))]
        ax.scatter(xs, ys, s=28, color=ARM_COLOUR[arm], edgecolor="#fcfcfb", linewidth=0.8, zorder=3, label=arm)
        marks = {}                     # one line per policy and value: (b) and (a_b) agree at both r for blind
        for h in p["hand_written"]["table"]["no_knock"]:
            if h["r"] in p["hand_written"]["by_arm"][arm]:
                marks.setdefault((h["policy"], h["evaluate_form"]), []).append(h["r"])
        for (pol, value), rs in marks.items():
            ax.hlines(value, x - 0.3, x + 0.3, colors=INK, linestyles=styles[pol], linewidth=1.2, zorder=2)
            notes.append((x, value, f"({pol}) r={', '.join(rs)}"))
    lo, hi = ax.get_ylim()
    gap, last = 0.035 * (hi - lo), {}
    for x, value, text in sorted(notes):           # labels closer than the gap are staggered upwards
        y = max(value, last.get(x, -math.inf) + gap)
        last[x] = y
        ax.annotate(text, (x + 0.32, y), fontsize=6.5, color=MUTED, va="center")
    for pol, ls in styles.items():
        ax.plot([], [], color=INK, linestyle=ls, linewidth=1.2, label=f"hand-written ({pol}), roads.json")
    ax.set_xticks(range(len(ARMS)), list(ARMS))
    ax.set_xlim(-0.5, len(ARMS) - 0.1)
    ax.set_ylabel("s, points of cut (evaluate.py's form, no knock)", color=INK)
    ax.set_title(title, fontsize=10, color=INK)
    _save(plt, fig, path, legend_from=ax, ncol=4)


def figure_delivery(res, path):
    p = res["part_9_5_v"]
    title = "9.5 (v): sighted minus blinded per seed (no reading)"
    if p["status"] != "computed":
        return _not_computed_figure(path, title, p["status"])
    plt, fig, axes = _figure(3, 13.0)
    names = (("fuel_figure", "fuel figure, % points"), ("mean_short_share", "mean short share"),
             ("pooled_short_share", "pooled short share"))
    for ax, (q, label) in zip(axes, names):
        ax.axhline(0.0, color=MUTED, linewidth=1.0)
        for i, (r, block) in enumerate(p["differences"].items()):
            colour, marker = R_STYLE[i % 2]
            ax.scatter(block[q]["seeds"], block[q]["values"], s=26, color=colour, marker=marker,
                       edgecolor="#fcfcfb", linewidth=0.8, zorder=3, label=f"r = {r}")
        ax.set_xlabel("seed", color=INK)
        ax.set_ylabel(label + ", sighted minus blinded", color=INK, fontsize=8)
    fig.suptitle(title, fontsize=10, color=INK)
    _save(plt, fig, path, legend_from=axes[0], ncol=2)


def figure_temps(res, path):
    p = res["part_9_6"]
    title = "9.6: seconds above the housing limits, each agent's mean over the roads (modelled)"
    if p["status"] != "computed":
        return _not_computed_figure(path, title, p["status"])
    plt, fig, axes = _figure(2, 11.0)
    for ax, lab in zip(axes, (f"{lim:g}" for lim in LIMITS_C)):
        q = f"above_{lab}"
        for x, arm in enumerate(ARMS):
            seeds = sorted(p["agents"][arm], key=int)
            ys = [p["agents"][arm][s][q] for s in seeds]
            ax.scatter([x + _jitter(i, len(seeds)) for i in range(len(seeds))], ys, s=26, color=ARM_COLOUR[arm],
                       edgecolor="#fcfcfb", linewidth=0.8, zorder=3, label=arm)
        ax.axhline(p["baseline"][q], color=INK, linestyle="--", linewidth=1.2, label=BASE)
        if p["current_grade"] is not None:
            ax.axhline(p["current_grade"][q], color=MUTED, linestyle=":", linewidth=1.5, label=CG)
        ax.set_xticks(range(len(ARMS)), list(ARMS))
        ax.set_ylabel(f"seconds above {lab} deg C, mean over the roads", color=INK, fontsize=8)
    fig.suptitle(title, fontsize=10, color=INK)
    _save(plt, fig, path, legend_from=axes[0], ncol=5)


def run_core(*, scores, records, out, jobs, root):
    if jobs < 1:
        refuse(f"--jobs {jobs}: at least 1")
    if inside(out, root) or inside(out, HERE):
        refuse(f"--out {out} is inside the repository: the outputs are written outside it first (PR-B:1804-1806)")
    paths = {name: os.path.join(out, name) for name in OUT_FILES}
    there = [name for name, p in paths.items() if os.path.exists(p)]
    if there:
        refuse(f"--out {out} already holds {there}: each output is written once")
    res, trace, dt = compute(scores=scores, records=records, jobs=jobs, root=root)
    os.makedirs(out, exist_ok=True)
    if trace is not None:
        res["current_grade"]["npz"] = {
            "path": paths["current_grade.npz"], "sha256": write_npz_once(paths["current_grade.npz"], trace, dt),
            "format": "evaluate.write_records': dt, t_turb, t_oil, ki float64 (roads, steps)"}
    figure_s(res, paths["b58h_core_s.png"])
    figure_delivery(res, paths["b58h_core_delivery.png"])
    figure_temps(res, paths["b58h_core_temps.png"])
    res["figures"] = {name: sha256_file(paths[name]) for name in OUT_FILES if name.endswith(".png")}
    lines = render(res)
    text = "\n".join(lines) + "\n"
    with _open_once(paths["b58h_core.txt"], "x") as fh:
        fh.write(text)
    res["report_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    sha = write_json_once(paths["b58h_core.json"], res)
    print(text, end="")
    print(f"written under {out}: {', '.join(OUT_FILES if trace is not None else OUT_FILES[:-1])}; "
          f"b58h_core.json sha256 {sha}")
    return 0


def main(argv=None, *, root=HERE):
    p = argparse.ArgumentParser(prog="b58h_beside.py", description="The B58 study's descriptive rows beside d "
                                "(PR-B sections 9.5 (i), 9.5 (v) and 9.6, b58h_beside.py core).")
    p.add_argument("--list", action="store_true", help="print the routes present, one per line, and write nothing")
    sub = p.add_subparsers(dest="route")
    c = sub.add_parser("core", help="9.5 (i), 9.5 (v) and 9.6: current-grade's 20 roads, no agent loaded")
    c.add_argument("--scores", required=True, help="the committed scores document (scores_b58h.json)")
    c.add_argument("--records", required=True, help="the per-step records' folder (evaluate.py --records-out)")
    c.add_argument("--out", required=True, help="a folder outside the repository; every file is written once")
    c.add_argument("--jobs", type=int, default=1, help="current-grade's roads run in parallel (default 1)")
    a = p.parse_args(argv)
    if a.list:
        if a.route is not None:
            p.error("--list takes no route")
        for route in ROUTES:
            print(route)
        return 0
    if a.route is None:
        p.error(f"a route is required, or --list (routes present: {', '.join(ROUTES)})")
    return run_core(scores=a.scores, records=a.records, out=a.out, jobs=a.jobs, root=root)


if __name__ == "__main__":
    sys.exit(main())
