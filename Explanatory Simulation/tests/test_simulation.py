import math
import sys
import unittest
from pathlib import Path
import numpy as np

EX_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EX_ROOT))

from backend.simulation import (  # noqa: E402
    ACT_HI,
    ACT_LO,
    _LOCK,
    _SESSIONS,
    create_session,
    physical_to_normalized,
    step_session,
)
from evaluate import DURATION as EVAL_DURATION, DT as EVAL_DT, EPISODES  # noqa: E402


class SimulationSessionTests(unittest.TestCase):
    def setUp(self):
        with _LOCK:
            _SESSIONS.clear()

    def test_manual_session_frame_matches_direct_environment_step(self):
        session = create_session(scenario="locked", preview=True, policy="manual", seed=4)
        obs_in = session.env._obs().copy()
        physical = [0.0, 0.0, 0.0, 1.0, 1.0]
        action = physical_to_normalized(physical)
        expected_obs, expected_reward, terminated, truncated, expected_info = session.env.step(action)

        session = create_session(scenario="locked", preview=True, policy="manual", seed=4)
        result = step_session(session, steps=1, controls={"trims": physical})

        self.assertEqual(len(result["frames"]), 1)
        frame = result["frames"][0]
        self.assertEqual(frame["time_s"], EVAL_DT)
        self.assertEqual(frame["input_time_s"], 0.0)
        self.assertEqual(frame["dt"], EVAL_DT)
        self.assertEqual(frame["obs_in"], obs_in.tolist())
        self.assertEqual(frame["obs"], expected_obs.tolist())
        self.assertAlmostEqual(frame["reward"], expected_reward, places=6)
        self.assertEqual(frame["cost_knock"], expected_info["cost_knock"])
        self.assertEqual(result["done"], terminated or truncated)
        self.assertEqual(len(frame["command"]), 5)
        self.assertEqual(frame["requested"], physical)
        self.assertEqual(frame["command"], session.env.prev_act.astype(float).tolist())

    def test_preview_blinding_only_zeros_future_grade_channels(self):
        session = create_session(scenario="locked", preview=False, policy="current-grade", seed=2)
        session.env.k = 180
        result = step_session(session, steps=1)
        frame = result["frames"][0]
        self.assertEqual(frame["preview_pct"], [0.0, 0.0, 0.0, 0.0])
        self.assertEqual(frame["obs_in"][14:18], [0.0, 0.0, 0.0, 0.0])
        self.assertGreater(frame["obs_in"][13], 0.0)  # current grade remains observable

    def test_frame_exposes_step_input_time_at_road_transition(self):
        session = create_session(scenario="locked", preview=True, policy="current-grade", seed=2)
        session.env.k = 179
        result = step_session(session, steps=1)
        frame = result["frames"][0]
        self.assertEqual(frame["input_time_s"], 179.0)
        self.assertEqual(frame["time_s"], 180.0)
        self.assertAlmostEqual(frame["obs_in"][13], 0.0)
        self.assertAlmostEqual(frame["obs"][13], 0.12 * 12.0, places=5)

    def test_step_frames_are_finite_and_include_baseline_and_vehicle_gear(self):
        session = create_session(scenario="flat", preview=True, policy="baseline", seed=7)
        result = step_session(session, steps=2)
        frame = result["frames"][0]
        for name in ("time_s", "rpm", "map_kpa", "torque_req", "torque", "egt_c",
                     "t_turb", "t_oil", "t_block", "reward", "r_resp", "r_fuel",
                     "r_life", "cost_torque", "cost_knock", "cost_egt"):
            self.assertTrue(math.isfinite(frame[name]), name)
        self.assertIn(frame["gear"], range(1, 9))
        self.assertIn("baseline", frame)
        self.assertIn("totals", frame)
        self.assertEqual(len(frame["obs"]), 23)

    def test_locked_scenario_pins_source_evaluation_episode_one(self):
        first = create_session(scenario="locked", preview=True, policy="baseline", seed=123)
        second = create_session(scenario="locked", preview=True, policy="current-grade", seed=987)
        episode_seed, weights = EPISODES[0]
        self.assertEqual(len(first.env.cycle["t"]), int(EVAL_DURATION / EVAL_DT))
        self.assertEqual(first.provenance["episode"], 1)
        self.assertEqual(first.provenance["episode_seed"], episode_seed)
        self.assertEqual(first.provenance["weights_source"], "evaluate.EPISODES[0]")
        self.assertEqual(first.provenance["duration_s"], EVAL_DURATION)
        self.assertEqual(first.env.cycle["t"][0], 0.0)
        self.assertEqual(first.env.cycle["t"][-1], EVAL_DURATION - EVAL_DT)
        self.assertAlmostEqual(float(first.env.cycle["grade"][int(180 / EVAL_DT)]), 0.12)
        self.assertAlmostEqual(float(first.env.cycle["grade"][0]), 0.0)
        np.testing.assert_allclose(first.env.w, weights, rtol=0, atol=1e-7)
        np.testing.assert_allclose(second.env.w, weights, rtol=0, atol=1e-7)

    def test_controls_validate_before_mutating_session(self):
        session = create_session(scenario="locked", preview=True, policy="manual", seed=0)
        before_speed = session.env.cycle["v_mps"].copy()
        with self.assertRaises(ValueError):
            step_session(session, steps=1, controls={"speed_kmh": 999, "trims": [0] * 5})
        self.assertEqual(session.env.k, 0)
        self.assertEqual(session.env.cycle["v_mps"].tolist(), before_speed.tolist())

    def test_sandbox_vehicle_controls_patch_only_the_isolated_cycle(self):
        session = create_session(scenario="locked", preview=True, policy="manual", seed=3)
        result = step_session(session, steps=1, controls={
            "speed_kmh": 50, "grade_pct": 4, "ambient_c": 25,
            "trims": [0, 0, 0, 1, 1],
        })
        frame = result["frames"][0]
        self.assertAlmostEqual(frame["speed_kmh"], 50.0, places=5)
        self.assertAlmostEqual(frame["grade_pct"], 4.0, places=5)
        self.assertAlmostEqual(session.env.cycle["t_amb"], 298.15, places=5)

    def test_exported_actor_uses_matching_derived_data_and_is_labelled_unverified(self):
        session = create_session(scenario="flat", preview=True, policy="sighted_seed0", seed=9)
        self.assertTrue(session.provenance["derived_data_match"])
        self.assertTrue(session.provenance["educational_rerun_only"])
        self.assertEqual(session.provenance["code_fingerprint"], "unavailable")
        frame = step_session(session, steps=1)["frames"][0]
        self.assertEqual(len(frame["action"]), 5)
        self.assertTrue(all(math.isfinite(value) and -1 <= value <= 1 for value in frame["action"]))
        blind = create_session(scenario="flat", preview=True, policy="blind_seed0", seed=9)
        self.assertFalse(blind.preview)
        self.assertEqual(blind.env._obs()[14:18].tolist(), [0.0] * 4)

    def test_physical_action_conversion_obeys_policy_bounds(self):
        normalized = physical_to_normalized(ACT_HI.tolist())
        self.assertEqual(normalized, [1.0] * 5)
        normalized = physical_to_normalized(ACT_LO.tolist())
        self.assertEqual(normalized, [-1.0] * 5)
        with self.assertRaises(ValueError):
            physical_to_normalized([0, 0, 0, 1.1, 1])


if __name__ == "__main__":
    unittest.main()
