"""test_calibrate_epa.py -- calibrate_epa.py's gate, runtime audit, order of work, proofs and records, on
synthetic repositories.

    python -B test_calibrate_epa.py     a few minutes; exit code 0 when all pass

Build step 2 of decision 24, WP3 (23 October 2026; docs/build_step_2/WP3_INTERFACES.md section 9.11:
amendments C3, C6, C8, C10, C13). Nothing here runs on EPA data and nothing fits a model to anything: every
subcommand runs in a temporary git repository with synthetic tables and a synthetic contract
(test_epa_fixtures.make_repo), with the expensive stages replaced by stand-ins whose output is fixed by
this file (the ladder, T0, the refit variants, the poison's stages, the completion's climbs), so that what
is tested is calibrate_epa.py's own work -- the gate, the audit, the order, the proofs each step requires,
the records, the defect route -- and the stand-ins are named as such. The cheap stages S1 and S3a-S3d run
for real on the synthetic rows, since the poison's reference is tied to them. The stages, statistics and
measurements the stand-ins replace are tested by test_epa_fit.py, test_epa_stats.py, test_k3_knee.py and
test_epa_coefficients.py. The command line itself runs in subprocesses on synthetic repositories whose
copy of epa_rows pins their own contract (test_epa_fixtures.pin_contract_commit); on this tree only a
one-line probe of the gate and dry-load run, and only once the probe shows the rule stands
(Gate.test_this_trees_contract_holds_the_first_evaluation). The switch EPA_RUN1_GO is set only where a test
names it, in a subprocess's own environment.

Each check is shown able to fail (mistake 12): a forbidden open and argv beside an allowed one, an import
-time open, an extra open and one refused while the poisoned stages run, a crash beside a run, a refused
order beside the order, a missing or false proof, a moved table, floor, identity, knee, hash or contract, a
check whose record was edited, a refit after the held-out run started.
"""
import ast
import contextlib
import copy
import dataclasses
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import calibrate_epa as C  # noqa: E402
import engines  # noqa: E402
import epa_fit  # noqa: E402
import epa_freeze  # noqa: E402
import epa_rows  # noqa: E402
import epa_stats  # noqa: E402
import k3_knee  # noqa: E402
import test_epa_fixtures as F  # noqa: E402

MAZDA, HONDA, FORD = "mazda_25t", "honda_l15b7", "ford_27tt"
ENV = {k: v for k, v in os.environ.items() if k != C.RUN1_GO}
ENV.update(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1")

# Synthetic band texts in the contract's format (its perturbations_E6), so that the completion's and the
# refit variants' parse (epa_stats.e6_band_values, epa_stats.row10_etas) finds its numbers. Not the
# contract's text.
BANDS = {4: "x0.75 and x1.333 each (synthetic)",
         5: "+- its fit's sigma (synthetic); the probe by consequence, else +-10 %; every d row's probe is +-10 % "
            "(synthetic)",
         7: "KI 0.90 and 1.10 (synthetic)",
         9: "the bracket, else the probe, else +-10 % (+-10 crank degrees for IVC and EVO) (synthetic)",
         10: "0.86-0.98 (synthetic)",
         11: "+-6.3 K (synthetic)",
         13: "the ECU's dwell gate at 0 s and at 30 s (synthetic)"}
RULE = ("synthetic: The first fit (Run 1) waits for both: Jad's column, and Ghassan's own answer to those rows "
        "and readings")
SUBS = ("t0", "fit", "poison", "e6", "complete", "check")


def setUpModule():
    if C.RUN1_GO in os.environ:
        raise RuntimeError(f"{C.RUN1_GO} is set in this environment; the tests never set it, and a gate test "
                           "would not test the gate")


def tearDownModule():
    epa_fit.close_pools()


def read(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)


def write_json(path, obj):
    write(path, json.dumps(obj, indent=1) + "\n")


def cal(src, eng, rel):
    return os.path.join(epa_freeze.calibration_dir(eng, root=src.root), *rel.split("/"))


def runs(src, eng):
    return read(cal(src, eng, C.RUN))["invocations"]


def invoke(sub, eng, src, body, *, scratch=None):
    return C.invoke(sub, eng, source=src, argv=[sub, "--engine", eng], body=body, scratch=scratch, audit=None)


def with_bands(repo, *, rule=None):
    def edit(c):
        for p in c["perturbations_E6"]:
            if p["n"] in BANDS:
                p["band"] = BANDS[p["n"]]
        if rule is not None:
            c["open_for_the_team"] = [rule]
    return F.rewrite_contract(repo, edit)


def spec_floor(c):
    """The synthetic contract's lambda clip floor set to each spec's typed one (the fit refuses two values
    for one number, epa_fit._fit and s3b_lambda)."""
    for e in c["engines"]:
        c["engines"][e]["lambda_clip_floor"]["floor"] = float(engines.read_spec(e)["ecu"]["lam_floor"])


def run_repo(case, *, rule=None):
    """A fresh repository a whole Run 1 runs on: the bands, the specs' floors, optionally the Run 1 rule."""
    return F.rewrite_contract(with_bands(case.fresh(), rule=rule), spec_floor)


def frozen_values(form="A"):
    """A frozen-sections dict that builds for any EPA engine: the B58's values (test_epa_fixtures.
    b58_values), its cycle form `form`. A stand-in for a fit's output; nothing is fitted."""
    v = F.b58_values()
    out = json.loads(json.dumps({s: v[s] for s in engines.FROZEN_SECTIONS}))
    out["cycle"]["form"] = form
    if "D" in form.split("+"):
        # form D runs the intake cam (decision 41): a flat schedule, synthetic, over a wide domain
        out["ecu"].update(cam_on=1, cam_rpm_lo=1000.0, cam_rpm_hi=6000.0, cam_map_lo=20.0, cam_map_hi=300.0,
                          cam_lo=-1.0, cam_hi=1.0)
    return out


def form_fit(name, form, *, stages=None):
    v = frozen_values(form)
    return epa_fit.FormFit(engine=name, form=form, stages=stages or {}, values=v,
                           frozen_sections_sha256=engines.frozen_sections_sha256(v), flags=())


def toy_evals(yield_, *, view, dtheta):
    """Every calibration row through epa_stats.kernel_point with test_epa_fixtures.ToyModel (closed-form
    laws, no cycle), its censoring marked: the same rows and the same function every time."""
    rows = epa_fit.cal_rows(yield_)
    model = F.ToyModel()
    evals = [epa_stats.kernel_point(model, epa_stats.make_task(r, view=view, conventions=epa_stats.NOMINAL,
                                                               dtheta=dtheta, needs=epa_stats.default_needs(r),
                                                               shift=None)) for r in rows]
    return epa_stats.mark_censored(evals, censoring=epa_stats.censoring(
        [r for r in rows if type(r) is epa_rows.FinalRow]))


class Judge:
    """A stand-in for epa_fit.in_sample_for: epa_stats.in_sample on the toy evaluations, every form passing
    but those in `failing` (which fail E1a), so a ladder stops where the test says; each call's form
    recorded. The same verdict every time, so check can give it back."""

    def __init__(self, failing=()):
        self.failing, self.calls = set(failing), []

    def __call__(self, name, fit, yield_, *, view, jobs, dtheta):
        self.calls.append(fit.form)
        ins = epa_stats.in_sample(toy_evals(yield_, view=view, dtheta=dtheta), view=view)
        if fit.form in self.failing:
            return dataclasses.replace(ins, passes=False, failing=("E1a",))
        return dataclasses.replace(ins, passes=True, failing=())


def cheap_stages(name, yield_, *, view, form):
    """The fit's stages that read no cycle (S1, S3a, S3b, S3c), for real on the synthetic rows: what the
    poison's reference is tied to (calibrate_epa.POISON_TIED_STAGES)."""
    rows = epa_fit.cal_rows(yield_)
    base = epa_fit._base_plant(name, form)
    cens = epa_stats.censoring([r for r in rows if epa_fit._final(r)])
    conv = epa_stats.NOMINAL
    out = {"S1": epa_fit.s1_backpressure(rows, view=view), "S3a": epa_fit.s3a_spark(rows, plant=base, view=view),
           "S3b": epa_fit.s3b_lambda(rows, plant=base, view=view, censoring=cens, lam_floor=float(view.lam_floor),
                                     conventions=conv),
           "S3c": epa_fit.s3c_envelope(rows, plant=base, view=view, conventions=conv)}
    if "D" in form.split("+"):
        out["S3d"] = epa_fit.s3d_cam(rows, view=view)       # form D's cam schedule, as the fit runs it
    return out


def fixed_stage(stage):
    return epa_fit.StageResult(stage=stage, values={"stand_in": 1.0}, rows_used=0, rows_excluded={}, flags=(),
                               bounds_active=(), convergence=None, report={"stand_in": True})


def stand_in_poison_stages(name, yield_, *, view, values, jobs, dtheta):
    """A stand-in for epa_fit.poison_stages: the cheap stages for real (and S3d), S2 and S6 fixed. A function
    of the yield and the view alone, so the poison's comparisons hold unless something else reaches it."""
    out = cheap_stages(name, yield_, view=view, form=values["cycle"]["form"])
    try:
        out["S3d"] = epa_fit.s3d_cam(epa_fit.cal_rows(yield_), view=view)
    except epa_fit.FitDefect:
        out["S3d"] = None
    out["S2"], out["S6"] = fixed_stage("S2"), fixed_stage("S6")
    return {k: out[k] for k in epa_fit.POISON_STAGES}


class StandIns:
    """The ladder, T0, the refit variants, the in-sample judge, the poison's stages and the full form-A poison
    fit replaced, each call recorded; the pins pinned (test_epa_fixtures.pinned_terms). `forms` are the forms
    the stand-in ladder fits (every one but the last fails its judge); `crash` makes the ladder raise;
    `stray` a path the ladder opens (an open outside the allowlist); `t0_pass` T0's verdict."""

    def __init__(self, test, *, crash=False, forms=("A",), t0_pass=True, stray=None):
        self.test, self.crash, self.forms, self.t0_pass, self.stray = test, crash, forms, t0_pass, stray
        self.judge = Judge(failing=forms[:-1])
        self.calls = []

    def ladder(self, name, yield_, *, view, jobs, dtheta):
        self.calls.append(("ladder", os.path.exists(cal(self.test.src, name, C.STARTED))))
        if self.stray:
            with open(self.stray, encoding="utf-8") as fh:
                fh.read()
        if self.crash:
            raise RuntimeError("a stand-in ladder that crashes")
        fits, ins = [], {}
        for f in self.forms:
            ff = form_fit(name, f, stages=cheap_stages(name, yield_, view=view, form=f))
            fits.append(ff)
            ins[f] = self.judge(name, ff, yield_, view=view, jobs=jobs, dtheta=dtheta)
            if ins[f].passes:                          # the ladder stops at the first form that passes
                break
        chosen, reason = epa_fit.ladder_choice(ins)
        return epa_fit.Ladder(engine=name, fits=tuple(fits), in_sample=ins, chosen=chosen, reason=reason)

    def refit_variant(self, name, yield_, *, view, form, conventions, ladder_fits, jobs, dtheta):
        self.calls.append(("refit", dataclasses.asdict(conventions), sorted(ladder_fits)))
        s = ladder_fits[form]
        return epa_fit.FormFit(engine=name, form=form, stages={}, values=s.values,
                               frozen_sections_sha256=s.frozen_sections_sha256, flags=())

    def run_t0(self, name, yield_, *, view, jobs, dtheta):
        self.calls.append(("t0", os.path.exists(cal(self.test.src, name, C.STARTED))))
        return {"schema": "epa-t0/1", "pass": self.t0_pass, "stand_in": True}

    def fit_form(self, name, yield_, *, view, form, start, jobs, dtheta):
        self.calls.append(("fit_form", form))
        return form_fit(name, form)

    def patches(self):
        return [mock.patch.object(epa_fit, "ladder", self.ladder),
                mock.patch.object(epa_fit, "refit_variant", self.refit_variant),
                mock.patch.object(epa_fit, "in_sample_for", self.judge),
                mock.patch.object(epa_fit, "run_t0", self.run_t0),
                mock.patch.object(epa_fit, "poison_stages", stand_in_poison_stages),
                mock.patch.object(epa_fit, "fit_form", self.fit_form),
                F.pinned_terms()]


def _cell(plant):
    """The stand-in climb cell of a plant: its gas a linear function of UA_PORT and the back-pressure
    ratio, its flow of the floor, everything else fixed, so a probe's size has a hand answer."""
    c = plant.engine.cycle
    return {"rpm": 2700.0, "map": 175.0, "iat": 330.0, "ect": 365.0, "spark": 2.0, "lam": 1.0,
            "egt": 900.0 + 0.5 * c.ua_port + 20.0 * c.exh_bp_ratio,
            "mdot": 120.0 * (1.0 + 0.001 * (c.exh_bp_min_kpa - 100.0)), "torque": 300.0, "treq": 300.0,
            "t_turb": 800.0}


HS = {"f": 0.8, "tau_s": 100.0, "dTh_per_unit_ln_mdot": 150.0, "ua_gas_turb": 1.0, "ua_turb_amb": 1.0,
      "c_turb": 1.0}
# The stand-in climb cell's median resolution (decision 85), K and g/s: synthetic, far below every response the
# stand-in cell gives a constant it sees (0.5 K per W/K of UA_PORT, 20 K per unit of the back-pressure ratio)
STAND_IN_RESOLUTION = {"egt": 1e-4, "mdot": 1e-4}


def stand_in_task(item):
    """A stand-in for calibrate_epa._completion_task, each kind's output a fixed function of the plant:
    the table and the floor independent of the knee (the F7 control's premise), the identity holding."""
    kind, plant, kw = item
    car = plant.car
    if kind == "table":
        raw = tuple((int(r), 100.0 + 0.0625 * float(r)) for r in car.table_rpms)
        return k3_knee.DeliverableTable(settle=kw["settle"], table=tuple((r, round(t, 1)) for r, t in raw), raw=raw,
                                        knock_flag_duty=0.0, calls=len(raw) * kw["settle"])
    if kind == "floor":
        return k3_knee.TorqueFloor(nm=12.5, closed_nm=10.0, rpm=float(max(1200.0, car.rpm_min)),
                                   t_amb_k=float(car.table_t_amb), settle=kw["settle"], rule="stand-in",
                                   extrapolation=True)
    if kind == "delivery":
        spread = {"min": 1.0, "median": 1.0, "max": 1.0}
        return {"delivery": {"t_from_s": 188.0, "steps": 531, "share_over_track_tol": 0.0, "largest_shortfall_nm": 0.0,
                             "held": {"box": "stepped", "counts": {"4": 531}}, "rpm": spread, "demand_nm": spread,
                             "margin_to_threshold": {"held": spread}, "bar_rpm_margin": None,
                             "map_vs_ceiling_kpa": spread},
                "identity": {"max_abs_dlam": 0.0, "max_abs_dspark": 0.0, "contacts_lam": 0, "contacts_spark": 0,
                             "bounds_are_python_floats": True, "steps": 719}}
    if kind == "k3":
        return k3_knee.K3(seconds=kw["seconds"], knee_k=1100.0 + 10.0 * (car.driveline_eff - 0.9),
                          time_above_knee_s=kw["seconds"], trace_sha256="0" * 64, second_knee_identical=True)
    if kind == "coefficients":
        return {"climb": {"point": _cell(plant), "housing": HS}, "stand_in": True}
    if kind == "climb_cell":
        return _cell(plant)
    if kind == "cell_resolution":                  # decision 85's noise floor: the base cell's medians, a resolution
        c = _cell(plant)
        return {"egt": c["egt"], "mdot": c["mdot"], "egt_resolution_k": STAND_IN_RESOLUTION["egt"],
                "mdot_resolution_gps": STAND_IN_RESOLUTION["mdot"], "samples": 319}
    if kind == "peak":
        return 850.0 + 0.001 * plant.engine.thermal.c_turb
    if kind == "damage":
        ka = plant.engine.cycle.knock_a
        return {"total": 1.0 + ka, "thermal": 1.0, "knock_share": ka / (1.0 + ka)}
    raise ValueError(kind)


def _swallowed_open_task(path):
    """A pool task that opens a file and catches the refusal, as linecache does: the audit must still report it."""
    try:
        return _open_task(path)
    except PermissionError:
        return -1


def _open_task(path):
    """A pool task that opens a file (the worker's audit must report it to the parent)."""
    with open(path, "rb") as fh:
        return len(fh.read())


class contextlib_all:
    """Enter several context managers (mock patches) as one."""

    def __init__(self, cms):
        self.cms = list(cms)

    def __enter__(self):
        for cm in self.cms:
            cm.__enter__()
        return self

    def __exit__(self, *exc):
        for cm in reversed(self.cms):
            cm.__exit__(*exc)
        return False


# ======================================================================================================
class RunCase(F.SyntheticRepoCase):
    """A fresh repository a Run 1 runs on, for each test, and the subcommands under invoke with stand-ins."""
    rule = None

    def setUp(self):
        super().setUp()
        self.repo = run_repo(self, rule=self.rule)
        self.src = F.synthetic_source(self.repo)
        self._n = 0

    def scratch(self):
        self._n += 1
        return os.path.join(os.path.dirname(self.repo.root), f"scratch_{self._n}")

    def sub(self, name, stand, *, defect=None, full=True, task=None, extra=(), jobs=1):
        """One subcommand under invoke with `stand`'s patches (and stand_in_task for the completion's climbs,
        or `task`), every other patch in `extra`. Returns the exit code."""
        scr = self.scratch() if name == "poison" else None
        bodies = {"t0": lambda: C.t0(MAZDA, source=self.src, jobs=jobs, defect=defect),
                  "fit": lambda: C.fit(MAZDA, source=self.src, jobs=jobs, defect=defect),
                  "poison": lambda: C.poison(MAZDA, source=self.src, jobs=jobs, scratch=scr, full=full),
                  "e6": lambda: C.e6(MAZDA, source=self.src, jobs=jobs),
                  "complete": lambda: C.complete(MAZDA, source=self.src, jobs=jobs),
                  "check": lambda: C.check(MAZDA, source=self.src, jobs=jobs, defect=defect)}
        env = {"DERIVING_PARAMS": "1"} if name == "complete" else {}
        cms = stand.patches() + [mock.patch.object(C, "_completion_task", task or stand_in_task),
                                 mock.patch.dict(os.environ, env)] + list(extra)
        with contextlib_all(cms):
            return invoke(name, MAZDA, self.src, bodies[name], scratch=scr)

    def through(self, last, stand, **kw):
        """Every subcommand of Run 1 in its order, up to and including `last`, each required to exit 0."""
        for s in SUBS:
            code = self.sub(s, stand, **kw)
            self.assertEqual(code, C.EXIT_OK, (s, runs(self.src, MAZDA)[-1]["outcome"]))
            if s == last:
                return

    def last(self):
        return runs(self.src, MAZDA)[-1]


# ======================================================================================================
class Gate(F.SyntheticRepoCase):
    """The contract's Run 1 rule holds the first evaluation at an EPA row's inputs: dry-load, and t0 or
    fit while STARTED is absent, refuse having read no EPA table and written nothing, unless EPA_RUN1_GO
    names the engine (which no test sets in its own process)."""

    def test_this_trees_contract_holds_the_first_evaluation(self):
        """On this tree: a one-line probe (a subprocess that prints run1_waits' boolean, nothing else) first;
        only if it shows the rule standing does the command line run here, and only the subcommands the gate
        holds -- dry-load, t0 and fit, STARTED absent -- each exiting EXIT_WAIT with results/EPA_CALIBRATION/
        and its scratch folder as they were. A contract that no longer holds the rule skips the test, by
        name, before anything runs (the review's finding: a later version would otherwise start Run 1 here)."""
        # the probe shows the gate's wiring as well as the rule (WP3's second fix of 23 October 2026, on the test
        # review's finding that a regressed gated() would have started Run 1 here): gated() holds each of the
        # three subcommands, and the rule stands
        # The probe prints two booleans: whether gated() holds the three subcommands, and whether the rule stands.
        # A gated() that regressed FAILS here; only a contract without the rule skips (WP3's fourth fix of 24 October
        # 2026, on the fourth tests review's finding that both read as one boolean and a regression skipped).
        probe = ("import sys, os; sys.path.insert(0, os.getcwd()); import epa_rows, calibrate_epa as C; "
                 "src = epa_rows.Source.repository(); "
                 "print(all(C.gated(s, 'mazda_25t', source=src) for s in ('dry-load', 't0', 'fit')), "
                 "C.run1_waits(source=src, environ={}, engine='mazda_25t')[0])")
        folder = os.path.join(HERE, *epa_freeze.CALIBRATION_DIR.split("/"))
        mazda_dir = os.path.join(folder, MAZDA)
        if os.path.isdir(mazda_dir) and os.path.exists(os.path.join(mazda_dir, C.STARTED)):
            self.skipTest("a run has started on this tree: t0 and fit are no longer gated here")
        p = subprocess.run([sys.executable, "-B", "-c", probe], cwd=HERE, env=ENV, capture_output=True, text=True,
                           timeout=600)
        self.assertEqual(p.returncode, 0, p.stderr[-800:])
        gated, waits = p.stdout.strip().splitlines()[-1].split()
        self.assertEqual(gated, "True", "gated() no longer holds dry-load, t0 and fit with STARTED absent")
        if waits != "True":
            self.skipTest("this tree's contract no longer holds the Run 1 rule: the command line is not run here")
        # a folder holding only a run.json of refused invocations (a refused t0 or fit with EPA_RUN1_GO set writes
        # one, STARTED absent; the fourth Run 1 review's finding) is the team's record: skipped by name, never
        # touched; anything else there fails below
        if os.path.isdir(mazda_dir) and sorted(os.listdir(mazda_dir)) == [C.RUN]:
            inv = read(os.path.join(mazda_dir, C.RUN)).get("invocations") or []
            if inv and all(str(i.get("outcome", "")).startswith("refused:") for i in inv):
                self.skipTest(f"{epa_freeze.CALIBRATION_DIR}/{MAZDA}/ holds only a run.json of refused invocations: "
                              "the command line is not run beside it")
        before = sorted(os.listdir(folder)) if os.path.isdir(folder) else None
        # nothing of this engine's calibration on this tree before the command line runs, so that a regressed gate
        # leaves nothing behind but what this test removes (WP3's third fix of 24 October 2026, on the test
        # review's finding that a regression would leave a run.json here, which the audit guard then reads)
        self.assertFalse(os.path.exists(mazda_dir), f"{epa_freeze.CALIBRATION_DIR}/{MAZDA}/ exists on this tree "
                         "without STARTED: the on-tree gate test runs the command line only where it writes nothing")
        try:
            with tempfile.TemporaryDirectory() as tmp:
                for sub in C.GATED_ALWAYS + C.GATED_UNTIL_STARTED:
                    # the command line itself, its audit refusing the engine's own tables from the start
                    # (_SEALED_CLI): a gate that let the subcommand through would crash at its first table open
                    argv = [sys.executable, "-B", "-c", _SEALED_CLI, sub, "--engine", MAZDA]
                    argv += ["--out", tmp] if sub == "dry-load" else ["--jobs", "1"]
                    r = subprocess.run(argv, cwd=HERE, env=ENV, capture_output=True, text=True, timeout=600)
                    self.assertEqual(r.returncode, C.EXIT_WAIT, (sub, r.stdout[-400:], r.stderr[-800:]))
                    self.assertIn("Run 1 waits", r.stdout)
                    self.assertIn("nothing was written", r.stdout)
                self.assertEqual(os.listdir(tmp), [], "a waiting subcommand wrote into its scratch folder")
        finally:
            after = sorted(os.listdir(folder)) if os.path.isdir(folder) else None
            if after != before:
                # a regression wrote here: what this run created is removed (it did not exist before), and the
                # assertion below names the regression
                if os.path.isdir(mazda_dir):
                    shutil.rmtree(mazda_dir)
                if before is None and os.path.isdir(folder) and not os.listdir(folder):
                    os.rmdir(folder)
        self.assertEqual(before, after, "a waiting subcommand wrote under results/EPA_CALIBRATION/")

    def test_the_command_line_on_a_synthetic_contract_that_holds_the_rule(self):
        """The command line itself, in subprocesses, in a synthetic repository whose epa_rows pins its own
        contract and whose contract holds the rule: the gated subcommands wait (EXIT_WAIT, nothing written);
        the others refuse for want of a freeze (EXIT_REFUSED); EPA_RUN1_GO naming another engine does not
        lift the gate, naming this one does (dry-load then runs and writes its scratch run.json)."""
        repo = F.pin_contract_commit(run_repo(self, rule=RULE))
        with tempfile.TemporaryDirectory() as tmp:
            for sub in ("dry-load",) + SUBS:
                argv = [sys.executable, "-B", "calibrate_epa.py", sub, "--engine", MAZDA]
                argv += ["--out", tmp] if sub == "dry-load" else ["--jobs", "1"]
                if sub == "poison":
                    argv += ["--scratch", tmp, "--full"]
                r = subprocess.run(argv, cwd=repo.root, env=ENV, capture_output=True, text=True, timeout=600)
                want = C.EXIT_WAIT if sub in C.GATED_ALWAYS + C.GATED_UNTIL_STARTED else C.EXIT_REFUSED
                self.assertEqual(r.returncode, want, (sub, r.stdout[-600:], r.stderr[-1200:]))
            self.assertEqual(os.listdir(tmp), [])
            folder = epa_freeze.calibration_dir(MAZDA, root=repo.root)
            self.assertEqual(set(os.listdir(folder)), {C.RUN}, "only the refused invocations' run.json")
            self.assertEqual({i["subcommand"] for i in read(os.path.join(folder, C.RUN))["invocations"]},
                             {"poison", "e6", "complete", "check"})
            argv = [sys.executable, "-B", "calibrate_epa.py", "dry-load", "--engine", MAZDA, "--out", tmp]
            other = subprocess.run(argv, cwd=repo.root, env=dict(ENV, **{C.RUN1_GO: FORD}), capture_output=True,
                                   text=True, timeout=600)
            self.assertEqual(other.returncode, C.EXIT_WAIT)
            go = subprocess.run(argv, cwd=repo.root, env=dict(ENV, **{C.RUN1_GO: f"{FORD},{MAZDA}"}),
                                capture_output=True, text=True, timeout=600)
            self.assertEqual(go.returncode, C.EXIT_OK, go.stdout[-600:] + go.stderr[-1200:])
            inv = read(os.path.join(tmp, C.RUN))["invocations"][-1]
            self.assertEqual((inv["outside_allowlist"], inv["refused_by_audit"]), ([], []))
            self.assertEqual(inv["run1_gate"]["switch"], f"{FORD},{MAZDA}")
            self.assertEqual(inv["run1_gate"]["rule"], RULE)

    def test_the_rule_and_the_switch(self):
        """run1_waits fails closed: any open_for_the_team entry naming Run 1 holds it (a reworded rule too),
        the commit epa_rows pins (version 5's, CONTRACT_COMMIT) holds it whatever the text, and only EPA_RUN1_GO
        naming the engine lifts it."""
        r = self.fresh()
        src = F.synthetic_source(r)
        self.assertEqual(C.run1_waits(source=src, environ={}, engine=MAZDA), (False, None),
                         "a synthetic contract with no rule holds nothing")
        src2 = F.synthetic_source(with_bands(r, rule=RULE))
        self.assertEqual(C.run1_waits(source=src2, environ={}, engine=MAZDA), (True, RULE))
        self.assertEqual(C.run1_waits(source=src2, environ={C.RUN1_GO: "1"}, engine=MAZDA), (True, RULE))
        self.assertEqual(C.run1_waits(source=src2, environ={C.RUN1_GO: FORD}, engine=MAZDA), (True, RULE))
        self.assertEqual(C.run1_waits(source=src2, environ={C.RUN1_GO: f"{FORD}, {MAZDA}"}, engine=MAZDA),
                         (False, RULE))
        reworded = "synthetic: Run 1 is held until the team has answered"
        src3 = F.synthetic_source(with_bands(r, rule=reworded))
        self.assertEqual(C.run1_waits(source=src3, environ={}, engine=MAZDA), (True, reworded))
        # the control: a sentence that names no Run 1 holds nothing, at a commit that is not the pinned one
        src4 = F.synthetic_source(with_bands(r, rule="synthetic: the roads' own seed is left to a later step"))
        self.assertEqual(C.run1_waits(source=src4, environ={}, engine=MAZDA), (False, None))
        # ... and at the commit epa_rows pins the same sentence still holds it
        with mock.patch.object(epa_rows, "CONTRACT_COMMIT", src4.contract_commit):
            self.assertEqual(C.run1_waits(source=src4, environ={}, engine=MAZDA),
                             (True, epa_rows.RUN1_PINNED_COMMIT))

    def test_the_gated_subcommands_refuse_before_reading_a_table(self):
        """dry-load, t0 and fit under an audit (the open recorder): each raises Run1Waits and opened no table
        and no epa_engine.json; the others, which the gate does not hold, refuse for want of a freeze (the
        control: a gate moved after the loader would show its tables here)."""
        r = run_repo(self, rule=RULE)
        src = F.synthetic_source(r)
        out = os.path.join(os.path.dirname(r.root), "scratch")
        paths = epa_rows.audit_paths(MAZDA, source=src)
        epa_files = set(paths["table_files"]) | {paths["engine_json"]}
        for call in (lambda: C.dry_load(MAZDA, source=src, out=out), lambda: C.t0(MAZDA, source=src, jobs=1, defect=None),
                     lambda: C.fit(MAZDA, source=src, jobs=1, defect=None)):
            a = C.install_audit(subcommand="fit", engine=MAZDA, root=r.root, scratch=None)
            a.bind(C._paths_for(MAZDA, source=src))
            try:
                with self.assertRaises(C.Run1Waits):
                    call()
            finally:
                C.deactivate()
            self.assertEqual(set(a.opened) & epa_files, set())
        for call in (lambda: C.poison(MAZDA, source=src, jobs=1, scratch=out, full=True),
                     lambda: C.e6(MAZDA, source=src, jobs=1), lambda: C.check(MAZDA, source=src, jobs=1, defect=None)):
            with self.assertRaises(C.Refusal) as cm:
                call()
            self.assertNotIsInstance(cm.exception, C.Run1Waits)
        self.assertFalse(os.path.exists(epa_freeze.calibration_dir(MAZDA, root=r.root)))
        self.assertFalse(os.path.exists(out))
        # the control of the recorder: the loader reading the tables shows them
        a = C.install_audit(subcommand="dry-load", engine=MAZDA, root=r.root, scratch=None)
        a.bind(C._paths_for(MAZDA, source=src))
        try:
            epa_rows.calibration_rows(MAZDA, source=src)
        finally:
            C.deactivate()
        self.assertTrue(set(paths["table_files"]) <= set(a.opened))

    def test_the_waiting_exit_checks_what_was_opened(self):
        """main's waiting path (wait_exit): EXIT_WAIT with no table opened; EXIT_DEFECT when the audit's record
        holds one of the engine's tables (a gate placed after a read)."""
        r = run_repo(self, rule=RULE)
        src = F.synthetic_source(r)
        C.install_audit(subcommand="fit", engine=MAZDA, root=r.root, scratch=None)
        self.assertEqual(C.wait_exit("fit", MAZDA, source=src), C.EXIT_WAIT)
        a = C.install_audit(subcommand="fit", engine=MAZDA, root=r.root, scratch=None)
        a.opened.add(epa_rows.audit_paths(MAZDA, source=src)["table_files"][0])
        self.assertEqual(C.wait_exit("fit", MAZDA, source=src), C.EXIT_DEFECT)


# The command line with its audit refusing the engine's own tables and epa_engine.json from the prelude on
# (Audit.refuse_tables; the contract stays readable, which the gate reads): calibrate_epa.py's own source run
# as __main__, the one line after its prelude added (WP3's second fix of 23 October 2026).
_SEALED_CLI = r'''
import os, sys
here = os.getcwd()
path = os.path.join(here, "calibrate_epa.py")
src = open(path, encoding="utf-8").read()
site = 'if __name__ == "__main__":\n    _ARGS = _prelude(sys.argv[1:])'
assert src.count(site) == 1
src = src.replace(site, site + "\n    _CURRENT[0].refuse_tables = True")
sys.argv = [path] + sys.argv[1:]
sys.path.insert(0, here)
exec(compile(src, path, "exec"), {"__name__": "__main__", "__file__": path})
'''


# ======================================================================================================
_PRE_IMPORT = r'''
import json, os, sys, types
code, root, info, sub, out = sys.argv[1:6]
sys.path.insert(0, code)
src_text = open(os.path.join(code, "calibrate_epa.py"), encoding="utf-8").read()
site = 'if __name__ == "__main__":\n    _ARGS = _prelude(sys.argv[1:])'
assert src_text.count(site) == 1
# the audit installed at the prelude's place, BEFORE the project imports, as the command line installs it
src_text = src_text.replace(site, f"install_audit(subcommand={sub!r}, engine='mazda_25t', root={root!r}, "
                                  f"scratch={(out or None)!r})")
mod = types.ModuleType("calibrate_epa")
mod.__file__ = os.path.join(code, "calibrate_epa.py")
sys.modules["calibrate_epa"] = mod
exec(compile(src_text, mod.__file__, "exec"), mod.__dict__)
C = mod
import epa_rows
s = epa_rows.Source(**json.loads(info))
if sub == "dry-load":
    code_ = C.invoke("dry-load", "mazda_25t", source=s, argv=["dry-load"], body=lambda: C.dry_load(
        "mazda_25t", source=s, out=out), scratch=out, audit=C._CURRENT[0])
else:
    import test_calibrate_epa as T
    stand = T.StandIns(types.SimpleNamespace(src=s))
    with T.contextlib_all(stand.patches()):
        code_ = C.invoke("fit", "mazda_25t", source=s, argv=["fit"], body=lambda: C.fit(
            "mazda_25t", source=s, jobs=1, defect=None), scratch=None, audit=C._CURRENT[0])
sys.exit(code_)
'''


class Audit(F.SyntheticRepoCase):
    """C3: what a subcommand opens is recorded and checked against its allowlist; a forbidden open or argv
    is refused at once; a pool worker's opens reach the parent's run.json, and a worker refuses the tables."""

    def test_the_audit_installed_before_the_imports_finds_nothing_outside(self):
        """The command line's order (WP3_INTERFACES.md 3.3): the audit installed before the first project
        import, then dry-load, and a stand-in fit, through invoke with that audit -- outside_allowlist empty
        although the import chain opens the B58's derived file (derived.py, through engines; the review's
        finding: every command line was a defect). The control: that file left off the allowlist is outside."""
        r = run_repo(self)
        s0 = F.synthetic_source(r)
        info = json.dumps(dataclasses.asdict(s0))
        out = os.path.join(os.path.dirname(r.root), "scratch")
        p = subprocess.run([sys.executable, "-B", "-c", _PRE_IMPORT, HERE, r.root, info, "dry-load", out], cwd=r.root,
                           env=ENV, capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, C.EXIT_OK, p.stdout[-600:] + p.stderr[-1500:])
        inv = read(os.path.join(out, C.RUN))["invocations"][-1]
        self.assertEqual((inv["outcome"], inv["outside_allowlist"], inv["refused_by_audit"]), ("ok", [], []))
        b58 = [o for o in inv["opened"] if o.endswith("data/derived_params.json")]
        self.assertEqual(len(b58), 1, "the import chain's read of the B58's derived file was recorded")
        a = C.Audit(subcommand="dry-load", engine=MAZDA, root=r.root, scratch=out)
        a.bind({k: v for k, v in C._paths_for(MAZDA, source=s0).items() if k != "b58_derived_abs"})
        self.assertFalse(a.allowed(b58[0]), "the control: without it the allowlist refuses the B58's file")
        # a stand-in fit the same way, T0's record in place (fit requires it), with the provenance of the code
        # it ran on (fit requires that code still: WP3's second fix of 23 October 2026)
        write_json(cal(s0, MAZDA, C.T0), {"schema": "epa-t0/1", "pass": True, "stand_in": True, "provenance":
                                          epa_freeze.provenance(MAZDA, source=s0, view=epa_rows.calibration_contract(
                                              MAZDA, source=s0))})
        p = subprocess.run([sys.executable, "-B", "-c", _PRE_IMPORT, HERE, r.root, info, "fit", ""], cwd=r.root,
                           env=ENV, capture_output=True, text=True, timeout=600)
        self.assertEqual(p.returncode, C.EXIT_OK, p.stdout[-600:] + p.stderr[-1500:])
        inv = runs(s0, MAZDA)[-1]
        self.assertEqual((inv["subcommand"], inv["outcome"], inv["outside_allowlist"]), ("fit", "ok", []))

    def test_dry_load_opens_only_its_allowlist(self):
        """The loader under the audit in a fresh process: its opened set inside the allowlist, the engine's
        tables and epa_engine.json among them, no channels file and no other engine's table."""
        r = self.fresh()
        out = os.path.join(os.path.dirname(r.root), "scratch")
        code = ("import os, sys; root, edir, cj, cm, commit, out, eng = sys.argv[1:8]; sys.path.insert(0, root)\n"
                "import calibrate_epa as C, epa_rows\n"
                "src = epa_rows.Source(root=root, engine_dir=edir, contract_json=cj, contract_md=cm, "
                "contract_commit=commit, allow_poisoned_tables=False)\n"
                "sys.exit(C.invoke('dry-load', eng, source=src, argv=['dry-load', '--engine', eng], "
                "body=lambda: C.dry_load(eng, source=src, out=out), scratch=out, audit=None))\n")
        s0 = F.synthetic_source(r)
        for eng in (MAZDA, FORD):
            p = subprocess.run([sys.executable, "-B", "-c", code, s0.root, s0.engine_dir, s0.contract_json,
                                s0.contract_md, s0.contract_commit, out, eng], cwd=r.root,
                               env=ENV, capture_output=True, text=True, timeout=600)
            self.assertEqual(p.returncode, C.EXIT_OK, p.stdout[-400:] + p.stderr[-1500:])
            inv = read(os.path.join(out, C.RUN))["invocations"][-1]
            self.assertEqual((inv["outcome"], inv["outside_allowlist"], inv["refused_by_audit"]), ("ok", [], []))
            paths = epa_rows.audit_paths(eng, source=F.synthetic_source(r))
            self.assertTrue(set(paths["table_files"]) <= set(inv["opened"]), "the engine's tables were read")
            self.assertIn(paths["engine_json"], inv["opened"])
            for c in paths["channels"]:
                self.assertNotIn(c, inv["opened"])
            others = [t for e in epa_rows.TABLES if e != eng
                      for t in epa_rows.audit_paths(e, source=F.synthetic_source(r))["table_files"]]
            self.assertFalse(set(others) & set(inv["opened"]), "another engine's table was opened")
            self.assertEqual(inv["result"]["rows"], sum(inv["result"]["by_type"].values()))
            self.assertFalse(os.path.exists(epa_freeze.calibration_dir(eng, root=r.root)),
                             "dry-load writes its scratch run.json only")

    def test_an_extra_open_is_a_defect(self):
        r = self.fresh()
        src = F.synthetic_source(r)
        stray = os.path.join(r.root, "notes.txt")
        write(stray, "not the calibration's\n")
        out = os.path.join(os.path.dirname(r.root), "scratch")
        code = invoke("dry-load", MAZDA, src, lambda: {"n": _open_task(stray)}, scratch=out)
        inv = read(os.path.join(out, C.RUN))["invocations"][-1]
        self.assertEqual(code, C.EXIT_DEFECT)
        self.assertEqual(inv["outside_allowlist"], ["notes.txt"])
        self.assertTrue(inv["outcome"].startswith("defect"))
        # the control: the same subcommand opening only its own table is no defect
        own = epa_rows.audit_paths(MAZDA, source=src)["table_files"][0]
        code = invoke("dry-load", MAZDA, src, lambda: {"n": _open_task(os.path.join(r.root, own))}, scratch=out)
        self.assertEqual(code, C.EXIT_OK)
        self.assertEqual(read(os.path.join(out, C.RUN))["invocations"][-1]["outside_allowlist"], [])

    def test_a_forbidden_open_is_refused_at_once(self):
        r = self.fresh()
        src = F.synthetic_source(r)
        paths = epa_rows.audit_paths(MAZDA, source=src)
        other = epa_rows.audit_paths(FORD, source=src)["table_files"][0]
        val = os.path.join(r.root, *paths["validation"].split("/"), MAZDA, "ARMED.json")
        out_file = os.path.join(r.root, *paths["outputs"].split("/"), "split.json")
        logs = os.path.join(r.root, "logs", "x.txt")
        for p in (val, out_file, logs):
            write(p, "{}\n")
        for target in (logs, os.path.join(r.root, paths["channels"][0]), os.path.join(r.root, other), val, out_file):
            seen = []

            def body(target=target):
                try:
                    _open_task(target)
                except PermissionError:
                    seen.append(True)
                    raise
            code = invoke("fit", MAZDA, src, body)
            self.assertEqual(code, C.EXIT_CRASH, target)
            self.assertEqual(seen, [True], target)
            inv = runs(src, MAZDA)[-1]
            self.assertEqual(inv["outcome"], "crash: PermissionError")
            self.assertEqual(len(inv["refused_by_audit"]), 1)
        # the control: the k3 file, the one generator output the calibration reads, is not refused
        code = invoke("fit", MAZDA, src, lambda: {"n": _open_task(os.path.join(r.root, paths["k3"]))})
        self.assertEqual(code, C.EXIT_OK)

    def test_the_data_folder_and_the_tables_rules(self):
        """The rules the open test cannot reach without opening real data, on the Audit itself: a path under
        the team's data folder is refused (here a temporary folder bound as it); the engine's own tables,
        epa_engine.json and the contract are refused only while the audit is sealed (a worker; every
        subcommand's computing phase; WP3's second fix of 23 October 2026), and refuse_tables refuses the
        first two alone (the gate's harness)."""
        r = self.fresh()
        src = F.synthetic_source(r)
        folder = os.path.join(os.path.dirname(r.root), "team_data")
        a = C.Audit(subcommand="fit", engine=MAZDA, root=r.root, scratch=None)
        a.bind(dict(C._paths_for(MAZDA, source=src), data_folder=folder.replace(os.sep, "/")))
        self.assertEqual(a.forbidden(os.path.join(folder, "MANIFEST.csv")), "the team's data folder")
        self.assertIsNone(a.forbidden(os.path.join(os.path.dirname(r.root), "elsewhere.csv")))
        paths = epa_rows.audit_paths(MAZDA, source=src)
        table = os.path.join(r.root, paths["table_files"][0])
        contract = os.path.join(r.root, paths["contract"][0])
        self.assertIsNone(a.forbidden(table))
        self.assertIsNone(a.forbidden(contract))
        a.refuse_tables = True
        self.assertIn("own tables", a.forbidden(table))
        self.assertIsNone(a.forbidden(contract), "refuse_tables leaves the contract readable")
        a.refuse_tables, a.sealed = False, True
        self.assertIn("own tables", a.forbidden(table))
        self.assertIn("own tables", a.forbidden(os.path.join(r.root, paths["engine_json"])))
        self.assertIn("the contract", a.forbidden(contract))
        self.assertIn("the contract", a.forbidden(os.path.join(r.root, paths["contract"][1])))

    def test_a_forbidden_argv_is_refused_and_ls_files_is_not(self):
        r = self.fresh()
        src = F.synthetic_source(r)
        table = epa_rows.audit_paths(MAZDA, source=src)["table_files"][0]

        def show():
            subprocess.run(["git", "show", f"HEAD:{table}"], cwd=r.root, capture_output=True)

        def ls_files():
            out = subprocess.run(["git", "ls-files", "-s", "--", table], cwd=r.root, capture_output=True, text=True)
            return {"listed": bool(out.stdout.strip())}
        self.assertEqual(invoke("fit", MAZDA, src, show), C.EXIT_CRASH)
        inv = runs(src, MAZDA)[-1]
        self.assertEqual(inv["outcome"], "crash: PermissionError")
        self.assertTrue(any("show" in x for x in inv["refused_by_audit"]))
        self.assertEqual(invoke("fit", MAZDA, src, ls_files), C.EXIT_OK)
        inv = runs(src, MAZDA)[-1]
        self.assertEqual(inv["result"], {"listed": True})
        self.assertTrue(any("ls-files" in " ".join(s) for s in inv["subprocesses"]))

    def test_a_git_command_that_reads_contents_is_refused_unless_its_path_is_allowed(self):
        """`git cat-file -p <sha>` names no folder, and reads any blob (the review's finding): refused; `git
        show <rev>:<the contract>` (the loader's own guard) and `git cat-file --batch-check` are not."""
        r = self.fresh()
        src = F.synthetic_source(r)
        table = epa_rows.audit_paths(MAZDA, source=src)["table_files"][0]
        blob = F.git(r.root, "rev-parse", f"HEAD:{table}")
        contract = epa_rows.audit_paths(MAZDA, source=src)["contract"][0]

        def cat():
            subprocess.run(["git", "cat-file", "-p", blob], cwd=r.root, capture_output=True)

        def fine():
            a = subprocess.run(["git", "show", f"HEAD:{contract}"], cwd=r.root, capture_output=True)
            b = subprocess.run(["git", "cat-file", "--batch-check"], cwd=r.root, input=b"HEAD\n", capture_output=True)
            return {"ok": a.returncode == 0 and b.returncode == 0}
        self.assertEqual(invoke("fit", MAZDA, src, cat), C.EXIT_CRASH)
        self.assertTrue(any("cat-file" in x for x in runs(src, MAZDA)[-1]["refused_by_audit"]))
        self.assertEqual(invoke("fit", MAZDA, src, fine), C.EXIT_OK)
        self.assertEqual(runs(src, MAZDA)[-1]["result"], {"ok": True})

    def bound(self, r, src):
        a = C.Audit(subcommand="fit", engine=MAZDA, root=r.root, scratch=None)
        a.bind(C._paths_for(MAZDA, source=src))
        return a

    def test_the_seal_covers_git_and_child_processes(self):
        """WP3's third fix of 24 October 2026 (the third isolation review): sealed, a git content read of the
        contract or a table is refused like the open (as an argv list and as Windows' command line), a child
        that is not git, or git running a subcommand outside SEALED_GIT, is refused; the step-2 code's own git
        commands are not. WP3's fourth fix (the fourth isolation review): sealed, git runs only in
        SEALED_GIT_SHAPES, word for word (own_git_forms, each shape the step-2 code runs), so the review's eleven
        planted forms (planted_git_forms) are refused, and so are a git with its own environment or another
        executable, a git outside the work tree, os.system, and a -c other than core.safecrlf=false whether
        sealed or not. The controls: unsealed, the same contract read and the same child pass, and every
        own form passes sealed."""
        r = self.fresh()
        src = F.synthetic_source(r)
        a = self.bound(r, src)
        paths = epa_rows.audit_paths(MAZDA, source=src)
        contract, table = paths["contract"][0], paths["table_files"][0]
        show_c, show_t = ["git", "show", "HEAD:" + contract], ["git", "show", "HEAD:" + table]
        child = [sys.executable, "-I", "-c", "print(1)"]
        own = own_git_forms(src)
        self.assertIsNone(a._argv_problem(show_c, cwd=r.root))
        self.assertIsNone(a._argv_problem(child, cwd=r.root))
        a.sealed = True
        for argv in (show_c, subprocess.list2cmdline(show_c), show_t, child, subprocess.list2cmdline(child),
                     ["git", "fast-export", "--all"], ["git", "worktree", "add", "x"], ["git", "--version"]):
            self.assertIsNotNone(a._argv_problem(argv, cwd=r.root), argv)
        self.assertIn("refuses now", a._argv_problem(show_c, cwd=r.root))
        self.assertIn("child process other than git", a._argv_problem(child, cwd=r.root))
        for argv in own:
            self.assertIsNone(a._argv_problem(argv, cwd=r.root), argv)
            self.assertIsNone(a._argv_problem(subprocess.list2cmdline(argv), cwd=r.root), argv)
        planted = planted_git_forms(src)
        self.assertEqual(len(planted), 11)
        for argv in planted:
            self.assertIsNotNone(a._argv_problem(argv, cwd=r.root), argv)
            self.assertIsNotNone(a._argv_problem(subprocess.list2cmdline(argv), cwd=r.root), argv)
        # an own form made a leak by what surrounds it: its own environment, another executable, another tree,
        # the shell, a pathspec's magic or glob, an extra word
        head = own[0]
        self.assertIn("environment", a._argv_problem(head, cwd=r.root, env={"GIT_CONFIG_COUNT": "1"}))
        self.assertIn("another executable", a._argv_problem(head, cwd=r.root, executable=sys.executable))
        self.assertIn("outside the work tree", a._argv_problem(head, cwd=os.path.dirname(r.root)))
        self.assertIn("outside the work tree", a._argv_problem(["git", "-C", os.path.dirname(r.root)] + head[1:],
                                                               cwd=r.root))
        self.assertIn("os.system", a._argv_problem(subprocess.list2cmdline(head), event="os.system", cwd=r.root))
        status = ["git", "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--"]
        self.assertIsNone(a._argv_problem(status + ["epa_rows.py"], cwd=r.root))
        for bad in (":(glob)epa_*.py", "epa_?ows.py", "epa_rows.py:", "../x.py", "/epa_rows.py", "-x"):
            self.assertIsNotNone(a._argv_problem(status + [bad], cwd=r.root), bad)
        self.assertIsNotNone(a._argv_problem(head + ["--quiet"], cwd=r.root))
        # a -c that is not core.safecrlf=false, the exec path, --config-env and the pager are refused unsealed too
        a.sealed = False
        for argv in (["git", "-c", "core.fsmonitor=x", "status"], ["git", "--exec-path=" + r.root, "status"],
                     ["git", "-c", "diff.external=x", "diff", "--ext-diff"], ["git", "-p", "log"],
                     ["git", "--config-env=core.fsmonitor=X", "status"]):
            self.assertIsNotNone(a._argv_problem(argv, cwd=r.root), argv)
        self.assertIsNone(a._argv_problem(["git", "-C", r.root, "-c", "core.safecrlf=false", "rev-parse", "HEAD"],
                                          cwd=r.root))
        # unsealed, diff prints contents unless --quiet, and log with any patch flag (the content rule judges it)
        for argv in (["git", "diff", "--exit-code", "HEAD", "--", "notes.txt"],
                     ["git", "diff", "--name-only", "-p", "HEAD", "--", "notes.txt"],
                     ["git", "log", "-U0", "--", "notes.txt"], ["git", "log", "--unified=0", "--", "notes.txt"],
                     ["git", "log", "-L", "1,9:notes.txt"], ["git", "log", "-Sx", "--", "notes.txt"],
                     ["git", "log", "--binary", "--", "notes.txt"], ["git", "log", "--cc", "--", "notes.txt"]):
            self.assertIn("outside the allowlist", a._argv_problem(argv, cwd=r.root) or "", argv)
        self.assertIsNone(a._argv_problem(["git", "diff", "--quiet", "HEAD", "--", "notes.txt"], cwd=r.root))
        self.assertIsNone(a._argv_problem(["git", "log", "--name-only", "--", "notes.txt"], cwd=r.root))

    def test_the_step2_codes_own_git_runs_pass_sealed(self):
        """The control of SEALED_GIT_SHAPES at run time (WP3's fourth fix of 24 October 2026): every git helper of
        epa_freeze and epa_rows, called in a sealed invoke on a synthetic repository, runs and is refused nothing;
        and each argv they ran is one of SEALED_GIT_SHAPES."""
        r = self.fresh()
        src = F.synthetic_source(r)
        paths = epa_rows.audit_paths(MAZDA, source=src)
        head = F.git(r.root, "rev-parse", "HEAD")
        code_file = os.path.join(r.root, "epa_rows.py")
        table = os.path.join(r.root, *paths["table_files"][0].split("/"))

        def body():
            C.seal_now()
            return {"head": epa_freeze.git_head(root=r.root) == head,
                    "clean": epa_freeze.git_clean(["epa_rows.py", "epa_fit.py"], root=r.root)[0] is True,
                    "dirs": len(epa_freeze.git_dirs(root=r.root)) >= 1,
                    "blob": bool(epa_freeze.git_blob(table, root=r.root)),
                    "head_blob": epa_freeze.head_blob(code_file, root=r.root) is not None,
                    "committed": epa_freeze.committed_at_head(code_file, root=r.root),
                    "blob_sha": len(epa_freeze.blob_sha256("HEAD", "epa_rows.py", root=r.root)) == 64,
                    "ancestor": epa_freeze.is_ancestor(head, head, root=r.root),
                    "logged": epa_freeze.logged_paths(r.root, paths["validation"] + "/" + MAZDA) == [],
                    "rows_head": epa_rows._git(r.root, "rev-parse", "HEAD").returncode == 0,
                    "rows_blob": epa_rows._git(r.root, "rev-parse", "HEAD:epa_rows.py").returncode == 0,
                    "rows_ancestor": epa_rows._git(r.root, "merge-base", "--is-ancestor", src.contract_commit,
                                                   "HEAD").returncode == 0,
                    "rows_show": epa_rows._blob_sha256(r.root, "HEAD", "epa_rows.py") is not None}
        code = invoke("fit", MAZDA, src, body)
        inv = runs(src, MAZDA)[-1]
        self.assertEqual((code, inv["outcome"], inv["refused_by_audit"]), (C.EXIT_OK, "ok", []))
        self.assertTrue(all(inv["result"].values()), inv["result"])
        ran = [x for x in inv["subprocesses"] if x]
        self.assertGreaterEqual(len(ran), 14)
        for argv in ran:
            g = C._git_parse(argv)
            self.assertTrue(C._sealed_shape(g["sub"], g["rest"]), argv)

    def test_another_spelling_of_a_sealed_file_is_refused_at_once(self):
        """The seal compares a file's identity as well as its normalised path (WP3's third fix of 24 October
        2026): the contract under Windows' \\\\?\\ prefix and a table through a hard link are refused while sealed;
        the control: unsealed, neither is."""
        r = self.fresh()
        src = F.synthetic_source(r)
        paths = epa_rows.audit_paths(MAZDA, source=src)
        contract = os.path.join(r.root, *paths["contract"][0].split("/"))
        table = os.path.join(r.root, *paths["table_files"][0].split("/"))
        link = os.path.join(os.path.dirname(r.root), "linked_table.csv")
        os.link(table, link)
        long_contract = "\\\\?\\" + os.path.abspath(contract) if os.name == "nt" else contract
        a = self.bound(r, src)
        self.assertIsNone(a.forbidden(link))
        self.assertIsNone(a.forbidden(long_contract))
        a.sealed = True
        self.assertIn("own tables", a.forbidden(link))
        self.assertIn("the contract", a.forbidden(long_contract))
        self.assertIsNone(a.forbidden(os.path.join(os.path.dirname(r.root), "elsewhere.csv")))

    def test_the_long_prefix_is_stripped_before_any_comparison(self):
        r"""_strip_long on its own (the fourth tests review: its \\?\ half was caught only by the file-id check, so
        a regression of it passed): the \\?\ and \\?\UNC\ spellings come back as the plain path, and a sealed audit
        with no file identities at all (own_ids, contract_ids and always_ids emptied) still refuses the contract
        under its \\?\ spelling by the path alone. The control: a plain path comes back unchanged."""
        self.assertEqual(C._strip_long(r"\\?\C:\x\y.json"), r"C:\x\y.json")
        self.assertEqual(C._strip_long(r"\\?\UNC\server\share\y.json"), r"\\server\share\y.json")
        self.assertEqual(C._strip_long(r"C:\x\y.json"), r"C:\x\y.json")
        if os.name != "nt":
            return
        r = self.fresh()
        src = F.synthetic_source(r)
        a = self.bound(r, src)
        a.sealed = True
        a.own_ids, a.contract_ids, a.always_ids = set(), set(), {}
        contract = os.path.abspath(os.path.join(r.root, *epa_rows.audit_paths(MAZDA, source=src)["contract"][0].split("/")))
        self.assertIn("the contract", a.forbidden(r"\\?" + "\\" + contract))
        self.assertIsNone(a.forbidden(r"\\?" + "\\" + os.path.join(os.path.dirname(r.root), "elsewhere.csv")))

    @unittest.skipUnless(os.name == "nt", "os.startfile is Windows' alone")
    def test_startfile_is_refused_while_sealed(self):
        """os.startfile while sealed is refused and named (the fourth tests review: with its rule off, every test
        passed). A path that does not exist, so that nothing would open had the audit let it through. The control:
        unsealed, the same call reaches the operating system, which reports the missing file."""
        r = self.fresh()
        src = F.synthetic_source(r)
        missing = os.path.join(os.path.dirname(r.root), "no_such_file_for_startfile.txt")

        def sealed_call():
            C.seal_now()
            os.startfile(missing)

        def unsealed_call():
            try:
                os.startfile(missing)
            except PermissionError:
                raise
            except OSError:
                return {"reached_the_os": True}
            return {"reached_the_os": True}
        self.assertEqual(invoke("fit", MAZDA, src, sealed_call), C.EXIT_CRASH)
        inv = runs(src, MAZDA)[-1]
        self.assertEqual(inv["outcome"], "crash: PermissionError")
        self.assertTrue(inv["refused_by_audit"][0].startswith("startfile"), inv["refused_by_audit"])
        self.assertEqual(invoke("fit", MAZDA, src, unsealed_call), C.EXIT_OK, runs(src, MAZDA)[-1]["outcome"])
        self.assertEqual(runs(src, MAZDA)[-1]["result"], {"reached_the_os": True})

    def test_a_pool_worker_reports_its_opens_and_refuses_the_tables(self):
        """C3: a parent's hook does not see a spawn worker; worker_init installs the audit there, and the
        opens it records come back with each task's result (epa_fit.ordered_map) into run.json. A worker reads
        no table: one that tries is refused (the parent crashes); the control, in this process (jobs 1), is
        this process's audit's, which allows the engine's own table."""
        r = self.fresh()
        src = F.synthetic_source(r)
        stray = os.path.join(r.root, "worker_notes.txt")
        write(stray, "opened in a worker\n")
        own = os.path.join(r.root, epa_rows.audit_paths(MAZDA, source=src)["table_files"][0])
        code = invoke("fit", MAZDA, src, lambda: {"sizes": epa_fit.ordered_map(_open_task, [stray, stray], jobs=2,
                                                                                initializer=epa_fit.WORKER_INIT)})
        inv = runs(src, MAZDA)[-1]
        self.assertEqual(code, C.EXIT_DEFECT, inv["outcome"])
        self.assertIn("worker_notes.txt", inv["opened"])
        self.assertEqual(inv["outside_allowlist"], ["worker_notes.txt"])
        code = invoke("fit", MAZDA, src, lambda: {"sizes": epa_fit.ordered_map(_open_task, [own, own], jobs=2,
                                                                                initializer=epa_fit.WORKER_INIT)})
        self.assertEqual(code, C.EXIT_CRASH, runs(src, MAZDA)[-1]["outcome"])
        # and the contract, which a worker never reads either (WP3's second fix of 23 October 2026)
        contract = os.path.join(r.root, epa_rows.audit_paths(MAZDA, source=src)["contract"][0])
        code = invoke("fit", MAZDA, src, lambda: {"sizes": epa_fit.ordered_map(_open_task, [contract, contract],
                                                                                jobs=2, initializer=epa_fit.WORKER_INIT)})
        self.assertEqual(code, C.EXIT_CRASH, runs(src, MAZDA)[-1]["outcome"])
        # (a task that raised returns no record of its opens: the crash is the record)

        # a worker whose code catches the refusal (linecache does) is still a defect: the refusal reaches run.json
        code = invoke("fit", MAZDA, src, lambda: {"sizes": epa_fit.ordered_map(_swallowed_open_task, [own, own],
                                                                                jobs=2, initializer=epa_fit.WORKER_INIT)})
        inv = runs(src, MAZDA)[-1]
        self.assertEqual(code, C.EXIT_DEFECT, inv["outcome"])
        self.assertIn(os.path.relpath(own, r.root).replace(os.sep, "/"), inv["refused_by_audit"])
        code = invoke("fit", MAZDA, src, lambda: {"sizes": epa_fit.ordered_map(
            _open_task, [own], jobs=1, initializer=epa_fit.WORKER_INIT)})
        self.assertEqual(code, C.EXIT_OK)

    def test_the_hook_is_installed_before_any_project_import(self):
        """On the command line (WP3_INTERFACES.md 3.3): the module's `if __name__ == "__main__"` prelude,
        which installs the audit, comes before its first project import, and every import before it is the
        standard library's."""
        with open(os.path.join(HERE, "calibrate_epa.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        project = {os.path.splitext(f)[0] for f in os.listdir(HERE) if f.endswith(".py")}
        first_project, prelude = None, None
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                if any(n.split(".")[0] in project for n in names) and first_project is None:
                    first_project = i
            if (isinstance(node, ast.If) and "__main__" in ast.unparse(node.test) and prelude is None
                    and "_prelude" in ast.unparse(node)):
                prelude = i
        self.assertIsNotNone(prelude)
        self.assertIsNotNone(first_project)
        self.assertLess(prelude, first_project)
        src = ast.unparse(next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_prelude"))
        self.assertIn("install_audit", src)
        self.assertIn("DERIVING_PARAMS", src)


# ======================================================================================================
class Order(RunCase):
    """PLAN.md WP4's order and Run 1's proofs: each subcommand refuses without its predecessor's record or
    proof, and the refusal is listed in run.json."""

    def test_every_subcommand_needs_its_predecessor(self):
        stand = StandIns(self)
        for sub in ("poison", "e6", "check", "complete"):
            self.assertEqual(self.sub(sub, stand), C.EXIT_REFUSED, sub)
        outs = [i["outcome"] for i in runs(self.src, MAZDA)]
        self.assertEqual(len(outs), 4)
        self.assertTrue(all(o.startswith("refused: ") for o in outs), outs)
        self.assertIn("freeze.json does not exist", outs[0])
        self.assertIn("row1.json does not exist", outs[3])
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.STARTED)), "a refused subcommand starts nothing")
        # fit needs T0's record, passed (amendment A1)
        self.assertEqual(self.sub("fit", stand), C.EXIT_REFUSED)
        self.assertIn("t0.json does not exist", self.last()["outcome"])

    def test_t0_writes_started_and_fit_needs_it_passed(self):
        """t0: STARTED exists when T0 first evaluates (the stand-in records it), and t0.json is written; a
        failed T0 holds the fit (the defect route re-runs it), a passed one lets it go."""
        stand = StandIns(self, t0_pass=False)
        self.assertEqual(self.sub("t0", stand), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(stand.calls[0], ("t0", True), "STARTED before T0's first evaluation")
        self.assertEqual(read(cal(self.src, MAZDA, C.STARTED))["first_subcommand"], "t0")
        self.assertEqual(self.sub("fit", stand), C.EXIT_REFUSED)
        self.assertIn("T0 did not pass", self.last()["outcome"])
        # t0 runs once; the defect route re-runs it on the committed fix
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_REFUSED)
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        route = epa_freeze.DefectRoute(reason="T0 failed (synthetic)", fix_commit=fix)
        self.assertEqual(self.sub("t0", StandIns(self), defect=route), C.EXIT_OK, self.last()["outcome"])
        d = read(cal(self.src, MAZDA, epa_freeze.DEFECTS))
        self.assertEqual([(e["k"], e["found_by"]) for e in d], [(1, "calibrate_epa.py t0 --defect")])
        self.assertEqual(sorted(d[0]), sorted(epa_freeze.DEFECT_KEYS), "no wall-clock date in defects.json")
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_OK, self.last()["outcome"])

    def test_t0_and_fit_need_committed_code_and_a_positive_job_count(self):
        """Every call under the stand-ins (WP3's second fix of 23 October 2026, on the test review's finding: a
        guard removed sent these calls into the real T0, and the suite hung instead of failing)."""
        write(cal(self.src, MAZDA, C.STAGE0), "{}\n")
        with self.assertRaises(C.Refusal) as cm:
            with contextlib_all(StandIns(self).patches()):
                C.t0(MAZDA, source=self.src, jobs=1, defect=None)
        self.assertIn("before the fit", str(cm.exception))
        os.remove(cal(self.src, MAZDA, C.STAGE0))
        for bad in (0, "2", 1.0):
            with self.assertRaises(C.Refusal) as cm:
                with contextlib_all(StandIns(self).patches()):
                    C.fit(MAZDA, source=self.src, jobs=bad, defect=None)
            self.assertIn("--jobs", str(cm.exception))
        with open(os.path.join(self.repo.root, "epa_stats.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# an uncommitted edit\n")
        for call in (lambda: C.t0(MAZDA, source=self.src, jobs=1, defect=None),
                     lambda: C.fit(MAZDA, source=self.src, jobs=1, defect=None)):
            with self.assertRaises(C.Refusal) as cm:
                with contextlib_all(StandIns(self).patches()):
                    call()
            self.assertIn("committed", str(cm.exception))

    def test_t0_and_fit_refuse_while_a_pin_is_open(self):
        """The pins guard on the production tables (decision 56; WP3_INTERFACES.md 11). The production u_D
        table pins the meter's and the torque's terms from every report's Table 8 (epa_stats.U_D), and the
        production D3 summary columns are pinned since 24 October 2026 (decisions 78-80: d3_rows.unpinned_for
        names nothing on any engine), so the production tables pass the guard. Controls (mistake 12): a D3
        summary column left open (d3_rows.unpinned_for patched, as WP3_INTERFACES.md 14 asks) makes t0 and fit
        refuse naming it alone; one report's torque pin taken away (the Ford's HD1), or every meter pin,
        refuses naming that term and the gating rows that read it; a D3 summary column unpinned under the
        synthetic terms refuses too. Every other test runs under pinned_terms, whose synthetic terms read on
        the synthetic rows, which belong to no report."""
        import d3_rows
        unpinned = [p for p in StandIns(self).patches() if not isinstance(p, type(F.pinned_terms()))]
        # the production tables, both pinned, pass the guard
        self.assertEqual(epa_stats.unpinned_u_d(terms=epa_stats.U_D), {})
        self.assertEqual([d3_rows.unpinned_for(e) for e in (FORD, HONDA, MAZDA)], [(), (), ()])
        self.assertIsNone(C._pins_guard(MAZDA))
        # ... and a D3 summary column left open refuses t0 and fit, naming it alone (the u_D table pinned)
        open_cx9 = (lambda e: ("cx9_2016.test_id",) if e == MAZDA else ())
        with mock.patch.object(d3_rows, "unpinned_for", open_cx9):
            for call in (lambda: C.t0(MAZDA, source=self.src, jobs=1, defect=None),
                         lambda: C.fit(MAZDA, source=self.src, jobs=1, defect=None)):
                with self.assertRaises(C.Refusal) as cm:
                    with contextlib_all(unpinned):
                        call()
                msg = str(cm.exception)
                self.assertIn("the D3 summary column cx9_2016.test_id", msg)
                self.assertNotIn("u_D's", msg, "the production u_D table is pinned (decision 56)")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.STARTED)))
        with mock.patch.object(d3_rows, "unpinned_for", lambda _engine: ()):
            self.assertIsNone(C._pins_guard(MAZDA))
        # ... and a pin taken away from it refuses, naming the term (the D3 columns pinned, so it is alone)
        torque, meter = epa_stats.U_D["torque"], epa_stats.U_D["meter"]
        short = dict(epa_stats.U_D, torque=dataclasses.replace(
            torque, cells=tuple(c for c in torque.cells if c[0] != epa_stats.FORD_HD1)))
        bare = dict(epa_stats.U_D, meter=dataclasses.replace(meter, cells=()))
        for terms, name in ((short, "'torque'"), (bare, "'meter'")):
            with self.subTest(term=name):
                with mock.patch.object(epa_stats, "U_D", terms), \
                        mock.patch.object(d3_rows, "unpinned_for", lambda _engine: ()):
                    with self.assertRaises(C.Refusal) as cm:
                        C._pins_guard(MAZDA)
                    msg = str(cm.exception)
                    self.assertIn(f"u_D's {name} term (read by ", msg)
                    self.assertIn("D1", msg)
                    self.assertNotIn("D3 summary column", msg)
                    for call in (lambda: C.t0(MAZDA, source=self.src, jobs=1, defect=None),
                                 lambda: C.fit(MAZDA, source=self.src, jobs=1, defect=None)):
                        with self.assertRaises(C.Refusal) as cm:
                            with contextlib_all(unpinned):
                                call()
                        self.assertIn(f"u_D's {name} term", str(cm.exception))
        with contextlib_all(StandIns(self).patches()), mock.patch.object(d3_rows, "unpinned_for",
                                                                         lambda name: ("cx9_2016.test_id",)):
            with self.assertRaises(C.Refusal) as cm:
                C.t0(MAZDA, source=self.src, jobs=1, defect=None)
        self.assertIn("cx9_2016.test_id", str(cm.exception))
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.STARTED)))

    def test_the_pins_guard_reads_every_engines_d3_columns(self):
        """The code is shared, so one engine's open D3 summary columns hold every engine's T0 and fit (WP3's third
        fix of 24 October 2026, on the Run 1 review's finding: pinning the Honda's columns in d3_rows.py after the
        Ford's T0 would change the code the Ford's T0 certified, and the Ford's arming would refuse under C10). In
        production every column is pinned since 24 October 2026 (decisions 78-80), so no engine's guard names one.
        Controls, with d3_rows.unpinned_for patched (WP3_INTERFACES.md 14): the Honda's and the Mazda's columns
        open refuse the Ford naming both; only the Honda's open refuses the Ford and the Mazda naming the Honda's
        alone; none open passes."""
        import d3_rows
        for eng in (FORD, HONDA, MAZDA):
            self.assertEqual(d3_rows.unpinned_for(eng), ())
            self.assertIsNone(C._pins_guard(eng))
        both = (lambda e: {HONDA: ("accord_2018.test_id",), MAZDA: ("cx9_2016.modal_fuel_to_g",)}.get(e, ()))
        with mock.patch.object(d3_rows, "unpinned_for", both):
            with self.assertRaises(C.Refusal) as cm:
                C._pins_guard(FORD)
        msg = str(cm.exception)
        self.assertIn(f"({HONDA})", msg)
        self.assertIn(f"({MAZDA})", msg)
        self.assertIn("accord_2018.", msg)
        self.assertIn("cx9_2016.", msg)
        only_honda = (lambda e: ("accord_2018.synthetic",) if e == HONDA else ())
        with mock.patch.object(d3_rows, "unpinned_for", only_honda):
            for eng in (FORD, MAZDA):
                with self.assertRaises(C.Refusal) as cm:
                    C._pins_guard(eng)
                self.assertIn(f"accord_2018.synthetic ({HONDA})", str(cm.exception))
                self.assertNotIn("cx9_2016", str(cm.exception))
            # and through t0 on the synthetic Mazda: refused before STARTED
            with contextlib_all([p for p in StandIns(self).patches() if not isinstance(p, type(F.pinned_terms()))]):
                with self.assertRaises(C.Refusal):
                    C.t0(MAZDA, source=self.src, jobs=1, defect=None)
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.STARTED)))
        with mock.patch.object(d3_rows, "unpinned_for", lambda _e: ()):
            for eng in (FORD, HONDA, MAZDA):
                self.assertIsNone(C._pins_guard(eng))

    def test_complete_needs_its_fresh_process(self):
        env = dict(os.environ)
        env.pop("DERIVING_PARAMS", None)
        with mock.patch.dict(os.environ, env, clear=True):
            with self.assertRaises(C.Refusal) as cm:
                C.complete(MAZDA, source=self.src, jobs=1)
        self.assertIn("DERIVING_PARAMS", str(cm.exception))


# ======================================================================================================
class Records(RunCase):
    """t0, fit, poison, e6, complete and check on a synthetic repository, the expensive stages replaced by
    StandIns and stand_in_task: STARTED before the first model evaluation and kept through a crash;
    stage0.json's SEEN_BEFORE_THE_FIT; the records' keys and hashes; the defect route; check's comparison."""

    def test_fit_writes_its_records_and_the_freeze(self):
        stand = StandIns(self)
        self.through("fit", stand)
        self.assertEqual(stand.calls[1], ("ladder", True), "STARTED is written before the ladder evaluates a row")
        started = read(cal(self.src, MAZDA, C.STARTED))
        self.assertEqual(started["first_subcommand"], "t0")
        self.assertEqual(sorted(started), ["code_sha_text", "contract_commit", "engine", "first_subcommand",
                                           "git_head", "run1_gate", "view_sha256"])
        self.assertEqual(started["run1_gate"], {"rule": None, "switch": None})
        s0 = read(cal(self.src, MAZDA, C.STAGE0))
        self.assertEqual(s0["schema"], "epa-stage0/1")
        self.assertEqual(s0["seen_before_the_fit"], list(C.SEEN_BEFORE_THE_FIT))
        for k in ("lambda_missing", "spark_sentinel", "censoring", "tip_below_barometer", "coolant_vs_oil",
                  "meter_vs_injector", "cam", "bounds", "hot_floor_rounding"):
            self.assertIn(k, s0["checks"])
        # decision 54's two sentinels counted apart (epa_rows.PointRow.spark_empty), against the synthetic
        # design's own calibration-line overrides (test_epa_fixtures.DEFAULT_SPECS), never typed
        design = F.DEFAULT_SPECS[MAZDA]
        cal_ov = [c for (_k, ln, _i), c in design.overrides.items() if ln not in design.held_out_lines]
        want = (sum(1 for c in cal_ov if c.get("spark_timing_cad_btdc") == "-120.0"),
                sum(1 for c in cal_ov if c.get("spark_timing_cad_btdc") == ""))
        sen = s0["checks"]["spark_sentinel"]
        self.assertEqual((sen["sentinel_value"], sen["empty_cell"]), want)
        self.assertEqual(sum(want), sen["total"])
        self.assertIn("no_statistic_outcomes", s0["declarations"])
        self.assertIn("s3b_depth_upper_invariant_source", s0["checks"]["bounds"])
        fa = read(cal(self.src, MAZDA, C.fit_file("A")))
        self.assertEqual(fa["provenance"]["git"]["head"], epa_freeze.git_head(root=self.repo.root))
        self.assertIn("validate_epa.py", fa["provenance"]["code_sha_text"])
        ins = read(cal(self.src, MAZDA, C.IN_SAMPLE))
        self.assertEqual((ins["chosen_form"], sorted(ins["forms"])), ("A", ["A"]))
        self.assertNotIn("E8", ins["forms"]["A"]["statistics"])
        self.assertIsNotNone(ins["forms"]["A"]["e8"])
        # decision 77's statistics that neither block nor pass, recorded per form (WP3's third fix of 24 October
        # 2026): the judge's own InSample.noise, as a list
        self.assertEqual(sorted(ins["forms"]["A"]),
                         ["e8", "failing", "no_line", "noise", "passes", "statistics", "steady_only_tit"])
        self.assertIsInstance(ins["forms"]["A"]["noise"], list)
        # decision 83: the steady-only TIT reading beside the form's stage, flagged a sensitivity that decides nothing
        sto = ins["forms"]["A"]["steady_only_tit"]
        self.assertEqual((sto["decides"], sto["rows"], sorted(sto["statistics"])),
                         (False, list(epa_stats.STEADY_TIT_ROWS), sorted(epa_stats.STEADY_TIT_ROWS)))
        self.assertIn("decision 83", sto["reading"])
        fz = read(cal(self.src, MAZDA, C.FREEZE))
        self.assertEqual(sorted(fz), sorted(epa_freeze.FREEZE_KEYS))
        self.assertEqual(sorted(fz["fits"]), ["fit_A.json", "in_sample.json", "stage0.json"])
        dvals = read(epa_freeze.derived_path(MAZDA, root=self.repo.root))
        self.assertEqual(engines.frozen_sections_sha256(dvals), fz["frozen_sections_sha256"])
        # every run.json entry records the gate as it stood
        self.assertEqual({tuple(sorted(i["run1_gate"])) for i in runs(self.src, MAZDA)},
                         {("gated", "rule", "switch", "waits")})
        # the order: a second fit is the defect route
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("re-freeze", self.last()["outcome"])

    def test_started_survives_a_crash_and_the_defect_route_moves_the_run(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.assertEqual(self.sub("fit", StandIns(self, crash=True)), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: RuntimeError")
        self.assertTrue(os.path.exists(cal(self.src, MAZDA, C.STARTED)), "a crashed fit leaves STARTED")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))
        # the control of the route: a plain re-fit is refused
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        # the fix, committed; the defect route names it, and re-runs from T0
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        route = epa_freeze.DefectRoute(reason="a stand-in ladder that crashed", fix_commit=fix)
        stand = StandIns(self)
        self.assertEqual(self.sub("fit", stand, defect=route), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual([c[0] for c in stand.calls], ["t0", "ladder"], "the defect route re-runs T0 first")
        old = os.path.join(epa_freeze.calibration_dir(MAZDA, root=self.repo.root), "defect_1")
        self.assertTrue({C.STARTED, C.T0, C.RUN} <= set(os.listdir(old)))
        self.assertEqual(read(os.path.join(old, C.RUN))["invocations"][1]["outcome"], "crash: RuntimeError")
        d = read(cal(self.src, MAZDA, epa_freeze.DEFECTS))
        self.assertEqual([(e["k"], e["fix_commit"], e["previous_run"], e["run_invocation"]) for e in d],
                         [(1, fix, "defect_1/", 1)])
        self.assertNotIn("date", d[0])
        self.assertEqual(runs(self.src, MAZDA)[d[0]["run_invocation"] - 1]["subcommand"], "fit")
        self.assertTrue(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))
        # a fix commit that is not one is refused before anything moves
        bad = epa_freeze.DefectRoute(reason="x", fix_commit="0" * 40)
        self.assertEqual(self.sub("fit", StandIns(self), defect=bad), C.EXIT_REFUSED)
        self.assertIn("defect route's authority", self.last()["outcome"])
        self.assertFalse(os.path.exists(os.path.join(epa_freeze.calibration_dir(MAZDA, root=self.repo.root),
                                                     "defect_2")))

    def test_started_by_a_fit_holds_and_started_by_t0_does_not(self):
        """WP3_INTERFACES.md 5.5.1, fit "requires STARTED absent or written by t0": a STARTED a fit wrote
        (here one that crashed before S0 wrote stage0.json) refuses a plain fit; T0's lets it run (the
        control), and a T0 STARTED with a crashed fit's stage0.json beside it refuses again."""
        write(cal(self.src, MAZDA, C.STARTED), json.dumps({"engine": MAZDA, "first_subcommand": "fit"}) + "\n")
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("a fit has started (STARTED)", self.last()["outcome"])
        write(cal(self.src, MAZDA, C.STARTED), json.dumps({"engine": MAZDA, "first_subcommand": "t0"}) + "\n")
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK, self.last()["outcome"])
        write(cal(self.src, MAZDA, C.STAGE0), "{}\n")
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("stage0.json exists", self.last()["outcome"])
        os.remove(cal(self.src, MAZDA, C.STAGE0))
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(read(cal(self.src, MAZDA, C.STARTED))["first_subcommand"], "t0", "STARTED is never rewritten")

    def test_e6_complete_and_check(self):
        stand = StandIns(self)
        self.through("e6", stand)
        convs = [c for c in stand.calls if c[0] == "refit"]
        self.assertEqual([c[1]["cell_referenced"] for c in convs], [False, True, True])
        self.assertEqual(convs[1][1]["afr_st"], engines.read_spec("b58")["fuel"]["afr_st"])
        self.assertEqual(convs[2][1]["lhv_j_per_kg"], engines.read_spec("b58")["fuel"]["lhv_j_per_kg"])
        self.assertEqual({tuple(c[2]) for c in convs}, {("A",)}, "the refits read the frozen ladder's fits")
        for v in C.E6_VARIANTS:
            f = read(cal(self.src, MAZDA, C.e6_file(v)))
            self.assertEqual(engines.frozen_sections_sha256(f["values"]), f["frozen_sections_sha256"])
            if f["conventions"] is not None:
                epa_stats.Conventions(**f["conventions"])                  # validate_epa's reading
        r7 = read(cal(self.src, MAZDA, C.e6_file("7_090")))
        base = read(cal(self.src, MAZDA, C.fit_file("A")))["values"]["cycle"]["knock_a"]
        self.assertEqual(r7["values"]["cycle"]["knock_a"], base / 0.9)
        pois = read(cal(self.src, MAZDA, C.POISON))
        self.assertTrue(pois["all_equal"])
        self.assertEqual(epa_freeze.poison_problems(pois, engine=MAZDA, frozen_sections_sha256=read(cal(
            self.src, MAZDA, C.FREEZE))["frozen_sections_sha256"], poisons=tuple(epa_rows.POISONS),
            run_keys=epa_fit.POISON_RUN_KEYS, stages=epa_fit.poison_run_stages(), tied_of=epa_fit.poison_tied_stages), [])
        self.assertTrue(all(r["full_form_a"]["frozen_sections_sha256_equal"] for r in pois["runs"].values()))
        self.assertTrue(all(r["copies_are_not_the_tables"] and r["engine_facts_equal"] for r in pois["runs"].values()))
        self.assertEqual(sorted(pois["reference_equals_fit"]), ["S1", "S3a", "S3b", "S3c"])
        # complete, with the climbs replaced; the probes' cells recorded as built (epa_fit.perturbed)
        moved, real_perturbed = [], epa_fit.perturbed

        def recording(plant, *, record, field, value):
            moved.append((field, value))
            return real_perturbed(plant, record=record, field=field, value=value)
        self.assertEqual(self.sub("complete", stand, extra=[mock.patch.object(epa_fit, "perturbed", recording)]),
                         C.EXIT_OK, self.last()["outcome"])
        comp = read(cal(self.src, MAZDA, C.COMPLETE))
        # a negative constant's +1 cell lies above it (IVC near -140 deg): v0 + 0.1 |v0|, then v0 - 0.1 |v0|
        ivc = [v for f, v in moved if f == "ivc_deg"]
        v0 = comp["e6_probes"]["row9"]["ivc_deg"]["value"]
        self.assertLess(v0, 0.0)
        self.assertEqual(ivc, [v0 + 0.1 * abs(v0), v0 - 0.1 * abs(v0)])
        fz = read(cal(self.src, MAZDA, C.FREEZE))
        self.assertEqual(comp["frozen_sections_sha256"], fz["frozen_sections_sha256"])
        self.assertTrue(comp["f7_table_and_floor_identical_under_two_knees"])
        dvals = read(epa_freeze.derived_path(MAZDA, root=self.repo.root))
        self.assertEqual(dvals["k3"], {"turb_knee_k": comp["k3"]["knee_k"]})
        self.assertEqual(dvals["loop"], {"torque_floor_nm": 12.5})
        self.assertEqual(dvals["deliverable_torque"], comp["deliverable_torque"]["table"])
        self.assertEqual(engines.frozen_sections_sha256(dvals), fz["frozen_sections_sha256"])
        built = engines.build_candidate(MAZDA, dvals)
        self.assertEqual(comp["engine_sha"], engines.engine_sha(built))
        self.assertEqual(comp["dump"]["sha256"], epa_freeze.frozen_plant_dump(built).sha256)
        self.assertEqual(sorted(comp["e6_files"]), sorted(f"{epa_freeze.CALIBRATION_DIR}/{MAZDA}/{C.e6_file(v)}"
                                                          for v in C.E6_VARIANTS))
        # E6 row 6's probe by its hand answer: the stand-in gas moves 0.5 K per W/K of UA_PORT and the flow
        # not at all, so the housing equivalent's slope is f x 0.5 and the change worth R1 is R1 / (0.5 f)
        r1 = F.CONTRACT_BLOCKS["r1_housing_k"]
        row6 = comp["e6_probes"]["row6"]
        self.assertAlmostEqual(row6["probe"]["ua_port"], r1 / (0.5 * HS["f"]), places=9)
        self.assertEqual(row6["detail"]["ua_port"]["method"], "probe")
        # a constant the stand-in climb does not see falls back: +-10 crank degrees for IVC (the synthetic
        # Mazda's tables give no effective stroke, and their constant Atkinson ratio 1.2 beside an intake cam that
        # moves with MAP is no exact fit of defect D-1's reading, so no bracket), +-10 % for the rest
        r9 = comp["e6_probes"]["row9"]
        self.assertEqual((r9["ivc_deg"]["method"], r9["ivc_deg"]["size"]), ("fallback", 10.0))
        self.assertIn("the Atkinson ratio is not x(EVO0 + exhaust cam)", r9["ivc_deg"]["why_not_bracket"])
        self.assertIn("no exact fit", comp["e6_probes"]["brackets"]["evo_deg"]["why_not_bracket"])
        # decision 85: the noise floor from the stand-in's resolution at the base cell; a constant the stand-in
        # climb does not see (IVC) is not visible at R1 and counted excluded, one it sees (UA_PORT, the floor of the
        # back-pressure law through the flow) keeps its probe
        nn = comp["e6_probes"]["numerical_noise"]
        cell = comp["e6_probes"]["climb_cell"]["point"]
        self.assertAlmostEqual(nn["housing_k"], HS["f"] * STAND_IN_RESOLUTION["egt"]
                               + HS["dTh_per_unit_ln_mdot"] * STAND_IN_RESOLUTION["mdot"] / cell["mdot"], places=15)
        self.assertIn("decision 85", nn["rule"])
        self.assertEqual((r9["ivc_deg"]["visible_at_r1"], r9["ivc_deg"]["counted_excluded"]), (False, True))
        self.assertIn("not visible at R1", r9["ivc_deg"]["not_visible_at_r1"])
        self.assertIn("ivc_deg", comp["e6_probes"]["not_visible_at_r1"])
        self.assertTrue(row6["detail"]["ua_port"]["visible_at_r1"])
        self.assertTrue(comp["e6_probes"]["row5"]["detail"]["exh_bp_min_kpa"]["visible_at_r1"])
        self.assertNotIn("ua_port", comp["e6_probes"]["not_visible_at_r1"])
        self.assertEqual(r9["t_head_k"]["size"], 0.1 * abs(r9["t_head_k"]["value"]))
        self.assertEqual(sorted(comp["e6_row4"]), ["c_turb", "frozen", "ua_gas_turb", "ua_turb_amb"])
        self.assertEqual(sorted(comp["e6_row4"]["c_turb"]), ["x0.75", "x1.333"])
        self.assertEqual(sorted(comp["e6_row7"]), ["0.90", "1.00", "1.10"])
        self.assertEqual(sorted(comp["e6_row13"]), ["dwell_0s", "dwell_30s", "rule"])
        self.assertEqual(sorted(comp["e6_in_use"]), sorted(("frozen",) + C.E6_VARIANTS))
        self.assertEqual([a["step"] for a in comp["finiteness"]["asserted_before"]][0], "1 table")
        # E6 rows 2 and 3's model in use carries the variant's fuel (engines.with_fuel); rows 1 and 7 the frozen
        # plant's (the control): row 3's heat release per gram is the B58's 44 MJ/kg, row 2's exhaust moves
        use = comp["e6_in_use"]
        lhv = float(engines.read_spec("b58")["fuel"]["lhv_j_per_kg"])
        self.assertEqual(use["3"]["heat_per_gram_j"], lhv * 1e-3)
        self.assertNotEqual(use["3"]["heat_per_gram_j"], use["frozen"]["heat_per_gram_j"])
        self.assertNotEqual(use["3"]["coolant_heat_w"], use["frozen"]["coolant_heat_w"])
        self.assertNotEqual(use["2"]["exhaust_gps"], use["frozen"]["exhaust_gps"])
        for v in ("1", "7_090", "7_110"):
            self.assertEqual(use[v]["heat_per_gram_j"], use["frozen"]["heat_per_gram_j"], v)
        # check: the in-sample stage given back byte for byte (the stand-in judge both times)
        self.assertEqual(self.sub("check", stand), C.EXIT_OK, self.last()["outcome"])
        # the control: one number of in_sample.json moved, and check reports a mismatch, apart from a refusal
        p = cal(self.src, MAZDA, C.IN_SAMPLE)
        rec = read(p)
        st = rec["forms"]["A"]["statistics"]
        row = next(k for k, v in st.items() if v["E"] is not None)
        st[row]["E"] = st[row]["E"] + 1e-9
        epa_freeze.write_json_atomic(p, rec)
        self.assertEqual(self.sub("check", stand), C.EXIT_MISMATCH)
        self.assertTrue(self.last()["outcome"].startswith("mismatch: the in-sample stage recomputed is not in_sample.json"),
                        self.last()["outcome"])
        # and the mismatch stands in run.json: a later check refuses until the defect route
        self.assertEqual(self.sub("check", stand), C.EXIT_REFUSED)
        self.assertIn("mismatch", self.last()["outcome"])

    def test_the_f7_control_fails_when_the_table_moves_with_the_knee(self):
        stand = StandIns(self)
        self.through("e6", stand)

        def moving(item):
            out = stand_in_task(item)
            if item[0] == "table":
                kn = item[1].engine.damage.turb_knee_k
                raw = tuple((r, t + 1e-6 * kn) for r, t in out.raw)
                out = dataclasses.replace(out, raw=raw)
            return out
        self.assertEqual(self.sub("complete", stand, task=moving), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.COMPLETE)))


# ======================================================================================================
class Poison(RunCase):
    """C8's proof: mandatory before e6 and complete, its comparisons able to come out false, the real tables
    unreadable while the poisoned stages run, the copies shown not to be the tables, the reference tied to
    the fit."""

    def test_the_proof_is_mandatory(self):
        """e6 refuses without poison.json, and with one that is not the proof; on the Mazda the full form-A
        poison fit is mandatory (the control is every test that runs e6 after a passing poison)."""
        stand = StandIns(self)
        self.through("fit", stand)
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("poison.json does not exist", self.last()["outcome"])
        self.assertEqual(self.sub("poison", stand, full=False), C.EXIT_REFUSED)
        self.assertIn("mandatory on mazda_25t", self.last()["outcome"])
        self.assertEqual(self.sub("poison", stand), C.EXIT_OK, self.last()["outcome"])
        p = cal(self.src, MAZDA, C.POISON)
        good = read(p)
        bad = json.loads(json.dumps(good))
        bad["runs"]["high"]["stages"]["S1"] = False
        epa_freeze.write_json_atomic(p, bad)
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("comparison is not equal", self.last()["outcome"])
        bad = dict(good, frozen_sections_sha256="0" * 64)
        epa_freeze.write_json_atomic(p, bad)
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("other frozen sections", self.last()["outcome"])
        epa_freeze.write_json_atomic(p, good)
        self.assertEqual(self.sub("e6", stand), C.EXIT_OK, self.last()["outcome"])

    def test_each_comparison_fails_alone_when_its_input_moves(self):
        """C8's proof, comparison by comparison (the fourth tests review: seven of poison.json's twelve comparisons
        were never shown able to fail; each wired to True passed every test, and the arming reads only the
        booleans). Each input of a poisoned or garbled Source changed alone -- the poisoned view's hash, the
        poisoned yield's, the manifest's, engine_facts, S0's report, the full form-A fit's frozen hash, the garbled
        contract's view or yield hash -- makes exactly its key false (in every poisoned run, or at the top for the
        garbled contract), all_equal false, the invocation a CompletionDefect crash, and e6 refuse after it. The
        control: test_the_proof_is_mandatory's poison, every key true."""
        stand = StandIns(self)
        self.through("fit", stand)
        src, hows = self.src, tuple(epa_rows.POISONS)
        real_load, real_manifest, real_facts, real_s0 = C._load, epa_rows.manifest, epa_rows.engine_facts, epa_fit.s0
        zero = "0" * 64

        def poisoned(source):
            return source.allow_poisoned_tables and not epa_rows._same_path(source.engine_dir, src.engine_dir)

        def garbled(source):
            return not epa_rows._same_path(source.contract_json, src.contract_json)

        marked = set()

        def loading(which, view_fn=None, yield_fn=None):
            def load(name, *, source):
                v, y = real_load(name, source=source)
                if which(source):
                    v = view_fn(v) if view_fn else v
                    y = yield_fn(y) if yield_fn else y
                    marked.add(id(y))
                return v, y
            return mock.patch.object(C, "_load", load)

        def other_view(v):
            cls = type("OtherShaView", (type(v),), {"sha256": property(lambda self: zero)})
            w = copy.copy(v)
            object.__setattr__(w, "__class__", cls)
            return w

        def other_yield(y):
            return dataclasses.replace(y, sha256=zero)

        def manifest(name, *, source):
            m = real_manifest(name, source=source)
            return dataclasses.replace(m, sha256=zero) if poisoned(source) else m

        def facts(name, *, source):
            f = real_facts(name, source=source)
            return dataclasses.replace(f, geometry_notes=str(f.geometry_notes) + " (moved)") if poisoned(source) else f

        def s0(yield_, *, view):
            out = real_s0(yield_, view=view)
            return dataclasses.replace(out, report=dict(out.report, moved=True)) if id(yield_) in marked else out

        def full_fit(name, yield_, *, view, form, start, jobs, dtheta):
            return dataclasses.replace(form_fit(name, form), frozen_sections_sha256=zero)
        runs_ = lambda key: {f"runs.{h}.{key}" for h in hows}        # noqa: E731
        cases = (("view", [loading(poisoned, view_fn=other_view)], runs_("view_equal")),
                 ("yield", [loading(poisoned, yield_fn=other_yield)], runs_("yield_equal")),
                 ("manifest", [mock.patch.object(epa_rows, "manifest", manifest)], runs_("manifest_equal")),
                 ("engine_facts", [mock.patch.object(epa_rows, "engine_facts", facts)], runs_("engine_facts_equal")),
                 ("S0", [loading(poisoned), mock.patch.object(epa_fit, "s0", s0)],
                  runs_("stage0_equal") | runs_("stages.S0")),
                 ("full form A", [mock.patch.object(epa_fit, "fit_form", full_fit)],
                  runs_("full_form_a.frozen_sections_sha256_equal")),
                 ("garbled view", [loading(garbled, view_fn=other_view)], {"garbled_contract_view_equal"}),
                 ("garbled yield", [loading(garbled, yield_fn=other_yield)], {"garbled_contract_yield_equal"}))
        pp = cal(self.src, MAZDA, C.POISON)
        for i, (name, patches, want) in enumerate(cases):
            marked.clear()
            self.assertEqual(self.sub("poison", stand, extra=patches), C.EXIT_CRASH, name)
            self.assertEqual(self.last()["outcome"], "crash: CompletionDefect", name)
            rec = read(pp)
            leaves = dict(_poison_leaves(rec))
            self.assertEqual({k for k, v in leaves.items() if v is False}, want, name)
            self.assertFalse(rec["all_equal"], name)
            if i < len(cases) - 1:
                os.remove(pp)                   # a test-only reset, as drop_last's: the next case runs afresh
                drop_last(self.src)
        # e6 refuses on the crash the run.json records, and, that entry removed, on the proof itself
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("(poison): crash", self.last()["outcome"])
        drop_last(self.src)
        drop_last(self.src)
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("poison.json is not C8's proof", self.last()["outcome"])
        self.assertIn("garbled_contract_yield_equal is not true", self.last()["outcome"])

    def test_a_held_out_cell_that_reaches_a_stage_fails_the_proof(self):
        """A stage made to read one held-out cell through the poisoned Source its yield came from (the copy's
        table, which the seal does not refuse: it holds no real held-out cell): poison writes poison.json with
        the false comparisons and stops (CompletionDefect, a crash); the reference stages, on the real yield,
        read nothing here, since their read of the real tables is the seal's to refuse (the next test). The
        control, the same stage through the unpatched stand-in, passes (test_the_proof_is_mandatory)."""
        stand = StandIns(self)
        self.through("fit", stand)
        held = F.held_rows(self.repo, MAZDA)
        steady = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
        held_sr = held[steady.name][0]
        source_of = {}

        def leaky(name, yield_, *, view, values, jobs, dtheta):
            out = stand_in_poison_stages(name, yield_, view=view, values=values, jobs=jobs, dtheta=dtheta)
            # the leak, through the loader's private readers on the Source the yield was loaded from: a poisoned
            # copy's held-out cell
            src = source_of[id(yield_)]
            v = None
            if src.allow_poisoned_tables:
                for sr, rec in epa_rows._records(steady, epa_rows.table_path(steady, source=src)):
                    if sr == held_sr:
                        v = epa_rows._cells(steady, rec).get("turbine_inlet_press_kpa_abs", "")
            s1 = out["S1"]
            out["S1"] = dataclasses.replace(s1, report=dict(s1.report, leak=v))
            return out

        real_load = C._load

        def tracked_load(name, *, source):
            view, y = real_load(name, source=source)
            source_of[id(y)] = source
            return view, y
        cms = StandIns(self).patches() + [mock.patch.object(C, "_load", tracked_load),
                                          mock.patch.object(epa_fit, "poison_stages", leaky)]
        with contextlib_all(cms):
            code = invoke("poison", MAZDA, self.src, lambda: C.poison(MAZDA, source=self.src, jobs=1,
                                                                       scratch=self.scratch(), full=True))
        self.assertEqual(code, C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        pois = read(cal(self.src, MAZDA, C.POISON))
        self.assertFalse(pois["all_equal"])
        self.assertFalse(all(r["stages"]["S1"] for r in pois["runs"].values()))
        self.assertEqual(self.last()["refused_by_audit"], [], "a read through the poisoned copies is not refused")
        # and the proof that failed holds e6
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)

    def test_a_stage_that_reads_the_repositorys_own_tables_is_refused(self):
        """The isolation review's leak (test_epa_rows.LEAK_SRC's runtime half): a stage that reads the
        repository's own tables -- where the real held-out cells are -- is refused by the audit, which is
        sealed while the reference and the poisoned stages run (refused_by_audit names the table; the
        subcommand crashes at the reference, the first stage; no poison.json). The control: unsealed, the same
        open is no refusal (Audit.test_the_data_folder_and_the_tables_rules)."""
        stand = StandIns(self)
        self.through("fit", stand)
        steady = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
        calls = []

        def leaky(name, yield_, *, view, values, jobs, dtheta):
            calls.append(len(calls))
            out = stand_in_poison_stages(name, yield_, view=view, values=values, jobs=jobs, dtheta=dtheta)
            tot = 0
            for _sr, rec in epa_rows._records(steady, epa_rows.table_path(steady, source=self.src)):
                tot += len(rec)
            return out
        cms = StandIns(self).patches() + [mock.patch.object(epa_fit, "poison_stages", leaky)]
        with contextlib_all(cms):
            code = invoke("poison", MAZDA, self.src, lambda: C.poison(MAZDA, source=self.src, jobs=1,
                                                                       scratch=self.scratch(), full=True))
        self.assertEqual(code, C.EXIT_CRASH)
        inv = self.last()
        self.assertEqual(inv["outcome"], "crash: PermissionError")
        self.assertEqual(len(calls), 1, "the reference stage, sealed, was refused at its first read")
        rel = os.path.relpath(epa_rows.table_path(steady, source=self.src), self.src.root).replace(os.sep, "/")
        self.assertEqual(inv["refused_by_audit"], [rel])
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.POISON)))

    def test_a_poison_that_reads_the_unpoisoned_tables_is_refused(self):
        """A poison whose copies are the tables themselves (poisoned_tables handing back the real Source) would
        compare the calibration with itself: copies_are_not_the_tables is false and the proof fails."""
        stand = StandIns(self)
        self.through("fit", stand)

        def same(name, *, source, dst_dir, how):
            return dataclasses.replace(source, allow_poisoned_tables=True)
        cms = StandIns(self).patches() + [mock.patch.object(epa_rows, "poisoned_tables", same)]
        with contextlib_all(cms):
            code = invoke("poison", MAZDA, self.src, lambda: C.poison(MAZDA, source=self.src, jobs=1,
                                                                       scratch=self.scratch(), full=True))
        self.assertEqual(code, C.EXIT_CRASH)
        pois = read(cal(self.src, MAZDA, C.POISON))
        self.assertEqual({h: r["copies_are_not_the_tables"] for h, r in pois["runs"].items()},
                         {h: False for h in epa_rows.POISONS})

    def test_the_reference_is_the_fits_recorded_stages(self):
        """The poison's reference stages equal the chosen fit_<form>.json's recorded S1 and S3a-S3c: a recorded
        stage edited after the fit (its frozen sections untouched) fails the proof."""
        stand = StandIns(self)
        self.through("fit", stand)
        p = cal(self.src, MAZDA, C.fit_file("A"))
        rec = read(p)
        rec["stages"]["S1"]["report"]["hinge_kpa"] = rec["stages"]["S1"]["report"]["hinge_kpa"] + 0.1
        epa_freeze.write_json_atomic(p, rec)
        self.assertEqual(self.sub("poison", stand), C.EXIT_CRASH)
        pois = read(cal(self.src, MAZDA, C.POISON))
        self.assertEqual(pois["reference_equals_fit"], {"S1": False, "S3a": True, "S3b": True, "S3c": True})


# ======================================================================================================
class Downstream(RunCase):
    """The audit's verdict and the held-out run hold every later step (PLAN.md 5.6; the contract, section 7)."""

    def test_a_fit_the_audit_judged_a_defect_holds_every_later_step(self):
        """The review's experiment: a stand-in ladder that opens a stray file; fit exits EXIT_DEFECT, and
        poison, e6, complete and check refuse, naming the invocation; the defect route clears it (the fit
        re-run from T0 writes a new run.json)."""
        stray = os.path.join(self.repo.root, "stray_notes.txt")
        write(stray, "x\n")
        F.commit_all(self.repo.root, "a stray file")
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.assertEqual(self.sub("fit", StandIns(self, stray=stray)), C.EXIT_DEFECT)
        self.assertEqual(self.last()["outside_allowlist"], ["stray_notes.txt"])
        # (complete and check meet their missing predecessor first; their audit guard is shown by
        # Records.test_e6_complete_and_check, where a mismatch holds the next check)
        for sub in ("poison", "e6"):
            self.assertEqual(self.sub(sub, StandIns(self)), C.EXIT_REFUSED, sub)
            self.assertIn("invocation 2 (fit): audit defect, opened outside the allowlist", self.last()["outcome"])
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        route = epa_freeze.DefectRoute(reason="a stray open", fix_commit=fix)
        self.assertEqual(self.sub("fit", StandIns(self), defect=route), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(self.sub("poison", StandIns(self)), C.EXIT_OK, self.last()["outcome"])

    def test_no_refit_after_the_held_out_run_started(self):
        """results/EPA_VALIDATION/<id>/ holding STARTED (or git log --all holding a path there): t0, fit (the
        defect route included), poison, e6 and complete refuse; check, which the arming runs, does not. The
        control: ARMED.json alone refuses nothing."""
        stand = StandIns(self)
        self.through("e6", stand)
        val = os.path.join(self.repo.root, "results", "EPA_VALIDATION", MAZDA)
        write(os.path.join(val, "ARMED.json"), "{}\n")
        self.assertEqual(self.sub("complete", stand), C.EXIT_OK, self.last()["outcome"])
        write(os.path.join(val, "STARTED"), "{}\n")
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "a fix after the held-out run, the validation's records with it")
        route = epa_freeze.DefectRoute(reason="a refit after the run", fix_commit=fix)
        for sub, kw in (("fit", {"defect": route}), ("t0", {"defect": route}), ("e6", {}), ("poison", {})):
            self.assertEqual(self.sub(sub, stand, **kw), C.EXIT_REFUSED, sub)
            self.assertIn("the held-out run has started", self.last()["outcome"])
        self.assertEqual(self.sub("check", stand), C.EXIT_OK, self.last()["outcome"])
        # STARTED removed from the disk: git log --all still holds it
        os.remove(os.path.join(val, "STARTED"))
        self.assertEqual(self.sub("fit", stand, defect=route), C.EXIT_REFUSED)
        self.assertIn("git log --all holds STARTED", self.last()["outcome"])


# ======================================================================================================
class Guards(RunCase):
    """Each guard of the completion and of check shown able to fire (mistake 12), on a stand-in run."""

    def test_the_neutral_action_identity_and_the_k3_second_knee(self):
        stand = StandIns(self)
        self.through("e6", stand)

        def not_neutral(item):
            out = stand_in_task(item)
            if item[0] == "delivery":
                out = dict(out, identity=dict(out["identity"], max_abs_dlam=1e-12))
            return out

        def second_knee(item):
            out = stand_in_task(item)
            return dataclasses.replace(out, second_knee_identical=False) if item[0] == "k3" else out
        for task in (not_neutral, second_knee):
            self.assertEqual(self.sub("complete", stand, task=task), C.EXIT_CRASH)
            self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
            self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.COMPLETE)))
            # the crash stands in run.json: clear it for the next case, as the defect route would
            inv = read(cal(self.src, MAZDA, C.RUN))
            inv["invocations"] = inv["invocations"][:-1]
            epa_freeze.write_json_atomic(cal(self.src, MAZDA, C.RUN), inv)

    def test_the_retag_and_the_plant_get_builds(self):
        stand = StandIns(self)
        self.through("e6", stand)
        self.assertEqual(self.sub("complete", stand, extra=[mock.patch.object(
            epa_fit, "retag_identity", lambda plant, *, grid, dtheta: False)]), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        inv = read(cal(self.src, MAZDA, C.RUN))
        inv["invocations"] = inv["invocations"][:-1]
        epa_freeze.write_json_atomic(cal(self.src, MAZDA, C.RUN), inv)
        other = epa_fit.perturbed(engines.build_candidate(MAZDA, {**frozen_values("A"), **json.loads(json.dumps(
            epa_fit.PROVISIONAL_COMPLETION))}), record="cycle", field="knock_a", value=1.0)
        self.assertEqual(self.sub("complete", stand, extra=[mock.patch.object(C, "_same_tree", lambda root: True),
                                                           mock.patch.object(engines, "get", lambda n: other)]),
                         C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")

    def test_an_edited_record_stops_the_completion(self):
        """An e6 file whose values moved after e6 wrote it; a derived file whose frozen section moved."""
        stand = StandIns(self)
        self.through("e6", stand)
        p = cal(self.src, MAZDA, C.e6_file("1"))
        good = read(p)
        bad = json.loads(json.dumps(good))
        bad["values"]["cycle"]["burn_base"] += 1.0
        epa_freeze.write_json_atomic(p, bad)
        self.assertEqual(self.sub("complete", stand), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        epa_freeze.write_json_atomic(p, good)
        inv = read(cal(self.src, MAZDA, C.RUN))
        inv["invocations"] = inv["invocations"][:-1]
        epa_freeze.write_json_atomic(cal(self.src, MAZDA, C.RUN), inv)
        d = epa_freeze.derived_path(MAZDA, root=self.repo.root)
        dv = read(d)
        dv["cycle"]["burn_base"] += 1.0
        epa_freeze.write_json_atomic(d, dv)
        # the early guard, which only it catches before a measurement: check_frozen on the derived file, before
        # the first completion task (WP3's second fix of 23 October 2026, on the test review's finding)
        tasks = []

        def counting(item):
            tasks.append(item[0])
            return stand_in_task(item)
        self.assertEqual(self.sub("complete", stand, task=counting), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: FrozenSectionsChanged")
        self.assertEqual(tasks, [], "the edited derived file stopped the completion before any measurement")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.COMPLETE)))

    def test_the_frozen_fits_hash_and_the_row7_scales(self):
        stand = StandIns(self)
        self.through("poison", stand)
        p = cal(self.src, MAZDA, C.fit_file("A"))
        good = read(p)
        bad = json.loads(json.dumps(good))
        bad["values"]["cycle"]["burn_base"] += 1.0
        epa_freeze.write_json_atomic(p, bad)
        self.assertEqual(self.sub("e6", stand), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        epa_freeze.write_json_atomic(p, good)
        inv = read(cal(self.src, MAZDA, C.RUN))
        inv["invocations"] = inv["invocations"][:-1]
        epa_freeze.write_json_atomic(cal(self.src, MAZDA, C.RUN), inv)

        def scales(c):
            for q in c["perturbations_E6"]:
                if q["n"] == 7:
                    q["band"] = "KI 0.80 and 1.20 (synthetic)"
        self.repo = F.rewrite_contract(self.repo, scales)
        self.src = F.synthetic_source(self.repo)
        self.assertEqual(self.sub("e6", stand), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: CompletionDefect")
        # the guard that fired, by its message (run.json records the type alone; WP3's second fix of 23 October
        # 2026, on the test review's finding that any crash passed this check)
        drop_last(self.src)
        with contextlib_all(stand.patches()):
            with self.assertRaisesRegex(C.CompletionDefect, "row 7 scales"):
                C.e6(MAZDA, source=self.src, jobs=1)

    def test_check_compares_the_contract_the_derived_file_and_every_form(self):
        stand = StandIns(self, forms=("A", "A+B"))
        self.through("complete", stand)
        n = len(stand.judge.calls)
        self.assertEqual(self.sub("check", stand), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(stand.judge.calls[n:], ["A", "A+B"], "check recomputes every form fitted")
        ins = read(cal(self.src, MAZDA, C.IN_SAMPLE))
        self.assertEqual((ins["chosen_form"], sorted(ins["forms"])), ("A+B", ["A", "A+B"]))
        fzp = cal(self.src, MAZDA, C.FREEZE)
        fz = read(fzp)
        bad = json.loads(json.dumps(fz))
        bad["contract"]["json_sha_text"] = "0" * 64
        epa_freeze.write_json_atomic(fzp, bad)
        self.assertEqual(self.sub("check", stand), C.EXIT_REFUSED)
        self.assertIn("the contract is not the one freeze.json records", self.last()["outcome"])
        epa_freeze.write_json_atomic(fzp, fz)
        d = epa_freeze.derived_path(MAZDA, root=self.repo.root)
        dv = read(d)
        dv["cycle"]["burn_base"] += 1.0
        epa_freeze.write_json_atomic(d, dv)
        self.assertEqual(self.sub("check", stand), C.EXIT_CRASH)
        self.assertEqual(self.last()["outcome"], "crash: FrozenSectionsChanged")

    def test_check_on_the_defect_route_writes_its_rerun_beside_the_first(self):
        """C11: check --defect writes in_sample_rerun1.json and a defects.json entry, refits nothing; a later
        plain check compares against the re-run file (in_sample.json may then differ; the re-run may not)."""
        stand = StandIns(self)
        self.through("complete", stand)
        write(os.path.join(self.repo.root, "fix_note.txt"), "an epa_stats fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic epa_stats fix")
        route = epa_freeze.DefectRoute(reason="an epa_stats defect (synthetic)", fix_commit=fix)
        n = len([c for c in stand.calls if c[0] in ("ladder", "refit")])
        self.assertEqual(self.sub("check", stand, defect=route), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(len([c for c in stand.calls if c[0] in ("ladder", "refit")]), n, "nothing refitted")
        rr = read(cal(self.src, MAZDA, "in_sample_rerun1.json"))
        self.assertEqual(rr["rerun"]["k"], 1)
        d = read(cal(self.src, MAZDA, epa_freeze.DEFECTS))
        self.assertEqual(d[-1]["previous_run"], "in_sample.json")
        self.assertIn("check --defect", d[-1]["found_by"])
        p = cal(self.src, MAZDA, C.IN_SAMPLE)
        rec = read(p)
        rec["reason"] = "moved"
        epa_freeze.write_json_atomic(p, rec)
        self.assertEqual(self.sub("check", stand), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(self.last()["result"]["compared"], "in_sample_rerun1.json")
        rr["reason"] = "moved"
        epa_freeze.write_json_atomic(cal(self.src, MAZDA, "in_sample_rerun1.json"), rr)
        self.assertEqual(self.sub("check", stand), C.EXIT_MISMATCH)


# ======================================================================================================
def contract_leak(src):
    """The second isolation review's contract leak, at run time (its scratch test_leak_replay.py): the whole
    contract loaded through the loader's private reader and the Source's lower-case attribute, an engine
    block's key list read (test_epa_rows.LEAK_CONTRACT_SRC is its source half)."""
    c = epa_rows._load_json(src.contract_json)
    return sorted(c["engines"][MAZDA])


def table_leak(src):
    """The same review's table leak: the engine's steady table read in-process by linecache, which no open
    rule of the scans named before WP3's second fix."""
    import linecache
    spec = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
    n = len(linecache.getlines(epa_rows.table_path(spec, source=src)))
    linecache.clearcache()
    return n


class Seal(RunCase):
    """The seal (Audit.sealed; WP3's second fix of 23 October 2026, on the second isolation review's must-fix):
    once a subcommand has loaded the view, the yield, engine_facts and the provenance, the contract, the
    engine's own tables and epa_engine.json are refused for the rest of it. The review's leaks, replayed in
    each subcommand's computing phase -- T0, the fit's ladder, the poison's reference stages, e6's refits,
    complete's measurements, check's recompute -- each crash there with the refused path named; the control
    is every other test of this file, whose subcommands load the same files before the seal and pass."""

    def rel(self, path):
        return os.path.relpath(path, self.src.root).replace(os.sep, "/")

    def refused(self, sub, stand, extra, want, **kw):
        code = self.sub(sub, stand, extra=extra, **kw)
        inv = self.last()
        self.assertEqual((code, inv["outcome"]), (C.EXIT_CRASH, "crash: PermissionError"), sub)
        self.assertEqual(inv["refused_by_audit"], [want], sub)

    def leaky_s1(self, leak):
        real = epa_fit.s1_backpressure
        src = self.src

        def s1(rows, *, view):
            st = real(rows, view=view)
            return dataclasses.replace(st, report=dict(st.report, leak=json.dumps(leak(src))))
        return mock.patch.object(epa_fit, "s1_backpressure", s1)

    def test_the_contract_leak_crashes_in_every_computing_phase(self):
        contract = self.rel(self.src.contract_json)
        stand = StandIns(self)

        def leaky_t0(name, yield_, *, view, jobs, dtheta):
            return {"schema": "epa-t0/1", "pass": True, "leak": contract_leak(self.src)}
        self.refused("t0", stand, [mock.patch.object(epa_fit, "run_t0", leaky_t0)], contract)
        # the record of that crash holds the later steps: the defect route clears it, as it would after a real one
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        self.assertEqual(self.sub("t0", StandIns(self), defect=epa_freeze.DefectRoute(reason="a leak", fix_commit=fix)),
                         C.EXIT_OK, self.last()["outcome"])
        self.refused("fit", StandIns(self), [self.leaky_s1(contract_leak)], contract)
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))

    def test_the_leaks_crash_in_poison_e6_complete_and_check(self):
        contract = self.rel(self.src.contract_json)
        stand = StandIns(self)
        self.through("fit", stand)
        self.refused("poison", stand, [self.leaky_s1(contract_leak)], contract)
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.POISON)))
        drop_last(self.src)
        self.assertEqual(self.sub("poison", stand), C.EXIT_OK, self.last()["outcome"])
        real_refit = stand.refit_variant

        def leaky_refit(name, yield_, **kw):
            contract_leak(self.src)
            return real_refit(name, yield_, **kw)
        self.refused("e6", stand, [mock.patch.object(epa_fit, "refit_variant", leaky_refit)], contract)
        drop_last(self.src)
        self.assertEqual(self.sub("e6", stand), C.EXIT_OK, self.last()["outcome"])

        def leaky_task(item):
            if item[0] == "coefficients":
                contract_leak(self.src)
            return stand_in_task(item)
        self.refused("complete", stand, [], contract, task=leaky_task)
        drop_last(self.src)
        self.assertEqual(self.sub("complete", stand), C.EXIT_OK, self.last()["outcome"])
        real_judge = stand.judge

        def leaky_judge(name, fit, yield_, **kw):
            contract_leak(self.src)
            return real_judge(name, fit, yield_, **kw)
        self.refused("check", stand, [mock.patch.object(epa_fit, "in_sample_for", leaky_judge)], contract)

    def test_the_table_leak_crashes_in_the_fit(self):
        """The review's in-process table read (linecache) during the fit's ladder: refused, and since
        linecache catches the PermissionError and returns no lines, the invocation is a defect by the refusal
        alone (EXIT_DEFECT, refused_by_audit naming the table); it passed t0 and fit before the seal."""
        steady = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
        table = self.rel(epa_rows.table_path(steady, source=self.src))
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        code = self.sub("fit", StandIns(self), extra=[self.leaky_s1(table_leak)])
        inv = self.last()
        self.assertEqual(code, C.EXIT_DEFECT, inv["outcome"])
        self.assertIn("an open refused by the audit", inv["outcome"])
        self.assertEqual(sorted(set(inv["refused_by_audit"])), [table])
        # and the next step does not build on it
        self.assertEqual(self.sub("poison", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("an open refused by the audit", self.last()["outcome"])

    # ---------------------------------------------------------------- the seal over child processes
    # The third isolation review's planted leaks (24 October 2026, its scratch iso_leaks_test.py): the contract
    # through `git show`, a held-out table cell through a child interpreter that joins the tables' folder
    # itself. Before WP3's third fix both passed the fit, the poison (all_equal true) and e6; now each crashes
    # where it is planted, the refused command named. The controls: the step-2 code's own git commands run
    # sealed in every other test of this file, and unsealed the same commands are not refused
    # (Audit.test_the_seal_covers_git_and_child_processes).
    def refused_process(self, sub, stand, extra, needle, **kw):
        code = self.sub(sub, stand, extra=extra, **kw)
        inv = self.last()
        self.assertEqual((code, inv["outcome"]), (C.EXIT_CRASH, "crash: PermissionError"), sub)
        self.assertEqual(len(inv["refused_by_audit"]), 1, inv["refused_by_audit"])
        self.assertIn(needle, inv["refused_by_audit"][0])

    def test_a_git_read_of_the_contract_crashes_in_the_fit(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.refused_process("fit", StandIns(self), [self.leaky_s1(git_contract_leak)], "show")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))

    def test_a_git_read_of_the_contract_crashes_in_the_poison(self):
        stand = StandIns(self)
        self.through("fit", stand)
        self.refused_process("poison", stand, [leaky_poison_stages(self.src, git_contract_leak)], "show")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.POISON)))

    def test_a_child_interpreter_crashes_in_the_fit(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.refused_process("fit", StandIns(self), [self.leaky_s1(child_table_leak)], os.path.basename(sys.executable))
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))

    def test_a_child_interpreter_crashes_in_the_poison(self):
        stand = StandIns(self)
        self.through("fit", stand)
        self.refused_process("poison", stand, [leaky_poison_stages(self.src, child_table_leak)],
                             os.path.basename(sys.executable))
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.POISON)))

    # ---------------------------------------------------------------- the sealed git shapes (WP3's fourth fix)
    # The fourth isolation review's planted forms (planted_git_forms): before WP3's fourth fix each passed the fit
    # (exit 0, a held-out cell in fit_A.json's S1 report) and the poison (all_equal true); now each is refused where
    # it is planted, the command named. The controls: the step-2 code's own git runs, sealed
    # (Audit.test_the_step2_codes_own_git_runs_pass_sealed), and every other test of this file.
    def test_a_planted_git_diff_crashes_in_the_fit(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.refused_process("fit", StandIns(self), [self.leaky_s1(planted_git_leak(0))], "--exit-code")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))

    def test_a_planted_glob_pathspec_crashes_in_the_fit(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        self.refused_process("fit", StandIns(self), [self.leaky_s1(planted_git_leak(8))], ":(glob)")
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.FREEZE)))

    def test_the_planted_log_and_config_forms_crash_in_the_poison(self):
        stand = StandIns(self)
        self.through("fit", stand)
        for i, needle in ((3, "-U0"), (6, "-L"), (9, "core.fsmonitor"), (10, "diff.external")):
            self.refused_process("poison", stand, [leaky_poison_stages(self.src, planted_git_leak(i))], needle)
            self.assertFalse(os.path.exists(cal(self.src, MAZDA, C.POISON)))
            drop_last(self.src)
        self.assertEqual(self.sub("poison", stand), C.EXIT_OK, self.last()["outcome"])

    def test_a_worker_refuses_every_planted_git_form_and_reports_it(self):
        """In a pool worker each of the eleven forms is refused, and each refusal the task caught reaches run.json
        (REFUSED_PROCESS_TAG), so the invocation is a defect."""
        item = (self.src.root, self.src.contract_json, self.src.engine_dir)

        def body():
            C.seal_now()
            return {"n": epa_fit.ordered_map(_planted_git_task, [item, item], jobs=2, initializer=epa_fit.WORKER_INIT)}
        code = invoke("fit", MAZDA, self.src, body)
        inv = self.last()
        self.assertEqual(code, C.EXIT_DEFECT, inv["outcome"])
        self.assertEqual(inv["result"], {"n": [11, 11]})
        self.assertEqual(len(inv["refused_by_audit"]), 22, inv["refused_by_audit"])

    def test_an_environment_change_and_a_link_are_refused(self):
        """Sealed, a change of the process's environment (os.putenv: GIT_CONFIG_* would reach the next git) is
        refused; a link made while the audit is active (os.link: another name for a refused file) is refused
        sealed or not. The controls: the same putenv unsealed runs, and no link is left."""
        target = os.path.join(self.src.root, "epa_rows.py")
        link = os.path.join(os.path.dirname(self.src.root), "linked_rows.py")

        def env_sealed():
            C.seal_now()
            os.environ["GIT_CONFIG_COUNT"] = "1"

        def env_unsealed():
            os.environ["EPA_FIX4_PROBE"] = "1"
            return {"set": True}

        def made_link():
            os.link(target, link)
        try:
            code = invoke("fit", MAZDA, self.src, env_sealed)
            inv = self.last()
            self.assertEqual((code, inv["outcome"]), (C.EXIT_CRASH, "crash: PermissionError"))
            self.assertTrue(inv["refused_by_audit"][0].startswith("os.putenv GIT_CONFIG_COUNT"), inv["refused_by_audit"])
            self.assertEqual(invoke("fit", MAZDA, self.src, env_unsealed), C.EXIT_OK, self.last()["outcome"])
            code = invoke("fit", MAZDA, self.src, made_link)
            inv = self.last()
            self.assertEqual((code, inv["outcome"]), (C.EXIT_CRASH, "crash: PermissionError"))
            self.assertTrue(inv["refused_by_audit"][0].startswith("os.link"), inv["refused_by_audit"])
            self.assertFalse(os.path.exists(link))
        finally:
            os.environ.pop("GIT_CONFIG_COUNT", None)
            os.environ.pop("EPA_FIX4_PROBE", None)

    def test_a_worker_that_starts_a_child_is_refused_and_reported(self):
        """In a pool worker (whose audit is sealed outright) a child is refused, and a refusal the task caught still
        reaches run.json (REFUSED_PROCESS_TAG), so the invocation is a defect."""
        def body():
            C.seal_now()
            return {"n": epa_fit.ordered_map(_swallowed_child_task, [1, 2], jobs=2, initializer=epa_fit.WORKER_INIT)}
        code = invoke("fit", MAZDA, self.src, body)
        inv = self.last()
        self.assertEqual(code, C.EXIT_DEFECT, inv["outcome"])
        self.assertTrue(inv["refused_by_audit"])
        self.assertTrue(all(x.startswith("<process> ") for x in inv["refused_by_audit"]), inv["refused_by_audit"])

    def test_a_pool_without_the_audits_initializer_is_refused_while_sealed(self):
        """A spawn pool a stage makes itself, or epa_fit's pool without the audit's initializer, starts children
        with no audit hook: refused while sealed (Audit._spawn_problem). The control: epa_fit's pool with the
        audit's initializer, sealed, runs."""
        import multiprocessing

        def raw():
            C.seal_now()
            with multiprocessing.get_context("spawn").Pool(1) as pool:
                return {"n": pool.map(abs, [1])}

        def bare():
            C.seal_now()
            return {"n": epa_fit.ordered_map(abs, [1, -2], jobs=2, initializer=None)}

        def own():
            C.seal_now()
            return {"n": epa_fit.ordered_map(abs, [1, -2], jobs=2, initializer=epa_fit.WORKER_INIT)}
        for body in (raw, bare):
            code = invoke("fit", MAZDA, self.src, body)
            inv = self.last()
            self.assertEqual((code, inv["outcome"]), (C.EXIT_CRASH, "crash: PermissionError"), body.__name__)
            self.assertTrue(any(x.startswith("CreateProcess") for x in inv["refused_by_audit"]), inv["refused_by_audit"])
        epa_fit.close_pools()
        self.assertEqual(invoke("fit", MAZDA, self.src, own), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(self.last()["result"], {"n": [1, 2]})


EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"        # git's empty tree (`git hash-object -t tree /dev/null`)


def own_git_forms(src):
    """One argv of each of calibrate_epa.SEALED_GIT_SHAPES as the step-2 code runs it (epa_freeze._git with cwd the
    root; epa_rows._git with -C <root> -c core.safecrlf=false): the controls of the sealed shapes."""
    paths = epa_rows.audit_paths(MAZDA, source=src)
    table = paths["table_files"][0]
    rows = ["git", "-C", src.root, "-c", "core.safecrlf=false"]
    return (["git", "rev-parse", "--verify", "HEAD"],
            ["git", "rev-parse", "--path-format=absolute", "--git-dir"],
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            ["git", "status", "--porcelain=v1", "-z", "--no-renames", "--untracked-files=all", "--", "epa_rows.py",
             "engine_specs/b58.toml", "requirements-lock.txt"],
            ["git", "ls-files", "-s", "--", table],
            ["git", "ls-files", "--modified", "--deleted", "--", table],
            ["git", "cat-file", "--batch-check"],
            ["git", "cat-file", "-t", "0" * 40],
            ["git", "cat-file", "blob", "HEAD:epa_rows.py"],
            ["git", "hash-object", "--", epa_freeze.derived_relpath(MAZDA)],
            ["git", "merge-base", "--is-ancestor", "0" * 40, "HEAD"],
            ["git", "log", "--all", "-m", "--no-renames", "--name-only", "--pretty=format:", "--",
             paths["validation"] + "/" + MAZDA + "/"],
            rows + ["show", "HEAD:epa_rows.py"],
            rows + ["merge-base", "--is-ancestor", "0" * 40, "HEAD"],
            rows + ["rev-parse", "HEAD"],
            rows + ["rev-parse", "HEAD:results/EPA_CALIBRATION/" + MAZDA + "/freeze.json"])


def planted_git_forms(src):
    """The fourth isolation review's planted forms (24 October 2026, its scratch iso4/test_iso4_git.py), each of which
    the third fix's subcommand list admitted while sealed: diff --exit-code (which never suppresses a patch), diff
    with --stat, --name-only beside -p or --patch, log with -U0, --unified=0, --binary, -L and --cc, a :(glob)
    pathspec that reaches a table past the folder rule's substring, and the two -c that start a hookless child
    (core.fsmonitor under status, diff.external under diff --ext-diff)."""
    c = os.path.relpath(src.contract_json, src.root).replace(os.sep, "/")
    steady = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
    rel = os.path.relpath(epa_rows.table_path(steady, source=src), src.root).replace(os.sep, "/")
    eng = os.path.relpath(src.engine_dir, src.root).replace(os.sep, "/")
    glob = ":(glob)" + rel.replace(eng + "/", eng[:-1] + "?/")          # the folder's last letter a glob
    py = sys.executable.replace("\\", "/")
    return (["git", "diff", "--exit-code", EMPTY_TREE, "HEAD", "--", c],
            ["git", "diff", "--stat", "-p", EMPTY_TREE, "HEAD", "--", c],
            ["git", "diff", "--name-only", "--patch", EMPTY_TREE, "HEAD", "--", c],
            ["git", "log", "-U0", "--", c], ["git", "log", "--unified=0", "--", c], ["git", "log", "--binary", "--", c],
            ["git", "log", "-L", "1,9:" + c], ["git", "log", "--cc", "--", c],
            ["git", "diff", "--exit-code", EMPTY_TREE, "HEAD", "--", glob],
            ["git", "-c", f"core.fsmonitor={py} -I -c print(1)", "status", "--porcelain"],
            ["git", "-c", f"diff.external={py}", "diff", "--ext-diff", "--exit-code"])


def planted_git_leak(i):
    """A leak through planted_git_forms(src)[i]: its output's length (the review's leaks parsed the contract or a
    held-out cell out of it)."""
    def leak(src):
        return len(subprocess.run(planted_git_forms(src)[i], cwd=src.root, capture_output=True).stdout)
    return leak


def _planted_git_task(item):
    """A pool task that tries every planted form and catches each refusal: the worker's audit must report each."""
    root, contract_json, engine_dir = item
    src = types.SimpleNamespace(root=root, contract_json=contract_json, engine_dir=engine_dir)
    n = 0
    for argv in planted_git_forms(src):
        try:
            subprocess.run(argv, cwd=root, capture_output=True)
        except PermissionError:
            n += 1
    return n


def git_contract_leak(src):
    """The third isolation review's leak (a): the contract through `git show HEAD:<contract>`, never an open."""
    rel = os.path.relpath(src.contract_json, src.root).replace(os.sep, "/")
    out = subprocess.run(["git", "show", "HEAD:" + rel], cwd=src.root, capture_output=True).stdout
    return len(json.loads(out)["engines"][MAZDA]["held_out_rows"])


def child_table_leak(src):
    """The same review's leak (b): the engine's steady table read by a child interpreter (which has no audit
    hook), its path joined in the child so that no argv names the tables' folder."""
    steady = next(t for t in epa_rows.TABLES[MAZDA] if t.role == "steady")
    code = ("import os, sys\np = os.path.join(sys.argv[1], 'da' + 'ta', 'eng' + 'ines', sys.argv[2], sys.argv[3])\n"
            "print(len(open(p, 'rb').read()))\n")
    out = subprocess.run([sys.executable, "-I", "-c", code, src.root, MAZDA, os.path.basename(
        epa_rows.table_path(steady, source=src))], capture_output=True, text=True)
    return out.stdout.strip()


def leaky_poison_stages(src, leak):
    """epa_fit.poison_stages replaced by the stand-in with `leak` planted in its S1 report (the reference stages
    and the poisoned ones alike)."""
    def stages(name, yield_, *, view, values, jobs, dtheta):
        out = stand_in_poison_stages(name, yield_, view=view, values=values, jobs=jobs, dtheta=dtheta)
        out["S1"] = dataclasses.replace(out["S1"], report=dict(out["S1"].report, leak=json.dumps(leak(src))))
        return out
    return mock.patch.object(epa_fit, "poison_stages", stages)


def _swallowed_child_task(_item):
    """A pool task that starts a child interpreter and catches the refusal: the worker's audit must still report it."""
    try:
        subprocess.run([sys.executable, "-I", "-c", "print(1)"], capture_output=True)
        return 0
    except PermissionError:
        return -1


def _poison_leaves(rec):
    """poison.json's comparison leaves as (dotted path, value): every boolean under runs, reference_equals_fit and the
    garbled contract's two keys."""
    def walk(obj, pre):
        if isinstance(obj, dict):
            for k, v in obj.items():
                yield from walk(v, f"{pre}.{k}" if pre else str(k))
        elif isinstance(obj, bool):
            yield pre, obj
    yield from walk({"runs": rec["runs"], "reference_equals_fit": rec["reference_equals_fit"]}, "")
    for key in ("garbled_contract_view_equal", "garbled_contract_yield_equal"):
        yield key, rec[key]


def drop_last(src):
    """Remove run.json's last invocation, as the defect route would clear a crash (so one test can show the
    next step's refusal): a test-only edit."""
    inv = read(cal(src, MAZDA, C.RUN))
    inv["invocations"] = inv["invocations"][:-1]
    epa_freeze.write_json_atomic(cal(src, MAZDA, C.RUN), inv)


class GateAfterStart(RunCase):
    """The gate's second half (WP3's second fix of 23 October 2026, on the test review's finding that no test
    covered it): while the rule stands, t0 with EPA_RUN1_GO naming the engine writes STARTED, and fit then
    runs without the switch, since STARTED exists; the control: with STARTED removed, fit waits."""
    rule = RULE

    def test_t0_with_the_switch_then_fit_without_it(self):
        with mock.patch.dict(os.environ, {C.RUN1_GO: MAZDA}):
            self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK, self.last()["outcome"])
        self.assertNotIn(C.RUN1_GO, os.environ)
        self.assertEqual(read(cal(self.src, MAZDA, C.STARTED))["run1_gate"], {"rule": RULE, "switch": MAZDA})
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(self.last()["run1_gate"]["gated"], False)
        os.remove(cal(self.src, MAZDA, C.STARTED))
        with contextlib_all(StandIns(self).patches()):
            with self.assertRaises(C.Run1Waits):
                C.fit(MAZDA, source=self.src, jobs=1, defect=epa_freeze.DefectRoute(reason="x", fix_commit="0" * 40))


class RunOnceAndTheCode(RunCase):
    """Run 1's other proofs, each with its control (WP3's second fix of 23 October 2026): the run-once marker
    in the work tree's git directory holds every refit (the isolation review's must-fix); fit does not build
    on a T0 the audit judged a defect (the test review's), on code or a plant T0 did not run on, or in another
    environment (the fit review's)."""

    def test_a_run_once_marker_holds_every_refit(self):
        stand = StandIns(self)
        self.through("e6", stand)
        marker = epa_freeze.run_marker_path("started", MAZDA, "a" * 40, root=self.repo.root)
        epa_freeze.write_json_atomic(marker, {"engine": MAZDA})
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "a fix after the held-out run")
        route = epa_freeze.DefectRoute(reason="a refit after the run", fix_commit=fix)
        for sub, kw in (("complete", {}), ("fit", {"defect": route}), ("t0", {"defect": route}), ("e6", {}),
                        ("poison", {})):
            self.assertEqual(self.sub(sub, stand, **kw), C.EXIT_REFUSED, sub)
            self.assertIn("git directory holds", self.last()["outcome"], sub)
        os.remove(marker)
        self.assertEqual(self.sub("complete", stand), C.EXIT_OK, self.last()["outcome"])

    def test_fit_refuses_a_t0_the_audit_judged_a_defect(self):
        """The review's probe (its scratch probe_fit_after_defective_t0.py): a stand-in T0 that opens a stray
        file exits EXIT_DEFECT, and fit refuses naming that invocation; the defect route clears it."""
        stray = os.path.join(self.repo.root, "stray_notes.txt")
        write(stray, "x\n")
        F.commit_all(self.repo.root, "a stray file")
        stand = StandIns(self)

        def t0_opens(name, yield_, *, view, jobs, dtheta):
            with open(stray, encoding="utf-8") as fh:
                fh.read()
            return {"schema": "epa-t0/1", "pass": True, "stand_in": True}
        self.assertEqual(self.sub("t0", stand, extra=[mock.patch.object(epa_fit, "run_t0", t0_opens)]), C.EXIT_DEFECT)
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("invocation 1 (t0): audit defect", self.last()["outcome"])
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        self.assertEqual(self.sub("fit", StandIns(self), defect=epa_freeze.DefectRoute(reason="a stray open",
                                                                                     fix_commit=fix)),
                         C.EXIT_OK, self.last()["outcome"])

    def test_fit_needs_the_code_and_the_environment_t0_ran_on(self):
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK)
        # a step-2 module edited and committed between t0 and fit
        with open(os.path.join(self.repo.root, "epa_stats.py"), "a", encoding="utf-8") as fh:
            fh.write("\n# a committed edit after T0\n")
        F.commit_all(self.repo.root, "an edit after T0")
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("not the code t0.json's T0 ran on", self.last()["outcome"])
        # the control: the defect route re-runs T0 on that code, and the fit goes
        head = epa_freeze.git_head(root=self.repo.root)
        route = epa_freeze.DefectRoute(reason="the code moved after T0", fix_commit=head)
        self.assertEqual(self.sub("fit", StandIns(self), defect=route), C.EXIT_OK, self.last()["outcome"])
        # another SciPy than the freeze's: every later step refuses; the control is every through() above
        real = epa_freeze.versions

        def other():
            return dict(real(), scipy="0.0.0")
        self.assertEqual(self.sub("poison", StandIns(self), extra=[mock.patch.object(epa_freeze, "versions", other)]),
                         C.EXIT_REFUSED)
        self.assertIn("the environment is not Run 1's", self.last()["outcome"])
        self.assertEqual(self.sub("poison", StandIns(self)), C.EXIT_OK, self.last()["outcome"])


def _plant_spec(name):
    """One of the engine's own spec files (fingerprint.plant_files' tail), repository-relative."""
    return next(f for f in epa_freeze.plant_files(name) if f.endswith(".toml"))


class TheFreezesCodeAndPlant(RunCase):
    """WP3's third fix of 24 October 2026, on the Run 1 review's findings, each with its control: poison, e6 and
    complete run on the step-2 code and the plant freeze.json records, committed and clean; t0 and fit on a
    committed plant; a plain t0 does not re-run over a crash; t0 --defect is refused after a fit; a scratch folder
    inside the work tree is refused; an interrupted subcommand leaves its crash in run.json; OpenBLAS's own
    thread variable is checked."""

    def edit(self, rel, text="\n# an uncommitted edit (synthetic)\n"):
        p = os.path.join(self.repo.root, *rel.split("/"))
        with open(p, encoding="utf-8", newline="") as fh:
            old = fh.read()
        with open(p, "a", encoding="utf-8", newline="") as fh:
            fh.write(text)
        return p, old

    def restore(self, p, old):
        with open(p, "w", encoding="utf-8", newline="") as fh:
            fh.write(old)

    def test_poison_e6_and_complete_run_on_the_freezes_code_and_plant(self):
        stand = StandIns(self)
        self.through("fit", stand)
        # an uncommitted plant edit: refused, named (the control: the same step after the edit is undone)
        p, old = self.edit(_plant_spec(MAZDA))
        self.assertEqual(self.sub("poison", stand), C.EXIT_REFUSED)
        self.assertIn("the plant's code and specs are not committed and clean", self.last()["outcome"])
        self.restore(p, old)
        self.assertEqual(self.sub("poison", stand), C.EXIT_OK, self.last()["outcome"])
        # an uncommitted step-2 edit during e6
        p, old = self.edit("k3_knee.py")
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("the step-2 code is not committed and clean", self.last()["outcome"])
        self.restore(p, old)
        # a committed step-2 edit after the freeze: not freeze.json's code (the defect route re-runs from T0)
        p, old = self.edit("epa_coefficients.py", "\n# a committed edit after the freeze (synthetic)\n")
        F.commit_all(self.repo.root, "an edit after the freeze")
        self.assertEqual(self.sub("e6", stand), C.EXIT_REFUSED)
        self.assertIn("not the code freeze.json records (epa_coefficients.py)", self.last()["outcome"])
        self.restore(p, old)
        F.commit_all(self.repo.root, "the edit undone")
        self.assertEqual(self.sub("e6", stand), C.EXIT_OK, self.last()["outcome"])
        # complete, on freeze.json's plant_sha (the running code's, fingerprint.plant_files): a freeze.json whose
        # plant_sha is another is refused; its own passes (the rest of this file)
        fp = cal(self.src, MAZDA, C.FREEZE)
        fz = read(fp)
        with open(fp, "rb") as fh:
            raw = fh.read()
        epa_freeze.write_json_atomic(fp, dict(fz, plant={"plant_sha": "0" * 64}))
        self.assertEqual(self.sub("complete", stand), C.EXIT_REFUSED)
        self.assertIn("(plant_sha) are not those freeze.json records", self.last()["outcome"])
        with open(fp, "wb") as fh:
            fh.write(raw)
        self.assertEqual(self.sub("complete", stand), C.EXIT_OK, self.last()["outcome"])
        for rel in ("poison.json", "e6/row1.json", "complete.json"):
            prov = read(cal(self.src, MAZDA, rel))["provenance"]
            self.assertEqual(prov["code_sha_text"], fz["code"], rel)
            self.assertEqual(prov["plant_sha"], fz["plant"]["plant_sha"], rel)

    def test_the_run1_inputs_outside_the_code_and_the_plant_are_bound(self):
        """WP3's fourth fix of 24 October 2026 (the fourth Run 1 review's blocking item): the B58's engine spec (the
        fit reads it), evaluate.py (the completion reads it) and requirements-lock.txt (the version authority) are
        hashed with the step-2 code (epa_freeze.RUN1_INPUTS). An uncommitted edit of engine_specs/b58.toml refuses
        fit, naming it; a committed edit of evaluate.py after the freeze refuses complete, naming it; each record
        carries all three. The controls: the same step after each edit is undone runs."""
        stand = StandIns(self)
        self.assertEqual(self.sub("t0", stand), C.EXIT_OK, self.last()["outcome"])
        p, old = self.edit("engine_specs/b58.toml")
        self.assertEqual(self.sub("fit", stand), C.EXIT_REFUSED)
        self.assertIn("the step-2 code is not committed and clean (engine_specs/b58.toml)", self.last()["outcome"])
        self.restore(p, old)
        for sub in ("fit", "poison", "e6"):
            self.assertEqual(self.sub(sub, stand), C.EXIT_OK, (sub, self.last()["outcome"]))
        fz = read(cal(self.src, MAZDA, C.FREEZE))
        self.assertTrue(set(epa_freeze.RUN1_INPUTS) <= set(fz["code"]), sorted(fz["code"]))
        p, old = self.edit("evaluate.py", "\n# a committed edit after the freeze (synthetic)\n")
        F.commit_all(self.repo.root, "an edit of evaluate.py after the freeze")
        self.assertEqual(self.sub("complete", stand), C.EXIT_REFUSED)
        self.assertIn("not the code freeze.json records (evaluate.py)", self.last()["outcome"])
        self.restore(p, old)
        F.commit_all(self.repo.root, "the edit undone")
        self.assertEqual(self.sub("complete", stand), C.EXIT_OK, self.last()["outcome"])

    def test_t0_and_fit_need_a_committed_plant(self):
        p, old = self.edit(_plant_spec(MAZDA))
        for call in (lambda: C.t0(MAZDA, source=self.src, jobs=1, defect=None),
                     lambda: C.fit(MAZDA, source=self.src, jobs=1, defect=None)):
            with self.assertRaises(C.Refusal) as cm:
                with contextlib_all(StandIns(self).patches()):
                    call()
            self.assertIn("the plant's code and specs are not committed and clean", str(cm.exception))
        self.restore(p, old)
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK, self.last()["outcome"])

    def test_a_plain_t0_does_not_rerun_over_a_crash_and_its_defect_route_stops_after_a_fit(self):
        def crashing(name, yield_, *, view, jobs, dtheta):
            raise RuntimeError("a stand-in T0 that crashes")
        self.assertEqual(self.sub("t0", StandIns(self), extra=[mock.patch.object(epa_fit, "run_t0", crashing)]),
                         C.EXIT_CRASH)
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_REFUSED)
        self.assertIn("invocation 1 (t0): crash", self.last()["outcome"])
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        route = epa_freeze.DefectRoute(reason="T0 crashed (synthetic)", fix_commit=fix)
        self.assertEqual(self.sub("t0", StandIns(self), defect=route), C.EXIT_OK, self.last()["outcome"])
        self.assertEqual(self.sub("fit", StandIns(self)), C.EXIT_OK, self.last()["outcome"])
        # after a fit, t0 --defect would move the folder and leave the derived file: refused, fit --defect named
        self.assertEqual(self.sub("t0", StandIns(self), defect=route), C.EXIT_REFUSED)
        self.assertIn("fit --defect", self.last()["outcome"])
        self.assertTrue(os.path.exists(cal(self.src, MAZDA, C.FREEZE)), "nothing was moved")
        self.assertEqual(self.sub("fit", StandIns(self), defect=route), C.EXIT_OK, self.last()["outcome"])

    def test_a_scratch_folder_inside_the_work_tree_is_refused(self):
        stand = StandIns(self)
        self.through("fit", stand)
        inside = os.path.join(self.repo.root, "poison_scratch")
        with contextlib_all(stand.patches()):
            code = invoke("poison", MAZDA, self.src, lambda: C.poison(MAZDA, source=self.src, jobs=1, scratch=inside,
                                                                       full=True), scratch=inside)
        self.assertEqual(code, C.EXIT_REFUSED)
        self.assertIn("inside the work tree", self.last()["outcome"])
        self.assertFalse(os.path.exists(inside))
        self.assertIsNone(C.scratch_problem(self.scratch(), self.repo.root))
        # dry-load writes its run.json into its scratch folder, so inside the tree it writes nothing at all
        out = os.path.join(self.repo.root, "dry_scratch")
        with contextlib_all(stand.patches()):
            code = invoke("dry-load", MAZDA, self.src, lambda: C.dry_load(MAZDA, source=self.src, out=out),
                          scratch=out)
        self.assertEqual(code, C.EXIT_REFUSED)
        self.assertFalse(os.path.exists(out))

    def test_an_interrupted_subcommand_leaves_its_crash_in_run_json(self):
        def body():
            raise KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            invoke("t0", MAZDA, self.src, body)
        self.assertEqual(self.last()["outcome"], "crash: KeyboardInterrupt")
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_REFUSED, "the crash holds a plain t0")

    def test_openblas_threads_are_one(self):
        env = dict(OMP_NUM_THREADS="1", MKL_NUM_THREADS="1", OPENBLAS_NUM_THREADS="4")
        with mock.patch.dict(os.environ, env):
            with self.assertRaises(SystemExit) as cm:
                C._prelude(["t0", "--engine", MAZDA, "--jobs", "1"])
            self.assertEqual(cm.exception.code, C.EXIT_REFUSED)
            with self.assertRaises(epa_fit.FitDefect):
                epa_fit.assert_one_blas_thread()
        for value in ("1", None):
            e = dict(env, OPENBLAS_NUM_THREADS=value) if value else {k: v for k, v in env.items()
                                                                    if k != "OPENBLAS_NUM_THREADS"}
            with mock.patch.dict(os.environ, e, clear=False):
                if value is None:
                    os.environ.pop("OPENBLAS_NUM_THREADS", None)
                self.assertIsNone(epa_fit.assert_one_blas_thread())


# ======================================================================================================
SLOW = "CALIBRATE_EPA_SLOW"


_POOL_KILLED = r"""
import json, os, sys, time
here, info, mode = sys.argv[1:4]
sys.path.insert(0, here)
import calibrate_epa as C, epa_fit, epa_rows
src = epa_rows.Source(**json.loads(info))
if mode == "close":                    # the control: the pools closed and joined as before the fix, never terminated
    real = epa_fit.close_pools
    epa_fit.close_pools = lambda *, terminate=False: real(terminate=False)
def body():
    pool = epa_fit._pool(2, epa_fit.WORKER_INIT)
    pool.apply_async(os._exit, (1,))   # a worker that dies mid-task: the task never completes
    time.sleep(5)
    raise KeyboardInterrupt            # the parent interrupted while it waits
try:
    C.invoke("t0", "mazda_25t", source=src, argv=["t0"], body=body, scratch=None, audit=None)
except KeyboardInterrupt:
    print("INTERRUPTED", flush=True)
os._exit(0)
"""


class RunOneRecovery(RunCase):
    """WP3's fourth fix of 24 October 2026, on the fourth Run 1 review's findings, each with its control: an
    interrupted body with a pool whose worker died still writes its crash entry (the pools are terminated, not
    joined); a loader guard that stops is a refusal, not an audited crash; fit --defect checks the environment
    before it moves the run."""

    def _kill_tree(self, p):
        if os.name == "nt":
            subprocess.run(["taskkill", "/T", "/F", "/PID", str(p.pid)], capture_output=True)
        else:
            p.kill()
        p.communicate()

    def test_an_interrupt_with_a_dead_worker_still_writes_its_crash(self):
        """At --jobs > 1 a worker that died mid-task left Pool.close() then join() waiting forever, so the interrupted
        subcommand never wrote run.json (the review's r1lens/pool_hang.py). Now the pools are terminated when the
        body did not end ok: the command returns, its run.json entry reads "crash: KeyboardInterrupt". The control:
        with the pools closed and joined as before, the same process does not return within 45 s."""
        info = json.dumps(dataclasses.asdict(self.src))
        p = subprocess.Popen([sys.executable, "-B", "-c", _POOL_KILLED, HERE, info, "terminate"], cwd=self.repo.root,
                             env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            out, err = p.communicate(timeout=300)
        except subprocess.TimeoutExpired:
            self._kill_tree(p)
            self.fail("the interrupted invocation did not return: its pool was not terminated")
        self.assertIn("INTERRUPTED", out, err[-1500:])
        self.assertEqual(self.last()["outcome"], "crash: KeyboardInterrupt")
        q = subprocess.Popen([sys.executable, "-B", "-c", _POOL_KILLED, HERE, info, "close"], cwd=self.repo.root,
                             env=ENV, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            q.communicate(timeout=45)
            hung = False
        except subprocess.TimeoutExpired:
            hung = True
            self._kill_tree(q)
        self.assertTrue(hung, "the control: closed and joined, the pool with a dead worker would have returned")
        self.assertEqual(len(runs(self.src, MAZDA)), 1, "the hung control wrote no entry")

    def test_a_loader_guard_that_stops_is_a_refusal(self):
        """A LoaderStop raised in a subcommand (a contract, table or header guard) is recorded as "refused: LoaderStop
        at <where>", its message (which can name rows) neither recorded nor printed, and the next plain t0 is not held
        by it. The control: another exception there is a crash, which holds a plain t0
        (test_a_plain_t0_does_not_rerun_over_a_crash_and_its_defect_route_stops_after_a_fit)."""
        def stop(name, *, source):
            raise epa_rows.LoaderStop("synthetic: mazda_25t/steady row 7 is held out twice")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = self.sub("t0", StandIns(self), extra=[mock.patch.object(C, "_load", stop)])
        self.assertEqual(code, C.EXIT_REFUSED)
        out = self.last()["outcome"]
        self.assertTrue(out.startswith("refused: LoaderStop at "), out)
        self.assertNotIn("row 7", out)
        self.assertNotIn("row 7", buf.getvalue())
        self.assertEqual(self.sub("t0", StandIns(self)), C.EXIT_OK, self.last()["outcome"])

    def test_fit_defect_checks_the_environment_before_it_moves_the_run(self):
        """fit --defect on the wrong NumPy or SciPy refuses before it moves the run to defect_<k>/ and appends to
        defects.json (it re-ran T0 first before the fix). The control: on the right environment the same route moves
        the run."""
        stand = StandIns(self)
        self.through("fit", stand)
        write(os.path.join(self.repo.root, "fix_note.txt"), "the synthetic fix\n")
        fix = F.commit_all(self.repo.root, "the synthetic fix")
        route = epa_freeze.DefectRoute(reason="a synthetic defect", fix_commit=fix)
        wrong = mock.patch.object(epa_freeze, "version_problems", lambda recorded: ["numpy 0.0 is not the lock's"])
        n_calls = len(stand.calls)
        self.assertEqual(self.sub("fit", stand, defect=route, extra=[wrong]), C.EXIT_REFUSED)
        self.assertIn("the environment is not Run 1's", self.last()["outcome"])
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, "defect_1")))
        self.assertFalse(os.path.exists(cal(self.src, MAZDA, "defects.json")))
        self.assertTrue(os.path.exists(cal(self.src, MAZDA, C.FREEZE)), "nothing was moved")
        self.assertEqual(len(stand.calls), n_calls, "neither T0 nor the ladder ran again")
        self.assertEqual(self.sub("fit", stand, defect=route), C.EXIT_OK, self.last()["outcome"])
        self.assertTrue(os.path.isdir(cal(self.src, MAZDA, "defect_1")))


@unittest.skipUnless(os.environ.get(SLOW, "").isdigit(), f"set {SLOW}=<jobs> to run Run 1 for real on synthetic "
                     "tables (about 20 minutes at 12 jobs)")
class WholeRun1OnSyntheticTables(RunCase):
    """Every subcommand for real but T0 -- fit (the whole per-engine ladder), poison (the full form-A fit
    included, mandatory on the Mazda), e6, complete (DERIVING_PARAMS=1) and check -- on the synthetic Mazda's
    tables in a temporary repository, the synthetic contract's lambda clip floor set to the spec's typed one
    and its E6 bands written in the contract's format, the pins pinned with synthetic values: each exits 0
    with nothing opened outside its allowlist, the poison moves nothing, the completion's F7 control, K3
    second knee and identity hold, and check gives the in-sample stage back byte for byte. T0 is a stand-in
    passing (its four ladders would take hours; T0's own machinery is test_epa_fit.T0's). Synthetic data: no
    figure of it is a figure of the project."""

    def test_run1_end_to_end(self):
        jobs = int(os.environ[SLOW])
        scratch = self.scratch()
        t0_stand = mock.patch.object(epa_fit, "run_t0", lambda name, y, *, view, jobs, dtheta: {
            "schema": "epa-t0/1", "pass": True, "stand_in": True})
        steps = [("t0", lambda: C.t0(MAZDA, source=self.src, jobs=jobs, defect=None), None),
                 ("fit", lambda: C.fit(MAZDA, source=self.src, jobs=jobs, defect=None), None),
                 ("poison", lambda: C.poison(MAZDA, source=self.src, jobs=jobs, scratch=scratch, full=True), scratch),
                 ("e6", lambda: C.e6(MAZDA, source=self.src, jobs=jobs), None),
                 ("complete", lambda: C.complete(MAZDA, source=self.src, jobs=jobs), None),
                 ("check", lambda: C.check(MAZDA, source=self.src, jobs=jobs, defect=None), None)]
        for sub, body, scr in steps:
            env = {"DERIVING_PARAMS": "1"} if sub == "complete" else {}
            with F.pinned_terms(), t0_stand, mock.patch.dict(os.environ, env):
                code = invoke(sub, MAZDA, self.src, body, scratch=scr)
            inv = runs(self.src, MAZDA)[-1]
            self.assertEqual((code, inv["outside_allowlist"]), (C.EXIT_OK, []), (sub, inv["outcome"]))
        comp = read(cal(self.src, MAZDA, C.COMPLETE))
        self.assertTrue(comp["f7_table_and_floor_identical_under_two_knees"])
        self.assertTrue(comp["k3"]["second_knee_identical"])
        self.assertEqual(comp["delivery"]["identity"]["contacts_lam"] + comp["delivery"]["identity"]["contacts_spark"], 0)
        pois = read(cal(self.src, MAZDA, C.POISON))
        self.assertTrue(pois["all_equal"])
        self.assertEqual(read(cal(self.src, MAZDA, C.FREEZE))["frozen_sections_sha256"], comp["frozen_sections_sha256"])


# The rehearsal's synthetic R, by gating row (RealT0OnSyntheticTables; WP3's fourth fix of 24 October 2026): the
# synthetic view test_epa_stats types for its hand answers (its R_TABLE), in place of the fixture's, which lie below
# the in-sample noise at T0_NOISE (E1a and E2a at 0.05 %, E4b at 0.2 %, D1 at 0.08 %); E1a, E2a and E3a as PLAN.md 5.1
# states S4's and S2's residual scales (1.9 %, 4.0 %, 10 K). Synthetic; not read from the contract.
T0_REHEARSAL_R = {"E1a": 1.9, "E2a": 4.0, "E3a": 10.0, "E4a": 10.0, "L0": 10.0, "D1": 16.6, "E4b": 16.6, "L1": 9.9,
                  "E8": 16.6}


@unittest.skipUnless(os.environ.get(SLOW, "").isdigit(), f"set {SLOW}=<jobs> to run the real T0 on synthetic tables")
class RealT0OnSyntheticTables(RunCase):
    """t0 with the real epa_fit.run_t0 -- its four ladders, the in-sample stage at every form, the judge -- on
    the synthetic Mazda's tables in a temporary repository (WP3's second fix of 23 October 2026, on the test
    review's finding that the first real T0 would otherwise run at Run 1): t0.json written with its schema,
    a boolean pass and its provenance, nothing opened outside the allowlist, nothing refused, and its time in
    run.json. Whether T0 passes on synthetic tables is reported, not asserted (epa_fit.T0_STOP_Z's note).
    The synthetic contract's R are set to T0_REHEARSAL_R (WP3's fourth fix of 24 October 2026, on the fourth Run 1
    review's finding): the fixture's lie below the in-sample noise at T0_NOISE -- D1, a mean of |delta_D|, has a
    floor of about 0.8 sigma (0.49 % at the truth itself), above the fixture's 0.08 %, and E1a's 0.05 % failed
    seeds 2 and 3 at their truth's form once D1's was raised -- and S4's residual scales are E1a's and E3a's R
    (epa_fit._scales; PLAN.md 5.1), so the fixture's put efficiency's residuals 76 times larger against TIT's than
    PLAN.md 5.1's scales do: the rehearsal failed whatever the fit did. Each seed's verdict and chi-square are
    printed, so the run shows what T0 would decide; with T0_REHEARSAL_R, at 9 jobs on 24 October 2026, T0 passed
    (WP3_INTERFACES.md 14)."""

    def test_t0_end_to_end(self):
        jobs = int(os.environ[SLOW])

        def rehearsal_r(c):
            for t in c["thresholds"]:
                if t.get("engine") == MAZDA and t.get("row") in T0_REHEARSAL_R:
                    t["R"] = T0_REHEARSAL_R[t["row"]]
        self.repo = F.rewrite_contract(self.repo, rehearsal_r)
        self.src = F.synthetic_source(self.repo)
        got = epa_rows.calibration_contract(MAZDA, source=self.src).R
        self.assertEqual({k: got[k][0] for k in T0_REHEARSAL_R if k in got},
                         {k: v for k, v in T0_REHEARSAL_R.items() if k in got})
        with F.pinned_terms():
            code = invoke("t0", MAZDA, self.src, lambda: C.t0(MAZDA, source=self.src, jobs=jobs, defect=None))
        inv = runs(self.src, MAZDA)[-1]
        self.assertEqual((code, inv["outside_allowlist"], inv["refused_by_audit"]), (C.EXIT_OK, [], []), inv["outcome"])
        rec = read(cal(self.src, MAZDA, C.T0))
        self.assertEqual(rec["schema"], "epa-t0/1")
        self.assertIsInstance(rec["pass"], bool)
        self.assertIn("code_sha_text", rec["provenance"])
        self.assertGreater(inv["seconds"], 0.0)
        for sd in rec["seeds"]:
            print(f"T0 seed {sd['seed']}: ok {sd['ok']}, stops at {sd['ladder_stops_at']} (expected "
                  f"{sd['expected_form']}), chi2 {sd['chi2']['value']:.2f} on {sd['chi2']['dof']} (99 % upper "
                  f"{sd['chi2']['quantile_99_hi']:.2f})")
        print(f"T0 pass {rec['pass']}; out-of-form detected {rec.get('out_of_form_detected')}")


# ======================================================================================================
class Pieces(F.Guarded):
    """The completion's pure pieces, by hand: the slider-crank inversion, the valve brackets, the probe
    sizes, the finiteness assertion, the other octane, and the copy of d3_rows' read list."""

    def test_the_slider_crank_inverts(self):
        import math
        stroke, rod = 0.0894, 0.14
        for deg in (30.0, 90.0, 140.0):
            t = math.radians(deg)
            r = stroke / 2.0
            x = r * (1.0 - math.cos(t)) + rod - math.sqrt(rod * rod - (r * math.sin(t)) ** 2)
            self.assertAlmostEqual(C.slider_crank_angle(x, stroke_m=stroke, conrod_m=rod), deg, places=9)
        self.assertIsNone(C.slider_crank_angle(stroke * 1.01, stroke_m=stroke, conrod_m=rod))

    def test_valve_brackets(self):
        geo = engines.Geometry(**engines.read_spec("honda_l15b7")["geometry"])     # the Honda's typed geometry
        import math

        def x(deg):
            t, r, rod = math.radians(deg), geo.stroke / 2.0, geo.conrod
            return 1000.0 * (r * (1.0 - math.cos(t)) + rod - math.sqrt(rod * rod - (r * math.sin(t)) ** 2))
        rows = [F.point_row(eff_compression_stroke_mm=x(a), eff_expansion_stroke_mm=x(b))
                for a, b in ((120.0, 130.0), (130.0, 140.0), (125.0, 135.0))]
        b = C.valve_brackets(rows, geometry=geo)
        self.assertEqual(b["ivc_deg"]["rows"], 3)
        self.assertAlmostEqual(b["ivc_deg"]["bracket"][0], -130.0, places=6)
        self.assertAlmostEqual(b["ivc_deg"]["bracket"][1], -120.0, places=6)
        self.assertAlmostEqual(b["evo_deg"]["bracket"][1], 140.0, places=6)
        self.assertEqual(b["ivc_deg"]["method"], "strokes")
        # the control: rows without the strokes give no bracket, with the reason -- the fixture's one row carries
        # the Atkinson ratio and both cam phases, but one cam pair cannot test three unknowns (defect D-1, 29
        # October 2026: the reason this asserted before, that no valve event follows from the ratio at all, was
        # false, and is gone)
        b2 = C.valve_brackets([F.point_row()], geometry=geo)
        self.assertIsNone(b2["ivc_deg"]["bracket"])
        self.assertIn("Atkinson ratio and both cam phases give 1 distinct cam pair", b2["ivc_deg"]["why_not_bracket"])
        self.assertNotIn("ratio of the effective expansion to the effective compression ratio",
                         b2["ivc_deg"]["why_not_bracket"])
        # a cam phase alone (the Ford's Cell 9) still brackets nothing, with its own reason
        b3 = C.valve_brackets([F.point_row(atkinson_ratio=None)], geometry=geo)
        self.assertIsNone(b3["evo_deg"]["bracket"])
        self.assertIn("a cam phase is a shift from a base timing", b3["evo_deg"]["why_not_bracket"])

    def test_valve_brackets_from_the_atkinson_ratio(self):
        """Defect D-1 (29 October 2026): EPA's Atkinson ratio is x(EVO0 + exhaust cam) / x(-(IVC0 + intake cam)),
        x the slider-crank travel, so synthetic rows made at a known IVC0, EVO0 and rod give them back exactly, and
        the cams' ranges bracket IVC and EVO. Controls (mistake 12): IVC0 moved 5 deg moves the IVC bracket 5 deg
        and leaves EVO's; one ratio off by 1e-6 is no exact fit and gives no bracket, with the reason; the old
        reading of the channel (compression over expansion) fits nothing exactly."""
        import math
        geo = engines.Geometry(**engines.read_spec("mazda_25t")["geometry"])

        def x(deg, lam):
            t = math.radians(deg)
            return 1.0 - math.cos(t) + lam - math.sqrt(lam * lam - math.sin(t) ** 2)
        cams = ((-74.0, 0.0), (-50.0, 20.0), (-30.0, 48.0), (-10.0, 5.0), (-0.5, 30.0), (-60.0, 40.0), (-20.0, 12.0))

        def rows_at(ivc0, evo0, lam, *, flip=False, off=0.0):
            out = []
            for i, (c, e) in enumerate(cams):
                num, den = x(evo0 + e, lam), x(-(ivc0 + c), lam)
                out.append(F.point_row(source_row=6 + i, cam_cad=c, exhaust_cam_cad=e,
                                       atkinson_ratio=(den / num if flip else num / den) + (off if i == 3 else 0.0)))
            return out
        b = C.valve_brackets(rows_at(-80.0, 120.0, 3.684), geometry=geo)
        fit = b["ivc_deg"]["atkinson_fit"]
        self.assertEqual((b["ivc_deg"]["method"], b["evo_deg"]["method"]), ("atkinson", "atkinson"))
        self.assertAlmostEqual(fit["ivc0_deg"], -80.0, places=7)
        self.assertAlmostEqual(fit["evo0_deg"], 120.0, places=7)
        self.assertAlmostEqual(fit["rod_over_half_stroke"], 3.684, places=7)
        self.assertLess(fit["max_abs_residual"], C.ATKINSON_EXACT)
        self.assertEqual((fit["rows"], fit["starts"]), (len(cams), len(C.ATKINSON_STARTS)))
        lo, hi = b["ivc_deg"]["bracket"]
        self.assertAlmostEqual(lo, -80.0 - 74.0, places=6)
        self.assertAlmostEqual(hi, -80.0 - 0.5, places=6)
        lo, hi = b["evo_deg"]["bracket"]
        self.assertAlmostEqual(lo, 120.0, places=6)
        self.assertAlmostEqual(hi, 168.0, places=6)
        self.assertAlmostEqual(b["evo_deg"]["rod_m_at_plant_stroke"], 3.684 * 0.5 * geo.stroke, places=9)
        # the control: IVC0 5 deg later moves the IVC bracket by 5 deg, EVO's not at all
        b5 = C.valve_brackets(rows_at(-75.0, 120.0, 3.684), geometry=geo)
        self.assertAlmostEqual(b5["ivc_deg"]["bracket"][0] - b["ivc_deg"]["bracket"][0], 5.0, places=6)
        self.assertAlmostEqual(b5["evo_deg"]["bracket"][1], b["evo_deg"]["bracket"][1], places=6)
        # the control: one ratio 1e-6 off is no exact fit, so no bracket, with the reason
        bad = C.valve_brackets(rows_at(-80.0, 120.0, 3.684, off=1e-6), geometry=geo)
        self.assertIsNone(bad["ivc_deg"]["bracket"])
        self.assertIn("no exact fit", bad["ivc_deg"]["why_not_bracket"])
        # the control: the ratio as EPA's printed description reads it (compression over expansion) is not this
        # channel's arithmetic, and is no exact fit either
        inv = C.valve_brackets(rows_at(-80.0, 120.0, 3.684, flip=True), geometry=geo)
        self.assertIsNone(inv["evo_deg"]["bracket"])
        self.assertIn("no exact fit", inv["evo_deg"]["why_not_bracket"])
        # an advance-published intake cam moves IVC the other way (CAM_SIGN): the same events from negated phases
        adv = [dataclasses.replace(r, cam_cad=-r.cam_cad, cam_channel="intake_cam_phase_cad_adv")
               for r in rows_at(-80.0, 120.0, 3.684)]
        ba = C.valve_brackets(adv, geometry=geo)
        self.assertAlmostEqual(ba["ivc_deg"]["bracket"][0], b["ivc_deg"]["bracket"][0], places=6)
        self.assertAlmostEqual(ba["ivc_deg"]["bracket"][1], b["ivc_deg"]["bracket"][1], places=6)

    def test_probe_sizes_by_hand(self):
        base = {"egt": 1000.0, "mdot": 100.0}
        cells = {("a", 1): {"egt": 1002.0, "mdot": 100.0}, ("a", -1): {"egt": 998.0, "mdot": 100.0},
                 ("b", 1): {"egt": 1000.0, "mdot": 100.0}, ("b", -1): {"egt": 1000.0, "mdot": 100.0},
                 ("ivc_deg", 1): {"egt": 1000.0, "mdot": 100.0}, ("ivc_deg", -1): {"egt": 1000.0, "mdot": 100.0}}
        hs = {"f": 0.5, "dTh_per_unit_ln_mdot": 0.0}
        out = C.probe_sizes(base, hs, cells, r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                            fields=(("cycle", "a"), ("cycle", "b"), ("geometry", "ivc_deg")),
                            brackets={"ivc_deg": {"bracket": [-150.0, -135.0]}}, v0={"a": 20.0, "b": 5.0,
                                                                                       "ivc_deg": -140.0},
                            sigmas={"a": 2.0})
        # a: +-10 % of 20 is +-2; the gas +-2 K; the housing f x 2 = +-1 K; the slope 0.5 K per unit
        self.assertAlmostEqual(out["a"]["slope_k_per_unit"], 0.5)
        self.assertAlmostEqual(out["a"]["worth_r1"], 20.0)
        self.assertEqual((out["a"]["method"], out["a"]["size"]), ("probe", 20.0))
        # load-bearing at the BAND, not at the probe (WP3's second fix of 23 October 2026): the probe moves the
        # housing equivalent by R1 by construction; the band, sigma 2, by 0.5 x 2 = 1 K, under R1
        self.assertAlmostEqual(out["a"]["probe_housing_change_k"], 10.0)
        self.assertAlmostEqual(out["a"]["housing_change_k"], 1.0)
        self.assertTrue(out["a"]["load_bearing"] is False)
        self.assertEqual(out["a"]["band"]["source"], "the fit's standard uncertainty")
        wide = C.probe_sizes(base, hs, cells, r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                             fields=(("cycle", "a"),), brackets={}, v0={"a": 20.0}, sigmas={"a": 30.0})
        self.assertTrue(wide["a"]["load_bearing"] is True)                  # 0.5 x 30 = 15 K, over R1
        self.assertEqual((out["b"]["method"], out["b"]["size"]), ("fallback", 0.5))
        self.assertIsNone(out["b"]["load_bearing"])                         # no band (ASSUMED)
        self.assertIn("no band", out["b"]["load_bearing_why"])
        # defect D-2: a bracket is its two edges, with no symmetric size (test_a_bracket_is_applied_as_its_two_edges)
        self.assertEqual((out["ivc_deg"]["method"], out["ivc_deg"]["size"]), ("bracket", None))
        self.assertEqual(out["ivc_deg"]["band"]["edges"], [-150.0, -135.0])
        self.assertIn("agents", out["a"]["worth_b_why"])
        nob = C.probe_sizes(base, hs, cells, r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                            fields=(("cycle", "a"),), brackets={}, v0={"a": 20.0}, sigmas={})
        self.assertIsNone(nob["a"]["load_bearing"])                         # the probe alone decides nothing
        # a NEGATIVE value with a slope (IVC near -140 deg): the +1 cell is the one at v0 + rel |v0| (the
        # completion builds it so), and the slope's sign is the gas's per degree, here +0.5 x f per degree
        cells2 = {("ivc_deg", 1): {"egt": 1007.0, "mdot": 100.0}, ("ivc_deg", -1): {"egt": 993.0, "mdot": 100.0}}
        out2 = C.probe_sizes(base, hs, cells2, r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                             fields=(("geometry", "ivc_deg"),), brackets={}, v0={"ivc_deg": -140.0}, sigmas={})
        # the housing f x (+-7 K) = +-3.5 K over 2 x 14 deg: +0.25 K per degree
        self.assertAlmostEqual(out2["ivc_deg"]["slope_k_per_unit"], 0.25, places=12)

    def test_a_bracket_is_applied_as_its_two_edges(self):
        """Defect D-2 (29 October 2026): a row-9 bracket is applied as its two edges -- the constant moved to the
        bracket's lower edge and to its upper edge -- never as v0 +- its farther edge from the value, which on the
        Mazda's IVC (v0 -140 deg, bracket [-154.27, -80.30]) probed -199.70 deg, 45 deg outside the bracket. The
        band is judged at the two edges: the housing change at each, slope x (edge - value), housing_change_k the
        larger magnitude (the farther edge's, so load_bearing does not move). The controls: HEAD's record gave the
        bracket a symmetric size, 59.70, whose minus side lies below the bracket; a constant without a bracket keeps
        v0 +- its size; and a bracket that is not [lo, hi] is a completion defect."""
        base = {"egt": 1000.0, "mdot": 100.0}
        hs = {"f": 0.5, "dTh_per_unit_ln_mdot": 0.0}
        # the Mazda's IVC in shape: +-10 % of 140 deg is +-14 deg, the gas +-3.5 K, the housing +-1.75 K: 0.125 K/deg
        cells = {("ivc_deg", 1): {"egt": 1003.5, "mdot": 100.0}, ("ivc_deg", -1): {"egt": 996.5, "mdot": 100.0},
                 ("t_head_k", 1): {"egt": 1002.0, "mdot": 100.0}, ("t_head_k", -1): {"egt": 998.0, "mdot": 100.0}}
        lo, hi = -154.26905, -80.29795
        kw = dict(r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                  fields=(("geometry", "ivc_deg"), ("cycle", "t_head_k")), v0={"ivc_deg": -140.0, "t_head_k": 90.0},
                  sigmas={})
        out = C.probe_sizes(base, hs, cells, brackets={"ivc_deg": {"bracket": [lo, hi]}}, **kw)
        ivc = out["ivc_deg"]
        self.assertIsNone(ivc["size"])                                  # HEAD: 59.70, the farther edge's distance
        self.assertEqual((ivc["method"], ivc["bracket"], ivc["values"]), ("bracket", [lo, hi], {"+": hi, "-": lo}))
        self.assertEqual(ivc["size_why"], C.BRACKET_EDGES)
        self.assertTrue(lo <= ivc["values"]["-"] <= hi and lo <= ivc["values"]["+"] <= hi)
        # the control: HEAD's symmetric application, v0 - the farther edge's distance, lies 45 deg below the bracket
        far = max(abs(lo + 140.0), abs(hi + 140.0))
        self.assertAlmostEqual(-140.0 - far, -199.70205, places=9)
        self.assertLess(-140.0 - far, lo - 45.0)
        # the band at its two edges: 0.125 K/deg x (edge - v0); housing_change_k the larger, the farther edge's
        slope = ivc["slope_k_per_unit"]
        self.assertAlmostEqual(slope, 0.125, places=12)
        at = ivc["band"]["housing_change_k_at_edges"]
        self.assertEqual((at["lo"], at["hi"]), (slope * (lo + 140.0), slope * (hi + 140.0)))
        self.assertEqual(ivc["housing_change_k"], max(abs(at["lo"]), abs(at["hi"])))
        self.assertAlmostEqual(ivc["housing_change_k"], slope * far, places=12)       # load-bearing does not move
        self.assertEqual(ivc["band"]["edges"], [lo, hi])
        self.assertEqual(ivc["probe_housing_change_k"], ivc["housing_change_k"])
        self.assertTrue(ivc["load_bearing"] is False)                                  # 7.46 K, under R1 10 K
        # the control: a constant without a bracket keeps v0 +- its size (its change worth R1, 10 / 0.01 K per K)
        th = out["t_head_k"]
        self.assertEqual((th["method"], th["bracket"]), ("probe", None))
        self.assertEqual(th["values"], {"+": 90.0 + th["size"], "-": 90.0 - th["size"]})
        # and a bracket that is not [lo, hi] is refused
        with self.assertRaises(C.CompletionDefect):
            C.probe_sizes(base, hs, cells, brackets={"ivc_deg": {"bracket": [hi, lo]}}, **kw)

    def test_a_probe_below_the_numerical_noise_is_not_visible_at_r1(self):
        """Decision 85 (29 October 2026): a probe whose antisymmetric housing response |h(+) - h(-)|/2 is at or
        below the climb cell's numerical noise (numerical_noise_k, the housing equivalent of the median's
        resolution) is "not visible at R1": the contract's +-10 % fallback, no worth R1, counted as excluded with
        the reason. By hand, the first pass's exh_bp_min_kpa in shape (a floor near 105 kPa whose +-10 % moves the
        housing by 1e-5 K): the controls are the same probe with no noise floor, which takes the change worth R1
        (about 1e6 kPa, as the first pass did), a constant whose response is far above the floor, which keeps its
        probe, and a bracketed constant below the floor, which keeps its bracket."""
        base = {"egt": 1000.0, "mdot": 100.0}
        hs = {"f": 0.5, "dTh_per_unit_ln_mdot": 0.0}
        res = {"egt": 1000.0, "mdot": 100.0, "egt_resolution_k": 1.2e-4, "mdot_resolution_gps": 9e-5, "samples": 319}
        noise = C.numerical_noise_k(hs, res)
        self.assertAlmostEqual(noise, 0.5 * 1.2e-4, places=15)
        self.assertAlmostEqual(C.numerical_noise_k({"f": -0.5, "dTh_per_unit_ln_mdot": -150.0}, res),
                               0.5 * 1.2e-4 + 150.0 * 9e-5 / 100.0, places=15)
        cells = {("floor", 1): {"egt": 1000.00002, "mdot": 100.0}, ("floor", -1): {"egt": 999.99998, "mdot": 100.0},
                 ("ua", 1): {"egt": 1002.0, "mdot": 100.0}, ("ua", -1): {"egt": 998.0, "mdot": 100.0},
                 ("ivc_deg", 1): {"egt": 1000.0, "mdot": 100.0}, ("ivc_deg", -1): {"egt": 1000.0, "mdot": 100.0}}
        kw = dict(r1_k=10.0, rel=0.1, else_rel=0.1, else_cad=10.0,
                  fields=(("cycle", "floor"), ("cycle", "ua"), ("geometry", "ivc_deg")),
                  brackets={"ivc_deg": {"bracket": [-150.0, -135.0]}}, v0={"floor": 105.0, "ua": 20.0, "ivc_deg": -140.0},
                  sigmas={})
        out = C.probe_sizes(base, hs, cells, noise_k=noise, **kw)
        fl = out["floor"]
        self.assertEqual((fl["method"], fl["visible_at_r1"], fl["counted_excluded"]), ("fallback", False, True))
        self.assertAlmostEqual(fl["size"], 10.5, places=12)                     # the contract's +-10 %
        self.assertIsNone(fl["worth_r1"])
        self.assertIn("not visible at R1", fl["not_visible_at_r1"])
        self.assertEqual(fl["counted_excluded_why"], fl["not_visible_at_r1"])
        self.assertAlmostEqual(fl["response_k"], 1e-5, places=9)
        self.assertEqual(fl["numerical_noise_k"], noise)
        # the controls: the visible constant keeps its probe sized by R1, the bracket its bracket
        self.assertEqual((out["ua"]["method"], out["ua"]["visible_at_r1"], out["ua"]["counted_excluded"]),
                         ("probe", True, False))
        self.assertAlmostEqual(out["ua"]["size"], 20.0)
        self.assertEqual((out["ivc_deg"]["method"], out["ivc_deg"]["bracket"]), ("bracket", [-150.0, -135.0]))
        self.assertFalse(out["ivc_deg"]["counted_excluded"])
        # the control: without a noise floor the same tiny slope takes the change worth R1, 1e6 kPa
        off = C.probe_sizes(base, hs, cells, **kw)
        self.assertEqual((off["floor"]["method"], off["floor"]["visible_at_r1"]), ("probe", None))
        self.assertAlmostEqual(off["floor"]["size"], 10.0 / (1e-5 / 10.5), delta=1.0)
        # at the edge: a response equal to the noise is not visible, one ulp above it is
        edge = {("floor", 1): {"egt": 1000.0 + 2.0 * noise, "mdot": 100.0},
                ("floor", -1): {"egt": 1000.0 - 2.0 * noise, "mdot": 100.0}}
        one = dict(kw, fields=(("cycle", "floor"),), brackets={}, v0={"floor": 105.0})
        r = C.probe_sizes(base, hs, edge, noise_k=noise, **one)["floor"]["response_k"]
        self.assertFalse(C.probe_sizes(base, hs, edge, noise_k=r, **one)["floor"]["visible_at_r1"])
        import math
        self.assertTrue(C.probe_sizes(base, hs, edge, noise_k=math.nextafter(r, 0.0), **one)["floor"]["visible_at_r1"])

    def test_the_finiteness_assertion(self):
        v = {**frozen_values("A"), **json.loads(json.dumps(epa_fit.PROVISIONAL_COMPLETION))}
        p = engines.build_candidate(MAZDA, v)
        C._assert_finite(p, excluded=set(), step="probe")
        bad = dataclasses.replace(p, engine=dataclasses.replace(p.engine, damage=dataclasses.replace(
            p.engine.damage, turb_knee_k=float("nan"))))
        with self.assertRaises(C.CompletionDefect):
            C._assert_finite(bad, excluded=set(), step="probe")
        C._assert_finite(bad, excluded={C.COMPLETION_FIELDS["knee"]}, step="probe")

    def test_the_other_octane(self):
        """other_octane (HANDOFFS.md WP3 item 5): none on one fuel batch; on two, epa_engine.json's alpha_fuel
        octane where it differs from the plant's, else the typed one less OCTANE_STEP_RON; never the plant's
        own, which fit_declarations refuses (the claim would hold trivially there)."""
        p = engines.build_candidate(FORD, {**frozen_values("A"), **json.loads(json.dumps(epa_fit.PROVISIONAL_COMPLETION))})
        own = float(p.engine.cycle.octane)
        fuel = lambda tag: epa_rows.TableFuel(ftag=tag, fuel_report="s", lhv_j_per_kg=42.9e6, afr_st=14.5)  # noqa: E731
        one = types.SimpleNamespace(fuel_by_table={"a": fuel("X"), "b": fuel("X")})
        two = types.SimpleNamespace(fuel_by_table={"a": fuel("X"), "b": fuel("Y")})
        facts = lambda ron: types.SimpleNamespace(alpha_fuel={} if ron is None else {"research_octane_number": ron})  # noqa
        self.assertEqual(C.other_octane(one, facts(own + 3.0), plant=p), (None, None))
        self.assertEqual(C.other_octane(two, facts(own + 3.0), plant=p)[0], own + 3.0)
        self.assertEqual(C.other_octane(two, facts(None), plant=p)[0], own - C.OCTANE_STEP_RON)
        self.assertEqual(C.other_octane(two, facts(own), plant=p)[0], own - C.OCTANE_STEP_RON)
        with self.assertRaises(ValueError):
            epa_fit.fit_declarations(p, view=two, other_octane=own, dtheta=1.0)

    def test_seen_before_the_fit_carries_d3_rows_read_list(self):
        """d3_rows.SOURCES_READ is copied (calibrate_epa names nothing of d3_rows but its pin check, N11);
        the literal is read here through ast and every entry must be in SEEN_BEFORE_THE_FIT (the control: one
        entry missing is seen); and the reviews' reads are disclosed."""
        with open(os.path.join(HERE, "d3_rows.py"), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
        lit = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                   and any(getattr(t, "id", None) == "SOURCES_READ" for t in n.targets))
        seen = " | ".join(C.SEEN_BEFORE_THE_FIT)
        self.assertTrue(all(s in seen for s in lit))
        self.assertFalse(all(s in seen.replace(lit[0], "") for s in lit))
        for s in epa_rows.SEEN:
            self.assertIn(s, C.SEEN_BEFORE_THE_FIT)
        self.assertIn("isolation reviewer", seen)
        self.assertIn("ENGINE_THRESHOLDS.md:980-1010", seen)

    def test_seen_before_the_fit_carries_the_disclosure(self):
        """Ghassan's order of 29 October 2026: the defect hunt's code-path investigator printed part of the Mazda's
        ALPHA full-throttle curve, whose node at 1751 rpm is held-out High Load Initial row 18's torque, and that
        read is recorded where the code records what was seen before the fit (stage0.json carries the tuple), with
        the hunt's and the fixer's own reads, naming what was seen and where and repeating no torque. The control:
        the tuple without the entry fails the check."""
        def disclosed(seen):
            return any("wot_torque_curve" in s and "rows 12, 18, 24 and 30" in s and "1751 rpm" in s
                       and "held-out row" in s and "E1i" in s for s in seen)
        self.assertTrue(disclosed(C.SEEN_BEFORE_THE_FIT))
        self.assertFalse(disclosed(tuple(s for s in C.SEEN_BEFORE_THE_FIT if not s.startswith("THE DISCLOSURE"))))
        self.assertTrue(any(s.startswith("the defect hunt, 24 October 2026") for s in C.SEEN_BEFORE_THE_FIT))
        self.assertTrue(any(s.startswith("the implementer of defect D-1") for s in C.SEEN_BEFORE_THE_FIT))

    def test_seen_before_the_fit_carries_the_pin_authors_reads(self):
        """epa_stats.SOURCES_READ, the u_D pins' author's reads (decision 56; the Mazda's ALPHA page read whole
        among them), is in SEEN_BEFORE_THE_FIT, entry by entry (amendment C13; WP3_INTERFACES.md 11; WP3's third
        fix of 24 October 2026, on all four reviews' finding that it was not). The control (mistake 12): the list
        with one of those entries dropped is caught. And the third round's reviewers' and fixer's reads are
        disclosed."""
        def missing(seen_list):
            seen = " | ".join(seen_list)
            return [s for s in epa_stats.SOURCES_READ if s not in seen]
        self.assertTrue(epa_stats.SOURCES_READ)
        self.assertEqual(missing(C.SEEN_BEFORE_THE_FIT), [])
        dropped = [x for x in C.SEEN_BEFORE_THE_FIT if epa_stats.SOURCES_READ[1] not in x]
        self.assertEqual(missing(dropped), [epa_stats.SOURCES_READ[1]])
        seen = " | ".join(C.SEEN_BEFORE_THE_FIT)
        for who in ("third isolation reviewer, 24 October 2026", "third contract reviewer, 24 October 2026",
                    "Run 1 reviewer, 24 October 2026", "third test reviewer, 24 October 2026",
                    "third fixer, 24 October 2026",
                    # the fourth round (WP3's fourth fix of 24 October 2026)
                    "fourth isolation reviewer, 24 October 2026", "fourth contract reviewer, 24 October 2026",
                    "fourth Run 1 reviewer, 24 October 2026", "fourth test reviewer, 24 October 2026",
                    "fourth fixer, 24 October 2026"):
            self.assertIn(who, seen)
        self.assertEqual(len(set(C.SEEN_BEFORE_THE_FIT)), len(C.SEEN_BEFORE_THE_FIT), "no entry twice")


if __name__ == "__main__":
    unittest.main(verbosity=2)
