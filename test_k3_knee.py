"""test_k3_knee.py -- the K3 knee, the neutral run, its identity and the delivery check, on the B58.

    python -B test_k3_knee.py        about eight minutes (six B58 climbs, one synthetic candidate's
                                     table and climb); exit code 0 when all pass

Build step 2, WP3 (23 October 2026): docs/build_step_2/PLAN.md section 7.7, WP3_INTERFACES.md
section 9.7. The B58 runs here, which is not EPA data: no EPA table, no contract JSON, no log is
opened (every class runs inside forbid_real_data), and no number is printed.

  Knee        baseline_trace + knee_for, under shifted_ecu exactly as thresholds/ecu_shift.py:70-78,
              give results/ENGINE_THRESHOLDS/ecu/k3_lam-0.02.json's and k3_spark-0.75.json's knee_k
              back bit for bit, with their 413 s and their three trace figures; the nominal trace
              spends k3_nominal.json's time_above_nominal_s, 413 s, above 1123 K. Controls: the
              unshifted trace gives another knee (the shift reached the trace), a knee 1 K higher
              another count, and ecu_shift's rule on a toy array with its two end cases
  K3          k3() reads the knee off the nominal trace and a second provisional knee gives the
              trace back bit for bit. Controls: a one-ulp change is seen, and k3 reports False when
              its second run hands back such a trace; equal knees, a NumPy knee and seconds
              without a midpoint are refused
  Neutral     neutral_run's trace is baseline_trace's bit for bit (the instance wrappers change
              nothing) and its ECU wrapper saw one call per step; the identity reads 0 and 0 with
              Python-float bounds and no contact. On this climb the float32 definition is load-
              bearing on spark (no spark_b is float32-exact) and not on lambda (lambda_b is 1.0 at
              every step). Controls (mistake 12): at a binding step, lambda_b exactly on the B58's
              floor 0.7, the identity reads no difference and no contact, where a float64
              difference would read one and a NumPy float64 bound would count a contact (MD
              section 4); each of the four bounds as a float64 is refused before the count; an
              agent lambda one part in a million off, a spark 0.25 deg off and trims the clips
              bind on are each seen
  Stops       neutral_run stops at the first step when an ECU call reaches the class past the
              instance wrapper (WP3_INTERFACES.md section 11), when the gearbox is called twice,
              and when its tracking error is not the environment's; a NaN knee is refused first
  Delivery    the B58 holds 7th over the 531 steps at t >= 188 s, below its shift ceiling, its 8th
              rejected above its own, its 6th not barred; 188 s is where the climb's ramp ends.
              Controls: from t 0 the launch's gears appear; a tracking error moved past TRACK_TOL
              is counted
  CVT         on a SYNTHETIC candidate (the B58's derived values on the Honda's specs and the
              Accord's CVT, its table measured through it): the run records the CVT's branches, its
              box state is a fresh ratio_for's at every step checked, the identity holds where
              lambda_b is not float32-exact, and delivery reports the kickdown margin and no bar
  Driveline   with_driveline_eff moves the demand as 1/eta, and refuses a NumPy eta

Each control is a case that must fail the check, and does (mistake 12).
"""
import dataclasses
import json
import math
import os
import sys
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import evaluate as V  # noqa: E402
import k3_knee as K  # noqa: E402
from test_epa_fixtures import Guarded, forbid_real_data  # noqa: E402  (WP3_INTERFACES.md 9.1)

ECU_DIR = os.path.join(HERE, "results", "ENGINE_THRESHOLDS", "ecu")


def _k3_file(name):
    with open(os.path.join(ECU_DIR, f"k3_{name}.json"), encoding="utf-8") as fh:
        return json.load(fh)


_CACHE = {}


def _plant():
    return engines.get("b58")


def _nominal():
    """The B58's nominal trace, run once per process and shared by the classes below."""
    if "nominal" not in _CACHE:
        _CACHE["nominal"] = K.baseline_trace(_plant())
    return _CACHE["nominal"]


class Guard(unittest.TestCase):
    def test_the_guard_fails_an_open_of_a_real_table_path(self):
        """Control of the guard these classes run in: an open, inside it, of a path where a real EPA
        table would be fails the block, whether the guard refuses the open or reports it on leaving;
        the probe does not exist, so without the guard the file system's FileNotFoundError, caught
        here, would leave nothing to fail."""
        probe = os.path.join(HERE, "data", "engines", "_probe", "epa_" + "probe.csv")
        with self.assertRaises(Exception) as cm:
            with forbid_real_data():
                try:
                    open(probe, encoding="utf-8").close()
                except FileNotFoundError:
                    pass
        self.assertNotIsInstance(cm.exception, FileNotFoundError)


class KneeOnTheB58(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = _plant()
        cls.files = {n: _k3_file(n) for n in ("nominal", "lam-0.02", "spark-0.75")}
        cls.nominal = _nominal()
        cls.shifted = {}
        for name, ds, dl in (("lam-0.02", 0.0, -0.02), ("spark-0.75", -0.75, 0.0)):
            f = cls.files[name]
            assert (f["dspark"], f["dlambda"]) == (ds, dl), name
            with K.shifted_ecu(ds, dl):
                cls.shifted[name] = K.baseline_trace(cls.plant)
        cls.seconds = cls.files["nominal"]["time_above_nominal_s"]

    def test_the_nominal_trace_spends_413_s_above_1123_k(self):
        f = self.files["nominal"]
        self.assertEqual(self.plant.engine.damage.turb_knee_k, 1123.0)
        self.assertEqual(f["knee_k"], 1123.0)
        self.assertEqual(self.seconds, 413)
        self.assertEqual(int((self.nominal.t_turb_k > 1123.0).sum()), self.seconds)
        self.assertEqual(len(self.nominal.t_turb_k), 719)
        for key, value in K.medians(self.nominal).items():
            self.assertEqual(value, f[key], key)
        # control: a knee 1 K higher has another count, so the 413 is the trace's, not a constant
        self.assertNotEqual(int((self.nominal.t_turb_k > 1124.0).sum()), self.seconds)

    def test_the_shifted_traces_give_the_contracts_knees_back(self):
        for name, tr in self.shifted.items():
            f = self.files[name]
            knee = K.knee_for(tr.t_turb_k, self.seconds)
            self.assertEqual(knee, f["knee_k"], name)                   # bit for bit
            self.assertEqual(int((tr.t_turb_k > knee).sum()), f["time_above_knee_s"], name)
            self.assertEqual(f["time_above_knee_s"], self.seconds)
            for key, value in K.medians(tr).items():
                self.assertEqual(value, f[key], (name, key))

    def test_the_shift_reached_the_trace(self):
        """Control: the unshifted trace's knee is neither shifted file's, so the patch moved what
        the knee is read off (mistake 25)."""
        k0 = K.knee_for(self.nominal.t_turb_k, self.seconds)
        for name in self.shifted:
            self.assertNotEqual(k0, self.files[name]["knee_k"], name)
            self.assertFalse(K.traces_identical(self.nominal, self.shifted[name]), name)

    def test_the_patch_is_restored_and_does_not_stack(self):
        self.assertIs(E.BaselineECU.step, K._ECU_STEP)
        with K.shifted_ecu(0.0, -0.02):
            self.assertIsNot(E.BaselineECU.step, K._ECU_STEP)
            with self.assertRaises(RuntimeError):
                with K.shifted_ecu(0.0, 0.01):
                    pass
        self.assertIs(E.BaselineECU.step, K._ECU_STEP)
        with self.assertRaises(ValueError):
            with K.shifted_ecu(0.0, -0.02):
                raise ValueError("inside")
        self.assertIs(E.BaselineECU.step, K._ECU_STEP)
        with self.assertRaises(TypeError):
            with K.shifted_ecu(np.float64(0.0), -0.02):
                pass

    def test_the_patch_acts_above_100_kpa_only(self):
        """The shift is ecu_shift's: spark clipped to the ECU's range, lambda moved, only while the
        ECU's own load input is above ECU_LOAD_KPA; below it the step is the original's."""
        cal = self.plant.engine.ecu
        args = (2700.0, None, 330.0, 366.0, False, 1.0)
        for map_kpa, moved in ((150.0, True), (100.0, False), (60.0, False)):
            a = (args[0], map_kpa) + args[2:]
            base = E.BaselineECU(cal).step(*a)
            with K.shifted_ecu(-0.75, -0.02):
                got = E.BaselineECU(cal).step(*a)
            if moved:
                self.assertEqual(got[0], float(np.clip(base[0] - 0.75, cal.spark_min, cal.spark_max)))
                self.assertEqual(got[1], base[1] - 0.02)
            else:
                self.assertEqual(got, base)

    def test_knee_for_is_ecu_shifts_rule(self):
        s = np.array([1.0, 5.0, 3.0, 2.0, 4.0])
        self.assertEqual(K.knee_for(s, 2), 3.5)        # the 2nd and 3rd highest, 4 and 3
        self.assertEqual(K.knee_for(s, 0), 5.0)        # ecu_shift's end cases, kept as they were
        self.assertEqual(K.knee_for(s, 5), 1.0)
        self.assertEqual(int((s > K.knee_for(s, 2)).sum()), 2)
        with self.assertRaises(TypeError):
            K.knee_for(self.nominal, 413)


class K3OnTheB58(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = _plant()
        cls.nominal = _nominal()
        cls.seconds = _k3_file("nominal")["time_above_nominal_s"]
        cls.k3 = K.k3(cls.plant, seconds=cls.seconds, provisional=(1123.0, 1250.0))

    def test_k3_reads_the_knee_off_the_nominal_trace(self):
        k = self.k3
        self.assertEqual(k.seconds, 413)
        self.assertEqual(k.knee_k, K.knee_for(self.nominal.t_turb_k, 413))
        self.assertEqual(k.time_above_knee_s, 413)
        self.assertEqual(k.trace_sha256, K.trace_sha256(self.nominal))
        self.assertTrue(k.second_knee_identical)
        # the B58's K3 knee sits between its 413th and 414th highest housing temperatures, where
        # its typed 1123 K also sits: both leave 413 s above
        s = np.sort(self.nominal.t_turb_k)[::-1]
        self.assertTrue(s[413] < k.knee_k < s[412] and s[413] < 1123.0 < s[412])
        self.assertEqual(set(k.as_json()), {"seconds", "knee_k", "time_above_knee_s", "trace_sha256",
                                            "second_knee_identical"})

    def test_the_second_knee_check_can_fail(self):
        """Control: one ulp in one value of a trace is seen; and what would make the check vacuous
        or the knee undefined is refused."""
        t2 = self.nominal.t_turb_k.copy()
        t2[500] = math.nextafter(t2[500], math.inf)
        other = K.BaselineTrace(t2, self.nominal.lam, self.nominal.spark)
        self.assertFalse(K.traces_identical(self.nominal, other))
        self.assertNotEqual(K.trace_sha256(self.nominal), K.trace_sha256(other))
        self.assertTrue(K.traces_identical(self.nominal, K.BaselineTrace(self.nominal.t_turb_k.copy(),
                                                                         self.nominal.lam, self.nominal.spark)))
        for bad, exc in (((1123.0, 1123.0), ValueError), ((np.float64(1123.0), 1250.0), TypeError),
                         ((1123.0, float("nan")), ValueError), ((1123.0,), ValueError)):
            with self.assertRaises(exc):
                K.k3(self.plant, seconds=413, provisional=bad)
        with self.assertRaises(TypeError):
            K.k3(self.plant, seconds=413.0, provisional=(1123.0, 1250.0))

    def test_the_second_knee_flag_reads_the_second_run(self):
        """Control (mistake 12): k3's second_knee_identical is False when the second run differs.
        baseline_trace is replaced, for this test only (unittest.mock; no file is edited), by one
        that records the knee of the plant it is given and hands back the nominal trace, then that
        trace with one value one ulp up. k3 runs the two provisional knees in order, reports
        False, and reads the knee off the first trace."""
        t2 = self.nominal.t_turb_k.copy()
        t2[500] = math.nextafter(t2[500], math.inf)
        traces = (self.nominal, K.BaselineTrace(t2, self.nominal.lam, self.nominal.spark))
        knees = []

        def fake(plant):
            knees.append(plant.engine.damage.turb_knee_k)
            return traces[len(knees) - 1]
        with mock.patch.object(K, "baseline_trace", fake):
            k = K.k3(self.plant, seconds=self.seconds, provisional=(1123.0, 1250.0))
        self.assertEqual(knees, [1123.0, 1250.0])
        self.assertFalse(k.second_knee_identical)
        self.assertEqual(k.knee_k, self.k3.knee_k)
        self.assertEqual(k.trace_sha256, self.k3.trace_sha256)

    def test_with_knee(self):
        p = K.with_knee(self.plant, 1200.0)
        self.assertEqual(p.engine.damage.turb_knee_k, 1200.0)
        self.assertEqual(dataclasses.replace(p.engine.damage, turb_knee_k=1123.0), self.plant.engine.damage)
        self.assertEqual(self.plant.engine.damage.turb_knee_k, 1123.0)      # the plant passed is unchanged
        for bad, exc in ((np.float64(1200.0), TypeError), (float("nan"), ValueError), (1200, TypeError)):
            with self.assertRaises(exc):
                K.with_knee(self.plant, bad)
        nan = dataclasses.replace(self.plant, engine=dataclasses.replace(
            self.plant.engine, damage=dataclasses.replace(self.plant.engine.damage, turb_knee_k=float("nan"))))
        with self.assertRaises(ValueError):           # refused before an episode that would end at once
            K.baseline_trace(nan)


class NeutralRunOnTheB58(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = _plant()
        cls.nominal = _nominal()
        seed, w = V.EPISODES[0]
        cls.cycle = V.episode_cycle(None, plant=cls.plant)
        cls.neutral = K.neutral_run(cls.plant, cycle=cls.cycle, seed=seed, weights=w)

    def test_the_wrappers_change_nothing(self):
        self.assertTrue(K.traces_identical(self.neutral.trace(), self.nominal))
        self.assertEqual(self.neutral.steps, 719)
        self.assertEqual(self.neutral.ecu_calls, self.neutral.steps)
        self.assertEqual(self.neutral.act.dtype, np.float32)
        self.assertTrue(np.all(self.neutral.act[:, :3] == 0.0))      # the neutral trims, exactly 0.0
        self.assertEqual(self.neutral.t[0], 0.0)
        self.assertEqual(self.neutral.t[-1], 718.0)

    def test_the_identity_reads_zero_and_zero(self):
        idt = K.neutral_identity(self.neutral, ecu=self.plant.engine.ecu)
        self.assertEqual(idt.max_abs_dlam, 0.0)
        self.assertEqual(idt.max_abs_dspark, 0.0)
        self.assertEqual((idt.contacts_lam, idt.contacts_spark), (0, 0))
        self.assertTrue(idt.bounds_are_python_floats)
        self.assertEqual(idt.steps, 719)
        self.assertTrue(idt.holds)
        self.assertEqual(set(idt.as_json()), {"max_abs_dlam", "max_abs_dspark", "contacts_lam",
                                              "contacts_spark", "bounds_are_python_floats", "steps"})
        # The float32 definition is load-bearing on this run's spark: no spark_b is float32-exact,
        # so an identity taken in float64 would read a difference. Its lambda_b is float32-exact at
        # every step (1.0 throughout: the B58's ECU does not enrich on this climb), so that channel
        # cannot tell float32 from float64 here; the binding-step test below shows it can.
        n = self.neutral
        self.assertGreater(float(np.max(np.abs(n.spark - n.spark_b))), 0.0)
        self.assertTrue(np.all(n.lam_b.astype(np.float32).astype(np.float64) == n.lam_b))

    def test_a_float64_bound_counts_a_contact_at_a_binding_step(self):
        """MD section 4: at a step where the baseline's lambda sits exactly on the floor, the
        float32 sum equals float32(lam_floor), which is below 0.7 in float64. The environment's
        comparison, against a Python-float bound, is float32 and sees no contact; a NumPy float64
        bound would make it float64 and count one. neutral_identity refuses such a bound first."""
        ecu = self.plant.engine.ecu
        floor = ecu.lam_floor
        self.assertNotEqual(float(np.float32(floor)), floor)      # 0.7 is not float32-exact
        i = 400
        lam_b = self.neutral.lam_b.copy()
        lam = self.neutral.lam.copy()
        lam_b[i], lam[i] = floor, float(np.float32(floor))
        binding = dataclasses.replace(self.neutral, lam_b=lam_b, lam=lam)
        idt = K.neutral_identity(binding, ecu=ecu)
        self.assertEqual((idt.contacts_lam, idt.max_abs_dlam), (0, 0.0))
        self.assertGreater(abs(lam[i] - lam_b[i]), 0.0)             # in float64 the two differ
        x = lam_b.astype(np.float32) + binding.act[:, 1]
        self.assertEqual(K.clip_contacts(x, floor, ecu.lam_ceiling), 0)
        self.assertEqual(K.clip_contacts(x, np.float64(floor), np.float64(ecu.lam_ceiling)), 1)
        # each of the four bounds as a NumPy float64 is refused by neutral_identity itself, before
        # the count (EcuCal checks none of the four's type, engines.py; the message is the check's)
        for name in ("lam_floor", "lam_ceiling", "spark_min", "spark_max"):
            bad = dataclasses.replace(ecu, **{name: np.float64(getattr(ecu, name))})
            with self.assertRaisesRegex(TypeError, f"{name}.*not Python floats"):
                K.neutral_identity(binding, ecu=bad)

    def test_the_identity_can_fail(self):
        """Controls: a lambda one part in a million off at one step, a spark off at another, and a
        lambda trim of -1 that the floor clips, are each seen."""
        ecu = self.plant.engine.ecu
        lam = self.neutral.lam.copy()
        lam[300] = lam[300] * (1.0 + 1e-6)
        spark = self.neutral.spark.copy()
        spark[350] = spark[350] + 0.25
        idt = K.neutral_identity(dataclasses.replace(self.neutral, lam=lam, spark=spark), ecu=ecu)
        self.assertGreater(idt.max_abs_dlam, 0.0)
        self.assertEqual(idt.max_abs_dspark, 0.25)
        self.assertFalse(idt.holds)
        act = self.neutral.act.copy()
        act[300, 1] = np.float32(-1.0)
        act[310, 0] = np.float32(100.0)
        idt = K.neutral_identity(dataclasses.replace(self.neutral, act=act), ecu=ecu)
        self.assertEqual((idt.contacts_lam, idt.contacts_spark), (1, 1))
        self.assertFalse(idt.holds)

    def test_delivery_reports_the_7th_gear_over_the_climb(self):
        self.assertEqual(K.full_grade_from_s(self.cycle), K.T_FROM_S)
        d = K.delivery(self.neutral, plant=self.plant, t_from_s=K.T_FROM_S)
        self.assertEqual(d.steps, 531)                             # t 188-718 s
        self.assertEqual(d.held, {"box": "stepped", "counts": {"7": 531}})
        m = d.margin_to_threshold
        self.assertLess(m["held"]["max"], 0.0)                     # 7th's demand under its ceiling
        self.assertEqual(m["held_lowest_steps"], 0)
        self.assertGreater(m["rejected_higher"], 0.0)              # 8th's above its own
        self.assertEqual(m["rejected_higher_steps"], 531)
        self.assertLess(d.bar_rpm_margin["fraction"]["max"], 0.0)  # 6th would turn under 6000 rpm
        self.assertEqual(d.bar_rpm_margin["barred_steps"], 0)
        self.assertTrue(0.0 <= d.share_over_track_tol <= 1.0)
        self.assertGreaterEqual(d.map_vs_ceiling_kpa["min"], 0.0)
        # the held gear is the one engine speed and road speed give (step_record.gear's reading)
        i = int(np.flatnonzero(self.neutral.t >= K.T_FROM_S)[0])
        wheel_rpm = self.neutral.v_mps[i] / self.plant.car.wheel_r * 60.0 / (2 * np.pi)
        ratios = np.asarray(self.plant.car.gears) * self.plant.car.final_drive
        self.assertEqual(int(np.argmin(np.abs(ratios - self.neutral.rpm[i] / wheel_rpm))) + 1, 7)
        # the request the environment computed is the held gear's demand
        on_climb = self.neutral.t >= K.T_FROM_S
        self.assertEqual(d.demand_nm["median"], float(np.median(self.neutral.torque_req[on_climb])))
        json.dumps(d.as_json(), allow_nan=False)                    # a record complete.json can hold

    def test_the_delivery_population_reaches_the_report(self):
        """Controls: from t 0 the launch's lower gears are in the counts; a tracking error moved
        past TRACK_TOL on every step is counted on every step."""
        d0 = K.delivery(self.neutral, plant=self.plant, t_from_s=0.0)
        self.assertEqual(d0.steps, 719)
        self.assertGreater(len(d0.held["counts"]), 1)
        late = dataclasses.replace(self.neutral, e_track=self.neutral.e_track + 2.0 * E.TRACK_TOL)
        self.assertEqual(K.delivery(late, plant=self.plant, t_from_s=K.T_FROM_S).share_over_track_tol, 1.0)
        with self.assertRaises(ValueError):
            K.delivery(self.neutral, plant=self.plant, t_from_s=1000.0)
        with self.assertRaises(TypeError):
            K.delivery(self.neutral, plant=self.plant, t_from_s=188)


class NeutralRunStops(Guarded):
    """Controls (mistake 12) of neutral_run's own stops, each on a subclass of the environment put
    in for one test (unittest.mock replaces engine_env's name while the block runs and restores it;
    no file and no class of engine_env is edited, amendment B5). Each stops at the first step; the
    unpatched run passes the same stops (NeutralRunOnTheB58 runs it whole)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = _plant()
        cls.seed, cls.w = V.EPISODES[0]
        cls.cycle = V.episode_cycle(None, plant=cls.plant)

    def _stops(self, env_class, pattern):
        base = E.SupervisoryTunerEnv
        with self.assertRaisesRegex(RuntimeError, pattern):
            with mock.patch.object(E, "SupervisoryTunerEnv", env_class):
                K.neutral_run(self.plant, cycle=self.cycle, seed=self.seed, weights=self.w)
        self.assertIs(E.SupervisoryTunerEnv, base)

    def test_an_ecu_call_the_wrapper_does_not_see_stops_the_run(self):
        """WP3_INTERFACES.md section 11's case: the step reaches BaselineECU.step through the class,
        not through the instance attribute the wrapper is, so the wrapper sees no call; the run
        stops and says the identity would need a plant change."""
        class AroundTheWrapper(E.SupervisoryTunerEnv):
            def step(self, action):
                w = self.ecu.__dict__.pop("step")
                try:
                    return super().step(action)
                finally:
                    self.ecu.step = w
        self._stops(AroundTheWrapper, r"\(0, 1, 2, 1\).*plant change")

    def test_an_extra_gearbox_call_stops_the_run(self):
        class Extra(E.SupervisoryTunerEnv):
            def step(self, action):
                out = super().step(action)
                self.veh.gear_for(self.v)
                return out
        self._stops(Extra, r"\(1, 2, 2, 1\)")

    def test_a_tracking_error_that_drifted_from_the_environments_stops_the_run(self):
        class Drift(E.SupervisoryTunerEnv):
            def step(self, action):
                obs, r, term, trunc, info = super().step(action)
                info["r_resp"] = info["r_resp"] - 1e-9
                return obs, r, term, trunc, info
        self._stops(Drift, "e_track changed")

    def test_a_nan_knee_is_refused_before_the_episode(self):
        nan = dataclasses.replace(self.plant, engine=dataclasses.replace(
            self.plant.engine, damage=dataclasses.replace(self.plant.engine.damage, turb_knee_k=float("nan"))))
        with self.assertRaisesRegex(ValueError, "provisional finite knee"):
            K.neutral_run(nan, cycle=self.cycle, seed=self.seed, weights=self.w)


class CvtOnASyntheticCandidate(Guarded):
    """The CVT path (the Accord's box, engine_env.CvtVehicle), which no B58 run reaches, on a
    SYNTHETIC candidate: engines.build_candidate("honda_l15b7", ...) from the B58's DERIVED values
    (test_epa_fixtures.b58_values), with its deliverable-torque table measured through the
    candidate itself as completion's step 1 measures it (engine_env.measure_deliverable_torque,
    rounded to 0.1 Nm). No EPA input: the Honda's typed specs and the B58's numbers. Nothing here
    is a statement about the Honda; only the structure is checked."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        from test_epa_fixtures import b58_values
        values = b58_values()
        first = engines.build_candidate("honda_l15b7", values)
        values["deliverable_torque"] = [[int(r), float(round(t, 1))] for r, t in
                                        E.measure_deliverable_torque(first.car.table_rpms, plant=first)]
        cls.plant = engines.build_candidate("honda_l15b7", values)
        seed, w = V.EPISODES[0]
        cls.neutral = K.neutral_run(cls.plant, cycle=V.episode_cycle(None, plant=cls.plant), seed=seed, weights=w)

    def test_the_run_records_the_cvts_branches_and_the_identity_holds(self):
        n = self.neutral
        self.assertIs(type(self.plant.car), engines.CvtCar)
        self.assertEqual(n.box, "cvt")
        self.assertEqual(n.ecu_calls, n.steps)
        self.assertTrue(set(n.held) <= {"economy", "kickdown", "power-limited", "low-speed"})
        self.assertTrue(np.all(n.gear_index == -1))
        idt = K.neutral_identity(n, ecu=self.plant.engine.ecu)
        self.assertTrue(idt.holds, idt)
        # here the ECU enriches, so lambda_b is not float32-exact at some steps and the float32
        # definition is load-bearing on lambda as well as spark
        self.assertTrue(np.any(n.lam_b.astype(np.float32).astype(np.float64) != n.lam_b))
        self.assertGreater(float(np.max(np.abs(n.lam - n.lam_b))), 0.0)

    def test_the_recorded_box_state_is_the_laws(self):
        """At every step the ratio, engine speed, branch and economy point recorded are what a fresh
        CvtVehicle's ratio_for gives at the speed and force recorded: the wrapper read the call the
        environment made (and the law is stateless, its docstring)."""
        n = self.neutral
        veh = E.vehicle_for(self.plant.car)
        for i in range(0, n.steps, 7):
            ratio, rpm, branch, n_eco, t_eco = veh.ratio_for(n.v_mps[i], n.force_n[i])
            self.assertEqual((float(ratio), float(rpm), branch), (n.cvt_ratio[i], n.rpm[i], n.held[i]), i)
            if n_eco is None:
                self.assertTrue(math.isnan(n.n_eco[i]) and math.isnan(n.t_eco[i]), i)
            else:
                self.assertEqual((float(n_eco), float(t_eco)), (n.n_eco[i], n.t_eco[i]), i)

    def test_delivery_reports_the_kickdown_margin_by_branch(self):
        d = K.delivery(self.neutral, plant=self.plant, t_from_s=K.T_FROM_S)
        self.assertEqual(d.held["box"], "cvt")
        self.assertEqual(sum(d.held["counts"].values()), d.steps)
        self.assertIsNone(d.bar_rpm_margin)
        m = d.margin_to_threshold
        self.assertEqual(m["threshold"], "CvtVehicle.kickdown_threshold_nm(N_eco)")
        # the law holds N_eco exactly while T_eco is at or under the threshold (economy), and kicks
        # down otherwise: off the economy branch every step's margin is above 0
        if "economy" not in d.held["counts"] and "low-speed" not in d.held["counts"]:
            self.assertGreater(m["economy_point"]["min"], 0.0)
        json.dumps(d.as_json(), allow_nan=False)
        with self.assertRaises(ValueError):                       # a run of another plant
            K.delivery(self.neutral, plant=_plant(), t_from_s=K.T_FROM_S)


class DrivelineEta(Guarded):
    def test_with_driveline_eff_moves_the_demand_as_one_over_eta(self):
        p = _plant()
        rho = 101.3 * 1000.0 / (287.0 * p.scenario.t_amb)
        v = p.scenario.v_kmh / 3.6
        tq = {}
        for eta in (0.86, 0.98):
            q = K.with_driveline_eff(p, eta)
            self.assertEqual(q.car.driveline_eff, eta)
            tq[eta], _ = E.vehicle_for(q.car).demand(v, 0.0, p.scenario.grade, rho=rho)
        base, _ = E.vehicle_for(p.car).demand(v, 0.0, p.scenario.grade, rho=rho)
        for eta, t in tq.items():
            self.assertAlmostEqual(t * eta / (base * p.car.driveline_eff), 1.0, places=12)
        self.assertEqual(p.car.driveline_eff, 0.92)                 # the plant passed is unchanged
        for bad, exc in ((np.float64(0.86), TypeError), (1.5, ValueError), (0.0, ValueError)):
            with self.assertRaises(exc):
                K.with_driveline_eff(p, bad)


class CompletionMeasurements(Guarded):
    """The completion's measurements k3_knee holds since WP3's integration (23 October 2026; PLAN.md 5.9
    items 1, 2, 3 and 8), on the B58, whose own records give each a hand answer: the table its derived
    file carries, the 15 Nm floor its spec types, the neutral run of the locked climb, the damage two
    ways. Each with a control (mistake 12)."""

    def test_the_b58s_table_is_measured_back(self):
        """deliverable_table at the car's own settling gives back the table data/derived_params.json
        carries (derive_params.py measured it the same way, rounded to 0.1 Nm); the knock flag's duty is a
        share of the load loop's calls. The control: one settling step more moves the unrounded table (the
        setting reaches the measurement, mistake 25)."""
        p = _plant()
        t = K.deliverable_table(p, settle=p.car.table_settle)
        self.assertEqual([list(x) for x in t.table], [[int(r), float(v)] for r, v in p.car.deliverable_torque])
        self.assertEqual(t.calls, len(p.car.table_rpms) * p.car.table_settle)
        self.assertTrue(0.0 <= t.knock_flag_duty <= 1.0)
        self.assertIs(E.SupervisoryTunerEnv._track_torque.__name__, "_track_torque")   # the wrap is gone
        t2 = K.deliverable_table(p, settle=p.car.table_settle + 1)
        self.assertNotEqual(t2.raw, t.raw)
        with self.assertRaises(TypeError):
            K.deliverable_table(p, settle=30.0)

    def test_the_b58s_floor_is_its_typed_15_nm(self):
        """torque_floor by the B58's rule gives back engine_specs/b58.toml's torque_floor_nm (1.25 x 12.0 Nm
        at 1200 rpm and the table's 42 C). The control: another factor gives another floor."""
        p = _plant()
        f = K.torque_floor(p, settle=p.car.table_settle)
        self.assertEqual(f.nm, p.engine.loop.torque_floor_nm)
        self.assertEqual(round(f.closed_nm, 1), 12.0)
        self.assertEqual((f.rpm, f.t_amb_k, f.extrapolation), (1200.0, p.car.table_t_amb, True))
        with mock.patch.object(K, "FLOOR_FACTOR", 1.5):
            self.assertNotEqual(K.torque_floor(p, settle=p.car.table_settle).nm, f.nm)

    def test_the_locked_neutral_run_and_the_damage_two_ways(self):
        """locked_neutral_run is neutral_run on the locked climb's frozen episode 1 (its trace baseline_trace's
        bit for bit); damage_readings' two readings and the knock term's share. The control: KI x 1.1 (knock_a
        / 1.1, E6 row 7's scale) moves the share and not the thermal reading's sign."""
        p = _plant()
        run = K.locked_neutral_run(p)
        self.assertTrue(K.traces_identical(run.trace(), _nominal()))
        d = K.damage_readings(p)
        self.assertGreater(d["total"], 0.0)
        self.assertLessEqual(d["thermal"], d["total"])
        self.assertEqual(d["knock_share"], (d["total"] - d["thermal"]) / d["total"])
        q = dataclasses.replace(p, engine=dataclasses.replace(p.engine, cycle=dataclasses.replace(
            p.engine.cycle, knock_a=p.engine.cycle.knock_a / 1.1)))
        d2 = K.damage_readings(q)
        self.assertNotEqual(d2["knock_share"], d["knock_share"])
        nan = K.with_knee(p, 1123.0)
        nan = dataclasses.replace(nan, engine=dataclasses.replace(nan.engine, damage=dataclasses.replace(
            nan.engine.damage, turb_knee_k=float("nan"))))
        with self.assertRaises(ValueError):
            K.damage_readings(nan)


if __name__ == "__main__":
    unittest.main(verbosity=2)
