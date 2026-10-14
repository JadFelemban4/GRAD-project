"""Bounded readers for saved training and evaluation decisions.

This module only reads files. NPZ data is fully decoded once per active source
revision because ZIP members must be decompressed before a requested window can
be served. It never loads a policy or calls the simulation.
"""
from __future__ import annotations

import hashlib
import json
import math
import ast
from pathlib import Path
from pathlib import PurePosixPath
import threading
import zipfile
import zlib

import numpy as np

MAX_ARCHIVE = 128 * 1024 * 1024
MAX_UNCOMPRESSED = 512 * 1024 * 1024
MAX_MEMBER = 256 * 1024 * 1024
MAX_MEMBERS = 128
MAX_SAMPLES = 2_000_000
MAX_NPY_HEADER = 10_000
ACTUATORS = (
    ("spark", "Spark trim", "deg", 0), ("lambda", "Lambda trim", "lambda trim", 1),
    ("boost", "Boost trim", "kPa", 2), ("fan", "Fan duty", "fraction", 3),
    ("pump", "Pump duty", "fraction", 4),
)
_LOCK = threading.RLock()
_CACHE: tuple | None = None
_HASH_CACHE: dict[tuple[str, tuple], str] = {}


class RecordError(ValueError):
    """A source is present but cannot be read as the documented schema."""


def _stat_signature(path: Path) -> tuple[int, ...]:
    st = path.stat()
    return (st.st_size, st.st_mtime_ns, getattr(st, "st_ctime_ns", 0),
            getattr(st, "st_dev", 0), getattr(st, "st_ino", 0),
            getattr(st, "st_birthtime_ns", 0))


def _hash_stream(path: Path, digest) -> None:
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)


def _hash_file(path: Path, max_bytes: int = MAX_ARCHIVE,
               expected_signature: tuple | None = None) -> str:
    """Hash once per replacement-sensitive file identity, with a stable-read check."""
    path = Path(path).resolve()
    signature = _stat_signature(path)
    if expected_signature is not None and signature != expected_signature:
        raise RecordError("source_replaced_during_read")
    if signature[0] > max_bytes:
        raise RecordError("source_too_large")
    key = (str(path), signature)
    with _LOCK:
        cached = _HASH_CACHE.get(key)
        if cached is not None:
            return cached
        digest = hashlib.sha256()
        _hash_stream(path, digest)
        if _stat_signature(path) != signature:
            raise RecordError("source_replaced_during_read")
        value = digest.hexdigest()
        if len(_HASH_CACHE) >= 2048:
            _HASH_CACHE.clear()
        _HASH_CACHE[key] = value
        return value


def content_revision(path: Path, max_bytes: int = MAX_ARCHIVE) -> str:
    return _hash_file(path, max_bytes=max_bytes)


def _stable_bytes(path: Path, limit: int = MAX_ARCHIVE) -> tuple[bytes, str, tuple]:
    path = Path(path)
    before = _stat_signature(path)
    if before[0] > limit:
        raise RecordError("source_too_large")
    raw = path.read_bytes()
    after = _stat_signature(path)
    if before != after or len(raw) != after[0]:
        raise RecordError("source_replaced_during_read")
    return raw, hashlib.sha256(raw).hexdigest(), after


def _validate_npy_member(stream, member_size: int) -> tuple[int, int]:
    magic = stream.read(6)
    if magic != b"\x93NUMPY":
        raise RecordError("npy_header_invalid")
    version_raw = stream.read(2)
    if len(version_raw) != 2:
        raise RecordError("npy_header_invalid")
    version = (version_raw[0], version_raw[1])
    if version == (1, 0):
        length_raw = stream.read(2)
        length_size = 2
        encoding = "latin1"
    elif version in ((2, 0), (3, 0)):
        length_raw = stream.read(4)
        length_size = 4
        encoding = "utf-8" if version == (3, 0) else "latin1"
    else:
        raise RecordError("npy_version_unsupported")
    if len(length_raw) != length_size:
        raise RecordError("npy_header_invalid")
    header_length = int.from_bytes(length_raw, "little")
    if not 1 <= header_length <= MAX_NPY_HEADER:
        raise RecordError("npy_header_limit")
    header_raw = stream.read(header_length)
    if len(header_raw) != header_length or not header_raw.endswith(b"\n"):
        raise RecordError("npy_header_invalid")
    try:
        header = ast.literal_eval(header_raw.decode(encoding).strip())
        if not isinstance(header, dict):
            raise ValueError
        shape = header["shape"]
        if not isinstance(shape, tuple) or any(isinstance(n, bool) or not isinstance(n, int) or n < 0 for n in shape):
            raise ValueError
        if not isinstance(header["fortran_order"], bool):
            raise ValueError
        dtype = np.dtype(header["descr"])
    except (UnicodeError, ValueError, TypeError, KeyError, SyntaxError, OverflowError, RecursionError) as exc:
        raise RecordError("npy_header_invalid") from exc
    if dtype.hasobject or dtype.fields is not None or dtype.kind not in "biuf" or dtype.itemsize <= 0:
        raise RecordError("unsupported_array_dtype")
    elements = math.prod(shape)
    expected_bytes = elements * dtype.itemsize
    data_start = stream.tell()
    available_bytes = member_size - data_start
    # This check happens while reading only the bounded header. It prevents a
    # tiny ZIP member from inducing a huge NumPy allocation from its shape.
    if expected_bytes != available_bytes:
        raise RecordError("npy_member_size_mismatch")
    if expected_bytes > MAX_MEMBER:
        raise RecordError("npy_array_allocation_limit")
    return expected_bytes, data_start


def _archive_members(path: Path) -> list[str]:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            if not infos or len(infos) > MAX_MEMBERS:
                raise RecordError("archive_member_limit")
            total = 0
            verified_total = 0
            names = []
            seen = set()
            for info in infos:
                if info.is_dir() or info.file_size < 0 or info.compress_size < 0:
                    raise RecordError("archive_member_invalid")
                member_path = PurePosixPath(info.filename)
                if member_path.name != info.filename or not info.filename.endswith(".npy"):
                    raise RecordError("archive_member_name_invalid")
                key = info.filename[:-4]
                if key in seen:
                    raise RecordError("archive_duplicate_member")
                seen.add(key)
                if info.file_size > MAX_MEMBER:
                    raise RecordError("archive_member_too_large")
                total += info.file_size
                if total > MAX_UNCOMPRESSED:
                    raise RecordError("archive_decompressed_limit")
                if info.file_size and info.compress_size == 0:
                    raise RecordError("archive_compression_invalid")
                if info.compress_size and info.file_size / info.compress_size > 1000:
                    raise RecordError("archive_compression_ratio_limit")
                if info.compress_type not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED):
                    raise RecordError("archive_compression_unsupported")
                with archive.open(info) as member:
                    expected_payload, data_start = _validate_npy_member(member, info.file_size)
                    actual_size = member.tell()
                    while True:
                        block = member.read(1024 * 1024)
                        if not block:
                            break
                        actual_size += len(block)
                        if actual_size > MAX_MEMBER:
                            raise RecordError("archive_member_too_large")
                    if actual_size != info.file_size:
                        raise RecordError("archive_member_truncated")
                    if actual_size - data_start != expected_payload:
                        raise RecordError("npy_member_size_mismatch")
                    verified_total += actual_size
                    if verified_total > MAX_UNCOMPRESSED:
                        raise RecordError("archive_decompressed_limit")
                names.append(info.filename)
            return names
    except (zipfile.BadZipFile, OSError, EOFError, RuntimeError, zlib.error) as exc:
        raise RecordError("archive_malformed") from exc


def _load_npz(path: Path) -> tuple[dict, str]:
    global _CACHE
    path = Path(path).resolve()
    with _LOCK:
        signature = _stat_signature(path)
        if _CACHE is not None and _CACHE[0] == str(path) and _CACHE[1] == signature:
            return _CACHE[2], _CACHE[3]
        if signature[0] > MAX_ARCHIVE:
            raise RecordError("source_too_large")
        _archive_members(path)
        # allow_pickle=False is essential: records are numeric data only.
        try:
            with np.load(path, allow_pickle=False, max_header_size=MAX_NPY_HEADER) as archive:
                arrays = {name: np.array(archive[name], copy=True) for name in archive.files}
        except (OSError, ValueError, EOFError, zipfile.BadZipFile) as exc:
            raise RecordError("archive_malformed_or_object_array") from exc
        after = _stat_signature(path)
        if after != signature:
            raise RecordError("source_replaced_during_read")
        revision = _hash_file(path, expected_signature=signature)
        _CACHE = (str(path), signature, arrays, revision)
        return arrays, revision


def _sidecar(path: Path, filename: str) -> dict | None:
    candidate = path.parent / filename
    try:
        if candidate.stat().st_size > 4 * 1024 * 1024:
            return None
        raw, _, _ = _stable_bytes(candidate, 4 * 1024 * 1024)
        doc = json.loads(raw.decode("utf-8-sig"), parse_constant=lambda _: None)
        return doc if isinstance(doc, dict) else None
    except (OSError, ValueError, UnicodeError):
        return None


def _dt(path: Path, kind: str, config: dict | None) -> float | None:
    # Training dt is recorded by train.py in config.json. Evaluation's producer
    # records the exact protocol and dt in eval_summary.json.
    candidates = []
    if isinstance(config, dict):
        candidates.extend([config.get("dt"), config.get("train_dt")])
    if kind == "evaluation":
        summary = _sidecar(path, "eval_summary.json") or {}
        protocol = summary.get("protocol")
        if isinstance(protocol, str):
            import re
            found = re.search(r"\bdt\s+([0-9]+(?:\.[0-9]+)?)", protocol)
            if found:
                candidates.insert(0, float(found.group(1)))
    for value in candidates:
        try:
            n = float(value)
            if math.isfinite(n) and n > 0:
                return n
        except (TypeError, ValueError):
            pass
    return None


def _descriptor(cid: str, label: str, unit: str, group: str, evidence: str,
                *, state: str = "recorded", reason: str | None = None, actuator: str | None = None,
                phase: str | None = None) -> dict:
    out = {"id": cid, "label": label, "unit": unit, "group": group,
           "evidence": evidence, "state": state}
    if reason:
        out["reason"] = reason
    if actuator:
        out["actuator"] = actuator
    if phase:
        out["phase"] = phase
    return out


def _array_channels(arrays: dict, kind: str) -> tuple[list[dict], dict[str, tuple[str, int | None]]]:
    channels: list[dict] = []
    mapping: dict[str, tuple[str, int | None]] = {}

    def add(cid, label, unit, group, key, col=None, evidence="recorded", actuator=None, phase=None):
        if key in arrays:
            channels.append(_descriptor(cid, label, unit, group, evidence, actuator=actuator, phase=phase))
            mapping[cid] = (key, col)
        else:
            channels.append(_descriptor(cid, label, unit, group, evidence, state="unavailable",
                                        reason="missing_recorded_channel", actuator=actuator, phase=phase))

    action_evidence = "normalized_policy_command[-1,1]" if kind == "training" else "normalized_policy_command[-1,1]"
    for name, label, unit, col in ACTUATORS:
        add(f"command_trim.{name}{'_deg' if name == 'spark' else '_kpa' if name == 'boost' else ''}",
            f"{label} command", "normalized [-1,1]", "command_trim", "action", col,
            action_evidence, name, "before_step")
    for name, label, unit, col in ACTUATORS:
        cid = f"applied_trim.{name}{'_deg' if name == 'spark' else '_kpa' if name == 'boost' else ''}"
        add(cid, f"{label} applied", unit, "applied_trim", "applied", col,
            "physical_applied_after_slew_limit", name, "after_step")

    if "obs" in arrays and arrays["obs"].ndim == (2 if kind == "training" else 3):
        size = arrays["obs"].shape[-1]
        semantic = [
            ("engine.rpm_normalized", "Engine speed", "observation", "normalized_policy_input"),
            ("engine.map_normalized", "Manifold pressure", "observation", "normalized_policy_input"),
            ("engine.throttle", "Throttle", "observation", "normalized_policy_input"),
            ("engine.spark_normalized", "Spark", "observation", "normalized_policy_input"),
            ("engine.lambda_normalized", "Lambda", "observation", "normalized_policy_input"),
            ("thermal.turbine_normalized", "Turbine temperature", "observation", "normalized_policy_input"),
            ("thermal.oil_normalized", "Oil temperature", "observation", "normalized_policy_input"),
            ("thermal.block_normalized", "Block temperature", "observation", "normalized_policy_input"),
            ("ambient.intake_temperature_normalized", "Intake temperature", "observation", "normalized_policy_input"),
            ("ambient.temperature_normalized", "Ambient temperature", "observation", "normalized_policy_input"),
            ("ambient.pressure_normalized", "Barometric pressure", "observation", "normalized_policy_input"),
            ("ambient.humidity_normalized", "Humidity", "observation", "normalized_policy_input"),
            ("vehicle.speed_normalized", "Vehicle speed", "observation", "normalized_policy_input"),
            ("road.grade_normalized", "Current road grade", "observation", "normalized_policy_input"),
            ("preview.grade_2s_normalized", "Road preview at 2 s", "preview", "recorded_policy_input"),
            ("preview.grade_5s_normalized", "Road preview at 5 s", "preview", "recorded_policy_input"),
            ("preview.grade_15s_normalized", "Road preview at 15 s", "preview", "recorded_policy_input"),
            ("preview.grade_30s_normalized", "Road preview at 30 s", "preview", "recorded_policy_input"),
            ("engine.torque_request_normalized", "Torque request", "observation", "normalized_policy_input"),
            ("policy.aggression", "Policy aggression", "observation", "recorded_policy_input"),
            ("policy.preference_weight[0]", "Policy preference weight 0", "observation", "recorded_policy_input"),
            ("policy.preference_weight[1]", "Policy preference weight 1", "observation", "recorded_policy_input"),
            ("policy.preference_weight[2]", "Policy preference weight 2", "observation", "recorded_policy_input"),
        ]
        for i in range(size):
            if i < len(semantic):
                cid, label, group, evidence = semantic[i]
            else:
                cid, label, group, evidence = (f"observation.vector[{i}]", f"Observation {i}",
                                               "observation", "recorded_policy_input")
            channels.append(_descriptor(cid, label, "normalized", group, evidence, phase="before_step"))
            mapping[cid] = ("obs", i)
    else:
        channels.append(_descriptor("observation.vector", "Observation vector", "normalized", "observation",
                                    "recorded_policy_input", state="unavailable", reason="missing_recorded_channel"))
    scalar_specs = {
        "reward": ("reward", "Reward", "reward", "recorded_reward"),
        "r_fuel": ("reward.fuel", "Fuel reward", "reward", "recorded_reward_component"),
        "r_life": ("reward.life", "Life reward", "reward", "recorded_reward_component"),
        "r_resp": ("reward.responsiveness", "Responsiveness reward", "reward", "recorded_reward_component"),
        "torque": ("engine.torque", "Torque", "N·m", "recorded_engine_state"),
        "torque_req": ("engine.torque_request", "Torque request", "N·m", "recorded_engine_state"),
        "rpm": ("engine.rpm", "Engine speed", "rpm", "recorded_engine_state"),
        "map_kpa": ("engine.map", "Manifold pressure", "kPa", "recorded_engine_state"),
        "t_turb": ("thermal.turbine", "Turbine temperature", "K", "recorded_engine_state"),
        "t_oil": ("thermal.oil", "Oil temperature", "K", "recorded_engine_state"),
        "t_block": ("thermal.block", "Block temperature", "K", "recorded_engine_state"),
        "t_turb_base": ("thermal.turbine_baseline", "Baseline turbine temperature", "K", "recorded_engine_state"),
        "egt_c": ("thermal.egt", "Exhaust gas temperature", "°C", "recorded_engine_state"),
        "ki": ("knock.integral", "Knock integral", "", "recorded_engine_state"),
        "damage_rate": ("damage.rate", "Damage rate", "", "recorded_damage_rate_unit_unspecified"),
        "mdot_fuel": ("engine.fuel_flow", "Fuel flow", "kg/s", "recorded_engine_state"),
        "spark": ("engine.spark", "Spark", "deg", "recorded_engine_state"),
        "lam": ("engine.lambda", "Lambda", "ratio", "recorded_engine_state"),
        "grade": ("road.grade", "Road grade", "fraction", "recorded_engine_state"),
    }
    for key, (cid, label, unit, evidence) in scalar_specs.items():
        add(cid, label, unit, "reward" if cid.startswith("reward") else "thermal" if cid.startswith("thermal") else "engine",
            key, evidence=evidence, phase="after_step")
    return channels, mapping


def _validated_arrays(path: Path, kind: str, config: dict | None) -> tuple[dict, str, list[dict], list[dict], float | None]:
    arrays, revision = _load_npz(path)
    expected = {"training": {"step", "episode", "action", "obs", "reward"},
                "evaluation": {"action", "applied", "obs", "reward"}}
    if kind not in expected or not expected[kind].issubset(arrays):
        raise RecordError("unsupported_record_schema")
    for name, value in arrays.items():
        if value.dtype.hasobject or value.dtype.kind not in "biuf":
            raise RecordError("unsupported_array_dtype")
    if kind == "training":
        n = arrays["step"].shape[0] if arrays["step"].ndim == 1 else -1
        if n < 1 or arrays["episode"].shape != (n,) or arrays["action"].shape != (n, 5) or arrays["obs"].ndim != 2 or arrays["obs"].shape[0] != n:
            raise RecordError("record_shape_invalid")
        if arrays["reward"].shape != (n,):
            raise RecordError("record_shape_invalid")
        if n > MAX_SAMPLES or arrays["obs"].shape[1] > 256:
            raise RecordError("record_sample_limit")
        for name, value in arrays.items():
            if name in ("step", "episode"):
                if value.shape != (n,):
                    raise RecordError("record_shape_invalid")
            elif value.shape and value.shape[0] != n:
                raise RecordError("record_shape_invalid")
        episodes = []
        for eid in np.unique(arrays["episode"]):
            idx = np.flatnonzero(arrays["episode"] == eid)
            episodes.append({"id": int(eid), "samples": int(len(idx)), "time_unit": "s" if _dt(path, kind, config) else "step"})
    else:
        if arrays["action"].ndim != 3 or arrays["action"].shape[2] != 5 or arrays["obs"].ndim != 3:
            raise RecordError("record_shape_invalid")
        shape = arrays["action"].shape[:2]
        if not shape[0] or not shape[1] or arrays["obs"].shape[:2] != shape or arrays["obs"].shape[2] > 256:
            raise RecordError("record_shape_invalid")
        if arrays["applied"].shape != arrays["action"].shape or arrays["reward"].shape != shape:
            raise RecordError("record_shape_invalid")
        if math.prod(shape) > MAX_SAMPLES:
            raise RecordError("record_sample_limit")
        for name, value in arrays.items():
            if name in ("episode_seed", "weights"):
                continue
            if name in ("action", "applied", "obs"):
                if value.shape[:2] != shape:
                    raise RecordError("record_shape_invalid")
            elif value.shape != shape:
                raise RecordError("record_shape_invalid")
        episodes = [{"id": i, "samples": int(shape[1]), "time_unit": "s" if _dt(path, kind, config) else "step"}
                    for i in range(shape[0])]
    for name, value in arrays.items():
        if value.dtype.kind in "f" and not np.all(np.isfinite(value)):
            # Values remain individually null in frame responses, with an issue.
            continue
    channels, mapping = _array_channels(arrays, kind)
    dt = _dt(path, kind, config)
    issues = []
    if dt is None:
        issues.append("timestep_unavailable_step_axis_only")
    if any(v.dtype.kind == "f" and not np.all(np.isfinite(v)) for v in arrays.values()):
        issues.append("non_finite_values_returned_as_null")
    return arrays, revision, episodes, channels, dt


def _resolve(path: Path, kind: str) -> Path:
    path = Path(path).resolve()
    if kind == "training" and path.is_dir():
        path = path / "train_record.npz"
    if kind == "evaluation" and path.is_dir():
        path = path / "eval_record.npz"
    if not path.is_file():
        raise FileNotFoundError(path)
    return path


def read_record_meta(path: Path, kind: str, config: dict | None = None) -> dict:
    path = _resolve(path, kind)
    arrays, revision, episodes, channels, dt = _validated_arrays(path, kind, config)
    return {"source_revision": revision, "kind": kind, "episodes": episodes,
            "time_unit": "s" if dt else "step", "dt": dt, "channels": channels,
            "issues": _issues(arrays, dt)}


def _issues(arrays: dict, dt: float | None) -> list[str]:
    out = ["sample_values_include_pre_and_post_step_phases"]
    if dt is None:
        out.append("timestep_unavailable_step_axis_only")
    if any(v.dtype.kind == "f" and not np.all(np.isfinite(v)) for v in arrays.values()):
        out.append("non_finite_values_returned_as_null")
    return out


def read_record_window(path: Path, kind: str, episode: int, start: int, count: int,
                       config: dict | None = None) -> dict:
    if isinstance(episode, bool) or not isinstance(episode, int) or episode < 0:
        raise RecordError("episode_bounds_invalid")
    if isinstance(start, bool) or not isinstance(start, int) or start < 0:
        raise RecordError("frame_bounds_invalid")
    if isinstance(count, bool) or not isinstance(count, int) or not 1 <= count <= 500:
        raise RecordError("frame_count_invalid")
    path = _resolve(path, kind)
    arrays, revision, episodes, channels, dt = _validated_arrays(path, kind, config)
    selected = next((e for e in episodes if e["id"] == episode), None)
    if selected is None or start > selected["samples"]:
        raise RecordError("frame_bounds_invalid")
    end = min(selected["samples"], start + count)
    mapping_channels, mapping = _array_channels(arrays, kind)
    if kind == "training":
        indexes = np.flatnonzero(arrays["episode"] == episode)[start:end]
        time_indexes = np.arange(start, end)
        getval = lambda key, col, j: arrays[key][indexes[j]] if col is None else arrays[key][indexes[j], col]
    else:
        indexes = np.arange(start, end)
        time_indexes = indexes
        getval = lambda key, col, j: arrays[key][episode, indexes[j]] if col is None else arrays[key][episode, indexes[j], col]
    frames = []
    for j, local_index in enumerate(time_indexes):
        values = {}
        for desc in mapping_channels:
            cid = desc["id"]
            if desc["state"] != "recorded":
                values[cid] = None
                continue
            key, col = mapping[cid]
            try:
                n = float(getval(key, col, j))
                values[cid] = n if math.isfinite(n) else None
            except (ValueError, TypeError, IndexError):
                values[cid] = None
        frames.append({"sample_index": int(local_index), "time": float(local_index * dt) if dt else None,
                       "values": values})
    return {"source_revision": revision, "kind": kind, "episode": episode, "start": start,
            "channels": channels, "frames": frames, "issues": _issues(arrays, dt)}

