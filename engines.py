"""engines.py -- the plants this project simulates: every engine- and car-specific
constant, one frozen record per engine and one per car, and no default engine.

    import engines
    plant = engines.get("b58")          # Plant(engine, car, scenario)
    plant.id                            # 'b58b30o1/a90-supra-zf8hp51'
    engines.engine_sha(plant)           # SHA-256 of every value, as built
    engines.name_of(plant)              # 'b58', the name it was built under
    engines.typed_engine("b58")         # geometry, cycle, charge, fuel: no derived file read
    engines.with_fuel(engine, fuel)     # the engine burning another fuel: both LHV copies move

WHY, 20 October 2026 (decision 24, results/VALIDATION_DECISIONS.md section F).
The H/tau test runs four engines, each in its own car. Until today the B58 WAS
the code: its geometry was plant.Geometry's defaults, its calibration literals
in plant.py, thermal.py and engine_env.py, its car the class attributes of
engine_env.Vehicle. A second engine would have been a second copy of the plant,
or would have inherited the B58 wherever a default stood in for it -- mistake 1
(the 2.0 L inline-four a default ran for three weeks), four times over.

NO DEFAULT ENGINE. Every record below is a frozen dataclass whose every field is
required: `_required` refuses a field with a default when the class is made.
Every entry point of the plant takes the record it needs as a required keyword
-- run_cycle(op, engine=...), ThermalNetwork(params), BaselineECU(cal),
Vehicle(car), damage_rate(..., cal=...), SupervisoryTunerEnv(cycle, plant=...)
-- and get() has no default name. test_engine_threading.py checks all three,
and scans every tracked .py for a plant call that leaves the engine out.

A DEFAULT READ FROM THE PLANT IS NOT A SILENT ONE. Some keywords may be omitted
when the value they stand for belongs to the plant that IS passed: the
TerrainTrainingEnv's speed and ambient default to plant.scenario's, an
environment's compressor inlet to plant.engine.boost.inlet_sea_kpa. What is never
allowed is a default that names an engine by itself.

WHERE THE VALUES LIVE. Three kinds, kept apart (REFERENCES.md, "the four kinds"):

  typed     engine_specs/<engine>.toml and engine_specs/<car>.toml. Every value
            is written { value = ..., label = ..., source = ... }; read_spec()
            refuses a value without a label or a source, a label outside LABELS,
            and the label DERIVED. (Not a folder called engines/: it would
            shadow this module.)
  DERIVED   computed from data by a script, read from the engine's derived file
            and never typed: data/derived_params.json for the B58 (derive_params.py,
            from the car's logs; derived_sha 326c0835548975e2 on 20 October), and
            data/engines/<id>/derived_params.json for every later engine
            (derived.engine_path). DERIVED_FIELDS names each one of the B58's and
            where it is read from, EPA_DERIVED_FIELDS each of an EPA engine's
            (since 22 October 2026: the engine spec's derived_set picks one).
  code      the model's form and the physics true of any petrol engine --
            Woschni's constants, gamma(T), the knock criterion KI = 1 -- stay
            in plant.py and thermal.py. The fuel's heating value and
            stoichiometric ratio stood there too, one gasoline for every
            engine, until 22 October 2026: they are the engine's Fuel now
            (build step 2, P1). Each EPA map was measured on its own test
            fuel, and the validation contract makes the plant and thermal.py
            take each engine's (results/ENGINE_THRESHOLDS.json,
            conventions.fuel). The rich-side slope of the combustion
            efficiency followed the same day (P3): the contract's form C fits
            it per engine, so it is the cycle record's, beside the form tag
            that says which of the contract's forms the engine runs. Form D
            (P4) puts the intake cam in the breathing: its term is the cycle
            record's, and the schedule that sets the cam the ECU record's
            (decision 41: the cam is run by the ECU).

VALUES THE REFERENCE READ AT CALL TIME ARE READ HERE ONCE, when the plant is
built: SPARK_A, ENR_DWELL_LO/HI, the boost envelope and its cap, the
deliverable-torque table. derived.py caches its file per process, so the values
are the ones a call would have read; a re-derivation reaches a process that
builds its plant after it, as before.

THE EPA ENGINES AND THEIR CARS (22 October 2026, build step 2 of decision 24,
P5). Two things differ by plant, and each is named in the spec, never inferred:
  which fields are DERIVED   the engine spec's top-level derived_set picks the
            map (DERIVED_BY_SET): "b58", DERIVED_FIELDS, what derive_params.py
            writes from the car's logs; "epa", EPA_DERIVED_FIELDS, what the EPA
            calibration writes (PLAN.md 5.8). Each field is converted by its own
            converter, keyed by (record, field) (amendment B14).
  which car record           the car spec's top-level kind picks it (CAR_KINDS):
            "two_term_stepped", Car, the Supra unchanged (decision 31);
            "three_term_stepped", EpaCar, EPA's road load and a stepped box;
            "three_term_cvt", CvtCar, EPA's road load and a CVT. EPA's published
            car file is converted by published_car with exact factors.
A calibration evaluates its candidates with build_candidate, which builds a plant
by _build itself from an in-memory DERIVED dict, so that what is fitted is what
get() later builds from the file (mistake 10); an EPA plant built from its file
is refused unless the file's frozen sections are the ones its freeze record
hashed. trainable() names the plants that may train or be scored (decision 47).

THE THREE ARE REGISTERED, AND NOT CALIBRATED (22 October 2026, build step 2 P6).
PLANTS names mazda_25t, honda_l15b7 and ford_27tt beside the B58, each with its
engine spec and its car spec (engine_specs/mazda_25t.toml and cx9_2016.toml,
honda_l15b7.toml and accord_2018.toml, ford_27tt.toml and f150_2015.toml), typed
values only: whatever the EPA rigs cannot set is carried from the B58 and marked
so (decision 45; test_carried.py checks each against the B58's plant). Until a
plant's calibration has written its derived file and its freeze record,
calibrated() says no, get() refuses it with the command that makes the file,
typed_engine() refuses it (its cycle record has DERIVED fields), and this
module's listing names it "not calibrated yet"; a test that walks the registry
and builds what it finds skips such a plant by name.

THE B58, BUILT HERE, IS THE PLANT OF cf43fbb. Every expression in plant.py,
thermal.py and engine_env.py keeps its operations in their old order with the
literal replaced by the record's field, so the numbers are the same doubles;
the identity harness of build step 1 compared the two trees byte for byte.
"""
import hashlib
import json
import math
import os
import struct
import tomllib
from dataclasses import MISSING, asdict, dataclass, fields, replace

import numpy as np

import derived

HERE = os.path.dirname(os.path.abspath(__file__))
SPECS = os.path.join(HERE, "engine_specs")

# What a typed value may be labelled. REFERENCES.md's kinds of number and its
# section 4b outcomes; DERIVED is not among them, on purpose.
LABELS = {
    "PUBLISHED": "a manufacturer's figure, opened and written down (REFERENCES.md kind 3)",
    "CORRELATION": "a constant of a correlation the model cites (REFERENCES.md section 1); "
                   "the source says whether the value itself was read off the page",
    "DERIVED_ONCE": "set once from our own data or our own model, on the date named, and held "
                    "(REFERENCES.md section 4b), for the reason the source gives",
    "DESIGN": "a choice that defines the experiment, not a property to be measured",
    "ASSUMED": "an engineering estimate nobody has verified (REFERENCES.md kind 4)",
}


def _required(cls):
    """Refuse a dataclass field with a default: a default is how mistake 1 happened."""
    for f in fields(cls):
        if f.default is not MISSING or f.default_factory is not MISSING:
            raise TypeError(f"{cls.__name__}.{f.name} has a default; a plant's fields are all required")
    return cls


# ------------------------------------------------------------------ the engine
@_required
@dataclass(frozen=True)
class Geometry:
    """Slider-crank geometry. Lengths in m, valve events in deg aTDC firing."""
    bore: float
    stroke: float
    conrod: float
    n_cyl: int
    comp_ratio: float
    ivc_deg: float
    evo_deg: float

    def __post_init__(self):
        # plant.Geometry.__post_init__'s five lines, in their order
        object.__setattr__(self, "crank", self.stroke / 2.0)
        object.__setattr__(self, "area_piston", np.pi * self.bore ** 2 / 4.0)
        object.__setattr__(self, "vd_cyl", self.area_piston * self.stroke)
        object.__setattr__(self, "vd_total", self.vd_cyl * self.n_cyl)
        object.__setattr__(self, "vc", self.vd_cyl / (self.comp_ratio - 1.0))

    def volume(self, theta_deg):
        """Instantaneous cylinder volume, theta in deg aTDC firing."""
        th = np.radians(theta_deg)
        a, l = self.crank, self.conrod
        s = a * np.cos(th) + np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        return self.vc + self.area_piston * (l + a - s)

    def dvolume_dtheta(self, theta_deg):
        """dV/dtheta in m^3 per degree."""
        th = np.radians(theta_deg)
        a, l = self.crank, self.conrod
        root = np.sqrt(l ** 2 - (a * np.sin(th)) ** 2)
        ds_dth = -a * np.sin(th) - (a ** 2 * np.sin(th) * np.cos(th)) / root
        return -self.area_piston * ds_dth * np.pi / 180.0

    def liner_area(self, theta_deg):
        """Exposed liner + head + piston crown area."""
        v = self.volume(theta_deg)
        x = (v - self.vc) / self.area_piston      # exposed liner height
        return 2.0 * self.area_piston + np.pi * self.bore * x


# THE CYCLE MODEL'S FORMS (22 October 2026, build step 2 of decision 24, P3): the
# validation contract's model form (results/ENGINE_THRESHOLDS.md), A -- the B58's
# cycle, plant.run_cycle as it was -- and its alternatives, each adding to the
# one before: B a linear MAP term in the breathing (plant.volumetric_efficiency),
# C a per-engine rich-side slope of plant.combustion_efficiency. D (P4, the same
# day; decision 41) adds the intake cam phase to the breathing, the cam run by the
# ECU (EcuCal's schedule, engine_env.BaselineECU.cam_deg), so that every policy
# inherits it as it inherits the spark.
CYCLE_FORMS = ("A", "A+B", "A+B+C", "A+B+C+D")
# The rich-side slope forms A and B share (the contract: combustion_efficiency is
# "shared and not fitted" under A; only C fits an engine its own): the literal of
# combustion_efficiency's rich branch, plant.py:91 on cf43fbb. CycleCal holds
# every engine without C to it.
SHARED_RICH_SLOPE = 0.65


@_required
@dataclass(frozen=True)
class CycleCal:
    """The 0-D cycle model's per-engine constants (plant.run_cycle): breathing,
    residual gas, wall and charge temperatures, burn, knock, friction, the port
    and the exhaust backpressure, and the fuel's octane; and, since 22 October
    2026 (build step 2 P3), the model's form and the two terms forms B and C add,
    and (P4) form D's cam term."""
    ve_base: float
    ve_amp: float
    ve_rpm: float
    ve_width: float
    ve_lo: float
    ve_hi: float
    fres_a: float
    fres_b: float
    fres_map_min: float
    fres_lo: float
    fres_hi: float
    t_head_k: float
    port_pickup_k: float
    t_residual_k: float
    flame_lam: float
    flame_width: float
    flame_floor: float
    burn_base: float
    burn_rpm: float
    burn_res: float
    delay_base: float
    delay_rpm: float
    delay_res: float
    wiebe_a: float
    wiebe_m: float
    knock_a: float
    knock_on: float
    knock_p: float
    knock_b: float
    n_poly: float
    fmep_0: float
    fmep_pmax: float
    fmep_sp: float
    fmep_sp2: float
    ua_port: float
    cp_exh: float
    octane: float
    exh_bp_ratio: float
    exh_bp_min_kpa: float
    # The model's form, one of CYCLE_FORMS, and the terms of forms B and C (22
    # October 2026, build step 2 P3): ve_map, per kPa, the breathing's linear MAP
    # term about ve_map_ref_kpa (B); ce_rich_slope, the rich-side slope of
    # combustion_efficiency (C; SHARED_RICH_SLOPE without C). The B58 is form A,
    # the plant of cf43fbb (decision 31), with ve_map 0.0 and the shared 0.65.
    form: str
    ve_map: float
    ve_map_ref_kpa: float
    ce_rich_slope: float
    # Form D's term (22 October 2026, build step 2 P4; decision 41): ve_cam, per
    # crank degree, the breathing's linear term in the intake cam phase about
    # cam_ref_deg. The cam itself is not the cycle's: the ECU schedules it
    # (EcuCal's cam_* fields, engine_env.BaselineECU.cam_deg) and the environment
    # hands it to plant.run_cycle. The B58 has no cam input (form A): 0.0 and 0.0.
    ve_cam: float
    cam_ref_deg: float

    def __post_init__(self):
        # A TERM ITS FORM DOES NOT HAVE IS REFUSED (PLAN.md WP1 P3, P4). Under form A
        # plant.volumetric_efficiency never reads ve_map, so a nonzero one would be
        # a fitted number nothing uses, reported as if it were the model (mistake
        # 25); and a slope other than the shared 0.65 is form C by definition. The
        # type is checked first (amendment B10): under NumPy 2 (NEP 50) a NumPy
        # scalar is not a Python float, and moves a result's bits wherever it meets
        # a float32, so a fit's NumPy value is refused, never converted.
        if type(self.form) is not str:
            raise TypeError(f"CycleCal.form must be a str, not {type(self.form).__name__} ({self.form!r})")
        for name in ("ve_map", "ve_map_ref_kpa", "ce_rich_slope", "ve_cam", "cam_ref_deg"):
            v = getattr(self, name)
            if type(v) is not float:
                raise TypeError(f"CycleCal.{name} must be a Python float, not {type(v).__name__} ({v!r}): "
                                "amendment B10, NEP 50 makes the type load-bearing")
            # A NaN or an infinity is refused too (the review of P3, 22 October 2026):
            # the two checks below compare with != and never look at ve_map_ref_kpa,
            # so a NaN would pass under the form that reads it, and form B's eta_v
            # would come out NaN without a word. ve_map_ref_kpa is typed 100 DESIGN
            # in every spec (decision 41, amendment D8) but stays a field, not a
            # constant: a reference other than 100 must be able to reach the
            # breathing, or nothing shows that it does (mistakes 12, 25;
            # test_fuel_forms.FormsBC). cam_ref_deg, form D's reference, typed 0
            # DESIGN in every spec, is a field for the same reason (P4; FormD).
            if not math.isfinite(v):
                raise ValueError(f"CycleCal.{name} must be finite, not {v!r}")
        if self.form not in CYCLE_FORMS:
            raise ValueError(f"cycle form {self.form!r} is not one of {CYCLE_FORMS} (results/"
                             "ENGINE_THRESHOLDS.md, the model form)")
        terms = self.form.split("+")
        if self.ve_map != 0.0 and "B" not in terms:
            raise ValueError(f"cycle form {self.form!r} has no MAP term (form B), and ve_map is "
                             f"{self.ve_map!r}: nothing would read it")
        if self.ve_cam != 0.0 and "D" not in terms:
            raise ValueError(f"cycle form {self.form!r} has no cam term (form D), and ve_cam is "
                             f"{self.ve_cam!r}: nothing would read it")
        if self.ce_rich_slope != SHARED_RICH_SLOPE and "C" not in terms:
            raise ValueError(f"cycle form {self.form!r} shares the rich slope {SHARED_RICH_SLOPE!r} "
                             f"(only form C fits an engine its own), and ce_rich_slope is {self.ce_rich_slope!r}")


@_required
@dataclass(frozen=True)
class ChargeCal:
    """plant.charge_temperature: the rise over ambient and the block coupling."""
    rise_k: float
    block_coupling: float


@_required
@dataclass(frozen=True)
class BoostCal:
    """plant.boost_ceiling_kpa: the envelope (DERIVED) and the sea-level inlet."""
    envelope_flow: tuple
    envelope_pr: tuple
    pr_cap: float
    inlet_sea_kpa: float


# The ECU's intake cam schedule, its twelve fields in EcuCal's order: the six
# coefficients, the input domain and the output clamp (22 October 2026, build step
# 2 P4; EcuCal's block on the cam says what each is).
CAM_SCHEDULE = ("cam_c0", "cam_c_rpm", "cam_c_map", "cam_c_rpm2", "cam_c_rpm_map", "cam_c_map2",
                "cam_rpm_lo", "cam_rpm_hi", "cam_map_lo", "cam_map_hi", "cam_lo", "cam_hi")


@_required
@dataclass(frozen=True)
class EcuCal:
    """engine_env.BaselineECU: spark map and knock limit, enrichment, compensations,
    knock feedback and the fan schedule; the clip every policy's lambda is held
    in (SupervisoryTunerEnv.step); and, since 22 October 2026 (build step 2 P4),
    the intake cam schedule of form D (BaselineECU.cam_deg)."""
    spark_a: float
    spark_b: float
    spark_c: float
    spark_ref_kpa: float
    spark_min: float
    spark_max: float
    kl_a: float
    kl_b: float
    kl_c: float
    kl_d: float
    enr_load: float
    enr_rpm_lo: float
    enr_rpm_hi: float
    enr_dwell_lo: float
    enr_dwell_hi: float
    enr_depth: float
    iat_gain: float
    iat_ref_c: float
    iat_max: float
    cold_k: float
    cold_retard: float
    knock_step: float
    knock_max: float
    knock_restore: float
    knock_detect_ki: float
    fan_hi_k: float
    fan_lo_k: float
    fan_lo_duty: float
    # The clip on every policy's lambda, the baseline's plus the agent's trim
    # (SupervisoryTunerEnv.step). Until 22 October 2026 it was engine_env.py's
    # literals 0.70 and 1.25, the B58's clip on every engine; it is each
    # engine's own since (build step 2 P2), the B58's the same two doubles. The
    # contract sets each EPA engine's floor, min(0.70, its deepest EPA lambda -
    # 0.01), so that the neutral action stays neutral (results/
    # ENGINE_THRESHOLDS.md, the lambda clip, finding 10). Engine refuses a clip
    # that would hold the baseline's own lambda (a floor above 1 - enr_depth, a
    # ceiling below 1, a negative depth) and a bound that is not a Python float
    # (amendments B1, B10).
    lam_floor: float
    lam_ceiling: float
    # THE INTAKE CAM SCHEDULE OF FORM D (22 October 2026, build step 2 P4; decision
    # 41: the contract's cam is "run by the ECU", results/ENGINE_THRESHOLDS.md, the
    # model form). cam_on is 1 for an engine whose cycle form has D and 0 for every
    # other (Engine refuses the two apart). The cam, in crank degrees, is a full
    # quadratic in rpm/1000 and MAP/100 (cam_c0 to cam_c_map2, in the order
    # BaselineECU.cam_deg sums them), its inputs clamped to the domain cam_rpm_lo-
    # cam_rpm_hi rpm and cam_map_lo-cam_map_hi kPa -- the speed and load of the
    # calibration rows that carry a cam value (amendment C1) -- and its output to
    # cam_lo-cam_hi, their measured cam range, so it is never extrapolated
    # (mistake 6). With the cam off all twelve are 0.0, the neutral values a form
    # without D carries (PLAN.md 5.8); the B58's are.
    cam_on: int
    cam_c0: float
    cam_c_rpm: float
    cam_c_map: float
    cam_c_rpm2: float
    cam_c_rpm_map: float
    cam_c_map2: float
    cam_rpm_lo: float
    cam_rpm_hi: float
    cam_map_lo: float
    cam_map_hi: float
    cam_lo: float
    cam_hi: float

    def __post_init__(self):
        # THE CAM SCHEDULE IS CHECKED WITH ITS RECORD (22 October 2026, build step 2
        # P4), as CycleCal checks its terms. cam_on is a Python int, 0 or 1: a bool
        # is refused (True is not the 1 a spec types, and engine_sha's json writes
        # it as true). The twelve are Python floats (amendment B10: a fit's NumPy
        # scalar is refused, never converted) and finite. A domain or a clamp whose
        # low end passes its high end is refused: np.clip would hand back the high
        # end for every input, a constant cam nobody fitted. With the cam off every
        # one of the twelve is 0.0, since nothing would read it (mistake 25).
        # Whether the cam is on is the cycle form's business: Engine checks that.
        if type(self.cam_on) is not int:
            raise TypeError(f"EcuCal.cam_on must be a Python int, 0 or 1, not {type(self.cam_on).__name__} "
                            f"({self.cam_on!r})")
        if self.cam_on not in (0, 1):
            raise ValueError(f"EcuCal.cam_on must be 0 or 1, not {self.cam_on!r}")
        for name in CAM_SCHEDULE:
            v = getattr(self, name)
            if type(v) is not float:
                raise TypeError(f"EcuCal.{name} must be a Python float, not {type(v).__name__} ({v!r}): "
                                "amendment B10, NEP 50 makes the type load-bearing")
            if not math.isfinite(v):
                raise ValueError(f"EcuCal.{name} must be finite, not {v!r}")
        for lo, hi in (("cam_rpm_lo", "cam_rpm_hi"), ("cam_map_lo", "cam_map_hi"), ("cam_lo", "cam_hi")):
            if getattr(self, lo) > getattr(self, hi):
                raise ValueError(f"EcuCal.{lo} {getattr(self, lo)!r} is above {hi} {getattr(self, hi)!r}: "
                                 "the cam schedule would clamp every input to one end")
        if self.cam_on == 0:
            nonzero = [n for n in CAM_SCHEDULE if getattr(self, n) != 0.0]
            if nonzero:
                raise ValueError(f"the ECU runs no cam (cam_on 0), and its cam schedule sets {nonzero}: "
                                 "nothing would read them (a form without D carries 0.0)")


@_required
@dataclass(frozen=True)
class ThermalParams:
    """thermal.ThermalNetwork's constants. thermal.py's module docstring and the
    block above ThermalNetwork say which are DERIVED, which ASSUMED, and why."""
    c_block: float
    c_oil: float
    c_turb: float
    n_turbines: int
    ua_block_oil: float
    ua_block_amb: float
    ua_oil_amb: float
    ua_oil_ram: float
    ua_turb_amb: float
    ua_gas_turb: float
    ua_rad_min: float
    ua_rad_ram: float
    ua_rad_fan: float
    t_stat_open: float
    t_stat_span: float
    frac_fuel_to_coolant: float
    frac_fuel_to_oil: float
    k_oil_rpm: float
    n_oil_rpm: float
    t_block_warm: float
    t_oil_warm: float
    t_turb_warm: float
    # The fuel's lower heating value, J/kg, which the network's fuel heat reads
    # (thermal.py, ThermalNetwork._substep): a COPY of the engine's
    # fuel.lhv_j_per_kg, made by _build and never typed in [thermal], so that
    # ThermalNetwork(p) keeps its one argument (22 October 2026, build step 2
    # P1). Engine refuses the two apart; with_fuel moves both.
    fuel_lhv_j_per_kg: float


@_required
@dataclass(frozen=True)
class DamageCal:
    """engine_env.damage_rate's knees, scales and weights, and the EGT limit of
    the environment's constraint cost."""
    turb_knee_k: float
    turb_scale_k: float
    oil_knee_k: float
    oil_scale_k: float
    oil_weight: float
    ki_knee: float
    ki_weight: float
    egt_limit_k: float


@_required
@dataclass(frozen=True)
class LoopCal:
    """The environment's load loop (SupervisoryTunerEnv._map_for / _track_torque),
    and the least torque a training road may ask of it."""
    ff_offset_kpa: float
    ff_kpa_per_nm: float
    map_floor_kpa: float
    i_gain: float
    i_clip: float
    p_gain: float
    i_out: float
    torque_floor_nm: float


@_required
@dataclass(frozen=True)
class Fuel:
    """The fuel the engine burns: its lower heating value, J/kg -- the heat the
    cycle releases (plant.run_cycle) and the network's fuel heat (through
    ThermalParams.fuel_lhv_j_per_kg) -- and its stoichiometric air-fuel ratio,
    which sets the fuel mass at a lambda (plant.run_cycle) and turns a measured
    air flow into a fuel flow (car_thermal.measured_fuel_gps).

    WHY, 22 October 2026 (build step 2 of decision 24, P1). Until then both were
    module constants of plant.py, LHV = 44.0e6 and AFR_STOICH = 14.7, and the
    heating value was a literal in thermal.py as well: one gasoline for every
    engine, mistake 1's shape. Each EPA map was measured on its own test fuel,
    and the validation contract makes the plant and thermal.py take each
    engine's (results/ENGINE_THRESHOLDS.json, conventions.fuel). The B58's are
    the old constants, the same doubles, typed in engine_specs/b58.toml [fuel].

    PYTHON FLOATS ONLY (amendment B10). Under NumPy 2 (NEP 50) a Python float is
    a weak scalar and a NumPy float64 is not: 14.7 times a float32 is a float32,
    np.float64(14.7) times a float32 a float64, so the TYPE of a field can move a
    result's bits wherever it meets a float32 (the agent's actions are float32).
    A fit's NumPy scalar is refused here, never converted without a word.

    FINITE AND ABOVE ZERO (22 October 2026, build step 2 P7; the review of P1). A
    NaN heating value used to be refused only by accident, by Engine's copy check
    and with its message about two fuels, and a zero or a negative one not at all;
    a zero afr_st divides the fuel mass by zero (plant.run_cycle). Each is refused
    here with its own message, when the fuel is built: no arithmetic of the B58's
    moves, since its 44.0e6 and 14.7 pass."""
    lhv_j_per_kg: float
    afr_st: float

    def __post_init__(self):
        for f in fields(self):
            v = getattr(self, f.name)
            if type(v) is not float:
                raise TypeError(f"Fuel.{f.name} must be a Python float, not {type(v).__name__} ({v!r}): "
                                "amendment B10, NEP 50 makes the type load-bearing")
            if not (math.isfinite(v) and v > 0.0):
                raise ValueError(f"Fuel.{f.name} must be finite and above 0, not {v!r}: a fuel's heating "
                                 "value and its stoichiometric air-fuel ratio are positive numbers")


@_required
@dataclass(frozen=True)
class Engine:
    id: str
    derived: str              # its derived file, relative to the repository
    geometry: Geometry
    cycle: CycleCal
    charge: ChargeCal
    boost: BoostCal
    ecu: EcuCal
    thermal: ThermalParams
    damage: DamageCal
    loop: LoopCal
    fuel: Fuel                # 22 October 2026 (build step 2 P1); its LHV is copied into thermal

    def __post_init__(self):
        # THE HEATING VALUE LIVES TWICE (22 October 2026, build step 2 P1): in
        # the fuel, which the cycle reads, and in the thermal record, which the
        # network reads (ThermalParams.fuel_lhv_j_per_kg). Two copies that can
        # part are the contract's finding 19: version 1 of its E6 row 3 "moved
        # plant.LHV only, and the thermal network's 44.0e6 would not have
        # followed" (results/ENGINE_THRESHOLDS.md; mistake 25). So an engine whose
        # copies are not the same Python float is refused; with_fuel moves both.
        # Compared by their bits since 22 October 2026 (build step 2 P7; the review
        # of P1): == calls -0.0 and 0.0 the same number and two NaNs different
        # ones, and .hex() writes every NaN as 'nan' whatever its sign and payload
        # (the review of P7), so the copies are compared as their eight bytes.
        lhv = self.thermal.fuel_lhv_j_per_kg
        if type(lhv) is not float or struct.pack("<d", lhv) != struct.pack("<d", self.fuel.lhv_j_per_kg):
            raise ValueError(f"engine {self.id}: thermal.fuel_lhv_j_per_kg is {lhv!r} "
                             f"({type(lhv).__name__}), fuel.lhv_j_per_kg {self.fuel.lhv_j_per_kg!r}: the "
                             "network would burn another fuel than the cycle. Change the fuel with "
                             "engines.with_fuel, which moves both")
        # THE NEUTRAL LAMBDA IS NEVER CLIPPED (22 October 2026, build step 2 P2).
        # Every policy's lambda is the baseline's plus its trim, clipped to
        # [ecu.lam_floor, ecu.lam_ceiling] (SupervisoryTunerEnv.step), while the
        # baseline runs the ECU's own unclipped: 1 - enr_depth * s * t, s and t in
        # [0, 1] (BaselineECU.base_lambda, its v4 law; the v1 map, enrichment_map=
        # True, before/after work only and never built by the environment, bottoms
        # out at 0.82 whatever enr_depth is, and is not covered). A floor above
        # 1 - enr_depth or a ceiling below 1 would clip the neutral action itself,
        # and every baseline-relative term would be offset without a word (the
        # contract's finding 10, results/ENGINE_THRESHOLDS.md; mistake 10). The
        # plan asks for those two; a negative depth is refused too, since the
        # baseline's lambda would then pass 1, and so is a floor at or below 0 (22
        # October 2026, build step 2 P7; the review of P2): with it a depth of 1
        # passes, and the baseline would run lambda 0, a fuel mass divided by zero
        # (plant.run_cycle, m_air / (afr_st * lam)); with the floor above 0 the
        # depth is below 1 by the check itself. The clip compares in float32 (the
        # trims are float32, NEP 50), and rounding keeps the order, so lam_b >=
        # lam_floor holds in float32 too. A Python float bound is cast as the
        # literals were; a NumPy float64 one would make the result float64, a
        # different double wherever the floor binds, so it is refused (amendments
        # B1, B10).
        ecu = self.ecu
        for name in ("lam_floor", "lam_ceiling"):
            v = getattr(ecu, name)
            if type(v) is not float:
                raise TypeError(f"engine {self.id}: ecu.{name} must be a Python float, not "
                                f"{type(v).__name__} ({v!r}): amendment B10, NEP 50 makes the type load-bearing")
        if not (ecu.enr_depth >= 0.0 and 1.0 - ecu.enr_depth >= ecu.lam_floor > 0.0 and ecu.lam_ceiling >= 1.0):
            raise ValueError(f"engine {self.id}: the lambda clip [{ecu.lam_floor!r}, {ecu.lam_ceiling!r}] "
                             f"with the ECU's enrichment depth {ecu.enr_depth!r} would clip the baseline's "
                             "own lambda, which runs from 1 down to 1 - enr_depth: the floor must be above 0 "
                             "and at most 1 - enr_depth, the ceiling at least 1, the depth at least 0 (the "
                             "neutral action would not be neutral)")
        # THE ECU RUNS A CAM EXACTLY WHEN THE FORM READS ONE (22 October 2026, build
        # step 2 P4): ecu.cam_on is 1 if the cycle form has D, 0 otherwise. Apart,
        # plant.volumetric_efficiency would refuse the first cycle -- None for a
        # form-D engine whose ECU runs no cam, a number nothing reads for a form
        # without D -- so they are refused here, when the engine is built, not
        # mid-episode.
        has_d = "D" in self.cycle.form.split("+")
        if ecu.cam_on != (1 if has_d else 0):
            raise ValueError(f"engine {self.id}: the cycle form is {self.cycle.form!r} and ecu.cam_on is "
                             f"{ecu.cam_on!r}: the ECU runs the intake cam (cam_on 1) exactly when the form "
                             "has D (decision 41)")


@_required
@dataclass(frozen=True)
class TypedEngine:
    """The engine's records that hold no DERIVED field -- its geometry, the cycle
    model's constants, the charge temperature's and its fuel -- built from its
    spec alone (typed_engine), without its derived file.

    For what has to run before that file exists. build_dataset.py inverts the
    logged air mass through plant.map_from_airflow and plant.charge_temperature,
    which read the geometry, cycle and charge records only, to write the master
    tables the derived file is made FROM; on cf43fbb it ran with no derived file,
    and engines.get, which builds every record, refused it (the review of 21
    October 2026).
    Anything that reads a DERIVED record -- the boost envelope, the thermal
    network, the ECU's spark offset -- needs the whole plant, engines.get.
    The fuel joined on 22 October 2026 (build step 2 P1): the thermal fit that
    derive_params.py runs turns the logged air into fuel with the fuel's AFR_st
    (calibrate_thermal.load_drive), before the derived file it writes exists."""
    id: str
    geometry: Geometry
    cycle: CycleCal
    charge: ChargeCal
    fuel: Fuel


# ------------------------------------------------------------------ the car
@_required
@dataclass(frozen=True)
class Car:
    """engine_env.Vehicle: mass and road load, the driveline, the shift rule, and
    the deliverable-torque table the kickdown reads (DERIVED, measured through
    this engine's plant), with the conditions it is measured at (table_*)."""
    id: str
    mass: float
    cd_a: float
    crr: float
    wheel_r: float
    final_drive: float
    gears: tuple
    driveline_eff: float
    peak_torque_nm: float
    shift_load: float
    shift_rpm_max: float
    upshift_min_rpm: float
    rpm_min: float
    rpm_max: float
    deliverable_torque: tuple
    # How the table above is measured through the plant (engine_env.
    # measure_deliverable_torque, wide_air.deliverable_torque): its rpm grid,
    # the ambient and the block it is measured in, and how many steps the load
    # loop settles for. They were measure_deliverable_torque's defaults, the
    # B58's, for any plant passed, until 21 October 2026 (the review of build
    # step 1): the next engine's table would have been measured on the B58's grid.
    table_rpm_lo: int
    table_rpm_hi: int
    table_rpm_step: int
    table_t_amb: float
    table_t_block: float
    table_settle: int

    @property
    def table_rpms(self):
        """The table's rpm grid: table_rpm_lo to table_rpm_hi, in table_rpm_step."""
        return tuple(range(self.table_rpm_lo, self.table_rpm_hi + 1, self.table_rpm_step))


# What a scalar field of each annotation may hold (amendment B10): a float field a
# Python float or int (TOML writes 1000 for a 1000.0, and a Python int is as weak
# as a float under NEP 50), an int field an int, a str field a str.
_SCALAR_TYPES = {float: (float, int), int: (int,), str: (str,)}


def _python_scalars(rec):
    """Refuse a record whose scalar fields do not hold a Python value of their own
    annotated type (_SCALAR_TYPES; amendment B10: under NumPy 2, NEP 50, a NumPy
    scalar is not a weak Python float, and moves a result's bits wherever it meets
    a float32). Checked by type(), so a NumPy scalar -- np.float64 subclasses
    float -- and a bool -- True is not the 1 a spec types -- are refused; a str in
    a float field, or a float in an int field (table_rpm_lo, table_settle), is
    refused here rather than failing later, or never. A fit's NumPy value is
    refused, never converted without a word. Each field against its annotation
    since 22 October 2026 (the review of P5): it was any of float, int and str for
    every field. Tuple fields are checked by their record: EpaCar's and CvtCar's
    by _car_tuples (P7); the Supra's Car calls neither (decision 31)."""
    for f in fields(rec):
        if f.type is tuple:
            continue
        want = _SCALAR_TYPES.get(f.type)
        if want is None:
            raise TypeError(f"{type(rec).__name__}.{f.name} is annotated {f.type!r}, which "
                            "engines._SCALAR_TYPES does not check: add its rule there")
        v = getattr(rec, f.name)
        if type(v) not in want:
            raise TypeError(f"{type(rec).__name__}.{f.name} must be a Python "
                            f"{' or '.join(t.__name__ for t in want)}, not {type(v).__name__} ({v!r}): "
                            "amendment B10, NEP 50 makes the type load-bearing")


def _car_tuples(rec):
    """Refuse an EPA car record whose tuple fields do not hold Python values (22
    October 2026, build step 2 P7; the review of P5; amendment B10): the
    deliverable-torque table a tuple of (rpm, Nm) pairs, each a tuple of a Python
    int and a Python float or int -- _epa_table's rule, () while the table is not
    measured -- and a stepped box's gears a tuple of Python floats or ints. The
    build makes both so (_epa_table; read_spec turns a TOML array into a tuple),
    but a dataclasses.replace converts nothing, and _python_scalars skips a tuple
    field: a NumPy torque or a list of gears would otherwise build. Checked by
    type(), so a bool, a NumPy scalar and a list are each refused."""
    name = f"{type(rec).__name__} {rec.id}"
    t = rec.deliverable_torque
    if type(t) is not tuple or not all(
            type(p) is tuple and len(p) == 2 and type(p[0]) is int and type(p[1]) in (float, int) for p in t):
        raise TypeError(f"{name}: deliverable_torque must be a tuple of (rpm, Nm) tuples, a Python int and a "
                        f"Python float or int each, not {t!r}: amendment B10, NEP 50 makes the type load-bearing")
    if any(f.name == "gears" for f in fields(rec)):
        g = rec.gears
        if type(g) is not tuple or not all(type(x) in (float, int) for x in g):
            raise TypeError(f"{name}: gears must be a tuple of Python floats or ints, not {g!r}: amendment B10")


# EPA'S ROAD LOAD (22 October 2026, build step 2 P5; decision 42). The three EPA
# cars run EPA's certification road load, not a drag area and a rolling
# coefficient: F = (A + B v) cos(theta) + C v^2 rho/rho_ref + m g sin(theta)
# (engine_env.EpaVehicle.road_force_n), A, B, C converted from EPA's lbf, mph form
# with exact factors (published_car) and rho_ref EPA's reference air. The Supra
# keeps Car, its two-term road load and its constants, unchanged (decision 31).


@_required
@dataclass(frozen=True)
class EpaCar:
    """engine_env.EpaVehicle: a car with EPA's three-term road load and a stepped
    box (the CX-9, the F-150; PLAN.md 7.1). Car's fields without cd_a and crr, and
    the road load: road_a_n (N), road_b_n_per_mps (N per m/s), road_c_n_per_mps2
    (N per (m/s)^2) and road_rho_ref (kg/m^3, the air the coefficients hold at).
    The gearbox, its shift rule and the deliverable-torque table are Car's, read
    by the same methods of engine_env.Vehicle (22 October 2026, build step 2 P5).

    Where each comes from: mass, the wheel radius and the road load are converted
    from the car's published file (published_car); the gears, the final drive and
    the shift constants are typed; the table is DERIVED, measured through the
    engine's plant after its freeze."""
    id: str
    mass: float
    road_a_n: float
    road_b_n_per_mps: float
    road_c_n_per_mps2: float
    road_rho_ref: float
    wheel_r: float
    final_drive: float
    gears: tuple
    driveline_eff: float
    peak_torque_nm: float
    shift_load: float
    shift_rpm_max: float
    upshift_min_rpm: float
    rpm_min: float
    rpm_max: float
    deliverable_torque: tuple
    table_rpm_lo: int
    table_rpm_hi: int
    table_rpm_step: int
    table_t_amb: float
    table_t_block: float
    table_settle: int

    table_rpms = Car.table_rpms             # the same grid rule, one definition

    def __post_init__(self):
        _python_scalars(self)
        _car_tuples(self)
        if not (self.road_rho_ref > 0.0 and self.mass > 0.0 and self.wheel_r > 0.0):
            raise ValueError(f"EpaCar {self.id}: mass {self.mass!r}, wheel_r {self.wheel_r!r} and "
                             f"road_rho_ref {self.road_rho_ref!r} must be positive")


# THE ACCORD'S CVT (22 October 2026, build step 2 P5; decision 40, its law (b),
# specified by amendment F6): a stateless kickdown. The box holds its top ratio
# while the demand there is at most kickdown_load (0.75, ASSUMED) of the
# deliverable torque; otherwise it runs the lowest engine speed whose demand is at
# most target_load (0.65, DESIGN) of it. engine_env.CvtVehicle runs it.


@_required
@dataclass(frozen=True)
class CvtCar:
    """engine_env.CvtVehicle: a car with EPA's three-term road load and a CVT (the
    Accord; PLAN.md 7.1). No gears: the ratio runs from ratio_low_gear down to
    ratio_top_gear (the published range), set by decision 40's law from
    kickdown_load, target_load and cvt_rpm_min, the engine speed the law never
    goes under. The road load is EpaCar's; the deliverable-torque table and its
    measuring conditions are Car's (22 October 2026, build step 2 P5).

    Where each comes from: mass, the wheel radius and the road load are converted
    from the car's published file (published_car), the radius at the top ratio;
    the ratio range and the final drive are typed (PUBLISHED); the law's three
    numbers are typed (decision 40); the table is DERIVED."""
    id: str
    mass: float
    road_a_n: float
    road_b_n_per_mps: float
    road_c_n_per_mps2: float
    road_rho_ref: float
    wheel_r: float
    final_drive: float
    ratio_low_gear: float
    ratio_top_gear: float
    driveline_eff: float
    kickdown_load: float
    target_load: float
    cvt_rpm_min: float
    rpm_min: float
    rpm_max: float
    deliverable_torque: tuple
    table_rpm_lo: int
    table_rpm_hi: int
    table_rpm_step: int
    table_t_amb: float
    table_t_block: float
    table_settle: int

    table_rpms = Car.table_rpms             # the same grid rule, one definition

    def __post_init__(self):
        # A LAW THAT CANNOT RUN IS REFUSED WHEN THE CAR IS BUILT, not mid-episode: a
        # range whose low ratio is not above its top one, a load outside (0, 1], a
        # target load not below the kickdown load, a floor of the law under the
        # calibration's lowest line (mistake 6: never run the engine where it was not
        # measured) or above its highest.
        _python_scalars(self)
        _car_tuples(self)
        if not (self.ratio_low_gear > self.ratio_top_gear > 0.0):
            raise ValueError(f"CvtCar {self.id}: the ratio range {self.ratio_low_gear!r} to "
                             f"{self.ratio_top_gear!r} must run from a low ratio down to a smaller top one")
        for name in ("kickdown_load", "target_load", "driveline_eff"):
            if not 0.0 < getattr(self, name) <= 1.0:
                raise ValueError(f"CvtCar {self.id}: {name} {getattr(self, name)!r} must lie in (0, 1]")
        # The kickdown's reserve (22 October 2026, the review of P5): law (b) is "a
        # kickdown law with a reserve" (PLAN.md CL-5; decision 40, 0.65 under 0.75).
        # With target_load above kickdown_load, N_eco itself can hold target_load
        # once economy has failed, and ratio_for hands back the economy ratio
        # labelled kickdown, so C5's threshold (decision 70) no longer separates the
        # branches; with the two equal the kickdown lands with no reserve at all.
        if not self.target_load < self.kickdown_load:
            raise ValueError(f"CvtCar {self.id}: target_load {self.target_load!r} must lie below kickdown_load "
                             f"{self.kickdown_load!r}: decision 40's law kicks down to a reserve")
        if not self.rpm_min <= self.cvt_rpm_min < self.rpm_max:
            raise ValueError(f"CvtCar {self.id}: cvt_rpm_min {self.cvt_rpm_min!r} must lie in "
                             f"[rpm_min {self.rpm_min!r}, rpm_max {self.rpm_max!r})")
        if not (self.road_rho_ref > 0.0 and self.mass > 0.0 and self.wheel_r > 0.0):
            raise ValueError(f"CvtCar {self.id}: mass {self.mass!r}, wheel_r {self.wheel_r!r} and "
                             f"road_rho_ref {self.road_rho_ref!r} must be positive")


# The car record each car spec's top-level `kind` builds (22 October 2026, build
# step 2 P5). A car spec without a kind is refused: there is no default car.
CAR_KINDS = {"two_term_stepped": Car, "three_term_stepped": EpaCar, "three_term_cvt": CvtCar}


@_required
@dataclass(frozen=True)
class Scenario:
    """The plant's locked climb: grade (fraction), road speed (km/h), ambient (K).
    engine_env.locked_climb builds it; the fingerprint's FATAL `scenario`."""
    grade: float
    v_kmh: float
    t_amb: float


@_required
@dataclass(frozen=True)
class Plant:
    engine: Engine
    car: Car                  # or EpaCar, CvtCar: the car spec's kind (CAR_KINDS; 22 October 2026)
    scenario: Scenario

    @property
    def id(self):
        return f"{self.engine.id}/{self.car.id}"


# ------------------------------------------------------------------ reading
def read_spec(name):
    """engine_specs/<name>.toml as {section: {field: value}}, plus "_meta" for the
    top-level keys. Every value is checked: a label from LABELS (never DERIVED),
    a non-empty source. Arrays come back as tuples."""
    path = os.path.join(SPECS, name + ".toml")
    with open(path, "rb") as fh:
        raw = tomllib.load(fh)
    out = {"_meta": {}}
    for key, val in raw.items():
        if not isinstance(val, dict):
            out["_meta"][key] = val
            continue
        out[key] = {f: _typed(name, key, f, entry) for f, entry in val.items()}
    return out


def _typed(spec, section, field, entry):
    where = f"engine_specs/{spec}.toml [{section}] {field}"
    if not isinstance(entry, dict) or "value" not in entry:
        raise ValueError(f"{where}: every value is written {{ value = ..., label = ..., source = ... }}")
    extra = set(entry) - {"value", "label", "source", "unit"}
    if extra:
        raise ValueError(f"{where}: unknown keys {sorted(extra)}")
    label = entry.get("label")
    if label == "DERIVED":
        raise ValueError(f"{where}: a DERIVED value is never typed. It is computed from data and read "
                         "from the engine's derived file (engines.DERIVED_BY_SET)")
    if label not in LABELS:
        raise ValueError(f"{where}: label {label!r} is not one of {sorted(LABELS)}")
    src = entry.get("source")
    if not isinstance(src, str) or not src.strip():
        raise ValueError(f"{where}: no source. A typed value says where it comes from, or why it is assumed")
    v = entry["value"]
    return tuple(v) if isinstance(v, list) else v


# Every DERIVED field: (record, field) -> (section, key) in the engine's derived
# file, key None for a whole section. The B58's file is written by
# derive_params.py; an EPA engine's by its own calibration (EPA_DERIVED_FIELDS,
# below; 22 October 2026). This is the B58's map, unchanged.
DERIVED_FIELDS = {
    ("thermal", k): ("thermal", k) for k in (
        "c_block", "c_oil", "ua_block_oil", "ua_block_amb", "ua_oil_amb", "ua_oil_ram",
        "ua_rad_min", "ua_rad_ram", "ua_rad_fan", "t_stat_open", "t_stat_span",
        "frac_fuel_to_coolant", "frac_fuel_to_oil", "k_oil_rpm", "n_oil_rpm")
}
DERIVED_FIELDS.update({
    ("boost", "envelope_flow"): ("boost_ceiling", "envelope_flow"),
    ("boost", "envelope_pr"): ("boost_ceiling", "envelope_pr"),
    ("boost", "pr_cap"): ("boost_ceiling", "pr_cap"),
    ("ecu", "spark_a"): ("spark", "SPARK_A"),
    ("ecu", "enr_dwell_lo"): ("enrichment", "ENR_DWELL_LO"),
    ("ecu", "enr_dwell_hi"): ("enrichment", "ENR_DWELL_HI"),
    ("car", "deliverable_torque"): ("deliverable_torque", None),
})


# THE EPA ENGINES' DERIVED FIELDS (22 October 2026, build step 2 P5; PLAN.md 5.8):
# what the EPA calibration (calibrate_epa.py, build step 2 WP3-WP4) writes to
# data/engines/<id>/derived_params.json. Three sections are written at the freeze
# and never after (FROZEN_SECTIONS): the cycle model's fitted constants and its
# form, the ECU's spark, knock-limit, enrichment and cam schedule, and the boost
# envelope; a term a form does not use is written at its neutral value. Three are
# completed after the freeze from no EPA data: the deliverable-torque table, the
# K3 knee (damage.turb_knee_k, decision 33) and the torque floor. Every other field
# of an EPA engine is typed in its spec, the constants carried from the B58 among
# them (decision 45).
EPA_DERIVED_FIELDS = {
    ("cycle", k): ("cycle", k) for k in (
        "form", "ve_base", "ve_amp", "ve_rpm", "ve_width", "ve_map", "ve_cam", "ce_rich_slope",
        "burn_base", "burn_rpm", "delay_base", "delay_rpm", "fmep_0", "fmep_pmax", "fmep_sp",
        "fmep_sp2", "ua_port", "exh_bp_ratio", "exh_bp_min_kpa", "knock_a")
}
EPA_DERIVED_FIELDS.update({
    ("ecu", k): ("ecu", k) for k in (
        "spark_a", "spark_b", "spark_c", "spark_min", "spark_max", "kl_a", "kl_b", "kl_c", "kl_d",
        "enr_load", "enr_rpm_lo", "enr_rpm_hi", "enr_depth", "cam_on") + CAM_SCHEDULE
})
EPA_DERIVED_FIELDS.update({
    ("boost", "envelope_flow"): ("boost_ceiling", "envelope_flow"),
    ("boost", "envelope_pr"): ("boost_ceiling", "envelope_pr"),
    ("boost", "pr_cap"): ("boost_ceiling", "pr_cap"),
    ("damage", "turb_knee_k"): ("k3", "turb_knee_k"),
    ("loop", "torque_floor_nm"): ("loop", "torque_floor_nm"),
    ("car", "deliverable_torque"): ("deliverable_torque", None),
})
# The sections of an EPA derived file its freeze record hashes (PLAN.md 5.8).
FROZEN_SECTIONS = ("cycle", "ecu", "boost_ceiling")

# Which fields are DERIVED, chosen by the engine spec's top-level derived_set
# (22 October 2026, build step 2 P5). DERIVED_FIELDS stays the B58's map, as it was.
DERIVED_BY_SET = {"b58": DERIVED_FIELDS, "epa": EPA_DERIVED_FIELDS}


# HOW EACH DERIVED FIELD IS CONVERTED, keyed by (record, field) with each DERIVED
# set (22 October 2026, build step 2 P5; amendment B14). Not by the field's type:
# a pair table and a float tuple are both annotated `tuple`. The B58's three
# branches are _derived_value's as it was on cf43fbb, byte for byte, the ()
# fallbacks under DERIVING_PARAMS=1 included; the EPA set's own are strict, since
# nothing there has a history to keep: a str is a str, an int an int (never a
# bool), a number a number, and the table and the envelope are checked element by
# element (_epa_table, _epa_floats). The B58's _table and _floats take a "1000" or
# a "1.5" through int() and float(); the EPA set used them until the review of P5
# (22 October 2026), which its strictness did not hold.
def _table(v):
    if v is None:                # only while derive_params.py builds the file
        return ()
    return tuple((int(a), float(b)) for a, b in v)


def _floats(v):
    if isinstance(v, float) and math.isnan(v):
        return ()
    return tuple(float(x) for x in v)


def _str(v):
    if type(v) is not str:
        raise TypeError(f"a str is DERIVED here, and the derived value is {v!r} ({type(v).__name__})")
    return v


def _int(v):
    if type(v) is not int:
        raise TypeError(f"an int is DERIVED here, and the derived value is {v!r} ({type(v).__name__})")
    return v


def _number(v):
    if type(v) not in (float, int):
        raise TypeError(f"a number is DERIVED here, and the derived value is {v!r} ({type(v).__name__})")
    return float(v)


def _epa_table(v):
    """An EPA car's deliverable-torque table: a list of [rpm, Nm] pairs, each rpm
    an int and each torque a number, never converted from a str or a float rpm.
    () for no table: [] in a candidate's values while it is not yet measured, None
    while the completion builds the file (DERIVING_PARAMS=1; derived.py), as the
    B58's _table gives while derive_params.py builds its (22 October 2026, the
    review of P5)."""
    if v is None:
        return ()
    if type(v) not in (list, tuple) or not all(
            type(p) in (list, tuple) and len(p) == 2 and type(p[0]) is int and type(p[1]) in (float, int)
            for p in v):
        raise TypeError(f"a table of [rpm (int), Nm (number)] pairs is DERIVED here, and the derived value "
                        f"is {v!r}")
    return tuple((a, float(b)) for a, b in v)


def _epa_floats(v):
    """An EPA engine's boost envelope: a list of numbers, each type-checked as
    _number checks a scalar. No NaN fallback, unlike the B58's _floats: the
    envelope is frozen (FROZEN_SECTIONS), so a file built after the freeze holds
    it, and a candidate holds every value (22 October 2026, the review of P5)."""
    if type(v) not in (list, tuple) or not all(type(x) in (float, int) for x in v):
        raise TypeError(f"a list of numbers is DERIVED here, and the derived value is {v!r} "
                        f"({type(v).__name__})")
    return tuple(float(x) for x in v)


CONVERT_BY_SET = {
    # Vehicle.DELIVERABLE_TORQUE's conversion, the envelope's, float otherwise
    "b58": {k: (_table if k[0] == "car" else _floats if k[1] in ("envelope_flow", "envelope_pr") else float)
            for k in DERIVED_FIELDS},
    "epa": {k: {("car", "deliverable_torque"): _epa_table, ("boost", "envelope_flow"): _epa_floats,
                ("boost", "envelope_pr"): _epa_floats, ("cycle", "form"): _str,
                ("ecu", "cam_on"): _int}.get(k, _number)
            for k in EPA_DERIVED_FIELDS},
}
if any(set(CONVERT_BY_SET[s]) != set(DERIVED_BY_SET[s]) for s in DERIVED_BY_SET) or \
        set(CONVERT_BY_SET) != set(DERIVED_BY_SET):
    raise RuntimeError("engines.CONVERT_BY_SET must convert exactly the fields of DERIVED_BY_SET")


def _python_value(v):
    """True for a Python float, int or str (not a bool), or a tuple of such values
    or of such tuples: what a record field may hold (amendment B10)."""
    if type(v) is tuple:
        return all(_python_value(x) for x in v)
    return type(v) in (float, int, str)


def _read_derived(source, section, key):
    """A value of the derived file `source` names, or of an in-memory dict shaped
    like one (a candidate's, build_candidate). The file is read by derived.get, as
    it always was; a candidate's dict holds every value or is refused, since a
    candidate has no file being built for NaN to stand in for."""
    if not isinstance(source, dict):
        return derived.get(section, key, path=source)
    d = source.get(section)
    if d is None or (key is not None and (not isinstance(d, dict) or key not in d)):
        raise KeyError(f"the candidate's values have no '{section}" + (f".{key}'" if key else "'")
                       + ": a candidate holds every DERIVED field of its engine's set (engines.build_candidate)")
    return d if key is None else d[key]


def _derived_value(source, derived_set, record, field):
    """One DERIVED field, converted by its own converter, keyed by (record, field)
    in its DERIVED set (amendment B14): for the B58 as the code that used to read
    it converted it. `source` is the derived file's path, or a candidate's
    in-memory dict. The converted value must be Python-typed (amendment B10)."""
    section, key = DERIVED_BY_SET[derived_set][(record, field)]
    v = CONVERT_BY_SET[derived_set][(record, field)](_read_derived(source, section, key))
    if not _python_value(v):
        raise TypeError(f"[{record}] {field}: the DERIVED value {v!r} is not Python-typed (amendment B10)")
    return v


def _record(cls, record, typed, source, derived_set, converted):
    """A record from its typed section, its DERIVED fields and its converted ones.
    A field comes from exactly one of the three, and none may be missing.
    `source` None builds a record with no DERIVED field only (typed_engine): one
    that has one is refused, never given NaN. `derived_set` names the DERIVED set
    (DERIVED_BY_SET: PLAN.md's derived_map, and its converters with it);
    `converted` holds the values published_car converts, {} for every record but
    an EPA car (22 October 2026, build step 2 P5)."""
    want = [f.name for f in fields(cls)]
    unknown = (set(typed) | set(converted)) - set(want)
    if unknown:
        raise ValueError(f"[{record}] has fields {cls.__name__} does not: {sorted(unknown)}")
    dmap = DERIVED_BY_SET[derived_set]
    kw = {}
    for name in want:
        is_derived = (record, name) in dmap
        if is_derived and name in typed:
            raise ValueError(f"[{record}] {name} is DERIVED and must not be typed")
        if name in converted and (is_derived or name in typed):
            raise ValueError(f"[{record}] {name} is converted from the car's published file "
                             "(engines.published_car) and must be neither typed nor DERIVED")
        if is_derived and source is None:
            raise ValueError(f"[{record}] {name} is DERIVED: it is read from the engine's derived "
                             "file, so this record needs engines.get, not typed_engine")
        if is_derived:
            kw[name] = _derived_value(source, derived_set, record, name)
        elif name in typed:
            kw[name] = typed[name]
        elif name in converted:
            kw[name] = converted[name]
        else:
            raise ValueError(f"[{record}] {name} is missing: neither typed, DERIVED nor converted")
    return cls(**kw)


# THE TOP-LEVEL KEYS A SPEC MUST CARRY, by its derived set or its car kind (22
# October 2026, build step 2 P5). Each is required -- a spec without a derived_set
# or a kind is refused, never given the B58's -- and an unknown key is refused,
# since nothing would read it (a misspelt `freeze` would otherwise skip the check
# it names). Their labels and sources are TOML comments in the spec: read_spec
# reads a top-level table as a section, so they cannot be { value, label, source }
# entries (amendment B13). They are hashed by their values (fingerprint's
# _spec_values), so adding them moved plant_sha. test_engine_threading.py checks
# each comment ("# <key> -- ...", a label, a source) in every registered plant's
# specs, so P6's six EPA specs carry them too: derived_set and freeze in each
# engine spec, kind and published in each car spec (the review of P5).
#   derived_set  "b58" or "epa", the DERIVED set (DERIVED_BY_SET)
#   freeze       an EPA engine's freeze record, results/EPA_CALIBRATION/<id>/freeze.json
#   kind         the car record (CAR_KINDS)
#   published    an EPA car's published file under engine_specs/cars/ (published_car)
ENGINE_KEYS = {"b58": ("id", "derived", "derived_set"), "epa": ("id", "derived", "derived_set", "freeze")}
CAR_KEYS = {"two_term_stepped": ("id", "kind"), "three_term_stepped": ("id", "kind", "published"),
            "three_term_cvt": ("id", "kind", "published")}


def _top_level(spec, raw, what, by, table):
    """A spec's top-level keys, checked: `by` names the one that picks the key set
    (`table`); refused if it is missing or unknown, or if the keys are not the set's."""
    meta = raw["_meta"]
    pick = meta.get(by)
    if pick not in table:
        raise ValueError(f"engine_specs/{spec}.toml: the {what} spec's top-level `{by}` is {pick!r}, not one "
                         f"of {sorted(table)}. It is required: there is no default (CLAUDE.md mistake 1)")
    if sorted(meta) != sorted(table[pick]):
        raise ValueError(f"engine_specs/{spec}.toml: a {by} {pick!r} spec's top-level keys are "
                         f"{list(table[pick])}, and these are {sorted(meta)}")
    return meta


def _build(engine_spec, car_spec, values=None):
    """The Plant the two specs describe, its DERIVED fields read from the engine's
    derived file, or, for a candidate (build_candidate), from `values`, an
    in-memory dict shaped like that file: one constructor for both, so a
    candidate is what get() later builds from the file (mistake 10)."""
    e, c = read_spec(engine_spec), read_spec(car_spec)
    em = _top_level(engine_spec, e, "engine", "derived_set", ENGINE_KEYS)
    cm = _top_level(car_spec, c, "car", "kind", CAR_KEYS)
    dset = em["derived_set"]
    path = os.path.join(HERE, em["derived"])
    if values is None and "freeze" in ENGINE_KEYS[dset]:
        _check_freeze(engine_spec, path, os.path.join(HERE, em["freeze"]))
    source = path if values is None else values
    fuel = _record(Fuel, "fuel", e.get("fuel", {}), source, dset, {})
    # The thermal record's heating value is the fuel's, copied here (22 October
    # 2026, build step 2 P1). Typed in [thermal] it would be a second source for
    # one number, and the copy below would overwrite it without a word: refused.
    if "fuel_lhv_j_per_kg" in e.get("thermal", {}):
        raise ValueError(f"engine_specs/{engine_spec}.toml [thermal] fuel_lhv_j_per_kg: it is the "
                         "fuel's, copied from [fuel] lhv_j_per_kg when the plant is built, and never typed")
    engine = Engine(
        id=em["id"], derived=em["derived"],
        geometry=_record(Geometry, "geometry", e.get("geometry", {}), source, dset, {}),
        cycle=_record(CycleCal, "cycle", e.get("cycle", {}), source, dset, {}),
        charge=_record(ChargeCal, "charge", e.get("charge", {}), source, dset, {}),
        boost=_record(BoostCal, "boost", e.get("boost", {}), source, dset, {}),
        ecu=_record(EcuCal, "ecu", e.get("ecu", {}), source, dset, {}),
        thermal=_record(ThermalParams, "thermal",
                        dict(e.get("thermal", {}), fuel_lhv_j_per_kg=fuel.lhv_j_per_kg), source, dset, {}),
        damage=_record(DamageCal, "damage", e.get("damage", {}), source, dset, {}),
        loop=_record(LoopCal, "loop", e.get("loop", {}), source, dset, {}),
        fuel=fuel)
    # The car record is the one its spec's kind names; an EPA car's mass, radius
    # and road load are converted from its published file (22 October 2026, build
    # step 2 P5). Its DERIVED table comes from the engine's file, in the engine's set.
    kind = cm["kind"]
    converted = {} if kind == "two_term_stepped" else published_car(cm["published"], kind)
    car = _record(CAR_KINDS[kind], "car", dict(c.get("car", {}), id=cm["id"]), source, dset, converted)
    scenario = _record(Scenario, "scenario", c.get("scenario", {}), source, dset, {})
    return Plant(engine=engine, car=car, scenario=scenario)


def frozen_sections_sha256(values):
    """sha256 of the canonical JSON of an EPA derived file's frozen sections
    (FROZEN_SECTIONS: cycle, ecu, boost_ceiling; PLAN.md 5.8): sorted keys, each
    float as its repr (json's), no NaN, LF (json.dumps writes no line break).
    The one definition (22 October 2026, build step 2 P5): the freeze record
    stores it and _build checks it, so the calibration's freeze (epa_freeze.py,
    WP3) must call this, never a copy (mistake 10)."""
    missing = [s for s in FROZEN_SECTIONS if s not in values]
    if missing:
        raise ValueError(f"the derived values have no frozen section {missing} (engines.FROZEN_SECTIONS)")
    blob = json.dumps({s: values[s] for s in FROZEN_SECTIONS}, sort_keys=True, allow_nan=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _check_freeze(engine_spec, path, freeze_path):
    """Refuse an EPA engine whose derived file's frozen sections are not the ones
    its freeze record hashed (PLAN.md 5.8, amendment F7): a constant edited after
    the freeze would otherwise be validated as the frozen model. The derived file
    is read first, so a missing one is named with the command that makes it."""
    d = derived.all_params(path=path)
    if not os.path.exists(freeze_path):
        raise FileNotFoundError(f"engine_specs/{engine_spec}.toml: no freeze record {os.path.relpath(freeze_path, HERE)}. "
                                "An EPA plant is built from its derived file only after its freeze; a "
                                "calibration evaluates its candidates with engines.build_candidate")
    with open(freeze_path, encoding="utf-8") as fh:
        want = json.load(fh).get("frozen_sections_sha256")
    got = frozen_sections_sha256(d)
    if got != want:
        raise ValueError(f"engine_specs/{engine_spec}.toml: the frozen sections of {os.path.relpath(path, HERE)} "
                         f"hash to {got}, and its freeze record {os.path.relpath(freeze_path, HERE)} holds {want!r}: "
                         "a frozen constant changed after the freeze")


# EXACT UNIT FACTORS (engine_specs/cars/README.md, "Deriving what the model
# needs"): exact by definition. The EPA reference air the road-load targets hold
# at, 98.21 kPa and 20 C (40 CFR 1066.305(a), as the README cites it), with the
# environment's own gas constant (engine_env.py's rho, 287.0).
LB_KG = 0.45359237
LBF_N = 4.4482216152605
MPH_MPS = 0.44704
MPH_M_PER_MIN = 26.8224
EPA_REF_KPA = 98.21
EPA_REF_K = 293.15
R_AIR_ENV = 287.0

# Where each converted value is read in a published car file, and the top ratio
# the wheel radius uses: a stepped box's last gear, a CVT's top ratio (its range
# is printed lowest gear first).
_TOP_RATIO = {"three_term_stepped": ("gear_ratios", -1), "three_term_cvt": ("cvt_ratio_range", 1)}


def published_car(path, kind):
    """The values a car record takes from the car's published file
    engine_specs/cars/<car>.toml, converted with exact factors (22 October 2026,
    build step 2 P5; decision 42; engine_specs/cars/README.md, "Deriving what the
    model needs"), from the row of EPA's Test Car List it holds:

      mass                 equivalent_test_weight_lb x LB_KG: EPA's test weight,
                           the loaded car (decision 42), not a curb weight
      road_a_n             target_coef_a_lbf x LBF_N
      road_b_n_per_mps     target_coef_b_lbf_per_mph x LBF_N / MPH_MPS
      road_c_n_per_mps2    target_coef_c_lbf_per_mph2 x LBF_N / MPH_MPS^2
      road_rho_ref         EPA_REF_KPA x 1e3 / (R_AIR_ENV x EPA_REF_K): 1.167304 kg/m^3
      wheel_r              MPH_M_PER_MIN x top x axle_ratio / (2 pi x n_over_v_rpm_per_mph):
                           EPA's N/V with no converter slip, and EPA's own axle
                           ratio, the row's (the CX-9's 4.41, not the 4.411 its
                           final_drive table prints: decision 42 discloses the
                           2.3e-4); never from D3

    `top` is the top gear of a stepped box (kind "three_term_stepped") or the
    top of a CVT's ratio range ("three_term_cvt"): for the Accord that reads EPA's
    N/V as measured in the top ratio, which no source states (a CVT's N/V depends
    on the ratio it was in; the README asks which the code uses). The road load is
    valid 15-115 km/h, so the 130 km/h climb extrapolates it (mistake 6;
    engine_env.EpaVehicle says by how much the convention matters there).

    `kind` is a car spec's three-term kind; the Supra's two-term car converts
    nothing (decision 31: its plant keeps its own typed values). Every value used
    must have status PUBLISHED; each returned value is a Python float (amendment B10)."""
    if kind not in _TOP_RATIO:
        raise ValueError(f"published_car converts a car of kind {sorted(_TOP_RATIO)}, not {kind!r}: the "
                         "Supra's car runs its own typed values (decision 31)")
    full = path if os.path.isabs(path) else os.path.join(HERE, path)
    with open(full, "rb") as fh:
        pub = tomllib.load(fh)
    where = os.path.relpath(full, HERE)
    table, index = _TOP_RATIO[kind]
    for name in (table, "epa_test_car"):
        if not isinstance(pub.get(name), dict) or pub[name].get("status") != "PUBLISHED":
            raise ValueError(f"{where}: [{name}] is missing or not PUBLISHED; published_car reads it")
    ratios = pub[table].get("value")
    if not (isinstance(ratios, list) and len(ratios) >= 2 and pub[table].get("unit") == "1"
            and ratios[index] == min(ratios)):
        raise ValueError(f"{where}: [{table}] value {ratios!r} is not a ratio list whose top ratio is "
                         f"its entry {index}")
    row = pub["epa_test_car"]
    need = ("equivalent_test_weight_lb", "target_coef_a_lbf", "target_coef_b_lbf_per_mph",
            "target_coef_c_lbf_per_mph2", "axle_ratio", "n_over_v_rpm_per_mph")
    bad = [k for k in need if type(row.get(k)) not in (float, int)]
    if bad:
        raise ValueError(f"{where}: [epa_test_car] has no number for {bad}")
    top = ratios[index]
    out = dict(
        mass=row["equivalent_test_weight_lb"] * LB_KG,
        road_a_n=row["target_coef_a_lbf"] * LBF_N,
        road_b_n_per_mps=row["target_coef_b_lbf_per_mph"] * LBF_N / MPH_MPS,
        road_c_n_per_mps2=row["target_coef_c_lbf_per_mph2"] * LBF_N / MPH_MPS ** 2,
        road_rho_ref=EPA_REF_KPA * 1e3 / (R_AIR_ENV * EPA_REF_K),
        wheel_r=MPH_M_PER_MIN * top * row["axle_ratio"] / (2.0 * math.pi * row["n_over_v_rpm_per_mph"]))
    if not all(type(v) is float for v in out.values()):
        raise TypeError(f"{where}: published_car's values must be Python floats: {out!r}")
    return out


# The plants, by the name --engine takes: (engine spec, car spec). Decision 24's
# three EPA engines, each in its own car, were registered on 22 October 2026
# (build step 2 P6; docs/build_step_2/PLAN.md WP1 P6): their six specs are typed
# values only, and each stays NOT CALIBRATED until calibrate_epa.py has written its
# derived file and its freeze record (calibrated(); get() refuses it until then,
# naming the command). trainable() still names the B58 alone (decision 47).
PLANTS = {"b58": ("b58", "a90_supra"),
          "mazda_25t": ("mazda_25t", "cx9_2016"),
          "honda_l15b7": ("honda_l15b7", "accord_2018"),
          "ford_27tt": ("ford_27tt", "f150_2015")}
_BUILT = {}


def known():
    return sorted(PLANTS)


# THE PLANTS THAT MAY TRAIN OR BE SCORED (22 October 2026, decision 47). The EPA
# engines are refused by train.py, train_all.py, run_phase_d.py and evaluate.py
# (their --engine choices) until fingerprint schema 4 can record them and their
# validation is committed (results/VALIDATION_DECISIONS.md section H): schema 3's
# FATAL gears and final_drive cannot record the Accord's CVT, and an engine whose
# held-out validation has not run is not yet a plant a result may be quoted on.
def trainable():
    return ("b58",)


def calibrated(name):
    """Whether the plant called `name` can be built from its files: its derived
    file exists and, for an EPA engine (derived_set "epa"), its freeze record does
    (22 October 2026, build step 2 P5; amendment B7). fingerprint.py refuses an
    uncalibrated plant by name with it, instead of dying in derived.py."""
    return not _missing_files(_named(name, "engines.calibrated"))


def _missing_files(name):
    """The files the plant called `name` is built from that do not exist yet, as
    its engine spec names them, in the order they are needed: its derived file,
    then, for an EPA engine, its freeze record. [] for a calibrated plant. The one
    definition calibrated() and this module's listing both read (22 October 2026,
    build step 2 P6: the listing names what is missing; mistake 10)."""
    spec = PLANTS[_named(name, "engines._missing_files")][0]
    em = _top_level(spec, read_spec(spec), "engine", "derived_set", ENGINE_KEYS)
    files = [em["derived"]] + ([em["freeze"]] if "freeze" in em else [])
    return [f for f in files if not os.path.exists(os.path.join(HERE, f))]


def _named(name, who):
    """`name` if it is a registered plant's; a TypeError for no name at all."""
    if not isinstance(name, str):
        raise TypeError(f"{who} needs a plant name, one of {known()}; got {name!r}. "
                        "There is no default engine (CLAUDE.md mistake 1).")
    if name not in PLANTS:
        raise KeyError(f"no plant {name!r}; known: {known()}")
    return name


def get(name):
    """The plant called `name`. NO DEFAULT: an unnamed engine is mistake 1.

    Built once per process and shared; every record is frozen, so a caller that
    needs a variant (a swept c_turb, a perturbed constant) makes one with
    dataclasses.replace and never changes the plant other callers hold."""
    _named(name, "engines.get")
    if name not in _BUILT:
        _BUILT[name] = _build(*PLANTS[name])
    return _BUILT[name]


def _plain(v, where):
    """Refuse anything in a candidate's values that is not a dict of str keys, a
    list or tuple, or a Python float, int or str (amendment B10)."""
    if isinstance(v, dict):
        for k, x in v.items():
            if type(k) is not str:
                raise TypeError(f"build_candidate: key {k!r} under {where or 'the top'} is not a str")
            _plain(x, f"{where}.{k}" if where else k)
    elif type(v) in (list, tuple):
        for i, x in enumerate(v):
            _plain(x, f"{where}[{i}]")
    elif type(v) not in (float, int, str):
        raise TypeError(f"build_candidate: {where} is {v!r} ({type(v).__name__}), not a Python float, int or "
                        "str: amendment B10, NEP 50 makes the type load-bearing (convert a fit's NumPy "
                        "values with float() before they become a candidate, never after)")


def build_candidate(name, values):
    """The plant registered as `name` with its DERIVED fields taken from `values`,
    a dict shaped like its derived file ({section: {key: value}}, and the
    deliverable-torque table as a list of (rpm, Nm) pairs, [] while it is not yet
    measured): built by _build, the constructor get() uses, from the same specs and
    with the same converters, so it is exactly the plant get() will build once
    `values` is the file (22 October 2026, build step 2 P5; mistake 10). Every
    DERIVED field of the engine's set must be in `values`: there is no NaN for a
    candidate. Every value must be a Python float, int or str (amendment B10).

    Uncached and unregistered: each call builds a new plant, never stored in
    _BUILT, so get(name) is never the candidate; no freeze record is read, since a
    candidate is what a calibration evaluates before its freeze. Both arguments
    are required (mistake 1).

    A CANDIDATE IS NEVER FINGERPRINTED (22 October 2026, the review of P5). Its
    engine.derived still names the engine's derived file, which it was not built
    from, so a fingerprint would record that file's derived_sha beside the
    candidate's own engine_sha. Each candidate is marked (is_candidate) by an
    attribute that is not a field -- so equality, asdict and engine_sha are a
    plant's, and build_candidate("b58", the file's values) == get("b58") -- and that
    travels with a pickle to a worker; fingerprint.plant_fingerprint refuses a
    marked plant. A variant made from a candidate with dataclasses.replace is a new
    object and is not marked: never fingerprint one either."""
    _named(name, "engines.build_candidate")
    if not isinstance(values, dict):
        raise TypeError(f"build_candidate needs the candidate's DERIVED values as a dict shaped like the "
                        f"derived file, not {type(values).__name__}")
    # top-level "_" keys are bookkeeping, as in the derived file (fingerprint.derived_sha
    # drops them), and no record reads them: not checked
    _plain({k: v for k, v in values.items() if not (isinstance(k, str) and k.startswith("_"))}, "")
    plant = _build(*PLANTS[name], values=values)
    object.__setattr__(plant, "_candidate_of", name)      # the mark: not a field (Plant is frozen)
    return plant


def is_candidate(plant):
    """Whether `plant` was built by build_candidate (its mark): such a plant is
    never fingerprinted (22 October 2026, the review of P5). `plant` is required."""
    if not isinstance(plant, Plant):
        raise TypeError(f"engines.is_candidate needs an engines.Plant, not {type(plant).__name__}")
    return getattr(plant, "_candidate_of", None) is not None


_TYPED = {}


def typed_engine(name):
    """The TypedEngine of the plant called `name`: its geometry, cycle and charge
    records, and since 22 October 2026 (build step 2 P1) its fuel, from its spec
    alone, so it builds whether or not the derived file exists (build_dataset.py,
    new_drive.py; calibrate_thermal.load_drive reads the fuel). The same values as
    get(name).engine's records, read from the same file; no default name, as get."""
    _named(name, "engines.typed_engine")
    if name not in _TYPED:
        spec = PLANTS[name][0]
        e = read_spec(spec)
        # the engine's own DERIVED set says which fields need the file (22 October
        # 2026, build step 2 P5): an EPA engine's cycle record has some, so it has
        # no TypedEngine before its freeze, and is refused here by _record
        dset = _top_level(spec, e, "engine", "derived_set", ENGINE_KEYS)["derived_set"]
        _TYPED[name] = TypedEngine(
            id=e["_meta"]["id"],
            geometry=_record(Geometry, "geometry", e.get("geometry", {}), None, dset, {}),
            cycle=_record(CycleCal, "cycle", e.get("cycle", {}), None, dset, {}),
            charge=_record(ChargeCal, "charge", e.get("charge", {}), None, dset, {}),
            fuel=_record(Fuel, "fuel", e.get("fuel", {}), None, dset, {}))
    return _TYPED[name]


def with_fuel(engine, fuel):
    """`engine`, an Engine, burning `fuel`, a Fuel: the fuel record and the
    thermal record's copy of its heating value replaced in ONE dataclasses.replace,
    so Engine's check sees both moved together (22 October 2026, build step 2 P1).

    It is the only way to change an engine's heating value: a replace of either
    copy alone is refused by Engine. The validation contract's E6 row 3 moves
    the LHV in the cycle and in the network together (results/
    ENGINE_THRESHOLDS.md), and a calibration row runs on its own table's fuel
    (decision 69). Both arguments are required; there is no default fuel
    (mistake 1)."""
    if not isinstance(engine, Engine) or not isinstance(fuel, Fuel):
        raise TypeError(f"with_fuel needs an engines.Engine and an engines.Fuel; got "
                        f"{type(engine).__name__} and {type(fuel).__name__}. There is no default fuel "
                        "(CLAUDE.md mistake 1)")
    return replace(engine, fuel=fuel,
                   thermal=replace(engine.thermal, fuel_lhv_j_per_kg=fuel.lhv_j_per_kg))


def spec_files(name):
    """The typed files a plant is built from, relative to the repository: its
    engine spec and its car spec, and, for a car of a three-term kind, the
    published car file (engine_specs/cars/<car>.toml) its mass, wheel radius and
    road load are converted from (published_car; 22 October 2026, the review of
    build step 2 P5): an edit to that file moves those values, so plant_sha and
    git_dirty_plant_files must see it, as engine_sha does. The Supra's car
    (two_term_stepped) converts nothing and has no such file, so the B58's list is
    the two specs, as it was. The published file is hashed as a typed spec is
    (fingerprint._spec_values), and since its tables carry more than { value,
    label, source, unit }, its notes and sources are hashed with its values: it is
    never edited after commit A anyway (amendment B5)."""
    out = tuple(f"engine_specs/{s}.toml" for s in PLANTS[_named(name, "engines.spec_files")])
    car = PLANTS[name][1]
    cm = _top_level(car, read_spec(car), "car", "kind", CAR_KEYS)
    if "published" in cm:
        pub = cm["published"]
        full = pub if os.path.isabs(pub) else os.path.join(HERE, pub)
        out += (os.path.relpath(full, HERE).replace(os.sep, "/"),)
    return out


_IDS = {}


def name_of(plant):
    """The name (PLANTS) of the plant `plant` was built as: the one whose engine
    spec and car spec carry its engine.id and car.id. A variant made with
    dataclasses.replace keeps both ids, so it is named by the plant it was made
    from; a plant no registered pair of specs describes is refused, never
    matched to the nearest. fingerprint.plant_fingerprint hashes the specs this
    names (fingerprint.plant_files), not the B58's for every plant."""
    want = (plant.engine.id, plant.car.id)
    for n in known():
        if n not in _IDS:
            e, c = PLANTS[n]
            _IDS[n] = (read_spec(e)["_meta"]["id"], read_spec(c)["_meta"]["id"])
    found = [n for n in known() if _IDS[n] == want]
    if len(found) != 1:
        raise LookupError(f"plant {want[0]}/{want[1]} is " + (
            f"registered {len(found)} times: {found}" if found else
            f"not built from any registered pair of specs; known: {known()}") + " (engines.PLANTS)")
    return found[0]


def engine_sha(plant):
    """SHA-256 over every value of the plant AS BUILT -- typed, derived, the car and
    the scenario -- read from the live objects: the fingerprint's FATAL engine_sha.
    json writes a float as its repr, which round-trips the double exactly."""
    blob = json.dumps(asdict(plant), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


if __name__ == "__main__":
    # A REGISTERED PLANT WITHOUT ITS FILES IS LISTED, NOT BUILT (22 October 2026,
    # build step 2 P6): get() would stop the listing inside derived.py at the first
    # EPA engine, before its calibration has written its derived file. Such a plant
    # is named with the first file it lacks -- its derived file, or, once that
    # exists, its freeze record -- and its ids are read from its specs alone.
    for n in known():
        missing = _missing_files(n)
        if missing:
            e, c = PLANTS[n]
            print(f"{n:6s} {read_spec(e)['_meta']['id']}/{read_spec(c)['_meta']['id']}   "
                  f"not calibrated yet (no {missing[0]})")
            continue
        p = get(n)
        print(f"{n:6s} {p.id}   engine_sha {engine_sha(p)}   derived {p.engine.derived}")
