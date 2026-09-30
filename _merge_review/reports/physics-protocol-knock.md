# physics-protocol-knock -- Ghassan's terrain_dt1 experiment, the knock-margin finding, against Jad's preregistered method

Label: physics-protocol-knock. Written 30 Sep 2026 (00:xx AST) by a workflow subagent.
Nothing in MERGE or in the main repository was modified. Every run below was made in
`scratchpad/work/physics-protocol-knock/` on copies of the trees (and on copies of four
C4 `final.zip` files read from the main repo's gitignored `runs_c4/`).

## 0. Bottom line

1. **Protocol.** Ghassan's design (arms, 50 000 steps, varied training roads, dt 1.0, the
   twenty frozen Phase-D episodes on the locked climb, pairing by seed, three rows, damage two
   ways) WAS written in committed documents before training (`cbb8d09`, 29 Sep 09:44; training
   started 11:55:45). What was NOT written before training: a hypothesis direction, alpha,
   sidedness, an MEI, a decision rule, a stopping rule -- and the seed count that ran (10) is not
   the count the committed plan named (5). Co-work C7 is therefore PARTLY right.
2. **Test set.** Every evaluation episode is the one locked road: flat, then an instantaneous
   step to 12 % at t = 180 s (`engine_env.py:1043`). That road is itself one of the five training
   families (the "locked" family, weight 0.15, `engine_env.py:1080,1122-1123`; 156 of 1100
   training episodes = 14.2 %, 5-11 per agent). No rolling or two-climb road is ever scored. C8
   is CONFIRMED.
3. **Preview, recomputed with Jad's statistics (MEI 50).** blind - sighted median damage,
   6 of 10 positive, mean +10.76, median +16.50, sd 72.14; sign p 0.3770, permutation p 0.3154;
   effect < 50: sign p 0.1719 (7 of 10 below), permutation 0.0547 -> **INCONCLUSIVE** (not
   "no effect"). Power of the n = 10 sign test against 50 units at this spread: 0.26; 23 seeds
   would be needed for 80 %.
4. **A new finding: the only consistent preview effect in this experiment is a model artefact
   in the knock term.** On the knock term alone the sighted agent takes less damage than its
   blind twin in 10 of 10 seeds (mean 21.7 units, sign p 0.0010, permutation p 0.0010). On
   thermal-only damage the sighted agents are slightly WORSE (mean -12.9 units, 4 of 10). The
   knock term is ~97 % one step: at t = 180 s the baseline ECU still commands part-load spark
   (it schedules spark on the previous second's MAP, `engine_env.py:867-874`) while the load
   jumps, KI = 2.06-2.16 for that one step. Traced: sighted seed 2 sees the step coming and
   retards spark at the slew limit from t = 175 s (trim -2.2 -> -7.9 deg), cutting that step's
   knock damage from 68.6 (its blind twin) to 11.5. Real grade changes are ramps, real ECUs
   schedule spark per cycle, and the knock model is unvalidated: this "preview benefit" would not
   exist on the car.
5. **Supervision.** As trained, 10 of 10 sighted and 10 of 10 blinded agents beat current-grade
   on median damage (+10.3 to +34.6 and +5.6 to +35.9 points). knock_margin.py's figures
   (+24.4 -> -1.8 points median margin; 9 of 20 still beat current-grade with spark advance
   forbidden) are CONFIRMED -- recomputed from `knock_margin.json`, and spot-re-run: 8 episodes
   reproduce the published damage to <= 0.05 % from the committed `policy.npz` alone. C12 and
   C15 CONFIRMED.
6. **Knock physics.** Every agent pins the spark trim at its +4 deg action bound on the climb
   (median 3.46-3.98). The bound, not the knee, stops them: at held torque the model's KI reaches
   the 0.85 damage knee only at 6.9 deg spark and the 1.0 knock flag at 10.0 deg, while the
   baseline runs ~0.8-1.2 deg (knock-limit surface 5.90 deg minus 5.12 deg IAT compensation).
   The benefit is physically real in DIRECTION (at held torque +4 deg: EGT -28 K, fuel -5.1 %),
   but whether the car has that margin is unsupported: in the car's own boosted logs the actual
   spark runs 3-8 deg BELOW what BaselineECU would command at the same rpm/MAP/ambient (few
   readings). A constant +4 deg trim alone, nothing else, takes the locked-climb damage from
   920.1 to 572.3 at 4.9 % LESS fuel -- about what the whole current-grade policy buys (520.5 at
   5.9 % MORE fuel), and more on thermal damage.
7. **Jad's agents do it too (C13, checked).** Two C4 agents (sighted/blind seed 0) on two D2
   episodes: spark trim on the climb +3.2 to +3.98 deg, KI p95 0.755-0.831; capping the trim at 0
   raises damage by 33-68 % (e.g. sighted ep 0: 501.7 -> 832.7; blind ep 0: 1222.9 -> 2053.1).
8. **C14 is overstated.** Neither branch shows a preview effect, but "firm" is wrong: Ghassan's
   is INCONCLUSIVE at power 0.26; Jad's D and D2 are INCONCLUSIVE; only C4's primary sign test
   says "smaller than the MEI", on a 7-of-8 threshold, with the permutation test disagreeing and
   the agents not converged. And the two "methods" share the knock model, the damage function,
   the twenty preference vectors, SAC settings, single-climb step roads and the grade-step spike.

## 1. What was read, and what was run

Read in full: GHASSAN `results/agents/terrain_dt1/README.md`, `KNOCK_MARGIN.md`,
`results/agents/README.md`, `train_all.py`, `train.py`, `evaluate.py`, `knock_margin.py`,
`record_agents.py`, `run_results.py`, `engine_env.py` (1279 lines), `check_map.py`,
`SESSION_REPORT_2026-09-29.md`, `NEXT_CHAT_PROMPT.md`, `logs/DRIVE_PLAN.md`,
`results/phase_d_130kmh.txt`; `plant.py` lines 80-379 (cycle, knock integral) -- the rest of
plant.py differs from Jad's only in the boost ceiling (`diff`); the 15 commit messages;
CLAUDE.md lines 1-300 and 1655-1714; REFERENCES.md 240-280; the relevant blocks of
`logs/CHANNEL_CENSUS.md`. JAD: `results/PREREGISTRATION.md`, `_D2.md`, `_C4.md` (all in full),
`analyse_phase_d.py`, `analyse_phase_d2.py`, `analyse_c4.py`, `evaluate.py` (all in full),
`power_analysis.py` 1-200, `random_road.climb`, the knock/exhaust/gear lines of `engine_env.py`,
AUDIT2.md Part 6. Parsed completely by script (not read by eye): every `eval_summary.json`,
`config.json`, `curve.csv`, `index.json`, `knock_margin.json`, `phase_d_130kmh_raw.json`,
`traces_130kmh.json`, `data/master_samples.csv`. Not read: the rest of Ghassan's CLAUDE.md
(~1800 lines, outside this topic), PNG figures (not viewed), npz files other than policy.npz.

Scripts (all in `scratchpad/work/physics-protocol-knock/`, outputs beside them as `*.out`):

| script | what | runtime |
|---|---|---|
| `recompute_stats.py` | Jad's sign/permutation/MEI rule on Ghassan's eval_summary.json; supervision; the cap | < 5 s |
| `knock_term_split.py` | damage - damage_thermal per arm and seed | < 2 s |
| `spot_knock_margin.py` | actor rebuilt from policy.npz; evaluate.run_episode unchanged; as trained and capped | 8 x 170-218 s |
| `step_spike_trace.py` | per-step trim/spark/KI around t = 180 s | 2 x ~4 min |
| `knock_probe.py` | A: constant spark trim on the locked climb; B: static spark sweep at the climb point | A 6-9 min/episode under load; B ~1 min |
| `car_spark_at_climb.py` | car's logged spark in boost vs BaselineECU at the same conditions | ~1 min |
| `jad_c4_spark.py`, `jad_d2_handwritten.py` | two C4 agents and the hand policies on two D2 episodes | 130-190 s/episode |

The first `knock_probe.py` launch (all trims in one process) was killed by my own
`timeout 3000` before finishing (the machine was shared by other agents); its partial Jad-tree
rows are kept in `knock_probe_jad_partial_killed_by_timeout.out` and it was relaunched one trim
per process.

## 2. Protocol, side by side

| | Jad Phase D | Jad D2 | Jad C4 | Ghassan terrain_dt1 |
|---|---|---|---|---|
| arms | sighted / blind (`--no-preview`) | same | same | same (`train_all.py:39,50-51`) |
| seeds | 0-7 | 0-7 | 0-7 (D2's, continued) | 0-9 (`train_all.py:33`) |
| pairing | by seed | by seed | by seed | by seed; sighted and blind of a seed see the SAME road sequence (curve.csv road counts identical per seed) |
| training roads | fixed climb (12 % at 180 s) | random single step, start 120-300 s, 12-16 % | = D2 | five families: locked 0.15, single 4-14 % 0.30, rolling 0.25, double 0.20, flat 0.10; ramps 4-12 s except "locked" (`engine_env.py:1077-1163`) |
| training dt | 0.2 | 0.2 | 0.2 | 1.0 (`train.py:263`) |
| steps | 50 000 = 11 episodes | 50 000 = 11 | 300 000 = 66 | 50 000 = 55 episodes (config.json) |
| eval roads | locked climb | `EPISODES_D2`: 20 frozen random single steps (Latin hypercube) | `EPISODES_D2` | locked climb only (`evaluate.py:126-127`) |
| eval episodes | 20 frozen (seed, weights) | Phase D's 20 seeds/weights + roads | = D2 | Phase D's 20 (`evaluate.py:65-86`, identical literals) |
| eval dt / length | 1.0 / 720 s | 1.0 / 720 s | 1.0 / 720 s | 1.0 / 720 s |
| primary statistic | per-seed median damage, blind - sighted, exact one-sided sign test, permutation beside it, alpha 0.05 | + MEI 50, three cells | + convergence rule, budget-change test | paired t (two-sided) and exact two-sided Wilcoxon on cut-% differences; 95 % CI (`record_agents.py:166-192`, `run_results.py:130-141`) |
| written before training? | yes, committed before seed 0 (MEI set after the result, labelled) | yes, incl. MEI and cells | yes (`79568e2`) incl. readings of every outcome | design yes (cbb8d09: CLAUDE.md "What to do next" 3-8, handoff Steps 3-4, NEXT_CHAT_PROMPT 3-4; paired t + Wilcoxon already in `run_results.py` at cbb8d09 for `range(5)`); NOT written: hypothesis direction, alpha, sidedness, MEI, decision rule, stopping rule; seeds written as 5, run as 10 |
| provenance | fingerprint + meta.json, evaluate.py refuses a mismatch | same | + zip budget certificate | config.json: `git_commit cbb8d09`, `git_dirty true`, data_sha1 `c4fdd4babfb3752a` (= committed derived_params.json); no fingerprint check in evaluate.py |

Timeline evidence (from the 20 `config.json`): every run `started` 2026-09-29T11:55:45-46,
`finished` 15:44-15:49, `resumed_from` null, 55 episodes, 50 000 steps, torch 2.14.0+cpu.
`cbb8d09` 09:44:30; results and the 10-seed rationale (`train.py:38-41`) committed in `74de99a`
20:07:57. So the 5 -> 10 change was made before training (all 20 started together) but committed
only with the results.

Is the evaluation set drawn from the training distribution? It is ONE member of it (an atom with
14.2 % of training episodes), not a draw from it: one climb, one start time, one grade, and the
only road in training with an instantaneous grade step. The blind arm is still blind at
evaluation in the D2 sense: before t = 180 s the locked road is indistinguishable from a single
or double climb that starts later (all are flat at 130 km/h from 30 s), so the blind agent can
hold a prior, not a preview.

## 3. Results, recomputed (`recompute_stats.out`)

Cross-check first: `eval_summary.json` (record_agents.py) against `phase_d_130kmh_raw.json`
(run_results.py): 1920 values (480 episodes x damage, thermal, fuel, peak), **0 differ**. (The
terrain_dt1 README's line "0 episodes were compared ... and are identical" is a vacuous count;
the two scoring paths do agree.)

Baseline median damage 920.07 (thermal 859.51); current-grade 520.55 (453.71). One point of
"cut" = 9.20 damage units, so **MEI 50 = 5.43 points** here (Jad: 5.21 % of 959.8, 4.47 % of
1118.0).

| seed | sighted | blinded | blind - sighted | thermal diff | knock-term diff |
|---|---|---|---|---|---|
| 0 | 387.1 | 443.8 | +56.7 | +53.6 | +4.35 |
| 1 | 426.0 | 469.0 | +43.0 | +17.8 | +16.29 |
| 2 | 280.0 | 414.7 | +134.7 | +83.1 | +50.02 |
| 3 | 284.2 | 227.6 | -56.6 | -76.1 | +16.61 |
| 4 | 307.0 | 364.1 | +57.1 | +13.7 | +43.35 |
| 5 | 362.6 | 230.9 | -131.7 | -157.4 | +24.72 |
| 6 | 270.1 | 253.1 | -17.0 | -33.2 | +9.53 |
| 7 | 257.3 | 272.1 | +14.8 | -7.3 | +23.45 |
| 8 | 368.6 | 386.8 | +18.2 | -3.1 | +20.44 |
| 9 | 201.8 | 190.2 | -11.6 | -20.1 | +8.45 |

(Medians over the twenty episodes; the thermal and knock-term columns are differences of
per-arm medians and need not add to the total.)

| test (Jad's functions, copied unchanged) | total damage | thermal-only | knock term | spark capped |
|---|---|---|---|---|
| positive / n | 6 / 10 | 4 / 10 | **10 / 10** | 5 / 10 |
| mean diff | +10.76 | -12.91 | **+21.72** | -8.70 |
| sd | 72.14 | 67.29 | | 163.99 |
| sign p (preview helps) | 0.3770 | 0.8281 | **0.0010** | 0.6230 |
| permutation p | 0.3154 | 0.7100 | **0.0010** | 0.5693 |
| sign p (effect < 50) | 0.1719 (7 of 10) | 0.0547 (8 of 10) | | 0.1719 |
| permutation p (effect < 50) | 0.0547 | 0.0068 (disagrees) | | 0.1523 |
| cell | **INCONCLUSIVE** | INCONCLUSIVE (sign primary; perm disagrees) | -- | INCONCLUSIVE |
| sign-test power vs 50 | 0.258 | 0.295 | | 0.060 |
| effect with 80 % power | 99.8 | 93.1 | | 226.9 |

Seeds 0-7 only (Jad's count): 5 of 8, mean +12.6, INCONCLUSIVE. MEI at 5.21 % of this baseline
(47.9): still INCONCLUSIVE. At n = 10 the sign test needs 9 of 10 (p 0.0107); 8 of 10 gives
0.0547. Ghassan's own figures reproduce: mean +1.169 points (= +10.76 units x 100/920.07), paired
t p 0.6484, exact two-sided Wilcoxon p 0.4316 (one-sided 0.2158).

Supervision (median damage vs current-grade): sighted 10 of 10 (+14.5 +10.3 +26.1 +25.7 +23.2
+17.2 +27.2 +28.6 +16.5 +34.6 points), blinded 10 of 10 (+8.3 to +35.9), sign p 0.0010 each.
Worst episode above current-grade's (single-rollout) 520.5: 3 of 10 sighted, 5 of 10 blinded
(blind seed 6: 2526.7). Under the cap: margin median +24.45 -> -1.78, 9 of 20 still beat
current-grade (sign p 0.748), share of the as-trained margin lost median 1.07; capped thermal-only
cut 40.2 % (sighted) / 40.3 % (blinded) against current-grade's 47.2 %.

## 4. The knock finding

### 4a. Why the agents advance spark

- Action space: spark trim in [-8, +4] deg, slew 1.5 deg/s (`engine_env.py:644-646`; identical on
  Jad's branch `engine_env.py:513-515`). The agent's spark is the baseline's plus the trim
  (`engine_env.py:887-888`; Jad `:771`).
- Nothing on the agent path answers knock: the ECU's knock retard is driven by the BASELINE'S own
  KI (`knock_flag_base = base["ki"] > 1.0`, `engine_env.py:874`; Jad `:763`); the agent's
  `c_knock` is bookkeeping only (`:919`). The only price of advance is the damage term
  `40*max(0, KI-0.85)^2` (`:641`), which is zero below KI 0.85.
- BaselineECU on the climb: `knock_limited_spark` surface (fitted to the plant at IAT 55 C,
  `engine_env.py:139-146`) gives 5.90 deg at 2706 rpm / 177.5 kPa; the IAT compensation
  (`:320-323`) subtracts 5.12 deg at a 57 C charge -> 0.78 deg (1.16 deg in the env's climb,
  committed engine stats; KI p95 0.614).
- The plant's own limits at that point (`kpB_ghassan.out`; plant.run_cycle is identical on both
  branches): KI 0.85 at 5.28 deg (fixed MAP) / 6.91 deg (torque held); KI 1.0 at 7.57 / 9.99 deg.
  So the baseline keeps ~6-9 deg of margin to the model's knock flag; the agents take +3.5-4.0 of
  it and stop at the ACTION BOUND (median trims 3.46-3.98, KI p95 0.767-0.789; every agent,
  committed `engine_on_climb`). "Just under the knee" is numerically true but the knee is not
  what stops them.
- What +1 deg buys at held torque: EGT -7 K, fuel -1.3 to -1.4 %, MAP -2.3 kPa. 1 -> 5 deg: EGT
  1025.1 -> 997.1 C, fuel 7.833 -> 7.430 g/s. Direction physically right (retarded, knock-limited
  spark is exactly why turbo engines run hot EGT under load).
- Constant trim, everything else neutral, locked climb, 720 s, dt 1.0 (Part A, `kpA_*.out`):

  | trim | spark on climb | KI p95 | EGT C | turbine C (late) | damage (turbine / oil / knock) | fuel |
  |---|---|---|---|---|---|---|
  | 0 (Ghassan tree) | 1.16 | 0.614 | 1022.1 | 883.0 | 920.1 (851.0 / 8.5 / 60.6) | 4572.7 |
  | +2 | 3.16 | 0.683 | 1008.0 | 867.7 | 702.0 (602.4 / 8.5 / 91.1) | 4457.0 |
  | **+4** | 5.16 | 0.758 | 994.1 | 852.7 | **572.3 (429.3 / 8.4 / 134.6)** | 4350.3 |
  | +6 | 7.16 | 0.841 | 980.2 | 838.0 | 512.1 (308.4 / 8.4 / 195.3) | 4252.7 |
  | +8 | 9.16 | 0.934 | 966.6 | 823.7 | 673.6 (223.7 / 8.4 / 441.5) | 4163.9 |
  | 0 (Jad tree) | 0.68 | 0.610 | 1027.2 | 884.0 | 959.8 (862.3 / 28.2 / 69.3) | 4663.5 |
  | +4 (Jad tree) | 4.68 | 0.754 | 999.0 | 853.5 | 607.0 (432.9 / 25.5 / 148.6) | 4434.8 |
  | +8 (Jad tree) | 8.68 | 0.928 | 971.4 | 824.3 | 781.6 (224.4 / 23.4 / 533.8) | 4242.6 |

  Current-grade: 520.5 / 4841 (+5.9 % fuel). The spark lever ALONE, held at +4, cuts total
  damage 37.8 % and thermal damage 49 % (437.7 vs 859.5) while saving 4.9 % fuel -- about the
  whole hand-written policy on total damage and more on thermal. Total damage is lowest near
  +6 deg, where the knock term starts to dominate: with a wider action bound the knee would
  become the stop. (The knock column here includes the grade-step spike made larger by a
  constant advance; the trained agents avoid much of it.)

### 4b. Spot-check of knock_margin.py (`spot_*.out`)

final.zip is gitignored, so the actor was rebuilt from `policy.npz` (tanh(mu(latent_pi)),
SB3's unscale) and `evaluate.run_episode` called unchanged:

| agent, episode | as trained: mine / published | capped: mine / published | trim on climb (trained) | KI p95 trained / capped |
|---|---|---|---|---|
| sighted_seed0, 0 | 327.991 / 327.991 | 467.862 / 467.862 | +3.94 | 0.776 / 0.633 |
| sighted_seed0, 7 | 495.422 / 495.475 | 891.990 / 892.100 | +3.94 | 0.726 / 0.609 |
| blind_seed5, 0 | 221.559 / 221.559 | 587.717 / 587.729 | +3.11 | 0.753 / 0.634 |
| blind_seed5, 7 | 438.204 / 438.205 | 784.701 / 785.091 | +3.89 | 0.770 / 0.628 |

All within 0.05 % (different torch build, 2.11 vs 2.14). KNOCK_MARGIN.md is reproducible from
committed files on any machine -- which also means P3 (re-testing the twenty on other roads)
does not need Ghassan's laptop.

### 4c. The grade-step spike (`step_spike_trace.py`, `knock_term_split.out`)

Hand-written policies (committed `traces_130kmh.json`): KI > 0.85 on exactly four steps -- t = 6,
7, 9 s (launch, KI 0.86-1.05) and **t = 180 s, KI 2.06-2.16 at 23.77 deg spark**, one step worth
58.6 of the baseline's 60.56 knock damage. The cause is the one-step-lagged spark schedule
(`ecu.step(self.rpm, self.map_b_prev, ...)`, `engine_env.py:867`) meeting an instantaneous grade
step (`:1043`). Jad's D2/C4 roads are also instantaneous steps (`random_road.py:111-113`), so the
spike exists there too (C4 episodes: KI max 1.6-2.2, knock damage 25-74 per episode).

sighted_seed2, episode 0: trim -2.16 at t 174, then -3.66, -5.16, -6.66, -7.89 (t 175-178, the
slew limit), spark at the step 16.17 deg, KI 1.386, knock damage 11.50. Its blind twin: trim
+2.83 at t 179, spark at the step 27.00, KI 2.159, knock damage 68.56. Total damage 292.97 vs
399.88. The sighted agents learned (on the 5-11 locked roads each saw in training) to pre-retard
for a one-second artefact.

### 4d. What the car says (`car_spark_at_climb.out`)

Genuine spark readings (value changes, AUDIT.md H4), rpm 2000-4000, drives with measured
ambient (drive B logs no spark):

| MAP kPa | readings | drives | car median | BaselineECU median (same rpm/MAP/ambient) | car - baseline |
|---|---|---|---|---|---|
| 140-160 | 7 | 4 | +4.50 | +11.83 | -7.65 |
| 160-180 | 4 | 2 | +1.88 | +5.09 | -7.12 |
| 180-200 | 4 | 2 | -0.75 | +7.59 | -4.51 |
| 200-240 | 16 | 3 | -1.12 | -3.42 | -2.91 |

The real ECU runs LESS advance than the model's baseline in boost, in cooler air (median ambient
24-36 C against the scenario's 42 C). Too few readings to calibrate anything, but they point
against the agents' extra +4 deg being margin the car has. Target-minus-actual (the retard) has
1-2 readings per bin -- useless, as Ghassan's 28 Sep diagnosis predicts.

Evidence on the knock model itself: Jad's branch reports correlation -0.149 between model KI
and the car's retard over 13 592 rows of 7475b5d7 (CLAUDE.md); Ghassan shows those rows hold
only 404/410 genuine readings of the two angles (one per ~8 s), so the test could not see a
1-2 s retard: UNTESTED, not refuted (Ghassan CLAUDE.md 1697-1707). Both agree it is not
validated. Nothing on either branch validates the 0.85 knee or the 40x weight.

### 4e. Jad's C4 agents (`jadc4_*.out`, `jad_d2_hand_*.out`)

| C4 agent, D2 episode | trim on climb | KI p95 | damage trained | damage capped | current-grade | baseline |
|---|---|---|---|---|---|---|
| sighted 0, ep 0 (141 s, 13.31 %) | +3.91 | 0.763 | 501.7 | 832.7 | 907.0 | 2113.5 |
| sighted 0, ep 8 (229 s, 14.03 %) | +3.67 | 0.831 | 204.2 | 271.7 | 374.1 | 560.5 |
| blind 0, ep 0 | +3.22 | 0.755 | 1222.9 | 2053.1 | 907.0 | 2113.5 |
| blind 0, ep 8 | +3.98 | 0.806 | 316.9 | 525.1 | 374.1 | 560.5 |

Zip copies verified against the scored ones (sha256 prefixes 20f0ae6a9c1564a9, 9ab8d2b29cbb9d06
match `results/c4_seed0.txt`).

## 4f. Co-work claims

| claim | verdict | evidence |
|---|---|---|
| C7 rules not written before training | PARTLY | design written in committed docs at cbb8d09 (09:44), training 11:55; paired t + two-sided Wilcoxon in run_results.py at cbb8d09 (for 5 seeds); no hypothesis direction, alpha, MEI, decision or stopping rule; 5 seeds written, 10 run; git_dirty true |
| C8 trained on varied roads, tested on one one-climb road | CONFIRMED | evaluate.py:126-127 builds make_grade_climb for all 20 episodes; locked family is 0.15 of training (156/1100 episodes); no rolling/double road scored |
| C11 agents advance spark to just under the knock limit because the model treats it as safe; model unvalidated | CONFIRMED with precision | trims 3.46-3.98 at the +4 bound; KI p95 0.767-0.789 < knee 0.85; knee at 6.9 deg, flag 1.0 at 10.0 deg (held torque); no knock feedback on the agent path |
| C12 cap: +24 -> -2 points; approximate | CONFIRMED | recomputed +24.45 -> -1.78, 9 of 20; spot re-run 8 episodes within 0.05 % |
| C13 Jad's agents probably do the same (extra) | CONFIRMED on 2 C4 agents x 2 D2 episodes | trims +3.2 to +3.98; capped damage +33 to +68 % |
| C14 main result firm on two branches | PARTLY | no significant preview effect anywhere, but INCONCLUSIVE at power 0.26 here; D, D2 INCONCLUSIVE; C4 sign-only; shared knock model and step artefact; the knock term shows a 10/10 artefactual preview effect |
| C15 supervision advantage depends on the knock model | CONFIRMED | cap removes the whole median margin; +4 trim alone ~ current-grade; car's boosted spark 3-8 deg below the model baseline |

## 5. What would settle it

**Measurement (read-only OBD logging only; nothing is ever written to the car).** Nothing on
this car can test "does the engine tolerate +4 deg" directly -- we cannot command spark. What we
CAN log is where the production ECU puts spark, and whether its knock control is retarding, at
the climb's operating point. That answers the question that matters: is BaselineECU's spark
representative there? If the car runs ~1 deg with retard active, the model is too lenient and
the agents' gain is an artefact; if it runs ~1 deg with no retard, the real calibration keeps
the margin on purpose and a supervisor that removes it trades robustness, not protection; if it
runs ~5 deg, the baseline is too conservative and the real ECU already has the gain. In none of
the three cases is the +4 deg a demonstrable benefit over the real car.

- Channels (6, ~1.25 s per channel): Engine speed, Air mass flow, Actual ignition angle, Target
  ignition angle from torque intervention, Coolant temperature, Ambient temperature (Ghassan's
  drive C list, `logs/DRIVE_PLAN.md`). Do not add channels: every extra one slows all of them
  (mistake 13b). Knock-sensor voltages are useless at this rate (census).
- Load: the climb point is ~2700 rpm at ~175 kPa (~340 Nm). A public mountain road at legal
  speed does not sustain that (drive10, the Taif climb, never came near). The legal way to reach
  it is what drive B did: firm-to-full throttle roll-ons in a held gear (manual mode) through
  2000-3500 rpm, 3-6 s each, 20 or more, with a minute of steady cruising between them so that
  each pull gives independent readings; on a straight, empty road, below the limit.
- Conditions: afternoon heat (ambient 38-42 C), fully warm (coolant >= 88 C), after sustained
  driving so the charge air is heat-soaked; 95 RON in the tank. Passenger runs the phone. Skip
  any pull that cannot be done safely.
- Read-out: per genuine reading, car spark minus `BaselineECU.base_spark + iat_compensation` at
  the same rpm, inverted MAP and ambient; and target - actual. Fixed before the drive: the
  comparison bins (MAP 160-200 kPa, 2400-3000 rpm) and the number of readings needed (>= 30).

**Compute (no drive needed).**

1. Cheapest, already done by Ghassan and reproduced here: the cap diagnostic (~50 min for 20 x 20
   on his laptop). It is out of distribution and can over- or under-state the dependence.
2. The decisive one: retrain the twenty with the spark lever retard-only (`ACT_HI[0] = 0`),
   everything else unchanged -- one variable. Cost measured on each branch: 234 min for 20 runs
   at once on Ghassan's 20-thread laptop (3.6 steps/s each); about 3 h in two waves of ten on
   Jad's 12-core machine (C4 ran ~10 000 steps per 17 min per run with ten at once). Scoring: ~50
   min. Preregister it first (Jad's method: primary outcome, sign test, MEI 50, cells), score it
   on BOTH the locked climb and EPISODES_D2, and report damage two ways.
3. Remove the grade-step artefact before any preview claim: ramp the grade step (the training
   roads already ramp 4-12 s) or schedule the baseline's spark on the current step's MAP. Either
   is a plant/scenario change and needs its own preregistration; until then report the
   ablation on thermal-only damage beside total damage.
4. P3 (twenty agents on multi-climb roads, no retraining): possible from policy.npz on any
   machine; ~400 episodes, about 1 h on 10-12 cores under light load. Freeze the road set and the
   test in writing before running it.
