"""logged_check.py -- the trained agents on the states the car has logs for.

    python logged_check.py --build                    the test drives -> results/logged_cycles.json
    python logged_check.py --set runs/extremes_dt1    every agent on every drive -> results/logged_check_<set>.json
    python logged_check.py --set runs/extremes_dt1 --report-only

DECISION 12'S CHECK (results/VALIDATION_DECISIONS.md, 8 October 2026): train on
the extremes the car never reached, so the agent knows them; check the trained
agent on the states we have logs for, so we know it trained correctly. The
logged drives are where the simulator is validated against the car. There an
agent must

    T  deliver the torque asked for: on the steps that ask for more than 40 Nm,
       it may fall more than the reward's tolerance (5 %) short on at most 1 %
       of the steps on which the baseline ECU, in the same run, does not;
    F  burn no more fuel than the baseline ECU: at most 1 % more over the drive.

An agent passes when it meets T and F on every drive at both weightings. What
it does where nothing needed protecting (the median applied actuators while the
baseline's housing is below 750 C, 100 K under the trigger) is reported beside
it, not scored: F already prices any protection it buys there.

WHAT A DRIVE BECOMES (fixed before any agent of the 8 October design trained):

    drives   every drive in data/manifest.csv that logs vehicle speed and
             ambient temperature and runs five minutes or more, except the
             census log fb988991 (23 % of its seconds were never recorded,
             CLAUDE.md mistake 8). Six drives, 270 minutes.
    speed    the logged vehicle speed, each reading placed where it first
             appears in the log, interpolated linearly onto a 1 s grid and
             smoothed with a 3 s centred moving average. The logger polls one
             channel per row, so a held value is not a reading.
    ambient  the drive's median ambient reading, one value per drive: the
             environment takes one ambient per episode.
    grade    zero. The logs carry no grade; rebuilding it from the car's air
             mass would lean on the unidentified mass and drag area. So this is
             a check that the agent does no harm, NOT that it protects: a flat
             replay under-loads the climbs the car actually drove.
    weights  two of the twenty frozen episodes' weightings: the one that weights
             component life most and the one that weights it least
             (evaluate.EPISODES), each with that episode's seed.

Each run carries the baseline ECU in parallel (engine_env), so the comparison
is paired step for step: the baseline's torque is in the info dict as
`torque_base` since 8 October. Current-grade runs as well, for reference: on a
flat road it acts only where the housing passes the trigger.

Every step of every run is recorded (step_record.py) under
results/records/logged/<set>/, gitignored like every per-step record.
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

CYCLES_JSON = os.path.join(HERE, "results", "logged_cycles.json")
MIN_MINUTES = 5.0
CENSUS = ("fb988991-20260906_143515.csv",)
DEMAND_NM = 40.0                     # t_ref's floor in the reward: below it the error is scaled to 40 Nm
T_LIMIT = 0.01                       # T: agent-only shortfall steps, share of demand steps
F_LIMIT = 1.01                       # F: agent fuel over baseline fuel
COLD_C = 750.0                       # "nothing needed protecting": baseline housing below this
HAND = (("current-grade", "p_grade_now"),)


def _out_json(set_dir):
    return os.path.join(HERE, "results", f"logged_check_{os.path.basename(os.path.normpath(set_dir))}.json")


def _records_dir(set_dir):
    return os.path.join(HERE, "results", "records", "logged", os.path.basename(os.path.normpath(set_dir)))


# ---------------------------------------------------------------- the drives
def qualifying_drives():
    """The selection rule in the docstring, applied to the manifest."""
    import pandas as pd
    import car_thermal as CT
    m = pd.read_csv(os.path.join(HERE, "data", "manifest.csv"))
    out = []
    for f, mins in zip(m.file, m.duration_min):
        if f in CENSUS or not (mins >= MIN_MINUTES):
            continue
        g = CT.raw_grid(f)
        if np.isfinite(g.v_kmh).sum() == 0 or np.isfinite(g.t_amb).sum() == 0:
            continue
        out.append(f)
    return out


def _readings(t, x):
    """Each genuine reading of a forward-filled channel: the row where a value first appears."""
    ok = np.isfinite(x)
    t, x = t[ok], x[ok]
    if len(x) == 0:
        return t, x
    new = np.r_[True, np.diff(x) != 0.0]
    return t[new], x[new]


def drive_cycle(source):
    """One logged drive as an environment cycle (see the docstring)."""
    import pandas as pd
    import car_thermal as CT
    path = os.path.join(HERE, "logs", "raw", source)
    d = pd.read_csv(path, low_memory=False)
    cols = {c.strip().lower(): c for c in d.columns}
    t = pd.to_numeric(d[cols["time"]], errors="coerce").to_numpy(float)
    t = t - t[0]
    v = pd.to_numeric(d[cols[CT.RAW_CHANNELS["v_kmh"]]], errors="coerce").to_numpy(float)
    amb = pd.to_numeric(d[cols[CT.RAW_CHANNELS["t_amb"]]], errors="coerce").to_numpy(float)
    amb = amb[np.isfinite(amb) & (amb != 0.0)]          # placeholder zeros (AUDIT.md M8)
    tr, vr = _readings(t, v)
    grid = np.arange(0.0, float(t[-1]), 1.0)
    vk = np.interp(grid, tr, vr, left=vr[0], right=vr[-1])
    vk = np.convolve(np.r_[vk[0], vk, vk[-1]], np.ones(3) / 3.0, mode="valid")
    vk = np.clip(vk, 0.0, None)
    t_amb = float(np.median(amb)) + 273.15
    return dict(t=grid, v_mps=vk / 3.6, grade=np.zeros_like(grid), t_amb=t_amb,
                p_baro=101.3, humidity=0.012)


def build():
    drives = qualifying_drives()
    rows = []
    for f in drives:
        c = drive_cycle(f)
        a = np.diff(c["v_mps"])
        rows.append(dict(drive=f, minutes=round(len(c["t"]) / 60.0, 2), t_amb_c=round(c["t_amb"] - 273.15, 2),
                         v_max_kmh=round(float(c["v_mps"].max() * 3.6), 1),
                         v_median_moving_kmh=round(float(np.median(c["v_mps"][c["v_mps"] > 1.0]) * 3.6), 1),
                         accel_p99=round(float(np.percentile(a, 99)), 3),
                         decel_p1=round(float(np.percentile(a, 1)), 3),
                         v_sha=hashlib.sha256(np.round(c["v_mps"], 6).tobytes()).hexdigest()[:16]))
        print(f"  {f:40s} {rows[-1]['minutes']:6.1f} min  {rows[-1]['t_amb_c']:5.1f} C  "
              f"v max {rows[-1]['v_max_kmh']:5.1f} km/h  sha {rows[-1]['v_sha']}")
    import evaluate as E
    life = [w[2] for _, w in E.EPISODES]
    hi, lo = int(np.argmax(life)) + 1, int(np.argmin(life)) + 1
    out = dict(rule=("every manifest drive with vehicle speed and ambient, >= 5 min, "
                     "except the census log; speed from genuine readings, linear, 3 s mean; "
                     "median ambient; grade zero"),
               drives=rows, minutes=round(sum(r["minutes"] for r in rows), 1),
               episodes=dict(life_most=hi, life_least=lo),
               criteria=dict(demand_nm=DEMAND_NM, t_limit=T_LIMIT, f_limit=F_LIMIT, cold_c=COLD_C))
    with open(CYCLES_JSON, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
        fh.write("\n")
    print(f"{len(rows)} drives, {out['minutes']} minutes; weightings of frozen episodes "
          f"{hi} (life most) and {lo} (life least)\nwrote {os.path.relpath(CYCLES_JSON, HERE)}")


def _check_cycles():
    """The drives must still be the ones the preregistration fixed."""
    with open(CYCLES_JSON, encoding="utf-8") as fh:
        fixed = json.load(fh)
    for r in fixed["drives"]:
        c = drive_cycle(r["drive"])
        sha = hashlib.sha256(np.round(c["v_mps"], 6).tobytes()).hexdigest()[:16]
        if sha != r["v_sha"]:
            raise SystemExit(f"{r['drive']}: the speed trace is not the one fixed in "
                             f"{os.path.relpath(CYCLES_JSON, HERE)} ({sha} vs {r['v_sha']})")
    return fixed


# ---------------------------------------------------------------- one run
_MODELS, _CYC = {}, {}


def _init_worker():
    try:
        import torch
        torch.set_num_threads(1)
    except ImportError:
        pass


def _policy(set_dir, ref):
    import check_premise as C
    import evaluate as E
    if ref in dict(HAND):
        return getattr(C, dict(HAND)[ref]), True
    from stable_baselines3 import SAC
    key = (set_dir, ref)
    if key not in _MODELS:
        _MODELS[key] = SAC.load(os.path.join(HERE, set_dir, ref, "final"), device="cpu")
    return E.agent_policy(_MODELS[key]), "blind" not in ref


def run(job):
    set_dir, ref, drive, ep = job
    import engine_env as EE
    import evaluate as E
    import step_record
    if drive not in _CYC:
        _CYC[drive] = drive_cycle(drive)
    cycle = dict(_CYC[drive])
    policy, preview = _policy(set_dir, ref)
    seed, weights = E.EPISODES[ep - 1]
    env = EE.SupervisoryTunerEnv(cycle, dt=1.0, seed=seed, use_preview=preview)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    rec = step_record.new()
    demand = short_a = short_b = short_only = 0
    above_a = above_b = 0
    cold = []
    while True:
        a = policy(env, obs)
        obs_before = obs
        obs, r, term, trunc, info = env.step(a)
        step_record.step(rec, env, a, obs_before, r, info)
        req = info["torque_req"]
        if req > DEMAND_NM:
            demand += 1
            sa = info["torque"] < (1.0 - EE.TRACK_TOL) * req
            sb = info["torque_base"] < (1.0 - EE.TRACK_TOL) * req
            short_a += sa
            short_b += sb
            short_only += sa and not sb
        above_a += info["t_turb"] - 273.15 > 850.0
        above_b += env.thermal_base.t_turb - 273.15 > 850.0
        if env.thermal_base.t_turb - 273.15 < COLD_C:
            cold.append(np.array(env.prev_act, dtype=float))
        if term or trunc:
            break
    e = env.ep
    rec = step_record.finish(rec)
    row = dict(steps=int(e["steps"]), demand_steps=demand, short_agent=short_a, short_base=short_b,
               short_agent_only=short_only, fuel=e["fuel"], fuel_base=e["fuel_base"],
               damage=e["damage"], damage_base=e["damage_base"],
               peak_turb=float(np.max(rec["t_turb"]) - 273.15),
               peak_turb_base=float(np.max(rec["t_turb_base"]) - 273.15),
               s_above=int(above_a), s_above_base=int(above_b),
               cold_steps=len(cold),
               act_cold=[round(float(x), 4) for x in (np.median(np.array(cold), axis=0) if cold
                                                       else np.full(5, np.nan))])
    row["T"] = short_only <= T_LIMIT * max(demand, 1)
    row["F"] = e["fuel"] <= F_LIMIT * e["fuel_base"]
    return job, row, rec


def _agent_tags(set_dir):
    d = os.path.join(HERE, set_dir)
    return sorted((t for t in os.listdir(d) if t.startswith(("sighted_seed", "blind_seed"))
                   and os.path.isfile(os.path.join(d, t, "final.zip"))),
                  key=lambda t: (t.startswith("blind"), int(t.split("seed")[1])))


def main_run(set_dir, workers):
    fixed = _check_cycles()
    eps = (fixed["episodes"]["life_most"], fixed["episodes"]["life_least"])
    refs = [h for h, _ in HAND] + _agent_tags(set_dir)
    out_json = _out_json(set_dir)
    done = {}
    if os.path.exists(out_json):
        with open(out_json, encoding="utf-8") as fh:
            done = {(r["policy"], r["drive"], r["episode"]): r for r in json.load(fh)["runs"]}
    drives = [r["drive"] for r in fixed["drives"]]
    # Longest drives first, so the pool does not end on one long run.
    mins = {r["drive"]: r["minutes"] for r in fixed["drives"]}
    jobs = sorted(((set_dir, ref, d, ep) for ref in refs for d in drives for ep in eps
                   if (ref, d, ep) not in done), key=lambda j: -mins[j[2]])
    print(f"{len(jobs)} runs to go ({len(done)} done) on {workers} workers", flush=True)
    rdir = _records_dir(set_dir)
    os.makedirs(rdir, exist_ok=True)
    import evaluate as E
    import step_record
    t0 = time.time()
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=_init_worker) as pool:
        for i, (job, row, rec) in enumerate(pool.map(run, jobs), 1):
            _, ref, d, ep = job
            row.update(policy=ref, drive=d, episode=ep)
            done[(ref, d, ep)] = row
            stem = f"{ref.replace(' ', '_')}__{d.split('-')[0]}__ep{ep}"
            seed, w = E.EPISODES[ep - 1]
            step_record.save(os.path.join(rdir, stem), [rec],
                             meta=dict(set=set_dir, policy=ref, drive=d, episode=ep,
                                       note="logged_check.py: flat replay of a logged drive"),
                             seeds=[seed], weights=[w])
            print(f"  {i}/{len(jobs)} {ref:18s} {d[:12]:12s} ep{ep:<2d} T {'ok' if row['T'] else 'FAIL'} "
                  f"F {'ok' if row['F'] else 'FAIL'}  fuel {100 * (row['fuel'] / row['fuel_base'] - 1):+.2f} %  "
                  f"short-only {row['short_agent_only']}/{row['demand_steps']}  "
                  f"{(time.time() - t0) / 60:.0f} min", flush=True)
            if i % 20 == 0 or i == len(jobs):
                _save(out_json, set_dir, fixed, done)
    _save(out_json, set_dir, fixed, done)
    report(set_dir)


def _save(out_json, set_dir, fixed, done):
    with open(out_json, "w", encoding="utf-8") as fh:
        json.dump(dict(set=set_dir, cycles=fixed, runs=sorted(done.values(), key=lambda r: (
            r["policy"], r["drive"], r["episode"]))), fh, indent=1)
        fh.write("\n")


def report(set_dir):
    with open(_out_json(set_dir), encoding="utf-8") as fh:
        d = json.load(fh)
    runs = d["runs"]
    by = {}
    for r in runs:
        by.setdefault(r["policy"], []).append(r)
    n_need = len(d["cycles"]["drives"]) * 2
    print(f"\nTHE LOGGED CHECK, {set_dir}: {len(d['cycles']['drives'])} drives x 2 weightings, flat replay")
    print(f"{'policy':18s} {'runs':>4} {'T':>5} {'F':>5}  {'worst fuel':>10}  {'worst short-only':>16}  "
          f"{'peak C (base)':>14}")
    passes = {"sighted": [0, 0], "blind": [0, 0]}
    for ref, rs in sorted(by.items(), key=lambda kv: (kv[0].startswith("blind"), kv[0])):
        t_ok = sum(r["T"] for r in rs)
        f_ok = sum(r["F"] for r in rs)
        wf = max(100 * (r["fuel"] / r["fuel_base"] - 1) for r in rs)
        ws = max(r["short_agent_only"] / max(r["demand_steps"], 1) for r in rs)
        pk = max(r["peak_turb"] for r in rs)
        pkb = max(r["peak_turb_base"] for r in rs)
        ok = len(rs) == n_need and t_ok == len(rs) and f_ok == len(rs)
        arm = "blind" if ref.startswith("blind") else "sighted" if ref.startswith("sighted") else None
        if arm:
            passes[arm][0] += ok
            passes[arm][1] += 1
        print(f"{ref:18s} {len(rs):4d} {t_ok:5d} {f_ok:5d}  {wf:+9.2f}%  {100 * ws:15.2f}%  "
              f"{pk:6.0f} ({pkb:4.0f}){'   PASS' if ok else ''}")
    for arm, (k, n) in passes.items():
        if n:
            print(f"{arm}: {k} of {n} agents pass T and F on every drive and weighting")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--set", default=None)
    ap.add_argument("--workers", type=int, default=18)
    ap.add_argument("--report-only", action="store_true")
    a = ap.parse_args()
    if a.build:
        build()
        return
    if not a.set:
        raise SystemExit("give --set runs/<design>, or --build")
    if a.report_only:
        report(a.set)
        return
    main_run(a.set, a.workers)


if __name__ == "__main__":
    main()
