"""test_carried.py -- every typed value of the six EPA specs against its registry: what is carried from the B58, bit for bit; the rest, as its own source gives it.

    python test_carried.py        a few seconds; exit code 0 when all pass

Build step 2 of decision 24, P6 (22 October 2026; docs/build_step_2/PLAN.md WP1 P6,
sections 7.5 and 9.2, as amendment F12 of docs/build_step_2/AMENDMENTS.md completes
them; decisions 43-46 and 69, results/VALIDATION_DECISIONS.md section H). The three
EPA engines are registered (engines.PLANTS) with six specs of typed values only.
Whatever EPA's rigs cannot set -- the thermal network, the ECU's compensations, its
knock feedback, the fan, the turbine housing, the constants the validation contract
shares between engines -- is the B58's, carried (decision 45): its source starts
"CARRIED FROM THE B58: " and names where the B58's value lives. Amendment F12 found
the plan's list of those values incomplete (the warm starts, the Wiebe and
Douaud-Eyzat constants missing), so REGISTRY below names EVERY typed field of each
spec, its label, and either the B58 field it is carried from or the value its own
source gives, with that source's arithmetic.

What this file does not read: no EPA table, no ALPHA curve, and not the validation
contract. The contract's values a spec types (the lambda floor, the fuel per table,
the calibration lines' ends) are pinned below with the key they come from, because
amendment C4 confines reading the contract to epa_rows.calibration_contract and the
validation's own scripts (WP3); a cross-check through that accessor belongs there.
The published car files are read, as engines.published_car reads them.

  Complete   each spec types exactly its registry's fields: one more (a DERIVED one
             among them) or one fewer fails (amendment F12)
  Labels     each field carries the registry's label
  Carried    a carried field's source starts with the marker and cites exactly the
             registry's B58 field, and its value is the B58's -- type and bits -- both
             as the B58's file holds it and as engines.get("b58") built it (the
             network's fifteen and the two dwells from the B58's derived file,
             derived_sha 326c0835548975e2)
  Own        an own field carries no marker, and its value is the registry's, type
             and bits: the PUBLISHED geometry; the Mazda's stroke from EPA's 2.488 L
             and 89 mm (DERIVED_ONCE); the conrod at the B58's ratio; the fuel per
             engine, the Ford's HD1's (decision 69); lam_floor, the contract's floor;
             the two loop gains scaled by displacement (decision 46); n_turbines,
             UNVERIFIED; the cars' published ratios and peak torques (decision 43:
             the CX-9's from Mazda's MZ19 sheet, 310 lb-ft); the calibration lines'
             ends (amendment C13)
  Types      every scalar is the Python type of its record field's annotation, a
             float field a float (amendment B10)
  TopLevel   each spec's top-level keys: the EPA set, the derived file where
             derived.engine_path puts it, the freeze record, the car's kind and its
             published file, and that file's engine
  Controls   (mistake 12) one ulp on a carried value; the B58's value moved instead;
             the marker dropped, added to an own value, or citing another field; a
             DERIVED field typed; a field left out; a label changed; a float field
             written as an int; an own value moved: each fails with its own message
"""
import copy
import math
import os
import re
import sys
import tomllib
import unittest
from dataclasses import fields, replace

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import derived  # noqa: E402
import engines  # noqa: E402

MARK = "CARRIED FROM THE B58: "
B58_SPEC, SUPRA_SPEC = "engine_specs/b58.toml", "engine_specs/a90_supra.toml"
B58_DERIVED = os.path.relpath(derived.B58_PATH, HERE).replace(os.sep, "/")    # the B58's derived file
EPA = ("mazda_25t", "honda_l15b7", "ford_27tt")
CAR_SPEC = {"mazda_25t": "cx9_2016", "honda_l15b7": "accord_2018", "ford_27tt": "f150_2015"}

# 1 lbf ft in N m: 4.4482216152605 N x 0.3048 m, both exact by definition (the
# README of engine_specs/cars/, "Deriving what the model needs").
NM_PER_LBF_FT = 4.4482216152605 * 0.3048
# The Mazda's stroke, DERIVED_ONCE on 22 October 2026 from EPA's displacement and
# bore (epa_engine.json displacement_l 2.488, n_cylinders 4, bore_mm 89): EPA
# asserts no stroke (PLAN.md 9.2). The expression its spec's source states.
MAZDA_STROKE = 2.488e-3 / (4 * (math.pi * 0.089 ** 2 / 4.0))

# The record each spec section builds (the annotation of each field is its type).
ENGINE_RECORDS = {"geometry": engines.Geometry, "cycle": engines.CycleCal, "charge": engines.ChargeCal,
                  "boost": engines.BoostCal, "ecu": engines.EcuCal, "thermal": engines.ThermalParams,
                  "damage": engines.DamageCal, "loop": engines.LoopCal, "fuel": engines.Fuel}


def carried(label, cite=None):
    """A field carried from the B58: its label here, and the B58 field its marker
    must cite, (file, section, field) -- None for the same section and field of the
    B58's engine spec, or of the Supra's car spec for a car spec's field."""
    return ("carried", label, cite)


def own(label, value):
    """A field this spec's own source sets: its label, and its value."""
    return ("own", label, value)


# ---------------------------------------------------------------- the registry
# CARRIED, the same in the three engine specs: the B58's typed values, by their label
# here (ASSUMED for an estimate or a fit of the B58's own; CORRELATION for a
# correlation's constant; DESIGN for a choice that defines the experiment), and the
# B58's DERIVED values that the EPA set does not derive (the network's fifteen, the
# two dwells; PLAN.md 9.2).
CARRIED_ENGINE = {}
for _sec, _label, _names in (
        ("geometry", "ASSUMED", ("ivc_deg", "evo_deg")),
        ("cycle", "ASSUMED", ("fres_a", "fres_b", "fres_map_min", "fres_lo", "fres_hi", "t_head_k", "port_pickup_k",
                              "t_residual_k", "flame_lam", "flame_width", "flame_floor", "burn_res", "delay_res",
                              "n_poly", "cp_exh")),
        ("cycle", "CORRELATION", ("wiebe_a", "wiebe_m", "knock_on", "knock_p", "knock_b")),
        ("charge", "ASSUMED", ("rise_k", "block_coupling")),
        ("boost", "ASSUMED", ("inlet_sea_kpa",)),
        ("ecu", "ASSUMED", ("iat_gain", "iat_ref_c", "iat_max", "cold_k", "cold_retard", "knock_step", "knock_max",
                            "knock_restore", "knock_detect_ki", "fan_hi_k", "fan_lo_k", "fan_lo_duty")),
        ("ecu", "DESIGN", ("spark_ref_kpa", "lam_ceiling")),
        ("thermal", "ASSUMED", ("c_turb", "ua_turb_amb", "ua_gas_turb")),
        ("thermal", "DESIGN", ("t_block_warm", "t_oil_warm", "t_turb_warm")),
        ("damage", "DESIGN", ("turb_scale_k", "oil_knee_k", "oil_scale_k", "oil_weight", "ki_knee", "ki_weight")),
        ("damage", "ASSUMED", ("egt_limit_k",)),
        ("loop", "DESIGN", ("ff_offset_kpa", "map_floor_kpa", "i_gain", "i_clip", "i_out"))):
    for _n in _names:
        CARRIED_ENGINE[(_sec, _n)] = carried(_label)
for _n in ("c_block", "c_oil", "ua_block_oil", "ua_block_amb", "ua_oil_amb", "ua_oil_ram", "ua_rad_min", "ua_rad_ram",
           "ua_rad_fan", "t_stat_open", "t_stat_span", "frac_fuel_to_coolant", "frac_fuel_to_oil", "k_oil_rpm",
           "n_oil_rpm"):
    CARRIED_ENGINE[("thermal", _n)] = carried("ASSUMED", (B58_DERIVED, "thermal", _n))
CARRIED_ENGINE[("ecu", "enr_dwell_lo")] = carried("ASSUMED", (B58_DERIVED, "enrichment", "ENR_DWELL_LO"))
CARRIED_ENGINE[("ecu", "enr_dwell_hi")] = carried("ASSUMED", (B58_DERIVED, "enrichment", "ENR_DWELL_HI"))

# OWN, per engine: (bore, stroke and its label, n_cyl, comp_ratio, octane and its
# label, lam_floor, n_turbines, LHV, AFR_st). Each with the file and key it comes
# from in the spec's source: the geometry and the octane from epa_engine.json's
# non-curve fields (the Ford's octane FTAG 26864's, decision 69; the Honda's from
# CATALOGUE.md, ASSUMED, PLAN.md 9.2); lam_floor results/ENGINE_THRESHOLDS.json
# engines.<id>.lambda_clip_floor.floor, the fuel its fuel_by_table (contract
# version 3); n_turbines PLAN.md 9.2, UNVERIFIED.
OWN_ENGINE = {
    "mazda_25t": (0.0890, (MAZDA_STROKE, "DERIVED_ONCE"), 4, 10.5, (97.6, "PUBLISHED"), 0.684, 1, 42.908e6, 14.559),
    "honda_l15b7": (0.0730, (0.0894, "PUBLISHED"), 4, 10.6, (96.1, "ASSUMED"), 0.61, 1, 42.898e6, 14.554),
    "ford_27tt": (0.0830, (0.0830, "PUBLISHED"), 6, 10.0, (97.6, "PUBLISHED"), 0.698, 2, 42.908e6, 14.559),
}

# The calibration lines' ends, rpm (results/ENGINE_THRESHOLDS.json engines.<id>.lines,
# contract version 3, whose end lines are never held out: amendment C13).
LINE_ENDS = {"mazda_25t": (1300.0, 5000.0), "honda_l15b7": (1000.0, 5000.0), "ford_27tt": (1000.0, 5500.0)}

# The peak torques the stepped cars type, in lbf ft as the sources print them
# (decision 43: the CX-9's from Mazda's MZ19 sheet, opened 22 October 2026; the
# F-150's from Ford's sheet, PLAN.md 7.5), and the sha256 of the MZ19 PDF opened.
PEAK_LBF_FT = {"mazda_25t": 310.0, "ford_27tt": 375.0}
MZ19_SHA256 = "aa0c19ad21248f1c17c72be13248ff2179fa8c393ea0ac95e194b36a296c45fb"


def raw(spec):
    """engine_specs/<spec>.toml as tomllib reads it: every entry with its label and
    its source (engines.read_spec keeps the values only)."""
    with open(os.path.join(engines.SPECS, spec + ".toml"), "rb") as fh:
        return tomllib.load(fh)


def published(name):
    """The published car file an EPA plant's car spec names (engines.published_car's)."""
    path = raw(CAR_SPEC[name])["published"]
    with open(os.path.join(HERE, path), "rb") as fh:
        return tomllib.load(fh)


def engine_registry(name, b58_raw):
    """Every typed field of the engine spec `name`: CARRIED_ENGINE and its own."""
    bore, (stroke, stroke_label), n_cyl, cr, (octane, octane_label), lam_floor, n_turb, lhv, afr = OWN_ENGINE[name]
    bg = b58_raw["geometry"]
    # the conrod at the B58's rod-to-stroke ratio, and the loop gains x V_d,B58 / V_d,
    # each displacement as engines.Geometry computes it (vd_total): the expressions the
    # specs' sources state (PLAN.md 9.2; decision 46)
    conrod = stroke * (bg["conrod"]["value"] / bg["stroke"]["value"])

    def geometry(g):
        return engines.Geometry(**{k: v["value"] for k, v in g.items()})
    me = geometry({"bore": {"value": bore}, "stroke": {"value": stroke}, "conrod": {"value": conrod},
                   "n_cyl": {"value": n_cyl}, "comp_ratio": {"value": cr}, "ivc_deg": bg["ivc_deg"],
                   "evo_deg": bg["evo_deg"]})
    ratio = geometry(bg).vd_total / me.vd_total
    reg = dict(CARRIED_ENGINE)
    reg.update({
        ("geometry", "bore"): own("PUBLISHED", bore),
        ("geometry", "stroke"): own(stroke_label, stroke),
        ("geometry", "conrod"): own("ASSUMED", conrod),
        ("geometry", "n_cyl"): own("PUBLISHED", n_cyl),
        ("geometry", "comp_ratio"): own("PUBLISHED", cr),
        ("cycle", "ve_lo"): own("DESIGN", 0.30),
        ("cycle", "ve_hi"): own("DESIGN", 1.30),
        ("cycle", "octane"): own(octane_label, octane),
        ("cycle", "ve_map_ref_kpa"): own("DESIGN", 100.0),
        ("cycle", "cam_ref_deg"): own("DESIGN", 0.0),
        ("ecu", "lam_floor"): own("DERIVED_ONCE", lam_floor),
        ("thermal", "n_turbines"): own("ASSUMED", n_turb),
        ("loop", "ff_kpa_per_nm"): own("DESIGN", b58_raw["loop"]["ff_kpa_per_nm"]["value"] * ratio),
        ("loop", "p_gain"): own("DESIGN", b58_raw["loop"]["p_gain"]["value"] * ratio),
        ("fuel", "lhv_j_per_kg"): own("PUBLISHED", lhv),
        ("fuel", "afr_st"): own("DERIVED_ONCE", afr),
    })
    return reg


def car_registry(name):
    """Every typed field of the car spec of the plant `name`."""
    pub = published(name)
    lo, hi = LINE_ENDS[name]
    reg = {("car", "driveline_eff"): carried("ASSUMED"), ("car", "table_t_amb"): carried("DESIGN"),
           ("car", "table_t_block"): carried("ASSUMED"), ("car", "table_settle"): carried("ASSUMED"),
           ("scenario", "grade"): carried("DESIGN"), ("scenario", "v_kmh"): carried("DESIGN"),
           ("scenario", "t_amb"): carried("DESIGN"),
           ("car", "final_drive"): own("PUBLISHED", pub["final_drive"]["value"]),
           ("car", "rpm_min"): own("DESIGN", lo), ("car", "rpm_max"): own("DESIGN", hi),
           ("car", "table_rpm_lo"): own("DESIGN", int(lo)), ("car", "table_rpm_hi"): own("DESIGN", int(hi)),
           ("car", "table_rpm_step"): own("DESIGN", 100)}
    if name == "honda_l15b7":                     # the CVT (decision 40, law (b))
        low, top = pub["cvt_ratio_range"]["value"]
        reg.update({("car", "ratio_low_gear"): own("PUBLISHED", low), ("car", "ratio_top_gear"): own("PUBLISHED", top),
                    ("car", "kickdown_load"): carried("ASSUMED", (SUPRA_SPEC, "car", "shift_load")),
                    ("car", "target_load"): own("DESIGN", 0.65), ("car", "cvt_rpm_min"): own("DESIGN", lo)})
    else:                                         # a stepped box
        reg.update({("car", "gears"): own("PUBLISHED", tuple(pub["gear_ratios"]["value"])),
                    ("car", "peak_torque_nm"): own("PUBLISHED", PEAK_LBF_FT[name] * NM_PER_LBF_FT),
                    ("car", "shift_load"): carried("ASSUMED"), ("car", "upshift_min_rpm"): carried("ASSUMED"),
                    ("car", "shift_rpm_max"): own("DESIGN", hi)})
    return reg


def same(a, b):
    """The same Python value, type and bits: a float by its repr, which round-trips
    the double (and tells -0.0 from 0.0); a list or tuple element by element."""
    if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
        return (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b)
                and all(same(x, y) for x, y in zip(a, b)))
    return type(a) is type(b) and repr(a) == repr(b)


class B58:
    """The B58's side of every carried value: its two typed specs as files, its
    derived file, and `plant`, the plant engines.get("b58") built from them, or a
    variant of it (the control that moves the B58's value instead of the EPA
    spec's). Both arguments are required: no default plant (mistake 1; the scan of
    test_engine_threading.py holds a test to it too)."""

    def __init__(self, plant, b58_spec):
        self.plant = plant
        self.files = {B58_SPEC: b58_spec, SUPRA_SPEC: raw("a90_supra")}
        self.derived = derived.all_params(path=derived.B58_PATH)
        self.from_derived = {v: k for k, v in engines.DERIVED_FIELDS.items()}     # (section, key) -> (record, field)

    def value(self, cite):
        """The B58's value at `cite`, in its file, and as the plant built it."""
        path, sec, key = cite
        if path == B58_DERIVED:
            rec, f = self.from_derived[(sec, key)]
            return self.derived[sec][key], getattr(getattr(self.plant.engine, rec), f)
        entry = self.files[path][sec][key]["value"]
        holder = (getattr(self.plant.engine, sec) if path == B58_SPEC
                  else self.plant.car if sec == "car" else self.plant.scenario)
        return entry, getattr(holder, key)


def the_b58():
    """The B58 as it is: engines.get("b58") and engine_specs/b58.toml."""
    return B58(engines.get("b58"), raw("b58"))


CITE = re.compile(r"CARRIED FROM THE B58: (\S+?\.(?:toml|json)) (?:\[(\w+)\] (\w+)|(\w+)\.(\w+))(?![\w.])")


def cite_of(source):
    """The (file, section, field) a marker cites, or None if it names none."""
    m = CITE.match(source)
    if m is None:
        return None
    return (m.group(1), m.group(2) or m.group(4), m.group(3) or m.group(5))


def problems(spec, raw_spec, registry, records, b58):
    """Every way the spec `spec` (as tomllib read it, `raw_spec`) departs from its
    `registry`, its record types (`records`, section -> dataclass) and the B58 (`b58`)."""
    out = []
    typed = {(sec, f): e for sec, d in raw_spec.items() if isinstance(d, dict) for f, e in d.items()}
    for key in sorted(set(registry) - set(typed)):
        out.append(f"{spec}: [{key[0]}] {key[1]} is in the registry and not typed")
    for key in sorted(set(typed) - set(registry)):
        out.append(f"{spec}: [{key[0]}] {key[1]} is typed and not in the registry")
    annot = {(sec, f.name): f.type for sec, cls in records.items() for f in fields(cls)}
    for key in sorted(set(typed) & set(registry)):
        e, (kind, label, want) = typed[key], registry[key]
        where = f"{spec}: [{key[0]}] {key[1]}"
        v, src = e.get("value"), e.get("source", "")
        if e.get("label") != label:
            out.append(f"{where}: label {e.get('label')!r}, the registry's {label!r}")
        t = annot.get(key)
        if t is tuple:
            if not (type(v) is list and v and all(type(x) is float for x in v)):
                out.append(f"{where}: {v!r} is not a list of Python floats (amendment B10)")
        elif t not in (float, int, str) or type(v) is not t:
            out.append(f"{where}: {v!r} is a {type(v).__name__}, the record's annotation {t!r} (amendment B10)")
        if kind == "carried":
            cite = want or ((B58_SPEC if key[0] not in ("car", "scenario") else SUPRA_SPEC),) + key
            if not src.startswith(MARK):
                out.append(f"{where}: carried, and its source does not start {MARK!r}")
            elif cite_of(src) != cite:
                out.append(f"{where}: its marker cites {cite_of(src)}, the registry's {cite}")
            in_file, built = b58.value(cite)
            if not (same(v, in_file) and same(v, built)):
                out.append(f"{where}: {v!r} is not the B58's: {in_file!r} in {cite[0]}, {built!r} as built")
        else:
            if MARK.strip() in src:
                out.append(f"{where}: its own value, and its source carries the marker")
            if not same(tuple(v) if type(v) is list else v, want):
                out.append(f"{where}: {v!r}, the registry's {want!r}")
    return out


def engine_problems(name, raw_spec=None, b58=None):
    b58 = the_b58() if b58 is None else b58
    rs = raw(name) if raw_spec is None else raw_spec
    return problems(name, rs, engine_registry(name, b58.files[B58_SPEC]), ENGINE_RECORDS, b58)


def car_problems(name, raw_spec=None, b58=None):
    b58 = the_b58() if b58 is None else b58
    rs = raw(CAR_SPEC[name]) if raw_spec is None else raw_spec
    records = {"car": engines.CAR_KINDS[rs["kind"]], "scenario": engines.Scenario}
    return problems(CAR_SPEC[name], rs, car_registry(name), records, b58)


class Registry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.b58 = the_b58()

    def test_the_three_are_registered_with_their_specs(self):
        self.assertEqual({n: engines.PLANTS[n] for n in EPA}, {n: (n, CAR_SPEC[n]) for n in EPA})

    def test_every_engine_spec_is_its_registry(self):
        print()
        for name in EPA:
            with self.subTest(spec=name):
                self.assertEqual(engine_problems(name, b58=self.b58), [])
                reg = engine_registry(name, self.b58.files[B58_SPEC])
                n_car = sum(1 for k in reg.values() if k[0] == "carried")
                n_der = sum(1 for k in reg.values() if k[0] == "carried" and k[2] and k[2][0] == B58_DERIVED)
                print(f"  {name:12s} {len(reg)} typed: {n_car} carried from the B58 ({n_der} from its derived "
                      f"file), {len(reg) - n_car} its own")

    def test_every_car_spec_is_its_registry(self):
        print()
        for name in EPA:
            with self.subTest(spec=CAR_SPEC[name]):
                self.assertEqual(car_problems(name, b58=self.b58), [])
                reg = car_registry(name)
                n_car = sum(1 for k in reg.values() if k[0] == "carried")
                print(f"  {CAR_SPEC[name]:12s} {len(reg)} typed: {n_car} carried from the Supra, "
                      f"{len(reg) - n_car} its own")

    def test_no_derived_field_is_carried_or_typed(self):
        """The registry carries none of the EPA set's DERIVED fields, and the B58's
        DERIVED values it carries are the ones that set does not derive."""
        engine_derived = {k for k in engines.EPA_DERIVED_FIELDS if k[0] != "car"}
        for name in EPA:
            reg = engine_registry(name, self.b58.files[B58_SPEC])
            self.assertEqual(set(reg) & set(engines.EPA_DERIVED_FIELDS), set())
            # with the copy of the LHV (never typed), the registry and the EPA set's
            # DERIVED fields are every field of every engine record, each once
            every = {(sec, f.name) for sec, cls in ENGINE_RECORDS.items() for f in fields(cls)}
            self.assertEqual(set(reg) | engine_derived | {("thermal", "fuel_lhv_j_per_kg")}, every)
            # and a car's: typed, converted from its published file, its id, its table
            meta = engines.read_spec(CAR_SPEC[name])["_meta"]
            cls = engines.CAR_KINDS[meta["kind"]]
            conv = engines.published_car(meta["published"], meta["kind"])
            car = {k[1] for k in car_registry(name) if k[0] == "car"}
            self.assertEqual(car & set(conv), set())
            self.assertEqual(car | set(conv) | {"id", "deliverable_torque"}, {f.name for f in fields(cls)})
            self.assertEqual({k[1] for k in car_registry(name) if k[0] == "scenario"},
                             {f.name for f in fields(engines.Scenario)})

    def test_the_b58s_own_specs_carry_no_marker(self):
        for spec in ("b58", "a90_supra"):
            for sec, d in raw(spec).items():
                if isinstance(d, dict):
                    for f, e in d.items():
                        self.assertNotIn(MARK.strip(), e.get("source", ""), f"{spec} [{sec}] {f}")

    def test_the_sources_say_what_the_plan_asks(self):
        """n_turbines is UNVERIFIED (PLAN.md 9.2); the Mazda's stroke states its
        arithmetic; the CX-9's peak torque names MZ19, its 310 lb-ft and the hash of
        the PDF opened (decision 43); lam_floor names the contract's key."""
        for name in EPA:
            e = raw(name)
            self.assertIn("UNVERIFIED", e["thermal"]["n_turbines"]["source"], name)
            self.assertIn(f"engines.{name}.lambda_clip_floor.floor", e["ecu"]["lam_floor"]["source"], name)
        self.assertIn("2.488e-3 / (4 x (pi x 0.089^2 / 4))", raw("mazda_25t")["geometry"]["stroke"]["source"])
        src = raw("cx9_2016")["car"]["peak_torque_nm"]["source"]
        for want in ("310 lb-ft @ 2,000 rpm", "MZ19", MZ19_SHA256):
            self.assertIn(want, src)


class TopLevel(unittest.TestCase):
    def test_the_engine_specs_top_level_keys(self):
        for name in EPA:
            with self.subTest(spec=name):
                meta = engines.read_spec(name)["_meta"]
                self.assertEqual(meta, {
                    "id": name, "derived_set": "epa",
                    "derived": os.path.relpath(derived.engine_path(name), HERE).replace(os.sep, "/"),
                    "freeze": f"results/EPA_CALIBRATION/{name}/freeze.json"})

    def test_the_car_specs_top_level_keys(self):
        kinds = {"mazda_25t": "three_term_stepped", "honda_l15b7": "three_term_cvt", "ford_27tt": "three_term_stepped"}
        for name in EPA:
            with self.subTest(spec=CAR_SPEC[name]):
                meta = engines.read_spec(CAR_SPEC[name])["_meta"]
                pub = published(name)
                self.assertEqual(meta, {"id": pub["car_id"], "kind": kinds[name],
                                        "published": f"engine_specs/cars/{pub['car_id']}.toml"})
                self.assertEqual(pub["engine_id"], name)

    def test_the_relations_between_the_typed_values(self):
        """What PLAN.md 7.5 ties together: the shift bar is rpm_max, the table's grid
        runs rpm_min to rpm_max, the CVT's floor is rpm_min, the table's ambient is
        the climb's."""
        for name in EPA:
            c = engines.read_spec(CAR_SPEC[name])
            car, sc = c["car"], c["scenario"]
            with self.subTest(spec=CAR_SPEC[name]):
                self.assertEqual((car["table_rpm_lo"], car["table_rpm_hi"]), (int(car["rpm_min"]), int(car["rpm_max"])))
                self.assertEqual(car["table_t_amb"], sc["t_amb"])
                self.assertEqual(car.get("shift_rpm_max", car["rpm_max"]), car["rpm_max"])
                self.assertEqual(car.get("cvt_rpm_min", car["rpm_min"]), car["rpm_min"])


class Controls(unittest.TestCase):
    """Mistake 12: each check above must be able to fail, for its own reason."""

    @classmethod
    def setUpClass(cls):
        cls.b58 = the_b58()

    def mutated(self, spec, change):
        r = copy.deepcopy(raw(spec))
        change(r)
        return r

    def assertFlags(self, got, *wants):
        self.assertTrue(got, "the control flagged nothing")
        for w in wants:
            self.assertTrue(any(w in g for g in got), f"no problem says {w!r}: {got}")

    def test_one_ulp_on_a_carried_value(self):
        r = self.mutated("honda_l15b7", lambda r: r["cycle"]["fres_a"].update(value=math.nextafter(0.035, 1.0)))
        self.assertFlags(engine_problems("honda_l15b7", r, self.b58), "[cycle] fres_a", "is not the B58's")
        r = self.mutated("mazda_25t", lambda r: r["thermal"]["c_block"].update(
            value=math.nextafter(r["thermal"]["c_block"]["value"], 0.0)))
        self.assertFlags(engine_problems("mazda_25t", r, self.b58), "[thermal] c_block", "is not the B58's")

    def test_the_b58s_value_moved_instead(self):
        """The check reads the live B58: its plant with one ulp on c_turb, or its
        spec file with one ulp on the Supra's driveline efficiency, flags the EPA
        spec that still holds the old value."""
        p = self.b58.plant
        moved = replace(p, engine=replace(p.engine, thermal=replace(p.engine.thermal, c_turb=math.nextafter(6000.0, 1e9))))
        self.assertFlags(engine_problems("ford_27tt", b58=B58(moved, raw("b58"))), "[thermal] c_turb", "as built")
        b = the_b58()
        b.files[SUPRA_SPEC] = copy.deepcopy(b.files[SUPRA_SPEC])
        b.files[SUPRA_SPEC]["car"]["driveline_eff"]["value"] = math.nextafter(0.92, 1.0)
        self.assertFlags(car_problems("mazda_25t", b58=b), "[car] driveline_eff", "is not the B58's")

    def test_the_marker_dropped_added_or_citing_another_field(self):
        r = self.mutated("mazda_25t", lambda r: r["ecu"]["iat_gain"].update(
            source=r["ecu"]["iat_gain"]["source"].replace(MARK, "the B58's: ")))
        self.assertFlags(engine_problems("mazda_25t", r, self.b58), "[ecu] iat_gain", "does not start")
        r = self.mutated("mazda_25t", lambda r: r["ecu"]["lam_floor"].update(
            source=MARK + r["ecu"]["lam_floor"]["source"]))
        self.assertFlags(engine_problems("mazda_25t", r, self.b58), "[ecu] lam_floor", "carries the marker")
        r = self.mutated("mazda_25t", lambda r: r["cycle"]["fres_lo"].update(
            source=r["cycle"]["fres_lo"]["source"].replace("[cycle] fres_lo", "[cycle] fres_hi")))
        self.assertFlags(engine_problems("mazda_25t", r, self.b58), "[cycle] fres_lo", "its marker cites")
        r = self.mutated("accord_2018", lambda r: r["car"]["kickdown_load"].update(
            source=r["car"]["kickdown_load"]["source"].replace("[car] shift_load", "[car] kickdown_load")))
        self.assertFlags(car_problems("honda_l15b7", r, self.b58), "[car] kickdown_load", "its marker cites")

    def test_a_field_typed_twice_over_or_left_out(self):
        r = self.mutated("ford_27tt", lambda r: r["cycle"].update(
            knock_a={"value": 0.01768, "label": "ASSUMED", "source": MARK + "engine_specs/b58.toml [cycle] knock_a"}))
        self.assertFlags(engine_problems("ford_27tt", r, self.b58), "[cycle] knock_a is typed and not in the registry")
        r = self.mutated("ford_27tt", lambda r: r["thermal"].pop("t_turb_warm"))
        self.assertFlags(engine_problems("ford_27tt", r, self.b58),
                         "[thermal] t_turb_warm is in the registry and not typed")

    def test_a_label_changed(self):
        r = self.mutated("mazda_25t", lambda r: r["cycle"]["wiebe_a"].update(label="ASSUMED"))
        self.assertFlags(engine_problems("mazda_25t", r, self.b58), "[cycle] wiebe_a: label 'ASSUMED'")

    def test_a_float_field_written_as_an_int(self):
        r = self.mutated("f150_2015", lambda r: r["car"]["upshift_min_rpm"].update(value=2000))
        self.assertFlags(car_problems("ford_27tt", r, self.b58), "[car] upshift_min_rpm", "amendment B10")

    def test_an_own_value_moved(self):
        for spec, getter, edit, want in (
                ("mazda_25t", engine_problems, lambda r: r["ecu"]["lam_floor"].update(value=0.685), "[ecu] lam_floor"),
                ("ford_27tt", engine_problems, lambda r: r["fuel"]["afr_st"].update(value=14.557), "[fuel] afr_st"),
                ("honda_l15b7", engine_problems,
                 lambda r: r["loop"]["p_gain"].update(value=r["loop"]["p_gain"]["value"] * (1.0 + 1e-15)),
                 "[loop] p_gain")):
            with self.subTest(spec=spec, field=want):
                self.assertFlags(getter(spec, self.mutated(spec, edit), self.b58), want, "the registry's")
        r = self.mutated("cx9_2016", lambda r: r["car"]["peak_torque_nm"].update(value=420.3))
        self.assertFlags(car_problems("mazda_25t", r, self.b58), "[car] peak_torque_nm", "the registry's")
        r = self.mutated("cx9_2016", lambda r: r["car"]["gears"].update(value=[3.487, 1.992, 1.449, 1.0, 0.707, 0.6001]))
        self.assertFlags(car_problems("mazda_25t", r, self.b58), "[car] gears", "the registry's")


if __name__ == "__main__":
    unittest.main(verbosity=2)
