from __future__ import annotations
import json
from pathlib import Path
import shutil
import tempfile
import unittest
try:
    from app import results_sets
except ImportError:
    results_sets = None

APP_ROOT = Path(__file__).resolve().parent
TMP_ROOT = APP_ROOT / ".superpowers" / "training-linked-app" / "tmp"

def _summary(policy):
    base = 10.0 if policy.startswith("sighted") else 12.0 if policy.startswith("blind") else 20.0
    if policy == "baseline ECU": base = 25.0
    metrics = {name: {"median": value, "q1": value-1, "q3": value+1, "worst": value+5, "best": value-2}
               for name, value in (("damage", base), ("damage_thermal", base-1), ("fuel", 100+base))}
    summary = {**metrics, "cut_pct": base, "thermal_cut_pct": base-1, "fuel_vs_baseline_pct": 0.0}
    summary.update({name: {"median": base, "q1": base-1, "q3": base+1, "worst": base+5, "best": base-2}
                    for name in ("ret", "torque_viol", "peak_turb", "knock")})
    actions = {}
    for name in ("spark trim (deg)", "lambda trim", "boost trim (kPa)", "fan duty", "pump duty"):
        actions[name] = {"neutral": 0.0, "flat": {"mean": .1, "p5": -.2, "p50": 0.0, "p95": .3},
                         "climb": {"mean": .2, "p5": -.1, "p50": .1, "p95": .4}, "slew_limited_pct": 1.0}
    return {"policy": policy, "protocol": "protocol fixture", "episodes": [
        {"damage": base+5, "damage_thermal": base+4, "fuel": 100+base+5},
        {"damage": base, "damage_thermal": base-1, "fuel": 100+base}],
        "summary": summary, "actions": actions}

class AgentSetPanelTests(unittest.TestCase):
    def test_reader_module_is_available(self): self.assertIsNotNone(results_sets)
    def setUp(self):
        TMP_ROOT.mkdir(parents=True, exist_ok=True)
        self.temp = Path(tempfile.mkdtemp(prefix="results_sets_", dir=TMP_ROOT))
        self.set_dir = self.temp / "results" / "agents" / "fixture"
        self.set_dir.mkdir(parents=True)
        names = ["baseline ECU", "sighted_seed0", "blind_seed0", "sighted_seed2"]
        policies = {}
        for name in names:
            folder = name.replace(" ", "_").replace("(", "").replace(")", "")
            member = self.set_dir / folder
            member.mkdir()
            record = _summary(name)
            config = {"git_head": "abc123", "git_commit": "abc123", "output": f"runs/fixture/{folder}",
                      "protocol": "protocol fixture", "plant_sha": "plant-hash", "derived_sha": None,
                      "recorded_steps": 100, "scenario": "fixture scenario",
                      "seed": int(name.rsplit("seed", 1)[1]) if "seed" in name else None,
                      "git_dirty": False}
            (member / "eval_summary.json").write_text(json.dumps(record), encoding="utf-8")
            (member / "config.json").write_text(json.dumps(config), encoding="utf-8")
            (member / "curve.csv").write_text("episode,return,length\n0,-1,10\n1,2,10\n", encoding="utf-8")
            policies[name] = {**record["summary"], "actions": record["actions"], "config": config}
        (self.set_dir / "index.json").write_text(json.dumps({"set": "fixture", "generated": "2026-10-08 12:00",
             "policies": policies, "ablation": {"secret": True}, "findings": ["secret"]}), encoding="utf-8")
        knock = {name: {"cut_orig": _summary(name)["summary"]["cut_pct"], "cut": 1.0, "seed": 0}
                 for name in ("sighted_seed0", "blind_seed0", "sighted_seed2")}
        (self.set_dir / "knock_margin.json").write_text(json.dumps({"agents": knock}), encoding="utf-8")
    def tearDown(self): shutil.rmtree(self.temp)
    def _set(self): return results_sets.read_agent_sets(self.temp)[0]
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_emits_six_published_panels_with_recorded_quartiles_and_pairing(self):
        record = self._set(); panels = {p["id"]: p for p in record["panels"]}
        self.assertEqual(set(panels), {"G07", "G08", "G09", "G10", "G12", "G13"})
        point = next(s["points"][0] for s in panels["G07"]["series"]
                     if s["id"] == "sighted_seed0" and s["role"] == "median")
        self.assertEqual((point["y"], point["low"], point["high"]), (10.0, 9.0, 11.0))
        self.assertEqual(point["seed"], 0)
        worst = next(s["points"][0] for s in panels["G07"]["series"]
                     if s["id"] == "sighted_seed0" and s["role"] == "worst")
        self.assertEqual((worst["y"], worst["episode"], worst["seed"]), (15.0, 0, 0))
        baseline = next(s["points"][0] for s in panels["G07"]["series"]
                        if s["id"] == "baseline ECU" and s["role"] == "median")
        self.assertNotIn("seed", baseline)
        self.assertTrue(any(p.get("seed") == 0 for s in panels["G08"]["channels"][0]["series"] for p in s["points"]))
        self.assertEqual(panels["G09"]["state"], "available")
        self.assertEqual(len(panels["G10"]["channels"]), 5)
        self.assertEqual(panels["G12"]["kind"], "scatter")
        self.assertEqual(panels["G13"]["series"][0]["points"][1]["episode"], 1)
        self.assertNotIn("secret", json.dumps(record))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_membership_comes_from_index_and_mismatch_is_reported(self):
        p=self.set_dir/"index.json"; i=json.loads(p.read_text()); del i["policies"]["sighted_seed0"]; p.write_text(json.dumps(i))
        (self.set_dir/"sighted_seed0"/"eval_summary.json").unlink()
        record=self._set()
        self.assertNotIn("sighted_seed0", json.dumps(record["panels"]))
        self.assertTrue(any(x.get("code")=="stale_policy_folder" for x in record["issues"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_index_summary_must_match_member_summary(self):
        p=self.set_dir/"index.json"; i=json.loads(p.read_text())
        i["policies"]["sighted_seed0"]["damage"]["median"] += 1
        p.write_text(json.dumps(i))
        record=self._set()
        self.assertTrue(any(x.get("code")=="summary_mismatch" for x in record["issues"]))
        panel={x["id"]:x for x in record["panels"]}["G07"]
        self.assertFalse(any(s["id"]=="sighted_seed0" for s in panel["series"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_knock_panel_is_withheld_when_cut_orig_disagrees(self):
        p=self.set_dir/"knock_margin.json"; k=json.loads(p.read_text()); k["agents"]["sighted_seed0"]["cut_orig"]=-500; p.write_text(json.dumps(k))
        panel={x["id"]:x for x in self._set()["panels"]}["G09"]
        self.assertEqual(panel["state"],"withheld"); self.assertIn("knock_cut_mismatch",panel["caveats"])
        self.assertIn("diagnostic_spark_cap_not_retrained",panel["caveats"])
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_config_identity_mismatch_excludes_member_and_surfaces_omission(self):
        p=self.set_dir/"sighted_seed0"/"config.json"; config=json.loads(p.read_text())
        config["git_commit"]="different-commit"; p.write_text(json.dumps(config))
        record=self._set(); panel={x["id"]:x for x in record["panels"]}["G07"]
        self.assertTrue(any(x.get("code")=="config_mismatch" for x in record["issues"]))
        self.assertFalse(any(s["id"]=="sighted_seed0" for s in panel["series"]))
        self.assertTrue(any(x.get("policy")=="sighted_seed0" for x in panel["omissions"]))
        panels={x["id"]:x for x in record["panels"]}
        self.assertTrue(any(row[0]==0 and row[3]=="config_mismatch" for row in panels["G08"]["table"]["rows"]))
        self.assertFalse(any(point.get("label")=="sighted_seed0" for ch in panels["G12"]["channels"]
                             for series in ch["series"] for point in series["points"]))
        self.assertFalse(any(s["id"]=="sighted_seed0" for s in panels["G13"]["series"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_unpaired_seed_is_visible_in_g08_table(self):
        panel={x["id"]:x for x in self._set()["panels"]}["G08"]
        self.assertIn("unpaired_seeds",panel["caveats"])
        self.assertTrue(any(row[0]==2 for row in panel["table"]["rows"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_g10_preserves_policy_positions_and_region_specific_gaps(self):
        p=self.set_dir/"baseline_ECU"/"eval_summary.json"; r=json.loads(p.read_text())
        del r["actions"]["spark trim (deg)"]["flat"]; p.write_text(json.dumps(r))
        p=self.set_dir/"sighted_seed0"/"eval_summary.json"; r=json.loads(p.read_text())
        del r["actions"]["spark trim (deg)"]["climb"]; p.write_text(json.dumps(r))
        panel={x["id"]:x for x in self._set()["panels"]}["G10"]
        channel=next(x for x in panel["channels"] if x["id"]=="spark_trim")
        flat=next(x for x in channel["series"] if x["id"]=="flat")["points"]
        climb=next(x for x in channel["series"] if x["id"]=="climb")["points"]
        self.assertEqual(next(p["x"] for p in flat if p["label"]=="sighted_seed0"),1)
        self.assertNotIn("sighted_seed0",[p["label"] for p in climb])
        self.assertTrue(any(x.get("policy")=="baseline ECU" and x.get("region")=="flat" for x in panel["omissions"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_g10_is_withheld_for_mixed_evaluation_protocols(self):
        p=self.set_dir/"blind_seed0"/"eval_summary.json"; r=json.loads(p.read_text())
        r["protocol"]="other protocol"; p.write_text(json.dumps(r))
        cp=self.set_dir/"blind_seed0"/"config.json"; c=json.loads(cp.read_text()); c["protocol"]="other protocol"; cp.write_text(json.dumps(c))
        ip=self.set_dir/"index.json"; i=json.loads(ip.read_text()); i["policies"]["blind_seed0"]["config"]=c; ip.write_text(json.dumps(i))
        panel={x["id"]:x for x in self._set()["panels"]}["G10"]
        self.assertEqual(panel["state"],"withheld")
        self.assertIn("protocol_mismatch",panel["caveats"])
        self.assertFalse(any(ch["series"] for ch in panel["channels"]))
    @unittest.skipIf(results_sets is None, "results_sets reader has not been implemented")
    def test_training_curve_reader_is_confined_to_repo(self):
        curve=self.set_dir/"sighted_seed0"/"curve.csv"
        panels=results_sets.read_training_panels(curve.parent,self.temp)
        self.assertEqual(panels[0]["id"],"G13")
        outside=self.temp.parent/"outside-run"; outside.mkdir(exist_ok=True)
        try:
            with self.assertRaises(ValueError): results_sets.read_training_panels(outside,self.temp)
        finally: outside.rmdir()

if __name__ == "__main__": unittest.main()




