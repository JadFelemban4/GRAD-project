"""Temporary-fixture tests for the read-only artifact registry."""
from __future__ import annotations

import json
import hashlib
import os
import sys
import tempfile
import types
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from app.artifact_catalog import ArtifactCatalog
from app.artifact_readiness import duplicated_metrics_match


def write_json(path: Path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def model_zip(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("data", json.dumps({
            "num_timesteps": 20, "_total_timesteps": 20,
            "_num_timesteps_at_start": 0, "buffer_size": 100,
        }))


def write_meta(path: Path, arm: str, seed: int, protocol="phase-d"):
    write_json(path / "meta.json", {"tag": f"{arm}_seed{seed}", "seed": seed,
                                     "use_preview": arm == "sighted", "steps_requested": 20,
                                     "train_road": "terrain",
                                     "scenario": {"protocol": protocol}})


class ArtifactCatalogTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.now = [10.0]
        self.catalog = ArtifactCatalog(self.root, clock=lambda: self.now[0],
                                       running_pid=lambda _path: None)

    def tearDown(self):
        self.tmp.cleanup()

    def stable_scan(self):
        self.catalog.scan()
        self.now[0] += 1.1
        self.catalog.scan()
        self.now[0] += 1.1
        return self.catalog.scan()

    def item(self, snapshot, rel):
        return next(x for x in snapshot["items"] if x["relative_path"] == rel)

    def test_discovers_nested_future_run_and_reports_individual_arms(self):
        base = self.root / "runs" / "future_set"
        for arm in ("sighted", "blind"):
            d = base / f"{arm}_seed0"
            write_json(d / "config.json", {"tag": f"{arm}_seed0", "seed": 0,
                                             "preview": arm == "sighted", "steps": 50_000,
                                             "status": "running"})
            (d / "RUNNING").write_text('{"pid": 123}', encoding="utf-8")
        self.catalog = ArtifactCatalog(self.root, clock=lambda: self.now[0],
                                       running_pid=lambda _path: 123)
        snap = self.stable_scan()
        run = self.item(snap, "runs/future_set")
        self.assertEqual(run["kind"], "run_pair")
        self.assertEqual(run["lifecycle"], "running")
        self.assertFalse(run["compatibility"]["replay_allowed"])
        self.assertEqual({(x["seed"], x["arm"]) for x in run["members"]},
                         {(0, "sighted"), (0, "blind")})

    def test_flat_pair_and_half_pair_are_not_confused(self):
        base = self.root / "runs_flat"
        for arm in ("sighted", "blind"):
            d = base / f"{arm}_seed1"
            model_zip(d / "final.zip")
            write_json(d / "config.json", {"tag": f"{arm}_seed1", "seed": 1,
                                             "preview": arm == "sighted", "steps": 20,
                                             "status": "finished", "total_timesteps": 20,
                                             "episodes": 1, "recorded_steps": 0})
            write_meta(d, arm, 1)
        snap = self.stable_scan()
        run = self.item(snap, "runs_flat")
        self.assertEqual(run["lifecycle"], "finished")
        self.assertTrue(run["capabilities"]["model"])
        self.assertEqual(len(run["pairs"]), 1)

        import shutil
        shutil.rmtree(base / "blind_seed1")
        self.catalog.scan()
        self.now[0] += 1.1
        self.catalog.scan()
        self.now[0] += 1.1
        snap = self.catalog.scan()
        run = self.item(snap, "runs_flat")
        pair = run["pairs"][0]
        self.assertFalse(pair["comparable"])
        self.assertEqual(pair["missing_arms"], ["blind"])

    def test_final_zip_alone_is_finalizing_not_finished(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        snap = self.stable_scan()
        agent = self.item(snap, "runs_x")["members"][0]
        self.assertEqual(agent["lifecycle"], "finalizing")
        self.assertFalse(agent["capabilities"]["training_curve"])

    def test_modern_finished_config_requires_consistent_meta(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "config.json", {"tag": "sighted_seed0", "seed": 0,
                                         "preview": True, "steps": 20,
                                         "status": "finished", "total_timesteps": 20,
                                         "episodes": 1, "recorded_steps": 0})
        agent = self.item(self.stable_scan(), "runs_x")["members"][0]
        self.assertEqual(agent["lifecycle"], "finalizing")

    def test_unknown_protocol_is_visible_but_never_replayable(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "meta.json", {"scenario": {"protocol": "future-protocol"}})
        write_json(d / "config.json", {"status": "finished", "steps": 20,
                                         "total_timesteps": 20, "episodes": 0,
                                         "recorded_steps": 0})
        write_meta(d, "sighted", 0, protocol="future-protocol")
        agent = self.item(self.stable_scan(), "runs_x")["members"][0]
        self.assertEqual(agent["protocol"], "future-protocol")
        self.assertFalse(agent["compatibility"]["replay_allowed"])
        self.assertIn("unknown", agent["compatibility"]["reason"].lower())

    def test_random_climb_protocol_alias_maps_to_d2(self):
        d = self.root / "runs_alias" / "sighted_seed0"
        write_json(d / "meta.json", {"scenario": {"protocol": "random-climb"}})
        agent = self.item(self.stable_scan(), "runs_alias")["members"][0]
        self.assertEqual(agent["protocol"], "d2")

    def test_missing_protocol_in_recorded_scenario_maps_to_phase_d(self):
        d = self.root / "runs_legacy" / "sighted_seed0"
        write_json(d / "meta.json", {"scenario": {"grade": 0.12}})
        agent = self.item(self.stable_scan(), "runs_legacy")["members"][0]
        self.assertEqual(agent["protocol"], "phase-d")

    def test_live_running_pid_overrides_existing_finished_files(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "config.json", {"status": "finished", "steps": 20,
                                         "total_timesteps": 20, "episodes": 0,
                                         "recorded_steps": 0})
        write_meta(d, "sighted", 0)
        catalog = ArtifactCatalog(self.root, clock=lambda: self.now[0],
                                  running_pid=lambda _path: 77)
        catalog.scan(); self.now[0] += 1.1
        agent = next(x for x in catalog.scan()["items"]
                     if x["relative_path"] == "runs_x")["members"][0]
        self.assertEqual(agent["lifecycle"], "running")

    def test_stale_running_marker_is_interrupted_even_with_model(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "config.json", {"status": "running", "steps": 20})
        (d / "RUNNING").write_text('{"pid": 999}', encoding="utf-8")
        agent = self.item(self.stable_scan(), "runs_x")["members"][0]
        self.assertEqual(agent["lifecycle"], "interrupted")

    def test_results_only_set_and_index_membership_validation(self):
        s = self.root / "results" / "agents" / "fixture_set"
        write_json(s / "index.json", {"set": "fixture_set", "policies": {
            "policy A": {"damage": {"median": 3.5}}}})
        write_json(s / "policy_A" / "eval_summary.json", {
            "policy": "policy A", "summary": {"damage": {"median": 3.5}}})
        snap = self.stable_scan()
        item = self.item(snap, "results/agents/fixture_set")
        self.assertEqual(item["kind"], "agent_set")
        self.assertEqual(len(item["members"]), 1)
        self.assertFalse(item["members"][0]["capabilities"]["model"])
        self.assertEqual(item["members"][0]["lifecycle"], "finished")

        write_json(s / "policy_A" / "eval_summary.json", {
            "policy": "policy A", "summary": {"damage": {"median": 999}}})
        pending = self.item(self.stable_scan(), "results/agents/fixture_set")
        self.assertIn(pending["coherence"], {"updating / last valid snapshot", "error"})
        self.assertTrue(pending["capabilities"]["evaluation_summary"])
        self.assertEqual(pending["members"][0]["summary"]["damage"]["median"], 3.5)
        (s / "policy_A" / "eval_summary.json").write_text("{", encoding="utf-8")
        corrupt = self.item(self.stable_scan(), "results/agents/fixture_set")
        self.assertEqual(corrupt["coherence"], "updating / last valid snapshot")
        self.assertEqual(corrupt["members"][0]["summary"]["damage"]["median"], 3.5)
        (s / "policy_A" / "eval_summary.json").unlink()
        deleted = self.item(self.stable_scan(), "results/agents/fixture_set")
        self.assertEqual(deleted["coherence"], "updating / last valid snapshot")
        self.assertEqual(deleted["members"][0]["summary"]["damage"]["median"], 3.5)

    def test_invalid_set_index_schema_keeps_last_valid_item_until_recovery(self):
        s = self.root / "results" / "agents" / "fixture_set"
        index_path = s / "index.json"
        write_json(index_path, {"set": "fixture_set", "policies": {
            "policy A": {"damage": {"median": 3.5}}}})
        write_json(s / "policy_A" / "eval_summary.json", {
            "policy": "policy A", "summary": {"damage": {"median": 3.5}}})
        valid = self.item(self.stable_scan(), "results/agents/fixture_set")

        for malformed in ({}, [], {"policies": []}):
            write_json(index_path, malformed)
            pending = self.stable_scan()
            item = self.item(pending, "results/agents/fixture_set")
            self.assertEqual(item["coherence"], "updating / last valid snapshot")
            self.assertTrue(pending["updating"])
            self.assertEqual(item["revision"], valid["revision"])
            self.assertEqual(item["members"], valid["members"])
            self.assertEqual(item["capabilities"], valid["capabilities"])
            self.assertTrue(item["issues"])

        write_json(index_path, {"set": "fixture_set", "policies": {
            "policy A": {"damage": {"median": 4.0}}}})
        write_json(s / "policy_A" / "eval_summary.json", {
            "policy": "policy A", "summary": {"damage": {"median": 4.0}}})
        recovered = self.item(self.stable_scan(), "results/agents/fixture_set")
        self.assertEqual(recovered["coherence"], "current")
        self.assertEqual(recovered["members"][0]["summary"]["damage"]["median"], 4.0)

    def test_invalid_set_index_without_prior_snapshot_is_explicit_error(self):
        s = self.root / "results" / "agents" / "new_set"
        write_json(s / "index.json", {"policies": []})
        item = self.item(self.stable_scan(), "results/agents/new_set")
        self.assertEqual(item["coherence"], "error")
        self.assertEqual(item["lifecycle"], "unknown")
        self.assertIn("policies", " ".join(item["issues"]))

    def test_all_duplicated_policy_metrics_actions_and_finite_values_match(self):
        policy = {"damage": {"median": 1.0, "q1": 0.5, "q3": 1.5,
                             "worst": 2.0, "best": 0.1},
                  "cut_pct": 20.0,
                  "actions": {"spark": {"flat": {"mean": 1.0, "p5": 0.0}}}}
        summary = {"policy": "p", "summary": {
            "damage": {"median": 1.0, "q1": 0.5, "q3": 1.5, "worst": 2.0, "best": 0.1},
            "cut_pct": 20.0},
            "actions": {"spark": {"flat": {"mean": 1.0, "p5": 0.0}}}}
        self.assertTrue(duplicated_metrics_match(policy, summary, "p"))
        bad_q1 = json.loads(json.dumps(summary)); bad_q1["summary"]["damage"]["q1"] = 999
        self.assertFalse(duplicated_metrics_match(policy, bad_q1, "p"))
        bad_worst = json.loads(json.dumps(summary)); bad_worst["summary"]["damage"]["worst"] = 999
        self.assertFalse(duplicated_metrics_match(policy, bad_worst, "p"))
        bad_cut = json.loads(json.dumps(summary)); bad_cut["summary"]["cut_pct"] = 999
        self.assertFalse(duplicated_metrics_match(policy, bad_cut, "p"))
        bad_action = json.loads(json.dumps(summary)); bad_action["actions"]["spark"]["flat"]["p5"] = 999
        self.assertFalse(duplicated_metrics_match(policy, bad_action, "p"))
        nonfinite = json.loads(json.dumps(summary)); nonfinite["summary"]["damage"]["median"] = float("nan")
        self.assertFalse(duplicated_metrics_match(policy, nonfinite, "p"))
        with_config = dict(policy, config={"seed": 1})
        self.assertTrue(duplicated_metrics_match(with_config, summary, "p", {"seed": 1}))
        self.assertFalse(duplicated_metrics_match(with_config, summary, "p", {"seed": 2}))

    def test_evaluation_text_discovered_and_corrupt_json_isolated(self):
        (self.root / "results").mkdir()
        (self.root / "results" / "phase_seed0.txt").write_text("score: 1\n", encoding="utf-8")
        d = self.root / "runs_bad" / "sighted_seed0"
        d.mkdir(parents=True)
        (d / "config.json").write_text("{", encoding="utf-8")
        snap = self.stable_scan()
        text_item = self.item(snap, "results/phase_seed0.txt")
        self.assertTrue(text_item["capabilities"]["evaluation_summary"])
        self.assertFalse(text_item["capabilities"]["verdict"])
        self.assertTrue(any(x["relative_path"] == "runs_bad" and x["issues"] for x in snap["items"]))

    def test_changed_file_requires_two_observations_and_pre_post_race_isolated(self):
        d = self.root / "runs_x" / "sighted_seed0"
        d.mkdir(parents=True)
        cfg = d / "config.json"
        write_json(cfg, {"status": "finished", "steps": 4, "total_timesteps": 4,
                         "episodes": 1, "recorded_steps": 0})
        first = self.catalog.scan()
        self.assertEqual(self.item(first, "runs_x")["members"][0]["lifecycle"], "unknown")
        self.assertIn("awaiting stable", self.item(first, "runs_x")["issues"][0])
        self.now[0] += 1.1
        second = self.catalog.scan()
        self.assertEqual(self.item(second, "runs_x")["members"][0]["lifecycle"], "finalizing")
        self.assertNotIn("awaiting stable", self.item(second, "runs_x")["issues"][0])

    def test_unknown_resolve_is_refused_and_contained_paths_resolve(self):
        base = self.root / "runs_x" / "sighted_seed0"
        base.mkdir(parents=True)
        snap = self.stable_scan()
        artifact_id = self.item(snap, "runs_x")["id"]
        self.assertEqual(self.catalog.resolve(artifact_id), (self.root / "runs_x").resolve())
        with self.assertRaises(KeyError):
            self.catalog.resolve("../../outside")

    def test_escaping_symlink_is_skipped(self):
        outside = Path(self.tmp.name).parent / (Path(self.tmp.name).name + "_outside")
        outside.mkdir(exist_ok=True)
        try:
            runs = self.root / "runs_escape"
            runs.mkdir()
            link = runs / "sighted_seed0"
            try:
                link.symlink_to(outside, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("directory symlinks are unavailable")
            snap = self.stable_scan()
            self.assertNotIn("runs_escape", [x["relative_path"] for x in snap["items"]])
        finally:
            try:
                outside.rmdir()
            except OSError:
                pass

    def test_unchanged_scan_does_not_rehash_model_or_change_revisions(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "config.json", {"status": "finished", "steps": 20,
                                         "total_timesteps": 20, "episodes": 0,
                                         "recorded_steps": 0})
        write_meta(d, "sighted", 0)
        with patch("app.artifact_catalog.FP.model_budget", wraps=__import__("fingerprint").model_budget) as budget:
            first = self.stable_scan()
            first_calls = budget.call_count
            self.now[0] += 2
            second = self.catalog.scan()
            self.assertEqual(budget.call_count, first_calls)
        self.assertEqual(first["revision"], second["revision"])
        self.assertEqual(self.catalog.snapshot(), second)

    def test_atomic_same_size_model_replacement_with_restored_mtime_changes_identity(self):
        base = self.root / "runs_x"
        for arm in ("sighted", "blind"):
            directory = base / f"{arm}_seed0"
            model_zip(directory / "final.zip")
            write_json(directory / "config.json", {"status": "finished", "steps": 20,
                                                     "total_timesteps": 20, "episodes": 0,
                                                     "recorded_steps": 0})
            write_meta(directory, arm, 0)
        first = self.stable_scan()
        first_run = self.item(first, "runs_x")
        first_member = next(member for member in first_run["members"] if member["arm"] == "sighted")

        model = base / "sighted_seed0" / "final.zip"
        original_stat = model.stat()
        replacement = model.with_suffix(".replacement")
        with zipfile.ZipFile(replacement, "w") as zf:
            zf.writestr("data", json.dumps({
                "num_timesteps": 21, "_total_timesteps": 21,
                "_num_timesteps_at_start": 0, "buffer_size": 100,
            }))
        self.assertEqual(replacement.stat().st_size, original_stat.st_size)
        os.replace(replacement, model)
        os.utime(model, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

        self.catalog.scan()
        self.now[0] += 1.1
        after = self.catalog.scan()
        after_run = self.item(after, "runs_x")
        after_member = next(member for member in after_run["members"] if member["arm"] == "sighted")
        self.assertNotEqual(after_member["model_identity"], first_member["model_identity"])
        self.assertNotEqual(after_run["revision"], first_run["revision"])

    def test_atomic_same_size_json_replacement_with_restored_mtime_changes_revision(self):
        base = self.root / "runs_json"
        for arm in ("sighted", "blind"):
            directory = base / f"{arm}_seed0"
            model_zip(directory / "final.zip")
            write_json(directory / "config.json", {"status": "finished", "steps": 20,
                                                     "total_timesteps": 20, "episodes": 0,
                                                     "recorded_steps": 0, "note": "A"})
            write_meta(directory, arm, 0)
        first = self.stable_scan()
        first_revision = self.item(first, "runs_json")["revision"]

        config = base / "sighted_seed0" / "config.json"
        original_stat = config.stat()
        replacement = config.with_suffix(".replacement")
        write_json(replacement, {"status": "finished", "steps": 20,
                                 "total_timesteps": 20, "episodes": 0,
                                 "recorded_steps": 0, "note": "B"})
        self.assertEqual(replacement.stat().st_size, original_stat.st_size)
        os.replace(replacement, config)
        os.utime(config, ns=(original_stat.st_atime_ns, original_stat.st_mtime_ns))

        self.catalog.scan()
        self.now[0] += 1.1
        after = self.catalog.scan()
        self.assertNotEqual(self.item(after, "runs_json")["revision"], first_revision)

    def test_scan_leaves_fixture_inputs_unchanged(self):
        d = self.root / "runs_x" / "sighted_seed0"
        model_zip(d / "final.zip")
        write_json(d / "config.json", {"status": "finished", "steps": 20,
                                         "total_timesteps": 20, "episodes": 0,
                                         "recorded_steps": 0})
        write_meta(d, "sighted", 0)
        paths = sorted(p for p in self.root.rglob("*") if p.is_file())
        before = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in paths}
        self.stable_scan()
        after = {p.relative_to(self.root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in paths}
        self.assertEqual(before, after)

    def test_derived_and_plant_provenance_change_revisions(self):
        (self.root / "data").mkdir()
        (self.root / "data" / "derived_params.json").write_text('{"x":1}', encoding="utf-8")
        first = self.stable_scan()
        (self.root / "data" / "derived_params.json").write_text('{"x":2}', encoding="utf-8")
        second = self.stable_scan()
        self.assertNotEqual(first["plant_revision"], second["plant_revision"])
        (self.root / "plant.py").write_text("x=1", encoding="utf-8")
        third = self.stable_scan()
        self.assertNotEqual(second["plant_revision"], third["plant_revision"])

    def test_loaded_plant_code_identity_is_distinct_from_disk_identity(self):
        module = types.ModuleType("plant")
        module.__file__ = str(self.root / "plant.py")
        exec("def marker(): return 1", module.__dict__)
        prior = sys.modules.get("plant")
        sys.modules["plant"] = module
        try:
            (self.root / "plant.py").write_text("def marker(): return 1", encoding="utf-8")
            self.catalog = ArtifactCatalog(self.root, clock=lambda: self.now[0],
                                           running_pid=lambda _path: None)
            first = self.stable_scan()
            exec("def marker(): return 2", module.__dict__)
            second = self.stable_scan()
            self.assertNotEqual(first["plant_revision"], second["plant_revision"])
            self.assertTrue(second["restart_needed"])
        finally:
            if prior is None:
                sys.modules.pop("plant", None)
            else:
                sys.modules["plant"] = prior

    def test_disk_change_before_first_stable_scan_needs_restart(self):
        module = types.ModuleType("plant")
        module.__file__ = str(self.root / "plant.py")
        exec("def marker(): return 1", module.__dict__)
        prior = sys.modules.get("plant")
        sys.modules["plant"] = module
        try:
            disk = self.root / "plant.py"
            disk.write_text("def marker(): return 1", encoding="utf-8")
            self.catalog = ArtifactCatalog(self.root, clock=lambda: self.now[0],
                                           running_pid=lambda _path: None)
            disk.write_text("def marker(): return 2", encoding="utf-8")
            snapshot = self.stable_scan()
            self.assertTrue(snapshot["restart_needed"])
        finally:
            if prior is None:
                sys.modules.pop("plant", None)
            else:
                sys.modules["plant"] = prior

    def test_scientific_dependencies_are_in_plant_revision(self):
        prior = self.stable_scan()
        for name in ("derived.py", "ecu.py", "controllers/ecu.py", "random_road.py",
                     "evaluate.py", "fingerprint.py", "data/derived_params.json"):
            dependency = self.root / name
            dependency.parent.mkdir(parents=True, exist_ok=True)
            dependency.write_text(f"source = {len(name)}", encoding="utf-8")
            current = self.stable_scan()
            self.assertNotEqual(prior["plant_revision"], current["plant_revision"], name)
            prior = current

    def test_unsettled_plant_inputs_mark_results_updating(self):
        (self.root / "derived.py").write_text("x = 1", encoding="utf-8")
        snap = self.catalog.scan()
        self.assertTrue(snap["plant_updating"])
        self.assertTrue(snap["results_updating"])

    def test_filesystem_errors_expose_only_relative_path_and_type(self):
        runs = self.root / "runs_denied"
        runs.mkdir()
        original_iterdir = Path.iterdir
        def fail_target(path):
            if path == runs:
                raise PermissionError(f"denied {path}")
            return original_iterdir(path)
        with patch.object(Path, "iterdir", fail_target):
            snap = self.catalog.scan()
        self.assertEqual(snap["issues"][0]["path"], "runs_denied")
        self.assertNotIn(str(self.root), snap["issues"][0]["message"])

    def test_result_context_changes_results_without_changing_training(self):
        d = self.root / "runs_x" / "sighted_seed0"
        d.mkdir(parents=True)
        first = self.stable_scan()
        (self.root / "results").mkdir()
        (self.root / "results" / "PREREGISTRATION.md").write_text("version one", encoding="utf-8")
        second = self.stable_scan()
        self.assertNotEqual(first["results_revision"], second["results_revision"])
        self.assertEqual(first["training_revision"], second["training_revision"])

    def test_deleted_current_artifact_disappears_from_published_snapshot(self):
        d = self.root / "runs_x" / "sighted_seed0"
        d.mkdir(parents=True)
        first = self.stable_scan()
        self.assertIn("runs_x", [x["relative_path"] for x in first["items"]])
        import shutil
        shutil.rmtree(self.root / "runs_x")
        second = self.stable_scan()
        self.assertNotIn("runs_x", [x["relative_path"] for x in second["items"]])
        self.assertNotEqual(first["training_revision"], second["training_revision"])


if __name__ == "__main__":
    unittest.main()
