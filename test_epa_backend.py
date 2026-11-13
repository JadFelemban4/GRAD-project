"""test_epa_backend.py -- epa_backend.py, commit Ta (ORDER step 17b; the interface sheet,
docs/build_step_2/INTERFACES.md, section 10.1): row 114's schedule as rows 135 and 136 fix it, on SYNTHETIC
rates, attempts and repositories.

    python -B test_epa_backend.py      not timed (ASSUMED a few minutes: Scans imports train.py's torch for
                                       test_engine_threading's scans); exit code 0 when all pass

Every class but Scans, Preregistration, PreregistrationB58H and LiveRecord is test_epa_fixtures.Guarded
(forbid_real_data) and passes `live` itself: no real B1 file, no plant run, no EPA table. The B1 attempts are
built in benchmark_training.py's own layout, recommendation.configurations by its own `configurations`, and read
through the JSON text as B1's are. Every refusal is matched by its text, so that another refusal cannot stand in
for it (mistake 12).

  Formula       hand arithmetic at exact boundaries (125 and 124.99 steps/s at N 20; 133.34 and 133.33 at N 16),
                exact fractions where the two-decimal per-run print would move n, n_max the largest, SEED_LIMIT
                refused, and agreement with benchmark_training.seeds_in_window for four identical engines
  ApplyRule     row 136's order: the B58 and the Ford below 20 drop the Ford with 12.5's reason and n null, the
                control at n >= 20 keeps it (mistake 12); four engines below 20, the Honda then the Mazda, n
                recomputed and traced after each; the order is DROP_ORDER's whatever each engine costs; every EPA
                engine dropped by Run 2 gives n null with no schedule drop and no n asked of the B58 alone
  Classify      one valid attempt is the measurement, exact; each of row 135 (4)'s outcomes from one mutation of
                it, (a) crashes, (b) operator faults, (c) a fallback on CUDA, a defect and a stop on the CPU; an
                outcome no row names is refused; the crash words are benchmark_training.row_verdict's own
  Series        bench_attempts and read_series in a SYNTHETIC git repository: a crash, then the measurement; an
                attempt after a measurement; a series that ends in a crash; a missing k; an attempt whose cost
                files changed is superseded, the control (a change outside them) is not; no B0 record is a fault;
                a CPU series beside the CPU protocol, each file named; a git_head this clone lacks (fetch it)
  Protocol      PROTOCOL as row 135 types it (step 3 on Jad's PC; the lock); the plan classify expects is the one
                the frozen script's own main() writes for the runbook's B1 command; the protocol commit is C1b,
                HEAD descends from it and benchmark_training.py is unchanged since; a wrong commit is refused
  RunbookNames  the runbook at the protocol commit, and in this tree (which B0 checks out), names what Ta reads
                (ATTEMPT, CPU_ATTEMPT, B0_RECORD, the k loop over $B1OUT and results/benchmarks, B5's globs);
                each renamed pattern fails with its own problem (the control)
  Record        compute, write and check on a SYNTHETIC repository, through engines' reader (P2, the sheet 6.3):
                12.5's layout, a Run-2 drop and a schedule drop with their reasons, n null when the schedule
                leaves no EPA engine (the failed schedule) and when Run 2 left none (the failed validations, with
                no schedule drop: Run 2's outcome), written once, check [] and then the field named after an
                edit, the refusals; B1 reading 'defect' or 'stop' refused with row 135 (4)(c)'s text (row 146
                (4)); check [] on PR-B's staged tree, and each change that can move the record refused by name
  CostFiles     cost_files at this tree: epa_fit.py inside it (row 146 (3)), the plant, the specs, the lock and
                the roads record; files that time nothing outside it (the control)
  PreregistrationCommands   the section-11 command check on SYNTHETIC text, every flag and its control
  LivePlants    the one plant_fingerprint call: both backends 'cycle', preview_h_s None, reward_knock False
  Cli           no option is taken: --n, --engines, --window, --rate, --runs, --device and --force exit 2
  Hygiene       the constants against their owners; P's names; no hashed module imports this one (and the
                check can fail); no torch and no file opened at import; public names only; redact (12 digits)
  Scans         unguarded: test_engine_threading's scan_source and scan_names on this module and its test
  PreregistrationState  the live test's verdict on SYNTHETIC states: the file present beside n null fails (the
                control of row 136 (1)), and so do an uncommitted file, a removed one and a file before the record
  LiveStates    the three live tests' skip-or-fail decisions on a SYNTHETIC repository: committed_state reads
                absent, uncommitted, committed and removed; PR-B and the record skip only before their commit, and
                fail when present uncommitted, removed after it, or (PR-B) added by more than one commit
  Preregistration   unguarded: skipped until results/PREREGISTRATION_4E.md is committed, a failure if skipped
                after; absent when the committed record's n is null, and Run 2 left no EPA engine
  PreregistrationB58H   unguarded (row 146 (5); the sheet 17's 10.1): row 147 (3)'s two commands, as SYNTHETIC
                text, pass b58h_problems and train_all.main() in-process (sys.argv patched, train_all.commands a
                stub raising a sentinel with the parsed arguments and check_four_engine's record); one flag
                changed fails (the control), and so do the lines train_all.main() refuses, by their text; what
                a command is (its program, or --engine after it; a pipe ends it; a mention is not one); the
                committed results/PREREGISTRATION_B58H.md is checked the same way, skipped until it is committed
                and a failure if skipped after
  LiveRecord    unguarded: skipped until results/EPA_BACKEND.json is committed, a failure if removed after; then
                check gives []

This tree holds the plant commit P (fingerprint schema 4; engines' reader of the records, the sheet 6.3), so no
test skips for P's absence; Hygiene fails if P's names are missing.
"""
import ast
import contextlib
import copy
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from decimal import Decimal
from fractions import Fraction
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import benchmark_training as B  # noqa: E402
import engines  # noqa: E402
import epa_backend as EB  # noqa: E402
import epa_roads as ER  # noqa: E402
import fingerprint as FP  # noqa: E402
import test_epa_fixtures as fx  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402
from thresholds import common  # noqa: E402

ALL = ("b58", "ford_27tt", "honda_l15b7", "mazda_25t")   # engines.known() order
PLANT = {"plant_sha": "a" * 16, "derived_sha": "d" * 16, "engine": "x/y", "engine_sha": "e" * 16,
         "backend": "cycle", "reward_knock": False}       # a SYNTHETIC plant block, PLANT_KEYS key for key
W = EB.W_S


def rates(lower, N, ids=ALL):
    return {e: (Fraction(Decimal(str(lower))), N) for e in ids}


def plant_of(engine):
    return dict(PLANT, engine=f"{engine}/car")


def live_for(ids):
    return {e: plant_of(e) for e in ids}


def synthetic_doc(engine_id, *, protocol=None, lowers=("106.19", "110.1"), git_head="abc1234", host="dev1",
                  trainable=("b58",)):
    """A finished B1 attempt of `engine_id` in benchmark_training.py's layout (main's result dict): plan, machine,
    code, determinism, the rows at N (one per repeat) and recommendation.configurations by benchmark_training's
    own configurations. SYNTHETIC numbers, the same for every engine but its plant block (plant_of). Its
    parameter is an engine id, not a plant record (test_engine_threading.RECORD_PARAMS)."""
    p = protocol or EB.PROTOCOL
    dev, N, S, R = p["device"], p["runs"], p["steps_per_run"], p["repeats"]
    plant = plant_of(engine_id)
    rows = []
    for rep, lo in enumerate((lowers * R)[:R]):
        row = dict(device=dev, runs=N, seeds=list(range(N)), steps_per_run=S, buffer=B.PROD_BUFFER,
                   background_cpu_pct=1.0, loaded=False, wall_s=400.0, exit_codes=[0] * N, ok=True, why=[],
                   launcher_steps_per_s=float(lo) - 1, ram=dict(used_gb=3.0, avail_before_gb=20.0),
                   plant=dict(plant), upper_steps_per_s=float(lo) + 5, lower_steps_per_s=float(lo), overlap=0.95,
                   stagger_s=1.0, per_run_min=8.0, per_run_max=9.0, steady=True, repeat=rep, repeats_planned=R,
                   production_gb=3.0, fits=True)
        if dev == "cuda" and N >= 2:
            row["seed0_twice"] = dict(identical=True, n_differences=0, first=[])
        rows.append(row)
    return dict(benchmark="benchmark_training.py", asked_by="Ghassan, 21 October 2026", status="finished",
                date="2026-11-12T10:00:00",
                code=dict(git_head=git_head, git_dirty=False, benchmark_sha="b" * 16, train_sha="t" * 16),
                machine=dict(host=host, python=p["python"], torch=p["torch"], torch_cuda=None,
                             engines_known=list(ALL), engines_trainable=list(trainable)),
                devices_asked=[dev], devices=[dev], notes=[], plan=EB.expected_plan(engine_id, p), parts={},
                determinism={dev: dict(device=dev, identical=True, steps=B.DET_STEPS, n_differences=0, first=[],
                                       compared=dict(tensors=10, record_fields=47, counters=8))},
                concurrency=rows,
                recommendation=dict(device=None, runs=None, clear=None, configurations=B.configurations(rows)))


def exact(doc):
    """The attempt as epa_backend reads B1's files: through the JSON text, every float a Decimal."""
    return json.loads(json.dumps(doc), parse_float=Decimal)


def b0_of(doc):
    return dict(doc["code"], host=doc["machine"]["host"])


def pr_text(engines_n, *, device="cpu", jobs=12, extra="", blind=False):
    ids, n = engines_n
    blocks = []
    for e in ids:
        blocks.append("```bash\n"
                      f"python train_all.py --engine {e} --device {device} --road four_engine --dt 1 --third-arm \\\n"
                      "    --recipe29 --roads-record results/EPA_ROADS/roads.json --reward-knock out \\\n"
                      f"    --seeds 0-{n - 1} \\\n"
                      f"    --steps 450000 --jobs {jobs} --no-resume --out runs/four_engine_dt1_{e}"
                      + (" --blind-per-h" if blind else "") + extra + "\n```\n")
    return "# PREREGISTRATION (SYNTHETIC)\n\n" + "\n".join(blocks)


def committed_state(rel, root=HERE):
    """`rel`'s state in the repository `root`: 'committed' (the working file is HEAD's blob); 'absent' (neither in
    the tree nor at HEAD, and never in HEAD's history: not written yet); 'removed' (absent now, and in HEAD's
    history: committed, then deleted and the deletion committed); 'uncommitted' otherwise (untracked, staged,
    modified, or deleted and not committed). 'removed' is never 'absent', so that a live test cannot skip after the
    commit (the sheet 10.1: "skipped until ... committed, and a failure if skipped after"). LiveStates is its test."""
    import epa_freeze
    if epa_freeze.committed_at_head(rel, root=root):
        return "committed"
    if not os.path.exists(os.path.join(root, *rel.split("/"))) and epa_freeze.head_blob(rel, root=root) is None:
        return "removed" if fx.git(root, "log", "--format=%H", "HEAD", "--", rel) else "absent"
    return "uncommitted"


STATE_WHY = {"uncommitted": "present and not committed (untracked, staged, modified, or deleted and not committed)",
             "removed": "removed after its commit (absent now, in HEAD's history)"}


def redact(text):
    """`text` with every run of 12 or more digits replaced: a refusal of train_all.py can quote roads.json's
    roads_seed or a revealed value (four_engine_roads.py:375-377), and none is stored or printed here."""
    return re.sub(r"[0-9]{12,}", "<integer>", text)


def preregistration_verdict(pr, rec, load_record, load_text):
    """The live Preregistration test's verdict from the states of the preregistration (`pr`) and the backend
    record (`rec`), each committed_state's: ('fail', why), ('skip', why) or ('pass', None). The record and the
    text are read through load_record() and load_text() only when their states say they are committed. With n
    null the file must be absent (row 136 (1); the sheet 10.1), and PreregistrationState is the control."""
    if pr == "uncommitted":
        return "fail", f"{EB.PREREGISTRATION_REL} is present and not committed"
    if pr == "removed":
        return "fail", f"{EB.PREREGISTRATION_REL} is {STATE_WHY['removed']}"
    if rec == "uncommitted":
        return "fail", "the backend record is present and not committed"
    if rec == "removed":
        return "fail", f"the backend record is {STATE_WHY['removed']}: it is written once and never removed (row 114)"
    if rec == "absent":
        if pr != "absent":
            return "fail", "the preregistration follows the backend record (Tb; the sheet section 0)"
        return "skip", "neither the backend record nor the preregistration is committed"
    record = load_record()
    if record["n"] is None:
        if pr != "absent":
            return "fail", "n is null: no EPA engine survives, so the preregistration is never written (row 136 (1))"
        return "pass", None
    if pr == "absent":
        return "skip", f"{EB.PREREGISTRATION_REL} is not committed yet (ORDER step 20)"
    probs = EB.preregistration_problems(load_text(), record, protocol=EB.preregistration_protocol(record),
                                        arms=EB.ARMS)
    return ("fail", "; ".join(probs)) if probs else ("pass", None)


# ----------------------------------------------------------------------------------------- PR-B's commands
# Row 147 (3)'s two commands, word for word: the training command as the row quotes it, and the pilot's, "the
# same with `--ratios 1.5 --seeds 2000-2004 --out runs/b58h_pilot_dt1`". Typed here from the row, so that
# EB.B58H_LINES and EB.b58h_flags are checked against the row and not against themselves (mistake 12)
TRAINING_147 = ("train_all.py --engine b58 --device cpu --road four_engine --dt 1 --third-arm --recipe29 "
                "--roads-record results/EPA_ROADS/roads.json --reward-knock out --seeds 0-19 --steps 450000 "
                "--jobs 12 --no-resume --out runs/b58h_dt1")
PILOT_147 = ("train_all.py --engine b58 --device cpu --road four_engine --dt 1 --third-arm --recipe29 "
             "--roads-record results/EPA_ROADS/roads.json --reward-knock out --ratios 1.5 --seeds 2000-2004 "
             "--steps 450000 --jobs 12 --no-resume --out runs/b58h_pilot_dt1")


def b58h_text(training=TRAINING_147, pilot=PILOT_147, *, prose=""):
    """A SYNTHETIC PR-B: a sentence quoting row 147 (3)'s training command in a code span, beside a mention of
    `train_all.py --recipe29` (no engine: not a command), then each command in a fenced block of its own, split
    over two lines by a backslash as a shell block would be (a command given as None is left out), then `prose`."""
    def fence(line):
        words = line.split(" ")
        return "```bash\npython " + " ".join(words[:9]) + " \\\n    " + " ".join(words[9:]) + "\n```\n"
    return ("# PREREGISTRATION_B58H (SYNTHETIC)\n\n"
            "Decision 29's recipe (`train_all.py --recipe29`) on row 116's training road. The training command is "
            f"`{TRAINING_147}`.\n\n"
            + (fence(training) if training else "") + "\n" + (fence(pilot) if pilot else "") + prose)


class Sentinel(Exception):
    """Raised by the stand-in for train_all.commands: main() got past its parser, seeds() and check_four_engine.
    It carries the parsed arguments and the record check_four_engine returned."""

    def __init__(self, a, record):
        super().__init__("train_all.commands was reached")
        self.a, self.record = a, record


TRAIN_ALL_RUNS = {}


def run_train_all(tokens):
    """train_all.main() in-process on `tokens` (the arguments after train_all.py), from the repository root, with
    sys.argv patched and train_all.commands replaced by a stand-in that raises Sentinel, so that main() runs its
    own parser, seeds() and check_four_engine and stops before any directory or run exists (commands comes
    before os.makedirs in main); train_all.subprocess is a stand-in whose Popen fails, should the stand-in ever
    be passed by. ('passed', the parsed arguments, the record) or ('refused', the refusal's text, redacted).
    Memoised by the tokens, since main() reads the committed roads.json (about 13 MB) each time. Nothing is
    printed."""
    key = tuple(tokens)
    if key not in TRAIN_ALL_RUNS:
        import train_all

        def stand_in(a, record):
            raise Sentinel(a, record)

        def no_run(*args, **kw):
            raise AssertionError("train_all.main() went past commands: no run may start here")
        out, err = io.StringIO(), io.StringIO()
        try:
            with mock.patch.object(sys, "argv", ["train_all.py", *key]), \
                    mock.patch.object(train_all, "commands", stand_in), \
                    mock.patch.object(train_all, "subprocess",
                                      types.SimpleNamespace(Popen=no_run, STDOUT=subprocess.STDOUT)), \
                    contextlib.chdir(HERE), contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
                train_all.main()
        except Sentinel as s:
            TRAIN_ALL_RUNS[key] = ("passed", s.a, s.record)
        except SystemExit as e:
            TRAIN_ALL_RUNS[key] = ("refused", redact(e.code if isinstance(e.code, str) else err.getvalue().strip()))
        else:
            raise AssertionError("train_all.main() returned without reaching commands")
    return TRAIN_ALL_RUNS[key]


def parsed_problems(a, record, kind):
    """Why what train_all.main() parsed from a PR-B line (`a`), with the record check_four_engine returned, is not
    row 147 (3)'s `kind` line, or []: the flag list's values (EB.PROTOCOL, EB.B58H_ENGINE, EB.PROD_STEPS), the
    line's seeds, folder and ratios (EB.B58H_LINES), the three flags set and --keep-buffer off; the REAL committed
    roads record; and the runs train_all would start (train_all.arms): one sighted arm at each ratio the record
    holds and the blinded arm (EB.ARMS) for the training, the blinded arm and r = 1.5 for the pilot. The record is
    never printed: it holds roads_seed."""
    import train_all
    p, spec = EB.PROTOCOL, EB.B58H_LINES[kind]
    want = dict(engine=EB.B58H_ENGINE, device=p["device"], road=p["road"], dt=p["dt"],
                roads_record=p["roads_record"], reward_knock=p["reward_knock"], steps=EB.PROD_STEPS, jobs=p["runs"],
                third_arm=True, recipe29=True, no_resume=True, keep_buffer=False,
                seeds=train_all.seeds([spec["--seeds"]]), out=spec["--out"],
                ratios=[float(spec["--ratios"])] if "--ratios" in spec else None)
    out = [f"{k} {getattr(a, k, '(absent)')!r}, not {v!r}" for k, v in want.items() if getattr(a, k, None) != v]
    if getattr(a, "blind_per_h", False):
        out.append("blind_per_h is set: never (row 135 (5))")
    if not isinstance(record, dict) or record.get("seed_kind") != "REAL":
        return out + ["check_four_engine returned no REAL roads record"]
    if os.path.normcase(record["path"]) != os.path.normcase(os.path.join(HERE, *ER.ROADS_REL.split("/"))):
        return out + [f"the roads record read is not this repository's {ER.ROADS_REL}"]
    held = [float(r) for r in record["ratios"]]
    ratios = train_all.ratios(a, record)
    if kind == "training" and (ratios != held or len(held) + 1 != EB.ARMS):
        out.append(f"the training's sighted ratios are {ratios}, not every ratio the record holds, {held}, "
                   f"with the blinded arm {EB.ARMS} arms")
    if kind == "pilot" and ratios != want["ratios"]:
        out.append(f"the pilot's sighted ratios are {ratios}, not {want['ratios']}")
    runs = train_all.arms(a, record)
    blinded = [s for s, sighted, _ in runs if not sighted]
    if len(runs) != (len(ratios) + 1) * len(want["seeds"]) or blinded != want["seeds"]:
        out.append(f"train_all would start {len(runs)} runs, not one blinded and {len(ratios)} sighted a seed")
    return out


def b58h_all_problems(text):
    """EB.b58h_problems on `text`, then every distinct command it finds through train_all.main() in-process
    (run_train_all), what it parsed checked by parsed_problems: [] when PR-B states row 147 (3)'s two commands and
    train_all.py takes each as the row means it."""
    probs = EB.b58h_problems(text, protocol=EB.PROTOCOL)
    commands, _ = EB.b58h_commands(text)
    for tokens in sorted({tuple(t) for _, t in commands}):
        res = run_train_all(tokens)
        kind = EB.b58h_kind(list(tokens))
        if res[0] == "refused":
            probs.append(f"train_all.main() refuses {' '.join(tokens)!r}: {res[1]}")
        elif kind is not None:
            probs += [f"train_all.main() parsed {' '.join(tokens)!r}: {p}"
                      for p in parsed_problems(res[1], res[2], kind)]
    return probs


def b58h_verdict(root=HERE, problems_of=None):
    """The live PreregistrationB58H test's verdict in the repository `root`: ('skip', why) while PR-B was never
    committed; ('fail', why) when it is present and not committed, removed after its commit, added by more than one
    commit (T* is the one commit that adds it, row 146 (6)), or when problems_of(its text) (b58h_all_problems by
    default) finds a problem; ('pass', None) otherwise. LiveStates is its test, on a SYNTHETIC repository."""
    rel = EB.B58H_PREREGISTRATION_REL
    state = committed_state(rel, root)
    if state == "absent":
        return "skip", f"{rel} is not committed yet (PR-B, ORDER step 20)"
    if state != "committed":
        return "fail", f"{rel} is {STATE_WHY[state]}"
    adds = fx.git(root, "log", "--diff-filter=A", "--format=%H", "HEAD", "--", rel).split()
    if len(adds) != 1:
        return "fail", f"T* is the one commit that adds {rel} (row 146 (6)): {len(adds)} commits add it"
    with open(os.path.join(root, *rel.split("/")), encoding="utf-8") as fh:
        probs = (problems_of or b58h_all_problems)(fh.read())
    return ("fail", redact("; ".join(probs))) if probs else ("pass", None)


def live_check(root):
    """EB.check in `root` with the live plants of the engines its committed summary.json leaves (the CLI's own)."""
    summary = engines.committed_record(root, engines.VALIDATION_SUMMARY_REL)
    return EB.check(root, live=EB.live_plants(engines.trainable_from(summary, None)))


def live_record_verdict(root=HERE, check_of=None):
    """The live LiveRecord test's verdict in the repository `root` (the sheet 10.1: skipped until the record is
    committed, and a failure if skipped after): ('skip', why) while results/EPA_BACKEND.json was never committed;
    ('fail', why) when it is present and not committed, removed after its commit, or when check_of(root)
    (live_check by default) finds a difference; ('pass', None) otherwise. LiveStates is its test."""
    rel = engines.BACKEND_REL
    state = committed_state(rel, root)
    if state == "absent":
        return "skip", f"{rel} is not committed: ORDER step 19 has not run"
    if state != "committed":
        return "fail", f"{rel} is {STATE_WHY[state]}"
    diff = (check_of or live_check)(root)
    return ("fail", redact(f"check finds differences: {diff}")) if diff else ("pass", None)


# =====================================================================================================
class Formula(Guarded):
    def test_hand_arithmetic(self):
        """ARMS 3, PROD_STEPS 450 000 (arithmetic by hand). At 125 steps/s and N 20 a wave is 72 000 s, 20 seeds
        take 3 waves an engine, and four engines take 864 000 s = W: n = 20, the boundary fits. 124.99 gives 13.
        At 82.4 and N 23, row 134's "n = 7 at 23 at once"; at 106.19 and N 12, step 3's "at most 16 seeds per arm
        fit the 10-day window" (both as SYNTHETIC rates of four engines)."""
        self.assertEqual(EB.wave_seconds(Fraction(125), 20), 72_000)
        self.assertEqual(EB.engine_seconds(20, Fraction(125), 20), 216_000)
        self.assertEqual(EB.engine_seconds(21, Fraction(125), 20), 288_000)
        self.assertEqual(EB.total_seconds(20, rates(125, 20)), W)
        for lower, N, n in ((125, 20, 20), ("124.99", 20, 13), ("82.4", 23, 7), ("106.19", 12, 16)):
            with self.subTest(lower=lower, N=N):
                self.assertEqual(EB.n_max(rates(lower, N), W), n)

    def test_exact_arithmetic_not_float(self):
        """lower_min is exact (row 135 (3)): 133.34 and 133.33 at N 16 fall on either side of W (n 21 and 16),
        and the benchmark's two-decimal per-run print (8.33 steps/s for 133.34 / 16) would give 16 where the
        exact rate gives 21. A float is refused."""
        self.assertEqual(EB.n_max(rates("133.34", 16), W), 21)
        self.assertEqual(EB.n_max(rates("133.33", 16), W), 16)
        printed = B.schedule(133.34, 16, 20)["per_run_steps_per_s"]
        self.assertEqual(printed, 8.33)
        self.assertEqual(EB.n_max(rates(Decimal("8.33") * 16, 16), W), 16)
        self.assertIsInstance(EB.engine_seconds(3, Fraction(13334, 100), 16), Fraction)
        for bad in (133.34, True, "133.34"):
            with self.subTest(bad=bad):
                with self.assertRaises(TypeError) as e:
                    EB.wave_seconds(bad, 16)
                self.assertIn("lower_min must be exact", str(e.exception))

    def test_n_max_is_the_largest_and_refused_at_the_seed_limit(self):
        rng = random.Random(1114)
        for _ in range(300):
            ids = ALL[:rng.randint(1, 4)]
            rs = {e: (Fraction(rng.randint(2000, 40000), 100), rng.choice((6, 12, 16, 23))) for e in ids}
            totals = [EB.total_seconds(n, rs) for n in range(60)]
            self.assertEqual(totals, sorted(totals))
            n = EB.n_max(rs, W)
            self.assertLessEqual(EB.total_seconds(n, rs), W)
            self.assertGreater(EB.total_seconds(n + 1, rs), W)
        self.assertEqual(EB.n_max(rates("0.5", 12), W), 0)
        with self.assertRaises(EB.Refused) as e:
            EB.n_max(rates(10 ** 7, 12), W)
        self.assertIn("SEED_LIMIT", str(e.exception))

    def test_four_identical_engines_agree_with_the_benchmarks_seeds_in_window(self):
        """benchmark_training.seeds_in_window counts ENGINES = 4 engines at one rate, in floating point: off its
        boundaries, n_max over four identical engines gives its answer (and its selftest's pins)."""
        for lower in (60.37, 82.4, 99.91, 106.19, 133.34, 151.7):
            for N in (6, 12, 16, 23):
                for days in (7.3, 10, 12.5):
                    with self.subTest(lower=lower, N=N, days=days):
                        w = Fraction(Decimal(str(days))) * 86400
                        n = EB.n_max(rates(lower, N), w)
                        self.assertNotEqual(EB.total_seconds(n, rates(lower, N)), w)   # off the boundary
                        self.assertEqual(n, B.seeds_in_window(lower, N, days))
        for lower, N, days, n in ((100.0, 20, 12.5, 20), (100.0, 20, 12.4, 13), (100.0, 20, 1.0, 0)):
            self.assertEqual(EB.n_max(rates(lower, N), Fraction(Decimal(str(days))) * 86400), n)
            self.assertEqual(B.seeds_in_window(lower, N, days), n)


# =====================================================================================================
class ApplyRule(Guarded):
    def test_the_b58_and_the_ford_below_20_drop_the_ford_and_n_is_null(self):
        """Row 136 (1): the Ford leaves only when it and the B58 cannot reach n >= 20, and then no EPA engine is
        left: n null, in_test ['b58'], the Ford's reason 12.5's. The control (mistake 12): the same pair at n >= 20
        keeps the Ford and gives that n."""
        r = EB.apply_rule(["b58", "ford_27tt"], rates(50, 12, ("b58", "ford_27tt")), w_s=W)
        self.assertIsNone(r["n"])
        self.assertEqual(r["in_test"], ["b58"])
        self.assertEqual(r["engines"]["ford_27tt"],
                         {"drop": True, "backend": None, "reason": "rows 114 and 136: the schedule (n 16 -> null)"})
        self.assertEqual(r["engines"]["b58"], {"drop": False, "backend": "cycle", "reason": None})
        self.assertEqual([(s["in_test"], s["n"]) for s in r["trace"]], [(["b58", "ford_27tt"], 16), (["b58"], None)])
        control = EB.apply_rule(["b58", "ford_27tt"], rates(80, 12, ("b58", "ford_27tt")), w_s=W)
        self.assertEqual(control["n"], 24)
        self.assertEqual(control["in_test"], ["b58", "ford_27tt"])
        self.assertFalse(control["engines"]["ford_27tt"]["drop"])
        self.assertEqual(len(control["trace"]), 1)

    def test_four_engines_below_20_the_honda_then_the_mazda(self):
        r = EB.apply_rule(list(ALL), rates(80, 12), w_s=W)
        self.assertEqual(r["n"], 24)
        self.assertEqual(r["in_test"], ["b58", "ford_27tt"])
        self.assertEqual(r["engines"]["honda_l15b7"]["reason"], EB.schedule_reason(12, 16))
        self.assertEqual(r["engines"]["mazda_25t"]["reason"], "rows 114 and 136: the schedule (n 16 -> 24)")
        self.assertEqual([(len(s["in_test"]), s["n"]) for s in r["trace"]], [(4, 12), (3, 16), (2, 24)])
        self.assertEqual([s["total_s"] for s in r["trace"]],
                         [float(EB.total_seconds(n, rates(80, 12, ids))) for n, ids in
                          ((12, ALL), (16, ("b58", "ford_27tt", "mazda_25t")), (24, ("b58", "ford_27tt")))])
        self.assertTrue(all(s["total_s"] <= W for s in r["trace"]))

    def test_the_order_is_drop_orders_whatever_each_engine_costs(self):
        """The Honda leaves first though it is the cheapest engine here, and the Ford last though it costs most."""
        rs = {"b58": (Fraction(100), 12), "honda_l15b7": (Fraction(400), 12), "mazda_25t": (Fraction(100), 12),
              "ford_27tt": (Fraction(40), 12)}
        r = EB.apply_rule(["b58", "ford_27tt", "honda_l15b7", "mazda_25t"], rs, w_s=W)
        dropped = [s["event"].split()[0] for s in r["trace"][:-1]]
        self.assertEqual(dropped, list(EB.DROP_ORDER[:len(dropped)]))
        self.assertEqual(dropped[0], "honda_l15b7")

    def test_every_epa_engine_dropped_by_run_2_gives_n_null_with_no_schedule_drop(self):
        """Run 2's outcome (section Q; row 136 (1)): the B58 alone in the test, so n is null and in_test ['b58'],
        with no schedule drop and no n asked of the B58 alone (at a rate where it would pass SEED_LIMIT nothing
        is refused, at a rate where it would reach 20 n is null all the same). The control is the first test: an
        EPA engine in the test is given an n."""
        for lower in (10 ** 7, 150, 1):
            with self.subTest(lower=lower):
                r = EB.apply_rule(["b58"], rates(lower, 12, ("b58",)), w_s=W)
                self.assertIsNone(r["n"])
                self.assertEqual(r["in_test"], ["b58"])
                self.assertEqual(r["engines"], {"b58": {"drop": False, "backend": "cycle", "reason": None}})
                self.assertEqual([(s["in_test"], s["n"]) for s in r["trace"]], [(["b58"], None)])
                self.assertIn("no EPA engine is left", r["trace"][0]["event"])

    def test_its_refusals(self):
        for in_test, rs, words in ((["ford_27tt"], rates(80, 12, ("ford_27tt",)), "b58 is not in the test"),
                                   (["b58", "ford_27tt"], rates(80, 12, ("b58",)), "rates for ['b58']"),
                                   (["b58", "other"], rates(80, 12, ("b58", "other")),
                                    "['other'] are neither the B58 nor in DROP_ORDER")):
            with self.subTest(in_test=in_test):
                with self.assertRaises(EB.Refused) as e:
                    EB.apply_rule(in_test, rs, w_s=W)
                self.assertIn(words, str(e.exception))


# =====================================================================================================
class Classify(Guarded):
    TB = ("b58",)

    def classify(self, doc, *, protocol=None, b0="same", script=None, live=None):
        """The B58's attempt `doc`, classified as B1's is read: through the JSON text."""
        p = protocol or EB.PROTOCOL
        doc = exact(doc)
        return EB.classify(doc, self.TB[0], p, live or live_for(ALL), b0_of(doc) if b0 == "same" else b0,
                           trainable_before=self.TB, protocol_script=script)

    def test_a_valid_attempt_is_the_measurement_exactly(self):
        kind, lower = self.classify(synthetic_doc("b58"))
        self.assertEqual(kind, "measurement")
        self.assertEqual(lower, Fraction(10619, 100))
        self.assertIsInstance(lower, Fraction)

    def test_a_crash(self):
        """Row 135 (4)(a), each from one change of the valid attempt."""
        cases = {}
        for status in ("running", "interrupted (Ctrl+C)", "failed: the plant step"):
            d = synthetic_doc("b58")
            d["status"] = status
            cases[f"status {status}"] = d
        d = synthetic_doc("b58")
        d["determinism"]["cpu"].update(identical=None, why="run 0: timed out")
        cases["seed 0 not trained twice"] = d
        for why in (["timed out after 900 s"], ["exit codes [1, 0]"], ["11 of 12 runs finished"], ["error: OSError()"]):
            d = synthetic_doc("b58")
            d["concurrency"][1].update(ok=False, why=why)
            cases[why[0]] = d
        d = synthetic_doc("b58")
        del d["concurrency"][1]
        cases["one repeat of two"] = d
        for name, doc in cases.items():
            with self.subTest(name):
                kind, why = self.classify(doc)
                self.assertEqual(kind, "crash")
                self.assertTrue(why.startswith("(a)"), why)

    def test_an_operator_fault_is_a_crash(self):
        """Row 135 (4)(b), each from one change; the valid attempt is the control."""
        def changed(fn):
            d = synthetic_doc("b58")
            fn(d)
            return d
        cases = {
            "git_dirty True": (changed(lambda d: d["code"].update(git_dirty=True)), {}),
            "git_dirty None": (changed(lambda d: d["code"].update(git_dirty=None)), {}),
            "devices asked": (changed(lambda d: d.update(devices_asked=["cuda"])), {}),
            "torch": (changed(lambda d: d["machine"].update(torch="2.14.0+cu130")), {}),
            "python": (changed(lambda d: d["machine"].update(python="3.13.15")), {}),
            "engines_trainable": (changed(lambda d: d["machine"].update(engines_trainable=["b58", "ford_27tt"])), {}),
            "the script": (synthetic_doc("b58"), dict(script="at abc1234 it differs")),
            "no B0 record": (synthetic_doc("b58"), dict(b0=None)),
            "B0 host": (synthetic_doc("b58"), dict(b0=dict(b0_of(synthetic_doc("b58")), host="laptop"))),
            "B0 benchmark_sha": (synthetic_doc("b58"), dict(b0=dict(b0_of(synthetic_doc("b58")), benchmark_sha="x"))),
            "B0 train_sha": (synthetic_doc("b58"), dict(b0=dict(b0_of(synthetic_doc("b58")), train_sha="x"))),
            "B0 dirty": (synthetic_doc("b58"), dict(b0=dict(b0_of(synthetic_doc("b58")), git_dirty=True))),
            "a row on another device": (changed(lambda d: d["concurrency"][0].update(ok=False, why=["trained on cpu"])),
                                        {}),
            "two plants in a row": (changed(lambda d: d["concurrency"][0].update(
                ok=False, why=["its runs trained on more than one plant (config.json's ...)"])), {}),
            "two plants across rows": (changed(lambda d: d["concurrency"][1]["plant"].update(plant_sha="f" * 16)),
                                       {}),
            "reward_knock True": (changed(lambda d: [r["plant"].update(reward_knock=True) for r in d["concurrency"]]),
                                  {}),
            "reward_knock None (before P)": (changed(lambda d: [r["plant"].update(reward_knock=None)
                                                                for r in d["concurrency"]]), {}),
            "a table backend": (changed(lambda d: [r["plant"].update(backend="table:0") for r in d["concurrency"]]),
                                {}),
            "not this tree's plant": (synthetic_doc("b58"), dict(live=dict(live_for(ALL), b58=dict(PLANT,
                                                                                                plant_sha="0" * 16)))),
        }
        plan_changes = dict(runs_grid=[11], steps_per_run=1500, repeats=1, reward_knock="in", roads_record=None,
                            scored_share=False, engine="mazda_25t", road="extremes", smoke_test=True,
                            no_determinism=True, window_days=10.0, buffer=100_000, det_steps=900, dt=0.5, extra=1)
        for k, v in plan_changes.items():
            cases[f"plan {k}"] = (changed(lambda d, k=k, v=v: d["plan"].update({k: v})), {})
        cases["plan without a key"] = (changed(lambda d: d["plan"].pop("scored_share")), {})
        for name, (doc, kw) in cases.items():
            with self.subTest(name):
                kind, why = self.classify(doc, **kw)
                self.assertEqual(kind, "crash")
                self.assertTrue(why.startswith("(b)"), why)
        self.assertEqual(self.classify(synthetic_doc("b58"))[0], "measurement")

    def test_the_cpus_defect_and_stop(self):
        d = synthetic_doc("b58")
        d["determinism"]["cpu"].update(identical=False, n_differences=3, first=["weights a"])
        self.assertEqual(self.classify(d)[0], "defect")
        d = synthetic_doc("b58")
        d["concurrency"][0]["fits"] = False
        d["recommendation"]["configurations"] = B.configurations(d["concurrency"])
        self.assertEqual(self.classify(d)[0], "stop")
        d["concurrency"][0]["fits"] = None             # not known is not False (configurations: fits_known)
        d["recommendation"]["configurations"] = B.configurations(d["concurrency"])
        self.assertEqual(self.classify(d)[0], "measurement")

    def test_cudas_fallback(self):
        """Row 135 (4)(c) on CUDA: identical False, fits False at N and seed0_twice False each fall back."""
        cuda = dict(EB.PROTOCOL, device="cuda", torch="2.14.0+cu130")
        self.assertEqual(self.classify(synthetic_doc("b58", protocol=cuda), protocol=cuda)[0], "measurement")
        d = synthetic_doc("b58", protocol=cuda)
        d["determinism"]["cuda"]["identical"] = False
        self.assertEqual(self.classify(d, protocol=cuda)[0], "fallback")
        for change in ({"fits": False}, {"seed0_twice": dict(identical=False, n_differences=1, first=["x"])}):
            d = synthetic_doc("b58", protocol=cuda)
            d["concurrency"][1].update(change)
            d["recommendation"]["configurations"] = B.configurations(d["concurrency"])
            with self.subTest(change=list(change)):
                self.assertEqual(self.classify(d, protocol=cuda)[0], "fallback")

    def test_an_outcome_no_row_names_is_refused(self):
        """Rule 1.11: a row not ok for a reason the frozen script does not print, and a file that disagrees with
        itself (its configurations edited), stop the step."""
        d = synthetic_doc("b58")
        d["concurrency"][0].update(ok=False, why=["a cosmic ray"])
        with self.assertRaises(EB.Refused) as e:
            self.classify(d)
        self.assertIn("is not ok for a reason row 135 (4) does not name", str(e.exception))
        d = synthetic_doc("b58")
        d["recommendation"]["configurations"][0]["lower_min"] = 107.0
        with self.assertRaises(EB.Refused) as e:
            self.classify(d)
        self.assertIn("disagrees with its rows on ['lower_min']", str(e.exception))

    def test_the_crash_words_are_the_frozen_scripts(self):
        """row_why_kind reads benchmark_training.row_verdict's own words (mistake 10: one source)."""
        runs = [dict(device="cpu", plant=dict(PLANT)), dict(device="cuda:0", plant=dict(PLANT, plant_sha="f" * 16))]
        whys = B.row_verdict("cpu", 3, dict(timed_out=True, codes=[0, 1]), runs, 900.0)
        self.assertEqual([EB.row_why_kind(w) for w in whys], ["a", "a", "a", "device", "plant"])
        self.assertEqual(EB.row_why_kind("error: RuntimeError('x')"), "a")
        self.assertIsNone(EB.row_why_kind("a cosmic ray"))


# =====================================================================================================
class SynRepo:
    """A SYNTHETIC git repository: the four cost entry points as stubs (train.py imports helper.py), committed as
    "C1b"; B1's attempts and B0 records added with attempt() and b0()."""

    def __init__(self, tmp):
        self.root = os.path.join(tmp, "repo")
        os.makedirs(self.root)
        fx.git(self.root, "init", "-q")
        self.write("train.py", "import helper\n")
        self.write("helper.py", "X = 1\n")
        for m in ("train_all.py", "benchmark_training.py", "check_training_device.py"):
            self.write(m, "# a stub\n")
        self.write("README.md", "synthetic\n")
        self.c1b = self.commit("C1b: the protocol (SYNTHETIC)")

    def write(self, rel, text):
        path = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def commit(self, message):
        return fx.commit_all(self.root, message)

    def short(self, sha):
        return fx.git(self.root, "rev-parse", "--short", sha)

    def attempt(self, engine_id, k, doc, *, kind="device", txt=True, json_too=True):
        name = (EB.ATTEMPT if kind == "device" else EB.CPU_ATTEMPT).format(engine=engine_id, k=k)
        if json_too:
            self.write(f"{EB.BENCH_REL}/{name}", json.dumps(doc, indent=1))
        if txt:
            self.write(f"{EB.BENCH_REL}/{name[:-5]}.txt", "printed\n")

    def b0(self, doc):
        self.write(f"{EB.BENCH_REL}/{EB.B0_RECORD.format(git_head=doc['code']['git_head'])}",
                   json.dumps(b0_of(doc), indent=1, sort_keys=True))


class RepoCase(Guarded):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="epa_backend_")
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.repo = SynRepo(self.tmp)
        self.enterContext(mock.patch.dict(EB.PROTOCOL, protocol_commit=self.repo.c1b))

    def doc(self, sha=None):
        """The B58's attempt at commit `sha` (the SYNTHETIC C1b when None)."""
        return synthetic_doc("b58", git_head=self.repo.short(sha or self.repo.c1b))

    def series(self):
        """The B58's device series, the B58 alone trainable."""
        return EB.read_series(self.repo.root, "b58", kind="device", protocol=EB.PROTOCOL, live=live_for(("b58",)),
                              trainable_before=("b58",), cache={})


class Series(RepoCase):
    def test_a_crash_then_the_measurement(self):
        r = self.repo
        r.attempt("b58", 1, None, json_too=False)            # crashed before its JSON: its .txt alone
        d = self.doc()
        r.attempt("b58", 2, d)
        r.b0(d)
        r.commit("B1")
        self.assertEqual([(a["k"], a["json"] is None, a["txt"] is None)
                          for a in EB.bench_attempts(r.root, "b58", kind="device")],
                         [(1, True, False), (2, False, False)])
        s = self.series()
        self.assertEqual(s["problems"], [])
        self.assertEqual(s["outcome"], ("measurement", Fraction(10619, 100)))
        self.assertEqual([c["path"] for c in s["crashes"]], [f"{EB.BENCH_REL}/B1_bench_b58.attempt1.txt"])
        self.assertEqual([x["git_head"] for x in s["b0"]], [d["code"]["git_head"]])
        self.assertEqual(EB.bench_attempts(r.root, "b58", kind="cpu"), [])

    def test_an_attempt_after_a_measurement_and_a_last_crash_are_refused(self):
        r = self.repo
        d = self.doc()
        r.attempt("b58", 1, d)
        crashed = copy.deepcopy(d)
        crashed["status"] = "running"
        r.attempt("b58", 2, crashed)
        r.b0(d)
        r.commit("B1")
        probs = self.series()["problems"]
        self.assertEqual(len(probs), 2, probs)
        self.assertIn("only a crash is repeated", probs[0])
        self.assertIn("is a crash", probs[1])

    def test_a_missing_k_is_refused(self):
        r = self.repo
        d = self.doc()
        r.attempt("b58", 2, d)
        r.b0(d)
        r.commit("B1")
        with self.assertRaises(EB.Refused) as e:
            EB.bench_attempts(r.root, "b58", kind="device")
        self.assertIn("b58's device attempts are k = [2]: one is missing", str(e.exception))

    def test_no_B0_record_is_an_operator_fault(self):
        r = self.repo
        r.attempt("b58", 1, self.doc())
        r.commit("B1")
        s = self.series()
        self.assertEqual(s["outcome"][0], "crash")
        self.assertIn("no committed B0 record", s["outcome"][1])

    def test_an_attempt_whose_cost_files_changed_is_superseded(self):
        """A change to helper.py, in train.py's import closure, after the first attempt supersedes it (row 140 (5));
        the second, at the changed commit, is read. The control: a change to README.md alone supersedes nothing."""
        r = self.repo
        old = self.doc()
        r.attempt("b58", 1, old)
        r.b0(old)
        r.write("helper.py", "X = 2\n")
        fixed = r.commit("the fix")
        new = self.doc(sha=fixed)
        r.attempt("b58", 2, new)
        r.b0(new)
        r.commit("B1 repeated")
        s = self.series()
        self.assertEqual(s["problems"], [])
        self.assertEqual([x["git_head"] for x in s["superseded"]], [old["code"]["git_head"]])
        self.assertIn("helper.py", s["superseded"][0]["why"])
        self.assertEqual(s["attempt"]["k"], 2)
        self.assertIn("helper.py", EB.cost_files(r.root, "HEAD"))
        self.assertIn("helper.py", EB.cost_files(r.root, old["code"]["git_head"]))

    def test_the_control_a_change_outside_the_cost_files_supersedes_nothing(self):
        r = self.repo
        d = self.doc()
        r.attempt("b58", 1, d)
        r.b0(d)
        r.write("README.md", "changed\n")
        r.commit("B1, and a document")
        s = self.series()
        self.assertEqual((s["problems"], s["superseded"], s["outcome"][0]), ([], [], "measurement"))

    def test_every_attempt_superseded_names_row_140_5(self):
        r = self.repo
        d = self.doc()
        r.attempt("b58", 1, d)
        r.b0(d)
        r.write("helper.py", "X = 3\n")
        r.commit("B1, then a plant change")
        probs = self.series()["problems"]
        self.assertEqual(len(probs), 1)
        self.assertIn("row 140 (5)", probs[0])

    def test_a_cpu_series_beside_the_cpu_protocol_is_refused(self):
        """CPU_PROTOCOL is None (row 135 names the CPU): a CPU attempt's .json and .txt are each refused, each named
        once, with row 135 (4)(c)'s words. The control (mistake 12): with the CPU series gone and the device's
        attempt in its place, nothing is refused."""
        r = self.repo
        d = self.doc()
        r.attempt("b58", 1, d, kind="cpu")
        r.commit("B1")
        probs = EB._cpu_files_problems(r.root, ("b58",))
        self.assertEqual(len(probs), 2, probs)
        self.assertTrue(all("a CPU series beside the protocol's, which names the CPU (row 135 (4)(c)" in p
                            for p in probs), probs)
        names = [EB.CPU_ATTEMPT.format(engine="b58", k=1), EB._txt(EB.CPU_ATTEMPT).format(engine="b58", k=1)]
        for name in names:
            self.assertEqual(sum(p.startswith(f"{EB.BENCH_REL}/{name}: ") for p in probs), 1, (name, probs))
        for name in names:
            os.remove(os.path.join(r.root, EB.BENCH_REL, name))
        r.attempt("b58", 1, d)
        r.commit("the CPU series removed, the device's attempt in its place (SYNTHETIC)")
        self.assertEqual(EB._cpu_files_problems(r.root, ("b58",)), [])

    def test_an_attempt_at_a_commit_this_clone_lacks_is_refused(self):
        """superseded_why refuses a git_head that is not a commit here, by its text (the laptop fetches it), before
        cost_files would refuse it with git archive's words. The control: the SYNTHETIC C1b, a commit here, is
        compared, and nothing but results changed since, so it is not superseded."""
        r = self.repo
        d = synthetic_doc("b58", git_head="fedcba9")
        r.attempt("b58", 1, d)
        r.b0(d)
        r.commit("B1, from a commit this clone lacks (SYNTHETIC)")
        with self.assertRaises(EB.Refused) as e:
            self.series()
        self.assertIn("the attempt's git_head fedcba9 is not a commit here: fetch it", str(e.exception))
        self.assertIsNone(EB.superseded_why(r.root, r.short(r.c1b), {}))


# =====================================================================================================
class Protocol(Guarded):
    def test_the_protocol_commit_is_C1b(self):
        """Row 135 (2): the commit is C1b's, HEAD descends from it, its subject names C1b, and
        benchmark_training.py is unchanged since (frozen from C1b on)."""
        c = EB.PROTOCOL["protocol_commit"]
        self.assertEqual(EB.protocol_commit_problems(HERE, EB.PROTOCOL), [])
        self.assertIn("C1b: the benchmark protocol", fx.git(HERE, "log", "-1", "--format=%s", c))

    def test_a_wrong_commit_is_refused(self):
        """The controls of the test above (mistake 12): here, a sha this repository does not hold and a sha that
        is not one; in a SYNTHETIC repository, a commit HEAD does not descend from, and benchmark_training.py
        edited after the protocol commit (and the SYNTHETIC C1b itself, which passes)."""
        for c, words in (("f" * 40, "not a commit"), ("abc", "40 hex")):
            with self.subTest(c=c):
                probs = EB.protocol_commit_problems(HERE, dict(EB.PROTOCOL, protocol_commit=c))
                self.assertEqual(len(probs), 1)
                self.assertIn(words, probs[0])
        tmp = tempfile.mkdtemp(prefix="epa_backend_")
        self.addCleanup(shutil.rmtree, tmp, True)
        r = SynRepo(tmp)
        fx.git(r.root, "checkout", "-q", "-b", "side")
        r.write("README.md", "a side branch\n")
        side = r.commit("a side branch (SYNTHETIC)")
        fx.git(r.root, "checkout", "-q", "-")
        r.write("benchmark_training.py", "# edited after C1b\n")
        r.commit("an edit to the frozen script (SYNTHETIC)")
        for c, words in ((side, "does not descend"), (r.c1b, "frozen from C1b on")):
            with self.subTest(c=c):
                probs = EB.protocol_commit_problems(r.root, dict(EB.PROTOCOL, protocol_commit=c))
                self.assertEqual(len(probs), 1)
                self.assertIn(words, probs[0])
        fx.git(r.root, "reset", "-q", "--hard", r.c1b)
        self.assertEqual(EB.protocol_commit_problems(r.root, dict(EB.PROTOCOL, protocol_commit=r.c1b)), [])

    def test_the_protocol_is_row_135s(self):
        """Step 3 on Jad's PC (docs/build_step_2/STEP3_RUN_2026-11-02_JAD_PC.md: the CPU, 12 at once, torch
        2.14.0+cpu; S and R the script's defaults); the lock's python; the four-engine road, the share on, the
        knock out; the timed recipe flags are benchmark_training's own object."""
        import epa_freeze
        p = EB.PROTOCOL
        self.assertEqual(set(p), {"device", "torch", "python", "runs", "steps_per_run", "repeats", "road", "dt",
                                  "buffer", "roads_record", "scored_share", "reward_knock", "recipe_timed",
                                  "protocol_commit", "lock"})
        self.assertEqual((p["device"], p["torch"], p["runs"], p["steps_per_run"], p["repeats"]),
                         ("cpu", "2.14.0+cpu", 12, 3000, B.REPEATS))
        self.assertEqual(p["python"], epa_freeze.lock_pins()["python"])
        self.assertEqual(p["lock"], epa_freeze.LOCK_FILE)
        self.assertIs(p["recipe_timed"], B.RECIPE29_TIMED)
        self.assertEqual((p["road"], p["dt"], p["buffer"], p["roads_record"], p["scored_share"], p["reward_knock"]),
                         ("four_engine", 1.0, 450_000, ER.ROADS_REL, True, "out"))
        self.assertIsNone(EB.CPU_PROTOCOL)                    # row 135 names the CPU: no CUDA series

    def test_the_frozen_script_writes_the_plan_classify_expects(self):
        """expected_plan is the plan benchmark_training.py's own main() writes for the runbook's B1 command under
        PROTOCOL (main_as: its probe and machine stood in, stopped at its first save; nothing runs). The probe
        says train.build_env takes reward_knock, as it will from P on."""
        import four_engine_roads as FER
        p = EB.PROTOCOL
        probe = dict(torch=p["torch"], torch_cuda=None, design_dt=B.DT, roads_known=["extremes", "four_engine"],
                     engines_known=list(ALL), engines_trainable=["b58"],
                     cuda=dict(ok=False, why="a CPU build"), build_env_takes_reward_knock=True)
        mach = dict(host="dev1", platform="P", cpu="C", logical_cpus=12, usable_cpus=12, physical_cpus=6,
                    ram_gb=32.0, available_gb=20.0, python=p["python"], torch=p["torch"], torch_cuda=None,
                    packages={}, power="plan", gpus=[], cuda=probe["cuda"], engines_known=list(ALL),
                    engines_trainable=["b58"])
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(FER, "real_record_problem", lambda path: None):
            argv = ["--engine", "b58", "--road", p["road"], "--roads-record", p["roads_record"], "--reward-knock",
                    p["reward_knock"], "--device", p["device"], "--runs", str(p["runs"]), "--steps",
                    str(p["steps_per_run"]), "--repeats", str(p["repeats"]),
                    "--out", os.path.join(tmp, "B1_bench_b58.attempt1.json")]
            text, ended, saved, _ = B.main_as(B, argv, probe, mach)
        self.assertEqual(ended, "saved", text)
        self.assertEqual(json.loads(saved[0]), EB.expected_plan("b58", p))


# =====================================================================================================
class RunbookNames(Guarded):
    """The runbook's B0, B1 and B5 shell text is the one definition of B1's file names (the sheet's "How it
    binds"); Ta's constants are checked against it as C1b, which alone edits it, committed it, and against the
    runbook in this tree, the one B0 checks out at Ta and Jad reads (row 146 (6))."""

    def text(self):
        return EB.runbook_text(HERE, EB.PROTOCOL["protocol_commit"])

    def test_the_runbook_at_the_protocol_commit_names_what_ta_reads(self):
        self.assertEqual(EB.runbook_name_problems(self.text()), [])

    def test_the_runbook_in_this_tree_names_what_ta_reads(self):
        with open(os.path.join(HERE, *EB.RUNBOOK_REL.split("/")), encoding="utf-8") as fh:
            self.assertEqual(EB.runbook_name_problems(fh.read().replace("\r\n", "\n")), [])

    def test_the_control_each_renamed_pattern_fails(self):
        """Mistake 12: each pattern renamed once fails with its own problem, so that no other can stand in."""
        text = self.text()
        for old, new, words in (
                ('--out "$B1OUT/B1_bench_$E.attempt$k.json"', '--out "$B1OUT/B1_bench_$E.try$k.json"',
                 "B1's --out names are"),
                ('--out "$B1OUT/B1_bench_$E.cpu.attempt$k.json"', '--out "$B1OUT/B1_bench_$E.gpu.attempt$k.json"',
                 "B1's --out names are"),
                ('tee "$B1OUT/B1_bench_$E.attempt$k.txt"', 'tee "$B1OUT/B1_bench_$E.attempt$k.log"',
                 "B1's tee names are"),
                ("f\"B0_{rec['git_head']}.json\"", "f\"B0_record_{rec['git_head']}.json\"", "B0's record name is"),
                ('"$B1OUT"/B0_*.json', '"$B1OUT"/B0x_*.json', "B5's globs"),
                ('"$B1OUT"/B0_*.json results/benchmarks/', '"$B1OUT"/B0_*.json results/bench/', "B5 copies into"),
                ('[ -e "results/benchmarks/B1_bench_$E.attempt$k.txt" ]',
                 '[ -e "results/bench/B1_bench_$E.attempt$k.txt" ]', "B1's k loops count")):
            with self.subTest(new=new):
                self.assertEqual(text.count(old), 1, old)
                probs = EB.runbook_name_problems(text.replace(old, new))
                self.assertEqual(len(probs), 1, probs)
                self.assertTrue(probs[0].startswith(words), probs)


# =====================================================================================================
class Record(RepoCase):
    """compute, write and check on a SYNTHETIC repository holding a SYNTHETIC summary.json and B1's attempts."""

    def summary(self, dropped=()):
        return {"schema": engines.VALIDATION_SUMMARY_SCHEMA,
                "engines": {e: {"drop": e in dropped, "reruns": {}} for e in common.EPA_ENGINES}}

    def build(self, lowers, *, dropped=()):
        """Run 2's summary (dropping `dropped`), then one measurement per surviving engine at `lowers[e]`."""
        r = self.repo
        r.write(engines.VALIDATION_SUMMARY_REL, json.dumps(self.summary(dropped), indent=1))
        b1 = r.commit("Run 2's summary")
        trainable = tuple(e for e in ALL if e not in dropped)
        for e in trainable:
            d = synthetic_doc(e, git_head=r.short(b1), trainable=trainable, lowers=(lowers[e],))
            r.attempt(e, 1, d)
            r.b0(d)
        r.commit("B1")
        return trainable

    def test_the_record_layout_with_every_engine_kept(self):
        trainable = self.build({e: "150" for e in ALL})
        before = sorted(os.listdir(self.repo.root))
        rec = EB.compute(self.repo.root, live=live_for(trainable))
        self.assertEqual(sorted(os.listdir(self.repo.root)), before)           # compute writes nothing
        self.assertEqual(list(rec), ["schema", "rule", "window", "constants", "protocol", "drop_order", "inputs",
                                     "trace", "engines", "in_test", "n", "seconds_at_n", "total_s", "slack_s",
                                     "notes", "provenance"])
        self.assertEqual(rec["schema"], engines.BACKEND_SCHEMA)
        self.assertEqual(list(rec["engines"]), list(engines.known()))
        self.assertEqual(rec["in_test"], list(ALL))
        self.assertEqual(rec["n"], 24)                       # 4 x ceil(72 / 12) x 36 000 s = 864 000 s
        self.assertEqual((rec["total_s"], rec["slack_s"]), (864000.0, 0.0))
        self.assertEqual(rec["drop_order"], list(EB.DROP_ORDER))
        self.assertEqual(set(rec["inputs"]), {"trainable_before", "summary", "benchmarks", "fallback", "superseded",
                                              "crashes", "b0"})
        self.assertEqual(rec["inputs"]["benchmarks"]["ford_27tt"]["r_e"], "25/2")     # 150 / 12
        self.assertEqual(rec["inputs"]["benchmarks"]["ford_27tt"]["lower_min"], "150.0")
        self.assertTrue(all(v == {"drop": False, "backend": "cycle", "reason": None} for v in rec["engines"].values()))
        json.dumps(rec, allow_nan=False)

    def test_a_run_2_drop_and_a_schedule_drop(self):
        """The Mazda dropped by Run 2; the Honda by the schedule (n 16 -> 28 at 90 steps/s, N 12; arithmetic)."""
        trainable = self.build({e: "90" for e in ALL}, dropped=("mazda_25t",))
        rec = EB.compute(self.repo.root, live=live_for(trainable))
        sha = common.sha_text(os.path.join(self.repo.root, *engines.VALIDATION_SUMMARY_REL.split("/")))
        self.assertEqual(rec["engines"]["mazda_25t"], {"drop": True, "backend": None, "reason":
                                                       f"Run 2: {engines.VALIDATION_SUMMARY_REL} {sha} (row 107 (1))"})
        self.assertEqual(rec["engines"]["honda_l15b7"]["reason"], "rows 114 and 136: the schedule (n 16 -> 28)")
        self.assertEqual((rec["in_test"], rec["n"]), (["b58", "ford_27tt"], 28))
        self.assertEqual(engines.trainable_from(self.summary(("mazda_25t",)), rec), tuple(rec["in_test"]))

    def test_n_null_when_no_epa_engine_survives(self):
        """The schedule leaves no EPA engine (row 136 (1)): the failed schedule is the result."""
        trainable = self.build({e: "50" for e in ALL})
        rec = EB.compute(self.repo.root, live=live_for(trainable))
        self.assertIsNone(rec["n"])
        self.assertEqual(rec["in_test"], ["b58"])
        self.assertEqual((rec["seconds_at_n"], rec["total_s"], rec["slack_s"]), (None, None, None))
        self.assertEqual([s["n"] for s in rec["trace"]], [8, 8, 16, None])
        self.assertEqual(rec["engines"]["ford_27tt"]["reason"], "rows 114 and 136: the schedule (n 16 -> null)")
        self.assertTrue(any("MD:1611-1612" in n and "the failed schedule is reported" in n for n in rec["notes"]))
        self.assertFalse(any("failed validations" in n for n in rec["notes"]))
        self.assertTrue(any("not this n" in n for n in rec["notes"]))

    def test_run_2_left_no_epa_engine_so_n_is_null_with_no_schedule_drop(self):
        """Run 2's outcome (section Q; row 146 (3)): summary.json drops all three, so B1 times the B58 alone, and
        the record holds n null and in_test ['b58'] with no schedule drop. Each EPA engine's reason is Run 2's,
        and the notes give the failed validations as the result, never a failed schedule (MD:1611-1612; the sheet
        17's 10.2). The control is the test above: the schedule's drops give the failed schedule."""
        trainable = self.build({"b58": "150"}, dropped=common.EPA_ENGINES)
        self.assertEqual(trainable, ("b58",))
        rec = EB.compute(self.repo.root, live=live_for(trainable))
        sha = common.sha_text(os.path.join(self.repo.root, *engines.VALIDATION_SUMMARY_REL.split("/")))
        self.assertIsNone(rec["n"])
        self.assertEqual(rec["in_test"], ["b58"])
        self.assertEqual(rec["inputs"]["trainable_before"], ["b58"])
        self.assertEqual(list(rec["inputs"]["benchmarks"]), ["b58"])
        self.assertEqual(rec["engines"]["b58"], {"drop": False, "backend": "cycle", "reason": None})
        for e in common.EPA_ENGINES:
            self.assertEqual(rec["engines"][e], {"drop": True, "backend": None, "reason":
                                                 f"Run 2: {engines.VALIDATION_SUMMARY_REL} {sha} (row 107 (1))"})
        self.assertEqual([(s["in_test"], s["n"]) for s in rec["trace"]], [(["b58"], None)])
        self.assertEqual((rec["seconds_at_n"], rec["total_s"], rec["slack_s"]), (None, None, None))
        self.assertTrue(any("failed validations are reported" in n and "MD:1611-1612" in n for n in rec["notes"]))
        self.assertFalse(any("failed schedule" in n for n in rec["notes"]))
        self.assertTrue(any("not this n" in n for n in rec["notes"]))
        self.assertEqual(engines.trainable_from(self.summary(common.EPA_ENGINES), rec), ("b58",))

    def test_written_once_and_checked(self):
        trainable = self.build({e: "150" for e in ALL})
        live = live_for(trainable)
        sha = EB.write(self.repo.root, live=live)
        path = EB.record_path(self.repo.root)
        self.assertEqual(common.sha_text(path), sha)
        with self.assertRaises(EB.Refused) as e:
            EB.write(self.repo.root, live=live)
        self.assertIn(f"{engines.BACKEND_REL} exists: it is written once", str(e.exception))
        with self.assertRaises(EB.Refused) as e:              # not committed yet
            EB.check(self.repo.root, live=live)
        self.assertIn(f"{engines.BACKEND_REL} is not committed at HEAD", str(e.exception))
        self.repo.commit("Tb")
        self.assertEqual(EB.check(self.repo.root, live=live), [])
        with open(path, encoding="utf-8") as fh:
            rec = json.load(fh)
        rec["n"] = 20
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(rec, fh)
        self.repo.commit("a hand edit")
        self.assertEqual(EB.check(self.repo.root, live=live), ["n: committed 20, recomputed 24"])
        os.remove(path)
        self.repo.commit("removed")
        with self.assertRaises(EB.Refused) as e:              # in HEAD's history: written once
            EB.write(self.repo.root, live=live)
        self.assertIn(f"{engines.BACKEND_REL} is in HEAD's history", str(e.exception))

    def test_the_refusals(self):
        trainable = self.build({e: "150" for e in ALL})
        live = live_for(trainable)
        self.assertEqual(EB.problems(self.repo.root, live=live), [])          # the control
        self.repo.write("stray.py", "x = 1\n")
        probs = EB.problems(self.repo.root, live=live)
        self.assertEqual(len(probs), 1, probs)
        self.assertTrue(probs[0].startswith("the work tree changes what the record is computed from: stray.py (a .py "
                                            "file"), probs)
        os.remove(os.path.join(self.repo.root, "stray.py"))
        with mock.patch.dict(EB.PROTOCOL, protocol_commit="f" * 40):
            self.assertIn("not a commit", EB.problems(self.repo.root, live=live)[0])
        self.assertIn("live covers", EB.problems(self.repo.root, live=live_for(("b58",)))[0])
        with mock.patch.dict(EB.PROTOCOL, runs=16):
            probs = EB.problems(self.repo.root, live=live)
        self.assertEqual(len(probs), 4)
        self.assertTrue(all("is a crash" in p and "plan is not the protocol's" in p for p in probs), probs)

    def test_check_on_pr_bs_staged_tree_refuses_only_what_can_move_the_record(self):
        """Row 146 (6) and the sheet 17's 14: PR-B's gate runs check on its staged tree. After Tb, a SYNTHETIC
        results/PREREGISTRATION_B58H.md, a session report and CHECKPOINT.md staged and a note untracked give check
        []. The controls (mistake 12): each change that can move the record, staged, modified, deleted or
        untracked, is refused alone and named with its reason, and PR-B's files are not named: helper.py staged
        (train.py's closure), a new .py untracked, the lock (a cost file that is not a .py) staged, a file under
        results/benchmarks untracked, Run 2's summary modified, and the record itself deleted."""
        r = self.repo
        live = live_for(self.build({e: "150" for e in ALL}))
        EB.write(r.root, live=live)
        r.commit("Tb")

        def pr_b():
            for rel in (EB.B58H_PREREGISTRATION_REL, "docs/session_reports/SYNTHETIC.md", "CHECKPOINT.md"):
                r.write(rel, "SYNTHETIC\n")
                fx.git(r.root, "add", "--", rel)
            r.write("notes.txt", "SYNTHETIC, untracked\n")
        pr_b()
        self.assertEqual(EB.check(r.root, live=live), [])
        r.write("helper.py", "X = 9\n")
        fx.git(r.root, "add", "--", "helper.py")
        with self.assertRaises(EB.Refused) as e:                  # the reviewer's control, through check itself
            EB.check(r.root, live=live)
        self.assertIn("is computed from: helper.py (a .py file", str(e.exception))
        for rel, change, why in (("helper.py", "staged", "a .py file: an import closure can change"),
                                 ("tools/new_module.py", "untracked", "a .py file: an import closure can change"),
                                 (EB.PROTOCOL["lock"], "staged", "a cost file"),
                                 (f"{EB.BENCH_REL}/B1_bench_b58.attempt2.txt", "untracked",
                                  f"under {EB.BENCH_REL}: B1's attempts and B0 records"),
                                 (engines.VALIDATION_SUMMARY_REL, "modified", "Run 2's summary"),
                                 (engines.BACKEND_REL, "deleted", "the backend record")):
            with self.subTest(rel=rel, change=change):
                fx.git(r.root, "reset", "-q", "--hard", "HEAD")
                fx.git(r.root, "clean", "-fdq")
                pr_b()
                if change == "deleted":
                    os.remove(os.path.join(r.root, *rel.split("/")))
                else:
                    r.write(rel, "X = 9\n" if rel.endswith(".py") else "SYNTHETIC change\n")
                if change == "staged":
                    fx.git(r.root, "add", "--", rel)
                probs = EB.problems(r.root, live=live)
                self.assertEqual(probs, [f"the work tree changes what the record is computed from: {rel} ({why}). "
                                         "Commit or restore each first; any other change is allowed (row 146 (6))"])
                self.assertNotIn(EB.B58H_PREREGISTRATION_REL, probs[0])

    def rewrite_b58_attempt(self, original, mutate):
        """The B58's committed attempt 1 replaced by `original` changed by `mutate`, and committed (SYNTHETIC: on
        the device an attempt is never edited)."""
        d = copy.deepcopy(original)
        mutate(d)
        self.repo.write(f"{EB.BENCH_REL}/{EB.ATTEMPT.format(engine='b58', k=1)}", json.dumps(d, indent=1))
        self.repo.commit(f"the B58's attempt, {mutate.__name__} (SYNTHETIC)")

    def test_b1_reading_defect_or_stop_is_refused_with_row_135_4_c_s_text(self):
        """Row 146 (4): B1 reading 'defect' or 'stop' follows row 135 (4)(c). The B58's one attempt (Run 2 left
        no EPA engine) with identical False refuses with DEFECT_TEXT and never STOP_TEXT; with fits False at N, with
        STOP_TEXT, in row 146 (4)'s reading, and never DEFECT_TEXT. The rows' words are typed here, so that the
        texts are checked against the rows and not against themselves. The control (mistake 12): the attempt
        unchanged gives the record."""
        trainable = self.build({"b58": "150"}, dropped=common.EPA_ENGINES)
        live = live_for(trainable)
        self.assertEqual(EB.compute(self.repo.root, live=live)["in_test"], ["b58"])     # the control
        with open(os.path.join(self.repo.root, EB.BENCH_REL, EB.ATTEMPT.format(engine="b58", k=1)),
                  encoding="utf-8") as fh:
            original = json.load(fh)

        def defect(d):
            d["determinism"]["cpu"].update(identical=False, n_differences=3, first=["weights a"])

        def no_fit(d):
            d["concurrency"][0]["fits"] = False
            d["recommendation"]["configurations"] = B.configurations(d["concurrency"])
        for mutate, first, mine, other, words in (
                (defect, "b58: (c) seed 0 trained two different agents on cpu", EB.DEFECT_TEXT, EB.STOP_TEXT,
                 ("on the CPU, identical False is a coding defect", "It is found and fixed",
                  "re-makes P by row 140 (5)'s route")),
                (no_fit, "b58: (c) N = 12 does not fit at production size on the CPU", EB.STOP_TEXT, EB.DEFECT_TEXT,
                 ("on the CPU, fits False at N stops the four-engine training before T, and it is reported",
                  "the study's training stops, and it is reported"))):
            with self.subTest(mutate.__name__):
                self.rewrite_b58_attempt(original, mutate)
                with self.assertRaises(EB.Refused) as e:
                    EB.compute(self.repo.root, live=live)
                probs = e.exception.problems
                self.assertEqual(len(probs), 1, probs)
                self.assertTrue(probs[0].startswith(first), probs)
                self.assertIn(mine, probs[0])
                self.assertNotIn(other, probs[0])
                for w in words:
                    self.assertIn(w, probs[0])


# =====================================================================================================
class CostFiles(Guarded):
    def test_the_cost_files_of_this_tree(self):
        """The sheet 10.1's set, read from this work tree: the import closures of the four entry points, with
        epa_fit.py among them (row 146 (3): train.py imports four_engine_roads, which imports epa_roads, which
        imports roads_ceiling, which imports epa_fit, so G lands before B1, rule 1.5), PLANT_CODE, every engine's
        spec, derived and freeze files, the lock and the roads record. The control (mistake 12): files that time
        nothing are outside it, this module and its test, four_engine_analysis.py, the runbook, both
        preregistrations and the backend record among them."""
        files = EB.cost_files(HERE, "HEAD")
        self.assertEqual(files, sorted(set(files)))
        for a, b in (("train.py", "four_engine_roads.py"), ("four_engine_roads.py", "epa_roads.py"),
                     ("epa_roads.py", "roads_ceiling.py"), ("roads_ceiling.py", "epa_fit.py")):
            with self.subTest(closure=a):
                self.assertIn(b, ER.import_closure(a, root=HERE))
        inside = set(EB.COST_ENTRIES) | {"four_engine_roads.py", "epa_roads.py", "roads_ceiling.py", "epa_fit.py",
                                         EB.PROTOCOL["lock"], EB.PROTOCOL["roads_record"]} | set(FP.PLANT_CODE)
        for e in engines.known():
            meta = engines.read_spec(engines.PLANTS[e][0])["_meta"]
            inside |= set(engines.spec_files(e)) | {meta[k] for k in ("derived", "freeze") if k in meta}
        self.assertEqual(sorted(inside - set(files)), [])
        outside = {EB.MODULE_REL, "test_epa_backend.py", "four_engine_analysis.py", EB.RUNBOOK_REL,
                   EB.PREREGISTRATION_REL, EB.B58H_PREREGISTRATION_REL, engines.BACKEND_REL}
        self.assertEqual(sorted(outside & set(files)), [])


# =====================================================================================================
class PreregistrationCommands(Guarded):
    REC = {"in_test": ["b58", "ford_27tt"], "n": 24, "inputs": {"fallback": None}}

    def test_the_sections_commands_pass(self):
        self.assertEqual(EB.preregistration_problems(pr_text((self.REC["in_test"], 24)), self.REC,
                                                     protocol=EB.PROTOCOL, arms=3), [])
        self.assertEqual(EB.preregistration_problems(pr_text((self.REC["in_test"], 24), blind=True), self.REC,
                                                     protocol=EB.PROTOCOL, arms=4), [])

    def test_each_control_fails(self):
        """Mistake 12: each flag wrong, missing or added, an engine missing or twice, a command in prose, the
        blinded arm's flag on the wrong side of ARMS, and n null."""
        ids = self.REC["in_test"]
        good = pr_text((ids, 24))
        flags = "flags ['{}'] absent, repeated or not the section's".format
        cases = {"jobs": (good.replace("--jobs 12", "--jobs 14", 1), "b58: --jobs '14' is not the section's"),
                 "device": (good.replace("--device cpu", "--device cuda", 1), "b58: --device 'cuda' is not"),
                 "seeds": (good.replace("--seeds 0-23", "--seeds 0-19", 1), "b58: --seeds '0-19' is not"),
                 "out": (good.replace("dt1_b58", "dt1", 1), "b58: --out 'runs/four_engine_dt1' is not"),
                 "steps": (good.replace("--steps 450000", "--steps 3000", 1), "b58: --steps '3000' is not"),
                 "dt": (good.replace("--dt 1", "--dt 2", 1), "b58: --dt '2' is not"),
                 "knock": (good.replace("--reward-knock out", "--reward-knock in", 1), "b58: --reward-knock 'in'"),
                 "record": (good.replace("results/EPA_ROADS/roads.json", "x.json", 1), "b58: --roads-record 'x.json'"),
                 "no resume": (good.replace(" --no-resume", "", 1), "b58: " + flags("--no-resume")),
                 "third arm": (good.replace(" --third-arm", "", 1), "b58: " + flags("--third-arm")),
                 "an extra flag": (pr_text((ids, 24), extra=" --keep-buffer"), "b58: " + flags("--keep-buffer")),
                 "the blinded arm with three arms": (pr_text((ids, 24), blind=True), "b58: " + flags("--blind-per-h")),
                 "an engine missing": (pr_text((ids[:1], 24)), "the commands train ['b58'], not each engine"),
                 "an engine twice": (pr_text((ids + ids[:1], 24)), "the commands train ['b58', 'ford_27tt', 'b58']"),
                 "prose": (good + "\nThen run `python train_all.py --engine mazda_25t --jobs 3`.\n",
                           "a train_all.py command outside a fenced block")}
        for name, (text, words) in cases.items():
            with self.subTest(name):
                probs = EB.preregistration_problems(text, self.REC, protocol=EB.PROTOCOL, arms=3)
                self.assertTrue(any(words in p for p in probs), probs)
        probs = EB.preregistration_problems(good, self.REC, protocol=EB.PROTOCOL, arms=4)
        self.assertTrue(any(flags("--blind-per-h") in p for p in probs), probs)
        probs = EB.preregistration_problems(good, dict(self.REC, n=None), protocol=EB.PROTOCOL, arms=3)
        self.assertTrue(any("the backend record's n is null" in p for p in probs), probs)

    def test_the_protocol_after_a_fallback_is_the_cpus(self):
        fell = dict(self.REC, inputs={"fallback": {"engine": "b58"}})
        self.assertIs(EB.preregistration_protocol(self.REC), EB.PROTOCOL)
        with self.assertRaises(EB.Refused) as e:
            EB.preregistration_protocol(fell)                  # CPU_PROTOCOL is None
        self.assertIn("read a CUDA fallback, and CPU_PROTOCOL is None", str(e.exception))
        cpu = dict(EB.PROTOCOL, runs=10)
        with mock.patch.object(EB, "CPU_PROTOCOL", cpu):
            self.assertIs(EB.preregistration_protocol(fell), cpu)
            self.assertEqual(EB.preregistration_problems(pr_text((self.REC["in_test"], 24), jobs=10), fell,
                                                         protocol=EB.preregistration_protocol(fell), arms=3), [])


class PreregistrationState(Guarded):
    """The live Preregistration test's verdict on SYNTHETIC states and records (preregistration_verdict)."""
    KEPT = {"in_test": ["b58", "ford_27tt"], "n": 24, "inputs": {"fallback": None}}
    NULL = {"in_test": ["b58"], "n": None, "inputs": {"fallback": None}}

    def verdict(self, pr, rec, record=None, text=None):
        def never():
            raise AssertionError("read although its state says it is absent")
        return preregistration_verdict(pr, rec, (lambda: record) if record else never,
                                       (lambda: text) if text is not None else never)

    def test_n_null_requires_the_file_absent_and_the_control_fails(self):
        """Row 136 (1): with n null the preregistration is never written. The control (mistake 12): the same
        record with the file committed beside it fails."""
        self.assertEqual(self.verdict("absent", "committed", self.NULL), ("pass", None))
        kind, why = self.verdict("committed", "committed", self.NULL, pr_text((["b58"], 20)))
        self.assertEqual(kind, "fail")
        self.assertIn("row 136 (1)", why)

    def test_the_other_states(self):
        good = pr_text((self.KEPT["in_test"], 24))
        self.assertEqual(self.verdict("committed", "committed", self.KEPT, good), ("pass", None))
        self.assertEqual(self.verdict("absent", "committed", self.KEPT)[0], "skip")
        self.assertEqual(self.verdict("absent", "absent")[0], "skip")
        for pr, rec, record, text, words in (
                ("committed", "committed", self.KEPT, good.replace("--jobs 12", "--jobs 6"),
                 "b58: --jobs '6' is not the section's"),
                ("uncommitted", "committed", self.KEPT, good, "is present and not committed"),
                ("removed", "committed", self.NULL, None, f"{EB.PREREGISTRATION_REL} is removed after its commit"),
                ("committed", "uncommitted", self.KEPT, good, "the backend record is present and not committed"),
                ("absent", "removed", None, None, "the backend record is removed after its commit"),
                ("committed", "absent", None, good, "the preregistration follows the backend record")):
            with self.subTest(pr=pr, rec=rec):
                kind, why = self.verdict(pr, rec, record, text)
                self.assertEqual(kind, "fail")
                self.assertIn(words, why)


class LiveStates(RepoCase):
    """The live tests' skip-or-fail decisions, read on a SYNTHETIC repository (the sheet 10.1: skipped until
    committed, a failure if skipped after): committed_state, b58h_verdict and live_record_verdict, each state made
    by one change. A reader that always says 'absent', that ignores HEAD's history, or that counts no adds, would
    leave a live test skipping or passing for ever; each fails here."""

    def test_committed_state_reads_each_state(self):
        r, rel = self.repo, EB.B58H_PREREGISTRATION_REL
        path = os.path.join(r.root, *rel.split("/"))
        seen = [committed_state(rel, r.root)]                 # never written
        r.write(rel, "SYNTHETIC\n")
        seen.append(committed_state(rel, r.root))             # untracked
        fx.git(r.root, "add", "--", rel)
        seen.append(committed_state(rel, r.root))             # staged
        r.commit("T* (SYNTHETIC)")
        seen.append(committed_state(rel, r.root))             # committed
        r.write(rel, "SYNTHETIC, edited\n")
        seen.append(committed_state(rel, r.root))             # modified after its commit
        os.remove(path)
        seen.append(committed_state(rel, r.root))             # deleted, the deletion not committed
        r.commit("PR-B removed (SYNTHETIC)")
        seen.append(committed_state(rel, r.root))             # removed after its commit
        self.assertEqual(seen, ["absent", "uncommitted", "uncommitted", "committed", "uncommitted", "uncommitted",
                                "removed"])
        self.assertEqual(committed_state("results/NEVER_WRITTEN.md", r.root), "absent")      # the control

    def test_pr_b_skips_only_before_its_commit(self):
        """b58h_verdict: a skip while PR-B was never committed; a failure when it is present and not committed,
        when its commands have a problem, when it is removed after its commit, and when a second commit adds it
        again (T* would be ambiguous); a pass once, with one add and no problem, which is the control."""
        r, rel = self.repo, EB.B58H_PREREGISTRATION_REL
        read = []

        def problems_of(text):
            read.append(text)
            return [] if text.startswith("good") else ["the fenced command 'x': --jobs '6', not '12'"]

        def verdict():
            return b58h_verdict(r.root, problems_of=problems_of)
        self.assertEqual(verdict(), ("skip", f"{rel} is not committed yet (PR-B, ORDER step 20)"))
        r.write(rel, "good (SYNTHETIC)\n")
        self.assertEqual(verdict(), ("fail", f"{rel} is {STATE_WHY['uncommitted']}"))
        r.commit("T* (SYNTHETIC)")
        self.assertEqual(verdict(), ("pass", None))
        self.assertEqual(read, ["good (SYNTHETIC)\n"])                  # the committed text, read once
        r.write(rel, "bad (SYNTHETIC)\n")
        r.commit("PR-B edited (SYNTHETIC)")
        self.assertEqual(verdict(), ("fail", "the fenced command 'x': --jobs '6', not '12'"))
        os.remove(os.path.join(r.root, *rel.split("/")))
        r.commit("PR-B removed (SYNTHETIC)")
        self.assertEqual(verdict(), ("fail", f"{rel} is {STATE_WHY['removed']}"))
        r.write(rel, "good again (SYNTHETIC)\n")
        r.commit("PR-B added again (SYNTHETIC)")
        self.assertEqual(verdict(), ("fail", f"T* is the one commit that adds {rel} (row 146 (6)): 2 commits add it"))

    def test_the_record_skips_only_before_its_commit(self):
        """live_record_verdict: a skip while results/EPA_BACKEND.json was never committed; a failure when it is
        present and not committed, when check finds a difference, and when it is removed after its commit; a pass
        when check gives [] (the control)."""
        r, rel = self.repo, engines.BACKEND_REL
        diffs, asked = [], []

        def check_of(root):
            asked.append(root)
            return list(diffs)

        def verdict():
            return live_record_verdict(r.root, check_of=check_of)
        self.assertEqual(verdict(), ("skip", f"{rel} is not committed: ORDER step 19 has not run"))
        r.write(rel, "{}\n")
        self.assertEqual(verdict(), ("fail", f"{rel} is {STATE_WHY['uncommitted']}"))
        r.commit("Tb (SYNTHETIC)")
        self.assertEqual(verdict(), ("pass", None))
        self.assertEqual(asked, [r.root])
        diffs.append("n: committed 20, recomputed 24")
        self.assertEqual(verdict(), ("fail", "check finds differences: ['n: committed 20, recomputed 24']"))
        diffs.clear()
        os.remove(os.path.join(r.root, *rel.split("/")))
        r.commit("the record removed (SYNTHETIC)")
        self.assertEqual(verdict(), ("fail", f"{rel} is {STATE_WHY['removed']}"))


# =====================================================================================================
class LivePlants(Guarded):
    def test_the_one_plant_fingerprint_call(self):
        calls = []

        def fp(*args, **kw):
            calls.append((args, kw))
            return dict(PLANT, backend=None, train_backend="cycle", plant_sha="c" * 16)
        with mock.patch.object(FP, "plant_fingerprint", fp), mock.patch.object(engines, "get", lambda e: f"<{e}>"):
            out = EB.live_plants(("b58", "ford_27tt"))
        self.assertEqual(calls, [(("phase-d",), dict(plant=f"<{e}>", train_backend="cycle", score_backend="cycle",
                                                     preview_h_s=None, reward_knock=False))
                                 for e in ("b58", "ford_27tt")])
        self.assertEqual(out["b58"], dict(PLANT, plant_sha="c" * 16))
        self.assertEqual(list(out["b58"]), list(B.PLANT_KEYS))


# =====================================================================================================
class Cli(Guarded):
    def test_no_choice_can_be_passed(self):
        """Each refused by argparse itself, matched by its message (exit 2): nothing is read before it."""
        for argv, words in ((["compute", "--n", "20"], "unrecognized arguments: --n 20"),
                            (["write", "--engines", "b58"], "unrecognized arguments: --engines b58"),
                            (["check", "--window", "1"], "unrecognized arguments: --window 1"),
                            (["compute", "--rate", "1"], "unrecognized arguments: --rate 1"),
                            (["compute", "--runs", "12"], "unrecognized arguments: --runs 12"),
                            (["compute", "--device", "cpu"], "unrecognized arguments: --device cpu"),
                            (["write", "--force"], "unrecognized arguments: --force"),
                            ([], "the following arguments are required: command"),
                            (["run"], "invalid choice: 'run'"),
                            (["compute", "write"], "unrecognized arguments: write")):
            err = io.StringIO()
            with self.subTest(argv=argv), contextlib.redirect_stderr(err):
                with self.assertRaises(SystemExit) as e:
                    EB.main(argv)
                self.assertEqual(e.exception.code, 2)
            self.assertIn(words, err.getvalue(), argv)


# =====================================================================================================
class Hygiene(Guarded):
    def test_the_order_of_leaving(self):
        """Row 136 (1): one tuple, the Honda, the Mazda, the Ford; the B58 in neither (MD:1590-1591)."""
        self.assertEqual(EB.DROP_ORDER, ("honda_l15b7", "mazda_25t", "ford_27tt"))
        self.assertIs(EB.LEAVE_ORDER, EB.DROP_ORDER)
        self.assertEqual(set(EB.DROP_ORDER), set(common.EPA_ENGINES))
        self.assertNotIn(ER.NEVER_DROPPED, EB.DROP_ORDER)
        self.assertFalse([n for n in vars(EB) if "TABLE" in n.upper()])        # no table constant (row 136)

    def test_the_constants_against_their_owners(self):
        self.assertEqual((EB.N_MIN, B.SEEDS_TARGET), (20, 20))
        self.assertEqual((EB.ARMS, EB.SEED_LIMIT), (B.ARMS, 1000))
        self.assertIs(EB.PROD_STEPS, B.PROD_STEPS)
        self.assertEqual((EB.W_S, EB.W_FIRST, EB.W_LAST), (864_000, "2026-11-10T00:00:00+03:00",
                                                            "2026-11-20T00:00:00+03:00"))
        self.assertEqual((EB.BENCH_REL, EB.ATTEMPT, EB.CPU_ATTEMPT, EB.B0_RECORD),
                         ("results/benchmarks", "B1_bench_{engine}.attempt{k}.json",
                          "B1_bench_{engine}.cpu.attempt{k}.json", "B0_{git_head}.json"))
        # the two preregistrations' paths as ORDER step 20 and the sheet 11 and 17's 11 name them: a misspelt
        # path would leave Preregistration or PreregistrationB58H skipping for ever
        self.assertEqual((EB.PREREGISTRATION_REL, EB.B58H_PREREGISTRATION_REL),
                         ("results/PREREGISTRATION_4E.md", "results/PREREGISTRATION_B58H.md"))
        self.assertEqual((EB.B58H_ENGINE, EB.B58H_N), ("b58", 20))

    def test_P_s_names_are_here(self):
        """P2's reader, which Record, Preregistration and LiveRecord read (the sheet 6.3)."""
        for name in ("trainable_from", "committed_record", "VALIDATION_SUMMARY_REL", "BACKEND_REL", "BACKEND_SCHEMA",
                     "NEVER_DROPPED"):
            self.assertTrue(hasattr(engines, name), name)
        self.assertEqual((engines.BACKEND_REL, engines.BACKEND_SCHEMA, engines.NEVER_DROPPED),
                         ("results/EPA_BACKEND.json", "epa-backend/1", ER.NEVER_DROPPED))
        self.assertEqual(engines.VALIDATION_SUMMARY_REL, ER.SUMMARY_REL)

    def test_no_hashed_module_imports_this_one(self):
        """Row 121: roads.json's 35 files, PLANT_CODE and epa_freeze.CODE_HASHED import epa_backend at no depth."""
        import epa_freeze
        files = set(ER.hashed_files(root=HERE, engines=ER.ENGINES)) | set(FP.PLANT_CODE) | set(epa_freeze.CODE_HASHED)
        self.assertNotIn(EB.MODULE_REL, files)
        for f in sorted(x for x in files if x.endswith(".py")):
            with self.subTest(f=f):
                self.assertNotIn(EB.MODULE_REL, ER.import_closure(f, root=HERE))
        with tempfile.TemporaryDirectory() as tmp:            # the control: the check can fail
            for name, src in (("hashed.py", "def f():\n    import epa_backend\n"), (EB.MODULE_REL, "x = 1\n")):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(src)
            self.assertIn(EB.MODULE_REL, ER.import_closure("hashed.py", root=tmp))

    def test_no_torch_and_no_file_at_import(self):
        """Its imports loaded first, then the module itself under an audit hook: no torch, and nothing opened
        but Python sources."""
        code = ("import os, sys\nsys.path.insert(0, sys.argv[1])\n"
                "import argparse, datetime, fnmatch, io, json, re, shlex, subprocess, tarfile, tempfile, decimal\n"
                "import fractions, benchmark_training, epa_roads, fingerprint\nfrom thresholds import common\n"
                "opened = []\n"
                "sys.addaudithook(lambda ev, a: opened.append(str(a[0])) if ev == 'open' and a else None)\n"
                "import epa_backend\n"
                "print(json.dumps(dict(torch='torch' in sys.modules, opened=[p for p in opened "
                "if not p.endswith(('.py', '.pyc'))])))\n")
        p = subprocess.run([sys.executable, "-B", "-c", code, HERE], capture_output=True, text=True, timeout=300,
                           env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        self.assertEqual(json.loads(p.stdout.strip().splitlines()[-1]), dict(torch=False, opened=[]))

    def test_redact_hides_a_run_of_12_digits(self):
        """redact, applied to every refusal text the tests store (train_all.py's can quote roads_seed): a run of 12
        digits is replaced (built here by multiplication, so this file holds no such run); the control, 11 digits,
        is kept."""
        self.assertEqual(redact("roads_seed " + "7" * 12 + " refused"), "roads_seed <integer> refused")
        self.assertEqual(redact("n " + "7" * 11), "n " + "7" * 11)

    def test_public_names_only(self):
        """No underscore name of another module (test_epa_rows' N12 scans epa_rows' and epa_freeze's)."""
        with open(os.path.join(HERE, EB.MODULE_REL), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        private = [f"{n.value.id}.{n.attr}" for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                   and isinstance(n.value, ast.Name) and n.value.id not in ("self", "fh", "tf", "e", "r", "p")
                   and n.attr.startswith("_") and not n.attr.startswith("__")]
        self.assertEqual(private, [])


class Scans(unittest.TestCase):
    """Unguarded: test_engine_threading's two scans of this module and its test. They import every plant module
    (train.py's torch among them) as test_engine_threading's own Names test does, outside forbid_real_data, so
    that an open made by another module's import is not read as this module's (Hygiene's import test is that)."""

    def test_test_engine_threadings_scans(self):
        import importlib
        import test_engine_threading as TET
        modules = {m: importlib.import_module(m) for m in TET.PLANT_MODULES}
        for rel in (EB.MODULE_REL, "test_epa_backend.py"):
            with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
                src = fh.read()
            with self.subTest(file=rel):
                self.assertEqual(TET.scan_source(src, rel), [])
                self.assertEqual(TET.scan_names(src, rel, modules), [])


# =====================================================================================================
class Preregistration(unittest.TestCase):
    """Unguarded. results/PREREGISTRATION_4E.md follows Tb (the sheet section 0): skipped while neither it nor the
    backend record is committed; a failure if it is present uncommitted, if it precedes the record, or if it stands
    beside a record whose n is null; once committed, every train_all.py command checked (section 11). Run 2 left
    no EPA engine, so the record's n is null and the file stays absent (row 136 (1); the sheet 17's 0 and 10.1):
    PR-B's results/PREREGISTRATION_B58H.md is PreregistrationB58H's."""

    def test_the_committed_preregistration_trains_what_the_record_allows(self):
        def read(rel):
            with open(os.path.join(HERE, *rel.split("/")), encoding="utf-8") as fh:
                return fh.read()
        verdict, why = preregistration_verdict(committed_state(EB.PREREGISTRATION_REL),
                                               committed_state(engines.BACKEND_REL),
                                               lambda: json.loads(read(engines.BACKEND_REL)),
                                               lambda: read(EB.PREREGISTRATION_REL))
        if verdict == "skip":
            self.skipTest(why)
        self.assertEqual(verdict, "pass", why)


class PreregistrationB58H(unittest.TestCase):
    """Unguarded (row 146 (5); the sheet 17's 10.1): PR-B's train_all.py commands, each read by b58h_problems and
    run through train_all.main() in-process (run_train_all, parsed_problems), train_all.py not edited for it. The
    first test reads the committed results/PREREGISTRATION_B58H.md: skipped until it is committed, a failure if
    skipped after (present and not committed, or removed after its commit). The others run from Ta on, on row 147
    (3)'s two commands as SYNTHETIC text, so that the check is seen to pass and to fail before PR-B exists."""

    def test_the_committed_preregistration_states_row_147s_commands(self):
        """b58h_verdict in this repository (LiveStates is its test): skipped until PR-B is committed, a failure if
        skipped after."""
        verdict, why = b58h_verdict()
        if verdict == "skip":
            self.skipTest(why)
        self.assertEqual(verdict, "pass", why)

    def test_what_a_command_is(self):
        """A fenced simple command is a train_all.py command when train_all.py is its program, after VAR=value
        words, an interpreter and its -B, or when --engine follows train_all.py; a `| tee` and a redirection end
        it. Row 146 (6)'s `git diff ... -- train.py train_all.py ...` and a `git log -- train_all.py` are
        mentions. Read by b58h_problems alone (no train_all.main() run). Each control fails by its own words: a
        program without --engine (an env word, $PY and -B before it), --engine after another program (nohup), and
        a stray word before the pipe."""
        T = TRAINING_147
        extra = ("\n```bash\ngit diff --cached --quiet abc1234 -- train.py train_all.py fingerprint.py\n"
                 "git log --format=%H -- train_all.py\n```\n\n```bash\nexport OMP_NUM_THREADS=1\n"
                 f"OMP_NUM_THREADS=1 $PY -B {T} 2>&1 | tee runs/b58h_dt1.log\n```\n")
        text = b58h_text(prose=extra)
        commands, problems = EB.b58h_commands(text)
        self.assertEqual(problems, [])
        self.assertEqual(sorted((where, EB.b58h_kind(tokens)) for where, tokens in commands),
                         [("fenced", "pilot"), ("fenced", "training"), ("fenced", "training"), ("prose", "training")])
        self.assertEqual([t for w, t in commands if w == "fenced" and EB.b58h_kind(t) == "training"][-1],
                         T.split()[1:])
        self.assertEqual(EB.b58h_problems(text, protocol=EB.PROTOCOL), [])
        for name, line, words in (
                ("a program without --engine", "OMP_NUM_THREADS=1 $PY -B train_all.py --seeds 0-19 --out runs/b58h_dt1",
                 "--engine: absent or repeated"),
                ("--engine after another program", "nohup $PY train_all.py --engine b58 --jobs 6 --out runs/b58h_dt1",
                 "--jobs '6', not '12'"),
                ("a stray word before the pipe", f"$PY {T} extra | tee runs/b58h_dt1.log",
                 "'extra' follows no flag that takes a value")):
            with self.subTest(name):
                probs = EB.b58h_problems(b58h_text(prose=f"\n```bash\n{line}\n```\n"), protocol=EB.PROTOCOL)
                self.assertTrue(any(words in p for p in probs), probs)

    def test_row_147s_two_commands_pass(self):
        """Row 147 (3)'s commands, in their fences and the training one in prose, pass; train_all.main() parses
        each as the row means it: the training line, seeds 0-19 at both ratios and blinded, 60 runs (row 147 (4):
        n = 20 an arm, three arms); the pilot line, seeds 2000-2004 blinded and at r = 1.5, 10 runs (row 146 (3):
        five pairs)."""
        import train_all
        text = b58h_text()
        commands, problems = EB.b58h_commands(text)
        self.assertEqual(problems, [])
        self.assertEqual(sorted((where, EB.b58h_kind(tokens)) for where, tokens in commands),
                         [("fenced", "pilot"), ("fenced", "training"), ("prose", "training")])
        self.assertEqual(EB.b58h_problems(text, protocol=EB.PROTOCOL), [])
        self.assertEqual(b58h_all_problems(text), [])
        for line, kind, n_runs in ((TRAINING_147, "training", 60), (PILOT_147, "pilot", 10)):
            with self.subTest(kind):
                res = run_train_all(line.split()[1:])
                self.assertEqual(res[0], "passed", res[1] if res[0] == "refused" else "")
                self.assertEqual(parsed_problems(res[1], res[2], kind), [])
                self.assertEqual(len(train_all.arms(res[1], res[2])), n_runs)

    def test_the_control_one_flag_changed_fails(self):
        """Mistake 12: row 147 (3)'s text with one flag changed fails, each with its own problem, by
        b58h_problems or by train_all.main() (run_train_all)."""
        T, P = TRAINING_147, PILOT_147
        cases = (("--jobs", dict(training=T.replace("--jobs 12", "--jobs 14")), "--jobs '14', not '12'"),
                 ("--device", dict(training=T.replace("--device cpu", "--device cuda")),
                  "--device 'cuda', not 'cpu'"),
                 ("--seeds", dict(training=T.replace("--seeds 0-19", "--seeds 0-18")), "--seeds '0-18', not '0-19'"),
                 ("--no-resume", dict(training=T.replace(" --no-resume", "")), "--no-resume: absent or repeated"),
                 ("--third-arm", dict(training=T.replace(" --third-arm", "")), "--third-arm: absent or repeated"),
                 ("--recipe29", dict(training=T.replace(" --recipe29", "")), "--recipe29: absent or repeated"),
                 ("--reward-knock", dict(training=T.replace("--reward-knock out", "--reward-knock in")),
                  "--reward-knock 'in', not 'out'"),
                 ("--steps", dict(training=T.replace("--steps 450000", "--steps 3000")),
                  "--steps '3000', not '450000'"),
                 ("--dt", dict(training=T.replace("--dt 1 ", "--dt 0.5 ")), "--dt '0.5', not 1.0"),
                 ("--roads-record", dict(training=T.replace("roads.json", "roads_copy.json")),
                  "--roads-record 'results/EPA_ROADS/roads_copy.json', not 'results/EPA_ROADS/roads.json'"),
                 ("--ratios on the training line",
                  dict(training=T.replace("--seeds 0-19", "--seeds 0-19 --ratios 1.5")),
                  "--ratios: not among the training line's flags"),
                 ("--blind-per-h", dict(training=T + " --blind-per-h"), "--blind-per-h: never"),
                 ("--keep-buffer", dict(training=T + " --keep-buffer"), "--keep-buffer: not among the training line's"),
                 ("--engine", dict(training=T.replace("--engine b58", "--engine ford_27tt")),
                  "--engine 'ford_27tt', not 'b58'"),
                 ("--out", dict(training=T.replace("runs/b58h_dt1", "runs/b58h_dt2")),
                  "is neither the training line's 'runs/b58h_dt1'"),
                 ("the pilot's --ratios", dict(pilot=P.replace("--ratios 1.5", "--ratios 0.5")),
                  "--ratios '0.5', not '1.5'"),
                 ("the pilot's two ratios", dict(pilot=P.replace("--ratios 1.5", "--ratios 0.5 1.5")),
                  "'1.5' follows no flag that takes a value"),
                 ("the pilot's --seeds", dict(pilot=P.replace("--seeds 2000-2004", "--seeds 2000-2009")),
                  "--seeds '2000-2009', not '2000-2004'"),
                 ("no pilot line", dict(pilot=None), "no fenced pilot line"),
                 ("a prose command", dict(prose="\nThen `train_all.py --engine b58 --jobs 6 --out runs/b58h_dt1`.\n"),
                  "the prose command"),
                 ("a bare command", dict(prose="\nThen run train_all.py --engine b58 --jobs 6.\n"),
                  "outside a fenced block and a code span"))
        for name, kw, words in cases:
            with self.subTest(name):
                probs = b58h_all_problems(b58h_text(**kw))
                self.assertTrue(any(words in p for p in probs), probs)

    def test_the_control_train_all_main_runs_its_own_checks(self):
        """main() runs its own parser and check_four_engine before the stand-in, each refusal matched by its text;
        and a line it takes with one value changed is caught by parsed_problems (the control of that check)."""
        T, P = TRAINING_147, PILOT_147
        for line, words in (
                (T.replace(" --reward-knock out", ""), "REFUSING: --road four_engine needs --reward-knock"),
                (P.replace("--ratios 1.5", "--ratios 0.7"), "REFUSING --ratios [0.7]: each must be one of"),
                (T.replace("--engine b58", "--engine ford_27tt"), "invalid choice: 'ford_27tt'"),
                (T.replace("--seeds 0-19", "--seeds 1000-1019"), "REFUSING --seeds on the four-engine roads"),
                (T + " --keep-buffer", "--keep-buffer exists for resuming; --no-resume forbids it"),
                (T + " --blind-per-h", "unrecognized arguments: --blind-per-h"),
                (T.replace("roads.json", "roads_copy.json"), "no roads record there")):
            with self.subTest(words):
                res = run_train_all(line.split()[1:])
                self.assertEqual(res[0], "refused")
                self.assertIn(words, res[1])
        res = run_train_all(T.replace("--jobs 12", "--jobs 14").split()[1:])
        self.assertEqual(res[0], "passed", res[1] if res[0] == "refused" else "")
        self.assertEqual(parsed_problems(res[1], res[2], "training"), ["jobs 14, not 12"])
        res = run_train_all(P.split()[1:])                    # the pilot line read as the training line
        self.assertEqual(res[0], "passed", res[1] if res[0] == "refused" else "")
        probs = parsed_problems(res[1], res[2], "training")
        for words in ("seeds [2000, 2001, 2002, 2003, 2004], not [0, 1, 2,", "out 'runs/b58h_pilot_dt1', not",
                      "ratios [1.5], not None", "the training's sighted ratios are [1.5], not every ratio",
                      "train_all would start 10 runs"):
            self.assertTrue(any(p.startswith(words) for p in probs), (words, probs))
        self.assertEqual(parsed_problems(res[1], res[2], "pilot"), [])


class LiveRecord(unittest.TestCase):
    """Unguarded: the committed results/EPA_BACKEND.json is what the committed inputs give (check, []). Skipped while
    it was never committed; a failure if it is present and not committed, or removed after its commit
    (live_record_verdict; LiveStates is its test)."""

    def test_the_committed_record_is_the_committed_inputs(self):
        verdict, why = live_record_verdict()
        if verdict == "skip":
            self.skipTest(why)
        self.assertEqual(verdict, "pass", why)


if __name__ == "__main__":
    unittest.main(verbosity=2)
