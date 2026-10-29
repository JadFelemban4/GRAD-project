"""epa_fit.py -- build step 2's fitting procedure: one EPA engine's cycle model and
ECU, fitted form by form on its calibration rows, and the in-sample stage that
picks its form (docs/build_step_2/PLAN.md section 5, as docs/build_step_2/
AMENDMENTS.md C1 and D1-D14 amend it; decisions 49-53; the interfaces are
docs/build_step_2/WP3_INTERFACES.md section 5.3).

    import epa_fit, plant
    lad = epa_fit.ladder("mazda_25t", yield_, view=view, jobs=16, dtheta=plant.DTHETA_DEG)
    lad.chosen                                  # the engine's own form (decision 49)
    fit = next(f for f in lad.fits if f.form == lad.chosen)
    fit.values                                  # the derived file's frozen sections
    epa_fit.fit_record(fit, view=view, start=None, dtheta=..., jobs=16, declarations=...)
                                                # fit_<form>.json, less its provenance
    epa_fit.run_t0("mazda_25t", yield_, view=view, jobs=16, dtheta=plant.DTHETA_DEG)
                                                # T0 (Run 1, before the fit: amendment A1)

WRITTEN 23 October 2026 (build step 2, WP3), BEFORE ANY FIT. Nothing here opens a
file, reads a table or names one (WP3_INTERFACES.md section 3: the rows come from
epa_rows' yield, the contract's numbers from its calibration view), and nothing
here has been run on an EPA row: the tests (test_epa_fit.py) fit synthetic rows
made by the plant at known truths. S0 and T0 run first in Run 1 (amendment A1).

WHAT A STAGE IS (PLAN.md 5.2). Each stage fits a few constants on the rows that
carry information on them, with every other constant held at its current value,
in the order S1 (back-pressure), S3a-S3d (the ECU's spark, enrichment, boost
envelope and cam: arithmetic on the rows, no cycle), S2 (breathing), S4 (burn,
friction, port), S5 (form C's rich slope), S6 (knock scale), then `verify`. S1 and
the S3 stages run before S2 here because S2 under form D reads S3d's cam, and every
candidate plant needs an ECU; none of them reads a cycle, so the order moves no
number. Every candidate is built by engines.build_candidate from a dict shaped like
the derived file, the constructor engines.get uses (mistake 10), and every value is
a Python float, int or str before it gets there (amendment B10).

WHAT IS NEVER DONE. No constant is held (PF-B1); no fit outcome stops the run
(RF-1): a bound hit, a non-convergence, a VE at its clip, a flat profile, a zero
Jacobian column at the optimum are each a flag, PLAN.md 5.6's declared outcomes. An
assertion that fails -- a count, a shortcut that is not the plant, a zero column at
the start -- is a coding defect, raised.

DETERMINISM (PLAN.md 5.1). No random number in the fit (T0's noise is a named
stream, and T0 is not the fit); fixed grids and starts; ordered_map gathers its
results in submission order; one BLAS thread, asserted in every worker; no clock in
any output.
"""
import dataclasses
import json
import math
import multiprocessing
import os
import struct
from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import least_squares, lsq_linear, minimize_scalar
from scipy.stats import chi2, norm

import engine_env
import engines
import epa_rows
import epa_stats
import plant as plant_model     # the module; `plant` is the parameter (an engines.Plant)

# ---------------------------------------------------------------------------
# Declared constants (PLAN.md 5.2; amendments D5, D6, D9; each with its source)
# ---------------------------------------------------------------------------
# THE RIDGE (PLAN.md 5.2, "The ridge, declared"; decision 50): each nonlinear stage
# adds sqrt(w) * (theta - theta0) / s for every parameter it fits. It decides only
# directions the data leave undetermined; at w = 0.01 it is about 1e4 times weaker
# than S2's information on ve_map (wrong claim 12), so it holds no term neutral.
RIDGE_W = 0.01
# The declared scale of each parameter (PLAN.md 5.2), in the parameter's own unit:
# the ridge divides by it and least_squares' x_scale is it (amendment D5).
SCALES = {
    "burn_base": 10.0, "burn_rpm": 0.002, "delay_base": 5.0, "delay_rpm": 0.001,
    "fmep_0": 0.4, "fmep_pmax": 0.005, "fmep_sp": 0.09, "fmep_sp2": 0.0009,
    "ua_port": 50.0, "ve_rpm": 1000.0, "ve_width": 1000.0,
    "ve_map": 1e-3, "ve_cam": 1e-3, "ce_rich_slope": 0.65,
}
# x_scale (amendment D5: "pass x_scale = the declared scales"). ve_base and ve_amp
# have no ridge scale in PLAN.md 5.2 (S2 solves them linearly inside its projection,
# amendment D9); their polish scale is declared here, DESIGN: 0.1, the order of
# their bounds' half-widths, so that one unit of x_scale is a comparable move on
# every axis of S2's polish.
X_SCALE = dict(SCALES, ve_base=0.1, ve_amp=0.1)
# THE BOUNDS (PLAN.md 5.2, amendment D9). ve_rpm's are the engine's end lines, read
# from the calibration view at the fit (D9: "within [rpm_min, rpm_max]"; amendment
# C13 cites them to JSON lines), so they are None here. ve_map's and ve_cam's are
# not in the plan: DESIGN, five times their ridge scale each way (five scale
# units; a VE move of 0.5 over 100 kPa or 100 CAD), wide enough that a bound that
# binds is itself a finding (flagged, PLAN.md 5.6). ce_rich_slope's is S5's Brent
# interval (PLAN.md 5.3).
BOUNDS = {
    "exh_bp_ratio": (1.0, 2.5), "exh_bp_min_kpa": (80.0, 140.0),
    "ve_base": (0.3, 1.3), "ve_amp": (-0.6, 0.6), "ve_rpm": None, "ve_width": (300.0, 20000.0),
    "ve_map": (-5e-3, 5e-3), "ve_cam": (-5e-3, 5e-3),
    "burn_base": (5.0, 90.0), "burn_rpm": (0.0, 0.012), "delay_base": (0.0, 30.0), "delay_rpm": (0.0, 0.006),
    "fmep_0": (-0.5, 2.0), "fmep_pmax": (-0.05, 0.05), "fmep_sp": (-0.1, 0.4), "fmep_sp2": (-0.01, 0.02),
    "ua_port": (0.0, 1000.0), "ce_rich_slope": (0.0, 1.5),
}
# THE SOLVER'S TOLERANCES (amendment D5: SciPy 1.18.1's least_squares defaults are
# 1e-8 each and x_scale 1 for trf; "declare ftol/xtol/gtol above the measured
# finite-difference noise"). MEASURED 23 October 2026 on synthetic B58 rows (the
# B58's plant, engines.get("b58"), at 30 synthetic operating points, 1500-5000 rpm,
# 40-220 kPa, lambda 1.00; targets from the same plant with burn_base, delay_base,
# fmep_0 and ua_port moved by 5 %; the scratchpad scripts fd_noise.py and
# fd_noise2.py of the WP3 session, both re-run by its second implementer the same
# day and printing these figures again; test_epa_fit.Tolerances re-measures the
# claim on a smaller construction at every run): S4's cost, moved along a burn or
# delay term, departs from a quadratic by at most 4e-13 of itself over 1e-4 of the
# parameter's scale, and from a degree-6 polynomial by up to 9.3e-4 of itself
# (median 3.4e-4 on burn_base) over +-0.05 of the scale at dtheta 0.25 (3.0e-3 at
# dtheta 1.0): plant.run_cycle's crank-angle grid switches (the knock window,
# Woschni's combustion term, the Wiebe ends) as the burn moves. FMEP's and
# UA_PORT's directions depart from the degree-6 polynomial by below 4e-8: they sit
# outside the integration. Until WP3's second fix S4's five starts ran at ftol 2e-3,
# above the 9.3e-4 at the production step, and xtol 1e-3, a scaled step of about
# 0.05 CAD on burn_base, on the claim that a step inside that roughness gains
# nothing. THOSE TOLERANCES DID NOT RESOLVE THE MINIMUM along the weakest
# direction, and the claim was wrong (WP3's second fix of 23 October 2026, on the
# fit review's measurement, its
# scratchpad rv/s4_tol.py, form A on T0's noisy synthetic rows of test_epa_fit's
# dataset at dtheta 0.25): at 2e-3/1e-3 the five starts stop after 4-8 evaluations
# with end points 3.94 scale units apart along the weakest direction (its sd 2.39),
# while at 1e-12 each converges in 28-40 evaluations to within 0.35, and the kept
# point moves by Mahalanobis^2 0.095 in the reported covariance. A polish of the
# best of those five at tight tolerances alone was measured and is not enough (the
# second fixer's re-run of the same script, scratchpad fix2/s4_polish_measure.py):
# it lowered that start's cost from 4.939798 to 4.938738 in 19 evaluations, while
# the best tight start, the one the declared tolerance had stopped worst, reached
# 4.934940 (Mahalanobis^2 0.037 between the two). So S4's five starts run at 1e-10
# each, where they converge (24-35 evaluations, status 2-3) and keep the 0.35 spread
# the cycle's roughness leaves along the weakest direction (sd 2.37), the kept
# point the best of them (4.934940); and that point is POLISHED once at
# TOLERANCES["S4_polish"], 1e-12 each, a declared final step whose departure
# fit_<form>.json records (S4's report, "polish"): measured, 3e-6 scale units in 19
# evaluations, Mahalanobis^2 4.5e-16 from the same fit with its starts at 1e-12. A form-A fit
# there took 50.3 s against 18.6 s at the old tolerances. S2's objective holds no
# cycle (plant.volumetric_efficiency, analytic): its noise is rounding, about 1e-15
# of the cost, and its three tolerances are 1e-12.
TOLERANCES = {"S2": {"ftol": 1e-12, "xtol": 1e-12, "gtol": 1e-12},
              "S4": {"ftol": 1e-10, "xtol": 1e-10, "gtol": 1e-10},
              "S4_polish": {"ftol": 1e-12, "xtol": 1e-12, "gtol": 1e-12}}
# PLAN.md 5.2 S4 and 5.6: 60 evaluations, then one declared second attempt at
# twice that from the best iterate; then the best iterate is accepted and flagged.
MAX_NFEV = 60
SECOND_ATTEMPT_NFEV = 120
# The load the part-load spark plane is written about, DESIGN (PLAN.md 9.2; the
# engine specs type it so, engine_specs/<id>.toml [ecu] spark_ref_kpa). Checked
# against the spec at every fit: two values for one number would be mistake 10.
SPARK_REF_KPA = 40.0
# THE COMPLETION SECTIONS WHILE THE FIT RUNS (WP3_INTERFACES.md 5.3, chosen there):
# a candidate needs every DERIVED field of its set (engines.build_candidate), and
# the three completion fields are measured only after the freeze (PLAN.md 5.9).
# None of them reaches a row output: no cycle and no ECU call reads the
# deliverable-torque table, the K3 knee or the torque floor (they are read by the
# environment's kickdown, damage and training-road guard). test_epa_fit shows two
# provisional sets give bit-identical row outputs (the control amendment F7 asks
# for, applied to the fit). 1123.0 is the B58's typed knee, a placeholder only.
PROVISIONAL_COMPLETION = {"deliverable_torque": [], "k3": {"turb_knee_k": 1123.0},
                          "loop": {"torque_floor_nm": 0.0}}

# The crank-angle step every fit, in-sample stage and completion runs at: the plant's own
# (plant.DTHETA_DEG, the FATAL dtheta_deg of the fingerprint), read here so that calibrate_epa.py,
# which imports no plant module (WP3_INTERFACES.md 3.1), passes the one value and never types it
# (WP3's integration, 23 October 2026). E6 row 8 halves it (validate_epa).
DTHETA_DEG = float(plant_model.DTHETA_DEG)

# S1: the hinge's grid step, kPa (PLAN.md 5.2 S1).
S1_GRID_KPA = 0.1
# S2: ve_width's log grid, 300-20 000 rpm (PLAN.md 5.2 S2), 41 points, DESIGN: a
# factor of 1.11 between neighbours, finer than the polish needs to start inside
# the right basin; the polish moves it off the grid.
S2_WIDTH_GRID = tuple(float(x) for x in np.geomspace(300.0, 20000.0, 41))
# S3a: the iteration cap and each piece's minimum row count (PLAN.md 5.2 S3a;
# amendment D7: "a minimum row count and rank per piece"). The plane has three
# coefficients and the knock-limited surface four (engine_env.BaselineECU); one
# row more than each, DESIGN, so that a piece is never an interpolation.
S3A_MAX_ITER = 50
S3A_MIN_ROWS = {"part_load": 4, "knock_limited": 5}
# S3b: the gate's grid step and the lowest edge's DESIGN alternative (amendment C1:
# "the lowest calibration Final MAP, or DESIGN 100 kPa"; chosen in
# WP3_INTERFACES.md 5.3: the lower of the two), the least rpm span of the
# enrichment ramp (PLAN.md 5.2 S3b), and where rpm_lo may sit below the lowest
# calibration line (amendment D2: "rpm_lo may take values below the lowest
# calibration line"): 500 rpm steps down to 2000 rpm below it, DESIGN, the order
# of the lines' own spacing.
S3B_GATE_STEP_KPA = 1.0
S3B_GATE_DESIGN_KPA = 100.0
S3B_RPM_SPAN_MIN = 300.0
S3B_RPM_LO_BELOW = (500.0, 1000.0, 1500.0, 2000.0)
# The dwell S3b evaluates the schedule at: 30 s, EPA's hold (PLAN.md 5.2 S3b, "dwell
# 30 s, so t = 1 with the carried 1.5 and 3.0 s"); the same dwell E8 runs the ECU at.
S3B_DWELL_S = 30.0
# S0: half the rounding of the contract's printed hot floor (thresholds/split.py writes round(floor, 2)):
# a calibration row within it of the printed floor may classify differently than split.compute did.
HOT_FLOOR_HALF_ROUNDING_KPA = 0.005
# S3c: the filter loss between the cell barometer and the compressor inlet, kPa
# (PLAN.md 5.2 S3c, "(barometer - 2)"; the B58's inlet_sea_kpa is 101.3 less the
# same 2 kPa, ASSUMED there).
S3C_FILTER_LOSS_KPA = 2.0
# S4: the forward-difference step on the burn and delay bases, CAD (PLAN.md 5.2 S4;
# amendment D4), the parameters in the order every report writes them.
FD_CAD = 0.5
S4_PARAMS = ("burn_base", "burn_rpm", "delay_base", "delay_rpm",
             "fmep_0", "fmep_pmax", "fmep_sp", "fmep_sp2", "ua_port")
S4_START_FACTORS = (1.0, 0.8, 1.2)          # PLAN.md 5.2 S4: the start, x0.8, x1.2
# S4's physical checks (PLAN.md 5.6): burn 20-120 CAD, delay 1-40 CAD, FMEP > 0.
S4_BURN_RANGE = (20.0, 120.0)
S4_DELAY_RANGE = (1.0, 40.0)
# S5: Brent's absolute tolerance on the slope, DESIGN (one part in 15 000 of its
# interval), and the physical check of PLAN.md 5.3: eta_comb >= 0.5 at the deepest
# calibration lambda.
S5_XATOL = 1e-4
S5_ETA_MIN = 0.5
# S5's central-difference step for the slope's standard uncertainty, DESIGN: ten times Brent's tolerance,
# so the difference spans more than the optimiser's own resolution of the slope.
S5_SIGMA_FD = 1e-3
# S6: the confirmation tolerance of decision 51's rescale (PLAN.md 5.2 S6).
S6_TOL = 1e-12
# Amendment D13's declaration, written into S4's report at every form and into the
# ladder's reason whenever form A fails E1a. The contract (section 2.4; JSON
# model_form.in_sample_stage, as decision 77 reads it) governs the ladder: the next form
# is fitted whenever any in-sample statistic but E8 fails -- by decision 77, whenever
# |E_cal| - 2 u_stat > R (epa_stats.in_sample_outcome) -- E1a included, and nothing here
# changes that; the declaration governs how such a step is READ.
D13_DECLARATION = (
    "amendment D13: an E1a miss on stoichiometric hot rows at form A is read as a burn/FMEP residual that "
    "no form B-D can act on (mistake 20); it is reported, with S4's residuals per line and per population, "
    "and never used to justify a form. The ladder still moves by the contract's criterion (section 2.4).")
# verify: a shortcut equals the plant within this, relative (PLAN.md 5.2 Verify);
# S2's air shortcut within 1e-12 (mistake 10).
VERIFY_REL = 1e-9
S2_VERIFY_REL = 1e-12

# The Ford's Cell 9 rows and the octane (docs/build_step_2/HANDOFFS.md WP3 item 5,
# chosen in WP3_INTERFACES.md 5.3): declared, and measured by octane_moves_only_knock.
FORD_CELL9_OCTANE = (
    "The Ford's Cell 9 rows run at the engine's typed octane (engine_specs/ford_27tt.toml "
    "[cycle] octane, HD1's batch, decision 69), not at their own batch's: engines.with_fuel "
    "moves the heating value and AFR_st only, and the octane is the cycle record's. The octane "
    "enters plant.run_cycle only through the knock delay, so it moves only knock_integral and "
    "knock_prob (epa_fit.octane_moves_only_knock measures this at the fit, mistake 24); no "
    "Cell 9 row is compared on either, since S6 and E6 row 7 use the High Load Final rows, "
    "HD1's, on that batch.")

# The cycle fields a candidate's derived file holds (engines.EPA_DERIVED_FIELDS),
# in its order, and the forms' neutral values (PLAN.md 5.8: "terms a form does not
# use are written at their neutral values").
CYCLE_FIELDS = tuple(k for (rec, k) in engines.EPA_DERIVED_FIELDS if rec == "cycle")
ECU_FIELDS = tuple(k for (rec, k) in engines.EPA_DERIVED_FIELDS if rec == "ecu")
# Every worker of ordered_map appends each path its audit hook records here
# (calibrate_epa.worker_init installs the hook; WP3_INTERFACES.md 3.3), and each
# task's result travels back with the paths seen while it ran; the parent's
# ordered_map extends POOL_OPENED with them, in task order, so run.json is
# deterministic. No queue or file is written from inside a hook.
WORKER_OPENED = []
POOL_OPENED = []


# ---------------------------------------------------------------------------
# Records (WP3_INTERFACES.md 5.3)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Convergence:
    """How a least-squares stage ended (mistake 15: a convergence claim needs a
    convergence measurement). cost is SciPy's (half the sum of squares); grad_norm
    its first-order optimality (the scaled gradient's largest component, what gtol
    tests); last_step_norm the scaled length of the last accepted step and
    cost_change that step's decrease of cost, both read off the accepted iterates
    (an evaluation whose cost is below every earlier one's)."""
    nfev: int
    njev: int
    status: int
    message: str
    cost: float
    grad_norm: float
    last_step_norm: float
    cost_change: float
    second_attempt: bool


@dataclass(frozen=True)
class StageResult:
    """One stage's outcome: the constants it set (Python scalars, amendment B10),
    the rows it used and the ones it left out by reason, its pre-declared flags
    (PLAN.md 5.6), the parameters at a bound, its convergence, and a report whose
    keys WP3_INTERFACES.md 7.2 lists per stage."""
    stage: str
    values: dict
    rows_used: int
    rows_excluded: dict
    flags: tuple
    bounds_active: tuple
    convergence: object
    report: dict


@dataclass(frozen=True)
class FormFit:
    """One form, fitted: its stages, the derived file's frozen sections it gives
    (`values`: cycle, ecu, boost_ceiling, terms the form does not use at their
    neutral values, PLAN.md 5.8), their hash by engines.frozen_sections_sha256 (the
    one definition; mistake 10) and every flag its stages raised."""
    engine: str
    form: str
    stages: dict
    values: dict
    frozen_sections_sha256: str
    flags: tuple

    def as_json(self):
        return _py({"engine": self.engine, "form": self.form,
                    "stages": {k: dataclasses.asdict(v) for k, v in self.stages.items()},
                    "values": self.values, "frozen_sections_sha256": self.frozen_sections_sha256,
                    "flags": list(self.flags)})


@dataclass(frozen=True)
class Ladder:
    """The per-engine ladder (decision 49): every form fitted, in order, each
    form's in-sample stage (decision 77's outcome per statistic: form_record), and
    the form chosen with the reason."""
    engine: str
    fits: tuple
    in_sample: dict
    chosen: str
    reason: str


@dataclass(frozen=True)
class Truth:
    """A T0 truth (PLAN.md 5.10, amendment D11): the derived-file values the
    synthetic rows are made from, the form the ladder should stop at, and, for the
    seed whose truth lies outside every form, the term added outside the plant."""
    engine: str
    seed: int
    label: str
    values: dict
    expected_form: str
    out_of_form: object


class FitDefect(RuntimeError):
    """A coding defect (PLAN.md 5.6): an assertion of the fit failed -- a shortcut
    that is not the plant, a Jacobian column that is zero at the start, a count.
    Never a fit outcome: those are flags."""


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------
def _py(x):
    """x with every NumPy scalar a Python one, every array and tuple a list, and
    every non-finite float None, so that a report is JSON with allow_nan=False and
    canonical (WP3_INTERFACES.md 2.6; amendment B10)."""
    if isinstance(x, dict):
        return {str(k): _py(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_py(v) for v in x]
    if isinstance(x, np.ndarray):
        return [_py(v) for v in x.tolist()]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        v = float(x)
        return v if math.isfinite(v) else None
    if dataclasses.is_dataclass(x) and not isinstance(x, type):
        return _py(dataclasses.asdict(x))
    return x


def json_safe(obj):
    """_py, public: a record's values as plain JSON (NumPy scalars as Python ones, tuples as lists, a
    non-finite float as None), for the records calibrate_epa.py writes from what the stages and the
    completion return (WP3's integration, 23 October 2026)."""
    return _py(obj)


def canonical(obj):
    """The canonical JSON bytes of `obj` (WP3_INTERFACES.md 4: epa_rows.canonical_json,
    the one form every record hash uses), after _py."""
    return epa_rows.canonical_json(_py(obj))


def _key(row):
    return (row.table, int(row.source_row))


def _bits(v):
    """A float's eight bytes (NaN-safe: two NaNs compare by payload, -0.0 is not 0.0)."""
    return struct.pack("<d", float(v))


def _same_result(a, b, *, skip=()):
    """Whether two plant.CycleResult are the same doubles, field by field, but `skip`."""
    return all(_bits(getattr(a, f.name)) == _bits(getattr(b, f.name))
               for f in dataclasses.fields(a) if f.name not in skip)


def assert_one_blas_thread():
    """PLAN.md 5.1: one BLAS thread, asserted. The variables are read by the BLAS
    when NumPy is first imported, so the parent sets them before any import
    (calibrate_epa.py) and every spawn worker inherits them."""
    for var in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if os.environ.get(var) != "1":
            raise FitDefect(f"{var} is {os.environ.get(var)!r}, not '1': the fit runs on one BLAS "
                            "thread (PLAN.md 5.1), set before NumPy is imported")
    # scipy-openblas reads OPENBLAS_NUM_THREADS before OMP_NUM_THREADS: unset or 1 (WP3's third fix of 24
    # October 2026, on the Run 1 review's finding)
    if os.environ.get("OPENBLAS_NUM_THREADS", "1") != "1":
        raise FitDefect(f"OPENBLAS_NUM_THREADS is {os.environ.get('OPENBLAS_NUM_THREADS')!r}, not unset or '1': "
                        "OpenBLAS reads it before OMP_NUM_THREADS (PLAN.md 5.1)")


# ---------------------------------------------------------------------------
# The ordered pool (PLAN.md 5.1; WP3_INTERFACES.md 3.3)
# ---------------------------------------------------------------------------
_POOLS = {}


def _pool_init(initializer):
    assert_one_blas_thread()
    if initializer is not None:
        fn, args = initializer
        fn(*args)


def _pool_task(packed):
    fn, item = packed
    out = fn(item)
    seen = list(WORKER_OPENED)
    del WORKER_OPENED[:]
    return out, seen


def _pool(jobs, initializer):
    key = (jobs, None if initializer is None else (initializer[0].__module__, initializer[0].__qualname__,
                                                   tuple(initializer[1])))
    if key not in _POOLS:
        ctx = multiprocessing.get_context("spawn")
        _POOLS[key] = ctx.Pool(jobs, initializer=_pool_init, initargs=(initializer,))
    return _POOLS[key]


def close_pools(*, terminate=False):
    """Close every pool ordered_map opened (calibrate_epa.py calls it at exit; the
    tests call it in tearDownModule). `terminate`: kill the workers instead of
    waiting for them (Pool.terminate, then join), as calibrate_epa.invoke does when
    its body did not end ok: a pool whose worker died mid-task (a Ctrl+C reaching
    the workers' console, a native crash) never completes that task, and close()
    then join() waits for it forever, so run.json's crash entry was never written
    (WP3's fourth fix of 24 October 2026, on the fourth Run 1 review's finding)."""
    for p in _POOLS.values():
        if terminate:
            p.terminate()
        else:
            p.close()
        p.join()
    _POOLS.clear()


def ordered_map(fn, items, *, jobs, initializer):
    """[fn(item) for item in items], in submission order whatever the workers'
    timing (PLAN.md 5.1). `jobs` 1 runs in this process; more runs a spawn pool of
    that many workers, kept open for the next call (a pool's start costs seconds,
    a cycle milliseconds). `initializer` is None or (callable, args): run in every
    worker after the one-BLAS-thread assertion -- calibrate_epa.worker_init, which
    installs the audit hook (WP3_INTERFACES.md 3.3; amendment C3: a parent's hook
    does not see a spawn worker). Each task's result comes back with the paths the
    worker's hook appended to WORKER_OPENED while it ran; they are added to
    POOL_OPENED in task order. `fn` and every item must pickle. Both keywords are
    required: no call relies on a default."""
    if type(jobs) is not int or jobs < 1:
        raise ValueError(f"jobs must be an int >= 1, not {jobs!r}")
    items = list(items)
    if jobs == 1 or len(items) <= 1:
        return [fn(it) for it in items]
    assert_one_blas_thread()
    chunk = max(1, len(items) // (4 * jobs))
    out = _pool(jobs, initializer).map(_pool_task, [(fn, it) for it in items], chunksize=chunk)
    res = []
    for r, seen in out:
        res.append(r)
        POOL_OPENED.extend(seen)
    return res


# ---------------------------------------------------------------------------
# The plant at a row (PLAN.md 5.1; WP3_INTERFACES.md 5.2.2 and 5.3)
# ---------------------------------------------------------------------------
def _fuel_record(table_fuel):
    """An engines.Fuel from an epa_rows.TableFuel (or anything carrying lhv_j_per_kg
    and afr_st), as Python floats (amendment B10)."""
    return engines.Fuel(lhv_j_per_kg=float(table_fuel.lhv_j_per_kg), afr_st=float(table_fuel.afr_st))


def _cycle_at(engine, x, *, dtheta, ecu_engine):
    """plant.run_cycle at a row's inputs `x` (epa_stats.RowInputs: rpm, map_kpa,
    iat_k, ect_k, spark_btdc, lam) with `engine` (already on the row's fuel) -- THE
    one definition of the model at a row (PLAN.md 5.1; JSON conventions.inputs_fed):
    EPA's inputs, the model's own back-pressure law, and on a form-D engine the cam
    its ECU schedules at the row's MAP (decision 41), from `ecu_engine`'s ECU."""
    cam = engine_env.BaselineECU(ecu_engine.ecu).cam_deg(x.rpm, x.map_kpa)
    op = plant_model.Operating(rpm=x.rpm, map_kpa=x.map_kpa, iat_k=x.iat_k, ect_k=x.ect_k,
                               spark_btdc=x.spark_btdc, lam=x.lam,
                               p_exh_kpa=plant_model.exhaust_backpressure_kpa(x.map_kpa, engine=engine))
    return plant_model.run_cycle(op, engine=engine, dtheta=dtheta, cam_deg=cam)


def _cycle_job(job):
    """A picklable cycle: (engine, x, dtheta) -> plant.CycleResult."""
    engine, x, dtheta = job
    return _cycle_at(engine, x, dtheta=dtheta, ecu_engine=engine)


class RowModel:
    """The calibrated model as the statistics see it (WP3_INTERFACES.md 5.2.2):
    `plant`, an engines.Plant (a candidate during the fit), run at a row's inputs
    on the row's own fuel (results/ENGINE_THRESHOLDS.md section 3, decision 69).
    `fuels` maps each table to its epa_rows.TableFuel; the engine on each table's
    fuel is built once here by engines.with_fuel, which moves the cycle's and the
    network's heating value together. A row whose inputs carry another fuel (E6
    rows 2 and 3) gets its own engine, cached by the fuel's two doubles. Picklable,
    so a spawn worker runs the same plant."""

    def __init__(self, plant, *, fuels):
        if not isinstance(plant, engines.Plant):
            raise TypeError(f"RowModel needs an engines.Plant, not {type(plant).__name__}")
        self.plant = plant
        self.fuels = dict(fuels)
        self._engines = {}
        for tf in self.fuels.values():
            self._engine_for(tf)

    def _engine_for(self, table_fuel):
        f = _fuel_record(table_fuel)
        k = (_bits(f.lhv_j_per_kg), _bits(f.afr_st))
        if k not in self._engines:
            self._engines[k] = engines.with_fuel(self.plant.engine, f)
        return self._engines[k]

    def result(self, x, *, dtheta):
        """The full plant.CycleResult at inputs x."""
        return _cycle_at(self._engine_for(x.fuel), x, dtheta=dtheta, ecu_engine=self.plant.engine)

    def cycle(self, x, *, dtheta):
        r = self.result(x, dtheta=dtheta)
        return epa_stats.ModelOut(torque_nm=r.torque_nm, fuel_gps=r.mdot_fuel_gps, air_gps=r.mdot_air_gps,
                                  egt_c=r.egt_c, knock_integral=r.knock_integral, eta_v=r.eta_v)

    def _ecu(self):
        return engine_env.BaselineECU(self.plant.engine.ecu)

    def ecu_at(self, rpm, map_kpa, iat_k, ect_k):
        """A fresh BaselineECU's one step at dwell 30 s, no knock (results/
        ENGINE_THRESHOLDS.md section 4 E8; decision 54: EPA's intake temperature)."""
        ecu = self._ecu()
        spark, lam, _fan = ecu.step(rpm, map_kpa, iat_k, ect_k, False, S3B_DWELL_S)
        return epa_stats.EcuOut(spark_btdc=spark, lam=lam, cam_deg=ecu.cam_deg(rpm, map_kpa))

    def base_spark(self, rpm, map_kpa):
        return self._ecu().base_spark(rpm, map_kpa)

    def cam(self, rpm, map_kpa):
        return self._ecu().cam_deg(rpm, map_kpa)

    def ecu_trace(self, rpm, map_kpa, iat_k, ect_k, dt):
        """The ECU run along a trace, its dwell timer included (C3's chain)."""
        ecu = self._ecu()
        sp, lm = [], []
        for r, m, i, e in zip(rpm, map_kpa, iat_k, ect_k):
            s, l, _fan = ecu.step(float(r), float(m), float(i), float(e), False, dt)
            sp.append(s)
            lm.append(l)
        return np.array(sp), np.array(lm)

    def charge(self, t_amb_k, t_block_k):
        return plant_model.charge_temperature(t_amb_k, t_block_k, engine=self.plant.engine)


# ---------------------------------------------------------------------------
# The rows the fit may read (amendment C1; WP3_INTERFACES.md 5.1 and 5.3)
# ---------------------------------------------------------------------------
WORKER_INIT = None


def set_worker_init(initializer):
    """The (callable, args) every pool worker runs (calibrate_epa.py passes its
    worker_init, which installs the audit hook, amendment C3); None in the tests.
    A module setting rather than a keyword on every stage, so that the stages'
    signatures stay WP3_INTERFACES.md's."""
    global WORKER_INIT
    WORKER_INIT = initializer


def _map(fn, items, jobs):
    return ordered_map(fn, items, jobs=jobs, initializer=WORKER_INIT)


def cal_rows(yield_):
    """The rows a fit may use: the yield's steady and High Load Final rows, each of
    type exactly epa_rows.SteadyRow or epa_rows.FinalRow (WP3_INTERFACES.md 5.1,
    chosen there: a held-out row is a different type with the same fields, so it
    cannot slip into a fit by being the same class). The yield's High Load Initial
    rows are calibration rows but no fit's (results/ENGINE_THRESHOLDS.md 2.3: their
    torque serves only the descriptive comparison), and are skipped. Anything else
    -- a HeldOutRow, a HeldOutInitialRow, a dict -- is refused. `yield_` is an
    epa_rows.Yield or a sequence of rows (T0's synthetic rows)."""
    rows = getattr(yield_, "rows", yield_)
    out = []
    for r in rows:
        t = type(r)
        if t is epa_rows.SteadyRow or t is epa_rows.FinalRow:
            out.append(r)
        elif t is epa_rows.InitialRow:
            continue
        else:
            raise TypeError(f"epa_fit.cal_rows: a {t.__name__} is not a calibration row (only epa_rows."
                            "SteadyRow and epa_rows.FinalRow enter a fit; WP3_INTERFACES.md 5.1)")
    return tuple(out)


def _final(r):
    return type(r) is epa_rows.FinalRow


def _no_sentinel(r):
    """Decision 54: a sentinel row (EPA's -120 or an empty spark cell) enters no fit."""
    return not r.spark_sentinel


def _has_lam(r):
    return (not r.lambda_missing) and r.lam_meas is not None


def _finite(v):
    return v is not None and math.isfinite(v)


def _s2_use(rows):
    """S2's rows (PLAN.md 5.2 S2): fired, with a meter and a lambda (the calibration
    air needs both), no sentinel row (decision 54). One definition, for S2 and for
    verify's check of S2's shortcut at the final candidate (mistake 10)."""
    return [r for r in rows if r.pops.fired_meter and _has_lam(r) and _no_sentinel(r)]


def _s4_use(rows):
    """S4's rows (PLAN.md 5.2 S4): the fired rows of the lambda~1 band, which run at
    lambda 1.00, no sentinel row. One definition, for S4 and verify."""
    return [r for r in rows if r.pops.fired_l1 and _no_sentinel(r)]


def _cal_lines(view):
    """The calibration lines, in the view's order (view.lines less view.held_out_lines)."""
    held = set(view.held_out_lines)
    return tuple(l for l in view.lines if l not in held)


def _line_speeds(lines):
    """Every nominal speed of the given lines, sorted (a merged line is named by its
    speeds joined with '/', thresholds/split.py name())."""
    return tuple(sorted({float(s) for l in lines for s in str(l).split("/")}))


def _rpm_ends(view):
    """[rpm_min, rpm_max]: the engine's end lines (amendment C13 cites them to JSON
    lines; the end lines are never held out), the range ve_rpm may take (D9). That
    claim is asserted, not assumed (WP3's fix of 23 October 2026): both end speeds
    must be speeds of the calibration lines, else the bound would come from a
    held-out line, a coding defect."""
    sp = _line_speeds(view.lines)
    cal = set(_line_speeds(_cal_lines(view)))
    if sp[0] not in cal or sp[-1] not in cal:
        raise FitDefect("ve_rpm's bounds would come from a held-out line: an end line of the view is held out "
                        "(amendment C13 says the end lines never are)")
    return sp[0], sp[-1]


def _scales(view):
    """The residual scales, read from the contract's R through the view (PLAN.md
    5.1: "Residuals are expressed in units of the gated statistic's R: torque and
    efficiency 1.9 %, air and fuel 4.0 %, TIT 10 K"): E1a's R for torque and
    efficiency, E2a's for air, E3a's for TIT. The contract's own numbers, never a
    second copy (mistake 10)."""
    def one(row):
        v = view.R[row]
        r, unit = (v["R"], v["unit"]) if isinstance(v, dict) else (v[0], v[1])
        r = float(r)
        return r / 100.0 if str(unit).lstrip().startswith("%") else r
    return {"eff": one("E1a"), "air": one("E2a"), "tit": one("E3a")}


def _inputs(rows, *, view, conventions, model):
    """Each row's epa_stats.RowInputs under `conventions`, on the row's own table's
    fuel after the conventions' overrides (epa_stats.fuel_of): the one definition of
    what is fed (results/ENGINE_THRESHOLDS.md section 3). epa_stats.row_inputs takes
    the resolved fuel in place of the interface's view (its docstring says why)."""
    return tuple(epa_stats.row_inputs(r, fuel=epa_stats.fuel_of(r, view=view, conventions=conventions),
                                      conventions=conventions, model=model) for r in rows)


def _b58_cycle():
    """The B58's typed cycle record: the ridge's centre and form A's start (PLAN.md
    5.2: "the centre is the B58's value"), read at call time, never retyped.
    typed_engine reads engine_specs/b58.toml only (no derived file)."""
    return engines.typed_engine("b58").cycle


def ridge_centre():
    """RIDGE_CENTRE (WP3_INTERFACES.md 5.3): the B58's value for each A term, 0 for
    the B and D terms, the shared slope for C (PLAN.md 5.2)."""
    c = _b58_cycle()
    out = {k: float(getattr(c, k)) for k in S4_PARAMS + ("ve_rpm", "ve_width")}
    out.update(ve_map=0.0, ve_cam=0.0, ce_rich_slope=float(engines.SHARED_RICH_SLOPE))
    return out


def _terms(form):
    if form not in engines.CYCLE_FORMS:
        raise ValueError(f"form {form!r} is not one of {engines.CYCLE_FORMS}")
    return set(form.split("+"))


def _completion():
    return json.loads(json.dumps(PROVISIONAL_COMPLETION))


def _placeholder_values(name, form):
    """A dict shaped like the derived file that builds (engines.build_candidate):
    the B58's typed cycle constants for every fitted cycle field, an ECU that never
    enriches, a flat envelope, the provisional completion. Used only to reach the
    engine's TYPED records and functions (its geometry, its ECU's IAT compensation
    and dwell times, its inlet) before the stages have set anything; no number of it
    reaches a stage's output."""
    c = _b58_cycle()
    terms = _terms(form)
    cyc = {k: (form if k == "form" else float(getattr(c, k))) for k in CYCLE_FIELDS}
    cyc["ve_map"], cyc["ve_cam"] = 0.0, 0.0
    cyc["ce_rich_slope"] = float(engines.SHARED_RICH_SLOPE)
    ecu = {k: 0.0 for k in ECU_FIELDS}
    ecu.update(spark_min=-90.0, spark_max=90.0, enr_load=1.0e6, enr_rpm_lo=0.0, enr_rpm_hi=1.0,
               enr_depth=0.0, cam_on=1 if "D" in terms else 0)
    out = {"cycle": cyc, "ecu": ecu,
           "boost_ceiling": {"envelope_flow": [0.0, 1.0], "envelope_pr": [1.0, 1.0], "pr_cap": 1.0}}
    out.update(_completion())
    return out


def candidate(name, values):
    """engines.build_candidate(name, the frozen sections of `values` and the
    provisional completion): the plant the fit evaluates (mistake 10: what is fitted
    is what get() later builds from the file)."""
    v = {k: values[k] for k in engines.FROZEN_SECTIONS}
    v.update(_completion())
    return engines.build_candidate(name, v)


def _base_plant(name, form):
    return engines.build_candidate(name, _placeholder_values(name, form))


def _deep(v):
    return json.loads(json.dumps(v))


# ---------------------------------------------------------------------------
# S0: the channel checks, on the yield only (PLAN.md 4.4 and 5.2 S0; amendments C1, C2)
# ---------------------------------------------------------------------------
def _lowest_final_map(rows):
    fm = [r.map_kpa for r in rows if _final(r)]
    if not fm:
        raise FitDefect("no calibration High Load Final row: S3a's start, S3b's grid and S3c's "
                        "envelope all read them (amendment C1)")
    return float(min(fm))


def _cell_rule(rows, attr):
    """A cell quantity for the rows that publish none (the Ford HD1 publishes neither
    cell pressure nor cell temperature): the median over the engine's calibration
    rows that publish it -- on the Ford, Cell 9's -- swept over their range
    (decision 53, amendment C1, for the barometer). The cell temperature follows the
    same rule, chosen here: S3c's corrected flow needs it, and decision 53 names
    only the barometer. None when every row publishes its own."""
    have = [float(getattr(r, attr)) for r in rows if _finite(getattr(r, attr))]
    if not have or len(have) == len(rows):
        return None
    return {"median": float(np.median(have)), "sweep": [min(have), max(have)], "from_rows": len(have)}


def _lam_target(r, conventions):
    """S3b's target, E8's own lambda (PLAN.md 5.2 S3b): EPA's, unsnapped and
    cell-referenced (epa_stats.lam_cellref); as published under E6 row 1's
    convention (conventions.cell_referenced False)."""
    if conventions.cell_referenced:
        return float(epa_stats.lam_cellref(r))
    return float(r.lam_meas)


# What the invariant's edge is, as stage0.json and S3b's report disclose it (amendment C13; WP3's fix of
# 23 October 2026, on the isolation and fit reviews): lam_floor is the contract's lambda clip floor, an
# ALL-ROW quantity, round(min(0.70, the deepest lambda over every row - 0.01), 3), held-out and Initial rows
# included (amendment C1). C1 says it serves the policy clip and the dump only and that P2's invariant stays
# an assertion; HANDOFFS.md WP3 item 1 asks the depth to respect the invariant, so the two authorities meet
# here, and the edge is flagged whenever it is the active one (an open item for the team before Run 1).
INVARIANT_EDGE_SOURCE = ("the contract's all-row lambda clip floor (lambda_clip_floor.floor: round(min(0.70, the "
                         "deepest lambda over every row - 0.01), 3), held-out and Initial rows included; amendment "
                         "C1, a C13 disclosure)")


def depth_edges(rows, *, lam_floor, conventions):
    """S3b's upper bound on the enrichment depth (amendment C1; HANDOFFS.md WP3 item
    1): min(C1's bound, the invariant's edge). C1's bound is 1 - (the least lambda of
    the calibration Final rows - 0.01), on S3b's own lambda, over every calibration
    Final row that publishes a lambda, sentinel rows included: C1 writes it over the
    yielded Final rows, and a sentinel's empty or -120 spark says nothing of its
    lambda (WP3's fix of 23 October 2026; the depth itself is still fitted on no
    sentinel row, decision 54). The invariant's edge is the largest double d with
    1.0 - d >= lam_floor, so that engines.Engine accepts the depth to the bit (1.0 -
    (1.0 - x) can land an ulp below x); lam_floor is an all-row quantity
    (INVARIANT_EDGE_SOURCE). `active` names the edge that is the bound, and
    `invariant_active` with `c1_minus_invariant` flag an active all-row edge."""
    lams = [_lam_target(r, conventions) for r in rows if _final(r) and _has_lam(r)]
    c1 = (1.0 - (min(lams) - 0.01)) if lams else None
    inv = 1.0 - float(lam_floor)
    while 1.0 - inv < lam_floor:
        inv = float(np.nextafter(inv, 0.0))
    # and up, while the next double still keeps 1 - d >= lam_floor (1 - d rounds,
    # so the first d found need not be the largest): a few ulps at most
    while 1.0 - float(np.nextafter(inv, 1.0)) >= lam_floor:
        inv = float(np.nextafter(inv, 1.0))
    upper = inv if (c1 is None or inv <= c1) else c1
    active = "invariant" if (c1 is None or inv <= c1) else "C1"
    return {"c1": c1, "invariant": float(inv), "upper": float(upper), "active": active,
            "invariant_source": INVARIANT_EDGE_SOURCE, "invariant_active": active == "invariant",
            "c1_minus_invariant": None if c1 is None else float(c1 - inv)}


def _range(vals):
    v = [float(x) for x in vals if x is not None and math.isfinite(x)]
    return [min(v), max(v)] if v else None


def _count_attr(rows, attr, want):
    if not rows or not all(hasattr(r, attr) for r in rows):
        return None
    return sum(1 for r in rows if bool(getattr(r, attr)) is want)


def s0(yield_, *, view):
    """S0, PLAN.md 4.4's channel checks, on the loader's yield only (amendment C2:
    no held-out cell and no all-row aggregate is read): the fired rows without
    lambda by population; the fired sentinel rows, a declared outcome (decision 54,
    never asserted to be zero); the censoring test on the calibration Final rows
    (epa_stats.censoring, the one definition); turbine-inlet pressure below the
    barometer, its count and largest deficit (decision 52), the HD1's rows judged
    against decision 53's barometer; coolant against oil (mistake 13); the meter
    against EPA's injector estimate (mistake 14); the cam channel's name, sign and
    range; and the bounds C1 derives from the rows (S3a's start, S3b's gate edge and
    depth edges, S3d's domain and clamp). Counts and arithmetic only."""
    rows = cal_rows(yield_)
    finals = [r for r in rows if _final(r)]
    lm = [r for r in rows if r.lambda_missing]
    sen = [r for r in rows if r.spark_sentinel]
    cens = epa_stats.censoring(finals)
    lam_c = [float(epa_stats.lam_cellref(r)) for r in finals if _has_lam(r)]
    baro_rule = _cell_rule(rows, "baro_kpa")

    def baro(r):
        if _finite(r.baro_kpa):
            return float(r.baro_kpa)
        return None if baro_rule is None else baro_rule["median"]

    tip_rows = [r for r in rows if r.pops.fired and _finite(r.tip_kpa)]
    with_baro = [r for r in tip_rows if baro(r) is not None]
    below = [r for r in with_baro if r.tip_kpa < baro(r)]
    by_table = {}
    for r in rows:
        by_table.setdefault(r.table, []).append(r)
    coolant = {t: {"rows": len(rr),
                   "identical": sum(1 for r in rr if _finite(r.oil_k) and r.ect_k == r.oil_k),
                   "all_identical": all(_finite(r.oil_k) and r.ect_k == r.oil_k for r in rr)}
               for t, rr in sorted(by_table.items())}
    meter = {}
    for t, rr in sorted(by_table.items()):
        q = [r.fuel_meter_gps / r.injector_fuel_gps for r in rr
             if _finite(r.fuel_meter_gps) and _finite(r.injector_fuel_gps) and r.injector_fuel_gps > 0]
        meter[t] = {"n": len(q), "median_ratio": float(np.median(q)) if q else None,
                    "p10": float(np.percentile(q, 10)) if q else None,
                    "p90": float(np.percentile(q, 90)) if q else None}
    cam_rows = [r for r in rows if _finite(r.cam_cad)]
    channels = sorted({r.cam_channel for r in cam_rows if r.cam_channel})
    one = channels[0] if len(channels) == 1 else None
    lowest = _lowest_final_map(rows)
    edges = depth_edges(rows, lam_floor=float(view.lam_floor), conventions=epa_stats.NOMINAL)
    floor = float(view.hot_map_floor_kpa)
    near_floor = [r for r in rows if abs(float(r.map_kpa) - floor) <= HOT_FLOOR_HALF_ROUNDING_KPA]
    report = {
        "lambda_missing": {"fired": sum(1 for r in lm if r.pops.fired),
                           "fired_meter": sum(1 for r in lm if r.pops.fired_meter),
                           "hot": sum(1 for r in lm if r.pops.hot), "keys": [_key(r) for r in lm]},
        # epa_rows.PointRow marks both kinds of sentinel with spark_sentinel and
        # spark_btdc None (decision 54's reading of 23 October); EPA's -120 and an
        # empty cell are told apart only if the row carries spark_empty (None if not)
        "spark_sentinel": {"sentinel_value": _count_attr(sen, "spark_empty", False),
                           "empty_cell": _count_attr(sen, "spark_empty", True),
                           "total": len(sen), "fired": sum(1 for r in sen if r.pops.fired),
                           "keys": [_key(r) for r in sen]},
        "censoring": {"final_rows_with_lambda": len(lam_c),
                      "min_lambda_cellref": min(lam_c) if lam_c else None,
                      "n_at_min_within_1e-9": int(cens.n_at_min), "censored": bool(cens.censored),
                      "value": cens.value, "documented_floor": cens.documented_floor, "rule": cens.rule},
        "tip_below_barometer": {
            "fired_rows_with_barometer": len(with_baro), "below": len(below),
            "largest_deficit_kpa": max(baro(r) - float(r.tip_kpa) for r in below) if below else None,
            "keys": [_key(r) for r in below],
            "hd1_barometer": None if baro_rule is None else {
                "median_kpa": baro_rule["median"], "sweep_kpa": baro_rule["sweep"],
                "from_rows": baro_rule["from_rows"]}},
        "coolant_vs_oil": coolant,
        "meter_vs_injector": meter,
        "cam": {"channel": one if one is not None else (channels or None),
                "direction": (None if one is None else "ret" if one.endswith("_ret")
                              else "adv" if one.endswith("_adv") else None),
                "rows_with_cam": len(cam_rows), "rows_without": len(rows) - len(cam_rows),
                "rpm_range": _range(r.speed_rpm for r in cam_rows),
                "map_range_kpa": _range(r.map_kpa for r in cam_rows),
                "cam_range_cad": _range(r.cam_cad for r in cam_rows),
                "median_cad": float(np.median([r.cam_cad for r in cam_rows])) if cam_rows else None},
        # the calibration rows whose MAP lies within half the contract's printed rounding of its hot floor:
        # split.compute classified every row at the unrounded floor, the loader at the printed one, so such a
        # row could sit in another population here (counts and keys only; a non-empty list is a declared
        # outcome, flagged; WP3's fix of 23 October 2026, on the contract review's finding)
        "hot_floor_rounding": {"printed_floor_rule": "round(floor, 2)", "half_width_kpa": HOT_FLOOR_HALF_ROUNDING_KPA,
                               "rows_within": len(near_floor), "keys": [_key(r) for r in near_floor]},
        "bounds": {"lowest_final_map_kpa": lowest, "s3a_start_map_kpa": lowest,
                   "s3b_gate_lo_kpa": min(lowest, S3B_GATE_DESIGN_KPA),
                   "s3b_depth_upper_c1": edges["c1"], "s3b_depth_upper_invariant": edges["invariant"],
                   "s3b_depth_upper": edges["upper"], "s3b_edge_active": edges["active"],
                   "s3b_depth_upper_invariant_source": edges["invariant_source"],
                   "s3b_invariant_edge_active": edges["invariant_active"],
                   "s3b_c1_minus_invariant": edges["c1_minus_invariant"],
                   "s3d_domain": {"rpm": _range(r.speed_rpm for r in cam_rows),
                                  "map_kpa": _range(r.map_kpa for r in cam_rows)},
                   "s3d_clamp_cad": _range(r.cam_cad for r in cam_rows)},
    }
    flags = []
    if any(r.pops.fired for r in sen):
        flags.append("S0_fired_sentinel_rows")          # decision 54: declared, never a stop
    if any(r.pops.fired for r in lm):
        flags.append("S0_fired_rows_without_lambda")
    if below:
        flags.append("S0_tip_below_barometer")          # decision 52: kept, refit as a sensitivity
    if cens.censored:
        flags.append("S0_lambda_censored")
    if near_floor:
        flags.append("S0_rows_at_the_rounded_hot_floor")   # declared: a population could differ from split's
    if edges["invariant_active"]:
        flags.append("S0_depth_edge_is_the_all_row_floor")  # C13: the depth's bound is an all-row quantity
    return StageResult(stage="S0", values={}, rows_used=len(rows), rows_excluded={}, flags=tuple(flags),
                       bounds_active=(), convergence=None, report=_py(report))


# ---------------------------------------------------------------------------
# S1: the back-pressure law (PLAN.md 5.2 S1; decision 52)
# ---------------------------------------------------------------------------
def _s1_solve(mp, tip):
    """min over (r, h) of sum (TIP - r max(h, MAP))^2: the hinge h profiled on
    S1_GRID_KPA over the rows' MAP range, r in closed form at each h within r in
    [1.0, 2.5] and r*h in [80, 140] kPa (the constrained one-dimensional minimum of
    a quadratic is the clipped one), the floor r*h. The plant's law, max(floor,
    ratio * MAP) (plant.exhaust_backpressure_kpa), is r * max(h, MAP) with h =
    floor / r, which fixes the ill-posed split. Ties go to the lowest hinge
    (np.argmin's first), chosen here: on a flat profile no row lies between the
    tied hinges. Hinges are integers times the step, so the grid has no drift."""
    (rlo, rhi), (flo, fhi) = BOUNDS["exh_bp_ratio"], BOUNDS["exh_bp_min_kpa"]
    k0 = int(math.ceil(float(min(mp)) / S1_GRID_KPA - 1e-9))
    k1 = int(math.floor(float(max(mp)) / S1_GRID_KPA + 1e-9))
    best = None
    for k in range(k0, k1 + 1):
        h = k * S1_GRID_KPA
        m = np.maximum(h, mp)
        lo, hi = max(rlo, flo / h), min(rhi, fhi / h)
        if lo > hi:
            continue
        r = float(np.clip(np.dot(m, tip) / np.dot(m, m), lo, hi))
        sse = float(np.sum((tip - r * m) ** 2))
        if best is None or sse < best[0]:
            best = (sse, float(h), r, lo, hi)
    if best is None:
        raise FitDefect("S1: no hinge on the grid admits a ratio in [1.0, 2.5] with a floor in [80, 140] kPa")
    return best


def s1_backpressure(rows, *, view):
    """S1 (PLAN.md 5.2): exh_bp_ratio and exh_bp_min_kpa on the fired steady and
    Final rows that publish a turbine-inlet pressure (no sentinel row, decision 54).
    Reported: sigma of both for E6 row 5, from the profiled least squares at the
    optimum and the residual variance (the hinge's column is zero when no row lies
    below the hinge: the floor's sigma is then None and flagged, amendment D10); the
    residual against rpm (the law has no rpm term: reported, never fitted); and
    decision 52's refit without the rows whose TIP is below their barometer (the
    HD1's judged against decision 53's), a sensitivity that moves nothing."""
    use = [r for r in rows if r.pops.fired and _finite(r.tip_kpa) and _no_sentinel(r)]
    excl = {"not_fired_or_no_tip": [_key(r) for r in rows if not (r.pops.fired and _finite(r.tip_kpa))],
            "sentinel": [_key(r) for r in rows
                         if r.pops.fired and _finite(r.tip_kpa) and not _no_sentinel(r)]}
    if len(use) < 3:
        raise FitDefect(f"S1 has {len(use)} rows with a turbine-inlet pressure; every EPA table publishes it "
                        "(PLAN.md 5.2 S1)")
    mp = np.array([r.map_kpa for r in use], dtype=float)
    tip = np.array([r.tip_kpa for r in use], dtype=float)
    rpm = np.array([r.speed_rpm for r in use], dtype=float)
    sse, h, ratio, rlo, rhi = _s1_solve(mp, tip)
    floor = ratio * h
    n = len(use)
    m = np.maximum(h, mp)
    J = np.column_stack([m, ratio * (mp < h).astype(float)])
    s2 = sse / max(n - 2, 1)
    flags, active = [], []
    sig = {"ratio": None, "floor_kpa": None}
    if np.all(J[:, 1] == 0.0):
        flags.append("S1_hinge_column_zero")            # amendment D10: no row below the hinge
        sig["ratio"] = float(math.sqrt(s2 / float(np.dot(m, m))))
    else:
        cov = s2 * np.linalg.inv(J.T @ J)
        sig["ratio"] = float(math.sqrt(max(cov[0, 0], 0.0)))
        g = np.array([h, ratio])                         # d(floor) = h d(r) + r d(h)
        sig["floor_kpa"] = float(math.sqrt(max(float(g @ cov @ g), 0.0)))
    if ratio in BOUNDS["exh_bp_ratio"]:
        active.append("exh_bp_ratio")
    elif ratio in (rlo, rhi):
        active.append("exh_bp_min_kpa")                  # the floor's bound, through r * h
    res = tip - ratio * m
    A = np.column_stack([np.ones(n), rpm / 1000.0])
    slope = float(np.linalg.lstsq(A, res, rcond=None)[0][1])
    baro_rule = _cell_rule(rows, "baro_kpa")

    def baro(r):
        return float(r.baro_kpa) if _finite(r.baro_kpa) else (None if baro_rule is None else baro_rule["median"])

    keep = [i for i, r in enumerate(use) if baro(r) is None or r.tip_kpa >= baro(r)]
    without = None
    if len(keep) < n:
        without = {"values": None, "rows_removed": n - len(keep)}
        if len(keep) >= 3:
            _s, hh, rr, _a, _b = _s1_solve(mp[keep], tip[keep])
            without["values"] = {"exh_bp_ratio": float(rr), "exh_bp_min_kpa": float(rr * hh)}
    if active:
        flags.append("S1_bound_active")
    return StageResult(
        stage="S1", values={"exh_bp_ratio": float(ratio), "exh_bp_min_kpa": float(floor)},
        rows_used=n, rows_excluded=_py(excl), flags=tuple(flags), bounds_active=tuple(active),
        convergence=None,
        report=_py({"hinge_kpa": h, "ratio": ratio, "floor_kpa": floor, "sigma": sig,
                    "residual_vs_rpm": {"slope_k_per_krpm": slope, "n": n, "unit": "kPa of TIP per 1000 rpm"},
                    "without_tip_below_barometer": without, "sse_kpa2": sse,
                    "grid_step_kpa": S1_GRID_KPA, "tie_rule": "the lowest hinge"}))


# ---------------------------------------------------------------------------
# S3a: the ECU's spark (PLAN.md 5.2 S3a; amendments C1, D3, D7)
# ---------------------------------------------------------------------------
_PIECES = ("part_load", "knock_limited")


def _lstsq(X, y):
    coef, _res, rank, _sv = np.linalg.lstsq(X, y, rcond=None)
    return coef, int(rank)


def s3a_spark(rows, *, plant, view):
    """S3a (PLAN.md 5.2): the part-load plane spark_a + spark_b*rpm - spark_c*(MAP -
    spark_ref_kpa) and the knock-limited surface kl_a + kl_b*rpm + kl_c*MAP +
    kl_d*MAP^2/1000 (engine_env.BaselineECU, the terms in its order), with spark_min
    and spark_max, on the fired steady and Final rows that publish a spark
    (sentinel rows enter no fit, decision 54).

    The target is EPA's spark less the ECU's IAT compensation at EPA's intake
    temperature, with the cold retard ADDED BACK where the coolant is below cold_k,
    because step() subtracts it (amendment D3 corrects the plan's sign).
    Alternating piecewise OLS: the rows below the lowest calibration Final MAP start
    on the plane and the rest on the surface (amendment C1, chosen in
    WP3_INTERFACES.md 5.3 over DESIGN 100 kPa); each row is then reassigned to the
    lower piece, the pieces refitted, until the assignment repeats (at most 50; else
    the visited assignment of least SSE, flagged). A piece needs S3A_MIN_ROWS rows
    and full column rank (amendment D7): an assignment that leaves one short stops
    the iteration at the last valid one, flagged. A start that leaves one short is a
    coding defect, raised: it would mean no fired part-load row below the holds.
    spark_min = floor(min over the rows of {EPA's spark, base, base + comp, base +
    comp - cold}) - 1 and spark_max = ceil(max of {EPA's spark, base}) + 1 (D3), so
    that at every row BaselineECU.step at dwell 30 s returns base + comp unclipped,
    which is asserted."""
    cal = plant.engine.ecu
    if cal.spark_ref_kpa != SPARK_REF_KPA:
        raise FitDefect(f"the engine spec types spark_ref_kpa {cal.spark_ref_kpa!r}, and epa_fit declares "
                        f"{SPARK_REF_KPA!r} (PLAN.md 9.2): two values for one number")
    ecu = engine_env.BaselineECU(cal)
    use = [r for r in rows if r.pops.fired and _no_sentinel(r) and _finite(r.spark_btdc)]
    excl = {"not_fired": [_key(r) for r in rows if not r.pops.fired],
            "sentinel": [_key(r) for r in rows if r.pops.fired and not _no_sentinel(r)]}
    rpm = np.array([r.speed_rpm for r in use], dtype=float)
    mp = np.array([r.map_kpa for r in use], dtype=float)
    sp = np.array([r.spark_btdc for r in use], dtype=float)
    comp = np.array([ecu.iat_compensation(r.imt_k) for r in use], dtype=float)
    cold = np.array([cal.cold_retard if r.ect_k < cal.cold_k else 0.0 for r in use], dtype=float)
    y = sp - comp + cold
    Xp = np.column_stack([np.ones(len(use)), rpm, -(mp - SPARK_REF_KPA)])
    Xk = np.column_stack([np.ones(len(use)), rpm, mp, mp ** 2 / 1000.0])
    lowest = _lowest_final_map(rows)

    def fit(z):
        out = {}
        for piece, X, sel in (("part_load", Xp, z), ("knock_limited", Xk, ~z)):
            n = int(sel.sum())
            if n < S3A_MIN_ROWS[piece]:
                return None, f"{piece}: {n} rows (fewer than {S3A_MIN_ROWS[piece]})"
            coef, rank = _lstsq(X[sel], y[sel])
            if rank < X.shape[1]:
                return None, f"{piece}: rank {rank} of {X.shape[1]}"
            out[piece] = (coef, n, rank)
        return out, None

    def sse(f):
        return float(np.sum((y - np.minimum(Xp @ f["part_load"][0], Xk @ f["knock_limited"][0])) ** 2))

    z = mp < lowest
    f, why = fit(z)
    if f is None:
        raise FitDefect(f"S3a's start (the rows below the lowest calibration Final MAP on the plane) leaves "
                        f"a piece short: {why} (amendment D7)")
    flags, visited, converged, it = [], [(sse(f), 0, z, f)], False, 0
    for it in range(1, S3A_MAX_ITER + 1):
        z_new = (Xp @ f["part_load"][0]) <= (Xk @ f["knock_limited"][0])
        if np.array_equal(z_new, z):
            converged = True
            break
        f_new, why = fit(z_new)
        if f_new is None:
            flags.append("S3a_empty_piece")              # D7: stop at the last valid assignment
            break
        z, f = z_new, f_new
        visited.append((sse(f), it, z, f))
    if not converged and "S3a_empty_piece" not in flags:
        flags.append("S3a_not_converged")                # PLAN.md 5.2: the least SSE visited
        s_best = min(v[0] for v in visited)
        _s, it, z, f = next(v for v in visited if v[0] == s_best)
    cp, ck = f["part_load"][0], f["knock_limited"][0]
    base = np.minimum(Xp @ cp, Xk @ ck)
    lo_vals = np.concatenate([sp, base, base + comp, base + comp - cold])
    spark_min = float(math.floor(float(lo_vals.min())) - 1)
    spark_max = float(math.ceil(float(np.concatenate([sp, base]).max())) + 1)
    vals = {"spark_a": float(cp[0]), "spark_b": float(cp[1]), "spark_c": float(cp[2]),
            "spark_min": spark_min, "spark_max": spark_max,
            "kl_a": float(ck[0]), "kl_b": float(ck[1]), "kl_c": float(ck[2]), "kl_d": float(ck[3])}
    # D3's check, through the ECU's own arithmetic: step() at dwell 30 s with no knock
    # returns base + comp - cold, unclipped, at every row
    e2 = engine_env.BaselineECU(replace(cal, **vals))
    unclipped = True
    for r in use:
        c = e2.cal
        fitted = c.spark_a + c.spark_b * r.speed_rpm - c.spark_c * (r.map_kpa - c.spark_ref_kpa)
        raw = (min(fitted, e2.knock_limited_spark(r.speed_rpm, r.map_kpa)) + e2.iat_compensation(r.imt_k)
               - (c.cold_retard if r.ect_k < c.cold_k else 0.0))
        out = engine_env.BaselineECU(c).step(r.speed_rpm, r.map_kpa, r.imt_k, r.ect_k, False, S3B_DWELL_S)[0]
        if not (c.spark_min < raw < c.spark_max and out == raw):
            unclipped = False
    if not unclipped:
        raise FitDefect("S3a: BaselineECU.step clips the fitted spark at a calibration row (amendment D3's "
                        "check)")
    on_plane = z.copy()
    return StageResult(
        stage="S3a", values=vals, rows_used=len(use), rows_excluded=_py(excl), flags=tuple(flags),
        bounds_active=(), convergence=None,
        report=_py({"iterations": it, "converged": converged,
                    "pieces": {"part_load": {"n": int(on_plane.sum()), "rank": f["part_load"][2]},
                               "knock_limited": {"n": int((~on_plane).sum()), "rank": f["knock_limited"][2]}},
                    "start_map_kpa": lowest,
                    "spark_min_rule": "floor(min over the rows of {EPA's spark, base, base + comp, "
                                      "base + comp - cold}) - 1 (amendment D3)",
                    "spark_max_rule": "ceil(max over the rows of {EPA's spark, base}) + 1",
                    "unclipped_at_every_row": unclipped, "cold_rows": int((cold > 0).sum()),
                    "rms_deg": float(math.sqrt(sse(f) / len(use))), "sse_deg2": sse(f)}))


# ---------------------------------------------------------------------------
# S3b: the ECU's enrichment (PLAN.md 5.2 S3b; amendments C1, D2; HANDOFFS.md WP3 item 1)
# ---------------------------------------------------------------------------
def _depth_1d(a, b, cens, d_max):
    """min over d in [0, d_max] of sum_u (b - a d)^2 + sum_c max(b - a d, 0)^2: the
    censored depth, a one-dimensional convex piecewise quadratic (amendment D2;
    wrong claim 23), solved exactly on each piece between the censored rows'
    breakpoints b/a. Returns (sse, d); of two depths with equal SSE, the lower."""
    pos = cens & (a > 0) & (b > 0)
    pts = sorted({0.0, d_max} | {float(p) for p in (b[pos] / a[pos]) if 0.0 < p < d_max})
    best = None
    for lo, hi in zip(pts[:-1], pts[1:]) if len(pts) > 1 else [(0.0, 0.0)]:
        mid = 0.5 * (lo + hi)
        act = (~cens) | (b - a * mid > 0)
        A = float(np.sum(a[act] ** 2))
        d = lo if A == 0.0 else min(max(float(np.sum(a[act] * b[act])) / A, lo), hi)
        r = b - a * d
        f = float(np.sum(np.where(cens, np.maximum(r, 0.0), r) ** 2))
        if best is None or f < best[0]:
            best = (f, d)
    return best


def _censored_mask(use, censoring):
    """The rows S3b treats one-sided: when the engine's lambda is censored
    (epa_stats.censoring, on the calibration Final rows), every row whose
    cell-referenced lambda sits at the censoring value within 1e-9, the scale
    epa_stats.censoring states its value on (results/ENGINE_THRESHOLDS.md section 3;
    epa_stats.mark_censored applies the same test)."""
    if not censoring.censored:
        return np.zeros(len(use), dtype=bool)
    v = float(censoring.value)
    return np.array([abs(float(epa_stats.lam_cellref(r)) - v) <= 1e-9 for r in use], dtype=bool)


def s3b_lambda(rows, *, plant, view, censoring, lam_floor, conventions):
    """S3b (PLAN.md 5.2, amendments C1 and D2): enr_load, enr_rpm_lo, enr_rpm_hi and
    enr_depth of the schedule lambda = 1 - depth * s(rpm) * t(dwell) above enr_load
    (engine_env.BaselineECU.base_lambda), at dwell 30 s, on the calibration Final
    rows that publish a lambda and the calibration steady rows that publish one (D2:
    they sit below the load where enrichment starts, and place the gate). The target
    is E8's lambda (_lam_target); censored rows count only where the schedule is
    above their reading. The gate runs on a 1 kPa grid from the lower of the lowest
    calibration Final MAP and DESIGN 100 kPa to the largest calibration Final MAP
    (C1); rpm_lo and rpm_hi on the calibration lines' speeds, rpm_lo also below the
    lowest line (D2), rpm_hi at least 300 rpm above rpm_lo; at each grid point the
    depth is the exact constrained minimum (_depth_1d) on [0, depth's upper edge]
    (depth_edges: C1's bound or the invariant's edge, whichever is lower, the active
    one reported; HANDOFFS.md WP3 item 1). Ties go to the highest gate (D2), then
    the lowest rpm_lo, then the lowest rpm_hi; the flat width is reported."""
    cal = plant.engine.ecu
    if float(cal.lam_floor) != float(lam_floor):
        raise FitDefect(f"the engine's ecu.lam_floor {cal.lam_floor!r} is not the contract's {lam_floor!r}")
    use = [r for r in rows if _has_lam(r) and _no_sentinel(r)]
    excl = {"no_lambda": [_key(r) for r in rows if not _has_lam(r)],
            "sentinel": [_key(r) for r in rows if _has_lam(r) and not _no_sentinel(r)]}
    rpm = np.array([r.speed_rpm for r in use], dtype=float)
    mp = np.array([r.map_kpa for r in use], dtype=float)
    y = np.array([_lam_target(r, conventions) for r in use], dtype=float)
    b = 1.0 - y
    cens = _censored_mask(use, censoring)
    t = float(np.clip((S3B_DWELL_S - cal.enr_dwell_lo) / (cal.enr_dwell_hi - cal.enr_dwell_lo), 0.0, 1.0))
    edges = depth_edges(rows, lam_floor=lam_floor, conventions=conventions)
    d_max = edges["upper"]
    fm = [r.map_kpa for r in rows if _final(r)]
    g_lo, g_hi = min(min(fm), S3B_GATE_DESIGN_KPA), max(fm)
    gates = [g_lo + k * S3B_GATE_STEP_KPA for k in range(int(math.floor((g_hi - g_lo) / S3B_GATE_STEP_KPA)) + 1)]
    speeds = _line_speeds(_cal_lines(view))
    lo_c = [speeds[0] - d for d in sorted(S3B_RPM_LO_BELOW, reverse=True)] + list(speeds)
    pairs = [(lo, hi) for lo in lo_c for hi in speeds if hi >= lo + S3B_RPM_SPAN_MIN]
    best, grid_hits_edge, table = None, False, {}
    for (lo, hi) in pairs:
        s = np.clip((rpm - lo) / (hi - lo), 0.0, 1.0)
        for g in sorted(gates, reverse=True):
            a = np.where(mp > g, s * t, 0.0)
            f, d = _depth_1d(a, b, cens, d_max)
            table[(g, lo, hi)] = f
            if d == d_max and d_max > 0:
                grid_hits_edge = True
            if best is None or f < best[0] or (f == best[0] and (-g, lo, hi) < (-best[1], best[2], best[3])):
                best = (f, g, lo, hi, d)
    sse, gate, lo, hi, depth = best
    flat = [g for g in gates if table[(g, lo, hi)] == sse]
    vals = {"enr_load": float(gate), "enr_rpm_lo": float(lo), "enr_rpm_hi": float(hi), "enr_depth": float(depth)}
    # engines.Engine's invariant on the fitted depth (HANDOFFS.md WP3 item 1: 1 - depth
    # >= lam_floor > 0): dataclasses.replace runs Engine.__post_init__, the check
    # build_candidate's constructor runs, so a depth on its edge is shown to build
    # here, at the stage, and not first at the candidate. A refusal is a coding
    # defect: depth_edges bounds the depth so that it cannot happen.
    try:
        replace(plant.engine, ecu=replace(cal, **vals))
    except ValueError as exc:
        raise FitDefect(f"S3b: the fitted enrichment breaks engines.Engine's invariant ({exc})") from exc
    # the schedule as the ECU computes it, at every row, against the grid's arithmetic
    e2 = engine_env.BaselineECU(replace(cal, **vals))
    s = np.clip((rpm - lo) / (hi - lo), 0.0, 1.0)
    lam_ecu = np.array([e2.base_lambda(r.speed_rpm, r.map_kpa, S3B_DWELL_S) for r in use])
    lam_grid = 1.0 - depth * np.where(mp > gate, s * t, 0.0)
    if np.max(np.abs(lam_ecu - lam_grid)) > 1e-12:
        raise FitDefect("S3b: BaselineECU.base_lambda is not the schedule the grid fitted (mistake 10)")
    steady_hot = [r for r in rows if not _final(r) and r.pops.hot]
    enriched = sum(1 for r in steady_hot if e2.base_lambda(r.speed_rpm, r.map_kpa, S3B_DWELL_S) < 1.0)
    above = mp > gate
    flags, active = [], []
    if depth == d_max:
        active.append("enr_depth")
        flags.append("S3b_depth_at_edge_" + edges["active"])
    if len(flat) > 1:
        flags.append("S3b_flat_profile")                 # PLAN.md 5.6: reported with its width, no hold
    # amendment C1: "report whether each bound is active at the optimum and anywhere on the S3b grid" -- the
    # gate's two grid edges and rpm_lo's and rpm_hi's extreme candidates, at the optimum and over the flat
    # interval, beside the depth's edge (WP3's fix of 23 October 2026, on the fit review's finding)
    edges_on = {"gate_lo": {"at_optimum": gate == gates[0], "on_flat_interval": min(flat) == gates[0]},
                "gate_hi": {"at_optimum": gate == gates[-1], "on_flat_interval": max(flat) == gates[-1]},
                "rpm_lo_lowest": {"at_optimum": lo == lo_c[0]}, "rpm_lo_highest": {"at_optimum": lo == lo_c[-1]},
                "rpm_hi_lowest": {"at_optimum": hi == speeds[0]}, "rpm_hi_highest": {"at_optimum": hi == speeds[-1]}}
    for k, v in edges_on.items():
        if any(v.values()):
            flags.append(f"S3b_{k}_edge")
            active.append({"gate_lo": "enr_load", "gate_hi": "enr_load"}.get(k, "enr_rpm_lo" if "rpm_lo" in k
                                                                              else "enr_rpm_hi"))
    if edges["invariant_active"] and depth == d_max:
        flags.append("S3b_depth_set_by_the_all_row_floor")   # C13: an all-row quantity bounds the frozen depth
    active = list(dict.fromkeys(active))
    return StageResult(
        stage="S3b", values=vals, rows_used=len(use), rows_excluded=_py(excl), flags=tuple(flags),
        bounds_active=tuple(active), convergence=None,
        report=_py({"grid": {"gate_lo_kpa": g_lo, "gate_hi_kpa": g_hi, "step_kpa": S3B_GATE_STEP_KPA,
                             "rpm_breakpoints": {"rpm_lo": lo_c, "rpm_hi": list(speeds)},
                             "dwell_s": S3B_DWELL_S, "t": t},
                    "flat_width_kpa": max(flat) - min(flat), "flat_gates_kpa": [min(flat), max(flat)],
                    "tie_rule": "the highest gate (amendment D2), then the lowest rpm_lo, then the lowest rpm_hi",
                    "rows_behind": {"enr_load": int(above.sum()),
                                    "enr_rpm_lo": int((above & (s > 0) & (s < 1)).sum()),
                                    "enr_rpm_hi": int((above & (s > 0) & (s < 1)).sum()),
                                    "enr_depth": int((above & (s > 0)).sum())},
                    "censored_rows": [_key(r) for r, c in zip(use, cens) if c],
                    "steady_rows": sum(1 for r in use if not _final(r)),
                    "final_rows": sum(1 for r in use if _final(r)),
                    "depth_edge": {"c1": edges["c1"], "invariant": edges["invariant"], "active": edges["active"],
                                   "invariant_source": edges["invariant_source"],
                                   "invariant_active": edges["invariant_active"],
                                   "c1_minus_invariant": edges["c1_minus_invariant"],
                                   "at_optimum": depth == d_max, "engine_invariant_checked": True},
                    "bounds_active_on_grid": grid_hits_edge, "grid_edges": edges_on,
                    "steady_hot_rows_enriched": enriched, "sse": sse}))


# ---------------------------------------------------------------------------
# S3c: the boost envelope (PLAN.md 5.2 S3c; amendments C1, D1; decision 53)
# ---------------------------------------------------------------------------
def _envelope(points, *, inlet, baro_of, temp_of):
    pts = []
    for p in points:
        flow = float(plant_model.corrected_flow(p["air"], temp_of(p["row"]), baro_of(p["row"]) - S3C_FILTER_LOSS_KPA))
        pts.append({"line": p["row"].line, "key": _key(p["row"]), "corrected_flow": flow,
                    "pr": float(p["row"].map_kpa / inlet)})
    pts.sort(key=lambda q: (q["corrected_flow"], q["key"]))
    return pts


def s3c_envelope(rows, *, plant, view, conventions):
    """S3c (PLAN.md 5.2 as amendment D1 and decision 53 change it): one point per
    calibration high-load line, its highest-MAP Final row whose calibration air
    exists (epa_stats.air_cal: a meter and a lambda), at corrected flow
    (plant.corrected_flow of that air, the cell temperature and the barometer less
    2 kPa) and PR = MAP / the engine's inlet_sea_kpa, so the in-use ceiling inlet x
    PR never exceeds a measured MAP. Sorted by flow, strictly increasing asserted
    (ties refused, D1), anchored at (0, 1), flat past the last point (np.interp
    holds its end), no running maximum: the measured shape. The cap is the largest
    point's PR. Lines without holds give no point and are listed. The HD1's rows,
    which publish no cell pressure or temperature, take decision 53's median of the
    rows that do, and the envelope is recomputed at both ends of their range."""
    inlet = float(plant.engine.boost.inlet_sea_kpa)
    lines = _cal_lines(view)
    finals = [r for r in rows if _final(r) and _no_sentinel(r)]
    baro_rule, temp_rule = _cell_rule(rows, "baro_kpa"), _cell_rule(rows, "cell_temp_k")
    points, no_holds, no_air, skipped = [], [], [], []
    for line in lines:
        fl = [r for r in finals if r.line == line]
        if not fl:
            no_holds.append(line)
            continue
        fl.sort(key=lambda r: (-r.map_kpa, r.table, r.source_row))
        with_air = [(r, epa_stats.air_cal(r, view=view, conventions=conventions)) for r in fl]
        ok = [(r, a) for r, a in with_air if a is not None]
        if not ok:
            no_air.append(line)
            continue
        if ok[0][0] is not fl[0]:
            skipped.append({"line": line, "key": _key(fl[0]), "why": "no calibration air (no meter or lambda)"})
        points.append({"row": ok[0][0], "air": float(ok[0][1])})

    def baro_at(v):
        return lambda r: float(r.baro_kpa) if _finite(r.baro_kpa) else v

    def temp_at(v):
        return lambda r: float(r.cell_temp_k) if _finite(r.cell_temp_k) else v

    b0 = None if baro_rule is None else baro_rule["median"]
    t0_ = None if temp_rule is None else temp_rule["median"]
    for p in points:
        r = p["row"]
        if (not _finite(r.baro_kpa) and b0 is None) or (not _finite(r.cell_temp_k) and t0_ is None):
            raise FitDefect(f"S3c: the envelope point {_key(r)} has no cell pressure or temperature, and no "
                            "calibration row publishes one for decision 53's median")
    pts = _envelope(points, inlet=inlet, baro_of=baro_at(b0), temp_of=temp_at(t0_))
    if not pts:
        raise FitDefect("S3c: no calibration high-load line gives an envelope point")
    flows = [p["corrected_flow"] for p in pts]
    if not (flows[0] > 0.0 and all(b2 > a2 for a2, b2 in zip(flows, flows[1:]))):
        raise ValueError("S3c: the envelope's corrected flows are not strictly increasing (ties are refused, "
                         "amendment D1; np.interp needs an increasing xp, plant.boost_ceiling_kpa)")
    prs = [p["pr"] for p in pts]
    vals = {"envelope_flow": [0.0] + flows, "envelope_pr": [1.0] + prs, "pr_cap": float(max(prs))}
    sweep = None
    if baro_rule is not None:
        sweep = {}
        for end, v in zip(("lo", "hi"), baro_rule["sweep"]):
            q = _envelope(points, inlet=inlet, baro_of=baro_at(v), temp_of=temp_at(t0_))
            sweep[end] = {"barometer_kpa": v, "envelope_flow": [0.0] + [p["corrected_flow"] for p in q],
                          "envelope_pr": [1.0] + [p["pr"] for p in q]}
    falls = [[pts[i]["line"], pts[i + 1]["line"]] for i in range(len(pts) - 1) if pts[i + 1]["pr"] < pts[i]["pr"]]
    flags = []
    if no_holds:
        flags.append("S3c_lines_without_holds")
    if falls:
        flags.append("S3c_pr_falls_with_flow")           # D1: whether the loop settles is checked in use
    return StageResult(
        stage="S3c", values=vals, rows_used=len(pts), rows_excluded=_py({"lines_without_air": no_air}),
        flags=tuple(flags), bounds_active=(), convergence=None,
        report=_py({"points": pts, "lines_without_holds": no_holds, "anchor": [0.0, 1.0],
                    "pr_cap": vals["pr_cap"], "inlet_sea_kpa": inlet,
                    "highest_map_rows_skipped": skipped,
                    "hd1_barometer": None if baro_rule is None else dict(baro_rule, envelope_at_sweep=sweep),
                    "cell_temperature_rule": temp_rule, "pr_falls_with_flow": falls,
                    "filter_loss_kpa": S3C_FILTER_LOSS_KPA}))


# ---------------------------------------------------------------------------
# S3d: form D's cam schedule (PLAN.md 5.3; amendments C1, D8; decision 41)
# ---------------------------------------------------------------------------
def s3d_cam(rows, *, view):
    """S3d (PLAN.md 5.3, form D): the full quadratic in x = rpm/1000 and y =
    MAP/100, in BaselineECU.cam_deg's term order (engines.CAM_SCHEDULE's first six),
    by OLS on the calibration rows that carry a cam value (empty cells excluded;
    sentinel rows enter no fit); its domain the rpm and MAP range of those rows, its
    clamp their measured cam range (amendment C1), so the schedule is never
    extrapolated (mistake 6). Calibration rows outside the domain are flagged as
    extrapolated (the Ford's HD1 holds, outside Cell 9's range). No sign is assumed:
    the cam is EPA's channel as published, and ve_cam absorbs _ret against _adv."""
    use = [r for r in rows if _finite(r.cam_cad) and _no_sentinel(r)]
    if len(use) < 7:
        raise FitDefect(f"S3d: {len(use)} calibration rows carry a cam value; a six-term quadratic needs more")
    x = np.array([r.speed_rpm for r in use], dtype=float) / 1000.0
    yy = np.array([r.map_kpa for r in use], dtype=float) / 100.0
    cam = np.array([r.cam_cad for r in use], dtype=float)
    X = np.column_stack([np.ones(len(use)), x, yy, x * x, x * yy, yy * yy])
    coef, rank = _lstsq(X, cam)
    if rank < 6:
        raise FitDefect(f"S3d: the cam rows' design has rank {rank} of 6")
    rlo, rhi = float(min(r.speed_rpm for r in use)), float(max(r.speed_rpm for r in use))
    mlo, mhi = float(min(r.map_kpa for r in use)), float(max(r.map_kpa for r in use))
    vals = {"cam_on": 1}
    vals.update({k: float(c) for k, c in zip(engines.CAM_SCHEDULE[:6], coef)})
    vals.update(cam_rpm_lo=rlo, cam_rpm_hi=rhi, cam_map_lo=mlo, cam_map_hi=mhi,
                cam_lo=float(cam.min()), cam_hi=float(cam.max()))
    outside = [r for r in rows if not (rlo <= r.speed_rpm <= rhi and mlo <= r.map_kpa <= mhi)]
    res = cam - X @ coef
    flags = ["S3d_extrapolated_rows"] if outside else []
    return StageResult(
        stage="S3d", values=vals, rows_used=len(use),
        rows_excluded=_py({"no_cam_value": [_key(r) for r in rows if not _finite(r.cam_cad)]}),
        flags=tuple(flags), bounds_active=(), convergence=None,
        report=_py({"domain": {"rpm": [rlo, rhi], "map_kpa": [mlo, mhi]}, "clamp_cad": [vals["cam_lo"], vals["cam_hi"]],
                    "rows": len(use), "empty_cells": sum(1 for r in rows if not _finite(r.cam_cad)),
                    "extrapolated_rows": [_key(r) for r in outside], "term_order": list(engines.CAM_SCHEDULE[:6]),
                    "rms_cad": float(math.sqrt(float(np.mean(res ** 2)))),
                    "channels": sorted({r.cam_channel for r in use if r.cam_channel})}))


# ---------------------------------------------------------------------------
# The least-squares machinery every nonlinear stage shares (amendments D5, D10)
# ---------------------------------------------------------------------------
class _Tracker:
    """Records every evaluation of a least-squares objective, so that the
    convergence report reads the accepted iterates (an evaluation whose cost is
    below every earlier one's) and the best iterate for a second attempt (mistake
    15). Deterministic: the solver and the objective are."""

    def __init__(self, fun, x_scale):
        self.fun, self.x_scale = fun, np.asarray(x_scale, dtype=float)
        self.accepted = []

    def __call__(self, x):
        r = self.fun(x)
        c = 0.5 * float(np.dot(r, r))
        if not self.accepted or c < self.accepted[-1][1]:
            self.accepted.append((np.array(x, dtype=float), c))
        return r

    def best(self):
        return self.accepted[-1][0]

    def last_step(self):
        if len(self.accepted) < 2:
            return 0.0, 0.0
        (x0, c0), (x1, c1) = self.accepted[-2], self.accepted[-1]
        return float(np.linalg.norm((x1 - x0) / self.x_scale)), float(c0 - c1)


def _solve(fun, jac, x0, *, lb, ub, x_scale, tol):
    """least_squares('trf') with the declared x_scale, tolerances and max_nfev
    (amendment D5), and PLAN.md 5.6's declared second attempt: a run that stops on
    max_nfev (status 0) is restarted once from its best iterate with twice the
    budget; the best iterate is then accepted, flagged by the caller. Returns
    (x, Convergence, flags)."""
    x0 = np.clip(np.asarray(x0, dtype=float), lb, ub)
    tr = _Tracker(fun, x_scale)
    res = least_squares(tr, x0, jac=jac, bounds=(lb, ub), method="trf", x_scale=np.asarray(x_scale, dtype=float),
                        max_nfev=MAX_NFEV, **tol)
    flags, second, nfev, njev = [], False, int(res.nfev), int(res.njev or 0)
    if res.status == 0:
        second = True
        tr2 = _Tracker(fun, x_scale)
        res = least_squares(tr2, np.clip(tr.best(), lb, ub), jac=jac, bounds=(lb, ub), method="trf",
                            x_scale=np.asarray(x_scale, dtype=float), max_nfev=SECOND_ATTEMPT_NFEV, **tol)
        nfev, njev = nfev + int(res.nfev), njev + int(res.njev or 0)
        tr = tr2
        if res.status == 0:
            flags.append("not_converged")               # PLAN.md 5.6: the best iterate, flagged
    step, dcost = tr.last_step()
    conv = Convergence(nfev=nfev, njev=njev, status=int(res.status), message=str(res.message),
                       cost=float(res.cost), grad_norm=float(res.optimality), last_step_norm=step,
                       cost_change=dcost, second_attempt=second)
    return np.array(res.x, dtype=float), np.array(res.active_mask), conv, flags


def _cov(J_all, r_data, n_par):
    """The parameter covariance at an optimum, scaled by the residual variance
    (amendment D11): s^2 (J'J)^-1, s^2 the data residuals' mean square over their
    degrees of freedom, J with the ridge's rows (the information the estimate was
    made with). None when singular."""
    dof = max(len(r_data) - n_par, 1)
    s2 = float(np.dot(r_data, r_data)) / dof
    H = J_all.T @ J_all
    try:
        return s2 * np.linalg.inv(H), s2
    except np.linalg.LinAlgError:
        return None, s2


def _corr(cov, names):
    if cov is None:
        return None
    d = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    return {a: {b: (float(cov[i, j] / (d[i] * d[j])) if d[i] > 0 and d[j] > 0 else None)
                for j, b in enumerate(names)} for i, a in enumerate(names)}


def _data_or_prior(J_data, names):
    """Each parameter's Fisher information from the data (the diagonal of J'J over
    the data rows, in the parameter's own units) against the ridge's (w / s^2): the
    larger names it (PLAN.md 5.2, 'data-dominated or prior-dominated'). A parameter
    the ridge does not hold (ve_base, ve_amp) is data-dominated by definition."""
    out = {}
    info = np.sum(J_data ** 2, axis=0)
    for j, n in enumerate(names):
        prior = RIDGE_W / SCALES[n] ** 2 if n in SCALES else 0.0
        out[n] = "data-dominated" if info[j] > prior else "prior-dominated"
    return out


def _zero_columns(J_data, names):
    return [n for j, n in enumerate(names) if not np.any(J_data[:, j] != 0.0)]


def _assert_columns_at_start(J_data, names, stage):
    """Amendment D10: every column non-zero at the start values (mistake 25: a
    parameter that cannot move a residual is not being fitted); a zero column is a
    coding defect. Zero columns at the optimum are reported, never asserted."""
    zero = _zero_columns(J_data, names)
    if zero:
        raise FitDefect(f"{stage}: the Jacobian's columns {zero} are zero at the start values (amendment D10)")


# ---------------------------------------------------------------------------
# S2: the breathing (PLAN.md 5.2 S2 and 5.3; amendments D5, D9; mistake 10)
# ---------------------------------------------------------------------------
def s2_names(form):
    """S2's parameters under a form: the curve's four, form B's MAP term, form D's cam term."""
    t = _terms(form)
    return ("ve_base", "ve_amp", "ve_rpm", "ve_width") + (("ve_map",) if "B" in t else ()) + \
        (("ve_cam",) if "D" in t else ())


def _air_at_unit_ve(e, rpm, mp, iat):
    """The air mass flow, g/s, the plant would give at volumetric efficiency 1:
    plant.run_cycle's operations with eta_v left out (rho_int, the swept volume,
    1 - f_res, n_cyl * rpm / 120, x 1000), f_res by plant.residual_fraction, the one
    definition. S2's shortcut is VE times this; verify checks it against run_cycle."""
    geo = e.geometry
    f_res = np.array([plant_model.residual_fraction(m, engine=e) for m in mp], dtype=float)
    rho = mp * 1000.0 / (plant_model.R_AIR * iat)
    return rho * geo.vd_cyl * (1.0 - f_res) * geo.n_cyl * rpm / 120.0 * 1000.0


def s2_breathing(rows, *, plant, view, form, conventions, dtheta, jobs):
    """S2 (PLAN.md 5.2, 5.3): ve_base, ve_amp, ve_rpm, ve_width, and form B's
    ve_map, form D's ve_cam, on the fired steady and Final rows with a meter and a
    lambda (no sentinel row). The target is the calibration's air (epa_stats.air_cal)
    over the plant's air at unit VE; the objective sum [(ln eta_model - ln
    eta_target) / R_air]^2 + the ridge, eta_model by plant.volumetric_efficiency
    itself, its clip included (and form D's cam the schedule's, the ECU's, at each
    row: decision 41). Variable projection first (amendment D9): ve_rpm over the
    calibration lines' speeds x ve_width on S2_WIDTH_GRID, the linear terms by a
    bounded linear solve (lsq_linear, BVLS) of the relative residual, ridge rows
    for ve_map and ve_cam included; the grid's least objective (the first in
    order on a tie) starts a least_squares('trf') polish of every term with the
    declared x_scale and bounds (D5, D9). `plant` is the candidate with this fit's
    ECU (so the cam is the one S3d fitted). Verified: run_cycle's mdot_air_gps at
    every row equals VE x the unit-VE air within 1e-12 (mistake 10)."""
    e = plant.engine
    names = s2_names(form)
    ecu = engine_env.BaselineECU(e.ecu)
    use = _s2_use(rows)
    excl = {"no_meter_or_not_fired": [_key(r) for r in rows if not r.pops.fired_meter],
            "no_lambda": [_key(r) for r in rows if r.pops.fired_meter and not _has_lam(r)],
            "sentinel": [_key(r) for r in rows if r.pops.fired_meter and _has_lam(r) and not _no_sentinel(r)]}
    if len(use) < len(names) + 2:
        raise FitDefect(f"S2 has {len(use)} rows for {len(names)} parameters")
    rpm = np.array([r.speed_rpm for r in use], dtype=float)
    mp = np.array([r.map_kpa for r in use], dtype=float)
    iat = np.array([r.imt_k for r in use], dtype=float)
    air = np.array([epa_stats.air_cal(r, view=view, conventions=conventions) for r in use], dtype=float)
    a_unit = _air_at_unit_ve(e, rpm, mp, iat)
    eta_t = air / a_unit
    cam = np.array([ecu.cam_deg(a, b) for a, b in zip(rpm, mp)], dtype=float) if "ve_cam" in names else None
    sig = _scales(view)["air"]
    centre = ridge_centre()
    rlo, rhi = _rpm_ends(view)
    bnd = {n: ((rlo, rhi) if n == "ve_rpm" else BOUNDS[n]) for n in names}
    lb = np.array([bnd[n][0] for n in names])
    ub = np.array([bnd[n][1] for n in names])
    ridge = [n for n in names if n in SCALES]
    c0 = e.cycle

    def cycle_of(th):
        d = dict(zip(names, (float(v) for v in th)))
        return replace(c0, **d)

    def eta_of(th):
        ee = replace(e, cycle=cycle_of(th))
        return plant_ve(rpm, mp, cam, ee)

    def unclipped(th):
        d = dict(zip(names, th))
        v = d["ve_base"] + d["ve_amp"] * np.exp(-((rpm - d["ve_rpm"]) / d["ve_width"]) ** 2)
        if "ve_map" in d:
            v = v + d["ve_map"] * (mp - c0.ve_map_ref_kpa)
        if "ve_cam" in d:
            v = v + d["ve_cam"] * (cam - c0.cam_ref_deg)
        return v

    def fun(th):
        r = (np.log(eta_of(th)) - np.log(eta_t)) / sig
        rr = [math.sqrt(RIDGE_W) * (th[names.index(n)] - centre[n]) / SCALES[n] for n in ridge]
        return np.concatenate([r, np.array(rr)])

    def jac_data(th):
        d = dict(zip(names, th))
        eta = eta_of(th)
        live = (unclipped(th) > c0.ve_lo) & (unclipped(th) < c0.ve_hi)
        g = np.exp(-((rpm - d["ve_rpm"]) / d["ve_width"]) ** 2)
        cols = {"ve_base": np.ones_like(rpm), "ve_amp": g,
                "ve_rpm": d["ve_amp"] * g * 2.0 * (rpm - d["ve_rpm"]) / d["ve_width"] ** 2,
                "ve_width": d["ve_amp"] * g * 2.0 * (rpm - d["ve_rpm"]) ** 2 / d["ve_width"] ** 3}
        if "ve_map" in d:
            cols["ve_map"] = mp - c0.ve_map_ref_kpa
        if "ve_cam" in d:
            cols["ve_cam"] = cam - c0.cam_ref_deg
        return np.column_stack([np.where(live, cols[n] / eta, 0.0) / sig for n in names])

    def jac(th):
        R = np.zeros((len(ridge), len(names)))
        for i, n in enumerate(ridge):
            R[i, names.index(n)] = math.sqrt(RIDGE_W) / SCALES[n]
        return np.vstack([jac_data(th), R])

    # amendment D10: every column non-zero at the declared start (the B58's curve,
    # the B and D terms at 0), clipped into the bounds
    start = np.clip(np.array([centre.get(n, float(getattr(_b58_cycle(), n))) for n in names]), lb, ub)
    _assert_columns_at_start(jac_data(start), names, "S2")
    # the variable projection
    lin = [n for n in names if n not in ("ve_rpm", "ve_width")]
    best = None
    for c in _line_speeds(_cal_lines(view)):
        for w in S2_WIDTH_GRID:
            g = np.exp(-((rpm - c) / w) ** 2)
            basis = {"ve_base": np.ones_like(rpm), "ve_amp": g}
            if "ve_map" in lin:
                basis["ve_map"] = mp - c0.ve_map_ref_kpa
            if "ve_cam" in lin:
                basis["ve_cam"] = cam - c0.cam_ref_deg
            A = np.column_stack([basis[n] for n in lin]) / (sig * eta_t)[:, None]
            b = np.full(len(use), 1.0 / sig)
            rid = [n for n in lin if n in SCALES]
            if rid:
                Ar = np.zeros((len(rid), len(lin)))
                for i, n in enumerate(rid):
                    Ar[i, lin.index(n)] = math.sqrt(RIDGE_W) / SCALES[n]
                A, b = np.vstack([A, Ar]), np.concatenate([b, np.zeros(len(rid))])
            sol = lsq_linear(A, b, bounds=([bnd[n][0] for n in lin], [bnd[n][1] for n in lin]), method="bvls")
            th = np.array([float(sol.x[lin.index(n)]) if n in lin else (c if n == "ve_rpm" else w) for n in names])
            th = np.clip(th, lb, ub)
            r = fun(th)
            cost = 0.5 * float(np.dot(r, r))
            if best is None or cost < best[0]:
                best = (cost, th)
    profile_min, x0 = best
    x, active, conv, sflags = _solve(fun, jac, x0, lb=lb, ub=ub, x_scale=[X_SCALE[n] for n in names],
                                     tol=TOLERANCES["S2"])
    vals = {n: float(v) for n, v in zip(names, x)}
    eta = eta_of(x)
    v_raw = unclipped(x)
    clip_rows = [_key(r) for r, v in zip(use, v_raw) if not (c0.ve_lo < v < c0.ve_hi)]
    Jd, Ja = jac_data(x), jac(x)
    r_data = (np.log(eta) - np.log(eta_t)) / sig
    cov, s2 = _cov(Ja, r_data, len(names))
    corr = _corr(cov, list(names))
    # mistake 10: run_cycle's own air at every row equals the shortcut, VE x unit air
    e_fit = replace(e, cycle=cycle_of(x))
    model = RowModel(replace(plant, engine=e_fit), fuels=view.fuel_by_table)
    xs = _inputs(use, view=view, conventions=conventions, model=model)
    res = _map(_cycle_job, [(model._engine_for(xi.fuel), xi, dtheta) for xi in xs], jobs)
    short = eta * a_unit
    worst = max(abs(rr.mdot_air_gps - s) / abs(rr.mdot_air_gps) for rr, s in zip(res, short))
    if worst > S2_VERIFY_REL:
        raise FitDefect(f"S2: run_cycle's air departs from VE x unit air by {worst!r} relative (mistake 10)")
    flags = ["S2_" + f for f in sflags]
    act = [n for n, a in zip(names, active) if a != 0]
    if act:
        flags.append("S2_bound_active")
    if clip_rows:
        flags.append("S2_ve_at_clip")                    # PLAN.md 5.6: a rail, never widened
    zero = _zero_columns(Jd, names)
    return StageResult(
        stage="S2", values=vals, rows_used=len(use), rows_excluded=_py(excl), flags=tuple(flags),
        bounds_active=tuple(act), convergence=conv,
        report=_py({"grid": {"ve_rpm": list(_line_speeds(_cal_lines(view))), "ve_width": list(S2_WIDTH_GRID)},
                    "profile_min_cost": profile_min, "start": dict(zip(names, x0)),
                    "declared_start": dict(zip(names, start)),
                    "verify_max_rel": worst, "clip_rows": clip_rows,
                    "corr_ve_cam_ve_map": (corr["ve_cam"]["ve_map"] if corr and "ve_cam" in names and
                                           "ve_map" in names else None),
                    "params": list(names), "estimate": vals,
                    "covariance": None if cov is None else cov.tolist(), "residual_variance": s2,
                    "correlations": corr, "data_or_prior": _data_or_prior(Jd, names),
                    "zero_columns_at_optimum": zero, "bounds": {n: list(bnd[n]) for n in names},
                    "x_scale": {n: X_SCALE[n] for n in names}}))


def plant_ve(rpm, mp, cam, e):
    """plant.volumetric_efficiency over arrays (the plant's own function; form A
    reads no MAP and no cam, form D the cam the ECU schedules)."""
    t = _terms(e.cycle.form)
    return np.asarray(plant_model.volumetric_efficiency(rpm, mp if "B" in t else None, cam if "D" in t else None,
                                                        engine=e), dtype=float)


# ---------------------------------------------------------------------------
# S4: burn, friction and the port (PLAN.md 5.2 S4; amendments D4, D6, D13)
# ---------------------------------------------------------------------------
def _outer(th):
    return tuple(float(v) for v in th[:4])


def _bare_engine(e, outer):
    """`e` at the four outer constants with FMEP's four coefficients and UA_PORT at
    0: the integration of plant.run_cycle (its loop) does not read them (FMEP is
    applied after the loop, UA_PORT only in the exhaust's port loss), so one cycle
    per row and outer 4-tuple serves every inner value, which _inner then applies
    in the plant's own operations (PLAN.md 5.2 S4: 'Cycles cached by the 4-tuple')."""
    bb, br, db, dr = outer
    return replace(e, cycle=replace(e.cycle, burn_base=bb, burn_rpm=br, delay_base=db, delay_rpm=dr,
                                    fmep_0=0.0, fmep_pmax=0.0, fmep_sp=0.0, fmep_sp2=0.0, ua_port=0.0))


def _inner(cached, x, e, th):
    """Torque, TIT and model fuel at one row from its cached bare cycle and the inner
    constants th[4:9], in plant.run_cycle's operations: FMEP's expression term by
    term, the brake torque of (imep_net - fmep) and the port's exponential with the
    gas flow and cp_exh. The shortcut verify checks against run_cycle (1e-9)."""
    torque_c, pmax, egt_c, m_air, m_fuel = cached
    geo, c = e.geometry, e.cycle
    f0, fp, fs, fs2, ua = th[4:9]
    sp = 2.0 * geo.stroke * x.rpm / 60.0
    fmep = f0 + fp * pmax + fs * sp + fs2 * sp ** 2
    torque = torque_c - fmep * 1e5 * geo.vd_total / (4.0 * np.pi)
    t_wall = 0.5 * x.ect_k + 0.5 * (x.ect_k + c.t_head_k)
    xflow = max((m_air + m_fuel) / 1000.0 * c.cp_exh, 1.0)
    t_bd = egt_c + 273.15
    tit = t_wall + (t_bd - t_wall) * math.exp(-ua / xflow) - 273.15
    return torque, tit, m_fuel, (sp, pmax, t_bd - t_wall, xflow)


def _bare_job(job):
    engine, x, dtheta = job
    r = _cycle_at(engine, x, dtheta=dtheta, ecu_engine=engine)
    return (r.torque_nm, r.p_max_bar, r.egt_c, r.mdot_air_gps, r.mdot_fuel_gps)


class _S4Model:
    """S4's residuals and Jacobian over its rows, with the bare cycles cached by the
    outer 4-tuple (PLAN.md 5.2 S4; amendment D4): the efficiency residual (T_m
    F_meter / (T_E F_m) - 1) / R_eff on the rows with a meter, the TIT residual
    (TIT_m - TIT_E) / R_tit on every row, the ridge on all nine; the outer columns by
    a forward difference of FD_CAD on the bases with the per-row chain rule in rpm
    (plant.burn_duration and ignition_delay read base + rpm term * rpm), FMEP's and
    UA_PORT's columns analytic."""

    def __init__(self, rows, xs, model, *, view, dtheta, jobs, centre):
        self.rows, self.xs, self.model = rows, xs, model
        self.dtheta, self.jobs, self.centre = dtheta, jobs, centre
        self.e = model.plant.engine
        sc = _scales(view)
        self.s_eff, self.s_tit = sc["eff"], sc["tit"]
        self.meter = np.array([r.fuel_meter_gps if _finite(r.fuel_meter_gps) else np.nan for r in rows])
        self.has_m = np.isfinite(self.meter)
        self.T_E = np.array([r.torque_nm for r in rows], dtype=float)
        self.TIT_E = np.array([r.tit_c for r in rows], dtype=float)
        self.rpm = np.array([x.rpm for x in xs], dtype=float)
        self.cache = {}
        self.cycles = 0

    def bare(self, outer):
        if outer not in self.cache:
            base = _bare_engine(self.e, outer)
            jobs = [(engines.with_fuel(base, _fuel_record(x.fuel)), x, self.dtheta) for x in self.xs]
            self.cache[outer] = _map(_bare_job, jobs, self.jobs)
            self.cycles += len(jobs)
        return self.cache[outer]

    def outputs(self, th, outer=None):
        cached = self.bare(_outer(th) if outer is None else outer)
        out = [_inner(c, x, self.e, th) for c, x in zip(cached, self.xs)]
        return (np.array([o[0] for o in out]), np.array([o[1] for o in out]), np.array([o[2] for o in out]),
                [o[3] for o in out])

    def data_res(self, th, outer=None):
        T, TIT, F, _aux = self.outputs(th, outer)
        eff = (T[self.has_m] * self.meter[self.has_m] / (self.T_E[self.has_m] * F[self.has_m]) - 1.0) / self.s_eff
        return np.concatenate([eff, (TIT - self.TIT_E) / self.s_tit])

    def ridge(self, th):
        return np.array([math.sqrt(RIDGE_W) * (th[i] - self.centre[n]) / SCALES[n] for i, n in enumerate(S4_PARAMS)])

    def fun(self, th):
        return np.concatenate([self.data_res(th), self.ridge(th)])

    def jac_data(self, th):
        th = np.asarray(th, dtype=float)
        o = _outer(th)
        r0 = self.data_res(th, o)
        rb = self.data_res(th, (o[0] + FD_CAD, o[1], o[2], o[3]))
        rd = self.data_res(th, (o[0], o[1], o[2] + FD_CAD, o[3]))
        rpm_rows = np.concatenate([self.rpm[self.has_m], self.rpm])
        db, dd = (rb - r0) / FD_CAD, (rd - r0) / FD_CAD
        T, TIT, F, aux = self.outputs(th, o)
        k = self.e.geometry.vd_total / (4.0 * np.pi) * 1e5
        sp = np.array([a[0] for a in aux])
        pmax = np.array([a[1] for a in aux])
        dgas = np.array([a[2] for a in aux])
        xflow = np.array([a[3] for a in aux])
        # d(eff)/dT on the meter rows, d(TIT)/dUA on every row
        kap = self.meter[self.has_m] / (self.T_E[self.has_m] * F[self.has_m]) / self.s_eff
        n_e = int(self.has_m.sum())
        J = np.zeros((n_e + len(self.rows), 9))
        J[:, 0], J[:, 1], J[:, 2], J[:, 3] = db, db * rpm_rows, dd, dd * rpm_rows
        for j, col in ((4, np.ones_like(sp)), (5, pmax), (6, sp), (7, sp ** 2)):
            J[:n_e, j] = -k * col[self.has_m] * kap
        J[n_e:, 8] = -dgas * np.exp(-th[8] / xflow) / xflow / self.s_tit
        return J

    def jac(self, th):
        R = np.diag([math.sqrt(RIDGE_W) / SCALES[n] for n in S4_PARAMS])
        return np.vstack([self.jac_data(th), R])


def _climb_cell(rows):
    """The calibration High Load Final row of highest MAP: where the weakest
    direction's in-use consequence is read (amendment D6: 'KI at the climb cell, the
    lambda lever'), chosen here as the calibration operating point nearest a climb's
    (hot, boosted, held)."""
    fl = [r for r in rows if _final(r) and _has_lam(r) and _no_sentinel(r)]
    return max(fl, key=lambda r: (r.map_kpa, r.table, r.source_row)) if fl else None


def s4_burn(rows, *, name, values, view, form, jobs, conventions, dtheta, start):
    """S4 (PLAN.md 5.2 as amendments D4, D6 and D13 change it): the nine parameters
    S4_PARAMS jointly in least_squares('trf') (D4) on the fired rows of the lambda~1
    band, which run at lambda 1.00 (rows between the bands and sentinel rows are
    left out): efficiency on the rows with a meter, TIT on all, the ridge on all
    nine (_S4Model). Starts: `start` (the B58's for form A, the previous form's
    solution after it: PLAN.md 5.4), x0.8 and x1.2, then two more at +-1 sd along
    the weakest direction of the best of those three (D6: burn and delay are nearly
    collinear); the best of the five is kept (the first on a tie). Reported:
    the weakest direction, its sd and its in-use consequence; the condition number,
    the correlations and each parameter as data- or prior-dominated; the residuals
    per line and per population (D13: an E1a miss on stoichiometric hot rows at
    form A is a burn/FMEP residual no form B-D acts on, never a reason for a form);
    the physical checks of PLAN.md 5.6, flagged. `values` holds every other
    constant (S1-S3 and S2's breathing)."""
    use = _s4_use(rows)
    excl = {"not_fired_lambda1": [_key(r) for r in rows if not r.pops.fired_l1],
            "sentinel": [_key(r) for r in rows if r.pops.fired_l1 and not _no_sentinel(r)]}
    if len(use) < 6:
        raise FitDefect(f"S4 has {len(use)} fired lambda~1 rows for nine parameters")
    cand = candidate(name, values)
    model = RowModel(cand, fuels=view.fuel_by_table)
    xs = _inputs(use, view=view, conventions=conventions, model=model)
    centre = ridge_centre()
    m = _S4Model(use, xs, model, view=view, dtheta=dtheta, jobs=jobs, centre=centre)
    lb = np.array([BOUNDS[n][0] for n in S4_PARAMS])
    ub = np.array([BOUNDS[n][1] for n in S4_PARAMS])
    xsc = [X_SCALE[n] for n in S4_PARAMS]
    th0 = np.clip(np.array([float(start[n]) for n in S4_PARAMS]), lb, ub)
    _assert_columns_at_start(m.jac_data(th0), S4_PARAMS, "S4")
    runs = []
    for f in S4_START_FACTORS:
        x, act, conv, fl = _solve(m.fun, m.jac, np.clip(th0 * f, lb, ub), lb=lb, ub=ub, x_scale=xsc,
                                  tol=TOLERANCES["S4"])
        runs.append({"from": f"x{f}", "x0": np.clip(th0 * f, lb, ub), "x": x, "active": act, "conv": conv,
                     "flags": fl})
    best3 = min(range(3), key=lambda i: (runs[i]["conv"].cost, i))
    xb = runs[best3]["x"]
    # D6: the weakest direction at the best of three, in scale units
    Jd = m.jac_data(xb)
    S = np.array(xsc)
    Ja_s = np.vstack([Jd, m.jac(xb)[len(Jd):]]) * S[None, :]
    rd = m.data_res(xb)
    s2 = float(np.dot(rd, rd)) / max(len(rd) - 9, 1)
    w_eig, v_eig = np.linalg.eigh(Ja_s.T @ Ja_s)
    v = v_eig[:, 0]
    v = v if v[np.argmax(np.abs(v))] > 0 else -v
    sd = float(math.sqrt(s2 / w_eig[0])) if w_eig[0] > 0 else float("inf")
    for sign in (+1.0, -1.0):
        x0 = np.clip(xb + sign * (sd if math.isfinite(sd) else 1.0) * v * S, lb, ub)
        x, act, conv, fl = _solve(m.fun, m.jac, x0, lb=lb, ub=ub, x_scale=xsc, tol=TOLERANCES["S4"])
        runs.append({"from": f"weakest{'+' if sign > 0 else '-'}", "x0": x0, "x": x, "active": act, "conv": conv,
                     "flags": fl})
    best = min(range(len(runs)), key=lambda i: (runs[i]["conv"].cost, i))
    # THE DECLARED FINAL POLISH (TOLERANCES' note; WP3's second fix of 23 October 2026): the start that stopped
    # lowest, run once more at TOLERANCES["S4_polish"]; trf only accepts steps that lower the cost, so the
    # polished point is kept, and its departure from that start is recorded
    xb5, conv5 = runs[best]["x"], runs[best]["conv"]
    xp, actp, convp, flp = _solve(m.fun, m.jac, xb5, lb=lb, ub=ub, x_scale=xsc, tol=TOLERANCES["S4_polish"])
    kept_polish = convp.cost <= conv5.cost
    x, conv = (xp, convp) if kept_polish else (xb5, conv5)
    act_kept, flags_kept = (actp, flp) if kept_polish else (runs[best]["active"], runs[best]["flags"])
    dep = (xp - xb5) / S
    polish = {"from": runs[best]["from"], "tolerances": dict(TOLERANCES["S4_polish"]), "cost_before": conv5.cost,
              "cost_after": convp.cost, "nfev": convp.nfev, "status": convp.status, "kept": bool(kept_polish),
              "departure_scale_units": dict(zip(S4_PARAMS, dep)), "departure_norm_scale_units": float(np.linalg.norm(dep)),
              "departure_along_weakest_scale_units": float(np.dot(dep, v))}
    vals = {n: float(val) for n, val in zip(S4_PARAMS, x)}
    # ftol bounds the reduction per step, not the distance to the minimum along the weakest direction: the
    # five starts' end points projected on that direction (scale units, from the kept point) and their
    # spread are the starts' share of the uncertainty, reported (WP3's fix of 23 October 2026, on the fit
    # review's finding), beside the polish that resolves the kept point (polish)
    proj = [float(np.dot((q["x"] - x) / S, v)) for q in runs]
    resolution = {"weakest_direction_projection": [{"from": q["from"], "scale_units": p, "cost": q["conv"].cost}
                                                   for q, p in zip(runs, proj)],
                  "spread_scale_units": float(max(proj) - min(proj)), "sd_scale_units": sd,
                  "statement": "the five starts choose the basin at the declared tolerances; the one that stopped "
                               "lowest is polished at TOLERANCES['S4_polish'] and the polished point is the frozen "
                               "one (polish: its departure from that start); the in-sample stage is evaluated there"}
    Jd = m.jac_data(x)
    Ja = m.jac(x)
    rd = m.data_res(x)
    cov, s2b = _cov(Ja, rd, 9)
    Ja_s = Ja * S[None, :]
    sv = np.linalg.svd(Ja_s, compute_uv=False)
    cond = float(sv[0] / sv[-1]) if sv[-1] > 0 else float("inf")
    # residuals per line and per population (D13)
    T, TIT, F, _aux = m.outputs(x)
    eff = np.where(m.has_m, T * np.where(m.has_m, m.meter, 1.0) / (m.T_E * F) - 1.0, np.nan)
    tit = TIT - m.TIT_E
    groups = {}
    for i, r in enumerate(use):
        groups.setdefault(("line", r.line), []).append(i)
        groups.setdefault(("pop", "hot_lambda1" if r.pops.hot_l1 else "part_load"), []).append(i)

    def summ(ix):
        e_ = [eff[i] for i in ix if np.isfinite(eff[i])]
        return {"n": len(ix), "mean_eff_rel": float(np.mean(e_)) if e_ else None,
                "mean_tit_k": float(np.mean([tit[i] for i in ix]))}

    by_line = {k[1]: summ(ix) for k, ix in sorted(groups.items()) if k[0] == "line"}
    by_pop = {k[1]: summ(ix) for k, ix in sorted(groups.items()) if k[0] == "pop"}
    # PLAN.md 5.6's physical checks, at the fitted constants, by the plant's own functions
    e_fit = replace(cand.engine, cycle=replace(cand.engine.cycle, **vals))
    f_res = [plant_model.residual_fraction(xi.map_kpa, engine=e_fit) for xi in xs]
    burn = [plant_model.burn_duration(xi.rpm, xi.lam, f, engine=e_fit) for xi, f in zip(xs, f_res)]
    delay = [plant_model.ignition_delay(xi.rpm, xi.lam, f, engine=e_fit) for xi, f in zip(xs, f_res)]
    fmeps = [vals["fmep_0"] + vals["fmep_pmax"] * a[1] + vals["fmep_sp"] * a[0] + vals["fmep_sp2"] * a[0] ** 2
             for a in _aux]
    checks = {"burn_cad": [float(min(burn)), float(max(burn))], "burn_ok": bool(
                  S4_BURN_RANGE[0] <= min(burn) and max(burn) <= S4_BURN_RANGE[1]),
              "delay_cad": [float(min(delay)), float(max(delay))], "delay_ok": bool(
                  S4_DELAY_RANGE[0] <= min(delay) and max(delay) <= S4_DELAY_RANGE[1]),
              "fmep_bar": [float(min(fmeps)), float(max(fmeps))], "fmep_positive": bool(min(fmeps) > 0.0)}
    flags = ["S4_" + f for f in flags_kept]
    if not (checks["burn_ok"] and checks["delay_ok"] and checks["fmep_positive"]):
        flags.append("S4_physical_check")                # PLAN.md 5.6: flagged
    act = [n for n, a in zip(S4_PARAMS, act_kept) if a != 0]
    if act:
        flags.append("S4_bound_active")
    cons = _weakest_consequence(rows, cand, vals, v * S, sd, view=view, conventions=conventions, dtheta=dtheta)
    zero = _zero_columns(Jd, S4_PARAMS)
    return StageResult(
        stage="S4", values=vals, rows_used=len(use), rows_excluded=_py(excl), flags=tuple(flags),
        bounds_active=tuple(act), convergence=conv,
        report=_py({"starts": [{"from": q["from"], "x0": dict(zip(S4_PARAMS, q["x0"])), "cost": q["conv"].cost,
                                "nfev": q["conv"].nfev, "status": q["conv"].status} for q in runs],
                    "best_start": runs[best]["from"], "resolution": resolution, "polish": polish,
                    "weakest_direction": {"vector": dict(zip(S4_PARAMS, v)), "sd": sd,
                                          "eigenvalue_scaled": float(w_eig[0]),
                                          "ki_at_climb_cell": cons["ki"], "lambda_lever": cons["lever"]},
                    "condition_number": cond, "correlations": _corr(cov, list(S4_PARAMS)),
                    "data_or_prior": _data_or_prior(Jd, S4_PARAMS),
                    "residuals": {"by_line": by_line, "by_population": by_pop},
                    "physical_checks": checks, "params": list(S4_PARAMS), "estimate": vals,
                    "covariance": None if cov is None else cov.tolist(), "residual_variance": s2b,
                    "zero_columns_at_optimum": zero, "cycles": m.cycles,
                    "rows_efficiency": int(m.has_m.sum()), "rows_tit": len(use),
                    "d13": D13_DECLARATION,
                    "shortcut": {_skey(r): {"torque_nm": float(T[i]), "egt_c": float(TIT[i]),
                                            "mdot_fuel_gps": float(F[i])}
                                 for i, r in enumerate(use)}}))


def _skey(r):
    return f"{r.table}#{int(r.source_row)}"


def _weakest_consequence(rows, cand, vals, step, sd, *, view, conventions, dtheta):
    """The weakest direction's in-use consequence (amendment D6) at the climb cell
    (_climb_cell): the knock integral at the fitted constants and at +-1 sd along
    the direction, and the lambda lever, dTIT/dlambda between lambda 1.00 and 0.95,
    at the same three points."""
    cell = _climb_cell(rows)
    if cell is None or not math.isfinite(sd):
        return {"ki": None, "lever": None}
    out = {"ki": {}, "lever": {}}
    for tag, sgn in (("fit", 0.0), ("plus", 1.0), ("minus", -1.0)):
        th = {n: float(min(max(vals[n] + sgn * sd * step[i], BOUNDS[n][0]), BOUNDS[n][1]))
              for i, n in enumerate(S4_PARAMS)}
        p = replace(cand, engine=replace(cand.engine, cycle=replace(cand.engine.cycle, **th)))
        model = RowModel(p, fuels=view.fuel_by_table)
        x = _inputs([cell], view=view, conventions=conventions, model=model)[0]
        r1 = model.result(replace(x, lam=1.0), dtheta=dtheta)
        r2 = model.result(replace(x, lam=0.95), dtheta=dtheta)
        out["ki"][tag] = model.result(x, dtheta=dtheta).knock_integral
        out["lever"][tag] = (r1.egt_c - r2.egt_c) / 0.05
    out["cell"] = _key(cell)
    return out


# ---------------------------------------------------------------------------
# S5: form C's rich slope (PLAN.md 5.3; amendment D4)
# ---------------------------------------------------------------------------
def _direct_res(rows, model, xs, *, view, dtheta, jobs):
    """S4's residuals (efficiency on the rows with a meter, TIT on all) by direct
    cycles at the model's constants: S5's objective (amendment D4: 'Do the same for
    S5')."""
    sc = _scales(view)
    res = _map(_cycle_job, [(model._engine_for(x.fuel), x, dtheta) for x in xs], jobs)
    eff = [(o.torque_nm * r.fuel_meter_gps / (r.torque_nm * o.mdot_fuel_gps) - 1.0) / sc["eff"]
           for r, o in zip(rows, res) if _finite(r.fuel_meter_gps)]
    tit = [(o.egt_c - r.tit_c) / sc["tit"] for r, o in zip(rows, res)]
    return np.array(eff + tit, dtype=float)


def s5_rich_slope(rows, *, name, values, s4, jobs, view, conventions, dtheta):
    """S5 (PLAN.md 5.3, form C): ce_rich_slope by bounded Brent on [0, 1.5]
    (minimize_scalar 'bounded', xatol S5_XATOL) over the enriched hot calibration
    rows (lambda <= lambda_ref - 0.05; no sentinel row), with S4's constants held
    (`s4`, its StageResult) and S4's residuals, plus the ridge toward the shared
    slope. Flagged: the bound hit (the slope within xatol of 0 or 1.5) and the
    physical check, eta_comb >= 0.5 at the deepest calibration lambda of those rows
    (plant.combustion_efficiency itself)."""
    use = [r for r in rows if r.pops.hot_enr and _no_sentinel(r)]
    excl = {"not_enriched_hot": [_key(r) for r in rows if not r.pops.hot_enr]}
    if "C" not in _terms(values["cycle"]["form"]):
        raise ValueError(f"S5 fits form C's slope, and the values are form {values['cycle']['form']!r}")
    v = _deep(values)
    v["cycle"].update(s4.values)
    cand = candidate(name, v)
    model0 = RowModel(cand, fuels=view.fuel_by_table)
    xs = _inputs(use, view=view, conventions=conventions, model=model0)
    s0_, sc = float(engines.SHARED_RICH_SLOPE), SCALES["ce_rich_slope"]
    evals = []

    def obj(slope):
        p = replace(cand, engine=replace(cand.engine, cycle=replace(cand.engine.cycle, ce_rich_slope=float(slope))))
        r = _direct_res(use, RowModel(p, fuels=view.fuel_by_table), xs, view=view, dtheta=dtheta, jobs=jobs) \
            if use else np.zeros(0)
        f = float(np.dot(r, r)) + RIDGE_W * ((float(slope) - s0_) / sc) ** 2
        evals.append((float(slope), f))
        return f

    lo, hi = BOUNDS["ce_rich_slope"]
    res = minimize_scalar(obj, bounds=(lo, hi), method="bounded", options={"xatol": S5_XATOL})
    slope = float(res.x)
    f_shared = obj(s0_)                                  # reported: the objective at the shared slope
    flags = []
    hit = slope - lo <= S5_XATOL or hi - slope <= S5_XATOL
    if hit:
        flags.append("S5_bound_hit")
    p = replace(cand, engine=replace(cand.engine, cycle=replace(cand.engine.cycle, ce_rich_slope=slope)))
    lam_min = min((x.lam for x in xs), default=None)
    eta = None if lam_min is None else float(plant_model.combustion_efficiency(lam_min, engine=p.engine))
    if eta is not None and eta < S5_ETA_MIN:
        flags.append("S5_physical_check")
    if not use:
        flags.append("S5_no_rows")                       # the ridge alone: the shared slope
    # The slope's standard uncertainty, as rows 5 and 6 take theirs (E6 row 9 under form C: "+- its fit's
    # standard uncertainty (reported)"; WP3's fix of 23 October 2026): the residuals' Jacobian in the slope
    # by a central difference of S5_SIGMA_FD at the optimum, the ridge's row with it (_cov's information),
    # scaled by the residual variance over n - 1 degrees of freedom. None without rows or information.
    sigma = None
    if use:
        def res_at(sl):
            q = replace(cand, engine=replace(cand.engine, cycle=replace(cand.engine.cycle, ce_rich_slope=float(sl))))
            return _direct_res(use, RowModel(q, fuels=view.fuel_by_table), xs, view=view, dtheta=dtheta, jobs=jobs)
        lo_s, hi_s = max(lo, slope - S5_SIGMA_FD), min(hi, slope + S5_SIGMA_FD)
        J = (res_at(hi_s) - res_at(lo_s)) / (hi_s - lo_s)
        r0 = res_at(slope)
        info = float(np.dot(J, J)) + RIDGE_W / sc ** 2
        dof = max(len(r0) - 1, 1)
        if info > 0.0:
            sigma = float(math.sqrt(float(np.dot(r0, r0)) / dof / info))
    return StageResult(
        stage="S5", values={"ce_rich_slope": slope}, rows_used=len(use), rows_excluded=_py(excl),
        flags=tuple(flags), bounds_active=("ce_rich_slope",) if hit else (),
        convergence=Convergence(nfev=int(res.nfev), njev=0, status=int(res.status), message=str(res.message),
                                cost=0.5 * float(res.fun), grad_norm=float("nan"), last_step_norm=float("nan"),
                                cost_change=float("nan"), second_attempt=False),
        report=_py({"slope": slope, "bound_hit": hit, "eta_comb_at_deepest_lambda": eta,
                    "sigma": sigma, "sigma_fd_step": S5_SIGMA_FD,
                    "deepest_lambda_fed": lam_min, "rows": len(use), "xatol": S5_XATOL,
                    "objective_at_shared_slope": f_shared, "objective_at_fit": float(res.fun),
                    "evaluations": len(evals)}))


# ---------------------------------------------------------------------------
# S6: the knock scale (PLAN.md 5.2 S6; decision 51)
# ---------------------------------------------------------------------------
def s6_knock(rows, *, name, values, jobs, view, conventions, dtheta):
    """S6 (decision 51): knock_a such that the geometric mean of the knock integral
    over the calibration High Load Final rows (with a lambda, no sentinel) is 1.
    KI is proportional to 1/knock_a (plant.run_cycle: tau = knock_a x ...), so one
    sweep at the B58's knock_a and knock_a <- knock_a_B58 x exp(mean ln KI); the
    rows are run again at the result and |mean ln KI| < 1e-12 is asserted (a
    failure would mean KI is not 1/knock_a, a coding defect). A row whose KI is 0
    has no logarithm: left out, flagged. KI's spread is reported (a descriptive check
    of the correlation's shape)."""
    use = [r for r in rows if _final(r) and _has_lam(r) and _no_sentinel(r)]
    if not use:
        raise FitDefect("S6: no calibration High Load Final row with a lambda")
    ref = float(_b58_cycle().knock_a)

    def ki_at(knock_a):
        v = _deep(values)
        v["cycle"]["knock_a"] = float(knock_a)
        model = RowModel(candidate(name, v), fuels=view.fuel_by_table)
        xs = _inputs(use, view=view, conventions=conventions, model=model)
        res = _map(_cycle_job, [(model._engine_for(x.fuel), x, dtheta) for x in xs], jobs)
        return np.array([o.knock_integral for o in res], dtype=float)

    ki0 = ki_at(ref)
    pos = ki0 > 0.0
    if not pos.any():
        raise FitDefect("S6: the knock integral is 0 at every Final row")
    knock_a = float(ref * math.exp(float(np.mean(np.log(ki0[pos])))))
    ki1 = ki_at(knock_a)
    m1 = float(np.mean(np.log(ki1[pos])))
    if not abs(m1) < S6_TOL:
        raise FitDefect(f"S6: after the rescale the mean ln KI is {m1!r}, not below {S6_TOL!r} (KI is not 1/knock_a)")
    flags = [] if pos.all() else ["S6_zero_ki_rows"]
    return StageResult(
        stage="S6", values={"knock_a": knock_a}, rows_used=int(pos.sum()),
        rows_excluded=_py({"ki_zero": [_key(r) for r, p in zip(use, pos) if not p],
                           "not_final_or_no_lambda": [_key(r) for r in rows
                                                      if not (_final(r) and _has_lam(r) and _no_sentinel(r))]}),
        flags=tuple(flags), bounds_active=(), convergence=None,
        report=_py({"knock_a": knock_a, "mean_ln_ki": m1, "knock_a_swept_at": ref,
                    "ki_spread": {"min": float(ki1.min()), "p50": float(np.median(ki1)), "max": float(ki1.max())},
                    "rows": int(pos.sum())}))


# ---------------------------------------------------------------------------
# verify (PLAN.md 5.2 Verify; amendment D10; mistake 10)
# ---------------------------------------------------------------------------
def _unmoved(stages):
    """The fitted parameters of S2 and S4 whose estimate is their DECLARED start's
    double, bit for bit (PLAN.md 5.2 Verify, "every fitted parameter moved"; mistake
    25: an output that does not move after its input changed means check that the
    input reached it). The declared starts are the ones amendment D10 asserts the
    columns at: S2's the B58's typed curve with the B and D terms at 0, S4's its
    first start (the B58's at form A, the previous form's solution after it). Not a
    run's own start: on noise-free rows the weakest direction's sd is 0, its two
    starts sit on the optimum, and a run that takes no step from there is not a
    parameter that never moved. Reported and flagged, never raised: a start on a
    bound may stay there (a bound hit, flagged by its stage)."""
    out = {}
    s2 = stages.get("S2")
    if s2 is not None and isinstance(s2.report, dict) and s2.report.get("declared_start"):
        st, est = s2.report["declared_start"], s2.values
        out["S2"] = [n for n in est if n in st and _bits(st[n]) == _bits(est[n])]
    s4 = stages.get("S4")
    if s4 is not None and isinstance(s4.report, dict) and s4.report.get("starts"):
        first = s4.report["starts"][0]["x0"]
        out["S4"] = [n for n in S4_PARAMS if _bits(first[n]) == _bits(s4.values[n])]
    return out


def verify(rows, *, name, values, jobs, view, conventions, dtheta, stages):
    """Every shortcut the stages took equals a direct plant.run_cycle of the final
    candidate (engines.build_candidate of `values`, the plant get() will build;
    mistake 10): S4's cached cycles with FMEP and UA_PORT applied after -- torque,
    TIT and the model fuel its efficiency residual divides by -- within 1e-9
    relative, and S2's VE target, VE x the unit-VE air, against run_cycle's air
    within 1e-12, both on every row of S2 and S4 at the FINAL constants (S2 checked
    its own at its own constants; the rich slope and the knock scale set after it
    must not reach the air, and this shows they do not). A departure is a coding
    defect, raised. Reported beside it: the stages' zero Jacobian columns at their
    optima (a pre-declared outcome, D10), that every column was non-zero at the start
    values (asserted when each stage began), and the parameters that did not move
    from their start (_unmoved)."""
    cand = candidate(name, values)
    model = RowModel(cand, fuels=view.fuel_by_table)
    e = cand.engine
    short = stages["S4"].report.get("shortcut") or {}
    keys = sorted(set(short) | {_skey(r) for r in _s2_use(rows)})
    by_key = {_skey(r): r for r in rows}
    missing = [k for k in short if k not in by_key]
    if missing:
        raise FitDefect(f"verify: S4's shortcut names rows the fit was not given: {missing[:3]} (a count)")
    pick = [by_key[k] for k in keys]
    xs = _inputs(pick, view=view, conventions=conventions, model=model)
    res = _map(_cycle_job, [(model._engine_for(x.fuel), x, dtheta) for x in xs], jobs)
    worst = 0.0
    for r, o in zip(pick, res):
        s = short.get(_skey(r))
        if s is None:
            continue
        for q, d in (("torque_nm", o.torque_nm), ("egt_c", o.egt_c), ("mdot_fuel_gps", o.mdot_fuel_gps)):
            if q in s:
                worst = max(worst, abs(d - s[q]) / max(abs(d), 1e-300))
    if worst > VERIFY_REL:
        raise FitDefect(f"verify: a shortcut departs from run_cycle by {worst!r} relative (mistake 10)")
    rpm = np.array([x.rpm for x in xs], dtype=float)
    mp = np.array([x.map_kpa for x in xs], dtype=float)
    cam = np.array([engine_env.BaselineECU(e.ecu).cam_deg(a, b) for a, b in zip(rpm, mp)], dtype=float) \
        if "D" in _terms(e.cycle.form) else None
    air_short = plant_ve(rpm, mp, cam, e) * _air_at_unit_ve(e, rpm, mp, np.array([x.iat_k for x in xs]))
    air_worst = max((abs(o.mdot_air_gps - s) / abs(o.mdot_air_gps) for o, s in zip(res, air_short)), default=0.0)
    if air_worst > S2_VERIFY_REL:
        raise FitDefect(f"verify: run_cycle's air at the final constants departs from VE x unit air by "
                        f"{air_worst!r} relative (mistake 10)")
    zero = {k: st.report.get("zero_columns_at_optimum") for k, st in stages.items()
            if isinstance(st.report, dict) and st.report.get("zero_columns_at_optimum")}
    unmoved = _unmoved(stages)
    flags = ["verify_zero_columns_at_optimum"] if zero else []
    if any(unmoved.values()):
        flags.append("verify_unmoved_parameter")
    # PLAN.md 5.6: "a VE at its clip on any calibration row" -- every calibration row the in-sample stage
    # evaluates, at the FINAL constants, not S2's rows alone (WP3's fix of 23 October 2026, on the fit
    # review's finding): the plant's own VE (its clip included) read at each row's speed, MAP and cam; a value
    # equal to ve_lo or ve_hi is at the rail
    all_x = _inputs(rows, view=view, conventions=conventions, model=model)
    a_rpm = np.array([x.rpm for x in all_x], dtype=float)
    a_mp = np.array([x.map_kpa for x in all_x], dtype=float)
    a_cam = (np.array([engine_env.BaselineECU(e.ecu).cam_deg(a, b) for a, b in zip(a_rpm, a_mp)], dtype=float)
             if "D" in _terms(e.cycle.form) else None)
    ve_all = plant_ve(a_rpm, a_mp, a_cam, e)
    at_clip = [_key(r) for r, v in zip(rows, ve_all) if v <= e.cycle.ve_lo or v >= e.cycle.ve_hi]
    if at_clip:
        flags.append("verify_ve_at_clip")
    return StageResult(
        stage="verify", values={}, rows_used=len(pick), rows_excluded={}, flags=tuple(flags), bounds_active=(),
        convergence=None,
        report=_py({"max_rel_shortcut": worst, "s2_verify_max_rel": stages["S2"].report.get("verify_max_rel"),
                    "max_rel_air_at_final": air_worst, "rows_s4_shortcut": len(short), "rows_air": len(pick),
                    "nonzero_columns_at_start": True, "zero_columns_at_optimum": zero,
                    "unmoved_from_start": unmoved, "ve_at_clip_rows": at_clip, "rows_ve_checked": len(rows),
                    "tolerances": {"shortcut": VERIFY_REL, "s2_air": S2_VERIFY_REL}}))


# ---------------------------------------------------------------------------
# A form, fitted (PLAN.md 5.2-5.4; decision 49)
# ---------------------------------------------------------------------------
_STAGE_ORDER = ("S1", "S2", "S3a", "S3b", "S3c", "S3d", "S4", "S5", "S6", "verify")


def _assemble(form, cycle_base, stages):
    """The derived file's frozen sections from the stages run so far (PLAN.md 5.8):
    the cycle from `cycle_base` (the previous form's, or the B58's start) moved by
    every stage's values, the terms the form does not use at their neutral values
    (ve_map 0.0 without B, ve_cam 0.0 and the cam schedule's zeros without D, the
    shared slope without C), the ECU from S3a, S3b and S3d, the envelope from S3c.
    Every value a Python scalar (amendment B10)."""
    t = _terms(form)
    cyc = {k: cycle_base[k] for k in CYCLE_FIELDS}
    cyc["form"] = form
    for k in ("S1", "S2", "S4", "S5", "S6"):
        if k in stages:
            cyc.update(stages[k].values)
    if "B" not in t:
        cyc["ve_map"] = 0.0
    if "D" not in t:
        cyc["ve_cam"] = 0.0
    if "C" not in t:
        cyc["ce_rich_slope"] = float(engines.SHARED_RICH_SLOPE)
    ecu = {k: 0.0 for k in ECU_FIELDS}
    ecu["cam_on"] = 0
    for k in ("S3a", "S3b", "S3d"):
        if k in stages:
            ecu.update(stages[k].values)
    if "D" not in t:
        ecu.update({k: 0.0 for k in engines.CAM_SCHEDULE}, cam_on=0)
    b = stages["S3c"].values
    out = {"cycle": {k: (cyc[k] if k == "form" else float(cyc[k])) for k in CYCLE_FIELDS},
           "ecu": {k: (int(ecu[k]) if k == "cam_on" else float(ecu[k])) for k in ECU_FIELDS},
           "boost_ceiling": {"envelope_flow": [float(x) for x in b["envelope_flow"]],
                             "envelope_pr": [float(x) for x in b["envelope_pr"]], "pr_cap": float(b["pr_cap"])}}
    return out


def _start_cycle(start):
    """The cycle constants a fit starts from: the B58's typed ones for form A (PLAN.md
    5.2: 'start at the B58's'), the previous form's solution after it (PLAN.md 5.4:
    'from A's solution with the new term at 0')."""
    if start is None:
        c = _b58_cycle()
        out = {k: (c.form if k == "form" else float(getattr(c, k))) for k in CYCLE_FIELDS}
        out.update(ve_map=0.0, ve_cam=0.0, ce_rich_slope=float(engines.SHARED_RICH_SLOPE))
        return out
    return dict(start.values["cycle"])


def _fit(name, yield_, *, view, form, conventions, start, keep, jobs, dtheta):
    rows = cal_rows(yield_)
    base = _base_plant(name, form)
    if float(base.engine.ecu.lam_floor) != float(view.lam_floor):
        raise FitDefect(f"{name}: the spec's ecu.lam_floor {base.engine.ecu.lam_floor!r} is not the contract's "
                        f"{view.lam_floor!r} (test_carried.py pins both)")
    cens = epa_stats.censoring([r for r in rows if _final(r)])
    t = _terms(form)
    st = {"S1": s1_backpressure(rows, view=view),
          "S3a": s3a_spark(rows, plant=base, view=view),
          "S3b": s3b_lambda(rows, plant=base, view=view, censoring=cens, lam_floor=float(view.lam_floor),
                            conventions=conventions),
          "S3c": s3c_envelope(rows, plant=base, view=view, conventions=conventions)}
    if "D" in t:
        st["S3d"] = s3d_cam(rows, view=view)
    cyc0 = _start_cycle(start)
    values = _assemble(form, cyc0, st)
    if "S2" in keep:
        st["S2"] = start.stages["S2"]
    else:
        st["S2"] = s2_breathing(rows, plant=candidate(name, values), view=view, form=form,
                                conventions=conventions, dtheta=dtheta, jobs=jobs)
    values = _assemble(form, cyc0, st)
    if "S4" in keep:
        st["S4"] = start.stages["S4"]
    else:
        st["S4"] = s4_burn(rows, name=name, values=values, view=view, form=form, jobs=jobs,
                           conventions=conventions, dtheta=dtheta, start={n: cyc0[n] for n in S4_PARAMS})
    values = _assemble(form, cyc0, st)
    if "C" in t:
        st["S5"] = s5_rich_slope(rows, name=name, values=values, s4=st["S4"], jobs=jobs, view=view,
                                 conventions=conventions, dtheta=dtheta)
        values = _assemble(form, cyc0, st)
    st["S6"] = s6_knock(rows, name=name, values=values, jobs=jobs, view=view, conventions=conventions,
                        dtheta=dtheta)
    values = _assemble(form, cyc0, st)
    st["verify"] = verify(rows, name=name, values=values, jobs=jobs, view=view, conventions=conventions,
                          dtheta=dtheta, stages=st)
    candidate(name, values)        # engines.Engine's invariants on the frozen values (HANDOFFS.md WP3 item 1)
    stages = {k: st[k] for k in _STAGE_ORDER if k in st}
    flags = tuple(f for s in stages.values() for f in s.flags)
    return FormFit(engine=name, form=form, stages=stages, values=values,
                   frozen_sections_sha256=engines.frozen_sections_sha256(values), flags=flags)


def fit_form(name, yield_, *, view, form, start, jobs, dtheta):
    """One form of one engine on its calibration rows (PLAN.md 5.2-5.3): S1, S3a-S3c
    (S3d under D), S2, S4, S5 under C, S6, verify. `start` is the previous form's
    FormFit (None for form A, which starts at the B58's). Under A+B+C, A+B's S2 and
    S4 are kept (PLAN.md 5.3: the rich slope moves neither, since S4's rows run at
    lambda 1.00); every other form refits each stage it has. Every argument is a
    required keyword: the engine by name (engines.PLANTS), the crank step dtheta
    included (no call relies on a default, WP3_INTERFACES.md 2.2)."""
    return _fit(name, yield_, view=view, form=form, conventions=epa_stats.NOMINAL, start=start,
                keep=_keep(form, start), jobs=jobs, dtheta=dtheta)


def _keep(form, start):
    """The ladder's keep policy (PLAN.md 5.3), one definition for the ladder and the refit variants: A+B+C
    keeps A+B's S2 and S4 (its start's), every other form refits each stage it has."""
    return ("S2", "S4") if (form == "A+B+C" and start is not None and start.form == "A+B") else ()


def _kernel(pair):
    model, task = pair
    return epa_stats.kernel_point(model, task)


def evaluate_rows(name, values, rows, *, view, conventions, jobs, dtheta):
    """Every calibration row's epa_stats.RowEval on the candidate of `values` (its
    needs by epa_stats.default_needs: EPA's MAP, D1's inversion, lambda 1, the ECU),
    the censored flag marked by the calibration Final rows' own test
    (epa_stats.censoring and mark_censored, contract section 3)."""
    model = RowModel(candidate(name, values), fuels=view.fuel_by_table)
    tasks = [epa_stats.make_task(r, view=view, conventions=conventions, dtheta=dtheta,
                                 needs=epa_stats.default_needs(r), shift=None) for r in rows]
    evals = _map(_kernel, [(model, t) for t in tasks], jobs)
    return epa_stats.mark_censored(evals, censoring=epa_stats.censoring([r for r in rows if _final(r)]))


def in_sample_for(name, fit, yield_, *, view, jobs, dtheta):
    """The in-sample stage of one fitted form (PLAN.md 5.5; contract section 2.4):
    every calibration steady and Final row evaluated on the form's candidate
    (sentinel rows at the model ECU's spark, rows without lambda at 1.00, decision
    54), then epa_stats.in_sample, the one definition the held-out run shares, its
    criterion decision 77's (each gating statistic judged with the held-out run's
    u_stat: fails, passes, or neither when its noise exceeds R)."""
    rows = cal_rows(yield_)
    evals = evaluate_rows(name, fit.values, rows, view=view, conventions=epa_stats.NOMINAL, jobs=jobs,
                          dtheta=dtheta)
    return epa_stats.in_sample(evals, view=view)


def _beside(s):
    """The statistics of one form's in-sample stage that neither block nor pass, for the ladder's reason (decision
    55's no line, decision 77's noise exceeding R): '' when there are none."""
    parts = (([f"no line: {', '.join(s.no_line)}"] if s.no_line else [])
             + ([f"noise exceeds R: {', '.join(s.noise)}"] if s.noise else []))
    return f" ({'; '.join(parts)})" if parts else ""


def ladder_choice(in_sample):
    """(chosen form, reason) from the in-sample stages of the forms fitted, in the ladder's order
    (engines.CYCLE_FORMS; `in_sample` {form: epa_stats.InSample}): the first form at which no statistic but E8
    fails (decision 77: a statistic fails only if |E_cal| - 2 u_stat > R; one with no calibration line, decision
    55, or whose noise exceeds R neither blocks nor passes, and the reason names both per form), else A+B+C+D
    with its failing statistics (contract section 2.4). The one definition of the choice and its reason, for
    the ladder and for calibrate_epa.py check, which recomputes the in-sample stage and must give in_sample.json
    back byte for byte (PLAN.md 6.1; mistake 10). Split out of the ladder by WP3's integration, 23 October
    2026; decision 77's reading the same day."""
    forms = [f for f in engines.CYCLE_FORMS if f in in_sample]
    if not forms or forms != list(engines.CYCLE_FORMS[:len(forms)]) or set(in_sample) != set(forms):
        raise ValueError(f"ladder_choice: the forms fitted {sorted(in_sample)} are not the ladder's first "
                         f"{len(forms)} of {engines.CYCLE_FORMS}")
    reasons, chosen = [], None
    for i, form in enumerate(forms):
        s = in_sample[form]
        if s.passes:
            if i != len(forms) - 1:
                raise ValueError(f"ladder_choice: {form} passes, and a form after it was fitted")
            chosen = form
            reasons.append(f"{form}: no in-sample statistic but E8 fails" + _beside(s))
            break
        reasons.append(f"{form}: fails {', '.join(s.failing)}" + _beside(s)
                       + (f" ({D13_DECLARATION})" if form == "A" and "E1a" in s.failing else ""))
    if chosen is None:
        if len(forms) != len(engines.CYCLE_FORMS):
            raise ValueError(f"ladder_choice: no form of {forms} passes, and the ladder stopped before "
                             f"{engines.CYCLE_FORMS[-1]}")
        chosen = engines.CYCLE_FORMS[-1]
        reasons.append("no form passes: A+B+C+D, its failing statistics reported (contract section 2.4)")
    return chosen, "; ".join(reasons)


def form_record(ins):
    """One form's in-sample stage as decision 77 reads it, per gating statistic: {row: {E, u_stat, R, outcome,
    why}} (outcome fails, passes or neither; None where the statistic has no statistic, decision 55, its reason
    in why). The ladder's record beside its choice (T0's ladders; in_sample.json carries the same in each
    statistic's JSON, epa_stats.StatResult.as_json)."""
    out = {}
    for r, res in ins.results.items():
        if r not in epa_stats.IN_SAMPLE_GATING:
            continue
        j = res.judgement
        out[r] = {"E": res.E, "u_stat": None if j is None else j["u_stat"], "R": res.R,
                  "outcome": None if j is None else j["outcome"], "why": res.reason if j is None else j["why"]}
    return _py(out)


def _ladder(name, yield_, *, view, jobs, dtheta, judge):
    fits, ins, prev = [], {}, None
    for form in engines.CYCLE_FORMS:
        fit = fit_form(name, yield_, view=view, form=form, start=prev, jobs=jobs, dtheta=dtheta)
        s = judge(name, fit, yield_, view=view, jobs=jobs, dtheta=dtheta)
        fits.append(fit)
        ins[form] = s
        if s.passes:            # no statistic but E8 fails (decision 77): the ladder moves on only on a "fails"
            break
        prev = fit
    chosen, reason = ladder_choice(ins)
    return Ladder(engine=name, fits=tuple(fits), in_sample=ins, chosen=chosen, reason=reason)


def ladder(name, yield_, *, view, jobs, dtheta):
    """The per-engine ladder (decision 49; contract section 2.4, which supersedes
    PLAN.md 5.4's common ladder, as decision 77 reads it): form A; its in-sample
    stage; if no statistic but E8 fails -- fails meaning |E_cal| - 2 u_stat > R, a
    statistic whose noise exceeds R (2 u_stat > R) or with no calibration line
    (decision 55) neither blocking nor passing -- A is the engine's form, else A+B
    from A's solution with the new term at 0, and so on: the ladder moves on only
    on a "fails". If every form fails, A+B+C+D with its failing statistics. Forms
    after the chosen one are not fitted; every form fitted is kept (fit_<form>.json)."""
    return _ladder(name, yield_, view=view, jobs=jobs, dtheta=dtheta, judge=in_sample_for)


POISON_STAGES = ("S1", "S2", "S3a", "S3b", "S3c", "S3d", "S6")
# The stages the poison's reference must also equal as the chosen fit recorded them (fit_<form>.json): those
# the fit ran at _base_plant from the rows alone, so the same at the frozen form as at the fit (S2 and S6 run
# there at other values, S4 is not a poison stage); S3d where the form has D (poison_tied_stages). Here,
# beside POISON_STAGES, so that calibrate_epa.py poison and the record check (epa_freeze.poison_problems, by
# its callers) read one definition (WP3's second fix of 23 October 2026, mistake 10).
POISON_TIED_STAGES = ("S1", "S3a", "S3b", "S3c")
# The comparisons every poisoned run records (calibrate_epa.py poison; poison.json's runs), besides its stages.
POISON_RUN_KEYS = ("copies_are_not_the_tables", "stage0_equal", "view_equal", "yield_equal", "manifest_equal",
                   "engine_facts_equal", "stages", "full_form_a")


def poison_tied_stages(form):
    """The reference stages tied to the fit at `form` (POISON_TIED_STAGES, and S3d under D)."""
    return POISON_TIED_STAGES + (("S3d",) if "D" in str(form).split("+") else ())


def poison_run_stages():
    """The stages of one poisoned run's record: S0 (against stage0.json) and POISON_STAGES."""
    return ("S0",) + POISON_STAGES


def poison_stages(name, yield_, *, view, values, jobs, dtheta):
    """Amendment C8's poison fit of S0-S3 and S6 (WP3_INTERFACES.md 5.5.1, poison.json's `stages`; S0 is
    s0's own): the stages _fit runs before and after S4, called as it calls them, on `yield_` and at the
    frozen sections `values` (S2's candidate and S6's), each a StageResult. S3d runs whatever the form,
    since the cam schedule's rows are the poison's question; an engine whose calibration rows carry no cam
    value gives None there (s3d_cam's FitDefect). calibrate_epa.py poison runs it on the real yield and
    on each poisoned one and requires the two byte-identical (stage_json, canonical). Added by WP3's
    integration, 23 October 2026, so the poison run calls the stages the fit calls, through the fit's own
    bases (mistake 10)."""
    rows = cal_rows(yield_)
    form = values["cycle"]["form"]
    base = _base_plant(name, form)
    cens = epa_stats.censoring([r for r in rows if _final(r)])
    conv = epa_stats.NOMINAL
    out = {"S1": s1_backpressure(rows, view=view),
           "S3a": s3a_spark(rows, plant=base, view=view),
           "S3b": s3b_lambda(rows, plant=base, view=view, censoring=cens, lam_floor=float(view.lam_floor),
                             conventions=conv),
           "S3c": s3c_envelope(rows, plant=base, view=view, conventions=conv)}
    try:
        out["S3d"] = s3d_cam(rows, view=view)
    except FitDefect:
        out["S3d"] = None
    out["S2"] = s2_breathing(rows, plant=candidate(name, values), view=view, form=form, conventions=conv,
                             dtheta=dtheta, jobs=jobs)
    out["S6"] = s6_knock(rows, name=name, values=values, jobs=jobs, view=view, conventions=conv, dtheta=dtheta)
    return {k: out[k] for k in POISON_STAGES}


# ---------------------------------------------------------------------------
# What fit_<form>.json and stage0.json record of the fit (WP3_INTERFACES.md 7.2)
# ---------------------------------------------------------------------------
# Decision 53's rule for the HD1's barometer, as stage0.json declares it (amendment
# C1: from the yield, never the all-row 97.6 kPa the plan typed).
HD1_BAROMETER = ("decision 53 as amendment C1 sets it: the rows that publish no cell pressure (the Ford's HD1) "
                 "take the median of the calibration rows that do (Cell 9's), and S3c's envelope is recomputed "
                 "at both ends of their range (the sweep); the cell temperature follows the same rule")


def fit_settings(name, *, view, form, dtheta, jobs):
    """fit_<form>.json's `settings` (WP3_INTERFACES.md 7.2): every declared setting
    the form's fit ran with, read from this module's constants (one definition), with
    ve_rpm's bounds the engine's end lines from the view (D9). The tolerances are per
    stage, since S2's and S4's differ (TOLERANCES). `jobs` is recorded, and moves no
    other output (FitForm's byte-identity test)."""
    t = _terms(form)
    s2, c = s2_names(form), (("ce_rich_slope",) if "C" in t else ())
    fitted = ("exh_bp_ratio", "exh_bp_min_kpa") + s2 + S4_PARAMS + c
    rlo, rhi = _rpm_ends(view)
    centre = ridge_centre()
    return _py({
        "engine": name, "form": form, "ridge_w": RIDGE_W,
        "ridge_centre": {n: centre[n] for n in fitted if n in SCALES},
        "ridge_scale": {n: SCALES[n] for n in fitted if n in SCALES},
        "bounds": {n: list((rlo, rhi) if n == "ve_rpm" else BOUNDS[n]) for n in fitted},
        "starts": {"S2": "the variable projection's best grid point: ve_rpm on the calibration lines' speeds x "
                         "ve_width on s2_width_grid, the linear terms by lsq_linear (amendment D9)",
                   # PLAN.md 5.4 starts A+B and later forms "from A's solution with the new term at 0"; S2 does not:
                   # its variable projection searches its grid afresh at every form and the polish starts from the
                   # grid's best point, so the previous form's S2 solution is not used. Deterministic either way;
                   # declared here (WP3's second fix of 23 October 2026, on the fit review's finding)
                   "S2_deviation_from_plan_5_4": S2_START_DEVIATION,
                   "S4": {"factors": list(S4_START_FACTORS), "weakest_direction_sd": [1.0, -1.0],
                          "of": "the B58's typed constants at form A, the previous form's solution after it "
                                "(PLAN.md 5.4); the weakest direction's two at the best of the first three "
                                "(amendment D6)",
                          "polish": "the start that stopped lowest, once more at TOLERANCES['S4_polish']"},
                   "S5": "bounded Brent on the slope's bounds" if c else None},
        "x_scale": {n: X_SCALE[n] for n in s2 + S4_PARAMS},
        "ftol": {k: v["ftol"] for k, v in TOLERANCES.items()},
        "xtol": {k: v["xtol"] for k, v in TOLERANCES.items()},
        "gtol": {k: v["gtol"] for k, v in TOLERANCES.items()},
        "max_nfev": MAX_NFEV, "second_attempt_nfev": SECOND_ATTEMPT_NFEV,
        "dtheta_deg": float(dtheta), "jobs": int(jobs),
        "fd_cad": FD_CAD, "s1_grid_kpa": S1_GRID_KPA, "s2_width_grid": list(S2_WIDTH_GRID),
        "s3a": {"max_iter": S3A_MAX_ITER, "min_rows": dict(S3A_MIN_ROWS)},
        "s3b": {"gate_step_kpa": S3B_GATE_STEP_KPA, "gate_design_kpa": S3B_GATE_DESIGN_KPA,
                "rpm_span_min": S3B_RPM_SPAN_MIN, "rpm_lo_below": list(S3B_RPM_LO_BELOW), "dwell_s": S3B_DWELL_S},
        "s3c_filter_loss_kpa": S3C_FILTER_LOSS_KPA, "s5_xatol": S5_XATOL, "s6_tol": S6_TOL,
        "verify_rel": VERIFY_REL, "s2_verify_rel": S2_VERIFY_REL, "spark_ref_kpa": SPARK_REF_KPA,
        "provisional_completion": _completion()})


S2_START_DEVIATION = ("PLAN.md 5.4 starts A+B and later forms from A's solution with the new term at 0; S2 starts "
                      "every form from its variable projection's best grid point instead (the previous form's S2 "
                      "solution is not used), and amendment D10's non-zero-column assertion is made at the B58's "
                      "curve; S4 does start from the previous form's solution")


def stage_json(st):
    """One StageResult as fit_<form>.json writes it (WP3_INTERFACES.md 7.2): values,
    rows_used, rows_excluded, flags, bounds_active, convergence (or null), report."""
    return _py({"values": st.values, "rows_used": st.rows_used, "rows_excluded": st.rows_excluded,
                "flags": list(st.flags), "bounds_active": list(st.bounds_active),
                "convergence": None if st.convergence is None else dataclasses.asdict(st.convergence),
                "report": st.report})


def fit_declarations(plant, *, view, other_octane, dtheta):
    """fit_<form>.json's `declarations` (WP3_INTERFACES.md 7.2; HANDOFFS.md WP3 item
    5). An engine whose tables are all on one fuel batch (one FTAG in the view's
    fuel_by_table: the Mazda, the Honda) has no octane question: both fields null.
    One on two batches (the Ford: Cell 9's FTAG beside HD1's) runs every row at its
    typed octane (FORD_CELL9_OCTANE), and the claim behind that choice is measured
    here at the fitted candidate `plant`: octane_moves_only_knock at `other_octane`,
    the other batch's RON, which the caller reads from epa_rows.engine_facts'
    alpha_fuel (this module opens nothing). The claim failing is a coding defect,
    raised: the declaration written beside it would be false (mistake 24)."""
    batches = sorted({str(tf.ftag) for tf in view.fuel_by_table.values()})
    if len(batches) == 1:
        return {"octane_moves_only_knock": None, "ford_cell9_octane": None, "fuel_batches": batches}
    if other_octane is None:
        raise ValueError(f"the engine's tables are on {len(batches)} fuel batches ({batches}): the octane "
                         "claim must be measured at the other batch's octane (HANDOFFS.md WP3 item 5)")
    if float(other_octane) == float(plant.engine.cycle.octane):
        # octane_moves_only_knock holds trivially at the plant's own octane (nothing moves): the claim is
        # measured only at another (WP3's fix of 23 October 2026, on the test review's finding)
        raise ValueError(f"the octane claim must be measured at an octane other than the plant's own "
                         f"{plant.engine.cycle.octane!r}")
    ok = octane_moves_only_knock(plant, octane=other_octane, grid=synthetic_grid(plant), dtheta=dtheta)
    if not ok:
        raise FitDefect(f"the octane {other_octane!r} moves a cycle output other than the knock integral and "
                        "knock_prob, or moves nothing: FORD_CELL9_OCTANE's claim is false")
    return {"octane_moves_only_knock": True, "ford_cell9_octane": FORD_CELL9_OCTANE,
            "octane_compared": float(other_octane), "fuel_batches": batches}


def fit_record(fit, *, view, start, dtheta, jobs, declarations):
    """fit_<form>.json without its provenance (WP3_INTERFACES.md 7.2; calibrate_epa
    adds epa_freeze.provenance and writes it with write_json_atomic): the form, where
    it started (`start`: the previous form's FormFit, None for the B58's start at
    form A) with the start values' hash, the settings, every stage, the frozen
    sections and their hash, the declarations (fit_declarations) and the flags."""
    return _py({"schema": "epa-fit/1", "form": fit.form,
                "start": {"from": "B58" if start is None else start.form,
                          "values_sha256": epa_rows.canonical_sha256(_py(_start_cycle(start)))},
                "settings": fit_settings(fit.engine, view=view, form=fit.form, dtheta=dtheta, jobs=jobs),
                "stages": {k: stage_json(v) for k, v in fit.stages.items()},
                "values": fit.values, "frozen_sections_sha256": fit.frozen_sections_sha256,
                "declarations": declarations, "flags": list(fit.flags)})


def stage0_declarations(yield_, *, view):
    """stage0.json's `declarations` (WP3_INTERFACES.md 7.2): the octane choice where
    the engine's tables are on two fuel batches (the Ford), decision 53's barometer
    rule where some calibration rows publish no cell pressure (the Ford's HD1; read
    off the yield, the rule's own trigger), the DESIGN spark reference, and the
    provisional completion values the fit's candidates carry."""
    two = len({str(tf.ftag) for tf in view.fuel_by_table.values()}) > 1
    no_baro = _cell_rule(cal_rows(yield_), "baro_kpa") is not None
    return {"ford_cell9_octane": FORD_CELL9_OCTANE if two else None,
            "hd1_barometer": HD1_BAROMETER if no_baro else None,
            "spark_ref_kpa": {"value": SPARK_REF_KPA, "label": "DESIGN"},
            "provisional_completion": _completion(),
            "no_statistic_outcomes": list(NO_STATISTIC_OUTCOMES),
            "d1_torque_target_u_d": epa_stats.D1_TORQUE_TARGET_U_D}


# Three outcomes the contract's section 7 does not write, which epa_stats reads as "no statistic" (declared
# here, before Run 1, WP3's fix of 23 October 2026 on the contract review's finding; held out, a d row
# without a statistic drops the engine, section 7; in-sample, a statistic without a statistic neither blocks
# nor passes a form, decision 55, which names only the line-minimum case).
NO_STATISTIC_OUTCOMES = (
    "E4b: a line whose boosted lambda~1 rows share one MAP has no reference line and decides nothing; with no "
    "other deciding line E4b has no statistic",
    "E4b: a data lever that sums to zero over the deciding lines leaves eps undefined: no statistic",
    "E4b held out: with fewer than 2 enriched rows over the deciding lines the pooled u_stat is undefined (the "
    "enriched side has no variance of its own), so E4b is labelled but cannot certify, and reads untested unless "
    "it is off (WP3's second fix of 23 October 2026)",
    "E4b in-sample: on the same fewer than 2 enriched rows the u_stat decision 77's rule needs is undefined, so "
    "the statistic can neither be shown to fail beyond its noise (|E_cal| - 2 u_stat > R) nor pass (2 u_stat <= R): "
    "it neither blocks a form nor passes it, recorded per form with its noise-exceeding statistics (epa_stats."
    "NO_U_STAT; declared 23 October 2026, before Run 1, with decision 77)",
    "C3b and C3d: a row whose u_val is incomplete (u_num, u_D or u_stat missing) has no statistic; the C3 "
    "chain's u-terms are read from the D3 files, which the arming hashes and the run first reads (C5), so "
    "this is a declared outcome of the one run, not an arm-time check")


# ---------------------------------------------------------------------------
# E6's refit variants and probes (PLAN.md 5.7; amendments E2, E3; HANDOFFS.md WP3 items 3, 5)
# ---------------------------------------------------------------------------
def refit_variant(name, yield_, *, view, form, conventions, ladder_fits, jobs, dtheta):
    """E6 rows 1-3 (PLAN.md 5.7): the frozen form's own fit, re-run under the variant's
    conventions (row 1: cell_referenced False, the snap kept; row 2: AFR_st 14.7 in
    the calibration air and the rows' fuel; row 3: LHV 44.0 MJ/kg through
    engines.with_fuel), no new ladder. RE-RUN AS THE FROZEN FORM RAN (WP3's fix of 23
    October 2026, on the fit review's finding: a refit started from the frozen solution
    moved S4 and S6 under a convention that changes nothing, so start-dependence mixed
    into E6's movement): S4's first start is the one the frozen form's S4 had -- the
    B58's at form A, the frozen previous form's solution after it -- and the ladder's
    keep policy applies as it did, so at A+B+C the variant's own A+B (S2 and S4 from
    the frozen A's solution) is fitted first and its S2 and S4 kept. A convention that
    moves no row input then gives the frozen sections bit for bit. `ladder_fits` maps
    each form the frozen ladder fitted, up to `form`, to its FormFit (its values; no
    stages needed). The plant in use stays the frozen one; validate_epa reports how far
    the model in use moves (amendment E2)."""
    forms = engines.CYCLE_FORMS[:engines.CYCLE_FORMS.index(form) + 1]
    missing = [f for f in forms if f not in ladder_fits]
    if missing:
        raise ValueError(f"refit_variant: the frozen ladder's fits {sorted(ladder_fits)} lack {missing}")
    prev = ladder_fits[forms[-2]] if len(forms) > 1 else None
    if _keep(form, prev):
        before = ladder_fits[forms[-3]] if len(forms) > 2 else None
        prev = _fit(name, yield_, view=view, form=prev.form, conventions=conventions, start=before,
                    keep=_keep(prev.form, before), jobs=jobs, dtheta=dtheta)
    return _fit(name, yield_, view=view, form=form, conventions=conventions, start=prev, keep=_keep(form, prev),
                jobs=jobs, dtheta=dtheta)


def knock_rescale(values, *, factor):
    """E6 row 7 (PLAN.md 5.7; decision 51): the frozen sections with knock_a /
    factor, which is KI x factor exactly, since KI is proportional to 1/knock_a
    (row7_090 is factor 0.90, row7_110 factor 1.10). A new dict; `values` is not
    touched."""
    v = _deep({k: values[k] for k in engines.FROZEN_SECTIONS})
    v["cycle"]["knock_a"] = float(values["cycle"]["knock_a"] / float(factor))
    return v


def perturbed(plant, *, record, field, value):
    """`plant` with one typed or derived constant moved (E6 rows 4, 5, 6, 9, 10):
    `record` is an engine record (geometry, cycle, charge, boost, ecu, thermal,
    damage, loop, fuel) or car or scenario, `field` its field, `value` a Python
    float or int (amendment B10: a NumPy scalar is refused). The fuel moves through
    engines.with_fuel (both heating-value copies together, mistake 25); the thermal
    record's copy of it is refused here. A new plant; the frozen one is untouched."""
    if type(value) not in (float, int):
        raise TypeError(f"perturbed: {record}.{field} = {value!r} ({type(value).__name__}) is not a Python "
                        "float or int (amendment B10)")
    if record in ("car", "scenario"):
        return replace(plant, **{record: replace(getattr(plant, record), **{field: value})})
    if record == "fuel":
        return replace(plant, engine=engines.with_fuel(plant.engine, replace(plant.engine.fuel, **{field: value})))
    if record == "thermal" and field == "fuel_lhv_j_per_kg":
        raise ValueError("perturbed: the thermal record's heating value is the fuel's copy; move record 'fuel'")
    if record not in {f.name for f in dataclasses.fields(engines.Engine)} - {"id", "derived"}:
        raise KeyError(f"perturbed: {record!r} is not a record of the engine, nor car or scenario")
    rec = getattr(plant.engine, record)
    return replace(plant, engine=replace(plant.engine, **{record: replace(rec, **{field: value})}))


def with_rich_slope_probe(plant, *, slope):
    """E6 row 9's probe of the rich slope on any form (amendment E3; HANDOFFS.md
    WP3 item 3): engines.CycleCal refuses a slope other than the shared one
    without form C, so a form A or A+B engine is retagged A+B+C at its own
    breathing terms (ve_map as fitted, 0.0 for A) and given the probed slope; a form
    with C keeps its form. retag_identity must have shown the retag gives the
    engine's own doubles before a probe is read."""
    c = plant.engine.cycle
    form = c.form if "C" in _terms(c.form) else "A+B+C"
    return replace(plant, engine=replace(plant.engine, cycle=replace(c, form=form, ce_rich_slope=float(slope))))


def synthetic_grid(plant):
    """A DESIGN grid of synthetic operating points (no EPA row): 5 speeds over the
    car's [rpm_min + 700, rpm_max - 1500], MAP 40, 100, 160, 220 kPa, spark 5 and
    15 deg, lambda 1.0, 0.95 and 0.85, intake 315 K, coolant 365 K -- for the
    identity checks below, which compare a plant with itself."""
    lo, hi = plant.car.rpm_min + 700.0, plant.car.rpm_max - 1500.0
    out = []
    for rpm in np.linspace(lo, hi, 5):
        for mp in (40.0, 100.0, 160.0, 220.0):
            for sp in (5.0, 15.0):
                for lam in (1.0, 0.95, 0.85):
                    out.append((float(rpm), mp, 315.0, 365.0, sp, lam))
    return tuple(out)


def _grid_results(eng, grid, dtheta, ecu_engine):
    out = []
    for rpm, mp, iat, ect, sp, lam in grid:
        x = epa_stats.RowInputs(engine="", table="", source_row=0, rpm=rpm, map_kpa=mp, iat_k=iat, ect_k=ect,
                                spark_btdc=sp, lam=lam, lam_source="synthetic", spark_source="synthetic", fuel=None)
        out.append(_cycle_at(eng, x, dtheta=dtheta, ecu_engine=ecu_engine))
    return out


def retag_identity(plant, *, grid, dtheta):
    """Whether the retag with_rich_slope_probe makes, at the engine's own slope,
    gives the engine's own doubles at every point of `grid` (every CycleResult
    field, bit for bit; HANDOFFS.md WP3 item 3; amendment B2): form A's breathing
    against A+B+C's at ve_map 0.0, A+B's against A+B+C's at its own ve_map. It is
    asserted, never relaxed, before E6 row 9's probe is read."""
    own = plant.engine
    probe = with_rich_slope_probe(plant, slope=float(own.cycle.ce_rich_slope)).engine
    a = _grid_results(own, grid, dtheta, own)
    b = _grid_results(probe, grid, dtheta, probe)
    return all(_same_result(p, q) for p, q in zip(a, b))


def octane_moves_only_knock(plant, *, octane, grid, dtheta):
    """HANDOFFS.md WP3 item 5 (chosen in WP3_INTERFACES.md 5.3; FORD_CELL9_OCTANE):
    whether running `plant` at another octane moves only knock_integral and
    knock_prob at every point of `grid` (every other CycleResult field bit for bit
    the same), and, when the octane differs, moves knock_integral at some point (so
    the octane reached the cycle: mistake 25). mistake 24: the explanation names a
    quantity, so it is measured."""
    if type(octane) is not float:
        raise TypeError(f"octane {octane!r} must be a Python float (amendment B10)")
    own = plant.engine
    other = replace(own, cycle=replace(own.cycle, octane=octane))
    a = _grid_results(own, grid, dtheta, own)
    b = _grid_results(other, grid, dtheta, other)
    only = all(_same_result(p, q, skip=("knock_integral", "knock_prob")) for p, q in zip(a, b))
    moved = any(_bits(p.knock_integral) != _bits(q.knock_integral) for p, q in zip(a, b))
    return bool(only and (moved or octane == own.cycle.octane))


# ---------------------------------------------------------------------------
# T0: synthetic recovery at the calibration rows' inputs (PLAN.md 5.10; amendments A1, D11)
# ---------------------------------------------------------------------------
# T0's noise, one stream per seed (WP3_INTERFACES.md 5.3, chosen there: a labelled
# stream, as the contract's 0xC5 is): torque 0.5 %, meter 0.5 %, TIT 3 K, spark 0.5
# deg, lambda 0.005 (PLAN.md 5.10), drawn five per row in that order, rows in the
# yield's order.
T0_STREAM = 0x70
T0_NOISE = {"torque_rel": 0.005, "meter_rel": 0.005, "tit_k": 3.0, "spark_deg": 0.5, "lam": 0.005}
# The out-of-form seed's term (amendment D11: "one seed whose truth lies outside the
# model's form"), DESIGN: TIT raised by 20 K per 100 kPa of MAP above 100 kPa, a
# port loss that rises with load in a way no form's UA_PORT, back-pressure or burn
# term can follow.
T0_OUT_OF_FORM_K_PER_100KPA = 20.0


def t0_truths(name, *, view, yield_):
    """T0's truths for one engine (PLAN.md 5.10, amendment D11): seeds 1 and 2 a
    form-A truth -- the B58's typed constants with burn x1.15, delay x0.9, FMEP x1.2,
    UA_PORT x3, the breathing moved, back-pressure 1.45 and 102 kPa, knock_a x1.3 --
    seed 3 the same with ve_map 2e-3 per kPa (form A+B: the ladder must stop there),
    seed 4 the form-A truth with T0_OUT_OF_FORM's term (the judge must fail it).
    The ECU's truth: a declared spark plane, the B58's typed knock-limited surface,
    and an enrichment whose gate lies between the calibration steady rows and the
    Final rows (amendment D2's T0 case), placed from the rows' MAPs (inputs: T0 runs
    at the calibration rows' inputs, amendment A1). `yield_` is an addition to the
    interface's signature: the gate's case needs the rows' MAPs."""
    rows = cal_rows(yield_)
    b = _b58_cycle()
    sp_b58 = engines.read_spec("b58")["ecu"]
    fm = min(r.map_kpa for r in rows if _final(r))
    below = [r.map_kpa for r in rows if not _final(r) and r.map_kpa < fm]
    gate = 0.5 * (max(below) + fm) if below else fm - 5.0
    speeds = _line_speeds(_cal_lines(view))
    lam_floor = float(view.lam_floor)
    cyc = {k: float(getattr(b, k)) for k in CYCLE_FIELDS if k != "form"}
    cyc.update(form="A", burn_base=b.burn_base * 1.15, burn_rpm=b.burn_rpm * 1.15, delay_base=b.delay_base * 0.9,
               delay_rpm=b.delay_rpm * 0.9, fmep_0=b.fmep_0 * 1.2, fmep_pmax=b.fmep_pmax * 1.2,
               fmep_sp=b.fmep_sp * 1.2, fmep_sp2=b.fmep_sp2 * 1.2, ua_port=b.ua_port * 3.0, ve_base=0.83,
               ve_amp=0.18, ve_rpm=float(speeds[len(speeds) // 2]), ve_width=3000.0, exh_bp_ratio=1.45,
               exh_bp_min_kpa=102.0, knock_a=b.knock_a * 1.3, ve_map=0.0, ve_cam=0.0,
               ce_rich_slope=float(engines.SHARED_RICH_SLOPE))
    ecu = {k: 0.0 for k in ECU_FIELDS}
    ecu.update(spark_a=12.0, spark_b=0.004, spark_c=0.10, spark_min=-60.0, spark_max=80.0,
               kl_a=float(sp_b58["kl_a"]), kl_b=float(sp_b58["kl_b"]), kl_c=float(sp_b58["kl_c"]),
               kl_d=float(sp_b58["kl_d"]), enr_load=float(gate), enr_rpm_lo=float(speeds[1]),
               enr_rpm_hi=float(speeds[-1]), enr_depth=float(min(0.15, 0.9 * (1.0 - lam_floor))), cam_on=0)
    boost = {"envelope_flow": [0.0, 1.0], "envelope_pr": [1.0, 1.0], "pr_cap": 1.0}
    a = {"cycle": cyc, "ecu": ecu, "boost_ceiling": boost}
    bb = _deep(a)
    bb["cycle"].update(form="A+B", ve_map=2e-3)
    return (Truth(engine=name, seed=1, label="form A", values=_deep(a), expected_form="A", out_of_form=None),
            Truth(engine=name, seed=2, label="form A", values=_deep(a), expected_form="A", out_of_form=None),
            Truth(engine=name, seed=3, label="form A+B: ve_map 2e-3 per kPa", values=bb, expected_form="A+B",
                  out_of_form=None),
            Truth(engine=name, seed=4, label="outside every form", values=_deep(a), expected_form=None,
                  out_of_form={"tit_k_per_100kpa_above_100": T0_OUT_OF_FORM_K_PER_100KPA}))


def t0_rows(yield_, *, truth, seed, view, dtheta, jobs):
    """T0's synthetic rows (PLAN.md 5.10): the calibration rows' inputs kept --
    speed, MAP, intake, coolant, the table and its fuel -- and every output replaced
    from `truth`: spark and lambda from the truth's ECU (one step at dwell 30 s, the
    lambda written back on the row's cell scale, lambda_ref - 1 added), then torque,
    TIT, the fuel and the meter from plant.run_cycle at the inputs the model will be
    fed (epa_stats.row_inputs of the new row), TIP from the truth's back-pressure law,
    BMEP from the torque; noise T0_NOISE from numpy.random.default_rng([T0_STREAM,
    seed]). The populations are the loader's own for the new values
    (epa_rows.populations, split.classify on the row's strings: amendment D11,
    "populations come from split.classify"), so a row whose lambda moves changes band
    as a real one would. A row without lambda stays without; a sentinel row stays a
    sentinel and runs at the truth ECU's spark. origin "t0". `view`, `dtheta` and
    `jobs` are additions to the interface's signature: the rows run cycles."""
    rows = cal_rows(yield_)
    tp = candidate(truth.engine, truth.values)
    model = RowModel(tp, fuels=view.fuel_by_table)
    rng = np.random.default_rng([T0_STREAM, int(seed)])
    z = rng.standard_normal((len(rows), 5))
    new, xs = [], []
    for r, zi in zip(rows, z):
        ecu = engine_env.BaselineECU(tp.engine.ecu)
        sp_t, lam_t, _fan = ecu.step(r.speed_rpm, r.map_kpa, r.imt_k, r.ect_k, False, S3B_DWELL_S)
        ch = {}
        if not r.spark_sentinel:
            ch["spark_btdc"] = float(sp_t + T0_NOISE["spark_deg"] * zi[3])
        if not r.lambda_missing:
            lm = float(lam_t + (r.lam_ref - 1.0) + T0_NOISE["lam"] * zi[4])
            ch["lam_meas"] = lm
            if r.lam_banks is not None:
                ch["lam_banks"] = (lm, lm)
        r1 = replace(r, **ch)
        new.append(r1)
        xs.append(epa_stats.row_inputs(r1, fuel=epa_stats.fuel_of(r1, view=view, conventions=epa_stats.NOMINAL),
                                       conventions=epa_stats.NOMINAL, model=model))
    res = _map(_cycle_job, [(model._engine_for(x.fuel), x, dtheta) for x in xs], jobs)
    out = []
    geo = tp.engine.geometry
    for r1, x, o, zi in zip(new, xs, res, z):
        extra = 0.0
        if truth.out_of_form:
            extra = truth.out_of_form["tit_k_per_100kpa_above_100"] * (r1.map_kpa / 100.0 - 1.0)
        torque = float(o.torque_nm * (1.0 + T0_NOISE["torque_rel"] * zi[0]))
        meter = None if r1.fuel_meter_gps is None else float(o.mdot_fuel_gps * (1.0 + T0_NOISE["meter_rel"] * zi[1]))
        bmep = float(torque * 4.0 * np.pi / geo.vd_total / 1e5)
        cells = {"intake_manifold_press_kpa_abs": repr(float(r1.map_kpa)), "bmep_bar": repr(bmep),
                 "fuel_meter_flow_gps": "" if meter is None else repr(meter),
                 "exhaust_lambda": "" if r1.lam_meas is None else repr(float(r1.lam_meas))}
        pops = epa_rows.populations(cells, r1.lam_ref, float(view.hot_map_floor_kpa),
                                     "final" if _final(r1) else "steady")
        out.append(replace(r1, origin="t0", torque_nm=torque, bmep_bar=bmep, fuel_meter_gps=meter,
                           meter_missing=meter is None, injector_fuel_gps=float(o.mdot_fuel_gps),
                           tit_c=float(o.egt_c + T0_NOISE["tit_k"] * zi[2] + extra),
                           tip_kpa=float(plant_model.exhaust_backpressure_kpa(r1.map_kpa, engine=tp.engine)),
                           pops=pops))
    return tuple(out)


def _chi2_of(fit, truth):
    """Two-sided chi^2 of (estimate - truth) over S2's and S4's data-dominated
    parameters against each stage's covariance scaled by its residual variance
    (amendment D11), the stages taken as independent blocks, with each parameter's
    standardised error."""
    d2, dof, z, params = 0.0, 0, {}, []
    for stage in ("S2", "S4"):
        rep = fit.stages[stage].report
        if rep.get("covariance") is None:
            continue
        names = list(rep["params"])
        pick = [i for i, n in enumerate(names) if rep["data_or_prior"][n] == "data-dominated"
                and n in truth.values["cycle"]]
        if not pick:
            continue
        C = np.array(rep["covariance"], dtype=float)[np.ix_(pick, pick)]
        d = np.array([fit.values["cycle"][names[i]] - truth.values["cycle"][names[i]] for i in pick])
        d2 += float(d @ np.linalg.solve(C, d))
        dof += len(pick)
        for k, i in enumerate(pick):
            z[names[i]] = float(d[k] / math.sqrt(C[k, k]))
            params.append(names[i])
    # a chi-square over no parameter tests nothing: its quantiles are NaN and it is neither within nor beyond
    # its interval, so it is marked empty and fails every reading of it (t0_judge; WP3's second fix of 23
    # October 2026, on the test review's finding that the out-of-form seed's empty chi-square read "detected")
    empty = dof < 1
    lo, hi = (None, None) if empty else (float(chi2.ppf(0.005, dof)), float(chi2.ppf(0.995, dof)))
    valid = not empty and math.isfinite(lo) and math.isfinite(hi) and math.isfinite(d2)
    return {"params": params, "value": d2, "dof": dof, "quantile_99_lo": lo, "quantile_99_hi": hi,
            "empty": not valid, "ok": bool(valid and lo <= d2 <= hi)}, z


# T0's STOP RULE IS PLAN.md 5.10's, RESTORED (WP3's second fix of 23 October 2026, on the fit review's
# must-fix): "the B-truth seed's ladder stops at A+B; the A-truth seeds stop at A". Amendment D11 changed the
# chi-square and added the out-of-form seed and the D1-D3 cases, and kept that criterion; the first fix's
# relaxed rule (the ladder had only to REACH the truth's form, every in-sample statistic within R + z u_stat
# there) was this module's own change, which no amendment or decision authorised, and under it T0 passed a
# form-A truth frozen at A+B+C+D and a ladder that never stopped. So an in-form seed passes only when its
# ladder CHOSE the truth's form and the chi-square there is within its 99 %. within_noise (|E_c| <= R + z
# u_stat_c, z the standard normal quantile of the chi-square's 99 %) and stopped_beyond_expected_form are
# reported beside the verdict as diagnostics, never in it. The fit review measured the real ladder on
# test_epa_fit's synthetic rows at dtheta 0.25: a form-A truth's in-sample E4b at T0_NOISE fails |E| <= R on
# sampling error and climbs the ladder to A+B+C+D, so this rule can fail on synthetic data. That was a
# question about the contract's in-sample gate for the team before Run 1, not one this code could absorb by
# relaxing T0, and the team answered it in the ladder's criterion, never in T0's: decision 77 (23 October
# 2026, before any fit, on synthetic data only) counts an in-sample statistic against a form only when
# |E_cal| - 2 u_stat > R (epa_stats.in_sample_outcome), so the ladder T0 runs is the fit's own and T0's stop
# rule here is unchanged: the ladder must still CHOOSE the truth's form.
T0_STOP_Z = float(norm.ppf(0.995))
# What follows a T0 failure the investigation traces to sampling rather than a coding defect, declared before
# Run 1 (WP3's second fix of 23 October 2026, on the fit review's finding that no outcome was declared): T0's
# noise stream and seeds are fixed (T0_STREAM, seeds 1-4) and are never changed after a result, which would be
# seed shopping. Such a failure stops Run 1 for the engine; the team decides what follows and records it in
# the engine's defects.json, and any further seeds are T0_STREAM's next ones in order (5, 6, ...), named here
# before any T0 has run.
T0_ON_SAMPLING_FAILURE = ("a T0 failure traced to sampling rather than a defect stops Run 1 for the engine: the seeds "
                          "and the stream are never changed after a result; the team decides, recorded in defects.json, "
                          "and any further seeds are T0_STREAM's next ones in order (5, 6, ...)")
# D1's T0 case (WP3's fix): the lines without holds' rows moved -- MAP up by T0_D1_MAP_MOVE_KPA and the meter
# doubled -- must leave the envelope bit for bit; moved, not deleted, since a deletion would move decision
# 53's median cell pressure, a property of every calibration row, and with it every point's corrected flow.
T0_D1_MAP_MOVE_KPA = 50.0
# The ceiling read back at each envelope point (plant.boost_ceiling_kpa) against inlet x the point's PR,
# relative: the round trip through corrected_flow's arithmetic (DESIGN: well above rounding, far below any
# point's spacing).
T0_D1_CEILING_REL = 1e-9
# S1's T0 case: the fitted law within this many hinge-grid steps (S1_GRID_KPA) of the noise-free truth's, times
# the fitted ratio, DESIGN: one step is the profile's own resolution, two leave room for a tie between
# neighbouring hinges.
T0_S1_GRID_STEPS = 2.0
# T0's cases (t0_cases), in t0.json's order.
T0_CASES = ("d1_envelope", "d2_gate", "d3_spark_min", "s1_law")
# DECISION 84 (Ghassan, 29 October 2026; results/VALIDATION_DECISIONS.md section H): T0's d2_gate case is widened
# to the data's resolution. The gate is identified only to the gap between neighbouring calibration Final rows
# (S3b enriches a row when its MAP exceeds the gate, so every gate between two neighbouring Final MAPs gives the
# Final rows the same schedule), so the case passes when the truth's gate lies within the fitted flat interval
# widened to the MAPs of the neighbouring calibration Final rows: down to the highest Final MAP at or below the
# interval's lower end (the highest Final row the fitted gates leave unenriched) and up to the lowest Final MAP
# above its upper end (the lowest one they enrich), as well as within the grid's 1 kPa of the interval, as before
# (amendment D2's case: the interval only ever widens). A side with no such Final row is not widened. For all
# three engines; a test fix, logged as one (the defect route records it, defects.json). It was written after
# Run 1's first T0 failed this case on the Honda's seed 1 (truth 123.43 kPa, flat interval [125, 125]), and
# T0 re-runs on every engine on the final code. Read as written, it does not reach below the lowest calibration
# Final row: a truth placed below that row and a fit that leaves the row unenriched are a row apart and still fail
# -- the Honda's seed 1 of the first pass among them (t0_truths places the truth between the highest steady MAP
# below the lowest Final MAP and that Final MAP, which the first pass put in (123.43, 124.86) kPa, below seed 1's
# interval [125, 125]); a wording that reaches down to that steady MAP is the team's to choose.
D2_GATE_RULE = ("decision 84: the truth's gate within the fitted flat interval widened to the MAPs of the "
                "neighbouring calibration Final rows (the highest at or below the interval, the lowest above it), "
                "or within the gate grid's step of the interval (amendment D2)")


def d2_gate_case(flat_gates_kpa, truth_gate_kpa, final_maps_kpa, *, fitted_gate_kpa, step_kpa):
    """T0's d2_gate case (amendment D2, decision 84 above): {"ok", "detail"}. `flat_gates_kpa` is S3b's flat
    interval [lo, hi] on its grid, `final_maps_kpa` the MAPs of the calibration Final rows (the seed's T0 rows,
    which keep the calibration rows' MAPs), `step_kpa` the grid's step. ok when lo - step < truth <= hi + step (the
    grid's resolution, as before) or when below <= truth <= above, below the highest Final MAP at or below lo
    (lo itself when none) and above the lowest Final MAP above hi (hi itself when none)."""
    lo, hi = (float(x) for x in flat_gates_kpa)
    g, step = float(truth_gate_kpa), float(step_kpa)
    maps = sorted(float(m) for m in final_maps_kpa)
    below = [m for m in maps if m <= lo]
    above = [m for m in maps if m > hi]
    w_lo = below[-1] if below else lo
    w_hi = above[0] if above else hi
    in_grid = bool(lo - step < g <= hi + step)
    in_gap = bool(w_lo <= g <= w_hi)
    return {"ok": bool(in_grid or in_gap),
            "detail": {"truth_gate_kpa": g, "fitted_gate_kpa": fitted_gate_kpa, "flat_gates_kpa": [lo, hi],
                       "widened_kpa": [w_lo, w_hi],
                       "neighbour_final_map_kpa": {"below": below[-1] if below else None,
                                                   "above": above[0] if above else None},
                       "within_grid_step": in_grid, "within_final_gap": in_gap, "final_rows": len(maps),
                       "rule": D2_GATE_RULE}}


def t0_cases(name, fit, truth, *, rows, view):
    """Amendments D1-D3's T0 cases on the fit a seed is judged at (WP3's fix of 23 October 2026: each now a
    check that can fail, on the fit review's finding that two could not):

      d1_envelope   the T0 rows of the lines without holds moved (T0_D1_MAP_MOVE_KPA, the meter x2): S3c
                    on them gives the fitted envelope bit for bit, so no such line reaches the ceiling; and
                    the fitted candidate's plant.boost_ceiling_kpa at each point's corrected flow is inlet x
                    the point's PR within T0_D1_CEILING_REL, so the in-use ceiling passes through every hold
                    it was fitted to;
      d2_gate       the truth's gate lies on the fitted gate's flat interval, to the grid's 1 kPa, or, since
                    decision 84 (29 October 2026), within that interval widened to the MAPs of the
                    neighbouring calibration Final rows (d2_gate_case);
      d3_spark_min  BaselineECU.step of the fitted ECU at every T0 row S3a used returns base + comp - cold
                    unclipped, re-run here independently of S3a's own assertion;
      s1_law        the fitted back-pressure law equals the noise-free truth's at every row S1 used, to the
                    hinge grid's resolution (T0_S1_GRID_STEPS).
    S3a's plane and S3b's depth and breakpoints are not recovered against a covariance here (their stages
    report none); D2's gate case and D3's spark case are their checks (declared, 23 October 2026)."""
    c = fit.stages["S3c"].report
    no = set(c["lines_without_holds"])
    cand = candidate(name, fit.values)
    base = _base_plant(name, fit.form)
    moved = tuple(replace(r, map_kpa=float(r.map_kpa + T0_D1_MAP_MOVE_KPA),
                          fuel_meter_gps=None if r.fuel_meter_gps is None else float(2.0 * r.fuel_meter_gps))
                  if r.line in no else r for r in cal_rows(rows))
    try:
        again = s3c_envelope(moved, plant=base, view=view, conventions=epa_stats.NOMINAL).values
        same = all(_bits_list(again[k]) == _bits_list(fit.values["boost_ceiling"][k])
                   for k in ("envelope_flow", "envelope_pr", "pr_cap"))
    except (ValueError, FitDefect):
        same = False                     # an envelope the moved rows break is one they reached
    inlet = float(cand.engine.boost.inlet_sea_kpa)
    worst = 0.0
    for p in c["points"]:
        mdot = float(p["corrected_flow"]) * (inlet / plant_model.P_REF_CORR) * 1e3
        ceil = plant_model.boost_ceiling_kpa(mdot, plant_model.T_REF_CORR, inlet, engine=cand.engine)
        worst = max(worst, abs(ceil / (inlet * float(p["pr"])) - 1.0))
    d1 = {"ok": bool(same and worst <= T0_D1_CEILING_REL),
          "detail": {"lines_without_holds": sorted(no), "point_lines": [p["line"] for p in c["points"]],
                     "envelope_unmoved_by_the_lines_without_holds": same, "ceiling_at_points_max_rel": worst}}
    b = fit.stages["S3b"].report
    # decision 84: widened to the MAPs of the neighbouring calibration Final rows (d2_gate_case)
    d2 = d2_gate_case(b["flat_gates_kpa"], truth.values["ecu"]["enr_load"],
                      [r.map_kpa for r in cal_rows(rows) if _final(r)],
                      fitted_gate_kpa=fit.values["ecu"]["enr_load"], step_kpa=S3B_GATE_STEP_KPA)
    ecu_cal = cand.engine.ecu
    used = [r for r in cal_rows(rows) if r.pops.fired and _no_sentinel(r) and _finite(r.spark_btdc)]
    clipped = 0
    for r in used:
        e2 = engine_env.BaselineECU(ecu_cal)
        plane = ecu_cal.spark_a + ecu_cal.spark_b * r.speed_rpm - ecu_cal.spark_c * (r.map_kpa - ecu_cal.spark_ref_kpa)
        raw = (min(plane, e2.knock_limited_spark(r.speed_rpm, r.map_kpa)) + e2.iat_compensation(r.imt_k)
               - (ecu_cal.cold_retard if r.ect_k < ecu_cal.cold_k else 0.0))
        out = e2.step(r.speed_rpm, r.map_kpa, r.imt_k, r.ect_k, False, S3B_DWELL_S)[0]
        if not (ecu_cal.spark_min < raw < ecu_cal.spark_max and out == raw):
            clipped += 1
    d3 = {"ok": bool(used) and clipped == 0,
          "detail": {"rows": len(used), "rows_clipped": clipped, "spark_min": fit.values["ecu"]["spark_min"],
                     "spark_max": fit.values["ecu"]["spark_max"]}}
    # S1's recovery (WP3's fix of 23 October 2026, on the fit review's finding that T0 judged S2 and S4
    # alone): T0's turbine-inlet pressure carries no noise, so the fitted law equals the truth's at every T0
    # row S1 used to within the hinge grid's resolution, T0_S1_GRID_STEPS steps of S1_GRID_KPA times the
    # fitted ratio (a hinge one step off moves the law by at most that)
    tcand = candidate(name, truth.values)
    s1_rows = [r for r in cal_rows(rows) if r.pops.fired and _finite(r.tip_kpa) and _no_sentinel(r)]
    s1_err = max((abs(plant_model.exhaust_backpressure_kpa(r.map_kpa, engine=cand.engine)
                      - plant_model.exhaust_backpressure_kpa(r.map_kpa, engine=tcand.engine)) for r in s1_rows),
                 default=None)
    edge = T0_S1_GRID_STEPS * S1_GRID_KPA * float(fit.values["cycle"]["exh_bp_ratio"])
    s1 = {"ok": s1_err is not None and s1_err <= edge,
          "detail": {"rows": len(s1_rows), "max_abs_law_kpa": s1_err, "edge_kpa": edge,
                     "fitted": {k: fit.values["cycle"][k] for k in ("exh_bp_ratio", "exh_bp_min_kpa")},
                     "truth": {k: truth.values["cycle"][k] for k in ("exh_bp_ratio", "exh_bp_min_kpa")}}}
    return {"d1_envelope": d1, "d2_gate": d2, "d3_spark_min": d3, "s1_law": s1}


def _bits_list(x):
    return tuple(_bits(float(v)) for v in (x if isinstance(x, (list, tuple)) else [x]))


def t0_judge(ladders, truths, *, rows, view):
    """T0's verdict (PLAN.md 5.10 as amendment D11 changes it; the stop rule above): for each in-form seed,
    the ladder CHOSE the truth's form (an A truth stops at A, the A+B truth at A+B) and the two-sided chi^2 of
    that form's data-dominated parameters lies within its 99 % interval; within_noise and
    stopped_beyond_expected_form are reported beside it. The out-of-form seed must FAIL a chi^2 that tests
    something at the form its ladder chose (the control: a T0 that cannot fail is no test, D11). A chi^2
    over no parameter (no covariance, or no data-dominated parameter the truth carries) is empty, on any
    seed: it fails an in-form seed, it is never a detection, and T0 does not pass while any seed has one
    (chi2_empty_seeds; WP3's second fix of 23 October 2026). D1-D3's cases hold on every in-form seed at its
    judged fit (t0_cases). `ladders`, `truths` and `rows` (each seed's T0 rows) are paired in order."""
    seeds, oof, cases_all, empty = [], None, [], []
    for lad, tr, rr in zip(ladders, truths, rows):
        fits = {f.form: f for f in lad.fits}
        if tr.out_of_form:
            fit = fits[lad.chosen]
            c2, z = _chi2_of(fit, tr)
            if c2["empty"]:
                empty.append(tr.seed)
            oof = {"seed": tr.seed, "truth": tr.values["cycle"], "ladder_stops_at": lad.chosen, "judged_at": lad.chosen,
                   "expected_form": None, "chi2": c2, "z": z}
            continue
        form = tr.expected_form
        reached = form in fits and form in (lad.in_sample or {})
        fit = fits[form] if reached else fits[lad.chosen]
        c2, z = _chi2_of(fit, tr)
        if c2["empty"]:
            empty.append(tr.seed)
        noise = epa_stats.within_noise(lad.in_sample[form], z=T0_STOP_Z) if reached else None
        rec = {"seed": tr.seed, "truth": tr.values["cycle"], "ladder_stops_at": lad.chosen,
               "expected_form": form, "judged_at": fit.form, "reached_expected_form": bool(reached),
               "stopped_at_expected_form": bool(lad.chosen == form),
               "stopped_beyond_expected_form": bool(reached and lad.chosen != form),
               "within_noise": noise, "chi2": c2, "z": z,
               "ok": bool(lad.chosen == form and not c2["empty"] and c2["ok"])}
        seeds.append(rec)
        cases_all.append(t0_cases(lad.engine, fit, tr, rows=rr, view=view))
    cases = {k: {"ok": all(c[k]["ok"] for c in cases_all), "detail": [c[k]["detail"] for c in cases_all]}
             for k in T0_CASES} if cases_all else {}
    detected = oof is not None and not oof["chi2"]["empty"] and not oof["chi2"]["ok"]
    ok = bool(seeds and all(s["ok"] for s in seeds) and detected and not empty
              and all(c["ok"] for c in cases.values()))
    return _py({"seeds": seeds, "out_of_form_seed": oof, "out_of_form_detected": detected, "chi2_empty_seeds": empty,
                "cases": cases,
                "stop_rule": {"z": T0_STOP_Z, "rule": "PLAN.md 5.10: each in-form seed's ladder stops at its truth's "
                              "form (an A truth at A, the A+B truth at A+B) and the chi^2 of that form's data-dominated "
                              "parameters lies within its 99 %; within_noise (every in-sample statistic but E8 within "
                              "R + z u_stat) and stopped_beyond_expected_form are diagnostics beside the verdict; the "
                              "out-of-form seed fails a chi^2 that tests something; an empty chi^2 on any seed fails T0",
                              "on_sampling_failure": T0_ON_SAMPLING_FAILURE,
                              # the criterion the ladder T0 runs stopped by (decision 77), the fit's own
                              "ladder_criterion": epa_stats.IN_SAMPLE_CRITERION},
                "pass": ok})


def t0_ladders(name, yield_, *, view, jobs, dtheta):
    """T0's fits (PLAN.md 5.10: "run the whole fitting procedure over 3 seeds", and
    amendment D11's out-of-form seed): for each truth of t0_truths, its synthetic rows
    (t0_rows) and the engine's whole per-engine ladder on them, the same `ladder` the
    fit runs, its in-sample stage included. Returns (truths, ladders, rows), paired. Run
    once, before Run 1, by calibrate_epa.py t0 on committed code (amendment A1): it
    evaluates at the calibration rows' inputs, and nothing in WP3 runs it on them."""
    truths = t0_truths(name, view=view, yield_=yield_)
    rows = tuple(t0_rows(yield_, truth=tr, seed=tr.seed, view=view, dtheta=dtheta, jobs=jobs) for tr in truths)
    ladders = tuple(ladder(name, rr, view=view, jobs=jobs, dtheta=dtheta) for rr in rows)
    return truths, ladders, rows


def run_t0(name, yield_, *, view, jobs, dtheta):
    """T0, whole: t0_ladders, then t0_judge -- t0.json's body without its provenance
    (WP3_INTERFACES.md 7.2: seeds, out_of_form_seed, cases, stop_rule, pass), with each
    seed's ladder (the forms fitted, the form chosen, the reason, and each form's
    in-sample record by decision 77, form_record) beside it."""
    truths, ladders, rows = t0_ladders(name, yield_, view=view, jobs=jobs, dtheta=dtheta)
    out = t0_judge(ladders, truths, rows=rows, view=view)
    out["ladders"] = {str(tr.seed): {"forms_fitted": [f.form for f in lad.fits], "chosen": lad.chosen,
                                     "reason": lad.reason,
                                     "in_sample": {f: form_record(lad.in_sample[f]) for f in lad.in_sample}}
                      for tr, lad in zip(truths, ladders)}
    out["schema"] = "epa-t0/1"
    return out
