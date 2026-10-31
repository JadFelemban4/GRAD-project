"""test_epa_roads.py -- the roads module (epa_roads.py; section I, rows 94-103), outside STEP2_TESTS.

    python -B test_epa_roads.py        about two minutes; exit code 0 when all pass

Every check runs on a SYNTHETIC seed or on temporary copies; nothing here draws a road of the test,
writes under results/EPA_ROADS/, or opens an EPA table, a held-out record, the real contract or any .csv:
every class is test_epa_fixtures.Guarded (WP3_INTERFACES.md 9.1), and the module's own guard is
installed below as well.

  Generator    it imports and reads no vehicle (row 95 (1)); the frozen twenty are read as evaluate.py
               holds them; the draw order and the fit rule against a hand-written expectation; the ramps
               are 8 s and the slot extents are as recorded; both of row 98's checks can fail; the road
               shape is make_grade_climb's; row 102's table of H, by hand
  Streams      the first draw, the replacement, the redraw, the practice and the training streams are
               separate and deterministic; the practice set by hand
  Replacement  the bound of 100 and the flat-slot outcome, with C5 mocked; a replaced grade is the
               slot's own 0x1D stream's
  C5           on each car, the probe's smallest margins come back (c5tau.txt); decision 40's diagnostic
               and the coverage flags on the Honda, counted on the kickdown and power-limited branches
  Reveal       the commit-reveal arithmetic; a private integer below 2**128 is refused; its refusals in
               a temporary git repository: the first attempt runs on the roads commit itself and the
               announced roads commit is the one found; no second set; the attempts log is append-only;
               a later attempt needs a note; the log is written before roads_seed is first used
  Records      roads.json is write-once; a one-byte change in each hashed file, a package shadowing a
               hashed module, and a changed version, plant_sha or engine_sha, are refused by the re-check
               and the redraws (temporary copies, a SYNTHETIC contract); --summary names one file; the
               drops are summary.json's; a redraw logs its start before it draws; the smoke run refuses a
               folder inside the repository and a seed of 2**32 or more
  Tightenings  after the real draw, roads.json's roads_seed is the reveal's and its hash lines the roads
               commit's (row 97; ORDER step 6), skipped while roads.json is absent; then
               results/EPA_TIGHTENINGS.json's roads_sha and roads_seed are the record's, skipped while
               the tightenings are absent and failed if they exist without roads.json; the hash lines,
               once set, are 64 lowercase hex digits and differ
"""
import contextlib
import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import epa_roads as R  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)

R.install_guard(())
SYNTHETIC_SEED = 271828182          # SYNTHETIC: a test seed, never roads_seed
PLANT_MODULES = ("engines", "engine_env", "plant", "thermal", "derived", "evaluate", "random_road", "fingerprint")


def hand_layout(rng):
    """Row 101's draws written out by hand: the lead-in, then L, g, G per climb; a climb whose ramp-down
    ends after 840 s is drawn and discarded and ends the road."""
    lead = int(rng.integers(150, 211))
    s, out = lead, []
    while True:
        L = int(rng.integers(67, 86))
        g = float(rng.uniform(0.10, 0.12))
        G = int(rng.integers(50, 151))
        if s + L + 8 > 840:
            return lead, out, (L, g, G)
        out.append((s, L, g, G))
        s += L + G


class Scripted:
    """An rng that returns scripted values and records each call."""

    def __init__(self, values):
        self.values = list(values)
        self.calls = []

    def integers(self, lo, hi):
        self.calls.append(("integers", lo, hi))
        return self.values.pop(0)

    def uniform(self, lo, hi):
        self.calls.append(("uniform", lo, hi))
        return self.values.pop(0)


class Generator(Guarded):
    def test_the_generator_imports_and_reads_no_vehicle(self):
        code = (
            "import os, sys\n"
            f"sys.path.insert(0, {HERE!r})\n"
            "opened = []\n"
            "sys.addaudithook(lambda e, a: opened.append(str(a[0])) if e == 'open' and a and "
            "isinstance(a[0], str) else None)\n"
            "import epa_roads as R\n"
            f"roads = R.generate({SYNTHETIC_SEED})\n"
            f"bad = sorted(m for m in {PLANT_MODULES!r} if m in sys.modules)\n"
            f"repo = os.path.normcase({HERE!r})\n"
            "files = sorted({os.path.relpath(p, repo).replace(os.sep, '/') for p in map(os.path.normcase, opened)\n"
            "                if p.startswith(repo + os.sep) and '.venv' not in p and not p.endswith('.pyc')})\n"
            "import json\n"
            "print(json.dumps([len(roads), bad, files]))\n")
        out = subprocess.run([sys.executable, "-B", "-c", code], capture_output=True, text=True,
                             env=dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1"))
        self.assertEqual(out.returncode, 0, out.stderr)
        n, bad, files = json.loads(out.stdout)
        self.assertEqual((n, bad), (20, []))
        # evaluate.py is read as text for EPISODES; the module's own source when no cached bytecode is used
        self.assertIn("evaluate.py", files)
        self.assertLessEqual(set(files), {"epa_roads.py", "evaluate.py"}, files)

    def test_no_vehicle_is_read_by_the_generator_or_the_practice_set(self):
        import engine_env
        import engines

        def refuse(*a, **k):
            raise AssertionError("a vehicle was read")
        with mock.patch.object(engines, "get", refuse), mock.patch.object(engine_env, "vehicle_for", refuse):
            self.assertEqual(len(R.generate(SYNTHETIC_SEED)), 20)
            self.assertEqual(len(R.practice_roads(SYNTHETIC_SEED)), 10)

    def test_the_frozen_twenty_are_evaluates(self):
        import evaluate
        self.assertEqual(R.frozen_episodes(root=HERE), evaluate.EPISODES)

    def test_the_draw_order_and_the_fit_rule_by_hand(self):
        import evaluate
        roads = R.generate(SYNTHETIC_SEED)
        rng = np.random.default_rng(SYNTHETIC_SEED)
        slot = 0
        for k, road in enumerate(roads):
            lead, climbs, discarded = hand_layout(rng)
            self.assertEqual((road["k"], road["episode_seed"], tuple(road["weights"])),
                             (k, evaluate.EPISODES[k][0], evaluate.EPISODES[k][1]))
            self.assertEqual(road["draws"]["lead_s"], lead)
            self.assertEqual([(c["onset_s"], c["L_s"], c["grade"], c["gap_s"]) for c in road["climbs"]],
                             [(float(s), float(L), g, float(G)) for s, L, g, G in climbs])
            self.assertEqual(road["draws"]["discarded"], {"L_s": discarded[0], "grade": discarded[1],
                                                          "gap_s": discarded[2]})
            self.assertEqual([c["slot"] for c in road["climbs"]], list(range(slot, slot + len(climbs))))
            slot += len(climbs)
            for c in road["climbs"]:
                self.assertLessEqual(c["onset_s"] + c["L_s"] + 8, 840)
            self.assertGreater(road["climbs"][-1]["onset_s"] + road["climbs"][-1]["L_s"] + road["climbs"][-1]["gap_s"]
                               + discarded[0] + 8, 840)

    def test_the_fit_rule_at_its_edge(self):
        # lead 670, a climb ending its ramp-down at exactly 840 s is kept; the next is drawn and discarded
        rng = Scripted([670, 162, 0.11, 50, 67, 0.105, 60])
        lead, climbs, discarded = R.layout(rng)
        self.assertEqual((lead, climbs, discarded), (670, [(670, 162, 0.11, 50)], (67, 0.105, 60)))
        self.assertEqual([c[0] for c in rng.calls], ["integers", "integers", "uniform", "integers",
                                                     "integers", "uniform", "integers"])
        self.assertEqual(rng.calls[0][1:], (150, 211))
        self.assertEqual(rng.calls[1][1:], (67, 86))
        self.assertEqual(rng.calls[2][1:], (0.10, 0.12))
        self.assertEqual(rng.calls[3][1:], (50, 151))
        # one second later it does not fit: all three of its draws are made, then the road ends
        rng = Scripted([671, 162, 0.11, 50])
        self.assertEqual(R.layout(rng), (671, [], (162, 0.11, 50)))
        self.assertEqual(rng.values, [])

    def test_the_ramps_are_8_s_and_the_extents_as_recorded(self):
        for road in R.generate(SYNTHETIC_SEED):
            g = np.asarray(road["cycle"]["grade"])
            self.assertEqual(R.ramp_problems(g, dt=1.0), [])
            nonzero = np.flatnonzero(g)
            expect = np.concatenate([np.arange(c["first_step"] + 1, c["last_step"]) for c in road["climbs"]])
            self.assertTrue(np.array_equal(nonzero, expect))
            for c in road["climbs"]:
                a, b, gr = c["first_step"], c["last_step"], c["grade"]
                self.assertEqual((a, b - a), (int(c["onset_s"]), int(c["L_s"]) + 8))
                self.assertEqual(g[a], 0.0)
                self.assertEqual(g[b], 0.0)
                self.assertTrue(np.all(g[a + 8:a + int(c["L_s"]) + 1] == gr))
                np.testing.assert_allclose(np.diff(g[a:a + 9]), gr / 8, rtol=1e-12)
                np.testing.assert_allclose(np.diff(g[b - 8:b + 1]), -gr / 8, rtol=1e-12)
                self.assertEqual(R.extent_problems(c, road, road), [])
                cand = R.with_grade(road, c["slot"], 0.1033)
                self.assertEqual(R.extent_problems(c, cand, road), [])
                self.assertEqual(R.ramp_problems(cand["cycle"]["grade"], dt=1.0), [])

    def test_both_checks_of_row_98_can_fail(self):
        g = np.zeros(100)
        g[50:] = 0.1                                           # a step
        self.assertTrue(R.ramp_problems(g, dt=1.0))
        g = np.clip((np.arange(100) - 50) / 7.0, 0, 1) * 0.1   # a 7 s ramp
        self.assertTrue(R.ramp_problems(g, dt=1.0))
        g = np.zeros(100)
        g[51:59] = 0.1 * (np.arange(1, 9) / 8.0) ** 2           # 8 s, not linear
        g[59:] = 0.1
        self.assertTrue(R.ramp_problems(g, dt=1.0))
        road = R.generate(SYNTHETIC_SEED)[0]
        c = road["climbs"][0]
        moved = copy.deepcopy(road)
        moved["climbs"][0]["onset_s"] += 1.0
        moved["climbs"][0]["first_step"] += 1
        moved["climbs"][0]["last_step"] += 1
        moved["cycle"]["grade"] = [float(x) for x in R.grade_from_climbs(np.asarray(road["cycle"]["t"]),
                                                                          moved["climbs"])]
        self.assertTrue(R.extent_problems(c, moved, road))
        other = R.with_grade(road, road["climbs"][1]["slot"], 0.1001)
        self.assertTrue(R.extent_problems(c, other, road))      # the road outside the slot moved

    def test_the_road_shape_is_make_grade_climbs(self):
        self.assertTrue(R.check_engine_env())
        with mock.patch.object(R, "RAMP_S", 7.0):
            with self.assertRaises(AssertionError):
                R.check_engine_env()

    def test_the_environments_cycle(self):
        road = R.generate(SYNTHETIC_SEED)[0]
        c = R.env_cycle(road)
        self.assertEqual((c["t_amb"], c["p_baro"], c["humidity"]), (315.0, 101.3, 0.012))
        self.assertEqual(len(c["t"]), 900)
        bad = copy.deepcopy(road)
        bad["cycle"]["t_amb"][5] = 316.0
        with self.assertRaises(ValueError):
            R.env_cycle(bad)

    def test_row_102s_table_of_H(self):
        # the taus row 102 quotes (the B58's from the smoke runs, the EPA three complete.json's), and the
        # row's own H and sample steps (H x (1/15, 1/6, 1/2, 1), step int(h / dt))
        taus = {"b58": 47.33506914379, "mazda_25t": 42.74181271696412, "honda_l15b7": 47.67174074702707,
                "ford_27tt": 66.76200860052332}
        want = {"b58": ((23.67, [1, 3, 11, 23]), (71.00, [4, 11, 35, 71])),
                "mazda_25t": ((21.37, [1, 3, 10, 21]), (64.11, [4, 10, 32, 64])),
                "honda_l15b7": ((23.84, [1, 3, 11, 23]), (71.51, [4, 11, 35, 71])),
                "ford_27tt": ((33.38, [2, 5, 16, 33]), (100.14, [6, 16, 50, 100]))}
        got = R.h_table(taus, (0.5, 1.5), dt=1.0)
        for e, (lo, hi) in want.items():
            for r, (H, steps) in (("0.5", lo), ("1.5", hi)):
                self.assertEqual(round(got[e][r]["H_s"], 2), H, (e, r))
                self.assertEqual(got[e][r]["sample_steps"], steps, (e, r))

    def test_the_draw_asks_roads_ceiling_for_every_variant(self):
        import roads_ceiling as RC
        self.assertEqual(set(R.DRAW_VARIANTS), set(RC.ALL_VARIANTS))
        self.assertEqual(set(R.DRAW_READINGS), set(RC.READINGS))
        self.assertEqual((R.ENGINES, R.EPA_ENGINES), (RC.ENGINES, RC.EPA_ENGINES))
        with mock.patch.object(R, "DRAW_VARIANTS", ("cg", "a")):           # a REAL draw that asks for less
            with self.assertRaises(R.Refused):
                R.first_draw(123, seed_kind="REAL", n_roads=1, engines=R.ENGINES, ratios=(1.5,),
                             variants=R.DRAW_VARIANTS, readings=R.DRAW_READINGS, companions=True, jobs=1,
                             log=print)


class Streams(Guarded):
    def test_deterministic(self):
        self.assertEqual(R.generate(SYNTHETIC_SEED), R.generate(SYNTHETIC_SEED))
        self.assertEqual(R.practice_roads(SYNTHETIC_SEED), R.practice_roads(SYNTHETIC_SEED))
        self.assertEqual(R.training_share_road(SYNTHETIC_SEED, 7), R.training_share_road(SYNTHETIC_SEED, 7))
        self.assertNotEqual(R.generate(SYNTHETIC_SEED), R.generate(SYNTHETIC_SEED + 1))

    def test_separate(self):
        s, k = SYNTHETIC_SEED, 3
        first = np.random.default_rng(s).random(8)
        rep = R.replacement_rng(s, k).random(8)
        red = R.redraw_rng(s, k).random(8)
        pra = np.random.default_rng([s, 0x50]).random(8)
        tra = np.random.default_rng([s, 0x7A, 11]).random(8)
        seqs = [first, rep, red, pra, tra, R.replacement_rng(s, k + 1).random(8)]
        for i in range(len(seqs)):
            for j in range(i + 1, len(seqs)):
                self.assertFalse(np.array_equal(seqs[i], seqs[j]), (i, j))
        self.assertTrue(np.array_equal(rep, np.random.default_rng([s, 0x1D, k]).random(8)))
        self.assertTrue(np.array_equal(red, np.random.default_rng([s, 0xC5, k]).random(8)))
        self.assertNotEqual(R.training_share_road(s, 1)["cycle"]["grade"], R.training_share_road(s, 2)["cycle"]["grade"])

    def test_the_practice_set_by_hand(self):
        import engine_env as E
        rng = np.random.default_rng([SYNTHETIC_SEED, 0x50])
        got = R.practice_roads(SYNTHETIC_SEED)
        for i, road in enumerate(got):
            lead, climbs, _ = hand_layout(rng)
            w_track = float(E.TRACK_W_MIN + (E.TRACK_W_MAX - E.TRACK_W_MIN) * rng.random())
            w_rest = rng.dirichlet(np.ones(2)) * (1.0 - w_track)
            self.assertEqual(road["episode_seed"], 4000 + i)
            self.assertEqual(road["weights"], [w_track, float(w_rest[0]), float(w_rest[1])])
            self.assertEqual([(c["onset_s"], c["L_s"], c["grade"]) for c in road["climbs"]],
                             [(float(s), float(L), g) for s, L, g, _ in climbs])

    def test_the_training_share_by_hand(self):
        rng = np.random.default_rng([SYNTHETIC_SEED, 0x7A, 5])
        lead, climbs, _ = hand_layout(rng)
        road = R.training_share_road(SYNTHETIC_SEED, 5)
        self.assertEqual([(c["onset_s"], c["L_s"], c["grade"]) for c in road["climbs"]],
                         [(float(s), float(L), g) for s, L, g, _ in climbs])
        self.assertIsNone(road["weights"])


def fake_c5(verdicts):
    """A c5_on_car stand-in: verdicts(car_name, grade) -> "fails" | "passes" | "nogated"."""
    def c5(plant, road, climb, *, margin):
        v = verdicts(plant, float(climb["grade"]))
        out = types.SimpleNamespace(outcome="fails" if v == "fails" else ("thinly_checked" if v == "nogated" else "passes"),
                                    n_gated=0 if v == "nogated" else 10, failing_steps=(5,) if v == "fails" else (),
                                    gated_share=0.0 if v == "nogated" else 0.9, transition_share=0.1,
                                    thin=v == "nogated", n_steps=11)
        return (), out
    return c5


class Replacement(Guarded):
    def setUp(self):
        self.roads = R.generate(SYNTHETIC_SEED)[:2]
        self.plants = {"b58": "b58", "ford_27tt": "ford_27tt"}     # names only: C5 is mocked
        self.lines = []

    def run_loop(self, verdicts):
        with mock.patch.object(R, "c5_on_car", fake_c5(verdicts)):
            return R.replacement_loop(self.roads, SYNTHETIC_SEED, plants=self.plants,
                                      gating={"b58", "ford_27tt"}, log=self.lines.append)

    def test_the_bound_and_the_flat_slot(self):
        target = self.roads[0]["climbs"][1]["slot"]
        g0 = self.roads[0]["climbs"][1]["grade"]
        bad = {g0} | {float(x) for x in R.replacement_rng(SYNTHETIC_SEED, target).uniform(0.10, 0.12, 100)}
        final, recs, c5 = self.run_loop(lambda car, g: "fails" if (car == "ford_27tt" and g in bad) else "passes")
        rec = [r for r in recs if r["slot"] == target][0]
        self.assertEqual(rec["outcome"], "flat")
        self.assertEqual(len(rec["candidates"]), 101)
        self.assertEqual([c["grade"] for c in rec["candidates"][1:]],
                         [float(x) for x in R.replacement_rng(SYNTHETIC_SEED, target).uniform(0.10, 0.12, 100)])
        self.assertIn("C5 case (1)", rec["candidates"][0]["failed"][0]["test"])
        road = final[0]
        self.assertNotIn(target, [c["slot"] for c in road["climbs"]])
        self.assertEqual([s["slot"] for s in road["flat_slots"]], [target])
        a, b = rec["first_step"], rec["last_step"]
        self.assertTrue(np.all(np.asarray(road["cycle"]["grade"])[a:b + 1] == 0.0))
        self.assertEqual([r["slot"] for r in recs], list(range(len(recs))))      # every index kept
        self.assertEqual(R.ramp_problems(road["cycle"]["grade"], dt=1.0), [])
        self.assertNotIn(str(target), c5["ford_27tt"])
        self.assertTrue(any("made flat" in x for x in self.lines))

    def test_a_replaced_grade_is_the_slots_own_stream(self):
        target = self.roads[1]["climbs"][0]["slot"]
        draws = [float(x) for x in R.replacement_rng(SYNTHETIC_SEED, target).uniform(0.10, 0.12, 3)]
        bad = {self.roads[1]["climbs"][0]["grade"], draws[0], draws[1]}
        final, recs, _ = self.run_loop(lambda car, g: "nogated" if (car == "b58" and g in bad) else "passes")
        rec = [r for r in recs if r["slot"] == target][0]
        self.assertEqual((rec["outcome"], rec["final_grade"], len(rec["candidates"])), ("replaced", draws[2], 4))
        self.assertIn("no gated step on b58", rec["candidates"][1]["failed"][0]["test"])
        self.assertEqual(R.climb_of(final[1], target)["grade"], draws[2])
        others = [r for r in recs if r["slot"] != target]
        self.assertTrue(all(r["outcome"] == "accepted" and len(r["candidates"]) == 1 for r in others))


class C5(Guarded):
    """The probe's c5tau.txt, first climb of L67 at 130 km/h (results/EPA_ROADS/probe_2026-10-30): the
    outcome and the smallest margin of each kind over the climb's non-transition steps, to 4 places."""
    EXPECT = {("b58", 0.10): ("passes", {"held": 0.2135, "rejected": 0.0883}),
              ("mazda_25t", 0.10): ("passes", {"held": 0.5137, "held(ungated)": 0.1318, "rejected": 0.2280}),
              ("honda_l15b7", 0.10): ("passes", {"eco": 0.2358}),
              ("ford_27tt", 0.12): ("passes", {"held": 0.1793, "held(ungated)": 0.2285, "rejected": 0.0287})}

    def test_the_probes_margins_come_back(self):
        for (e, g), (outcome, mins) in self.EXPECT.items():
            road = R.make_road(k=0, episode_seed=1000, weights=(0.69, 0.01, 0.3), lead=180,
                               climbs=[(180, 67, g, 100), (347, 67, g, 100)], discarded=(67, g, 100), first_slot=0)
            steps, out = R.c5_on_car(R.plant_of(e), road, road["climbs"][0], margin=R.C5_MARGIN)
            got = {}
            for s in steps:
                if s.transition:
                    continue
                for name, m, gates in s.margins:
                    key = name.split("_")[1] + ("" if gates else "(ungated)")
                    got[key] = min(got.get(key, 9.0), m)
            self.assertEqual(out.outcome, outcome, e)
            self.assertEqual({k: round(v, 4) for k, v in got.items()}, mins, e)

    def test_decision_40s_diagnostic_and_the_coverage_flags_on_the_honda(self):
        """The reports that discard nothing, on a short SYNTHETIC road (one climb, 300 s): decision 40's
        diagnostic at every gated step, counted on the kickdown and power-limited branches with every
        branch beside them (MD:1236); the coverage flags against a synthetic coverage (never the
        contract's, which this class may not open)."""
        road = R.make_road(k=0, episode_seed=1000, weights=(0.69, 0.01, 0.3), lead=150,
                           climbs=[(150, 67, 0.11, 100)], discarded=(67, 0.11, 100), first_slot=0)
        for key in ("t", "v_mps", "grade", "t_amb"):
            road["cycle"][key] = road["cycle"][key][:300]
        climb = road["climbs"][0]
        res = R._identity_task((R.CVT_ENGINE, road, True))
        self.assertTrue(res["holds"], res)
        run = res["arrays"]
        plant = R.plant_of(R.CVT_ENGINE)
        steps, _ = R.c5_on_car(plant, road, climb, margin=R.C5_MARGIN)
        d = R.cvt_diagnostics(plant, road, climb, steps, run, margin=R.C5_MARGIN)
        gated = [s for s in steps if s.gated]
        self.assertGreater(len(gated), 0)
        self.assertEqual(d["all_branches"]["gated_steps"], len(gated))
        self.assertEqual(sum(d["steps_by_branch"].values()), len(gated))
        self.assertEqual(d["gated_steps"], sum(1 for x in d["steps"] if x["branch"] in R.CVT_GATED_BRANCHES))
        self.assertLessEqual(d["not_connected"], d["all_branches"]["not_connected"])
        tot = R.cvt_totals([d, d])
        self.assertEqual(tot["all_branches"]["gated_steps"], 2 * len(gated))
        import epa_stats as ES
        cov = {"calibration_fired": {ES.map_band_key(m): {"speed_rpm": [0.0, 1e9]} for m in run["map_kpa"]},
               "calibration_hot": {}}
        f = R.coverage_flags(R.CVT_ENGINE, road, climb, run, coverage=cov)
        n = climb["last_step"] - climb["first_step"] + 1
        self.assertEqual((f["steps"], f["covered_fired"], f["covered_hot"]), (n, True, False))
        self.assertEqual(f["steps_outside_calibration_hot"], n)
        self.assertEqual(f["steps_above_115_kmh"], n)              # 130 km/h on the whole climb
        self.assertTrue(f["hold_longer_than_30_s"])


def git(root, *args):
    r = subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-c", "core.autocrlf=false", *args],
                       cwd=root, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"git {args}: {r.stderr}")
    return r.stdout.strip()


def module_with(g, j):
    with open(os.path.join(HERE, "epa_roads.py"), encoding="utf-8") as fh:
        src = fh.read().replace("\r\n", "\n")
    assert "\nCOMMITMENT_G = None\n" in src and "\nCOMMITMENT_J = None\n" in src
    return (src.replace("\nCOMMITMENT_G = None\n", f"\nCOMMITMENT_G = {g!r}\n")
            .replace("\nCOMMITMENT_J = None\n", f"\nCOMMITMENT_J = {j!r}\n"))


class Reveal(Guarded):
    A_G, A_J = 2 ** 200 + 918273645, 2 ** 201 + 5647382910          # SYNTHETIC private integers
    H_G = hashlib.sha256(str(2 ** 200 + 918273645).encode("ascii")).hexdigest()
    H_J = hashlib.sha256(str(2 ** 201 + 5647382910).encode("ascii")).hexdigest()
    NOTE = "SYNTHETIC: the test's coding defect, fixed in no commit"

    def test_the_arithmetic(self):
        self.assertEqual(R.commitment_hash(self.A_G), self.H_G)
        self.assertTrue(R.reveal_matches(self.A_J, self.H_J))
        self.assertFalse(R.reveal_matches(self.A_J + 1, self.H_J))
        sha = "0123456789abcdef0123456789abcdef01234567"
        want = int(hashlib.sha256(f"{self.A_G}:{self.A_J}:{sha}".encode("ascii")).hexdigest()[:15], 16)
        self.assertEqual(R.roads_seed_from(self.A_G, self.A_J, sha), want)
        self.assertTrue(0 <= want < 16 ** 15)
        for bad in ("007", "-1", " 1", "1.0", "", "1e3", "0", "918273645", str(2 ** 128 - 1)):
            with self.assertRaises(R.Refused):
                R.parse_reveal(bad)
        self.assertEqual(R.parse_reveal(str(2 ** 128)), 2 ** 128)
        with self.assertRaises(ValueError):
            R.roads_seed_from(1, 2, "abc")

    def test_a_small_private_integer_is_refused(self):
        """Row 96's seed is hidden only if neither integer can be searched from its hash line."""
        for a in (0, 5, 918273645, 2 ** 128 - 1, True, 2.0 ** 200):
            with self.assertRaises(ValueError):
                R.commitment_hash(a)
        self.assertFalse(R.reveal_matches(5, hashlib.sha256(b"5").hexdigest()))
        x, y = R.new_private_integer(), R.new_private_integer()
        self.assertNotEqual(x, y)
        self.assertTrue(2 ** 255 <= x < 2 ** 256)
        self.assertRegex(R.commitment_hash(x), r"^[0-9a-f]{64}$")
        self.assertEqual(R.parse_reveal(str(x)), x)

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="epa_roads_git_")
        self.root = os.path.join(self.tmp, "repo")
        self.origin = os.path.join(self.tmp, "origin.git")
        os.makedirs(self.root)
        git(self.tmp, "init", "-q", "--bare", self.origin)
        git(self.root, "init", "-q")
        git(self.root, "checkout", "-q", "-b", "GRA-test")
        git(self.root, "remote", "add", "origin", self.origin)
        self.commit(module_with(None, None), "the roads module")
        self.c1 = git(self.root, "rev-parse", "HEAD")
        self.commit(module_with(self.H_G, self.H_J), "the roads commit: both hash lines")
        self.c2 = git(self.root, "rev-parse", "HEAD")
        self.push()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def commit(self, src, msg, rel="epa_roads.py"):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(src)
        git(self.root, "add", rel)
        git(self.root, "commit", "-q", "-m", msg)

    def push(self):
        git(self.root, "push", "-q", "origin", "HEAD:refs/heads/GRA-test")
        git(self.root, "fetch", "-q", "origin")

    def record_attempt(self, msg):
        """The protocol between attempts: the log and the printed outputs are committed and pushed."""
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", msg)
        self.push()

    def mocks(self, first_draw):
        """draw()'s plant work stood in for: the frozen check passes, the hashes are empty, the ceiling
        module gives its ratios; first_draw is the test's."""
        frozen = {"versions": {"python": "3.13.2", "platform": "SYNTHETIC"}, "plants": {}}
        prov = {"files": {}, "contract": {}, "plants": {}, "versions": {}}
        return [mock.patch.object(R, "frozen_problems", lambda *a, **k: ([], frozen)),
                mock.patch.object(R, "provenance", lambda **k: prov),
                mock.patch.object(R, "first_draw", first_draw),
                mock.patch.object(R, "_ceiling_module", lambda: types.SimpleNamespace(RATIOS=(0.5, 1.5)))]

    def draw(self, *, a_j=None, announced=None, note=None, first_draw=None):
        def fake(roads_seed, **kw):
            return {"schema": R.ROADS_SCHEMA, "passes_T": {"passes": False}, "hashes": {"files": {}, "contract": {}}}
        with contextlib.ExitStack() as st:
            for m in self.mocks(first_draw or fake):
                st.enter_context(m)
            return R.draw(str(self.A_G), str(self.A_J if a_j is None else a_j),
                          roads_commit_announced=announced or self.c2, note=note, root=self.root, jobs=1)

    def refusal(self, **kw):
        with self.assertRaises(R.Refused) as cm:
            self.draw(**kw)
        return " | ".join(cm.exception.args[0])

    def test_the_first_attempt_runs_on_the_roads_commit_itself(self):
        c, g, j = R.find_roads_commit(root=self.root)
        self.assertEqual((c, g, j), (self.c2, self.H_G, self.H_J))
        probs, ctx = R.draw_preconditions(root=self.root, roads_commit=c)
        self.assertEqual(probs, [])
        self.assertTrue(ctx["clean"] and ctx["pushed"] and ctx["remote_sha"] == self.c2)
        # a pushed descendant that changes the design after the roads commit is refused at attempt 1
        # (the integrity review's case A); so is one that changes only a file nothing hashes
        tuned = module_with(self.H_G, self.H_J).replace("GRADE_LO, GRADE_HI = 0.10, 0.12",
                                                        "GRADE_LO, GRADE_HI = 0.10, 0.105")
        self.assertNotEqual(tuned, module_with(self.H_G, self.H_J))
        for src, rel in ((tuned, "epa_roads.py"), ("unhashed\n", "notes.txt")):
            self.commit(src, "a commit after the roads commit", rel=rel)
            self.push()
            self.assertIn("the first attempt runs on the roads commit", self.refusal())
        self.assertFalse(os.path.exists(os.path.join(self.root, R.ATTEMPTS_REL)))   # nothing was written

    def test_the_announced_roads_commit_is_the_one_found(self):
        self.assertIn("announced before the reveal", self.refusal(announced=self.c1))
        self.assertIn("40-digit", self.refusal(announced=self.c2[:12]))

    def test_the_refusals(self):
        c = R.find_roads_commit(root=self.root)[0]
        with open(os.path.join(self.root, "stray.txt"), "w") as fh:
            fh.write("x")
        self.assertTrue(any("not clean" in p for p in R.draw_preconditions(root=self.root, roads_commit=c)[0]))
        os.remove(os.path.join(self.root, "stray.txt"))
        self.commit("{}\n", "a record", rel=R.ROADS_REL)
        probs = R.draw_preconditions(root=self.root, roads_commit=c)[0]
        self.assertTrue(any("written once" in p for p in probs), probs)
        self.assertTrue(any("committed in HEAD's history" in p for p in probs), probs)
        self.assertTrue(any("push it first" in p for p in probs), probs)
        git(self.root, "checkout", "-q", "-b", "other", self.c1)
        self.commit(module_with(self.H_G, self.H_J), "the hash lines on another line of history")
        probs = R.draw_preconditions(root=self.root, roads_commit=c)[0]
        self.assertTrue(any("not a descendant" in p for p in probs), probs)
        git(self.root, "checkout", "-q", "--detach", self.c1)
        with self.assertRaises(R.Refused):
            R.find_roads_commit(root=self.root)          # the hash lines are missing

    def test_pushed_is_the_remotes_own_answer(self):
        # a local origin ref set by hand does not make HEAD pushed: the remote is asked (git ls-remote)
        self.commit("x\n", "not pushed", rel="notes.txt")
        git(self.root, "update-ref", "refs/remotes/origin/GRA-test", "HEAD")
        head = git(self.root, "rev-parse", "HEAD")
        pushed, sha, why = R.remote_state(self.root, head)
        self.assertEqual((pushed, sha), (False, self.c2))
        self.assertIn("push it first", why)

    def test_a_hash_line_changed_or_set_alone_is_refused(self):
        self.commit(module_with(self.H_G, "f" * 64), "Jad's line changed")
        with self.assertRaises(R.Refused) as cm:
            R.find_roads_commit(root=self.root)
        self.assertIn("other values", str(cm.exception))
        git(self.root, "checkout", "-q", "-b", "split", self.c1)
        self.commit(module_with(self.H_G, None), "Ghassan's line alone")
        self.commit(module_with(self.H_G, self.H_J), "Jad's line later")
        with self.assertRaises(R.Refused):
            R.find_roads_commit(root=self.root)

    def test_a_bad_reveal_is_logged_stops_and_ends_the_roads_step(self):
        log = os.path.join(self.root, R.ATTEMPTS_REL)

        def reached(*a, **k):
            raise AssertionError("roads_seed was used after a reveal that does not match")
        with mock.patch.object(R, "roads_seed_from", reached):
            with self.assertRaises(R.RoadsStop) as cm:
                self.draw(a_j=self.A_J + 1, first_draw=reached)
            self.assertNotIsInstance(cm.exception, R.CodingDefect)
            first = R.read_attempts(log)
            self.assertEqual([x["event"] for x in first], ["start", "outcome"])
            self.assertEqual((first[0]["reveal_matches"], first[1]["outcome"], first[1]["coding_defect"]),
                             ({"ghassan": True, "jad": False}, "stop", False))
            self.assertEqual(first[0]["roads_commit_announced"], self.c2)
            self.record_attempt("attempt 1 recorded")
            self.assertIn("has ended", self.refusal(note=self.NOTE, first_draw=reached))   # nobody retries
        self.assertEqual(len(R.read_attempts(log)), 2)

    def test_the_attempts_log_is_append_only(self):
        """The integrity review's cases C and C2: deleting the committed log, or cutting its stop line,
        does not reopen a roads step a mismatched reveal ended."""
        log = os.path.join(self.root, R.ATTEMPTS_REL)
        with self.assertRaises(R.RoadsStop):
            self.draw(a_j=self.A_J + 1)
        self.record_attempt("attempt 1 recorded")
        with open(log, encoding="utf-8") as fh:
            lines = fh.read().splitlines(keepends=True)
        with open(log, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(lines[0])                                    # the stop line cut
        self.record_attempt("the log cut")
        self.assertIn("does not extend", self.refusal(note=self.NOTE))
        git(self.root, "rm", "-q", R.ATTEMPTS_REL)
        self.record_attempt("the log deleted")
        self.assertIn("was deleted in commit", self.refusal(note=self.NOTE))

    def test_no_second_set_is_drawn(self):
        """The integrity review's case B: once a set is drawn, removing roads.json does not allow another."""
        sha = self.draw()
        self.assertEqual(R.read_attempts(os.path.join(self.root, R.ATTEMPTS_REL))[-1]["roads_sha"], sha)
        self.record_attempt("the roads (attempt 1)")
        git(self.root, "rm", "-q", R.ROADS_REL)
        self.record_attempt("roads.json removed")
        msg = self.refusal(note=self.NOTE)
        self.assertIn("wrote its record (roads)", msg)
        self.assertIn("committed in HEAD's history", msg)

    def test_the_attempt_is_logged_before_roads_seed_is_used(self):
        """The first attempt stops for a coding defect, which allows a second from the same roads_seed
        (row 98) with a note; at each attempt the log's start line exists when roads_seed is first
        computed, and the second's records every file and commit since the roads commit."""
        log = os.path.join(self.root, R.ATTEMPTS_REL)
        seen = {"at_first_use": [], "seeds": []}
        real_seed = R.roads_seed_from

        def seed_spy(a, b, c):
            seen["at_first_use"].append(R.read_attempts(log))
            return real_seed(a, b, c)

        def fake_draw(roads_seed, **kw):
            seen["seeds"].append(roads_seed)
            print("printed by attempt", len(seen["seeds"]))
            if len(seen["seeds"]) == 1:
                raise R.CodingDefect("a SYNTHETIC identity failure")
            return {"schema": R.ROADS_SCHEMA, "passes_T": {"passes": False}, "hashes": {"files": {}, "contract": {}}}
        with mock.patch.object(R, "roads_seed_from", seed_spy):
            with self.assertRaises(R.CodingDefect):
                self.draw(first_draw=fake_draw)
            self.assertEqual([(x["event"], x.get("outcome"), x.get("coding_defect")) for x in R.read_attempts(log)],
                             [("start", None, None), ("outcome", "stop", True)])
            self.record_attempt("attempt 1 recorded (a coding defect)")
            self.assertIn("--note", self.refusal(first_draw=fake_draw))
            sha = self.draw(note=self.NOTE, first_draw=fake_draw)
        self.assertEqual([[x["event"] for x in e] for e in seen["at_first_use"]],
                         [["start"], ["start", "outcome", "start"]])
        last_start = seen["at_first_use"][1][-1]
        self.assertEqual((last_start["attempt"], last_start["clean"], last_start["roads_commit"], last_start["note"]),
                         (2, True, self.c2, self.NOTE))
        self.assertIn("platform", last_start["versions"])
        self.assertIn(R.ATTEMPTS_REL, last_start["files_changed_since_roads_commit"])
        self.assertEqual(len(last_start["commits_since_roads_commit"]), 1)
        self.assertEqual(seen["seeds"], [real_seed(self.A_G, self.A_J, self.c2)] * 2)
        after = R.read_attempts(log)
        self.assertEqual((after[-1]["event"], after[-1]["outcome"], after[-1]["roads_sha"]), ("outcome", "roads", sha))
        with open(os.path.join(self.root, R.ROADS_REL), encoding="utf-8") as fh:
            rec = json.load(fh)
        self.assertEqual(rec["commit_reveal"]["roads_seed"], seen["seeds"][0])
        self.assertEqual(len(rec["attempts"]), 3)
        p1 = os.path.join(self.root, R.ROADS_DIR_REL, "attempt_1_printed.txt")
        p2 = os.path.join(self.root, R.ROADS_DIR_REL, "attempt_2_printed.txt")
        from thresholds import common
        self.assertEqual(rec["printed_earlier"], [{"attempt": 1, "path": f"{R.ROADS_DIR_REL}/attempt_1_printed.txt",
                                                   "sha_text": common.sha_text(p1)}])
        with open(p2, encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("printed by attempt 2", text)
        self.assertIn("roads.json written", text)                  # the last line is in the printed file
        self.assertEqual(after[-1]["printed_sha_text"], common.sha_text(p2))


def hashed_copy(dst):
    """The files roads.json would hash, copied to `dst`, and the contract's two as SYNTHETIC stand-ins
    (a Guarded test never opens the real contract)."""
    import engines
    import fingerprint
    files = set(R.import_closure(R.MODULE_REL, root=HERE))
    for m in R.NAMED_MODULES:
        files.update(R.import_closure(m, root=HERE))
    files.update(fingerprint.PLANT_CODE)
    for e in R.ENGINES:
        files.update(engines.spec_files(e))
    for f in files:
        os.makedirs(os.path.dirname(os.path.join(dst, f)), exist_ok=True)
        shutil.copyfile(os.path.join(HERE, f), os.path.join(dst, f))
    for f in R.CONTRACT_FILES:
        os.makedirs(os.path.dirname(os.path.join(dst, f)), exist_ok=True)
        with open(os.path.join(dst, f), "w", encoding="utf-8", newline="\n") as fh:
            fh.write(f"SYNTHETIC stand-in for {f}: the test's copy, never the contract\n")


def flip_one_byte(path):
    with open(path, "rb") as fh:
        raw = bytearray(fh.read())
    i = next(i for i, b in enumerate(raw) if chr(b).isalpha())
    old = raw[i]
    raw[i] = ord("b") if chr(old) != "b" else ord("c")
    with open(path, "wb") as fh:
        fh.write(bytes(raw))
    return old, i


def synthetic_summary(drops):
    """A SYNTHETIC results/EPA_VALIDATION/summary.json body: each EPA engine's drop and re-check margin."""
    return {"engines": {e: {"drop": bool(drops.get(e, False)),
                            "c5_recheck_margin": {"margin_fraction": 0.03, "margin_unit": "percent"}}
                        for e in R.EPA_ENGINES}}


class Records(Guarded):
    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="epa_roads_rec_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_roads_json_is_write_once(self):
        p = os.path.join(self.tmp, "roads.json")
        sha = R.write_once(p, {"a": 1})
        from thresholds import common
        self.assertEqual(sha, common.sha_text(p))
        with self.assertRaises(R.Refused):
            R.write_once(p, {"a": 2})
        with open(p, encoding="utf-8") as fh:
            self.assertEqual(json.load(fh), {"a": 1})
        with self.assertRaises(ValueError):
            R.write_once(os.path.join(self.tmp, "nan.json"), {"a": float("nan")})

    def test_a_one_byte_change_in_each_hashed_file_is_refused(self):
        root = os.path.join(self.tmp, "tree")
        hashed_copy(root)
        record = {"hashes": R.provenance(root=root, engines=R.ENGINES), "seed_kind": "SYNTHETIC",
                  "commit_reveal": {"roads_seed": SYNTHETIC_SEED}, "roads": []}
        self.assertEqual(R.verify_record(record, root=root), [])
        files = sorted(record["hashes"]["files"]) + sorted(record["hashes"]["contract"])
        for name in R.NAMED_MODULES + ("epa_roads.py", "plant.py", "engine_specs/b58.toml"):
            self.assertIn(name, files)
        for f in files:
            p = os.path.join(root, f)
            old, i = flip_one_byte(p)
            probs = R.verify_record(record, root=root)
            self.assertEqual(probs, [f"{f}: its sha_text is not roads.json's"], f)
            with open(p, "rb") as fh:
                raw = bytearray(fh.read())
            raw[i] = old
            with open(p, "wb") as fh:
                fh.write(bytes(raw))
        self.assertEqual(R.verify_record(record, root=root), [])
        # a package placed beside a hashed module is what Python imports, while every hash still matches
        # (the integrity review's shadow.py): refused
        os.makedirs(os.path.join(root, "epa_stats"))
        with open(os.path.join(root, "epa_stats", "__init__.py"), "w", encoding="utf-8") as fh:
            fh.write("# SYNTHETIC shadow\n")
        probs = R.verify_record(record, root=root)
        self.assertEqual(len(probs), 1, probs)
        self.assertIn("epa_stats.py is shadowed", probs[0])
        shutil.rmtree(os.path.join(root, "epa_stats"))
        self.assertEqual(R.verify_record(record, root=root), [])
        # the redraws and the re-check refuse before they draw anything
        flip_one_byte(os.path.join(root, "epa_stats.py"))

        def reached(*a, **k):
            raise AssertionError("drew something before the refusal")
        with mock.patch.object(R, "_ceiling_module", reached), mock.patch.object(R, "recheck_slots", reached):
            with self.assertRaises(R.Refused):
                R.redraw(record, roads_sha_value="x", margins={}, margins_source="SYNTHETIC", dropped=(), jobs=1,
                         root=root, log=print, engines=R.SMOKE_ENGINES, max_slots=1)
            os.makedirs(os.path.join(root, R.ROADS_DIR_REL), exist_ok=True)
            with open(os.path.join(root, R.ROADS_REL), "w", encoding="utf-8") as fh:
                json.dump(record, fh)
            for kind in ("recheck", "redraw"):
                with self.assertRaises(R.Refused) as cm:
                    R.recheck_or_redraw(kind, summary_path=os.path.join(self.tmp, "absent.json"), dropped=(),
                                        note=None, jobs=1, root=root, out_path=None)
                self.assertIn("epa_stats.py: its sha_text is not roads.json's", str(cm.exception))
            with open(os.path.join(root, R.REDRAWS_REL), "w", encoding="utf-8") as fh:
                fh.write("{}\n")
            with self.assertRaises(R.Refused) as cm:              # written once, refused before anything
                R.recheck_or_redraw("redraw", summary_path=os.path.join(self.tmp, "absent.json"), dropped=(),
                                    note=None, jobs=1, root=root, out_path=None)
            self.assertIn("written once", str(cm.exception))

    def test_a_version_or_plant_change_is_refused(self):
        live = R.live_provenance(R.ENGINES)
        files = R.sha_texts(R.hashed_files(root=HERE, engines=R.ENGINES), root=HERE)
        record = {"hashes": {"files": files, "contract": {}, "plants": live["plants"], "versions": live["versions"]}}
        self.assertEqual(R.verify_record(record, root=HERE), [])
        for path in (("versions", "numpy"), ("plants", "ford_27tt", "plant_sha"), ("plants", "b58", "engine_sha")):
            rec = copy.deepcopy(record)
            d = rec["hashes"]
            for key in path[:-1]:
                d = d[key]
            d[path[-1]] = "something else"
            probs = R.verify_record(rec, root=HERE)
            self.assertEqual(len(probs), 1, probs)
            self.assertIn(path[-1], probs[0])
        rec = copy.deepcopy(record)
        rec["hashes"]["files"].pop("k3_knee.py")                    # a module the record does not name
        self.assertEqual(R.verify_record(rec, root=HERE), ["k3_knee.py: reached by the code as it stands, not "
                                                            "hashed by roads.json"])

    def test_the_smoke_run_writes_outside_the_repository_only(self):
        """The roads folder is the same before and after two refused smoke runs into the repository. It is
        compared by content, not required to be empty: after the draw (ORDER step 6) it holds roads.json and
        the attempts log, and this file runs again at steps 6, 8, 9 and 12 (the forward-path audit of 31
        October 2026)."""
        folder = os.path.join(HERE, R.ROADS_DIR_REL)

        def state():
            names = sorted(os.listdir(folder)) if os.path.isdir(folder) else []
            out = {}
            for n in names:
                p = os.path.join(folder, n)
                if os.path.isfile(p):
                    with open(p, "rb") as fh:
                        out[n] = hashlib.sha256(fh.read()).hexdigest()
            return out
        before = state()
        for inside in (HERE, folder):
            with self.assertRaises(R.Refused):
                R.smoke(SYNTHETIC_SEED, out_dir=inside, jobs=1, with_redraw=False, full=False)
        self.assertEqual(state(), before)

    def test_a_synthetic_seed_is_below_2_32(self):
        """The integrity review's case D: the 60-bit roads_seed is never a SYNTHETIC seed."""
        sixty = R.roads_seed_from(2 ** 200, 2 ** 201, "0123456789abcdef0123456789abcdef01234567")
        for seed in (2 ** 32, sixty, -1, 1.0, True):
            with self.assertRaises(R.Refused):
                R.smoke(seed, out_dir=self.tmp, jobs=1, with_redraw=False, full=False)
            with self.assertRaises(R.Refused):
                R.first_draw(seed, seed_kind="SYNTHETIC", n_roads=1, engines=R.SMOKE_ENGINES, ratios=(1.5,),
                             variants=R.SMOKE_VARIANTS, readings=R.SMOKE_READINGS, companions=False, jobs=1, log=print)
        self.assertEqual(os.listdir(self.tmp), [])                   # refused before anything was written
        self.assertIsNone(R._seed_problem(2 ** 32 - 1, seed_kind="SYNTHETIC"))
        self.assertIsNone(R._seed_problem(sixty, seed_kind="REAL"))
        self.assertIsNotNone(R._seed_problem(16 ** 15, seed_kind="REAL"))

    def test_the_guard_refuses_what_it_names(self):
        for p in ("logs/epa/x.txt", "data/engines/ford_27tt/epa_x", "results/EPA_VALIDATION/summary.json",
                  os.path.join(self.tmp, "x.csv")):
            self.assertTrue(R.refused_path(os.path.join(HERE, p) if not os.path.isabs(p) else p), p)
        self.assertFalse(R.refused_path(os.path.join(HERE, "data", "engines", "ford_27tt", "derived_params.json")))
        with self.assertRaises(PermissionError):
            open(os.path.join(self.tmp, "x.csv"), "w")

    def test_summary_names_one_file(self):
        """The integrity review's guards.py: --summary may name only results/EPA_VALIDATION/summary.json,
        so the guard's one exception cannot be pointed at a table (no file is opened here)."""
        good = os.path.join(HERE, R.SUMMARY_REL)
        self.assertEqual(R.summary_path_allowed(good, root=HERE), os.path.abspath(good))
        for bad in (os.path.join(HERE, "logs", "epa", "x.csv"), os.path.join(HERE, "data", "engines", "ford_27tt",
                                                                             "epa_channels.csv"),
                    os.path.join(HERE, "results", "EPA_VALIDATION", "ford_27tt", "rows.json"),
                    os.path.join(self.tmp, "results", "EPA_VALIDATION", "summary.json")):
            with self.assertRaises(R.Refused):
                R.summary_path_allowed(bad, root=HERE)
        self.assertEqual(R.main(["recheck", "--summary", os.path.join(HERE, "logs", "epa", "x.csv"),
                                 "--dropped", "none", "--jobs", "1"]), 2)

    def test_margins_and_drops_come_from_the_summary(self):
        m = R.margins_from_summary(synthetic_summary({}), engines=R.ENGINES)
        self.assertEqual(m, {"b58": 0.019, "mazda_25t": 0.03, "honda_l15b7": 0.03, "ford_27tt": 0.03})
        low = synthetic_summary({})
        low["engines"]["ford_27tt"]["c5_recheck_margin"]["margin_fraction"] = 0.01
        with self.assertRaises(R.Refused):
            R.margins_from_summary(low, engines=R.ENGINES)
        self.assertEqual(R.dropped_problems(synthetic_summary({"ford_27tt": True}), ("ford_27tt",)), [])
        self.assertEqual(len(R.dropped_problems(synthetic_summary({"ford_27tt": True}), ())), 1)
        self.assertEqual(len(R.dropped_problems(synthetic_summary({}), ("mazda_25t",))), 1)
        with self.assertRaises(R.Refused):
            R._dropped("b58")


class RedrawLog(Guarded):
    """The redraws use roads_seed's 0xC5 streams, so they are an attempt (row 96): a start line before
    they draw, an outcome line after, run once (the integrity and correctness reviews)."""

    def setUp(self):
        super().setUp()
        self.tmp = tempfile.mkdtemp(prefix="epa_roads_redraw_")
        self.root = os.path.join(self.tmp, "repo")
        self.origin = os.path.join(self.tmp, "origin.git")
        os.makedirs(self.root)
        git(self.tmp, "init", "-q", "--bare", self.origin)
        git(self.root, "init", "-q")
        git(self.root, "checkout", "-q", "-b", "GRA-test")
        git(self.root, "remote", "add", "origin", self.origin)
        self.summary = os.path.join(self.root, R.SUMMARY_REL)
        R.install_guard((self.summary,))           # the guard's one exception, as main() installs it
        self.write(R.ROADS_REL, {"seed_kind": "SYNTHETIC", "hashes": {}, "roads": []})
        self.write(R.SUMMARY_REL, synthetic_summary({}))
        self.commit_all("the roads record and a SYNTHETIC summary")

    def tearDown(self):
        R.install_guard(())
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, rel, obj):
        p = os.path.join(self.root, rel)
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as fh:
            json.dump(obj, fh)

    def commit_all(self, msg):
        git(self.root, "add", "-A")
        git(self.root, "commit", "-q", "-m", msg)
        git(self.root, "push", "-q", "origin", "HEAD:refs/heads/GRA-test")

    def run_redraw(self, *, dropped=(), note=None):
        log = os.path.join(self.root, R.ATTEMPTS_REL)
        seen = []

        def spy(record, **kw):
            seen.append(R.read_attempts(log))
            return {"SYNTHETIC": True}
        with mock.patch.object(R, "verify_record", lambda record, root: []), mock.patch.object(R, "redraw", spy):
            R.recheck_or_redraw("redraw", summary_path=self.summary, dropped=dropped, note=note, jobs=1,
                                root=self.root, out_path=None)
        return seen

    def test_the_start_line_comes_before_the_redraws_and_they_run_once(self):
        seen = self.run_redraw()
        self.assertEqual(len(seen), 1)
        start = seen[0][-1]
        self.assertEqual((start["step"], start["event"], start["attempt"], start["clean"], start["pushed"]),
                         ("redraw", "start", 1, True, True))
        from thresholds import common
        self.assertEqual(start["summary"]["sha_text"], common.sha_text(self.summary))
        after = R.read_attempts(os.path.join(self.root, R.ATTEMPTS_REL))
        self.assertEqual([(x["event"], x.get("outcome")) for x in after], [("start", None), ("outcome", "redraws")])
        self.assertTrue(os.path.isfile(os.path.join(self.root, R.REDRAWS_REL)))
        self.commit_all("the redraws")
        git(self.root, "rm", "-q", R.REDRAWS_REL)
        self.commit_all("redraws.json removed")
        with self.assertRaises(R.Refused) as cm:
            self.run_redraw(note="SYNTHETIC")
        msg = " | ".join(cm.exception.args[0])
        self.assertIn("wrote its record (redraws)", msg)
        self.assertIn("committed in HEAD's history", msg)

    def test_a_dirty_tree_or_a_drop_list_that_disagrees_is_refused(self):
        with open(os.path.join(self.root, "stray.txt"), "w") as fh:
            fh.write("x")
        with self.assertRaises(R.Refused) as cm:
            self.run_redraw()
        self.assertIn("not clean", str(cm.exception))
        os.remove(os.path.join(self.root, "stray.txt"))
        with self.assertRaises(R.Refused) as cm:
            self.run_redraw(dropped=("ford_27tt",))
        self.assertIn("summary.json's section 7 says kept", str(cm.exception))
        self.assertFalse(os.path.exists(os.path.join(self.root, R.ATTEMPTS_REL)))     # nothing was written


class Tightenings(Guarded):
    """Row 97 and ORDER steps 6 and 8, on the real records once they exist."""

    def test_the_roads_record_names_its_reveal(self):
        roads = os.path.join(HERE, R.ROADS_REL)
        if not os.path.isfile(roads):
            self.skipTest("results/EPA_ROADS/roads.json is absent: the draw has not run (row 96)")
        with open(roads, encoding="utf-8") as fh:
            rec = json.load(fh)
        cr = rec["commit_reveal"]
        self.assertEqual(cr["roads_seed"], R.roads_seed_from(cr["reveal"]["ghassan"], cr["reveal"]["jad"],
                                                             cr["roads_commit"]))
        self.assertTrue(R.reveal_matches(cr["reveal"]["ghassan"], cr["hash_lines"]["ghassan"]))
        self.assertTrue(R.reveal_matches(cr["reveal"]["jad"], cr["hash_lines"]["jad"]))
        commit, g, j = R.find_roads_commit(root=HERE)
        self.assertEqual((cr["roads_commit"], cr["hash_lines"]["ghassan"], cr["hash_lines"]["jad"]), (commit, g, j))
        self.assertEqual(cr["roads_commit_announced"], commit)
        outs = [x for x in R.read_attempts(os.path.join(HERE, R.ATTEMPTS_REL))
                if x.get("step", "draw") == "draw" and x.get("outcome") == "roads"]
        self.assertEqual(len(outs), 1)
        self.assertEqual(outs[0]["roads_sha"], R.roads_sha(roads))

    def test_the_tightenings_name_the_roads_record(self):
        roads = os.path.join(HERE, R.ROADS_REL)
        tight = os.path.join(HERE, R.TIGHTENINGS_REL)
        if not os.path.isfile(tight):
            self.skipTest("results/EPA_TIGHTENINGS.json is absent: the tightenings have not run (row 104)")
        self.assertTrue(os.path.isfile(roads), "the tightenings exist and name a roads record that is not there")
        with open(roads, encoding="utf-8") as fh:
            rec = json.load(fh)
        with open(tight, encoding="utf-8") as fh:
            t = json.load(fh)
        self.assertEqual(t["roads_sha"], R.roads_sha(roads))
        self.assertEqual(t["roads_seed"], rec["commit_reveal"]["roads_seed"])

    def test_the_hash_lines_once_set(self):
        """The integrity review: a malformed hash line could never be corrected after the roads commit, so
        the roads commit's own test run checks the form of both before the push."""
        g, j = R.COMMITMENT_G, R.COMMITMENT_J
        self.assertEqual(g is None, j is None, "both hash lines are set in one commit, or neither")
        if g is not None:
            for v in (g, j):
                self.assertRegex(v, r"^[0-9a-f]{64}$")
            self.assertNotEqual(g, j)


if __name__ == "__main__":
    unittest.main(verbosity=2)
