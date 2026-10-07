import sys
import json
import unittest
from pathlib import Path


EX_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(EX_ROOT))

from backend import catalog  # noqa: E402


class CatalogTests(unittest.TestCase):
    def test_metadata_has_source_derived_controller_contract(self):
        data = catalog.metadata()
        self.assertEqual([item["id"] for item in data["actions"]], [
            "spark_trim", "lambda_trim", "boost_trim", "fan_duty", "pump_duty"
        ])
        self.assertEqual([item["lo"] for item in data["actions"]], [-8.0, -0.15, -40.0, 0.0, 0.3])
        self.assertEqual([item["hi"] for item in data["actions"]], [4.0, 0.06, 15.0, 1.0, 1.0])
        self.assertEqual([item["slew"] for item in data["actions"]], [1.5, 0.03, 10.0, 0.25, 0.2])
        self.assertEqual(len(data["observations"]), 23)
        self.assertEqual(data["preview_s"], [2.0, 5.0, 15.0, 30.0])
        self.assertEqual([item["index"] for item in data["observations"]], list(range(23)))
        self.assertEqual([item["id"] for item in data["observations"]], [
            "rpm", "map", "tps", "spark", "lam", "t_block", "t_oil", "t_turb",
            "charge_temp", "ambient_temp", "barometric_pressure", "humidity", "speed",
            "grade", "preview_2s", "preview_5s", "preview_15s", "preview_30s",
            "torque_req", "aggression", "weight_tracking", "weight_fuel", "weight_life",
        ])
        self.assertAlmostEqual(data["vehicle"]["displacement_cc"], 2997.5, places=1)
        self.assertEqual(len(data["vehicle"]["gears"]), 8)
        self.assertTrue(all(item["source"]["line"] > 0 for item in data["actions"] + data["observations"]))
        self.assertGreaterEqual(len(data["concepts"]), 25)
        self.assertTrue(data["tour"])
        self.assertTrue(data["viva"])

    def test_metadata_matches_ui_concept_and_scenario_contract(self):
        data = catalog.metadata()
        concepts = {item["id"]: item for item in data["concepts"]}
        required = {
            "engine", "air", "map", "spark", "lam", "egt", "t_turb", "t_block",
            "t_oil", "grade", "gear", "torque_req", "preview", "agent", "fuel",
            "knock", "damage", "r_resp", "r_fuel", "r_life",
        }
        self.assertTrue(required.issubset(concepts))
        self.assertEqual({item["id"] for item in data["scenarios"]}, {"locked", "flat", "terrain"})
        self.assertEqual(concepts["spark"]["evidence_class"], "MODELLED")
        self.assertIn("trim", concepts["spark"]["meaning"].lower())
        self.assertEqual([item["id"] for item in data["observations"]][5:8], ["t_block", "t_oil", "t_turb"])
        self.assertEqual(concepts["t_block"]["evidence_class"], "MODELLED")
        self.assertEqual(concepts["t_oil"]["evidence_class"], "MODELLED")
        self.assertEqual(concepts["t_turb"]["evidence_class"], "MODELLED")

    def test_each_observation_opens_a_matching_concept(self):
        data = catalog.metadata()
        concept_ids = {item["id"] for item in data["concepts"]}
        self.assertEqual(len(data["observations"]), 23)
        self.assertTrue({item["id"] for item in data["observations"]}.issubset(concept_ids))
        self.assertGreaterEqual(len(data["viva"]), 13)
        for item in data["viva"]:
            focuses = item["focus"] if isinstance(item["focus"], list) else [item["focus"]]
            self.assertTrue(focuses, "Each viva question needs an inspectable target")
            self.assertTrue(all(isinstance(focus, str) and focus in concept_ids for focus in focuses))
        self.assertTrue({item.get("layer", "agent") for item in data["viva"]}.issubset({"vehicle", "engine", "turbo", "thermal", "agent"}))
        self.assertTrue(all(set(item["concepts"]).issubset(concept_ids) for item in data["tour"]))
        self.assertTrue(all(item["layer"] in {"vehicle", "engine", "turbo", "thermal", "agent"} for item in data["tour"]))
        self.assertEqual(data["observations"][3]["id"], "spark")
        self.assertIn("actual model", data["observations"][3]["meaning"].lower())
        self.assertIn("not relative humidity", data["observations"][11]["meaning"].lower())

    def test_all_causal_edges_resolve_to_catalog_concepts(self):
        concepts = {item["id"] for item in catalog.metadata()["concepts"]}
        for item in catalog.metadata()["concepts"]:
            self.assertTrue(set(item["upstream"]).issubset(concepts), item["id"])
            self.assertTrue(set(item["downstream"]).issubset(concepts), item["id"])

    def test_results_are_current_and_inconclusive_with_explicit_caveats(self):
        data = catalog.results()
        self.assertEqual(data["verdict"], "INCONCLUSIVE")
        self.assertEqual(data["freshness"]["set"], "terrain_dt1")
        self.assertAlmostEqual(data["index"]["ablation"]["ci95"][0], -4.439052814892159)
        self.assertAlmostEqual(data["premise"]["_preview_over_current_grade_pts"], -0.32, places=1)
        self.assertTrue(data["caveats"])
        self.assertTrue(data["sources"])
        self.assertEqual(data["freshness"]["current_plant_sha"], "c236a8db3e201090")
        self.assertEqual(data["freshness"]["replay_status"], "UNVERIFIED")
        self.assertIn("41.6 %", data["knock_margin"])
        self.assertEqual(data["verdict_evidence"]["n"], 10)
        self.assertAlmostEqual(data["verdict_evidence"]["mean"], 1.1693, places=4)
        self.assertAlmostEqual(data["verdict_evidence"]["ci95"][1], 6.777652814892162)
        self.assertAlmostEqual(data["verdict_evidence"]["p_t"], 0.648406012250384)
        self.assertAlmostEqual(data["verdict_evidence"]["p_wilcoxon"], 0.431640625)

    def test_source_returns_numbered_bounded_excerpt_and_rejects_traversal(self):
        excerpt = catalog.source("engine_env.py", 648)
        self.assertEqual(excerpt["file"], "engine_env.py")
        self.assertLessEqual(excerpt["end"] - excerpt["start"], 20)
        self.assertTrue(any(line["number"] == 648 for line in excerpt["lines"]))
        with self.assertRaises(ValueError):
            catalog.source("../secrets.txt", 1)
        with self.assertRaises(ValueError):
            catalog.source("engine_env.py", 0)

    def test_every_authored_concept_source_resolves_to_an_excerpt(self):
        data = catalog.metadata()
        refs = [(concept["id"], concept["source"]) for concept in data["concepts"]]
        refs += [(item["id"], item["source"]) for item in data["actions"] + data["observations"]]
        refs += [("vehicle", data["vehicle"]["source"])]
        for item_id, ref in refs:
            with self.subTest(item=item_id):
                excerpt = catalog.source(ref["file"], ref["line"])
                self.assertTrue(excerpt["lines"])
                self.assertIn(ref["line"], [row["number"] for row in excerpt["lines"]])


class FinalCatalogFixTests(unittest.TestCase):
    def test_damage_copy_separates_life_reward_rate_from_episode_integral(self):
        concepts = {item["id"]: item for item in catalog.metadata("en")["concepts"]}
        why = concepts["damage"]["why"].lower()
        self.assertRegex(why, r"life reward.*instantaneous damage rates")
        self.assertRegex(why, r"episode.*rate\s*[×*]\s*dt")
        self.assertIn("not measured component life", why)
        source = (catalog.PROJECT_ROOT / "engine_env.py").read_text(encoding="utf-8")
        self.assertIn("r_life = (d_b - d_a) / (d_b + 0.05)", source)
        self.assertIn('e["damage"] += d_a * self.dt', source)

    def test_thermal_causal_paths_and_signed_exchange_match_read_only_source(self):
        required = {"t_block": {"fuel", "t_oil", "ambient_temp"},
                    "t_oil": {"fuel", "ambient_temp", "t_block"}}
        for language in ("en", "ar"):
            concepts = {item["id"]: item for item in catalog.metadata(language)["concepts"]}
            for node, upstream in required.items():
                self.assertTrue(upstream.issubset(concepts[node]["upstream"]), (language, node))
            self.assertIn("t_block", concepts["t_oil"]["downstream"])
        english = {item["id"]: item for item in catalog.metadata("en")["concepts"]}
        self.assertRegex(english["t_turb"]["meaning"].lower(), r"gas.*cool")
        self.assertRegex(english["t_turb"]["meaning"].lower(), r"hotter.*colder")
        self.assertRegex(english["t_oil"]["increase"].lower(), r"hotter.*colder")
        authored = json.loads((EX_ROOT / "content.json").read_text(encoding="utf-8"))
        oil = next(item for item in authored["concepts"] if item["id"] == "t_oil")
        self.assertEqual(oil["source"]["line"], 220)
        source = (catalog.PROJECT_ROOT / "thermal.py").read_text(encoding="utf-8")
        for expression in ("q_in_turb = ua_gt * (egt_k - self.t_turb)",
                           "q_in_block = q_fuel * p.frac_fuel_to_coolant",
                           "q_in_oil = q_fuel * p.frac_fuel_to_oil",
                           "p.ua_block_oil * (self.t_block - self.t_oil)"):
            self.assertIn(expression, source)

    def test_seed_question_has_the_same_explicit_results_destination_in_both_catalogs(self):
        for language in ("en", "ar"):
            questions = catalog.metadata(language)["viva"]
            destinations = [item for item in questions if item.get("destination") == "seed-results"]
            self.assertEqual(len(destinations), 1, language)
            self.assertEqual(destinations[0]["focus"], "preview_result")


if __name__ == "__main__":
    unittest.main()
