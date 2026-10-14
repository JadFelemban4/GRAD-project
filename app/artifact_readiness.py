"""Small, bounded filesystem and publication checks for artifact_catalog."""
from __future__ import annotations

import json
import math
import os
import stat
import time
from pathlib import Path
from typing import Callable


MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_MODEL_BYTES = 512 * 1024 * 1024
MAX_MODEL_DATA_BYTES = 4 * 1024 * 1024
MAX_MODEL_UNCOMPRESSED_BYTES = 32 * 1024 * 1024


def file_signature(path: Path) -> tuple[int, int, int, int, int] | None:
    """Return a replacement-sensitive signature for a regular file.

    Device and inode distinguish atomic replacements where the bytes' size and
    mtime are restored. ctime remains in the signature as a fallback signal on
    filesystems that do not provide a useful inode number.
    """
    try:
        st = path.stat()
        if not stat.S_ISREG(st.st_mode):
            return None
        return (st.st_size, st.st_mtime_ns, getattr(st, "st_dev", 0),
                getattr(st, "st_ino", 0), getattr(st, "st_ctime_ns", int(st.st_ctime * 1_000_000_000)))
    except OSError:
        return None


class StabilityTracker:
    """Require an unchanged size/mtime observation at least one second later."""

    def __init__(self, clock: Callable[[], float] = time.monotonic, interval: float = 1.0):
        self.clock = clock
        self.interval = interval
        self._seen: dict[str, tuple[tuple[int, int, int, int, int], float]] = {}

    def stable(self, path: Path) -> tuple[bool, tuple[int, int, int, int, int] | None]:
        sig = file_signature(path)
        if sig is None:
            self._seen.pop(str(path.resolve(strict=False)), None)
            return False, None
        key = str(path.resolve(strict=False))
        now = self.clock()
        previous = self._seen.get(key)
        if previous and previous[0] == sig:
            return now - previous[1] >= self.interval, sig
        self._seen[key] = (sig, now)
        return False, sig


def contained(root: Path, path: Path) -> bool:
    """Whether a path resolves under root, including on Windows junctions."""
    try:
        root_real = root.resolve(strict=True)
        path_real = path.resolve(strict=True)
        return os.path.commonpath((str(root_real), str(path_real))) == str(root_real)
    except (OSError, ValueError):
        return False


def read_json_stable(path: Path, expected_signature: tuple[int, int, int, int, int]):
    """Read a small JSON file only if its signature still matches afterwards."""
    before = file_signature(path)
    if before != expected_signature or before[0] > MAX_JSON_BYTES:
        raise ValueError("JSON changed or exceeds the size limit")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("invalid JSON") from exc
    after = file_signature(path)
    if after != before:
        raise ValueError("JSON changed while being read")
    return data


def file_digest_stable(path: Path, expected_signature: tuple[int, int, int, int, int], *, limit=MAX_MODEL_BYTES) -> str:
    """Hash one stable file with pre/post stat checks and a hard byte bound."""
    import hashlib

    before = file_signature(path)
    if before != expected_signature or before[0] > limit:
        raise ValueError("file changed or exceeds the size limit")
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    if file_signature(path) != before:
        raise ValueError("file changed while being read")
    return h.hexdigest()


def zip_within_budget(path: Path, expected_signature: tuple[int, int, int, int, int]) -> bool:
    """Reject oversized or malformed SB3-like archives before FP.model_budget."""
    import zipfile

    if expected_signature[0] > MAX_MODEL_BYTES:
        return False
    before = file_signature(path)
    if before != expected_signature:
        return False
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            total = sum(info.file_size for info in infos)
            data = next((info for info in infos if info.filename == "data"), None)
            valid = (data is not None and data.file_size <= MAX_MODEL_DATA_BYTES
                     and total <= MAX_MODEL_UNCOMPRESSED_BYTES
                     and archive.testzip() is None)
    except (OSError, zipfile.BadZipFile, RuntimeError):
        return False
    return valid and file_signature(path) == before


def counts_consistent(config: dict, expected_tag: str) -> bool:
    """Validate the required modern completion fields and duplicated identity."""
    if config.get("status") != "finished":
        return False
    if config.get("tag") not in (None, expected_tag):
        return False
    try:
        arm, seed_text = expected_tag.rsplit("_seed", 1)
        seed = int(seed_text)
        steps = int(config["steps"])
        total = int(config["total_timesteps"])
        episodes = int(config["episodes"])
        recorded = int(config["recorded_steps"])
    except (KeyError, TypeError, ValueError):
        return False
    if min(steps, total, episodes, recorded) < 0 or steps <= 0 or total != steps:
        return False
    if config.get("seed", seed) != seed:
        return False
    if "preview" in config and bool(config["preview"]) != (arm == "sighted"):
        return False
    return True


def metadata_consistent(config: dict, meta: dict, expected_tag: str) -> bool:
    """Cross-check modern config identity against recorded training metadata."""
    if not isinstance(config, dict) or not isinstance(meta, dict):
        return False
    for key, expected in (("tag", expected_tag),):
        if meta.get(key) is not None and meta[key] != expected:
            return False
    arm, seed_text = expected_tag.rsplit("_seed", 1)
    seed = int(seed_text)
    if meta.get("seed", seed) != seed:
        return False
    if "use_preview" in meta and "preview" in config:
        if bool(meta["use_preview"]) != bool(config["preview"]):
            return False
    if "steps_requested" in meta and "steps" in config:
        try:
            if int(meta["steps_requested"]) != int(config["steps"]):
                return False
        except (TypeError, ValueError):
            return False
    train_road = meta.get("train_road")
    if train_road is not None and config.get("road") is not None and train_road != config["road"]:
        return False
    if "preview" in config and bool(config["preview"]) != (arm == "sighted"):
        return False
    return True


def duplicated_metrics_match(index_policy, summary_doc, expected_policy=None, config_doc=None) -> bool:
    """Check every duplicated statistic, scalar, and action in the publication."""
    if not isinstance(index_policy, dict) or not isinstance(summary_doc, dict):
        return False
    if expected_policy is not None and summary_doc.get("policy") != expected_policy:
        return False
    summary = summary_doc.get("summary")
    if not isinstance(summary, dict):
        return False

    def same(expected, actual):
        if isinstance(expected, dict):
            return isinstance(actual, dict) and all(
                key in actual and same(value, actual[key]) for key, value in expected.items())
        if isinstance(expected, list):
            return isinstance(actual, list) and len(expected) == len(actual) and all(
                same(a, b) for a, b in zip(expected, actual))
        if isinstance(expected, bool):
            return isinstance(actual, bool) and expected == actual
        if isinstance(expected, (int, float)):
            if isinstance(actual, bool) or not isinstance(actual, (int, float)):
                return False
            return math.isfinite(float(expected)) and math.isfinite(float(actual)) and expected == actual
        return type(expected) is type(actual) and expected == actual

    for key, value in index_policy.items():
        if key == "actions":
            actual = summary_doc.get("actions")
        elif key == "config":
            actual = config_doc
        else:
            actual = summary.get(key)
        if actual is None or not same(value, actual):
            return False
    return True
