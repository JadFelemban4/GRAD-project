"""Read-only teaching metadata, current result summaries and source excerpts."""
from __future__ import annotations

import ast
import json
import math
import re
from pathlib import Path, PurePosixPath
from typing import Any


EX_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = EX_ROOT.parent
CONTENT_FILE = EX_ROOT / "content.json"
_EXCERPT_RADIUS = 10
_MAX_SOURCE_BYTES = 2_000_000


def _read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream)
    if not isinstance(value, dict):
        raise ValueError(f"expected a JSON object in {path.name}")
    return value


def _content(locale: str = "en") -> dict[str, Any]:
    if locale not in ("en", "ar"):
        raise ValueError("unsupported content language")
    return _read_json(EX_ROOT / "content.ar.json" if locale == "ar" else CONTENT_FILE)


def _engine_tree() -> tuple[ast.Module, list[str]]:
    path = PROJECT_ROOT / "engine_env.py"
    text = path.read_text(encoding="utf-8")
    return ast.parse(text, filename=str(path)), text.splitlines()


def _assignment_value(tree: ast.Module, name: str) -> Any:
    """Read a literal source constant without importing the simulation stack."""
    for node in tree.body:
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        if not any(isinstance(target, ast.Name) and target.id == name for target in targets):
            continue
        value = node.value
        if isinstance(value, ast.Call) and value.args:
            value = value.args[0]  # np.array([...], dtype=...)
        try:
            return ast.literal_eval(value)
        except (ValueError, TypeError):
            return None
    raise ValueError(f"source constant {name} was not found")


def _class_value(tree: ast.Module, class_name: str, name: str) -> Any:
    for node in tree.body:
        if not isinstance(node, ast.ClassDef) or node.name != class_name:
            continue
        for member in node.body:
            if isinstance(member, ast.Assign):
                targets = member.targets
            elif isinstance(member, ast.AnnAssign):
                targets = [member.target]
            else:
                continue
            if any(isinstance(target, ast.Name) and target.id == name for target in targets):
                try:
                    return ast.literal_eval(member.value)
                except (ValueError, TypeError):
                    return None
    raise ValueError(f"{class_name}.{name} was not found")


def _source_allowlist() -> set[str]:
    data = _content()
    files = {
        "engine_env.py", "plant.py", "thermal.py", "train.py", "evaluate.py",
        "REFERENCES.md", "CLAUDE.md", "validation_table.md", "compare_log.py",
        "data/derived_params.json",
        "results/premise.json", "results/README.md",
        "results/agents/terrain_dt1/index.json",
        "results/agents/terrain_dt1/README.md",
        "results/agents/terrain_dt1/KNOCK_MARGIN.md",
        "results/agents/terrain_dt1/sighted_seed0/eval_summary.json",
        "results/PHASE_D_RESULT.txt", "results/PHASE_D2_RESULT.txt",
        "results/C4_RESULT.txt",
    }
    for item in data.get("concepts", []):
        ref = item.get("source") or {}
        if isinstance(ref.get("file"), str):
            files.add(ref["file"])
    for collection in (data.get("actions", []), data.get("observations", [])):
        for item in collection:
            ref = item.get("source") or {}
            if isinstance(ref.get("file"), str):
                files.add(ref["file"])
    return files


def _safe_path(file: str) -> tuple[str, Path]:
    if not isinstance(file, str) or not file or "\\" in file:
        raise ValueError("source file must be an allowlisted project-relative path")
    pure = PurePosixPath(file)
    if pure.is_absolute() or any(part in ("", ".", "..") for part in pure.parts):
        raise ValueError("source file path is not allowed")
    normalized = pure.as_posix()
    if normalized not in _source_allowlist():
        raise ValueError("source file is not allowlisted")
    path = (PROJECT_ROOT / Path(*pure.parts)).resolve()
    try:
        path.relative_to(PROJECT_ROOT.resolve())
    except ValueError as exc:
        raise ValueError("source file path is not allowed") from exc
    if not path.is_file() or path.stat().st_size > _MAX_SOURCE_BYTES:
        raise ValueError("source file is unavailable")
    return normalized, path


def _symbol_span(lines: list[str], symbol: str) -> tuple[int, int] | None:
    if not symbol:
        return None
    escaped = re.escape(symbol)
    start = None
    indent = 0
    for index, line in enumerate(lines):
        if re.search(rf"^\s*(?:async\s+)?def\s+{escaped}\b|^\s*class\s+{escaped}\b", line):
            start = index
            indent = len(line) - len(line.lstrip())
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.strip() and len(line) - len(line.lstrip()) <= indent and not line.lstrip().startswith(("#", "\"\"\"", "'''")):
            end = index
            break
    return start, end


def _resolve_line(ref: dict[str, Any]) -> int:
    """Prefer a live symbol/variable match; retain the authored line as fallback."""
    try:
        _, path = _safe_path(ref["file"])
        lines = path.read_text(encoding="utf-8").splitlines()
    except (KeyError, OSError, ValueError):
        return int(ref.get("line", 1))
    hint = max(1, int(ref.get("line", 1)))
    match = ref.get("match") or ref.get("variable")
    if not isinstance(match, str) or not match:
        return min(hint, max(1, len(lines)))
    span = _symbol_span(lines, str(ref.get("symbol", "")))
    candidates = range(*span) if span else range(len(lines))
    hits = [i for i in candidates if match in lines[i]]
    if not hits:
        # The symbol can be an assignment or a document heading rather than a
        # Python def/class; search the allowlisted file in that case.
        hits = [i for i, line in enumerate(lines) if match in line]
    if not hits:
        return min(hint, max(1, len(lines)))
    return min(hits, key=lambda i: (abs((i + 1) - hint), i)) + 1


def _resolved_ref(ref: dict[str, Any]) -> dict[str, Any]:
    out = dict(ref)
    out["line"] = _resolve_line(ref)
    return out


def metadata(locale: str = "en") -> dict[str, Any]:
    """Return the source-derived controller contract and authored teaching copy."""
    data = _content(locale)
    data["locale"] = locale
    tree, _ = _engine_tree()
    low = _assignment_value(tree, "ACT_LO")
    high = _assignment_value(tree, "ACT_HI")
    slew = _assignment_value(tree, "SLEW")
    preview = _assignment_value(tree, "PREVIEW_S")
    obs_dim = int(_assignment_value(tree, "OBS_DIM"))
    if not (len(low) == len(high) == len(slew) == len(data["actions"]) == 5):
        raise ValueError("action metadata no longer matches engine_env.py")
    if len(data["observations"]) != obs_dim or obs_dim != 23:
        raise ValueError("observation metadata no longer matches engine_env.py")

    action_sources = [
        {"file": "engine_env.py", "symbol": "_rescale", "variable": "ACT_LO", "line": 644, "match": "ACT_LO ="},
        {"file": "engine_env.py", "symbol": "_rescale", "variable": "ACT_HI", "line": 645, "match": "ACT_HI ="},
        {"file": "engine_env.py", "symbol": "step", "variable": "SLEW", "line": 864, "match": "SLEW * self.dt"},
    ]
    actions = []
    for index, raw in enumerate(data["actions"]):
        item = dict(raw)
        item.update(lo=float(low[index]), hi=float(high[index]), slew=float(slew[index]))
        item["source"] = _resolved_ref(action_sources[0])
        item["upper_source"] = _resolved_ref(action_sources[1])
        item["slew_source"] = _resolved_ref(action_sources[2])
        item["normalized_range"] = [-1.0, 1.0]
        item["index"] = index
        actions.append(item)

    obs_matches = [
        "self.rpm / 3000.0 - 1.0", "self.map_kpa / 120.0 - 1.0", "self.tps,",
        "self.spark / 20.0 - 1.0", "(self.lam - 1.0) * 8.0",
        "(t[0] - 363.0) / 25.0", "(t[1] - 373.0) / 30.0",
        "(t[2] - 873.0) / 200.0", "(self.iat_k - 303.0) / 25.0",
        "(c[\"t_amb\"] - 293.0) / 15.0", "(c.get(\"p_baro\", 101.3) - 101.3) / 8.0",
        "c.get(\"humidity\", 0.01) * 40.0 - 0.5", "self.v / 25.0 - 1.0",
        "c[\"grade\"][self.k] * 12.0", "g * 12.0", "self.torque_req / 200.0 - 1.0",
        "self.aggression", "float(self.w[0])", "float(self.w[1])", "float(self.w[2])",
    ]
    # Four preview entries share the exact g*12 scaling expression.
    obs_source_lines = [790, 791, 792, 793, 794, 795, 796, 797, 798, 799, 800, 801, 802, 803,
                        805, 805, 805, 805, 807, 808, 809, 809, 809]
    observations = []
    for index, raw in enumerate(data["observations"]):
        item = dict(raw)
        item["index"] = index
        match_index = index if index < 14 else (14 if index < 18 else index - 3)
        item["source"] = _resolved_ref({
            "file": "engine_env.py", "symbol": "_obs", "variable": obs_matches[match_index],
            "line": obs_source_lines[index], "match": obs_matches[match_index],
        })
        observations.append(item)

    plant_tree = ast.parse((PROJECT_ROOT / "plant.py").read_text(encoding="utf-8"))
    geometry = {name: _class_value(plant_tree, "Geometry", name)
                for name in ("bore", "stroke", "n_cyl", "comp_ratio")}
    data["vehicle"].update(
        cylinders=int(geometry["n_cyl"]),
        bore_mm=float(geometry["bore"]) * 1000.0,
        stroke_mm=float(geometry["stroke"]) * 1000.0,
        displacement_cc=(math.pi / 4.0 * geometry["bore"] ** 2
                         * geometry["stroke"] * geometry["n_cyl"] * 1_000_000.0),
        compression_ratio=float(geometry["comp_ratio"]),
        gears=list(_class_value(tree, "Vehicle", "gears")),
        final_drive=float(_class_value(tree, "Vehicle", "final_drive")),
    )
    data["vehicle"]["source"] = _resolved_ref(data["vehicle"]["source"])
    data["actions"] = actions
    data["observations"] = observations
    data["preview_s"] = [float(value) for value in preview]
    data["thresholds"]["turb_k"] = float(_assignment_value(tree, "TURB_PROTECT_K"))
    data["thresholds"]["oil_k"] = float(_assignment_value(tree, "OIL_PROTECT_K"))
    data["thresholds"]["torque_tracking_tolerance"] = float(_assignment_value(tree, "TRACK_TOL"))
    derived_data = _read_json(PROJECT_ROOT / "data/derived_params.json")
    data["derived"] = {
        "data_file": "data/derived_params.json",
        "generated": derived_data.get("_generated"),
        "data_sha1": derived_data.get("_inputs", {}).get("data_sha1"),
        "note": "Derived calibration inputs; this data fingerprint is not the same as the simulator-code plant fingerprint.",
    }
    data["concepts"] = [dict(item, source=_resolved_ref(item["source"])) for item in data["concepts"]]
    return data


def _current_plant_sha() -> str:
    """Use the project fingerprint implementation, without importing engine code."""
    import sys

    root_text = str(PROJECT_ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)
    import fingerprint

    return fingerprint._sha_files(fingerprint.PLANT_FILES)


def results() -> dict[str, Any]:
    """Load only the current terrain_dt1 summary, current premise and knock diagnostic."""
    index_path = PROJECT_ROOT / "results/agents/terrain_dt1/index.json"
    premise_path = PROJECT_ROOT / "results/premise.json"
    knock_path = PROJECT_ROOT / "results/agents/terrain_dt1/KNOCK_MARGIN.md"
    index = _read_json(index_path)
    premise = _read_json(premise_path)
    knock_margin = knock_path.read_text(encoding="utf-8")
    policy = index["policies"]["sighted_seed0"]["config"]
    data_sha = policy.get("plant_inputs", {}).get("data_sha1")
    derived = _read_json(PROJECT_ROOT / "data/derived_params.json")
    current_plant_sha = _current_plant_sha()
    recorded_config_plant_sha = policy.get("plant_sha")
    actor_count = len(list((PROJECT_ROOT / "results/agents/terrain_dt1").glob("*/policy.npz")))
    paired = index.get("ablation", {})
    interval = paired.get("ci95", [None, None])
    p_values = [paired.get("p_t"), paired.get("p_wilcoxon")]
    inconclusive = (
        len(interval) == 2
        and isinstance(interval[0], (int, float))
        and isinstance(interval[1], (int, float))
        and interval[0] <= 0.0 <= interval[1]
        and all(isinstance(value, (int, float)) and value >= 0.05 for value in p_values)
    )
    return {
        "index": index,
        "premise": premise,
        "knock_margin": knock_margin,
        "verdict": "INCONCLUSIVE" if inconclusive else "REVIEW REQUIRED",
        "verdict_evidence": {
            "n": paired.get("n"), "mean": paired.get("mean"),
            "ci95": interval, "p_t": paired.get("p_t"),
            "p_wilcoxon": paired.get("p_wilcoxon"),
        },
        "caveats": [
            "The paired preview CI spans zero; this is inconclusive, not evidence of no effect.",
            "The sighted and blind actor files are exported policy weights, not the exact scored final.zip artefacts.",
            "The terrain_dt1 training config records a data fingerprint but no plant_sha; actor replays are UNVERIFIED.",
            "Most of the trained agents’ apparent advantage over hand-written policies depends on the unvalidated knock model.",
            "The turbine node is modelled from assumed constants and has no matching car sensor.",
            "The simulator’s thermal block/coolant update oscillates at dt=1 s; H/tau sweep claims remain unquotable.",
            "The integrated damage value is a proxy and is not a prediction of real component lifetime.",
        ],
        "sources": [
            {"file": "results/agents/terrain_dt1/index.json", "line": 1, "label": "Generated agent summaries, paired ablation and training provenance"},
            {"file": "results/agents/terrain_dt1/README.md", "line": 56, "label": "Ablation table and per-seed differences"},
            {"file": "results/agents/terrain_dt1/KNOCK_MARGIN.md", "line": 1, "label": "Spark-advance-capped diagnostic"},
            {"file": "results/premise.json", "line": 1, "label": "Current merged-plant hand-policy results"},
        ],
        "freshness": {
            "set": index.get("set"),
            "results_generated": index.get("generated"),
            "derived_generated": derived.get("_generated"),
            "data_sha1": data_sha,
            "current_plant_sha": current_plant_sha,
            "training_commit": policy.get("git_commit"),
            "training_worktree_dirty": policy.get("git_dirty"),
            "training_plant_sha": recorded_config_plant_sha,
            "trained_actor_exports": actor_count,
            "recorded_scored_actor_sha": None,
            "replay_status": "UNVERIFIED" if actor_count else "UNAVAILABLE",
            "paired_n": paired.get("n"),
        },
        "limitations": _content()["limitations"],
    }


def source(file: str, line: int) -> dict[str, Any]:
    """Return a numbered ±10-line excerpt from an allowlisted repository file."""
    if isinstance(line, bool) or not isinstance(line, int) or line < 1:
        raise ValueError("line must be a positive one-based integer")
    rel, path = _safe_path(file)
    lines = path.read_text(encoding="utf-8").splitlines()
    if line > len(lines):
        raise ValueError("line is beyond the end of the source file")
    start = max(1, line - _EXCERPT_RADIUS)
    end = min(len(lines), line + _EXCERPT_RADIUS)
    return {
        "file": rel,
        "line": line,
        "start": start,
        "end": end,
        "lines": [{"number": number, "text": lines[number - 1]} for number in range(start, end + 1)],
    }
