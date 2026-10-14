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


# Part B — CHECKPOINT.md as it stood on 14 October 2026, rotated verbatim

Every session entry from 9 September to 14 October, in the order the file held
them. The new `CHECKPOINT.md` carries the current state only.

# CHECKPOINT.md — state as of 28 September 2026 (evening)

**What this file is for:** a dated snapshot of where the work stands and what was
verified when. `CLAUDE.md` is the permanent handoff and the mistake log — the
rules and the traps, written to outlive any one week. This file is the diary of a
particular day, and it is meant to go out of date. Where the two disagree,
`CLAUDE.md` and the scripts win. Regenerate the numbers rather than trusting this
file if it is more than a week old.

> **10 September, v16 and its audit.** The load constant `k` is now derived
> rather than fitted, and the residual reads 1.4 % with zero free parameters.
> An audit of that change found it measures no part of the plant, and that the
> intake temperature channel reads compressor-outlet air. See the section at the
> bottom of this file and mistakes 12 and 13 in `CLAUDE.md`. `AUDIT_2026-09-10.md`
> was one of the five duplicates deleted on 11 September; what it found is in
> those two mistakes. The repository is now on GitHub at `JadFelemban4/GRAD-project`,
> private.

> **11 September, v17 and a document sweep.** The charge-temperature correction
> shipped, the operating points moved down to **30–75 kPa**, and every tracked
> document was swept against the data. See the 11 September section at the
> bottom of this file.

<!-- RETIRED-OK: 175.5, 9 -- the manifest as it stood that day -->
> **14 September, the citation pass, the live app and a ninth drive.**
> `REFERENCES.md` now records, row by row, which of `validate.py`'s eleven
> bands have a source and which do not — **seven do not**. `app/` runs the
> same physics alongside the car. `pull01` takes the manifest to **nine
> drives, 175.5 minutes** and adds zero samples by design. Two findings
> change what the model may claim: the B58 has **no thermostat**, and the
> compression ratio depends on an engine version nobody has recorded. See the
> last section of this file.

<!-- RETIRED-OK: 175.5, 9 -- the manifest as it stood that day -->
> **13–16 September, v19, the ninth drive and the live app.** `pull01` joined
> `logs/raw/`, taking the manifest to **nine drives, 175.5 minutes** — it
> contributes zero samples and zero operating points by design, so no
> calibration figure moved. `app/`, the live supervisor, was imported and then
> hardened; two defects in it are now **mistakes 14 and 15** in `CLAUDE.md`, and
> a third, **mistake 16**, is about the release archive that carried it. See the
> section at the bottom of this file.

<!-- RETIRED-OK: 295.0, 10 -- the figures of that session, before the merge of 30 September -->
*(Note added 22 September 2026: the two boxes above give the manifest as it
stood on their own dates. An earlier document sweep had overwritten them with
the later total — in the first box a pairing that was never true on any date;
the figures of the day are restored. `drive10` later took the manifest to ten drives, 295.0
minutes — see `CLAUDE.md`.)*

---

## Phase status

<!-- RETIRED-OK: 0.837 -->
*(Written 16 September 2026. Row B was updated on 19 September (commit
`6e40cd8`, the tenth drive) to 295.0 min, 26 points and derived k 0.831, and
its fitted k 0.837 was not; the other rows are as they stood on 16 September.
Agents have since been trained to the C1 budget and Phase D has run and
returned a null, with a blinded arm that was not blind — `CLAUDE.md` carries
the current table.)*

<!-- RETIRED-OK: 0.837, 46 -- figures of that day, superseded; see FULL_RUN.txt -->
| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — 1.4 % load residual with k derived (0.831, zero free parameters), 1.1 % with k fitted (0.839, one). 26 pooled points, 30–75 kPa, 321.7 min logged over eleven drives. Since 28 Sep the constants the logs can set are DERIVED from them (`derive_params.py`); `validate.py` 8 of 11. Read mistake 12 before quoting the residual |
| C · get an agent to learn | **retrain ready, not run.** New road every episode, dt = 1.0. The ten agents in `runs/` are a record (110 km/h, dt 0.2, one road, an older plant) |
| D · baselines and the ablation | protocol exists (`evaluate.py`, twenty frozen episodes, now with a thermal-only damage column). **No valid result yet. This is the floor of the project** |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | measurable again (the scenario binds); `generality_test.py` now reports preview over CURRENT-GRADE, the honest comparator. Not before D |
| G · writing | not started |
| **APP · live supervisor** | **working and tested.** `app/` runs this same physics beside the car and estimates turbine temperature. A SECOND deliverable — it does not advance D |

**Phase D is the passing bar.** Validated simulator + agent beating two baselines
+ an ablation isolating preview. Do not start E or F until D produces a table.

---

## Full verification run — 9 September 2026

<!-- RETIRED-OK: section 829.2, 548.6, 437.6, 23, 16.5, 18.0, 26.0 -->

Every script in the repo was executed end to end. **All eight passed.**

<!-- RETIRED-OK: 295.0, 10 -- the figures of that session, before the merge of 30 September -->
| # | Script | Result |
|---|---|---|
| 1 | `plant.py` | ✅ four sweeps; torque 431–514 Nm across the boosted sweep |
| 2 | `validate.py` | ✅ **8 of 11** inside band; τ_turb 48.0 s; 2997.5 cc |
| 3 | `check_premise.py` | ✅ **829.2 · 548.6 · 437.6 · 548.6** |
| 4 | `verify_docs.py` | ✅ every published figure matched. Run it and read the total it prints |
| 5 | `test_reward.py` | ✅ **4 of 4** |
| 6 | `build_dataset.py` | ✅ 295.0 min, 10 drives, 23 points |
| 7 | `compare_log.py` | ✅ **PASS** — 1.4 % load residual with k derived, 1.1 % with k fitted |
| 8 | `generality_test.py` | ✅ H2 table reproduced: 16.5 / 18.0 / 26.0 pts |

Nothing in the repository is stale. Every published figure regenerates.

### The premise check, in full

<!-- RETIRED-OK: section 829.2, 548.6, 437.6, 33.8, 47.2, 13.4, 879 -->

Protection trigger **1123 K (850 °C)** — the knee of the turbine damage term.

| policy | fuel g | damage | peak turb °C | peak oil °C |
|---|---|---|---|---|
| baseline ECU (neutral trims) | 4091 | **829.2** | 879 | 128 |
| reactive protection | 4175 | **548.6** | 859 | 123 |
| predictive protection | 4314 | **437.6** | 852 | 109 |
| predictive, **preview disabled** | 4175 | **548.6** | 859 | 123 |

**The ablation held again.** Preview-disabled lands on reactive across *all four*
reported quantities, not just damage. Reactive cuts damage 33.8 %, predictive
47.2 % — **13.4 points**.

The cost is legible and worth quoting: predictive burns **139 g more fuel than
reactive** (+3.3 %) and **223 g more than baseline** (+5.5 %) to buy that damage
reduction, and it drops peak oil by **19 °C** where reactive manages 5 °C.

### The validation table

<!-- RETIRED-OK: dated record; best BSFC read 241.2 g/kWh until the converged cycle model, 239.9 since -->
| Quantity | Model | Published | Status |
|---|---|---|---|
| Displacement | 2997.5 cc | 2990–3000 | inside |
| MFB50 at MBT | 8.5° | 8–10 | inside |
| Best BSFC (λ1, knock-feasible) | 241.2 | 235–260 | inside |
| Knock-limited spark (3000 / 200 kPa) | 11.0° | 8–14 | inside |
| EGT cruise band, min | 714.5 °C | 600–750 | inside |
| EGT cruise band, max | 777.3 °C | 600–750 | **outside** |
| Turbine housing τ | 48.0 s | 40–120 | inside |
| Oil temp, sustained climb | 110.2 °C | 115–140 | **outside** |
| Oil τ | 16.0 s | 20–400 | **outside** |
| Coolant, thermostat-regulated | 94.5 °C | 88–108 | inside |
| Coolant apparent τ | 9.5 s | 1–600 | inside |

The three misses are documented in `validation_table.md` and are **not** to be
closed by tuning toward the band.

### The reward gate

| check | result | detail |
|---|---|---|
| neutral scores ≈ zero | PASS | −0.00438 (want \|r\| < 0.05) |
| refusing torque is punished | PASS | starver **−0.28044** vs neutral −0.00438 |
| disabling preview changes the observation | PASS | max \|Δobs\| = 1.44 |
| rewards are finite | PASS | 1499 / 1499 / 1499 steps |

For information, not pass/fail: a random policy scores −0.08197.

---

## Changes made on 9 September

Two fixes and one documentation correction. **No calculation changed; every
number above is identical before and after.**

### 1. `gymnasium` was not installed

Installed **1.3.0**. It is an active line in `requirements.txt` (only the SB3 and
torch lines are commented out), so this was a missing environment, not a missing
dependency declaration.

### 2. Console encoding — six scripts crashed or mangled their own output

`build_dataset.py` wrote all three CSVs successfully and **then died** printing
its summary table, because a Windows console defaults to cp1252 and cannot encode
`λ`. The data was fine; the run looked failed. `validate.py` printed `—` as `?`
in its title.

Fixed by forcing UTF-8 on stdout in the six scripts that print non-ASCII:
`build_dataset.py`, `validate.py`, `compare_log.py`, `extract_steady.py`,
`generality_test.py`, `train.py`.

All six re-run clean at exit code 0. **`train.py`'s patch is the one exception —
it is unverified at runtime**, because the script exits immediately with a clean
"stable-baselines3 is not installed" message and never reaches its print
statements. It compiles; it will be confirmed the first time SB3 is present.

An audit of all 13 scripts confirms **no script prints non-ASCII without the
guard**. The remaining seven confine theirs to comments and docstrings.

### 3. `CLAUDE.md` carried a stale drive count

<!-- RETIRED-OK: section 113, 7, 5, 8, 168.1 -->
The old sentence is quoted below deliberately, as the record of what was
corrected. `verify_docs.py` needs the marker above to know that.

It said "seven drives, 113 minutes, five carrying samples." The data says **eight
drives, 168.1 minutes, seven carrying samples**.

The old sentence was also wrong in a subtler way, and the correction records the
distinction: **`fb988991` does carry samples** — 16.3 minutes of them — but not
one of its windows survives the span and gap checks, so it contributes zero
*operating points*. Six carry samples; five carry points. Three different counts.

---

## Open problems, honestly stated

### 1. Phase F's H2b threshold rule does not survive the correct engine

<!-- RETIRED-OK: section 16.5, 18.0, 26.0 -->

H2b sets the constraint at the 80th percentile of the unprotected trace, which
assumes the temperature spends a *minority* of the episode near its peak. The
standard scenario is a sustained climb — nine of its twelve minutes at the top —
so p80 lands on the peak and the top three rows saturate at 100 % for both
policies.

Today's run confirms it, unchanged:

| C_turb J/K | τ s | H/τ | t_ref K | reactive | predictive | edge |
|---|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 2500 | 21.0 | 1.43 | 1152 | 100.0 % | 100.0 % | 0.0 |
| 6000 | 50.3 | 0.60 | 1146 | 100.0 % | 100.0 % | 0.0 |
| 18000 | 150.9 | 0.20 | 1022 | 0.0 % | 57.0 % | **57.0** |
| 60000 | 503.1 | 0.06 | 752 | 0.0 % | 9.7 % | 9.7 |

**Until the percentile rule is replaced, use the fixed-limit H2 table:**

| C_turb J/K | τ s | H/τ | reactive | predictive | preview edge |
|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 79.6 % | 96.1 % | 16.5 pts |
| 2500 | 21.0 | 1.43 | 78.7 % | 96.7 % | 18.0 pts |
| 6000 | 50.3 | 0.60 | 73.2 % | 99.1 % | **26.0 pts** |
| 18000 | 150.9 | 0.20 | — | — | never exceeds the limit |
| 60000 | 503.1 | 0.06 | — | — | never exceeds the limit |

Preview edge rises as τ grows — **16.5 → 18.0 → 26.0** as H/τ falls from 4.47 to
0.60 — then the component becomes massive enough that the constraint stops
binding. That is the direction the physical argument predicts.

**These numbers moved from 0.0 / 0.1 / 0.2 at the old 930 K trigger. Nothing
about the plant changed — only the threshold.** Report the threshold with every
preview figure.

### 2. Known limitations to state in the thesis, not fix quietly

- **Vehicle validation covers 30–75 kPa only.** Steady points require steady
  driving, which is light-load driving.
- **The boosted inversion is within 2 % of the car, once the charge temperature
  is right.** 587 modelled samples against 887 logged `Boost pressure` readings
  above 200 kPa, logged median 226 kPa: the raw sensor gives 279.5 kPa,
  **+23.7 %**; `plant.charge_temperature()` gives 232.7 kPa, **+1.9 %**. An
  ambient + 8 K rule scores 227.5 kPa, +0.7 %, and was rejected as a knob tuned
  to hit the target. What is still uncertain under boost is the MAF ceiling at
  1020 kg/h and the logger's round-robin sampling.
- **Peak power is not a prediction.** Manifold pressure is an input. An operating
  line is not a compressor map.
- **The compressor envelope is unmeasured above 0.303 kg/s corrected**, because
  that is where the MAF saturates. Only the 0.33–0.36 kg/s bin remains empty and
  no drive can fill it with this sensor.
- **The radiator is not identifiable on this car**, and the channel census proves
  it: every water-pump and fan-actual channel is all-zero. A constrained fit
  gives R² = 0.157 with a negative ram coefficient. Stop trying.
<!-- RETIRED-OK: 103 -->
- **Oil above 117 °C is extrapolation.** That is the hottest oil anywhere in the
  logs, on `7475b5d7`; 111 °C after the filter. This line said 103 °C until
  10 September, which was the figure before the eighth drive arrived — quoted
  here on purpose, as the record of the correction.
- **Steady points are steady for fast quantities only.** The 60 s window is fully
  settled for air, lambda, spark and manifold pressure, and reaches just **71 %**
  of a turbine thermal step (τ = 48 s). Never validate a thermal quantity at a
  steady point.
- **Enrichment uses dwell above `ENR_LOAD` = 180 kPa as a proxy** for turbine
  inlet temperature, which this vehicle does not expose. The gate moved from
  200 kPa with the manifold-pressure *definition*, not with the physics, and
  selects the same 1055 samples. The weakest cell of the fit is 3500–4500 rpm at
  **long** dwell: n = 47, observed 0.90 against a modelled 0.93.

---

## What to do next, in order

1. `pip install "stable-baselines3[extra]"` — **2 minutes**. Also confirms the
   last unverified encoding patch.
2. `python train.py --steps 50000 --seed 0` — **about 4.6 hours on one CPU core**,
   measured not guessed: the environment runs at 19.5 steps/s alone and 3.0
   steps/s once SAC's gradient updates are included. **Plan an overnight, not an
   evening.** Checkpoints land every 10 000 steps. Expect a poor result; it
   running is the point.
3. `python test_reward.py` before trusting any training curve.
4. **Five seeds, one per team member, overnight** — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. **Phase D**: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds.

> **Once the 20 evaluation episodes are fixed they never change.** Changing the
> test set after seeing results is the one mistake this project cannot recover
> from.

Full detail: [handoff.md](handoff.md).

---

## Session of 9–10 September 2026 — v16, and an audit of it

### What was run

<!-- RETIRED-OK: section 829.2, 548.6, 437.6 -->

`engine-supervisor-v16.zip` was unpacked over the working copy. All 38 archive
files are byte-identical to the archive. All six checks were run in order.

| script | result |
|---|---|
| `check_premise.py` | 829.2 · 548.6 · 437.6 · 548.6 at 1123 K; rows 2 and 4 equal to the last float bit |
| `verify_docs.py` | failed on three documents the unzip left behind, then passed once they were corrected. Run it and read the total it prints |
| `test_reward.py` | 4 of 4, neutral −0.00438, starver −0.28044 |
| `check_map.py` | 85 of 85 adjacent pairs monotonic, 6 unreachable, 0 `knk` |
| `validate.py` | 8 of 11 inside band, τ_turb 48.0 s, 2997.5 cc |
| `compare_log.py` | derived 1.4 %, fitted 1.1 % |

**The preview identity was checked below the printed decimals.** A probe compared
the reactive and preview-disabled rollouts at full float precision. All seven
returned fields are bit-identical: fuel `4175.220663624409`, damage
`548.6498477371352`, peak turbine `858.6302607939912`, knock `0`.

### Why `verify_docs.py` had failed

Not v16's fault. The archive holds 38 files and does not contain the six
documents written on 9 September, so unzipping left them behind unchanged while
everything else moved to v16. Three of them still carried retired figures. The
checker passed on a clean extraction of the archive alone, all along.

<!-- RETIRED-OK: 178 -- the dwell figure of that day, superseded; see FULL_RUN.txt -->
Fixed on 10 September: `Context.md` and `DATA-MODEL.md` — both deleted on
11 September as duplicates — had a live seven-drive dwell figure corrected, and the historical quotation in this file was marked
`RETIRED-OK`, which is what the checker requires for a deliberate mention. That
dwell figure has since been recomputed again on the corrected manifold-pressure
scale, and now reads **178 s above 207 kPa**.

The checker itself was reworked after this run — see the 11 September section —
so its totals from that day do not compare with today's.

### What the audit found

Two entries were added to the mistake log in `CLAUDE.md`.

- **Mistake 12 — the load residual tests no part of the plant.** Because
  `map_from_airflow()` inverts the exact relation `run_cycle()` uses, volumetric
  efficiency, residual fraction and intake temperature all cancel out of the
  comparison. The 1.4 % is the ECU's filling channel against its own air-mass
  channel. Forcing volumetric efficiency to 0.5 leaves the residual at 1.3740 %.
  There is no part-load test of the breathing model anywhere in the repository.
- **Mistake 13 — the intake temperature channel reads compressor-outlet air.**
  The B58's charge cooler sits inside the intake manifold, downstream of the
  throttle, so the "before throttle valve" sensor is before the cooler. A
  modelled post-cooler temperature in the inversion lands on the logged boost
  pressure. Recomputed from the shipped data on 11 September, over 587 modelled
  samples against 887 logged readings above 200 kPa whose median is 226 kPa:
  **232.7 kPa, +1.9 %**, where the raw sensor gives 279.5 kPa, **+23.7 %**. The
  boost gap was the temperature, not the breathing model.

### Stale figures corrected the same day

<!-- RETIRED-OK -->
This paragraph is the record of what changed on 10 September, so every arrow
reads old → new *as of that day*. Two of those new values have since moved
again; the note underneath carries the current ones.

<!-- RETIRED-OK: 192, 31, 82, 517, 5, 33.8, 33.9, 22, 2.8, 2.3, 17, 79, 103 -->
Oil extrapolation 103 → **117 °C**. Enrichment v4 fitted on seven → **eight**
drives. MAF ceiling 192 samples on four → **517 on five** drives. Compressor fit
30 534 → **74 013** quasi-steady samples. Vehicle validation 31–79 → **31–82 kPa**.
Load residual 2.3 % over 17 points → **1.4 % and 2.8 % over 22**. Reactive damage
reduction 33.9 → **33.8 %**. The claim that the inversion and the logged boost
channel agree inside 4.4 % below 80 kPa was removed; both pressure channels are
pre-throttle and disagree by 44–52 % at the steady points.

**Current values, 11 September.** The charge-temperature correction moved the
point span again: it is **30–75 kPa** now, not 31–82. And the fitted residual is
**1.1 %** against the derived **1.4 %**, over the same 23 points — dropping the
fitted parameter makes the residual rise, not fall.

### Also corrected, in the second pass

<!-- RETIRED-OK -->
A record of edits made on 10 September; the superseded values are named on
purpose, because they are the thing that was corrected.

<!-- RETIRED-OK: 8, 168.1, 1.163, 2.3 -->
`validation_table.md` section E now says eight drives and 168.1 minutes, and its
MAF and manifold-pressure items carry the current counts. Its thermal test
condition keeps the 7.6 g/s figure but now states plainly that the condition
sits **below** the hardest sustained 60 s fuel flow in the logs — **8.7 g/s** —
rather than above it. `README.md` moved off the 2.3 % residual in both places.
The module docstring of `engine_env.py` and two comments in `build_dataset.py`
moved off the seven-drive correlations and the 1.163 combustion-air ratio, which
is **1.095** on the current dataset; both are comments, and `test_reward.py` and
`build_dataset.py` were re-run to prove it. The regenerated `data/` files are
byte-identical to what was there before.

### Still open — these need a decision, not a correction

- **`compare_log.py --map-from-log` scores zero rows** on
  `data/master_points.csv`: the alias table has no entry for the manifold
  pressure channel under the short schema, so every row is dropped, the table
  prints empty, and the script still exits 0. `CLAUDE.md` says this mode exists
  to reproduce the pre-throttle failure for the thesis; it cannot, on the
  canonical dataset. Fail-open, the same shape as mistake 9.
- **`compare_log.py` tells the reader to look at volumetric efficiency** when
  the load residual is large. That quantity cancels, so the residual cannot grow
  for that reason. The advice is unreachable.
- **`validate.py` still prints that there is no compressor flow ceiling**,
  although `plant.boost_ceiling_kpa` exists and bounds the model.
- **`check_map.py` schedules lambda by load**, which mistake 4 identifies as the
  wrong variable. The effect is at most one degree per cell and no cell becomes
  `knk`, so no published figure changes.
- **The B58 cooler layout rests on vendor documentation**, not a BMW service
  source. Get the primary source before the thesis leans on it. The measured
  numbers behind mistake 13 stand either way.
- **Nothing asserts the 1.4 % itself.** `verify_docs.py` checks the constant,
  the derived value and the excluded alternative, but not the residual, so that
  figure can drift without the checker noticing.

---

## Session of 11 September 2026 — v17, and a sweep of every document

### What shipped: the charge-temperature correction

<!-- RETIRED-OK: section 0.837, 23, 829.2, 548.6, 437.6, 33.8, 47.2, 13.4 -->

`build_dataset.py` and `compare_log.py` no longer feed the pre-throttle intake
temperature channel into `map_from_airflow()`. That channel is a compressor
outlet — mistake 13 in `CLAUDE.md` — and the inversion now uses
`plant.charge_temperature()`. What moved, recomputed from the shipped data:

<!-- RETIRED-OK: 295.0, 10 -- the figures of that session, before the merge of 30 September -->
| quantity | value after v17 |
|---|---|
| operating-point span | **30–75 kPa**, 23 points, 295.0 min over 10 drives |
| load residual, k **derived** 0.831 | **1.4 %**, zero free parameters |
| load residual, k **fitted** 0.837 | **1.1 %**, one free parameter |
| a 20 °C reference state would need | k = 0.890 — the fit excludes it |
| enrichment gate `ENR_LOAD` | 180 kPa, 1055 samples above it |
| boosted inversion against the car | 232.7 kPa modelled against a logged median of 226, **+1.9 %** |

**Dropping the fitted parameter makes the residual rise, 1.1 → 1.4 %.** Say it
that way round. The derived form is not the more accurate one; it is the more
falsifiable one, because it has no constant to absorb an error with — which is
why it would have caught the wrong-engine bug on day one and the fitted form did
not.

The premise result did not move: **829.2 · 548.6 · 437.6 · 548.6**, reactive
cutting damage 33.8 % against predictive 47.2 %, a **13.4-point** gap. The
simulator never read that sensor; `engine_env` models its own charge temperature.

### The document sweep

**55 stale figures were found across the tracked documents.** Almost none of them
were in the code — the code had moved and the prose had not, which is mistake 11
happening at scale instead of in six places.

`verify_docs.py` was reworked in answer to that. It used to compare figures
recomputed from the data against constants written inside itself, which proves
the data has not drifted and says nothing about what any document claims. It now
recomputes the published figures from the shipped data, then **opens every
tracked document and compares what is written there against those numbers**,
reporting by file and line, and it still greps every document for retired values.
A passage that quotes a superseded figure on purpose must carry
`<!-- RETIRED-OK -->` in its section, which is an assertion that the passage is
history.

Run it and read the total it prints. **Do not write a check count into any
document** — it moves every time a figure is added, and a count in prose is one
more number to go stale.

### Five documents deleted, two kept

Seven overlapping status documents had accumulated. Five were duplicates of
`CLAUDE.md` carrying older numbers and were deleted. This file and
[handoff.md](handoff.md) were restored at the owner's request, because they are
wanted for the write-up, and both were brought current the same day.

They are now part of the tracked set that `verify_docs.py` scans, and that is the
condition of keeping them: **a second document is only safe while something
checks it.** The division of labour is stated at the top of this file —
`CLAUDE.md` is the permanent handoff and mistake log, this file is a dated
snapshot. What belongs in the first should not be restated in the second, which
is how five duplicates came to exist in the first place.

---

## Session of 14 September 2026 — the citation pass, and a merge

Two pieces of work met in one merge commit. They were done independently and
they are reported separately here, because only one of them was verified by the
person writing this section.

### What the citation pass was for

`validate.py` scores the model against eleven "published bands". Until this day
the repository cited **one** source for all eleven: the word "Heywood" in a code
comment, with no edition and no page. An examiner asking *"where does 115–140 °C
come from?"* had no answer.

`REFERENCES.md` replaces that. It is written for a reader who is not an
internal-combustion specialist — every term carries a plain-English gloss — and
it sorts every number in the project into four kinds: measured by us, general
engine physics, specific to the B58, or assumed. It is tracked by
`verify_docs.py`, so the figures it quotes from our own logs cannot drift.

### What was promoted, and on what evidence

Sources were opened, not remembered. Each row carries the page, column or
paragraph the claim was read from.

| what | status now | where it was read |
|---|---|---|
| Bosch relative air charge | **CONFIRMED** | US 6,588,261 B1, col. 3 l. 55 – col. 4 l. 2: *"rl = ma/m_norm … under the standard conditions: Tn=273 K, Pn=1013 hPa"* |
| Bore 82.0, stroke 94.6, displacement | **CONFIRMED** | Toyota Australia spec table GTP-009045 p. 1; BMW Canada Z4 2020MY guide p. 2; BMW 3 Series 05/2015 p. 7 |
| Row 2, MFB50 at MBT 8–10° | **CONFIRMED** as the common rule | Zhu, Haskara & Winkelman, IEEE TCST 15(3) 2007, p. 417 |
| Row 7, turbine τ 40–120 s | **PARTIAL** | Burke et al., IJHFF 52 (2015) §5.3 — housing heat flow settles from ~7 kW to ~3.6 kW within three minutes, bounding τ above at roughly 45–60 s |

Two corrections fell out of re-checking the six records the file already called
CONFIRMED: the Wiebe book's publisher is **Verlag Technik** (no catalogue that
could be opened shows the "VEB" prefix the file carried), and Chen & Flynn's SAE
650733 is titled *"Development of a Single Cylinder Compression Ignition Research
Engine"* — a paper about building a research engine, whose abstract never
mentions friction. **That the FMEP correlation in `plant.py` comes from a page of
it has not been checked.**

### What was searched for and not found — this is the useful half

<!-- RETIRED-OK: dated record; best BSFC read 241.2 g/kWh until the converged cycle model, 239.9 since -->
- **Row 3, best BSFC 235–260 g/kWh.** No source states it. Heywood gives
  **270 g/kWh**, above the band; a 2018 SwRI/EPA turbocharged GDI engine measures
  **233**, below it. Our 241.2 sits between them. The band was **not** widened to
  swallow the evidence; it is labelled engineering judgement and bracketed.
- **Row 4, knock-limited spark 8–14°.** Nothing admissible, which is what the
  task expected. Douaud & Eyzat supply the knock *model*, not this band. Drop the
  row or relabel it an internal consistency check.
- **Rows 5, 6, 8, 9 and 11.** No source states a part-load exhaust-temperature
  range, a sustained-load oil band, or either time constant.

Seven of eleven bands therefore remain unsourced. **Say so in Chapter 3.**

### Two findings that change what the model may claim

**The B58 has no thermostat.** BMW's own training document (ST1505, information
status April 2015, §4.2) states that the conventional thermostat *"is replaced by
a so-called heat management module"* — a motor-driven rotary valve positioned by
the engine computer from the coolant and cylinder-head temperatures, with no wax
element and no published opening temperature. `thermal.py`'s `t_stat_open` = 88 °C
is therefore a **modelling equivalent** identified from the car's own coolant
channel (regulated 88–97 °C in every log), and must never be cited to BMW. It is
also a **third** reason the radiator is unidentifiable from the logs: the
radiator branch opening is a commanded valve angle, not a function of coolant
temperature, so even a coolant-flow signal would not close the heat equation
without the valve position.

**The compression ratio follows the engine version, not the model year.**
Manufacturer sheets on both sides print 10.2:1 beside the engine code
**B58B30O1** — the 285 kW / 382 hp engine, which is what `plant.py` models. But
Toyota UK's own technical specifications of Feb 2021, June 2022 and Feb 2024
print **11.0:1** for the 250 kW / 340 PS GR Supra 3.0 sold in Europe. **Nobody
has recorded which version this car is.** The rated output on its registration or
compliance plate settles it in one look; if it is the 250 kW car, the knock model
is running the wrong compression ratio. Third-party specification aggregators
splice the North American "382 hp" with the European "11.0:1" — such a listing is
two markets stitched together, not a manufacturer figure.

### Mistake 11 recurred a third time, and named two holes in the checker

<!-- RETIRED-OK: 295.0, 10 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK: section 168.1, 8, 175.5, 9 -->
This subsection names the superseded figure throughout, because the figure is
what was corrected. The current dataset is ten drives and 295.0 minutes.

`pull01` took the manifest from eight drives and 168.1 minutes to nine and
175.5. Seventeen lines were swept. **Five were not**, by two different routes:

- **Three escaped the regex.** The dataset-size pattern requires *pooled*,
  *dataset*, *manifest* or a drive count within thirty characters of the figure,
  so `REFERENCES.md`'s "168.1 minutes of OBD-II logs from our own car" matched
  nothing. The anchoring is the right trade — a looser pattern misreported the
  thermal fit's "three drives (80 minutes)" as a wrong total — but it means a
  figure in an unusual sentence is invisible.
- **Two escaped inside a `RETIRED-OK` paragraph.** The marker exempts its whole
  paragraph, and a live claim about the current dataset shared a paragraph with
  the retired figure the marker was there for.

**And nothing in `RETIRED` was guarding 168.1 at all** — the seven-drive entry
still named "eight drives, 168.1 minutes" as the value to use instead, so the
list pointed at a figure that had itself been superseded.

All five are corrected, the seven-drive entry points at ten drives, and `168.1`
is now a retired pattern in its own right. It deliberately does not match "eight
drives" alone: the enrichment map and the compressor fit genuinely rest on eight
drives of samples, because `pull01` contributes **zero** samples.

### Verification on the merged tree — every script re-run

<!-- RETIRED-OK: section 829.2, 548.6, 437.6, 36 -->

| script | result |
|---|---|
| `check_premise.py` | **829.2 · 548.6 · 437.6 · 548.6**, trigger 1123 K; rows 2 and 4 identical |
| `validate.py` | **8 of 11** inside band; every model value unchanged |
| `test_reward.py` | **4 of 4** pass; neutral −0.00438, starver −0.28044 |
| `compare_log.py` | **PASS** — 1.4 % residual, derived k 0.831 |
| `check_map.py` | 6 cells above the compressor ceiling, **0** reachable fail-open cells |
| `verify_docs.py` | **all 33 checks pass**; 29 retired figures guarded, 51 historical mentions marked |
| `app/test_replay.py` | **36 of 36** pass, including the read-only and no-raw-data-on-disk assertions |

The citation pass changed no code logic and no numeric value: the compiled
bytecode and every numeric constant of `thermal.py` and `validate.py` are
identical to the commit before it. Only `test_reward.py`'s unseeded
random-policy line moves run to run, and it is printed under the heading
"FOR INFORMATION, NOT A PASS/FAIL".

### Not verified by the author of this section

`app/` and the ninth drive came from the other half of the merge. `app/test_replay.py`
was run here and passes 36 of 36, but the app's design, its estimator and its
alert thresholds were not reviewed. `CLAUDE.md` describes it; read that before
changing it.

### Still open after this session

1. **Which engine version the car is.** Two minutes with the registration.
   Decides whether the compression ratio is right.
2. **Row 7's actual time constant.** Burke 2014, *J. Eng. Gas Turbines Power*
   136(10) 101511, should carry the turbine-node capacitance and conductances,
   giving a published C/UA to set against our 48.0 s and 6000 J/K.
3. **The MTZ article** (Landerl et al., *MTZ worldwide* 76(10) 2015, pp. 22–29),
   the only BMW-authored document on this engine. Library access. It may settle
   row 3 and replace the grey training document used for the thermostat finding.
4. **Phase C.** Still the next real step, and nothing has been trained yet.

## Session of 14–16 September 2026 — hardening the live app, and a document sweep

*(Overlaps the section above by a day. The two were done independently: that one
is the citation pass, this one is the app. Neither supersedes the other.)*

### What arrived

| thing | what it is |
|---|---|
| `logs/raw/pull01-20260913_093527.csv` | the **ninth** drive. Purpose-built, 7 channels, to settle mistake 13. Contributes **zero samples, zero operating points** — no coolant channel, so the warm filter excludes it |
| `app/` | the live supervisor: reader, estimator, alert engine, server, three pages |
| `DOC/`, `presentation/`, `REFERENCES.md` | from the branch, in parallel — the document reorganisation and the provenance file |

### The dataset now reads three different drive counts, and all three are right

<!-- RETIRED-OK -->
| population | count | used for |
|---|---|---|
| manifest | **9** drives, 295.0 min | "how much have we logged" |
| carrying usable samples | **6** | anything computed from `master_samples` |
| behind the fitted calibrations | **8** | enrichment, spark — `pull01` is not in them |

`verify_docs.py` asserts the first two separately. Quoting the wrong one is now
the easiest available mistake.

### What was verified, on the merged tree

<!-- RETIRED-OK: dated record; validate.py read 8 of 11 until rows 8-11 moved onto car data on 28 September -->
| # | Script | Result |
|---|---|---|
| 1 | `verify_docs.py` | ✅ **All 33 checks pass**, 228 figure mentions scanned across 22 tracked files |
| 2 | `validate.py` | ✅ **8 of 11** inside band — unchanged |
| 3 | `test_reward.py` | ✅ **4 of 4**; neutral −0.00438, unchanged |
| 4 | `python -m app.test_replay --full` | ✅ **46 of 46** |

`check_premise.py`, `build_dataset.py`, `compare_log.py` and `generality_test.py`
were not re-run this session: nothing under them changed, and `verify_docs.py`
recomputes their published figures from the shipped data and agrees. Re-run them
before a release rather than trusting this line.

### The app's own numbers, pinned so a regression is visible

Replaying `7475b5d7` end to end:

<!-- RETIRED-OK: 884.9, 13 -- the app pins of that session, superseded; see FULL_RUN.txt -->
| quantity | value |
|---|---|
| samples estimated | **14278 of 14340** (99.7 % of samples with the engine running) |
| peak estimated turbine | **884.9 °C** — a MODEL OUTPUT, not a reading |
| alerts | **13 thermal · 0 mismatch · 19 novel** |
| seed forgotten after | **461 s** — not the 145 s the code used to assume |

<!-- RETIRED-OK: 593.7 -->
And on `pull01`, the fast regression: 2186 of 2193 estimated, peak **593.7 °C**,
4 novel, seed forgotten at 172 s.

**None of these is evidence about the car.** The turbine figure is a model
output with an assumed heat capacity and the alert counts are a property of
thresholds we chose. They are pinned so that a change to the pipeline shows up,
which is a different job from being a result.

### Three defects found and fixed — the detail is in CLAUDE.md mistakes 14–16

1. **The mismatch detector was measuring the throttle.** 55 alerts on
   `7475b5d7` looked like an over-sensitive threshold; the firing condition was
   actually true for **95.7 % of the drive** at a median of −52 %, because
   `Boost pressure` is a pre-throttle channel. Fixed with three validity gates,
   not a threshold change: **55 → 0**. The threshold did move, 15 % → 25 %, for
   a separate and measured reason.
2. **The app reported a turbine temperature its own physics called impossible.**
   The 500 °C seed sat outside the ambient-to-EGT bracket — on `pull01`, 300 K
   outside it. The fixed 145 s warm-up timer also used τ = 48 s, which is the
   *loaded* time constant; at cruise it is 151 s and at idle 239 s.
3. **The v19 archive was an older snapshot of everything except `app/`.**
   Unzipping it over the branch would have reverted a fortnight of document
   work, including three figures that had already been corrected once. They are
   now guarded by `verify_docs.RETIRED`.

### Two defects in `verify_docs.py` itself, both fixed here

- **It crashed while reporting.** The new document scanner echoes the offending
  line back; line 54 of this file contains a tick emoji; on a cp1252 console
  that raised `UnicodeEncodeError` and killed the run **after every check had
  already computed correctly**. Third occurrence of the character-encoding bug
  in this repository, and the worst place for it.
- **Its MAF-ceiling drive count and its MAF-ceiling sample count were counting
  different populations** — raw files against the warm-filtered dataset. Adding
  `pull01`, which pins 56 times in its raw log, pushed them apart: 6 drives
  against 547 samples over 5. Both halves now count the same set.

### What this session did NOT do

- **No training run.** Phase C is still where it was, and Phase D is still the
  floor of the project. The app is a second deliverable and it is not on that
  path — see the backlog at the end of `CLAUDE.md`'s plan section.
- **No live-car test.** Everything about the app is replay. The first item in
  its backlog is one drive with `--live`, and it is the only item that can find
  something replay cannot.
- **No fault has ever been shown to the mismatch detector.** Nothing in nine
  drives is broken, so every number behind it is a false-positive rate, not a
  detection rate. Say that in the thesis rather than implying validation.

---

## Session of 17 September 2026 — the merge, and a sweep behind the audit fixes

**No code behaviour changed.** One constant moved (`train.py`'s printed
estimate) and one guard was added. Everything else is documents.

### What arrived

`main` was **behind both branches** and carried no commit they lacked.
`JMF-2340550` held everything but one commit; `JMF-new-plan` added `aca526d`,
which only creates `ABSTRACT.md`, `CONTROL_SCOPE.md`, three `DOC/Abstract_*.docx`
and `presentation/plan.html`. Fast-forward, then merge: **zero conflicts**.

### What was verified, on the merged tree

Every script run, output read, nothing taken from a document:

<!-- RETIRED-OK: 1.3, 23, 294.2, 812 -- the run of that session, superseded; see FULL_RUN.txt -->
| script | result |
|---|---|
| `verify_docs.py` | **38 of 38**, 311 figure mentions, 25 files |
| `test_reward.py` | **4 of 4**; neutral −0.00870, starver −0.49080 |
| `python -m app.test_replay` | **49 of 49** |
| `compare_log.py` | PASS, 1.3 % derived / 1.1 % fitted over 23 points |
| `check_premise.py` | baseline **294.2 at 812 °C**, constraint does not bind |
| `train.py --steps 3000` | ran; SAC trains |

### Six stale figures found and swept

All the same failure: the 16 September audit fixes moved the code and no
document followed. **Mistake 11 for the fifth time.**

<!-- RETIRED-OK: 256.5, 801, 2.2, 294.2, 812, 1.8, 884.9, 36, 46 -->
| where | said | prints |
|---|---|---|
| CLAUDE.md, README.md, handoff.md | 256.5 · 801 °C · 2.2 pts | **294.2 · 812 °C · 1.8 pts** |
| CLAUDE.md, handoff.md | 36 of 36 / 46 of 46, peak 884.9 °C | **49 of 49**, peak **890.6 °C** |
| CLAUDE.md phase table + app section | "six known bugs", "none fixed" | **all six fixed** |
| presentation/README.md | 801 °C, "thirteen mistakes" | 812 °C, sixteen |

### Two measurements taken this session

<!-- RETIRED-OK: 0.351, 172.6, 812 -- a dated record of what was measured that day; the
     tenth drive (Taif) took the total to 292.0 min and 0.206 % on 19 Sep -->
**Every drive replayed against the protection trigger.** One of nine binds:
`7475b5d7` peaks at 890.6 °C, **41 K above**, for **36 s of 172.6 replayed
minutes — 0.351 %**. The synthetic climb reaches 812 °C and misses by 38 K, so
**the car's own driving is 78 K hotter than the scenario written to stress it.**
The scenario is what is wrong, not the trigger.

**The training rate, re-timed.** `STEPS_PER_S` was 3.0, quoted as "4.6 hours on
one CPU core". Measured over 2000 SAC steps with updates running: **19.19
steps/s at one thread, 18.14 at six.** Both halves of the old claim were wrong
and neither is a hardware difference — one thread is marginally FASTER than six,
and the gradient updates cost ~2 %, not 6.5×. **Phase D is ~7.5 hours, one
evening, not "five overnights twice".** `plant.DTHETA_DEG` is what sets the
cost; it was halved on 16 September.

### Two holes left open on purpose

<!-- RETIRED-OK: 829.2, 548.6, 437.6 -- naming the void figures IS the finding -->
- **`presentation/index.html`** still hard-codes 829.2 ×24, 548.6 ×70,
  437.6 ×16. Fixing it means regenerating the page, not editing a document.
- **`check_retired()` never opens it.** It builds its own list from
  `glob("**/*.md")` plus the root `*.py`, while `TRACKED_DOCS` — used by the
  FIGURE scan — does include the page. **Two scans, two file lists, and only one
  was fixed** when AUDIT.md L11 was closed. Measured: the retired scan opens
  25 files; 77 lines of that page would fire six retired patterns.

### One guard added, and it is not a figure

<!-- RETIRED-OK: the retired string is the subject of this paragraph -->
`King Abdulaziz` joins `RETIRED`. CLAUDE.md line 13 carried the wrong university
until `d57f3da` — inside a commit about `REFERENCES.md`, so the change is
invisible from the log. Confirmed with the team: **University of Jeddah**.
Verified by planting the string and watching the run fail. `DOC/*.docx`,
`DOC/*.pdf` and `presentation/index.html` were checked by hand; **none carries a
university name at all**, which is open if the submission template needs one.

### What this session did NOT do

- **No Phase D.** Nothing trained beyond a 3000-step smoke run.
- **No scenario chosen.** That is the one blocker, and it is a team decision:
  pick it from something physical, never by turning a knob until the gap looks
  good.
<!-- RETIRED-OK: 829.2, 548.6 -- the figures named here are the ones the run rejected -->
- **`verify_docs.py` caught the author mid-edit**, correctly, when explaining
  the void headline re-quoted 829.2 and 548.6. The errata came out with the
  figure. **When a number goes void, its corrections go with it.**

---

## Session of 18-19 September 2026 — the scenario, a gearbox defect, and the first ablation

<!-- RETIRED-OK: 11.7 -- naming the void figure IS this note -->
*(Note added 22 September 2026, the entry itself left as written: the +11.7
points below is VOID. Both agents were trained on the invented six-speed
gearbox that `27e720c` replaced seven hours later -- see `results/void/README.md`.
Phase D's result, from sixteen agents on the real gearbox trained to the C1
budget (50 000 steps), is the null in the 21-22 September entry: preview does
not separate from seed noise.)*

**The project has a measured preview advantage for the first time.** It is one
seed against one seed and it is not quotable yet. Everything below was run, not
argued; the output of each command is in `results/`.

### The scenario is chosen and LOCKED

`make_grade_climb` defaults move **v_kmh 110 -> 130**. Decided before any
training run existed, from an envelope measured beforehand (eight grade/speed
pairs, in CLAUDE.md), and it does not move again. Four conditions hold together
for the first time in this project:

| | |
|---|---|
| constraint binds | 857 C against an 850 C trigger |
| torque trackable | 316 Nm demanded, **0.0 %** shortfall |
| reward gate | 4 of 4, neutral **+0.00048** |
| protection works | current-grade cuts damage **29.7 %** |

**The published towing standard was tried first and rejected by measurement.**
`SAE J2807` Davis Dam does not bind even behind a two-tonne trailer — 756.3 C,
94 K short. A truck standard at truck speeds asks a modest road power however
much torque the trailer adds.

### The gate caught a gearbox defect — mistake 17

`test_reward.py` FAILED on the new scenario: neutral scored **-0.124** against a
+/-0.05 band. The baseline demanded **381 Nm and delivered 359**, short 5.7 % on
**519 of 519** climb samples. `Vehicle.gear_for` selected on road speed alone, so
at the 115 km/h rung **the model upshifted into top gear halfway up a 12 %
grade**. A 4 % step in road speed moved the torque demand 23 %.

Fixed with a load term and a 25 % torque reserve. **Every operating point the
environment had already been used at keeps its gear**, so the old scenario is
bit-identical. Cost: peak turbine 899.4 -> 857.0 C, so the scenario binds by 7 K
instead of 49.

**Third defect in this project that was invisible until the load became real**,
after the wrong engine and the reward hack. Same shape every time.

### Phase C ran. Phase D has its protocol and its first point.

`train.py` executed past its import guard **for the first time**: 50 000 steps,
seed 0, sighted and blinded, **63 minutes each** — not the 45 min a 2000-step
probe predicted, so quote 63.

`evaluate.py` is new: **twenty frozen episodes**, weights pinned as literals, the
same for every policy. It exists because training-curve returns are NOT
comparable — the preference vector is redrawn every episode, and seed 0 ranged
from -506.4 to +643.6 over eleven episodes with its best in the FIRST five.

| policy | damage med | IQR | worst | fuel med |
|---|---|---|---|---|
| baseline ECU | 572.8 | 0.0 | 572.8 | 4528 |
| reactive | 540.9 | 0.0 | 540.9 | 4552 |
| current-grade | 402.6 | 0.0 | 402.6 | 4796 |
| **agent, sighted** | **194.7** | 35.6 | 378.8 | 5337 |
| **agent, blinded** | **261.4** | 19.9 | 336.9 | 5008 |

<!-- RETIRED-OK: 11.7, 66.0, 54.4 -- void, see results/void/README.md -->
**SIGHTED over BLINDED: +11.7 points.** Sighted cuts 66.0 %, blinded 54.4 %.

### This reverses the hand-written result, and that is the finding

Earlier the same day, preview was measured with HAND-WRITTEN policies across
five scenarios — constant grade and four rolling periods — and **lost in every
one**, between -0.1 and -2.3 points. The cause is one line: `p_predictive` takes
`max(preview[+15 s], preview[+30 s])`, so on a road that keeps climbing it
protects continuously, including through easy sections.

**AUDIT.md C3 said hand-written policies cannot answer this. They now
demonstrably cannot: the two verdicts differ by 12 points.**

<!-- RETIRED-OK: 11.7 -- void, see results/void/README.md -->
### Four limits on the +11.7, all of them stated

1. **n = 1 against n = 1.** The protocol wants five seeds each.
2. **The worst episode reverses it** — blinded 336.9 against sighted 378.8.
3. **The sighted agent burns 6.6 % more fuel**, 5337 against 5008 g.
4. **The twenty episodes vary the preference weights only**, not the road or the
   ambient — which is why every hand-written policy shows IQR 0.0. The protocol
   compares policies; it does not test robustness.

### What this session did NOT do

- **No five-seed result.** Eight runs remain, 63 min each, about 8.4 hours.
- **No second plant.** `battery.py` still does not exist, and with one plant the
  H/tau claim cannot be tested at all — only a curve, never an overlap.
- **The 115-125 km/h band still over-asks**, because the gear rule uses a flat
  torque ceiling on an rpm-dependent quantity. Not tuned away: lowering it would
  have moved 16 % at 110 km/h, the team's third scenario.

---

## Session of 19 September 2026 — the branches merged, and the gearbox is the car's

**The two working branches are one again.** `JMF-2340550` (Ghassan: the real
gearbox, the tenth drive, mistake 18) merged into the `sep17` line (mistake 17,
the locked scenario, `evaluate.py`, Phase D's first ablation). Two conflicts,
both in the gearbox, both resolved toward the measured side.

### What the merge took from each

<!-- RETIRED-OK: 11.7 -- void, see results/void/README.md -->
| from `sep17` | from `JMF-2340550` |
|---|---|
| mistake 17 — the load-aware downshift | **the real ZF 8HP51**, eight published ratios on 3.150 |
| the locked 12 % / 130 km/h scenario | mistake 18 — `Actual gear` clamps at 6 |
| `evaluate.py` and its twenty frozen episodes | the tenth drive, +119.5 min |
| Phase D's first ablation, +11.7 points | the runtime 3 L verification |

**Ghassan carried mistake 17's `SHIFT_LOAD` into the eight-speed deliberately**,
so the merge resolved to ONE rule rather than a conflict. Without it the taller
top gear (2.016 overall against 2.312) would have reintroduced the mid-climb
upshift that 17 was written to stop.

### The gearbox is validated against the car, not just cited

Toyota publishes the 8HP51 set. **The car confirms it.** Reproduced independently
from `data/master_samples.csv` during the merge: **80 898 moving samples, 85.1 %
within 4 %** of one of the eight published overall ratios (Ghassan reports 86.7 %
on 79 105 — a sample-filter difference, same result).

It also **excludes the alternative**: the 6MT top gear is 2.927 overall, the
8AT 8th is 2.016, and the car measures **1.993** in top-gear cruise. That is
1.1 % from the automatic and 32 % from the manual — the car's own data says it is
the eight-speed.

### The locked scenario survived, and it survived BY LUCK

| | peak turbine | vs trigger |
|---|---|---|
| 110 km/h, real gearbox | 840 °C | **−10 K** |
| 130 km/h, invented gearbox | 857 °C | +7 K |
| **130 km/h, real gearbox** | **884 °C** | **+34 K** |

130 was chosen because it was the only speed that bound **on a gearbox that did
not exist**. On the real one it binds by 34 K instead of 7 — a better scenario
than the one that was picked. **Recorded in `make_grade_climb`'s docstring as an
accident, not as foresight.**

### And the mechanism is load per cycle, for the third time

The first explanation offered was "the real box holds a lower gear, more rpm,
more exhaust flow". **Measured, it is backwards:**

```
invented 6-speed   5th, overall 2.788   2913 rpm   316 Nm
real ZF 8HP51      7th, overall 2.589   2706 rpm   340 Nm
```

The real box is **taller** here, so the engine turns **slower** and each cycle
carries **more** load. Road power is identical — 96.4 kW at the wheels either
way. All the gearbox changes is how that power splits between torque and rpm,
and the higher load per cycle is worth **27 K of turbine housing**.

**Same mechanism as `12 % @ 90` running hotter than `4 % @ 150`, and the same one
that makes SAE J2807's slow heavy climb produce a cool turbine.** Three times now
the answer has been load per cycle rather than flow.

### Verified on the merged tree

<!-- RETIRED-OK: 959.8, 884, 34.0, 0.4, -0.4 -- the figures of that session, before the merge of 30 September -->
```
verify_docs.py    All 38 checks pass, 311 figure mentions
test_reward.py    4 of 4; neutral -0.00038, starver -0.90349
check_premise.py  baseline 959.8 at 884 C; current-grade cuts 34.0 %;
                  preview over current grade -0.4 points
```

**`test_reward`'s starver margin recovered from −0.10 to −0.90.** The real
gearbox gives the engine room, so refusing to make torque is a clear crime
again — the number flagged on 18 September as the first to watch.

### What this session did NOT do, and it is the blocker

**No training run exists on this tree.** Two runs were on the invented gearbox
at 130 km/h; Ghassan's ten were on the real gearbox at 110 km/h without
`evaluate.py`. **All twelve are on trees that no longer exist**, and the 110 km/h
scenario does not bind at all — an agent trained there had nothing to learn about
protection.

Phase D restarts from zero on this tree: ten runs, seeds 0–4 sighted and blinded.

---

## Session of 19 September 2026, later — Phase D was NOT started, and four checks were run instead

**Phase D was requested, then stood down before any run was launched.** Nothing
was trained. `runs/` is untouched. What follows is verification work on the
merged tree, done in its place.

### Verified on this tree, independently

```
verify_docs.py    All 38 checks pass, 311 figure mentions, 15 tracked files
test_reward.py    4 of 4; neutral -0.00038, starver -0.90349
```

Both match what the merge reported, so the tree is the tree.

### 1 · The gearbox is the real one, reproduced rather than read

`Vehicle.gears` carries eight ratios on a 3.150 final drive, and **all eight are
reachable**: 8th on the flat at 130 km/h, 7th on the 12 % grade at the same
speed, 2706 rpm and 340 Nm.

Ghassan's channel finding was re-derived from `data/master_samples.csv` without
reference to his figures — overall ratio straight from rpm and road speed:

| | |
|---|---|
| moving samples | 80 898 |
| within 4 % of a published ratio | **85.1 %** |
| maximum value of `Actual gear` | **6.0**, on every drive |

Inside the samples the channel calls "gear 6": **60.2 % are really 8th, 17.4 %
really 7th, 15.5 % really 6th.** Top-gear cruise measures **1.997** overall
against the 8HP51's 2.016 (0.9 %) and the 6MT's 2.927 (32 %).

Mistake 18 stands in every particular. *(85.1 % on 80 898 here against
Ghassan's 86.7 % on 79 105 — the sample-filter difference this file already
records.)*

### 2 · Every cooling path is live on the locked scenario EXCEPT enrichment

Instrumented over a full neutral-policy episode:

| path | state | measured |
|---|---|---|
| thermostat / radiator | live | open 0.20 → 0.70, never shut, ~100 kW rejected |
| cooling fan | live | 0.4 rung for 97.4 % of the climb, never 1.0 |
| coolant pump | live | baseline at 1.0 |
| charge cooler | live | 42 °C ambient → 56.9 °C charge |
| knock retard | live | peak 3.2°, active 3.8 % |
| **enrichment** | **never fires** | **λ = 1.000 on every step** |

**And the enrichment is off structurally, not by accident.** The climb sits at
2706 rpm, and `base_lambda` returns 1.000 there at any load and any dwell —
178 or 220 kPa, 0 or 30 s. First enrichment appears at 3600 rpm. That is the
map being faithful to the car (mistake 4: no enrichment below ~3300 rpm however
long boost is held).

Consequence for Phase D, now in CLAUDE.md's limitations: the baseline does not
use one of the four protection levers here and the agent can, so every "cuts
damage N %" figure against the baseline is inflated by a lever, not by
anticipation. The sighted-vs-blinded ablation is unaffected — both agents hold
the same lever.

### 3 · `dt` is inside the signal, not underneath it

Ghassan's open question 4, measured. Hand-written policies, locked scenario,
720 s, same seed and weights, only the step changed:

<!-- RETIRED-OK: 900.9 -- the baseline at the finer training step, not the protocol step -->
| policy | dt = 1.0 | dt = 0.2 | cuts vs baseline |
|---|---|---|---|
| baseline ECU | 959.8 | 900.9 | — |
| current-grade | 633.2 | 567.8 | 34.0 % → **37.0 %** |
| reactive | 679.0 | 622.5 | 29.3 % → **30.9 %** |

Peak turbine is **dt-invariant** (884.0 °C at both) and fuel moves 0.2 %, so the
physics is sound. The damage integral is not. **The gap between two fixed
policies moves 4.8 → 6.1 points on the step alone**, against preview effects of
0.4–2.3 points from hand-written policies.

`train.py` runs 0.2, `evaluate.py` runs 1.0, so **a trained agent is scored in a
discretisation it did not learn in**. The cause is `_track_torque`'s PI, which
accumulates per step with no `dt` — the defect AUDIT.md M16 fixed for `SLEW`, in
the loop M16 left alone. The preview horizon is clean: `_preview()` uses
`int(h / dt)`, so H is wall-clock at every step size.

Shared by both agents, so not a bias by construction; **symmetry unmeasured**.

### 4 · Mistake 18's outstanding order, carried out

Mistake 18 ends "re-derive it from the inferred gear before quoting the p99
again". Done:

| gear filter | n | p95 | p99 |
|---|---|---|---|
| steady CHANNEL gear | 15 654 | 12.75 | 21.75 |
| **steady INFERRED gear** | **13 329** | **9.75** | **18.00** |

Not cosmetic. **But it does not replace the published 9.8**, because neither
that figure nor its n = 10 896 reproduces from the shipped data under a
gear filter alone — the torque-cut half of the original filter is undocumented.
The row now carries no quotable p99 until its author re-runs it.

### One documentation defect found and fixed

`neutral_action()`'s fan caveat was inverted in both halves — see the
19 September addition to mistake 10. The constant was deliberately NOT changed;
the sentence was.

### What this session did NOT do

- **No training, no Phase D, no five-seed result.** Ten runs still outstanding.
- **`runs/sighted_seed0` and `runs/blind_seed0` are still there**, from the
  invented gearbox, both at 50 000 steps. `train.py` resumes from the newest
  `ckpt_*_steps.zip`, so `--seed 0` on this tree would print "already at 50000
  of 50000 steps", train nothing, and write a `final.zip` holding an agent from
  a gearbox that no longer exists. **Move them aside before Phase D starts.**
- **The step budget is still undecided** — 50 000 steps is eleven episodes for a
  weight-conditioned policy, and Ghassan asked for a decision before the five
  seeds are treated as Phase D's input.

---

## Session of 20-21 September 2026 — the SECOND audit, and the Phase D result does not reproduce

**Nothing in the repository was changed by the audit itself.** It ran read-only:
every historical tree was exported with `git archive`, every rebuild went to a
scratch directory outside the repo, and `train.py` was exercised only on a copy
of `runs/`. The only file this session adds is `AUDIT2.md`, plus this entry.

**`AUDIT2.md` is the report: 1041 lines, 50 new findings** (3 CRITICAL, 12 HIGH,
16 MEDIUM, 13 LOW, 4 NITPICK), IDs `C2-n` / `H2-n` / `M2-n` / `L2-n` / `N2-n` so
they never collide with `AUDIT.md`. 34 are CONFIRMED by execution here, 16 are
PLAUSIBLE on one agent's output and are labelled as such.

### The headline: neither Phase D file is a result, and this branch's does not reproduce

`python evaluate.py runs/sighted_seed0 runs/blind_seed0` on HEAD, 76 min,
same two trained agents as `results/phase_d_seed0.txt`:

<!-- RETIRED-OK: 11.7, 7.5, 572.8, 857 -- the void pair, named as the finding -->
| row | the shipped file | re-run on HEAD |
|---|---|---|
| baseline damage / peak | 572.8 / 857 C | **959.8 / 884 C** |
| sighted median (IQR, worst) | 194.7 (35.6, 378.8) | 279.3 (9.6, 360.6) |
| blinded median (IQR, worst) | 261.4 (19.9, 336.9) | 351.1 (31.8, 435.0) |
| **sighted over blinded** | **+11.7** | **+7.5** |

<!-- RETIRED-OK: 11.7, 7.5 -->
**Why:** the SB3 archives decode to 130 km/h at **2913 rpm**, which is the
invented six-speed in 5th after mistake 17's load-aware downshift. The ZF landed
at `27e720c`, seven hours after `a68715f` committed the result. The +7.5 is not
a Phase D point either -- it scores agents on a plant they never saw.

**Isolated on three exported trees, one neutral episode each, 720 s at dt 1.0:**

<!-- RETIRED-OK: 294.2, 812.3, 812, 572.8, 857.0, 462.7, 839.7 -- measurements on superseded trees, named as the finding -->
```
six-speed (a68715f)   110 km/h  damage 294.2  peak 812.3 C
six-speed (a68715f)   130 km/h  damage 572.8  peak 857.0 C
ZF 8HP51  (f6b46e9)   110 km/h  damage 462.7  peak 839.7 C
ZF 8HP51  (HEAD)      130 km/h  damage 959.8  peak 884.0 C
```

Every published baseline row is on that grid. Speed is worth -44.3 K and the
gearbox +27.4 K; they add to the observed gap within 0.4 K, so nothing else in
the 209-line `engine_env.py` divergence moves the baseline.

### Three things the tree says that the scripts contradict

<!-- RETIRED-OK: 959.8, 884 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK: 294.2, 812, 175.5, 9, 22, 74, 13 -- the stale figures this table names are its subject -->
| document | says | prints today |
|---|---|---|
| `CLAUDE.md`, `README.md`, `handoff.md` | baseline 294.2 at 812 C, "the constraint does not bind" | 959.8 at 884 C, binds by **34 K** |
| the four abstracts, `CONTROL_SCOPE.md` | 175.5 min, nine drives, 22 points, 30-74 kPa | 295.0, ten, 26, 30-75 |
| `CLAUDE.md:1664`, `CHECKPOINT.md:657` | 13 thermal alerts on `7475b5d7` | **15** |

### The guard is blind to the figures that decide the project

16 deliberate drifts injected into a `git archive` copy; 4 CAUGHT, 12 MISSED.
Caught: `8 of 11`, `ten drives`, `DTHETA_DEG`, `derived k`. **Missed:** the load
residual, the app's peak turbine, every Phase D figure, the premise table, the
scenario docstring, **`make_grade_climb`'s default `v_kmh` 130 -> 120**, and
**`TURB_PROTECT_K` 1123 -> 1100**. `check_retired` globs `**/*.md` plus root
`*.py` only, so `presentation/index.html`, `plan.html` and `data.js` -- which
<!-- RETIRED-OK: 829.2, 548.6, 437.6, 13.4 -- naming the void set the deck still ships IS the finding -->
carry 829.2 / 548.6 / 437.6 / 13.4 on more than a hundred lines -- are outside it.

### M16 is not fixed, and the mechanism is not the one recorded

Same policy, seed and weights; only the step changed:

<!-- RETIRED-OK: 959.8, 900.9, 1034.9 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK: 900.9 -- the baseline at the finer training step, not the protocol step -->
| policy | dt 0.2 | dt 1.0 | dt 2.0 |
|---|---|---|---|
| baseline | 900.9 | 959.8 | 1034.9 |
| current-grade | 567.8 | 633.2 | 723.2 |
| **cuts vs baseline** | **37.0 %** | **34.0 %** | **30.1 %** |

Splitting the baseline integral by term: turbine 862.26 -> 858.87 (-0.4 %), oil
unchanged, **knock 69.33 -> 13.85**. So **94 % of the dt shift is one step**: a
knock spike of 66.3 damage/s at t = 181 s, where the grade steps 0 -> 12 %,
charged for one step whatever the step is. `_track_torque`'s PI is per-step, but
its effect lives inside the remaining 0.4 %. The dt paragraph in `CLAUDE.md`
names the wrong loop.

### Verified as still holding, by execution

C1, C2 (ECU on the lagged baseline MAP; retard peak 3.2 deg, 3.3 % of steps),
C3, H1, H3, H4, H7 (`master_points.csv` byte-identical in two input orders), H8,
M5, M7, M8, M10, M11. **Incomplete here:** M16, H6 (resume blanks `curve.csv`
and re-saves `final.zip` on a no-op), M2/M12 (`generality_test` still scores with
its own `damage(scale=25.0)` against the retired reactive comparator), M3, H2,
L11, M15.

### The scenario: locked in its parameters, not in its experiment

Git supports the envelope-before-choice account (`9f41082`, 18 Sep 17:26, three
hours before the first run). It cannot settle "decided by the team", and the
sighted run's SB3 `start_time` is **26 s before** the lock commit `1df41a2` --
the run demonstrably used the new code, but no artefact records an uncommitted
tree. The plant under the locked scenario was then replaced and the result kept.

**What protects the project, and it is measured:** preview LOSES on this row
under every hand-written policy (-0.6, -2.3, -0.4), so the row cannot have been
chosen to favour the claim. Say that in the defence.

### What this session did NOT do

- **No fix was applied.** Every finding in `AUDIT2.md` is described, none is
  implemented. The repository is exactly as it was apart from the report.
- **No training.** `runs/` still holds the two six-speed agents, untouched.
- **Four of nine audit parts ran on the orchestrator rather than on agents**,
  because the account's usage limit killed two full workflow runs; the coverage
  and what could not be verified are listed in the report's confidence ledger.

## Session of 21 September 2026 — results get a fingerprint, and the guard gets the figures that decide the project

The second audit's fixes 1 and 2. Fix 3, the document sweep, is NOT done and is
still the next session's work — see the ledger below, which is how much of it is
outstanding, counted.

### Fix 1 — every trained result now records the plant that produced it

<!-- RETIRED-OK: 11.7 -- naming the void figure IS the finding -->
`AUDIT2.md` C2-1: `results/phase_d_seed0.txt` says +11.7 points and was produced
on an invented six-speed gearbox that commit `27e720c` replaced seven hours
later. Nothing in `runs/` recorded which gearbox. The header that was supposed to
say was a hardcoded string, **byte-identical on both plants**.

New `fingerprint.py` builds a block from the LIVE objects:

| field | what it is | fatal? |
|---|---|---|
| `plant_sha` | SHA-256 over the bytes of `plant.py` + `thermal.py` + `engine_env.py` | yes |
| `gears`, `final_drive` | the transmission | yes |
| `dtheta_deg` | the crank-angle integration step | yes |
| `turb_protect_k`, `oil_protect_k` | the protection triggers | yes |
| `scenario` | grade / v_kmh / t_amb, from `inspect.signature` | yes |
| `episodes_sha` | a hash of the twenty frozen evaluation episodes | yes |
| `git_head`, `git_dirty`, `python`, `train_dt`, `eval_dt` … | context | no |

**The plant SHA outranks the git commit deliberately.** The audit measured that
the 18 September sighted run started **26 seconds before** the commit that locked
the scenario, from an uncommitted working tree — so `git rev-parse HEAD`
describes a tree that run did not use. It is recorded, and it is advisory.

**`dt` is advisory too, and that is not an oversight.** Training builds its
environment at dt 0.2 over 900 s; `evaluate.py` scores at 1.0 over 720 s. The
asymmetry is real, deliberate on both sides, and an open problem (H2-2). Making
it fatal would refuse every legitimate evaluation this project performs, so it is
printed side by side with the finding named instead.

What changed where:

- `train.py` writes `runs/<tag>/meta.json` before the first step, and on resume
  **refuses** a missing or mismatched fingerprint (`--force-plant-mismatch`
  overrides and says so in the output).
- `train.py` **appends** to `curve.csv` instead of overwriting it (H2-3: a re-run
  of a finished agent blanked a twelve-episode curve to its header), and a re-run
  with nothing left to do now returns **before** `model.learn` and `model.save`
  instead of silently rewriting the only copy of a trained agent.
- `evaluate.py` builds its scenario line from `inspect.signature(make_grade_climb)`,
  prints the fingerprint block, writes the whole report to `--out`, and refuses a
  model whose `meta.json` disagrees.

Six paths were exercised rather than argued: a fresh run, a no-op re-run, a
resume that appends, a refused plant mismatch, a refused missing `meta.json`, and
a clean match.

### Fix 2 — the guard now sees the figures that decide the experiment

`AUDIT2.md` C2-2 measured that fourteen realistic drifts were injected into a
copy of the tree and **twelve went through green**, including
`make_grade_climb(v_kmh=)` 130 → 120 and `TURB_PROTECT_K` 1123 → 1100. Either one
re-bases every damage figure in the repository while every document goes on
saying 130 km/h and 850 °C.

`check_scenario()` asserts, from the live objects: the four `make_grade_climb`
defaults, both protection triggers, the eight ZF ratios and the final drive,
`evaluate.DT` / `DURATION`, a hash of `EPISODES`, `check_premise`'s baseline
damage and peak (a real 34-second rollout, identical to the script's own first
row), both of `compare_log`'s residuals and its fitted k (by running it and
reading what it prints), and `app/test_replay`'s pinned peak and alert counts.

Three structural changes came with it:

- **ONE file list for both scans**, from `git ls-files`, so a file that is in the
  repository cannot be outside the checker by accident. It reaches every tracked
  `.py`, `.html`, `.js` and `.txt` now, with HTML tags stripped per line. The
  retired scan went from 35 files to 52.
- **`RETIRED-OK` is figure-specific** (H2-6). A marker names the figures it
<!-- RETIRED-OK: 168.1, 113 -- the marker syntax being quoted, not a claim -->
  excuses: `<!-- RETIRED-OK: 168.1, 113 -->`. A marker that names none can excuse
  the RETIRED scan only — it can no longer switch off the comparison against live
  data. The per-file exempted count is printed every run.
- **A mention is not a marker.** Five passages in this repository *discuss* the
  mechanism in backticks, and every one of them was switching the checker off for
  its own paragraph — including one whose next sentence states a live and wrong
  dwell figure. An occurrence inside an inline code span is now ignored.

### The known-stale ledger, and why the run is green with rot outstanding

Turning the guard on over the whole repository surfaced roughly two hundred and
fifty stale figures in one run. **Every one is already a written finding** in
`AUDIT2.md` with fix 3 scheduled against it.

Leaving the checker red was rejected: a checker that is red for a week is a
checker nobody reads, and this project's house rule is to run it before quoting
any number. Exempting the files was rejected too — that is the blunt instrument
H2-6 is about, one level up.

So they are **counted**. `KNOWN_STALE` carries one row per (file, figure) with
the audit finding, the exact count, and **the exact stale values**. A row that
grows is new rot and fails. A row that shrinks fails too, so the ledger has to be
swept in the same commit as the documents. A row whose *values* move fails — a
count alone cannot see a stale line being edited into a differently stale one,
<!-- RETIRED-OK: 294.2, 812 -- naming the stale pair IS the example -->
which is how `CLAUDE.md`'s "294.2 at 812 °C" could have had its 812 changed
unnoticed.

**Read the ledger total as the size of fix 3.** It is printed every run.

### The acceptance test is in the repository

`drift_test.py` re-runs AUDIT2 Part 4a's injected drifts against the current
tree, each in its own copy of the tracked file set, and reports CAUGHT or MISSED
per row. It is the file that makes fix 2's claim checkable instead of asserted,
and it is the reason `verify_docs.py` may not simply be trusted when it prints
green.

### What this session did NOT do

- **Fix 3 is not started.** The document sweep is the next session's work and the
  ledger is its inventory.
- **No training, and no Phase D.** `runs_sixspeed_18sep/` is untouched.
- **`presentation/` is untouched.** Its void premise figures are ledgered under
  C2-3, not fixed; the deck still must not be shown.


## Session of 21-22 September 2026 - Phase D has a result, and the result is a null

Fixes 1 and 2 from `AUDIT2.md`, then the whole of Phase D end to end. Fix 3,
the document sweep, is still NOT done; the known-stale ledger `verify_docs.py`
prints is its inventory, counted.

### THE RESULT

Sixteen agents, eight seeds per arm, trained on the ZF plant under
`results/PREREGISTRATION.md`, which was committed **before any of them
started**. `python analyse_phase_d.py`:

| seed | baseline | curr-grade | sighted | blinded | blind - sighted |
|---|---|---|---|---|---|
| 0 | 959.8 | 633.2 | 340.5 | 350.3 | +9.8 |
| 1 | 959.8 | 633.2 | 354.0 | 348.2 | -5.8 |
| 2 | 959.8 | 633.2 | 308.2 | 376.8 | +68.6 |
| 3 | 959.8 | 633.2 | 302.5 | 689.7 | **+387.2** |
| 4 | 959.8 | 633.2 | 639.5 | 367.8 | **-271.7** |
| 5 | 959.8 | 633.2 | 525.7 | 237.5 | **-288.2** |
| 6 | 959.8 | 633.2 | 498.5 | 549.5 | +51.0 |
| 7 | 959.8 | 633.2 | 331.5 | 418.6 | +87.1 |

```
positive (preview helped) : 5 of 8
mean difference           : +4.8 damage units
exact one-sided sign test        p = 0.3633
exact paired permutation test    p = 0.4922
alpha 0.05  ->  NOT SIGNIFICANT
```

**Preview cannot be shown to help.** The seed-to-seed spread is tens of times
the effect: seed 3 says preview saves 387 damage units, seed 5 says it costs
288. The mean of +4.8 is noise.

**AND THAT IS WHAT THE EIGHT SEEDS WERE FOR.** Train seed 3 alone and the
answer is "+387, preview works", and it would have been written up. The seeds
are the only thing separating a result from a coincidence.

### The second finding, which is positive and is NOT the same claim

The trained agent beats `current-grade` by **+29 to +34 points** on five of
eight seeds, and is positive on seven of eight.

**Learned supervision works. PREVIEW specifically is what cannot be shown.**
Two separate claims, and only the second was preregistered as the hypothesis.
Say both in the thesis, and do not let the first be read as evidence for the
second -- that conflation is what `AUDIT.md` C3 was about.

This agrees with everything before it: the hand-written policies put preview at
**-0.4 points**, and five scenarios gave the same sign. The trained pair now
agrees with them.

### Still outstanding before this is written up

**The minimum effect of interest is not set** (`PREREGISTRATION.md` section 5,
TEAM DECISION). Until it is, "preview does not help" cannot be told apart from
"our experiment was too small to see it". That distinction is the difference
between a null result and no result.

### What it took to get there, because it is a lesson about machines

Phase D's first two launches lost **21 of 29 runs to memory**, in the first
minute, twice.

| launch | lost | cause | how it was settled |
|---|---|---|---|
| 1 | 13 of 16 | a 1 000 000-transition replay buffer x16 | counted CORES, never checked memory |
| 2 | 8 of 13 | concurrency cap from an ESTIMATE of 0.9 GB/run | guessed a number |
| 3 | 0 of 8 | - | MEASURED: 1522 MB per process |

The estimate was 70 % low, which is exactly the margin between a cap that works
and one that does not. **Cores tell you how many runs can make PROGRESS; memory
tells you how many can START.**

Sizing the buffer to the run could have changed what was learned, and three
runs had already finished on the old setting, so it was proven rather than
assumed: same seed both ways, **32 tensors, 368 398 values, largest difference
0.000e+00**. `python prove_buffer.py` re-runs it.

No seed was changed, added or dropped. Every failure was mechanical, happened
before any agent had learned anything, and is recorded in `PREREGISTRATION.md`
section 6a as section 6 requires.

### The fingerprint earned its keep, on a real case

Across the sixteen `meta.json` files:

```
plant_sha   ONE value, identical for all sixteen
git_head    TWO values, e429715 and f3da0b9
```

Some runs started before the memory-fix commit and some after, so the commit
hash genuinely differs -- and the physics files did not change, so the plant
hash does not. Had the fatal comparison been on the commit, **thirteen
legitimate agents would now be refused.** That is why `plant_sha` is fatal and
`git_head` is advisory, decided hours before the case arose.

`evaluate.py` accepted all sixteen and refused the six-speed pair in
`runs_sixspeed_18sep/` with *"no meta.json ... nothing records which plant it
was trained on"*.

<!-- RETIRED-OK: 11.7 -->
`results/void/` keeps the +11.7 file with a README saying why it is void.


## 22 September 2026, later — a claim was drafted, checked, and REFUTED; and the ablation has a design flaw

**Recorded in full because the refuted claim is the one the next person will
draft, and because the check found something much worse than the error it was
looking for.**

### The claim, which is wrong

Asked "would adding GPS make a difference?", the answer given in chat was:

> The preview IS the GPS. The agent sees at most 30 s ahead; the turbine takes
> 48 s; so H/τ = 0.62, below the region near 1 where the theory says preview
> matters. **So the null is consistent with the project's own theory.**

That was about to be written into `CLAUDE.md` as a reframing of the result. It
was checked first by four independent read-only agents, each told to REFUTE it,
and then re-checked directly. **It is wrong in four places:**

| said | truth |
|---|---|
| H/τ = 0.62 | 0.23 while the preview can first act (flat, τ = 129 s), 0.62 on the climb (τ = 48 s). τ spans 40–239 s over one episode |
| "the region near 1" | invented. "Near 1" appears nowhere in the repo |
| "consistent with the theory" | the OPPOSITE. The project's only H/τ curve (void) puts the LARGEST preview value near 0.6, where Phase D sits |
| a real GPS is strictly worse | worse in accuracy, far BETTER in reach — it sees the whole route |

A second wrong figure was also given in chat — "τ is 54.2 s, not 48" — built on
an exhaust flow of 103 g/s taken from a code comment. The climb's measured τ is
48.4 s.

**None of it reached a file.** That was checked. The lesson is the one this
repository keeps relearning: a claim that makes the result look better is the
one to verify hardest, and verifying it BEFORE writing is what kept it out.

### What the check found instead, and it matters more

**1. THE BLINDED ARM IS NOT BLIND.** Verified directly, not relayed:

```
road identical across 3 resets with different seeds : True
distinct grade values in the road                   : [0.0, 0.12]
step location                                        : t = 180 s
blind agent, flat phase: obs[7] over 900 steps      : 900 distinct values
```

The road never changes between episodes, and the blind agent's thermal state is
a clock. So Phase D compared an explicit preview channel with an implicit one on
a memorisable road — not foresight with none. **Four explanations for the null
are now live and the experiment separates none of them** (`PREREGISTRATION.md`
limit 7). The decisive fix is cheap: **randomise the climb per episode.**

**2. The H/τ axis is broken.** `generality_test.py:81` reads
`info.get("mdot")`; the environment never emits that key; so
`_exhaust_of_climb()` returns 0 samples and the script falls back to the assumed
112.5 g/s every run. The `AUDIT.md` M12 fix does not work. Verified by calling
it.

**3. `CLAUDE.md`'s τ line presented one method as two.** "C/UA gives 50.3 s;
the step response gives 48.0 s" — but `validate.py` holds the flow constant, so
the step response IS C/UA; swept over nine parameter cells they agree to 0.13 s.
And 50.3 s was C/UA at the condemned 112.5 g/s. Corrected in `CLAUDE.md`.

### Where each finding now lives

| finding | file |
|---|---|
| the blinded arm is not blind | `results/PREREGISTRATION.md` limit 7, `CLAUDE.md` result box, `results/README.md`, **printed by `analyse_phase_d.py`** |
| the correct H/τ position, and why the rescue is wrong | `results/PREREGISTRATION.md` limit 8, `CLAUDE.md`, `results/README.md` |
| the broken mdot / M12 axis | `results/PREREGISTRATION.md` limit 8, this entry, the next-session prompt |
| the τ line corrected | `CLAUDE.md`, Known limitations |

### Not done, and stated

- **`generality_test.py` is not fixed.** The bug is documented with its line and
  cause; fixing it moves figures that are void anyway (C1, H2-5), so it waits
  for the session that re-runs the H/τ sweep properly.
- **`README.md`'s explanation of the 48.0 / 50.3 gap is still there** —
  "the gas-side coefficient rises with flow, so the node is not first-order" —
  and it is false for a constant-flow test. It is `AUDIT2.md` fix-3 work.
- **The climb has not been randomised.** That is the next experiment, and it
  needs its own preregistration.


## 22 September 2026, later still — the randomised-climb range was measured, and half of it fails

The team accepted a design for the next experiment — randomise the climb's start
between 120 and 300 s and its grade between 8 % and 16 % — and before anything
was built, the grade range was measured.

| grade | peak | vs trigger | binds? |
|---|---|---|---|
| 8 % | 848.9 °C | −1.0 K | **no** |
| 10 % | 826.6 °C | −23.3 K | **no** |
| 12 % | 884.0 °C | +34.2 K | yes |
| 14 % | 862.6 °C | +12.7 K | yes |
| 16 % | 902.9 °C | +53.0 K | yes |

Neutral policy, 130 km/h, 720 s, dt 1.0. The start time does not move the peak:
12 % at 120 s and at 300 s both reach 884.0 °C.

**Grades of 8 % and 10 % never reach the trigger**, so an episode drawn there
carries no protection signal and dilutes the rest. **And peak temperature is not
monotonic in grade** — 10 % is cooler than 8 %, 14 % cooler than 12 % — because
the gearbox downshifts under load and a lower load per cycle means a cooler
exhaust.

Recommended in its place: randomise the start time only, grade fixed at 12 %.
The options and the reasoning are in `results/NEXT_EXPERIMENT_DESIGN.md`. The
decision is open and belongs in the next preregistration, before training.


## 22 September 2026, last — the next experiment's design is DECIDED, and it is B

The team chose option B over the recommended A: randomise both the climb's start
time (120–300 s) and its grade (12–16 %). **Jad's principle: "our goal is not the
highest result, our goal is to be realistic."** Recorded in
`results/NEXT_EXPERIMENT_DESIGN.md` as a design principle, because it will decide
future choices the same way.

The reasoning beat the recommendation. A was chosen for ease of interpretation;
B tests the preview a real map provides (when AND how steep), and because the
comparison is paired, the gearbox's non-monotonic peak hits both arms equally —
so A's advantage was overstated.

B's one risk was measured away before the decision was recorded: **all nine
grades from 12 % to 16 % in 0.5 % steps bind**, weakest 14.0 % at +12.7 K. The
peak is a sawtooth — up to 920.8 °C at 13.5 %, down 58 K at 14 % where the box
changes gear, up again.

**What "realistic" cannot mean, and it is recorded rather than glossed:** the
road can vary like a real one, but it cannot be as gentle as a real one. The Taif
mountain drive peaks 52 K below the trigger, real driving sits above the limit
0.206 % of the time, and 8 % and 10 % grades do not bind. Realistic severity and
a binding constraint are mutually exclusive on this car.

**The whole next step is planned as ONE session** (`NEXT_SESSION_2026-09-22.md`),
at the team's request. It fits because training and evaluation run in the
background for ~6 hours while the document sweep runs in the foreground.


## SESSION CLOSE, 21–22 September 2026 — the index to everything above

Eleven commits, `8bb7342` … `4510f33`, on `JMF-2340550-sep17`. The entries
above are the detail; this is where to start.

### What the session set out to do, and did

| task | state | where |
|---|---|---|
| `AUDIT2.md` fix 1 — every result records the plant that produced it | **done** | `fingerprint.py`, `train.py`, `evaluate.py` |
| `AUDIT2.md` fix 2 — the guard sees the figures that decide the project | **done**, 16 of 16 drifts caught | `verify_docs.py`, `drift_test.py` |
| Phase D, preregistered and run | **done — a NULL** | `results/PREREGISTRATION.md`, `analyse_phase_d.py` |
| `AUDIT2.md` fix 3 — the document sweep | **NOT done** — inventoried | `verify_docs.py` KNOWN STALE ledger, ~187 mentions |

### What was found that nobody asked for

| finding | where it lives |
|---|---|
| the fingerprint must hash CODE, not bytes, or the doc sweep invalidates every agent; and must normalise CRLF, or five people on five machines cannot compare results | `fingerprint.py` docstring |
| a fresh-start train into a directory holding `final.zip` stamped a new certificate on an old agent — C2-1 with provenance attached | `train.py`; reproduced, then refused |
| 13 of 16 then 8 of 13 runs died of memory: cores say how many runs can progress, memory how many can START; an estimate was 70 % low | `run_phase_d.py`, `PREREGISTRATION.md` §6a |
| the replay-buffer size changes nothing learned — proven, 368 398 weights, max difference 0 | `prove_buffer.py` |
| the agents are C1 ("the first bad run"), 11 episodes — the null must carry that | `PREREGISTRATION.md` limit 6; printed by `analyse_phase_d.py` |
| **the blinded arm is not blind** — fixed road plus a thermal clock | `PREREGISTRATION.md` limit 7; printed by `analyse_phase_d.py` |
| "the null fits the H/τ theory" — drafted, checked, **refuted** | `PREREGISTRATION.md` limit 8 |
| `generality_test.py` line 81 reads a key the env never emits; the M12 fix never worked | `PREREGISTRATION.md` limit 8 |
| CLAUDE.md's two τ measurements were one method | `CLAUDE.md`, Known limitations |
| 8 % and 10 % grades never bind; peak is a sawtooth in grade because of the gearbox | `results/NEXT_EXPERIMENT_DESIGN.md` |

### Decisions taken, by whom

| decision | by | recorded in |
|---|---|---|
| eight seeds per arm, not five | proposed, accepted | `PREREGISTRATION.md` §4 |
| the next experiment is option B — start 120–300 s, grade 12–16 % | **Jad**, overriding the recommendation | `results/NEXT_EXPERIMENT_DESIGN.md` |
| "our goal is not the highest result, our goal is to be realistic" | **Jad** | same file |
| the whole next step is one session | **Jad** | `NEXT_SESSION_2026-09-22.md` |

### Open, and the next session's to close

1. **The minimum effect of interest** — TEAM DECISION, blocks both write-ups.
2. **The randomised-climb experiment** — designed, measured, not built.
3. **The document sweep** — `presentation/` first, 116 mentions.
4. **`generality_test.py` line 81.**

### Two process failures in this session, stated

- **A commit claimed a green `verify_docs.py` run that had failed**, because the
  check was chained `grep && git commit` — exactly the trap the brief named. The
  commit was amended; every run since reads `$?` into its own variable.
- **A wrong claim was given in chat as a reframing of the result** — the H/τ
  rescue. It was verified before being written and never reached a file, but it
  was said. The rule now in force: every finding goes into a tracked file before
  the turn ends, and a claim that flatters the result is the one to check hardest.


## Session of 22–23 September 2026 — Phase D2: the minimum effect set, the climb randomised, the documents swept

Commits `190be60` … (see `git log`), on `JMF-2340550-sep17`. Run from
`NEXT_SESSION_2026-09-22.md`, all of it in one session, as the team decided.

### The result

**Phase D2 is INCONCLUSIVE, and so — under the same rule, labelled post-hoc — is
Phase D.** The blind arm is now verifiably blind, and preview still does not
separate from seed noise.

```
python analyse_phase_d2.py
                     Phase D (post-hoc MEI)      Phase D2 (preregistered)
blinded arm          not blind                   blind -- checked
positive             5 of 8                      4 of 8
mean (blind-sighted) +4.8                        +6.4 damage units
preview helps        sign p 0.3633               sign p 0.6367
below the MEI (50)   sign p 0.6367               sign p 0.1445  (6 of 8 under 50)
sd of differences    214.4                       98.8
cell                 INCONCLUSIVE                INCONCLUSIVE
```

- **Removing the memorisable road did not pull the arms apart.** Limit 7's
  design flaw is not what hid a preview effect. Left standing: preview buys
  little at this configuration, or C1 agents cannot learn to use it.
- **The spread prediction FAILED.** The preregistration said randomising the
  climb was "not expected" to shrink the seed spread; it fell to 46 % of Phase D's.
  At D2's spread eight seeds have power 0.24 against 50 units; 80 % needs about
  42 seeds per arm.
- **Supervision, separately:** the sighted agent beats `current-grade` on 8 of 8
  seeds (+2.3 to +28.8 points), and every blind agent does too.
- **Limit 10, torque delivery:** `check_d2_tracking.py` — **no agent refuses torque.** 0 of 16 track torque
  more than one point worse than the baseline ECU; every median is within 0.05
  points of it. The five agents that burn less fuel than the baseline are not
  buying it with torque. Worst single episodes do show tracking error — blind
  seed 3 10.47 %, blind seed 5 5.33 %, current-grade 4.39 % — as episodes, not
  as typical behaviour. Its damage column reproduces `evaluate.py`'s medians to
  the decimal: the D2 evaluation is reproducible. So the D2 damage figures can
  be read as protection.

The full account is `results/PREREGISTRATION_D2.md` section 11; the captured
output is `results/PHASE_D2_RESULT.txt`.

### What the session set out to do, and did

| step | state | where |
|---|---|---|
| 1 · minimum effect of interest | **set: 50 damage units** — by Jad, after being shown the power analysis | `results/PREREGISTRATION_D2.md` §5; `results/PREREGISTRATION.md` §5 (closed, marked post-hoc) |
| 2 · preregistration | **committed `d8d05e2` before any D2 agent trained**, pinned to code `8e91276` | `results/PREREGISTRATION_D2.md` |
| 3 · the randomised road | **built as a wrapper**; both gates pass | `random_road.py`, `check_random_road.py`, `test_reward.py --road random` |
| 4 · train and evaluate | **16 runs, 8 evaluations** — see the run log | `runs_d2/`, `results/d2_seed*.txt`, prereg §6a |
| 5–6 · the document sweep | **187 stale mentions → 0**; ledger emptied; guard 16/16 | commit `3f4627d` |
| 7 · `generality_test.py` line 81 | **fixed**: the axis measures 118.1 g/s (was an assumed 112.5), τ 48.3 s | commit `b6b4ff5` |
| 8 · the preregistered test | **INCONCLUSIVE** (4 of 8, sign p = 0.6367); Phase D beside it, also INCONCLUSIVE post-hoc — commit `52514f1` | `analyse_phase_d2.py` |
| 9 · write it into the files | this entry; `CLAUDE.md`; `results/` | — |

### What was found that nobody asked for

| finding | where it lives |
|---|---|
| **Phase D was underpowered by design.** At its measured spread (sd 214.4), eight seeds have power 0.10 against 50 units and reach 80 % only near 269 — 28 % of baseline damage. Its null is as consistent with preview worth 100 units as with nothing | `power_analysis.py`; `PREREGISTRATION.md` §5 |
| more seeds is not monotonically better for a sign test: ten need 9 of 10, stricter than eight's 7 of 8 | `power_analysis.py` |
| **the flattery check on the late MEI was first written WRONG** ("every MEI gives INCONCLUSIVE"); computed, Phase D's label flips at MEI ≥ 87.2. 50 gives the weaker label | `PREREGISTRATION.md` §5 |
| editing `engine_env.py` would have moved `plant_sha` and locked out all sixteen Phase D agents — so D2 is a wrapper and the environment is byte-identical | `random_road.py` docstring; `fingerprint.py` |
| **the gearbox notch is at 13.73 % (+6.9 K), not 14.0 % (+12.7 K)** — between the design grid's points. All 121 grades still bind | `NEXT_EXPERIMENT_DESIGN.md` addendum |
| the blind arm is now blind, measured: identical observations on every road until its climb arrives (150 s), sighted diverges 30 s earlier (120 s) | `check_random_road.py` B |
| **at 16 % the reward barely punishes torque refusal** — the starver clears the gate by 0.006. Not retuned; declared | `PREREGISTRATION_D2.md` limit 10 |
| the launcher computes its concurrency cap ONCE — a game holding 6.3 GB at launch pinned it at 1, which would have run all sixteen in sequence (~18 h). Relaunched twice, no run interrupted | `PREREGISTRATION_D2.md` §6a |
| `verify_docs.py`'s premise pattern read the interquartile range on D2's baseline row as a contradiction of the premise figure, because it cannot read four-digit damage (1118.0). Scoped the two premise figures away from the D2 result files, by name | `verify_docs.py` |
| `generality_test.py`'s "103 g/s, τ 7 % low" comment pointed the wrong way on today's scenario: measured 118.1 g/s, τ 48.3 s, agreeing with the step response | `generality_test.py` |
| **commit `6e40cd8` changed "nine drives" to "ten" without re-measuring**, in mistake 14 and `app/alerts.py` | `CLAUDE.md` mistake 11 addendum |
| **HTML-comment markers were invisible to the guard**, and marker explanations were read as figures | `verify_docs.py`; `CLAUDE.md` mistake 11 addendum |
| **emptying the ledger silently removed the only catch for an edit of +11.7** — drift_test 16 → 14; restored as `PINNED_HISTORY` | `verify_docs.py`; `CLAUDE.md` mistake 11 addendum |
| the deck argued the void result on ~70 lines, and its race widget printed the C3 claim as a conclusion | commit `3f4627d` |

### Decisions taken, by whom

| decision | by | recorded in |
|---|---|---|
| the minimum effect of interest is 50 damage units | **Jad** | `PREREGISTRATION_D2.md` §5 |
| run D2 as planned — eight seeds, C1 — knowing it has power 0.10, and declare it | **Jad** | `PREREGISTRATION_D2.md` §4, §5a |
| D2 as a wrapper, `engine_env.py` untouched | proposed, adopted | `random_road.py` |
| the fix-3 guard findings go into mistake 11 as an addendum, not a new mistake 19 | proposed | `CLAUDE.md` |
| **the next experiment is C4 — D2's design at 300 000 steps — and it runs in a NEW session** | **Jad**, 23 Sep | this entry; `CLAUDE.md` live list; `NEXT_SESSION_2026-09-23.md` |
| **one variable at a time: C4 first, more seeds only after, never both at once** — in Jad's words, «ولا كذا ما نعرف مين السبب، فنسويهم واحد واحد عشان نقدر نحدد» | **Jad**, 23 Sep | same |

### Process failures in this session, stated

- **Three numbers were written before they were checked**, and each was caught
  before it was committed: "every MEI from 10 to 400 gives INCONCLUSIVE" (false
  above 87.2); "18 blockers across 21 files" (13 and 19); and a round-2 agent's
  "as of 14 September" (the sentence is from 16 September, commit `4905498`).
  The rule from the last session held: check the claim before it lands.
- Elapsed time was misjudged once (eight minutes read as forty-five) while
  deciding whether a run was stalled. No consequence; the timestamps settled it.

### Open, and the next session's to close

1. **C4 — DECIDED (Jad, 23 Sep), for the next session.** D2's design, eight
   seeds per arm, 300 000 steps (~66 training climbs per agent against C1's 11),
   ~16 hours of training in the background. Its own preregistration first.
   More seeds comes AFTER C4, and only if C4 leaves the question open — one
   variable at a time. `NEXT_SESSION_2026-09-23.md`.
   **Its first task is to disarm three traps, verified at close by a
   read-only review of that prompt:** `train.py` resumes any run directory
   whose FATAL fingerprint matches, and `steps` is only advisory — so a
   300 000-step launch into `runs_d2/` or `runs/` would resume and overwrite
   the D2 or Phase D agents, and the launcher truncates their training logs
   at launch; `--evaluate` hard-codes the `d2` result prefix; and
   `check_d2_tracking.py` hard-codes `runs_d2/`. **Both agent directories are
   backed up** (23 Sep, 184 and 189 files, spot-checked byte-identical) at
   `graduation project/GRAD-agent-backups/2026-09-23/`, outside the repo.
2. **The ablation chapter** — Phase D and D2, both findings kept separate, the
   failed spread prediction stated.
3. **Small, recorded:** `app/alerts.py` `VALID_MAP_HI` 74 in code against the
   30–75 kPa span; the deck tabulates 13 of 18 mistakes; `run_phase_d.py`'s
   one-shot concurrency cap.

## Session of 23 September 2026 — C4: the traps closed, preregistered, running

Commits `f987049` … `87ee394` on `JMF-2340550-sep17`, run from
`NEXT_SESSION_2026-09-23.md`. **C4 is TRAINING at the time of this entry** —
launched 16:42, sixteen runs, ten at a time; no C4 result exists.

### The state in one paragraph

C4 is Phase D2's design at 300 000 steps per run — ONE variable changed, the
training budget, by Jad's rule (one at a time; more seeds only later, never
both). It was preregistered in `results/PREREGISTRATION_C4.md` (`79568e2`)
before any of its sixteen agents trained, pinning the code at `a1af19a`. At
17:00 all ten first-wave runs were **bit-identical to their D2 twins at
10 000 steps** (`check_c4_start.py`, 10 of 10) — C4 is, so far, D2's agents
trained longer.

### What the session set out to do, and did

| step | state | where |
|---|---|---|
| 1 · disarm the three traps | **done, and hardened twice by review** — see below | `f987049`; `train.py` "A RESUME IS NOT A LONGER RUN"; `run_phase_d.py` docstring |
| 2 · preregister C4 before training | **done** — `79568e2`, after two adversarial reviews and a calibration | `results/PREREGISTRATION_C4.md` |
| 3 · launch | **running** since 16:42 from a clean tree; launcher detached from the session (WMI) | section 6a; `runs_c4/launcher_train.log` |
| 4 · the ablation chapter | **drafted and reviewed** | `thesis/CHAPTER4_ABLATION_DRAFT.md` (`87ee394`) |
| 5 · the C4 test | **waiting on training** — expected ~07:00 on 24 Sep | `PREREGISTRATION_C4.md` section 9 |

### What was found that nobody asked for

| finding | where it lives |
|---|---|
| **a finished run with only `checkpoint.zip` left resumed "at 0 steps" and trained over itself** — the step count came from the file NAME. Older than C4; closed by reading it from the zip | `train.py`; `fingerprint.model_budget` |
| **the first crash-rule fix would have moved LIVE runs** — a live run and a crashed one look identical on disk. Closed with a `RUNNING` mark, a 30-min quiet check and a required `--seeds` | `fingerprint.running_pid`; `run_phase_d.py` |
| `--steps 300000` with a forgotten `--out` would have extended D2 with new seeds, which its pinned analysis globs in; `runs/` and `runs_d2/` are now CLOSED | `train.py`, `run_phase_d.py` |
| the draft preregistration read a C4 separation as proof the budget mattered; D2 was INCONCLUSIVE, not a shown absence. A paired budget-change test was added (5c) | `PREREGISTRATION_C4.md` 2a, 5c |
| the convergence rule's noise floor, measured: one gradient step moves an agent's practice damage by max 7.9 units, a pair by max 8.5 — against a 25-unit band. D2's C1 agents moved a median 118.2 between 30k and 50k (15 of 16 beyond the band) | `results/c4_convergence_calibration.txt` |
| a fresh 300 000-step run on today's tree reproduces D2's agent bit for bit at 10 000 steps — then confirmed for all ten first-wave runs | `PREREGISTRATION_C4.md` 3a, 6a |
| `power_analysis.py` still said randomising the climb does NOT shrink the spread, after D2 measured that it did; and asserted convergence would | `power_analysis.py` docstring |
| **the IQR / worst-episode columns weaken the supervision claim**: on the worst episode 5 of 8 sighted agents in each experiment are worse than `current-grade`'s worst; in D2 the sighted agent has the wider IQR in 6 of 8 seeds | `thesis/CHAPTER4_ABLATION_DRAFT.md` 4.5, 4.7 |
| per-run peak memory is 1519 MB with a 300 000-slot buffer — `PEAK_GB` 1.5 holds | `PREREGISTRATION_C4.md` 6a |

### Decisions taken, by whom

| decision | by | recorded in |
|---|---|---|
| convergence judged at checkpoints 200k/250k/300k on ten practice episodes, 25-unit band, 6 of 8 per arm — over the learning curve alone, or all sixteen | **Jad** | `PREREGISTRATION_C4.md` 5b |
| **add the pair condition** (7 of 8 seed pairs settled), after the calibration | **Jad** | same |
| push to `JMF-2340550-sep17` for the whole session | **Jad** | — |
| launcher started as its own process, so closing the session cannot stop C4 | proposed, done | 6a |

### Process failures in this session, stated

- **Elapsed time misjudged twice** — "calibration ends ~15:00", then
  "~15:20"; it ended ~15:42, and the launch was at 16:42. No consequence; the
  clocks were checked before any time was written into the run log.
- **A shell heredoc turned `\n` escapes into real newlines** in one patch to
  `check_d2_tracking.py`; caught by a parse check before anything ran, and
  repaired with a script.
- **The trap fix as first written had two holes** (live runs moved; the
  `checkpoint.zip` resume). Both were found by the review, not by the author —
  which is why the review ran before the commit.

### Open, and the next session's to close

1. **While C4 trains:** `python check_c4_start.py` after the second wave
   reaches 50 000 steps. A crash is re-run FROM SCRATCH with
   `--seeds <k> --restart-crashed`, never resumed. **Do not edit tracked files
   while a wave is starting** — the launcher holds its queue while the tree is
   dirty. Windows Update was not confirmed paused.
2. **After training — `PREREGISTRATION_C4.md` section 9, in this order:**
   `check_c4_start.py --out results/c4_identity.txt` and
   `check_c4_convergence.py`, COMMITTED; then
   `run_phase_d.py --road random --out runs_c4 --evaluate --jobs 8`; then
   `check_d2_tracking.py runs_c4 --out results/c4_tracking.txt`; then
   `python analyse_c4.py`. Write the result into `PREREGISTRATION_C4.md`
   section 11, `CLAUDE.md`, `results/README.md` and Chapter 4.10.
3. **Small, recorded:** `app/alerts.py` `VALID_MAP_HI` 74 in code against the
   30–75 kPa span; the deck tabulates 13 of 18 mistakes; capture
   `check_d2_tracking.py --out results/d2_tracking.txt` once the machine is free,
   so Chapter 4 cites a file rather than a record.

## 24 September 2026 — C4 has a result: SMALLER THAN THE MEI, not converged, and it hangs on one seed

Commits `4bfece8` … on `JMF-2340550-sep17`. Training finished 07:25 (16 of 16,
882 min, no failure); evaluated 08:26–09:47; torque checked by 10:25.

### The result

```
python analyse_c4.py          (results/C4_RESULT.txt)
                         Phase D (post-hoc)   Phase D2        C4
positive                 5 of 8               4 of 8          3 of 8
mean / sd                +4.8 / 214.4         +6.4 / 98.8     +30.2 / 139.9 (median -1.3)
below the MEI  sign      0.6367               0.1445          0.0352 (7 of 8)
               perm      0.2578               0.1250          0.3867  <- DISAGREES
cell                     INCONCLUSIVE         INCONCLUSIVE    SMALLER THAN THE MEI
convergence (C4 5b)                                           NOT-CONVERGED 2/8 1/8 pairs 1/8
budget-change test (5c)                                       p 0.6367 -- not shown
```

- **The preregistered reading, verbatim:** *"Preview's effect is below the MEI
  at 300 000 steps: (i) is supported AT THIS BUDGET. The agents were still
  changing, so (ii) is not ruled out."*
- **It hangs on one seed.** 7 of 8 is exactly the sign test's threshold; the
  permutation test disagrees because seed 0 carries +360.6 — its blinded agent
  got worse with longer training (practice damage 538.8 → 694.5; test damage
  145.3 worse than at 50 000 steps). Described, not dropped.
- **C4 is D2's agents trained longer:** 80 of 80 checkpoint pairs identical to
  D2 through 50 000 steps (`results/c4_identity.txt`).
- **Supervision, separately:** sighted beats `current-grade` on the median in
  8 of 8, blinded in 7 of 8; on the worst episode 4 of 8 sighted and 5 of 8
  blinded are worse than `current-grade`'s worst. No agent refuses torque
  (`results/c4_tracking.txt`, 0 of 16).

### Where it lives

`results/PREREGISTRATION_C4.md` section 11 (the account) and 6a (the run log);
`results/C4_RESULT.txt`; `results/c4_identity.txt`, `c4_convergence.txt`,
`c4_tracking.txt`, `c4_seed0-7.txt`; `CLAUDE.md` (the box); `results/README.md`;
`thesis/CHAPTER4_ABLATION_DRAFT.md` 4.10 (added after the reviewed draft).

### Open — the team's decision

**What next:** a longer budget (the agents were still changing) or more seeds
(the result hangs on one seed) — one variable at a time, with its own
preregistration. `C4_RESULT.txt` and section 11 are what to decide from.

### SESSION CLOSE, 23–24 September 2026 — the index

Commits `f987049` … on `JMF-2340550-sep17`, all pushed. Run from
`NEXT_SESSION_2026-09-23.md`; the next session's prompt is
`NEXT_SESSION_2026-09-24.md`.

| step of the plan | outcome |
|---|---|
| 1 · disarm the traps | done; the review found two holes in the first fix, both closed |
| 2 · preregister C4 before training | `79568e2` |
| 3 · train | 16 of 16, 882 min, no failure; 80 of 80 identical to D2 through 50 000 steps |
| 4 · the ablation chapter | `thesis/CHAPTER4_ABLATION_DRAFT.md`, reviewed; 4.10 updated after C4 |
| 5 · the C4 test | SMALLER THAN THE MEI (sign p 0.0352), permutation disagreeing (0.3867), NOT-CONVERGED |

Found at close, and fixed before it — mostly by the review of the next
session's prompt, which found the documents around it lagging:

| what | fixed |
|---|---|
| `CLAUDE.md`'s TOP still said "C4 NOT done", the live list still said "the next experiment is C4", and G · writing said "not started" | a "Current state — 24 September (after C4)" box at the top; phase rows C, D, G; the 23 Sep live list marked superseded; `analyse_c4.py` in the numbers block |
| `README.md` said "No D2 result exists yet" a day after D2's result | D2 and C4 results, with the correction dated |
| the presentation said "C4 not done" and "no D2 result yet" in seventeen places across both languages | all corrected (`grep` for the pending phrases now finds none). *(This row, and commit `5d75707`'s message, said "eleven" -- a miscount; the four passes made 6 + 8 + 2 + 1 = 17 edits. Corrected 26 September.)* |
| `runs_c4/` had no backup — the only copies | `GRAD-agent-backups/2026-09-24/runs_c4`, 587 files, all sixteen `final.zip` sha-checked |
| `runs_c4/` could still take new seeds; `runs_C4` walked past every closed-experiment guard (NTFS is case-insensitive) | `runs_c4` / `c4` added to all three CLOSED tables, compared case-insensitively; tested |
| the planning figures for the next experiment (power 0.15; ~80 seeds per arm; ~11 without seed 0) were printed by no script | `power_analysis.py` gains a C4 section that prints them, with the sensitivity labelled planning-only |
| the prompt's option B would have retrained seeds 0-7 — C4 itself, bit for bit | the prompt now says NEW seeds only, reported beside C4, never pooled |

**Open:** the next experiment — a longer budget or more seeds, one at a time —
is Jad's and the team's decision; `NEXT_SESSION_2026-09-24.md` carries both
options with their measured costs.

## 26–27 September 2026 — Jad briefed on C4, one idea at a time; the visual-simulation prompt; no experiment run

Commits `18f5d66` `79eb8a0` `19fbca4` `7fff577` `46019f6` `6e435ba` `cc1418b`
`b6b8149` on `JMF-2340550-sep17`, all pushed. Nothing trained, scored or
re-analysed; no figure in `results/` moved.

### What the session did

| what | where it landed |
|---|---|
| Jad, back from being away, asked what the C4 session did. A five-part reply lost him; one idea per message, each with a familiar example and one question, got him through C4's result, the preregistration, typical-versus-worst ride and why eight pairs | `team/jad.md`, 26 September — what landed, which examples worked (kabsa pots; "our constitution"; two students; seed 0 alone), and a new rule: a multi-point question still gets a one-point answer |
| the next-experiment options, one at a time: **A explained**, and Jad answered its check question correctly ("the training is incomplete"). **B and C not yet explained** | `NEXT_SESSION_2026-09-27.md` |
| a prompt for the visual simulation (the replay lab): agents' experiments current and future, road grade, a map built from the experiments' own grade, and jev as a hidden feature | `NEXT_SESSION_VIZ_2026-09-26.md` |
| "jev" identified from the page Jad sent: typesafe.ai's hosted "System One" model — structured state in, typed decisions out, early access by waitlist. Only the vendor's claims are recorded, labelled as claims | the same prompt, section JEV |
| the C4 close's CHECKPOINT row and commit said the deck was fixed in "eleven" places; it was seventeen | corrected in place (`18f5d66`) |

### Found, stated

- `node --test app/static/sim/` **fails** on this machine's Node 24 (a bare
  directory is read as a file); the quoted glob `"app/static/sim/*.test.mjs"`
  ran 30 of 30 passing at the time, before the agent-replay session added its
  own tests. The viz prompt uses the glob.
- **Process failures:** the five-part explanation (Jad: "you complicated it");
  and one reply went out in English despite the profile's "Arabic first" —
  Jad had to ask for Arabic.

### The other session, recorded not verified

A separate session ran from `NEXT_SESSION_VIZ_2026-09-26.md` and committed
**Agent replay M1** — 28 commits, the last at 02:52 on 27 September: one C4 pair
driving one frozen episode side by side at `/agents`. Its record is
`docs/superpowers/specs/2026-09-26-agent-replay-design.md` (rulings and deferred
items at the end). `git diff --stat` from `b6b8149` shows it touched only `app/`
and `docs/` — not `plant.py`, `thermal.py`, `engine_env.py`, `random_road.py`,
`evaluate.py`, `train.py`, `fingerprint.py` or `run_phase_d.py`. **This session
did not re-run its tests;** read its own commits for those.

### Open

- **The next experiment — A, B or C — is still the team's decision.** B and C
  still need their one-at-a-time explanation to Jad.
- **jev needs early access and an API key** that Jad may not have; the viz
  prompt makes that the first question.

## 28 September 2026 — the team's profiles, "ask who you are", and two chart pages

Commits `064aba6` `b146ba7` (already on GitHub: the other session's push of
its M2 work carried them) and `29c78d5` `55d18db` `8c39617` `3b5ccd8` (not
pushed yet), all on `JMF-2340550-sep17`. Nothing trained, scored or
re-analysed; no figure in `results/` moved. This entry was written mid-session,
after a usage limit had already cut the session off once, and is extended at
close.

### What the session did

| Jad asked | what landed | where |
|---|---|---|
| profile files for the other four | stubs for Khaled, Abdulhadi and Mohammed: a name and a student number, every other section "Unrecorded"; the student number in the frontmatter of all five files and the template | `team/` (`064aba6`) |
| "the first thing it does is ask who you are" | `CLAUDE.md` now opens by asking «مين معي؟» unless the person already said who they are. Matching `git config user.email` is retired: AUDIT2.md Part 6 had found two of the three identities in the history matching no file. A stub is said to be a stub and never filled from a guess; subagents skip the question | `CLAUDE.md`, `team/README.md` (`b146ba7`) |
| "the charts comparing the simulation's results with our data" | five charts, each labelled with its kind of evidence: the gearbox and the boost pressure are independent checks, the compressor envelope and the enrichment map are fits, and the load residual is a consistency check (mistake 12). Every number is printed in `numbers.txt` | `plot_sim_vs_car.py`, `figures/sim_vs_car/` (`29c78d5`) |
| "why not put it on a website" | the same page in the viewer's light or dark theme, safe on a phone, published privately at https://claude.ai/artifact/YWSKwwCEPAwg1oMXCVXTec | `figures/sim_vs_car/page.html` (`8c39617`) |
| "add the agents' points and the seeds" | a second page: Phase D, D2 and C4, eight pairs each, every agent a dot, every verdict quoted by `app/agent_catalog.verdict()`, nothing computed. Published at https://claude.ai/artifact/6B2gRmzj4RT1ysLZoFNJMg; the two pages link to each other | `plot_agent_pairs.py`, `figures/agent_pairs/` (`3b5ccd8`) |
| "something like this, but with my data", pointing at a page built from another branch | the same kind of page from this branch: summary tiles, the three ablations, every C4 policy's typical and worst episode, damage against fuel, the roads, the simulator against the car with a status table, the drives, the caveats. Its counts reproduce `CLAUDE.md`'s: C4 medians below current-grade's for 8 of 8 sighted and 7 of 8 blind agents; worst episodes above current-grade's worst for 4 of 8 and 5 of 8; `validate.py` 8 of 11. Published at https://claude.ai/artifact/9fCJ1tYWQLj3qrUsaQ5yeW | `plot_study_page.py`, `figures/study/` |
| "compare them with our baseline, not only the blind agent with the other; can you, or must we change the code and retrain?" | **No code change and no retraining.** `evaluate.py` already printed each policy's share of the baseline ECU's median damage removed (the "cuts median damage" lines of every `results/<experiment>_seed<k>.txt`), so each experiment now opens with every agent against the baseline, current-grade drawn beside it as the policy an agent has to beat. Each value is read and checked against the medians in the same file. C4: sighted agents remove 46.1–70.2 %, blind agents 35.6–68.9 %, current-grade 41.5 %. The sighted-against-blind pair chart stays under it, because it is the preview test registered before training | `plot_agent_pairs.py` (`chart_vs_baseline`), `plot_study_page.py`; both pages republished |

**The page Jad pointed at is not this branch's.** It says it was built from
`JMF-2340550 @ 480711b`. That commit is in neither this repository nor on
GitHub, where `JMF-2340550` stands at `7f6c7f1`. Its experiment is a different
one: five seeds, scored in points, trained at 110 km/h, with code changes this
branch does not have (a gearbox kick-down, a refitted spark map). Its numbers
will not match this branch's, and should not be compared as if they measured
the same thing.

### Found, stated

<!-- RETIRED-OK: 0.027 -- the figures of that session, before the merge of 30 September -->
- **The enrichment map misses the car by 0.076 in λ in one cell** once the
  dwell axis is the corrected one (AUDIT.md H3). The documents said every cell
  sat within 0.027. The full account, and why no experiment is touched, is in
  `CLAUDE.md`'s limitations (`55d18db`).
- **Mistake 13's "117 °C median" does not reproduce.** The 587 samples behind
  its 279.5 kPa, which does reproduce, read 106.8 °C. Recorded under that
  table in `CLAUDE.md`.
- **matplotlib cannot be imported on Jad's machine.** Windows Application
  Control blocks its `_image` DLL on the system Python as well as the `.venv`.
  The charts are therefore plain SVG, turned into PNG and PDF by headless
  Chrome.
- **`verify_docs.py` has three false-positive traps for generated pages.**
  Each was avoided in the output and none was fixed in the guard. First, a
  line that begins with an rpm band and ends with a number is read as a row of
  `base_lambda`'s sample-count table. Second, the retired load-residual
  pattern has no leading boundary, so a live value ending in 2.3 or 2.8 with a
  percent sign after it fails. Third, the premise-baseline pattern reads the
  word "baseline" in a table header and takes the first three-digit figure on
  the next row. Fixing them means editing the guard and re-running
  `drift_test.py`.
- **Correction to commit `3b5ccd8`'s message.** It counts the pairs at or above
  the 50-unit minimum effect as "one in D2, one in C4, three in Phase D". The
  pages are right and the message is not: four in Phase D (seeds 2, 3, 6 and 7),
  two in D2 (seeds 0 and 4), one in C4 (seed 0). The commit is history and is
  not rewritten.
- **Another session built Agent replay M2 in the same working tree** during
  this one (tasks 6 to 9) and pushed through task 6 (`a4a23a0`). Recorded, not
  verified. Every commit of this session was made by explicit path, so neither
  session's files entered the other's commits.

### Open

- `base_lambda()`'s docstring table still shows the old-axis median for the
  high-speed, medium-dwell cell. Correcting a docstring is safe for the agents;
  it is left for a moment when no build is running in the tree.
- The four new profiles are stubs until their owners fill them in.
- The study page's second stage, each needing new simulator runs: the turbine
  temperature through an episode, why 12 % at 130 km/h, and the training
  curves; and three comparisons with the car not yet computed on this branch
  (part-load spark, oil over a whole drive, the knock replay).
- The next experiment (A, B or C) is still the team's decision, and B and C
  still need their one-at-a-time explanation to Jad.
- The installed `/i-have-adhd` skill is the old version: it still says "Five
  items ranked beats ten unranked", which `team/jad.md` asks to have updated.
  It is a synced skill, so the lasting update belongs in Jad's claude.ai
  account.

## Entries from Ghassan's branch, `JMF-2340550`, 19–28 September 2026

*Added by the merge of 30 September 2026. These three entries were written on
`JMF-2340550` while the entries above were written on `JMF-2340550-sep17`; they are
kept whole, as written. Two readings in them were corrected by the merge review
(`conflict.md`): the 19 September entry's "rpm and exhaust flow both rise" is the
reading the sep17 entries measured the other way (both are true against different
six-speeds), and "sep17 has the six-speed box" was wrong.*

## Session of 19 September 2026 — the real gearbox, and the scenario binds again

### The headline, because it reverses a blocker

Fitting the car's **actual transmission** made the standard scenario reach the
protection trigger for the first time since the audit fixes. The model had a
generic six-speed with invented ratios; the car has a **ZF 8HP51**.

| scenario | peak turbine | share of episode above 850 °C |
|---|---|---|
| 110 km/h, 12 % — this branch's default | 839.7 °C | **0.0 %** |
| **130 km/h, 12 % — the `sep17` lock** | **884.0 °C** | **66.3 %** |

The real box holds **7th** on the climb (2.589 overall) where the invented
six-speed sat in top (2.312), so rpm and exhaust flow both rise. **The blocker
went by the model becoming more correct**, not by a knob being turned — and the
130 km/h lock was decided on 18 September, before any training existed.

### The gearbox, and how it was verified

Toyota's own sheet names the unit "8-speed Sports Automatic 8HP 51" and prints
all eight ratios plus the 3.150 final drive; Toyota USA's pressroom confirms
3.15 on the 382 hp car independently. But the car is the better witness:

> **86.7 % of 79 105 moving samples land within 4 % of one of the eight
> published ratios**, and the measured top-gear overall ratio of **1.998**
> matches the 8HP51's 8th (2.016) to 0.9 % while matching nothing on the
> six-speed manual (2.927).

`UPSHIFT_MIN_RPM` is calibrated against the car rather than guessed — 2000 rpm,
bias +0.28 gears, 79.7 % within one. Exact agreement peaks at ~47 % for ANY
threshold, because a real automatic shifts on throttle and load too. That is the
honest headline and it is in the docstring. It was not tuned to move a result:
1400 and 2000 rpm both select 7th at the scenario.

### Mistake 18 — `Actual gear` clamps at 6

The verification broke a channel. `Actual gear` never exceeds 6 across 45 606
moving samples; within the samples it labels "gear 6" there are three clusters
at 2.016, 2.589 and 3.15 — 8th, 7th and 6th. **The channel saturates.** Fourth
misread channel on this car, and the first that fails by RANGE rather than
meaning. The knock-retard p99 is filtered with it and must be re-derived.

### Phase C ran, on the wrong scenario

Ten SAC agents — 5 sighted, 5 blinded, 50 000 steps, **173 minutes each**, ten
sharing a 20-core machine (~4.5 steps/s each, ~45 aggregate against 9.4 solo).

**They trained at 110 km/h, where nothing binds.** They had nothing to protect
against, so they cannot settle Phase D. The runs are kept; the next action is to
retrain at 130.

**And they produced exactly 11 episodes each**, which is the arithmetic in
`evaluate.py`'s docstring: 4500 steps per episode, three preference weights
drawn fresh each reset, so the policy must generalise across a 3-D simplex from
eleven samples of it.

### Two defects found in tooling

- **`evaluate.py` printed a scenario it was not running.** Its header was the
  literal string "12 % at 130 km/h" while the env took `make_grade_climb`'s
  DEFAULT — 110 on this branch. It now derives the line from the cycle and
  cannot disagree with what it scored.
- The compression-ratio open question is **settled**: the team confirmed the
  285 kW / ~386 hp car, so `plant.py`'s 10.2:1 is right and Toyota UK's 11.0:1
  belongs to the 250 kW variant.

### Verified

<!-- RETIRED-OK: 295.0, 10 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK: dated record; validate.py read 8 of 11 until rows 8-11 moved onto car data on 28 September -->
```
verify_docs.py    All 38 checks pass, 309 figure mentions, 24 tracked files
validate.py       8 of 11 inside band, unchanged (no plant change)
test_reward.py    4 of 4, neutral inside the ±0.05 band
app.test_replay   49 of 49
build_dataset.py  295.0 min, 10 drives, 26 operating points
```

### What this session did NOT do

- **No valid Phase D number.** The agents trained off-scenario.
- **No merge with `sep17`.** Twelve commits still apart.
- **The 850 °C trigger is still unverifiable on this car.** Its only exhaust
  channel is modelled, post-catalyst and clamped at 645.3 °C.

### Later the same day — the scenario is loaded, and the logs explain why it had to be

**`make_grade_climb` now defaults to 130 km/h**, the value `sep17` locked on
18 September before any training existed. Adopting it is not tuning; it is
catching up to a decision already made.

**Why elevation belongs in the scenario at all.** The car's own logs cannot load
the engine, and this is measured rather than asserted — over 79 134 moving
samples from the ten drives:

| | |
|---|---|
| median relative air filling, per drive | **24–40 %** |
| samples above 120 % relative filling | 1 563 of 79 134 — **2.0 %** |
| median road speed, per drive | 95–137 km/h, peaks past 200 |

**The driving is fast but not loaded.** Straight-line motorway cruising on flat
road asks for aerodynamic drag and rolling resistance and nothing else. No
amount of further logging will exercise the thermal model's hot region — the
duty cycle is wrong, not the model. Measured on the simulator:

| speed | grade | peak turbine |
|---|---|---|
| 90 km/h | 0 % | **335.4 °C** |
| 90 km/h | 6 % | 540.6 °C |
| 90 km/h | 12 % | 717.0 °C |
| 130 km/h | 12 % | **884.0 °C — binds, 66.3 % of the episode** |

**What the loaded scenario shows.** `check_premise.py`, hand-written policies:

<!-- RETIRED-OK: 959.8, 884 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK -->
| policy | damage | cuts | peak turbine |
|---|---|---|---|
| baseline ECU (true neutral) | 959.8 | — | 884 °C |
| reactive protection | 679.0 | 29.3 % | 862 °C |
| current-grade protection | 633.2 | **34.0 %** | 861 °C |
| predictive protection | 637.4 | 33.6 % | 861 °C |

**Every policy does real work now** — the reactive row is no longer a copy of
the baseline row, which it was at 110 km/h. **Preview is −0.4 points against
current-grade**, the closest to level it has been. The question is open rather
than trivially negative, and only a trained pair can settle it.

<!-- RETIRED-OK: dated record; validate.py read 8 of 11 until rows 8-11 moved onto car data on 28 September -->
`test_reward.py` 4 of 4 on the loaded scenario, neutral **−0.00038**.
`verify_docs.py` 38 of 38. `validate.py` 8 of 11. `app.test_replay` 49 of 49.

---

## Session of 21–28 September 2026 — training roads, two fixes, three comparisons re-read

Full account: `SESSION_REPORT_2026-09-28.md`. What was verified, and on what:

<!-- RETIRED-OK: 951.9, 884, 7 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK -->
| check | result, 28 September |
|---|---|
| `verify_docs.py` | all checks pass |
| `test_reward.py` | 8 of 8 — four new checks on the training roads |
| `check_roads.py` | PASS over 40 roads; 11 bind; worst neutral +0.004, worst p95 tracking 0.015 |
| `check_premise.py` | baseline 951.9 at 884 °C; current-grade cuts 34.4 %, predictive 34.0 %; preview −0.4 |
| `validate.py` | 7 of 11 — rows 8–11 (oil, coolant) now scored against our own car; it read eight of eleven against literature bands |
| `check_map.py` | 6 cells above the compressor ceiling, 0 without knock-free spark (unchanged) |
| `python -m app.test_replay` | 49 of 49; `--full` 59 of 59; `pull01` pin 608.0 → 609.2 °C with its reason (that morning) |
| `model_vs_data.py` | eleven comparisons: 3 agree, 3 limited, 3 off, 1 untested, 1 not covered — drive10's oil and coolant moved to *off* once the replay was fed the car's measured fuel |
| `evaluate.py`, ten existing agents | training +25.9 pts over current-grade; ablation mean −0.5, CI −2.0 to +1.1 |

What changed in the simulator: the gearbox kicks down when the engine cannot
deliver the request (`Vehicle.DELIVERABLE_TORQUE`), and the part-load spark
map's offset was refitted (`SPARK_A` 26.18 → 13.33). What changed in training:
a new road every episode, dt = 1.0, output to `runs/terrain_dt1/`. Scoring is
untouched.

What was re-read without changing the model: the knock test rests on one
reading per ~8 s and is untested; preview's −0.4 is entirely the knock term;
the existing logs cannot calibrate the oil node. The retrain has not been run.

### Later on 28 September — the car scores its own oil and coolant

`validate.py` rows 8–11 (oil and coolant) moved off literature bands, three of
which had no source, onto bands computed from our own drives. The replay is
`car_thermal.py`, shared by `validate.py` and `model_vs_data.py`: free-running,
seeded at the first real reading, fed measured fuel (air mass / 14.7 λ).

| row | model | band, from our car | |
|---|---|---|---|
| 8 oil, drive10's hottest 10 min | 96.4 °C | 103–111 | outside |
| 9 oil apparent time constant | 14.0 s | 70–100 | outside |
| 10 coolant, synthetic climb | 94.5 °C | 83.5–95.6 | inside |
| 11 coolant, drive10 | 88.4 °C | 91.8–94 | outside |

<!-- RETIRED-OK: 7 -- the figures of that session, before the merge of 30 September -->
<!-- RETIRED-OK -->
**7 of 11** (that afternoon): 6 of 7 literature, 1 of 4 car. The car's oil τ implies
c_oil ≈ 60 000–86 000 J/K against the assumed 12 000; `thermal.py` unchanged,
because it moves the locked scenario. REFERENCES.md gained section 2c (GCC
spec: no uprated cooling found; 95 vs 98 RON moves only the knock term) and
section 3 now grades rows 8–11 as MEASURED (ours). Found by hand: REFERENCES
still quoted the pre-H1 best BSFC (239.9 since); fixed and guarded in
`verify_docs.RETIRED`. Verification on this tree is in the commit message.

---

## Session of 28 September 2026, evening — drive B, and the constants the data sets

Full account: `SESSION_REPORT_2026-09-28_evening.md`. Verified on this tree:

<!-- RETIRED-OK: 920.1, -0.3 -- what check_premise printed on 28 September; 848.1 and -0.0 since 8 October -->
| check | result, 28 September (evening) |
|---|---|
| `build_dataset.py` | 321.7 min, 11 drives, 26 operating points; drive B's 7 windows dropped (no spark or lambda channel); then `derive_params.py` |
| `derive_params.py` | thermal fit on 7 drives, oil τ 57 s, stat opens 92.1 °C, radiator ×1.42; envelope over 11 bins, cap 2.515; SPARK_A 13.42; ENR_DWELL 1.5 / 3.0 s |
| `validate.py` | **8 of 11**: 6 of 7 literature, 2 of 4 car — rows 10 and 11 inside, rows 8 and 9 outside |
| `check_premise.py` | baseline 920.1 at 883 °C; reactive 625.7, current-grade 520.5, predictive 523.5; preview over current-grade −0.3 |
| `test_reward.py` | 8 of 8 |
| `check_roads.py` | PASS; 14 of 40 roads bind |
| `check_map.py` | unchanged shape; 6 cells above the ceiling, 0 unsafe |
| `compare_log.py` | 1.4 % derived (k 0.831); 1.1 % fitted (k 0.839) |
| `model_vs_data.py` | charge temperature +1.9 % (drive B's assumed-ambient rows excluded); drive10 oil median −1.6 K, coolant −0.6 K |
| `python -m app.test_replay` | 49 of 49; `--full` 59 of 59. Pins moved and attributed by reverting one change at a time: `pull01` 609.2 → 604.8 °C, thermal 1 → 0 (the derived enrichment dwell); `7475b5d7` 890.6 → 873.1 °C, thermal 15 → 14 (exhaust = air + fuel) |
| `generality_test.py` | τ axis on the measured 121.3 g/s; preview over CURRENT-GRADE 0.0 points at every τ and cost curvature (the reactive edges are 13–80 points) |
| `run_results.py` | traces, sweep (3 of 12 bind; 12 % / 130 km/h 883.0 °C) and the ten old agents re-scored: +25.7 over current-grade, ablation mean −1.3 (t −0.53) |
| `verify_docs.py` | all checks pass (run it and read its total) |

What changed in the simulator, one step at a time and each measured, is
section 6 of the session report and `results/figures/fig23`.

---

## Session of 29–30 September 2026 — the two branches merged

Ghassan's `JMF-2340550` (`74de99a`) was merged into Jad's `JMF-2340550-sep17`
(`086c519`) in a separate clone, reviewed conflict by conflict, and finished after
both accepted the five decisions (`conflict.md` section 0; Ghassan's written reply
of 30 September). **The rule: Ghassan's physics, Jad's method.** The full account is
`SESSION_REPORT_2026-09-30_merge.md`; the review's evidence is `_merge_review/reports/`.

| what | result |
|---|---|
| conflicts | 15 files, 91 hunks, resolved hunk by hunk as `conflict.md` recommends |
| files dropped | none: every file of both branches is in the merge. Two were MOVED, not deleted: `results/phase_d_seed0_110kmh.txt` to `results/void/` (it turned Phase D's n = 8 into 9), and `NEXT_CHAT_PROMPT.md` to `NEXT_SESSION_2026-09-29_ghassan.md` with a superseded banner |
| tags | `sep17-before-merge` (`086c519`, plant_sha `b5a3069f32a83754`) and `ghassan-before-merge` (`74de99a`) |
| merged plant | plant_sha `c236a8db3e201090`; all 48 of Jad's agents are refused on it, correctly |

Checks, run on a copy of the resolved tree before committing:

| check | result |
|---|---|
| `analyse_phase_d.py` / `analyse_phase_d2.py` / `analyse_c4.py` | 5 of 8, sign p 0.3633 / 4 of 8, 0.6367 / SMALLER THAN THE MEI — the preregistered figures, unchanged |
| `validate.py` | 8 of 11 (6 of 7 literature, 2 of 4 car) |
| `test_reward.py` | 8 of 8 pass; neutral −0.00028; starver −0.13265 (97 % of it from the launch — the training-road starver, −2.32655, is the check that holds) |
| `check_premise.py` | baseline 920.1 at 883 °C; preview over current-grade −0.3 <!-- RETIRED-OK: 920.1, -0.3 -- the merged plant's, as printed that day --> |
| `check_roads.py` | PASS, 40 roads, 14 bind |
| `random_road.py` | self-test passes, road sha `1a29dc46db24f233` |
| `python -m app.test_replay --full` | 59 of 59 (pins 873.1 °C, 604.8 °C, 14 thermal) |
| `python -m app.test_simulation` | 15 of 15 |
| `python -m unittest app.test_agents` | 129 OK, 14 skipped (they need the gitignored `runs*/`) |
| `verify_docs.py` | all 73 checks pass, 837 figure mentions scanned |
| `drift_test.py` | 16 of 16 drifts caught (rows 6 and 13 re-anchored on the live figures: the old ones are now marked history) |

What the guard needed, found by the run: the two sides' `RETIRED_EXEMPT_DIRS` clashed
(renamed); the whole-file marker was honoured by one scan only; the pins moved to the
merged plant; the preregistrations, dated prompts and the generated pages of 28–29
September were exempted as records; `drift_test.py` needed an encoding for Arabic text.

**Agreed, NOT in the merge, before any training:** sub-step the thermal network; the
fingerprint covers `data/derived_params.json`; cap the spark trim at 0; ramp every
grade change; a new preregistration; then drive C before drive A (`CLAUDE.md`, the
first box).

---

## Session of 30 September – 6 October 2026 — the results tab, milestone R1a

Jad asked on 30 September for a page with interactive charts, built from Ghassan's
published page and adapting by itself when the results change. It was designed
(`docs/superpowers/specs/2026-09-30-results-tab-design.md`, approved by Jad on
5 October), planned (`docs/superpowers/plans/2026-10-05-results-tab-r1a.md`, applied
from its own text in a scratch clone before execution) and built by subagent-driven
execution: a fresh implementer per task, a review before the next task began, a
whole-branch review at the end. From Task 5 on Jad raised the effort, and each review
became four lenses with three refuters on every serious finding. **Branch
`JMF-2340550-results-tab`, not pushed.** The build record at the end of the spec says
what was built and what the reviews changed; every ruling the controller made on
Jad's behalf, with its cost if wrong, and every deferred minor finding are in
`docs/superpowers/plans/2026-10-05-results-tab-r1a-review-notes.md`.

| what | result |
|---|---|
| the tab | `/results` in the lab (`python -m app.server --simulation`): Phase D, D2 and C4, each rebuilt from `results/<prefix>_seed<N>.txt` on every open, with its plant state, its preregistered verdict quoted with file and line, its required notes, the pairs chart and the hand-written comparison, Arabic first and English |
| not in R1a | Ghassan's set (`results/agents/`), which the page names as coming with R1b; the simulator and car figures (R2) |
| tasks | ten, each reviewed; nine needed a fix commit; the final review six more fixes |
| decisions | 23 rulings, each with its reason and its cost if wrong (the review notes) |
| after updating | a browser that opened the lab before this update may show `nav.results` in the nav until one Ctrl+F5; `/static` now answers `Cache-Control: no-cache`, so later updates need none |

Checks on the final tree (`f5a93cc`), each read off its own run:

| check | result |
|---|---|
| `python -m app.test_results` | 120 tests, OK |
| `python -m app.test_simulation` | 15 tests, OK |
| `python -m app.test_replay` | 49 of 49, READ-ONLY passes |
| `node --test "static/sim/*.test.mjs"` | 236 pass, 0 fail |
| `python -m app.test_agents` | its pre-R1a baseline exactly (the merged plant refuses Jad's agents); no new failing entry |
| `verify_docs.py` | all 73 checks pass |
| `drift_test.py` | 16 of 16 drifts caught |
| browser check (headless Chrome, both languages and themes) | 18 of 18 at Task 10; the fix wave's own checks 16 of 16 |

**Next, in order:** Jad opens the tab and reads it; the branch is pushed when he says
so; R1b (Ghassan's set, his post-hoc reading through `analyse_agent_set.py`, the
incomplete box) is the next milestone, and the review notes are its starting list.

# Part C — the void headline, from CLAUDE.md's "The numbers that matter" (moved 14 October 2026)

The figures this file used to lead with, void since 16 September, and the
ablation identity, verbatim.

<!-- RETIRED-OK: section -->
### VOID — the preview advantage this file used to lead with

**Reactive cuts damage 33.8 %, predictive 47.2 % — a 13.4-point advantage.**
**DO NOT QUOTE ANY OF THAT.** All three figures are void as of 16 September
(AUDIT.md C1/C2/C3) and they are printed here only so the old value is
recognisable if someone is still holding it.

Until 17 September this passage stated them as a plain live claim, with the
retraction three paragraphs further down under a different heading — and a
parenthesis underneath that said the 13.4-point gap was *"unchanged"*, which had
stopped being true. **A reader who stopped at the bold number would have carried
a void figure into a meeting.** Mistake 11 in its most dangerous form: not a
stale number in a corner, but a retracted headline still reading as current.

**What replaces it:** run `check_premise.py`. On the plant of 8 October it prints
a baseline of 848.1 at 883 °C, the constraint binding against the 850 °C
trigger, and preview worth **−0.0 points** against a policy that only knows the
grade it is on now. <!-- RETIRED-OK: 920.1, -0.3 -- the merged plant's -->
On the merged plant (30 September) it read 920.1 and −0.3, and the −0.3 was all
one second of knock at the instantaneous grade step, which the 8 s ramp removed.

*(A parenthesis here used to restate the arithmetic behind an 11 September typo
correction to the first figure. It was deleted on 17 September: `RETIRED` now
guards all three numbers, and re-quoting them to explain a superseded rounding
made the checker fail — correctly. **When a figure goes void, its errata go with
it.**)*

**WHAT USED TO BE CALLED THE STRONGEST SINGLE FACT IN THE PROJECT WAS AN
IDENTITY, NOT A FINDING.** This file said, for weeks, that disabling preview
collapses the predictive policy onto the reactive one *to the decimal* — and
that the identity holding every time made it the load-bearing claim.

<!-- RETIRED-OK -->
It could not have failed. `p_predictive` reads its preview through
`env._preview()`, and with `use_preview=False` that returns zeros, so the
function computes `k_ahead = 0` and returns **the reactive policy's own vector
on every single step**. The two rows were the same rollout. AUDIT.md C3.

An ablation is evidence only when the blinded policy could in principle have
behaved differently and did not. That means a TRAINED blinded agent against a
trained sighted one, which is Phase D.

> **PHASE D HAS NOW BEEN RUN, 21–22 September 2026, and it settles this
> paragraph.** Eight trained blinded agents against eight trained sighted ones,
> paired by seed, preregistered before any of them started. **Preview is not
> significant:** 5 of 8 positive, mean +4.8 damage units, sign test p = 0.3633,
> permutation p = 0.4922. The blinded policies COULD have behaved differently —
> they were trained blind, not zeroed at evaluation — and across eight pairs the
> difference does not separate from seed noise. That is a real ablation and a
> real answer. See `results/PREREGISTRATION.md` and `analyse_phase_d.py`.

The honest comparator —
added 16 September — is a policy that acts on the grade the car is on right now,
with no preview, and it still BEATS the predictive one: by **0.3 points** on the
merged plant (`check_premise.py`), all of it one second of knock at the grade
step.


# Part D — what changed on 8 and 11 September, from CLAUDE.md's phase table (moved 14 October 2026)

**What changed since 11 September.**

<!-- RETIRED-OK: 295.0, 10 -- the manifest before drive B -->
<!-- RETIRED-OK -->
- **The ninth drive.** `pull01` arrived and the dataset reads **ten drives,
  295.0 minutes**. It contributes **zero samples and zero operating points** by
  design — no coolant channel, so the warm filter excludes it. Every calibration
  figure is unchanged. *Read the manifest/sample distinction below before
  quoting a drive count.*
- **`app/` was written, then hardened.** Two defects in it are now mistakes 14
  and 15, and both are old mistakes recurring in new clothes.
- **A release archive tried to drag the tree backwards** — mistake 16.

**What changed since 8 September.** Two more mistakes are logged and the
documents have been swept behind them.

- **Mistake 12** — the load residual cannot see the model it was said to
  validate. `eta_v`, `f_res` and the intake temperature all cancel out of it.
  It still earns three things, listed there, but "the simulator matches the car"
  is not one of them.
- **Mistake 13** — `Intake air temperature before throttle valve` is a
  compressor outlet, not a charge temperature. Correcting it moved the
  operating-point span, both values of k, and the enrichment gate. It did not
  move the premise result or the load residual, and the second of those is the
  point of mistake 12.
- **`verify_docs.py` now opens the documents.** Until 11 September it compared
  the data against constants written inside itself and never read a document at
  all, so it printed green while 55 stale figures were still shipping. See the
  closing note of mistake 11.


# Part E — CLAUDE.md's "What to do next, in order" (moved 14 October 2026)

The live list of 30 September with Ghassan's note of 9 October, its parallel
items, the superseded lists of 22-24 September, the route Phase D took, the
comparisons to improve (28 September) and the app's backlog, verbatim. The six
items of the live list are CLAUDE.md's Training gate, each with its status.

## What to do next, in order

> **THE LIVE LIST — 30 September 2026, after the merge. Agreed by Jad and Ghassan**
> (`conflict.md` section 0 and Ghassan's reply). Before ANY training, in this order:
>
> *Where it stands, 9 October:* steps 1–4 landed on 8 October (`75ca65f`), each
> measured one at a time (`premise_split.py`), with one part of step 1 still
> open: the fit that derives the thermal constants steps at 1 s, not sub-stepped
> (mistake 25); re-fitting is a plant change, so it waits for the next. Step 5: X1's preregistration was
> written and committed before X1 trained, but its test set is decision 12's (the
> locked climb's twenty frozen episodes), not the one step 5 names; whether X1 IS
> step 5 is open, for Jad and Ghassan to answer. Step 6, drive C, is still to do, and X1
> trained before it, on Ghassan's order (PREREGISTRATION_X1.md §0).
>
> 1. **Sub-step the thermal network** (or integrate it implicitly), then re-run
>    `validate.py`, `check_premise.py`, `test_reward.py`, `check_roads.py`,
>    `generality_test.py` and the app pins, and sweep the figures that move.
> 2. **The fingerprint covers `data/derived_params.json`** (and `derived.py`).
> 3. **Cap the spark trim at 0 for the next training**; report every result
>    with and without the knock term until drive C.
> 4. **Ramp every grade change** (the one-step knock spike).
> 5. **A new preregistration**, written before anything trains: D2-style
>    randomised roads plus multi-climb roads as the test set, the blind-arm
>    check, damage reported both ways.
> 6. **Drive C (knock), before drive A** (`logs/DRIVE_PLAN.md`): read-only,
>    six channels, roll-ons in a held gear, the passenger on the phone, its
>    decision rule written before the drive.
>
> In parallel: Ghassan's twenty agents on multi-climb roads, on the plant they
> trained on (`ghassan-before-merge`), once that test is written down; the
> 20-episode spark-capped rescoring of Jad's 48 agents (from
> `sep17-before-merge`); Chapter 4 with both branches' experiments side by
> side, never pooled; the battery (Phase E) for the other three, profiles
> first. The agents page waits for step 1 and the retrain.

> **C4 HAS A RESULT — 24 September 2026. SMALLER THAN THE MEI by the primary
> test, the sensitivity test DISAGREEING, and the agents NOT CONVERGED.**
> D2's design at 300 000 steps, one variable changed (the budget),
> preregistered in `results/PREREGISTRATION_C4.md` (`79568e2`) before any C4
> agent trained.
>
> ```
> python analyse_c4.py        (captured: results/C4_RESULT.txt)
> positive 3 of 8   mean +30.2   median -1.3   sd 139.9
> effect below the MEI (50): sign p = 0.0352 (7 of 8)   permutation p = 0.3867
> cell SMALLER THAN THE MEI     convergence NOT-CONVERGED (2/8, 1/8, pairs 1/8)
> budget-change test (5c): p = 0.6367 -- not shown
> ```
>
> - **The preregistered reading, verbatim:** *"Preview's effect is below the
>   MEI at 300 000 steps: (i) is supported AT THIS BUDGET. The agents were
>   still changing, so (ii) is not ruled out."* Never "preview does not help".
> - **It hangs on one seed.** 7 of 8 is the sign test's exact threshold; the
>   permutation test disagrees because seed 0 carries +360.6 the other way
>   (its blinded agent got WORSE with longer training). Both are reported; the
>   sign test is primary; neither is chosen after the fact.
> - **Every C4 agent retraced its D2 twin bit for bit through 50 000 steps**
>   (80 of 80) — C4 is D2's agents trained longer. No agent refuses torque.
> - **Supervision, separately:** sighted beats `current-grade` on the median in
>   8 of 8 seeds, blinded in 7 of 8 — but on the worst episode 4 of 8 sighted
>   and 5 of 8 blinded agents are worse than `current-grade`'s worst.
> - **Next is the team's decision** — longer budget (the agents were still
>   changing) or more seeds (the result hangs on one seed); one, not both.
>   *(Superseded 30 September: the merge's live list above comes first.)*
>
> The full account: `PREREGISTRATION_C4.md` section 11. The traps that could
> have destroyed Phase D's and D2's agents are closed (`f987049`; `train.py`
> "A RESUME IS NOT A LONGER RUN").

> *(SUPERSEDED 24 September — C4 has run; see the box above and the top of this
> file. Kept as the record of the decision that led to it.)*
>
> **THE LIVE LIST — 23 September 2026, after Phase D2.** Both ablations are in
> and both are INCONCLUSIVE at the C1 budget. Everything in the older list below
> is done (the MEI is set; the document sweep landed in `3f4627d`).
>
> 1. **The next experiment is C4 — DECIDED by Jad, 23 September, for a new
>    session — and it gets its own preregistration before anything trains.**
>    **One variable at a time:** C4 first; more seeds only after C4 and only if
>    it leaves the question open; never both at once, because a change in the
>    result could then not be attributed. The two candidates, as measured:
>    - **C4 — the training budget.** D2's design at 300 000 steps: about six
>      times D2's training, so roughly 16 hours on this machine. It tests
>      explanation (ii) directly. Whether convergence shrinks the spread is a
>      prediction to CHECK, not assume — the last spread prediction was wrong.
>    - **More seeds at C1.** At D2's measured spread, 80 % power against 50
>      units needs about 42 seeds per arm (`power_analysis.py`) — about five
>      times D2's compute. It answers the power question without touching the
>      budget question.
> 2. **Write the ablation chapter — Phase D AND Phase D2.** Both findings kept
>    separate (preview is INCONCLUSIVE; supervision beats `current-grade` on
>    8 of 8 D2 seeds, blind agents included), each with the limits its
>    preregistration declared before the numbers, and the failed spread
>    prediction stated plainly.
>
> Smaller, and recorded rather than urgent: `app/alerts.py`'s `VALID_MAP_HI` is
> 74 kPa in code against the 30–75 kPa span (an app threshold moves only for a
> measurement); the deck tabulates 13 of the 18 mistakes; `run_phase_d.py`
> computes its concurrency cap once, so a transient at launch pins it
> (`PREREGISTRATION_D2.md` §6a).
>
> **DO NOT add seeds to D2** — its section 7, same rule as Phase D.

> *(SUPERSEDED 23 September — the MEI was set at 50 damage units on
> 22 September, and the ledger below was swept to zero in `3f4627d`. Kept as the
> record. The DO NOT at its end still holds.)*
>
> **THIS LIST WAS THE ROUTE TO PHASE D AND PHASE D IS DONE.** Steps 1–5 below
> were followed on 21–22 September and are kept as the record of how, not as
> instructions. **The list that followed it, 22 September:**
>
> 1. **Set the minimum effect of interest.** `results/PREREGISTRATION.md`
>    section 5 says TEAM DECISION — NOT YET SET. It blocks the write-up, not the
>    experiment: until it is set, "preview does not help" cannot be told apart
>    from "the experiment was too small to see it", and that is the first thing
>    an examiner will ask.
> 2. **Sweep the documents — `AUDIT2.md` fix 3, about a day.** `verify_docs.py`
>    prints a KNOWN STALE ledger, ~187 mentions over ~78 rows, each with the
>    file, the figure, the exact count and the finding it belongs to. **That
>    ledger is the work list.** Rewrite from `FULL_RUN.txt`, a transcript of
>    every script run in one pass with its exit code — not from memory. Lower a
>    ledger row in the same commit that sweeps its file; the checker fails if a
>    row shrinks, on purpose. Priority by who reads the file: `presentation/`
>    (116 mentions, and it is what an examiner is shown), then `CLAUDE.md` /
>    `README.md` / `handoff.md` (26, and they state the OPPOSITE of the truth on
>    whether the constraint binds), then `ABSTRACT.md` / `CONTROL_SCOPE.md` (7).
> 3. **Write the Phase D chapter.** Both findings, kept separate, with the
>    limits from `PREREGISTRATION.md` section 8 — declared before the numbers,
>    which is what makes them limits rather than excuses.
>
> **DO NOT add seeds.** `PREREGISTRATION.md` section 7: sixteen runs, then stop.
> Adding seeds now, having seen the result, destroys the preregistration. More
> seeds is a SECOND experiment with its own preregistration, and both get
> reported. Do not switch to a two-sided test because the one-sided one failed.

<!-- RETIRED-OK: section -- the route that was taken, kept as the record -->

**How Phase D was actually run, for the record:**

1. `python check_premise.py` — confirm the environment works at all.
2. `pip install "stable-baselines3[extra]"`, then
   `python train.py --steps 50000 --seed 0`. Expect a poor result; it running is
   the point. **About 45 minutes** — re-measured 17 September by timing 2000 SAC
   steps with gradient updates running: **19.19 steps/s at one thread, 18.14 at
   six.** Checkpoints land every 10 000 steps.

   One thread is marginally faster than six, because the policy network is
   tiny, and the combustion model is the whole cost: each env step runs six
   engine cycles at ~9 ms against ~1 ms for a gradient step. **What sets it is
   `plant.DTHETA_DEG`** — halving the crank-angle step roughly doubles the run.
   Re-time after touching it.
3. `python test_reward.py` before trusting any training curve.
4. Five seeds, one per team member, overnight — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. Phase D: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds. **Once the 20 episodes are
   fixed they never change.** Changing the test set after seeing results is the
   one mistake this project cannot recover from.

**Read this first: the scenario changed on 19 September and it now BINDS.**
Everything below assumes the 130 km/h lock. See the current-state box at the top.

0. **(28 Sep, evening) Review and commit the working tree** — DONE 29 September
   (`cbb8d09`). The order of drive A and the retrain is settled by the live list
   at the top of this section. Drive A must log `Ambient temperature` and
   `Oil temperature`; it is the data `validate.py` rows 8 and 9 still need.

1. **Merge `origin/JMF-2340550-sep17`** — DONE 30 September (`a7ce729`), hunk by
   hunk per `conflict.md`.
2. **Adopt the locked scenario here** — DONE 19 September:
   `make_grade_climb(..., v_kmh=130.0)`. It was decided 18 September before any
   training existed; adopting it is not tuning.
3. **Retrain at 130, on varied roads, at dt = 1.0** — DONE 29 September, ten
   seeds a side (`python train_all.py`, 234 min), scored and documented
   (`python record_agents.py runs/terrain_dt1`). Results in the box at the top.
   What the step said before it ran: `python train.py --steps 50000 --seed 0..4`,
   then the same five with `--no-preview`. Every episode is a new road (`TerrainTrainingEnv`); scoring
   stays on the locked climb. Output goes to `runs/terrain_dt1/`, deliberately
   not `runs/`, where train.py would resume the 110 km/h agents. Run
   `python check_roads.py` first; it must PASS. 13.7 steps/s for one run alone,
   about 1 h for 50 000 steps; ten together took 173 min on 19 September.
4. **The step budget: decided 27 September.** dt = 1.0 makes the episode 900
   steps instead of 4500, so 50 000 steps is **55 episodes, not eleven**, for
   the same compute — and the agent finally trains in the discretisation
   `evaluate.py` scores it in (train.py never passed dt before, so every earlier
   agent learned at 0.2 s and was scored at 1.0 s). If the ablation is still
   inside its noise at 55 episodes, raise the steps; do not change the twenty.
   **29 Sep: it is inside its noise (CI −4.4 to +6.8), and the seeds disagree by
   up to 29 points between pairs.** Before raising the steps, measure how much of
   the agents' gain rests on the knock margin (step 9): if most of it does, more
   steps buy a better exploit of an untested model, not a better answer.
5. **Score with `evaluate.py` and nothing else.** Twenty frozen episodes, median
   and IQR. **The twenty never change.** Changing the test set after seeing a
   result is the one mistake this project cannot recover from.
6. **Report three rows, not two.** Sighted, blinded, AND the current-grade
   policy — a no-preview comparator that reads the gradient the car is on now.
   It has beaten the predictive policy on every hand-written comparison so far.
   If the trained agent cannot beat it either, that is a RESULT about H/τ, not a
   failure.
7. **The octane — SETTLED 29 September: 95 RON**, confirmed by the team; the
   model already runs 95, so nothing is refitted. (What this step said before:
   ask which fuel the car was logged on, and if 98, refit
   `BaselineECU.knock_limited_spark`. REFERENCES.md 2c.)
8. **Report damage two ways until the knock model is tested** — total, and
   turbine plus oil alone. The knock term is 6–12 % of damage and is ALL of the
   hand-written −0.4 (28 September). This is an extra column in the reporting,
   not a change to the reward, the training or the twenty episodes.

9. **(29 Sep) Measure the knock margin — DONE the same day** (`knock_margin.py`):
   with spark advance forbidden the agents' median cut falls to 41.6 / 41.7 %,
   below current-grade's 43.4 %, and the median margin over it goes +24.4 ->
   −1.8 points. So **drive C (logs/DRIVE_PLAN.md) is now the most valuable
   drive**: it decides whether the knock margin the agents use is real. If the
   car knocks earlier than the model says, the reward's knock term has to move
   before the next retrain; if it does not, the agents' margin stands.
10. **(29 Sep) Where the agent records live — DECIDED by the team:** git keeps
   the summaries, configs, curves, policy weights, READMEs and figures (about
   11 MB); the per-step `train_record.npz` / `eval_record.npz` (85 MB) stay on
   the training machine and are gitignored. `eval_summary.json` carries what the
   page and the READMEs read from the records, so both build from git alone.

Do not start Phase E or F until D produces a table. **It has one now (29 Sep).**

### Improving the comparisons that do not agree — 28 September

Each row says what it would take, and whether it touches the plant. **A plant
change after the retrain means retraining.** The order is decided (the live
list at the top of this section): drive C before drive A, and no training before
the five agreed steps.

| comparison | status | what would improve it | touches the plant? |
|---|---|---|---|
| Knock | untested | Drive C: 6 channels, both ignition angles every ~1.25 s, held gear. Then re-run the comparison; if a relationship appears, retune Douaud-Eyzat to the car's retard onset | only if retuned |
| Oil on hard pulls | limited (28 Sep) | DONE in part: the oil node re-structured and derived (mistake 20) — no more spikes, peak 102.6 °C against the car's 107. Still open: row 8 and row 9 (`validate.py`), which need drive A logged with oil AND ambient | yes |
| Oil and coolant, long drive | agrees on drive10 (28 Sep) | DONE: median −1.6 K oil, −0.6 K coolant on drive10; row 11 passes even with drive10 held out. Still open: the heat-management valve's control law (82–84 °C after load on hot afternoons), which a fixed setpoint cannot follow — drive A | yes |
| Compressor ceiling | limited | DONE in part with drive B (28 Sep): the ceiling IS the measured envelope now, within −7 to +7 % of drive B's highest boost per 200 rpm from 2000 rpm up, but 9–20 % LOW at 1600–2000 rpm (corrected 29 Sep; it said "matches at 1400–2400"). Admitting drive B's transient roll-on readings into the envelope would raise it there — a plant change, so decide with the retrain. The kickdown workaround stays (no torque channel; roll-ons are spool-limited). Above 0.314 kg/s the MAF saturates | yes (derived) |
| Load | limited | Nothing at part load: both pressure channels on this car are pre-throttle, so no part-load test of `eta_v` exists. At wide-open throttle the boost comparison IS an `eta_v` test (+1.9 %); drive B extends it down in rpm. Say so in Chapter 3 | no |
| Enrichment | limited | DONE for the dwell (28 Sep): `ENR_DWELL_LO/HI` derived on timestamps; worst cell now 0.033 lean at 3500–4500 rpm, long dwell. The speed band and depth need more independent readings at 3500–7000 rpm and sustained full load — a track-day job. Irrelevant to Phase D: the climb never enriches | derived, yes |
| Operating region | not covered | Drive A gives sustained load at road speeds; the exact 130 km/h / 12 % point does not exist on any road and is sea-level air by construction | no |
| Validation table | limited | 8 of 11 (28 Sep, evening). Both car-row misses are the oil node: row 8 (97.0 °C against 103–111) and row 9 (60 s against 70–100), after the oil node was re-structured and derived. Drive A, logged WITH ambient and oil, is the data. The literature miss, EGT cruise max, needs a source — library access, REFERENCES.md section 3 | via the oil node |

**Where the app fits in that order: behind the live list.** It is finished
enough to demo; the agents page waits for step 1 and the retrain (the live
list). If you have an hour, spend it on the live list, not on `app/`. The app's
own next steps are kept separately below so they cannot be mistaken for the
critical path.

### The app's backlog — behind the live list

Listed because the work is understood, not because it is scheduled. Each item
says what it would buy, so that none of them gets started because it is
interesting.

1. **Confirm it against the car.** Everything so far is replay. One drive with
   `--live` and the six-channel set, checked for: does the adapter sustain
   ~1.4 s per channel as mistake 13b predicts, do any channels retire, does the
   warm-start band settle in the time the model says. **This is the only item
   that can find something replay cannot**, and it needs a driver and an hour.
2. **A mismatch case with a known fault.** The detector has never seen a real
   boost leak. Nothing in ten drives is faulty, so every number in mistake 14
   is a FALSE-POSITIVE rate and none of them is a detection rate. Inducing a
   leak safely is not obviously possible on a borrowed car; if it is not, say so
   in the thesis rather than implying the detector is validated.
3. **Wire the trained agent in, live.** Half of it exists: the agent replay
   (`python -m app.server --simulation`, `app/agent_api.py`) shows trained
   agents on finished simulated episodes, with no vehicle connection. What does
   not exist is the live half — what the agent WOULD command, beside what the
   baseline ECU commands, while the car is driven. That is the honest bridge
   between the two halves of this project, and it is read-only in exactly the
   same way — a suggestion on a screen, never a write.
4. **Oil as a measured node.** `Oil temperature` is an optional channel the car
   does publish. Adding it makes the oil node measured rather than estimated,
   at the cost of ~14 % of every other channel's rate. Worth it only if the oil
   alert turns out to matter.

**Never, in any version:** a write path to the vehicle, or raw samples on disk.
Both are asserted by `app/test_replay.py`, so breaking either fails a check.

---


# Part F — the full text of sections condensed in CLAUDE.md (moved 14 October 2026)

CLAUDE.md keeps a short version with the same meaning; this is the original
title and the original "ask who you are talking to", verbatim.

# CLAUDE.md — read this first

Project context for Claude Code. If you are an AI assistant opening this repo,
this file is the handoff: it tells you what the project claims, what has been
measured so far, and which mistakes have already been made so you do not repeat
them.

If you are a human, read it too. It is shorter than the handbook.

---

## Before anything else: ask who you are talking to

**Jad's rule, 28 September 2026: the first thing you do in every session is ask
who you are talking to** — before reading further, before answering, before
explaining anything. One short line, Arabic first:

```
مين معي؟
Who am I talking to?
```

If they already said who they are in their first message, that is the answer;
do not ask again. Then open the file in `team/` whose `name:` matches — a first
name or the student number is enough — and follow it for the whole session. It
says what to assume that person knows, what not to assume, which language, and
how they take an explanation in.

- **Their file is still a stub** (it says STUB at the top): say so in one line,
  and ask whether they want to fill it in now — the template's questions, one
  per message. Never fill a section from a guess. Until it is filled, say that
  you are working without a profile.
- **No file matches:** carry on without a profile, say so, and point at
  `team/_TEMPLATE.md`.
- **You are a subagent:** skip this. You are not talking to a person, and the
  session that launched you already asked.

**Why ask, and not read `git config user.email`.** Until 28 September this
section said to match `git config user.email` against each file's `email:`
line. It failed, and `AUDIT2.md` Part 6 recorded how: Jad commits under two
addresses and his file lists one, and Ghassan's file had no address at all, so
two of the three identities in the history matched nothing. And an address
names whoever set up that clone, not whoever is at the keyboard: anyone working
on a teammate's machine would get the teammate's profile. Asking avoids both.

Five people share this repository and they do not share a background.
**This is not a courtesy.** One of the five is comfortable with engines and lost
in reinforcement learning; another is the reverse. An explanation pitched at the
wrong person is a wasted message in both directions, and the profiles exist
because guessing has already gone wrong. `team/README.md` says how to add
yourself; `team/_TEMPLATE.md` is the starting point.

---


# Part G — handoff.md as it stood on 14 October 2026 (moved verbatim)

The short entry point the project used until the restructure: what to run and
what each script printed, the path to a passing project, what not to do, and
the one thing to carry into the viva. handoff.md now only points.

# handoff.md — pick this up and keep going

**What this file is for.** This is the entry point, and only that: what to run
first, what to do next, what not to touch. It is deliberately the shortest of the
three. `CLAUDE.md` is the permanent handoff and the mistake log — the rules, the
traps, and every mistake already made; read it before you change
anything. `CHECKPOINT.md` is a dated snapshot of what was verified and when, and
it is meant to go out of date. This file holds no history and makes no argument,
so it should never become a third source of truth. **Where any of the three
disagree, the scripts win: run the command and read what it prints.**

`REFERENCES.md` sits beside those three and answers a different question: where
every number we did **not** measure comes from. Read it before calling any band
in `validate.py` "published": four of the seven literature bands still have no
source, and rows 8–11 are not published bands at all — they come from our car.

You are taking over a project that works. Everything in the repository
regenerates, and `verify_docs.py` re-checks the published figures against the
shipped data every time it runs. What was missing was Phase D, and it has now
run.

> **Where the project stands, 30 September 2026: the two branches are merged.**
> Ghassan's physics, Jad's method — the first box of `CLAUDE.md`, and `conflict.md`.
>
> Four trained ablations, none decisive: Phase D and D2 INCONCLUSIVE; C4 smaller
> than the minimum effect of interest by the sign test only, the agents not
> converged; Ghassan's ten-pair retrain INCONCLUSIVE under the same rule. Write
> *preview does not separate from seed noise at these budgets*, never *preview
> does not help*. **Separately**, trained agents beat `current-grade` on the
> median in every set — but that margin rests on spark advance that only the
> untested knock model allows; with advance forbidden it disappears.
>
> **Before any new training**, do the five agreed steps in `CLAUDE.md`'s first
> box: sub-step the thermal network, extend the fingerprint to
> `data/derived_params.json`, cap the spark trim, ramp the grade changes, and
> write the new preregistration. Then drive C.
>
> `python analyse_phase_d.py`, `analyse_phase_d2.py` and `analyse_c4.py` print the
> sep17 results from the committed files (their agents re-run only from the tag
> `sep17-before-merge`); `results/agents/terrain_dt1/README.md` holds Ghassan's.

**There is now a second deliverable, `app/`, and it is NOT the missing piece.**
It runs this same physics beside the car in real time and estimates turbine
temperature, which the vehicle has no sensor for. It works, it is tested, and it
is the first thing anyone will ask to see. It does not test the claim; Phase D
and D2 do. If you have an hour, spend it on those, not on the app.

**Where the numbers stand today.** 321.7 minutes over eleven drives, eight
carrying samples, **26 distinct operating points spanning 30–75 kPa**. The load
residual is **1.4 % with the DIN constant derived** (k = 0.831, zero free
parameters) and **1.1 % with it fitted** (k = 0.839, one). Note the direction:
dropping the fitted parameter makes the residual **rise**, 1.1 → 1.4 %. Say that
out loud rather than quoting only the derived figure — and read mistake 12 in
`CLAUDE.md` before quoting either, because the residual cancels the breathing
model and therefore cannot validate it.

---

> ## 29 September 2026 — THE RETRAIN RAN
>
> Twenty agents, seeds 0–9 sighted and blinded, 130 km/h on varied roads, on the
> derived plant. **All twenty beat every hand-written policy; sighted minus
> blinded is +1.2 points (95 % CI −4.4 to +6.8, n = 10) — INCONCLUSIVE under the
> MEI rule (sign-test power 0.26).** Every agent advances spark to the +4° action
> bound, which sits just under the untested knock model's knee, and with that
> advance forbidden (`knock_margin.py`) their median cut
> falls to ~41.6 %, below current-grade's 43.4 %: **most of their margin rests on
> the knock model, so drive C (knock) is now the most valuable drive.** Blinded
> seed 6 does more damage than the baseline on the five episodes that weight
> component life least. The fuel is settled (95 RON). Every action is recorded
> (`results/agents/`; the per-step records stay on the training machine,
> gitignored); `results/agents/terrain_dt1/README.md` has every table.
> `SESSION_REPORT_2026-09-29.md` is the full account. Committed 29 September.

<!-- RETIRED-OK: section 829.2, 548.6, 437.6 -->

```bash
python verify_docs.py      # every check must pass before you quote anything
python test_reward.py      # 8 of 8, four of them on the training roads
python check_roads.py      # PASS: the baseline can drive every training road
python check_premise.py    # the hand-written policies on the locked climb
```

A few minutes — five full rollouts. It prints the protection trigger, then one
row per policy, then a warning you must read.

**THE FOUR NUMBERS THIS FILE USED TO TELL YOU TO EXPECT ARE VOID.** They were
829.2 / 548.6 / 437.6 / 548.6, and the 15 September audit found three reasons
not to trust them — the baseline had its cooling switched off, the baseline ECU
was scheduled on a load the engine was not at, and the reactive comparator
protected less hard rather than merely later. See the box in
[README.md](README.md), and `AUDIT.md` findings C1, C2 and C3.

What it prints on the plant of 8 October (the locked scenario, 12 % at
130 km/h in 42 °C air, the climb ramped over 8 s, on the ZF 8HP51 gearbox; the
physics derived from the logs; the thermal network sub-stepped):

```
protection trigger: 1123 K (850 C) = the knee of the turbine damage term

policy                             fuel g    damage  peak turb C  peak oil C
----------------------------------------------------------------------------
baseline ECU (true neutral)          4544     848.1          883          94
reactive protection                  4683     559.7          860          94
current-grade protection             4810     449.6          853          94
predictive protection                4815     449.7          853          94
predictive, preview disabled         4683     559.7          860          94
----------------------------------------------------------------------------
  reactive protection            cuts damage  34.0 %
  current-grade protection       cuts damage  47.0 %
  predictive protection          cuts damage  47.0 %

  preview over reactive      +13.0 points
  preview over current grade  -0.0 points   <- THE HONEST ONE
```

**Read the warning underneath it.** The baseline peaks at 883 °C against the
850 °C trigger, so **the constraint binds**, and every protecting policy acts.
"Predictive, preview disabled" equals "reactive" **by construction**, not as a
finding (`AUDIT.md` C3). These are hand-written policies. Preview and
current-grade tie: the 8 s ramp of 8 October removed the one second of knock at
the grade step that was all of the merged plant's deficit.

<!-- RETIRED-OK: 920.1, 625.7, 520.5, 523.5, 4573, 32.0, 43.4, 43.1, 11.1, -0.3 -- the merged plant of 30 September -->
*(On the merged plant, 30 September to 8 October, it printed baseline 920.1 at
883 °C, reactive 625.7, current-grade 520.5 and predictive 523.5 (cuts 32.0,
43.4, 43.1 %), and preview −0.3 against current-grade: that knock spike. The
ramp is 70 of the 72 units the baseline moved; the sub-stepping 2.5.)*

<!-- RETIRED-OK: 959.8, 884, 679.0, 633.2, 637.4, 29.3, 34.0, 33.6, 4.3 -->
*(On `JMF-2340550-sep17`'s plant, before the merge, the same script printed
baseline 959.8 at 884 °C, current-grade cutting 34.0 % and preview −0.4 against
it. The equal peak is two of the merged plant's corrections cancelling: +5.5 K
from the exhaust flow, −6.2 K from the air density.)*

The row worth looking at is **current-grade protection**: no preview at all,
only the gradient the car is on right now, and hand-written preview **gains
nothing over it** (−0.0 points).

<!-- RETIRED-OK: 256.5, 801, 294.2, 812, 2.2, 1.8, 110 -->
*(This block held 256.5 / 801 °C / 2.2 points until 17 September — the figures
from before the H1 crank-angle correction took `plant.DTHETA_DEG` to 0.25°;
`AUDIT_FIXES.md` H1 records the move. It then held baseline 294.2 at 812 °C
until 22 September — the six-speed run at 110 km/h, from before the scenario
moved to 12 % at 130 km/h — in which the constraint did not bind and
current-grade beat predictive by 1.8 points. Both times the code moved and
this file did not.)*

**How the scenario compares with the car's own driving, measured over every
drive** — on 17–19 September, with the app's physics of that day (exhaust
= fuel × 15). On today's physics `7475b5d7` peaks at 872.7 °C (the pinned
figure in `app/test_replay.py`; 873.1 °C on the merged plant before the thermal
network was sub-stepped on 8 October) <!-- RETIRED-OK: 873.1 -- the merged plant's pin -->;
the other rows were not re-measured. Replay them through `app/` and read the peak estimated turbine housing
— a MODEL OUTPUT, not a reading — against the 850 °C trigger:

```
7475b5d7   55.1 min   890.6 C   +40.8   36 s above
670063b2    7.3 min   780.3 C   -69.5    0
cb67b01f   21.6 min   728.0 C  -121.9    0
3aca2ec1   41.7 min   676.1 C  -173.7    0
683640a0   24.0 min   664.1 C  -185.7    0
pull01      7.4 min   608.0 C  -241.8    0
fb988991   14.7 min   607.9 C  -242.0    0
3f64372e    0.7 min   340.1 C  -509.8    0
f51686d7        -- no estimate
drive10   119.4 min   797.6 C   -52.4    0      <- TAIF, a real mountain climb
                                        ----
total     292.0 min                      36 s  =  0.206 %
```

<!-- RETIRED-OK: 812, 38, 78 -->
**One drive of ten reaches the limit, for 36 seconds in 292.0 minutes.** When
this was first measured, on 17 September, the synthetic climb peaked at 812 °C
and missed by 38 K, so the car's own driving was 78 K hotter than the scenario
written to stress it — and the conclusion was that the scenario was wrong, not
the trigger. The scenario was re-chosen and the trigger did not move: the
locked climb now peaks at 884 °C and binds.

**And the mountain drive does NOT bind, which is the 19 September addition.**
`drive10` is Jeddah to Taif and back — two hours, ambient falling 31.5 to
20.5 °C and recovering, driver reaching 167 km/h. It peaks at **797.6 °C with
zero seconds above the trigger**. The hottest moment is a brief acceleration at
137 km/h and 5792 rpm, not the climb and not the top speed: the housing's ~50 s
time constant ignores bursts, and the 160 km/h stretch lasted five seconds.
**Road power, not altitude** — the locked scenario holds 88.7 kW for twelve
minutes, the Taif climb asks about half that.

Reproduce it: replay each log through `app.estimator.Estimator` and count
samples with `t_turb_c` above `engine_env.TURB_PROTECT_K - 273.15`.

> The old "548.6 against 548.6" identity was never evidence. With
> `use_preview=False` the preview term is literally zero, so the predictive
> policy returns the reactive policy's vector on every step — the identity
> could not have failed. The real ablation needs a TRAINED blinded agent, and
> that is Phase D — which has now run as four trained ablations, none of them
> decisive (the box at the top of this file).

---

## What each script should print today

Run any of these before quoting anything out of it. If a number here does not
reproduce, the number here is stale and the script is right.

| command | what it prints today |
|---|---|
| `python analyse_phase_d.py` | Phase D, on sep17's plant: 5 of 8 seeds positive, mean +4.8, sign p 0.3633, permutation p 0.4922 — NOT SIGNIFICANT. The agent's margin over `current-grade` is a DIFFERENT claim, and it rests on spark advance |
| `python analyse_phase_d2.py` / `python analyse_c4.py` | D2 INCONCLUSIVE (4 of 8, sign p 0.6367); C4 SMALLER THAN THE MEI by the sign test only (p 0.0352), permutation disagreeing, not converged. From the committed result files |
| `python check_premise.py` | baseline **848.1** at **883 °C**; reactive 559.7 (cuts 34.0 %), current-grade 449.6 (47.0 %), predictive 449.7 (47.0 %); preview over current-grade **−0.0**. Writes `results/premise.json`. Hand-written — read AUDIT.md C1 and C3 first |
| `python test_reward.py` | **12 of 12** pass. Neutral scores inside ±0.05 on the locked climb, on every training-road family, on the extremes roads of X1 and at X2's two thin-air corners (0 °C and 45 °C, both at 80 kPa); refusing torque is punished on all three kinds of road; the gearbox's torque table still matches the plant. A random policy scores just below neutral (informational) |
| `python check_roads.py --road extremes` | **PASS** over 40 of X1's training roads; 10 push the baseline past 850 °C; worst neutral reward −0.0043, worst p95 tracking error 0.018 |
| `python check_roads.py --road wideair` | **PASS** over 40 of X2's training roads (0–45 °C, 80–101.3 kPa); only 2 push the baseline past 850 °C; worst neutral reward −0.0054, worst p95 tracking error 0.013 |
| `python test_wide_air.py` | **16 tests OK** (about 6 min): X2's roads reduce to the plant at sea level, leave every other environment alone, and follow the air |
| `python analyse_x2.py` | X2's preregistered test (`results/PREREGISTRATION_X2.md`): **INCONCLUSIVE**, 1 of 5 pairs positive, mean −4.40, sd 20.51 (143 seeds for 80 % power against the MEI); the same thermal-only. `python check_x2_convergence.py`: **NOT-CONVERGED**, 0 of 5 pairs settled. 7 of 10 agents beat current-grade; 0 of 10 pass the logged-drive check |
| `python analyse_x1.py` | X1's preregistered test (`results/PREREGISTRATION_X1.md`): **SMALLER THAN THE MEI**, 17 of 23 pairs below 5.43 points (sign p 0.0173, permutation p 0.0027), the same without the knock term; 39 of 46 agents beat current-grade. Writes `results/X1_RESULT.txt` and `.json`; `--set terrain_dt1` is its dry run on the twenty of 29 September |
| `python logged_check.py --set runs/extremes_dt1` | X1's check on the car's own drives, replayed flat (six drives, two weightings): **1 of 46** agents pass. The torque is delivered; the fuel is not — with life weighted most, 252 of 276 runs burn more than 1 % over the baseline ECU. About 4 h; writes `results/logged_check_extremes_dt1.json` |
| `python conditions_test.py --set runs/extremes_dt1 --report-only` | X1's transfer battery, descriptive (five episodes a condition): held out, **30 of 46** beat that condition's current-grade at 25 °C on a 21.75 % hill and **26 of 46** at 50 °C; in range, 29 (42 °C) and 42 (35 °C). Re-scoring all seven conditions (`--resume-all`) takes about 3.5 h |
| `python check_roads.py` | **PASS** over 40 roads; 14 push the baseline past 850 °C; worst neutral reward about −0.002, worst p95 tracking error 0.016 against a 0.05 band. The terrain roads of the 29 September agents, as checked on 28 September on the plant they trained on; `results/training_roads.json` is kept as that record (the page draws it), so it was not re-run on X1's plant — X1's own roads are the `--road extremes` row |
| `python validate.py` | **8 of 11** inside their band — 6 of 7 against literature, **2 of 4 against our own car** (rows 8–11, oil and coolant); displacement 2997.5 cc; turbine τ **48.0 s** |
| `python compare_log.py data/master_points.csv` | fitted k 0.839 → **1.1 %**; derived k 0.831 → **1.4 %**, PASS. Mistake 12: it cannot see the breathing model |
| `python derive_params.py` | re-derives every constant the logs set into `data/derived_params.json`, in about a minute; `build_dataset.py` runs it |
| `python calibrate_thermal.py` | the thermal fit with leave-one-drive-out scores, `results/thermal_calibration.json` (~3 min) |
| `python run_results.py` | regenerates `results/traces_130kmh.json`, `sweep_speed_grade.json` and the Phase D files (~15 min) |
| `python compare_calibration.py` | the 28 Sep before/after comparisons, `results/calibration_comparison.json`, for figures 20–25 |
| `python check_map.py` | spark falls with load in every row and rises with speed in every column; **6 cells above the compressor ceiling**, 0 with no knock-free spark |
| `python build_dataset.py "logs/raw/*.csv"` | 321.7 min, 11 drives, 26 operating points — then it runs `derive_params.py` |
| `python model_vs_data.py` | eleven comparisons of the simulator against the car, each beside the figure the documents quote; ~10 min |
| `python verify_docs.py` | recomputes the published figures and scans every tracked document. **Do not memorise its count** — it moves each time a figure is added |
| `python -m app.test_replay` | **49 of 49**. Add `--full` for **59 of 59**: 14278 of 14340 samples estimated, peak estimated turbine **872.7 °C**, **14 thermal · 0 mismatch · 19 novel**. Both drives' pins moved on 28 Sep (exhaust = air + fuel; the derived enrichment dwell) and again on 8 Oct (the thermal sub-stepping, 0.4–0.6 K); the change behind each is written beside it |
| `python make_figures.py` / `python make_page.py` | the thesis figures in `results/figures/`, and the phone page `results/page/index.html` |

`validate.py` being 8 of 11 is expected, not a failure. Against literature the one miss
is the cruise-band EGT maximum. Against the car, rows 10 and 11 (coolant) pass since the
thermal network was derived from the logs; rows 8 and 9 (oil) still miss — the model's oil
runs cool of the car's over drive10's sustained high-rpm stretch (97.0 °C against
103–111) and its time constant is 60 s against the car's 70–100. Drive A is the data.
`validation_table.md` section A says how each band is built, section C what the
derivation changed.

---

## The path to a passing project

**Phase D is the bar**: validated simulator + agent beating two baselines + an
ablation isolating preview. It has run four times (the box at the top of this
file): none separated preview from seed noise, and the agents' margin over
`current-grade` rests on the untested knock model until drive C.

How the runs were made is recorded in `CLAUDE.md` ("How Phase D was actually
run") and, for the twenty agents of 29 September, in
`SESSION_REPORT_2026-09-29.md`. What still binds the next training run — after
the five agreed steps in `CLAUDE.md`'s first box and a new preregistration:

1. **Check the gates first:** `python test_reward.py` (8 of 8) and
   `python check_roads.py` (PASS). A training curve computed against a broken
   reward is worse than no curve, because it looks like progress — the reward
   has carried a live hack twice (mistake 5), and the training roads found a
   gearbox defect that no single-road check could have (27 September).
2. **Ask the owner before starting.** `python train_all.py` occupies the machine
   for about four hours (twenty runs took 234 min on 29 September).
3. **Move the previous `runs/terrain_dt1/` aside first.** `train.py` resumes any
   checkpoint it finds there, at the same `--steps` only; a different `--steps`
   is refused (`train.py`, "A RESUME IS NOT A LONGER RUN").
4. **The training curve cannot show learning** — returns vary with the road and
   the preference weights. Score it: `python record_agents.py runs/terrain_dt1`
   runs `evaluate.py`'s twenty frozen episodes, median and IQR, paired by seed.
   Report three rows — sighted, blinded and `current-grade` — and damage two
   ways, total and turbine plus oil, until the knock model is tested.

> **The twenty episodes never change.** Changing the test set after seeing
> results is the one mistake this project cannot recover from. **Do not add
> seeds to Phase D or D2:** more seeds, having seen the result, is a second
> experiment with its own preregistration (`results/PREREGISTRATION.md`
> section 7).

---

## What you must not do

| Never | Why |
|---|---|
| **Write to the vehicle's ECU** | Read-only OBD-II logging only. If a task seems to require it, it is the wrong task — say so rather than finding a way |
| Edit `data/` or `validation_table.md` by hand | Regenerate them |
| Edit `logs/raw/` | Those are measurements |
| Quote a number no script prints | Run `verify_docs.py` first |
| Change the locked scenario or the twenty episodes | `make_grade_climb` and `evaluate.EPISODES`. Training roads may vary; scoring may not |
| Point `train.py` at `runs/` | It resumes any checkpoint there — the 110 km/h agents |
| Feed `map_raw` into the model | It is a pre-throttle sensor. Use `plant.map_from_airflow()` |
| Feed the raw intake-air-temperature channel in as charge temperature | `Intake air temperature before throttle valve` is a **compressor outlet**. Use `plant.charge_temperature()` |
| Rely on a default plant geometry | Pass `geo=GEO` explicitly. This cost three weeks once |
| Call a validation band "published" without checking `REFERENCES.md` | Most have no source |
| Cite the 88 °C thermostat to BMW | The B58 has a heat-management valve; 88 °C is our own stand-in, identified from the logs |
| Quote the knock model as calibrated — or as refuted | The only test so far could not see knock (28 September) |
| Describe the scenario as a mountain | It is sustained load in sea-level air; altitude is not modelled |
| **Add a write path to `app/`, in any form** | The read-only rule is structural, not stylistic. A future version may SUGGEST an ECU parameter as text on a screen; applying it is a different product and must never share a code path. `app/test_replay.py` asserts that no write path exists |
| **Write raw samples to disk from `app/`** | The stream is memory → websocket → gone. Only what the model *marks* is persisted, to `app/review_log.jsonl`. A test asserts a whole replay creates exactly one file |
| Add a seventh live channel without justifying it | The adapter polls one channel per round trip, so every addition costs every other channel ~14 % of its rate. Put the reason in the channel's `why` field |
| Lower an `app/` threshold to quiet a demo | A threshold changes for a measurement, and the measurement goes in the docstring. See mistake 14 |
| **Unzip a release archive over the tree** | The v19 archive was older than the branch for everything except `app/` and would have reverted a fortnight of work. Diff first, take only what is new. Mistake 16 |

On that charge-temperature row, the car settles it. Over 762 boosted model
samples against 1097 logged readings of the vehicle's own boost channel (the
counts `verify_docs.py` asserts on the current dataset), the shipped
`charge_temperature()` sits **+1.9 %** from the car; the raw sensor, when it
was used, put the inversion **+23.7 %** high. An `ambient + 8 K` knob scored
+0.7 % when the correction was made on 10 September, on the smaller dataset of
the time, and was rejected for being tuned to the target.

One constant to watch while reading older prose: **`ENR_LOAD` is 180 kPa, not
200.** The enrichment gate is written in manifold pressure and manifold pressure
changed definition when the charge temperature was corrected; 180 on the current
scale selects exactly the samples that 200 selected on the old one, and
every enrichment figure reproduces without a refit.

---

## Habits that keep this project defensible

1. **Change one thing, re-run, write down what happened.** Two changes at once
   and you no longer know which one did it.
2. **After changing `plant.py` or `thermal.py`** — re-run `validate.py` and update
   `validation_table.md` **in the same commit**.
3. **After changing the reward, the env, the plant, the gearbox or the roads** —
   re-run `test_reward.py` and `check_roads.py`, and paste the output into the
   commit message.
4. **Report numbers with their condition attached.** "1.4 % load residual over
   26 points, 30–75 kPa" — not "the model is accurate."
5. **Report the protection threshold with every preview figure.**
6. **Before calling a residual a validation, perturb the thing it supposedly
   validates and check the number moves** (mistake 12).
7. **Count readings, not rows.** The logger polls one channel per row; a row
   count can be 25 times the measurement count (AUDIT.md H4). The knock test
   failed exactly this way.
8. **Never promote a citation from memory.** Open the source and write down the
   page. `REFERENCES.md` is where that record lives.
9. **When a figure changes, grep the tree for the OLD value yourself and read
   every hit** — including inside sections marked `RETIRED-OK`, which the
   checker skips.

---

## When a new drive CSV arrives

The drives worth making are in `logs/DRIVE_PLAN.md` — A (climb), B (roll-ons),
C (knock) — each with its channel set and how to drive it.

```bash
cp <new>.csv logs/raw/<descriptive-name>.csv
python new_drive.py logs/raw/<descriptive-name>.csv   # what did it buy?
python build_dataset.py "logs/raw/*.csv"              # rebuilds all three data files
python compare_log.py data/master_points.csv          # re-scores the load
python model_vs_data.py                               # re-scores everything else
```

Then check: did anything get filtered out (a drive without `Coolant temperature`
contributes nothing); did the operating-point count rise; did any window fail
for span or a logger gap; does the load residual stay near 1.4 %. If the drive
changes a calibration, check how many **independent readings** support it and
that the variable you fitted against actually correlates. For lambda that is
engine speed (−0.47), air mass (−0.41) and dwell (−0.44); manifold pressure
carries no detectable signal (+0.11).

> **Census once with everything, then record the small set for real drives.**
> Fewer channels, faster refresh: 7 channels read each every 1.45 s, 26 every
> 7.5 s.

---

## The open problem, if you want the harder work

**Phase F's H2b threshold rule does not survive the correct engine.** It sets the
constraint at the 80th percentile of the unprotected trace, which assumes the
temperature spends a minority of the episode near its peak. The standard scenario
is a sustained climb — nine of twelve minutes at the top — so p80 lands on the
peak and the top three rows saturate at 100 % for both policies.

`check_premise.py` hit the same wall and solved it by anchoring to the **damage
model** instead — 1123 K, the knee of `exp((t_turb − 1123)/45)`. That is a
statement about the component rather than about one episode, and it transfers
between scenarios. `generality_test.py` now imports the same constant,
`engine_env.TURB_PROTECT_K`, so the two experiments cannot report different
protection limits.

**Replacing H2b's percentile rule with something that transfers is real,
publishable work.** Until then there is no usable H/τ table: the fixed-limit
H2 table is void too (`AUDIT.md` C1 and M12). Re-run `generality_test.py`,
read what it prints, and quote the threshold with every figure taken from it.
And do not use H/τ to rescue Phase D's null: that reading was drafted and
refuted (`results/PREREGISTRATION.md` limit 8).

---

## Where everything is

| You need | File |
|---|---|
| the rules, the traps, the mistakes already made, the improvement plan | [CLAUDE.md](CLAUDE.md) |
| **the four preview ablations**, and the rules they were run under | `python analyse_phase_d.py`, `analyse_phase_d2.py`, `analyse_c4.py`, [results/agents/terrain_dt1/README.md](results/agents/terrain_dt1/README.md) and [results/PREREGISTRATION.md](results/PREREGISTRATION.md) |
| what was verified, and on what date | [CHECKPOINT.md](CHECKPOINT.md) |
| the last session in full | the newest `SESSION_REPORT_*.md` — [SESSION_REPORT_2026-09-30_merge.md](SESSION_REPORT_2026-09-30_merge.md) on 30 September |
| the prompt to continue in a new session | the newest `NEXT_SESSION_*.md`; read its first lines for SUPERSEDED before pasting it |
| **where every number we did not measure comes from** | [REFERENCES.md](REFERENCES.md) |
| the drives still worth making, and how | [logs/DRIVE_PLAN.md](logs/DRIVE_PLAN.md) |
| results, figures, and the phone page | [results/](results/) — `results/page/index.html` |
| the project in prose, for a reader outside the team | [README.md](README.md) |
| Chapter 3's evidence | [validation_table.md](validation_table.md) |
| which team PDFs still carry void numbers | [DOCUMENT_STATUS.md](DOCUMENT_STATUS.md) |
| what the car can and cannot measure, all 656 channels | [logs/CHANNEL_CENSUS.md](logs/CHANNEL_CENSUS.md) |
| the live app, and why it estimates what it estimates | [app/estimator.py](app/estimator.py) — read its docstring first |

---

## The one thing to carry into the viva

**We built an ablation that could fail and ran it four times; it has not
separated.** Phase D and D2 are INCONCLUSIVE, C4 is smaller than the minimum
effect by the sign test only, and Ghassan's retrain is INCONCLUSIVE: preview does
not separate from seed noise at these budgets. Separately, and never as evidence
for preview, the trained agents beat `current-grade` — by a margin that rests on
spark advance the untested knock model allows. Carry the limits with both.

**The claim is a criterion, not a controller:** preview is worth acquiring only
where the horizon H and the protected part's time constant τ are comparable.

<!-- RETIRED-OK: section 13.4 -- the superseded viva claim, kept so it is recognisable -->
**The evidence for it is a TRAINED ablation, and nothing else.** A sighted agent
and a blinded one, trained identically, scored on twenty frozen episodes, paired
by seed, beside a comparator that reads only the grade the car is on now.

*What this section used to say, kept so it is recognisable:* the size of the
preview effect has changed four times, across two engines, two scenarios and
two protection triggers — 30 points on a guessed baseline, 4 after that
baseline was recalibrated against real data, 13.4 on the corrected engine at
the 1123 K limit. The first two were real measurements of different systems.
*(The 13.4 is void — `AUDIT.md` C1: it was measured against a baseline with
its cooling switched off; and the identity it leaned on could not fail, C3.)*

**The number is not the result. The ablation is.** The section used to close
with this sentence, which is the refuted claim:

> *"Preview-disabled has landed on reactive to the decimal, every single time.
> Whatever the gap is, it is attributable to preview information and to
> nothing else. That is the sentence to defend."*

> **REFUTED TWICE — do not defend this.** The identity cannot fail: with
> `use_preview=False` the preview vector is zeros, so `p_predictive` returns
> `p_reactive`'s action on every step and the two rows are one rollout
> (`AUDIT.md` C3). And the real ablation ran on 21–22 September — eight trained
> blinded agents against eight trained sighted ones, preregistered — and
> **preview is not significant**: 5 of 8 positive, mean +4.8, p = 0.3633.
>
> The defensible sentence is the one at the top of this section: *we built an
> ablation that could fail, ran it four times, and it has not separated.*
The hand-written policies cannot carry this. Their "preview disabled equals
reactive, to the decimal" was an identity built into the code (AUDIT.md C3), and
their deficit against current-grade (−0.3 points on the merged plant) is one
second of knock at the grade step. On the twenty agents of 29 September,
training beat every hand-written policy while sighted and blinded were
indistinguishable — and most of that margin rests on the knock model.

**The retrain did not separate preview from seed noise on this scenario
(INCONCLUSIVE under the MEI rule), and that is the result**: a statement about
H/τ at this operating point, reported as one — never *preview does not help*.
Pair it with a validation table that says what it does not cover, and defend
that.

# Part H — CHECKPOINT.md as it stood before the restructure reached main (14 October 2026)

Rotated verbatim when the documentation restructure was pushed (plan v3
section 8.3).

# CHECKPOINT — Current Project State

Last verified: 2026-10-14 — verify_docs.py 73/73 · drift_test.py: the affected rows after each step of the restructure; the full run follows it
main 39fce4b, with the restructure local on `docs-restructure-2026-10-14` · sim-v1 not tagged yet (plan v3 phase 3) · plant_sha 3c48890dd15bc116 (Python 3.12.10) · derived_sha 326c0835548975e2 · fingerprint schema 2

The previous CHECKPOINT.md, every session from 9 September to 14 October, is
`STATE_HISTORY.md` part B, verbatim. This file holds the current state only: the
permanent rules are `CLAUDE.md`, the history is `STATE_HISTORY.md`.

## Current objective

Test whether preview information is worth acquiring (the H/τ criterion,
`CLAUDE.md`). The two newest ablations, X1 and X2, did not settle it, and the
knock model the agents learn against is untested until drive C.

## Verified current state (each line names the script or file that proves it)

- X2 (11–13 October): INCONCLUSIVE on five pairs, the agents not converged
  (`python analyse_x2.py` -> `results/X2_RESULT.txt`; `results/x2_convergence.txt`).
- X1 (8–9 October): preview's effect below the MEI of 5.43 points of cut, 17 of
  23 pairs, sign p 0.0173 (`python analyse_x1.py` -> `results/X1_RESULT.txt`).
- The plant carries the four steps agreed on 30 September (`75ca65f`), and the
  premise reads baseline 848.1 at 883 °C (`python check_premise.py`).
- Ghassan's `GRA-2340394` (`c16b857`) was merged into Jad's work on 14 October
  (`cc5468f`; every conflict, both sides, in `conflict_2026-10-14.md`); `main`
  is `39fce4b`.
- `python verify_docs.py`: 73 of 73 checks pass.
- App suites after the merge (14 October): `python -m app.test_replay` 49 of 49
  and node 305 of 305; `app.test_results` and `app.test_agents` fail more than
  before the merge, because the results tab assumes fingerprint schema 1 (the
  open item in `team/jad.md`).

## In progress (who · branch · what)

- Jad, with Claude Code · `docs-restructure-2026-10-14` · plan v3 phase 4:
  `CLAUDE.md` under 200 lines and this file under 100, every moved line
  verbatim (`_merge_review/MIGRATION_LEDGER.md`). It reaches `main` only after
  Ghassan's OK.

## Blockers

- The knock model is untested: drive C decides how much of every agent's
  margin is real.
- Thirteen validation decisions wait for Jad's and Ghassan's columns
  (`results/VALIDATION_DECISIONS.md`); nothing is relabelled, re-preregistered
  or retrained until they are answered.

## Next actions (in order)

1. Finish the documentation restructure; push it after Ghassan's OK.
2. Drive C, then A, then D (`logs/DRIVE_PLAN.md`, revised 14 October, `c16b857`).
3. The validation decisions.
4. The results tab learns fingerprint schema 2, and the learning lab's pins move
   to the live plant (both in `team/jad.md`).
5. Plan v3 phase 3: tag `sim-v1`, write `CHANGELOG.md` and the results index.
6. The parallel items of 30 September (Ghassan's twenty on multi-climb roads,
   the spark-capped rescoring of Jad's 48, Chapter 4 with both branches side by
   side and never pooled, the battery of Phase E) and the app's backlog are
   `STATE_HISTORY.md` part E, verbatim. X1 and X2 came after them: check an item
   before taking it up.

## Files outside git (where · last backup · manifest)

- Trained agents (`runs*/`) and the per-step records (`*_record.npz`) live on
  the machines that trained them. Jad's machine: a backup of 14 October, 4,391
  files, 2.5 GB, VERIFIED, with its `MANIFEST.csv` and `SHA256SUMS`; one copy,
  on the same disk; a Google Drive copy and a USB copy are still to make.
- `GRAD-agent-backups/2026-09-23` and `2026-09-24` (`runs_c4`, sha-checked).

## References

`CLAUDE.md` (Training gate) · `README.md` · `results/README.md` ·
`STATE_HISTORY.md` · `HISTORY.md` and `CHANGELOG.md` (not written yet)
