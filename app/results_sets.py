"""Read published agent-set artifacts into the results-panel contract.

This module reads only index, evaluation summary, config, knock-margin and
curve files. It does not load training or evaluation code and never writes.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from pathlib import Path


MAX_JSON_BYTES = 16 * 1024 * 1024
MAX_CURVE_BYTES = 12 * 1024 * 1024
MAX_CURVE_ROWS = 250_000
METRICS = ("damage", "damage_thermal", "fuel", "ret", "torque_viol", "peak_turb", "knock",
           "cut_pct", "thermal_cut_pct", "fuel_vs_baseline_pct")
ACTUATORS = (
    ("spark trim (deg)", "spark_trim", "deg"),
    ("lambda trim", "lambda_trim", "ratio"),
    ("boost trim (kPa)", "boost_trim", "kPa"),
    ("fan duty", "fan_duty", "fraction"),
    ("pump duty", "pump_duty", "fraction"),
)


def _inside(path: Path, root: Path) -> Path:
    path, root = path.resolve(), root.resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise ValueError("path escapes repository root") from exc
    return path


def _read_bytes(path: Path, limit: int) -> bytes:
    """Read a bounded file and reject replacement or mutation during the read."""
    before = path.stat()
    if not path.is_file() or before.st_size > limit:
        raise ValueError("not a bounded regular file")
    data = path.read_bytes()
    after = path.stat()
    signature = lambda st: (st.st_dev, st.st_ino, st.st_size, st.st_mtime_ns)
    if signature(before) != signature(after) or len(data) != after.st_size:
        raise ValueError("file changed while being read")
    return data


def _json(path: Path) -> tuple[dict, bytes]:
    data = _read_bytes(path, MAX_JSON_BYTES)
    value = json.loads(data.decode("utf-8-sig"), parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)))
    if not isinstance(value, dict):
        raise ValueError("JSON root must be an object")
    return value, data


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _digest(*values: bytes) -> str:
    h = hashlib.sha256()
    for value in values:
        h.update(len(value).to_bytes(8, "big"))
        h.update(value)
    return h.hexdigest()


def _policy_folder(name: str) -> str:
    # Same naming rule as record_agents.py:451; this is intentionally a text
    # port so importing the recorder cannot trigger training dependencies.
    return name.replace(" ", "_").replace("(", "").replace(")", "")


def _panel(panel_id, kind, source_files, revision, *, state="available", reason=None,
           x_label="policy", x_unit="index", y_label="damage", y_unit="damage_units",
           caveats=None, series=None, channels=None):
    result = {
        "id": panel_id, "group": "evaluation" if panel_id != "G13" else "training",
        "kind": kind, "state": state, "source_files": list(dict.fromkeys(source_files)),
        "caveats": list(caveats or []), "reason": reason,
        "axes": {"x": {"label": x_label, "unit": x_unit}, "y": {"label": y_label, "unit": y_unit}},
        "series": series or [], "revision": revision,
    }
    if channels is not None:
        result["channels"] = channels
    return result


def _unavailable(panel_id, source, reason, caveat, *, revision="", kind="scatter"):
    return _panel(panel_id, kind, [source], revision, state="unavailable", reason=reason,
                  caveats=[caveat], series=[])


def _metric_equal(indexed, summary):
    for key in METRICS:
        if key not in indexed or key not in summary or indexed[key] != summary[key]:
            return False
    return True


def _paired_seed(name, summary, config):
    prefix, sep, tail = name.rpartition("_seed")
    if not sep or prefix not in ("sighted", "blind") or not tail.isdigit():
        return None
    seed = int(tail)
    if config.get("seed") != seed:
        return None
    return prefix, seed


def _seed_label(name):
    prefix, sep, tail = name.rpartition("_seed")
    if sep and prefix in ("sighted", "blind") and tail.isdigit():
        return prefix, int(tail)
    return None


def _omissions(issues, codes):
    return [{"policy": issue.get("policy"), "code": issue["code"],
             "source": issue.get("path"), "reason": issue.get("reason")}
            for issue in issues if issue.get("code") in codes]


def _worst_episode(record, metric):
    values = record.get("episodes")
    target = record.get("summary", {}).get(metric, {}).get("worst")
    if not isinstance(values, list) or not _finite(target):
        return None
    for index, episode in enumerate(values):
        if isinstance(episode, dict) and episode.get(metric) == target:
            return index
    return None


def _curve_panel(run_dir: Path, root: Path) -> dict:
    root = Path(root).resolve()
    run_dir = _inside(Path(run_dir), root)
    curve = _inside(run_dir / "curve.csv", root)
    rel = curve.relative_to(root).as_posix()
    try:
        raw = _read_bytes(curve, MAX_CURVE_BYTES)
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if not reader.fieldnames or "episode" not in reader.fieldnames or "return" not in reader.fieldnames:
            raise ValueError("curve.csv requires episode and return columns")
        points = []
        for source_index, row in enumerate(reader):
            if source_index >= MAX_CURVE_ROWS:
                raise ValueError("curve.csv exceeds row limit")
            try:
                episode_raw, return_raw = row["episode"], row["return"]
                episode_value, return_value = float(episode_raw), float(return_raw)
            except (TypeError, ValueError, KeyError) as exc:
                raise ValueError("curve.csv has an invalid episode or return") from exc
            if not math.isfinite(episode_value) or not math.isfinite(return_value):
                raise ValueError("curve.csv has a non-finite episode or return")
            points.append({"x": episode_value, "y": return_value, "episode": episode_value,
                           "source_index": source_index})
        if not points:
            raise ValueError("curve.csv has no samples")
        return _panel("G13", "line", [rel], _digest(raw), x_label="episode", x_unit="episode",
                      y_label="return", y_unit="return", series=[{
                          "id": run_dir.name, "label": run_dir.name, "role": "recorded",
                          "points": points,
                      }])
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        return _unavailable("G13", rel, type(exc).__name__, "curve_unavailable", revision="", kind="line")


def read_training_panels(run_dir: Path, root: Path) -> list[dict]:
    """Read a run's raw curve from a path confined to the repository root."""
    return [_curve_panel(Path(run_dir), Path(root))]


def _build_set(root: Path, set_dir: Path, issues: list[dict]) -> dict:
    rel_dir = set_dir.relative_to(root).as_posix()
    index_path = _inside(set_dir / "index.json", root)
    index, index_bytes = _json(index_path)
    policies = index.get("policies")
    if not isinstance(policies, dict) or not policies:
        raise ValueError("index.json has no named policies")
    members = {}
    used_bytes = [index_bytes]
    sources = [index_path.relative_to(root).as_posix()]
    for name, indexed in policies.items():
        if not isinstance(name, str) or not name or not isinstance(indexed, dict):
            issues.append({"code": "invalid_policy_entry", "path": sources[0]})
            continue
        folder = _policy_folder(name)
        try:
            member_dir = _inside(set_dir / folder, root)
            summary_path = _inside(member_dir / "eval_summary.json", root)
        except ValueError as exc:
            issues.append({"code": "invalid_policy_path", "policy": name,
                           "path": sources[0], "reason": str(exc)})
            continue
        try:
            record, summary_bytes = _json(summary_path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            issues.append({"code": "member_unreadable", "policy": name,
                           "path": summary_path.relative_to(root).as_posix(),
                           "reason": type(exc).__name__})
            continue
        try:
            config_path = _inside(member_dir / "config.json", root)
            config, config_bytes = _json(config_path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            config, config_bytes = {}, b""
            config_path = member_dir / "config.json"
            if "_seed" in name:
                issues.append({"code": "config_unavailable", "policy": name,
                               "path": config_path.relative_to(root).as_posix(),
                               "reason": type(exc).__name__})
        used_bytes.append(summary_bytes)
        if config_bytes:
            used_bytes.append(config_bytes)
            sources.append(config_path.relative_to(root).as_posix())
        sources.append(summary_path.relative_to(root).as_posix())
        if record.get("policy") != name:
            issues.append({"code": "identity_mismatch", "policy": name,
                           "path": summary_path.relative_to(root).as_posix()})
            continue
        indexed_config = indexed.get("config")
        config_status = "missing" if not config else "recorded"
        config_conflict = isinstance(indexed_config, dict) and indexed_config != config
        config_protocol = config.get("protocol")
        if config_protocol and config_protocol != record.get("protocol"):
            config_conflict = True
        if config_conflict:
            config_status = "mismatch"
            issues.append({"code": "config_mismatch", "policy": name,
                           "path": config_path.relative_to(root).as_posix()})
            continue
        summary = record.get("summary")
        if not isinstance(summary, dict) or not _metric_equal(indexed, summary):
            issues.append({"code": "summary_mismatch", "policy": name,
                           "path": summary_path.relative_to(root).as_posix()})
            continue
        member = {"name": name, "record": record, "summary": summary, "config": config,
                  "config_status": config_status, "protocol": record.get("protocol")}
        members[name] = member
    # Report stale seed folders without reading them or admitting them as data.
    listed = {_policy_folder(name) for name in policies if isinstance(name, str)}
    try:
        children = list(set_dir.iterdir())
    except OSError:
        children = []
    for child in children:
        if child.is_dir() and "_seed" in child.name and child.name not in listed:
            issues.append({"code": "stale_policy_folder", "path": child.relative_to(root).as_posix()})

    all_protocols = sorted({m["protocol"] for m in members.values() if isinstance(m["protocol"], str)})
    protocol_incompatible = (len(all_protocols) > 1 or
                             sum(isinstance(m["protocol"], str) for m in members.values()) != len(members))
    if len(all_protocols) > 1:
        issues.append({"code": "protocol_mismatch", "path": sources[0], "protocols": all_protocols})
    elif protocol_incompatible:
        issues.append({"code": "protocol_missing", "path": sources[0]})
    for name, member in members.items():
        member["pair_seed"] = _paired_seed(name, member["summary"], member["config"])

    # G07: exact medians, published quartile endpoints and published worst values.
    g07_series, g07_worst = [], []
    for position, name in enumerate(policies):
        member = members.get(name)
        if member is None:
            continue
        damage = member["summary"].get("damage")
        if not isinstance(damage, dict) or not all(_finite(damage.get(k)) for k in ("median", "q1", "q3", "worst")):
            issues.append({"code": "damage_statistics_missing", "policy": name})
            continue
        x = len(g07_series)
        label = name
        pair = member.get("pair_seed")
        pair_seed = pair[1] if pair is not None else None
        median_point = {"x": x, "y": damage["median"], "low": damage["q1"],
                        "high": damage["q3"], "label": label}
        if pair_seed is not None:
            median_point["seed"] = pair_seed
        g07_series.append({"id": name, "label": name, "role": "median",
                           "points": [median_point]})
        episode = _worst_episode(member["record"], "damage")
        point = {"x": x, "y": damage["worst"], "label": label}
        if pair_seed is not None:
            point["seed"] = pair_seed
        if episode is not None:
            point["episode"] = episode
            point["source_index"] = episode
        g07_worst.append({"id": name, "label": name, "role": "worst", "points": [point]})
    g07_sources = [sources[0], *[s for s in sources if s.endswith("eval_summary.json")]]
    revision = _digest(*used_bytes)
    g07 = _panel("G07", "bar", g07_sources, revision, x_label="policy", x_unit="category",
                 y_label="damage", y_unit="damage_score", series=[*g07_series, *g07_worst])
    g07["omissions"] = _omissions(issues, {"member_unreadable", "identity_mismatch", "summary_mismatch",
                                            "config_mismatch", "damage_statistics_missing"})
    if protocol_incompatible:
        g07["state"], g07["reason"] = "withheld", "Member evaluation protocols differ within this set."
        g07["caveats"] = ["protocol_mismatch"]
        g07["series"] = []
    if not g07_series:
        g07["state"], g07["reason"] = "unavailable", "No member has validated damage summary values."

    # G08: matched seeds only, keeping each seed's two arms connected.
    by_seed = {arm: {} for arm in ("sighted", "blind")}
    listed_by_seed = {arm: {} for arm in ("sighted", "blind")}
    for name in policies:
        parsed = _seed_label(name) if isinstance(name, str) else None
        if parsed is not None:
            listed_by_seed[parsed[0]][parsed[1]] = name
    for member in members.values():
        pair = member.get("pair_seed")
        if pair is None:
            continue
        arm, seed = pair
        if protocol_incompatible:
            continue
        by_seed[arm][seed] = member
    pair_series = []
    thermal_series = []
    unpaired_rows = []
    for seed in sorted(set(listed_by_seed["sighted"]) | set(listed_by_seed["blind"])):
        sighted_name = listed_by_seed["sighted"].get(seed)
        blind_name = listed_by_seed["blind"].get(seed)
        sighted = by_seed["sighted"].get(seed)
        blind = by_seed["blind"].get(seed)
        if sighted is None or blind is None:
            invalid = {issue.get("policy"): issue.get("code") for issue in issues if issue.get("policy")}
            reason = ("protocol_mismatch" if protocol_incompatible else
                      invalid.get(sighted_name) or invalid.get(blind_name) or "unpaired_seed")
            unpaired_rows.append([seed, sighted_name, blind_name, reason])
            continue
        pair = []
        thermal = []
        for x, arm in enumerate(("sighted", "blind")):
            member = sighted if arm == "sighted" else blind
            for metric, target in (("damage", pair), ("damage_thermal", thermal)):
                summary = member["summary"].get(metric)
                value = summary.get("median") if isinstance(summary, dict) else None
                if _finite(value):
                    target.append({"x": x, "y": value, "seed": seed, "label": arm})
        if len(pair) == 2:
            pair_series.append({"id": f"seed-{seed}", "label": f"seed {seed}", "role": "matched_pair", "points": pair})
        if len(thermal) == 2:
            thermal_series.append({"id": f"seed-{seed}", "label": f"seed {seed}", "role": "matched_pair", "points": thermal})
    g08_sources = [s for s in sources if s.endswith("eval_summary.json")]
    g08 = _panel("G08", "line", g08_sources, revision, x_label="agent_arm", x_unit="category",
                 y_label="damage", y_unit="damage_score", caveats=[],
                 channels=[{"id": "total", "label": "total damage", "unit": "damage_score",
                            "axes": {"x": {"label": "agent_arm", "unit": "category"}, "y": {"label": "damage", "unit": "damage_score"}},
                            "series": pair_series,
                            **({} if pair_series else {"state": "unavailable", "reason": "No validated matched total-damage pair.", "source_files": g08_sources})},
                           {"id": "thermal", "label": "thermal damage", "unit": "damage_score",
                            "axes": {"x": {"label": "agent_arm", "unit": "category"}, "y": {"label": "damage_thermal", "unit": "damage_score"}},
                            "series": thermal_series,
                            **({} if thermal_series else {"state": "unavailable", "reason": "Thermal damage is missing from validated eval_summary files.", "source_files": g08_sources})}],
                 )
    g08["table"] = {"columns": ["seed", "sighted_policy", "blind_policy", "reason"], "rows": unpaired_rows}
    g08["omissions"] = _omissions(issues, {"member_unreadable", "identity_mismatch", "summary_mismatch",
                                            "config_mismatch", "config_unavailable"})
    if unpaired_rows:
        g08["caveats"].append("unpaired_seeds")
        g08["omissions"].extend({"seed": row[0], "policy": row[1] or row[2], "code": row[3],
                                "source": g08_sources} for row in unpaired_rows)
    if not pair_series:
        g08["state"], g08["reason"] = "unavailable", "No sighted/blind seed pair shares a validated protocol."
        g08["caveats"] = ["matched_pairs_missing"]
    if protocol_incompatible:
        g08["state"], g08["reason"] = "withheld", "Member evaluation protocols differ within this set."
        g08["caveats"] = ["protocol_mismatch"]
        for channel in g08["channels"]:
            channel["series"] = []
    elif not thermal_series:
        g08["caveats"] = ["thermal_damage_missing"]

    # G09: knock-margin comparator is admitted only after the exact old-value check.
    knock_path = _inside(set_dir / "knock_margin.json", root)
    knock_rel = knock_path.relative_to(root).as_posix()
    knock_values, knock_bytes = None, None
    try:
        if knock_path.is_file():
            knock_values, knock_bytes = _json(knock_path)
            used_bytes.append(knock_bytes)
            sources.append(knock_rel)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        issues.append({"code": "knock_margin_unreadable", "path": knock_rel, "reason": type(exc).__name__})
    g09_series = []
    knock_omissions = []
    mismatch = False
    knock_agents = knock_values.get("agents") if isinstance(knock_values, dict) else None
    if isinstance(knock_agents, dict):
        for member in members.values():
            item = knock_agents.get(member["name"])
            if not isinstance(item, dict):
                knock_omissions.append({"policy": member["name"], "code": "knock_margin_missing",
                                        "source": knock_rel})
                continue
            orig = item.get("cut_orig")
            recorded = member["summary"].get("cut_pct")
            if not (_finite(orig) and _finite(recorded)) or orig != recorded:
                mismatch = True
                issues.append({"code": "knock_cut_mismatch", "policy": member["name"], "path": knock_rel})
                knock_omissions.append({"policy": member["name"], "code": "knock_cut_mismatch",
                                        "source": knock_rel})
                continue
            capped = item.get("cut")
            if not _finite(capped):
                knock_omissions.append({"policy": member["name"], "code": "knock_capped_value_missing",
                                        "source": knock_rel})
                continue
            g09_series.append({"id": member["name"], "label": member["name"], "role": "agent",
                               "points": [{"x": 0, "y": orig, "label": "original"},
                                          {"x": 1, "y": capped, "label": "spark_capped"}]})
        for name, member in members.items():
            if "seed" not in name and name in ("current-grade", "predictive (hand)"):
                value = member["summary"].get("cut_pct")
                if _finite(value):
                    g09_series.append({"id": name, "label": name, "role": "hand_written_comparator",
                                       "points": [{"x": 2, "y": value, "label": "hand_written"}]})
    if mismatch:
        g09 = _panel("G09", "line", [knock_rel, *g07_sources], revision, state="withheld",
                     reason="knock_margin cut_orig does not exactly match eval_summary cut_pct.",
                     x_label="evaluation", x_unit="category", y_label="damage_cut", y_unit="percent",
                     caveats=["knock_cut_mismatch"])
    elif not g09_series:
        g09 = _unavailable("G09", knock_rel, "No validated knock-margin comparison is available.",
                            "knock_margin_missing", revision=revision, kind="line")
    else:
        g09 = _panel("G09", "line", [knock_rel, *g07_sources], revision, x_label="evaluation",
                     x_unit="category", y_label="damage_cut", y_unit="percent", series=g09_series)
    g09["caveats"] = list(dict.fromkeys([*g09.get("caveats", []), "diagnostic_spark_cap_not_retrained"]))
    if not isinstance(knock_agents, dict):
        knock_omissions.extend({"policy": name, "code": "knock_margin_missing", "source": knock_rel}
                               for name in members)
    g09["omissions"] = [*_omissions(issues, {"member_unreadable", "identity_mismatch", "summary_mismatch",
                                              "config_mismatch"}), *knock_omissions]
    if protocol_incompatible:
        g09["state"], g09["reason"] = "withheld", "Member evaluation protocols differ within this set."
        g09["caveats"] = ["protocol_mismatch"]
        g09["series"] = []

    # G10: five actuator series, each retaining its recorded p5/p50/p95 for both regions.
    action_channels = []
    action_sources = [s for s in sources if s.endswith("eval_summary.json")]
    action_omissions = []
    policy_positions = {name: position for position, name in enumerate(policies)}
    for action_key, action_id, unit in ACTUATORS:
        region_series = []
        for region in ("flat", "climb"):
            points = []
            for name in policies:
                member = members.get(name)
                actions = member["record"].get("actions") if member else None
                raw = actions.get(action_key, {}).get(region) if isinstance(actions, dict) else None
                if not isinstance(raw, dict) or not all(_finite(raw.get(k)) for k in ("p5", "p50", "p95")):
                    continue
                points.append({"x": policy_positions[name], "y": raw["p50"], "low": raw["p5"], "high": raw["p95"], "label": name})
            for name in policies:
                member = members.get(name)
                actions = member["record"].get("actions") if member else None
                raw = actions.get(action_key, {}).get(region) if isinstance(actions, dict) else None
                if not isinstance(raw, dict) or not all(_finite(raw.get(k)) for k in ("p5", "p50", "p95")):
                    action_omissions.append({"policy": name, "channel": action_id, "region": region,
                                             "code": "actuator_statistics_missing",
                                             "source": f"{rel_dir}/{_policy_folder(name)}/eval_summary.json"})
            if points:
                region_series.append({"id": region, "label": region, "role": "median_applied", "points": points})
        action_channels.append({"id": action_id, "label": action_key, "unit": unit,
                                "axes": {"x": {"label": "policy", "unit": "category"}, "y": {"label": action_id, "unit": unit}},
                                "series": region_series,
                                **({} if region_series else {"state": "unavailable", "reason": "Recorded actuator percentiles are missing.", "source_files": action_sources})})
    g10 = _panel("G10", "bar", action_sources, revision, x_label="policy", x_unit="category",
                 y_label="actuator_value", y_unit="recorded_unit", channels=action_channels)
    if not any(channel["series"] for channel in action_channels):
        g10["state"], g10["reason"] = "unavailable", "No recorded actuator percentile summaries are available."
        g10["caveats"] = ["actuator_statistics_missing"]
    elif any(not channel["series"] for channel in action_channels):
        g10["caveats"] = ["actuator_channel_missing"]
    g10["omissions"] = [*_omissions(issues, {"member_unreadable", "identity_mismatch", "summary_mismatch", "config_mismatch"}), *action_omissions]
    if protocol_incompatible:
        g10["state"], g10["reason"] = "withheld", "Member evaluation protocols differ within this set."
        g10["caveats"] = ["protocol_mismatch"]
        for channel in g10["channels"]:
            channel["series"] = []

    # G12: paired policy medians from the same set; units are absolute.
    trade_channels = []
    trade_omissions = []
    for metric in ("damage", "damage_thermal"):
        series_by_arm = {"sighted": [], "blind": [], "other": []}
        for name in policies:
            member = members.get(name)
            if not member:
                continue
            damage = member["summary"].get(metric)
            fuel = member["summary"].get("fuel")
            if not isinstance(damage, dict) or not isinstance(fuel, dict):
                trade_omissions.append({"policy": name, "code": "trade_metrics_missing",
                                        "source": g07_sources})
                continue
            x, y = damage.get("median"), fuel.get("median")
            if not (_finite(x) and _finite(y)):
                trade_omissions.append({"policy": name, "code": "trade_metrics_missing",
                                        "source": g07_sources})
                continue
            pair = member.get("pair_seed")
            arm = pair[0] if pair else ("other" if name not in ("baseline ECU",) else "other")
            series_by_arm[arm].append({"x": x, "y": y, "seed": pair[1] if pair else None,
                                       "label": name})
        trade_channels.append({"id": metric, "label": metric, "unit": "damage_score",
                               "axes": {"x": {"label": metric, "unit": "damage_score"},
                                        "y": {"label": "fuel", "unit": "fuel_g"}},
                               "series": [{"id": arm, "label": arm, "role": "policy",
                                           "points": points} for arm, points in series_by_arm.items() if points]})
    g12 = _panel("G12", "scatter", g07_sources, revision, x_label="damage", x_unit="damage_score",
                 y_label="fuel", y_unit="fuel_g", channels=trade_channels)
    if not any(ch["series"] for ch in trade_channels):
        g12["state"], g12["reason"] = "unavailable", "No same-set damage and fuel medians are available."
        g12["caveats"] = ["trade_metrics_missing"]
    if protocol_incompatible:
        g12["state"], g12["reason"] = "withheld", "Member evaluation protocols differ within this set."
        g12["caveats"] = ["protocol_mismatch"]
        for channel in g12["channels"]:
            channel["series"] = []
    g12["omissions"] = [*_omissions(issues, {"member_unreadable", "identity_mismatch", "summary_mismatch",
                                              "config_mismatch"}), *trade_omissions]

    # G13: raw curve.csv per listed member; curve files are independent sources.
    g13_series, curve_sources, curve_bytes = [], [], []
    curve_omissions = []
    for name in policies:
        member = members.get(name)
        if member is None:
            curve_omissions.append({"policy": name, "code": "member_unavailable",
                                   "source": f"{rel_dir}/{_policy_folder(name)}/eval_summary.json"})
            continue
        curve = _inside(set_dir / _policy_folder(name) / "curve.csv", root)
        curve_rel = curve.relative_to(root).as_posix()
        try:
            raw = _read_bytes(curve, MAX_CURVE_BYTES)
            text = raw.decode("utf-8-sig")
            reader = csv.DictReader(io.StringIO(text, newline=""))
            if not reader.fieldnames or "episode" not in reader.fieldnames or "return" not in reader.fieldnames:
                raise ValueError("curve.csv requires episode and return columns")
            points = []
            for source_index, row in enumerate(reader):
                if source_index >= MAX_CURVE_ROWS:
                    raise ValueError("curve.csv exceeds row limit")
                episode, ret = float(row["episode"]), float(row["return"])
                if not (math.isfinite(episode) and math.isfinite(ret)):
                    raise ValueError("curve.csv has a non-finite episode or return")
                points.append({"x": episode, "y": ret, "episode": episode, "source_index": source_index})
            if not points:
                raise ValueError("curve.csv has no samples")
            g13_series.append({"id": name, "label": name, "role": "recorded", "points": points})
            curve_sources.append(curve_rel)
            curve_bytes.append(raw)
        except (OSError, UnicodeError, ValueError, KeyError, csv.Error) as exc:
            issues.append({"code": "curve_unavailable", "policy": name, "path": curve_rel,
                           "reason": type(exc).__name__})
            curve_omissions.append({"policy": name, "code": "curve_unavailable", "source": curve_rel,
                                    "reason": type(exc).__name__})
    g13 = _panel("G13", "line", curve_sources or [sources[0]], _digest(*curve_bytes) if curve_bytes else revision,
                 x_label="episode", x_unit="episode", y_label="return", y_unit="return",
                 caveats=["raw_training_curve"] if g13_series else ["curve_unavailable"], series=g13_series)
    if not g13_series:
        g13["state"], g13["reason"] = "unavailable", "No listed policy has a readable raw curve.csv."
    g13["omissions"] = curve_omissions

    provenance = {
        "set": index.get("set", set_dir.name), "generated": index.get("generated"),
        "protocols": all_protocols,
        "training": [{"policy": name, "config_status": member["config_status"], **{key: member["config"].get(key) for key in
                        ("git_head", "git_commit", "output", "protocol", "plant_sha", "derived_sha",
                         "recorded_steps", "scenario", "seed", "git_dirty")}}
                     for name, member in members.items()],
        "score_generation": "recorded eval_summary.json; record_agents scoring plant not recorded",
    }
    return {"relative_path": rel_dir, "panels": [g07, g08, g09, g10, g12, g13], "issues": issues,
            "provenance": provenance, "revision": revision,
            "record_only": all(not member.get("pair_seed") for member in members.values()),
            "recorder_test": set_dir.name.endswith("_TEST")}


def read_agent_sets(root: Path) -> list[dict]:
    """Read each qualifying results/agents set, using index policies as membership."""
    root = Path(root).resolve()
    agents_dir = _inside(root / "results" / "agents", root)
    if not agents_dir.is_dir():
        return []
    records = []
    for set_dir in sorted(agents_dir.iterdir(), key=lambda p: p.name.casefold()):
        try:
            set_dir = _inside(set_dir, root)
        except ValueError:
            continue
        if not set_dir.is_dir():
            continue
        index = set_dir / "index.json"
        if not index.is_file():
            continue
        issues = []
        try:
            records.append(_build_set(root, _inside(set_dir, root), issues))
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            relative = set_dir.relative_to(root).as_posix()
            records.append({"relative_path": relative, "panels": [], "issues": [
                {"code": "set_unreadable", "path": f"{relative}/index.json", "reason": type(exc).__name__}],
                "provenance": {}, "revision": "", "record_only": True,
                "recorder_test": set_dir.name.endswith("_TEST")})
    return records
