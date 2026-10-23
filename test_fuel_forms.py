"""test_fuel_forms.py -- the fuel, the lambda clip and the cycle's form are the engine's, and the B58 is still the B58.

    python test_fuel_forms.py        about 2 min; exit code 0 when all pass

Build step 2 of decision 24 (docs/build_step_2/PLAN.md, WP1; its amendments,
docs/build_step_2/AMENDMENTS.md, govern) lets three EPA engines run on the B58's
cycle model, one plant change at a time, and the B58 must stay the plant of
cf43fbb bit for bit (results/B58_IDENTITY.md). This file starts with the first
change, P1 (22 October 2026): THE FUEL IS THE ENGINE'S. Until then the heating
value and the stoichiometric ratio were plant.py's LHV = 44.0e6 and AFR_STOICH =
14.7, and thermal.py burned a literal 44.0e6 of its own -- one gasoline for every
engine, mistake 1's shape -- while each EPA map was measured on its own test
fuel and the validation contract makes the plant and thermal.py take each
engine's (results/ENGINE_THRESHOLDS.json, conventions.fuel). Now engines.Fuel
holds them, the thermal record holds a copy of the heating value that Engine
refuses to let part from it, and engines.with_fuel moves both.

The second, P2 (22 October 2026): THE POLICIES' LAMBDA CLIP IS THE ENGINE'S.
engine_env.py clipped every policy's lambda to 0.70-1.25 for every engine, while
the contract gives each EPA engine its own floor so that the neutral action
stays neutral (results/ENGINE_THRESHOLDS.md, the lambda clip, finding 10). The
bounds are the ECU record's now, and Engine refuses a clip that would hold the
baseline's own lambda.

The third, P3 (22 October 2026): FORMS B AND C. The contract's model form is A,
the B58's cycle, or an alternative that adds to it: B a linear MAP term in the
breathing, C a per-engine rich-side slope of the combustion efficiency
(results/ENGINE_THRESHOLDS.md). The cycle record carries the form and the two
terms; the B58 is form A, and its breathing is cf43fbb's expression verbatim.

The fourth, P4 (22 October 2026): FORM D, THE INTAKE CAM RUN BY THE ECU (decision
41). The contract's form D gives the breathing the intake cam phase through a
schedule cam(rpm, MAP) run by the ECU. The cycle record carries the breathing's
cam term, the ECU record the schedule, BaselineECU.cam_deg evaluates it, and the
environment hands the ECU's cam to both load loops, the baseline's and the
agent's; the B58's ECU runs no cam, and every cam it passes is None.

  TheB58sFuel   the B58's fuel is exactly 44.0e6 J/kg and 14.7, typed in its
                spec; the measured fuel flow is cf43fbb's expression bit for
                bit; the B58-only literals the plan leaves in five scripts are
                pinned to that record
  NoFuelConstant  no fuel literal and no module-level fuel name is read by
                run_cycle or the thermal step (by AST), and plant.py has none
  WithFuel      with_fuel moves both copies, and nothing else; a replace that
                moves one copy raises; the build copies the fuel into the
                thermal record and refuses a typed copy; Python floats only
                (amendment B10), finite and above 0, the two copies compared
                by their bits (P7, the review of P1)
  OneUlp        one ulp on afr_st moves the fuel flow; one ulp on the thermal
                record's heating value moves the network; one ulp through
                with_fuel moves the cycle and the network
  ThermalReplay car_thermal.thermal_replay meters a logged drive with the
                plant's own fuel, cf43fbb's expression bit for bit, and one ulp
                on afr_st moves it; a thermal record of another heating value
                than the plant's fuel is refused (amendment B6; P7)
  LambdaClip    the B58's bounds are cf43fbb's 0.70 and 1.25, typed DESIGN,
                Python floats (amendments B1, B10); Engine refuses a bound of
                another type, a floor at or below 0, and a clip that would hold
                the baseline's lambda;
                the environment's clip reads the engine's bounds: one float32
                step on the floor moves the lambda that sits on it, one float64
                ulp does not, and a ceiling of 1 holds a lean trim
  FormsBC       the B58 is form A with ve_map 0, ve_map_ref_kpa 100 and the
                shared rich slope 0.65, typed; CycleCal refuses an unknown form,
                a term its form does not have, a NumPy scalar and a value that
                is not finite; forms A+B and A+B+C at those neutral values give
                form A's doubles on the harness's units grid and over one
                random-trim episode that runs rich; finite steps off neutral,
                and one ulp on the slope at lambda 0.95, come out different
                exactly where they should; form B's eta_v is its expression to
                the bit, its reference read and its clip last; form A reads no
                MAP; map_from_airflow inverts form A only
  FormD         the B58 runs no cam: ve_cam and cam_ref_deg 0.0, cam_on 0 and the
                twelve schedule fields 0.0, typed DESIGN; the records refuse a cam
                term without D, a schedule set with the cam off, a cam_on other
                than the int 0 or 1, a NumPy scalar, a value that is not finite, a
                domain or clamp upside down, and an ECU whose cam disagrees with
                the form; BaselineECU.cam_deg is its quadratic to the bit, its
                inputs and output clamped; the breathing takes a cam exactly under
                D, the term to the bit; A+B+C+D at neutral values, and amendment
                B2's schedule at ve_cam 0, give form A's doubles on the units grid
                and over one episode, the schedule at ve_cam 1e-4 moves them; step()
                hands the ECU's cam on the lagged load to both loops, by keyword,
                and so does the deliverable-torque table; a surrogate takes none;
                the source text other files pin survives (amendment B12)
  EngineSha     engine_sha with the keys P1 to P4 add stripped is build step 1's,
                99d2a9658b1258a7, over exactly build step 1's key set (amendment
                B11); unstripped it is the b58 lens's widened plant's

Every check has a control that must fail (mistake 12: a check that cannot fail
is not a check). The neutral forms are run through an episode here and through
whole episodes by the certificate harness's HARNESS_SET controls (amendment B2);
the harness lives outside the repository, so the episode here is what guards
step() on every run.
"""
import ast
import hashlib
import inspect
import json
import os
import sys
import tomllib
import unittest
from dataclasses import asdict, replace
from unittest import mock

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import car_thermal as CT  # noqa: E402
import engine_env as E  # noqa: E402
import engines  # noqa: E402
import plant as P  # noqa: E402
import thermal as T  # noqa: E402

# The plant these checks are made on, named: the B58 in its Supra.
PLANT = engines.get("b58")
ENG = PLANT.engine


def _up(x):
    """One float64 ulp above x, as a Python float (amendment B10)."""
    return float(np.nextafter(x, np.inf))


# ------------------------------------------------------------- the B58's fuel
# The literals the plan leaves where they are, because they belong to the B58 and
# folding them into a record read would change bits (PLAN.md WP1 P1): each is
# pinned to the B58's fuel record, so changing that record names them. (file,
# text, how often it appears, the literal, the record's value in the literal's
# unit.) 44.0e3 is the heating value in J/g.
B58_LITERALS = (
    ("calibrate_thermal.py", 'q = d["fuel"][i] * 44.0e3', 2, 44.0e3, lambda f: f.lhv_j_per_kg / 1e3),
    ("substep_fit_check.py", 'q = d["fuel"][i] * 44.0e3', 2, 44.0e3, lambda f: f.lhv_j_per_kg / 1e3),
    ("model_vs_data.py", "frac * f[i] * 1e-3 * 44.0e6", 1, 44.0e6, lambda f: f.lhv_j_per_kg),
    ("validate.py", "me = mf * (1.0 + 14.7 * 1.0)", 1, 14.7, lambda f: f.afr_st),
    ("verify_docs.py", "fu = (d.air_gps / (14.7 * d.lam))", 1, 14.7, lambda f: f.afr_st),
)


def literal_problems(pins, fuel, read):
    """Every pin whose text is not in its file as often as it says, or whose
    literal is not `fuel`'s value. `read(path)` returns a file's text."""
    out = []
    for path, text, count, literal, value in pins:
        n = read(path).count(text)
        if n != count:
            out.append(f"{path}: {text!r} appears {n} times, not {count}")
        if value(fuel) != literal:
            out.append(f"{path}: the literal {literal!r} is not this fuel's {value(fuel)!r}")
    return out


def _read(path):
    with open(os.path.join(HERE, path), encoding="utf-8") as fh:
        return fh.read()


class TheB58sFuel(unittest.TestCase):
    def test_the_b58s_fuel_is_the_old_constants(self):
        """44.0e6 J/kg and 14.7, the doubles of plant.py's LHV and AFR_STOICH and
        thermal.py's literal on cf43fbb; the thermal copy is the same double, and
        typed_engine, which reads the spec alone, builds the same fuel."""
        self.assertEqual(ENG.fuel, engines.Fuel(lhv_j_per_kg=44.0e6, afr_st=14.7))
        self.assertEqual(ENG.fuel.lhv_j_per_kg.hex(), (44.0e6).hex())
        self.assertEqual(ENG.fuel.afr_st.hex(), (14.7).hex())
        self.assertEqual(ENG.thermal.fuel_lhv_j_per_kg.hex(), (44.0e6).hex())
        self.assertEqual(engines.typed_engine("b58").fuel, ENG.fuel)
        spec = engines.read_spec("b58")
        self.assertEqual(spec["fuel"], {"lhv_j_per_kg": 44.0e6, "afr_st": 14.7})
        self.assertNotIn("fuel_lhv_j_per_kg", spec["thermal"], "the copy is never typed")

    def test_the_measured_fuel_is_cf43fbbs_expression(self):
        """car_thermal.measured_fuel_gps with the B58's afr_st is `air / (14.7 * lam)`
        bit for bit, its two fallbacks included (a stopped engine, a lambda
        placeholder): the inputs of the thermal fit, so the derived file, do not
        move. The control: one ulp on afr_st does move it."""
        rng = np.random.default_rng(22)
        air = rng.uniform(1.0, 280.0, 5000)
        lam = rng.uniform(0.6, 1.3, 5000)
        rpm = rng.uniform(0.0, 6500.0, 5000)
        air[::97], lam[::89], lam[::83] = np.nan, np.nan, 0.3
        a = np.where(np.isfinite(air) & (np.nan_to_num(rpm) > 400.0), air, 0.0)
        lm = np.where(np.isfinite(lam) & (lam > 0.5), lam, 1.0)
        old = a / (14.7 * lm)
        new = CT.measured_fuel_gps(air, lam, rpm, afr_st=ENG.fuel.afr_st)
        self.assertEqual(new.tobytes(), old.tobytes())
        moved = CT.measured_fuel_gps(air, lam, rpm, afr_st=_up(ENG.fuel.afr_st))
        self.assertGreater(int((moved != new).sum()), 0)

    def test_the_b58_only_literals_are_its_fuel(self):
        """The five scripts' literals are the B58's fuel, and the pin can fail: with
        another fuel every pin is reported, and so is a text that is gone (the
        thermal step's own literal, which P1 removed)."""
        self.assertEqual(literal_problems(B58_LITERALS, ENG.fuel, _read), [])
        other = engines.Fuel(lhv_j_per_kg=43.0e6, afr_st=14.6)
        self.assertEqual(len(literal_problems(B58_LITERALS, other, _read)), len(B58_LITERALS))
        gone = (("thermal.py", "q_fuel = mdot_fuel_gps * 1e-3 * 44.0e6", 1, 44.0e6,
                 lambda f: f.lhv_j_per_kg),)
        self.assertEqual(len(literal_problems(gone, ENG.fuel, _read)), 1)


# ------------------------------------------------------- no fuel constant left
FUEL_NAMES = frozenset({"LHV", "AFR_STOICH"})
FUEL_LITERALS = (44.0e6, 44.0e3, 14.7)          # J/kg, J/g, the ratio: the B58's, as cf43fbb wrote them


def _function(tree, qualname):
    """The FunctionDef `qualname` ("run_cycle", "ThermalNetwork._substep") in `tree`."""
    body = tree.body
    for part in qualname.split("."):
        node = next(n for n in body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name == part)
        body = node.body
    return node


def fuel_constants_in(src, qualname, module_globals):
    """(line, what) for every fuel literal in the function `qualname` of `src`, and
    every module-level name it reads that is a fuel property: one of FUEL_NAMES,
    or a global whose value is one of FUEL_LITERALS (a renamed constant). A name
    the function binds itself -- a parameter, a local, a nested def -- is its own."""
    fn = _function(ast.parse(src), qualname)
    bound = {a.arg for a in ast.walk(fn) if isinstance(a, ast.arg)}
    bound |= {n.id for n in ast.walk(fn) if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    bound |= {n.name for n in ast.walk(fn) if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n is not fn}

    def fuel_number(v):
        return isinstance(v, (int, float)) and not isinstance(v, bool) and v in FUEL_LITERALS
    found = []
    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and fuel_number(node.value):
            found.append((node.lineno, f"literal {node.value!r}"))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load) and node.id not in bound:
            if node.id in FUEL_NAMES or fuel_number(module_globals.get(node.id)):
                found.append((node.lineno, f"module name {node.id}"))
        elif isinstance(node, ast.Attribute) and node.attr in FUEL_NAMES:
            found.append((node.lineno, f"attribute .{node.attr}"))
    return found


class NoFuelConstant(unittest.TestCase):
    def test_run_cycle_and_the_thermal_step_read_the_engines_fuel_only(self):
        """No fuel literal and no module-level fuel name in plant.run_cycle, or in
        ThermalNetwork.step and _substep; and plant.py no longer has LHV or
        AFR_STOICH for anything else to reach."""
        for path, module, names in (("plant.py", P, ("run_cycle",)),
                                    ("thermal.py", T, ("ThermalNetwork.step", "ThermalNetwork._substep"))):
            src = _read(path)
            for name in names:
                with self.subTest(function=name):
                    self.assertEqual(fuel_constants_in(src, name, vars(module)), [])
        for name in FUEL_NAMES:
            self.assertFalse(hasattr(P, name), f"plant.{name} is back")

    def test_the_ast_check_can_fail(self):
        """cf43fbb's own three lines are flagged, and so is a fuel constant under
        another name; the engine's fuel read through a local or an attribute is not."""
        cf43fbb = {
            "run_cycle": ("def run_cycle(op, *, engine):\n"
                          "    m_fuel = m_air / (AFR_STOICH * op.lam)\n"
                          "    q_total = min(m_fuel, m_air / AFR_STOICH) * LHV * eta_comb\n"),
            "ThermalNetwork._substep": ("class ThermalNetwork:\n"
                                        "    def _substep(self, dt, mdot_fuel_gps):\n"
                                        "        q_fuel = mdot_fuel_gps * 1e-3 * 44.0e6\n"),
        }
        consts = {"LHV": 44.0e6, "AFR_STOICH": 14.7}
        self.assertEqual(len(fuel_constants_in(cf43fbb["run_cycle"], "run_cycle", consts)), 3)
        self.assertEqual(fuel_constants_in(cf43fbb["ThermalNetwork._substep"], "ThermalNetwork._substep", {}),
                         [(3, "literal 44000000.0")])
        renamed = "def run_cycle(op, *, engine):\n    return m / (STOICH * op.lam)\n"
        self.assertEqual(fuel_constants_in(renamed, "run_cycle", {"STOICH": 14.7}),
                         [(2, "module name STOICH")])
        clean = ("def run_cycle(op, *, engine):\n    fuel = engine.fuel\n"
                 "    return m / (fuel.afr_st * op.lam) * fuel.lhv_j_per_kg\n")
        self.assertEqual(fuel_constants_in(clean, "run_cycle", consts), [])


# ------------------------------------------------------------------ with_fuel
OTHER = engines.Fuel(lhv_j_per_kg=43.0e6, afr_st=14.6)     # not a fuel of this project: a probe


class WithFuel(unittest.TestCase):
    def test_with_fuel_moves_both_copies_and_nothing_else(self):
        e = engines.with_fuel(ENG, OTHER)
        self.assertEqual(e.fuel, OTHER)
        self.assertEqual(e.thermal.fuel_lhv_j_per_kg, OTHER.lhv_j_per_kg)
        self.assertEqual(replace(e.thermal, fuel_lhv_j_per_kg=ENG.thermal.fuel_lhv_j_per_kg), ENG.thermal)
        self.assertEqual(replace(e, fuel=ENG.fuel, thermal=ENG.thermal), ENG)
        self.assertEqual(ENG.fuel.lhv_j_per_kg, 44.0e6, "the plant other callers hold is untouched")
        self.assertEqual(engines.with_fuel(e, ENG.fuel), ENG, "and the way back is the same plant")

    def test_a_replace_that_moves_one_copy_raises(self):
        """The fuel alone, the thermal copy alone, the copy as a NumPy float of the
        same value: each refused by Engine. The control: a replace that moves
        only afr_st, which has one copy, is not."""
        with self.assertRaises(ValueError):
            replace(ENG, fuel=replace(ENG.fuel, lhv_j_per_kg=43.0e6))
        with self.assertRaises(ValueError):
            replace(ENG, thermal=replace(ENG.thermal, fuel_lhv_j_per_kg=43.0e6))
        with self.assertRaises(ValueError):
            replace(ENG, thermal=replace(ENG.thermal, fuel_lhv_j_per_kg=np.float64(44.0e6)))
        e = replace(ENG, fuel=replace(ENG.fuel, afr_st=14.6))
        self.assertEqual((e.fuel.afr_st, e.thermal.fuel_lhv_j_per_kg), (14.6, 44.0e6))

    def test_a_fuel_must_be_finite_and_above_zero(self):
        """The review of P1 (22 October 2026, build step 2 P7): Fuel refuses a NaN,
        an infinity, a zero of either sign and a negative value in either field,
        each with its own message -- a NaN fuel reached with_fuel and was refused
        by Engine's message about two fuels, a zero afr_st divides the fuel mass by
        zero. And Engine compares the two heating-value copies by their bits: a
        thermal copy of -0.0 beside a fuel of 0.0, equal under ==, is refused (the
        fuel built past its own check with object.__new__, the one way left to put
        a zero in an Engine). The controls: the B58's fuel builds, a copy of the
        same bits is accepted, and with_fuel of the B58's own fuel is its engine."""
        for field in ("lhv_j_per_kg", "afr_st"):
            for bad in (float("nan"), float("inf"), float("-inf"), 0.0, -0.0, -14.7):
                kw = dict(lhv_j_per_kg=44.0e6, afr_st=14.7)
                kw[field] = bad
                with self.subTest(field=field, value=repr(bad)):
                    with self.assertRaisesRegex(ValueError, rf"Fuel\.{field} must be finite and above 0"):
                        engines.Fuel(**kw)
        self.assertEqual(engines.Fuel(lhv_j_per_kg=44.0e6, afr_st=14.7), ENG.fuel)
        self.assertEqual(engines.with_fuel(ENG, engines.Fuel(lhv_j_per_kg=44.0e6, afr_st=14.7)), ENG)
        zero = object.__new__(engines.Fuel)
        object.__setattr__(zero, "lhv_j_per_kg", 0.0)
        object.__setattr__(zero, "afr_st", 14.7)
        self.assertEqual(-0.0, 0.0, "the reason for the bits: == does not tell them apart")
        with self.assertRaisesRegex(ValueError, "the network would burn another fuel than the cycle"):
            replace(ENG, fuel=zero, thermal=replace(ENG.thermal, fuel_lhv_j_per_kg=-0.0))
        same = replace(ENG, fuel=zero, thermal=replace(ENG.thermal, fuel_lhv_j_per_kg=0.0))
        self.assertEqual(same.thermal.fuel_lhv_j_per_kg.hex(), (0.0).hex())

    def test_with_fuel_takes_an_engine_and_a_fuel(self):
        with self.assertRaises(TypeError):
            engines.with_fuel(None, OTHER)
        with self.assertRaises(TypeError):
            engines.with_fuel(ENG, None)
        with self.assertRaises(TypeError):
            engines.with_fuel(engines.typed_engine("b58"), OTHER)     # it has no thermal record
        with self.assertRaises(TypeError):
            engines.with_fuel(PLANT, OTHER)                           # a plant: pass plant.engine

    def test_the_build_copies_the_fuel_and_refuses_a_typed_copy(self):
        """_build copies [fuel] lhv_j_per_kg into the thermal record; the same value
        typed in [thermal] is refused (a second source for one number), and so is
        a spec without [fuel]. The control: the spec as it is builds the plant
        engines.get holds."""
        real = engines.read_spec

        def spec_with(change):
            def read(name):
                s = real(name)
                if name == "b58":
                    change(s)
                return s
            return read
        self.assertEqual(engines._build("b58", "a90_supra"), PLANT)
        typed = spec_with(lambda s: s["thermal"].update(fuel_lhv_j_per_kg=44.0e6))
        with mock.patch.object(engines, "read_spec", side_effect=typed):
            with self.assertRaises(ValueError):
                engines._build("b58", "a90_supra")
        with mock.patch.object(engines, "read_spec", side_effect=spec_with(lambda s: s.pop("fuel"))):
            with self.assertRaises(ValueError):
                engines._build("b58", "a90_supra")

    def test_python_floats_only(self):
        """Amendment B10: under NEP 50 a NumPy scalar is not a Python float (14.7
        times a float32 is a float32, np.float64(14.7) times one a float64). Fuel
        refuses one, or an int; every scalar field of the B58 as built is a
        Python float, int or str. The control: the walk finds a NumPy scalar."""
        for bad in (dict(lhv_j_per_kg=np.float64(44.0e6), afr_st=14.7),
                    dict(lhv_j_per_kg=44.0e6, afr_st=np.float32(14.7)),
                    dict(lhv_j_per_kg=44000000, afr_st=14.7)):
            with self.subTest(fuel=bad):
                with self.assertRaises(TypeError):
                    engines.Fuel(**bad)
        self.assertIs(type(np.float32(0.5) * 14.7), np.float32, "NEP 50, the reason for the rule")
        self.assertIs(type(np.float32(0.5) * np.float64(14.7)), np.float64)
        self.assertEqual(not_python_scalars(asdict(PLANT)), [])
        self.assertIs(type(ENG.thermal.fuel_lhv_j_per_kg), float)
        poked = asdict(PLANT)
        poked["engine"]["fuel"]["afr_st"] = np.float64(14.7)
        self.assertEqual(not_python_scalars(poked), ["engine.fuel.afr_st (float64)"])


def not_python_scalars(d, path=""):
    """Every leaf of an asdict tree (tuples included) that is not a Python float,
    int or str, as 'record.field (type)'."""
    out = []
    for k, v in d.items():
        where = f"{path}.{k}" if path else k
        if isinstance(v, dict):
            out += not_python_scalars(v, where)
            continue
        flat = [v]
        while any(isinstance(x, tuple) for x in flat):
            flat = [y for x in flat for y in (x if isinstance(x, tuple) else (x,))]
        out += [f"{where} ({type(x).__name__})" for x in flat if type(x) not in (float, int, str)]
    return out


# --------------------------------------------------------------------- one ulp
# Operating points of the cycle model: three speeds, three loads, three lambdas.
GRID = [P.Operating(rpm=rpm, map_kpa=mp, iat_k=320.0, ect_k=363.0, spark_btdc=12.0, lam=lam,
                    p_exh_kpa=max(105.0, mp * 1.15))
        for rpm in (1500.0, 2706.0, 4800.0) for mp in (60.0, 140.0, 210.0) for lam in (0.81, 0.9, 1.0)]
CYCLE_FIELDS = ("torque_nm", "egt_c", "knock_integral", "mdot_fuel_gps", "t_max_k")


def _cycles(engine):
    return np.array([[getattr(P.run_cycle(op, engine=engine), f) for f in CYCLE_FIELDS] for op in GRID])


def _network(params):
    """thermal.py's own worked example, every state: a cruise, then a climb."""
    tn = T.ThermalNetwork(params)
    tn.reset(t_amb=315.0)
    out = []
    for i in range(1801):
        climbing = i > 300
        mf = 7.5 if climbing else 1.6
        tn.step(1.0, mf, mf * 15.0, 1150.0 if climbing else 950.0, 315.0, 22.0 if climbing else 33.0,
                1.0 if tn.t_block > 373.0 else 0.0, rpm=3000.0 if climbing else 2200.0)
        out.append(tn.state())
    return np.array(out)


class OneUlp(unittest.TestCase):
    """mistake 25: an output that does not move when its input changed means the
    input never reached it. One float64 ulp is the smallest change there is."""

    @classmethod
    def setUpClass(cls):
        cls.cycles = _cycles(ENG)
        cls.network = _network(ENG.thermal)

    def test_the_same_fuel_moves_nothing(self):
        """The control for the two below: with_fuel with the engine's own fuel, and
        a thermal record copied with its own value, give the same bits."""
        self.assertEqual(_cycles(engines.with_fuel(ENG, ENG.fuel)).tobytes(), self.cycles.tobytes())
        same = replace(ENG.thermal, fuel_lhv_j_per_kg=ENG.thermal.fuel_lhv_j_per_kg)
        self.assertEqual(_network(same).tobytes(), self.network.tobytes())

    def test_one_ulp_on_afr_st_moves_the_fuel_flow(self):
        e = engines.with_fuel(ENG, replace(ENG.fuel, afr_st=_up(ENG.fuel.afr_st)))
        k = CYCLE_FIELDS.index("mdot_fuel_gps")
        moved = _cycles(e)[:, k] != self.cycles[:, k]
        print(f"\n  afr_st {ENG.fuel.afr_st!r} -> {e.fuel.afr_st!r}: the fuel flow moved at "
              f"{int(moved.sum())} of {len(GRID)} operating points")
        self.assertGreater(int(moved.sum()), 0)

    def test_one_ulp_on_the_thermal_records_lhv_moves_the_network(self):
        """Built directly as a ThermalParams, which Engine would refuse: the
        network alone reads it."""
        tp = replace(ENG.thermal, fuel_lhv_j_per_kg=_up(ENG.thermal.fuel_lhv_j_per_kg))
        moved = _network(tp) != self.network
        print(f"\n  thermal LHV {ENG.thermal.fuel_lhv_j_per_kg!r} -> {tp.fuel_lhv_j_per_kg!r}: "
              f"{int(moved.sum())} of {moved.size} network states moved (block, oil, turbine: "
              f"{moved.any(axis=0).tolist()})")
        self.assertGreater(int(moved.sum()), 0)

    def test_one_ulp_through_with_fuel_moves_the_cycle_and_the_network(self):
        """Both copies reach an output: the cycle's heat release and the network's
        fuel heat."""
        e = engines.with_fuel(ENG, replace(ENG.fuel, lhv_j_per_kg=_up(ENG.fuel.lhv_j_per_kg)))
        n_cycle = int((_cycles(e) != self.cycles).sum())
        n_network = int((_network(e.thermal) != self.network).sum())
        print(f"\n  LHV + 1 ulp through with_fuel: {n_cycle} cycle values and {n_network} network "
              "states moved")
        self.assertGreater(n_cycle, 0)
        self.assertGreater(n_network, 0)


# ------------------------------------------------------- the replay's fuel
def _cf43fbb_fuel(d, afr_st):
    """cf43fbb's measured fuel flow on a drive's grid `d` (car_thermal.log_grid):
    `air / (afr_st * lam)` with its two fallbacks, a stopped engine and a lambda
    placeholder, typed here rather than called, so the replay is checked against
    the expression and not against itself."""
    air, lam, rpm = d.air_gps.to_numpy(), d.lam.to_numpy(), d.rpm.to_numpy()
    a = np.where(np.isfinite(air) & (np.nan_to_num(rpm) > 400.0), air, 0.0)
    lm = np.where(np.isfinite(lam) & (lam > 0.5), lam, 1.0)
    return a / (afr_st * lm)


class ThermalReplay(unittest.TestCase):
    """Amendment B6, guarded (22 October 2026, build step 2 P7; the review of P1):
    car_thermal.thermal_replay meters the logged air with the PLANT's fuel, and the
    network it drives burns that same fuel. Until this class only the scan's
    presence check (test_engine_threading, `afr_st=` given) stood behind it, which
    a literal 14.7 or typed_engine("b58") inside thermal_replay would pass (mistake
    1). On the sustained drive (car_thermal.SUSTAINED_DRIVE), the B58's own log."""

    @classmethod
    def setUpClass(cls):
        cls.grid = CT.log_grid(CT.SUSTAINED_DRIVE)
        cls.b58 = CT.thermal_replay(CT.SUSTAINED_DRIVE, plant=PLANT)

    def test_the_replay_meters_the_plants_own_fuel(self):
        """The B58's replay meters with 14.7, cf43fbb's expression bit for bit; a
        plant whose afr_st is one ulp higher (engines.with_fuel) meters with its
        own, its expression bit for bit, and its fuel flow moves (mistake 25): a
        replay that named the B58's fuel, or typed 14.7, fails here."""
        self.assertEqual(self.b58["fuel"].tobytes(), _cf43fbb_fuel(self.grid, 14.7).tobytes())
        up = _up(ENG.fuel.afr_st)
        other = replace(PLANT, engine=engines.with_fuel(ENG, replace(ENG.fuel, afr_st=up)))
        r = CT.thermal_replay(CT.SUSTAINED_DRIVE, plant=other)
        moved = int((r["fuel"] != self.b58["fuel"]).sum())
        print(f"\n  thermal_replay, afr_st {ENG.fuel.afr_st!r} -> {up!r}: the fuel flow moved at {moved} of "
              f"{r['fuel'].size} seconds of {CT.SUSTAINED_DRIVE}")
        self.assertGreater(moved, 0)
        self.assertEqual(r["fuel"].tobytes(), _cf43fbb_fuel(self.grid, up).tobytes())

    def test_params_must_burn_the_plants_fuel(self):
        """A `params` whose heating value is not the plant's -- another fuel's, one
        ulp off, or the same value as a NumPy float (amendment B10) -- is refused
        before a second is replayed: the network would burn one fuel and the replay
        meter another. The controls: model_vs_data's variant, the plant's own
        thermal record with twice the oil capacity, replays on the same fuel flow
        and moves the oil node; and a plant moved to another fuel by with_fuel,
        given its own thermal record, replays on that fuel's flow."""
        for bad in (43.0e6, _up(ENG.fuel.lhv_j_per_kg), np.float64(ENG.fuel.lhv_j_per_kg)):
            with self.subTest(lhv=repr(bad)):
                with self.assertRaisesRegex(ValueError, "would burn another fuel than the fuel flow"):
                    CT.thermal_replay(CT.SUSTAINED_DRIVE, params=replace(ENG.thermal, fuel_lhv_j_per_kg=bad),
                                      plant=PLANT)
        oil = CT.thermal_replay(CT.SUSTAINED_DRIVE, params=replace(ENG.thermal, c_oil=ENG.thermal.c_oil * 2.0),
                                plant=PLANT)
        self.assertEqual(oil["fuel"].tobytes(), self.b58["fuel"].tobytes())
        self.assertGreater(int((oil["oil_model"] != self.b58["oil_model"]).sum()), 0)
        e = engines.with_fuel(ENG, OTHER)
        r = CT.thermal_replay(CT.SUSTAINED_DRIVE, params=e.thermal, plant=replace(PLANT, engine=e))
        self.assertEqual(r["fuel"].tobytes(), _cf43fbb_fuel(self.grid, OTHER.afr_st).tobytes())


# ------------------------------------------------------------- the lambda clip
def _with_ecu(plant, **changes):
    """`plant` with these fields of its ECU record changed, through Engine, whose
    check runs on the new record."""
    return replace(plant, engine=replace(plant.engine, ecu=replace(plant.engine.ecu, **changes)))


def _rich(plant):
    """`plant` with an ECU that enriches to its full depth from the first second on
    any road: every gate open (no load gate, the rpm and dwell ramps done at 1 rpm
    and 1 s), so the baseline's lambda is 1 - enr_depth, 0.81 on the B58: the
    deepest lambda the floor must stay under."""
    return _with_ecu(plant, enr_load=0.0, enr_rpm_lo=0.0, enr_rpm_hi=1.0, enr_dwell_lo=0.0, enr_dwell_hi=1.0)


def _agent_lams(plant, trim, n):
    """The agent's lambda, info["lam"], over the first n seconds of the plant's
    locked climb, with the network's lambda action held at `trim` (-1 the trim's
    most negative, ACT_LO[1] = -0.15; +1 its most positive, +0.06; None the
    neutral action's, a trim of exactly 0) and the rest of the action neutral.
    The trim slews 0.03 a second from 0."""
    env = E.SupervisoryTunerEnv(E.locked_climb(plant, duration=30.0, dt=1.0), plant=plant, dt=1.0, seed=0)
    env.reset(seed=0)
    act = E.neutral_action().copy()
    if trim is not None:
        act[1] = trim
    return [env.step(act)[4]["lam"] for _ in range(n)]


def _f32_up(x):
    """The next float32 above float32(x), as a Python float: the smallest change
    the policies' float32 lambda can see (amendment B1)."""
    return float(np.nextafter(np.float32(x), np.float32(np.inf)))


class LambdaClip(unittest.TestCase):
    """P2 (22 October 2026): the clip on every policy's lambda is the engine's,
    ecu.lam_floor and ecu.lam_ceiling, where engine_env.py had 0.70 and 1.25."""

    def test_the_b58s_bounds_are_the_old_literals(self):
        """0.70 and 1.25, the doubles of engine_env.py's literals on cf43fbb, typed
        DESIGN in the B58's spec, and Python floats (amendments B1, B10). The
        reason for the type, on the clip itself: NumPy 2 casts a Python float
        bound to the float32 of the policies' lambda, as it cast the literal; a
        NumPy float64 bound turns the result float64, another double where the
        floor binds."""
        ecu = ENG.ecu
        self.assertIs(type(ecu.lam_floor), float)
        self.assertIs(type(ecu.lam_ceiling), float)
        self.assertEqual((ecu.lam_floor.hex(), ecu.lam_ceiling.hex()), ((0.70).hex(), (1.25).hex()))
        with open(os.path.join(HERE, "engine_specs", "b58.toml"), "rb") as fh:
            raw = tomllib.load(fh)["ecu"]
        self.assertEqual({k: (raw[k]["value"], raw[k]["label"]) for k in ("lam_floor", "lam_ceiling")},
                         {"lam_floor": (0.70, "DESIGN"), "lam_ceiling": (1.25, "DESIGN")})
        x = np.float32(0.66)
        self.assertIs(type(np.clip(x, ecu.lam_floor, ecu.lam_ceiling)), np.float32)
        self.assertEqual(float(np.clip(x, ecu.lam_floor, ecu.lam_ceiling)), float(np.float32(0.70)))
        self.assertIs(type(np.clip(x, np.float64(ecu.lam_floor), ecu.lam_ceiling)), np.float64)
        self.assertNotEqual(float(np.clip(x, np.float64(ecu.lam_floor), ecu.lam_ceiling)),
                            float(np.clip(x, ecu.lam_floor, ecu.lam_ceiling)))

    def test_engine_refuses_a_clip_that_would_hold_the_baselines_lambda(self):
        """The B58's ECU enriches to 1 - enr_depth = 0.81 at most. A floor above
        that (one ulp is enough), a ceiling below 1 (one ulp), a NaN floor, and a
        negative depth -- which would lean the baseline to 1.30, past the B58's
        ceiling, and which the plan's two conditions alone let through -- are
        each refused. So is a floor at or below 0 with the full depth 1 (the
        review of P2, 22 October 2026, build step 2 P7): the conditions above
        let it through, and the baseline would run lambda 0, a fuel mass divided
        by zero. The controls: the floor at exactly 1 - enr_depth and the ceiling
        at exactly 1, the edges of a clip that never holds the baseline, are
        built, and so is a small floor above 0 under a depth that leaves room."""
        edge = 1.0 - ENG.ecu.enr_depth
        self.assertEqual(edge, 0.81)
        for bad in (dict(lam_floor=_up(edge)), dict(lam_floor=0.95),
                    dict(lam_ceiling=float(np.nextafter(1.0, 0.0))), dict(lam_ceiling=0.9),
                    dict(lam_floor=float("nan")), dict(enr_depth=-0.30),
                    dict(lam_floor=0.0, enr_depth=1.0), dict(lam_floor=-0.5, enr_depth=1.0),
                    dict(lam_floor=float("-inf"), enr_depth=1.0)):
            with self.subTest(**bad):
                # the refusal must be the clip's own (the review of P7: a refusal
                # for another reason would pass a bare assertRaises)
                with self.assertRaisesRegex(ValueError, "would clip the baseline's"):
                    _with_ecu(PLANT, **bad)
        for good in (dict(lam_floor=edge), dict(lam_ceiling=1.0), dict(lam_floor=edge, lam_ceiling=1.0),
                     dict(lam_floor=0.05, enr_depth=0.95)):
            with self.subTest(**good):
                e = _with_ecu(PLANT, **good).engine.ecu
                self.assertEqual({k: getattr(e, k) for k in good}, good)

    def test_a_bound_that_is_not_a_python_float_is_refused(self):
        """A NumPy float64 or float32, or an int, is refused (TypeError), never
        converted without a word, whatever its value. The control: the same
        values as Python floats build the B58's own engine."""
        for bad in (dict(lam_floor=np.float64(0.70)), dict(lam_floor=np.float32(0.70)),
                    dict(lam_ceiling=np.float64(1.25)), dict(lam_ceiling=1)):
            with self.subTest(**bad):
                with self.assertRaises(TypeError):
                    _with_ecu(PLANT, **bad)
        self.assertEqual(_with_ecu(PLANT, lam_floor=0.70, lam_ceiling=1.25), PLANT)

    def test_the_spec_must_type_both_bounds(self):
        """No default clip (mistake 1): a spec without lam_floor or lam_ceiling does
        not build, and one whose floor would hold the baseline is refused when the
        plant is built. The control: the spec as it is builds the plant
        engines.get holds."""
        real = engines.read_spec

        def spec_with(change):
            def read(name):
                s = real(name)
                if name == "b58":
                    change(s)
                return s
            return read
        self.assertEqual(engines._build("b58", "a90_supra"), PLANT)
        for what, change in (("no floor", lambda s: s["ecu"].pop("lam_floor")),
                             ("no ceiling", lambda s: s["ecu"].pop("lam_ceiling")),
                             ("floor 0.82", lambda s: s["ecu"].update(lam_floor=0.82))):
            with self.subTest(what):
                with mock.patch.object(engines, "read_spec", side_effect=spec_with(change)):
                    with self.assertRaises(ValueError):
                        engines._build("b58", "a90_supra")

    def test_the_environment_clips_to_the_engines_bounds(self):
        """Mistake 25: each bound must reach the agent's lambda. With the ECU at its
        deepest enrichment (0.81) and the trim driven to -0.15, the agent's lambda
        comes to sit on float32(lam_floor), 0.699999988079071. One float32 step
        on the floor moves exactly the steps that sit on it, to the new float32
        floor, and no other; one float64 ulp moves none, because float32 of 0.70
        plus one ulp is float32(0.70) (amendment B1: the plan's 3.5 expected
        DIFFERENT from that ulp). With no trim the lambda is float32 of the
        baseline's, never clipped (the plan's 3.4). With the trim at +0.06 the
        lambda passes 1, under the B58's 1.25; a ceiling of 1, the lowest Engine
        accepts, holds it at 1."""
        rich = _rich(PLANT)
        floor32 = float(np.float32(ENG.ecu.lam_floor))
        self.assertEqual(set(_agent_lams(rich, None, 4)), {float(np.float32(1.0 - ENG.ecu.enr_depth))})
        base = _agent_lams(rich, -1.0, 8)
        on = [i for i, x in enumerate(base) if x == floor32]
        self.assertGreater(len(on), 0, "the floor never bound: the checks below could not fail")
        self.assertLess(len(on), len(base), "no step was off the floor to show it stays put")
        step = _f32_up(ENG.ecu.lam_floor)
        moved = _agent_lams(_with_ecu(rich, lam_floor=step), -1.0, 8)
        self.assertEqual([i for i, (a, b) in enumerate(zip(base, moved)) if a != b], on)
        self.assertEqual({moved[i] for i in on}, {step})
        self.assertEqual(_agent_lams(_with_ecu(rich, lam_floor=_up(ENG.ecu.lam_floor)), -1.0, 8), base)
        lean = _agent_lams(PLANT, 1.0, 4)
        self.assertTrue(all(1.0 < x < ENG.ecu.lam_ceiling for x in lean), lean)
        self.assertEqual(_agent_lams(_with_ecu(PLANT, lam_ceiling=1.0), 1.0, 4), [1.0] * 4)
        print(f"\n  floor {ENG.ecu.lam_floor!r}, float32 {floor32!r}: the lambda sat on it at steps {on} of "
              f"{len(base)}; one float32 step moved those to {step!r}, one float64 ulp moved none")


# ------------------------------------------------------------ forms B and C
# The certificate harness's units grid (its `units` job, results/B58_IDENTITY.md):
# run_cycle at six speeds, five loads, five sparks, four lambdas and two charge
# temperatures, every CycleResult field; predict at lambda 0.95, with and without
# a backpressure, every output.
UNITS_CYCLE = [dict(rpm=rpm, map_kpa=mp, iat_k=iat, ect_k=365.0, spark_btdc=sp, lam=lam,
                    p_exh_kpa=max(105.0, mp * 1.15))
               for rpm in (900.0, 1500.0, 2706.0, 3800.0, 5200.0, 6500.0)
               for mp in (25.0, 60.0, 100.0, 175.0, 249.8)
               for sp in (-10.0, 0.0, 8.0, 20.0, 40.0)
               for lam in (0.70, 0.85, 1.0, 1.12)
               for iat in (300.0, 330.0)]
UNITS_PREDICT = [(rpm, mp, p_exh) for rpm in (1200.0, 2706.0, 4800.0) for mp in (40.0, 120.0, 210.0)
                 for p_exh in (None, 150.0)]
RESULT_FIELDS = ("torque_nm", "power_kw", "bmep_bar", "imep_bar", "fmep_bar", "bsfc_gpkwh", "egt_c",
                 "p_max_bar", "knock_integral", "knock_prob", "mfb50_deg", "mdot_fuel_gps", "t_max_k",
                 "mdot_air_gps", "eta_v", "f_res")
# Every row of the grid; and its rows at one spark and one charge temperature,
# every speed, load and lambda, for the steps off neutral, compared row by row.
ALL = list(range(len(UNITS_CYCLE)))
SUB = [i for i, kw in enumerate(UNITS_CYCLE) if kw["spark_btdc"] == 8.0 and kw["iat_k"] == 330.0]


def _units(engine, rows):
    """run_cycle at these rows of the units grid (ALL, SUB), one result row each, at
    the cam the engine's ECU schedules at each row's speed and MAP: None, no cam
    input, unless its form has D (P4). The harness's units job builds its grid the
    same way (amendment B2: cam_deg=BaselineECU(eng.ecu).cam_deg(rpm, map))."""
    ops = [UNITS_CYCLE[i] for i in rows]
    cam = E.BaselineECU(engine.ecu).cam_deg
    results = [P.run_cycle(P.Operating(**kw), engine=engine, cam_deg=cam(kw["rpm"], kw["map_kpa"]))
               for kw in ops]
    return np.array([[getattr(r, f) for f in RESULT_FIELDS] for r in results])


def _predicts(engine):
    out = []
    cam = E.BaselineECU(engine.ecu).cam_deg
    for rpm, mp, p_exh in UNITS_PREDICT:
        d = P.predict(rpm, mp, 330.0, 363.0, 12.0, 0.95, p_exh_kpa=p_exh, cam_deg=cam(rpm, mp), engine=engine)
        out.append([d[k] for k in sorted(d)])
    return np.array(out)


_FORM_A = {}


def _form_a():
    """Form A's -- the B58's -- units grid, predicts and extremes episode, computed
    once per run and shared by FormsBC and FormD: (cycles, predicts, (episode, lams))."""
    if not _FORM_A:
        _FORM_A["v"] = (_units(ENG, ALL), _predicts(ENG), _episode(PLANT))
    return _FORM_A["v"]


def _form(engine, **cycle):
    """`engine` with its cycle record's form and terms set in ONE replace, as the
    harness's HARNESS_SET sets them (amendment B2): CycleCal refuses a term its
    form does not have, so a form and its terms cannot be set one at a time."""
    return replace(engine, cycle=replace(engine.cycle, **cycle))


def _moved_rows(a, b):
    """The rows of two result arrays that differ anywhere, bit for bit."""
    return [i for i in range(len(a)) if a[i].tobytes() != b[i].tobytes()]


def _episode(plant, duration=60.0):
    """One random-trim episode of the extremes roads: the harness's
    extremes:double:12:random cut to `duration` seconds (ExtremesTrainingEnv at
    dt 1 and seed 12, the double family, and the harness's random policy, uniform
    actions from default_rng(0) as float32). Its observations (the reset's
    first), rewards, the info's numbers per step and the episode summary, each one
    array, as the harness dumps them; and the agent's lambda per step."""
    env = E.ExtremesTrainingEnv(duration=duration, dt=1.0, seed=12, plant=plant)
    obs, _ = env.reset(seed=12, options={"family": "double"})
    rng = np.random.default_rng(0)
    out = dict(obs=[obs], reward=[], info=[])
    keys, lams = None, []
    while True:
        obs, r, term, trunc, info = env.step(rng.uniform(-1.0, 1.0, 5).astype(np.float32))
        keys = keys or sorted(k for k, v in info.items()
                              if isinstance(v, (int, float, np.floating, np.integer, bool)))
        out["obs"].append(obs)
        out["reward"].append(r)
        out["info"].append([float(info[k]) for k in keys])
        lams.append(info["lam"])
        if term or trunc:
            out["summary"] = [float(v) for _, v in sorted(info["episode_summary"].items())]
            return {k: np.asarray(v, dtype=np.float64) for k, v in out.items()}, lams


def _keys_moved(a, b):
    """The keys of two episodes (_episode) whose arrays differ, bit for bit."""
    return [k for k in a if a[k].tobytes() != b[k].tobytes()]


class FormsBC(unittest.TestCase):
    """P3 (22 October 2026): the cycle record carries the contract's model form,
    and forms B and C add their terms -- ve_map in plant.volumetric_efficiency, the
    rich slope in plant.combustion_efficiency -- behind a branch form A never takes."""

    @classmethod
    def setUpClass(cls):
        cls.cycles, cls.predicts, _ = _form_a()

    def test_the_b58_is_form_a(self):
        """Form A, ve_map 0.0, ve_map_ref_kpa 100.0 (DESIGN) and ce_rich_slope 0.65
        (ASSUMED, the literal of combustion_efficiency on cf43fbb), typed in the
        spec, a str and Python floats (amendment B10); the shared slope is that
        double; typed_engine builds the same record."""
        c = ENG.cycle
        self.assertEqual((c.form, c.ve_map.hex(), c.ve_map_ref_kpa.hex(), c.ce_rich_slope.hex()),
                         ("A", (0.0).hex(), (100.0).hex(), (0.65).hex()))
        self.assertEqual([type(getattr(c, k)) for k in ("form", "ve_map", "ve_map_ref_kpa", "ce_rich_slope")],
                         [str, float, float, float])
        self.assertEqual(engines.SHARED_RICH_SLOPE.hex(), (0.65).hex())
        with open(os.path.join(HERE, "engine_specs", "b58.toml"), "rb") as fh:
            raw = tomllib.load(fh)["cycle"]
        self.assertEqual({k: (raw[k]["value"], raw[k]["label"])
                          for k in ("form", "ve_map", "ve_map_ref_kpa", "ce_rich_slope")},
                         {"form": ("A", "DESIGN"), "ve_map": (0.0, "DESIGN"), "ve_map_ref_kpa": (100.0, "DESIGN"),
                          "ce_rich_slope": (0.65, "ASSUMED")})
        self.assertEqual(engines.typed_engine("b58").cycle, c)

    def test_cyclecal_refuses_a_term_its_form_does_not_have(self):
        """An unknown form (A+B+D among them: each form adds to the one before), a
        ve_map without B (one ulp above zero is enough), a slope other than 0.65
        without C (one ulp), each a ValueError; a NumPy scalar or an int, a
        TypeError (amendment B10); a NaN or an infinity in any of the three floats,
        a ValueError, under a form that reads it. The controls: each term under its
        own form builds, a reference other than 100 kPa among them. A+B+C+D, known
        since P4, needs its ECU's cam: FormD."""
        for bad in (dict(form="B"), dict(form="A+C"), dict(form="A+B+D"), dict(form="a"), dict(form=""),
                    dict(ve_map=1e-4), dict(ve_map=5e-324), dict(ve_map=-1e-4),
                    dict(ce_rich_slope=_up(0.65)), dict(form="A+B", ce_rich_slope=_up(0.65)),
                    dict(form="A+B", ce_rich_slope=0.70)):
            with self.subTest(**bad):
                with self.assertRaises(ValueError):
                    _form(ENG, **bad)
        for bad in (dict(form=np.str_("A")), dict(ve_map=np.float64(0.0)), dict(ve_map=0),
                    dict(ve_map_ref_kpa=np.float32(100.0)), dict(ce_rich_slope=np.float64(0.65))):
            with self.subTest(**{k: repr(v) for k, v in bad.items()}):
                with self.assertRaises(TypeError):
                    _form(ENG, **bad)
        # Not finite (the review of P3): each under a form that reads the term, so
        # that only the finiteness check can refuse it; != lets a NaN through.
        for bad in (dict(form="A+B", ve_map=float("nan")), dict(form="A+B", ve_map=float("inf")),
                    dict(form="A+B", ve_map=1e-4, ve_map_ref_kpa=float("nan")),
                    dict(ve_map_ref_kpa=float("-inf")),
                    dict(form="A+B+C", ce_rich_slope=float("nan")),
                    dict(form="A+B+C", ce_rich_slope=float("inf"))):
            with self.subTest(**{k: repr(v) for k, v in bad.items()}):
                with self.assertRaisesRegex(ValueError, "must be finite"):
                    _form(ENG, **bad)
        for good in (dict(form="A+B", ve_map=1e-4), dict(form="A+B+C", ve_map=1e-4, ce_rich_slope=0.70),
                     dict(form="A+B+C", ce_rich_slope=_up(0.65)), dict(form="A+B+C"),
                     dict(form="A+B", ve_map=1e-4, ve_map_ref_kpa=101.0)):
            with self.subTest(**good):
                c = _form(ENG, **good).cycle
                self.assertEqual({k: getattr(c, k) for k in good}, good)
        self.assertEqual(ENG.cycle.form, "A", "the plant other callers hold is untouched")

    def test_the_spec_must_type_the_form_and_its_terms(self):
        """No default form (mistake 1): a spec without one of the four does not
        build, nor one typing a ve_map under form A. Each refusal is the rule's
        own, by its message (the review of P3, 22 October 2026: any ValueError
        passed, so a refusal for an unrelated reason would have too; mistake 12):
        _record's "is missing" for a field left out, CycleCal's "has no MAP term"
        for the ve_map. The control: the spec as it is builds the plant
        engines.get holds."""
        real = engines.read_spec

        def spec_with(change):
            def read(name):
                s = real(name)
                if name == "b58":
                    change(s)
                return s
            return read
        self.assertEqual(engines._build("b58", "a90_supra"), PLANT)
        for what, change, message in [(f"no {k}", lambda s, k=k: s["cycle"].pop(k), rf"\[cycle\] {k} is missing")
                                      for k in ("form", "ve_map", "ve_map_ref_kpa", "ce_rich_slope")] + [
                ("ve_map 1e-4 under A", lambda s: s["cycle"].update(ve_map=1e-4),
                 r"cycle form 'A' has no MAP term \(form B\), and ve_map is 0\.0001")]:
            with self.subTest(what):
                with mock.patch.object(engines, "read_spec", side_effect=spec_with(change)):
                    with self.assertRaisesRegex(ValueError, message):
                        engines._build("b58", "a90_supra")

    def test_forms_at_neutral_values_give_form_as_doubles(self):
        """A+B at ve_map 0.0, and A+B+C at the shared slope 0.65, give form A's
        doubles, by tobytes(), over the units grid's 1200 cycles and 18 predicts:
        form B's sum adds an exact 0.0 at a finite MAP, and C's slope is the same
        double (the plan's section 3.2). The control is
        test_steps_off_neutral_come_out_different."""
        for form, terms in (("A+B", dict(ve_map=0.0)), ("A+B+C", dict(ve_map=0.0, ce_rich_slope=0.65))):
            with self.subTest(form=form):
                e = _form(ENG, form=form, **terms)
                self.assertEqual(_units(e, ALL).tobytes(), self.cycles.tobytes())
                self.assertEqual(_predicts(e).tobytes(), self.predicts.tobytes())
        print(f"\n  forms A+B and A+B+C at neutral values: {self.cycles.size} cycle values and "
              f"{self.predicts.size} predict values, form A's bit for bit")

    def test_forms_at_neutral_values_give_form_as_episode(self):
        """The plan's "and on one episode" (PLAN.md, WP1 tests; the review of P3,
        22 October 2026): A+B at ve_map 0.0 and A+B+C at 0.65 give form A's
        observations, rewards, info and episode summary, by tobytes(), over a
        60 s random-trim extremes episode (_episode). It must run rich, or the C
        half could not fail: the B58's neutral terrain episode never does, and
        reads the same at a slope of 0.70 (the review's control rvw_P3_C070).
        Kept here as well as in the certificate harness's HARNESS_SET controls
        (amendment B2): the harness lives outside the repository, and P4 edits
        step(). The controls: a slope of 0.70 under A+B+C and a ve_map of 1e-4
        under A+B each move all four. FormD extends it to A+B+C+D (P4)."""
        base, lams = _form_a()[2]
        n_rich = sum(1 for x in lams if x < 1.0)
        self.assertGreater(n_rich, 0, "the episode never ran rich: form C's half could not fail")
        for form, terms in (("A+B", dict(ve_map=0.0)), ("A+B+C", dict(ve_map=0.0, ce_rich_slope=0.65))):
            with self.subTest(form=form):
                got, _ = _episode(replace(PLANT, engine=_form(ENG, form=form, **terms)))
                self.assertEqual(_keys_moved(base, got), [])
        for form, terms in (("A+B+C", dict(ce_rich_slope=0.70)), ("A+B", dict(ve_map=1e-4))):
            with self.subTest(control=form, **terms):
                got, _ = _episode(replace(PLANT, engine=_form(ENG, form=form, **terms)))
                self.assertEqual(_keys_moved(base, got), list(base))
        print(f"\n  forms A+B and A+B+C at neutral values over {len(lams)} steps of an extremes episode "
              f"({n_rich} of them rich): form A's obs, rewards, info and summary bit for bit; a slope "
              f"of 0.70 and a ve_map of 1e-4 move all four")

    def test_steps_off_neutral_come_out_different(self):
        """Mistake 25: each term must reach the outputs, and only where it should.
        ve_map 1e-4 under A+B moves every row of the units grid's speeds, loads and
        lambdas (at one spark and charge temperature) whose MAP is not
        ve_map_ref_kpa, and none at 100 kPa, where the term is exactly 0. A slope
        of 0.70 under A+B+C moves every rich row, and no row at lambda 1 or above,
        which the lean branch computes. One ulp above 0.65 moves predict at lambda
        0.95, the harness's control (amendment B2), and nothing on the grid: one
        ulp is lost in rounding 1 - slope (1 - lambda) at 0.70, 0.85 and float32
        of 0.81, and seen at 0.95."""
        base = self.cycles[SUB]
        ops = [UNITS_CYCLE[i] for i in SUB]
        ve = _units(_form(ENG, form="A+B", ve_map=1e-4), SUB)
        self.assertEqual(_moved_rows(base, ve), [i for i, kw in enumerate(ops) if kw["map_kpa"] != 100.0])
        k = RESULT_FIELDS.index("eta_v")
        self.assertTrue(all(ve[i, k] != base[i, k] for i, kw in enumerate(ops) if kw["map_kpa"] != 100.0))
        slope = _units(_form(ENG, form="A+B+C", ce_rich_slope=0.70), SUB)
        self.assertEqual(_moved_rows(base, slope), [i for i, kw in enumerate(ops) if kw["lam"] < 1.0])
        ulp = _form(ENG, form="A+B+C", ce_rich_slope=_up(0.65))
        n_predict = len(_moved_rows(self.predicts, _predicts(ulp)))
        self.assertGreater(n_predict, 0)
        self.assertEqual(_moved_rows(base, _units(ulp, SUB)), [])
        seen = {lam: P.combustion_efficiency(lam, engine=ulp) != P.combustion_efficiency(lam, engine=ENG)
                for lam in (0.70, 0.85, float(np.float32(0.81)), 0.95)}
        self.assertEqual(seen, {0.70: False, 0.85: False, float(np.float32(0.81)): False, 0.95: True})
        print(f"\n  ve_map 1e-4: {len(_moved_rows(base, ve))} of {len(SUB)} rows moved (none at 100 kPa); "
              f"slope 0.70: {len(_moved_rows(base, slope))} (the rich ones); slope + 1 ulp: "
              f"{n_predict} of {len(UNITS_PREDICT)} predicts at lambda 0.95, no grid row")

    def test_form_bs_breathing_is_its_expression(self):
        """Form B's eta_v to the bit, out of run_cycle (the review of P3, 22 October
        2026: "some rows moved" let a flipped sign, a scaled term, a literal 100 kPa
        reference and a term added after the clip all pass). (1) ve_map 1e-4 at
        2706 rpm and 175 kPa, unclipped, is clip(curve + 1e-4 (175 - 100)), the sum
        in the plan's order. (2) ve_map_ref_kpa 101 moves every row of the grid,
        those at 100 kPa among them, which the reference 100 leaves alone; at 2706
        rpm and 100 kPa it gives clip(curve + 1e-4 (100 - 101)): the reference is
        read. (3) ve_map 1e-3 at 3800 rpm and 249.8 kPa, where the curve is 1.0,
        under ve_hi, and the sum 1.1498, over it, gives exactly ve_hi: the clip
        comes after the term."""
        c = ENG.cycle

        def curve(rpm):
            return c.ve_base + c.ve_amp * np.exp(-((rpm - c.ve_rpm) / c.ve_width) ** 2)

        def expected(rpm, mp, ve_map, ref):
            return float(np.clip(curve(rpm) + ve_map * (mp - ref), c.ve_lo, c.ve_hi))

        def eta_v(engine, rpm, mp):
            kw = next(kw for kw in UNITS_CYCLE if (kw["rpm"], kw["map_kpa"]) == (rpm, mp))
            return P.run_cycle(P.Operating(**kw), engine=engine).eta_v
        ref100 = _form(ENG, form="A+B", ve_map=1e-4)
        got = eta_v(ref100, 2706.0, 175.0)
        self.assertEqual(got.hex(), expected(2706.0, 175.0, 1e-4, 100.0).hex())
        self.assertTrue(c.ve_lo < got < c.ve_hi and got != eta_v(ENG, 2706.0, 175.0), got)
        ref101 = _form(ENG, form="A+B", ve_map=1e-4, ve_map_ref_kpa=101.0)
        self.assertEqual(_moved_rows(self.cycles[SUB], _units(ref101, SUB)), list(range(len(SUB))))
        self.assertEqual(eta_v(ref100, 2706.0, 100.0).hex(), eta_v(ENG, 2706.0, 100.0).hex())
        at_100 = eta_v(ref101, 2706.0, 100.0)
        self.assertEqual(at_100.hex(), expected(2706.0, 100.0, 1e-4, 101.0).hex())
        self.assertNotEqual(at_100, eta_v(ENG, 2706.0, 100.0))
        self.assertTrue(curve(3800.0) < c.ve_hi < curve(3800.0) + 1e-3 * (249.8 - 100.0))
        clipped = eta_v(_form(ENG, form="A+B", ve_map=1e-3), 3800.0, 249.8)
        self.assertEqual(clipped.hex(), c.ve_hi.hex())
        print(f"\n  form B's eta_v: {got!r} at 2706 rpm and 175 kPa (form A {eta_v(ENG, 2706.0, 175.0)!r}); "
              f"{at_100!r} at 100 kPa about 101; {clipped!r} = ve_hi at 3800 rpm and 249.8 kPa "
              f"(the sum {float(curve(3800.0) + 1e-3 * (249.8 - 100.0))!r})")

    def test_form_a_reads_no_map(self):
        """Form A's breathing is cf43fbb's expression verbatim: the same double for
        any MAP, None and NaN included. Form B's sum at ve_map 0 is not that: a NaN
        MAP makes it NaN (0.0 * NaN), the reason form A keeps its own line (the
        plan's section 3.2); and B refuses None. (No cam under either: None, P4.)"""
        ab = _form(ENG, form="A+B")
        for rpm in (900.0, 2706.0, 6500.0):
            with self.subTest(rpm=rpm):
                a = P.volumetric_efficiency(rpm, 100.0, None, engine=ENG)
                for mp in (None, float("nan"), 25.0, 249.8):
                    self.assertEqual(P.volumetric_efficiency(rpm, mp, None, engine=ENG).hex(), a.hex())
                self.assertEqual(P.volumetric_efficiency(rpm, 175.0, None, engine=ab).hex(), a.hex())
                self.assertTrue(np.isnan(P.volumetric_efficiency(rpm, float("nan"), None, engine=ab)))
                with self.assertRaises(ValueError):
                    P.volumetric_efficiency(rpm, None, None, engine=ab)

    def test_map_from_airflow_inverts_form_a_only(self):
        """Under form B the breathing reads the MAP the inversion solves for, so
        every form other than A is refused, even at neutral values, by the
        inversion itself (not only by the breathing's refusal of a None MAP,
        which a form without B would not reach). The control: form A inverts,
        through get's engine and typed_engine's alike."""
        for form in ("A+B", "A+B+C"):
            with self.subTest(form=form):
                with self.assertRaisesRegex(ValueError, "inverts form A only"):
                    P.map_from_airflow(80.0, 2706.0, 315.0, engine=_form(ENG, form=form))
        a = P.map_from_airflow(80.0, 2706.0, 315.0, engine=ENG)
        self.assertTrue(np.isfinite(a))
        self.assertEqual(P.map_from_airflow(80.0, 2706.0, 315.0, engine=engines.typed_engine("b58")), a)


# --------------------------------------------------------------------- form D
P4_CYCLE = ("ve_cam", "cam_ref_deg")
# Form D's cycle record at neutral values: B's and C's terms neutral, no cam term.
D_NEUTRAL = dict(form="A+B+C+D", ve_map=0.0, ce_rich_slope=0.65, ve_cam=0.0, cam_ref_deg=0.0)
# Amendment B2's schedule for the certificate's DIFFERENT control: cam_c0 10 and
# every other coefficient 0, so a cam of 10 crank degrees everywhere, on the
# domain 800-7000 rpm x 20-260 kPa, clamped to -60..60.
B2_SCHEDULE = dict(cam_on=1, cam_c0=10.0, cam_rpm_lo=800.0, cam_rpm_hi=7000.0, cam_map_lo=20.0,
                   cam_map_hi=260.0, cam_lo=-60.0, cam_hi=60.0)
# Every coefficient in use, a clamp the quadratic passes at both ends of the
# domain: a probe of the expression, no engine's.
FULL_SCHEDULE = dict(cam_on=1, cam_c0=-30.0, cam_c_rpm=12.5, cam_c_map=-8.25, cam_c_rpm2=-0.75,
                     cam_c_rpm_map=1.5, cam_c_map2=2.0, cam_rpm_lo=1000.0, cam_rpm_hi=6000.0,
                     cam_map_lo=30.0, cam_map_hi=250.0, cam_lo=-20.0, cam_hi=20.0)
# A cam that moves with speed and load (1 deg per 1000 rpm, 10 per 100 kPa), so
# that the load it is scheduled on can be told apart.
LOAD_SCHEDULE = dict(cam_on=1, cam_c_rpm=1.0, cam_c_map=10.0, cam_rpm_hi=10000.0, cam_map_hi=400.0,
                     cam_lo=-60.0, cam_hi=60.0)


def _form_d(engine, ecu, **cycle):
    """`engine` at form A+B+C+D (D_NEUTRAL, with `cycle`'s changes) and these cam
    fields of its ECU record, set in ONE Engine replace, as the harness's
    HARNESS_SET sets them (amendment B2): Engine refuses a form with D whose ECU
    runs no cam, and the reverse, so neither can be set alone."""
    return replace(engine, cycle=replace(engine.cycle, **dict(D_NEUTRAL, **cycle)),
                   ecu=replace(engine.ecu, **ecu))


def _expected_cam(cal, rpm, mp):
    """The cam an ECU record's schedule gives at (rpm, mp), written out here: the
    inputs clamped to the domain, the quadratic in rpm/1000 and MAP/100 summed in
    BaselineECU.cam_deg's order, the output clamped."""
    x = min(max(rpm, cal.cam_rpm_lo), cal.cam_rpm_hi) / 1000.0
    y = min(max(mp, cal.cam_map_lo), cal.cam_map_hi) / 100.0
    q = (cal.cam_c0 + cal.cam_c_rpm * x + cal.cam_c_map * y
         + cal.cam_c_rpm2 * x * x + cal.cam_c_rpm_map * x * y + cal.cam_c_map2 * y * y)
    return min(max(q, cal.cam_lo), cal.cam_hi)


def _step_calls(plant, n):
    """n neutral steps of the plant's locked climb, with _track_torque and _evaluate
    wrapped as the learning lab's CapturingEnv and thresholds/b58_propagation.py
    wrap them, (*args, **kwargs). Per step: the load loops' calls as (positional
    count, keywords, whose loop: the state dict args[7] is the baseline's or the
    agent's), the evaluations' as (positional count, keywords), and the ECU's cam
    on the lagged load its step saw (map_b_prev before the step) and on the agent's
    own MAP after it."""
    env = E.SupervisoryTunerEnv(E.locked_climb(plant, duration=30.0, dt=1.0), plant=plant, dt=1.0, seed=0)
    env.reset(seed=0)
    ecu = E.BaselineECU(plant.engine.ecu)
    orig_tt, orig_ev = E.SupervisoryTunerEnv._track_torque, E.SupervisoryTunerEnv._evaluate
    loops, evals, cams = [], [], []

    def tt(self, *args, **kwargs):
        whose = "base" if args[7] is self.pi_base else ("agent" if args[7] is self.pi_agent else "?")
        loops[-1].append((len(args), dict(kwargs), whose))
        return orig_tt(self, *args, **kwargs)

    def ev(self, *a, **k):
        evals[-1].append((len(a), dict(k)))
        return orig_ev(self, *a, **k)
    with mock.patch.object(E.SupervisoryTunerEnv, "_track_torque", tt), \
            mock.patch.object(E.SupervisoryTunerEnv, "_evaluate", ev):
        for _ in range(n):
            loops.append([])
            evals.append([])
            lagged = env.map_b_prev
            env.step(E.neutral_action())
            cams.append((ecu.cam_deg(env.rpm, lagged), ecu.cam_deg(env.rpm, env.map_kpa)))
    return loops, evals, cams


# Source text other files pin on lines P4 edits (amendment B12): (file, text, how
# often it appears). The learning lab anchors two explanations on engine_env.py's
# step() (content.json, content.ar.json and the test that reads them), make_page.py's
# glossary pins _evaluate's return line, and the lab's CapturingEnv tells the
# baseline's load loop by its eighth positional argument.
SOURCE_PINS = (
    ("engine_env.py", "base, map_b = self._track_torque", 1),
    ("engine_env.py", "self.spark =", 1),
    ("engine_env.py", "ki=r.knock_integral, unc=0.0)", 1),
    ("make_page.py", '"ki=r.knock_integral, unc=0.0)",', 1),
    ("Explanatory Simulation/content.json", '"match": "base, map_b = self._track_torque"', 1),
    ("Explanatory Simulation/content.json", '"match": "self.spark ="', 1),
    ("Explanatory Simulation/content.ar.json", '"match": "base, map_b = self._track_torque"', 1),
    ("Explanatory Simulation/content.ar.json", '"match": "self.spark ="', 1),
    ("Explanatory Simulation/src/model/command-explanations.test.mjs", "'base, map_b = self._track_torque'", 1),
    ("Explanatory Simulation/src/model/command-explanations.test.mjs", "'self.spark ='", 1),
    ("Explanatory Simulation/backend/simulation.py", "args[7] is self.pi_base", 1),
)


def pin_problems(pins, read):
    """Every pin whose text is not in its file as often as it says."""
    out = []
    for path, text, count in pins:
        n = read(path).count(text)
        if n != count:
            out.append(f"{path}: {text!r} appears {n} times, not {count}")
    return out


class FormD(unittest.TestCase):
    """P4 (22 October 2026; decision 41): form D's intake cam, run by the ECU -- the
    cycle record's ve_cam and cam_ref_deg, the ECU record's cam_on and schedule,
    BaselineECU.cam_deg, the breathing's term, and step()'s hand-over of the cam."""

    @classmethod
    def setUpClass(cls):
        cls.cycles, cls.predicts, (cls.episode, _) = _form_a()

    def test_the_b58_runs_no_cam(self):
        """ve_cam and cam_ref_deg 0.0, cam_on the int 0 and the twelve schedule
        fields 0.0, typed DESIGN in the spec with those types (amendment B10: an
        int 0 typed for a float would be refused); the ECU's cam is None at every
        speed and load; typed_engine builds the same cycle record; A+B+C+D is a
        form now."""
        c, ecu = ENG.cycle, ENG.ecu
        self.assertEqual([(type(getattr(c, k)), getattr(c, k).hex()) for k in P4_CYCLE], [(float, "0x0.0p+0")] * 2)
        self.assertEqual((type(ecu.cam_on), ecu.cam_on), (int, 0))
        self.assertEqual([(type(getattr(ecu, k)), getattr(ecu, k).hex()) for k in engines.CAM_SCHEDULE],
                         [(float, "0x0.0p+0")] * 12)
        with open(os.path.join(HERE, "engine_specs", "b58.toml"), "rb") as fh:
            raw = tomllib.load(fh)
        typed = {k: raw["cycle"][k] for k in P4_CYCLE}
        typed.update({k: raw["ecu"][k] for k in ("cam_on",) + engines.CAM_SCHEDULE})
        self.assertEqual({k: (type(v["value"]), v["value"], v["label"]) for k, v in typed.items()},
                         dict({k: (float, 0.0, "DESIGN") for k in P4_CYCLE + engines.CAM_SCHEDULE},
                              cam_on=(int, 0, "DESIGN")))
        cam = E.BaselineECU(ecu).cam_deg
        self.assertEqual({cam(rpm, mp) for rpm in (0.0, 900.0, 2706.0, 6500.0, 9000.0)
                          for mp in (0.0, 25.0, 175.0, 400.0)}, {None})
        self.assertEqual(engines.typed_engine("b58").cycle, c)
        self.assertEqual(engines.CYCLE_FORMS, ("A", "A+B", "A+B+C", "A+B+C+D"))

    def test_the_records_refuse_a_cam_nothing_runs(self):
        """CycleCal: a ve_cam under a form without D (one ulp above zero is enough)
        a ValueError; a NumPy scalar or an int a TypeError; a NaN or an infinity a
        ValueError. EcuCal: a cam_on other than 0 or 1 a ValueError, a bool, a
        float or a NumPy int a TypeError; a schedule field that is a NumPy float or
        an int a TypeError, one not finite a ValueError; a domain or a clamp upside
        down (by one ulp) a ValueError; with the cam off, any one of the twelve
        away from 0.0 a ValueError. Engine: a form with D and the cam off, or the
        cam on and a form without D, a ValueError. The controls: A+B+C+D with the
        cam on builds, at zeros (a domain and a clamp of one point), at B2's
        schedule and at FULL_SCHEDULE with a reference of 5 deg, and the plant
        other callers hold is untouched."""
        for form in ("A", "A+B", "A+B+C"):
            for v in (1e-4, 5e-324, -1e-4):
                with self.subTest(form=form, ve_cam=v):
                    with self.assertRaisesRegex(ValueError, "no cam term"):
                        replace(ENG.cycle, form=form, ve_cam=v)
        for bad in (dict(ve_cam=np.float64(0.0)), dict(ve_cam=0), dict(cam_ref_deg=np.float32(0.0)),
                    dict(cam_ref_deg=0)):
            with self.subTest(**{k: repr(v) for k, v in bad.items()}):
                with self.assertRaises(TypeError):
                    replace(ENG.cycle, **bad)
        for bad in (dict(form="A+B+C+D", ve_cam=float("nan")), dict(form="A+B+C+D", ve_cam=float("inf")),
                    dict(cam_ref_deg=float("nan")), dict(cam_ref_deg=float("-inf"))):
            with self.subTest(**{k: repr(v) for k, v in bad.items()}):
                with self.assertRaisesRegex(ValueError, "must be finite"):
                    replace(ENG.cycle, **bad)
        for bad in (2, -1):
            with self.subTest(cam_on=bad):
                with self.assertRaisesRegex(ValueError, "0 or 1"):
                    replace(ENG.ecu, cam_on=bad)
        for bad in (True, False, 1.0, np.int64(1)):
            with self.subTest(cam_on=repr(bad)):
                with self.assertRaises(TypeError):
                    replace(ENG.ecu, cam_on=bad)
        for name in engines.CAM_SCHEDULE:
            with self.subTest(field=name):
                for bad in (np.float64(0.0), 0):
                    with self.assertRaises(TypeError):
                        replace(ENG.ecu, cam_on=1, **{name: bad})
                for bad in (float("nan"), float("inf"), float("-inf")):
                    with self.assertRaisesRegex(ValueError, "must be finite"):
                        replace(ENG.ecu, cam_on=1, **{name: bad})
                off = -1.0 if name.endswith("_lo") else (1.0 if name.endswith("_hi") else 5e-324)
                with self.assertRaisesRegex(ValueError, "runs no cam"):
                    replace(ENG.ecu, **{name: off})
        for lo, hi in (("cam_rpm_lo", "cam_rpm_hi"), ("cam_map_lo", "cam_map_hi"), ("cam_lo", "cam_hi")):
            with self.subTest(lo=lo, hi=hi):
                with self.assertRaisesRegex(ValueError, "is above"):
                    replace(ENG.ecu, cam_on=1, **{lo: 1.0, hi: float(np.nextafter(1.0, 0.0))})
        with self.assertRaisesRegex(ValueError, "exactly when the form"):
            replace(ENG, cycle=replace(ENG.cycle, **D_NEUTRAL))
        for form in ("A", "A+B", "A+B+C"):
            with self.subTest(form=form, cam_on=1):
                with self.assertRaisesRegex(ValueError, "exactly when the form"):
                    replace(ENG, cycle=replace(ENG.cycle, form=form), ecu=replace(ENG.ecu, cam_on=1))
        for ecu, cycle in ((dict(cam_on=1), {}), (dict(cam_on=1, cam_rpm_lo=900.0, cam_rpm_hi=900.0), {}),
                           (B2_SCHEDULE, dict(ve_cam=1e-4)), (FULL_SCHEDULE, dict(ve_cam=1e-4, cam_ref_deg=5.0))):
            with self.subTest(ecu=ecu, cycle=cycle):
                e = _form_d(ENG, ecu, **cycle)
                self.assertEqual({k: getattr(e.ecu, k) for k in ecu}, ecu)
                self.assertEqual({k: getattr(e.cycle, k) for k in cycle}, cycle)
        self.assertEqual((ENG.cycle.form, ENG.ecu.cam_on), ("A", 0), "the plant other callers hold is untouched")

    def test_the_spec_must_type_the_cam(self):
        """No default cam (mistake 1): a spec without one of the fifteen does not
        build, nor one typing a ve_cam or cam_on 1 under form A, a schedule with
        the cam off, or an int where a float belongs (TOML's `0` for `0.0`). The
        control: the spec as it is builds the plant engines.get holds."""
        real = engines.read_spec

        def spec_with(change):
            def read(name):
                s = real(name)
                if name == "b58":
                    change(s)
                return s
            return read
        self.assertEqual(engines._build("b58", "a90_supra"), PLANT)
        cases = ([(f"no {k}", ValueError, lambda s, k=k: s["cycle"].pop(k)) for k in P4_CYCLE]
                 + [(f"no {k}", ValueError, lambda s, k=k: s["ecu"].pop(k)) for k in ("cam_on",) + engines.CAM_SCHEDULE]
                 + [("ve_cam 1e-4 under A", ValueError, lambda s: s["cycle"].update(ve_cam=1e-4)),
                    ("cam_on 1 under A", ValueError, lambda s: s["ecu"].update(cam_on=1)),
                    ("cam_c0 10 with the cam off", ValueError, lambda s: s["ecu"].update(cam_c0=10.0)),
                    ("cam_on typed 0.0", TypeError, lambda s: s["ecu"].update(cam_on=0.0)),
                    ("cam_hi typed 0", TypeError, lambda s: s["ecu"].update(cam_hi=0)),
                    ("ve_cam typed 0", TypeError, lambda s: s["cycle"].update(ve_cam=0))])
        for what, error, change in cases:
            with self.subTest(what):
                with mock.patch.object(engines, "read_spec", side_effect=spec_with(change)):
                    with self.assertRaises(error):
                        engines._build("b58", "a90_supra")

    def test_the_schedule_is_its_expression(self):
        """BaselineECU.cam_deg on FULL_SCHEDULE, to the bit, at 49 points inside
        and outside the domain: the quadratic in rpm/1000 and MAP/100 in its
        order, a Python float. Outside the domain the cam is the edge's; inside it
        moves. The output clamp is reached at both ends (the quadratic passes it
        there) and holds the cam on it. Each coefficient reaches the cam."""
        cal = replace(ENG.ecu, **FULL_SCHEDULE)
        cam = E.BaselineECU(cal).cam_deg
        rpms = (500.0, 1000.0, 1500.0, 2706.0, 4000.0, 6000.0, 9000.0)
        maps = (10.0, 30.0, 60.0, 100.0, 175.0, 250.0, 400.0)
        got = {(r, m): cam(r, m) for r in rpms for m in maps}
        self.assertEqual({k: v.hex() for k, v in got.items()}, {k: _expected_cam(cal, *k).hex() for k in got})
        self.assertEqual({type(v) for v in got.values()}, {float})
        for m in maps:
            self.assertEqual((got[(500.0, m)], got[(9000.0, m)]), (got[(1000.0, m)], got[(6000.0, m)]))
        for r in rpms:
            self.assertEqual((got[(r, 10.0)], got[(r, 400.0)]), (got[(r, 30.0)], got[(r, 250.0)]))
        self.assertNotEqual(got[(1500.0, 100.0)], got[(1000.0, 100.0)])
        self.assertNotEqual(got[(4000.0, 60.0)], got[(4000.0, 100.0)])
        free = replace(cal, cam_lo=-1e9, cam_hi=1e9)
        raw = {k: _expected_cam(free, *k) for k in got}
        high = [k for k, q in raw.items() if q > cal.cam_hi]
        low = [k for k, q in raw.items() if q < cal.cam_lo]
        inside = [k for k, q in raw.items() if cal.cam_lo < q < cal.cam_hi]
        self.assertTrue(high and low and inside, (len(high), len(low), len(inside)))
        self.assertEqual({got[k] for k in high}, {cal.cam_hi})
        self.assertEqual({got[k] for k in low}, {cal.cam_lo})
        self.assertEqual([k for k in inside if got[k] != raw[k]], [])
        at = (4000.0, 100.0)
        for name in ("cam_c0", "cam_c_rpm", "cam_c_map", "cam_c_rpm2", "cam_c_rpm_map", "cam_c_map2"):
            with self.subTest(coefficient=name):
                moved = E.BaselineECU(replace(cal, **{name: getattr(cal, name) + 1.0})).cam_deg(*at)
                self.assertNotEqual(moved, got[at])
        print(f"\n  cam_deg on FULL_SCHEDULE: {len(got)} points to the bit; {len(high)} on cam_hi, "
              f"{len(low)} on cam_lo, {len(inside)} inside; at {at} {got[at]!r}")

    def test_the_breathing_takes_a_cam_exactly_under_d(self):
        """plant.volumetric_efficiency: a cam under a form without D is refused (0.0
        too), and None under D; under D at no cam term it is form A's double. The
        term to the bit: after B's, before the clip, its reference read, exactly 0
        at the reference. run_cycle and predict hand the cam to it, by keyword, and
        refuse a D engine run without one; map_from_airflow refuses form D."""
        d = _form_d(ENG, dict(cam_on=1))
        for e in (ENG, _form(ENG, form="A+B"), _form(ENG, form="A+B+C")):
            for cam in (0.0, 10.0):
                with self.subTest(form=e.cycle.form, cam=cam):
                    with self.assertRaisesRegex(ValueError, "no cam input"):
                        P.volumetric_efficiency(2706.0, 175.0, cam, engine=e)
        with self.assertRaisesRegex(ValueError, "cam_deg is None"):
            P.volumetric_efficiency(2706.0, 175.0, None, engine=d)
        a = P.volumetric_efficiency(2706.0, 175.0, None, engine=ENG)
        self.assertEqual(P.volumetric_efficiency(2706.0, 175.0, 0.0, engine=d).hex(), a.hex())
        c = ENG.cycle

        def curve(rpm):
            return c.ve_base + c.ve_amp * np.exp(-((rpm - c.ve_rpm) / c.ve_width) ** 2)

        def clip(v):
            return float(np.clip(v, c.ve_lo, c.ve_hi))
        e = _form_d(ENG, dict(cam_on=1), ve_map=1e-4, ve_cam=1e-4)
        got = P.volumetric_efficiency(2706.0, 175.0, 10.0, engine=e)
        self.assertEqual(got.hex(), clip(curve(2706.0) + 1e-4 * (175.0 - 100.0) + 1e-4 * (10.0 - 0.0)).hex())
        self.assertTrue(c.ve_lo < got < c.ve_hi, got)
        ref5 = _form_d(ENG, dict(cam_on=1), ve_map=1e-4, ve_cam=1e-4, cam_ref_deg=5.0)
        at5 = P.volumetric_efficiency(2706.0, 175.0, 10.0, engine=ref5)
        self.assertEqual(at5.hex(), clip(curve(2706.0) + 1e-4 * (175.0 - 100.0) + 1e-4 * (10.0 - 5.0)).hex())
        self.assertNotEqual(at5, got)
        b_only = P.volumetric_efficiency(2706.0, 175.0, None, engine=_form(ENG, form="A+B", ve_map=1e-4))
        self.assertEqual(P.volumetric_efficiency(2706.0, 175.0, 5.0, engine=ref5).hex(), b_only.hex())
        self.assertTrue(curve(3800.0) < c.ve_hi < curve(3800.0) + 1e-3 * 30.0)
        hi = _form_d(ENG, dict(cam_on=1), ve_cam=1e-3)
        self.assertEqual(P.volumetric_efficiency(3800.0, 100.0, 30.0, engine=hi).hex(), c.ve_hi.hex())
        pe = max(105.0, 175.0 * 1.15)
        op = P.Operating(rpm=2706.0, map_kpa=175.0, iat_k=330.0, ect_k=365.0, spark_btdc=8.0, lam=1.0, p_exh_kpa=pe)
        with self.assertRaisesRegex(ValueError, "cam_deg is None"):
            P.run_cycle(op, engine=e)
        r = P.run_cycle(op, engine=e, cam_deg=10.0)
        self.assertEqual(r.eta_v, got)
        with self.assertRaisesRegex(ValueError, "cam_deg is None"):
            P.predict(2706.0, 175.0, 330.0, 365.0, 8.0, 1.0, p_exh_kpa=pe, engine=e)
        self.assertEqual(P.predict(2706.0, 175.0, 330.0, 365.0, 8.0, 1.0, p_exh_kpa=pe, cam_deg=10.0,
                                   engine=e)["torque_nm"], r.torque_nm)
        with self.assertRaisesRegex(ValueError, "no cam input"):
            P.run_cycle(op, engine=ENG, cam_deg=0.0)
        rc = inspect.signature(P.run_cycle).parameters["cam_deg"]
        self.assertEqual((rc.kind, rc.default), (inspect.Parameter.KEYWORD_ONLY, None))
        self.assertIsNone(inspect.signature(P.predict).parameters["cam_deg"].default)
        with self.assertRaisesRegex(ValueError, "inverts form A only"):
            P.map_from_airflow(80.0, 2706.0, 315.0, engine=d)

    def test_form_d_at_neutral_values_gives_form_as_doubles(self):
        """A+B+C+D at zeros (the cam on, its schedule a point at 0 deg), and B2's
        schedule (a cam of 10 deg) at ve_cam 0, give form A's doubles over the
        units grid's 1200 cycles and 18 predicts, each run at its ECU's cam as the
        harness runs them (amendment B2's IDENTICAL controls). The control, B2's
        DIFFERENT one: the same schedule at ve_cam 1e-4 moves every row of the
        grid's speeds, loads and lambdas and every predict, eta_v at each, and the
        cam there is 10 deg, not the reference's 0 (amendment B2's own pre-check:
        a schedule of zeros could not fail)."""
        for what, e in (("A+B+C+D at zeros", _form_d(ENG, dict(cam_on=1))),
                        ("B2's schedule, ve_cam 0", _form_d(ENG, B2_SCHEDULE))):
            with self.subTest(what):
                self.assertEqual(_units(e, ALL).tobytes(), self.cycles.tobytes())
                self.assertEqual(_predicts(e).tobytes(), self.predicts.tobytes())
        on = _form_d(ENG, B2_SCHEDULE, ve_cam=1e-4)
        cam = E.BaselineECU(on.ecu).cam_deg
        self.assertEqual({cam(kw["rpm"], kw["map_kpa"]) for kw in UNITS_CYCLE}, {10.0})
        base, moved = self.cycles[SUB], _units(on, SUB)
        self.assertEqual(_moved_rows(base, moved), list(range(len(SUB))))
        k = RESULT_FIELDS.index("eta_v")
        self.assertTrue(all(moved[i, k] != base[i, k] for i in range(len(SUB))))
        n_predict = len(_moved_rows(self.predicts, _predicts(on)))
        self.assertEqual(n_predict, len(UNITS_PREDICT))
        print(f"\n  A+B+C+D at zeros and B2's schedule at ve_cam 0: {self.cycles.size} cycle values and "
              f"{self.predicts.size} predict values, form A's bit for bit; ve_cam 1e-4 at a cam of 10 deg: "
              f"{len(_moved_rows(base, moved))} of {len(SUB)} rows and {n_predict} of {len(UNITS_PREDICT)} "
              "predicts moved")

    def test_form_d_at_neutral_values_gives_form_as_episode(self):
        """The same two IDENTICAL controls over the 60 s random-trim extremes
        episode (_episode): form A's observations, rewards, info and summary, by
        tobytes(). The control: B2's schedule at ve_cam 1e-4 moves all four."""
        base = self.episode
        for what, e in (("A+B+C+D at zeros", _form_d(ENG, dict(cam_on=1))),
                        ("B2's schedule, ve_cam 0", _form_d(ENG, B2_SCHEDULE))):
            with self.subTest(what):
                got, _ = _episode(replace(PLANT, engine=e))
                self.assertEqual(_keys_moved(base, got), [])
        got, _ = _episode(replace(PLANT, engine=_form_d(ENG, B2_SCHEDULE, ve_cam=1e-4)))
        self.assertEqual(_keys_moved(base, got), list(base))

    def test_step_hands_the_ecus_cam_to_both_loops(self):
        """Every step calls the baseline's load loop, then the agent's, each with
        eight positional arguments -- the eighth its own state, which the learning
        lab's CapturingEnv reads -- and the cam by keyword alone; each loop's three
        evaluations take six positional arguments and the same keyword
        (b58_propagation's `ev(self, *a, **k)` passes it through). The cam is the
        ECU's on the lagged load its step saw, map_b_prev before the step, for the
        agent's loop too: the agent inherits the cam as it inherits the spark. On
        the B58 it is None, passed. The control: on LOAD_SCHEDULE the cam at the
        agent's own MAP differs from it at some step, so the check tells the
        loads apart."""
        d = replace(PLANT, engine=_form_d(ENG, LOAD_SCHEDULE, ve_cam=1e-4))
        for name, plant in (("b58", PLANT), ("form D", d)):
            with self.subTest(name):
                loops, evals, cams = _step_calls(plant, 12)
                for calls, ev, (lagged, _) in zip(loops, evals, cams):
                    self.assertEqual(calls, [(8, {"cam_deg": lagged}, "base"), (8, {"cam_deg": lagged}, "agent")])
                    self.assertEqual(ev, [(6, {"cam_deg": lagged})] * 6)
        _, _, cams = _step_calls(PLANT, 3)
        self.assertEqual({c for pair in cams for c in pair}, {None})
        _, _, cams = _step_calls(d, 12)
        self.assertTrue(all(isinstance(lagged, float) for lagged, _ in cams))
        apart = [i for i, (lagged, own) in enumerate(cams) if lagged != own]
        self.assertGreater(len(apart), 0, "the lagged load and the agent's never differed: the check could not fail")
        print(f"\n  step(): both loops at the ECU's cam on the lagged load, by keyword; on LOAD_SCHEDULE "
              f"{cams[0][0]!r} .. {cams[-1][0]!r} deg, apart from the agent's own MAP's at {len(apart)} of 12 steps")

    def test_the_deliverable_table_runs_at_the_ecus_cam(self):
        """measure_deliverable_torque hands each load-loop call the ECU's cam on the
        lagged load its step was given (150 kPa first, then the loop's last
        pressure), by keyword: on LOAD_SCHEDULE a cam that moves with the load,
        call by call; on the B58 None, passed."""
        d = replace(PLANT, engine=_form_d(ENG, LOAD_SCHEDULE, ve_cam=1e-4))
        orig = E.SupervisoryTunerEnv._track_torque
        for name, plant in (("b58", PLANT), ("form D", d)):
            with self.subTest(name):
                calls = []

                def tt(self, *args, **kwargs):
                    out, mp = orig(self, *args, **kwargs)
                    calls.append((args[1], kwargs.get("cam_deg", "absent"), mp))
                    return out, mp
                with mock.patch.object(E.SupervisoryTunerEnv, "_track_torque", tt):
                    E.measure_deliverable_torque([1600, 4400], plant=plant)
                settle = plant.car.table_settle
                self.assertEqual(len(calls), 2 * settle)
                cam = E.BaselineECU(plant.engine.ecu).cam_deg
                want = [cam(rpm, 150.0 if j % settle == 0 else calls[j - 1][2]) for j, (rpm, _, _) in enumerate(calls)]
                self.assertEqual([c for _, c, _ in calls], want)
                if plant is PLANT:
                    self.assertEqual(set(want), {None})
                else:
                    self.assertGreater(len(set(want)), 2, "the cam never moved with the load: the check could not fail")

    def test_a_surrogate_takes_no_cam(self):
        """_evaluate with a surrogate engine_model: without a cam, or with None, it
        calls the surrogate; with a cam it is refused (the surrogate's predict takes
        none). The controls: the cycle model takes the cam under D, and the B58's
        breathing refuses one."""
        class Stub:
            def predict(self, *a):
                return dict(torque=1.0, mdot_fuel=1.0, mdot_air=1.0, egt_k=900.0, ki=0.0, unc=0.0)
        args = (2706.0, 175.0, 330.0, 363.0, 8.0, 1.0)
        env = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0,
                                    engine_model=Stub())
        self.assertEqual(env._evaluate(*args)["torque"], 1.0)
        self.assertEqual(env._evaluate(*args, cam_deg=None)["torque"], 1.0)
        with self.assertRaisesRegex(ValueError, "surrogate"):
            env._evaluate(*args, cam_deg=10.0)
        d = replace(PLANT, engine=_form_d(ENG, B2_SCHEDULE, ve_cam=1e-4))
        out = E.SupervisoryTunerEnv(E.locked_climb(d, duration=60.0, dt=1.0), plant=d, dt=1.0)._evaluate(
            *args, cam_deg=10.0)
        self.assertTrue(np.isfinite(out["torque"]))
        b58 = E.SupervisoryTunerEnv(E.locked_climb(PLANT, duration=60.0, dt=1.0), plant=PLANT, dt=1.0)
        with self.assertRaisesRegex(ValueError, "no cam input"):
            b58._evaluate(*args, cam_deg=10.0)

    def test_the_source_pins_survive(self):
        """Amendment B12: the text other files pin on the lines P4 edits is still
        there, as often as it was. The control: the call P4 replaced,
        `self._evaluate(rpm, mp, iat_k, ect_k, spark, lam)` closed there, is gone,
        and a pin on it is reported."""
        self.assertEqual(pin_problems(SOURCE_PINS, _read), [])
        gone = (("engine_env.py", "out = self._evaluate(rpm, mp, iat_k, ect_k, spark, lam)\n", 1),)
        self.assertEqual(len(pin_problems(gone, _read)), 1)


# ------------------------------------------------------------------ engine_sha
# Build step 1's B58, the plant certified against cf43fbb (results/B58_IDENTITY.md:
# engine_sha 99d2a9658b1258a7): the keys of asdict(engines.get("b58")) on HEAD
# c47907b, record by record, printed from that tree on 22 October 2026.
BUILD_STEP_1_SHA = "99d2a9658b1258a7"
BUILD_STEP_1_KEYS = {
    "": "car engine scenario",
    "car": "cd_a crr deliverable_torque driveline_eff final_drive gears id mass peak_torque_nm rpm_max "
           "rpm_min shift_load shift_rpm_max table_rpm_hi table_rpm_lo table_rpm_step table_settle "
           "table_t_amb table_t_block upshift_min_rpm wheel_r",
    "engine": "boost charge cycle damage derived ecu geometry id loop thermal",
    "engine.boost": "envelope_flow envelope_pr inlet_sea_kpa pr_cap",
    "engine.charge": "block_coupling rise_k",
    "engine.cycle": "burn_base burn_res burn_rpm cp_exh delay_base delay_res delay_rpm exh_bp_min_kpa "
                    "exh_bp_ratio flame_floor flame_lam flame_width fmep_0 fmep_pmax fmep_sp fmep_sp2 fres_a "
                    "fres_b fres_hi fres_lo fres_map_min knock_a knock_b knock_on knock_p n_poly octane "
                    "port_pickup_k t_head_k t_residual_k ua_port ve_amp ve_base ve_hi ve_lo ve_rpm ve_width "
                    "wiebe_a wiebe_m",
    "engine.damage": "egt_limit_k ki_knee ki_weight oil_knee_k oil_scale_k oil_weight turb_knee_k "
                     "turb_scale_k",
    "engine.ecu": "cold_k cold_retard enr_depth enr_dwell_hi enr_dwell_lo enr_load enr_rpm_hi enr_rpm_lo "
                  "fan_hi_k fan_lo_duty fan_lo_k iat_gain iat_max iat_ref_c kl_a kl_b kl_c kl_d "
                  "knock_detect_ki knock_max knock_restore knock_step spark_a spark_b spark_c spark_max "
                  "spark_min spark_ref_kpa",
    "engine.geometry": "bore comp_ratio conrod evo_deg ivc_deg n_cyl stroke",
    "engine.loop": "ff_kpa_per_nm ff_offset_kpa i_clip i_gain i_out map_floor_kpa p_gain torque_floor_nm",
    "engine.thermal": "c_block c_oil c_turb frac_fuel_to_coolant frac_fuel_to_oil k_oil_rpm n_oil_rpm "
                      "n_turbines t_block_warm t_oil_warm t_stat_open t_stat_span t_turb_warm ua_block_amb "
                      "ua_block_oil ua_gas_turb ua_oil_amb ua_oil_ram ua_rad_fan ua_rad_min ua_rad_ram "
                      "ua_turb_amb",
    "scenario": "grade t_amb v_kmh",
}
# The keys build step 2 adds, stripped before the comparison, with the B58's
# typed value of each (amendment B11's list: P1's two, P2's two, P3's four, and
# P4's fifteen -- ve_cam, cam_ref_deg, cam_on and the twelve schedule fields).
ADDED = {
    "engine.fuel": {"lhv_j_per_kg": 44.0e6, "afr_st": 14.7},
    "engine.thermal.fuel_lhv_j_per_kg": 44.0e6,
    "engine.ecu.lam_floor": 0.70,
    "engine.ecu.lam_ceiling": 1.25,
    "engine.cycle.form": "A",
    "engine.cycle.ve_map": 0.0,
    "engine.cycle.ve_map_ref_kpa": 100.0,
    "engine.cycle.ce_rich_slope": 0.65,
    "engine.cycle.ve_cam": 0.0,
    "engine.cycle.cam_ref_deg": 0.0,
    "engine.ecu.cam_on": 0,
    **{f"engine.ecu.{k}": 0.0 for k in engines.CAM_SCHEDULE},
}
# The b58 lens's widened plant (docs/build_step_2/AMENDMENTS.md B11): the B58 with
# every field the plan adds, at its neutral value, built in memory before any of
# them was written (scratchpad plan_review/b58_lens/sha_old_fields.py), hashed to
# this. With P4 the B58 as built carries exactly that field set, so it hashes the same.
LENS_WIDENED_SHA = "023f5589215ee68e"


def _sha(d):
    """engines.engine_sha's hash of an asdict tree."""
    return hashlib.sha256(json.dumps(d, sort_keys=True).encode("utf-8")).hexdigest()[:16]


def strip_added(plant):
    """(asdict(plant) without the ADDED keys, {key: the value stripped}). A key of
    ADDED that is missing is a KeyError: the keys are all there or this is not the
    tree they were written for."""
    d = asdict(plant)
    taken = {}
    for path in ADDED:
        *parents, key = path.split(".")
        node = d
        for p in parents:
            node = node[p]
        taken[path] = node.pop(key)
    return d, taken


def key_set(d, path=""):
    """{record path: its keys, sorted and space-joined}, as BUILD_STEP_1_KEYS."""
    out = {path: " ".join(sorted(d))}
    for k, v in d.items():
        if isinstance(v, dict):
            out.update(key_set(v, f"{path}.{k}" if path else k))
    return out


class EngineSha(unittest.TestCase):
    def test_without_the_added_keys_it_is_build_step_1s(self):
        """The hash this file computes is engine_sha's; the added keys stripped, it
        is build step 1's, over exactly build step 1's key set (any other new field
        fails), and what was stripped is the B58's typed fuel, lambda clip, form,
        terms and cam, each of its type (cam_on an int, 0 == 0.0 would not tell).
        Unstripped, it is the b58 lens's widened plant's (LENS_WIDENED_SHA)."""
        self.assertEqual(_sha(asdict(PLANT)), engines.engine_sha(PLANT))
        d, taken = strip_added(PLANT)
        self.assertEqual(key_set(d), BUILD_STEP_1_KEYS)
        self.assertEqual(taken, ADDED)
        self.assertEqual({k: type(v) for k, v in taken.items()}, {k: type(v) for k, v in ADDED.items()})
        self.assertEqual(_sha(d), BUILD_STEP_1_SHA)
        self.assertEqual(engines.engine_sha(PLANT), LENS_WIDENED_SHA)
        print(f"\n  engine_sha {engines.engine_sha(PLANT)}; without {sorted(ADDED)}: {_sha(d)}")

    def test_the_comparison_can_fail(self):
        """One ulp on thermal.c_turb moves the stripped hash, and a field that is
        not in ADDED fails the key set."""
        q = replace(PLANT, engine=replace(ENG, thermal=replace(ENG.thermal, c_turb=_up(ENG.thermal.c_turb))))
        d, _ = strip_added(q)
        self.assertEqual(key_set(d), BUILD_STEP_1_KEYS)
        self.assertNotEqual(_sha(d), BUILD_STEP_1_SHA)
        d, _ = strip_added(PLANT)
        d["engine"]["cycle"]["ve_probe"] = 0.0           # no step adds it (ve_map is P3's, in ADDED)
        self.assertNotEqual(key_set(d), BUILD_STEP_1_KEYS)


if __name__ == "__main__":
    unittest.main(verbosity=2)
