"""The results tab's own suite. Nothing here writes into the repository.

    python -m app.test_results                                  every test
    python -m unittest app.test_results.EvalParserTests -v      one class

Run from the repository root. Fixtures are made in temporary directories
OUTSIDE the repository, with Path.write_text and Path.write_bytes only:
app/test_replay.py's read-only scan reads every app/*.py, this file included.
"""
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import warnings

import analyse_phase_d as APD
import analyse_phase_d2 as APD2
import fingerprint as FP
from app import results_eval as EV
from app import results_provenance as RP

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


# ---- Task 1: app/results_eval.py ---------------------------------------------

# Jad's three evaluation experiments as their files record them: the header's
# title, the header's protocol, the protocol the block's scenario names, the
# date the episodes were frozen, and the directory the agents were read from.
REAL = {
    "phase_d": ("PHASE D EVALUATION", None, "phase-d", "18 Sep 2026", "runs"),
    "d2": ("PHASE D2 EVALUATION (randomised climb)", None, "d2", "22 Sep 2026", "runs_d2"),
    "c4": ("C4 EVALUATION (agents from runs_c4/)", "d2", "d2", "22 Sep 2026", "runs_c4"),
}
REAL_SEEDS = range(8)
# analyse_phase_d.parse names the policies by label prefix; the tab, by role
APD_NAMES = {"blind": "agent (blind)", "sighted": "agent", "baseline": "baseline ECU",
             "reactive": "reactive", "current_grade": "current-grade"}

SYN_HEADER = ("ZZ EVALUATION (agents from runs_zz/) -- scored on the 'd2' protocol, "
              "20 FIXED EPISODES, frozen 22 Sep 2026")
SYN_FP = {"plant_sha": "0123456789abcdef", "gears": [5.25, 3.36, 2.172], "final_drive": 3.15,
          "scenario": {"protocol": "random-climb", "grade": [0.12, 0.16],
                       "road_sha": "aaaabbbbccccdddd"},
          "episodes_sha": "fedcba9876543210", "git_dirty": False, "git_dirty_plant_files": [],
          "git_head": "0a1b2c3d4e5f60718293a4b5c6d7e8f901234567", "python": "3.12.10",
          "plant_text_sha": "1111222233334444"}
# SYN_FP as fingerprint.format_block renders it and the parser reads it back:
# the fatal fields first, the rest sorted, every value as text
SYN_BLOCK = {"plant_sha": "0123456789abcdef", "gears": "5.25 3.36 2.172", "final_drive": "3.15",
             "scenario": "grade=0.12 0.16 protocol=random-climb road_sha=aaaabbbbccccdddd",
             "episodes_sha": "fedcba9876543210", "git_dirty": "False",
             "git_dirty_plant_files": "",
             "git_head": "0a1b2c3d4e5f60718293a4b5c6d7e8f901234567",
             "plant_text_sha": "1111222233334444", "python": "3.12.10"}
SYN_PROVENANCE = (
    "note sighted_seed0: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)",
    "model runs_zz\\sighted_seed0: trained 300000 steps of 300000 requested, from step 0, "
    "buffer 300000, zip sha 0123456789abcdef",
    "note blind_seed0: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)",
    "model runs_zz\\blind_seed0: budget unreadable",
)
SYN_FORCED = (
    "!! runs_zz\\sighted_seed0: PLANT MISMATCH",
    "     plant_sha          model 'aaaaaaaaaaaaaaaa'  live '0123456789abcdef'",
    "     episodes_sha       model 'bbbbbbbbbbbbbbbb'  live 'fedcba9876543210'",
    "     --force-plant-mismatch was given; the rows below are NOT a Phase D result.",
    "model runs_zz\\sighted_seed0: trained 300000 steps of 300000 requested, from step 0, "
    "buffer 300000, zip sha 0123456789abcdef",
    "!! runs_zz\\blind_seed0: NO meta.json -- plant unknown, --force-plant-mismatch used",
    "model runs_zz\\blind_seed0: budget unreadable",
)
# (label, median, IQR width, worst, median fuel, hottest turbine)
SYN_ROWS = (("baseline ECU", 1000.0, 40.0, 1200.0, 4700, 890),
            ("reactive", 700.0, 30.0, 800.0, 4800, 870),
            ("current-grade", 650.0, 25.0, 760.0, 4900, 869),
            ("agent runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
            ("agent (blind) runs_zz\\blind_seed0", 450.0, 22.0, 600.0, 5100, 855))
# (label, median without the knock term, its cut)
SYN_THERMAL = (("baseline ECU", 1500.0, 0.0), ("reactive", 1100.0, 26.7),
               ("current-grade", 1050.0, 30.0), ("agent runs_zz\\sighted_seed0", 600.0, 60.0),
               ("agent (blind) runs_zz\\blind_seed0", 1650.0, -10.0))


def _real_files():
    """{(prefix, seed): path} for every results/<prefix>_seed<N>.txt of REAL."""
    out = {}
    for path in sorted(RESULTS.glob("*_seed*.txt")):
        key = EV.parse_name(path.name)
        if key is not None and key[0] in REAL:
            out[key] = path
    return out


def _quietly(fn, *args):
    """fn(*args) with ResourceWarning silenced. analyse_phase_d.parse leaves its
    file for the garbage collector to close; the warning is about that code, not
    this suite, and it would bury the test report."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        return fn(*args)


def _row(label, median, iqr, worst, fuel, peak):
    """One policy row, formatted as evaluate.main() formats it."""
    return f"{label:<28}{median:>12.1f}{iqr:>9.1f}{worst:>9.1f}{fuel:>10.0f}{peak:>9.0f}"


def _thermal_line(label, median, cut):
    """One line of the knock-term block, formatted as evaluate.main() formats it."""
    return f"    {label:<26} thermal med {median:8.1f}   thermal cut {cut:5.1f} %"


def _eval_text(header=SYN_HEADER, fp=SYN_FP, block=True, provenance=SYN_PROVENANCE,
               table=True, rows=SYN_ROWS, thermal=None):
    """A result file's text, line by line as evaluate.main() lays it out, with
    `fp` rendered by fingerprint.format_block as this run's block. A row or a
    knock-term line given as a str is written as it is."""
    lines = [header, "scenario: a synthetic road for the parser test", "trigger:  850 C", ""]
    if block:
        lines += FP.format_block(fp, EV.BLOCK_TITLE).splitlines()
    lines += list(provenance) + [""]
    if table:
        lines.append(f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
                     f"{'fuel med':>10}{'peak C':>9}")
        lines.append("-" * 77)
        lines += [r if isinstance(r, str) else _row(*r) for r in rows]
        lines.append("-" * 77)
        base = rows[0][1] if rows and not isinstance(rows[0], str) else None
        if base:
            lines += [f"  {r[0]:<26} cuts median damage {100 * (1 - r[1] / base):5.1f} %"
                      for r in rows[1:] if not isinstance(r, str)]
    if thermal is not None:
        lines += ["", "  WITHOUT THE KNOCK TERM (turbine + oil only; the knock model is untested)"]
        lines += [t if isinstance(t, str) else _thermal_line(*t) for t in thermal]
    lines += ["", "  It is the project's result only if the fingerprint block above is the plant"]
    return "\n".join(lines) + "\n"


class EvalParserTests(unittest.TestCase):
    """Task 1: app/results_eval.py reads evaluate.py's result files."""

    def _reason(self, text):
        with self.assertRaises(EV.NotEvaluationFile) as cm:
            EV.parse_eval_text(text)
        return cm.exception.reason

    # ---- the real tree ----

    def test_real_files_are_the_twenty_four(self):
        self.assertEqual(sorted(_real_files()), sorted((p, k) for p in REAL for k in REAL_SEEDS))

    def test_real_files_parse(self):
        for (prefix, seed), path in sorted(_real_files().items()):
            with self.subTest(file=path.name):
                got = EV.parse_eval_file(path)
                title, head_protocol, block_protocol, frozen, runs = REAL[prefix]
                self.assertEqual(got["path"], str(path))
                self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                                 (title, head_protocol, 20, frozen))
                self.assertEqual(EV.protocol_from_fingerprint(got["fingerprint"]), block_protocol)
                self.assertTrue(set(FP.FATAL) <= set(got["fingerprint"]))
                self.assertEqual(got["fingerprint"]["git_dirty_plant_files"], "")
                self.assertEqual(list(got["policies"]), list(EV.ROLES))
                self.assertEqual(got["policies"]["sighted"]["dir"], f"{runs}/sighted_seed{seed}")
                self.assertEqual(got["policies"]["blind"]["dir"], f"{runs}/blind_seed{seed}")
                self.assertEqual([got["policies"][r]["dir"] for r in ("baseline", "reactive",
                                                                     "current_grade")],
                                 [None, None, None])
                self.assertTrue(got["scenario_line"].startswith("scenario: "))
                self.assertTrue(got["trigger_line"].startswith("trigger: "))
                self.assertEqual(got["forced"], [])
                self.assertIsNone(got["thermal"], "these files predate the knock-term block")

    def test_real_medians_equal_analyse_phase_d_parse(self):
        for (prefix, seed), path in sorted(_real_files().items()):
            with self.subTest(file=path.name):
                policies = EV.parse_eval_file(path)["policies"]
                ours = {role: p["median"] for role, p in policies.items()}
                theirs = _quietly(APD.parse, str(path))
                self.assertEqual(sorted(theirs), sorted(APD_NAMES.values()))
                self.assertEqual(ours, {role: theirs[name] for role, name in APD_NAMES.items()})

    def test_real_pairs_equal_analyse_phase_d2_load(self):
        files = _real_files()
        for prefix in REAL:
            with self.subTest(prefix=prefix):
                rows, incomplete = _quietly(APD2.load, prefix)
                self.assertEqual(incomplete, [])
                self.assertEqual([seed for seed, _, _ in rows], list(REAL_SEEDS))
                for seed, medians, diff in rows:
                    got = EV.parse_eval_file(files[(prefix, seed)])["policies"]
                    self.assertEqual(got["blind"]["median"] - got["sighted"]["median"], diff)
                    self.assertEqual({role: got[role]["median"] for role in APD_NAMES},
                                     {role: medians[name] for role, name in APD_NAMES.items()})

    def test_real_c4_models_and_dt_notes(self):
        got = EV.parse_eval_file(RESULTS / "c4_seed0.txt")
        self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
        self.assertEqual([n.split(":")[0] for n in got["notes"]],
                         ["note sighted_seed0", "note blind_seed0"])
        budget = "trained 300000 steps of 300000 requested, from step 0, buffer 300000, zip sha "
        self.assertEqual(got["models"], [
            {"dir": "runs_c4/sighted_seed0", "text": budget + "20f0ae6a9c1564a9",
             "steps": 300000, "requested": 300000, "zip_sha": "20f0ae6a9c1564a9"},
            {"dir": "runs_c4/blind_seed0", "text": budget + "9ab8d2b29cbb9d06",
             "steps": 300000, "requested": 300000, "zip_sha": "9ab8d2b29cbb9d06"}])
        for seed in REAL_SEEDS:
            with self.subTest(seed=seed):
                models = EV.parse_eval_file(RESULTS / f"c4_seed{seed}.txt")["models"]
                self.assertEqual([(m["dir"], m["steps"], m["requested"]) for m in models],
                                 [(f"runs_c4/sighted_seed{seed}", 300000, 300000),
                                  (f"runs_c4/blind_seed{seed}", 300000, 300000)])
                self.assertTrue(all(len(m["zip_sha"]) == 16 for m in models))

    def test_real_phase_d_and_d2_have_notes_and_no_model_lines(self):
        for prefix in ("phase_d", "d2"):
            with self.subTest(prefix=prefix):
                got = EV.parse_eval_file(RESULTS / f"{prefix}_seed0.txt")
                self.assertEqual(got["models"], [])
                self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
                self.assertEqual(len(got["notes"]), 2)

    # ---- the helpers ----

    def test_roles(self):
        self.assertEqual(sorted(r for _, r in EV.ROLE_PREFIXES), sorted(EV.ROLES))
        prefixes = [p for p, _ in EV.ROLE_PREFIXES]
        self.assertLess(prefixes.index("agent (blind)"), prefixes.index("agent"))

    def test_parse_name(self):
        for name, want in (("phase_d_seed0.txt", ("phase_d", 0)), ("d2_seed7.txt", ("d2", 7)),
                           ("c4_seed12.txt", ("c4", 12)), ("zz_v2_seed3.txt", ("zz_v2", 3))):
            with self.subTest(name=name):
                self.assertEqual(EV.parse_name(name), want)
        for name in ("Phase_D_seed0.txt", "phase-d_seed0.txt", "c4_convergence.txt",
                     "phase_d_130kmh.txt", "curve_sighted_seed0.csv", "d2_seed.txt",
                     "_d2_seed0.txt", "d2__x_seed0.txt", "2d_seed0.txt", "d2_seed0.txt.bak",
                     "results/d2_seed0.txt", "d2_seed0.txt\n", "d2_seed-1.txt", ""):
            with self.subTest(name=name):
                self.assertIsNone(EV.parse_name(name))

    def test_normalise_dir(self):
        for text, want in (("runs_c4\\sighted_seed0", "runs_c4/sighted_seed0"),
                           ("runs_c4/sighted_seed0", "runs_c4/sighted_seed0"),
                           ("./runs_d2/blind_seed3/", "runs_d2/blind_seed3"),
                           (".\\runs\\blind_seed0\\", "runs/blind_seed0"),
                           ("  runs_c4//sighted_seed0  ", "runs_c4/sighted_seed0"),
                           ("runs/./sighted_seed1", "runs/sighted_seed1"),
                           ("C:\\work\\runs_c4\\sighted_seed0", "C:/work/runs_c4/sighted_seed0"),
                           ("Runs_C4\\Sighted_seed0", "Runs_C4/Sighted_seed0")):
            with self.subTest(text=text):
                self.assertEqual(EV.normalise_dir(text), want)

    def test_parse_block_line(self):
        for line, want in (("  plant_sha                b5a3069f32a83754",
                            ("plant_sha", "b5a3069f32a83754")),
                           ("  gears                    5.25 3.36 2.172 1.72",
                            ("gears", "5.25 3.36 2.172 1.72")),
                           ("  git_dirty_plant_files    ", ("git_dirty_plant_files", "")),
                           ("  git_dirty_plant_files", ("git_dirty_plant_files", "")),
                           ("  scenario                 grade=0.12 t_amb=315 v_kmh=130\r",
                            ("scenario", "grade=0.12 t_amb=315 v_kmh=130"))):
            with self.subTest(line=line):
                self.assertEqual(EV.parse_block_line(line), want)
        for line in ("--- PLANT FINGERPRINT (this run) " + "-" * 30, "-" * 62,
                     "plant_sha                b5a3069f32a83754",
                     "   plant_sha             b5a3069f32a83754", "  ", ""):
            with self.subTest(line=line):
                self.assertIsNone(EV.parse_block_line(line))

    def test_parse_fingerprint_block(self):
        rendered = FP.format_block(SYN_FP, EV.BLOCK_TITLE).splitlines()
        got = EV.parse_fingerprint_block(rendered)
        self.assertEqual(got, SYN_BLOCK)
        self.assertEqual(list(got), list(SYN_BLOCK))
        # the live side renders with format_block's own title; the same reader
        self.assertEqual(EV.parse_fingerprint_block(FP.format_block(SYN_FP).splitlines()),
                         SYN_BLOCK)
        # lines before the title and after the closing line are not fields
        noisy = ["  stray_field              x"] + rendered + ["  reactive        cuts"]
        self.assertEqual(EV.parse_fingerprint_block(noisy), SYN_BLOCK)
        self.assertEqual(EV.parse_fingerprint_block(rendered[1:]), {})
        self.assertEqual(EV.parse_fingerprint_block([]), {})

    def test_protocol_from_fingerprint(self):
        P = EV.protocol_from_fingerprint
        self.assertEqual(P({"scenario": "grade=0.12 0.16 protocol=random-climb road_sha=ab"}), "d2")
        self.assertEqual(P({"scenario": "grade=0.12 t_amb=315 v_kmh=130"}), "phase-d")
        self.assertIsNone(P({"scenario": "protocol=something-else v_kmh=130"}))
        self.assertIsNone(P({"scenario": "protocol=random-climb-v2"}))
        self.assertIsNone(P({"plant_sha": "0123456789abcdef"}))
        self.assertIsNone(P({}))

    # ---- synthetic files ----

    def test_synthetic_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_text(_eval_text(), encoding="utf-8")
            got = EV.parse_eval_file(path)
        self.assertEqual(got["path"], str(path))
        self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                         ("ZZ EVALUATION (agents from runs_zz/)", "d2", 20, "22 Sep 2026"))
        self.assertEqual(got["scenario_line"], "scenario: a synthetic road for the parser test")
        self.assertEqual(got["trigger_line"], "trigger:  850 C")
        self.assertEqual(got["fingerprint"], SYN_BLOCK)
        self.assertEqual(got["forced"], [])
        self.assertEqual(got["notes"], [SYN_PROVENANCE[0], SYN_PROVENANCE[2]])
        self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
        self.assertEqual(got["models"], [
            {"dir": "runs_zz/sighted_seed0", "text": SYN_PROVENANCE[1].split(": ", 1)[1],
             "steps": 300000, "requested": 300000, "zip_sha": "0123456789abcdef"},
            {"dir": "runs_zz/blind_seed0", "text": "budget unreadable",
             "steps": None, "requested": None, "zip_sha": None}])
        self.assertEqual(list(got["policies"]), list(EV.ROLES))
        self.assertEqual(got["policies"]["sighted"],
                         {"label": "agent runs_zz\\sighted_seed0", "dir": "runs_zz/sighted_seed0",
                          "median": 400.0, "iqr": 20.0, "worst": 520.0, "fuel": 5000.0,
                          "peak": 850.0})
        self.assertEqual(got["policies"]["blind"]["label"], "agent (blind) runs_zz\\blind_seed0")
        self.assertEqual(got["policies"]["blind"]["dir"], "runs_zz/blind_seed0")
        self.assertEqual({r: p["median"] for r, p in got["policies"].items()},
                         dict(zip(EV.ROLES, (row[1] for row in SYN_ROWS))))
        self.assertEqual([got["policies"][r]["dir"] for r in ("baseline", "reactive",
                                                             "current_grade")],
                         [None, None, None])
        self.assertIsNone(got["thermal"])

    def test_header_without_protocol(self):
        got = EV.parse_eval_text(
            _eval_text(header="PHASE D EVALUATION -- 20 FIXED EPISODES, frozen 18 Sep 2026"))
        self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                         ("PHASE D EVALUATION", None, 20, "18 Sep 2026"))

    def test_thermal_block(self):
        got = EV.parse_eval_text(_eval_text(thermal=SYN_THERMAL))
        self.assertEqual(got["thermal"], {
            "baseline": {"median": 1500.0, "cut": 0.0}, "reactive": {"median": 1100.0, "cut": 26.7},
            "current_grade": {"median": 1050.0, "cut": 30.0},
            "sighted": {"median": 600.0, "cut": 60.0}, "blind": {"median": 1650.0, "cut": -10.0}})
        # the block adds no table row and moves no median
        self.assertEqual(got["policies"], EV.parse_eval_text(_eval_text())["policies"])

    def test_thermal_block_skips_unknown_and_unreadable_lines(self):
        lines = (SYN_THERMAL[0], ("predictive (hand)", 1200.0, 20.0),
                 ("current-grade", float("nan"), float("nan")), SYN_THERMAL[3], SYN_THERMAL[4])
        self.assertEqual(sorted(EV.parse_eval_text(_eval_text(thermal=lines))["thermal"]),
                         ["baseline", "blind", "sighted"])
        # the block ends at its first blank line
        text = _eval_text(thermal=SYN_THERMAL[:1]) + "\n" + _thermal_line(*SYN_THERMAL[1]) + "\n"
        self.assertEqual(list(EV.parse_eval_text(text)["thermal"]), ["baseline"])

    def test_forced_lines_keep_their_indented_lines(self):
        got = EV.parse_eval_text(_eval_text(provenance=SYN_FORCED))
        self.assertEqual(got["forced"], [SYN_FORCED[k] for k in (0, 1, 2, 3, 5)])
        self.assertEqual([m["dir"] for m in got["models"]],
                         ["runs_zz/sighted_seed0", "runs_zz/blind_seed0"])
        self.assertEqual((got["notes"], got["dt_notes"]), ([], []))
        self.assertEqual(list(got["policies"]), list(EV.ROLES))

    def test_model_line_with_a_drive_letter(self):
        line = "model C:\\work\\runs_zz\\blind_seed0: budget unreadable"
        self.assertEqual(EV.parse_eval_text(_eval_text(provenance=(line,)))["models"],
                         [{"dir": "C:/work/runs_zz/blind_seed0", "text": "budget unreadable",
                           "steps": None, "requested": None, "zip_sha": None}])

    def test_label_path_with_spaces_and_digits(self):
        rows = SYN_ROWS[:3] + (("agent my runs 2\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
                               SYN_ROWS[4])
        got = EV.parse_eval_text(_eval_text(rows=rows))["policies"]["sighted"]
        self.assertEqual((got["label"], got["dir"], got["median"], got["peak"]),
                         ("agent my runs 2\\sighted_seed0", "my runs 2/sighted_seed0",
                          400.0, 850.0))

    def test_line_endings_and_byte_order_mark(self):
        text = _eval_text(thermal=SYN_THERMAL)
        want = EV.parse_eval_text(text)
        self.assertEqual(want["fingerprint"]["git_dirty_plant_files"], "")
        self.assertEqual(EV.parse_eval_text(text.replace("\n", "\r\n")), want)
        self.assertEqual(EV.parse_eval_text(chr(0xFEFF) + text), want)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_bytes((chr(0xFEFF) + text.replace("\n", "\r\n")).encode("utf-8"))
            got = EV.parse_eval_file(path)
        self.assertEqual({k: v for k, v in got.items() if k != "path"}, want)

    def test_header_failure(self):
        good = _eval_text()
        for bad in ("", "\n" + good, "scenario: no header line\n",
                    good.replace(" -- scored on the 'd2' protocol, ", " ", 1),
                    good.replace("FIXED EPISODES", "EPISODES", 1),
                    good.replace(" FIXED EPISODES, frozen 22 Sep 2026", " FIXED EPISODES", 1)):
            with self.subTest(text=bad[:60]):
                self.assertEqual(self._reason(bad), "header")

    def test_missing_block(self):
        self.assertEqual(self._reason(_eval_text(block=False)), "no_fingerprint")
        other = _eval_text().replace(EV.BLOCK_TITLE, "PLANT FINGERPRINT (live)")
        self.assertEqual(self._reason(other), "no_fingerprint")

    def test_duplicate_role(self):
        second = ("agent runs_zz\\sighted_seed1", 410.0, 21.0, 530.0, 5010, 851)
        self.assertEqual(self._reason(_eval_text(rows=SYN_ROWS + (second,))), "duplicate_role")
        twice = SYN_THERMAL + (("agent runs_zz\\sighted_seed1", 610.0, 59.0),)
        self.assertEqual(self._reason(_eval_text(thermal=twice)), "duplicate_role")

    def test_no_table(self):
        self.assertEqual(self._reason(_eval_text(table=False)), "no_table")
        self.assertEqual(self._reason(_eval_text(rows=())), "no_table")
        # a row cut off after its second number, as a half-written file holds
        # it, and a label that only starts with "agent"
        unreadable = (_row(*SYN_ROWS[1])[:49],
                      ("agentsmith runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850))
        self.assertEqual(self._reason(_eval_text(rows=unreadable)), "no_table")

    def test_unknown_and_unreadable_rows_are_skipped(self):
        rows = (SYN_ROWS[0], ("predictive (hand)", 690.0, 28.0, 790.0, 4850, 866),
                _row(*SYN_ROWS[1])[:49],
                ("agentsmith runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
                SYN_ROWS[2], SYN_ROWS[3], SYN_ROWS[4])
        got = EV.parse_eval_text(_eval_text(rows=rows))["policies"]
        self.assertEqual(list(got), ["baseline", "current_grade", "sighted", "blind"])

    def test_not_evaluation_file_is_a_value_error(self):
        err = EV.NotEvaluationFile("no_table")
        self.assertIsInstance(err, ValueError)
        self.assertEqual((err.reason, str(err)), ("no_table", "no_table"))

    def test_unreadable_file_raises_what_reading_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_bytes(_eval_text().encode("utf-8") + bytes([0xFF, 0xFE]))
            with self.assertRaises(UnicodeDecodeError):
                EV.parse_eval_file(path)
            with self.assertRaises(OSError):
                EV.parse_eval_file(Path(tmp) / "zz_seed1.txt")


# ---- Task 2: app/results_provenance.py, git and the live side -----------------

# The result files of Jad's three experiments, as git names them.
SEEDED = [f"results/{prefix}_seed{seed}.txt" for prefix in REAL for seed in REAL_SEEDS]
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
LIVE_KEYS = {"python", "minor", "plant_sha", "plant_text_sha", "restart_needed",
             "derived_sha", "data_sha1", "derived_loaded_differs", "blocks", "import_errors"}
# Two file names git would quote by default, the second built from its code
# points so that this file stays ASCII.
SPACED = "notes/b c.txt"
ACCENTED = "notes/" + chr(0xE9) + "t" + chr(0xE9) + ".txt"


def _git_out(*args, cwd=ROOT):
    """git's own answer, asked directly, to compare the helper with; None on failure."""
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=60,
                           env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


def _clean(*relpaths):
    """True when git shows no change to `relpaths` in this checkout."""
    out = _git_out("status", "--porcelain", "--", *relpaths)
    return out is not None and out.strip() == ""


def _index_file():
    """This checkout's index file (a worktree keeps its own), or None."""
    rel = _git_out("rev-parse", "--git-path", "index")
    if not rel:
        return None
    path = Path(rel.strip())
    return path if path.is_absolute() else ROOT / path


def _child(code):
    """(True, stdout) of `code` run by a new interpreter from the repository
    root, or (False, the last line it wrote to stderr)."""
    r = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True,
                       timeout=900, env=CHILD_ENV)
    if r.returncode != 0:
        lines = r.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return False, lines[-1] if lines else f"exit code {r.returncode}"
    return True, r.stdout.decode("utf-8", errors="replace").strip()


class ProvenanceLiveTests(unittest.TestCase):
    """results_provenance part 1, against this checkout and against fixtures."""

    def _need_git(self):
        git = RP.Git(ROOT)
        if not git.available:
            self.skipTest(f"git is not usable here ({git.reason})")
        return git

    def test_optional_locks_are_set_before_fingerprint_is_imported(self):
        tree = ast.parse(Path(RP.__file__).read_text(encoding="utf-8"))
        order = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and "GIT_OPTIONAL_LOCKS" in ast.dump(node):
                order.append("locks")
            elif isinstance(node, ast.Import) and any(a.name == "fingerprint" for a in node.names):
                order.append("fingerprint")
        self.assertEqual(order, ["locks", "fingerprint"])
        self.assertEqual(os.environ.get("GIT_OPTIONAL_LOCKS"), "0")

    def test_git_reads_this_checkout(self):
        git = self._need_git()
        self.assertIsNone(git.reason)
        self.assertEqual(git.head_short(), _git_out("rev-parse", "--short", "HEAD").strip())
        full = _git_out("rev-parse", "HEAD").strip()
        self.assertEqual(git.resolve("HEAD"), full)
        self.assertEqual(git.resolve(full[:12]), full)
        for refused in ("--output=x", "HEAD~1", "a b", ""):
            self.assertIsNone(git.resolve(refused), refused)
        self.assertIsNone(git.resolve("f" * 40))
        self.assertTrue(git.available, "an unknown commit is an answer, not a broken git")

    def test_last_commits_equal_a_per_file_log(self):
        git = self._need_git()
        rels = [r for r in SEEDED if (ROOT / r).is_file()]
        if not rels:
            self.skipTest("no results/<prefix>_seed<N>.txt in this checkout")
        got = git.last_commits(rels)
        self.assertEqual(sorted(got), sorted(rels))
        for rel in rels:
            one = _git_out("log", "-1", "--format=%h%x09%cI", "--", rel).strip()
            short, _, date = one.partition("\t")
            self.assertEqual(got[rel], {"short": short, "date": date}, rel)

    def test_status_leaves_out_a_clean_committed_file(self):
        git = self._need_git()
        rel = "results/phase_d_seed0.txt"
        if not (ROOT / rel).is_file() or not _clean(rel):
            self.skipTest(f"{rel} is absent or changed in this checkout")
        self.assertNotIn(rel, git.status([rel]))
        self.assertEqual(git.status([]), {})
        self.assertEqual(git.last_commits([]), {})

    def test_a_missing_git_is_unavailable_and_answers_none(self):
        git = RP.Git(ROOT, exe="git-does-not-exist")
        self.assertFalse(git.available)
        self.assertEqual(git.reason, "missing")
        self.assertIsNone(git.run("--version"))
        self.assertIsNone(git.head_short())
        self.assertIsNone(git.resolve("HEAD"))
        self.assertIsNone(git.show("HEAD", "plant.py"))
        self.assertEqual(git.last_commits(["results"]), {})
        self.assertEqual(git.status(["results"]), {})
        self.assertIsNone(RP.plant_at(git, "HEAD"))
        self.assertIsNone(RP.road_sha_at(git, "HEAD"))

    def test_a_folder_outside_any_checkout_is_not_a_repo(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            ceiling = {"GIT_CEILING_DIRECTORIES": str(Path(tmp).resolve().parent)}
            with mock.patch.dict(os.environ, ceiling):
                git = RP.Git(tmp)
            self.assertEqual((git.available, git.reason), (False, "not_a_repo"))
            self.assertIsNone(git.head_short())
            gone = RP.Git(Path(tmp) / "absent")
            self.assertEqual((gone.available, gone.reason), (False, "not_a_repo"))

    def test_a_temporary_repository_reads_back(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args):
                r = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=60)
                self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", errors="replace"))
                return r.stdout.decode("utf-8", errors="replace").strip()

            git("init", "-q")
            for key, value in (("user.name", "results tab test"),
                               ("user.email", "test@example.invalid"),
                               ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
                git("config", key, value)
            (repo / "notes").mkdir()
            (repo / "a.txt").write_bytes(b"one\n")
            (repo / SPACED).write_bytes(b"two\n")
            (repo / ACCENTED).write_bytes(b"three\n")
            git("add", "-A")
            git("commit", "-q", "-m", "first")
            first = git("rev-parse", "HEAD")
            (repo / "a.txt").write_bytes(b"one, again\n")
            git("commit", "-q", "-am", "second")
            second = git("rev-parse", "HEAD")
            (repo / SPACED).write_bytes(b"two, changed\n")
            (repo / "notes" / "new.txt").write_bytes(b"four\n")

            helper = RP.Git(repo)
            self.assertTrue(helper.available, helper.reason)
            last = helper.last_commits(["a.txt", "notes"])
            self.assertEqual(sorted(last), sorted(["a.txt", SPACED, ACCENTED]))
            self.assertTrue(second.startswith(last["a.txt"]["short"]))
            self.assertTrue(first.startswith(last[SPACED]["short"]))
            self.assertTrue(first.startswith(last[ACCENTED]["short"]))
            self.assertEqual(last["a.txt"]["date"], git("log", "-1", "--format=%cI", "--", "a.txt"))
            self.assertEqual(helper.status(["a.txt", "notes"]),
                             {SPACED: "M", "notes/new.txt": "??"})
            self.assertEqual(helper.resolve(first[:10]), first)
            self.assertEqual(helper.show(first, "a.txt"), b"one\n")
            self.assertIsNone(helper.show(first, "notes/new.txt"))
            self.assertTrue(helper.available)

    def _temp_repo(self, repo):
        """`repo` made a repository with one commit (a.txt); the function that
        runs git in it, which fails the test when git fails."""

        def git(*args):
            r = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=60)
            self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", errors="replace"))
            return r.stdout.decode("utf-8", errors="replace").strip()

        git("init", "-q")
        for key, value in (("user.name", "results tab test"),
                           ("user.email", "test@example.invalid"),
                           ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
            git("config", key, value)
        (repo / "a.txt").write_bytes(b"one\n")
        git("add", "-A")
        git("commit", "-q", "-m", "first")
        return git

    def test_a_status_git_rejects_loses_git_instead_of_reading_clean(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            self._temp_repo(repo)
            (repo / "a.txt").write_bytes(b"one, changed\n")
            helper = RP.Git(repo)
            self.assertEqual(helper.status(["a.txt"]), {"a.txt": "M"})
            (repo / ".git" / "index").write_bytes(b"not an index")
            self.assertIsNone(_git_out("status", "--porcelain", cwd=repo),
                              "git must reject the damaged index for this test to mean anything")
            self.assertEqual(helper.status(["a.txt"]), {})
            self.assertEqual((helper.available, helper.reason), (False, "error"))
            # Lost for good: nothing runs again, and the reason stays.
            self.assertIsNone(helper.head_short())
            self.assertEqual(helper.last_commits(["a.txt"]), {})
            self.assertEqual((helper.available, helper.reason), (False, "error"))

    def test_a_log_git_rejects_loses_git_instead_of_reading_no_commit(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            git = self._temp_repo(repo)
            helper = RP.Git(repo)
            self.assertEqual(sorted(helper.last_commits(["a.txt"])), ["a.txt"])
            git("update-ref", "-d", "HEAD")  # the branch HEAD names has no commit now
            self.assertIsNone(_git_out("log", "--", "a.txt", cwd=repo),
                              "git must reject a log with no commit for this test to mean anything")
            self.assertEqual(helper.last_commits(["a.txt"]), {})
            self.assertEqual((helper.available, helper.reason), (False, "error"))

    def test_a_rejected_call_keeps_the_reason_git_was_already_lost_for(self):
        git = self._need_git()
        git.exe = "git-does-not-exist"  # the next call cannot even start
        self.assertEqual(git.status(["results"]), {})
        self.assertEqual((git.available, git.reason), (False, "missing"))
        self.assertEqual(git.last_commits(["results"]), {})
        self.assertEqual((git.available, git.reason), (False, "missing"))

    def test_hashes_equal_fingerprint_sha_files(self):
        sources = [(ROOT / n).read_bytes() for n in FP.PLANT_FILES]
        self.assertEqual(RP.code_hash(sources), FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(RP.byte_hash(sources), FP._sha_files(FP.PLANT_FILES, code_only=False))
        lf = [s.replace(b"\r\n", b"\n") for s in sources]
        crlf = [s.replace(b"\n", b"\r\n") for s in lf]
        self.assertEqual(RP.code_hash(lf), RP.code_hash(crlf))
        self.assertEqual(RP.byte_hash(lf), RP.byte_hash(crlf))
        commented = [lf[0] + b"\n# a comment the code hash does not see\n"] + lf[1:]
        self.assertEqual(RP.code_hash(commented), RP.code_hash(lf))
        self.assertNotEqual(RP.byte_hash(commented), RP.byte_hash(lf))
        # A file that does not parse is hashed as bytes, after the same CRLF rule.
        self.assertEqual(RP.code_hash([b"def (:\r\n"]), hashlib.sha256(b"def (:\n").hexdigest()[:16])

    def test_minor(self):
        self.assertEqual(RP.minor("3.12.10"), "3.12")
        self.assertEqual(RP.minor("3.13.2"), "3.13")
        self.assertEqual(RP.minor(platform.python_version()),
                         ".".join(platform.python_version_tuple()[:2]))
        for bad in (None, "", "None", "three"):
            self.assertIsNone(RP.minor(bad), bad)

    def test_plant_at_head_equals_the_files_on_disk(self):
        git = self._need_git()
        if not _clean(*FP.PLANT_FILES):
            self.skipTest("the plant files have uncommitted changes, so HEAD's plant is not the disk's")
        got = RP.plant_at(git, "HEAD")
        self.assertEqual(got, {"plant_sha": FP._sha_files(FP.PLANT_FILES),
                               "plant_text_sha": FP._sha_files(FP.PLANT_FILES, code_only=False)})
        self.assertEqual(RP.plant_at(git, git.resolve("HEAD")), got)
        self.assertIsNone(RP.plant_at(git, "f" * 40))

    def test_road_sha_at_head_equals_random_road(self):
        git = self._need_git()
        try:
            import random_road
        except (Exception, SystemExit) as exc:
            self.skipTest(f"random_road cannot be imported here ({type(exc).__name__})")
        if not _clean("random_road.py"):
            self.skipTest("random_road.py has uncommitted changes")
        self.assertEqual(RP.road_sha_at(git, "HEAD"), random_road.code_sha())

    def test_data_fingerprint_equals_derive_params(self):
        if importlib.util.find_spec("pandas") is None:
            self.skipTest("pandas is not installed, and derive_params imports it")
        ok, out = _child("import derive_params; print(derive_params.fingerprint()['data_sha1'])")
        if not ok:
            self.skipTest(f"derive_params could not be imported in a subprocess: {out}")
        self.assertEqual(RP.data_fingerprint(ROOT), out)

    def test_derived_sha_equals_train(self):
        missing = [m for m in ("torch", "stable_baselines3") if importlib.util.find_spec(m) is None]
        if missing:
            self.skipTest(f"{', '.join(missing)} not installed, and train imports them")
        ok, out = _child("import train; print(train.derived_sha())")
        if not ok:
            self.skipTest(f"train could not be imported in a subprocess: {out}")
        self.assertEqual(RP.derived_sha(ROOT), out)

    def test_data_hashes_on_a_temporary_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(RP.data_fingerprint(root))
            self.assertIsNone(RP.derived_sha(root))
            (root / "data").mkdir()
            samples, points = b"a,b\r\n1,2\r\n", b"x\r\n3\r\n"
            (root / "data" / "master_samples.csv").write_bytes(samples)
            (root / "data" / "master_points.csv").write_bytes(points)
            want = hashlib.sha1(b"a,b\n1,2\nx\n3\n").hexdigest()[:16]
            self.assertEqual(RP.data_fingerprint(root), want)
            path = root / "data" / "derived_params.json"
            path.write_text(json.dumps({"b": [1, 2], "a": {"c": 0.5}, "_note": "kept out"}),
                            encoding="utf-8")
            kept = json.dumps({"a": {"c": 0.5}, "b": [1, 2]}, sort_keys=True)
            self.assertEqual(RP.derived_sha(root), hashlib.sha256(kept.encode()).hexdigest()[:16])
            for text in ("[1, 2]", "{not json"):
                path.write_text(text, encoding="utf-8")
                self.assertIsNone(RP.derived_sha(root), text)

    def test_derived_loaded_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "derived_params.json").write_text(json.dumps({"a": 1, "_b": 2}),
                                                                encoding="utf-8")
            fake = types.SimpleNamespace(_CACHE={})
            with mock.patch.dict(sys.modules, {"derived": fake}):
                self.assertFalse(RP.derived_loaded_differs(root), "nothing loaded yet")
                fake._CACHE["d"] = {"a": 1, "_b": 99}
                self.assertFalse(RP.derived_loaded_differs(root), "underscore keys are not values")
                fake._CACHE["d"] = {"a": 2}
                self.assertTrue(RP.derived_loaded_differs(root))
            with mock.patch.dict(sys.modules):
                sys.modules.pop("derived", None)
                self.assertFalse(RP.derived_loaded_differs(root))

    def test_live_side(self):
        env_before = {k: os.environ.get(k) for k in ("DERIVING_PARAMS", "OMP_NUM_THREADS")}
        index = _index_file()
        index_before = index.stat().st_mtime_ns if index is not None and index.is_file() else None
        modules_before = set(sys.modules)
        live = RP.live_side(ROOT)
        self.assertEqual(set(live), LIVE_KEYS)
        self.assertEqual(live["python"], platform.python_version())
        self.assertEqual(live["minor"], RP.minor(platform.python_version()))
        self.assertEqual(live["plant_sha"], FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(live["plant_text_sha"], FP._sha_files(FP.PLANT_FILES, code_only=False))
        self.assertIs(live["restart_needed"], live["plant_sha"] != RP.IMPORT_PLANT_SHA)
        self.assertEqual(live["derived_sha"], RP.derived_sha(ROOT))
        self.assertEqual(live["data_sha1"], RP.data_fingerprint(ROOT))
        self.assertIsInstance(live["derived_loaded_differs"], bool)
        for protocol in ("phase-d", "d2"):
            module = f"fingerprint.plant_fingerprint({protocol})"
            if any(e["module"] == module for e in live["import_errors"]):
                self.assertNotIn(protocol, live["blocks"])
                continue
            block = live["blocks"][protocol]
            self.assertEqual(block["plant_sha"], live["plant_sha"])
            self.assertLessEqual(set(FP.FATAL), set(block), protocol)
        self.assertEqual({k: os.environ.get(k) for k in env_before}, env_before)
        new = set(sys.modules) - modules_before
        self.assertFalse({"derive_params", "train", "record_agents", "knock_margin"} & new)
        if index_before is not None:
            self.assertEqual(index.stat().st_mtime_ns, index_before, ".git/index was rewritten")

    def test_live_side_restart_and_import_errors(self):
        with mock.patch.object(RP, "IMPORT_PLANT_SHA", "0" * 16):
            self.assertIs(RP.live_side(ROOT, protocols=())["restart_needed"], True)

        def refuses(protocol="phase-d", **advisory):
            raise AssertionError("an import-time check failed")

        with mock.patch.object(RP.FP, "plant_fingerprint", refuses):
            live = RP.live_side(ROOT)
        self.assertEqual(live["blocks"], {})
        self.assertEqual(live["import_errors"], [
            {"module": "fingerprint.plant_fingerprint(phase-d)", "type": "AssertionError"},
            {"module": "fingerprint.plant_fingerprint(d2)", "type": "AssertionError"}])
        with mock.patch.object(RP.FP, "plant_fingerprint", side_effect=SystemExit(2)):
            got = RP.live_side(ROOT, protocols=("d2",))["import_errors"]
        self.assertEqual(got, [{"module": "fingerprint.plant_fingerprint(d2)", "type": "SystemExit"}])
        with mock.patch.object(RP.FP, "plant_fingerprint", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                RP.live_side(ROOT, protocols=("d2",))
        self.assertEqual(RP.live_side(ROOT, protocols=("phase-x",))["import_errors"],
                         [{"module": "fingerprint.plant_fingerprint(phase-x)", "type": "ValueError"}])


# ---- Task 3: app/results_provenance.py, the plant state of a file -------------

# A header title to its protocol, as Task 4 builds it from evaluate.PROTOCOLS.
TITLE_PROTOCOLS = {"PHASE D EVALUATION": "phase-d",
                   "PHASE D2 EVALUATION (randomised climb)": "d2"}
REASONS = (None, "python", "no_git_route", "dirty", "one_sided", "restart", "derived_restart",
           "protocol", "import", "derived_differs")
CLASSIFIED_KEYS = {"state", "reason", "route", "protocol", "recorded", "live", "differs",
                   "tag", "forced", "file"}
D2_FILE = "results/d2_seed0.txt"


class ProvenanceStateTests(unittest.TestCase):
    """results_provenance part 2: classify_eval, tag_for, section_provenance."""

    @classmethod
    def setUpClass(cls):
        cls.git = RP.Git(ROOT)
        cls.live = RP.live_side(ROOT)
        cls.rels = [r for r in SEEDED if (ROOT / r).is_file()]
        cls.last = cls.git.last_commits(cls.rels)
        cls.status = cls.git.status(cls.rels)

    def _parsed(self, rel=D2_FILE, **fields):
        """A real file's parse with fingerprint fields changed; None deletes one."""
        if not (ROOT / rel).is_file():
            self.skipTest(f"{rel} is not in this checkout")
        parsed = EV.parse_eval_file(ROOT / rel)
        for key, value in fields.items():
            if value is None:
                parsed["fingerprint"].pop(key, None)
            else:
                parsed["fingerprint"][key] = value
        return parsed

    def _live_like(self, parsed, **changes):
        """A live side whose blocks are `parsed`'s own block, under its Python:
        this tree as if it were the plant that file was made on."""
        fp = parsed["fingerprint"]
        live = {"python": fp["python"], "minor": RP.minor(fp["python"]),
                "plant_sha": fp["plant_sha"], "plant_text_sha": fp.get("plant_text_sha"),
                "restart_needed": False, "derived_sha": None, "data_sha1": None,
                "derived_loaded_differs": False,
                "blocks": {"phase-d": dict(fp), "d2": dict(fp)}, "import_errors": []}
        live.update(changes)
        return live

    def _classify(self, parsed, live=None, rel=D2_FILE, git=None, status=None):
        got = RP.classify_eval(parsed, self.live if live is None else live,
                               self.git if git is None else git, rel, self.last,
                               self.status if status is None else status, TITLE_PROTOCOLS)
        self.assertEqual(set(got), CLASSIFIED_KEYS)
        self.assertIn(got["state"], RP.STATES)
        self.assertIn(got["reason"], REASONS)
        self.assertIn(got["route"], (None, "same_python", "git"))
        self.assertEqual(set(got["recorded"]), {"plant_sha", "python", "git_head", "derived_sha"})
        self.assertEqual(set(got["file"]), {"rel", "commit", "changed"})
        return got

    def _need_commit(self, parsed):
        """Skip unless git here knows the commit the parsed file records."""
        if not self.git.available or self.git.resolve(parsed["fingerprint"].get("git_head")) is None:
            self.skipTest("the commit this file records is not in this clone")

    def _need_tags(self):
        if not self.git.available or any(self.git.resolve(t) is None for t in RP.TAGS):
            self.skipTest("the tags sep17-before-merge and ghassan-before-merge are not in this clone")

    def test_jads_files_are_made_on_another_plant(self):
        self._need_tags()
        if not self.rels:
            self.skipTest("no results/<prefix>_seed<N>.txt in this checkout")
        for prefix in REAL:
            for seed in REAL_SEEDS:
                rel = f"results/{prefix}_seed{seed}.txt"
                if not (ROOT / rel).is_file():
                    continue
                parsed = EV.parse_eval_file(ROOT / rel)
                got = self._classify(parsed, rel=rel)
                same_python = RP.minor(parsed["fingerprint"].get("python")) == self.live["minor"]
                with self.subTest(rel=rel):
                    self.assertEqual((got["state"], got["reason"]), ("another", None))
                    self.assertEqual(got["route"], "same_python" if same_python else "git")
                    self.assertEqual(got["tag"], "sep17-before-merge")
                    self.assertIn("plant_sha", got["differs"])
                    self.assertEqual(got["protocol"], REAL[prefix][1] or REAL[prefix][2])
                    self.assertEqual(got["recorded"]["plant_sha"], parsed["fingerprint"]["plant_sha"])
                    self.assertEqual(got["live"], {"plant_sha": self.live["plant_sha"],
                                                   "python": self.live["python"]})
                    self.assertEqual(got["file"], {"rel": rel, "commit": self.last.get(rel),
                                                   "changed": rel in self.status})
                    self.assertEqual(got["forced"], [])

    def test_title_protocols_are_evaluates(self):
        try:
            import evaluate
        except (Exception, SystemExit) as exc:
            self.skipTest(f"evaluate cannot be imported here ({type(exc).__name__})")
        self.assertEqual({header: name for name, (_episodes, header, _prefix)
                          in evaluate.PROTOCOLS.items()}, TITLE_PROTOCOLS)

    def test_forced_comes_before_everything(self):
        parsed = self._parsed(plant_sha=None)
        parsed["forced"] = ["!! runs_x/sighted_seed0: PLANT MISMATCH",
                            "     plant_sha                model 'aaaa'  live 'bbbb'"]
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]), ("forced", None, None))
        self.assertEqual(got["forced"], parsed["forced"])

    def test_not_recorded(self):
        got = self._classify(self._parsed(plant_sha=None))
        self.assertEqual((got["state"], got["reason"], got["route"]), ("not_recorded", None, None))
        self.assertIsNone(got["recorded"]["plant_sha"])

    def test_the_protocol_and_its_live_block(self):
        parsed = self._parsed("results/phase_d_seed0.txt", scenario=None)
        self.assertEqual(self._classify(parsed, rel="results/phase_d_seed0.txt")["protocol"],
                         "phase-d", "taken from the title through title_protocols")
        parsed = self._parsed(scenario=None)
        parsed["title"] = "SOME NEW EVALUATION"
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "protocol", None))
        broken = dict(self.live, blocks={k: v for k, v in self.live["blocks"].items() if k != "d2"},
                      import_errors=[{"module": "fingerprint.plant_fingerprint(d2)",
                                      "type": "AssertionError"}])
        got = self._classify(self._parsed(), broken)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "import", "d2"))
        parsed = self._parsed()
        parsed["protocol"] = "d9"
        got = self._classify(parsed, broken)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "protocol", "d9"))

    def test_another_python_with_no_route_through_git(self):
        got = self._classify(self._parsed(python="3.13.2", git_head="0" * 40))
        self.assertEqual((got["state"], got["reason"], got["route"]), ("cannot_compare", "python", None))
        got = self._classify(self._parsed(python="3.13.2", git_head=None))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "python"))
        nogit = RP.Git(ROOT, exe="git-does-not-exist")
        got = RP.classify_eval(self._parsed(python="3.13.2"), self.live, nogit, D2_FILE,
                               {}, {}, TITLE_PROTOCOLS)
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "python"))
        self.assertEqual(got["file"], {"rel": D2_FILE, "commit": None, "changed": False})

    def test_the_same_python_needs_no_git(self):
        parsed = self._parsed()
        live = self._live_like(parsed)
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        nogit = RP.Git(ROOT, exe="git-does-not-exist")
        got = RP.classify_eval(parsed, live, nogit, D2_FILE, {}, {}, TITLE_PROTOCOLS)
        self.assertEqual((got["state"], got["route"], got["differs"], got["tag"]),
                         ("another", "same_python", ["plant_sha"], None))

    def test_another_python_through_git(self):
        self._need_tags()
        parsed = self._parsed(python="3.13.2", plant_sha="0123456789abcdef")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"], got["tag"]),
                         ("another", None, "git", "sep17-before-merge"))
        self.assertIn("plant_sha", got["differs"])
        self.assertEqual(got["recorded"]["plant_sha"], "0123456789abcdef")

    def test_the_git_route_recomputes_plant_and_road(self):
        if "d2" not in self.live["blocks"] or not self.git.available:
            self.skipTest("no live d2 block, or no git, here")
        if not _clean(*FP.PLANT_FILES, "random_road.py"):
            self.skipTest("the plant files or random_road.py have uncommitted changes")
        fp = dict(self.live["blocks"]["d2"], python="3.13.2", plant_sha="0123456789abcdef",
                  git_head=self.git.resolve("HEAD"), git_dirty_plant_files="")
        fp["scenario"] = re.sub(r"road_sha=[0-9a-f]+", "road_sha=fedcba9876543210", fp["scenario"])
        parsed = {"title": "PHASE D2 EVALUATION (randomised climb)", "protocol": None,
                  "fingerprint": fp, "forced": []}
        live = dict(self.live, restart_needed=False, derived_sha=None,
                    derived_loaded_differs=False)
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"], got["route"], got["differs"]),
                         ("same_code", None, "git", []))

    def test_the_bytes_at_the_commit_must_be_the_bytes_hashed(self):
        parsed = self._parsed(python="3.13.2", plant_text_sha="0123456789abcdef")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]),
                         ("cannot_compare", "no_git_route", None))

    def test_dirty_plant_files_have_no_git_route(self):
        parsed = self._parsed(python="3.13.2", git_dirty_plant_files="engine_env.py")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]), ("cannot_compare", "dirty", None))

    def test_same_plant_code_derived_not_recorded(self):
        parsed = self._parsed()
        got = self._classify(parsed, self._live_like(parsed))
        self.assertEqual((got["state"], got["reason"], got["route"], got["differs"], got["tag"]),
                         ("same_code", None, "same_python", [], None))

    def test_same_plant(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789"))
        self.assertEqual((got["state"], got["reason"]), ("same", None))
        self.assertEqual(got["recorded"]["derived_sha"], "abcdef0123456789")

    def test_only_the_derived_constants_differ(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="0123456789abcdef"))
        self.assertEqual((got["state"], got["reason"], got["differs"]),
                         ("another", "derived_differs", []))
        self.assertEqual(got["tag"], RP.tag_for(self.git, parsed["fingerprint"]["plant_sha"]))

    def test_a_fatal_difference_and_the_derived_constants(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        live = self._live_like(parsed, derived_sha="0123456789abcdef")
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"], got["differs"]), ("another", None, ["plant_sha"]))

    def test_a_field_on_one_side_only(self):
        parsed = self._parsed()
        live = self._live_like(parsed)
        del live["blocks"]["d2"]["dtheta_deg"]
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))
        parsed = self._parsed(episodes_sha=None)
        got = self._classify(parsed, self._live_like(self._parsed()))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))
        live = self._live_like(self._parsed())
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["differs"]), ("another", ["plant_sha"]),
                         "a shared field that differs comes before a field on one side only")
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha=None))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))

    def test_a_restart_is_needed(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789",
                                                     restart_needed=True))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "restart"))

    def test_derived_constants_changed_since_start_leave_no_same(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789",
                                                     derived_loaded_differs=True))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "derived_restart"))
        self.assertEqual(got["recorded"]["derived_sha"], "abcdef0123456789")

    def test_derived_constants_changed_since_start_leave_no_same_code(self):
        parsed = self._parsed()
        got = self._classify(parsed, self._live_like(parsed, derived_loaded_differs=True))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "derived_restart"))
        self.assertIsNone(got["recorded"]["derived_sha"])

    def test_a_plant_restart_comes_before_a_derived_restart(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789",
                                                     restart_needed=True,
                                                     derived_loaded_differs=True))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "restart"))

    def test_a_fatal_difference_comes_before_a_derived_restart(self):
        parsed = self._parsed()
        live = self._live_like(parsed, derived_loaded_differs=True)
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"], got["differs"]),
                         ("another", None, ["plant_sha"]))

    def test_a_one_sided_field_comes_before_a_derived_restart(self):
        parsed = self._parsed()
        live = self._live_like(parsed, derived_loaded_differs=True)
        del live["blocks"]["d2"]["dtheta_deg"]
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))

    def test_a_changed_file_says_so(self):
        got = self._classify(self._parsed(), status={D2_FILE: "M"})
        self.assertTrue(got["file"]["changed"])
        self.assertEqual(got["file"]["commit"], self.last.get(D2_FILE))

    def test_tag_for(self):
        self._need_tags()
        sep17 = RP.plant_at(self.git, "sep17-before-merge")["plant_sha"]
        ghassan = RP.plant_at(self.git, "ghassan-before-merge")["plant_sha"]
        self.assertEqual(RP.tag_for(self.git, sep17), "sep17-before-merge")
        self.assertEqual(RP.tag_for(self.git, ghassan),
                         "sep17-before-merge" if ghassan == sep17 else "ghassan-before-merge")
        self.assertIsNone(RP.tag_for(self.git, "0" * 16))
        self.assertIsNone(RP.tag_for(self.git, None))
        self.assertIsNone(RP.tag_for(RP.Git(ROOT, exe="git-does-not-exist"), sep17))

    def test_section_provenance_of_phase_d(self):
        self._need_tags()
        per = {}
        for seed in REAL_SEEDS:
            rel = f"results/phase_d_seed{seed}.txt"
            if (ROOT / rel).is_file():
                per[seed] = self._classify(EV.parse_eval_file(ROOT / rel), rel=rel)
        if not per:
            self.skipTest("no Phase D result file in this checkout")
        got = RP.section_provenance(per)
        self.assertEqual((got["state"], got["reason"], got["tag"]),
                         ("another", None, "sep17-before-merge"))
        heads = sorted({p["recorded"]["git_head"][:7] for p in per.values()})
        self.assertEqual(got["commits"], heads)
        self.assertEqual(len(heads), 2, "Phase D's files record two commits")
        self.assertEqual(list(got["files"]), [str(s) for s in sorted(per)])
        self.assertIs(got["files"][str(min(per))], per[min(per)])

    def test_section_provenance_mixed_and_common(self):
        a = {"state": "another", "reason": None, "tag": "sep17-before-merge",
             "recorded": {"git_head": "a" * 40}}
        b = {"state": "same", "reason": None, "tag": None, "recorded": {"git_head": "b" * 40}}
        got = RP.section_provenance({1: b, 0: a})
        self.assertEqual((got["state"], got["reason"], got["tag"]), ("mixed", None, None))
        self.assertEqual(got["commits"], ["aaaaaaa", "bbbbbbb"])
        self.assertEqual(list(got["files"]), ["0", "1"])
        c = {"state": "cannot_compare", "reason": "python", "tag": None,
             "recorded": {"git_head": None}}
        got = RP.section_provenance({0: c, 3: dict(c)})
        self.assertEqual((got["state"], got["reason"], got["tag"], got["commits"]),
                         ("cannot_compare", "python", None, []))
        with self.assertRaises(ValueError):
            RP.section_provenance({})


# ---- Task 4: app/results_data.py (discovery, sections, notes, verdicts, build) ----
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

import numpy as np  # noqa: E402

import analyse_phase_d2  # noqa: E402
import evaluate  # noqa: E402
import fingerprint as FP  # noqa: E402
import run_phase_d  # noqa: E402
from app import results_data as RD  # noqa: E402
from app import results_provenance as RP  # noqa: E402

HAND_ROWS = (("baseline ECU", 0), ("reactive", 1), ("current-grade", 2))
NOTE = "note {arm}_seed{seed}: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)"
MODEL = ("model runs_x\\{arm}_seed{seed}: trained 1000 steps of 1000 requested, from step 0, "
         "buffer 1000, zip sha 0123456789abcdef")
NEVER_READ = ("phase_d_130kmh.txt", "c4_convergence.txt")


def _ar(*points):
    """Arabic text from its code points, so that this file stays ASCII (Task 1's byte check)."""
    return "".join(map(chr, points))


# The wording rules (spec 5.2 and 5.5) for every text the tab shows from the
# server: current-grade is exempt (its Arabic name is taken out of a text
# before the Arabic words are looked for), and quoted anchor lines are
# verbatim and exempt. Arabic is matched with its vowel marks dropped, so the
# order of a shadda and its vowel cannot hide a word.
AR_NEW = _ar(0x062D, 0x062F, 0x064A, 0x062B)                  # hadith: new, recent
AR_OLD = _ar(0x0642, 0x062F, 0x064A, 0x0645)                  # qadim: old
AR_UPDATED = _ar(0x0645, 0x062D, 0x062F, 0x062B)              # muhaddath: updated
AR_PREVIEW = _ar(0x0627, 0x0644, 0x0627, 0x0633, 0x062A, 0x0628, 0x0627, 0x0642)  # al-istibaq
AR_HELPS = _ar(0x064A, 0x0633, 0x0627, 0x0639, 0x062F)        # yusaid: helps
AR_NOT = _ar(0x0644, 0x0627)                                  # la: not
AR_AVAILS = _ar(0x064A, 0x0641, 0x064A, 0x062F)               # yufid: is of use
AR_INSPECTION = _ar(0x0627, 0x0644, 0x0645, 0x0639, 0x0627, 0x064A, 0x0646, 0x0629)  # al-muayana
AR_AVAILS_F = _ar(0x062A, 0x0641, 0x064A, 0x062F)             # tufid: is of use (feminine)
AR_CURRENT = _ar(0x062D, 0x0627, 0x0644, 0x064A)              # hali: current
AR_THE = _ar(0x0627, 0x0644)                                  # al-: the
AR_MAYL = _ar(0x0627, 0x0644, 0x0645, 0x064A, 0x0644)         # al-mayl: the grade, the slope
AR_SITUATION = _ar(0x0627, 0x0644, 0x0648, 0x0636, 0x0639)    # al-wad: the situation
_AR_BLOCK = f"[{chr(0x0600)}-{chr(0x06FF)}]"
_AR_MARKS = re.compile(f"[{chr(0x064B)}-{chr(0x0652)}]")
_AR_PREFIX = "|".join((_ar(0x0627, 0x0644), _ar(0x0648), _ar(0x0628)))       # al-, wa-, bi-
_AR_SUFFIX = "|".join((_ar(0x0629), _ar(0x0648, 0x0646), _ar(0x064A, 0x0646), _ar(0x0627, 0x062A)))
# current-grade's Arabic name, "al-mayl al-hali": the one place the word for current may stand
_AR_EXEMPT = re.compile(AR_MAYL + r"\s+" + AR_THE + AR_CURRENT)
BANNED = (
    re.compile(r"\b(?:current(?!-grade)|stale|outdated|fresh|up[ -]to[ -]date)\b", re.I),
    re.compile(r"preview (?:helps|does not help|doesn't help)|adds nothing measurable"
               r"|not from seeing ahead|replicat|pooled", re.I),
    re.compile(f"(?<!{_AR_BLOCK})(?:{_AR_PREFIX})?(?:{AR_NEW}|{AR_OLD}|{AR_UPDATED})"
               f"(?:{_AR_SUFFIX})?(?!{_AR_BLOCK})"),
    # The Arabic word for current. No word boundary, unlike the three words
    # above, which sit inside common words (updating, presenting): this one
    # must also catch its feminine form, its adverb and a conjunction or a
    # preposition in front of it, and the tab has no use for a longer word
    # that contains it.
    re.compile(AR_CURRENT),
    re.compile("|".join((f"{AR_PREVIEW} {AR_HELPS}", f"{AR_HELPS} {AR_PREVIEW}",
                         f"{AR_PREVIEW} {AR_NOT} {AR_AVAILS}", f"{AR_NOT} {AR_AVAILS} {AR_PREVIEW}",
                         f"{AR_PREVIEW} {AR_NOT} {AR_HELPS}",
                         f"{AR_INSPECTION} {AR_NOT} {AR_AVAILS_F}"))),
)


def _banned(text):
    """True when `text` breaks a wording rule (Arabic vowel marks dropped first,
    then current-grade's Arabic name taken out, so that only a use of the word
    for current outside that name is found)."""
    bare = _AR_EXEMPT.sub(" ", _AR_MARKS.sub("", text))
    return any(rx.search(bare) for rx in BANNED)


def _texts(x, path=()):
    """(where, text) for every string in an answer, quoted verdict lines left out."""
    if isinstance(x, dict):
        for key, value in x.items():
            if not (key == "lines" and "verdict" in path):
                yield from _texts(value, path + (str(key),))
    elif isinstance(x, list):
        for value in x:
            yield from _texts(value, path)
    elif isinstance(x, str):
        yield "/".join(path), x


def _row_values(seed, k):
    """(median, IQR, worst, fuel, peak) made from the seed and the row, so that
    no damage figure is typed in this file (verify_docs.py reads it)."""
    return (1000.0 + 10 * k + seed, 10.0, 2000.0 + k, 4000.0 + k, 1100.0 + k)


def _data_text(seed, arms=("sighted", "blind"), *, thermal=False, header=None, block=True,
               table=True, models=True):
    """One results/<prefix>_seed<N>.txt in evaluate.py's own layout (its main()).

    The header, scenario, trigger and fingerprint block are copied from the
    real results/c4_seed0.txt, so the provenance code reads a real block.
    """
    real = (RD.RESULTS / "c4_seed0.txt").read_text(encoding="utf-8").splitlines()
    head = real[:real.index("-" * 62) + 1]
    if header is not None:
        head[0] = header
    if not block:
        head = head[:next(i for i, line in enumerate(head) if line.startswith("--- "))]
    lines = list(head)
    for arm in arms:
        lines.append(NOTE.format(arm=arm, seed=seed))
        if models:
            lines.append(MODEL.format(arm=arm, seed=seed))
    if table:
        rows = [(label, _row_values(seed, k)) for label, k in HAND_ROWS]
        rows += [(("agent (blind)" if arm == "blind" else "agent") + f" runs_x\\{arm}_seed{seed}",
                  _row_values(seed, 3 if arm == "sighted" else 4)) for arm in arms]
        lines += ["", f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
                      f"{'fuel med':>10}{'peak C':>9}", "-" * 77]
        lines += [f"{label:<28}{v[0]:>12.1f}{v[1]:>9.1f}{v[2]:>9.1f}{v[3]:>10.0f}{v[4]:>9.0f}"
                  for label, v in rows]
        lines.append("-" * 77)
        if thermal:
            lines += ["", "  WITHOUT THE KNOCK TERM (turbine + oil only; the knock model is untested)"]
            lines += [f"    {label:<26} thermal med {v[0] - 5:8.1f}   thermal cut {2.0 + i:5.1f} %"
                      for i, (label, v) in enumerate(rows)]
    return "\n".join(lines) + "\n"


def _found_verdict(prefix, root=None):
    """A stand-in for app.agent_catalog.verdict with every anchor found."""
    return {"state": "found", "lines": [{"key": "result", "file": "X.txt", "line": 1,
                                         "text": "RESULT"}],
            "missing": [], "short": {"ar": "a reading (ar)", "en": "a reading"},
            "cells": [{"cell": "INCONCLUSIVE", "gloss": {"ar": "a gloss (ar)", "en": "a gloss"}}]}


class DataTests(unittest.TestCase):
    """app/results_data.py on a temporary tree and on the real one (spec 4.1, 4.4, 5.6, 9)."""

    @classmethod
    def setUpClass(cls):
        # analyse_phase_d.parse leaves each file it reads to the garbage
        # collector, and unittest shows that as a ResourceWarning per file.
        cls.quiet = warnings.catch_warnings()
        cls.quiet.__enter__()
        warnings.filterwarnings("ignore", category=ResourceWarning, module="analyse_phase_d")
        # One real build first: every module build() imports is then loaded, so
        # the mock.patch.dict(sys.modules, ...) tests below remove nothing else.
        cls.real = RD.build(RD.RESULTS, RD.ROOT)
        cls.live = RP.live_side(RD.ROOT)
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        res = base / "results"
        (res / "nested").mkdir(parents=True)
        files = {
            "newexp_seed0.txt": _data_text(0, thermal=True),
            "newexp_seed1.txt": _data_text(1),
            "newexp_seed2.txt": _data_text(2, arms=("sighted",)),
            "Bad-Name_seed0.txt": _data_text(0),
            "hdr_seed0.txt": _data_text(0, header="not an evaluate.py header"),
            "noblock_seed0.txt": _data_text(0, block=False),
            "d2_seed0.txt": "",
            "c4_seed0.txt": _data_text(0, table=False),
            "nested/zz_seed0.txt": _data_text(0),
        }
        for name, text in files.items():
            (res / name).write_text(text, encoding="utf-8")
        (res / "bytes_seed0.txt").write_bytes(b"\xff\xfe\x00not utf-8\n")
        for name in NEVER_READ:
            (res / name).write_text((RD.RESULTS / name).read_text(encoding="utf-8"),
                                    encoding="utf-8")
        cls.tree = RD.build(res, base, live=cls.live)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        cls.quiet.__exit__(None, None, None)

    def section(self, built, prefix):
        return next(s for s in built["sections"] if s["prefix"] == prefix)

    # ---- the temporary tree ---------------------------------------------
    def test_discovery_lists_every_file_it_does_not_read(self):
        got = sorted((n["path"], n["reason"], n["type"]) for n in self.tree["not_read"])
        self.assertEqual(got, [
            ("results/Bad-Name_seed0.txt", "name", None),
            ("results/bytes_seed0.txt", "unreadable", "UnicodeDecodeError"),
            ("results/c4_seed0.txt", "no_table", None),
            ("results/d2_seed0.txt", "header", None),
            ("results/hdr_seed0.txt", "header", None),
            ("results/noblock_seed0.txt", "no_fingerprint", None),
        ])
        text = json.dumps(self.tree)
        for name in NEVER_READ + ("zz_seed0",):
            self.assertNotIn(name, text, f"{name} must never be a candidate")

    def test_two_files_naming_one_seed_are_both_listed_and_neither_is_read(self):
        # Spec 4.1: an unpaired or unreadable seed is listed, never dropped
        # silently. A seed written with and without a leading zero is one seed
        # named twice: the names cannot say which file is the experiment's, and
        # showing either would hide the other.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            res = base / "results"
            res.mkdir()
            for name, seed in (("newexp_seed0.txt", 0), ("newexp_seed7.txt", 7),
                               ("newexp_seed07.txt", 7)):
                (res / name).write_text(_data_text(seed), encoding="utf-8")
            got = RD.build(res, base, live=self.live)
        listed = sorted((n["path"], n["reason"], n["type"]) for n in got["not_read"])
        self.assertEqual(listed, [("results/newexp_seed07.txt", "duplicate_seed", None),
                                  ("results/newexp_seed7.txt", "duplicate_seed", None)])
        sec = self.section(got, "newexp")
        self.assertEqual([s["seed"] for s in sec["seeds"]], [0])
        self.assertEqual(sec["unpaired"], [])
        self.assertEqual(sorted(sec["provenance"]["files"]), ["0"])
        text = json.dumps(sec)
        for name in ("newexp_seed7.txt", "newexp_seed07.txt"):
            self.assertNotIn(name, text, f"{name} must not be read")

    def test_a_prefix_whose_every_seed_is_named_twice_is_missing_or_absent(self):
        # The ruling on Task 4's review: such a prefix is left out of discovery,
        # so a known experiment reads as its usual missing section and an
        # unknown one has no section; the not-read list says why in both cases.
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            res = base / "results"
            res.mkdir()
            for name, seed in (("d2_seed3.txt", 3), ("d2_seed03.txt", 3),
                               ("zz_seed1.txt", 1), ("zz_seed01.txt", 1)):
                (res / name).write_text(_data_text(seed), encoding="utf-8")
            got = RD.build(res, base, live=self.live)
        self.assertEqual(sorted((n["path"], n["reason"], n["type"]) for n in got["not_read"]), [
            ("results/d2_seed03.txt", "duplicate_seed", None),
            ("results/d2_seed3.txt", "duplicate_seed", None),
            ("results/zz_seed01.txt", "duplicate_seed", None),
            ("results/zz_seed1.txt", "duplicate_seed", None)])
        self.assertEqual([s["prefix"] for s in got["sections"]], ["phase_d", "d2", "c4"])
        d2 = self.section(got, "d2")
        self.assertEqual(d2["state"], "unavailable")
        self.assertEqual(d2["error"], {
            "kind": "missing", "file": "results/d2_seed<N>.txt",
            "command": RD.EVAL_COMMAND.replace("<prefix>", "d2"), "type": None, "module": None})

    def test_sections_in_order_known_first(self):
        self.assertEqual([s["prefix"] for s in self.tree["sections"]],
                         ["phase_d", "d2", "c4", "newexp"])
        self.assertEqual([s["id"] for s in self.tree["sections"]],
                         ["exp-phase_d", "exp-d2", "exp-c4", "exp-newexp"])

    def test_each_failure_kind_costs_only_its_section(self):
        phase_d = self.section(self.tree, "phase_d")
        self.assertEqual(phase_d["state"], "unavailable")
        self.assertEqual(phase_d["name"], run_phase_d.CLOSED_PREFIX["phase_d"])
        self.assertEqual(phase_d["error"], {
            "kind": "missing", "file": "results/phase_d_seed<N>.txt",
            "command": RD.EVAL_COMMAND.replace("<prefix>", "phase_d"), "type": None,
            "module": None})
        for prefix in ("d2", "c4"):
            sec = self.section(self.tree, prefix)
            self.assertEqual(sec["state"], "unavailable", prefix)
            self.assertEqual(sec["error"], {
                "kind": "read", "file": f"results/{prefix}_seed0.txt", "command": None,
                "type": "NotEvaluationFile", "module": None}, prefix)
        self.assertEqual(self.section(self.tree, "newexp")["state"], "ok")

    def test_a_new_prefix_appears_by_itself(self):
        sec = self.section(self.tree, "newexp")
        self.assertIsNone(sec["name"])
        self.assertFalse(sec["known"])
        self.assertEqual(sec["order"], RD.UNKNOWN_ORDER)
        self.assertIsNone(sec["continues"])
        self.assertEqual(sec["protocol"], "d2")
        self.assertEqual([s["seed"] for s in sec["seeds"]], [0, 1])
        self.assertEqual(sec["unpaired"], [{"seed": 2, "file": "results/newexp_seed2.txt",
                                            "have": ["baseline", "reactive", "current_grade",
                                                     "sighted"]}])
        for s in sec["seeds"]:
            self.assertEqual(s["diff"], s["blind"]["median"] - s["sighted"]["median"])
            self.assertEqual(s["budget"], {"steps": 1000, "requested": 1000})
            self.assertEqual(s["file"], f"results/newexp_seed{s['seed']}.txt")
        self.assertEqual(sec["seeds"][0]["sighted"]["dir"], "runs_x/sighted_seed0")
        self.assertIsNone(sec["seeds"][0]["baseline"]["dir"])
        self.assertEqual(sec["mei"], analyse_phase_d2.MEI)
        self.assertFalse(sec["mei_after_result"])
        self.assertEqual(sec["thermal_recorded"], "some")
        self.assertEqual(set(sec["seeds"][0]["thermal"]), set(RD.E.ROLES))
        self.assertIsNone(sec["seeds"][1]["thermal"])
        self.assertEqual(sorted(sec["provenance"]["files"]), ["0", "1", "2"])
        self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis", "state": "pass",
                                          "detail": None}])
        self.assertIsNone(sec["error"])

    def test_an_unknown_prefix_gets_only_what_its_files_record(self):
        sec = self.section(self.tree, "newexp")
        self.assertEqual(sec["notes"], [
            {"key": "budget_from_file", "values": {"steps": 1000}},
            {"key": "dt_mismatch", "values": {"train_dt": 0.2, "eval_dt": 1.0}},
            {"key": "knock_model", "values": {}},
            {"key": "turbine_modelled", "values": {}},
            {"key": "no_other_notes", "values": {}},
        ])

    def test_no_verdict_shows_no_short_line(self):
        verdict = self.section(self.tree, "newexp")["verdict"]
        self.assertEqual(verdict["state"], "none")
        self.assertIsNone(verdict["short"], "the 'none' text says nothing here is a result")
        self.assertEqual((verdict["lines"], verdict["cells"], verdict["missing"]), ([], [], []))

    def test_temporary_tree_has_no_git(self):
        self.assertEqual(self.tree["built"]["git"], "unavailable")
        self.assertIsNone(self.tree["built"]["head"])
        self.assertEqual(self.tree["import_failures"], [])

    def test_a_git_that_fails_leaves_no_commit_fact(self):
        # The controller's ruling on Task 2's review: build() asks git status
        # before git log, so a status git rejects loses git before any commit
        # is read, and no file shows a last commit beside "git unavailable".
        if _git_out("--version") is None:
            self.skipTest("git is not usable here")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            res = base / "results"
            res.mkdir()
            for seed in (0, 1):
                (res / f"newexp_seed{seed}.txt").write_text(_data_text(seed), encoding="utf-8")
            for args in (("init", "-q"), ("config", "user.name", "results tab test"),
                         ("config", "user.email", "test@example.invalid"),
                         ("config", "commit.gpgsign", "false"),
                         ("config", "core.autocrlf", "false"),
                         ("add", "-A"), ("commit", "-q", "-m", "first")):
                self.assertIsNotNone(_git_out(*args, cwd=base), args)
            (base / ".git" / "index").write_bytes(b"not an index")
            self.assertIsNone(_git_out("status", "--porcelain", cwd=base),
                              "git must reject the damaged index for this test to mean anything")
            got = RD.build(res, base, live=self.live)
        self.assertEqual(got["built"]["git"], "unavailable")
        # Spec 6.3: with git unavailable the git facts are omitted, the head
        # of the checkout among them, even when it was read before git was lost.
        self.assertIsNone(got["built"]["head"])
        files = self.section(got, "newexp")["provenance"]["files"]
        self.assertEqual(sorted(files), ["0", "1"])
        for seed, entry in files.items():
            self.assertIsNone(entry["file"]["commit"], seed)

    # ---- failures --------------------------------------------------------
    def test_a_reader_raising_system_exit_costs_one_section(self):
        def verdict(prefix, root=None):
            if prefix == "d2":
                raise SystemExit("a reader gave up")
            return _found_verdict(prefix)

        got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=verdict)
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "unavailable", "ok"])
        self.assertEqual(self.section(got, "d2")["error"], {
            "kind": "build", "file": None, "command": None, "type": "SystemExit",
            "module": None})

    def test_keyboard_interrupt_is_not_caught(self):
        def verdict(prefix, root=None):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=verdict)

    def test_catalog_import_failure_is_one_line_and_no_verdict(self):
        with mock.patch.dict(sys.modules, {"app.agent_catalog": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live)
        self.assertEqual(got["import_failures"],
                         [{"module": "app.agent_catalog", "type": "ModuleNotFoundError"}])
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "ok", "ok"])
        for sec in got["sections"]:
            self.assertEqual(sec["verdict"], {"state": "unavailable"}, sec["prefix"])

    def test_a_section_says_which_module_it_needs(self):
        with mock.patch.dict(sys.modules, {"analyse_phase_d2": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"],
                         [{"module": "analyse_phase_d2", "type": "ModuleNotFoundError"}])
        for sec in got["sections"]:
            self.assertEqual(sec["state"], "unavailable", sec["prefix"])
            self.assertEqual(sec["error"]["kind"], "module")
            self.assertEqual(sec["error"]["module"], "analyse_phase_d2")

    def test_without_analyse_phase_d_the_check_is_not_compared(self):
        with mock.patch.dict(sys.modules, {"analyse_phase_d": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"],
                         [{"module": "analyse_phase_d", "type": "ModuleNotFoundError"}])
        for sec in got["sections"]:
            self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis",
                                              "state": "not_compared", "detail": None}])

    def test_live_side_import_errors_reach_the_tab(self):
        live = dict(self.live, blocks={}, import_errors=[
            {"module": "fingerprint.plant_fingerprint(phase-d)", "type": "AssertionError"},
            {"module": "fingerprint.plant_fingerprint(d2)", "type": "AssertionError"}])
        got = RD.build(RD.RESULTS, RD.ROOT, live=live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"], live["import_errors"])
        for sec in got["sections"]:
            self.assertEqual(sec["provenance"]["state"], "cannot_compare", sec["prefix"])
            self.assertEqual(sec["provenance"]["reason"], "import", sec["prefix"])

    def test_nan_becomes_null(self):
        parse = RD.E.parse_eval_file

        def with_nan(path):
            out = parse(path)
            if Path(path).name == "c4_seed3.txt":
                out["policies"]["sighted"]["median"] = float("nan")
            return out

        with mock.patch.object(RD.E, "parse_eval_file", with_nan):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        seed3 = next(s for s in self.section(got, "c4")["seeds"] if s["seed"] == 3)
        self.assertIsNone(seed3["sighted"]["median"])
        self.assertIsNone(seed3["diff"])
        check = self.section(got, "c4")["checks"][0]
        self.assertEqual(check["state"], "fail")
        self.assertIn("results/c4_seed3.txt", check["detail"])
        json.dumps(got, allow_nan=False)

    def test_jsonable(self):
        got = RD.jsonable({"a": float("nan"), 1: (np.float32(2.5), np.int64(3), np.bool_(True),
                                                   float("inf"), None, "x"),
                           "arr": np.array([1.0, np.nan])})
        self.assertEqual(got, {"a": None, "1": [2.5, 3, True, None, None, "x"],
                               "arr": [1.0, None]})
        self.assertIs(RD.jsonable(True), True)
        with self.assertRaises(TypeError):
            RD.jsonable(object())

    # ---- the real tree ---------------------------------------------------
    def test_real_tree_three_sections_in_order(self):
        secs = self.real["sections"]
        self.assertEqual([s["prefix"] for s in secs], ["phase_d", "d2", "c4"])
        self.assertEqual([s["state"] for s in secs], ["ok", "ok", "ok"])
        for sec in secs:
            self.assertEqual(sec["name"], run_phase_d.CLOSED_PREFIX[sec["prefix"]])
            self.assertTrue(sec["known"])
            self.assertEqual([s["seed"] for s in sec["seeds"]], list(range(8)))
            self.assertEqual(sec["unpaired"], [])
            self.assertEqual(sec["thermal_recorded"], "none")
            self.assertEqual(sec["episodes"], len(evaluate.EPISODES))
            self.assertTrue(sec["scenario"].startswith("scenario: "))
            self.assertEqual(sec["mei"], analyse_phase_d2.MEI)
        self.assertEqual([s["protocol"] for s in secs], ["phase-d", "d2", "d2"])
        self.assertEqual([s["mei_after_result"] for s in secs], [True, False, False])
        self.assertEqual([s["continues"] for s in secs], [None, None, "d2"])
        self.assertFalse([n for n in self.real["not_read"]
                          if n["path"].split("/")[-1].startswith(("phase_d_", "d2_", "c4_"))])

    def test_real_tree_diffs_equal_the_analysis(self):
        for sec in self.real["sections"]:
            rows, incomplete = analyse_phase_d2.load(sec["prefix"])
            self.assertEqual(incomplete, [], sec["prefix"])
            self.assertEqual([(s["seed"], s["diff"]) for s in sec["seeds"]],
                             [(seed, diff) for seed, _, diff in rows], sec["prefix"])

    def test_real_tree_checks_pass(self):
        for sec in self.real["sections"]:
            self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis",
                                              "state": "pass", "detail": None}], sec["prefix"])

    def test_real_tree_is_made_on_another_plant(self):
        for sec in self.real["sections"]:
            prov = sec["provenance"]
            self.assertEqual(prov["state"], "another", sec["prefix"])
            self.assertTrue(prov["commits"], sec["prefix"])
            self.assertEqual(sorted(prov["files"]), [str(k) for k in range(8)])

    def test_real_tree_notes(self):
        import analyse_c4
        keys = {s["prefix"]: [n["key"] for n in s["notes"]] for s in self.real["sections"]}
        tail = ["dt_mismatch", "no_thermal_only", "knock_model", "turbine_modelled"]
        self.assertEqual(keys["phase_d"], RD.KNOWN["phase_d"]["notes"] + tail)
        self.assertEqual(keys["d2"], RD.KNOWN["d2"]["notes"] + tail)
        self.assertEqual(keys["c4"], RD.KNOWN["c4"]["notes"] + ["budget_from_file"] + tail)
        # Spec 5.4: C4's budget is "not converged", and only C4's
        self.assertIn("c4_not_converged", keys["c4"])
        self.assertEqual([p for p, found in keys.items() if "c4_not_converged" in found], ["c4"])
        notes = {n["key"]: n["values"] for n in self.section(self.real, "c4")["notes"]}
        self.assertEqual(notes["budget_from_file"], {"steps": analyse_c4.C4_STEPS})
        self.assertEqual(notes["dt_mismatch"], {"train_dt": 0.2, "eval_dt": 1.0})
        for s in self.section(self.real, "c4")["seeds"]:
            self.assertEqual(s["budget"], {"steps": analyse_c4.C4_STEPS,
                                           "requested": analyse_c4.C4_STEPS})
        for prefix in ("phase_d", "d2"):
            self.assertEqual([s["budget"] for s in self.section(self.real, prefix)["seeds"]],
                             [None] * 8, prefix)

    def test_real_tree_verdicts_are_quoted(self):
        from app import agent_catalog
        for sec in self.real["sections"]:
            want = agent_catalog.verdict(sec["prefix"])
            self.assertEqual(sec["verdict"], {k: want[k] for k in
                                              ("state", "lines", "cells", "missing", "short")})
            self.assertEqual(sec["verdict"]["state"], "found", sec["prefix"])

    def test_real_tree_serialises_strictly(self):
        json.dumps(self.real, allow_nan=False)
        built = self.real["built"]
        self.assertEqual(set(self.real), {"built", "import_failures", "sections", "not_read"})
        self.assertEqual(self.real["import_failures"], [])
        self.assertEqual(built["python"], platform.python_version())
        self.assertEqual(built["plant_sha"], FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(built["git"], "ok")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RD.ROOT,
                              capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout.strip()
        self.assertEqual(built["head"], head)
        self.assertIsInstance(built["elapsed_ms"], int)
        print(f"\n    build() on the real tree: {built['elapsed_ms']} ms", file=sys.stderr)

    def test_build_leaves_no_trace(self):
        # --git-path, because in a worktree .git is a file and the index lives elsewhere
        where = subprocess.run(["git", "rev-parse", "--git-path", "index"], cwd=RD.ROOT,
                               capture_output=True, text=True, timeout=60,
                               env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout.strip()
        index = Path(where) if Path(where).is_absolute() else RD.ROOT / where
        self.assertTrue(index.is_file(), index)
        env = {k: os.environ.get(k) for k in ("DERIVING_PARAMS", "OMP_NUM_THREADS")}
        before = (index.stat().st_mtime_ns, index.stat().st_size)
        RD.build(RD.RESULTS, RD.ROOT)
        self.assertEqual((index.stat().st_mtime_ns, index.stat().st_size), before,
                         ".git/index moved during a build")
        self.assertEqual({k: os.environ.get(k) for k in env}, env)

    def test_without_git_only_the_git_facts_go(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["built"]["git"], "unavailable")
        self.assertIsNone(got["built"]["head"])
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "ok", "ok"])
        for sec, real in zip(got["sections"], self.real["sections"]):
            self.assertEqual(sec["seeds"], real["seeds"], sec["prefix"])
            self.assertEqual(sec["provenance"]["state"], "another", sec["prefix"])
            self.assertIsNone(sec["provenance"]["tag"], sec["prefix"])
            for item in sec["provenance"]["files"].values():
                self.assertIsNone(item["file"]["commit"], sec["prefix"])

    def test_wording_of_the_answer_and_of_the_quoted_verdicts(self):
        bad = ("an up to date figure", "a stale file", "the current plant", "pooled seeds",
               "preview does not help",
               _ar(0x0646, 0x062A, 0x064A, 0x062C, 0x0629) + " " + AR_OLD + _ar(0x0629),  # an old result
               _ar(0x0645, 0x062D, 0x062F, 0x064E, 0x0651, 0x062B),                      # updated, marked
               f"{AR_PREVIEW} {AR_NOT} {AR_AVAILS}",
               AR_SITUATION + " " + AR_THE + AR_CURRENT,                                 # the current situation
               AR_THE + AR_CURRENT + _ar(0x0629),                                        # the current, feminine
               AR_THE + AR_CURRENT + _ar(0x0651, 0x064F),                                # the current, marked
               AR_CURRENT + _ar(0x0627, 0x064B),                                         # currently
               AR_MAYL + " " + AR_THE + AR_CURRENT + " " + _ar(0x0648) + AR_SITUATION
               + " " + AR_THE + AR_CURRENT)             # current-grade, then the current situation
        fine = ("current-grade", "Current-grade median",
                _ar(0x062A) + AR_NEW + " " + _ar(0x0627, 0x0644, 0x0645, 0x0644, 0x0641),  # updating the file
                AR_MAYL + " " + AR_THE + AR_CURRENT,                                       # current-grade
                _ar(0x0628, 0x0627, 0x0644, 0x0645, 0x064E, 0x064A, 0x0652, 0x0644) + " "
                + AR_THE + AR_CURRENT + _ar(0x0651),                                       # with current-grade, marked
                _ar(0x062D, 0x0627, 0x0644, 0x0629) + " " + _ar(0x0627, 0x0644, 0x0645, 0x0644, 0x0641))  # the file's state
        self.assertEqual([text for text in bad if not _banned(text)], [])
        self.assertEqual([text for text in fine if _banned(text)], [])
        from app import agent_catalog
        texts = list(_texts(self.real))
        texts += [(f"SHORT_VERDICT[{k}][{lang}]", v[lang])
                  for k, v in agent_catalog.SHORT_VERDICT.items() for lang in ("ar", "en")]
        texts += [(f"GLOSS[{k}][{lang}]", v[lang])
                  for k, v in agent_catalog.GLOSS.items() for lang in ("ar", "en")]
        self.assertGreater(len(texts), 100)
        self.assertEqual([(where, text) for where, text in texts if _banned(text)], [])

    def test_known_matches_the_closed_prefixes(self):
        self.assertEqual(set(RD.KNOWN), set(run_phase_d.CLOSED_PREFIX))

    def test_imports_stay_light(self):
        """Importing results_data loads no agent code; a build never imports the
        four modules spec 5.2 forbids, nor sets DERIVING_PARAMS."""
        code = ("import json, os, sys\n"
                "import app.results_data as RD\n"
                "heavy = ('app.agent', 'evaluate', 'engine_env', 'random_road')\n"
                "first = sorted(m for m in sys.modules if m.startswith(heavy))\n"
                "RD.build(RD.RESULTS, RD.ROOT)\n"
                "banned = ('derive_params', 'record_agents', 'knock_margin', 'train')\n"
                "print(json.dumps([first, sorted(m for m in banned if m in sys.modules),\n"
                "                  os.environ.get('DERIVING_PARAMS')]))\n")
        run = subprocess.run([sys.executable, "-c", code], cwd=RD.ROOT, capture_output=True,
                             text=True, timeout=300,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        first, banned, deriving = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(first, [])
        self.assertEqual(banned, [])
        self.assertIsNone(deriving)


# ---- Task 5: app/results_api.py and its wiring in app/server.py ---------------
import ast  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402
import unittest  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import results_api as RA  # noqa: E402

APP_DIR = Path(RA.__file__).resolve().parent
LOCAL = {"host": "127.0.0.1:8000"}
TOP_KEYS = {"built", "import_failures", "sections", "not_read"}
REFUSAL = "refused: this page answers 127.0.0.1 and localhost only"


def _results_client(build=None):
    app = FastAPI()
    RA.mount_results(app, build=build)
    return app, TestClient(app)


class RouteTests(unittest.TestCase):
    """app/results_api.py: two GET routes, the Host guard, the lock, no-store (spec 6.1)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.page = Path(tmp.name) / "results.html"
        self.page.write_text("<!doctype html><title>a results page</title>\n", encoding="utf-8")
        patcher = mock.patch.object(RA, "PAGE", self.page)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_page_answers_this_machine_with_or_without_a_port(self):
        _, client = _results_client(build=lambda: {})
        for host in ("127.0.0.1:8000", "localhost:8765", "localhost", "127.0.0.1"):
            r = client.get("/results", headers={"host": host})
            self.assertEqual(r.status_code, 200, host)
            self.assertEqual(r.headers.get("cache-control"), "no-store", host)
            self.assertTrue(r.headers.get("content-type", "").startswith("text/html"), host)
            self.assertEqual(r.text, self.page.read_text(encoding="utf-8"), host)

    def test_the_page_is_read_on_every_request(self):
        _, client = _results_client(build=lambda: {})
        self.page.write_text("<!doctype html><title>changed</title>\n", encoding="utf-8")
        self.assertIn("changed", client.get("/results", headers=LOCAL).text)

    def test_a_foreign_host_is_refused_on_both_routes(self):
        calls = []
        _, client = _results_client(build=lambda: calls.append(1) or {})
        for host in ("evil.example:8000", "127.0.0.1.evil.example", "localhost.evil.example:8000",
                     "127.0.0.2:8000", "localhost:123456", "testserver"):
            for path in ("/results", "/api/results"):
                r = client.get(path, headers={"host": host})
                self.assertEqual(r.status_code, 403, (host, path))
                self.assertEqual(r.headers.get("cache-control"), "no-store", (host, path))
                self.assertEqual(r.text, REFUSAL, (host, path))
        self.assertEqual(calls, [], "a refused request must not build")
        self.assertFalse(RA.host_ok(types.SimpleNamespace(headers={})))

    def test_only_get(self):
        app, client = _results_client(build=lambda: {})
        for path in ("/results", "/api/results"):
            self.assertEqual(client.post(path, headers=LOCAL).status_code, 405, path)
        added = {r.path: set(r.methods) for r in app.routes
                 if getattr(r, "path", None) in ("/results", "/api/results")}
        self.assertEqual(added, {"/results": {"GET"}, "/api/results": {"GET"}})

    def test_the_answer_is_the_build_with_no_store(self):
        body = {"built": {"head": None}, "import_failures": [], "sections": [], "not_read": []}
        _, client = _results_client(build=lambda: body)
        r = client.get("/api/results", headers=LOCAL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(r.json(), body)

    def test_the_default_build_answers_the_contract_keys(self):
        _, client = _results_client()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ResourceWarning, module="analyse_phase_d")
            r = client.get("/api/results", headers={"host": "localhost"})
        self.assertEqual(r.status_code, 200, r.text[:300])
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(set(r.json()), TOP_KEYS)

    def test_a_failing_build_is_a_fixed_500(self):
        for exc in (RuntimeError("secret detail"), SystemExit("secret detail")):
            def boom(exc=exc):
                raise exc

            _, client = _results_client(build=boom)
            r = client.get("/api/results", headers=LOCAL)
            self.assertEqual(r.status_code, 500, type(exc).__name__)
            self.assertEqual(r.headers.get("cache-control"), "no-store")
            self.assertEqual(r.json(), {"detail": f"results failed: {type(exc).__name__}"})
            self.assertNotIn("secret", r.text)

    def test_one_build_at_a_time(self):
        state = {"inside": 0, "peak": 0}
        guard = threading.Lock()

        def slow():
            with guard:
                state["inside"] += 1
                state["peak"] = max(state["peak"], state["inside"])
            time.sleep(0.2)
            with guard:
                state["inside"] -= 1
            return {}

        app, _ = _results_client(build=slow)
        endpoint = next(r.endpoint for r in app.routes
                        if getattr(r, "path", None) == "/api/results")
        request = types.SimpleNamespace(headers=dict(LOCAL))
        threads = [threading.Thread(target=endpoint, args=(request,)) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(state["peak"], 1)

    def test_the_host_pattern_is_agent_api_s_plus_no_port(self):
        tree = ast.parse((APP_DIR / "agent_api.py").read_text(encoding="utf-8"))
        theirs = next(re.compile(ast.literal_eval(n.value.args[0])) for n in ast.walk(tree)
                      if isinstance(n, ast.Assign)
                      and [getattr(t, "id", None) for t in n.targets] == ["LOCAL_HOST"])
        hosts = ["127.0.0.1:8000", "localhost:8765", "localhost:1", "127.0.0.1:65535",
                 "localhost", "127.0.0.1", "evil.example:8000", "127.0.0.1.evil.example:8000",
                 "localhost.evil.example", "LOCALHOST:8000", "127.0.0.1:", "localhost:123456",
                 "[::1]:8000", ""]
        ours = {h for h in hosts if RA.LOCAL_HOST.fullmatch(h)}
        self.assertEqual(ours, {h for h in hosts if theirs.fullmatch(h)} | {"localhost", "127.0.0.1"})

    def test_server_mounts_results_inside_simulation_after_install(self):
        tree = ast.parse((APP_DIR / "server.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", getattr(n.func, "attr", None)) == "mount_results"]
        self.assertEqual(len(calls), 1, "mount_results( must be called exactly once")
        guarded = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                   and isinstance(n.test, ast.Attribute) and n.test.attr == "simulation"
                   and getattr(n.test.value, "id", None) == "a"]
        self.assertEqual(len(guarded), 1)
        body = [ast.unparse(s) for s in guarded[0].body]
        at = body.index("install(app)")
        self.assertEqual(body[at + 1:at + 3], ["from app.results_api import mount_results",
                                               "mount_results(app)"])
        agents = body.index("print(f'  agent replay:  http://localhost:{a.http_port}/agents')")
        self.assertEqual(body[agents + 1],
                         "print(f'  results:       http://localhost:{a.http_port}/results')")
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse([n for n in top if "results" in (getattr(n, "module", "") or "")],
                         "server.py must not import the results modules at module level")

    def test_static_files_are_revalidated_on_every_load(self):
        from app import server
        client = TestClient(server.app)
        first = client.get("/static/sim/i18n.mjs")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers.get("cache-control"), "no-cache")
        again = client.get("/static/sim/i18n.mjs", headers={"if-none-match": first.headers["etag"]})
        self.assertEqual(again.status_code, 304)
        self.assertEqual(again.headers.get("cache-control"), "no-cache")

    def test_importing_the_server_loads_no_results_module(self):
        code = ("import json, sys\n"
                "import app.server\n"
                "from fastapi import FastAPI\n"
                "before = sorted(m for m in sys.modules if m.startswith('app.results'))\n"
                "from app.results_api import mount_results\n"
                "mount_results(FastAPI())\n"
                "after = sorted(m for m in sys.modules if m.startswith('app.results'))\n"
                "print(json.dumps([before, after]))\n")
        run = subprocess.run([sys.executable, "-c", code], cwd=APP_DIR.parent, capture_output=True,
                             text=True, timeout=180,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        before, after = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(before, [], "--live and --replay would load the readers")
        self.assertEqual(after, ["app.results_api", "app.results_eval", "app.results_provenance"],
                         "mounting takes the plant hash now, and loads no reader")


if __name__ == "__main__":
    unittest.main()
