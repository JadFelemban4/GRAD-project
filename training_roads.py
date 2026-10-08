"""training_roads.py -- the road, the preference weights and the applied
actuators under every step of a terrain training run, regenerated from the
run's seed and its recorded actions, and checked against what the run recorded.

    python training_roads.py runs/terrain_dt1            check every run, then write train_roads.npz
    python training_roads.py runs/terrain_dt1 --check    check only

Written 7 October 2026 (Ghassan: "everything from the environment to the
actions of the agents recorded"). The twenty agents of 29 September recorded
every training action, but not the road it was taken on, the weights it was
paid by, or what the actuators did with it: train.py kept no grade, speed or
gear until _StepState was added. This recovers them. MEASURED on all twenty
runs, 1 000 000 steps: every episode's family equals curve.csv; the torque
request agrees to the old record's float16 rounding (0.125 Nm) on every step;
the reward rebuilt from the regenerated weights, the recorded reward terms and
the regenerated actuators agrees to 2e-6 on every step (results/train_roads_check.json).

THE WEIGHTS AND THE ACTUATORS. SupervisoryTunerEnv draws the preference
weights at reset from np.random.default_rng(seed), a stream nothing else
touches; they also sit in the observation's last three inputs, at float16. The
applied actuators follow from the recorded actions through the step's slew
limit and bounds, from rest at each reset. Rebuilding the reward from both is
the check that they are right.

WHY IT CAN BE DONE EXACTLY. TerrainTrainingEnv draws each episode's road from
its own random stream, np.random.default_rng([seed, 0x7E4A1]), advanced only at
reset -- never by the agent's actions, never by the preference weights, which
have their own stream. Stable-Baselines3 resets once with the run's seed, which
rebuilds that stream, and without one after. So the i-th road of a run is the
i-th draw, whatever the agent did. (A RESUMED run would restart the stream at
the resume; config.json's `resumed_from` says whether one was, and the check
below would catch it.)

WHY IT IS CHECKED ANYWAY. Two things the run itself kept must agree with the
regenerated roads: the family of every episode (curve.csv's `road` column) and
the torque the driver model asked for on every step (train_record.npz's
`torque_req`), which the road sets through Vehicle.demand and the agent cannot
move. A run whose roads do not reproduce is reported and nothing is written
for it.

Writes, beside each train_record.npz (gitignored like the record):
train_roads.npz -- per step, aligned to the record: grade, v_kmh, rpm, gear,
torque_req, weights, applied (regenerated); per episode: family.
show_record.py reads it. Records written by train.py since 7 October carry all
of these themselves and need none of this.
"""
import argparse
import csv
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)


def regenerate(seed, n_episodes, duration=900.0, dt=1.0, v_kmh=130.0, t_amb=315.0):
    """The roads a TerrainTrainingEnv(seed=seed) gives on its first n resets."""
    import engine_env as EE
    rng = np.random.default_rng([int(seed), EE.TerrainTrainingEnv._TERRAIN_STREAM])
    return [EE.make_terrain(rng, duration=duration, dt=dt, v_kmh=v_kmh, t_amb=t_amb,
                            families=EE.TERRAIN_FAMILIES, weights=EE.TERRAIN_WEIGHTS)
            for _ in range(n_episodes)]


def weights(seed, n_episodes):
    """The preference weights of a run's first n episodes: SupervisoryTunerEnv
    draws them at reset from np.random.default_rng(seed), a stream nothing else
    touches (engine_env.py, reset)."""
    import engine_env as EE
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n_episodes):
        w_track = float(EE.TRACK_W_MIN + (EE.TRACK_W_MAX - EE.TRACK_W_MIN) * rng.random())
        w_rest = rng.dirichlet(np.ones(2)) * (1.0 - w_track)
        out.append(np.array([w_track, w_rest[0], w_rest[1]], dtype=np.float32))
    return out


def applied(actions, dt=1.0):
    """What the actuators did, from the actions the agent sent: the step's own
    slew limit and bounds (engine_env.SupervisoryTunerEnv.step), from rest at
    reset. Returns the applied actuators and the smoothness term the reward
    charged."""
    import engine_env as EE
    prev = np.zeros(5, dtype=np.float32)
    out, smooth = [], []
    for a in actions:
        raw = EE.ACT_LO + (np.clip(np.asarray(a, dtype=np.float32), -1.0, 1.0) + 1.0) * 0.5 * (EE.ACT_HI - EE.ACT_LO)
        slew = EE.SLEW * dt
        act = np.clip(np.clip(raw, prev - slew, prev + slew), EE.ACT_LO, EE.ACT_HI)
        smooth.append(float(np.sum(((act - prev) / (EE.ACT_HI - EE.ACT_LO)) ** 2)))
        out.append(act)
        prev = act
    return np.array(out), np.array(smooth)


def drive(cycle, steps, dt=1.0):
    """What SupervisoryTunerEnv.step computes from the road alone: the speed,
    the grade, the driver's torque request, the engine speed and the gear."""
    import engine_env as EE
    import step_record
    veh = EE.Vehicle()
    v_all, g_all = cycle["v_mps"], cycle["grade"]
    n = len(v_all)
    rho = cycle.get("p_baro", 101.3) * 1000.0 / (287.0 * cycle["t_amb"])
    out = {k: [] for k in ("grade", "v_kmh", "rpm", "gear", "torque_req")}

    class _At:                                   # what step_record.gear reads
        pass
    for k in range(steps):
        v = float(v_all[k])
        accel = (float(v_all[min(k + 1, n - 1)]) - v) / dt
        tq, rpm = veh.demand(v, accel, float(g_all[k]), rho=rho)
        at = _At()
        at.veh, at.v, at.rpm = veh, v, rpm
        out["grade"].append(float(g_all[k]))
        out["v_kmh"].append(v * 3.6)
        out["rpm"].append(rpm)
        out["gear"].append(step_record.gear(at))
        out["torque_req"].append(tq)
    return out


def check_run(run_dir, write=True, check=None):
    check = {} if check is None else check
    with open(os.path.join(run_dir, "config.json"), encoding="utf-8") as fh:
        cfg = json.load(fh)
    tag = os.path.basename(os.path.normpath(run_dir))
    if "TerrainTrainingEnv" not in str(cfg.get("roads", "")):
        return tag, False, "not a terrain run: its road is in config.json"
    if cfg.get("resumed_from"):
        return tag, False, f"resumed from {cfg['resumed_from']}: the road stream restarted there"
    rec = np.load(os.path.join(run_dir, "train_record.npz"))
    ep = rec["episode"]
    eps = np.unique(ep)
    with open(os.path.join(run_dir, "curve.csv"), newline="", encoding="utf-8") as fh:
        curve = {int(r["episode"]): r["road"] for r in csv.DictReader(fh)}
    roads = regenerate(cfg["seed"], int(eps.max()) + 1, cfg.get("duration_s", 900.0), cfg.get("dt", 1.0))
    fam = [c["family"] for c in roads]
    fam_bad = [e for e in curve if e < len(fam) and curve[e] != fam[e]]
    dt = cfg.get("dt", 1.0)
    cols = {k: np.full(len(ep), np.nan) for k in ("grade", "v_kmh", "rpm", "torque_req", "reward")}
    gear = np.zeros(len(ep), dtype=np.int8)
    w_ep = weights(cfg["seed"], int(eps.max()) + 1)
    w_step = np.zeros((len(ep), 3), dtype=np.float32)
    act = np.zeros((len(ep), 5), dtype=np.float32)
    for e in eps:
        idx = np.flatnonzero(ep == e)
        d = drive(roads[e], len(idx), dt)
        for k in ("grade", "v_kmh", "rpm", "torque_req"):
            cols[k][idx] = d[k]
        gear[idx] = d["gear"]
        w_step[idx] = w_ep[e]
        act[idx], smooth = applied(rec["action"][idx], dt)
        w = w_ep[e]
        # the reward the step paid, rebuilt: it checks the weights AND the applied actuators
        cols["reward"][idx] = (w[1] * rec["r_fuel"][idx].astype(float) + w[2] * rec["r_life"][idx].astype(float)
                               + w[0] * rec["r_resp"][idx].astype(float) - 0.05 * smooth / max(dt, 1e-6))
    recorded = rec["torque_req"].astype(float)
    # the old record stored torque_req as float16: 0.25 Nm steps at 256-512 Nm
    tol = np.maximum(0.5, np.abs(recorded) * 2.0 ** -10)
    err = np.abs(cols["torque_req"] - recorded)
    bad = int(np.sum(err > tol))
    # the weights are also in the observation's last three inputs (float16 there)
    w_err = float(np.max(np.abs(rec["obs"][:, -3:].astype(float) - w_step)))
    r_err = np.abs(cols["reward"] - rec["reward"].astype(float))
    r_bad = int(np.sum(r_err > 1e-4 + 1e-4 * np.abs(rec["reward"].astype(float))))
    ok = not fam_bad and bad == 0 and w_err < 1e-3 and r_bad == 0
    note = (f"{len(eps)} episodes, families {'equal curve.csv' if not fam_bad else f'DIFFER at {fam_bad[:3]}'}; "
            f"torque request: largest difference {err.max():.3f} Nm, {bad} of {len(ep)} beyond float16 "
            f"rounding; weights against the observation {w_err:.1e}; reward rebuilt from weights, terms "
            f"and applied actuators: largest difference {r_err.max():.1e}, {r_bad} beyond 1e-4")
    if ok and write:
        arrays = dict(episode=ep, step=rec["step"], gear=gear, family=np.array(fam),
                      weights=w_step, applied=act,
                      **{k: cols[k].astype(np.float32) for k in ("grade", "v_kmh", "rpm", "torque_req")})
        for d in (run_dir, os.path.join(HERE, "results", "agents", os.path.basename(os.path.dirname(
                os.path.normpath(run_dir))), tag)):
            if os.path.isfile(os.path.join(d, "train_record.npz")):
                np.savez_compressed(os.path.join(d, "train_roads.npz"), **arrays)
    check.update(tag=tag, ok=bool(ok), episodes=int(len(eps)), steps=int(len(ep)),
                 families_equal=not fam_bad, torque_err_max_nm=round(float(err.max()), 4),
                 torque_beyond_rounding=bad, weights_err_max=round(w_err, 6),
                 reward_err_max=float(f"{r_err.max():.3g}"), reward_beyond=r_bad)
    return tag, ok, note


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    ap.add_argument("--check", action="store_true", help="check only; write nothing")
    a = ap.parse_args()
    runs = sorted(os.path.dirname(p) for p in glob.glob(os.path.join(HERE, a.set_dir, "*_seed*", "train_record.npz")))
    if not runs:
        raise SystemExit(f"no <tag>/train_record.npz under {a.set_dir}")
    n_ok, checks = 0, []
    for r in runs:
        checks.append({})
        tag, ok, note = check_run(r, write=not a.check, check=checks[-1])
        n_ok += ok
        print(f"  {tag:16s} {'REPRODUCED' if ok else 'NOT REPRODUCED'}  {note}", flush=True)
    print(f"{n_ok} of {len(runs)} runs: the road under every training step regenerated and checked"
          + ("" if a.check else "; train_roads.npz written beside each record"))
    # The check itself is small and committed (the records are not): what the
    # results page and the documents quote about the regenerated roads.
    path = os.path.join(HERE, "results", "train_roads_check.json")
    good = [c for c in checks if c.get("ok")]
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dict(set=os.path.basename(os.path.normpath(a.set_dir)), runs=len(runs), reproduced=n_ok,
                       steps=sum(c.get("steps", 0) for c in checks),
                       torque_err_max_nm=max((c["torque_err_max_nm"] for c in good), default=None),
                       reward_err_max=max((c["reward_err_max"] for c in good), default=None),
                       per_run=checks), fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")
    return 0 if n_ok == len(runs) else 1


if __name__ == "__main__":
    sys.exit(main())
