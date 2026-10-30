"""test_epa_plants.py -- each EPA plant as its calibration leaves it: listed, built, fingerprinted, its
deliverable-torque table and its frozen-plant dump given back (docs/build_step_2/PLAN.md 7.6, WP4;
WP3_INTERFACES.md 9.12; HANDOFFS.md WP4 item 1).

    python -B test_epa_plants.py      a few minutes; exit code 0 when all pass

Build step 2 of decision 24, WP3 (23 October 2026): written in WP3, run at commit D. For each EPA plant
whose derived file and freeze record exist in this tree (engines.calibrated), five checks, each run in
a fresh process in the tree (so engines reads the tree's own files, and the cache of no earlier build
answers): `python engines.py` lists it with its engine_sha and its derived file; engines.get builds it,
and its engine_sha is complete.json's; `fingerprint.py --engine <id>` no longer refuses it (a CVT car:
refuses it by amendment B17's words until fingerprint schema 4, decision 91); a fresh
engine_env.measure_deliverable_torque at the car's own grid, rounded as the completion rounds it, is
the table the plant carries and complete.json's; and epa_freeze.frozen_plant_dump of the plant get()
builds is complete.json's dump. Until a plant is calibrated its checks skip by name (the pattern of
test_engine_threading.uncalibrated_or_skip, inverted: these check the calibrated state).

The same checks run on a synthetic frozen candidate in a temporary repository (the B58's values under
the Mazda's name, nothing fitted, no EPA data), so they are shown able to pass, and each is shown able
to fail on a copy with one thing changed (mistake 12): one ulp of a frozen constant, one entry of the
table, the dump's hash.
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import engines  # noqa: E402
import epa_fit  # noqa: E402
import epa_freeze  # noqa: E402
import test_epa_fixtures as F  # noqa: E402

EPA_PLANTS = tuple(n for n in engines.PLANTS if engines.read_spec(engines.PLANTS[n][0])["_meta"].get("derived_set")
                   == "epa")
ENV = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")

# The checks' own process: run in the tree being checked, it prints one JSON line (no figure reaches a
# document: the numbers are compared here and never written).
_PROBE = r'''
import json, subprocess, sys
name = sys.argv[1]
out = {}
lst = subprocess.run([sys.executable, "-B", "engines.py"], capture_output=True, text=True)
out["listing"] = [l for l in lst.stdout.splitlines() if l.split()[:1] == [name]]
try:
    import engines, engine_env, epa_freeze
    p = engines.get(name)
    out["engine_sha"] = engines.engine_sha(p)
    out["table_carried"] = [[int(r), float(t)] for r, t in p.car.deliverable_torque]
    out["table_fresh"] = [[int(r), round(float(t), 1)] for r, t in
                          engine_env.measure_deliverable_torque(p.car.table_rpms, plant=p)]
    out["dump_sha256"] = epa_freeze.frozen_plant_dump(p).sha256
    out["cvt"] = isinstance(p.car, engines.CvtCar)
except Exception as exc:
    out["error"] = f"{type(exc).__name__}: {exc}"
fp = subprocess.run([sys.executable, "-B", "fingerprint.py", "--engine", name], capture_output=True, text=True)
out["fingerprint_exit"] = fp.returncode
out["fingerprint_output"] = (fp.stdout + fp.stderr)[-2000:]
print(json.dumps(out))
'''

# DECISION 91 (Ghassan, 30 October 2026): fingerprint schema 3 cannot record a car without gears (amendment
# B17; test_cars.Fingerprint pins the refusal), so until schema 4 (decisions 27 and 28, before any EPA engine
# trains) a CVT plant's check is that fingerprint.py refuses it in B17's words; a stepped plant's is exit 0
# (WP3_INTERFACES.md 9.12, "no longer refusing it"). The words are fingerprint.py's own, as test_cars pins them.
B17_REFUSAL = "this car has no gears; fingerprint schema 3 cannot record it"


def report(name, *, root):
    """The probe's record of plant `name` in the work tree `root`."""
    r = subprocess.run([sys.executable, "-B", "-c", _PROBE, name], cwd=root, env=ENV, capture_output=True,
                       text=True, timeout=1800)
    if r.returncode != 0:
        raise RuntimeError(f"the probe of {name} in {root} stopped: {r.stderr[-1500:]}")
    return json.loads(r.stdout.strip().splitlines()[-1])


def problems(name, rep, complete):
    """Every check of the module's docstring that `rep` (report) fails against `complete` (the plant's
    complete.json), each named."""
    out = []
    lines = rep.get("listing") or []
    if len(lines) != 1 or "not calibrated" in lines[0] or f"engine_sha {complete.get('engine_sha')}" not in lines[0]:
        out.append(f"python engines.py does not list {name} with complete.json's engine_sha: {lines}")
    elif f"derived {epa_freeze.derived_relpath(name)}" not in lines[0]:
        out.append(f"python engines.py does not list {name} with its derived file: {lines}")
    if "error" in rep:
        out.append(f"engines.get({name!r}) does not build: {rep['error']}")
    else:
        if rep["engine_sha"] != complete.get("engine_sha"):
            out.append("the plant get() builds is not complete.json's engine_sha")
        if rep["table_fresh"] != rep["table_carried"]:
            out.append("a fresh measure_deliverable_torque is not the table the plant carries")
        if rep["table_carried"] != (complete.get("deliverable_torque") or {}).get("table"):
            out.append("the plant's table is not complete.json's")
        if rep["dump_sha256"] != (complete.get("dump") or {}).get("sha256"):
            out.append("the frozen-plant dump is not complete.json's")
    if rep.get("cvt"):
        if rep.get("fingerprint_exit") == 0 or B17_REFUSAL not in (rep.get("fingerprint_output") or ""):
            out.append(f"fingerprint.py --engine {name} does not refuse its CVT car in amendment B17's words "
                       f"(exits {rep.get('fingerprint_exit')}; decision 91)")
    elif rep.get("fingerprint_exit") != 0:
        out.append(f"fingerprint.py --engine {name} exits {rep.get('fingerprint_exit')}")
    return out


class RealPlants(F.Guarded):
    """This tree's EPA plants, each once its calibration has written its files; skipped by name before."""

    def test_each_calibrated_plant(self):
        for name in EPA_PLANTS:
            with self.subTest(plant=name):
                if not engines.calibrated(name):
                    self.skipTest(f"{name}: not calibrated yet (no derived file or freeze record); "
                                  "these checks run at commit D")
                comp = epa_freeze.read_json(os.path.join(epa_freeze.calibration_dir(name, root=HERE),
                                                         "complete.json"), root=HERE)
                self.assertEqual(problems(name, report(name, root=HERE), comp), [])


def synthetic_frozen(root, name):
    """A frozen candidate of `name` written into the synthetic repository `root` as a calibration leaves
    it: the derived file (the B58's values as frozen sections, a deliverable-torque table measured on the
    candidate as the completion measures it, the B58's knee and floor), a freeze record holding the frozen
    sections' hash (the key engines._check_freeze reads), and a complete.json with the engine_sha, the
    table and the dump of the plant build_candidate makes from those values (the constructor get() uses).
    Returns complete.json's dict. Nothing is fitted and no EPA row is read."""
    v = F.b58_values()
    frozen = json.loads(json.dumps({s: v[s] for s in engines.FROZEN_SECTIONS}))
    vals = {**frozen, **json.loads(json.dumps(epa_fit.PROVISIONAL_COMPLETION))}
    vals["k3"], vals["loop"] = dict(v["k3"]), dict(v["loop"])
    import engine_env
    cand = engines.build_candidate(name, vals)
    vals["deliverable_torque"] = [[int(r), round(float(t), 1)] for r, t in
                                  engine_env.measure_deliverable_torque(cand.car.table_rpms, plant=cand)]
    file = {"_about": "synthetic, by test_epa_plants.py", "_inputs": {k: "synthetic" for k in epa_freeze.INPUTS_KEYS},
            **vals}
    file["_inputs"]["freeze_record"] = epa_freeze.freeze_relpath(name)
    epa_freeze.write_json_atomic(epa_freeze.derived_path(name, root=root), file)
    epa_freeze.write_json_atomic(epa_freeze.freeze_path(name, root=root),
                                 {"frozen_sections_sha256": engines.frozen_sections_sha256(vals)})
    plant = engines.build_candidate(name, vals)
    comp = {"engine_sha": engines.engine_sha(plant), "deliverable_torque": {"table": vals["deliverable_torque"]},
            "dump": epa_freeze.frozen_plant_dump(plant).as_json()}
    epa_freeze.write_json_atomic(os.path.join(epa_freeze.calibration_dir(name, root=root), "complete.json"), comp)
    return comp


class SyntheticPlant(F.SyntheticRepoCase):
    """The checks on a synthetic frozen Mazda candidate in a temporary repository: they pass, and each
    fails on a copy with one thing changed."""

    NAME = "mazda_25t"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comp = synthetic_frozen(cls.base.root, cls.NAME)
        cls.rep = report(cls.NAME, root=cls.base.root)          # the unchanged tree's, read by two tests

    def copy(self):
        tmp = tempfile.mkdtemp(prefix="epa_plants_", dir=self._tmp.name)
        dst = os.path.join(tmp, "repo")
        shutil.copytree(self.base.root, dst)
        return dst

    def test_the_checks_pass_on_a_frozen_candidate(self):
        self.assertEqual(problems(self.NAME, self.rep, self.comp), [])

    def test_one_ulp_of_a_frozen_constant_is_refused(self):
        root = self.copy()
        p = epa_freeze.derived_path(self.NAME, root=root)
        d = epa_freeze.read_json(p, root=root)
        d["cycle"]["burn_base"] = math.nextafter(d["cycle"]["burn_base"], math.inf)
        epa_freeze.write_json_atomic(p, d)
        got = problems(self.NAME, report(self.NAME, root=root), self.comp)
        self.assertTrue(any("does not build" in g for g in got), got)
        self.assertTrue(any("fingerprint.py" in g for g in got), got)

    def test_a_table_entry_changed_is_seen(self):
        root = self.copy()
        p = epa_freeze.derived_path(self.NAME, root=root)
        d = epa_freeze.read_json(p, root=root)
        d["deliverable_torque"][3][1] = d["deliverable_torque"][3][1] + 0.1
        epa_freeze.write_json_atomic(p, d)
        got = problems(self.NAME, report(self.NAME, root=root), self.comp)
        self.assertIn("a fresh measure_deliverable_torque is not the table the plant carries", got)
        self.assertIn("the plant's table is not complete.json's", got)

    def test_a_dump_that_is_not_the_plants_is_seen(self):
        comp = json.loads(json.dumps(self.comp))
        comp["dump"]["sha256"] = "0" * 64
        self.assertEqual(problems(self.NAME, self.rep, comp), ["the frozen-plant dump is not complete.json's"])

    def test_another_engine_sha_and_a_listing_without_the_derived_file_are_seen(self):
        """Each check alone (WP3's fix of 23 October 2026, the test review's finding that the one-ulp case
        fires every check at once): complete.json with another engine_sha fails the listing's and the build's
        engine_sha checks and nothing else; a listing line without the derived file fails the listing alone;
        a fingerprint that refuses fails that check alone."""
        comp = dict(json.loads(json.dumps(self.comp)), engine_sha="0" * 16)
        got = problems(self.NAME, self.rep, comp)
        self.assertEqual(len(got), 2, got)
        self.assertTrue(got[0].startswith("python engines.py does not list") and "engine_sha" in got[0], got)
        self.assertEqual(got[1], "the plant get() builds is not complete.json's engine_sha")
        self.assertTrue(self.rep["listing"] and f"derived {epa_freeze.derived_relpath(self.NAME)}" in self.rep["listing"][0])
        rep = dict(self.rep, listing=[self.rep["listing"][0].split("   derived ")[0]])
        got = problems(self.NAME, rep, self.comp)
        self.assertEqual(got, [f"python engines.py does not list {self.NAME} with its derived file: {rep['listing']}"])
        self.assertEqual(problems(self.NAME, dict(self.rep, fingerprint_exit=2), self.comp),
                         [f"fingerprint.py --engine {self.NAME} exits 2"])

    def test_a_cvt_car_is_checked_for_b17s_refusal(self):
        """Decision 91: a CVT plant passes the fingerprint check only when fingerprint.py refuses it in
        amendment B17's words; one that fingerprints (exit 0), or refuses for another reason, fails it alone.
        The synthetic Mazda is stepped (its record says so, and it fingerprints), so the CVT cases are its
        record with the car's kind and the fingerprint's outcome changed; the control is the record as it
        is, which passes on the stepped reading."""
        self.assertIs(self.rep.get("cvt"), False, self.rep)
        self.assertEqual(self.rep["fingerprint_exit"], 0)
        msg = f"fingerprint.py --engine {self.NAME} does not refuse its CVT car in amendment B17's words"
        refused = dict(self.rep, cvt=True, fingerprint_exit=1,
                       fingerprint_output=f"ValueError: {self.NAME}: {B17_REFUSAL}\n")
        self.assertEqual(problems(self.NAME, refused, self.comp), [])
        got = problems(self.NAME, dict(self.rep, cvt=True), self.comp)
        self.assertEqual(len(got), 1, got)
        self.assertTrue(got[0].startswith(msg) and "exits 0" in got[0], got)
        got = problems(self.NAME, dict(refused, fingerprint_output="LookupError: no registered pair\n"), self.comp)
        self.assertEqual(len(got), 1, got)
        self.assertTrue(got[0].startswith(msg) and "exits 1" in got[0], got)
        self.assertEqual(problems(self.NAME, self.rep, self.comp), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
