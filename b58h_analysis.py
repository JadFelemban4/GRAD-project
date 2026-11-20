"""b58h_analysis.py -- the B58 preview study's analysis (AB), PR-B sections 6, 7, 9.1 and 10.

    python -B b58h_analysis.py context --scores results/B58H_RESULT/scores_b58h.json --out C.json
    python -B b58h_analysis.py analyse --scores results/B58H_RESULT/scores_b58h.json --context C.json
                                       --out A.json --report A.txt

PR-B is results/PREREGISTRATION_B58H.md; "PR-B:n" cites its line n at T* (720587d). Where this file and PR-B
differ, PR-B governs (PR-B:488-490), and after the first scoring command a difference is a coding defect handled by
section 11 (PR-B:1180). The commands are PR-B 6.8's (PR-B:628-629), with item (b) of 6.9 their place in the order
(PR-B:654). Both run on the B58 study's scores alone, after scoring.

WHAT AB IS, AND WHAT IT MAY COMPUTE (PR-B 6.0, :469-487). This file reads the scores and the committed records
and writes the context and the analysis (PR-B:469-470). It computes what sections 6 and 9.1 state, and nothing
else (PR-B:481-482). For 6.1-6.7 every quantity, reading, form and rule is PR-B's (PR-B:482). A descriptive or
form detail PR-B does not fix is fixed below, before any score, as a choice that cannot move d, Delta, the band,
the status or any verdict (PR-B:483-485): "CHOICES" below. A computation of the primary analysis that needs a
choice PR-B does not fix prints every reading the words allow, calls none primary, and is recorded: "GAPS" below
(PR-B:485-487). Section 15 records both at AB's commit (PR-B:1834-1835).

NOTHING HERE LOADS AN AGENT (PR-B:475-476, :503-505). No function reads runs/, a model file or a checkpoint;
the scores document is the only score this file reads. Of roads.json, EPA_TIGHTENINGS.json and reverify.json only
the key paths named below are used: never commit_reveal, roads_seed, attempts or steps_log, and none is printed.

THE RULES, EACH WITH ITS PR-B LINES
  binding     the scores file is bound to its context by its sha_text (thresholds.common.sha_text, CRLF read as
              LF); its raw sha256 is kept beside it as a record that binds nothing (PR-B:461-463)
  d           per ratio r and seed, d = cut(sighted at r) - cut(blinded), each cut in evaluate.py's form
              (four_engine_analysis.cut, the median form evaluate.median_cut prints); the mean form beside it,
              deciding nothing (PR-B:509-515)
  readings    every damage number in the no-knock reading first, the with-knock reading beside it, labelled
              "not converged in dt on these roads" (four_engine_analysis.WITH_KNOCK_LABEL); a fuel or torque row
              has no reading and says so (PR-B:517-520)
  the tests   decision 30's paired one-sided t-test (primary) and the exact one-sided sign test (the declared
              secondary), each under row 113 (2)'s graph: run by four_engine_analysis.analyse, never here
              (PR-B:524-532)
  intervals   each d, per ratio, reading and form, with its two-sided 95 % t interval, mean +- t x sd / sqrt(n),
              sd at ddof 1, t = scipy.stats.t.ppf(0.975, n - 1), unadjusted for the graph (PR-B:536-538)
  Delta       Delta(s) = cut(sighted r = 1.5, s) - cut(sighted r = 0.5, s) in evaluate.py's form, with its
              interval and the exact two-sided sign test (twice the smaller one-sided tail of
              analyse_phase_d.sign_test on Delta and on -Delta, capped at 1); its mean form beside it; roads.json's
              hand-written prediction C_u(1.5) - C_u(0.5) beside both; exploratory, deciding nothing
              (PR-B:542-551)
  the band    Delta_e per ratio and reading, the root sum of squares of six parts, the linear sum beside it
              (PR-B:559-572); b = MEI / N_SHARES (four_engine_analysis.MEI, thresholds.contract.N_SHARES); d =
              four_engine_analysis.t_greater's mean of the paired d in evaluate.py's form; phi = max(1,
              |1 + ln(1 - c)|) at each arm's median over its seeds of its cuts (as a fraction), the larger of the
              sighted and blinded arms' (PR-B:559-563, :585-589, row 149 (2)(ii)-(iv)):
                PRIMARY, "kappa 1 in the contract's form": P1 = P2 = P5 = b (|d| / MEI) phi; P3 = b;
                  P4 = kappa_E8 b (|d| / MEI) phi; P6 = 0 (PR-B:565-578)
                OTHER, "b itself": P1 = P2 = P5 = b; the rest as PRIMARY (PR-B:579-581)
                VERSION 5's reading: the band left out, 0 at every ratio and reading (PR-B:593-594)
                COMPANION: as PRIMARY with P3 = kappa_L1 b, at the smallest and the largest kappa_L1 of
                  summary.json's engines (PR-B:596-599)
              only PRIMARY enters the context (PR-B:582); MODEL-LIMITED is four_engine_analysis.analyse's corners
              (d moved by -Delta_e and +Delta_e, the graph re-run), so each reading is one FEA.analyse run with
              that band in the context (PR-B:555-557); a d > 0 verdict that moves with the band is refused as a
              defect (PR-B:584-585)
  context     every value read, none typed (PR-B:603-605): engines_in_test from EPA_BACKEND.json in_test;
              seeds_per_arm epa_backend.B58H_N (row 147 (4)); model_band the PRIMARY Delta_e; ceiling roads.json
              ceilings.per_engine.b58.by[r].C at full precision; status_basis s_p from results/X2_RESULT.txt:24,
              pilot_pairs its n, s_star four_engine_analysis.status_star({b58: C(1.5)}, seeds_per_arm); status the
              rule's output, four_engine_analysis.validate_context's rule (PR-B:606-618); the s_p label in the
              provenance (PR-B:614-615)
  refusals    context: a record of the five not committed at HEAD; scores that are not the B58 alone, both
              ratios and seeds exactly 0 to B58H_N - 1; a provenance that does not read d34, version 6, the knock
              option false and roads.json's roads_sha (PR-B:633-635); a variant other than null (PR-B:433).
              analyse: the same refusals of the scores; a context for other scores (by sha_text) or for another
              reading of "at b"; a band that is not the one recomputed from the scores (PR-B:636-637)
  the report  four_engine_analysis.report verbatim, with AB's note above it saying its first lines are the
              committed script's fixed header (PR-B:620-623); then AB's blocks
  section 7   each verdict's sentence as section 7's table writes it, with d, the 95 % interval, the mean form,
              the band, the ceiling and the MEI, the with-knock reading of each in brackets (PR-B:676-698, :1101);
              the sign test beside every verdict in its own words, its with-knock reading in brackets; Delta
              labelled exploratory (PR-B:699-701); exploratory for every number (PR-B:702); AB's own text never
              holds the phrases of PR-B:703-704 (FORBIDDEN; the negation section 7 itself writes, "not a test of
              the H/tau criterion", PR-B:682, is allowed, and four_engine_analysis's verbatim report is not AB's
              text)
  9.1         per seed: the fuel figure, the mean over the roads of 100 (fuel / the baseline ECU's fuel - 1); the
              short share's mean over the roads with a demand step; its worst road; the pooled short share. Per
              arm: median, mean and range over the seeds of the fuel figure and of the mean short share, and the
              worst road over every seed; the baseline ECU's and current-grade's own figures beside; a seed with
              no demand step named; no reading; a refusal of the block is reported and the analysis still runs
              (PR-B:749-762, :1181)
  section 10  the beside values the analysis covers, each with its file and line (PR-B:1099-1113)
  everything  every number printed is reported, whatever it shows (PR-B:1154-1158); a document once written is
              kept, so every output is written once and an existing one is refused (PR-B:1159-1164)

WHAT IS READ, AND WHERE (paths read from their modules' constants where one exists)
  the scores                  --scores: four_engine_analysis.validate_scores, then load_scores' refusals
  results/EPA_ROADS/roads.json  ceilings.readings (must be roads_ceiling.READINGS), ceilings.per_engine.b58.
                              by[r].C, by[r].C_u.<noknock|knock>.<evaluate_form|mean> (Delta's prediction),
                              and by[r].a.knock.mean (the ceiling's with-knock reading, G11)
  results/EPA_TIGHTENINGS.json  E8.b58_u_val_kappa.with_roads.kappa (kappa_E8, P4)
  results/EPA_VALIDATION/summary.json  engines.<id>.kappa.L1 for every engine listed (the companion)
  results/EPA_BACKEND.json    in_test (engines_in_test)
  results/X2_RESULT.txt       line 24 (s_p, the no-knock spread, PR-B:612-613); line 11 (the with-knock spread,
                              section 10)
  results/X1_RESULT.txt       lines 29 and 60 (X1's spreads, section 10)
  results/EPA_ROADS/reverify.json  plants.b58.plant_sha_now and plant_sha_at_draw (section 10)
  A spread line is parsed by SD_LINE, "n <pairs> ... sd <x> points", CRLF read as LF; the section it sits under is
  the last unindented line above it, and is printed with it.

OUTPUTS. context: four-engine-context/1 (four_engine_analysis.validate_context passes before it is written).
analyse: b58h-analysis/1 JSON (the five four_engine_analysis results, the band under every reading, the flags,
the intervals, Delta, 9.1 or its refusal, section 10, the sentences) and the text report. Both JSON files with
indent 1, sorted keys, LF, ASCII, through four_engine_analysis._jsonable, as four_engine_analysis writes its
result; each file opened "x" (written once), analyse's two, the JSON first, before either is written (C2).

CHOICES THIS FILE FIXES BEFORE ANY SCORE (PR-B:483-485; none can move d, Delta, the band, the status or a verdict)
  C1  CLI: two subcommands, context and analyse, exactly PR-B 6.8's options; a refusal exits nonzero with
      "REFUSED: <reason>", a defect with "REFUSED (a defect of AB's code): <reason>"; nothing is written then.
  C2  Write-once: an existing --out or --report is refused before anything is read; --out and --report may not
      name one file. Every output's text is built and encoded, its folder made and its file opened "x" before any
      output is written (analyse: the JSON, then the report), so one that cannot be created (its folder path a
      file, say) is refused and leaves none written. A write that fails after the files are open (a full disk) is
      refused too, and every file the command opened, one written in full among them, is removed: a refused
      command leaves no document to block its rerun. A file named without a folder is written in the current one.
  C3  Paths recorded in the outputs are repository-relative with forward slashes when they lie in the
      repository, absolute otherwise; git_head is HEAD's first 7 hex digits.
  C4  context also requires the scores file itself committed at HEAD (6.9 (a) commits it before (b)).
  C5  analyse rebuilds the whole context from the scores and the re-read records, each checked committed at HEAD
      again, and refuses a context whose slots (the status basis among them), records' sha_text or provenance
      inputs differ from the rebuilt ones (floats to a relative and absolute 1e-12, every other value exactly);
      the raw sha256, the scores' path and git_head are not compared, since a CRLF checkout changes the raw
      sha256 and nothing else.
  C6  X2_RESULT.txt:24 must sit under its THERMAL-ONLY DAMAGE section (the no-knock one), and its n must equal
      four_engine_analysis.PILOT_PAIRS; otherwise context refuses.
  C7  The companion's smallest and largest kappa_L1 are taken by value; a tie takes the engine first in name
      order (equal kappa give equal bands).
  C8  Order of the report: the 4-line header, the note, four_engine_analysis.report verbatim, then section 7's
      sentences, the intervals, Delta, the band and the flags, 9.1, section 10. The sentences give r = 1.5 first,
      the graph's first test.
  C9  Number formats: d, Delta and their intervals signed at 2 decimals; the band and the ceiling at 2 in the
      sentences and at 4 in the band block, with the parts, phi and the kappas; p as four_engine_analysis._p
      prints it (4 decimals, or 2 significant digits in e-notation below 1e-4); t at 4; Delta's prediction at
      4; the fuel figure (%) and the shares at 4. The JSON holds every number at full precision.
  C10 The 9.1 validator (the block is the scores' provenance.delivery, evaluate.delivery_block's form): exactly
      the keys rule, hand and arms; hand holds the baseline ECU (evaluate.BASELINE) and current-grade (the
      evaluate.HAND_POLICIES name of check_premise.p_grade_now); the arms and seeds are the scores'; every
      policy's entry (reactive's included) holds exactly fuel, demand_steps, short_steps and short_share,
      each a list of n_roads; fuel finite, the baseline ECU's above 0 on every road; demand and short steps
      integers at least 0, short at most demand; short_share null exactly where demand is 0, else finite and
      short / demand to 1e-12. Any failure prints "REFUSED: <reason>" for 9.1 alone.
  C11 9.1 worst road: the road of the largest short share among the roads with a demand step; tied roads all
      listed, lowest first; "no demand step" when there is none. A seed with no demand step on any road has
      no mean short share and is named; an arm's statistics of the mean short share are over the seeds that
      have one, their count printed. Reactive's figures are not printed (PR-B names only the baseline ECU and
      current-grade). The baseline ECU's own fuel figure is printed (0 by its definition).
  C12 Section 10: a file of it that is absent or not committed at HEAD, or a line that does not parse, prints
      "not read: <reason>" and the analysis still runs; the practice spread reads "computed at item (c), after
      this analysis" (PR-B:655: it does not exist at item (b)). The rows of section 10 the other blocks print
      are named in one pointer line.
  C13 The forbidden-phrase check runs on AB's own text (everything but four_engine_analysis's verbatim report)
      before anything is written; a hit is a defect.

GAPS OF THE PRIMARY ANALYSIS (PR-B:485-487: every reading the words allow is printed, none is called primary)
  G1  "a verdict that does [depend on the assumed b] is printed by name" (PR-B:598-599): a MODEL-LIMITED flag
      that differs between PRIMARY and either companion, and one that differs between the two companions, are
      both printed by name; and every run's flag is printed for every verdict in the flags block.
  G2  Delta's mean form (PR-B:545): its own interval and two-sided sign test are printed beside, labelled
      deciding nothing.
  G3  Delta's prediction in the with-knock reading: PR-B names the no-knock C_u (PR-B:545-547), printed beside
      both readings; roads.json's C_u.knock difference is printed beside the with-knock Delta too, labelled.
  G4  Whether AB renders section 7's sentences (PR-B:583-584): it does, beside four_engine_analysis's own
      verdict lines, which stay verbatim.
  G5  Section 10's beside values (PR-B:1108-1110): all printed, with their file and line.
  G6  9.1's "the worst road over every seed" (PR-B:759-760): printed both as each seed's worst road and as the
      arm's one largest (seed, road), ties listed.
  G7  "the two-sided interval lies wholly below 0" (PR-B:685): the sentence prints for the verdict's interval
      (no knock, evaluate.py's form); whether the with-knock and the mean-form intervals lie wholly below 0 is
      printed beside, in their own brackets.
  G8  "MODEL-LIMITED under the other reading of 'at b'" (PR-B:583-584, "every verdict"; PR-B:556, "either
      test"): printed in the words of the t-test's verdict and of the sign test's, each in its no-knock sentence
      and in its with-knock bracket, when the OTHER run alone flags that verdict; when PRIMARY flags it, the
      words read ", MODEL-LIMITED" after the verdict (one punctuation for both tests, in the head, the brackets and
      the sign words) and the sentence carries PR-B:684's words; every run's flag is printed in the flags block
      whatever they read.
  G9  How analyse detects "another reading of 'at b'" (PR-B:636-637): both readings of the words are applied,
      the context's recorded label (provenance.at_b) and the band recomputed from the scores.
  G10 phi at a median cut at or above 100 % (PR-B 6.5 has ln(1 - c)): refused with AB's message; it cannot
      occur on real scores, whose every damage is above 0.
  G11 The ceiling's with-knock reading ("the ceiling at that ratio, with the with-knock reading beside it in
      brackets", PR-B:676-678): C is roads.json by[r].C, which roads_ceiling sets to by[r].a.noknock.mean, the
      no-knock reading's; it stays the context's ceiling and the no-knock sentence's (PR-B 6.7). The with-knock
      bracket prints by[r].a.knock.mean beside it, labelled, and the analysis JSON records it with its key path;
      it decides nothing.

WHERE THIS FILE DEPARTS FROM THE AGENTS' DESIGN NOTE OF 19 NOVEMBER (PR-B governs it)
  - Section 7's sentences are copied in ASCII ("H = r x tau", "H/tau", "Delta"), since the note also asks for an
    ASCII report; the words are otherwise PR-B:682-685's, filled.
  - 9.1's per-arm statistics of the fuel figure are over every seed, as PR-B:759-760 reads ("over the seeds"); the
    mean short share's are over the seeds that have one (C11).
  - Beyond the note's list of analyse's refusals, C5 and C6 refuse a context or an X2 line that the records do
    not give; both are refusals of form, never readings.
  - PR-B's no-knock prediction of Delta is printed once, beside both forms and both readings; the note's C_u.knock
    difference beside the with-knock Delta (G3).
  - 9.1's worst road is printed per seed as well as the arm's one largest (G6); the validator checks reactive's
    entry's form too (C10), although reactive is not printed.
  - The note puts "MODEL-LIMITED under the other reading of 'at b'" on the no-knock t-test's verdict alone;
    PR-B:556 and :583-584 put it on every verdict of either test, so the sign test's words carry it too (G8).
  - The with-knock bracket carries the with-knock mean form, band and ceiling as well as d (PR-B:676-678, :1101;
    G11).
"""
import argparse
import copy
import hashlib
import json
import math
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyse_phase_d as APD          # noqa: E402  sign_test, the exact one-sided sign test X1 and X2 used
import check_premise as CP             # noqa: E402  p_grade_now, current-grade's function (its name only)
import engines                         # noqa: E402  BACKEND_REL
import epa_backend as EB               # noqa: E402  B58H_N, row 147 (4); B58H_ENGINE
import epa_freeze as EF                # noqa: E402  committed_at_head, git_head
import epa_roads as ER                 # noqa: E402  roads_sha, ROADS_REL, TIGHTENINGS_REL, SUMMARY_REL
import evaluate as V                   # noqa: E402  DECISION_34, REDRAW_READING, BASELINE, HAND_POLICIES
import four_engine_analysis as FEA     # noqa: E402
import four_engine_roads as FER        # noqa: E402  REVERIFY_REL
import roads_ceiling as RC             # noqa: E402  READINGS, roads.json's reading keys
from thresholds import common as TC    # noqa: E402  sha_text, CRLF read as LF
from thresholds import contract as TCON  # noqa: E402  N_SHARES, PARTS

SCHEMA = "b58h-analysis/1"
ENGINE = EB.B58H_ENGINE
ROADS = ER.ROADS_REL
TIGHTENINGS = ER.TIGHTENINGS_REL
SUMMARY = ER.SUMMARY_REL
BACKEND = engines.BACKEND_REL
REVERIFY = FER.REVERIFY_REL
X2_RESULT = "results/X2_RESULT.txt"            # PR-B:612-613
X1_RESULT = "results/X1_RESULT.txt"            # PR-B:1110
CONTEXT_RECORDS = (ROADS, TIGHTENINGS, SUMMARY, BACKEND, X2_RESULT)        # PR-B:633-634
ARMS = ("blind",) + tuple(FEA.arm_name(r) for r in FEA.RATIOS)
RATIO_LO, RATIO_HI = FEA.RATIOS
ROADS_READING = dict(zip(FEA.READINGS, RC.READINGS))        # no_knock -> noknock, with_knock -> knock
X2_SP_LINE = 24                    # PR-B:612: X2's no-knock spread
X2_SP_SECTION = "THERMAL-ONLY DAMAGE"
X2_KNOCK_LINE = 11                 # section 10's "X2's ... with knock" (its TOTAL DAMAGE section)
X1_LINES = (29, 60)                # section 10's X1 spreads (TOTAL DAMAGE and THERMAL-ONLY DAMAGE)
SD_LINE = re.compile(r"^\s*n\s+(\d+)\b.*\bsd\s+([-+0-9.]+)\s+points\s*$")
AT_B_PRIMARY = "kappa 1 in the contract's form"     # PR-B:577
AT_B_OTHER = "b itself"                             # PR-B:579
S_P_LABEL = "X2's spread: another plant, road and budget; not a pilot of this study"   # PR-B:614-615
PRACTICE_SENTENCE = "computed at item (c), after this analysis"
NO_READING = "no reading: fuel and torque hold no damage"
TOL = 1e-12
RUNS = ("primary", "other_at_b", "version_5", "companion_min", "companion_max")
CURRENT_GRADE = {fn: name for name, fn in V.HAND_POLICIES}[CP.p_grade_now.__name__]
BASELINE = V.BASELINE
PER_KEYS = ("fuel", "demand_steps", "short_steps", "short_share")
# PR-B:703-704, never in AB's own text; "not a test of the H/tau criterion" (PR-B:682) does not contain the first
FORBIDDEN = ("a test of the criterion", "a collapse", "h/tau governs", "h/\u03c4 governs", "the criterion holds",
             "the criterion fails", "preview does not help")
NOTE = ("NOTE (PR-B 6.7): below, four_engine_analysis's report verbatim. Its first line, 'FOUR-ENGINE TEST (row "
        "113)', is the committed script's fixed header, followed by its line 'ONE ENGINE: the four-engine test does "
        "not run (row 107 (2))': with one engine the four-engine test does not run, and the analysis is exploratory.")
# section 7's table (PR-B:682-685), in ASCII; {flag} carries "MODEL-LIMITED ..." inside the sentence (PR-B:684)
D_GT_0 = ("On decision 34's roads, B58 agents that saw the grade H = {r} x tau ahead took less simulated turbine and "
          "oil damage (the no-knock reading) on the B58 model, which is not validated (its band assumed at b; "
          "section 12.1), than their blinded twins (paired t under the graph, adjusted p = {p}; d = {d} points, "
          "two-sided 95 % t interval {lo} to {hi}, against an MEI of {mei} points; n = {n} seeds per arm){flag}. "
          "Exploratory, on one plant; not a test of the H/tau criterion.")
NOT_SHOWN = ("The study does not show a preview effect at H = {r} x tau in the simulated turbine and oil damage (the "
             "no-knock reading) of the B58 model, which is not validated, on these roads (d = {d} points, two-sided "
             "95 % t interval {lo} to {hi}, against an MEI of {mei} points){flag}. A null was the expected outcome "
             "(row 147 (7)) and says nothing against the criterion.")
BELOW_ZERO = ("The sighted agents at r = {r} took more simulated turbine and oil damage (the no-knock reading) on the "
              "B58 model, which is not validated (its band assumed at b; section 12.1), than their blinded twins on "
              "these roads (d = {d} points, two-sided 95 % t interval {lo} to {hi}, against an MEI of {mei} "
              "points){flag}: a finding about this learner and recipe at this budget, never evidence that preview "
              "is worthless, and never read as a result about the criterion.")
ML_PRIMARY = (", MODEL-LIMITED: it changes within the B58's model band, so the plant's unvalidated model, not the "
              "agents, may decide it (row 113 (6))")
ML_OTHER = ", MODEL-LIMITED under the other reading of 'at b'"
ML_FLAG = ", MODEL-LIMITED"            # after a verdict of either test, in its bracket too (G8)
DELTA_STATEMENTS = ("Delta's spread is UNKNOWN: no spread of a difference between two sighted arms has been measured.",
                    "a Delta interval covering 0 says nothing about preview value across H.",
                    "Delta decides nothing about the criterion; it is exploratory.")


class B58HError(ValueError):
    """A refusal of AB's: the text names what was refused and why."""


class DefectError(B58HError):
    """A defect of AB's own code (PR-B 6.5's band that moves a d > 0 verdict, a forbidden phrase in AB's text):
    the step stops and the refusal is reported (PR-B:1180)."""


# ------------------------------------------------------------------------------------------ shared helpers
def sha256_file(path):
    """Raw sha256 of a file's bytes (a record that binds nothing, PR-B 5.2)."""
    with open(path, "rb") as fh:
        return hashlib.sha256(fh.read()).hexdigest()


def shown(path, root=HERE):
    """A path as the outputs record it: repository-relative with "/" inside `root`, else absolute (C3)."""
    p = os.path.abspath(path)
    try:
        rel = os.path.relpath(p, os.path.abspath(root))
    except ValueError:                      # another drive
        return p.replace(os.sep, "/")
    if rel == os.pardir or rel.startswith(os.pardir + os.sep) or os.path.isabs(rel):
        return p.replace(os.sep, "/")
    return rel.replace(os.sep, "/")


def require_committed(relpaths, *, root=HERE):
    """Refuse unless every path (repository-relative, or absolute inside `root`) is in HEAD's tree and the
    working file is that blob (epa_freeze.committed_at_head: a CRLF checkout of an LF blob counts as committed)."""
    bad = []
    for p in relpaths:
        try:
            ok = EF.committed_at_head(p, root=root)
            why = "absent, untracked or changed"
        except (ValueError, TypeError, OSError, EF.FreezeRefusal) as e:
            ok, why = False, str(e)
        if not ok:
            bad.append(f"{shown(p, root) if os.path.isabs(p) else p} ({why})")
    if bad:
        raise B58HError(f"not committed at HEAD in {root}: " + "; ".join(bad))


def git_head(root=HERE):
    """HEAD's first 7 hex digits (C3)."""
    try:
        return EF.git_head(root=root)[:7]
    except (TypeError, OSError, EF.FreezeRefusal) as e:
        raise B58HError(f"git HEAD in {root}: {e}")


def load_scores(path, *, root=HERE):
    """Read and check the scores document (PR-B 6.8): four_engine_analysis.validate_scores, then the B58
    alone, both ratios, the three arms, seeds exactly 0..B58H_N-1, no variant, and a provenance that reads
    d34, version 6, the knock option false and roads.json's roads_sha. Returns {"doc", "path", "sha_text",
    "sha256", "checked"}; raises B58HError."""
    try:
        with open(path, "rb") as fh:
            raw = fh.read()
    except OSError as e:
        raise B58HError(f"{path}: cannot be read ({e})")
    try:
        doc = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as e:
        raise B58HError(f"{path}: not a JSON document ({e})")
    try:
        checked = FEA.validate_scores(doc)
    except FEA.AnalysisError as e:
        raise B58HError(f"{path}: {e}")
    if set(doc["engines"]) != {ENGINE}:
        raise B58HError(f"{path}: engines {sorted(doc['engines'])}, the study scores the B58 alone")
    if list(doc["ratios"]) != list(FEA.RATIOS):
        raise B58HError(f"{path}: ratios {doc['ratios']}, the study scores both, {' and '.join(FEA.RATIOS)}")
    arms = doc["engines"][ENGINE]["arms"]
    if tuple(sorted(arms)) != tuple(sorted(ARMS)):
        raise B58HError(f"{path}: arms {sorted(arms)}, the study has {list(ARMS)}")
    want = [str(s) for s in range(EB.B58H_N)]
    for arm in ARMS:
        got = sorted(arms[arm]["seeds"], key=int)
        if got != want:
            raise B58HError(f"{path}: {arm}'s seeds {got}, the study's are exactly 0-{EB.B58H_N - 1}")
    if doc.get("variant") is not None:
        raise B58HError(f"{path}: variant {doc['variant']!r}; the primary scoring's variant is null (PR-B 5.2)")
    prov = doc.get("provenance")
    if not isinstance(prov, dict):
        raise B58HError(f"{path}: provenance {type(prov).__name__}, an object naming the protocol is required")
    want_prov = (("protocol", V.DECISION_34), ("reading", V.REDRAW_READING), ("reward_knock", False))
    for key, value in want_prov:
        if prov.get(key) != value or type(prov.get(key)) is not type(value):
            raise B58HError(f"{path}: provenance.{key} {prov.get(key)!r}, not {value!r}")
    try:
        roads_sha = ER.roads_sha(os.path.join(root, *ROADS.split("/")))
    except OSError as e:
        raise B58HError(f"{ROADS}: cannot be read ({e})")
    if prov.get("roads_sha") != roads_sha:
        raise B58HError(f"{path}: provenance.roads_sha is not roads.json's ({roads_sha[:7]})")
    return {"doc": doc, "path": path, "sha_text": TC.sha_text(path), "sha256": hashlib.sha256(raw).hexdigest(),
            "checked": checked}


def t_interval(values):
    """Mean, sd (ddof 1), n and the two-sided 95 % t interval mean +- t_0.975,n-1 x sd / sqrt(n), unadjusted
    (PR-B 6.3); t from scipy.stats.t (power_b58.txt:33-34 prints it at 4 decimals)."""
    from scipy import stats
    x = np.asarray(values, dtype=float)
    n = int(x.size)
    if n < 2:
        raise B58HError(f"an interval needs at least 2 values, got {n}")
    mean = float(x.mean())
    sd = float(x.std(ddof=1))
    t = float(stats.t.ppf(0.975, n - 1))
    half = t * sd / math.sqrt(n)
    return {"mean": mean, "sd": sd, "n": n, "t": t, "lo": mean - half, "hi": mean + half}


def sign_counts(values):
    """The sign count: how many values are positive, negative and zero."""
    x = [float(v) for v in values]
    return {"positive": sum(v > 0 for v in x), "negative": sum(v < 0 for v in x), "zero": sum(v == 0 for v in x)}


def sign_two_sided(values):
    """The exact two-sided sign test of PR-B 6.4: twice the smaller of the two one-sided tails of
    analyse_phase_d.sign_test, on the values and on their negatives, capped at 1 (zeros dropped)."""
    x = [float(v) for v in values]
    return min(1.0, 2.0 * min(APD.sign_test(x)[2], APD.sign_test([-v for v in x])[2]))


# ------------------------------------------------------------------------------------------ reading records
def _path(root, rel):
    return os.path.join(root, *rel.split("/"))


def _json(root, rel):
    try:
        with open(_path(root, rel), encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError) as e:
        raise B58HError(f"{rel}: cannot be read as JSON ({e})")


def _lines(root, rel):
    """A text record's lines, CRLF read as LF (the .txt records check out CRLF on this laptop)."""
    try:
        with open(_path(root, rel), "rb") as fh:
            return fh.read().replace(b"\r\n", b"\n").decode("utf-8").split("\n")
    except (OSError, UnicodeDecodeError) as e:
        raise B58HError(f"{rel}: cannot be read as text ({e})")


def _walk(obj, keys, where):
    for k in keys:
        if not isinstance(obj, dict) or k not in obj:
            raise B58HError(f"{where}: no key {'.'.join(keys)}")
        obj = obj[k]
    return obj


def _number(v, where):
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v):
        raise B58HError(f"{where}: a finite number is required, found {v!r}")
    return float(v)


def read_sd_line(root, rel, lineno):
    """A spread line of a committed result record: {"value", "n", "line", "section", "where"}. The section is
    the last unindented line above it (C6, C12). Refuses a line that does not read SD_LINE."""
    lines = _lines(root, rel)
    if lineno > len(lines):
        raise B58HError(f"{rel} has {len(lines)} lines, line {lineno} was to be read")
    text = lines[lineno - 1]
    m = SD_LINE.match(text)
    if not m:
        raise B58HError(f"{rel}:{lineno} does not read 'n <pairs> ... sd <x> points': {text.strip()!r}")
    try:
        value = float(m.group(2))
    except ValueError:
        raise B58HError(f"{rel}:{lineno}: sd {m.group(2)!r} is not a number")
    section = next((x for x in reversed(lines[:lineno - 1]) if x.strip() and not x[0].isspace()), None)
    return {"value": value, "n": int(m.group(1)), "line": text.strip(), "section": section,
            "where": f"{rel}:{lineno}"}


def read_records(root=HERE, *, check=True):
    """The five records PR-B 6.8 names, each committed at HEAD (checked here unless the caller has just
    checked them), by the key paths in the docstring."""
    if check:
        require_committed(CONTEXT_RECORDS, root=root)
    roads = _json(root, ROADS)
    readings = _walk(roads, ("ceilings", "readings"), ROADS)
    if list(readings) != list(RC.READINGS):
        raise B58HError(f"{ROADS}: ceilings.readings {readings!r}, roads_ceiling.READINGS is {list(RC.READINGS)}")
    by = _walk(roads, ("ceilings", "per_engine", ENGINE, "by"), ROADS)
    where = f"{ROADS} ceilings.per_engine.{ENGINE}.by"
    ceiling = {r: _number(_walk(by, (r, "C"), where), f"{where}['{r}'].C") for r in FEA.RATIOS}
    kpa = ("a", ROADS_READING["with_knock"], "mean")
    ceiling_knock = {r: _number(_walk(by, (r,) + kpa, where), f"{where}['{r}'].{'.'.join(kpa)}") for r in FEA.RATIOS}
    c_u ={r: {rd: {form: _number(_walk(by, (r, "C_u", ROADS_READING[rd], form), where),
                                  f"{where}['{r}'].C_u.{ROADS_READING[rd]}.{form}")
                    for form in ("evaluate_form", "mean")} for rd in FEA.READINGS} for r in FEA.RATIOS}
    del roads
    kpath = ("E8", "b58_u_val_kappa", "with_roads", "kappa")
    kappa_e8 = _number(_walk(_json(root, TIGHTENINGS), kpath, TIGHTENINGS), f"{TIGHTENINGS} {'.'.join(kpath)}")
    summ = _walk(_json(root, SUMMARY), ("engines",), SUMMARY)
    if not isinstance(summ, dict) or not summ:
        raise B58HError(f"{SUMMARY}: engines holds no engine, the companion needs kappa.L1 of each")
    kappa_l1 = {e: _number(_walk(summ, (e, "kappa", "L1"), SUMMARY), f"{SUMMARY} engines.{e}.kappa.L1")
                for e in sorted(summ)}
    in_test = _walk(_json(root, BACKEND), ("in_test",), BACKEND)
    if not isinstance(in_test, list) or not all(isinstance(e, str) for e in in_test) or ENGINE not in in_test:
        raise B58HError(f"{BACKEND}: in_test {in_test!r}, a list holding {ENGINE!r} is required")
    sp = read_sd_line(root, X2_RESULT, X2_SP_LINE)
    if not (sp["section"] or "").startswith(X2_SP_SECTION):
        raise B58HError(f"{sp['where']} sits under {sp['section']!r}, not under the {X2_SP_SECTION} section "
                        "(the no-knock reading, PR-B 6.7)")
    if sp["n"] != FEA.PILOT_PAIRS:
        raise B58HError(f"{sp['where']}: n {sp['n']}, row 103 (4)'s factor is for {FEA.PILOT_PAIRS} pairs")
    shas = {rel: TC.sha_text(_path(root, rel)) for rel in CONTEXT_RECORDS}
    return {"ceiling": ceiling, "ceiling_knock": ceiling_knock, "c_u": c_u, "kappa_e8": kappa_e8,
            "kappa_l1": kappa_l1, "in_test": list(in_test), "s_p": sp, "sha_text": shas}


# ------------------------------------------------------------------------------------------ the band (6.5)
def part_rows():
    """The six parts' names and rows from thresholds.contract.PARTS; P6 reads as its description, the table."""
    names = [p[0] for p in TCON.PARTS]
    if names != ["P1", "P2", "P3", "P4", "P5", "P6"]:
        raise DefectError(f"thresholds.contract.PARTS names {names}, PR-B 6.5's table has P1 to P6")
    return {p[0]: (p[1] if p[0] == "P6" else "/".join(p[2])) for p in TCON.PARTS}


def phi_of(c):
    """max(1, |1 + ln(1 - c)|) at a median cut c as a fraction (MD:176-186; PR-B 6.5); c >= 1 refused (G10)."""
    if not c < 1.0:
        raise B58HError(f"a median cut of {100.0 * c:.2f} %: phi = max(1, |1 + ln(1 - c)|) needs c below 100 % "
                        "(it cannot occur on real scores, whose every damage is above 0)")
    return max(1.0, abs(1.0 + math.log(1.0 - c)))


def band_point(eng, ratio, reading):
    """d (t_greater's mean of the paired d in evaluate.py's form), each arm's median cut and phi, the larger
    phi, at one ratio and reading (row 149 (2)(iii)-(iv))."""
    rows = FEA.paired_d(eng, ratio, reading)
    d = FEA.t_greater([v[0] for v in rows])["mean"]
    cuts = {FEA.arm_name(ratio): [v[2] for v in rows], "blind": [v[3] for v in rows]}
    c, phi = {}, {}
    for arm, xs in cuts.items():
        c[arm] = float(np.median(xs)) / 100.0
        try:
            phi[arm] = phi_of(c[arm])
        except B58HError as e:
            raise B58HError(f"r = {ratio}, {reading}, the {arm} arm: {e}")
    return {"d": d, "median_cut": c, "phi_arm": phi, "phi": max(phi.values())}


def band_parts(point, *, b, mei, kappa_e8, at_b, p3_kappa=None):
    """PR-B 6.5's six parts at one point, under one reading of "at b", P3 at p3_kappa x b for a companion."""
    m = b * (abs(point["d"]) / mei) * point["phi"]
    mult = m if at_b == AT_B_PRIMARY else b
    parts = {"P1": mult, "P2": mult, "P3": b if p3_kappa is None else p3_kappa * b, "P4": kappa_e8 * m,
             "P5": mult, "P6": 0.0}
    vals = [parts[k] for k in ("P1", "P2", "P3", "P4", "P5", "P6")]
    return {"parts": parts, "multiplicative": m, "delta_e": math.sqrt(sum(v * v for v in vals)),
            "linear_sum": sum(vals)}


def companions(records):
    """The smallest and the largest kappa_L1 over summary.json's engines, by value (C7)."""
    items = sorted(records["kappa_l1"].items())          # name order: min and max keep the first of a tie
    lo, hi = min(items, key=lambda kv: kv[1]), max(items, key=lambda kv: kv[1])
    return {"companion_min": {"engine": lo[0], "kappa": lo[1]}, "companion_max": {"engine": hi[0], "kappa": hi[1]}}


def run_label(name, comp):
    if name == "primary":
        return f"PRIMARY: the reading of 'at b' {AT_B_PRIMARY!r}, the context's band"
    if name == "other_at_b":
        return f"OTHER reading of 'at b': {AT_B_OTHER!r}, deciding nothing"
    if name == "version_5":
        return "VERSION 5's reading: the B58's band left out (0), deciding nothing"
    c = comp[name]
    which = "smallest" if name == "companion_min" else "largest"
    return (f"COMPANION: P3 at kappa_L1 x b, the {which} kappa_L1, {c['kappa']:.4f} ({c['engine']}); "
            "every other part as PRIMARY; deciding nothing")


def bands(eng, records):
    """Every reading of the band: {"points", "tables": {run: {r: {reading: parts}}}, "model_band": {run: ...},
    "companions", "b", "MEI", "N_SHARES", "kappa_E8", "labels"}."""
    if FEA.MEI != TCON.MEI:
        raise DefectError(f"four_engine_analysis.MEI {FEA.MEI} and thresholds.contract.MEI {TCON.MEI} differ")
    b = FEA.MEI / TCON.N_SHARES
    comp = companions(records)
    points = {r: {rd: band_point(eng, r, rd) for rd in FEA.READINGS} for r in FEA.RATIOS}
    spec = {"primary": (AT_B_PRIMARY, None), "other_at_b": (AT_B_OTHER, None),
            "companion_min": (AT_B_PRIMARY, comp["companion_min"]["kappa"]),
            "companion_max": (AT_B_PRIMARY, comp["companion_max"]["kappa"])}
    tables = {}
    for name in RUNS:
        tables[name] = {}
        for r in FEA.RATIOS:
            tables[name][r] = {}
            for rd in FEA.READINGS:
                if name == "version_5":
                    tables[name][r][rd] = {"parts": None, "multiplicative": None, "delta_e": 0.0, "linear_sum": 0.0}
                else:
                    at_b, k = spec[name]
                    tables[name][r][rd] = band_parts(points[r][rd], b=b, mei=FEA.MEI, kappa_e8=records["kappa_e8"],
                                                     at_b=at_b, p3_kappa=k)
    model_band = {name: {ENGINE: {r: {rd: tables[name][r][rd]["delta_e"] for rd in FEA.READINGS}
                                  for r in FEA.RATIOS}} for name in RUNS}
    rows = part_rows()
    labels = {"P1": f"{rows['P1']}: no row: assumed at b", "P2": f"{rows['P2']}: no row: assumed at b",
              "P3": f"{rows['P3']}: b (additive; kappa 1), kappa_L1 x b in the companion",
              "P4": f"{rows['P4']}: kappa_E8 x b x (|d| / MEI) x phi",
              "P5": f"{rows['P5']}: no row: assumed at b", "P6": f"{rows['P6']}: nothing (the exact cycle)"}
    return {"points": points, "tables": tables, "model_band": model_band, "companions": comp, "b": b,
            "MEI": FEA.MEI, "N_SHARES": TCON.N_SHARES, "kappa_E8": records["kappa_e8"],
            "kappa_L1": dict(records["kappa_l1"]), "labels": labels,
            "run_labels": {name: run_label(name, comp) for name in RUNS}}


# ------------------------------------------------------------------------------------------ the context (6.7)
def assemble_context(sc, records, *, root=HERE):
    """The context four_engine_analysis.validate_context needs, from the checked scores and the records."""
    eng = sc["checked"]["engines"][ENGINE]
    bd = bands(eng, records)
    n = EB.B58H_N
    s_p = records["s_p"]["value"]
    s_star = FEA.status_star({ENGINE: records["ceiling"][FEA.S_STAR_RATIO]}, n)[ENGINE]
    rule = "confirmatory" if FEA.pilot_factor() * s_p <= s_star else "exploratory"
    ctx = {"schema": FEA.CONTEXT_SCHEMA, "engines_in_test": list(records["in_test"]), "seeds_per_arm": n,
           "model_band": bd["model_band"]["primary"], "ceiling": {ENGINE: dict(records["ceiling"])},
           "status": {ENGINE: rule},
           "status_basis": {"s_p": s_p, "pilot_pairs": records["s_p"]["n"], "s_star": {ENGINE: s_star}},
           "provenance": {"scores": {"path": shown(sc["path"], root), "sha_text": sc["sha_text"],
                                     "sha256": sc["sha256"]},
                          "at_b": AT_B_PRIMARY, "s_p_label": S_P_LABEL, "records": dict(records["sha_text"]),
                          "inputs": {"kappa_E8": records["kappa_e8"], "kappa_L1": dict(records["kappa_l1"]),
                                     "b": bd["b"], "MEI": bd["MEI"], "N_SHARES": bd["N_SHARES"],
                                     "ceiling": dict(records["ceiling"]), "s_p": s_p,
                                     "s_p_line": records["s_p"]["where"], "pilot_pairs": records["s_p"]["n"]},
                          "band": {"points": bd["points"], "parts": bd["tables"]["primary"],
                                   "labels": bd["labels"]},
                          "git_head": git_head(root)}}
    try:
        FEA.validate_context(ctx, sc["checked"])
    except FEA.AnalysisError as e:
        raise B58HError(f"the context assembled does not pass four_engine_analysis.validate_context: {e}")
    return ctx, bd


def _refuse_existing(*paths):
    real = [os.path.abspath(p) for p in paths]
    if len(set(os.path.normcase(p) for p in real)) != len(real):
        raise B58HError("the outputs name one file twice: " + ", ".join(paths))
    for p in paths:
        if os.path.exists(p):
            raise B58HError(f"{p} exists: a document of this study, once written, is kept (PR-B:1159-1160)")


def _abandon(opened, why):
    """Close and remove every file one _write_all call opened (each opened "x" by it, so none existed before), and
    return the refusal to raise (C1, C2: a refused command leaves nothing written). A file that cannot be removed
    is named in it."""
    left = []
    for path, fh in opened:
        try:
            fh.close()
        except OSError:
            pass                     # a flush that fails again on close: the file is removed below all the same
        try:
            os.remove(path)
        except OSError as e:
            left.append(f"{path} ({e})")
    if left:
        return B58HError(f"{why}; a file this call opened could not be removed: {'; '.join(left)}")
    if opened:
        return B58HError(f"{why}; nothing is written (this call's files removed: {', '.join(p for p, _ in opened)})")
    return B58HError(f"{why}; nothing is written")


def _write_all(outputs):
    """Write-once for one command's outputs together, in the order given (C1, C2): every text is encoded, every
    folder made and every file opened "x" before any is written, so an output that cannot be created is refused and
    leaves none written. A write that fails (a full disk, say) is refused the same way: every file this call opened,
    one already written in full among them, is closed and removed, so a refusal never leaves a document behind to
    block the rerun. Refuses with B58HError."""
    data = [(path, text.encode("utf-8")) for path, text in outputs]
    for path, _ in data:
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        except OSError as e:
            raise B58HError(f"{path}: its folder cannot be made ({e}); nothing is written")
    opened = []
    for path, _ in data:
        try:
            fh = open(path, "xb")
        except FileExistsError:
            raise _abandon(opened, f"{path} exists: a document of this study, once written, is kept (PR-B:1159-1160)")
        except OSError as e:
            raise _abandon(opened, f"{path}: cannot be created ({e})")
        opened.append((path, fh))
    done = 0
    try:
        for (path, fh), (_, raw) in zip(opened, data):
            with fh:
                fh.write(raw)
            done += 1
    except OSError as e:
        raise _abandon(opened, f"{opened[done][0]}: the write failed ({e})")


def _write_once(path, text):
    _write_all([(path, text)])


def _dump(obj):
    return json.dumps(FEA._jsonable(obj), indent=1, sort_keys=True, allow_nan=False) + "\n"


def context(scores, out, *, root=HERE):
    """PR-B 6.8's context command: refuses, assembles, checks with validate_context and writes once. Returns
    the printed lines."""
    _refuse_existing(out)
    require_committed(CONTEXT_RECORDS + (os.path.abspath(scores),), root=root)      # PR-B:633-634; C4
    sc = load_scores(scores, root=root)
    records = read_records(root, check=False)
    ctx, bd = assemble_context(sc, records, root=root)
    text = _dump(ctx)
    _write_once(out, text)
    lines = [f"context {shown(out, root)} written once: sha_text {TC.sha_text(out)}",
             f"  for the scores {shown(scores, root)}, sha_text {sc['sha_text']}; the reading of 'at b' "
             f"{AT_B_PRIMARY!r}",
             f"  status {ctx['status'][ENGINE]} (row 103 (4)'s rule: {FEA.pilot_factor():.4f} x s_p "
             f"{ctx['status_basis']['s_p']:g} against s* {ctx['status_basis']['s_star'][ENGINE]:g})"]
    for r in FEA.RATIOS:
        mb = ctx["model_band"][ENGINE][r]
        lines.append(f"  r = {r}: model band {mb['no_knock']:.4f} [{mb['with_knock']:.4f}], ceiling "
                     f"{ctx['ceiling'][ENGINE][r]:.4f}")
    return "\n".join(lines)


# ------------------------------------------------------------------------------------------ analyse: checks
def _same(a, b, where, diffs):
    """Collect every difference of two JSON values, floats to TOL relative and absolute (C5)."""
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b)):
            if k not in a or k not in b:
                diffs.append(f"{where}.{k}: present in one only")
            else:
                _same(a[k], b[k], f"{where}.{k}", diffs)
    elif isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        if len(a) != len(b):
            diffs.append(f"{where}: lengths {len(a)} and {len(b)}")
        else:
            for i, (x, y) in enumerate(zip(a, b)):
                _same(x, y, f"{where}[{i}]", diffs)
    elif (isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool)
          and not isinstance(b, bool) and (isinstance(a, float) or isinstance(b, float))):
        if not math.isclose(a, b, rel_tol=TOL, abs_tol=TOL):
            diffs.append(f"{where}: {a!r} recorded, {b!r} recomputed")
    elif a != b or type(a) is not type(b):
        diffs.append(f"{where}: {a!r} recorded, {b!r} recomputed")
    return diffs


def check_binding(ctx, sc):
    """analyse's first refusals (PR-B:636-637; G9): a context for other scores, by sha_text, or for another
    reading of "at b", by its recorded label."""
    if not isinstance(ctx, dict) or not isinstance(ctx.get("provenance"), dict):
        raise B58HError("the context has no provenance: it was not made by this file's context command")
    prov = ctx["provenance"]
    bound = prov["scores"].get("sha_text") if isinstance(prov.get("scores"), dict) else None
    if bound != sc["sha_text"]:
        raise B58HError(f"the context was made for other scores: its sha_text {str(bound)[:7]}, the scores' "
                        f"{sc['sha_text'][:7]} (thresholds.common.sha_text, CRLF read as LF)")
    if prov.get("at_b") != AT_B_PRIMARY:
        raise B58HError(f"the context was made for another reading of 'at b': {prov.get('at_b')!r}, the primary "
                        f"is {AT_B_PRIMARY!r} (PR-B 6.5)")


def check_rebuilt(ctx, rebuilt):
    """analyse's band refusal (PR-B:636; G9) and C5's: the context must be the one the scores and the
    committed records give, its band to TOL."""
    prov = ctx["provenance"]
    diffs = _same(ctx.get("model_band"), rebuilt["model_band"], "model_band", [])
    if diffs:
        raise B58HError("the context's model_band is not the band recomputed from these scores and the committed "
                        "records: " + "; ".join(diffs[:6]))
    for key in ("schema", "engines_in_test", "seeds_per_arm", "ceiling", "status", "status_basis"):
        _same(ctx.get(key), rebuilt[key], key, diffs)
    for key in ("records", "inputs", "s_p_label", "band"):
        _same(prov.get(key), rebuilt["provenance"][key], f"provenance.{key}", diffs)
    if diffs:
        raise B58HError("the context is not the one these scores and the committed records give: "
                        + "; ".join(diffs[:6]))


def fea_runs(scores_doc, ctx, bd, sources):
    """four_engine_analysis.analyse once per reading of the band: the context as written (PRIMARY) and the
    same context with each other reading's model_band (PR-B 6.5-6.6)."""
    out = {}
    for name in RUNS:
        cx = copy.deepcopy(ctx)
        if name != "primary":
            cx["model_band"] = copy.deepcopy(bd["model_band"][name])
        try:
            out[name] = FEA.analyse(scores_doc, cx, dict(sources, b58h_run=name))
        except FEA.AnalysisError as e:
            raise B58HError(f"four_engine_analysis refuses the {name} run: {e}")
    return out


def check_verdicts_fixed(results):
    """PR-B:584-585: a d > 0 verdict that moves with the band is refused as a defect."""
    base = FEA.verdicts(results["primary"])
    moved = []
    for name, res in results.items():
        got = FEA.verdicts(res)
        for k in sorted(set(base) | set(got)):
            if base.get(k) != got.get(k):
                moved.append(f"{k}: {base.get(k)} under the primary band, {got.get(k)} under {name}")
    if moved:
        raise DefectError("a d > 0 verdict moves with the band (PR-B 6.5: the band only flags): " + "; ".join(moved))


def flags(results):
    """{verdict: {run: {d_gt_0, model_limited, at_minus_band, at_plus_band}}}, FEA.verdicts' keys."""
    out = {}
    for name, res in results.items():
        for rd in FEA.READINGS:
            for n, row in res["readings"][rd]["d"].items():
                for test in ("t", "sign"):
                    key = f"{rd} d>0 ({test}) {n}"
                    out.setdefault(key, {})[name] = {k: bool(row[test][k]) for k in
                                                     ("d_gt_0", "model_limited", "at_minus_band", "at_plus_band")}
    return out


def companion_named(fl):
    """G1: the verdicts whose MODEL-LIMITED flag depends on the assumed b, by name."""
    out = []
    for key, runs in fl.items():
        p, lo, hi = (runs[n]["model_limited"] for n in ("primary", "companion_min", "companion_max"))
        if p != lo or p != hi or lo != hi:
            out.append(key)
    return out


# ------------------------------------------------------------------------------------------ intervals, Delta
def intervals(primary):
    """PR-B 6.3: per ratio, reading and form, from four_engine_analysis's own per-seed d."""
    out = {}
    for r in FEA.RATIOS:
        out[r] = {}
        for rd in FEA.READINGS:
            row = primary["readings"][rd]["d"][FEA.node(ENGINE, r)]
            out[r][rd] = {"evaluate_form": t_interval(row["d_per_seed"]),
                          "mean_form": t_interval(row["d_mean_form_per_seed"])}
    return out


def delta(checked, records):
    """PR-B 6.4: Delta per seed in both forms and both readings, its interval, sign count and two-sided sign
    test, and roads.json's prediction (G2, G3)."""
    eng = checked["engines"][ENGINE]
    hi, lo = FEA.arm_name(RATIO_HI), FEA.arm_name(RATIO_LO)
    arms, seeds = eng["arms"], eng["seeds"]
    out = {"readings": {}, "statements": list(DELTA_STATEMENTS)}
    for rd in FEA.READINGS:
        forms = {"evaluate_form": [FEA.cut(arms[hi][s][rd]["D"], arms[hi][s][rd]["D_base"])
                                   - FEA.cut(arms[lo][s][rd]["D"], arms[lo][s][rd]["D_base"]) for s in seeds],
                 "mean_form": [FEA.road_mean_points(arms[hi][s][rd]["D"], arms[hi][s][rd]["D_base"])
                               - FEA.road_mean_points(arms[lo][s][rd]["D"], arms[lo][s][rd]["D_base"])
                               for s in seeds]}
        out["readings"][rd] = {}
        for form, x in forms.items():
            iv = t_interval(x)
            out["readings"][rd][form] = {
                "per_seed": {str(s): v for s, v in zip(seeds, x)}, "interval": iv, "sign": sign_counts(x),
                "sign_p_two_sided": sign_two_sided(x), "covers_0": bool(iv["lo"] <= 0.0 <= iv["hi"]),
                "role": "Delta, exploratory" if form == "evaluate_form" else "beside, deciding nothing"}
    cu = records["c_u"]
    out["prediction"] = {rd: {"evaluate_form": cu[RATIO_HI][rd]["evaluate_form"] - cu[RATIO_LO][rd]["evaluate_form"],
                              "mean_form": cu[RATIO_HI][rd]["mean"] - cu[RATIO_LO][rd]["mean"]}
                         for rd in FEA.READINGS}
    out["prediction_where"] = (f"{ROADS} ceilings.per_engine.{ENGINE}.by[r].C_u.<reading>.<evaluate_form|mean>, "
                               f"C_u({RATIO_HI}) - C_u({RATIO_LO})")
    return out


# ------------------------------------------------------------------------------------------ 9.1
def _check_per(per, where, n_roads):
    if not isinstance(per, dict) or set(per) != set(PER_KEYS):
        got = sorted(per) if isinstance(per, dict) else type(per).__name__
        raise B58HError(f"{where}: keys {got}, exactly {list(PER_KEYS)} are required")
    for key in PER_KEYS:
        if not isinstance(per[key], list) or len(per[key]) != n_roads:
            n = len(per[key]) if isinstance(per[key], list) else type(per[key]).__name__
            raise B58HError(f"{where}.{key}: {n_roads} roads required, found {n}")
    for k in range(n_roads):
        _number(per["fuel"][k], f"{where}.fuel[{k}]")
        dm, sh, share = per["demand_steps"][k], per["short_steps"][k], per["short_share"][k]
        for name, v in (("demand_steps", dm), ("short_steps", sh)):
            if isinstance(v, bool) or not isinstance(v, int) or v < 0:
                raise B58HError(f"{where}.{name}[{k}]: an integer at least 0 is required, found {v!r}")
        if sh > dm:
            raise B58HError(f"{where}: road {k} has {sh} short steps among {dm} demand steps")
        if dm == 0:
            if share is not None:
                raise B58HError(f"{where}.short_share[{k}]: {share!r} on a road with no demand step, null required")
        else:
            _number(share, f"{where}.short_share[{k}]")
            if abs(share - sh / dm) > TOL:
                raise B58HError(f"{where}.short_share[{k}]: {share!r}, but short / demand is {sh}/{dm}")


def validate_delivery(block, checked, n_roads):
    """The scores' provenance.delivery against evaluate.delivery_block's form (C10). Raises B58HError."""
    if not isinstance(block, dict):
        raise B58HError(f"provenance.delivery: {type(block).__name__}, an object is required")
    if set(block) != {"rule", "hand", "arms"}:
        raise B58HError(f"provenance.delivery: keys {sorted(block)}, exactly ['arms', 'hand', 'rule'] are required")
    if not isinstance(block["rule"], dict):
        raise B58HError("provenance.delivery.rule: an object is required")
    hand, arms = block["hand"], block["arms"]
    if not isinstance(hand, dict) or BASELINE not in hand or CURRENT_GRADE not in hand:
        raise B58HError(f"provenance.delivery.hand: {sorted(hand) if isinstance(hand, dict) else hand!r}, the "
                        f"{BASELINE!r} and {CURRENT_GRADE!r} entries are required")
    eng = checked["engines"][ENGINE]
    want_arms = sorted(eng["arms"])
    if not isinstance(arms, dict) or sorted(arms) != want_arms:
        raise B58HError(f"provenance.delivery.arms: {sorted(arms) if isinstance(arms, dict) else arms!r}, the "
                        f"scores' arms are {want_arms}")
    want_seeds = sorted(str(s) for s in eng["seeds"])
    for arm in want_arms:
        if not isinstance(arms[arm], dict) or sorted(arms[arm]) != want_seeds:
            raise B58HError(f"provenance.delivery.arms.{arm}: its seeds are not the scores' "
                            f"(0-{max(eng['seeds'])})")
    for name, per in hand.items():
        _check_per(per, f"provenance.delivery.hand.{name}", n_roads)
    for arm in want_arms:
        for s in want_seeds:
            _check_per(arms[arm][s], f"provenance.delivery.arms.{arm}.{s}", n_roads)
    for k, f in enumerate(hand[BASELINE]["fuel"]):
        if not f > 0:
            raise B58HError(f"provenance.delivery.hand.{BASELINE}.fuel[{k}]: {f!r}; the fuel figure divides by it")


def per_figures(per, base_fuel):
    """One policy's or agent's 9.1 figures (PR-B:756-759; C11)."""
    fuel = float(np.mean([100.0 * (f / b - 1.0) for f, b in zip(per["fuel"], base_fuel)]))
    demand_roads = [k for k, dm in enumerate(per["demand_steps"]) if dm > 0]
    shares = {k: float(per["short_share"][k]) for k in demand_roads}
    worst = max(shares.values()) if shares else None
    dm, sh = sum(per["demand_steps"]), sum(per["short_steps"])
    return {"fuel_figure": fuel, "mean_short_share": float(np.mean(list(shares.values()))) if shares else None,
            "roads_with_demand": len(demand_roads), "worst_share": worst,
            "worst_roads": [k for k in demand_roads if shares[k] == worst] if shares else [],
            "pooled_short_share": sh / dm if dm else None, "short_steps": sh, "demand_steps": dm}


def _stats(xs):
    return {"median": float(np.median(xs)), "mean": float(np.mean(xs)), "min": float(min(xs)),
            "max": float(max(xs)), "n": len(xs)}


def delivery(sc):
    """Section 9.1, or {"refused": "REFUSED: <reason>"} with nothing else of it (PR-B:761-762)."""
    checked = sc["checked"]
    block = sc["doc"]["provenance"].get("delivery")
    try:
        validate_delivery(block, checked, sc["doc"]["n_roads"])
    except B58HError as e:
        return {"refused": f"REFUSED: {e}", "label": NO_READING}
    base = block["hand"][BASELINE]["fuel"]
    seeds = [str(s) for s in checked["engines"][ENGINE]["seeds"]]
    out = {"label": NO_READING, "rule": block["rule"], "arms": {},
           "beside": {name: per_figures(block["hand"][name], base) for name in (BASELINE, CURRENT_GRADE)}}
    for arm in ARMS:
        figs = {s: per_figures(block["arms"][arm][s], base) for s in seeds}
        with_demand = [s for s in seeds if figs[s]["roads_with_demand"]]
        all_pairs = [(int(s), k, float(block["arms"][arm][s]["short_share"][k])) for s in seeds
                     for k in range(len(base)) if block["arms"][arm][s]["demand_steps"][k] > 0]
        top = max(v for _, _, v in all_pairs) if all_pairs else None
        out["arms"][arm] = {
            "per_seed": figs,
            "fuel_figure": _stats([figs[s]["fuel_figure"] for s in seeds]),
            "mean_short_share": (_stats([figs[s]["mean_short_share"] for s in with_demand]) if with_demand else None),
            "no_demand_seeds": [s for s in seeds if not figs[s]["roads_with_demand"]],
            "worst": {"share": top, "at": sorted([s, k] for s, k, v in all_pairs if v == top)}}
    return out


# ------------------------------------------------------------------------------------------ section 10
def beside_10(root, ctx, primary):
    """PR-B 10's beside values (G5; C12): each read value with its file and line, or "not read: <reason>"."""
    out = {"status": {"primary": f"the analysis's {primary['status'][ENGINE]}",
                      "beside": f"the context's recorded rule output, {ctx['status'][ENGINE]}"},
           "s_p": {"value": ctx["status_basis"]["s_p"], "pairs": ctx["status_basis"]["pilot_pairs"],
                   "where": (ctx["provenance"].get("inputs") or {}).get("s_p_line"),
                   "label": ctx["provenance"].get("s_p_label")},
           "practice": PRACTICE_SENTENCE}
    try:
        require_committed([REVERIFY], root=root)
        plants = _walk(_json(root, REVERIFY), ("plants", ENGINE), REVERIFY)
        out["plant_sha"] = {k: {"value": _walk(plants, (k,), REVERIFY),
                                "where": f"{REVERIFY} plants.{ENGINE}.{k}"}
                            for k in ("plant_sha_now", "plant_sha_at_draw")}
    except B58HError as e:
        out["plant_sha"] = {"not_read": f"not read: {e}"}
    spreads, committed = {}, {}
    for rel, line in [(X2_RESULT, X2_KNOCK_LINE)] + [(X1_RESULT, x) for x in X1_LINES]:
        try:
            if rel not in committed:
                try:
                    require_committed([rel], root=root)
                    committed[rel] = None
                except B58HError as e:
                    committed[rel] = e
            if committed[rel] is not None:
                raise committed[rel]
            spreads[f"{rel}:{line}"] = read_sd_line(root, rel, line)
        except B58HError as e:
            spreads[f"{rel}:{line}"] = {"not_read": f"not read: {e}"}
    out["spreads"] = spreads
    return out


# ------------------------------------------------------------------------------------------ section 7
def _pt(v):
    return "-" if v is None else f"{v:+.2f}"


def _iv(iv):
    return f"{iv['lo']:+.2f} to {iv['hi']:+.2f}"


def _yn(b):
    return "yes" if b else "no"


def _ml(row_t, other_t):
    """G8's flag: (the words inside the sentence, the words after a verdict): the primary's, or the other
    reading's alone."""
    if row_t["model_limited"]:
        return ML_PRIMARY, ML_FLAG
    if other_t["model_limited"]:
        return ML_OTHER, ML_OTHER
    return "", ""


def _sign_words(s, other_s):
    """The sign test's verdict in its own words (PR-B:695), with its flag (G8): MODEL-LIMITED when the primary
    band moves it, else MODEL-LIMITED under the other reading of 'at b' when that reading alone does."""
    words = "shows d > 0" if s["d_gt_0"] else "does not show d > 0"
    flag = ML_FLAG if s["model_limited"] else (ML_OTHER if other_s["model_limited"] else "")
    return (f"{s['positive']} of {s['nonzero']} differences above 0 ({s['zero']} zero, dropped), one-sided p "
            f"{FEA._p(s['p'])}, graph p {FEA._p(s['adjusted_p'])}: it {words} under its own graph{flag}")


def sentences(results, ivs, fl, bd, ceiling_knock):
    """Section 7's sentences per ratio, r = 1.5 first (C8), from the PRIMARY run (G4, G7, G8, G1); ceiling_knock is
    read_records' by[r].a.knock.mean per ratio, the ceiling's with-knock reading for the bracket (G11)."""
    P, O = results["primary"], results["other_at_b"]
    mei = f"{P['constants']['MEI']:g}"
    hi_rejects = P["readings"]["no_knock"]["d"][FEA.node(ENGINE, RATIO_HI)]["t"]["d_gt_0"]
    named = set(companion_named(fl))
    comp = bd["companions"]
    out = {}
    for r in (RATIO_HI, RATIO_LO):
        n = FEA.node(ENGINE, r)
        row, krow = P["readings"]["no_knock"]["d"][n], P["readings"]["with_knock"]["d"][n]
        t, s, kt, ks = row["t"], row["sign"], krow["t"], krow["sign"]
        orow, okrow = O["readings"]["no_knock"]["d"][n], O["readings"]["with_knock"]["d"][n]
        ot, okt = orow["t"], okrow["t"]
        iv, ivm, ivk = ivs[r]["no_knock"]["evaluate_form"], ivs[r]["no_knock"]["mean_form"], \
            ivs[r]["with_knock"]["evaluate_form"]
        ivkm = ivs[r]["with_knock"]["mean_form"]
        flag, head_flag = _ml(t, ot)
        fill = {"r": r, "p": FEA._p(t["adjusted_p"]), "d": _pt(t["mean"]), "lo": f"{iv['lo']:+.2f}",
                "hi": f"{iv['hi']:+.2f}", "mei": mei, "n": row["n"], "flag": flag}
        if t["d_gt_0"]:
            head = "d > 0" + head_flag
            text = [D_GT_0.format(**fill)]
        else:
            head = "d > 0 not shown" + head_flag
            if r == RATIO_LO and not hi_rejects:
                head = (f"d > 0 not shown at r = {r}{head_flag} (the r = {RATIO_HI} test did not reject, so the "
                        f"graph gives this test no alpha; its unadjusted p {FEA._p(t['p'])})")
            text = [NOT_SHOWN.format(**fill)]
        if iv["hi"] < 0.0:
            text.append(BELOW_ZERO.format(**fill))
        other_band = bd["tables"]["other_at_b"][r]["no_knock"]["delta_e"]
        text.append(f"beside it: the mean form {_pt(row['d_mean_form'])} points (95 % {_iv(ivm)}"
                    f"{'; wholly below 0' if ivm['hi'] < 0 else ''}; decides nothing); the band Delta_e "
                    f"{row['band']:.2f} points under the primary reading of 'at b' ({other_band:.2f} under the "
                    f"other, 0 under version 5's); the ceiling C({r}) {row['ceiling']:.2f} points (roads.json, the "
                    f"mean form); the MEI {mei} points")
        kflag = _ml(kt, okt)[1]
        k_other_band = bd["tables"]["other_at_b"][r]["with_knock"]["delta_e"]
        text.append(f"[with knock, {FEA.WITH_KNOCK_LABEL}: d {_pt(kt['mean'])} points, 95 % {_iv(ivk)}"
                    f"{'; wholly below 0' if ivk['hi'] < 0 else ''}, adjusted p {FEA._p(kt['adjusted_p'])}: "
                    f"{'d > 0' if kt['d_gt_0'] else 'd > 0 not shown'}{kflag}; its mean form "
                    f"{_pt(krow['d_mean_form'])} points (95 % {_iv(ivkm)}{'; wholly below 0' if ivkm['hi'] < 0 else ''}"
                    f"; decides nothing); its band Delta_e {krow['band']:.2f} points under the primary reading of "
                    f"'at b' ({k_other_band:.2f} under the other, 0 under version 5's); the ceiling's with-knock "
                    f"reading {ceiling_knock[r]:.2f} points (roads.json a.knock.mean, beside C, the no-knock "
                    "reading's); the MEI as above]")
        text.append(f"the sign test, the declared secondary, in its own words: {_sign_words(s, orow['sign'])}"
                    + ("; it and the t-test disagree: both are reported, and the t-test's verdict stands"
                       if s["d_gt_0"] != t["d_gt_0"] else "")
                    + f" [with knock, {FEA.WITH_KNOCK_LABEL}: {_sign_words(ks, okrow['sign'])}]")
        mine = [k for k in fl if k.endswith(f" {n}") and k in named]
        for k in mine:
            runs = fl[k]
            text.append(f"companion, printed by name (PR-B 6.6): '{k}' MODEL-LIMITED: under kappa 1 "
                        f"{_yn(runs['primary']['model_limited'])}; under {comp['companion_min']['engine']}'s kappa "
                        f"{comp['companion_min']['kappa']:.4f} {_yn(runs['companion_min']['model_limited'])}; under "
                        f"{comp['companion_max']['engine']}'s kappa {comp['companion_max']['kappa']:.4f} "
                        f"{_yn(runs['companion_max']['model_limited'])}")
        if not mine:
            text.append(f"companion (P3 at kappa_L1 x b): no verdict at r = {r} has a MODEL-LIMITED flag that depends "
                        "on the assumed b")
        out[r] = {"verdict": head, "text": text}
    return out


# ------------------------------------------------------------------------------------------ the report
def _block_sentences(sent):
    L = ["SECTION 7: THE VERDICTS (PR-B 7), the no-knock t-test under the graph (primary), the r = 1.5 test first; "
         "each with its d, its two-sided 95 % interval, its mean form, its band and the ceiling, the MEI for scale, "
         "the with-knock reading in brackets; exploratory for every number"]
    for r in (RATIO_HI, RATIO_LO):
        L.append(f"  r = {r}: {sent[r]['verdict']}")
        L += [f"    {x}" for x in sent[r]["text"]]
    return L


def _block_intervals(ivs):
    t = ivs[RATIO_LO]["no_knock"]["evaluate_form"]
    L = [f"INTERVALS (PR-B 6.3): each d's two-sided 95 % t interval, mean +- t x sd / sqrt(n), sd at ddof 1, "
         f"t_0.975,{t['n'] - 1} = {t['t']:.4f} (scipy.stats.t); not adjusted for the graph"]
    for r in FEA.RATIOS:
        for rd in FEA.READINGS:
            lab = "no knock" if rd == FEA.PRIMARY else f"with knock [{FEA.WITH_KNOCK_LABEL}]"
            for form, fl in (("evaluate_form", "evaluate.py's form"), ("mean_form", "the mean form (decides nothing)")):
                iv = ivs[r][rd][form]
                L.append(f"  r = {r}, {lab}, {fl}: d {_pt(iv['mean'])}  sd {iv['sd']:.2f}  n {iv['n']}  "
                         f"95 % {_iv(iv)}")
    return L


def _block_delta(dl):
    L = ["DELTA, THE ACROSS-H CONTRAST (PR-B 6.4), exploratory, deciding nothing: Delta(s) = cut(sighted r = "
         f"{RATIO_HI}, s) - cut(sighted r = {RATIO_LO}, s), paired by seed; no blind cut"]
    for rd in FEA.READINGS:
        lab = "no knock" if rd == FEA.PRIMARY else f"with knock [{FEA.WITH_KNOCK_LABEL}]"
        for form, fl in (("evaluate_form", "evaluate.py's form"),
                         ("mean_form", "the mean form, beside, deciding nothing")):
            x = dl["readings"][rd][form]
            iv, sg = x["interval"], x["sign"]
            words = ("covers 0" if x["covers_0"] else "excludes 0: the sighted cut differed between the two H on "
                     "these roads, in that direction, and nothing about the criterion")
            L.append(f"  {lab}, {fl}: mean {_pt(iv['mean'])}  sd {iv['sd']:.2f}  n {iv['n']}  95 % {_iv(iv)} "
                     f"({words}); exact two-sided sign test: {sg['positive']} positive, {sg['negative']} negative, "
                     f"{sg['zero']} zero, p {FEA._p(x['sign_p_two_sided'])}")
    pr = dl["prediction"]
    L.append(f"  the prediction beside both forms (row 147 (7); {dl['prediction_where']}), no knock: "
             f"{pr['no_knock']['evaluate_form']:+.4f} in evaluate.py's form, {pr['no_knock']['mean_form']:+.4f} in "
             "the mean form")
    L.append(f"  beside the with-knock Delta (roads.json C_u.knock; PR-B names the no-knock prediction, G3): "
             f"{pr['with_knock']['evaluate_form']:+.4f} in evaluate.py's form, {pr['with_knock']['mean_form']:+.4f} "
             "in the mean form")
    L += [f"  {s}" for s in dl["statements"]]
    return L


def _block_band(bd, fl):
    c = bd["companions"]
    L = [f"THE B58'S MODEL BAND Delta_e (PR-B 6.5, 6.6): b = MEI / {bd['N_SHARES']} = {bd['b']:.4f} points (MEI "
         f"{bd['MEI']:g}); kappa_E8 {bd['kappa_E8']:.4f} ({TIGHTENINGS} E8.b58_u_val_kappa.with_roads.kappa); the "
         f"companion's kappa_L1 {c['companion_min']['kappa']:.4f} ({c['companion_min']['engine']}, the smallest) "
         f"and {c['companion_max']['kappa']:.4f} ({c['companion_max']['engine']}, the largest) of "
         f"{SUMMARY} engines.<id>.kappa.L1"]
    L.append("  the parts: " + "; ".join(f"{k} {v}" for k, v in bd["labels"].items()))
    L += [f"  {name}: {lab}" for name, lab in bd["run_labels"].items()]
    for r in FEA.RATIOS:
        for rd in FEA.READINGS:
            pt = bd["points"][r][rd]
            lab = "no knock" if rd == FEA.PRIMARY else f"with knock [{FEA.WITH_KNOCK_LABEL}]"
            arms = ", ".join(f"{a} {100.0 * pt['median_cut'][a]:+.2f} % (phi {pt['phi_arm'][a]:.4f})"
                             for a in pt["median_cut"])
            L.append(f"  r = {r}, {lab}: d (t_greater's mean) {_pt(pt['d'])}; median cuts {arms}; phi "
                     f"{pt['phi']:.4f}")
            for name in RUNS:
                tb = bd["tables"][name][r][rd]
                if tb["parts"] is None:
                    L.append(f"    {name:<14} the band left out: Delta_e 0")
                    continue
                parts = "  ".join(f"{k} {v:.4f}" for k, v in tb["parts"].items())
                L.append(f"    {name:<14} {parts}  Delta_e {tb['delta_e']:.4f} (RSS)  linear sum "
                         f"{tb['linear_sum']:.4f}")
    L.append("FLAGS: each verdict under each band (four_engine_analysis's corners: d moved by -Delta_e and +Delta_e, "
             "the graph re-run); verdict / MODEL-LIMITED per run")
    for key, runs in fl.items():
        p = runs["primary"]
        L.append(f"  {key}: {'d > 0' if p['d_gt_0'] else 'd > 0 not shown'}; MODEL-LIMITED "
                 + ", ".join(f"{name} {_yn(runs[name]['model_limited'])}" for name in RUNS))
    L.append("  every d > 0 verdict is the same under every band (PR-B 6.5: a verdict that moves is refused as a "
             "defect); the band only flags")
    return L


def _block_delivery(dv):
    L = [f"SECTION 9.1: FUEL AND TORQUE DELIVERY (PR-B 9.1), {dv['label']}; descriptive, deciding nothing"]
    if "refused" in dv:
        L.append(f"  {dv['refused']}")
        return L
    L.append("  the rule (the scores' delivery block): "
             + "; ".join(f"{k}: {v}" for k, v in sorted(dv["rule"].items())))

    def fig(f, note=""):
        share = "-" if f["mean_short_share"] is None else f"{f['mean_short_share']:.4f}"
        pooled = "-" if f["pooled_short_share"] is None else f"{f['pooled_short_share']:.4f}"
        worst = ("no demand step" if not f["worst_roads"] else
                 f"road {', '.join(map(str, f['worst_roads']))} ({f['worst_share']:.4f})")
        return (f"fuel figure {f['fuel_figure']:+.4f} %{note}, mean short share {share} over "
                f"{f['roads_with_demand']} roads with a demand step, worst {worst}, pooled {pooled} "
                f"({f['short_steps']} of {f['demand_steps']} demand steps short)")

    for arm in ARMS:
        a = dv["arms"][arm]
        ff, ss = a["fuel_figure"], a["mean_short_share"]
        L.append(f"  {arm}: the fuel figure (mean over the roads of 100 x (fuel / the baseline ECU's on the road - 1), "
                 f"%): median {ff['median']:+.4f}, mean {ff['mean']:+.4f}, range {ff['min']:+.4f} to {ff['max']:+.4f} "
                 f"over {ff['n']} seeds")
        L.append("    the mean short share over the roads with a demand step: " + (
            "no seed has a demand step" if ss is None else
            f"median {ss['median']:.4f}, mean {ss['mean']:.4f}, range {ss['min']:.4f} to {ss['max']:.4f} over "
            f"{ss['n']} seeds"))
        L.append("    no demand step on any road: " + (", ".join(f"seed {s}" for s in a["no_demand_seeds"]) or "none"))
        w = a["worst"]
        L.append("    the worst road over every seed: " + ("no demand step" if w["share"] is None else
                                                          ", ".join(f"seed {s} road {k}" for s, k in w["at"])
                                                          + f" (short share {w['share']:.4f})"))
        for s, f in a["per_seed"].items():
            L.append(f"    seed {s}: {fig(f)}")
    for name, f in dv["beside"].items():
        L.append(f"  beside, {name}'s own: {fig(f, ' (0 by its definition)' if name == BASELINE else '')}")
    return L


def _block_10(b10):
    L = ["SECTION 10: THE BESIDE VALUES THE ANALYSIS COVERS (PR-B 10), each deciding nothing"]
    ps = b10["plant_sha"]
    if "not_read" in ps:
        L.append(f"  the B58's plant_sha: {ps['not_read']}")
    else:
        now, draw = ps["plant_sha_now"], ps["plant_sha_at_draw"]
        L.append(f"  the B58's plant_sha: P's {now['value']} ({now['where']}) | beside it {draw['value']}, the frozen "
                 f"plant's before P ({draw['where']})")
    L.append(f"  the status: {b10['status']['primary']} | beside it {b10['status']['beside']}")
    sp = b10["s_p"]
    L.append(f"  s_p: {sp['value']:g} over {sp['pairs']} pairs ({sp['where']}; {sp['label']}) | beside it:")
    for where, x in b10["spreads"].items():
        if "not_read" in x:
            L.append(f"    {where}: {x['not_read']}")
        else:
            L.append(f"    {x['value']:g} over {x['n']} pairs ({x['where']}, under {x['section']!r}), another "
                     "experiment's spread, never pooled with this study")
    L.append(f"    the training's own seeds 0-4 on the practice roads: {b10['practice']}")
    L.append("  printed in the blocks above: the damage reading (no knock | with knock, in brackets); the band "
             "(version 6's | version 5's); 'at b' (kappa 1 in the contract's form | b itself); P3's kappa (1 | the "
             "companion); the form (evaluate.py's | the mean form); the test (paired t | exact sign test)")
    return L


def phrase_hits(text):
    """Section 7's never-written phrases found in a text (C13)."""
    low = text.lower()
    return [p for p in FORBIDDEN if p in low]


# ------------------------------------------------------------------------------------------ analyse
def analyse(scores, context_path, out, report, *, root=HERE):
    """PR-B 6.8's analyse command: refuses, runs four_engine_analysis five times, computes AB's blocks and
    writes the analysis JSON and the report once each. Returns the report text."""
    _refuse_existing(out, report)
    sc = load_scores(scores, root=root)
    try:
        with open(context_path, "rb") as fh:
            craw = fh.read()
        ctx = json.loads(craw.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as e:
        raise B58HError(f"{context_path}: not a context document ({e})")
    ctx_sha_text = hashlib.sha256(craw.replace(b"\r\n", b"\n")).hexdigest()
    check_binding(ctx, sc)
    records = read_records(root)
    rebuilt, bd = assemble_context(sc, records, root=root)
    check_rebuilt(ctx, rebuilt)
    sources = {"scores": {"path": shown(scores, root), "sha_text": sc["sha_text"]},
               "context": {"path": shown(context_path, root), "sha_text": ctx_sha_text}}
    results = fea_runs(sc["doc"], ctx, bd, sources)
    check_verdicts_fixed(results)
    fl = flags(results)
    ivs = intervals(results["primary"])
    dl = delta(sc["checked"], records)
    dv = delivery(sc)
    b10 = beside_10(root, ctx, results["primary"])
    sent = sentences(results, ivs, fl, bd, records["ceiling_knock"])
    fea_text = FEA.report(results["primary"])
    head = ["B58 PREVIEW STUDY: THE ANALYSIS (b58h_analysis.py analyse; PR-B sections 6, 7, 9.1 and 10); exploratory "
            "for every number",
            f"scores  {shown(scores, root)}: sha_text {sc['sha_text']} (raw sha256 {sc['sha256']}, a record that "
            "binds nothing)",
            f"context {shown(context_path, root)}: sha_text {ctx_sha_text}, made for these scores and the reading "
            f"of 'at b' {AT_B_PRIMARY!r}",
            f"records committed at HEAD {rebuilt['provenance']['git_head']}: " + ", ".join(CONTEXT_RECORDS)]
    blocks = (_block_sentences(sent) + [""] + _block_intervals(ivs) + [""] + _block_delta(dl) + [""]
              + _block_band(bd, fl) + [""] + _block_delivery(dv) + [""] + _block_10(b10))
    own = "\n".join(head + [NOTE] + blocks)
    hits = phrase_hits(own) + phrase_hits(json.dumps(sent))
    if hits:
        raise DefectError(f"AB's own text holds section 7's never-written phrases {sorted(set(hits))} (PR-B:703-704)")
    text = "\n".join(head + [NOTE, "", fea_text, ""] + blocks)
    doc = {"schema": SCHEMA,
           "label": "the B58 preview study's analysis (PR-B 6, 7, 9.1, 10): exploratory for every number",
           "inputs": {"scores": {"path": shown(scores, root), "sha_text": sc["sha_text"], "sha256": sc["sha256"]},
                      "context": {"path": shown(context_path, root), "sha_text": ctx_sha_text,
                                  "sha256": hashlib.sha256(craw).hexdigest()},
                      "records": dict(records["sha_text"]), "git_head": rebuilt["provenance"]["git_head"]},
           "fea": results, "fea_runs": {name: {"label": bd["run_labels"][name], "model_band": bd["model_band"][name]}
                                        for name in RUNS},
           "verdicts_fixed_under_every_band": True, "flags": fl, "companion_named": companion_named(fl),
           "band": {k: bd[k] for k in ("b", "MEI", "N_SHARES", "kappa_E8", "kappa_L1", "companions", "points",
                                       "tables", "labels", "run_labels")},
           "intervals": ivs, "delta": dl, "delivery": dv, "section_10": b10, "sentences": sent,
           "ceiling_with_knock": {"by_ratio": dict(records["ceiling_knock"]),
                                  "where": f"{ROADS} ceilings.per_engine.{ENGINE}.by[r].a.knock.mean",
                                  "label": "beside C, the no-knock reading's and the context's; decides nothing (G11)"}}
    _write_all([(out, _dump(doc)), (report, text + "\n")])
    return text


# ------------------------------------------------------------------------------------------ CLI
def main(argv=None, *, root=HERE):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="command", required=True)
    c = sub.add_parser("context", help="assemble the context four_engine_analysis.validate_context needs (PR-B 6.7)")
    c.add_argument("--scores", required=True, help="the study's scores document, committed at HEAD")
    c.add_argument("--out", required=True, help="the context, written once")
    a = sub.add_parser("analyse", help="the analysis: four_engine_analysis five times, and AB's blocks (PR-B 6, 9.1)")
    a.add_argument("--scores", required=True, help="the study's scores document")
    a.add_argument("--context", required=True, help="the context the context command wrote for these scores")
    a.add_argument("--out", required=True, help="the analysis JSON, written once")
    a.add_argument("--report", required=True, help="the text report, written once")
    args = ap.parse_args(argv)
    try:
        if args.command == "context":
            text = context(args.scores, args.out, root=root)
        else:
            text = analyse(args.scores, args.context, args.out, args.report, root=root)
    except DefectError as e:
        raise SystemExit(f"REFUSED (a defect of AB's code): {e}")
    except (B58HError, FEA.AnalysisError) as e:
        raise SystemExit(f"REFUSED: {e}")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
