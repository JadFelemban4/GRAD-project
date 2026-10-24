"""test_epa_stats.py -- epa_stats on synthetic rows, with hand answers (build step 2, WP3; 23 October 2026).

Every statistic of the contract's sections 3-5 that epa_stats defines (results/ENGINE_THRESHOLDS.md and
.json version 5, whose sections 3-5 are version 4's; docs/build_step_2/WP3_INTERFACES.md 5.2 and 9.4) is
run here on rows this file makes: synthetic epa_rows records, RowEvals typed by hand, and a closed-form
toy model that satisfies the model protocol (5.2.2). No test opens an EPA table, the real contract, a D3
file or anything under logs/: an audit hook installed for the whole module refuses those opens, and one
test shows it able to refuse (mistake 12). The contract's numbers used here (each R, G = 980.27 K, the
B58's head-start-pair tables of section 1.5) are typed from the contract's own text, B58 measurements and
rules, never an EPA value.

Each test proves its point with a control that must fail or move (mistake 12). Run alone:
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B test_epa_stats.py
"""
import dataclasses
import json
import math
import os
import re
import sys
import types
import unittest
from dataclasses import replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import numpy as np  # noqa: E402

import engine_env as E  # noqa: E402
import engines  # noqa: E402
import epa_rows  # noqa: E402
import epa_stats as S  # noqa: E402
from thresholds import common as C  # noqa: E402
from thresholds import contract as K  # noqa: E402
from thresholds import split as SP  # noqa: E402  (its constants and coverage() only: no table is read)

# ---------------------------------------------------------------------------------------------
# No real data (WP3_INTERFACES.md 9.1, forbid_real_data's rule, kept here so this file stands alone)
# ---------------------------------------------------------------------------------------------
_GUARD = {"on": False}
# The paths are built from parts and from this file's own folder: WP3_INTERFACES.md 3.2 confines the names of the
# contract's files and of the engines' folder (N1, N3) to the loader, the validation and the freeze, and the
# guard only refuses opens of them.
_CONTRACT = os.path.join(HERE, "results", "ENGINE_THRESHOLDS")
_FORBIDDEN_PREFIXES = tuple(os.path.normcase(os.path.abspath(p)) for p in (
    os.path.join(HERE, "logs"), C.DATA_FOLDER, _CONTRACT + ".json", _CONTRACT + ".md",
    os.path.join(_CONTRACT, "split.json")))
_EPA_FOLDER = os.path.normcase(os.path.abspath(os.path.join(HERE, "data", "engines")))


def _forbidden(path):
    try:
        p = os.path.normcase(os.path.abspath(os.fsdecode(path)))
    except (TypeError, ValueError):
        return False
    if any(p == f or p.startswith(f + os.sep) for f in _FORBIDDEN_PREFIXES):
        return True
    return p.startswith(_EPA_FOLDER + os.sep) and os.path.basename(p).startswith("epa_")


def _hook(event, args):
    if _GUARD["on"] and event == "open" and args and isinstance(args[0], (str, bytes, os.PathLike)):
        if _forbidden(args[0]):
            # recorded as well as refused: an open the code under test catches still fails the module at
            # tearDownModule (forbid_real_data's rule; WP3's fix of 23 October 2026, the test review's finding)
            _GUARD["hits"].append(os.path.basename(os.fsdecode(args[0])))
            raise PermissionError(f"test_epa_stats opens no real EPA data: {args[0]}")


_GUARD["hits"] = []
sys.addaudithook(_hook)


def setUpModule():
    _GUARD["on"] = True


def tearDownModule():
    _GUARD["on"] = False
    if _GUARD["hits"]:
        raise AssertionError(f"test_epa_stats opened real data {len(_GUARD['hits'])} time(s): "
                             + ", ".join(sorted(set(_GUARD["hits"]))))


# ---------------------------------------------------------------------------------------------
# Synthetic records
# ---------------------------------------------------------------------------------------------
POP_KEYS = [f.name for f in dataclasses.fields(epa_rows.Populations)]


def pops(*true):
    for t in true:
        assert t in POP_KEYS, t
    return epa_rows.Populations(**{k: (k in true) for k in POP_KEYS})


FUEL = epa_rows.TableFuel(ftag="F1", fuel_report="synthetic", lhv_j_per_kg=42.9e6, afr_st=14.56)


def prow(cls=epa_rows.SteadyRow, **kw):
    """A synthetic steady or Final row with every field set (origin "fixture")."""
    base = dict(engine="synth", table="t_steady", source_row=6, test_cell="cell", fuel_report="synthetic",
                origin="fixture", line="2000", nominal_rpm=2000, hold=None, speed_rpm=2000.0, map_kpa=120.0,
                imt_k=310.0, ect_k=360.0, oil_k=365.0, spark_btdc=10.0, spark_sentinel=False, lam_meas=1.0,
                lam_banks=None, lambda_missing=False, lam_ref=1.0, torque_nm=200.0, bmep_bar=10.0,
                fuel_meter_gps=5.0, meter_missing=False, injector_fuel_gps=5.0, tit_c=800.0, tip_kpa=130.0,
                baro_kpa=98.0, cell_temp_k=298.0, cam_cad=None, cam_channel=None, cam_missing=True,
                exhaust_cam_cad=None, valve_overlap_cad=None, atkinson_ratio=None, eff_compression_stroke_mm=None,
                eff_expansion_stroke_mm=None, eff_compression_ratio=None, eff_expansion_ratio=None,
                pops=pops("fired", "fired_meter"))
    base.update(kw)
    return cls(**base)


def held_final(**kw):
    kw.setdefault("hold", kw.get("source_row", 6))
    kw.setdefault("table", "t_final")
    return prow(epa_rows.HeldOutRow, kind="final", **kw)


R_TABLE = {"E1a": (1.9, "% of the measured torque"), "E2a": (4.0, "% of the measured flow"), "E3a": (10.0, "K"),
           "E4a": (10.0, "K"), "L0": (10.0, "K of housing"), "D1": (16.6, "% of the measured flow"),
           "E4b": (16.6, "% of the lever's effect"), "L1": (9.9, "K of housing"),
           "E8": (16.6, "% of the head-start pair"), "E1b": (None, "%"), "E1i": (None, "%"), "E2b": (None, "%"),
           "E3b": (None, "K"), "E5": (None, "%")}
# The B58's head-start-pair tables under K3 (contract section 1.5; JSON ecu_strategy_b58), as printed
K3_LAM = [(-0.1, -0.6486096287580572), (-0.05, -0.3609955520349323), (-0.02, -0.16259325655562773),
          (-0.01, -0.08878863760686961), (-0.005, -0.05117178820446244), (0.0, 0.0), (0.005, -0.09695938787167324),
          (0.01, -0.19368855665269336), (0.02, -0.4243894274478406), (0.05, -0.8160228123309472)]
K3_SPARK = [(-3.0, 0.19735627221739116), (-1.5, 0.08396136769978235), (-0.75, 0.031637593225743554), (0.0, 0.0),
            (0.75, -0.05811986727917795), (1.5, -0.10153883005480036)]
G_K = 980.27


def view(**kw):
    """A synthetic calibration view: the attributes epa_stats reads (WP3_INTERFACES.md 5.1 CalibrationView)."""
    base = dict(engine="synth", R=R_TABLE, b_points=0.905, mei_points=5.43,
                propagation_b58={"G_gas_over_42C_k": G_K, "used": {"flow_pct_per_pct_torque": 1.353}},
                ecu_strategy_b58={"k3_pair_change_vs_lambda": K3_LAM, "k3_pair_change_vs_spark": K3_SPARK,
                                  "worth_b": {"lambda_rich": {"shift": -0.0206}}},
                e8_min_rows=3, fuel_by_table={"t_steady": FUEL, "t_final": FUEL, "t_initial": FUEL},
                lambda_ref={"t_steady": 1.0, "t_final": 1.0, "t_initial": 1.0},
                coverage_calibration_fired={"100-120 kPa": {}, "120-140 kPa": {}},
                coverage_calibration_hot={"120-140 kPa": {}})
    base.update(kw)
    return types.SimpleNamespace(**base)


V = view()
_X = S.RowInputs(engine="synth", table="t_steady", source_row=6, rpm=2000.0, map_kpa=120.0, iat_k=310.0,
                 ect_k=360.0, spark_btdc=10.0, lam=1.0, lam_source="snapped", spark_source="published", fuel=FUEL)


def mo(torque=200.0, fuel=5.0, egt=800.0):
    return S.ModelOut(torque_nm=float(torque), fuel_gps=float(fuel), air_gps=float(fuel) * 14.56, egt_c=float(egt),
                      knock_integral=0.0, eta_v=0.9)


def ev(n, line, pp, *, kind="steady", T_E=200.0, T_m=None, meter=5.0, F_m=None, tit=800.0, egt=None,
       lam=1.0, spark=10.0, map_kpa=120.0, d1=None, ecu=None, lam1=None, flags=(), dtheta=0.25, shift=None,
       hold=None, table=None):
    """A RowEval typed by hand: the model's out at EPA's MAP from T_m, F_m, egt (defaults: EPA's own)."""
    out = mo(T_E if T_m is None else T_m, meter if F_m is None else F_m, tit if egt is None else egt)
    meas = S.Measured(torque_nm=float(T_E), meter_gps=None if meter is None else float(meter), tit_c=float(tit),
                      lam_cellref=None if lam is None else float(lam),
                      spark_btdc=None if spark is None else float(spark), map_kpa=float(map_kpa), bmep_bar=10.0)
    tab = table or {"steady": "t_steady", "final": "t_final", "initial": "t_initial"}[kind]
    return S.RowEval(engine="synth", table=tab, source_row=int(n), line=line, kind=kind,
                     hold=hold if hold is not None else (n if kind != "steady" else None),
                     pops=None if kind == "initial" else pp, origin="fixture", inputs=replace(_X, source_row=int(n)),
                     measured=meas, out=out, lam1=lam1, d1=d1, ecu=ecu, flags=frozenset(flags), shift=shift,
                     dtheta=float(dtheta))


def d1p(delta, e_d, *, meter=5.0, tit=800.0, bracketed=True):
    """A D1 point whose fuel gives delta_D and whose egt gives e_D against the row's meter and TIT."""
    return S.D1Point(map_kpa=130.0, bracketed=bracketed, bound_kpa=None if bracketed else 400.0, spark_btdc=10.0,
                     cam_deg=None, out=mo(200.0, meter * (1.0 + delta), tit + e_d), delta_d=delta, e_d=e_d,
                     n_cycles=54)


class Toy:
    """A closed-form model satisfying the protocol (WP3_INTERFACES.md 5.2.2), linear where a hand answer needs it:
    torque = 1.5 MAP + 0.8 spark + 0.01 (rpm - 2000) - 20 + bias (dtheta - 0.25) MAP; fuel = 0.002 MAP rpm/1000/lam;
    egt = 400 + 2 MAP - 3 spark + 500 (lam - 1) + 0.5 (iat - 300); the ECU's spark 30 - 0.1 MAP - 0.2 (iat - 300),
    its lambda 1 below 150 kPa and 1 - 0.002 (MAP - 150) above."""

    def __init__(self, bias=0.0):
        self.bias = bias

    def cycle(self, x, *, dtheta):
        t = 1.5 * x.map_kpa + 0.8 * x.spark_btdc + 0.01 * (x.rpm - 2000.0) - 20.0 + self.bias * (dtheta - 0.25) * x.map_kpa
        f = 0.002 * x.map_kpa * x.rpm / 1000.0 / x.lam
        egt = 400.0 + 2.0 * x.map_kpa - 3.0 * x.spark_btdc + 500.0 * (x.lam - 1.0) + 0.5 * (x.iat_k - 300.0)
        return S.ModelOut(torque_nm=t, fuel_gps=f, air_gps=f * 14.56 * x.lam, egt_c=egt, knock_integral=0.0, eta_v=0.9)

    def ecu_at(self, rpm, map_kpa, iat_k, ect_k):
        lam = 1.0 if map_kpa <= 150.0 else 1.0 - 0.002 * (map_kpa - 150.0)
        return S.EcuOut(spark_btdc=30.0 - 0.1 * map_kpa - 0.2 * (iat_k - 300.0), lam=lam, cam_deg=None)

    def base_spark(self, rpm, map_kpa):
        return 30.0 - 0.1 * map_kpa

    def cam(self, rpm, map_kpa):
        return None


class HumpToy(Toy):
    """Torque with a hump in MAP, which crosses a target twice: D1 must take the first bracket from 20 kPa up."""

    def cycle(self, x, *, dtheta):
        out = super().cycle(x, dtheta=dtheta)
        return replace(out, torque_nm=300.0 - (x.map_kpa - 200.0) ** 2 / 100.0)


D_TERMS = dict(S.U_D, meter=S.UD(0.01, None, "random", "synthetic", "test", True),
               torque=S.UD(0.5, None, "random", "synthetic", "test", True))


def u_inputs(evals, *, effect, d_terms=D_TERMS, fine=None, common_lam=None, terms=S.U_INPUT):
    """UncertaintyInputs built by hand: each row shifted by +-u_j with its torque moved by sign*effect(e, ch) and
    its egt by the same (so a hand answer can be written), the 0.125 deg set from `fine` (key -> RowEval) or the
    rows themselves at 0.125 with nothing moved."""
    shifted = {}
    for e in evals:
        for ch in S.INPUT_CHANNELS:
            for sg in (+1, -1):
                d = sg * effect(e, ch)
                out = replace(e.out, torque_nm=e.out.torque_nm + d, egt_c=e.out.egt_c + d)
                shifted[(ch, sg, S._key(e))] = replace(e, out=out, shift=S.input_shift(ch, sg, terms[ch]))
    if fine is None:
        fine = {S._key(e): replace(e, dtheta=0.125) for e in evals}
    return S.UncertaintyInputs(evals_0125=fine, shifted=shifted, common_lam=common_lam, input_terms=terms,
                               d_terms=d_terms)


# =============================================================================================
class NoRealData(unittest.TestCase):
    def test_the_guard_refuses_the_real_contract_and_a_real_table(self):
        """Control (mistake 12): the module's audit hook refuses an open of the real contract and of a real
        EPA table's path (the file need not exist: the open is refused before the OS is asked)."""
        for p in (_CONTRACT + ".json", os.path.join(_EPA_FOLDER, "mazda_25t", "epa_" + "steady.csv"),
                  os.path.join(HERE, "logs", "x.txt")):
            with self.assertRaises(PermissionError):
                open(p, "rb").close()
        # and an ordinary file is allowed: the guard is not refusing everything
        open(os.path.abspath(__file__), "rb").close()
        # the three refusals were recorded too (an open the code catches still fails the module), and are this
        # control's own: taken off the record, so tearDownModule judges every other test's opens
        self.assertEqual(len(_GUARD["hits"]), 3)
        del _GUARD["hits"][:]


class Constants(unittest.TestCase):
    def test_the_split_constants_are_the_generators(self):
        """epa_stats takes the split's constants through epa_rows (amendment C2): they are thresholds/split.py's."""
        for name in ("LAM_BAND", "LAM_ENR", "TOL", "MIN_CLUSTERS", "MAP_SPLIT", "FIRED_BMEP", "MAP_BAND"):
            self.assertEqual(getattr(S, name), getattr(SP, name), name)

    def test_the_band_key_is_split_coverages(self):
        """map_band_key names a MAP's coverage band exactly as split.coverage() does, on a grid that crosses band
        edges; control: the keys of 39.999 and 40.0 differ in both."""
        for m in [19.999, 20.0, 39.999, 40.0, 99.5, 100.0, 109.56, 140.0, 228.7, 399.99]:
            cov = SP.coverage([{"intake_manifold_press_kpa_abs": repr(m), "speed_rpm": "2000",
                                "intake_manifold_temp_c": "40", "coolant_temp_c": "90"}])
            self.assertEqual(list(cov), [S.map_band_key(m)], m)
        self.assertNotEqual(S.map_band_key(39.999), S.map_band_key(40.0))

    def test_round_down_is_the_contracts(self):
        """The rounding of a tightened R is the contract's rdown (thresholds/contract.py) on a grid; control: a
        round-half-up would differ at 9.99."""
        for x in np.linspace(0.0, 30.0, 3001):
            self.assertEqual(S._round_down(float(x)), K.rdown(float(x)), x)
        self.assertEqual(S._round_down(9.99), 9.9)
        self.assertNotEqual(round(9.99, 1), 9.9)

    def test_d1_prescan_is_the_contracts(self):
        """20-400 kPa every 10 kPa: 39 points (decision 57)."""
        self.assertEqual(len(S.D1_SCAN_KPA), 39)
        self.assertEqual((S.D1_SCAN_KPA[0], S.D1_SCAN_KPA[-1]), (20.0, 400.0))
        self.assertEqual(S.D1_BISECT_KPA, 1e-3)


class LambdaAndInputs(unittest.TestCase):
    def test_the_snap_and_its_edge(self):
        """Within 0.02 of lambda_ref (and the split's 1e-9) a row runs at 1.00; just outside, cell-referenced
        (control: 1.0201 is not snapped)."""
        n = S.NOMINAL
        self.assertEqual(S.lam_fed(prow(lam_meas=1.02), conventions=n), (1.0, "snapped"))
        self.assertEqual(S.lam_fed(prow(lam_meas=0.98), conventions=n), (1.0, "snapped"))
        lam, src = S.lam_fed(prow(lam_meas=1.0201), conventions=n)
        self.assertEqual(src, "cell_referenced")
        self.assertAlmostEqual(lam, 1.0201, places=15)

    def test_the_snap_is_judged_against_the_rows_lambda_ref(self):
        """The snap reads the row's own lambda_ref, never 1.00 (contract section 3; the fourth contract review's
        mutant m26, which snapped against 1.0, survived every test): on a lambda_ref-0.99 table (the Honda's)
        0.975 lies 0.015 from it and runs at 1.00, while 1.015 lies 0.025 from it and runs cell-referenced at
        1.025, though 1.015 lies within 0.02 of 1.00 and 0.975 does not. The control: on a lambda_ref-1.0 table
        the two readings swap."""
        n = S.NOMINAL
        self.assertEqual(S.lam_fed(prow(lam_meas=0.975, lam_ref=0.99), conventions=n), (1.0, "snapped"))
        lam, src = S.lam_fed(prow(lam_meas=1.015, lam_ref=0.99), conventions=n)
        self.assertEqual(src, "cell_referenced")
        self.assertAlmostEqual(lam, 1.025, places=14)
        lam, src = S.lam_fed(prow(lam_meas=0.975, lam_ref=1.0), conventions=n)
        self.assertEqual(src, "cell_referenced")
        self.assertAlmostEqual(lam, 0.975, places=14)
        self.assertEqual(S.lam_fed(prow(lam_meas=1.015, lam_ref=1.0), conventions=n), (1.0, "snapped"))

    def test_cell_referencing_and_the_e6_conventions(self):
        """A Honda-like cell (lambda_ref 0.99): 0.95 runs at 0.95 - (0.99 - 1) = 0.96; E6 row 1 runs it as
        published (0.95), the snap kept; E6 row 12 removes the snap, so a row within the band runs
        cell-referenced instead of at 1.00."""
        r = prow(lam_meas=0.95, lam_ref=0.99)
        self.assertAlmostEqual(S.lam_fed(r, conventions=S.NOMINAL)[0], 0.96, places=14)
        row1 = S.Conventions(snap=True, cell_referenced=False, afr_st=None, lhv_j_per_kg=None)
        self.assertEqual(S.lam_fed(r, conventions=row1), (0.95, "published"))
        self.assertEqual(S.lam_fed(prow(lam_meas=0.995, lam_ref=0.99), conventions=row1), (1.0, "snapped"))
        row12 = S.Conventions(snap=False, cell_referenced=True, afr_st=None, lhv_j_per_kg=None)
        lam, src = S.lam_fed(prow(lam_meas=1.01), conventions=row12)
        self.assertEqual(src, "cell_referenced")
        self.assertAlmostEqual(lam, 1.01, places=15)

    def test_a_row_without_lambda_runs_at_one(self):
        """Decision 54: a fired row without lambda runs at 1.00, flagged; it has no EPA lambda to compare."""
        r = prow(lam_meas=None, lambda_missing=True)
        self.assertEqual(S.lam_fed(r, conventions=S.NOMINAL), (1.0, "missing_at_1.00"))
        self.assertIsNone(S.lam_cellref(r))
        self.assertIsNone(S.air_cal(r, view=V, conventions=S.NOMINAL))

    def test_fuel_and_the_calibration_air(self):
        """The table's own fuel, E6 rows 2-3's overrides, and air = meter x AFR_st x lambda fed; None without a
        meter (control) or for an Initial row's table."""
        r = prow(lam_meas=0.90, fuel_meter_gps=4.0)
        self.assertIs(S.fuel_of(r, view=V, conventions=S.NOMINAL), FUEL)
        f2 = S.fuel_of(r, view=V, conventions=S.Conventions(True, True, 14.7, 44.0e6))
        self.assertEqual((f2.afr_st, f2.lhv_j_per_kg, f2.ftag), (14.7, 44.0e6, "F1"))
        self.assertAlmostEqual(S.air_cal(r, view=V, conventions=S.NOMINAL), 4.0 * 14.56 * 0.90, places=12)
        self.assertIsNone(S.air_cal(prow(fuel_meter_gps=None, meter_missing=True), view=V, conventions=S.NOMINAL))

    def test_a_sentinel_row_runs_at_the_model_ecus_spark(self):
        """Decision 54: a sentinel row (or an empty spark cell) runs at the model ECU's spark at EPA's MAP and
        intake temperature; a published spark is fed as published (control)."""
        toy = Toy()
        sen = prow(spark_btdc=None, spark_sentinel=True, map_kpa=130.0, imt_k=320.0)
        x = S.row_inputs(sen, view=V, conventions=S.NOMINAL, model=toy)
        self.assertEqual(x.spark_source, "model_ecu_sentinel")
        self.assertAlmostEqual(x.spark_btdc, 30.0 - 13.0 - 4.0, places=12)
        x2 = S.row_inputs(prow(spark_btdc=7.5), view=V, conventions=S.NOMINAL, model=toy)
        self.assertEqual((x2.spark_btdc, x2.spark_source), (7.5, "published"))
        with self.assertRaises(TypeError):
            S.row_inputs(sen, conventions=S.NOMINAL, model=toy)


class Censoring(unittest.TestCase):
    def finals(self, lams):
        return [prow(epa_rows.FinalRow, table="t_final", source_row=6 + i, hold=6 + i, lam_meas=x)
                for i, x in enumerate(lams)]

    def test_two_rows_at_their_minimum_censor(self):
        """At least 2 calibration Final rows at their own minimum within 1e-9 (decision 54, amendment C1)."""
        c = S.censoring(self.finals([0.70, 0.70 + 5e-10, 0.75]))
        self.assertTrue(c.censored)
        self.assertEqual((c.n_at_min, c.value), (2, 0.70))

    def test_one_row_or_a_wider_gap_does_not(self):
        """Controls: one row at the minimum, or a second 2e-9 away, is not censoring."""
        self.assertFalse(S.censoring(self.finals([0.70, 0.75, 0.80])).censored)
        self.assertFalse(S.censoring(self.finals([0.70, 0.70 + 2e-9, 0.75])).censored)

    def test_censoring_is_defined_on_final_rows_only(self):
        with self.assertRaises(ValueError):
            S.censoring(self.finals([0.70, 0.70]) + [prow(lam_meas=0.70)])

    def test_the_runs_flag_marks_the_value_and_not_below_it(self):
        """mark_censored, the function the run calls (validate_epa._marked, epa_fit.evaluate_rows; E8's censored
        list and dl_without_censored read its flag), by the same rule as held_out_censored (the fourth contract
        review's mutant m24, which flagged rows at or below the value, survived: only held_out_censored was
        tested): a Final row at the censoring value (within 1e-9) is flagged; one below it, one above it, a steady
        row and an Initial row at it are not. The control: without censoring nothing is flagged."""
        c = S.censoring(self.finals([0.70, 0.70]))
        F_ = pops("fired", "hot")
        evs = [ev(10, "2000", F_, kind="final", lam=0.70), ev(11, "2000", F_, kind="final", lam=0.70 + 5e-10),
               ev(12, "2000", F_, kind="final", lam=0.69), ev(13, "2000", F_, kind="final", lam=0.71),
               ev(14, "2000", F_, kind="steady", lam=0.70), ev(15, "2000", F_, kind="initial", lam=0.70)]
        out = S.mark_censored(evs, censoring=c)
        self.assertEqual([("censored" in e.flags) for e in out], [True, True, False, False, False, False])
        none = S.mark_censored(evs, censoring=S.censoring(self.finals([0.70, 0.75])))
        self.assertFalse(any("censored" in e.flags for e in none))
        # the two rules agree on the same rows (mistake 10: one rule, two functions)
        rows = [held_final(source_row=20, lam_meas=0.70), held_final(source_row=21, lam_meas=0.69),
                held_final(source_row=22, lam_meas=0.70 + 5e-10)]
        self.assertEqual(S.held_out_censored(rows, censoring=c), (("t_final", 20), ("t_final", 22)))

    def test_a_held_out_row_below_the_value_is_not_counted(self):
        """A held-out Final row at the censoring value is counted; one below it shows the sensor reads lower and is
        not (contract section 3, after the seventh review); one above is not either."""
        c = S.censoring(self.finals([0.70, 0.70]))
        rows = [held_final(source_row=10, lam_meas=0.70), held_final(source_row=11, lam_meas=0.69),
                held_final(source_row=12, lam_meas=0.71)]
        self.assertEqual(S.held_out_censored(rows, censoring=c), (("t_final", 10),))


class D1Inversion(unittest.TestCase):
    def setUp(self):
        self.toy = Toy()
        self.s = -0.1           # the toy ECU's d spark / d MAP

    def root(self, target):
        # T(MAP) = 1.5 MAP + 0.8 (10 + s (MAP - 120)) - 20 = 1.42 MAP - 2.4 at 2000 rpm
        return (target + 2.4) / 1.42

    def test_the_first_bracket_is_bisected_to_1e3_kpa(self):
        """Pre-scan, bracket 140-150 kPa, 14 bisections to a width under 1e-3 kPa, the midpoint within 5e-4 kPa of
        the hand root, the spark moved by s (MAP - MAP_E) (decision 57)."""
        p = S.d1_invert(_X, 200.0, model=self.toy, dtheta=0.25, spark_slope=self.s)
        self.assertTrue(p.bracketed)
        self.assertLessEqual(abs(p.map_kpa - self.root(200.0)), 5e-4)
        self.assertGreater(abs(p.map_kpa - self.root(200.0)), 0.0)
        self.assertAlmostEqual(p.spark_btdc, 10.0 + self.s * (p.map_kpa - 120.0), places=12)
        self.assertEqual(p.n_cycles, 39 + 14 + 1)

    def test_a_tie_between_the_bounds_is_counted_at_20_kpa(self):
        """With no bracket and EPA's torque equally far from the model's at both ends, the row sits at 20 kPa
        (contract section 4, D1: "20 kPa on a tie"; the contract review's mutant m18, < for <=, survived). A model
        whose torque is flat at 100 N m, the target 90: both ends 10 away. The control: target 110, the same tie
        from above, is 20 kPa too, and a target below a rising torque is the lower bound by distance alone
        (test_no_bracket_is_counted_at_the_nearer_bound)."""
        class Flat(Toy):
            def cycle(self, x, *, dtheta):
                out = Toy.cycle(self, x, dtheta=dtheta)
                return replace(out, torque_nm=100.0)
        for target in (90.0, 110.0):
            p = S.d1_invert(_X, target, model=Flat(), dtheta=0.25, spark_slope=self.s)
            self.assertEqual((p.bracketed, p.bound_kpa, p.map_kpa), (False, 20.0, 20.0), target)

    def test_no_bracket_is_counted_at_the_nearer_bound(self):
        """Above the scan's torque the row sits at 400 kPa, below it at 20 kPa (controls of each other)."""
        hi = S.d1_invert(_X, 600.0, model=self.toy, dtheta=0.25, spark_slope=self.s)
        lo = S.d1_invert(_X, -100.0, model=self.toy, dtheta=0.25, spark_slope=self.s)
        self.assertEqual((hi.bracketed, hi.bound_kpa, hi.map_kpa), (False, 400.0, 400.0))
        self.assertEqual((lo.bracketed, lo.bound_kpa, lo.map_kpa), (False, 20.0, 20.0))
        self.assertEqual(hi.n_cycles, 39)

    def test_a_scan_point_that_hits_the_target_is_the_answer(self):
        t150 = self.toy.cycle(replace(_X, map_kpa=150.0, spark_btdc=10.0 + self.s * 30.0), dtheta=0.25).torque_nm
        p = S.d1_invert(_X, t150, model=self.toy, dtheta=0.25, spark_slope=self.s)
        self.assertEqual((p.map_kpa, p.n_cycles), (150.0, 39))

    def test_the_first_crossing_from_20_kpa_up(self):
        """A torque that crosses EPA's twice (129.3 and 270.7 kPa): the first bracket from 20 kPa up is taken;
        control: the second root is a different MAP."""
        p = S.d1_invert(_X, 250.0, model=HumpToy(), dtheta=0.25, spark_slope=self.s)
        self.assertLessEqual(abs(p.map_kpa - (200.0 - math.sqrt(5000.0))), 5e-4)
        self.assertGreater(abs(p.map_kpa - (200.0 + math.sqrt(5000.0))), 100.0)


class Kernel(unittest.TestCase):
    def test_epa_lambda_is_cell_referenced_by_the_rows_lambda_ref_and_never_snapped(self):
        """kernel_point's Measured.lam_cellref, E8's EPA lambda, is lambda_meas - (lambda_ref - 1), unsnapped
        (contract section 4, E8; decision 57; the fourth tests review's finding that raw lambda_meas in its place
        survived every test): on a lambda_ref-0.99 Final row 0.995 reads 1.005, though the model runs the row
        snapped at 1.00. The control: lambda_ref 1.0 reads lambda_meas, 0.995."""
        toy = Toy()
        for ref, want in ((0.99, 1.005), (1.0, 0.995)):
            r = prow(epa_rows.FinalRow, table="t_final", hold=9, source_row=9, lam_meas=0.995, lam_ref=ref,
                     pops=pops("fired", "hot"))
            e = S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25,
                                                needs={"at_epa", "ecu"}, shift=None))
            self.assertAlmostEqual(e.measured.lam_cellref, want, places=14)
            self.assertEqual((e.inputs.lam, e.inputs.lam_source), (1.0, "snapped"))

    def test_a_row_is_evaluated_for_what_its_populations_need(self):
        """kernel_point: at EPA's MAP, D1 on a fired row with a meter, lambda 1 on an enriched hot row, the ECU on a
        Final row; the D1 slope is the ECU's central difference +-2 kPa (here -0.1 deg/kPa exactly)."""
        toy = Toy()
        r = prow(epa_rows.FinalRow, table="t_final", hold=9, source_row=9, lam_meas=0.85,
                 pops=pops("fired", "fired_meter", "hot", "hot_enr"))
        need = S.default_needs(r)
        self.assertEqual(need, frozenset({"at_epa", "d1", "lam1", "ecu"}))
        e = S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25, needs=need, shift=None))
        self.assertEqual((e.kind, e.hold, e.inputs.lam_source), ("final", 9, "cell_referenced"))
        self.assertAlmostEqual(e.lam1.egt_c - e.out.egt_c, 500.0 * (1.0 - 0.85), places=9)
        self.assertAlmostEqual(e.d1.spark_btdc - 10.0, -0.1 * (e.d1.map_kpa - 120.0), places=9)
        self.assertAlmostEqual(e.d1.delta_d, e.d1.out.fuel_gps / 5.0 - 1.0, places=15)
        self.assertEqual(e.ecu.lam, 1.0)
        steady = prow(pops=pops("fired"))
        self.assertEqual(S.default_needs(steady), frozenset({"at_epa"}))
        # L0 and L1 read D1's point at every hot lambda~1 row with a meter, fired or not (WP3's fix of 23
        # October 2026: such a row below 2 bar would have stopped the run in _need); the control above, a fired
        # row without a meter, needs no D1
        hl1m = prow(pops=pops("hot", "hot_l1", "hot_meter", "hot_l1_meter"))
        self.assertEqual(S.default_needs(hl1m), frozenset({"at_epa", "d1"}))

    def test_a_shift_moves_the_reading_and_not_the_populations(self):
        """InputShift moves one reading (E6 row 11's +6.3 K on the charge; u_input's +-u_j); a sentinel row has
        no spark to shift (control: a published spark moves)."""
        toy = Toy()
        r = prow(pops=pops("fired", "hot"))
        t = S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25, needs={"at_epa"}, shift=S.InputShift("imt", 6.3))
        e = S.kernel_point(toy, t)
        self.assertAlmostEqual(e.inputs.iat_k, 316.3, places=12)
        self.assertEqual(e.pops, r.pops)
        sen = prow(spark_btdc=None, spark_sentinel=True)
        a = S.kernel_point(toy, replace(t, row=sen, shift=S.InputShift("spark", 1.0)))
        b = S.kernel_point(toy, replace(t, row=sen, shift=None))
        self.assertEqual(a.inputs.spark_btdc, b.inputs.spark_btdc)
        c = S.kernel_point(toy, replace(t, shift=S.InputShift("spark", 1.0)))
        self.assertEqual(c.inputs.spark_btdc, 11.0)
        with self.assertRaises(ValueError):
            S.InputShift("tip", 1.0)
        # the torque reading (D1's inversion target, WP3's second fix of 23 October 2026): an absolute and a
        # relative shift move it and nothing the cycle reads
        d = S.kernel_point(toy, replace(t, shift=S.InputShift("torque", 2.0)))
        self.assertEqual(d.measured.torque_nm, r.torque_nm + 2.0)
        self.assertEqual(d.inputs, S.kernel_point(toy, replace(t, shift=None)).inputs)
        q = S.kernel_point(toy, replace(t, shift=S.InputShift("torque_rel", 0.01)))
        self.assertEqual(q.measured.torque_nm, r.torque_nm * 1.01)


# =============================================================================================
def e1a_set():
    """Three hot lines: 1750 at +1, +2, +3 %; 2500 at -3 % three times; 3500 with two rows at +10 % (2 clusters:
    not deciding); one fired row that is not hot at +50 % (outside the population)."""
    H = pops("fired", "fired_meter", "hot", "hot_meter")
    evs = [ev(10 + i, "1750", H, T_m=200.0 * (1 + x / 100)) for i, x in enumerate((1.0, 2.0, 3.0))]
    evs += [ev(20 + i, "2500", H, T_m=200.0 * 0.97) for i in range(3)]
    evs += [ev(30 + i, "3500", H, T_m=200.0 * 1.10) for i in range(2)]
    evs += [ev(40, "1750", pops("fired", "fired_meter"), T_m=300.0)]
    return evs


class PerLineRows(unittest.TestCase):
    def test_e1a_takes_the_worst_deciding_line(self):
        """E1a = the worst deciding line's mean signed error (decision 57): -3 % on 2500; the 3500 line (2 rows)
        does not decide; in-sample it fails against 1.9 %."""
        r = S.row_E1a(e1a_set(), view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.E, -3.0, places=10)
        self.assertEqual((r.worst_line, r.deciding, r.passes), ("2500", ("1750", "2500"), False))
        self.assertEqual({ls.line: ls.clusters for ls in r.lines}, {"1750": 4 - 1, "2500": 3, "3500": 2})

    def test_a_row_outside_the_population_does_not_move_it(self):
        """Control: the non-hot row's output moves nothing; a member's moves E."""
        evs = e1a_set()
        base = S.row_E1a(evs, view=V, stage="in_sample", tightening=None).E
        moved = [replace(e, out=replace(e.out, torque_nm=999.0)) if e.source_row == 40 else e for e in evs]
        self.assertEqual(S.row_E1a(moved, view=V, stage="in_sample", tightening=None).E, base)
        moved = [replace(e, out=replace(e.out, torque_nm=200.0)) if e.source_row == 20 else e for e in evs]
        self.assertNotEqual(S.row_E1a(moved, view=V, stage="in_sample", tightening=None).E, base)

    def test_no_deciding_line_neither_blocks_nor_passes(self):
        """Decision 55: in-sample, no calibration line with 3 clusters gives passes None and no statistic."""
        evs = [e for e in e1a_set() if e.line == "3500"]
        r = S.row_E1a(evs, view=V, stage="in_sample", tightening=None)
        self.assertEqual((r.no_statistic, r.passes, r.E), (True, None, None))

    def test_each_population(self):
        """E2a hot_meter (fuel), E3a hot_l1 (TIT), E4a hot_enr, E1b fired, E2b fired_meter, E3b fired_l1, each on its
        own rows with a hand answer."""
        P = pops("fired", "fired_meter", "fired_l1", "hot", "hot_meter", "hot_l1", "hot_l1_meter")
        Q = pops("fired", "fired_meter", "hot", "hot_meter", "hot_enr")
        evs = [ev(1, "2000", P, F_m=5.0 * 1.02, egt=805.0), ev(2, "2000", P, F_m=5.0 * 1.04, egt=811.0),
               ev(3, "2000", P, F_m=5.0 * 0.97, egt=796.0),
               ev(4, "2000", Q, F_m=5.0 * 1.10, egt=830.0), ev(5, "2000", Q, F_m=5.0, egt=790.0),
               ev(6, "2000", Q, F_m=5.0, egt=805.0)]
        g = dict(view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(S.row_E2a(evs, **g).E, (2 + 4 - 3 + 10 + 0 + 0) / 6, places=10)
        self.assertAlmostEqual(S.row_E3a(evs, **g).E, (5 + 11 - 4) / 3, places=10)
        self.assertAlmostEqual(S.row_E4a(evs, **g).E, (30 - 10 + 5) / 3, places=10)
        self.assertAlmostEqual(S.row_E1b(evs, **g).E, 0.0, places=10)
        self.assertAlmostEqual(S.row_E2b(evs, **g).E, (2 + 4 + 3 + 10) / 6, places=10)
        self.assertAlmostEqual(S.row_E3b(evs, **g).E, (5 + 11 + 4) / 3, places=10)
        self.assertAlmostEqual(S.row_E1b(evs, **g).extra["worth_b_pct"], 100 * 0.905 / 5.43 / 1.353, places=12)

    def test_rows_without_a_reading_and_the_readings_without_them(self):
        """Decision 54: a lambda-less row enters E1a (hot) at lambda 1.00 and no lambda band; a sentinel row enters
        at the model ECU's spark; every statistic is also reported without each (hand values)."""
        H = pops("fired", "fired_meter", "hot", "hot_meter")
        evs = [ev(1, "2000", H, T_m=202.0), ev(2, "2000", H, T_m=204.0), ev(3, "2000", H, T_m=206.0),
               ev(4, "2000", H, T_m=220.0, lam=None, flags={"lambda_missing"}),
               ev(5, "2000", H, T_m=180.0, spark=None, flags={"spark_sentinel"})]
        r = S.row_E1a(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.E, (1 + 2 + 3 + 10 - 10) / 5, places=10)
        self.assertAlmostEqual(r.without["lambda_missing"], (1 + 2 + 3 - 10) / 4, places=10)
        self.assertAlmostEqual(r.without["spark_sentinel"], (1 + 2 + 3 + 10) / 4, places=10)

    def test_the_tie_goes_to_the_larger_u_val_held_out(self):
        """Two lines with equal |E|: in-sample the first in line order is reported; held out the one with the
        larger u_val (decision 57). Line 3000's rows carry a larger input sensitivity, so its u_val is larger."""
        H = pops("fired", "fired_meter", "hot", "hot_meter")
        evs = [ev(i, "2000", H, T_m=250.0) for i in range(3)] + [ev(10 + i, "3000", H, T_m=150.0) for i in range(3)]
        r = S.row_E1a(evs, view=V, stage="in_sample", tightening=None)
        self.assertEqual((r.worst_line, abs(r.E)), ("2000", 25.0))           # +25 % and -25 %, exactly equal
        unc = u_inputs(evs, effect=lambda e, ch: (2.0 if e.line == "3000" else 0.0) if ch == "map" else 0.0)
        h = S.held_out_row("E1a", evs, view=V, tightening=None, unc=unc)
        u = {ls.line: ls.u.u_val for ls in h.lines}
        self.assertGreater(u["3000"], u["2000"])
        self.assertEqual((h.worst_line, h.E), ("3000", -25.0))


class Labels(unittest.TestCase):
    def test_every_branch_of_line_label(self):
        """off if |E| - 2u > R; untested if 2u > R; validated if |E| + 2u <= R; else limited; each edge on the side
        the contract writes (> and <=); certifies only if 2 u_stat <= R."""
        self.assertEqual(S.line_label(5.0, 1.0, 0.5, 2.0), ("off", True))
        self.assertEqual(S.line_label(-5.0, 1.0, 2.0, 2.0), ("off", False))
        self.assertEqual(S.line_label(1.0, 1.5, 0.5, 2.0), ("untested", True))
        self.assertEqual(S.line_label(0.5, 0.5, 0.5, 2.0), ("validated", True))
        self.assertEqual(S.line_label(1.5, 0.5, 1.0, 2.0), ("limited", True))
        self.assertEqual(S.line_label(1.0, 0.5, 1.0000001, 2.0)[1], False)
        self.assertEqual(S.line_label(1.0, 0.5, 0.5, 2.0)[0], "validated")     # |E| + 2u == R
        self.assertEqual(S.line_label(4.0, 1.0, 0.5, 2.0)[0], "limited")       # |E| - 2u == R is not off, 2u == R not untested
        self.assertEqual(S.line_label(4.0, 0.999, 0.5, 2.0)[0], "off")          # control: just inside the edge
        self.assertEqual(S.line_label(0.0, 1.0, 0.5, 2.0)[0], "validated")     # 2u == R is not untested

    def test_row_label_and_worse(self):
        """A row is off if a deciding line is; else the worse of the certifying lines' validated and limited;
        untested if none certifies."""
        L = S.LineStat
        self.assertEqual(S.row_label([L("a", 3, 1, None, "off", False), L("b", 3, 0, None, "validated", True)]), "off")
        self.assertEqual(S.row_label([L("a", 3, 1, None, "validated", True), L("b", 3, 1, None, "limited", True)]),
                         "limited")
        self.assertEqual(S.row_label([L("a", 3, 1, None, "validated", True), L("b", 3, 1, None, "limited", False)]),
                         "validated")
        self.assertEqual(S.row_label([L("a", 3, 1, None, "limited", False)]), "untested")
        self.assertEqual(S.row_label([L("a", 3, 1, None, "untested", True)]), "untested")
        order = ["validated", "limited", "untested", "off"]
        for i, a in enumerate(order):
            for j, b in enumerate(order):
                self.assertEqual(S.worse(a, b), order[max(i, j)])

    def test_kappa(self):
        self.assertEqual(S.kappa(0.3, 0.2, 2.0, "validated"), 1.0)
        self.assertAlmostEqual(S.kappa(-1.5, 0.5, 2.0, "limited"), 1.25, places=15)
        self.assertAlmostEqual(S.kappa(3.0, 2.0, 2.0, "untested"), 3.5, places=15)


class HousingBounds(unittest.TestCase):
    CASES = [(3.317, 0.01353), (-4.0, 0.002), (2.0, -0.01), (0.0, 0.0), (-1.0, -0.004), (12.0, 0.0), (0.5, 0.03),
             (-8.0, 0.012)]

    def test_l0_closed_form_against_a_dense_grid(self):
        """max over f of |f e + f(1 - f) G d| by endpoints and vertex equals the maximum over 10 001 points in f to
        the grid's resolution, and is never below it."""
        f = np.linspace(0.0, 1.0, 10001)
        for e, d in self.CASES:
            val, fs, h = S.house_max(e, d, G_K)
            grid = np.max(np.abs(f * e + f * (1 - f) * G_K * d))
            self.assertGreaterEqual(val + 1e-12, grid)
            self.assertLess(val - grid, 1e-6)
            self.assertAlmostEqual(abs(h), val, places=12)

    def test_the_contracts_5183_from_its_coefficients(self):
        """E1a's R rests on 5.183 K per 1 % of torque at f* = 0.625 (contract section 1.4). From b58_propagation.json's
        own coefficients (the step output the contract read) the closed form gives 5.183 to the printed digits.
        From the coefficients the JSON prints rounded, (3.317, 0.01353, 980.27), it gives 5.1817, which prints as
        5.182: the rounded coefficients do not reproduce the printed bound (WP3_INTERFACES.md 9.4's expectation)."""
        with open(os.path.join(C.OUT_DIR, "b58_propagation.json"), encoding="utf-8") as fh:
            b = json.load(fh)
        env = b["env_torque_bias"]
        G = b["climb"]["point"]["egt"] - K.T_AMB_C
        gas = max(abs(env["+0.01"]["degt_k"]), abs(env["-0.01"]["degt_k"]))
        flow = max(abs(env["+0.01"]["dmdot_rel"]), abs(env["-0.01"]["dmdot_rel"]))
        val, fs, _ = S.house_max(gas, flow, G)
        self.assertEqual(round(val, 3), 5.183)
        self.assertEqual(round(fs, 3), 0.625)
        rounded, _, _ = S.house_max(3.317, 0.01353, G_K)
        self.assertEqual(round(rounded, 3), 5.182)

    def test_l1_closed_form_against_a_dense_grid(self):
        """L1 = max over f of [max_l H_l - min_l H_l], exact over ordered pairs, equals a 10 001-point grid's."""
        f = np.linspace(0.0, 1.0, 10001)
        for lines in ({"a": (3.0, 0.01), "b": (-2.0, 0.004), "c": (1.0, -0.006)},
                      {"a": (0.0, 0.02), "b": (0.0, -0.02)}, {"a": (5.0, 0.0), "b": (-5.0, 0.0), "c": (0.0, 0.0)}):
            H = np.array([f * e + f * (1 - f) * G_K * d for e, d in lines.values()])
            grid = float(np.max(H.max(axis=0) - H.min(axis=0)))
            val, fs, a, b = S.l1_spread(lines, G_K)
            self.assertGreaterEqual(val + 1e-12, grid)
            self.assertLess(val - grid, 1e-6)
            ea, da = lines[a]
            eb, db = lines[b]
            self.assertAlmostEqual(val, (fs * ea + fs * (1 - fs) * G_K * da) - (fs * eb + fs * (1 - fs) * G_K * db), 12)

    def l0_rows(self):
        P = pops("fired", "fired_meter", "hot", "hot_meter", "hot_l1", "hot_l1_meter")
        spec = {"1750": [(0.01, 4.0), (0.02, 6.0), (0.015, 2.0)], "2500": [(-0.01, -3.0), (0.0, -5.0), (-0.02, -1.0)],
                "3500": [(0.03, 9.0), (0.01, 7.0)]}
        evs, n = [], 0
        for line, pts in spec.items():
            for dlt, e_d in pts:
                evs.append(ev(n, line, P, d1=d1p(dlt, e_d)))
                n += 1
        return evs, spec

    def test_l0_and_l1_on_rows(self):
        """L0 per deciding line on the line means at the D1 point, its u_stat the SE of h_i at f* (the envelope
        theorem); L1 over the deciding lines (the 2-row line excluded) with u_stat sqrt(u_a^2 + u_b^2)."""
        evs, spec = self.l0_rows()
        r0 = S.row_L0(evs, view=V, stage="in_sample", tightening=None)
        means = {ln: (np.mean([p[1] for p in pts]), np.mean([p[0] for p in pts])) for ln, pts in spec.items()}
        exp = {ln: S.house_max(e, d, G_K)[0] for ln, (e, d) in means.items() if ln != "3500"}
        self.assertEqual(r0.deciding, ("1750", "2500"))
        worst = max(exp, key=lambda k: exp[k])
        self.assertEqual(r0.worst_line, worst)
        self.assertAlmostEqual(r0.E, exp[worst], places=10)
        core = S._core_L0(tuple(evs), V, None)
        _, fs, _ = S.house_max(*means["1750"], G_K)
        h = [fs * e + fs * (1 - fs) * G_K * d for d, e in spec["1750"]]
        self.assertAlmostEqual(core.comp_se["1750"], np.std(h, ddof=1) / math.sqrt(3), places=12)
        r1 = S.row_L1(evs, view=V, stage="in_sample", tightening=None)
        val, f1, a, b = S.l1_spread({k: means[k] for k in ("1750", "2500")}, G_K)
        self.assertAlmostEqual(r1.E, val, places=10)
        c1 = S._core_L1(tuple(evs), V, None)
        ha = [f1 * e + f1 * (1 - f1) * G_K * d for d, e in spec[a]]
        hb = [f1 * e + f1 * (1 - f1) * G_K * d for d, e in spec[b]]
        self.assertAlmostEqual(c1.comp_se["L1"], math.sqrt(np.var(ha, ddof=1) / 3 + np.var(hb, ddof=1) / 3), places=12)

    def test_l1_needs_two_deciding_lines_and_takes_the_tightened_r(self):
        """L1 has no statistic on one deciding line (control: two give one); held out, the B58's roads slope sets
        R = min(9.9, b/slope rounded down) (decision 71), in-sample R stays 9.9 K."""
        evs, _ = self.l0_rows()
        one = [e for e in evs if e.line != "2500"]
        self.assertTrue(S.row_L1(one, view=V, stage="in_sample", tightening=None).no_statistic)
        tight = {"plant": "b58", "L1": {"slope_points_per_K": 0.12}}
        h = S.row_L1(evs, view=V, stage="held_out", tightening=tight)
        self.assertEqual(h.R, K.rdown(0.905 / 0.12))
        loose = {"plant": "b58", "L1": {"slope_points_per_K": 0.05}}
        self.assertEqual(S.row_L1(evs, view=V, stage="held_out", tightening=loose).R, 9.9)
        self.assertEqual(S.row_L1(evs, view=V, stage="in_sample", tightening=None).R, 9.9)
        with self.assertRaises(ValueError):
            S.row_L1(evs, view=V, stage="held_out", tightening={"plant": "mazda_25t", "L1": {"slope_points_per_K": 0.2}})


class E8Rows(unittest.TestCase):
    def finals(self, lam_diffs, spark_diffs, *, lam_none=(), spark_none=(), lines=None):
        evs = []
        for i, (dl, ds) in enumerate(zip(lam_diffs, spark_diffs)):
            lam = None if i in lam_none else 0.9
            spark = None if i in spark_none else 2.0
            ecu = S.EcuOut(spark_btdc=2.0 + ds, lam=0.9 + dl, cam_deg=None)
            evs.append(ev(100 + i, (lines or ["2000"] * 99)[i], pops("fired", "hot"), kind="final", lam=lam,
                          spark=spark, ecu=ecu, map_kpa=150.0 + 10 * i,
                          flags={"lambda_missing"} if i in lam_none else ({"spark_sentinel"} if i in spark_none else ())))
        return evs

    def test_e8_reads_epa_lambda_unsnapped_inside_the_band(self):
        """Inside the snap band EPA's lambda is compared as measured (contract section 4, E8: "with no snap";
        decision 57); the snapped reading is reported beside it, descriptive. Three Final rows at EPA lambda 0.99,
        the ECU at 1.00, its spark 0.5 above EPA's: dl 0.01 (the snapped reading 0.0) and E8 = 100 (|P_lambda(0.01)|
        + |P_spark(0.5)|) (the fourth tests review's mutation snapping EPA's lambda in _e8_parts survived every
        test: its finals lie outside the band). The control: the snapped E differs."""
        ecu = S.EcuOut(spark_btdc=2.5, lam=1.0, cam_deg=None)
        evs = [ev(100 + i, "2000", pops("fired", "hot"), kind="final", lam=0.99, spark=2.0, ecu=ecu,
                  map_kpa=150.0 + 10 * i) for i in range(3)]
        r = S.row_E8(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.extra["dl"], 0.01, places=12)
        self.assertAlmostEqual(r.extra["terms"]["lambda"]["shift"], 0.01, places=12)
        self.assertAlmostEqual(r.extra["ds"], 0.5, places=12)
        self.assertAlmostEqual(r.E, 100 * (abs(K.interp(K3_LAM, 0.01)) + abs(K.interp(K3_SPARK, 0.5))), places=9)
        self.assertAlmostEqual(r.extra["snapped"]["dl"], 0.0, places=12)
        self.assertGreater(abs(r.E - r.extra["snapped"]["E_pct"]), 1.0)

    def test_e8_on_a_lambda_ref_099_table_through_the_kernel(self):
        """E8 end to end through kernel_point on a lambda_ref-0.99 table (the Honda's), every Final row within 0.02
        of lambda_ref, the Toy ECU at 1.00 and 0.5 deg above EPA's spark: lambda_meas 0.975, 0.985, 0.995 read
        0.985, 0.995, 1.005 cell-referenced, so the gating dl is 0.005 and the snapped one 0.0. The contract
        review's mutants give other numbers: the cell-referencing's sign flipped (m38) 0.025, E8 gated on the
        snapped dl (m44) 0.0."""
        toy = Toy()
        rows = [prow(epa_rows.FinalRow, table="t_final", hold=9 + i, source_row=9 + i, map_kpa=m, lam_meas=lm,
                     lam_ref=0.99, spark_btdc=sp, pops=pops("fired", "hot"))
                for i, (m, lm, sp) in enumerate(((120.0, 0.975, 15.5), (130.0, 0.985, 14.5), (140.0, 0.995, 13.5)))]
        evs = [S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25, needs={"at_epa", "ecu"},
                                               shift=None)) for r in rows]
        res = S.row_E8(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(res.extra["dl"], 0.005, places=12)
        self.assertAlmostEqual(res.extra["ds"], 0.5, places=12)
        self.assertAlmostEqual(res.extra["snapped"]["dl"], 0.0, places=12)
        self.assertAlmostEqual(res.E, 100 * (abs(K.interp(K3_LAM, 0.005)) + abs(K.interp(K3_SPARK, 0.5))), places=9)

    def test_e8_is_the_sum_of_p_through_the_contracts_interp(self):
        """E8 = 100 (|P_lambda(dl)| + |P_spark(ds)|), P equal to thresholds.contract.interp on the contract's B58
        tables, inside and beyond the grid (extrapolation flagged)."""
        for dls, dss in (((-0.03, -0.03, -0.03), (0.5, 0.5, 0.5)), ((0.08, 0.08, 0.08), (-4.0, -4.0, -4.0))):
            r = S.row_E8(self.finals(dls, dss), view=V, stage="in_sample", tightening=None)
            P_l, P_s = K.interp(K3_LAM, dls[0]), K.interp(K3_SPARK, dss[0])
            self.assertAlmostEqual(r.extra["terms"]["lambda"]["P"], P_l, places=12)
            self.assertAlmostEqual(r.E, 100 * (abs(P_l) + abs(P_s)), places=9)
            ext = dls[0] > 0.05
            self.assertEqual((r.extra["terms"]["lambda"]["extrapolated"], r.extra["terms"]["spark"]["extrapolated"]),
                             (ext, ext))

    def test_the_slope_at_zero_is_the_steeper_side(self):
        """At a shift of exactly 0 the u-propagating slope is the steeper of the two segments beside it; elsewhere
        the segment interp uses (decision 57)."""
        self.assertAlmostEqual(S.p_slope(K3_LAM, 0.0), (-0.09695938787167324 - 0.0) / 0.005, places=10)
        self.assertAlmostEqual(S.p_slope(K3_SPARK, 0.0), -0.05811986727917795 / 0.75, places=12)
        # on the B58's tables the steeper side at 0 is the right one, the segment interp itself would use; a table
        # whose left side is steeper tells the two apart (control)
        self.assertEqual(S.p_slope([(-1.0, 2.0), (0.0, 0.0), (1.0, -0.5)], 0.0), -2.0)
        self.assertEqual(S.p_slope([(-1.0, 2.0), (0.0, 0.0), (1.0, -0.5)], 0.5), -0.5)
        self.assertAlmostEqual(S.p_slope(K3_LAM, -0.03), (-0.16259325655562773 + 0.3609955520349323) / 0.03, places=10)
        self.assertAlmostEqual(S.p_slope(K3_LAM, 0.2), (-0.8160228123309472 + 0.4243894274478406) / 0.03, places=10)

    def test_each_subset_needs_three_rows(self):
        """dl over the Final rows that publish a lambda, ds over those that publish a spark, each at least 3 rows or
        E8 has no statistic (version 4's reading of decision 54, kept by version 5); control: three of each give
        one."""
        ok = self.finals((0.01,) * 4, (0.5,) * 4)
        self.assertFalse(S.row_E8(ok, view=V, stage="in_sample", tightening=None).no_statistic)
        short_ds = self.finals((0.01,) * 4, (0.5,) * 4, spark_none=(0, 1))
        r = S.row_E8(short_ds, view=V, stage="in_sample", tightening=None)
        self.assertTrue(r.no_statistic)
        self.assertIn("ds", r.reason)
        self.assertEqual(r.extra["n_dl"], 4)
        short_dl = self.finals((0.01,) * 4, (0.5,) * 4, lam_none=(0, 1))
        self.assertIn("dl", S.row_E8(short_dl, view=V, stage="in_sample", tightening=None).reason)

    def test_rows_without_a_reading_in_e8(self):
        """A lambda-less row enters ds only and a sentinel row dl only; over every Final row they count at lambda
        1.00 and at a spark difference of zero (reported beside, decision 54 read literally)."""
        evs = self.finals((0.01, 0.02, 0.03, 0.04, 0.05), (1.0, 1.0, 1.0, 1.0, 1.0), lam_none=(3,), spark_none=(4,))
        r = S.row_E8(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.extra["dl"], (0.01 + 0.02 + 0.03 + 0.05) / 4, places=12)
        self.assertAlmostEqual(r.extra["ds"], 1.0, places=12)
        ev_all = r.extra["every_final_row"]
        self.assertAlmostEqual(ev_all["dl"], (0.01 + 0.02 + 0.03 + (0.94 - 1.0) + 0.05) / 5, places=12)
        self.assertAlmostEqual(ev_all["ds"], 4.0 / 5, places=12)

    def test_censored_rows_are_listed_and_dl_reported_without_them(self):
        evs = self.finals((0.01, 0.02, 0.03, 0.10), (0.5,) * 4)
        evs[3] = replace(evs[3], flags=evs[3].flags | {"censored"})
        r = S.row_E8(evs, view=V, stage="in_sample", tightening=None)
        self.assertEqual(r.extra["censored_rows"], [["t_final", 103]])
        self.assertAlmostEqual(r.extra["dl_without_censored"], 0.02, places=12)
        self.assertAlmostEqual(r.extra["dl"], 0.04, places=12)

    def test_the_tightening_keeps_the_larger_response_with_its_sign(self):
        """Held out, P per shift is the larger |change| of the contract's and the roads' tables, its sign kept;
        a record measured on another plant, or off the contract's grid, is refused (controls)."""
        roads_l = [(a, (0.20 if a == -0.02 else b * 0.5)) for a, b in K3_LAM]
        roads_s = [(a, b) for a, b in K3_SPARK]
        t = {"plant": "b58", "E8": {"k3_pair_change_vs_lambda_roads": roads_l, "k3_pair_change_vs_spark_roads": roads_s}}
        pl, ps = S.e8_response(V, tightening=t)
        self.assertEqual(dict(pl)[-0.02], 0.20)
        self.assertEqual(dict(pl)[-0.05], K3_LAM[1][1])
        self.assertEqual(ps, K3_SPARK)
        with self.assertRaises(ValueError):
            S.e8_response(V, tightening=dict(t, plant="honda_l15b7"))
        bad = {"plant": "b58", "E8": {"k3_pair_change_vs_lambda_roads": roads_l[1:], "k3_pair_change_vs_spark_roads": roads_s}}
        with self.assertRaises(ValueError):
            S.e8_response(V, tightening=bad)

    def test_e8s_u_propagates_through_the_slopes(self):
        """Held out, E8's u_val and u_stat are dl's and ds's propagated through P's local slopes:
        100 sqrt((s_l u_dl)^2 + (s_s u_ds)^2)."""
        evs = self.finals((0.012, 0.022, 0.032), (0.4, 0.5, 0.9))           # dl 0.022, ds 0.6: inside segments
        unc = u_inputs(evs, effect=lambda e, ch: 0.0)
        h = S.held_out_row("E8", evs, view=V, tightening=None, unc=unc)
        sl, ss = abs(S.p_slope(K3_LAM, 0.022)), abs(S.p_slope(K3_SPARK, 0.6))
        se_l, se_s = np.std([0.012, 0.022, 0.032], ddof=1) / math.sqrt(3), np.std([0.4, 0.5, 0.9], ddof=1) / math.sqrt(3)
        self.assertAlmostEqual(h.u.u_stat, 100 * math.sqrt((sl * se_l) ** 2 + (ss * se_s) ** 2), places=10)
        self.assertAlmostEqual(h.u.u_D, 100 * sl * 0.012, places=10)          # lambda's common 0.012 moves dl by it
        self.assertIn(h.label, S.LABEL_ORDER)


class E4bRows(unittest.TestCase):
    def rows(self, y=(2.0, 4.0, 6.0)):
        B = pops("fired", "fired_meter", "l1_boost", "hot", "hot_l1")
        N = pops("fired", "fired_meter", "hot", "hot_enr")
        evs = [ev(1 + i, "2500", B, map_kpa=m, egt=800.0 + yy) for i, (m, yy) in enumerate(zip((100, 120, 140), y))]
        evs += [ev(10, "2500", N, map_kpa=180.0, egt=805.0, lam1=mo(egt=855.0), lam=0.85),
                ev(11, "2500", N, map_kpa=200.0, egt=809.0, lam1=mo(egt=869.0), lam=0.82)]
        # a line with 2 boosted rows: not deciding, its enriched row would move eps (control)
        evs += [ev(20 + i, "3500", B, map_kpa=m, egt=800.0) for i, m in enumerate((100, 130))]
        evs += [ev(30, "3500", N, map_kpa=190.0, egt=900.0, lam1=mo(egt=910.0), lam=0.85)]
        return evs

    def test_eps_against_a_hand_sum(self):
        """e-hat from the line's least squares (0.1 MAP - 8) at each enriched row's MAP: 10 and 12 K; L_S = 50, 60;
        e_enr = 5, 9; eps = 110 / (45 + 57) - 1; the 60 kPa extrapolation reported; the 3500 line does not
        enter."""
        r = S.row_E4b(self.rows(), view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.E, 100 * (110.0 / 102.0 - 1.0), places=10)
        self.assertEqual(r.deciding, ("2500",))
        self.assertAlmostEqual(r.extra["extrapolation_kpa"]["2500"], 60.0, places=12)
        # below the boosted range too (WP3's fix of 23 October 2026): none here, and an enriched row moved below
        # the boosted MAPs is reported by its distance (the control)
        self.assertEqual(r.extra["extrapolation_below_kpa"]["2500"], 0.0)
        low = [replace(e, measured=replace(e.measured, map_kpa=90.0)) if e.source_row == 10 else e for e in self.rows()]
        r2 = S.row_E4b(low, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r2.extra["extrapolation_below_kpa"]["2500"], 10.0, places=12)
        self.assertEqual(r.extra["enriched_rows"], 2)

    def test_the_delta_method_against_numeric_derivatives(self):
        """u_stat: each enriched row through (a_i - R b_i)/B with n/(n-1), each boosted row through d eps/d y_j
        times its residual's SD (m - 2 dof); the derivatives taken here by finite differences of the statistic."""
        y = (2.5, 3.5, 6.0)
        evs = self.rows(y)
        core = S._core_E4b(tuple(evs), V, None)
        a = [50.0, 60.0]
        x = [100.0, 120.0, 140.0]
        bb, aa = np.polyfit(x, y, 1)
        ehat = [aa + bb * 180.0, aa + bb * 200.0]
        b = [50.0 + 5.0 - ehat[0], 60.0 + 9.0 - ehat[1]]
        A, B = sum(a), sum(b)
        R = A / B
        t_enr = sum((ai - R * bi) ** 2 for ai, bi in zip(a, b)) * 2 / 1 / B ** 2
        res = [yy - (aa + bb * xx) for xx, yy in zip(x, y)]
        s2 = sum(r * r for r in res) / (3 - 2)
        grads = []
        for j in range(3):
            h = 1e-6
            yp = list(y)
            yp[j] += h
            ep = S._core_E4b(tuple(self.rows(tuple(yp))), V, None).E
            grads.append((ep - core.E) / h / 100.0)
        t_reg = sum(g * g for g in grads) * s2
        self.assertAlmostEqual(core.comp_se["pooled"], 100 * math.sqrt(t_enr + t_reg), places=5)

    def test_no_line_with_three_boosted_rows(self):
        evs = [e for e in self.rows() if e.line == "3500"]
        self.assertTrue(S.row_E4b(evs, view=V, stage="in_sample", tightening=None).no_statistic)

    def test_a_line_whose_boosted_rows_share_one_map_decides_nothing(self):
        """WP3's integration (23 October 2026): a line whose boosted lambda~1 rows sit at one MAP has no
        reference line; it decides nothing and is named (it raised ValueError, which would have stopped the
        one-shot run). The control: the same rows at three MAPs give the statistic."""
        B = pops("fired", "fired_meter", "l1_boost", "hot", "hot_l1")
        N = pops("fired", "fired_meter", "hot", "hot_enr")
        evs = [ev(1 + i, "2500", B, map_kpa=120.0, egt=800.0 + i) for i in range(3)]
        evs += [ev(10, "2500", N, map_kpa=180.0, egt=805.0, lam1=mo(egt=855.0), lam=0.85)]
        r = S.row_E4b(evs, view=V, stage="in_sample", tightening=None)
        self.assertTrue(r.no_statistic)
        self.assertIn("one MAP only: 2500", r.reason)
        self.assertEqual(r.extra["lines_one_map"], ["2500"])
        self.assertIsNone(r.passes)
        self.assertFalse(S.row_E4b(self.rows(), view=V, stage="in_sample", tightening=None).no_statistic)

    def test_a_lever_that_sums_to_zero_is_no_statistic(self):
        """WP3's integration: eps = sum L_S / sum(L_S + e_enr - e-hat) - 1 is undefined when the lever sums to
        zero; no statistic with its reason (it raised ValueError). Built from self.rows' 2500 line: the first
        enriched row's lever is 45 K, the second made -45 K (L_S 50 K, e_enr -83 K, e-hat 12 K at 200 kPa).
        The control: its gas 1 K higher, and the statistic is there."""
        B = pops("fired", "fired_meter", "l1_boost", "hot", "hot_l1")
        N = pops("fired", "fired_meter", "hot", "hot_enr")

        def rows(egt2):
            evs = [ev(1 + i, "2500", B, map_kpa=m, egt=800.0 + yy) for i, (m, yy) in
                   enumerate(zip((100, 120, 140), (2.0, 4.0, 6.0)))]
            return evs + [ev(10, "2500", N, map_kpa=180.0, egt=805.0, lam1=mo(egt=855.0), lam=0.85),
                          ev(11, "2500", N, map_kpa=200.0, egt=egt2, lam1=mo(egt=egt2 + 50.0), lam=0.82)]
        r = S.row_E4b(rows(717.0), view=V, stage="in_sample", tightening=None)
        self.assertTrue(r.no_statistic)
        self.assertIn("sums to zero", r.reason)
        self.assertEqual(r.extra["sum_data_lever_k"], 0.0)
        self.assertFalse(S.row_E4b(rows(718.0), view=V, stage="in_sample", tightening=None).no_statistic)

    def test_the_e6_band_values_are_the_bands_text(self):
        """epa_stats.e6_band_values and row10_etas read the contract's band text (WP3's integration): each
        number as printed; a band that states none is refused by name (the control)."""
        bands = [{"n": 4, "band": "x0.75 and x1.333 each, synthetic"},
                 {"n": 5, "band": "+- sigma; else +-10 %; every d row's probe is +-12 % (synthetic)"},
                 {"n": 7, "band": "KI 0.90 and 1.10 (synthetic)"},
                 {"n": 9, "band": "else +-10 % (+-8 crank degrees for IVC and EVO)"},
                 {"n": 10, "band": "0.84-0.97 (synthetic)"},
                 {"n": 13, "band": "the ECU's dwell gate at 0 s and at 30 s"}]
        got = S.e6_band_values(bands)
        self.assertEqual(got, {"d_probe_rel": 0.12, "else_rel": 0.1, "else_cad": 8.0, "row4_factors": (0.75, 1.333),
                               "row7_ki": (0.9, 1.1), "row13_dwell_s": (0.0, 30.0)})
        self.assertEqual(S.row10_etas(bands), (0.84, 0.97))
        bad = [dict(b) for b in bands]
        bad[2]["band"] = "synthetic"
        with self.assertRaises(ValueError) as cm:
            S.e6_band_values(bad)
        self.assertIn("row7_ki", str(cm.exception))

    def test_the_pair_estimate_is_descriptive(self):
        """Over holds whose lambda drops by at least 0.05 from Initial to Final: sum(dS - dD)/sum(dD) (descriptive)."""
        evs = self.rows()
        fin = ev(50, "2500", pops("fired", "hot"), kind="final", hold=50, egt=820.0, tit=810.0, lam=0.88)
        ini = ev(51, "2500", None, kind="initial", hold=50, egt=790.0, tit=770.0, lam=0.95)
        small = ev(53, "2500", None, kind="initial", hold=52, egt=700.0, tit=600.0, lam=0.90)
        fin2 = ev(52, "2500", pops("fired", "hot"), kind="final", hold=52, egt=800.0, tit=800.0, lam=0.88)
        r = S.row_E4b(evs + [fin, ini, small, fin2], view=V, stage="held_out", tightening=None)
        pe = r.extra["pair_estimate"]
        self.assertEqual(pe["holds"], 1)
        self.assertAlmostEqual(pe["value_pct"], 100 * ((30.0 - 40.0) / 40.0), places=10)


class E1iRows(unittest.TestCase):
    def initial(self, n, line, torque, lam=0.95):
        return epa_rows.HeldOutInitialRow(
            engine="synth", table="t_initial", source_row=n, test_cell="cell", line=line, nominal_rpm=2000, hold=n,
            speed_rpm=2000.0, torque_nm=torque, origin="fixture", transient=True, map_kpa=150.0, imt_k=310.0,
            ect_k=360.0, spark_btdc=5.0, spark_sentinel=False, lam_meas=lam, lambda_missing=False, bmep_bar=15.0,
            tit_c=780.0, tip_kpa=160.0)

    def test_e1i_per_line_at_the_initial_rows_own_inputs(self):
        """E1i (held-out only, descriptive): an Initial row carries no lam_ref and no populations, so its task takes
        its table's lambda_ref from the view; the toy's torque at the row's own inputs, 1.5 x 150 + 0.8 x 5 - 20 =
        209 N m, against EPA's per line, labelled a transient; the in-sample stage refuses it (amendment C7)."""
        toy = Toy()
        rows = [self.initial(6 + i, ln, t) for i, (ln, t) in enumerate((("2000", 190.0), ("2000", 200.0), ("2000", 209.0),
                                                                         ("3000", 220.0)))]
        evs = [S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25,
                                                needs=S.default_needs(r), shift=None)) for r in rows]
        self.assertEqual({e.kind for e in evs}, {"initial"})
        self.assertIsNone(evs[0].pops)
        self.assertAlmostEqual(evs[0].measured.lam_cellref, 0.95, places=15)
        r = S.row_E1i(evs, view=V, stage="held_out", tightening=None)
        self.assertAlmostEqual(r.E, 100 * ((209 / 190 - 1) + (209 / 200 - 1) + 0.0) / 3, places=10)
        self.assertEqual((r.kind, r.deciding, r.extra["label"]), ("descriptive", ("2000",), "transient"))
        with self.assertRaises(ValueError):
            S.row_E1i(evs, view=V, stage="in_sample", tightening=None)
        with self.assertRaises(ValueError):
            S.held_out_row("E1i", evs, view=V, tightening=None, unc=None)


class E5Rows(unittest.TestCase):
    def test_pooled_slope_ratio_per_window(self):
        """Sum of cov(MAP, S) over sum of cov(MAP, D) - 1 per window, lines with 3 rows (np.cov, ddof 1); the
        hand covariance is written out here."""
        Bp, Ap = pops("l1_boost", "fired"), pops("l1_thr", "fired")
        m = [100.0, 120.0, 140.0]
        S_ = [700.0, 720.0, 760.0]
        D_ = [690.0, 715.0, 740.0]
        evs = [ev(i, "2000", Bp, map_kpa=mm, egt=s, tit=d) for i, (mm, s, d) in enumerate(zip(m, S_, D_))]
        evs += [ev(10 + i, "2000", Ap, map_kpa=mm, egt=s, tit=d) for i, (mm, s, d) in
                enumerate(zip((50.0, 70.0, 90.0), (500.0, 540.0, 560.0), (510.0, 530.0, 560.0)))]
        evs += [ev(20, "3000", Bp, map_kpa=150.0, egt=900.0, tit=800.0)]        # one row: no window line
        r = S.row_E5(evs, view=V, stage="held_out", tightening=None)

        def cov(a, b):
            ma, mb = sum(a) / 3, sum(b) / 3
            return sum((x - ma) * (y - mb) for x, y in zip(a, b)) / 2
        self.assertAlmostEqual(r.extra["windows"]["B"]["value_pct"], 100 * (cov(m, S_) / cov(m, D_) - 1), places=10)
        self.assertAlmostEqual(r.extra["windows"]["A"]["value_pct"],
                               100 * (cov((50, 70, 90), (500, 540, 560)) / cov((50, 70, 90), (510, 530, 560)) - 1), 10)
        self.assertEqual(list(r.extra["windows"]["B"]["lines"]), ["2000"])


class D1Rows(unittest.TestCase):
    def test_d1_counts_unreachable_rows_at_the_bound(self):
        """D1 = mean |delta_D| pooled over fired rows with a meter; an unreachable row counts at its bound (the D1
        that gates) and D1 is also reported without it (decision 57; amendment D12)."""
        F = pops("fired", "fired_meter")
        evs = [ev(1, "2000", F, d1=d1p(0.05, 1.0)), ev(2, "2000", F, d1=d1p(-0.10, 1.0)),
               ev(3, "3000", F, d1=d1p(0.02, 1.0)), ev(4, "3000", F, d1=d1p(0.30, 1.0, bracketed=False))]
        r = S.row_D1(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.E, 100 * (0.05 + 0.10 + 0.02 + 0.30) / 4, places=9)
        self.assertAlmostEqual(r.without["unreachable"], 100 * (0.05 + 0.10 + 0.02) / 3, places=9)
        self.assertEqual(r.extra["unreachable"], [["t_steady", 4]])
        self.assertEqual(r.passes, True)                                    # 11.75 % against 16.6 %


class UTermsTests(unittest.TestCase):
    def line(self, tits=(800.0, 810.0, 820.0), egts=(805.0, 812.0, 829.0)):
        P = pops("fired", "hot", "hot_l1", "fired_l1")
        return [ev(i, "2000", P, tit=t, egt=g) for i, (t, g) in enumerate(zip(tits, egts))]

    def stat(self, row):
        return lambda evs: S._CORES[row](tuple(evs), V, None).comps["2000"]

    def test_u_num_of_a_mean_is_the_demeaned_scatter_over_n(self):
        """u_num: per row the 0.125 deg change, the population's mean removed: for a mean, SD/sqrt(n) with SD of
        ddof 1 (PLAN.md 6.2; WP3's second fix of 23 October 2026: it read sqrt((n-1)/n) of it): changes 0.3,
        0.1, -0.1 give SD 0.2, so 0.2/sqrt(3), which is sqrt(0.08)/3 x sqrt(3/2) -- d3_rows' u_num on the same
        changes, the control that the two definitions agree; evaluations at one crank step twice are refused."""
        evs = self.line()
        fine = {S._key(e): replace(e, dtheta=0.125, out=replace(e.out, egt_c=e.out.egt_c + d))
                for e, d in zip(evs, (0.3, 0.1, -0.1))}
        u, sd = S.u_num(self.stat("E3a"), evs, fine)
        self.assertAlmostEqual(u, 0.2 / math.sqrt(3), places=12)
        self.assertAlmostEqual(u, math.sqrt(0.08) / 3 * math.sqrt(1.5), places=12)
        self.assertAlmostEqual(u, S.u_stat_line([0.3, 0.1, -0.1]), places=12)      # SD/sqrt(n), d3_rows' reading
        self.assertAlmostEqual(sd, u * math.sqrt(3), places=12)
        same = {S._key(e): replace(e, dtheta=0.25) for e in evs}
        with self.assertRaises(ValueError):
            S.u_num(self.stat("E3a"), evs, same)
        # control: a uniform change is absorbed entirely
        flat = {S._key(e): replace(e, dtheta=0.125, out=replace(e.out, egt_c=e.out.egt_c + 0.7)) for e in evs}
        self.assertAlmostEqual(S.u_num(self.stat("E3a"), evs, flat)[0], 0.0, places=12)

    def test_u_input_is_the_central_difference_of_the_whole_statistic(self):
        """With each row's TIT error moved by +-k under the MAP channel, a mean's u_input is sqrt(n k^2)/n; a
        shifted evaluation that does not carry exactly +-u_j is refused (mistake 19)."""
        evs = self.line()
        unc = u_inputs(evs, effect=lambda e, ch: 0.4 if ch == "map" else 0.0)
        u = S.u_input(self.stat("E3a"), evs, unc.shifted, terms=unc.input_terms)
        self.assertAlmostEqual(u, math.sqrt(3 * 0.4 ** 2) / 3, places=12)
        bad = dict(unc.shifted)
        k = ("map", 1, S._key(evs[0]))
        bad[k] = replace(bad[k], shift=S.InputShift("map", 0.01))
        with self.assertRaises(ValueError):
            S.u_input(self.stat("E3a"), evs, bad, terms=unc.input_terms)

    def test_u_d_common_and_random_parts(self):
        """The thermocouple's 0.0075 |t| / sqrt(3), common, moves a TIT mean by its own mean; the meter, random, by
        sqrt(sum (d_i / n)^2); an unpinned term refuses (control: pinned, it computes)."""
        evs = self.line()
        u = S.u_d(self.stat("E3a"), evs, channels=("tit",), terms=D_TERMS)
        self.assertAlmostEqual(u, 0.0075 / math.sqrt(3) * 810.0, places=9)
        M = pops("fired", "fired_meter", "hot", "hot_meter")
        mev = [ev(i, "2000", M, meter=m, F_m=f) for i, (m, f) in enumerate(((5.0, 5.1), (4.0, 3.9), (6.0, 6.3)))]
        st = lambda evs: S._CORES["E2a"](tuple(evs), V, None).comps["2000"]     # noqa: E731
        hand = math.sqrt(sum((100 * (f / (m + 0.01) - f / m) / 3) ** 2 for m, f in ((5.0, 5.1), (4.0, 3.9), (6.0, 6.3))))
        self.assertAlmostEqual(S.u_d(st, mev, channels=("meter",), terms=D_TERMS), hand, places=10)
        with self.assertRaises(S.UnpinnedUncertainty):
            S.u_d(st, mev, channels=("meter",))
        with self.assertRaises(S.UnpinnedUncertainty):
            S.u_d(st, mev)

    def test_held_out_e1a_end_to_end_through_the_toy(self):
        """The toy model evaluated at 0.25 and 0.125 deg and under every +-u_j shift; held_out_row gives each line
        u_val = sqrt(u_num^2 + u_input^2 + u_D^2), its u_input the hand value sqrt(sum_c sum_j (100 a_j u_j /
        (T_E n))^2) from the toy's torque sensitivities, its label from line_label, and the same E as row_E1a."""
        toy = Toy(bias=0.02)
        H = pops("fired", "fired_meter", "hot", "hot_meter")
        rows = [prow(source_row=10 + i, line=ln, speed_rpm=sp, map_kpa=mp, torque_nm=te, pops=H)
                for i, (ln, sp, mp, te) in enumerate((("2000", 2000.0, 120.0, 168.0), ("2000", 2010.0, 125.0, 172.0),
                                                      ("2000", 1995.0, 130.0, 186.0), ("3000", 3000.0, 140.0, 200.0),
                                                      ("3000", 3005.0, 150.0, 214.0), ("3000", 2990.0, 160.0, 228.0)))]

        def run(dtheta, shift=None):
            return [S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=dtheta,
                                                    needs={"at_epa"}, shift=shift)) for r in rows]
        base = run(0.25)
        fine = {S._key(e): e for e in run(0.125)}
        shifted = {}
        for ch, sg, sh in S.input_shifts():
            for e in run(0.25, sh):
                shifted[(ch, sg, S._key(e))] = e
        unc = S.UncertaintyInputs(evals_0125=fine, shifted=shifted, common_lam=None, input_terms=S.U_INPUT,
                                  d_terms=D_TERMS)
        h = S.held_out_row("E1a", base, view=V, tightening=None, unc=unc)
        r = S.row_E1a(base, view=V, stage="held_out", tightening=None)
        self.assertAlmostEqual(h.E, r.E, places=12)
        a = {"speed": 0.01, "map": 1.5, "spark": 0.8}
        for ls in h.lines:
            u = ls.u
            self.assertAlmostEqual(u.u_val, math.sqrt(u.u_num ** 2 + u.u_input ** 2 + u.u_D ** 2), places=12)
            mem = [x for x in rows if x.line == ls.line]
            hand = math.sqrt(sum((100 * a[j] * S.U_INPUT[j].value / (x.torque_nm * 3)) ** 2 for x in mem for j in a))
            self.assertAlmostEqual(u.u_input, hand, places=9)
            self.assertGreater(u.u_num, 0.0)
            self.assertEqual((ls.label, ls.certifies), S.line_label(ls.E, u.u_val, u.u_stat, 1.9))
            self.assertIn("u_input speed", u.unsourced)
        self.assertEqual(h.label, S.row_label([ls for ls in h.lines if ls.line in h.deciding]))
        self.assertAlmostEqual(h.kappa, S.kappa(h.E, h.u.u_val, 1.9, h.label), places=12)
        json.dumps(h.as_json(), allow_nan=False)
        json.dumps(r.as_json(), allow_nan=False)


class Section7AndE6(unittest.TestCase):
    def res(self, row, **kw):
        base = dict(row=row, stage="held_out", R=16.6, unit="%", kind=S.KIND.get(row, "d"), E=1.0, lines=(),
                    deciding=("pooled",), certifying=("pooled",), worst_line=None, u=None, label="validated",
                    kappa=1.0, passes=None, no_statistic=False, reason=None, without={}, coverage_restricted=None,
                    extra={}, n_rows=5, n_clusters=5)
        base.update(kw)
        return S.StatResult(**base)

    def test_a_part_with_two_rows_takes_the_larger_kappa(self):
        """P5 (C3b and C3d, the Mazda's): a part takes its rows' larger kappa (contract section 7; the fourth
        contract review's mutant m30, min for max, survived: every part test had one row or none). The control:
        the rows swapped give the same."""
        for kb, kd in ((1.4, 1.1), (1.1, 1.4)):
            res = {"C3b": self.res("C3b", label="limited", kappa=kb), "C3d": self.res("C3d", label="limited", kappa=kd)}
            s7 = S.section7(res, engine="synth", unsnapped={}, excluded_every={})
            self.assertEqual(s7["parts"]["P5"], 1.4)

    def test_a_move_equal_to_u_val_is_not_an_exclusion(self):
        """Excluded only when the probed statistic moves by strictly less than its own u_val (contract section 4,
        E6; the contract review's mutant m31, < to <=, survived): u_val 0.25 (0.0625 + 0 + 0, exact), a move of
        exactly 0.25 is not an exclusion, one a hair below it is."""
        u = S.combine(0.0, 0.25, 0.0, 0.05, ())
        self.assertEqual(u.u_val, 0.25)
        base = self.res("E3a", E=2.0, u=u)
        self.assertFalse(S.excluded_for(base, self.res("E3a", E=2.25)))
        self.assertTrue(S.excluded_for(base, self.res("E3a", E=2.0 + (0.25 - 2.0 ** -40))))

    def test_drops_bands_and_d1s_two_readings(self):
        """An off d row and a d row with no statistic write DROP; a part's kappa is its rows'; D1 under E6 row 12
        takes the worse label and the larger kappa; the level rows give the 850 C row's label (the worst)."""
        results = {"D1": self.res("D1"), "E4b": self.res("E4b", label="limited", kappa=1.25),
                   "L1": self.res("L1", label="off", kappa=3.0),
                   "E8": self.res("E8", no_statistic=True, label=None, kappa=None, reason="ds short"),
                   "E1a": self.res("E1a", kind="level", label="limited"), "E3a": self.res("E3a", kind="level", label="validated")}
        s7 = S.section7(results, engine="synth", unsnapped={"D1": self.res("D1", label="limited", kappa=1.3)},
                        excluded_every={})
        self.assertEqual(s7["drop_rows"], ["L1", "E8"])
        self.assertTrue(s7["drop"])
        # P5 has no row on this engine: a string, never a number a six-part sum could read as 0
        self.assertEqual(s7["parts"], {"P1": 1.3, "P2": 1.25, "P3": "DROP", "P4": "DROP", "P5": S.PART_WITHOUT_ROW})
        self.assertIsInstance(s7["parts"]["P5"], str)
        self.assertEqual(s7["d"]["D1"]["label"], "limited")
        self.assertEqual(s7["level_850c_label"], "limited")
        self.assertEqual(set(s7["level_rows_without_statistic"]), {"E2a", "E4a", "L0"})
        clean = S.section7({"D1": self.res("D1")}, engine="synth", unsnapped={}, excluded_every={})
        self.assertFalse(clean["drop"])
        ex = S.section7({"D1": self.res("D1")}, engine="synth", unsnapped={}, excluded_every={"D1": True})
        self.assertEqual(ex["drop_rows"], ["D1"])

    def test_e6_row_12_both_ways_for_the_850c_row(self):
        """E6 row 12 (contract section 4): E3a and L0 labelled by the worse of their snapped and unsnapped
        readings for the 850 C row, D1 too with the larger kappa; reported_labels the same (WP3's fix of 23
        October 2026). The control: with an unsnapped reading that is as good, the snapped label stands."""
        def lev(row, lab):
            return self.res(row, kind="level", label=lab)
        results = {"E3a": lev("E3a", "validated"), "L0": lev("L0", "validated"), "E1a": lev("E1a", "validated")}
        worse = {"E3a": lev("E3a", "limited"), "L0": lev("L0", "validated")}
        s7 = S.section7(results, engine="synth", unsnapped=worse, excluded_every={})
        self.assertEqual(s7["level"]["E3a"], "limited")
        self.assertEqual(s7["level_850c_label"], "limited")
        rep_ = S.reported_labels(results, unsnapped=worse, excluded_every={})
        self.assertEqual((rep_["E3a"]["label"], rep_["E1a"]["label"]), ("limited", "validated"))
        # a row excluded for every constant it claims to test reads no label and no kappa, as section 7 reads
        # it (WP3's second fix of 23 October 2026); the control is the call above
        ex = S.reported_labels(results, unsnapped=worse, excluded_every={"E1a": True})
        self.assertEqual((ex["E1a"]["label"], ex["E1a"]["kappa"]), (None, None))
        self.assertIn("excluded for every constant", ex["E1a"]["how"])
        same = S.section7(results, engine="synth", unsnapped={"E3a": lev("E3a", "validated")}, excluded_every={})
        self.assertEqual(same["level_850c_label"], "validated")
        # an unsnapped reading without a statistic cannot make the row worse: the snapped reading alone
        none = S.section7(results, engine="synth", unsnapped={"E3a": self.res("E3a", no_statistic=True, label=None)},
                          excluded_every={})
        self.assertEqual(none["level"]["E3a"], "validated")

    def test_a_level_row_excluded_for_every_constant_has_no_statistic(self):
        """The contract (section 4, E6): a row excluded for every constant it claims to test "has no statistic
        and counts as such in section 7" -- a level row too (E4a: both its members perturbed). The control: not
        excluded, it gives its label to the 850 C row."""
        results = {"E4a": self.res("E4a", kind="level", label="off"), "E1a": self.res("E1a", kind="level")}
        on = S.section7(results, engine="synth", unsnapped={}, excluded_every={"E4a": True})
        self.assertIsNone(on["level"]["E4a"])
        self.assertIn("E4a", on["level_rows_without_statistic"])
        self.assertEqual(on["level_850c_label"], "validated")
        off = S.section7(results, engine="synth", unsnapped={}, excluded_every={"E4a": False})
        self.assertEqual(off["level_850c_label"], "off")

    def test_a_narrow_band_that_is_not_validated_is_flagged(self):
        """kappa = (|E| + 2u_val)/R can fall below 1 on a row that is not validated (2u_stat > R): a band
        narrower than a validated row's, which section 7 does not write; flagged, never changed (the contract
        gap is the team's). The control: a validated row with kappa 1 is not flagged."""
        s7 = S.section7({"E4b": self.res("E4b", label="untested", kappa=0.4), "D1": self.res("D1")}, engine="synth",
                        unsnapped={}, excluded_every={})
        self.assertEqual(s7["kappa_below_1_not_validated"], ["E4b"])
        self.assertTrue(s7["d"]["E4b"]["kappa_below_1_not_validated"])
        self.assertFalse(s7["d"]["D1"]["kappa_below_1_not_validated"])

    TESTS = {"E1a": [{"member": "burn", "perturbed_by_E6_row": None}, {"member": "FMEP", "perturbed_by_E6_row": None},
                     {"member": "back-pressure", "perturbed_by_E6_row": 5}],
             "E4a": [{"member": "UA_PORT", "perturbed_by_E6_row": 6}, {"member": "rich slope", "perturbed_by_E6_row": 9}],
             "E8": []}

    def test_the_tests_list_counting_rule(self):
        """Decision 59 (amendment E4): excluded for every listed constant only if every member is perturbed and
        excluded; a member no E6 row perturbs counts as not excluded; E8 is never excluded; a perturbed member
        without a recorded exclusion is refused."""
        f = S.excluded_for_every_listed_constant
        self.assertFalse(f("E1a", {"back-pressure": True}, tests_lists=self.TESTS))
        self.assertTrue(f("E4a", {"UA_PORT": True, "rich slope": True}, tests_lists=self.TESTS))
        self.assertFalse(f("E4a", {"UA_PORT": True, "rich slope": False}, tests_lists=self.TESTS))
        self.assertFalse(f("E8", {}, tests_lists=self.TESTS))
        with self.assertRaises(KeyError):
            f("E4a", {"UA_PORT": True}, tests_lists=self.TESTS)

    def test_exclusion_and_the_refit_rows(self):
        u = S.combine(0.1, 0.2, 0.2, 0.05, ())
        base = self.res("E3a", E=2.0, u=u)
        self.assertTrue(S.excluded_for(base, self.res("E3a", E=2.2)))      # |0.2| < u_val 0.3
        self.assertFalse(S.excluded_for(base, self.res("E3a", E=2.4)))     # control
        mm = S.must_not_move({"D1": base}, {"D1": self.res("D1", E=2.5)}, ["D1"])
        self.assertEqual(mm["D1"][2], False)
        self.assertAlmostEqual(S.refit_movement({"E1a": base}, {"E1a": self.res("E1a", E=1.5)})["E1a"], -0.5, places=12)
        self.assertAlmostEqual(u.u_val, 0.3, places=15)
        self.assertIsNone(u.u_num_sd_undivided)


class InSampleStage(unittest.TestCase):
    def evals(self, e1a_error, e8_lam_diff, final_error=0.0):
        H = pops("fired", "hot")
        evs = [ev(i, "2000", H, T_m=200.0 * (1 + e1a_error / 100)) for i in range(3)]
        evs += [ev(10 + i, "2000", pops("fired", "hot"), kind="final", T_m=200.0 * (1 + final_error / 100), lam=0.9,
                   ecu=S.EcuOut(spark_btdc=10.0, lam=0.9 + e8_lam_diff, cam_deg=None)) for i in range(3)]
        return evs

    def test_t0s_noise_edge(self):
        """within_noise's edge is inclusive: |E| = R + z u_stat is consistent, a hair beyond it is not (the fourth
        tests review's sweep found <= at the edge untested)."""
        stage = S.in_sample(self.evals(5.0, 0.0), view=V)
        R = stage.results["E1a"].R
        edge = R + 2.0 * 0.5
        at = replace(stage, scatter={**stage.scatter, "E1a": {"2000": (edge, 0.5)}})
        self.assertNotIn("E1a", S.within_noise(at, z=2.0)["beyond"])
        past = replace(stage, scatter={**stage.scatter, "E1a": {"2000": (math.nextafter(edge, math.inf), 0.5)}})
        self.assertIn("E1a", S.within_noise(past, z=2.0)["beyond"])

    def test_e8_is_outside_the_criterion_and_no_line_neither_blocks_nor_passes(self):
        """A form passes when no statistic but E8 fails (decisions 39(a), 55, 77); E8 is computed and reported, and
        carries no decision 77 judgement; a statistic with no calibration line neither blocks nor passes. Control:
        an E1a whose failure exceeds its noise fails the form (six rows at +5 %: u_stat 0, and 5 - 0 > 1.9)."""
        ok = S.in_sample(self.evals(1.0, 0.05), view=V)
        self.assertTrue(ok.passes)
        self.assertFalse(ok.results["E8"].passes)
        self.assertIsNone(ok.results["E8"].judgement)
        self.assertIn("E2a", ok.no_line)
        bad = S.in_sample(self.evals(5.0, 0.0, final_error=5.0), view=V)
        self.assertEqual((bad.passes, bad.failing, bad.noise), (False, ("E1a",), ()))
        self.assertEqual(bad.results["E1a"].judgement["u_stat"], 0.0)
        json.dumps(bad.as_json(), allow_nan=False)
        with self.assertRaises(ValueError):
            S.in_sample(self.evals(1.0, 0.0) + [ev(99, "2000", None, kind="initial")], view=V)

    def test_t0s_noise_reading(self):
        """within_noise (T0's diagnostic, WP3's fix of 23 October 2026): a component within R + z u_stat is
        consistent with the form though |E| > R; one beyond it is not (the control). The same stage under decision
        77: E1a's six rows (+5 % three times, 0 three times) give E 2.5 % and u_stat sqrt(1.25) = 1.118, so
        2 u_stat = 2.236 > 1.9: its noise exceeds R, and it neither blocks nor passes."""
        stage = S.in_sample(self.evals(5.0, 0.0), view=V)               # E1a beyond R, within its noise ...
        self.assertEqual((stage.failing, stage.noise, stage.passes), ((), ("E1a",), True))
        self.assertAlmostEqual(stage.results["E1a"].judgement["u_stat"], math.sqrt(1.25), places=12)
        E, se = stage.scatter["E1a"]["2000"]
        self.assertGreater(abs(E), 1.9)
        self.assertLessEqual(abs(E), 1.9 + 2.576 * se)                  # ... within its own scatter
        self.assertTrue(S.within_noise(stage, z=2.576)["ok"])
        self.assertEqual(S.within_noise(stage, z=0.0)["beyond"], ["E1a"])
        quiet = replace(stage, scatter={**stage.scatter, "E1a": {"2000": (E, 0.0)}})
        self.assertEqual(S.within_noise(quiet, z=2.576)["beyond"], ["E1a"])   # no scatter: the strict test

    def test_one_definition_for_both_stages(self):
        """Mistake 10: the in-sample and held-out values of a row on the same evaluations are the same number."""
        evs = e1a_set()
        a = S.row_E1a(evs, view=V, stage="in_sample", tightening=None)
        b = S.row_E1a(evs, view=V, stage="held_out", tightening=None)
        self.assertEqual(a.E, b.E)
        with self.assertRaises(ValueError):
            S.row_E1a(evs, view=V, stage="in_sample", tightening={"plant": "b58"})

    def test_coverage_flag_and_the_restricted_reading(self):
        """Decision 58: a held-out row whose MAP band holds no calibration row of its population is flagged, and
        the statistic is also reported restricted to the coverage, beside it."""
        H = pops("fired", "hot")
        evs = [ev(i, "2000", H, T_m=202.0, map_kpa=125.0) for i in range(3)] + [ev(9, "2000", H, T_m=240.0, map_kpa=250.0)]
        marked = S.mark_coverage(evs, view=V)
        self.assertEqual([("outside_calibration_map_coverage" in e.flags) for e in marked], [False] * 3 + [True])
        r = S.row_E1a(marked, view=V, stage="held_out", tightening=None)
        self.assertAlmostEqual(r.E, (1 + 1 + 1 + 20) / 4, places=10)
        self.assertAlmostEqual(r.coverage_restricted, 1.0, places=10)


# =============================================================================================
class InSampleRule(unittest.TestCase):
    """Decision 77 (23 October 2026): an in-sample statistic fails a form only if |E_cal| - 2 u_stat > R, u_stat the
    held-out run's; one whose 2 u_stat > R neither blocks nor passes, recorded per form. Hand answers for the three
    outcomes on one component, on a per-line row (E1a, R 1.9 %) and on a pooled row (D1, R 16.6 %), each "neither"
    and "passes" with the control that the literal |E_cal| <= R fails it, so the ladder would have climbed."""
    H = pops("fired", "hot")                   # E1a's population only: no meter, so E2a, D1 and L0 have no line
    F = pops("fired", "fired_meter")

    def e1a_line(self, line, errors, n0):
        return [ev(n0 + i, line, self.H, T_m=200.0 * (1.0 + x / 100.0)) for i, x in enumerate(errors)]

    def d1_rows(self, deltas):
        return [ev(1 + i, "2000", self.F, d1=d1p(d, 1.0)) for i, d in enumerate(deltas)]

    def test_a_failure_beyond_its_noise_fails_whatever_its_noise(self):
        """Decision 77's reading (a): a statistic with |E| - 2u > R fails even though 2u > R (the fourth tests
        review swapped the two checks of in_sample_outcome and no hand test failed): 10 - 4 = 6 > 2 with 2u = 4 > 2
        fails; on one E1a line, errors 20, 25, 30 % give E 25, u 5/sqrt(3) = 2.887, 2u = 5.77 > 1.9 and 25 - 5.77 >
        1.9: fails. The control: the swapped order reads both as neither."""
        self.assertEqual(S.in_sample_outcome(10.0, 2.0, 2.0), ("fails", S.FAILS_BEYOND_NOISE))
        r = S.row_E1a(self.e1a_line("2000", (20.0, 25.0, 30.0), 1), view=V, stage="in_sample", tightening=None)
        j = r.judgement
        self.assertAlmostEqual(r.E, 25.0, places=10)
        self.assertAlmostEqual(j["u_stat"], 5.0 / math.sqrt(3.0), places=10)
        self.assertGreater(2.0 * j["u_stat"], 1.9)
        self.assertEqual((j["outcome"], j["why"]), ("fails", S.FAILS_BEYOND_NOISE))
        self.assertFalse(r.passes)

    def test_the_rule_on_one_component(self):
        """in_sample_outcome by hand (R 2.0, exact binary numbers): fails when |E| - 2u > R; neither when it does
        not and 2u > R; passes otherwise; the edges on line_label's side (|E| - 2u = R does not fail, 2u = R does
        not exceed R); no u_stat (None or NaN) neither; a non-finite E fails; a negative u_stat is refused."""
        f = S.in_sample_outcome
        self.assertEqual(f(5.0, 0.5, 2.0), ("fails", S.FAILS_BEYOND_NOISE))           # 5 - 1 = 4 > 2
        self.assertEqual(f(-2.5, 1.25, 2.0), ("neither", S.NOISE_EXCEEDS_R))          # 2.5 - 2.5 = 0; 2.5 > 2
        self.assertEqual(f(2.5, 0.5, 2.0), ("passes", None))                         # 2.5 - 1 = 1.5; 1 <= 2
        for E in (2.5, -2.5):                                    # the controls: the literal rule fails both
            self.assertFalse(abs(E) <= 2.0)
        self.assertEqual(f(3.0, 0.5, 2.0)[0], "passes")                              # 3 - 1 = 2 = R: not > R
        self.assertEqual(f(3.0 + 2.0 ** -40, 0.5, 2.0)[0], "fails")                  # just beyond the edge
        self.assertEqual(f(1.0, 1.0, 2.0)[0], "passes")                              # 2u = 2 = R: not > R
        self.assertEqual(f(1.0, 1.0 + 2.0 ** -40, 2.0), ("neither", S.NOISE_EXCEEDS_R))
        self.assertEqual(f(40.0, None, 2.0), ("neither", S.NO_U_STAT))
        self.assertEqual(f(40.0, float("nan"), 2.0), ("neither", S.NO_U_STAT))
        self.assertEqual(f(float("nan"), 0.1, 2.0)[0], "fails")
        self.assertEqual(f(1.0, float("inf"), 2.0), ("neither", S.NOISE_EXCEEDS_R))
        with self.assertRaises(ValueError):
            f(1.0, -0.1, 2.0)

    def test_a_per_line_row_by_hand(self):
        """E1a on one line, three rows each (u_stat = SD/sqrt(3)): errors 4, 5, 6 % give E 5, u 1/sqrt(3) and
        5 - 1.155 > 1.9, fails; 0, 2.5, 5 give E 2.5, u 2.5/sqrt(3) = 1.443, 2u = 2.887 > 1.9, neither; 1.5, 2.1,
        2.7 give E 2.1, u 0.6/sqrt(3) = 0.346, 2.1 - 0.693 = 1.407 <= 1.9 and 2u <= 1.9, passes. The last two
        fail |E| <= 1.9 (the controls)."""
        cases = {"fails": ((4.0, 5.0, 6.0), 5.0, 1.0 / math.sqrt(3.0)),
                 "neither": ((0.0, 2.5, 5.0), 2.5, 2.5 / math.sqrt(3.0)),
                 "passes": ((1.5, 2.1, 2.7), 2.1, 0.6 / math.sqrt(3.0))}
        for want, (errors, E, u) in cases.items():
            r = S.row_E1a(self.e1a_line("2000", errors, 1), view=V, stage="in_sample", tightening=None)
            j = r.judgement
            self.assertEqual(j["outcome"], want, errors)
            self.assertAlmostEqual(r.E, E, places=10)
            self.assertAlmostEqual(j["u_stat"], u, places=10)
            self.assertEqual((j["component"], j["R"], set(j["components"])), ("2000", 1.9, {"2000"}))
            self.assertEqual(r.passes, S.IN_SAMPLE_PASSES[want])
            if want != "fails":
                self.assertGreater(abs(r.E), r.R)                     # the literal criterion fails it
            js = r.as_json()
            self.assertEqual((js["outcome"], js["R"]), (want, 1.9))
            self.assertAlmostEqual(js["u_stat"], u, places=10)
            self.assertEqual(js["components"]["2000"]["outcome"], want)
            json.dumps(js, allow_nan=False)
        self.assertEqual(S.row_E1a(self.e1a_line("2000", (0.0, 2.5, 5.0), 1), view=V, stage="in_sample",
                                   tightening=None).judgement["why"], S.NOISE_EXCEEDS_R)

    def test_the_lines_of_a_per_line_row(self):
        """Held-out row_label's structure: a row fails if any deciding line fails, passes if none fails and one
        passes, neither if every deciding line's noise exceeds R; its E and u_stat are the worst line's (decision
        57), here the noisy line 1750 (|2.5| > |2.1|); a line of 2 rows does not decide. The u_stat of each line is
        the one held_out_row labels it with (mistake 10)."""
        noisy = self.e1a_line("1750", (0.0, 2.5, 5.0), 1)
        quiet = self.e1a_line("2500", (1.5, 2.1, 2.7), 10)
        bad = self.e1a_line("3500", (4.0, 5.0, 6.0), 20)
        short = self.e1a_line("4000", (50.0, 60.0), 30)                   # 2 clusters: no line, decides nothing
        r = S.row_E1a(noisy + quiet + short, view=V, stage="in_sample", tightening=None)
        j = r.judgement
        self.assertEqual((j["outcome"], j["component"], set(j["components"])), ("passes", "1750", {"1750", "2500"}))
        self.assertEqual({c: v["outcome"] for c, v in j["components"].items()}, {"1750": "neither", "2500": "passes"})
        self.assertAlmostEqual(j["u_stat"], 2.5 / math.sqrt(3.0), places=10)
        self.assertIsNone(j["why"])
        r2 = S.row_E1a(noisy + quiet + bad, view=V, stage="in_sample", tightening=None)
        self.assertEqual((r2.judgement["outcome"], r2.judgement["component"]), ("fails", "3500"))
        self.assertEqual(r2.judgement["why"], "3500: " + S.FAILS_BEYOND_NOISE)
        r3 = S.row_E1a(noisy + short, view=V, stage="in_sample", tightening=None)
        self.assertEqual((r3.judgement["outcome"], r3.passes), ("neither", None))
        self.assertEqual(r3.judgement["why"], S.NOISE_EXCEEDS_R)              # one component: its own why
        evs = noisy + quiet + bad
        h = S.held_out_row("E1a", evs, view=V, tightening=None, unc=u_inputs(evs, effect=lambda e, ch: 0.0))
        for ls in h.lines:
            self.assertEqual(ls.u.u_stat, r2.judgement["components"][ls.line]["u_stat"], ls.line)

    def test_a_line_that_fails_behind_a_worse_noisier_one_still_fails(self):
        """Decision 77's reading (b), the misreading it excludes ("testing the worst line alone ... would let a line
        that fails beyond its noise pass behind a worse but noisier one"; WP3's third fix of 24 October 2026, on the
        test review's mutation m1, which judged the worst line alone and survived every test): the worst line
        1750 (errors 0, 6, 12: E 6, u 6/sqrt(3), 2u = 6.93 > 1.9) neither blocks nor passes, and the quieter 2500
        (4, 5, 6: E 5, u 0.577, 5 - 1.155 > 1.9) fails beyond its noise: the statistic fails, reported at the worst
        line, the why naming 2500. The control: the worst line's own outcome is "neither"."""
        worst = self.e1a_line("1750", (0.0, 6.0, 12.0), 1)
        failing = self.e1a_line("2500", (4.0, 5.0, 6.0), 10)
        r = S.row_E1a(worst + failing, view=V, stage="in_sample", tightening=None)
        j = r.judgement
        self.assertEqual(r.worst_line, "1750")
        self.assertEqual((j["outcome"], j["component"]), ("fails", "1750"))
        self.assertEqual({c: v["outcome"] for c, v in j["components"].items()}, {"1750": "neither", "2500": "fails"})
        self.assertEqual(j["why"], "2500: " + S.FAILS_BEYOND_NOISE)
        self.assertAlmostEqual(j["E"], 6.0, places=10)
        self.assertAlmostEqual(j["u_stat"], 6.0 / math.sqrt(3.0), places=10)
        self.assertFalse(r.passes)
        # the same on in_sample_judgement directly, with the control that the reported line alone reads neither
        d = S.in_sample_judgement({"1750": (6.0, 4.0), "2500": (5.0, 0.2)}, 1.9, report="1750")
        self.assertEqual((d["outcome"], d["component"], d["why"]), ("fails", "1750", "2500: " + S.FAILS_BEYOND_NOISE))
        self.assertEqual(S.in_sample_outcome(6.0, 4.0, 1.9), ("neither", S.NOISE_EXCEEDS_R))

    def test_a_pooled_row_by_hand(self):
        """D1 pooled (u_stat = SD/sqrt(n) of the |delta_D| in percent): 30, 32, 34 % give E 32, u 2/sqrt(3) and
        32 - 2.309 > 16.6, fails; 5, 10, 45 % give E 20, u sqrt(475)/sqrt(3) = 12.58, 2u = 25.2 > 16.6, neither;
        15, 18, 21 % give E 18, u sqrt(3) and 18 - 3.464 = 14.5 <= 16.6, 2u <= 16.6, passes. The last two fail
        |E| <= 16.6 (the controls)."""
        cases = {"fails": ((0.30, 0.32, 0.34), 32.0, 2.0 / math.sqrt(3.0)),
                 "neither": ((0.05, 0.10, 0.45), 20.0, math.sqrt(475.0) / math.sqrt(3.0)),
                 "passes": ((0.15, 0.18, 0.21), 18.0, math.sqrt(3.0))}
        for want, (deltas, E, u) in cases.items():
            r = S.row_D1(self.d1_rows(deltas), view=V, stage="in_sample", tightening=None)
            j = r.judgement
            self.assertEqual((j["outcome"], j["component"], set(j["components"])), (want, "pooled", {"pooled"}), deltas)
            self.assertAlmostEqual(r.E, E, places=9)
            self.assertAlmostEqual(j["u_stat"], u, places=9)
            self.assertEqual(j["u_stat"], S._core_D1(tuple(self.d1_rows(deltas)), V, None).comp_se["pooled"])
            if want != "fails":
                self.assertGreater(abs(r.E), r.R)

    def test_e4b_without_a_standard_error_neither_blocks_nor_passes(self):
        """E4b on one enriched row has no u_stat (the held-out run's None: epa_fit.NO_STATISTIC_OUTCOMES), so it
        cannot pass, and its failure cannot be shown to exceed its noise: neither. By hand: e-hat 0.1 MAP - 8 = 10 K
        at 180 kPa, L_S = 845 - 795 = 50 K, e_enr = -5 K, eps = 50 / (50 - 5 - 10) - 1 = 42.9 % > 16.6 % (the
        literal rule fails it); the control: a second enriched row gives a u_stat and a judgement by it."""
        B = pops("fired", "fired_meter", "l1_boost", "hot", "hot_l1")
        N = pops("fired", "fired_meter", "hot", "hot_enr")
        evs = [ev(1 + i, "2500", B, map_kpa=m, egt=800.0 + y) for i, (m, y) in enumerate(zip((100, 120, 140), (2, 4, 6)))]
        evs += [ev(10, "2500", N, map_kpa=180.0, egt=795.0, lam1=mo(egt=845.0), lam=0.85)]
        r = S.row_E4b(evs, view=V, stage="in_sample", tightening=None)
        self.assertAlmostEqual(r.E, 100.0 * (50.0 / 35.0 - 1.0), places=10)
        self.assertGreater(abs(r.E), r.R)
        self.assertEqual((r.judgement["outcome"], r.judgement["u_stat"], r.judgement["why"], r.passes),
                         ("neither", None, S.NO_U_STAT, None))
        two = evs + [ev(11, "2500", N, map_kpa=200.0, egt=797.0, lam1=mo(egt=857.0), lam=0.82)]
        r2 = S.row_E4b(two, view=V, stage="in_sample", tightening=None)
        self.assertIsNotNone(r2.judgement["u_stat"])
        self.assertEqual(r2.judgement["outcome"], S.in_sample_outcome(r2.E, r2.judgement["u_stat"], r2.R)[0])

    def test_l0_and_l1_take_the_held_out_u_stat(self):
        """L0's u_stat is each line's at its own maximising f, L1's from its two extreme lines at the spread's f
        (the cores' comp_se, which test_l0_and_l1_on_rows checks by hand): the judgement reads exactly those."""
        evs, _ = HousingBounds.l0_rows(None)
        r0 = S.row_L0(evs, view=V, stage="in_sample", tightening=None)
        c0 = S._core_L0(tuple(evs), V, None)
        self.assertEqual({c: v["u_stat"] for c, v in r0.judgement["components"].items()},
                         {ln: c0.comp_se[ln] for ln in c0.deciding})
        r1 = S.row_L1(evs, view=V, stage="in_sample", tightening=None)
        self.assertEqual((r1.judgement["component"], r1.judgement["u_stat"]),
                         ("L1", S._core_L1(tuple(evs), V, None).comp_se["L1"]))

    def test_the_form_moves_on_only_on_a_fails(self):
        """in_sample_stage, the form's reading: a form whose only failure under |E| <= R is noise passes, the
        statistic recorded in `noise` (as decision 55's gap is in `no_line`); the control, the literal criterion,
        would have failed it (and the ladder climbed); a statistic beyond its noise fails the form."""
        ins = S.in_sample(self.e1a_line("2000", (0.0, 2.5, 5.0), 1), view=V)
        self.assertEqual((ins.passes, ins.failing, ins.noise), (True, (), ("E1a",)))
        self.assertIn("E2a", ins.no_line)                                   # no meter population: no line
        self.assertNotIn("E1a", ins.no_line)
        literal = tuple(r for r in S.IN_SAMPLE_GATING if not ins.results[r].no_statistic
                        and not abs(ins.results[r].E) <= ins.results[r].R)
        self.assertEqual(literal, ("E1a",))
        self.assertEqual(ins.as_json()["noise"], ["E1a"])
        self.assertEqual(ins.as_json()["statistics"]["E1a"]["outcome"], "neither")
        bad = S.in_sample(self.e1a_line("2000", (4.0, 5.0, 6.0), 1), view=V)
        self.assertEqual((bad.passes, bad.failing, bad.noise), (False, ("E1a",), ()))
        # the aggregation refuses what the in-sample stage cannot have produced
        with self.assertRaises(ValueError):
            S.in_sample_stage({"E1a": replace(ins.results["E1a"], judgement=None)})
        with self.assertRaises(ValueError):
            S.in_sample_stage({"E1b": ins.results["E1a"]})
        with self.assertRaises(ValueError):
            S.in_sample_stage({"E1a": S.row_E1a(self.e1a_line("2000", (0.0, 2.5, 5.0), 1), view=V, stage="held_out",
                                                tightening=None)})


# =============================================================================================
class SecondFix(unittest.TestCase):
    """WP3's second fix of 23 October 2026, the contract review's findings, each by hand with its control."""

    def test_the_torque_target_term_moves_d1_through_its_inversion(self):
        """D1's u_D reads the torque reading through its inversion target: torque_target holds every member
        re-run through kernel_point with its torque moved by torque's u_D, the inversion re-run there; the
        random part is the statistic's change per cluster. On ToyModel's torque curve a moved target moves the
        inverted MAP and the fuel, so the term is not zero; the controls: an unpinned term refuses, a member
        shifted by another amount refuses, and without the mapping D1 refuses."""
        toy = Toy()
        rows = [prow(source_row=6 + i, speed_rpm=2000.0 + 10 * i, torque_nm=150.0 + 5 * i,
                     pops=pops("fired", "fired_meter")) for i in range(4)]
        pinned = dict(S.U_D, meter=S.UD(0.01, None, "random", "t", "t", True),
                      torque=S.UD(0.5, None, "random", "t", "t", True))

        def evals(shift):
            return tuple(S.kernel_point(toy, S.make_task(r, view=V, conventions=S.NOMINAL, dtheta=0.25,
                                                         needs={"at_epa", "d1"}, shift=shift)) for r in rows)
        base = evals(None)
        moved = {S._key(e): e for e in evals(S.torque_target_shift(pinned))}
        stat = lambda evs: S._CORES["D1"](tuple(evs), V, None).comps.get("pooled", 0.0)   # noqa: E731
        members = tuple(S._key(e) for e in base)
        u, _ = S.u_d_terms(stat, base, channels=("torque_target",), members=members, terms=pinned,
                           torque_target=moved)
        self.assertGreater(u, 0.0)
        self.assertNotEqual(moved[members[0]].d1.map_kpa, base[0].d1.map_kpa)
        with self.assertRaises(S.UnpinnedUncertainty):
            S.u_d_terms(stat, base, channels=("torque_target",), members=members, terms=S.U_D, torque_target=moved)
        other = {S._key(e): e for e in evals(S.InputShift("torque", 0.25))}
        with self.assertRaises(ValueError):
            S.u_d_terms(stat, base, channels=("torque_target",), members=members, terms=pinned, torque_target=other)
        with self.assertRaises(ValueError):
            S.u_d_terms(stat, base, channels=("torque_target",), members=members, terms=pinned)
        rel = dict(pinned, torque=S.UD(None, 0.002, "random", "t", "t", True))
        self.assertEqual(S.torque_target_shift(rel), S.InputShift("torque_rel", 0.002))

    def test_a_u_stat_of_none_never_certifies(self):
        """combine keeps a u_stat of None; line_label then certifies nothing (E4b on one enriched row): the row
        reads untested unless it is off. The control: the same with a u_stat certifies."""
        u = S.combine(0.1, 0.1, 0.1, None, ())
        self.assertIsNone(u.u_stat)
        self.assertEqual(u.as_json()["u_stat"], None)
        lab, cert = S.line_label(1.0, u.u_val, u.u_stat, 10.0)
        self.assertEqual((lab, cert), ("validated", False))
        self.assertEqual(S.row_label([S.LineStat(line="pooled", clusters=1, E=1.0, u=u, label=lab, certifies=cert)]),
                         "untested")
        self.assertEqual(S.line_label(1.0, u.u_val, 0.1, 10.0), ("validated", True))
        self.assertEqual(S.line_label(30.0, u.u_val, None, 10.0)[0], "off")

    def test_e4b_on_one_enriched_row_has_no_pooled_u_stat(self):
        """E4b's pooled u_stat is None below 2 enriched rows (its regression term alone could certify it), and
        a value with 2 (the control)."""
        def set_(n_enr):
            out = []
            for i, m in enumerate((105.0, 125.0, 145.0)):
                out.append(ev(i, "2000", pops("fired", "hot", "hot_l1", "l1_boost", "fired_l1"), tit=800.0 + i,
                              egt=801.0 + 2 * i, map_kpa=m))
            for j in range(n_enr):
                e = ev(10 + j, "2000", pops("fired", "hot", "hot_enr"), tit=850.0 + j, egt=845.0 + j, map_kpa=150.0 + j)
                out.append(replace(e, lam1=replace(e.out, egt_c=e.out.egt_c + 40.0 + j)))
            return tuple(out)
        one = S._CORES["E4b"](set_(1), V, None)
        two = S._CORES["E4b"](set_(2), V, None)
        self.assertFalse(one.no_statistic)
        self.assertIsNone(one.comp_se["pooled"])
        self.assertIsNotNone(two.comp_se["pooled"])

    def test_l1s_tightened_r_takes_a_magnitude(self):
        """L1's tightened R: a slope that is not finite and above 0 is refused (validate_epa refuses it at the
        arming too); the control, a positive slope, tightens R to b/slope rounded down."""
        b = float(V.b_points)
        ok = {"plant": "b58", "L1": {"slope_points_per_K": 0.1}}
        R, _ = S._R(V, "L1", "held_out", ok)
        self.assertEqual(R, min(float(V.R["L1"][0]), S._round_down(b / 0.1)))
        for bad in (-0.12, 0.0, float("inf"), float("nan")):
            with self.assertRaises(ValueError):
                S._R(V, "L1", "held_out", {"plant": "b58", "L1": {"slope_points_per_K": bad}})

    def test_e5_is_reported_without_its_flagged_rows(self):
        """E5's readings without the lambda-less and sentinel rows (decision 54) and restricted to calibration
        MAP coverage (decision 58), its windows again; in-sample no coverage reading."""
        evs = []
        for i, m in enumerate((40.0, 60.0, 80.0, 50.0)):
            e = ev(i, "2000", pops("fired", "l1_thr", "fired_l1"), tit=600.0 + 3 * i, egt=605.0 + 2 * i, map_kpa=m)
            if i == 3:
                e = replace(e, flags=frozenset({"spark_sentinel"}))
            evs.append(e)
        r = S.row_E5(tuple(evs), view=V, stage="held_out", tightening=None)
        self.assertEqual(sorted(r.extra["without"]), ["lambda_missing", "spark_sentinel"])
        self.assertEqual(r.extra["without"]["spark_sentinel"]["A"]["lines"]["2000"]["n"], 3)
        self.assertEqual(r.extra["windows"]["A"]["lines"]["2000"]["n"], 4)
        self.assertIsNotNone(r.extra["coverage_restricted"])
        self.assertIsNone(S.row_E5(tuple(evs), view=V, stage="in_sample", tightening=None).extra["coverage_restricted"])


class Pins(unittest.TestCase):
    """Decision 56's pins (WP3_INTERFACES.md 5.2.6 and 11): EPA's stated standard uncertainty per test report,
    each read back out of the Table 8 row it quotes; the contract's fallback, unsourced, where no report states
    one; and the pin a row reads is its own report's."""

    # Typed a second time from the four reports' Tables 8 (read 23 October 2026), apart from epa_stats' quoted
    # rows, so an edit of either is seen: (channel, report) -> (the number as printed, the column it sits under).
    STATED = {
        ("speed", S.MAZDA_CELL9): ("1.000", "u(signal)"), ("speed", S.HONDA_CELL7): ("0.302", "u(signal)"),
        ("speed", S.FORD_CELL9): ("1.197", "u(signal)"), ("speed", S.FORD_HD1): ("0.637", "u(calibration)"),
        ("map", S.FORD_CELL9): ("0.321", "u(signal)"),
        ("imt", S.FORD_CELL9): ("0.593", "u(signal)"), ("ect", S.FORD_CELL9): ("0.593", "u(signal)"),
        ("meter", S.MAZDA_CELL9): ("0.00241", "u(signal)"), ("meter", S.HONDA_CELL7): ("0.0100", "u(signal)"),
        ("meter", S.FORD_CELL9): ("0.00737", "u(signal)"), ("meter", S.FORD_HD1): ("0.00581", "u(calibration)"),
        ("torque", S.MAZDA_CELL9): ("0.127", "u(signal)"), ("torque", S.HONDA_CELL7): ("0.135", "u(signal)"),
        ("torque", S.FORD_CELL9): ("0.159", "u(signal)"), ("torque", S.FORD_HD1): ("1.591", "u(calibration)"),
    }
    LABEL = {"speed": "Speed (rpm)", "map": "Pressure (kPa)", "imt": "Temperature (deg C)",
             "ect": "Temperature (deg C)", "meter": "Fuel (g/sec)", "torque": "Torque (Nm)"}

    @staticmethod
    def all_pins():
        out = {}
        for table in (S.U_INPUT, S.U_D):
            for ch, t in table.items():
                for cell, p in t.cells:
                    out[(ch, cell)] = p
        return out

    def test_each_pin_is_the_number_its_report_prints(self):
        """Every CellPin's value is the number its quoted Table 8 row prints under its column (u(signal), or
        u(calibration) where the report prints nothing else, HD1), the row is the channel's, the file the
        report's, and the set of pins is the one typed again above; the meter's row is never the injector
        correlation's. Control: the same row read under another column gives another number."""
        pins = self.all_pins()
        self.assertEqual(set(pins), set(self.STATED))
        for (ch, cell), p in pins.items():
            printed, column = self.STATED[(ch, cell)]
            self.assertEqual((p.printed, p.column), (printed, column), (ch, cell))
            self.assertEqual(p.value, float(printed), (ch, cell))
            cells, head = p.row.split(" | "), p.header.split(" | ")
            self.assertEqual(len(cells), len(head), (ch, cell))
            self.assertEqual(cells[head.index(column)], printed, (ch, cell))
            self.assertTrue(cells[0].startswith(self.LABEL[ch]), (ch, cell, cells[0]))
            self.assertEqual(column, "u(signal)" if "u(signal)" in head else "u(calibration)", (ch, cell))
            self.assertEqual(p.file, S.REPORTS[cell])
            self.assertIn("Table 8: Standard Uncertainties for Signals", p.where)
            self.assertTrue(p.note)
        for cell, p in S.U_D["meter"].cells:
            self.assertNotIn("transient", p.row)
        _, other = S._t8(S.MAZDA_CELL9, "Torque (Nm) | 0.116 | - | 0.0519 | 0.127", column="u(calibration)")
        self.assertNotEqual(other.value, float(self.STATED[("torque", S.MAZDA_CELL9)][0]))

    def test_the_reports_are_the_four_cells_test_reports(self):
        """REPORTS names each (engine, test_cell)'s own report under logs/epa/<engine>/; the Ford's two cells are
        two reports, and the Mazda's Cell 9 is not the Ford's (the key is the engine and the cell together)."""
        self.assertEqual(S.REPORT_CELLS, (S.MAZDA_CELL9, S.HONDA_CELL7, S.FORD_CELL9, S.FORD_HD1))
        for (eng, _), f in S.REPORTS.items():
            self.assertTrue(f.startswith(f"logs/epa/{eng}/") and f.endswith("Test Report.docx"), f)
        self.assertIn("Cell 9 - Test Report", S.REPORTS[S.FORD_CELL9])
        self.assertIn("HD1 - Test Report", S.REPORTS[S.FORD_HD1])
        self.assertEqual(len(set(S.REPORTS.values())), 4)
        self.assertEqual(S.MAZDA_CELL9[1], S.FORD_CELL9[1])
        self.assertNotEqual(S.MAZDA_CELL9, S.FORD_CELL9)

    def test_the_fallbacks_are_the_contracts_and_unsourced(self):
        """Where no report states a channel: u_input's steady-table resolution/sqrt(12) (PLAN.md 6.2: lambda
        0.01, MAP 0.01 kPa, temperature 0.1 C, speed 1 rpm) and spark's declared 0.1 CAD, the thermocouple's IEC
        class 2 and lambda's 0.012 (contract section 3), each unsourced. The meter and torque carry no fallback
        and a pin for every report; speed is stated by every report."""
        for ch, r in {"speed": 1.0, "map": 0.01, "imt": 0.1, "ect": 0.1, "spark": 0.1, "lam": 0.01}.items():
            self.assertEqual(S.U_INPUT[ch].value, r / math.sqrt(12.0), ch)
            self.assertTrue(S.U_INPUT[ch].unsourced, ch)
        self.assertEqual((S.U_INPUT["spark"].cells, S.U_INPUT["lam"].cells), ((), ()))
        self.assertEqual({k for k, _ in S.U_INPUT["speed"].cells}, set(S.REPORT_CELLS))
        tit, lam = S.U_D["tit"], S.U_D["lam"]
        self.assertEqual((tit.value, tit.rel, tit.part, tit.cells, tit.unsourced),
                         (None, 0.0075 / math.sqrt(3.0), "common", (), True))
        self.assertEqual((lam.value, lam.rel, lam.part, lam.cells, lam.unsourced), (0.012, None, "common", (), True))
        for ch in ("meter", "torque"):
            t = S.U_D[ch]
            self.assertEqual((t.value, t.rel, t.part, t.unsourced), (None, None, "random", False), ch)
            self.assertEqual({k for k, _ in t.cells}, set(S.REPORT_CELLS), ch)
            self.assertTrue(t.pinned_for_every_report(), ch)
        self.assertFalse(re.search(r"\d\.\d", " ".join(S.SOURCES_READ)))

    def test_the_production_u_d_table_is_pinned_and_an_open_one_is_listed(self):
        """unpinned_u_d (WP3's fix of 23 October 2026): with every report's meter and torque pinned (decision
        56) nothing is open. Controls: one report's torque pin taken away opens torque again for every gating
        row that reads it (D1's torque target, and L0 and L1 through D1's point: WP3's second fix of 23 October
        2026); the meter without pins opens the meter for D1; a fallback pins every report."""
        self.assertEqual(S.unpinned_u_d(terms=S.U_D), {})
        t = S.U_D["torque"]
        short = dict(S.U_D, torque=replace(t, cells=tuple(c for c in t.cells if c[0] != S.FORD_HD1)))
        self.assertEqual(S.unpinned_u_d(terms=short), {"torque": ("E1a", "D1", "L0", "L1")})
        bare = dict(S.U_D, meter=replace(S.U_D["meter"], cells=()))
        self.assertIn("D1", S.unpinned_u_d(terms=bare)["meter"])
        synth = dict(S.U_D, meter=S.UD(0.01, None, "random", "t", "t", True),
                     torque=S.UD(0.05, None, "random", "t", "t", True))
        self.assertEqual(S.unpinned_u_d(terms=synth), {})

    def test_a_row_reads_its_own_reports_pin(self):
        """A shift moves each row by its own report's u (InputShift.delta_for, cell_of): torque by 0.127 N m on
        the Mazda, 0.159 on the Ford's Cell 9 and 1.591 on HD1; speed by 1.000 rpm on the Mazda and 0.637 on HD1;
        MAP by 0.321 kPa on the Ford's Cell 9 and by the fallback elsewhere. kernel_point carries the row's cell
        into its RowEval. Controls: a row of no report reads speed's fallback, and refuses torque, which has
        none."""
        mz = prow(engine="mazda_25t", test_cell="Test Cell 9", source_row=6)
        f9 = prow(engine="ford_27tt", test_cell="Test Cell 9", source_row=7)
        hd = prow(engine="ford_27tt", test_cell="Test Cell HD1", source_row=8)
        syn = prow(source_row=9)
        sh = S.torque_target_shift(S.U_D)
        self.assertEqual([S._shifted_row(r, sh).torque_nm for r in (mz, f9, hd)],
                         [200.0 + 0.127, 200.0 + 0.159, 200.0 + 1.591])
        with self.assertRaises(S.UnpinnedUncertainty):
            S._shifted_row(syn, sh)
        up = {ch: s for ch, sg, s in S.input_shifts() if sg == +1}
        self.assertEqual([S._shifted_row(r, up["speed"]).speed_rpm for r in (mz, hd, syn)],
                         [2000.0 + 1.0, 2000.0 + 0.637, 2000.0 + 1.0 / math.sqrt(12.0)])
        self.assertEqual([S._shifted_row(r, up["map"]).map_kpa for r in (f9, mz)],
                         [120.0 + 0.321, 120.0 + 0.01 / math.sqrt(12.0)])
        e = S.kernel_point(Toy(), S.make_task(hd, view=V, conventions=S.NOMINAL, dtheta=0.25, needs={"at_epa"},
                                              shift=sh))
        self.assertEqual((S.cell_of(e), e.measured.torque_nm), (S.FORD_HD1, 200.0 + 1.591))

    def test_u_d_and_the_unsourced_marks_read_each_members_report(self):
        """The meter's random u_D moves each member by its own report's u (two Mazda rows by 0.00241 g/s, an HD1
        row by 0.00581), by hand, and nothing is unsourced; u_input's MAP is sourced on the Ford's Cell 9 alone.
        Controls: a member of no report refuses the production meter, which has no fallback, and with a fallback
        it reads it and the term is marked unsourced."""
        M = pops("fired", "fired_meter", "hot", "hot_meter")
        spec = ((S.MAZDA_CELL9, 5.0, 5.1), (S.MAZDA_CELL9, 4.0, 3.9), (S.FORD_HD1, 6.0, 6.3))
        mev = [replace(ev(i, "2000", M, meter=m, F_m=f), engine=c[0], test_cell=c[1])
               for i, (c, m, f) in enumerate(spec)]
        keys = tuple(S._key(e) for e in mev)
        st = lambda evs: S._CORES["E2a"](tuple(evs), V, None).comps["2000"]     # noqa: E731
        u_of = {S.MAZDA_CELL9: 0.00241, S.FORD_HD1: 0.00581}
        hand = math.sqrt(sum((100 * (f / (m + u_of[c]) - f / m) / 3) ** 2 for c, m, f in spec))
        u, uns = S.u_d_terms(st, mev, channels=("meter",), members=keys, terms=S.U_D)
        self.assertAlmostEqual(u, hand, places=12)
        self.assertEqual(uns, ())
        self.assertTrue(S.input_unsourced("map", mev, keys, terms=S.U_INPUT))
        f9 = [replace(e, engine="ford_27tt", test_cell="Test Cell 9") for e in mev]
        self.assertFalse(S.input_unsourced("map", f9, keys, terms=S.U_INPUT))
        self.assertFalse(S.input_unsourced("speed", mev, keys, terms=S.U_INPUT))
        mixed = mev[:2] + [replace(mev[2], engine="synth", test_cell=None)]
        with self.assertRaises(S.UnpinnedUncertainty):
            S.u_d_terms(st, mixed, channels=("meter",), members=keys, terms=S.U_D)
        fb = dict(S.U_D, meter=replace(S.U_D["meter"], value=0.01, unsourced=True))
        u2, uns2 = S.u_d_terms(st, mixed, channels=("meter",), members=keys, terms=fb)
        hand2 = math.sqrt(sum((100 * (f / (m + u_) - f / m) / 3) ** 2
                              for (_, m, f), u_ in zip(spec, (0.00241, 0.00241, 0.01))))
        self.assertAlmostEqual(u2, hand2, places=12)
        self.assertEqual(uns2, ("u_D meter",))
        self.assertTrue(S.input_unsourced("speed", mixed, keys, terms=S.U_INPUT))


class C5(unittest.TestCase):
    def setUp(self):
        self.b58 = engines.get("b58")

    def road(self, grade, n=6, v_kmh=130.0):
        g = np.full(n, float(grade)) if np.isscalar(grade) else np.asarray(grade, float)
        n = len(g)
        return dict(t=np.arange(n) * 1.0, v_mps=np.full(n, v_kmh / 3.6), grade=g, t_amb=315.0, p_baro=101.3)

    def test_the_b58s_7th_to_6th_notch_at_130_kmh(self):
        """test_reward.py's notch (decision 70; amendment F2): at 13.96 % the box holds 7th with its demand just under
        shift_ceiling_nm, at 13.97 % it holds 6th with 7th rejected just over: C5's margin is the code's threshold."""
        s1 = S.c5_margin(self.b58, self.road(0.1396), dt=1.0)[2]
        s2 = S.c5_margin(self.b58, self.road(0.1397), dt=1.0)[2]
        self.assertEqual((s1.held, s2.held), ("7", "6"))
        veh = E.vehicle_for(self.b58.car)
        rpm7 = 130 / 3.6 / veh.wheel_r * veh.gears[6] * veh.final_drive * 60 / (2 * np.pi)
        self.assertLess(s1.demand_nm, veh.shift_ceiling_nm(rpm7))
        m1 = dict((a, b) for a, b, _ in s1.margins)
        m2 = dict((a, b) for a, b, _ in s2.margins)
        self.assertLess(m1["gear7_held"], 0.001)
        self.assertLess(m2["gear7_rejected"], 0.001)
        self.assertTrue(all(g for _, _, g in s2.margins))
        self.assertEqual(S.c5_climb([s1], margin=0.019, thin_share=0.5).outcome, "fails")
        locked = S.c5_margin(self.b58, self.road(0.12), dt=1.0)[2]
        self.assertEqual(locked.held, "7")
        self.assertEqual(S.c5_climb([locked], margin=0.019, thin_share=0.5).outcome, "passes")

    def test_a_barred_downshift_does_not_gate_the_held_margin(self):
        """A held gear whose lower gear is barred by SHIFT_RPM_MAX does not gate its own margin even with its
        demand under its ceiling (gear_for would stop at the ceiling test first); the rejected higher gear still
        gates; held and highest allowed, no margin gates (the third non-gated case). Control: the same step with
        the bar at 6000 rpm gates the held margin."""
        car = replace(self.b58.car, shift_rpm_max=3000.0)
        st = S.c5_margin(replace(self.b58, car=car), self.road(0.12), dt=1.0)[2]
        self.assertEqual(st.held, "7")
        m = {a: g for a, _, g in st.margins}
        self.assertEqual(m, {"gear7_held": False, "gear8_rejected": True})
        self.assertTrue(st.gated)
        self.assertGreater(st.bar_rpm_margin, 0.0)
        car2 = replace(self.b58.car, shift_rpm_max=2500.0)
        st2 = S.c5_margin(replace(self.b58, car=car2), self.road(0.05), dt=1.0)[2]
        self.assertEqual((st2.held, st2.gated, st2.no_margin_case), ("8", False, "barred_highest_allowed"))
        ctrl = S.c5_margin(self.b58, self.road(0.05), dt=1.0)[2]
        self.assertEqual((ctrl.held, ctrl.gated, ctrl.margins[0][2]), ("8", True, True))

    def test_the_transition_test_is_exact_and_the_end_steps_their_own_neighbours(self):
        """A one-ulp grade change is a transition (no tolerance); a speed that changes at the next step makes this
        step a transition; the first and last steps compare with themselves where no neighbour exists."""
        g = np.full(6, 0.12)
        g[3] = np.nextafter(0.12, 1.0)
        steps = S.c5_margin(self.b58, self.road(g), dt=1.0)
        self.assertEqual([s.transition for s in steps], [False, False, False, True, True, False])
        cyc = self.road(0.12)
        cyc["v_mps"] = cyc["v_mps"].copy()
        cyc["v_mps"][5] += 0.1
        steps = S.c5_margin(self.b58, cyc, dt=1.0)
        self.assertEqual([s.transition for s in steps], [False, False, False, False, True, True])
        self.assertFalse(any(s.gated for s in steps if s.transition))
        with self.assertRaises(ValueError):
            S.c5_margin(self.b58, cyc, dt=0.5)

    def step(self, k, gated, m, transition=False):
        return S.C5Step(k=k, transition=transition, gated=gated, held="7", margins=(("gear7_held", m, True),),
                        bar_rpm_margin=None, bar_rpm_margin_frac=None, no_margin_case=None, v_mps=36.1, grade=0.1,
                        demand_nm=300.0, rpm=2700.0)

    def test_the_three_outcome_cases(self):
        """(1) fails at a gated margin at or below m; (2) thinly checked when none fails and fewer than half the steps
        are gated; (3) passes. A thin climb that fails at a gated step fails; one with no gated step never passes."""
        f = S.c5_climb
        self.assertEqual(f([self.step(0, True, 0.019), self.step(1, True, 0.5)], margin=0.019, thin_share=0.5).outcome, "fails")
        thin = f([self.step(0, True, 0.5)] + [self.step(k, False, 0.5, True) for k in (1, 2)], margin=0.019, thin_share=0.5)
        self.assertEqual((thin.outcome, thin.thin), ("thinly_checked", True))
        ok = f([self.step(0, True, 0.5), self.step(1, True, 0.3), self.step(2, False, 0.0, True)], margin=0.019, thin_share=0.5)
        self.assertEqual((ok.outcome, ok.thin), ("passes", False))
        tf = f([self.step(0, True, 0.01)] + [self.step(k, False, 0.5, True) for k in (1, 2)], margin=0.019, thin_share=0.5)
        self.assertEqual((tf.outcome, tf.thin), ("fails", True))
        none = f([self.step(k, False, 0.5, True) for k in range(3)], margin=0.019, thin_share=0.5)
        self.assertEqual(none.outcome, "thinly_checked")
        half = f([self.step(0, True, 0.5), self.step(1, False, 0.5, True)], margin=0.019, thin_share=0.5)
        self.assertEqual((half.outcome, half.thin), ("passes", False))      # gated = half: not fewer than half

    def test_the_cvt_margin_and_its_diagnostic(self):
        """The CVT: no margin on its low-speed branch (not gated), T_eco against kickdown_threshold_nm(N_eco)
        elsewhere; decision 40's diagnostic reports connectedness and the branch under (1 +- m)."""
        import test_cars as TC
        acc = TC.epa_car(TC.ACCORD, "three_term_cvt", TC.TYPED_ACCORD)
        plant = replace(self.b58, car=acc)
        slow = S.c5_margin(plant, self.road(0.0, v_kmh=3.6), dt=1.0)[2]
        self.assertEqual((slow.held, slow.gated, slow.no_margin_case), ("low-speed", False, "cvt_low_speed"))
        fast = S.c5_margin(plant, self.road(0.0), dt=1.0)[2]
        veh = E.vehicle_for(acc)
        rho = 101.3 * 1000.0 / (287.0 * 315.0)
        f = veh.road_force_n(130 / 3.6, 0.0, rho=rho)
        _, _, br, ne, te = veh.ratio_for(130 / 3.6, f)
        self.assertEqual(fast.held, br)
        self.assertAlmostEqual(fast.margins[0][1], abs(te / veh.kickdown_threshold_nm(ne) - 1), places=12)
        self.assertTrue(fast.gated)
        d = S.cvt_diagnostic(plant, v_mps=130 / 3.6, force_n=veh.road_force_n(130 / 3.6, 0.12, rho=rho), margin=0.019)
        self.assertEqual(len(d["cases"]), 4)
        self.assertIn(d["branch"], ("economy", "kickdown", "power-limited"))
        self.assertIsInstance(d["connected"], bool)
        with self.assertRaises(TypeError):
            S.cvt_diagnostic(self.b58, v_mps=30.0, force_n=1000.0, margin=0.019)


if __name__ == "__main__":
    unittest.main(verbosity=2)
