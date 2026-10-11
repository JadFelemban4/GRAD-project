"""conditions_test.py -- the twenty agents in air they never trained in, on a hill
steep enough that protection is needed, with a speed target that keeps changing.

    python conditions_test.py --resume-all    everything missing: the check, the hills, every condition, the merge
    python conditions_test.py --calibrate     the harness check and the hills -> results/conditions_grades.json
    python conditions_test.py --condition 3   one condition -> results/conditions_test.part3.json
    python conditions_test.py --merge         the parts -> results/conditions_test.json, the table, the figure
    python conditions_test.py --gears         the baseline on each hill: rpm and gear -> results/conditions_gears.json
    python conditions_test.py --report-only   re-prints and re-draws from results/conditions_test.json
    python conditions_test.py --set runs/extremes_dt1 --hills-only   the hills on the current plant, no agents
    python conditions_test.py --set runs/extremes_dt1 --resume-all   the 8 October agents, all of it

ANOTHER AGENT SET (8 October 2026): --set points every path at that set. The
twenty of 29 September keep the paths they were published under; any other set
writes results/conditions_<set>/, results/records/conditions_<set>/ and
results/figures/conditions_test_<set>.png. For the agents of the 8 October
design (decision 12) this test is the TRANSFER test: they trained on ambients of
25-45 C and hills to 18 %, so 50 C and the 25 C condition's hill (21.75 % on the
plant of 29 September) are held out, and the hills are fixed on the current plant
with --hills-only BEFORE any of them trains. The harness check, which needs the
agents' committed scores, then runs first in --resume-all. For X2 (runs/
wideair_dt1, 11 October: ambient 0-45 C and 80-101.3 kPa in training) the held-out
conditions are 50 C, 76 kPa and the 25 C hill; this test's altitude is milder
than X2's training in one more way, its gearbox kicking down on the sea-level
table (PREREGISTRATION_X2.md 5e).

ABOUT TWO AND A HALF HOURS on 18 workers of the 20-thread team laptop, longer
than one task in a Claude session may run, so --resume-all is meant to be
started in its own window; every condition is saved as it finishes.

A DIAGNOSTIC BESIDE THE PROTOCOL, NEVER A CHANGE TO IT (7 October 2026, asked
by Ghassan before the team chooses how the next agents are trained). Every
agent of runs/terrain_dt1 trained, and was scored, at 42 C and 101.3 kPa and at
a constant 130 km/h: ambient and pressure are INPUTS of its observation
(engine_env._obs), and all three were constant for all 50 000 steps. So the
network never learned what any of them means. This measures what it does when
they change:

    ambient   25, 35, 50 C at 101.3 kPa
    pressure  90, 82 (about Taif's altitude), 76 kPa (the climb's top) at 42 C
    and the trained air, 42 C at 101.3 kPa

THE SPEED TARGET CHANGES DURING THE RUN (Ghassan, 7 October: "speed will vary,
not a static value; even mid-run it has a target and the agent will try to
match it"). The car follows SPEED_STEPS: the locked climb's launch to 130 km/h,
then a new target every one to two minutes between 110 and 145 km/h, reached
at no more than 0.8 m/s^2. The driver model turns each target, its
acceleration and the grade into a torque request; delivering that torque is
the reward's tracking term, so an agent that protects by refusing torque is
seen (the 'short' column). The same profile is used for every condition,
policy and episode, so every comparison is paired.

EACH CONDITION GETS ITS OWN HILL (Ghassan, 7 October: "make it so that it
reaches the limit and starts to protect"). On a 12 % hill, 25 C air never
reaches the 850 C trigger, so there is nothing to protect. So for each
condition the climb's grade is searched from 6 to 30 % (beyond 13 % and beyond
13 degrees, 23 %) for the gentlest grade at which the baseline ECU, on this
speed profile, peaks at the locked climb's own severity: 883 C, 33 K over the
trigger. A coarse 1 % grid, then 0.25 % steps inside the crossing; the whole
curve of peak against grade is kept and drawn. Grades above 14 % are steeper
than any training road the agents saw: part of what is being tested.

THE HARNESS IS CHECKED FIRST: on the locked climb itself (12 %, 130 km/h, 42 C,
101.3 kPa) five agent and baseline episodes must EQUAL their committed scores.

Scored on frozen episodes 1, 5, 9, 13 and 17 (every fourth of the twenty,
fixed before any run), for the twenty agents and the four hand-written
policies, each condition against its OWN baseline ECU and, as the line every
agent is compared with, its own CURRENT-GRADE policy. Recorded for each
episode: damage, peak turbine, seconds above the trigger, torque shortfall,
and the median of each applied actuator on the climb -- what the agent DOES.

HOW PRESSURE REACHES THE ENGINE HERE, AND WHAT IS LEFT OUT. The plant never
reads the cycle's p_baro except for drag. For this test, and only in this
process, the compressor's inlet becomes p_baro * 99.3 / 101.3 (the same 2 kPa
filter loss plant.boost_ceiling_kpa assumes at sea level), so the boost
ceiling and the hard pressure cap fall with altitude, and drag uses the
thinner air. NOT modelled, so altitude here is MILDER than real: the hotter
compressor outlet at the higher pressure ratio (plant.charge_temperature has
no pressure ratio in it), the exhaust backpressure's fall, and the colder air
of a real mountain (ambient is held at 42 C to change one thing at a time).
No hashed plant file changes, so plant_sha and every certificate stand.
"""
import argparse
import concurrent.futures as cf
import json
import os
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

SET = "runs/terrain_dt1"
EPISODES = (1, 5, 9, 13, 17)                      # every fourth frozen episode
HAND = (("baseline ECU", "p_neutral"), ("current-grade", "p_grade_now"),
        ("reactive", "p_reactive"), ("predictive (hand)", "p_predictive"))
CONDITIONS = (                                    # name, ambient K, pressure kPa
    ("42 C, 101.3 kPa (trained air)", 315.0, 101.3),
    ("25 C", 298.15, 101.3),
    ("35 C", 308.15, 101.3),
    ("50 C", 323.15, 101.3),
    ("90 kPa", 315.0, 90.0),
    ("82 kPa, about Taif", 315.0, 82.0),
    ("76 kPa, the climb's top", 315.0, 76.0),
)
# (time s, new target km/h). Before the first entry: the locked climb's own
# launch, 0 -> 130 km/h over 20 s. The climb starts at 180 s.
SPEED_STEPS = ((60, 115.0), (120, 130.0), (300, 110.0), (420, 145.0), (540, 120.0), (640, 135.0))
ACCEL_MAX = 0.8                                   # m/s^2, both ways
TARGET_PEAK_C = 883.0                             # the locked climb's baseline peak
COARSE = tuple(round(g, 4) for g in np.arange(0.06, 0.3001, 0.01))
TRIGGER_C = 850.0
CHECK = (("baseline ECU", 1), ("sighted_seed0", 1), ("blind_seed3", 5), ("sighted_seed6", 9),
         ("blind_seed9", 17))
ACTS = ("spark trim, deg", "lambda trim", "boost trim, kPa", "fan duty", "pump duty")
GRADES_JSON = os.path.join(HERE, "results", "conditions_grades.json")
OUT_JSON = os.path.join(HERE, "results", "conditions_test.json")
OUT_PNG = os.path.join(HERE, "results", "figures", "conditions_test.png")


AGENTS_RESULTS = os.path.join(HERE, "results", "agents", "terrain_dt1")
PART_DIR = os.path.join(HERE, "results")
HARNESS_JSON = None                              # the 29 Sep set keeps its check in the grades file


def use_set(set_dir):
    """Point every path at one agent set; see the docstring."""
    global SET, AGENTS_RESULTS, PART_DIR, GRADES_JSON, OUT_JSON, OUT_PNG, RECORDS, GEARS_JSON, HARNESS_JSON
    SET = set_dir
    name = os.path.basename(os.path.normpath(set_dir))
    AGENTS_RESULTS = os.path.join(HERE, "results", "agents", name)
    if name == "terrain_dt1":
        return
    PART_DIR = os.path.join(HERE, "results", f"conditions_{name}")
    GRADES_JSON = os.path.join(PART_DIR, "conditions_grades.json")
    OUT_JSON = os.path.join(PART_DIR, "conditions_test.json")
    GEARS_JSON = os.path.join(PART_DIR, "conditions_gears.json")
    HARNESS_JSON = os.path.join(PART_DIR, "harness_check.json")
    OUT_PNG = os.path.join(HERE, "results", "figures", f"conditions_test_{name}.png")
    RECORDS = os.path.join(HERE, "results", "records", f"conditions_{name}")


def _part(k):
    return os.path.join(PART_DIR, f"conditions_test.part{k}.json")


# EVERY STEP OF EVERY EPISODE (7 October 2026, Ghassan: "everything from the
# environment to the actions of the agents recorded"). One .npz per condition
# and policy, its five episodes stacked, with a .json beside it naming the
# condition, the hill and the speed profile; the fields are step_record.py's.
# Gitignored, like every per-step record. Draw one with show_record.py.
RECORDS = os.path.join(HERE, "results", "records", "conditions")


def _slug(s):
    import re
    return re.sub(r"[^A-Za-z0-9.]+", "_", s).strip("_")


def _records_dir(k):
    return os.path.join(RECORDS, f"{k}_{_slug(CONDITIONS[k][0])}")


def save_records(k, recs):
    """recs[ref][episode index] -> one file per policy."""
    import evaluate as E
    import step_record
    name, t_amb, p = CONDITIONS[k]
    g = grades()[name]["grade"]
    head = step_record.git_head()
    for ref, by_ep in recs.items():
        idx = sorted(by_ep)
        hand = ref in dict(HAND)
        step_record.save(
            os.path.join(_records_dir(k), _slug(ref) + ".npz"), [by_ep[i] for i in idx],
            dict(script="conditions_test.py", commit=head, policy=ref,
                 source=("check_premise." + dict(HAND)[ref]) if hand else f"{SET}/{ref}/final.zip",
                 preview=(ref == "predictive (hand)") if hand else ("blind" not in ref),
                 condition=name, t_amb_k=t_amb, p_kpa=p, compressor_inlet_kpa=round(p * 99.3 / 101.3, 3),
                 grade=g, climb_from_s=180, profile="varying", speed_steps=SPEED_STEPS,
                 accel_max_mps2=ACCEL_MAX, dt=E.DT, duration_s=E.DURATION,
                 episodes=idx, episode_seed=[E.EPISODES[i - 1][0] for i in idx]),
            seeds=[E.EPISODES[i - 1][0] for i in idx], weights=[E.EPISODES[i - 1][1] for i in idx])
    print(f"wrote {len(recs)} records to {os.path.relpath(_records_dir(k), HERE)}", flush=True)


def _agent_tags():
    return sorted(t for t in os.listdir(os.path.join(HERE, SET))
                  if t.startswith(("sighted_seed", "blind_seed"))
                  and os.path.isfile(os.path.join(HERE, SET, t, "final.zip")))


def _records_done(k):
    d = _records_dir(k)
    want = len(HAND) + len(_agent_tags())
    return os.path.isdir(d) and len([f for f in os.listdir(d) if f.endswith(".npz")]) >= want


def speed_profile(locked_v_mps, dt):
    """The varying target, from the locked climb's own array (its launch kept)."""
    v = np.array(locked_v_mps, dtype=float)
    target = v[int(20 / dt)]
    steps = dict((int(t / dt), kmh / 3.6) for t, kmh in SPEED_STEPS)
    for k in range(int(20 / dt), len(v)):
        target = steps.get(k, target)
        prev = v[k - 1]
        v[k] = prev + float(np.clip(target - prev, -ACCEL_MAX * dt, ACCEL_MAX * dt))
    return v


# ---------------------------------------------------------------- one episode
_MODELS = {}


def _init_worker(set_dir=None):
    """Each worker re-imports this module, so it must be told the agent set:
    without it every worker loaded runs/terrain_dt1's agent of the same name
    (9 October 2026, X1's first harness check; the check caught it)."""
    if set_dir:
        use_set(set_dir)
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass


def _policy(ref):
    import check_premise as C
    import evaluate as E
    if ref in dict(HAND):
        return getattr(C, dict(HAND)[ref]), True
    from stable_baselines3 import SAC
    if ref not in _MODELS:
        _MODELS[ref] = SAC.load(os.path.join(HERE, SET, ref, "final"), device="cpu")
    return E.agent_policy(_MODELS[ref]), "blind" not in ref


def _episode(job):
    return _run(job)


def _episode_recorded(job):
    """The same episode with every step recorded (step_record.py)."""
    import step_record
    rec = step_record.new()
    job, row = _run(job, rec)
    return job, row, step_record.finish(rec)


def _run(job, rec=None):
    """evaluate.run_episode, step for step, on a climb of this grade in this
    ambient and pressure, the compressor inlet following the pressure, on the
    varying speed profile (or, for the harness check, the locked one). `rec`,
    if given, receives every step; it only reads."""
    ref, idx, t_amb, p_baro, grade, profile = job
    import engine_env as EE
    import evaluate as E
    import plant
    import step_record
    p_inlet = p_baro * 99.3 / 101.3

    def ceiling(mdot_air_gps, t_inlet_k=298.0, _p=p_inlet):
        return plant.boost_ceiling_kpa(mdot_air_gps, t_inlet_k, _p)
    EE.boost_ceiling_kpa = ceiling                # this worker process only

    class Env(EE.SupervisoryTunerEnv):
        @property
        def MAP_CEIL_KPA(self):
            return p_inlet * float(plant.boost_ceiling_constants()["pr_cap"])

    policy, preview = _policy(ref)
    seed, weights = E.EPISODES[idx - 1]
    cycle = EE.make_grade_climb(duration=E.DURATION, dt=E.DT, t_amb=t_amb, grade=grade)
    cycle["p_baro"] = p_baro
    if profile == "varying":
        cycle["v_mps"] = speed_profile(cycle["v_mps"], E.DT)
    env = Env(cycle, dt=E.DT, seed=seed, use_preview=preview)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    ret, peak, thermal, short, above = 0.0, 0.0, 0.0, 0, 0
    applied = []
    while True:
        k = env.k
        a = policy(env, obs)
        obs_before = obs
        obs, r, term, trunc, info = env.step(a)
        if rec is not None:
            step_record.step(rec, env, a, obs_before, r, info)
        ret += r
        peak = max(peak, info["t_turb"])
        thermal += EE.damage_rate(info["t_turb"], info["t_oil"]) * env.dt
        short += int(info["torque"] < 0.95 * info["torque_req"])
        above += int(info["t_turb"] - 273.15 > TRIGGER_C)
        if cycle["grade"][k] > 0:
            applied.append(np.array(env.prev_act, dtype=float))
        if term or trunc:
            break
    s = info["episode_summary"]
    acts = np.median(np.array(applied), axis=0) if applied else np.full(5, np.nan)
    return job, dict(ret=ret, damage=s["damage"], damage_thermal=thermal, fuel=s["fuel"],
                     torque_viol=s["torque_viol"], peak_turb=peak - 273.15,
                     knock=s["knock_events"], short_steps=short, s_above=above * env.dt,
                     act_climb=[round(float(v), 4) for v in acts])


# ---------------------------------------------------------------- check and hills
def harness_check(workers):
    """Five agent and baseline episodes on the locked climb must EQUAL their
    committed scores (results/agents/<set>/<policy>/eval_summary.json)."""
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(SET,)) as pool:
        check = dict(pool.map(_episode, [(ref, i, 315.0, 101.3, 0.12, "locked") for ref, i in CHECK]))
    bad = []
    for (ref, i, *_), row in check.items():
        folder = ref.replace(" ", "_") if ref in dict(HAND) else ref
        with open(os.path.join(AGENTS_RESULTS, folder, "eval_summary.json"), encoding="utf-8") as fh:
            want = json.load(fh)["episodes"][i - 1]
        bad += [(ref, i, k, row[k], want[k]) for k in ("ret", "damage", "damage_thermal", "fuel",
                                                       "torque_viol", "peak_turb", "knock")
                if row[k] != want[k]]
    print(f"harness check on the locked climb: {len(check)} episodes against their committed scores -- "
          f"{'all identical' if not bad else f'{len(bad)} DIFFER: {bad[:3]}'}", flush=True)
    if bad:
        raise SystemExit("the harness does not reproduce evaluate.py; nothing else is run")
    return {"episodes": len(check), "identical": True}


def calibrate(workers, harness=True):
    """The harness check on the locked climb (unless `harness` is False: a set
    whose agents have not trained yet), then for each condition the gentlest
    grade at which the baseline ECU, on the varying speed profile, peaks at
    TARGET_PEAK_C, with the whole curve of peak against grade."""
    def run(jobs):
        with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init_worker, initargs=(SET,)) as pool:
            return dict(pool.map(_episode, jobs))

    out = {"harness_check": harness_check(workers) if harness else None,
           "speed_steps": SPEED_STEPS, "accel_max": ACCEL_MAX, "target_peak_c": TARGET_PEAK_C}
    if not harness:
        import fingerprint as FP
        out["fixed_before_training"] = dict(set=SET, plant_sha=FP.plant_fingerprint()["plant_sha"],
                                            derived_sha=FP.derived_sha())
    for name, t_amb, p in CONDITIONS:
        print(f"hill for {name}: coarse grid", flush=True)
        res = run([("baseline ECU", 1, t_amb, p, g, "varying") for g in COARSE])
        curve = {job[4]: row["peak_turb"] for job, row in res.items()}
        hit = [g for g in COARSE if curve[g] >= TARGET_PEAK_C - 0.5]
        if not hit:
            out[name] = dict(grade=None, curve={str(g): round(v, 2) for g, v in sorted(curve.items())},
                             note="never reaches the target within 30 %")
            print(f"   never reaches {TARGET_PEAK_C:.0f} C up to 30 %", flush=True)
            continue
        g0 = round(hit[0] - 0.01, 4)
        if g0 >= COARSE[0]:
            res = run([("baseline ECU", 1, t_amb, p, round(g0 + d, 4), "varying")
                       for d in (0.0025, 0.005, 0.0075)])
            curve.update({job[4]: row["peak_turb"] for job, row in res.items()})
        grade = min(g for g in curve if curve[g] >= TARGET_PEAK_C - 0.5)
        out[name] = dict(grade=grade, peak=round(curve[grade], 2),
                         curve={str(g): round(v, 2) for g, v in sorted(curve.items())})
        print(f"   grade {grade * 100:.2f} %, baseline peak {curve[grade]:.1f} C", flush=True)
    os.makedirs(os.path.dirname(GRADES_JSON), exist_ok=True)
    with open(GRADES_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(GRADES_JSON, HERE)}", flush=True)


def grades():
    with open(GRADES_JSON, encoding="utf-8") as fh:
        return json.load(fh)


GEARS_JSON = os.path.join(HERE, "results", "conditions_gears.json")


def _gears(job):
    """The baseline ECU on one condition's hill: engine speed and the gear the
    box chose, per stretch of the speed target. The peak-against-grade curves
    drop wherever the box kicks down (a lower gear, more rpm, less load per
    cycle, a cooler exhaust), so two conditions' hills can sit in different
    gears; this says which."""
    name, t_amb, p_baro, grade = job
    import check_premise as C
    import engine_env as EE
    import evaluate as E
    import plant
    p_inlet = p_baro * 99.3 / 101.3
    EE.boost_ceiling_kpa = lambda m, t=298.0, _p=p_inlet: plant.boost_ceiling_kpa(m, t, _p)

    class Env(EE.SupervisoryTunerEnv):
        @property
        def MAP_CEIL_KPA(self):
            return p_inlet * float(plant.boost_ceiling_constants()["pr_cap"])
    seed, weights = E.EPISODES[0]
    cycle = EE.make_grade_climb(duration=E.DURATION, dt=E.DT, t_amb=t_amb, grade=grade)
    cycle["p_baro"] = p_baro
    cycle["v_mps"] = speed_profile(cycle["v_mps"], E.DT)
    env = Env(cycle, dt=E.DT, seed=seed, use_preview=True)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    rows = []
    while True:
        obs, _, term, trunc, info = env.step(C.p_neutral(env, obs))
        rows.append((env.k - 1, env.rpm, env.v, env.map_kpa, info["t_turb"] - 273.15))
        if term or trunc:
            break
    ratios = np.array(EE.Vehicle.gears) * EE.Vehicle.final_drive
    out = []
    edges = [180] + [t for t, _ in SPEED_STEPS if t > 180] + [len(rows)]
    for lo, hi in zip(edges[:-1], edges[1:]):
        seg = [r for r in rows if lo + 15 <= r[0] < hi]          # past the ramp into the stretch
        if not seg:
            continue
        rpm = float(np.median([r[1] for r in seg]))
        v = float(np.median([r[2] for r in seg]))
        wheel_rpm = v / (2 * np.pi * EE.Vehicle.wheel_r) * 60.0 if v > 1.0 else None
        gear = (int(np.argmin(np.abs(ratios - rpm / wheel_rpm))) + 1) if wheel_rpm else None
        out.append(dict(t_from=lo, kmh=round(v * 3.6, 1), rpm=round(rpm), gear=gear,
                        map_kpa=round(float(np.median([r[3] for r in seg])), 1),
                        turb_c=round(float(np.max([r[4] for r in seg])), 1)))
    return name, out


def gears_report(workers):
    hills = grades()
    jobs = [(name, t, p, hills[name]["grade"]) for name, t, p in CONDITIONS if hills[name]["grade"] is not None]
    with cf.ProcessPoolExecutor(max_workers=min(workers, len(jobs)), initializer=_init_worker, initargs=(SET,)) as pool:
        res = dict(pool.map(_gears, jobs))
    print("the baseline ECU on each hill: per stretch of the speed target, engine speed (gear) and the hottest turbine")
    for name, segs in res.items():
        cells = "  ".join(f"{s['kmh']:.0f} km/h {s['rpm']} rpm (g{s['gear']}) {s['turb_c']:.0f}C" for s in segs)
        print(f"  {name:32s} {hills[name]['grade'] * 100:5.2f} %  {cells}")
    with open(GEARS_JSON, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(GEARS_JSON, HERE)}")


# ---------------------------------------------------------------- analysis
def summarise(rows):
    """Per condition: the baseline, current-grade, and each agent's margin over
    current-grade in points of cut against that condition's own baseline."""
    from scipy import stats
    hills = grades()
    out = {}
    tags = sorted({key[0] for key in rows if key[0] not in dict(HAND)})
    for name, t_amb, p in CONDITIONS:
        g = hills[name]["grade"]
        if g is None:
            out[name] = dict(grade=None)
            continue
        key = lambda ref, i: (ref, i, t_amb, p, g)

        def med(ref, k="damage"):
            return float(np.median([rows[key(ref, i)][k] for i in EPISODES]))
        base = med("baseline ECU")
        refs = [h for h, _ in HAND] + tags
        cut = {ref: 100 * (1.0 - med(ref) / base) for ref in refs}
        margin = {ref: cut[ref] - cut["current-grade"] for ref in refs}
        seeds = sorted({int(t.split("seed")[1]) for t in tags})
        diff = np.array([cut[f"sighted_seed{s}"] - cut[f"blind_seed{s}"] for s in seeds])
        half = float(stats.t.ppf(0.975, len(diff) - 1)) * diff.std(ddof=1) / np.sqrt(len(diff))

        def act_med(group):
            arr = np.array([rows[key(ref, i)]["act_climb"] for ref in group for i in EPISODES])
            return [round(float(v), 3) for v in np.nanmedian(arr, axis=0)]
        sighted = [t for t in tags if t.startswith("sighted")]
        blind = [t for t in tags if t.startswith("blind")]
        worst = max(((t, i) for t in tags for i in EPISODES), key=lambda ti: rows[key(*ti)]["peak_turb"])
        # Each agent's own spark trim on the climb (median over its episodes).
        # The group medians alone read "+3 to +4 everywhere" (8 October), and
        # hid the agents that retard -- the ones that fail at 25 C.
        spark = {t: float(np.median([rows[key(t, i)]["act_climb"][0] for i in EPISODES])) for t in tags}
        out[name] = dict(
            grade=g, t_amb_c=round(t_amb - 273.15, 2), p_kpa=p,
            base_damage=round(base, 1), base_peak=round(med("baseline ECU", "peak_turb"), 1),
            base_s_above=med("baseline ECU", "s_above"),
            grade_cut=round(cut["current-grade"], 2), grade_peak=round(med("current-grade", "peak_turb"), 1),
            grade_s_above=med("current-grade", "s_above"),
            sighted_margin=round(float(np.median([margin[t] for t in sighted])), 2),
            blind_margin=round(float(np.median([margin[t] for t in blind])), 2),
            margin_min=round(min(margin[t] for t in tags), 2), margin_max=round(max(margin[t] for t in tags), 2),
            beat_grade=int(sum(margin[t] > 0 for t in tags)), n_agents=len(tags),
            beat_base=int(sum(cut[t] > 0 for t in tags)),
            agents_s_above=float(np.median([rows[key(t, i)]["s_above"] for t in tags for i in EPISODES])),
            agents_peak_max=round(rows[key(*worst)]["peak_turb"], 1), worst=list(worst),
            ablation_mean=round(float(diff.mean()), 2),
            ablation_lo=round(float(diff.mean() - half), 2), ablation_hi=round(float(diff.mean() + half), 2),
            short_max=int(max(rows[key(ref, i)]["short_steps"] for ref in refs for i in EPISODES)),
            short_agents_median=float(np.median([rows[key(t, i)]["short_steps"] for t in tags for i in EPISODES])),
            short_base=int(max(rows[key("baseline ECU", i)]["short_steps"] for i in EPISODES)),
            # Current-grade pulls boost by about 10 kPa on any grade; where that
            # leaves it short of the torque asked for, part of its cut is not
            # protection, and as a yardstick it flatters itself.
            short_grade=float(np.median([rows[key("current-grade", i)]["short_steps"] for i in EPISODES])),
            acts_sighted=act_med(sighted), acts_blind=act_med(blind),
            acts_grade=act_med(["current-grade"]), acts_base=act_med(["baseline ECU"]),
            spark_by_agent={t: round(v, 2) for t, v in spark.items()},
            spark_under3=int(sum(v < 3.0 for v in spark.values())),
            spark_retard=sorted(([t, round(v, 2)] for t, v in spark.items() if v < 0.0), key=lambda x: x[1]),
            margins={t: round(margin[t], 2) for t in tags}, cuts={k_: round(v, 2) for k_, v in cut.items()})
    return out


def report(summary, hills):
    hc = hills.get("harness_check")
    if hc is None and HARNESS_JSON and os.path.isfile(HARNESS_JSON):
        # A set whose hills were fixed before it trained keeps its check beside them.
        with open(HARNESS_JSON, encoding="utf-8") as fh:
            hc = json.load(fh)
    if hc is None:
        print("harness check: NOT RUN for this set")
    else:
        print(f"harness check: {hc.get('episodes')} episodes on the locked climb "
              + ("equal their committed scores" if hc.get("identical", True) else "DIFFER from their committed scores"))
    print("speed target, km/h: 130 from the launch, then " + ", ".join(
        f"{kmh:.0f} at {t} s" for t, kmh in SPEED_STEPS) + f" (at most {ACCEL_MAX} m/s^2); climb from 180 s")
    print("\neach condition on its own hill (the grade where the baseline peaks at "
          f"{TARGET_PEAK_C:.0f} C); margins in points of cut over CURRENT-GRADE, median over episodes "
          + ", ".join(map(str, EPISODES)))
    print(f"{'condition':30s} {'grade %':>7s} {'base pk':>7s} {'grade cut':>9s} {'s>850 grade':>11s} "
          f"{'sighted':>8s} {'blind':>7s} {'agents min..max':>16s} {'>grade':>7s} {'s>850 agents':>12s} "
          f"{'hottest agent':>24s} {'ablation [95 %]':>22s} {'short base/grade/agents/max':>28s}")
    for name, s in summary.items():
        if s.get("grade") is None:
            print(f"{name:30s}   never reaches {TARGET_PEAK_C:.0f} C up to 30 %")
            continue
        w = f"{s['worst'][0]} ep{s['worst'][1]} {s['agents_peak_max']:.0f}C"
        print(f"{name:30s} {s['grade'] * 100:7.2f} {s['base_peak']:7.1f} {s['grade_cut']:9.1f} "
              f"{s['grade_s_above']:11.0f} {s['sighted_margin']:+8.1f} {s['blind_margin']:+7.1f} "
              f"{s['margin_min']:+7.1f}..{s['margin_max']:<+7.1f} {s['beat_grade']:3d}/{s['n_agents']:<3d} "
              f"{s['agents_s_above']:12.0f} {w:>24s} {s['ablation_mean']:+6.1f} "
              f"[{s['ablation_lo']:+5.1f},{s['ablation_hi']:+5.1f}] "
              f"{s['short_base']:6d}/{s['short_grade']:5.0f}/{s['short_agents_median']:5.0f}/{s['short_max']:<5d}")
    print("\nwhat they do on the climb (median applied actuator): sighted / blinded / current-grade / baseline")
    for name, s in summary.items():
        if s.get("grade") is None:
            continue
        cells = "  ".join(f"{a.split(',')[0]} {s['acts_sighted'][j]:+.2f}/{s['acts_blind'][j]:+.2f}/"
                          f"{s['acts_grade'][j]:+.2f}/{s['acts_base'][j]:+.2f}" for j, a in enumerate(ACTS))
        print(f"  {name:30s} {cells}")
    import engine_env as EE
    sparks = [v for s in summary.values() if s.get("grade") is not None
              for v in s.get("spark_by_agent", {}).values()]
    capped = bool(sparks) and EE.SPARK_TRIM_MAX < 4.0 and max(sparks) <= EE.SPARK_TRIM_MAX + 1e-6
    print("\neach agent's own spark trim on the climb (median of its episodes): "
          + (f"advance is forbidden for this set (cap {EE.SPARK_TRIM_MAX:+.0f} deg), so only which retard"
             if capped else "how many sit under +3 deg, and which retard"))
    for name, s in summary.items():
        if s.get("grade") is None or "spark_under3" not in s:
            continue
        retard = ", ".join(f"{t} {v:+.2f}" for t, v in s["spark_retard"]) or "none"
        if capped:
            print(f"  {name:30s} retarding: {len(s['spark_retard']):2d} of {s['n_agents']}: {retard}")
        else:
            print(f"  {name:30s} under +3: {s['spark_under3']:2d} of {s['n_agents']}   retarding: {retard}")
    print("\n'short' = steps (of 719) delivering under 95 % of the torque asked for: the baseline's most, "
          "current-grade's median, the agents' median, any policy's most; 's>850' = seconds with the "
          "turbine housing above the trigger. Where current-grade is short for many steps, its cut is "
          "partly not protection, and the margins over it understate the agents")


def figure(summary, hills):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import engine_env as EE
    import evaluate as E
    names = [n for n in summary if summary[n].get("grade") is not None]
    x = np.arange(len(names))
    labels = [f"{n.split(',')[0]}\n{summary[n]['grade'] * 100:.1f} %" for n in names]
    labels_short = [f"{lab}\ncg short {summary[n].get('short_grade', 0):.0f}" for lab, n in zip(labels, names)]
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    a = axes[0, 0]
    locked = EE.make_grade_climb(duration=E.DURATION, dt=E.DT)
    v = speed_profile(locked["v_mps"], E.DT) * 3.6
    a.plot(locked["t"], v, color="#2a78d6", lw=1.6, label="speed target, km/h")
    a.plot(locked["t"], locked["v_mps"] * 3.6, color="#9aa0a4", lw=1, ls="--", label="the locked climb, 130 km/h")
    a.axvspan(180, locked["t"][-1], color="#e4e7e3", zorder=0, label="the climb (its grade per condition)")
    a.set_xlabel("time, s"); a.set_ylabel("km/h"); a.set_ylim(0, 160)
    a.set_title("The speed the car is asked to hold", fontsize=10); a.legend(fontsize=8, loc="lower right")
    a = axes[0, 1]
    for name, _, _ in CONDITIONS:
        c = hills[name]["curve"]
        keys = sorted(c, key=float)
        a.plot([float(k) * 100 for k in keys], [c[k] for k in keys], "-", lw=1.4, label=name.split(",")[0])
    a.axhline(TARGET_PEAK_C, color="#4b5157", ls="--", lw=1, label=f"{TARGET_PEAK_C:.0f} C, the locked climb's peak")
    a.axhline(TRIGGER_C, color="#d03b3b", ls=":", lw=1, label="850 C trigger")
    a.set_xlabel("climb grade, %"); a.set_ylabel("baseline ECU, peak turbine, C")
    a.set_title("Finding each condition's hill", fontsize=10); a.legend(fontsize=7)
    a = axes[1, 0]
    for k, name in enumerate(names):
        m = summary[name]["margins"]
        sig = [val for t, val in m.items() if t.startswith("sighted")]
        bli = [val for t, val in m.items() if t.startswith("blind")]
        a.scatter(np.full(len(sig), k - 0.12), sig, s=14, color="#4a3aa7", alpha=0.8,
                  label="trained, sighted" if k == 0 else None)
        a.scatter(np.full(len(bli), k + 0.12), bli, s=14, color="#e87ba4", alpha=0.8,
                  label="trained, blinded" if k == 0 else None)
    a.axhline(0, color="#1baf7a", lw=2, label="current-grade, hand-written")
    a.set_xticks(x, labels_short, fontsize=7.5)
    a.set_ylabel("points of cut over current-grade")
    a.set_title("Each agent against current-grade (cg short: its steps short of torque, of 719)", fontsize=10)
    a.legend(fontsize=7.5, loc="lower right")
    a = axes[1, 1]
    sparks = [v for n in names for v in summary[n].get("spark_by_agent", {}).values()]
    if sparks and EE.SPARK_TRIM_MAX < 4.0 and max(sparks) <= EE.SPARK_TRIM_MAX + 1e-6:
        # A set trained with advance forbidden: every arm's median is the cap, so
        # bars would show nothing. Each agent's own median instead, which shows
        # who retards.
        for k, name in enumerate(names):
            sp = summary[name]["spark_by_agent"]
            sig = [val for t, val in sp.items() if t.startswith("sighted")]
            bli = [val for t, val in sp.items() if t.startswith("blind")]
            a.scatter(np.full(len(sig), k - 0.12), sig, s=14, color="#4a3aa7", alpha=0.8,
                      label="sighted, each agent" if k == 0 else None)
            a.scatter(np.full(len(bli), k + 0.12), bli, s=14, color="#e87ba4", alpha=0.8,
                      label="blinded, each agent" if k == 0 else None)
        a.axhline(EE.SPARK_TRIM_MAX, color="#d03b3b", ls=":", lw=1,
                  label=f"{EE.SPARK_TRIM_MAX:+.0f} deg, the cap")
        a.set_ylim(min(sparks) - 0.6, EE.SPARK_TRIM_MAX + 1.4)
        a.set_ylabel("each agent's median spark trim on the climb, deg")
        a.set_title("Spark, advance forbidden: below 0 is retard (current-grade and baseline hold 0)", fontsize=10)
        a.legend(fontsize=7.5, loc="upper center", ncol=3)
    else:
        w = 0.2
        for j, (key, lab, col) in enumerate((("acts_sighted", "sighted", "#4a3aa7"), ("acts_blind", "blinded", "#e87ba4"),
                                              ("acts_grade", "current-grade", "#1baf7a"),
                                              ("acts_base", "baseline", "#9aa0a4"))):
            a.bar(x + (j - 1.5) * w, [summary[n][key][0] for n in names], width=w, color=col, label=lab)
        a.axhline(4.0, color="#d03b3b", ls=":", lw=1, label="+4 deg, the trim's limit")
        a.set_ylim(0, 5.0)
        a.set_ylabel("median spark trim on the climb, deg")
        a.set_title("What they do: spark (current-grade and the baseline hold 0)", fontsize=10)
        a.legend(fontsize=7.5, loc="upper center", ncol=5)
    a.set_xticks(x, labels, fontsize=7.5)
    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT_PNG), exist_ok=True)
    fig.savefig(OUT_PNG, dpi=120)
    print(f"wrote {os.path.relpath(OUT_PNG, HERE)}")


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-only", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--condition", type=int, default=None)
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--gears", action="store_true",
                    help="the baseline on each hill: engine speed and gear per stretch -> results/conditions_gears.json")
    ap.add_argument("--resume-all", action="store_true",
                    help="the check and hills if missing, every condition whose part is missing, then the "
                         "merge; safe to stop and start again")
    ap.add_argument("--workers", type=int, default=max(1, min(18, (os.cpu_count() or 2) - 2)))
    ap.add_argument("--set", default=SET, help="the agent set (default runs/terrain_dt1)")
    ap.add_argument("--hills-only", action="store_true",
                    help="the hills on the current plant, without the harness check: a set "
                         "whose agents have not trained yet")
    ap.add_argument("--harness", action="store_true",
                    help="only the harness check, written beside the set's results")
    a = ap.parse_args()
    use_set(a.set)
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    if a.hills_only:
        calibrate(a.workers, harness=False)
        return 0
    if a.harness:
        res = harness_check(a.workers)
        os.makedirs(PART_DIR, exist_ok=True)
        with open(HARNESS_JSON or GRADES_JSON + ".harness.json", "w", encoding="utf-8") as fh:
            json.dump(res, fh)
        return 0
    if a.report_only:
        with open(OUT_JSON, encoding="utf-8") as fh:
            saved = json.load(fh)
        report(saved["summary"], saved["hills"])
        figure(saved["summary"], saved["hills"])
        return 0
    if a.resume_all:
        me = [sys.executable, "-u", os.path.abspath(__file__), "--set", SET]
        if not os.path.isfile(GRADES_JSON):
            subprocess.run(me + ["--calibrate", "--workers", str(a.workers)], check=True)
        elif grades().get("harness_check") is None and not os.path.isfile(HARNESS_JSON or ""):
            subprocess.run(me + ["--harness", "--workers", str(a.workers)], check=True)
        for k in range(len(CONDITIONS)):
            if os.path.isfile(_part(k)) and (_records_done(k) or grades()[CONDITIONS[k][0]]["grade"] is None):
                print(f"condition {k} already done", flush=True)
                continue
            print(f"condition {k}: {CONDITIONS[k][0]}", flush=True)
            subprocess.run(me + ["--condition", str(k), "--workers", str(a.workers)], check=True)
        return subprocess.run(me + ["--merge"]).returncode
    if a.calibrate:
        calibrate(a.workers)
        return 0
    if a.gears:
        gears_report(a.workers)
        return 0
    tags = _agent_tags()
    hills = grades()
    rows = {}
    if a.merge:
        for k in range(len(CONDITIONS)):
            if not os.path.isfile(_part(k)):
                continue
            with open(_part(k), encoding="utf-8") as fh:
                for r in json.load(fh):
                    rows[(r.pop("ref"), r.pop("episode"), r.pop("t_amb_k"), r.pop("p_kpa"),
                          r.pop("grade"))] = r
    else:
        name, t_amb, p = CONDITIONS[a.condition]
        g = hills[name]["grade"]
        if g is None:
            with open(_part(a.condition), "w", encoding="utf-8") as fh:
                json.dump([], fh)
            print(f"{name}: no hill reaches the target; nothing to run")
            return 0
        jobs = [(ref, i, t_amb, p, g, "varying") for ref in [h for h, _ in HAND] + tags for i in EPISODES]
        print(f"{name}, grade {g * 100:.2f} %: {len(jobs)} episodes, {a.workers} workers", flush=True)
        recs = {}
        with cf.ProcessPoolExecutor(max_workers=a.workers, initializer=_init_worker, initargs=(SET,)) as pool:
            for n, (job, row, rec) in enumerate(pool.map(_episode_recorded, jobs, chunksize=2), 1):
                rows[job[:5]] = row
                recs.setdefault(job[0], {})[job[1]] = rec
                if n % 20 == 0 or n == len(jobs):
                    print(f"  {n}/{len(jobs)}", flush=True)
        save_records(a.condition, recs)
        with open(_part(a.condition), "w", encoding="utf-8") as fh:
            json.dump([dict(ref=k_[0], episode=k_[1], t_amb_k=k_[2], p_kpa=k_[3], grade=k_[4], **v)
                       for k_, v in rows.items()], fh, indent=1)
        print(f"wrote {os.path.relpath(_part(a.condition), HERE)}", flush=True)
        return 0
    summary = summarise(rows)
    if os.path.isfile(OUT_JSON):
        # A re-run must reproduce the saved rows exactly: the episodes are
        # deterministic and the recorder only reads.
        with open(OUT_JSON, encoding="utf-8") as fh:
            old = {(r["ref"], r["episode"], r["t_amb_k"], r["p_kpa"], r["grade"]): r
                   for r in json.load(fh)["rows"]}
        new = {k_: dict(ref=k_[0], episode=k_[1], t_amb_k=k_[2], p_kpa=k_[3], grade=k_[4], **v)
               for k_, v in rows.items()}
        differ = [k_ for k_ in new if k_ in old and old[k_] != new[k_]]
        print(f"against the saved {os.path.relpath(OUT_JSON, HERE)}: {len(new)} rows, "
              f"{len(set(new) & set(old))} in both, {len(differ)} differ"
              + (f" -- first {differ[:2]}" if differ else " -- identical"), flush=True)
    with open(OUT_JSON, "w", encoding="utf-8") as fh:
        json.dump({"episodes": EPISODES, "conditions": [list(c) for c in CONDITIONS],
                   "speed_steps": SPEED_STEPS, "accel_max": ACCEL_MAX,
                   "target_peak_c": TARGET_PEAK_C, "hills": hills, "summary": summary,
                   "rows": [dict(ref=k_[0], episode=k_[1], t_amb_k=k_[2], p_kpa=k_[3], grade=k_[4], **v)
                            for k_, v in rows.items()]}, fh, indent=1)
        fh.write("\n")
    report(summary, hills)
    figure(summary, hills)
    return 0


if __name__ == "__main__":
    sys.exit(main())
