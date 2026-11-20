"""test_b58h_beside.py -- b58h_beside.py: --list and the core route, PR-B sections 9.5 (i), 9.5 (v) and 9.6.

    python -B -m unittest test_b58h_beside -v       synthetic throughout; exit code 0 when all pass

Every score, record, index, report and roads record here is SYNTHETIC, built by this file in tempfile folders
outside the repository (evaluate.scores_document, write_once_json, write_records and d34_report build them, so
the fixtures are the d34 route's own formats), committed in a temporary git repository where committed_at_head is
what is tested. hw_opt's report and the grids print are copies of the committed files. No agent, checkpoint or
real road is opened: evaluate.load_agent, read_agents and average_lines are patched to raise for the whole
module, and an audit hook refuses any open under runs/b58h_dt1, runs/b58h_check_dt1, logs/epa,
data/engines/*/epa_*.csv, results/EPA_ROADS/attempt_1_printed.txt and the row-96 integers file. Current-grade's
road runner (evaluate.run_road_episode) is a deterministic fake everywhere but RealShortRoads, which runs
check_premise.p_grade_now on two eight-sample roads (test_scoring_protocol.short_road's pattern).

Each computation is checked against a computation of its own here, with a control that FAILS (mistake 12):
  Cli            --list prints the routes, needs no subcommand and writes nothing; no route is refused
  EndToEnd       the six files, written once (and each writer refuses an existing file itself); the .json and .txt
                 LF on every platform, the printed sha256 the file's own; dt float64; nothing of commit_reveal
                 printed; ASCII; the refusals of the whole command (an uncommitted scores or roads.json, a D_base
                 that is not one list in either reading, a load_scores refusal, --out inside the repository or
                 inside the module's own folder with another root), each with the passing run beside it
  CurrentGrade   the call is score_set's for a hand-written policy; decision 34's roads refused, or another count
                 of them, or not the scored ones, or the run failing on a road (an exception, a refusal, unequal
                 step counts) reads 9.5 (i) "not computed" while 9.5 (v) and 9.6 run, and the command still writes
                 its files; the roads check records its own outcome (NOT RUN, FAIL with its detail exact, and PASS,
                 passed True itself, when the run failed after it); a refusal's line breaks (inside it too, a CR
                 alone, every break str.splitlines knows, a whitespace-only line) do not split a printed line, nor
                 run_cg's own RuntimeError text
  Controls       control 1 (one road's fuel off by one ulp fails, road 5 and the last road; its detail exact),
                 control 2 (each reading's value moved fails, and its detail is exact: the report's line first,
                 the run's second, both readings named with the label; a CRLF report passes; an uncommitted one
                 fails; a git failure of several lines reads on one line; exactly one line, after the header, which
                 must be there; evaluate's header and line format), control 3 (an absolute 2e-6 fails, 0.5e-6
                 passes, exactly 1e-6 passes and one ulp more fails, in either reading and on the last road, and
                 the savings still print with the differences; the largest relative difference on its own road;
                 roads out of order fail)
  Savings        s against statistics.median by hand, both forms and readings; current-grade's own cut in both
                 forms; the per-arm count, median, sd (ddof 1, not 0) and range of each form; s = 0 is not below 0;
                 a cut against another base differs; the hand-written savings read (evaluate_form) and recomputed
                 (the mean form over D_neutral, not roads.json's mean or D_base)
  TunedBests     the largest saving in evaluate.py's form (not the mean form's), ties, the two frontier lines of
                 its own reading (another reading's block in the section is not read); the committed report
                 parses; refusals; decision 13's lines (the rule and the b58's count; exactly 100 lines suffice);
                 not committed reads "not read" and nothing else stops
  Delivery       the fuel figure, the mean and pooled short shares, their differences, intervals against
                 scipy.stats.t.interval, the sign count, a seed with no demand step in either arm dropped and
                 named, reactive not beside; every refusal of the block with its control; a refused block reads
                 9.5 (v) "not computed"
  Temperatures   peak, strict exceedance (an exact 778 is not above it), dt scaling; per agent, arm and seed
                 against hand sums; every integrity refusal (a record's sha256, the index's scores_sha256, a
                 missing or extra file, an uncommitted index, an index that is not JSON or is nested too deep for
                 json, a record that does not load: not a zip, a truncated npz, a bare .npy, a .npy header numpy
                 refuses in several lines; a record without dt or without t_turb, dt 2 s or not a 0-d float64 (1-d,
                 2-d, a str, raw bytes, complex, bool, int), a shape, a NaN, float32, every record one road short,
                 every t_turb 1-d) reads 9.6 "not computed", on one line, while 9.5 (i) and (v) run; _load_record
                 closes its file (no ResourceWarning on a good or a truncated record); sha_text, not the raw sha256,
                 of a CRLF scores file; 850 deg C in both readings, each by its own trigger at >= (a peak exactly
                 at the knee triggers; an agent's or the baseline ECU's peak sets it off; seconds above the knee
                 and above 850 against hand counts); current-grade's peak counted only when its row is computed;
                 its trace of another shape drops its row
  RealShortRoads current-grade through evaluate.run_road_episode at jobs 1 and 2, equal; p_neutral differs
  Guard          the guard fires; core's code names no agent loader; every np.load refuses pickles
  Text           no phrase PR-B 7 forbids in core's report, and the scan finds one when injected; every line that
                 names the with-knock reading, or holds a bracketed number, carries its label, and so does every
                 line under the tuned bests' knock heading (none under the no-knock one); current-grade's cut line
                 exactly; each reading's numbers under its own name (control 3's lines, and each arm's statistics,
                 per-seed s and hand-written savings, line by line); the printed decimals (s, seconds and 9.6's
                 temperatures: every peak, the limits, the knee in K and deg C; the summaries, 9.5 (v)'s fuel
                 figure and shares)
"""
import ast
import contextlib
import gc
import io
import json
import os
import re
import shutil
import stat
import statistics
import struct
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from unittest import mock

import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import b58h_analysis as AB      # noqa: E402
import b58h_beside as BS        # noqa: E402
import check_premise as CP      # noqa: E402
import engines                  # noqa: E402
import epa_backend as EB        # noqa: E402
import epa_freeze as EF         # noqa: E402
import epa_roads as ER          # noqa: E402
import evaluate as V            # noqa: E402
import four_engine_analysis as FEA  # noqa: E402
from thresholds import common as TC  # noqa: E402

N = V.N_D34_ROADS
STEPS = 12
SEEDS = list(range(EB.B58H_N))
RATIOS = ["0.5", "1.5"]
SENTINEL = "SYNTHETIC-ROADS-SEED-NEVER-PRINTED"
FORBIDDEN = ("a test of the criterion", "a collapse", "H/tau governs", "H/\u03c4 governs", "the criterion holds",
             "the criterion fails", "preview does not help")
STATE = {}


# ------------------------------------------------------------------------------------------ the guard
def _norm(p):
    return os.path.normcase(os.path.abspath(p))


GUARD = {"on": 0, "hits": [], "installed": False,
         "prefixes": [_norm(os.path.join(HERE, *p)) + os.sep for p in
                      (("runs", "b58h_dt1"), ("runs", "b58h_check_dt1"), ("logs", "epa"))],
         "files": {_norm(os.path.join(HERE, "results", "EPA_ROADS", "attempt_1_printed.txt"))},
         "engines": _norm(os.path.join(HERE, "data", "engines")) + os.sep}


def _forbidden(path):
    p = _norm(path)
    if p in GUARD["files"] or any(p.startswith(x) or p + os.sep in x for x in GUARD["prefixes"]):
        return True
    base = os.path.basename(p)
    return (p.startswith(GUARD["engines"]) and base.startswith("epa_") and base.endswith(".csv")) or \
        "grad_row96_integers" in base


def _hook(event, args):
    if event != "open" or not GUARD["on"] or not args or not isinstance(args[0], (str, bytes, os.PathLike)):
        return
    path = os.fsdecode(args[0])
    if _forbidden(path):
        GUARD["hits"].append(path)
        raise PermissionError(f"test_b58h_beside's guard: an open of {path}")


def _loader(*a, **kw):
    raise AssertionError("an agent loader was called inside test_b58h_beside")


def setUpModule():
    if not GUARD["installed"]:
        sys.addaudithook(_hook)
        GUARD["installed"] = True
    GUARD["on"] += 1
    STATE["patches"] = [mock.patch.object(V, name, _loader) for name in ("load_agent", "read_agents", "average_lines")]
    for p in STATE["patches"]:
        p.start()
    tmp = tempfile.mkdtemp(prefix="b58h_beside_test_")
    assert not BS.inside(tmp, HERE), tmp
    STATE["tmp"] = tmp


def _make_writable(func, path, exc):
    """rmtree's onexc: git writes its objects read-only, which Windows will not delete; make one writable, retry."""
    os.chmod(path, stat.S_IWRITE)
    func(path)


def tearDownModule():
    for p in STATE.get("patches", []):
        p.stop()
    GUARD["on"] -= 1
    tmp = STATE.pop("tmp", None)
    STATE.pop("fx", None)                               # the shared fixture lives in tmp
    STATE.pop("res", None)
    if tmp and os.path.isdir(tmp):
        shutil.rmtree(tmp, onexc=_make_writable)        # the temporary repositories' read-only objects too


class Case(unittest.TestCase):
    def tearDown(self):
        hits, GUARD["hits"][:] = list(GUARD["hits"]), []
        self.assertEqual(hits, [], "a forbidden path was opened")


def fresh(name):
    return tempfile.mkdtemp(prefix=name + "_", dir=STATE["tmp"])


@contextlib.contextmanager
def quiet():
    with contextlib.redirect_stdout(io.StringIO()) as buf:
        yield buf


def git(root, *args):
    r = subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@local", *args], cwd=root,
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise AssertionError(f"git {' '.join(args)}: {r.stderr.strip()}")
    return r.stdout


def put_json(root, rel, obj):
    path = os.path.join(root, *rel.split("/"))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(obj, fh)
    return path


def put_bytes(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


# ------------------------------------------------------------------------------------------ SYNTHETIC fixtures
def make_rows(*, steps=STEPS, seed=11):
    """score_set's layout with SYNTHETIC numbers and traces: every hand-written policy and 20 seeds x 3 arms on
    N roads. Blind seed 3 has no demand step on any road; the baseline ECU has none on road 1."""
    rng = np.random.default_rng(seed)

    def row(level, lo_k, hi_k, demand=True):
        dth = float(rng.uniform(40.0, 80.0)) * level
        tt = (lo_k + (hi_k - lo_k) * rng.random(steps)).tolist()
        dem = int(rng.integers(50, 120)) if demand else 0
        return dict(ret=0.0, damage=dth + float(rng.uniform(1.0, 4.0)), damage_thermal=dth,
                    fuel=float(rng.uniform(900.0, 1000.0)), torque_viol=0.0, peak_turb=max(tt) - 273.15, knock=0,
                    steps=steps, demand_steps=dem, short_steps=int(rng.integers(0, 10)) if demand else 0,
                    fuel_base=950.0, damage_base=dth,
                    trace={"t_turb": tt, "t_oil": (380.0 + 10.0 * rng.random(steps)).tolist(),
                           "ki": (0.5 * rng.random(steps)).tolist()})
    hand = {V.BASELINE: [row(1.0, 1045.0, 1098.0, demand=(k != 1)) for k in range(N)],
            "reactive": [row(0.9, 1040.0, 1096.0) for _ in range(N)],
            BS.CG: [row(0.7, 1040.0, 1094.0) for _ in range(N)]}
    agents = {}
    for s in SEEDS:
        for arm in BS.ARMS:
            level = float(rng.uniform(0.6, 0.8))
            agents[(arm, s)] = [row(level, 1035.0, 1095.0, demand=not (arm == "blind" and s == 3)) for _ in range(N)]
    return {"hand": hand, "agents": agents}


def make_roads(steps=STEPS):
    """N SYNTHETIC roads: what decision34_roads returns, cycles long enough for epa_roads.arrays_sha256."""
    roads = []
    for k in range(N):
        t = [float(i) for i in range(steps + 1)]
        roads.append({"k": k, "episode_seed": V.EPISODES[k][0], "weights": [float(w) for w in V.EPISODES[k][1]],
                      "dt": 1.0, "cycle": {"t": t, "v_mps": [20.0 + 0.1 * k] * len(t),
                                           "grade": [0.01 * (i % 5) for i in range(len(t))],
                                           "t_amb": [315.0] * len(t), "p_baro": 101.3, "humidity": 0.012}})
    return roads


def scaled(rows_of_policy, factor, reading):
    key = V.READING_KEYS[reading]
    return [factor * float(r[key]) for r in rows_of_policy]


def roads_record(rows, *, knee_k):
    """A SYNTHETIC roads.json: per_road D (neutral = the baseline ECU's rows, so control 3 passes), a decoy
    per_road D_base (the parallel network's, never to be used) and decoy `mean` fields, the hand-written
    evaluate_form computed as roads_ceiling computes it, the knee, and secret keys that must never be printed."""
    base, cg = rows["hand"][V.BASELINE], rows["hand"][BS.CG]
    factors = {"a@0.5": 0.98, "a@1.5": 0.95, "b": 0.93, "a_b": 0.97}
    per_road = []
    for k in range(N):
        D = {"neutral": {"noknock": base[k]["damage_thermal"], "knock": base[k]["damage"]},
             "cg": {"noknock": cg[k]["damage_thermal"], "knock": cg[k]["damage"]}}
        for name, f in factors.items():
            D[name] = {"noknock": f * cg[k]["damage_thermal"] * (1.0 + 0.01 * (k % 3)),
                       "knock": f * cg[k]["damage"] * (1.0 + 0.01 * (k % 4))}
        per_road.append({"k": k, "D": D, "D_base": {"noknock": 1.0, "knock": 1.0}})
    by = {}
    for r in RATIOS:
        by[r] = {}
        for pol in BS.HW_POLICIES:
            key = f"a@{r}" if pol == "a" else pol
            by[r][pol] = {}
            for rj in ("noknock", "knock"):
                cgd = np.array([p["D"]["cg"][rj] for p in per_road])
                x = np.array([p["D"][key][rj] for p in per_road])
                nd = np.array([p["D"]["neutral"][rj] for p in per_road])
                by[r][pol][rj] = {"evaluate_form": float(100.0 * (np.median(cgd) - np.median(x)) / np.median(nd)),
                                  "mean": 999.0, "median": 999.0, "pooled": 999.0, "per_road": []}
    return {"schema": "epa-roads/1", "seed_kind": "SYNTHETIC",
            "ceilings": {"readings": ["noknock", "knock"],
                         "per_engine": {"b58": {"by": by, "per_road": per_road}}},
            "report": {"knee_shares": {"b58": {"turb_knee_k": float(knee_k)}}},
            "commit_reveal": {"roads_seed": SENTINEL}, "attempts": [SENTINEL], "steps_log": [SENTINEL]}


def fake_roads(roads):
    def decision34_roads(*, root):
        return [dict(r) for r in roads], {"arrays_sha256": ER.arrays_sha256(roads)}
    return decision34_roads


def fake_runner(rows, *, calls=None, fuel_of=None, trace_of=None):
    """evaluate.run_road_episode's stand-in: current-grade's synthetic row of road k, its kwargs recorded."""
    def run_road_episode(policy, road, *, plant, use_preview, preview_h_s, reward_knock, record=None):
        k = road["k"]
        if calls is not None:
            calls.append(dict(policy=policy, k=k, plant=plant, use_preview=use_preview, preview_h_s=preview_h_s,
                              reward_knock=reward_knock, record=record))
        src = rows["hand"][BS.CG][k]
        out = {key: src[key] for key in ("damage_thermal", "damage", "fuel", "demand_steps", "short_steps", "steps",
                                         "peak_turb", "ret", "knock", "torque_viol", "fuel_base", "damage_base")}
        if fuel_of is not None:
            out["fuel"] = fuel_of(k, out["fuel"])
        trace = {key: list(v) for key, v in src["trace"].items()}
        if trace_of is not None:
            trace = trace_of(k, trace)
        out["trace"] = trace
        return out
    return run_road_episode


REAL_HW = os.path.join(HERE, *BS.HW_OPT_REPORT.split("/"))
REAL_GRIDS = os.path.join(HERE, *BS.GRIDS.split("/"))


class Fixture:
    """A temporary repository holding a SYNTHETIC roads.json, copies of hw_opt's report and the grids print, and
    the d34 route's three files (scores, index, report), committed; the 61 records outside it."""

    def __init__(self, name, *, knee_k=1123.0, rows=None, mutate_doc=None, mutate_roads_record=None):
        self.base = fresh(name)
        self.root = os.path.join(self.base, "repo")
        self.records = os.path.join(self.base, "records")
        self.out = os.path.join(self.base, "out")
        os.makedirs(self.root)
        self.rows = rows if rows is not None else make_rows()
        self.roads = make_roads()
        rec = roads_record(self.rows, knee_k=knee_k)
        if mutate_roads_record:
            mutate_roads_record(rec)
        roads_path = put_json(self.root, BS.ROADS, rec)
        for src, rel in ((REAL_HW, BS.HW_OPT_REPORT), (REAL_GRIDS, BS.GRIDS)):
            with open(src, "rb") as fh:
                put_bytes(os.path.join(self.root, *rel.split("/")), fh.read())
        prov = {"protocol": V.DECISION_34, "reading": V.REDRAW_READING, "reward_knock": False,
                "roads_sha": TC.sha_text(roads_path), "arrays_sha256": ER.arrays_sha256(self.roads),
                "made_by": "test_b58h_beside: SYNTHETIC, no agent"}
        doc = V.scores_document("b58", self.rows, ratios=RATIOS, provenance=prov)
        if mutate_doc:
            mutate_doc(doc)
        self.doc = doc
        self.scores = os.path.join(self.root, "results", "B58H_RESULT", "scores_b58h.json")
        self.sha = V.write_once_json(self.scores, doc)
        self.files = V.write_records(self.records, "b58", self.rows, dt=1.0)
        self.index = V.records_index_path(self.scores)
        V.write_once_json(self.index, {"files": self.files, "scores_sha256": self.sha, "command": "SYNTHETIC"})
        self.report = os.path.splitext(self.scores)[0] + ".txt"
        lines = V.d34_report("b58", self.rows, header=V.D34_HEADER, reading=V.REDRAW_READING, ratios=RATIOS,
                             lines=[])
        self.write_text(self.report, "\n".join(lines) + "\n")
        git(self.root, "init", "-q")
        git(self.root, "config", "core.autocrlf", "true")
        self.commit()

    def write_text(self, path, text, newline="\n"):
        with open(path, "w", encoding="utf-8", newline=newline) as fh:
            fh.write(text)

    def commit(self):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "--allow-empty", "-m", "SYNTHETIC")

    @contextlib.contextmanager
    def patched(self, runner=None, roads=None):
        with mock.patch.object(V, "decision34_roads", roads or fake_roads(self.roads)), \
                mock.patch.object(V, "run_road_episode", runner or fake_runner(self.rows)):
            yield

    def compute(self, runner=None, roads=None):
        with self.patched(runner=runner, roads=roads), quiet():
            res, trace, dt = BS.compute(scores=self.scores, records=self.records, jobs=1, root=self.root)
        return res

    def main(self, *extra, runner=None, out=None):
        argv = ["core", "--scores", self.scores, "--records", self.records, "--out", out or self.out,
                "--jobs", "1", *extra]
        with self.patched(runner=runner), quiet() as buf:
            code = BS.main(argv, root=self.root)
        return code, buf.getvalue()


def shared():
    if "fx" not in STATE:
        STATE["fx"] = Fixture("shared")
        STATE["res"] = STATE["fx"].compute()
    return STATE["fx"], STATE["res"]


def cut_by_hand(D, D_base):
    return 100.0 * (1.0 - statistics.median(D) / statistics.median(D_base))


ROADS_PASS = {"passed": True, "detail": "arrays_sha256 equal"}
ROADS_HEAD = "  the roads check (epa_roads.arrays_sha256 against the scores' provenance.arrays_sha256): "
BRACKET_NUMBER = re.compile(r"(?<!interval )\[\s*[+-]?\d+\.\d+")


def roads_line(res):
    """The roads check's printed verdict and detail, read from the rendered report."""
    lines = [ln for ln in BS.render(res) if ln.startswith(ROADS_HEAD)]
    assert len(lines) == 1, lines
    return lines[0][len(ROADS_HEAD):]


BREAKS = re.compile("[\n\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")    # every break str.splitlines splits at


def broken(lines):
    """Printed lines that a line break inside them would split in b58h_core.txt (R2-2)."""
    return [ln for ln in lines if BREAKS.search(ln)]


def unlabelled(lines):
    """Printed lines holding a bracketed number (the with-knock reading's place in evaluate.py's line and in core's
    own), other than a t interval and control 2's expected and found lines, that do not carry the label."""
    return [ln for ln in lines if BRACKET_NUMBER.search(ln) and FEA.WITH_KNOCK_LABEL not in ln
            and not ln.startswith(("    expected ", "    found    "))]


# ------------------------------------------------------------------------------------------ Cli
class Cli(Case):
    def test_list_prints_the_routes_and_writes_nothing(self):
        with quiet() as buf:
            self.assertEqual(BS.main(["--list"]), 0)
        self.assertEqual(buf.getvalue(), "core\n")
        cwd = fresh("list")
        r = subprocess.run([sys.executable, "-B", os.path.join(HERE, "b58h_beside.py"), "--list"], cwd=cwd,
                           capture_output=True, text=True)
        self.assertEqual((r.returncode, r.stdout), (0, "core\n"))          # as step 3 runs it (PR-B:1790)
        self.assertEqual(os.listdir(cwd), [])                               # it wrote nothing
        self.assertEqual(BS.ROUTES, ("core",))

    def test_no_route_is_refused(self):                                     # the control: --list is needed
        for argv in ([], ["--list", "core", "--scores", "s", "--records", "r", "--out", "o"]):
            with self.assertRaises(SystemExit) as cm, contextlib.redirect_stderr(io.StringIO()):
                BS.main(argv)
            self.assertEqual(cm.exception.code, 2)


# ------------------------------------------------------------------------------------------ EndToEnd
class EndToEnd(Case):
    def test_the_six_files_written_once(self):
        fx = Fixture("e2e")
        code, printed = fx.main()
        self.assertEqual(code, 0)
        self.assertEqual(sorted(os.listdir(fx.out)), sorted(BS.OUT_FILES))
        with open(os.path.join(fx.out, "b58h_core.json"), encoding="utf-8") as fh:
            text = fh.read()
        res = json.loads(text)
        self.assertEqual(text, json.dumps(res, indent=1, sort_keys=True) + "\n")
        self.assertEqual(res["schema"], BS.SCHEMA)
        self.assertEqual([res[k]["status"] for k in ("part_9_5_i", "part_9_5_v", "part_9_6")], ["computed"] * 3)
        for name in ("b58h_core.json", "b58h_core.txt"):                    # LF on every platform (Windows too)
            with open(os.path.join(fx.out, name), "rb") as fh:
                self.assertNotIn(b"\r", fh.read(), name)
        printed_sha = re.search(r"b58h_core\.json sha256 ([0-9a-f]{64})$", printed.rstrip("\n")).group(1)
        self.assertEqual(printed_sha, AB.sha256_file(os.path.join(fx.out, "b58h_core.json")))   # the file's own
        self.assertEqual(printed_sha, TC.sha_text(os.path.join(fx.out, "b58h_core.json")))
        self.assertEqual(res["report_sha256"], AB.sha256_file(os.path.join(fx.out, "b58h_core.txt")))
        npz = os.path.join(fx.out, "current_grade.npz")
        self.assertEqual(res["current_grade"]["npz"]["sha256"], AB.sha256_file(npz))
        with np.load(npz, allow_pickle=False) as z:
            self.assertEqual(sorted(z.files), ["dt", "ki", "t_oil", "t_turb"])
            self.assertEqual((z["dt"].shape, z["dt"].dtype, float(z["dt"])), ((), np.float64, 1.0))
            for key in BS.TRACE_KEYS:
                self.assertEqual((z[key].dtype, z[key].shape), (np.float64, (N, STEPS)))
            want = np.array([r["trace"]["t_turb"] for r in fx.rows["hand"][BS.CG]])
            self.assertTrue(np.array_equal(z["t_turb"], want))
        with open(os.path.join(fx.out, "b58h_core.txt"), encoding="utf-8") as fh:
            report = fh.read()
        self.assertTrue(printed.startswith(report))
        for name in ("b58h_core_s.png", "b58h_core_delivery.png", "b58h_core_temps.png"):
            with open(os.path.join(fx.out, name), "rb") as fh:
                self.assertEqual(fh.read(8), b"\x89PNG\r\n\x1a\n")
        for blob in (text, report):
            self.assertNotIn(SENTINEL, blob)                                # commit_reveal & co. never printed
        report.encode("ascii")
        self.assertIn(FEA.WITH_KNOCK_LABEL, report)
        with self.assertRaises(SystemExit) as cm:                           # the control: written once
            fx.main()
        self.assertIn("already holds", str(cm.exception))

    def test_each_writer_opens_its_file_once(self):
        folder = fresh("once")
        js, nz = os.path.join(folder, "x.json"), os.path.join(folder, "x.npz")
        sha = BS.write_json_once(js, {"a": 1})
        trace = {k: np.zeros((2, 3)) for k in BS.TRACE_KEYS}
        BS.write_npz_once(nz, trace, 1.0)                                   # the control: a new file is written
        self.assertEqual(sha, AB.sha256_file(js))
        before = {p: AB.sha256_file(p) for p in (js, nz)}
        for write in (lambda: BS.write_json_once(js, {"a": 2}), lambda: BS.write_npz_once(nz, trace, 2.0)):
            with self.assertRaises(SystemExit) as cm:                       # the writer itself refuses, not only
                write()                                                     # run_core's check of --out
            self.assertIn("each output is written once", str(cm.exception))
        self.assertEqual({p: AB.sha256_file(p) for p in (js, nz)}, before)

    def test_a_part_not_computed_still_draws_its_figure(self):
        fx = Fixture("e2e_nc")
        os.remove(os.path.join(fx.records, "b58", "blind_seed0.npz"))
        code, _ = fx.main()
        self.assertEqual(code, 0)
        with open(os.path.join(fx.out, "b58h_core.json"), encoding="utf-8") as fh:
            res = json.load(fh)
        self.assertTrue(res["part_9_6"]["status"].startswith("not computed: the record b58/blind_seed0.npz"))
        self.assertTrue(os.path.isfile(os.path.join(fx.out, "b58h_core_temps.png")))

    def test_refusals_of_the_whole_command(self):
        fx = Fixture("e2e_ref")
        out_in = os.path.join(fx.root, "beside")
        with self.assertRaises(SystemExit) as cm:
            fx.main(out=out_in)
        self.assertIn("inside the repository", str(cm.exception))
        here_out = os.path.join(HERE, "__b58h_beside_out_never_written__")  # the module's own folder, root elsewhere
        self.assertFalse(BS.inside(here_out, fx.root))
        self.assertFalse(os.path.exists(here_out))
        with mock.patch.object(BS, "compute", side_effect=AssertionError("core ran with --out in HERE")), \
                self.assertRaises(SystemExit) as cm:                        # compute patched: nothing can be
            fx.main(out=here_out)                                           # written there, even by a mutant
        self.assertIn("inside the repository", str(cm.exception))
        self.assertFalse(os.path.exists(here_out))
        with self.assertRaises(SystemExit) as cm, quiet():
            BS.main(["core", "--scores", fx.scores, "--records", fx.records, "--out", fx.out, "--jobs", "0"],
                    root=fx.root)
        self.assertIn("--jobs 0", str(cm.exception))
        self.assertFalse(os.path.exists(fx.out))
        with open(fx.scores, "a", encoding="utf-8", newline="\n") as fh:   # not committed any more
            fh.write("\n")
        with self.assertRaises(SystemExit) as cm:
            fx.compute()
        self.assertIn("not committed at HEAD", str(cm.exception))
        fx.commit()
        self.assertEqual(fx.compute()["part_9_6"]["status"], "not computed: the records index's scores_sha256 "
                         f"({fx.sha[:12]}) is not the committed scores file's sha_text "
                         f"({TC.sha_text(fx.scores)[:12]})")                 # the control: committed, core runs
        git(fx.root, "rm", "-q", "--cached", BS.ROADS)                     # present and unchanged, not in HEAD
        git(fx.root, "commit", "-q", "-m", "SYNTHETIC: roads.json left out of HEAD")
        with self.assertRaises(SystemExit) as cm:
            fx.compute()
        self.assertIn(f"{BS.ROADS}: not committed at HEAD", str(cm.exception))

    def test_d_base_must_be_one_list_and_load_scores_refusals_are_core_s(self):
        def nudge(doc):
            d = doc["engines"]["b58"]["arms"]["sighted_r1.5"]["seeds"]["4"]["no_knock"]["D_base"]
            d[2] = d[2] * (1.0 + 1e-12)                                     # inside FEA's 1e-9, not exact
        with self.assertRaises(SystemExit) as cm:
            Fixture("dbase", mutate_doc=nudge).compute()
        self.assertIn("D_base (no_knock) differs", str(cm.exception))

        def nudge_knock(doc):                                               # the with-knock reading is checked too
            d = doc["engines"]["b58"]["arms"]["blind"]["seeds"]["11"]["with_knock"]["D_base"]
            d[N - 1] = d[N - 1] * (1.0 + 1e-12)
        with self.assertRaises(SystemExit) as cm:
            Fixture("dbase_k", mutate_doc=nudge_knock).compute()
        self.assertIn("D_base (with_knock) differs", str(cm.exception))

        def variant(doc):
            doc["variant"] = "c_turb x0.75"
        with self.assertRaises(SystemExit) as cm:
            Fixture("variant", mutate_doc=variant).compute()
        self.assertIn("variant", str(cm.exception))
        self.assertEqual(shared()[1]["part_9_5_i"]["status"], "computed")   # the control


# ------------------------------------------------------------------------------------------ CurrentGrade
class CurrentGrade(Case):
    def test_the_call_is_score_set_s(self):
        fx, _ = shared()
        calls = []
        fx.compute(runner=fake_runner(fx.rows, calls=calls))
        self.assertEqual([c["k"] for c in calls], list(range(N)))
        for c in calls:
            self.assertIs(c["policy"], CP.p_grade_now)
            self.assertIsNot(c["policy"], CP.p_reactive)
            self.assertIs(c["use_preview"], True)
            self.assertIs(type(c["preview_h_s"]), float)
            self.assertEqual(c["preview_h_s"], V.PREVIEW_H_S)
            self.assertIs(c["reward_knock"], False)
            self.assertIsNone(c["record"])
            self.assertEqual(c["plant"], engines.get("b58"))
        self.assertEqual(dict(V.HAND_POLICIES)[BS.CG], "p_grade_now")
        self.assertEqual(BS.CG, "current-grade")

    def test_roads_refused_or_not_the_scored_ones(self):
        fx, base = shared()
        self.assertEqual(base["controls"]["roads"], ROADS_PASS)             # the control
        self.assertIs(base["controls"]["roads"]["passed"], True)            # True itself: the JSON's true, not 1
        self.assertEqual(roads_line(base), "PASS: arrays_sha256 equal")

        def refused(*, root):                                               # a break inside it, not only before it
            raise SystemExit("\nREFUSING decision 34's roads: SYNTHETIC first line\n  SYNTHETIC second line")
        res = fx.compute(roads=refused)
        why = "decision 34's roads refused: REFUSING decision 34's roads: SYNTHETIC first line SYNTHETIC second line"
        self.assertEqual(broken(BS.render(res)), [])                        # R2-2: no printed line split
        self.assertEqual(res["part_9_5_i"]["status"], "not computed: " + why)
        self.assertEqual(res["part_9_5_v"]["status"], "computed")
        self.assertEqual(res["part_9_6"]["status"], "computed")
        self.assertIsNone(res["part_9_6"]["current_grade"])
        self.assertTrue(res["part_9_6"]["current_grade_note"].startswith("not computed: decision 34's roads"))
        self.assertEqual(res["controls"]["roads"], {"passed": None, "detail": why})   # the check never ran (D1)
        self.assertEqual(roads_line(res), "NOT RUN: " + why)
        res = fx.compute(roads=fake_roads(make_roads()[:-1]))               # another count of roads: not run
        why = f"decision 34's roads are {N - 1}, the scores' {N}"
        self.assertEqual(res["part_9_5_i"]["status"], "not computed: " + why)
        self.assertEqual(res["controls"]["roads"], {"passed": None, "detail": why})
        other = make_roads()
        other[7]["cycle"]["grade"][3] += 0.001
        res = fx.compute(roads=fake_roads(other))
        got, want = ER.arrays_sha256(other), ER.arrays_sha256(fx.roads)    # the roads run, and the scored ones
        self.assertNotEqual(got[:12], want[:12])
        detail = (f"epa_roads.arrays_sha256 of decision 34's roads ({got[:12]}) is not the scores' "
                  f"provenance.arrays_sha256 ({want[:12]})")                 # each prefix its own, never X is not X
        self.assertEqual(res["part_9_5_i"]["status"], "not computed: the roads check failed: " + detail)
        self.assertEqual(res["part_9_5_v"]["status"], "computed")
        self.assertIs(res["controls"]["roads"]["passed"], False)            # it ran, and failed
        self.assertEqual(res["controls"]["roads"], {"passed": False, "detail": detail})
        self.assertEqual(roads_line(res), "FAIL: " + detail)

    def assert_i_not_computed(self, res, start):
        """9.5 (i) not computed for a run that failed AFTER the roads check passed: the check still reads PASS
        (D1, R2-1), and no printed line is broken by the failure's text (R2-2)."""
        self.assertTrue(res["part_9_5_i"]["status"].startswith("not computed: " + start), res["part_9_5_i"]["status"])
        self.assertEqual((res["part_9_5_v"]["status"], res["part_9_6"]["status"]), ("computed", "computed"))
        self.assertIsNone(res["part_9_6"]["current_grade"])
        self.assertTrue(res["part_9_6"]["current_grade_note"].startswith("not computed: " + start))
        self.assertTrue(res["current_grade"]["run"].startswith("not completed: " + start))
        self.assertEqual(res["controls"]["roads"], ROADS_PASS)
        self.assertIs(res["controls"]["roads"]["passed"], True)
        self.assertEqual(roads_line(res), "PASS: arrays_sha256 equal")
        self.assertEqual(broken(BS.render(res)), [])                        # LF, CR alone or any other break

    def test_a_failed_run_reads_not_computed(self):                         # PR-B:1182, never a crash of core
        fx, base = shared()
        self.assertEqual(base["part_9_5_i"]["status"], "computed")          # the control

        def failing(exc):
            inner = fake_runner(fx.rows)

            def run_road_episode(policy, road, **kw):
                if road["k"] == 3:
                    raise exc
                return inner(policy, road, **kw)
            return run_road_episode
        self.assert_i_not_computed(fx.compute(runner=failing(ValueError("SYNTHETIC step count\n  on two lines"))),
                                   "current-grade's run failed: ValueError: SYNTHETIC step count on two lines")
        res = fx.compute(runner=failing(SystemExit("\nREFUSING SYNTHETIC\n  its second line")))
        self.assert_i_not_computed(res, "current-grade's run failed: RuntimeError: current-grade on road 3: ")
        self.assertEqual(res["part_9_5_i"]["status"], "not computed: current-grade's run failed: RuntimeError: "
                         "current-grade on road 3: REFUSING SYNTHETIC its second line")   # one line, R2-2
        res = fx.compute(runner=failing(SystemExit("\nREFUSING SYNTHETIC\rits second line")))   # a CR alone
        self.assert_i_not_computed(res, "current-grade's run failed: RuntimeError: current-grade on road 3: "
                                        "REFUSING SYNTHETIC its second line")
        for text, want in (("\nA\n  B \n\nC", "A B C"),               # blank and whitespace-only lines dropped, and
                           ("\nA\r  B\r\n   \n\tC\x0bD\x0cE\u2028F", "A B C D E F")):  # every splitlines break
            self.assertEqual(BS._one_line(text), want, repr(text))
        for ch in BREAKS.pattern[1:-1]:                                     # the scan's breaks are splitlines' own
            self.assertEqual(f"a{ch}b".splitlines(), ["a", "b"], repr(ch))
        self.assertEqual(broken(["ok", "a\rb", "a\u2028b"]), ["a\rb", "a\u2028b"])  # the control: the scan sees them

        def longer_on_0(k, trace):
            return {key: v + [v[-1]] for key, v in trace.items()} if k == 0 else trace
        self.assert_i_not_computed(fx.compute(runner=fake_runner(fx.rows, trace_of=longer_on_0)),
                                   f"current-grade's roads ran [{STEPS}, {STEPS + 1}] steps")
        fx2 = Fixture("failed_run")                                         # the whole command still writes
        code, _ = fx2.main(runner=failing(SystemExit("\nREFUSING SYNTHETIC")))
        self.assertEqual(code, 0)
        self.assertEqual(sorted(os.listdir(fx2.out)), sorted(n for n in BS.OUT_FILES if n != "current_grade.npz"))
        with open(os.path.join(fx2.out, "b58h_core.txt"), encoding="utf-8") as fh:
            written = fh.read().split("\n")
        with open(os.path.join(fx2.out, "b58h_core.json"), encoding="utf-8") as fh:
            self.assertEqual(json.load(fh)["controls"]["roads"], ROADS_PASS)
        self.assertEqual([ln for ln in written if ln.startswith("REFUSING")], [])  # no reason broken in two
        self.assertEqual(sum("current-grade on road 3: REFUSING SYNTHETIC" in ln for ln in written),
                         2 + len(BS.ARMS))          # the run's line, 9.5 (i)'s status, 9.6's row beside each arm
        self.assertIn("  the roads check (epa_roads.arrays_sha256 against the scores' provenance.arrays_sha256): "
                      "PASS: arrays_sha256 equal", written)

    def test_run_cg_s_own_text_is_one_line(self):                           # the text a pool worker carries back
        road = make_roads()[3]

        def refusing(policy, road, **kw):
            raise SystemExit("\n  REFUSING SYNTHETIC\r\n  its second line")
        with mock.patch.object(V, "run_road_episode", refusing), self.assertRaises(RuntimeError) as cm:
            BS.run_cg((BS.ENGINE, road, False))
        self.assertEqual(str(cm.exception), "current-grade on road 3: REFUSING SYNTHETIC its second line")
        with mock.patch.object(V, "run_road_episode", fake_runner(shared()[0].rows)):   # the control: no refusal
            self.assertEqual(BS.run_cg((BS.ENGINE, road, False))["steps"], STEPS)


# ------------------------------------------------------------------------------------------ Controls
class Controls(Case):
    def test_control_1(self):
        fx, base = shared()
        self.assertTrue(base["controls"]["1"]["passed"])
        self.assertIsNotNone(base["part_9_6"]["current_grade"])

        for road in (5, N - 1):                                             # every road, the last one too
            def off(k, fuel, road=road):
                return float(np.nextafter(fuel, np.inf)) if k == road else fuel
            res = fx.compute(runner=fake_runner(fx.rows, fuel_of=off))
            self.assertFalse(res["controls"]["1"]["passed"])
            self.assertTrue(res["part_9_5_i"]["status"].startswith(
                f"not computed: control 1 failed: fuel differs on 1 road(s), first road {road}"))
            block = fx.doc["provenance"]["delivery"]["hand"][BS.CG]["fuel"][road]
            run = float(np.nextafter(block, np.inf))
            self.assertEqual(res["controls"]["1"]["detail"],                # grams at 6, the difference in e-notation
                             f"fuel differs on 1 road(s), first road {road}: run {run:.6f} g, delivery block "
                             f"{block:.6f} g, difference {run - block:+.3e} g")
            self.assertNotIn("s", res["part_9_5_i"])
            self.assertIsNone(res["part_9_6"]["current_grade"])
            self.assertTrue(res["part_9_6"]["current_grade_note"].startswith("not computed: control 1 failed"))
            self.assertEqual((res["part_9_5_v"]["status"], res["part_9_6"]["status"]), ("computed", "computed"))

    def test_control_2(self):
        fx = Fixture("c2")
        self.assertTrue(fx.compute()["controls"]["2"]["passed"])
        with open(fx.report, encoding="utf-8") as fh:
            text = fh.read()
        fx.write_text(fx.report, text, newline="\r\n")                     # a CRLF checkout of the same blob
        with open(fx.report, "rb") as fh:
            self.assertIn(b"\r\n", fh.read())
        res = fx.compute()
        self.assertTrue(res["controls"]["2"]["passed"], res["controls"]["2"])
        line = [ln for ln in text.split("\n") if ln.startswith(f"    {BS.CG} ")][0]
        m = re.fullmatch(r"    current-grade\s+([+-]\d+\.\d\d) \[\s*([+-]\d+\.\d\d)\]", line)
        nk, wk = float(m.group(1)), float(m.group(2))
        self.assertEqual(BS.report_line(BS.CG, nk, wk), line)
        for moved in (BS.report_line(BS.CG, nk + 0.01, wk), BS.report_line(BS.CG, nk, wk + 0.01)):
            self.assertNotEqual(moved, line)
            fx.write_text(fx.report, text.replace(line, moved))
            fx.commit()
            res = fx.compute()
            self.assertFalse(res["controls"]["2"]["passed"])
            detail = (f"the report reads {moved.strip()!r}, the run gives {line.strip()!r} (no knock [with knock, "
                      f"{FEA.WITH_KNOCK_LABEL}], evaluate.py's line)")      # the report's line first, the readings
            self.assertEqual(res["controls"]["2"]["detail"], detail)        # named in their own order
            self.assertEqual((res["controls"]["2"]["found"], res["controls"]["2"]["expected"]), (moved, line))
            self.assertEqual(res["part_9_5_i"]["status"], "not computed: control 2 failed: " + detail)
            self.assertEqual(res["part_9_6"]["status"], "computed")
            self.assertIsNone(res["part_9_6"]["current_grade"])
            lines = BS.render(res)                                          # its detail, quoted by 9.5 (i) and 9.6,
            self.assertEqual(unlabelled(lines), [])                         # names the with-knock reading (R2-3)
            quoted = [ln for ln in lines if "control 2 failed: the report reads" in ln]
            self.assertEqual(len(quoted), 1 + len(BS.ARMS))                 # 9.5 (i)'s status, 9.6's row per arm
            self.assertTrue(all(FEA.WITH_KNOCK_LABEL in ln for ln in quoted))
        fx.write_text(fx.report, text)
        fx.commit()
        self.assertTrue(fx.compute()["controls"]["2"]["passed"])
        fx.write_text(fx.report, text + "\n")                              # changed, not committed
        res = fx.compute()
        self.assertFalse(res["controls"]["2"]["passed"])
        self.assertIn("not committed at HEAD", res["controls"]["2"]["detail"])
        put_bytes(fx.report, b"\xff\xfe SYNTHETIC, not UTF-8\n")             # committed, and not text: a failed
        fx.commit()                                                         # control, never a crash
        res = fx.compute()
        self.assertFalse(res["controls"]["2"]["passed"])
        self.assertIn("does not read as UTF-8 text (UnicodeDecodeError)", res["controls"]["2"]["detail"])
        self.assertEqual(res["part_9_6"]["status"], "computed")

    def test_a_git_failure_s_text_is_one_line(self):                       # GitError carries git's stderr
        fx, _ = shared()
        report = os.path.splitext(os.path.abspath(fx.scores))[0] + ".txt"
        real = EF.committed_at_head
        text = ("git hash-object -- results/B58H_RESULT/scores_b58h.txt in SYNTHETIC: exit 128: warning: SYNTHETIC "
                "first line\nfatal: SYNTHETIC second line")             # epa_freeze.py:234's form, two lines

        def failing_for_the_report(path, *, root):
            if os.path.normcase(os.path.abspath(path)) == os.path.normcase(report):
                raise EF.GitError(text)
            return real(path, root=root)
        with mock.patch.object(EF, "committed_at_head", failing_for_the_report):
            self.assertEqual(BS.commit_problem(report, root=fx.root), "cannot be checked against HEAD (git "
                             "hash-object -- results/B58H_RESULT/scores_b58h.txt in SYNTHETIC: exit 128: warning: "
                             "SYNTHETIC first line fatal: SYNTHETIC second line)")
            res = fx.compute()
        why = "cannot be checked against HEAD (" + " ".join(text.split("\n")) + ")"
        self.assertEqual(res["controls"]["2"]["detail"], f"the text report {report}: {why}")
        self.assertEqual(res["part_9_5_i"]["status"],
                         f"not computed: control 2 failed: the text report {report}: {why}")
        self.assertEqual(res["part_9_6"]["status"], "computed")
        self.assertEqual(broken(BS.render(res)), [])                        # control 2's line, 9.5 (i), 9.6's rows
        self.assertTrue(shared()[1]["controls"]["2"]["passed"])             # the control: git answers, it passes

    def test_control_2_reads_the_one_line_after_the_header(self):
        fx = Fixture("c2_one")
        with open(fx.report, encoding="utf-8") as fh:
            text = fh.read()
        line = [ln for ln in text.split("\n") if ln.startswith(f"    {BS.CG} ")][0]
        nk = float(line.split()[1])
        decoy = BS.report_line(BS.CG, nk + 5.0, 0.0)                         # above the header: not the cut's line
        cases = {"a decoy above the header": (text.replace(BS.CUT_HEADER, decoy + "\n" + BS.CUT_HEADER), True, ""),
                 "the line twice after it": (text.replace(line, line + "\n" + line), False,
                                             f"2 lines of {BS.CG} after the cut header, not one"),
                 "no header": (text.replace(BS.CUT_HEADER + "\n", ""), False, "the text report has no line")}
        for name, (changed, passes, words) in cases.items():
            self.assertNotEqual(changed, text, name)
            fx.write_text(fx.report, changed)
            fx.commit()
            c2 = fx.compute()["controls"]["2"]
            self.assertEqual(c2["passed"], passes, (name, c2))
            self.assertIn(words, c2["detail"], name)

    def test_control_2_reads_evaluate_s_header_and_line(self):
        fx, res = shared()
        lines = V.d34_report("b58", fx.rows, header=V.D34_HEADER, reading=V.REDRAW_READING, ratios=RATIOS, lines=[])
        self.assertIn(BS.CUT_HEADER, lines)
        cg, base = fx.rows["hand"][BS.CG], fx.rows["hand"][V.BASELINE]
        want = BS.report_line(BS.CG, *[V.median_cut([x[k] for x in cg], [b[k] for b in base])
                                       for k in (V.READING_KEYS["no_knock"], V.READING_KEYS["with_knock"])])
        self.assertIn(want, lines)
        self.assertEqual(res["controls"]["2"]["found"], want)

    def test_control_3_both_branches(self):
        _, base = shared()
        self.assertTrue(base["controls"]["3"]["passed"])
        self.assertEqual(base["controls"]["3"]["by"]["no_knock"]["max_abs"], 0.0)
        self.assertIsNone(base["part_9_5_i"]["control_3_beside"])

        def shift(by):
            def m(rec):
                rec["ceilings"]["per_engine"]["b58"]["per_road"][4]["D"]["neutral"]["noknock"] += by
            return m
        fx = Fixture("c3_small", mutate_roads_record=shift(0.5e-6))
        self.assertTrue(fx.compute()["controls"]["3"]["passed"])
        fx = Fixture("c3", mutate_roads_record=shift(2e-6))
        res = fx.compute()
        c3 = res["controls"]["3"]
        self.assertFalse(c3["passed"])                                      # 2e-6 absolute, 4e-8 relative
        self.assertEqual(c3["by"]["no_knock"]["road"], 4)
        self.assertAlmostEqual(c3["by"]["no_knock"]["max_abs"], 2e-6, delta=1e-12)
        self.assertLess(c3["by"]["no_knock"]["max_rel"], 1e-6)
        self.assertEqual(c3["by"]["with_knock"]["max_abs"], 0.0)
        self.assertEqual(res["part_9_5_i"]["status"], "computed")           # never "not computed"
        self.assertEqual(res["part_9_5_i"]["control_3_beside"], c3["by"])
        self.assertIn("control 3 FAILED", "\n".join(BS.render(res)))
        self.assertNotIn("control 3 FAILED", "\n".join(BS.render(base)))

        def shift_last_knock(rec):                                          # the other reading, the last road
            rec["ceilings"]["per_engine"]["b58"]["per_road"][N - 1]["D"]["neutral"]["knock"] -= 2e-6
        c3 = Fixture("c3_knock", mutate_roads_record=shift_last_knock).compute()["controls"]["3"]
        self.assertFalse(c3["passed"])
        self.assertEqual((c3["by"]["with_knock"]["road"], c3["by"]["no_knock"]["max_abs"]), (N - 1, 0.0))
        self.assertAlmostEqual(c3["by"]["with_knock"]["max_abs"], 2e-6, delta=1e-12)

    def test_control_3_boundary_and_relative(self):
        def per_road(noknock):
            return [{"k": k, "D": {"neutral": {"noknock": v, "knock": 1.0}}} for k, v in enumerate(noknock)]
        at = BS.control_3(per_road([2e-6, 1.0]), {"no_knock": [1e-6, 1.0], "with_knock": [1.0, 1.0]})
        self.assertEqual(2e-6 - 1e-6, BS.CONTROL_3_ABS)                     # exactly 1e-6 apart: "to 1e-6" passes
        self.assertTrue(at["passed"], at)
        self.assertEqual(at["by"]["no_knock"]["max_abs"], 1e-6)
        over = BS.control_3(per_road([float(np.nextafter(2e-6, 1.0)), 1.0]),
                            {"no_knock": [1e-6, 1.0], "with_knock": [1.0, 1.0]})
        self.assertFalse(over["passed"])                                    # the control: one ulp more fails
        D_base = {"no_knock": [1.0, 100.0], "with_knock": [1.0, 1.0]}       # the largest relative difference is on
        c3 = BS.control_3(per_road([1.0 + 1e-7, 100.0 + 5e-7]), D_base)    # another road than the absolute one
        nd = np.array([1.0 + 1e-7, 100.0 + 5e-7])
        rel = np.abs(nd - np.array(D_base["no_knock"])) / np.array(D_base["no_knock"])
        self.assertEqual(c3["by"]["no_knock"]["road"], 1)
        self.assertEqual(c3["by"]["no_knock"]["max_abs"], float(abs(nd[1] - 100.0)))
        self.assertEqual(c3["by"]["no_knock"]["max_rel"], float(rel.max()))
        self.assertEqual(int(np.argmax(rel)), 0)
        self.assertNotAlmostEqual(c3["by"]["no_knock"]["max_rel"], float(rel[1]), places=12)

    def test_control_3_road_order(self):
        fx, _ = shared()
        with open(os.path.join(fx.root, *BS.ROADS.split("/")), encoding="utf-8") as fh:
            per_road = json.load(fh)["ceilings"]["per_engine"]["b58"]["per_road"]
        rows = fx.rows["hand"][V.BASELINE]
        D_base = {rd: [float(r[key]) for r in rows] for rd, key in V.READING_KEYS.items()}
        self.assertTrue(BS.control_3(per_road, D_base)["passed"])            # the control
        relabelled = [dict(p, k=N - 1 - i) for i, p in enumerate(per_road)]  # the same D, the roads' k reversed
        for bad in (per_road[::-1], relabelled, per_road[:-1]):
            c3 = BS.control_3(bad, D_base)
            self.assertFalse(c3["passed"])
            self.assertIn(f"is not roads 0-{N - 1} in order", c3["detail"])


# ------------------------------------------------------------------------------------------ Savings
class Savings(Case):
    def test_s_by_hand(self):
        fx, res = shared()
        p = res["part_9_5_i"]
        base, cg = fx.rows["hand"][V.BASELINE], fx.rows["hand"][BS.CG]
        stats_of = {}
        for reading, key in V.READING_KEYS.items():
            Db, Dcg = [b[key] for b in base], [c[key] for c in cg]
            own = p["current_grade_cut"][reading]                           # current-grade's own cut, both forms
            self.assertAlmostEqual(own["evaluate_form"], cut_by_hand(Dcg, Db), places=10)
            cg_mean = sum(100.0 * (1.0 - Dcg[k] / Db[k]) for k in range(N)) / N
            self.assertAlmostEqual(own["mean_form"], cg_mean, places=10)
            self.assertNotAlmostEqual(own["mean_form"], 100.0 * (1.0 - sum(Dcg) / sum(Db)), places=6)  # of means
            for arm in BS.ARMS:
                want = {"evaluate_form": [], "mean_form": []}
                for s in SEEDS:
                    D = [x[key] for x in fx.rows["agents"][(arm, s)]]
                    ev = cut_by_hand(D, Db) - cut_by_hand(Dcg, Db)
                    mf = sum(100.0 * (Dcg[k] - D[k]) / Db[k] for k in range(N)) / N
                    got = p["s"][arm][str(s)][reading]
                    self.assertAlmostEqual(got["evaluate_form"], ev, places=10)
                    self.assertAlmostEqual(got["mean_form"], mf, places=10)
                    self.assertNotAlmostEqual(ev, mf, places=3)             # the two forms differ here
                    wrong = cut_by_hand(D, Db) - cut_by_hand(Dcg, [1.0] * N)  # cg's cut on another base
                    self.assertNotAlmostEqual(got["evaluate_form"], wrong, places=3)
                    want["evaluate_form"].append(ev)
                    want["mean_form"].append(mf)
                for form, vals in want.items():                             # each form's statistics, by hand
                    st = p["per_arm"][arm][reading][form]
                    self.assertEqual(st["below_0"], sum(v < 0 for v in vals))
                    self.assertAlmostEqual(st["median"], statistics.median(vals), places=10)
                    self.assertNotAlmostEqual(st["median"], statistics.mean(vals), places=6)
                    self.assertAlmostEqual(st["sd"], statistics.stdev(vals), places=10)
                    self.assertNotAlmostEqual(st["sd"], statistics.pstdev(vals), places=6)  # ddof 0 differs
                    self.assertAlmostEqual(st["min"], min(vals), places=10)
                    self.assertAlmostEqual(st["max"], max(vals), places=10)
                    self.assertEqual(st["n"], len(SEEDS))
                    stats_of[(arm, reading, form)] = (st["median"], st["sd"], st["min"], st["max"])
        for arm in BS.ARMS:                                                  # the readings' statistics differ, so a
            for form in ("evaluate_form", "mean_form"):                     # reading swapped would be seen
                self.assertNotEqual(stats_of[(arm, "no_knock", form)], stats_of[(arm, "with_knock", form)])
        counts = [p["per_arm"][a]["no_knock"]["evaluate_form"]["below_0"] for a in BS.ARMS]
        self.assertTrue(any(0 < c < len(SEEDS) for c in counts), counts)   # the count is not trivially 0 or n

    def test_an_agent_level_with_current_grade(self):                       # s = 0 is not below current-grade
        self.assertEqual(BS.arm_stats([0.0, -1e-12, 3.0])["below_0"], 1)
        rows = make_rows()
        for agent, cg in zip(rows["agents"][("sighted_r0.5", 0)], rows["hand"][BS.CG]):
            agent["damage"], agent["damage_thermal"] = cg["damage"], cg["damage_thermal"]
        p = Fixture("level", rows=rows).compute()["part_9_5_i"]
        for rd in BS.READINGS:
            for form in ("evaluate_form", "mean_form"):
                self.assertEqual(p["s"]["sighted_r0.5"]["0"][rd][form], 0.0)
                vals = [p["s"]["sighted_r0.5"][str(s)][rd][form] for s in SEEDS]
                below = p["per_arm"]["sighted_r0.5"][rd][form]["below_0"]
                self.assertEqual(below, sum(v < 0 for v in vals))
                self.assertNotEqual(below, sum(v <= 0 for v in vals))       # the control: <= would count it

    def test_hand_written_read_and_recomputed(self):
        fx, res = shared()
        hw = res["part_9_5_i"]["hand_written"]
        with open(os.path.join(fx.root, *BS.ROADS.split("/")), encoding="utf-8") as fh:
            ceil = json.load(fh)["ceilings"]["per_engine"]["b58"]
        self.assertEqual(hw["by_arm"], {"blind": RATIOS, "sighted_r0.5": ["0.5"], "sighted_r1.5": ["1.5"]})
        for reading, rj in BS.READING_RJ.items():
            self.assertEqual(len(hw["table"][reading]), len(RATIOS) * len(BS.HW_POLICIES))
            for h in hw["table"][reading]:
                entry = ceil["by"][h["r"]][h["policy"]][rj]
                self.assertEqual(h["evaluate_form"], entry["evaluate_form"])
                self.assertNotEqual(h["mean_form"], entry["mean"])          # roads.json's mean is not printed
                key = f"a@{h['r']}" if h["policy"] == "a" else h["policy"]
                pr = ceil["per_road"]
                mf = sum(100.0 * (q["D"]["cg"][rj] - q["D"][key][rj]) / q["D"]["neutral"][rj] for q in pr) / N
                self.assertAlmostEqual(h["mean_form"], mf, places=10)
                on_base = sum(100.0 * (q["D"]["cg"][rj] - q["D"][key][rj]) / q["D_base"][rj] for q in pr) / N
                self.assertNotAlmostEqual(h["mean_form"], on_base, places=3)  # the parallel network's base
        text = "\n".join(BS.render(res))
        self.assertNotIn("999.0", text)


# ------------------------------------------------------------------------------------------ TunedBests
SYN_HW = """
=== reading: noknock (primary)

blind: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  D=0 delta=0.33              2.000    1.000   +0.500   808.0
  D=0 delta=1.00              1.000    3.000   +0.900   807.0
  D=5 delta=1.00              0.500    3.000   +1.000   807.5

sighted r=0.5: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  lead=1.00H delta=1.00       0.700    0.900   +0.300   808.1

sighted r=1.5: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  lead=0.50H delta=0.67       4.000   -1.000   +0.100   808.2
  lead=1.00H delta=1.00       3.000    2.000   +0.200   808.3

frontier, mean, noknock: blind [(0.0, 0.0)]
  r=0.5: largest sighted-minus-blind saving at equal extra fuel: +9.111 points (MEAN)
  r=1.5: largest sighted-minus-blind saving at equal extra fuel: +9.222 points (MEAN)

frontier, evaluate_form, noknock: blind [(0.0, 0.0)]
  r=0.5: sighted frontier [(0.0, 0.0)]
  r=0.5: largest sighted-minus-blind saving at equal extra fuel: +1.111 points (EVAL)
  r=1.5: largest sighted-minus-blind saving at equal extra fuel: +1.222 points (EVAL)

=== reading: knock (beside it)

blind: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  D=0 delta=1.00              1.000    1.500   +0.900   807.0

sighted r=0.5: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  lead=1.00H delta=1.00       0.700    0.800   +0.300   808.1

sighted r=1.5: setting, saving (mean form), saving (evaluate.py's form), extra fuel %, peak C
  lead=1.00H delta=1.00       3.000    2.500   +0.200   808.3

frontier, evaluate_form, knock: blind [(0.0, 0.0)]
  r=0.5: largest sighted-minus-blind saving at equal extra fuel: +2.111 points (EVAL K)
  r=1.5: largest sighted-minus-blind saving at equal extra fuel: +2.222 points (EVAL K)
"""


class TunedBests(Case):
    def test_the_largest_saving_in_evaluate_s_form(self):
        tb = BS.tuned_bests(SYN_HW, RATIOS)
        best = tb["noknock"]["best"]
        self.assertEqual([ln.split()[0:2] for ln in best["blind"]], [["D=0", "delta=1.00"], ["D=5", "delta=1.00"]])
        self.assertNotIn("  D=0 delta=0.33              2.000    1.000   +0.500   808.0", best["blind"])  # mean's
        self.assertEqual(best["sighted r=1.5"], ["  lead=1.00H delta=1.00       3.000    2.000   +0.200   808.3"])
        self.assertEqual([ln.split("(")[-1] for ln in tb["noknock"]["frontier"]], ["EVAL)", "EVAL)"])
        self.assertEqual([ln.split("(")[-1] for ln in tb["knock"]["frontier"]], ["EVAL K)", "EVAL K)"])
        for ln in sum(best.values(), []) + tb["noknock"]["frontier"]:
            self.assertIn(ln, SYN_HW.split("\n"))                           # verbatim
        foreign = ("frontier, evaluate_form, knock: blind [(0.0, 0.0)]\n"
                   "  r=0.5: largest sighted-minus-blind saving at equal extra fuel: +7.111 points (FOREIGN)\n"
                   "  r=1.5: largest sighted-minus-blind saving at equal extra fuel: +7.222 points (FOREIGN)\n\n")
        text = SYN_HW.replace("=== reading: knock", foreign + "=== reading: knock")
        self.assertIn("(FOREIGN)", text)
        tb = BS.tuned_bests(text, RATIOS)                                   # another reading's block inside the
        self.assertEqual([ln.split("(")[-1] for ln in tb["noknock"]["frontier"]], ["EVAL)", "EVAL)"])  # section
        self.assertEqual([ln.split("(")[-1] for ln in tb["knock"]["frontier"]], ["EVAL K)", "EVAL K)"])

    def test_refusals(self):
        bad = {"no knock section": SYN_HW.split("=== reading: knock")[0],
               "a garbled setting": SYN_HW.replace("  D=5 delta=1.00              0.500", "  D=5 delta=1.00   x"),
               "one frontier line": SYN_HW.replace("  r=1.5: largest sighted-minus-blind saving at equal extra fuel: "
                                                   "+2.222 points (EVAL K)\n", "")}
        for name, text in bad.items():
            with self.assertRaises(AB.B58HError, msg=name):
                BS.tuned_bests(text, RATIOS)
        BS.tuned_bests(SYN_HW, RATIOS)                                      # the control

    def test_the_committed_report_and_grids_parse(self):
        text = BS.read_text_lf(REAL_HW)
        tb = BS.tuned_bests(text, RATIOS)
        lines = text.split("\n")
        self.assertEqual(sorted(tb), ["knock", "noknock"])
        for rd in tb:
            self.assertEqual(sorted(tb[rd]["best"]), ["blind", "sighted r=0.5", "sighted r=1.5"])
            self.assertEqual(len(tb[rd]["frontier"]), 2)
            for ln in sum(tb[rd]["best"].values(), []) + tb[rd]["frontier"]:
                self.assertIn(ln, lines)
        d13 = BS.decision13(BS.read_text_lf(REAL_GRIDS))
        self.assertEqual(d13, BS.read_text_lf(REAL_GRIDS).split("\n")[98:100])
        self.assertTrue(d13[1].startswith("  b58: steps "))
        with self.assertRaises(AB.B58HError):                               # the control: a line off
            BS.decision13("\n" + BS.read_text_lf(REAL_GRIDS))
        first = BS.read_text_lf(REAL_GRIDS).split("\n")[:BS.GRIDS_LINES[1]]
        self.assertEqual(BS.decision13("\n".join(first)), d13)              # exactly 100 lines hold 99 and 100
        with self.assertRaises(AB.B58HError) as cm:                         # the control: 99 lines do not
            BS.decision13("\n".join(first[:-1]))
        self.assertIn("99 lines, not at least 100", str(cm.exception))
        lines = BS.read_text_lf(REAL_GRIDS).split("\n")
        lines[99] = "  mazda_25t: " + lines[99].split(": ", 1)[1]           # the rule kept, another engine's count
        with self.assertRaises(AB.B58HError) as cm:
            BS.decision13("\n".join(lines))
        self.assertIn("the b58's count", str(cm.exception))

    def test_not_committed_reads_not_read(self):
        fx = Fixture("hw_nc")
        before = fx.compute()
        self.assertIsNotNone(before["part_9_5_i"]["tuned_bests"])
        with open(os.path.join(fx.root, *BS.HW_OPT_REPORT.split("/")), "ab") as fh:
            fh.write(b"x\n")
        res = fx.compute()
        self.assertIsNone(res["part_9_5_i"]["tuned_bests"])
        note = res["part_9_5_i"]["tuned_bests_note"]
        self.assertTrue(note.startswith(f"not read: {BS.HW_OPT_REPORT}: not committed"), note)
        self.assertEqual(res["part_9_5_i"]["decision13"], before["part_9_5_i"]["decision13"])
        self.assertEqual(res["part_9_5_i"]["s"], before["part_9_5_i"]["s"])
        put_bytes(os.path.join(fx.root, *BS.GRIDS.split("/")), b"\xff SYNTHETIC, not UTF-8\n")
        fx.commit()                                                         # committed, and not text
        res = fx.compute()
        self.assertEqual(res["part_9_5_i"]["decision13_note"],
                         f"not read: {BS.GRIDS}: it does not read as UTF-8 text (UnicodeDecodeError)")
        self.assertEqual(res["part_9_5_i"]["s"], before["part_9_5_i"]["s"])


# ------------------------------------------------------------------------------------------ Delivery
class Delivery(Case):
    def test_the_figures_by_hand(self):
        fx, res = shared()
        p = res["part_9_5_v"]
        self.assertEqual(p["status"], "computed")
        base = fx.rows["hand"][V.BASELINE]

        def fig(rows):
            fuel = sum(100.0 * (r["fuel"] / b["fuel"] - 1.0) for r, b in zip(rows, base)) / N
            dem = [r for r in rows if r["demand_steps"]]
            mean = sum(r["short_steps"] / r["demand_steps"] for r in dem) / len(dem) if dem else None
            tot = sum(r["demand_steps"] for r in rows)
            pooled = sum(r["short_steps"] for r in rows) / tot if tot else None
            return fuel, mean, pooled
        for r in RATIOS:
            sig = f"sighted_r{r}"
            kept = [s for s in SEEDS if s != 3]
            for i, q in enumerate(("fuel_figure", "mean_short_share", "pooled_short_share")):
                seeds = SEEDS if q == "fuel_figure" else kept
                want = [fig(fx.rows["agents"][(sig, s)])[i] - fig(fx.rows["agents"][("blind", s)])[i] for s in seeds]
                sm = p["differences"][r][q]
                self.assertEqual(sm["seeds"], seeds)
                np.testing.assert_allclose(sm["values"], want, rtol=0, atol=1e-12)
                lo, hi = stats.t.interval(0.95, len(want) - 1, loc=np.mean(want), scale=stats.sem(want))
                self.assertAlmostEqual(sm["interval"]["lo"], lo, places=10)
                self.assertAlmostEqual(sm["interval"]["hi"], hi, places=10)
                self.assertEqual(sm["signs"], {"positive": sum(v > 0 for v in want),
                                               "negative": sum(v < 0 for v in want), "zero": sum(v == 0 for v in want)})
                self.assertEqual(sm["dropped"], [] if q == "fuel_figure" else [3])
        rows = fx.rows["agents"][("sighted_r1.5", 2)]
        dem = [x for x in rows if x["demand_steps"]]
        self.assertEqual(len(dem), N)
        self.assertAlmostEqual(p["per_seed"]["sighted_r1.5"]["2"]["mean_short_share"], fig(rows)[1], places=12)
        self.assertNotAlmostEqual(fig(rows)[1], fig(rows)[2], places=6)    # the mean and pooled shares differ
        b_rows = base
        b_mean = fig(b_rows)[1]
        self.assertAlmostEqual(p["beside"][V.BASELINE]["mean_short_share"], b_mean, places=12)
        self.assertNotAlmostEqual(b_mean, sum(x["short_steps"] / x["demand_steps"] if x["demand_steps"] else 0.0
                                              for x in b_rows) / N, places=6)  # road 1 has no demand step
        self.assertEqual(sorted(p["beside"]), sorted([V.BASELINE, BS.CG]))  # reactive is not printed (G29)
        self.assertIn("reactive", fx.doc["provenance"]["delivery"]["hand"])  # the control: the block holds it
        self.assertEqual(p["beside"][V.BASELINE]["fuel_figure"], 0.0)
        self.assertAlmostEqual(p["beside"][BS.CG]["fuel_figure"], fig(fx.rows["hand"][BS.CG])[0], places=10)
        self.assertEqual(p["no_demand_seeds"], {"blind": [3], "sighted_r0.5": [], "sighted_r1.5": []})
        self.assertIn(BS.KNOCK_STATEMENT_V, "\n".join(BS.render(res)))

    def test_a_sighted_seed_without_demand_is_dropped(self):               # G23: either arm, not only the blinded
        rows = make_rows()
        for x in rows["agents"][("sighted_r0.5", 4)]:
            x["demand_steps"], x["short_steps"] = 0, 0
        p = Fixture("v_sighted", rows=rows).compute()["part_9_5_v"]
        self.assertEqual(p["status"], "computed")
        self.assertEqual(p["no_demand_seeds"], {"blind": [3], "sighted_r0.5": [4], "sighted_r1.5": []})
        for q in ("mean_short_share", "pooled_short_share"):
            self.assertEqual((p["differences"]["0.5"][q]["dropped"], p["differences"]["1.5"][q]["dropped"]),
                             ([3, 4], [3]), q)
            self.assertEqual(p["differences"]["0.5"][q]["seeds"], [s for s in SEEDS if s not in (3, 4)])
        self.assertEqual(p["differences"]["0.5"]["fuel_figure"]["seeds"], SEEDS)   # the fuel figure keeps them

    def test_the_block_s_refusals(self):
        fx, _ = shared()
        seeds = [str(s) for s in SEEDS]
        self.assertIsNone(BS.delivery_problem(fx.doc, seeds=seeds))         # the control

        def broken(change):
            doc = json.loads(json.dumps(fx.doc))
            change(doc["provenance"]["delivery"])
            return BS.delivery_problem(doc, seeds=seeds)
        cases = {
            "absent": (lambda d: d.clear(), "holds []"),
            "a rule that is not an object": (lambda d: d.__setitem__("rule", "SYNTHETIC"), "are not all objects"),
            "no current-grade": (lambda d: d["hand"].pop(BS.CG), "has no 'current-grade'"),
            "a share not short / demand": (lambda d: d["arms"]["blind"]["5"]["short_share"].__setitem__(
                0, d["arms"]["blind"]["5"]["short_share"][0] + 1e-9), "is not short / demand"),
            "a share where no demand": (lambda d: d["hand"][V.BASELINE]["short_share"].__setitem__(1, 0.0),
                                        "is not null"),
            "a baseline fuel of 0": (lambda d: d["hand"][V.BASELINE]["fuel"].__setitem__(0, 0.0), "not above 0"),
            "a seed missing": (lambda d: d["arms"]["sighted_r0.5"].pop("19"), "seeds are not"),
            "short above demand": (lambda d: d["arms"]["blind"]["2"]["short_steps"].__setitem__(0, 10 ** 6),
                                   "exceed"),
            "a road missing": (lambda d: d["arms"]["blind"]["2"]["fuel"].pop(), "is not a list of 20"),
            "a fuel that is not finite": (lambda d: d["hand"][BS.CG]["fuel"].__setitem__(3, float("nan")),
                                          "not a finite number")}
        for name, (change, words) in cases.items():
            why = broken(change)
            self.assertIsNotNone(why, name)
            self.assertIn(words, why, name)

    def test_a_refused_block_reads_not_computed(self):
        def drop(doc):
            doc["provenance"]["delivery"]["hand"][BS.CG]["short_share"][0] = 0.5
        res = Fixture("deliv", mutate_doc=drop).compute()
        self.assertTrue(res["part_9_5_v"]["status"].startswith("not computed: the delivery block is refused"))
        self.assertTrue(res["part_9_5_i"]["status"].startswith(
            "not computed: control 1 failed: the delivery block is refused"))
        self.assertEqual(res["part_9_6"]["status"], "computed")


# ------------------------------------------------------------------------------------------ Temperatures
class Temperatures(Case):
    def test_peak_strict_exceedance_and_dt(self):
        tt = np.array([[1052.5, 1053.5, 1000.0, 1100.0], [1050.0, 1060.0, 1070.0, 1080.0]])
        at = float(tt[0, 0] - 273.15)                                       # a limit the first step sits exactly at
        lim = [("778", 778.0), ("804", 804.0), ("at", at)]
        one = BS.temps_of(tt, 1.0, lim)
        self.assertEqual(one["peak"], [1100.0 - 273.15, 1080.0 - 273.15])
        self.assertEqual(one["above"]["778"], [3.0, 3.0])
        self.assertEqual(one["above"]["804"], [1.0, 1.0])
        self.assertEqual(one["above"]["at"][0], 2.0)                        # the step at the limit is not above it
        self.assertEqual(int(np.count_nonzero(tt[0] - 273.15 >= at)), 3)    # a >= rule would count it
        two = BS.temps_of(tt, 2.0, lim)
        self.assertEqual(two["above"]["778"], [6.0, 6.0])                   # dt x the count
        self.assertNotEqual(two["above"], one["above"])

    def test_by_hand(self):
        fx, res = shared()
        p = res["part_9_6"]
        self.assertEqual(p["status"], "computed")
        self.assertFalse(p["knee"]["reached"])
        self.assertEqual(sorted(p["limits_c"]), ["778", "804"])

        def summary_by_hand(rows):
            peaks = [max(r["trace"]["t_turb"]) - 273.15 for r in rows]
            out = {"peak_mean": sum(peaks) / N, "peak_max": max(peaks)}
            for lab, lim in (("778", 778.0), ("804", 804.0)):
                out[f"above_{lab}"] = sum(sum(1.0 for x in r["trace"]["t_turb"] if x - 273.15 > lim)
                                          for r in rows) / N
            return out
        for arm in BS.ARMS:
            for s in SEEDS:
                want = summary_by_hand(fx.rows["agents"][(arm, s)])
                for q, v in want.items():
                    self.assertAlmostEqual(p["agents"][arm][str(s)][q], v, places=10)
            means = {q: np.mean([p["agents"][arm][str(s)][q] for s in SEEDS]) for q in want}
            for q in want:
                self.assertAlmostEqual(p["per_arm"][arm][q], means[q], places=10)
            highest = max(p["agents"][arm][str(s)]["peak_max"] for s in SEEDS)
            self.assertEqual(p["per_arm"][arm]["highest_peak"], highest)
            self.assertNotAlmostEqual(p["per_arm"][arm]["highest_peak"], p["per_arm"][arm]["peak_max"], places=6)
        for q, v in summary_by_hand(fx.rows["hand"][V.BASELINE]).items():
            self.assertAlmostEqual(p["baseline"][q], v, places=10)
        for q, v in summary_by_hand(fx.rows["hand"][BS.CG]).items():
            self.assertAlmostEqual(p["current_grade"][q], v, places=10)
        for r in RATIOS:
            for q in ("peak_mean", "peak_max", "above_778", "above_804"):
                d = [p["agents"][f"sighted_r{r}"][str(s)][q] - p["agents"]["blind"][str(s)][q] for s in SEEDS]
                sm = p["differences"][r][q]
                np.testing.assert_allclose(sm["values"], d, rtol=0, atol=1e-12)
                lo, hi = stats.t.interval(0.95, N - 1, loc=np.mean(d), scale=stats.sem(d))
                self.assertAlmostEqual(sm["interval"]["lo"], lo, places=9)
                self.assertAlmostEqual(sm["interval"]["hi"], hi, places=9)
        self.assertIn(BS.TEMPS_STATEMENT, "\n".join(BS.render(res)))

    def assert_96_refused(self, res, words):
        self.assertTrue(res["part_9_6"]["status"].startswith("not computed: "), res["part_9_6"]["status"])
        self.assertIn(words, res["part_9_6"]["status"])
        self.assertEqual(res["part_9_5_i"]["status"], "computed")
        self.assertEqual(res["part_9_5_v"]["status"], "computed")

    def test_integrity_refusals(self):
        fx = Fixture("integrity")
        self.assertEqual(fx.compute()["part_9_6"]["status"], "computed")   # the control
        rec = os.path.join(fx.records, "b58", "sighted_r0.5_seed7.npz")
        keep = rec + ".keep"
        shutil.copyfile(rec, keep)
        with np.load(rec) as z:
            arrays = {k: np.array(z[k]) for k in z.files}
        arrays["t_turb"][0, 0] += 1.0
        os.remove(rec)
        np.savez(rec, **arrays)
        self.assert_96_refused(fx.compute(), "the record b58/sighted_r0.5_seed7.npz's sha256 is not the index's")
        shutil.copyfile(keep, rec)
        self.assertEqual(fx.compute()["part_9_6"]["status"], "computed")
        os.remove(rec)
        self.assert_96_refused(fx.compute(), "b58/sighted_r0.5_seed7.npz is missing")
        shutil.copyfile(keep, rec)

        def index_with(**change):
            with open(fx.index, encoding="utf-8") as fh:
                idx = json.load(fh)
            idx.update(change)
            put_json(fx.root, os.path.relpath(fx.index, fx.root).replace(os.sep, "/"), idx)
            fx.commit()
        index_with(scores_sha256="0" * 64)
        self.assert_96_refused(fx.compute(), "scores_sha256 (" + "0" * 12 + ") is not the committed scores file's")
        files = dict(fx.files)
        files.pop("b58/blind_seed19.npz")
        index_with(scores_sha256=fx.sha, files=files)
        self.assert_96_refused(fx.compute(), "missing ['b58/blind_seed19.npz']")
        index_with(files=dict(fx.files, **{"b58/reactive.npz": "0" * 64}))
        self.assert_96_refused(fx.compute(), "extra ['b58/reactive.npz']")
        index_with(files=fx.files)
        self.assertEqual(fx.compute()["part_9_6"]["status"], "computed")
        with open(fx.index, "a", encoding="utf-8") as fh:
            fh.write(" ")
        self.assert_96_refused(fx.compute(), "not committed at HEAD")
        fx.write_text(fx.index, "{not json")                                # committed, and does not parse
        fx.commit()
        self.assert_96_refused(fx.compute(), "does not read as JSON (JSONDecodeError")
        fx.write_text(fx.index, "[" * 200000 + "]" * 200000)               # nested too deep for json: refused,
        fx.commit()                                                         # never a RecursionError out of core
        self.assert_96_refused(fx.compute(), "does not read as JSON (RecursionError: ")
        two_lines = ValueError("SYNTHETIC first line\n  SYNTHETIC second line")
        with mock.patch.object(json, "load", side_effect=two_lines), self.assertRaises(AB.B58HError) as cm:
            BS.read_records(fx.index, fx.records, sha_text=fx.sha, seeds=[str(s) for s in SEEDS], n_roads=N,
                            root=fx.root)                                   # the reason on one line (R2-2)
        self.assertEqual(str(cm.exception), f"the records index {fx.index} does not read as JSON (ValueError: "
                                            "SYNTHETIC first line SYNTHETIC second line)")
        with mock.patch.object(BS, "read_records", side_effect=AB.B58HError("SYNTHETIC first\r\n  SYNTHETIC second")):
            res = fx.compute()                                              # 9.6's status is one line whatever a
        self.assert_96_refused(res, "not computed: SYNTHETIC first SYNTHETIC second")   # reason holds
        self.assertEqual(broken(BS.render(res)), [])

    def test_dt_and_shape_refusals(self):
        fx = Fixture("records")
        rel = "b58/blind_seed2.npz"
        path = os.path.join(fx.records, *rel.split("/"))
        with np.load(path) as z:
            good = {k: np.array(z[k]) for k in z.files}
        keep = path + ".keep"
        shutil.copyfile(path, keep)

        def reindex(records, files):
            put_json(fx.root, os.path.relpath(fx.index, fx.root).replace(os.sep, "/"),
                     {"files": files, "scores_sha256": fx.sha, "command": "SYNTHETIC"})
            fx.commit()
            fx.records = records
            return fx.compute()

        def bad_record(data=None, drop=(), **arrays):                       # one record changed, the index re-made
            os.remove(path)                                                 # so its sha256 matches
            if data is not None:
                put_bytes(path, data)
            else:
                np.savez(path, **{k: v for k, v in dict(good, **arrays).items() if k not in drop})
            return reindex(fx.records, dict(fx.files, **{rel: AB.sha256_file(path)}))
        nan = good["t_turb"].copy()
        nan[4, 5] = np.nan
        not_f64 = f"the record {rel}'s dt is {{}}, not a 0-d float64 (write_records' np.float64(dt))"
        cases = [({"dt": np.float64(2.0)}, f"the record {rel}'s dt is 2.0 s, not the records' 1 s"),
                 ({"dt": np.array([1.0])}, not_f64.format("float64 (1,)")),             # not 0-d
                 ({"dt": np.ones((2, 3))}, not_f64.format("float64 (2, 3)")),           # numpy's repr of these
                 ({"dt": np.full(20, 1.0)}, not_f64.format("float64 (20,)")),           # two would wrap lines
                 ({"dt": np.array("abc")}, not_f64.format("<U3 ()")),                   # float() would raise on
                 ({"dt": np.array(1 + 0j)}, not_f64.format("complex128 ()")),           # these two, and read the
                 ({"dt": np.array("1")}, not_f64.format("<U1 ()")),                     # next two as 1.0
                 ({"dt": np.array(True)}, not_f64.format("bool ()")),
                 ({"dt": np.int64(1)}, not_f64.format("int64 ()")),
                 ({"t_turb": np.full((N, STEPS + 1), 1050.0)}, "the others"),
                 ({"t_turb": nan}, f"{rel}'s t_turb is float64 ({N}, {STEPS}), not finite float64"),
                 ({"t_turb": good["t_turb"].astype(np.float32)}, f"{rel}'s t_turb is float32 ({N}, {STEPS})")]
        for arrays, words in cases:
            res = bad_record(**arrays)
            self.assert_96_refused(res, words)
            self.assertEqual(broken(BS.render(res)), [], words)              # one printed line, whatever dt is
        for gone in ("dt", "t_turb"):                                       # a member missing: named, not a crash
            names = sorted(set(good) - {gone})
            self.assertEqual(len(names), 3)
            self.assert_96_refused(bad_record(drop=(gone,)), f"the record {rel} holds {names}, not dt and t_turb")
        with open(keep, "rb") as fh:
            whole = fh.read()
        npy = io.BytesIO()
        np.save(npy, good["t_turb"])
        for data, kind in ((b"SYNTHETIC: not an npz", "ValueError"), (whole[:len(whole) // 2], "BadZipFile"),
                           (npy.getvalue(), "TypeError")):                  # not a zip, a truncated npz, a bare .npy
            self.assert_96_refused(bad_record(data=data), f"the record {rel} does not load as an npz ({kind}: ")

        def rezipped(members):                                              # the record's zip, members replaced
            buf = io.BytesIO()
            with zipfile.ZipFile(io.BytesIO(whole)) as zin, zipfile.ZipFile(buf, "w") as zout:
                for item in zin.infolist():
                    name = item.filename
                    if name in members:
                        name, data = members[name]
                    else:
                        data = zin.read(name)
                    zout.writestr(name, data)
            return buf.getvalue()
        res = bad_record(data=rezipped({"dt.npy": ("dt", b"abc")}))          # a member without .npy: np.load
        self.assert_96_refused(res, not_f64.format("|S3 ()"))               # hands back its raw bytes
        hdr = "{'descr': '<f8', 'fortran_order': False, 'shape': (), }"     # a v2.0 .npy with a 20000-byte header:
        hdr += " " * (20000 - len(hdr) - 1) + "\n"                          # numpy refuses it in several lines
        long_dt = b"\x93NUMPY\x02\x00" + struct.pack("<I", len(hdr)) + hdr.encode("latin1") + struct.pack("<d", 1.0)
        res = bad_record(data=rezipped({"dt.npy": ("dt.npy", long_dt)}))
        self.assert_96_refused(res, f"the record {rel} does not load as an npz (ValueError: Header info length "
                                    "(20000) is large")
        self.assertEqual(broken(BS.render(res)), [])
        with self.assertRaises(AB.B58HError) as cm:                         # _load_record's own text is one line
            BS._load_record(path, rel)
        self.assertEqual(broken([str(cm.exception)]), [])
        self.assertEqual(str(cm.exception), res["part_9_6"]["status"][len("not computed: "):])
        with open(path, "rb") as fh, np.load(fh, allow_pickle=False) as z, self.assertRaises(ValueError) as raw:
            z["dt"]
        self.assertGreater(len(str(raw.exception).splitlines()), 1)         # the control: numpy's text is not
        shutil.copyfile(keep, path)
        self.assertEqual(reindex(fx.records, fx.files)["part_9_6"]["status"], "computed")   # the control
        flat = os.path.join(fx.base, "records_1d")                         # every record's t_turb 1-d of n_roads:
        for name in fx.files:                                               # one shape, and shape[0] is n_roads
            with np.load(os.path.join(fx.records, *name.split("/"))) as z:
                arrays = {k: np.array(z[k]) for k in z.files}
            arrays["t_turb"] = np.ascontiguousarray(arrays["t_turb"][:, 0])
            os.makedirs(os.path.join(flat, os.path.dirname(name)), exist_ok=True)
            np.savez(os.path.join(flat, *name.split("/")), **arrays)
        files = {name: AB.sha256_file(os.path.join(flat, *name.split("/"))) for name in fx.files}
        self.assert_96_refused(reindex(flat, files), f"the record b58/baseline.npz's t_turb is float64 ({N},), not "
                                                     f"finite float64 ({N}, steps)")
        rows = {"hand": {V.BASELINE: fx.rows["hand"][V.BASELINE][:-1]},   # every record one road short: one
                "agents": {key: rs[:-1] for key, rs in fx.rows["agents"].items()}}  # shape, not the scores' roads
        short = os.path.join(fx.base, "records_short")
        files = V.write_records(short, "b58", rows, dt=1.0)
        self.assert_96_refused(reindex(short, files), f"t_turb is float64 ({N - 1}, {STEPS}), not finite float64 "
                                                      f"({N}, steps)")

    def test_load_record_closes_its_file(self):                             # round 2's T1: the handle is its own
        fx, _ = shared()
        rel = "b58/blind_seed3.npz"
        good = os.path.join(fx.records, *rel.split("/"))
        with open(good, "rb") as fh:
            whole = fh.read()
        trunc = os.path.join(fresh("handle"), "truncated_record.npz")
        put_bytes(trunc, whole[:len(whole) // 2])                           # np.load(path) leaves its own open here

        def unclosed(call, path):
            """ResourceWarnings naming `path` from one call, every cycle collected (none left to the GC)."""
            gc.collect()
            with warnings.catch_warnings(record=True) as caught:
                warnings.simplefilter("always")
                try:
                    call(path)
                except AB.B58HError:
                    pass
                gc.collect()
            return [str(w.message) for w in caught if issubclass(w.category, ResourceWarning)
                    and os.path.basename(path) in str(w.message)]
        for path in (trunc, good):
            self.assertEqual(unclosed(lambda p: BS._load_record(p, rel), path), [], path)
        self.assertEqual(len(unclosed(lambda p: open(p, "rb"), trunc)), 1)  # the control: an unclosed file is seen
        with self.assertRaises(AB.B58HError):                              # and the truncated one is refused
            BS._load_record(trunc, rel)

    def test_sha_text_not_the_raw_sha256(self):
        fx = Fixture("crlf")
        with open(fx.scores, encoding="utf-8") as fh:
            text = fh.read()
        fx.write_text(fx.scores, text, newline="\r\n")                     # a CRLF checkout of the same blob
        raw = AB.sha256_file(fx.scores)
        self.assertNotEqual(raw, fx.sha)
        self.assertEqual(TC.sha_text(fx.scores), fx.sha)
        res = fx.compute()
        self.assertEqual(res["part_9_6"]["status"], "computed")
        with self.assertRaises(AB.B58HError):                               # the control: the raw sha256 fails
            BS.read_records(fx.index, fx.records, sha_text=raw, seeds=[str(s) for s in SEEDS], n_roads=N,
                            root=fx.root)

    def test_the_knee(self):
        rows = make_rows()
        top = max(max(r["trace"]["t_turb"]) for rs in [*rows["hand"].values(), *rows["agents"].values()] for r in rs)
        cg0 = rows["hand"][BS.CG][0]["trace"]["t_turb"]
        hot = top + 5.0
        cg0[3] = hot                                                        # current-grade holds the hottest step
        rows["hand"][BS.CG][0]["peak_turb"] = hot - 273.15
        fx = Fixture("knee", rows=rows, knee_k=hot)                         # a peak exactly at the knee reaches it
        res = fx.compute()
        k = res["part_9_6"]["knee"]
        self.assertTrue(k["reached"])
        self.assertFalse(k["reached_850"])                                  # the knee here is below 850 deg C
        self.assertEqual(k["highest_recorded_peak_c"], k["threshold_c"])
        self.assertEqual(sorted(res["part_9_6"]["limits_c"]), ["778", "804", "knee"])
        for arm in BS.ARMS:
            self.assertIn("above_knee", res["part_9_6"]["per_arm"][arm])
            self.assertNotIn("above_850", res["part_9_6"]["per_arm"][arm])
        self.assertEqual(res["part_9_6"]["current_grade"]["above_knee"], 0.0)   # at it, not above it
        self.assertIn("it reaches the knee, so the seconds above the knee are reported", "\n".join(BS.render(res)))

        def off(kk, fuel):                                                  # control 1 fails: its row drops out
            return fuel + 1.0 if kk == 0 else fuel
        res = fx.compute(runner=fake_runner(fx.rows, fuel_of=off))
        self.assertIsNone(res["part_9_6"]["current_grade"])
        self.assertFalse(res["part_9_6"]["knee"]["reached"])
        self.assertEqual(sorted(res["part_9_6"]["limits_c"]), ["778", "804"])
        res = Fixture("knee_hi", rows=make_rows(), knee_k=hot + 1.0).compute()
        self.assertFalse(res["part_9_6"]["knee"]["reached"])

    def assert_seconds_by_hand(self, fx, p, labs):
        """Every agent's, the arms', the baseline ECU's, current-grade's and the differences' seconds above each
        limit in `labs`, against a count by hand (strictly above, dt 1 s, mean over the roads)."""
        def above(rows, lim):
            return sum(sum(1.0 for x in r["trace"]["t_turb"] if x - 273.15 > lim) for r in rows) / N
        for lab in labs:
            lim = p["limits_c"][lab]
            for arm in BS.ARMS:
                mine = [above(fx.rows["agents"][(arm, s)], lim) for s in SEEDS]
                self.assertEqual([p["agents"][arm][str(s)][f"above_{lab}"] for s in SEEDS], mine, (lab, arm))
                self.assertAlmostEqual(p["per_arm"][arm][f"above_{lab}"], sum(mine) / len(SEEDS), places=12)
            for r in RATIOS:
                d = [above(fx.rows["agents"][(f"sighted_r{r}", s)], lim) - above(fx.rows["agents"][("blind", s)], lim)
                     for s in SEEDS]
                np.testing.assert_allclose(p["differences"][r][f"above_{lab}"]["values"], d, rtol=0, atol=1e-12)
            self.assertEqual(p["baseline"][f"above_{lab}"], above(fx.rows["hand"][V.BASELINE], lim), lab)
            self.assertEqual(p["current_grade"][f"above_{lab}"], above(fx.rows["hand"][BS.CG], lim), lab)

    def test_850_by_every_policy_s_peak(self):                              # the knee read from roads.json: 1123 K
        def hot(rows, cells):
            for (who, road, step, kelvin) in cells:
                rs = rows["hand"][who] if isinstance(who, str) else rows["agents"][who]
                rs[road]["trace"]["t_turb"][step] = kelvin
                rs[road]["peak_turb"] = max(rs[road]["trace"]["t_turb"]) - 273.15
            return rows
        # an agent alone sets it off, at or above the knee and below 850 deg C: the knee's seconds, not 850's
        fx = Fixture("knee_agent", knee_k=1123.0, rows=hot(make_rows(), [(("blind", 5), 2, 4, 1123.1)]))
        p = fx.compute()["part_9_6"]
        self.assertGreaterEqual(p["knee"]["threshold_c"], 849.0)
        self.assertLess(p["knee"]["threshold_c"], BS.ABOVE_850_C)
        self.assertEqual((p["knee"]["reached"], p["knee"]["reached_850"]), (True, False))
        self.assertEqual(sorted(p["limits_c"]), ["778", "804", "knee"])
        self.assertEqual(p["agents"]["blind"]["5"]["above_knee"], 1.0 / N)
        self.assertLess(max(p["baseline"]["peak_max"], p["current_grade"]["peak_max"]), p["knee"]["threshold_c"])
        self.assert_seconds_by_hand(fx, p, ["778", "804", "knee"])
        # the baseline ECU alone reaches 850 deg C; an agent sits between the knee and 850: both are reported
        cells = [(V.BASELINE, 0, 2, 1123.1), (V.BASELINE, 0, 5, 1124.0), (("sighted_r1.5", 2), 7, 1, 1123.05)]
        fx = Fixture("knee_base", knee_k=1123.0, rows=hot(make_rows(), cells))
        res = fx.compute()
        p = res["part_9_6"]
        self.assertEqual((p["knee"]["reached"], p["knee"]["reached_850"]), (True, True))
        self.assertEqual(sorted(p["limits_c"]), ["778", "804", "850", "knee"])
        self.assertEqual((p["limits_c"]["850"], p["limits_c"]["knee"]), (850.0, 1123.0 - 273.15))
        self.assertEqual((p["baseline"]["above_knee"], p["baseline"]["above_850"]), (2.0 / N, 1.0 / N))
        one = p["agents"]["sighted_r1.5"]["2"]
        self.assertEqual((one["above_knee"], one["above_850"]), (1.0 / N, 0.0))
        agents_top = max(p["agents"][a][s]["peak_max"] for a in BS.ARMS for s in p["agents"][a])
        self.assertLess(agents_top, BS.ABOVE_850_C)                         # so the baseline's peak set it off
        self.assert_seconds_by_hand(fx, p, ["778", "804", "knee", "850"])
        self.assertIn("it reaches the knee and 850 deg C", "\n".join(BS.render(res)))

    def test_current_grade_s_trace_shape(self):
        fx, base = shared()
        self.assertIsNotNone(base["part_9_6"]["current_grade"])              # the control

        def longer(k, trace):                                               # every road one step longer
            return {key: v + [v[-1]] for key, v in trace.items()}
        res = fx.compute(runner=fake_runner(fx.rows, trace_of=longer))
        self.assertEqual(res["part_9_5_i"]["status"], "computed")
        self.assertEqual(res["part_9_6"]["status"], "computed")
        self.assertIsNone(res["part_9_6"]["current_grade"])
        self.assertEqual(res["part_9_6"]["current_grade_note"],
                         f"not computed: its trace is ({N}, {STEPS + 1}), the records ({N}, {STEPS})")


# ------------------------------------------------------------------------------------------ RealShortRoads
def short_road(n, *, k, seed, weights, onset):
    """test_scoring_protocol.short_road's pattern: the roads' launch and speed, n one-second samples, a 10 %
    climb from `onset` s, scalar p_baro (a list would not pass epa_roads.env_cycle)."""
    t, v = ER.time_and_speed()
    t, v = t[:n], v[:n]
    grade = ER.climb_profile(t, float(onset), 30.0, 0.10)
    return {"k": k, "episode_seed": seed, "weights": [float(w) for w in weights], "dt": 1.0,
            "cycle": {"t": [float(x) for x in t], "v_mps": [float(x) for x in v], "grade": [float(x) for x in grade],
                      "t_amb": [ER.T_AMB_K] * n, "p_baro": ER.P_BARO_KPA, "humidity": ER.HUMIDITY}}


class RealShortRoads(Case):
    def test_current_grade_through_run_road_episode(self):
        roads = [short_road(8, k=0, seed=V.EPISODES[0][0], weights=V.EPISODES[0][1], onset=3),
                 short_road(8, k=1, seed=V.EPISODES[1][0], weights=V.EPISODES[1][1], onset=1)]
        tasks = [(BS.ENGINE, road, False) for road in roads]
        one = BS.run_roads(tasks, n_jobs=1)
        two = BS.run_roads(tasks, n_jobs=2)                                 # the spawn pool, its own processes
        self.assertEqual(one, two)
        for road, row in zip(roads, one):
            self.assertEqual(sorted(row), sorted(BS.KEEP + ("trace",)))
            self.assertEqual(row["steps"], 7)
            self.assertEqual({k: len(v) for k, v in row["trace"].items()}, {k: 7 for k in BS.TRACE_KEYS})
            direct = V.run_road_episode(CP.p_grade_now, road, plant=engines.get("b58"), use_preview=True,
                                        preview_h_s=V.PREVIEW_H_S, reward_knock=False)
            self.assertEqual({k: direct[k] for k in BS.KEEP}, {k: row[k] for k in BS.KEEP})
            self.assertEqual(direct["trace"]["t_turb"], row["trace"]["t_turb"])
        neutral = V.run_road_episode(CP.p_neutral, roads[0], plant=engines.get("b58"), use_preview=True,
                                     preview_h_s=V.PREVIEW_H_S, reward_knock=False)
        self.assertNotEqual((neutral["fuel"], neutral["damage_thermal"]),
                            (one[0]["fuel"], one[0]["damage_thermal"]))     # the control: the policy reached it


# ------------------------------------------------------------------------------------------ Guard
class Guard(Case):
    def test_the_guard_fires(self):
        for parts in (("runs", "b58h_dt1", "__guard_probe_never_exists__.zip"),
                      ("runs", "b58h_check_dt1", "__guard_probe_never_exists__.npz")):
            path = os.path.join(HERE, *parts)                               # never there: the hook refuses first
            with self.assertRaises(PermissionError):
                open(path, "rb")
            with self.assertRaises(PermissionError):
                np.load(path)
        self.assertEqual(len(GUARD["hits"]), 4)
        GUARD["hits"][:] = []
        for parts in (("results", "EPA_ROADS", "attempt_1_printed.txt"), ("logs", "epa", "x.csv"),
                      ("data", "engines", "b58", "epa_x.csv"), ("runs", "b58h_dt1")):
            self.assertTrue(_forbidden(os.path.join(HERE, *parts)), parts)  # checked, never opened
        self.assertTrue(_forbidden(os.path.join(os.path.expanduser("~"), "Documents",
                                                "GRAD_row96_integers_2026-10-31.txt")))
        self.assertFalse(_forbidden(os.path.join(HERE, "b58h_beside.py")))
        for name in ("load_agent", "read_agents", "average_lines"):
            with self.assertRaises(AssertionError):
                getattr(V, name)("runs/b58h_dt1/blind_seed0", {}, device="cpu")
        with open(os.path.join(HERE, "b58h_beside.py"), "rb"):             # an ordinary file opens
            pass

    def test_core_names_no_agent_loader(self):
        with open(os.path.join(HERE, "b58h_beside.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        banned = {"load_agent", "read_agents", "average_lines", "agent_policy", "AveragedPolicy", "SAC",
                  "model_budget", "load_checkpoint"}
        names = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)}
        names |= {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
        self.assertEqual(names & banned, set())
        mods = {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
        mods |= {n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
        self.assertEqual(mods & {"stable_baselines3", "zipfile", "training_recipe"}, set())
        torch_uses = {n.attr for n in ast.walk(tree) if isinstance(n, ast.Attribute)
                      and isinstance(n.value, ast.Name) and n.value.id == "torch"}
        self.assertEqual(torch_uses, {"set_num_threads"})
        injected = ast.parse("import evaluate as V\nV.load_agent('x', {}, device='cpu')\n")
        self.assertIn("load_agent", {n.attr for n in ast.walk(injected) if isinstance(n, ast.Attribute)})

    def test_every_np_load_refuses_pickles(self):                           # DESIGN 2.4: allow_pickle=False
        def loads(tree):
            calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                     and n.func.attr == "load" and isinstance(n.func.value, ast.Name) and n.func.value.id == "np"]
            return [any(k.arg == "allow_pickle" and isinstance(k.value, ast.Constant) and k.value.value is False
                        for k in c.keywords) for c in calls]
        with open(os.path.join(HERE, "b58h_beside.py"), encoding="utf-8") as fh:
            found = loads(ast.parse(fh.read()))
        self.assertTrue(found)
        self.assertTrue(all(found), found)
        self.assertEqual(loads(ast.parse("import numpy as np\nnp.load('x', allow_pickle=True)\nnp.load('y')\n")),
                         [False, False])                                    # the control: the scan sees them


# ------------------------------------------------------------------------------------------ Text
def forbidden_in(text):
    return [p for p in FORBIDDEN if p in text]


class Text(Case):
    def test_no_forbidden_phrase(self):
        _, res = shared()
        text = "\n".join(BS.render(res))
        self.assertEqual(forbidden_in(text), [])
        self.assertEqual(forbidden_in(text + "\nso preview does not help"), ["preview does not help"])  # control
        text.encode("ascii")
        for name in ("DESCRIPTIVE", "KNOCK_STATEMENT_V", "TEMPS_STATEMENT", "HW_LABEL", "D13_LABEL"):
            self.assertEqual(forbidden_in(getattr(BS, name)), [], name)

    def test_every_with_knock_line_carries_its_label(self):                 # PR-B:1101, :819
        _, res = shared()
        failed = json.loads(json.dumps(res))                                # control 3's failing branch prints too
        failed["controls"]["3"]["passed"] = False
        failed["part_9_5_i"]["control_3_beside"] = failed["controls"]["3"]["by"]
        lab = FEA.WITH_KNOCK_LABEL
        for r in (res, failed):
            lines = BS.render(r)
            named = [ln for ln in lines if re.search(r"with[ _]knock|reading knock", ln)]
            self.assertGreater(len(named), 10)
            self.assertEqual([ln for ln in named if lab not in ln], [])
            self.assertEqual(unlabelled(lines), [])                         # every bracketed number, named or not
        self.assertEqual(unlabelled(["    x +1.0000 [+2.0000]", "      t: 95 % t interval [+1.0, +2.0]"]),
                         ["    x +1.0000 [+2.0000]"])                     # the control: the scan sees one
        per_seed = [ln for ln in BS.render(res) if ln.startswith("    per seed, s no knock")]
        self.assertEqual(len(per_seed), len(BS.ARMS))
        self.assertTrue(all(lab in ln for ln in per_seed))
        self.assertTrue(any("control 3 FAILED" in ln and lab in ln for ln in BS.render(failed)))
        lines = BS.render(res)
        cut = res["part_9_5_i"]["current_grade_cut"]                        # current-grade's cut, both brackets
        self.assertIn(f"  current-grade's cut against the baseline ECU: evaluate.py's form "
                      f"{cut['no_knock']['evaluate_form']:+.4f} [with knock {cut['with_knock']['evaluate_form']:+.4f}, "
                      f"{lab}]; mean form {cut['no_knock']['mean_form']:+.4f} [with knock "
                      f"{cut['with_knock']['mean_form']:+.4f}, {lab}]", lines)
        for rd, labelled in (("noknock", False), ("knock", True)):          # every line under each reading of the
            head = f"    reading {rd}" + (f" ({lab})" if labelled else "") + ":"   # tuned bests, named or not
            block = []
            for ln in lines[lines.index(head) + 1:]:
                if not ln.startswith("      "):
                    break
                block.append(ln)
            self.assertGreaterEqual(len(block), 5, rd)                      # three families and two frontier lines
            self.assertEqual([lab in ln for ln in block], [labelled] * len(block), rd)

    def test_each_reading_s_numbers_under_its_own_name(self):              # control 3's two readings, by value
        _, res = shared()
        lab = FEA.WITH_KNOCK_LABEL
        failed = json.loads(json.dumps(res))
        by = {"no_knock": {"max_abs": 2e-6, "road": 4, "max_rel": 3e-8},
              "with_knock": {"max_abs": 5e-7, "road": 9, "max_rel": 7e-9}}
        failed["controls"]["3"].update(passed=False, by=by)
        failed["part_9_5_i"]["control_3_beside"] = by
        lines = BS.render(failed)
        self.assertIn("    no knock: largest absolute difference 2.000e-06 (road 4), largest relative 3.000e-08", lines)
        self.assertIn(f"    with knock ({lab}): largest absolute difference 5.000e-07 (road 9), largest relative "
                      "7.000e-09", lines)
        beside = [ln for ln in lines if ln.startswith("  control 3 FAILED")]
        self.assertEqual(len(beside), 1)
        self.assertTrue(beside[0].endswith(f": no knock largest absolute 2.000e-06 (road 4), relative 3.000e-08; "
                                           f"with knock ({lab}) largest absolute 5.000e-07 (road 9), relative "
                                           "7.000e-09"), beside[0])

    def test_each_arm_s_numbers_under_their_reading(self):                 # PR-B:817-819, :1101: no knock primary,
        _, res = shared()                                                   # with knock beside it, each named
        lab = FEA.WITH_KNOCK_LABEL
        p = res["part_9_5_i"]
        name = {"no_knock": "no knock", "with_knock": f"with knock ({lab})"}
        form_name = {"evaluate_form": "evaluate.py's form", "mean_form": "mean form"}
        lines = BS.render(res)
        for arm in BS.ARMS:
            want = []
            for rd in BS.READINGS:
                for form in ("evaluate_form", "mean_form"):
                    st = p["per_arm"][arm][rd][form]
                    want.append(f"    {form_name[form]}, {name[rd]}: {st['below_0']} of {st['n']} agents with s < 0; "
                                f"median {st['median']:+.4f}, sd {st['sd']:.4f} (ddof 1), range {st['min']:+.4f} to "
                                f"{st['max']:+.4f}")
            s = p["s"][arm]
            pairs = [(x, s[x]["no_knock"]["evaluate_form"], s[x]["with_knock"]["evaluate_form"])
                     for x in sorted(s, key=int)]
            want.append(f"    per seed, s no knock [with knock, {lab}], evaluate.py's form: "
                        + ", ".join(f"{x} {nk:+.4f} [{wk:+.4f}]" for x, nk, wk in pairs))
            for rd in BS.READINGS:
                hw = [h for h in p["hand_written"]["table"][rd] if h["r"] in p["hand_written"]["by_arm"][arm]]
                want.append(f"    beside, hand-written savings over current-grade, evaluate.py's form, {name[rd]}: "
                            + "; ".join(f"({h['policy']}) at r = {h['r']} {h['evaluate_form']:+.4f} [mean form "
                                        f"{h['mean_form']:+.4f}]" for h in hw))
            start = lines.index(f"  {arm}:") + 1
            self.assertEqual(lines[start:start + len(want)], want, arm)
            for i, j in ((0, 2), (1, 3), (5, 6)):                           # the control: the readings print other
                self.assertNotEqual(want[i].split(": ", 1)[1], want[j].split(": ", 1)[1], (arm, i, j))   # numbers,
            self.assertTrue(any(f"{nk:+.4f}" != f"{wk:+.4f}" for _, nk, wk in pairs), arm)   # so a swap is seen

    def test_printed_decimals(self):                                         # the module docstring's choices
        _, res = shared()
        lines = BS.render(res)
        per_seed = [ln for ln in lines if ln.startswith("    per seed, s no knock")]
        pairs = re.findall(r"(\d+) ([+-]\d+\.(\d+)) \[([+-]\d+\.(\d+))\]", per_seed[0].split(": ", 1)[1])
        self.assertEqual(len(pairs), len(SEEDS))
        self.assertEqual({len(p[2]) for p in pairs} | {len(p[4]) for p in pairs}, {4})    # s at 4 decimals
        seconds = [m for ln in lines if ln.startswith("    seed ") for m in re.findall(r"s above \w+ (\d+\.(\d+))", ln)]
        self.assertEqual(len(seconds), 2 * len(SEEDS) * len(BS.ARMS))
        self.assertEqual({len(m[1]) for m in seconds}, {2})                 # seconds at 2
        summaries = [ln for ln in lines if re.match(r"^      (peak_mean|peak_max|above_\w+): n ", ln)]
        self.assertEqual(len(summaries), 4 * len(RATIOS))
        for ln in summaries:
            m = re.search(r"mean ([+-]\d+\.(\d+)), 95 % t interval \[([+-]\d+\.(\d+)), ([+-]\d+\.(\d+))\] "
                          r"\(t (\d+\.(\d+)), sd (\d+\.(\d+))", ln)
            self.assertEqual([len(m.group(i)) for i in (2, 4, 6, 8, 10)], [2, 2, 2, 4, 2], ln)
        start = lines.index("9.6 THE TEMPERATURE ROWS, the modelled housing (row 151)")
        temps = [m for ln in lines[start:] for m in re.findall(r"(?:peak mean|highest(?: single| recorded)?(?: peak)?) "
                                                                r"(\d+\.(\d+))", ln)]
        self.assertGreater(len(temps), 3 * len(SEEDS))                      # 9.6's temperatures at 2 (T10)
        self.assertEqual({len(m[1]) for m in temps}, {2})
        self.assertIn("  limits, deg C (seconds strictly above, dt x steps): 778 = 778.00, 804 = 804.00", lines)
        k = res["part_9_6"]["knee"]                                         # the knee in K and deg C, 850 and the
        self.assertEqual(k["turb_knee_k"], 1123.0)                          # highest recorded peak, each at 2
        self.assertIn("  850 deg C, both readings (PR-B 9.6): the knee, turb_knee_k 1123.00 K = 849.85 deg C "
                      "(roads.json report.knee_shares), and 850.00 deg C; highest recorded peak "
                      f"{k['highest_recorded_peak_c']:.2f} deg C: no recorded peak reaches either", lines)
        seed_peaks = [re.match(r"    seed \d+: peak mean (\d+\.(\d+)), highest (\d+\.(\d+)) deg C", ln)
                      for ln in lines[start:] if ln.startswith("    seed ")]
        self.assertEqual(len(seed_peaks), len(SEEDS) * len(BS.ARMS))
        self.assertEqual({(len(m.group(2)), len(m.group(4))) for m in seed_peaks}, {(2, 2)})
        v_nd = {"fuel figure, % points": 4, "mean short share (roads with a demand step)": 6,
                "pooled short share": 6}                                    # 9.5 (v): the fuel figure 4, shares 6
        for name, nd in v_nd.items():
            got = [re.search(r": n \d+, mean [+-]\d+\.(\d+), 95 % t interval \[[+-]\d+\.(\d+), [+-]\d+\.(\d+)\] "
                             r"\(t \d+\.(\d+), sd \d+\.(\d+)", ln)
                   for ln in lines if ln.startswith(f"      {name}: n ")]
            self.assertEqual(len(got), len(RATIOS), name)
            self.assertEqual({tuple(len(g) for g in m.groups()) for m in got}, {(nd, nd, nd, 4, nd)}, name)
        beside = [re.fullmatch(r"  beside, .+'s own: fuel figure [+-]\d+\.(\d+) %, mean short share \d\.(\d+), "
                               r"pooled \d\.(\d+)", ln) for ln in lines if ln.startswith("  beside, ")]
        self.assertEqual(len(beside), 2)
        self.assertEqual({tuple(len(g) for g in m.groups()) for m in beside}, {(4, 6, 6)})


if __name__ == "__main__":
    unittest.main(verbosity=2)
