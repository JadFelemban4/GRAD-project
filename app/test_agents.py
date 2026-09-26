"""The agent replay page's own suite. Nothing here writes, trains or evaluates.

    python -m app.test_agents          the default suite
    python -m app.test_agents --full   adds the slow checks

Run from the repository root. app/test_replay.py's test_read_only scans this
file too, so banned tokens are written as raw regexes, never as calls, and
fixtures are made in temporary directories OUTSIDE the repository.
"""
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

import numpy as np

from app import agent_trace as T
from engine_env import (ACT_HI, ACT_LO, SLEW, SupervisoryTunerEnv, make_grade_climb,
                        neutral_action)
from evaluate import EPISODES, EPISODES_D2, agent_policy, run_episode

ROOT = Path(__file__).resolve().parent.parent
FULL = "--full" in sys.argv


class TraceTests(unittest.TestCase):
    """agent_trace: episodes, cycles, road geometry, JSON safety, the mirror."""

    def test_jsonable_converts_numpy(self):
        got = T.jsonable({"a": np.float32(0.3), "b": np.bool_(True),
                          "c": float("nan"), "d": np.inf,
                          "e": np.array([0.25, 0.5], dtype=np.float32),
                          "f": (np.int64(3), [np.float64(1.5), None, "x"]),
                          7: np.array([True, False])})
        self.assertIs(type(got["a"]), float)
        self.assertEqual(got["a"], float(np.float32(0.3)))
        self.assertIs(got["b"], True)
        self.assertIsNone(got["c"])
        self.assertIsNone(got["d"])
        self.assertEqual(got["e"], [0.25, 0.5])
        self.assertTrue(all(type(v) is float for v in got["e"]))
        self.assertEqual(got["f"], [3, [1.5, None, "x"]])
        self.assertIs(type(got["f"][0]), int)
        self.assertEqual(got["7"], [True, False])
        self.assertTrue(all(type(v) is bool for v in got["7"]))
        json.dumps(got, allow_nan=False)
        with self.assertRaises(TypeError):
            T.jsonable(object())

    def test_episode_indexing(self):
        ep = T.episode("d2", 1)
        self.assertEqual(ep["seed"], 1000)
        self.assertEqual(ep["weights"], EPISODES_D2[0][1])
        self.assertEqual(ep["road"], (141.05, 0.13314))
        self.assertEqual((ep["protocol"], ep["idx"]), ("d2", 1))
        self.assertEqual(T.episode("d2", 20)["seed"], EPISODES_D2[19][0])
        pd = T.episode("phase-d", 1)
        self.assertIsNone(pd["road"])
        self.assertEqual((pd["seed"], pd["weights"]), EPISODES[0])
        for protocol, idx in (("d2", 0), ("d2", 21), ("d2", "1"), ("d2", True),
                              ("x", 1)):
            with self.subTest(protocol=protocol, idx=idx):
                with self.assertRaises(KeyError):
                    T.episode(protocol, idx)

    def test_route_geometry(self):
        cycle = T.build_cycle(T.episode("d2", 1))
        before = {k: np.asarray(v).tobytes() for k, v in cycle.items()}
        r = T.route(cycle)
        for k, v in cycle.items():
            self.assertEqual(np.asarray(v).tobytes(), before[k], f"route() changed cycle[{k!r}]")
        for key in ("s_m", "x_m", "z_m", "grade_pct", "speed_kmh"):
            self.assertEqual(len(r[key]), T.STEPS + 1, key)
        self.assertAlmostEqual(r["length_m"], 25603, delta=1)
        self.assertAlmostEqual(r["rise_m"], 2755, delta=1)
        self.assertEqual(r["climb_start_s"], 141.0)
        v, g = cycle["v_mps"], cycle["grade"]
        for k in range(T.STEPS):
            theta = np.arctan(g[k])
            self.assertAlmostEqual(r["x_m"][k + 1] - r["x_m"][k], v[k] * T.DT * np.cos(theta), delta=1e-9)
            self.assertAlmostEqual(r["z_m"][k + 1] - r["z_m"][k], v[k] * T.DT * np.sin(theta), delta=1e-9)
        json.dumps(r, allow_nan=False)
        self.assertAlmostEqual(T.route(T.build_cycle(T.episode("d2", 5)))["rise_m"], 1917, delta=1)
        self.assertAlmostEqual(T.route(T.build_cycle(T.episode("d2", 6)))["rise_m"], 3247, delta=1)
        self.assertEqual(T.route(T.build_cycle(T.episode("phase-d", 1)))["climb_start_s"], 180.0)

    def test_applied_not_commanded(self):
        frames = []
        with mock.patch.object(T, "build_cycle", _short_cycle):
            T.run_lanes([(_neutral, True)], T.episode("d2", 1),
                        on_frame=lambda frame, seen: frames.append(frame))
        car = frames[0]["cars"][0]
        self.assertEqual(car["cmd"], [float(v) for v in neutral_action()])
        self.assertEqual(car["act"], [0.0, 0.0, 0.0, 0.25, float(np.float32(0.3))])
        self.assertEqual(car["held"], [False, False, False, True, True])

    def test_preview_slice_is_the_observation(self):
        ep = T.episode("d2", 1)
        self.assertEqual(T.STEPS, len(T.build_cycle(ep)["v_mps"]) - 1)
        envs, obs = {}, {}
        for sighted in (True, False):
            env = SupervisoryTunerEnv(T.build_cycle(ep), dt=T.DT, seed=ep["seed"],
                                      use_preview=sighted)
            env.reset(seed=ep["seed"])
            env.w = np.asarray(ep["weights"], dtype=np.float32)
            envs[sighted], obs[sighted] = env, env._obs()
        grade = envs[True].cycle["grade"]
        for k in range(151):
            if k in (0, 125, 150):
                s, b = obs[True], obs[False]
                want = (12 * np.asarray(envs[True]._preview())).astype(np.float32)
                self.assertEqual(s[T.PREVIEW].tolist(), want.tolist(), f"k={k}")
                self.assertEqual(s[13], np.float32(12 * grade[k]), f"k={k}")
                self.assertEqual(b[13], s[13], f"k={k}: the blind car sees the grade it is on")
                self.assertEqual(b[T.PREVIEW].tolist(), [0.0] * len(T.PREVIEW_S), f"k={k}")
            if k == 125:
                # The climb starts at 141 s: 16 s away, so only the 30 s horizon sees it.
                self.assertEqual((s[13], s[16]), (0.0, 0.0))
                self.assertGreater(s[17], 0.0)
            for sighted, env in envs.items():
                obs[sighted] = env.step(neutral_action())[0]

    def test_lane_stops_on_divergence(self):
        frames = []
        with mock.patch.object(T, "build_cycle", _short_cycle):
            got = T.run_lanes([(_neutral, True), (_nan_policy, False)], T.episode("d2", 1),
                              on_frame=lambda frame, seen: frames.append((frame, seen)))
        self.assertEqual([f["k"] for f, _ in frames], list(range(29)))
        self.assertIsNotNone(frames[0][0]["cars"][1])
        self.assertEqual(frames[0][0]["cars"][1]["act"], [None] * 5)
        for frame, seen in frames[1:]:
            self.assertIsNone(frame["cars"][1])
            self.assertIsNone(seen[1])
            self.assertEqual((seen[0].shape, seen[0].dtype), ((23,), np.float32))
        for frame, _ in frames:
            json.dumps(frame, allow_nan=False)
        self.assertEqual(len(got), 2)
        for result in got:
            self.assertEqual(set(result), RESULT_KEYS)


RESULT_KEYS = {"ret", "damage", "fuel", "torque_viol", "peak_turb", "knock"}


def _short_cycle(ep):
    """A 30 s climb: 29 steps, about a second of plant."""
    return make_grade_climb(duration=30.0, dt=1.0)


def _neutral(env, obs):
    return neutral_action()


def _nan_policy(env, obs):
    return np.full(5, np.nan, dtype=np.float32)


class ProofTests(unittest.TestCase):
    """Spec tests 1 and 2: the tracer IS evaluate.run_episode, on a real C4 pair.

    `==` on whole result dicts, no tolerance. If it ever fails, find the cause;
    the fallback is sequential lanes, never an epsilon.
    """

    @classmethod
    def setUpClass(cls):
        paths = [str(ROOT / "runs_c4" / f"{arm}_seed0") + "/final" for arm in ("sighted", "blind")]
        try:
            from stable_baselines3 import SAC
        except ImportError:
            SAC = None
        if SAC is None or not all(Path(p + ".zip").is_file() for p in paths):
            print("\n  agent path UNPROVEN on this machine (no runs_c4/*_seed0/final.zip "
                  "or no stable-baselines3)")
            raise unittest.SkipTest("agent path UNPROVEN on this machine")
        m_s, m_b = SAC.load(paths[0]), SAC.load(paths[1])     # no device: evaluate.py:370
        cls.device = str(m_s.device)
        cls.ep = T.episode("d2", 1)
        seed, weights, start_s, grade = EPISODES_D2[0]
        cls.frames = []
        cls.got = T.run_lanes([(agent_policy(m_s), True), (agent_policy(m_b), False)], cls.ep,
                              on_frame=lambda frame, seen: cls.frames.append(frame))
        cls.want = [run_episode(agent_policy(m_s), seed, weights, True, road=(start_s, grade)),
                    run_episode(agent_policy(m_b), seed, weights, False, road=(start_s, grade))]

    def test_tracer_equals_run_episode(self):
        print(f"\n  == proof on {self.device}: sighted damage {self.got[0]['damage']!r}, "
              f"blind damage {self.got[1]['damage']!r}")
        self.assertEqual(self.got, self.want)

    def test_frames_are_the_episode(self):
        frames, road = self.frames, T.route(T.build_cycle(self.ep))
        self.assertEqual(len(frames), T.STEPS)
        self.assertEqual([f["k"] for f in frames], list(range(T.STEPS)))
        rescale = SupervisoryTunerEnv(T.build_cycle(self.ep), dt=T.DT)._rescale
        any_held = False
        for lane, result in enumerate(self.got):
            cars = [f["cars"][lane] for f in frames]
            self.assertEqual(cars[-1]["damage"], result["damage"])
            self.assertEqual(max(c["turb_c"] for c in cars), result["peak_turb"])
            prev = np.zeros(5, dtype=np.float32)
            for k, car in enumerate(cars):
                for key in ("act", "cmd", "preview_pct"):
                    self.assertNotIn(None, car[key], f"lane {lane} k {k} {key}")
                self.assertIsNotNone(car["map_kpa"])
                raw = rescale(np.asarray(car["cmd"], dtype=np.float32))
                want = np.clip(np.clip(raw, prev - SLEW * T.DT, prev + SLEW * T.DT), ACT_LO, ACT_HI)
                act = np.asarray(car["act"], dtype=np.float32)
                self.assertEqual(act.tolist(), want.tolist(), f"lane {lane} k {k}")
                self.assertEqual(car["held"], (act != raw).tolist(), f"lane {lane} k {k}")
                any_held = any_held or any(car["held"])
                prev = act
                for j, h in enumerate(T.PREVIEW_S):
                    if lane == 0:
                        g = road["grade_pct"][min(k + int(h / T.DT), T.STEPS)] / 100.0
                        self.assertAlmostEqual(car["preview_pct"][j] / 100.0, g, delta=1e-6)
                    else:
                        self.assertEqual(car["preview_pct"][j], 0.0)
        self.assertTrue(any_held, "the rate limit never held a command back: suspicious")
        for f in frames:
            json.dumps(f, allow_nan=False)


if __name__ == "__main__":
    unittest.main(argv=[sys.argv[0]] + [a for a in sys.argv[1:] if a != "--full"], verbosity=2)
