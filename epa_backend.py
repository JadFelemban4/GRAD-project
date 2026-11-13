"""epa_backend.py -- row 114's schedule, applied once after B1: the engines in the four-engine test and n.

    python -B epa_backend.py compute
        The backend record as `write` would write it, printed; nothing is written.
    python -B epa_backend.py write
        ORDER step 19 (commit Tb): results/EPA_BACKEND.json, written once, then its trace printed (the
        engines in the test and n before each drop, each engine's seconds at n, W's slack) for Tb's message.
        Refused unless the record is absent from the tree and from HEAD's history, and `compute` would build it.
    python -B epa_backend.py check
        The committed record against a recomputation from the committed inputs: the differences, [] when
        there are none (Tb's gate after its commit, the interface sheet 10.2; PR-B's gate on its staged tree
        and again at T*, row 146 (6) and the sheet 17's 14).

    No other argument. n, the engines, the window, the rates, the device and the protocol are never passed,
    only read (row 114: "applied after Run 2 with no choice left"). Exit codes: 0 done, 2 refused (a check
    that finds a difference included).

WHERE IT SITS (the interface sheet, docs/build_step_2/INTERFACES.md, sections 0, 10 and 17). Commit Ta (ORDER
step 17b) is this module and test_epa_backend.py, after the plant commit P, Qa, Q, G and V (the sheet 17's 0; CU
is not made, since row 135 names the CPU) and before B1: Ta's pushed commit is B1's tree, and nothing is pushed
from the laptop after it until B1 is (row 146 (6)). Commit Tb (ORDER step 19) runs `write` from it after B1 and
commits the record. It is outside PLANT_CODE, epa_freeze.CODE_HASHED and the 35 files roads.json hashes, and no
hashed module imports it (row 121; test_epa_backend.Hygiene). It reads engines.py's reader of the records (P2;
the sheet 6.3: trainable_from, committed_record, VALIDATION_SUMMARY_REL, BACKEND_REL, BACKEND_SCHEMA) when a
function is called, never at import, and never retypes it (mistake 10). benchmark_training.py, the protocol
script, is read and never edited: it is frozen from C1b on (row 135 (2)), and its own schedule lines (ENGINES = 4
engines at one engine's rate, `_days`) are not this schedule, so this module takes only ARMS, PROD_STEPS,
SEEDS_TARGET, DT, PROD_BUFFER, DET_STEPS, PLANT_KEYS, RECIPE29_TIMED and `configurations` from it.

THE PROTOCOL (row 135). PROTOCOL is typed from row 135 and settable from neither the command line nor the
environment: the device and its torch build from step 3 on the training device (Jad's PC, 2 November 2026,
docs/build_step_2/STEP3_RUN_2026-11-02_JAD_PC.md: "CPU with 12 runs at once (torch 2.14.0+cpu)", the merge of
A5), python 3.13.2 (requirements-lock.txt's pin), N = 12 runs at once for every engine (the runs step 3's
recommendation picks on the B58, `pick_runs`; row 135 (2): one N, also the training's concurrency), S = 3000 steps
per run and R = 2 repeats (the script's defaults, which step 3 ran), the four-engine road at dt 1.0 with the
production buffer, the committed roads record with decision 29's share on and the reward without the knock
term, the timed recipe flags (benchmark_training.RECIPE29_TIMED, imported), the protocol commit (C1b's sha) and
the lock. The protocol commit is C1b, 008f69f (row 135 (2); pushed on GRA-test), and benchmark_training.py is
the same at every commit read here (protocol_commit_problems, and classify (b) for each attempt's git_head).
CPU_PROTOCOL is None: row 135 names the CPU, so there is no CUDA series and no fallback (row 135 (4)(c)). ARMS is
benchmark_training.ARMS, 3: row 135 (5) MEASURED the blinded arm bit for bit across H on the scratch H draft, so
row 114's three arms stand and there is no fourth (4 only after a failure on a draft that meets row 117's
construction, contract version 6 for the arm count only; the sheet 6.9).

THE RULE (rows 114 and 136; row 134 (1)). Each engine's rate is r_e = lower_min / N exactly (row 135 (3)):
lower_min is the (device, N) row of the attempt's recommendation.configurations, the lowest repeat of bounds()'
two-decimal lower rate, read from the JSON text through Decimal into a Fraction, so a boundary is never moved by
a float or by the two-decimal per-run print. A wave of N runs of PROD_STEPS = 450 000 steps takes
450 000 N / lower_min s; engine e takes ceil(ARMS n / N) waves; n is the largest n whose sum over the engines in
the test fits W = 864 000 s (row 134 (1): 10-20 November 2026, AST, the device training 24 h a day), searched up
from 1 and refused at SEED_LIMIT (1000: row 96's reserved episode seeds begin there). Every engine trains on the
exact cycle (row 136 (2): no table is built for any engine). While n < N_MIN = 20 (decision 30's target,
benchmark_training.SEEDS_TARGET; rule 0) and an EPA engine is in the test, the first engine of DROP_ORDER still
in it, the Honda, then the Mazda, then the Ford (row 136 (1), contract version 6 for the order of leaving),
leaves and is dropped, and n is recomputed. The B58 is never dropped (MD:1590-1591; epa_roads.NEVER_DROPPED).
So the Ford leaves only when it and the B58 together cannot reach n >= 20, and then no EPA engine survives: n is
null, the four-engine test does not run, and the failed schedule is reported as the result (row 136 (1);
MD:1611-1612). When Run 2 has already dropped every EPA engine, as it did (section Q: B1 times the B58 alone, and
in_test is ['b58']), n is null with no schedule drop, the four-engine test does not run, and the failed
validations are reported as the results (MD:1611-1612; the sheet 17's 10.2), not a failed schedule. n is never an
int below 20, and the B58 alone is never the four-engine test. Either null n is the four-engine test's, never the
B58 study's: that study's n = 20 is row 147 (4)'s, fixed, and read from no record ("The backend record's null n is
not this n"). validate_epa.DROP_ORDER (validate_epa.py:165-167, the text summary.json carries: the Ford first) is
contract version 5's, CODE_HASHED, and decides nothing here; the record's notes say so.

THE ATTEMPTS (row 135 (4); the sheet 10.1 and 12.8). B1 writes each engine's attempts as
results/benchmarks/B1_bench_<engine>.attempt<k>.json with its .txt (ATTEMPT), on CUDA also the CPU series
(CPU_ATTEMPT), and B0_<git_head>.json for each commit B1 ran from (B0_RECORD); the runbook's shell text is the
one definition of these names, and test_epa_backend.RunbookNames checks the three constants against it at the
protocol commit and in this tree. Every attempt of a series is read in k order, k = 1, 2, ... with none missing;
an attempt that left only its .txt is a crash. `classify` reads one attempt: (a) a crash (a status other than
'finished'; seed 0 not trained twice to the end, identical None; a row at N not ok only through exit codes, a
timeout, missing runs or an 'error:' line); (b) an operator fault, which is a crash (a dirty tree; the plan unlike
the protocol's, key for key; the device, the torch build or the python unlike it; the commit's
benchmark_training.py unlike the protocol commit's; no committed B0 record for its git_head, or a host,
benchmark_sha or train_sha unlike that record's, never compared with this laptop's hashes, which core.autocrlf
moves; machine.engines_trainable unlike the summary-only reading; runs on more than one plant, a
plant.reward_knock not False, a plant.backend not 'cycle', or a plant unlike this tree's own, PLANT_KEYS key for
key); (c) on CUDA a fallback (identical False, fits False at N, seed0_twice False); on the CPU (d) a defect
(identical False) and (e) a stop (fits False at N); otherwise the measurement, lower_min. In every series every
attempt but the last is a crash and the last is not. A defect refuses with row 135 (4)(c)'s text (DEFECT_TEXT),
and so does a stop (STOP_TEXT, with row 146 (4)'s reading of it: "the study's training stops, and it is
reported"); a fallback reads every engine's CPU series instead. An attempt whose git_head is not a commit here is
refused (fetch it). Any outcome row 135 (4) does not name (a row not ok for a reason the frozen script does not
print, a file the script did not write) is refused: the step stops and it is reported (rule 1.11 of the sheet).

THE COST FILES (the sheet 10.1; rows 135 (4)(c), 140 (5)). An attempt timed the code at its git_head. If any
cost file differs between that git_head and HEAD, the attempt is superseded: listed in inputs.superseded and not
read. The cost files are the union, at both commits, of the import closures (epa_roads.import_closure, every
depth, imports inside functions included) of train.py, train_all.py, benchmark_training.py and
check_training_device.py, then fingerprint.PLANT_CODE, every engine's spec files and derived and freeze files,
the lock and the roads record. epa_fit.py is among them (train.py imports four_engine_roads, which imports
epa_roads, which imports roads_ceiling, which imports epa_fit; row 146 (3)), so G lands before B1 (rule 1.5 of the
sheet; test_epa_backend.CostFiles). An engine left with no attempt to read refuses, naming row 140 (5): B1 is
repeated for every engine from the pushed tree, by the same protocol, every attempt kept.

THE RECORD (the sheet 12.5, its one definition): schema, rule, window, constants, protocol, drop_order, inputs
{trainable_before, summary, benchmarks, fallback, superseded, crashes, b0}, trace, engines (all four, in
engines.known() order: drop, backend 'cycle' or null, reason), in_test, n, seconds_at_n, total_s, slack_s, notes,
provenance. A Run-2 drop's reason is 'Run 2: results/EPA_VALIDATION/summary.json <sha_text> (row 107 (1))', a
schedule drop's 'rows 114 and 136: the schedule (n <before> -> <after>)' (schedule_reason). Before it is written,
engines.trainable_from(summary, record) must give back in_test: a refusal there is this module's defect, never
P's. It is written once through epa_roads.write_once (LF, ASCII, no NaN) and never edited.

THE WORK TREE (row 146 (6); the sheet 17's 14). compute, write and check read HEAD's files, some of them from the
work tree, so they refuse a work tree that changes any file that can move the record (record_moving_paths), each
named with why: any .py (an import closure, or the running code's own sha_text, can change), a file under
results/benchmarks (B1's attempts and B0 records), Run 2's summary, the backend record itself, and every other
cost file of HEAD (a spec, a derived or freeze file, the lock, the roads record), staged, modified, deleted or
untracked alike. Any other change moves nothing and is allowed, so that PR-B's gate runs `check` on its staged
tree (the preregistration, the session report and CHECKPOINT staged) as well as at T*.

THE PREREGISTRATIONS' COMMANDS (the sheet 10.1, 11 and 17's 10.1 and 11). The four-engine test's,
results/PREREGISTRATION_4E.md (PREREGISTRATION_REL), is never written once the record's n is null (row 136 (1)),
and Run 2 left no EPA engine: preregistration_problems is its check, kept for that reading. The B58 study across H
(rows 146-147) is preregistered in results/PREREGISTRATION_B58H.md (B58H_PREREGISTRATION_REL; PR-B, ORDER step
20, whose own commit is T*). Every train_all.py command PR-B states is one of B58H_LINES: row 147 (3)'s training
line (--seeds 0-19, --out runs/b58h_dt1, no --ratios) or its pilot line (--seeds 2000-2004 --ratios 1.5, --out
runs/b58h_pilot_dt1), each carrying b58h_flags(PROTOCOL) and the flags B58H_ALONE, never --blind-per-h, and each
stated in a fenced block (b58h_problems). A command is a simple command of a fenced line whose program is
train_all.py (after VAR=value words, an interpreter and its -B), or in which --engine follows train_all.py, and an
inline code span in which --engine follows it; a `| tee` or a redirection ends it, and any other naming of
train_all.py (`git diff ... -- train.py train_all.py`) is a mention (_train_all_args).
test_epa_backend.PreregistrationB58H runs each through train_all.main() in-process, stopped before any directory
or run exists (row 146 (5)); train_all.py is not edited for it.

WHAT IT NEVER DOES. It opens no EPA table, no held-out row and nothing under logs/; it reads the committed
summary.json through P's reader only. It imports no torch (it never imports train.py: live_plants is the only
caller of fingerprint.plant_fingerprint here, and only the command line calls it). It writes nothing but the
record, and `compute` and `check` write nothing in the repository (cost_files reads another commit's .py
files from `git archive` into a temporary folder outside it, removed after).
"""
import argparse
import datetime
import fnmatch
import io
import json
import os
import re
import shlex
import subprocess
import sys
import tarfile
import tempfile
from decimal import Decimal
from fractions import Fraction

import benchmark_training as B
import epa_roads as ER
import fingerprint as FP
from thresholds import common

REPO = os.path.dirname(os.path.abspath(__file__))
MODULE_REL = "epa_backend.py"
PROTOCOL_SCRIPT_REL = "benchmark_training.py"       # frozen from C1b on (row 135 (2); the sheet section 2)
RUNBOOK_REL = "docs/build_step_2/DEVICE_RUNBOOK.md"  # C1b alone edits it (the sheet section 2)
PREREGISTRATION_REL = "results/PREREGISTRATION_4E.md"   # the sheet section 11; never written with n null (row 136 (1))
PR_OUT = "runs/four_engine_dt1_{engine}"            # each engine's own --out (the sheet section 11: train.py:750, :753)

# ------------------------------------------------------------------ row 135: the benchmark protocol
PROTOCOL = {
    "device": "cpu",                      # step 3's merge on Jad's PC: "CPU with 12 runs at once" (row 135 (1))
    "torch": "2.14.0+cpu",                # its exact build, the lock's (requirements-lock.txt:5)
    "python": "3.13.2",                   # requirements-lock.txt:11, epa_freeze.lock_pins()['python']
    "runs": 12,                           # N, one value for every engine and the training's --jobs (row 135 (2))
    "steps_per_run": 3000,                # S, the script's default, as step 3 ran it
    "repeats": 2,                         # R, the script's REPEATS, as step 3 ran it
    "road": "four_engine",                # row 116's training road (row 130 (5))
    "dt": B.DT,                           # 1.0, the step every road is benchmarked at
    "buffer": B.PROD_BUFFER,              # 450 000: the allocation a production run makes
    "roads_record": ER.ROADS_REL,         # decision 29's share on, from the committed record (row 130 (5))
    "scored_share": True,
    "reward_knock": "out",                # the reward without the knock term (row 113 (5))
    "recipe_timed": B.RECIPE29_TIMED,     # train_all --recipe29's flags but --checkpoint-average (C1b)
    # C1b, "build step 2, C1b: the benchmark protocol" (row 135 (2)): benchmark_training.py frozen from it
    "protocol_commit": "008f69f5ff13834c89872c92b47a6e63c7784fe4",
    "lock": "requirements-lock.txt",      # epa_freeze.LOCK_FILE (test_epa_backend.Protocol pins it)
}
# Row 135 names the CPU: no CUDA series, so no CPU series beside it and no fallback (row 135 (4)(c))
CPU_PROTOCOL = None

# ------------------------------------------------------------------ row 134 (1), 91c6ece: the window
W_S = 864_000                             # 240 h of the device's wall-clock time
W_FIRST = "2026-11-10T00:00:00+03:00"
W_LAST = "2026-11-20T00:00:00+03:00"

# ------------------------------------------------------------------ rows 114 and 136: the rule
N_MIN = 20                                # decision 30's target; n is never set below it (rule 0)
SEED_LIMIT = 1000                         # n >= 1000 refused: row 96's reserved episode seeds start at 1000
# Row 136 (1): contract version 6 for the order of leaving. An engine that leaves the exact cycle is dropped,
# with no table (row 136 (2)), so the order of leaving and the order of dropping are one tuple
DROP_ORDER = ("honda_l15b7", "mazda_25t", "ford_27tt")
LEAVE_ORDER = DROP_ORDER
ARMS = B.ARMS                             # decision 27's three arms; row 135 (5): bit for bit across H, no fourth
PROD_STEPS = B.PROD_STEPS                 # 450 000 steps a run (decision 29)

# ------------------------------------------------------------------ B1's files (C1b's runbook; the sheet 12.8)
BENCH_REL = "results/benchmarks"
ATTEMPT = "B1_bench_{engine}.attempt{k}.json"
CPU_ATTEMPT = "B1_bench_{engine}.cpu.attempt{k}.json"
B0_RECORD = "B0_{git_head}.json"
# ------------------------------------------------------------------ rows 146 (5), 147 (3): PR-B's two commands
# The sheet 17's 10.1 and 11. PR-B, ORDER step 20: its own commit is T*, the commit the pilot and the training
# run from (git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md)
B58H_PREREGISTRATION_REL = "results/PREREGISTRATION_B58H.md"
B58H_ENGINE = ER.NEVER_DROPPED            # --engine b58: the study's one plant (row 147 (1))
B58H_N = 20                               # row 147 (4), Ghassan's answer Q3: fixed, never this record's n
B58H_LINES = {
    # row 147 (3)'s training command: three arms at every ratio the roads record holds, so no --ratios
    "training": {"--seeds": f"0-{B58H_N - 1}", "--out": "runs/b58h_dt1"},
    # the pilot, PL-B (row 146 (3), ORDER step 21): five pairs, blinded and sighted at r = 1.5 (row 112)
    "pilot": {"--seeds": "2000-2004", "--ratios": "1.5", "--out": "runs/b58h_pilot_dt1"},
}
B58H_ALONE = ("--third-arm", "--recipe29", "--no-resume")    # and never --blind-per-h (row 135 (5): three arms)
B58H_WITH_VALUE = ("--engine", "--device", "--road", "--dt", "--roads-record", "--reward-knock", "--steps",
                   "--jobs", "--seeds", "--ratios", "--out")
# The entry points whose import closures time a step (the sheet 10.1, cost_files)
COST_ENTRIES = ("train.py", "train_all.py", "benchmark_training.py", "check_training_device.py")
# The keys of a (device, N) configuration compared with benchmark_training.configurations recomputed from the
# rows (its medians are floats rounded in the file, so they are not among them)
CONF_KEYS = ("repeats", "repeats_planned", "ok", "fits", "fits_known", "steady", "loaded", "lower_min",
             "seed0_twice")

if N_MIN != B.SEEDS_TARGET:
    raise RuntimeError(f"epa_backend: N_MIN {N_MIN} is not benchmark_training.SEEDS_TARGET {B.SEEDS_TARGET}")
if sorted(DROP_ORDER) != sorted(common.EPA_ENGINES) or ER.NEVER_DROPPED in DROP_ORDER:
    raise RuntimeError(f"epa_backend: DROP_ORDER {DROP_ORDER} is not the EPA engines {common.EPA_ENGINES} "
                       f"without {ER.NEVER_DROPPED}")
if (datetime.datetime.fromisoformat(W_LAST) - datetime.datetime.fromisoformat(W_FIRST)).total_seconds() != W_S:
    raise RuntimeError(f"epa_backend: {W_FIRST} to {W_LAST} is not W_S = {W_S} s (row 134 (1))")


class Refused(Exception):
    """A precondition does not hold, or an outcome no row covers: nothing is written (exit 2)."""

    def __init__(self, problems):
        self.problems = list(problems)
        super().__init__("; ".join(self.problems))


# ================================================================== the arithmetic (pure, exact)
def _exact(x, what):
    """x as a Fraction: an int, a Decimal or a Fraction, never a float or a bool (row 135 (3): exact)."""
    if isinstance(x, bool) or not isinstance(x, (int, Decimal, Fraction)):
        raise TypeError(f"{what} must be exact (an int, a Decimal or a Fraction), not {x!r}")
    return Fraction(x)


def wave_seconds(lower_min, N):
    """One wave of N runs of PROD_STEPS steps at the per-run rate lower_min / N: PROD_STEPS N / lower_min s."""
    return Fraction(PROD_STEPS) * N / _exact(lower_min, "lower_min")


def engine_seconds(n, lower_min, N):
    """One engine's ARMS x n runs, N at a time: ceil(ARMS n / N) waves (a wave that is not full still takes a
    run's time, as benchmark_training.schedule counts them)."""
    return -(-ARMS * n // N) * wave_seconds(lower_min, N)


def total_seconds(n, rates):
    """The engines' seconds at n, summed over `rates` ({engine: (lower_min, N)}) only: train_all.py trains one
    engine per call, so the engines run one after another (row 114's sum)."""
    return sum((engine_seconds(n, *rates[e]) for e in rates), Fraction(0))


def n_max(rates, w_s):
    """The largest n >= 0 with total_seconds(n, rates) <= w_s (0 when one seed does not fit). The total never
    falls as n grows, so the first n that does not fit ends the search. Refused at SEED_LIMIT."""
    if not rates:
        raise Refused(["n_max: no engine is in the test"])
    n = 0
    while total_seconds(n + 1, rates) <= w_s:
        n += 1
        if n >= SEED_LIMIT:
            raise Refused([f"n reaches SEED_LIMIT = {SEED_LIMIT}: seeds 0..n-1 would meet row 96's reserved "
                           "episode seeds (1000-1019); no row caps n, so the case is reported"])
    return n


def schedule_reason(before, after):
    """A schedule drop's reason, the sheet 12.5's one definition: `after` is the n recomputed after the drop,
    None when no EPA engine is left (written 'null')."""
    return f"rows 114 and 136: the schedule (n {before} -> {'null' if after is None else after})"


def _trace_step(test, rates, n, event):
    return {"in_test": list(test), "n": n, "total_s": float(total_seconds(n, {e: rates[e] for e in test})),
            "total_s_at_n_min": float(total_seconds(N_MIN, {e: rates[e] for e in test})), "event": event}


def apply_rule(in_test, rates, *, w_s):
    """Rows 114 and 136 on the engines in the test (`in_test`, the B58 among them; Run 2's drops already out),
    each on the exact cycle at its rate (`rates`: {engine: (lower_min, N)}): {engines, in_test, n, trace}.

    n is n_max over them. While n < N_MIN and an EPA engine is in the test, the first engine of DROP_ORDER still in
    it is dropped, with schedule_reason, and n is recomputed (row 136 (1)-(2)). The B58 is never dropped. When no
    EPA engine is left, n is None whatever n_max gives the B58 alone: the four-engine test does not run (row 136
    (1); MD:1611-1612). `engines` holds an entry for each engine given; `trace` holds, before each drop, the
    engines in the test, n and the total at n (and at N_MIN), then the end."""
    test = list(in_test)
    if ER.NEVER_DROPPED not in test:
        raise Refused([f"apply_rule: {ER.NEVER_DROPPED} is not in the test {test}: it is never dropped "
                       "(MD:1590-1591)"])
    if sorted(rates) != sorted(test) or len(set(test)) != len(test):
        raise Refused([f"apply_rule: rates for {sorted(rates)}, engines in the test {test}"])
    unknown = [e for e in test if e != ER.NEVER_DROPPED and e not in DROP_ORDER]
    if unknown:
        raise Refused([f"apply_rule: {unknown} are neither the B58 nor in DROP_ORDER {DROP_ORDER}"])
    engines_out = {e: {"drop": False, "backend": FP.BACKEND_CYCLE, "reason": None} for e in test}
    trace = []

    def epa_left():
        return [e for e in test if e in DROP_ORDER]
    # n_max is never asked of the B58 alone: its n would decide nothing, and a fast device could reach SEED_LIMIT
    n = n_max({e: rates[e] for e in test}, w_s) if epa_left() else None
    while n is not None and n < N_MIN:
        leaving = next(e for e in DROP_ORDER if e in test)
        trace.append(_trace_step(test, rates, n, f"{leaving} leaves and is dropped (row 136 (1)-(2))"))
        test.remove(leaving)
        after = n_max({e: rates[e] for e in test}, w_s) if epa_left() else None
        engines_out[leaving] = {"drop": True, "backend": None, "reason": schedule_reason(n, after)}
        n = after
    if n is None:
        trace.append({"in_test": list(test), "n": None, "total_s": None, "total_s_at_n_min": None,
                      "event": "end: no EPA engine is left, so the four-engine test does not run (row 136 (1); "
                               "MD:1611-1612)"})
        return {"engines": engines_out, "in_test": test, "n": None, "trace": trace}
    trace.append(_trace_step(test, rates, n, "end"))
    return {"engines": engines_out, "in_test": test, "n": n, "trace": trace}


# ================================================================== git
def _git(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True, text=True, encoding="utf-8")


def _git_bytes(root, *args):
    return subprocess.run(["git", "-C", root, *args], capture_output=True)


def _git_out(root, *args):
    r = _git(root, *args)
    if r.returncode != 0:
        raise Refused([f"git {' '.join(args[:3])}{' ...' if len(args) > 3 else ''} in {root}: "
                       f"{r.stderr.strip() or 'exit ' + str(r.returncode)}"])
    return r.stdout


def _same(root, a, b, paths):
    """None when `paths` are the same at commits a and b, else the paths that differ ('unknown commit' when git
    cannot name a or b here: the laptop must fetch it)."""
    r = _git(root, "diff", "--quiet", a, b, "--", *paths)
    if r.returncode == 0:
        return None
    if r.returncode == 1:
        names = _git(root, "diff", "--name-only", a, b, "--", *paths).stdout.split()
        return names or ["(git diff --quiet exit 1)"]
    return [f"unknown commit ({r.stderr.strip()[:200]})"]


def head_files(root, rel_dir):
    """The files under `rel_dir` in HEAD's tree, repository-relative."""
    return _git_out(root, "ls-tree", "-r", "--name-only", "HEAD", "--", rel_dir).split("\n")


def protocol_commit_problems(root, protocol):
    """Why `protocol`'s protocol commit cannot be read in `root`'s HEAD, or []: 40 hex digits, a commit HEAD
    descends from, and benchmark_training.py at HEAD the same (frozen from C1b on, row 135 (2))."""
    c = protocol["protocol_commit"]
    if not isinstance(c, str) or not re.fullmatch(r"[0-9a-f]{40}", c):
        return [f"the protocol commit {c!r} is not 40 hex digits"]
    if _git(root, "cat-file", "-t", c).stdout.strip() != "commit":
        return [f"the protocol commit {c} is not a commit in {root}"]
    if _git(root, "merge-base", "--is-ancestor", c, "HEAD").returncode != 0:
        return [f"HEAD does not descend from the protocol commit {c}"]
    diff = _same(root, c, "HEAD", [PROTOCOL_SCRIPT_REL])
    return [] if diff is None else [f"{PROTOCOL_SCRIPT_REL} at HEAD is not the protocol commit's {c} (row 135 (2): "
                                    f"frozen from C1b on): {diff}"]


def protocol_script_problem(root, git_head, protocol):
    """None when benchmark_training.py at `git_head` is the protocol commit's (`git diff --quiet <C1b>
    <git_head> -- benchmark_training.py`), else why not: an operator fault in classify (b)."""
    if not git_head:
        return "the attempt names no git_head"
    diff = _same(root, protocol["protocol_commit"], git_head, [PROTOCOL_SCRIPT_REL])
    return None if diff is None else f"at {git_head} it differs from {protocol['protocol_commit'][:12]}'s ({diff})"


# ================================================================== the cost files
def _spec_meta(engine):
    import engines
    return engines.read_spec(engines.PLANTS[engine][0])["_meta"]


def _closures(tree):
    files = set()
    for m in COST_ENTRIES:
        if os.path.isfile(os.path.join(tree, m)):
            try:
                files.update(ER.import_closure(m, root=tree))
            except ER.Refused as e:
                raise Refused([f"the import closure of {m}: {p}" for p in e.args[0]]) from None
        else:
            files.add(m)
    return files


def cost_files(root, rev):
    """The files whose change makes an attempt's rate stale (the sheet 10.1): the import closures of COST_ENTRIES
    at `rev` ('HEAD' is read from the work tree, where compute refuses any changed .py, record_moving_paths;
    another commit's .py files are read from `git archive` into a temporary folder), FP.PLANT_CODE,
    engines.spec_files(e) for every engine, each engine's derived file and freeze record (its spec's own keys, as
    engines.calibrated reads them), the lock (and CPU_PROTOCOL's, if any) and the roads record. The module lists
    after the closures are HEAD's: a change to one changes engines.py or fingerprint.py, which are in the set."""
    import engines
    if rev == "HEAD":
        files = _closures(root)
    else:
        r = _git_bytes(root, "archive", "--format=tar", rev, "--", "*.py")
        if r.returncode != 0:
            raise Refused([f"git archive {rev}: {r.stderr.decode('utf-8', 'replace').strip()[:200]}"])
        with tempfile.TemporaryDirectory(prefix="epa_backend_rev_") as tmp:
            with tarfile.open(fileobj=io.BytesIO(r.stdout)) as tf:
                tf.extractall(tmp, filter="data")
            files = _closures(tmp)
    files.update(FP.PLANT_CODE)
    for e in engines.known():
        files.update(engines.spec_files(e))
        meta = _spec_meta(e)
        files.update(meta[k] for k in ("derived", "freeze") if k in meta)
    for p in (PROTOCOL, CPU_PROTOCOL):
        if p is not None:
            files.update((p["lock"], p["roads_record"]))
    return sorted(files)


def superseded_why(root, git_head, cache):
    """None when the cost files are the same at `git_head` and HEAD (the union of both commits' sets), else
    why the attempt is superseded. `cache` maps a revision to its cost files. Refused when `git_head` is not a
    commit in `root`, before cost_files would refuse it with git archive's words: the laptop fetches it (B1's
    commit is taken with git pull --ff-only, row 146 (6))."""
    if _git(root, "cat-file", "-t", f"{git_head}^{{commit}}").stdout.strip() != "commit":
        raise Refused([f"the attempt's git_head {git_head} is not a commit here: fetch it"])
    for rev in ("HEAD", git_head):
        if rev not in cache:
            cache[rev] = cost_files(root, rev)
    diff = _same(root, git_head, "HEAD", sorted(set(cache["HEAD"]) | set(cache[git_head])))
    if diff and diff[0].startswith("unknown commit"):
        raise Refused([f"git diff {git_head} HEAD failed in {root}: {diff[0]}"])
    return None if diff is None else ("its cost files differ from HEAD's (row 140 (5); row 135 (4)(c)): "
                                      + ", ".join(diff[:8]) + (" ..." if len(diff) > 8 else ""))


# ================================================================== reading the attempts
def _attempt_re(template, engine):
    pat = re.escape(template).replace(re.escape("{engine}"), re.escape(engine))
    return re.compile(pat.replace(re.escape("{k}"), "([1-9][0-9]*)"))


def _txt(name):
    return name[:-len(".json")] + ".txt"


def bench_attempts(root, engine, *, kind):
    """Every attempt of `engine`'s `kind` series ('device': ATTEMPT; 'cpu': CPU_ATTEMPT) committed at HEAD under
    BENCH_REL, in k order: [{k, json, txt}], each a repository-relative path or None (an attempt that crashed
    before it wrote its JSON left only its .txt). Refused when a k is missing: an attempt is never renamed or
    deleted (B5)."""
    template = {"device": ATTEMPT, "cpu": CPU_ATTEMPT}[kind]
    jre, tre = _attempt_re(template, engine), _attempt_re(_txt(template), engine)
    found = {}
    for path in head_files(root, BENCH_REL):
        name = path.rpartition("/")[2]
        for rx, slot in ((jre, "json"), (tre, "txt")):
            m = rx.fullmatch(name)
            if m and path == f"{BENCH_REL}/{name}":
                found.setdefault(int(m.group(1)), {"json": None, "txt": None})[slot] = path
    ks = sorted(found)
    if ks != list(range(1, len(ks) + 1)):
        raise Refused([f"{engine}'s {kind} attempts are k = {ks}: one is missing, and an attempt is never renamed "
                       "or deleted (B5; the sheet 12.8)"])
    return [dict(k=k, **found[k]) for k in ks]


def _no_constant(name):
    raise ValueError(f"{name} in a benchmark file: the frozen script writes none")


def read_json_exact(path):
    """A benchmark file with every float read as a Decimal (row 135 (3): lower_min exact); NaN refused."""
    with open(path, encoding="utf-8") as fh:
        return json.loads(fh.read(), parse_float=Decimal, parse_constant=_no_constant)


def b0_record(root, git_head):
    """(path, the committed B0 record of `git_head` or None). B0 writes it once for each commit B1 runs from, and
    B5 commits it (C1b's runbook B0)."""
    if not git_head:
        return None, None
    rel = f"{BENCH_REL}/{B0_RECORD.format(git_head=git_head)}"
    if rel not in head_files(root, BENCH_REL):
        return rel, None
    with open(os.path.join(root, rel), encoding="utf-8") as fh:
        return rel, json.load(fh)


def expected_plan(engine, protocol):
    """The plan block benchmark_training.py writes for the runbook's B1 command under `protocol`, key for key
    (make_plan, then main's update; test_epa_backend.Protocol builds it through the frozen script's own main)."""
    return dict(road=protocol["road"], engine=engine, dt=protocol["dt"], roads_record=protocol["roads_record"],
                scored_share=protocol["scored_share"], reward_knock=protocol["reward_knock"],
                steps_per_run=protocol["steps_per_run"], det_steps=B.DET_STEPS, runs_grid=[protocol["runs"]],
                repeats=protocol["repeats"], buffer=protocol["buffer"], smoke_test=False, window_days=None,
                no_determinism=False)


def _plant_id(plant):
    return json.dumps({k: (plant or {}).get(k) for k in B.PLANT_KEYS}, sort_keys=True, default=str)


def operator_faults(doc, engine, protocol, b0, *, trainable_before, protocol_script):
    """Row 135 (4)(b)'s operator faults that the attempt's own blocks show before its rows are read: [] or why."""
    code, m, plan = doc.get("code") or {}, doc.get("machine") or {}, doc.get("plan") or {}
    out = []
    if code.get("git_dirty") is not False:
        out.append(f"code.git_dirty is {code.get('git_dirty')!r}, not False")
    want = expected_plan(engine, protocol)
    diff = sorted(k for k in set(want) | set(plan) if k not in plan or k not in want or plan[k] != want[k])
    if diff:
        out.append("the plan is not the protocol's: " + ", ".join(
            f"{k} {plan.get(k, '(absent)')!r} for {want.get(k, '(absent)')!r}" for k in diff))
    for key, have, wanted in (("devices_asked", doc.get("devices_asked"), [protocol["device"]]),
                              ("machine.torch", m.get("torch"), protocol["torch"]),
                              ("machine.python", m.get("python"), protocol["python"])):
        if have != wanted:
            out.append(f"{key} {have!r}, not the protocol's {wanted!r}")
    if protocol_script is not None:
        out.append(f"its {PROTOCOL_SCRIPT_REL} is not the protocol commit's: {protocol_script}")
    if b0 is None:
        out.append(f"no committed B0 record for its git_head {code.get('git_head')!r} "
                   f"({BENCH_REL}/{B0_RECORD.format(git_head=code.get('git_head'))})")
    else:
        for key, have in (("host", m.get("host")), ("git_head", code.get("git_head")),
                          ("benchmark_sha", code.get("benchmark_sha")), ("train_sha", code.get("train_sha"))):
            if b0.get(key) != have:
                out.append(f"its {key} {have!r} is not its B0 record's {b0.get(key)!r}")
        if b0.get("git_dirty") is not False:
            out.append(f"its B0 record's git_dirty is {b0.get('git_dirty')!r}, not False")
    if m.get("engines_trainable") != list(trainable_before):
        out.append(f"machine.engines_trainable {m.get('engines_trainable')!r} is not the summary-only reading "
                   f"{list(trainable_before)!r} (inputs.trainable_before)")
    return out


def row_why_kind(why):
    """What a row's `why` (benchmark_training.row_verdict's words) is: 'a' a crash (a timeout, exit codes,
    missing runs, an 'error:' line, row 135 (4)(a)), 'device' or 'plant' an operator fault ((b)), None a reason
    the frozen script does not print."""
    if (why.startswith("timed out after ") or why.startswith("exit codes ") or why.startswith("error: ")
            or re.fullmatch(r"[0-9]+ of [0-9]+ runs finished", why)):
        return "a"
    if why.startswith("trained on "):
        return "device"
    if why.startswith("its runs trained on more than one plant"):
        return "plant"
    return None


def configuration(doc, device, N):
    """The (device, N) row of the attempt's recommendation.configurations, checked against
    benchmark_training.configurations recomputed from its rows (CONF_KEYS). Refused when the file disagrees
    with itself: the frozen script did not write it so."""
    recorded = [c for c in ((doc.get("recommendation") or {}).get("configurations") or [])
                if c.get("device") == device and c.get("runs") == N]
    again = [c for c in B.configurations(doc.get("concurrency") or []) if c["device"] == device and c["runs"] == N]
    if len(recorded) != 1 or len(again) != 1:
        raise Refused([f"recommendation.configurations holds {len(recorded)} rows at ({device}, {N}), its rows "
                       f"give {len(again)}: not as benchmark_training.py writes it (rule 1.11)"])
    bad = [k for k in CONF_KEYS if recorded[0].get(k) != again[0].get(k)]
    if bad:
        raise Refused([f"recommendation.configurations at ({device}, {N}) disagrees with its rows on {bad}: not as "
                       "benchmark_training.py writes it (rule 1.11)"])
    return recorded[0]


def classify(doc, engine, protocol, live, b0, *, trainable_before, protocol_script):
    """One B1 attempt (`doc`, read by read_json_exact) of `engine` under `protocol`, by row 135 (4):
    ('crash', why), ('fallback', why), ('defect', why), ('stop', why) or ('measurement', lower_min, a Fraction).

    `live` is {engine: the plant block live_plants builds}; `b0` is the committed B0 record of the attempt's
    git_head, or None; `trainable_before` is inputs.trainable_before; `protocol_script` is
    protocol_script_problem's answer for its git_head (None: the protocol commit's script). Refused for an
    outcome row 135 (4) does not name (rule 1.11)."""
    dev, N, R = protocol["device"], protocol["runs"], protocol["repeats"]
    status = doc.get("status")
    if status != "finished":
        return "crash", f"(a) its status is {status!r}, not 'finished'"
    faults = operator_faults(doc, engine, protocol, b0, trainable_before=trainable_before,
                             protocol_script=protocol_script)
    if faults:
        return "crash", "(b) an operator fault: " + "; ".join(faults)
    det = (doc.get("determinism") or {}).get(dev) or {}
    if det.get("identical") is None:
        return "crash", f"(a) seed 0 was not trained twice to the end on {dev}: {det.get('why') or 'no verdict'}"
    if det.get("identical") is False:
        why = f"seed 0 trained two different agents on {dev} (section 4: {det.get('first')})"
        return ("fallback", "(c) " + why) if dev == "cuda" else ("defect", "(c) " + why)
    rows = doc.get("concurrency") or []
    stray = [(r.get("device"), r.get("runs")) for r in rows if r.get("device") != dev or r.get("runs") != N]
    if stray:
        return "crash", f"(b) an operator fault: rows the protocol does not time, at {stray}"
    for r in rows:
        if not r.get("ok"):
            whys = list(r.get("why") or [])
            kinds = [row_why_kind(w) for w in whys]
            if not whys or None in kinds:
                raise Refused([f"{engine}: a row at N = {N} is not ok for a reason row 135 (4) does not name "
                               f"({whys}): the step stops and it is reported (rule 1.11)"])
            label = "(b) an operator fault: " if {"device", "plant"} & set(kinds) else "(a) "
            return "crash", label + f"repeat {r.get('repeat')}'s row at N = {N}: " + "; ".join(whys)
    if len(rows) != R:
        return "crash", f"(a) the row at N = {N} was measured {len(rows)} of {R} times"
    if len({_plant_id(r.get("plant")) for r in rows}) > 1:
        return "crash", "(b) an operator fault: its rows trained on more than one plant"
    plant = rows[0].get("plant") or {}
    if plant.get("reward_knock") is not False:
        return "crash", f"(b) an operator fault: plant.reward_knock is {plant.get('reward_knock')!r}, not False"
    if plant.get("backend") != FP.BACKEND_CYCLE:
        return "crash", f"(b) an operator fault: plant.backend is {plant.get('backend')!r}, not 'cycle' (row 136)"
    mine = live[engine]
    off = [k for k in B.PLANT_KEYS if plant.get(k) != mine.get(k)]
    if off:
        return "crash", f"(b) an operator fault: the plant timed is not this tree's, on {off}"
    conf = configuration(doc, dev, N)
    if not conf.get("ok"):
        return "crash", f"(a) the row at N = {N} is not clean in every repeat planned"
    if dev == "cuda":
        twins = conf.get("seed0_twice") or []
        if False in twins:
            return "fallback", "(c) two copies of seed 0 trained different agents while they shared the GPU"
        if len(twins) != R or None in twins:
            return "crash", f"(a) seed 0's two copies were compared in {twins}, not in each of {R} repeats"
        if conf.get("fits") is False:
            return "fallback", f"(c) N = {N} does not fit at production size"
    elif conf.get("fits") is False:
        return "stop", f"(c) N = {N} does not fit at production size on the CPU"
    return "measurement", Fraction(conf["lower_min"])


# Row 135 (4)(c)'s words, and row 146 (4)'s: "B1 reading 'defect' or 'stop': row 135 (4)(c), with its "stops the
# four-engine training before T, and it is reported" read as "the study's training stops, and it is reported"; a
# defect is fixed, P is re-made by row 140 (5) if PLANT_CODE moves, and B1 is repeated"
DEFECT_TEXT = ("row 135 (4)(c): on the CPU, identical False is a coding defect. It is found and fixed (a fix to "
               "PLANT_CODE re-makes P by row 140 (5)'s route), B1 is then repeated for every engine by this protocol, "
               "every attempt kept, and the attempts before the fix are superseded")
STOP_TEXT = ("row 135 (4)(c): on the CPU, fits False at N stops the four-engine training before T, and it is "
             "reported; for the B58 study (row 146 (4)), the study's training stops, and it is reported")


def read_series(root, engine, *, kind, protocol, live, trainable_before, cache):
    """One series of `engine`'s attempts (`kind`), read by the sheet 10.1's rule: every attempt whose cost files
    differ from HEAD's superseded; of the rest, every one but the last a crash, and the last not. Returns
    {outcome, attempt, doc, crashes, superseded, b0, problems}."""
    out = {"outcome": None, "attempt": None, "doc": None, "crashes": [], "superseded": [], "b0": [],
           "problems": []}
    attempts = bench_attempts(root, engine, kind=kind)
    if not attempts:
        out["problems"].append(f"{engine}: no committed {kind} attempt under {BENCH_REL} (B1, ORDER step 18)")
        return out
    read = []
    for a in attempts:
        if a["json"] is None:
            read.append((a, ("crash", "(a) no JSON: the benchmark ended before it wrote its file (its .txt only)"),
                         None))
            continue
        doc = read_json_exact(os.path.join(root, a["json"]))
        head = (doc.get("code") or {}).get("git_head")
        sup = superseded_why(root, head, cache) if head else None
        if sup:
            out["superseded"].append({"engine": engine, "path": a["json"],
                                      "sha_text": common.sha_text(os.path.join(root, a["json"])),
                                      "git_head": head, "why": sup})
            continue
        b0_rel, b0 = b0_record(root, head)
        if b0 is not None and all(x["path"] != b0_rel for x in out["b0"]):
            out["b0"].append({"path": b0_rel, "sha_text": common.sha_text(os.path.join(root, b0_rel)),
                              "git_head": head})
        script = protocol_script_problem(root, head, protocol)
        read.append((a, classify(doc, engine, protocol, live, b0, trainable_before=trainable_before,
                                 protocol_script=script), doc))
    if not read:
        out["problems"].append(f"{engine}: every {kind} attempt is superseded, so none is left to read: B1 is "
                               "repeated for every engine from the re-made, pushed tree by row 135's protocol, every "
                               "attempt kept (row 140 (5))")
        return out
    for a, o, _ in read[:-1]:
        if o[0] != "crash":
            out["problems"].append(f"{engine}: {kind} attempt {a['k']} reads {o[0]}, and attempt {read[-1][0]['k']} "
                                   "follows it: only a crash is repeated (row 135 (4))")
    for a, o, _ in read:
        if o[0] == "crash":
            path = a["json"] or a["txt"]
            out["crashes"].append({"engine": engine, "path": path,
                                   "sha_text": common.sha_text(os.path.join(root, path)), "why": o[1]})
    a, o, doc = read[-1]
    if o[0] == "crash":
        out["problems"].append(f"{engine}: its last {kind} attempt ({a['k']}) is a crash: {o[1]}. Repeat it, for "
                               "that engine alone, into its next k (row 135 (4)(a)-(b); the runbook's B1)")
    out.update(outcome=o, attempt=a, doc=doc)
    return out


def benchmark_entry(root, series, protocol):
    """inputs.benchmarks[e] (the sheet 12.5) for a series whose last attempt is the measurement."""
    doc, path = series["doc"], series["attempt"]["json"]
    dev, N = protocol["device"], protocol["runs"]
    rows = [r for r in doc["concurrency"] if r["device"] == dev and r["runs"] == N]
    conf = configuration(doc, dev, N)
    lower = Fraction(conf["lower_min"])
    r_e = lower / N
    return {"path": path, "sha_text": common.sha_text(os.path.join(root, path)),
            "git_head": doc["code"]["git_head"], "host": doc["machine"]["host"], "device": dev,
            "torch": doc["machine"]["torch"], "python": doc["machine"]["python"],
            "benchmark_sha": doc["code"]["benchmark_sha"], "train_sha": doc["code"]["train_sha"],
            "plant": {k: rows[0]["plant"].get(k) for k in B.PLANT_KEYS}, "runs": N,
            "lower_by_repeat": [str(r["lower_steps_per_s"]) for r in sorted(rows, key=lambda r: r.get("repeat", 0))],
            "lower_min": str(conf["lower_min"]), "r_e": f"{r_e.numerator}/{r_e.denominator}",
            "r_e_steps_per_s": float(r_e), "steady": conf["steady"], "loaded": conf["loaded"], "fits": conf["fits"],
            "determinism": {k: doc["determinism"][dev].get(k) for k in ("identical", "steps", "n_differences")},
            "git_dirty": doc["code"]["git_dirty"]}


# ================================================================== the record
def _jsonable(protocol):
    return None if protocol is None else {k: list(v) if isinstance(v, tuple) else v for k, v in protocol.items()}


def live_plants(engine_ids):
    """{engine: its plant block, B.PLANT_KEYS key for key}, as a B1 row's config.json records it from the
    fingerprint: the only caller of FP.plant_fingerprint here, with both backends 'cycle', preview_h_s None and
    reward_knock False, every one passed (mistake 19; the sheet 1.7), and 'backend' read from train_backend
    (config.json's backend = live['train_backend'], the sheet 12.2). PLANT_KEYS hold no scenario or episodes, so
    the protocol passed, 'phase-d', changes none of them and needs no redraws.json."""
    import engines
    out = {}
    for e in engine_ids:
        fp = FP.plant_fingerprint("phase-d", plant=engines.get(e), train_backend=FP.BACKEND_CYCLE,
                                  score_backend=FP.BACKEND_CYCLE, preview_h_s=None, reward_knock=False)
        out[e] = {k: (fp["train_backend"] if k == "backend" else fp.get(k)) for k in B.PLANT_KEYS}
    return out


def _cpu_files_problems(root, engines_read):
    if CPU_PROTOCOL is not None:
        return []
    stray = [p for p in head_files(root, BENCH_REL) for e in engines_read
             if _attempt_re(CPU_ATTEMPT, e).fullmatch(p.rpartition("/")[2])
             or _attempt_re(_txt(CPU_ATTEMPT), e).fullmatch(p.rpartition("/")[2])]
    return [f"{p}: a CPU series beside the protocol's, which names the CPU (row 135 (4)(c): on the CPU there is no "
            "second series)" for p in stray]


def dirty_paths(root):
    """Every path `git status --porcelain=v1 -z --untracked-files=all` lists in `root`: staged, modified, deleted or
    untracked, both paths of a rename or a copy, repository-relative and unquoted."""
    items = _git_out(root, "status", "--porcelain=v1", "-z", "--untracked-files=all").split("\0")
    out, i = [], 0
    while i < len(items):
        entry, i = items[i], i + 1
        if len(entry) < 4:
            continue
        out.append(entry[3:])
        if "R" in entry[:2] or "C" in entry[:2]:          # -z writes a rename as 'XY new', then 'old'
            if i < len(items) and items[i]:
                out.append(items[i])
            i += 1
    return out


def record_moving_paths(root, head):
    """Of dirty_paths(root), every change that can move the record compute builds at commit `head`, as 'path
    (why)', [] when there is none: any .py (an import closure, or the running code's own sha_text, can change), a
    file under BENCH_REL (B1's attempts and B0 records), Run 2's summary, the backend record, and every other cost
    file of `head` (cost_files(root, head), read from git archive, so that a changed .py cannot change the list).
    Any other change, such as PR-B's staged preregistration, its session report and CHECKPOINT, moves nothing
    (row 146 (6): PR-B's gate runs check on its staged tree; the sheet 17's 14)."""
    import engines
    out, rest = [], []
    for p in dirty_paths(root):
        why = ("a .py file: an import closure can change" if p.endswith(".py") else
               f"under {BENCH_REL}: B1's attempts and B0 records" if p.startswith(BENCH_REL + "/") else
               "Run 2's summary" if p == engines.VALIDATION_SUMMARY_REL else
               "the backend record" if p == engines.BACKEND_REL else None)
        if why is None:
            rest.append(p)
        else:
            out.append(f"{p} ({why})")
    if rest:
        costs = set(cost_files(root, head))
        out += [f"{p} (a cost file)" for p in rest if p in costs]
    return out


def _build(root, *, live):
    """(the record or None, the problems): compute's whole work, writing nothing."""
    import engines
    root = os.path.abspath(root)
    problems = protocol_commit_problems(root, PROTOCOL)
    if CPU_PROTOCOL is not None:
        problems += protocol_commit_problems(root, CPU_PROTOCOL)
    if problems:
        return None, problems
    try:
        head = ER.tree_state(root)[0]
    except ER.Refused as e:
        return None, list(e.args[0])
    # row 146 (6): only a change that can move the record is refused (THE WORK TREE), so that PR-B's staged tree
    # passes check
    moving = record_moving_paths(root, head)
    if moving:
        return None, ["the work tree changes what the record is computed from: " + "; ".join(moving[:8])
                      + (" ..." if len(moving) > 8 else "") + ". Commit or restore each first; any other change "
                      "is allowed (row 146 (6))"]
    try:
        summary = engines.committed_record(root, engines.VALIDATION_SUMMARY_REL)
        if summary is None:
            return None, [f"{engines.VALIDATION_SUMMARY_REL} is not committed: the backend record follows Run 2 "
                          "(ORDER step 11) and B1 (step 18)"]
        trainable_before = engines.trainable_from(summary, None)
    except ValueError as e:
        return None, [f"engines' reader of the records: {e}"]
    if sorted(live) != sorted(trainable_before):
        return None, [f"live covers {sorted(live)}, not the engines B1 timed, {list(trainable_before)}"]
    cache, series = {}, {}
    for e in trainable_before:
        series[e] = read_series(root, e, kind="device", protocol=PROTOCOL, live=live,
                                trainable_before=trainable_before, cache=cache)
        problems += series[e]["problems"]
    problems += _cpu_files_problems(root, trainable_before)
    if PROTOCOL["device"] == "cuda":
        # row 135 (4)(c): on CUDA every engine's CPU series exists, run at the same visit; it is read only after a
        # fallback, and then for every engine
        if CPU_PROTOCOL is None:
            problems.append("PROTOCOL names CUDA and CPU_PROTOCOL is None (row 135 (4)(c))")
        else:
            problems += [f"{e}: no committed CPU series beside its CUDA one (row 135 (4)(c))"
                         for e in trainable_before if not bench_attempts(root, e, kind="cpu")]
    if problems:
        return None, problems
    fallback, protocol = None, PROTOCOL
    failed = [e for e in trainable_before if series[e]["outcome"][0] == "fallback"]
    if failed:
        e = failed[0]
        fallback = {"engine": e, "path": series[e]["attempt"]["json"],
                    "sha_text": common.sha_text(os.path.join(root, series[e]["attempt"]["json"])),
                    "why": series[e]["outcome"][1], "engines": failed}
        cpu = {}
        for e2 in trainable_before:
            cpu[e2] = read_series(root, e2, kind="cpu", protocol=CPU_PROTOCOL, live=live,
                                  trainable_before=trainable_before, cache=cache)
            cpu[e2]["crashes"] = series[e2]["crashes"] + cpu[e2]["crashes"]
            cpu[e2]["superseded"] = series[e2]["superseded"] + cpu[e2]["superseded"]
            cpu[e2]["b0"] = series[e2]["b0"] + [x for x in cpu[e2]["b0"] if x not in series[e2]["b0"]]
            problems += cpu[e2]["problems"]
        series, protocol = cpu, CPU_PROTOCOL
        if problems:
            return None, problems
    for e in trainable_before:
        kind = series[e]["outcome"][0]
        if kind == "defect":
            problems.append(f"{e}: {series[e]['outcome'][1]}. {DEFECT_TEXT}")
        elif kind == "stop":
            problems.append(f"{e}: {series[e]['outcome'][1]}. {STOP_TEXT}")
        elif kind != "measurement":
            problems.append(f"{e}: its series ends in {kind} on {protocol['device']}, which row 135 (4) gives no "
                            "consequence there (rule 1.11)")
    if problems:
        return None, problems
    rates = {e: (series[e]["outcome"][1], protocol["runs"]) for e in trainable_before}
    rule = apply_rule(trainable_before, rates, w_s=W_S)
    summary_rel = engines.VALIDATION_SUMMARY_REL
    summary_sha = common.sha_text(os.path.join(root, summary_rel))
    entries = {}
    for e in engines.known():
        if e in rule["engines"]:
            entries[e] = rule["engines"][e]
        else:
            entries[e] = {"drop": True, "backend": None, "reason": f"Run 2: {summary_rel} {summary_sha} (row 107 (1))"}
    n = rule["n"]
    in_test = [e for e in engines.known() if not entries[e]["drop"]]
    at_n = None if n is None else {e: total_seconds(n, {e: rates[e]}) for e in in_test}
    total = None if at_n is None else sum(at_n.values(), Fraction(0))
    notes = ["Every engine trains and is scored on the exact cycle, with no table (row 136, contract version 6 for "
             "the order of leaving and the table route only).",
             f"{summary_rel}'s drop_order text (validate_epa.DROP_ORDER, validate_epa.py:165-167: the Ford first) is "
             "contract version 5's; the order applied here is row 136's, drop_order.",
             "Each attempt's own recommendation.schedule, seeds_in_window and 'x 4 engines' lines count ENGINES = 4 "
             "engines at that engine's rate (benchmark_training._days) and are not this schedule."]
    if n is None:
        if any(v["drop"] for v in rule["engines"].values()):
            notes.append("No EPA engine survives: the schedule dropped the last one (row 136 (1)), so the four-engine "
                         "test does not run, and the failed schedule is reported as the result (MD:1611-1612).")
        else:
            notes.append("No EPA engine survives: Run 2 dropped every one (inputs.summary) and the schedule dropped "
                         "none, so the four-engine test does not run, and the failed validations are reported as "
                         "the results (row 136 (1); MD:1611-1612; INTERFACES 17's 10.2).")
        notes.append("This null n is the four-engine test's. The B58 study across H (rows 146-147) trains n = 20 per "
                     "arm, fixed by row 147 (4) and read from no record: \"The backend record's null n is not this "
                     "n.\"")
    # the running code's own sha_text: this module and its import closure, in its own tree (REPO)
    closure = ER.import_closure(MODULE_REL, root=REPO)
    record = {
        "schema": engines.BACKEND_SCHEMA,
        "rule": ("rows 114 and 136 (W: row 134 (1); the protocol: row 135): n is the largest n for which the sum over "
                 "the engines in the test of ceil(ARMS n / N) x PROD_STEPS x N / lower_min fits W; while n < 20 and an "
                 "EPA engine is in the test, the Honda, then the Mazda, then the Ford leave and are dropped, with no "
                 "table, and n is recomputed; with no EPA engine left, n is null and the four-engine test does not "
                 "run (MD:1611-1612)"),
        "window": {"W_s": W_S, "first": W_FIRST, "last": W_LAST, "row": "row 134 (1)"},
        "constants": {"arms": ARMS, "prod_steps": PROD_STEPS, "n_min": N_MIN, "seed_limit": SEED_LIMIT,
                      "never_dropped": ER.NEVER_DROPPED},
        "protocol": {"PROTOCOL": _jsonable(PROTOCOL), "CPU_PROTOCOL": _jsonable(CPU_PROTOCOL)},
        "drop_order": list(DROP_ORDER),
        "inputs": {
            "trainable_before": list(trainable_before),
            "summary": {"path": summary_rel, "sha_text": summary_sha},
            "benchmarks": {e: benchmark_entry(root, series[e], protocol) for e in trainable_before},
            "fallback": fallback,
            "superseded": [x for e in trainable_before for x in series[e]["superseded"]],
            "crashes": [x for e in trainable_before for x in series[e]["crashes"]],
            "b0": sorted({x["path"]: x for e in trainable_before for x in series[e]["b0"]}.values(),
                         key=lambda x: x["path"]),
        },
        "trace": rule["trace"],
        "engines": entries,
        "in_test": in_test,
        "n": n,
        "seconds_at_n": None if at_n is None else {e: float(v) for e, v in at_n.items()},
        "total_s": None if total is None else float(total),
        "slack_s": None if total is None else float(W_S - total),
        "notes": notes,
        "provenance": {"commit": head, "code_sha_text": ER.sha_texts(closure, root=REPO),
                       "versions": _versions()},
    }
    try:
        again = engines.trainable_from(summary, record)
    except ValueError as e:
        return None, [f"engines.trainable_from refuses the record: {e} (this module's defect, never P's)"]
    if tuple(again) != tuple(in_test):
        return None, [f"engines.trainable_from gives {again} from the record, not its in_test {in_test} (this "
                      "module's defect, never P's)"]
    return record, []


def _versions():
    import epa_freeze
    return epa_freeze.versions()


def problems(root, *, live):
    """Every reason compute(root, live=live) refuses, [] when it would build the record."""
    try:
        return _build(root, live=live)[1]
    except Refused as e:
        return e.problems


def compute(root, *, live):
    """The record from the committed inputs in `root` (at a commit descending from the protocol commit, with no
    change in the work tree that can move the record, record_moving_paths), writing nothing. Refused with every
    problem found."""
    record, probs = _build(root, live=live)
    if probs:
        raise Refused(probs)
    return record


def record_path(root):
    import engines
    return os.path.join(os.path.abspath(root), *engines.BACKEND_REL.split("/"))


def write(root, *, live):
    """Tb: the record, written once through epa_roads.write_once, refused when it exists in the tree or in HEAD's
    history. Returns its sha_text."""
    import engines
    rel, path = engines.BACKEND_REL, record_path(root)
    probs = []
    if os.path.exists(path):
        probs.append(f"{rel} exists: it is written once and never edited")
    if _git_out(root, "log", "--format=%H", "HEAD", "--", rel).strip():
        probs.append(f"{rel} is in HEAD's history: it is written once (row 114)")
    if probs:
        raise Refused(probs)
    record = compute(root, live=live)
    try:
        return ER.write_once(path, record)
    except ER.Refused as e:
        raise Refused(e.args[0]) from None


def differences(a, b):
    """Every path where `a` and `b` differ, as text."""
    return _differences_at(a, b, "")


def _differences_at(a, b, at):
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in sorted(set(a) | set(b), key=str):
            if k not in a or k not in b:
                out.append(f"{at}{k}: {'absent' if k not in a else 'present'} in the committed record, "
                           f"{'absent' if k not in b else 'present'} in the recomputation")
            else:
                out += _differences_at(a[k], b[k], f"{at}{k}.")
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        return [d for i, (x, y) in enumerate(zip(a, b)) for d in _differences_at(x, y, f"{at}{i}.")]
    return [] if a == b and type(a) is type(b) else [f"{at.rstrip('.')}: committed {a!r}, recomputed {b!r}"]


# The commit the record was computed at and the interpreter that computed it describe where, not what: check
# compares everything else
CHECK_IGNORES = ("commit", "versions")


def check(root, *, live):
    """The differences between the record committed at HEAD and compute's recomputation, [] when equal. Refused
    when the record is not committed at HEAD."""
    import engines
    import epa_freeze
    if not epa_freeze.committed_at_head(engines.BACKEND_REL, root=os.path.abspath(root)):
        raise Refused([f"{engines.BACKEND_REL} is not committed at HEAD in {root}"])
    with open(record_path(root), encoding="utf-8") as fh:
        committed = json.load(fh)
    again = json.loads(json.dumps(compute(root, live=live), allow_nan=False))
    for rec in (committed, again):
        for k in CHECK_IGNORES:
            (rec.get("provenance") or {}).pop(k, None)
    return differences(committed, again)


# ================================================================== the runbook's names (RunbookNames)
def runbook_text(root, rev):
    """docs/build_step_2/DEVICE_RUNBOOK.md as commit `rev` holds it (CRLF read as LF)."""
    return _git_out(root, "show", f"{rev}:{RUNBOOK_REL}").replace("\r\n", "\n")


def runbook_blocks(text, step):
    """Every ```bash block of the runbook's step `step` ('B0', 'B1', 'B5'), from its bold heading to the next
    step's or section's (test_device_gate.RunbookB1 reads the blocks the same way)."""
    start = text.find(f"**{step}.")
    if start == -1:
        return []
    end = min(i for i in (text.find("\n**B", start + 1), text.find("\n## ", start + 1), len(text)) if i != -1)
    out, at = [], start
    while True:
        first = text.find("```bash\n", at, end)
        if first == -1:
            return out
        first += len("```bash\n")
        last = text.find("\n```", first)
        out.append(text[first:last])
        at = last + len("\n```")


def _as_template(name):
    return name.replace("$E", "{engine}").replace("$k", "{k}").replace("{rec['git_head']}", "{git_head}")


def runbook_name_problems(text):
    """Why the runbook's B0, B1 and B5 blocks do not name what this module reads, or []: B1's --out names (with $E
    and $k read as {engine} and {k}) are ATTEMPT and CPU_ATTEMPT, its tee'd .txt their twins, and its k loop counts
    each name over $B1OUT and BENCH_REL; B0's record is B0_RECORD (rec['git_head'] read as {git_head}); B5 copies
    into BENCH_REL, and every name the three format matches one of its `cp -n` globs."""
    out = []
    b1 = "\n".join(runbook_blocks(text, "B1"))
    outs = {_as_template(m) for m in re.findall(r'--out "\$B1OUT/([^"]+)"', b1)}
    tees = {_as_template(m) for m in re.findall(r'tee "\$B1OUT/([^"]+)"', b1)}
    if outs != {ATTEMPT, CPU_ATTEMPT}:
        out.append(f"B1's --out names are {sorted(outs)}, not ATTEMPT and CPU_ATTEMPT {[ATTEMPT, CPU_ATTEMPT]}")
    if tees != {_txt(ATTEMPT), _txt(CPU_ATTEMPT)}:
        out.append(f"B1's tee names are {sorted(tees)}, not the attempts' .txt twins")
    counted = {(d, _as_template(n)) for d, n in re.findall(r'\[ -e "(\$B1OUT|[^"$]+)/([^"]+)" \]', b1)}
    want = {(d, n) for d in ("$B1OUT", BENCH_REL) for n in (ATTEMPT, CPU_ATTEMPT, _txt(ATTEMPT), _txt(CPU_ATTEMPT))}
    if counted != want:
        out.append(f"B1's k loops count {sorted(counted)}, not each attempt's .json and .txt over $B1OUT and "
                   f"{BENCH_REL} (the sheet 12.8)")
    b0 = "\n".join(runbook_blocks(text, "B0"))
    recs = {_as_template(m) for m in re.findall(r'f"(B0_[^"]*\.json)"', b0)}
    if recs != {B0_RECORD}:
        out.append(f"B0's record name is {sorted(recs)}, not B0_RECORD {B0_RECORD!r}")
    b5 = "\n".join(runbook_blocks(text, "B5"))
    cps = re.findall(r"^cp -n (.+) (\S+)$", b5, flags=re.M)
    if len(cps) != 1:
        return out + [f"B5 holds {len(cps)} `cp -n` lines, not one"]
    sources, dest = cps[0]
    if dest.rstrip("/") != BENCH_REL:
        out.append(f"B5 copies into {dest!r}, not {BENCH_REL}/")
    globs = [s.replace('"$B1OUT"/', "", 1) for s in sources.split()]
    if any("/" in g or "$" in g for g in globs):
        out.append(f"B5's sources {sources.split()} are not all in \"$B1OUT\"")
    names = [t.format(engine=e, k=k) for t in (ATTEMPT, CPU_ATTEMPT, _txt(ATTEMPT), _txt(CPU_ATTEMPT))
             for e in ("b58",) + DROP_ORDER for k in (1, 2, 10)] + [B0_RECORD.format(git_head="0fbc744")]
    lost = [n for n in names if not any(fnmatch.fnmatchcase(n, g) for g in globs)]
    if lost:
        out.append(f"B5's globs {globs} do not copy {lost[:4]}{' ...' if len(lost) > 4 else ''}")
    return out


# ================================================================== the preregistration's commands
FLAGS_WITH_VALUE = ("--engine", "--device", "--road", "--dt", "--roads-record", "--reward-knock", "--seeds",
                    "--steps", "--jobs", "--out")
FLAGS_ALONE = ("--third-arm", "--recipe29", "--no-resume")


def preregistration_commands(text):
    """(every train_all.py command in the preregistration's fenced blocks, as its tokens after train_all.py,
    a line continued by a backslash joined; the lines outside the fences that name `train_all.py --`)."""
    commands, outside, fenced, buf = [], [], False, ""
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip().startswith("```"):
            fenced, buf = not fenced, ""
            continue
        if not fenced:
            if re.search(r"train_all\.py\s+--", line):
                outside.append(line.strip())
            continue
        buf += line.rstrip()
        if buf.endswith("\\"):
            buf = buf[:-1] + " "
            continue
        whole, buf = buf, ""
        if "train_all.py" not in whole:
            continue
        tokens = shlex.split(whole, comments=True, posix=True)
        at = [i for i, t in enumerate(tokens) if t.replace("\\", "/").rpartition("/")[2] == "train_all.py"]
        if at:
            commands.append(tokens[at[0] + 1:])
    return commands, outside


def _number(x, kind):
    try:
        return kind(x)
    except (TypeError, ValueError):
        return None


def preregistration_protocol(record):
    """The protocol the preregistration's commands are checked against: CPU_PROTOCOL when B1's committed series
    read a fallback (the record's inputs.fallback not null; row 135 (4)(c)), PROTOCOL otherwise (the sheet 10.1)."""
    if (record.get("inputs") or {}).get("fallback") is None:
        return PROTOCOL
    if CPU_PROTOCOL is None:
        raise Refused(["the backend record read a CUDA fallback, and CPU_PROTOCOL is None"])
    return CPU_PROTOCOL


def preregistration_problems(text, record, *, protocol, arms):
    """Why the preregistration's train_all.py commands are not the ones the sheet section 11 fixes for `record`
    (its in_test and n) under `protocol` (PROTOCOL, or CPU_PROTOCOL after a fallback) and `arms`, or []: one command
    per engine in the test, each with exactly the section's flags and values, --blind-per-h exactly when arms is 4."""
    if record.get("n") is None:
        return ["the backend record's n is null: no EPA engine survives, so the preregistration is never written "
                "(row 136 (1); the sheet 10.2)"]
    commands, outside = preregistration_commands(text)
    out = [f"a train_all.py command outside a fenced block: {line!r}" for line in outside]
    n, seen = record["n"], []
    for cmd in commands:
        flags, i = {}, 0
        while i < len(cmd):
            f = cmd[i]
            if f in FLAGS_WITH_VALUE and i + 1 < len(cmd):
                flags.setdefault(f, []).append(cmd[i + 1])
                i += 2
            else:
                flags.setdefault(f, []).append(None)
                i += 1
        engine = (flags.get("--engine") or [None])[0]
        seen.append(engine)
        want_alone = set(FLAGS_ALONE) | ({"--blind-per-h"} if arms == 4 else set())
        bad = sorted(f for f in flags if f not in FLAGS_WITH_VALUE and f not in want_alone)
        bad += sorted(f for f in set(FLAGS_WITH_VALUE) | want_alone if len(flags.get(f) or []) != 1)
        if bad:
            out.append(f"{engine}: flags {bad} absent, repeated or not the section's")
            continue
        v = {f: flags[f][0] for f in FLAGS_WITH_VALUE}
        wants = (("--device", v["--device"] == protocol["device"]),
                 ("--jobs", v["--jobs"] == str(protocol["runs"])),
                 ("--road", v["--road"] == protocol["road"]),
                 ("--dt", _number(v["--dt"], float) == protocol["dt"]),
                 ("--roads-record", v["--roads-record"] == protocol["roads_record"]),
                 ("--reward-knock", v["--reward-knock"] == protocol["reward_knock"]),
                 ("--steps", v["--steps"] == str(PROD_STEPS)),
                 ("--seeds", v["--seeds"] == f"0-{n - 1}"),
                 ("--out", v["--out"] == PR_OUT.format(engine=engine)),
                 ("--engine", engine in record["in_test"]))
        out += [f"{engine}: {f} {v[f]!r} is not the section's" for f, ok in wants if not ok]
    if sorted(x for x in seen if x) != sorted(record["in_test"]) or None in seen:
        out.append(f"the commands train {seen}, not each engine of in_test {record['in_test']} once")
    return out


# ================================================================== the B58 study's commands (PR-B)
def _tokens(text):
    """`text` split as the shell splits it (a trailing # comment dropped); by spaces when it does not parse."""
    try:
        return shlex.split(text, comments=True, posix=True)
    except ValueError:
        return text.split()


# A shell line's words: its control operators (each a word of its own, as shlex leaves them), a VAR=value word,
# an interpreter (python, python3, python.exe, a path to one, or a shell variable such as $PY) and its flags, and a
# redirection ('2>&1', '>log', or '>' with its target next)
SHELL_OPERATORS = ("|", "||", "&&", ";", "&")
_ENV_WORD = re.compile(r"[A-Za-z_][A-Za-z0-9_]*=.*")
_INTERPRETER = re.compile(r"python[0-9.]*(\.exe)?|\$\{?[A-Za-z_][A-Za-z0-9_]*\}?", re.IGNORECASE)
_INTERPRETER_FLAGS = re.compile(r"-[BIu]+")
_REDIRECTION = re.compile(r"[0-9]*(?:>>?|<)(&[0-9]+)?(.*)")


def _file_name(token):
    return token.replace("\\", "/").rpartition("/")[2]


def _simple_commands(tokens):
    """`tokens` cut at the shell's control operators, each simple command without its redirections and their
    targets: a `| tee log` or a `> log` after a command is not its argument."""
    out, words, target = [], [], False
    for t in tokens:
        m = _REDIRECTION.fullmatch(t)
        if t in SHELL_OPERATORS:
            out.append(words)
            words, target = [], False
        elif target:
            target = False
        elif m:
            target = not m.group(1) and not m.group(2)
        else:
            words.append(t)
    return [w for w in out + [words] if w]


def _train_all_args(tokens, *, span):
    """The arguments of every simple command in `tokens` that runs train_all.py: one whose program is
    train_all.py, after any VAR=value words, an interpreter and its -B, -I or -u; or one in which --engine follows
    train_all.py (so `nohup $PY train_all.py --engine ...` too). In an inline code span (`span`), only the second,
    as row 147 (3) quotes the training command. Any other naming of train_all.py, such as row 146 (6)'s `git diff
    ... -- train.py train_all.py ...` or a span such as `train_all.py --recipe29`, is a mention, not a command."""
    found = []
    for words in _simple_commands(tokens):
        at = next((i for i, t in enumerate(words) if _file_name(t) == "train_all.py"), None)
        if at is None:
            continue
        i = 0
        while i < at and _ENV_WORD.fullmatch(words[i]):
            i += 1
        if i < at and _INTERPRETER.fullmatch(_file_name(words[i])):
            i += 1
            while i < at and _INTERPRETER_FLAGS.fullmatch(words[i]):
                i += 1
        rest = words[at + 1:]
        if "--engine" in rest or (i == at and not span):
            found.append(rest)
    return found


def b58h_commands(text):
    """PR-B's train_all.py commands: ([(where, its arguments)], problems). `where` is 'fenced' for a command of a
    fenced line (a line continued by a backslash joined) and 'prose' for one of an inline code span outside the
    fences, each as _train_all_args reads it. A train_all.py command outside both, in bare prose, is a problem: no
    check would read it."""
    commands, problems, fenced, buf = [], [], False, ""
    for n, line in enumerate(text.replace("\r\n", "\n").split("\n"), 1):
        if line.strip().startswith("```"):
            fenced, buf = not fenced, ""
            continue
        if fenced:
            buf += line.rstrip()
            if buf.endswith("\\"):
                buf = buf[:-1] + " "
                continue
            whole, buf = buf, ""
            if "train_all.py" in whole:
                commands += [("fenced", rest) for rest in _train_all_args(_tokens(whole), span=False)]
            continue
        for span in re.findall(r"`([^`]*)`", line):
            if "train_all.py" in span:
                commands += [("prose", rest) for rest in _train_all_args(_tokens(span), span=True)]
        if re.search(r"train_all\.py\s+--", re.sub(r"`[^`]*`", " ", line)):
            problems.append(f"line {n}: a train_all.py command outside a fenced block and a code span: "
                            f"{line.strip()!r}")
    return commands, problems


def b58h_flags(protocol):
    """The flags every train_all.py line of PR-B carries with their values (the sheet 17's 10.1): --engine b58,
    --jobs PROTOCOL's runs typed as a number, --device PROTOCOL's device, --road four_engine, --dt 1,
    --roads-record PROTOCOL['roads_record'], --reward-knock out and --steps 450000, each read from `protocol` or
    from its owner, never typed here; besides them B58H_ALONE, and the line's own B58H_LINES entry."""
    return {"--engine": B58H_ENGINE, "--jobs": str(protocol["runs"]), "--device": protocol["device"],
            "--road": protocol["road"], "--dt": protocol["dt"], "--roads-record": protocol["roads_record"],
            "--reward-knock": protocol["reward_knock"], "--steps": str(PROD_STEPS)}


def b58h_kind(tokens):
    """'training' or 'pilot', the B58H_LINES entry whose --out the line names once; None for any other line."""
    outs = [tokens[i + 1] for i, t in enumerate(tokens[:-1]) if t == "--out"]
    return next((k for k, spec in B58H_LINES.items() if outs == [spec["--out"]]), None)


def b58h_line(tokens, *, protocol):
    """(b58h_kind of the line, why it is not that line of row 147 (3) under `protocol`, or []): exactly
    b58h_flags(protocol), the line's B58H_LINES values and B58H_ALONE, each once, no other flag and no stray
    token; --dt compared as a number, every other value as its text."""
    flags, stray, i = {}, [], 0
    while i < len(tokens):
        t = tokens[i]
        if t in B58H_WITH_VALUE:
            v = tokens[i + 1] if i + 1 < len(tokens) and not tokens[i + 1].startswith("--") else None
            flags.setdefault(t, []).append(v)
            i += 1 if v is None else 2
        elif t.startswith("--"):
            flags.setdefault(t, []).append(None)
            i += 1
        else:
            stray.append(t)
            i += 1
    kind = b58h_kind(tokens)
    if kind is None:
        return None, [f"--out {flags.get('--out')!r} is neither the training line's "
                      f"{B58H_LINES['training']['--out']!r} nor the pilot line's {B58H_LINES['pilot']['--out']!r} "
                      "(row 147 (3))"]
    want = dict(b58h_flags(protocol), **B58H_LINES[kind])
    probs = [f"{t!r} follows no flag that takes a value" for t in stray]
    for f in sorted(set(flags) - set(want) - set(B58H_ALONE)):
        probs.append(f"{f}: never (row 135 (5): the blinded arm is one arm, so three arms; the sheet 17's 10.1)"
                     if f == "--blind-per-h" else
                     f"{f}: not among the {kind} line's flags (the sheet 17's 10.1; row 147 (3))")
    for f in B58H_ALONE:
        if flags.get(f) != [None]:
            probs.append(f"{f}: absent or repeated")
    for f, v in want.items():
        got = flags.get(f) or []
        if len(got) != 1:
            probs.append(f"{f}: absent or repeated")
            continue
        same = _number(got[0], float) == v if f == "--dt" else got[0] == v
        if not same:
            probs.append(f"{f} {got[0]!r}, not {v!r}")
    return kind, probs


def b58h_problems(text, *, protocol):
    """Why PR-B's text does not state row 147 (3)'s two commands as the sheet 17's 10.1 fixes them, or []: every
    command b58h_commands finds is the training line or the pilot line (b58h_line), and each of the two is
    stated in a fenced block. The run of each through train_all.main() is test_epa_backend's."""
    commands, out = b58h_commands(text)
    fenced = set()
    for where, tokens in commands:
        kind, probs = b58h_line(tokens, protocol=protocol)
        out += [f"the {where} command {' '.join(tokens)!r}: {p}" for p in probs]
        if kind is not None and not probs and where == "fenced":
            fenced.add(kind)
    out += [f"no fenced {kind} line (row 147 (3); the sheet 17's 10.1)" for kind in B58H_LINES if kind not in fenced]
    return out


# ================================================================== the command line
def _print_trace(record):
    print(f"{'step':>4}  {'in the test':<44} {'n':>4} {'total s at n':>14}  event")
    for i, s in enumerate(record["trace"], 1):
        total = "" if s["total_s"] is None else f"{s['total_s']:.0f}"
        print(f"{i:>4}  {' '.join(s['in_test']):<44} {str(s['n']):>4} {total:>14}  {s['event']}")
    print(f"n = {record['n']}; in the test: {record['in_test']}; total {record['total_s']} s of W = {W_S} s; "
          f"slack {record['slack_s']} s")
    for e, v in (record["seconds_at_n"] or {}).items():
        print(f"  {e:<12} {v:.0f} s at n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("command", choices=("compute", "write", "check"))
    a = ap.parse_args(argv)
    import engines
    try:
        summary = engines.committed_record(REPO, engines.VALIDATION_SUMMARY_REL)
        live = live_plants(engines.trainable_from(summary, None))
        if a.command == "compute":
            print(json.dumps(compute(REPO, live=live), indent=1))
        elif a.command == "write":
            sha = write(REPO, live=live)
            with open(record_path(REPO), encoding="utf-8") as fh:
                _print_trace(json.load(fh))
            print(f"wrote {engines.BACKEND_REL} (sha_text {sha})")
        else:
            diff = check(REPO, live=live)
            print(json.dumps(diff, indent=1))
            if diff:
                return 2
    except (Refused, ValueError) as e:
        print("REFUSED:", file=sys.stderr)
        for p in getattr(e, "problems", [str(e)]):
            print(f"  - {p}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
