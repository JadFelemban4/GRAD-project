"""test_roads_ceiling.py -- roads_ceiling.py: the control, the lever windows, the points, the charge
wrapper, tau, and the probe's value on one family, rebuilt with this module's own code.

    python -B test_roads_ceiling.py        about eight minutes at 4 jobs (ROADS_TEST_JOBS): 17 tests in
                                            503 s on this laptop, 30 October 2026, with 8 other runs beside
                                            them; exit code 0 when all pass

Section I of results/VALIDATION_DECISIONS.md, rows 100-103, and docs/build_step_2/ORDER_TO_TRAINING.md
step 4. No EPA table, logs/epa file, validation record or contract file is opened: every class runs
inside test_epa_fixtures.forbid_real_data, and roads_ceiling's own worker processes refuse the first
three (roads_ceiling._forbidden). Every road here is hand-made or SYNTHETIC; none is drawn from a
roads_seed, and nothing is written to results/.

  Control     the B58's locked climb, neutral and current-grade, give results/premise.json's 848.052
              (damage_base 848.885) and 449.625 to the printed digit (row 103, "To implement")
  Windows     (a)'s window is the H s before each onset, clipped to the previous climb's full-grade
              end, or to 20 s for the first; (b) is each whole gap; (a_b) runs from 50 s after each
              ramp down starts (150 s on the lead-in); a flat slot opens no window and ends none; the
              lambda variant commands -1 (= -0.15) inside its windows and current-grade's action
              outside. Control: a window one second wider is seen
  Points      the mean, pooled, median and evaluate.py forms on a hand-computed three-road case, and
              passes_T against T = MEI / 4 at r = 1.5. Controls: a road one unit off moves the mean,
              and a set at T - 1e-9 fails
  Charge      charge_shifted moves plant.charge_temperature by exactly +-6.3 K at every input (the
              block's None included) and no other value of the plant; in the environment the charge
              of the first step moves by exactly the offset and the damage of a 240 s climb moves
              (mistake 12: the perturbation reaches the number)
  Tau         tau_s of the three EPA engines equals complete.json's e6_row4.frozen.tau_s exactly, the
              B58's is the probe's 47.3351 s (c5tau.txt, to its four decimals), and E6 row 4's taus at
              the frozen cell equal complete.json's row-4 taus exactly
  Probe       the probe's closed-loop (a) at H 130 s on the Ford, family L67_g12_G100_v130 (its
              table.json, unrounded; table_full.csv prints it as 3.2319 points, base 145.365,
              current-grade's cut 9.375), rebuilt with family_road and run by run_set: equal to
              1e-9 (points and units)
  Guard       the forbidden paths are refused (any .csv, a long path and an exported tree among
              them) and the allowed ones are not; a recorded tau is read and never recomputed; the
              usable window under its two conventions, by hand; a seed of 2**32 or more is not a
              SYNTHETIC seed; write_record refuses the roads module's record names; the interface's
              names and signatures
"""
import dataclasses
import inspect
import json
import math
import os
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import check_premise as CP  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import evaluate as V  # noqa: E402
import plant as plant_model  # noqa: E402
import roads_ceiling as R  # noqa: E402
from test_epa_fixtures import Guarded  # noqa: E402  (WP3_INTERFACES.md 9.1)

JOBS = int(os.environ.get("ROADS_TEST_JOBS", "4"))
PROBE_TABLE = os.path.join(HERE, "results", "EPA_ROADS", "probe_2026-10-30", "table.json")


def _road(climbs, *, lead, duration, k):
    s, w = V.EPISODES[k]
    return R.family_road(k=k, episode_seed=s, weights=w, lead_s=lead, climbs=climbs, v_kmh=130.0,
                         duration_s=duration, dt=1.0, t_amb_k=315.0, slot_start=0, label="test (hand-made)")


class Control(Guarded):
    def test_the_locked_climb_gives_the_premise_back(self):
        with open(R.PREMISE, encoding="utf-8") as fh:
            prem = json.load(fh)
        specs = [R._locked_spec(policy=("neutral",), egt_windows=(), detail="light"),
                 R._locked_spec(policy=("cg",), egt_windows=(), detail="light")]
        neu, cg = R.execute(specs, jobs=JOBS)
        self.assertEqual(round(neu["D_knock"], 3), 848.052)
        self.assertEqual(round(neu["base_knock"], 3), 848.885)
        self.assertEqual(round(cg["D_knock"], 3), 449.625)
        self.assertEqual(round(neu["D_knock"], 3), round(prem[R.PREMISE_NEUTRAL]["damage"], 3))
        self.assertEqual(round(cg["D_knock"], 3), round(prem[R.PREMISE_CG]["damage"], 3))
        # the parallel baseline does not depend on the agent's policy
        self.assertEqual(neu["base_knock"], cg["base_knock"])
        self.assertEqual(neu["base_noknock"], cg["base_noknock"])


class Windows(Guarded):
    def setUp(self):
        super().setUp()
        # onsets 150 (L 70, gap 60) and 280 (L 70, gap 100) and 450 (L 67)
        self.road = _road([(70, 0.11, 60), (70, 0.12, 100), (67, 0.10, 100)], lead=150, duration=900, k=0)

    def test_a_is_the_H_seconds_before_each_onset_clipped_to_the_last_full_grade(self):
        self.assertEqual(R.windows_a(self.road, H=30.0), ((120.0, 150.0), (250.0, 280.0), (420.0, 450.0)))
        self.assertEqual(R.windows_a(self.road, H=100.0), ((50.0, 150.0), (220.0, 280.0), (350.0, 450.0)))
        # control: H one second longer moves a window that is not clipped
        self.assertNotEqual(R.windows_a(self.road, H=31.0), R.windows_a(self.road, H=30.0))

    def test_the_first_window_starts_no_earlier_than_20_s(self):
        road = _road([(70, 0.11, 60)], lead=40, duration=300, k=1)
        self.assertEqual(R.windows_a(road, H=100.0), ((20.0, 40.0),))
        self.assertEqual(R.windows_b(road), ((20.0, 40.0),))

    def test_b_is_each_whole_gap_and_ab_starts_50_s_after_each_ramp_down(self):
        self.assertEqual(R.windows_b(self.road), ((20.0, 150.0), (220.0, 280.0), (350.0, 450.0)))
        self.assertEqual(R.windows_ab(self.road), ((270.0, 280.0), (400.0, 450.0)))
        # the lead-in of 150 s opens no (a_b) window; a longer one does, from 150 s
        road = _road([(70, 0.11, 60)], lead=200, duration=400, k=2)
        self.assertEqual(R.windows_ab(road), ((150.0, 200.0),))

    def test_a_flat_slot_opens_no_window_and_ends_none(self):
        flat = json.loads(json.dumps(self.road))
        flat["climbs"][1]["grade"] = 0.0          # row 101: a slot made flat road keeps its index
        self.assertEqual(R.windows_a(flat, H=300.0), ((20.0, 150.0), (220.0, 450.0)))
        self.assertEqual([c[0] for c in R.climbs_of(flat)], [150.0, 450.0])

    def test_the_lambda_variant_acts_only_inside_its_windows(self):
        plant = engines.get("b58")
        cyc = R.env_cycle(self.road, dt=1.0)
        env = E.SupervisoryTunerEnv(cyc, plant=plant, dt=1.0, seed=1000, use_preview=True)
        obs, _ = env.reset(seed=1000)
        pol = R.make_policy(("lam", R.windows_a(self.road, H=30.0)))
        for k, inside in ((119, False), (120, True), (149, True), (150, False), (250, True)):
            env.k = k
            a, ref = pol(env, obs), CP.p_grade_now(env, obs)
            if inside:
                self.assertEqual(float(a[R.LAM_INDEX]), -1.0)
                self.assertEqual(float(env._rescale(a)[R.LAM_INDEX]), float(E.ACT_LO[1]))
                np.testing.assert_array_equal(np.delete(a, R.LAM_INDEX), np.delete(ref, R.LAM_INDEX))
            else:
                np.testing.assert_array_equal(a, ref)


class Points(Guarded):
    def test_the_four_forms_on_a_hand_computed_case(self):
        ref, var, base, neu = [10.0, 20.0, 30.0], [9.0, 18.0, 24.0], [100.0, 50.0, 200.0], [90.0, 40.0, 150.0]
        a = R.aggregate(ref, var, base, neutral=neu)
        pts = [1.0, 4.0, 3.0]                       # 100 (10-9)/100, 100 (20-18)/50, 100 (30-24)/200
        self.assertEqual(a["per_road"], pts)
        self.assertAlmostEqual(a["mean"], 8.0 / 3.0, places=12)
        self.assertAlmostEqual(a["pooled"], 100.0 * 9.0 / 350.0, places=12)
        self.assertEqual(a["median"], 3.0)
        self.assertAlmostEqual(a["evaluate_form"], 100.0 * (20.0 - 18.0) / 90.0, places=12)
        b = R.aggregate(ref, [9.0, 18.0, 25.0], base, neutral=None)
        self.assertNotEqual(b["mean"], a["mean"])  # control: one road's damage one unit off is seen
        self.assertIsNone(b["evaluate_form"])

    def test_passes_T_reads_r_1_5_against_MEI_over_4(self):
        def res(c):
            return dict(per_engine={e: dict(by={"1.5": dict(a=dict(noknock=dict(mean=v)))})
                                    for e, v in c.items()})
        self.assertEqual(R.T_POINTS, 5.43 / 4)
        ok, c = R.passes_T(res({"b58": 3.0, "ford_27tt": R.T_POINTS}), engines=("b58", "ford_27tt"))
        self.assertTrue(ok)
        self.assertEqual(c, {"b58": 3.0, "ford_27tt": R.T_POINTS})
        ok, _ = R.passes_T(res({"b58": 3.0, "ford_27tt": R.T_POINTS - 1e-9}), engines=("b58", "ford_27tt"))
        self.assertFalse(ok)                       # control: just under T fails
        ok, _ = R.passes_T(res({"b58": 3.0, "ford_27tt": 0.0}), engines=("b58",))
        self.assertTrue(ok)                        # an engine out of the test does not gate (row 95 (2))


class Charge(Guarded):
    def test_the_charge_moves_by_exactly_the_offset_at_every_input(self):
        for name in R.ENGINES:
            p = engines.get(name)
            for off in (R.CHARGE_OFFSET_K, -R.CHARGE_OFFSET_K):
                q = R.charge_shifted(p, offset_k=off)
                for t_amb in (288.15, 315.0, 323.15):
                    for t_block in (None, 330.0, 363.0, 371.4):
                        a = plant_model.charge_temperature(t_amb, t_block, engine=p.engine)
                        b = plant_model.charge_temperature(t_amb, t_block, engine=q.engine)
                        self.assertAlmostEqual(b - a, off, delta=1e-9)
            with self.assertRaises(TypeError):
                R.charge_shifted(p, offset_k=np.float64(6.3))

    def test_nothing_else_of_the_plant_moves(self):
        def flat(x, pre=""):
            if dataclasses.is_dataclass(x):
                x = dataclasses.asdict(x)
            if isinstance(x, dict):
                out = {}
                for k, v in x.items():
                    out.update(flat(v, f"{pre}{k}."))
                return out
            return {pre[:-1]: x}
        for name in R.ENGINES:
            p = engines.get(name)
            a, b = flat(p), flat(R.charge_shifted(p, offset_k=R.CHARGE_OFFSET_K))
            self.assertEqual(set(a), set(b))
            diff = sorted(k for k in a if a[k] != b[k])
            self.assertEqual(diff, ["engine.charge.rise_k"])
            self.assertAlmostEqual(b["engine.charge.rise_k"] - a["engine.charge.rise_k"], R.CHARGE_OFFSET_K, delta=1e-12)
            self.assertNotEqual(engines.engine_sha(p), engines.engine_sha(R.charge_shifted(p, offset_k=R.CHARGE_OFFSET_K)))

    def test_in_the_environment_the_charge_moves_and_the_damage_moves(self):
        base = engines.get("mazda_25t")
        cyc = E.make_grade_climb(duration=240.0, dt=1.0, t_amb=315.0, grade=0.12, v_kmh=130.0)
        iat, dmg = {}, {}
        for off in (0.0, R.CHARGE_OFFSET_K, -R.CHARGE_OFFSET_K):
            p = base if off == 0.0 else R.charge_shifted(base, offset_k=off)
            env = E.SupervisoryTunerEnv(cyc, plant=p, dt=1.0, seed=1000, use_preview=True)
            obs, _ = env.reset(seed=1000)
            first = None
            while True:
                obs, _r, term, trunc, info = env.step(CP.p_grade_now(env, obs))
                if first is None:
                    first = env.iat_k
                if term or trunc:
                    break
            iat[off], dmg[off] = first, info["episode_summary"]["damage"]
        self.assertAlmostEqual(iat[R.CHARGE_OFFSET_K] - iat[0.0], R.CHARGE_OFFSET_K, delta=1e-9)
        self.assertAlmostEqual(iat[-R.CHARGE_OFFSET_K] - iat[0.0], -R.CHARGE_OFFSET_K, delta=1e-9)
        self.assertNotEqual(dmg[R.CHARGE_OFFSET_K], dmg[0.0])       # mistake 12: the number moves
        self.assertNotEqual(dmg[-R.CHARGE_OFFSET_K], dmg[0.0])


class Tau(Guarded):
    def test_tau_is_the_frozen_definition_on_all_four(self):
        taus = R.tau_table(list(R.ENGINES), variant=("frozen",), jobs=JOBS)
        for name in R.EPA_ENGINES:
            rec = R.frozen_tau_record(name)
            self.assertEqual(taus[name][0], rec["frozen"]["tau_s"])
        self.assertEqual(round(taus["b58"][0], 4), 47.3351)
        import epa_coefficients as EC
        for name in R.EPA_ENGINES:
            rec, cell = R.frozen_tau_record(name), taus[name][1]
            for f in R.ROW4_FIELDS:
                self.assertEqual(sorted(rec[f]), sorted(f"x{x:g}" for x in R.ROW4_FACTORS))
                for x in R.ROW4_FACTORS:
                    pp = R.plant_for(name, ("thermal", f, x))
                    tau = EC.housing(pp, cell["egt"], cell["mdot"], t_amb_c=EC.T_AMB_C)["tau_s"]
                    self.assertEqual(tau, rec[f][f"x{x:g}"]["tau_s"])


class Probe(Guarded):
    def test_the_probes_closed_loop_value_on_one_family(self):
        # the probe's table.json (unrounded; its table_full.csv prints the same row as 3.2319 points, base
        # 145.365, cut 9.375): read as JSON, since this module's guard refuses every .csv
        with open(PROBE_TABLE, encoding="utf-8") as fh:
            row = next(r for r in json.load(fh) if r["fid"] == "L67_g12_G100_v130" and r["engine"] == "ford_27tt")
        road = _road([(67, 0.12, 100)] * 4, lead=180, duration=808, k=0)   # the probe's lib.road: tail 60 s
        hz = {"ford_27tt": {"130": 130.0}}
        runs = R.run_set([road], engine_ids=["ford_27tt"], variant=("frozen",), horizons=hz, dt=1.0, jobs=JOBS,
                         policies=("a",))
        per = R.summarise_set([road], runs, engine_ids=["ford_27tt"], variant=("frozen",), horizons=hz, dt=1.0,
                              readings=R.READINGS, variants=("cg", "a"), egt_drop_k=None)["ford_27tt"]
        pts = per["by"]["130"]["a"]["noknock"]["mean"]
        base = per["per_road"][0]["D_base"]["noknock"]
        cut = per["per_road"][0]["cg_cut"]["noknock"]
        self.assertLessEqual(abs(pts - row["closed"]["a130"]["noknock"]), 1e-9)
        self.assertLessEqual(abs(base - row["base"]["noknock"]), 1e-9)
        self.assertLessEqual(abs(cut - row["cg_cut"]["noknock"]), 1e-9)
        self.assertEqual(round(row["closed"]["a130"]["noknock"], 4), 3.2319)


class Guard(Guarded):
    def test_the_forbidden_paths(self):
        export = os.path.join(os.path.dirname(HERE), "an_export", "results", "EPA_VALIDATION", "summary.json")
        for p in ("logs/epa/MANIFEST.csv", os.path.join(HERE, "logs", "epa", "x"),
                  "data/engines/ford_27tt/epa_channels.csv", "results/EPA_VALIDATION/mazda_25t/run.json",
                  "\\\\?\\" + os.path.join(HERE, "results", "EPA_VALIDATION", "summary.json"), export,
                  os.path.join(os.path.dirname(HERE), "anywhere.csv"),
                  os.path.join(HERE, "results", "EPA_ROADS", "probe_2026-10-30", "table_full.csv")):
            self.assertTrue(R._forbidden(p), p)
        for p in ("results/premise.json", "data/engines/ford_27tt/derived_params.json",
                  "results/EPA_CALIBRATION/ford_27tt/complete.json", "results/EPA_ROADS/control.json", PROBE_TABLE):
            self.assertFalse(R._forbidden(p), p)

    def test_a_recorded_tau_is_read_never_recomputed(self):
        saved = dict(R._TAUS)
        try:
            R._TAUS.pop(("ford_27tt", ("frozen",)), None)
            R.use_recorded_taus({"ford_27tt": (66.5, {"egt": 1.0})})
            self.assertEqual(R.tau_s("ford_27tt"), 66.5)        # read, not run (a run gives 66.762)
            self.assertEqual(R.tau_table(["ford_27tt"], variant=("frozen",), jobs=1)["ford_27tt"][0], 66.5)
            with self.assertRaises(ValueError):                  # a different value is refused
                R.use_recorded_taus({"ford_27tt": (66.6, None)})
        finally:
            R._TAUS.clear()
            R._TAUS.update(saved)

    def test_the_usable_window_under_both_conventions(self):
        # onsets 150 (L 70), 280 (L 70), 450 (L 67): gaps from the full-grade ends 150 - 20, 280 - 220, 450 - 350
        road = _road([(70, 0.11, 60), (70, 0.12, 100), (67, 0.10, 100)], lead=150, duration=900, k=0)
        u = R._usable([road], {"b58": 50.0}, (1.5,))["b58"]["by_r"]["1.5"]
        self.assertEqual(u["every_window"]["n"], 3)
        self.assertEqual(u["gaps_only"]["n"], 2)
        self.assertAlmostEqual(u["gaps_only"]["usable_over_tau_mean"], (60 / 50 + 75 / 50) / 2, places=12)
        self.assertAlmostEqual(u["every_window"]["usable_over_tau_mean"], (75 / 50 + 60 / 50 + 75 / 50) / 3,
                               places=12)
        self.assertEqual(u["gaps_only"]["P_G_below_H"], 0.5)          # 60 < 75; 100 is not
        self.assertAlmostEqual(u["every_window"]["P_G_below_H"], 1 / 3, places=12)

    def test_synthetic_seeds_and_records(self):
        with self.assertRaises(ValueError):
            R.synthetic_roads(2 ** 32, n_roads=1, duration_s=900.0)
        roads = R.synthetic_roads(7, n_roads=2, duration_s=900.0)
        self.assertTrue(all(r["label"].startswith(R.SYNTHETIC) for r in roads))
        self.assertEqual(roads, R.synthetic_roads(7, n_roads=2, duration_s=900.0))
        slots = [c["slot"] for r in roads for c in r["climbs"]]
        self.assertEqual(slots, list(range(len(slots))))
        for r in roads:
            for c in r["climbs"]:
                self.assertTrue(67 <= c["L_s"] <= 85 and 0.10 <= c["grade"] < 0.12)
                self.assertLessEqual(c["onset_s"] + c["L_s"] + R.RAMP_S, 900.0 - 60.0)
        for name in ("roads", "redraws", "attempts"):
            with self.assertRaises(ValueError):
                R.write_record(name, {}, "", out_dir=os.path.join(HERE, "results", "EPA_ROADS"))

    def test_the_interface(self):
        self.assertEqual(R.ENGINES, ("b58", "mazda_25t", "honda_l15b7", "ford_27tt"))
        self.assertEqual((R.MEI, R.T_POINTS, R.RATIOS), (5.43, 5.43 / 4, (0.5, 1.5)))
        sig = {n: set(inspect.signature(getattr(R, n)).parameters) for n in
               ("ceilings", "passes_T", "slot_candidate_ceilings", "report", "control", "sweep", "timing", "tau_s")}
        self.assertEqual(sig["ceilings"], {"roads", "engines", "ratios", "dt", "jobs", "variants", "readings"})
        self.assertEqual(sig["passes_T"], {"ceiling_result", "engines"})
        self.assertEqual(sig["slot_candidate_ceilings"], {"roads", "slot", "candidate_road", "engines", "dt", "jobs"})
        self.assertEqual(sig["report"], {"roads", "engines", "dt", "jobs"})
        self.assertEqual(sig["control"], {"jobs"})
        self.assertEqual(sig["tau_s"], {"engine_id"})

    def test_a_road_without_its_ambient_keys_is_refused(self):
        road = _road([(70, 0.11, 60)], lead=150, duration=400, k=0)
        del road["cycle"]["humidity"]
        with self.assertRaises(KeyError):
            R.env_cycle(road, dt=1.0)
        road = _road([(70, 0.11, 60)], lead=150, duration=400, k=0)
        road["cycle"]["grade"][200] += 0.01          # not the family's ramps: no rebuild at 0.5 s
        R.env_cycle(road, dt=1.0)
        with self.assertRaises(ValueError):
            R.env_cycle(road, dt=0.5)


if __name__ == "__main__":
    unittest.main()
