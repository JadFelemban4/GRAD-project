"""Bounded, read-only discovery of training and published result artifacts.

The catalog accepts a repository root, never a request path. IDs identify
locations; revisions identify the stable contents visible at that location.
It intentionally imports only the lightweight fingerprint helper and does not
import training, evaluation, recorder, simulator, NumPy, or Torch modules.
"""
from __future__ import annotations

import hashlib
import json
import marshal
import re
import sys
import time
import types
from pathlib import Path
from typing import Callable

import fingerprint as FP

from . import artifact_readiness as readiness


_AGENT = re.compile(r"^(sighted|blind)_seed(\d+)$")
_RUNS = re.compile(r"^runs[a-z0-9_]*$")
_RESULT_TEXT = re.compile(r"^.+_seed.*\.txt$")
_PLANT_FILES = ("plant.py", "thermal.py", "engine_env.py", "random_road.py")
_PROVENANCE_FILES = (
    "plant.py", "thermal.py", "engine_env.py", "random_road.py", "derived.py",
    "fingerprint.py", "evaluate.py", "check_premise.py", "run_phase_d.py",
    "analyse_c4.py", "ecu.py", "controllers/ecu.py",
    "data/derived_params.json", "data/master_samples.csv", "data/master_points.csv",
)
_RESULT_CONTEXT = ("PREREGISTRATION.md", "KNOCK_MARGIN.md", "knock_margin.json",
                   "README.md", "index.json", "episode_trace.json")
_MEMBER_FILES = ("eval_summary.json", "eval_record.npz", "train_record.npz",
                 "policy.npz", "curve.csv", "config.json")


def _canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, default=str).encode("utf-8")


def _hash(value) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()[:24]


def _artifact_id(relative_path: str) -> str:
    return "art_" + _hash(relative_path)


def _rel(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


class ArtifactCatalog:
    """Discover stable runs, evaluation text, and published agent sets."""

    def __init__(self, root: Path, *, clock: Callable[[], float] = time.monotonic,
                 running_pid: Callable[[str], int | None] = FP.running_pid):
        self.root = Path(root).resolve()
        self.clock = clock
        self.running_pid = running_pid
        self._stability = readiness.StabilityTracker(clock)
        self._json_cache: dict[str, tuple[tuple[int, int, int, int, int], object]] = {}
        self._digest_cache: dict[str, tuple[tuple[int, int, int, int, int], str]] = {}
        self._model_cache: dict[str, tuple[tuple[int, int, int, int, int], dict | None]] = {}
        self._set_last_valid: dict[str, dict] = {}
        self._id_paths: dict[str, Path] = {}
        self._loaded_module_cache: dict[str, tuple[int, str, str]] = {}
        self._loaded_baseline = self._loaded_modules_identity()
        self._disk_baseline = self._disk_provenance_signatures()
        self._snapshot = self._empty_snapshot()

    @staticmethod
    def _empty_snapshot():
        return {"schema_version": 1, "revision": _hash([]),
                "training_revision": _hash([]), "results_revision": _hash([]),
                "plant_revision": _hash([]), "items": [], "issues": [],
                "updating": False, "training_updating": False,
                "results_updating": False, "plant_updating": False,
                "restart_needed": False}

    def snapshot(self) -> dict:
        """Return the last published value without touching disk."""
        return json.loads(json.dumps(self._snapshot))

    def revisions(self) -> dict:
        """Return current revision and update flags without rebuilding content."""
        snap = self._snapshot
        return {key: snap[key] for key in (
            "revision", "training_revision", "results_revision", "plant_revision",
            "updating", "training_updating", "results_updating", "plant_updating",
            "restart_needed")}

    def resolve(self, artifact_id: str) -> Path:
        """Resolve a server-issued current ID to a still-contained location."""
        path = self._id_paths.get(str(artifact_id))
        if path is None or not readiness.contained(self.root, path):
            raise KeyError(artifact_id)
        return path

    def restart_required(self) -> bool:
        """Recheck the loaded/disk boundary before inference, outside scan throttling."""
        loaded = self._loaded_modules_identity()
        return bool(loaded) and (loaded != self._loaded_baseline
                                or self._disk_provenance_signatures() != self._disk_baseline)

    def _stable(self, path: Path):
        if not readiness.contained(self.root, path):
            return False, None
        return self._stability.stable(path)

    def _json(self, path: Path):
        stable, sig = self._stable(path)
        if not stable:
            return None, False, "awaiting stable file"
        key = str(path.resolve())
        cached = self._json_cache.get(key)
        if cached and cached[0] == sig:
            return cached[1], True, None
        try:
            value = readiness.read_json_stable(path, sig)
        except ValueError as exc:
            self._json_cache.pop(key, None)
            return None, False, str(exc)
        self._json_cache[key] = (sig, value)
        return value, True, None

    def _digest(self, path: Path):
        stable, sig = self._stable(path)
        if not stable:
            return None, False
        key = str(path.resolve())
        cached = self._digest_cache.get(key)
        if cached and cached[0] == sig:
            return cached[1], True
        try:
            digest = readiness.file_digest_stable(path, sig, limit=2 * 1024 * 1024 * 1024)
        except (OSError, ValueError):
            return None, False
        self._digest_cache[key] = (sig, digest)
        return digest, True

    def _model(self, path: Path):
        stable, sig = self._stable(path)
        if not stable:
            return None, False
        key = str(path.resolve())
        cached = self._model_cache.get(key)
        if cached and cached[0] == sig:
            return cached[1], True
        if not readiness.zip_within_budget(path, sig):
            self._model_cache[key] = (sig, None)
            return None, True
        try:
            value = FP.model_budget(str(path))
        except (OSError, ValueError, RuntimeError):
            value = None
        if readiness.file_signature(path) != sig:
            self._model_cache.pop(key, None)
            return None, False
        # The producer's reader hashes the ZIP itself. The stability checks and
        # bounded archive inspection above limit that work to changed files.
        self._model_cache[key] = (sig, value)
        return value, True

    def _source(self, path: Path, *, binary=False):
        digest, stable = self._digest(path)
        return (_rel(self.root, path), digest, stable)

    def _member(self, run_dir: Path, agent_dir: Path):
        rel_dir = _rel(self.root, agent_dir)
        tag = agent_dir.name
        match = _AGENT.fullmatch(tag)
        if not match:
            return None, False
        arm, seed_text = match.groups()
        seed = int(seed_text)
        issues = []
        source_files = []
        file_digests = []
        updating = False
        config, config_ok, config_issue = self._json(agent_dir / "config.json") if (agent_dir / "config.json").exists() else (None, True, None)
        meta, meta_ok, meta_issue = self._json(agent_dir / "meta.json") if (agent_dir / "meta.json").exists() else (None, True, None)
        for name, value, okay, issue in (("config.json", config, config_ok, config_issue),
                                          ("meta.json", meta, meta_ok, meta_issue)):
            p = agent_dir / name
            if p.exists():
                if not okay:
                    updating |= issue == "awaiting stable file"
                    issues.append(f"{name}: {issue}")
                else:
                    if not isinstance(value, dict):
                        issues.append(f"{name}: expected an object")
                        if name == "config.json": config_ok = False
                        else: meta_ok = False
                    digest = _hash(value)
                    source_files.append(_rel(self.root, p))
                    file_digests.append((name, digest))

        model_path = agent_dir / "final.zip"
        model = None
        model_ok = not model_path.exists()
        if model_path.exists():
            model, model_ok = self._model(model_path)
            if not model_ok:
                updating = True
                issues.append("final.zip: awaiting stable file")
            else:
                if model is not None:
                    source_files.append(_rel(self.root, model_path))
                    file_digests.append(("final.zip", model.get("sha")))
                else:
                    issues.append("final.zip: unreadable or over budget")

        capabilities = {
            "model": model is not None,
            "training_curve": False,
            "training_record": False,
            "evaluation_summary": False,
            "evaluation_record": False,
            "verdict": False,
        }
        for name, cap in (("curve.csv", "training_curve"), ("train_record.npz", "training_record"),
                          ("eval_summary.json", "evaluation_summary"), ("eval_record.npz", "evaluation_record")):
            p = agent_dir / name
            if p.is_file():
                digest, stable = self._digest(p)
                if not stable:
                    updating = True
                elif digest:
                    capabilities[cap] = True
                    source_files.append(_rel(self.root, p))
                    file_digests.append((name, digest))

        live = self.running_pid(str(agent_dir))
        marker = agent_dir / "RUNNING"
        marker_exists = marker.exists()
        status = config.get("status") if isinstance(config, dict) else None
        if live is not None:
            lifecycle = "running"
        elif status == "running" or marker_exists:
            lifecycle = "interrupted"
            issues.append("stale RUNNING marker or running config")
        elif status == "finished":
            if (not config_ok or not meta_ok or not readiness.counts_consistent(config or {}, tag)
                    or model is None or not readiness.metadata_consistent(config or {}, meta, tag)):
                lifecycle = "finalizing"
                issues.append("finished config, metadata, readable model, and consistent counts are required")
            else:
                lifecycle = "finished"
        elif not config_ok or not meta_ok:
            lifecycle = "unknown"
        elif model is not None and config is None and isinstance(meta, dict):
            lifecycle = "finished"
            issues.append("legacy evidence; exact completion time and recorded counts are unavailable")
        elif model_path.exists() or status == "finalizing":
            lifecycle = "finalizing"
        elif config is not None:
            lifecycle = "interrupted"
        else:
            lifecycle = "unknown"

        scenario = (meta.get("scenario") or {}) if isinstance(meta, dict) else None
        protocol = meta.get("protocol") if isinstance(meta, dict) else None
        if protocol is None and isinstance(scenario, dict):
            protocol = scenario.get("protocol", "phase-d")
        if protocol == "random-climb":
            protocol = "d2"
        compatibility = {"replay_allowed": False, "reason": None}
        if protocol not in ("phase-d", "d2"):
            compatibility["reason"] = "unknown protocol" if protocol is not None else "protocol is not recorded"
        elif not isinstance(meta, dict):
            compatibility["reason"] = "plant metadata is unavailable"
        elif lifecycle in ("running", "finalizing", "interrupted"):
            compatibility["reason"] = f"run is {lifecycle}"
        elif lifecycle == "unknown":
            compatibility["reason"] = "run readiness is unknown"
        else:
            # Replay authorization remains with agent_catalog's fingerprint,
            # arm and scored-model checks. Discovery only records evidence.
            compatibility["reason"] = "existing replay compatibility checks are required"

        if model is not None:
            file_digests.append(("model_budget", model))
        file_digests.append(("lifecycle", lifecycle))
        member = {"id": _artifact_id(rel_dir), "relative_path": rel_dir, "kind": "agent",
                  "seed": seed, "arm": arm, "protocol": protocol,
                  "lifecycle": lifecycle, "legacy_evidence": any("legacy evidence" in x for x in issues),
                  "compatibility": compatibility, "capabilities": capabilities,
                  "source_files": sorted(set(source_files)), "issues": issues,
                  "revision": _hash(sorted(file_digests)),
                  "model_identity": (model.get("sha") if isinstance(model, dict) else None)}
        return member, updating

    def _run_item(self, run_dir: Path):
        members = []
        updating = False
        for child in sorted(run_dir.iterdir(), key=lambda p: p.name):
            if not child.is_dir() or not _AGENT.fullmatch(child.name):
                continue
            if not readiness.contained(self.root, child):
                continue
            member, changed = self._member(run_dir, child)
            if member:
                members.append(member)
                updating |= changed
        if not members:
            return None, updating
        pairs = []
        by_seed = {}
        for member in members:
            by_seed.setdefault(member["seed"], {})[member["arm"]] = member
        for seed, arms in sorted(by_seed.items()):
            missing = [arm for arm in ("sighted", "blind") if arm not in arms]
            protocols = {arms[a]["protocol"] for a in ("sighted", "blind") if a in arms}
            coherent = (not missing and all(arms[a]["lifecycle"] == "finished" for a in ("sighted", "blind"))
                        and len(protocols) == 1 and next(iter(protocols)) in ("phase-d", "d2"))
            compatible = not missing and all(arms[a]["compatibility"]["replay_allowed"] for a in ("sighted", "blind"))
            pairs.append({"seed": seed, "arms": {a: arms[a] for a in ("sighted", "blind") if a in arms},
                          "missing_arms": missing, "comparable": coherent,
                          "replay_allowed": compatible,
                          "revision": _hash(sorted((a, arms[a]["revision"]) for a in arms))})
        states = {m["lifecycle"] for m in members}
        lifecycle = ("running" if "running" in states else
                     "finalizing" if "finalizing" in states else
                     "interrupted" if "interrupted" in states else
                     "finished" if states == {"finished"} else "unknown")
        rel_path = _rel(self.root, run_dir)
        sources = sorted({source for m in members for source in m["source_files"]})
        revision = _hash(sorted((m["relative_path"], m["revision"]) for m in members))
        item = {"id": _artifact_id(rel_path), "relative_path": rel_path,
                "kind": "run_pair", "revision": revision, "lifecycle": lifecycle,
                "compatibility": {"replay_allowed": bool(pairs) and all(p["replay_allowed"] for p in pairs),
                                  "reason": None if pairs and all(p["replay_allowed"] for p in pairs)
                                  else "one or more arms are incomplete or require replay compatibility checks"},
                "capabilities": {key: any(m["capabilities"][key] for m in members)
                                 for key in ("model", "training_curve", "training_record", "evaluation_summary", "evaluation_record", "verdict")},
                "source_files": sources, "issues": [i for m in members for i in m["issues"]],
                "members": members, "pairs": pairs}
        return item, updating

    def _run_items(self):
        items = []
        updating = False
        try:
            entries = sorted(self.root.iterdir(), key=lambda p: p.name)
        except OSError as exc:
            return items, True, [{"path": ".", "message": f"filesystem access failed: {type(exc).__name__}"}]
        issues = []
        for runs in entries:
            if not _RUNS.fullmatch(runs.name) or not runs.is_dir() or not readiness.contained(self.root, runs):
                continue
            try:
                children = list(runs.iterdir())
            except OSError as exc:
                issues.append({"path": _rel(self.root, runs),
                               "message": f"filesystem access failed: {type(exc).__name__}"})
                updating = True
                continue
            has_flat = any(p.is_dir() and _AGENT.fullmatch(p.name) and readiness.contained(self.root, p)
                           for p in children)
            if has_flat:
                item, changed = self._run_item(runs)
                if item:
                    items.append(item)
                updating |= changed
            for group in children:
                if not group.is_dir() or _AGENT.fullmatch(group.name) or not readiness.contained(self.root, group):
                    continue
                try:
                    has_agents = any(p.is_dir() and _AGENT.fullmatch(p.name)
                                     and readiness.contained(self.root, p) for p in group.iterdir())
                except OSError as exc:
                    issues.append({"path": _rel(self.root, group),
                                   "message": f"filesystem access failed: {type(exc).__name__}"})
                    updating = True
                    continue
                if has_agents:
                    item, changed = self._run_item(group)
                    if item:
                        items.append(item)
                    updating |= changed
        return items, updating, issues

    def _text_items(self):
        results = self.root / "results"
        items = []
        updating = False
        if not results.is_dir() or not readiness.contained(self.root, results):
            return items, updating
        try:
            paths = [p for p in results.iterdir() if p.is_file() and _RESULT_TEXT.fullmatch(p.name)]
        except OSError:
            return items, True
        for path in sorted(paths):
            if not readiness.contained(self.root, path):
                continue
            digest, stable = self._digest(path)
            if not stable:
                updating = True
                continue
            rel_path = _rel(self.root, path)
            items.append({"id": _artifact_id(rel_path), "relative_path": rel_path,
                          "kind": "evaluation_text", "revision": _hash(digest),
                          "lifecycle": "finished", "compatibility": {"replay_allowed": False, "reason": None},
                          "capabilities": {"model": False, "training_curve": False,
                                           "training_record": False, "evaluation_summary": True,
                                           "evaluation_record": False, "verdict": False},
                          "source_files": [rel_path], "issues": [], "members": []})
        return items, updating

    def _result_context_revision(self):
        """Hash the bounded top-level R1a evidence inputs without exposing paths."""
        results = self.root / "results"
        if not results.is_dir() or not readiness.contained(self.root, results):
            return _hash([]), False
        entries = []
        updating = False
        try:
            paths = sorted((p for p in results.iterdir() if p.is_file()
                            and p.suffix.lower() in {".txt", ".json", ".md", ".csv"}),
                           key=lambda p: p.name)
        except OSError:
            return _hash(["unreadable"]), True
        # Raw legacy learning curves are now displayed by G13. Their content
        # changes the graphic snapshot; checkpoints still do not invalidate it.
        for runs in sorted(self.root.iterdir(), key=lambda p: p.name):
            if not _RUNS.fullmatch(runs.name) or not runs.is_dir() or not readiness.contained(self.root, runs):
                continue
            paths.extend(sorted(runs.glob('*/curve.csv')))
            paths.extend(sorted(runs.glob('*/*/curve.csv')))
        for path in paths:
            if not readiness.contained(self.root, path):
                continue
            digest, stable = self._digest(path)
            if not stable:
                updating = True
            elif digest:
                entries.append((_rel(self.root, path), digest))
        return _hash(sorted(entries)), updating

    def _set_item(self, set_dir: Path):
        rel_path = _rel(self.root, set_dir)
        index, stable, issue = self._json(set_dir / "index.json")
        if not stable:
            prior = self._set_last_valid.get(rel_path)
            if prior is not None:
                item = json.loads(json.dumps(prior))
                item["coherence"] = "updating / last valid snapshot"
                item["issues"] = [issue or "index is being updated"]
                return item, True
            item = {"id": _artifact_id(rel_path), "relative_path": rel_path, "kind": "agent_set",
                    "revision": _hash(["pending", issue]), "lifecycle": "unknown",
                    "coherence": "error" if issue != "awaiting stable file" else "pending",
                    "compatibility": {"replay_allowed": False, "reason": None},
                    "capabilities": {"model": False, "training_curve": False, "training_record": False,
                                     "evaluation_summary": False, "evaluation_record": False, "verdict": False},
                    "source_files": [], "issues": [issue or "index is not ready"], "members": []}
            return item, True
        if not isinstance(index, dict) or not isinstance(index.get("policies"), dict):
            issue = "index.json has no policies object"
            prior = self._set_last_valid.get(rel_path)
            if prior is not None:
                item = json.loads(json.dumps(prior))
                item["coherence"] = "updating / last valid snapshot"
                item["issues"] = [issue]
                return item, True
            return {"id": _artifact_id(rel_path), "relative_path": rel_path, "kind": "agent_set",
                    "revision": _hash(index), "lifecycle": "unknown", "coherence": "error",
                    "compatibility": {"replay_allowed": False, "reason": None},
                    "capabilities": {"model": False, "training_curve": False, "training_record": False,
                                     "evaluation_summary": False, "evaluation_record": False, "verdict": False},
                    "source_files": [_rel(self.root, set_dir / "index.json")],
                    "issues": [issue], "members": []}, False

        members = []
        issues = []
        file_ids = [("index.json", _hash(index))]
        source_files = [_rel(self.root, set_dir / "index.json")]
        member_updating = False
        coherent = True
        for policy_name, index_policy in sorted(index["policies"].items()):
            # Producers use a sanitized disk directory name, but membership and
            # display identity always come from the published index key.
            disk_name = str(policy_name).replace(" ", "_").replace("(", "").replace(")", "")
            policy_dir = set_dir / disk_name
            summary, summary_stable, summary_issue = self._json(policy_dir / "eval_summary.json")
            if not summary_stable:
                coherent = False
                member_updating |= summary_issue == "awaiting stable file"
                issues.append(f"{policy_name}: {summary_issue or 'summary unavailable'}")
                continue
            config_doc = None
            if isinstance(index_policy, dict) and "config" in index_policy:
                config_doc, config_stable, config_issue = self._json(policy_dir / "config.json")
                if not config_stable:
                    coherent = False
                    member_updating |= config_issue == "awaiting stable file"
                    issues.append(f"{policy_name}: config {config_issue or 'unavailable'}")
                    continue
            if (not isinstance(summary, dict)
                    or not readiness.duplicated_metrics_match(index_policy, summary, policy_name, config_doc)):
                coherent = False
                issues.append(f"{policy_name}: index and eval_summary disagree")
                continue
            summary_path = policy_dir / "eval_summary.json"
            members.append({"name": policy_name, "relative_path": _rel(self.root, policy_dir),
                            "lifecycle": "finished", "compatibility": {"replay_allowed": False, "reason": None},
                            "capabilities": {"model": False, "training_curve": False,
                                             "training_record": False, "evaluation_summary": True,
                                             "evaluation_record": False, "verdict": False},
                            "source_files": [_rel(self.root, summary_path)],
                            "summary": summary.get("summary"), "issues": []})
            source_files.append(_rel(self.root, summary_path))
            file_ids.append((policy_name, _hash(summary)))
            for filename in _MEMBER_FILES:
                path = policy_dir / filename
                if filename == "eval_summary.json" or not path.is_file() or not readiness.contained(self.root, path):
                    continue
                digest, file_stable = self._digest(path)
                if not file_stable:
                    member_updating = True
                elif digest:
                    source_files.append(_rel(self.root, path))
                    file_ids.append((policy_name + "/" + filename, digest))
                    if filename == "eval_record.npz":
                        members[-1]["capabilities"]["evaluation_record"] = True
                    if filename == "curve.csv":
                        members[-1]["capabilities"]["training_curve"] = True
                    if filename == "train_record.npz":
                        members[-1]["capabilities"]["training_record"] = True
                    if filename == "policy.npz":
                        members[-1]["capabilities"]["model"] = True

        # Include only bounded set-level source files consumed as evidence.
        for name in _RESULT_CONTEXT:
            path = set_dir / name
            if path.is_file() and readiness.contained(self.root, path):
                digest, file_stable = self._digest(path)
                if file_stable and digest:
                    source_files.append(_rel(self.root, path))
                    file_ids.append((name, digest))
                else:
                    coherent = False
                    member_updating = True

        if coherent and len(members) == len(index["policies"]):
            item = {"id": _artifact_id(rel_path), "relative_path": rel_path, "kind": "agent_set",
                    "revision": _hash(sorted(file_ids)), "lifecycle": "finished", "coherence": "current",
                    "compatibility": {"replay_allowed": False, "reason": None},
                    "capabilities": {"model": any(x["capabilities"]["model"] for x in members),
                                     "training_curve": any(x["capabilities"]["training_curve"] for x in members),
                                     "training_record": any(x["capabilities"]["training_record"] for x in members),
                                     "evaluation_summary": bool(members),
                                     "evaluation_record": any(x["capabilities"]["evaluation_record"] for x in members),
                                     "verdict": (set(_RESULT_CONTEXT) <= {Path(x).name for x in source_files})},
                    "source_files": sorted(set(source_files)), "issues": [], "members": members}
            self._set_last_valid[rel_path] = json.loads(json.dumps(item))
            return item, member_updating
        prior = self._set_last_valid.get(rel_path)
        if prior is not None:
            item = json.loads(json.dumps(prior))
            item["coherence"] = "updating / last valid snapshot"
            item["issues"] = issues or ["agent set is being replaced"]
            return item, True
        return {"id": _artifact_id(rel_path), "relative_path": rel_path, "kind": "agent_set",
                "revision": _hash(sorted(file_ids)), "lifecycle": "unknown", "coherence": "error",
                "compatibility": {"replay_allowed": False, "reason": None},
                "capabilities": {"model": False, "training_curve": False, "training_record": False,
                                 "evaluation_summary": False, "evaluation_record": False, "verdict": False},
                "source_files": source_files, "issues": issues, "members": members}, True

    def _set_items(self):
        base = self.root / "results" / "agents"
        items = []
        updating = False
        if not base.is_dir() or not readiness.contained(self.root, base):
            return items, updating
        try:
            dirs = sorted((p for p in base.iterdir() if p.is_dir() and readiness.contained(self.root, p)),
                          key=lambda p: p.name)
        except OSError:
            return items, True
        for path in dirs:
            if not (path / "index.json").is_file():
                continue
            item, changed = self._set_item(path)
            items.append(item)
            updating |= changed
        return items, updating

    def _plant_state(self):
        paths = [self.root / name for name in _PROVENANCE_FILES]
        identities = []
        signatures = {}
        updating = False
        for path in paths:
            if not path.is_file():
                continue
            sig = readiness.file_signature(path)
            if sig is not None:
                signatures[_rel(self.root, path)] = sig
            digest, stable = self._digest(path)
            if stable and digest:
                identities.append((_rel(self.root, path), digest))
            else:
                updating = True
        loaded = self._loaded_modules_identity()
        revision = _hash({"disk": sorted(identities), "loaded_modules": loaded})
        restart_needed = bool(loaded) and (signatures != self._disk_baseline or loaded != self._loaded_baseline)
        return revision, updating, restart_needed

    def _disk_provenance_signatures(self):
        signatures = {}
        for name in _PROVENANCE_FILES:
            path = self.root / name
            sig = readiness.file_signature(path)
            if sig is not None:
                signatures[name] = sig
        return signatures

    def _loaded_modules_identity(self):
        loaded = []
        names = ("plant", "thermal", "engine_env", "random_road", "derived",
                 "check_premise", "evaluate", "fingerprint", "ecu", "controllers.ecu")
        for name in names:
            module = sys.modules.get(name)
            if module is not None:
                loaded.append((name, str(getattr(module, "__file__", "")),
                               self._loaded_code_identity(module)))
        return loaded

    def _loaded_code_identity(self, module) -> str:
        """Hash code objects and small constants held by an already-loaded module."""
        name = getattr(module, "__name__", "")
        namespace = vars(module)
        token_parts = []
        code_parts = []
        for key, value in sorted(namespace.items()):
            if key.startswith("__"):
                continue
            if isinstance(value, types.FunctionType) and value.__module__ == name:
                token_parts.append((key, id(value.__code__)))
                code_parts.append((key, value.__code__))
            elif isinstance(value, type) and value.__module__ == name:
                methods = []
                for method_name, method in sorted(vars(value).items()):
                    if isinstance(method, (staticmethod, classmethod)):
                        method = method.__func__
                    if isinstance(method, types.FunctionType):
                        token_parts.append((key, method_name, id(method.__code__)))
                        methods.append((method_name, method.__code__))
                if methods:
                    code_parts.append((key, methods))
            elif isinstance(value, (str, int, float, bool, type(None), tuple, list, dict)):
                try:
                    encoded = _canonical(value)
                except (TypeError, ValueError):
                    continue
                if len(encoded) <= 8192:
                    token_parts.append((key, encoded.decode("utf-8", errors="replace")))
        token = _hash(token_parts)
        cached = self._loaded_module_cache.get(name)
        if cached and cached[0] == id(module) and cached[1] == token:
            return cached[2]
        code_hashes = [(key, marshal.dumps(code).hex()) for key, code in code_parts]
        digest = _hash((token, code_hashes))
        self._loaded_module_cache[name] = (id(module), token, digest)
        return digest

    def scan(self) -> dict:
        """Scan bounded families and atomically replace the published snapshot."""
        run_items, training_updating, issues = self._run_items()
        text_items, text_updating = self._text_items()
        set_items, set_updating = self._set_items()
        plant_revision, plant_updating, restart_needed = self._plant_state()
        items = sorted(run_items + text_items + set_items,
                       key=lambda x: (x["kind"], x["relative_path"]))
        training_ids = sorted((x["relative_path"], x["revision"]) for x in run_items)
        results_items = text_items + set_items
        result_ids = sorted((x["relative_path"], x["revision"]) for x in results_items)
        result_context, context_updating = self._result_context_revision()
        # Result revisions also move when provenance changes, even if the result
        # payload itself did not. Training checkpoints remain independent.
        training_revision = _hash(training_ids)
        results_revision = _hash({"items": result_ids, "context": result_context,
                                  "plant": plant_revision})
        revision = _hash({"training": training_revision, "results": results_revision,
                          "plant": plant_revision})
        self._id_paths = {x["id"]: (self.root / Path(x["relative_path"])) for x in items}
        snapshot = {"schema_version": 1, "revision": revision,
                    "training_revision": training_revision, "results_revision": results_revision,
                    "plant_revision": plant_revision, "items": items, "issues": issues,
                    "updating": bool(training_updating or text_updating or set_updating or plant_updating or context_updating),
                    "training_updating": bool(training_updating),
                    "results_updating": bool(text_updating or set_updating or context_updating or plant_updating),
                    "plant_updating": bool(plant_updating),
                    "restart_needed": bool(restart_needed)}
        self._snapshot = snapshot
        return self.snapshot()
