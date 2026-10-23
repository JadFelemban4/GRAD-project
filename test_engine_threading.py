"""test_engine_threading.py -- no plant call anywhere leans on a default engine.

    python test_engine_threading.py        a few seconds; exit code 0 when all pass

Decision 24 (20 October 2026) makes the H/tau test four engines, each in its own
car. Until then the B58 was the plant's DEFAULT -- plant.Geometry's defaults,
the literals of plant.py, thermal.py and engine_env.py, the class attributes of
engine_env.Vehicle, make_grade_climb's defaults -- so any call that left the
engine out got the B58 without a word. That is mistake 1 (the 2.0 L
inline-four a default ran for three weeks), and a second engine would have
inherited the B58 wherever a default stood in for it. engines.py carries every
engine- and car-specific value now, and every entry point takes it explicitly.
This file holds the line, five ways, and each can fail:

  Signatures    every function or method in the tree with a parameter called
                engine, plant, cal or car gives it no default; the plant's
                entry points require their record (inspect, on the live
                objects); make_grade_climb has no default at all; a record
                field with a default is refused when its class is made
  Defaults      in such a function every OTHER default is one of the
                experiment's own settings, the same for every engine
                (PROTOCOL_DEFAULTS), or None standing for the plant's own value
                (PLANTS_OWN_IF_NONE); anything else -- a number, a module
                constant, None standing for one engine's grid -- is flagged.
                Added 21 October 2026 (the review of build step 1):
                measure_deliverable_torque took plant= and measured the B58
                table's grid, 42 C and a 365 K block for any plant it was given,
                and the record-parameter rule above could not see it
  Calls         an AST scan of every .py a commit of this tree would hold --
                tracked, or untracked and not ignored, so a new file is scanned
                before it is committed -- finds no call of a plant entry point
                that leaves the record out (CALLS lists each one and what it
                must be given), nor of a class that subclasses one and keeps
                its constructor (the learning lab's CapturingEnv); a call that
                forwards **kwargs is taken on trust, and the runtime refuses it
                if it lied. Since 22 October 2026 (build step 2 P7): a measured
                fuel flow given its afr_st as a typed number (NOT_LITERAL)
  Names         every name taken from a plant module exists in it, and no
                property is read off a class
  Registry      engines.get refuses None and an unknown name, and builds the
                B58 that the specs and the derived file describe; typed_engine
                builds its typed records without that file; name_of names a
                plant by its specs; a spec is hashed by its values in either
                TOML form. Since 22 October 2026 (build step 2 P5): every plant
                through its own DERIVED set (DERIVED_BY_SET), each field by its
                own converter (amendment B14); build_candidate builds what get()
                builds from the same numbers, the B58 and an EPA-set engine alike
                (mistake 10), and refuses a NumPy value (amendment B10); an EPA
                plant built from its file is refused unless its frozen sections
                are its freeze record's; a spec's top-level keys are required and
                no others, and each of B13's says its label and source in the
                comment above it; calibrated() and trainable() (decision 47,
                amendment B7). Since P6 (22 October 2026): the three EPA plants
                are registered with their six specs and not calibrated -- get()
                and typed_engine refuse them, a candidate holds every value their
                specs type, and `python engines.py` lists each as "not
                calibrated yet" instead of stopping. Since P7 (22 October 2026):
                a check of that uncalibrated state is skipped by name for a
                plant whose calibration has written one of its files, never
                failed (uncalibrated_or_skip)
  The scans can fail: each is run on a scratch source holding an engine-less
  call, a subclass call without its record, a removed name, a B58 default
  beside a record, and must flag them (mistake 12: a check that cannot fail is
  not a check).

THE FOUR DRIVE-C FILES ARE EXEMPT, ON PURPOSE. drive_c_analysis.py,
drive_c_rule_numbers.py, drive_c_check.py and test_drive_c_analysis.py are
frozen until drive C's stage C has run on main (decisions 14-23 and 25 of
results/VALIDATION_DECISIONS.md: editing them changes their code_sha, which the
frozen rule records), and their plant calls are mended when GRA-test merges
into main, after stage C (decision 25). FROZEN below names them; nothing else
is exempt. On GRA-test they cannot run: drive_c_analysis.plant_check, which
stages A, B and C call before they read anything, stops with an exception
before its plant_sha comparison is reached (fingerprint.derived_sha requires
its path since 20 October 2026, and fingerprint.PLANT_FILES is gone since 21
October; FrozenFiles checks it). This said "they refuse by design -- their
guard finds a plant_sha that is not X1's" until 21 October 2026, which nobody
had run: the guard never got that far (the review of build step 1).
"""
import ast
import contextlib
import inspect
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# Decision 25: frozen until drive C's stage C runs on main, mended at the merge.
FROZEN = frozenset({"drive_c_analysis.py", "drive_c_rule_numbers.py", "drive_c_check.py",
                    "test_drive_c_analysis.py"})

# A parameter by one of these names carries a plant record and may never default.
RECORD_PARAMS = frozenset({"engine", "plant", "cal", "car"})

# DEFAULTS BESIDE A RECORD. In a function that takes one of RECORD_PARAMS, a
# parameter may default only when this names it: the experiment's own setting,
# the same for every engine, with the reason...
PROTOCOL_DEFAULTS = {
    "seed": "the random stream",
    "dt": "the experiment's step (train.DESIGN_DT, evaluate.DT)",
    "duration": "the episode's length (train.DURATION_S, evaluate.DURATION)",
    "use_preview": "the agent's arm, sighted or blind",
    "uncertainty_beta": "the reward's price on a surrogate's uncertainty, 0 from the cycle model",
    "protocol": "the experiment, 'phase-d' or 'd2'; a mismatch is refused on the FATAL scenario",
    "road": "the road design (train.build_env) or the locked climb when None (evaluate)",
    "families": "the training roads' families (engine_env.TERRAIN_FAMILIES)",
    "weights": "their shares (engine_env.TERRAIN_WEIGHTS)",
    "grade_max": "the steepest training hill (engine_env.TERRAIN_GRADE_MAX)",
    "enrichment_map": "a mode of the ECU model, off unless asked",
    "pin_block": "a mode of the replay (car_thermal.thermal_replay)",
    "dtheta": "the crank-angle step, every engine's (plant.DTHETA_DEG, the FATAL dtheta_deg)",
}
# ... or when it defaults to None, and only None, because the function then reads
# the plant's own value (engines.py: a default read from the plant is not a
# silent one) or the input is absent.
PLANTS_OWN_IF_NONE = {
    "v_kmh": "the plant's locked-climb speed (plant.scenario)",
    "t_amb": "the plant's locked-climb ambient (plant.scenario)",
    "inlet_kpa": "the engine's sea-level inlet (plant.engine.boost.inlet_sea_kpa)",
    "cycle": "the plant's locked climb (engine_env.EngineEnv)",
    "engine_model": "no surrogate: the plant's own cycle model",
    "p_exh_kpa": "the engine's backpressure model (plant.exhaust_backpressure_kpa)",
    "params": "the plant's own thermal constants (car_thermal.thermal_replay)",
    "family": "a family drawn from the families",
    "record": "no record kept",
    "w": "weights the environment draws",
    "knock_integral": "no knock term (engine_env.damage_rate)",
    # build step 2 P4 (22 October 2026): form D's intake cam, which the ECU
    # schedules (engine_env.BaselineECU.cam_deg) and plant.run_cycle takes
    "cam_deg": "no cam input: an engine whose form has no D; a form-D engine refuses None",
}
# Positional arguments that may not be passed as a literal None either (a charge
# temperature's t_block_k may: None is its explicit "no block coupling").
# engine and fuel since 22 October 2026: engines.with_fuel's two records.
# values and kind since 22 October 2026 (build step 2 P5): build_candidate's and published_car's.
NOT_NONE = frozenset({"p", "cal", "car", "plant", "name", "path", "engine", "fuel", "values", "kind"})
# Keywords that carry a record's value and may not be given as a number typed at
# the call (22 October 2026, build step 2 P7; the review of P1): a measured fuel
# flow's afr_st is the fuel's, plant.engine.fuel.afr_st or typed_engine's, and a
# literal 14.7 there is the B58's fuel wherever the function runs (amendment B6;
# mistake 1). The keyword's presence alone was all the scan checked.
NOT_LITERAL = frozenset({"afr_st"})

# Each plant entry point, by the name it is called by, and what a call must
# give it: ("kw", name) a keyword; ("pos_or_kw", n, name) the n-th positional
# argument or that keyword; ("all_kw", names) every one of these keywords.
# Names other modules also use for unrelated functions are matched only when
# called through the module (QUALIFIED).
CALLS = {
    "run_cycle": [("kw", "engine")],
    "predict": [("kw", "engine")],
    "map_from_airflow": [("kw", "engine")],
    "boost_ceiling_kpa": [("kw", "engine"), ("pos_or_kw", 2, "p_inlet_kpa")],
    "charge_temperature": [("kw", "engine"), ("pos_or_kw", 1, "t_block_k")],
    # map_kpa since 22 October 2026 (build step 2 P3): form B's MAP term; None is
    # allowed, form A's breathing reads no MAP (map_from_airflow passes None). And
    # cam_deg (P4): form D's cam, None for a form without D, also passed explicitly
    "volumetric_efficiency": [("kw", "engine"), ("pos_or_kw", 1, "map_kpa"), ("pos_or_kw", 2, "cam_deg")],
    # build step 2 P3 (22 October 2026): its rich slope is the engine's (form C)
    "combustion_efficiency": [("kw", "engine")],
    "burn_duration": [("kw", "engine")],
    "ignition_delay": [("kw", "engine")],
    "residual_fraction": [("kw", "engine")],
    "exhaust_backpressure_kpa": [("kw", "engine")],
    "damage_rate": [("kw", "cal")],
    "ThermalNetwork": [("pos_or_kw", 0, "p")],
    "BaselineECU": [("pos_or_kw", 0, "cal")],
    "Vehicle": [("pos_or_kw", 0, "car")],
    "ThinAirVehicle": [("pos_or_kw", 0, "plant")],
    "SupervisoryTunerEnv": [("kw", "plant")],
    "TerrainTrainingEnv": [("kw", "plant")],
    "ExtremesTrainingEnv": [("kw", "plant")],
    "WideAirTrainingEnv": [("kw", "plant")],
    "EngineEnv": [("kw", "plant")],
    "make_terrain": [("kw", "plant")],
    "locked_climb": [("pos_or_kw", 0, "plant")],
    "make_grade_climb": [("all_kw", ("duration", "dt", "t_amb", "grade", "v_kmh"))],
    "measure_deliverable_torque": [("kw", "plant"), ("pos_or_kw", 0, "rpms")],
    "min_tractive_force": [("pos_or_kw", 2, "floor_nm")],
    "extreme_speed_profile": [("pos_or_kw", 6, "floor_nm")],
    "plant_fingerprint": [("kw", "plant"), ("kw", "backend")],
    "run_episode": [("kw", "plant")],
    "episode_cycle": [("kw", "plant")],
    "scenario_line": [("kw", "plant")],
    "deliverable_torque": [("kw", "plant")],
    "thin_air_ratios": [("pos_or_kw", 0, "plant")],
    "inlet_kpa": [("kw", "engine")],
    "thermal_replay": [("kw", "plant")],
    "oil_time_constants": [("kw", "plant")],
    # build step 2 P1 (22 October 2026): the fuel is the engine's. with_fuel is
    # the only way to change it; a measured fuel flow names the fuel's AFR_st,
    # which was plant.AFR_STOICH for every engine
    "with_fuel": [("pos_or_kw", 0, "engine"), ("pos_or_kw", 1, "fuel")],
    "measured_fuel_gps": [("kw", "afr_st")],
    # build step 2 P5 (22 October 2026): each car's own vehicle model, given its car
    "vehicle_for": [("pos_or_kw", 0, "car")],
    "EpaVehicle": [("pos_or_kw", 0, "car")],
    "CvtVehicle": [("pos_or_kw", 0, "car")],
}
# (module, name): calls whose rule depends on the module, because another module
# has a function of the same name (engine_env's and wide_air's grade_floor) or the
# name is too common to check anywhere else (get, rollout). A CALLS name is
# checked when it is bound, in the file, to one of the plant's modules or
# functions (_bindings): model.predict is stable-baselines3's, not plant.predict.
QUALIFIED = {
    ("derived", "get"): [("kw", "path")],
    ("derived", "all_params"): [("kw", "path")],
    ("fingerprint", "derived_sha"): [("pos_or_kw", 0, "path")],
    ("engines", "get"): [("pos_or_kw", 0, "name")],
    ("engines", "typed_engine"): [("pos_or_kw", 0, "name")],
    ("engines", "spec_files"): [("pos_or_kw", 0, "name")],
    ("engines", "name_of"): [("pos_or_kw", 0, "plant")],
    ("fingerprint", "plant_files"): [("pos_or_kw", 0, "name")],
    ("random_road", "check_plant"): [("pos_or_kw", 0, "plant")],
    ("engine_env", "grade_floor"): [("pos_or_kw", 4, "floor_nm")],
    ("wide_air", "grade_floor"): [("pos_or_kw", 5, "floor_nm")],
    ("wide_air", "speed_profile"): [("pos_or_kw", 7, "floor_nm")],
    ("check_premise", "rollout"): [("kw", "plant")],
    ("train", "build_env"): [("kw", "plant")],
    ("engines", "engine_sha"): [("pos_or_kw", 0, "plant")],
    # build step 2 P5 (22 October 2026): a candidate plant, a published car file, and
    # whether a plant can be built from its files
    ("engines", "build_candidate"): [("pos_or_kw", 0, "name"), ("pos_or_kw", 1, "values")],
    ("engines", "published_car"): [("pos_or_kw", 0, "path"), ("pos_or_kw", 1, "kind")],
    ("engines", "calibrated"): [("pos_or_kw", 0, "name")],
    ("fingerprint", "refuse_uncalibrated"): [("pos_or_kw", 0, "name")],
    # the review of P5 (22 October 2026): whether a plant is a candidate, which is
    # never fingerprinted
    ("engines", "is_candidate"): [("pos_or_kw", 0, "plant")],
}


def tracked_py():
    """Every .py a commit of this working tree would hold, repository-relative:
    the tracked ones and the untracked ones git does not ignore (engines.py and
    this file were untracked while build step 1 ran). The four frozen files are
    left out."""
    out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                         cwd=HERE, capture_output=True, text=True, check=True).stdout.splitlines()
    return sorted({f for f in out if os.path.basename(f) not in FROZEN or "/" in f})


def _callee(node):
    f = node.func
    if isinstance(f, ast.Name):
        return None, f.id
    if isinstance(f, ast.Attribute):
        # "?" for a base that is not a plain name (self.env.step, a().b), so it is
        # never mistaken for a bare call
        mod = f.value.id if isinstance(f.value, ast.Name) else "?"
        return mod, f.attr
    return None, None


def _number_literal(v):
    """Whether an argument is a number typed at the call: 14.7, -14.7, +14.7."""
    if isinstance(v, ast.UnaryOp) and isinstance(v.op, (ast.UAdd, ast.USub)):
        v = v.operand
    return isinstance(v, ast.Constant) and type(v.value) in (int, float)


def _missing(node, rules):
    """The rules a call does not satisfy. A call that forwards **kwargs (or *args,
    for a positional rule) is taken on trust: the runtime refuses it if it lied."""
    kws = {k.arg for k in node.keywords if k.arg is not None}
    star_kw = any(k.arg is None for k in node.keywords)
    star_pos = any(isinstance(a, ast.Starred) for a in node.args)
    bad = []
    for rule in rules:
        if rule[0] == "kw":
            if rule[1] not in kws and not star_kw:
                bad.append(rule[1])
            elif rule[1] in NOT_LITERAL and any(k.arg == rule[1] and _number_literal(k.value)
                                                for k in node.keywords):
                bad.append(f"{rule[1]} (a literal)")
        elif rule[0] == "pos_or_kw":
            n, name = rule[1], rule[2]
            if len(node.args) <= n and name not in kws and not star_kw and not star_pos:
                bad.append(name)
            elif (len(node.args) > n and isinstance(node.args[n], ast.Constant)
                  and node.args[n].value is None and name in NOT_NONE):
                bad.append(f"{name} (None)")
        elif rule[0] == "all_kw":
            if not star_kw:
                bad += [k for k in rule[1] if k not in kws]
    return bad


def _bindings(tree, rel):
    """Which local names are the plant's modules, and which are its functions,
    in this file: {alias: {module}} and {local name: (module, name)}. A plant
    module's own file binds its module-level functions and classes too."""
    mods, names = {}, {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in PLANT_MODULES:
                    mods.setdefault(a.asname or a.name, set()).add(a.name)
        elif isinstance(node, ast.ImportFrom) and node.module in PLANT_MODULES and node.level == 0:
            for a in node.names:
                names[a.asname or a.name] = (node.module, a.name)
    me = rel[:-3] if rel.endswith(".py") and "/" not in rel else None
    if me in PLANT_MODULES:
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                names.setdefault(node.name, (me, node.name))
    return mods, names


def _rules(module, name):
    return QUALIFIED.get((module, name)) or CALLS.get(name)


def _call_rules(mod, name, mods, names, inherited):
    """The rules for a call of `mod.name` (mod None for a bare name) in a file
    with these bindings, or None when it is not a plant call."""
    if mod is None and name in names:
        return _rules(*names[name])
    if mod is None and name in inherited:
        return inherited[name]
    rules = None
    if mod in mods:
        for m in sorted(mods[mod]):
            rules = rules or _rules(m, name)
    return rules


def _inherited(tree, mods, names):
    """{class name: rules} for every class in the file that subclasses a plant
    entry point and keeps its constructor: no __init__ of its own, or one that
    forwards *args/**kwargs to a super().__init__ that does not name the record
    itself. Such a class is called as its base is (the learning lab's
    CapturingEnv(SupervisoryTunerEnv) and CapturingBaselineECU(BaselineECU) were
    called without their plant, and only the runtime said so). A subclass whose
    super().__init__ passes the record is not its callers' concern: that call
    is checked like any other."""
    classes = [n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
    out = {}
    grew = True
    while grew:                                  # a subclass of a subclass
        grew = False
        for cls in classes:
            if cls.name in out or cls.name in names:
                continue
            for base in cls.bases:
                bmod, bname = _callee(ast.Call(func=base, args=[], keywords=[]))
                rules = _call_rules(bmod, bname, mods, names, out)
                if rules and _keeps_constructor(cls, rules):
                    out[cls.name] = rules
                    grew = True
                    break
    return out


def _keeps_constructor(cls, rules):
    init = next((b for b in cls.body if isinstance(b, ast.FunctionDef) and b.name == "__init__"), None)
    if init is None:
        return True
    if init.args.vararg is None and init.args.kwarg is None:
        return False
    for node in ast.walk(init):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == "__init__" and isinstance(node.func.value, ast.Call)
                and isinstance(node.func.value.func, ast.Name) and node.func.value.func.id == "super"):
            bare = ast.Call(func=node.func, args=[a for a in node.args if not isinstance(a, ast.Starred)],
                            keywords=[k for k in node.keywords if k.arg is not None])
            if not _missing(bare, rules):
                return False                     # it passes the record itself
    return True


def _inside_assert_raises(tree):
    """ids of every node inside a `with self.assertRaises(...)` block (or
    assertRaisesRegex, pytest.raises): a call there is made wrongly on purpose,
    to show that it is refused, and is not a caller leaning on a default."""
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.With, ast.AsyncWith)) and any(
                isinstance(item.context_expr, ast.Call)
                and isinstance(item.context_expr.func, ast.Attribute)
                and item.context_expr.func.attr in ("assertRaises", "assertRaisesRegex", "raises")
                for item in node.items):
            for stmt in node.body:
                out.update(id(n) for n in ast.walk(stmt))
    return out


def scan_source(src, rel):
    """(file, line, call, what is missing) for every plant call in `src` that
    leaves a record out, and every record parameter given a default. A call is
    a plant call when its name is bound to the plant's module or function in
    this file, or names a class here that subclasses one (_inherited):
    model.predict and a dict called `derived` are not."""
    tree = ast.parse(src, filename=rel)
    mods, names = _bindings(tree, rel)
    inherited = _inherited(tree, mods, names)
    expected_to_raise = _inside_assert_raises(tree)
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and id(node) not in expected_to_raise:
            mod, name = _callee(node)
            rules = _call_rules(mod, name, mods, names, inherited)
            if rules:
                miss = _missing(node, rules)
                if miss:
                    found.append((rel, node.lineno, f"{mod + '.' if mod else ''}{name}", ", ".join(miss)))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda)):
            a = node.args
            pos = a.posonlyargs + a.args
            pos_defaults = dict(zip([p.arg for p in pos][len(pos) - len(a.defaults):], a.defaults))
            kw_defaults = {p.arg: d for p, d in zip(a.kwonlyargs, a.kw_defaults) if d is not None}
            fname = getattr(node, "name", "<lambda>")
            takes_record = RECORD_PARAMS & {p.arg for p in pos + a.kwonlyargs}
            for p, d in list(pos_defaults.items()) + list(kw_defaults.items()):
                if p in RECORD_PARAMS:
                    found.append((rel, node.lineno, f"def {fname}", f"parameter {p!r} has a default"))
                elif takes_record and not _default_allowed(p, d):
                    found.append((rel, node.lineno, f"def {fname}",
                                  f"parameter {p!r} defaults to {ast.unparse(d)} beside the plant record"))
    return found


def _default_allowed(name, default):
    """A default beside a record is the experiment's own (PROTOCOL_DEFAULTS), or
    None standing for the plant's own value (PLANTS_OWN_IF_NONE)."""
    if name in PROTOCOL_DEFAULTS:
        return True
    return (name in PLANTS_OWN_IF_NONE and isinstance(default, ast.Constant)
            and default.value is None)


# The plant's modules: a name imported from one, or read off one, must exist in
# it. The B58's old defaults went with names -- TURB_PROTECT_K, GEO, b58(),
# EXH_BACKPRESSURE_RATIO, boost_ceiling_constants, thermal.ThermalParams,
# Vehicle.gears as a class attribute -- and a caller still reaching for one
# would fail only when that line ran.
PLANT_MODULES = ("plant", "engine_env", "thermal", "wide_air", "evaluate", "check_premise",
                 "fingerprint", "engines", "derived", "random_road", "step_record", "car_thermal",
                 "train")


def scan_names(src, rel, modules):
    """(file, line, name, why) for every name taken from a plant module that it
    does not define, and every property read off a class instead of an instance
    (BaselineECU.ENR_LOAD is the property object, not 180 kPa)."""
    tree = ast.parse(src, filename=rel)
    alias = {}                          # local name -> set of modules it may be
    other = set()                       # names this file also binds to something else
    found = []

    def dotted(n):
        parts = []
        while isinstance(n, ast.Attribute):
            parts.append(n.attr)
            n = n.value
        return ".".join([n.id] + parts[::-1]) if isinstance(n, ast.Name) else None

    # a name the file assigns itself (a monkeypatch, timestep_study's
    # _step_once) is not the module's to have; a property read only to reach
    # its .fget (wide_air's ThinAirVehicle) is read on purpose
    stored = {dotted(t) for node in ast.walk(tree) if isinstance(node, (ast.Assign, ast.AugAssign))
              for t in (node.targets if isinstance(node, ast.Assign) else [node.target])}
    via_fget = {id(node.value) for node in ast.walk(tree)
                if isinstance(node, ast.Attribute) and node.attr in ("fget", "fset")}

    def check_attr(obj, attr, node, shown):
        if dotted(node) in stored:
            return
        if not hasattr(obj, attr):
            found.append((rel, node.lineno, shown, "does not exist"))
        elif (inspect.isclass(obj) and id(node) not in via_fget
              and isinstance(inspect.getattr_static(obj, attr, None), property)):
            found.append((rel, node.lineno, shown, "is a property, read off the class"))

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name in modules:
                    alias.setdefault(a.asname or a.name, set()).add(a.name)
                else:
                    other.add(a.asname or a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module in modules and node.level == 0:
            mod = modules[node.module]
            for a in node.names:
                if a.name == "*":
                    continue
                if not hasattr(mod, a.name):
                    found.append((rel, node.lineno, f"from {node.module} import {a.name}", "does not exist"))
                elif inspect.isclass(getattr(mod, a.name)):
                    alias.setdefault(a.asname or a.name, set()).add(f"{node.module}.{a.name}")
        elif isinstance(node, ast.ImportFrom):
            other.update(a.asname or a.name for a in node.names)
    alias = {k: v for k, v in alias.items() if k not in other}   # ambiguous in this file: not checked
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Attribute) and isinstance(node.ctx, ast.Load)):
            continue
        base = node.value
        if isinstance(base, ast.Name) and base.id in alias:
            objs = [_resolve(modules, m) for m in alias[base.id]]
            have = [o for o in objs if hasattr(o, node.attr)]
            if not have and dotted(node) not in stored:
                found.append((rel, node.lineno, f"{base.id}.{node.attr}", "does not exist"))
            elif have:
                check_attr(have[0], node.attr, node, f"{base.id}.{node.attr}")
        elif (isinstance(base, ast.Attribute) and isinstance(base.value, ast.Name)
              and base.value.id in alias):
            for m in alias[base.value.id]:
                o = _resolve(modules, m)
                cls = getattr(o, base.attr, None)
                if inspect.isclass(cls):
                    check_attr(cls, node.attr, node, f"{base.value.id}.{base.attr}.{node.attr}")
    return found


def _resolve(modules, dotted):
    mod, _, cls = dotted.partition(".")
    return getattr(modules[mod], cls) if cls else modules[mod]


def scan_tree():
    hits, unread = [], []
    for rel in tracked_py():
        path = os.path.join(HERE, rel)
        if not os.path.isfile(path):
            continue
        with open(path, encoding="utf-8") as fh:
            src = fh.read()
        try:
            hits += scan_source(src, rel)
        except SyntaxError as exc:
            unread.append((rel, str(exc)))
    return hits, unread


class Calls(unittest.TestCase):
    def test_no_plant_call_leaves_the_record_out(self):
        hits, unread = scan_tree()
        self.assertEqual(unread, [], ".py files that do not parse, so were not scanned")
        self.assertEqual(hits, [], "plant calls without their record, or record parameters "
                                   "with a default:\n" + "\n".join(f"  {f}:{n}  {c}  -> {m}"
                                                                   for f, n, c, m in hits))

    def test_the_scan_can_fail(self):
        """An engine-less call in a scratch file must be flagged (mistake 12),
        and so must a call of a subclass that keeps its base's constructor."""
        bad = ("import plant, engine_env as E\n"
               "from engine_env import BaselineECU\n"
               "r = plant.run_cycle(op)\n"
               "env = E.SupervisoryTunerEnv(cycle, dt=1.0)\n"
               "t = plant.charge_temperature(315.0, engine=e)\n"
               "c = E.make_grade_climb(duration=60.0, dt=1.0)\n"
               "d = E.damage_rate(1100.0, 400.0)\n"
               "def f(x, plant=None):\n    return x\n"
               # the learning lab's shape: no __init__, or one that forwards
               "class Capturing(BaselineECU):\n    pass\n"
               "class Lab(E.SupervisoryTunerEnv):\n"
               "    def __init__(self, *a, **kw):\n        super().__init__(*a, **kw)\n"
               "class Deeper(Lab):\n    pass\n"
               "ecu = Capturing()\n"
               "lab = Lab(cycle, dt=1.0)\n"
               "deep = Deeper(cycle)\n"
               # not flagged: given the record, or a subclass that passes it itself
               "ok1 = Capturing(cal)\n"
               "ok2 = Lab(cycle, plant=p)\n"
               "class Own(E.SupervisoryTunerEnv):\n"
               "    def __init__(self, cycle, **kw):\n        super().__init__(cycle, plant=P, **kw)\n"
               "ok3 = Own(cycle, dt=1.0)\n"
               # a refusal test is exempt only inside its assertRaises block
               "with self.assertRaises(TypeError):\n    E.Vehicle(None)\n"
               "v = E.Vehicle(None)\n"
               # the review's case: one engine's grid, air and block beside the
               # record (flagged: rpms, t_amb, t_block, settle), next to defaults
               # that are allowed (seed, dt, v_kmh None)
               "def measure(rpms=None, t_amb=315.0, t_block=365.0, settle=30, seed=0, dt=1.0,\n"
               "            v_kmh=None, *, plant):\n    return plant\n"
               # and a call that leaves the new required keywords out
               "t = E.measure_deliverable_torque(plant=p)\n"
               "fp = FP.plant_fingerprint(plant=p)\n"
               # build step 2 P1 (22 October 2026): with_fuel without its fuel, or
               # with None for the engine, and a measured fuel flow without the
               # fuel's AFR_st; not flagged: with_fuel given both
               "e2 = engines.with_fuel(eng)\n"
               "e3 = engines.with_fuel(None, f)\n"
               "fu = CT.measured_fuel_gps(air, lam, rpm)\n"
               "ok4 = engines.with_fuel(eng, f)\n"
               # build step 2 P3 (22 October 2026): the combustion efficiency without
               # its engine, the breathing without its MAP; and P4: the breathing
               # without its cam. Not flagged: the breathing given None for both,
               # form A's (map_from_airflow)
               "ce = plant.combustion_efficiency(0.9)\n"
               "ve = plant.volumetric_efficiency(3000.0, engine=e)\n"
               "ve2 = plant.volumetric_efficiency(3000.0, None, engine=e)\n"
               "ok5 = plant.volumetric_efficiency(3000.0, None, None, engine=e)\n"
               # build step 2 P5 (22 October 2026): a vehicle without its car, a candidate
               # without its values or with None for its name, a published car without its
               # kind. Not flagged: each given what it needs
               "vf = E.vehicle_for()\n"
               "ev = E.EpaVehicle()\n"
               "cv = E.CvtVehicle(None)\n"
               "bc = engines.build_candidate('b58')\n"
               "bn = engines.build_candidate(None, vals)\n"
               "pc = engines.published_car(path)\n"
               "ok6 = E.vehicle_for(p.car)\n"
               "ok7 = engines.build_candidate('b58', vals)\n"
               "ok8 = engines.published_car(path, 'three_term_cvt')\n"
               # the review of P5: is_candidate without its plant; not flagged: given one
               "ic = engines.is_candidate()\n"
               "ok9 = engines.is_candidate(p)\n"
               # build step 2 P7 (22 October 2026; the review of P1): a measured fuel
               # flow given the B58's AFR_st as a number, or its negative; not
               # flagged: given the fuel's
               "fl = CT.measured_fuel_gps(air, lam, rpm, afr_st=14.7)\n"
               "fn = CT.measured_fuel_gps(air, lam, rpm, afr_st=-14.7)\n"
               "ok10 = CT.measured_fuel_gps(air, lam, rpm, afr_st=plant.engine.fuel.afr_st)\n")
        bad = "import fingerprint as FP\nimport engines\nimport car_thermal as CT\n" + bad
        with tempfile.TemporaryDirectory() as tmp:
            p = os.path.join(tmp, "injected.py")
            with open(p, "w", encoding="utf-8") as fh:
                fh.write(bad)
            with open(p, encoding="utf-8") as fh:
                hits = scan_source(fh.read(), "injected.py")
        flagged = sorted(c for _, _, c, _ in hits)
        self.assertEqual(flagged, sorted(["plant.run_cycle", "E.SupervisoryTunerEnv",
                                          "plant.charge_temperature", "E.make_grade_climb",
                                          "E.damage_rate", "def f", "Capturing", "Lab", "Deeper",
                                          "E.Vehicle", "def measure", "def measure", "def measure",
                                          "def measure", "E.measure_deliverable_torque",
                                          "FP.plant_fingerprint", "engines.with_fuel", "engines.with_fuel",
                                          "CT.measured_fuel_gps", "CT.measured_fuel_gps",
                                          "CT.measured_fuel_gps", "plant.combustion_efficiency",
                                          "plant.volumetric_efficiency", "plant.volumetric_efficiency",
                                          "E.vehicle_for", "E.EpaVehicle", "E.CvtVehicle",
                                          "engines.build_candidate", "engines.build_candidate",
                                          "engines.published_car", "engines.is_candidate"]), hits)
        self.assertEqual([n for _, n, c, _ in hits if c == "E.Vehicle"],
                         [bad[:bad.index("v = E.Vehicle")].count("\n") + 1],
                         "only the call outside the assertRaises block")
        beside = sorted(m.split("'")[1] for _, _, c, m in hits if c == "def measure")
        self.assertEqual(beside, ["rpms", "settle", "t_amb", "t_block"],
                         "seed, dt and v_kmh=None are the experiment's or the plant's own")
        self.assertEqual([m for _, _, c, m in hits if c == "FP.plant_fingerprint"], ["backend"])
        self.assertEqual([m for _, _, c, m in hits if c == "E.measure_deliverable_torque"], ["rpms"])
        self.assertEqual(sorted(m for _, _, c, m in hits if c == "engines.with_fuel"),
                         ["engine (None)", "fuel"])
        self.assertEqual(sorted(m for _, _, c, m in hits if c == "CT.measured_fuel_gps"),
                         ["afr_st", "afr_st (a literal)", "afr_st (a literal)"])
        self.assertEqual([m for _, _, c, m in hits if c == "plant.combustion_efficiency"], ["engine"])
        self.assertEqual(sorted(m for _, _, c, m in hits if c == "plant.volumetric_efficiency"),
                         ["cam_deg", "map_kpa, cam_deg"])
        self.assertEqual([m for _, _, c, m in hits if c in ("E.vehicle_for", "E.EpaVehicle", "E.CvtVehicle")],
                         ["car", "car", "car (None)"])
        self.assertEqual(sorted(m for _, _, c, m in hits if c == "engines.build_candidate"),
                         ["name (None)", "values"])
        self.assertEqual([m for _, _, c, m in hits if c == "engines.published_car"], ["kind"])
        self.assertEqual([m for _, _, c, m in hits if c == "engines.is_candidate"], ["plant"])

    def test_every_allowed_default_says_why(self):
        """The two lists of allowed defaults are the rule's exemptions: each
        names its reason, and no name is in both."""
        for table in (PROTOCOL_DEFAULTS, PLANTS_OWN_IF_NONE):
            for name, why in table.items():
                self.assertTrue(isinstance(why, str) and why.strip(), name)
        self.assertEqual(set(PROTOCOL_DEFAULTS) & set(PLANTS_OWN_IF_NONE), set())
        self.assertEqual(set(PROTOCOL_DEFAULTS) & RECORD_PARAMS, set())
        self.assertEqual(set(PLANTS_OWN_IF_NONE) & RECORD_PARAMS, set())

    def test_the_tree_scan_flags_an_injected_file(self):
        """The real scan of the tree, not a string: a file dropped into the
        repository, untracked, holding an engine-less call, is flagged by
        scan_tree (mistake 12). Untracked files are scanned because engines.py
        and this file were untracked while build step 1 ran, and a new caller
        must not wait for a commit to be checked. The file is removed after."""
        fd, path = tempfile.mkstemp(prefix="_scan_probe_", suffix=".py", dir=HERE)
        rel = os.path.basename(path)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write("import engine_env as E\nenv = E.SupervisoryTunerEnv(cycle, dt=1.0)\n")
            self.assertIn(rel, tracked_py())
            hits, _ = scan_tree()
            self.assertIn((rel, 2, "E.SupervisoryTunerEnv", "plant"), hits)
        finally:
            os.remove(path)
        self.assertNotIn(rel, tracked_py())

    def test_the_exemption_is_exactly_the_four_frozen_files(self):
        listed = subprocess.run(["git", "ls-files", *sorted(FROZEN)], cwd=HERE, capture_output=True,
                                text=True, check=True).stdout.split()
        self.assertEqual(sorted(listed), sorted(FROZEN), "every exempt file must exist and be tracked")
        self.assertTrue(FROZEN.isdisjoint(tracked_py()))


def scan_all_names():
    import importlib
    modules = {m: importlib.import_module(m) for m in PLANT_MODULES}
    hits = []
    for rel in tracked_py():
        path = os.path.join(HERE, rel)
        if os.path.isfile(path):
            with open(path, encoding="utf-8") as fh:
                hits += scan_names(fh.read(), rel, modules)
    return hits


class Names(unittest.TestCase):
    def test_every_plant_name_used_exists(self):
        hits = scan_all_names()
        self.assertEqual(hits, [], "names taken from the plant's modules that are not there:\n"
                         + "\n".join(f"  {f}:{n}  {c}  {m}" for f, n, c, m in hits))

    def test_the_name_scan_can_fail(self):
        import importlib
        modules = {m: importlib.import_module(m) for m in PLANT_MODULES}
        bad = ("import engine_env as EE\n"
               "from engine_env import TURB_PROTECT_K, BaselineECU\n"
               "x = EE.GEO\n"
               "g = EE.Vehicle.gears\n"
               "e = BaselineECU.ENR_LOAD\n")
        flagged = {c for _, _, c, _ in scan_names(bad, "injected.py", modules)}
        self.assertEqual(flagged, {"from engine_env import TURB_PROTECT_K", "EE.GEO", "EE.Vehicle.gears",
                                   "BaselineECU.ENR_LOAD"})


class Signatures(unittest.TestCase):
    def test_entry_points_require_their_record(self):
        import car_thermal as CT
        import derived
        import engine_env as E
        import engines
        import evaluate as V
        import fingerprint as FP
        import plant as P
        import random_road as RR
        import thermal as T
        import wide_air as W
        import check_premise as C
        required = [
            (P.run_cycle, "engine"), (P.predict, "engine"), (P.map_from_airflow, "engine"),
            (P.boost_ceiling_kpa, "engine"), (P.boost_ceiling_kpa, "p_inlet_kpa"),
            (P.boost_ceiling_kpa, "t_inlet_k"), (P.charge_temperature, "engine"),
            (P.charge_temperature, "t_block_k"), (P.volumetric_efficiency, "engine"),
            (P.burn_duration, "engine"), (P.ignition_delay, "engine"), (P.residual_fraction, "engine"),
            (P.exhaust_backpressure_kpa, "engine"),
            (T.ThermalNetwork, "p"), (E.BaselineECU, "cal"), (E.Vehicle, "car"),
            (E.damage_rate, "cal"), (E.SupervisoryTunerEnv, "plant"), (E.TerrainTrainingEnv, "plant"),
            (E.ExtremesTrainingEnv, "plant"), (E.EngineEnv, "plant"), (E.make_terrain, "plant"),
            (E.locked_climb, "plant"), (E.measure_deliverable_torque, "plant"),
            (E.min_tractive_force, "floor_nm"), (E.grade_floor, "veh"), (E.grade_floor, "floor_nm"),
            (E.extreme_speed_profile, "veh"), (E.extreme_speed_profile, "floor_nm"),
            (W.WideAirTrainingEnv, "plant"), (W.ThinAirVehicle, "plant"), (W.deliverable_torque, "plant"),
            (W.thin_air_ratios, "plant"), (W.inlet_kpa, "engine"), (W.grade_floor, "floor_nm"),
            (W.speed_profile, "floor_nm"),
            (FP.plant_fingerprint, "plant"), (FP.plant_fingerprint, "backend"), (FP.derived_sha, "path"),
            (FP.plant_files, "name"),
            (V.run_episode, "plant"), (V.episode_cycle, "plant"), (V.scenario_line, "plant"),
            (C.rollout, "plant"), (derived.get, "path"), (derived.all_params, "path"),
            (engines.get, "name"), (engines.typed_engine, "name"), (engines.spec_files, "name"),
            (engines.name_of, "plant"),
            # the review of 21 October 2026: what the table is measured on, and the backend
            (E.measure_deliverable_torque, "rpms"), (W.deliverable_torque, "rpms"),
            (RR.check_plant, "plant"), (CT.oil_time_constants, "drives"),
            # build step 2 P1 (22 October 2026): the fuel is the engine's
            (engines.with_fuel, "engine"), (engines.with_fuel, "fuel"), (CT.measured_fuel_gps, "afr_st"),
            # build step 2 P3 (22 October 2026): the rich slope is the engine's; the
            # breathing takes the MAP, form B's term; and (P4) the cam, form D's
            (P.combustion_efficiency, "engine"), (P.volumetric_efficiency, "map_kpa"),
            (P.volumetric_efficiency, "cam_deg"),
            # build step 2 P5 (22 October 2026): the cars, the candidate, the published
            # car file, whether a plant can be built, and the CVT's law
            (E.vehicle_for, "car"), (E.EpaVehicle, "car"), (E.CvtVehicle, "car"),
            (engines.build_candidate, "name"), (engines.build_candidate, "values"),
            (engines.published_car, "path"), (engines.published_car, "kind"), (engines.calibrated, "name"),
            (FP.refuse_uncalibrated, "name"), (E.CvtVehicle.ratio_for, "v_mps"),
            (E.CvtVehicle.ratio_for, "force_n"), (E.EpaVehicle.road_force_n, "rho"),
            (E.CvtVehicle.demand, "rho"), (E.EpaVehicle.demand, "rho"),
            # the review of P5 (22 October 2026)
            (engines.is_candidate, "plant"),
            # build step 2 P6 (22 October 2026): what a registered plant still lacks
            (engines._missing_files, "name"),
        ]
        for fn, name in required:
            with self.subTest(fn=fn.__qualname__, param=name):
                params = inspect.signature(fn).parameters
                self.assertIn(name, params)
                self.assertIs(params[name].default, inspect.Parameter.empty)

    def test_make_grade_climb_has_no_default_at_all(self):
        import engine_env as E
        params = inspect.signature(E.make_grade_climb).parameters
        self.assertEqual({k for k, p in params.items() if p.default is not inspect.Parameter.empty}, set())

    def test_a_missing_record_is_refused_at_run_time(self):
        import engine_env as E
        import thermal as T
        with self.assertRaises(TypeError):
            T.ThermalNetwork(None)
        with self.assertRaises(TypeError):
            E.BaselineECU(None)
        with self.assertRaises(TypeError):
            E.Vehicle(None)
        with self.assertRaises(TypeError):
            E.SupervisoryTunerEnv({}, plant=None)
        for fn in (E.vehicle_for, E.EpaVehicle, E.CvtVehicle):     # build step 2 P5
            with self.assertRaises(TypeError):
                fn(None)

    def test_a_record_field_cannot_have_a_default(self):
        from dataclasses import MISSING, dataclass, fields
        import engines
        with self.assertRaises(TypeError):
            @engines._required
            @dataclass(frozen=True)
            class Bad:
                x: float = 1.0
        for cls in (engines.Geometry, engines.CycleCal, engines.ChargeCal, engines.BoostCal,
                    engines.EcuCal, engines.ThermalParams, engines.DamageCal, engines.LoopCal,
                    engines.Fuel, engines.Engine, engines.TypedEngine, engines.Car, engines.Scenario,
                    engines.Plant, engines.EpaCar, engines.CvtCar):
            with self.subTest(record=cls.__name__):
                self.assertTrue(cls.__dataclass_params__.frozen)
                self.assertEqual([f.name for f in fields(cls)
                                  if f.default is not MISSING or f.default_factory is not MISSING], [])


def _reader(specs):
    """A read_spec that returns a copy of these probe specs by name, and what the
    read_spec in place now returns for any other name (22 October 2026, P5)."""
    import copy
    import engines
    inner = engines.read_spec
    return lambda n: copy.deepcopy(specs[n]) if n in specs else inner(n)


@contextlib.contextmanager
def _probe_plant(name, spec, car_spec=None):
    """A plant registered as `name` for the block: its engine spec `spec` (read as
    <name>_engine), its car the Supra's or `car_spec` (<name>_car). Nothing is
    written to engine_specs/; PLANTS and the caches are restored after."""
    from unittest import mock
    import engines
    specs = {name + "_engine": spec}
    if car_spec is not None:
        specs[name + "_car"] = car_spec
    saved = dict(engines.PLANTS)
    engines.PLANTS[name] = (name + "_engine", name + "_car" if car_spec is not None else "a90_supra")
    try:
        with mock.patch.object(engines, "read_spec", side_effect=_reader(specs)):
            yield
    finally:
        engines.PLANTS.clear()
        engines.PLANTS.update(saved)
        engines._IDS.clear()
        for cache in (engines._TYPED, engines._BUILT):
            cache.pop(name, None)


def _probe_derived(engine_id):
    """The derived file an EPA engine called `engine_id` would have, as a spec's
    `derived` names it (relative, with "/"): derived.engine_path's, so no test
    carries that folder's literal, which amendment C3's scan forbids outside
    epa_rows.py (the review of P5, 22 October 2026). The probes are never
    calibrated: no such file exists, and nothing opens it."""
    import derived
    return os.path.relpath(derived.engine_path(engine_id), HERE).replace(os.sep, "/")


def calibration_files_written(name):
    """The files the calibration of the EPA plant `name` writes -- its derived file
    and its freeze record, as its engine spec names them -- that exist on disk."""
    import engines
    meta = engines.read_spec(engines.PLANTS[name][0])["_meta"]
    return [f for f in (meta["derived"], meta["freeze"]) if os.path.exists(os.path.join(HERE, f))]


def uncalibrated_or_skip(test, name):
    """`test`'s current subTest skipped, by the plant's name, once the calibration
    of the EPA plant `name` has written its derived file or its freeze record (22
    October 2026, build step 2 P7; the review of P6). A check that calls this pins
    P6's state, a registered plant with neither file. WP4's first `calibrate_epa.py
    fit` ends that state, and commit D, which re-runs this file (decision 48),
    replaces the check with one of the built plant on purpose; until then it must
    skip, never fail for a reason that is not the plant's (mistake 12's other side:
    a check that fails for the wrong reason teaches people to ignore it). The files
    are read from the spec, then looked for on disk: a file that exists is what
    skips, never a path that differs from the expected one, which the check itself
    still compares."""
    written = calibration_files_written(name)
    if written:
        test.skipTest(f"{name}: its calibration has written {', '.join(written)}; this check pins the "
                      "uncalibrated plant of build step 2 P6, and commit D replaces it")


def _epa_probe(p):
    """An engine spec of the EPA DERIVED set made from the B58's, and the values
    that set derives, as the B58 plant `p` holds them: the B58's typed values minus
    every field the EPA set derives, plus, typed, the B58's DERIVED values the EPA
    set does not derive (the network's fifteen, the two dwells: what decision 45
    carries into each EPA spec). Built from these, an EPA-set engine must be the
    B58's engine, value for value."""
    import engines
    b58 = engines.read_spec("b58")
    spec = {k: dict(v) for k, v in b58.items() if k != "_meta"}
    spec["_meta"] = {"id": b58["_meta"]["id"], "derived": _probe_derived("_p5_probe"),
                     "derived_set": "epa", "freeze": "results/EPA_CALIBRATION/_p5_probe/freeze.json"}
    for (rec, f) in engines.EPA_DERIVED_FIELDS:
        spec.get(rec, {}).pop(f, None)
    for (rec, f) in engines.DERIVED_FIELDS:
        if (rec, f) not in engines.EPA_DERIVED_FIELDS:
            spec.setdefault(rec, {})[f] = getattr(getattr(p.engine, rec), f)
    vals = {}
    for (rec, f), (sec, key) in engines.EPA_DERIVED_FIELDS.items():
        v = getattr(p.car if rec == "car" else getattr(p.engine, rec), f)
        if isinstance(v, tuple):
            v = [list(x) if isinstance(x, tuple) else x for x in v]
        if key is None:
            vals[sec] = v
        else:
            vals.setdefault(sec, {})[key] = v
    return spec, vals


def replace_derived(plant, like):
    """`plant` with `like`'s derived-file name, the one field a file-built probe and
    its candidate differ in."""
    from dataclasses import replace
    return replace(plant, engine=replace(plant.engine, derived=like.engine.derived))


# AMENDMENT B13's KEYS: a spec's top-level keys that carry their label and source
# in a TOML comment, since read_spec reads a top-level table as a section (the
# review of P5, 22 October 2026: `published`, an EPA car spec's, joined the three).
B13_KEYS = ("derived_set", "freeze", "kind", "published")


def _b13_problems(text):
    """The B13 keys of a spec's TOML `text` whose comment is missing: each key's
    line, at the top level (above the first [section]), must sit directly under a
    comment block that starts "# <key> --" and names "label <one of
    engines.LABELS>" and "source:"."""
    import re
    import engines
    lines = text.splitlines()
    bad = []
    for i, line in enumerate(lines):
        if line.startswith("["):
            break
        m = re.match(r"(\w+)\s*=", line)
        if not m or m.group(1) not in B13_KEYS:
            continue
        j = i
        while j > 0 and lines[j - 1].startswith("#"):
            j -= 1
        block = " ".join(lines[j:i])
        if not (block.startswith(f"# {m.group(1)} --") and "source:" in block
                and re.search(r"\blabel (" + "|".join(engines.LABELS) + r")\b", block)):
            bad.append(m.group(1))
    return bad


class Registry(unittest.TestCase):
    def test_get_refuses_none_and_unknown_names(self):
        import engines
        with self.assertRaises(TypeError):
            engines.get(None)
        with self.assertRaises(KeyError):
            engines.get("b59")
        with self.assertRaises(KeyError):
            engines.get("")

    def test_the_b58_is_what_its_files_say(self):
        import engines
        import fingerprint as FP
        p = engines.get("b58")
        self.assertEqual(p.id, "b58b30o1/a90-supra-zf8hp51")
        self.assertIs(engines.get("b58"), p)
        self.assertAlmostEqual(p.engine.geometry.vd_total * 1e6, 2997.5, places=0)
        self.assertEqual(p.car.gears, (5.250, 3.360, 2.172, 1.720, 1.316, 1.000, 0.822, 0.640))
        self.assertEqual((p.scenario.grade, p.scenario.v_kmh, p.scenario.t_amb), (0.12, 130.0, 315.0))
        # the derived file is the B58's own, unchanged by the refactor
        self.assertEqual(FP.derived_sha(os.path.join(HERE, p.engine.derived)), "326c0835548975e2")
        # every DERIVED field came from that file, none was typed: every registered
        # plant, through its own engine spec's DERIVED set (build step 2 P5)
        self.assertIs(engines.DERIVED_BY_SET["b58"], engines.DERIVED_FIELDS)
        for name in engines.known():
            espec, cspec = engines.PLANTS[name]
            dset = engines.read_spec(espec)["_meta"]["derived_set"]
            for (record, field), _ in engines.DERIVED_BY_SET[dset].items():
                spec = engines.read_spec(cspec if record == "car" else espec)
                self.assertNotIn(field, spec.get(record, {}), f"{name}: {record}.{field} is DERIVED and typed")
        self.assertEqual(engines.read_spec("b58")["_meta"]["derived_set"], "b58")

    def test_a_typed_value_needs_a_label_and_a_source(self):
        import engines
        for bad in ({"value": 1.0}, {"value": 1.0, "label": "ASSUMED"},
                    {"value": 1.0, "label": "DERIVED", "source": "x"},
                    {"value": 1.0, "label": "GUESSED", "source": "x"}, 1.0):
            with self.subTest(entry=bad):
                with self.assertRaises(ValueError):
                    engines._typed("test", "section", "field", bad)
        self.assertEqual(engines._typed("test", "s", "f", {"value": [1, 2], "label": "ASSUMED",
                                                           "source": "none"}), (1, 2))

    def test_engine_sha_moves_on_a_value_and_not_on_a_source(self):
        from dataclasses import replace
        import engines
        import fingerprint as FP
        p = engines.get("b58")
        q = replace(p, engine=replace(p.engine, thermal=replace(p.engine.thermal, c_turb=6000.000000000001)))
        self.assertNotEqual(engines.engine_sha(p), engines.engine_sha(q))
        with open(os.path.join(HERE, "engine_specs", "b58.toml"), encoding="utf-8") as fh:
            spec = fh.read()
        reworded = spec.replace('source = "no source recorded in plant.py or REFERENCES.md"',
                                'source = "still no source"')
        renumbered = spec.replace("c_turb = { value = 6000.0", "c_turb = { value = 6001.0")
        self.assertNotEqual(reworded, spec)
        self.assertNotEqual(renumbered, spec)
        name = "engine_specs/b58.toml"
        self.assertEqual(FP._file_code(name, reworded), FP._file_code(name, spec))
        self.assertNotEqual(FP._file_code(name, renumbered), FP._file_code(name, spec))

    def test_a_spec_is_hashed_by_its_values_in_either_toml_form(self):
        """The same spec as inline tables (engine_specs/ today) and as TOML tables
        ([geometry.bore] then value = ...), which read_spec reads alike: both by
        their values, a source edit moving neither (the review of 21 October 2026:
        the table form parses as Python and was hashed as code). The control: the
        rule `_code_only` alone still calls the table form code."""
        import tomllib
        import fingerprint as FP
        inline = ('id = "x"\n[geometry]\n'
                  'bore = { value = 0.0820, unit = "m", label = "PUBLISHED", source = "p. 1" }\n')
        table = ('id = "x"\n[geometry.bore]\n'
                 'value = 0.0820\nunit = "m"\nlabel = "PUBLISHED"\nsource = "p. 1"\n')
        self.assertEqual(tomllib.loads(inline), tomllib.loads(table))
        for text in (inline, table):
            with self.subTest(form="inline" if text is inline else "table"):
                code = FP._file_code("engine_specs/x.toml", text)
                self.assertEqual(code, FP._file_code("engine_specs/x.toml", inline))
                self.assertEqual(FP._file_code("engine_specs/x.toml", text.replace("p. 1", "p. 7")), code)
                self.assertNotEqual(FP._file_code("engine_specs/x.toml", text.replace("0.0820", "0.0821")),
                                    code)
        self.assertIsNotNone(FP._code_only(table), "the table form is valid Python: the control")
        self.assertIsNone(FP._code_only(inline))

    def test_plant_files_are_the_plants_own_specs(self):
        """plant_sha hashes the code and the passed plant's own specs, by the
        name the plant was built under (the review of 21 October 2026: one tuple
        named the B58's specs for every plant)."""
        from dataclasses import replace
        import engines
        import fingerprint as FP
        p = engines.get("b58")
        self.assertEqual(FP.plant_files("b58"), FP.PLANT_CODE + ("engine_specs/b58.toml",
                                                                 "engine_specs/a90_supra.toml"))
        self.assertEqual(engines.name_of(p), "b58")
        v = replace(p, engine=replace(p.engine, thermal=replace(p.engine.thermal, c_turb=7000.0)))
        self.assertEqual(engines.name_of(v), "b58", "a variant is named by the plant it was made from")
        with self.assertRaises(LookupError):
            engines.name_of(replace(p, car=replace(p.car, id="another-car")))
        saved = dict(engines.PLANTS)
        try:
            engines.PLANTS["_probe"] = ("_probe_engine", "a90_supra")
            self.assertEqual(FP.plant_files("_probe"), FP.PLANT_CODE + ("engine_specs/_probe_engine.toml",
                                                                        "engine_specs/a90_supra.toml"))
            del engines.PLANTS["_probe"]               # its spec does not exist; only its names were asked
            engines.PLANTS["_twin"] = ("b58", "a90_supra")
            with self.assertRaises(LookupError):
                engines.name_of(p)                     # two names for one pair of specs: refused
        finally:
            engines.PLANTS.clear()
            engines.PLANTS.update(saved)
            engines._IDS.clear()
        self.assertFalse(hasattr(FP, "PLANT_FILES"), "one list for every plant is what this replaced")

    def test_typed_engine_needs_no_derived_file(self):
        """build_dataset.py and new_drive.py run before data/derived_params.json
        exists (on cf43fbb they did; engines.get refused them until 21 October
        2026). typed_engine builds the geometry, cycle and charge records, and the
        fuel since 22 October 2026, from the spec alone -- derived.get is never
        called -- and they equal get's."""
        from unittest import mock
        import derived
        import engines
        engines._TYPED.clear()
        with mock.patch.object(derived, "get", side_effect=AssertionError("read the derived file")):
            t = engines.typed_engine("b58")
        e = engines.get("b58").engine
        self.assertEqual((t.id, t.geometry, t.cycle, t.charge, t.fuel),
                         (e.id, e.geometry, e.cycle, e.charge, e.fuel))
        self.assertEqual(t.geometry.vd_cyl, e.geometry.vd_cyl)
        with self.assertRaises(TypeError):
            engines.typed_engine(None)
        with self.assertRaises(ValueError):          # a record with a DERIVED field needs the file
            engines._record(engines.BoostCal, "boost", {"inlet_sea_kpa": 99.3}, None, "b58", {})

    def test_the_table_is_measured_on_the_cars_grid(self):
        """The car says where its deliverable-torque table is measured (Car.table_*,
        the review of 21 October 2026); the stored table is on that grid."""
        import engines
        car = engines.get("b58").car
        self.assertEqual(tuple(r for r, _ in car.deliverable_torque), car.table_rpms)
        self.assertEqual((car.table_rpms[0], car.table_rpms[-1], len(car.table_rpms)), (1000, 6600, 29))
        self.assertEqual((car.table_t_amb, car.table_t_block, car.table_settle), (315.0, 365.0, 30))

    # ---- build step 2 P5 (22 October 2026): DERIVED sets, candidates, the freeze

    def test_build_candidate_is_get_from_the_same_numbers(self):
        """build_candidate builds by _build, the constructor get() uses, from an
        in-memory DERIVED dict (mistake 10): given the B58's derived file's own
        values it IS the B58, uncached. Controls: one ulp on a value moves it, a
        NumPy value and a missing value are refused (amendment B10)."""
        import copy
        import derived
        import engines
        import numpy as np
        p = engines.get("b58")
        vals = derived.all_params(path=derived.B58_PATH)
        c = engines.build_candidate("b58", copy.deepcopy(vals))
        self.assertEqual(c, p)
        self.assertEqual(engines.engine_sha(c), engines.engine_sha(p))
        self.assertIsNot(c, p)
        self.assertIs(engines.get("b58"), p, "a candidate is never cached")
        moved = copy.deepcopy(vals)
        moved["thermal"]["c_block"] = float(np.nextafter(moved["thermal"]["c_block"], np.inf))
        self.assertNotEqual(engines.engine_sha(engines.build_candidate("b58", moved)), engines.engine_sha(p))
        bad = copy.deepcopy(vals)
        bad["thermal"]["c_block"] = np.float64(bad["thermal"]["c_block"])
        with self.assertRaises(TypeError):
            engines.build_candidate("b58", bad)
        bad = copy.deepcopy(vals)
        del bad["enrichment"]
        with self.assertRaises(KeyError):
            engines.build_candidate("b58", bad)
        for args in ((None, vals), ("b58", None), ("b59", vals)):
            with self.subTest(args=args[:1]):
                with self.assertRaises((TypeError, KeyError)):
                    engines.build_candidate(*args)

    def test_each_derived_set_has_its_converters(self):
        """Amendment B14: a converter per (record, field), with each DERIVED set; the
        B58's three branches are cf43fbb's, the () fallbacks included; the EPA set's
        are strict, its table and envelope element by element."""
        import math
        import engines
        for s in engines.DERIVED_BY_SET:
            self.assertEqual(set(engines.CONVERT_BY_SET[s]), set(engines.DERIVED_BY_SET[s]), s)
        b = engines.CONVERT_BY_SET["b58"]
        self.assertEqual(b[("car", "deliverable_torque")](None), ())
        self.assertEqual(b[("car", "deliverable_torque")]([[1000, 300]]), ((1000, 300.0),))
        self.assertEqual(b[("boost", "envelope_flow")](math.nan), ())
        self.assertEqual(b[("boost", "envelope_pr")]([1, 2.5]), (1.0, 2.5))
        self.assertIs(b[("ecu", "spark_a")], float)
        e = engines.CONVERT_BY_SET["epa"]
        self.assertEqual((e[("cycle", "form")]("A+B"), e[("ecu", "cam_on")](1), e[("cycle", "ve_base")](1)),
                         ("A+B", 1, 1.0))
        for key, bad in ((("cycle", "form"), 1), (("ecu", "cam_on"), True), (("ecu", "cam_on"), 1.0),
                         (("cycle", "ve_base"), "0.8"), (("cycle", "ve_base"), True)):
            with self.subTest(field=key, value=bad):
                with self.assertRaises(TypeError):
                    e[key](bad)
        # the EPA set's table and envelope, element by element (the review of P5, 22
        # October 2026): no table is (), as the B58's; nothing else is converted, and the
        # frozen envelope has no NaN fallback. Control: the B58's own take "1000" and "1.5"
        tbl, env = e[("car", "deliverable_torque")], e[("boost", "envelope_pr")]
        self.assertEqual((tbl(None), tbl([]), tbl([[1000, 300]]), env([1, 2.5])),
                         ((), (), ((1000, 300.0),), (1.0, 2.5)))
        for conv, bad in ((tbl, [["1000", 300.0]]), (tbl, [[1000.0, 300.0]]), (tbl, [[True, 300.0]]),
                          (tbl, [[1000, "300"]]), (tbl, [[1000, 300.0, 1]]), (tbl, "1000,300"),
                          (env, ["1.5", 2.5]), (env, [True]), (env, math.nan), (env, None), (env, "1.5")):
            with self.subTest(converter=conv.__name__, value=bad):
                with self.assertRaises(TypeError):
                    conv(bad)
        self.assertIs(e[("boost", "envelope_flow")], env)
        self.assertEqual((b[("car", "deliverable_torque")]([["1000", "300"]]),
                          b[("boost", "envelope_pr")](["1.5"])), (((1000, 300.0),), (1.5,)))
        self.assertEqual(set(engines.EPA_DERIVED_FIELDS) & set(engines.DERIVED_FIELDS),
                         {("boost", "envelope_flow"), ("boost", "envelope_pr"), ("boost", "pr_cap"),
                          ("ecu", "spark_a"), ("car", "deliverable_torque")})

    def test_under_deriving_params_the_b58s_fallbacks_hold(self):
        """derive_params.py builds the B58 before its file exists (DERIVING_PARAMS=1):
        a missing scalar reads NaN, the envelope and the table come back (), as on
        cf43fbb (amendment B14)."""
        import math
        from unittest import mock
        import engines
        real = engines.read_spec
        spec = real("b58")
        spec["_meta"] = dict(spec["_meta"], derived=os.path.join(tempfile.gettempdir(), "_p5_none", "missing.json"))
        with mock.patch.dict(os.environ, {"DERIVING_PARAMS": "1"}), \
                mock.patch.object(engines, "read_spec", side_effect=lambda n: spec if n == "_p5_b58" else real(n)):
            p = engines._build("_p5_b58", "a90_supra")
        self.assertEqual((p.engine.boost.envelope_flow, p.engine.boost.envelope_pr, p.car.deliverable_torque),
                         ((), (), ()))
        self.assertTrue(math.isnan(p.engine.thermal.c_block) and math.isnan(p.engine.ecu.spark_a))

    def test_an_epa_set_engine_built_from_the_b58s_numbers_is_the_b58(self):
        """The EPA set and its converters (EPA_DERIVED_FIELDS, amendment B14): an
        engine spec of the "epa" set holding the B58's typed values, and typed what
        that set does not derive (the network, the dwells: decision 45's carried
        constants), built by build_candidate from the B58's values of what it does,
        is the B58's engine, value for value. Controls: a field the set derives,
        typed, is refused; a value of the wrong type is refused."""
        from dataclasses import replace
        from unittest import mock
        import engines
        p = engines.get("b58")
        spec, vals = _epa_probe(p)
        with _probe_plant("_p5_epa", spec):
            c = engines.build_candidate("_p5_epa", vals)
            self.assertEqual(replace(c, engine=replace(c.engine, derived=p.engine.derived)), p)
            typed = {k: dict(v) for k, v in spec.items()}
            typed["cycle"]["ve_base"] = 0.8
            with mock.patch.object(engines, "read_spec", side_effect=_reader({"_p5_epa_engine": typed})):
                with self.assertRaises(ValueError):
                    engines.build_candidate("_p5_epa", vals)
            for sec, key, bad in (("ecu", "cam_on", 0.0), ("cycle", "form", 1), ("k3", "turb_knee_k", "1123")):
                with self.subTest(field=f"{sec}.{key}", value=bad):
                    wrong = {k: (dict(v) if isinstance(v, dict) else v) for k, v in vals.items()}
                    wrong[sec][key] = bad
                    with self.assertRaises(TypeError):
                        engines.build_candidate("_p5_epa", wrong)
        self.assertEqual(engines.typed_engine("b58").fuel, p.engine.fuel)
        # an EPA engine's cycle record has DERIVED fields, so typed_engine refuses it, by
        # the engine's own derived_set: the message is the DERIVED refusal's (the review of
        # P5, 22 October 2026: read in the B58's set, the same fields are missing, and a
        # bare ValueError let that through)
        refusal = r"\[cycle\] \w+ is DERIVED: .* needs engines.get, not typed_engine"
        with _probe_plant("_p5_epa", spec), self.assertRaisesRegex(ValueError, refusal):
            engines.typed_engine("_p5_epa")

    def test_an_epa_plant_is_built_from_its_file_only_after_its_freeze(self):
        """PLAN.md 5.8 and amendment F7: get() of an EPA plant checks the derived
        file's frozen sections against its freeze record. The file-built plant is
        the candidate built from the same values (mistake 10). Controls: no freeze
        record, a wrong hash, a frozen constant edited after the freeze are each
        refused; a completion section edited is not, since it is not frozen."""
        import json
        import engines
        p = engines.get("b58")
        spec, vals = _epa_probe(p)
        with tempfile.TemporaryDirectory() as tmp, _probe_plant("_p5_epa", spec):
            cand = engines.build_candidate("_p5_epa", vals)

            def build(name, values, sha):
                d, f = os.path.join(tmp, name + "_derived.json"), os.path.join(tmp, name + "_freeze.json")
                with open(d, "w", encoding="utf-8") as fh:
                    json.dump(values, fh)
                if sha is not None:
                    with open(f, "w", encoding="utf-8") as fh:
                        json.dump({"frozen_sections_sha256": sha}, fh)
                s = dict(spec, _meta=dict(spec["_meta"], derived=d, freeze=f))
                with _probe_plant("_p5_file", s):
                    return engines._build("_p5_file_engine", "a90_supra"), engines.calibrated("_p5_file")

            sha = engines.frozen_sections_sha256(vals)
            built, ok = build("good", vals, sha)
            self.assertTrue(ok)
            self.assertEqual(replace_derived(built, cand), cand)
            with self.assertRaises(FileNotFoundError):
                build("nofreeze", vals, None)
            with self.assertRaises(ValueError):
                build("wrongsha", vals, "0" * 64)
            edited = json.loads(json.dumps(vals))
            edited["cycle"]["burn_base"] *= 1.0 + 1e-12
            with self.assertRaises(ValueError):
                build("edited", edited, sha)
            later = json.loads(json.dumps(vals))
            later["k3"]["turb_knee_k"] = 1100.0
            built, _ = build("completed", later, sha)
            self.assertEqual(built.engine.damage.turb_knee_k, 1100.0)
        with self.assertRaises(ValueError):          # the hash refuses a NaN, never writes one
            engines.frozen_sections_sha256(dict(vals, cycle=dict(vals["cycle"], burn_base=float("nan"))))
        with self.assertRaises(ValueError):
            engines.frozen_sections_sha256({"cycle": {}, "ecu": {}})

    def test_a_specs_top_level_keys_are_required_and_no_others(self):
        """Amendment B13 and mistake 1: derived_set and kind are required, never the
        B58's by default, and a key a set does not have is refused."""
        from unittest import mock
        import engines
        real = engines.read_spec
        b58, supra = real("b58"), real("a90_supra")
        bad_engines = [dict(b58["_meta"], derived_set=None), dict(b58["_meta"], derived_set="b59"),
                       dict(b58["_meta"], freeze="results/x/freeze.json"),
                       dict(b58["_meta"], derived_set="epa")]                 # the EPA set needs its freeze
        del bad_engines[0]["derived_set"]
        for meta in bad_engines:
            with self.subTest(engine=meta):
                specs = {"_p5_engine": dict(b58, _meta=meta)}
                with mock.patch.object(engines, "read_spec", side_effect=_reader(specs)), \
                        self.assertRaises(ValueError):
                    engines._build("_p5_engine", "a90_supra")
        bad_cars = [{"id": supra["_meta"]["id"]}, dict(supra["_meta"], kind="two_term"),
                    dict(supra["_meta"], published="engine_specs/cars/a90_supra_2020.toml"),
                    dict(supra["_meta"], kind="three_term_stepped")]          # without its published file
        for meta in bad_cars:
            with self.subTest(car=meta):
                specs = {"_p5_car": dict(supra, _meta=meta)}
                with mock.patch.object(engines, "read_spec", side_effect=_reader(specs)), \
                        self.assertRaises(ValueError):
                    engines._build("b58", "_p5_car")
        self.assertEqual(engines._build("b58", "a90_supra"), engines.get("b58"))      # the control

    def test_every_b13_key_says_its_label_and_source(self):
        """Amendment B13: a top-level key's label and source are the comment above
        it, in every registered plant's specs: the B58's derived_set and the
        Supra's kind, and the six EPA specs P6 registered, derived_set and freeze
        in each engine spec, kind and published in each car spec (the review of P5,
        22 October 2026). Controls: the Supra's spec with its kind comment cut, or
        its label dropped, is refused."""
        import engines
        for name in engines.known():
            for spec in engines.PLANTS[name]:
                with open(os.path.join(engines.SPECS, spec + ".toml"), encoding="utf-8") as fh:
                    text = fh.read()
                with self.subTest(spec=spec):
                    self.assertTrue(any(line.split("=")[0].strip() in B13_KEYS for line in text.splitlines()
                                        if "=" in line and not line.startswith("#")), spec)
                    self.assertEqual(_b13_problems(text), [])
        with open(os.path.join(engines.SPECS, "a90_supra.toml"), encoding="utf-8") as fh:
            text = fh.read()
        lines = text.splitlines()
        k = j = lines.index('kind = "two_term_stepped"')
        while lines[j - 1].startswith("#"):
            j -= 1
        self.assertGreater(k - j, 1)
        self.assertEqual(_b13_problems("\n".join(lines[:j] + lines[k:])), ["kind"])
        self.assertEqual(_b13_problems(text.replace("# label DESIGN; source:", "# DESIGN; source:")), ["kind"])

    def test_the_car_spec_kind_picks_the_record(self):
        """An EPA car's spec names its published file; _build converts it
        (published_car) and builds the record its kind names."""
        import engines
        p = engines.get("b58")
        spec, vals = _epa_probe(p)
        typed_stepped = dict(final_drive=4.411, gears=(3.487, 1.992, 1.449, 1.00, 0.707, 0.600),
                             driveline_eff=0.92, peak_torque_nm=400.0, shift_load=0.75, shift_rpm_max=5000.0,
                             upshift_min_rpm=2000.0, rpm_min=1300.0, rpm_max=5000.0, table_rpm_lo=1300,
                             table_rpm_hi=5000, table_rpm_step=100, table_t_amb=315.0, table_t_block=365.0,
                             table_settle=30)
        typed_cvt = dict(final_drive=5.36, ratio_low_gear=2.645, ratio_top_gear=0.405, driveline_eff=0.92,
                         kickdown_load=0.75, target_load=0.65, cvt_rpm_min=1000.0, rpm_min=1000.0, rpm_max=5000.0,
                         table_rpm_lo=1000, table_rpm_hi=5000, table_rpm_step=100, table_t_amb=315.0,
                         table_t_block=365.0, table_settle=30)
        scenario = engines.read_spec("a90_supra")["scenario"]
        for kind, file, typed, cls in (
                ("three_term_stepped", "engine_specs/cars/cx9_2016_25t.toml", typed_stepped, engines.EpaCar),
                ("three_term_cvt", "engine_specs/cars/accord_2018_15t.toml", typed_cvt, engines.CvtCar)):
            car_spec = {"_meta": {"id": "_p5-car", "kind": kind, "published": file}, "car": typed,
                        "scenario": scenario}
            with self.subTest(kind=kind), _probe_plant("_p5_epa", spec, car_spec):
                c = engines.build_candidate("_p5_epa", vals)
                self.assertIs(type(c.car), cls)
                conv = engines.published_car(file, kind)
                self.assertEqual({k: getattr(c.car, k) for k in conv}, conv)
                with_mass = dict(car_spec, car=dict(typed, mass=2000.0))     # a converted field, typed: refused
                with _probe_plant("_p5_epa", spec, with_mass), self.assertRaises(ValueError):
                    engines.build_candidate("_p5_epa", vals)

    def test_calibrated_and_trainable(self):
        """Decision 47: only the B58 may train or be scored. Amendment B7: whether a
        plant can be built from its files, and fingerprint.py's refusal by name."""
        import engines
        import fingerprint as FP
        self.assertEqual(engines.trainable(), ("b58",))
        self.assertTrue(set(engines.trainable()) <= set(engines.known()))
        self.assertTrue(engines.calibrated("b58"))
        FP.refuse_uncalibrated("b58")                       # the control: no exit
        spec, _ = _epa_probe(engines.get("b58"))
        spec = dict(spec, _meta=dict(spec["_meta"], derived=_probe_derived("_p5_probe"),
                                     freeze="results/EPA_CALIBRATION/_p5_probe/freeze.json"))
        with _probe_plant("_p5_epa", spec):
            self.assertFalse(engines.calibrated("_p5_epa"))
            with self.assertRaises(SystemExit) as cm:
                FP.refuse_uncalibrated("_p5_epa")
            msg = str(cm.exception)
            self.assertIn("'_p5_epa' is not calibrated yet", msg)
            self.assertIn("calibrate_epa.py fit --engine _p5_probe, then e6, complete and check", msg)
        # an EPA engine's derived file without its freeze record is not calibrated either
        with _probe_plant("_p5_epa", dict(spec, _meta=dict(spec["_meta"], derived="data/derived_params.json"))):
            self.assertFalse(engines.calibrated("_p5_epa"))
        with self.assertRaises(TypeError):
            engines.calibrated(None)

    # ---- build step 2 P6 (22 October 2026): the six EPA specs and the registration

    def test_the_epa_plants_are_registered_and_not_calibrated(self):
        """PLAN.md WP1 P6: the three EPA plants are registered, each with its engine
        spec and its car spec, and none is calibrated: calibrated() says no and
        names the derived file, then the freeze record, as missing; get() refuses
        each with the command that makes its file, and caches nothing; typed_engine
        refuses each by its DERIVED cycle fields; trainable() is still the B58
        alone (decision 47). Built as a candidate from the B58's values for the EPA
        set's DERIVED fields (numbers that only let the records build; nothing is
        run, no EPA row is read), each plant holds every value its specs type, by
        the record field of that name (mistake 25), and name_of names it by its
        specs. The tests above that walk the registry read specs only, so they
        cover these three too; one that builds what it finds skips an uncalibrated
        plant by name (test_plant_guards.DerivedFingerprint). Each plant's checks
        are skipped by name once its calibration has written one of its files
        (uncalibrated_or_skip; P7, the review of P6), and the next test shows it."""
        import derived
        import engines
        epa = {"mazda_25t": "cx9_2016", "honda_l15b7": "accord_2018", "ford_27tt": "f150_2015"}
        self.assertEqual(engines.known(), sorted(["b58"] + list(epa)))
        self.assertEqual({n: engines.PLANTS[n] for n in epa}, {n: (n, c) for n, c in epa.items()})
        self.assertEqual(engines.trainable(), ("b58",))
        self.assertEqual(engines._missing_files("b58"), [])
        p = engines.get("b58")
        vals = {}
        for (rec, f), (sec, key) in engines.EPA_DERIVED_FIELDS.items():
            v = [] if rec == "car" else getattr(getattr(p.engine, rec), f)
            if rec == "car":
                vals[sec] = v
            else:
                vals.setdefault(sec, {})[key] = list(v) if isinstance(v, tuple) else v
        refusal = r"\[cycle\] \w+ is DERIVED: .* needs engines.get, not typed_engine"
        for name, car_spec in epa.items():
            with self.subTest(plant=name):
                uncalibrated_or_skip(self, name)
                rel = os.path.relpath(derived.engine_path(name), HERE).replace(os.sep, "/")
                self.assertFalse(engines.calibrated(name))
                self.assertEqual(engines._missing_files(name), [rel, f"results/EPA_CALIBRATION/{name}/freeze.json"])
                with self.assertRaises(FileNotFoundError) as cm:
                    engines.get(name)
                self.assertIn(f"python calibrate_epa.py fit --engine {name}, then e6, complete and check",
                              str(cm.exception))
                self.assertNotIn(name, engines._BUILT)
                with self.assertRaisesRegex(ValueError, refusal):
                    engines.typed_engine(name)
                c = engines.build_candidate(name, vals)
                self.assertEqual(engines.name_of(c), name)
                self.assertEqual(c.engine.derived, rel)
                self.assertEqual(c.engine.thermal.fuel_lhv_j_per_kg, c.engine.fuel.lhv_j_per_kg)
                for spec, holder in ((name, c.engine), (car_spec, c)):
                    for sec, d in engines.read_spec(spec).items():
                        if sec == "_meta":
                            continue
                        rec = getattr(holder, sec)
                        for f, v in d.items():
                            got = getattr(rec, f)
                            self.assertEqual((type(got), got), (type(v), v), f"{spec} [{sec}] {f}")

    def test_the_uncalibrated_checks_skip_once_a_calibration_writes_a_file(self):
        """P7 (22 October 2026; the review of P6): the two checks of P6's
        uncalibrated plants, the one above and the listing's below, skip a plant by
        name once its calibration has written one of its files, and fail nothing.
        Run here as the real test methods, with the Mazda's spec naming as its
        derived file one that exists (a temporary file: nothing under data/ is
        written): each reports the Mazda's subtest skipped, by name, and no failure
        or error, so the Honda and the Ford are still checked. The control
        (mistake 12): with the spec as it is, the same runs skip only the plants
        whose files exist -- none, until WP4 writes one, which this control then
        expects rather than failing on."""
        from unittest import mock
        import engines
        real = engines.read_spec
        methods = ("test_the_epa_plants_are_registered_and_not_calibrated",
                   "test_the_listing_names_an_uncalibrated_plant_instead_of_stopping")
        already = {n for n in ("mazda_25t", "honda_l15b7", "ford_27tt") if calibration_files_written(n)}
        with tempfile.TemporaryDirectory() as tmp:
            written = os.path.join(tmp, "derived_params.json")
            with open(written, "w", encoding="utf-8") as fh:
                fh.write("{}")

            def read(name):
                s = real(name)
                return dict(s, _meta=dict(s["_meta"], derived=written)) if name == "mazda_25t" else s
            for patched in (True, False):
                for method in methods:
                    with self.subTest(method=method, written=patched):
                        result = unittest.TestResult()
                        with contextlib.ExitStack() as stack:
                            if patched:
                                stack.enter_context(mock.patch.object(engines, "read_spec", side_effect=read))
                            type(self)(method).run(result)
                        self.assertEqual((result.failures, result.errors), ([], []))
                        reasons = [r for _, r in result.skipped]
                        self.assertEqual(sorted(r.split(":")[0] for r in reasons),
                                         sorted(already | ({"mazda_25t"} if patched else set())), reasons)
                        if patched:
                            self.assertTrue(any(r.startswith(f"mazda_25t: its calibration has written {written}")
                                                for r in reasons), reasons)

    def test_missing_files_names_the_freeze_record_once_the_file_exists(self):
        """_missing_files, which calibrated() and the listing read: a derived file
        present and its freeze record absent names the freeze record alone; both
        present, nothing (the control: calibrated() then says yes)."""
        import engines
        spec, _ = _epa_probe(engines.get("b58"))
        with tempfile.TemporaryDirectory() as tmp:
            d, f = os.path.join(tmp, "derived_params.json"), os.path.join(tmp, "freeze.json")
            with open(d, "w", encoding="utf-8") as fh:
                fh.write("{}")
            with _probe_plant("_p6_epa", dict(spec, _meta=dict(spec["_meta"], derived=d, freeze=f))):
                self.assertEqual(engines._missing_files("_p6_epa"), [f])
                self.assertFalse(engines.calibrated("_p6_epa"))
                with open(f, "w", encoding="utf-8") as fh:
                    fh.write("{}")
                self.assertEqual(engines._missing_files("_p6_epa"), [])
                self.assertTrue(engines.calibrated("_p6_epa"))
        with self.assertRaises(TypeError):
            engines._missing_files(None)

    def test_the_listing_names_an_uncalibrated_plant_instead_of_stopping(self):
        """`python engines.py` (PLAN.md WP1 P6): the B58's line as before, and each
        EPA plant "not calibrated yet (no <its derived file>)", exit 0; an EPA
        plant's line is skipped by name once its calibration has written one of
        its files (uncalibrated_or_skip; P7, the review of P6). The control
        (mistake 12): with _missing_files made to say nothing is missing, the same
        listing reaches engines.get and dies in derived.py, so the lines above are
        the check's, not luck."""
        import derived
        import engines
        env = dict(os.environ, OMP_NUM_THREADS="1", MKL_NUM_THREADS="1")
        p = subprocess.run([sys.executable, "-B", "engines.py"], cwd=HERE, capture_output=True, text=True,
                           timeout=600, env=env)
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        got = p.stdout.splitlines()
        self.assertEqual(len(got), 4, p.stdout)
        b58 = engines.get("b58")
        self.assertEqual(got[0], f"b58    {b58.id}   engine_sha {engines.engine_sha(b58)}   derived "
                                 f"{b58.engine.derived}")
        for line, n in zip(got[1:], ("ford_27tt", "honda_l15b7", "mazda_25t")):
            with self.subTest(plant=n):
                uncalibrated_or_skip(self, n)
                e, c = engines.PLANTS[n]
                rel = os.path.relpath(derived.engine_path(n), HERE).replace(os.sep, "/")
                self.assertEqual(line, f"{n:6s} {engines.read_spec(e)['_meta']['id']}/"
                                       f"{engines.read_spec(c)['_meta']['id']}   not calibrated yet (no {rel})")
        code = ("import sys\nsys.path.insert(0, {here!r})\nsrc = open({path!r}, encoding='utf-8').read()\n"
                "src = src.replace('missing = _missing_files(n)', 'missing = []')\n"
                "assert 'missing = []' in src\n"
                "exec(compile(src, {path!r}, 'exec'), {{'__name__': '__main__', '__file__': {path!r}}})\n"
                ).format(here=HERE, path=os.path.join(HERE, "engines.py"))
        q = subprocess.run([sys.executable, "-B", "-c", code], cwd=HERE, capture_output=True, text=True,
                           timeout=600, env=env)
        self.assertNotEqual(q.returncode, 0, q.stdout + q.stderr)
        self.assertIn("FileNotFoundError", q.stderr)
        self.assertNotIn("not calibrated yet", q.stdout)


class FrozenFiles(unittest.TestCase):
    def test_drive_c_analysis_cannot_run_on_this_tree(self):
        """The four frozen files are exempt from the scans only because they
        cannot run here: plant_check, which stages A, B and C call before they
        read anything, must stop (the review of 21 October 2026: it was said to
        refuse on a plant_sha mismatch, and stops before reaching it). If it ever
        runs through, the exemption is no longer safe and this fails."""
        import drive_c_analysis as D
        with self.assertRaises((TypeError, AttributeError, SystemExit)):
            D.plant_check()


if __name__ == "__main__":
    unittest.main(verbosity=2)
