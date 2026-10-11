"""test_wide_air.py -- X2's training roads hold to what wide_air.py claims.

    python test_wide_air.py        # about a minute

wide_air.py swaps engine_env's boost ceiling, in its own process, for one that
follows the inlet of a stepping WideAirTrainingEnv, and copies two of
engine_env's road builders so their drag can use the episode's air. Each claim
it makes is checked here, and each check fails if the claim stops holding:

  SeaLevel        at 101.3 kPa the road builders return engine_env's, to the bit,
                  and a whole episode equals the same road on the plain
                  environment, step for step
  OtherEnvs       an environment that is not a WideAirTrainingEnv sees the
                  plant's ceiling, in this process and in one without wide_air
  ThinAir         at 80 kPa both the hard cap and the flow ceiling fall in
                  proportion to the inlet, the steps use it, and the agent sees
                  the pressure
  Floor           the closed-throttle torque reproduces engine_env's 42 C row,
                  the road's floor is X1's rule at the episode's ambient, and
                  the cold road that failed check_roads at 15 Nm now passes
  Gearbox         the kickdown table is the stored one at sea level and the
                  measured one in thin air, and the hot thin-air climb that
                  failed test_reward's corner is now drivable
  Draws           ambient and pressure stay inside 0-45 C and 80-101.3 kPa,
                  a seed repeats its sequence, and forcing an episode's air
                  leaves the stream unchanged
"""
import copy
import json
import os
import subprocess
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engine_env as EE                                  # noqa: E402
import plant                                             # noqa: E402
import wide_air as W                                     # noqa: E402

FLOWS = (20.0, 60.0, 120.0, 180.0, 240.0)               # g/s of air
P_IDX = 10                                               # the pressure input in _obs() (9 is the ambient)


def rollout(env, n, rng_seed=0):
    """n steps of a fixed random action sequence; every reward and info."""
    rng = np.random.default_rng(rng_seed)
    out = []
    for _ in range(n):
        a = rng.uniform(-1.0, 1.0, 5).astype(np.float32)
        obs, r, term, trunc, info = env.step(a)
        out.append((obs.copy(), r, {k: info[k] for k in ("torque", "t_turb", "t_oil", "ki", "mdot_exh")}))
        if term or trunc:
            break
    return out


def same(a, b):
    return all(np.array_equal(x[0], y[0]) and x[1] == y[1] and x[2] == y[2] for x, y in zip(a, b)) \
        and len(a) == len(b)


class SeaLevel(unittest.TestCase):
    def test_builders_equal_engine_env(self):
        for seed in (1, 2, 3):
            for t_amb in (273.15, 300.0, 318.15):
                c = EE.make_terrain(np.random.default_rng(seed), duration=900.0, dt=1.0, t_amb=t_amb,
                                    grade_max=EE.EXTREME_GRADE_MAX)
                r1, r2 = np.random.default_rng(seed + 50), np.random.default_rng(seed + 50)
                v1 = EE.extreme_speed_profile(r1, len(c["t"]), 1.0, c["grade"], t_amb)
                v2 = W.speed_profile(r2, len(c["t"]), 1.0, c["grade"], t_amb, 101.3)
                self.assertTrue(np.array_equal(v1, v2))
                self.assertTrue(np.array_equal(EE.grade_floor(v1, t_amb, 1.0),
                                               W.grade_floor(v1, t_amb, 101.3, 1.0)))

    def test_episode_equals_plain_env(self):
        w = W.WideAirTrainingEnv(seed=5)
        w.reset(seed=5, options={"p_kpa": 101.3, "t_amb_c": 30.0})
        self.assertEqual(w.MAP_CEIL_KPA, EE.SupervisoryTunerEnv.MAP_CEIL_KPA.fget(w))
        e = EE.SupervisoryTunerEnv(copy.deepcopy(w.cycle), dt=1.0, seed=5)
        e.reset(seed=5)
        for tn in (e.thermal, e.thermal_base):
            tn.p.c_turb = w.thermal.p.c_turb
        self.assertTrue(np.array_equal(w._obs(), e._obs()))
        self.assertTrue(same(rollout(w, 300), rollout(e, 300)))


class OtherEnvs(unittest.TestCase):
    def test_ceiling_is_the_plants_when_nothing_steps(self):
        self.assertIs(EE.boost_ceiling_kpa, W.boost_ceiling_kpa)
        for m in FLOWS:
            for t in (273.15, 298.0, 318.15):
                self.assertEqual(EE.boost_ceiling_kpa(m, t), plant.boost_ceiling_kpa(m, t))

    def test_plain_env_unchanged_beside_a_thin_air_env(self):
        def locked():
            e = EE.SupervisoryTunerEnv(EE.make_grade_climb(duration=300.0, dt=1.0), dt=1.0, seed=3)
            e.reset(seed=3)
            return rollout(e, 300, rng_seed=3)
        before = locked()
        w = W.WideAirTrainingEnv(seed=9)
        w.reset(seed=9, options={"p_kpa": 80.0})
        rollout(w, 50)
        self.assertTrue(same(before, locked()))
        # and against a process that never imported wide_air
        code = ("import json,numpy as np,engine_env as EE\n"
                "e=EE.SupervisoryTunerEnv(EE.make_grade_climb(duration=300.0,dt=1.0),dt=1.0,seed=3)\n"
                "e.reset(seed=3);rng=np.random.default_rng(3);out=[]\n"
                "for _ in range(300):\n"
                "  o,r,t,tr,i=e.step(rng.uniform(-1.0,1.0,5).astype(np.float32));out.append([r,i['t_turb']])\n"
                "  if t or tr: break\n"
                "print(json.dumps(out))")
        res = subprocess.run([sys.executable, "-c", code], cwd=HERE, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, res.stderr)
        fresh = json.loads(res.stdout)
        self.assertEqual([[r, i["t_turb"]] for _, r, i in before], fresh)


class ThinAir(unittest.TestCase):
    def test_ceilings_fall_with_the_inlet(self):
        w = W.WideAirTrainingEnv(seed=4)
        w.reset(seed=4, options={"p_kpa": 80.0})
        inlet = 99.3 * 80.0 / 101.3
        cap = float(plant.boost_ceiling_constants()["pr_cap"])
        self.assertAlmostEqual(w.MAP_CEIL_KPA, inlet * cap, places=9)
        W._STEPPING.append(w._p_inlet)
        try:
            for m in FLOWS:
                self.assertAlmostEqual(EE.boost_ceiling_kpa(m, 315.0),
                                       plant.boost_ceiling_kpa(m, 315.0, inlet), places=9)
                self.assertLess(EE.boost_ceiling_kpa(m, 315.0), plant.boost_ceiling_kpa(m, 315.0))
        finally:
            W._STEPPING.pop()
        self.assertEqual(W._STEPPING, [])

    def test_steps_use_the_episode_inlet(self):
        seen, real = [], W._PLANT_CEILING

        def spy(m, t=298.0, p=99.3):
            seen.append(p)
            return real(m, t, p)
        W._PLANT_CEILING = spy
        try:
            w = W.WideAirTrainingEnv(seed=4)
            w.reset(seed=4, options={"p_kpa": 80.0})
            seen[:] = []                      # reset's floor measurement shuts the throttle
            rollout(w, 30)
            thin, seen[:] = list(seen), []
            e = EE.SupervisoryTunerEnv(EE.make_grade_climb(duration=60.0, dt=1.0), dt=1.0, seed=4)
            e.reset(seed=4)
            rollout(e, 30)
            plain = list(seen)
        finally:
            W._PLANT_CEILING = real
        self.assertTrue(thin and plain)
        self.assertTrue(all(abs(p - 99.3 * 80.0 / 101.3) < 1e-9 for p in thin))
        self.assertTrue(all(p == 99.3 for p in plain))

    def test_agent_sees_the_pressure(self):
        w = W.WideAirTrainingEnv(seed=4)
        obs, _ = w.reset(seed=4, options={"p_kpa": 80.0})
        self.assertAlmostEqual(float(obs[P_IDX]), (80.0 - 101.3) / 8.0, places=5)

    def test_stepping_restores_the_stack(self):
        w = W.WideAirTrainingEnv(seed=6)
        w.reset(seed=6, options={"p_kpa": 85.0})
        rollout(w, 5)
        self.assertEqual(W._STEPPING, [])


class Floor(unittest.TestCase):
    """The road's torque floor is X1's rule at the episode's own ambient."""

    def test_closed_throttle_torque_reproduces_the_measurements(self):
        w = W.WideAirTrainingEnv(seed=1)
        self.assertAlmostEqual(W.closed_throttle_nm(w, 315.15), 12.1, delta=0.1)
        self.assertAlmostEqual(W.closed_throttle_nm(w, 273.15), 20.6, delta=0.1)

    def test_floor_rule(self):
        w = W.WideAirTrainingEnv(seed=1)
        self.assertEqual(W.torque_floor_nm(w, 318.15), EE.EXTREME_T_FLOOR_NM)   # X1's 15 Nm in hot air
        cold = W.torque_floor_nm(w, 273.15)
        self.assertAlmostEqual(cold, 1.25 * W.closed_throttle_nm(w, 273.15), places=9)
        self.assertGreater(cold, 25.0)

    def test_cold_road_asks_no_less_than_the_floor_allows(self):
        """seed 109 at 0.7 C failed check_roads with the 15 Nm floor (p95 error 0.094);
        on the neutral policy it must now stay inside the tolerance band."""
        w = W.WideAirTrainingEnv(seed=109)
        w.reset(seed=109)
        self.assertLess(float(w.cycle["t_amb"]) - 273.15, 1.0)
        errs = []
        while True:
            _, _, term, trunc, info = w.step(EE.neutral_action())
            errs.append(abs(info["torque_req"] - info["torque"]) / max(info["torque_req"], 40.0))
            if term or trunc:
                break
        self.assertLess(float(np.percentile(errs, 95)), EE.TRACK_TOL)


class Gearbox(unittest.TestCase):
    """The kickdown table follows the pressure; at sea level it is the stored one."""

    def test_sea_level_table_is_the_stored_table(self):
        v = W.ThinAirVehicle()
        v.set_pressure(101.3)
        self.assertEqual(v.DELIVERABLE_TORQUE, EE.Vehicle().DELIVERABLE_TORQUE)

    def test_thin_air_table_is_the_measured_one(self):
        v = W.ThinAirVehicle()
        v.set_pressure(80.0)
        thin, sea = dict(v.DELIVERABLE_TORQUE), dict(EE.Vehicle().DELIVERABLE_TORQUE)
        self.assertTrue(all(thin[r] < sea[r] for r in sea))
        self.assertAlmostEqual(thin[2000], 252.8, delta=0.5)          # deliverable_torque's docstring
        m = W.deliverable_torque(80.0, (2000, 3000))
        self.assertAlmostEqual(thin[2000], m[2000], places=6)
        self.assertAlmostEqual(thin[3000], m[3000], places=6)

    def test_hot_thin_climb_is_drivable(self):
        """The road test_reward.py's corner failed before the gearbox knew the air:
        the 12 % climb at 45 C and 80 kPa, neutral -0.139 a step, p95 error 0.171."""
        w = W.WideAirTrainingEnv(seed=11)
        w.reset(seed=11, options={"family": "locked", "t_amb_c": 45.0, "p_kpa": 80.0})
        rs, errs = [], []
        while True:
            _, r, term, trunc, info = w.step(EE.neutral_action())
            rs.append(r)
            errs.append(abs(info["torque_req"] - info["torque"]) / max(info["torque_req"], 40.0))
            if term or trunc:
                break
        self.assertLess(abs(float(np.mean(rs))), 0.05)
        self.assertLess(float(np.percentile(errs, 95)), EE.TRACK_TOL)


class Draws(unittest.TestCase):
    def test_air_inside_the_ranges_and_repeatable(self):
        def air(seed, n=30):
            w = W.WideAirTrainingEnv(seed=seed)
            out = []
            for i in range(n):
                w.reset(seed=seed if i == 0 else None)
                out.append((float(w.cycle["t_amb"]) - 273.15, float(w.cycle["p_baro"])))
            return out
        a = air(7)
        self.assertEqual(a, air(7))
        t, p = np.array(a).T
        self.assertTrue((t >= 0.0).all() and (t <= 45.0).all())
        self.assertTrue((p >= 80.0).all() and (p <= 101.3).all())
        self.assertLess(t.min(), 10.0)
        self.assertGreater(t.max(), 35.0)
        self.assertLess(p.min(), 86.0)

    def test_forcing_the_air_keeps_the_stream(self):
        w1, w2 = W.WideAirTrainingEnv(seed=8), W.WideAirTrainingEnv(seed=8)
        w1.reset(seed=8)
        w2.reset(seed=8, options={"t_amb_c": 0.0, "p_kpa": 80.0})
        self.assertEqual(w2.cycle["family"], w1.cycle["family"])
        self.assertTrue(np.array_equal(w1.cycle["t"], w2.cycle["t"]))
        w1.reset()
        w2.reset()
        self.assertEqual((w1.cycle["t_amb"], w1.cycle["p_baro"]), (w2.cycle["t_amb"], w2.cycle["p_baro"]))
        self.assertTrue(np.array_equal(w1.cycle["grade"], w2.cycle["grade"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
