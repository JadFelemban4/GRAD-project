"""four_engine_roads.py -- the four engines' training roads (row 116), a WRAPPER, not an edit.

    python four_engine_roads.py measure --engine E [E ...] --seeds S [S ...] --episodes K
           (--synthetic-roads-seed N | --roads-record PATH | --no-scored-share) [--verify-steps M] [--jobs J] [--out FILE]
    python four_engine_roads.py bounds --engine E [E ...] [--jobs J] [--out FILE]
                    THE NOTIONAL CAR's four numbers against each car's own climb and coast (below);
                    exit 1 when the notional car leaves any car's bounds
                    row 116's measurement "on drawn episodes, reported before training": each engine's
                    share of training steps whose torque request lies below its torque floor
                    (plant.engine.loop.torque_floor_nm) or above its deliverable torque, and the share of
                    training time above 115 km/h, on K episodes per seed drawn exactly as training draws
                    them. A SYNTHETIC roads seed (an int below 2**32) stands in for roads_seed until the
                    reveal (row 96), and everything it prints says SYNTHETIC; --out must then lie outside
                    the repository

Section I of results/VALIDATION_DECISIONS.md governs this file: row 116 (the training mix), row 118
(decision 29's recipe behind flags whose defaults are X1's), rows 96 and 101 (the share's stream and
its generator), row 98 (every grade change a ramp), rows 102 and 117 (H = r tau, and what waits for the
plant commit), row 121 (3) (a new module: random_road.py, engine_env.py and the 35 files roads.json
hashes are left alone; no hashed module imports this one). docs/build_step_2/ORDER_TO_TRAINING.md step
7 builds it. train.py's road mode `four_engine` trains on it.

WHY A WRAPPER. The extremes builders (engine_env.extreme_speed_profile, grade_floor) read the Supra's
two-term road load and gears and refuse every EPA car (BUILT, engine_env._two_term_car; amendment B15),
and engine_env.py may not change before the commit that records the last redraw (rows 94, 97). So this
module builds each episode's cycle itself and hands it to the unchanged environment at every reset, as
random_road.RandomClimb does (random_road.py, RandomClimb.reset), and draws decision 12's first
safeguard, the housing's heat capacity, as ExtremesTrainingEnv.reset draws it.

ONE GENERATOR, NO VEHICLE (row 116). general_episode(rng) takes a random stream and nothing else: its
arrays are the same for every car, as row 95's roads are (test_four_engine_training checks them equal on
the four engines). Decision 12's training ranges, every one read from engine_env (one definition,
mistake 11):
    ambient       uniform on EXTREME_T_AMB_C, 25-45 C, one value per episode (50 C held out)
    speed         from rest, a target drawn uniform on EXTREME_V_KMH, 60-150 km/h, held for EXTREME_HOLD_S,
                  60-180 s (the first counted from 20 s, epa_roads.SPEED_RAMP_S, as extreme_speed_profile
                  counts it), and followed at no more than EXTREME_ACCEL, 0.8 m/s^2, BOTH ways, the launch
                  from rest included (row 116's words; to 150 km/h it takes 52 s), and inside THE NOTIONAL
                  CAR's climb and coast (below): it slows on a hill too steep for its speed and coasts no
                  faster than the road allows. extreme_speed_profile's draws, in its order
    grade         flat for the first TERRAIN_FLAT_START_S, 30 s (no grade while the car accelerates from
                  rest, as make_terrain), then holds, each lasting EXTREME_HOLD_S (60-180 s) from the
                  start of its ramp, at a grade drawn uniform on 0 to EXTREME_GRADE_MAX, 0-18 % (18-22 %
                  held out). Every change is a linear ramp of GRADE_RAMP_S = 8 s from the hold's start,
                  epa_roads.climb_profile's expression, so epa_roads.ramp_problems (row 98 (a)) passes
                  every road. A change whose ramp would not end inside the road is drawn and discarded,
                  as epa_roads.layout discards a climb that does not fit. No descents: without a car,
                  grade_floor cannot be applied either (DESIGN, row 116)
    c_turb        the scale of both thermal networks' c_turb, log-uniform on EXTREME_C_TURB (x0.75-1.333),
                  drawn after the road from the same stream and set on NEW records with
                  dataclasses.replace, never on the plant's (ExtremesTrainingEnv.reset's lines). Decision
                  12 also names the knock threshold and the damage scale; X1 never drew them and they are
                  not drawn here (row 113 (5)), disclosed
    air           101.3 kPa and humidity 0.012 (epa_roads.P_BARO_KPA, HUMIDITY: make_grade_climb's values,
                  which epa_roads.check_engine_env holds equal). There is no thin air: wide_air's
                  ThinAirVehicle refuses an EPA car (row 116)
    length        900 s at dt 1.0 (epa_roads.DURATION_S, DT): a road of 900 samples, an episode of 899
                  steps (epa_roads.EPISODE_STEPS_NOTE). Any other step or length is refused
THE GRADE HOLDS ARE A JUDGEMENT, NOT A MEASUREMENT, stated so, as engine_env states TERRAIN_WEIGHTS:
uniform grades over the whole range (no family weights invented beside it) and the speed holds' own
range (no second range invented). The held grades average 9 % (the uniform's mean, arithmetic), and
unlike make_terrain's families there is no flat or rolling family among them: the flat roads of the
mix are the share's gaps and the 30 s lead-in. measure() reports what the engines are asked for on it.

THE NOTIONAL CAR (31 October 2026, the review of ORDER step 7, findings S1 and F1; a departure from row
116's literal design, stated so, that the team's correction row records). Row 116 first limited the
speed to EXTREME_ACCEL both ways and the grades to 0-18 %, because a generator that takes no car cannot
apply extreme_speed_profile's coast limit or grade_floor. Built that way it failed row 119's road gate,
for two causes MEASURED by the review (check_roads.py --engine E --train-road four_engine --synthetic-seed
101, and its probes; the neutral action's mean reward against |r| < 0.05): (1) a 0.8 m/s^2 slowdown on a
low grade asks the engine for less than its closed-throttle torque, down to -79.7 Nm on the B58 (seed 102:
16 such steps carried -382.7 of the episode's -389.0), the failure engine_env records for X1's first drafts
and the reason extreme_speed_profile coasts; (2) a steep hold at speed asks some cars for more than they
deliver (the Mazda, seed 100: 25 such steps, -50.86 of the episode's reward; the Honda above its
deliverable torque on 8.49 % of general-road steps in the builder's SYNTHETIC measurement). Both limits are
therefore applied, and without reading any car: the speed follows a NOTIONAL car no stronger and no more
slippery than any of the four at any speed, its four numbers (CLIMB_P_W_PER_KG, CLIMB_C_PER_M,
COAST_AT_60, COAST_D0) set once from the four frozen cars' own Vehicle.demand by `bounds` and held there
by test_four_engine_training.NotionalCar. The arrays stay the same for every car, and the generator still
takes no vehicle at run time; what moves is the speed, never a draw or a grade. MEASURED after the change,
31 October 2026, on the team laptop (`python -B four_engine_roads.py measure --engine b58 mazda_25t
honda_l15b7 ford_27tt --seeds 9000 9001 9002 --episodes 10 --synthetic-roads-seed 4242`, SYNTHETIC): on
the 27 general episodes (24 273 steps per car) no request of any of the four cars falls below its torque
floor or above its deliverable torque (before the change: 1.4-1.8 % below the floor on every car, and
above deliverable 1.13 % on the Mazda, 8.49 % on the Honda, 1.10 % on the Ford); the 3 share episodes,
row 101's roads, which this change does not touch, ask the Mazda and the Honda for more than they deliver
on 6 steps each and the Ford on 3, all at steps 17-18 of the 20 s launch to 130 km/h (MEASURED, the same
roads through requests()). Training time above 115 km/h is 29.83 %
of the general steps (36.48 % before) and 36.66 % of all of them. Row 119's road gate then passes on the
three cars train.py can build today (check_roads.py --engine E --train-road four_engine --synthetic-seed
101 --n 8: worst neutral reward -0.0043 on the B58, -0.0081 on the Mazda, -0.0221 on the Ford, against
|r| < 0.05). Row 116's own measurement is re-run on the drawn record before training.

DECISION 29'S SHARE OF THE SCORED KIND OF ROAD (rows 101, 116, 118; train.py --scored-share). A fixed
10 %: with the share on, episode e (counted from the last seeded reset) is a road of row 101's generator
when e % SHARE_EVERY == 0 -- episodes 0, 10, 20, ... -- and a general road otherwise (DESIGN). Why that
schedule: "a fixed share" is exactly one episode in ten for every seed, where a per-episode draw would
make the share itself a random variable (binomial: 50 +/- 6.7 episodes of 500, arithmetic); it is decided by the
episode count alone, so the general stream is consumed by general episodes only and a seed's general
roads come in the same order with the share on or off; and episode 0 is a share episode, so the share's
path runs inside the first episode of any run, smoke runs included. A share road comes from
default_rng([roads_seed, 0x7A, seed]) (epa_roads.STREAM_TRAINING; row 96), seed being the training
seed, through epa_roads.layout and epa_roads.make_road WITHOUT the replacement loop: one layout per share
episode, then that episode's c_turb scale, from the same stream, in that order (as epa_roads.
practice_roads draws a layout, then its weights). The first share road of a seed is therefore epa_roads.
training_share_road(roads_seed, seed) exactly (test_four_engine_training holds the two equal: two
writings of one road are how this project acquires drift, mistake 11). Every share road is a fresh
layout, so a blinded agent cannot memorise when its climbs come (the reason random_road.py exists).
The stream is disjoint from the first draw, the replacement, redraw and practice streams and the frozen
twenty, which are labelled apart (row 96). Its weights are the environment's own draw at reset.

roads_seed is read from the committed roads record, results/EPA_ROADS/roads.json (written once at the
draw, ORDER step 6; row 97), given by its path (read_roads_record). It does not exist yet: with the share
on and no path, the wrapper refuses. A REAL record's roads_seed must be the one its reveal gives
(epa_roads.roads_seed_from); a SYNTHETIC one (an int below 2**32, the tests' and smoke runs') is labelled
SYNTHETIC in every road log line, and train.py refuses to train on one into the repository.

H (rows 102, 117). horizon_s(record, engine_id, r) is H = r x tau_e with tau_e read from the roads
record's `tau` (row 102: the draw computes it once by roads_ceiling's one definition and writes it there;
the re-check and the redraws read it from there), cross-checked against the record's H_table. Until
row 94's plant commit makes H an environment parameter (row 117), preview_h_problem refuses every H but
today's 30 s, whose samples H x (1/15, 1/6, 1/2, 1) are engine_env.PREVIEW_S exactly.

WHAT WAITS FOR LATER STEPS, stated: the EPA engines train through train.py only once trainable() opens
(decision 47; the plant commit, ORDER step 14); the Honda's training also needs step_record's CVT branch
(ORDER step 12a), since train.py's recorder refuses a CVT (step_record.gear); H reaches the environment
with the plant commit; each engine's gates on these roads are ORDER step 17 (row 119).

Every function that runs a plant takes the engine explicitly (mistake 1; test_engine_threading).
"""
import argparse
import hashlib
import inspect
import json
import os
import sys
import tempfile
from dataclasses import replace

import gymnasium as gym
import numpy as np

import engine_env as E
import epa_roads as ER

HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ the design (row 116), DESIGN values
DURATION_S = ER.DURATION_S              # 900 s, row 101's episode
DT = ER.DT                              # 1.0 s
LAUNCH_S = ER.SPEED_RAMP_S              # 20 s from rest, as every road in the project launches
FLAT_START_S = E.TERRAIN_FLAT_START_S   # 30 s with no grade while the car accelerates
RAMP_S = E.GRADE_RAMP_S                 # 8 s, every grade change (row 98 (a))
GRADE_HOLD_S = E.EXTREME_HOLD_S         # the grade holds take the speed holds' range, 60-180 s (DESIGN)
P_BARO_KPA = ER.P_BARO_KPA              # 101.3 kPa
HUMIDITY = ER.HUMIDITY                  # 0.012

# ------------------------------------------------------------------ the streams
# The general roads' stream, default_rng([seed, GENERAL_STREAM]): "4ENG" in ASCII, a label of its own,
# as TerrainTrainingEnv's 0x7E4A1 and random_road's ROAD_STREAM separate theirs from the weight stream
# the environment draws from the same integer seed (DESIGN). It takes no roads_seed: the general roads
# are the same before and after the reveal.
GENERAL_STREAM = 0x34454E47
SHARE_STREAM = ER.STREAM_TRAINING       # 0x7A: default_rng([roads_seed, 0x7A, seed]) (rows 96, 116)
SHARE_EVERY = 10                        # decision 29's fixed 10 %: episodes 0, 10, 20, ... (DESIGN)

# EPA's road-load targets cover 15-115 km/h (40 CFR 1066.305(a); engine_env._ThreeTermRoad): above it
# every EPA car's road load is extrapolated (MD:1111), counted strictly above, as epa_roads.coverage_flags
# counts its steps_above_115_kmh
COVERAGE_KMH = 115.0

# H (rows 102, 117): a sighted agent at horizon H sees the grade H/15, H/6, H/2 and H ahead
PREVIEW_DIVISORS = (15.0, 6.0, 2.0, 1.0)

# THE NOTIONAL CAR (31 October 2026, the review of ORDER step 7, findings S1 and F1; the module docstring
# says why). The speed profile's two limits, four numbers that read no car at run time, each the largest
# round value under the four frozen cars' own bounds (car_bounds: their Vehicle.demand, 25 and 45 C air):
#   climb  a + G0 sin(theta) <= CLIMB_P_W_PER_KG / v - CLIMB_C_PER_M v^2, held under CLIMB_MARGIN's 95 % of
#          the least car's climb at its deliverable torque. The binding car is the Honda above 115 km/h
#          (1.039 m/s^2 at 150 km/h) and the Mazda and the Ford where their boxes run out of gears
#          (105-110 km/h); the B58 never binds. CLIMB_MARGIN is DESIGN: the deliverable tables are measured
#          at 315 K and the training air reaches 318 K.
#   coast  a slowdown <= G0 sin(theta) + COAST_AT_60 + COAST_D0 max(0, v^2 - v60^2), under the least car's
#          coast at its torque floor; the binding car is the B58 (0.024 m/s^2 at 60 km/h on 18 %, 0.469 at
#          150 km/h), the Mazda here and there.
# MEASURED, 31 October 2026, on the team laptop: `python -B four_engine_roads.py bounds --engine b58
# mazda_25t honda_l15b7 ford_27tt --jobs 4` (1 km/h; least climb room +0.006 m/s^2, least coast room
# +0.004), and test_four_engine_training.NotionalCar holds the four numbers inside every car's bounds on a
# coarse grid each run. A car whose spec or derived file changes can move its bounds: the test then fails,
# and these numbers are re-derived by that command, never adjusted by hand.
G0 = 9.81
CLIMB_P_W_PER_KG = 57.5
CLIMB_C_PER_M = 2.3e-4
COAST_AT_60 = 0.02
COAST_D0 = 2.8e-4
COAST_V0 = E.EXTREME_V_KMH[0] / 3.6        # 60 km/h: no slowdown runs below it (the targets' least)
CLIMB_MARGIN = 0.05


class Refused(Exception):
    """A precondition of the training roads does not hold: nothing was drawn."""


# =====================================================================================================
# The generator: a random stream in, a cycle out; no vehicle
# =====================================================================================================
def grade_profile(rng, n, dt):
    """Row 116's grades: flat for FLAT_START_S, then holds of GRADE_HOLD_S at a grade uniform on
    [0, EXTREME_GRADE_MAX], each change a linear ramp of RAMP_S from the hold's start (epa_roads.
    climb_profile's expression). Each hold draws its grade, then its length. A change whose ramp would
    not end inside the road (s + ramp > n - 1) is drawn and discarded and the road holds its grade to the
    end. Each ramp starts from the value the road holds, so a held grade is exactly constant (row 98 (a)
    reads any difference as a change); the clip only removes rounding at the range's ends."""
    t = np.arange(n) * dt
    g = np.zeros(n)
    ramp = int(round(RAMP_S / dt))
    s = int(round(FLAT_START_S / dt))
    while True:
        new = float(rng.uniform(0.0, E.EXTREME_GRADE_MAX))
        hold = int(rng.uniform(*GRADE_HOLD_S) / dt)
        if s + ramp > n - 1:
            break
        held = float(g[s - 1]) if s > 0 else 0.0
        g[s:] = held + (new - held) * np.clip((t[s:] - t[s]) / RAMP_S, 0.0, 1.0)
        s += hold
    return np.clip(g, 0.0, E.EXTREME_GRADE_MAX)


def climb_limit(v_mps):
    """The notional car's climb (m/s^2): the most a + G0 sin(atan(grade)) it asks for at speed v,
    CLIMB_P_W_PER_KG / v - CLIMB_C_PER_M v^2. No limit at rest."""
    v = float(v_mps)
    return float("inf") if v <= 0.0 else CLIMB_P_W_PER_KG / v - CLIMB_C_PER_M * v * v


def coast_road(v_mps):
    """The notional car's coast less the grade's pull (m/s^2): COAST_AT_60 + COAST_D0 (v^2 - v60^2), and
    COAST_AT_60 at 60 km/h and below."""
    v = float(v_mps)
    return COAST_AT_60 + COAST_D0 * max(0.0, v * v - COAST_V0 * COAST_V0)


def coast_limit(v_mps, grade):
    """The notional car's coast (m/s^2): the fastest it slows at speed v on this grade,
    G0 sin(atan(grade)) + coast_road(v): the grade's pull plus a road load under every car's coast at its
    torque floor."""
    return G0 * float(np.sin(np.arctan(float(grade)))) + coast_road(v_mps)


def speed_profile(rng, n, dt, grade):
    """Row 116's speed on the road `grade`: from rest, a target uniform on EXTREME_V_KMH held for
    EXTREME_HOLD_S (the first counted from LAUNCH_S, as extreme_speed_profile counts it), followed at no
    more than EXTREME_ACCEL both ways, and within the notional car's two limits (THE NOTIONAL CAR,
    above): speeding up, a + G0 sin(theta) never above climb_limit(v), which makes the car slow on a
    hill too steep for its speed; slowing down, never faster than coast_limit(v, grade). The step that
    drives v[i-1] to v[i] is step i-1, which the environment reads at v[i-1] and grade[i-1] (forward
    difference), so both limits read those. extreme_speed_profile's draws in its order: the limits
    move the speed, never a draw. The grade is an array of the road, not a car."""
    g = np.asarray(grade, dtype=float)
    v = np.empty(n)
    v[0] = 0.0
    target = rng.uniform(*E.EXTREME_V_KMH) / 3.6
    nxt = int(LAUNCH_S / dt) + int(rng.uniform(*E.EXTREME_HOLD_S) / dt)
    for i in range(1, n):
        if i >= nxt:
            target = rng.uniform(*E.EXTREME_V_KMH) / 3.6
            nxt = i + int(rng.uniform(*E.EXTREME_HOLD_S) / dt)
        vp = float(v[i - 1])
        pull = G0 * float(np.sin(np.arctan(float(g[i - 1]))))
        down = min(E.EXTREME_ACCEL, coast_limit(vp, g[i - 1]))
        up = max(min(E.EXTREME_ACCEL, climb_limit(vp) - pull), -down)
        v[i] = vp + float(np.clip(target - vp, -down * dt, up * dt))
    return v


def c_turb_scale(rng):
    """Decision 12's first safeguard: the housing's heat capacity scale, log-uniform on EXTREME_C_TURB,
    ExtremesTrainingEnv.reset's expression."""
    lo, hi = np.log(E.EXTREME_C_TURB[0]), np.log(E.EXTREME_C_TURB[1])
    return float(np.exp(rng.uniform(lo, hi)))


def general_episode(rng):
    """One general training episode from `rng`: (cycle, c_turb scale). The draws in
    ExtremesTrainingEnv.reset's order: the ambient, the grade, the speed, then the housing's scale. The
    cycle is the environment's form (t_amb one number). Reads no vehicle."""
    n = int(DURATION_S / DT)
    t_amb = 273.15 + float(rng.uniform(*E.EXTREME_T_AMB_C))
    grade = grade_profile(rng, n, DT)
    v = speed_profile(rng, n, DT, grade)
    scale = c_turb_scale(rng)
    cycle = dict(t=np.arange(n) * DT, v_mps=v, grade=grade, t_amb=t_amb, p_baro=P_BARO_KPA,
                 humidity=HUMIDITY)
    return cycle, scale


def share_episode(rng, *, seed):
    """One episode of decision 29's share from the share stream `rng` (default_rng([roads_seed, 0x7A,
    seed])): row 101's layout and road, without the replacement loop, then the c_turb scale. Returns
    (cycle in the environment's form, c_turb scale, the road dict). The first call on a fresh stream is
    epa_roads.training_share_road(roads_seed, seed)'s road; that function draws one road from a stream
    of its own, and these are its two lines on a stream kept for the whole run."""
    lead, climbs, discarded = ER.layout(rng)
    road = ER.make_road(k=None, episode_seed=seed, weights=None, lead=lead, climbs=climbs,
                        discarded=discarded, first_slot=0)
    scale = c_turb_scale(rng)
    return ER.env_cycle(road), scale, road


def general_rng(seed):
    return np.random.default_rng([int(seed), GENERAL_STREAM])


def share_rng(roads_seed, seed):
    return np.random.default_rng([int(roads_seed), SHARE_STREAM, int(seed)])


def is_share_episode(episode):
    return int(episode) % SHARE_EVERY == 0


# =====================================================================================================
# The roads record: roads_seed, tau and H (rows 96, 97, 102, 117)
# =====================================================================================================
def read_roads_record(path):
    """What the training reads from the committed roads record (results/EPA_ROADS/roads.json): roads_seed,
    the seed's kind, the record's sha_text (roads_sha, epa_roads.roads_sha), tau, the ratios and the H
    table. Refused without a path, without a file, or when roads_seed is not the reveal's (REAL) or not a
    SYNTHETIC seed's, or when the record's training-share stream is not row 96's."""
    if path is None:
        raise Refused(f"the scored share needs roads_seed, from the committed roads record {ER.ROADS_REL} "
                      "(written once at the draw, ORDER step 6; row 96): give its path. It does not exist "
                      "until the reveal; a test passes a SYNTHETIC record")
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise Refused(f"{path}: no roads record there. roads_seed comes from {ER.ROADS_REL}, written at the "
                      "draw (ORDER step 6), which does not exist before the reveal (row 96)")
    with open(path, encoding="utf-8") as fh:
        rec = json.load(fh)
    kind = rec.get("seed_kind")
    cr = rec.get("commit_reveal") or {}
    seed = cr.get("roads_seed")
    if not (isinstance(seed, int) and not isinstance(seed, bool)):
        raise Refused(f"{path}: commit_reveal.roads_seed {seed!r} is not an integer")
    if kind == "SYNTHETIC":
        if cr.get("SYNTHETIC") is not True or not 0 <= seed < ER.SYNTHETIC_SEED_LIMIT:
            raise Refused(f"{path}: a SYNTHETIC record holds a seed below 2**32 and says SYNTHETIC; this one "
                          f"holds {seed!r}")
    elif kind == "REAL":
        rev = cr.get("reveal") or {}
        lines = cr.get("hash_lines") or {}
        # The reveal is checked as the draw checked it (epa_roads.draw): each integer at least 2**128 and
        # matching its hash line, and the two lines the ones the roads commit recorded. Without this a
        # hand-made "REAL" record with made-up integers read as REAL (the review of 31 October 2026, R0-2)
        for who in ("ghassan", "jad"):
            if not ER._private_int_ok(rev.get(who)):
                raise Refused(f"{path}: {who}'s revealed integer is not an int of at least 2**128 (row 96)")
            if not ER.reveal_matches(rev.get(who), lines.get(who)):
                raise Refused(f"{path}: {who}'s revealed integer does not match the record's hash line (row 96)")
        committed = committed_hash_lines(cr.get("roads_commit"))
        if committed != (lines.get("ghassan"), lines.get("jad")):
            raise Refused(f"{path}: the record's hash lines are not the ones the roads commit "
                          f"{cr.get('roads_commit')!r} recorded in epa_roads.py (COMMITMENT_G, COMMITMENT_J; "
                          "row 96)")
        live = (ER.COMMITMENT_G, ER.COMMITMENT_J)
        if live != (None, None) and live != committed:
            raise Refused(f"{path}: this tree's epa_roads.py holds other commitment lines than the roads "
                          "commit's: they are set once, in the roads commit (row 96)")
        try:
            want = ER.roads_seed_from(rev.get("ghassan"), rev.get("jad"), cr.get("roads_commit"))
        except (TypeError, ValueError) as exc:
            raise Refused(f"{path}: the reveal cannot be read ({exc})") from exc
        if not 0 <= seed < ER.ROADS_SEED_LIMIT or seed != want:
            raise Refused(f"{path}: roads_seed {seed!r} is not the one the record's reveal gives ({want}; "
                          "row 96)")
    else:
        raise Refused(f"{path}: seed_kind {kind!r} is neither REAL nor SYNTHETIC")
    stream = (rec.get("streams") or {}).get("training_share")
    if stream != ER.streams()["training_share"]:
        raise Refused(f"{path}: the record's training-share stream is {stream!r}, not row 96's "
                      f"{ER.streams()['training_share']!r}")
    return dict(path=path, roads_seed=int(seed), seed_kind=kind, roads_sha=ER.roads_sha(path),
                tau=rec.get("tau") or {}, ratios=list(rec.get("ratios") or []), H_table=rec.get("H_table") or {})


def committed_hash_lines(roads_commit):
    """(COMMITMENT_G, COMMITMENT_J) as the roads commit's epa_roads.py assigns them (epa_roads.
    committed_values on `git show <commit>:epa_roads.py`, in this repository). Refused when the commit is
    not a full sha, or git cannot show the file at it."""
    if not isinstance(roads_commit, str) or len(roads_commit) != 40 or any(c not in "0123456789abcdef"
                                                                         for c in roads_commit):
        raise Refused(f"the roads commit {roads_commit!r} is not a full 40-digit sha (row 96)")
    import subprocess
    p = subprocess.run(["git", "show", f"{roads_commit}:{ER.MODULE_REL}"], cwd=HERE, capture_output=True,
                       text=True, encoding="utf-8")
    if p.returncode != 0:
        raise Refused(f"git cannot show {ER.MODULE_REL} at the roads commit {roads_commit} in {HERE}: "
                      f"{p.stderr.strip()[:200]}")
    return ER.committed_values(p.stdout)


def real_record_problem(path):
    """Why a REAL record at `path` cannot be what a run trains on, or None: it must be the committed roads
    record itself, results/EPA_ROADS/roads.json in this repository, tracked and unchanged since HEAD (the
    draw writes it once and it is committed, ORDER step 6; row 97). train.py and train_all.py ask this of
    every REAL record (the review of 31 October 2026, R0-2)."""
    import subprocess
    want = os.path.normcase(os.path.abspath(os.path.join(HERE, ER.ROADS_REL)))
    if os.path.normcase(os.path.abspath(path)) != want:
        return f"a REAL roads record is read only from {ER.ROADS_REL} in this repository, not from {path}"
    tracked = subprocess.run(["git", "ls-files", "--error-unmatch", "--", ER.ROADS_REL], cwd=HERE,
                             capture_output=True, text=True)
    if tracked.returncode != 0:
        return f"{ER.ROADS_REL} is not tracked: the roads record is committed with the draw (ORDER step 6)"
    clean = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", ER.ROADS_REL], cwd=HERE,
                           capture_output=True, text=True)
    if clean.returncode != 0:
        return f"{ER.ROADS_REL} differs from HEAD's: the roads record is written once (row 97)"
    return None


# Row 96's episode seeds, which the training seeds avoid: the frozen twenty (evaluate.EPISODES, read as
# text by epa_roads.frozen_episodes), D2's practice set (check_c4_convergence.PRACTICE, read as text here,
# so nothing is imported) and the roads' practice episodes (epa_roads.PRACTICE_SEEDS)
def _d2_practice_seeds():
    import ast
    with open(os.path.join(HERE, "check_c4_convergence.py"), encoding="utf-8") as fh:
        tree = ast.parse(fh.read())
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "PRACTICE"
                                                for t in node.targets):
            return tuple(int(row[0]) for row in ast.literal_eval(node.value))
    raise KeyError("check_c4_convergence.py holds no PRACTICE literal")


def reserved_seeds():
    """{name: seeds}: the episode seeds row 96 keeps apart from every training seed."""
    return {"the frozen twenty (evaluate.EPISODES)": tuple(s for s, _ in ER.frozen_episodes(root=HERE)),
            "D2's practice set (check_c4_convergence.PRACTICE)": _d2_practice_seeds(),
            "the roads' practice episodes (epa_roads.PRACTICE_SEEDS)": tuple(ER.PRACTICE_SEEDS)}


def reserved_seed_problem(seeds):
    """Why these training seeds cannot train on the four-engine roads, or None: a training seed in row 96's
    reserved sets would start its first episode on the stream of a scored or practice episode, because
    the environment draws its weights from the reset seed (SupervisoryTunerEnv.reset)."""
    hits = []
    for name, res in reserved_seeds().items():
        got = sorted(set(int(s) for s in seeds) & set(res))
        if got:
            hits.append(f"{got} are {name}")
    if not hits:
        return None
    return ("row 96: the training seeds avoid the frozen twenty, D2's practice set and the practice "
            "episodes; " + "; ".join(hits))


def write_synthetic_record(path, roads_seed, *, taus=None, ratios=None):
    """A SYNTHETIC roads record for tests and smoke runs: the fields read_roads_record reads, with
    roads_seed an int below 2**32 (never a roads seed), and, when given, tau and the H table as the draw
    writes them (epa_roads.h_table). `taus` is {engine_id: tau_s} computed by the roads code
    (roads_ceiling.tau_table); never typed here. The path must lie outside the repository."""
    if inside_repository(path):
        raise Refused(f"{path}: a SYNTHETIC roads record is written outside the repository only")
    if not (isinstance(roads_seed, int) and 0 <= roads_seed < ER.SYNTHETIC_SEED_LIMIT):
        raise Refused(f"the SYNTHETIC seed {roads_seed!r} is not an int below 2**32")
    rec = {"schema": ER.ROADS_SCHEMA, "seed_kind": "SYNTHETIC",
           "label": "SYNTHETIC: not roads.json, and its seed is not roads_seed (row 96)",
           "commit_reveal": {"SYNTHETIC": True, "roads_seed": int(roads_seed)}, "streams": ER.streams()}
    if taus is not None:
        rs = [float(r) for r in ratios]
        rec["ratios"] = rs
        rec["tau"] = {e: {"tau_s": float(t)} for e, t in taus.items()}
        rec["H_table"] = ER.h_table({e: float(t) for e, t in taus.items()}, rs, dt=DT)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(rec, fh, indent=1)
    return path


def horizon_s(record, engine_id, ratio):
    """H = r x tau_e (row 102), tau_e from the roads record (read_roads_record's `tau`), r one of the
    record's ratios, and the product equal to the record's H_table entry where it has one. Refused
    otherwise: H is computed here and nowhere else in the training path, never typed."""
    r = float(ratio)
    if r not in [float(x) for x in record["ratios"]]:
        raise Refused(f"r = {r:g} is not one of the roads record's ratios {record['ratios']} (row 102: the "
                      "ratios are fixed, the same on every engine)")
    t = (record["tau"].get(engine_id) or {}).get("tau_s")
    if t is None:
        raise Refused(f"the roads record holds no tau for {engine_id} (row 102: the draw writes every "
                      "engine's tau into it)")
    h = r * float(t)
    ht = ((record["H_table"].get(engine_id) or {}).get(f"{r:g}") or {}).get("H_s")
    if ht is not None and float(ht) != h:
        raise Refused(f"{engine_id}: r tau = {h!r} s, and the record's H_table says {ht!r} s")
    return h


def preview_steps(h_s, *, dt):
    """The step each of row 117's four samples falls on: int((H / d) / dt), as epa_roads.h_table."""
    return [int((float(h_s) / d) / dt) for d in PREVIEW_DIVISORS]


def preview_h_problem(h_s):
    """Why the environment cannot train at H = h_s seconds today, or None. Today's preview is
    engine_env.PREVIEW_S = (2, 5, 15, 30) s, which is H = 30 s at row 117's samples H x (1/15, 1/6,
    1/2, 1) exactly; no other H exists until row 94's plant commit makes H an environment parameter
    (row 117), and engine_env.py may not change before the commit that records the last redraw."""
    if h_s is None:
        return None
    if tuple(float(h_s) / d for d in PREVIEW_DIVISORS) == tuple(float(x) for x in E.PREVIEW_S):
        return None
    return (f"H = {float(h_s):.4f} s: the environment previews at engine_env.PREVIEW_S = "
            f"{tuple(E.PREVIEW_S)} s, which is H = 30 s, and at no other H. H becomes an environment "
            "parameter in row 94's plant commit (row 117; ORDER step 14), which changes engine_env.py and "
            "may not land before the commit that records the last redraw (ORDER step 12). Until then "
            "nothing trains at any other H")


def run_tag(seed, *, use_preview, ratio):
    """A run's directory name: sighted_seed<S> or blind_seed<S> (unchanged), and sighted_r<r>_seed<S> for a
    sighted agent at H = r tau (the third arm, train_all.py --third-arm). A blinded agent has no r: one
    blinded arm serves both ratios (row 117)."""
    if ratio is None:
        return f"{'sighted' if use_preview else 'blind'}_seed{int(seed)}"
    if not use_preview:
        raise Refused("a blinded agent sees no grade ahead at any H: it takes no ratio (row 117)")
    return f"sighted_r{float(ratio):g}_seed{int(seed)}"


def inside_repository(path):
    a = os.path.normcase(os.path.abspath(path))
    return a == os.path.normcase(HERE) or a.startswith(os.path.normcase(HERE) + os.sep)


def code_sha():
    """sha256 over this module's CODE and epa_roads.py's (whose generator the share draws), docstrings
    and comments excluded, by fingerprint._code_only, the rule random_road.code_sha uses: train.py
    records it in meta.json (advisory train_road_sha) and refuses a resume across a change."""
    import fingerprint as FP
    h = hashlib.sha256()
    for mod in (sys.modules[__name__], ER):
        src = inspect.getsource(mod).replace("\r\n", "\n")
        code = FP._code_only(src)
        h.update((code if code is not None else src).encode("utf-8"))
    return h.hexdigest()[:16]


# =====================================================================================================
# The wrapper
# =====================================================================================================
class FourEngineRoads(gym.Wrapper):
    """Set the environment's cycle at every reset to the next training road (row 116).

    `reset(seed=s)` reseeds both road streams from s and restarts the episode count; a plain `reset()`
    draws the next episode, as random_road.RandomClimb does and as stable-baselines3 calls it (seeded
    once, then unseeded), so a training run is a fixed sequence of roads given its seed. After the
    environment's own reset, both thermal networks get the episode's c_turb on a NEW record, as
    ExtremesTrainingEnv.reset sets it. The drawn road is in info["road"] and self.road; road_log keeps
    one line per reset for train.py's curve.csv.

    `scored_share` turns on decision 29's share (default off, X1's training: row 118); it then needs
    `roads_record`, the path of the roads record that holds roads_seed. Refused: a step other than DT, a
    length other than DURATION_S, a share with no record, a record with no share (nothing would read it).
    """

    def __init__(self, env, *, seed, duration, scored_share=False, roads_record=None):
        super().__init__(env)
        base = env.unwrapped
        if float(duration) != DURATION_S or float(base.dt) != DT:
            raise Refused(f"the four-engine roads are {DURATION_S:g} s at dt {DT:g} (row 101's episode, row "
                          f"116); this environment runs {float(duration):g} s at dt {float(base.dt):g}")
        if scored_share:
            self.share = read_roads_record(roads_record)
        elif roads_record is not None:
            raise Refused("a roads record without the scored share: nothing would read it")
        else:
            self.share = None
        self._c_turb0 = float(base.thermal.p.c_turb)
        self.c_turb_scale = 1.0
        self.road = None
        self.road_log = []
        self._reseed(seed)

    def _reseed(self, seed):
        self.road_seed = int(seed)
        self._general = general_rng(self.road_seed)
        self._share = None if self.share is None else share_rng(self.share["roads_seed"], self.road_seed)
        self.episode = 0

    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self._reseed(seed)
        base = self.env.unwrapped
        if self.share is not None and is_share_episode(self.episode):
            cycle, scale, road = share_episode(self._share, seed=self.road_seed)
            kind = "scored"
            extra = dict(seed_kind=self.share["seed_kind"], lead_s=road["draws"]["lead_s"],
                         climbs=len(road["climbs"]))
        else:
            cycle, scale = general_episode(self._general)
            kind, extra = "general", {}
        base.cycle = cycle
        self.c_turb_scale = scale
        obs, info = self.env.reset(seed=seed, options=options)
        # The episode's housing: a NEW record with the drawn capacity, never a change to the plant's
        # (ExtremesTrainingEnv.reset's lines, after the environment's reset as there)
        for tn in (base.thermal, base.thermal_base):
            tn.p = replace(tn.p, c_turb=self._c_turb0 * self.c_turb_scale)
        self.road = dict(kind=kind, episode=self.episode, t_amb_c=float(cycle["t_amb"]) - 273.15,
                         c_turb_scale=scale, **extra)
        label = "scored " + self.share["seed_kind"] if kind == "scored" else kind
        self.road_log.append(f"{label} {self.road['t_amb_c']:.1f}C c_turb x{scale:.3f}")
        self.episode += 1
        info = dict(info)
        info["road"] = dict(self.road)
        return obs, info


def wrap(env, *, seed, scored_share, roads_record):
    """train.build_env's call: the wrapper at the standard length."""
    return FourEngineRoads(env, seed=seed, duration=DURATION_S, scored_share=scored_share,
                           roads_record=roads_record)


# =====================================================================================================
# Row 116's measurement: what the drawn episodes ask of each engine
# =====================================================================================================
def requests(env):
    """(torque_req, rpm, v_kmh) at every step of the episode env.cycle holds, k = 0 .. n - 2 (the
    environment truncates at k >= n - 1), computed as SupervisoryTunerEnv.step computes them before it
    runs the plant: the car's demand at the step's speed, forward-difference acceleration, grade and air
    density. The request depends on the road and the car alone, never on the policy, so no plant runs
    here; verify() holds these equal to env.step's own, element for element."""
    c = env.cycle
    v = np.asarray(c["v_mps"], dtype=float)
    g = np.asarray(c["grade"], dtype=float)
    n = len(v)
    rho = c.get("p_baro", 101.3) * 1000.0 / (287.0 * c["t_amb"])
    tq, rpm = np.empty(n - 1), np.empty(n - 1)
    for k in range(n - 1):
        vk = float(v[k])
        accel = (float(v[min(k + 1, n - 1)]) - vk) / env.dt
        tq[k], rpm[k] = env.veh.demand(vk, accel, float(g[k]), rho=rho)
    return tq, rpm, v[:n - 1] * 3.6


def deliverable_nm(env, rpm):
    """The car's DERIVED deliverable-torque table at these engine speeds, read as Vehicle.
    shift_ceiling_nm and CvtVehicle.deliverable_nm read it (np.interp, held at its ends). The table is
    measured at the car's table air (car.table_t_amb, 42 C on all four), not at the episode's."""
    r, t = zip(*env.veh.DELIVERABLE_TORQUE)
    return np.interp(np.asarray(rpm, dtype=float), r, t)


def episode_counts(env):
    """One drawn episode's counts: steps, requests below the torque floor (and below 0 Nm), above the
    deliverable torque, either, and steps above COVERAGE_KMH."""
    tq, rpm, kmh = requests(env)
    floor = float(env.plant.engine.loop.torque_floor_nm)
    below = tq < floor
    above = tq > deliverable_nm(env, rpm)
    return dict(steps=int(len(tq)), below_floor=int(np.count_nonzero(below)),
                negative=int(np.count_nonzero(tq < 0.0)), above_deliverable=int(np.count_nonzero(above)),
                either=int(np.count_nonzero(below | above)),
                above_coverage_kmh=int(np.count_nonzero(kmh > COVERAGE_KMH)))


def arrays_sha(cycle):
    h = hashlib.sha256()
    for key in ("t", "v_mps", "grade"):
        h.update(np.asarray(cycle[key], dtype=np.float64).tobytes())
    h.update(np.float64(cycle["t_amb"]).tobytes())
    return h.hexdigest()[:16]


def _base_env(plant, *, seed):
    return E.SupervisoryTunerEnv(E.locked_climb(plant, duration=DURATION_S, dt=DT), plant=plant, dt=DT,
                                 seed=seed)


def verify(engine_id, *, seed, steps, scored_share, roads_record):
    """requests() against env.step on the seed's first episode, the neutral action, `steps` steps: the
    torque request and the engine speed must be equal, element for element (a mismatch is a defect of
    requests(), never a tolerance). Returns the number of steps compared."""
    import engines
    plant = engines.get(engine_id)
    w = FourEngineRoads(_base_env(plant, seed=seed), seed=seed, duration=DURATION_S,
                        scored_share=scored_share, roads_record=roads_record)
    w.reset(seed=seed)
    base = w.unwrapped
    tq, rpm, _ = requests(base)
    a = E.neutral_action()
    m = min(int(steps), len(tq))
    for k in range(m):
        _, _, _, _, info = w.step(a)
        if info["torque_req"] != tq[k] or base.rpm != rpm[k]:
            raise AssertionError(f"{engine_id}, step {k}: env.step asks {info['torque_req']!r} Nm at "
                                 f"{base.rpm!r} rpm, requests() {tq[k]!r} Nm at {rpm[k]!r} rpm")
    return m


def measure_engine(engine_id, *, seeds, episodes, scored_share, roads_record):
    """Every drawn episode's counts on one engine: K episodes per seed, drawn through the wrapper exactly
    as a training run draws them (the first reset seeded, the rest not)."""
    import engines
    plant = engines.get(engine_id)
    out, w = [], None
    for s in seeds:
        w = FourEngineRoads(_base_env(plant, seed=s), seed=s, duration=DURATION_S,
                            scored_share=scored_share, roads_record=roads_record)
        for ep in range(int(episodes)):
            w.reset(seed=s if ep == 0 else None)
            base = w.unwrapped
            row = dict(seed=int(s), episode=ep, kind=w.road["kind"], t_amb_c=w.road["t_amb_c"],
                       c_turb_scale=w.road["c_turb_scale"], arrays_sha=arrays_sha(base.cycle))
            row.update(episode_counts(base))
            out.append(row)
    return dict(engine=engine_id, torque_floor_nm=float(plant.engine.loop.torque_floor_nm),
                vehicle=type(w.unwrapped.veh).__name__,
                table_t_amb_k=float(plant.car.table_t_amb), episodes=out)


def _measure_task(task):
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    kind, engine_id, kw = task
    if kind == "verify":
        return kind, engine_id, verify(engine_id, **kw)
    return kind, engine_id, measure_engine(engine_id, **kw)


def summarise(rows, keys=("below_floor", "negative", "above_deliverable", "either", "above_coverage_kmh")):
    """Shares of the steps of `rows`, with the counts behind them (mistake 4)."""
    steps = sum(r["steps"] for r in rows)
    out = dict(episodes=len(rows), steps=steps)
    for k in keys:
        n = sum(r[k] for r in rows)
        out[k] = dict(steps=n, share=(n / steps if steps else float("nan")))
    return out


def measure(engine_ids, *, seeds, episodes, scored_share, roads_record, verify_steps, jobs):
    """Row 116's measurement on every engine (in `jobs` processes): per engine, the shares over all its
    drawn episodes, over the general and the scored ones apart, and the check that every engine drew the
    same arrays (the generator reads no vehicle)."""
    tasks = [("measure", e, dict(seeds=list(seeds), episodes=int(episodes), scored_share=scored_share,
                                 roads_record=roads_record)) for e in engine_ids]
    if verify_steps:
        tasks += [("verify", e, dict(seed=int(seeds[0]), steps=int(verify_steps), scored_share=scored_share,
                                     roads_record=roads_record)) for e in engine_ids]
    if jobs <= 1:
        res = [_measure_task(t) for t in tasks]
    else:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(min(int(jobs), len(tasks))) as pool:
            res = pool.map(_measure_task, tasks)
    per = {e: r for k, e, r in res if k == "measure"}
    verified = {e: r for k, e, r in res if k == "verify"}
    shas = {e: [row["arrays_sha"] for row in per[e]["episodes"]] for e in engine_ids}
    same = all(shas[e] == shas[engine_ids[0]] for e in engine_ids)
    out = dict(engines={}, same_arrays_on_every_engine=same, verified_steps=verified,
               seeds=list(seeds), episodes_per_seed=int(episodes))
    for e in engine_ids:
        rows = per[e]["episodes"]
        out["engines"][e] = dict({k: v for k, v in per[e].items() if k != "episodes"},
                                 all=summarise(rows), general=summarise([r for r in rows if r["kind"] == "general"]),
                                 scored=summarise([r for r in rows if r["kind"] == "scored"]),
                                 t_amb_c=[min(r["t_amb_c"] for r in rows), max(r["t_amb_c"] for r in rows)],
                                 c_turb_scale=[min(r["c_turb_scale"] for r in rows),
                                               max(r["c_turb_scale"] for r in rows)],
                                 episodes=rows)
    return out


def report_lines(res, *, label):
    """The measurement as printed."""
    lines = [f"ROW 116'S MEASUREMENT ON DRAWN TRAINING EPISODES -- {label}",
             f"  seeds {res['seeds']}, {res['episodes_per_seed']} episodes each, drawn as training draws them "
             f"(the share {'on' if any(r['kind'] == 'scored' for e in res['engines'].values() for r in e['episodes']) else 'off'})",
             f"  every engine drew the same arrays: {res['same_arrays_on_every_engine']}",
             "  " + ("; ".join(f"{e}: requests() equal to env.step on {n} steps" for e, n in res["verified_steps"].items())
                     or "requests() not checked against env.step in this run"),
             "  request shares, of the training steps (an episode is 899 steps):",
             f"    {'engine':<12} {'part':<8} {'eps':>4} {'steps':>6} {'< floor':>14} {'< 0 Nm':>14} "
             f"{'> deliverable':>14} {'either':>14} {'> 115 km/h':>14}"]
    for e, r in res["engines"].items():
        for part in ("all", "general", "scored"):
            s = r[part]
            if not s["episodes"]:
                continue
            cells = " ".join(f"{100 * s[k]['share']:6.2f} % {s[k]['steps']:>5}" for k in
                             ("below_floor", "negative", "above_deliverable", "either", "above_coverage_kmh"))
            lines.append(f"    {e:<12} {part:<8} {s['episodes']:>4} {s['steps']:>6} {cells}")
        lines.append(f"    {'':<12} floor {r['torque_floor_nm']:g} Nm; {r['vehicle']}; deliverable table at "
                     f"{r['table_t_amb_k']:g} K; ambient drawn {r['t_amb_c'][0]:.1f}-{r['t_amb_c'][1]:.1f} C; "
                     f"c_turb x{r['c_turb_scale'][0]:.3f}-{r['c_turb_scale'][1]:.3f}")
    return lines


# =====================================================================================================
# The notional car against the four cars: what `bounds` measures and the tests hold
# =====================================================================================================
BOUNDS_SPEEDS_KMH = tuple(float(x) for x in range(1, 151))       # the climb: the launch included
BOUNDS_COAST_KMH = tuple(float(x) for x in range(60, 151))       # the coast: a slowdown runs at 60-150 km/h
BOUNDS_GRADES = tuple(round(0.01 * k, 2) for k in range(19))     # 0-18 % in steps of 1 %
BOUNDS_T_AMB_C = E.EXTREME_T_AMB_C                               # the training air's two ends, 25 and 45 C


def _rho(t_amb_c):
    return P_BARO_KPA * 1000.0 / (287.0 * (273.15 + float(t_amb_c)))


def _first(ok, lo, hi, step, tol=1e-4):
    """The least x in [lo, hi] at which ok(x) is False, by a scan of `step` from lo (so a test that is not
    monotone shows its first failure), then bisection inside the failing interval; hi when none fails."""
    x = lo
    while x + step <= hi:
        if not ok(x + step):
            a, b = x, x + step
            while b - a > tol:
                m = 0.5 * (a + b)
                a, b = (m, b) if ok(m) else (a, m)
            return a
        x += step
    return hi


def car_bounds(engine_id, *, speeds_kmh=BOUNDS_SPEEDS_KMH, coast_kmh=BOUNDS_COAST_KMH, grades=BOUNDS_GRADES,
               parts=("climb", "coast")):
    """One car's two bounds, through its own Vehicle.demand (the request the environment computes, the
    gear or ratio included), no plant stepped. `climb[v]`: the least specific force s = a + G0 sin(theta),
    m/s^2, at which the request passes the car's deliverable torque at the engine speed demand() returns
    (the box has no lower gear left to give it, or the CVT no more power), the least over the training
    air's two ends and over two ways of asking it (accelerating at s on a flat road; holding speed on the
    grade whose pull is s). `coast[v]`: the least, over `grades`, of the largest deceleration at which the
    request stays at or above the torque floor (engine.loop.torque_floor_nm), less the grade's pull, at
    the same two airs. Scanned in steps of 0.01 m/s^2 (climb) and 0.02 (coast) from 0, so a request that
    is not monotone shows its first failure, then bisected to 1e-4. A bound past the generator's reach
    (a + pull above EXTREME_ACCEL + the 18 % pull, or a coast residual over 1 m/s^2) is reported as that
    reach."""
    import engines
    plant = engines.get(engine_id)
    veh = E.vehicle_for(plant.car)
    rr, tt = (np.asarray(x, dtype=float) for x in zip(*veh.DELIVERABLE_TORQUE))
    floor = float(plant.engine.loop.torque_floor_nm)
    reach = climb_reach()
    rhos = [_rho(t) for t in BOUNDS_T_AMB_C]
    climb = {}
    for vk in (speeds_kmh if "climb" in parts else ()):
        v, worst = vk / 3.6, reach
        for rho in rhos:
            for way in ("accelerate", "climb"):
                def ok(s, v=v, rho=rho, way=way):
                    a, g = (s, 0.0) if way == "accelerate" else (0.0, float(np.tan(np.arcsin(min(s / G0, 0.99)))))
                    tq, rpm = veh.demand(v, a, g, rho=rho)
                    return tq <= float(np.interp(rpm, rr, tt))
                worst = min(worst, _first(ok, 0.0, reach, 0.01))
        climb[vk] = worst
    coast = {}
    for vk in (coast_kmh if "coast" in parts else ()):
        v, worst = vk / 3.6, 1.0
        for rho in rhos:
            for gr in grades:
                pull = G0 * float(np.sin(np.arctan(gr)))
                def ok(d, v=v, rho=rho, gr=gr):
                    return veh.demand(v, -d, gr, rho=rho)[0] >= floor
                worst = min(worst, _first(ok, 0.0, pull + 1.0, 0.02) - pull)
        coast[vk] = worst
    return dict(engine=engine_id, vehicle=type(veh).__name__, torque_floor_nm=floor, climb=climb, coast=coast)


def climb_reach():
    """The most a + G0 sin(theta) the generator can ask at all: EXTREME_ACCEL up the steepest grade."""
    return E.EXTREME_ACCEL + G0 * float(np.sin(np.arctan(E.EXTREME_GRADE_MAX)))


def notional_problems(bounds):
    """Where the notional car leaves one car's bounds, [(kind, v_kmh, the notional car's, the car's)]: its
    climb as the generator applies it (at most climb_reach()), above (1 - CLIMB_MARGIN) x the car's climb
    bound wherever that bound lies inside the reach; its coast's road-load part, coast_road(v), above the
    car's coast residual."""
    reach = climb_reach()
    out = []
    for vk, b in bounds["climb"].items():
        mine = min(reach, climb_limit(float(vk) / 3.6))
        if b < reach and mine > (1.0 - CLIMB_MARGIN) * b:
            out.append(("climb", float(vk), mine, b))
    for vk, b in bounds["coast"].items():
        mine = coast_road(float(vk) / 3.6)
        if mine > b:
            out.append(("coast", float(vk), mine, b))
    return out


def feasibility_problems():
    """Where the two limits cannot both hold: a hill at the top of the range (EXTREME_GRADE_MAX) at a speed
    whose climb limit asks the car to slow faster than EXTREME_ACCEL, which the profile then cannot do;
    [(v_kmh, the deceleration needed)] over 60-150 km/h in steps of 1 km/h."""
    pull = G0 * float(np.sin(np.arctan(E.EXTREME_GRADE_MAX)))
    out = []
    for vk in BOUNDS_COAST_KMH:
        need = pull - climb_limit(vk / 3.6)
        if need > E.EXTREME_ACCEL:
            out.append((vk, need))
    return out


def _bounds_task(task):
    os.environ["OMP_NUM_THREADS"] = "1"
    os.environ["MKL_NUM_THREADS"] = "1"
    engine_id, kw = task
    return car_bounds(engine_id, **kw)


def bounds(engine_ids, *, jobs, **kw):
    """car_bounds on every engine (in `jobs` processes), with notional_problems on each."""
    tasks = [(e, kw) for e in engine_ids]
    if jobs <= 1:
        res = [_bounds_task(t) for t in tasks]
    else:
        import multiprocessing as mp
        with mp.get_context("spawn").Pool(min(int(jobs), len(tasks))) as pool:
            res = pool.map(_bounds_task, tasks)
    for r in res:
        r["problems"] = notional_problems(r)
    return res


def bounds_lines(res):
    reach = climb_reach()
    lines = ["THE NOTIONAL CAR AGAINST EACH CAR (demand() only; the training air's two ends, 25 and 45 C)",
             f"  climb: a + g sin(theta) <= {CLIMB_P_W_PER_KG:g} / v - {CLIMB_C_PER_M:g} v^2 (m/s^2), held under "
             f"{100 * (1 - CLIMB_MARGIN):.0f} % of each car's climb at its deliverable torque",
             f"  coast: a deceleration <= g sin(theta) + {COAST_AT_60:g} + {COAST_D0:g} (v^2 - v60^2), held under each car's "
             "coast at its torque floor"]
    for r in res:
        cl, co = r["climb"], r["coast"]
        lines.append(f"  {r['engine']} ({r['vehicle']}, floor {r['torque_floor_nm']:g} Nm):")
        if cl:
            lines.append("    climb bound by km/h (notional in brackets): " + " ".join(
                f"{vk:.0f}:{b:.3f}({min(reach, climb_limit(vk / 3.6)):.3f})" for vk, b in cl.items() if vk % 10 == 0))
            room = [((1 - CLIMB_MARGIN) * b - min(reach, climb_limit(vk / 3.6)), vk) for vk, b in cl.items()
                    if b < reach]
            lines.append("    least climb room: " + (f"{min(room)[0]:+.4f} m/s^2 at {min(room)[1]:.0f} km/h"
                                                      if room else "the car's bound is past the reach everywhere"))
        if co:
            lines.append("    coast residual by km/h (notional in brackets): " + " ".join(
                f"{vk:.0f}:{b:.3f}({coast_road(vk / 3.6):.3f})" for vk, b in co.items() if vk % 10 == 0))
            room = min((b - coast_road(vk / 3.6), vk) for vk, b in co.items())
            lines.append(f"    least coast room: {room[0]:+.4f} m/s^2 at {room[1]:.0f} km/h")
        lines.append(f"    problems: {len(r['problems'])}" + (f", first {r['problems'][0]}" if r["problems"] else ""))
    feas = feasibility_problems()
    lines.append(f"  feasibility (an 18 % hill at 60-150 km/h needs no slowdown faster than EXTREME_ACCEL): "
                 + ("OK" if not feas else f"{len(feas)} speeds fail, first {feas[0]}"))
    return lines


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("measure", help="row 116's measurement on drawn episodes")
    m.add_argument("--engine", nargs="+", required=True, choices=ER.ENGINES,
                   help="the engines to measure (REQUIRED: no default engine, CLAUDE.md mistake 1)")
    m.add_argument("--seeds", nargs="+", type=int, required=True,
                   help="training seeds to draw from (scratch seeds here; the preregistration names the real ones)")
    m.add_argument("--episodes", type=int, required=True, help="episodes drawn per seed")
    g = m.add_mutually_exclusive_group(required=True)
    g.add_argument("--synthetic-roads-seed", type=int, help="a SYNTHETIC roads seed (an int below 2**32)")
    g.add_argument("--roads-record", help="the committed roads record, results/EPA_ROADS/roads.json")
    g.add_argument("--no-scored-share", action="store_true", help="the general roads only")
    m.add_argument("--verify-steps", type=int, default=120,
                   help="steps of each engine's first episode on which requests() is checked against env.step")
    m.add_argument("--jobs", type=int, default=4)
    m.add_argument("--out", help="write the JSON here (outside the repository for a SYNTHETIC seed)")
    b = sub.add_parser("bounds", help="the notional car's two limits against each car's own")
    b.add_argument("--engine", nargs="+", required=True, choices=ER.ENGINES,
                   help="the cars to hold the notional car against (REQUIRED: no default engine, mistake 1)")
    b.add_argument("--jobs", type=int, default=4)
    b.add_argument("--out", help="write the JSON here")
    a = ap.parse_args(argv)
    if a.cmd == "bounds":
        res = bounds(a.engine, jobs=a.jobs)
        print("\n".join(bounds_lines(res)))
        if a.out:
            with open(a.out, "w", encoding="utf-8") as fh:
                json.dump(res, fh, indent=1)
            print(f"written to {a.out}")
        return 1 if any(r["problems"] for r in res) or feasibility_problems() else 0
    tmp = None
    try:
        if a.synthetic_roads_seed is not None:
            if a.out and inside_repository(a.out):
                raise Refused(f"{a.out}: a SYNTHETIC measurement is written outside the repository only")
            tmp = tempfile.mkdtemp(prefix="four_engine_synthetic_")
            record = write_synthetic_record(os.path.join(tmp, "roads.SYNTHETIC.json"), a.synthetic_roads_seed)
            share, label = True, f"SYNTHETIC roads seed {a.synthetic_roads_seed} (not roads_seed; row 96)"
        elif a.roads_record:
            rec = read_roads_record(a.roads_record)
            record, share = a.roads_record, True
            label = f"{rec['seed_kind']} roads record {rec['path']} (roads_sha {rec['roads_sha']})"
            if rec["seed_kind"] == "SYNTHETIC" and a.out and inside_repository(a.out):
                raise Refused(f"{a.out}: a SYNTHETIC measurement is written outside the repository only")
        else:
            record, share, label = None, False, "no scored share"
        res = measure(a.engine, seeds=a.seeds, episodes=a.episodes, scored_share=share, roads_record=record,
                      verify_steps=a.verify_steps, jobs=a.jobs)
    except Refused as exc:
        raise SystemExit(f"REFUSED: {exc}")
    finally:
        if tmp:
            import shutil
            shutil.rmtree(tmp, ignore_errors=True)
    res["label"] = label
    print("\n".join(report_lines(res, label=label)))
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=1)
        print(f"written to {a.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
