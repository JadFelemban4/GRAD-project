"""timestep_study.py -- how much of each thermal result is the time step?

    python timestep_study.py     prints two tables, writes results/timestep_study.json
                                 and results/figures/timestep_study.png

ASME V&V 20's u_num, the numerical part of a comparison's uncertainty, is
estimated by solving the same case with a finer and finer step and watching
the result settle (results/VALIDATION_PLAN.md, section 5c). The thermal
network (thermal.ThermalNetwork.step) is explicit Euler, called once per
environment step (1 s on the climb) and once per second in the car replays,
and with the derived constants its block node responds in about a second
(validate.py prints a step-response tau of 1.2 s).

Here the SAME call is split into n equal sub-steps with the inputs held, for n
= 1 (as shipped), 2, 5, 10, 20 and 50, and two cases are re-run:

  A. the locked climb, the baseline ECU and current-grade (dt 1.0, 720 s,
     frozen episode 1): peak turbine, damage, the cut, and how much the
     coolant swings from one step to the next on the climb;
  B. the drive10 replay that validate.py rows 8 and 11 score: the model's
     oil over the car's hottest ten minutes, and its whole-drive coolant;
  C. the locked climb at dt 2.0, the step generality_test.py's H/tau sweep
     runs at, where the merge review found the coolant never settles.

A DIAGNOSTIC BESIDE THE PROTOCOL. thermal.py is not edited: the sub-stepping
exists only inside this process (agreed step 1 will make it permanent, and
that is a plant change). So plant_sha, the certificates and every published
figure stand.

SINCE 8 OCTOBER 2026 agreed step 1 IS permanent: thermal.ThermalNetwork.step
sub-steps at most thermal.DT_SUB_MAX (0.1 s) on its own. So "n = 1 (as shipped)"
is now the sub-stepped network, and each n splits the call on top of that. Run
on the plant of 8 October this measures what is left of u_num, which is what
the H/tau sweep's "not quotable" rested on. (Its first run, 7 October, measured
the plant before the change; results/timestep_study.json carries whichever ran
last.)
"""
import concurrent.futures as cf
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
SUBSTEPS = (1, 2, 5, 10, 20, 50)
SUBSTEPS_DT2 = (1, 2, 5, 100)          # sub-steps of a 2 s step: 2, 1, 0.4 and 0.02 s
CLIMB_FROM_S = 504                     # the last 30 % of the 720 s climb episode


def _substep(n):
    """Split every ThermalNetwork.step into n sub-steps, in this process only."""
    import thermal
    if not hasattr(thermal.ThermalNetwork, "_step_once"):
        thermal.ThermalNetwork._step_once = thermal.ThermalNetwork.step

    def step(self, dt, *args, **kw):
        for _ in range(n):
            out = self._step_once(dt / n, *args, **kw)
        return out
    thermal.ThermalNetwork.step = step if n > 1 else thermal.ThermalNetwork._step_once


def _climb(job):
    policy_name, n, dt = job
    _substep(n)
    import check_premise as C
    import engine_env as EE
    import evaluate as E
    policy = {"baseline ECU": C.p_neutral, "current-grade": C.p_grade_now}[policy_name]
    seed, weights = E.EPISODES[0]
    cycle = EE.make_grade_climb(duration=E.DURATION, dt=dt)
    env = EE.SupervisoryTunerEnv(cycle, dt=dt, seed=seed, use_preview=True)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)
    obs = env._obs()
    peak, thermal, block = 0.0, 0.0, []
    while True:
        obs, _, term, trunc, info = env.step(policy(env, obs))
        peak = max(peak, info["t_turb"])
        thermal += EE.damage_rate(info["t_turb"], info["t_oil"]) * env.dt
        block.append(info["t_block"] - 273.15)
        if term or trunc:
            break
    b = np.array(block[int(CLIMB_FROM_S / dt):])
    jumps = np.diff(b)
    return job, dict(peak_turb=peak - 273.15, damage=info["episode_summary"]["damage"],
                     damage_thermal=thermal,
                     coolant_mean=float(b.mean()), coolant_swing=float(b.max() - b.min()),
                     coolant_step=float(np.mean(np.abs(jumps))),
                     coolant_flips=float(np.mean(np.sign(jumps[1:]) != np.sign(jumps[:-1]))))


def _drive(n):
    _substep(n)
    import car_thermal as CT
    r = CT.thermal_replay(CT.SUSTAINED_DRIVE)
    k = 273.15
    sl = CT.hottest_window(r["oil_car"])
    return n, dict(row8_oil=float(np.median(r["oil_model"][sl]) - k),
                   row11_coolant=float(np.median(r["ect_model"]) - k),
                   oil_median_error=float(np.nanmedian(r["oil_model"] - r["oil_car"])),
                   coolant_median_error=float(np.nanmedian(r["ect_model"] - r["ect_car"])))


def main():
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    jobs = [(p, n, 1.0) for p in ("baseline ECU", "current-grade") for n in SUBSTEPS]
    jobs2 = [(p, n, 2.0) for p in ("baseline ECU", "current-grade") for n in SUBSTEPS_DT2]
    with cf.ProcessPoolExecutor(max_workers=12) as pool:
        climb_f = pool.map(_climb, jobs)
        climb2_f = pool.map(_climb, jobs2)
        drive_f = pool.map(_drive, SUBSTEPS)
        climb = {f"{p} | {n}": r for (p, n, _), r in climb_f}
        climb2 = {f"{p} | {n}": r for (p, n, _), r in climb2_f}
        drive = {str(n): r for n, r in drive_f}

    print("A. the locked climb, frozen episode 1; coolant over the last 30 % of the episode")
    print(f"   {'policy':14s} {'sub-steps':>9s} {'peak C':>8s} {'damage':>8s} {'thermal':>8s} "
          f"{'coolant C':>9s} {'swing K':>8s} {'K/step':>7s} {'flips':>6s}")
    for p in ("baseline ECU", "current-grade"):
        for n in SUBSTEPS:
            r = climb[f"{p} | {n}"]
            print(f"   {p:14s} {n:9d} {r['peak_turb']:8.2f} {r['damage']:8.1f} {r['damage_thermal']:8.1f} "
                  f"{r['coolant_mean']:9.2f} {r['coolant_swing']:8.2f} {r['coolant_step']:7.3f} "
                  f"{r['coolant_flips']:6.2f}")
    cuts = {n: 100.0 * (1.0 - climb[f"current-grade | {n}"]["damage"] / climb[f"baseline ECU | {n}"]["damage"])
            for n in SUBSTEPS}
    print("   current-grade's cut against the baseline: "
          + ", ".join(f"{n} sub-steps {c:.2f} %" for n, c in cuts.items()))
    print("\nB. drive10 replay, the quantities validate.py rows 8 and 11 score")
    print(f"   {'sub-steps':>9s} {'row 8 oil C':>12s} {'row 11 coolant C':>17s} {'oil err K':>10s} "
          f"{'coolant err K':>14s}")
    for n in SUBSTEPS:
        r = drive[str(n)]
        print(f"   {n:9d} {r['row8_oil']:12.2f} {r['row11_coolant']:17.2f} {r['oil_median_error']:+10.2f} "
              f"{r['coolant_median_error']:+14.2f}")

    print("\nC. the locked climb at dt 2.0, the H/tau sweep's step")
    print(f"   {'policy':14s} {'sub-steps':>9s} {'peak C':>8s} {'damage':>8s} {'coolant C':>9s} "
          f"{'swing K':>8s} {'K/step':>7s} {'flips':>6s}")
    for p in ("baseline ECU", "current-grade"):
        for n in SUBSTEPS_DT2:
            r = climb2[f"{p} | {n}"]
            print(f"   {p:14s} {n:9d} {r['peak_turb']:8.2f} {r['damage']:8.1f} {r['coolant_mean']:9.2f} "
                  f"{r['coolant_swing']:8.2f} {r['coolant_step']:7.3f} {r['coolant_flips']:6.2f}")
    cuts2 = {n: 100.0 * (1.0 - climb2[f"current-grade | {n}"]["damage"] / climb2[f"baseline ECU | {n}"]["damage"])
             for n in SUBSTEPS_DT2}
    print("   current-grade's cut against the baseline: "
          + ", ".join(f"{n} sub-steps {c:.2f} %" for n, c in cuts2.items()))

    finest = str(SUBSTEPS[-1])
    u = dict(
        peak_turb_k=abs(climb["baseline ECU | 1"]["peak_turb"] - climb[f"baseline ECU | {finest}"]["peak_turb"]),
        damage=abs(climb["baseline ECU | 1"]["damage"] - climb[f"baseline ECU | {finest}"]["damage"]),
        cut_points=abs(cuts[1] - cuts[SUBSTEPS[-1]]),
        row8_oil_k=abs(drive["1"]["row8_oil"] - drive[finest]["row8_oil"]),
        row11_coolant_k=abs(drive["1"]["row11_coolant"] - drive[finest]["row11_coolant"]))
    print(f"\nshipped step against {finest} sub-steps (the u_num estimate, before any safety factor):")
    for k, v in u.items():
        print(f"   {k:16s} {v:.3f}")
    path = os.path.join(HERE, "results", "timestep_study.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"substeps": SUBSTEPS, "climb": climb, "cuts": {str(k): v for k, v in cuts.items()},
                   "drive10": drive, "u_num_vs_finest": u,
                   "dt2": {"substeps": SUBSTEPS_DT2, "climb": climb2,
                           "cuts": {str(k): v for k, v in cuts2.items()}}}, fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")
    figure(climb, drive, cuts)


def figure(climb, drive, cuts):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    n = np.array(SUBSTEPS)
    fig, axes = plt.subplots(1, 3, figsize=(13, 3.8))
    a = axes[0]
    for p, c in (("baseline ECU", "#4b5157"), ("current-grade", "#1baf7a")):
        a.plot(n, [climb[f"{p} | {k}"]["damage"] for k in SUBSTEPS], "o-", color=c, label=p)
    a.set_xscale("log"); a.set_xlabel("thermal sub-steps per 1 s step"); a.set_ylabel("climb damage")
    a.set_title("Damage on the locked climb", fontsize=10); a.legend(fontsize=8)
    a = axes[1]
    a.plot(n, [climb[f"baseline ECU | {k}"]["coolant_swing"] for k in SUBSTEPS], "o-", color="#2a78d6")
    a.set_xscale("log"); a.set_xlabel("thermal sub-steps per 1 s step")
    a.set_ylabel("coolant max - min on the climb, K"); a.set_title("Baseline coolant swing", fontsize=10)
    a = axes[2]
    a.plot(n, [drive[str(k)]["row8_oil"] for k in SUBSTEPS], "o-", color="#eb6834", label="row 8 oil, hottest 10 min")
    a.plot(n, [drive[str(k)]["row11_coolant"] for k in SUBSTEPS], "s-", color="#2a78d6", label="row 11 coolant, whole drive")
    a.set_xscale("log"); a.set_xlabel("thermal sub-steps per 1 s step"); a.set_ylabel("model, C")
    a.set_title("drive10 replay", fontsize=10); a.legend(fontsize=8)
    fig.tight_layout()
    path = os.path.join(HERE, "results", "figures", "timestep_study.png")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fig.savefig(path, dpi=130)
    print(f"wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()
