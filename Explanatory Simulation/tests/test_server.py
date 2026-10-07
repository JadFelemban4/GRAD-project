import math
import sys
import unittest
from pathlib import Path

EX_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EX_ROOT.parent
sys.path.insert(0, str(EX_ROOT))
sys.path.insert(0, str(PROJECT_ROOT))

from fastapi.testclient import TestClient  # noqa: E402
from backend.server import app  # noqa: E402
from plant import boost_ceiling_kpa, charge_temperature, predict  # noqa: E402


class BridgeApiTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_session_step_returns_contract_fields_from_real_env(self):
        created = self.client.post("/api/session", json={
            "scenario": "locked", "preview": False, "policy": "manual", "seed": 11,
        })
        self.assertEqual(created.status_code, 200, created.text)
        body = created.json()
        self.assertEqual(len(body["frame"]["obs"]), 23)
        self.assertEqual(len(body["road"]["grade_pct"]), 720)
        self.assertEqual(body["provenance"]["episode"], 1)
        self.assertEqual(body["provenance"]["weights_source"], "evaluate.EPISODES[0]")
        step = self.client.post(f"/api/session/{body['id']}/step", json={
            "steps": 1, "controls": {"trims": [0, 0, 0, 1, 1]},
        })
        self.assertEqual(step.status_code, 200, step.text)
        frame = step.json()["frames"][0]
        for field in ("time_s", "rpm", "map_kpa", "speed_kmh", "grade_pct", "gear",
                      "torque_req", "torque", "egt_c", "t_turb", "t_oil", "t_block",
                      "spark", "lam", "mdot_fuel", "mdot_air", "ki", "damage_rate",
                      "reward", "r_resp", "r_fuel", "r_life", "cost_torque", "cost_knock",
                      "cost_egt", "action", "requested", "command", "obs", "obs_in",
                      "preview_pct", "baseline", "totals"):
            self.assertIn(field, frame)
        self.assertEqual(frame["preview_pct"], [0, 0, 0, 0])
        self.assertEqual(step.json()["done"], False)

        controlled = self.client.post(f"/api/session/{body['id']}/step", json={
            "steps": 1, "controls": {"speed_kmh": 50, "grade_pct": 4},
        })
        self.assertEqual(controlled.status_code, 200, controlled.text)
        self.assertEqual(len(controlled.json()["road"]["grade_pct"]), 720)
        self.assertAlmostEqual(controlled.json()["road"]["grade_pct"][1], 4.0, places=5)
        self.assertTrue(controlled.json()["road"]["customized"])
        self.assertEqual(controlled.json()["road"]["nominal_grade_pct"], 4.0)

    def test_invalid_vehicle_controls_are_rejected_without_a_partial_step(self):
        created = self.client.post("/api/session", json={"policy": "manual"}).json()
        response = self.client.post(f"/api/session/{created['id']}/step", json={
            "steps": 1, "controls": {"speed_kmh": 300, "grade_pct": 10},
        })
        self.assertEqual(response.status_code, 422)
        next_step = self.client.post(f"/api/session/{created['id']}/step", json={"steps": 1})
        self.assertEqual(next_step.status_code, 200)
        self.assertEqual(next_step.json()["frames"][0]["speed_kmh"], 0.0)

    def test_plant_endpoint_uses_source_predict_with_temperature_units_converted(self):
        body = {"rpm": 3000, "map_kpa": 250, "ambient_c": 35, "ect_c": 90,
                "spark": 8, "lam": 0.95}
        got = self.client.post("/api/plant", json=body)
        self.assertEqual(got.status_code, 200, got.text)
        iat_k = charge_temperature(308.15)
        expected = predict(3000, 250, iat_k, 363.15, 8, 0.95)
        self.assertAlmostEqual(got.json()["torque_nm"], expected["torque_nm"], places=6)
        self.assertAlmostEqual(got.json()["iat_k"], iat_k, places=6)
        self.assertAlmostEqual(got.json()["charge_temp_c"], iat_k - 273.15, places=6)
        self.assertIn("no block-temperature input", got.json()["charge_temp_source"])
        self.assertAlmostEqual(got.json()["observed_ceiling_kpa"],
                               boost_ceiling_kpa(expected["mdot_air_gps"], 308.15), places=6)
        self.assertGreater(got.json()["map_over_ceiling_kpa"], 0.0)
        self.assertTrue(any("not vehicle-feasible" in warning for warning in got.json()["warnings"]))

    def test_built_ui_is_served_from_loopback_api_when_dist_exists(self):
        index = EX_ROOT / "dist" / "index.html"
        if not index.is_file():
            self.skipTest("production dist has not been built")
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertIn("مختبر السوبرا", response.text)
        self.assertIn('lang="ar"', response.text)
        self.assertIn('dir="rtl"', response.text)
        self.assertIn("/assets/", response.text)
        assets = list((EX_ROOT / "dist" / "assets").iterdir())
        self.assertTrue(assets)

    def test_thermal_endpoint_returns_finite_thermal_network_frames(self):
        response = self.client.post("/api/thermal", json={
            "rpm": 3000, "map_kpa": 150, "ambient_c": 35, "spark": 8,
            "lam": 0.95, "fan": 0.7, "pump": 0.8, "heat_s": 2.0, "cool_s": 2.0,
        })
        self.assertEqual(response.status_code, 200, response.text)
        body = response.json()
        self.assertTrue(body["teaching_experiment"])
        self.assertEqual(body["initial_state"], "cold_start_at_ambient")
        self.assertIn("charge_temperature", body["method"])
        self.assertIn("ECT=ambient", body["method"])
        self.assertLessEqual(body["frames"][-1]["time_s"], 4.0)
        self.assertIsNone(body["frames"][0]["egt_c"])
        self.assertAlmostEqual(body["frames"][0]["exhaust_boundary_c"], 35.0)
        for frame in body["frames"]:
            for key in ("t_turb", "t_oil", "t_block"):
                self.assertTrue(math.isfinite(frame[key]), (key, frame))
            if frame["phase"] == "heating":
                self.assertTrue(math.isfinite(frame["egt_c"]))
                self.assertIsNone(frame["exhaust_boundary_c"])
            else:
                self.assertIsNone(frame["egt_c"])
                self.assertEqual(frame["exhaust_boundary_c"], 35.0)

    def test_catalog_endpoints_use_current_data_and_source_allowlist(self):
        meta = self.client.get("/api/meta")
        self.assertEqual(meta.status_code, 200, meta.text)
        self.assertEqual(meta.json()["bridge"]["host"], "127.0.0.1")
        results = self.client.get("/api/results")
        self.assertEqual(results.status_code, 200, results.text)
        self.assertIn("INCONCLUSIVE", str(results.json()).upper())
        excerpt = self.client.get("/api/source", params={"file": "engine_env.py", "line": 671})
        self.assertEqual(excerpt.status_code, 200, excerpt.text)
        self.assertTrue(all("number" in item and "text" in item for item in excerpt.json()["lines"]))
        blocked = self.client.get("/api/source", params={"file": "../engine_env.py", "line": 1})
        self.assertEqual(blocked.status_code, 400)

    def test_replay_endpoint_accepts_only_catalogued_trip_ids(self):
        response = self.client.post("/api/replay", json={"trip_id": "../../secret.csv"})
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
