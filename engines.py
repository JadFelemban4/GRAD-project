"""engines.py -- the plants this project simulates: every engine- and car-specific
constant, one frozen record per engine and one per car, and no default engine.

    import engines
    plant = engines.get("b58")          # Plant(engine, car, scenario)
    plant.id                            # 'b58b30o1/a90-supra-zf8hp51'
    engines.engine_sha(plant)           # SHA-256 of every value, as built
    engines.name_of(plant)              # 'b58', the name it was built under
    engines.typed_engine("b58")         # geometry, cycle, charge: no derived file read

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
            (derived.engine_path). DERIVED_FIELDS names each one and where it is
            read from.
  code      the model's form and the physics true of any petrol engine --
            Woschni's constants, gamma(T), the fuel's heating value, the knock
            criterion KI = 1 -- stay in plant.py and thermal.py.

VALUES THE REFERENCE READ AT CALL TIME ARE READ HERE ONCE, when the plant is
built: SPARK_A, ENR_DWELL_LO/HI, the boost envelope and its cap, the
deliverable-torque table. derived.py caches its file per process, so the values
are the ones a call would have read; a re-derivation reaches a process that
builds its plant after it, as before.

THE B58, BUILT HERE, IS THE PLANT OF cf43fbb. Every expression in plant.py,
thermal.py and engine_env.py keeps its operations in their old order with the
literal replaced by the record's field, so the numbers are the same doubles;
the identity harness of build step 1 compared the two trees byte for byte.
"""
import hashlib
import json
import math
import os
import tomllib
from dataclasses import MISSING, asdict, dataclass, fields

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


@_required
@dataclass(frozen=True)
class CycleCal:
    """The 0-D cycle model's per-engine constants (plant.run_cycle): breathing,
    residual gas, wall and charge temperatures, burn, knock, friction, the port
    and the exhaust backpressure, and the fuel's octane."""
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


@_required
@dataclass(frozen=True)
class EcuCal:
    """engine_env.BaselineECU: spark map and knock limit, enrichment, compensations,
    knock feedback and the fan schedule."""
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


@_required
@dataclass(frozen=True)
class TypedEngine:
    """The engine's records that hold no DERIVED field -- its geometry, the cycle
    model's constants and the charge temperature's -- built from its spec alone
    (typed_engine), without its derived file.

    For what has to run before that file exists. build_dataset.py inverts the
    logged air mass through plant.map_from_airflow and plant.charge_temperature,
    which read these three records only, to write the master tables the derived
    file is made FROM; on cf43fbb it ran with no derived file, and engines.get,
    which builds every record, refused it (the review of 21 October 2026).
    Anything that reads a DERIVED record -- the boost envelope, the thermal
    network, the ECU's spark offset -- needs the whole plant, engines.get."""
    id: str
    geometry: Geometry
    cycle: CycleCal
    charge: ChargeCal


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
    car: Car
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
                         "from the engine's derived file (engines.DERIVED_FIELDS)")
    if label not in LABELS:
        raise ValueError(f"{where}: label {label!r} is not one of {sorted(LABELS)}")
    src = entry.get("source")
    if not isinstance(src, str) or not src.strip():
        raise ValueError(f"{where}: no source. A typed value says where it comes from, or why it is assumed")
    v = entry["value"]
    return tuple(v) if isinstance(v, list) else v


# Every DERIVED field: (record, field) -> (section, key) in the engine's derived
# file, key None for a whole section. The B58's file is written by
# derive_params.py; a later engine's by its own calibration (not yet written).
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


def _derived_value(path, record, field):
    """One DERIVED field, converted as the code that used to read it converted it."""
    section, key = DERIVED_FIELDS[(record, field)]
    v = derived.get(section, key, path=path)
    if record == "car":              # Vehicle.DELIVERABLE_TORQUE's conversion
        if v is None:                # only while derive_params.py builds the file
            return ()
        return tuple((int(a), float(b)) for a, b in v)
    if field in ("envelope_flow", "envelope_pr"):
        if isinstance(v, float) and math.isnan(v):
            return ()
        return tuple(float(x) for x in v)
    return float(v)


def _record(cls, record, typed, path):
    """A record from its typed section and its DERIVED fields. A field may come
    from one of the two, never both, and none may be missing. `path` None builds
    a record with no DERIVED field only (typed_engine): one that has one is
    refused, never given NaN."""
    want = [f.name for f in fields(cls)]
    unknown = set(typed) - set(want)
    if unknown:
        raise ValueError(f"[{record}] has fields {cls.__name__} does not: {sorted(unknown)}")
    kw = {}
    for name in want:
        is_derived = (record, name) in DERIVED_FIELDS
        if is_derived and name in typed:
            raise ValueError(f"[{record}] {name} is DERIVED and must not be typed")
        if is_derived and path is None:
            raise ValueError(f"[{record}] {name} is DERIVED: it is read from the engine's derived "
                             "file, so this record needs engines.get, not typed_engine")
        if is_derived:
            kw[name] = _derived_value(path, record, name)
        elif name in typed:
            kw[name] = typed[name]
        else:
            raise ValueError(f"[{record}] {name} is missing: neither typed nor DERIVED")
    return cls(**kw)


def _build(engine_spec, car_spec):
    e, c = read_spec(engine_spec), read_spec(car_spec)
    path = os.path.join(HERE, e["_meta"]["derived"])
    engine = Engine(
        id=e["_meta"]["id"], derived=e["_meta"]["derived"],
        geometry=_record(Geometry, "geometry", e.get("geometry", {}), path),
        cycle=_record(CycleCal, "cycle", e.get("cycle", {}), path),
        charge=_record(ChargeCal, "charge", e.get("charge", {}), path),
        boost=_record(BoostCal, "boost", e.get("boost", {}), path),
        ecu=_record(EcuCal, "ecu", e.get("ecu", {}), path),
        thermal=_record(ThermalParams, "thermal", e.get("thermal", {}), path),
        damage=_record(DamageCal, "damage", e.get("damage", {}), path),
        loop=_record(LoopCal, "loop", e.get("loop", {}), path))
    car = _record(Car, "car", dict(c.get("car", {}), id=c["_meta"]["id"]), path)
    scenario = _record(Scenario, "scenario", c.get("scenario", {}), path)
    return Plant(engine=engine, car=car, scenario=scenario)


# The plants, by the name --engine takes: (engine spec, car spec). Decision 24
# adds three more engines, each in its own car, in a later build step.
PLANTS = {"b58": ("b58", "a90_supra")}
_BUILT = {}


def known():
    return sorted(PLANTS)


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


_TYPED = {}


def typed_engine(name):
    """The TypedEngine of the plant called `name`: its geometry, cycle and charge
    records from its spec alone, so it builds whether or not the derived file
    exists (build_dataset.py, new_drive.py). The same values as get(name).engine's
    records, read from the same file; no default name, as get."""
    _named(name, "engines.typed_engine")
    if name not in _TYPED:
        e = read_spec(PLANTS[name][0])
        _TYPED[name] = TypedEngine(
            id=e["_meta"]["id"],
            geometry=_record(Geometry, "geometry", e.get("geometry", {}), None),
            cycle=_record(CycleCal, "cycle", e.get("cycle", {}), None),
            charge=_record(ChargeCal, "charge", e.get("charge", {}), None))
    return _TYPED[name]


def spec_files(name):
    """The typed files a plant is built from, relative to the repository."""
    return tuple(f"engine_specs/{s}.toml" for s in PLANTS[_named(name, "engines.spec_files")])


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
    for n in known():
        p = get(n)
        print(f"{n:6s} {p.id}   engine_sha {engine_sha(p)}   derived {p.engine.derived}")
