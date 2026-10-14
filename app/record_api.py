"""Registry-bound GET routes for historical saved records."""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse, PlainTextResponse

from app import record_reader

LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost)(:\d{1,5})?$")
NO_STORE = {"Cache-Control": "no-store"}
_ID = re.compile(r"^rec_[0-9a-f]{24}$")


def _host_ok(request: Request) -> bool:
    return bool(LOCAL_HOST.fullmatch(request.headers.get("host") or ""))


_JSON_CACHE: dict[tuple[str, tuple], dict | None] = {}


def _json(path: Path, cap: int = 4 * 1024 * 1024, root: Path | None = None) -> dict | None:
    try:
        path = Path(path).resolve()
        if root is not None and not path.is_relative_to(Path(root).resolve()):
            return None
        signature = record_reader._stat_signature(path)
        key = (str(path), signature)
        if key in _JSON_CACHE:
            return _JSON_CACHE[key]
        if signature[0] > cap:
            return None
        record_reader.content_revision(path, max_bytes=cap)
        raw = path.read_bytes()
        if record_reader._stat_signature(path) != signature:
            return None
        value = json.loads(raw.decode("utf-8-sig"), parse_constant=lambda _: None)
        result = value if isinstance(value, dict) else None
        if len(_JSON_CACHE) >= 2048:
            _JSON_CACHE.clear()
        _JSON_CACHE[key] = result
        return result
    except (OSError, ValueError, UnicodeError):
        return None


def _policy_disk_name(name: str) -> str:
    return str(name).replace(" ", "_").replace("(", "").replace(")", "")


def _record_id(relative_path: str, kind: str) -> str:
    return "rec_" + hashlib.sha256(f"{relative_path}\0{kind}".encode()).hexdigest()[:24]


def _record_item(root: Path, relative_path: str, policy: str, kind: str,
                 expected_file: str, protocol: str | None, source_identity: dict) -> dict:
    directory = (root / relative_path).resolve()
    item = {"id": _record_id(relative_path, kind), "relative_path": relative_path,
            "policy": policy, "kind": kind, "protocol": protocol,
            "expected_file": expected_file, "source_revision": None,
            "archive_revision": None, "sidecar_revision": None,
            "state": "unavailable", "reason": "missing_record", "provenance": source_identity}
    if not directory.is_relative_to(root):
        item.update(state="invalid", reason="source_outside_project")
        return item
    try:
        sidecars = [directory / name for name in ("config.json", "meta.json", "eval_summary.json")]
        rel = Path(relative_path)
        if rel.parts[:2] == ("results", "agents"):
            sidecars.append(directory.parent / "index.json")
        identity_parts = []
        for sidecar in sidecars:
            resolved = sidecar.resolve()
            if not resolved.is_relative_to(root):
                item.update(state="invalid", reason="sidecar_outside_project")
                return item
            if resolved.is_file():
                revision = record_reader.content_revision(resolved, max_bytes=4 * 1024 * 1024)
                identity_parts.append((sidecar.relative_to(root).as_posix(), revision))
            else:
                identity_parts.append((sidecar.relative_to(root).as_posix(), None))
        sidecar_revision = hashlib.sha256(json.dumps(identity_parts, separators=(",", ":"),
                                              sort_keys=True).encode()).hexdigest()
        item["sidecar_revision"] = sidecar_revision
        item["source_revision"] = hashlib.sha256(json.dumps(
            {"archive": None, "sidecars": sidecar_revision},
            sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        path = directory / expected_file
        if path.resolve().is_relative_to(root) and path.is_file():
            archive_revision = record_reader.content_revision(path)
            source_revision = hashlib.sha256(json.dumps(
                {"archive": archive_revision, "sidecars": sidecar_revision},
                sort_keys=True, separators=(",", ":")).encode()).hexdigest()
            item.update(archive_revision=archive_revision, source_revision=source_revision,
                        state="available", reason=None)
        elif path.exists() and not path.resolve().is_relative_to(root):
            item.update(state="invalid", reason="source_outside_project")
        if kind == "evaluation":
            sidecar = _json(directory / "eval_summary.json", root=root)
            if sidecar and sidecar.get("policy") and sidecar["policy"] != policy:
                item.update(state="invalid", reason="recorded_policy_mismatch")
            elif sidecar and sidecar.get("protocol"):
                item["protocol"] = sidecar["protocol"]
                item["provenance"]["protocol"] = sidecar["protocol"]
                item["provenance"]["protocol_evidence"] = "eval_summary.json"
    except FileNotFoundError:
        pass
    except (OSError, ValueError) as exc:
        item.update(state="invalid", reason=str(exc) if isinstance(exc, ValueError) else "source_unreadable")
    return item


def discover_records(root: Path) -> list[dict]:
    """Discover only known run and published-set layouts under the project root."""
    root = Path(root).resolve()
    records: list[dict] = []
    for runs_dir in sorted(root.glob("runs*")):
        if not runs_dir.is_dir() or not runs_dir.resolve().is_relative_to(root):
            continue
        for policy_dir in sorted(runs_dir.iterdir()):
            if not policy_dir.is_dir() or not ((policy_dir / "meta.json").exists()
                                                 or (policy_dir / "train_record.npz").exists()
                                                 or (policy_dir / "eval_record.npz").exists()):
                continue
            if not policy_dir.resolve().is_relative_to(root):
                continue
            rel = policy_dir.relative_to(root).as_posix()
            meta = _json(policy_dir / "meta.json", root=root) or {}
            policy = policy_dir.name
            source = {"policy": policy, "source_revision": None, "source_revision_evidence": "record archive hash",
                      "generation": meta.get("git_head"), "generation_status": "partial" if meta.get("git_head") else "unknown",
                      "recorded_source": {key: meta.get(key) for key in
                                          ("git_head", "plant_sha", "plant_text_sha", "protocol", "train_dt",
                                           "train_road", "scenario") if meta.get(key) is not None},
                      "note": "Historical provenance is not complete enough to claim current-plant compatibility."}
            records.append(_record_item(root, rel, policy, "training", "train_record.npz", None, source))
            # Runs can contain eval_record.npz only after a user explicitly
            # published one; do not infer evaluation from model or curve files.
            if (policy_dir / "eval_record.npz").exists():
                records.append(_record_item(root, rel, policy, "evaluation", "eval_record.npz", None, source.copy()))

    agents_root = root / "results" / "agents"
    if agents_root.is_dir():
        for set_dir in sorted(agents_root.iterdir()):
            if not set_dir.is_dir() or not set_dir.resolve().is_relative_to(root):
                continue
            index = _json(set_dir / "index.json", root=root) or {}
            policies = index.get("policies")
            if not isinstance(policies, dict):
                continue
            for policy in sorted(policies):
                policy_dir = set_dir / _policy_disk_name(policy)
                if not policy_dir.resolve().is_relative_to(root):
                    continue
                summary = _json(policy_dir / "eval_summary.json", root=root) or {}
                protocol = summary.get("protocol") if isinstance(summary.get("protocol"), str) else None
                config = _json(policy_dir / "config.json", root=root) or {}
                source = {"policy": policy, "set": set_dir.name, "source_revision": None,
                          "source_revision_evidence": "record archive hash",
                          "generation": config.get("generation") or config.get("recorded_generation"),
                          "generation_status": "recorded" if config.get("generation") or config.get("recorded_generation") else "unknown",
                          "plant_fingerprint": config.get("plant_fingerprint"),
                          "note": "Archive identity is verified; missing generation or plant fields remain unknown."}
                rel = policy_dir.relative_to(root).as_posix()
                records.append(_record_item(root, rel, policy, "evaluation", "eval_record.npz", protocol, source))
                if (policy_dir / "train_record.npz").exists():
                    records.append(_record_item(root, rel, policy, "training", "train_record.npz", None, source.copy()))
    return sorted(records, key=lambda x: (x["relative_path"], x["kind"]))


def _resolve(root: Path, record_id: str) -> tuple[dict, Path, dict | None]:
    if not _ID.fullmatch(record_id):
        raise KeyError(record_id)
    item = next((x for x in discover_records(root) if x["id"] == record_id), None)
    if item is None:
        raise KeyError(record_id)
    path = (root / item["relative_path"] / item["expected_file"]).resolve()
    if not path.is_relative_to(root.resolve()):
        raise KeyError(record_id)
    directory = path.parent.resolve()
    if not directory.is_relative_to(root):
        raise KeyError(record_id)
    config = _json(directory / "config.json", root=root) or _json(directory / "meta.json", root=root)
    return item, path, config


def install_record_routes(app, root: Path) -> None:
    """Install the three read-only record routes on the simulation app."""
    root = Path(root).resolve()

    def refuse(request):
        return not _host_ok(request)

    def listing(request: Request):
        if refuse(request):
            return PlainTextResponse("refused: this page answers 127.0.0.1 and localhost only", status_code=403, headers=NO_STORE)
        return JSONResponse({"records": discover_records(root), "indexing": "zero-based episodes and samples"}, headers=NO_STORE)

    def metadata(request: Request, record_id: str):
        if refuse(request):
            return PlainTextResponse("refused: this page answers 127.0.0.1 and localhost only", status_code=403, headers=NO_STORE)
        try:
            item, path, config = _resolve(root, record_id)
            if item["state"] == "invalid":
                raise record_reader.RecordError(item["reason"])
            result = record_reader.read_record_meta(path, item["kind"], config)
            result.update({k: item[k] for k in ("id", "relative_path", "policy", "protocol", "state", "reason", "provenance")})
            result.update({k: item[k] for k in ("source_revision", "archive_revision", "sidecar_revision")})
            return JSONResponse(result, headers=NO_STORE)
        except KeyError:
            raise HTTPException(404, "Unknown record")
        except FileNotFoundError:
            raise HTTPException(404, "Record unavailable")
        except record_reader.RecordError as exc:
            raise HTTPException(422, str(exc))

    def frames(request: Request, record_id: str, episode: int = 0, start: int = 0, count: int = 200):
        if refuse(request):
            return PlainTextResponse("refused: this page answers 127.0.0.1 and localhost only", status_code=403, headers=NO_STORE)
        try:
            item, path, config = _resolve(root, record_id)
            if item["state"] == "invalid":
                raise record_reader.RecordError(item["reason"])
            result = record_reader.read_record_window(path, item["kind"], episode, start, count, config)
            result["provenance"] = item["provenance"]
            result.update({k: item[k] for k in ("source_revision", "archive_revision", "sidecar_revision")})
            return JSONResponse(result, headers=NO_STORE)
        except KeyError:
            raise HTTPException(404, "Unknown record")
        except FileNotFoundError:
            raise HTTPException(404, "Record unavailable")
        except record_reader.RecordError as exc:
            raise HTTPException(422, str(exc))

    app.add_api_route("/api/records", listing, methods=["GET"])
    app.add_api_route("/api/records/{record_id}/meta", metadata, methods=["GET"])
    app.add_api_route("/api/records/{record_id}/frames", frames, methods=["GET"])

