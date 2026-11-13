"""evaluate.py — Phase D's evaluation protocol. TWENTY FIXED EPISODES.

    python evaluate.py --engine b58                          the hand-written policies only
    python evaluate.py --engine b58 runs/sighted_seed0        add one trained agent
    python evaluate.py --engine b58 runs/sighted_seed0 runs/blind_seed0    sighted vs blinded
    python evaluate.py --engine b58 --out results/<new file>.txt runs/... runs/...
                                               (an existing --out is refused)
    python evaluate.py --engine b58 --protocol d34 --reward-knock out --scores-out <outside>/S.json
                       [--records-out <outside>/DIR] [--out <report>.txt] [--jobs N] runs/b58h_dt1/<each run>
    python evaluate.py --engine b58 --protocol d34 --practice --reward-knock out
                       --scores-out <outside>/P.json [--jobs N] runs/b58h_pilot_dt1/<each run>
                                               (DECISION 34'S PROTOCOL, below)

--engine IS REQUIRED (20 October 2026, decision 24: the H/tau test runs four
engines). It names the plant the episodes run on (engines.get), and the
fingerprint's FATAL `engine` and `engine_sha` fields then refuse a model trained
on another. A meta.json of fingerprint schema 2 -- every agent trained before the
four-engine build, X1's and X2's among them -- names no engine and is refused
with a message that says so: those agents are scored on main. A meta.json of
schema 3, written before the plant commit (ORDER step 14), is refused with its
own message: it records no transmission, backend pair, H or knock option.

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
here. (Those are the 19-21 September plant's figures. On the plant of
8 October -- derived from the logs, merged 30 September, the thermal network
sub-stepped and the climb ramped -- the baseline row is 848.1 at 883 C.)

So the scenario line is now built from the plant's own scenario (it was
`inspect.signature(make_grade_climb)`'s defaults until 20 October 2026)
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

THE HEADER IS ALSO CHECKED AGAINST THE CYCLE   (JMF-2340550, 3207727)
----------------------------------------------------------------------
The other branch removed the same literal a different way: it read the
scenario off the cycle object. Both are kept. `scenario_line` states the
plant's declared scenario -- the source fingerprint.py's FATAL `scenario` field
uses, so the header and the refusal cannot disagree -- and then builds the cycle
exactly as `run_episode` builds it (`episode_cycle`) and refuses to print a
header the cycle does not carry. A declared value the road builder stopped
honouring would otherwise pass unseen.

DAMAGE TWO WAYS   (JMF-2340550, cbb8d09)
----------------------------------------
`run_episode` also returns `damage_thermal`: the same damage model without its
knock term, because the knock model is untested against this car (CLAUDE.md,
"THE KNOCK MODEL IS NOT VALIDATED"). A reporting column only -- the episode,
the policy and the reward are untouched. It is printed in its own indented
block BELOW the policy table, never as a sixth column of it:
`analyse_phase_d.parse`, which analyse_phase_d2.py and analyse_c4.py import,
reads the LAST FIVE fields of each policy row, and a sixth column makes it read
the IQR as the damage median without an error.

THE REWARD'S KNOCK OPTION   (rows 113 (5), 117; the plant commit P)
--------------------------------------------------------------------
`--reward-knock in|out` is the environment's knock option, the reward an agent
trained with: 'in', X1's, keeps the knock term in r_life, and 'out' is row 113
(5)'s primary reading. It is a FATAL field of fingerprint schema 4, so an agent
trained 'out' is refused unless the flag says 'out'. Absent, it reads 'in' on
phase-d and d2, X1's agents' reward. It moves `ret` alone: every score
`run_episode` returns comes from the episode's damage bookkeeping and info,
which the option does not touch.

RECORDING   (JMF-2340550, 74de99a)
----------------------------------
`run_episode(..., record=new_record())` appends every step -- the action, what
the actuators applied, the observation, the reward terms and the engine state
-- for record_agents.py and knock_margin.py. It reads the environment after
each step and writes nothing into it; the scores are identical with or
without it.

DECISION 34'S PROTOCOL   (ORDER step 16, commit V; rows 95, 103 (4), 112, 117, 118, 143, 146 (3), 147)
--------------------------------------------------------------------------------------------------------
`--protocol d34` scores the B58 study's agents (row 147) on decision 34's twenty roads, as R4's
redraws.json reads them under version 6 (row 95 (2); fingerprint.d34_roads), road k with EPISODES[k]'s
seed and weights, which are read and never edited. Scores are computed on the version-6 set only: the
version-5 reading and the drop list are reported in the scores' provenance, never scored (row 95). The
current re-verification record (four_engine_roads.current_reverify, row 140) must be EQUAL, name the live
roads.json and redraws.json, have run on an ancestor of HEAD and keep every plant_sha (decision34_roads).

Each agent is scored as decision 29 reports it, the action average of its checkpoints
(training_recipe.AveragedPolicy, load_agent; row 118), at its own H: read from its meta.json and checked
against r x tau from the roads record (arm_of; row 117). Each is checked against the decision-34
fingerprint it trained under (live_decision34), its train_backend read from the committed
results/EPA_BACKEND.json (Tb's record; committed_train_backend), paired with its seed's blinded agent by
row 117's rule (pairing_problems), and every agent of the engine must have trained on one environment
(environment_problems; row 143 (5)). --force-plant-mismatch is refused here, and --reward-knock is
required, never read from meta.json. The baseline ECU, reactive and current-grade run once per road
(score_set), in a spawn pool that gives the same numbers at any --jobs.

The scores follow four-engine-scores/1 (scores_document): no knock is damage_thermal, the primary
reading; with knock is damage, "not converged in dt on these roads" (with_knock_label). Each policy's
fuel, the baseline ECU's fuel and the share of demand steps short of the tracking tolerance, road by
road, ride in the provenance (row 147 (5); delivery_block), with the version-5 slots, the re-verification
record, every agent's H, r and manifest, the versions, the platform and the device (interface sheet
12.7). --records-out keeps the baseline ECU's and each agent's per-step t_turb, t_oil and ki
(write_records). --practice
scores row 96's ten practice roads instead, read from roads.json and regenerated from nothing
(practice_set), in the same form, for decision 29's pilot (rows 103 (4), 112): pilot_spread reads s_p
from that document, the report prints it, and the recipe checks (the learning rate at 0, the average
taken) ride beside it; its provenance keeps the decision-34 set's episodes_sha under trained_under only.

THE DECLARED TRANSFER ROUTE (row 147 (11)). check_transfer lets a decision-34 agent be scored off its own
roads -- the locked climb, the logged drives, the conditions battery, b58h_descriptive.py's three
descriptive rows -- when every FATAL field but scenario and episodes_sha is the live one. It prints both
of those, the trained and the scored, and it takes no force. The phase-d and d2 body of main() below is
unchanged; run_episode's loop became _drive, step for step, the one loop every route runs.

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
import json
import os

import numpy as np

import check_premise as C
import engines
import fingerprint as FP
import random_road as RR
from engine_env import (PREVIEW_H_S, REWARD_KNOCK_DEFAULT, TRACK_TOL, SupervisoryTunerEnv, damage_rate,
                        locked_climb)

HERE = os.path.dirname(os.path.abspath(__file__))

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
#
# THOSE MARGINS ARE THE 22 SEPTEMBER PLANT'S (plant_sha b5a3069f32a83754). On
# the plant derived from the logs (JMF-2340550, plant_sha c236a8db3e201090,
# measured 29-30 September with the neutral policy) all twenty still bind and
# the same two roads are still the thinnest, at +12.2 and +13.1 K; but 13.73 %
# at a 300 s start is +75.5 K there -- the gear hand-back moved to between
# 13.76 and 13.988 %, and the new deepest point is unmeasured. Re-run
# check_random_road.py before anything is trained or scored on this set.
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

# ==============================================================================
# DECISION 34'S PROTOCOL (ORDER step 16, commit V; interface sheet sections 8, 12.7 and 17). A protocol
# of its own, beside PROTOCOLS, which keeps its two entries (app/results_data.py reads them): --protocol
# takes sorted(PROTOCOLS) + [DECISION_34]. The name is fingerprint.plant_fingerprint's (schema 4).
# ==============================================================================
DECISION_34 = "d34"
D34_HEADER = "DECISION 34 EVALUATION"
PRACTICE_HEADER = "PRACTICE EPISODES (row 96) -- NOT THE TEST"
# the study's analysis reads this schema; a test pins the two strings equal (mistake 10), and this file
# never imports the analysis (row 121)
SCORES_SCHEMA = "four-engine-scores/1"
PRACTICE_SCHEMA = "four-engine-practice/1"
N_D34_ROADS = 20                     # decision 34's twenty, road k with EPISODES[k] (row 101)
N_PRACTICE = 10                      # row 96's practice roads
REDRAW_READING = "version 6"         # the reading that is scored (row 95 (2))
VERSION_5_READING = "version 5 (every engine gating)"     # epa_roads.redraw's name for the other one
# each reading's damage, as run_episode names them: no knock (the primary reading) and with knock
READING_KEYS = {"no_knock": "damage_thermal", "with_knock": "damage"}
# run_episode's dict, its keys in their order: app/agent_trace.py and app.test_agents compare whole dicts
EPISODE_KEYS = ("ret", "damage", "damage_thermal", "fuel", "torque_viol", "peak_turb", "knock")
# the hand-written policies, as main() runs them, each once per road; the baseline ECU gives D_base
HAND_POLICIES = (("baseline ECU", "p_neutral"), ("reactive", "p_reactive"), ("current-grade", "p_grade_now"))
BASELINE = "baseline ECU"
# TORQUE DELIVERY (row 147 (5)): a demand step asks for more than DEMAND_NM, the floor of the reward's
# reference torque t_ref (engine_env.SupervisoryTunerEnv.step, max(torque_req, 40)); it is short when the
# torque delivered falls more than the reward's tolerance TRACK_TOL below the request. logged_check.py's
# T criterion counts the same steps (logged_check.DEMAND_NM; a test pins the two equal, since this file
# may not import that one, row 121)
DEMAND_NM = 40.0
# THE DECLARED TRANSFER ROUTE (row 147 (11)): the two FATAL fields an agent scored off its own roads may
# differ in, each printed, trained and scored (check_transfer)
TRANSFER_EXEMPT = ("scenario", "episodes_sha")
# ONE ENVIRONMENT (row 143 (5); CLAUDE.md rules 3 and 5): what every agent of an engine must share,
# config.json's versions, device and machine (train.run_config) and meta.json's advisory python and
# numpy (fingerprint.plant_fingerprint; a key that no meta.json holds reads None for every agent)
ENV_KEYS = (("config.json", ("versions", "python")), ("config.json", ("versions", "stable_baselines3")),
            ("config.json", ("versions", "torch")), ("config.json", ("versions", "gymnasium")),
            ("config.json", ("versions", "numpy")), ("config.json", ("device",)),
            ("config.json", ("machine", "system")), ("config.json", ("machine", "processor")),
            ("config.json", ("machine", "cpus")), ("meta.json", ("python",)), ("meta.json", ("numpy",)))
# the one ENV_KEYS entry no schema-4 meta.json records: fingerprint.plant_fingerprint writes python and never
# numpy, whose version config.json's versions.numpy carries (train.run_config). It reads None for every
# agent, so its absence is not refused; every other value must be recorded (environment_problems)
ENV_UNRECORDED = ("meta.json numpy",)


# What record_agents.py keeps of every evaluation step (29 September 2026), read
# off the environment AFTER the step, so the episode itself is untouched. Since
# 7 October the fields are defined once, in step_record.py, for every script
# that runs episodes: the 29 September fields under their old names, plus the
# road speed, the gear, the parallel baseline car and the running totals.
def _record_step(record, env, a, obs_before, r, info):
    """Append one step. `action` is what the policy returned, in [-1, 1];
    `applied` is what the actuators actually did after the slew limit and the
    bounds, in physical units (spark trim deg, lambda trim, boost trim kPa, fan
    duty, pump duty) -- the two differ whenever the policy asks for more than
    the slew allows. step_record.py lists every field."""
    import step_record
    step_record.step(record, env, a, obs_before, r, info)


def new_record():
    import step_record
    return step_record.new()


def episode_cycle(road=None, *, plant):
    """The cycle an evaluation episode runs on -- ONE definition, used by
    run_episode and by scenario_line's check, so the header cannot describe a
    road the episodes did not drive.

    `road` is None for Phase D's fixed climb -- the plant's locked climb -- or a
    (start_s, grade) pair for a Phase D2 episode -- in which case the cycle is
    built by random_road.climb, the same function training draws through, so
    there is one definition of a D2 road and not two. `plant` is required.
    """
    if road is None:
        return locked_climb(plant, duration=DURATION, dt=DT)
    # D2's roads are built from random_road's constants, the Supra's locked
    # climb, not from the plant: another car's is refused (21 October 2026)
    RR.check_plant(plant)
    return RR.climb(road[0], road[1], duration=DURATION, dt=DT)


def run_episode(policy, seed, weights, use_preview=True, road=None, record=None, *, plant,
                reward_knock=REWARD_KNOCK_DEFAULT):
    """One episode with the weights PINNED after reset, so every policy sees
    the same ruler on the same episode.

    `road`: see episode_cycle. `record`, if given (new_record()), receives
    every step: the action, what the actuators did, the observation and the
    engine's state. It only reads; the scores are identical with or without it
    (record_agents.py checks). `plant` (engines.get) is required.
    `reward_knock` is the environment's knock option (rows 113 (5), 117): only
    `ret` depends on it; damage, damage_thermal, fuel, torque_viol, peak_turb and
    knock are the same in both modes.

    THE LOOP IS _drive's SINCE COMMIT V (ORDER step 16; interface sheet 8): moved
    there step for step, so decision 34's episodes run the one loop this one
    runs. The dict returned here keeps exactly its seven keys, in their order
    (EPISODE_KEYS): app/agent_trace.py and app.test_agents compare whole dicts.
    """
    env = SupervisoryTunerEnv(episode_cycle(road, plant=plant), plant=plant, dt=DT, seed=seed,
                              use_preview=use_preview, reward_knock=reward_knock)
    env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)   # override the fresh draw
    out = _drive(env, policy, plant=plant, record=record, observe=None)
    return {k: out[k] for k in EPISODE_KEYS}


def _drive(env, policy, *, plant, record, observe):
    """The step loop of every scored episode (run_episode's until commit V, moved
    here step for step; interface sheet 8). `env` has been reset and its weights
    pinned by the caller; the first observation is read here, after the pin, as
    run_episode read it. `record` (new_record(), or None) receives every step, as
    before; `observe` (a callable observe(env, action, info), or None) is called
    after each step and only reads: b58h_descriptive.py counts logged_check's and
    conditions_test's quantities through it. Neither moves a score.

    Returns run_episode's seven values and, beside them, what decision 34's
    scores carry (row 147 (5); interface sheet 12.7): `steps`; `demand_steps`
    and `short_steps`, the steps asking more than DEMAND_NM and those of them
    delivered more than TRACK_TOL short; `fuel_base` and `damage_base`, the
    parallel baseline network's; and `trace`, each step's t_turb, t_oil and ki
    as the environment reported them (write_records keeps them)."""
    obs = env._obs()
    ret, peak, thermal = 0.0, 0.0, 0.0
    steps = demand = short = 0
    trace = {"t_turb": [], "t_oil": [], "ki": []}
    while True:
        a = policy(env, obs)
        obs_before = obs
        obs, r, term, trunc, info = env.step(a)
        if record is not None:
            _record_step(record, env, a, obs_before, r, info)
        if observe is not None:
            observe(env, a, info)
        ret += r
        peak = max(peak, info["t_turb"])
        # DAMAGE TWO WAYS (JMF-2340550, 28 September): the same damage model
        # without its knock term, because the knock model is untested against
        # this car. A REPORTING column only -- the episode, the policy and the
        # reward are untouched.
        thermal += damage_rate(info["t_turb"], info["t_oil"], cal=plant.engine.damage) * env.dt
        # TORQUE DELIVERY (row 147 (5)): counted from info, after the step; nothing is written back
        steps += 1
        req = info["torque_req"]
        if req > DEMAND_NM:
            demand += 1
            short += int(info["torque"] < (1.0 - TRACK_TOL) * req)
        for key in trace:
            trace[key].append(info[key])
        if term or trunc:
            break
    s = info["episode_summary"]
    return dict(ret=ret, damage=s["damage"], damage_thermal=thermal, fuel=s["fuel"],
                torque_viol=s["torque_viol"], peak_turb=peak - 273.15,
                knock=s["knock_events"], steps=steps, demand_steps=demand, short_steps=short,
                fuel_base=s["fuel_base"], damage_base=s["damage_base"], trace=trace)


def _env_horizon(use_preview, preview_h_s):
    """The H an environment is built at for one arm (row 117): a sighted arm's own H, a positive finite
    float; for the blinded arm, whose preview_h_s is None, the environment's default, since its four
    samples are 0 whatever H is (row 135 (5) measured the blinded arm bit for bit at every H). Anything else
    is refused (ValueError), never approximated."""
    if use_preview is True:
        if not (type(preview_h_s) is float and np.isfinite(preview_h_s) and preview_h_s > 0.0):
            raise ValueError(f"a sighted arm's H is a positive finite float, not {preview_h_s!r} (row 117)")
        return preview_h_s
    if use_preview is False:
        if preview_h_s is not None:
            raise ValueError(f"the blinded arm's H is None (row 117), not {preview_h_s!r}")
        return PREVIEW_H_S
    raise ValueError(f"use_preview is True or False, not {use_preview!r}")


def run_cycle_episode(policy, cycle, seed, weights, *, plant, dt, use_preview, preview_h_s, reward_knock,
                      inlet_kpa, record, observe):
    """One episode on `cycle` (the environment's form: arrays, t_amb one number), at the arm's own H
    (_env_horizon) and the reward's knock option, the weights pinned after the seeded reset as run_episode
    pins them, through _drive. `inlet_kpa` is the compressor's inlet (None: the engine's sea-level one).
    Every argument is passed: the arm's H and the knock option are FATAL (interface sheet rule 1.7), and the
    plant is the record (mistake 1). Returns _drive's dict."""
    env = SupervisoryTunerEnv(cycle, plant=plant, dt=dt, seed=seed, use_preview=use_preview,
                              preview_h_s=_env_horizon(use_preview, preview_h_s), reward_knock=reward_knock,
                              inlet_kpa=inlet_kpa)
    env.reset(seed=seed)
    env.w = np.asarray(weights, dtype=np.float32)   # override the fresh draw
    return _drive(env, policy, plant=plant, record=record, observe=observe)


def run_road_episode(policy, road, *, plant, use_preview, preview_h_s, reward_knock, record=None):
    """One episode of a road of the roads step -- one of decision 34's twenty or of row 96's practice roads:
    SupervisoryTunerEnv(epa_roads.env_cycle(road), plant=plant, dt=road['dt'], seed=road['episode_seed'], ...)
    at the arm's H, reset with that seed, the road's weights pinned as float32 (interface sheet 8). Refused
    (ValueError) unless the episode ran len(t) - 1 steps, 899 on decision 34's roads (the environment
    truncates at k >= n - 1; epa_roads.EPISODE_STEPS_NOTE). Returns _drive's dict."""
    import epa_roads as ER
    cycle = ER.env_cycle(road)
    out = run_cycle_episode(policy, cycle, int(road["episode_seed"]), road["weights"], plant=plant,
                            dt=float(road["dt"]), use_preview=use_preview, preview_h_s=preview_h_s,
                            reward_knock=reward_knock, inlet_kpa=None, record=record, observe=None)
    want = len(cycle["t"]) - 1
    if out["steps"] != want:
        raise ValueError(f"road {road.get('k')}: the episode ran {out['steps']} steps, and a road of "
                         f"{len(cycle['t'])} samples runs {want} (epa_roads.EPISODE_STEPS_NOTE)")
    return out


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


def scenario_line(protocol="phase-d", *, plant):
    """The scenario sentence, READ FROM THE PLANT rather than typed.

    AUDIT2.md C2-1 and H2-10. The literal this replaces was identical on the
    six-speed and on the ZF, which is why `results/phase_d_seed0.txt` cannot be
    told apart from a run on a plant that no longer exists. A sentence built
    from the declared scenario changes when the experiment changes. It was read
    from `inspect.signature(make_grade_climb)`'s defaults until 20 October 2026;
    it is the plant's scenario now (engines.Scenario), the same source the
    fingerprint's FATAL `scenario` field reads.

    For Phase D2 it is built from `random_road.RANGES` for the same reason.

    AND THE CYCLE IS READ AS WELL (JMF-2340550, 3207727, which derived the
    header from the cycle object instead). The declared values are what the
    fingerprint's FATAL `scenario` field records; the cycle is what the
    episodes drive. They must agree, and this refuses to print if they do not.
    """
    if protocol == "d2":
        (s0, s1), (g0, g1) = RR.RANGES["start_s"], RR.RANGES["grade"]
        off = [(st, g) for _, _, st, g in EPISODES_D2
               if not (s0 <= st <= s1 and g0 <= g <= g1)]
        if off:
            raise SystemExit(f"EPISODES_D2 roads outside random_road.RANGES: {off}")
        return (f"scenario: climb from {s0:.0f}-{s1:.0f} s at {100 * g0:.0f}-"
                f"{100 * g1:.0f} %, per episode, {RR.V_KMH:.0f} km/h, "
                f"{RR.T_AMB_K - 273.15:.0f} C, {DURATION:.0f} s, dt {DT}")
    sc = plant.scenario
    grade, v, t_amb = float(sc.grade), float(sc.v_kmh), float(sc.t_amb)
    c = episode_cycle(plant=plant)
    seen = (float(np.max(c["grade"])), float(np.max(c["v_mps"]) * 3.6), float(c["t_amb"]))
    if not np.allclose(seen, (grade, v, t_amb), rtol=0.0, atol=1e-6):
        raise SystemExit(f"the plant declares (grade, km/h, K) = "
                         f"{(grade, v, t_amb)} but the cycle run_episode drives "
                         f"carries {seen}. Fix locked_climb before scoring on it.")
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

    # A fingerprint written before schema 3 names no engine (20 October 2026).
    # It is refused with its own message, never compared field by field into a
    # list of "mismatches" that hides the reason.
    old = FP.schema_problem(stored)
    if old:
        if not force:
            raise SystemExit(f"\nREFUSING to evaluate {path}: {old}")
        print(old)
        return [f"!! {path}: {old} --force-plant-mismatch used; the rows below are NOT a result"]

    bad = FP.compare(stored, live)
    if not bad:
        # The dt asymmetry (trained at 0.2, scored at 1.0) is legitimate for
        # every agent trained before 27 September -- train.py passes dt 1.0
        # since then (JMF-2340550) -- so it is reported rather than refused,
        # and it is reported EVERY time: AUDIT2.md H2-2 measured the baseline's
        # "cuts" moving 37.0 -> 34.0 % between dt 0.2 and 1.0 on the step
        # alone, 94 % of it the knock term. A reader of a result file should
        # not have to know that.
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


# ==============================================================================
# DECISION 34'S PROTOCOL: the roads, the agents, the fingerprints (commit V; interface sheet 8). Every
# refusal raises SystemExit with its reason, before anything is scored; nothing here takes a force.
# ==============================================================================
def with_knock_label():
    """The with-knock reading's label, roads_ceiling.KNOCK_LABEL, imported here and nowhere at the top: a
    test pins it to the study's analysis's own label (rows 101, 113 (5))."""
    import roads_ceiling
    return roads_ceiling.KNOCK_LABEL


def _slot_summary(slot):
    """A redrawn slot as the scores' provenance carries it: what was kept, never its candidates."""
    return {k: slot.get(k) for k in ("slot", "road", "redraws", "discarded", "stopped_at", "kept", "kept_grade",
                                     "gear_sensitive", "thin_on")}


def decision34_roads(*, root):
    """(roads, provenance): decision 34's twenty as they are scored (rows 95, 140; interface sheet 8).

    The roads are fingerprint.d34_roads': R4's redraws.json read under version 6, whose roads_sha is
    roads.json's, k = 0..19 in order with EPISODES[k]'s seed and weights. Refused unless that reading is
    version 6 (the scores are computed on it only, row 95); unless each road is roads.json's road k with
    every slot that reading redrew rebuilt by epa_roads.with_grade(road, slot, kept_grade), and no other
    change, at the design's sample count; unless a REAL roads.json is the committed one
    (four_engine_roads.real_record_problem); and unless the current re-verification record
    (four_engine_roads.current_reverify, row 140) exists, reads EQUAL, names the live roads_sha and
    redraws_sha, ran on an ancestor of HEAD (epa_freeze.is_ancestor) and holds every plant's plant_sha_now
    equal to epa_freeze.plant_sha. The provenance (interface sheet 12.7) names the record, the arrays'
    sha256, the slots redrawn under version 6, the drop list and version 5's reading, reported and never
    scored. Nothing is regenerated and no stream of roads_seed is drawn."""
    import epa_freeze as EF
    import epa_roads as ER
    import four_engine_roads as FER
    from thresholds import common

    def refuse(why):
        raise SystemExit(f"\nREFUSING decision 34's roads: {why}")
    try:
        scenario, roads = FP.d34_roads(root=root)
    except (OSError, KeyError, ValueError) as exc:
        refuse(str(exc))
    if scenario["reading"] != REDRAW_READING:
        refuse(f"they are the {scenario['reading']!r} reading, and the scores are computed on the "
               f"{REDRAW_READING} set only (row 95), which R4's redraws.json gives")
    rec_path = os.path.join(root, *ER.ROADS_REL.split("/"))
    record = ER.load_record(rec_path)
    if record.get("seed_kind") == "REAL":
        problem = FER.real_record_problem(rec_path)
        if problem:
            refuse(problem)
    redraws = ER.load_record(os.path.join(root, *ER.REDRAWS_REL.split("/")))
    v6 = redraws["readings"][REDRAW_READING]
    original = record["roads"]
    if len(roads) != N_D34_ROADS or len(original) != N_D34_ROADS:
        refuse(f"{len(roads)} roads in the reading and {len(original)} in roads.json, not decision 34's "
               f"{N_D34_ROADS}")
    design = record["design"]
    samples = int(round(float(design["duration_s"]) / float(design["dt"])))
    redrawn = {}
    for slot in v6.get("slots") or []:
        redrawn.setdefault(int(slot["road"]), []).append(slot)
    for road in roads:
        k = int(road["k"])
        want = original[k]
        for slot in redrawn.get(k, []):
            want = ER.with_grade(want, slot["slot"], slot["kept_grade"])
        if road != want:
            refuse(f"road {k} of the {REDRAW_READING} reading is not roads.json's road {k} with the slots that "
                   "reading redrew (epa_roads.with_grade at each kept grade) and nothing else changed (row 95 (2))")
        if len(road["cycle"]["t"]) != samples or float(road["dt"]) != float(design["dt"]):
            refuse(f"road {k} holds {len(road['cycle']['t'])} samples at dt {road['dt']}, and the design "
                   f"{samples} at dt {design['dt']}")
    cur = FER.current_reverify(root=root)
    if cur is None:
        refuse("no current re-verification record: four_engine_roads.current_reverify finds none naming this "
               "roads.json and redraws.json, tracked and unmodified at HEAD (row 140; the plant commit P "
               "carries results/EPA_ROADS/reverify.json)")
    rel, rv = cur
    probs = []
    if rv.get("verdict") != "EQUAL":
        probs.append(f"its verdict is {rv.get('verdict')!r}, not 'EQUAL' (row 140)")
    if (rv.get("roads_sha"), rv.get("redraws_sha")) != (scenario["roads_sha"], scenario["redraws_sha"]):
        probs.append("its roads_sha and redraws_sha are not the live roads.json's and redraws.json's")
    try:
        if not EF.is_ancestor(str(rv.get("head")), "HEAD", root=root):
            probs.append(f"its head {rv.get('head')} is not an ancestor of HEAD")
    except EF.GitError as exc:
        probs.append(f"its head {rv.get('head')!r} cannot be placed in HEAD's history ({exc})")
    plants = rv.get("plants") if isinstance(rv.get("plants"), dict) else {}
    if not plants:
        probs.append("it names no plant")
    for e, p in sorted(plants.items()):
        now = EF.plant_sha(e)
        got = p.get("plant_sha_now") if isinstance(p, dict) else None
        if got != now:
            probs.append(f"{e}: its plant_sha_now {got!r} is not this tree's plant_sha {now}")
    if probs:
        refuse(f"the current re-verification record {rel}: " + "; ".join(probs))
    v5 = redraws["readings"].get(VERSION_5_READING)
    prov = {"protocol": DECISION_34, "scenario": scenario, "roads_sha": scenario["roads_sha"],
            "redraws_sha": scenario["redraws_sha"],
            "reverify": {"path": rel, "sha_text": common.sha_text(os.path.join(root, *rel.split("/")))},
            "arrays_sha256": ER.arrays_sha256(roads), "reading": REDRAW_READING,
            "redrawn_version_6": [_slot_summary(s) for s in v6.get("slots") or []],
            "dropped": list(redraws.get("dropped") or []),
            "version_5_reading": None if v5 is None else {
                "name": VERSION_5_READING, "scored": False, "gating": list(v5.get("gating") or []),
                "failing": list(v5.get("failing") or []), "slots": [_slot_summary(s) for s in v5.get("slots") or []]}}
    return roads, prov


def practice_set(record):
    """Row 96's ten practice roads, record['practice'] of the roads record, as written at the draw; nothing
    is regenerated (interface sheet 8). Refused unless there are N_PRACTICE, road i with k == i and
    episode_seed == epa_roads.PRACTICE_SEEDS[i], three float weights each, and none of their seeds one of
    EPISODES'."""
    import epa_roads as ER

    def refuse(why):
        raise SystemExit(f"\nREFUSING the practice roads: {why}")
    roads = record.get("practice") if isinstance(record, dict) else None
    if not isinstance(roads, list) or len(roads) != N_PRACTICE:
        refuse(f"the roads record holds {len(roads) if isinstance(roads, list) else roads!r} practice roads, not "
               f"row 96's {N_PRACTICE}")
    for i, road in enumerate(roads):
        if road.get("k") != i:
            refuse(f"practice road {i} has k {road.get('k')!r}")
        if road.get("episode_seed") != ER.PRACTICE_SEEDS[i]:
            refuse(f"practice road {i} has episode seed {road.get('episode_seed')!r}, not "
                   f"epa_roads.PRACTICE_SEEDS[{i}] {ER.PRACTICE_SEEDS[i]}")
        w = road.get("weights")
        if not (isinstance(w, list) and len(w) == 3 and all(type(x) is float for x in w)):
            refuse(f"practice road {i}'s weights {w!r} are not three floats")
    clash = sorted({r["episode_seed"] for r in roads} & {s for s, _ in EPISODES})
    if clash:
        refuse(f"seeds {clash} are the frozen twenty's (row 96 keeps them apart)")
    return roads


def arm_of(path, meta, roads_rec, engine):
    """(arm, H_s) of one decision-34 agent, read from its meta.json (row 117; interface sheet 8).

    Blind: use_preview False and preview_h_s None; the arm is 'blind' and H is None. Sighted: preview_h_s
    equal to four_engine_roads.horizon_s(roads_rec, engine, train_recipe.horizon_ratio), r x tau with tau
    from the roads record ({ratios, tau, H_table}, four_engine_roads.read_roads_record's), exactly; the arm
    is 'sighted_r<r>'. Refused otherwise, when the run's folder is not four_engine_roads.run_tag(seed,
    use_preview, ratio), and when its training share was not drawn from a REAL roads record
    (train_recipe.scored_share.seed_kind)."""
    import four_engine_roads as FER

    def refuse(why):
        raise SystemExit(f"\nREFUSING {path}: {why}")
    recipe = meta.get("train_recipe") if isinstance(meta.get("train_recipe"), dict) else {}
    share = recipe.get("scored_share") if isinstance(recipe.get("scored_share"), dict) else {}
    if share.get("seed_kind") != "REAL":
        refuse(f"its training share's roads record is {share.get('seed_kind')!r}, not 'REAL': an agent trained "
               "on a SYNTHETIC share is a test, never scored (train.py's refusal)")
    seed = meta.get("seed")
    if type(seed) is not int:
        refuse(f"its meta.json records seed {seed!r}, not an int")
    use_preview, h = meta.get("use_preview"), meta.get("preview_h_s")
    if use_preview is False:
        if h is not None:
            refuse(f"a blinded agent's preview_h_s is None (row 117); this one records {h!r}")
        arm, ratio = "blind", None
    elif use_preview is True:
        ratio = recipe.get("horizon_ratio")
        if ratio is None:
            refuse("a sighted agent of decision 34 trains at H = r x tau (train.py --horizon-ratio), and this "
                   "one records no horizon_ratio")
        try:
            want = FER.horizon_s(roads_rec, engine, ratio)
        except FER.Refused as exc:
            refuse(str(exc))
        if h != want:
            refuse(f"its preview_h_s {h!r} is not r x tau = {want!r} s from the roads record (r = {float(ratio):g})")
        arm = f"sighted_r{float(ratio):g}"
    else:
        refuse(f"its meta.json records use_preview {use_preview!r}, not a bool")
    tag = FER.run_tag(seed, use_preview=use_preview, ratio=ratio)
    run = os.path.basename(os.path.normpath(path))
    if run != tag:
        refuse(f"its folder is {run!r}, and its meta.json makes it {tag!r} (four_engine_roads.run_tag)")
    return arm, h


def _read_json(path):
    try:
        with open(path, encoding="utf-8") as fh:
            got = json.load(fh)
    except (OSError, ValueError):
        return None
    return got if isinstance(got, dict) else None


def read_agents(paths, *, roads_rec, engine):
    """[{path, meta, config, arm, H_s, r, seed}] of decision-34 agents: meta.json of fingerprint schema 4
    (refused otherwise, with fingerprint.schema_problem's reason), config.json, and the arm and H through
    arm_of. Refused: a folder without meta.json or config.json, and one arm and seed held twice."""
    out, seen = [], {}
    for path in paths:
        run = path.rstrip("/\\")
        meta = FP.read(os.path.join(run, "meta.json"))
        if meta is None:
            raise SystemExit(f"\nREFUSING {run}: it has no meta.json, so nothing records which plant it trained on")
        old = FP.schema_problem(meta)
        if old:
            raise SystemExit(f"\nREFUSING {run}: {old}")
        config = _read_json(os.path.join(run, "config.json"))
        if config is None:
            raise SystemExit(f"\nREFUSING {run}: it has no config.json, so its training environment is unknown "
                             "(row 143 (5))")
        arm, h = arm_of(run, meta, roads_rec, engine)
        r = None if h is None else float(meta["train_recipe"]["horizon_ratio"])
        key = (arm, meta["seed"])
        if key in seen:
            raise SystemExit(f"\nREFUSING {run}: {seen[key]} is the same arm and seed ({arm}, seed {meta['seed']})")
        seen[key] = run
        out.append(dict(path=run, meta=meta, config=config, arm=arm, H_s=h, r=r, seed=meta["seed"]))
    return out


def env_of(meta, config):
    """ENV_KEYS' values of one agent, {'config.json versions.torch': ..., ...}; a missing key reads None."""
    out = {}
    for source, keys in ENV_KEYS:
        v = config if source == "config.json" else meta
        for k in keys:
            v = v.get(k) if isinstance(v, dict) else None
        out[f"{source} {'.'.join(keys)}"] = v
    return out


def environment_problems(agents):
    """[str]: why the agents (path, meta, config) of one engine did not train on one environment (row 143
    (5); CLAUDE.md rules 3 and 5): every ENV_KEYS value equal across them, and every one present but
    ENV_UNRECORDED's. [] when they did. The preregistration declares no environment ablation, so any
    difference is refused on decision 34's protocol and its practice route."""
    out, first = [], None
    for path, meta, config in agents:
        if not isinstance(config, dict):
            out.append(f"{path}: no config.json, so its training environment is unknown")
            continue
        env = env_of(meta, config)
        out += [f"{path}: its {k} is not recorded" for k, v in env.items() if v is None and k not in ENV_UNRECORDED]
        if first is None:
            first = (path, env)
            continue
        p0, e0 = first
        out += [f"{k}: {path} {env[k]!r}, {p0} {e0[k]!r}" for k in e0 if env[k] != e0[k]]
    return out


def pairing_problems(agents):
    """[str]: why the agents (read_agents') are not row 117's pairs. Every seed holds every arm the set
    scores, a blinded one among them and at least one sighted, and each sighted agent pairs with its seed's
    blinded agent (fingerprint.pair_problems: every FATAL field but preview_h_s agrees, H a positive float
    on the first and None on the second). An unpaired seed is refused, never scored alone."""
    arms = sorted({x["arm"] for x in agents})
    out = []
    if "blind" not in arms:
        out.append("no blinded agent: d is the sighted cut minus the blinded cut of one seed (row 117)")
    if not [a for a in arms if a != "blind"]:
        out.append("no sighted agent")
    if out:
        return out
    by_seed = {}
    for x in agents:
        by_seed.setdefault(x["seed"], {})[x["arm"]] = x
    for seed, got in sorted(by_seed.items()):
        missing = [a for a in arms if a not in got]
        if missing:
            out.append(f"seed {seed} is unpaired: it holds no {', '.join(missing)}")
            continue
        for a in arms:
            if a != "blind":
                out += [f"seed {seed}, {a} with blind: {k} {x!r} / {y!r} (row 117's pairing rule)"
                        for k, x, y in FP.pair_problems(got[a]["meta"], got["blind"]["meta"])]
    return out


def committed_train_backend(engine, *, root):
    """`engine`'s train_backend as the committed backend record names it: results/EPA_BACKEND.json's
    engines[engine].backend, read through engines.committed_record (Tb's record, ORDER step 19; 'cycle'
    beside n null for the B58). A REAL scoring without the record, a record not committed at HEAD, and an
    engine it drops or names no backend for are refused (interface sheet 8, "train_backend")."""
    try:
        rec = engines.committed_record(root, engines.BACKEND_REL)
    except ValueError as exc:
        raise SystemExit(f"\nREFUSING: {exc}")
    if rec is None:
        raise SystemExit(f"\nREFUSING: no {engines.BACKEND_REL}: the train_backend every agent is checked against "
                         "is the committed backend record's (Tb, ORDER step 19), and a scoring without it is refused")
    if rec.get("schema") != engines.BACKEND_SCHEMA:
        raise SystemExit(f"\nREFUSING: {engines.BACKEND_REL} is schema {rec.get('schema')!r}, not "
                         f"{engines.BACKEND_SCHEMA!r}")
    entry = (rec.get("engines") or {}).get(engine)
    if not isinstance(entry, dict) or entry.get("drop") is not False or entry.get("backend") is None:
        raise SystemExit(f"\nREFUSING: {engines.BACKEND_REL} keeps no backend for {engine}: {entry!r}")
    return entry["backend"]


def backend_problems(agents, train_backend):
    """[str]: the agents whose meta.json train_backend is not the backend record's (interface sheet 8)."""
    return [f"{x['path']}: its train_backend {x['meta'].get('train_backend')!r} is not the backend record's "
            f"{train_backend!r}" for x in agents if x["meta"].get("train_backend") != train_backend]


def live_decision34(plant, *, preview_h_s, reward_knock, train_backend):
    """The decision-34 fingerprint an agent at H = preview_h_s is checked against (interface sheet 8):
    fingerprint.plant_fingerprint('d34', ...), its scenario and episodes_sha read from the roads records,
    its eval_dt and eval_duration the design's, the cycle model scoring. Every FATAL input is passed; the
    blinded arm's block is fingerprint.for_arm(live, sighted=False)."""
    return FP.plant_fingerprint(DECISION_34, plant=plant, train_backend=train_backend,
                                score_backend=FP.BACKEND_CYCLE, preview_h_s=preview_h_s, reward_knock=reward_knock)


def _fmt(v):
    return json.dumps(v, sort_keys=True) if isinstance(v, (dict, list)) else str(v)


def check_transfer(path, stored, live, *, route):
    """THE DECLARED TRANSFER ROUTE (row 147 (11)): scoring an agent off the roads it trained for.

    `stored` is the agent's meta.json, `live` the block of what it is scored on, built at the agent's own H
    and the reward's knock option. Every FATAL field but TRANSFER_EXEMPT (scenario and episodes_sha) must
    be the live one, or the transfer is refused with each field named; a meta.json that is missing or of
    another schema is refused too. There is no force. Prints, and returns, the declaration: the route, and
    both exempt fields as trained and as scored."""
    if stored is None:
        raise SystemExit(f"\nREFUSING the declared transfer {route} of {path}: it has no meta.json, so nothing "
                         "records which plant it trained on")
    old = FP.schema_problem(stored)
    if old:
        raise SystemExit(f"\nREFUSING the declared transfer {route} of {path}: {old}")
    bad = [(k, a, b) for k, a, b in FP.compare(stored, live) if k not in TRANSFER_EXEMPT]
    if bad:
        raise SystemExit(f"\nREFUSING the declared transfer {route} of {path}: a transfer lets only "
                         f"{' and '.join(TRANSFER_EXEMPT)} differ (row 147 (11)), and "
                         + "; ".join(f"{k} is {a!r} in its meta.json and {b!r} live" for k, a, b in bad))
    lines = [f"DECLARED TRANSFER {route}: {path}: every FATAL field but {' and '.join(TRANSFER_EXEMPT)} is the "
             "live one (row 147 (11))"]
    lines += [f"  {k:<14} trained {_fmt(stored.get(k))}   scored {_fmt(live.get(k))}" for k in TRANSFER_EXEMPT]
    for line in lines:
        print(line)
    return lines


def average_lines(path, meta):
    """(manifest, lines): decision 29's checkpoint average of one run, every check made and nothing loaded
    (row 118; interface sheet 8). Refused unless meta.json's train_recipe.checkpoint_average is
    training_recipe.DECISION_29_WINDOW, the manifest exists and reads (training_recipe.read_manifest checks
    each snapshot's sha256 and the rule's steps), its window is that window, and its total_steps is
    final.zip's own num_timesteps (fingerprint.model_budget). The manifest gains its file's sha256."""
    import hashlib
    import training_recipe as TR
    run = path.rstrip("/\\")
    recipe = (meta or {}).get("train_recipe")
    n = recipe.get("checkpoint_average") if isinstance(recipe, dict) else None
    if n != TR.DECISION_29_WINDOW:
        raise SystemExit(f"\nREFUSING {run}: its meta.json records checkpoint_average {n!r}, not decision 29's "
                         f"{TR.DECISION_29_WINDOW}: decision 34 scores the checkpoint average (row 118)")
    man_path = os.path.join(run, TR.MANIFEST)
    if not os.path.isfile(man_path):
        raise SystemExit(f"\nREFUSING {run}: no {TR.MANIFEST}: its checkpoint average was never written "
                         "(train.py writes it when the run ends)")
    try:
        man = TR.read_manifest(run)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"\nREFUSING {run}: its checkpoint average does not read: {exc}")
    if man.get("window") != TR.DECISION_29_WINDOW:
        raise SystemExit(f"\nREFUSING {run}: its manifest's window is {man.get('window')!r}, not "
                         f"{TR.DECISION_29_WINDOW}")
    budget = FP.model_budget(os.path.join(run, "final.zip"))
    if budget is None or budget["num_timesteps"] != man.get("total_steps"):
        raise SystemExit(f"\nREFUSING {run}: its manifest's total_steps {man.get('total_steps')!r} is not "
                         f"final.zip's num_timesteps {None if budget is None else budget['num_timesteps']!r}")
    with open(man_path, "rb") as fh:
        sha = hashlib.sha256(fh.read()).hexdigest()
    lines = [f"model {run}: the checkpoint average, {man['rule']}; manifest sha256 {sha}",
             f"  final.zip: {FP.format_budget(budget)}"]
    lines += [f"  snapshot at step {s['step']}: sha256 {s['sha256']}" for s in man["snapshots"]]
    return dict(man, sha256=sha), lines


def load_agent(path, meta, *, device):
    """(policy, lines): the agent as decision 34 and its practice route score it, decision 29's
    checkpoint average, training_recipe.AveragedPolicy.load(run, device=device), after average_lines'
    checks. Wrap it with agent_policy, as one model is wrapped."""
    import training_recipe as TR
    _, lines = average_lines(path, meta)
    return TR.AveragedPolicy.load(path.rstrip("/\\"), device=device), lines


# ------------------------------------------------------------------------------ scoring
_TASK = {"key": None, "policy": None}


def _one_thread():
    """torch on one thread, as every gate runs (OMP_NUM_THREADS=1), so that a worker and this process
    give the same actions. Nothing when torch is not installed (hand-written policies only)."""
    try:
        import torch
    except ImportError:
        return
    torch.set_num_threads(1)


def _worker_init():
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    _one_thread()


def _policy_of(kind, ref):
    """The policy of a task, kept while the next task is the same policy's (a task list runs each policy's
    roads one after another): a hand-written policy by its name, or an agent's checkpoint average."""
    if _TASK["key"] != (kind, ref):
        _TASK.update(key=None, policy=None)
        if kind == "hand":
            pol = getattr(C, dict(HAND_POLICIES)[ref])
        else:
            avg, _ = load_agent(ref, FP.read(os.path.join(ref, "meta.json")), device="cpu")
            pol = agent_policy(avg)
        _TASK.update(key=(kind, ref), policy=pol)
    return _TASK["policy"]


def _score_task(task):
    """One policy on one road, in this process or in a spawn worker: run_road_episode's dict, its per-step
    trace dropped unless the records are kept. A refusal becomes a RuntimeError, which a pool carries back."""
    engine, kind, ref, use_preview, h_s, reward_knock, road, keep = task
    try:
        out = run_road_episode(_policy_of(kind, ref), road, plant=engines.get(engine), use_preview=use_preview,
                               preview_h_s=h_s, reward_knock=reward_knock, record=None)
    except SystemExit as exc:
        raise RuntimeError(f"{ref} on road {road.get('k')}: {exc}") from None
    if not keep:
        out.pop("trace")
    return out


def score_set(engine, models, roads, *, plant, reward_knock, train_backend, jobs, keep_records):
    """Every policy on every road (interface sheet 8): the baseline ECU, reactive and current-grade once per
    road, at the default H as main() runs them, then each agent of `models` (read_agents' dicts) at its own
    H, every episode with the reward's knock option. In this process at jobs 1, else in a spawn pool of
    `jobs` workers, each building its plant (engines.get) and loading each agent itself; every episode is
    deterministic and the results come back in task order, so the numbers are the same at any jobs. With
    keep_records the per-step trace stays in each row. Returns {'hand': {name: [row per road]}, 'agents':
    {(arm, seed): [row per road]}}. Refused (ValueError): another backend than the cycle model (row 136), a
    plant that is not engines.get(engine) itself, as every worker builds it (a variant or a candidate)."""
    if train_backend != FP.BACKEND_CYCLE:
        raise ValueError(f"train_backend {train_backend!r}: only {FP.BACKEND_CYCLE!r} exists (row 136)")
    if engines.is_candidate(plant) or plant != engines.get(engine):
        raise ValueError(f"the plant passed is not {engine}'s as engines.get({engine!r}) builds it, which every "
                         "worker scores on")
    import evaluate as _self            # the tasks are pickled by this module's name, as a script too
    n = len(roads)
    tasks, keys = [], []
    for name, _ in HAND_POLICIES:
        tasks += [(engine, "hand", name, True, PREVIEW_H_S, reward_knock, road, keep_records) for road in roads]
        keys.append(("hand", name))
    for x in models:
        tasks += [(engine, "agent", x["path"], x["H_s"] is not None, x["H_s"], reward_knock, road, keep_records)
                  for road in roads]
        keys.append(("agents", (x["arm"], x["seed"])))
    if jobs <= 1:
        if models:
            _one_thread()
        res = [_self._score_task(t) for t in tasks]
    else:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(min(int(jobs), len(tasks)), initializer=_self._worker_init) as pool:
            res = pool.map(_self._score_task, tasks, chunksize=max(1, n))
    out = {"hand": {}, "agents": {}}
    for i, (group, key) in enumerate(keys):
        out[group][key] = res[i * n:(i + 1) * n]
    return out


def median_cut(D, D_base):
    """evaluate.py's form of a cut, the one main() prints for each policy: 100 x (1 - median D / median
    D_base) over the roads or episodes (row 113 (1))."""
    return float(100.0 * (1.0 - np.median(D) / np.median(D_base)))


def delivery_block(rows):
    """Torque delivery and fuel, road by road, for every policy scored (row 147 (5); interface sheet 17.8):
    each one's fuel (the baseline ECU's among them), its demand steps, the steps of them short of the
    tracking tolerance and their share (None on a road with no demand step)."""
    def per(rs):
        return {"fuel": [float(x["fuel"]) for x in rs], "demand_steps": [int(x["demand_steps"]) for x in rs],
                "short_steps": [int(x["short_steps"]) for x in rs],
                "short_share": [(int(x["short_steps"]) / int(x["demand_steps"]) if x["demand_steps"] else None)
                                for x in rs]}
    arms = {}
    for (arm, seed), rs in sorted(rows["agents"].items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
        arms.setdefault(arm, {})[str(int(seed))] = per(rs)
    return {"rule": {"demand_step": f"torque_req > {DEMAND_NM:g} Nm (the reward's t_ref floor; logged_check.DEMAND_NM)",
                     "short_step": f"torque < (1 - {TRACK_TOL:g}) x torque_req (engine_env.TRACK_TOL)",
                     "fuel": "g over the road (the episode's own count)"},
            "hand": {name: per(rs) for name, rs in rows["hand"].items()}, "arms": arms}


def _arms_of(rows, ratios):
    """The scores' arms: {'blind': {'seeds': ...}, 'sighted_r<r>': ...}, each seed's D and D_base per reading,
    D_base the baseline ECU's on the same road."""
    base = rows["hand"][BASELINE]
    arms = {"blind": {"seeds": {}}}
    for r in ratios:
        arms[f"sighted_r{r}"] = {"seeds": {}}
    for (arm, seed), rs in sorted(rows["agents"].items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
        if arm not in arms:
            raise ValueError(f"the arm {arm!r} is not one of {sorted(arms)} (the ratios {ratios})")
        if len(rs) != len(base):
            raise ValueError(f"{arm} seed {seed}: {len(rs)} roads, the baseline ECU {len(base)}")
        arms[arm]["seeds"][str(int(seed))] = {
            reading: {"D": [float(x[key]) for x in rs], "D_base": [float(b[key]) for b in base]}
            for reading, key in READING_KEYS.items()}
    return arms


def scores_document(engine, rows, *, ratios, provenance):
    """A four-engine-scores/1 document of one engine (interface sheet 12.7): arms blind and sighted_r<r> for
    each r of `ratios` (strings, '0.5' and '1.5'), seeds as decimal strings, D and D_base per road and
    reading, variant null (the declared sensitivity route is not built, row 147 (10)), and the provenance
    with delivery_block's figures beside it (row 147 (5)), which the analysis copies untouched."""
    base = rows["hand"][BASELINE]
    return {"schema": SCORES_SCHEMA, "ratios": list(ratios), "n_roads": len(base), "variant": None,
            "provenance": dict(provenance, delivery=delivery_block(rows)),
            "engines": {engine: {"arms": _arms_of(rows, ratios)}}}


def practice_document(engine, rows, *, roads, ratios, provenance):
    """A four-engine-practice/1 document (interface sheet 12.7): the practice roads by k, seed and weights,
    and the arms in the scores' layout, on N_PRACTICE roads; labelled PRACTICE_HEADER, never the test."""
    return {"schema": PRACTICE_SCHEMA, "label": PRACTICE_HEADER, "engine": engine, "ratios": list(ratios),
            "n_roads": len(roads),
            "roads": [{"k": r["k"], "episode_seed": r["episode_seed"], "weights": r["weights"]} for r in roads],
            "provenance": dict(provenance, delivery=delivery_block(rows)), "arms": _arms_of(rows, ratios)}


def score_practice(engine, models, record, *, plant, reward_knock, train_backend, jobs, provenance):
    """Decision 29's pilot on row 96's practice roads (rows 103 (4), 112; interface sheet 8): practice_set
    of the roads record, every agent and the hand-written policies by score_set, as a practice document."""
    roads = practice_set(record)
    rows = score_set(engine, models, roads, plant=plant, reward_knock=reward_knock, train_backend=train_backend,
                     jobs=jobs, keep_records=False)
    ratios = sorted({f"{x['r']:g}" for x in models if x["r"] is not None}, key=float)
    return practice_document(engine, rows, roads=roads, ratios=ratios, provenance=provenance), rows


def pilot_spread(practice_doc, *, engine, ratio):
    """s_p (row 103 (4); row 112): the spread of the paired d on the practice roads at r = `ratio`, in the
    no-knock reading and evaluate.py's form, d = cut(sighted_r, seed) - cut(blind, seed), s_p their
    standard deviation with ddof = 1. Returns {engine, ratio, reading, seeds, d, s_p, pairs}. Refused
    (ValueError): another schema or engine, an unpaired seed, fewer than two pairs."""
    if practice_doc.get("schema") != PRACTICE_SCHEMA or practice_doc.get("engine") != engine:
        raise ValueError(f"not a {PRACTICE_SCHEMA} document of {engine}")
    r = f"{float(ratio):g}"
    sig = practice_doc["arms"][f"sighted_r{r}"]["seeds"]
    blind = practice_doc["arms"]["blind"]["seeds"]
    if set(sig) != set(blind):
        raise ValueError(f"unpaired seeds: sighted_r{r} {sorted(sig, key=int)}, blind {sorted(blind, key=int)}")
    seeds = sorted(sig, key=int)
    if len(seeds) < 2:
        raise ValueError(f"{len(seeds)} pair(s): a spread needs at least 2")
    d = [median_cut(sig[s]["no_knock"]["D"], sig[s]["no_knock"]["D_base"])
         - median_cut(blind[s]["no_knock"]["D"], blind[s]["no_knock"]["D_base"]) for s in seeds]
    return {"engine": engine, "ratio": r, "reading": "no_knock", "seeds": [int(s) for s in seeds], "d": d,
            "s_p": float(np.std(d, ddof=1)), "pairs": len(d)}


def write_once_json(path, obj):
    """Write `obj` as JSON once: refused (SystemExit) if `path` exists. LF, no NaN. Returns its sha256."""
    import hashlib
    text = json.dumps(obj, indent=1, allow_nan=False) + "\n"
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    try:
        with open(path, "x", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
    except FileExistsError:
        raise SystemExit(f"\n{path} exists: a scores document is written once, never overwritten") from None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def write_records(records_dir, engine, rows, *, dt):
    """Per-step records (interface sheet 12.7): <records_dir>/<engine>/baseline.npz and <arm>_seed<S>.npz,
    float64 t_turb, t_oil and ki of shape (roads, steps) in road k order, and dt. Refused (SystemExit) if a
    file exists. Returns {path relative to records_dir: sha256}."""
    import hashlib
    folder = os.path.join(records_dir, engine)
    os.makedirs(folder, exist_ok=True)
    files = {}

    def save(name, rs):
        path = os.path.join(folder, name + ".npz")
        if os.path.exists(path):
            raise SystemExit(f"\n{path} exists: a record is written once")
        arrays = {k: np.asarray([r["trace"][k] for r in rs], dtype=np.float64) for k in ("t_turb", "t_oil", "ki")}
        np.savez(path, dt=np.float64(dt), **arrays)
        with open(path, "rb") as fh:
            files[f"{engine}/{name}.npz"] = hashlib.sha256(fh.read()).hexdigest()
    save("baseline", rows["hand"][BASELINE])
    for (arm, seed), rs in sorted(rows["agents"].items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
        save(f"{arm}_seed{int(seed)}", rs)
    return files


def rescore_from_records(records, *, cal):
    """{'no_knock': [D per road], 'with_knock': [D per road]} from a per-step record (write_records'
    arrays): a sequential Python sum of engine_env.damage_rate(...) * dt, the one damage definition, at
    the damage record `cal`."""
    tt, to, ki = (np.asarray(records[k], dtype=np.float64) for k in ("t_turb", "t_oil", "ki"))
    dt = float(records["dt"])
    out = {"no_knock": [], "with_knock": []}
    for i in range(tt.shape[0]):
        nk = wk = 0.0
        for j in range(tt.shape[1]):
            nk += damage_rate(tt[i, j], to[i, j], cal=cal) * dt
            wk += damage_rate(tt[i, j], to[i, j], ki[i, j], cal=cal) * dt
        out["no_knock"].append(nk)
        out["with_knock"].append(wk)
    return out


def merge_scores(paths):
    """One four-engine-scores/1 document from several, one engine each (interface sheet 8; row 143 (1),
    (4)). Refused (SystemExit): another schema, n_roads not N_D34_ROADS, mixed ratios or variants, an
    engine in two documents, and documents whose versions, platform or device differ (one engine's
    documents never differ; two engines' may only once cross-machine stability is measured, row 143 (4),
    which no record holds). The merged provenance names every source by path and sha256."""
    import hashlib
    docs = []
    for path in paths:
        with open(path, "rb") as fh:
            raw = fh.read()
        doc = json.loads(raw)
        if doc.get("schema") != SCORES_SCHEMA:
            raise SystemExit(f"\nREFUSING {path}: schema {doc.get('schema')!r}, not {SCORES_SCHEMA!r}")
        if doc.get("n_roads") != N_D34_ROADS:
            raise SystemExit(f"\nREFUSING {path}: n_roads {doc.get('n_roads')!r}, not {N_D34_ROADS}")
        docs.append((path, hashlib.sha256(raw).hexdigest(), doc))
    if len({json.dumps(d["ratios"]) for _, _, d in docs}) > 1:
        raise SystemExit("\nREFUSING to merge: the documents hold different ratios")
    if len({json.dumps(d.get("variant")) for _, _, d in docs}) > 1:
        raise SystemExit("\nREFUSING to merge: the documents hold different variants")
    where, merged = {}, {}
    for path, _, d in docs:
        for e, entry in d["engines"].items():
            if e in where:
                raise SystemExit(f"\nREFUSING to merge: {e} is in {where[e]} and in {path}")
            where[e] = path
            merged[e] = entry
    envs = {json.dumps([(d.get("provenance") or {}).get(k) for k in ("versions", "platform", "device")],
                       sort_keys=True) for _, _, d in docs}
    if len(envs) > 1:
        raise SystemExit("\nREFUSING to merge: the documents' versions, platform or device differ, and no record "
                         "measures cross-machine stability (row 143 (4))")
    first = docs[0][2]
    return {"schema": SCORES_SCHEMA, "ratios": first["ratios"], "n_roads": first["n_roads"],
            "variant": first.get("variant"),
            "provenance": {"copied_from": [{"path": p, "sha256": s, "engines": sorted(d["engines"])}
                                           for p, s, d in docs],
                           "per_document": [d.get("provenance") for _, _, d in docs]},
            "engines": merged}


def agents_provenance(agents, manifests):
    """{arm: {seed: {path, H_s, r, manifest_sha256}}} (interface sheet 12.7)."""
    out = {}
    for x in agents:
        out.setdefault(x["arm"], {})[str(int(x["seed"]))] = {
            "path": x["path"].replace(os.sep, "/"), "H_s": x["H_s"], "r": x["r"],
            "manifest_sha256": manifests[x["path"]]["sha256"]}
    return out


def d34_report(engine, rows, *, header, reading, ratios, lines):
    """The text report of a decision-34 or practice scoring: the provenance lines, each policy's medians,
    each agent's cut in evaluate.py's form in both readings, and each seed's sighted minus blinded cut per
    ratio. Never written as results/*_seed*.txt (the app reads only those)."""
    base = rows["hand"][BASELINE]
    say = [f"{header} -- {engine}, {len(base)} roads ({reading}), each with its own seed and weights",
           f"reading: no knock (damage_thermal) is primary; with knock (damage) is beside it, "
           f"\"{with_knock_label()}\", and decides nothing", ""]
    say += lines
    say.append("")
    say.append(f"{'policy':<30}{'D no knock':>12}{'D knock':>10}{'fuel med':>10}{'short med':>11}{'peak C':>9}")
    say.append("-" * 82)

    def med(rs, k):
        return float(np.median([float(x[k]) for x in rs]))

    def share(rs):
        v = [x["short_steps"] / x["demand_steps"] for x in rs if x["demand_steps"]]
        return float(np.median(v)) if v else float("nan")
    named = [(name, rs) for name, rs in rows["hand"].items()]
    named += [(f"{arm} seed {seed}", rs) for (arm, seed), rs in
              sorted(rows["agents"].items(), key=lambda kv: (kv[0][0], int(kv[0][1])))]
    for name, rs in named:
        say.append(f"{name:<30}{med(rs, 'damage_thermal'):>12.1f}{med(rs, 'damage'):>10.1f}{med(rs, 'fuel'):>10.0f}"
                   f"{share(rs):>11.4f}{max(float(x['peak_turb']) for x in rs):>9.0f}")
    say.append("-" * 82)
    say.append("  cut against the baseline ECU, 100 x (1 - median D / median D_base): no knock [with knock]")
    cut = {}
    for name, rs in named:
        if name == BASELINE:
            continue
        c = {reading_: median_cut([x[key] for x in rs], [b[key] for b in base])
             for reading_, key in READING_KEYS.items()}
        cut[name] = c
        say.append(f"    {name:<28} {c['no_knock']:+8.2f} [{c['with_knock']:+8.2f}]")
    for r in ratios:
        say.append(f"  d at r = {r}, sighted_r{r} minus blind, per seed: no knock [with knock]")
        for (arm, seed), _ in sorted(rows["agents"].items(), key=lambda kv: (kv[0][0], int(kv[0][1]))):
            if arm != f"sighted_r{r}" or f"blind seed {seed}" not in cut:
                continue
            s, b = cut[f"{arm} seed {seed}"], cut[f"blind seed {seed}"]
            say.append(f"    seed {seed:<6} {s['no_knock'] - b['no_knock']:+8.2f} "
                       f"[{s['with_knock'] - b['with_knock']:+8.2f}]")
    return say


def main():
    ap = argparse.ArgumentParser(description="Phase D evaluation protocol.")
    ap.add_argument("models", nargs="*",
                    help="runs/<tag> directories; 'blind' in the name means "
                         "the preview channel was zeroed during training")
    # engines.trainable(), not known() (22 October 2026, decision 47): the B58 and the EPA
    # engines the committed records keep (rows 107 (5) and 139); any other is not scored
    ap.add_argument("--engine", required=True, choices=engines.trainable(),
                    help="the plant the episodes run on (engines.get), one that may be "
                         "scored (engines.trainable(), decision 47). REQUIRED: "
                         "there is no default engine (CLAUDE.md mistake 1)")
    ap.add_argument("--out", default=None,
                    help="also write the whole report, fingerprint block "
                         "included, to this file")
    ap.add_argument("--force-plant-mismatch", action="store_true",
                    help="evaluate a model whose meta.json disagrees with this "
                         "tree, or has none. The mismatch is stamped into the "
                         "output; it is never silent.")
    ap.add_argument("--protocol", choices=sorted(PROTOCOLS) + [DECISION_34], default="phase-d",
                    help="which frozen episode set: 'phase-d' (the fixed climb, "
                         "the default and unchanged), 'd2' (the randomised "
                         "climb) or 'd34' (decision 34's twenty roads, ORDER "
                         "step 16; see the docstring). Each has its own "
                         "fingerprint, so an agent trained under one is refused "
                         "by the other.")
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
    ap.add_argument("--reward-knock", choices=("in", "out"), default=None,
                    help="the reward the agents trained with (row 113 (5)): 'in', "
                         "X1's, the knock term in r_life, or 'out'. A FATAL "
                         "fingerprint field (row 117), so an agent trained the "
                         "other way is refused. Absent: 'in' on phase-d and d2; "
                         "required on d34")
    # decision 34's protocol only (ORDER step 16; interface sheet 8), each refused on phase-d and d2
    ap.add_argument("--practice", action="store_true",
                    help="with --protocol d34: score row 96's ten practice roads (decision 29's pilot), "
                         "not the test set")
    ap.add_argument("--scores-out", default=None, metavar="PATH",
                    help="with --protocol d34: the four-engine-scores/1 (or, with --practice, "
                         "four-engine-practice/1) document, written once, outside the repository")
    ap.add_argument("--records-out", default=None, metavar="DIR",
                    help="with --protocol d34: a new folder outside the repository for the baseline ECU's "
                         "and every agent's per-step t_turb, t_oil and ki")
    ap.add_argument("--jobs", type=int, default=None, metavar="N",
                    help="with --protocol d34: spawn workers (default 1); the scores are the same at any N")
    a = ap.parse_args()
    if a.protocol == DECISION_34:
        return main_decision34(a)
    for flag, given in (("--practice", a.practice), ("--scores-out", a.scores_out is not None),
                        ("--records-out", a.records_out is not None), ("--jobs", a.jobs is not None)):
        if given:
            raise SystemExit(f"\nREFUSING {flag} on --protocol {a.protocol}: it belongs to decision 34's "
                             f"protocol (--protocol {DECISION_34}); the {a.protocol} route is unchanged")
    knock = (a.reward_knock or "in") == "in"     # REWARD_KNOCK_DEFAULT when absent (row 118)
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

    plant = engines.get(a.engine)
    # backend: run_episode's SupervisoryTunerEnv has no engine_model, so every
    # episode below runs the 0-D cycle model (fingerprint.backend_of), at the
    # default H with the reward --reward-knock names, X1's when absent (fingerprint
    # schema 4); a blinded model is compared with the blinded arm's block, whose H
    # is None (FP.for_arm)
    live = FP.plant_fingerprint(plant=plant, protocol=a.protocol, train_backend=FP.BACKEND_CYCLE,
                                score_backend=FP.BACKEND_CYCLE, preview_h_s=PREVIEW_H_S,
                                reward_knock=knock, eval_dt=DT, eval_duration=DURATION)

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
        blind = "blind" in path
        provenance += check_model_fingerprint(path, FP.for_arm(live, sighted=not blind), a.force_plant_mismatch)
        # HOW LONG THIS AGENT WAS TRAINED, from the zip. The fingerprint cannot
        # tell a C4 agent from a Phase D2 one -- same plant, scenario and
        # episodes -- and meta.json's steps_requested is advisory and is not
        # rewritten by a resume. The zip's own counters are written by the
        # training loop, and its hash names exactly which artefact was scored.
        # `analyse_c4.py` reads this line back.
        mdir = path.rstrip("/\\")
        provenance.append(f"model {mdir}: "
                          f"{FP.format_budget(FP.model_budget(mdir + '/final.zip'))}")
        model = SAC.load(path.rstrip("/\\") + "/final")
        policies.append((("agent (blind)" if blind else "agent") + " " + path,
                         agent_policy(model), not blind))

    frozen = "18 Sep 2026" if a.protocol == "phase-d" else "22 Sep 2026"
    if a.label:
        say(f"{a.label} -- scored on the '{a.protocol}' protocol, "
            f"{len(episodes)} FIXED EPISODES, frozen {frozen}")
    else:
        say(f"{header} -- {len(episodes)} FIXED EPISODES, frozen {frozen}")
    say(scenario_line(a.protocol, plant=plant))
    say(f"trigger:  {plant.engine.damage.turb_knee_k - 273.15:.0f} C")
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
            rows = [run_episode(pol, s, w, prev, plant=plant, reward_knock=knock) for s, w in episodes]
        else:
            rows = [run_episode(pol, s, w, prev, road=(st, g), plant=plant, reward_knock=knock)
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

    # DAMAGE TWO WAYS (JMF-2340550, 28 September). Its OWN block, indented, and
    # worded without "cuts median damage": analyse_phase_d.parse reads rows that
    # START with a policy name and takes their last five fields, and
    # plot_agent_pairs.CUT_ROW reads "cuts median damage" lines -- a sixth
    # table column or a reused phrase would feed both a wrong number silently.
    say("")
    say("  WITHOUT THE KNOCK TERM (turbine + oil only; the knock model is untested)")
    base_t = np.median([r["damage_thermal"] for r in out["baseline ECU"]])
    for name in out:
        tm = np.median([r["damage_thermal"] for r in out[name]])
        say(f"    {name:<26} thermal med {tm:8.1f}   thermal cut {100*(1-tm/base_t):5.1f} %")

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


def recipe_checks(agents, manifests):
    """Decision 29's recipe as each agent's own files record it (ORDER step 21's checks: the learning rate
    reaches 0, the average is taken): config.json's recipe.learning_rate_at_end and the manifest scored.
    Reported, never refused here: a broken recipe is a coding defect, handled by row 112."""
    out = {}
    for x in agents:
        lr = (x["config"].get("recipe") or {}).get("learning_rate_at_end")
        man = manifests[x["path"]]
        out[x["path"].replace(os.sep, "/")] = {"learning_rate_at_end": lr, "learning_rate_reaches_0": lr == 0.0,
                                               "average_taken": len(man["snapshots"]), "manifest_sha256": man["sha256"]}
    return out


def records_index_path(scores_out):
    """<scores>.records.json, beside the scores document (interface sheet 12.7)."""
    return os.path.splitext(scores_out)[0] + ".records.json"


def main_decision34(a):
    """--protocol d34, and --practice (DECISION 34'S PROTOCOL, in the docstring): every refusal of the
    command line first, then the roads, the agents and their checks (the arm and H, one environment, the
    backend record, row 117's pairs, each agent's decision-34 fingerprint, its checkpoint average), the
    scoring, the document written once, the records and the report."""
    import fnmatch
    import platform
    import sys
    import epa_freeze as EF
    import epa_roads as ER
    import four_engine_roads as FER

    def refuse(why):
        raise SystemExit(f"\nREFUSING --protocol {DECISION_34}{' --practice' if a.practice else ''}: {why}")
    if a.force_plant_mismatch:
        refuse("--force-plant-mismatch: every agent is scored on the plant, H and reward it trained on, or not "
               "at all (interface sheet 8)")
    if a.label is not None:
        refuse(f"--label: the report is headed {D34_HEADER!r}, or {PRACTICE_HEADER!r} on the practice roads")
    if a.overwrite:
        refuse("--overwrite: decision 34's documents and reports are written once")
    if a.reward_knock is None:
        refuse("--reward-knock in|out is required: the reward the agents trained with is a FATAL field, passed "
               "on the command line and never read from meta.json (interface sheet 8)")
    if a.scores_out is None:
        refuse("--scores-out PATH is required: the scores document is the scoring's result")
    if a.practice and a.records_out is not None:
        refuse("--records-out: the per-step records are the test set's, not the practice roads'")
    for flag, path in (("--scores-out", a.scores_out), ("--records-out", a.records_out)):
        if path is not None and FER.inside_repository(path):
            refuse(f"{flag} {path} lies inside the repository: it is written outside it, and its own step "
                   "commits it")
    if a.out and fnmatch.fnmatch(os.path.basename(a.out), "*_seed*.txt"):
        refuse(f"--out {a.out}: the report is never written as results/*_seed*.txt, which the app reads as "
               "Phase D's")
    index = records_index_path(a.scores_out) if a.records_out else None
    for flag, path in (("--scores-out", a.scores_out), ("--out", a.out), ("--records-out", a.records_out),
                       ("the records' index", index)):
        if path is not None and os.path.exists(path):
            refuse(f"{flag} {path} exists: it is written once")
    if not a.models:
        refuse("no agents given: decision 34 scores runs/<set>/<run> folders")
    jobs = 1 if a.jobs is None else int(a.jobs)
    if jobs < 1:
        refuse(f"--jobs {jobs}: at least 1")
    knock = a.reward_knock == "in"
    plant = engines.get(a.engine)
    rec_path = os.path.join(HERE, *ER.ROADS_REL.split("/"))
    try:
        roads_rec = FER.read_roads_record(rec_path)
    except FER.Refused as exc:
        refuse(str(exc))
    if roads_rec["seed_kind"] == "REAL":
        problem = FER.real_record_problem(rec_path)
        if problem:
            refuse(problem)
    train_backend = committed_train_backend(a.engine, root=HERE)
    record = None
    if a.practice:
        record = ER.load_record(rec_path)
        roads = practice_set(record)
        prov = {"protocol": f"{DECISION_34} practice", "label": PRACTICE_HEADER, "roads_sha": roads_rec["roads_sha"],
                "practice_arrays_sha256": ER.arrays_sha256(roads), "reading": "row 96's practice roads"}
    else:
        roads, prov = decision34_roads(root=HERE)
    agents = read_agents(a.models, roads_rec=roads_rec, engine=a.engine)
    for check, problems in (("one environment (row 143 (5); CLAUDE.md rules 3 and 5)",
                             environment_problems([(x["path"], x["meta"], x["config"]) for x in agents])),
                            ("the backend record's train_backend", backend_problems(agents, train_backend)),
                            ("row 117's pairs", pairing_problems(agents))):
        if problems:
            refuse(f"{check}: " + "; ".join(problems))
    lives = {}
    for x in agents:
        if x["H_s"] is not None and x["H_s"] not in lives:
            lives[x["H_s"]] = live_decision34(plant, preview_h_s=x["H_s"], reward_knock=knock,
                                              train_backend=train_backend)
    blind_live = FP.for_arm(next(iter(lives.values())), sighted=False)
    lines, manifests = [], {}
    for h, live in sorted(lives.items()):
        lines.append(FP.format_block(live, f"DECISION 34 FINGERPRINT (sighted at H {h:g} s)"))
    lines.append(FP.format_block(blind_live, "DECISION 34 FINGERPRINT (blinded)"))
    for x in agents:
        lines += check_model_fingerprint(x["path"], blind_live if x["H_s"] is None else lives[x["H_s"]], False)
        manifests[x["path"]], more = average_lines(x["path"], x["meta"])
        lines.append(f"{x['path']}: {x['arm']}, seed {x['seed']}, H {x['H_s']} s, r {x['r']}")
        lines += more
    ratios = sorted({f"{x['r']:g}" for x in agents if x["r"] is not None}, key=float)
    # the scored set's episodes_sha is the decision-34 twenty's on the test set; the practice roads are not
    # that set, so there it is kept under trained_under alone
    scored_sha = {} if a.practice else {"episodes_sha": blind_live["episodes_sha"]}
    prov.update(trained_under={"scenario": blind_live["scenario"], "episodes_sha": blind_live["episodes_sha"]},
                **scored_sha, reward_knock=knock, train_backend={a.engine: train_backend},
                score_backend=FP.BACKEND_CYCLE, versions=EF.versions(), platform=platform.platform(), device="cpu",
                environment=env_of(agents[0]["meta"], agents[0]["config"]),
                agents=agents_provenance(agents, manifests), recipe_checks=recipe_checks(agents, manifests),
                variant_lines=[], rescored_engines=[a.engine], copied_from=None)
    if a.practice:
        doc, rows = score_practice(a.engine, agents, record, plant=plant, reward_knock=knock,
                                   train_backend=train_backend, jobs=jobs, provenance=prov)
    else:
        rows = score_set(a.engine, agents, roads, plant=plant, reward_knock=knock, train_backend=train_backend,
                         jobs=jobs, keep_records=a.records_out is not None)
        doc = scores_document(a.engine, rows, ratios=ratios, provenance=prov)
    sha = write_once_json(a.scores_out, doc)
    say = d34_report(a.engine, rows, header=PRACTICE_HEADER if a.practice else D34_HEADER, reading=prov["reading"],
                     ratios=ratios, lines=lines)
    if a.practice:
        # decision 29's pilot reads s_p from this document (row 103 (4)); printed beside the scores, never its
        # bound, which is the analysis's (pilot_spread)
        for r in ratios:
            try:
                sp = pilot_spread(doc, engine=a.engine, ratio=r)
            except ValueError as exc:
                say.append(f"s_p at r = {r}: not computed ({exc})")
            else:
                say.append(f"s_p at r = {r} (row 103 (4); no knock, ddof 1, {sp['pairs']} pairs): {sp['s_p']:.4f}")
    say.append("")
    say.append(f"scores document {a.scores_out}: sha256 {sha}")
    if a.records_out:
        files = write_records(a.records_out, a.engine, rows, dt=float(roads[0]["dt"]))
        isha = write_once_json(index, {"files": files, "scores_sha256": sha, "command": " ".join(sys.argv)})
        say.append(f"per-step records under {a.records_out}: {len(files)} files; index {index}, sha256 {isha}")
    print("\n".join(say))
    if a.out:
        os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
        with open(a.out, "x", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(say) + "\n")
        print(f"\nwritten to {a.out}")
    return 0


if __name__ == "__main__":
    main()
