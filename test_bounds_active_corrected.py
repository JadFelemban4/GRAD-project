"""test_bounds_active_corrected.py -- decision 92's corrected bound lists (bounds_active_corrected.py and its
record, results/EPA_CALIBRATION/bounds_active_corrected.json; commit G, VALIDATION_DECISIONS rows 109 and 141;
docs/build_step_2/INTERFACES.md sections 7 and 12.6).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B test_bounds_active_corrected.py
        seconds; exit code 0 when all pass

WHAT IT PINS. The committed record equals its recomputation from the frozen calibration records, every key but
`versions` (Record); row 109's four join delay_rpm and no S2 list moves; every fitted parameter has its distance,
consistent with the lists. Every refusal of the writer fires, each on a scratch copy of the frozen records edited
for it (one with epa_fit.BOUNDS patched instead), and each test asserts the refusal's own text, so that another
refusal cannot stand in for it; the untouched copy, which gives the record (test_the_copy_gives_the_record), is
their control. The tolerance names a parameter at half of it and not at twice it (Refusals: mistake 12). The
writer imports no fingerprint and no epa_rows, calls no fingerprint function, names no table, and no hashed module
imports it (Isolation). The command line agrees (Cli).

WHAT IT IS NOT. It is outside epa_freeze.STEP2_TESTS, which is frozen with the code it lists. Every class is
test_epa_fixtures.Guarded, so an open of an EPA table, logs/** or the contract fails it; the writer reads only
results/EPA_CALIBRATION/<id>/freeze.json and the frozen fit record, which the guard allows. No frozen value is typed
here: the controls move the scratch copies' own values, and the names of row 109's list are the row's. It cannot
run on row 94's restored branch, where epa_fit.py is the third commit F's and has no bounds_at (row 141 (5)).
"""
import ast
import contextlib
import io
import json
import math
import os
import shutil
import sys
import tempfile
import unittest
from unittest import mock

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import bounds_active_corrected as B  # noqa: E402
import engines  # noqa: E402
import epa_fit  # noqa: E402
import epa_freeze  # noqa: E402
import epa_roads as ER  # noqa: E402
import epa_rows  # noqa: E402
import fingerprint  # noqa: E402
import test_epa_fixtures as F  # noqa: E402
import test_epa_rows as TR  # noqa: E402
import tit_cap_ecu  # noqa: E402
from thresholds import common  # noqa: E402

WRITER = "bounds_active_corrected.py"
NEW = (WRITER, "test_bounds_active_corrected.py")
# Row 109's lists, the names each corrected stage adds: "The Ford's burn_rpm, fmep_0 and fmep_sp, and the Honda's
# burn_rpm, join delay_rpm", the Mazda's S4 list staying empty, and no S2 list moving. Names, not values. Should the
# writer's run name other lists, row 141 (1) commits them as found, disclosed beside row 109's; this constant then
# changes with that disclosure, in BOTH stages as printed, and the tolerance does not.
ROW_109_ADDED = {"S2": {"mazda_25t": [], "honda_l15b7": [], "ford_27tt": []},
                 "S4": {"mazda_25t": [], "honda_l15b7": ["burn_rpm"], "ford_27tt": ["burn_rpm", "fmep_0", "fmep_sp"]}}
# INTERFACES.md 12.6, in its order.
TOP_KEYS = ["schema", "decisions", "rule", "tolerance", "bounds", "x_scale", "engines", "code_sha_text", "versions",
            "fit_run", "frozen_records_rewritten", "not_rewritten_note"]
ENGINE_KEYS = ["form", "inputs", "frozen_sections_sha256", "ve_rpm_bounds_from", "distances", "stages",
               "other_forms"]


def read(rel):
    with open(os.path.join(HERE, rel), encoding="utf-8") as fh:
        return fh.read()


def frozen_fit(engine, root):
    """(freeze.json, its frozen fit record, the fit record's path) in `root`, read as the writer reads them."""
    fz_rel = epa_freeze.freeze_relpath(engine)
    fz = epa_freeze.read_json(fz_rel, root=root)
    fit_rel = f"{os.path.dirname(fz_rel)}/fit_{fz['form']}.json"
    return fz, epa_freeze.read_json(fit_rel, root=root), fit_rel


def copy_inputs(root):
    """A scratch work tree holding each engine's freeze.json and frozen fit record, byte for byte."""
    for e in B.ENGINES:
        _fz, _rec, fit_rel = frozen_fit(e, HERE)
        for rel in (epa_freeze.freeze_relpath(e), fit_rel):
            dst = os.path.join(root, *rel.split("/"))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copyfile(os.path.join(HERE, *rel.split("/")), dst)


def edit(root, engine, change, *, rehash_fits, rehash_sections):
    """Apply change(record) to the scratch copy of `engine`'s frozen fit record. rehash_fits writes its new sha_text
    into freeze.json's `fits`; rehash_sections recomputes both frozen_sections_sha256 (engines' own function), so
    that every check but the one under test still holds."""
    fz_rel = epa_freeze.freeze_relpath(engine)
    fz_path = os.path.join(root, *fz_rel.split("/"))
    fz = common.load_json(fz_path)
    fit_name = f"fit_{fz['form']}.json"
    fit_path = os.path.join(os.path.dirname(fz_path), fit_name)
    rec = common.load_json(fit_path)
    change(rec)
    if rehash_sections:
        rec["frozen_sections_sha256"] = fz["frozen_sections_sha256"] = engines.frozen_sections_sha256(rec["values"])
    epa_freeze.write_json_atomic(fit_path, rec)
    if rehash_fits:
        fz["fits"][fit_name] = common.sha_text(fit_path)
    epa_freeze.write_json_atomic(fz_path, fz)


def writer_problems(src):
    """The writer's own AST (INTERFACES.md section 7): an import of fingerprint or epa_rows, and any attribute
    reached through FP, fingerprint or an attribute named fingerprint (epa_freeze imports fingerprint at module
    level, epa_freeze.py:65, so an import closure cannot tell; the source can)."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Import):
            out += [f"import {a.name}" for a in node.names if a.name.split(".")[0] in ("fingerprint", "epa_rows")]
        elif isinstance(node, ast.ImportFrom) and node.module and node.module.split(".")[0] in ("fingerprint",
                                                                                                  "epa_rows"):
            out.append(f"from {node.module} import")
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in ("FP", "fingerprint", "epa_rows"):
                out.append(f"{node.value.id}.{node.attr}")
            elif node.attr in ("fingerprint", "epa_rows"):
                out.append(f"<...>.{node.attr}")
    return out


# =====================================================================================================
class Record(F.Guarded):
    """The committed record: its recomputation, row 109's lists, every distance, the sheet's layout."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.path = B.out_path(HERE)
        cls.fresh = B.compute(HERE)

    def test_the_record_is_what_the_frozen_vectors_give(self):
        self.assertTrue(os.path.isfile(self.path), f"{B.OUT_REL} is absent: `bounds_active_corrected.py write` "
                                                   "has not run")
        self.assertEqual(B.problems(HERE), [])
        have = common.load_json(self.path)
        fresh = json.loads(json.dumps(self.fresh))
        self.assertEqual({k: v for k, v in have.items() if k != "versions"},
                         {k: v for k, v in fresh.items() if k != "versions"})
        self.assertEqual(set(have["versions"]), set(epa_freeze.versions()))
        self.assertEqual(have["code_sha_text"], {"epa_fit.py": common.sha_text(os.path.join(HERE, "epa_fit.py")),
                                                 WRITER: common.sha_text(os.path.join(HERE, WRITER))})

    def test_decision_92s_four_join_delay_rpm(self):
        tol = epa_fit.BOUND_TOL_SCALE_UNITS
        for e, part in self.fresh["engines"].items():
            s2, s4 = part["stages"]["S2"], part["stages"]["S4"]
            self.assertEqual(s4["added"], ROW_109_ADDED["S4"][e], e)
            self.assertEqual(s4["corrected"], [n for n in epa_fit.S4_PARAMS if n in s4["recorded"] + s4["added"]])
            if ROW_109_ADDED["S4"][e]:
                self.assertIn("delay_rpm", s4["recorded"])
            # row 109: no S2 list moves
            self.assertEqual(s2["added"], ROW_109_ADDED["S2"][e], e)
            self.assertEqual(s2["corrected"], [n for n in s2["params"] if n in s2["recorded"] + s2["added"]], e)
            for g in (s2, s4):
                self.assertEqual(g["flag_corrected"], bool(g["corrected"]))
                self.assertEqual(g["flag_recorded"], bool(g["recorded"]))
                # each list is exactly what the record's own distances and the tolerance give
                for n in g["params"]:
                    near = part["distances"][n]["distance_x_scale_units"] <= tol
                    self.assertEqual(n in g["corrected"], n in g["recorded"] or near, (e, n))
            self.assertEqual(part["form"], "A+B+C+D")
            self.assertEqual(set(part["stages"]), {"S1", "S2", "S3b", "S4", "S5"})
            for s in ("S1", "S3b", "S5"):
                self.assertEqual(part["stages"][s]["rule"], B.COPIED_RULES[s])

    def test_every_parameter_has_its_distance(self):
        for e, part in self.fresh["engines"].items():
            _fz, rec, _rel = frozen_fit(e, HERE)
            bounds = rec["settings"]["bounds"]
            self.assertEqual(list(part["distances"]), list(bounds), e)
            for n, d in part["distances"].items():
                self.assertGreaterEqual(d["to_lower"], 0.0, (e, n))
                self.assertGreaterEqual(d["to_upper"], 0.0, (e, n))
                self.assertEqual(d["distance"], min(d["to_lower"], d["to_upper"]))
                self.assertEqual([d["lower"], d["upper"]], bounds[n])
                self.assertEqual(d["value"], rec["values"]["cycle"][n])
                self.assertEqual(d["x_scale"], epa_fit.X_SCALE.get(n))
            stage = {n: d["stage"] for n, d in part["distances"].items()}
            self.assertEqual({n for n, s in stage.items() if s == "S4"}, set(epa_fit.S4_PARAMS))
            self.assertEqual({n for n, s in stage.items() if s == "S2"}, set(epa_fit.s2_names(part["form"])))
            # ve_rpm's ends are the fit's own (row 141 (3)), not epa_fit.BOUNDS', which holds None
            self.assertIsNone(self.fresh["bounds"]["ve_rpm"])
            self.assertEqual([part["distances"]["ve_rpm"]["lower"], part["distances"]["ve_rpm"]["upper"]],
                             rec["stages"]["S2"]["report"]["bounds"]["ve_rpm"])

    def test_the_layout_is_the_interface_sheets(self):
        rec = self.fresh
        self.assertEqual(list(rec), TOP_KEYS)
        self.assertEqual((rec["schema"], rec["decisions"]), (B.SCHEMA, ["decision 92", "row 109", "row 141"]))
        self.assertEqual(rec["tolerance"], {"value": epa_fit.BOUND_TOL_SCALE_UNITS, "unit": "epa_fit.X_SCALE units",
                                            "constant": "epa_fit.BOUND_TOL_SCALE_UNITS",
                                            "chosen_after": "the distances were read (disclosed)"})
        self.assertEqual(rec["x_scale"], epa_fit.X_SCALE)
        self.assertEqual((rec["fit_run"], rec["frozen_records_rewritten"]), (False, False))
        self.assertEqual(list(rec["engines"]), list(common.EPA_ENGINES))
        for e, part in rec["engines"].items():
            self.assertEqual(list(part), ENGINE_KEYS)
            fz, _rec, fit_rel = frozen_fit(e, HERE)
            self.assertEqual(list(part["inputs"]), [epa_freeze.freeze_relpath(e), fit_rel])
            self.assertEqual(part["frozen_sections_sha256"], fz["frozen_sections_sha256"])
            self.assertEqual(set(part["other_forms"].values()), {"not corrected"})
            self.assertEqual(len(part["other_forms"]), len([f for f in fz["fits"] if f.startswith("fit_")]) - 1)
        blob = json.dumps(rec)
        for word in ("timestamp", "git_head", "started", "finished"):          # recomputed exactly: no clock, no HEAD
            self.assertNotIn(f'"{word}"', blob)


class Refusals(F.Guarded):
    """Each check of the writer refuses on a scratch copy of the frozen records, and the copy itself gives the
    record (the base every control is made from)."""

    def setUp(self):
        super().setUp()
        self.root = tempfile.mkdtemp(prefix="bounds_active_")
        self.addCleanup(shutil.rmtree, self.root, True)
        copy_inputs(self.root)

    def refused(self):
        with self.assertRaises(B.Refused) as cm:
            B.compute(self.root)
        return cm.exception.problems

    def test_the_copy_gives_the_record(self):
        self.assertEqual(B.compute(self.root), B.compute(HERE))

    def test_one_ulp_on_a_frozen_value_is_refused(self):
        def ulp(rec):
            v = rec["values"]["cycle"]["burn_base"]
            rec["values"]["cycle"]["burn_base"] = math.nextafter(v, math.inf)
        edit(self.root, "mazda_25t", ulp, rehash_fits=True, rehash_sections=False)
        probs = self.refused()
        self.assertTrue(any("frozen_sections_sha256" in p and p.startswith("mazda_25t") for p in probs), probs)
        self.assertTrue(any("values.cycle['burn_base'] is not S4's own value" in p for p in probs), probs)

    def test_a_fit_record_that_freeze_json_does_not_name_is_refused(self):
        edit(self.root, "honda_l15b7", lambda rec: rec["provenance"].update(scratch_edit=True), rehash_fits=False,
             rehash_sections=False)
        probs = self.refused()
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("is not the file freeze.json's fits names", probs[0])

    def test_bounds_and_scales_unlike_epa_fits_are_refused(self):
        edit(self.root, "ford_27tt", lambda rec: rec["settings"]["bounds"].update(fmep_sp=[-0.2, 0.4]),
             rehash_fits=True, rehash_sections=False)
        probs = self.refused()
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("settings.bounds['fmep_sp']", probs[0])
        copy_inputs(self.root)

        def scale(rec):
            rec["settings"]["x_scale"]["burn_rpm"] *= 2.0
        edit(self.root, "ford_27tt", scale, rehash_fits=True, rehash_sections=False)
        self.assertTrue(any("settings.x_scale['burn_rpm']" in p for p in self.refused()))
        copy_inputs(self.root)

        def ends(rec):                               # ve_rpm's ends no longer S2's report bounds (row 141 (3))
            rec["settings"]["bounds"]["ve_rpm"][0] += 1.0
        edit(self.root, "ford_27tt", ends, rehash_fits=True, rehash_sections=False)
        self.assertTrue(any("S2's report bounds for ve_rpm" in p for p in self.refused()))

    def test_a_stage_point_or_flag_unlike_the_frozen_record_is_refused(self):
        def stage_value(rec):
            v = rec["stages"]["S4"]["values"]["fmep_sp"]
            rec["stages"]["S4"]["values"]["fmep_sp"] = math.nextafter(v, -math.inf)
        edit(self.root, "mazda_25t", stage_value, rehash_fits=True, rehash_sections=False)
        probs = self.refused()
        self.assertEqual(probs, ["mazda_25t: values.cycle['fmep_sp'] is not S4's own value bit for bit"])
        copy_inputs(self.root)

        def flag(rec):
            rec["stages"]["S4"]["flags"] = [f for f in rec["stages"]["S4"]["flags"] if f != "S4_bound_active"]
        edit(self.root, "honda_l15b7", flag, rehash_fits=True, rehash_sections=False)
        self.assertTrue(any("S4_bound_active disagrees" in p for p in self.refused()))

    # The fix round (the review of commit G, its M1): every other refusal of engine_part, one test each, on a copy
    # edited so that this refusal alone fires (the fits, frozen_sections and values checks still hold), its text
    # asserted whole. The control of each is test_the_copy_gives_the_record: the same copy, unedited, is refused
    # nothing. Each fails if its check is removed (compute then returns, or raises a KeyError, not Refused) or its
    # text changes.
    def test_a_freeze_record_whose_fits_do_not_name_its_form_is_refused(self):
        fz_path = os.path.join(self.root, *epa_freeze.freeze_relpath("honda_l15b7").split("/"))
        fz = common.load_json(fz_path)
        fit_name = f"fit_{fz['form']}.json"
        del fz["fits"][fit_name]
        epa_freeze.write_json_atomic(fz_path, fz)
        self.assertEqual(self.refused(), [f"honda_l15b7: freeze.json's fits does not name {fit_name}, the form it "
                                          "froze"])

    def test_a_fit_record_of_another_engine_is_refused(self):
        form = frozen_fit("mazda_25t", self.root)[0]["form"]
        edit(self.root, "mazda_25t", lambda rec: rec["settings"].update(engine="ford_27tt"), rehash_fits=True,
             rehash_sections=False)
        self.assertEqual(self.refused(), [f"mazda_25t: fit_{form}.json is the fit of 'ford_27tt' at form {form!r}, "
                                          f"not of mazda_25t at {form!r}"])

    def test_a_bound_epa_fit_does_not_hold_is_refused(self):
        edit(self.root, "ford_27tt", lambda rec: rec["settings"]["bounds"].update(not_a_parameter=[0.0, 1.0]),
             rehash_fits=True, rehash_sections=False)
        self.assertEqual(self.refused(), [
            "ford_27tt: settings.bounds names not_a_parameter, which epa_fit.BOUNDS does not",
            "ford_27tt: settings.bounds' not_a_parameter is fitted by [], not by exactly one stage"])

    def test_a_bound_epa_fit_holds_as_none_other_than_ve_rpms_is_refused(self):
        with mock.patch.dict(epa_fit.BOUNDS, {"fmep_sp": None}):         # the copy untouched, the code patched
            probs = self.refused()
        self.assertEqual(probs, [f"{e}: epa_fit.BOUNDS holds None for fmep_sp; only ve_rpm's ends are read from the "
                                 "fit" for e in B.ENGINES])

    def test_bounds_out_of_order_are_refused(self):
        rev = []

        def reverse(rec):                  # ve_rpm's ends swapped, in settings.bounds and S2's report alike
            rev.extend(reversed(rec["settings"]["bounds"]["ve_rpm"]))
            rec["settings"]["bounds"]["ve_rpm"] = list(rev)
            rec["stages"]["S2"]["report"]["bounds"]["ve_rpm"] = list(rev)
        edit(self.root, "ford_27tt", reverse, rehash_fits=True, rehash_sections=False)
        self.assertEqual(self.refused(), [f"ford_27tt: settings.bounds['ve_rpm'] {rev!r} is not two finite ends in "
                                          "order"])

    def test_report_params_unlike_epa_fits_are_refused(self):
        swapped = []

        def swap(rec):
            p = rec["stages"]["S4"]["report"]["params"]
            p[0], p[1] = p[1], p[0]
            swapped.extend(p)
        edit(self.root, "mazda_25t", swap, rehash_fits=True, rehash_sections=False)
        self.assertEqual(self.refused(), [f"mazda_25t: S4's report params {swapped} are not epa_fit's "
                                          f"{list(epa_fit.S4_PARAMS)}"])

    def test_a_param_without_its_scale_is_refused(self):
        edit(self.root, "mazda_25t", lambda rec: rec["settings"]["x_scale"].pop("fmep_sp"), rehash_fits=True,
             rehash_sections=False)
        self.assertEqual(self.refused(), ["mazda_25t: S4's fmep_sp has no settings.bounds or settings.x_scale entry"])

    def test_a_recorded_list_out_of_its_params_order_is_refused(self):
        def order(rec):                    # two S4 names, last before first; the flag raised, as a list needs
            s4 = rec["stages"]["S4"]
            s4["bounds_active"] = [epa_fit.S4_PARAMS[-1], epa_fit.S4_PARAMS[0]]
            if "S4_bound_active" not in s4["flags"]:
                s4["flags"].append("S4_bound_active")
        edit(self.root, "ford_27tt", order, rehash_fits=True, rehash_sections=False)
        self.assertEqual(self.refused(), [
            f"ford_27tt: S4's recorded list {[epa_fit.S4_PARAMS[-1], epa_fit.S4_PARAMS[0]]} is not a list of its "
            "params in their order"])

    def test_a_param_fitted_by_two_stages_is_refused(self):
        def twice(rec):
            rec["stages"]["S5"]["values"]["fmep_sp"] = rec["stages"]["S4"]["values"]["fmep_sp"]
        edit(self.root, "mazda_25t", twice, rehash_fits=True, rehash_sections=False)
        self.assertEqual(self.refused(), ["mazda_25t: settings.bounds' fmep_sp is fitted by ['S4', 'S5'], not by "
                                          "exactly one stage"])

    def test_the_tolerance_names_a_parameter_at_half_of_it_and_not_at_twice(self):
        lo = epa_fit.BOUNDS["fmep_sp"][0]
        step = epa_fit.BOUND_TOL_SCALE_UNITS * epa_fit.X_SCALE["fmep_sp"]
        got = {}
        for k in (0.5, 2.0):
            copy_inputs(self.root)

            def place(rec, value=lo + k * step):
                rec["values"]["cycle"]["fmep_sp"] = rec["stages"]["S4"]["values"]["fmep_sp"] = value
            edit(self.root, "mazda_25t", place, rehash_fits=True, rehash_sections=True)
            s4 = B.compute(self.root)["engines"]["mazda_25t"]["stages"]["S4"]
            got[k] = ("fmep_sp" in s4["corrected"], "fmep_sp" in s4["added"], "fmep_sp" in s4["recorded"])
        self.assertEqual(got[0.5], (True, True, False))
        self.assertEqual(got[2.0], (False, False, False))              # the control, at twice the tolerance

    def test_the_record_is_written_once_and_check_finds_an_edit(self):
        rec, sha = B.write(self.root)
        self.assertEqual(sha, common.sha_text(B.out_path(self.root)))
        self.assertEqual(B.problems(self.root), [])
        self.assertIsNone(B.versions_note(self.root))
        with self.assertRaises(B.Refused) as cm:
            B.write(self.root)
        self.assertEqual(cm.exception.problems, [f"{B.OUT_REL} exists: the record is written once (check compares "
                                                 "it)"])
        have = common.load_json(B.out_path(self.root))
        have["versions"]["platform"] = "another platform"                 # printed, never counted
        epa_freeze.write_json_atomic(B.out_path(self.root), have)
        self.assertEqual(B.problems(self.root), [])
        self.assertIn("another platform", B.versions_note(self.root))
        have["engines"]["ford_27tt"]["stages"]["S4"]["added"] = []
        epa_freeze.write_json_atomic(B.out_path(self.root), have)
        self.assertEqual(B.problems(self.root), [
            "engines.ford_27tt.stages.S4.added: committed [], recomputed "
            f"{rec['engines']['ford_27tt']['stages']['S4']['added']!r}"])
        os.remove(B.out_path(self.root))
        with self.assertRaises(B.Refused) as cm:
            B.problems(self.root)
        self.assertEqual(cm.exception.problems, [f"{B.OUT_REL} is absent: `write` has not run"])


class Isolation(F.Guarded):
    """The writer reads no rows and builds no plant, and nothing frozen reaches it."""

    def test_the_writer_imports_no_fingerprint_and_calls_no_fingerprint_function(self):
        self.assertEqual(writer_problems(read(WRITER)), [])
        bad = ("import fingerprint as FP\nfrom epa_rows import calibration_rows\nx = FP.plant_sha\n"
               "y = epa_freeze.fingerprint.PLANT_CODE\n")
        self.assertEqual(len(writer_problems(bad)), 4)                   # the control (mistake 12)

    def test_outside_cal_records_and_imported_by_nothing_hashed(self):
        self.assertEqual(os.path.dirname(B.OUT_REL), epa_freeze.CALIBRATION_DIR)
        self.assertFalse(any(B.OUT_REL.startswith(f"{epa_freeze.CALIBRATION_DIR}/{e}/") for e in epa_rows.TABLES))
        self.assertFalse(epa_freeze.readable_record(B.OUT_REL))         # calibrate_epa's reader never reads it
        entries = set(fingerprint.PLANT_CODE) | set(epa_freeze.CODE_HASHED) | set(tit_cap_ecu.RECORD_HASHED)
        entries |= set(ER.hashed_files(root=HERE, engines=ER.ENGINES))
        closure = set()
        for rel in sorted(e for e in entries if e.endswith(".py") and os.path.isfile(os.path.join(HERE, e))):
            closure |= set(ER.import_closure(rel, root=HERE))
        self.assertIn("epa_fit.py", closure)
        self.assertEqual(sorted(set(NEW) & closure), [])
        self.assertEqual(sorted(set(NEW) & entries), [])
        self.assertNotIn(WRITER, epa_freeze.STEP2_TESTS + epa_freeze.CODE_HASHED)
        tmp = tempfile.mkdtemp(prefix="bounds_active_closure_")
        self.addCleanup(shutil.rmtree, tmp, True)
        for rel, text in (("a.py", "def f():\n    import b\n"), ("b.py", "import bounds_active_corrected\n"),
                          (WRITER, "")):
            with open(os.path.join(tmp, rel), "w", encoding="utf-8") as fh:
                fh.write(text)
        self.assertIn(WRITER, ER.import_closure("a.py", root=tmp))        # the control, two imports away

    def test_the_new_files_name_no_table_and_keep_test_epa_rows_rules(self):
        names = sorted({s.name for specs in epa_rows.TABLES.values() for s in specs})
        self.assertTrue(names)
        for rel in NEW:
            src = read(rel)
            self.assertEqual([n for n in names if n in src], [], rel)
            self.assertEqual(TR.scan_words(src, rel), [], rel)
            self.assertEqual(TR.scan_source(src, rel), [], rel)
        self.assertEqual(TR.unguarded_test_classes(read("test_bounds_active_corrected.py"),
                                                   "test_bounds_active_corrected.py"), [])
        self.assertTrue(TR.scan_source(f"p = '{TR.DE}/x'\n", WRITER))      # the control: N1 fires on this name


class Cli(F.Guarded):
    def test_check_agrees_and_write_refuses_the_committed_record(self):
        self.assertTrue(os.path.isfile(B.out_path(HERE)))                  # so that write below can only refuse
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["check"])
        self.assertEqual(code, B.EXIT_OK, out.getvalue())
        self.assertIn("bounds_active_corrected.py check: []", out.getvalue())
        self.assertIn("separation over every engine's S2 and S4", out.getvalue())
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = B.main(["write"])
        self.assertEqual(code, B.EXIT_REFUSED, out.getvalue())
        self.assertIn("written once", out.getvalue())


if __name__ == "__main__":
    unittest.main(verbosity=2)
