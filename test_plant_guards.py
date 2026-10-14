"""test_plant_guards.py -- the two guards of 8 October, each with a test that
fails if the guard is removed.

    python test_plant_guards.py        about a second; exit code 0 when all pass

1. THE THERMAL NETWORK IS SUB-STEPPED (agreed step 1 of 30 September,
   thermal.DT_SUB_MAX). One step of 1 s must equal ten steps of 0.1 s, and one
   of 2 s twenty: the integrator splits every step into equal sub-steps of at
   most DT_SUB_MAX. And at the H/tau sweep's 2 s step the coolant must settle on
   a held climb, where before the fix it swung about 10 K every step
   (timestep_study.py, results/timestep_study_before_substep.json). Set
   DT_SUB_MAX back to one step per call and both tests fail.

2. THE FINGERPRINT COVERS THE DERIVED CONSTANTS (agreed step 2,
   fingerprint.derived_sha). Changing one constant in data/derived_params.json
   must move derived_sha, which train.py and evaluate.py treat as fatal; the
   file's bookkeeping (keys starting with "_", such as the timestamp
   derive_params.py writes) must not, or every rebuild of the dataset would
   lock out every trained agent. Runs on a copy of the file; the real one is
   never touched.

Added 9 October 2026: WBS v3 rows 2.2 and 2.6 named these tests as missing.
"""
import copy
import json
import os
import shutil
import sys
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import fingerprint as FP  # noqa: E402
import thermal  # noqa: E402

# The locked climb's operating point, held: 12 % at 130 km/h in 42 C air,
# 7th gear at 2706 rpm, the exhaust flow the H/tau axis uses (121.3 g/s) and
# the gas temperature the baseline reaches there (1022 C, CLAUDE.md mistake 23).
CLIMB = dict(mdot_fuel_gps=8.2, mdot_exh_gps=121.3, egt_k=1022.0 + 273.15, t_amb=315.15,
             vehicle_mps=130.0 / 3.6, fan_duty=0.4, coolant_pump_duty=1.0, rpm=2706.0)


def _net():
    n = thermal.ThermalNetwork()
    n.reset(t_amb=CLIMB["t_amb"], warm=True)
    return n


class SubStepping(unittest.TestCase):
    def test_a_step_equals_its_substeps(self):
        """One 1 s step is ten 0.1 s steps; one 2 s step is twenty."""
        self.assertLessEqual(thermal.DT_SUB_MAX, 0.1 + 1e-12)
        for dt, n in ((1.0, 10), (2.0, 20)):
            a, b = _net(), _net()
            for _ in range(30):
                a.step(dt, **CLIMB)
                for _ in range(n):
                    b.step(dt / n, **CLIMB)
            np.testing.assert_allclose(a.state(), b.state(), rtol=0, atol=1e-9,
                                       err_msg=f"a {dt} s step is not {n} steps of {dt / n} s")

    def test_coolant_settles_at_the_sweeps_2s_step(self):
        """Held climb at dt 2 s for 20 minutes: the block node must stop moving.
        Before the sub-stepping it zig-zagged about 10 K on every step."""
        n = _net()
        block = []
        for _ in range(600):
            n.step(2.0, **CLIMB)
            block.append(n.t_block)
        last = np.abs(np.diff(block[-30:]))
        self.assertLess(float(last.max()), 0.05,
                        f"the block node still moves {last.max():.3f} K per 2 s step at the end of a held climb")


class DerivedFingerprint(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp(prefix="derived_sha_")
        self.path = os.path.join(self.dir, "derived_params.json")
        shutil.copyfile(os.path.join(HERE, "data", "derived_params.json"), self.path)
        with open(self.path, encoding="utf-8") as fh:
            self.d = json.load(fh)

    def tearDown(self):
        shutil.rmtree(self.dir, ignore_errors=True)

    def _sha_of(self, d):
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(d, fh)
        return FP.derived_sha(self.path)

    def test_a_copy_hashes_as_the_live_file(self):
        self.assertEqual(self._sha_of(self.d), FP.derived_sha())

    def test_one_changed_constant_moves_it(self):
        d = copy.deepcopy(self.d)
        stat = d["thermal"]["t_stat_span"]
        d["thermal"]["t_stat_span"] = stat * 1.001
        self.assertNotEqual(self._sha_of(d), FP.derived_sha(),
                            "derived_sha did not move when a derived constant changed")

    def test_bookkeeping_does_not(self):
        d = copy.deepcopy(self.d)
        d["_generated"] = "2099-01-01 00:00"
        self.assertEqual(self._sha_of(d), FP.derived_sha(),
                         "derived_sha moved on a timestamp: every rebuild would refuse every agent")

    def test_it_is_fatal(self):
        self.assertIn("derived_sha", FP.FATAL)


if __name__ == "__main__":
    unittest.main(verbosity=2)
