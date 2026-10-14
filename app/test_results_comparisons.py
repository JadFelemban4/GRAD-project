"""Focused contract checks for the published comparison adapters."""
from __future__ import annotations

import json
import math
from pathlib import Path
import tempfile
import unittest

from app.results_comparisons import read_reference_panels


ROOT = Path(__file__).resolve().parents[1]
TMP = Path(__file__).resolve().parent / ".superpowers" / "training-linked-app" / "tmp"
EXPECTED = [*(f"G{i:02d}" for i in range(1, 7)), *(f"G{i:02d}" for i in range(14, 26))]


class ReferencePanelTests(unittest.TestCase):
    def test_real_published_sources_have_all_requested_views(self):
        panels = read_reference_panels(ROOT)
        self.assertEqual([p["id"] for p in panels], EXPECTED)
        by_id = {p["id"]: p for p in panels}
        for panel in panels:
            self.assertEqual(panel["state"], "available", (panel["id"], panel.get("reason")))
            self.assertIn(panel["state"], {"available", "unavailable", "withheld"})
            self.assertIsInstance(panel["source_files"], list)
            self.assertIsInstance(panel["caveats"], list)
            self.assertTrue(panel["revision"] or panel["state"] == "unavailable")
            if panel["state"] == "available":
                self.assertTrue(panel["source_files"])
                self.assertTrue(panel.get("series") or panel.get("channels") or panel.get("table"))
                for series in panel.get("series", []) + [s for channel in panel.get("channels", []) for s in channel["series"]]:
                    for point in series["points"]:
                        self.assertIn("source_index", point)
                        if point["source_index"] is None:
                            self.assertTrue(point.get("source_indices") or point.get("cell_index"))
                        else:
                            self.assertIsInstance(point["source_index"], int)
                        for key in ("x", "y", "low", "high", "value"):
                            if key in point and point[key] is not None:
                                self.assertTrue(math.isfinite(point[key]))
        self.assertEqual(by_id["G01"]["state"], "available")
        self.assertTrue(by_id["G01"]["series"][0]["points"])
        self.assertEqual(by_id["G14"]["state"], "available")
        self.assertTrue(by_id["G14"]["series"][0]["points"])
        self.assertEqual(len(by_id["G18"]["channels"]), 2)
        self.assertEqual(len(by_id["G20"]["channels"]), 2)
        self.assertTrue(by_id["G05"]["series"][0]["points"][0].get("value") is not None)
        self.assertTrue(by_id["G24"]["series"][0]["points"][0].get("value") is not None)
        self.assertTrue(by_id["G25"].get("table", {}).get("rows"))
        self.assertIn("STATUS_QUOTED_AS_RECORDED_NOT_A_CURRENT_VALIDATION_VERDICT", by_id["G25"]["caveats"])
        self.assertEqual(by_id["G01"]["intervals"][0]["source"].split(";")[0], "results/traces_130kmh.json:baseline ECU.grade")
        self.assertIn("TURBINE_THRESHOLD_NOT_RECORDED_IN_TRACE_SOURCE", by_id["G01"]["caveats"])
        self.assertEqual(by_id["G14"]["references"], [{"axis": "identity", "label": "identity", "source": "display reference y=x"}])
        self.assertEqual(by_id["G16"]["kind"], "heatmap")
        self.assertEqual(by_id["G16"]["channels"][0]["axes"]["x"]["ticks"][0]["label"],
                         json.loads((ROOT / "results/model_vs_data.json").read_text(encoding="utf-8"))["enrichment"]["cells"][0]["rpm"])
        self.assertEqual(by_id["G17"]["channels"][0]["id"], "residual")
        self.assertIn("before residual", by_id["G17"]["table"]["columns"])
        self.assertTrue(by_id["G21"]["channels"][0]["series"][0]["points"][0].get("source_indices"))
        density = by_id["G21"]["channels"][0]
        self.assertEqual(density["coverage"]["total"], 14318)
        self.assertEqual(density["coverage"]["excluded"], 1424)
        self.assertEqual(density["coverage"]["included"] + density["coverage"]["excluded"], 14318)
        self.assertEqual(sum(p["value"] for p in density["series"][0]["points"]), density["coverage"]["included"])
        self.assertTrue(all(ref["axis"] == "x" and "gearbox.published" in ref["source"] for ref in by_id["G22"]["references"]))
        self.assertEqual(by_id["G24"]["series"][1]["role"], "scenario")
        self.assertEqual(by_id["G25"]["context_sources"], ["validation_table.md", "VALIDATION_PLAN_REVIEW.md"])
        self.assertIn("VALIDATION_PLAN_DRAFT_NOT_ON_BRANCH_DECISIONS_PENDING_2026_10_07", by_id["G25"]["caveats"])

    def test_malformed_source_is_local_to_its_panels_and_bad_values_are_sanitized(self):
        TMP.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root = Path(name)
            (root / "results").mkdir()
            (root / "results" / "traces_130kmh.json").write_text("{bad json", encoding="utf-8")
            calibration = {
                "premise_steps": [{"step": "recorded", "baseline": float("nan"), "reactive": 2,
                                   "current_grade": 3, "predictive": 4}]
            }
            (root / "results" / "calibration_comparison.json").write_text(json.dumps(calibration), encoding="utf-8")
            panels = {p["id"]: p for p in read_reference_panels(root)}
            self.assertEqual(panels["G01"]["state"], "unavailable")
            self.assertEqual(panels["G02"]["state"], "unavailable")
            self.assertEqual(panels["G03"]["state"], "available")
            self.assertIsNone(panels["G03"]["series"][0]["points"][0]["y"])
            self.assertEqual(panels["G14"]["state"], "unavailable")

    def test_density_reports_every_excluded_pair_and_keeps_boundary_samples(self):
        with tempfile.TemporaryDirectory(dir=TMP) as name:
            root = Path(name)
            (root / "results").mkdir()
            recorded = {"knock": {"ki": [0, 1.6, -0.1, 1.7, 0.1, float("nan")],
                                   "retard": [-2, 20, 0, 0, 20.1, 0]},
                        "knock_sampling": {"samples": 6}}
            (root / "results/model_vs_data.json").write_text(json.dumps(recorded), encoding="utf-8")
            panel = next(p for p in read_reference_panels(root) if p["id"] == "G21")
            self.assertEqual(panel["state"], "available")
            density = panel["channels"][0]
            self.assertEqual(density["coverage"], {"total": 6, "included": 2, "excluded": 4,
                                                   "ki_range": [0, 1.6], "retard_range": [-2, 20]})
            self.assertEqual(sum(p["value"] for p in density["series"][0]["points"]), 2)
            self.assertEqual([p["source_indices"] for p in density["series"][0]["points"]], [[0], [1]])
            self.assertEqual(len(panel["series"][0]["points"]), 6)
            raw = next(c for c in panel["channels"] if c["id"] == "raw")
            self.assertEqual(raw["kind"], "scatter")
            self.assertEqual(raw["series"], panel["series"])

    def test_views_follow_published_comparison_contracts(self):
        panels = {p["id"]: p for p in read_reference_panels(ROOT)}
        traces = json.loads((ROOT / "results/traces_130kmh.json").read_text(encoding="utf-8"))
        positive = [i for i, value in enumerate(traces["baseline ECU"]["grade"]) if value > 0]
        interval = panels["G01"]["intervals"][0]
        self.assertEqual(interval["start"], traces["baseline ECU"]["t"][positive[0]])
        self.assertEqual(interval["end"], traces["baseline ECU"]["t"][positive[-1]])

        generality = json.loads((ROOT / "results/generality.json").read_text(encoding="utf-8"))
        self.assertEqual(panels["G04"]["series"][0]["points"][0]["y"],
                         generality["h2"][0]["predictive"] - generality["h2"][0]["grade"])
        self.assertEqual(panels["G04"]["table"]["rows"][0][4], generality["h2"][0]["predictive"])

        model = json.loads((ROOT / "results/model_vs_data.json").read_text(encoding="utf-8"))
        cell = model["enrichment"]["cells"][0]
        logged = panels["G16"]["channels"][0]["series"][0]["points"][0]
        self.assertEqual(logged["value"], cell["meas"])
        self.assertEqual(panels["G16"]["channels"][0]["axes"]["x"]["ticks"][0]["label"], cell["rpm"])
        spark = model["spark"]
        residual = panels["G17"]["channels"][0]["series"][0]["points"][0]
        self.assertEqual(residual["y"], spark["points"][0]["before"] - spark["points"][0]["meas"])
        self.assertEqual(panels["G17"]["published_metrics"]["before"]["rmse"], spark["before"]["rmse"])

        gear = model["gearbox"]
        self.assertEqual(panels["G22"]["references"][0]["value"], gear["published"][0])
        duty = model["duty"]
        scenario = panels["G24"]["series"][1]["points"][0]
        self.assertEqual((scenario["x"], scenario["y"]), (duty["scenario_rpm"], duty["scenario_map"]))
        self.assertEqual(panels["G25"]["table"]["rows"][0][6], "inside (as recorded)")


if __name__ == "__main__":
    unittest.main()
