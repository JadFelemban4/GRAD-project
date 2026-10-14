"""Small numeric contract fixtures for the saved-record reader and routes."""
from __future__ import annotations

import json
import os
from pathlib import Path
import struct
import tempfile
import unittest
import zipfile
import zlib
from unittest.mock import patch

import numpy as np
from fastapi import FastAPI
from types import SimpleNamespace

from app import record_api
from app.record_api import discover_records, install_record_routes
from app import record_reader
from app.record_reader import RecordError, read_record_meta, read_record_window

TMP = Path(__file__).resolve().parent / ".superpowers" / "training-linked-app" / "tmp"


def training_fixture(path: Path, *, object_action=False, unequal=False, nonfinite=False):
    action = np.array([[0.1, 0.2, 0.3, 0.4, 0.5], [-0.1, 0, 0, 0, 0]], dtype=float)
    if object_action:
        action = np.array([["bad"]] * 2, dtype=object)
    if nonfinite:
        action[0, 0] = np.nan
    obs = np.arange(46, dtype=np.float16).reshape(2, 23)
    if unequal:
        obs = obs[:1]
    np.savez_compressed(path, step=np.array([10, 11], dtype=np.int32),
                        episode=np.array([3, 3], dtype=np.int32), action=action,
                        obs=obs, reward=np.array([1., 2.], dtype=np.float32),
                        torque=np.array([80., 81.], dtype=np.float32),
                        r_fuel=np.array([-.1, -.2], dtype=np.float32))


def evaluation_fixture(path: Path):
    np.savez_compressed(path,
                        action=np.array([[[0, 0, 0, 0, 0], [.5, 0, 0, 0, 0]]], dtype=np.float32),
                        applied=np.array([[[0, 0, 0, 0, 0], [1, 0, 0, 0, 0]]], dtype=np.float32),
                        obs=np.zeros((1, 2, 23), dtype=np.float16),
                        reward=np.array([[1., 2.]], dtype=np.float32),
                        t_turb=np.array([[850., 851.]], dtype=np.float32),
                        torque=np.array([[100., 101.]], dtype=np.float32),
                        episode_seed=np.array([7]), weights=np.array([[.4, .6]]))
    (path.parent / "eval_summary.json").write_text(json.dumps({
        "policy": "sighted_seed7", "protocol": "frozen test, 720 s, dt 1.0"
    }), encoding="utf-8")


class SavedRecordTests(unittest.TestCase):
    def setUp(self):
        TMP.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=TMP)
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_training_meta_and_window_keep_command_applied_distinct(self):
        path = self.root / "train_record.npz"
        training_fixture(path)
        meta = read_record_meta(path, "training", {"dt": 0.5})
        self.assertEqual(meta["episodes"], [{"id": 3, "samples": 2, "time_unit": "s"}])
        channels = {c["id"]: c for c in meta["channels"]}
        self.assertEqual(channels["command_trim.spark_deg"]["evidence"], "normalized_policy_command[-1,1]")
        self.assertEqual(channels["command_trim.spark_deg"]["phase"], "before_step")
        self.assertEqual(channels["applied_trim.spark_deg"]["state"], "unavailable")
        self.assertEqual(channels["preview.grade_2s_normalized"]["group"], "preview")
        frames = read_record_window(path, "training", 3, 1, 1, {"dt": 0.5})
        self.assertEqual(frames["frames"][0]["sample_index"], 1)
        self.assertEqual(frames["frames"][0]["time"], 0.5)
        self.assertAlmostEqual(frames["frames"][0]["values"]["command_trim.spark_deg"], -0.1)
        self.assertIsNone(frames["frames"][0]["values"]["applied_trim.spark_deg"])

    def test_evaluation_episode_axis_and_physical_applied_units(self):
        path = self.root / "eval_record.npz"
        evaluation_fixture(path)
        meta = read_record_meta(path, "evaluation")
        self.assertEqual(meta["episodes"][0]["samples"], 2)
        self.assertEqual(meta["time_unit"], "s")
        window = read_record_window(path, "evaluation", 0, 1, 1)
        self.assertEqual(window["frames"][0]["time"], 1.0)
        channels = {c["id"]: c for c in window["channels"]}
        self.assertEqual(channels["applied_trim.spark_deg"]["unit"], "deg")
        self.assertEqual(window["frames"][0]["values"]["applied_trim.spark_deg"], 1.0)

    def test_missing_dt_uses_step_axis_without_invented_seconds(self):
        path = self.root / "train_record.npz"
        training_fixture(path)
        meta = read_record_meta(path, "training")
        self.assertEqual(meta["time_unit"], "step")
        self.assertIn("timestep_unavailable_step_axis_only", meta["issues"])
        self.assertIn("sample_values_include_pre_and_post_step_phases", meta["issues"])
        window = read_record_window(path, "training", 3, 0, 2)
        self.assertIsNone(window["frames"][0]["time"])

    def test_malformed_missing_object_and_shape_errors(self):
        with self.assertRaises(FileNotFoundError):
            read_record_meta(self.root / "absent.npz", "training")
        malformed = self.root / "broken.npz"
        malformed.write_bytes(b"not a zip")
        with self.assertRaisesRegex(RecordError, "archive_malformed"):
            read_record_meta(malformed, "training")
        obj = self.root / "object.npz"
        training_fixture(obj, object_action=True)
        with self.assertRaises(RecordError):
            read_record_meta(obj, "training")
        badshape = self.root / "badshape.npz"
        training_fixture(badshape, unequal=True)
        with self.assertRaisesRegex(RecordError, "record_shape_invalid"):
            read_record_meta(badshape, "training")

    def test_nonfinite_values_are_null_and_reported(self):
        path = self.root / "nan.npz"
        training_fixture(path, nonfinite=True)
        window = read_record_window(path, "training", 3, 0, 1)
        self.assertIsNone(window["frames"][0]["values"]["command_trim.spark_deg"])
        self.assertIn("non_finite_values_returned_as_null", window["issues"])

    def test_bounds_are_rejected(self):
        path = self.root / "train_record.npz"
        training_fixture(path)
        for episode, start, count in ((-1, 0, 1), (3, -1, 1), (3, 0, 0), (3, 0, 501), (4, 0, 1)):
            with self.subTest(episode=episode, start=start, count=count):
                with self.assertRaises(RecordError):
                    read_record_window(path, "training", episode, start, count)

    def test_archive_uncompressed_limit_is_checked_before_numpy_load(self):
        path = self.root / "bomb.npz"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("huge.npy", b"x")
        raw = bytearray(path.read_bytes())
        central = raw.index(b"PK\x01\x02")
        raw[central + 24:central + 28] = struct.pack("<I", 256 * 1024 * 1024 + 1)
        path.write_bytes(raw)
        with self.assertRaisesRegex(RecordError, "archive_member_too_large"):
            read_record_meta(path, "training")

    def test_atomic_source_replacement_changes_revision(self):
        path = self.root / "train_record.npz"
        training_fixture(path)
        before = read_record_meta(path, "training")["source_revision"]
        replacement = self.root / "replacement.npz"
        training_fixture(replacement, nonfinite=True)
        old_stat = path.stat()
        os.utime(replacement, ns=(old_stat.st_atime_ns, old_stat.st_mtime_ns))
        replacement.replace(path)
        after = read_record_meta(path, "training")["source_revision"]
        self.assertNotEqual(before, after)

    def test_registry_items_and_get_routes_are_bound_to_discovered_paths(self):
        policy = self.root / "results" / "agents" / "fixture_set" / "sighted_seed7"
        policy.mkdir(parents=True)
        (self.root / "results" / "agents" / "fixture_set" / "index.json").write_text(
            json.dumps({"policies": {"sighted_seed7": {}}}), encoding="utf-8")
        evaluation_fixture(policy / "eval_record.npz")
        items = discover_records(self.root)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["state"], "available")
        app = FastAPI()
        install_record_routes(app, self.root)
        routes = {route.path: route.endpoint for route in app.routes if hasattr(route, "endpoint")}
        self.assertIn("/api/records", routes)
        self.assertIn("/api/records/{record_id}/meta", routes)
        self.assertIn("/api/records/{record_id}/frames", routes)
        request = SimpleNamespace(headers={"host": "localhost:8000"})
        listing = json.loads(routes["/api/records"](request).body)
        self.assertEqual(len(listing["records"]), 1)
        rid = listing["records"][0]["id"]
        meta = json.loads(routes["/api/records/{record_id}/meta"](request, rid).body)
        frames = json.loads(routes["/api/records/{record_id}/frames"](request, rid, 0, 0, 1).body)
        self.assertEqual(meta["kind"], "evaluation")
        self.assertEqual(frames["frames"][0]["sample_index"], 0)
        self.assertEqual(meta["source_revision"], frames["source_revision"])
        self.assertEqual(meta["archive_revision"], frames["archive_revision"])

    def test_simulation_startup_registers_record_routes_before_server_start(self):
        from app import server

        simulation_app = FastAPI()
        with patch.object(server, "app", simulation_app), \
                patch("sys.argv", ["server", "--simulation"]), \
                patch("app.agent_api.install") as agent_install, \
                patch("app.artifact_api.mount_artifacts", return_value=object()), \
                patch("app.results_api.mount_results"), \
                patch("app.record_api.install_record_routes", wraps=install_record_routes) as record_install, \
                patch("uvicorn.run") as uvicorn_run:
            server.main()

        agent_install.assert_called_once_with(simulation_app)
        record_install.assert_called_once_with(simulation_app, Path(server.HERE).parent)
        uvicorn_run.assert_called_once()
        route_paths = {route.path for route in simulation_app.routes}
        self.assertTrue({"/api/records", "/api/records/{record_id}/meta",
                         "/api/records/{record_id}/frames"}.issubset(route_paths))

    def test_discovery_reuses_archive_hash_for_unchanged_source(self):
        policy = self.root / "runs_fixture" / "agent0"
        policy.mkdir(parents=True)
        (policy / "meta.json").write_text(json.dumps({"train_dt": 0.2}), encoding="utf-8")
        archive = policy / "train_record.npz"
        training_fixture(archive)
        original = record_reader._hash_stream
        hashed = []

        def counted(path, digest):
            if Path(path).name == "train_record.npz":
                hashed.append(str(path))
            return original(path, digest)

        with patch.object(record_reader, "_hash_stream", side_effect=counted):
            first = discover_records(self.root)
            second = discover_records(self.root)
        self.assertEqual(first[0]["source_revision"], second[0]["source_revision"])
        self.assertEqual(len(hashed), 1)
        stable = record_reader._stable_bytes
        archive_reads = []

        def count_stable(path, *args, **kwargs):
            if Path(path).name == "train_record.npz":
                archive_reads.append(str(path))
            return stable(path, *args, **kwargs)

        with patch.object(record_reader, "_stable_bytes", side_effect=count_stable):
            discover_records(self.root)
            discover_records(self.root)
        self.assertEqual(archive_reads, [])

    def test_sidecar_protocol_change_changes_record_revision(self):
        policy = self.root / "results" / "agents" / "fixture_set" / "sighted_seed7"
        policy.mkdir(parents=True)
        set_dir = policy.parent
        (set_dir / "index.json").write_text(json.dumps({"policies": {"sighted_seed7": {}}}), encoding="utf-8")
        evaluation_fixture(policy / "eval_record.npz")
        first = discover_records(self.root)[0]
        self.assertEqual(first["protocol"], "frozen test, 720 s, dt 1.0")
        app = FastAPI()
        install_record_routes(app, self.root)
        endpoint = next(route.endpoint for route in app.routes
                        if getattr(route, "path", "") == "/api/records/{record_id}/meta")
        request = SimpleNamespace(headers={"host": "localhost"})
        before_meta = json.loads(endpoint(request, first["id"]).body)
        summary_path = policy / "eval_summary.json"
        summary_path.write_text(json.dumps({"policy": "sighted_seed7", "protocol": "frozen, dt 2.0"}), encoding="utf-8")
        os.utime(summary_path, ns=(summary_path.stat().st_atime_ns, summary_path.stat().st_mtime_ns + 2_000_000_000))
        second = discover_records(self.root)[0]
        self.assertEqual(first.get("archive_revision"), second.get("archive_revision"))
        self.assertNotEqual(first["source_revision"], second["source_revision"])
        self.assertNotEqual(first["sidecar_revision"], second["sidecar_revision"])
        self.assertNotEqual(first["protocol"], second["protocol"])
        after_meta = json.loads(endpoint(request, first["id"]).body)
        self.assertNotEqual(before_meta["source_revision"], after_meta["source_revision"])
        self.assertEqual(before_meta["dt"], 1.0)
        self.assertEqual(after_meta["dt"], 2.0)
        meta = read_record_meta(policy / "eval_record.npz", "evaluation")
        self.assertEqual(meta["dt"], 2.0)

    def test_symlinked_run_policy_is_rejected_before_reading_sidecars(self):
        outside = self.root.parent / (self.root.name + "_outside")
        runs = self.root / "runs_fixture"
        policy = runs / "linked-policy"
        policy.mkdir(parents=True)
        (policy / "meta.json").write_text(json.dumps({"git_head": "outside-secret"}), encoding="utf-8")
        original_resolve = Path.resolve

        def resolve_as_escape(path, *args, **kwargs):
            try:
                relative = path.relative_to(policy)
            except ValueError:
                return original_resolve(path, *args, **kwargs)
            return outside / relative

        original_json = record_api._json

        def guarded_json(path, *args, **kwargs):
            if Path(path) == policy / "meta.json":
                self.fail("escaped policy metadata was read before containment validation")
            return original_json(path, *args, **kwargs)

        with patch.object(Path, "resolve", resolve_as_escape), \
                patch.object(record_api, "_json", side_effect=guarded_json):
            records = discover_records(self.root)
        self.assertEqual(records, [])

    def test_npy_header_claim_cannot_exceed_zip_member_bytes(self):
        path = self.root / "header-bomb.npz"
        header = b"{'descr': '<f8', 'fortran_order': False, 'shape': (100000000,)}"
        prefix_len = 10
        padding = (16 - ((prefix_len + len(header) + 1) % 16)) % 16
        header += b" " * padding + b"\n"
        npy = b"\x93NUMPY\x01\x00" + struct.pack("<H", len(header)) + header
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("action.npy", npy)
        with self.assertRaisesRegex(RecordError, "npy_member_size_mismatch"):
            record_reader._archive_members(path)
        with self.assertRaisesRegex(RecordError, "npy_member_size_mismatch"):
            read_record_meta(path, "training")

    def test_truncated_deflate_member_is_streamed_and_crc_checked(self):
        path = self.root / "truncated.npz"
        buffer = __import__("io").BytesIO()
        np.save(buffer, np.arange(300_000, dtype=np.float32), allow_pickle=False)
        npy_bytes = buffer.getvalue()
        with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("action.npy", npy_bytes)
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("action.npy")
        raw = bytearray(path.read_bytes())
        name_length, extra_length = struct.unpack_from("<HH", raw, info.header_offset + 26)
        data_start = info.header_offset + 30 + name_length + extra_length
        compressor = zlib.compressobj(level=6, wbits=-15)
        shortened = compressor.compress(npy_bytes[:-8]) + compressor.flush()
        self.assertLessEqual(len(shortened), info.compress_size)
        raw[data_start:data_start + info.compress_size] = shortened + b"\x00" * (info.compress_size - len(shortened))
        path.write_bytes(raw)
        with zipfile.ZipFile(path) as archive:
            with archive.open("action.npy") as member:
                expected_payload, _ = record_reader._validate_npy_member(member, info.file_size)
                self.assertEqual(expected_payload, len(npy_bytes) - member.tell())
        with self.assertRaisesRegex(RecordError, "archive_malformed|archive_member_truncated"):
            record_reader._archive_members(path)


if __name__ == "__main__":
    unittest.main()
