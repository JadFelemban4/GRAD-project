"""epa_rows.py -- the leak-proof loader of build step 2: an EPA engine's calibration rows, and
nothing of a held-out row, by construction.

    imported, never run. Its callers are calibrate_epa.py (the calibration rows and the
    calibration view of the contract) and validate_epa.py (the held-out counts at the arm step,
    and the held-out rows once ARMED.json is committed); its self-test is test_epa_rows.py.

Build step 2 of decision 24, WP3 (23 October 2026; docs/build_step_2/PLAN.md section 4 as
amendments C1-C9, C12 and C13 of docs/build_step_2/AMENDMENTS.md correct it; the interfaces of
docs/build_step_2/WP3_INTERFACES.md section 5.1). The validation contract
(results/ENGINE_THRESHOLDS.md and .json, version 5, commit c842d74) holds each EPA engine's
held-out rows out of the calibration: "Only the validation sees every column of every held-out
row" (its section 2.3). This module is where that sentence is enforced in code.

WHERE THE HELD-OUT SET COMES FROM (plan 4.1)
  H, the held-out rows, is the set of (table, source_row) pairs of the contract JSON's
  engines.<id>.held_out_rows; L, the held-out lines, is held_out_lines; the lines are
  engines.<id>.lines with merged names split on "/". lambda_ref, the hot MAP floor and the fuels
  are read from the JSON, never recomputed on calibration rows: recomputing them would move the
  populations (the contract's section 3).

THE GUARDS, ALL CHECKED BEFORE A ROW IS READ (plan 4.2)
  1. the contract: its two files equal their blobs at the contract commit, that commit is an
     ancestor of HEAD, and its schema is 4 (CONTRACT_SCHEMA; the plan's 3 was version 3's, and
     version 5 kept version 4's 4);
  2. the generator: every file of generators.sha256 hashes to its value, both the copy in the
     source's root and the module this process imported (split.__file__, common.__file__: the
     code that runs). The populations are split.classify's own (mistake 10);
  3. the tables: each table's raw sha256 equals epa_tables_sha256, and its header equals the
     pinned HEADERS (mistake 13: a new column is a new hypothesis);
  4. epa_engine.json is exposed only through an allowlist (engine_facts); its curves never.

STREAMING (plan 4.3, amendments C9 and wrong claim 15)
  Each table is read with csv.reader, never thresholds.split.load (a dict of every row). Of
  each record source_row is read first: a key in H is counted and skipped -- its other cells
  are tokenised by csv.reader, never converted, yielded or cached. Otherwise the row's line is
  recomputed from its own speed (split.nominal): a speed in no contract line raises KeyError, a
  held-out line SplitViolation. After each table: the held keys seen are that table's share of
  H, the counts are the contract's, the ids are exactly 6..N+5 (epa_map.py writes data from
  spreadsheet row 6), and after the last the High Load Initial and Final calibration ids are
  identical. Any mismatch stops: "a re-derivation must reproduce the counts of section 2.2, or
  stop" (the contract, section 10). Each guard is its own module-level function, so the
  self-test shows each one able to fail with it switched off (mistake 12).

THE ROW TYPES carry no field for a dropped column (DROPPED_COLUMNS). A High Load Initial row
carries its speed and torque only: asking it for a turbine-inlet temperature, a lambda or a
manifold pressure raises AttributeError (the contract, section 2.3: "never their TIT, lambda or
(absent) fuel"). The held-out rows are their own types (HeldOutRow, HeldOutInitialRow), never a
subclass of a calibration type, so a fit that takes exactly SteadyRow or FinalRow refuses them
by type.

THE HELD-OUT READER read_held_out exists for validate_epa.py alone (test_epa_rows.Scans, rule
N2). It refuses, whatever token it is given, unless results/EPA_VALIDATION/<id>/ARMED.json is
committed at HEAD with table, derived-file and code hashes that match the tree (amendment C5).

WHAT THIS MODULE NEVER DOES: it imports no plant module, epa_map or test_epa_map (amendments
C2, C3); it never calls split.load, compute, run or report (C2, C12); it reads no ALPHA curve
(C7) and no epa_channels.csv (whose minima and maxima span every row, plan 4.5); it prints
nothing. No literal table name appears in it: the names come from split.ENG and are checked
against the contract's own keys (amendment C3, the generator's claim).
"""
import copy
import csv
import dataclasses
import hashlib
import io
import json
import math
import os
import subprocess
import types
from dataclasses import dataclass
from typing import Mapping, Optional, Tuple

from thresholds import common, split
from thresholds.split import (FIRED_BMEP, LAM_BAND, LAM_ENR, MAP_BAND, MAP_SPLIT, MIN_CLUSTERS,  # noqa: F401
                              NOMINAL_RPM, OFF_REF, TOL)

# ---------------------------------------------------------------------------- constants
# The contract this calibration is held to: version 5, committed as c842d74 on 23 October 2026 on
# cfe6211, version 4's checkpoint, so it descends from version 4 (a1b88e6) (plan 4.2 guard 1). Its
# schema is the contract's own numbering (the contract, section 13), and version 5 kept version 4's 4
# (its section 14, the JSON's version_5.schema).
CONTRACT_COMMIT = "c842d746ab8d50606dc5a3ae70c24bcc16f5f6c8"
CONTRACT_SCHEMA = 4

# EPA's published spark sentinel: the Mazda's fuel-cut points read exactly -120 (epa_map.py's
# docstring). A row whose Spark Timing cell is exactly that, or empty, is a sentinel row
# (decision 54 and its reading of 23 October 2026, the contract's section 3).
SENTINEL_SPARK = -120.0
ROLES = ("steady", "initial", "final")
# epa_map.FIRST_DATA_ROW: rows 1-3 of a sheet are its title, fuel report and citation, row 4
# the names, row 5 the units; data starts at spreadsheet row 6. Pinned here because no step-2
# module imports epa_map (amendment C3); test_epa_rows.Columns reads epa_map.py's literal.
FIRST_DATA_ROW = 6
# epa_map.KEY_COLUMNS and KEY_COLUMNS_STEADY, pinned the same way: the columns every table
# carries a finite value for on every row (test_epa_map.py's Keys), the meter on steady tables.
KEY_COLUMNS = ("speed_rpm", "torque_nm", "bmep_bar", "intake_manifold_press_kpa_abs", "intake_manifold_temp_c",
               "turbine_inlet_temp_c", "turbine_inlet_press_kpa_abs", "injector_fuel_flow_gps",
               "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c")
KEY_COLUMNS_STEADY = ("fuel_meter_flow_gps",)
# What the loader requires finite on a calibration steady or Final row: the key columns but the
# spark, since an empty Spark Timing cell is a sentinel row, a declared outcome and never a stop
# (decision 54, the reading of 23 October 2026).
REQUIRED_POINT = tuple(c for c in KEY_COLUMNS if c != "spark_timing_cad_btdc")
# An Initial row converts its speed and torque and nothing else (the contract, section 2.3).
REQUIRED_INITIAL = ("speed_rpm", "torque_nm")
PROVENANCE = ("source_file", "source_sheet", "source_row", "test_cell", "fuel_report")

# The tables, by role and position: data, from the generator's own split.ENG (amendment C3: the
# names are never literals in a step-2 .py). The Ford's steady index 0 is Cell 9 and index 1 HD1;
# its high-load holds are HD1's.


@dataclass(frozen=True)
class TableSpec:
    """One table of one engine: its file name as the contract's engines.<id>.tables keys hold
    it, its role (ROLES) and its position among the engine's tables of that role."""
    engine: str
    name: str
    role: str
    index: int


def _tables_from_split():
    out = {}
    for eng, spec in split.ENG.items():
        ts = [TableSpec(eng, fn, "steady", i) for i, fn in enumerate(spec["steady"])]
        ts.append(TableSpec(eng, spec["hli"], "initial", 0))
        ts.append(TableSpec(eng, spec["hlf"], "final", 0))
        out[eng] = tuple(ts)
    return types.MappingProxyType(out)


TABLES = _tables_from_split()

# Each table's header, pinned by (engine, role, index), never by a table name (amendment C3).
# Typed on 23 October 2026 by WP3's implementer from each table's first line, read once before
# commit C (a structural read, entered in calibrate_epa.SEEN_BEFORE_THE_FIT through SEEN below);
# no other line of any table was read to type them. Mistake 13: a column EPA adds or renames is
# a new hypothesis, so the loader stops on any header that is not this one.
_MAZDA_POINT = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "cell_press_kpa_abs", "bsfc_g_per_kwh", "bte_pct", "fuel_meter_flow_gps", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "cac_outlet_press_kpa_abs", "cac_outlet_temp_c", "intake_manifold_press_kpa_abs", "intake_manifold_temp_c",
    "turbine_inlet_press_kpa_abs", "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c",
    "exhaust_lambda", "intake_cam_phase_cad_ret", "exhaust_cam_phase_cad_ret", "valve_overlap_cad",
    "epa_atkinson_ratio")
_MAZDA_INITIAL = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "cell_press_kpa_abs", "bsfc_g_per_kwh", "bte_pct", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "cac_outlet_press_kpa_abs", "cac_outlet_temp_c", "intake_manifold_press_kpa_abs", "intake_manifold_temp_c",
    "turbine_inlet_press_kpa_abs", "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c",
    "exhaust_lambda", "intake_cam_phase_cad_ret", "exhaust_cam_phase_cad_ret", "valve_overlap_cad",
    "epa_atkinson_ratio")
_HONDA_POINT = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "cell_press_kpa_abs", "bsfc_g_per_kwh", "bte_pct", "fuel_meter_flow_gps", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "cac_inlet_press_kpa_abs", "cac_inlet_temp_c", "cac_outlet_press_kpa_abs", "cac_outlet_temp_c",
    "intake_manifold_press_kpa_abs", "intake_manifold_temp_c", "turbine_inlet_press_kpa_abs",
    "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c", "exhaust_lambda",
    "intake_cam_phase_cad_adv", "effective_compression_stroke_mm", "effective_compression_ratio",
    "exhaust_cam_phase_cad_ret", "effective_expansion_stroke_mm", "effective_expansion_ratio", "valve_overlap_cad")
_HONDA_INITIAL = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "cell_press_kpa_abs", "bsfc_g_per_kwh", "bte_pct", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "cac_inlet_press_kpa_abs", "cac_inlet_temp_c", "cac_outlet_press_kpa_abs", "cac_outlet_temp_c",
    "intake_manifold_press_kpa_abs", "intake_manifold_temp_c", "turbine_inlet_press_kpa_abs",
    "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c", "exhaust_lambda",
    "intake_cam_phase_cad_adv", "effective_compression_stroke_mm", "effective_compression_ratio",
    "exhaust_cam_phase_cad_ret", "effective_expansion_stroke_mm", "effective_expansion_ratio", "valve_overlap_cad")
_FORD_CELL9 = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "cell_press_kpa_abs", "bsfc_g_per_kwh", "bte_pct", "fuel_meter_flow_gps", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "intake_manifold_press_kpa_abs", "intake_manifold_temp_c", "turbine_inlet_press_kpa_abs",
    "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c", "exhaust_lambda",
    "intake_cam_phase_cad_ret", "exhaust_cam_phase_cad_ret")
_FORD_HD1_POINT = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "bsfc_g_per_kwh", "bte_pct", "fuel_meter_flow_gps", "injector_fuel_flow_gps",
    "fuel_rail_press_mpa_gauge", "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c",
    "intake_manifold_press_kpa_abs", "intake_manifold_temp_c", "turbine_inlet_press_kpa_abs",
    "turbine_inlet_temp_c", "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c", "exhaust_lambda_left",
    "exhaust_lambda_right")
_FORD_HD1_INITIAL = (
    "source_file", "source_sheet", "source_row", "test_cell", "fuel_report", "speed_rpm", "torque_nm", "bmep_bar",
    "cell_temp_c", "bsfc_g_per_kwh", "bte_pct", "injector_fuel_flow_gps", "fuel_rail_press_mpa_gauge",
    "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c", "intake_manifold_press_kpa_abs",
    "intake_manifold_temp_c", "turbine_inlet_press_kpa_abs", "turbine_inlet_temp_c",
    "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c", "exhaust_lambda_left", "exhaust_lambda_right")
HEADERS = types.MappingProxyType({
    ("mazda_25t", "steady", 0): _MAZDA_POINT, ("mazda_25t", "initial", 0): _MAZDA_INITIAL,
    ("mazda_25t", "final", 0): _MAZDA_POINT,
    ("honda_l15b7", "steady", 0): _HONDA_POINT, ("honda_l15b7", "initial", 0): _HONDA_INITIAL,
    ("honda_l15b7", "final", 0): _HONDA_POINT,
    ("ford_27tt", "steady", 0): _FORD_CELL9, ("ford_27tt", "steady", 1): _FORD_HD1_POINT,
    ("ford_27tt", "initial", 0): _FORD_HD1_INITIAL, ("ford_27tt", "final", 0): _FORD_HD1_POINT,
})

# Every converted column and the field it becomes (the rows' units: rpm, kPa absolute, K for the
# intake, coolant, oil and cell temperatures, degC for the turbine-inlet gas, the unit of
# plant.CycleResult.egt_c it is compared with; WP3_INTERFACES section 2.9).
FIELD_OF_COLUMN = types.MappingProxyType({
    "source_row": "source_row", "test_cell": "test_cell", "fuel_report": "fuel_report",
    "speed_rpm": "speed_rpm", "torque_nm": "torque_nm", "bmep_bar": "bmep_bar",
    "cell_temp_c": "cell_temp_k", "cell_press_kpa_abs": "baro_kpa",
    "fuel_meter_flow_gps": "fuel_meter_gps", "injector_fuel_flow_gps": "injector_fuel_gps",
    "spark_timing_cad_btdc": "spark_btdc", "coolant_temp_c": "ect_k", "oil_sump_temp_c": "oil_k",
    "intake_manifold_press_kpa_abs": "map_kpa", "intake_manifold_temp_c": "imt_k",
    "turbine_inlet_press_kpa_abs": "tip_kpa", "turbine_inlet_temp_c": "tit_c",
    "exhaust_lambda": "lam_meas", "exhaust_lambda_left": "lam_banks", "exhaust_lambda_right": "lam_banks",
    "intake_cam_phase_cad_ret": "cam_cad", "intake_cam_phase_cad_adv": "cam_cad",
    "exhaust_cam_phase_cad_ret": "exhaust_cam_cad", "valve_overlap_cad": "valve_overlap_cad",
    "epa_atkinson_ratio": "atkinson_ratio",
    "effective_compression_stroke_mm": "eff_compression_stroke_mm",
    "effective_compression_ratio": "eff_compression_ratio",
    "effective_expansion_stroke_mm": "eff_expansion_stroke_mm",
    "effective_expansion_ratio": "eff_expansion_ratio",
})
# The columns tokenised and never converted: provenance the rows do not need, BSFC and BTE
# (EPA's calculated ratios, which run into the tens of thousands near zero torque), the rail
# pressure, and the charge-air cooler and catalyst channels no statistic reads.
DROPPED_COLUMNS = frozenset({
    "source_file", "source_sheet", "bsfc_g_per_kwh", "bte_pct", "fuel_rail_press_mpa_gauge",
    "cac_inlet_press_kpa_abs", "cac_inlet_temp_c", "cac_outlet_press_kpa_abs", "cac_outlet_temp_c",
    "catalyst_inlet_press_kpa_abs", "catalyst_inlet_temp_c"})
_INTAKE_CAM = ("intake_cam_phase_cad_ret", "intake_cam_phase_cad_adv")

# A lambda-sensor floor is documented only by a source opened and cited before the fit (the
# contract's section 3, "censored"); none has been opened, so censoring rests on the calibration
# Final rows alone (epa_stats.censoring).
DOCUMENTED_FLOORS = types.MappingProxyType({})

# What this module's author saw before any fit, for calibrate_epa.SEEN_BEFORE_THE_FIT (amendment
# C13). Each entry names what was seen and where, and repeats no value.
SEEN = (
    "WP3's loader author, 23 October 2026: the first line (the header) of each of the ten EPA "
    "tables, read once to pin epa_rows.HEADERS; no other line of any table",
    "WP3's loader author, 23 October 2026: the contract JSON's key paths and value types, its "
    "lines and held_out_lines (C4's allowlist), and the keys, never the values, of one held_out_rows "
    "record, one alpha_nodes_removed record and of engines.mazda_25t.lambda_clip_floor",
    "WP3's loader author, 23 October 2026: the contract MD's section 2.2 (the published table counts, "
    "the held-out lines' structural counts) and section 3 (the lambda_ref values and decision 54's "
    "readings), as written there",
)

_CONTRACT_JSON_REL = os.path.relpath(common.CONTRACT_JSON, common.REPO).replace(os.sep, "/")
_CONTRACT_MD_REL = os.path.relpath(common.CONTRACT_MD, common.REPO).replace(os.sep, "/")
_ENGINE_REL = os.path.relpath(common.ENGINE_DIR, common.REPO)
_K3_REL = "ecu/k3_nominal.json"            # generator_inputs_sha256's key; under common.OUT_DIR
_OUT_REL = os.path.relpath(common.OUT_DIR, common.REPO)
_VALIDATION_REL = "results/EPA_VALIDATION"
# Where calibrate_epa.py's records live (epa_freeze.CALIBRATION_DIR, which this module cannot import: it
# imports the plant; test_epa_freeze pins the two equal): the held-out counts refuse until the
# calibration's freeze and completion are committed (_guard_calibrated).
CALIBRATION_REL = "results/EPA_CALIBRATION"


# ---------------------------------------------------------------------------- exceptions
class LoaderStop(Exception):
    """A count, hash, header or id mismatch: "a re-derivation must reproduce the counts of
    section 2.2, or stop" (the contract, section 10). Its message names the table, row and
    column, never a value."""


class SplitViolation(LoaderStop):
    """A calibration row on a held-out line."""


class NotArmed(Exception):
    """read_held_out called before ARMED.json is committed at HEAD with hashes that match the
    tree, or with a token that is not ARMED.json's (amendment C5)."""


# ---------------------------------------------------------------------------- records
@dataclass(frozen=True)
class Source:
    """Where the tables and the contract live: an explicit source rather than module paths, so
    that every test of the reader runs on a temporary repository (amendment C5) while production
    code names the repository once (Source.repository()).

    allow_poisoned_tables is True only for C8's poison run: the tables under engine_dir are then
    scratch copies whose held-out cells were poisoned, and the table-hash guard is replaced by a
    stronger one -- the repository's own tables (under root) hash to the contract, and the
    copies' calibration records equal theirs, header and raw strings (the manifest); the contract
    may likewise be a scratch copy whose keys this module never reads were garbled (C4), checked
    equal to the committed contract on every key it does read."""
    root: str
    engine_dir: str
    contract_json: str
    contract_md: str
    contract_commit: str
    allow_poisoned_tables: bool

    @classmethod
    def repository(cls):
        """The repository itself: thresholds.common's paths and the contract of version 5."""
        return cls(root=common.REPO, engine_dir=common.ENGINE_DIR, contract_json=common.CONTRACT_JSON,
                   contract_md=common.CONTRACT_MD, contract_commit=CONTRACT_COMMIT, allow_poisoned_tables=False)


_POP_KEYS = ("fired", "fired_meter", "hot", "hot_meter", "hot_l1", "hot_enr", "hot_l1_meter", "l1_boost",
             "l1_thr", "l1_off_ref")


@dataclass(frozen=True)
class Populations:
    """The populations a steady or Final row belongs to: split.classify's own keys, computed by
    split.classify on a minimal dict of the row's raw strings, so the populations are the
    generator's (mistake 10). fired_l1 (E3b's population, "fired lambda~1") is
    classify(row, lambda_ref, -inf, kind)["hot_l1"] and fired: classify has no fired-lambda~1 key,
    and writing its lambda test again would be a second definition."""
    fired: bool
    fired_meter: bool
    hot: bool
    hot_meter: bool
    hot_l1: bool
    hot_enr: bool
    hot_l1_meter: bool
    l1_boost: bool
    l1_thr: bool
    l1_off_ref: bool
    fired_l1: bool


@dataclass(frozen=True)
class PointRow:
    """The fields a steady or High Load Final row carries (plan 4.3, as amendments C1 and C9 and
    decision 54 correct it; WP3_INTERFACES section 5.1). No field exists for a dropped column.

    Units: rpm; kPa absolute; imt_k, ect_k, oil_k and cell_temp_k in K (EPA's degC + 273.15);
    tit_c in degC, the gas-side thermocouple (mistake 23), the unit of the model's egt_c; spark in
    degrees BTDC; flows g/s; torque N m; BMEP bar. spark_btdc is None on a sentinel row; lam_meas
    is None when no lambda was published (on the Ford HD1, when either bank is empty: decision
    54's reading of 23 October 2026). lam_ref is the table's lambda_ref from the contract, never
    recomputed. injector_fuel_gps is EPA's calculated estimate, never a stand-in for the meter
    (mistakes 9, 19). The cam is the intake cam as published, under its channel name (_cad_ret or
    _cad_adv), no sign assumed (mistake 13)."""
    engine: str
    table: str
    source_row: int
    test_cell: str
    fuel_report: str
    origin: str
    line: str
    nominal_rpm: int
    hold: Optional[int]
    speed_rpm: float
    map_kpa: float
    imt_k: float
    ect_k: float
    oil_k: float
    spark_btdc: Optional[float]
    spark_sentinel: bool
    # Which of decision 54's two sentinels a sentinel row is: True for an empty Spark Timing cell,
    # False for EPA's -120 (and on every row that is no sentinel). stage0.json counts the two apart
    # (WP3_INTERFACES section 7.2, checks.spark_sentinel: sentinel_value, empty_cell); added by WP3's
    # integration, 23 October 2026, since spark_sentinel alone cannot tell them apart. Keyword-only
    # with a default, so that a row built in memory (the fixtures, the tests' own rows) need not
    # name it; the loader always sets it from the cell (_point_fields).
    spark_empty: bool = dataclasses.field(default=False, kw_only=True)
    lam_meas: Optional[float]
    lam_banks: Optional[Tuple[Optional[float], Optional[float]]]
    lambda_missing: bool
    lam_ref: float
    torque_nm: float
    bmep_bar: float
    fuel_meter_gps: Optional[float]
    meter_missing: bool
    injector_fuel_gps: float
    tit_c: float
    tip_kpa: float
    baro_kpa: Optional[float]
    cell_temp_k: Optional[float]
    cam_cad: Optional[float]
    cam_channel: Optional[str]
    cam_missing: bool
    exhaust_cam_cad: Optional[float]
    valve_overlap_cad: Optional[float]
    atkinson_ratio: Optional[float]
    eff_compression_stroke_mm: Optional[float]
    eff_expansion_stroke_mm: Optional[float]
    eff_compression_ratio: Optional[float]
    eff_expansion_ratio: Optional[float]
    pops: Populations


@dataclass(frozen=True)
class SteadyRow(PointRow):
    """A calibration steady row."""


@dataclass(frozen=True)
class FinalRow(PointRow):
    """A calibration High Load Final row; hold is its spreadsheet row, shared with its Initial row."""


@dataclass(frozen=True)
class HeldOutRow(PointRow):
    """A held-out steady or Final row (kind "steady" or "final"): read by read_held_out only. Not
    a subclass of SteadyRow or FinalRow, so a fit that takes exactly those refuses it by type."""
    kind: str


@dataclass(frozen=True)
class InitialRow:
    """A calibration High Load Initial row: provenance, its hold, speed and torque, and nothing
    else (plan 4.3; the contract, section 2.3). Its torque serves only amendment C7's descriptive
    full-throttle comparison, labelled transient. It has no TIT, lambda, MAP or fuel field: asking
    for one raises AttributeError."""
    engine: str
    table: str
    source_row: int
    test_cell: str
    line: str
    nominal_rpm: int
    hold: int
    speed_rpm: float
    torque_nm: float
    origin: str
    transient: bool


@dataclass(frozen=True)
class HeldOutInitialRow:
    """A held-out High Load Initial row: InitialRow's fields and the inputs E1i runs it at, with
    its TIT and lambda for the descriptive Initial-to-Final pair estimate (the contract's section 4,
    E1i and E4b). Not a subclass of InitialRow."""
    engine: str
    table: str
    source_row: int
    test_cell: str
    line: str
    nominal_rpm: int
    hold: int
    speed_rpm: float
    torque_nm: float
    origin: str
    transient: bool
    map_kpa: float
    imt_k: float
    ect_k: float
    spark_btdc: Optional[float]
    spark_sentinel: bool
    lam_meas: Optional[float]
    lambda_missing: bool
    bmep_bar: float
    tit_c: float
    tip_kpa: float


@dataclass(frozen=True)
class TableCount:
    name: str
    role: str
    rows: int
    calibration: int
    held_out_skipped: int


@dataclass(frozen=True)
class ManifestTable:
    """One table's calibration records, from raw strings and keys alone: the header's sha256,
    the sorted calibration source rows, and the sha256 of the calibration records' raw cells
    re-serialised by csv.writer (LF) in file order. No value is converted to compute it, so a
    poisoned held-out cell cannot move it."""
    header_sha256: str
    keys: Tuple[int, ...]
    rows_sha256: str


@dataclass(frozen=True)
class Manifest:
    engine: str
    tables: Mapping[str, ManifestTable]
    sha256: str


@dataclass(frozen=True)
class Yield:
    """The calibration rows of one engine (table order, then file order), the per-table counts,
    the manifest, and the sha256 of the canonical JSON of every row (with its type)."""
    engine: str
    rows: tuple
    counts: Tuple[TableCount, ...]
    manifest: Manifest
    sha256: str


@dataclass(frozen=True)
class TableFuel:
    """A table's test fuel (decision 69; the contract's conventions.fuel). lhv_j_per_kg is
    float(repr(lhv_mj_per_kg) + "e6"): the correctly rounded double of the decimal the contract
    prints, the double TOML gives for the spec's 42.908e6; a product by 1e6 can differ by an ulp
    (WP3_INTERFACES section 5.1)."""
    ftag: str
    fuel_report: str
    lhv_j_per_kg: float
    afr_st: float


@dataclass(frozen=True)
class CalibrationView:
    """The calibration's one view of the contract (amendment C4): an allowlist, deep-copied and
    read-only. Never in it: held_out_rows, per_held_out_line, deciding_lines, pooled_counts,
    offsets, eligible, alpha_nodes_removed, the all-row coverage blocks, lambda_clip_floor.where
    (C4, C7). ecu_strategy_b58, perturbations_e6 and k3_seconds join C4's list (B58 measurements
    and rule text only; WP3_INTERFACES section 10, choice 8)."""
    engine: str
    contract_commit: str
    contract_sha_text: str
    lines: Tuple[str, ...]
    held_out_lines: Tuple[str, ...]
    table_counts: Tuple[TableCount, ...]
    lambda_ref: Mapping[str, float]
    hot_map_floor_kpa: float
    fuel_by_table: Mapping[str, TableFuel]
    lam_floor: float
    coverage_calibration_fired: Mapping
    coverage_calibration_hot: Mapping
    conventions: Mapping
    model_form: Mapping
    R: Mapping
    mei_points: float
    r1_housing_k: float
    b_points: float
    propagation_b58: Mapping
    ecu_strategy_b58: Mapping
    perturbations_e6: tuple
    e8_min_rows: int
    k3_seconds: int

    def as_json(self):
        """The view as plain JSON values, for the poison comparison and the view's hash."""
        return _plain(self)

    @property
    def sha256(self):
        return canonical_sha256(self.as_json())


@dataclass(frozen=True)
class EngineFacts:
    """epa_engine.json through its allowlist (plan 4.2 guard 4; amendment C7): the geometry, the
    ALPHA fuel's printout, each table's fuel report and test cell, and the reference-only columns.
    The two ALPHA torque curves, whose measured_at_speed records hold held-out rows' torques, are
    never returned."""
    displacement_l: Optional[float]
    n_cylinders: Optional[int]
    compression_ratio: Optional[float]
    bore_mm: Optional[float]
    stroke_mm: Optional[float]
    geometry_notes: Mapping
    alpha_fuel: Mapping
    table_sources: Mapping
    reference_only_columns: Tuple[str, ...]


@dataclass(frozen=True)
class ContractCheck:
    """What guards 1 and 2 checked. generator_inputs is the contract's generator_inputs_sha256
    (hashes of the generator's step outputs, no EPA value), for test_epa_rows.Structural's
    re-derivation of split.json (plan 4.6 item 2), since no test reads the contract itself (C4)."""
    commit: str
    json_sha_text: str
    md_sha_text: str
    schema: int
    generators: Mapping[str, str]
    generator_inputs: Mapping[str, str]


@dataclass(frozen=True)
class HeldOut:
    engine: str
    rows: tuple
    counts: Mapping[str, int]


@dataclass(frozen=True)
class HeldOutCounts:
    """The held-out counts the contract takes only when the held-out run is armed (its section 3;
    amendment C2): fired held-out rows without lambda and with the sentinel, and the Final rows
    behind E8's two subsets (decision 54's readings). A fired sentinel row is a declared outcome,
    never a stop."""
    fired_lambda_missing: int
    fired_spark_sentinel: int
    final_rows: int
    final_lambda_published: int
    final_spark_published: int
    e8_subsets_enough: bool


# ---------------------------------------------------------------------------- hashing
def _plain(obj):
    """obj as plain JSON values: dataclasses to dicts, mappings to dicts, tuples to lists."""
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return {f.name: _plain(getattr(obj, f.name)) for f in dataclasses.fields(obj)}
    if isinstance(obj, Mapping):
        return {k: _plain(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_plain(v) for v in obj]
    return obj


def canonical_json(obj):
    """The one canonical form for every hash a JSON record carries (WP3_INTERFACES section 4):
    json.dumps with sorted keys and no NaN, UTF-8, the form engines.frozen_sections_sha256 uses."""
    return json.dumps(_plain(obj), sort_keys=True, allow_nan=False).encode("utf-8")


def canonical_sha256(obj):
    return hashlib.sha256(canonical_json(obj)).hexdigest()


def _freeze(obj):
    """A deep, read-only copy: mappings become MappingProxyType, lists tuples."""
    if isinstance(obj, Mapping):
        return types.MappingProxyType({k: _freeze(v) for k, v in obj.items()})
    if isinstance(obj, (list, tuple)):
        return tuple(_freeze(v) for v in obj)
    return copy.deepcopy(obj)


# ---------------------------------------------------------------------------- git and files
def _git(root, *args):
    return subprocess.run(["git", "-C", root, "-c", "core.safecrlf=false", *args], capture_output=True)


def _rel_in(root, path):
    rel = os.path.relpath(os.path.abspath(path), os.path.abspath(root))
    if rel.startswith(".."):
        raise LoaderStop(f"{path} is not inside the source's root")
    return rel.replace(os.sep, "/")


def _same_path(a, b):
    return os.path.normcase(os.path.realpath(a)) == os.path.normcase(os.path.realpath(b))


def _blob_sha256(root, commit, rel):
    """sha256 of a blob at a commit: equal to the working file's sha_text when it is unchanged
    (the blob is LF; core.autocrlf=true, plan 1.1)."""
    r = _git(root, "show", f"{commit}:{rel}")
    if r.returncode != 0:
        return None
    return hashlib.sha256(r.stdout).hexdigest()


def _load_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def table_path(spec, *, source):
    """The file of one table under the source's engine folder."""
    return os.path.join(source.engine_dir, spec.engine, spec.name)


def _repository_table_path(spec, *, source):
    """The file of one table in the source's own work tree (the reference of a poison run)."""
    return os.path.join(source.root, _ENGINE_REL, spec.engine, spec.name)


def _named(engine):
    if not isinstance(engine, str) or engine not in TABLES:
        raise ValueError(f"epa_rows needs an EPA engine's name, one of {sorted(TABLES)}, not {engine!r} "
                         "(mistake 1: no default engine)")


# ---------------------------------------------------------------------------- guards 1 and 2
# Each guard is a module-level function, so test_epa_rows can switch one off and show the
# corruption it catches then passes (mistake 12).
def _guard_contract_blob(source, json_path, md_path):
    """Guard 1: the contract's two files equal their blobs at the contract commit."""
    for path in (json_path, md_path):
        rel = _rel_in(source.root, path)
        want = _blob_sha256(source.root, source.contract_commit, rel)
        if want is None:
            raise LoaderStop(f"{rel} is not in the contract commit {source.contract_commit}")
        if common.sha_text(path) != want:
            raise LoaderStop(f"{rel} differs from its blob at the contract commit {source.contract_commit}")


def _guard_contract_ancestor(source):
    """Guard 1: the contract commit is an ancestor of HEAD."""
    r = _git(source.root, "merge-base", "--is-ancestor", source.contract_commit, "HEAD")
    if r.returncode != 0:
        raise LoaderStop(f"the contract commit {source.contract_commit} is not an ancestor of HEAD")


def _guard_schema(contract):
    """Guard 1: the contract's schema is CONTRACT_SCHEMA, version 4's, which version 5 kept."""
    if contract.get("schema") != CONTRACT_SCHEMA:
        raise LoaderStop(f"the contract's schema is not {CONTRACT_SCHEMA}")


def _imported_generator_files():
    """The generator modules this process runs: the code whose helpers name the populations."""
    return {"thresholds/split.py": split.__file__, "thresholds/common.py": common.__file__}


def _guard_generators(source, contract):
    """Guard 2: every file of generators.sha256 hashes to its value, the root's copy and, for
    split.py and common.py, the module imported (plan 4.2)."""
    gens = contract.get("generators", {}).get("sha256")
    if not isinstance(gens, Mapping) or not gens:
        raise LoaderStop("the contract names no generator files")
    imported = _imported_generator_files()
    for rel, sha in gens.items():
        path = os.path.join(source.root, *rel.split("/"))
        if not os.path.isfile(path) or common.sha_text(path) != sha:
            raise LoaderStop(f"{rel} in the source's root is not the generator the contract records")
        if rel in imported and common.sha_text(imported[rel]) != sha:
            raise LoaderStop(f"the imported {rel} is not the generator the contract records")
    for rel in imported:
        if rel not in gens:
            raise LoaderStop(f"the contract records no hash of {rel}")


# The contract keys this module reads, as paths ("*" any engine): the view's allowlist (C4), the
# loader's inputs (held_out_rows, epa_tables_sha256) and the guards' (schema, generators,
# generator_inputs_sha256). Everything else is never read; garbled_contract garbles it.
_READ_PATHS = (
    ("schema",), ("conventions",), ("model_form",), ("thresholds",), ("mei_points",), ("r1_housing_k",),
    ("budget", "b_points"), ("propagation_b58",), ("ecu_strategy_b58",), ("perturbations_E6",),
    ("generators",), ("generator_inputs_sha256",), ("epa_tables_sha256",),
    ("engines", "*", "lines"), ("engines", "*", "held_out_lines"), ("engines", "*", "tables"),
    ("engines", "*", "hot_map_floor_kpa"), ("engines", "*", "lambda_ref"), ("engines", "*", "held_out_rows"),
    ("engines", "*", "fuel_by_table"), ("engines", "*", "lambda_clip_floor", "floor"),
    ("engines", "*", "coverage", "calibration_fired"), ("engines", "*", "coverage", "calibration_hot"),
    # the team's open list, any entry of which that names Run 1 holds it (run1_wait, which fails closed;
    # WP3's integration, 23 October 2026): rule text, no EPA value
    ("open_for_the_team",),
)


def _is_read(path):
    for rp in _READ_PATHS:
        if len(path) >= len(rp) and all(r == "*" or r == p for r, p in zip(rp, path)):
            return True
    return False


def _read_subset(obj, path=()):
    """The part of a contract this module reads, as a nested dict (None where nothing is read)."""
    if _is_read(path):
        return obj
    if isinstance(obj, Mapping):
        out = {}
        for k, v in obj.items():
            sub = _read_subset(v, path + (k,))
            if sub is not None:
                out[k] = sub
        return out or None
    return None


def _guard_poisoned_contract(contract, reference):
    """Under allow_poisoned_tables: the scratch contract equals the committed one on every key
    this module reads (amendment C4's poison of the keys)."""
    if canonical_sha256(_read_subset(contract)) != canonical_sha256(_read_subset(reference)):
        raise LoaderStop("the scratch contract differs from the committed one on a key the loader reads")


def _verified_contract(source):
    """The contract dict, after guards 1 and 2, and its ContractCheck."""
    own_json = os.path.join(source.root, *_CONTRACT_JSON_REL.split("/"))
    own_md = os.path.join(source.root, *_CONTRACT_MD_REL.split("/"))
    if not source.allow_poisoned_tables and not (_same_path(source.contract_json, own_json)
                                                 and _same_path(source.contract_md, own_md)):
        raise LoaderStop("the contract must be the source root's own (a scratch contract only in a poison run)")
    _guard_contract_blob(source, own_json, own_md)
    _guard_contract_ancestor(source)
    reference = _load_json(own_json)
    contract = reference
    if not _same_path(source.contract_json, own_json):
        contract = _load_json(source.contract_json)
        _guard_poisoned_contract(contract, reference)
    _guard_schema(contract)
    _guard_generators(source, contract)
    check = ContractCheck(commit=source.contract_commit, json_sha_text=common.sha_text(own_json),
                          md_sha_text=common.sha_text(own_md), schema=contract["schema"],
                          generators=types.MappingProxyType(dict(contract["generators"]["sha256"])),
                          generator_inputs=types.MappingProxyType(dict(contract.get("generator_inputs_sha256", {}))))
    return contract, check


def check_contract(*, source):
    """Guards 1 and 2 (plan 4.2): the contract's sha_text equals its blobs at the contract
    commit, that commit is an ancestor of HEAD, its schema is 4, and the generator's files
    (the root's copies and the modules imported) hash to generators.sha256."""
    return _verified_contract(source)[1]


# ---------------------------------------------------------------------------- guard 3
def _engine_block(contract, engine):
    try:
        return contract["engines"][engine]
    except (KeyError, TypeError):
        raise LoaderStop(f"the contract has no engine {engine}") from None


def _guard_table_names(engine, contract):
    """The contract's table keys for the engine equal TABLES[engine]'s names."""
    names = {t.name for t in TABLES[engine]}
    e = _engine_block(contract, engine)
    hashed = {k.split("/", 1)[1] for k in contract.get("epa_tables_sha256", {}) if k.startswith(engine + "/")}
    for what, keys in (("tables", set(e.get("tables", {}))), ("epa_tables_sha256", hashed),
                       ("lambda_ref", set(e.get("lambda_ref", {}))), ("fuel_by_table", set(e.get("fuel_by_table", {})))):
        if keys != names:
            raise LoaderStop(f"{engine}: the contract's {what} keys are not the generator's tables")


def _guard_table_hash(engine, spec, path, contract):
    """Guard 3: the table's raw sha256 equals epa_tables_sha256."""
    if not os.path.isfile(path) or common.sha_raw(path) != contract["epa_tables_sha256"][f"{engine}/{spec.name}"]:
        raise LoaderStop(f"{engine}/{spec.name} is not the table the contract records")


def _guard_header(spec, header):
    """Guard 3: the table's header equals the pinned one (mistake 13)."""
    if tuple(header) != HEADERS[(spec.engine, spec.role, spec.index)]:
        raise LoaderStop(f"{spec.engine}/{spec.name}: its header is not the pinned header")


def _guard_poisoned_table(spec, path, real_path, held):
    """Under allow_poisoned_tables: the scratch copy's calibration records equal the
    repository's own table's, header and raw strings (the manifest), a stronger check than the
    hash a poisoned copy cannot keep."""
    if _manifest_table(spec, path, held) != _manifest_table(spec, real_path, held):
        raise LoaderStop(f"{spec.engine}/{spec.name}: the poisoned copy's calibration records are not the table's")


def check_tables(engine, *, source):
    """Guard 3 for every table of the engine (plan 4.2): the contract's table keys equal
    TABLES[engine]'s names; each table's raw sha256 equals epa_tables_sha256 (or, in a poison
    run, the repository's table does and the copy's calibration records equal it); each header is
    pinned. Returns the engine's TableSpecs."""
    _named(engine)
    contract, _ = _verified_contract(source)
    return _check_tables(engine, contract, source)


def _check_tables(engine, contract, source):
    _guard_table_names(engine, contract)
    held = _held_keys(engine, contract)
    for spec in TABLES[engine]:
        path = table_path(spec, source=source)
        if source.allow_poisoned_tables:
            real = _repository_table_path(spec, source=source)
            _guard_table_hash(engine, spec, real, contract)
            _guard_header(spec, _header_of(real))
            _guard_poisoned_table(spec, path, real, held.get(spec.name, frozenset()))
        else:
            _guard_table_hash(engine, spec, path, contract)
        _guard_header(spec, _header_of(path))
    return TABLES[engine]


def _header_of(path):
    with open(path, newline="", encoding="utf-8") as fh:
        return next(csv.reader(fh), [])


# ---------------------------------------------------------------------------- H and L
def _lines_of(engine, contract):
    """{nominal rpm: line name} from the contract's lines, merged names split on "/"."""
    out = {}
    for ln in _engine_block(contract, engine).get("lines", []):
        for part in str(ln).split("/"):
            out[int(part)] = ln
    return out


def _guard_held_structure(engine, contract):
    """H and L as the contract writes them: every held-out line is a line; every H record names
    one of the engine's tables, a held-out line, a nominal speed in that line and a window that
    is its table's; no key twice. A line removed from L with its rows kept in H stops here."""
    e = _engine_block(contract, engine)
    lines = _lines_of(engine, contract)
    held_lines = list(e.get("held_out_lines", []))
    if not set(held_lines) <= set(lines.values()):
        raise LoaderStop(f"{engine}: a held-out line is not one of the contract's lines")
    window = {"steady": "steady", "initial": "High Load Initial", "final": "High Load Final"}
    role = {t.name: t.role for t in TABLES[engine]}
    seen = set()
    for rec in e.get("held_out_rows", []):
        key = (rec.get("table"), rec.get("source_row"))
        if key[0] not in role or type(key[1]) is not int:
            raise LoaderStop(f"{engine}: a held_out_rows record names no table of the engine or no integer row")
        if key in seen:
            raise LoaderStop(f"{engine}: {key[0]} row {key[1]} is held out twice")
        seen.add(key)
        if rec.get("line") not in held_lines or lines.get(rec.get("nominal_rpm")) != rec.get("line"):
            raise LoaderStop(f"{engine}: {key[0]} row {key[1]} is held out on a line that is not held out")
        if rec.get("window") != window[role[key[0]]]:
            raise LoaderStop(f"{engine}: {key[0]} row {key[1]} is held out in another table's window")


def _held_keys(engine, contract):
    """{table: frozenset of held-out source rows}: H, per table."""
    _guard_held_structure(engine, contract)
    out = {t.name: set() for t in TABLES[engine]}
    for rec in _engine_block(contract, engine)["held_out_rows"]:
        out[rec["table"]].add(rec["source_row"])
    return {k: frozenset(v) for k, v in out.items()}


def _is_held(table, source_row, held):
    """The skip: a key in H is counted and never parsed further."""
    return source_row in held.get(table, frozenset())


# ---------------------------------------------------------------------------- streaming
def _records(spec, path):
    """(source_row, tokens) of every record of a table, in file order, after its header guard.
    source_row is the one cell read before the skip; the rest stay tokens."""
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.reader(fh)
        header = next(reader, [])
        _guard_header(spec, header)
        i_sr = header.index("source_row")
        for k, rec in enumerate(reader, start=1):
            if len(rec) != len(header):
                raise LoaderStop(f"{spec.engine}/{spec.name}: record {k} has not the header's number of cells")
            raw = rec[i_sr]
            if not raw.isdigit():
                raise LoaderStop(f"{spec.engine}/{spec.name}: record {k}'s source_row is not an integer")
            yield int(raw), rec


def _csv_line(tokens):
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(tokens)
    return buf.getvalue().encode("utf-8")


class _ManifestBuilder:
    """One table's manifest, fed the calibration records' tokens in file order."""

    def __init__(self, header):
        self.header_sha256 = hashlib.sha256(_csv_line(header)).hexdigest()
        self.keys = []
        self.h = hashlib.sha256()

    def add(self, source_row, tokens):
        self.keys.append(source_row)
        self.h.update(_csv_line(tokens))

    def done(self):
        return ManifestTable(header_sha256=self.header_sha256, keys=tuple(sorted(self.keys)),
                             rows_sha256=self.h.hexdigest())


def _manifest_table(spec, path, held_rows):
    b = _ManifestBuilder(HEADERS[(spec.engine, spec.role, spec.index)])
    for sr, rec in _records(spec, path):
        if sr in held_rows:
            continue
        b.add(sr, rec)
    return b.done()


def _manifest(engine, tables):
    body = {"engine": engine, "tables": {k: _plain(v) for k, v in tables.items()}}
    return Manifest(engine=engine, tables=types.MappingProxyType(dict(tables)), sha256=canonical_sha256(body))


def _guard_finite(spec, source_row, column, value):
    """A required column that is not finite on a row stops the loader, naming the table, row
    and column, never the value."""
    if value is None or not math.isfinite(value):
        raise LoaderStop(f"{spec.engine}/{spec.name} row {source_row}: {column} is not a finite number")


def _guard_line(spec, source_row, line, held_lines):
    """A calibration row on a held-out line is a SplitViolation."""
    if line in held_lines:
        raise SplitViolation(f"{spec.engine}/{spec.name} row {source_row} is on a held-out line")


def _guard_held_seen(spec, seen, expected):
    """The held keys seen in a table are exactly that table's share of H."""
    if set(seen) != set(expected):
        raise LoaderStop(f"{spec.engine}/{spec.name}: the held-out rows seen are not the table's share of H")


def _guard_counts(spec, rows, held_out, calibration, contract):
    """A table's counts equal the contract's engines.<id>.tables (the contract's section 2.2)."""
    want = _engine_block(contract, spec.engine)["tables"][spec.name]
    if (rows, held_out, calibration) != (want.get("rows"), want.get("held_out"), want.get("calibration")):
        raise LoaderStop(f"{spec.engine}/{spec.name}: the row counts are not the contract's")


def _guard_ids(spec, ids):
    """A table's ids are exactly FIRST_DATA_ROW..N+FIRST_DATA_ROW-1, in file order."""
    if list(ids) != list(range(FIRST_DATA_ROW, FIRST_DATA_ROW + len(ids))):
        raise LoaderStop(f"{spec.engine}/{spec.name}: its source rows are not {FIRST_DATA_ROW}..N+{FIRST_DATA_ROW - 1}")


def _guard_pairs(engine, initial, final):
    """The High Load Initial and Final calibration ids are identical, each pair on one line
    (one hold is one spreadsheet row, epa_map.py; split.py asserts it over every row)."""
    if [(r.source_row, r.line) for r in initial] != [(r.source_row, r.line) for r in final]:
        raise LoaderStop(f"{engine}: the High Load Initial and Final calibration rows are not the same holds")


def _cells(spec, tokens):
    return dict(zip(HEADERS[(spec.engine, spec.role, spec.index)], tokens))


def _number(raw):
    """A cell as a number: None when empty, else split.f's float (NaN for text)."""
    return None if raw is None or raw == "" else split.f(raw)


def _req(spec, sr, cells, column):
    x = _number(cells.get(column))
    _guard_finite(spec, sr, column, x)
    return x


def _opt(spec, sr, cells, column):
    """An optional column: None when absent or empty; a cell that is present must be finite."""
    x = _number(cells.get(column))
    if x is not None:
        _guard_finite(spec, sr, column, x)
    return x


def _line_of(spec, sr, cells, lines):
    """The row's nominal speed and line, from its own speed (split.nominal). A speed in no
    contract line raises KeyError."""
    _req(spec, sr, cells, "speed_rpm")
    try:
        nominal = split.nominal({"speed_rpm": cells["speed_rpm"]})
    except AssertionError:
        raise LoaderStop(f"{spec.engine}/{spec.name} row {sr}: its speed is not within "
                         f"{NOMINAL_RPM / 2.0:g} rpm of a nominal speed") from None
    if nominal not in lines:
        raise KeyError(f"{spec.engine}/{spec.name} row {sr}: its speed is in no line of the contract")
    return nominal, lines[nominal]


def _spark(spec, sr, cells):
    """(spark or None, sentinel): exactly SENTINEL_SPARK or an empty cell is a sentinel row."""
    raw = cells.get("spark_timing_cad_btdc")
    if raw is None or raw == "":
        return None, True
    x = _number(raw)
    _guard_finite(spec, sr, "spark_timing_cad_btdc", x)
    if x == SENTINEL_SPARK:
        return None, True
    return x, False


def _lambda(spec, sr, cells):
    """(lam_meas or None, banks or None): split.lam's own expression on the raw strings, so a
    Ford HD1 row with either bank empty has none (decision 54's reading of 23 October 2026)."""
    if "exhaust_lambda" in cells:
        lam = _opt(spec, sr, cells, "exhaust_lambda")
        return lam, None
    left = _opt(spec, sr, cells, "exhaust_lambda_left")
    right = _opt(spec, sr, cells, "exhaust_lambda_right")
    lam = split.lam({"exhaust_lambda_left": cells["exhaust_lambda_left"],
                     "exhaust_lambda_right": cells["exhaust_lambda_right"]})
    return (lam if split.ok(lam) else None), (left, right)


def populations(cells, lam_ref, floor, kind):
    """split.classify on a minimal dict of the row's raw strings (mistake 10): the one definition of
    a row's populations, for the loader and for T0's synthetic rows (epa_fit.t0_rows, which re-derives
    the populations of a row whose lambda it moved, as a real row's would be). `cells` maps column
    names to their strings, as the table holds them; `kind` is "steady" or "final". Public since WP3's
    integration (23 October 2026): epa_fit called the private name."""
    r = {k: cells[k] for k in ("intake_manifold_press_kpa_abs", "bmep_bar", "fuel_meter_flow_gps", "exhaust_lambda",
                               "exhaust_lambda_left", "exhaust_lambda_right") if k in cells}
    c = split.classify(r, lam_ref, floor, kind)
    any_hot = split.classify(r, lam_ref, -math.inf, kind)
    return Populations(**{k: bool(c[k]) for k in _POP_KEYS}, fired_l1=bool(any_hot["hot_l1"] and c["fired"]))


_populations = populations          # the name the loader and its tests have used


def _spark_empty(cells):
    """Whether a row's Spark Timing cell is empty (decision 54's second sentinel), read from the raw
    string alone."""
    raw = cells.get("spark_timing_cad_btdc")
    return raw is None or raw == ""


def _point_fields(spec, sr, cells, nominal, line, lam_ref, floor, origin):
    """The PointRow fields of a steady or Final row (plan 4.3; WP3_INTERFACES section 5.1)."""
    kind = "final" if spec.role == "final" else "steady"
    for col in REQUIRED_POINT + (KEY_COLUMNS_STEADY if spec.role == "steady" else ()):
        _req(spec, sr, cells, col)
    spark, sentinel = _spark(spec, sr, cells)
    lam, banks = _lambda(spec, sr, cells)
    meter = _opt(spec, sr, cells, "fuel_meter_flow_gps")
    cell_t = _opt(spec, sr, cells, "cell_temp_c")
    cam_col = next((c for c in _INTAKE_CAM if c in cells), None)
    cam = _opt(spec, sr, cells, cam_col) if cam_col else None
    return dict(
        engine=spec.engine, table=spec.name, source_row=sr, test_cell=cells["test_cell"],
        fuel_report=cells["fuel_report"], origin=origin, line=line, nominal_rpm=nominal,
        hold=sr if kind == "final" else None, speed_rpm=_req(spec, sr, cells, "speed_rpm"),
        map_kpa=_req(spec, sr, cells, "intake_manifold_press_kpa_abs"),
        imt_k=_req(spec, sr, cells, "intake_manifold_temp_c") + 273.15,
        ect_k=_req(spec, sr, cells, "coolant_temp_c") + 273.15,
        oil_k=_req(spec, sr, cells, "oil_sump_temp_c") + 273.15,
        spark_btdc=spark, spark_sentinel=sentinel, spark_empty=_spark_empty(cells), lam_meas=lam, lam_banks=banks,
        lambda_missing=lam is None,
        lam_ref=lam_ref, torque_nm=_req(spec, sr, cells, "torque_nm"), bmep_bar=_req(spec, sr, cells, "bmep_bar"),
        fuel_meter_gps=meter, meter_missing=meter is None,
        injector_fuel_gps=_req(spec, sr, cells, "injector_fuel_flow_gps"),
        tit_c=_req(spec, sr, cells, "turbine_inlet_temp_c"),
        tip_kpa=_req(spec, sr, cells, "turbine_inlet_press_kpa_abs"),
        baro_kpa=_opt(spec, sr, cells, "cell_press_kpa_abs"),
        cell_temp_k=None if cell_t is None else cell_t + 273.15,
        cam_cad=cam, cam_channel=cam_col, cam_missing=cam is None,
        exhaust_cam_cad=_opt(spec, sr, cells, "exhaust_cam_phase_cad_ret"),
        valve_overlap_cad=_opt(spec, sr, cells, "valve_overlap_cad"),
        atkinson_ratio=_opt(spec, sr, cells, "epa_atkinson_ratio"),
        eff_compression_stroke_mm=_opt(spec, sr, cells, "effective_compression_stroke_mm"),
        eff_expansion_stroke_mm=_opt(spec, sr, cells, "effective_expansion_stroke_mm"),
        eff_compression_ratio=_opt(spec, sr, cells, "effective_compression_ratio"),
        eff_expansion_ratio=_opt(spec, sr, cells, "effective_expansion_ratio"),
        pops=_populations(cells, lam_ref, floor, kind))


def _initial_fields(spec, sr, cells, nominal, line, origin):
    """An Initial row's speed and torque, and nothing else of it converted."""
    for col in REQUIRED_INITIAL:
        _req(spec, sr, cells, col)
    return dict(engine=spec.engine, table=spec.name, source_row=sr, test_cell=cells["test_cell"], line=line,
                nominal_rpm=nominal, hold=sr, speed_rpm=_req(spec, sr, cells, "speed_rpm"),
                torque_nm=_req(spec, sr, cells, "torque_nm"), origin=origin, transient=True)


def _row_hash(rows):
    return canonical_sha256([{"type": type(r).__name__, **_plain(r)} for r in rows])


class _Pass:
    """One guarded pass over an engine's tables: the calibration rows converted, the per-table
    counts, the manifest, and the calibration rows' raw strings for the coverage (amendment C9)."""

    def __init__(self, engine, source):
        _named(engine)
        contract, self.check = _verified_contract(source)
        specs = _check_tables(engine, contract, source)
        held = _held_keys(engine, contract)
        e = _engine_block(contract, engine)
        lines, held_lines = _lines_of(engine, contract), set(e["held_out_lines"])
        floor = e["hot_map_floor_kpa"]
        self.rows, self.counts, self.raw, tables = [], [], [], {}
        by_role = {"initial": [], "final": []}
        for spec in specs:
            ids, seen, cal = [], [], []
            mb = _ManifestBuilder(HEADERS[(spec.engine, spec.role, spec.index)])
            lam_ref = e["lambda_ref"][spec.name]
            for sr, rec in _records(spec, table_path(spec, source=source)):
                ids.append(sr)
                if _is_held(spec.name, sr, held):
                    seen.append(sr)              # counted and skipped: its cells are never converted
                    continue
                mb.add(sr, rec)
                cells = _cells(spec, rec)
                nominal, line = _line_of(spec, sr, cells, lines)
                _guard_line(spec, sr, line, held_lines)
                if spec.role == "initial":
                    cal.append(InitialRow(**_initial_fields(spec, sr, cells, nominal, line, "epa")))
                    continue
                f = _point_fields(spec, sr, cells, nominal, line, lam_ref, floor, "epa")
                cal.append((FinalRow if spec.role == "final" else SteadyRow)(**f))
                self.raw.append((f["pops"], {k: cells.get(k, "") for k in (
                    "intake_manifold_press_kpa_abs", "speed_rpm", "intake_manifold_temp_c", "coolant_temp_c")}))
            _guard_ids(spec, ids)
            _guard_held_seen(spec, seen, held[spec.name])
            _guard_counts(spec, len(ids), len(seen), len(cal), contract)
            if spec.role in by_role:
                by_role[spec.role] = cal
            self.rows += cal
            self.counts.append(TableCount(name=spec.name, role=spec.role, rows=len(ids), calibration=len(cal),
                                          held_out_skipped=len(seen)))
            tables[spec.name] = mb.done()
        _guard_pairs(engine, by_role["initial"], by_role["final"])
        self.manifest = _manifest(engine, tables)


# ---------------------------------------------------------------------------- the public readers
def calibration_rows(engine, *, source):
    """The engine's calibration rows, after every guard (plan 4.2-4.3; amendments C1, C9): the
    Yield of SteadyRow, FinalRow and InitialRow records, table order then file order."""
    p = _Pass(engine, source)
    return Yield(engine=engine, rows=tuple(p.rows), counts=tuple(p.counts), manifest=p.manifest,
                 sha256=_row_hash(p.rows))


def table_counts_record(yield_):
    """{"tables": {name: {role, rows, calibration, held_out_skipped}}}: a Yield's per-table counts as the
    records write them (stage0.json's yield block, dry-load's run.json; WP3_INTERFACES section 7.2), built
    here because only this module names the tables' key (rule N1; WP3's integration, 23 October 2026)."""
    return {"tables": {c.name: {"role": c.role, "rows": c.rows, "calibration": c.calibration,
                                "held_out_skipped": c.held_out_skipped} for c in yield_.counts}}


def manifest(engine, *, source):
    """Per table, the sorted calibration keys and the sha256 of their raw records (plan 4.3),
    from raw strings and keys alone: no value of any row is converted."""
    _named(engine)
    contract, _ = _verified_contract(source)
    specs = _check_tables(engine, contract, source)
    held = _held_keys(engine, contract)
    return _manifest(engine, {s.name: _manifest_table(s, table_path(s, source=source), held[s.name]) for s in specs})


def calibration_coverage(engine, *, source):
    """split.coverage over the fired and over the hot calibration rows, built from their raw
    degC strings (amendment C9: split.coverage rounds degC to 0.1, the rows hold K), for the
    comparison with the contract's coverage.calibration_fired and calibration_hot (plan 4.6
    item 3: it proves the set, not just its size)."""
    p = _Pass(engine, source)
    return {"calibration_fired": split.coverage([r for pops, r in p.raw if pops.fired]),
            "calibration_hot": split.coverage([r for pops, r in p.raw if pops.hot])}


def calibration_contract(engine, *, source):
    """The calibration's one accessor of the contract (amendment C4): the allowlisted keys,
    deep-copied and read-only (CalibrationView). k3_seconds is the B58's nominal K3 time above
    the knee, results/ENGINE_THRESHOLDS/ecu/k3_nominal.json's time_above_nominal_s, its sha_text
    checked against generator_inputs_sha256 (plan 5.9 item 4)."""
    _named(engine)
    contract, check = _verified_contract(source)
    _guard_table_names(engine, contract)
    e = _engine_block(contract, engine)
    k3_path = os.path.join(source.root, _OUT_REL, *_K3_REL.split("/"))
    want = contract.get("generator_inputs_sha256", {}).get(_K3_REL)
    if not os.path.isfile(k3_path) or common.sha_text(k3_path) != want:
        raise LoaderStop(f"{_K3_REL} is not the file the contract records")
    k3 = _load_json(k3_path)["time_above_nominal_s"]
    role = {t.name: t.role for t in TABLES[engine]}
    counts = tuple(TableCount(name=t.name, role=role[t.name], rows=e["tables"][t.name]["rows"],
                              calibration=e["tables"][t.name]["calibration"],
                              held_out_skipped=e["tables"][t.name]["held_out"]) for t in TABLES[engine])
    fuels = {}
    for t in TABLES[engine]:
        fb = e["fuel_by_table"][t.name]
        fuels[t.name] = TableFuel(ftag=str(fb["ftag"]), fuel_report=str(fb["fuel_report"]),
                                  lhv_j_per_kg=float(repr(float(fb["lhv_mj_per_kg"])) + "e6"),
                                  afr_st=float(fb["afr_st"]))
    R = {t["row"]: (t["R"], t["unit"]) for t in contract["thresholds"] if t.get("engine") == engine}
    return CalibrationView(
        engine=engine, contract_commit=check.commit, contract_sha_text=check.json_sha_text,
        lines=tuple(e["lines"]), held_out_lines=tuple(e["held_out_lines"]), table_counts=counts,
        lambda_ref=_freeze({t.name: float(e["lambda_ref"][t.name]) for t in TABLES[engine]}),
        hot_map_floor_kpa=float(e["hot_map_floor_kpa"]), fuel_by_table=types.MappingProxyType(fuels),
        lam_floor=float(e["lambda_clip_floor"]["floor"]),
        coverage_calibration_fired=_freeze(e["coverage"]["calibration_fired"]),
        coverage_calibration_hot=_freeze(e["coverage"]["calibration_hot"]),
        conventions=_freeze(contract["conventions"]), model_form=_freeze(contract["model_form"]),
        R=_freeze(R), mei_points=float(contract["mei_points"]), r1_housing_k=float(contract["r1_housing_k"]),
        b_points=float(contract["budget"]["b_points"]), propagation_b58=_freeze(contract["propagation_b58"]),
        ecu_strategy_b58=_freeze(contract["ecu_strategy_b58"]), perturbations_e6=_freeze(contract["perturbations_E6"]),
        e8_min_rows=int(contract["conventions"]["statistic_details"]["e8_min_rows"]), k3_seconds=int(k3))


# epa_engine.json's allowlist (plan 4.2 guard 4); the curves never leave engine_facts.
_FACT_KEYS = ("displacement_l", "n_cylinders", "compression_ratio", "bore_mm", "stroke_mm")


def engine_facts(engine, *, source):
    """epa_engine.json's non-curve facts (plan 4.2 guard 4; amendment C7). The tables it names
    must be the generator's."""
    _named(engine)
    j = _load_json(os.path.join(source.engine_dir, engine, "epa_engine.json"))
    tabs = j.get("tables", {})
    if set(tabs) != {t.name for t in TABLES[engine]}:
        raise LoaderStop(f"{engine}: epa_engine.json names other tables than the generator's")
    return EngineFacts(
        **{k: j.get(k) for k in _FACT_KEYS}, geometry_notes=_freeze(j.get("geometry_notes") or {}),
        alpha_fuel=_freeze(j.get("alpha_fuel") or {}),
        table_sources=types.MappingProxyType({n: (tabs[n].get("fuel_report"), tabs[n].get("test_cell"))
                                              for n in sorted(tabs)}),
        reference_only_columns=tuple(j.get("reference_only_columns") or ()))


def _garble(v):
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return -999999 if v != -999999 else 999999
    if isinstance(v, float):
        return -1e6 if v != -1e6 else 1e6
    if isinstance(v, str):
        return "garbled" if v != "garbled" else "GARBLED"
    return "garbled"


def _garbled(obj, path=()):
    if _is_read(path):
        return copy.deepcopy(obj)
    if isinstance(obj, Mapping):
        return {k: _garbled(v, path + (k,)) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_garbled(v, path + ("[]",)) for v in obj]
    return _garble(obj)


def garbled_contract(src_json, dst_json):
    """A copy of a contract with every key this module never reads garbled, the structure kept
    (amendment C4's poison of the keys: the view and the yield must come out byte-identical).
    held_out_rows is the loader's input (it defines H) and is kept, as every key of _READ_PATHS
    is. For calibrate_epa.py poison and the tests."""
    obj = _load_json(src_json)
    os.makedirs(os.path.dirname(os.path.abspath(dst_json)), exist_ok=True)
    with open(dst_json, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(_garbled(obj), indent=1, ensure_ascii=True, allow_nan=False) + "\n")


def garbled_source(source, *, dst_dir):
    """The poison run's garbled-contract Source (amendment C4): garbled_contract of source's contract
    written under dst_dir with the contract's own file name, the tables and the rest of the source as they
    are, allow_poisoned_tables True (its view and yield must come out byte-identical). Here, so that
    calibrate_epa.py names no attribute of a Source that holds the contract's or the tables' path (rule N3
    as widened by WP3's second fix of 23 October 2026)."""
    dst = os.path.join(dst_dir, os.path.basename(source.contract_json))
    garbled_contract(source.contract_json, dst)
    return dataclasses.replace(source, contract_json=dst, allow_poisoned_tables=True)


def tables_moved(poisoned, *, source):
    """Whether the poison run's Source `poisoned` reads its tables from another folder than `source` does:
    the first half of "the copies are not the tables" (calibrate_epa.py poison; the second half is a raw
    sha256 that differs). Here for the same reason as garbled_source."""
    return not _same_path(poisoned.engine_dir, source.engine_dir)


# The two engine files beside the tables that other step-2 modules hash (epa_freeze.data_shas): by name, so
# that no other module joins a path under source.engine_dir itself (rule N3 as widened, 23 October 2026).
ENGINE_FILES = ("epa_engine.json", "epa_channels.csv")


def engine_file_path(engine, basename, *, source):
    """The path of one of ENGINE_FILES of `engine` under the source's tables folder. Opens nothing:
    epa_freeze hashes epa_engine.json raw and takes epa_channels.csv's git blob id without opening it
    (plan 4.5)."""
    _named(engine)
    if basename not in ENGINE_FILES:
        raise ValueError(f"engine_file_path: {basename!r} is not one of {ENGINE_FILES}")
    return os.path.join(source.engine_dir, engine, basename)


# Amendment C8's three poisons: finite extremes far outside any channel's range, chosen without
# reading one (a DESIGN choice, WP3_INTERFACES section 5.5.1), and the empty cell. Text garbage
# would become NaN (split.f) and be filtered by split.ok, hiding a min/max-type leak (C8).
POISONS = types.MappingProxyType({"low": "-1e+06", "high": "1e+06", "blank": ""})


def poisoned_tables(engine, *, source, dst_dir, how):
    """Scratch copies of the engine's tables under dst_dir/<id>/ with every non-provenance cell
    of every held-out row replaced by POISONS[how], written with csv.writer; the calibration
    records and epa_engine.json copied unchanged. Returns the poison run's Source (engine_dir
    dst_dir, allow_poisoned_tables True). The held-out cells are tokenised and overwritten, never
    converted. Here because only this module opens the tables (amendment C3), for
    calibrate_epa.py poison (C8) and the tests. epa_engine.json is copied with every key engine_facts
    never reads garbled (ENGINE_FACT_KEYS_READ kept): its ALPHA curves' measured_at_speed records hold
    held-out rows' torques (amendment C7), so a leak through them would otherwise be invisible to the
    poison; calibrate_epa.py poison requires engine_facts of the copy to equal the original's (WP3's fix of
    23 October 2026)."""
    _named(engine)
    value = POISONS[how]
    contract, _ = _verified_contract(source)
    specs = _check_tables(engine, contract, source)
    held = _held_keys(engine, contract)
    out = os.path.join(dst_dir, engine)
    os.makedirs(out, exist_ok=True)
    for spec in specs:
        header = HEADERS[(spec.engine, spec.role, spec.index)]
        keep = {i for i, c in enumerate(header) if c in PROVENANCE}
        buf = io.StringIO()
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(header)
        for sr, rec in _records(spec, table_path(spec, source=source)):
            if _is_held(spec.name, sr, held):
                rec = [t if i in keep else value for i, t in enumerate(rec)]
            w.writerow(rec)
        with open(os.path.join(out, spec.name), "wb") as fh:
            fh.write(buf.getvalue().encode("utf-8"))
    j = _load_json(os.path.join(source.engine_dir, engine, "epa_engine.json"))
    garbled = {k: (v if k in ENGINE_FACT_KEYS_READ else _garble_all(v)) for k, v in j.items()}
    with open(os.path.join(out, "epa_engine.json"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(garbled, indent=1, ensure_ascii=True, allow_nan=False) + "\n")
    return dataclasses.replace(source, engine_dir=dst_dir, allow_poisoned_tables=True)


# The keys of epa_engine.json engine_facts reads (amendment C7's allowlist); every other key -- the ALPHA
# curves among them -- is garbled in a poison run's copy.
ENGINE_FACT_KEYS_READ = _FACT_KEYS + ("geometry_notes", "alpha_fuel", "tables", "reference_only_columns")


def _garble_all(obj):
    """Every leaf of `obj` garbled, the structure kept (the poison run's copy of epa_engine.json)."""
    if isinstance(obj, Mapping):
        return {k: _garble_all(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_garble_all(v) for v in obj]
    return _garble(obj)


def held_out_keys(engine, *, source):
    """{table: frozenset of held-out source rows}: H's keys, no value, after guards 1-3. For
    test_epa_rows (yielded and H disjoint by keys, plan 4.6 item 1) and the validation alone
    (test_epa_rows.Scans: no calibration module calls it, since H is not in the view, C4)."""
    _named(engine)
    contract, _ = _verified_contract(source)
    _check_tables(engine, contract, source)
    return types.MappingProxyType(_held_keys(engine, contract))


# The contract's rule that holds Run 1 (its open_for_the_team). Version 4's first entry read "The first fit
# (Run 1) waits for both: Jad's column, and Ghassan's own answer to those rows and readings" (its section
# 13, "What is open"); version 5's first entry records Ghassan's order of 23 October that Run 1 go ahead
# before Jad's column is filled (its section 14; the JSON's version_5.go_ahead), and its entries 0 and 3
# name Run 1. run1_wait FAILS CLOSED (WP3's fix of 23 October 2026, on the test review's finding that two
# words opened the gate on any rewording): Run 1 waits while the contract is the commit this loader pins
# (CONTRACT_COMMIT, whose text can no longer change), or while any entry of open_for_the_team names Run 1 at
# all; only a later contract version that names Run 1 nowhere lifts it. Under version 5 the gate therefore
# still holds, and the go-ahead is given as EPA_RUN1_GO naming the engine, which nothing in WP3 sets.
RUN1_RULE_WORD = "Run 1"
RUN1_PINNED_COMMIT = ("the contract is the commit epa_rows pins (CONTRACT_COMMIT), at which the first fit (Run 1) "
                      "waits until EPA_RUN1_GO names the engine, whatever its open_for_the_team says")


def run1_wait(*, source):
    """The contract's rule that Run 1 must wait, as its text, or None when the contract holds no such
    rule (WP3's integration, 23 October 2026; calibrate_epa.py refuses the first evaluation at an EPA row's
    inputs while it stands, unless the environment variable EPA_RUN1_GO names the engine). Read from the
    verified contract (guards 1 and 2): the first entry of open_for_the_team that names Run 1, else
    RUN1_PINNED_COMMIT when the source's contract commit is CONTRACT_COMMIT, else None. Rule text only, no EPA
    value; a synthetic contract that names no Run 1 at another commit holds no rule."""
    contract, _ = _verified_contract(source)
    for entry in contract.get("open_for_the_team") or ():
        if isinstance(entry, str) and RUN1_RULE_WORD in entry:
            return entry
    if source.contract_commit == CONTRACT_COMMIT:
        return RUN1_PINNED_COMMIT
    return None


def audit_paths(engine, *, source):
    """The paths calibrate_epa.py's runtime audit names (WP3_INTERFACES section 3.3, amendment C3), so
    that no other module types the tables' folder or the contract's file (rules N1, N3): each relative
    to source.root with forward slashes where it lies inside it, absolute otherwise. `engines` is the
    folder of every engine's tables, `own` this engine's, `table_files` its tables and `engine_json` its
    epa_engine.json, `channels` every engine's epa_channels.csv (never opened, plan 4.5), `contract`
    the contract's two files, `k3` the one generator output the calibration reads, `outputs` the
    generator's output folder (results/ENGINE_THRESHOLDS/), `validation` results/EPA_VALIDATION/ and
    `data_folder` the team's data folder (thresholds.common.DATA_FOLDER), outside the repository."""
    _named(engine)

    def rel(p):
        a = os.path.abspath(p)
        try:
            r = os.path.relpath(a, os.path.abspath(source.root))
        except ValueError:
            return a.replace(os.sep, "/")
        return a.replace(os.sep, "/") if r == os.pardir or r.startswith(os.pardir + os.sep) else r.replace(os.sep, "/")

    own = os.path.join(source.engine_dir, engine)
    return types.MappingProxyType({
        "engines": rel(source.engine_dir), "own": rel(own),
        "table_files": tuple(rel(table_path(t, source=source)) for t in TABLES[engine]),
        "engine_json": rel(os.path.join(own, "epa_engine.json")),
        "channels": tuple(rel(os.path.join(source.engine_dir, e, "epa_channels.csv")) for e in sorted(TABLES)),
        "contract": (rel(source.contract_json), rel(source.contract_md)),
        "k3": rel(os.path.join(source.root, _OUT_REL, *_K3_REL.split("/"))),
        "outputs": rel(os.path.join(source.root, _OUT_REL)),
        "validation": _VALIDATION_REL,
        "data_folder": os.path.abspath(common.DATA_FOLDER).replace(os.sep, "/"),
    })


# ---------------------------------------------------------------------------- the held-out side
def _guard_calibrated(engine, source):
    """The held-out counts convert held-out cells (BMEP, MAP, the meter, lambda), so they are taken only
    after the calibration is frozen and completed (amendment C2: "taken only when the held-out run is
    armed"): results/EPA_CALIBRATION/<id>/freeze.json and complete.json committed at HEAD and unchanged in
    source.root, or LoaderStop. A runtime precondition beside rule N2's scan, which confines the callers
    (WP3's fix of 23 October 2026: an alias or a getattr passes a scan, never this). Never on poisoned
    tables."""
    if source.allow_poisoned_tables:
        raise LoaderStop("the held-out counts are never taken on poisoned tables")
    for base in ("freeze.json", "complete.json"):
        rel = f"{CALIBRATION_REL}/{engine}/{base}"
        path = os.path.join(source.root, *rel.split("/"))
        committed = (os.path.isfile(path) and _git(source.root, "rev-parse", f"HEAD:{rel}").returncode == 0
                     and common.sha_text(path) == _blob_sha256(source.root, "HEAD", rel))
        if not committed:
            raise LoaderStop(f"{rel} is not committed at HEAD: the held-out counts are taken after the "
                             "calibration's freeze and completion (amendment C2)")


def held_out_counts(engine, *, source):
    """validate_epa.arm's held-out counts (amendment C2; the contract's section 3, "the held-out
    rows' counts of both are taken only when the held-out run is armed"; decision 54): the held-out
    rows are tokenised, and only the BMEP, the lambda cells' presence and the spark cell's
    sentinel test are converted. Called by validate_epa.py alone (test_epa_rows.Scans, rule N2), and
    refused until the calibration is committed (_guard_calibrated)."""
    _named(engine)
    _guard_calibrated(engine, source)
    contract, _ = _verified_contract(source)
    specs = _check_tables(engine, contract, source)
    held = _held_keys(engine, contract)
    n = dict(fired_lambda_missing=0, fired_spark_sentinel=0, final_rows=0, final_lambda_published=0,
             final_spark_published=0)
    for spec in specs:
        if spec.role == "initial":
            continue
        for sr, rec in _records(spec, table_path(spec, source=source)):
            if not _is_held(spec.name, sr, held):
                continue
            cells = _cells(spec, rec)
            fired = _req(spec, sr, cells, "bmep_bar") >= FIRED_BMEP - TOL
            lam_cols = [c for c in ("exhaust_lambda", "exhaust_lambda_left", "exhaust_lambda_right") if c in cells]
            has_lam = all(cells[c] != "" for c in lam_cols)
            raw = cells.get("spark_timing_cad_btdc", "")
            sentinel = raw == "" or split.f(raw) == SENTINEL_SPARK
            n["fired_lambda_missing"] += int(fired and not has_lam)
            n["fired_spark_sentinel"] += int(fired and sentinel)
            if spec.role == "final":
                n["final_rows"] += 1
                n["final_lambda_published"] += int(has_lam)
                n["final_spark_published"] += int(not sentinel)
    k = int(contract["conventions"]["statistic_details"]["e8_min_rows"])
    return HeldOutCounts(**n, e8_subsets_enough=n["final_lambda_published"] >= k and n["final_spark_published"] >= k)


# The population keys the contract's per_held_out_line counts per line over the steady and Final rows
# (thresholds/split.py compute: P[line][key] += classify(...)[key], every key gated off on an Initial row).
POPULATION_COUNT_KEYS = _POP_KEYS


def held_out_population_counts(engine, *, source):
    """{held-out line: {population: rows}} over the held-out steady and Final rows, each row's populations
    as this loader computes them (populations: split.classify on the row's raw strings, at the contract's
    lambda_ref and its printed hot floor), for validate_epa.arm alone (rule N2) to compare with the
    contract's per_held_out_line before the engine is armed. Why (WP3's integration, 23 October 2026, on
    the loader author's finding): the contract prints hot_map_floor_kpa rounded to 0.01 (split.compute's
    round(floor, 2)), while split.compute classified every row at the unrounded floor, so a held-out row
    whose MAP lay between the two would sit in another population here than in the contract; the counts
    show it, and arm stops, before any held-out statistic exists. Counts only: the held-out rows are
    tokenised, and only the cells split.classify reads (MAP, BMEP, the meter, lambda) are converted, as
    held_out_counts converts BMEP (amendment C2: the held-out counts are taken at the arming), and refused
    until the calibration is committed (_guard_calibrated)."""
    _named(engine)
    _guard_calibrated(engine, source)
    contract, _ = _verified_contract(source)
    specs = _check_tables(engine, contract, source)
    held = _held_keys(engine, contract)
    e = _engine_block(contract, engine)
    lines, held_lines = _lines_of(engine, contract), set(e["held_out_lines"])
    out = {line: {k: 0 for k in POPULATION_COUNT_KEYS} for line in e["held_out_lines"]}
    for spec in specs:
        if spec.role == "initial":
            continue
        lam_ref = e["lambda_ref"][spec.name]
        kind = "final" if spec.role == "final" else "steady"
        for sr, rec in _records(spec, table_path(spec, source=source)):
            if not _is_held(spec.name, sr, held):
                continue
            cells = _cells(spec, rec)
            _nominal, line = _line_of(spec, sr, cells, lines)
            if line not in held_lines:
                raise LoaderStop(f"{spec.engine}/{spec.name} row {sr} is held out but not on a held-out line")
            pops = populations(cells, lam_ref, e["hot_map_floor_kpa"], kind)
            for k in POPULATION_COUNT_KEYS:
                out[line][k] += int(getattr(pops, k))
    return types.MappingProxyType({line: types.MappingProxyType(v) for line, v in out.items()})


def _armed_rel(engine):
    return f"{_VALIDATION_REL}/{engine}/ARMED.json"


def _guard_armed(engine, source, token):
    """Amendment C5: whatever token is passed, ARMED.json must be committed at HEAD and
    unchanged, with table, derived-file and code hashes that match the tree; and the token must
    carry this engine, this root, HEAD and ARMED.json's blob at HEAD (checked by its fields, so
    this module needs no import of validate_epa)."""
    if source.allow_poisoned_tables:
        raise NotArmed("the held-out rows are never read from poisoned tables")
    rel = _armed_rel(engine)
    path = os.path.join(source.root, *rel.split("/"))
    head = _git(source.root, "rev-parse", "HEAD")
    blob = _git(source.root, "rev-parse", f"HEAD:{rel}")
    if head.returncode != 0 or blob.returncode != 0 or not os.path.isfile(path):
        raise NotArmed(f"{rel} is not committed at HEAD")
    head, blob = head.stdout.decode().strip(), blob.stdout.decode().strip()
    if common.sha_text(path) != _blob_sha256(source.root, "HEAD", rel):
        raise NotArmed(f"{rel} differs from its blob at HEAD")
    if (getattr(token, "engine", None) != engine or getattr(token, "armed_blob", None) != blob
            or getattr(token, "head", None) != head or not isinstance(getattr(token, "root", None), str)
            or not _same_path(token.root, source.root)):
        raise NotArmed("the token is not this engine's, this tree's and ARMED.json's at HEAD")
    armed = _load_json(path)
    if armed.get("engine") != engine:
        raise NotArmed(f"{rel} arms another engine")
    tables = (armed.get("data") or {}).get("tables_sha256") or {}
    if set(tables) != {t.name for t in TABLES[engine]}:
        raise NotArmed(f"{rel} records other tables than the engine's")
    for spec in TABLES[engine]:
        p = table_path(spec, source=source)
        if not os.path.isfile(p) or common.sha_raw(p) != tables[spec.name]:
            raise NotArmed(f"{engine}/{spec.name} is not the table ARMED.json records")
    derived = armed.get("derived") or {}
    dpath = os.path.join(source.root, *str(derived.get("path", "")).split("/"))
    if not derived.get("path") or not os.path.isfile(dpath) or common.sha_text(dpath) != derived.get("sha_text"):
        raise NotArmed("the derived file is not the one ARMED.json records")
    code = armed.get("code") or {}
    if not code:
        raise NotArmed(f"{rel} records no code")
    for crel, sha in code.items():
        cpath = os.path.join(source.root, *crel.split("/"))
        if not os.path.isfile(cpath) or common.sha_text(cpath) != sha:
            raise NotArmed(f"{crel} is not the code ARMED.json records")


def read_held_out(engine, *, source, token):
    """The held-out rows, for validate_epa.py run alone (test_epa_rows.Scans, rule N2). Refuses,
    whatever token is passed, unless results/EPA_VALIDATION/<id>/ARMED.json is committed at HEAD
    with hashes that match the tree, and unless the token is ARMED.json's (amendment C5). Every
    guard of the calibration reader runs too; each held-out row's line, recomputed from its own
    speed, must be its H record's held-out line."""
    _named(engine)
    _guard_armed(engine, source, token)
    contract, _ = _verified_contract(source)
    specs = _check_tables(engine, contract, source)
    held = _held_keys(engine, contract)
    e = _engine_block(contract, engine)
    lines, held_lines = _lines_of(engine, contract), set(e["held_out_lines"])
    floor = e["hot_map_floor_kpa"]
    rows, counts = [], {}
    pairs = {"initial": [], "final": []}
    for spec in specs:
        ids, mine = [], []
        lam_ref = e["lambda_ref"][spec.name]
        for sr, rec in _records(spec, table_path(spec, source=source)):
            ids.append(sr)
            if not _is_held(spec.name, sr, held):
                continue
            cells = _cells(spec, rec)
            nominal, line = _line_of(spec, sr, cells, lines)
            if line not in held_lines:
                raise LoaderStop(f"{spec.engine}/{spec.name} row {sr} is held out but not on a held-out line")
            if spec.role == "initial":
                f = _initial_fields(spec, sr, cells, nominal, line, "epa")
                for col in REQUIRED_POINT:
                    _req(spec, sr, cells, col)
                spark, sentinel = _spark(spec, sr, cells)
                lam, _banks = _lambda(spec, sr, cells)
                f.update(map_kpa=_req(spec, sr, cells, "intake_manifold_press_kpa_abs"),
                         imt_k=_req(spec, sr, cells, "intake_manifold_temp_c") + 273.15,
                         ect_k=_req(spec, sr, cells, "coolant_temp_c") + 273.15, spark_btdc=spark,
                         spark_sentinel=sentinel, lam_meas=lam, lambda_missing=lam is None,
                         bmep_bar=_req(spec, sr, cells, "bmep_bar"), tit_c=_req(spec, sr, cells, "turbine_inlet_temp_c"),
                         tip_kpa=_req(spec, sr, cells, "turbine_inlet_press_kpa_abs"))
                mine.append(HeldOutInitialRow(**f))
            else:
                f = _point_fields(spec, sr, cells, nominal, line, lam_ref, floor, "epa")
                mine.append(HeldOutRow(**f, kind="final" if spec.role == "final" else "steady"))
        _guard_ids(spec, ids)
        _guard_held_seen(spec, [r.source_row for r in mine], held[spec.name])
        want = e["tables"][spec.name]
        if (len(ids), len(mine)) != (want.get("rows"), want.get("held_out")):
            raise LoaderStop(f"{spec.engine}/{spec.name}: the row counts are not the contract's")
        if spec.role in pairs:
            pairs[spec.role] = mine
        rows += mine
        counts[spec.name] = len(mine)
    _guard_pairs(engine, pairs["initial"], pairs["final"])
    return HeldOut(engine=engine, rows=tuple(rows), counts=types.MappingProxyType(counts))
