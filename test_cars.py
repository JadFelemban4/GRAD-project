"""test_cars.py -- the EPA cars as the plant builds them: their converted values, EPA's road load, the CVT's law, the guards, and the Supra unchanged.

    python test_cars.py        about 10 s; exit code 0 when all pass

Build step 2 of decision 24 (docs/build_step_2/PLAN.md WP1 P5 and section 7; its
amendments, docs/build_step_2/AMENDMENTS.md, govern), P5 (22 October 2026): the
three EPA engines run in their own cars (decision 24), and those cars are not the
Supra. They run EPA's certification road load, F = (A + B v) cos(theta) +
C v^2 rho/rho_ref + m g sin(theta) (decision 42), their mass and wheel radius
converted from EPA's Test Car List row with exact factors (engines.published_car);
the CX-9 and the F-150 have a stepped box (engines.EpaCar, engine_env.EpaVehicle),
the Accord a CVT run by decision 40's stateless kickdown (engines.CvtCar,
engine_env.CvtVehicle; amendment F6). The Supra keeps engines.Car and
engine_env.Vehicle unchanged (decision 31).

Until P6 no EPA plant was registered: the cars of every class but RegisteredCars
are built from the published car files through published_car and engines._record,
with the typed fields a test's own (TYPED_*, test values, not the specs' values),
and the deliverable-torque table synthetic (CVT_TABLE). P6 (22 October 2026)
registered the three plants with their six specs; RegisteredCars builds their cars
as the plants will hold them. Nothing here reads an EPA engine table.

  Converted   the converted values of the three cars, printed (amendment section
              4 item 4), are the plan's arithmetic (PLAN.md 7.5)
  C1          EPA's road force at m a = 0 on a level road in EPA's reference air
              is EPA's own polynomial, A + B mph + C mph^2 computed in lbf and mph
              and converted with exact factors, at 15, 20, ... 115 km/h, to 1e-6
              (MD:805-813). Control (amendment F9): A x (1 + 1e-5) fails it
  C2          mass = ETW x 0.45359237 and the wheel radius = 26.8224 x top x axle
              / (2 pi N/V), recomputed here from the plan's own numbers (CX-9
              0.370346, Accord 0.328616, F-150 0.374992), to 1e-6; the model's
              top-gear N/V, from the vehicle's radius, top ratio and final drive,
              printed beside EPA's with its gap, which is decision 42's disclosed
              one: the CX-9's 2.27e-4 (final drive 4.411, EPA's axle 4.41), the
              others' under 1e-6 (PLAN.md 7.4); the published gears, final drive
              and CVT range are what the files print (RegisteredCars compares the
              typed specs with them). Control: 4.411 in place of the CX-9's 4.41
              fails the radius, by C2's own check (c2_errors; P7)
  RegisteredCars  (P6, 22 October 2026) the cars of the three registered plants,
              built by build_candidate as the plants will hold them, printed with
              their converted and typed values: each is the record its kind names,
              its converted values published_car's of its own published file and
              the plan's arithmetic; its gears, final drive and CVT range the file's;
              C1 and the top-gear N/V gap (the CX-9's alone, 2.27e-4); the peak
              torques the sources' 310 and 375 lb-ft (decision 43: Mazda's MZ19
              sheet for the CX-9); each plant's files its two specs and its
              published car file
  EpaVehicle  Vehicle's gearbox under EPA's road load: with coefficients that
              make EPA's force the Supra's, its demand is the Supra's (control: C
              moved fails it); the records refuse a NumPy scalar (amendment B10),
              and, in their table and gears, a NumPy value or a list (P7)
  CvtLaw      decision 40's law (b) per amendment F6: v = 0 and the launch (the
              low-speed branch and its boundary), economy at the top ratio, the
              kickdown at kickdown_load x T_del(N_eco) to a part in 1e9 (control:
              a different load moves it), the smallest speed holding target_load
              to the bisection's 0.01 rpm, the power-limited branch flagged, f <= 0,
              statelessness, over-speed refused, bad records refused (a target
              load not below the kickdown load among them: no reserve). Off the
              low-speed branch every step turns the engine at the ratio's speed
              and gives the road's power, T omega eta = f v; at 30 km/h the window's
              top, min(rpm_max, n_w x low x fd), is the power-limited speed. An
              empty table names the EPA command, not the B58's
  Dispatch    vehicle_for picks each car's model by the record's exact type, and
              the environment and measure_deliverable_torque run an EPA car's own
              (the B58's engine in the test's records: each step's demand is the
              car's own vehicle's, to the bit)
  Guards      every training-road builder, engine_env's and wide_air's, and
              wide_air.ThinAirVehicle refuse an EpaVehicle and a CvtVehicle, each by
              its OWN guard, its own name first in the message, and run for the
              Supra's Vehicle (amendment B15); the control: an EpaVehicle IS a
              Vehicle, so only the car record's type stops it
  StepRecord  step_record.gear refuses a CVT (amendment B16's second option: a
              CVT is never recorded), and gives the Supra's gear for the Supra
  Fingerprint fingerprint.plant_fingerprint refuses a CVT car by name, "this car
              has no gears" (amendment B17), and a candidate (build_candidate);
              the Supra's plant fingerprints; an EPA plant's files include its
              published car file, the Supra's are its two specs
  Supra       the Supra's Car has build step 1's fields, vehicle_for(car) is a
              Vehicle, and its demand, and the environment's vehicle's, are
              cf43fbb's doubles, bit for bit: those of cf43fbb's Vehicle, copied
              and run in the same process, so on any machine (P7); on the
              platform that made it, the copy and the live vehicle hash to
              SUPRA_DEMAND_SHA256, cf43fbb's own digest; the control: the same
              sum regrouped fails both
"""
import hashlib
import math
import os
import pickle
import sys
import tempfile
import unittest
from dataclasses import fields, replace

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import engines  # noqa: E402
import engine_env as E  # noqa: E402

CARS = os.path.join(HERE, "engine_specs", "cars")
CX9, ACCORD, F150 = (os.path.join(CARS, f + ".toml") for f in ("cx9_2016_25t", "accord_2018_15t",
                                                                 "f150_2015_27tt"))

# Exact factors, typed here independently of engines.py (C1 and C2 recompute with them).
LBF_N, MPH_MPS, LB_KG, MPH_M_PER_MIN = 4.4482216152605, 0.44704, 0.45359237, 26.8224

# A test's own typed fields for the cars (NOT the P6 specs' values): the Supra's
# carried constants where they exist (a90_supra.toml), the published gears and
# final drive, and the calibration lines PLAN.md 7.5 names.
TYPED_STEPPED = dict(driveline_eff=0.92, peak_torque_nm=400.0, shift_load=0.75, upshift_min_rpm=2000.0,
                     table_t_amb=315.0, table_t_block=365.0, table_settle=30, table_rpm_step=100)
TYPED_CX9 = dict(TYPED_STEPPED, id="test-cx9", final_drive=4.411, gears=(3.487, 1.992, 1.449, 1.00, 0.707, 0.600),
                 shift_rpm_max=5000.0, rpm_min=1300.0, rpm_max=5000.0, table_rpm_lo=1300, table_rpm_hi=5000)
TYPED_F150 = dict(TYPED_STEPPED, id="test-f150", final_drive=3.31, gears=(4.17, 2.34, 1.52, 1.14, 0.86, 0.69),
                  shift_rpm_max=5500.0, rpm_min=1000.0, rpm_max=5500.0, table_rpm_lo=1000, table_rpm_hi=5500)
TYPED_ACCORD = dict(id="test-accord", final_drive=5.36, ratio_low_gear=2.645, ratio_top_gear=0.405,
                    driveline_eff=0.92, kickdown_load=0.75, target_load=0.65, cvt_rpm_min=1000.0,
                    rpm_min=1000.0, rpm_max=5000.0, table_rpm_lo=1000, table_rpm_hi=5000, table_rpm_step=100,
                    table_t_amb=315.0, table_t_block=365.0, table_settle=30)


def synthetic_table(lo, hi, step):
    """A deliverable-torque table of the shape a turbocharged engine's has: a rise
    to a plateau, then a fall steep enough that the most power is at 4500 rpm.
    Synthetic, so the law is tested, not an engine."""
    out = []
    for n in range(lo, hi + 1, step):
        t = min(220.0, 120.0 + (n - 1000) * 0.125) if n <= 4500 else 220.0 - (n - 4500) * 0.2
        out.append([n, float(t)])
    return out


def epa_car(path, kind, typed, table=None):
    """The car record the plant would build from this published file: its mass,
    radius and road load converted by engines.published_car, the rest `typed`,
    the table (DERIVED) from an in-memory source, through engines._record."""
    cls = engines.CAR_KINDS[kind]
    t = synthetic_table(typed["table_rpm_lo"], typed["table_rpm_hi"], typed["table_rpm_step"]) \
        if table is None else table
    return engines._record(cls, "car", typed, {"deliverable_torque": t}, "epa", engines.published_car(path, kind))


def published(path):
    import tomllib
    with open(path, "rb") as fh:
        return tomllib.load(fh)


def read_text(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def c1_errors(veh, pub):
    """C1: the relative error of the plant's road force against EPA's polynomial
    at 15, 20, ... 115 km/h, level, in EPA's reference air, with m a = 0."""
    row = pub["epa_test_car"]
    out = []
    for kmh in range(15, 116, 5):
        v = kmh / 3.6
        mph = v / MPH_MPS
        ref = (row["target_coef_a_lbf"] + row["target_coef_b_lbf_per_mph"] * mph
               + row["target_coef_c_lbf_per_mph2"] * mph ** 2) * LBF_N
        got = float(veh.road_force_n(v, 0.0, rho=veh.road_rho_ref))
        out.append(abs(got - ref) / abs(ref))
    return out


class Converted(unittest.TestCase):
    def test_the_converted_values_are_the_plans_arithmetic(self):
        want = {  # PLAN.md 7.5 (arith.), mass, A, B, C, wheel_r
            CX9: (2041.166, 179.899, 2.58073, 0.586931, 0.370346, "three_term_stepped"),
            ACCORD: (1587.573, 194.610, -6.01202, 0.582947, 0.328616, "three_term_cvt"),
            F150: (2154.564, 100.307, 3.89060, 0.698246, 0.374992, "three_term_stepped")}
        print()
        for path, (m, a, b, c, r, kind) in want.items():
            got = engines.published_car(path, kind)
            print(f"  {os.path.basename(path):24s} mass {got['mass']!r} kg  A {got['road_a_n']!r} N  "
                  f"B {got['road_b_n_per_mps']!r} N/(m/s)  C {got['road_c_n_per_mps2']!r} N/(m/s)^2  "
                  f"rho_ref {got['road_rho_ref']!r}  wheel_r {got['wheel_r']!r} m")
            for key, plan in (("mass", m), ("road_a_n", a), ("road_b_n_per_mps", b), ("road_c_n_per_mps2", c),
                              ("wheel_r", r)):
                with self.subTest(car=os.path.basename(path), field=key):
                    self.assertIs(type(got[key]), float)
                    self.assertAlmostEqual(got[key] / plan, 1.0, delta=1e-5)
            # rho_ref = 98 210 / (287.0 x 293.15) = 1.167304 (PLAN.md 7.2)
            self.assertAlmostEqual(got["road_rho_ref"], 1.167304, places=6)

    def test_published_car_refuses_what_it_cannot_convert(self):
        with self.assertRaises(ValueError):
            engines.published_car(os.path.join(CARS, "a90_supra_2020.toml"), "two_term_stepped")
        with self.assertRaises(ValueError):          # a CVT read as a stepped box: no [gear_ratios]
            engines.published_car(ACCORD, "three_term_stepped")
        with self.assertRaises(ValueError):          # a stepped box read as a CVT: no [cvt_ratio_range]
            engines.published_car(CX9, "three_term_cvt")
        text = read_text(CX9)
        with tempfile.TemporaryDirectory() as tmp:
            for old, new in (('status = "PUBLISHED"\nsource = "EPA16"\nfile_rows = [2677',
                              'status = "DERIVED"\nsource = "EPA16"\nfile_rows = [2677'),
                             ("n_over_v_rpm_per_mph = 30.5\nnote = \"rows 2677",
                              "n_over_v_rpm_per_mph = \"30.5\"\nnote = \"rows 2677")):
                with self.subTest(change=new[:30]):
                    self.assertEqual(text.count(old), 1)
                    p = os.path.join(tmp, "bad.toml")
                    with open(p, "w", encoding="utf-8") as fh:
                        fh.write(text.replace(old, new))
                    with self.assertRaises(ValueError):
                        engines.published_car(p, "three_term_stepped")


class C1(unittest.TestCase):
    def test_the_road_force_is_epas_polynomial(self):
        for path, kind, typed in ((CX9, "three_term_stepped", TYPED_CX9), (ACCORD, "three_term_cvt", TYPED_ACCORD),
                                  (F150, "three_term_stepped", TYPED_F150)):
            veh = E.vehicle_for(epa_car(path, kind, typed))
            err = max(c1_errors(veh, published(path)))
            with self.subTest(car=os.path.basename(path)):
                print(f"\n  C1 {os.path.basename(path)}: largest relative error {err:.2e} over 15-115 km/h")
                self.assertLess(err, 1e-6)

    def test_c1_fails_on_a_relative_1e5_change_to_a(self):
        """Amendment F9: an absolute 1e-5 on A moves F by at most 2.5e-7, so the
        control is relative, A x (1 + 1e-5), and it must fail C1 on every car."""
        for path, kind, typed in ((CX9, "three_term_stepped", TYPED_CX9), (ACCORD, "three_term_cvt", TYPED_ACCORD),
                                  (F150, "three_term_stepped", TYPED_F150)):
            car = epa_car(path, kind, typed)
            moved = replace(car, road_a_n=car.road_a_n * (1.0 + 1e-5))
            err = max(c1_errors(E.vehicle_for(moved), published(path)))
            with self.subTest(car=os.path.basename(path)):
                print(f"\n  C1 control {os.path.basename(path)}: A x (1 + 1e-5) gives {err:.2e}")
                self.assertGreater(err, 1e-6)

    def test_the_air_scales_c_only(self):
        """At twice the reference air only the C term doubles, and the grade adds
        m g sin(theta) and turns A + B v by cos(theta)."""
        veh = E.vehicle_for(epa_car(CX9, "three_term_stepped", TYPED_CX9))
        v, rho, g = 30.0, 2.0 * veh.road_rho_ref, 0.12
        th = math.atan(g)
        want = ((veh.road_a_n + veh.road_b_n_per_mps * v) * math.cos(th) + 2.0 * veh.road_c_n_per_mps2 * v * v
                + veh.mass * 9.81 * math.sin(th))
        self.assertAlmostEqual(float(veh.road_force_n(v, g, rho=rho)) / want, 1.0, delta=1e-14)


class C2(unittest.TestCase):
    @staticmethod
    def radius(top, axle, nv):
        return MPH_M_PER_MIN * top * axle / (2.0 * math.pi * nv)

    # The model's top-gear N/V against EPA's, relative (decision 42's disclosure):
    # the CX-9 runs its final drive, 4.411 (TYPED_CX9, as its [final_drive] prints),
    # where EPA's row and so its radius have the axle 4.41; the F-150's and the
    # Accord's final drive is their row's axle.
    NV_GAP = {CX9: 4.411 / 4.41 - 1.0, ACCORD: 0.0, F150: 0.0}

    def test_mass_and_radius_are_epas(self):
        for path, kind, top, typed in ((CX9, "three_term_stepped", 0.600, TYPED_CX9),
                                       (ACCORD, "three_term_cvt", 0.405, TYPED_ACCORD),
                                       (F150, "three_term_stepped", 0.69, TYPED_F150)):
            row = published(path)["epa_test_car"]
            got = engines.published_car(path, kind)
            with self.subTest(car=os.path.basename(path)):
                self.assertEqual(c2_errors(path, kind, path), [])           # mass and radius: C2's check
                # THE MODEL'S top-gear N/V beside EPA's (PLAN.md 7.4), from the vehicle the
                # plant builds: its radius, its top ratio and its final drive, the ratio
                # EpaVehicle and CvtVehicle run (gears[g] x final_drive; ratio x
                # final_drive). Until the review of P5 (22 October 2026) this took EPA's
                # axle for the final drive, gave EPA's N/V back by construction and hid
                # the CX-9's gap; a radius or a final drive moved now fails it.
                veh = E.vehicle_for(epa_car(path, kind, typed))
                top_ratio = veh.ratio_top if kind == "three_term_cvt" else veh.gears[-1]
                self.assertEqual(top_ratio, top)
                nv_model = MPH_MPS * 60.0 / (2.0 * math.pi * veh.wheel_r) * top_ratio * veh.final_drive
                gap = nv_model / row["n_over_v_rpm_per_mph"] - 1.0
                print(f"\n  C2 {os.path.basename(path)}: wheel_r {got['wheel_r']:.6f} m; the model's top-gear "
                      f"N/V {nv_model:.4f} rpm/mph ({top_ratio} x final drive {veh.final_drive}) against "
                      f"EPA's {row['n_over_v_rpm_per_mph']} (axle {row['axle_ratio']}): {gap:+.3e} relative")
                self.assertLess(abs(gap - self.NV_GAP[path]), 1e-6)

    def test_the_published_ratios_are_the_files(self):
        """The gears, final drive and CVT range as the files print them; the
        typed specs are compared with these by
        RegisteredCars.test_the_typed_ratios_are_the_published_files."""
        cx9, f150, acc = published(CX9), published(F150), published(ACCORD)
        self.assertEqual(cx9["gear_ratios"]["value"], [3.487, 1.992, 1.449, 1.00, 0.707, 0.600])
        self.assertEqual(cx9["final_drive"]["value"], 4.411)
        self.assertEqual(f150["gear_ratios"]["value"], [4.17, 2.34, 1.52, 1.14, 0.86, 0.69])
        self.assertEqual(f150["final_drive"]["value"], 3.31)
        self.assertEqual(acc["cvt_ratio_range"]["value"], [2.645, 0.405])
        self.assertEqual(acc["final_drive"]["value"], 5.36)
        self.assertEqual(TYPED_CX9["gears"], tuple(cx9["gear_ratios"]["value"]))

    def test_4411_in_place_of_441_fails_the_radius(self):
        """Decision 42's disclosure, as a control of C2's OWN check (the review of
        P5, 22 October 2026: this recomputed the radius itself, so C2 could have
        lost its comparison with the plan and the control would still have
        passed; mistake 12): the CX-9's file with its EPA row's axle 4.41 written
        as 4.411, the final drive it prints, fails c2_errors on the radius, 2.3e-4
        off the plan's, and on nothing else -- its row check passes, since the
        radius moves with the row it is computed from. The file as it is passes."""
        text = read_text(CX9)
        old = "axle_ratio = 4.41\nn_over_v_rpm_per_mph = 30.5\nnote = \"rows 2677"
        self.assertEqual(text.count(old), 1)
        self.assertEqual(c2_errors(CX9, "three_term_stepped", CX9), [])
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "cx9_4411.toml")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(text.replace(old, old.replace("4.41", "4.411")))
            errors = c2_errors(p, "three_term_stepped", CX9)
        print("\n  C2 control, 4.411: " + "; ".join(errors))
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all(e.startswith("wheel_r ") for e in errors), errors)
        self.assertTrue(any("off the plan's inputs'" in e for e in errors), errors)
        self.assertFalse(any("off the row's" in e for e in errors), errors)


# C2's radius from the plan's own numbers (PLAN.md 7.4, arith.): each car's top
# ratio, its EPA row's axle and N/V, and the radius they give to six digits.
C2_PLAN = {CX9: (0.600, 4.41, 30.5, 0.370346), ACCORD: (0.405, 5.36, 28.2, 0.328616),
           F150: (0.69, 3.31, 26.0, 0.374992)}


def c2_errors(path, kind, car):
    """C2's mass and radius checks (22 October 2026, build step 2 P7; the review of
    P5) on the car converted from the published file `path` read as `kind`, with
    the plan's numbers for `car` (CX9, ACCORD or F150; C2_PLAN): what fails, as
    text, [] when it passes. The mass is EPA's test weight in kg (1e-6); the
    radius is held to the file's own row (1e-6), to the plan's top ratio, axle and
    N/V (1e-6), and to the plan's six digits (2e-6). One definition, called by C2
    and by its control, so the control runs the check it controls."""
    row = published(path)["epa_test_car"]
    got = engines.published_car(path, kind)
    top, axle, nv, plan_r = C2_PLAN[car]
    out = []
    if not abs(got["mass"] / (row["equivalent_test_weight_lb"] * LB_KG) - 1.0) < 1e-6:
        out.append(f"mass {got['mass']!r} is not EPA's test weight x {LB_KG}")
    for what, r, tol in (("the row's", C2.radius(top, row["axle_ratio"], row["n_over_v_rpm_per_mph"]), 1e-6),
                         ("the plan's inputs'", C2.radius(top, axle, nv), 1e-6),
                         ("the plan's six digits", plan_r, 2e-6)):
        if not abs(got["wheel_r"] / r - 1.0) < tol:
            out.append(f"wheel_r {got['wheel_r']!r} is {got['wheel_r'] / r - 1.0:+.3e} off {what} {r!r}")
    return out


# THE REGISTERED CARS (22 October 2026, build step 2 P6): engines.PLANTS names each
# EPA engine with its car spec, engine_specs/cx9_2016.toml, accord_2018.toml and
# f150_2015.toml. No EPA plant is calibrated, so each is built here as a candidate
# (engines.build_candidate, the constructor get() will use): from its two specs, its
# published car file, and, for the engine's DERIVED fields, the B58's own values with
# no table yet -- numbers that only let the records build; nothing is run, and no
# EPA row is read. The car record is the one the plant will hold.
PUBLISHED_OF = {"mazda_25t": (CX9, "three_term_stepped", engines.EpaCar),
                "honda_l15b7": (ACCORD, "three_term_cvt", engines.CvtCar),
                "ford_27tt": (F150, "three_term_stepped", engines.EpaCar)}


def neutral_values():
    """A candidate's DERIVED values for an EPA engine: the B58's, as engines.get("b58")
    holds them, for every field of the EPA set, and the deliverable-torque table
    empty (not measured yet). They are not any EPA engine's: they let its records
    build, so that what its specs type can be read back from the plant."""
    p = engines.get("b58")
    vals = {}
    for (rec, f), (sec, key) in engines.EPA_DERIVED_FIELDS.items():
        if rec == "car":
            vals[sec] = []
            continue
        v = getattr(getattr(p.engine, rec), f)
        vals.setdefault(sec, {})[key] = list(v) if isinstance(v, tuple) else v
    return vals


class RegisteredCars(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plants = {n: engines.build_candidate(n, neutral_values()) for n in PUBLISHED_OF}

    def test_the_registered_cars_converted_values(self):
        """Each registered car is the record its kind names, its converted values
        are published_car's of the file its spec names, bit for bit, and the plan's
        arithmetic (PLAN.md 7.5) to 1e-5; printed with what the spec types."""
        print()
        for name, (path, kind, cls) in PUBLISHED_OF.items():
            car = self.plants[name].car
            with self.subTest(car=car.id):
                self.assertIs(type(car), cls)
                self.assertEqual(engines.read_spec(engines.PLANTS[name][1])["_meta"]["published"],
                                 os.path.relpath(path, HERE).replace(os.sep, "/"))
                conv = engines.published_car(path, kind)
                self.assertEqual({k: getattr(car, k) for k in conv}, conv)
                box = (f"ratio {car.ratio_low_gear}-{car.ratio_top_gear}, kickdown_load {car.kickdown_load}, "
                       f"target_load {car.target_load}, cvt_rpm_min {car.cvt_rpm_min!r}" if cls is engines.CvtCar else
                       f"gears {car.gears}, peak_torque_nm {car.peak_torque_nm!r}, shift_load {car.shift_load}, "
                       f"shift_rpm_max {car.shift_rpm_max!r}")
                print(f"  {name:12s} {car.id}: mass {car.mass!r} kg, A {car.road_a_n!r} N, B {car.road_b_n_per_mps!r} "
                      f"N/(m/s), C {car.road_c_n_per_mps2!r} N/(m/s)^2, rho_ref {car.road_rho_ref!r}, wheel_r "
                      f"{car.wheel_r!r} m; final drive {car.final_drive}, {box}; eta {car.driveline_eff}; rpm "
                      f"{car.rpm_min!r}-{car.rpm_max!r}; table {car.table_rpm_lo}-{car.table_rpm_hi} by "
                      f"{car.table_rpm_step} at {car.table_t_amb} K, block {car.table_t_block} K, settle "
                      f"{car.table_settle}; climb {self.plants[name].scenario}")
        want = {"mazda_25t": (2041.166, 179.899, 2.58073, 0.586931, 0.370346),       # PLAN.md 7.5 (arith.)
                "honda_l15b7": (1587.573, 194.610, -6.01202, 0.582947, 0.328616),
                "ford_27tt": (2154.564, 100.307, 3.89060, 0.698246, 0.374992)}
        for name, plan in want.items():
            car = self.plants[name].car
            for key, v in zip(("mass", "road_a_n", "road_b_n_per_mps", "road_c_n_per_mps2", "wheel_r"), plan):
                with self.subTest(car=car.id, field=key):
                    self.assertAlmostEqual(getattr(car, key) / v, 1.0, delta=1e-5)

    def test_the_typed_ratios_are_the_published_files(self):
        """What P5 left to P6 (C2's last item): the gears, the final drive and the
        CVT's range the specs type are what the published files print; the
        F-150's and the Accord's final drive is their EPA row's axle, the CX-9's
        4.411 is not its row's 4.41 (decision 42's disclosed gap)."""
        cx9, f150, acc = (self.plants[n].car for n in ("mazda_25t", "ford_27tt", "honda_l15b7"))
        p_cx9, p_f150, p_acc = published(CX9), published(F150), published(ACCORD)
        self.assertEqual(cx9.gears, tuple(p_cx9["gear_ratios"]["value"]))
        self.assertEqual(f150.gears, tuple(p_f150["gear_ratios"]["value"]))
        self.assertEqual((acc.ratio_low_gear, acc.ratio_top_gear), tuple(p_acc["cvt_ratio_range"]["value"]))
        for car, pub in ((cx9, p_cx9), (f150, p_f150), (acc, p_acc)):
            self.assertEqual(car.final_drive, pub["final_drive"]["value"])
        self.assertEqual((f150.final_drive, acc.final_drive),
                         (p_f150["epa_test_car"]["axle_ratio"], p_acc["epa_test_car"]["axle_ratio"]))
        self.assertEqual((cx9.final_drive, p_cx9["epa_test_car"]["axle_ratio"]), (4.411, 4.41))

    def test_the_registered_cars_c1_and_top_gear_nv(self):
        """C1 on the cars the plants will hold, and the model's top-gear N/V beside
        EPA's: the CX-9's gap is 4.411 / 4.41 - 1, the others' none (C2's)."""
        for name, (path, kind, cls) in PUBLISHED_OF.items():
            veh = E.vehicle_for(self.plants[name].car)
            row = published(path)["epa_test_car"]
            with self.subTest(car=veh.car.id):
                self.assertLess(max(c1_errors(veh, published(path))), 1e-6)
                top = veh.ratio_top if cls is engines.CvtCar else veh.gears[-1]
                nv = MPH_MPS * 60.0 / (2.0 * math.pi * veh.wheel_r) * top * veh.final_drive
                self.assertLess(abs(nv / row["n_over_v_rpm_per_mph"] - 1.0 - C2.NV_GAP[path]), 1e-6)

    def test_the_peak_torques_are_the_published_ones(self):
        """Decision 43: the CX-9's from Mazda's MZ19 sheet, 310 lb-ft, opened 22
        October 2026; the F-150's from Ford's sheet, 375 lb-ft (PLAN.md 7.5); each
        converted with exact factors. The F-150's is the plan's 508.4 to its digits."""
        nm = LBF_N * 0.3048
        self.assertEqual(self.plants["mazda_25t"].car.peak_torque_nm, 310.0 * nm)
        self.assertEqual(self.plants["ford_27tt"].car.peak_torque_nm, 375.0 * nm)
        self.assertAlmostEqual(self.plants["ford_27tt"].car.peak_torque_nm, 508.4, places=1)
        print(f"\n  peak torque: CX-9 {310.0 * nm!r} Nm (310 lb-ft, MZ19), F-150 {375.0 * nm!r} Nm (375 lb-ft)")

    def test_each_registered_plants_files_include_its_published_car_file(self):
        import fingerprint as FP
        for name, (path, _, _) in PUBLISHED_OF.items():
            espec, cspec = engines.PLANTS[name]
            self.assertEqual(FP.plant_files(name), FP.PLANT_CODE + (
                f"engine_specs/{espec}.toml", f"engine_specs/{cspec}.toml",
                os.path.relpath(path, HERE).replace(os.sep, "/")))


class EpaVehicleTests(unittest.TestCase):
    def test_it_is_the_supras_gearbox_under_epas_road_load(self):
        """With A = crr m g, B = 0 and C = cd_a rho_ref / 2, EPA's force is the
        Supra's, so an EpaCar holding the Supra's box, table and shift constants
        must ask the same torque at the same rpm in the same gear (to round-off:
        the sums associate differently, which is why EpaVehicle is a new class)."""
        sup = engines.get("b58").car
        rho_ref = 1.1673038442818338
        car = engines.EpaCar(
            id="test-supra-as-epa", mass=sup.mass, road_a_n=sup.crr * sup.mass * 9.81, road_b_n_per_mps=0.0,
            road_c_n_per_mps2=0.5 * sup.cd_a * rho_ref, road_rho_ref=rho_ref, wheel_r=sup.wheel_r,
            final_drive=sup.final_drive, gears=sup.gears, driveline_eff=sup.driveline_eff,
            peak_torque_nm=sup.peak_torque_nm, shift_load=sup.shift_load, shift_rpm_max=sup.shift_rpm_max,
            upshift_min_rpm=sup.upshift_min_rpm, rpm_min=sup.rpm_min, rpm_max=sup.rpm_max,
            deliverable_torque=sup.deliverable_torque, table_rpm_lo=sup.table_rpm_lo,
            table_rpm_hi=sup.table_rpm_hi, table_rpm_step=sup.table_rpm_step, table_t_amb=sup.table_t_amb,
            table_t_block=sup.table_t_block, table_settle=sup.table_settle)
        a, b = E.EpaVehicle(car), E.Vehicle(sup)
        n = 0
        for v in np.linspace(0.5, 45.0, 37):
            for acc in (-1.0, 0.0, 0.8):
                for g in (-0.03, 0.0, 0.06, 0.12):
                    (ta, ra), (tb, rb) = a.demand(float(v), acc, g, rho=1.12), b.demand(float(v), acc, g, rho=1.12)
                    self.assertAlmostEqual(ta, tb, delta=1e-9 * max(1.0, abs(tb)))
                    self.assertAlmostEqual(ra, rb, delta=1e-9 * rb)
                    n += 1
        self.assertEqual(n, 37 * 3 * 4)
        # the control: C moved by 1e-3 moves the torque at speed
        moved = E.EpaVehicle(replace(car, road_c_n_per_mps2=car.road_c_n_per_mps2 * 1.001))
        self.assertNotAlmostEqual(moved.demand(36.0, 0.0, 0.0, rho=1.12)[0], b.demand(36.0, 0.0, 0.0, rho=1.12)[0],
                                  delta=1e-6)

    def test_the_records_take_python_values_only(self):
        """Amendment B10: a fit's NumPy scalar is refused, never converted."""
        car = epa_car(CX9, "three_term_stepped", TYPED_CX9)
        for name in ("road_a_n", "wheel_r", "mass"):
            with self.subTest(field=name):
                with self.assertRaises(TypeError):
                    replace(car, **{name: np.float64(getattr(car, name))})
        cvt = epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD)
        for name in ("kickdown_load", "cvt_rpm_min"):
            with self.subTest(field=name):
                with self.assertRaises(TypeError):
                    replace(cvt, **{name: np.float64(getattr(cvt, name))})
        with self.assertRaises(TypeError):
            replace(car, gears=tuple(np.float64(g) for g in car.gears))
        self.assertEqual(replace(car, road_a_n=float(car.road_a_n)), car)      # the control: a float passes
        # each field against its own annotation (the review of P5): a str in a float
        # field, a float or a bool in an int field, a number in a str field, refused;
        # an int in a float field taken, as TOML writes 1000 for 1000.0
        for rec, name, bad in ((car, "road_a_n", "179.9"), (car, "table_settle", 30.0),
                               (car, "table_rpm_lo", True), (car, "id", 9), (cvt, "cvt_rpm_min", "1000"),
                               (cvt, "table_rpm_step", 100.0)):
            with self.subTest(field=name, value=bad):
                with self.assertRaises(TypeError):
                    replace(rec, **{name: bad})
        self.assertEqual(replace(car, mass=2041).mass, 2041)

    def test_the_tuple_fields_take_python_values_only(self):
        """The review of P5 (22 October 2026, build step 2 P7; amendment B10): the
        scalar check skips a tuple field, so EpaCar and CvtCar check theirs
        (engines._car_tuples). A deliverable-torque table whose torques are NumPy
        floats, whose rpms are NumPy ints, floats or a bool, a table that is a list,
        or holds a list or a triple, and a stepped box's gears as a list or holding
        a NumPy float or a bool, are each refused by a dataclasses.replace, which
        converts nothing. The controls: the same values as Python ints and floats,
        int torques among them, and the empty table of a car not yet measured."""
        car = epa_car(CX9, "three_term_stepped", TYPED_CX9)
        cvt = epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD)
        for rec in (car, cvt):
            t = rec.deliverable_torque
            for what, bad in (("NumPy float64 torques", tuple((a, np.float64(b)) for a, b in t)),
                              ("NumPy float32 torques", tuple((a, np.float32(b)) for a, b in t)),
                              ("NumPy int rpms", tuple((np.int64(a), b) for a, b in t)),
                              ("float rpms", tuple((float(a), b) for a, b in t)),
                              ("a bool rpm", ((True, t[0][1]),) + t[1:]),
                              ("a list", list(t)), ("a list pair", (list(t[0]),) + t[1:]),
                              ("a triple", ((t[0][0], t[0][1], 0.0),) + t[1:])):
                with self.subTest(car=rec.id, table=what):
                    with self.assertRaisesRegex(TypeError, "deliverable_torque must be a tuple of"):
                        replace(rec, deliverable_torque=bad)
            for good in (t, tuple((a, int(b)) for a, b in t), ()):
                with self.subTest(car=rec.id, control=len(good)):
                    self.assertEqual(replace(rec, deliverable_torque=good).deliverable_torque, good)
        for what, bad in (("a list", list(car.gears)),
                          ("a NumPy float", car.gears[:-1] + (np.float64(car.gears[-1]),)),
                          ("a bool", car.gears[:-1] + (True,))):
            with self.subTest(gears=what):
                with self.assertRaisesRegex(TypeError, "gears must be a tuple of"):
                    replace(car, gears=bad)
        self.assertEqual(replace(car, gears=tuple(float(g) for g in car.gears)), car)

    def test_an_empty_table_names_the_epa_command(self):
        """Mistake 1, in a message: an EPA car's table is measured by the EPA
        completion, not by derive_params.py. Control: the Supra's still names
        derive_params.py, its own."""
        car = replace(epa_car(CX9, "three_term_stepped", TYPED_CX9), deliverable_torque=())
        with self.assertRaises(RuntimeError) as cm:
            E.EpaVehicle(car).demand(30.0, 0.5, 0.06, rho=1.12)
        self.assertIn("calibrate_epa.py complete", str(cm.exception))
        self.assertNotIn("derive_params.py", str(cm.exception))
        sup = replace(engines.get("b58").car, deliverable_torque=())
        with self.assertRaises(RuntimeError) as cm:
            E.Vehicle(sup).shift_ceiling_nm(2000.0)
        self.assertIn("python derive_params.py", str(cm.exception))


class CvtLaw(unittest.TestCase):
    def setUp(self):
        self.car = epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD)
        self.veh = E.CvtVehicle(self.car)
        self.rho = self.car.road_rho_ref

    def n_w(self, v):
        return v / self.car.wheel_r * 60.0 / (2 * np.pi)

    def check_step(self, v, a, g):
        """One demand, and what every branch must hold: rpm in the law's range, the
        ratio in the published range, and the torque f r / (ratio fd eta) at that
        ratio. Off the low-speed branch (where the converter is assumed to slip),
        two more: the engine turns at the ratio's speed, rpm = n_w x ratio x fd (a
        locked converter), and gives the road's power, T omega eta = f v -- the
        power balance itself, which the torque line alone cannot check, since it
        holds at whatever ratio the law returns (the review of P5)."""
        tq, rpm = self.veh.demand(v, a, g, rho=self.rho)
        car, veh = self.car, self.veh
        self.assertIn(veh.branch, ("low-speed", "economy", "kickdown", "power-limited"))
        self.assertTrue(car.cvt_rpm_min <= rpm <= car.rpm_max, rpm)
        self.assertTrue(car.ratio_top_gear <= veh.ratio <= car.ratio_low_gear, veh.ratio)
        f = car.mass * a + float(veh.road_force_n(v, g, rho=self.rho))
        self.assertAlmostEqual(tq * veh.ratio * car.final_drive * car.driveline_eff / car.wheel_r, f,
                               delta=1e-9 * max(1.0, abs(f)))
        if veh.branch != "low-speed":
            self.assertAlmostEqual(rpm, self.n_w(v) * veh.ratio * car.final_drive, delta=1e-9 * rpm,
                                   msg=f"{veh.branch} at {v:.3f} m/s: the engine speed is not the ratio's")
            self.assertAlmostEqual(tq * (2 * np.pi * rpm / 60.0) * car.driveline_eff, f * v,
                                   delta=1e-9 * max(1.0, abs(f * v)))
        return tq, rpm

    def test_v_zero_is_the_low_speed_branch(self):
        tq, rpm = self.check_step(0.0, 1.8, 0.0)
        self.assertEqual((self.veh.branch, rpm, self.veh.ratio), ("low-speed", 1000.0, 2.645))
        f = self.car.mass * 1.8 + self.car.road_a_n
        self.assertAlmostEqual(tq, f * self.car.wheel_r / (2.645 * 5.36) / 0.92, delta=1e-9)
        self.assertTrue(math.isfinite(tq))
        # the floor is the law's cvt_rpm_min, not the calibration's rpm_min (equal in the
        # fixture): at 1200 the launch turns 1200
        high = E.CvtVehicle(replace(self.car, cvt_rpm_min=1200.0))
        self.assertEqual(high.demand(0.0, 1.8, 0.0, rho=self.rho)[1], 1200.0)

    def test_the_launch(self):
        """make_grade_climb's launch, 0 to 130 km/h in 20 s: the low-speed branch
        exactly below the speed where the low ratio turns cvt_rpm_min (about 8.7
        km/h, PLAN.md 7.3), the law above it, and no jump in rpm at the boundary."""
        v_b = 1000.0 / (2.645 * 5.36) * 2 * np.pi / 60.0 * self.car.wheel_r
        self.assertAlmostEqual(v_b * 3.6, 8.74, delta=0.01)
        a = 130.0 / 3.6 / 20.0
        for v in np.linspace(0.0, 130.0 / 3.6, 201):
            self.check_step(float(v), a, 0.0)
            self.assertEqual(self.veh.branch == "low-speed", v < v_b, float(v))
        _, below = self.check_step(v_b * (1 - 1e-9), a, 0.0)
        _, above = self.check_step(v_b * (1 + 1e-9), a, 0.0)
        self.assertAlmostEqual(below, above, delta=1e-3)

    def test_economy_holds_the_top_ratio(self):
        v = 100.0 / 3.6
        tq, rpm = self.check_step(v, 0.0, 0.0)
        self.assertEqual(self.veh.branch, "economy")
        self.assertAlmostEqual(self.veh.ratio, 0.405, delta=1e-12)
        self.assertAlmostEqual(rpm, self.n_w(v) * 0.405 * 5.36, delta=1e-9)
        self.assertEqual(self.veh.n_eco, rpm)

    def test_the_kickdown_threshold_is_kickdown_load_of_t_del_at_n_eco(self):
        """Decision 70: the law's one discrete decision. A force that asks T_eco a
        part in 1e9 below kickdown_load x T_del(N_eco) holds the top ratio; a part
        above kicks down. Control: at kickdown_load 0.70 the first kicks down too."""
        v = 100.0 / 3.6
        n_eco = self.n_w(v) * 0.405 * 5.36
        t_th = 0.75 * self.veh.deliverable_nm(n_eco)
        self.assertEqual(self.veh.kickdown_threshold_nm(n_eco), t_th)
        f_th = t_th * (n_eco * 2 * np.pi / 60.0) * 0.92 / v
        for scale, branch in ((1 - 1e-9, "economy"), (1 + 1e-9, "kickdown")):
            with self.subTest(scale=scale):
                ratio, rpm, got, n_e, t_e = self.veh.ratio_for(v, f_th * scale)
                self.assertEqual(got, branch)
                self.assertAlmostEqual(n_e, n_eco, delta=1e-9)
                self.assertAlmostEqual(t_e / t_th, scale, delta=1e-12)
        low = E.CvtVehicle(replace(self.car, kickdown_load=0.70))
        self.assertEqual(low.ratio_for(v, f_th * (1 - 1e-9))[2], "kickdown")

    def test_the_kickdown_runs_the_smallest_speed_that_holds_target_load(self):
        v = 100.0 / 3.6
        n_eco = self.n_w(v) * 0.405 * 5.36
        f = 1.2 * 0.75 * self.veh.deliverable_nm(n_eco) * (n_eco * 2 * np.pi / 60.0) * 0.92 / v
        ratio, n_star, branch, _, _ = self.veh.ratio_for(v, f)
        self.assertEqual(branch, "kickdown")
        p = f * v / 0.92

        def holds(n):
            return p / (n * 2 * np.pi / 60.0) <= 0.65 * self.veh.deliverable_nm(n)
        self.assertTrue(holds(n_star))
        self.assertFalse(holds(n_star - E.CVT_BISECT_RPM))
        # and no 10 rpm scan point below it holds (the smallest, to the scan)
        self.assertFalse(any(holds(n) for n in np.arange(n_eco, n_star - E.CVT_BISECT_RPM, E.CVT_SCAN_RPM)))
        self.assertAlmostEqual(ratio, n_star / (self.n_w(v) * 5.36), delta=1e-12)

    def test_no_speed_holds_it_power_limited(self):
        """Mistake 9: when nothing qualifies, the most deliverable power in the
        window, and the branch says so."""
        v = 130.0 / 3.6
        f = 1e5
        ratio, n_star, branch, n_eco, _ = self.veh.ratio_for(v, f)
        self.assertEqual(branch, "power-limited")
        n_hi = min(5000.0, self.n_w(v) * 2.645 * 5.36)
        grid = [float(n) for n in np.arange(n_eco, n_hi, E.CVT_SCAN_RPM)] + [n_hi]
        self.assertEqual(n_star, max(grid, key=lambda n: self.veh.deliverable_nm(n) * n))
        self.assertAlmostEqual(n_star, 4500.0, delta=E.CVT_SCAN_RPM)   # the synthetic table's power peak

    def test_power_limited_at_30_kmh_is_the_windows_top(self):
        """The window's top, N_hi = min(rpm_max, n_w x low x fd) (PLAN.md 7.3,
        amendment F6), checked where it binds (the review of P5): at 30 km/h it is
        3433.14 rpm, below the synthetic table's 4500 rpm power peak, so under a
        force no speed holds, N* is the window's top and the ratio the low one. A
        law unbounded above would run 4500 rpm, past what the low ratio turns at
        this wheel speed under a locked converter."""
        v = 30.0 / 3.6
        n_top = self.n_w(v) * 2.645 * 5.36
        self.assertAlmostEqual(n_top, 3433.14, delta=0.01)
        ratio, n_star, branch, _, _ = self.veh.ratio_for(v, 2e4)
        self.assertEqual(branch, "power-limited")
        self.assertAlmostEqual(n_star, n_top, delta=1e-9 * n_top)
        self.assertAlmostEqual(ratio, 2.645, delta=1e-12)
        self.check_step(v, 10.0, 0.0)
        self.assertEqual(self.veh.branch, "power-limited")

    def test_a_force_at_or_below_zero_holds_n_eco(self):
        v = 100.0 / 3.6
        for f in (0.0, -500.0):
            with self.subTest(f=f):
                ratio, rpm, branch, n_eco, _ = self.veh.ratio_for(v, f)
                self.assertEqual((branch, rpm), ("economy", n_eco))
                self.assertAlmostEqual(ratio, 0.405, delta=1e-12)
        self.check_step(v, -1.0, -0.03)

    def test_the_law_is_stateless(self):
        v, f = 90.0 / 3.6, 2500.0
        first = self.veh.ratio_for(v, f)
        self.veh.demand(20.0, 1.0, 0.1, rho=self.rho)
        self.veh.demand(0.0, 0.0, 0.0, rho=self.rho)
        self.assertEqual(self.veh.ratio_for(v, f), first)
        self.assertEqual(E.CvtVehicle(self.car).ratio_for(v, f), first)

    def test_over_speed_and_an_empty_table_are_refused(self):
        with self.assertRaises(ValueError):          # the top ratio past rpm_max: about 285 km/h
            self.veh.ratio_for(300.0 / 3.6, 100.0)
        empty = E.CvtVehicle(replace(self.car, deliverable_torque=()))
        with self.assertRaises(RuntimeError) as cm:
            empty.ratio_for(100.0 / 3.6, 2000.0)
        self.assertIn("calibrate_epa.py complete", str(cm.exception))      # the EPA command, not the B58's
        self.assertNotIn("derive_params.py", str(cm.exception))

    def test_a_law_that_cannot_run_is_refused(self):
        for change in (dict(ratio_low_gear=0.405), dict(ratio_top_gear=0.0), dict(kickdown_load=1.2),
                       dict(target_load=0.0), dict(cvt_rpm_min=900.0), dict(cvt_rpm_min=5000.0),
                       dict(driveline_eff=1.5)):
            with self.subTest(change=change):
                with self.assertRaises(ValueError):
                    replace(self.car, **change)
        # the kickdown's reserve (the review of P5): a target load at or above the
        # kickdown load, each inside (0, 1], so only the reserve's own check refuses
        # it. Control: just under the kickdown load is a law that runs
        for change in (dict(target_load=0.75), dict(target_load=0.8), dict(kickdown_load=0.6)):
            with self.subTest(change=change):
                with self.assertRaises(ValueError) as cm:
                    replace(self.car, **change)
                self.assertIn("must lie below kickdown_load", str(cm.exception))
        self.assertEqual(replace(self.car, target_load=0.7499).target_load, 0.7499)


class Dispatch(unittest.TestCase):
    def test_vehicle_for_picks_each_cars_model(self):
        sup = engines.get("b58").car
        cx9 = epa_car(CX9, "three_term_stepped", TYPED_CX9)
        acc = epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD)
        self.assertIs(type(E.vehicle_for(sup)), E.Vehicle)
        self.assertIs(type(E.vehicle_for(cx9)), E.EpaVehicle)
        self.assertIs(type(E.vehicle_for(acc)), E.CvtVehicle)
        for bad in (None, object(), engines.get("b58").engine):
            with self.subTest(car=type(bad).__name__):
                with self.assertRaises(TypeError):
                    E.vehicle_for(bad)
        for cls, wrong in ((E.EpaVehicle, sup), (E.EpaVehicle, acc), (E.CvtVehicle, sup), (E.CvtVehicle, cx9)):
            with self.subTest(vehicle=cls.__name__, car=type(wrong).__name__):
                with self.assertRaises(TypeError):
                    cls(wrong)
        with self.assertRaises(TypeError):
            E.EpaVehicle(None)
        with self.assertRaises(TypeError):
            E.CvtVehicle(None)

    def test_the_environment_runs_each_cars_own_vehicle(self):
        """PLAN.md P5: SupervisoryTunerEnv builds its vehicle with vehicle_for, so an
        EPA car runs its own model in the environment, and in
        measure_deliverable_torque, which measures through it (completion's first
        step, PLAN.md 5.9 item 1). The B58's engine in the test's car records,
        synthetic tables (no EPA engine): a reset, five neutral steps of the locked
        climb, each step's demand the car's own vehicle's at that step's speed,
        acceleration, grade and air, to the bit; then a two-point table at four
        settling steps. The review of P5 (22 October 2026): with the environment's
        vehicle_for turned back to Vehicle(plant.car), no test failed. The Supra's
        environment is Supra.test_the_supras_car_and_vehicle_are_unchanged's."""
        p = engines.get("b58")
        for path, kind, typed, model in ((CX9, "three_term_stepped", TYPED_CX9, E.EpaVehicle),
                                         (ACCORD, "three_term_cvt", TYPED_ACCORD, E.CvtVehicle)):
            car = epa_car(path, kind, typed)
            plant = replace(p, car=car)
            with self.subTest(car=os.path.basename(path)):
                env = E.SupervisoryTunerEnv(E.locked_climb(plant, duration=30.0, dt=1.0), plant=plant, dt=1.0,
                                            seed=0)
                self.assertIs(type(env.veh), model)
                self.assertIs(env.veh.car, car)
                env.reset(seed=0)
                own, c = E.vehicle_for(car), env.cycle
                for _ in range(5):
                    k = env.k
                    v, nxt = float(c["v_mps"][k]), float(c["v_mps"][k + 1])
                    rho = c.get("p_baro", 101.3) * 1000.0 / (287.0 * c["t_amb"])
                    want = own.demand(v, (nxt - v) / env.dt, float(c["grade"][k]), rho=rho)
                    obs, r, term, trunc, _ = env.step(E.neutral_action())
                    self.assertEqual((env.torque_req, env.rpm), want)
                    self.assertTrue(np.all(np.isfinite(obs)) and math.isfinite(r) and not (term or trunc))
                if model is E.CvtVehicle:                 # the law ran: its last branch is kept
                    self.assertIn(env.veh.branch, ("low-speed", "economy", "kickdown", "power-limited"))
                table = E.measure_deliverable_torque((1500, 3000), plant=replace(plant, car=replace(car,
                                                                                               table_settle=4)))
                print(f"\n  the environment, {os.path.basename(path)}: {type(env.veh).__name__}, five steps; "
                      f"a two-point table {table}")
                self.assertEqual([rpm for rpm, _ in table], [1500, 3000])
                self.assertTrue(all(type(t) is float and math.isfinite(t) for _, t in table))

    def test_the_kind_names_the_record(self):
        self.assertEqual(engines.CAR_KINDS, {"two_term_stepped": engines.Car,
                                             "three_term_stepped": engines.EpaCar,
                                             "three_term_cvt": engines.CvtCar})
        self.assertEqual(engines.read_spec("a90_supra")["_meta"]["kind"], "two_term_stepped")


class Guards(unittest.TestCase):
    """Amendment B15: the training roads' builders read the Supra's two-term road
    load, so each refuses any car record but engines.Car."""

    def setUp(self):
        self.plant = engines.get("b58")
        self.sup = E.Vehicle(self.plant.car)
        self.epa = E.EpaVehicle(epa_car(CX9, "three_term_stepped", TYPED_CX9))
        self.cvt = E.CvtVehicle(epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD))

    def builders(self):
        """Each builder, by name: the `who` its own guard names first, and a call."""
        import wide_air as W
        v = np.linspace(20.0, 35.0, 40)
        grade = np.zeros(40)
        return {
            "engine_env.min_tractive_force": ("min_tractive_force", lambda veh: E.min_tractive_force(veh, 30.0, 15.0)),
            "engine_env.grade_floor": ("grade_floor", lambda veh: E.grade_floor(v, 315.0, 1.0, veh, 15.0)),
            "engine_env.extreme_speed_profile": ("extreme_speed_profile", lambda veh: E.extreme_speed_profile(
                np.random.default_rng(0), 40, 1.0, grade, 315.0, veh, 15.0)),
            "wide_air.grade_floor": ("wide_air.grade_floor",
                                     lambda veh: W.grade_floor(v, 315.0, 90.0, 1.0, veh, 15.0)),
            "wide_air.speed_profile": ("wide_air.speed_profile", lambda veh: W.speed_profile(
                np.random.default_rng(0), 40, 1.0, grade, 315.0, 90.0, veh, 15.0)),
        }

    def test_every_builder_refuses_an_epa_car_and_runs_for_the_supra(self):
        """A control per builder (amendment B15): the refusal must be the builder's
        own guard's, its name first in the message. Each grade_floor and each speed
        profile calls min_tractive_force before it reads the road load, and that
        guard raises the same TypeError, so a message that only cites B15 would
        let a builder's own guard go missing unnoticed (the review of P5)."""
        for name, (who, build) in self.builders().items():
            for veh in (self.epa, self.cvt):
                with self.subTest(builder=name, vehicle=type(veh).__name__):
                    with self.assertRaises(TypeError) as cm:
                        build(veh)
                    self.assertIn("amendment B15", str(cm.exception))
                    self.assertTrue(str(cm.exception).startswith(f"{who} builds training roads"),
                                    f"{name}: refused by another guard: {cm.exception}")
            with self.subTest(builder=name, vehicle="Vehicle"):
                out = build(self.sup)                     # the control: the Supra's car passes
                self.assertTrue(np.all(np.isfinite(out)))

    def test_thin_air_vehicle_refuses_an_epa_car(self):
        import wide_air as W
        for car in (self.epa.car, self.cvt.car):
            with self.subTest(car=type(car).__name__):
                with self.assertRaises(TypeError) as cm:
                    W.ThinAirVehicle(replace(self.plant, car=car))
                self.assertTrue(str(cm.exception).startswith("ThinAirVehicle builds training roads"),
                                str(cm.exception))
        self.assertIs(W.ThinAirVehicle(self.plant).car, self.plant.car)      # the control

    def test_the_vehicle_alone_could_not_stop_it(self):
        """Why the guard tests the car record (amendment B15): an EpaVehicle is a
        Vehicle, and min_tractive_force's own body reads only the gearbox, which an
        EpaVehicle has: without the record's type it would hand back a number."""
        self.assertIsInstance(self.epa, E.Vehicle)
        g = self.epa.gear_for(30.0, force_n=0.0)
        body = 15.0 * self.epa.gears[g] * self.epa.final_drive * self.epa.driveline_eff / self.epa.wheel_r
        self.assertTrue(math.isfinite(body))
        self.assertFalse(hasattr(self.epa, "cd_a"))


class StepRecord(unittest.TestCase):
    def test_a_cvt_is_refused_and_the_supra_has_its_gear(self):
        """Amendment B16, its second option (chosen at the review of P5): a CVT is
        never recorded, since 0 is "at rest"; the ratio and the branch are read off
        the vehicle directly."""
        import step_record

        class At:
            pass
        cvt = E.CvtVehicle(epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD))
        at = At()
        at.veh, at.v = cvt, 30.0
        _, at.rpm = cvt.demand(30.0, 0.0, 0.0, rho=1.12)
        with self.assertRaises(ValueError) as cm:
            step_record.gear(at)
        self.assertIn("A CVT is never recorded (amendment B16)", str(cm.exception))
        self.assertIsNotNone(cvt.ratio)                   # what a report reads instead
        self.assertEqual(cvt.branch, "economy")
        sup = E.Vehicle(engines.get("b58").car)
        at.veh, at.v = sup, 36.11
        _, at.rpm = sup.demand(36.11, 0.0, 0.12, rho=1.12)
        self.assertEqual(step_record.gear(at), 7)         # the locked climb's 7th (Vehicle's note)


class Fingerprint(unittest.TestCase):
    def test_a_cvt_car_is_refused_by_name(self):
        import fingerprint as FP
        p = engines.get("b58")
        cvt = replace(p, car=epa_car(ACCORD, "three_term_cvt", TYPED_ACCORD))
        with self.assertRaises(ValueError) as cm:
            FP.plant_fingerprint(plant=cvt, backend=FP.BACKEND_CYCLE)
        self.assertIn("this car has no gears; fingerprint schema 3 cannot record it", str(cm.exception))
        # the controls: a stepped EPA car is not refused for its gears (it stops later, at
        # name_of, since no registered pair of specs describes it), and the Supra fingerprints
        with self.assertRaises(LookupError):
            FP.plant_fingerprint(plant=replace(p, car=epa_car(CX9, "three_term_stepped", TYPED_CX9)),
                                 backend=FP.BACKEND_CYCLE)
        fp = FP.plant_fingerprint(plant=p, backend=FP.BACKEND_CYCLE)
        self.assertEqual(fp["gears"], [5.25, 3.36, 2.172, 1.72, 1.316, 1.0, 0.822, 0.64])

    def test_a_candidate_is_refused(self):
        """A candidate is built from in-memory values, and derived_sha would hash
        the file on disk (the review of P5). Its mark is not a field: the candidate
        built from the file's own values is the B58, value for value, and the mark
        travels with a pickle. Control: the plant get() builds fingerprints (above)."""
        import derived
        import fingerprint as FP
        p = engines.get("b58")
        cand = engines.build_candidate("b58", derived.all_params(path=os.path.join(HERE, p.engine.derived)))
        self.assertEqual(cand, p)
        self.assertEqual(engines.engine_sha(cand), engines.engine_sha(p))
        self.assertTrue(engines.is_candidate(cand))
        self.assertFalse(engines.is_candidate(p))
        self.assertTrue(engines.is_candidate(pickle.loads(pickle.dumps(cand))))
        with self.assertRaises(ValueError) as cm:
            FP.plant_fingerprint(plant=cand, backend=FP.BACKEND_CYCLE)
        self.assertIn("a candidate (engines.build_candidate)", str(cm.exception))
        with self.assertRaises(TypeError):
            engines.is_candidate(None)

    def test_an_epa_plants_files_include_its_published_car_file(self):
        """plant_sha and git_dirty_plant_files hash a plant's own files: for an EPA
        car they include the published file its mass, radius and road load are
        converted from (the review of P5). A probe car spec of a three-term kind,
        through engines.read_spec. Control: the Supra converts nothing, and the
        B58's files are build step 1's, PLANT_CODE and its two specs."""
        from unittest import mock
        import fingerprint as FP
        real = engines.read_spec

        def read_spec(name):
            if name == "_probe_cx9":
                return {"_meta": {"id": "probe-cx9", "kind": "three_term_stepped", "published": pub}}
            return real(name)
        for pub in ("engine_specs/cars/cx9_2016_25t.toml", CX9):           # relative, or absolute
            with self.subTest(published=pub), mock.patch.dict(engines.PLANTS, {"_probe": ("b58", "_probe_cx9")}), \
                    mock.patch.object(engines, "read_spec", side_effect=read_spec):
                self.assertEqual(FP.plant_files("_probe"),
                                 FP.PLANT_CODE + ("engine_specs/b58.toml", "engine_specs/_probe_cx9.toml",
                                                  "engine_specs/cars/cx9_2016_25t.toml"))
        self.assertEqual(FP.plant_files("b58"),
                         ("plant.py", "thermal.py", "engine_env.py", "derived.py", "engines.py",
                          "engine_specs/b58.toml", "engine_specs/a90_supra.toml"))


# The Supra's Car as build step 1 left it (engines.py on cf43fbb's successor
# c47907b; decision 31): its fields, in order.
SUPRA_CAR_FIELDS = ("id", "mass", "cd_a", "crr", "wheel_r", "final_drive", "gears", "driveline_eff",
                    "peak_torque_nm", "shift_load", "shift_rpm_max", "upshift_min_rpm", "rpm_min", "rpm_max",
                    "deliverable_torque", "table_rpm_lo", "table_rpm_hi", "table_rpm_step", "table_t_amb",
                    "table_t_block", "table_settle")


# THE SUPRA'S DOUBLES, PINNED TO cf43fbb (the review of P5, 22 October 2026;
# mistake 12). Vehicle.demand's (torque, rpm) on supra_demands' grid -- 46 speeds
# from 0 to 45 m/s, 3 accelerations, 4 grades, 2 air densities: 2208 doubles --
# against cf43fbb's own Vehicle, copied below and run in the same process
# (_Cf43fbbVehicle; build step 2 P7, the review of P5): the comparison holds on
# any machine, since both sides run on that machine's np.sin, np.cos and
# np.arctan. The sha256 of the doubles was the pin until then, made in a tree of
# cf43fbb (git archive cf43fbb, the identity harness's reference), where the Supra
# was Vehicle()'s class attributes, by supra_demands below run there on
# E.Vehicle():
#     hashlib.sha256(supra_demands(E.Vehicle()).tobytes()).hexdigest()
# on this laptop (PIN_MADE_ON). It is kept as the check that the copy below IS
# cf43fbb's code, and run only on the platform that made it: elsewhere NumPy may
# round its transcendentals otherwise (SVML on a Linux training device, decision
# 32), and the digest would fail with no regression behind it.
SUPRA_DEMAND_SHA256 = "d0f458126a512e480e5011d2c758899cc888c27dc4248ae2783e4d258db1cbea"
PIN_MADE_ON = ("Windows", "AMD64", "3.13.2", "2.5.3")     # platform.system(), machine(), Python, NumPy


def pin_platform():
    import platform
    return (platform.system(), platform.machine(), platform.python_version(), np.__version__)


class _Cf43fbbVehicle:
    """cf43fbb's engine_env.Vehicle, the Supra's demand as that commit computed it
    (build step 2 P7, 22 October 2026; the review of P5): its class constants and
    the four methods demand reaches -- shift_ceiling_nm, _upshift_speeds, gear_for,
    demand -- copied VERBATIM from `git show cf43fbb:engine_env.py` (lines 395-563),
    their docstrings and comments left out and every expression and literal kept,
    0.92, 800.0 and 6500.0 among them. Its deliverable-torque table is the B58's
    derived file's, which cf43fbb's DELIVERABLE_TORQUE property read through
    derived.get on each call and converted the same way; derived_sha
    326c0835548975e2 is cf43fbb's. On PIN_MADE_ON its doubles hash to
    SUPRA_DEMAND_SHA256, the digest made in cf43fbb's own tree, which is what
    shows the copy is that code."""
    mass = 1520.0
    cd_a = 0.66
    crr = 0.011
    wheel_r = 0.33
    final_drive = 3.150
    gears = (5.250, 3.360, 2.172, 1.720, 1.316, 1.000, 0.822, 0.640)
    PEAK_TORQUE_NM = 500.0
    SHIFT_LOAD = 0.75
    SHIFT_RPM_MAX = 6000.0
    UPSHIFT_MIN_RPM = 2000.0

    def __init__(self):
        import json
        import derived
        with open(derived.B58_PATH, encoding="utf-8") as fh:
            t = json.load(fh)["deliverable_torque"]
        self.DELIVERABLE_TORQUE = tuple((int(a), float(b)) for a, b in t)

    def shift_ceiling_nm(self, rpm):
        r, t = zip(*self.DELIVERABLE_TORQUE)
        return min(self.SHIFT_LOAD * self.PEAK_TORQUE_NM, float(np.interp(rpm, r, t)))

    def _upshift_speeds(self):
        out = []
        for g in self.gears[1:]:
            ratio = g * self.final_drive
            out.append(self.UPSHIFT_MIN_RPM * (2 * np.pi / 60.0) * self.wheel_r / ratio)
        return out

    def gear_for(self, v_mps, force_n=None):
        ups = self._upshift_speeds()
        g = 0
        for i, v_up in enumerate(ups):
            if v_mps >= v_up:
                g = i + 1
        if force_n is None:
            return g
        while g > 0:
            ratio = self.gears[g] * self.final_drive
            rpm_g = v_mps / self.wheel_r * ratio * 60.0 / (2 * np.pi)
            if force_n * self.wheel_r / max(ratio, .1) / 0.92 <= self.shift_ceiling_nm(rpm_g):
                break
            lower = self.gears[g - 1] * self.final_drive
            if v_mps / self.wheel_r * lower * 60.0 / (2 * np.pi) > self.SHIFT_RPM_MAX:
                break
            g -= 1
        return g

    def demand(self, v_mps, accel, grade, *, rho):
        f = (self.mass * accel
             + 0.5 * rho * self.cd_a * v_mps ** 2
             + self.crr * self.mass * 9.81 * np.cos(np.arctan(grade))
             + self.mass * 9.81 * np.sin(np.arctan(grade)))
        g = self.gear_for(v_mps, force_n=f)
        ratio = self.gears[g] * self.final_drive
        torque = f * self.wheel_r / max(ratio, .1) / 0.92
        rpm = float(np.clip(v_mps / self.wheel_r * ratio * 60.0 / (2 * np.pi), 800.0, 6500.0))
        return float(torque), rpm


def supra_demands(veh):
    """Vehicle.demand on the pinned grid, every (torque, rpm) as float64."""
    out = []
    for v in np.linspace(0.0, 45.0, 46):
        for acc in (-1.0, 0.0, 0.8):
            for g in (-0.05, 0.0, 0.12, 0.2):
                for rho in (1.12, 1.2):
                    out += veh.demand(float(v), acc, g, rho=rho)
    return np.asarray(out, dtype=np.float64)


class _RegroupedVehicle(E.Vehicle):
    """The pin's control: Vehicle.demand with its sum regrouped, m a + (drag +
    rolling) + grade -- the change PLAN.md 7.2 keeps out of the Supra's sum, equal
    in exact arithmetic and not in doubles. Everything else is Vehicle.demand's."""

    def demand(self, v_mps, accel, grade, *, rho):
        f = (self.mass * accel
             + (0.5 * rho * self.cd_a * v_mps ** 2
                + self.crr * self.mass * 9.81 * np.cos(np.arctan(grade)))
             + self.mass * 9.81 * np.sin(np.arctan(grade)))
        g = self.gear_for(v_mps, force_n=f)
        ratio = self.gears[g] * self.final_drive
        torque = f * self.wheel_r / max(ratio, .1) / self.driveline_eff
        rpm = float(np.clip(v_mps / self.wheel_r * ratio * 60.0 / (2 * np.pi),
                            self.car.rpm_min, self.car.rpm_max))
        return float(torque), rpm


class Supra(unittest.TestCase):
    def test_the_supras_car_and_vehicle_are_unchanged(self):
        """The Supra's Car has build step 1's fields, vehicle_for gives it a
        Vehicle, and that vehicle's demand, and the environment's vehicle's, are
        cf43fbb's doubles: the bytes of _Cf43fbbVehicle's, run in this process, on
        any machine (P7)."""
        p = engines.get("b58")
        self.assertIs(type(p.car), engines.Car)
        self.assertEqual(tuple(f.name for f in fields(engines.Car)), SUPRA_CAR_FIELDS)
        a = E.vehicle_for(p.car)
        self.assertIs(type(a), E.Vehicle)
        env = E.SupervisoryTunerEnv(E.locked_climb(p, duration=60.0, dt=1.0), plant=p, dt=1.0, seed=0)
        self.assertIs(type(env.veh), E.Vehicle)
        self.assertEqual(vars(env.veh).keys(), vars(E.Vehicle(p.car)).keys())
        ref = supra_demands(_Cf43fbbVehicle())
        for name, veh in (("vehicle_for(car)", a), ("the environment's", env.veh)):
            with self.subTest(vehicle=name):
                self.assertEqual(supra_demands(veh).tobytes(), ref.tobytes(),
                                 f"{name} vehicle's demand is not cf43fbb's doubles")

    def test_the_copy_is_cf43fbbs_code_on_the_machine_that_pinned_it(self):
        """On the platform that made SUPRA_DEMAND_SHA256 in cf43fbb's own tree
        (PIN_MADE_ON), the copy's doubles and the live vehicle's hash to it: the
        copy is that commit's code, not a second guess at it. Skipped elsewhere,
        with the reason printed: there NumPy's transcendentals may round otherwise,
        and the digest would fail with no regression behind it (the machine-
        independent comparison above still runs)."""
        here = pin_platform()
        if here != PIN_MADE_ON:
            print(f"\n  Supra digest SKIPPED: this platform {here} is not {PIN_MADE_ON}, where the digest was "
                  "made; the copy-to-live comparison still ran")
            self.skipTest(f"the digest was made on {PIN_MADE_ON}, this is {here}")
        for name, veh in (("cf43fbb's copy", _Cf43fbbVehicle()), ("vehicle_for(car)",
                                                                  E.vehicle_for(engines.get("b58").car))):
            with self.subTest(vehicle=name):
                self.assertEqual(hashlib.sha256(supra_demands(veh).tobytes()).hexdigest(), SUPRA_DEMAND_SHA256)

    def test_the_pin_fails_on_a_regrouped_sum(self):
        """Mistake 12: the pin above must see a change that moves no value by more
        than round-off. The regrouped sum moves some of the 2208 doubles, so its
        bytes are not the copy's, and its digest is not cf43fbb's."""
        car = engines.get("b58").car
        base, moved = supra_demands(E.Vehicle(car)), supra_demands(_RegroupedVehicle(car))
        n = int(np.sum(base != moved))
        print(f"\n  Supra pin control: the regrouped sum moves {n} of {base.size} doubles, the largest by "
              f"{np.max(np.abs(moved - base) / np.maximum(np.abs(base), 1.0)):.1e} relative")
        self.assertGreater(n, 0)
        self.assertNotEqual(moved.tobytes(), supra_demands(_Cf43fbbVehicle()).tobytes())
        self.assertNotEqual(hashlib.sha256(moved.tobytes()).hexdigest(), SUPRA_DEMAND_SHA256)


if __name__ == "__main__":
    unittest.main(verbosity=2)
