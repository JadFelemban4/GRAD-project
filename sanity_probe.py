"""sanity_probe.py -- a hotter housing must never get less protection (decision 12, safeguard 2).

    python sanity_probe.py runs/extremes_dt1     -> results/agents/extremes_dt1/sanity_probe.json

Written 8 October 2026 with results/PREREGISTRATION_X1.md, before any X1 agent
trained, so the probe is fixed before there is a policy to aim it at. A
REPORTED diagnostic, not a gate and not a test of preview.

WHAT IT ASKS. The extremes are where the simulator is least trusted, so beside
the scores each agent is asked a question whose right answer is physics, not
the plant's numbers: shown the same moment of the climb with its turbine housing
50 K hotter, does it protect at least as much? Protection on the climb is the
two levers that cool the housing in this model: a richer lambda trim and a lower
boost trim. (Spark is capped at 0 for X1, so it can only retard, and the fan and
pump act on the coolant loop, which the gas-heated housing barely sees.)

HOW. From each agent's own recorded frozen episodes (eval_record.npz, written
by record_agents.py), every 10th step on the climb (grade above 2 %) is taken.
The observation's housing input (index 7, (T - 873 K) / 200 K) is raised by
50 K and the deterministic policy is asked again. A state is a VIOLATION when
the hotter housing gets a LEANER lambda trim by more than 0.005 or a HIGHER
boost trim by more than 1 kPa, in the physical units of the action
(SupervisoryTunerEnv._rescale). Reported per agent: the share of probed states
that violate, and the median change in each lever.

What it cannot say: a policy whose protection does not grow with temperature at
the probed states passes it, and one that already sits at a lever's bound cannot
move further. It checks direction, not amount.
"""
import argparse
import glob
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

T_IDX, T_SCALE = 7, 200.0          # engine_env._obs: (t_turb - 873) / 200
HOTTER_K = 50.0
EVERY = 10
LAMBDA_TOL, BOOST_TOL = 0.005, 1.0


def probe(agent_dir, record_dir):
    import engine_env as E
    from stable_baselines3 import SAC
    model = SAC.load(os.path.join(HERE, agent_dir, "final"), device="cpu")
    rec = np.load(os.path.join(record_dir, "eval_record.npz"))
    obs, grade = rec["obs"].astype(np.float32), rec["grade"]
    env = E.SupervisoryTunerEnv(E.make_grade_climb(duration=60.0, dt=1.0), dt=1.0)
    states = [obs[e, k] for e in range(obs.shape[0]) for k in range(0, obs.shape[1], EVERY)
              if np.isfinite(grade[e, k]) and grade[e, k] > 0.02]
    x = np.stack(states)
    hot = x.copy()
    hot[:, T_IDX] += HOTTER_K / T_SCALE
    a0, _ = model.predict(x, deterministic=True)
    a1, _ = model.predict(hot, deterministic=True)
    p0 = np.array([env._rescale(a) for a in a0])
    p1 = np.array([env._rescale(a) for a in a1])
    d_lam, d_boost = p1[:, 1] - p0[:, 1], p1[:, 2] - p0[:, 2]
    bad = (d_lam > LAMBDA_TOL) | (d_boost > BOOST_TOL)
    return dict(states=int(len(x)), violations=int(bad.sum()), share=round(float(bad.mean()), 4),
                d_lambda_median=round(float(np.median(d_lam)), 4),
                d_boost_kpa_median=round(float(np.median(d_boost)), 3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("set_dir")
    a = ap.parse_args()
    name = os.path.basename(os.path.normpath(a.set_dir))
    out = {}
    for d in sorted(glob.glob(os.path.join(HERE, a.set_dir, "*_seed*", "final.zip"))):
        tag = os.path.basename(os.path.dirname(d))
        rdir = os.path.join(HERE, "results", "agents", name, tag)
        if not os.path.isfile(os.path.join(rdir, "eval_record.npz")):
            print(f"{tag}: no eval_record.npz -- run record_agents.py {a.set_dir} first")
            continue
        out[tag] = probe(os.path.relpath(os.path.dirname(d), HERE), rdir)
        r = out[tag]
        print(f"{tag:16s} {r['states']:4d} states  violations {r['violations']:4d} ({100 * r['share']:5.1f} %)  "
              f"median d lambda {r['d_lambda_median']:+.4f}  d boost {r['d_boost_kpa_median']:+.2f} kPa")
    path = os.path.join(HERE, "results", "agents", name, "sanity_probe.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(dict(rule=dict(hotter_k=HOTTER_K, every=EVERY, lambda_tol=LAMBDA_TOL, boost_tol_kpa=BOOST_TOL),
                       agents=out), fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(path, HERE)}")


if __name__ == "__main__":
    main()
