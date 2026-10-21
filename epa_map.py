"""epa_map.py -- the EPA engine maps of decision 24, read into tidy tables.

    python epa_map.py                    # about a second: logs/epa/ -> data/engines/<engine>/
    python epa_map.py --check            # rebuild in memory, write nothing, exit 1 if a file differs
    python epa_map.py --stage <folder>   # once: copy the EPA files out of the data folder into logs/epa/

WHAT THIS IS
------------
Decision 24 (results/VALIDATION_DECISIONS.md, section F) makes the H/tau test four engines. Three
of them -- the Mazda 2.5 L turbo, the Honda 1.5 L L15B7 and the Ford 2.7 L twin-turbo V6 -- exist
for this project only as the US EPA's engine benchmarking packages: test-cell workbooks of
averaged operating points, and an ALPHA engine file (.m) built from them. logs/epa/ holds EPA's
files byte for byte (logs/epa/README.md); this script reads them and writes, per engine, into
data/engines/<engine>/:

  epa_steady*.csv            one row per published operating point, every channel the sheet
  epa_highload_initial*.csv  carries, the unit in the column name, and the workbook, sheet and
  epa_highload_final*.csv    spreadsheet row the point came from. The Ford was mapped in two
                             test cells on two fuel batches, so its tables carry _cell9 / _hd1
                             and are never merged here. Initial and Final row r are the same
                             high-load hold (same spreadsheet row; test_epa_map.py checks speeds)
  epa_channels.csv           one row per column of those tables: EPA's own name, unit,
                             description and measurement status, verbatim from the workbook's
                             Test Parameter List, and two flags. `reference_only` = 1 where EPA
                             says "Reference Only": spark, lambda and fuel-rail pressure are
                             uncalibrated sensors or OEM-signal readings (mistake 13). They are
                             FLAGGED, NOT DROPPED -- the calibration needs them and needs to
                             know. `calculated` = 1 where EPA computed the value (BMEP, BSFC,
                             BTE, the injector fuel estimate, cam phasing)
  epa_engine.json            displacement, cylinders and compression ratio from the ALPHA .m;
                             bore and stroke where the package states them, else null with the
                             reason; the full-throttle and closed-throttle torque curves, every
                             node marked measured or not against the sheets EPA built them
                             from (mistake 6: EPA built the curves' edges from published
                             figures, not from its own measurements); EPA's fuel properties;
                             every table's source

Everything under data/engines/ is generated: never edit it by hand (CLAUDE.md, conventions); run
this again. test_epa_map.py checks that a rebuild reproduces it byte for byte.

The workbooks are read with the standard library (zipfile + xml.etree). openpyxl is not
installed in the project's environment and is not to be installed for this.

WHAT IT DOES NOT DO
-------------------
It fits nothing and calibrates nothing (calibrate_epa.py, a later step of the four-engine
build). It changes no value: an empty cell stays empty, and EPA's sentinels stay as published
-- the Mazda's spark reads -120 on its fuel-cut points, and BSFC runs into the tens of
thousands of g/kWh near zero torque (a division by almost nothing). Filter them where they are
used, in the open. `Turbine Inlet Temp` is a gas-side sensor at the turbine inlet, not the
housing metal the plant protects (mistake 23).

Added 20 October 2026, build step 1 of decision 24 (the data, before any calibration).
"""
import argparse
import csv
import datetime
import hashlib
import html
import io
import json
import math
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
EPA_DIR = os.path.join(HERE, "logs", "epa")
OUT_DIR = os.path.join(HERE, "data", "engines")

# --------------------------------------------------------------------------- the engines
# Which file is which, per engine. Every name is EPA's own, as it sits in the package zip.
# `cell` is the test cell the workbook's points were taken in: the Mazda's and the Honda's from
# their test reports ("performed in National Center for Advanced Technology (NCAT) Test Cell 9"
# / "... Test Cell 7"), the Ford's from the workbooks' own titles ("Tier 2 Fuel Cell 9", "Tier 2
# Fuel HD1"). test_epa_map.py checks each label against that text.
ENGINES = {
    "mazda_25t": dict(
        alpha_m="7- engine_2016_Mazda_Skyactiv_Turbo_2L5_Tier2.m",
        alpha_html="3- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - ALPHA Generation Process.html",
        workbooks=[dict(file="4- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Data.xlsx",
                        cell="Test Cell 9",
                        report="3a- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Report.docx",
                        tables={"Steady State": "epa_steady.csv",
                                "High Load Initial": "epa_highload_initial.csv",
                                "High Load Final": "epa_highload_final.csv"})]),
    "honda_l15b7": dict(
        alpha_m="7- engine_2016_Honda_L15B7_1L5_Tier2.m",
        alpha_html="3- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - ALPHA Generation Process.html",
        workbooks=[dict(file="4- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Data.xlsx",
                        cell="Test Cell 7",
                        report="3a- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Report.docx",
                        tables={"Steady State": "epa_steady.csv",
                                "High Load Initial": "epa_highload_initial.csv",
                                "High Load Final": "epa_highload_final.csv"})]),
    "ford_27tt": dict(
        alpha_m="7- engine_2015_Ford_EcoBoost_2L7_Tier2.m",
        alpha_html="3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel - ALPHA Generation Process.html",
        workbooks=[dict(file="4- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test Data.xlsx",
                        cell="Test Cell 9",
                        report="3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test Report.docx",
                        tables={"Steady State": "epa_steady_cell9.csv"}),
                   dict(file="4- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Data.xlsx",
                        cell="Test Cell HD1",
                        report="3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Report.docx",
                        tables={"Steady State": "epa_steady_hd1.csv",
                                "High Load Initial": "epa_highload_initial_hd1.csv",
                                "High Load Final": "epa_highload_final_hd1.csv"})]),
}

# What --stage copies into logs/epa/<engine>/: (package folder in the data folder, member of that
# package's zip, role). The Tier 2 test data and ALPHA map packages only; Tier 3, LEV III and the
# plots stay in the data folder. The fuel analysis reports and the ALPHA generation documents are
# copied too: the first carry the fuel each map ran on (the air flow the calibration needs is
# fuel x stoichiometric ratio x lambda), the second say which points of EPA's curves were not
# measured, and they hold the bore of the Mazda and the Honda (`epa_engine.json`).
_PKG = "epa-ncat-benchmarking"
STAGE = {
    "mazda_25t": [
        ("mazda-2.5t-2016_tier2-test-data", "4- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Data.xlsx",
         "test data workbook"),
        ("mazda-2.5t-2016_tier2-test-data",
         "3a- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Report.docx", "test report"),
        ("mazda-2.5t-2016_tier2-test-data", "6- NVFEL Fuel Analysis Report 26864.pdf", "fuel analysis report"),
        ("mazda-2.5t-2016_tier2-alpha-map", "7- engine_2016_Mazda_Skyactiv_Turbo_2L5_Tier2.m", "ALPHA engine file"),
        ("mazda-2.5t-2016_tier2-alpha-map",
         "3- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - ALPHA Generation Process.html",
         "ALPHA generation process"),
    ],
    "honda_l15b7": [
        ("honda-l15b7-2016_tier2-test-data", "4- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Data.xlsx",
         "test data workbook"),
        ("honda-l15b7-2016_tier2-test-data", "3a- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Report.docx",
         "test report"),
        ("honda-l15b7-2016_tier2-test-data", "6- NVFEL Fuel Analysis Report 25842.pdf", "fuel analysis report"),
        ("honda-l15b7-2016_tier2-alpha-map", "7- engine_2016_Honda_L15B7_1L5_Tier2.m", "ALPHA engine file"),
        ("honda-l15b7-2016_tier2-alpha-map",
         "3- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - ALPHA Generation Process.html", "ALPHA generation process"),
    ],
    "ford_27tt": [
        ("ford-2.7tt-2015_tier2-cell9-test-data",
         "4- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test Data.xlsx", "test data workbook"),
        ("ford-2.7tt-2015_tier2-cell9-test-data",
         "3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test Report.docx", "test report"),
        ("ford-2.7tt-2015_tier2-cell9-test-data", "6- NVFEL Fuel Analysis Report 25278.pdf", "fuel analysis report"),
        ("ford-2.7tt-2015_tier2-hd1-test-data",
         "4- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Data.xlsx", "test data workbook"),
        ("ford-2.7tt-2015_tier2-hd1-test-data",
         "3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Report.docx", "test report"),
        ("ford-2.7tt-2015_tier2-hd1-test-data", "6- NVFEL Fuel Analysis Report 26864.pdf", "fuel analysis report"),
        ("ford-2.7tt-2015_tier2-alpha-map", "7- engine_2015_Ford_EcoBoost_2L7_Tier2.m", "ALPHA engine file"),
        ("ford-2.7tt-2015_tier2-alpha-map",
         "3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel - ALPHA Generation Process.html",
         "ALPHA generation process"),
    ],
}
# Size limits for --stage, from the task that created logs/epa (20 October 2026): no file over
# 50 MB, a test report only if it is under 10 MB, the whole folder about 60 MB at most.
MAX_FILE_BYTES = 50 * 1024 * 1024
MAX_REPORT_BYTES = 10 * 1024 * 1024
MAX_TOTAL_BYTES = 60 * 1024 * 1024

# The downloads fetch_engine_data.py re-fetches: every download row of the data folder's
# MANIFEST.csv in these folders. Not listed: epa-pasteur (an older copy of the Honda packages,
# identical data, CATALOGUE.md 1.4) and anl-d3-documentation (Argonne's method slides): nothing
# in the repository reads them.
SOURCE_GROUPS = ("anl-d3-2016-mazda-cx9", "anl-d3-2018-honda-accord-lx", "epa-ncat-benchmarking",
                 "epa-test-car-list")
# Two Test Car List files that engine_specs/cars/a90_supra_2020.toml cites and the data folder
# does not hold (it stops at model year 2020). The vehicles strand of 20 October 2026 downloaded
# them (scratchpad fe/vehicles/dl_epa/); bytes and sha256 are of that copy.
EXTRA_SOURCES = [
    dict(url="https://www.epa.gov/system/files/documents/2022-04/21-tstcar-2022-04-15.xlsx",
         rel_path="epa-test-car-list/MY2021/21-tstcar-2022-04-15.xlsx", bytes=1568801,
         sha256="f7441de1be356d946fdb8578cb7641f9c899c35940bd6a8b767d97e7b06664a5",
         group="epa-test-car-list",
         note="not in the data folder of 20 Oct 2026; hash of the vehicles strand's download"),
    dict(url="https://www.epa.gov/system/files/documents/2024-05/23-testcar-2024-05-17_0.xlsx",
         rel_path="epa-test-car-list/MY2023/23-testcar-2024-05-17_0.xlsx", bytes=1216302,
         sha256="985fc3090c1e913168ab8147b9173735e25b7bc5b086ea4df60dd659de9c030e",
         group="epa-test-car-list",
         note="not in the data folder of 20 Oct 2026; hash of the vehicles strand's download"),
]

# --------------------------------------------------------------------------- the channels
# (EPA channel name, EPA unit as printed in row 5 of the sheet) -> column name. A pair not listed
# here stops the build: a new name or a new unit is a new hypothesis about what was measured
# (mistake 13), not a column to guess a name for. Units: _c degC, _kpa_abs kPaA (absolute),
# _mpa_gauge MPaG, _gps g/s, _cad crank-angle degrees; lambda and the ratios are dimensionless.
CHANNELS = {
    ("Speed", "rpm"): "speed_rpm",
    ("Torque", "Nm"): "torque_nm",
    ("BMEP", "bar"): "bmep_bar",
    ("Cell Temp", "degC"): "cell_temp_c",
    ("Cell Press", "kPaA"): "cell_press_kpa_abs",
    ("BSFC", "g/kW-hr"): "bsfc_g_per_kwh",
    ("BTE", "%"): "bte_pct",
    ("Fuel Meter Flow", "g/s"): "fuel_meter_flow_gps",
    ("Injector Fuel Flow", "g/s"): "injector_fuel_flow_gps",
    ("Fuel Rail Press", "MPaG"): "fuel_rail_press_mpa_gauge",
    ("Spark Timing", "CAD BTDC"): "spark_timing_cad_btdc",
    ("Coolant Temp", "degC"): "coolant_temp_c",
    ("Oil Sump Temp", "degC"): "oil_sump_temp_c",
    ("CAC Inlet Press", "kPaA"): "cac_inlet_press_kpa_abs",
    ("CAC Inlet Temp", "degC"): "cac_inlet_temp_c",
    ("CAC Outlet Press", "kPaA"): "cac_outlet_press_kpa_abs",
    ("CAC Outlet Temp", "degC"): "cac_outlet_temp_c",
    ("Intake Manifold Press", "kPaA"): "intake_manifold_press_kpa_abs",
    ("Intake Manifold Temp", "degC"): "intake_manifold_temp_c",
    ("Turbine Inlet Press", "kPaA"): "turbine_inlet_press_kpa_abs",
    ("Turbine Inlet Temp", "degC"): "turbine_inlet_temp_c",
    ("Catalyst Inlet Press", "kPaA"): "catalyst_inlet_press_kpa_abs",
    ("Catalyst Inlet Temp", "degC"): "catalyst_inlet_temp_c",
    ("Exhaust Lambda", "LAMBDA"): "exhaust_lambda",
    ("Exhaust Lambda", "---"): "exhaust_lambda",
    ("Exhaust Lambda Left", "LAMBDA"): "exhaust_lambda_left",
    ("Exhaust Lambda Right", "LAMBDA"): "exhaust_lambda_right",
    ("Intake Cam Phase", "CAD RET"): "intake_cam_phase_cad_ret",
    ("Intake Cam Phase", "CAD ADV"): "intake_cam_phase_cad_adv",
    ("Exhaust Cam Phase", "CAD RET"): "exhaust_cam_phase_cad_ret",
    ("Valve Overlap", "CAD"): "valve_overlap_cad",
    ("EPA Atkinson Ratio", "---"): "epa_atkinson_ratio",
    # The Honda's "Compression Ratio" is EPA's estimate of the EFFECTIVE ratio from intake-valve
    # closing (Test Parameter List), not the geometric 10.6 of the .m -- hence the name.
    ("Compression Stroke Length", "mm"): "effective_compression_stroke_mm",
    ("Compression Ratio", "---"): "effective_compression_ratio",
    ("Expansion Stroke Length", "mm"): "effective_expansion_stroke_mm",
    ("Expansion Ratio", "---"): "effective_expansion_ratio",
}
# Columns every table must carry a finite value for on every row (test_epa_map.py checks it):
# the operating point, the boost, the exhaust temperature and pressure the turbine node is
# calibrated against, the fuel, and the warm-up state.
KEY_COLUMNS = ("speed_rpm", "torque_nm", "bmep_bar", "intake_manifold_press_kpa_abs", "intake_manifold_temp_c",
               "turbine_inlet_temp_c", "turbine_inlet_press_kpa_abs", "injector_fuel_flow_gps",
               "spark_timing_cad_btdc", "coolant_temp_c", "oil_sump_temp_c")
KEY_COLUMNS_STEADY = ("fuel_meter_flow_gps",)       # High Load Initial publishes no meter value
PROVENANCE = ("source_file", "source_sheet", "source_row", "test_cell", "fuel_report")
FIRST_DATA_ROW = 6                                   # rows 1-3 title, fuel report, citation; 4 names; 5 units
NEAR_RPM = 30.0      # ASSUMED: a curve node and a measured point are "at the same speed" within this.
                     # Wider than the 17 rpm between the two windows of one high-load hold (Ford HD1,
                     # the widest), narrower than the ~100 rpm between EPA's nearest set speeds (Honda)

# --------------------------------------------------------------------------- reading xlsx
_SS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
_REL = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def _col(ref):
    """'AB12' -> 27: the 0-based column of a cell reference."""
    n = 0
    for ch in ref:
        if not ch.isalpha():
            break
        n = n * 26 + ord(ch.upper()) - 64
    return n - 1


def read_xlsx(path):
    """Every sheet of a workbook: {sheet name: {row number: {column: (text, type)}}}.

    The standard library's zip and XML readers are enough for what EPA publishes: values and
    shared strings, no formulas. The type is Excel's own ('n' number, 's' shared string,
    'inlineStr', 'str' formula text, 'b', 'e' error), so a caller refuses what it does not
    expect instead of guessing what it meant (mistake 9). Also reads the Test Car Lists."""
    with zipfile.ZipFile(path) as z:
        strings = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).iter(_SS + "si"):
                # the text of a plain string or of every run of a rich one; a phonetic
                # guide (rPh) is not part of the value
                parts = [t.text or "" for t in si.findall(_SS + "t")]
                for run in si.findall(_SS + "r"):
                    parts += [t.text or "" for t in run.findall(_SS + "t")]
                strings.append("".join(parts))
        book = ET.fromstring(z.read("xl/workbook.xml"))
        rels = {r.get("Id"): r.get("Target") for r in ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))}
        out = {}
        for sheet in book.find(_SS + "sheets"):
            target = rels[sheet.get(_REL)]
            part = target.lstrip("/") if target.startswith("/") else "xl/" + target
            rows = {}
            for row in ET.fromstring(z.read(part)).find(_SS + "sheetData").findall(_SS + "row"):
                cells = {}
                for c in row.findall(_SS + "c"):
                    kind = c.get("t", "n")
                    if kind == "inlineStr":
                        text = "".join(t.text or "" for t in c.iter(_SS + "t"))
                    else:
                        v = c.find(_SS + "v")
                        if v is None:
                            continue
                        if kind == "s" and not 0 <= int(v.text) < len(strings):
                            raise SystemExit(f"{path}: cell {c.get('r')} names shared string {v.text} of {len(strings)}")
                        text = strings[int(v.text)] if kind == "s" else (v.text or "")
                    cells[_col(c.get("r"))] = (text, kind)
                rows[int(row.get("r"))] = cells
            out[sheet.get("name")] = rows
    return out


def _text(cells, col):
    return cells.get(col, ("", ""))[0].strip()


def _num(text, where):
    """A cell's number as the tables write it: repr of the double, the shortest text that reads
    back as the same value, so no digit is invented or lost and a rebuild is byte for byte."""
    x = float(text)
    if not math.isfinite(x):
        raise ValueError(f"{where}: non-finite value {text!r}")
    return repr(x)


def _excel_date(serial):
    """Excel's 1900 date system: day 1 is 1900-01-01, counted through its phantom 29 Feb 1900."""
    return (datetime.date(1899, 12, 30) + datetime.timedelta(days=int(float(serial)))).isoformat()


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# --------------------------------------------------------------------------- one sheet
def parameter_list(book, where):
    """The workbook's Test Parameter List: {EPA channel name: dict(unit, description, status)},
    and EPA's own definitions of the statuses where the sheet carries them (its footnote)."""
    rows = book["Test Parameter List"]
    head = [_text(rows[4], c) for c in sorted(rows[4])]
    if head[:3] != ["Name", "Units", "Description"]:
        raise SystemExit(f"{where}: Test Parameter List row 4 reads {head!r}; expected Name, Units, Description")
    out, definitions = {}, {}
    for n in sorted(rows):
        if n <= 4:
            continue
        name = _text(rows[n], 0)
        if name.startswith("*"):
            # "* Measurement Type & Status Descriptions:" then one "status - definition" a line
            for line in name.splitlines()[1:]:
                if " \u2013 " in line:
                    status, meaning = line.rsplit(" \u2013 ", 1)
                    definitions[status.strip()] = meaning.strip()
            continue
        if name:
            out[name] = dict(unit=_text(rows[n], 1), description=_text(rows[n], 2), status=_text(rows[n], 3))
    return out, definitions


def sheet_table(book, file_name, sheet, cell, params):
    """One sheet as (columns, rows, meta). Refuses anything the layout does not explain."""
    where = f"{file_name} / {sheet}"
    rows = book[sheet]
    title, fuel_line, citation = _text(rows[1], 0), _text(rows[2], 0), _text(rows[3], 0)
    m = re.fullmatch(r"NVFEL Fuel Analysis Report (\d+)", fuel_line)
    if not m:
        raise SystemExit(f"{where}: row 2 reads {fuel_line!r}; expected 'NVFEL Fuel Analysis Report <n>'")
    fuel = m.group(1)
    version = [t for c, (t, k) in sorted(rows[2].items()) if c > 0 and k == "n"]
    head, units = rows[4], rows[5]
    cols = sorted(head)
    channels, names = [], []
    for c in cols:
        key = (_text(head, c), _text(units, c))
        if key not in CHANNELS:
            raise SystemExit(f"{where}: channel {key[0]!r} in {key[1]!r} is not in epa_map.CHANNELS. "
                             "Name it there, from EPA's Test Parameter List, before it is read.")
        if key[0] not in params:
            raise SystemExit(f"{where}: channel {key[0]!r} is not in the workbook's Test Parameter List")
        if params[key[0]]["unit"] != key[1]:
            raise SystemExit(f"{where}: {key[0]!r} is in {key[1]!r} on the sheet and "
                             f"{params[key[0]]['unit']!r} in the Test Parameter List")
        channels.append(CHANNELS[key])
        names.append(key[0])
    if len(set(channels)) != len(channels):
        raise SystemExit(f"{where}: two EPA channels map to one column: {channels}")
    out = []
    numbers = sorted(r for r in rows if r >= FIRST_DATA_ROW)
    gaps = sorted(set(range(FIRST_DATA_ROW, numbers[-1] + 1)) - set(numbers)) if numbers else ["all"]
    if gaps:
        raise SystemExit(f"{where}: rows {gaps[:5]} are missing inside the data")
    for n in numbers:
        cells = rows[n]
        if not cells:
            raise SystemExit(f"{where}: row {n} is empty inside the data")
        stray = sorted(set(cells) - set(cols))
        if stray:
            raise SystemExit(f"{where}: row {n} has values in columns with no channel name: {stray}")
        values = []
        for c in cols:
            if c not in cells:
                values.append("")
                continue
            text, kind = cells[c]
            if kind != "n":
                raise SystemExit(f"{where}: row {n}, {names[cols.index(c)]!r} holds {text!r} (cell type {kind})")
            values.append(_num(text, f"{where} row {n}"))
        if values[channels.index("speed_rpm")] == "":
            raise SystemExit(f"{where}: row {n} has no Speed")
        out.append([file_name, sheet, str(n), cell, fuel] + values)
    meta = dict(title=title, fuel_report=fuel, citation=citation.replace("SUGGESTED CITATION:", "").strip(),
                version_serial=int(float(version[0])) if version else None,
                version_date=_excel_date(version[0]) if version else None)
    return list(PROVENANCE) + channels, names, out, meta


def csv_bytes(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


# --------------------------------------------------------------------------- the ALPHA files
def parse_alpha_m(path):
    """The scalars and the four torque-curve vectors of an ALPHA engine definition (.m)."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    scalars = {k: float(v) for k, v in re.findall(r"^engine\.(\w+)\s*=\s*([-+0-9.eE]+)\s*;", text, re.M)}
    vectors = {k: [float(x) for x in re.split(r"[;\s]+", body) if x]
               for k, body in re.findall(r"^engine\.(\w+)\s*=\s*\[(.*?)\]\s*;", text, re.M | re.S)}
    name = re.search(r"^engine\.name\s*=\s*'([^']*)'", text, re.M)
    made = re.search(r"^% Generated (.+?)\s*$", text, re.M)
    cite = re.search(r"^% SUGGESTED CITATION:\s*\n%\s*(.+?)\s*$", text, re.M)
    fuel = re.search(r"class_REVS_fuel\('([^']*)'\)", text)
    need_s = ("displacement_L", "num_cylinders", "compression_ratio")
    need_v = ("full_throttle_speed_radps", "full_throttle_torque_Nm",
              "closed_throttle_speed_radps", "closed_throttle_torque_Nm")
    missing = [k for k in need_s if k not in scalars] + [k for k in need_v if k not in vectors]
    if missing or not (name and made and cite and fuel):
        raise SystemExit(f"{path}: the ALPHA file lacks {missing or 'its name, date, citation or fuel tag'}")
    for a, b in (need_v[0:2], need_v[2:4]):
        if len(vectors[a]) != len(vectors[b]):
            raise SystemExit(f"{path}: {a} has {len(vectors[a])} values and {b} {len(vectors[b])}")
    return dict(scalars=scalars, vectors=vectors, name=name.group(1), generated=made.group(1),
                citation=cite.group(1), fuel_tag=fuel.group(1))


def html_lines(path):
    """The visible text of an ALPHA generation document, one non-empty line a list item."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        raw = fh.read()
    raw = re.sub(r"<script.*?</script>|<style.*?</style>", " ", raw, flags=re.S | re.I)
    raw = re.sub(r"<(br|p|div|tr|li|h\d)\b[^>]*>", "\n", raw, flags=re.I)
    text = html.unescape(re.sub(r"<[^>]+>", " ", raw))
    return [s for s in (re.sub(r"[ \t\r\xa0]+", " ", line).strip() for line in text.split("\n")) if s]


_ASSIGN = re.compile(r"^(%\s*)?(engine|enigne)\.(bore_mm|stroke_mm)\s*=\s*([0-9.]+)\s*;")


def geometry_from(alpha, lines, html_name, m_name):
    """Bore and stroke where the package states them: the .m first, then an executed line of
    EPA's generation script. Never anything else -- no handbook, no Wikipedia (task of 20 Oct)."""
    found, commented = {}, {}
    for line in lines:
        m = _ASSIGN.match(line)
        if not m:
            continue
        key, value = m.group(3), float(m.group(4))
        if m.group(1):
            commented.setdefault(key, (value, line))
        else:
            found.setdefault(key, (value, line, m.group(2)))
    out, notes = {}, {}
    for key in ("bore_mm", "stroke_mm"):
        if key in alpha["scalars"]:
            out[key] = alpha["scalars"][key]
            notes[key] = f"the ALPHA engine file ({m_name}): engine.{key}"
        elif key in found:
            value, line, var = found[key]
            out[key] = value
            notes[key] = (f"EPA's generation script ({html_name}): {line!r}"
                          + (" -- misspelt 'enigne', so the assignment never reached the engine and the .m "
                             "file has no " + key if var == "enigne" else ""))
        else:
            out[key] = None
            notes[key] = "not stated by the package" + (
                f"; its generation script carries the line {commented[key][1]!r}, commented out, so EPA "
                "does not assert it" if key in commented else "") + (
                "; a value from a handbook or Wikipedia is not typed here (task of 20 October 2026)")
        if key in commented:
            out[key + "_commented_out"] = commented[key][0]
    source = next((l for l in lines if l.startswith("Set physical characteristics")), None)
    return out, notes, source


def alpha_fuel(lines):
    """EPA's printout of the ALPHA fuel ('class_REVS_fuel with properties:' then 'key: value')."""
    try:
        i = lines.index("class_REVS_fuel with properties:")
    except ValueError:
        return None
    out = {}
    for line in lines[i + 1:]:
        m = re.fullmatch(r"(\w+): (.+)", line)
        if not m:
            break
        v = m.group(2).strip()
        try:
            out[m.group(1)] = float(v)
        except ValueError:
            out[m.group(1)] = v.strip("'")
    return out


def alpha_inputs(lines):
    """(workbook, sheet) pairs EPA's generation script reads, in order: its readtable2 calls."""
    found = re.findall(r"readtable2\(\s*'([^']+)'\s*,\s*'Sheet'\s*,\s*'([^']+)'", "\n".join(lines))
    return list(dict.fromkeys(found))


def _at_speed(rpm, tables, pick):
    """The measured point at a curve node's speed: within NEAR_RPM, the extreme torque."""
    best = None
    for name, header, rows in tables:
        i_s, i_t, i_r = header.index("speed_rpm"), header.index("torque_nm"), header.index("source_row")
        for r in rows:
            if abs(float(r[i_s]) - rpm) <= NEAR_RPM:
                cand = dict(table=name, source_row=int(r[i_r]), speed_rpm=float(r[i_s]), torque_nm=float(r[i_t]))
                if best is None or pick(cand["torque_nm"], best["torque_nm"]):
                    best = cand
    return best


def _is_measured(rpm, torque, tables):
    """True when a node IS a measured point: the same torque (to 1e-6 Nm, EPA copied the number)
    at a measured speed within NEAR_RPM."""
    for _name, header, rows in tables:
        i_s, i_t = header.index("speed_rpm"), header.index("torque_nm")
        if any(abs(float(r[i_s]) - rpm) <= NEAR_RPM and abs(float(r[i_t]) - torque) <= 1e-6 for r in rows):
            return True
    return False


def curve(speed_radps, torque_nm, tables, pick, note):
    rpm = [w * 30.0 / math.pi for w in speed_radps]
    return dict(speed_radps=speed_radps, speed_rpm=rpm, torque_nm=torque_nm,
                node_is_measured=[n > 0 and _is_measured(n, t, tables) for n, t in zip(rpm, torque_nm)],
                measured_at_speed=[_at_speed(n, tables, pick) if n > 0 else None for n in rpm], note=note)


# --------------------------------------------------------------------------- one engine
def build_engine(engine_id):
    """Every generated file of one engine, as {path relative to data/engines/: bytes}."""
    spec = ENGINES[engine_id]
    src = os.path.join(EPA_DIR, engine_id)
    files, dictionary, tables, built, sheet_of = {}, [], {}, {}, {}
    ref_only, status_defs = set(), {}
    for wb in spec["workbooks"]:
        path = os.path.join(src, wb["file"])
        book = read_xlsx(path)
        params, defs = parameter_list(book, wb["file"])
        status_defs.update(defs)
        for sheet, out_name in wb["tables"].items():
            header, names, rows, meta = sheet_table(book, wb["file"], sheet, wb["cell"], params)
            files[out_name] = csv_bytes(header, rows)
            for j, col in enumerate(header[len(PROVENANCE):]):
                k = len(PROVENANCE) + j
                vals = [float(r[k]) for r in rows if r[k] != ""]
                p = params[names[j]]
                flag_ref = int(p["status"].lower().startswith("reference only"))
                if flag_ref:
                    ref_only.add(col)
                dictionary.append([out_name, col, names[j], p["unit"], p["description"], p["status"], flag_ref,
                                   int(p["status"].lower().startswith("calculated")), len(vals),
                                   len(rows) - len(vals), repr(min(vals)) if vals else "",
                                   repr(max(vals)) if vals else ""])
            tables[out_name] = dict(workbook=f"logs/epa/{engine_id}/{wb['file']}", workbook_sha256=sha256(path),
                                    sheet=sheet, rows=len(rows), test_cell=wb["cell"], **meta)
            built[out_name] = (out_name, header, rows)
            sheet_of[(wb["file"], sheet)] = out_name
    files["epa_channels.csv"] = csv_bytes(
        ["table", "column", "epa_channel", "epa_unit", "epa_description", "epa_status", "reference_only",
         "calculated", "n_values", "n_empty", "min", "max"], dictionary)

    m_path, h_path = os.path.join(src, spec["alpha_m"]), os.path.join(src, spec["alpha_html"])
    alpha = parse_alpha_m(m_path)
    lines = html_lines(h_path)
    geom, geom_notes, geom_source = geometry_from(alpha, lines, spec["alpha_html"], spec["alpha_m"])
    s, v = alpha["scalars"], alpha["vectors"]
    out = dict(
        _generated="by epa_map.py from logs/epa/ -- never edit by hand; run `python epa_map.py`",
        engine_id=engine_id, engine_name=alpha["name"],
        alpha=dict(file=f"logs/epa/{engine_id}/{spec['alpha_m']}", sha256=sha256(m_path),
                   generated=alpha["generated"], citation=alpha["citation"], fuel_tag=alpha["fuel_tag"],
                   process_document=f"logs/epa/{engine_id}/{spec['alpha_html']}", process_sha256=sha256(h_path)),
        displacement_l=s["displacement_L"], n_cylinders=int(s["num_cylinders"]),
        compression_ratio=s["compression_ratio"],
        **geom,
        geometry_notes=dict(geom_notes, epa_source=geom_source, compression_ratio="geometric, from the .m" + (
            "; the workbook's 'Compression Ratio' channel (effective_compression_ratio) is EPA's estimate of "
            "the EFFECTIVE ratio from intake-valve closing, another quantity"
            if any("effective_compression_ratio" in t[1] for t in built.values()) else "")),
    )
    if geom["bore_mm"] is not None and geom["stroke_mm"] is not None:
        # a consistency figure, not a constant: test_epa_map.py holds it to displacement_l
        out["displacement_from_bore_stroke_l"] = (out["n_cylinders"] * math.pi / 4.0 * geom["bore_mm"] ** 2
                                                  * geom["stroke_mm"] / 1e6)
    # The sheets EPA built its curves from, as its own generation script reads them (readtable2).
    inputs = alpha_inputs(lines)
    out["alpha"]["inputs"] = [dict(workbook=f, sheet=sh, table=sheet_of.get((f, sh))) for f, sh in inputs]
    used = [built[sheet_of[k]] for k in inputs if k in sheet_of]
    if not used:
        raise SystemExit(f"{spec['alpha_html']}: names no input sheet that this script tabulates")
    out["wot_torque_curve"] = curve(
        v["full_throttle_speed_radps"], v["full_throttle_torque_Nm"], used, lambda a, b: a > b,
        "ALPHA full-throttle curve. node_is_measured: the node is a point EPA measured, in the sheets it "
        "built the curve from (alpha.inputs). Where it is false the node is EPA's addition, named in its "
        f"generation document: model rather than data (mistake 6). measured_at_speed: the highest torque "
        f"measured within {NEAR_RPM:g} rpm of the node, or null where EPA measured none")
    out["closed_throttle_torque_curve"] = curve(
        v["closed_throttle_speed_radps"], v["closed_throttle_torque_Nm"], used, lambda a, b: a < b,
        "ALPHA closed-throttle (motoring) curve. node_is_measured as above; measured_at_speed: the lowest "
        f"torque measured within {NEAR_RPM:g} rpm of the node, or null where EPA measured none")
    out["alpha_fuel"] = alpha_fuel(lines)
    out["tables"] = tables
    out["reference_only_columns"] = sorted(ref_only)
    out["status_definitions"] = status_defs
    files["epa_engine.json"] = (json.dumps(out, indent=1, ensure_ascii=True, allow_nan=False) + "\n").encode("ascii")
    return files


# The attributes that keep the generated files byte for byte through git on Windows: this
# machine's git has core.autocrlf=true, which would otherwise rewrite every line ending on
# commit or checkout and break test_epa_map.py's byte-for-byte rebuild.
GITATTRIBUTES = b"# written by epa_map.py: store and check out these files exactly as generated\n* -text\n"


def build_all():
    """{path relative to data/engines/: bytes} for every engine."""
    out = {".gitattributes": GITATTRIBUTES}
    for engine_id in ENGINES:
        for name, data in build_engine(engine_id).items():
            out[f"{engine_id}/{name}"] = data
    return out


def changed(files):
    """The generated files whose bytes on disk differ from `files` (or are missing)."""
    bad = []
    for rel, data in files.items():
        p = os.path.join(OUT_DIR, rel)
        if not os.path.exists(p):
            bad.append((rel, "missing"))
            continue
        with open(p, "rb") as fh:
            if fh.read() != data:
                bad.append((rel, "differs"))
    return bad


def report(files):
    for rel in sorted(files):
        if rel.endswith(".csv") and "/epa_" in rel and not rel.endswith("epa_channels.csv"):
            n = files[rel].count(b"\n") - 1
            print(f"  {rel:<44} {n:>4} rows")
    for engine_id in ENGINES:
        j = json.loads(files[f"{engine_id}/epa_engine.json"])
        bore = "null" if j["bore_mm"] is None else f"{j['bore_mm']:g} mm"
        stroke = "null" if j["stroke_mm"] is None else f"{j['stroke_mm']:g} mm"
        print(f"  {engine_id:<12} {j['displacement_l']:g} L, {j['n_cylinders']} cyl, CR {j['compression_ratio']:g}, "
              f"bore {bore}, stroke {stroke}; reference-only: {', '.join(j['reference_only_columns'])}")


# --------------------------------------------------------------------------- staging
def _rel(path, root):
    return os.path.relpath(path, root).replace("\\", "/")


def stage(folder):
    """Copy the files in STAGE out of the data folder into logs/epa/, verified, once.

    Each source must be listed in the data folder's MANIFEST.csv and hash to its sha256 there;
    each copy must hash the same. A file already in logs/epa/ with other bytes is never
    overwritten: logs/epa/ holds measurements (CLAUDE.md, conventions)."""
    folder = os.path.abspath(folder)
    with open(os.path.join(folder, "MANIFEST.csv"), encoding="utf-8", newline="") as fh:
        manifest = list(csv.DictReader(fh))
    by_path = {_rel(r["local_path"], folder): r for r in manifest}
    plan = []
    for engine_id, items in STAGE.items():
        for package, member, role in items:
            rel = f"{_PKG}/{package}/unzipped/{member}"
            row = by_path.get(rel)
            if row is None:
                raise SystemExit(f"{rel}: not in {folder}/MANIFEST.csv")
            m = re.fullmatch(r"zip-member: (\S+) :: (.+)", row["url"])
            if not m or m.group(2) != member:
                raise SystemExit(f"{rel}: the manifest's url {row['url']!r} does not name this member")
            plan.append(dict(engine_id=engine_id, role=role, member=member, src=os.path.join(folder, rel),
                             rel=rel, url=m.group(1), bytes=int(row["bytes"]), sha256=row["sha256"]))
    keep, total = [], 0
    for p in sorted(plan, key=lambda p: p["bytes"]):
        limit = MAX_REPORT_BYTES if p["role"] == "test report" else MAX_FILE_BYTES
        if p["bytes"] >= limit or total + p["bytes"] > MAX_TOTAL_BYTES:
            print(f"  LEFT OUT  {p['rel']}  ({p['bytes']:,} bytes: over the size rule)")
            continue
        keep.append(p)
        total += p["bytes"]
    rows = []
    for p in sorted(keep, key=lambda p: (list(STAGE).index(p["engine_id"]), p["member"])):
        got = sha256(p["src"])
        if got != p["sha256"] or os.path.getsize(p["src"]) != p["bytes"]:
            raise SystemExit(f"{p['rel']}: does not match the data folder's own manifest -- stop")
        dst = os.path.join(EPA_DIR, p["engine_id"], p["member"])
        if os.path.exists(dst):
            if sha256(dst) != p["sha256"]:
                raise SystemExit(f"{_rel(dst, HERE)} exists with other bytes. logs/epa/ is never overwritten.")
            print(f"  same      {_rel(dst, HERE)}")
        else:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(p["src"], dst)
            if sha256(dst) != p["sha256"]:
                os.remove(dst)
                raise SystemExit(f"{_rel(dst, HERE)}: the copy does not hash like its source -- removed")
            print(f"  copied    {_rel(dst, HERE)}  ({p['bytes']:,} bytes)")
        rows.append([p["url"], p["member"], _rel(dst, HERE), p["bytes"], p["sha256"], p["rel"], p["engine_id"],
                     p["role"]])
    with open(os.path.join(EPA_DIR, ".gitattributes"), "wb") as fh:
        fh.write(GITATTRIBUTES.replace(b"epa_map.py", b"epa_map.py --stage"))
    with open(os.path.join(EPA_DIR, "MANIFEST.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["url", "zip_member", "repo_path", "bytes", "sha256", "data_folder_path", "engine_id", "role"])
        w.writerows(rows)
    sources = []
    for r in manifest:
        rel = _rel(r["local_path"], folder)
        if r["kind"] == "download" and rel.split("/")[0] in SOURCE_GROUPS:
            sources.append([r["url"], rel, r["bytes"], r["sha256"], rel.split("/")[0], r["note"]])
    for x in EXTRA_SOURCES:
        sources.append([x["url"], x["rel_path"], x["bytes"], x["sha256"], x["group"], x["note"]])
    with open(os.path.join(EPA_DIR, "D3_AND_EPA_SOURCES.csv"), "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["url", "rel_path", "bytes", "sha256", "group", "note"])
        w.writerows(sources)
    print(f"  logs/epa: {len(rows)} files, {sum(r[3] for r in rows):,} bytes; MANIFEST.csv written; "
          f"D3_AND_EPA_SOURCES.csv: {len(sources)} downloads")


# --------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--check", action="store_true", help="rebuild in memory; exit 1 if a file on disk differs")
    ap.add_argument("--stage", metavar="FOLDER", help="copy the EPA files out of this data folder into logs/epa/")
    a = ap.parse_args()
    if a.stage:
        stage(a.stage)
        return
    files = build_all()
    if a.check:
        bad = changed(files)
        for rel, why in bad:
            print(f"  {why:<8} data/engines/{rel}")
        print("  data/engines/ is as epa_map.py builds it" if not bad else
              f"  {len(bad)} file(s) differ from a rebuild: run `python epa_map.py`")
        sys.exit(1 if bad else 0)
    for rel, _why in changed(files):
        p = os.path.join(OUT_DIR, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "wb") as fh:
            fh.write(files[rel])
    report(files)
    print(f"  wrote data/engines/ ({len(files)} files)")


if __name__ == "__main__":
    main()
