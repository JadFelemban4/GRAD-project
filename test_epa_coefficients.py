"""test_epa_coefficients.py -- an engine's own coefficients, pointed at the B58.

    python -B test_epa_coefficients.py        about four minutes (four B58 climbs); exit 0 when all pass

Build step 2, WP3 (23 October 2026): docs/build_step_2/PLAN.md section 2 (WP3) and 5.9 item 5;
amendment F5; docs/build_step_2/HANDOFFS.md, WP3 item 4; WP3_INTERFACES.md section 9.8. The B58
runs here, which is not EPA data: no EPA table, no contract JSON, no log is opened (every class
runs inside forbid_real_data), and no number is printed.

  B58         coefficients(the B58) gives results/ENGINE_THRESHOLDS/b58_propagation.json back bit for
              bit: its text, written in the generator's form (thresholds.common.write_json: indent 1,
              ASCII, LF), is the file's bytes. Control: one ulp in one value is seen
  Ambient     the climb is the plant's own ambient and G stays over the contract's 42 C (F5): a B58
              with a 305 K scenario climbs at 305 K and its climb cell moves off the file's, while
              G at a given gas and flow does not move with the scenario. Controls: the climb's
              arrays other than the ambient are the B58's; another reference moves G by f(1-f)
              times the difference; a NaN knee and a NumPy bias are refused before any episode
  Cam         the B58 runs no cam, and cyc() is b58_propagation's cycle there to the bit; a form-D
              variant of the B58 is evaluated at its ECU's cam, not refused (HANDOFFS WP3 item 4).
              Controls: the same variant run without a cam is refused by the breathing, and a
              different cam schedule moves the torque (the cam reached the cycle, mistake 25)
"""
import dataclasses
import json
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_coefficients as EC  # noqa: E402
import evaluate as V  # noqa: E402
from plant import Operating, run_cycle, exhaust_backpressure_kpa  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)
from thresholds.contract import T_AMB_C  # noqa: E402

PROPAGATION_JSON = os.path.join(HERE, "results", "ENGINE_THRESHOLDS", "b58_propagation.json")


def _file_bytes():
    with open(PROPAGATION_JSON, "rb") as fh:
        return fh.read()


def _generator_text(obj):
    """The text thresholds.common.write_json writes for obj: json.dump with indent 1 and ASCII, LF
    line endings (thresholds/common.py:51-56), here as a string so that nothing is written."""
    return json.dumps(obj, indent=1, ensure_ascii=True)


def _with_ambient(plant, t_amb):
    return dataclasses.replace(plant, scenario=dataclasses.replace(plant.scenario, t_amb=t_amb))


def _form_d(plant, *, cam_c0):
    """A form-D variant of the plant: the breathing reads the intake cam (ve_cam per crank degree
    about cam_ref_deg 0), and its ECU runs a cam schedule, constant cam_c0 inside a domain that
    covers the climb. DESIGN values for the test only; Engine's own checks build it (the ECU runs a
    cam exactly when the form has D)."""
    eng = plant.engine
    cycle = dataclasses.replace(eng.cycle, form="A+B+C+D", ve_cam=0.004, cam_ref_deg=0.0)
    ecu = dataclasses.replace(eng.ecu, cam_on=1, cam_c0=cam_c0, cam_rpm_lo=1000.0, cam_rpm_hi=6500.0,
                              cam_map_lo=20.0, cam_map_hi=260.0, cam_lo=-40.0, cam_hi=60.0)
    return dataclasses.replace(plant, engine=dataclasses.replace(eng, cycle=cycle, ecu=ecu))


class B58(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = engines.get("b58")
        cls.res = EC.coefficients(cls.plant)
        cls.file = _file_bytes()

    def test_the_b58_comes_back_bit_for_bit(self):
        self.assertEqual(self.file.count(b"\r"), 0)
        self.assertEqual(_generator_text(self.res).encode("ascii"), self.file)
        self.assertEqual(json.loads(self.file), self.res)
        self.assertEqual(list(self.res), ["episode_summary", "peak_t_turb_c", "climb", "flat",
                                          "env_torque_bias", "env_coefficients"])

    def test_the_comparison_can_fail(self):
        """Control: one ulp in one value of the result changes the text, so the comparison above
        reads every value's bits."""
        res = json.loads(_generator_text(self.res))
        f = res["climb"]["housing"]["f"]
        res["climb"]["housing"]["f"] = math.nextafter(f, math.inf)
        self.assertNotEqual(_generator_text(res).encode("ascii"), self.file)

    def test_g_is_over_42_c_on_the_b58(self):
        c = self.res["climb"]
        hs = EC.housing(self.plant, c["point"]["egt"], c["point"]["mdot"], t_amb_c=T_AMB_C)
        self.assertEqual(hs, c["housing"])
        self.assertEqual(T_AMB_C, 42.0)
        self.assertEqual(self.plant.scenario.t_amb, 315.0)

    def test_the_climb_cell_and_the_housing_equivalent(self):
        """climb_cell (WP3's integration, 23 October 2026: one climb per E6 probe in the completion's pool)
        is the cell coefficients() reads, b58_propagation.json's climb point bit for bit; housing_equivalent
        at its housing gives back chain()'s steady housing change of a 1 % torque bias, the same expression.
        The control: one ulp of the gas moves the equivalent."""
        self.assertEqual(EC.climb_cell(self.plant), json.loads(self.file)["climb"]["point"])
        hs = self.res["climb"]["housing"]
        for arm in ("fixed_spark", "ecu_schedule"):
            tb = self.res["climb"][arm]["torque_bias_1pct"]
            self.assertEqual(EC.housing_equivalent(hs, tb["degt_k"], tb["dmdot_rel"]), tb["dTh_ss_k"])
        tb = self.res["climb"]["fixed_spark"]["torque_bias_1pct"]
        self.assertNotEqual(EC.housing_equivalent(hs, math.nextafter(tb["degt_k"], math.inf), tb["dmdot_rel"]),
                            tb["dTh_ss_k"])

    def test_the_climb_cells_resolution(self):
        """Decision 85 (29 October 2026): climb_cell_resolution runs the climb climb_cell runs, its medians the cell's
        own bit for bit (b58_propagation.json's climb point), each resolution the gap to the median's next order
        statistic over CLIMB_S, positive and below the window's spread."""
        r = EC.climb_cell_resolution(self.plant)
        point = json.loads(self.file)["climb"]["point"]
        self.assertEqual((r["egt"], r["mdot"]), (point["egt"], point["mdot"]))
        self.assertEqual(r["samples"], EC.CLIMB_S[1] - EC.CLIMB_S[0] + 1)
        for k in ("egt_resolution_k", "mdot_resolution_gps"):
            self.assertTrue(math.isfinite(r[k]) and r[k] >= 0.0, (k, r[k]))


class MedianResolution(Guarded):
    def test_median_resolution_by_hand(self):
        """The median and how far it moves when one sample crosses it, by hand, odd and even; the control: fewer
        than 3 values are refused."""
        self.assertEqual(EC.median_resolution([7.0, 1.0, 11.0, 2.0, 4.0]), (4.0, 3.0))   # gaps 2 and 3
        self.assertEqual(EC.median_resolution([1.0, 2.0, 4.0, 7.0]), (3.0, 4.0))         # 3 - 1 and 7 - 3
        self.assertEqual(EC.median_resolution([5.0, 5.0, 5.0]), (5.0, 0.0))
        with self.assertRaises(ValueError):
            EC.median_resolution([1.0, 2.0])


class Ambient(Guarded):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.plant = engines.get("b58")
        cls.cool = _with_ambient(cls.plant, 305.0)
        rec, _ = EC.run_climb(cls.cool, bias=0.0)
        cls.cool_climb = EC.median_point(rec, *EC.CLIMB_S)
        cls.file_climb = json.loads(_file_bytes())["climb"]["point"]

    def test_the_climb_runs_at_the_plants_ambient(self):
        a, b = EC.climb_cycle(self.plant), EC.climb_cycle(self.cool)
        self.assertEqual((a["t_amb"], b["t_amb"]), (315.0, 305.0))
        # control: only the ambient differs between the two climbs
        for key in ("t", "v_mps", "grade"):
            self.assertTrue(np.array_equal(a[key], b[key]), key)
        self.assertEqual({k: v for k, v in a.items() if k not in ("t", "v_mps", "grade", "t_amb")},
                         {k: v for k, v in b.items() if k not in ("t", "v_mps", "grade", "t_amb")})
        # it is the plant's locked climb (engine_env.locked_climb), at evaluate's length and step
        lc = E.locked_climb(self.cool, duration=V.DURATION, dt=V.DT)
        self.assertTrue(all(np.array_equal(lc[k], b[k]) for k in ("t", "v_mps", "grade")) and lc["t_amb"] == 305.0)

    def test_another_ambient_moves_the_climb(self):
        """F5's test: a plant with another scenario ambient climbs at it. Its climb cell is not the
        B58 file's: a cooler charge and a cooler housing (mistake 25: the input reached the output)."""
        self.assertLess(self.cool_climb["iat"], self.file_climb["iat"])
        self.assertLess(self.cool_climb["t_turb"], self.file_climb["t_turb"])
        self.assertNotEqual(self.cool_climb, self.file_climb)

    def test_g_stays_over_the_contracts_42_c(self):
        p = self.file_climb
        warm = EC.housing(self.plant, p["egt"], p["mdot"], t_amb_c=T_AMB_C)
        cool = EC.housing(self.cool, p["egt"], p["mdot"], t_amb_c=T_AMB_C)
        self.assertEqual(warm, cool)                  # the scenario's ambient does not reach G
        # control: the reference does; 10 K lower raises G's term by f(1 - f) x 10 K
        other = EC.housing(self.plant, p["egt"], p["mdot"], t_amb_c=T_AMB_C - 10.0)
        f = warm["f"]
        self.assertAlmostEqual(other["dTh_per_unit_ln_mdot"] - warm["dTh_per_unit_ln_mdot"],
                               f * (1.0 - f) * 10.0, places=9)

    def test_what_would_give_another_climb_is_refused(self):
        nan = dataclasses.replace(self.plant, engine=dataclasses.replace(
            self.plant.engine, damage=dataclasses.replace(self.plant.engine.damage, turb_knee_k=float("nan"))))
        with self.assertRaises(ValueError):
            EC.run_climb(nan, bias=0.0)
        with self.assertRaises(TypeError):
            EC.run_climb(self.plant, bias=np.float64(0.0))
        with self.assertRaises(TypeError):
            EC.coefficients(None)


class Cam(Guarded):
    POINT = dict(rpm=2705.0, map_kpa=175.0, iat_k=330.0, ect_k=366.0, spark=1.16, lam=1.0)

    def _op(self, eng):
        p = self.POINT
        return Operating(rpm=p["rpm"], map_kpa=p["map_kpa"], iat_k=p["iat_k"], ect_k=p["ect_k"],
                         spark_btdc=p["spark"], lam=p["lam"],
                         p_exh_kpa=exhaust_backpressure_kpa(p["map_kpa"], engine=eng))

    def test_the_b58_runs_no_cam_and_cyc_is_b58_propagations_cycle(self):
        plant = engines.get("b58")
        p = self.POINT
        self.assertIsNone(E.BaselineECU(plant.engine.ecu).cam_deg(p["rpm"], p["map_kpa"]))
        got = EC.cyc(plant, *p.values())
        r = run_cycle(self._op(plant.engine), engine=plant.engine)          # b58_propagation.py:44-46
        self.assertEqual(got, dict(torque=r.torque_nm, egt=r.egt_c, mdot=r.mdot_air_gps + r.mdot_fuel_gps,
                                   fuel=r.mdot_fuel_gps, ki=r.knock_integral))

    def test_a_form_d_engine_is_evaluated_at_its_ecus_cam(self):
        plant = _form_d(engines.get("b58"), cam_c0=10.0)
        eng = plant.engine
        p = self.POINT
        cam = E.BaselineECU(eng.ecu).cam_deg(p["rpm"], p["map_kpa"])
        self.assertEqual(cam, 10.0)
        got = EC.cyc(plant, *p.values())
        self.assertTrue(all(math.isfinite(v) for v in got.values()))
        r = run_cycle(self._op(eng), engine=eng, cam_deg=cam)
        self.assertEqual(got["torque"], r.torque_nm)
        # control: b58_propagation's cyc, which passes no cam, is refused on this engine
        with self.assertRaisesRegex(ValueError, "cam_deg is None"):
            run_cycle(self._op(eng), engine=eng)
        # control: another schedule moves the torque, so the cam cyc passes reaches the cycle
        other = EC.cyc(_form_d(engines.get("b58"), cam_c0=20.0), *p.values())
        self.assertNotEqual(other["torque"], got["torque"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
