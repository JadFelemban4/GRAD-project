"""check_c4_convergence.py — had the C4 agents finished learning? Decided before any trained.

    python check_c4_convergence.py             runs_c4/, about 45 minutes
    python check_c4_convergence.py --selftest  the practice set regenerates; seconds
    python check_c4_convergence.py --calibrate the rule's noise floor, measured on
                                               Phase D2's agents; about 40 minutes

Writes `results/c4_convergence.txt`. `analyse_c4.py` reads its VERDICT line and
the per-agent hashes above it.

WHY THIS EXISTS
---------------
Phase D and Phase D2 were both INCONCLUSIVE with C1 agents -- 50 000 steps, 11
training episodes -- and "maybe they were still undertrained" was a live
explanation for both nulls (`PREREGISTRATION.md` limit 6). C4 trains the same
design for 300 000 steps to test exactly that. So if C4 is ALSO a null, the
first question an examiner asks is "were THESE agents still undertrained?" --
and an answer invented after seeing the result would be worth nothing. This
file is the answer, written and committed before any of the sixteen C4 agents
trained (`results/PREREGISTRATION_C4.md` section 5b).

WHY NOT THE LEARNING CURVE, which is the obvious place to look
---------------------------------------------------------------
`curve.csv` holds one return per training episode, and every training episode
is scored with a DIFFERENT ruler: `reset()` draws a fresh preference vector,
and on the randomised climb a fresh road too. `evaluate.py`'s docstring
measured what that does -- eleven C1 episodes ranged from -506 to +644, and
the largest came FIRST. A flatness test on returns like that passes on noise:
"the curve is flat" would be true of an agent that was still learning. The
curve is printed below as supporting evidence, never as the rule.

THE RULE, fixed here
--------------------
Every agent is scored at three points in the last third of its training --
the checkpoints at 200 000 and 250 000 steps and the final model at 300 000 --
on the SAME ten practice episodes (`PRACTICE`, below). Same episodes, same
weights, same roads, deterministic policy: the ruler is fixed, so a change
between checkpoints is a change in the AGENT.

  settled     the agent's median damage over the practice set moves by no more
              than SETTLE_BAND across the three points (max minus min)
  converged   at least MIN_SETTLED of the 8 agents in EACH arm are settled

SETTLE_BAND is half the minimum effect of interest. An agent whose damage is
still moving by more than that over its last 100 000 steps is changing at a
scale that could create or erase an effect the team would care about. The rule
is PER ARM because the objection it answers is specific: "the sighted agents
had not yet learned to use the preview". An experiment in which one arm
settled and the other did not is not converged, whatever the total.

WHAT THE RULE ALLOWS AT THE PAIR LEVEL, stated because the review of the draft
preregistration found it: settling is judged per agent, and the test is on the
per-seed PAIR. Two settled agents moving 25 units in opposite directions move
their pair by 50, the whole MEI; and 6 of 8 per arm lets the four unsettled
agents sit in four different seeds. The paired movement is therefore printed
beside the verdict, as a description. The rule itself is the team's choice.

THE PRACTICE SET IS NOT THE TEST SET. `evaluate.EPISODES_D2` is the frozen test
set and nothing here touches it: judging convergence on it would be looking at
the test before the test. The practice set is ten episodes drawn once from
`numpy.default_rng(20260923)` -- seeds 3000-3009, which no frozen set uses,
weights drawn as `SupervisoryTunerEnv.reset()` draws them, roads a Latin
hypercube over the same [120, 300] s x [12, 16] % ranges as training.
`--selftest` regenerates it and checks the literal.

WHAT THE VERDICT DOES, AND WHAT IT CANNOT DO. It labels the result. It does
not select a checkpoint, extend a run, drop an agent or change the test: the
agent that is scored is always the final one, at 300 000 steps. "Not
converged" is reported beside the C4 result, not repaired -- more training is
a new experiment with its own preregistration. It is run, and committed,
BEFORE the test set is scored (`PREREGISTRATION_C4.md` section 9).
"""
import argparse
import os
import sys
import time
from multiprocessing import Pool

import numpy as np

import fingerprint as FP

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- the rule. results/PREREGISTRATION_C4.md section 5b. -------------------
MEI = 50.0                        # analyse_phase_d2.MEI; --selftest checks it
SETTLE_BAND = MEI / 2             # 25 damage units
CHECKPOINTS = (200_000, 250_000, 300_000)
MIN_SETTLED = 6                   # of 8, in EACH arm
C4_STEPS = 300_000

PRACTICE_SEED = 20260923
# (episode seed, (w_track, w_fuel, w_life), climb start s, climb grade)
PRACTICE = (
    (3000, (0.688185, 0.254903, 0.056912), 191.85, 0.13563),
    (3001, (0.538674, 0.40085, 0.060476), 210.74, 0.12661),
    (3002, (0.529153, 0.093578, 0.377269), 266.33, 0.15755),
    (3003, (0.518188, 0.383257, 0.098555), 160.82, 0.14183),
    (3004, (0.519459, 0.199479, 0.281062), 241.66, 0.12393),
    (3005, (0.641503, 0.295978, 0.062519), 150.72, 0.14803),
    (3006, (0.49435, 0.359639, 0.146011), 123.18, 0.13862),
    (3007, (0.626027, 0.051563, 0.322409), 263.22, 0.15306),
    (3008, (0.658825, 0.099183, 0.241992), 289.94, 0.13038),
    (3009, (0.684474, 0.050576, 0.26495), 203.74, 0.14592),
)

TAGS = [f"{arm}_seed{s}" for s in range(8) for arm in ("sighted", "blind")]


def practice_set(seed=PRACTICE_SEED, n=10):
    """Regenerate PRACTICE. Weights as reset() draws them; roads stratified."""
    from engine_env import TRACK_W_MIN, TRACK_W_MAX
    import random_road as RR
    rng = np.random.default_rng(seed)
    (s_lo, s_hi), (g_lo, g_hi) = RR.RANGES["start_s"], RR.RANGES["grade"]
    u_s = (rng.permutation(n) + rng.random(n)) / n
    u_g = (rng.permutation(n) + rng.random(n)) / n
    out = []
    for i in range(n):
        w_track = float(TRACK_W_MIN + (TRACK_W_MAX - TRACK_W_MIN) * rng.random())
        w_rest = rng.dirichlet(np.ones(2)) * (1.0 - w_track)
        w = (round(w_track, 6), round(float(w_rest[0]), 6),
             round(float(w_rest[1]), 6))
        out.append((3000 + i, w, round(s_lo + (s_hi - s_lo) * float(u_s[i]), 2),
                    round(g_lo + (g_hi - g_lo) * float(u_g[i]), 5)))
    return tuple(out)


def checkpoint_path(agent_dir, steps):
    """The zip scored at `steps`: a periodic checkpoint, or final.zip at the end."""
    if steps == C4_STEPS:
        return os.path.join(agent_dir, "final.zip")
    return os.path.join(agent_dir, f"ckpt_{steps}_steps.zip")


def score(job):
    """(tag, zip path, key) -> (tag, key, damages, returns, budget)."""
    tag, path, key = job
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    import evaluate as E
    from stable_baselines3 import SAC
    model = SAC.load(path)
    pol = E.agent_policy(model)
    preview = not tag.startswith("blind")
    dmg, ret = [], []
    for s, w, st, g in PRACTICE:
        r = E.run_episode(pol, s, w, preview, road=(st, g))
        dmg.append(r["damage"])
        ret.append(r["ret"])
    return tag, key, dmg, ret, FP.model_budget(path)


def curve_trend(agent_dir):
    """Supporting evidence only: the return trend over the last third of training.

    Least-squares slope of episode return on episode index, per 10 episodes,
    with its standard error. Each return was earned under a different
    preference draw and road, so this is noisy by construction -- which is
    exactly why it is not the rule.
    """
    p = os.path.join(agent_dir, "curve.csv")
    try:
        c = np.loadtxt(p, delimiter=",", skiprows=1, ndmin=2)
    except (OSError, ValueError):
        return None
    if c.ndim != 2 or c.shape[0] == 0 or c.shape[1] < 2:
        return None
    y = c[:, 1]
    tail = y[len(y) - len(y) // 3:]
    if len(tail) < 5:
        return None
    x = np.arange(len(tail), dtype=float)
    b, a0 = np.polyfit(x, tail, 1)
    resid = tail - (a0 + b * x)
    se = float(np.sqrt(resid.var(ddof=2) / ((x - x.mean()) ** 2).sum()))
    return dict(n=len(y), tail=len(tail), slope10=10 * b, se10=10 * se)


def selftest():
    import analyse_phase_d2
    regen = practice_set()
    ok_set = regen == PRACTICE
    ok_mei = analyse_phase_d2.MEI == MEI
    import evaluate
    overlap = {e[0] for e in PRACTICE} & (
        {e[0] for e in evaluate.EPISODES} | {e[0] for e in evaluate.EPISODES_D2})
    print(f"PRACTICE regenerates from seed {PRACTICE_SEED}      : {ok_set}")
    print(f"MEI here equals analyse_phase_d2.MEI ({MEI:.0f})     : {ok_mei}")
    print(f"no episode seed shared with a frozen test set : {not overlap}")
    ok = ok_set and ok_mei and not overlap
    print("SELF-TEST " + ("PASSES" if ok else "FAILS"))
    return 0 if ok else 1


def run_pool(jobs):
    n = max(1, min(10, (os.cpu_count() or 4) - 2))
    print(f"scoring {len(jobs)} (agent, checkpoint) pairs on {len(PRACTICE)} "
          f"practice episodes, {n} in parallel")
    with Pool(n) as pool:
        out = pool.map(score, jobs)
    return {(t, k): (float(np.median(d)), float(np.median(r)), b)
            for t, k, d, r, b in out}


def write_out(path, lines):
    full = os.path.join(HERE, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\nwritten to {path}")


def calibrate(runs_name):
    """How much does practice-set damage move when an agent barely changes?

    ADDED BEFORE THE C4 PREREGISTRATION WAS COMMITTED, because the review of
    the draft asked the right question: nobody had measured how far an agent's
    practice-set median damage moves between checkpoints for reasons that are
    not learning. SAC at a constant learning rate never stops moving its
    weights, and a deterministic policy can flip an action near a threshold,
    so some movement is noise. If that noise were near SETTLE_BAND, the rule
    would say NOT-CONVERGED whatever the agents did -- a rule in name only.

    Phase D2's agents give the measurement, and touch nothing of C4:

      * `final.zip` against `ckpt_50000_steps.zip` -- ONE gradient step apart
        (`_n_updates` 49 900 against 49 899). Their difference is the floor
        of movement that has nothing to do with learning.
      * `ckpt_30000` / `ckpt_40000` / `ckpt_50000` -- 10 000 steps apart, at a
        stage where C1 agents are still learning fast. NOT the C4 situation
        (200k-300k); printed for scale only.

    Practice set only. Writes `results/c4_convergence_calibration.txt`.
    """
    runs = os.path.join(HERE, runs_name)
    keys = ("ckpt_30000", "ckpt_40000", "ckpt_50000", "final")
    jobs, missing = [], []
    for tag in TAGS:
        for k in keys:
            p = os.path.join(runs, tag, "final.zip" if k == "final" else f"{k}_steps.zip")
            if os.path.exists(p):
                jobs.append((tag, p, k))
            else:
                missing.append(p)
    if missing:
        raise SystemExit("missing:\n  " + "\n  ".join(missing))
    out = os.path.join("results", "c4_convergence_calibration.txt")
    if os.path.exists(os.path.join(HERE, out)):
        raise SystemExit(f"{out} exists -- it is never overwritten")
    t0 = time.time()
    res = run_pool(jobs)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("C4 CONVERGENCE RULE -- CALIBRATION on Phase D2's agents, practice set only")
    say(f"agents from {runs_name}/; practice set seed {PRACTICE_SEED}, "
        f"{len(PRACTICE)} episodes; median damage per agent and checkpoint")
    say(f"the rule under test: an agent is settled if its median damage moves "
        f"<= {SETTLE_BAND:.0f} units")
    say("")
    say(f"{'agent':<16}" + "".join(f"{k:>12}" for k in keys)
        + f"{'1 step':>9}{'30-50k':>9}")
    say("-" * 82)
    one, span = {}, {}
    for tag in TAGS:
        dm = [res[(tag, k)][0] for k in keys]
        one[tag] = abs(dm[3] - dm[2])
        span[tag] = max(dm[:3]) - min(dm[:3])
        say(f"{tag:<16}" + "".join(f"{v:>12.1f}" for v in dm)
            + f"{one[tag]:>9.1f}{span[tag]:>9.1f}")
    say("-" * 82)
    o = np.array(list(one.values()))
    say("ONE GRADIENT STEP (final.zip against ckpt_50000), |change| in median damage")
    say(f"  per agent: median {np.median(o):.1f}, max {o.max():.1f}; "
        f"above the band ({SETTLE_BAND:.0f}): {int((o > SETTLE_BAND).sum())} of 16")

    def pdiff(s, k):
        return res[(f"blind_seed{s}", k)][0] - res[(f"sighted_seed{s}", k)][0]
    pair = [abs(pdiff(s, "final") - pdiff(s, "ckpt_50000")) for s in range(8)]
    say(f"  per seed PAIR (blind - sighted): median {np.median(pair):.1f}, "
        f"max {max(pair):.1f}; above the band: "
        f"{sum(p > SETTLE_BAND for p in pair)} of 8")
    sp = np.array(list(span.values()))
    say("30k -> 50k, C1 agents still learning: max - min over three checkpoints")
    say(f"  per agent: median {np.median(sp):.1f}, max {sp.max():.1f}; "
        f"within the band: {int((sp <= SETTLE_BAND).sum())} of 16")
    say(f"({(time.time() - t0) / 60:.1f} min)")
    write_out(out, lines)
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("runs", nargs="?", default=None,
                    help="default runs_c4 (runs_d2 with --calibrate)")
    ap.add_argument("--out", default=os.path.join("results", "c4_convergence.txt"))
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--calibrate", action="store_true",
                    help="score Phase D2's ckpt 30k/40k/50k and final.zip on the "
                         "practice set: how far damage moves with no learning")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if selftest() != 0:
        raise SystemExit("the practice set or the MEI has drifted -- refusing")
    if a.calibrate:
        return calibrate(a.runs or "runs_d2")

    runs_name = a.runs or "runs_c4"
    runs = os.path.join(HERE, runs_name)
    jobs, missing = [], []
    for tag in TAGS:
        for steps in CHECKPOINTS:
            p = checkpoint_path(os.path.join(runs, tag), steps)
            if os.path.exists(p):
                jobs.append((tag, p, steps))
            else:
                missing.append(p)
    if missing:
        raise SystemExit("missing checkpoints:\n  " + "\n  ".join(missing))
    if os.path.exists(os.path.join(HERE, a.out)):
        raise SystemExit(f"{a.out} exists -- it is never overwritten; delete "
                         "it yourself to re-run")

    t0 = time.time()
    res = run_pool(jobs)
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    say("C4 CONVERGENCE -- results/PREREGISTRATION_C4.md section 5b")
    say(f"agents from {runs_name}/; practice set seed {PRACTICE_SEED}, "
        f"{len(PRACTICE)} episodes, NOT the test set")
    say(f"settled: median damage moves <= {SETTLE_BAND:.0f} units across "
        f"{', '.join(f'{c:,}' for c in CHECKPOINTS)} steps")
    say(f"converged: >= {MIN_SETTLED} of 8 settled in EACH arm")
    say("")
    # A C4 checkpoint must belong to a fresh 300 000-step run whose buffer
    # never evicts -- the same four numbers analyse_c4.certify and
    # check_c4_start require, so the three scripts agree on what a C4 agent is.
    bad_budget = [(t, s, b) for (t, s), (_, _, b) in res.items()
                  if b is None or b["num_timesteps"] != s
                  or b["total_timesteps"] != C4_STEPS
                  or b["num_timesteps_at_start"] != 0
                  or b["buffer_size"] != C4_STEPS]
    head = "".join(f"{f'dmg@{c // 1000}k':>11}" for c in CHECKPOINTS)
    say(f"{'agent':<16}{head}{'moves':>8}  {'settled':<8}{'return@300k':>12}"
        f"{'curve: slope/10 ep, se':>30}")
    say("-" * 106)
    settled = {"sighted": 0, "blind": 0}
    for tag in TAGS:
        dm = [res[(tag, c)][0] for c in CHECKPOINTS]
        moves = max(dm) - min(dm)
        ok = moves <= SETTLE_BAND
        settled[tag.split("_")[0]] += ok
        tr = curve_trend(os.path.join(runs, tag))
        trs = ("--" if tr is None else
               f"{tr['slope10']:+8.1f} +/- {tr['se10']:6.1f} ({tr['n']} ep)")
        say(f"{tag:<16}" + "".join(f"{v:>11.1f}" for v in dm)
            + f"{moves:>8.1f}  {'yes' if ok else 'NO':<8}"
            + f"{res[(tag, C4_STEPS)][1]:>12.2f}{trs:>30}")
    say("-" * 106)
    say(f"settled: sighted {settled['sighted']} of 8, blind {settled['blind']} of 8")
    # DESCRIPTIVE, not the rule: the same movement on the quantity the test is
    # about, the per-seed paired difference -- see the docstring.
    moves_pair = []
    for s in range(8):
        p = [res[(f"blind_seed{s}", c)][0] - res[(f"sighted_seed{s}", c)][0]
             for c in CHECKPOINTS]
        moves_pair.append(f"s{s} {max(p) - min(p):.1f}")
    say("paired difference (blind - sighted), max - min over the three points, "
        "DESCRIPTIVE:")
    say("  " + "  ".join(moves_pair))
    conv = all(settled[arm] >= MIN_SETTLED for arm in settled)
    if bad_budget:
        say("")
        for t, s, b in bad_budget:
            say(f"!! {t} at {s}: {FP.format_budget(b)} -- NOT a fresh "
                f"{C4_STEPS:,}-step run")
        conv = False
    say("")
    # WHICH AGENTS the verdict is about, by the hash of the final.zip it
    # scored. analyse_c4.py uses the verdict only if these equal the zips
    # certified in the result files.
    for tag in TAGS:
        b = res[(tag, C4_STEPS)][2]
        say(f"AGENT {tag} final.zip sha {b['sha'] if b else 'unreadable'}")
    # The line analyse_c4.py parses. Keep its shape.
    say(f"VERDICT {'CONVERGED' if conv else 'NOT-CONVERGED'} "
        f"sighted {settled['sighted']}/8 blind {settled['blind']}/8 "
        f"band {SETTLE_BAND:.0f} need {MIN_SETTLED} runs {runs_name}"
        + (" BUDGET-MISMATCH" if bad_budget else ""))
    say(f"({(time.time() - t0) / 60:.1f} min)")
    write_out(a.out, lines)
    return 0


if __name__ == "__main__":
    sys.exit(main())
