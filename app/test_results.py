"""The results tab's own suite. Nothing here writes into the repository.

    python -m app.test_results                                  every test
    python -m unittest app.test_results.EvalParserTests -v      one class

Run from the repository root. Fixtures are made in temporary directories
OUTSIDE the repository, with Path.write_text and Path.write_bytes only:
app/test_replay.py's read-only scan reads every app/*.py, this file included.
"""
from pathlib import Path
import tempfile
import unittest
import warnings

import analyse_phase_d as APD
import analyse_phase_d2 as APD2
import fingerprint as FP
from app import results_eval as EV

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


if __name__ == "__main__":
    unittest.main()
