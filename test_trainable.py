"""test_trainable.py -- the four entry points that train or score refuse an EPA engine, and take the B58.

    python test_trainable.py        about 1 min; exit code 0 when all pass

Decision 47 (results/VALIDATION_DECISIONS.md section H; build step 2 P5, 22
October 2026): the EPA engines are refused by train.py, train_all.py,
run_phase_d.py and evaluate.py until fingerprint schema 4 can record them and
their validation is committed. Each takes --engine from engines.trainable(),
("b58",), not engines.known(). Amendment B8: nothing on this laptop runs these
entry points (training runs on the training device), so each is run here as far
as its argument parser, which is where the refusal lives, and never further:
every run below ends at --help or at the parser's refusal, and nothing trains.

The control (mistake 12). Until P6 no EPA engine was registered, so "--engine
mazda_25t" would have been refused by engines.known() too, and the refusal alone
could not show that trainable() is what refuses it. Each refusal is therefore run
with mazda_25t REGISTERED in the child process (a name only, the B58's specs;
nothing is built), and run again with trainable() replaced by known(): the same
command must then pass the parser. Since P6 (22 October 2026) engines.PLANTS
registers the three EPA plants itself, so the same pair runs on the registry as it
stands too: refused, and through once trainable() is known().

  Help        each entry point's --help exits 0 (amendment B8)
  B58         "--engine b58 --help" passes the parser
  Refused     "--engine mazda_25t --help", mazda_25t registered: exit 2, "invalid choice"
  Control     the same with trainable() made known(): exit 0
  Registry    (P6) the same on engines.PLANTS as it stands: each of the three EPA
              plants refused, and the Mazda through with trainable() made known()
  FingerprintCli  fingerprint.py, which keeps known(), refuses an uncalibrated
              plant by name, with the command that calibrates it, and no
              traceback (amendment B7; added at the review of P5); the control:
              with calibrated() made to say yes it dies in derived.py instead
  FingerprintCliRegistered  (P6) each of the three registered EPA plants, nothing
              patched, is refused the same way, its own derived file and freeze
              record named; since P7 a plant whose calibration has written one of
              its files is skipped by name, never failed (with its control)
  Source      each parser's --engine choices are engines.trainable(), by AST
"""
import ast
import os
import subprocess
import sys
import unittest
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import derived  # noqa: E402

ENTRY_POINTS = ("train.py", "train_all.py", "run_phase_d.py", "evaluate.py")

# The child: register mazda_25t by name when asked (never built: --help and the
# parser's refusal both stop before anything reads a plant), optionally make
# trainable() known() (the control), then run the script as __main__.
CHILD = """
import runpy, sys
sys.path.insert(0, {here!r})
import engines
if {register}:
    engines.PLANTS["mazda_25t"] = ("b58", "a90_supra")
if {control}:
    engines.trainable = lambda: tuple(engines.known())
sys.argv = [{script!r}] + {argv!r}
runpy.run_path({path!r}, run_name="__main__")
"""


def run(script, argv, register=False, control=False):
    code = CHILD.format(here=HERE, register=register, control=control, script=script, argv=list(argv),
                        path=os.path.join(HERE, script))
    env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
    p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True,
                       timeout=600, env=env)
    return p.returncode, p.stdout + p.stderr


EPA_PLANTS = ("mazda_25t", "honda_l15b7", "ford_27tt")
CASES = {
    "help": dict(argv=["--help"]),
    "b58": dict(argv=["--engine", "b58", "--help"]),
    "refused": dict(argv=["--engine", "mazda_25t", "--help"], register=True),
    "control": dict(argv=["--engine", "mazda_25t", "--help"], register=True, control=True),
    # the registry as it stands: since P6 (22 October 2026) it registers the three
    # EPA plants itself (engines.PLANTS); each is refused, and the Mazda passes once
    # trainable() is known() (the control)
    **{f"registry_{n}": dict(argv=["--engine", n, "--help"]) for n in EPA_PLANTS},
    "registry_control_mazda_25t": dict(argv=["--engine", "mazda_25t", "--help"], control=True),
}


class EntryPoints(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        jobs = [(s, c) for s in ENTRY_POINTS for c in CASES]
        with ThreadPoolExecutor(max_workers=4) as pool:
            out = pool.map(lambda sc: run(sc[0], **CASES[sc[1]]), jobs)
        cls.result = dict(zip(jobs, out))

    def test_help_exits_0(self):
        for s in ENTRY_POINTS:
            with self.subTest(script=s):
                rc, out = self.result[(s, "help")]
                self.assertEqual(rc, 0, out[-2000:])
                self.assertIn("--engine", out)

    def test_the_b58_passes_the_parser(self):
        for s in ENTRY_POINTS:
            with self.subTest(script=s):
                rc, out = self.result[(s, "b58")]
                self.assertEqual(rc, 0, out[-2000:])

    def test_an_epa_engine_is_refused_even_when_registered(self):
        for s in ENTRY_POINTS:
            with self.subTest(script=s):
                rc, out = self.result[(s, "refused")]
                self.assertEqual(rc, 2, out[-2000:])
                self.assertIn("invalid choice: 'mazda_25t'", out)

    def test_the_registered_epa_plants_are_refused(self):
        """P6: engines.PLANTS registers the three EPA plants, and each entry point
        refuses each by trainable(); with trainable() made known() the Mazda passes
        the parser (the control: the refusal is trainable()'s, not a missing name)."""
        for s in ENTRY_POINTS:
            for n in EPA_PLANTS:
                with self.subTest(script=s, plant=n):
                    rc, out = self.result[(s, f"registry_{n}")]
                    self.assertEqual(rc, 2, out[-2000:])
                    self.assertIn(f"invalid choice: '{n}'", out)
            with self.subTest(script=s, control="mazda_25t"):
                rc, out = self.result[(s, "registry_control_mazda_25t")]
                self.assertEqual(rc, 0, out[-2000:])

    def test_the_control_trainable_as_known_lets_it_through(self):
        """Mistake 12: the refusal above is trainable()'s. With trainable() made
        known() in the child, the registered mazda_25t passes the same parser."""
        for s in ENTRY_POINTS:
            with self.subTest(script=s):
                rc, out = self.result[(s, "control")]
                self.assertEqual(rc, 0, out[-2000:])


# fingerprint.py's command line on an UNCALIBRATED plant (amendment B7; the review
# of P5, 22 October 2026). The child registers mazda_25t on a probe engine spec:
# the B58's spec read through engines.read_spec with an EPA engine's top-level keys,
# whose derived file and freeze record do not exist (a folder no calibration
# writes). Nothing is built: the refusal comes before engines.get. The control
# makes engines.calibrated() say yes, so the same command reaches engines.get and
# dies there, in derived.py, with a traceback: the assertions below are the
# refusal's, and would fail if fingerprint.py stopped calling it. The probe's
# derived file is derived.engine_path's, relative with "/" as a spec writes it, so
# this file carries no literal of that folder (amendment C3's scan forbids it
# outside epa_rows.py; the review of P5, 22 October 2026).
PROBE_DERIVED = os.path.relpath(derived.engine_path("_uncalibrated_probe"), HERE).replace(os.sep, "/")
PROBE_FREEZE = "results/EPA_CALIBRATION/_uncalibrated_probe/freeze.json"
FP_CHILD = """
import runpy, sys
sys.path.insert(0, {here!r})
import engines
real = engines.read_spec
def read_spec(name):
    if name != "_uncalibrated_probe":
        return real(name)
    spec = real("b58")
    spec["_meta"] = dict(spec["_meta"], derived_set="epa", derived={derived!r}, freeze={freeze!r})
    return spec
engines.read_spec = read_spec
engines.PLANTS["mazda_25t"] = ("_uncalibrated_probe", "a90_supra")
if {control}:
    engines.calibrated = lambda name: True
sys.argv = ["fingerprint.py", "--engine", "mazda_25t"]
runpy.run_path({path!r}, run_name="__main__")
"""


class FingerprintCli(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for f in (PROBE_DERIVED, PROBE_FREEZE):
            assert not os.path.exists(os.path.join(HERE, f)), f"{f} exists: the probe would be calibrated"
        env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")

        def go(control):
            code = FP_CHILD.format(here=HERE, derived=PROBE_DERIVED, freeze=PROBE_FREEZE, control=control,
                                   path=os.path.join(HERE, "fingerprint.py"))
            p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True,
                               timeout=600, env=env)
            return p.returncode, p.stdout + p.stderr
        cls.refused, cls.control = go(False), go(True)

    def test_an_uncalibrated_plant_is_refused_by_name(self):
        rc, out = self.refused
        self.assertNotEqual(rc, 0, out[-2000:])
        self.assertIn("fingerprint.py: plant 'mazda_25t' is not calibrated yet: no " + PROBE_DERIVED, out)
        self.assertIn("python calibrate_epa.py fit --engine _uncalibrated_probe, then e6, complete and check", out)
        self.assertNotIn("Traceback", out)

    def test_the_control_calibrated_says_yes_and_it_dies_elsewhere(self):
        """Mistake 12: without the refusal the command still fails, in derived.py,
        with a traceback and no refusal text, so the test above is the refusal's."""
        rc, out = self.control
        self.assertNotEqual(rc, 0, out[-2000:])
        self.assertIn("Traceback", out)
        self.assertIn("FileNotFoundError", out)
        self.assertNotIn("is not calibrated yet", out)


# fingerprint.py's command line on the three REGISTERED EPA plants (22 October 2026,
# build step 2 P6): nothing patched; each is refused by name, its own derived file
# and freeze record named, with the command that makes them. The derived file is
# derived.engine_path's, so no literal of that folder is carried here (amendment C3).
FP_REAL = """
import runpy, sys
sys.path.insert(0, {here!r})
sys.argv = ["fingerprint.py", "--engine", {name!r}]
runpy.run_path({path!r}, run_name="__main__")
"""


def calibration_files_written(name):
    """The files the calibration of the EPA plant `name` writes -- its derived file
    and its freeze record, as its engine spec names them -- that exist on disk."""
    import engines
    meta = engines.read_spec(engines.PLANTS[name][0])["_meta"]
    return [f for f in (meta["derived"], meta["freeze"]) if os.path.exists(os.path.join(HERE, f))]


def uncalibrated_or_skip(test, name):
    """`test`'s current subTest skipped, by the plant's name, once the calibration
    of the EPA plant `name` has written its derived file or its freeze record (22
    October 2026, build step 2 P7; the review of P6). The refusal below is P6's
    state, a registered plant with neither file; WP4's first `calibrate_epa.py fit`
    ends it, and commit D, which re-runs this file (decision 48), changes the check
    on purpose. It was a bare assert, which would have failed the class for a
    reason that is not the plant's. The rule of
    test_engine_threading.uncalibrated_or_skip, kept here so that this file imports
    no other test: a file that exists is what skips."""
    written = calibration_files_written(name)
    if written:
        test.skipTest(f"{name}: its calibration has written {', '.join(written)}; this check pins the "
                      "uncalibrated plant of build step 2 P6, and commit D replaces it")


class FingerprintCliRegistered(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")

        def go(name):
            code = FP_REAL.format(here=HERE, name=name, path=os.path.join(HERE, "fingerprint.py"))
            p = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True,
                               timeout=600, env=env)
            return p.returncode, p.stdout + p.stderr
        with ThreadPoolExecutor(max_workers=3) as pool:
            cls.result = dict(zip(EPA_PLANTS, pool.map(go, EPA_PLANTS)))

    def test_each_registered_epa_plant_is_refused_by_name(self):
        for n in EPA_PLANTS:
            rel = os.path.relpath(derived.engine_path(n), HERE).replace(os.sep, "/")
            with self.subTest(plant=n):
                uncalibrated_or_skip(self, n)
                rc, out = self.result[n]
                self.assertNotEqual(rc, 0, out[-2000:])
                self.assertIn(f"fingerprint.py: plant '{n}' is not calibrated yet: no {rel} or no "
                              f"results/EPA_CALIBRATION/{n}/freeze.json", out)
                self.assertIn(f"python calibrate_epa.py fit --engine {n}, then e6, complete and check", out)
                self.assertNotIn("Traceback", out)

    def test_a_plant_whose_calibration_wrote_a_file_is_skipped(self):
        """P7 (22 October 2026; the review of P6): the test above, run as itself
        with the Mazda's spec naming as its derived file one that exists (a
        temporary file: nothing under data/ is written), reports exactly the
        Mazda's subtest skipped, by name, and no failure or error, so the Honda
        and the Ford are still checked. The control (mistake 12): with the spec as
        it is, the same run skips only the plants whose files exist -- none, until
        WP4 writes one, which this control then expects rather than failing on."""
        import tempfile
        from unittest import mock
        import engines
        real = engines.read_spec
        already = {n for n in EPA_PLANTS if calibration_files_written(n)}
        with tempfile.TemporaryDirectory() as tmp:
            written = os.path.join(tmp, "derived_params.json")
            with open(written, "w", encoding="utf-8") as fh:
                fh.write("{}")

            def read(name):
                s = real(name)
                return dict(s, _meta=dict(s["_meta"], derived=written)) if name == "mazda_25t" else s
            for patched in (True, False):
                with self.subTest(written=patched):
                    result = unittest.TestResult()
                    case = type(self)("test_each_registered_epa_plant_is_refused_by_name")
                    if patched:
                        with mock.patch.object(engines, "read_spec", side_effect=read):
                            case.run(result)
                    else:
                        case.run(result)
                    self.assertEqual((result.failures, result.errors), ([], []))
                    reasons = [r for _, r in result.skipped]
                    self.assertEqual(sorted(r.split(":")[0] for r in reasons),
                                     sorted(already | ({"mazda_25t"} if patched else set())), reasons)
                    if patched:
                        self.assertTrue(any(r.startswith(f"mazda_25t: its calibration has written {written}")
                                            for r in reasons), reasons)


class Source(unittest.TestCase):
    def test_each_engine_argument_takes_trainable(self):
        """Every add_argument("--engine", ...) of the four entry points has
        choices=engines.trainable(); fingerprint.py keeps known() (amendment B7)."""
        for s, want in [(s, "trainable") for s in ENTRY_POINTS] + [("fingerprint.py", "known")]:
            with open(os.path.join(HERE, s), encoding="utf-8") as fh:
                tree = ast.parse(fh.read(), filename=s)
            found = []
            for node in ast.walk(tree):
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                        and node.func.attr == "add_argument" and node.args
                        and isinstance(node.args[0], ast.Constant) and node.args[0].value == "--engine"):
                    ch = {k.arg: k.value for k in node.keywords}.get("choices")
                    found.append(ast.unparse(ch) if ch is not None else None)
            with self.subTest(script=s):
                self.assertEqual(found, [f"engines.{want}()"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
