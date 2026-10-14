"""Read-only adapters for the published comparison figures G01-G06/G14-G25.

This module reads bounded JSON files under ``results/`` only. It does not
import a producer, evaluate a model, or write files. Every series point keeps
the source sample index so the UI can resolve selections to recorded values.
"""
from __future__ import annotations

import hashlib
import json
import math
from bisect import bisect_right
from pathlib import Path
from typing import Any


_MAX_SOURCE_BYTES = 16 * 1024 * 1024
_FILES = {
    "trace": "results/traces_130kmh.json",
    "cal": "results/calibration_comparison.json",
    "gen": "results/generality.json",
    "sweep": "results/sweep_speed_grade.json",
    "roads": "results/training_roads.json",
    "model": "results/model_vs_data.json",
}
_CAVEATS = {
    "historical": "HISTORICAL_PUBLISHED_RECORD",
    "altitude": "SEA_LEVEL_AIR_NO_ALTITUDE_MODEL",
    "single_scenario": "HAND_WRITTEN_SINGLE_SCENARIO_CANNOT_SETTLE_PREVIEW",
    "thermal_damage": "THERMAL_ONLY_DAMAGE_NOT_RECORDED",
    "assumed_turbine": "TURBINE_CAPACITY_ASSUMED_TAU_CONDITION_DEPENDENT",
    "htau": "H_TAU_METHOD_NOT_QUOTABLE_UNTIL_THERMAL_SUBSTEP",
    "roads": "SAMPLED_ROADS_NOT_EXACT_TRAINING_HISTORY",
    "enrichment": "TIMESTAMP_DWELL_SOURCE_RETIRED_ROW_COUNT_AXIS_NOT_USED",
    "thermal_fit": "DRIVE10_IS_IN_THERMAL_FIT_FITTED_DRIVE_TRACE",
    "knock": "WEAK_KNOCK_SAMPLING_CANNOT_ESTABLISH_AGREEMENT",
    "gear": "GEAR_CHANNEL_SATURATES_AT_RECORDED_MAXIMUM",
    "envelope": "OPERATING_ENVELOPE_IS_NOT_A_COMPRESSOR_MAP",
    "status": "STATUS_QUOTED_AS_RECORDED_NOT_A_CURRENT_VALIDATION_VERDICT",
    "validation": "PUBLISHED_VALIDATION_RECORD_HAS_DOCUMENTED_LIMITATIONS",
    "trace_threshold": "TURBINE_THRESHOLD_NOT_RECORDED_IN_TRACE_SOURCE",
    "trace_components": "BLOCK_AND_COOLANT_TRACE_CHANNELS_NOT_RECORDED",
    "validation_date": "VALIDATION_TABLE_LAST_REGENERATED_2026_09_30",
    "validation_no_plan": "VALIDATION_PLAN_DRAFT_NOT_ON_BRANCH_DECISIONS_PENDING_2026_10_07",
    "validation_no_claim": "NO_CURRENT_VALIDATION_OR_AGREEMENT_CLAIM",
}


class _SourceError(Exception):
    pass


def _finite(value: Any) -> float | None:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return number if math.isfinite(number) else None


def _point(x: Any, y: Any, index: int | None, **extra: Any) -> dict[str, Any]:
    result: dict[str, Any] = {"x": _finite(x), "y": _finite(y), "source_index": index}
    for key, value in extra.items():
        if key in ("low", "high", "value"):
            result[key] = _finite(value)
        elif value is not None:
            result[key] = value
    return result


def _series(series_id: str, label: str, points: list[dict[str, Any]], role: str = "recorded") -> dict[str, Any]:
    return {"id": series_id, "label": label, "role": role, "points": points}


def _base(panel_id: str, group: str, kind: str, sources: list[str],
          x: tuple[str, str], y: tuple[str, str], caveats: list[str] | None = None) -> dict[str, Any]:
    return {
        "id": panel_id, "group": group, "kind": kind, "state": "available",
        "source_files": sources, "caveats": list(caveats or []), "reason": None,
        "axes": {"x": {"label": x[0], "unit": x[1]}, "y": {"label": y[0], "unit": y[1]}},
        "series": [], "revision": "",
    }


def _read(root: Path, rel: str, cache: dict[str, tuple[Any, str]]) -> Any:
    if rel in cache:
        return cache[rel][0]
    path = (root / rel).resolve()
    root_resolved = root.resolve()
    if not path.is_relative_to(root_resolved):
        raise _SourceError("source path escaped repository root")
    try:
        before = path.stat()
        if before.st_size > _MAX_SOURCE_BYTES:
            raise _SourceError("source exceeds bounded JSON read size")
        raw = path.read_bytes()
        after = path.stat()
    except OSError as exc:
        raise _SourceError(type(exc).__name__) from exc
    if (before.st_size, before.st_mtime_ns) != (after.st_size, after.st_mtime_ns) or len(raw) != after.st_size:
        raise _SourceError("source changed while being read")
    try:
        value = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise _SourceError(type(exc).__name__) from exc
    cache[rel] = (value, hashlib.sha256(raw).hexdigest())
    return value


def _revision(sources: list[str], cache: dict[str, tuple[Any, str]]) -> str:
    digest = hashlib.sha256()
    for rel in sorted(sources):
        digest.update(rel.encode("utf-8"))
        digest.update(cache[rel][1].encode("ascii"))
    return digest.hexdigest()


def _table(columns: list[str], rows: list[list[Any]]) -> dict[str, Any]:
    return {"columns": columns, "rows": rows}


def _unavailable(panel_id: str, group: str, kind: str, sources: list[str], reason: str) -> dict[str, Any]:
    panel = _base(panel_id, group, kind, sources, ("", ""), ("", ""))
    panel.update(state="unavailable", reason=reason)
    return panel


def read_reference_panels(root: Path) -> list[dict[str, Any]]:
    """Return the 18 requested reference panels from published JSON records."""
    root = Path(root)
    cache: dict[str, tuple[Any, str]] = {}

    def build(panel_id: str, group: str, kind: str, rels: list[str], axes: tuple[tuple[str, str], tuple[str, str]], fn,
              caveats: list[str] | None = None) -> dict[str, Any]:
        panel = _base(panel_id, group, kind, rels, axes[0], axes[1], caveats)
        try:
            data = {name: _read(root, rel, cache) for name, rel in zip(("a", "b"), rels)}
            fn(panel, data)
            panel["revision"] = _revision(rels, cache)
            return panel
        except Exception as exc:
            return _unavailable(panel_id, group, kind, rels, f"published source unavailable or malformed: {type(exc).__name__}: {exc}")

    panels: list[dict[str, Any]] = []
    trace_rel = _FILES["trace"]
    policies = [("baseline ECU", "Baseline ECU"), ("reactive", "Reactive"),
                ("current-grade", "current-grade"), ("predictive (hand)", "Predictive (hand-written)")]

    def trace_panel(pid: str, field: str, y: tuple[str, str], title: str, caveats: list[str]):
        def fill(p, d):
            tr = d["a"]
            for key, label in policies:
                obj = tr[key]
                values = obj[field]
                p["series"].append(_series(key.replace(" ", "_"), label,
                    [_point(obj["t"][i], values[i], i) for i in range(min(len(obj["t"]), len(values)))]))
            p["table"] = _table(["policy", "recorded peak or endpoint"], [
                [label, _finite(tr[key].get("summary", {}).get("damage") if field == "dmg_cum" else max((_finite(v) for v in tr[key].get(field, []) if _finite(v) is not None), default=None))]
                for key, label in policies])
            p["caption"] = title
            if pid == "G01":
                baseline = tr[policies[0][0]]
                positive = [i for i, value in enumerate(baseline["grade"]) if _finite(value) is not None and float(value) > 0]
                if positive:
                    p["intervals"] = [{"axis": "x", "start": _finite(baseline["t"][positive[0]]),
                                       "end": _finite(baseline["t"][positive[-1]]),
                                       "label": "Recorded climb (grade > 0)",
                                       "source": "results/traces_130kmh.json:baseline ECU.grade; first through last sample with grade > 0"}]
        return build(pid, "overview", "line", [trace_rel], (("Time", "s"), y), fill, caveats)

    panels.append(trace_panel("G01", "t_turb", ("Turbine housing temperature", "°C"),
                              "Historical hand-written policy traces; modelled turbine temperature.",
                              [_CAVEATS["historical"], _CAVEATS["altitude"], _CAVEATS["single_scenario"], _CAVEATS["assumed_turbine"],
                               _CAVEATS["trace_threshold"], _CAVEATS["trace_components"]]))
    panels.append(trace_panel("G02", "dmg_cum", ("Accumulated damage", "recorded damage units"),
                              "Recorded cumulative damage for the same historical episode.",
                              [_CAVEATS["historical"], _CAVEATS["single_scenario"], _CAVEATS["thermal_damage"]]))

    cal_rel = _FILES["cal"]
    def g03(p, d):
        rows = d["a"]["premise_steps"]
        for key, label in (("baseline", "Baseline"), ("reactive", "Reactive"),
                            ("current_grade", "current-grade"), ("predictive", "Predictive (hand-written)")):
            p["series"].append(_series(key, label, [_point(i, row[key], i) for i, row in enumerate(rows)]))
        p["table"] = _table(["step", "baseline", "reactive", "current-grade", "predictive"],
                            [[r["step"], *[_finite(r[k]) for k in ("baseline", "reactive", "current_grade", "predictive")]] for r in rows])
        p["caption"] = "One recorded premise step at a time; the thermal-only split was not recorded per step."
    panels.append(build("G03", "overview", "line", [cal_rel], (("Recorded premise step", "index"), ("Damage", "recorded damage units")), g03,
                        [_CAVEATS["historical"], _CAVEATS["single_scenario"], _CAVEATS["thermal_damage"]]))

    gen_rel = _FILES["gen"]
    def g04(p, d):
        g = d["a"]
        for table_key, label in (("h2", "H2 comparator set"), ("h2b", "H2b comparator set")):
            rows = g[table_key]
            for comparator, series_label in (("grade", "Predictive minus current-grade"), ("reactive", "Predictive minus reactive")):
                points = []
                for i, row in enumerate(rows):
                    predictive = _finite(row.get("predictive"))
                    reference = _finite(row.get(comparator))
                    delta = predictive - reference if predictive is not None and reference is not None else None
                    points.append(_point(row.get("h_tau"), delta, i))
                p["series"].append(_series(f"{table_key}_preview_minus_{comparator}", f"{label}: {series_label}", points))
        p["table"] = _table(["set", "source index", "h/tau", "binds", "predictive", "grade", "reactive"], [
            [name, i, _finite(r.get("h_tau")), r.get("binds"), _finite(r.get("predictive")), _finite(r.get("grade")), _finite(r.get("reactive"))]
            for name in ("h2", "h2b") for i, r in enumerate(g[name])])
        p["caption"] = "Per-row predictive-minus-comparator values use the published make_page.generality() transformation; the table retains absolute scores and binding flags."
    panels.append(build("G04", "overview", "scatter", [gen_rel], (("H / τ", "ratio as recorded"), ("Predictive minus comparator", "recorded score units")), g04,
                        [_CAVEATS["historical"], _CAVEATS["htau"], _CAVEATS["single_scenario"]]))

    sweep_rel = _FILES["sweep"]
    def g05(p, d):
        rows = d["a"]
        speeds = sorted({r["v_kmh"] for r in rows})
        for speed in speeds:
            cells = [(i, r) for i, r in enumerate(rows) if r["v_kmh"] == speed]
            p["series"].append(_series(f"speed_{speed}", f"{speed} km/h", [_point(r["grade"], speed, i, value=r["peak_c"]) for i, r in cells]))
        p["channels"] = [{"id": "peak", "label": "Recorded peak temperature", "unit": "°C", "axes": p["axes"], "series": p["series"]}]
        p["table"] = _table(["source index", "speed km/h", "grade", "peak °C", "fraction above", "binds"],
                            [[i, r["v_kmh"], r["grade"], _finite(r["peak_c"]), _finite(r["frac_above"]), r["binds"]] for i, r in enumerate(rows)])
        p["kind"] = "heatmap"
        p["caption"] = "Only tested speed and grade cells are represented; no values are interpolated."
    panels.append(build("G05", "overview", "heatmap", [sweep_rel], (("Grade", "% as recorded"), ("Speed", "km/h")), g05,
                        [_CAVEATS["historical"], _CAVEATS["altitude"]]))

    roads_rel = _FILES["roads"]
    def g06(p, d):
        roads = d["a"]["roads"]
        chosen: dict[str, tuple[int, dict[str, Any]]] = {}
        for i, road in enumerate(roads):
            chosen.setdefault(road["family"], (i, road))
        for family, (road_index, road) in chosen.items():
            p["series"].append(_series(f"{family}_grade", f"{family}: grade", [_point(i * 5, v, i) for i, v in enumerate(road["grade"])], "grade"))
        elev_series = [_series(f"{family}_elevation", f"{family}: elevation", [_point(i * 5, v, i) for i, v in enumerate(road["elev_m"])], "elevation")
                       for family, (_, road) in chosen.items()]
        p["channels"] = [{"id": "grade", "label": "Road grade", "unit": "fraction", "axes": p["axes"], "series": p["series"]},
                          {"id": "elevation", "label": "Road elevation", "unit": "m", "axes": {"x": {"label": "Road sample time", "unit": "s"}, "y": {"label": "Elevation", "unit": "m"}}, "series": elev_series}]
        p["table"] = _table(["road source index", "seed", "family", "thermal peak °C", "grade min", "grade max"],
                            [[i, r.get("seed"), r.get("family"), _finite(r.get("peak_c")), _finite(r.get("grade_min")), _finite(r.get("grade_max"))] for i, r in enumerate(roads)])
        p["caption"] = "First recorded sample per road family, plus the thermal peaks of every sampled road; 5 s spacing is the published reader contract."
    panels.append(build("G06", "overview", "line", [roads_rel], (("Road sample time", "s"), ("Grade", "fraction")), g06,
                        [_CAVEATS["historical"], _CAVEATS["roads"], _CAVEATS["altitude"]]))

    model_rel = _FILES["model"]
    def g14(p, d):
        rows = d["a"]["load"]["points"]
        p["series"] = [_series("measured_modelled", "Recorded load points", [_point(r["meas"], r["model"], i) for i, r in enumerate(rows)])]
        p["table"] = _table(["source index", "RPM", "MAP kPa", "measured load", "modelled load"], [[i, _finite(r.get("rpm")), _finite(r.get("map_kpa")), _finite(r.get("meas")), _finite(r.get("model"))] for i, r in enumerate(rows)])
        p["references"] = [{"axis": "identity", "label": "identity", "source": "display reference y=x"}]
        p["caption"] = "Modelled versus measured load on the published 26-point selection; the identity line is a display reference."
    panels.append(build("G14", "comparison", "scatter", [model_rel], (("Measured load", "fraction"), ("Modelled load", "fraction")), g14,
                        [_CAVEATS["historical"], "LOAD_COMPARISON_LIMITED_TO_PUBLISHED_30_75_KPA_POINTS"]))

    def g15(p, d):
        boost = d["a"]["boost"]
        for key, label in (("logged", "Logged MAP"), ("model", "Modelled MAP"), ("raw_sensor", "Raw pre-throttle sensor")):
            vals = boost[key]
            ordered = sorted(((float(v), i) for i, v in enumerate(vals) if _finite(v) is not None), key=lambda pair: pair[0])
            n = len(ordered)
            p["series"].append(_series(key, label, [_point(v, (rank + 1) / n, index) for rank, (v, index) in enumerate(ordered)]))
        p["caption"] = "Empirical distributions of the recorded samples; raw sensor and modelled/ logged pressure remain separate sources."
    panels.append(build("G15", "comparison", "line", [model_rel], (("Manifold pressure", "kPa absolute"), ("Empirical fraction", "fraction")), g15,
                        [_CAVEATS["historical"], "BOOST_SOURCE_POPULATIONS_DIFFER; RAW_SENSOR_IS_PRE_THROTTLE"]))

    def g16(p, d):
        rows = d["a"]["enrichment"]["cells"]
        p["channels"] = []
        rpm_labels = list(dict.fromkeys(r.get("rpm") for r in rows))
        dwell_labels = list(dict.fromkeys(r.get("dwell") for r in rows))
        rpm_index = {label: i for i, label in enumerate(rpm_labels)}
        dwell_index = {label: i for i, label in enumerate(dwell_labels)}
        axes = {"x": {"label": "RPM category", "unit": "recorded category index",
                      "ticks": [{"value": i, "label": label} for i, label in enumerate(rpm_labels)]},
                "y": {"label": "Timestamp dwell category", "unit": "recorded category index",
                      "ticks": [{"value": i, "label": label} for i, label in enumerate(dwell_labels)]}}
        p["axes"] = axes
        for key, label, value_field in (("logged", "Logged mixture", "meas"), ("simulated", "Simulated mixture", "model")):
            points = [_point(rpm_index[r.get("rpm")], dwell_index[r.get("dwell")], i, value=r.get(value_field)) for i, r in enumerate(rows)]
            p["channels"].append({"id": key, "label": label, "unit": "lambda ratio", "kind": "heatmap", "axes": axes,
                                  "series": [_series(key, label, points)]})
        p["table"] = _table(["source index", "RPM category", "timestamp dwell category", "count", "logged lambda", "simulated lambda"],
                            [[i, r.get("rpm"), r.get("dwell"), r.get("n"), _finite(r.get("meas")), _finite(r.get("model"))] for i, r in enumerate(rows)])
        p["caption"] = "Recorded RPM and timestamp-dwell categories are heatmap coordinates; tick labels preserve the source categories and the table retains counts."
        p["kind"] = "heatmap"
    panels.append(build("G16", "comparison", "heatmap", [model_rel], (("RPM category", "recorded category index"), ("Timestamp dwell category", "recorded category index")), g16,
                        [_CAVEATS["historical"], _CAVEATS["enrichment"]]))

    def g17(p, d):
        spark = d["a"]["spark"]
        rows = spark["points"]
        p["channels"] = []
        for key, label in (("before", "Before calibration"), ("after", "After calibration")):
            p["series"].append(_series(key, label, [_point(r.get("meas"), r.get(key), i) for i, r in enumerate(rows)]))
        residual_points = {key: [] for key in ("before", "after")}
        table_rows = []
        for i, row in enumerate(rows):
            measured = _finite(row.get("meas"))
            residuals = {}
            for key in ("before", "after"):
                modelled = _finite(row.get(key))
                residuals[key] = modelled - measured if modelled is not None and measured is not None else None
                residual_points[key].append(_point(row.get("rpm"), residuals[key], i))
            table_rows.append([i, *[_finite(row.get(k)) for k in ("rpm", "map_kpa", "meas", "before", "after")], residuals["before"], residuals["after"]])
        p["channels"].append({"id": "residual", "label": "Spark residuals (model minus measured)", "unit": "degrees", "kind": "scatter",
                              "axes": {"x": {"label": "Engine speed", "unit": "rpm"}, "y": {"label": "Model minus measured spark", "unit": "degrees"}},
                              "series": [_series(key, f"{key.title()} calibration residual", residual_points[key]) for key in ("before", "after")]})
        p["table"] = _table(["source index", "RPM", "MAP kPa", "measured advance", "before", "after", "before residual", "after residual"], table_rows)
        p["published_metrics"] = {key: {name: _finite(value) for name, value in spark[key].items() if name in ("mean", "mae", "rmse", "line_sets")} for key in ("before", "after")}
        p["caption"] = "The residual channel shows model minus measured at each recorded point; summary metrics are quoted from the published reader source."
    panels.append(build("G17", "comparison", "scatter", [model_rel], (("Measured spark", "degrees as recorded"), ("Modelled spark", "degrees as recorded")), g17,
                        [_CAVEATS["historical"], "SPARK_CALIBRATION_STATE_BEFORE_AND_AFTER_RECORDED"]))

    def g18(p, d):
        cal = d["a"]["thermal"]["traces"]["drive10-20260918_233912.csv"]
        p["channels"] = []
        for field, caption in (("oil", "Oil"), ("coolant", "Coolant")):
            p["channels"].append({"id": field, "label": caption, "unit": "°C", "axes": {"x": {"label": "Time", "unit": "min"}, "y": {"label": f"{caption} temperature", "unit": "°C"}},
                "series": [_series(f"{field}_{source}", label, [_point(cal["t_min"][i], cal[f"{source}_{field}" if source != "logged" else f"car_{field}"][i], i) for i in range(len(cal["t_min"]))])
                           for source, label in (("logged", "Logged"), ("before", "Original model"), ("after", "Calibrated model"))]})
        p["caption"] = "Drive10 fit trace; each series uses its recorded time samples."
    panels.append(build("G18", "comparison", "line", [cal_rel], (("Time", "min"), ("Temperature", "°C")), g18,
                        [_CAVEATS["historical"], _CAVEATS["thermal_fit"]]))

    def g19(p, d):
        rows = d["a"]["thermal"]["per_drive"]
        for field, label in (("oil", "Oil RMSE"), ("coolant", "Coolant RMSE")):
            for key, source in (("shipped", "Original parameters"), ("fitted", "Fitted drive"), ("held_out", "Held-out drive")):
                p["series"].append(_series(f"{field}_{key}", f"{label}: {source}", [_point(i, row[key][field], i) for i, row in enumerate(rows)]))
        p["table"] = _table(["drive", "original oil", "fitted oil", "held-out oil", "original coolant", "fitted coolant", "held-out coolant"],
                            [[r["drive"], *[_finite(r[k][chan]) for chan in ("oil", "coolant") for k in ("shipped", "fitted", "held_out")]] for r in rows])
        p["caption"] = "Per-drive errors remain separate; the published source supplies these per-drive values."
    panels.append(build("G19", "comparison", "bar", [cal_rel], (("Drive source index", "index"), ("RMSE", "°C")), g19,
                        [_CAVEATS["historical"], "PER_DRIVE_RMSE_FIT_AND_HELD_OUT_COLUMNS_AS_RECORDED"]))

    def g20(p, d):
        cal = d["a"]["thermal"]
        structures = d["a"]["oil_structures"]
        traces = cal["traces"]["7475b5d7-20260908_142743.csv"]
        p["channels"] = [{"id": "hard_pull_oil", "label": "Hard-pull oil trace", "unit": "°C", "axes": {"x": {"label": "Time", "unit": "min"}, "y": {"label": "Oil temperature", "unit": "°C"}},
            "series": [_series(key, label, [_point(traces["t_min"][i], traces[field][i], i) for i in range(len(traces["t_min"]))]) for key, label, field in (("car", "Logged", "car_oil"), ("before", "Original model", "before_oil"), ("after", "Calibrated model", "after_oil"))]},
            {"id": "oil_structure", "label": "Structure comparison", "unit": "RMSE °C", "axes": {"x": {"label": "Structure source index", "unit": "index"}, "y": {"label": "Drive10 oil RMSE", "unit": "°C"}},
             "series": [_series("structures", "Published structures", [_point(i, r.get("drive10_rmse"), i) for i, r in enumerate(structures)])]}]
        p["table"] = _table(["structure", "RMSE °C", "recorded note"], [[r.get("structure"), _finite(r.get("drive10_rmse")), r.get("note")] for r in structures])
        p["caption"] = "The hard-pull trace and structure comparison are separate published records from one calibration generation."
    panels.append(build("G20", "comparison", "line", [cal_rel], (("Time", "min"), ("Temperature", "°C")), g20,
                        [_CAVEATS["historical"], "HARD_PULL_TRACE_AND_STRUCTURE_FIT_HAVE_DISTINCT_AXES"]))

    def g21(p, d):
        k = d["a"]["knock"]
        paired = min(len(k["ki"]), len(k["retard"]))
        p["series"] = [_series("knock_indicator_retard", "Recorded knock indicator and retard", [_point(k["ki"][i], k["retard"][i], i) for i in range(paired)])]
        # Exact display bins from make_page.model_vs_car(); these are a
        # published reader projection, not a newly selected binning scheme.
        ki_edges = [i * 0.04 for i in range(41)]
        retard_edges = [-2.0 + i * 0.5 for i in range(45)]
        counts: dict[tuple[int, int], list[int]] = {}
        for i in range(paired):
            ki_value, retard_value = _finite(k["ki"][i]), _finite(k["retard"][i])
            if ki_value is None or retard_value is None or not (ki_edges[0] <= ki_value <= ki_edges[-1]) or not (retard_edges[0] <= retard_value <= retard_edges[-1]):
                continue
            ki_bin = min(len(ki_edges) - 2, bisect_right(ki_edges, ki_value) - 1)
            retard_bin = min(len(retard_edges) - 2, bisect_right(retard_edges, retard_value) - 1)
            counts.setdefault((ki_bin, retard_bin), []).append(i)
        density_points = [_point(ki_edges[ki_bin], retard_edges[retard_bin], None,
                                 value=len(indices), source_indices=indices)
                          for (ki_bin, retard_bin), indices in sorted(counts.items())]
        density_axes = {"x": {"label": "Knock indicator bin lower edge", "unit": "ratio"},
                        "y": {"label": "Retard bin lower edge", "unit": "degrees"}}
        included = sum(len(indices) for indices in counts.values())
        coverage = {"total": paired, "included": included, "excluded": paired - included,
                    "ki_range": [ki_edges[0], ki_edges[-1]], "retard_range": [retard_edges[0], retard_edges[-1]]}
        p["channels"] = [{"id": "density", "label": "Published knock/retard sample density", "unit": "samples per bin", "kind": "heatmap", "coverage": coverage,
                          "axes": density_axes, "series": [_series("density", "Paired samples", density_points)]},
                         {"id": "raw", "label": "Recorded knock indicator and retard", "unit": "degrees", "kind": "scatter",
                          "axes": p["axes"], "series": p["series"]}]
        ks = d["a"]["knock_sampling"]
        p["table"] = _table(["sampling field", "recorded value"], [[key, _finite(value)] for key, value in ks.items()])
        p["caption"] = "Paired values are sparse in time; density cells reuse make_page.model_vs_car()'s published 0.04 KI and 0.5° retard bins."
    panels.append(build("G21", "comparison", "scatter", [model_rel], (("Knock indicator", "ratio"), ("Recorded retard", "degrees")), g21,
                        [_CAVEATS["historical"], _CAVEATS["knock"]]))

    def g22(p, d):
        g = d["a"]["gearbox"]
        p["series"] = [_series("observed_histogram", "Observed overall-ratio histogram", [_point((g["edges"][i] + g["edges"][i + 1]) / 2.0, count, i) for i, count in enumerate(g["hist"])])]
        p["axes"] = {"x": {"label": "Observed overall ratio", "unit": "ratio"}, "y": {"label": "Count", "unit": "samples"}}
        p["references"] = [{"axis": "x", "value": _finite(value), "label": f"Gear {i + 1} published overall ratio",
                             "source": f"results/model_vs_data.json:gearbox.published[{i}]"}
                            for i, value in enumerate(g["published"])]
        p["channels"] = [{"id": "observed", "label": "Observed overall-ratio histogram", "unit": "samples", "axes": p["axes"], "series": p["series"], "references": p["references"]},
                          {"id": "references", "label": "Published gear-ratio references", "unit": "overall ratio", "axes": {"x": {"label": "Gear number", "unit": "gear"}, "y": {"label": "Overall ratio", "unit": "ratio"}},
                           "series": [_series("published_overall", "Published overall ratio", [_point(i + 1, value, i) for i, value in enumerate(g["published"])]),
                                      _series("published_gear", "Published gearbox ratio", [_point(i + 1, value, i) for i, value in enumerate(g["gears"])])] }]
        p["table"] = _table(["bin index", "ratio lower edge", "ratio upper edge", "observed count"],
            [[i, _finite(g["edges"][i]), _finite(g["edges"][i + 1]), g["hist"][i]] for i in range(len(g["hist"]))])
        p["caption"] = "Observed histogram values use source-bin midpoints for display; the table retains exact bounds and reference lines use source ratios on the same axis."
    panels.append(build("G22", "comparison", "bar", [model_rel], (("Observed overall ratio", "ratio"), ("Count", "samples")), g22,
                        [_CAVEATS["historical"], _CAVEATS["gear"]]))

    def g23(p, d):
        model = d["a"]["envelope"]
        cal = _read(root, cal_rel, cache)["boost"]
        p["source_files"] = [model_rel, cal_rel]
        p["channels"] = [{"id": "operating_envelope", "label": "Logged operating envelope", "unit": "pressure ratio", "axes": {"x": {"label": "Corrected airflow", "unit": "kg/s"}, "y": {"label": "Pressure ratio", "unit": "ratio"}},
            "series": [_series("logged", "Logged operating points", [_point(model["flow"][i], model["pr"][i], i) for i in range(min(len(model["flow"]), len(model["pr"])))])]},
            {"id": "low_rpm_boost", "label": "Low-RPM boost comparison", "unit": "kPa absolute", "axes": {"x": {"label": "Engine speed", "unit": "rpm"}, "y": {"label": "Manifold pressure", "unit": "kPa absolute"}},
             "series": [_series("car_wot", "Logged full-throttle points", [_point(cal["car_wot"]["rpm"][i], cal["car_wot"]["map_kpa"][i], i) for i in range(min(len(cal["car_wot"]["rpm"]), len(cal["car_wot"]["map_kpa"])))])]+[
                 _series(name, label, [_point(row["rpm"], row["map_kpa"], i) for i, row in enumerate(cal[name])]) for name, label in (("model_before", "Original model"), ("model_after", "Calibrated model"))]}]
        p["series"] = p["channels"][0]["series"]
        p["table"] = _table(["flow kg/s", "pressure ratio", "source index"], [[_finite(model["flow"][i]), _finite(model["pr"][i]), i] for i in range(min(len(model["flow"]), len(model["pr"])))])
        p["caption"] = "Operating points and the derived ceiling curve are separate from low-RPM logged/modelled boost; this is not a compressor map."
        p["channels"][0]["series"].append(_series("published_ceiling", "Published plant ceiling curve", [_point(model["curve_flow"][i], model["curve_pr"][i], i) for i in range(min(len(model["curve_flow"]), len(model["curve_pr"])))], "modelled"))
    panels.append(build("G23", "comparison", "scatter", [model_rel, cal_rel], (("Corrected airflow", "kg/s"), ("Pressure ratio", "ratio")), g23,
                        [_CAVEATS["historical"], _CAVEATS["envelope"], "LOW_RPM_BOOST_COMPARISON_HAS_ITS_OWN_AXES"]))

    def g24(p, d):
        duty = d["a"]["duty"]
        rows = []
        for ri, row in enumerate(duty["H"]):
            for ci, value in enumerate(row):
                if _finite(value) is not None and float(value) > 0:
                    rows.append([ri, ci, _finite(duty["rpm_edges"][ri]), _finite(duty["rpm_edges"][ri + 1]),
                                 _finite(duty["map_edges"][ci]), _finite(duty["map_edges"][ci + 1]), _finite(value)])
        p["kind"] = "heatmap"
        p["series"] = [_series("logged_coverage", "Logged operating-region counts", [_point(r[2], r[4], None, value=r[6], cell_index=[r[0], r[1]]) for r in rows]),
                        _series("scenario_point", "Simulated scenario", [_point(duty["scenario_rpm"], duty["scenario_map"], 0)], "scenario")]
        p["channels"] = [{"id": "coverage", "label": "Logged operating-region counts with scenario marker", "unit": "samples", "kind": "heatmap", "axes": p["axes"], "series": p["series"]}]
        p["table"] = _table(["RPM bin index", "MAP bin index", "RPM lower", "RPM upper", "MAP lower kPa", "MAP upper kPa", "recorded count"], rows)
        p["caption"] = "Logged coverage is recorded as counts; the scenario point comes from the published simulation record."
    panels.append(build("G24", "comparison", "heatmap", [model_rel], (("RPM bin lower edge", "rpm"), ("MAP bin lower edge", "kPa absolute")), g24,
                        [_CAVEATS["historical"], "SCENARIO_POINT_IS_SIMULATED_AND_SEPARATELY_LABELLED"]))

    def g25(p, d):
        rows = d["a"]["literature"]
        def limitation(name: str) -> str:
            if "Knock-limited spark" in name:
                return "ROW4_SOURCE_UNSPECIFIED_KNOCK_MODEL_NOT_VALIDATED"
            if "EGT, cruise band (max)" in name:
                return "ROW6_TEST_POINT_ABOVE_RECORDED_CRUISE_PRESSURE_RANGE_BAND_NOT_MOVED"
            if "Turbine housing time constant" in name:
                return "TAU_RECOMPUTES_C_OVER_UA_NOT_AN_INDEPENDENT_MEASUREMENT_CAPACITY_ASSUMED"
            if "Oil, sustained load" in name:
                return "ROW8_DRIVE10_IN_THERMAL_FIT_IN_SAMPLE"
            if "Oil apparent time constant" in name:
                return "ROW9_IDENTIFIED_ON_FOUR_OF_FIVE_EXCITED_DRIVES"
            if "Coolant, regulated" in name:
                return "ROW10_SYNTHETIC_CLIMB_SCORED_AGAINST_CAR_WARM_RANGE"
            if "Coolant, whole drive" in name:
                return "ROW11_DRIVE10_IN_SAMPLE_LEAVE_ONE_DRIVE_OUT_VALUE_ALSO_RECORDED"
            return "SOURCE_STATUS_ONLY_NO_ADDITIONAL_ROW_LIMITATION"
        p["kind"] = "table"
        p["context_sources"] = ["validation_table.md", "VALIDATION_PLAN_REVIEW.md"]
        p["table"] = _table(["quantity", "value", "unit", "band low", "band high", "basis", "status recorded in source", "documented limitation"],
            [[r.get("name"), _finite(r.get("value")), r.get("unit"), _finite(r.get("lo")), _finite(r.get("hi")), r.get("basis"),
              "inside (as recorded)" if r.get("ok") is True else "outside (as recorded)" if r.get("ok") is False else "not recorded",
              limitation(str(r.get("name", "")))] for r in rows])
        p["caption"] = "Rows quote the 30 September validation record and its source statuses. VALIDATION_PLAN_REVIEW.md describes a draft whose decisions remain pending; this table assigns no validation verdict."
    panels.append(build("G25", "comparison", "table", [model_rel], (("Validation row", "source row"), ("Value", "source unit")), g25,
                        [_CAVEATS["historical"], _CAVEATS["validation"], _CAVEATS["status"], _CAVEATS["validation_date"],
                         _CAVEATS["validation_no_plan"], _CAVEATS["validation_no_claim"]]))

    return panels
