"""test_epa_fit.py -- epa_fit's fitting procedure on SYNTHETIC rows made by the plant at
known truths (docs/build_step_2/WP3_INTERFACES.md section 9.5; PLAN.md section 5 as
amendments C1 and D1-D14 amend it; HANDOFFS.md WP3 items 1, 3 and 5).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python -B test_epa_fit.py

WRITTEN 23 October 2026 (build step 2, WP3), before any fit. NO EPA ROW IS READ HERE:
every row is made below from the plant (engines.build_candidate of the Mazda's specs
with synthetic constants, the B58's typed values moved by declared factors) at
synthetic operating points; the view is a synthetic calibration view, its R values
synthetic numbers of the contract's units; no table, contract or D3 file is opened.
The engine is mazda_25t only because its specs build a candidate: its typed
geometry, fuel and lambda floor are read from engine_specs/ (typed values, no EPA
row). Each test proves its point with a control that must fail (mistake 12).

THE CRANK STEP. The rows are made and fitted at DTH = 1.0 deg (plant.run_cycle at any
step is the same plant; four times faster than 0.25), so that a truth is exactly
representable; Tolerances measures the roughness at the production 0.25.
"""
import dataclasses
import json
import math
import os
import sys
import unittest
from unittest import mock
from dataclasses import replace

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np                      # noqa: E402

import engine_env                       # noqa: E402
import engines                          # noqa: E402
import epa_fit                          # noqa: E402
import epa_rows                         # noqa: E402
import epa_stats                        # noqa: E402
import plant                            # noqa: E402
import test_epa_fixtures as fx          # noqa: E402  the real-data guard (WP3_INTERFACES.md 9.1)

NAME = "mazda_25t"
DTH = 1.0
JOBS = 6
TABLE_S, TABLE_F = "syn_steady.csv", "syn_final.csv"     # synthetic names: no EPA table is named
LINES = ("1500", "2000", "2500", "2750", "3000", "3500", "4000", "4500")
HELD = ("2750",)
STEADY_MAP = (35.0, 50.0, 65.0, 80.0, 95.0, 110.0, 125.0, 140.0)
FINAL_MAP = (150.0, 175.0, 200.0, 225.0)
GATE = 140.0                            # the truth's enrichment gate: between the steady and the Final rows
CAM_TRUTH = (-20.0, 4.0, 6.0, -0.5, 1.2, -1.5)   # a synthetic cam schedule, CAD (form D's tests)


def _spec(section, field):
    return engines.read_spec(NAME)[section][field]


def truth_values(*, form="A", **cycle_moves):
    """A synthetic truth, shaped like the derived file: the B58's typed cycle constants
    moved by declared factors, a declared ECU (the B58's typed knock surface), a flat
    envelope (S3c recovers whatever the rows give)."""
    b = engines.typed_engine("b58").cycle
    cyc = {k: float(getattr(b, k)) for k in epa_fit.CYCLE_FIELDS if k != "form"}
    cyc.update(form=form, burn_base=b.burn_base * 1.1, burn_rpm=b.burn_rpm * 1.1, delay_base=b.delay_base * 0.92,
               delay_rpm=b.delay_rpm * 0.92, fmep_0=b.fmep_0 * 1.1, fmep_pmax=b.fmep_pmax * 1.1,
               fmep_sp=b.fmep_sp * 1.1, fmep_sp2=b.fmep_sp2 * 1.1, ua_port=b.ua_port * 2.0, ve_base=0.84,
               ve_amp=0.16, ve_rpm=3000.0, ve_width=2800.0, exh_bp_ratio=1.3, exh_bp_min_kpa=104.0,
               knock_a=b.knock_a * 1.2, ve_map=0.0, ve_cam=0.0, ce_rich_slope=float(engines.SHARED_RICH_SLOPE))
    cyc.update({k: float(v) if k != "form" else v for k, v in cycle_moves.items()})
    kl = engines.read_spec("b58")["ecu"]
    ecu = {k: 0.0 for k in epa_fit.ECU_FIELDS}
    ecu.update(spark_a=14.0, spark_b=0.003, spark_c=0.09, spark_min=-40.0, spark_max=60.0,
               kl_a=float(kl["kl_a"]), kl_b=float(kl["kl_b"]), kl_c=float(kl["kl_c"]), kl_d=float(kl["kl_d"]),
               enr_load=GATE, enr_rpm_lo=2500.0, enr_rpm_hi=4000.0, enr_depth=0.12, cam_on=0)
    if "D" in form.split("+"):
        ecu.update(dict(zip(engines.CAM_SCHEDULE[:6], CAM_TRUTH)), cam_on=1, cam_rpm_lo=1504.0, cam_rpm_hi=4504.0,
                   cam_map_lo=35.0, cam_map_hi=225.0, cam_lo=-40.0, cam_hi=40.0)
    return {"cycle": cyc, "ecu": ecu,
            "boost_ceiling": {"envelope_flow": [0.0, 1.0], "envelope_pr": [1.0, 1.0], "pr_cap": 1.0}}


def synthetic_view(*, R=None, lam_floor=None):
    """A calibration view of synthetic numbers (epa_rows.CalibrationView's fields): the
    synthetic lines, one fuel for both synthetic tables (the Mazda's typed fuel), the
    spec's lambda floor (the fit checks the two agree), and R in the contract's units."""
    fuel = epa_rows.TableFuel(ftag="synthetic", fuel_report="synthetic",
                              lhv_j_per_kg=float(_spec("fuel", "lhv_j_per_kg")), afr_st=float(_spec("fuel", "afr_st")))
    R = R or {"E1a": (2.0, "% of the measured torque"), "E2a": (4.0, "% of the measured fuel flow"),
              "E3a": (10.0, "K"), "E4a": (10.0, "K"), "E4b": (15.0, "%"), "D1": (15.0, "%"),
              "L0": (10.0, "K"), "L1": (10.0, "K"), "E8": (15.0, "%")}
    return epa_rows.CalibrationView(
        engine=NAME, contract_commit="synthetic", contract_sha_text="synthetic", lines=LINES, held_out_lines=HELD,
        table_counts=(), lambda_ref={TABLE_S: 1.0, TABLE_F: 1.0}, hot_map_floor_kpa=FINAL_MAP[0],
        fuel_by_table={TABLE_S: fuel, TABLE_F: fuel},
        lam_floor=float(_spec("ecu", "lam_floor")) if lam_floor is None else lam_floor,
        coverage_calibration_fired={}, coverage_calibration_hot={}, conventions={}, model_form={}, R=R,
        mei_points=1.0, r1_housing_k=1.0, b_points=1.0, propagation_b58={"G_gas_over_42C_k": 3.0},
        ecu_strategy_b58={"k3_pair_change_vs_lambda": [[-0.1, -10.0], [0.0, 0.0], [0.1, 10.0]],
                          "k3_pair_change_vs_spark": [[-2.0, -5.0], [0.0, 0.0], [2.0, 5.0]], "worth_b": None},
        perturbations_e6=(), e8_min_rows=3, k3_seconds=413)


def _row(cls, **f):
    base = dict(engine=NAME, test_cell="synthetic", fuel_report="synthetic", origin="fixture", oil_k=362.0,
                spark_sentinel=False, lam_banks=None, lambda_missing=False, lam_ref=1.0, meter_missing=False,
                baro_kpa=99.6, cell_temp_k=298.0, cam_cad=None, cam_channel=None, cam_missing=True,
                exhaust_cam_cad=None, valve_overlap_cad=None, atkinson_ratio=None, eff_compression_stroke_mm=None,
                eff_expansion_stroke_mm=None, eff_compression_ratio=None, eff_expansion_ratio=None)
    base.update(f)
    return cls(**base)


def _pops(map_kpa, bmep, meter, lam, kind):
    """The loader's own populations (epa_rows.populations: split.classify on the row's
    strings; mistake 10) for a synthetic row."""
    cells = {"intake_manifold_press_kpa_abs": repr(float(map_kpa)), "bmep_bar": repr(float(bmep)),
             "fuel_meter_flow_gps": "" if meter is None else repr(float(meter)),
             "exhaust_lambda": "" if lam is None else repr(float(lam))}
    return epa_rows.populations(cells, 1.0, FINAL_MAP[0], kind)


def make_rows(values, *, view, cam=False, steady_map=STEADY_MAP, final_map=FINAL_MAP, lines=None,
              final_lines=None, lam_override=None):
    """Synthetic calibration rows made by the plant at `values` (the truth): inputs on
    the synthetic lines and MAPs; spark and lambda from the truth's ECU (one step at
    dwell 30 s); torque, TIT, the fuel and the meter from plant.run_cycle at the inputs
    the model is fed (epa_stats.row_inputs: the snap included); TIP from the truth's
    back-pressure law; BMEP from the torque; the populations the loader's own."""
    tp = epa_fit.candidate(NAME, values)
    model = epa_fit.RowModel(tp, fuels=view.fuel_by_table)
    e = tp.engine
    lines = lines or [l for l in LINES if l not in HELD]
    final_lines = final_lines if final_lines is not None else [l for l in lines if int(l) >= 2000]
    out, sr = [], {TABLE_S: 6, TABLE_F: 6}
    specs = [(TABLE_S, l, m) for l in lines for m in steady_map] + [(TABLE_F, l, m) for l in final_lines
                                                                      for m in final_map]
    for table, line, mp in specs:
        final = table == TABLE_F
        rpm = float(line) + 4.0
        imt = 320.0 if final else 308.0
        spark, lam, _fan = engine_env.BaselineECU(e.ecu).step(rpm, mp, imt, 360.0, False, 30.0)
        if lam_override is not None and final:
            lam = lam_override(rpm, mp, lam)
        cam_cad = None
        if cam:
            x, y = rpm / 1000.0, mp / 100.0
            c = CAM_TRUTH
            cam_cad = c[0] + c[1] * x + c[2] * y + c[3] * x * x + c[4] * x * y + c[5] * y * y
        cls = epa_rows.FinalRow if final else epa_rows.SteadyRow
        n = sr[table]
        sr[table] += 1
        stub = _row(cls, table=table, source_row=n, line=line, nominal_rpm=int(line), hold=n if final else None,
                    speed_rpm=rpm, map_kpa=mp, imt_k=imt, ect_k=360.0, spark_btdc=float(spark), lam_meas=float(lam),
                    torque_nm=0.0, bmep_bar=0.0, fuel_meter_gps=0.0, injector_fuel_gps=0.0, tit_c=0.0, tip_kpa=0.0,
                    cam_cad=cam_cad, cam_channel="intake_cam_phase_cad_ret" if cam else None, cam_missing=not cam,
                    pops=_pops(mp, 5.0, 1.0, lam, "final" if final else "steady"))
        x = epa_stats.row_inputs(stub, fuel=epa_stats.fuel_of(stub, view=view, conventions=epa_stats.NOMINAL),
                                 conventions=epa_stats.NOMINAL, model=model)
        r = model.result(x, dtheta=DTH)
        bmep = r.torque_nm * 4.0 * math.pi / e.geometry.vd_total / 1e5
        out.append(replace(stub, torque_nm=r.torque_nm, bmep_bar=float(bmep), fuel_meter_gps=r.mdot_fuel_gps,
                           injector_fuel_gps=r.mdot_fuel_gps, tit_c=r.egt_c,
                           tip_kpa=float(plant.exhaust_backpressure_kpa(mp, engine=e)),
                           pops=_pops(mp, bmep, r.mdot_fuel_gps, lam, "final" if final else "steady")))
    return tuple(out)


_CACHE = {}


def dataset(key="A", **kw):
    """The synthetic rows of one truth, made once per process."""
    if key not in _CACHE:
        view = synthetic_view()
        vals = truth_values(**kw)
        _CACHE[key] = (vals, view, make_rows(vals, view=view, cam=True))
    return _CACHE[key]


def tearDownModule():
    epa_fit.close_pools()


# ===========================================================================================
class Rows(fx.Guarded):
    def test_cal_rows_takes_steady_and_final_skips_initial_and_refuses_held_out(self):
        _v, _view, rows = dataset()
        self.assertEqual(epa_fit.cal_rows(rows), rows)
        ini = epa_rows.InitialRow(engine=NAME, table="syn_initial.csv", source_row=6, test_cell="synthetic",
                                  line="2000", nominal_rpm=2000, hold=6, speed_rpm=2004.0, torque_nm=100.0,
                                  origin="fixture", transient=True)
        self.assertEqual(epa_fit.cal_rows(rows + (ini,)), rows)
        # the control: the same fields as a held-out row are refused by type
        f = {fl.name: getattr(rows[0], fl.name) for fl in dataclasses.fields(rows[0])}
        held = epa_rows.HeldOutRow(**f, kind="steady")
        with self.assertRaises(TypeError):
            epa_fit.cal_rows(rows + (held,))
        with self.assertRaises(TypeError):
            epa_fit.cal_rows((held,))

    def test_the_synthetic_populations_are_the_loaders(self):
        _v, _view, rows = dataset()
        fl1 = [r for r in rows if r.pops.fired_l1]
        enr = [r for r in rows if r.pops.hot_enr]
        self.assertGreater(len(fl1), 20)
        self.assertGreaterEqual(len(enr), 9)
        self.assertTrue(all(epa_fit._final(r) for r in enr))


# ===========================================================================================
class S1(fx.Guarded):
    def test_recovers_the_ratio_and_floor(self):
        v, view, rows = dataset()
        st = epa_fit.s1_backpressure(rows, view=view)
        self.assertAlmostEqual(st.values["exh_bp_ratio"], 1.3, places=12)
        self.assertAlmostEqual(st.values["exh_bp_min_kpa"], 104.0, places=9)
        self.assertNotIn("S1_hinge_column_zero", st.flags)
        self.assertEqual(st.report["sigma"]["ratio"] < 1e-9, True)
        # the control: TIP moved by 5 kPa on every row moves the fit
        moved = tuple(replace(r, tip_kpa=r.tip_kpa + 5.0) for r in rows)
        st2 = epa_fit.s1_backpressure(moved, view=view)
        self.assertNotAlmostEqual(st2.values["exh_bp_min_kpa"], 104.0, places=3)

    def test_no_row_below_the_hinge_is_reported_never_asserted(self):
        v, view, rows = dataset()
        high = tuple(r for r in rows if r.map_kpa >= 110.0)
        st = epa_fit.s1_backpressure(high, view=view)
        self.assertIn("S1_hinge_column_zero", st.flags)       # amendment D10: a declared outcome
        self.assertIsNone(st.report["sigma"]["floor_kpa"])
        st_all = epa_fit.s1_backpressure(rows, view=view)       # the control: rows below it
        self.assertNotIn("S1_hinge_column_zero", st_all.flags)


# ===========================================================================================
class S3a(fx.Guarded):
    def setUp(self):
        self.v, self.view, self.rows = dataset()
        self.base = epa_fit._base_plant(NAME, "A")

    def test_recovers_the_spark_and_holds_base_plus_comp_unclipped(self):
        st = epa_fit.s3a_spark(self.rows, plant=self.base, view=self.view)
        for k in ("spark_a", "spark_b", "spark_c", "kl_a", "kl_b", "kl_c", "kl_d"):
            self.assertAlmostEqual(st.values[k] / self.v["ecu"][k], 1.0, places=8, msg=k)
        self.assertTrue(st.report["converged"])
        self.assertTrue(st.report["unclipped_at_every_row"])
        hot = [r for r in self.rows if r.imt_k - 273.15 >= 37.5 and r.pops.fired]
        self.assertTrue(hot)
        # the control (amendment D3): the plan's rule, floor(min target) - 1, clips at a
        # row whose IAT compensation pulls the spark below it
        cal = replace(self.base.engine.ecu, **st.values)
        e2 = engine_env.BaselineECU(cal)
        targets = [r.spark_btdc - e2.iat_compensation(r.imt_k) for r in self.rows if r.pops.fired]
        plan_min = float(math.floor(min(targets)) - 1)
        bad = engine_env.BaselineECU(replace(cal, spark_min=plan_min))
        clipped = 0
        for r in self.rows:
            if not r.pops.fired:
                continue
            out = bad.step(r.speed_rpm, r.map_kpa, r.imt_k, r.ect_k, False, 30.0)[0]
            if out != e2.step(r.speed_rpm, r.map_kpa, r.imt_k, r.ect_k, False, 30.0)[0]:
                clipped += 1
        self.assertGreater(clipped, 0)

    def test_the_empty_piece_rule(self):
        st = epa_fit.s3a_spark(self.rows, plant=self.base, view=self.view)
        self.assertNotIn("S3a_empty_piece", st.flags)
        n0 = sum(1 for r in self.rows if r.pops.fired and r.map_kpa < FINAL_MAP[0])
        n1 = st.report["pieces"]["part_load"]["n"]
        self.assertLess(n1, n0, "the synthetic spark must move rows off the plane after the start")
        saved = dict(epa_fit.S3A_MIN_ROWS)
        try:
            # amendment D7: a minimum the first reassignment cannot meet stops the
            # iteration at the last valid assignment (the start), flagged
            epa_fit.S3A_MIN_ROWS["part_load"] = n0
            st2 = epa_fit.s3a_spark(self.rows, plant=self.base, view=self.view)
            self.assertIn("S3a_empty_piece", st2.flags)
            self.assertEqual(st2.report["pieces"]["part_load"]["n"], n0)
            # the control: a start that leaves a piece short is a coding defect
            epa_fit.S3A_MIN_ROWS["part_load"] = n0 + 1
            with self.assertRaises(epa_fit.FitDefect):
                epa_fit.s3a_spark(self.rows, plant=self.base, view=self.view)
        finally:
            epa_fit.S3A_MIN_ROWS.clear()
            epa_fit.S3A_MIN_ROWS.update(saved)


# ===========================================================================================
class S3b(fx.Guarded):
    def setUp(self):
        self.v, self.view, self.rows = dataset()
        self.base = epa_fit._base_plant(NAME, "A")
        self.cens = epa_stats.censoring([r for r in self.rows if epa_fit._final(r)])

    def fit(self, rows):
        return epa_fit.s3b_lambda(rows, plant=self.base, view=self.view, censoring=self.cens,
                                  lam_floor=self.view.lam_floor, conventions=epa_stats.NOMINAL)

    def test_finds_a_gate_between_the_steady_and_final_rows_ties_to_the_highest(self):
        st = self.fit(self.rows)
        self.assertEqual(st.values["enr_rpm_lo"], 2500.0)
        self.assertEqual(st.values["enr_rpm_hi"], 4000.0)
        self.assertAlmostEqual(st.values["enr_depth"], 0.12, places=12)
        lo, hi = st.report["flat_gates_kpa"]
        self.assertEqual((lo, hi), (max(STEADY_MAP), FINAL_MAP[0] - 1.0))
        self.assertTrue(lo <= GATE <= hi)                        # the truth lies on the flat interval
        self.assertEqual(st.values["enr_load"], hi)              # amendment D2: the highest gate
        self.assertIn("S3b_flat_profile", st.flags)
        self.assertEqual(st.report["flat_width_kpa"], hi - lo)
        # the control: without the steady rows (D2 adds them) the flat interval runs to
        # the grid's lower edge, so a lowest-gate rule would put the gate at 100 kPa
        st2 = self.fit(tuple(r for r in self.rows if epa_fit._final(r)))
        self.assertEqual(st2.report["flat_gates_kpa"][0], epa_fit.S3B_GATE_DESIGN_KPA)

    def test_the_invariants_edge_is_the_largest_depth_engine_accepts(self):
        # HANDOFFS.md WP3 item 1: 1.0 - (1.0 - x) can land an ulp below x, so the edge
        # is searched in doubles: at it 1 - d >= lam_floor, one ulp above it not
        for floor in (0.7, 0.61, 0.6, 0.585, 0.812, 0.333, float(self.view.lam_floor)):
            d = epa_fit.depth_edges(self.rows, lam_floor=floor, conventions=epa_stats.NOMINAL)["invariant"]
            self.assertGreaterEqual(1.0 - d, floor, msg=floor)
            self.assertLess(1.0 - float(np.nextafter(d, 1.0)), floor, msg=floor)
        # the controls: the plain difference 1 - lam_floor is not the edge either way --
        # at 0.333 it breaks the invariant (1 - (1 - x) lands an ulp below x), at 0.7
        # the next double up still keeps it
        self.assertLess(1.0 - (1.0 - 0.333), 0.333)
        self.assertGreaterEqual(1.0 - float(np.nextafter(1.0 - 0.7, 1.0)), 0.7)

    def test_the_depths_upper_edge_is_the_invariants_when_lower(self):
        floor = self.view.lam_floor
        deep = 1.0 - (1.0 - floor) - 0.02                      # readings deeper than the floor allows
        rows = tuple(replace(r, lam_meas=1.0 - (1.0 - deep) * min(max((r.speed_rpm - 2500.0) / 1500.0, 0.0), 1.0))
                     if epa_fit._final(r) else r for r in self.rows)
        edges = epa_fit.depth_edges(rows, lam_floor=floor, conventions=epa_stats.NOMINAL)
        self.assertEqual(edges["active"], "invariant")
        self.assertLess(edges["invariant"], edges["c1"])
        st = self.fit(rows)
        self.assertEqual(st.values["enr_depth"], edges["invariant"])
        self.assertIn("enr_depth", st.bounds_active)
        self.assertEqual(st.report["depth_edge"]["active"], "invariant")
        vals = truth_values()
        vals["ecu"].update(st.values)
        epa_fit.candidate(NAME, vals)                          # builds: Engine's invariant holds
        # the control: C1's bound alone would build an engine engines.Engine refuses
        vals["ecu"]["enr_depth"] = edges["c1"]
        with self.assertRaises(ValueError):
            epa_fit.candidate(NAME, vals)
        # and in the ordinary case C1's bound is the lower and is the one reported
        self.assertEqual(epa_fit.depth_edges(self.rows, lam_floor=floor, conventions=epa_stats.NOMINAL)["active"], "C1")
        self.assertTrue(st.report["depth_edge"]["engine_invariant_checked"])
        # the control: an edge one step past the invariant's is refused AT THE STAGE,
        # by engines.Engine's own check, as a coding defect
        orig = epa_fit.depth_edges

        def past(rows_, *, lam_floor, conventions):
            d = orig(rows_, lam_floor=lam_floor, conventions=conventions)
            return dict(d, upper=float(np.nextafter(d["invariant"], 1.0)), active="C1")
        epa_fit.depth_edges = past
        try:
            with self.assertRaises(epa_fit.FitDefect):
                self.fit(rows)
        finally:
            epa_fit.depth_edges = orig


# ===========================================================================================
class S3c(fx.Guarded):
    def setUp(self):
        self.v, self.view, self.rows = dataset()
        self.base = epa_fit._base_plant(NAME, "A")

    def fit(self, rows, view=None):
        return epa_fit.s3c_envelope(rows, plant=self.base, view=view or self.view, conventions=epa_stats.NOMINAL)

    def test_a_line_without_holds_cannot_lower_the_ceiling(self):
        st = self.fit(self.rows)
        self.assertEqual(sorted(st.report["lines_without_holds"]), ["1500"])
        self.assertEqual(len(st.values["envelope_flow"]), 1 + 6)
        self.assertEqual(st.values["envelope_flow"][0], 0.0)
        self.assertEqual(st.values["envelope_pr"][0], 1.0)
        self.assertTrue(all(b > a for a, b in zip(st.values["envelope_flow"], st.values["envelope_flow"][1:])))
        # a calibration line with steady rows only, at a high load, gives no point
        extra = make_rows(self.v, view=self.view, steady_map=(130.0, 140.0), final_map=(), lines=["4500"],
                          final_lines=[])
        extra = tuple(replace(r, line="5000", nominal_rpm=5000, source_row=900 + i) for i, r in enumerate(extra))
        view2 = replace(self.view, lines=self.view.lines + ("5000",))
        st2 = self.fit(self.rows + extra, view=view2)
        self.assertEqual(st2.values, st.values)
        self.assertIn("5000", st2.report["lines_without_holds"])
        # the control: were that line's rows Final rows, it would give a point
        as_final = tuple(epa_rows.FinalRow(**{f.name: getattr(r, f.name) for f in dataclasses.fields(r)})
                         for r in extra)
        as_final = tuple(replace(r, hold=r.source_row) for r in as_final)
        st3 = self.fit(self.rows + as_final, view=view2)
        self.assertNotEqual(st3.values, st.values)

    def test_rows_without_a_cell_pressure_take_decision_53s_median_and_sweep(self):
        # the HD1's case: the Final rows publish no cell pressure or temperature, the
        # steady rows do (Cell 9's), each its own barometer
        baros = [98.0 + 0.1 * (i % 7) for i in range(len(self.rows))]
        rows = tuple(replace(r, baro_kpa=None, cell_temp_k=None) if epa_fit._final(r)
                     else replace(r, baro_kpa=b) for r, b in zip(self.rows, baros))
        have = [b for r, b in zip(self.rows, baros) if not epa_fit._final(r)]
        st = self.fit(rows)
        hd1 = st.report["hd1_barometer"]
        self.assertEqual(hd1["median"], float(np.median(have)))
        self.assertEqual(hd1["sweep"], [min(have), max(have)])
        self.assertEqual(hd1["from_rows"], len(have))
        lo, hi = hd1["envelope_at_sweep"]["lo"], hd1["envelope_at_sweep"]["hi"]
        self.assertEqual((lo["barometer_kpa"], hi["barometer_kpa"]), (min(have), max(have)))
        self.assertLess(hi["envelope_flow"][1], st.values["envelope_flow"][1])      # corrected flow ~ 1/p
        self.assertGreater(lo["envelope_flow"][1], st.values["envelope_flow"][1])
        self.assertEqual(st.values["envelope_pr"], lo["envelope_pr"])               # PR is MAP / inlet
        self.assertEqual(epa_fit.stage0_declarations(rows, view=self.view)["hd1_barometer"], epa_fit.HD1_BAROMETER)
        # the controls: every row its own cell pressure, no rule; no row with one, a
        # coding defect (no median to take), never a silent None
        self.assertIsNone(self.fit(self.rows).report["hd1_barometer"])
        self.assertIsNone(epa_fit.stage0_declarations(self.rows, view=self.view)["hd1_barometer"])
        with self.assertRaises(epa_fit.FitDefect):
            self.fit(tuple(replace(r, baro_kpa=None) for r in self.rows))

    def test_ties_are_refused(self):
        fl = [r for r in self.rows if epa_fit._final(r) and r.line == "3000" and r.map_kpa == FINAL_MAP[-1]][0]
        twin = replace(fl, line="1500", nominal_rpm=1500, source_row=999, hold=999)
        with self.assertRaises(ValueError):
            self.fit(self.rows + (twin,))


# ===========================================================================================
class S3d(fx.Guarded):
    def test_recovers_the_cam_schedule_and_flags_extrapolated_rows(self):
        v, view, rows = dataset("D", form="A+B+C+D")
        st = epa_fit.s3d_cam(rows, view=view)
        for k, c in zip(engines.CAM_SCHEDULE[:6], CAM_TRUTH):
            self.assertAlmostEqual(st.values[k], c, places=8, msg=k)
        self.assertEqual(st.values["cam_on"], 1)
        self.assertEqual([st.values["cam_rpm_lo"], st.values["cam_rpm_hi"]],
                         [min(r.speed_rpm for r in rows), max(r.speed_rpm for r in rows)])
        self.assertEqual(st.values["cam_lo"], min(r.cam_cad for r in rows))
        self.assertEqual(st.report["extrapolated_rows"], [])
        # the control: a calibration row outside the cam rows' domain is flagged
        out = replace(rows[0], speed_rpm=6000.0, cam_cad=None, cam_missing=True, source_row=777)
        st2 = epa_fit.s3d_cam(rows + (out,), view=view)
        self.assertIn(list(epa_fit._key(out)), st2.report["extrapolated_rows"])
        self.assertIn("S3d_extrapolated_rows", st2.flags)


# ===========================================================================================
_FITS = {}


def form_a_fit(key="A", **kw):
    """Form A fitted on a dataset, once per process (the stage tests below read it)."""
    if key not in _FITS:
        v, view, rows = dataset(key, **kw)
        _FITS[key] = epa_fit.fit_form(NAME, rows, view=view, form="A", start=None, jobs=JOBS, dtheta=DTH)
    return _FITS[key]


def form_c_fits():
    """Forms A, A+B and A+B+C fitted in turn on a rich-slope truth, once per process."""
    if "C-ladder" not in _FITS:
        v, view, rows = dataset("C0.9", form="A+B+C", ce_rich_slope=0.9)
        fa = epa_fit.fit_form(NAME, rows, view=view, form="A", start=None, jobs=JOBS, dtheta=DTH)
        fb = epa_fit.fit_form(NAME, rows, view=view, form="A+B", start=fa, jobs=JOBS, dtheta=DTH)
        fc = epa_fit.fit_form(NAME, rows, view=view, form="A+B+C", start=fb, jobs=JOBS, dtheta=DTH)
        _FITS["C-ladder"] = (fa, fb, fc)
    return _FITS["C-ladder"]


class _NoRidge:
    """RIDGE_W at 0 inside the block: a stage then minimises its data residuals alone,
    so a noise-free truth is its exact answer."""

    def __enter__(self):
        self.w = epa_fit.RIDGE_W
        epa_fit.RIDGE_W = 0.0

    def __exit__(self, *a):
        epa_fit.RIDGE_W = self.w


def _s2_cost(rows, view, form, theta):
    """S2's declared objective at `theta` (data and ridge), by S2's own residuals: the
    fit's cost must not exceed the truth's (the solver found the declared optimum)."""
    names = epa_fit.s2_names(form)
    use = [r for r in rows if r.pops.fired_meter and epa_fit._has_lam(r) and epa_fit._no_sentinel(r)]
    rpm = np.array([r.speed_rpm for r in use])
    mp = np.array([r.map_kpa for r in use])
    iat = np.array([r.imt_k for r in use])
    vals = truth_values(form=form)
    e = epa_fit.candidate(NAME, vals).engine
    air = np.array([epa_stats.air_cal(r, view=view, conventions=epa_stats.NOMINAL) for r in use])
    eta_t = air / epa_fit._air_at_unit_ve(e, rpm, mp, iat)
    ee = replace(e, cycle=replace(e.cycle, **{n: float(theta[n]) for n in names}))
    r = (np.log(epa_fit.plant_ve(rpm, mp, None, ee)) - np.log(eta_t)) / epa_fit._scales(view)["air"]
    c = epa_fit.ridge_centre()
    rr = [math.sqrt(epa_fit.RIDGE_W) * (theta[n] - c[n]) / epa_fit.SCALES[n] for n in names if n in epa_fit.SCALES]
    return 0.5 * float(np.dot(r, r) + np.dot(rr, rr))


class S2(fx.Guarded):
    def test_recovers_the_breathing_exactly_without_the_ridge(self):
        for key, kw, form in (("A", {}, "A"), ("B", {"form": "A+B", "ve_map": 2e-3}, "A+B")):
            v, view, rows = dataset(key, **kw)
            plant_s3 = epa_fit.candidate(NAME, v)
            with _NoRidge():
                st = epa_fit.s2_breathing(rows, plant=plant_s3, view=view, form=form, conventions=epa_stats.NOMINAL,
                                          dtheta=DTH, jobs=JOBS)
            for n in epa_fit.s2_names(form):
                self.assertAlmostEqual(st.values[n] / v["cycle"][n], 1.0, places=8, msg=(key, n))
            self.assertLessEqual(st.report["verify_max_rel"], epa_fit.S2_VERIFY_REL)

    def test_with_the_declared_ridge_the_fit_is_the_objectives_minimum(self):
        v, view, rows = dataset()
        st = form_a_fit().stages["S2"]
        truth = {n: v["cycle"][n] for n in epa_fit.s2_names("A")}
        self.assertLessEqual(_s2_cost(rows, view, "A", st.values), _s2_cost(rows, view, "A", truth))
        self.assertLessEqual(st.convergence.grad_norm, 1e-6)
        # the ridge's pull is reported, never hidden: every parameter labelled
        self.assertEqual(set(st.report["data_or_prior"]), set(epa_fit.s2_names("A")))

    def test_a_form_without_the_truths_term_cannot_fit_it(self):
        # the control: a ve_map truth fitted at form A leaves a residual the A+B fit removes
        v, view, rows = dataset("B", form="A+B", ve_map=2e-3)
        p = epa_fit.candidate(NAME, v)
        with _NoRidge():
            a = epa_fit.s2_breathing(rows, plant=replace(p, engine=replace(p.engine, cycle=replace(
                p.engine.cycle, form="A", ve_map=0.0))), view=view, form="A", conventions=epa_stats.NOMINAL,
                dtheta=DTH, jobs=JOBS)
            b = epa_fit.s2_breathing(rows, plant=p, view=view, form="A+B", conventions=epa_stats.NOMINAL,
                                     dtheta=DTH, jobs=JOBS)
        self.assertGreater(a.convergence.cost, 1e6 * max(b.convergence.cost, 1e-30))


class S4(fx.Guarded):
    def test_recovers_burn_friction_and_port_without_the_ridge(self):
        v, view, rows = dataset()
        fit = form_a_fit()
        with _NoRidge():
            st = epa_fit.s4_burn(epa_fit.cal_rows(rows), name=NAME, values=fit.values, view=view, form="A", jobs=JOBS,
                                 conventions=epa_stats.NOMINAL, dtheta=DTH,
                                 start={n: float(getattr(engines.typed_engine("b58").cycle, n))
                                        for n in epa_fit.S4_PARAMS})
        # what the rows determine, to the precision the cycle's roughness leaves (the
        # burn and delay terms are nearly collinear, amendment D6, and S4's xtol stops a
        # step inside that roughness): the burn and the delay bases at every line's
        # speed within 0.05 CAD, FMEP within 0.002 bar at every row's speed (at a peak
        # pressure of 60 bar), UA_PORT within 1e-4
        stroke = epa_fit.candidate(NAME, v).engine.geometry.stroke

        def fmep(q, rpm):
            sp = 2.0 * stroke * rpm / 60.0
            return q["fmep_0"] + q["fmep_pmax"] * 60.0 + q["fmep_sp"] * sp + q["fmep_sp2"] * sp ** 2

        def close(vals, truth):
            out = []
            for rpm in (float(l) + 4.0 for l in LINES):
                for a, b in (("burn_base", "burn_rpm"), ("delay_base", "delay_rpm")):
                    out.append(abs((vals[a] + vals[b] * rpm) - (truth[a] + truth[b] * rpm)) < 0.05)
                out.append(abs(fmep(vals, rpm) - fmep(truth, rpm)) < 0.002)
            out.append(abs(vals["ua_port"] / truth["ua_port"] - 1.0) < 1e-4)
            return all(out)
        truth = {n: v["cycle"][n] for n in epa_fit.S4_PARAMS}
        self.assertTrue(close(st.values, truth))
        # the control: the same test against a truth whose burn is 2 % longer fails
        moved = dict(truth, burn_base=truth["burn_base"] * 1.02, burn_rpm=truth["burn_rpm"] * 1.02)
        self.assertFalse(close(st.values, moved))

    def test_five_starts_the_weakest_direction_and_the_reports(self):
        st = form_a_fit().stages["S4"]
        rep = st.report
        self.assertEqual([s["from"] for s in rep["starts"]], ["x1.0", "x0.8", "x1.2", "weakest+", "weakest-"])
        vec = np.array([rep["weakest_direction"]["vector"][n] for n in epa_fit.S4_PARAMS])
        self.assertAlmostEqual(float(np.linalg.norm(vec)), 1.0, places=12)
        self.assertGreater(vec[np.argmax(np.abs(vec))], 0.0)
        self.assertTrue(math.isfinite(rep["weakest_direction"]["sd"]))
        self.assertEqual(set(rep["weakest_direction"]["ki_at_climb_cell"]), {"fit", "plus", "minus"})
        best = min(s["cost"] for s in rep["starts"])
        # the declared final polish (WP3's second fix of 23 October 2026): from the start that stopped lowest,
        # at TOLERANCES["S4_polish"], kept since trf only lowers the cost
        pol = rep["polish"]
        self.assertEqual((pol["from"], pol["cost_before"], pol["kept"]), (rep["best_start"], best, True))
        self.assertLessEqual(st.convergence.cost, best)
        self.assertEqual(st.convergence.cost, pol["cost_after"])
        self.assertEqual(set(pol["departure_scale_units"]), set(epa_fit.S4_PARAMS))
        self.assertEqual(set(rep["residuals"]["by_population"]), {"hot_lambda1", "part_load"})
        self.assertTrue(rep["physical_checks"]["fmep_positive"])
        self.assertEqual(set(rep["data_or_prior"]), set(epa_fit.S4_PARAMS))
        self.assertEqual(len(rep["covariance"]), 9)
        # the five starts' end points on the weakest direction, from the kept point (WP3's fix of 23 October 2026)
        res = rep["resolution"]
        self.assertEqual([q["from"] for q in res["weakest_direction_projection"]], [s["from"] for s in rep["starts"]])
        kept = next(q for q in res["weakest_direction_projection"] if q["from"] == rep["best_start"])
        self.assertAlmostEqual(kept["scale_units"], -pol["departure_along_weakest_scale_units"], places=9)
        self.assertGreaterEqual(res["spread_scale_units"], 0.0)

    def test_a_zero_column_at_the_start_is_a_coding_defect(self):
        v, view, rows = dataset()
        fit = form_a_fit()
        orig = epa_fit._S4Model.jac_data

        def zeroed(self_, th):
            J = orig(self_, th)
            J[:, 8] = 0.0
            return J
        epa_fit._S4Model.jac_data = zeroed
        try:
            with self.assertRaises(epa_fit.FitDefect):
                epa_fit.s4_burn(epa_fit.cal_rows(rows), name=NAME, values=fit.values, view=view, form="A", jobs=JOBS,
                                conventions=epa_stats.NOMINAL, dtheta=DTH,
                                start={n: fit.values["cycle"][n] for n in epa_fit.S4_PARAMS})
        finally:
            epa_fit._S4Model.jac_data = orig
        # the same zero column at the optimum is reported, never raised (amendment D10)
        J = np.ones((4, 3))
        J[:, 1] = 0.0
        self.assertEqual(epa_fit._zero_columns(J, ("a", "b", "c")), ["b"])
        with self.assertRaises(epa_fit.FitDefect):
            epa_fit._assert_columns_at_start(J, ("a", "b", "c"), "test")
        epa_fit._assert_columns_at_start(np.ones((4, 3)), ("a", "b", "c"), "test")


class S5(fx.Guarded):
    def test_recovers_the_rich_slope_and_flags_its_bound(self):
        for slope, hit in ((0.9, False), (1.8, True)):
            v, view, rows = dataset(f"C{slope}", form="A+B+C", ce_rich_slope=slope)
            vals = {k: dict(v[k]) for k in engines.FROZEN_SECTIONS}
            s4 = epa_fit.StageResult(stage="S4", values={n: v["cycle"][n] for n in epa_fit.S4_PARAMS}, rows_used=0,
                                     rows_excluded={}, flags=(), bounds_active=(), convergence=None, report={})
            vals["cycle"]["ce_rich_slope"] = float(engines.SHARED_RICH_SLOPE)
            with _NoRidge():
                st = epa_fit.s5_rich_slope(epa_fit.cal_rows(rows), name=NAME, values=vals, s4=s4, jobs=JOBS, view=view,
                                           conventions=epa_stats.NOMINAL, dtheta=DTH)
            self.assertEqual("S5_bound_hit" in st.flags, hit, msg=slope)
            if not hit:
                self.assertAlmostEqual(st.values["ce_rich_slope"], slope, delta=2 * epa_fit.S5_XATOL)
            else:
                self.assertGreater(st.values["ce_rich_slope"], 1.5 - 2 * epa_fit.S5_XATOL)
            self.assertGreaterEqual(st.rows_used, 9)
            # the slope's standard uncertainty, from the residuals' Jacobian (WP3's fix of 23 October 2026)
            self.assertIsNotNone(st.report["sigma"])
            self.assertTrue(math.isfinite(st.report["sigma"]) and st.report["sigma"] >= 0.0)


class S6(fx.Guarded):
    def test_the_geometric_mean_knock_integral_is_one(self):
        v, view, rows = dataset()
        fit = form_a_fit()
        st = fit.stages["S6"]
        use = [r for r in rows if epa_fit._final(r)]
        model = epa_fit.RowModel(epa_fit.candidate(NAME, fit.values), fuels=view.fuel_by_table)
        xs = epa_fit._inputs(use, view=view, conventions=epa_stats.NOMINAL, model=model)
        ki = np.array([model.result(x, dtheta=DTH).knock_integral for x in xs])
        self.assertLess(abs(float(np.mean(np.log(ki)))), epa_fit.S6_TOL)
        # by hand: one sweep at the B58's knock_a, then the rescale
        vv = json.loads(json.dumps(fit.values))
        vv["cycle"]["knock_a"] = float(engines.typed_engine("b58").cycle.knock_a)
        m0 = epa_fit.RowModel(epa_fit.candidate(NAME, vv), fuels=view.fuel_by_table)
        k0 = np.array([m0.result(x, dtheta=DTH).knock_integral for x in xs])
        self.assertEqual(st.values["knock_a"], float(vv["cycle"]["knock_a"] * math.exp(float(np.mean(np.log(k0))))))
        # the control: one per cent off, the mean is far from zero
        vv["cycle"]["knock_a"] = st.values["knock_a"] * 1.01
        m1 = epa_fit.RowModel(epa_fit.candidate(NAME, vv), fuels=view.fuel_by_table)
        k1 = np.array([m1.result(x, dtheta=DTH).knock_integral for x in xs])
        self.assertGreater(abs(float(np.mean(np.log(k1)))), 1e-3)


class Verify(fx.Guarded):
    def test_every_shortcut_is_run_cycle(self):
        fit = form_a_fit()
        self.assertLessEqual(fit.stages["verify"].report["max_rel_shortcut"], epa_fit.VERIFY_REL)
        self.assertLessEqual(fit.stages["verify"].report["s2_verify_max_rel"], epa_fit.S2_VERIFY_REL)
        # the control: a shortcut one part in 1e7 off the plant is a coding defect
        v, view, rows = dataset()
        orig = epa_fit._inner

        def off(cached, x, e, th):
            t, tit, f, aux = orig(cached, x, e, th)
            return t * (1.0 + 1e-7), tit, f, aux
        stages = dict(fit.stages)
        epa_fit._inner = off
        try:
            m = epa_fit._S4Model([r for r in rows if r.pops.fired_l1], epa_fit._inputs(
                [r for r in rows if r.pops.fired_l1], view=view, conventions=epa_stats.NOMINAL,
                model=epa_fit.RowModel(epa_fit.candidate(NAME, fit.values), fuels=view.fuel_by_table)),
                epa_fit.RowModel(epa_fit.candidate(NAME, fit.values), fuels=view.fuel_by_table), view=view, dtheta=DTH,
                jobs=JOBS, centre=epa_fit.ridge_centre())
            th = np.array([fit.values["cycle"][n] for n in epa_fit.S4_PARAMS])
            T, TIT, _F, _a = m.outputs(th)
            bad = {epa_fit._skey(r): {"torque_nm": float(T[i]), "egt_c": float(TIT[i])} for i, r in enumerate(m.rows)}
        finally:
            epa_fit._inner = orig
        stages["S4"] = replace(fit.stages["S4"], report=dict(fit.stages["S4"].report, shortcut=bad))
        with self.assertRaises(epa_fit.FitDefect):
            epa_fit.verify(epa_fit.cal_rows(rows), name=NAME, values=fit.values, jobs=JOBS, view=view,
                           conventions=epa_stats.NOMINAL, dtheta=DTH, stages=stages)

    def test_the_fuel_and_the_air_shortcuts_are_checked_at_the_final_constants(self):
        fit = form_a_fit()
        v, view, rows = dataset()
        rep = fit.stages["verify"].report
        n_s2 = len(epa_fit._s2_use(epa_fit.cal_rows(rows)))
        self.assertGreaterEqual(rep["rows_air"], n_s2)
        self.assertLessEqual(rep["max_rel_air_at_final"], epa_fit.S2_VERIFY_REL)
        self.assertTrue(all("mdot_fuel_gps" in s for s in fit.stages["S4"].report["shortcut"].values()))

        def run(stages):
            return epa_fit.verify(epa_fit.cal_rows(rows), name=NAME, values=fit.values, jobs=JOBS, view=view,
                                  conventions=epa_stats.NOMINAL, dtheta=DTH, stages=stages)
        self.assertLessEqual(run(fit.stages).report["max_rel_shortcut"], epa_fit.VERIFY_REL)
        # the control (fuel): the model fuel the efficiency residual divides by, 1e-7 off
        short = {k: dict(s, mdot_fuel_gps=s["mdot_fuel_gps"] * (1.0 + 1e-7))
                 for k, s in fit.stages["S4"].report["shortcut"].items()}
        stages = dict(fit.stages, S4=replace(fit.stages["S4"], report=dict(fit.stages["S4"].report, shortcut=short)))
        with self.assertRaises(epa_fit.FitDefect):
            run(stages)
        # the control (air): S2's unit-VE air one part in 1e9 off the plant's
        orig = epa_fit._air_at_unit_ve
        epa_fit._air_at_unit_ve = lambda e, rpm, mp, iat: orig(e, rpm, mp, iat) * (1.0 + 1e-9)
        try:
            with self.assertRaises(epa_fit.FitDefect):
                run(fit.stages)
        finally:
            epa_fit._air_at_unit_ve = orig

    def test_a_ve_at_its_rail_is_listed_over_every_calibration_row(self):
        """PLAN.md 5.6 over every calibration row the in-sample stage evaluates (WP3's fix of 23 October 2026):
        none on the dataset; the control, a final candidate whose VE sits at its upper rail, lists every row."""
        fit = form_a_fit()
        v, view, rows = dataset()
        rep = fit.stages["verify"].report
        self.assertEqual((rep["ve_at_clip_rows"], rep["rows_ve_checked"]), ([], len(epa_fit.cal_rows(rows))))
        # the control: a VE curve raised past its upper rail at every row (the plant clips it, and run_cycle's air
        # is the clipped VE's, so the air shortcut still holds; S4's cached cycles, made at the fitted VE, are
        # left out of this check), and every row is listed and flagged
        high = json.loads(json.dumps(fit.values))
        high["cycle"]["ve_base"] = 5.0
        stages = dict(fit.stages, S4=replace(fit.stages["S4"], report=dict(fit.stages["S4"].report, shortcut={})))
        st = epa_fit.verify(epa_fit.cal_rows(rows), name=NAME, values=high, jobs=JOBS, view=view,
                            conventions=epa_stats.NOMINAL, dtheta=DTH, stages=stages)
        self.assertEqual(len(st.report["ve_at_clip_rows"]), len(epa_fit.cal_rows(rows)))
        self.assertIn("verify_ve_at_clip", st.flags)

    def test_parameters_that_never_left_their_start_are_reported(self):
        fit = form_a_fit()
        self.assertEqual(fit.stages["verify"].report["unmoved_from_start"], {"S2": [], "S4": []})
        self.assertNotIn("verify_unmoved_parameter", fit.flags)
        # the control (mistake 25): an estimate equal to its declared start is listed
        s4, s2 = fit.stages["S4"], fit.stages["S2"]
        stuck = replace(s4, values=dict(s4.values, ua_port=s4.report["starts"][0]["x0"]["ua_port"]))
        self.assertEqual(epa_fit._unmoved(dict(fit.stages, S4=stuck))["S4"], ["ua_port"])
        stuck2 = replace(s2, values=dict(s2.values, ve_width=s2.report["declared_start"]["ve_width"]))
        self.assertEqual(epa_fit._unmoved(dict(fit.stages, S2=stuck2))["S2"], ["ve_width"])


class FitForm(fx.Guarded):
    def test_two_runs_are_byte_identical(self):
        v, view, rows = dataset()
        a = form_a_fit()
        b = epa_fit.fit_form(NAME, rows, view=view, form="A", start=None, jobs=1, dtheta=DTH)
        self.assertEqual(epa_fit.canonical(a.as_json()), epa_fit.canonical(b.as_json()))
        self.assertEqual(a.frozen_sections_sha256, engines.frozen_sections_sha256(a.values))
        # the control: one ulp of one frozen constant moves the hash
        vv = json.loads(json.dumps(a.values))
        vv["cycle"]["ua_port"] = float(np.nextafter(vv["cycle"]["ua_port"], 1e9))
        self.assertNotEqual(engines.frozen_sections_sha256(vv), a.frozen_sections_sha256)

    def test_values_are_the_derived_files_sections_python_typed(self):
        fit = form_a_fit()
        self.assertEqual(sorted(fit.values), sorted(engines.FROZEN_SECTIONS))
        self.assertEqual(sorted(fit.values["cycle"]), sorted(epa_fit.CYCLE_FIELDS))
        self.assertEqual(sorted(fit.values["ecu"]), sorted(epa_fit.ECU_FIELDS))
        self.assertEqual((fit.values["cycle"]["ve_map"], fit.values["cycle"]["ve_cam"], fit.values["ecu"]["cam_on"]),
                         (0.0, 0.0, 0))
        epa_fit.candidate(NAME, fit.values)
        # the control (amendment B10): a NumPy scalar is refused by the constructor
        vv = json.loads(json.dumps(fit.values))
        vv["cycle"]["burn_base"] = np.float64(vv["cycle"]["burn_base"])
        with self.assertRaises(TypeError):
            epa_fit.candidate(NAME, vv)

    def test_the_provisional_completion_moves_no_row_output(self):
        v, view, rows = dataset()
        fit = form_a_fit()
        other = {"deliverable_torque": [[1000, 100.0], [6000, 300.0]], "k3": {"turb_knee_k": 900.0},
                 "loop": {"torque_floor_nm": 55.0}}
        p1 = epa_fit.candidate(NAME, fit.values)
        p2 = engines.build_candidate(NAME, dict({k: fit.values[k] for k in engines.FROZEN_SECTIONS}, **other))
        self.assertNotEqual(engines.engine_sha(p1), engines.engine_sha(p2))
        m1, m2 = (epa_fit.RowModel(p, fuels=view.fuel_by_table) for p in (p1, p2))
        xs = epa_fit._inputs(rows, view=view, conventions=epa_stats.NOMINAL, model=m1)
        for x in xs[::5]:
            self.assertTrue(epa_fit._same_result(m1.result(x, dtheta=DTH), m2.result(x, dtheta=DTH)))
            self.assertEqual(m1.ecu_at(x.rpm, x.map_kpa, x.iat_k, x.ect_k),
                             m2.ecu_at(x.rpm, x.map_kpa, x.iat_k, x.ect_k))
        # the control: a frozen constant does move the outputs
        vv = json.loads(json.dumps(fit.values))
        vv["cycle"]["knock_a"] *= 1.1
        m3 = epa_fit.RowModel(epa_fit.candidate(NAME, vv), fuels=view.fuel_by_table)
        self.assertFalse(epa_fit._same_result(m1.result(xs[-1], dtheta=DTH), m3.result(xs[-1], dtheta=DTH)))

    def test_form_c_keeps_a_plus_bs_s2_and_s4(self):
        fa, fb, fc = form_c_fits()
        self.assertIs(fc.stages["S2"], fb.stages["S2"])
        self.assertIs(fc.stages["S4"], fb.stages["S4"])
        self.assertIn("S5", fc.stages)
        self.assertNotIn("S5", fb.stages)
        self.assertEqual(fb.values["cycle"]["ce_rich_slope"], float(engines.SHARED_RICH_SLOPE))
        self.assertAlmostEqual(fc.values["cycle"]["ce_rich_slope"], 0.9, delta=0.01)
        # A+B refits S4 from A's solution (PLAN.md 5.4), it does not keep it
        self.assertEqual(fb.stages["S4"].report["starts"][0]["x0"]["burn_base"], fa.values["cycle"]["burn_base"])


FIT_JSON_KEYS = {"schema", "form", "start", "settings", "stages", "values", "frozen_sections_sha256",
                 "declarations", "flags"}           # WP3_INTERFACES.md 7.2, provenance added by calibrate_epa
SETTINGS_KEYS = {"ridge_w", "ridge_centre", "ridge_scale", "bounds", "starts", "x_scale", "ftol", "xtol", "gtol",
                 "max_nfev", "second_attempt_nfev", "dtheta_deg", "jobs"}
STAGE_KEYS = {"values", "rows_used", "rows_excluded", "flags", "bounds_active", "convergence", "report"}


class Records(fx.Guarded):
    def test_fit_record_has_the_interfaces_keys_and_is_strict_json(self):
        fa, fb, fc = form_c_fits()
        _v, view, _rows = dataset("C0.9", form="A+B+C", ce_rich_slope=0.9)
        decl = epa_fit.fit_declarations(epa_fit.candidate(NAME, fc.values), view=view, other_octane=None, dtheta=DTH)
        for fit, start in ((fa, None), (fb, fa), (fc, fb)):
            rec = epa_fit.fit_record(fit, view=view, start=start, dtheta=DTH, jobs=JOBS, declarations=decl)
            self.assertEqual(set(rec), FIT_JSON_KEYS)
            self.assertLessEqual(SETTINGS_KEYS, set(rec["settings"]))
            want = {"S1", "S2", "S3a", "S3b", "S3c", "S4", "S6", "verify"} | ({"S5"} if fit.form == "A+B+C" else set())
            self.assertEqual(set(rec["stages"]), want, msg=fit.form)
            self.assertTrue(all(set(s) == STAGE_KEYS for s in rec["stages"].values()))
            # strict JSON (allow_nan=False, as epa_freeze.write_json_atomic writes it):
            # S5's Brent has no gradient norm, written null, never NaN
            json.dumps(rec, allow_nan=False)
            self.assertEqual(rec["frozen_sections_sha256"], engines.frozen_sections_sha256(rec["values"]))
            self.assertEqual(rec["start"]["from"], "B58" if start is None else start.form)
        rc = epa_fit.fit_record(fc, view=view, start=fb, dtheta=DTH, jobs=JOBS, declarations=decl)
        self.assertIsNone(rc["stages"]["S5"]["convergence"]["grad_norm"])
        self.assertEqual(rc["settings"]["bounds"]["ve_rpm"], [1500.0, 4500.0])        # the view's end lines (D9)
        self.assertIn("ce_rich_slope", rc["settings"]["ridge_centre"])
        self.assertNotIn("ce_rich_slope",
                         epa_fit.fit_record(fa, view=view, start=None, dtheta=DTH, jobs=JOBS,
                                            declarations=decl)["settings"]["ridge_centre"])
        # the control: the start's hash names where the fit started
        ra = epa_fit.fit_record(fa, view=view, start=None, dtheta=DTH, jobs=JOBS, declarations=decl)
        rb = epa_fit.fit_record(fb, view=view, start=fa, dtheta=DTH, jobs=JOBS, declarations=decl)
        self.assertNotEqual(ra["start"]["values_sha256"], rb["start"]["values_sha256"])
        self.assertEqual(rb["start"]["values_sha256"], epa_rows.canonical_sha256(fa.values["cycle"]))

    def test_the_octane_declaration_is_measured_where_two_batches_meet(self):
        _v, view, _rows = dataset()
        p = epa_fit.candidate(NAME, truth_values())
        one = epa_fit.fit_declarations(p, view=view, other_octane=None, dtheta=DTH)
        self.assertEqual((one["octane_moves_only_knock"], one["ford_cell9_octane"]), (None, None))
        self.assertIsNone(epa_fit.stage0_declarations(_rows, view=view)["ford_cell9_octane"])
        # two batches (the Ford's case): the claim is measured, and must be
        f2 = replace(view.fuel_by_table[TABLE_S], ftag="another batch")
        view2 = replace(view, fuel_by_table={TABLE_S: f2, TABLE_F: view.fuel_by_table[TABLE_F]})
        with self.assertRaises(ValueError):
            epa_fit.fit_declarations(p, view=view2, other_octane=None, dtheta=DTH)
        two = epa_fit.fit_declarations(p, view=view2, other_octane=96.6, dtheta=DTH)
        self.assertIs(two["octane_moves_only_knock"], True)
        self.assertEqual(two["ford_cell9_octane"], epa_fit.FORD_CELL9_OCTANE)
        self.assertEqual(epa_fit.stage0_declarations(_rows, view=view2)["ford_cell9_octane"], epa_fit.FORD_CELL9_OCTANE)
        # the control: a cycle the octane reached beyond the knock is a coding defect
        orig = epa_fit._cycle_at

        def leaky(engine, x, *, dtheta, ecu_engine):
            r = orig(engine, x, dtheta=dtheta, ecu_engine=ecu_engine)
            return replace(r, egt_c=r.egt_c + 1e-6 * (engine.cycle.octane - 97.0))
        epa_fit._cycle_at = leaky
        try:
            with self.assertRaises(epa_fit.FitDefect):
                epa_fit.fit_declarations(p, view=view2, other_octane=96.6, dtheta=DTH)
        finally:
            epa_fit._cycle_at = orig


class Ladder(fx.Guarded):
    def test_stops_at_a_for_an_a_truth_and_at_a_plus_b_for_a_ve_map_truth(self):
        v, view, rows = dataset()
        lad = epa_fit.ladder(NAME, rows, view=view, jobs=JOBS, dtheta=DTH)
        self.assertEqual(lad.chosen, "A")
        self.assertEqual([f.form for f in lad.fits], ["A"])                 # forms after it are not fitted
        self.assertTrue(lad.in_sample["A"].passes)
        v, view, rows = dataset("B", form="A+B", ve_map=2e-3)
        lad = epa_fit.ladder(NAME, rows, view=view, jobs=JOBS, dtheta=DTH)
        self.assertEqual(lad.chosen, "A+B")
        self.assertEqual([f.form for f in lad.fits], ["A", "A+B"])
        self.assertFalse(lad.in_sample["A"].passes)                         # the control: A cannot fit it
        self.assertIn("E2a", lad.in_sample["A"].failing)
        self.assertTrue(lad.in_sample["A+B"].passes)
        self.assertAlmostEqual(lad.fits[1].values["cycle"]["ve_map"], 2e-3, delta=1e-4)

    def test_the_ladder_follows_its_judge(self):
        # decision 49's rule on its own: the first form whose statistics pass; none, A+B+C+D
        v, view, rows = dataset()
        calls = []

        class Verdict:
            def __init__(self, ok):
                self.passes, self.failing, self.no_line, self.noise = ok, () if ok else ("E1a",), (), ()

        def judge(name, fit, y, *, view, jobs, dtheta):
            calls.append(fit.form)
            return Verdict(False)
        lad = epa_fit._ladder(NAME, rows, view=view, jobs=JOBS, dtheta=DTH, judge=judge)
        self.assertEqual(lad.chosen, "A+B+C+D")
        self.assertEqual(calls, list(engines.CYCLE_FORMS))
        self.assertIn("no form passes", lad.reason)
        # amendment D13: form A failing E1a moves the ladder (the contract's criterion)
        # and the reason carries D13's reading of it, once, at form A
        self.assertEqual(lad.reason.count(epa_fit.D13_DECLARATION), 1)
        self.assertIn("A: fails E1a (" + epa_fit.D13_DECLARATION, lad.reason)
        self.assertIn(epa_fit.D13_DECLARATION, [f.stages["S4"].report["d13"] for f in lad.fits][0])

        # the control: a form A failing E2a alone gives no D13 reading (the forms are
        # stand-ins here: the reading is the ladder's, not a fit's)
        class E2aVerdict(Verdict):
            def __init__(self, ok):
                super().__init__(ok)
                self.failing = () if ok else ("E2a",)

        orig = epa_fit.fit_form
        epa_fit.fit_form = lambda name, y, *, view, form, start, jobs, dtheta: lad.fits[engines.CYCLE_FORMS.index(form)]
        try:
            lad2 = epa_fit._ladder(NAME, rows, view=view, jobs=JOBS, dtheta=DTH,
                                   judge=lambda name, fit, y, *, view, jobs, dtheta: E2aVerdict(fit.form == "A+B"))
        finally:
            epa_fit.fit_form = orig
        self.assertEqual(lad2.chosen, "A+B")
        self.assertEqual([f.form for f in lad2.fits], ["A", "A+B"])
        self.assertNotIn(epa_fit.D13_DECLARATION, lad2.reason)


class LadderChoice(fx.Guarded):
    """ladder_choice, the ladder's choice and reason in one definition (WP3's integration, 23 October
    2026: calibrate_epa.py check recomputes in_sample.json through it), and poison_stages, the poison
    run's stages through the fit's own calls (amendment C8)."""

    class V:
        def __init__(self, ok, failing=("E1a",), no_line=(), noise=()):
            self.passes, self.failing, self.no_line, self.noise = ok, () if ok else failing, no_line, noise

    def test_the_choice_and_its_reason(self):
        V = self.V
        self.assertEqual(epa_fit.ladder_choice({"A": V(True)}), ("A", "A: no in-sample statistic but E8 fails"))
        chosen, reason = epa_fit.ladder_choice({"A": V(False, ("E2a",)), "A+B": V(True, no_line=("E4b",))})
        self.assertEqual(chosen, "A+B")
        self.assertEqual(reason, "A: fails E2a; A+B: no in-sample statistic but E8 fails (no line: E4b)")
        # decision 77: the statistics whose noise exceeds R are named per form, beside decision 55's
        chosen, reason = epa_fit.ladder_choice({"A": V(False, ("E2a",), noise=("D1",)),
                                                "A+B": V(True, no_line=("E8",), noise=("E4b", "L1"))})
        self.assertEqual((chosen, reason), ("A+B", "A: fails E2a (noise exceeds R: D1); A+B: no in-sample statistic "
                                                   "but E8 fails (no line: E8; noise exceeds R: E4b, L1)"))
        chosen, reason = epa_fit.ladder_choice({f: V(False) for f in engines.CYCLE_FORMS})
        self.assertEqual(chosen, "A+B+C+D")
        self.assertIn("no form passes", reason)
        self.assertEqual(reason.count(epa_fit.D13_DECLARATION), 1)
        # the controls: a set the ladder cannot have produced is refused
        for bad in ({"A+B": V(True)}, {"A": V(True), "A+B": V(True)}, {"A": V(False)}, {}):
            with self.assertRaises(ValueError):
                epa_fit.ladder_choice(bad)

    def test_the_ladder_moves_on_only_on_a_fails(self):
        """Decision 77 through the ladder itself (_ladder, the fits stood in: the criterion is the stage's, not a
        fit's): an E4b of 16 % against R 15 % with u_stat 8 (2u = 16 > 15, and 16 - 16 <= 15) neither blocks nor
        passes, so the ladder stops at A and names it; with u_stat 2 (16 - 4 = 12 <= 15) it passes, and stops at
        A; with E4b 40 % and u_stat 2 (40 - 4 > 15) it fails at every form, and the ladder climbs to A+B+C+D.
        The control: the literal |E_cal| <= R, read off the same stages, would have climbed on the first two."""
        def run(stage):
            calls = []

            def judge(name, fit, y, *, view, jobs, dtheta):
                calls.append(fit.form)
                return stage

            def stand_in(name, y, *, view, form, start, jobs, dtheta):
                return epa_fit.FormFit(engine=name, form=form, values={}, stages={}, flags=(),
                                       frozen_sections_sha256="stand-in")
            with mock.patch.object(epa_fit, "fit_form", stand_in):
                lad = epa_fit._ladder(NAME, (), view=None, jobs=1, dtheta=DTH, judge=judge)
            return lad, calls
        noisy, quiet, bad = e4b_stage(16.0, 8.0), e4b_stage(16.0, 2.0), e4b_stage(40.0, 2.0)
        self.assertEqual((noisy.passes, noisy.failing, noisy.noise), (True, (), ("E4b",)))
        lad, calls = run(noisy)
        self.assertEqual((lad.chosen, calls), ("A", ["A"]))
        self.assertEqual(lad.reason, "A: no in-sample statistic but E8 fails (noise exceeds R: E4b)")
        rec = epa_fit.form_record(lad.in_sample["A"])
        self.assertEqual(rec, {"E4b": {"E": 16.0, "u_stat": 8.0, "R": 15.0, "outcome": "neither",
                                       "why": epa_stats.NOISE_EXCEEDS_R}})
        lad, calls = run(quiet)
        self.assertEqual((lad.chosen, calls, quiet.noise), ("A", ["A"], ()))
        lad, calls = run(bad)
        self.assertEqual((lad.chosen, calls), ("A+B+C+D", list(engines.CYCLE_FORMS)))
        self.assertTrue(lad.reason.startswith("A: fails E4b; A+B: fails E4b"), lad.reason)
        # the control: the literal criterion on the same stages fails the first two, and the ladder climbs
        for st in (noisy, quiet):
            r = st.results["E4b"]
            literal = replace(st, passes=abs(r.E) <= r.R, failing=("E4b",), noise=())
            self.assertFalse(literal.passes)
            lad, calls = run(literal)
            self.assertEqual((lad.chosen, calls), ("A+B+C+D", list(engines.CYCLE_FORMS)))

    def test_poison_stages_are_the_fits_own(self):
        """On form A's dataset, poison_stages gives S1 and S3a-S3c as _fit computed them (the same rows,
        view, base plant and censoring), S3d as s3d_cam gives it (None where no row carries a cam value), and
        S2 and S6 at the
        frozen values the same on a second call (deterministic, mistake 10's one definition)."""
        v, view, rows = dataset()
        fit = form_a_fit()
        got = epa_fit.poison_stages(NAME, rows, view=view, values=fit.values, jobs=JOBS, dtheta=DTH)
        self.assertEqual(tuple(got), epa_fit.POISON_STAGES)
        for k in ("S1", "S3a", "S3b", "S3c"):
            self.assertEqual(epa_fit.canonical(epa_fit.stage_json(got[k])),
                             epa_fit.canonical(epa_fit.stage_json(fit.stages[k])), k)
        self.assertEqual(epa_fit.canonical(epa_fit.stage_json(got["S3d"])),
                         epa_fit.canonical(epa_fit.stage_json(epa_fit.s3d_cam(epa_fit.cal_rows(rows), view=view))))
        no_cam = tuple(replace(r, cam_cad=None, cam_missing=True) for r in rows)
        self.assertIsNone(epa_fit.poison_stages(NAME, no_cam, view=view, values=fit.values, jobs=JOBS,
                                                dtheta=DTH)["S3d"])
        again = epa_fit.poison_stages(NAME, rows, view=view, values=fit.values, jobs=JOBS, dtheta=DTH)
        for k in ("S2", "S6"):
            self.assertEqual(epa_fit.canonical(epa_fit.stage_json(got[k])),
                             epa_fit.canonical(epa_fit.stage_json(again[k])), k)
        # the control: one row's turbine-inlet pressure moved moves S1
        moved = list(rows)
        i = next(j for j, r in enumerate(moved) if r.pops.fired)
        moved[i] = replace(moved[i], tip_kpa=moved[i].tip_kpa + 5.0)
        other = epa_fit.poison_stages(NAME, tuple(moved), view=view, values=fit.values, jobs=JOBS, dtheta=DTH)
        self.assertNotEqual(epa_fit.canonical(epa_fit.stage_json(other["S1"])),
                            epa_fit.canonical(epa_fit.stage_json(got["S1"])))

    def test_the_crank_step_is_the_plants(self):
        import plant as plant_model
        self.assertEqual(epa_fit.DTHETA_DEG, plant_model.DTHETA_DEG)
        self.assertIs(type(epa_fit.DTHETA_DEG), float)
        self.assertEqual(epa_fit.json_safe({"a": (1, float("nan"))}), {"a": [1, None]})


class Identities(fx.Guarded):
    def setUp(self):
        self.v, self.view, self.rows = dataset()
        self.p = epa_fit.candidate(NAME, self.v)
        self.grid = epa_fit.synthetic_grid(self.p)

    def test_the_retag_at_the_shared_slope_is_the_engine_bit_for_bit(self):
        self.assertTrue(epa_fit.retag_identity(self.p, grid=self.grid, dtheta=DTH))
        pb = epa_fit.candidate(NAME, truth_values(form="A+B", ve_map=1e-3))
        self.assertTrue(epa_fit.retag_identity(pb, grid=self.grid, dtheta=DTH))
        self.assertEqual(epa_fit.with_rich_slope_probe(pb, slope=0.7).engine.cycle.form, "A+B+C")
        self.assertEqual(epa_fit.with_rich_slope_probe(pb, slope=0.7).engine.cycle.ve_map, 1e-3)
        # the control (amendment B2): one ulp above the shared slope is seen at lambda 0.95,
        # and nowhere at lambda >= 1, where the rich branch is not taken
        # (one ulp of the slope, 1.1e-16, times 1 - lambda can round away against the
        # ulp of the efficiency, so it is seen at some rich points, never at a lean one)
        ulp = epa_fit.with_rich_slope_probe(self.p, slope=float(np.nextafter(engines.SHARED_RICH_SLOPE, 1.0))).engine
        own = self.p.engine
        seen = {True: 0, False: 0}
        for pt in self.grid:
            a = epa_fit._grid_results(own, (pt,), DTH, own)[0]
            b = epa_fit._grid_results(ulp, (pt,), DTH, ulp)[0]
            if pt[5] >= 1.0:
                self.assertTrue(epa_fit._same_result(a, b), msg=pt)
            elif pt[5] == 0.95:
                seen[epa_fit._same_result(a, b)] += 1
        self.assertGreater(seen[False], 0)

    def test_the_octane_moves_only_the_knock_integral(self):
        self.assertTrue(epa_fit.octane_moves_only_knock(self.p, octane=96.6, grid=self.grid, dtheta=DTH))
        self.assertTrue(epa_fit.octane_moves_only_knock(self.p, octane=float(self.p.engine.cycle.octane),
                                                        grid=self.grid, dtheta=DTH))
        with self.assertRaises(TypeError):
            epa_fit.octane_moves_only_knock(self.p, octane=np.float64(96.6), grid=self.grid, dtheta=DTH)
        # the control: a cycle whose torque the octane reached would be caught
        orig = epa_fit._cycle_at

        def leaky(engine, x, *, dtheta, ecu_engine):
            r = orig(engine, x, dtheta=dtheta, ecu_engine=ecu_engine)
            return replace(r, torque_nm=r.torque_nm * (1.0 + 1e-6 * (engine.cycle.octane - 97.0)))
        epa_fit._cycle_at = leaky
        try:
            self.assertFalse(epa_fit.octane_moves_only_knock(self.p, octane=96.6, grid=self.grid, dtheta=DTH))
        finally:
            epa_fit._cycle_at = orig

    def test_perturbed_and_knock_rescale(self):
        p2 = epa_fit.perturbed(self.p, record="thermal", field="c_turb", value=self.p.engine.thermal.c_turb * 0.75)
        self.assertEqual(p2.engine.thermal.c_turb, self.p.engine.thermal.c_turb * 0.75)
        self.assertEqual(self.p.engine.thermal.c_turb, float(_spec("thermal", "c_turb")))   # the frozen one untouched
        p3 = epa_fit.perturbed(self.p, record="fuel", field="lhv_j_per_kg", value=44.0e6)
        self.assertEqual((p3.engine.fuel.lhv_j_per_kg, p3.engine.thermal.fuel_lhv_j_per_kg), (44.0e6, 44.0e6))
        with self.assertRaises(TypeError):
            epa_fit.perturbed(self.p, record="cycle", field="ua_port", value=np.float64(20.0))
        with self.assertRaises(ValueError):
            epa_fit.perturbed(self.p, record="thermal", field="fuel_lhv_j_per_kg", value=44.0e6)
        # E6 row 7: knock_a / factor is KI x factor (KI is 1/knock_a)
        x = epa_fit._inputs(self.rows[-1:], view=self.view, conventions=epa_stats.NOMINAL,
                            model=epa_fit.RowModel(self.p, fuels=self.view.fuel_by_table))[0]
        k0 = epa_fit.RowModel(self.p, fuels=self.view.fuel_by_table).result(x, dtheta=DTH).knock_integral
        for f in (0.90, 1.10):
            vv = epa_fit.knock_rescale(self.v, factor=f)
            self.assertEqual(self.v["cycle"]["knock_a"], truth_values()["cycle"]["knock_a"])
            k = epa_fit.RowModel(epa_fit.candidate(NAME, vv), fuels=self.view.fuel_by_table).result(
                x, dtheta=DTH).knock_integral
            self.assertAlmostEqual(k / k0, f, places=12)


NO_OP = epa_stats.Conventions(snap=True, cell_referenced=False, afr_st=None, lhv_j_per_kg=None)


class E6Refits(fx.Guarded):
    def test_a_no_op_convention_gives_the_frozen_fit_back_on_noisy_rows(self):
        """PLAN.md 5.7: lambda_ref = 1.000 makes row 1 a no-op by construction, and the refit re-runs the
        frozen form's fit as it ran (S4 from the frozen form's own first start; WP3's fix of 23 October 2026,
        on the fit review's finding that a refit from the frozen solution moved S4 and S6 on noisy rows): the
        frozen sections come back bit for bit. The control: AFR_st 14.7 moves the calibration air, the
        breathing and the hash."""
        v, view, rows = dataset()
        truths = epa_fit.t0_truths(NAME, view=view, yield_=rows)
        noisy = epa_fit.t0_rows(rows, truth=truths[0], seed=1, view=view, dtheta=DTH, jobs=JOBS)
        frozen = epa_fit.fit_form(NAME, noisy, view=view, form="A", start=None, jobs=JOBS, dtheta=DTH)
        before = epa_fit.canonical(frozen.as_json())
        r1 = epa_fit.refit_variant(NAME, noisy, view=view, form="A", jobs=JOBS, dtheta=DTH, ladder_fits={"A": frozen},
                                   conventions=NO_OP)
        self.assertEqual(r1.frozen_sections_sha256, frozen.frozen_sections_sha256)
        r2 = epa_fit.refit_variant(NAME, noisy, view=view, form="A", jobs=JOBS, dtheta=DTH, ladder_fits={"A": frozen},
                                   conventions=epa_stats.Conventions(snap=True, cell_referenced=True,
                                                                     afr_st=14.7, lhv_j_per_kg=None))
        self.assertNotEqual(r2.frozen_sections_sha256, frozen.frozen_sections_sha256)
        self.assertGreater(abs(r2.values["cycle"]["ve_base"] / frozen.values["cycle"]["ve_base"] - 1.0), 1e-3)
        self.assertEqual(epa_fit.canonical(frozen.as_json()), before)        # the frozen fit is untouched
        with self.assertRaises(ValueError):                                  # the ladder's fits are required
            epa_fit.refit_variant(NAME, noisy, view=view, form="A+B", jobs=JOBS, dtheta=DTH,
                                  ladder_fits={"A": frozen}, conventions=NO_OP)

    def test_at_a_plus_b_plus_c_the_keep_policy_is_the_ladders(self):
        """A+B+C keeps A+B's S2 and S4 (PLAN.md 5.3): the variant fits its own A+B from the frozen A, keeps
        those, and with a convention that moves nothing gives the frozen A+B+C back bit for bit."""
        fa, fb, fc = form_c_fits()
        v, view, rows = dataset("C0.9", form="A+B+C", ce_rich_slope=0.9)
        r = epa_fit.refit_variant(NAME, rows, view=view, form="A+B+C", jobs=JOBS, dtheta=DTH, conventions=NO_OP,
                                  ladder_fits={"A": fa, "A+B": fb, "A+B+C": fc})
        self.assertEqual(r.frozen_sections_sha256, fc.frozen_sections_sha256)


# A form's in-sample stage that is consistent with it (no statistic beyond R + z u_stat): T0's judge tests
# below give it where the stand-in ladder fitted a form.
OK_STAGE = epa_stats.InSample(results={}, passes=True, failing=(), no_line=(), criterion="test", scatter={})


def e4b_stage(E, se):
    """A form's in-sample stage whose only statistic is E4b at E (percent, the synthetic view's R 15 %), its
    pooled u_stat se, judged by epa_stats' own decision 77 rule and aggregated by its own in_sample_stage: fails
    if |E| - 2 se > 15, neither if not and 2 se > 15, else passes; within_noise reads it against R + z se."""
    j = epa_stats.in_sample_judgement({"pooled": (E, se)}, 15.0, report="pooled")
    r = epa_stats.StatResult(row="E4b", stage="in_sample", R=15.0, unit="%", kind="d", E=E, lines=(), deciding=("2500",),
                             certifying=(), worst_line=None, u=None, label=None, kappa=None,
                             passes=epa_stats.IN_SAMPLE_PASSES[j["outcome"]], no_statistic=False, reason=None,
                             without={}, coverage_restricted=None, extra={}, n_rows=5, n_clusters=5, judgement=j)
    return epa_stats.in_sample_stage({"E4b": r})


class T0(fx.Guarded):
    def test_the_synthetic_rows(self):
        v, view, rows = dataset()
        truths = epa_fit.t0_truths(NAME, view=view, yield_=rows)
        self.assertEqual([t.seed for t in truths], [1, 2, 3, 4])
        self.assertEqual([t.expected_form for t in truths], ["A", "A", "A+B", None])
        g = truths[0].values["ecu"]["enr_load"]
        self.assertTrue(max(STEADY_MAP) < g < FINAL_MAP[0])               # amendment D2's case
        a = epa_fit.t0_rows(rows, truth=truths[0], seed=1, view=view, dtheta=DTH, jobs=1)
        b = epa_fit.t0_rows(rows, truth=truths[0], seed=1, view=view, dtheta=DTH, jobs=JOBS)
        c = epa_fit.t0_rows(rows, truth=truths[0], seed=2, view=view, dtheta=DTH, jobs=1)
        self.assertEqual(a, b)                                            # one stream, any pool
        self.assertNotEqual(a, c)                                         # the control: another seed
        self.assertTrue(all(r.origin == "t0" for r in a))
        self.assertEqual([epa_fit._key(r) for r in a], [epa_fit._key(r) for r in rows])
        self.assertEqual([r.speed_rpm for r in a], [r.speed_rpm for r in rows])   # the inputs kept
        for r in a[::7]:
            want = _pops(r.map_kpa, r.bmep_bar, r.fuel_meter_gps, r.lam_meas,
                         "final" if epa_fit._final(r) else "steady")
            self.assertEqual(r.pops, want)                                # the loader's own populations

    def test_the_judge_passes_a_known_recovery_and_fails_the_out_of_form_seed(self):
        """The driver (run_t0: t0_truths, t0_rows, the ladder, t0_judge) with the
        ladder replaced by its forms up to each truth's own: the judge's arithmetic
        and its controls, on fits whose stopping form is given (the real ladder's
        stopping rule is Ladder's test). The real ladder on these synthetic noisy rows
        is RealT0's, opt-in (it takes minutes)."""
        v, view, rows = dataset()
        truths = epa_fit.t0_truths(NAME, view=view, yield_=rows)
        seen, made = [], {}

        def to_its_form(name, r, *, view, jobs, dtheta):
            seen.append(r)
            if r not in made:                        # the same rows, the same fits (made once)
                fa = epa_fit.fit_form(name, r, view=view, form="A", start=None, jobs=jobs, dtheta=dtheta)
                fits = (fa,)
                if len(seen) % 4 == 3:               # the A+B truth's rows (t0_truths' order)
                    fits += (epa_fit.fit_form(name, r, view=view, form="A+B", start=fa, jobs=jobs, dtheta=dtheta),)
                made[r] = epa_fit.Ladder(engine=name, fits=fits, in_sample={f.form: OK_STAGE for f in fits},
                                         chosen=fits[-1].form, reason="test")
            return made[r]
        orig = epa_fit.ladder
        epa_fit.ladder = to_its_form
        try:
            out = epa_fit.run_t0(NAME, rows, view=view, jobs=JOBS, dtheta=DTH)
            truths2, lads, trows = epa_fit.t0_ladders(NAME, rows, view=view, jobs=JOBS, dtheta=DTH)
        finally:
            epa_fit.ladder = orig
        self.assertEqual(truths2, truths)
        # the ladder ran on each truth's own rows, from its own stream
        for tr, r in zip(truths, seen[:4]):
            self.assertEqual(r, epa_fit.t0_rows(rows, truth=tr, seed=tr.seed, view=view, dtheta=DTH, jobs=JOBS))
        def judge(ls):
            return epa_fit.t0_judge(ls, truths, rows=trows, view=view)
        j = judge(lads)
        self.assertEqual({k: out[k] for k in j}, j)
        self.assertEqual(out["schema"], "epa-t0/1")
        self.assertEqual(out["ladders"]["3"]["forms_fitted"], ["A", "A+B"])
        json.dumps(out, allow_nan=False)
        self.assertTrue(all(s["chi2"]["ok"] for s in j["seeds"]), [s["chi2"] for s in j["seeds"]])
        self.assertFalse(j["out_of_form_seed"]["chi2"]["ok"])
        self.assertTrue(j["out_of_form_detected"])
        self.assertTrue(all(c["ok"] for c in j["cases"].values()), j["cases"])
        self.assertTrue(j["pass"])
        # the controls: a ladder that stops BEFORE its truth's form (the A+B truth at A) fails T0, and so does
        # an out-of-form seed the judge cannot tell from a recovery
        wrong = list(lads)
        wrong[2] = replace(lads[2], chosen="A", fits=lads[2].fits[:1], in_sample={"A": OK_STAGE})
        self.assertFalse(judge(wrong)["pass"])
        self.assertFalse(judge(wrong)["seeds"][2]["reached_expected_form"])
        blind = list(lads)
        blind[3] = lads[1]
        self.assertFalse(judge(blind)["pass"])
        # PLAN.md 5.10's criterion, restored (WP3's second fix of 23 October 2026, on the fit review's must-fix):
        # a form-A truth whose ladder climbed past A fails T0, even on an E4b beyond R but within its own
        # sampling error; within_noise and stopped_beyond_expected_form are reported beside the verdict. Since
        # decision 77 the ladder's own criterion stops at such an A (16 - 2 x 2 <= 15: passes), and the judge
        # still reads the ladder's choice, never re-judging the stage
        self.assertEqual((e4b_stage(16.0, 2.0).passes, e4b_stage(16.0, 2.0).results["E4b"].judgement["outcome"]),
                         (True, "passes"))
        climbed = list(lads)
        climbed[0] = replace(lads[0], chosen="A+B", fits=lads[0].fits + lads[2].fits[1:],
                             in_sample={"A": e4b_stage(16.0, 2.0), "A+B": OK_STAGE})
        jc = judge(climbed)
        self.assertFalse(jc["pass"], jc["seeds"][0])
        s0 = jc["seeds"][0]
        self.assertEqual((s0["judged_at"], s0["stopped_beyond_expected_form"], s0["stopped_at_expected_form"],
                          s0["within_noise"]["ok"], s0["chi2"]["ok"], s0["ok"]), ("A", True, False, True, True, False))
        # an empty chi-square (no covariance, so no parameter tested) is never a detection and fails T0, on the
        # out-of-form seed and on an in-form one (WP3's second fix of 23 October 2026, on the test review's
        # must-fix: at dof 0 the NaN quantiles made "not ok" read as detected)

        def no_cov(f):
            st = dict(f.stages)
            for k in ("S2", "S4"):
                st[k] = replace(st[k], report=dict(st[k].report, covariance=None))
            return replace(f, stages=st)
        blind_cov = list(lads)
        blind_cov[3] = replace(lads[3], fits=tuple(no_cov(f) for f in lads[3].fits))
        jb = judge(blind_cov)
        self.assertEqual((jb["pass"], jb["out_of_form_detected"], jb["chi2_empty_seeds"]), (False, False, [4]))
        self.assertEqual((jb["out_of_form_seed"]["chi2"]["dof"], jb["out_of_form_seed"]["chi2"]["empty"]), (0, True))
        json.dumps(jb, allow_nan=False)
        empty0 = list(lads)
        empty0[0] = replace(lads[0], fits=tuple(no_cov(f) for f in lads[0].fits))
        je = judge(empty0)
        self.assertEqual((je["pass"], je["seeds"][0]["ok"], je["chi2_empty_seeds"]), (False, False, [1]))
        # D1's and D3's cases can fail (the review's finding: both could not): a stand-in S3c that reads the
        # lines without holds, and a fitted ECU whose spark_max clips the rows
        fit = lads[0].fits[0]
        self.assertTrue(epa_fit.t0_cases(NAME, fit, truths[0], rows=trows[0], view=view)["d1_envelope"]["ok"])
        real_s3c = epa_fit.s3c_envelope

        def leaky_s3c(rows_, **kw):                 # s3c_envelope's keywords (plant, view, conventions)
            st = real_s3c(rows_, **kw)
            no = set(st.report["lines_without_holds"])
            mp = [r.map_kpa for r in rows_ if r.line in no]
            pr = list(st.values["envelope_pr"])
            pr[1] = max(mp) / float(st.report["inlet_sea_kpa"])
            return replace(st, values=dict(st.values, envelope_pr=pr))
        leaky = leaky_s3c(epa_fit.cal_rows(trows[0]), plant=epa_fit._base_plant(NAME, "A"), view=view,
                          conventions=epa_stats.NOMINAL)
        fake = replace(fit, stages=dict(fit.stages, S3c=leaky),
                       values=dict(fit.values, boost_ceiling={k: leaky.values[k] for k in fit.values["boost_ceiling"]}))
        with mock.patch.object(epa_fit, "s3c_envelope", leaky_s3c):
            self.assertFalse(epa_fit.t0_cases(NAME, fake, truths[0], rows=trows[0], view=view)["d1_envelope"]["ok"])
        clip = replace(fit, values=dict(fit.values, ecu=dict(fit.values["ecu"], spark_max=fit.values["ecu"]["spark_min"] + 1.0)))
        self.assertTrue(epa_fit.t0_cases(NAME, fit, truths[0], rows=trows[0], view=view)["d3_spark_min"]["ok"])
        self.assertFalse(epa_fit.t0_cases(NAME, clip, truths[0], rows=trows[0], view=view)["d3_spark_min"]["ok"])
        # S1's recovery: the noise-free TIP gives the truth's law back to the hinge grid; the control, a ratio
        # 1 % off, does not
        self.assertTrue(epa_fit.t0_cases(NAME, fit, truths[0], rows=trows[0], view=view)["s1_law"]["ok"])
        off = replace(fit, values=dict(fit.values, cycle=dict(fit.values["cycle"],
                                                                exh_bp_ratio=fit.values["cycle"]["exh_bp_ratio"] * 1.01)))
        self.assertFalse(epa_fit.t0_cases(NAME, off, truths[0], rows=trows[0], view=view)["s1_law"]["ok"])


# THE REAL T0 ON SYNTHETIC ROWS (WP3's second fix of 23 October 2026, on the fit and test reviews' finding that
# no test ran T0's real ladder before Run 1): opt-in, since it fits every form of four truths. Set
# EPA_FIT_SLOW_T0=<jobs>; EPA_FIT_SLOW_T0_OUT=<path> also writes the whole record there (synthetic numbers: no
# figure of it is a figure of the project).
SLOW_T0 = "EPA_FIT_SLOW_T0"
SLOW_T0_OUT = "EPA_FIT_SLOW_T0_OUT"


def t0_summary(out):
    """Each seed's verdict from a run_t0 record, compact: the truth's form, the form its ladder chose, the forms
    fitted, the chi-square with its 99 % interval, and each fitted form's in-sample outcomes (decision 77)."""
    seeds = {}
    for s_ in out["seeds"] + ([out["out_of_form_seed"]] if out["out_of_form_seed"] else []):
        c2 = s_["chi2"]
        lad = out["ladders"][str(s_["seed"])]
        seeds[str(s_["seed"])] = {
            "truth_form": s_["expected_form"], "chosen": s_["ladder_stops_at"], "judged_at": s_["judged_at"],
            "forms_fitted": lad["forms_fitted"], "ok": s_.get("ok"),
            "chi2": {k: c2[k] for k in ("value", "dof", "quantile_99_lo", "quantile_99_hi", "ok", "empty")},
            "in_sample": {f: {r: v["outcome"] for r, v in rec.items()} for f, rec in lad["in_sample"].items()}}
    return {"pass": out["pass"], "out_of_form_detected": out["out_of_form_detected"],
            "chi2_empty_seeds": out["chi2_empty_seeds"], "cases": {k: c["ok"] for k, c in out["cases"].items()},
            "seeds": seeds}


@unittest.skipUnless(os.environ.get(SLOW_T0, "").isdigit(), f"set {SLOW_T0}=<jobs> to run T0's real ladder on the "
                     "synthetic rows at the production crank step (about 10 minutes at 12 jobs)")
class RealT0(fx.Guarded):
    """epa_fit.run_t0 itself -- the four truths, t0_rows, the real per-engine ladder with its in-sample stage
    at every form, the judge -- on this file's synthetic rows at the plant's own crank step (DTHETA_DEG):
    the record is complete and JSON, every seed's verdict is PLAN.md 5.10's criterion recomputed from the
    record itself, every ladder moved on only on an in-sample "fails" (decision 77, read off the record's
    in-sample outcomes), and T0's pass is theirs with the out-of-form detection and the cases. It prints
    each seed's verdict (t0_summary) and does not assert that T0 passes: under the literal |E_cal| <= R the
    fit review's run (23 October 2026, dtheta 0.25, 8 jobs, 334 s) and a second (12 jobs, 587 s) saw seed 1,
    a form-A truth, climb to A+B+C+D on an in-sample E4b that sampling error alone pushed past R; decision
    77 is the team's answer, in the ladder's criterion, and this test reports what T0 does under it."""

    def test_run_t0_end_to_end(self):
        jobs = int(os.environ[SLOW_T0])
        v, view, rows = dataset()
        out = epa_fit.run_t0(NAME, rows, view=view, jobs=jobs, dtheta=epa_fit.DTHETA_DEG)
        json.dumps(out, allow_nan=False)
        if os.environ.get(SLOW_T0_OUT):
            with open(os.environ[SLOW_T0_OUT], "w", encoding="utf-8") as fh:
                json.dump(out, fh, indent=1, allow_nan=False)
        print("\nRealT0 (synthetic rows, dtheta %r, %d jobs): %s"
              % (epa_fit.DTHETA_DEG, jobs, json.dumps(t0_summary(out), indent=1)))
        self.assertEqual(out["schema"], "epa-t0/1")
        self.assertEqual(sorted(out["ladders"]), ["1", "2", "3", "4"])
        self.assertEqual([s["seed"] for s in out["seeds"]], [1, 2, 3])
        self.assertEqual(out["stop_rule"]["ladder_criterion"], epa_stats.IN_SAMPLE_CRITERION)
        for s_ in out["seeds"]:
            self.assertEqual(s_["ok"], s_["stopped_at_expected_form"] and not s_["chi2"]["empty"] and s_["chi2"]["ok"])
            self.assertEqual(s_["ladder_stops_at"], out["ladders"][str(s_["seed"])]["chosen"])
        # decision 77 from the record: a form is followed by another only if one of its statistics fails, and the
        # chosen form fails none unless it is A+B+C+D after every form failed
        for seed, lad in out["ladders"].items():
            fitted = lad["forms_fitted"]
            self.assertEqual(list(lad["in_sample"]), fitted, seed)
            for f in fitted:
                outcomes = {r: rec["outcome"] for r, rec in lad["in_sample"][f].items()}
                self.assertTrue(set(outcomes.values()) <= {"fails", "passes", "neither", None}, outcomes)
                fails = any(o == "fails" for o in outcomes.values())
                if f != fitted[-1]:
                    self.assertTrue(fails, (seed, f, outcomes))
                elif lad["chosen"] == f and not (f == engines.CYCLE_FORMS[-1] and fails):
                    self.assertFalse(fails, (seed, f, outcomes))
        want = (all(s_["ok"] for s_ in out["seeds"]) and out["out_of_form_detected"] and not out["chi2_empty_seeds"]
                and all(c["ok"] for c in out["cases"].values()))
        self.assertEqual(out["pass"], want)


class S4Polish(fx.Guarded):
    def test_the_polish_is_declared_kept_and_converged(self):
        """TOLERANCES["S4_polish"] on this file's form-A fit: the polish starts from the start that stopped
        lowest, at the declared tolerances, lowers (or keeps) its cost, ends on a tolerance and not on the
        evaluation budget (status other than 0), and the frozen point is the polished one, its departure
        recorded. Its measurement at the production step is the fit review's (TOLERANCES' note)."""
        st = form_a_fit().stages["S4"]
        pol = st.report["polish"]
        self.assertEqual(pol["tolerances"], epa_fit.TOLERANCES["S4_polish"])
        self.assertEqual(pol["from"], st.report["best_start"])
        self.assertLessEqual(pol["cost_after"], pol["cost_before"])
        self.assertNotEqual(pol["status"], 0)
        self.assertTrue(pol["kept"])
        self.assertEqual(st.convergence.cost, pol["cost_after"])
        self.assertGreaterEqual(pol["departure_norm_scale_units"], abs(pol["departure_along_weakest_scale_units"]))
        settings = epa_fit.fit_settings(NAME, view=dataset()[1], form="A", dtheta=DTH, jobs=JOBS)
        self.assertEqual(settings["ftol"]["S4_polish"], epa_fit.TOLERANCES["S4_polish"]["ftol"])
        self.assertIn("S2_deviation_from_plan_5_4", settings["starts"])


class Tolerances(fx.Guarded):
    def test_the_cycles_roughness_and_s4s_tolerances(self):
        """TOLERANCES' measurement, re-run on a smaller construction (mistake 22): the
        B58's plant at 12 synthetic points, targets from it with four constants moved 5
        %, S4's cost along burn_base at dtheta 0.25. Over +-1e-4 of the scale it is
        smooth; over +-0.05 of the scale it departs from a degree-6 polynomial by more
        than S4's ftol and S2's. Until WP3's second fix of 23 October 2026 S4's ftol sat
        ABOVE that roughness (2e-3), on the claim that a tighter one would only chase
        it; the fit review measured that it stopped the starts short of the minimum, so
        S4's tolerances now sit below the roughness and its five starts converge, their
        spread along the weakest direction reported (TOLERANCES' note)."""
        b = engines.get("b58")
        e, c = b.engine, b.engine.cycle
        pts = tuple((rpm, mp, 315.0, 365.0, 10.0 if mp < 150 else 2.0, 1.0)
                    for rpm in (1500.0, 3000.0, 4500.0) for mp in (40.0, 100.0, 160.0, 220.0))

        def outs(eng):
            res = epa_fit._grid_results(eng, pts, 0.25, eng)
            return (np.array([r.torque_nm for r in res]), np.array([r.egt_c for r in res]),
                    np.array([r.mdot_fuel_gps for r in res]))
        TE, TITE, FE = outs(replace(e, cycle=replace(c, burn_base=c.burn_base * 1.05, delay_base=c.delay_base * 0.95,
                                                     fmep_0=c.fmep_0 * 1.05, ua_port=c.ua_port * 1.05)))

        def cost(bb):
            T, TIT, F = outs(replace(e, cycle=replace(c, burn_base=float(bb))))
            r = np.concatenate([(T * FE / (TE * F) - 1.0) / 0.019, (TIT - TITE) / 10.0])
            return 0.5 * float(np.dot(r, r))
        s = epa_fit.SCALES["burn_base"]
        c0 = cost(c.burn_base)

        def departure(half, n, deg):
            ts = np.linspace(-half, half, n)
            cs = np.array([cost(c.burn_base + t * s) for t in ts])
            return float(np.max(np.abs(cs - np.polyval(np.polyfit(ts, cs, deg), ts))) / c0)
        smooth = departure(1e-4, 9, 2)
        rough = departure(0.05, 41, 6)
        self.assertLess(smooth, 1e-10)
        self.assertGreater(rough, epa_fit.TOLERANCES["S4"]["ftol"])
        self.assertGreater(rough, epa_fit.TOLERANCES["S2"]["ftol"])
        self.assertLessEqual(epa_fit.TOLERANCES["S4_polish"]["ftol"], epa_fit.TOLERANCES["S4"]["ftol"])


class S0(fx.Guarded):
    def test_the_checks_and_bounds_on_the_yield(self):
        v, view, rows = dataset()
        sen = replace(rows[10], spark_btdc=None, spark_sentinel=True)
        lm = replace(rows[11], lam_meas=None, lambda_missing=True)
        rr = rows[:10] + (sen, lm) + rows[12:]
        st = epa_fit.s0(rr, view=view)
        rep = st.report
        self.assertEqual(rep["spark_sentinel"]["total"], 1)
        self.assertEqual(rep["spark_sentinel"]["keys"], [list(epa_fit._key(sen))])
        self.assertIn("S0_fired_sentinel_rows", st.flags)                 # declared, never a stop
        self.assertEqual(rep["lambda_missing"]["keys"], [list(epa_fit._key(lm))])
        self.assertEqual(rep["bounds"]["lowest_final_map_kpa"], FINAL_MAP[0])
        self.assertEqual(rep["bounds"]["s3b_gate_lo_kpa"], min(FINAL_MAP[0], epa_fit.S3B_GATE_DESIGN_KPA))
        e = epa_fit.depth_edges(rr, lam_floor=view.lam_floor, conventions=epa_stats.NOMINAL)
        self.assertEqual(rep["bounds"]["s3b_depth_upper"], e["upper"])
        self.assertEqual(rep["tip_below_barometer"]["below"], 0)
        self.assertEqual(rep["cam"]["direction"], "ret")
        # the rows at the printed hot floor (the synthetic view's is the first Final MAP): counted, flagged, a
        # declared outcome; the control, a floor no row sits within 0.005 kPa of, lists none
        at = [r for r in rr if abs(r.map_kpa - view.hot_map_floor_kpa) <= 0.005]
        self.assertTrue(at)
        self.assertEqual(rep["hot_floor_rounding"]["rows_within"], len(at))
        self.assertIn("S0_rows_at_the_rounded_hot_floor", st.flags)
        off = epa_fit.s0(rows, view=replace(view, hot_map_floor_kpa=view.hot_map_floor_kpa + 0.37))
        self.assertEqual(off.report["hot_floor_rounding"]["rows_within"], 0)
        self.assertIn("all-row", rep["bounds"]["s3b_depth_upper_invariant_source"])
        self.assertFalse(rep["bounds"]["s3b_invariant_edge_active"])
        # the control: none of either, no flag
        st0 = epa_fit.s0(rows, view=view)
        self.assertNotIn("S0_fired_sentinel_rows", st0.flags)
        self.assertEqual(st0.report["spark_sentinel"]["total"], 0)

    def test_c1s_depth_bound_reads_every_final_row_with_a_lambda(self):
        """Amendment C1's bound over the calibration Final rows that publish a lambda, a sentinel's included
        (its spark says nothing of its lambda; WP3's fix of 23 October 2026); the depth itself is still fitted
        on no sentinel row. The control: the same deep row with its lambda missing does not move the bound."""
        v, view, rows = dataset()
        i = next(k for k, r in enumerate(rows) if epa_fit._final(r))
        base = epa_fit.depth_edges(rows, lam_floor=view.lam_floor, conventions=epa_stats.NOMINAL)["c1"]
        deep = replace(rows[i], lam_meas=0.70, spark_btdc=None, spark_sentinel=True)
        got = epa_fit.depth_edges(rows[:i] + (deep,) + rows[i + 1:], lam_floor=view.lam_floor,
                                  conventions=epa_stats.NOMINAL)["c1"]
        self.assertAlmostEqual(got, 1.0 - (0.70 - 0.01), places=12)
        self.assertGreater(got, base)
        gone = replace(deep, lam_meas=None, lambda_missing=True)
        self.assertEqual(epa_fit.depth_edges(rows[:i] + (gone,) + rows[i + 1:], lam_floor=view.lam_floor,
                                             conventions=epa_stats.NOMINAL)["c1"], base)

    def test_the_end_lines_are_calibration_lines(self):
        """_rpm_ends asserts the end lines are never held out (amendment C13's claim), not assumes it: a view
        whose top line is held out stops as a coding defect; the control, the synthetic view, gives its ends."""
        v, view, rows = dataset()
        self.assertEqual(epa_fit._rpm_ends(view), (1500.0, 4500.0))
        with self.assertRaises(epa_fit.FitDefect):
            epa_fit._rpm_ends(replace(view, held_out_lines=view.held_out_lines + (LINES[-1],)))

    def test_sentinel_rows_and_rows_without_lambda_enter_no_fit(self):
        v, view, rows = dataset()
        sen = replace(rows[10], spark_btdc=None, spark_sentinel=True)
        st = epa_fit.s3a_spark(rows[:10] + (sen,) + rows[11:], plant=epa_fit._base_plant(NAME, "A"), view=view)
        self.assertIn(list(epa_fit._key(sen)), st.rows_excluded["sentinel"])
        s1 = epa_fit.s1_backpressure(rows[:10] + (sen,) + rows[11:], view=view)
        fired = sum(1 for r in rows if r.pops.fired)
        self.assertTrue(rows[10].pops.fired)
        self.assertEqual(s1.rows_used, fired - 1)
        self.assertIn(list(epa_fit._key(sen)), s1.rows_excluded["sentinel"])
        lm = replace(rows[12], lam_meas=None, lambda_missing=True)
        s3b = epa_fit.s3b_lambda(rows[:12] + (lm,) + rows[13:], plant=epa_fit._base_plant(NAME, "A"), view=view,
                                 censoring=epa_stats.censoring([r for r in rows if epa_fit._final(r)]),
                                 lam_floor=view.lam_floor, conventions=epa_stats.NOMINAL)
        self.assertIn(list(epa_fit._key(lm)), s3b.rows_excluded["no_lambda"])


def _record_open(i):
    epa_fit.WORKER_OPENED.append(f"probe/{i}")
    return i * i


class Pool(fx.Guarded):
    def test_results_and_worker_opens_come_back_in_submission_order(self):
        del epa_fit.POOL_OPENED[:]
        out = epa_fit.ordered_map(_record_open, list(range(40)), jobs=4, initializer=None)
        self.assertEqual(out, [i * i for i in range(40)])
        self.assertEqual(epa_fit.POOL_OPENED, [f"probe/{i}" for i in range(40)])
        self.assertEqual(epa_fit.ordered_map(_record_open, [3], jobs=1, initializer=None), [9])
        with self.assertRaises(ValueError):
            epa_fit.ordered_map(_record_open, [1], jobs=0, initializer=None)
        del epa_fit.POOL_OPENED[:]


class Scan(fx.Guarded):
    """WP3_INTERFACES.md 3.1-3.2 for this module (test_epa_rows.Scans checks every
    module): epa_fit imports from the project only epa_rows, epa_stats, engines,
    plant and engine_env; never validate_epa, thresholds.split or thresholds.contract;
    opens no file; names no table."""
    ALLOWED = {"epa_rows", "epa_stats", "engines", "plant", "engine_env"}

    @staticmethod
    def problems(src):
        import ast
        tree = ast.parse(src)
        project = {os.path.splitext(f)[0] for f in os.listdir(HERE) if f.endswith(".py")} | {"thresholds"}
        out = []
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                mods = [node.module]
            for m in mods:
                if m.split(".")[0] in project and m not in Scan.ALLOWED:
                    out.append(f"import {m}")
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "open":
                out.append("open(")
            if isinstance(node, ast.Constant) and isinstance(node.value, str) and (
                    ("epa_" + "steady") in node.value or ("epa_" + "highload") in node.value):
                out.append("a table name")
        return out

    def test_every_class_here_runs_inside_the_real_data_guard(self):
        """WP3_INTERFACES.md 9.1: every class of this file is test_epa_fixtures.Guarded,
        so an open of a real EPA table, logs/** or the contract fails the test. The
        control opens a name under logs/ that no file has (nothing is read: the hook
        refuses before the open) and must be caught."""
        mod = sys.modules[__name__]
        classes = [c for c in vars(mod).values() if isinstance(c, type) and issubclass(c, unittest.TestCase)
                   and c.__module__ == __name__]
        self.assertGreater(len(classes), 15)
        self.assertEqual([c.__name__ for c in classes if not issubclass(c, fx.Guarded)], [])
        with self.assertRaises(AssertionError):
            with fx.forbid_real_data():
                try:
                    open(os.path.join(HERE, "logs", "no_such_file.txt"), encoding="utf-8")
                except PermissionError:
                    pass

    def test_the_module_keeps_its_rules_and_the_scan_can_fail(self):
        with open(os.path.join(HERE, "epa_fit.py"), encoding="utf-8") as fh:
            self.assertEqual(self.problems(fh.read()), [])
        bad = ("import thresholds.split\nimport validate_epa\nx = open('a')\n"
               f"t = '{'epa_' + 'steady'}.csv'\n")
        self.assertEqual(len(self.problems(bad)), 4)


if __name__ == "__main__":
    unittest.main()
