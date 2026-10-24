"""test_epa_fixtures.py -- the synthetic tables, contracts, repositories, rows, models and traces
every test of build step 2 runs on, and a guard that fails a test which opens real EPA data.

    python test_epa_fixtures.py     about half a minute; its own self-test, exit code 0 when all pass

Build step 2 of decision 24, WP3 (23 October 2026; docs/build_step_2/WP3_INTERFACES.md section
9.1). Nothing in WP3 runs on EPA data: every test of a fit, a statistic, the validation or the D3
reader runs on what this file makes (the task of WP3; amendment C5: the reader's and the
validation's tests run in temporary git repositories with synthetic tables and a synthetic
contract). The one exception, test_epa_rows.Structural, opens the real tables itself.

WHAT IS HERE
  make_repo(tmp, specs)     a temporary git repository: the code a step-2 subprocess imports,
                            copied byte for byte from this working tree (CODE_FILES); synthetic
                            tables for all three engines under its data/engines/ (`* -text`, as
                            the real folder); a synthetic contract whose held-out structure is the
                            generator's own split.compute() run in that repository (split_of), so
                            the populations and the split are the generator's (mistake 10); every
                            commit with fixed names and dates, so its shas are reproducible
  SyntheticEngine, DEFAULT_SPECS   what a synthetic engine's tables hold, row by row
  rewrite_contract, rehash_tables, commit_all, copy_repo   the edits the corruption tests make
  point_row, held_out_row, initial_row   in-memory rows (origin "fixture")
  ToyModel                  closed-form torque, fuel, air, TIT and ECU laws (epa_stats' model
                            protocol, section 5.2.2), for hand answers
  truth_candidate, b58_values, rows_from_plant   a known truth from the B58's typed values, and
                            rows whose outputs are its run_cycle's at synthetic inputs
  synthetic_columns, write_trace, synthetic_trace, write_summary_xlsx   D3-dialect traces and a
                            summary workbook, for test_d3_rows.py
  commit_armed, add_worktree, synthetic_tightenings   the validation guards' records
  forbid_real_data()        an audit hook that fails a test on an open of the real
                            data/engines/*/epa_*, logs/**, the real contract, the generator's
                            split.json or the team's data folder (every test class but
                            test_epa_rows.Structural and CarriedPins, test_contract_pinned and
                            test_calibrate_epa.Gate's one probe of this tree runs inside it;
                            Guarded does that)
  pinned_terms(), pin_contract_commit(repo)   the synthetic pins a Run 1 or an arming gets past, and
                            a repository whose own epa_rows pins its contract (its command line)

WHAT IT NEVER DOES: it reads no real EPA table, no real contract and no D3 file (its own guard
is on while its self-test runs); the synthetic contract's B58 blocks (CONTRACT_BLOCKS) are
stand-ins, not the contract's values. Its numbers are synthetic and are no figure of the project.
"""
import ast
import contextlib
import csv
import glob
import hashlib
import io
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from dataclasses import dataclass, field
from typing import Callable, Mapping, Optional

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epa_rows  # noqa: E402
from thresholds import common, split  # noqa: E402

# ---------------------------------------------------------------------------- the code a repo needs
STEP2_MODULES = ("epa_rows.py", "epa_stats.py", "epa_fit.py", "epa_freeze.py", "calibrate_epa.py", "k3_knee.py",
                 "epa_coefficients.py", "validate_epa.py", "d3_rows.py")


def _plant_code():
    """fingerprint.PLANT_CODE, read from fingerprint.py's literal (no import of the plant)."""
    with open(os.path.join(HERE, "fingerprint.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "PLANT_CODE" for t in node.targets):
            return tuple(ast.literal_eval(node.value))
    raise RuntimeError("fingerprint.py defines no PLANT_CODE")


def _project_imports(rel):
    """The repository's top-level modules a file imports (an AST scan, never an import)."""
    try:
        with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError, UnicodeDecodeError):
        return set()
    out = set()
    for node in ast.walk(tree):
        names = []
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names = [node.module]
        for n in names:
            top = n.split(".")[0]
            if os.path.isfile(os.path.join(HERE, top + ".py")):
                out.add(top + ".py")
    return out


def _code_files():
    """CODE_FILES: PLANT_CODE, fingerprint.py, evaluate.py, check_premise.py, engine_specs/**,
    data/derived_params.json (the B58's derived file), requirements-lock.txt, thresholds/**, engine_thresholds.py and
    the nine step-2 modules that exist, with every top-level module they import, closed over
    (WP3_INTERFACES section 9.1). Never data/engines/** or logs/**."""
    seed = set(_plant_code()) | {"fingerprint.py", "evaluate.py", "check_premise.py", "engine_thresholds.py"}
    seed |= {m for m in STEP2_MODULES if os.path.isfile(os.path.join(HERE, m))}
    todo, py = sorted(seed), set()
    while todo:
        rel = todo.pop()
        if rel in py or not os.path.isfile(os.path.join(HERE, rel)):
            continue
        py.add(rel)
        todo += sorted(_project_imports(rel) - py)
    other = [os.path.relpath(p, HERE).replace(os.sep, "/") for pat in (
        "engine_specs/*.toml", "engine_specs/cars/*.toml", "engine_specs/cars/*.md", "engine_specs/*.md",
        "thresholds/*.py", "thresholds/*.md") for p in glob.glob(os.path.join(HERE, *pat.split("/")))]
    other.append("data/derived_params.json")
    # the environment's pins, which every subcommand of Run 1 compares (epa_freeze.version_problems reads the
    # code tree's copy; WP3's second fix of 23 October 2026)
    other.append("requirements-lock.txt")
    return tuple(sorted(py | set(other)))


CODE_FILES = _code_files()

# ---------------------------------------------------------------------------- synthetic engines
TABLE_KEYS = {"steady": "steady", "initial": "initial", "final": "final"}


def table_key(spec):
    """A table's key in a SyntheticEngine: its role and index, never its name ("steady0")."""
    return f"{spec.role}{spec.index}"


def table_names(engine):
    """{"steady0": name, ..., "initial0": name, "final0": name}: role and index to the table's
    file name, from epa_rows.TABLES (no literal name, amendment C3)."""
    return {table_key(s): s.name for s in epa_rows.TABLES[engine]}


@dataclass(frozen=True)
class SyntheticEngine:
    """What a synthetic engine's tables hold. lines are the contract lines it should come out
    with (merged names "1750/1800"); steady_rows_per_line {"steady0": {line: n}}; holds_per_line
    {line: n} (High Load Initial and Final share them); lam_ref {"steady0": lambda} is the
    closed-loop lambda of each steady table (the holds take the last steady table's, as
    split.compute does); held_out_lines and hot_map_floor_kpa are what split.compute must give
    for this design (make_repo asserts both: they are expectations, never inputs); values, when
    given, maps (table key, line, i) to a row's cells and replaces default_cells; overrides
    {(table key, line, i): {column: text}} edits single cells (a sentinel, an empty lambda)."""
    engine: str
    lines: tuple
    held_out_lines: tuple
    steady_rows_per_line: Mapping
    holds_per_line: Mapping
    lam_ref: Mapping
    hot_map_floor_kpa: float
    values: Optional[Callable] = None
    overrides: Mapping = field(default_factory=dict)


def _fmt(x, nd=2):
    return repr(float(round(x, nd)))


def default_cells(se, key, line, i):
    """A plausible synthetic row: MAP spread over 30-190 kPa on a steady line and 120 kPa up in
    25 kPa steps over the holds; BMEP, torque, the meter, TIT and TIP rising with MAP; lambda at
    the table's closed-loop value below 150 kPa and enriched above; spark falling with MAP. Every
    number is made up here, printed to 0.01 as EPA's are (0.001 for lambda)."""
    groups = [int(x) for x in line.split("/")]
    steady = key.startswith("steady")
    nominal = groups[0] if steady else groups[-1]
    lam_ref = se.lam_ref[key] if steady else se.lam_ref[sorted(k for k in se.lam_ref)[-1]]
    if steady:
        n = se.steady_rows_per_line[key][line]
        mp = 30.0 + i * (160.0 / max(n - 1, 1))
        lam = lam_ref if mp < 150.0 else lam_ref - 0.002 * (mp - 140.0)
        spark = 38.0 - 0.15 * mp
    else:
        mp = 120.0 + 25.0 * i + (3.0 if key.startswith("initial") else 0.0)
        lam = lam_ref if i < 2 else lam_ref - 0.10 - 0.02 * (i - 2)
        spark = 12.0 - 0.04 * (mp - 120.0)
    rpm = nominal + 1.0 + 0.5 * i
    bmep = (mp - 22.0) * 0.1
    torque = bmep * 19.9
    fuel = max(torque, 1.0) * rpm / 9549.0 / (0.30 * 42.9)
    c = {
        "speed_rpm": _fmt(rpm), "torque_nm": _fmt(torque), "bmep_bar": _fmt(bmep), "cell_temp_c": "24.5",
        "cell_press_kpa_abs": "98.6", "bsfc_g_per_kwh": "250.0", "bte_pct": "33.0",
        "fuel_meter_flow_gps": _fmt(fuel), "injector_fuel_flow_gps": _fmt(fuel * 1.03),
        "fuel_rail_press_mpa_gauge": "12.0", "spark_timing_cad_btdc": _fmt(spark), "coolant_temp_c": "90.0",
        "oil_sump_temp_c": _fmt(95.0 + 0.02 * mp), "cac_inlet_press_kpa_abs": _fmt(mp + 8.0),
        "cac_inlet_temp_c": "80.0", "cac_outlet_press_kpa_abs": _fmt(mp + 3.0), "cac_outlet_temp_c": "40.0",
        "intake_manifold_press_kpa_abs": _fmt(mp), "intake_manifold_temp_c": _fmt(30.0 + 0.06 * mp),
        "turbine_inlet_press_kpa_abs": _fmt(100.0 + 0.55 * mp), "turbine_inlet_temp_c": _fmt(450.0 + 2.2 * mp),
        "catalyst_inlet_press_kpa_abs": "103.0", "catalyst_inlet_temp_c": _fmt(400.0 + 2.0 * mp),
        "exhaust_lambda": _fmt(lam, 3), "exhaust_lambda_left": _fmt(lam, 3), "exhaust_lambda_right": _fmt(lam, 3),
        "intake_cam_phase_cad_ret": _fmt(8.0 + 0.05 * mp), "intake_cam_phase_cad_adv": _fmt(8.0 + 0.05 * mp),
        "exhaust_cam_phase_cad_ret": "4.0", "valve_overlap_cad": "12.0", "epa_atkinson_ratio": "1.2",
        "effective_compression_stroke_mm": "70.0", "effective_compression_ratio": "9.5",
        "effective_expansion_stroke_mm": "85.0", "effective_expansion_ratio": "11.0"}
    return c


def _lines(*rpm):
    return tuple(str(x) for x in rpm)


# The three default designs. Their held_out_lines and floors are what split.compute gives for
# them (make_repo checks); the special rows exercise decision 54's declared outcomes: a spark
# sentinel and an empty spark cell on fuel-cut and fired rows, a fired row without lambda, a
# Final row without a meter, an HD1 row with one bank empty -- on calibration and held lines.
_MZ = _lines(1500, 2000, 2500, 3000, 3500, 4000, 4500)
_HO = ("1000", "1500", "1750/1800", "2000", "2500", "3000", "3500", "4000", "4500")
_FD = _lines(1000, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000)
DEFAULT_SPECS = {
    "mazda_25t": SyntheticEngine(
        engine="mazda_25t", lines=_MZ, held_out_lines=("2000", "3500"),
        steady_rows_per_line={"steady0": {ln: 8 for ln in _MZ}}, holds_per_line={ln: 4 for ln in _MZ},
        lam_ref={"steady0": 1.0}, hot_map_floor_kpa=120.0,
        overrides={("steady0", "3000", 0): {"spark_timing_cad_btdc": "-120.0"},
                   ("steady0", "2000", 0): {"spark_timing_cad_btdc": "-120.0"},
                   ("steady0", "4000", 3): {"spark_timing_cad_btdc": ""},
                   ("steady0", "2500", 2): {"exhaust_lambda": ""},
                   ("steady0", "3500", 2): {"exhaust_lambda": ""},
                   ("steady0", "3500", 4): {"spark_timing_cad_btdc": ""},
                   ("final0", "3500", 0): {"exhaust_lambda": ""},
                   ("final0", "3000", 1): {"fuel_meter_flow_gps": ""}}),
    "honda_l15b7": SyntheticEngine(
        engine="honda_l15b7", lines=_HO, held_out_lines=("1750/1800", "3000"),
        steady_rows_per_line={"steady0": {ln: 7 for ln in _HO}},
        holds_per_line={ln: 4 for ln in _HO if ln not in ("1000", "4500")}, lam_ref={"steady0": 0.99},
        hot_map_floor_kpa=120.0),
    "ford_27tt": SyntheticEngine(
        engine="ford_27tt", lines=_FD, held_out_lines=None,
        steady_rows_per_line={"steady0": {ln: 6 for ln in _FD},
                              "steady1": {ln: 5 for ln in _lines(1500, 2000, 2500, 3000, 3500)}},
        holds_per_line={ln: 3 for ln in _lines(2000, 2500, 3000, 3500, 4000)},
        lam_ref={"steady0": 0.98, "steady1": 1.0}, hot_map_floor_kpa=120.0,
        overrides={("steady1", "2000", 3): {"exhaust_lambda_right": ""}}),
}


def _rows_of(se, spec):
    """[(line, i)] of one table, in file order: lines ascending, then i."""
    key = table_key(spec)
    order = sorted(se.lines, key=lambda ln: int(ln.split("/")[0]))
    if spec.role == "steady":
        per = se.steady_rows_per_line.get(key, {})
        return [(ln, i) for ln in order for i in range(per.get(ln, 0))]
    return [(ln, i) for ln in order for i in range(se.holds_per_line.get(ln, 0))]


def engine_folder(root, engine):
    """<root>/data/engines/<id>: where a synthetic repository keeps an engine's tables."""
    return os.path.join(root, "data", "engines", engine)


def table_file(root, engine, role, index):
    spec = next(s for s in epa_rows.TABLES[engine] if (s.role, s.index) == (role, index))
    return os.path.join(engine_folder(root, engine), spec.name)


def write_tables(root, se):
    """The engine's synthetic tables under <root>/data/engines/<id>/, with epa_rows.HEADERS,
    written with csv.writer (LF), data from spreadsheet row 6. {table name: path}."""
    folder = engine_folder(root, se.engine)
    os.makedirs(folder, exist_ok=True)
    out = {}
    for spec in epa_rows.TABLES[se.engine]:
        header = epa_rows.HEADERS[(spec.engine, spec.role, spec.index)]
        key = table_key(spec)
        values = se.values or (lambda k, ln, i: default_cells(se, k, ln, i))
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        for n, (ln, i) in enumerate(_rows_of(se, spec)):
            cells = dict(values(key, ln, i))
            cells.update(se.overrides.get((key, ln, i), {}))
            cells.update(source_file="synthetic.xlsx", source_sheet=f"synthetic {spec.role}",
                         source_row=str(epa_rows.FIRST_DATA_ROW + n),
                         test_cell="HD1" if (se.engine == "ford_27tt" and key != "steady0") else "Cell S",
                         fuel_report=_fuel(se.engine, spec.name)["fuel_report"])
            w.writerow([cells.get(c, "") for c in header])
        path = os.path.join(folder, spec.name)
        with open(path, "wb") as fh:
            fh.write(buf.getvalue().encode("utf-8"))
        out[spec.name] = path
    return out


_GEOMETRY = {"mazda_25t": (2.488, 4, 10.5, 89.0, None), "honda_l15b7": (1.496, 4, 10.6, 73.0, 89.4),
             "ford_27tt": (2.694, 6, 10.0, 83.0, 83.0)}


def write_engine_json(root, se):
    """A synthetic epa_engine.json: the allowlisted facts, and two curves whose measured_at_speed
    records the loader must never return (amendment C7)."""
    disp, ncyl, cr, bore, stroke = _GEOMETRY[se.engine]
    curve = dict(speed_rpm=[1000.0, 2000.0], torque_nm=[100.0, 200.0], node_is_measured=[True, False],
                 measured_at_speed=[dict(table=epa_rows.TABLES[se.engine][0].name, source_row=6, speed_rpm=1001.0,
                                         torque_nm=123.0), None], note="synthetic")
    out = dict(_generated="synthetic, by test_epa_fixtures.py", engine_id=se.engine, displacement_l=disp,
               n_cylinders=ncyl, compression_ratio=cr, bore_mm=bore, stroke_mm=stroke,
               geometry_notes={"bore_mm": "synthetic"}, wot_torque_curve=curve, closed_throttle_torque_curve=curve,
               alpha_fuel={"research_octane_number": 97.6, "energy_density_MJpkg": 42.908},
               tables={s.name: dict(test_cell="Cell S", fuel_report=_fuel(se.engine, s.name)["fuel_report"], rows=0)
                       for s in epa_rows.TABLES[se.engine]},
               reference_only_columns=["exhaust_lambda", "spark_timing_cad_btdc"], status_definitions={})
    with open(os.path.join(engine_folder(root, se.engine), "epa_engine.json"), "wb") as fh:
        fh.write((json.dumps(out, indent=1, ensure_ascii=True) + "\n").encode("ascii"))


def write_channels_csv(root, se):
    """A synthetic epa_channels.csv: names, units and statuses, and no range of any data."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["table", "column", "epa_channel", "epa_unit", "epa_description", "epa_status", "reference_only",
                "calculated", "n_values", "n_empty", "min", "max"])
    for s in epa_rows.TABLES[se.engine]:
        for c in epa_rows.HEADERS[(s.engine, s.role, s.index)][len(epa_rows.PROVENANCE):]:
            w.writerow([s.name, c, c, "synthetic", "synthetic", "Measured", 0, 0, "", "", "", ""])
    with open(os.path.join(engine_folder(root, se.engine), "epa_channels.csv"), "wb") as fh:
        fh.write(buf.getvalue().encode("utf-8"))


# The synthetic fuels: the three engines' typed values (engine_specs/<id>.toml [fuel]), the Ford's
# Cell 9 at its own batch's 14.557 (decision 69). Synthetic records, shaped as the contract's.
def _fuel(engine, name):
    if engine == "honda_l15b7":
        lhv, afr, ftag = 42.898, 14.554, "25842"
    elif engine == "ford_27tt" and name == epa_rows.TABLES["ford_27tt"][0].name:
        lhv, afr, ftag = 42.908, 14.557, "25278"
    else:
        lhv, afr, ftag = 42.908, 14.559, "26864"
    return dict(ftag=ftag, lhv_mj_per_kg=lhv, carbon_weight_fraction=0.8663, afr_st=afr, alcohol_pct_vol=0.0,
                fuel_report=ftag, source="synthetic")


# ---------------------------------------------------------------------------- git
GIT_ENV = {"GIT_AUTHOR_NAME": "synthetic", "GIT_AUTHOR_EMAIL": "synthetic@example.invalid",
           "GIT_AUTHOR_DATE": "2026-10-23T12:00:00+03:00", "GIT_COMMITTER_NAME": "synthetic",
           "GIT_COMMITTER_EMAIL": "synthetic@example.invalid", "GIT_COMMITTER_DATE": "2026-10-23T12:00:00+03:00"}


def git(root, *args, check=True):
    env = dict(os.environ, **GIT_ENV)
    r = subprocess.run(["git", "-C", root, "-c", "core.safecrlf=false", *args], capture_output=True, env=env)
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {root}: {r.stderr.decode(errors='replace')}")
    return r.stdout.decode(errors="replace").strip()


def commit_all(root, message):
    """Stage everything and commit with the fixed names and dates; the new HEAD."""
    git(root, "add", "-A")
    git(root, "commit", "-q", "--allow-empty", "-m", message)
    return git(root, "rev-parse", "HEAD")


@dataclass(frozen=True)
class Repo:
    root: str
    contract_commit: str
    head: str


def _contract_paths(root):
    return (os.path.join(root, *os.path.relpath(common.CONTRACT_JSON, common.REPO).split(os.sep)),
            os.path.join(root, *os.path.relpath(common.CONTRACT_MD, common.REPO).split(os.sep)))


def synthetic_source(repo):
    """The epa_rows.Source of a synthetic repository."""
    cj, cm = _contract_paths(repo.root)
    return epa_rows.Source(root=repo.root, engine_dir=os.path.join(repo.root, "data", "engines"), contract_json=cj,
                           contract_md=cm, contract_commit=repo.contract_commit, allow_poisoned_tables=False)


def split_of(root):
    """The generator's own split.compute() over root's synthetic tables, run in root's
    interpreter as a subprocess (python -I -B -c, so thresholds.common.REPO is root): the one
    sanctioned use of split.compute outside test_epa_rows.Structural and validate_epa.arm, since
    the synthetic contract's populations must be the generator's (mistake 10). Returns
    (dict, text): text is split.json as the generator writes it (indent 1, ASCII)."""
    code = ("import json, sys; sys.path.insert(0, sys.argv[1]); from thresholds import split; "
            "sys.stdout.buffer.write(json.dumps(split.compute(), indent=1, ensure_ascii=True).encode('ascii'))")
    r = subprocess.run([sys.executable, "-I", "-B", "-c", code, root], capture_output=True, cwd=root)
    if r.returncode != 0:
        raise RuntimeError("split.compute failed on the synthetic tables: " + r.stderr.decode(errors="replace"))
    text = r.stdout.decode("ascii")
    out = json.loads(text)
    assert json.dumps(out, indent=1, ensure_ascii=True) == text
    return out, text


# Stand-ins for the contract's B58 and rule blocks: synthetic values, shaped as version 4's (whose keys
# version 5 kept), so that a view of a synthetic contract has every field. Not the contract's numbers.
CONTRACT_BLOCKS = {
    "mei_points": 6.0, "r1_housing_k": 30.0,
    "budget": {"b_points": 1.0, "parts": ["synthetic"] * 6, "n_parts": 6},
    "conventions": {"inputs_fed": "synthetic", "lambda": "synthetic", "fuel": "synthetic",
                    "lambda_missing": "synthetic", "spark_sentinel": "synthetic", "held_out_counts": "synthetic",
                    "censored": "synthetic", "air_for_calibration": "synthetic", "populations": "synthetic",
                    "u_val": "synthetic", "u_D": "synthetic", "labels": "synthetic",
                    "statistic_details": {"decision": "synthetic", "d1": "synthetic", "e8": "synthetic",
                                          "e8_subsets": "synthetic", "e8_min_rows": 3, "lines": "synthetic"}},
    "model_form": {"base_A": "synthetic", "alternatives_in_order": ["B", "C", "D"], "in_sample_stage": "synthetic",
                   "in_sample_rules": {"criterion": "synthetic"}, "plant_in_use": "synthetic",
                   "lambda_clip_floor": "synthetic", "neutral_action_identity": {"rule": "synthetic"}},
    "propagation_b58": {"source": "synthetic", "G_gas_over_42C_k": 1000.0,
                        "used": {"gas_k_per_pct_torque": 3.0, "flow_pct_per_pct_torque": 0.01}},
    "ecu_strategy_b58": {"source": "synthetic",
                         "k3_pair_change_vs_lambda": [[-0.02, -0.05], [0.0, 0.0], [0.02, 0.04]],
                         "k3_pair_change_vs_spark": [[-0.75, 0.03], [0.0, 0.0], [0.75, -0.02]],
                         "worth_b": {"lambda_rich": {"shift": -0.02, "b": 1.0}}},
    "perturbations_E6": [{"n": n, "constant": f"synthetic {n}", "band": "synthetic", "must_show": "synthetic",
                          "refit": n in (1, 2, 3, 7)} for n in range(1, 14)],
    "tests_lists": {"decision": "synthetic", "rule": "synthetic", "lists": {"E1a": ["synthetic"]}},
}
_SYNTHETIC_ROWS = (("E1a", 0.05, "%"), ("E2a", 0.05, "%"), ("E3a", 20.0, "K"), ("E4a", 20.0, "K"),
                   ("E4b", 0.2, "%"), ("D1", 0.08, "%"), ("L0", 5.0, "K"), ("L1", 9.9, "K"), ("E8", 0.1, "%"),
                   ("E1b", None, "%"), ("E1i", None, "%"))


def synthetic_contract(root, specs, *, contract_commit=None, blocks=None):
    """A synthetic contract (schema 4) for root's synthetic tables: the held-out structure,
    lambda_ref, the hot floor, the coverage and the table counts from split_of(root), the
    generator's own; the fuels, the lambda clip floor (thresholds/contract.py's rule, min(0.70,
    deepest - 0.01) to 0.001) and the B58 blocks synthetic; generators.sha256 from root's copies
    of thresholds/ and engine_thresholds.py (byte for byte this tree's), epa_tables_sha256 from the
    written tables, generator_inputs_sha256 from split.json's text and the synthetic K3 file.
    contract_commit, when given, is only recorded in _generated."""
    sp, text = split_of(root)
    for eng, se in specs.items():
        got = sp[eng]
        if se.held_out_lines is not None and tuple(got["held_out_lines"]) != tuple(se.held_out_lines):
            raise AssertionError(f"{eng}: split gives held-out lines {got['held_out_lines']}, the design "
                                 f"{list(se.held_out_lines)}")
        if tuple(got["lines"]) != tuple(se.lines):
            raise AssertionError(f"{eng}: split gives lines {got['lines']}, the design {list(se.lines)}")
        if got["hot_map_floor_kpa"] != se.hot_map_floor_kpa:
            raise AssertionError(f"{eng}: split gives a hot floor {got['hot_map_floor_kpa']}")
    b = copy_blocks(blocks)
    engines_block = {}
    for eng in epa_rows.TABLES:
        s = sp[eng]
        e = {k: s[k] for k in ("lines", "eligible", "offsets", "offset_chosen", "held_out_lines", "tables",
                               "hot_map_floor_kpa", "lambda_ref", "per_held_out_line", "deciding_lines",
                               "pooled_counts", "coverage", "n_rows", "n_held_out_rows", "held_out_rows")}
        e["alpha_nodes_removed"] = []
        e["fuel_by_table"] = {t.name: _fuel(eng, t.name) for t in epa_rows.TABLES[eng]}
        lm = s["lambda_min_cell_referenced"]
        e["lambda_clip_floor"] = {"deepest_epa_lambda_cell_referenced": lm["value"],
                                  "floor": round(min(0.70, lm["value"] - 0.01), 3), "where": lm}
        engines_block[eng] = e
    gens = {}
    for p in sorted(glob.glob(os.path.join(root, "thresholds", "*.py")) + glob.glob(os.path.join(root, "thresholds", "*.md"))
                    + [os.path.join(root, "engine_thresholds.py")]):
        gens[os.path.relpath(p, root).replace(os.sep, "/")] = common.sha_text(p)
    k3 = os.path.join(root, "results", "ENGINE_THRESHOLDS", "ecu", "k3_nominal.json")
    thresholds = [dict(engine=eng, row=r, R=R, unit=u, kind="synthetic", on_fail="synthetic", part="synthetic",
                       quantity="synthetic", rows="synthetic", statistic="synthetic")
                  for eng in list(epa_rows.TABLES) + ["b58"] for r, R, u in _SYNTHETIC_ROWS]
    return dict(
        _generated=f"synthetic, by test_epa_fixtures.py ({contract_commit or 'its own commit'})", schema=4,
        status="synthetic", **b, thresholds=thresholds, engines=engines_block, rows=[], cars=[], d3_files_c3=[],
        generators={"entry_point": "synthetic", "sha256": gens, "hash_rule": "sha_text"},
        generator_inputs_sha256={"split.json": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                                 "ecu/k3_nominal.json": common.sha_text(k3)},
        epa_tables_sha256=dict(sp["sha256_inputs"]))


def copy_blocks(blocks):
    return json.loads(json.dumps(CONTRACT_BLOCKS if blocks is None else blocks))


def write_contract(root, contract):
    """The contract's two files in root, as the generator writes the JSON (indent 1, ASCII, LF)."""
    cj, cm = _contract_paths(root)
    os.makedirs(os.path.dirname(cj), exist_ok=True)
    with open(cj, "wb") as fh:
        fh.write((json.dumps(contract, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii"))
    with open(cm, "wb") as fh:
        fh.write(b"# Synthetic validation contract\n\nWritten by test_epa_fixtures.py; no figure of the project.\n")


def read_contract(repo):
    """A synthetic repository's own contract (never the real one)."""
    cj, _ = _contract_paths(repo.root)
    with open(cj, encoding="utf-8") as fh:
        return json.load(fh)


def make_repo(tmp, specs=None):
    """A temporary git repository under tmp (see the module's docstring). specs: {engine:
    SyntheticEngine}; an engine left out takes DEFAULT_SPECS' (split.compute reads all three)."""
    specs = {**DEFAULT_SPECS, **(specs or {})}
    root = os.path.join(tmp, "repo")
    os.makedirs(root)
    git(root, "init", "-q", "-b", "main")
    git(root, "config", "core.autocrlf", "true")
    git(root, "config", "user.name", GIT_ENV["GIT_AUTHOR_NAME"])
    git(root, "config", "user.email", GIT_ENV["GIT_AUTHOR_EMAIL"])
    for rel in CODE_FILES:
        src = os.path.join(HERE, *rel.split("/"))
        dst = os.path.join(root, *rel.split("/"))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copyfile(src, dst)
    with open(os.path.join(root, ".gitignore"), "wb") as fh:
        fh.write(b"__pycache__/\n")
    os.makedirs(os.path.join(root, "data", "engines"), exist_ok=True)
    with open(os.path.join(root, "data", "engines", ".gitattributes"), "wb") as fh:
        fh.write(b"# synthetic: store and check out these files exactly as written\n* -text\n")
    for eng in epa_rows.TABLES:
        write_tables(root, specs[eng])
        write_engine_json(root, specs[eng])
        write_channels_csv(root, specs[eng])
    k3 = os.path.join(root, "results", "ENGINE_THRESHOLDS", "ecu", "k3_nominal.json")
    os.makedirs(os.path.dirname(k3), exist_ok=True)
    with open(k3, "wb") as fh:
        fh.write(json.dumps({"mode": "k3", "name": "nominal", "synthetic": True, "time_above_nominal_s": 400},
                            indent=1).encode("ascii"))
    commit_all(root, "synthetic code and tables")
    write_contract(root, synthetic_contract(root, specs))
    head = commit_all(root, "synthetic contract")
    return Repo(root=root, contract_commit=head, head=head)


def copy_repo(repo, tmp):
    """A copy of a synthetic repository under tmp, its .git included (the same shas)."""
    root = os.path.join(tmp, "repo")
    shutil.copytree(repo.root, root)
    return Repo(root=root, contract_commit=repo.contract_commit, head=repo.head)


def rewrite_contract(repo, edit):
    """Apply edit(contract dict) to a synthetic repository's contract and commit it: the new
    commit is the contract commit, so guard 1 passes and the next guard meets the edit."""
    c = read_contract(repo)
    edit(c)
    write_contract(repo.root, c)
    head = commit_all(repo.root, "synthetic contract, edited")
    return Repo(root=repo.root, contract_commit=head, head=head)


def pin_contract_commit(repo):
    """The synthetic repository's copy of epa_rows.py with its CONTRACT_COMMIT set to the repository's own
    contract commit, committed: then epa_rows.Source.repository() inside that repository -- the command line
    of calibrate_epa.py or validate_epa.py run there in a subprocess -- reads the synthetic contract through
    every guard, as the real tree reads version 5 (WP3's fix of 23 October 2026: the command line itself
    is tested on synthetic tables, never on this tree's). Returns the Repo, its head the new commit."""
    path = os.path.join(repo.root, "epa_rows.py")
    with open(path, encoding="utf-8") as fh:
        src = fh.read()
    pinned = [ln for ln in src.splitlines() if ln.startswith("CONTRACT_COMMIT = ")]
    if len(pinned) != 1:
        raise RuntimeError("epa_rows.py pins its contract commit on no single line")
    src = src.replace(pinned[0], f'CONTRACT_COMMIT = "{repo.contract_commit}"')
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(src)
    head = commit_all(repo.root, "synthetic: epa_rows pins the synthetic contract")
    return Repo(root=repo.root, contract_commit=repo.contract_commit, head=head)


def rehash_tables(repo):
    """Record the tables as they now are in the contract's epa_tables_sha256, and commit: a
    table edit then reaches the guards after the hash."""
    def edit(c):
        for k in c["epa_tables_sha256"]:
            eng, name = k.split("/", 1)
            c["epa_tables_sha256"][k] = common.sha_raw(os.path.join(engine_folder(repo.root, eng), name))
    return rewrite_contract(repo, edit)


def held_rows(repo, engine):
    """{table: sorted held-out source rows} of a synthetic repository's own contract."""
    out = {}
    for rec in read_contract(repo)["engines"][engine]["held_out_rows"]:
        out.setdefault(rec["table"], []).append(rec["source_row"])
    return {k: sorted(v) for k, v in out.items()}


def edit_table(path, edit):
    """Rewrite one table through edit(header, rows) -> rows (lists of strings), csv.writer, LF."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    body = edit(rows[0], rows[1:])
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(rows[0])
    w.writerows(body)
    with open(path, "wb") as fh:
        fh.write(buf.getvalue().encode("utf-8"))


def commit_armed(repo, engine, armed):
    """results/EPA_VALIDATION/<id>/ARMED.json written and committed; the new HEAD."""
    path = os.path.join(repo.root, "results", "EPA_VALIDATION", engine, "ARMED.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write((json.dumps(armed, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii"))
    return commit_all(repo.root, f"synthetic ARMED.json for {engine}")


def add_worktree(repo):
    """A linked worktree of the synthetic repository (what amendment C6 refuses); its path."""
    path = repo.root + "_wt"
    git(repo.root, "worktree", "add", "-q", "--detach", path, "HEAD")
    return path


def b58_identity():
    """{"plant_sha", "engine_sha"} of the B58 as this code builds it, what validate_epa.arm requires of the
    tightenings' provenance (decision 71). Imported here, not at the top: this module imports no plant code
    at import time."""
    import engines
    import epa_freeze
    return {"plant_sha": epa_freeze.plant_sha("b58"), "engine_sha": engines.engine_sha(engines.get("b58"))}


def synthetic_tightenings(repo, *, plant):
    """results/EPA_TIGHTENINGS.json in validate_epa's schema (WP3_INTERFACES section 7.5),
    synthetic values, committed; its path."""
    grid_l = [s for s, _ in CONTRACT_BLOCKS["ecu_strategy_b58"]["k3_pair_change_vs_lambda"]]
    grid_s = [s for s, _ in CONTRACT_BLOCKS["ecu_strategy_b58"]["k3_pair_change_vs_spark"]]
    rec = {"schema": "epa-tightenings/1", "plant": plant, "roads_sha": "0" * 64, "roads_seed": 0,
           "L1": {"slope_points_per_K": 0.05, "set": "synthetic", "shift_k": 10, "damage_reading": "synthetic"},
           "E8": {"k3_pair_change_vs_lambda_roads": [[s, 0.0] for s in grid_l],
                  "k3_pair_change_vs_spark_roads": [[s, 0.0] for s in grid_s]},
           # the B58 as this code builds it: the arming compares both with the plant itself (decision 71; WP3's
           # second fix of 23 October 2026), so a synthetic word there would be refused
           "provenance": {"commit": repo.head, "code_sha_text": {}, **b58_identity()}}
    path = os.path.join(repo.root, "results", "EPA_TIGHTENINGS.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write((json.dumps(rec, indent=1) + "\n").encode("ascii"))
    commit_all(repo.root, "synthetic tightenings")
    return path


# ---------------------------------------------------------------------------- in-memory rows
def _pops(fields_, kind, floor):
    lam = fields_.get("lam_meas")
    r = {"intake_manifold_press_kpa_abs": repr(fields_["map_kpa"]), "bmep_bar": repr(fields_["bmep_bar"]),
         "fuel_meter_flow_gps": "" if fields_.get("fuel_meter_gps") is None else repr(fields_["fuel_meter_gps"]),
         "exhaust_lambda": "" if lam is None else repr(lam)}
    c = split.classify(r, fields_["lam_ref"], floor, kind)
    a = split.classify(r, fields_["lam_ref"], -math.inf, kind)
    return epa_rows.Populations(**{k: bool(c[k]) for k in epa_rows._POP_KEYS},
                                fired_l1=bool(a["hot_l1"] and c["fired"]))


def _point(cls, kind, fields_):
    f = dict(engine="mazda_25t", table="synthetic", source_row=6, test_cell="Cell S", fuel_report="26864",
             origin="fixture", line="2000", nominal_rpm=2000, hold=None if kind == "steady" else 6,
             speed_rpm=2001.0, map_kpa=100.0, imt_k=310.0, ect_k=363.15, oil_k=368.15, spark_btdc=20.0,
             spark_sentinel=False, lam_meas=1.0, lam_banks=None, lambda_missing=False, lam_ref=1.0,
             torque_nm=150.0, bmep_bar=7.8, fuel_meter_gps=5.0, meter_missing=False, injector_fuel_gps=5.1,
             tit_c=700.0, tip_kpa=155.0, baro_kpa=98.6, cell_temp_k=297.65, cam_cad=13.0,
             cam_channel="intake_cam_phase_cad_ret", cam_missing=False, exhaust_cam_cad=4.0, valve_overlap_cad=12.0,
             atkinson_ratio=1.2, eff_compression_stroke_mm=None, eff_expansion_stroke_mm=None,
             eff_compression_ratio=None, eff_expansion_ratio=None)
    floor = fields_.pop("hot_floor", 100.0)
    f.update(fields_)
    if f["lam_meas"] is None:
        f["lambda_missing"] = True
    if f["fuel_meter_gps"] is None:
        f["meter_missing"] = True
    if f["spark_btdc"] is None:
        f["spark_sentinel"] = True
    if "pops" not in fields_:
        f["pops"] = _pops(f, kind, floor)
    return cls(**f)


def point_row(**fields_):
    """An in-memory SteadyRow (kind="steady", the default) or FinalRow (kind="final"), every
    field defaulted to a plausible synthetic value and origin "fixture"; pops computed by
    split.classify from the fields unless given (hot_floor= sets the floor, 100 kPa)."""
    kind = fields_.pop("kind", "steady")
    return _point(epa_rows.FinalRow if kind == "final" else epa_rows.SteadyRow, kind, fields_)


def held_out_row(**fields_):
    """An in-memory HeldOutRow (kind "steady" or "final")."""
    kind = fields_.pop("kind", "steady")
    return _point(lambda **f: epa_rows.HeldOutRow(**f, kind=kind), kind, fields_)


def initial_row(**fields_):
    f = dict(engine="mazda_25t", table="synthetic", source_row=6, test_cell="Cell S", line="2000", nominal_rpm=2000,
             hold=6, speed_rpm=2003.0, torque_nm=160.0, origin="fixture", transient=True)
    f.update(fields_)
    return epa_rows.InitialRow(**f)


# ---------------------------------------------------------------------------- models
@dataclass(frozen=True)
class _ToyModelOut:
    torque_nm: float
    fuel_gps: float
    air_gps: float
    egt_c: float
    knock_integral: float
    eta_v: float


@dataclass(frozen=True)
class _ToyEcuOut:
    spark_btdc: float
    lam: float
    cam_deg: Optional[float]


def _out_types():
    """epa_stats' ModelOut and EcuOut when it exists (WP3_INTERFACES section 5.2.2), else the
    same fields here, so the fixture's own self-test runs before epa_stats is written."""
    try:
        import epa_stats
        return epa_stats.ModelOut, epa_stats.EcuOut
    except ImportError:
        return _ToyModelOut, _ToyEcuOut


class ToyModel:
    """Closed-form laws satisfying epa_stats' model protocol, every coefficient a class
    attribute so a test computes its hand answer from the same numbers:
      air    = K_AIR * MAP * rpm/1000 * 300/IAT                     g/s
      fuel   = air / (afr_st * lam)                                g/s
      torque = T0 + K_T * MAP + K_SPARK * (spark - SPARK_REF)      N m
      egt    = TIT0 + K_TIT * MAP - K_TIT_LAM * (1 - lam)          degC
      base spark = S0 - S_MAP * MAP + S_RPM * rpm/1000; the ECU's lambda is 1 up to ENR_MAP and
      falls ENR_SLOPE per kPa above it; no cam (form A); knock_integral 0; eta_v = air / (K_AIR *
      100 * rpm/1000), the air relative to 100 kPa at 300 K."""
    K_AIR, T0, K_T, K_SPARK, SPARK_REF = 0.01, -30.0, 1.5, 0.8, 20.0
    TIT0, K_TIT, K_TIT_LAM = 400.0, 2.0, 500.0
    S0, S_MAP, S_RPM, ENR_MAP, ENR_SLOPE = 40.0, 0.15, 1.0, 150.0, 0.001
    CHARGE_GAIN = 0.2

    def air(self, rpm, map_kpa, iat_k):
        return self.K_AIR * map_kpa * rpm / 1000.0 * 300.0 / iat_k

    def cycle(self, x, *, dtheta):
        mo, _ = _out_types()
        air = self.air(x.rpm, x.map_kpa, x.iat_k)
        return mo(torque_nm=self.T0 + self.K_T * x.map_kpa + self.K_SPARK * (x.spark_btdc - self.SPARK_REF),
                  fuel_gps=air / (x.fuel.afr_st * x.lam), air_gps=air,
                  egt_c=self.TIT0 + self.K_TIT * x.map_kpa - self.K_TIT_LAM * (1.0 - x.lam), knock_integral=0.0,
                  eta_v=air / (self.K_AIR * 100.0 * x.rpm / 1000.0))

    def base_spark(self, rpm, map_kpa):
        return self.S0 - self.S_MAP * map_kpa + self.S_RPM * rpm / 1000.0

    def lam_at(self, map_kpa):
        return 1.0 if map_kpa <= self.ENR_MAP else 1.0 - self.ENR_SLOPE * (map_kpa - self.ENR_MAP)

    def cam(self, rpm, map_kpa):
        return None

    def ecu_at(self, rpm, map_kpa, iat_k, ect_k):
        _, eo = _out_types()
        return eo(spark_btdc=self.base_spark(rpm, map_kpa), lam=self.lam_at(map_kpa), cam_deg=None)

    def ecu_trace(self, rpm, map_kpa, iat_k, ect_k, dt):
        import numpy as np
        rpm, mp = np.asarray(rpm, dtype=float), np.asarray(map_kpa, dtype=float)
        return (self.S0 - self.S_MAP * mp + self.S_RPM * rpm / 1000.0,
                np.where(mp <= self.ENR_MAP, 1.0, 1.0 - self.ENR_SLOPE * (mp - self.ENR_MAP)))

    def charge(self, t_amb_k, t_block_k):
        return t_amb_k if t_block_k is None else t_amb_k + self.CHARGE_GAIN * (t_block_k - t_amb_k)


def b58_values():
    """The B58's built values for every DERIVED field of the EPA set (engines.EPA_DERIVED_FIELDS),
    shaped as an EPA derived file ({section: {key: value}}, the deliverable-torque table [])."""
    import engines
    b = engines.get("b58")
    out = {}
    for (rec, fld), (sec, key) in engines.EPA_DERIVED_FIELDS.items():
        if key is None:
            out[sec] = []
            continue
        owner = b.car if rec == "car" else getattr(b.engine, rec)
        v = getattr(owner, fld)
        out.setdefault(sec, {})[key] = list(v) if isinstance(v, tuple) else v
    return out


def truth_candidate(name, *, theta):
    """engines.build_candidate(name, ...) from the B58's values (b58_values) with theta's entries
    put in: {"section.key": value}, each a Python float, int or str (amendment B10). A known truth
    for recovery tests on synthetic inputs; no EPA input."""
    import engines
    values = b58_values()
    for k, v in theta.items():
        sec, key = k.split(".", 1)
        if key not in values.get(sec, {}):
            raise KeyError(f"truth_candidate: {k} is not a DERIVED field of the EPA set")
        values[sec][key] = v
    return engines.build_candidate(name, values)


def rows_from_plant(plant, *, inputs, seed):
    """SteadyRow and FinalRow records whose outputs are plant.run_cycle's at synthetic inputs
    (the model's own back-pressure law and its ECU's cam, plan 5.1). inputs: Mappings with rpm,
    map_kpa, imt_k, ect_k, spark_btdc, lam and optionally kind ("steady" or "final"), line,
    source_row, table, lam_ref. seed None: exact outputs; an int: noise from
    numpy.random.default_rng([0xF1, seed]), torque and meter 0.5 %, TIT 3 K."""
    import numpy as np
    import engine_env
    import plant as P
    e = plant.engine
    rng = None if seed is None else np.random.default_rng([0xF1, seed])
    out = []
    for k, x in enumerate(inputs):
        rpm, mp = float(x["rpm"]), float(x["map_kpa"])
        cam = engine_env.BaselineECU(e.ecu).cam_deg(rpm, mp)
        op = P.Operating(rpm, mp, float(x["imt_k"]), float(x["ect_k"]), float(x["spark_btdc"]), float(x["lam"]),
                         P.exhaust_backpressure_kpa(mp, engine=e))
        r = P.run_cycle(op, engine=e, dtheta=P.DTHETA_DEG, cam_deg=cam)
        torque, fuel, tit = float(r.torque_nm), float(r.mdot_fuel_gps), float(r.egt_c)
        if rng is not None:
            torque *= float(1.0 + 0.005 * rng.standard_normal())
            fuel *= float(1.0 + 0.005 * rng.standard_normal())
            tit += float(3.0 * rng.standard_normal())
        kind = x.get("kind", "steady")
        out.append(point_row(kind=kind, engine=plant.engine.id if hasattr(plant.engine, "id") else "synthetic",
                             table=x.get("table", "synthetic"), source_row=int(x.get("source_row", 6 + k)),
                             line=str(x.get("line", int(round(rpm / 50.0)) * 50)),
                             nominal_rpm=int(round(rpm / 50.0)) * 50, hold=(6 + k) if kind == "final" else None,
                             speed_rpm=rpm, map_kpa=mp, imt_k=float(x["imt_k"]), ect_k=float(x["ect_k"]),
                             spark_btdc=float(x["spark_btdc"]), lam_meas=float(x["lam"]),
                             lam_ref=float(x.get("lam_ref", 1.0)), torque_nm=torque, bmep_bar=float(r.bmep_bar),
                             fuel_meter_gps=fuel, injector_fuel_gps=fuel, tit_c=tit,
                             cam_cad=None if cam is None else float(cam), cam_missing=cam is None))
    return tuple(out)


# ---------------------------------------------------------------------------- D3 traces
# The contract's own D3 channel names (its section 5), and the three it does not name -- time, road
# speed, coolant -- under the names d3_rows pins for the CX-9 (d3_rows.CHANNELS, from CATALOGUE.md;
# WP3_INTERFACES 5.9). They were placeholders here ("Time[s]", "Eng_coolant_temp_PCM[C]") until WP3's
# integration (23 October 2026) took d3_rows' pins, which the CX-9's reader requires.
D3_CHANNELS = ("Dyno_TractiveForce[N]", "Trans_gear_actual_CAN[]", "Eng_speed_CAN", "Trans_turbine_shaft_speed_TCM",
               "HVAC_ACComp_cycling_switch_PCM", "Eng_ManifoldAir_pressure_sensor_PCM[kPa]",
               "Eng_FuelFlow_Direct2[gps]", "Eng_mass_air_flow_PCM[gps]", "Eng_equiv_ratio_b1_s1_PCM[]")
D3_ROLES = ("time", "speed", "coolant")


def d3_names():
    """{role: header} of the three channels the contract does not name, the first name d3_rows.CHANNELS
    accepts for each (imported here, not at the top: the fixtures load without d3_rows)."""
    import d3_rows
    by_role = {c.role: c for c in d3_rows.CHANNELS.channels}
    return {r: by_role[r].headers[0][0] for r in D3_ROLES}


def synthetic_columns(n=600, dt=0.1, **kw):
    """{channel header: list of floats} of a synthetic D3 drive: a steady segment in one gear;
    every column overridable by keyword (the header name, or time/speed/coolant)."""
    t = [round(k * dt, 6) for k in range(n)]
    names = d3_names()
    cols = {names["time"]: t, names["speed"]: [40.0] * n, names["coolant"]: [90.0] * n,
            "Dyno_TractiveForce[N]": [800.0] * n, "Trans_gear_actual_CAN[]": [4.0] * n, "Eng_speed_CAN": [2000.0] * n,
            "Trans_turbine_shaft_speed_TCM": [2000.0] * n, "HVAC_ACComp_cycling_switch_PCM": [0.0] * n,
            "Eng_ManifoldAir_pressure_sensor_PCM[kPa]": [60.0 + (k // 5 % 2) * 0.1 for k in range(n)],
            "Eng_FuelFlow_Direct2[gps]": [2.0] * n, "Eng_mass_air_flow_PCM[gps]": [29.4] * n,
            "Eng_equiv_ratio_b1_s1_PCM[]": [1.0] * n}
    for k, v in kw.items():
        cols[names.get(k, k)] = list(v)
    return cols


def write_trace(path, columns):
    """A D3-dialect file (tab-delimited, one header row, units in brackets) from {header: values}."""
    names = list(columns)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write("\t".join(names) + "\n")
        for k in range(len(columns[names[0]])):
            fh.write("\t".join(repr(float(columns[c][k])) for c in names) + "\n")
    return path


def synthetic_trace(tmp, *, test, **kw):
    """d3_rows.read_trace of a synthetic CX-9 file written under tmp, read with the CX-9's channels
    (d3_rows.CHANNELS: read_trace names its car, no default; WP3's integration, 23 October 2026, when
    read_trace's `channels` keyword was passed here for the first time), so the Trace is d3_rows' own."""
    import d3_rows
    path = write_trace(os.path.join(tmp, f"{test} Test Data.txt"), synthetic_columns(**kw))
    return d3_rows.read_trace(path, test=test, channels=d3_rows.CHANNELS)


def write_summary_xlsx(path, rows):
    """A minimal workbook (one sheet, shared strings, numbers as numbers) from rows (the first
    the header), readable with zipfile and xml.etree as epa_map.py reads EPA's."""
    strings, index = [], {}

    def ref(r, c):
        s = ""
        c += 1
        while c:
            c, m = divmod(c - 1, 26)
            s = chr(65 + m) + s
        return f"{s}{r}"
    sheet = []
    for r, row in enumerate(rows, start=1):
        cells = []
        for c, v in enumerate(row):
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                cells.append(f'<c r="{ref(r, c)}"><v>{v!r}</v></c>')
            else:
                v = str(v)
                if v not in index:
                    index[v] = len(strings)
                    strings.append(v)
                cells.append(f'<c r="{ref(r, c)}" t="s"><v>{index[v]}</v></c>')
        sheet.append(f'<row r="{r}">{"".join(cells)}</row>')
    ns = 'xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
    rel = 'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"'
    esc = lambda s: s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")  # noqa: E731
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("[Content_Types].xml",
                   '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/'
                   'content-types"><Default Extension="xml" ContentType="application/xml"/></Types>')
        z.writestr("xl/workbook.xml", f'<?xml version="1.0" encoding="UTF-8"?><workbook {ns} {rel}><sheets>'
                                      '<sheet name="Summary" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr("xl/_rels/workbook.xml.rels",
                   '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/'
                   'package/2006/relationships"><Relationship Id="rId1" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr("xl/sharedStrings.xml", f'<?xml version="1.0" encoding="UTF-8"?><sst {ns}>'
                                           + "".join(f"<si><t>{esc(s)}</t></si>" for s in strings) + "</sst>")
        z.writestr("xl/worksheets/sheet1.xml",
                   f'<?xml version="1.0" encoding="UTF-8"?><worksheet {ns}><sheetData>{"".join(sheet)}'
                   '</sheetData></worksheet>')
    return path


# ---------------------------------------------------------------------------- the real-data guard
def _norm(p):
    return os.path.normcase(os.path.abspath(p))


_REAL = {"engines": _norm(common.ENGINE_DIR) + os.sep, "logs": _norm(os.path.join(common.REPO, "logs")) + os.sep,
         "data_folder": _norm(common.DATA_FOLDER) + os.sep,
         "files": {_norm(common.CONTRACT_JSON), _norm(common.CONTRACT_MD),
                   _norm(os.path.join(common.OUT_DIR, "split.json"))}}
_GUARD = {"on": 0, "hits": []}


def _forbidden(path):
    p = _norm(path)
    if p in _REAL["files"] or p.startswith(_REAL["logs"]) or p.startswith(_REAL["data_folder"]):
        return True
    return p.startswith(_REAL["engines"]) and os.path.basename(p).startswith("epa_")


def _hook(event, args):
    if event != "open" or not _GUARD["on"] or not args:
        return
    path = args[0]
    if isinstance(path, bytes):
        path = os.fsdecode(path)
    if not isinstance(path, (str, os.PathLike)):
        return
    if _forbidden(os.fspath(path)):
        _GUARD["hits"].append(os.fspath(path))
        raise PermissionError(f"forbid_real_data: a test opened real data ({os.path.basename(os.fspath(path))})")


_INSTALLED = []


@contextlib.contextmanager
def pinned_terms():
    """While inside, the meter's and the torque's u_D terms carry synthetic values for every row and no D3
    summary column reads as unpinned, so that a synthetic Run 1 or arming gets past the pin checks
    (epa_stats.unpinned_u_d, d3_rows.unpinned_for; WP3's fix of 23 October 2026) and its statistics read a
    u_D: the production terms are pinned per report from each report's Table 8 (decision 56) and have no
    fallback, so a synthetic row, whose test cell is no report's, would refuse them. Synthetic numbers, no
    instrument's: the production tables are untouched, the D3 summary columns stay unpinned in production,
    and each refusal is tested without this (test_calibrate_epa.Order, test_validate_guards.ArmProofs)."""
    from unittest import mock
    import d3_rows
    import epa_stats
    pinned = dict(epa_stats.U_D)
    pinned["meter"] = epa_stats.UD(0.01, None, "random", "synthetic", "test_epa_fixtures.pinned_terms", True)
    pinned["torque"] = epa_stats.UD(0.05, None, "random", "synthetic", "test_epa_fixtures.pinned_terms", True)
    with mock.patch.object(epa_stats, "U_D", pinned), mock.patch.object(d3_rows, "unpinned_for", lambda name: ()):
        yield pinned


@contextlib.contextmanager
def forbid_real_data():
    """While inside, an open of the real data/engines/*/epa_*, logs/**, the real contract, the
    generator's split.json or the team's data folder raises PermissionError inside the open (it
    never happens), and leaving the block fails with AssertionError naming each such open, even
    one the code caught. An audit hook stays for the process; it acts only inside the block."""
    if not _INSTALLED:
        sys.addaudithook(_hook)
        _INSTALLED.append(True)
    _GUARD["on"] += 1
    start = len(_GUARD["hits"])
    try:
        yield
    finally:
        _GUARD["on"] -= 1
        hits = _GUARD["hits"][start:]
        del _GUARD["hits"][start:]
    if hits:
        raise AssertionError(f"forbid_real_data: {len(hits)} open(s) of real data: "
                             + ", ".join(sorted({os.path.basename(h) for h in hits})))


class Guarded(unittest.TestCase):
    """A test class that runs its class setup and every test inside forbid_real_data."""

    @classmethod
    def setUpClass(cls):
        cls.enterClassContext(forbid_real_data())

    def setUp(self):
        self.enterContext(forbid_real_data())


class SyntheticRepoCase(Guarded):
    """Guarded, with one synthetic repository made for the class (cls.base) and a fresh copy of
    it for each test that asks (self.fresh())."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._tmp = tempfile.TemporaryDirectory(prefix="epa_fixture_")
        cls.addClassCleanup(cls._tmp.cleanup)
        cls.base = make_repo(cls._tmp.name)

    def fresh(self):
        tmp = tempfile.mkdtemp(prefix="epa_fixture_", dir=self._tmp.name)
        return copy_repo(self.base, tmp)


# ---------------------------------------------------------------------------- self-test
class SelfTest(SyntheticRepoCase):
    def test_a_synthetic_repository_passes_the_loaders_guards(self):
        src = synthetic_source(self.base)
        chk = epa_rows.check_contract(source=src)
        self.assertEqual(chk.schema, 4)
        self.assertEqual(chk.commit, self.base.contract_commit)
        for eng in epa_rows.TABLES:
            self.assertEqual(epa_rows.check_tables(eng, source=src), epa_rows.TABLES[eng])

    def test_the_designs_give_the_held_out_lines_they_expect(self):
        c = read_contract(self.base)
        for eng, se in DEFAULT_SPECS.items():
            self.assertEqual(tuple(c["engines"][eng]["lines"]), se.lines)
            if se.held_out_lines is not None:
                self.assertEqual(tuple(c["engines"][eng]["held_out_lines"]), se.held_out_lines)
            self.assertGreaterEqual(len(c["engines"][eng]["held_out_lines"]), 1)

    def test_the_contract_records_the_generators_own_split(self):
        _, text = split_of(self.base.root)
        self.assertEqual(read_contract(self.base)["generator_inputs_sha256"]["split.json"],
                         hashlib.sha256(text.encode("utf-8")).hexdigest())

    def test_two_repositories_have_the_same_shas(self):
        with tempfile.TemporaryDirectory(prefix="epa_fixture_") as tmp:
            other = make_repo(tmp)
            self.assertEqual(other.head, self.base.head)

    def test_the_guard_catches_an_open_of_a_real_table(self):
        """The control: inside the block, an open of a real table's path is refused before it
        happens, and leaving the block fails even though the code caught the refusal."""
        spec = epa_rows.TABLES["mazda_25t"][0]
        path = os.path.join(common.ENGINE_DIR, spec.engine, spec.name)
        refused = []
        with self.assertRaises(AssertionError):
            with forbid_real_data():
                try:
                    open(path, "rb").close()
                except PermissionError:
                    refused.append(True)
        self.assertEqual(refused, [True])
        # and a synthetic table's path is not refused
        with forbid_real_data():
            open(table_file(self.base.root, "mazda_25t", "steady", 0), "rb").close()

    def test_the_toy_model_gives_its_hand_answers(self):
        m = ToyModel()
        x = types_ns(rpm=2000.0, map_kpa=100.0, iat_k=300.0, spark_btdc=25.0, lam=0.9,
                     fuel=epa_rows.TableFuel(ftag="s", fuel_report="s", lhv_j_per_kg=42.9e6, afr_st=14.5))
        out = m.cycle(x, dtheta=0.25)
        self.assertEqual(out.air_gps, 0.01 * 100.0 * 2.0 * 1.0)
        self.assertEqual(out.torque_nm, -30.0 + 150.0 + 0.8 * 5.0)
        self.assertAlmostEqual(out.fuel_gps, 2.0 / (14.5 * 0.9), places=15)
        self.assertEqual(m.ecu_at(2000.0, 160.0, 300.0, 360.0).lam, 1.0 - 0.001 * 10.0)

    def test_in_memory_rows_carry_their_populations(self):
        r = point_row(map_kpa=150.0, bmep_bar=10.0, lam_meas=0.9, hot_floor=120.0)
        self.assertTrue(r.pops.hot and r.pops.hot_enr and not r.pops.hot_l1)
        self.assertIs(type(point_row(kind="final")), epa_rows.FinalRow)
        self.assertIs(type(held_out_row()), epa_rows.HeldOutRow)
        with self.assertRaises(AttributeError):
            initial_row().tit_c

    def test_the_summary_workbook_is_readable(self):
        with tempfile.TemporaryDirectory(prefix="epa_fixture_") as tmp:
            p = write_summary_xlsx(os.path.join(tmp, "s.xlsx"), [["test", "fuel_g"], ["a", 1.5]])
            with zipfile.ZipFile(p) as z:
                self.assertIn(b"fuel_g", z.read("xl/sharedStrings.xml"))
                self.assertIn(b"<v>1.5</v>", z.read("xl/worksheets/sheet1.xml"))

    def test_a_synthetic_trace_reads_back_through_d3_rows(self):
        """synthetic_trace writes the CX-9's dialect under d3_rows' pinned names and reads it back with
        d3_rows.read_trace and the CX-9's channels (WP3's integration, 23 October 2026: until then it called
        read_trace without its car and under placeholder names). The control: a column renamed is a header
        that does not resolve, refused before any value is converted."""
        import d3_rows
        with tempfile.TemporaryDirectory(prefix="epa_fixture_") as tmp:
            tr = synthetic_trace(tmp, test="T1")
            self.assertEqual((tr.test, len(tr.t_s)), ("T1", 600))
            self.assertEqual(tr.t_s[1] - tr.t_s[0], 0.1)
            cols = synthetic_columns()
            time_name = d3_names()["time"]
            cols["Time_renamed"] = cols.pop(time_name)
            path = write_trace(os.path.join(tmp, "T2 Test Data.txt"), cols)
            with self.assertRaises(d3_rows.HeaderDefect):
                d3_rows.read_trace(path, test="T2", channels=d3_rows.CHANNELS)

    def test_a_truth_candidate_builds_for_an_epa_engine(self):
        import engines
        b = b58_values()
        p = truth_candidate("mazda_25t", theta={"cycle.burn_base": b["cycle"]["burn_base"] * 1.15})
        self.assertTrue(engines.is_candidate(p))
        self.assertEqual(p.engine.cycle.burn_base, b["cycle"]["burn_base"] * 1.15)


def types_ns(**kw):
    """A plain namespace standing in for epa_stats.RowInputs in the fixture's own self-test."""
    import types
    return types.SimpleNamespace(**kw)


if __name__ == "__main__":
    unittest.main(verbosity=2)
