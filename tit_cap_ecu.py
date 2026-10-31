"""tit_cap_ecu.py -- decision 62's TIT-cap ECU (row 105): the Ford's baseline ECU enriching by the least amount
that holds the model's turbine-inlet temperature at or below a cap, as a patch of engine_env.BaselineECU.step
outside PLANT_CODE.

    imported, never trained on; its test is test_tit_cap.py. Two measurements of its own, on the plant only:
    python -B tit_cap_ecu.py probe --engine ford_27tt
        the model TIT against lambda at a grid of ECU operating points (no cap, no EPA row)
    python -B tit_cap_ecu.py climb --engine ford_27tt --record PATH --which cap|egt_limit --duration S --dt S
                                   [--uncommitted]
        the plant's locked climb, neutral action, unpatched (the control) and under the record's cap: what the
        cap did, step by step counted, and the realised TIT, t_turb, damage and fuel of both runs. --uncommitted
        admits a record outside results/EPA_TIT_CAP/ or from uncommitted code (a measurement, never row 115's)

    --engine is required (mistake 1: no default engine). OMP_NUM_THREADS=1 MKL_NUM_THREADS=1, as every command.

Build step 2, ORDER step 5 (docs/build_step_2/ORDER_TO_TRAINING.md, step 5). Decision 62 (results/
VALIDATION_DECISIONS.md, row 62) as amendment 62 changes it (docs/build_step_2/AMENDMENTS.md, amendment 62: "an
ECU patch outside PLANT_CODE in ecu_shift.py:70-78's pattern, closing over the plant, that solves for the least
lambda holding model TIT <= cap"), and row 105, which puts it outside PLANT_CODE, CODE_HASHED and thresholds/ (row
94). Its inputs are the note at engine_env.py:888-894, followed exactly. Nothing here edits engine_env.py: the class
attribute is swapped inside capped() and put back on the way out.

THE OPERATING POINT (engine_env.py:888-894). step's own arguments -- rpm, the MAP it is given (the environment
passes the previous step's baseline pressure, map_b_prev, engine_env.py:1283-1285), iat_k and ect_k --, the
spark the ECU's own step returns, the cam the ECU schedules on the same load (self.cam_deg(rpm, map_kpa), as
engine_env.py:1290 calls it; None on an engine without form D) and plant.exhaust_backpressure_kpa(map_kpa,
engine=...) (plant.py:381) make the plant.Operating at which plant.run_cycle (plant.py:199) gives the model
TIT: egt_c + 273.15, in K, the gas temperature the environment hands both thermal networks (engine_env.py:1057)
and the quantity Run 1 fitted to EPA's turbine-inlet thermocouple, egt_c against the row's tit_c in degC
(epa_fit.py:2067; epa_rows.PointRow, epa_rows.py:336-337). Not the housing node t_turb, which the damage knee
reads (mistake 23). test_tit_cap.Patch checks at every acted step that the lambda, spark, cam, rpm, iat and ect
recorded here are the ones the baseline's load loop then ran (engine_env._track_torque), and the MAP the
environment's map_b_prev.

THE LEAST ENRICHMENT (least_enrichment). lambda_ECU is the lambda of the ECU's own step. If TIT(lambda_ECU) <=
cap, the step returns the original tuple itself, so a cap above every TIT reached changes no bit. Otherwise
lambda is scanned down from lambda_ECU in steps of SCAN_STEP to the ECU's own floor (EcuCal.lam_floor, the clip
engine_env.py:1316 applies to every policy) until a lambda holds the cap, and that bracket is bisected to
LAMBDA_TOL: the lambda returned holds TIT <= cap, the bracket's lean end one LAMBDA_TOL away does not. Enrichment
only, so the result lies in [lam_floor, lambda_ECU], inside the ECU's bounds [lam_floor, lam_ceiling] (engines.
EcuCal; lambda_ECU <= 1 <= lam_ceiling by engines.Engine's check, engines.py:603). Spark, fan and the ECU's state
(knock retard, dwell timer) are the original step's: it runs once, first, as thresholds/ecu_shift.py:72 runs it.
The lambda returned is a Python float, as the original's is (amendment B10).
  A scan, not a bisection over [lam_floor, lambda_ECU], because the model TIT is not monotone in lambda.
  MEASURED on the frozen Ford, 31 October 2026 (`python -B tit_cap_ecu.py probe --engine ford_27tt`: 20 points,
  1500-5500 rpm by 1000, 100-250 kPa by 50, lambda 0.698 to 1 in 152 points): from lambda 1 the TIT falls by
  8.90-23.81 K to a minimum at lambda 0.700-0.844 and rises again toward the floor 0.698, by 0.03-11.50 K; the
  largest reversal on either side of the minimum is 0.0227 K (not explained here: no run at another crank-angle
  step was made). Enrichment can therefore lower this model's TIT by at most about 24 K on that grid, and an ECU
  lambda rich of the minimum can only be made hotter by more. The scan finds the leanest crossing below
  lambda_ECU, which is the least enrichment; a crossing narrower than SCAN_STEP could be stepped over, which a
  TIT this smooth in lambda does not show on the grid, and a cap within a few hundredths of a K of the minimum is
  inside the reversals.

NO LAMBDA IN BOUNDS HOLDS THE CAP (results/VALIDATION_DECISIONS.md, row 124 (1), answered 31 October 2026 by both,
on the review's finding F1): the step returns the lambda of least model TIT in [lam_floor, lambda_ECU] (least_tit: the
scan's points, lambda_ECU and lam_floor among them, then a golden-section search to LAMBDA_TOL around the
least of them, and the least TIT of every point evaluated, the leanest on a tie), and counts the step as unheld
(CapStats.unheld). That is the closest to holding the cap enrichment can come, and never hotter than lambda_ECU,
which is one of the points (CapStats.unheld_hotter counts the steps where it would be, and stays 0;
CapStats.unheld_unchanged the steps where lambda_ECU itself is the least TIT, so nothing changes). The first build
returned lam_floor, the rich bound: since this model's TIT rises again toward the floor, the review of 31 October
(finding F1, a scratch run beside the build) found that it made the capped baseline hotter than the unpatched one
on the Ford's locked climb at the primary cap, which is not decision 62's "least enrichment that holds TIT <=
cap". The other alternative, lambda_ECU unchanged, was rejected by row 124: the row would then move only on the
held steps.

WHICH ECUs (capped). An ECU whose calibration IS plant.engine.ecu (the object: SupervisoryTunerEnv builds
BaselineECU(plant.engine.ecu), engine_env.py:1021) is capped on the closed-over plant's cycle; one whose
calibration equals it but is another object is refused (RuntimeError), since its engine cannot be told from its
ECU; any other ECU runs the original step and is counted as passed (the B58 inside the context is unchanged). A
variant of the plant made with dataclasses.replace keeps engine.ecu, and is capped on the plant passed to
capped(): pass the variant itself, and run one plant per context.

ONE PROCESS (the review's finding S9). capped() swaps the class attribute in the process that enters it, and in
no other: a pool's workers (multiprocessing's spawn, as the roads code uses) run the frozen ECU unless each enters
capped() itself, from the pool's initializer or around its own episodes. A run that applies the cap checks
CapStats.calls against the steps it ran, as climb does (a context whose calls stay 0 capped nothing).

THE CAP is a number (capped's cap_k), or read from row 105's record by cap_from_record: "cap", the highest TIT on
the Ford's calibration Final rows (row 105's rule, decision 62's first option), or "egt_limit", the spec's
egt_limit_k (ASSUMED, the second sensitivity row). The record is refused (record_problems, the review's finding
I2) unless its schema, plant and engine_sha are this plant's, its audit refused nothing and found nothing
outside the allowlist (before the audit included), its cap.tit_k is its cap.tit_c + 273.15 and its second cap the
plant's egt_limit_k, and its sha_text and code_sha_text equal the files as they are now (a record made before an
edit of this module or tit_cap.py is stale); and, unless the caller says committed=False (a measurement), unless
its git block says the code was committed and clean, its audit watched the imports (the command line's prelude),
and the file itself is <this tree>/RECORD_DIR/<plant>.json, tracked and unmodified (committed_problem). This module never imports epa_rows: the rows are tit_cap.py's, read
once.

PREDICTED, NOT REALISED. The cap holds the model TIT at the ECU's operating point, which is all the ECU sees: the
baseline's load loop then runs at its own pressure (engine_env._track_torque, three inner iterations), so the
TIT the networks receive can differ from the one held. `climb` counts the steps where it exceeds the cap, in the
capped run and in the unpatched control.
"""
import argparse
import contextlib
import dataclasses
import json
import math
import os
import statistics
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import engine_env  # noqa: E402
import engines  # noqa: E402
import plant as P  # noqa: E402

SCHEMA = "epa-tit-cap/2"            # tit_cap.SCHEMA, the record this module reads (test_tit_cap pins them equal)
RECORD_DIR = "results/EPA_TIT_CAP"  # tit_cap.RECORD_DIR
RECORD_HASHED = ("tit_cap.py", "tit_cap_ecu.py", "epa_rows.py")     # tit_cap.HASHED
LAMBDA_TOL = 1e-4                   # DESIGN: the bisection's width in lambda (EPA prints lambda to 0.001)
SCAN_STEP = 0.01                    # DESIGN: the downward scan's step in lambda
WHICH = ("cap", "egt_limit")        # the record's two caps: row 105's primary and its second sensitivity row
ORIGINAL_QUALNAME = "BaselineECU.step"
GOLDEN = (math.sqrt(5.0) - 1.0) / 2.0


@dataclasses.dataclass
class CapStats:
    """What one capped() context did. calls: patched steps of the plant's own ECUs; acted: those whose
    TIT(lambda_ECU) exceeded the cap; held: acted and a lambda in bounds held it; unheld: acted and none did (the
    lambda of least TIT returned); unheld_hotter: unheld steps where the TIT returned exceeds TIT(lambda_ECU) (0
    by construction, kept as a check); unheld_unchanged: unheld steps where lambda_ECU is itself the least TIT;
    passed: steps of another plant's ECU, run unchanged; tit_max_k: the highest TIT(lambda_ECU) seen; steps:
    every acted step's inputs and outcome when keep_steps (call: its 0-based index among the context's calls, rpm,
    map_kpa, iat_k, ect_k, spark, cam, lam_ecu, tit_ecu_k, lam, tit_k, outcome), else None."""
    cap_k: float
    calls: int
    acted: int
    held: int
    unheld: int
    unheld_hotter: int
    unheld_unchanged: int
    passed: int
    tit_max_k: float
    steps: object

    def as_json(self):
        return {k: v for k, v in dataclasses.asdict(self).items() if k != "steps"}


def model_tit_k(plant, *, rpm, map_kpa, iat_k, ect_k, spark, lam, cam):
    """The model TIT in K at one ECU operating point (engine_env.py:888-894): plant.run_cycle at
    exhaust_backpressure_kpa(map_kpa), egt_c + 273.15 as engine_env.py:1057 forms it."""
    eng = plant.engine
    op = P.Operating(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k, spark_btdc=spark, lam=lam,
                     p_exh_kpa=P.exhaust_backpressure_kpa(map_kpa, engine=eng))
    return P.run_cycle(op, engine=eng, cam_deg=cam).egt_c + 273.15


def least_tit(f, seen):
    """(lambda, f(lambda)) of least f over the points evaluated: `seen`, [(lambda, f)] from lambda_ECU down to
    lam_floor in the scan's order, and a golden-section search to LAMBDA_TOL between the least point's two
    neighbours in it (its one neighbour at an end). The least value of every point, the leanest on a tie, so
    never above any point of `seen`, lambda_ECU (seen[0]) included, and inside [seen[-1], seen[0]]."""
    i = min(range(len(seen)), key=lambda j: (seen[j][1], -seen[j][0]))
    a, b = seen[min(i + 1, len(seen) - 1)][0], seen[max(i - 1, 0)][0]        # the richer and the leaner neighbour
    pts = list(seen)
    if b - a > LAMBDA_TOL:
        c, d = b - GOLDEN * (b - a), a + GOLDEN * (b - a)
        fc, fd = f(c), f(d)
        pts += [(c, fc), (d, fd)]
        while b - a > LAMBDA_TOL:
            if fc < fd:
                b, d, fd = d, c, fc
                c = b - GOLDEN * (b - a)
                fc = f(c)
                pts.append((c, fc))
            else:
                a, c, fc = c, d, fd
                d = a + GOLDEN * (b - a)
                fd = f(d)
                pts.append((d, fd))
    return min(pts, key=lambda p: (p[1], -p[0]))


def least_enrichment(plant, *, cap_k, rpm, map_kpa, iat_k, ect_k, spark, lam, cam):
    """(lambda, TIT at it in K, outcome, TIT(lambda_ECU) in K): outcome "below" (lambda_ECU holds the cap and is
    returned as given), "held" (the leanest lambda in [lam_floor, lambda_ECU] that holds it, to LAMBDA_TOL) or
    "unheld" (none does: the lambda of least TIT in [lam_floor, lambda_ECU], least_tit). The scan, the bisection
    and the fallback of the module's docstring."""
    def tit(x):
        return model_tit_k(plant, rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k, spark=spark, lam=x, cam=cam)
    t_ecu = tit(lam)
    if t_ecu <= cap_k:
        return lam, t_ecu, "below", t_ecu
    floor = plant.engine.ecu.lam_floor
    seen = [(lam, t_ecu)]
    hi, k = lam, 1
    while True:
        x = max(float(lam - k * SCAN_STEP), floor)
        t = tit(x)
        seen.append((x, t))
        if t <= cap_k:
            lo, t_lo = x, t
            break
        if x <= floor:
            x, t = least_tit(tit, seen)
            return x, t, "unheld", t_ecu
        hi, k = x, k + 1
    while hi - lo > LAMBDA_TOL:
        mid = 0.5 * (lo + hi)
        t = tit(mid)
        if t <= cap_k:
            lo, t_lo = mid, t
        else:
            hi = mid
    return float(lo), t_lo, "held", t_ecu


@contextlib.contextmanager
def capped(plant, *, cap_k, keep_steps):
    """engine_env.BaselineECU.step patched to the TIT-cap ECU of `plant` at cap_k (K) while inside, in this process
    only (ONE PROCESS), and the original put back on exit, after an exception too (thresholds/ecu_shift.py:66-78
    and :114's pattern). Yields the context's CapStats. Refused when cap_k is not a finite positive number, and
    when step is already patched (another capped() or ecu_shift's patch active), so two patches never stack."""
    if isinstance(cap_k, bool) or not isinstance(cap_k, (int, float)) or not math.isfinite(cap_k) or cap_k <= 0:
        raise ValueError(f"capped: cap_k must be a finite temperature in K, not {cap_k!r}")
    cls = engine_env.BaselineECU
    orig = cls.__dict__["step"]
    if getattr(orig, "__qualname__", None) != ORIGINAL_QUALNAME or getattr(orig, "__module__", None) != "engine_env":
        raise RuntimeError(f"capped: BaselineECU.step is already patched ({getattr(orig, '__qualname__', orig)!r}); "
                           "two patches never stack")
    cal = plant.engine.ecu
    stats = CapStats(cap_k=float(cap_k), calls=0, acted=0, held=0, unheld=0, unheld_hotter=0, unheld_unchanged=0,
                     passed=0, tit_max_k=-math.inf, steps=[] if keep_steps else None)

    def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):
        out = orig(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt)
        if self.cal is not cal:
            if self.cal == cal:
                raise RuntimeError("capped: an ECU whose calibration equals the capped plant's but is another "
                                   "object; its engine cannot be told from its ECU (run the plant passed to capped)")
            stats.passed += 1
            return out
        stats.calls += 1
        sp, lam_ecu, fan = out
        cam = self.cam_deg(rpm, map_kpa)
        lam, t, outcome, t_ecu = least_enrichment(plant, cap_k=stats.cap_k, rpm=rpm, map_kpa=map_kpa, iat_k=iat_k,
                                                  ect_k=ect_k, spark=sp, lam=lam_ecu, cam=cam)
        stats.tit_max_k = max(stats.tit_max_k, t_ecu)
        if outcome == "below":
            return out
        stats.acted += 1
        if outcome == "held":
            stats.held += 1
        else:
            stats.unheld += 1
            stats.unheld_hotter += int(t > t_ecu)
            stats.unheld_unchanged += int(lam == lam_ecu)
        if keep_steps:
            stats.steps.append(dict(call=stats.calls - 1, rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                                    spark=sp, cam=cam, lam_ecu=lam_ecu, tit_ecu_k=t_ecu, lam=lam, tit_k=t,
                                    outcome=outcome))
        return sp, float(lam), fan

    cls.step = step
    try:
        yield stats
    finally:
        cls.step = orig


# ---------------------------------------------------------------------------- the record
def _git(root, *args):
    return subprocess.run(["git", *args], cwd=root, capture_output=True, text=True)


def record_problems(rec, *, plant, committed):
    """Why row 105's record `rec` (a dict) cannot give this plant a cap, or [] (THE CAP): its schema, plant and
    engine_sha; its audit; its two caps; its hashes against the files now; and, when committed, its git block and
    its prelude (before_the_audit watched)."""
    from thresholds import common
    out = []
    if rec.get("schema") != SCHEMA:
        return [f"the schema is {rec.get('schema')!r}, not {SCHEMA!r}"]
    name = engines.name_of(plant)
    if rec.get("plant") != name:
        out.append(f"it is the record of {rec.get('plant')!r}, not of {name!r}")
    want = engines.engine_sha(plant)
    prov = rec.get("provenance") or {}
    if prov.get("engine_sha") != want:
        out.append(f"it was computed beside engine_sha {prov.get('engine_sha')!r}; this plant is {want!r}")
    a = rec.get("audit") or {}
    for k in ("refused_by_audit", "outside_allowlist"):
        if a.get(k) != []:
            out.append(f"its audit's {k} is {a.get(k)!r}, not empty")
    b = a.get("before_the_audit") or {}
    if b.get("watched") is True:
        for k in ("forbidden", "outside_allowlist", "subprocesses"):
            if b.get(k) != []:
                out.append(f"before its audit, {k} is {b.get(k)!r}, not empty")
    elif b.get("watched") is not False:
        out.append("its audit says nothing of the opens before it")
    cap, eg = rec.get("cap") or {}, rec.get("sensitivity_egt_limit") or {}
    if not isinstance(cap.get("tit_c"), float) or cap.get("tit_k") != cap["tit_c"] + 273.15:
        out.append(f"its cap.tit_k {cap.get('tit_k')!r} is not its cap.tit_c {cap.get('tit_c')!r} + 273.15")
    if eg.get("tit_k") != plant.engine.damage.egt_limit_k:
        out.append(f"its second cap {eg.get('tit_k')!r} is not the plant's egt_limit_k "
                   f"{plant.engine.damage.egt_limit_k!r}")
    sha = rec.get("sha_text") or {}
    if tuple(sorted(sha)) != tuple(sorted(RECORD_HASHED)):
        out.append(f"its sha_text names {sorted(sha)}, not {sorted(RECORD_HASHED)}")
    code = prov.get("code_sha_text")
    if not isinstance(code, dict) or not code:
        out.append("its provenance holds no code_sha_text")
        code = {}
    for f, v in sorted({**code, **sha}.items()):
        p = os.path.join(HERE, *f.split("/"))
        if not os.path.isfile(p) or common.sha_text(p) != v:
            out.append(f"{f} is not the file it was computed with (the record is stale)")
    if committed and (rec.get("git") or {}).get("code_clean") is not True:
        out.append("its code was not committed and clean (git.code_clean)")
    if committed and b.get("watched") is not True:
        out.append("it was not written by the command line, whose prelude watches the imports")
    return out


def committed_problem(path, *, root, name):
    """Why `path` is not row 105's committed record of `name` in the work tree `root`, or None: it must be
    <root>/RECORD_DIR/<name>.json, tracked by git and unmodified (git ls-files, git status --porcelain)."""
    want = os.path.join(root, *RECORD_DIR.split("/"), f"{name}.json")
    if os.path.normcase(os.path.abspath(path)) != os.path.normcase(os.path.abspath(want)):
        return f"{path} is not {RECORD_DIR}/{name}.json of {root}"
    rel = f"{RECORD_DIR}/{name}.json"
    tracked = _git(root, "ls-files", "--error-unmatch", "--", rel)
    if tracked.returncode != 0:
        return f"{rel} is not tracked in {root}"
    status = _git(root, "status", "--porcelain=v1", "--untracked-files=all", "--", rel)
    if status.returncode != 0 or status.stdout.strip():
        return f"{rel} differs from its commit in {root}"
    return None


def cap_from_record(path, *, plant, which, committed):
    """(cap in K, the record's sha_text) from row 105's record (tit_cap.py's, schema SCHEMA): which "cap" (the
    highest TIT on the calibration Final rows) or "egt_limit" (the spec's egt_limit_k, the second sensitivity
    row). Refused (ValueError) on any record_problems, and, when committed, on committed_problem in this tree: a
    cap is read only beside the frozen plant and the code it was computed with. committed=False is for a
    measurement on a scratch record (climb --uncommitted), never for row 115's re-scoring."""
    from thresholds import common
    if which not in WHICH:
        raise ValueError(f"cap_from_record: which is one of {WHICH}, not {which!r}")
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    bad = record_problems(rec, plant=plant, committed=committed)
    if committed:
        why = committed_problem(path, root=HERE, name=engines.name_of(plant))
        if why is not None:
            bad.append(why)
    if bad:
        raise ValueError(f"cap_from_record: {path} refused: " + "; ".join(bad))
    cap = rec["cap"]["tit_k"] if which == "cap" else rec["sensitivity_egt_limit"]["tit_k"]
    return float(cap), common.sha_text(path)


# ---------------------------------------------------------------------------- the two measurements
PROBE_RPM = (1500.0, 2500.0, 3500.0, 4500.0, 5500.0)     # DESIGN: the probe's grid
PROBE_MAP = (100.0, 150.0, 200.0, 250.0)
PROBE_DLAM = 0.002


def probe(plant):
    """The model TIT against lambda at the probe's grid: each (rpm, MAP) at the ECU's base spark with its IAT
    compensation (engine_env.py:396) and its cam, the charge at the scenario's ambient with the warm block
    (plant.charge_temperature), lambda from lam_floor to 1 in PROBE_DLAM. Prints one line per point."""
    eng = plant.engine
    ecu = engine_env.BaselineECU(eng.ecu)
    t_block = eng.thermal.t_block_warm
    iat = P.charge_temperature(plant.scenario.t_amb, t_block, engine=eng)
    n = int(round((1.0 - eng.ecu.lam_floor) / PROBE_DLAM))
    lams = [eng.ecu.lam_floor + i * (1.0 - eng.ecu.lam_floor) / n for i in range(n + 1)]
    print(f"probe: {engines.name_of(plant)}, iat {iat:.2f} K, ect {t_block:.2f} K, lambda {lams[0]} to {lams[-1]} "
          f"in {len(lams)} points")
    rows = []
    for rpm in PROBE_RPM:
        for mp in PROBE_MAP:
            sp = min(max(ecu.base_spark(rpm, mp) + ecu.iat_compensation(iat), eng.ecu.spark_min), eng.ecu.spark_max)
            cam = ecu.cam_deg(rpm, mp)
            ts = [model_tit_k(plant, rpm=rpm, map_kpa=mp, iat_k=iat, ect_k=t_block, spark=sp, lam=x, cam=cam)
                  for x in lams]
            i_min = min(range(len(ts)), key=ts.__getitem__)
            # the largest reversal on each side of the minimum: a fall in TIT as lambda rises toward 1 on the
            # lean side, a rise as lambda rises toward the minimum on the rich side (0 when monotone)
            lean = max([0.0] + [a - b for a, b in zip(ts[i_min:], ts[i_min + 1:])])
            rich = max([0.0] + [b - a for a, b in zip(ts[:i_min], ts[1:i_min + 1])])
            i_max = max(range(len(ts)), key=ts.__getitem__)
            row = dict(rpm=rpm, map_kpa=mp, spark=sp, tit_floor_k=ts[0], lam_min=lams[i_min], tit_min_k=ts[i_min],
                       tit_1_k=ts[-1], lam_max=lams[i_max], reversal_lean_k=lean, reversal_rich_k=rich)
            rows.append(row)
            print(f"  rpm {rpm:6.0f} MAP {mp:5.0f} spark {sp:6.2f}: TIT {ts[-1]:7.2f} K at lambda 1 (the highest at "
                  f"{lams[i_max]:.3f}), minimum {ts[i_min]:7.2f} K at {lams[i_min]:.3f} ({ts[-1] - ts[i_min]:5.2f} K "
                  f"below), {ts[0]:7.2f} K at the floor ({ts[0] - ts[i_min]:5.2f} K above the minimum); largest "
                  f"reversal {lean:.4f} K lean of the minimum, {rich:.4f} K rich of it")
    print(f"  over the grid: below lambda 1 by {min(r['tit_1_k'] - r['tit_min_k'] for r in rows):.2f}-"
          f"{max(r['tit_1_k'] - r['tit_min_k'] for r in rows):.2f} K at the minimum, at lambda "
          f"{min(r['lam_min'] for r in rows):.3f}-{max(r['lam_min'] for r in rows):.3f}; the floor above the minimum "
          f"by {min(r['tit_floor_k'] - r['tit_min_k'] for r in rows):.2f}-"
          f"{max(r['tit_floor_k'] - r['tit_min_k'] for r in rows):.2f} K; the largest reversal "
          f"{max(max(r['reversal_lean_k'], r['reversal_rich_k']) for r in rows):.4f} K; the highest TIT at lambda "
          f"{sorted({r['lam_max'] for r in rows})}")
    return rows


def climb_run(plant, *, cap_k, duration, dt):
    """One locked climb (engine_env.locked_climb) at `duration` and `dt`, seed 0, the neutral action
    (engine_env.neutral_action), with whatever ECU is in place: the baseline network's TIT inputs (the egt_k its
    thermal step is given, engine_env.py:1303-1304), how many exceed cap_k and by how much, its t_turb after each
    step, the lambda the baseline's load loop ran (its _track_torque call on pi_base, engine_env.py:1291-1293),
    and the episode's damage_base and fuel_base (info["episode_summary"])."""
    import numpy as np
    env = engine_env.SupervisoryTunerEnv(engine_env.locked_climb(plant, duration=duration, dt=dt), plant=plant,
                                         dt=dt, seed=0)
    env.reset(seed=0)
    base_step, seen, tturb = env.thermal_base.step, [], []
    track, lam_b = env._track_torque, []

    def recording(dt_, mdot_fuel, mdot_exh, egt_k, *a, **kw):
        seen.append(float(egt_k))
        r = base_step(dt_, mdot_fuel, mdot_exh, egt_k, *a, **kw)
        tturb.append(float(env.thermal_base.t_turb))
        return r

    def tracking(torque_req, rpm, iat_k, ect_k, spark, lam, boost_trim, state, **kw):
        if state is env.pi_base:
            lam_b.append(float(lam))
        return track(torque_req, rpm, iat_k, ect_k, spark, lam, boost_trim, state, **kw)
    env.thermal_base.step = recording
    env._track_torque = tracking
    act = np.array(engine_env.neutral_action(), dtype=np.float32)
    while True:
        _, _, term, trunc, info = env.step(act)
        if term or trunc:
            break
    over = [x for x in seen if x > cap_k]
    e = info["episode_summary"]
    return dict(steps=len(seen), realised_max_k=max(seen), realised_over_cap=len(over),
                realised_over_max_k=max(over) - cap_k if over else 0.0, t_turb_max_k=max(tturb),
                lam_b_median=statistics.median(lam_b), lam_b_min=min(lam_b),
                lam_b_at_floor=sum(1 for x in lam_b if x == plant.engine.ecu.lam_floor),
                damage_base=float(e["damage_base"]), fuel_base=float(e["fuel_base"]))


def acted_summary(st):
    """The acted steps of a CapStats kept with keep_steps: lambda_ECU (how many at 1, below 1, the median), the
    excess TIT(lambda_ECU) - cap (min, median, 90th percentile by numpy.percentile's linear rule, max), the
    reduction TIT(lambda_ECU) - TIT returned (median, max), and the lambda returned (median, min)."""
    import numpy as np
    s = st.steps
    if not s:
        return {"acted": 0}
    lam_ecu = [x["lam_ecu"] for x in s]
    exc = [x["tit_ecu_k"] - st.cap_k for x in s]
    red = [x["tit_ecu_k"] - x["tit_k"] for x in s]
    return dict(acted=len(s), lam_ecu_at_1=sum(1 for v in lam_ecu if v == 1.0),
                lam_ecu_below_1=sum(1 for v in lam_ecu if v < 1.0), lam_ecu_median=statistics.median(lam_ecu),
                excess_k=dict(min=min(exc), median=statistics.median(exc), p90=float(np.percentile(exc, 90)),
                              max=max(exc)),
                reduction_k=dict(median=statistics.median(red), max=max(red)),
                lam_median=statistics.median(x["lam"] for x in s), lam_min=min(x["lam"] for x in s))


def climb(plant, *, cap_k, duration, dt):
    """The locked climb twice (climb_run): unpatched, the control (mistake 12: a perturbation's numbers need their
    reference), then under capped(plant, cap_k), refused unless the context capped every step it ran (ONE
    PROCESS). Returns (the CapStats, the capped run, the control, acted_summary)."""
    control = climb_run(plant, cap_k=cap_k, duration=duration, dt=dt)
    with capped(plant, cap_k=cap_k, keep_steps=True) as st:
        run = climb_run(plant, cap_k=cap_k, duration=duration, dt=dt)
    if st.calls != run["steps"] or st.calls == 0:
        raise RuntimeError(f"climb: the context capped {st.calls} ECU steps of the {run['steps']} run: the patch did "
                           "not reach this run's ECU")
    return st, run, control, acted_summary(st)


def main(argv):
    ap = argparse.ArgumentParser(prog="tit_cap_ecu.py", description="decision 62's TIT-cap ECU (see the docstring)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p1 = sub.add_parser("probe")
    p1.add_argument("--engine", required=True)
    p2 = sub.add_parser("climb")
    p2.add_argument("--engine", required=True)
    p2.add_argument("--record", required=True)
    p2.add_argument("--which", required=True, choices=WHICH)
    p2.add_argument("--duration", required=True, type=float)
    p2.add_argument("--dt", required=True, type=float)
    p2.add_argument("--uncommitted", action="store_true")
    args = ap.parse_args(argv)
    pl = engines.get(args.engine)
    t0 = time.time()
    if args.cmd == "probe":
        probe(pl)
    else:
        cap, sha = cap_from_record(args.record, plant=pl, which=args.which, committed=not args.uncommitted)
        st, run, control, acted = climb(pl, cap_k=cap, duration=args.duration, dt=args.dt)
        kind = "an uncommitted record (a measurement, not row 115's)" if args.uncommitted else "the committed record"
        print(f"climb: {args.engine}, cap {args.which} {cap!r} K from {kind} (sha_text {sha}), {args.duration} s at "
              f"dt {args.dt}")
        print(f"  capped ECU: {json.dumps(st.as_json())}")
        print(f"  acted steps: {json.dumps(acted)}")
        print(f"  the baseline, capped:    {json.dumps(run)}")
        print(f"  the baseline, unpatched: {json.dumps(control)}")
        print("  capped minus unpatched: " + json.dumps({k: run[k] - control[k] for k in run if k != "steps"}))
    print(f"{time.time() - t0:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
