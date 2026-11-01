"""test_epa_tightenings.py -- row 104's tightenings (epa_tightenings.py), outside STEP2_TESTS.

    python -B test_epa_tightenings.py        a few minutes (two real locked-climb tasks); exit code 0 when all pass

Nothing here draws a road of the test, writes in the tree, opens an EPA table, a held-out record, logs/ or any
.csv: epa_roads' audit hook is installed below, every class but RealInputs, SyntheticRecord, TimingPath,
AuditGuard, RealGates, StoppedRoute and LiveRecord is test_epa_fixtures.Guarded (WP3_INTERFACES.md 9.1), and
those read the real contract, the pinned K3 files and results/car_spark_boost.json (RealGates and StoppedRoute
copy them into a temporary repository), never a table. Each check has its control (mistake 12).

  Policy           S2a's predictive policy at H against a road with one known climb: the largest grade over steps
                   k+1 .. k+int(H) by hand, the first step it acts, p_predictive's levers, the preview off
  SlopeRule        the slope rule, the re-score and the pair against hand-worked numbers; a tie; a run the
                   re-score does not give back is refused
  E8Path           E8 goes through k3_knee only: shifted_ecu, k3 and with_knee, each road run under its own
                   shift at its own K3 knee, the L1 runs unshifted at the B58's knee; ecu_shift.one and run_all
                   never called; results/ENGINE_THRESHOLDS/ecu/ untouched; the tables are
                   thresholds.contract.response's; a zero nominal pair and a grid off the contract's refused;
                   the locked-climb tasks run before every road run; each shift records whether reactive acted;
                   the real run's knee checks refuse as their tasks end, before any road run
  Band             row 107 (4)'s u_val and kappa by hand: untested (the floor and the formula), missing u_val; a
                   line that would certify still reads untested (no u_stat); a flat first segment; off has no
                   kappa; the model-minus-car reading beside it
  RealInputs       on the real contract: the locked-climb-only band gives row 107 (4)'s arithmetic back (E 25.9 %,
                   u_val 15.6 %, kappa 3.44), and the model-minus-car reading beside it; the fifteen runs are
                   ecu_shift's k3 runs; the spark inputs reproduce (row 107 (4)'s condition, and every field); the
                   pinned knees are read and the folder is left
  KneeReal         the real tasks: ecu_shift's above0 is k3_nominal.json's, the K3 knee of spark -0.75 deg is
                   k3_spark-0.75.json's bit for bit and keeps its seconds, and a real road run's re-score gives its
                   damage back
  SyntheticRecord  the record a SYNTHETIC run writes (the plant runs stood in for) passes
                   validate_epa.load_tightenings and tightening_problems on the real contract; spoiled variants are
                   refused; it names its roads record's sha_text and seed
  TimingPath       `timing` on one SYNTHETIC road of the design, the plant runs stood in for: its record, once,
                   with the real run's counts and prediction
  Isolation        the import closure of the 35 files roads.json hashes holds no epa_tightenings (row 121 (2)), with
                   a control; this module imports the roads module; code_sha_text covers the closure
  Audit            the guard refuses an EPA table, logs/epa and results/EPA_VALIDATION; a run opens none, writes
                   nothing under the pinned folder and calls no epa_rows reader
  Gates            the roads record's refusals; the out path's; the writer leaves nothing on a refusal; the real
                   run refuses before anything when a gate fails, refuses in this tree while roads.json is absent,
                   and refuses a Python that writes bytecode; the no-roads route refuses in this tree while no stop
                   is committed
  RealGates        every gate of real_problems in a synthetic git repository with a REAL-kind roads.json (a test
                   commit and reveal), the control first: uncommitted code, compiled files, uncommitted data inputs,
                   the roads step's outputs, the attempts log, the seed and the reveal, another plant; run_real
                   (compute stood in) writes once, and the committed record passes committed_record_problems while
                   each spoiled copy, a SYNTHETIC one among them, is refused
  StoppedRoute     row 129 (4) in a synthetic git repository built as RealGates builds one, after a real
                   epa_roads.draw() stop (Jad's integer withheld, entered as 2**128; the plant work stood in for as
                   test_epa_roads.Reveal stands it in): the draw logged a stop that is not a coding defect and refuses
                   a later attempt; the control (stopped_problems [], run_stopped writes once, then refuses, and what
                   it wrote is the contract's, read here); one refusal per gate, each from the control and back to it,
                   the re-check before the write among them; the log read as draw writes it (the logged reveals
                   checked again, ints of at least 2**128, the stop right after its own start); the shared branch
                   (the stop pushed, HEAD the tip; a fork at the roads commit beside a drawn set refused); the
                   committed, pushed record passes validate_epa._arm_tightenings, tightening_problems,
                   stopped_record_problems, test_epa_roads' check and LiveRecord's, each spoiled copy is refused, and
                   so is the record once a roads.json stands beside it or the shared branch holds one; the held-out R
                   is the contract's 9.9 K and P the contract's, each with a control that moves it
  LiveRecord       once results/EPA_TIGHTENINGS.json exists: with roads.json, the committed record is the real run's;
                   without it, row 129 (4)'s no-roads record (epa_tightenings.stopped_record_problems); no other
"""
import contextlib
import copy
import dataclasses
import io
import json
import math
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import check_premise as CP  # noqa: E402
import engine_env as E  # noqa: E402
import epa_freeze  # noqa: E402
import epa_roads as R  # noqa: E402
import epa_stats as ES  # noqa: E402
import epa_tightenings as T  # noqa: E402
import evaluate as V  # noqa: E402
import k3_knee as K  # noqa: E402
import roads_ceiling as RC  # noqa: E402
import validate_epa as VE  # noqa: E402
import test_epa_fixtures as fx  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)
from thresholds import common  # noqa: E402
from thresholds import contract as TC  # noqa: E402
from thresholds import ecu_shift as ECU  # noqa: E402

R.install_guard(())
SYNTHETIC_SEED = 314159265          # SYNTHETIC: a test seed, never roads_seed
TAU_B58_S = 47.335                  # row 102's B58 tau (MEASURED by the probe, `python c5tau.py`), for test roads
QUIET = (lambda msg: None)          # noqa: E731

# Every open while ON is set (path, mode): the Audit class reads it.
OPEN_LOG = {"on": False, "seen": []}


def _record_open(event, args):
    if event == "open" and OPEN_LOG["on"] and args and isinstance(args[0], (str, bytes, os.PathLike)):
        OPEN_LOG["seen"].append((os.fsdecode(args[0]), args[1] if len(args) > 1 else None))


sys.addaudithook(_record_open)


def tiny_road(*, k, lead_s, climbs, duration_s):
    """A road of row 101's shape from explicit climbs (roads_ceiling.family_road), paired with EPISODES[k]."""
    seed, w = V.EPISODES[k]
    return RC.family_road(k=k, episode_seed=seed, weights=w, lead_s=lead_s, climbs=climbs, v_kmh=130.0,
                          duration_s=duration_s, dt=1.0, t_amb_k=315.0, slot_start=0, label="SYNTHETIC test road")


def tiny_record(n_roads=1):
    roads = [tiny_road(k=i, lead_s=40.0, climbs=[(30.0, 0.11, 40.0)], duration_s=120.0) for i in range(n_roads)]
    return T.synthetic_roads_record(SYNTHETIC_SEED, n_roads=n_roads, roads=roads, tau_s=TAU_B58_S, jobs=1)


SMALL_GRID = {"source": "synthetic", "k3_pair_change_vs_lambda": [[-0.02, -0.1], [0.0, 0.0], [0.02, -0.2]],
              "k3_pair_change_vs_spark": [[-0.75, 0.05], [0.0, 0.0], [0.75, -0.05]]}
SPARK = {"ends_deg": [-3.81, -1.78], "u_deg": 2.07}


# ------------------------------------------------------------------ the stand-ins for the plant runs
class Stand:
    """Stand-ins for k3_knee.baseline_trace and roads_ceiling.run_episode_record, and a spy on k3_knee's three
    functions: each records what it was given and the shift in force (the stack of shifted_ecu blocks). The
    road runs return per-step arrays whose damage is the plant's own damage_rate, so the re-score check holds;
    the housing depends on the policy and on the shift, so every pair is nonzero."""

    BASES = {CP.p_neutral: 1140.0, CP.p_reactive: 1128.0, CP.p_grade_now: 1118.0}

    def __init__(self, bases=None):
        self.shift = []
        self.calls = {"shifted_ecu": [], "k3": [], "with_knee": [], "trace": [], "run": []}
        self.seq = []                                   # the order of the k3 and road calls
        self.bases = {**self.BASES, **(bases or {})}
        self.real = {"shifted_ecu": K.shifted_ecu, "k3": K.k3, "with_knee": K.with_knee}

    @contextlib.contextmanager
    def shifted_ecu(self, ds, dl):
        self.calls["shifted_ecu"].append((ds, dl))
        with self.real["shifted_ecu"](ds, dl):
            self.shift.append((ds, dl))
            try:
                yield
            finally:
                self.shift.pop()

    def k3(self, plant, *, seconds, provisional):
        patched = E.BaselineECU.step is not K._ECU_STEP
        self.calls["k3"].append({"seconds": seconds, "provisional": tuple(provisional), "patched": patched,
                                 "shift": self.shift[-1] if self.shift else None})
        self.seq.append("k3")
        return self.real["k3"](plant, seconds=seconds, provisional=provisional)

    def with_knee(self, plant, knee_k):
        self.calls["with_knee"].append(knee_k)
        return self.real["with_knee"](plant, knee_k)

    def trace(self, plant):
        ds, dl = self.shift[-1] if self.shift else (0.0, 0.0)
        self.calls["trace"].append(((ds, dl), plant.engine.damage.turb_knee_k))
        t = 1000.0 + 150.0 * np.sin(np.arange(719) / 40.0) + 20.0 * ds - 400.0 * dl
        return K.BaselineTrace(t, np.ones(719), np.zeros(719))

    def run(self, plant, cycle, policy, *, seed, weights, dt, egt_ambient_windows, detail):
        shift = self.shift[-1] if self.shift else None
        self.calls["run"].append({"shift": shift, "patched": E.BaselineECU.step is not K._ECU_STEP,
                                  "knee": plant.engine.damage.turb_knee_k, "policy": policy, "seed": seed,
                                  "weights": tuple(weights), "detail": detail})
        self.seq.append("run")
        n = len(cycle["t"]) - 1
        if isinstance(policy, T.HorizonPredictive):
            base = 1115.0 - policy.h_s / 10.0
        else:
            base = self.bases[policy]
        ds, dl = shift or (0.0, 0.0)
        tt = base + 30.0 * np.sin(np.arange(n) / 9.0) + 4.0 * ds - 150.0 * dl
        to = np.full(n, 390.0)
        ki = np.where(np.arange(n) % 7 == 0, 0.95, 0.0)
        cal = plant.engine.damage
        dk = sum(E.damage_rate(a, b, c, cal=cal) for a, b, c in zip(tt, to, ki)) * dt
        dn = sum(E.damage_rate(a, b, cal=cal) for a, b in zip(tt, to)) * dt
        return {"D_knock": dk, "D_noknock": dn, "steps": n, "ret": 0.0, "peak_turb_k": float(tt.max()),
                "t_turb": tt, "t_oil": to, "ki": ki}

    @contextlib.contextmanager
    def installed(self, *, real_runs=False):
        with contextlib.ExitStack() as st:
            st.enter_context(mock.patch.object(K, "shifted_ecu", self.shifted_ecu))
            st.enter_context(mock.patch.object(K, "k3", self.k3))
            st.enter_context(mock.patch.object(K, "with_knee", self.with_knee))
            st.enter_context(mock.patch.object(K, "baseline_trace", self.trace))
            if not real_runs:
                st.enter_context(mock.patch.object(RC, "run_episode_record", self.run))
            st.enter_context(mock.patch.object(ECU, "one", side_effect=AssertionError("ecu_shift.one was called")))
            st.enter_context(mock.patch.object(ECU, "run_all", side_effect=AssertionError("ecu_shift.run_all called")))
            yield self


def stood_in_compute(record, *, strategy, seconds=None, pinned=None, pinned_strict=False, st=None):
    st = st or Stand()
    with st.installed():
        out = T.compute(record, roads_ref="SYNTHETIC test roads", strategy=strategy, r_e8_pct=16.6, spark=SPARK,
                        pinned=pinned, seconds=seconds, jobs=1, log=QUIET, pinned_strict=pinned_strict)
    return out, st


def stand_trace_k(ds, dl):
    """The Stand's locked-climb housing under a shift (Stand.trace)."""
    return 1000.0 + 150.0 * np.sin(np.arange(719) / 40.0) + 20.0 * ds - 400.0 * dl


def hand_D(T_k, O_k, ki, *, cal, shift):
    """engine_env.damage_rate's published form, written out by hand, at the knee shifted by `shift`:
    (with the knock term, without it)."""
    tot_n = tot_k = 0.0
    for a, b, c in zip(T_k, O_k, ki):
        d = math.exp((a - cal.turb_knee_k - shift) / cal.turb_scale_k) + cal.oil_weight * math.exp(
            (b - cal.oil_knee_k) / cal.oil_scale_k)
        tot_n += d
        tot_k += d + cal.ki_weight * max(0.0, c - cal.ki_knee) ** 2
    return tot_k, tot_n


def hand_runs(n_roads):
    """Four constant-housing L1 runs per road; each policy's housing differs by road."""
    n = 50
    runs = {}
    temps = {"neutral": 1140.0, "cg": 1125.0, "pred@0.5": 1121.0, "pred@1.5": 1112.0}
    cal = T._b58().engine.damage
    for i in range(n_roads):
        for p, t0 in temps.items():
            tt = np.full(n, t0 + 3.0 * i)
            tt[: 10 + 5 * i] = 1000.0                   # a cool lead-in, so the knee shift is not a factor
            to = np.full(n, 395.0 + i)
            ki = np.zeros(n)
            ki[::5] = 0.9 + 0.05 * i
            dk, dn = hand_D(tt, to, ki, cal=cal, shift=0.0)
            runs[(i, p)] = {"t_turb": tt, "t_oil": to, "ki": ki, "D_knock": dk, "D_noknock": dn,
                            "peak_turb_k": float(tt.max())}
    return runs, cal


# =====================================================================================================
class Policy(Guarded):
    """S2a's predictive policy at H (MD:1500-1502) on a road with one climb: onset 60 s, L 45 s, 11 %."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = T._b58()
        cls.road = tiny_road(k=0, lead_s=60.0, climbs=[(45.0, 0.11, 60.0)], duration_s=200.0)
        cls.grade = list(cls.road["cycle"]["grade"])

    def env(self, use_preview=True):
        e = E.SupervisoryTunerEnv(RC.env_cycle(self.road, dt=1.0), plant=self.plant, dt=1.0, seed=1000,
                                  use_preview=use_preview)
        e.reset(seed=1000)
        return e

    def test_the_window_is_steps_k1_to_k_int_H(self):
        env = self.env()
        n = len(self.grade)
        for H in (23.6675, 71.0025, 1.0):
            m = int(H)
            for k in range(n):
                env.k = k
                hi = min(k + m, n - 1)
                want = max(self.grade[k + 1:hi + 1]) if hi >= k + 1 else 0.0
                self.assertEqual(T.largest_grade_ahead(env, H), want, (H, k))

    def test_it_acts_int_H_steps_before_the_ramp_passes_2_percent(self):
        """By hand: the ramp from 60 s reads 0.11/8 = 1.375 % at 61 s and 2.75 % at 62 s, so the policy (housing
        cold) first protects when step 62 enters the window, at k = 62 - int(H): 39 at H 23.67 s, and from the
        start at H 71.00 s (62 - 71 < 0). Control: current-grade first acts at k = 62 itself."""
        self.assertEqual((self.grade[61], self.grade[62]), (0.11 / 8.0, 0.11 * 2.0 / 8.0))
        for H, first in ((23.6675, 39), (71.0025, 0)):
            env = self.env()
            pol = T.HorizonPredictive(H)
            acts = []
            for k in range(0, 80):
                env.k = k
                self.assertLess(env.thermal.t_turb, self.plant.engine.damage.turb_knee_k)
                acts.append(not np.array_equal(pol(env, None), CP.NEUTRAL))
            self.assertEqual(acts.index(True), first, H)
        env = self.env()
        cg = []
        for k in range(0, 80):
            env.k = k
            cg.append(not np.array_equal(CP.p_grade_now(env, None), CP.NEUTRAL))
        self.assertEqual(cg.index(True), 62)

    def test_it_is_p_predictives_levers(self):
        env = self.env()
        pol = T.HorizonPredictive(23.6675)
        for k in (30, 39, 41, 45, 50, 70, 100, 150, 190):
            env.k = k
            ahead = T.largest_grade_ahead(env, 23.6675)
            k_ahead = float(np.clip(ahead / 0.08, 0.0, 1.0)) if ahead > 0.02 else 0.0
            want = CP._protect(max(0.0, 0.55 * k_ahead))
            np.testing.assert_array_equal(pol(env, None), want)
        # the housing above the knee: p_predictive's own k_now, read through the view
        env.k = 0
        env.thermal.t_turb = self.plant.engine.damage.turb_knee_k + 12.5
        np.testing.assert_array_equal(pol(env, None), CP._protect(0.5))

    def test_the_preview_off_reads_nothing(self):
        env = self.env(use_preview=False)
        pol = T.HorizonPredictive(71.0025)
        for k in range(0, 120, 5):
            env.k = k
            self.assertEqual(T.largest_grade_ahead(env, 71.0025), 0.0)
            np.testing.assert_array_equal(pol(env, None), CP.NEUTRAL)

    def test_H_is_a_positive_python_float(self):
        for bad in (23, 0.0, -1.0, np.float64(23.0)):
            with self.assertRaises(ValueError):
                T.HorizonPredictive(bad)
        self.assertIsInstance(T.policy_of(("pred", 23.6675)), T.HorizonPredictive)
        self.assertIs(T.policy_of(("cg",)), CP.p_grade_now)


# =====================================================================================================
class SlopeRule(Guarded):
    hand_D = staticmethod(hand_D)

    def test_the_rescore_is_the_published_form(self):
        cal = T._b58().engine.damage
        run = {"t_turb": np.array([1100.0, 1133.0, 1160.0, 1090.0]), "t_oil": np.array([395.0, 400.0, 410.0, 380.0]),
               "ki": np.array([0.0, 0.9, 1.2, 0.5])}
        for s in T.SHIFTS_K:
            k, n = self.hand_D(run["t_turb"], run["t_oil"], run["ki"], cal=cal, shift=s)
            self.assertAlmostEqual(T.rescored(run, cal=cal, shift_k=s, reading="knock", dt=1.0) / k, 1.0, places=12)
            self.assertAlmostEqual(T.rescored(run, cal=cal, shift_k=s, reading="noknock", dt=1.0) / n, 1.0, places=12)
        self.assertEqual(T.SHIFTS_K, (-57.0, -25.0, -10.0, -5.0, 0.0, 5.0, 10.0, 25.0, 57.0))   # knee_shift.py:22

    def test_the_pair_is_evaluate_pys_cut_difference(self):
        """evaluate.py:533-538 written out: cut = 100 (1 - median D / median D_base); pair = cut_var - cut_ref."""
        ref, var, base = [10.0, 30.0, 20.0], [8.0, 25.0, 50.0], [40.0, 41.0, 39.0]
        cut = lambda D: 100.0 * (1.0 - np.median(D) / np.median(base))      # noqa: E731
        self.assertAlmostEqual(T.evaluate_pair(ref, var, base), cut(var) - cut(ref), places=12)
        self.assertAlmostEqual(T.evaluate_pair(ref, var, base), 100.0 * (20.0 - 25.0) / 40.0, places=12)

    def test_the_slope_rule_by_hand(self):
        shifts = T.SHIFTS_K
        pairs = {h: {rd: {s: 2.0 + 0.01 * s for s in shifts} for rd in T.READINGS} for h in ("0.5", "1.5")}
        pairs["1.5"]["noknock"][-5.0] = 2.0 + 1.0           # |3.0 - 2.0| / 5 = 0.2, the largest by hand
        pairs["0.5"]["knock"][57.0] = 2.0 + 5.7             # 5.7 / 57 = 0.1
        every, best = T.slope_rule(pairs, shifts=shifts)
        self.assertEqual(len(every), 2 * 2 * 8)
        self.assertEqual((best["H"], best["reading"], best["shift_k"]), ("1.5", "noknock", -5.0))
        self.assertAlmostEqual(best["slope_points_per_K"], 0.2, places=12)
        others = [x["slope_points_per_K"] for x in every if x is not best]
        self.assertTrue(all(abs(v - 0.01) < 1e-12 or abs(v - 0.1) < 1e-12 for v in others))
        # a tie goes to the first in the order H, reading, shift
        pairs["0.5"]["knock"][57.0] = 2.0 + 0.2 * 57.0
        _, best = T.slope_rule(pairs, shifts=shifts)
        self.assertEqual((best["H"], best["reading"], best["shift_k"]), ("0.5", "knock", 57.0))

    def runs_by_hand(self, n_roads):
        return hand_runs(n_roads)

    def test_l1_block_by_hand(self):
        runs, cal = self.runs_by_hand(3)
        roads = [{"dt": 1.0}] * 3
        H = {"0.5": 23.6675, "1.5": 71.0025}
        l1 = T.l1_block(runs, roads, H=H, roads_ref="hand")
        for h in H:
            for rd in T.READINGS:
                ix = 0 if rd == "knock" else 1
                for s in T.SHIFTS_K:
                    D = {p: [self.hand_D(runs[(i, p)]["t_turb"], runs[(i, p)]["t_oil"], runs[(i, p)]["ki"], cal=cal,
                                         shift=s)[ix] for i in range(3)] for p in ("neutral", "cg", f"pred@{h}")}
                    want = 100.0 * (np.median(D["cg"]) - np.median(D[f"pred@{h}"])) / np.median(D["neutral"])
                    self.assertAlmostEqual(l1["pairs_points"][h][rd][f"{s:+g}"], want, places=9)
        slopes = [abs(l1["pairs_points"][h][rd][f"{s:+g}"] - l1["pairs_points"][h][rd]["+0"]) / abs(s)
                  for h in H for rd in T.READINGS for s in T.SHIFTS_K if s]
        self.assertAlmostEqual(l1["slope_points_per_K"], max(slopes), places=12)
        self.assertIn(l1["damage_reading"], T.READING_TEXT.values())
        self.assertIn(f"H {H[l1['H']]:.2f} s", l1["set"])
        self.assertLess(l1["rescore_worst_relative"], 1e-12)

    def test_a_run_the_rescore_does_not_give_back_is_refused(self):
        runs, _ = self.runs_by_hand(2)
        runs[(1, "cg")]["D_knock"] *= 1.0 + 1e-4
        with self.assertRaises(T.TighteningsDefect):
            T.l1_block(runs, [{"dt": 1.0}] * 2, H={"0.5": 23.6675, "1.5": 71.0025}, roads_ref="hand")


# =====================================================================================================
class E8Path(Guarded):
    """E8 through k3_knee only (row 104), the plant runs stood in for so that the path itself is seen."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.state0 = T.ecu_folder_state()
        cls.rec = tiny_record(2)
        OPEN_LOG["seen"] = []
        OPEN_LOG["on"] = True
        try:
            (cls.l1, cls.e8, cls.timing, cls.opened), cls.st = stood_in_compute(cls.rec, strategy=SMALL_GRID)
        finally:
            OPEN_LOG["on"] = False
        cls.opens = list(OPEN_LOG["seen"])

    def test_ecu_shift_is_never_called_and_its_folder_is_left(self):
        # the Stand patches one and run_all to raise: the compute above would have stopped
        self.assertEqual(T.ecu_folder_state(), self.state0)
        ecu_dir = os.path.normcase(os.path.abspath(common.ECU_DIR))
        writes = [p for p, m in self.opens if os.path.normcase(os.path.abspath(p)).startswith(ecu_dir)
                  and isinstance(m, str) and any(c in m for c in "wax+")]
        self.assertEqual(writes, [])

    def test_each_shift_has_its_k3_knee_under_its_own_shift(self):
        c = self.st.calls
        nonzero = [(0.0, -0.02), (0.0, 0.02), (-0.75, 0.0), (0.75, 0.0)]
        k3s = c["k3"]
        self.assertEqual(sorted(x["shift"] for x in k3s), sorted(nonzero))
        self.assertTrue(all(x["patched"] for x in k3s))
        # seconds: the unshifted stand-in trace's seconds above the B58's knee (ecu_shift.one's above0)
        k0 = T._b58().engine.damage.turb_knee_k
        tr0 = self.st.trace(T._b58())                      # the unshifted trace, by the same stand-in
        above0 = int((tr0.t_turb_k > k0).sum())
        self.assertTrue(all(x["seconds"] == above0 for x in k3s))
        self.assertEqual(self.e8["time_above_nominal_s"], above0)
        self.assertTrue(all(x["provisional"] == (k0, k0 + T.PROVISIONAL_STEP_K) for x in k3s))
        # each K3 knee is knee_for(the shifted trace, above0), and the runs of that shift used it
        for (ds, dl) in nonzero:
            name = T._name_of(ds, dl)
            want = K.knee_for(1000.0 + 150.0 * np.sin(np.arange(719) / 40.0) + 20.0 * ds - 400.0 * dl, above0)
            self.assertEqual(self.e8["shifts"][name]["knee_k"], want)
            runs = [r for r in c["run"] if r["shift"] == (ds, dl)]
            self.assertEqual(len(runs), 2 * 3)                               # two roads, three policies
            self.assertTrue(all(r["patched"] and r["knee"] == want for r in runs))
            self.assertIn(want, c["with_knee"])

    def test_the_nominal_and_l1_runs(self):
        c = self.st.calls
        k0 = T._b58().engine.damage.turb_knee_k
        nominal = [r for r in c["run"] if r["shift"] == (0.0, 0.0)]
        self.assertEqual(len(nominal), 2 * 3)
        self.assertTrue(all(r["patched"] and r["knee"] == k0 for r in nominal))   # ecu_shift's patch(0, 0)
        l1 = [r for r in c["run"] if r["shift"] is None]
        self.assertEqual(len(l1), 2 * 4)                                      # neutral, cg, two horizons
        self.assertTrue(all(not r["patched"] and r["knee"] == k0 and r["detail"] == "full" for r in l1))
        hs = sorted(r["policy"].h_s for r in l1 if isinstance(r["policy"], T.HorizonPredictive))
        self.assertEqual(hs, sorted([0.5 * TAU_B58_S, 1.5 * TAU_B58_S] * 2))
        # road k with EPISODES[k]'s seed and weights (row 101)
        for r in c["run"]:
            k = [s for s, _ in V.EPISODES].index(r["seed"])
            self.assertEqual(r["weights"], tuple(V.EPISODES[k][1]))

    def test_the_tables_are_contract_response(self):
        table = {n: dict(dlambda=v["dlambda"], dspark=v["dspark"], **v["medians"]) for n, v in self.e8["shifts"].items()}
        for lever in ("lambda", "spark"):
            want = [[float(a), float(b)] for a, b in TC.response(table, lever)]
            self.assertEqual(self.e8[T.ROADS_KEYS[lever]], want)
            self.assertEqual([a for a, _ in want], [float(a) for a, _ in SMALL_GRID[T.GRID_KEYS[lever]]])
        # by hand, one shift: the larger |change| of the two readings, its sign kept
        nom, sh = self.e8["shifts"]["nominal"], self.e8["shifts"]["lam+0.02"]
        ch = [sh["pair_points"][rd] / nom["pair_points"][rd] - 1.0 for rd in T.READINGS]
        got = dict((a, b) for a, b in self.e8[T.ROADS_KEYS["lambda"]])[0.02]
        self.assertAlmostEqual(got, max(ch, key=abs), places=12)

    def test_a_zero_nominal_pair_and_an_off_grid_are_refused(self):
        rec = tiny_record(1)
        st = Stand()
        orig = st.run

        def flat(plant, cycle, policy, **kw):
            out = orig(plant, cycle, policy, **kw)
            if st.shift and policy in (CP.p_reactive, CP.p_grade_now):
                out = dict(out, D_knock=1.0, D_noknock=1.0)
            return out
        st.run = flat
        with st.installed(), self.assertRaises(T.Refused):
            T.compute(rec, roads_ref="x", strategy=SMALL_GRID, r_e8_pct=16.6, spark=SPARK, pinned=None, seconds=413,
                      jobs=1, log=QUIET)
        with mock.patch.object(TC, "response", lambda table, var: [(0.0, 0.0)]):
            st = Stand()
            with st.installed(), self.assertRaises(T.TighteningsDefect):
                T.compute(rec, roads_ref="x", strategy=SMALL_GRID, r_e8_pct=16.6, spark=SPARK, pinned=None,
                          seconds=413, jobs=1, log=QUIET)

    def test_a_second_knee_that_moves_the_trace_is_a_defect(self):
        st = Stand()
        real_k3 = st.k3

        def moved(plant, *, seconds, provisional):
            return dataclasses.replace(real_k3(plant, seconds=seconds, provisional=provisional),
                                       second_knee_identical=False)
        st.k3 = moved
        with st.installed(), self.assertRaises(T.TighteningsDefect):
            T.compute(tiny_record(1), roads_ref="x", strategy=SMALL_GRID, r_e8_pct=16.6, spark=SPARK, pinned=None,
                      seconds=413, jobs=1, log=QUIET)

    def test_the_locked_climb_tasks_run_first_and_each_knee_records_its_seconds(self):
        """The queue puts above0 and the k3 tasks before every road run (URGENT); each shift's record keeps
        the seconds its knee was set at (k3_knee.K3.seconds, above0), not the task's wall time (task_s)."""
        seq = self.st.seq
        self.assertEqual(seq.count("k3"), 4)
        self.assertLess(max(i for i, s in enumerate(seq) if s == "k3"), seq.index("run"))
        above0 = self.e8["time_above_nominal_s"]
        for name, v in self.e8["shifts"].items():
            self.assertEqual(v["k3_seconds"], None if name == "nominal" else above0, name)
        self.assertEqual(self.timing["tasks"], {"road": 2 * (4 + 3 * 5), "k3": 4, "above0": 1})

    def test_each_shift_records_whether_reactive_ever_acted(self):
        """reactive_identical_to_neutral_roads counts the roads on which reactive's damage equals neutral's bit for
        bit; neutral_peak_minus_knee_k is the neutral run's peak housing minus the shift's knee. By hand on the
        Stand's housing; the control is a Stand whose reactive policy runs neutral's housing."""
        n_steps = 119                                                          # a 120 s road, 119 steps
        for name, v in self.e8["shifts"].items():
            self.assertEqual(v["reactive_identical_to_neutral_roads"], {"knock": 0, "noknock": 0}, name)
            peak = 1140.0 + 30.0 * np.sin(np.arange(n_steps) / 9.0).max() + 4.0 * v["dspark"] - 150.0 * v["dlambda"]
            for got in v["neutral_peak_minus_knee_k"]:
                self.assertAlmostEqual(got, peak - v["knee_k"], places=9)
        self.assertEqual(self.e8["reactive_identical_to_neutral"]["roads"], {"knock": 0, "noknock": 0})
        self.assertEqual(self.e8["reactive_identical_to_neutral"]["of"], 2 * 5)
        st = Stand(bases={CP.p_reactive: Stand.BASES[CP.p_neutral]})
        (_, e8, _, _), _ = stood_in_compute(tiny_record(2), strategy=SMALL_GRID, seconds=413, st=st)
        self.assertEqual(e8["reactive_identical_to_neutral"]["roads"], {"knock": 10, "noknock": 10})
        self.assertTrue(all(v["reactive_identical_to_neutral_roads"] == {"knock": 2, "noknock": 2}
                            for v in e8["shifts"].values()))

    def strict_pinned(self):
        """The pinned record the Stand's own knees would give: above0 and every knee by hand."""
        k0 = T._b58().engine.damage.turb_knee_k
        above0 = int((stand_trace_k(0.0, 0.0) > k0).sum())
        knees = {T._name_of(ds, dl): K.knee_for(stand_trace_k(ds, dl), above0)
                 for ds, dl in [(0.0, -0.02), (0.0, 0.02), (-0.75, 0.0), (0.75, 0.0)]}
        knees["nominal"] = k0
        return {"knees": knees, "time_above_nominal_s": above0, "folder": None}

    def test_the_real_runs_knee_checks_refuse_before_any_road_run(self):
        """pinned_strict (run_real): an above0 that is not the pinned one stops the run when above0 ends, before
        any k3 task or road run; a K3 knee that is not the pinned one stops it when its task ends, and the k3
        tasks run before every road run, so no road run has started. The control: the pinned values the Stand
        gives pass."""
        good = self.strict_pinned()
        (_, e8, _, _), st = stood_in_compute(tiny_record(1), strategy=SMALL_GRID, pinned=good, pinned_strict=True)
        self.assertTrue(e8["knees_equal_pinned"])
        self.assertEqual(len(st.calls["run"]), 4 + 3 * 5)                      # the control ran everything
        bad = dict(good, time_above_nominal_s=good["time_above_nominal_s"] + 1)
        st = Stand()
        with self.assertRaises(T.TighteningsDefect) as cm:
            stood_in_compute(tiny_record(1), strategy=SMALL_GRID, pinned=bad, pinned_strict=True, st=st)
        self.assertIn("k3_nominal.json", str(cm.exception))
        self.assertEqual((st.calls["k3"], st.calls["run"]), ([], []))
        bad = dict(good, knees=dict(good["knees"], **{"spark+0.75": good["knees"]["spark+0.75"] + 1e-9}))
        st = Stand()
        with self.assertRaises(T.TighteningsDefect) as cm:
            stood_in_compute(tiny_record(1), strategy=SMALL_GRID, pinned=bad, pinned_strict=True, st=st)
        self.assertIn("k3_spark+0.75.json", str(cm.exception))
        self.assertEqual((len(st.calls["k3"]), st.calls["run"]), (4, []))
        with self.assertRaises(ValueError):                                     # strict needs above0 measured
            stood_in_compute(tiny_record(1), strategy=SMALL_GRID, pinned=good, pinned_strict=True, seconds=413)

    def test_the_fifteen_names_are_ecu_shifts(self):
        names = [n for n, _, _ in T.e8_shifts(SMALL_GRID)]
        self.assertEqual(names, ["nominal", "lam-0.02", "lam+0.02", "spark-0.75", "spark+0.75"])
        with self.assertRaises(T.Refused):
            T.e8_shifts({"k3_pair_change_vs_lambda": [[-0.02, 0.0], [0.02, 0.0]],
                         "k3_pair_change_vs_spark": [[0.0, 0.0], [0.75, 0.0]]})


# =====================================================================================================
class Band(Guarded):
    """Row 107 (4) by hand on synthetic tables (P as fractions, R in %)."""
    LOCKED = [(-3.0, 0.20), (-1.5, 0.08), (0.0, 0.0), (0.75, -0.06)]
    ROADS = [[-3.0, 0.25], [-1.5, 0.05], [0.0, 0.0], [0.75, -0.07]]

    def strategy(self):
        return {"k3_pair_change_vs_lambda": [[-0.02, -0.1], [0.0, 0.0]],
                "k3_pair_change_vs_spark": [list(p) for p in self.LOCKED]}

    def test_untested_with_the_roads_by_hand(self):
        b = T.b58_band({T.ROADS_KEYS["lambda"]: [[-0.02, -0.05], [0.0, 0.0]], T.ROADS_KEYS["spark"]: self.ROADS},
                       strategy=self.strategy(), r_pct=16.6, spark=SPARK)
        w = b["with_roads"]
        # P: the larger |.| at each shift, its sign kept: (-3, 0.25), (-1.5, 0.08), (0, 0), (0.75, -0.07)
        self.assertEqual(w["P_spark"], [[-3.0, 0.25], [-1.5, 0.08], [0.0, 0.0], [0.75, -0.07]])
        slope = (0.25 - 0.08) / 1.5                                   # the first segment, extrapolated below
        E_ = 100.0 * (0.25 + slope * 0.81)                            # at -3.81 deg
        u = 100.0 * 2.07 * slope
        self.assertAlmostEqual(w["E_pct"], E_, places=9)
        self.assertEqual(w["E_from_ds_deg"], -3.81)
        self.assertTrue(w["ends"][0]["extrapolated"] and not w["ends"][1]["extrapolated"])
        self.assertAlmostEqual(w["u_val_pct"], u, places=9)
        self.assertEqual(w["label"], "untested")                     # 2u > R, |E| - 2u < R
        self.assertAlmostEqual(w["kappa"], max(1.0 + E_ / 16.6, (E_ + 2.0 * u) / 16.6), places=9)
        self.assertFalse(w["floor_binds"])
        # beside it, the locked climb alone: 0.20 + (0.12 / 1.5) 0.81
        lo = b["locked_climb_only"]
        self.assertAlmostEqual(lo["E_pct"], 100.0 * (0.20 + 0.12 / 1.5 * 0.81), places=9)

    def test_missing_u_takes_the_floor(self):
        b = T.b58_band({T.ROADS_KEYS["lambda"]: [[-0.02, 0.0], [0.0, 0.0]], T.ROADS_KEYS["spark"]: self.ROADS},
                       strategy=self.strategy(), r_pct=16.6, spark={"ends_deg": [-3.81, -1.78], "u_deg": None})
        w = b["with_roads"]
        self.assertIsNone(w["u_val_pct"])
        self.assertEqual(w["label"], "untested")
        self.assertAlmostEqual(w["kappa"], 1.0 + w["E_pct"] / 16.6, places=12)

    def test_a_line_that_would_certify_still_reads_untested(self):
        """No row defines a u_stat for the B58's reading, so the line is labelled with u_stat None and certifies
        nothing (epa_stats.line_label): the row reads untested where the line reads validated or limited, and
        kappa is max(1 + |E|/R, (|E| + 2u_val)/R) (row 107 (3); row 107 (4): untested on the B58)."""
        small = [[-3.0, 0.02], [-1.5, 0.01], [0.0, 0.0], [0.75, -0.005]]
        strat = {"k3_pair_change_vs_lambda": [[0.0, 0.0], [0.02, 0.0]], "k3_pair_change_vs_spark": small}
        tabs = {T.ROADS_KEYS["lambda"]: [[0.0, 0.0], [0.02, 0.0]], T.ROADS_KEYS["spark"]: small}
        v = T.b58_band(tabs, strategy=strat, r_pct=16.6, spark={"ends_deg": [-1.78], "u_deg": 2.07})["with_roads"]
        # E = 100 (0.01 + 0.01/1.5 0.28) = 1.19 %, u = 100 2.07 (0.01/1.5) = 1.38 %: |E| + 2u <= R
        self.assertEqual((v["line_label"], v["certifies"], v["label"]), ("validated", False, "untested"))
        self.assertIsNone(v["u_stat_pct"])
        self.assertAlmostEqual(v["kappa"], max(1.0 + v["E_pct"] / 16.6, (v["E_pct"] + 2.0 * v["u_val_pct"]) / 16.6),
                               places=12)
        self.assertTrue(v["floor_binds"])
        lim = T.b58_band(tabs, strategy=strat, r_pct=3.5, spark={"ends_deg": [-1.78], "u_deg": 2.07})["with_roads"]
        self.assertEqual((lim["line_label"], lim["label"]), ("limited", "untested"))   # 2u 2.76 <= 3.5 < |E| + 2u
        self.assertAlmostEqual(lim["kappa"], 1.0 + lim["E_pct"] / 3.5, places=12)      # the floor binds
        # the control, epa_stats itself: with u_stat = u_val the same line certifies, the case this closes
        lab, cert = ES.line_label(lim["E_pct"], lim["u_val_pct"], lim["u_val_pct"], 3.5)
        self.assertEqual((lab, cert), ("limited", True))

    def test_a_flat_first_segment_does_not_lower_kappa_below_the_floor(self):
        """The review's case: P_spark's -1.5 deg point raised to 0.14 makes the first segment flat, 2u_val <= R.
        By hand: slope (0.197 - 0.14)/1.5 per deg, E = 100 (0.197 + slope 0.81), u = 100 2.07 slope; untested,
        kappa = 1 + E/R (the floor), not the formula's (E + 2u)/R."""
        ps = [(-3.0, 0.197), (-1.5, 0.14), (0.0, 0.0), (0.75, -0.06)]
        b = T._band_of(ps, r_pct=16.6, ends=[-3.81, -1.78], u_deg=2.07)
        slope = (0.197 - 0.14) / 1.5
        E_, u = 100.0 * (0.197 + slope * 0.81), 100.0 * 2.07 * slope
        self.assertAlmostEqual(b["E_pct"], E_, places=9)
        self.assertAlmostEqual(b["u_val_pct"], u, places=9)
        self.assertLessEqual(2.0 * u, 16.6)
        self.assertEqual((b["line_label"], b["label"]), ("limited", "untested"))
        self.assertAlmostEqual(b["kappa"], 1.0 + E_ / 16.6, places=12)
        self.assertGreater(b["kappa"], (E_ + 2.0 * u) / 16.6)
        self.assertTrue(b["floor_binds"])

    def test_an_off_line_has_no_kappa(self):
        """|E| - 2u_val > R: the row reads off, which row 107 (4) does not expect and row 107 (3) gives no kappa:
        kappa is None, with the note for the team. Control: the untested table beside it has a kappa."""
        ps = [(-3.0, 0.30), (-1.5, 0.29), (0.0, 0.0), (0.75, -0.06)]
        b = T._band_of(ps, r_pct=16.6, ends=[-3.81, -1.78], u_deg=2.07)
        self.assertGreater(b["E_pct"] - 2.0 * b["u_val_pct"], 16.6)
        self.assertEqual(b["label"], "off")
        self.assertIsNone(b["kappa"])
        self.assertTrue(b["kappa_undefined"])
        self.assertEqual(b["note"], T.OFF_NOTE)
        self.assertEqual(T._kappa_text(b), "undefined (off: the team's call, row 107 (3))")
        ok = T._band_of([(a, float(c)) for a, c in self.LOCKED], r_pct=16.6, ends=[-3.81, -1.78], u_deg=2.07)
        self.assertEqual(ok["label"], "untested")
        self.assertIsNotNone(ok["kappa"])

    def test_the_model_minus_car_reading_is_beside_it(self):
        """S2's sign: the same band at the ends' opposite sign, labelled descriptive; the primary is row 107 (4)'s."""
        b = T.b58_band({T.ROADS_KEYS["lambda"]: [[-0.02, -0.05], [0.0, 0.0]], T.ROADS_KEYS["spark"]: self.ROADS},
                       strategy=self.strategy(), r_pct=16.6, spark=SPARK)
        m = b["model_minus_car"]
        self.assertIn("descriptive", m["reading"])
        self.assertEqual([x["ds_deg"] for x in m["with_roads"]["ends"]], [3.81, 1.78])
        want = T._band_of([tuple(p) for p in b["with_roads"]["P_spark"]], r_pct=16.6, ends=[3.81, 1.78], u_deg=2.07)
        self.assertEqual(m["with_roads"], want)
        self.assertEqual([x["ds_deg"] for x in b["with_roads"]["ends"]], [-3.81, -1.78])


# =====================================================================================================
class RealInputs(unittest.TestCase):
    """The real contract, the pinned K3 files and results/car_spark_boost.json (read, never written; no table).
    Not Guarded: the fixture's guard refuses the real contract, which these checks are about."""

    @classmethod
    def setUpClass(cls):
        cls.ci = T.contract_inputs()

    def test_the_locked_climb_gives_row_107_4s_arithmetic_back(self):
        """Row 107 (4): slope 7.53 % per degree between -3.0 and -1.5 deg, u_val 15.6 %, 2u_val 31.2 % > R,
        untested, kappa = max(1 + 25.9/16.6, (25.9 + 31.2)/16.6) = max(2.56, 3.44) = 3.44 (arithmetic, not a run)."""
        strat = self.ci["ecu_strategy_b58"]
        self.assertEqual(self.ci["r_e8_pct"], 16.6)
        ps = [(float(a), float(b)) for a, b in strat["k3_pair_change_vs_spark"]]
        b = T._band_of(ps, r_pct=self.ci["r_e8_pct"], ends=[-3.81, -1.78], u_deg=2.07)
        self.assertEqual(round(abs(b["ends"][0]["slope_per_deg"]) * 100.0, 2), 7.56)   # 7.53 from the MD's rounded table
        self.assertEqual((round(b["E_pct"], 1), round(b["u_val_pct"], 1), b["label"]), (25.9, 15.6, "untested"))
        self.assertEqual(round(b["ends"][1]["P"] * 100.0, 1), 10.5)              # the other end, MD:376-378
        self.assertEqual(round(b["kappa"], 2), 3.44)
        self.assertEqual(round(1.0 + b["E_pct"] / 16.6, 2), 2.56)

    def test_the_model_minus_car_reading_on_the_locked_climb(self):
        """The descriptive reading at E8's statistic's sign (model minus car, +3.81 / +1.78 deg) on the contract's
        locked-climb table: E 23.53 %, u_val 11.98 %, untested, kappa 2.861 (MEASURED by this test; the review's
        sign probe of 31 October printed the same), against row 107 (4)'s 25.86 %, 15.65 % and 3.443."""
        strat = self.ci["ecu_strategy_b58"]
        b = T.b58_band({T.ROADS_KEYS[x]: [list(p) for p in strat[T.GRID_KEYS[x]]] for x in T.ROADS_KEYS},
                       strategy=strat, r_pct=self.ci["r_e8_pct"], spark=SPARK)
        lo, m = b["locked_climb_only"], b["model_minus_car"]["locked_climb_only"]
        self.assertEqual((round(lo["E_pct"], 2), round(lo["u_val_pct"], 2), lo["label"], round(lo["kappa"], 3)),
                         (25.86, 15.65, "untested", 3.443))
        self.assertEqual((round(m["E_pct"], 2), round(m["u_val_pct"], 2), m["label"], round(m["kappa"], 3)),
                         (23.53, 11.98, "untested", 2.861))
        self.assertEqual(b["with_roads"], lo)               # the roads tables equal to the locked climb's: P is the same

    def test_the_fifteen_runs_are_ecu_shifts_k3_runs(self):
        got = T.e8_shifts(self.ci["ecu_strategy_b58"])
        want = [(n, ds, dl) for mode, n, ds, dl in ECU.RUNS if mode == "k3"]
        self.assertEqual(len(got), 15)
        self.assertEqual(sorted(got), sorted(want))
        self.assertEqual(got[0], ("nominal", 0.0, 0.0))

    def test_the_spark_inputs_reproduce(self):
        """Row 107 (4)'s condition is the 31 readings' standard error: the "all" cell's readings and diff_se.
        Today every field of both cells comes back too. Controls: a moved reading changes the standard error, and
        u is then missing; a printed field outside that condition (the climb cell's quartile) is recorded as not
        reproduced and leaves u; a printed standard error that is not the readings' makes u missing."""
        s = T.spark_inputs(root=HERE)
        self.assertTrue(s["reproduced"])
        self.assertTrue(s["reproduced_cells_all_fields"])
        self.assertEqual((s["ends_deg"], s["u_deg"]), ([-3.81, -1.78], 2.07))
        self.assertEqual(s["reproduced_cells"], s["printed_cells"])
        import car_spark_boost as CSB
        self.assertIsNotNone(CSB.CLIMB)
        fresh = lambda: common.load_json(os.path.join(HERE, T.SPARK_RECORD_REL))      # noqa: E731

        def with_record(rec):
            with mock.patch.object(common, "load_json", lambda p: rec):
                return T.spark_inputs(root=HERE)
        rec = fresh()
        rec["readings"][0]["spark"] += 3.0
        bad = with_record(rec)
        self.assertNotEqual(bad["reproduced_cells"][T.SPARK_CELL_ALL]["diff_se"], 2.07)
        self.assertEqual((bad["reproduced"], bad["u_deg"]), (False, None))
        rec = fresh()
        rec["cells"][T.SPARK_CELL_CLIMB]["diff_q1"] += 1.0
        part = with_record(rec)
        self.assertEqual((part["reproduced"], part["reproduced_cells_all_fields"], part["u_deg"]), (True, False, 2.07))
        rec = fresh()
        rec["cells"][T.SPARK_CELL_ALL]["diff_se"] = 2.08
        se = with_record(rec)
        self.assertEqual((se["reproduced"], se["u_deg"]), (False, None))

    def test_the_pinned_knees_are_read_and_the_folder_left(self):
        before = T.ecu_folder_state()
        p = T.pinned_k3(root=HERE)
        self.assertEqual(len(p["knees"]), 15)
        self.assertEqual(p["time_above_nominal_s"], 413)
        self.assertEqual(p["knees"]["nominal"], 1123.0)
        self.assertEqual(T.ecu_folder_state(), before)
        self.assertEqual(p["folder"], before)


# =====================================================================================================
class KneeReal(Guarded):
    """The real tasks, no stand-in: ecu_shift's above0 on the B58's locked climb, one K3 knee, one road run."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        with open(ECU.path("k3", "spark-0.75"), encoding="utf-8") as fh:
            cls.pinned = json.load(fh)
        with open(ECU.path("k3", "nominal"), encoding="utf-8") as fh:
            cls.nominal = json.load(fh)
        cls.above0 = T._task({"kind": "above0"})
        cls.k3 = T._task({"kind": "k3", "ds": -0.75, "dl": 0.0, "seconds": cls.above0["time_above_nominal_s"]})

    def test_above0_is_k3_nominals(self):
        self.assertEqual(self.above0["time_above_nominal_s"], self.nominal["time_above_nominal_s"])
        self.assertEqual(self.above0["steps"], 719)

    def test_the_k3_knee_is_ecu_shifts_bit_for_bit(self):
        self.assertEqual(self.k3["knee_k"], self.pinned["knee_k"])
        self.assertTrue(self.k3["second_knee_identical"])
        self.assertEqual(self.k3["time_above_knee_s"], self.pinned["time_above_knee_s"])
        self.assertIs(E.BaselineECU.step, K._ECU_STEP)                       # the patch was restored
        # the K3 record's own seconds is the above0 it was set at, the task's wall time beside it (task_s)
        self.assertEqual(self.k3["seconds"], self.above0["time_above_nominal_s"])
        self.assertGreater(self.k3["task_s"], 1.0)

    def test_a_real_road_run_is_given_back_by_the_rescore(self):
        road = tiny_road(k=3, lead_s=30.0, climbs=[(25.0, 0.12, 30.0)], duration_s=80.0)
        k0 = T._b58().engine.damage.turb_knee_k
        res = {}
        for p in ("neutral", "cg"):
            res[(0, p)] = T._task(T.road_task(road, policy=(p,), knee_k=k0, ds=0.0, dl=0.0, shifted=False,
                                              per_step=True))
        for h in ("0.5", "1.5"):
            H = (0.5 if h == "0.5" else 1.5) * TAU_B58_S
            res[(0, f"pred@{h}")] = T._task(T.road_task(road, policy=("pred", H), knee_k=k0, ds=0.0, dl=0.0,
                                                        shifted=False, per_step=True))
        self.assertTrue(all(v["steps"] == 79 for v in res.values()))         # 80 samples, 79 steps (row 122 (2))
        l1 = T.l1_block(res, [road], H={"0.5": 0.5 * TAU_B58_S, "1.5": 1.5 * TAU_B58_S}, roads_ref="real")
        self.assertLess(l1["rescore_worst_relative"], T.RESCORE_TOL)
        # the same run through evaluate's own episode loop gives the same damage (the scoring's control)
        seed, w = V.EPISODES[3]
        env = E.SupervisoryTunerEnv(RC.env_cycle(road, dt=1.0), plant=T._b58(), dt=1.0, seed=seed)
        obs, _ = env.reset(seed=seed)
        env.w = np.asarray(w, dtype=np.float32)
        obs = env._obs()
        while True:
            obs, _, term, trunc, info = env.step(CP.p_grade_now(env, obs))
            if term or trunc:
                break
        self.assertEqual(info["episode_summary"]["damage"], res[(0, "cg")]["D_knock"])


# =====================================================================================================
class SyntheticRecord(unittest.TestCase):
    """The record a SYNTHETIC run writes, the plant runs stood in for (Stand), on the real contract's grid:
    validate_epa.load_tightenings takes it and tightening_problems finds nothing; spoiled copies are refused.
    Not Guarded: run_synthetic reads the real contract (no table; epa_roads' guard is installed)."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="epa_tightenings_test_")
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)
        cls.roads_path = os.path.join(cls.tmp, "roads_SYNTHETIC.json")
        R.write_once(cls.roads_path, tiny_record(1))
        cls.st = Stand()
        OPEN_LOG["seen"] = []
        OPEN_LOG["on"] = True
        try:
            with cls.st.installed():
                cls.sha, cls.rec, cls.path = T.run_synthetic(synthetic_seed=SYNTHETIC_SEED, n_roads=1, out_dir=cls.tmp,
                                                             roads_record=cls.roads_path, jobs=1, log=QUIET)
        finally:
            OPEN_LOG["on"] = False
        cls.opens = list(OPEN_LOG["seen"])
        cls.contract = T.contract_inputs()

    def check(self, raw):
        p = os.path.join(self.tmp, "spoiled.json")
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(raw, fh)
        try:
            t = VE.load_tightenings(p)
        except ValueError as exc:
            return [str(exc)]
        finally:
            os.remove(p)
        return VE.tightening_problems(t, {"ecu_strategy_b58": self.contract["ecu_strategy_b58"]},
                                      b58=VE.b58_identity())

    def test_validate_epa_takes_it(self):
        t = VE.load_tightenings(self.path)
        self.assertEqual(t.sha_text, self.sha)
        self.assertEqual(VE.tightening_problems(t, {"ecu_strategy_b58": self.contract["ecu_strategy_b58"]},
                                                b58=VE.b58_identity()), [])
        self.assertEqual((t.plant, t.roads_sha, t.roads_seed), ("b58", R.roads_sha(self.roads_path), SYNTHETIC_SEED))
        self.assertEqual(t.raw["provenance"]["plant_sha"], VE.b58_identity()["plant_sha"])
        self.assertEqual(t.raw["seed_kind"], "SYNTHETIC")
        self.assertEqual(len(t.e8_lambda_roads), 10)
        self.assertEqual(len(t.e8_spark_roads), 6)
        self.assertGreater(t.l1_slope_points_per_k, 0.0)
        # what epa_stats reads at the held-out run: the combined P on the contract's grid
        view = types.SimpleNamespace(ecu_strategy_b58=self.contract["ecu_strategy_b58"])
        pl, ps = ES.e8_response(view, tightening=t.raw)
        self.assertEqual([a for a, _ in pl], [a for a, _ in t.e8_lambda_roads])
        self.assertIn("b58_u_val_kappa", t.raw["E8"])
        self.assertEqual(sorted(t.raw["provenance"]["code_sha_text"]), T.code_files(root=HERE))

    def test_spoiled_copies_are_refused(self):
        good = common.load_json(self.path)
        self.assertEqual(self.check(good), [])                               # the control
        edits = {
            "no schema": lambda d: d.pop("schema"),
            "another schema": lambda d: d.update(schema="epa-tightenings/0"),
            "another plant": lambda d: d.update(plant="mazda_25t"),
            "a float seed": lambda d: d.update(roads_seed=float(d["roads_seed"])),
            "no L1 slope": lambda d: d["L1"].pop("slope_points_per_K"),
            "a negative slope": lambda d: d["L1"].update(slope_points_per_K=-0.1),
            "a zero slope": lambda d: d["L1"].update(slope_points_per_K=0.0),
            "a text slope": lambda d: d["L1"].update(slope_points_per_K="0.1"),
            "no set": lambda d: d["L1"].pop("set"),
            "an E8 table off the grid": lambda d: d["E8"][T.ROADS_KEYS["lambda"]][0].__setitem__(0, -0.2),
            "an E8 table of one pair": lambda d: d["E8"].update({T.ROADS_KEYS["spark"]: [[0.0, 0.0]]}),
            "another engine_sha": lambda d: d["provenance"].update(engine_sha="0" * 16),
            "another plant_sha": lambda d: d["provenance"].update(plant_sha="0" * 16),
            "no commit": lambda d: d["provenance"].pop("commit"),
            "no code_sha_text": lambda d: d["provenance"].pop("code_sha_text"),
        }
        for what, edit in edits.items():
            bad = copy.deepcopy(good)
            edit(bad)
            self.assertNotEqual(self.check(bad), [], what)

    def test_it_was_written_outside_the_tree_and_opened_no_table(self):
        self.assertTrue(T.outside_work_trees(self.path))
        self.assertFalse(os.path.exists(self.path + ".partial"))
        bad = [p for p, _ in self.opens if R.refused_path(p)]
        self.assertEqual(bad, [])
        self.assertEqual([p for p in self.rec["files_opened"] if R.refused_path(os.path.join(HERE, p))], [])

    def test_it_is_written_once(self):
        with self.assertRaises(T.Refused):
            T.run_synthetic(synthetic_seed=SYNTHETIC_SEED, n_roads=1, out_dir=self.tmp, roads_record=self.roads_path,
                            jobs=1, log=QUIET)


# =====================================================================================================
class TimingPath(unittest.TestCase):
    """`timing`'s path: one SYNTHETIC road of the design (epa_roads.generate, 900 s) through the whole chain on
    the real contract's grid, the plant runs and the tau stood in for, and the real run's prediction written with
    the per-task counts. Not Guarded: it reads the real contract (no table; epa_roads' guard is installed)."""

    def test_timing_writes_its_record_once_with_the_prediction(self):
        with tempfile.TemporaryDirectory(prefix="epa_tightenings_timing_test_") as tmp:
            st = Stand()
            with st.installed(), mock.patch.object(RC, "tau_table", lambda ids, *, variant, jobs: {
                    T.PLANT: (TAU_B58_S, None)}):
                t, path = T.run_timing(out_dir=tmp, jobs=1, log=QUIET)
                with self.assertRaises(T.Refused):
                    T.run_timing(out_dir=tmp, jobs=1, log=QUIET)
            self.assertEqual(path, os.path.join(tmp, T.TIMING_NAME))
            rec = common.load_json(path)
            self.assertEqual(rec["tasks"], {"road": 49, "k3": 14, "above0": 1})     # one road: 4 + 3 x 15
            self.assertEqual(rec["real_run"]["road_runs"], 980)
            self.assertEqual((rec["real_run"]["k3_tasks"], rec["real_run"]["episode_steps"]), (14, 899))
            self.assertGreater(rec["real_run"]["predicted_wall_s"], 0.0)
            self.assertEqual(rec["synthetic_seed"], T.SYNTHETIC_SEED_TIMING)
            self.assertTrue(os.path.isfile(os.path.join(tmp, T.SYNTHETIC_OUT_NAME)))
            self.assertEqual(len(common.load_json(os.path.join(tmp, T.SYNTHETIC_ROADS_NAME))["roads"]), 1)
            runs = [r for r in st.calls["run"]]
            self.assertTrue(all(r["seed"] == V.EPISODES[0][0] for r in runs))       # road 0 with EPISODES[0]


# =====================================================================================================
class Isolation(Guarded):
    def test_no_hashed_module_imports_this_one(self):
        """Row 121 (2): the 35 files roads.json hashes (epa_roads.hashed_files) hold no epa_tightenings, and none of
        them imports it at any nesting."""
        files = R.hashed_files(root=HERE, engines=R.ENGINES)
        self.assertEqual(len(files), 35)
        self.assertNotIn(T.MODULE_REL, files)
        for f in files:
            if f.endswith(".py"):
                self.assertFalse(any(n.split(".")[0] == "epa_tightenings" for n in R._imports_of(os.path.join(HERE, f))), f)

    def test_the_closure_check_can_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            for name, src in (("hashed.py", "def f():\n    import epa_tightenings\n"), ("epa_tightenings.py", "x = 1\n")):
                with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                    fh.write(src)
            self.assertIn("epa_tightenings.py", R.import_closure("hashed.py", root=tmp))

    def test_it_imports_the_roads_module_and_hashes_its_closure(self):
        closure = R.import_closure(T.MODULE_REL, root=HERE)
        self.assertIn("epa_roads.py", closure)
        self.assertTrue(set(R.import_closure("epa_roads.py", root=HERE)) <= set(closure))
        cf = set(T.code_files(root=HERE))
        self.assertTrue(set(closure) | set(epa_freeze.CODE_HASHED) <= cf)
        self.assertIn("engine_specs/b58.toml", cf)


# =====================================================================================================
class AuditGuard(unittest.TestCase):
    """epa_roads' guard, which this module installs and every worker installs. Not Guarded: the fixture's own
    hook would count these refused opens as opens of real data."""

    def test_the_guard_refuses_the_epa_paths(self):
        for parts in (("data", "engines", "mazda_25t", "epa_" + "probe.txt"), ("logs", "epa", "x.txt"),
                      ("results", "EPA_VALIDATION", "x.json"), ("results", "x.csv")):
            with self.assertRaises(PermissionError):
                open(os.path.join(HERE, *parts), encoding="utf-8")
        self.assertFalse(R.refused_path(os.path.join(HERE, "results", "car_spark_boost.json")))   # the control


class Audit(Guarded):
    def test_a_run_opens_no_table_and_calls_no_reader(self):
        import epa_rows
        names = [n for n in ("calibration_rows", "read_held_out", "held_out_counts", "held_out_keys", "_records")
                 if hasattr(epa_rows, n)]
        self.assertTrue(names)
        with contextlib.ExitStack() as st:
            spies = {n: st.enter_context(mock.patch.object(epa_rows, n, side_effect=AssertionError(n))) for n in names}
            OPEN_LOG["seen"] = []
            OPEN_LOG["on"] = True
            try:
                (_, _, _, opened), _ = stood_in_compute(tiny_record(1), strategy=SMALL_GRID, seconds=413)
            finally:
                OPEN_LOG["on"] = False
        self.assertTrue(all(not s.called for s in spies.values()))
        self.assertEqual([p for p, _ in OPEN_LOG["seen"] if R.refused_path(p)], [])
        self.assertEqual([p for p in opened if R.refused_path(os.path.join(HERE, p))], [])


# =====================================================================================================
class Gates(Guarded):
    def test_the_roads_records_refusals(self):
        good = tiny_record(1)
        self.assertEqual(T.roads_problems(good, kind="SYNTHETIC"), [])
        self.assertTrue(T.roads_problems(good, kind="REAL"))                # a SYNTHETIC seed and one road
        cases = {
            "unpaired": lambda d: d["roads"][0].update(weights=list(V.EPISODES[1][1])),
            "another seed": lambda d: d["roads"][0].update(episode_seed=V.EPISODES[1][0]),
            "H not r tau": lambda d: d["H_table"]["b58"]["1.5"].update(H_s=71.0),
            "a 60-bit seed as SYNTHETIC": lambda d: d["commit_reveal"].update(roads_seed=2 ** 40),
            "another schema": lambda d: d.update(schema="epa-roads/0"),
            "no roads": lambda d: d.update(roads=[]),
            "another dt": lambda d: d["roads"][0].update(dt=0.5),
        }
        for what, edit in cases.items():
            bad = copy.deepcopy(good)
            edit(bad)
            self.assertTrue(T.roads_problems(bad, kind="SYNTHETIC"), what)

    def test_the_out_path(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertIsNone(T.out_problem(os.path.join(tmp, "t.json"), in_tree_rel=None))
            with open(os.path.join(tmp, "t.json"), "w", encoding="utf-8") as fh:
                fh.write("{}")
            self.assertIn("written once", T.out_problem(os.path.join(tmp, "t.json"), in_tree_rel=None))
        inside = os.path.join(HERE, "results", "x_never_written.json")
        self.assertIn("outside every work tree", T.out_problem(inside, in_tree_rel=None))
        self.assertIn("goes under", T.out_problem(inside, in_tree_rel=T.OUT_DIR_REL))
        timing = os.path.join(HERE, *T.OUT_DIR_REL.split("/"), "x_never_written.json")
        with mock.patch.object(epa_freeze, "git_clean", lambda paths, root: (False, ("epa_tightenings.py",))):
            self.assertIn("committed code", T.out_problem(timing, in_tree_rel=T.OUT_DIR_REL))
        with mock.patch.object(epa_freeze, "git_clean", lambda paths, root: (True, ())):
            self.assertIsNone(T.out_problem(timing, in_tree_rel=T.OUT_DIR_REL))
        with self.assertRaises(T.Refused):
            T.run_synthetic(synthetic_seed=SYNTHETIC_SEED, n_roads=1, out_dir=os.path.join(HERE, "results", "x"),
                            roads_record=None, jobs=1, log=QUIET)
        self.assertFalse(os.path.exists(os.path.join(HERE, "results", "x")))

    def test_the_writer_leaves_nothing_on_a_refusal(self):
        rec = {"schema": T.SCHEMA, "plant": "b58", "roads_sha": "0" * 64, "roads_seed": 1,
               "L1": {"slope_points_per_K": 0.0, "set": "s", "shift_k": 5.0, "damage_reading": "d"},
               "E8": {T.ROADS_KEYS["lambda"]: [[-0.02, 0.0], [0.0, 0.0], [0.02, 0.0]],
                      T.ROADS_KEYS["spark"]: [[-0.75, 0.0], [0.0, 0.0], [0.75, 0.0]]},
               "provenance": {"commit": "c", "code_sha_text": {}, **VE.b58_identity()}}
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "t.json")
            with self.assertRaises(T.Refused):                               # a zero slope (tightening_problems)
                T.write_checked(p, rec, strategy=SMALL_GRID)
            self.assertEqual(os.listdir(tmp), [])
            rec["L1"]["slope_points_per_K"] = 0.05
            T.write_checked(p, rec, strategy=SMALL_GRID)                     # the control
            self.assertEqual(os.listdir(tmp), ["t.json"])
            with self.assertRaises(T.Refused):                               # written once
                T.write_checked(p, rec, strategy=SMALL_GRID)

    def test_the_real_run_refuses_before_anything(self):
        with mock.patch.object(T, "real_problems", lambda root: (["a gate"], None, None)), \
                mock.patch.object(sys, "dont_write_bytecode", True), \
                mock.patch.object(T, "compute", side_effect=AssertionError("computed")):
            with self.assertRaises(T.Refused) as cm:
                T.run_real(jobs=1, log=QUIET)
        self.assertEqual(cm.exception.args[0], ["a gate"])

    def test_the_real_run_refuses_in_this_tree_while_the_roads_are_absent(self):
        if os.path.exists(os.path.join(HERE, *R.ROADS_REL.split("/"))):
            self.skipTest("results/EPA_ROADS/roads.json exists: the draw has run (test_epa_roads checks its record)")
        probs, rec, sha = T.real_problems(root=HERE)
        self.assertIsNone(rec)
        self.assertTrue(any("roads.json is absent" in p for p in probs), probs)
        self.assertFalse(os.path.exists(os.path.join(HERE, *T.OUT_REL.split("/"))))

    def test_the_real_run_refuses_a_python_that_writes_bytecode(self):
        with mock.patch.object(sys, "dont_write_bytecode", False), \
                mock.patch.object(T, "real_problems", side_effect=AssertionError("gated")):
            with self.assertRaises(T.Refused) as cm:
                T.run_real(jobs=1, log=QUIET)
        self.assertIn("python -B", cm.exception.args[0][0])

    def test_the_no_roads_route_refuses_in_this_tree_while_no_stop_is_committed(self):
        """Row 129 (4): `stopped` writes only after a committed non-defect stop; this tree has logged none. The
        shared branch is stood in for (no network in a test: StoppedRoute.test_f reads a bare origin)."""
        if os.path.exists(os.path.join(HERE, *R.ATTEMPTS_REL.split("/"))):
            self.skipTest(f"{R.ATTEMPTS_REL} exists: the draw has run (StoppedRoute and LiveRecord check the route)")
        remote = mock.patch.object(R, "remote_state", lambda root, head: (False, None, "STOOD IN: no network here"))
        with remote:
            probs, found = T.stopped_problems(root=HERE)
        self.assertTrue(any(f"{R.ATTEMPTS_REL} is not committed at HEAD" in p for p in probs), probs)
        self.assertTrue(any("do not end in exactly one stop that is not a coding defect" in p for p in probs), probs)
        self.assertTrue(any(p.startswith("the shared branch: STOOD IN") for p in probs), probs)
        self.assertIsNone(found["stop"])
        with remote, mock.patch.object(sys, "dont_write_bytecode", True), \
                mock.patch.object(T, "provenance", side_effect=AssertionError("built")):
            with self.assertRaises(T.Refused):
                T.run_stopped(log=QUIET)
        self.assertFalse(os.path.exists(os.path.join(HERE, *T.OUT_REL.split("/"))))


# =====================================================================================================
def committed_record_problems(t, *, root):
    """What validate_epa's arming does not check of a committed results/EPA_TIGHTENINGS.json (it takes any
    record in the layout with the B58's plant_sha and engine_sha, a SYNTHETIC one included), [] when all holds:
    seed_kind REAL; roads_sha and roads_seed roads.json's; the provenance (epa_tightenings.provenance_problems,
    which the no-roads record's check shares: the code and the data inputs committed and clean at the run, with
    no compiled file beside the code; provenance.commit an ancestor of (or) the record's last commit, and each
    code_sha_text the sha256 of that file's blob at provenance.commit; the B58's plant_sha 865f8e7b7e5c2dbe);
    above0 measured and the pinned one; every K3 knee the pinned one; the pinned folder unchanged by the run and
    as it is now."""
    out = []
    roads_path = os.path.join(root, *R.ROADS_REL.split("/"))
    roads = common.load_json(roads_path)
    if t.get("seed_kind") != "REAL":
        out.append(f"seed_kind is {t.get('seed_kind')!r}, not 'REAL'")
    if t.get("roads_sha") != R.roads_sha(roads_path):
        out.append("roads_sha is not roads.json's")
    if t.get("roads_seed") != roads["commit_reveal"]["roads_seed"]:
        out.append("roads_seed is not roads.json's")
    out += T.provenance_problems(t, root=root)
    e8 = t.get("E8") or {}
    pinned = T.pinned_k3(root=root)
    if e8.get("above0_measured") is not True or e8.get("time_above_nominal_s") != pinned["time_above_nominal_s"]:
        out.append(f"above0 {e8.get('time_above_nominal_s')!r} (measured {e8.get('above0_measured')!r}) is not "
                   f"k3_nominal.json's {pinned['time_above_nominal_s']}")
    if e8.get("knees_equal_pinned") is not True:
        out.append(f"E8.knees_equal_pinned is {e8.get('knees_equal_pinned')!r}")
    ecu = t.get("ecu_folder_sha256") or {}
    if not ecu.get("before") == ecu.get("after") == pinned["folder"]:
        out.append("results/ENGINE_THRESHOLDS/ecu/ changed during the run or since")
    return out


def rmtree_writable(path):
    """shutil.rmtree that clears the read-only bit git sets on its object files (Windows refuses to delete
    those), so the temporary repository goes with the class; a folder already gone is no error."""
    def again(fn, p, exc):
        os.chmod(p, stat.S_IWRITE)
        fn(p)
    if os.path.exists(path):
        shutil.rmtree(path, onexc=again)


def canned_compute(record, *, roads_ref, strategy, r_e8_pct, spark, pinned, seconds, jobs, log, pinned_strict=False):
    """compute stood in for RealGates' run_real: L1 from two roads of hand-worked runs (hand_runs), E8 from
    hand-written damages on every road with every K3 knee the pinned one and above0 the pinned seconds, the
    B58's band on those tables. No plant runs; the record is a test's, never the tightenings."""
    if not (pinned_strict is True and seconds is None):
        raise AssertionError("run_real must ask compute for the strict checks, above0 measured")
    roads = record["roads"]
    runs, _ = hand_runs(2)
    l1 = T.l1_block(runs, [{"dt": 1.0}] * 2, H=T.horizons(record), roads_ref=roads_ref)
    shifts = T.e8_shifts(strategy)
    k0 = T._b58().engine.damage.turb_knee_k
    a0 = pinned["time_above_nominal_s"]
    e8_runs = {}
    for name, ds, dl in shifts:
        for i in range(len(roads)):
            for pol, d in (("neutral", 100.0 + i), ("reactive", 99.0 + i), ("cg", 80.0 + i - 200.0 * dl + 3.0 * ds)):
                e8_runs[(name, i, pol)] = {"D_knock": d, "D_noknock": 0.9 * d, "peak_turb_k": 1100.0}
    knees = {name: {"knee_k": pinned["knees"][name], "k0": k0, "seconds": None if name == "nominal" else a0,
                    "time_above_knee_s": None, "second_knee_identical": None if name == "nominal" else True,
                    "trace_sha256": None} for name, _, _ in shifts}
    e8 = T.e8_block(e8_runs, knees, shifts, roads, strategy=strategy,
                    above0={"time_above_nominal_s": a0, "measured": True}, pinned=pinned)
    e8["b58_u_val_kappa"] = T.b58_band({T.ROADS_KEYS[x]: e8[T.ROADS_KEYS[x]] for x in T.ROADS_KEYS},
                                       strategy=strategy, r_pct=r_e8_pct, spark=spark)
    return l1, e8, T.timing_of({}, wall=0.0, jobs=jobs, n_roads=len(roads), n_shifts=len(shifts)), []


HASH_LINE = re.compile(r"^(COMMITMENT_[GJ]) = (?:None|'[0-9a-f]{64}'|\"[0-9a-f]{64}\")(?=\r?$)", re.M)


def gates_repository(root):
    """The synthetic git repository RealGates and StoppedRoute run in, at `root` (a new folder): a copy of the code
    (code_files, the roads module's hashed files) and the data inputs (the contract, results/car_spark_boost.json,
    the pinned K3 folder), with __pycache__/ ignored, committed on main (core.autocrlf true, the fixture's names
    and dates). Returns the commit."""
    files = set(T.code_files(root=HERE)) | set(R.hashed_files(root=HERE, engines=(T.PLANT,)))
    files |= set(R.CONTRACT_FILES) | {T.SPARK_RECORD_REL}
    ecu = os.path.join(HERE, *T.ECU_DIR_REL.split("/"))
    files |= {f"{T.ECU_DIR_REL}/{n}" for n in os.listdir(ecu) if os.path.isfile(os.path.join(ecu, n))}
    for rel in sorted(files):
        dst = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(os.path.join(HERE, *rel.split("/")), dst)
    mod = os.path.join(root, R.MODULE_REL)             # the copy's roads module as R0a committed it: both hash
    with open(mod, encoding="utf-8", newline="") as fh:   # lines None, whatever the tree holds (row 132 (2))
        src = fh.read()
    src, n = HASH_LINE.subn(r"\1 = None", src)
    assert n == 2
    with open(mod, "w", encoding="utf-8", newline="") as fh:
        fh.write(src)
    with open(os.path.join(root, ".gitignore"), "wb") as fh:
        fh.write(b"__pycache__/\n")
    fx.git(root, "init", "-q", "-b", "main")
    fx.git(root, "config", "core.autocrlf", "true")
    fx.git(root, "config", "user.name", fx.GIT_ENV["GIT_AUTHOR_NAME"])
    fx.git(root, "config", "user.email", fx.GIT_ENV["GIT_AUTHOR_EMAIL"])
    return fx.commit_all(root, "synthetic copy: the code and the data inputs")


def roads_commit_in(root):
    """The roads commit (row 96) in a gates_repository: both hash lines of the copy's epa_roads.py set, in one
    commit, from two fresh TEST integers (never the team's). Returns (the commit, a_G, a_J, line G, line J)."""
    a_g, a_j = R.new_private_integer(), R.new_private_integer()
    h_g, h_j = R.commitment_hash(a_g), R.commitment_hash(a_j)
    mod = os.path.join(root, R.MODULE_REL)
    with open(mod, encoding="utf-8", newline="") as fh:
        src = fh.read()
    new = src.replace("COMMITMENT_G = None", f'COMMITMENT_G = "{h_g}"').replace(
        "COMMITMENT_J = None", f'COMMITMENT_J = "{h_j}"')
    assert new.count(h_g) == 1 and new.count(h_j) == 1
    with open(mod, "w", encoding="utf-8", newline="") as fh:
        fh.write(new)
    return fx.commit_all(root, "synthetic roads commit: the two hash lines"), a_g, a_j, h_g, h_j


def side_commit(root, files, *, parents, message, tree_of=None):
    """A commit made with plumbing only in the synthetic repository at `root` (a temporary index, commit-tree), so
    the work tree, the index and HEAD are left as they are: the tree of `tree_of` (parents[0] by default) with
    `files` {repository-relative path: bytes} added or replaced, its parents `parents`, the fixture's names and
    dates. Returns its sha."""
    index = os.path.join(root, ".git", "side_commit.index")
    env = dict(os.environ, GIT_INDEX_FILE=index, **fx.GIT_ENV)

    def g(*args, data=None):
        r = subprocess.run(["git", "-C", root, *args], capture_output=True, env=env, input=data)
        if r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)} failed in {root}: {r.stderr.decode(errors='replace')}")
        return r.stdout.decode().strip()
    try:
        g("read-tree", tree_of or parents[0])
        for rel, data in files.items():
            g("update-index", "--add", "--cacheinfo", f"100644,{g('hash-object', '-w', '--stdin', data=data)},{rel}")
        return g("commit-tree", g("write-tree"), *[a for p in parents for a in ("-p", p)], "-m", message)
    finally:
        if os.path.exists(index):
            os.remove(index)


class RealGates(unittest.TestCase):
    """real_problems' gates and run_real's writer in a synthetic git repository under a temporary folder: a copy
    of the code (code_files, the roads module's hashed files) and the data inputs (the contract,
    results/car_spark_boost.json, the pinned K3 folder), committed; a roads commit that sets both hash lines from
    two fresh private integers (a TEST commit and reveal: its roads_seed is never the test's, which needs the
    team's two integers); a REAL-kind roads.json of twenty roads from epa_roads.generate, its hashes taken in the
    copy, and its attempts log, committed. The control is real_problems == []; each refusal is a spoiled copy,
    restored to the control after. The B58 as built is this tree's (validate_epa.b58_identity), so a plant other
    than the B58 is stood in for. Not Guarded: the copy reads the real contract (no table; epa_roads' guard is
    installed). The methods run in name order; test_z commits a record and runs last."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="epa_tightenings_gates_")
        cls.addClassCleanup(rmtree_writable, cls.tmp)
        root = cls.root = os.path.join(cls.tmp, "repo")
        gates_repository(root)
        commit, a_g, a_j, h_g, h_j = roads_commit_in(root)
        seed = R.roads_seed_from(a_g, a_j, commit)
        ident = VE.b58_identity()
        cls.roads = R.jsonable({
            "schema": R.ROADS_SCHEMA, "seed_kind": "REAL", "design": R.design(), "streams": R.streams(),
            "engines": [T.PLANT], "ratios": list(T.RATIOS), "roads": R.generate(seed, n_roads=R.N_ROADS),
            "commit_reveal": {"roads_seed": seed, "roads_commit": commit, "reveal": {"ghassan": a_g, "jad": a_j},
                              "hash_lines": {"ghassan": h_g, "jad": h_j}},
            "tau": {T.PLANT: {"tau_s": TAU_B58_S, "plant_sha": ident["plant_sha"], "engine_sha": ident["engine_sha"]}},
            "H_table": R.h_table({T.PLANT: TAU_B58_S}, T.RATIOS, dt=R.DT),
            "hashes": R.provenance(root=root, engines=(T.PLANT,)),
            "note": "TEST ONLY: a REAL-kind roads record in a temporary repository (test_epa_tightenings.RealGates)"})
        cls.roads_path = os.path.join(root, *R.ROADS_REL.split("/"))
        cls.attempts_path = os.path.join(root, *R.ATTEMPTS_REL.split("/"))
        cls.sha = cls.put_roads(cls.roads)
        fx.commit_all(root, "synthetic R1: roads.json and its attempts log")

    @classmethod
    def put_roads(cls, rec, log_shas=None):
        if os.path.exists(cls.roads_path):
            os.remove(cls.roads_path)
        R.write_once(cls.roads_path, rec)
        sha = R.roads_sha(cls.roads_path)
        with open(cls.attempts_path, "w", encoding="utf-8", newline="\n") as fh:
            for s in (log_shas(sha) if log_shas else [sha]):
                fh.write(json.dumps({"step": "draw", "event": "outcome", "outcome": "roads", "roads_sha": s}) + "\n")
        return sha

    def probs(self):
        return T.real_problems(root=self.root)[0]

    def assertRefused(self, *needles):
        ps = self.probs()
        for n in needles:
            self.assertTrue(any(n in p for p in ps), (n, ps))
        return ps

    def assertControl(self):
        self.assertEqual(self.probs(), [])

    @contextlib.contextmanager
    def spoiled(self, rel):
        p = os.path.join(self.root, *rel.split("/"))
        with open(p, "rb") as fh:
            keep = fh.read()
        try:
            yield p
        finally:
            with open(p, "wb") as fh:
                fh.write(keep)

    def append(self, p, text):
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def test_a_the_control(self):
        probs, rec, sha = T.real_problems(root=self.root)
        self.assertEqual(probs, [])
        self.assertEqual((sha, rec["commit_reveal"]["roads_seed"]), (self.sha, self.roads["commit_reveal"]["roads_seed"]))

    def test_b_uncommitted_code(self):
        for rel in (T.MODULE_REL, "car_spark_boost.py", "validate_epa.py", "thresholds/common.py"):
            with self.spoiled(rel) as p:
                self.append(p, "\n# test edit\n")
                self.assertRefused(f"the code is not committed and clean: {rel}")
            self.assertControl()

    def test_c_compiled_files_beside_the_code(self):
        for rel in ("__pycache__/plant.cpython-313.pyc", "thresholds/__pycache__/contract.cpython-313.pyc"):
            p = os.path.join(self.root, *rel.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "wb") as fh:
                fh.write(b"")
            try:
                ps = self.assertRefused("compiled files stand beside the code", rel)
                self.assertEqual(len(ps), 1, ps)                       # gitignored: no git gate sees it
            finally:
                os.remove(p)
            self.assertControl()
        # the control of the match: a cache of a module outside the code is not the code's
        p = os.path.join(self.root, "__pycache__", "notcode.cpython-313.pyc")
        with open(p, "wb") as fh:
            fh.write(b"")
        try:
            self.assertControl()
        finally:
            os.remove(p)

    def test_d_uncommitted_data_inputs(self):
        for rel in (T.SPARK_RECORD_REL, f"{T.ECU_DIR_REL}/k3_nominal.json", R.CONTRACT_FILES[1]):
            with self.spoiled(rel) as p:
                self.append(p, "\n")
                self.assertRefused(f"the run's data inputs are not committed and clean: {rel}")
            self.assertControl()
        stray = os.path.join(self.root, *T.ECU_DIR_REL.split("/"), "stray.json")
        with open(stray, "w", encoding="utf-8") as fh:
            fh.write("{}")
        try:
            self.assertRefused("the run's data inputs are not committed and clean")
        finally:
            os.remove(stray)
        self.assertControl()

    def test_e_the_roads_steps_outputs_uncommitted(self):
        with self.spoiled(R.ROADS_REL) as p:
            d = common.load_json(p)
            d["note"] += " (edited)"
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(d) + "\n")
            self.assertRefused(f"{R.ROADS_DIR_REL}/ is not committed and clean", f"{R.ROADS_REL} is not committed at HEAD",
                               "the attempts log does not name this roads.json's roads_sha")
        self.assertControl()
        stray = os.path.join(self.root, *R.ROADS_DIR_REL.split("/"), "stray.json")
        with open(stray, "w", encoding="utf-8") as fh:
            fh.write("{}")
        try:
            self.assertRefused(f"{R.ROADS_DIR_REL}/ is not committed and clean")
        finally:
            os.remove(stray)
        with self.spoiled(R.ATTEMPTS_REL) as p:
            self.append(p, json.dumps({"step": "draw", "event": "note"}) + "\n")
            self.assertRefused(f"{R.ROADS_DIR_REL}/ is not committed and clean")
        self.assertControl()

    def test_f_a_roads_json_the_attempts_log_does_not_name(self):
        other = copy.deepcopy(self.roads)
        other["note"] += " (a second roads.json)"
        self.put_roads(other, lambda s: [self.sha])
        fx.commit_all(self.root, "test: another roads.json, the log unchanged")
        self.assertRefused("the attempts log does not name this roads.json's roads_sha")
        self.put_roads(other, lambda s: [self.sha, s])
        fx.commit_all(self.root, "test: two roads outcomes")
        self.assertRefused("the attempts log does not name this roads.json's roads_sha")
        self.put_roads(self.roads)
        fx.commit_all(self.root, "test: the first roads.json back")
        self.assertControl()

    def test_g_a_roads_seed_the_reveal_does_not_give(self):
        bad = copy.deepcopy(self.roads)
        bad["commit_reveal"]["roads_seed"] ^= 1
        self.put_roads(bad)
        fx.commit_all(self.root, "test: a roads_seed that is not the reveal's")
        self.assertRefused("roads_seed is not the one the reveal gives")
        bad = copy.deepcopy(self.roads)
        bad["commit_reveal"]["reveal"]["jad"] += 1
        self.put_roads(bad)
        fx.commit_all(self.root, "test: a reveal that is not the hash line's")
        self.assertRefused("reveals do not match its hash lines")
        self.put_roads(self.roads)
        fx.commit_all(self.root, "test: the roads.json back")
        self.assertControl()

    def test_h_a_plant_other_than_the_b58(self):
        """A value edit of the copy's b58.toml (a comment would not move plant_sha: fingerprint hashes code only)
        is refused as code not committed and, committed, as a file roads.json hashed differently. The B58 as built
        is this tree's, so another plant_sha is stood in for; and a roads record whose tau is on another plant."""
        rel = "engine_specs/b58.toml"
        with self.spoiled(rel) as p:
            with open(p, "rb") as fh:
                b = fh.read()
            self.assertEqual(b.count(b"turb_knee_k = { value = 1123.0,"), 1)
            with open(p, "wb") as fh:
                fh.write(b.replace(b"turb_knee_k = { value = 1123.0,", b"turb_knee_k = { value = 1124.0,"))
            self.assertRefused(f"the code is not committed and clean: {rel}", f"{rel}: its sha_text is not roads.json's")
            fx.commit_all(self.root, "test: another B58, committed")
            ps = self.assertRefused(f"{rel}: its sha_text is not roads.json's")
            self.assertFalse(any("the code is not committed" in x for x in ps), ps)
        fx.commit_all(self.root, "test: the B58 back")
        self.assertControl()
        other = dict(VE.b58_identity(), plant_sha="4580f7ffdfad7a16")
        with mock.patch.object(VE, "b58_identity", lambda: other):
            self.assertRefused(f"the B58 as built is plant_sha 4580f7ffdfad7a16, not {R.B58_PLANT_SHA}")
        bad = copy.deepcopy(self.roads)
        bad["tau"][T.PLANT]["plant_sha"] = "4580f7ffdfad7a16"
        self.put_roads(bad)
        fx.commit_all(self.root, "test: a tau on another plant")
        self.assertRefused(f"the B58's tau is not on plant_sha {R.B58_PLANT_SHA}")
        self.put_roads(self.roads)
        fx.commit_all(self.root, "test: the roads.json back")
        self.assertControl()

    def test_z_run_real_writes_once_and_the_committed_record_is_checked(self):
        """run_real, compute stood in (canned_compute), writes the record once from the clean copy and refuses a
        second run; validate_epa's loader and checks take it; committed, committed_record_problems finds nothing
        (the control), and each spoiled copy of it is refused, a SYNTHETIC record among them (validate_epa's arming
        takes those). Afterwards the gates refuse for good: the record exists, and was committed."""
        out = os.path.join(self.root, *T.OUT_REL.split("/"))
        with mock.patch.object(sys, "dont_write_bytecode", True), mock.patch.object(T, "compute", canned_compute):
            sha, rec = T.run_real(jobs=1, log=QUIET, root=self.root)
            self.assertTrue(os.path.isfile(out))
            self.assertFalse(os.path.exists(out + ".partial"))
            with self.assertRaises(T.Refused) as cm:
                T.run_real(jobs=1, log=QUIET, root=self.root)
        self.assertTrue(any("exists: it is written once" in p for p in cm.exception.args[0]), cm.exception.args)
        t = VE.load_tightenings(out)
        self.assertEqual(t.sha_text, sha)
        self.assertEqual(VE.tightening_problems(t, {"ecu_strategy_b58": T.contract_inputs()["ecu_strategy_b58"]},
                                                b58=VE.b58_identity()), [])
        self.assertEqual((t.roads_sha, t.roads_seed, t.raw["seed_kind"]),
                         (self.sha, self.roads["commit_reveal"]["roads_seed"], "REAL"))
        self.assertEqual(rec["provenance"]["git"]["bytecode_caches"], [])
        self.assertEqual(sorted(rec["provenance"]["code_sha_text"]), T.code_files(root=self.root))
        fx.commit_all(self.root, "synthetic R3b: the tightenings record")
        good = common.load_json(out)
        self.assertEqual(committed_record_problems(good, root=self.root), [])                # the control
        # a commit with HEAD's tree and no parent: its blobs are the code's, so only the ancestor check can refuse it
        outside = side_commit(self.root, {}, parents=[], message="test: a commit outside the history", tree_of="HEAD")
        bad = copy.deepcopy(good)
        bad["provenance"]["commit"] = outside
        self.assertEqual(committed_record_problems(bad, root=self.root),
                         [f"provenance.commit {outside!r} is not an ancestor of the record's commit "
                          f"{fx.git(self.root, 'rev-parse', 'HEAD')}"])
        spoils = {
            "SYNTHETIC": lambda d: d.update(seed_kind="SYNTHETIC"),
            "another roads_sha": lambda d: d.update(roads_sha="0" * 64),
            "another roads_seed": lambda d: d.update(roads_seed=d["roads_seed"] ^ 1),
            "dirty code": lambda d: d["provenance"]["git"].update(code_clean=False),
            "dirty data": lambda d: d["provenance"]["git"].update(data_inputs_clean=False),
            "a compiled file": lambda d: d["provenance"]["git"].update(bytecode_caches=["__pycache__/plant.pyc"]),
            "another plant": lambda d: d["provenance"].update(plant_sha="4580f7ffdfad7a16"),
            "an unknown commit": lambda d: d["provenance"].update(commit="0" * 40),
            "another code hash": lambda d: d["provenance"]["code_sha_text"].update({T.MODULE_REL: "0" * 64}),
            "no module hash": lambda d: d["provenance"]["code_sha_text"].pop(T.MODULE_REL),
            "above0 not measured": lambda d: d["E8"].update(above0_measured=False),
            "another above0": lambda d: d["E8"].update(time_above_nominal_s=412),
            "a knee off the pinned": lambda d: d["E8"].update(knees_equal_pinned=False),
            "the folder changed": lambda d: d["ecu_folder_sha256"].update(after="0" * 64),
        }
        for what, edit in spoils.items():
            bad = copy.deepcopy(good)
            edit(bad)
            self.assertNotEqual(committed_record_problems(bad, root=self.root), [], what)
        ps = self.assertRefused(f"{T.OUT_REL} exists: it is written once", f"{T.OUT_REL} was committed in HEAD's history")
        os.remove(out)
        fx.commit_all(self.root, "test: the record deleted")
        ps = self.probs()
        self.assertEqual(ps, [f"{T.OUT_REL} was committed in HEAD's history: the tightenings are measured once"])


WITHHELD = 2 ** 128          # row 129 (4): a withheld or lost integer, as it is entered in `epa_roads.py draw`


@contextlib.contextmanager
def draw_stood_in(seed_calls):
    """test_epa_roads.Reveal's stand-ins for epa_roads.draw()'s plant work: the frozen check passes, the hashes are
    empty, the ceiling module gives its ratios. first_draw and roads_seed_from record a call in `seed_calls` and fail:
    a reveal that does not match its hash line stops the draw before roads_seed is computed (epa_roads.py:1598-1602
    against :1611)."""
    def reached(*a, **k):
        seed_calls.append(a)
        raise AssertionError("roads_seed was used after a reveal that does not match")
    frozen = {"versions": {"python": "3.13.2", "platform": "SYNTHETIC"}, "plants": {}}
    prov = {"files": {}, "contract": {}, "plants": {}, "versions": {}}
    stand = {"frozen_problems": lambda *a, **k: ([], frozen), "provenance": lambda **k: prov, "first_draw": reached,
             "roads_seed_from": reached, "_ceiling_module": lambda: types.SimpleNamespace(RATIOS=(0.5, 1.5))}
    with contextlib.ExitStack() as st:
        for name, value in stand.items():
            st.enter_context(mock.patch.object(R, name, value))
        yield


class StoppedRoute(unittest.TestCase):
    """Row 129 (4)'s route in a synthetic git repository built as RealGates builds one (gates_repository,
    roads_commit_in), pushed to a bare origin beside it: a real epa_roads.draw() on the roads commit, its plant work
    stood in for (draw_stood_in), Ghassan's reveal his integer and Jad's withheld, entered as 2**128; the stop
    committed and pushed, as the protocol between attempts does. The control is stopped_problems == [] with
    run_stopped writing once, then refusing, and what it wrote read against the contract here, not through
    untightened (test_b, in a copy; mistake 12); each gate is made on the control and undone to it (test_c, the
    re-check before the write among them), or made in a copy of its own when it needs a commit (test_d, test_e:
    the log as draw writes it), or an origin of its own (test_f: the shared branch, the fork at the roads commit
    among it); test_z writes, commits and pushes the record here and calls the arming. Not Guarded: the copy is
    made from the real contract (no table; epa_roads' guard is installed). The methods run in name order; test_z
    runs last."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="epa_tightenings_stopped_")
        cls.addClassCleanup(rmtree_writable, cls.tmp)
        root = cls.root = os.path.join(cls.tmp, "repo")
        gates_repository(root)
        fx.git(cls.tmp, "init", "-q", "--bare", "origin.git")
        fx.git(root, "remote", "add", "origin", os.path.join(cls.tmp, "origin.git"))
        cls.roads_commit, cls.a_g, cls.a_j, cls.h_g, cls.h_j = roads_commit_in(root)
        cls.push()
        cls.pre = cls.copy_of(root, "pre_draw")             # before the draw: test_e's hand-written logs
        cls.log_path = os.path.join(root, *R.ATTEMPTS_REL.split("/"))
        cls.seed_calls, cls.stop, cls.later = [], None, None
        with draw_stood_in(cls.seed_calls):
            try:
                R.draw(str(cls.a_g), str(WITHHELD), roads_commit_announced=cls.roads_commit, note=None, root=root,
                       jobs=1)
            except R.RoadsStop as exc:
                cls.stop = exc
        cls.lines = R.read_attempts(cls.log_path)
        fx.commit_all(root, "the roads stop, attempt 1: Jad's integer withheld, entered as 2**128 (SYNTHETIC)")
        cls.push()
        with draw_stood_in(cls.seed_calls):
            try:
                R.draw(str(cls.a_g), str(cls.a_j), roads_commit_announced=cls.roads_commit,
                       note="SYNTHETIC: Jad's integer found", root=root, jobs=1)
            except R.Refused as exc:
                cls.later = " | ".join(exc.args[0])
        cls.contract = common.load_json(os.path.join(root, *T.CONTRACT_JSON_REL.split("/")))

    @classmethod
    def push(cls):
        fx.git(cls.root, "push", "-q", "origin", "HEAD:refs/heads/GRA-test")
        fx.git(cls.root, "fetch", "-q", "origin")

    @classmethod
    def copy_of(cls, src, label):
        dst = os.path.join(cls.tmp, label)
        shutil.copytree(src, dst)
        return dst

    @classmethod
    def own_origin(cls, cp, label, *, tip="HEAD", bare=None):
        """The copy `cp`'s origin made a bare repository of its own (a new one named `label`, or `bare`), so the
        shared one is left; its GRA-test set to `tip` (None: left as it is) and fetched. Returns the bare path."""
        if bare is None:
            fx.git(cls.tmp, "init", "-q", "--bare", f"{label}.git")
            bare = os.path.join(cls.tmp, f"{label}.git")
        fx.git(cp, "remote", "set-url", "origin", bare)
        if tip is not None:
            fx.git(cp, "push", "-q", "-f", "origin", f"{tip}:refs/heads/GRA-test")
        fx.git(cp, "fetch", "-q", "origin")
        return bare

    def probs(self, root=None):
        return T.stopped_problems(root=root or self.root)[0]

    def assertRefused(self, *needles, root=None):
        ps = self.probs(root)
        for n in needles:
            self.assertTrue(any(n in p for p in ps), (n, ps))
        return ps

    def assertControl(self, root=None):
        self.assertEqual(self.probs(root), [])

    @contextlib.contextmanager
    def spoiled(self, rel):
        p = os.path.join(self.root, *rel.split("/"))
        with open(p, "rb") as fh:
            keep = fh.read()
        try:
            yield p
        finally:
            with open(p, "wb") as fh:
                fh.write(keep)

    @staticmethod
    def append(p, text):
        with open(p, "a", encoding="utf-8", newline="\n") as fh:
            fh.write(text)

    def test_a_the_draw_logged_a_stop_that_is_not_a_coding_defect(self):
        """Jad's integer withheld, entered as 2**128, the smallest integer parse_reveal takes (one below it is refused
        before anything is logged): draw() logs its start line and a stop that is not a coding defect, raises
        RoadsStop, never reaches roads_seed, writes nothing else, and refuses a later attempt with both right
        integers, writing nothing."""
        self.assertIsInstance(self.stop, R.RoadsStop)
        self.assertNotIsInstance(self.stop, R.CodingDefect)
        self.assertEqual(self.seed_calls, [])
        self.assertEqual([(x["event"], x.get("outcome"), x.get("coding_defect")) for x in self.lines],
                         [("start", None, None), ("outcome", "stop", False)])
        self.assertEqual(self.lines[0]["reveal"], {"ghassan": self.a_g, "jad": WITHHELD})
        self.assertEqual(self.lines[0]["reveal_matches"], {"ghassan": True, "jad": False})
        self.assertEqual(self.lines[0]["roads_commit"], self.roads_commit)
        self.assertIn("has ended", self.later or "")
        self.assertEqual(R.read_attempts(self.log_path), self.lines)
        self.assertEqual(sorted(os.listdir(os.path.dirname(self.log_path))), ["attempts.jsonl"])
        self.assertEqual(R.parse_reveal(str(WITHHELD)), WITHHELD)
        with self.assertRaises(R.Refused):
            R.parse_reveal(str(WITHHELD - 1))

    def test_b_the_control(self):
        probs, found = T.stopped_problems(root=self.root)
        self.assertEqual(probs, [])
        self.assertEqual((found["attempt"], found["roads_commit"], found["stop"]), (1, self.roads_commit, self.lines[1]))
        self.assertEqual(found["reveal_matches_rechecked"], {"ghassan": True, "jad": False})
        # the writer, once, in a copy of this state (test_z writes here, last)
        cp = self.copy_of(self.root, "control_write")
        self.assertControl(cp)
        out = os.path.join(cp, *T.OUT_REL.split("/"))
        with mock.patch.object(sys, "dont_write_bytecode", True):
            sha, rec = T.run_stopped(log=QUIET, root=cp)
            self.assertTrue(os.path.isfile(out))
            self.assertFalse(os.path.exists(out + ".partial"))
            with self.assertRaises(T.Refused) as cm:
                T.run_stopped(log=QUIET, root=cp)
        self.assertTrue(any(f"{T.OUT_REL} exists: it is written once" in p for p in cm.exception.args[0]),
                        cm.exception.args)
        t = VE.load_tightenings(out)
        self.assertEqual(t.sha_text, sha)
        self.assertEqual(VE.tightening_problems(t, self.contract, b58=VE.b58_identity()), [])
        self.assertEqual((t.plant, t.roads_sha, t.roads_seed, t.raw["seed_kind"]), ("b58", "none", -1, "NONE"))
        self.assertIs(type(t.roads_seed), int)
        self.assertEqual(sorted(rec["provenance"]["code_sha_text"]), T.code_files(root=cp))
        self.assertEqual(rec["provenance"]["git"]["bytecode_caches"], [])
        self.assertEqual(rec["no_roads"]["stop"], self.lines[1])
        self.assertEqual(rec["no_roads"]["earlier_attempts_both_matching"], [])
        self.assertEqual(rec["no_roads"]["shared_branch_at_write"],
                         {"remote": "origin", "branch": "GRA-test", "sha": fx.git(cp, "rev-parse", "HEAD")})
        # what the writer read from the contract, against the contract read here and row 107 (4)'s figures, never
        # through untightened, which the record's check shares with the writer (mistake 12)
        largest, strategy = self.contract["knee_shift"]["largest"], self.contract["ecu_strategy_b58"]
        l1, e8 = rec["L1"], rec["E8"]
        self.assertEqual(float.hex(l1["slope_points_per_K"]), float.hex(float(largest["slope"])))
        self.assertEqual(l1["set"], largest["set"])
        self.assertIs(type(l1["shift_k"]), float)
        self.assertEqual(l1["shift_k"], float(largest["shift_k"]))
        self.assertIs(largest["knock"], True)                         # so the reading is the knock term on
        self.assertEqual(l1["damage_reading"], "knock term on (the episode's damage)")
        self.assertEqual(e8["k3_pair_change_vs_lambda_roads"], strategy["k3_pair_change_vs_lambda"])
        self.assertEqual(e8["k3_pair_change_vs_spark_roads"], strategy["k3_pair_change_vs_spark"])
        band = e8["b58_u_val_kappa"]
        for reading, want in ((band["with_roads"], (25.86, 15.65, "untested", 3.443, 16.6)),
                              (band["model_minus_car"]["with_roads"], (23.53, 11.98, "untested", 2.861, 16.6))):
            self.assertEqual((round(reading["E_pct"], 2), round(reading["u_val_pct"], 2), reading["label"],
                              round(reading["kappa"], 3), reading["R_pct"]), want)
        self.assertEqual(band["with_roads"], band["locked_climb_only"])
        label = "untightened: no roads (row 103 (3))"
        self.assertEqual(T.UNTIGHTENED, label)
        self.assertEqual((rec["untightened"], l1["label"], e8["label"], l1["tightened"], e8["tightened"]),
                         (label, label, label, False, False))

    def test_c_each_gate_from_the_control_and_back(self):
        """Every gate that needs no commit, made on the control and undone to it."""
        out = os.path.join(self.root, *T.OUT_REL.split("/"))
        for rel, needle in ((T.OUT_REL, f"{T.OUT_REL} exists: it is written once"),
                            (R.ROADS_REL, f"{R.ROADS_REL} exists: a road set was drawn"),
                            (f"{R.ROADS_DIR_REL}/stray.json", f"{R.ROADS_DIR_REL}/ is not committed and clean")):
            p = os.path.join(self.root, *rel.split("/"))
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                fh.write("{}\n")
            try:
                self.assertRefused(needle)
            finally:
                os.remove(p)
            self.assertControl()
        for rel in (T.MODULE_REL, R.MODULE_REL, "validate_epa.py", "thresholds/common.py"):
            with self.spoiled(rel) as p:
                self.append(p, "\n# test edit\n")
                self.assertRefused(f"the code is not committed and clean: {rel}")
            self.assertControl()
        for rel in (T.SPARK_RECORD_REL, R.CONTRACT_FILES[0], f"{T.ECU_DIR_REL}/k3_nominal.json"):
            with self.spoiled(rel) as p:
                self.append(p, "\n")
                self.assertRefused(f"the run's data inputs are not committed and clean: {rel}")
            self.assertControl()
        rel = "__pycache__/epa_tightenings.cpython-313.pyc"
        p = os.path.join(self.root, *rel.split("/"))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(b"")
        try:
            ps = self.assertRefused("compiled files stand beside the code", rel)
            self.assertEqual(len(ps), 1, ps)                           # gitignored: no git gate sees it
        finally:
            os.remove(p)
        self.assertControl()
        with self.spoiled(R.ATTEMPTS_REL) as p:
            self.append(p, json.dumps({"step": "draw", "event": "note"}) + "\n")
            self.assertRefused(f"{R.ATTEMPTS_REL} in the tree is not HEAD's", "do not end in exactly one stop")
        self.assertControl()
        other = dict(VE.b58_identity(), plant_sha="4580f7ffdfad7a16")
        with mock.patch.object(VE, "b58_identity", lambda: other):
            self.assertRefused(f"the B58 as built is plant_sha 4580f7ffdfad7a16, not {R.B58_PLANT_SHA}")
        self.assertControl()
        with mock.patch.object(sys, "dont_write_bytecode", False), \
                mock.patch.object(T, "stopped_problems", side_effect=AssertionError("gated")):
            with self.assertRaises(T.Refused) as cm:
                T.run_stopped(log=QUIET, root=self.root)
        self.assertIn("python -B", cm.exception.args[0][0])
        self.assertFalse(os.path.exists(out))
        self.assertControl()
        # the second check, before the write: the contract changes after the first check, while the record is built
        real_blocks = T.stopped_blocks

        def blocks_then_an_edit(ci, spark):
            blocks = real_blocks(ci, spark)
            self.append(os.path.join(self.root, *R.CONTRACT_FILES[1].split("/")), "\n")
            return blocks
        with self.spoiled(R.CONTRACT_FILES[1]), mock.patch.object(sys, "dont_write_bytecode", True), \
                mock.patch.object(T, "stopped_blocks", blocks_then_an_edit):
            self.assertControl()                                       # the first check passes
            with self.assertRaises(T.Refused) as cm:
                T.run_stopped(log=QUIET, root=self.root)
        self.assertIn("changed while the record was built", cm.exception.args[0][0])
        self.assertFalse(os.path.exists(out))
        self.assertFalse(os.path.exists(out + ".partial"))
        self.assertControl()

    def test_d_each_gate_on_the_history_in_a_copy_of_its_own(self):
        """The gates on HEAD's history: each in a fresh copy of the control (checked first), changed and committed."""
        def logp(cp):
            return os.path.join(cp, *R.ATTEMPTS_REL.split("/"))

        def committed_then_removed(rel):
            def edit(cp):
                p = os.path.join(cp, *rel.split("/"))
                with open(p, "w", encoding="utf-8", newline="\n") as fh:
                    fh.write("{}\n")
                fx.commit_all(cp, f"test: {rel} committed")
                os.remove(p)
                fx.commit_all(cp, f"test: {rel} removed")
            return edit

        def appended(entry):
            def edit(cp):
                self.append(logp(cp), json.dumps(entry, sort_keys=True) + "\n")
                fx.commit_all(cp, "test: a line appended to the attempts log")
            return edit

        def cut(cp):
            with open(logp(cp), encoding="utf-8") as fh:
                first = fh.read().splitlines(keepends=True)[0]
            with open(logp(cp), "w", encoding="utf-8", newline="\n") as fh:
                fh.write(first)
            fx.commit_all(cp, "test: the stop line cut")

        def deleted(cp):
            fx.git(cp, "rm", "-q", R.ATTEMPTS_REL)
            fx.commit_all(cp, "test: the attempts log deleted")

        roads_out = {"step": "draw", "event": "outcome", "attempt": 1, "outcome": "roads", "roads_sha": "0" * 64}
        cases = {
            "the record committed once": (committed_then_removed(T.OUT_REL),
                                          [f"{T.OUT_REL} was committed in HEAD's history"]),
            "roads.json committed once": (committed_then_removed(R.ROADS_REL),
                                          [f"{R.ROADS_REL} was committed in HEAD's history"]),
            "the stop line cut": (cut, ["does not extend the version before it", "do not end in exactly one stop"]),
            "a roads outcome": (appended(roads_out), ["holds a roads outcome"]),
            "a second non-defect stop": (appended(self.lines[1]), ["(2 such stops"]),
            "a later start": (appended({"step": "draw", "event": "start", "attempt": 2}),
                              ["do not end in exactly one stop"]),
            "the log deleted": (deleted, [f"{R.ATTEMPTS_REL} is not committed at HEAD", "was deleted in commit"]),
        }
        for i, (what, (edit, needles)) in enumerate(cases.items()):
            with self.subTest(what):
                cp = self.copy_of(self.root, f"history_{i}")
                self.assertControl(cp)
                edit(cp)
                self.assertRefused(*needles, root=cp)

    def test_e_the_log_is_read_as_draw_writes_it(self):
        """The log gates (no_roads_problems) on hand-written logs, each committed in a copy of the repository before the
        draw. The stopped attempt's logged reveals are checked again against the roads commit's hash lines and the
        log's own verdict is not taken: Jad's 2**128 and a mistyped integer pass (the controls, the first through
        every gate of stopped_problems with an origin of its own), and both right integers are refused whatever
        the log's verdict says. A line draw cannot write is refused: a log whose verdict is not the re-check; a
        reveal logged as a decimal string (the review's: both right integers, which give roads_seed), a null or none
        at all; hash lines that are not the roads commit's; another roads commit; a stop that does not follow its own
        start line (the review's interleaved order among them); start lines repeated or out of order; a coding-defect
        stop, or one that does not say, after reveals that do not match; an earlier start line draw cannot write. A
        crash after both right integers, then an attempt that stops, passes with the earlier attempt named: row 129
        (4) discloses that either person could force a stop after the reveal, and the team decides that case."""
        TF, TT_ = {"ghassan": True, "jad": False}, {"ghassan": True, "jad": True}

        def start(n, *, g=None, j=WITHHELD, matches=TF, **kw):
            line = {"step": "draw", "event": "start", "attempt": n, "kind": "REAL", "roads_commit": self.roads_commit,
                    "roads_commit_announced": self.roads_commit, "hash_lines": {"ghassan": self.h_g, "jad": self.h_j},
                    "reveal": {"ghassan": self.a_g if g is None else g, "jad": j}, "reveal_matches": matches,
                    "note": None if n == 1 else "SYNTHETIC: the defect and its fix"}
            line.update(kw)
            return line

        def outcome(n, what, **kw):
            line = {"step": "draw", "event": "outcome", "attempt": n, "outcome": what, "reason": "SYNTHETIC: by hand"}
            if what == "stop":
                line["coding_defect"] = False
            line.update(kw)
            return line

        def without(line, key):
            return {k: v for k, v in line.items() if k != key}

        def hand_log(label, lines):
            cp = self.copy_of(self.pre, label)
            p = os.path.join(cp, *R.ATTEMPTS_REL.split("/"))
            os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8", newline="\n") as fh:
                for x in lines:
                    fh.write(json.dumps(x, sort_keys=True) + "\n")
            fx.commit_all(cp, f"test: {label}, written by hand")
            return cp

        cp = hand_log("hand_withheld", [start(1), outcome(1, "stop")])
        self.own_origin(cp, "hand_withheld")
        probs, found = T.stopped_problems(root=cp)
        self.assertEqual(probs, [])
        self.assertEqual((found["attempt"], found["reveal_matches_rechecked"], found["earlier_attempts_both_matching"]),
                         (1, TF, []))
        probs, found = T.no_roads_problems(root=hand_log("hand_mistyped", [start(1, j=self.a_j + 1), outcome(1, "stop")]))
        self.assertEqual((probs, found["reveal_matches_rechecked"]), ([], TF))
        crash_then_stop = [start(1, j=self.a_j, matches=TT_), outcome(1, "crash"), start(2), outcome(2, "stop")]
        probs, found = T.no_roads_problems(root=hand_log("hand_crash_then_stop", crash_then_stop))
        self.assertEqual((probs, found["attempt"], found["earlier_attempts_both_matching"]), ([], 2, [1]))
        refused = {
            # label: (the log, what the problems say, how many there are: each case is about its own gates)
            "hand_both_right": ([start(1, j=self.a_j, matches=TT_), outcome(1, "stop")], ["logged reveals both match"], 1),
            "hand_both_right_logged_otherwise": ([start(1, j=self.a_j), outcome(1, "stop")],
                                                 ["logged reveals both match", "logged reveal_matches"], 2),
            "hand_verdict_not_the_recheck": ([start(1, matches=TT_), outcome(1, "stop")], ["logged reveal_matches"], 1),
            "hand_strings_both_right": ([start(1, g=str(self.a_g), j=str(self.a_j), matches=TT_), outcome(1, "stop")],
                                        ["logs ghassan's reveal as a str", "logs jad's reveal as a str",
                                         "logged reveal_matches"], 3),
            "hand_no_reveal": ([without(start(1, matches={"ghassan": False, "jad": False}), "reveal"), outcome(1, "stop")],
                               ["logs ghassan's reveal as a NoneType", "logs jad's reveal as a NoneType"], 2),
            "hand_null_jad": ([start(1, j=None), outcome(1, "stop")], ["logs jad's reveal as a NoneType"], 1),
            "hand_other_hash_lines": ([start(1, hash_lines={"ghassan": self.h_g, "jad": "0" * 64}), outcome(1, "stop")],
                                      ["logged hash lines are not the roads commit's"], 1),
            "hand_other_commit": ([start(1, roads_commit="0" * 40), outcome(1, "stop")],
                                  [f"not {self.roads_commit}, the one HEAD's history holds"], 1),
            "hand_a_line_between": ([start(1), {"step": "draw", "event": "note"}, outcome(1, "stop")],
                                    ["does not follow its own start line"], 1),
            "hand_interleaved": ([start(1), start(2, j=self.a_j, matches=TT_), outcome(1, "stop")],
                                 ["does not follow its own start line"], 1),
            "hand_start_twice": ([start(1), start(1), outcome(1, "stop")], ["numbered [1, 1]"], 1),
            "hand_out_of_order": ([start(2), outcome(2, "crash"), start(1), outcome(1, "stop")], ["numbered [2, 1]"], 1),
            "hand_coding_defect": ([start(1), outcome(1, "stop", coding_defect=True)], ["(0 such stops"], 1),
            "hand_coding_defect_unsaid": ([start(1), without(outcome(1, "stop"), "coding_defect")], ["(0 such stops"], 1),
            "hand_earlier_strings": ([start(1, g=str(self.a_g), j=str(self.a_j), matches=TT_), outcome(1, "crash"),
                                      start(2), outcome(2, "stop")],
                                     ["attempt 1's start line logs ghassan's reveal as a str", "attempt 1's logged"], 3),
        }
        for label, (lines, needles, count) in refused.items():
            with self.subTest(label):
                probs = T.no_roads_problems(root=hand_log(label, lines))[0]
                for n in needles:
                    self.assertTrue(any(n in p for p in probs), (n, probs))
                self.assertEqual(len(probs), count, probs)

    def test_f_the_shared_branch(self):
        """origin_problems, each case in a copy whose origin is a bare repository of its own (the shared one is left):
        the control (its GRA-test at HEAD); the stop committed and not pushed; the branch ahead of HEAD; an origin that
        cannot be read. Then the fork a review of 31 October measured: origin's GRA-test holds a drawn set (a roads.json
        stand-in and its roads outcome, committed on the roads commit), and a clone left at the roads commit runs the
        real draw (its plant work stood in) with both integers entered as 2**128. The draw lets it through, since its
        first attempt runs on the roads commit, which the branch holds: it logs a stop that is not a coding defect, and
        that log passes every log gate. stopped_problems refuses it as not pushed, and refuses it again once its stop
        is merged into the branch beside the drawn set, where HEAD is in the branch but is not its tip."""
        cp = self.copy_of(self.root, "branch_control")
        self.own_origin(cp, "branch_control")
        self.assertControl(cp)
        cp = self.copy_of(self.root, "branch_behind")
        self.own_origin(cp, "branch_behind", tip=self.roads_commit)
        self.assertEqual(self.assertRefused("is not in origin's GRA-test", root=cp)[0][:18], "the shared branch:")
        cp = self.copy_of(self.root, "branch_ahead")
        head = fx.git(cp, "rev-parse", "HEAD")
        ahead = side_commit(cp, {"NOTE.txt": b"SYNTHETIC: pushed from another clone\n"}, parents=[head],
                            message="test: a commit pushed from another clone")
        self.own_origin(cp, "branch_ahead", tip=ahead)
        self.assertRefused(f"origin's GRA-test is at {ahead}, not at HEAD {head}", root=cp)
        cp = self.copy_of(self.root, "branch_unreadable")
        fx.git(cp, "remote", "set-url", "origin", os.path.join(self.tmp, "no_such_origin.git"))
        self.assertRefused("origin's GRA-test cannot be read", root=cp)
        # the fork at the roads commit, while the shared branch holds a drawn set
        drawn = self.copy_of(self.pre, "branch_drawn")
        R.write_once(os.path.join(drawn, *R.ROADS_REL.split("/")), {"note": "TEST ONLY: a stand-in for a drawn set"})
        with open(os.path.join(drawn, *R.ATTEMPTS_REL.split("/")), "w", encoding="utf-8", newline="\n") as fh:
            for x in ({"step": "draw", "event": "start", "attempt": 1, "kind": "REAL", "roads_commit": self.roads_commit,
                       "reveal": {"ghassan": self.a_g, "jad": self.a_j}, "reveal_matches": {"ghassan": True, "jad": True}},
                      {"step": "draw", "event": "outcome", "attempt": 1, "outcome": "roads", "roads_sha": "0" * 64}):
                fh.write(json.dumps(x, sort_keys=True) + "\n")
        r1 = fx.commit_all(drawn, "synthetic R1 on the shared branch: a drawn set")
        bare = self.own_origin(drawn, "branch_drawn")
        fork = self.copy_of(self.pre, "branch_fork")
        self.own_origin(fork, None, tip=None, bare=bare)
        calls = []
        with draw_stood_in(calls):
            with self.assertRaises(R.RoadsStop) as cm:
                R.draw(str(WITHHELD), str(WITHHELD), roads_commit_announced=self.roads_commit, note=None, root=fork,
                       jobs=1)
        self.assertNotIsInstance(cm.exception, R.CodingDefect)
        self.assertEqual(calls, [])
        stop = fx.commit_all(fork, "the fork's stop, never pushed")
        self.assertEqual(T.no_roads_problems(root=fork)[0], [])            # every log gate passes in the fork
        ps = self.assertRefused(f"HEAD {stop} is not in origin's GRA-test ({r1})", root=fork)
        self.assertEqual([p[:18] for p in ps], ["the shared branch:"], ps)
        merge = side_commit(fork, {}, parents=[r1, stop], message="test: the fork merged beside the drawn set",
                            tree_of=r1)
        fx.git(fork, "push", "-q", "origin", f"{merge}:refs/heads/GRA-test")
        self.assertTrue(R.remote_state(fork, stop)[0])                     # HEAD is in the branch: not enough
        ps = self.assertRefused(f"origin's GRA-test is at {merge}, not at HEAD {stop}", root=fork)
        self.assertEqual([p[:18] for p in ps], ["the shared branch:"], ps)

    def test_z_the_committed_record_passes_the_arming_and_its_checks(self):
        """run_stopped writes the record here; validate_epa._arm_tightenings refuses it uncommitted (the arming's
        control) and takes it committed, with tightening_problems; committed and pushed, stopped_record_problems,
        test_epa_roads' check and LiveRecord's find nothing (the control), each spoiled copy is refused (the
        stopped_record_problems spoils named by the gate that must refuse them), and so is a spoiled record written in
        place, by both live checks; a roads.json beside it makes every check refuse it, and so does a shared branch
        that holds a drawn set, another log or another record, or not the record's commit; the held-out L1 R is the
        contract's 9.9 K on every EPA engine and E8's P the contract's, each with a control that moves it; every
        summary line about L1 or E8 is labelled untightened. Afterwards the route refuses for good."""
        root = self.root
        out = os.path.join(root, *T.OUT_REL.split("/"))
        with mock.patch.object(sys, "dont_write_bytecode", True):
            sha, rec = T.run_stopped(log=QUIET, root=root)

        def arm():
            ctx = {"source": types.SimpleNamespace(root=root), "contract": self.contract, "record": {}}
            return VE._arm_tightenings(ctx), ctx
        self.assertEqual(arm()[0], [f"{T.OUT_REL} is not committed and clean (the roads step comes first)"])
        stop_commit = fx.git(root, "rev-parse", "HEAD")
        record_commit = fx.commit_all(root, "synthetic R3b: the no-roads tightenings record (row 129 (4))")
        good = common.load_json(out)
        self.assertTrue(any("the shared branch does not hold the record's commit" in p
                            for p in T.stopped_record_problems(good, root=root)))        # committed, not pushed
        self.push()
        probs, ctx = arm()
        self.assertEqual(probs, [])
        self.assertEqual((ctx["record"]["tightenings"]["sha_text"], ctx["record"]["tightenings"]["plant"]), (sha, "b58"))
        t = VE.load_tightenings(out)
        self.assertEqual(VE.tightening_problems(t, self.contract, b58=VE.b58_identity()), [])
        good = common.load_json(out)
        import test_epa_roads as TR
        self.assertEqual(T.stopped_record_problems(good, root=root), [])              # the control
        self.assertEqual(TR.tightenings_problems(root), [])                            # test_epa_roads.Tightenings'
        self.assertEqual(live_record_problems(root), [])                               # LiveRecord's
        spoils = {
            "seed_kind REAL": lambda d: d.update(seed_kind="REAL"),
            "seed_kind SYNTHETIC": lambda d: d.update(seed_kind="SYNTHETIC"),
            "a roads_sha": lambda d: d.update(roads_sha="0" * 64),
            "roads_seed 0": lambda d: d.update(roads_seed=0),
            "roads_seed -1.0": lambda d: d.update(roads_seed=-1.0),
            "L1 tightened": lambda d: d["L1"].update(slope_points_per_K=1.5 * d["L1"]["slope_points_per_K"]),
            "another set": lambda d: d["L1"].update(set="SYNTHETIC roads"),
            "another shift": lambda d: d["L1"].update(shift_k=d["L1"]["shift_k"] + 1.0),
            "another reading": lambda d: d["L1"].update(damage_reading="edited"),
            "L1 marked tightened": lambda d: d["L1"].update(tightened=True),
            "no L1 label": lambda d: d["L1"].pop("label"),
            "an E8 change moved": lambda d: d["E8"][T.ROADS_KEYS["lambda"]][0].__setitem__(1, 0.0),
            "an E8 shift dropped": lambda d: d["E8"][T.ROADS_KEYS["spark"]].pop(),
            "E8 marked tightened": lambda d: d["E8"].update(tightened=True),
            "another band": lambda d: d["E8"]["b58_u_val_kappa"]["with_roads"].update(E_pct=0.0),
            "another stop": lambda d: d["no_roads"]["stop"].update(reason="edited"),
            "another re-check": lambda d: d["no_roads"].update(reveal_matches_rechecked={"ghassan": True, "jad": True}),
            "another log": lambda d: d["no_roads"].update(attempts_sha_text="0" * 64),
            "dirty code": lambda d: d["provenance"]["git"].update(code_clean=False),
            "a compiled file": lambda d: d["provenance"]["git"].update(bytecode_caches=["__pycache__/plant.pyc"]),
            "another plant": lambda d: d["provenance"].update(plant_sha="4580f7ffdfad7a16"),
            "an unknown commit": lambda d: d["provenance"].update(commit="0" * 40),
            "another code hash": lambda d: d["provenance"]["code_sha_text"].update({T.MODULE_REL: "0" * 64}),
        }
        for what, edit in spoils.items():
            bad = copy.deepcopy(good)
            edit(bad)
            self.assertNotEqual(T.stopped_record_problems(bad, root=root), [], what)
        # spoils each gate must refuse by itself: the needle is that gate's
        outside = side_commit(root, {}, parents=[], message="test: a commit outside the history", tree_of="HEAD")
        band_both = (lambda d: [d["E8"]["b58_u_val_kappa"][k].update(E_pct=0.0, kappa=1.0)
                                for k in ("with_roads", "locked_climb_only")])
        named = {
            "another schema": (lambda d: d.update(schema="epa-tightenings/0"), "schema is 'epa-tightenings/0'"),
            "another plant name": (lambda d: d.update(plant="mazda_25t"), "plant is 'mazda_25t'"),
            "another top-level label": (lambda d: d.update(untightened="tightened on the roads"),
                                        "untightened is 'tightened on the roads'"),
            "no top-level label": (lambda d: d.pop("untightened"), "untightened is None"),
            "an int shift": (lambda d: d["L1"].update(shift_k=int(d["L1"]["shift_k"])), "L1.shift_k is 57,"),
            "both band readings alike": (band_both, "E8.b58_u_val_kappa is not b58_band's"),
            "the model-minus-car reading": (
                lambda d: d["E8"]["b58_u_val_kappa"]["model_minus_car"]["with_roads"].update(kappa=99.0),
                "E8.b58_u_val_kappa is not b58_band's"),
            "another roads commit": (lambda d: d["no_roads"].update(roads_commit="0" * 40), "no_roads.roads_commit is"),
            "another attempt": (lambda d: d["no_roads"].update(attempt=2), "no_roads.attempt is"),
            "another start commit": (lambda d: d["no_roads"].update(start_commit="0" * 40), "no_roads.start_commit is"),
            "another logged verdict": (lambda d: d["no_roads"].update(reveal_matches_logged={"ghassan": True, "jad": True}),
                                       "no_roads.reveal_matches_logged is"),
            "an earlier attempt named": (lambda d: d["no_roads"].update(earlier_attempts_both_matching=[1]),
                                         "no_roads.earlier_attempts_both_matching is"),
            "an earlier attempt unsaid": (lambda d: d["no_roads"].pop("earlier_attempts_both_matching"),
                                          "no_roads.earlier_attempts_both_matching is"),
            "provenance at the roads commit": (lambda d: d["provenance"].update(commit=self.roads_commit),
                                               f"{R.ATTEMPTS_REL} at provenance.commit is not the log the record names"),
            "a commit outside the history": (lambda d: d["provenance"].update(commit=outside),
                                             "is not an ancestor of the record's commit"),
        }
        for what, (edit, needle) in named.items():
            bad = copy.deepcopy(good)
            edit(bad)
            ps = T.stopped_record_problems(bad, root=root)
            self.assertEqual(len(ps), 1, (what, ps))
            self.assertIn(needle, ps[0], what)
        # a log that is neither the one in the tree nor the one at provenance.commit: both checks say so
        bad = copy.deepcopy(good)
        bad["no_roads"]["attempts_sha_text"] = "0" * 64
        ps = T.stopped_record_problems(bad, root=root)
        self.assertEqual(len(ps), 2, ps)
        self.assertTrue(any("no_roads.attempts_sha_text is not the committed attempts log's" in p for p in ps), ps)
        self.assertTrue(any(f"{R.ATTEMPTS_REL} at provenance.commit is not the log the record names" in p
                            for p in ps), ps)
        # a spoiled record written in place: both live checks refuse it, and take the record back
        with open(out, "rb") as fh:
            keep = fh.read()
        try:
            with open(out, "w", encoding="utf-8", newline="\n") as fh:
                fh.write(json.dumps(dict(good, seed_kind="SYNTHETIC"), indent=1) + "\n")
            self.assertTrue(any("seed_kind is 'SYNTHETIC'" in p for p in TR.tightenings_problems(root)))
            self.assertTrue(any("seed_kind is 'SYNTHETIC'" in p for p in live_record_problems(root)))
        finally:
            with open(out, "wb") as fh:
                fh.write(keep)
        self.assertEqual((TR.tightenings_problems(root), live_record_problems(root)), ([], []))
        # the shared branch: each case a copy whose origin's GRA-test is set by hand (origin_record_problems)
        with open(os.path.join(root, *R.ATTEMPTS_REL.split("/")), "rb") as fh:
            log_bytes = fh.read().replace(b"\r\n", b"\n")
        branches = {
            "the record's commit": (lambda cp: record_commit, None),
            "a drawn set merged in": (
                lambda cp: side_commit(cp, {}, parents=[record_commit, side_commit(
                    cp, {R.ROADS_REL: b'{"note": "TEST ONLY: a drawn set"}\n'}, parents=[record_commit],
                    message="test: a set drawn elsewhere")], message="test: merged, its tree the record's",
                    tree_of=record_commit),
                f"holds {R.ROADS_REL} in its history"),
            "a line more in its log": (
                lambda cp: side_commit(cp, {R.ATTEMPTS_REL: log_bytes + b'{"event": "note", "step": "draw"}\n'},
                                       parents=[record_commit], message="test: the log extended elsewhere"),
                f"{R.ATTEMPTS_REL} at origin's GRA-test"),
            "another record": (
                lambda cp: side_commit(cp, {T.OUT_REL: keep.replace(b"\r\n", b"\n") + b"\n"}, parents=[record_commit],
                                       message="test: the record edited elsewhere"),
                f"{T.OUT_REL} at origin's GRA-test"),
            "the stop, not the record": (lambda cp: stop_commit, "the shared branch does not hold the record's commit"),
        }
        for i, (what, (tip_of, needle)) in enumerate(branches.items()):
            with self.subTest(what):
                cp = self.copy_of(root, f"record_branch_{i}")
                self.own_origin(cp, f"record_branch_{i}", tip=tip_of(cp))
                ps = T.stopped_record_problems(good, root=cp)
                if needle is None:
                    self.assertEqual(ps, [])
                else:
                    self.assertEqual(len(ps), 1, ps)
                    self.assertIn(needle, ps[0])
        # a roads.json beside it: no check takes the no-roads record
        stray = os.path.join(root, *R.ROADS_REL.split("/"))
        with open(stray, "w", encoding="utf-8", newline="\n") as fh:
            json.dump({"commit_reveal": {"roads_seed": 1}, "note": "TEST ONLY"}, fh)
        try:
            self.assertTrue(any(f"{R.ROADS_REL} exists" in p for p in T.stopped_record_problems(good, root=root)))
            self.assertNotEqual(TR.tightenings_problems(root), [])
            self.assertTrue(any("seed_kind is 'NONE', not 'REAL'" in p for p in live_record_problems(root)))
        finally:
            os.remove(stray)
        self.assertEqual(live_record_problems(root), [])
        # the held-out effect, as validate_epa run hands epa_stats the raw record
        strategy, b = self.contract["ecu_strategy_b58"], float(self.contract["budget"]["b_points"])
        for eng in R.EPA_ENGINES:
            rmap = {x["row"]: (x["R"], x["unit"]) for x in self.contract["thresholds"] if x.get("engine") == eng}
            view = types.SimpleNamespace(R=rmap, b_points=b, ecu_strategy_b58=strategy)
            held = ES._R(view, "L1", "held_out", t.raw)
            self.assertEqual(held, ES._R(view, "L1", "in_sample", None), eng)
            self.assertEqual(held[0], 9.9, eng)
            ctrl = copy.deepcopy(t.raw)
            ctrl["L1"]["slope_points_per_K"] = 0.1                                     # a tightening moves R
            self.assertLess(ES._R(view, "L1", "held_out", ctrl)[0], held[0], eng)
        view = types.SimpleNamespace(ecu_strategy_b58=strategy)
        self.assertEqual(ES.e8_response(view, tightening=t.raw), ES.e8_response(view, tightening=None))
        ctrl = copy.deepcopy(t.raw)
        ctrl["E8"][T.ROADS_KEYS["lambda"]] = [[s, 2.0 * c] for s, c in ctrl["E8"][T.ROADS_KEYS["lambda"]]]
        self.assertNotEqual(ES.e8_response(view, tightening=ctrl), ES.e8_response(view, tightening=None))
        # every printed summary labels L1 and E8 untightened, the command line's among them
        about = [x for x in T.summary_lines(good) if "L1" in x or "E8" in x]
        self.assertGreaterEqual(len(about), 4)
        self.assertTrue(all(T.UNTIGHTENED in x for x in about), about)
        with mock.patch.object(T, "run_stopped", lambda *, log, root=T.REPO: (sha, good)), \
                contextlib.redirect_stdout(io.StringIO()) as buf:
            self.assertEqual(T.main(["stopped"]), 0)
        printed = [x for x in buf.getvalue().splitlines() if "L1" in x or "E8" in x]
        self.assertGreaterEqual(len(printed), 5)
        self.assertTrue(all(T.UNTIGHTENED in x for x in printed), printed)
        with mock.patch.object(T, "run_stopped", side_effect=T.Refused(["a gate"])), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(T.main(["stopped"]), 2)
        # the route has ended: the record exists and was committed
        self.assertRefused(f"{T.OUT_REL} exists: it is written once", f"{T.OUT_REL} was committed in HEAD's history")
        os.remove(out)
        fx.commit_all(root, "test: the record deleted")
        self.push()
        self.assertEqual(self.probs(), [f"{T.OUT_REL} was committed in HEAD's history: the tightenings are measured once"])


def live_record_problems(root):
    """LiveRecord's check of results/EPA_TIGHTENINGS.json under `root`, [] when it holds; None while it is absent.
    With roads.json, the real run's record (committed_record_problems); without it, row 129 (4)'s no-roads record
    (epa_tightenings.stopped_record_problems); no other record either way."""
    path = os.path.join(root, *T.OUT_REL.split("/"))
    if not os.path.exists(path):
        return None
    t = common.load_json(path)
    if os.path.exists(os.path.join(root, *R.ROADS_REL.split("/"))):
        return committed_record_problems(t, root=root)
    return T.stopped_record_problems(t, root=root)


class LiveRecord(unittest.TestCase):
    """Live once results/EPA_TIGHTENINGS.json exists (ORDER step 8's record; run it in step 9's rehearsal beside
    test_epa_roads): with roads.json the committed record is the real run's (committed_record_problems; its control
    and spoiled copies are RealGates.test_z's), without it row 129 (4)'s no-roads record (stopped_record_problems;
    StoppedRoute.test_z's), and no other (live_record_problems). Skips while the record is absent."""

    def test_the_committed_record_is_the_real_runs_or_the_no_roads_one(self):
        probs = live_record_problems(HERE)
        if probs is None:
            self.skipTest(f"{T.OUT_REL} is absent: ORDER step 8 has not run")
        self.assertEqual(probs, [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
