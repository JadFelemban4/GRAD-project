"""Review-only numeric reproductions. No training, evaluation, or model execution.

Run from repo root: .venv/Scripts/python.exe -B app/verification/review-2026-10-09-repro.py
All temporary fixtures and the evidence report stay under app/.
"""
from pathlib import Path
import json
import sys
import tempfile
from types import SimpleNamespace
from unittest.mock import patch
import zipfile

import numpy as np
from fastapi import FastAPI

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from app import record_reader, record_api

TMP = ROOT / "app/.superpowers/training-linked-app/tmp"
TMP.mkdir(parents=True, exist_ok=True)


def evaluation(path, reward=1.0):
    obs = np.zeros((1, 2, 23), dtype=np.float16)
    # Producer: thermal.state() == [block, oil, turbine].
    obs[:, :, 5:8] = [11, 22, 33]
    np.savez_compressed(path, action=np.zeros((1, 2, 5), dtype=np.float32),
                        applied=np.zeros((1, 2, 5), dtype=np.float32), obs=obs,
                        reward=np.full((1, 2), reward, dtype=np.float32),
                        mdot_fuel=np.full((1, 2), 10, dtype=np.float32))


report = {}
with tempfile.TemporaryDirectory(dir=TMP) as tmp:
    root = Path(tmp)
    directory = root / "runs_review" / "sighted_seed7"
    directory.mkdir(parents=True)
    path = directory / "eval_record.npz"
    evaluation(path)
    config = {"dt": 0.2}
    (directory / "config.json").write_text(json.dumps(config), encoding="utf-8")
    meta = record_reader.read_record_meta(path, "evaluation", config)
    data = record_reader.read_record_window(path, "evaluation", 0, 0, 2, config)
    values = data["frames"][0]["values"]
    descriptors = {c["id"]: c for c in meta["channels"]}
    report["thermal_mapping"] = {
        "input_obs_5_6_7": [11, 22, 33],
        "producer_order": ["block", "oil", "turbine"],
        "reader_values": {k: values[f"thermal.{k}_normalized"] for k in ("block", "oil", "turbine")},
    }
    report["fuel_flow"] = {"input_g_per_s": 10, "reader_value": values["engine.fuel_flow"],
                           "reader_unit": descriptors["engine.fuel_flow"]["unit"]}
    report["evaluation_without_timing_sidecar"] = {
        "training_config": config, "evaluation_summary_exists": False,
        "reader_dt": meta["dt"], "reader_time_unit": meta["time_unit"],
        "reader_sample_times": [f["time"] for f in data["frames"]], "issues": meta["issues"],
    }
    # Invoke actual installed route, introducing only an atomic file replacement
    # at the boundary after discovery and before the real decoder runs.
    app = FastAPI()
    record_api.install_record_routes(app, root)
    routes = {r.path: r.endpoint for r in app.routes if hasattr(r, "endpoint")}
    item = next(r for r in record_api.discover_records(root) if r["kind"] == "evaluation")
    replacement = directory / "replacement.npz"
    evaluation(replacement, reward=99.0)
    actual_new_revision = record_reader.content_revision(replacement)
    original = record_reader.read_record_window

    def replace_then_read(*args, **kwargs):
        replacement.replace(path)
        return original(*args, **kwargs)

    request = SimpleNamespace(headers={"host": "localhost:8000"})
    with patch.object(record_reader, "read_record_window", side_effect=replace_then_read):
        response = routes["/api/records/{record_id}/frames"](request, item["id"], 0, 0, 1)
    body = json.loads(response.body)
    report["replacement_during_api_request"] = {
        "old_reward": 1, "new_reward": 99, "response_reward": body["frames"][0]["values"]["reward"],
        "old_archive_revision": item["archive_revision"],
        "actual_new_archive_revision": actual_new_revision,
        "response_archive_revision": body["archive_revision"],
        "response_source_revision_matches_old": body["source_revision"] == item["source_revision"],
        "status": response.status_code,
    }
    # Legitimate producer-shaped long record with a constant reward component.
    n = 1_000_000
    training = directory / "train_record.npz"
    rng = np.random.default_rng(0)
    np.savez_compressed(training, step=np.arange(n, dtype=np.int32),
                        episode=np.arange(n, dtype=np.int32) // 3600,
                        action=rng.uniform(-1, 1, (n, 5)).astype(np.float32),
                        obs=rng.uniform(-1, 1, (n, 23)).astype(np.float16),
                        reward=rng.random(n).astype(np.float32),
                        r_resp=np.zeros(n, dtype=np.float32))
    with zipfile.ZipFile(training) as archive:
        members = {m.filename: {"bytes": m.file_size, "ratio": m.file_size / max(1, m.compress_size)}
                   for m in archive.infolist()}
    try:
        record_reader.read_record_meta(training, "training", {"dt": 1.0})
        outcome = "accepted"
    except record_reader.RecordError as exc:
        outcome = str(exc)
    report["constant_channel_compression"] = {
        "samples": n, "uncompressed_bytes": sum(m["bytes"] for m in members.values()),
        "constant_component": members["r_resp.npy"], "reader_outcome": outcome,
    }

out = Path(__file__).with_name("review-2026-10-09-repro.json")
out.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
