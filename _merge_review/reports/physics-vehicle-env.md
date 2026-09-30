# physics-vehicle-env -- whose vehicle / engine / environment modelling is more physical

Agent label: physics-vehicle-env. Written 30 Sep 2026 00:40 AST.
Trees compared: JAD = JMF-2340550-sep17 @ 086c519, GHASSAN = JMF-2340550 @ 74de99a, BASE = f6b46e9.
All runs in copies under `scratchpad/work/physics-vehicle-env/` (Python 3.12, PYTHONIOENCODING=utf-8).
Nothing in MERGE, the main repository or `scratchpad/trees` was modified (the only runs that
imported from the trees, `spark_check.py`, found valid `__pycache__` files already present from
22:41 and wrote nothing; checked with `ls --time-style` on both `__pycache__` folders).

## Headline

**Ghassan's vehicle/engine physics is more correct on every component where the env/plant code
differs -- shift ceiling, drag air density, exhaust flow, boost-ceiling inlet and form, spark
offset, enrichment dwell -- and each is either unambiguous physics or measured against the car.
Against him: his derived thermal constants are numerically unstable above dt ~1.1 s (finding 2).
Two findings outweigh any single component, and the first applies to BOTH branches:**

1. **The knock damage term on every step-shaped road is a one-sample artifact.** At the instant the
   grade steps (t = 180 s on the locked climb, and at the drawn start of every D2/C4 road), the
   baseline ECU's spark is scheduled on the PREVIOUS step's manifold pressure (cruise, ~66 kPa)
   while the load loop jumps the pressure to ~145 kPa in the same step. KI reaches 2.1 for exactly
   one step. At dt 1.0 that one step is 66.3 damage units on Jad's physics (96 % of the episode's
   knock term, 6.9 % of total damage) and 58.6 on Ghassan's; it is proportional to dt (13.3 at dt
   0.2, 132.7 at dt 2.0), and on the D2 grade range it is 34-102 units per episode -- the size of
   the 50-unit minimum effect of interest. **Ramping the same grade over 8 s removes it** (knock
   69.3 -> 3.5 on Jad's, 60.6 -> 2.4 on Ghassan's; turbine term unchanged). It is 94 % of the dt
   sensitivity CLAUDE.md measured, and it is ALL of the hand-written "preview over current-grade"
   gap (-0.44 / -0.32 points at dt 1.0; on turbine-only damage the gap is +0.01 / +0.04 points).
   Preview is the one piece of information that lets a policy pre-retard for it.
2. **Ghassan's derived thermal constants make the coolant node numerically stiff.** Explicit-Euler
   amplification per step of a coolant perturbation at the climb: -0.78 at dt 1.0, -1.67 at 1.5,
   -2.56 at 2.0 (Jad's: +0.84 at 1.0, +0.67 at 2.0). So on Ghassan's branch dt 1.0 is stable but
   rings, and **generality_test.py (dt 2.0 on both branches) runs with a sustained coolant limit
   cycle of 86.8-95.4 C, 8.3 K per step, thermostat flipping 0 <-> 1** (measured, neutral policy).

Verdict per component (details and evidence below):

| component | Jad | Ghassan | more physical |
|---|---|---|---|
| ZF 8HP51 ratios, final drive, locked converter, upshift rule | same code | same code | equal |
| downshift / torque limit | flat 0.75 x 500 Nm | min(375 Nm, model's deliverable torque at gear rpm) | Ghassan (vs the model's engine); neither vs the real 500 Nm engine |
| aero drag air density | typed 1.2 kg/m3 | ideal gas at cycle ambient (1.1205 at 42 C) | Ghassan |
| exhaust mass flow into turbine node | fuel x 15 | air + fuel | Ghassan |
| boost ceiling inlet temperature | charge temperature (~330 K) | ambient (315 K) | Ghassan (plant.py's own docstring, both branches) |
| boost ceiling form | 2-parameter saturating fit | running-max of binned p95 | Ghassan, medium confidence |
| BaselineECU part-load spark offset | 26.18, line never used | derived 13.42, line used 25/26 | Ghassan |
| enrichment dwell 2/9 s vs 1.5/3 s | row-count axis | timestamp axis | Ghassan (irrelevant to both experiments) |
| roads | randomised single step climb | 5 families, ramped | mixed (see section 2) |
| train/eval time step | 0.2 / 1.0 | 1.0 / 1.0 | Ghassan (consistency) -- but sidestepped, not fixed |
| per-step constructs (PI, knock pull, 1-step spark lag) | present | present, identical | neither |
| thermal integration stability | stable at every dt tested | unstable above ~1.1 s | Jad |

## What was read, what was not

Read in full: JAD/engine_env.py (1037 lines), GHASSAN/engine_env.py (1279), JAD/random_road.py
(314), GHASSAN/check_roads.py (103), JAD/plant.py (588), GHASSAN/plant.py (diff vs base in full +
lines 380-459), GHASSAN/derived.py, GHASSAN/derive_params.py, GHASSAN/data/derived_params.json,
JAD/train.py, GHASSAN/train.py, GHASSAN/evaluate.py, JAD/check_premise.py + the Ghassan diff,
GHASSAN/test_reward.py, JAD/thermal.py, GHASSAN/thermal.py diff vs base, GHASSAN/compare_calibration.py,
ghassan_commits.txt (all 15 messages). Diffs base->jad and base->ghassan of engine_env.py, plant.py,
thermal.py in full.
Read in part: JAD/evaluate.py (90-110, 255-290, all `dt` lines), JAD/test_reward.py (diff vs base),
GHASSAN/knock_margin.py (1-80), GHASSAN/CLAUDE.md (165-195), GHASSAN/NEXT_CHAT_PROMPT.md (40-70),
GHASSAN/SESSION_REPORT_2026-09-28_evening.md (280-296), SESSION_REPORT_2026-09-19.md (255-270,
320-335), REFERENCES.md section 7 (545-575).
Not read: JAD/check_random_road.py, fingerprint.py, the preregistrations (their results are quoted
from JAD/CLAUDE.md only where marked).

## 1. Gearbox

**Ratios are identical and came from Ghassan.** JAD/engine_env.py:325-326 and GHASSAN/engine_env.py:402-403:
final drive 3.150, gears (5.250, 3.360, 2.172, 1.720, 1.316, 1.000, 0.822, 0.640). Introduced by
Ghassan's 5c859f0 (19 Sep 05:50, "env: the real gearbox -- ZF 8HP51"), already in the merge base
f6b46e9, and merged into Jad's branch by 27e720c (19 Sep 07:35, "merge: Ghassan's real gearbox with
sep17's locked scenario and Phase D protocol"). UPSHIFT_MIN_RPM 2000, SHIFT_LOAD 0.75, SHIFT_RPM_MAX
6000, locked converter: same on both.

**The only gearbox difference is the downshift ceiling.**
- Jad (JAD/engine_env.py:412-420): hand back a gear while torque request > 0.75 x 500 = 375 Nm, flat.
- Ghassan (GHASSAN/engine_env.py:453-464, 539-547): > min(375, DELIVERABLE_TORQUE(rpm in that gear)),
  a table measured through the env's own load loop at a 1000 Nm request (derived_params.json).
  So it IS rpm-dependent, but only where the model engine makes < 375 Nm (below ~2200 rpm).

Measured deliverable torque (gearbox_probe.py torque, each branch's own loop, min over steps 15-29):

| rpm | 1600 | 1800 | 2000 | 2200 | 2600 | 2800 | 3000 | 3400 | 4000 | 4400 |
|---|---|---|---|---|---|---|---|---|---|---|
| Jad Nm | 288.5 | 305.9 | 323.4 | 340.9 | 375.0 | 391.3 | 407.0 | 436.0 | 465.5 | 471.5 |
| Ghassan Nm | 249.3 | 271.2 | 316.3 | 375.9 | 413.3 | 427.1 | 442.6 | 463.9 | 475.0 | 480.8 |

(Ghassan's matches his stored table to 0.02 %. Jad's matches the "TORQUE_BEFORE" table typed in
GHASSAN/compare_calibration.py:39-43, i.e. Ghassan's 27-Sep table was measured on Jad's plant.)
The real B58B30O1: 500 Nm at 1800-5000 rpm (Toyota Australia GTP-009045, REFERENCES.md section 7, both
branches). **Both model engines are 4-46 % short of the published curve in that band**, so the model,
not the TCU rule, is the root defect.

Constant grade at 130 km/h, 300 s, dt 1.0, neutral policy (gearbox_probe.py grade):

| grade | Jad: gear, request -> delivered, p95 err, mean r | Ghassan |
|---|---|---|
| 8.0 % | 8th, 332.5 -> 332.6, 0.004, -0.0028 | 8th, 326.5 -> 326.8, 0.004, -0.0012 |
| 9.0 % | **8th, 358.8 -> 332.6, 0.073, -0.362** | 7th, 274.6 -> 274.7, 0.002, -0.0008 |
| 9.3 % | **8th, 366.6 -> 332.6, 0.093, -0.644** | 7th, 280.7 -> 280.9, 0.002, -0.0008 |
| 9.6 % | **8th, 374.5 -> 332.6, 0.112, -0.914** | 7th, 286.8 -> 287.0, 0.002, -0.0008 |

On Jad's physics no policy can meet the torque request on sustained ~8-9.7 % grades at 130 km/h
(the MAP pins at the 186.2 kPa ceiling at 2107 rpm), and the neutral reward is -0.36 to -0.91 per
step instead of ~0: exactly Ghassan's "baseline delivers torque on a 9.3 % grade (was 0.09 before)"
(reproduced: 0.093). Jad's D2/C4 roads never enter the band (0 -> 12-16 % steps), so it did not
touch his experiments; any varied-road experiment on the merged tree would.

**Is Ghassan's rule right?** As a consistency fix for the MODEL, yes: it downshifts exactly when the
modelled engine cannot deliver. As a model of the real 8HP51 TCU, no: the real engine makes 500 Nm
at 2107 rpm, so the real box need not kick down there; Ghassan states the cost himself
(GHASSAN/engine_env.py:438-442: "one gear lower and about 600 rpm faster than the real car would
need to"). Below ~2200 rpm his rule keeps NO reserve (min() hands the gear back only at the ceiling)
while above it keeps 25 %: inconsistent, harmless on the roads used.

**The D2 notch moves.** Analytic gear by grade at 130 km/h (gearbox_probe.py demand): the 7th->6th
shift is at 13.73 % on Jad's physics and between 13.80 and 13.97 % on Ghassan's (drag is 7 % lower).
Peak turbine, neutral, dt 1.0, climb from 180 s: Jad 13.70 % 925.2 C (+75.2 K), **13.73 % 856.8 C
(+6.8 K, reproduces check_random_road's +6.9 K)**, 16 % 902.9 C; Ghassan 13.96 % 930.4 C (+80.4 K),
**14.00 % 862.3 C (+12.3 K)**, 16 % 902.6 C. So D2's 12-16 % range still binds everywhere tested on
Ghassan's physics. Damage across the notch jumps 2352 -> 546 (Jad, 13.70 -> 13.73 %) and 2618 ->
595 (Ghassan, 13.96 -> 14.00 %): the notch is an ASSUMED-parameter (SHIFT_LOAD) cliff on both.

**C9 -- confirmed.** Ghassan's files say Jad's branch has the old six-speed:
- GHASSAN/CLAUDE.md:181 "Resolve code toward this branch; `sep17`'s `engine_env.py` still has the six-speed box."
- GHASSAN/NEXT_CHAT_PROMPT.md:54 "Resolve code toward THIS branch -- sep17's engine_env.py has the six-speed gearbox."
- GHASSAN/SESSION_REPORT_2026-09-28_evening.md:290 "`sep17`'s `engine_env.py` still carries the six-speed gearbox."
All three were written in cbb8d09 (29 Sep 09:44), ten days after 27e720c put Ghassan's own ZF ratios
on Jad's branch. How the error arose is UNVERIFIED (a stale local ref, or the six-speed history in
Jad's make_grade_climb docstring, are both possible).

Semantic conflict to resolve in the merge (docstrings, not code): Jad's make_grade_climb says the
real box runs hotter because it is TALLER than the invented six-speed in 5th (2.788 overall, 2913
rpm; JAD/engine_env.py:864-882); Ghassan's says the real box runs hotter because it is LOWER than the
invented six-speed in top (2.312; GHASSAN/engine_env.py:1016-1019, SESSION_REPORT_2026-09-19.md:260,
328). Both are true against different six-speeds (Jad's had mistake 17's load guard, Ghassan's did
not). Also JAD/engine_env.py:874 calls 96.4 kW "at the wheels"; it is engine power (340.2 Nm x 2706
rpm); wheel power is 88.7 kW.

## 2. Roads

- Jad D2/C4 (JAD/random_road.py:84-114): flat, then an instantaneous step to U[12,16] % at U[120,300] s,
  130 km/h, 42 C. Every road binds by design (minimum margin +6.8 K at the notch). Tests whether
  preview of ONE climb's onset and steepness helps, with the blind arm verified blind.
- Ghassan (GHASSAN/engine_env.py:1077-1199): per episode one of locked 15 % (the scored road itself),
  single 30 % (4-14 %), rolling 25 % (-3 to +10 %), double 20 % (two 6-14 % climbs), flat 10 %; grade
  changes ramped over 4-12 s; 130 km/h and 42 C fixed. I regenerated all 550 training roads of the
  20 retrained agents (10 seeds x 55 episodes; sighted and blinded of a seed share roads) from
  make_terrain and the road stream: the family sequence matches each agent's curve.csv exactly;
  163 of 550 episodes reach >= 12 %, 94 stay below 6 %; seed 2 saw no flat road (roads_regen.py).
  His 40-road check: 14 bind (results/training_roads.json). Evaluation is only the locked climb.

Which is more realistic: Ghassan's training roads, in shape -- ramped transitions (a vertical curve,
not a step), descents, several climbs, and roads where protection only costs fuel. Jad's evaluation
is the more rigorous ablation (randomised, blind arm verified, preregistered), but every one of its
roads is a step, and a step is where the one-sample knock artifact lives (section 3).

Where realism is impossible, measured: realistic grade-speed pairs do not bind on either physics --
Jad's physics 6 % at 90 km/h peaks 539.2 C, 12 % at 90 km/h 716.7 C (my runs); Ghassan's sweep 546.1 /
720.5 C (results/sweep_speed_grade.json); the car's own Taif drive, replayed, 797.6 C, 52 K short
(JAD/CLAUDE.md). A binding climb at 130 km/h rises 2340 m in the 720-s episode (3120 m in 900 s,
terrain_time.py) at sea-level pressure (p_baro fixed at 101.3 on both). Descents: neither model has
overrun/fuel cut; at 130 km/h -5 % asks -11.5 Nm (Jad) / -17.5 Nm (Ghassan), the engine floors at
~10 Nm, p95 error 0.55 / 0.69, neutral reward -7.2 / -9.1 per step -- which is why Ghassan stops at
-3 %. So both branches must use roads that do not exist; the question is only which unreal road.

## 3. Time step

- Jad: trains at dt 0.2 (JAD/train.py:177 builds SupervisoryTunerEnv(make_grade_climb(...)) with no dt;
  defaults 0.2 at JAD/engine_env.py:524, 834), scores at 1.0 (JAD/evaluate.py:98; :266 "train 0.2,
  score 1.0").
- Ghassan: trains at 1.0 (GHASSAN/train.py:93, :263; every results/agents/terrain_dt1/*/config.json
  "dt": 1.0, 900 steps/episode) and scores at 1.0 (GHASSAN/evaluate.py:60). His 19-Sep agents
  trained at 0.2 (a50d22c).
- **Sidestepped, not fixed.** The PI loop is unchanged (GHASSAN/engine_env.py:725-745 == JAD:589-637
  minus Jad's comment): 3 iterations per step, integrator +0.05 x error per iteration, no dt. Two
  more per-step constructs are identical on both: knock-retard pull +3 deg per knocking STEP
  (JAD:253, GHASSAN:330) and the one-step-lagged spark schedule on map_b_prev (JAD:756-762,
  GHASSAN:867-873).

Locked climb, 720 s, damage by term (trace.py; totals reproduce check_premise exactly at dt 1.0):

| branch, policy | dt | total | turbine | oil | knock | knock at 180-186 s |
|---|---|---|---|---|---|---|
| Jad baseline (neutral) | 1.0 | 959.8 | 862.3 | 28.2 | 69.3 | 66.3 |
| Jad baseline | 0.2 | 900.9 | 858.9 | 28.2 | 13.9 | 13.3 |
| Jad baseline | 2.0 | 1034.9 | 866.1 | 28.2 | 140.7 | 132.7 |
| Jad current-grade | 1.0 | 633.2 | 523.8 | 31.8 | 77.5 | 74.5 |
| Jad current-grade | 0.2 | 567.8 | 521.8 | 31.8 | 14.2 | 13.6 |
| Ghassan baseline | 1.0 | 920.1 | 851.0 | 8.5 | 60.6 | 58.6 |
| Ghassan baseline | 0.2 | 868.5 | 847.8 | 8.6 | 12.1 | 11.7 |
| Ghassan baseline | 2.0 | 971.3 | 842.3 | 7.4 | 121.6 | 117.3 |
| Ghassan current-grade | 1.0 | 520.5 | 445.1 | 8.7 | 66.8 | 64.9 |
| Ghassan current-grade | 0.2 | 464.5 | 443.4 | 8.7 | 12.4 | 12.0 |

- dt 1.0 -> 0.2 moves baseline damage -58.9 (Jad), of which -55.4 is knock; -51.6 (Ghassan), of which
  -48.5 is knock. Turbine-only cuts are dt-invariant to 0.15 points (Jad current-grade 39.25 % at both
  steps; Ghassan 47.70 % at both). Peak turbine is dt-invariant (884.0 / 883.0 C).
- The spike, traced (Jad, neutral, dt 1.0): t=179 MAP 67.6 kPa spark 20.15; t=180 grade 12 %, gear
  8->7, rpm 2107->2706, spark 23.99 deg (scheduled on 67.6 kPa) at MAP 144.7 kPa, KI 2.14; t=181
  knock pull 3 deg, spark 3.12 at 172.6 kPa, KI 0.69. Ghassan: 23.77 deg at 143.1 kPa, KI 2.06.
- Ramped over 8 s instead: knock 3.5 (Jad) / 2.4 (Ghassan), max KI 1.05 / 1.04, total 891.9 / 858.6,
  peaks unchanged; preview over current-grade -0.06 / -0.01 points.
- D2 grades, neutral, dt 1.0: spike 34.3-101.7 units (Jad), 35.4-96.6 (Ghassan) per episode.
  So an agent trained at 0.2 sees one-fifth of the spike it is scored on at 1.0.
- Coolant numerics (euler_stability.py, perturbation of the block node at the climb steady state):
  Ghassan factor +0.64 (dt 0.2), +0.11 (0.5), -0.78 (1.0), -1.67 (1.5), -2.56 (2.0); Jad +0.97 ..
  +0.67. In the dt 1.0 episode Ghassan's coolant step changes alternate sign 28 times in 0-60 s and
  31 times in 180-260 s (Jad's: 2 and 2), then settle (93.05 C); at dt 2.0 it never settles: 86.8-95.4 C, 8.26 K
  steps, 121 of 157 alternating in 400-720 s, thermostat 0.00-1.00. generality_test.py runs at dt
  2.0 on both branches (GHASSAN/generality_test.py:93, 114), so Ghassan's H/tau sweep ran on an
  oscillating coolant node (effect on the turbine small but unmeasured; the node feeds charge
  temperature and the fan schedule).

## 4. The BaselineECU spark offset refit (0d8e6ca)

spark_check.py, each branch's BaselineECU against its own data/master_points.csv (26 points, 30-75
kPa, 1549-5053 rpm): Jad SPARK_A 26.18 -> line a median +9.55 deg above the knock limit, sets spark
at 0 of 26, commanded spark biased +3.16 deg (RMS 4.00) vs the car's logged spark. Ghassan 13.42 ->
line sets spark at 25 of 26, bias +0.00, RMS 2.50. Ghassan's claims reproduced exactly.
Physically right in intent: the compensation input changed definition (mistake 13) and the constant
did not; the refit ties part-load spark to the car's own spark instead of the unvalidated
Douaud-Eyzat surface. Effect measured in the episode: cruise (2107 rpm, 66-68 kPa) spark 20.14 ->
19.60 deg, KI 0.64 -> 0.59; climb unchanged in kind -- knock-limited on both (0.69 vs 1.16 deg, the
difference is MAP 178.2 vs 174.9 kPa, not the refit), KI 0.61 on both; the spike-step spark 23.99 ->
23.77 deg. Caveats: slopes held from 7 Sep; points only 30-75 kPa; the climb and all boost remain on
the knock model; "logged spark" is `Actual ignition angle`, itself questioned in CLAUDE.md.
Note for C11-C13 (another agent's scope): at the climb the baseline sits at KI 0.61 on both branches,
leaving headroom to the 0.85 damage knee -- the headroom knock_margin.py says the agents use.

## 5. Boost ceiling

- Jad/base (JAD/plant.py:432, 454-456): PR = 1 + 14.5023 m / (1 + 6.4019 m), cap 2.6, and the env
  evaluates it at the CHARGE temperature (JAD/engine_env.py:633-634) although plant.py:448-452 says
  the inlet is ambient; effective MAP cap 250 kPa (JAD/engine_env.py:570).
- Ghassan (GHASSAN/plant.py:399-449): running maximum of the binned p95, linear interpolation, cap
  2.5155 (= the single highest stable reading), evaluated at ambient (GHASSAN/engine_env.py:742-743).

Against drive B's 89 genuine full-throttle readings (Ghassan's results/calibration_comparison.json;
the model side measured by me; ceiling_vs_driveB.py): readings ABOVE the model's ceiling -- which a
true ceiling cannot have -- Jad 41/89, Ghassan 17/89; in 2000-3400 rpm (8th/7th/6th at 130 km/h run
2107/2706/3292) Jad 36/57, Ghassan 5/57. Mean |model / band max - 1|: Jad 8.7 %, Ghassan 5.7 %. By
band: 1400-1600 Jad +26.3 % / Ghassan +4.3 %; 1800-2000 -8.0 / -16.0 %; 2200-2400 -15.7 / -3.6 %;
2600-2800 -11.3 / -0.7 %; 3000-3200 -2.6 / +7.0 %. (Drive B is fully independent of Jad's 8-Sep fit;
its quasi-steady rows are inside Ghassan's envelope data, so his agreement is partly by construction.)
Robustness: the top two bins rest on 8 and 5 independent readings and both caps are one reading
(derived_params.json bins); a running maximum lets one high reading in a thin bin lift every flow
above it, a 2-parameter fit cannot follow the 0.075-0.105 kg/s jump (RMS 0.128 vs 0.013 in PR).
Where it matters: not on the locked climb (MAP 178.2 vs ceiling 198.8 kPa Jad; 174.9 vs 216.5
Ghassan), but in the 8th-gear band of section 1, in the kickdown table, and in the boost-trim lever:
the starver (boost trim -40 kPa) cuts damage to 363.8 on Jad's climb (peak 839.4 C) but only to
866.2 on Ghassan's (peak 883.1 C), which is why test_reward's starver reads -0.90 vs -0.13.

## 6. Other environment physics

- Exhaust flow: JAD/engine_env.py:764, 778 fuel x 15; GHASSAN/engine_env.py:880, 894 air + fuel. The plant
  makes air/fuel = 14.7 lambda exactly (plant.py:196), so fuel x 15 is 4.5 % low at lambda 1 and 16 %
  high at 0.81, and it grows with enrichment -- it partly cancels the enrichment lever. Ghassan's
  record (compare_calibration.py:52-69, PREMISE_STEPS, a record I did not regenerate): +5 K peak,
  baseline 927.3 -> 1052.1.
- Air density: JAD:425 1.2; GHASSAN:556, 843 p/(287 T) = 1.1205 at 42 C. Request on the climb 340.2 ->
  335.5 Nm; same record: -6 K peak, 1052.1 -> 920.1. **The 884 vs 883 C agreement of C10 is these two
  corrections cancelling**, not the simulators agreeing (current-grade cut 34.0 % vs 43.4 %).
- Enrichment dwell 1.5/3.0 s vs 2/9 s: never active in either experiment (lambda 1.00 at the climb,
  2706 rpm < 3300; 6th at 130 km/h is 3292 rpm).
- Fan/pump and neutral_action: identical code. Jad's docstring corrected (fan 0.4 on 97.4 % of the
  climb); Ghassan's still says "exactly neutral during the climb" (GHASSAN/engine_env.py:1239-1242),
  false on his physics too: his baseline fan is 0.0 for the whole episode (coolant 93.05 < 93.85 C).
  Neutral vs baseline arm: 959.8 vs 964.1 (Jad), 920.1 vs 921.3 (Ghassan).

## 7. Time for the plan

This machine: AMD Ryzen 5 9600X, 6 cores / 12 threads. My runs shared it with 34-63 other Python
processes at 100 % load, so CPU time is the comparable figure:
- one 720-s locked-climb episode, dt 1.0, baseline: CPU 63.5 s (Jad), 64.0 s (Ghassan), ~88 ms/step;
  wall 1021-1039 s under that load, 87-96 s at the lighter load of the ramp runs; the orchestrator's
  unmodified check_premise (5 episodes) took 227 / 229 s, ~45 s per episode. Same cost on both branches.
- dt 0.2: CPU 313-317 s (5x). dt 2.0: CPU 31.3 s.
- one of Ghassan's training roads (900 s, dt 1.0, 899 steps, neutral): CPU 78.0-80.0 s for all five
  families (87-89 ms/step), 1.25x the 720-s episode.
- P3 arithmetic (estimate, not measured): 20 agents x 20 roads x ~900 steps x ~63 ms = ~6.3 CPU-h, plus
  ~15 % for the three comparators, i.e. roughly 1-1.5 h on 6 physical cores unloaded. "1-2 hours" is
  consistent with 10-20 roads per agent, not with 40+.

## Co-work claims checked

- C5 CONFIRMED for Ghassan's 29-Sep retrain (train 1.0, test 1.0) and Jad's D2/C4 (train 0.2, test 1.0).
  Not a fix: the per-step loops remain; and dt 1.0 is where the knock spike is 5x its dt 0.2 size.
- C6 CONFIRMED: locked/single/rolling/double/flat, weights 0.15/0.30/0.25/0.20/0.10, 550 roads
  regenerated and matched; "up-and-down" = rolling -3..+10 %; the locked scored road is 14 % of training.
- C9 CONFIRMED: three sentences quoted above; Jad's branch has had the ZF since 27e720c.
- C10 CONFIRMED: 884.0 vs 883.0 C; preview over current-grade -0.44 / -0.32 points; on turbine-only
  damage +0.01 / +0.04 points; the whole gap is one step's knock sample (74.5 vs 78.7 units Jad;
  64.9 vs 68.1 Ghassan). The equal peaks come from two opposite corrections cancelling.

## Recommendations for the merge

1. Take Ghassan's exhaust flow, air density, ceiling-at-ambient and spark offset; take his kickdown
   table or, better, fix the low-flow boost ceiling so the flat 375 Nm rule is consistent with the engine.
2. Do not take Ghassan's thermal constants without an integration fix: sub-step the thermal network
   (e.g. 0.1 s inside each env step) or use an implicit update, and re-run generality_test.py.
3. Remove the knock artifact before any new ablation: ramp every grade change (Ghassan's _smooth_steps
   exists) including the locked climb and D2, or schedule the ECU on the current step's pressure /
   sub-step it. Changing the locked scenario is a team decision and a new preregistration.
4. Pick one dt for train and eval (Ghassan's rule), and report turbine-only damage beside total damage.
5. Fix the docstrings: C9's three sentences, the two "why the real box runs hotter" explanations, the
   neutral_action fan caveat (Ghassan), "96.4 kW at the wheels" (Jad).

## Runs

All exit 0 unless stated; CPU/wall per run.
- gearbox_probe.py {jad,ghassan} demand: <5 s each; gear/torque/rpm by grade (section 1).
- gearbox_probe.py {jad,ghassan} grade {0.08,0.09,0.093,0.096,-0.04,-0.05}: 300-s episodes; table in section 1/2.
- gearbox_probe.py {jad,ghassan} torque: CPU 38.8 / 38.4 s; deliverable torque tables.
- trace.py {jad,ghassan} {neutral,grade_now,reactive,predictive,starver} 1.0 720: CPU 62.7-64.0 s, wall 1021-1039 s.
- trace.py {jad,ghassan} {neutral,grade_now,reactive,predictive} 0.2 720: CPU 312.5-317.0 s, wall 3596-3654 s.
- trace.py {jad,ghassan} neutral 2.0 720: CPU 31.3 s, wall 407-409 s.
- trace.py notch sweep (Jad 13.70/13.73/13.80/16.00 %, Ghassan 13.80/13.90/13.96/14.00/16.00 %): CPU ~63 s each.
- trace.py Jad 6 % and 12 % at 90 km/h: 539.2 / 716.7 C.
- trace.py 8-s ramp, both x neutral/current-grade/predictive: CPU 61.7-62.9 s, wall 87-96 s.
- terrain_time.py ghassan {locked,single,rolling,double,flat} seed 11: CPU 78.0-80.0 s, wall 1204-1209 s.
- euler_stability.py jad / ghassan; ceiling_vs_driveB.py; roads_regen.py; spark_check.py jad / ghassan; analyse.py.
- Lost work, stated: the first trace.py resolved its output path after chdir, so two dt 1.0 runs
  finished without writing and eight dt 0.2 runs were killed and relaunched; a smoke test failed on
  numpy float serialisation and was fixed before any kept run.
Outputs: scratchpad/work/physics-vehicle-env/out/*.json and *.log.
