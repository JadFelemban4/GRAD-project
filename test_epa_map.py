"""test_epa_map.py -- the EPA engine data of decision 24 hold to what epa_map.py claims.

    python test_epa_map.py        # a few seconds; exit code 0 when all pass

Each check below fails when its claim stops holding, and ChecksCanFail runs every one of them
on a corrupted copy and requires it to catch the corruption (mistake 12: a check that cannot
fail is not a check). Nothing here writes a file.

  Inputs      every file in logs/epa/<engine>/ is in logs/epa/MANIFEST.csv with its size and
              sha256, and nothing else is there; each sha256 equals the data folder's own
              MANIFEST.csv when the folder is on this machine (GRAD_ENGINE_DATA, else
              C:\\Users\\badcl\\Desktop\\GRAD-engine-data); no file over 50 MB, no test report over
              10 MB, the folder under 60 MB
  Counts      the row counts of the data folder's catalogue: Mazda 210/61/61, Honda 190/65/65,
              Ford Cell 9 180, HD1 76 + 19/19
  Units       every column's unit suffix is the unit EPA prints for its channel
  Ranges      speed 500-6500 rpm; torque from -60 Nm to 1 % over the ALPHA full-throttle
              maximum; turbine-inlet gas 150-950 C; lambda 0.5-1.6. EPA's BMEP column follows
              from its torque and a displacement within 0.3 % of the ALPHA file's
  Keys        no empty or non-finite value in epa_map.KEY_COLUMNS
  Pairs       High Load Initial row r and Final row r are one hold: the same spreadsheet row,
              speeds within 25 rpm, torques within 10 %
  Regenerate  a rebuild reproduces every file epa_map.py writes under data/engines/ byte for
              byte, and no stale epa_* file is left beside them
  Engine      bore, stroke and displacement agree where the package states all three; a null
              says why; every test-cell label is in its workbook's title or its test report
  CarSpecs    engine_specs/cars/*.toml have the form engine_specs/cars/README.md describes,
              every value a status and a source that resolves, and every EPA row equals the
              Test Car List file it cites (files missing from the data folder are looked for
              by name in GRAD_EXTRA_DATA, hashed against D3_AND_EPA_SOURCES.csv first); the
              Supra's [repo_current] equals the plant engines.get("b58") builds (added 21
              October 2026: it pointed at engine_env.py's lines after build step 1 had moved
              the values, and nothing compared the copy with the plant)

Added 20 October 2026 with epa_map.py, build step 1 of decision 24.
"""
import copy
import csv
import functools
import glob
import io
import json
import math
import os
import re
import sys
import tomllib
import unittest
import xml.etree.ElementTree as ET
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import epa_map as E  # noqa: E402

EPA = os.path.join(HERE, "logs", "epa")
CARS = os.path.join(HERE, "engine_specs", "cars")
DATA_FOLDER = os.environ.get("GRAD_ENGINE_DATA", r"C:\Users\badcl\Desktop\GRAD-engine-data")
EXTRA_FOLDERS = [p for p in os.environ.get("GRAD_EXTRA_DATA", "").split(os.pathsep) if p]

# The data folder's CATALOGUE.md, section 1.1 (rows per Tier 2 sheet), as the task of
# 20 October 2026 quoted it: Mazda 210/61/61, Honda 190/65/65, Ford Cell 9 180, HD1 76 + 19 pairs.
EXPECTED_ROWS = {
    "mazda_25t/epa_steady.csv": 210, "mazda_25t/epa_highload_initial.csv": 61,
    "mazda_25t/epa_highload_final.csv": 61,
    "honda_l15b7/epa_steady.csv": 190, "honda_l15b7/epa_highload_initial.csv": 65,
    "honda_l15b7/epa_highload_final.csv": 65,
    "ford_27tt/epa_steady_cell9.csv": 180, "ford_27tt/epa_steady_hd1.csv": 76,
    "ford_27tt/epa_highload_initial_hd1.csv": 19, "ford_27tt/epa_highload_final_hd1.csv": 19,
}
# Physical bounds, not fitted to these data: idle to the highest redline of the three engines;
# a motoring floor and the engine's own published maximum; turbine-inlet GAS temperatures a
# running gasoline engine produces (the hottest Tier 2 point is the Mazda's 900.8 C, CATALOGUE.md
# 1.2); lambda from deep enrichment to lean idle.
RPM_RANGE = (500.0, 6500.0)
TORQUE_FLOOR_NM = -60.0
WOT_MARGIN = 1.01
TIT_RANGE_C = (150.0, 950.0)
LAMBDA_RANGE = (0.5, 1.6)
# Measured on the tables of 20 October 2026, before these tolerances were written: EPA's BMEP
# implies 2.488 L for the Mazda (the ALPHA file's), 1.495 L for the Honda (0.067 % under 1.496)
# and 2.700 L for the Ford (0.223 % over 2.694); Initial/Final pairs agree within 17.0 rpm and
# 8.0 % of torque (Ford HD1, Honda), and a one-row shift breaks 25 of 60, 11 of 64 and 6 of 18
# pairs at the bounds below.
BMEP_DISPLACEMENT_TOL = 0.003
PAIR_RPM, PAIR_TORQUE = 25.0, 0.10
SUFFIX_UNITS = (("_rpm", "rpm"), ("_nm", "Nm"), ("_bar", "bar"), ("_c", "degC"), ("_kpa_abs", "kPaA"),
                ("_g_per_kwh", "g/kW-hr"), ("_pct", "%"), ("_gps", "g/s"), ("_mpa_gauge", "MPaG"),
                ("_cad_btdc", "CAD BTDC"), ("_cad_ret", "CAD RET"), ("_cad_adv", "CAD ADV"), ("_cad", "CAD"),
                ("_mm", "mm"), ("_ratio", "---"), ("lambda", "LAMBDA"), ("lambda", "---"),
                ("lambda_left", "LAMBDA"), ("lambda_right", "LAMBDA"))


def read_csv(path_or_bytes):
    if isinstance(path_or_bytes, bytes):
        return list(csv.DictReader(io.StringIO(path_or_bytes.decode("utf-8"))))
    with open(path_or_bytes, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def tables():
    """{'engine/table.csv': rows} for every data table on disk."""
    out = {}
    for engine_id, spec in E.ENGINES.items():
        for wb in spec["workbooks"]:
            for name in wb["tables"].values():
                out[f"{engine_id}/{name}"] = read_csv(os.path.join(E.OUT_DIR, engine_id, name))
    return out


def engine_json(engine_id):
    with open(os.path.join(E.OUT_DIR, engine_id, "epa_engine.json"), encoding="ascii") as fh:
        return json.load(fh)


# --------------------------------------------------------------------------- the checks
def manifest_problems(rows):
    bad = []
    for r in rows:
        p = os.path.join(HERE, r["repo_path"])
        if not os.path.exists(p):
            bad.append(f"{r['repo_path']}: missing")
        elif os.path.getsize(p) != int(r["bytes"]) or E.sha256(p) != r["sha256"]:
            bad.append(f"{r['repo_path']}: size or sha256 differs from MANIFEST.csv")
    return bad


def unit_problems(dictionary):
    bad = []
    for r in dictionary:
        col, unit = r["column"], r["epa_unit"]
        if not any(col.endswith(s) and unit == u for s, u in SUFFIX_UNITS):
            bad.append(f"{r['table']}: {col} is in {unit!r}")
    return bad


def range_problems(rows, wot_max_nm):
    bad = []
    for r in rows:
        tag = f"{r['source_sheet']} row {r['source_row']}"
        if not RPM_RANGE[0] <= float(r["speed_rpm"]) <= RPM_RANGE[1]:
            bad.append(f"{tag}: speed {r['speed_rpm']}")
        if not TORQUE_FLOOR_NM <= float(r["torque_nm"]) <= WOT_MARGIN * wot_max_nm:
            bad.append(f"{tag}: torque {r['torque_nm']}")
        if not TIT_RANGE_C[0] <= float(r["turbine_inlet_temp_c"]) <= TIT_RANGE_C[1]:
            bad.append(f"{tag}: turbine inlet {r['turbine_inlet_temp_c']} C")
        for k in ("exhaust_lambda", "exhaust_lambda_left", "exhaust_lambda_right"):
            if r.get(k) and not LAMBDA_RANGE[0] <= float(r[k]) <= LAMBDA_RANGE[1]:
                bad.append(f"{tag}: {k} {r[k]}")
    return bad


def bmep_problems(rows, displacement_l):
    """EPA's BMEP is 4 pi T / V_d: the displacement it implies, against the ALPHA file's."""
    implied = sorted(4.0 * math.pi * float(r["torque_nm"]) / (float(r["bmep_bar"]) * 1e5) * 1e3
                     for r in rows if abs(float(r["torque_nm"])) > 50.0)
    mid = implied[len(implied) // 2]
    off = abs(mid / displacement_l - 1.0)
    return [] if off <= BMEP_DISPLACEMENT_TOL else [f"BMEP implies {mid:.4f} L against {displacement_l} L"]


def key_problems(rows, steady):
    bad = []
    for r in rows:
        for k in E.KEY_COLUMNS + (E.KEY_COLUMNS_STEADY if steady else ()):
            v = r.get(k, "")
            if v == "" or not math.isfinite(float(v)):
                bad.append(f"{r['source_sheet']} row {r['source_row']}: {k} is {v!r}")
    return bad


def pair_problems(initial, final):
    if len(initial) != len(final):
        return [f"{len(initial)} initial holds against {len(final)} final"]
    bad = []
    for a, b in zip(initial, final):
        if a["source_row"] != b["source_row"]:
            bad.append(f"row {a['source_row']} paired with row {b['source_row']}")
        if abs(float(a["speed_rpm"]) - float(b["speed_rpm"])) > PAIR_RPM:
            bad.append(f"row {a['source_row']}: speeds {a['speed_rpm']} / {b['speed_rpm']}")
        if abs(float(b["torque_nm"]) / float(a["torque_nm"]) - 1.0) > PAIR_TORQUE:
            bad.append(f"row {a['source_row']}: torques {a['torque_nm']} / {b['torque_nm']}")
    return bad


def docx_text(path):
    with zipfile.ZipFile(path) as z:
        root = ET.fromstring(z.read("word/document.xml"))
    w = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    return "\n".join("".join(t.text or "" for t in p.iter(w + "t")) for p in root.iter(w + "p"))


def car_problems(spec):
    """The form of a car file: every table that holds a value names its status and a source
    that [sources] resolves to a URL (or, for the repository's own values, a path)."""
    bad = []
    sources = spec.get("sources", {})
    for key, src in sources.items():
        if not (src.get("url", "").startswith("https://") or (key == "REPO" and src.get("path"))):
            bad.append(f"source {key} has no https url")
    tabs = [(k, v) for k, v in spec.items() if isinstance(v, dict) and k not in ("sources", "not_typed")]
    tabs += [(f"epa_test_car_other_rows[{i}]", v) for i, v in enumerate(spec.get("epa_test_car_other_rows", []))]
    for name, t in tabs:
        if t.get("status") not in ("PUBLISHED", "REPO"):
            bad.append(f"[{name}] status {t.get('status')!r}")
        if t.get("source") not in sources:
            bad.append(f"[{name}] source {t.get('source')!r} is not in [sources]")
        if (t.get("status") == "REPO") != (name == "repo_current"):
            bad.append(f"[{name}] only [repo_current] may hold the repository's own values")
    for k in ("schema", "car_id", "engine_id", "epa_test_car", "not_typed"):
        if k not in spec:
            bad.append(f"no {k}")
    return bad


def repo_current_problems(spec, car):
    """The Supra file's [repo_current], a copy of the plant's road load and tyre radius,
    against the plant's car record (engines.Car): every disagreement."""
    rc = spec.get("repo_current", {})
    want = {"mass_kg": car.mass, "cd_a_m2": car.cd_a, "crr": car.crr, "wheel_r_m": car.wheel_r}
    return [f"[repo_current] {k} {rc.get(k)!r}, the plant's {v!r}" for k, v in want.items() if rc.get(k) != v]


# EPA Test Car List columns, against the car file's keys.
TCL_COLUMNS = {
    "model_year": "Model Year", "represented_model": "Represented Test Veh Model",
    "test_vehicle_id": "Test Vehicle ID", "engine_code": "Engine Code",
    "equivalent_test_weight_lb": "Equivalent Test Weight (lbs.)", "target_coef_a_lbf": "Target Coef A (lbf)",
    "target_coef_b_lbf_per_mph": "Target Coef B (lbf/mph)", "target_coef_c_lbf_per_mph2": "Target Coef C (lbf/mph**2)",
    "axle_ratio": "Axle Ratio", "n_over_v_rpm_per_mph": "N/V Ratio", "rated_hp": "Rated Horsepower",
}


@functools.lru_cache(maxsize=None)
def tcl_rows(path):
    """{spreadsheet row number: {column: text}} of a Test Car List (.csv or .xlsx); row 1 is the header."""
    if path.lower().endswith(".xlsx"):
        sheet = next(iter(E.read_xlsx(path).values()))
        width = max(max(c) for c in sheet.values() if c) + 1
        grid = {n: [cells.get(i, ("", ""))[0] for i in range(width)] for n, cells in sheet.items()}
    else:
        with open(path, "rb") as fh:
            raw = fh.read()
        for enc in ("utf-8-sig", "cp1252"):
            try:
                text = raw.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        grid = {i + 1: row for i, row in enumerate(csv.reader(io.StringIO(text)))}
    head = grid[1]
    return {n: dict(zip(head, row)) for n, row in grid.items() if n > 1}


def same(a, b):
    try:
        return math.isclose(float(a), float(b), rel_tol=1e-12, abs_tol=1e-12)
    except (TypeError, ValueError):
        return str(a).strip() == str(b).strip()


def epa_row_problems(row, source_rows):
    bad = []
    for n in row["file_rows"]:
        got = source_rows.get(n)
        if got is None:
            bad.append(f"row {n} is not in the file")
            continue
        for key, column in TCL_COLUMNS.items():
            if key in row and not same(row[key], got.get(column)):
                bad.append(f"row {n}: {key} = {row[key]!r}, the file says {got.get(column)!r}")
    return bad


@functools.lru_cache(maxsize=None)
def find_source_file(url):
    """The local copy of a source download: the data folder by its manifest path, else an extra
    folder by file name -- trusted only if it hashes to D3_AND_EPA_SOURCES.csv's sha256."""
    for s in read_csv(os.path.join(EPA, "D3_AND_EPA_SOURCES.csv")):
        if s["url"] != url:
            continue
        candidates = [os.path.join(DATA_FOLDER, s["rel_path"])]
        candidates += [os.path.join(d, os.path.basename(s["rel_path"])) for d in EXTRA_FOLDERS]
        for c in candidates:
            if os.path.exists(c) and E.sha256(c) == s["sha256"]:
                return c
        return None
    raise AssertionError(f"{url} is not in logs/epa/D3_AND_EPA_SOURCES.csv")


# --------------------------------------------------------------------------- the tests
class Inputs(unittest.TestCase):
    def setUp(self):
        self.rows = read_csv(os.path.join(EPA, "MANIFEST.csv"))

    def test_every_file_is_listed_and_hashes(self):
        self.assertEqual(manifest_problems(self.rows), [])
        on_disk = sorted(os.path.relpath(p, HERE).replace("\\", "/")
                         for engine_id in E.ENGINES for p in glob.glob(os.path.join(EPA, engine_id, "*")))
        self.assertEqual(on_disk, sorted(r["repo_path"] for r in self.rows))
        for name in ("README.md", "MANIFEST.csv", "D3_AND_EPA_SOURCES.csv", ".gitattributes"):
            self.assertTrue(os.path.exists(os.path.join(EPA, name)), name)

    def test_every_file_epa_map_reads_is_listed(self):
        listed = {r["repo_path"] for r in self.rows}
        for engine_id, spec in E.ENGINES.items():
            for name in [spec["alpha_m"], spec["alpha_html"]] + [w["file"] for w in spec["workbooks"]]:
                self.assertIn(f"logs/epa/{engine_id}/{name}", listed)

    def test_sizes(self):
        total = sum(int(r["bytes"]) for r in self.rows)
        self.assertLess(total, E.MAX_TOTAL_BYTES)
        for r in self.rows:
            self.assertLess(int(r["bytes"]), E.MAX_REPORT_BYTES if r["role"] == "test report" else E.MAX_FILE_BYTES)

    def test_hashes_equal_the_data_folder_manifest(self):
        path = os.path.join(DATA_FOLDER, "MANIFEST.csv")
        if not os.path.exists(path):
            self.skipTest(f"no data folder at {DATA_FOLDER} (set GRAD_ENGINE_DATA)")
        theirs = {}
        for r in read_csv(path):
            theirs[os.path.relpath(r["local_path"], DATA_FOLDER).replace("\\", "/")] = r
        for r in self.rows:
            t = theirs.get(r["data_folder_path"])
            self.assertIsNotNone(t, r["data_folder_path"])
            self.assertEqual((t["sha256"], t["bytes"]), (r["sha256"], r["bytes"]), r["repo_path"])
            self.assertEqual(t["url"], f"zip-member: {r['url']} :: {r['zip_member']}", r["repo_path"])


class Counts(unittest.TestCase):
    def test_row_counts(self):
        got = {k: len(v) for k, v in tables().items()}
        self.assertEqual(got, EXPECTED_ROWS)

    def test_json_counts_agree(self):
        for engine_id in E.ENGINES:
            for name, t in engine_json(engine_id)["tables"].items():
                self.assertEqual(t["rows"], EXPECTED_ROWS[f"{engine_id}/{name}"])


class Units(unittest.TestCase):
    def test_suffixes_match_epa_units(self):
        for engine_id in E.ENGINES:
            d = read_csv(os.path.join(E.OUT_DIR, engine_id, "epa_channels.csv"))
            self.assertEqual(unit_problems(d), [], engine_id)

    def test_key_channels_carry_epa_units(self):
        want = {"speed_rpm": "rpm", "torque_nm": "Nm", "turbine_inlet_temp_c": "degC",
                "intake_manifold_press_kpa_abs": "kPaA"}
        for engine_id in E.ENGINES:
            for r in read_csv(os.path.join(E.OUT_DIR, engine_id, "epa_channels.csv")):
                if r["column"] in want:
                    self.assertEqual(r["epa_unit"], want[r["column"]], (engine_id, r["table"]))

    def test_reference_only_channels_are_flagged_not_dropped(self):
        for engine_id in E.ENGINES:
            d = read_csv(os.path.join(E.OUT_DIR, engine_id, "epa_channels.csv"))
            flagged = {r["column"] for r in d if r["reference_only"] == "1"}
            self.assertIn("spark_timing_cad_btdc", flagged, engine_id)
            self.assertTrue(flagged & {"exhaust_lambda", "exhaust_lambda_left"}, engine_id)
            for r in d:
                self.assertEqual(r["reference_only"] == "1", r["epa_status"].lower().startswith("reference only"))
            self.assertEqual(sorted(flagged), engine_json(engine_id)["reference_only_columns"])


class Ranges(unittest.TestCase):
    def test_physical_ranges(self):
        for key, rows in tables().items():
            wot = max(engine_json(key.split("/")[0])["wot_torque_curve"]["torque_nm"])
            self.assertEqual(range_problems(rows, wot), [], key)

    def test_bmep_follows_from_torque_and_displacement(self):
        for key, rows in tables().items():
            vd = engine_json(key.split("/")[0])["displacement_l"]
            self.assertEqual(bmep_problems(rows, vd), [], key)


class Keys(unittest.TestCase):
    def test_no_empty_key_values(self):
        for key, rows in tables().items():
            self.assertEqual(key_problems(rows, "steady" in key), [], key)


class Pairs(unittest.TestCase):
    def test_initial_and_final_are_one_hold(self):
        t = tables()
        for key in t:
            if "highload_initial" in key:
                self.assertEqual(pair_problems(t[key], t[key.replace("initial", "final")]), [], key)


class Regenerate(unittest.TestCase):
    def test_rebuild_is_byte_for_byte(self):
        files = E.build_all()
        self.assertEqual(E.changed(files), [], "run `python epa_map.py` (or check .gitattributes)")
        # no stale table either: every epa_* file under data/engines/ is one epa_map.py builds
        # (other generated files, such as a later calibration's, may live beside them)
        on_disk = sorted(os.path.relpath(os.path.join(d, f), E.OUT_DIR).replace("\\", "/")
                         for d, _, fs in os.walk(E.OUT_DIR) for f in fs if f.startswith("epa_"))
        self.assertEqual(on_disk, sorted(k for k in files if os.path.basename(k).startswith("epa_")))


class Engine(unittest.TestCase):
    def test_bore_stroke_displacement(self):
        for engine_id in E.ENGINES:
            j = engine_json(engine_id)
            for k in ("bore_mm", "stroke_mm"):
                self.assertIn(k, j["geometry_notes"])
                if j[k] is None:
                    self.assertIn("not stated by the package", j["geometry_notes"][k])
            if j["bore_mm"] is not None and j["stroke_mm"] is not None:
                self.assertLess(abs(j["displacement_from_bore_stroke_l"] / j["displacement_l"] - 1.0), 0.001)

    def test_test_cells(self):
        """A workbook whose title names its cell must carry that cell's label; one whose title
        does not (Mazda, Honda) must carry the cell its test report says it ran in."""
        for engine_id, spec in E.ENGINES.items():
            for wb in spec["workbooks"]:
                title = engine_json(engine_id)["tables"][next(iter(wb["tables"].values()))]["title"]
                named = re.search(r"Fuel (Cell \S+|HD\d+) - Test Data$", title)
                if named:
                    self.assertTrue(wb["cell"].endswith(named.group(1)), (engine_id, wb["cell"], title))
                else:
                    report = docx_text(os.path.join(EPA, engine_id, wb["report"]))
                    self.assertIn(f"performed in National Center for Advanced Technology (NCAT) {wb['cell']}",
                                  report, (engine_id, wb["cell"]))

    def test_curves_are_the_alpha_files(self):
        for engine_id, spec in E.ENGINES.items():
            j = engine_json(engine_id)
            m = E.parse_alpha_m(os.path.join(EPA, engine_id, spec["alpha_m"]))
            self.assertEqual(j["wot_torque_curve"]["torque_nm"], m["vectors"]["full_throttle_torque_Nm"])
            self.assertEqual(j["closed_throttle_torque_curve"]["torque_nm"], m["vectors"]["closed_throttle_torque_Nm"])
            self.assertEqual(j["displacement_l"], m["scalars"]["displacement_L"])


class CarSpecs(unittest.TestCase):
    def setUp(self):
        self.cars = {}
        for p in sorted(glob.glob(os.path.join(CARS, "*.toml"))):
            with open(p, "rb") as fh:
                self.cars[os.path.basename(p)[:-5]] = tomllib.load(fh)

    def test_the_four_cars(self):
        self.assertEqual(sorted(self.cars), ["a90_supra_2020", "accord_2018_15t", "cx9_2016_25t", "f150_2015_27tt"])
        for car_id, spec in self.cars.items():
            self.assertEqual(spec["car_id"], car_id)
            self.assertEqual(car_problems(spec), [], car_id)
        self.assertEqual({c["engine_id"] for c in self.cars.values()}, {"b58"} | set(E.ENGINES))

    def test_epa_rows_equal_the_test_car_list(self):
        checked, unread = 0, []
        for car_id, spec in self.cars.items():
            for row in [spec["epa_test_car"]] + spec.get("epa_test_car_other_rows", []):
                url = spec["sources"][row["source"]]["url"]
                path = find_source_file(url)
                if path is None:
                    unread.append(f"{car_id}: {os.path.basename(url)}")
                    continue
                self.assertEqual(epa_row_problems(row, tcl_rows(path)), [], (car_id, row["file_rows"]))
                checked += 1
        if unread:
            print(f"\n  CarSpecs: {checked} EPA rows checked; not on this machine, so not checked: "
                  + "; ".join(sorted(set(unread))), file=sys.stderr)
        if checked == 0:
            self.skipTest("no Test Car List file on this machine (set GRAD_ENGINE_DATA)")

    def test_repo_current_is_the_plant(self):
        import engines
        self.assertEqual(repo_current_problems(self.cars["a90_supra_2020"], engines.get("b58").car), [])


class ChecksCanFail(unittest.TestCase):
    """Each check above, run on a corrupted copy, must catch the corruption (mistake 12)."""

    def setUp(self):
        self.t = tables()
        self.rows = self.t["mazda_25t/epa_steady.csv"]

    def test_manifest(self):
        rows = read_csv(os.path.join(EPA, "MANIFEST.csv"))
        rows[0] = dict(rows[0], sha256="0" * 64)
        self.assertTrue(manifest_problems(rows))

    def test_units(self):
        d = read_csv(os.path.join(E.OUT_DIR, "mazda_25t", "epa_channels.csv"))
        d[0] = dict(d[0], column="speed_rpm", epa_unit="kPaA")
        self.assertTrue(unit_problems(d))

    def test_ranges(self):
        for col, bad in (("speed_rpm", "9000.0"), ("torque_nm", "600.0"), ("turbine_inlet_temp_c", "1200.0")):
            rows = copy.deepcopy(self.rows)
            rows[5][col] = bad
            self.assertTrue(range_problems(rows, 441.6), col)

    def test_bmep(self):
        self.assertTrue(bmep_problems(self.rows, 2.488 * 1.01))

    def test_keys(self):
        rows = copy.deepcopy(self.rows)
        rows[7]["turbine_inlet_temp_c"] = ""
        self.assertTrue(key_problems(rows, True))
        rows = copy.deepcopy(self.rows)
        rows[7]["fuel_meter_flow_gps"] = ""
        self.assertTrue(key_problems(rows, True))
        self.assertFalse(key_problems(rows, False))

    def test_pairs_shifted_by_one(self):
        for key in self.t:
            if "highload_initial" in key:
                final = self.t[key.replace("initial", "final")]
                shifted = [dict(b, source_row=a["source_row"]) for a, b in zip(self.t[key][:-1], final[1:])]
                self.assertTrue(pair_problems(self.t[key][:-1], shifted), key)

    def test_curve_provenance(self):
        """A node is 'measured' only when it IS a measured point: move it 0.01 Nm and it is not."""
        hli = [("epa_highload_initial.csv", E.PROVENANCE + ("speed_rpm", "torque_nm"), [])]
        rows = self.t["mazda_25t/epa_highload_initial.csv"]
        hli[0][2].extend([[r[k] for k in hli[0][1]] for r in rows])
        node = next(r for r in rows if r["source_row"] == "12")
        rpm, nm = float(node["speed_rpm"]), float(node["torque_nm"])
        self.assertTrue(E._is_measured(rpm, nm, hli))
        self.assertFalse(E._is_measured(rpm, nm + 0.01, hli))
        self.assertFalse(E._is_measured(rpm + 2 * E.NEAR_RPM, nm, hli))

    def test_regenerate(self):
        files = E.build_all()
        rel = "ford_27tt/epa_steady_hd1.csv"
        files[rel] = files[rel].replace(b"\n", b"\r\n")
        self.assertEqual(E.changed(files), [(rel, "differs")])

    def test_car_specs(self):
        with open(os.path.join(CARS, "cx9_2016_25t.toml"), "rb") as fh:
            spec = tomllib.load(fh)
        broken = copy.deepcopy(spec)
        del broken["final_drive"]["source"]
        self.assertTrue(car_problems(broken))
        broken = copy.deepcopy(spec)
        broken["gear_ratios"]["status"] = "DERIVED"
        self.assertTrue(car_problems(broken))
        import engines
        with open(os.path.join(CARS, "a90_supra_2020.toml"), "rb") as fh:
            supra = tomllib.load(fh)
        broken = copy.deepcopy(supra)
        broken["repo_current"]["mass_kg"] = 1521.0
        self.assertTrue(repo_current_problems(broken, engines.get("b58").car))
        row = dict(spec["epa_test_car"], target_coef_a_lbf=40.453)
        path = find_source_file(spec["sources"]["EPA16"]["url"])
        if path is None:
            self.skipTest("no 2016 Test Car List on this machine")
        self.assertTrue(epa_row_problems(row, tcl_rows(path)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
