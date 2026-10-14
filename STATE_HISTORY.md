# STATE_HISTORY — the project's superseded states, verbatim

Append-only, newest first within each part. Nothing in this file is current:
the current state is `CHECKPOINT.md`, the permanent rules are `CLAUDE.md`, and
the live figures are in `README.md`. Every block here was moved, not rewritten,
on 14 October 2026 (the documentation restructure, plan v3 phase 4). The ledger
of every move is `_merge_review/MIGRATION_LEDGER.md`; a block's history before
the move is `git log -L` on the file it came from.

# Part A — the dated state boxes from CLAUDE.md (moved 14 October 2026)

From Ghassan's X2 box of 11–13 October back to Phase D's of 21–22 September, in
the order CLAUDE.md held them.

## 11–13 October 2026, on `GRA-2340394`: X2 — wider air, 5 seeds a side, 1200 episodes each

> **X2 HAS RUN. ITS PREREGISTERED READING IS INCONCLUSIVE, AND ITS AGENTS HAD
> NOT CONVERGED** (`python analyse_x2.py` -> `results/X2_RESULT.txt`;
> `results/x2_convergence.txt`): 1 of 5 pairs favours preview, mean −4.40
> points, sd 20.51; the same thermal-only. **The sentence that may be said:**
> *"INCONCLUSIVE on five pairs: the paired differences have an sd of 20.51
> points, at which a test needs 143 seeds for 80 % power against the MEI. The
> agents were still changing at 1200 episodes."* Never "preview does not help".
>
> - **Convergence (C4's rule): 0 of 5 sighted and 1 of 5 blinded agents settled,
>   0 of 5 pairs**; between 720 000 and 1 080 000 steps the practice cuts still
>   moved by up to 33.6 points against a band of 2.7. About 22 times X1's
>   training did not settle these agents, and the spread barely narrowed (sd
>   20.51 against X1's 24.78).
> - **Supervision, separately:** 7 of 10 beat `current-grade`; 4 of 10 do more
>   damage than the baseline ECU on some frozen episode. Post hoc: sighted seeds
>   1 and 2 cut under `current-grade` and no blinded agent does — X1's pattern.
> - **No agent passes the probe** (22–93 % of states violate) and **0 of 10 pass
>   the logged-drive check**: with life weighted most, 59 of 60 runs burn more
>   than 1 % over the ECU car (median +6.92 %), more than X1's agents; five also
>   fall short of the torque somewhere. Wider air did not teach fuel restraint.
> - **The transfer test (T; five episodes a condition, so descriptive):** held
>   out, 8 of 10 agents beat that condition's `current-grade` at 50 °C, 6 of 10
>   at 76 kPa (partly by refusing torque: a median of 48 steps short, one run 525
>   of 719) and 5 of 10 at 25 °C on the 21.75 % hill (X1: 26, 25 and 30 of 46);
>   in range 4–10 of 10. One agent does more damage than its baseline ECU
>   (sighted seed 2, 25 °C). Its first run stopped on its own harness (it named
>   seeds X2 does not have); fixed, re-run, 5 of 5 identical
>   (PREREGISTRATION_X2.md 11–12).
> - **Why it failed, measured after the result** (`results/X2_AGENTS.md`,
>   `python x2_agents.py`; description, not a test). (1) The sighted agents read
>   the preview and use it in opposite directions: seeds 3 and 4 add protection
>   before the hill, seeds 0–2 lean out and raise boost; seeds 1 and 2 then
>   enrich about a quarter as deeply as their twins on the climb, whose air X2
>   drew on 1–2 % of episodes and whose constant speed never. (2) The policies
>   never settled: each agent's practice cut spans 6.0–88.5 points across six
>   checkpoints, and which way a pair reads depends on where each twin is in its
>   swing. (3) The fuel goes to knock: 56–97 % of the extra fuel is spent where
>   the ECU car's housing is under 500 °C, and what the agents avoid there is the
>   baseline ECU's one-step knock spike (spark on the previous step's manifold
>   pressure) at every jump in the torque request. About 85 % of the training
>   knock falls on the start of a speed-up or the end of a slow-down, which no
>   observation shows coming. The knock model is untested (drive C).
>
> **What X2 was** (`runs/wideair_dt1/`, trained 11–13 October, 51 hours, none
> crashed), under `results/PREREGISTRATION_X2.md`, committed as `06f4686` before
> any X2 agent trained. Ordered by Ghassan: the extremes roads with ambient
> **0–45 °C** and pressure **80–101.3 kPa** drawn per episode, **5 seeds a side**
> (he chose five over three once shown that three pairs can never pass the sign
> test), **1 080 000 steps (1200 episodes) per run**. Nothing else changed from
> X1, the plant included: X1's fingerprint, so X1's agents stay scoreable.
>
> - **Five pairs, said before the result:** the smallest one-sided sign p is
>   0.031, so every cell but INCONCLUSIVE needs all five pairs on one side, and
>   at X1's spread the power against the MEI is 0.07. X2 is also a measurement:
>   whether the agents settle (`check_x2_convergence.py`, C4's rule) and how far
>   apart the seeds are after 1200 episodes, which sizes the next test
>   (`analyse_x2.py` prints the seed count).
> - **`wide_air.py`, no hashed plant file touched:** the compressor inlet follows
>   the pressure (the conditions test's model, per episode), and two of X1's
>   rules follow the air, each found by a gate before training. The road's torque
>   floor: the engine makes 20.6 Nm with the throttle shut at 0 °C, and X1's
>   15 Nm failed five cold roads. The gearbox's kickdown table: at 45 °C and
>   80 kPa the sea-level table held a gear the engine could no longer pull. At
>   101.3 kPa the design reduces to the plant to the bit (`test_wide_air.py`).
> - **Gates:** `test_reward.py` 12 of 12 (two new, on the thin-air corners);
>   `check_roads.py --road wideair` PASS, worst neutral −0.0054. **The baseline
>   passes 850 °C on 2 of 40 wideair roads against 10 of 40 on X1's**: most of
>   X2's training needs no protection (preregistration limit 7).
> - **Crash rule, new:** `--keep-buffer`. A run that stops resumes from its last
>   checkpoint WITH its replay buffer: re-run the same `train_all.py` command.
>   Never needed: no run stopped.
> - **Scored unattended** by `x2_score.py` (`results/x2_score/SCORE_LOG.txt`).

## 8–9 October 2026, on `GRA-2340394`: X1 — the agreed fixes in the plant, the extremes design, 23 seeds a side

> **X1 HAS RUN. ITS PREREGISTERED READING IS SMALLER THAN THE MEI**
> (`python analyse_x1.py` -> `results/X1_RESULT.txt`): 17 of 23 seed pairs below
> 5.43 points of cut, sign p 0.0173, the permutation test agreeing (p 0.0027);
> preview helps in 10 of 23 (p 0.80); preview costs damage, 13 of 23, is not
> significant (p 0.34). The same reading without the knock term. **The sentence
> that may be said:** *"Preview's effect on the locked climb is below the MEI
> (5.43 points of cut) for agents trained on the extremes design at 50 000
> steps."* Never "preview does not help".
>
> - **Say what it rests on.** Mean −10.35 points, sd 24.78 — three times the
>   spread of 29 September (power 0.20 against the MEI at it). **Six sighted
>   agents cut under 40 % on the scored climb (seeds 4, 13, 16, 17, 21, 22) and
>   no blinded agent does** — post hoc, not a test. On their own training roads
>   the same six protected like the rest (25.6–47.4 % against the parallel car);
>   on the climb five enrich at most half as deeply as their twins and three
>   retard spark 2.2–4.3°. Why their training did not carry over is not measured;
>   the climb's constant 130 km/h is never drawn in X1's training.
> - **Supervision, separately:** 39 of 46 beat `current-grade` (17 sighted, 22
>   blinded); 19 of 46 do more damage than the baseline ECU on some frozen episode.
> - **No agent passes safeguard 2's probe outright:** a 50 K hotter housing gets
>   less protection on 1.1–98.5 % of probed climb states (median 49 % sighted,
>   62 % blinded). Under every damage formula decisions 8 and 9 named, 38–39 of 46
>   still beat current-grade and the ablation mean stays −9.9 to −13.0 points.
> - **The transfer test (T; five episodes a condition, so descriptive):** held
>   out, **30 of 46** agents beat that condition's `current-grade` at 25 °C on
>   the 21.75 % hill and **26 of 46** at 50 °C; on the in-range controls 29 of 46
>   at 42 °C and 42 of 46 at 35 °C; under air pressure X1 never trained in,
>   25–32 of 46. In every condition 0–3 agents do more damage than its baseline
>   ECU, mostly the same few (blinded seed 2, sighted seeds 17 and 21). Only at
>   25 and 35 °C does `current-grade` deliver its torque (elsewhere it misses
>   on 16–297 of 719 steps, so its cut is partly torque refused), which makes
>   those two the clean pair: held out 30, in range 42. The twenty of
>   29 September on the same hills, on the plant before the fixes and with
>   spark advance allowed: 6 of 20 at 25 °C, 19 of 20 at 50 °C — a reading
>   beside X1, not a test. `python conditions_test.py --set runs/extremes_dt1
>   --report-only`. Its first run stopped on its own harness check (the workers
>   loaded the 29 September agents); fixed, 5 of 5 identical, re-run.
> - **The logged-drive check: 1 of 46 agents passes** (sighted seed 18). They
>   deliver the torque; they burn fuel: weighting life most, 252 of 276 runs
>   spend more than 1 % over the ECU (median +4.3 %, worst +21.4 %), and 67 % of
>   all that extra fuel goes while the ECU car's housing is under 500 °C. On the
>   car's own driving, X1's agents protect where nothing needs it.
>
> <!-- RETIRED-OK: 920.1, 43.4, -0.32, 917.6, 850.4 -- the merged plant's premise, named beside X1's -->
> **X1 WAS PREREGISTERED (`results/PREREGISTRATION_X1.md`, committed before any
> X1 agent trained) AND TRAINED into `runs/extremes_dt1/`.** Ordered by
> Ghassan ("add more seeds and retrain") before Jad's column of the decision
> sheet is filled; section 9 of the preregistration lists the decisions X1
> adopts provisionally and what a different answer from Jad would cost.
>
> - **The four plant steps agreed on 30 September are in**, each measured on the
>   locked climb (`check_premise.py`): the thermal network sub-stepped
>   (`thermal.DT_SUB_MAX` 0.1 s), the fingerprint covering the derived constants
>   (schema 2, `derived_sha` fatal), the spark trim capped at 0, every grade
>   change ramped over 8 s. **Baseline 920.1 → 848.1 at 883 °C, current-grade
>   cuts 43.4 → 47.0 %, preview over current-grade −0.32 → −0.01 points**; the
>   ramp is 70 of the 72 units (the one-step knock spike), the sub-stepping 2.5.
>   `plant_sha` is now `3c48890dd15bc116`: every earlier agent is refused on it.
> - **The training design is decision 12** (`engine_env.ExtremesTrainingEnv`,
>   `train.py --road extremes`): ambient 25–45 °C, a speed target of 60–150 km/h
>   redrawn every 60–180 s, hills to 18 %, the housing's heat capacity ×0.75–1.33
>   per episode. No road asks less than 15 Nm: the model has no fuel cut, and the
>   first drafts made the baseline itself score −0.05 to −0.69 per step. Held
>   out: 50 °C and hills of 18–22 % (`conditions_test.py --set`); checked on six
>   logged drives replayed flat (`logged_check.py`); `sanity_probe.py` asks
>   whether a hotter housing ever gets less protection.
> - **23 seeds a side, 46 runs:** the exact sign test reaches 0.822 power against
>   the MEI (5.43 points of cut) at the spread of 29 September; 20 pairs give
>   0.640. The test is fixed in `analyse_x1.py`, dry-run on the twenty of
>   29 September (it reproduces their INCONCLUSIVE).
> - **Gates on this plant:** `test_reward.py` 10 of 10 (two new checks on the
>   extremes roads); `check_roads.py --road extremes` PASS on 40 roads, 10 bind;
>   `validate.py` 8 of 11 (row 8, oil, 97.0 → 97.1 °C).
> - **Every figure below this box that quotes the merged plant (920.1, 43.4 %,
>   −0.3) is that plant's.** The document sweep follows the launch.
> - Fixed on the way: `power_analysis.delta_for_power` returned 64.63 points at
>   23 seeds (a binomial tail that underflowed near p = 1); it gives 5.26 now,
>   and the script's own output did not move. `train_all.py` passes `--road`
>   explicitly; `runs/terrain_dt1/` is CLOSED in `train.py`.
> - **The step error is gone, and the H/τ sweep re-ran on this plant.**
>   `timestep_study.py`: stepping the network 50 times finer now moves a cut by
>   0.00 points at 1 s and at the sweep's 2 s (the coolant swing that made the
>   sweep unquotable is gone); `generality_test.py`: preview over current-grade
>   0.0 points at every binding τ, 0.0 to +0.3 with the limit kept binding.

## 7–8 October 2026, on `GRA-2340394`: the validation plan, every step recorded, the damage constants

> **THIRTEEN DECISIONS ARE OPEN, ONE SHEET: `results/VALIDATION_DECISIONS.md`,**
> a column each for Ghassan and Jad. Nothing is relabelled, re-preregistered or
> retrained until they are answered and committed. Nothing below changed a
> hashed plant file, the reward or the twenty frozen episodes.
>
> - **`results/VALIDATION_PLAN.md` (DRAFT):** every scorecard label to be
>   COMPUTED (ASME V&V 20's comparison error and validation uncertainty against a
>   required accuracy per context of use; NASA-STD-7009B for the risk side), not
>   assigned by reading. Jad's review of 7 October is taken (its section 12).
> - **Diagnostics behind it:** `validation_numbers.py`, `car_spark_boost.py`,
>   `timestep_study.py` (u_num: converged at dt 1.0, too large at the sweep's
>   dt 2.0), `damage_robustness.py`, `conditions_test.py` (the twenty agents in
>   other air and on a varying speed target), `damage_constants.py`.
> - **EVERY STEP IS RECORDED** (`step_record.py`, one definition of a step, used
>   by `evaluate.py`, `record_agents.py`, `knock_margin.py`, `conditions_test.py`
>   and `train.py`): the action and what the actuators applied, the observation,
>   the reward and its terms, the road (grade, speed, gear), the engine, the heat,
>   the parallel baseline car and the running totals. `train.py` now keeps 44
>   fields a step; an agent trained with the recorder is the agent trained
>   without it (600 steps, largest weight difference 0.0). The twenty of
>   29 September recorded no road: `training_roads.py` regenerated their roads,
>   preference weights and applied actuators from the seeds and the recorded
>   actions, and checked every step (20 of 20 runs). `show_record.py` draws any
>   episode of any record. Records stay out of git (decision 11).
> - **The damage constants** (`results/DAMAGE_CONSTANTS.md`): the turbine scale
>   is calculable once a mechanism is named (creep rupture: 20.3 K); the knee is
>   bracketed by published gas limits; the oil weight and knee are one number;
>   the weights are valuations; the knock knee waits for drive C. Under every
>   calculated value all twenty agents still beat current-grade and the ablation
>   stays inconclusive, unless the knock term is made large.
> - **Mistake 23:** the knee was called "80 K more conservative" than a GAS
>   limit it is not comparable with; like for like it is 54 K hotter.
> - **Mistake 24, found in the new records:** blinded seed 6 is NOT trading life
>   for fuel on its five bad frozen episodes; it burns more fuel there too, and
>   retards spark. The same retard is behind its failure at 25 °C, and the plan's
>   "every agent keeps +3 to +4° of spark" was a group median (corrected).

## Current state — 30 September 2026 (the two branches merged)

> <!-- RETIRED-OK: 959.8, 884, 920.1, 43.4, -0.3 -- sep17's plant, and the merged plant's own premise, superseded on 8 October -->
> **THE BRANCHES ARE ONE AGAIN.** Ghassan's `JMF-2340550` (tip `74de99a`) was merged
> into Jad's `JMF-2340550-sep17` (tip `086c519`) on 30 September, hunk by hunk, as
> both of them agreed: the decisions are `conflict.md` (Arabic copy `conflict_ar.md`),
> Ghassan's reply accepted all five, and the account is
> `SESSION_REPORT_2026-09-30_merge.md`. The old tips are tagged `sep17-before-merge`
> and `ghassan-before-merge`; the branches were renamed
> `JMF-2340550-leftin-2026-09-30` and `GRA-2340394-leftin-2026-09-30`.
>
> **The rule of the merge: Ghassan's physics, Jad's method.**
>
> - **Physics (Ghassan's):** exhaust into the turbine node = air + fuel (it was
>   fuel × 15); drag air density from the ambient; the boost ceiling = the measured
>   envelope, evaluated at ambient; the spark offset, the enrichment dwell, the
>   kickdown table and the thermal block and oil nodes derived from the logs
>   (`derive_params.py` → `data/derived_params.json`).
> - **Method (Jad's):** preregistration before training, the MEI rule (50 damage
>   units), the plant fingerprint, the `train.py` guards, the document guard.
>
> ```
> python check_premise.py   merged plant: baseline 920.1 at 883 C, current-grade cuts
>                           43.4 %, preview over current-grade -0.3 points
>                           (sep17's plant printed 959.8 at 884 C: the equal peaks are
>                           two corrections cancelling, +5.5 K exhaust, -6.2 K air)
> dataset                   11 drives, 321.7 minutes, 8 carrying samples, 26 points
> plant_sha                 c236a8db3e201090 (sep17's agents: b5a3069f32a83754)
> ```
>
> - **All 48 of Jad's agents (Phase D, D2, C4) are REFUSED on the merged plant** —
>   correctly. Their preregistered results stand as records of the sep17 plant;
>   `analyse_phase_d.py`, `analyse_phase_d2.py` and `analyse_c4.py` still print them
>   from the committed result files; re-running an agent needs `sep17-before-merge`.
> - **Every preview result is INCONCLUSIVE or one seed thin:** Phase D and D2
>   INCONCLUSIVE; C4 smaller than the MEI by the sign test only, not converged;
>   Ghassan's ten-pair retrain INCONCLUSIVE under the MEI rule (6 of 10, sign
>   p 0.377, power 0.26). Never "preview does not help".
>
> **TWO FINDINGS OF THE MERGE REVIEW, TRUE ON BOTH BRANCHES:**
>
> 1. **All 68 trained agents push the spark trim to its +4° action bound.** With
>    advance forbidden, their margin over `current-grade` goes: Ghassan's 20,
>    +24.4 → −1.8 points (20 episodes); Jad's C4, +15.7 → −1.2 (one episode). The
>    car's own boosted logs run 3–8° *below* the model baseline's spark. **The
>    supervision claim rests on the untested knock model.**
> 2. **A one-step knock spike at every instantaneous grade step.** The baseline
>    ECU schedules spark on the previous step's MAP, so for one step KI reaches
>    ~2.1: 59 damage units on the merged plant (66 on sep17's), 34–102 on D2's
>    roads — the size of the MEI. It is all of the hand-written preview gap, and
>    the only significant preview effect in Ghassan's retrain (knock term, 10 of
>    10 seeds). An 8 s ramp removes it.
>
> **AGREED BY JAD AND GHASSAN, BEFORE ANY TRAINING, IN THIS ORDER:**
>
> 1. Sub-step the thermal network, or integrate it implicitly. With the derived
>    constants it is stiff above dt ~1.1 s: at dt 1.0 the coolant zig-zags ~2 K
>    on every step of the climb, at dt 2.0 it swings 85–95 °C and never settles.
>    No H/τ output is quotable until this lands.
> 2. The fingerprint covers `data/derived_params.json`. Today a new drive changes
>    the plant without moving `plant_sha`.
> 3. Cap the spark trim at 0 for the next training, and report every result with
>    and without the knock term until drive C.
> 4. Ramp every grade change.
> 5. A new preregistration for the next experiment. **Then drive C (knock), before
>    drive A.**
>
> The boxes below are each branch's own, kept as written, with four corrections
> Ghassan accepted marked in his.

---

## State as of 29 September 2026 (the retrain: twenty agents, every action recorded), on `JMF-2340550`

> ### THE RETRAIN RAN. THE AGENTS PROTECT; PREVIEW IS INCONCLUSIVE.
>
> *(Corrected 30 September, accepted by Ghassan: this heading said "PREVIEW ADDS
> NOTHING MEASURABLE". Under the preregistered MEI rule the ten pairs are
> INCONCLUSIVE, sign-test power 0.26.)*
>
> Committed on `JMF-2340550` on 29 September. Full account:
> `SESSION_REPORT_2026-09-29.md`. Every table, generated:
> `results/agents/terrain_dt1/README.md` and `KNOCK_MARGIN.md` beside it.
>
> - **Twenty agents** (`python train_all.py`): seeds 0–9, sighted and blinded,
>   50 000 steps (55 episodes) each, a new road every episode, 130 km/h,
>   dt 1.0, on the derived plant (data fingerprint `c4fdd4babfb3752a`, commit
>   `cbb8d09`). All twenty at once took 234 min on the team laptop, 3.6 steps/s
>   each. **Ten seeds, not five:** with five pairs an exact Wilcoxon test
>   cannot go below p = 0.0625, so five seeds could never show a preview effect.
> - **On the CPU, and it was measured:** the plant is 84 % of a step (61.6 ms,
>   against 11.5 ms for SAC's update), so a GPU could save at most 16 %, and
>   twenty CUDA contexts do not fit a 4 GB laptop card. The installed torch is
>   a CPU build. `train.py --device` is there for when that changes.
> - **Scored with the twenty frozen episodes** (`run_results.py` ->
>   `results/phase_d_130kmh.*`; `record_agents.py` re-ran all 480 agent and
>   hand-written episodes and found them identical):
>
>   | | median cut | over current-grade | thermal-only cut |
>   |---|---|---|---|
>   | sighted, median of 10 | 67.9 % | +24.5 | 67.0 % |
>   | blinded, median of 10 | 65.4 % | +22.0 | 68.5 % |
>   | current-grade, hand-written | 43.4 % | — | 47.2 % |
>
>   **All twenty beat every hand-written policy**; the weakest, blinded seed 1,
>   cuts 49.0 %.
> - **THE ABLATION, TEN PAIRS: sighted minus blinded +1.2 points, 95 % CI −4.4
>   to +6.8, paired t p = 0.65, exact Wilcoxon p = 0.43.** Thermal-only (no
>   knock term): −1.5 points, p = 0.56. The pairs run from −14.3 to +14.6. At
>   this scenario's H/τ (30 s over τ ≈ 47 s, 0.64) what a learned policy gains
>   comes from learning to protect, not from seeing ahead. **One point on the
>   H/τ curve, not the curve** — Phase F is what maps it.
> - **Every agent advances spark to the +4° ACTION BOUND, which happens to sit
>   just under the knock knee** (corrected 30 September). On the climb
>   the median trim is +3.5 to +4.0° over the baseline's 1.2° (the trim's upper
>   bound is +4), and the knock integral's 95th percentile is 0.77–0.79 against
>   the baseline's 0.61 and the damage knee's 0.85. **MOST of every agent's gain
>   over the hand-written policies is margin the UNTESTED knock model grants.**
>   Measured (`knock_margin.py`, a diagnostic beside the twenty episodes, never a
>   change to them): with spark advance forbidden the median cut falls 67.9 ->
>   41.6 % (sighted) and 65.4 -> 41.7 % (blinded), against current-grade's
>   43.4 %; 9 of 20 still beat it; the margin over it, median of all twenty,
>   +24.4 -> −1.8 points. A LOWER BOUND — an agent trained without the lever could
>   do better than one that has it taken away. The ablation is untouched, under
>   the cap too (−0.95 points). **Drive C (knock) now decides how much of the
>   agents' advantage is real.** `results/agents/terrain_dt1/KNOCK_MARGIN.md`.
> - **Blinded seed 6 does MORE damage than the baseline ECU on 5 of the 20
>   episodes** (worst 2 527 against 920, turbine 932 °C) — exactly the five with
>   the lowest weight on component life (at most 0.089). The preference-weighted
>   reward lets it trade life for fuel. No other agent does. By `evaluate.py`'s
>   own standard, a protection policy that is sometimes terrible is not one.
>   *(Corrected 8 October, from the per-step records: it is NOT trading life for
>   fuel. On those five episodes it retards spark on the climb, where on the
>   other fifteen it advances, burns 6.3–9.9 % more fuel than the baseline, and
>   its return is negative. It loses on fuel and life together: a policy that
>   fails on the inputs where life is weighted least, not a trade the reward
>   pays for. `python show_record.py results/agents/terrain_dt1/blind_seed6/eval_record.npz --episode 12`.)*
> - **Every action is recorded.** Training: `train_record.npz`, all 50 000
>   steps of each run (action, observation, reward, engine state). Evaluation:
>   `eval_record.npz`, every step of the twenty episodes, the commanded AND the
>   applied actuators. With config, curve, policy weights and a scored summary,
>   in `results/agents/terrain_dt1/` (the twenty) and
>   `results/agents/sep19_110kmh/` (the ten of 19 September, whose TRAINING
>   actions were never recorded and cannot be recovered). **The per-step
>   records (85 MB) are gitignored by the team's decision**; everything else —
>   configs, curves, summaries, policy weights, READMEs, figures — is in git.
> - **The fuel is settled: 95 RON**, confirmed by the team — what the model
>   already runs, so no refit (REFERENCES.md 2c).
> - **Still open, each a plant change and so a retrain:** the boost ceiling low
>   at 1600–2000 rpm (mistake 22) and drive A. **The team will retrain after
>   each new drive** (the plant re-derives from the logs), so a drive is a
>   retrain by plan, not a setback. And the sep17 merge.

## State as of 28 September 2026, evening (drive B; the data sets the constants)

> ### THE CONSTANTS THE CAR'S LOGS CAN SET ARE NOW COMPUTED FROM THEM
>
> **Nothing below is committed yet** — the working tree carries it all. The full
> account is `SESSION_REPORT_2026-09-28_evening.md`.
>
> - **Drive B is in** (`logs/raw/driveB_rollons-20260928_140513.csv`): 26.7 min of
>   full-throttle roll-ons in a held 6th/7th/8th, 7 channels read every 1.05 s.
>   Dataset **321.7 min, eleven drives, eight carrying samples**. It logged **no
>   ambient temperature and no oil**; its corrected flow uses
>   `build_dataset.AMB_FALLBACK_C` (42 °C, from the other afternoon drives), its
>   rows carry `t_amb_assumed = 1`, and the charge-temperature check excludes them.
> - **`derive_params.py` → `data/derived_params.json` → `derived.py`.** Every
>   constant the logs can set is recomputed from them, and `build_dataset.py`
>   runs it at the end: the thermal block and oil nodes, the boost ceiling, the
>   spark offset, the enrichment dwell, the kickdown table. **No module types a
>   fitted number the data can set.** What cannot be derived, and why, is
>   REFERENCES.md section 4b. **A new drive therefore changes the plant — and a
>   plant change after the retrain means retraining.**
> - **The oil node had the wrong STRUCTURE.** The car's oil heats with engine
>   speed (drive10: 3700–4800 rpm at 70–100 km/h, oil 11–15 K over coolant) and is
>   cooled by road speed (130–140 km/h cruise: oil 2–3 K under coolant); the model
>   heated it with 5 % of fuel. Re-structured and fitted (`calibrate_thermal.py`,
>   7 drives, leave-one-out): oil τ **14 → 57 s**; drive10 RMSE oil
>   **7.55 → 3.57 K** (3.90 held out), coolant **5.51 → 2.28 K** (2.35 held out).
> - **`validate.py`: 8 of 11** (6 of 7 literature, **2 of 4 car**). Rows 10 and 11
>   (coolant) inside; **rows 8 and 9 (oil) still outside** — 97.0 °C against
>   103–111 and 60 s against 70–100 — and NOT tuned in: of row 8's 12.0 K miss, 4.6 K is the coolant (the car's heat-management valve let it rise to 97–99 °C where the model regulates near 93; pinning the block to the measured coolant recovers 4.6 K) and 7.3 K is the oil node itself, which runs 4.4 K over its coolant where the car's oil runs 11.7 K (`model_vs_data.row8_split`, 29 Sep; this read "about 6 K" of coolant until then, which was not measured). drive10 is in the fit; fitted WITHOUT it, row 8 reads
>   96.1 °C (outside) and row 11 92.0 °C (**still inside** — a genuine prediction).
> - **The boost ceiling IS the measured envelope** (binned p95, monotone, capped
>   at 2.515) — no formula. Against the highest boost drive B reached in each
>   200 rpm band it sits −7 to +7 % from 2000 rpm up (the 8 Sep formula was up to
>   17 % low there), but **9–20 % LOW at 1600–2000 rpm**: the car made more boost
>   there than the model allows. The envelope is built from quasi-steady rows and
>   roll-ons are transients, so those readings are outside it by construction.
>   *(Corrected 29 Sep: this said "matches at 1400–2400 rpm"; it does not at
>   1600–2000.)* The locked climb runs at 2706 rpm, where they agree (−0.7 %).
>   The kickdown workaround stays: no torque channel.
> - **Fixed on the way, each measured:** exhaust flow was fuel × 15 (now
>   air + fuel, +5 K turbine); the ceiling used the charge temperature as its
>   inlet (now ambient); air density was a typed 1.2 (now 1.12 at 42 °C);
>   `generality_test.py`'s M12 fix read a key nobody wrote (the τ axis silently
>   stayed at 112.5 g/s); the premise figures were unguarded (`results/premise.json`
>   and `verify_docs.check_derived` now); `check_map.py` still used 1.12
>   backpressure; three results files had no script (`run_results.py`).
> <!-- RETIRED-OK: 920.1, -0.3 -- the 28 September plant, superseded on 8 October -->
> - **The premise, one change at a time** (`fig23`): baseline damage falls to
>   **920.1** at **883 °C** (current-grade **520.5**, predictive **523.5**). **Preview over
>   current-grade stayed at −0.4 → −0.3 through every step.**
> - **THE H/τ SWEEP, WITH THE HONEST COMPARATOR, SHOWS NO PREVIEW VALUE.**
>   *(30 September: not quotable until the thermal network is sub-stepped — at
>   dt 2.0, where the sweep runs, the derived coolant node never settles.)*
>   `generality_test.py` measured preview only against the REACTIVE policy; it
>   now also measures it against CURRENT-GRADE (AUDIT.md C3's comparator). At
>   every τ (H/τ 4.77, 1.53, 0.64) and every cost curvature, preview over
>   current-grade is **0.0 points** (at most +0.3 on H2b). The 13–80-point
>   "edges" were all timing against a reactive policy. Hand-written policies on
>   a single-step climb cannot settle it (C3), but **no sweep result can be
>   cited for the criterion now** — the trained ablation on varied roads is the
>   test. The τ axis uses the climb's measured 121.3 g/s exhaust flow.
> - **The ten old agents, re-scored on the derived plant** (`run_results.py`,
>   still a record): training over current-grade **+25.7** points; sighted minus
>   blinded, paired by seed, mean **−1.3** (sd 5.5, t −0.53, Wilcoxon p 1.00).
>   On thermal-only damage predictive and current-grade still tie (47.3 % /
>   47.2 %): the hand-written deficit is still the knock term. The speed-by-grade
>   sweep still binds at 3 of 12 combinations (12 % / 130 km/h peaks 883.0 °C).
> - **Gates on the final plant:** `test_reward.py` 8 of 8; `check_roads.py` PASS,
>   14 of 40 roads bind (was 11). A random policy now scores +0.004, just above
>   neutral — informational, but protection is cheap to earn by accident.
> - **The `sep17` merge** *(corrected 30 September, accepted by Ghassan: this
>   said 7 conflicts, 4 in code, "resolve code toward this branch", and that
>   `sep17`'s `engine_env.py` still had the six-speed box. The merge had 15
>   conflicted files, 7 of them code; it was resolved hunk by hunk per
>   `conflict.md`; and `sep17` had carried the ZF 8HP51 since `27e720c`,
>   19 September.)*

## State as of 28 September 2026, morning (the retrain is ready; three comparisons re-read)

<!-- RETIRED-OK: section -->
*The three boxes below are the morning's. The evening box above supersedes their
figures wherever the two differ (validate.py 7 → 8 of 11, the premise, the
dataset size, the oil node).*

> <!-- RETIRED-OK: 951.9, 931.5, 7 -- the 28 September morning plant and count -->
> ### LATER 28 SEPTEMBER: THE CAR NOW SCORES ITS OWN OIL AND COOLANT
>
> `validate.py` rows 8–11 are oil and coolant — quantities the car logs — and
> three of their four bands had no source. **They are now scored against bands
> computed from our own drives** (`validate.check_against_car`), through one
> shared replay, **`car_thermal.py`**: `thermal.py` free-running over a logged
> drive, fed the fuel the car actually burned (air mass / 14.7 λ, two measured
> channels, so the fuel cut is in it). `model_vs_data.py` uses the same replay.
>
> | row | model | band, from our car | |
> |---|---|---|---|
> | 8 oil, drive10's hottest 10 min | 96.4 °C | 103–111 | outside |
> | 9 oil apparent time constant | 14.0 s | 70–100 | outside |
> | 10 coolant, synthetic climb | 94.5 °C | 83.5–95.6 | inside |
> | 11 coolant, drive10 free-running | 88.4 °C | 91.8–94 | outside |
>
> **`validate.py` reads 7 of 11: 6 of 7 against literature, 1 of 4 against our
> car.** It read eight of eleven against the old bands; `verify_docs.py`'s
> expectation moved with that reason beside it. How each band is built:
> `validation_table.md` section A.
>
> - **The oil node is four to seven times too light — or too tightly coupled.**
>   The model's oil τ is c_oil / (ua_block_oil + ua_oil_amb) = 12 000 / 860 =
>   14 s; the car's is 70–100 s on four drives. At the fitted 800 W/K that is
>   c_oil ≈ 60 000–86 000 J/K, and the independent two-parameter fit lands on
>   48 000. `ua_block_oil` was fitted with `frac_fuel_to_oil` assumed, so the
>   ratio is what is known, not which term is wrong. **`thermal.py` is NOT
>   changed**: it moves the locked scenario's oil damage. Decide before the
>   retrain, with drive A.
> - **drive10's oil and coolant moved from "agrees" to "off"** once the replay
>   was fed measured fuel: −6.1 K and −4.7 K median (it read −4.4 / −4.0 on
>   modelled fuel). The coolant drifts down at light load where the car's
>   heat-management valve holds 92–94 °C.
> - **GCC spec (REFERENCES.md 2c).** The 382 hp engine is confirmed; no
>   admissible source shows uprated GCC cooling — do not write that it has any.
>   50 % stronger radiator and fan moves the climb's turbine 884.0 → 883.5 °C.
> - **Fuel.** The manual (team's report): 95 RON minimum, 98 recommended; the
>   model runs 95. At 98 only the knock term moves (baseline 951.9 → 931.5);
>   thermal-only preview stays +0.00. **Ask which fuel the car was logged on**
>   before the retrain — a change means refitting the knock-limited spark.
> - REFERENCES.md still quoted the best BSFC from before AUDIT.md H1; `validate.py` has
>   printed 239.9 since. Fixed and guarded in `verify_docs.RETIRED`.

> ### 28 SEPTEMBER: WHAT THE "OFF" AND "NEGATIVE" COMPARISONS ACTUALLY SAY
>
> Three measurements, none of which changed the model (`model_vs_data.py`):
>
> - **The knock comparison could not have seen knock.** `7475b5d7` was logged
>   with 26 channels, so its 14 318 rows hold only **404 readings of the target
>   ignition angle and 410 of the actual** in 55 minutes — one every ~8 s — and
>   a third of the pairs in a row were read more than a second apart. A knock
>   retard lasts a second or two. The −0.12 correlation is therefore **untested,
>   not refuted**: mistake 13b's trap again. Drive C in `logs/DRIVE_PLAN.md`
>   logs 6 channels to read both angles every ~1.25 s.
> - **Preview's −0.4 against current-grade is entirely the knock term.** On the
>   hand-written policies the knock damage term is 6–12 % of total damage, and
>   on turbine and oil damage alone predictive and current-grade TIE
>   (555.7 vs 555.8). Until the knock model is tested, report Phase D both
>   ways — total damage and thermal-only.
> - **The logs we have cannot calibrate the oil node.** Fitting the two ASSUMED
>   oil parameters on the three light-load calibration drives fixes the hard
>   pulls (134 → 104 °C, car 107) but breaks drive10, the only drive inside the
>   published band (116 → 102 °C, car 117). The drives pull opposite ways; only
>   sustained-load data (drive A) can decide. `thermal.py` is unchanged.
>
> **Elevation, stated plainly.** The scored climb rises **2 340 m** in its
> 720 s (3 120 m over a 900 s training episode); the training roads climb up to
> 3.8 km. But `p_baro` is fixed at 101.3 kPa and the plant never reads it:
> **the engine breathes sea-level air the whole way**, where a standard
> atmosphere gives about 76 kPa at 2 340 m. The scenario is sustained heavy load
> at sea level, not a mountain — which is also why no real road will ever cover
> it. Adding altitude would change the locked scenario, so it is not for Phase D.
>
> **A plant change after the retrain means retraining again.** Drives A and B
> would change the plant (oil node; boost ceiling and the gearbox workaround).
> Either drive first, or retrain now and retrain once more afterwards — about
> three hours of machine time each way. The improvement plan for every
> comparison is under "What to do next".

> ### 27 SEPTEMBER: THE RETRAIN IS READY, ON VARIED ROADS AT dt = 1.0
>
> - **Training draws a new road every episode** (`engine_env.TerrainTrainingEnv`):
>   the locked climb itself, single climbs of 4–14 %, rolling hills, double
>   climbs and flat. On one fixed road preview has nothing to say. **Scoring is
>   untouched** — `evaluate.py` still runs the locked climb and its twenty frozen
>   episodes. `python check_roads.py` drives the baseline over 40 of them.
> - **The roads found a gearbox defect.** In 8th at 130 km/h the model sustains
>   333 Nm but the box only downshifted above 375 Nm, so grades near 9 % could
>   not be driven by ANY policy (neutral reward −0.26). The box now kicks down
>   when the engine falls short (`Vehicle.DELIVERABLE_TORQUE`). Stated cost: in
>   that band the model runs a gear lower than the real car would need, because
>   its boost ceiling is too low at low rpm — flat-road logs never asked for it.
> - **The car-fitted spark map was never in use.** It sat above the model's own
>   knock limit at all 26 steady points, so the unvalidated knock model set
>   part-load spark. `SPARK_A` 26.18 → 13.33 (offset only): bias +3.16° → −0.08°.
> - **train.py now passes dt = 1.0**, the step `evaluate.py` scores at. It never
>   passed dt before: every earlier agent learned at 0.2 s. 50 000 steps is now
>   55 episodes, not 11. Output goes to `runs/terrain_dt1/`.
> - **Drives that would settle what the logs cannot:** `logs/DRIVE_PLAN.md`.
> - Results and figures for all of it: `results/`, and the phone page built by
>   `make_page.py`.
>
> Both fixes moved the locked climb's hand-written numbers a little (below);
> **preview against current-grade stayed at −0.4 points.**

## State as of 19 September 2026 (the real gearbox, and the scenario is loaded)

> <!-- RETIRED-OK: 951.9, 884 -- the 27 September plant -->
> ### THE SCENARIO IS LOCKED AT 12 % / 130 km/h, AND IT BINDS
>
> `make_grade_climb` now defaults to **130 km/h** (it was 110 on this branch).
> That is the value `sep17` locked on 18 September, **before any training run
> existed**, so adopting it is not tuning.
>
> **Why elevation has to be in the scenario at all: the car's own logs cannot
> load the engine.** Over 79 134 moving samples from the ten drives, median
> relative air filling per drive is **24–40 %**, and only **2.0 %** of samples
> exceed 120 %. The driving is fast — median 95–137 km/h, peaks past 200 — but
> it is straight-line motorway cruising on flat road, which asks for drag and
> rolling resistance and nothing else. **No amount of further logging will
> exercise the thermal model's hot region. The duty cycle is wrong, not the
> model.** A flat road at 90 km/h leaves the turbine at 349 °C against an
> 850 °C trigger; 6 % of grade gets it to 541 °C; it takes 12 % at 130 km/h to
> reach the knee. The full sweep, peak turbine over a 900 s episode:
>
> | speed | 0 % grade | 6 % | 12 % | 16 % |
> |---|---|---|---|---|
> | 90 km/h | 348.7 °C | 540.6 | 717.0 | 831.5 |
> | 110 km/h | 417.4 | 617.9 | 839.7 | **871.2 — binds** |
> | **130 km/h** | 476.3 | 760.4 | **884.0 — binds** | 902.9 — binds |
>
> *(The 0 % column moved on 27 September — 335.4 / 406.1 / 472.9 until then —
> because flat-road cruise now runs on the refitted part-load spark. Every
> loaded cell is knock-limited and did not move.)* <!-- RETIRED-OK -->
>
> **Three of twelve combinations bind**, so the locked 12 % / 130 km/h is not a
> uniquely tuned point. And at 0 % grade the turbine never passes 477 °C at any
> motorway speed — which is the whole argument for putting elevation in.
>
> **What the loaded scenario now shows** (`check_premise.py`, hand-written
> policies, and read AUDIT.md C1/C3 before quoting any of it). Measured
> 27 September, after the gearbox and spark fixes; it read 959.8 / 679.0 /
> 633.2 / 637.4 before them. <!-- RETIRED-OK -->
>
> | policy | damage | cuts | peak turbine |
> |---|---|---|---|
> | baseline ECU (true neutral) | 951.9 | — | **884 °C** |
> | reactive protection | 671.1 | 29.5 % | 862 °C |
> | current-grade protection | 624.5 | **34.4 %** | 861 °C |
> | predictive protection | 628.4 | 34.0 % | 861 °C |
>
> **Every policy now does real work** — the reactive row is no longer the
> baseline row. **Preview is worth −0.4 points against current-grade**, which is
> the closest to level it has ever been. The question is finally open rather
> than trivially negative, and only a TRAINED pair can settle it.
>
> **THE NEXT ACTION IS TO RETRAIN AT 130 km/h.** The ten agents trained on
> 19 September trained at 110, where nothing binds; they are kept as a record,
> not a result. 173 min per run, ten runs, one machine-night.

## State as of 24 September 2026 (after C4), on `JMF-2340550-sep17`

> **C4 HAS RUN. BY THE PRIMARY TEST PREVIEW'S EFFECT IS BELOW THE MINIMUM OF
> INTEREST — ON A MARGIN ONE SEED WIDE, WITH THE SENSITIVITY TEST DISAGREEING,
> AND WITH AGENTS THAT HAD NOT CONVERGED.** C4 is D2's design at 300 000 steps,
> one variable changed; every C4 agent retraced its D2 twin bit for bit through
> 50 000 steps (80 of 80). Preregistered in `results/PREREGISTRATION_C4.md`
> (`79568e2`) before any C4 agent trained.
>
> ```
> python analyse_c4.py     3 of 8 positive   mean +30.2   median -1.3   sd 139.9
>   below the MEI: sign p 0.0352 (7 of 8)   permutation p 0.3867  <- disagree
>   cell SMALLER THAN THE MEI   convergence NOT-CONVERGED   5c p 0.6367
> ```
>
> - **The sentence that may be said** (C4 section 2a, fixed before training):
>   *"Preview's effect is below the MEI at 300 000 steps: (i) is supported AT
>   THIS BUDGET. The agents were still changing, so (ii) is not ruled out."*
>   (i) reads "with one grade step per episode". Never "preview does not help".
> - **It hangs on one seed:** seed 0 carries +360.6 (its blinded agent got worse
>   with training). Most seeds show no benefit, one shows a large one.
> - **Supervision, separately:** beats `current-grade` on the median (8 of 8
>   sighted, 7 of 8 blinded), not on the worst episode.
> - **Next is a TEAM DECISION** — a longer budget or more (NEW) seeds, one at a
>   time. `NEXT_SESSION_2026-09-24.md` carries both with their costs;
>   `python power_analysis.py`, the C4 section, prints the power figures.
> - `runs/`, `runs_d2/` and `runs_c4/` are CLOSED experiments; the tools refuse
>   new work in them. `runs_c4/` is backed up outside the repo
>   (`GRAD-agent-backups/2026-09-24/runs_c4`, 587 files, sha-checked).
>
> Full account: `PREREGISTRATION_C4.md` section 11. The D2 box below is D2's own,
> kept as written.

### Phase D2, 22–23 September — the box below is D2's own, kept as written

> **PHASE D2 HAS RUN, AND IT REMOVES PHASE D'S WORST LIMIT WITHOUT CHANGING THE
> ANSWER.** Phase D's blinded arm could memorise one fixed road (limit 7 below).
> D2 re-ran the same ablation on a **randomised climb** — start 120–300 s, grade
> 12–16 %, drawn per episode — under `results/PREREGISTRATION_D2.md`, committed
> before any D2 agent trained, with the **minimum effect of interest set in
> advance at 50 damage units** (Jad, 22 Sep). `check_random_road.py` verified the
> blind arm is blind: identical observations on every road until its climb comes.
>
> ```
> Phase D2   positive 4 of 8   mean +6.4   sign p = 0.6367   perm p = 0.4688
>            below the MEI: sign p = 0.1445 (6 of 8 seeds under 50)   -> INCONCLUSIVE
>            sd of the paired differences 98.8   (Phase D: 214.4)
> ```
>
> - **Removing the memorisable road did not pull the arms apart**, so the design
>   flaw is not what hid a preview effect. Left: preview buys little here, or C1
>   agents cannot learn to use it. **INCONCLUSIVE, not "preview does not help"**:
>   eight seeds have power 0.24 against 50 units (`python power_analysis.py`).
> - **The spread halved, and the preregistration predicted it would not.** Say so.
>   It means 80 % power against 50 units now needs ~42 seeds per arm, not 186.
> - **Supervision, the separate claim:** the sighted agent beats `current-grade`
>   on 8 of 8 seeds (+2.3 to +28.8 points), and so does every BLIND agent — the
>   gain over the hand-written comparator does not need the preview channel.
> - **Limit 10, checked:** five agents burn less fuel than the baseline ECU, and
>   `python check_d2_tracking.py` shows none of them is refusing torque (0 of 16
>   track more than one point worse than the baseline). D2's damage figures read
>   as protection.
> - Phase D's null is ALSO INCONCLUSIVE under the MEI rule — labelled post-hoc,
>   because its MEI was set after its result.
>
> Reproduce: `python analyse_phase_d2.py` (both experiments, side by side). The
> full account: `results/PREREGISTRATION_D2.md` section 11, and `CHECKPOINT.md`,
> session of 22–23 September.

### Phase D, 21–22 September — the box below is Phase D's own, kept as written

> **PHASE D HAS RUN AND THE PROJECT HAS ITS RESULT. It is a null, and a null is
> a result.** Sixteen agents — eight seeds per arm, sighted and blinded — were
> trained on the corrected ZF plant under `results/PREREGISTRATION.md`, which
> was committed **before any of them started**.
>
> ```
> positive (preview helped) : 5 of 8        mean difference : +4.8 damage units
> exact one-sided sign test   p = 0.3633
> exact paired permutation    p = 0.4922     alpha 0.05 -> NOT SIGNIFICANT
> ```
>
> **Preview cannot be shown to help.** The seed-to-seed spread is tens of times
> the effect: seed 3 says preview saves 387 damage units, seed 5 says it costs
> 288. A mean of +4.8 across that is noise — and separating a result from a
> coincidence is the entire reason eight seeds were run rather than one.
>
> **SEPARATELY, AND IT IS A DIFFERENT CLAIM:** the trained agent beats the
> `current-grade` comparator by **+29 to +34 points** on five of eight seeds and
> is positive on seven of eight. **Learned supervision works; PREVIEW
> specifically is what cannot be shown.** Do not let the first be read as
> evidence for the second — that conflation is `AUDIT.md` C3.
>
> **AND SAY THE TRAINING BUDGET IN THE SAME BREATH AS THE NULL.** These are
> **C1** agents — 50 000 steps, which `train.py` calls "the first bad run",
> 11 training episodes each. A null from an undertrained agent and a null from a
> converged one are different claims, and 11 episodes cannot tell them apart.
> The defensible sentence is *with agents trained to the C1 budget, preview does
> not separate from seed noise* — not *preview does not help*. Settling it means
> the same sixteen runs at 300 000 steps, which is a SECOND experiment with its
> own preregistration. `results/PREREGISTRATION.md` limit 6.
>
> **AND THE BLINDED ARM IS NOT BLIND — the most serious limit, found 22 Sep and
> verified directly.** The road is the same hill at the same second (t = 180 s)
> in every training and evaluation episode, and the blind agent's thermal state
> takes a distinct value at every step, so it is a clock on a road it can
> memorise. **Phase D therefore compared an explicit preview channel with an
> implicit one — not foresight with none.** Whether the blind agents used it is
> unmeasured, and that is the point: four explanations for the null are live and
> this experiment separates none. **The cheap decisive fix, before C4:**
> randomise the climb's start time and grade per episode, so that the preview
> channel is the only route to knowing when the hill comes.
> `results/PREREGISTRATION.md` limits 7 and 8.
>
> **Do not rescue the null with H/τ.** Phase D sits at H/τ ≈ 0.23–0.62 depending
> on the phase, and the project's only H/τ curve (void) puts the LARGEST preview
> value near 0.6 — so on the repository's own numbers the null is in tension
> with the theory, not consistent with it. That reading was drafted, checked and
> refuted on 22 September; limit 8 records why.
>
> Reproduce in seconds: `python analyse_phase_d.py`.
> The full account is `CHECKPOINT.md`, entry of 21–22 September.

