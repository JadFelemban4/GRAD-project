"""evaluate.py — Phase D's evaluation protocol. TWENTY FIXED EPISODES.

    python evaluate.py                          the hand-written policies only
    python evaluate.py runs/sighted_seed0        add one trained agent
    python evaluate.py runs/sighted_seed0 runs/blind_seed0    sighted vs blinded
    python evaluate.py --out results/<new file>.txt runs/... runs/...
                                               (an existing --out is refused)

EVERY RESULT CARRIES THE PLANT THAT PRODUCED IT   (AUDIT2.md C2-1)
------------------------------------------------------------------
This file used to print its scenario as a hardcoded sentence:

    print(f"scenario: 12 % at 130 km/h, 42 C, {DURATION:.0f} s, dt {DT}")

RETIRED-OK: 572.8, 857 -- the six-speed figures this paragraph exists to retire
That sentence was true, and it was **byte-identical on two different plants**.
On 18 September two agents were trained on an invented six-speed gearbox and
scored here at +11.7 points; on 19 September commit `27e720c` replaced the
gearbox with the car's real ZF 8HP51; the result file was kept. The same
command on the corrected plant prints +7.5, with every row moved -- baseline
damage 572.8 -> 959.8, peak 857 -> 884 C -- and the +11.7 cannot be regenerated
from this tree at all, because the `engine_env.py` it needs no longer exists
here.

So the scenario line is now built from `inspect.signature(make_grade_climb)`
rather than typed, and a full fingerprint block (gear ratios, final drive,
crank-angle step, protection trigger, scenario tuple, a hash of the twenty
frozen episodes, the SHA of the three physics files) is printed, written into
the result file, and CHECKED against each model's `runs/<tag>/meta.json`.

**A model whose fingerprint disagrees is refused.** Not warned about -- refused,
with the disagreeing fields named. `--force-plant-mismatch` overrides it and
stamps the mismatch into the result file in full, because the only thing worse
than refusing is producing a number whose provenance is a footnote.

A model with no `meta.json` is refused too. That is the pre-fingerprint case --
`runs_sixspeed_18sep/` is exactly it -- and "we do not know which plant this
agent saw" is the finding, not an inconvenience.

================================================================================
THE TWENTY EPISODES ARE FROZEN. DO NOT EDIT `EPISODES`.
Changing the test set after seeing a result is the one mistake this project
cannot recover from -- CLAUDE.md, "What to do next", step 5. If the protocol has
to change, that is a new protocol with a new name, and BOTH get reported.
================================================================================

WHY A FIXED SET EXISTS AT ALL, and it is not bureaucracy.

`SupervisoryTunerEnv.reset()` draws a fresh preference vector every episode --
how much the agent is asked to weigh torque tracking against fuel and against
component life. So **every episode is scored with a different ruler**, and an
episode return cannot be compared with the next one.

That is not a hypothetical. The first training run, 50 000 steps on seed 0,
produced eleven episodes ranging from **-506.4 to +643.6**, and `train.py`
summarised them as "first 5 -115.99 -> last 5 +103.71, the curve improved". The
largest positive episode in that run (+643.6) is in the FIRST five. **With that
spread and eleven samples, first-five-versus-last-five is not evidence of
learning.** It is the weight draw.

This file removes the ruler as a variable: twenty (seed, weights) pairs, drawn
once from seed 20260918, written below as literals, and used identically for
every policy. A difference between two rows is then a difference between the
POLICIES.

WHAT IS REPORTED, and why median and IQR rather than a mean.

Damage is an exponential in temperature, so its distribution is skewed and a
single hot episode drags a mean around. The median says what a typical episode
costs; the interquartile range says how much the policy varies. Report both, and
report the worst episode too -- a protection policy that is good on average and
occasionally terrible is not a protection policy.

THE COMPARATORS, and the middle one is the one that matters.

  baseline ECU    the production-representative controller, no supervision
  reactive        acts on the turbine temperature it can already measure
  current-grade   acts on the slope the car is on RIGHT NOW, with NO preview
  agent           trained, with preview
  agent (blind)   the same training with the preview channel zeroed

**`current-grade` is the honest comparator for preview**, because it is what a
vehicle gets for free from a nose-down accelerometer. Beating `baseline` proves
supervision helps; only beating `current-grade` proves the PREVIEW helped. See
AUDIT.md C3.
"""
import argparse
import inspect
import os

import numpy as np

import check_premise as C
import fingerprint as FP
import random_road as RR
from engine_env import SupervisoryTunerEnv, make_grade_climb, TURB_PROTECT_K

DT = 1.0
DURATION = 720.0

# Drawn once from numpy's default_rng(20260918), exactly as reset() draws them.
# (episode seed, (w_track, w_fuel, w_life))
EPISODES = (
    (1000, (0.690154, 0.012829, 0.297017)),
    (1001, (0.682741, 0.181419, 0.135840)),
    (1002, (0.690313, 0.060454, 0.249233)),
    (1003, (0.484162, 0.022753, 0.493085)),
    (1004, (0.583678, 0.036390, 0.379932)),
    (1005, (0.529443, 0.168930, 0.301627)),
    (1006, (0.690245, 0.057769, 0.251987)),
    (1007, (0.590381, 0.320322, 0.089297)),
    (1008, (0.699723, 0.046890, 0.253387)),
    (1009, (0.506395, 0.277739, 0.215866)),
    (1010, (0.538101, 0.136805, 0.325095)),
    (1011, (0.552078, 0.178668, 0.269254)),
    (1012, (0.540735, 0.424900, 0.034366)),
    (1013, (0.592943, 0.187398, 0.219659)),
    (1014, (0.685668, 0.285069, 0.029263)),
    (1015, (0.571092, 0.379759, 0.049149)),
    (1016, (0.654867, 0.283297, 0.061836)),
    (1017, (0.508297, 0.185553, 0.306150)),
    (1018, (0.673297, 0.013299, 0.313404)),
    (1019, (0.592214, 0.097373, 0.310413)),
)

# ==============================================================================
# PHASE D2 -- THE RANDOMISED CLIMB. A SECOND FROZEN SET, AND IT IS FROZEN TOO.
# Committed 22 September 2026, BEFORE any Phase D2 agent was trained, under
# results/PREREGISTRATION_D2.md. Same rule as EPISODES above: do not edit it
# after a result exists. A different set is a different protocol.
#
# (episode seed, weights, climb start in s, climb grade)
#
# THE SEEDS AND WEIGHTS ARE PHASE D's TWENTY, UNCHANGED, so the only thing that
# differs between Phase D's episode k and this one is the ROAD. The roads are a
# Latin hypercube over [120, 300] s x [12, 16] %, drawn once from
# numpy default_rng(20260922) by random_road.frozen_episodes(), which
# `python random_road.py` re-runs and checks against this literal. Two of them
# (13.988 % and 14.029 %) sit just past the gearbox shift and carry the
# thinnest margins of the twenty, +12.5 and +13.3 K (check_random_road.py, D).
# The sweep's deepest point, 13.73 % at +6.9 K, falls between strata and no
# frozen episode lands on it -- stated so nobody reads the set as covering it.
# All twenty bind.
# ==============================================================================
EPISODES_D2 = (
    (1000, (0.690154, 0.012829, 0.297017), 141.05, 0.13314),
    (1001, (0.682741, 0.181419, 0.135840), 281.95, 0.15025),
    (1002, (0.690313, 0.060454, 0.249233), 181.29, 0.12717),
    (1003, (0.484162, 0.022753, 0.493085), 153.75, 0.15438),
    (1004, (0.583678, 0.036390, 0.379932), 282.64, 0.12237),
    (1005, (0.529443, 0.168930, 0.301627), 128.45, 0.15393),
    (1006, (0.690245, 0.057769, 0.251987), 247.53, 0.15802),
    (1007, (0.590381, 0.320322, 0.089297), 262.02, 0.15729),
    (1008, (0.699723, 0.046890, 0.253387), 228.71, 0.14029),
    (1009, (0.506395, 0.277739, 0.215866), 296.25, 0.14849),
    (1010, (0.538101, 0.136805, 0.325095), 163.40, 0.14227),
    (1011, (0.552078, 0.178668, 0.269254), 204.50, 0.14478),
    (1012, (0.540735, 0.424900, 0.034366), 199.65, 0.13988),
    (1013, (0.592943, 0.187398, 0.219659), 238.26, 0.14640),
    (1014, (0.685668, 0.285069, 0.029263), 137.66, 0.13012),
    (1015, (0.571092, 0.379759, 0.049149), 217.89, 0.12963),
    (1016, (0.654867, 0.283297, 0.061836), 226.65, 0.12016),
    (1017, (0.508297, 0.185553, 0.306150), 271.29, 0.13459),
    (1018, (0.673297, 0.013299, 0.313404), 187.71, 0.12567),
    (1019, (0.592214, 0.097373, 0.310413), 167.38, 0.13651),
)

PROTOCOLS = {
    # name: (episode set, header, result-file prefix)
    "phase-d": (EPISODES, "PHASE D EVALUATION", "phase_d"),
    "d2": (EPISODES_D2, "PHASE D2 EVALUATION (randomised climb)", "d2"),
}


def run_episode(policy, seed, weights, use_preview=True, road=None):
    """One episode with the weights PINNED after reset, so every policy sees
    the same ruler on the same episode.

    `road` is None for Phase D's fixed climb, or a (start_s, grade) pair for a
    Phase D2 episode -- in which case the cycle is built by random_road.climb,
    the same function training draws through, so there is one definition of a
    D2 road and not two.
    """
    if road is None:
        cycle = make_grade_climb(duration=DURATION, dt=DT)
    else:
        cycle = RR.climb(road[0], road[1], duration=DURATION, dt=DT)
    env = SupervisoryTunerEnv(cycle, dt=DT, seed=seed, use_preview=use_preview)
    obs, _ = env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)   # override the fresh draw
    obs = env._obs()
    ret, peak = 0.0, 0.0
    while True:
        obs, r, term, trunc, info = env.step(policy(env, obs))
        ret += r
        peak = max(peak, info["t_turb"])
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(ret=ret, damage=s["damage"], fuel=s["fuel"],
                torque_viol=s["torque_viol"], peak_turb=peak - 273.15,
                knock=s["knock_events"])


def agent_policy(model, use_preview=True):
    """Wrap a stable-baselines3 model as a policy(env, obs) callable."""
    def p(env, obs):
        a, _ = model.predict(obs, deterministic=True)
        return a
    return p


def summarise(rows, key):
    v = np.array([r[key] for r in rows], dtype=float)
    q1, med, q3 = np.percentile(v, [25, 50, 75])
    return med, q3 - q1, v.max(), v.min()


def scenario_line(protocol="phase-d"):
    """The scenario sentence, READ FROM THE CYCLE FUNCTION rather than typed.

    AUDIT2.md C2-1 and H2-10. The literal this replaces was identical on the
    six-speed and on the ZF, which is why `results/phase_d_seed0.txt` cannot be
    told apart from a run on a plant that no longer exists. A sentence built
    from `inspect.signature` changes when the experiment changes.

    For Phase D2 it is built from `random_road.RANGES` for the same reason.
    """
    if protocol == "d2":
        (s0, s1), (g0, g1) = RR.RANGES["start_s"], RR.RANGES["grade"]
        return (f"scenario: climb from {s0:.0f}-{s1:.0f} s at {100 * g0:.0f}-"
                f"{100 * g1:.0f} %, per episode, {RR.V_KMH:.0f} km/h, "
                f"{RR.T_AMB_K - 273.15:.0f} C, {DURATION:.0f} s, dt {DT}")
    d = inspect.signature(make_grade_climb).parameters
    grade = float(d["grade"].default)
    v = float(d["v_kmh"].default)
    t_amb = float(d["t_amb"].default)
    return (f"scenario: {100 * grade:.0f} % at {v:.0f} km/h, "
            f"{t_amb - 273.15:.0f} C, {DURATION:.0f} s, dt {DT}")


def check_model_fingerprint(path, live, force):
    """Refuse a model whose `meta.json` describes a different plant.

    Returns the lines to record in the result file: empty when the model
    matches, a full account of the disagreement when `force` let it through.
    """
    meta_path = os.path.join(path.rstrip("/\\"), "meta.json")
    stored = FP.read(meta_path)

    if stored is None:
        msg = (f"\n{path} has no meta.json.\n"
               "It predates the plant fingerprint (AUDIT2.md C2-1), so nothing "
               "records which\nplant it was trained on -- and this project has "
               "already shipped one result\nthat was produced on a gearbox "
               "replaced seven hours later. Retrain it with\nthe current "
               "train.py, or pass --force-plant-mismatch and expect to defend "
               "the\nnumber without provenance.")
        if not force:
            raise SystemExit(msg)
        print(msg)
        return [f"!! {path}: NO meta.json -- plant unknown, --force-plant-mismatch used"]

    bad = FP.compare(stored, live)
    if not bad:
        # The dt asymmetry is legitimate and permanent (train 0.2, score 1.0),
        # so it is reported rather than refused -- but it is reported EVERY
        # time, because CLAUDE.md records it as an open problem and AUDIT2.md
        # H2-2 measures the headline percentage moving 37.0 -> 30.1 % on the
        # step alone. A reader of a result file should not have to know that.
        t_dt = stored.get("train_dt")
        if t_dt is not None and abs(float(t_dt) - DT) > 1e-9:
            return [f"note {os.path.basename(path.rstrip('/'))}: trained at "
                    f"dt {float(t_dt):g}, scored at dt {DT:g} "
                    f"(known, unresolved -- AUDIT2.md H2-2)"]
        return []

    lines = [f"!! {path}: PLANT MISMATCH"]
    for k, was, now in bad:
        lines.append(f"     {k:<18} model {was!r}  live {now!r}")
    if not force:
        # Printed HERE only on the refusing path, because that path raises
        # before main() gets the chance. When --force lets the run continue,
        # main() prints these same lines through say(), which also captures
        # them for --out -- printing in both places showed the block twice.
        print("\n".join(lines))
        raise SystemExit(
            f"\nREFUSING to evaluate {path}: it was trained on a different "
            "plant.\nScoring it here would produce a number that belongs to "
            "neither -- which is\nexactly what results/phase_d_seed0.txt is "
            "(AUDIT2.md C2-1). Retrain on this\ntree, or pass "
            "--force-plant-mismatch and quote the mismatch beside the number.")
    lines.append("     --force-plant-mismatch was given; the rows below are "
                 "NOT a Phase D result.")
    return lines


def main():
    ap = argparse.ArgumentParser(description="Phase D evaluation protocol.")
    ap.add_argument("models", nargs="*",
                    help="runs/<tag> directories; 'blind' in the name means "
                         "the preview channel was zeroed during training")
    ap.add_argument("--out", default=None,
                    help="also write the whole report, fingerprint block "
                         "included, to this file")
    ap.add_argument("--force-plant-mismatch", action="store_true",
                    help="evaluate a model whose meta.json disagrees with this "
                         "tree, or has none. The mismatch is stamped into the "
                         "output; it is never silent.")
    ap.add_argument("--protocol", choices=sorted(PROTOCOLS), default="phase-d",
                    help="which frozen episode set: 'phase-d' (the fixed climb, "
                         "the default and unchanged) or 'd2' (the randomised "
                         "climb). Each has its own fingerprint, so an agent "
                         "trained under one is refused by the other.")
    ap.add_argument("--overwrite", action="store_true",
                    help="replace an existing --out file. Without it an "
                         "existing file is refused: results/*.txt are "
                         "committed evidence, and the guard belongs in the "
                         "writer, not only in run_phase_d.py.")
    ap.add_argument("--label", default=None,
                    help="title the report by EXPERIMENT rather than by "
                         "protocol. C4 is scored on D2's protocol, and without "
                         "this its result files would open 'PHASE D2 "
                         "EVALUATION'. run_phase_d.py passes it for any "
                         "non-default result prefix.")
    a = ap.parse_args()
    episodes, header, _ = PROTOCOLS[a.protocol]
    if a.out and os.path.exists(a.out) and not a.overwrite:
        raise SystemExit(f"\n{a.out} exists. Result files are evidence and are "
                         "not overwritten by default --\nscore into a new file, "
                         "or pass --overwrite and say why in the commit.")

    # Everything printed is also captured, so the result file and the terminal
    # cannot disagree -- the failure mode that let a result file carry a
    # scenario header its own run did not have.
    captured = []

    def say(*parts):
        line = " ".join(str(p) for p in parts)
        print(line)
        captured.append(line)

    live = FP.plant_fingerprint(protocol=a.protocol, eval_dt=DT,
                                eval_duration=DURATION)

    policies = [
        ("baseline ECU",  C.p_neutral,     True),
        ("reactive",      C.p_reactive,    True),
        ("current-grade", C.p_grade_now,   True),
    ]

    provenance = []
    for path in a.models:
        try:
            from stable_baselines3 import SAC
        except ImportError:
            raise SystemExit('stable-baselines3 is not installed.\n'
                             '    pip install "stable-baselines3[extra]"')
        provenance += check_model_fingerprint(path, live, a.force_plant_mismatch)
        # HOW LONG THIS AGENT WAS TRAINED, from the zip. The fingerprint cannot
        # tell a C4 agent from a Phase D2 one -- same plant, scenario and
        # episodes -- and meta.json's steps_requested is advisory and is not
        # rewritten by a resume. The zip's own counters are written by the
        # training loop, and its hash names exactly which artefact was scored.
        # `analyse_c4.py` reads this line back.
        mdir = path.rstrip("/\\")
        provenance.append(f"model {mdir}: "
                          f"{FP.format_budget(FP.model_budget(mdir + '/final.zip'))}")
        blind = "blind" in path
        model = SAC.load(path.rstrip("/\\") + "/final")
        policies.append((("agent (blind)" if blind else "agent") + " " + path,
                         agent_policy(model), not blind))

    frozen = "18 Sep 2026" if a.protocol == "phase-d" else "22 Sep 2026"
    if a.label:
        say(f"{a.label} -- scored on the '{a.protocol}' protocol, "
            f"{len(episodes)} FIXED EPISODES, frozen {frozen}")
    else:
        say(f"{header} -- {len(episodes)} FIXED EPISODES, frozen {frozen}")
    say(scenario_line(a.protocol))
    say(f"trigger:  {TURB_PROTECT_K - 273.15:.0f} C")
    say("")
    say(FP.format_block(live, "PLANT FINGERPRINT (this run)"))
    for line in provenance:
        say(line)
    say("")
    say(f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
        f"{'fuel med':>10}{'peak C':>9}")
    say("-" * 77)

    out = {}
    for name, pol, prev in policies:
        if a.protocol == "phase-d":
            rows = [run_episode(pol, s, w, prev) for s, w in episodes]
        else:
            rows = [run_episode(pol, s, w, prev, road=(st, g))
                    for s, w, st, g in episodes]
        out[name] = rows
        dm, di, dw, _ = summarise(rows, "damage")
        fm, _, _, _ = summarise(rows, "fuel")
        pk = max(r["peak_turb"] for r in rows)
        say(f"{name:<28}{dm:>12.1f}{di:>9.1f}{dw:>9.1f}{fm:>10.0f}{pk:>9.0f}")

    say("-" * 77)
    base = np.median([r["damage"] for r in out["baseline ECU"]])
    for name in out:
        if name == "baseline ECU":
            continue
        med = np.median([r["damage"] for r in out[name]])
        say(f"  {name:<26} cuts median damage {100*(1-med/base):5.1f} %")

    grade = next((n for n in out if n.startswith("current-grade")), None)
    agent = next((n for n in out if n.startswith("agent ") and "blind" not in n), None)
    blind = next((n for n in out if "blind" in n), None)

    say("")
    if agent and grade:
        am = np.median([r["damage"] for r in out[agent]])
        g = np.median([r["damage"] for r in out[grade]])
        edge = 100*(1-am/base) - 100*(1-g/base)
        say(f"  AGENT over CURRENT-GRADE: {edge:+.1f} points")
    if agent and blind:
        am = np.median([r["damage"] for r in out[agent]])
        b = np.median([r["damage"] for r in out[blind]])
        say(f"  SIGHTED over BLINDED:     {100*(1-am/base) - 100*(1-b/base):+.1f}"
            " points   <- THE ABLATION")
        # AUDIT2.md C2-1. This line used to end "This is the project's result",
        # unconditionally, printed under a number produced on a plant the
        # repository had already replaced. The fingerprint block above is what
        # makes the claim checkable, so the claim now says so.
        say("  It is the project's result only if the fingerprint block above is "
            "the plant\n  every figure beside it was measured on. That is now "
            "checkable -- check it.")
    elif agent:
        say("  No blinded agent supplied, so THERE IS NO ABLATION YET. Train one\n"
            "  with --no-preview and pass it as the second argument. Until then\n"
            "  nothing here separates preview from the rest of the policy.")
    else:
        say("  Hand-written policies only. AUDIT.md C3: these say the environment\n"
            "  rewards anticipation; they do NOT say what an agent would gain, and\n"
            "  five scenarios have now shown preview losing to current-grade with\n"
            "  policies a human wrote. Only a trained pair settles it.")

    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write("\n".join(captured) + "\n")
        print(f"\nwritten to {a.out}")


if __name__ == "__main__":
    main()
