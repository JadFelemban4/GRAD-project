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

## What this project is

A BSc graduation project, five students, University of Jeddah, Jeddah.

**The claim.** Not "a predictive controller for engines" — that is commercially
solved and academically crowded. The claim is a **criterion for when preview
information is worth acquiring at all**, governed by one dimensionless ratio:

> **H / τ** — the preview horizon divided by the time constant of the component
> being protected.

When τ ≫ H you are seeing thirty seconds into a problem that takes ten minutes
to develop, and preview buys nothing. When τ ≪ H the system reacts faster than
you can anticipate and preview is redundant. The useful region is where they are
comparable, and nobody has mapped it.

**The falsifiable version.** Preview value should collapse onto a single curve
when plotted against H/τ, regardless of which plant produced the point. If the
two plants do not overlap, the criterion is wrong or incomplete — and reporting
that is still a result.

---

## Hard constraint, no exceptions

**The project never writes to the vehicle's ECU.** Read-only OBD-II logging
only. No flashing, no CAN transmission, no tuning. If a task seems to require
writing to the car, it is the wrong task. Say so rather than finding a way.

---

## Current state — 30 September 2026 (the two branches merged)

> <!-- RETIRED-OK: 959.8, 884 -- sep17's plant, named beside the merged one -->
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

### Where every phase stands — current, 30 September (after the merge)

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — load residual **1.4 % with zero fitted parameters** (derived k = 0.831), **1.1 % with the one fitted k** (0.839), over 26 pooled points, 30–75 kPa, from a dataset of eleven drives, 321.7 minutes. **Read mistake 12 before quoting it:** that residual is a consistency check between two ECU channels, not a test of the cycle model. **Since 28 Sep the thermal network, boost ceiling, spark offset and enrichment dwell are DERIVED from the logs** (`derive_params.py`); `validate.py` 8 of 11 (6 of 7 literature, 2 of 4 against our car). The knock model is NOT validated |
| C · get an agent to learn | **Two sets, each on its own plant.** On sep17's plant: C1 (16 agents, 50 000 steps) and C4 (16 agents, 300 000 steps, NOT converged by C4's preregistered rule, `PREREGISTRATION_C4.md` 5b). On Ghassan's derived plant: twenty agents, ten seeds a side, 50 000 steps (55 episodes), a new road every episode, dt 1.0 (`results/agents/terrain_dt1/`). **None has been trained on the merged plant with the agreed fixes** (sub-stepping, spark cap, ramps) |
| D · baselines and the ablation | **done four times, never decisively.** Phase D and D2 INCONCLUSIVE; C4 SMALLER THAN THE MEI by the sign test only (p 0.0352), the permutation test disagreeing (0.3867), not converged; Ghassan's retrain INCONCLUSIVE under the MEI rule (6 of 10, power 0.26). Supervision beats `current-grade` on the median in every set — **but with spark advance forbidden that margin disappears** (the box at the top). The MEI is 50 damage units (set 22 Sep) |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary, hand-written policies only; **not quotable until the thermal network is sub-stepped** (the sweep runs at dt 2.0) |
| G · writing | **started** — `thesis/CHAPTER4_ABLATION_DRAFT.md`, drafted and reviewed 23 September; C4 paragraphs (4.10) added after. It must now carry Ghassan's retrain and the two merge-review findings |
| **APP · the live supervisor** | **runs; the six audit findings against it are now FIXED.** `app/` runs this same physics beside the car and estimates turbine temperature, which the vehicle has no sensor for. Its suite reports **49 of 49**, up from 46 because each fix shipped with a regression test. The lesson still stands and is worth more than the fixes: **the suite reported 46 of 46 while all six were live.** Only M9 carries no test of its own. **Read `AUDIT.md` and `AUDIT_FIXES.md` before quoting anything it prints.** A SECOND DELIVERABLE, not a substitute for Phase D |

**Where the app sits, and what it must not be allowed to become.** The app is
the demonstrable, showable half of this project and it will be the first thing
anyone asks to see. It is still not the claim. The claim is the H/τ criterion,
and the claim is TESTED in Phase D. **Phase D has now run four times, and it
has not proved the claim — preview has not separated from seed noise in any of
the four (the box at the top).** That is the project's result so far; what it is
not is a confirmation. The rule that got us there
is worth keeping for E, F and G: treat time spent on `app/` past the point where
it works as time taken from the claim. Note the verb: **tested**, not proved —
a phase that can only confirm is not an experiment.

What the app does earn, and it is worth saying plainly in the thesis: it is the
same validated plant, running forward in real time against a live stream rather
than in a scenario, and it inherits Phase B's validation *and* Phase B's limits
intact. That is an honest end-to-end demonstration that the model is usable
outside the notebook it was fitted in.

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

**MANIFEST DRIVES vs SAMPLE DRIVES. Quote the right one.** These are now three
different numbers and every one of them is correct:

| what | count | what it means |
|---|---|---|
| drives in the manifest | **11**, 321.7 min | everything ever logged, `pull01` and drive B included |
| drives carrying usable samples | **8** | survive the warm-sample filter |
| drives behind the 8 September fits | **8** | the set the enrichment shape and the spark slopes were built on |
| drives behind the thermal derivation | **7** | log coolant, oil and ambient for 5 min or more (`calibrate_thermal.usable_drives`) |

`verify_docs.py` asserts the first two separately for exactly this reason. A
sentence that says "ten drives" about a *fit* is wrong, and so is one that says
"eight drives" about the *logs*. Say which population you mean.

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

**What "passing project" means here:** validated simulator + agent beating two
baselines + an ablation isolating preview. That is Phase D, and it has now run
four times (the box at the top). The verdict is SPLIT, and it must be reported
as two claims and never as one:

- the trained agents beat `current-grade` on the median in every set (Phase D:
  **+29 to +34 points** on five of eight seeds, positive on seven of eight) —
  **but with spark advance forbidden that margin disappears**, so this claim
  rests on the untested knock model until drive C;
- the ablation isolating preview has not separated from seed noise in any of
  the four (Phase D: p = 0.3633 sign, p = 0.4922 permutation).

Whether the floor is down is drive C's question. Everything after Phase D
raises the ceiling.

---

## The numbers that matter

Anyone can regenerate these. Do not quote a number that a script does not print.
**`python full_run.py` runs every one of them in a single pass and writes
`FULL_RUN.txt` with each block's EXIT CODE. Sweep documents from that file, not
from this list** — a list goes stale, a transcript is dated.

```
python analyse_phase_d.py  Phase D, the first of the four ablations (the box at
                           the top has all four). 5 of 8 seeds positive, mean
                           +4.8 damage units, exact one-sided sign p = 0.3633,
                           exact paired permutation p = 0.4922 -> NOT
                           SIGNIFICANT at alpha 0.05. Also prints the agent's
                           +29 to +34 points over current-grade, which is a
                           DIFFERENT claim -- see the box at the top of this file
python drift_test.py       16 of 16 injected drifts CAUGHT. The guard's own
                           acceptance test; every row AUDIT2 Part 4a marked
                           MISSED is now caught
python power_analysis.py   At Phase D's spread (sd 214.4) eight seeds have power
                           0.10 against the minimum effect of interest (50
                           damage units) and reach 80 % only near 269. Read it
                           before calling any null "no effect"
python check_random_road.py  D2's gates: 0 of 121 grades fail to bind (weakest
                           13.73 % at +6.9 K), 0 of 20 frozen episodes, and the
                           blind arm's observations identical on every road
                           until its climb arrives -- on SEP17'S plant. On the
                           merged plant the notch moved to ~13.96 %: re-run
                           it before any new D2-design training
python analyse_c4.py       C4's preregistered test, D2 and Phase D beside it:
                           3 of 8, below-MEI sign p 0.0352 / permutation
                           0.3867 (disagree), SMALLER THAN THE MEI, NOT
                           CONVERGED. Captured in results/C4_RESULT.txt
python analyse_phase_d2.py D2's result beside Phase D's, each classified by the
                           MEI rule
python full_run.py         every script below, one pass, exit codes -> FULL_RUN.txt
python -m app.test_simulation   15 of 15. The replay lab. SEPARATE from
                           app.test_replay -- run both after touching app/
python check_premise.py    the hand-written policies on the locked climb:
                           baseline 920.1 at 883 C, current-grade cuts 43.4 %,
                           preview -0.3 points against it. Writes
                           results/premise.json. HAND-WRITTEN -- read AUDIT.md
                           C1 and C3 before quoting any of it
python validate.py         8 of 11 inside their band: 6 of 7 against literature,
                           2 of 4 against our own car (rows 8-11, since 28 Sep)
python derive_params.py    every constant the car's logs set, recomputed from
                           them -> data/derived_params.json (build_dataset.py
                           runs it). REFERENCES.md 4b: what is still typed, why
python calibrate_thermal.py  the thermal fit, per drive, with every drive also
                           scored HELD OUT; results/thermal_calibration.json
python test_reward.py      8 of 8 checks pass, four of them on the TRAINING
                           roads -- run it after any change to the reward, the
                           plant, the gearbox or the roads
python train_all.py        the twenty agents: seeds 0-9 x sighted/blinded, one
                           process each on the CPU, ~4 h; writes runs/terrain_dt1/
python record_agents.py runs/terrain_dt1   scores them on the twenty frozen
                           episodes, records EVERY step, and documents each agent
                           in results/agents/terrain_dt1/ (README.md: every table)
python knock_margin.py     the twenty with spark advance forbidden, a diagnostic:
                           median cut 67.9 -> 41.6 % sighted, 65.4 -> 41.7 %
                           blinded, against current-grade's 43.4 %
python check_roads.py      drives the baseline over 40 training roads and fails
                           if any is one the baseline cannot drive; 14 bind
python model_vs_data.py    eleven comparisons of the simulator against the car,
                           each printed beside the figure the documents quote
python run_results.py      regenerates the traces, the speed-by-grade sweep and
                           the Phase D files the figures and the page draw on
python compare_calibration.py  the 28 Sep before/after comparisons (figs 20-25)
python make_page.py        the phone-readable results page, results/page/
python build_dataset.py "logs/raw/*.csv"    321.7 min, 11 drives, 26 operating points
python compare_log.py data/master_points.csv   PASS, 1.4 % load residual,
                           k derived 0.831 and zero free parameters. Read what
                           it prints, not what you hope: it compares two ECU
                           channels through the displacement and three defined
                           constants, and it does NOT measure the breathing
                           model — mistake 12
python verify_docs.py      recomputes the published figures from the shipped
                           data, checks the derived constants and the premise
                           are FRESH, then greps every tracked document and .py
                           file both for those figures and for retired ones. It
                           prints its own total; read that, do not quote a
                           count from here
python check_map.py        spark falls with load in every row, rises with speed
                           in every column; 6 cells above the compressor ceiling
python -m app.test_replay  49 of 49 fast checks. Add --full for 59 of 59,
                           which replays the whole of 7475b5d7 and pins the
                           app's own numbers: 14278 of 14340 samples estimated,
                           peak estimated turbine 873.1 C, 14 thermal / 0
                           mismatch / 19 novel alerts. The reason for every
                           move of a pin is written beside it in the file
                           (28 Sep: the exhaust-flow fix moved 7475b5d7; the
                           derived enrichment dwell moved pull01)
```

**Two of those app figures are not measurements and must never be quoted as
though they were.** The peak turbine temperature is a MODEL OUTPUT whose heat
capacity is an assumed number (REFERENCES.md section 4), and the alert counts
are a property of thresholds this project chose. They are pinned so that a
regression is visible, which is a different job from being evidence.

`build_dataset.py` used to crash on a Windows console **after** writing all three
CSVs — its summary header printed a Greek lambda, which cp1252 cannot encode, so
the run failed loudly on data that was already correct. Header is ASCII now. If
any script ever does this again, the character is the bug, not the data.
**It happened again on 16 September, in `verify_docs.py` itself** — see
mistake 16's second half. Same cause, third occurrence, still the character.

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

**What replaces it:** run `check_premise.py`. On the merged plant (30 September) it
prints a baseline of 920.1 at 883 °C, the constraint binding against the 850 °C
trigger, and preview worth **−0.3 points** against a policy that only knows the
grade it is on now — all of it one second of knock at the grade step.

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

**And the scenario is the thing to fix, not the threshold — measured
17 September over EVERY drive.** *(17 Sep conclusion, since done: the scenario
was rebuilt at 12 % / 130 km/h on the ZF 8HP51 and now binds by ~34 K, peak
884 C against the 850 C trigger. The do-not-lower-the-limit half still stands.)*
Replaying every drive through `app/` (nine on 17 September, drive10 added on
the 19th) and reading the peak estimated turbine housing against the 1123 K
trigger, with the app's physics of those days (exhaust = fuel × 15). The merge's
exhaust-flow fix has since lowered `7475b5d7`'s pinned peak (the Numbers
section); the other rows, the 36 seconds and the fraction under the table were
not re-measured. Replay them before quoting any:

| drive | minutes | peak C | vs trigger | seconds above |
|---|---|---|---|---|
| `7475b5d7` | 55.1 | **890.6** | **+40.8** | **36** |
| `670063b2` | 7.3 | 780.3 | −69.5 | 0 |
| `cb67b01f` | 21.6 | 728.0 | −121.9 | 0 |
| `3aca2ec1` | 41.7 | 676.1 | −173.7 | 0 |
| `683640a0` | 24.0 | 664.1 | −185.7 | 0 |
| `pull01` | 7.4 | 608.0 | −241.8 | 0 |
| `fb988991` | 14.7 | 607.9 | −242.0 | 0 |
| `3f64372e` | 0.7 | 340.1 | −509.8 | 0 |
| `f51686d7` | — | no estimate | — | — |
| **`drive10` — TAIF** | **119.4** | **797.6** | **−52.4** | **0** |
| **total** | **292.0** | | | **36 s = 0.206 %** |

**ONE drive of ten reaches the limit, for 36 seconds in 292.0 minutes.**

**THE TAIF ROW IS THE IMPORTANT ONE AND IT WAS ADDED 19 SEPTEMBER.** `drive10`
is a real mountain drive — Jeddah to Taif and back, two hours — and it is the
drive this project had been saying it did not have. The ambient channel proves
the altitude without a barometer: **31.5 °C at the start, 20.5 °C at minute 50,
34.5 °C at the end.** Sea level, up, and back down.

**It does not bind. It does not come close. 797.6 °C, 52 K short, zero seconds
above the trigger in 119.4 minutes.**

And the driver was not gentle. Measured off the same replay:

| | |
|---|---|
| above 140 km/h | 15 s |
| above 160 km/h | **5 s** |
| peak speed | 167 km/h |
| turbine median at 160+ km/h | **667.8 °C** |
| **where the peak actually happened** | **137 km/h at 5792 rpm, minute 13.5** |

**The hottest moment of the Taif drive was an acceleration, not the climb and
not the top speed** — a low gear at high rpm, held briefly. Every one of those
bursts is short, and the housing has a ~50 s time constant, so none of them
lands. The 160 km/h stretch lasted five seconds and ran *cooler* than the
peak.

**This is load-per-cycle and road power for the fourth time**, after
`12 % @ 90` beating `4 % @ 150`, SAE J2807's slow heavy climb, and the real
gearbox running hotter than the invented one. A mountain road taken at 59 to
90 km/h asks 40–50 kW; the locked scenario asks **88.7 kW for twelve
uninterrupted minutes**. Altitude does not heat a turbine. Sustained power
does.

**What this settles, and it is worth more than the row.** The obvious objection
to the locked scenario — that 12 % at 130 km/h is contrived — now has a
measured answer: **the hardest real climb we have recorded is 86 K cooler than
it.** The scenario is deliberately above real driving, and that is a stated
design choice rather than an accident.

*(The synthetic climb figure quoted in the next paragraph, 812 C, is the
pre-gearbox one. On the real ZF 8HP51 the same scenario reaches 884 C. See the
19 September checkpoint.)* <!-- RETIRED-OK: 812 -->

<!-- RETIRED-OK: 812, 38, 78 -->
The synthetic climb reaches 812 C and misses by 38 K, so **the car's own driving
gets 78 K hotter than the scenario written to stress it.**

Two conclusions, and they pull in opposite directions — state both:

- *(17 Sep, pre-gearbox. Since done: the scenario was rebuilt at 12 % /
  130 km/h and binds by ~34 K, peak 884 C against 850 C. The Do-NOT-lower-the-
  limit half still stands.)* **The scenario is too mild, not the trigger too
  high.** Rebuild it from measured driving. Do NOT lower the limit: 1123 K is already 80 K more
  conservative than the 930 C pre-turbine enrichment limit REFERENCES.md cites
  (Conway et al., SAE 2018-01-1423, p. 10), and moving it is turning the one
  knob the audit named.
- **0.206 % is itself a result about H/tau, and it belongs in the thesis.** On
  this vehicle, in this driving, the protected component is near its limit a
  fifth of one percent of the time. That is a statement about how much preview
  could be worth HERE, and it is exactly the kind of answer the criterion exists
  to give.

  **The caveat that used to close this bullet is now RETRACTED, and the
  retraction is a stronger result than the caveat.** It read: *"it is not a
  measurement of the sustained-climb duty cycle the project targets, because
  no logged drive is one."* Since 19 September one is — `drive10`, the Taif
  run, two hours of real mountain driving. **It reaches 797.6 °C and spends
  zero seconds above the trigger.** So the sentence to write in the thesis is
  no longer "we have no sustained climb"; it is **"we have one, and it does
  not bind"** — which is a measurement rather than a gap.

  <!-- RETIRED-OK: 0.351, 172.6 -- naming the superseded pair IS the sentence -->
  Adding it moved the figure from 0.351 % over 172.6 minutes to **0.206 % over
  292.0 minutes**, because the numerator did not move at all: Taif contributed
  119.4 minutes and **not one second** above the limit.

#### 17. THE GEARBOX UPSHIFTED MID-CLIMB, AND ONLY A HARDER SCENARIO COULD SHOW IT

Found 18 September, by the reward gate refusing to pass. **This is the third
defect in this project that was invisible until the load became real**, after the
wrong engine (mistake 1) and the reward hack (mistake 5), and it has the same
shape: a simplification that is harmless at part load and wrong exactly where the
project does its work.

**What happened.** The scenario moved to 12 % at 130 km/h and `test_reward.py`
failed its first check: the neutral action -- which by construction reproduces
the baseline ECU -- scored **-0.124** against a +/-0.05 band. The script's own
advice is to raise the tracking weight. **That advice was written for a different
failure and following it would have made this one worse.**

**The real cause, measured on the shipped trace.** Over the whole climb the
baseline demanded **381 Nm and delivered 359** -- short by **5.7 %, on 519 of
519 samples**, just past `TRACK_TOL` = 5 %, so the hinge fired every single step.
The baseline could not hold the demand. No reward weight fixes a scenario asking
for torque the vehicle cannot make.

**Why it could not.** `Vehicle.gear_for` selected on ROAD SPEED ALONE:

| km/h | gear | demand Nm | shortfall |
|---|---|---|---|
| 110 | 5th (0.82) | 297 | 0.0 % |
| **115** | **6th (0.68)** | **364** | **7.8 %** |

**A 4 % step in road speed moved the torque demand 23 %.** That is the ratio
dropping at the 115 km/h rung of a fixed speed ladder: **the model upshifted into
top gear halfway up a 12 % grade**, which no automatic transmission does, and
then asked the engine for the whole hill at 2137 rpm.

**The fix is a load term, and it is guarded against being a convenience.**
`gear_for` now takes the tractive force and hands back a gear while the required
torque exceeds `SHIFT_LOAD` x `PEAK_TORQUE_NM` -- a 25 % torque reserve, declared
ASSUMED -- subject to the lower gear not hitting the limiter. **Every operating
point the environment had already been used at keeps the gear it had**: 110 km/h
flat, 110 at 12 %, 110 at 16 %, 90 flat and 50 km/h town are all unchanged, so
the old scenario is bit-identical. Only 130 and 150 km/h on the 12 % grade
downshift, 381 Nm -> 316 Nm at 2913 rpm.

**What it cost, stated rather than buried.** The peak turbine at 130 km/h falls
**899.4 -> 857.0 C** -- the downshift raises rpm and lowers load per cycle, so
the EGT drops. The scenario still binds, by **7 K instead of 49**, and protection
still does real work: current-grade cuts damage **29.7 %**. The gate passes at
**+0.00048**. But the starver's margin narrowed from -2.16 to -0.10, because an
engine that meets its demand easily makes refusing to work a smaller crime --
**that is the number to watch first if a trained agent turns lazy.**

**A KNOWN LIMIT OF THE FIX, because it is a flat ceiling on an rpm-dependent
quantity.** 500 Nm is peak torque, not torque at every speed, so 115-125 km/h
still over-ask: they sit at 364-375 Nm, under the ceiling, while the engine
cannot deliver that at 2137 rpm. Those speeds are not scenarios and the ceiling
was NOT lowered to smooth the table -- doing so would have moved 16 % at 110 km/h,
which is the team's third scenario. Fixing it properly needs an rpm-dependent
torque limit, which is a larger change.

**The lesson, and it is mistake 5's written down one level out:** a reward is
only safe relative to the dynamics it scores, and **a plant simplification is
only safe relative to the operating points it has been used at.** Both go stale
the moment the scenario gets harder. Run `test_reward.py` after a scenario
change, read WHICH check failed, and diagnose it before taking the advice the
failure prints.

#### A ROLLING ROAD MAKES PREVIEW WORSE, NOT BETTER. 18 September

Once the scenario binds, the obvious next question is whether preview was losing
because the road has only ONE change in it -- flat for three minutes, then a
constant grade, so 30 s of lookahead buys a single head start in 720 s. Tested by
alternating the grade about the same 12 % mean at the same 130 km/h, sweeping only
how fast it alternates. Neither bound is chosen for effect: 2 % is the policies'
own deadband (`grade_now > 0.02`) and 16 % is engine headroom, 471 Nm of 500.

| road period | baseline | grade-now | predictive | preview edge |
|---|---|---|---|---|
| constant | 1402.0 | 697.3 | 705.7 | −0.6 pts |
| 60 s | 1395.4 | 992.9 | 1025.4 | **−2.3 pts** |
| 120 s | 937.6 | 655.1 | 674.0 | −2.0 pts |
| 240 s | 754.5 | 502.3 | 514.0 | −1.5 pts |
| 480 s | 791.9 | 473.5 | 478.2 | −0.6 pts |

**The faster the road varies, the WORSE preview does.** The hypothesis was the
opposite and it is refuted.

**THE MECHANISM IS ONE LINE, AND IT IS THE POLICY, NOT THE INFORMATION.**
`check_premise.p_predictive` takes `max(preview[+15 s], preview[+30 s])`, so on a
road that keeps climbing again there is always a steep section in view and the
policy protects almost continuously -- including through the easy sections, where
protection costs and buys nothing. It is a driver who brakes for a red light
half a kilometre early. **Preview is not what loses here; using preview as a
worst-case-ahead maximum is.**

**FIRST ATTEMPT AT THIS SWEEP WAS BLIND, and the failure is worth more than the
row it produced.** It alternated 8 % ↔ 16 %, and both policies normalise grade as
`clip(grade/0.08, 0, 1)` -- 8 % gives 1.0 and 16 % gives 1.0 after the clip. The
road varied and NEITHER POLICY COULD SEE IT. Every row printed −0.1 points, which
looked like a finding and was zero information. AUDIT.md C3's lesson one level
down: a test that cannot see cannot measure, exactly as a test that cannot fail
cannot confirm.

**What this settles, and it is the useful part.** Five scenarios, three
hand-written policies, and preview loses in all of them -- by a margin that moves
with a formatting choice inside one policy. **The question "is preview worth
acquiring" cannot be answered by hand-written policies at all.** That is
AUDIT.md C3's own sentence, now measured rather than argued, and it means Phase D
is not one route to the result. It is the only one.

#### The published towing standard was tried, and it does NOT bind. 18 September

This file and README both name "a published towing cycle" as a legitimate source
for the new scenario. **It was looked up, implemented and measured, and it is the
wrong standard for this vehicle.** Recorded so nobody spends the afternoon again.

`SAE J2807` FEB2016 section 4.3.5, read off the standard's own PDF rather than a
summary: Arizona SR 68, **18.3 km (11.4 miles)**, grade **0–7 %** (Figure 2, GPS
data 11/2004), minimum speed **64.4 km/h (40 mph)**, minimum ambient **37.8 °C
(100 °F)**, air conditioning at maximum. Run with `Vehicle.mass` swept, neutral
policy:

| trailer kg | peak turbine C | vs trigger | peak torque Nm |
|---|---|---|---|
| 0 | 432.4 | −417.5 | 140 |
| 1000 | 587.0 | −262.9 | 224 |
| **2000** | **756.3** | **−93.5** | **308** |

**Two tonnes of trailer is still 94 K short**, and extrapolating puts the
crossing near four tonnes behind a 1520 kg sports car. Do not pursue it.

**WHY IT FAILS IS WORTH MORE THAN THE FAILURE, and it redirects the search.**
Compare the last row with the standard climb: 308 Nm → 756 °C against 297 Nm →
812 °C. **Nearly the same torque, 56 K apart.** The turbine node is heated by
`ua_gas_turb · mdot_exh · (egt − t_turb)`, so **the housing is heated by EXHAUST
FLOW, not by torque.** J2807 is a truck standard run at truck speeds: 40 mph puts
the engine at low speed and low airflow, so a heavily loaded engine grinding
slowly uphill produces a *cool* turbine.

**WHAT MOVES IT IS ROAD POWER — and a first reading of this measurement said
"speed, not grade", which the next sweep refuted within the hour.** Both axes
work. Neutral policy, 42 °C, 12 min:

| grade | km/h | peak turbine C | vs trigger |
|---|---|---|---|
| 12 % | 90 | 756.0 | −93.8 |
| 12 % | 110 | 812.3 | −37.6 |
| **12 %** | **130** | **899.4** | **+49.5** |
| **12 %** | **150** | **942.6** | **+92.7** |
| 7 % | 130 | 758.8 | −91.0 |
| 7 % | 150 | 820.4 | −29.5 |
| **16 %** | **110** | **906.2** | **+56.3** |
| 4 % | 150 | 708.5 | −141.4 |

**Three combinations bind, and the boundary is near 12 % at ~120 km/h.** The two
cleanest rows are the argument: 12 % at 130 km/h and 16 % at 110 km/h demand
**88.7 and 88.5 kW** of road power and reach **899 and 906 °C** — different
grade, different speed, same power, same temperature. **Do not promote that to a
law:** 12 % at 90 km/h (54.7 kW → 756 °C) is HOTTER than 4 % at 150 km/h
(60.4 kW → 709 °C), because the slower row sits at 2018 rpm against 2790 and so
runs a higher load per cycle and a hotter EGT. Flow and EGT both enter
`ua_gas_turb·ṁ_exh·(EGT − T_turb)`, and only the measurement settles a case.

That is why J2807 fails: 40 mph at 0–7 %, even behind two tonnes, is a modest
road power however much torque the trailer asks for.

**Two cautions from doing this.** The web summaries of J2807 report "11.4" as a
PERCENT GRADE; it is the LENGTH IN MILES, and only opening the standard settled
it. And the first sweep's "peak torque" column was measuring the launch
transient from rest, not the climb, which is why two different rows showed the
same number — it was deleted rather than explained.

<!-- RETIRED-OK -->
*(One caveat, stated rather than buried: the J2807 runs above used the standard's
37.8 °C, while the project scenario uses 42 °C. The gap is not the ambient — the
turbine is gas-heated and barely sees it — but the comparison is not
temperature-matched and should not be quoted as though it were.)*

---

## Twenty-two mistakes already made. Do not remake them.

*(**17 and 18 are the same gearbox, found from two directions and now merged.**
17 is the mid-climb upshift, found on `sep17` when the reward gate refused to
pass. 18 is the ratio set itself — invented six-speed against the car's real
ZF 8HP51 — found on `JMF-2340550` from the specification and confirmed against
the car's own logs. **18's fix carries 17's load-aware guard deliberately**, so
the merge resolved to one rule rather than to a conflict. Both entries are kept:
they are different failures in the same component, and the second would not have
been looked for without the first.)*

### 1. THE SIMULATION WAS THE WRONG ENGINE FOR THREE WEEKS

`plant.Geometry` defaulted to a generic **2.0 L inline-four**. `b58()` — the
real 3.0 L inline-six — was an opt-in override that **not one call site in the
repository ever passed**. Every `run_cycle()` call omitted the geometry
argument, so the Gymnasium environment, the premise check, the reward tests, the
H/τ sweep and ten of the eleven validation rows all simulated a 1998 cc
four-cylinder while every document said 2998 cc six.

Torque was 33 % low, air mass 33 % low, EGT 46 °C low.

Phase B escaped, because `predict()` and `map_from_airflow()` did use `b58()` —
which is exactly why the error survived: the number everyone watched, the load
residual, was computed on the right engine.

What it cost once corrected: the thermal network turned out to be uncalibrated,
the standard scenario turned out not to load the real engine, and the reward
hack from mistake 5 turned out to still be live. None of those were visible
while the plant was two thirds of its true size.

`Geometry()` and `b58()` now return the same object and every call site passes
one explicitly. **A default that silently picks a different physical system is
not a convenience, it is a trap.** If a second engine is ever added, pass it.

### 2. The pressure channel is not what it says

`Intake manifold absolute pressure` on this vehicle is a **pre-throttle sensor**.
At warm idle it reads 13.49 against an ambient of 14.23, where real manifold
pressure must be about a third of ambient. Using it as the model's load input
gives **75 % air-mass error**; inverting the air-mass channel gives **1.3 %**.

**Always use `plant.map_from_airflow()`.** `compare_log.py --map-from-log` exists
only to reproduce the failure for the thesis.

### 3. The baseline ECU was flattering us

The original guessed baseline ran a knock integral of 1.4–2.1 — detonating
continuously, which no production ECU does. About 90 % of its apparent "damage"
was a knock penalty. Recalibrating against real data dropped baseline damage
from 527 to 52.7 and cut the headline preview advantage from 30 points to 4.

Both of those sets are now void anyway — they were measured on the wrong engine
(mistake 1). What survives is the lesson: **a baseline you guessed will flatter
you, and the flattery shows up as a large headline number.**

### 4. The enrichment map has been wrong three times, most recently in its variable

| version | behaviour | verdict |
|---|---|---|
| v1, guessed | enriches from 120 kPa | far too early |
| v2, from one 42-min drive | never enriches | only 4 s of high-load data |
| v3, from two drives | stoichiometric to 207 kPa, then 0.85 | right effect, **wrong variable** |
| v4, from eight drives | function of engine speed and sustained dwell | current |

v3 was fitted to 17 seconds at high load. The two 8 September drives took that
to **208 seconds above 207 kPa**. Over the 1055 rows above 180 kPa the
correlations are: engine speed **−0.47**, air mass flow **−0.41**, dwell above
the 180 kPa gate **−0.44**, and manifold pressure **+0.11**.

**READ THOSE WITH THEIR ERROR BARS, WHICH THIS FILE USED NOT TO GIVE.**
AUDIT.md H4: 1055 is a count of FORWARD-FILLED ROWS. The exporter polls one
channel per row, so those 1055 rows contain about **39 independent air-mass
readings and 74 lambda readings** — a 15–30× inflation. The standard error on a
correlation at that sample size is about **±0.17**.

Two things follow, and the second is a correction to this entry's own argument:

- **The v4 conclusion still stands.** −0.56 and −0.49 are three standard errors
  from zero. Engine speed and air mass really do carry the signal.
- **The "+0.23 points the WRONG WAY" argument does NOT stand**, and it used to
  be stated here as though it did. +0.23 is 1.4 σ — indistinguishable from zero,
  and the reviewer's decimation across poll phases put it anywhere between
  −0.01 and +0.34. The honest statement is that **manifold pressure carries no
  detectable signal**, which is still enough to reject a load table. It is not
  evidence that load points the other way.

<!-- RETIRED-OK -->
*(The dwell figure was **−0.47** until 16 September, computed on a dwell axis
built from row counts over an assumed 4.6 Hz when the drives log at 4.34–6.63 Hz.
Summed from the timestamps it is −0.41. AUDIT.md H3.)*

<!-- RETIRED-OK -->
Both pressures in that paragraph are on the **corrected** scale of mistake 13.
The gate `ENR_LOAD` is 180 kPa and the high-load cut is 207 kPa; on the old
compressor-outlet scale those were 200 and 230 kPa, and they select the same
samples.

<!-- RETIRED-OK -->
*(This paragraph read 118 s / +0.02 / −0.60 / −0.52 / −0.38 until 9 September:
the seven-drive figures, written before `7475b5d7` arrived and never updated.
`base_lambda()`'s docstring had the current numbers all along, and
`verify_docs.py` asserts them and passes — the checker was right and the prose
was stale. Note the dwell term STRENGTHENED, −0.38 to −0.47: the correction
makes the v4 story stronger, not weaker. See mistake 11.)*

Below about 3300 rpm the car does not enrich however long the
boost is held; above 4500 rpm it runs stoichiometric for the first seconds of a
pull and enriches to 0.81 only after roughly eight seconds.

**Enrichment on this engine is component protection, not a load table.** That
matters beyond calibration accuracy: enrichment is one of the actions the agent
controls, and it is a thermal action.

**The lesson, twice over: one drive is not evidence, and a fit that reproduces
the effect can still be built on the wrong variable.** Check how many samples
support a fit, and check that the variable you fitted against actually
correlates.

### 5. The reward had a live hack — twice

**First time.** An unconstrained Dirichlet over three preference weights let the
tracking weight land near zero, and on those episodes refusing to make torque
was free — a policy that pinned boost trim to minimum scored **+0.285** against
neutral's **+0.003**. Fixed with `TRACK_W_MIN = 0.45`.

**Second time.** That fix was verified on the four-cylinder, in a scenario so
light the torque constraint never bound. On the real engine at a grade that
actually loads it, the starver scored **+0.011** against neutral's **−0.027**:
the hack was back, and a weight floor alone could not close it, because a linear
tracking penalty is always tradeable against damage at some exchange rate.

The fix is a tolerance band plus a steep hinge, `TRACK_TOL = 0.05` and
`TRACK_HINGE = 25`, sized so that **no achievable damage saving pays for a
sustained torque shortfall beyond 10 %**. Starver now scores −0.280 against
neutral's −0.004.

**Delivering the requested torque is the job, not a preference.** Run
`test_reward.py` after any reward change *and after any change to the plant or
the scenario* — a reward is only safe relative to the dynamics it scores.

### 6. Extrapolating a part-load fit into boost

A straight-line spark fit on 11 part-load points, extrapolated to 240 kPa, put
the baseline at +21° BTDC, which no turbo engine survives. The shipped map is
two pieces: the fit below ~90 kPa, and the plant's own knock limit above it.

**Do not extend a fit beyond the data that produced it.** Say where it stops.

### 7. A channel can hit its range limit and keep reporting

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on seven
separate drives, **568 samples** (six and 547 until drive B's last roll-on). That is a sensor ceiling, and on the same
samples `Air mass flow participating in combustion` reads up to 1233 kg/h.

A pinned sample under-reports air, so the manifold pressure inverted from it
comes out low and the compressor pressure ratio at that flow comes out high —
exactly at the top of the envelope, where the fit is most exposed.
`build_dataset.py` flags them (`maf_pinned`) and excludes them from `stable`.

They are **not repaired** by substituting the combustion-air channel: that is
the ECU's modelled trapped charge, a different quantity (median ratio 1.095),
and splicing two definitions puts a step in the middle of the curve.

**Before fitting anything, check whether the channel saturated.** A flat maximum
repeated across drives is the tell.

### 8. A "60 second window" was neither 60 seconds nor a window

`steady_points()` sizes its window in SAMPLES, from each drive's average rate.
On a drive whose rate is not constant, that is not a 60-second window at all.
Measured before the check existed: windows spanned **42.8 to 73.7 seconds**, and
one contained an internal hole of **3.18 s** during which nothing was recorded.

The cause is upstream. `fb988991` was logged with **655 channels selected** and
the logger could not keep up: 196 gaps larger than three times the median
interval, **222 of its 980 seconds missing entirely — 23 % of the drive never
recorded.** Its nominal 3.52 Hz is not a slow steady rate, it is a normal rate
with a quarter of the samples dropped.

That single fact explains three separate symptoms previously filed as unrelated:
the fuel-cut point with a 124 % residual, the load channel that disagreed with
its own airflow, and the drive's outlier status in every per-drive table.

A window is now rejected unless its real wall-clock span is within 20 % of
WINDOW_S and it contains no gap larger than four median intervals. Every
surviving point records `t_span` and `max_gap` so the check is auditable.

Effect on the day: 20 operating points became 17, `fb988991` contributed none,
and the pooled load residual roughly halved. **Do not quote that day's residual
as the project's number.** The dataset has since gained a drive and the charge
temperature has since been corrected (mistake 13), and the current figure is
**1.4 % derived / 1.1 % fitted over 26 points, 30–75 kPa**. Be honest about the
improvement either way — part of it was the removal of the worst drive, and the
exclusion rule was written from a measurable defect rather than from the
residual, which is the only reason it is legitimate.

**But do not read this as "fb988991 was logged wrong."** It and `f51686d7` were
deliberate reconnaissance runs made before anyone knew which parameters this car
publishes, with every channel selected on purpose. They are the reason the
21-channel set exists, and they are still answering questions — see
`logs/CHANNEL_CENSUS.md`. A census log is supposed to be unusable as driving
data; that is the trade it makes.

The rule is therefore: **census once with everything, then record the small set
for real drives.** Twenty channels log cleanly at 4.6 Hz with no dropouts.

### 9. A knock limiter that failed OPEN, and published MBT as the calibration

`check_map.py` searched spark from 0 to 45° and recorded the knock-limited
advance as `klsa`, starting at `None`. The caller then did:

```python
final = min(mbt, klsa) if klsa is not None else mbt      # WRONG
```

In a cell that knocks at **every** advance in the range, `klsa` stayed `None`
and the table printed **MBT** — the most knock-prone advance in the row — as if
it were the calibration. The 1200 rpm row read `11, 3, 21, 22`: spark falling
with load as it should, then jumping back up by 18° at 180 kPa. That jump is
the fallback firing, not physics.

A limiter that publishes the unlimited value when it cannot find a safe one is
worse than no limiter, because the output still looks like a number.

Second, smaller defect in the same function: `klsa = sp` inside the loop with no
`break` records the **last** advance seen below the threshold, not the largest
one with every advance below it also safe. The knock integral is not monotonic
in spark — it turns over near 42° as combustion finishes too early to dwell at
peak temperature — so a cell whose integral dipped back under 1.0 at extreme
advance would have published that extreme advance as safe. No cell currently
does. The search now stops at the first knocking advance, which is what "knock
limit" means.

**Third, the cells were not operating points at all.** 1200 rpm at 180 kPa is
off the compressor map: the highest MAP that closes on itself against
`boost_ceiling_kpa` is 148 kPa at that speed, 168 at 1600, 184 at 2000, 204 at
2500. Six of the 56 cells in the grid are unreachable and are now marked `--`
rather than filled with numbers from a state this engine cannot occupy.

With all three fixed the map is monotonic in both directions — spark falls with
load in every row, rises with speed in every column — and **zero reachable
cells** hit the fail-open path, so no published figure changes. Every spot check
is unchanged. The bug was never affecting a result; it was affecting whether the
table could be shown to an examiner.

**Found from a screenshot of the terminal, not from a test.** Nothing in the
repo asserted that the spark surface was monotonic. If a table is meant to have
a shape, check the shape.

### 10. `neutral_action()` was not neutral, and was outside the action space

The five actions are not the same kind of thing. Actions 0–2 are **trims** added
to what the baseline commands, so their neutral is 0. Actions 3 and 4 are
**absolute duties** — cooling fan and coolant pump — and their neutral is what
the baseline runs, not zero.

`neutral_action()` mapped all five to "zero", which put the fan **off** and the
pump at its 0.3 floor. That is not a neutral policy, it is a policy with the
cooling disabled. It also returned **−1.857** for the pump: outside the
`Box(-1, 1)` action space the env declares. `step()` clips, so it never crashed.

`test_reward.py` already knew — it carried a local `true_neutral()` and a
docstring explaining the trap — but the fix lived in the test file while the
exported function stayed wrong, and `engine_env.py`'s own `__main__` block
imported the broken one and printed its score under the label `(target: ~0)`.

That block made the second mistake its own docstring warns about too: it rolls
200 steps of a 60 s episode, and `make_grade_climb()` puts the grade at
**t = 180 s**. It never reaches the climb. `python engine_env.py` was therefore
reporting `-0.06046` next to the words "target: ~0" for a 40-second cold cruise
that contains no constraint and no reward check.

Fixed in `neutral_action()` itself, with an assert that the result is inside the
action space. `true_neutral()` is now a pass-through. The `__main__` block is
labelled a smoke test and says to run `test_reward.py` for the real figure.
`test_reward.py` still reports neutral inside the ±0.05 band, because it was
already using the correct vector.

**The lesson: a fix that lives in the test file is not a fix.** If a helper is
wrong, correct the helper. Everything downstream of it inherits the bug, and
the next person to call it will not have read the test's docstring.

**19 September: the fix was right and the SENTENCE EXPLAINING IT was backwards.**
The corrected `neutral_action()` carried a caveat saying the baseline's fan
"holds 1.0 once the engine is hot, which is the part of the episode the
constraint binds in — exactly neutral during the climb, slightly over-cooled
during the first three minutes of flat running." Measured on the locked
scenario over the 720 s episode:

| fan duty | whole episode | during the climb |
|---|---|---|
| 0.0 | 26.8 % | 2.6 % |
| 0.4 | 73.2 % | **97.4 %** |
| 1.0 | **0.0 %** | **0.0 %** |

**The baseline fan never reaches 1.0 at all**, because coolant peaks at 94.2 °C
here and the 1.0 rung needs 98.9 °C. So the action is over-cooled *during the
climb* — the exact window the caveat claimed it was neutral in — and neutral
during the flat running it claimed was over-cooled. **Both halves inverted.**

**The constant was NOT changed, and that is deliberate.** The fan acts on the
coolant loop (700 W/K of a 1925 W/K peak UA) while the turbine housing is
gas-heated, so the protected component barely sees it; `test_reward.py`
measures the whole effect and neutral still scores −0.00038 against a ±0.05
band. Moving a constant inside a locked scenario to make a docstring true would
be tuning for prose. **The sentence was what was wrong, so the sentence is what
changed.**

Mistake 11's shape, inside mistake 10's own function: the code was right, the
number was right, and nothing was checking the prose beside them.

### 11. The seven-drive figures survived in the prose after the data moved on

<!-- RETIRED-OK: section 113, 168.1, 5, 7, 8, 30534 -- this whole entry is the record of what changed. -->

`7475b5d7` arrived on 8 September and took the dataset from 113 minutes over
seven drives to **168.1 minutes over eight**. The code was updated. The
documents were not, in six places:

| where | said | should say |
|---|---|---|
| CLAUDE.md mistake 4, README | 118 s above 230 kPa | **198 s** |
| CLAUDE.md mistake 4, README | corr(λ, MAP) **+0.02** | **−0.05** |
| CLAUDE.md mistake 4, README | −0.60 / −0.52 / −0.38 | **−0.47 / −0.41 / −0.44** |
| README enrichment table | n = 353 / 80 / 176 | **441 / 235 / 665** |
| CLAUDE.md limitations | seven drives, 113 min, five carrying | **eight, 168.1, six** |
| CLAUDE.md limitations | weakest cell: short dwell, n=29, 0.94 vs 1.00 | **long dwell, n=47, 0.90 vs 0.93** |

`base_lambda()`'s docstring had every one of the corrected figures already, and
`verify_docs.py` asserts them and passes. **The checker was right, the code was
right, and the prose was wrong** — which is exactly the failure verify_docs.py
was written for, recurring one level up.

Two details worth keeping:

- **The correction strengthens the result.** The dwell correlation moved from
  −0.38 to −0.47 and the 3500–4500 rpm cell went from n=29 to n=47. The stale
  numbers were understating the evidence for the model's own central variable.
  A stale number is not automatically a flattering one, which is why "it still
  supports our conclusion" is not a reason to leave it.
- **The old weakest cell was noise.** At n=29 that cell read 0.94; at n=47 it
  reads 0.99, and the genuinely weakest cell is a different one. Quoting a cell
  as "the weakest" when it holds 29 samples was reading structure into scatter.

`verify_docs.py` now greps the documents for these retired values and fails if
any reappears (`RETIRED` at the bottom of the file). **Checking that a number is
correct is not the same as checking that no document still carries the old one.**

**11 September: the same failure, one level further up.** The checker compared
each figure computed from the shipped data against a constant written inside
`verify_docs.py` itself — and then never opened a document. It printed green on
every run while **55 stale figures** were still shipping across CLAUDE.md,
README.md, `validation_table.md`, `logs/CHANNEL_SET_FINAL.md` and four `.py`
docstrings, including the dataset size, the MAF ceiling, the enrichment
correlations and the load residual. Every one of them had a matching green line
in the checker's own output.

It now scans every tracked `.md` and `.py` file, compares each figure **as the
document states it** against the value computed from the data rather than
against a constant of its own, and fails naming the file and the line. A passage
that quotes a superseded figure on purpose says so with a `RETIRED-OK` marker in
its own section, and the checker counts those separately.

**A checker that only checks itself is not a checker.** That is the lesson of
this whole pass, and it is mistake 11 recurring one level up for the second
time: the data were right, the code was right, and nothing was looking at the
prose.

**And record HOW 55 of them arrived at once, because that part will recur.** The
v17 release did not drift figure by figure. Its documents were written from an
earlier base and the corrections made in the last v16 commit were simply not in
it — `validation_table.md` came back saying 30 534 quasi-steady samples, 192
pinned MAF samples and seven drives, all of which v16 had already fixed. The
code moved forward and the prose moved backward, in the same zip.

Two rules follow, and neither is optional:

- **A release is a diff against the repository, not a fresh export of someone's
  working copy.** Before shipping an archive, diff it against the tree it will
  land on and account for every file that moves BACKWARD. A document that gets
  shorter is the tell.
- **Unzipping over a repository is not an update.** It cannot delete, so any
  tracked file the archive omits survives at its old content while everything
  around it moves on. Seven such files were carried for two releases this way
  and were deleted on 11 September — they had become a second source of truth
  that contradicted the first, and nothing referenced them.

Run `verify_docs.py` immediately after unpacking any release. It is now the
thing that would have caught this on the day it shipped.

**14 September: a third recurrence, and it names the two holes the checker
still has.** `pull01` took the manifest from eight drives and 168.1 minutes to
**nine and 175.5**. Seventeen lines were swept to the new figure. **Five were
not**, and they escaped by two different routes, both worth knowing:

- **Three escaped the regex**, because the patterns are anchored. The
  dataset-size pattern needs the words *pooled*, *dataset*, *manifest* or a
  drive count within thirty characters of the figure, so
  `REFERENCES.md`'s "168.1 minutes of OBD-II logs from our own car" and
  `CHECKPOINT.md`'s "30–75 kPa, 168.1 min." matched nothing. An anchored
  pattern is the right trade — a loose one reported the thermal fit's "three
  drives (80 minutes)" as a wrong total — but it means **a figure written in
  an unusual sentence is invisible to the checker.**
- **Two escaped inside a `RETIRED-OK` paragraph.** The marker exempts its
  whole paragraph, and in `validate.py` and `build_dataset.py` a **live**
  claim about the current dataset sat in the same paragraph as the retired
  figure the marker was there for. The exemption is a blunt instrument: it
  cannot tell the historical sentence from the current one beside it.

**And nothing in `RETIRED` was guarding 168.1 at all** — the seven-drive entry
still named "eight drives, 168.1 minutes" as the value to use instead, so the
list was pointing at a figure that had itself been superseded. A retired-value
list has to be swept when the value that replaced it moves on.

Fixed: the five lines carry the current figure, the seven-drive entry points
at ten drives, and `168.1` is now a retired pattern in its own right. The
pattern deliberately does **not** match "eight drives" on its own, because
the enrichment map and the compressor fit genuinely rest on eight drives of
samples: `pull01` adds 7.5 minutes and **zero** samples, so every figure fitted
to samples is unchanged and those sentences are still true.

**The rule that comes out of three recurrences:** when a figure changes,
grep the whole tree for the OLD value yourself and read every hit, then add
it to `RETIRED`. Do not trust a green run to prove the sweep was complete —
a green run proves only that the patterns that exist found nothing.

<!-- RETIRED-OK: 11.7 -->
**22 September: the fourth recurrence, and it was in the GUARD, found by the
guard's own acceptance test.** `AUDIT2.md` fix 3 swept the KNOWN STALE ledger
from 187 mentions to zero (commit `3f4627d`), and emptying it was right. But
`drift_test.py` then fell from **16 of 16 to 14 of 16**, and one of the two was
a real hole: the ledger had been counting the void `+11.7` margin in the files
that quote it, and that COUNT was the only thing catching an edit of `+11.7`
into `+13.7`. Nobody had written that down. **A protection that exists only as
a side effect of another mechanism disappears when that mechanism is retired.**
It is now an explicit check, `PINNED_HISTORY`, and the test is back at 16 of 16.

The same sweep found two more holes in the guard that had been there since
fix 2, both worth knowing when you write a marker:

- **HTML-comment markers were invisible.** The tag stripper deleted
  `<!-- RETIRED-OK ... -->` with every other tag, so every marker in
  `presentation/*.html` was decorative. They survive stripping now.
- **A marker's explanation was read as figures.** `RETIRED-OK: 900.9 -- the
  baseline at dt 0.2, not the protocol step of dt 1.0` also excused 0.2 and
  1.0 in its scope. Figures now come from the list before the first ` -- `.

And one forward-update of exactly this entry's shape: commit `6e40cd8` changed
"all nine drives" to "all ten drives" in mistake 14 and `app/alerts.py` when
drive10 arrived, **without re-running the measurement** the sentence described.
Restored. **After retiring or reworking anything in the guard, run
`drift_test.py` before committing** — it is the only thing that checks the
checker.

### 12. A residual that could not see the thing it was said to validate

<!-- RETIRED-OK: section -- this entry is the record of what changed. -->

`compare_log.py` reported a load residual and the documents called it "the
simulator matches the car". **It never tested the simulator.**

`map_from_airflow()` inverts the same relation `run_cycle()` uses, so:

```
load_model = eta_v*(1-f_res)*map   and   map = m_dot*R*T / (eta_v*(1-f_res)*V*rpm/120)
    ==>  load_model = m_dot*R*T / (V*rpm/120)      eta_v and f_res CANCEL
    ==>  k*load_model = 269.6*m_dot*R / (V*rpm/120)   T cancels too
```

Measured, not argued:

| test | residual |
|---|---|
| as shipped | 1.3737 % |
| intake temperature forced to 300 K | 1.3738 % |
| `eta_v` forced to 0.50 | 1.3740 % |
| `eta_v` forced to 1.20 | 1.3739 % |
| model-free, `plant.py` never imported | **1.3740 %** |

Delete the entire breathing model and the number does not move. It is a
consistency check between two ECU channels — relative air filling against air
mass flow — through the displacement and three defined constants.

**Both the fitted 1.1 % and the derived 1.4 % have this property.** The derived
residual is the larger of the two, and that is the honest direction: one free
parameter should fit better than none. Dropping the parameter was not a
regression — it made an existing overstatement visible.

What the number DOES earn, and it is not nothing:

- It pins the meaning of BMW's `Relative air filling` channel: the DIN
  reference state, 1013 mbar and 0 °C. That was a guess before.
- **It is blind-sensitive to displacement.** Derived k on the true I6 gives
  1.4 %; forced onto the old 2.0 L inline-four it gives **48.1 %**. The fitted
  form absorbs the wrong engine into the constant and reports **1.1 % either
  way**. Had the derived form been in place in August, it would have caught
  mistake 1 on day one.
- Zero fitted parameters. That part was always true.

**The lesson: a residual computed through an inversion of the same model cannot
test that model.** Before quoting any residual as validation, perturb the
parameter it supposedly validates and check the number moves. It takes one run.

Also retract the "0.1 % agreement" language. The implied reference temperature
is **276.9 K**, not 273.15 — a real +1.4 % bias — and the fitted-vs-derived
agreement was partly luck. Say: *consistent with a 0 °C reference to within
1.4 %, and excludes 20 °C.* Bosch defines it; cite them rather than claiming a
discovery.

### 13. The charge temperature was a compressor outlet

<!-- RETIRED-OK: section -- this entry is the record of what changed. -->

`logs/CHANNEL_SET_FINAL.md` labelled `Intake air temperature before throttle
valve` as "charge temperature. Post-intercooler", and `build_dataset.py` and
`compare_log.py` fed it straight into `map_from_airflow()`.

**It reads 149 °C under boost, 163 °C peak.** No water-to-air charge cooler
with its circuit near ambient delivers 149 °C air to the ports. What it matches
is a compressor outlet: PR 2.3 at 70 % efficiency from 40 °C gives 160 °C. The
B58 carries its cooler INSIDE the intake manifold, downstream of the throttle
body, so "before throttle valve" is before the cooler.

<!-- RETIRED-OK: 587, 887 -->
The car settles it. **587** boosted MAF-unpinned model samples against **887**
boosted readings of the vehicle's own `Boost pressure` channel (median
226 kPa) — the 10 September counts. *(With the drives since added, the same
comparison rests on 762 model samples against 1097 logged readings, and the
shipped formula's gap is still +1.9 % — `verify_docs.py`, CHARGE TEMPERATURE.)*

| charge temperature used | inverted MAP | gap |
|---|---|---|
| the raw sensor (117 °C median) | 279.5 kPa | **+23.7 %** |
| `plant.charge_temperature()` (52 °C median) | 232.7 kPa | **+1.9 %** |
| ambient + 8 K (45 °C median) | 227.5 kPa | +0.7 % |

*(28 September: the 117 °C in the first row does not reproduce. The 587
samples whose inversion gives the 279.5 kPa read 106.8 °C at the median, while
the 279.5 kPa itself reproduces exactly (`plot_sim_vs_car.py`, chart 2). Which
population the 117 °C describes is not recorded, so treat it as unverified.
`plant.charge_temperature()`'s docstring carries the same row.)*

**The >200 kPa gate on the model side is not arbitrary, and say so wherever
this table appears.** The logged side filters on `Boost pressure` > 15 psi
gauge, and (15 + 14.23) × 6.894757 = **201.5 kPa absolute**, so a 200 kPa model
gate selects the same population by construction rather than by choice.

**This file used to blame that 23.7 % on `volumetric_efficiency()` understating
breathing under boost. It was the temperature. The breathing model is cleared,
not convicted** — and there is no part-load test of it at all, because both
pressure channels on this car sit before the throttle.

`ambient + 8 K` scores +0.7 % and was **rejected**: it is a knob tuned to hit
the target, which is mistake 12 all over again. The shipped formula was written
independently for the Gymnasium environment months earlier and carries no
parameter fitted to the boost channel. 1.9 % from an independent model beats
0.7 % from a fitted one.

<!-- RETIRED-OK: 0.784, 0.837, 0.783 -->
**What it changed.** Operating points 31–82 kPa → **30–75 kPa**. Fitted k 0.784
→ 0.837, derived 0.783 → 0.831. `ENR_LOAD` 200 → 180 kPa, because the gate is
written in manifold pressure and manifold pressure changed definition — 180 on
the new scale selects exactly the 1055 samples that 200 selected on the old one,
and every enrichment figure reproduces to the decimal without a refit. *(The
fitted k has since moved on to 0.839; `compare_log.py data/master_points.csv`
prints the current value.)*

**What it did NOT change.** The premise result — 829.2 / 548.6 / 437.6 / 548.6 —
*(all four since VOID, AUDIT.md C1/C3; the point here is only that the sensor
change did not move them)* is identical, because the simulator never used the sensor; `engine_env` always
modelled its own charge temperature. The load residual is also identical at
1.4 %, because T cancels (mistake 12). **The residual could not see the very
error being fixed.**

**Third channel on this car that is not what its name says**, after the
pre-throttle pressure sold as manifold pressure and the MAF that saturates while
still reporting. **Treat every channel name as a hypothesis.**

---

### 13b. CONFIRMED 13 September — the sensor is a LAGGED compressor outlet

> **Restored 16 September.** This entry shipped in the v19 release archive but
> never existed on the branch, because the branch did not have `pull01` — and
> the merge that brought `pull01` in took the branch's `CLAUDE.md`, which
> dropped it. It is load-bearing: `app/reader.py`'s entire channel budget is
> built on the 7.5 s / 1.45 s measurement below, and the app cites this entry
> by number. **Mistake 16, in miniature: the archive held something real and
> the merge nearly threw it away.**


`pull01`, a purpose-built **7-channel** drive, settled mistake 13 and explained
why the first attempt at settling it failed.

**The logging rule was confirmed to the decimal.** The logger polls one channel
per row, round-robin, so per-channel rate is (row rate ÷ channels):

| drive | channels | predicted | measured |
|---|---|---|---|
| `7475b5d7` | 26 | — | 7.5 s |
| **`pull01`** | **7** | **1.43 s** | **1.45 s** |

**5.2x faster per channel**, from logging fewer of them. Halving the channel
count really does roughly halve the interval.

**And that resolution is what made the physics visible.** Testing whether
`Intake air temperature before throttle valve` is a compressor outlet:

    T_out = T_inlet * (1 + (PR^0.2857 - 1) / eta)

| test | correlation |
|---|---|
| raw, on the old 26-channel data | +0.47 |
| raw, on `pull01` | +0.35 |
| **`pull01`, with a first-order thermal lag applied** | **+0.95** |

Best fit: **eta ~= 0.55-0.65, sensor time constant ~= 10 s**, RMSE 13.8 K, with
a residual **+11.7 K** offset consistent with heat soak in the charge pipe.

**The hypothesis was right and the earlier test was simply too slow to see it.**
A sensor with a 10 s time constant cannot be characterised by samples taken
7.5 s apart — there are barely two points per pull. At 1.45 s there are four or
five, and the lag becomes fittable. The weak +0.35/+0.47 correlations were an
artefact of the sampling, not evidence against the hypothesis.

This also explains the raw readings: the sensor peaks at 150 C on `pull01` while
the un-lagged compressor-outlet prediction at peak boost is around 200 C. It is
not reading a lower temperature — it is failing to keep up with a rising one.

**`pull01` contributes ZERO samples and ZERO operating points, by design.** It
carries no coolant channel, so the warm-sample filter excludes it outright. A
purpose-built drive answers one question and cannot contaminate a calibration it
was not designed for. That is the argument for small sets, not just the rate.

**What this does NOT change.** `charge_temperature()` is unaffected — the charge
temperature is still post-intercooler and still unmeasured on this car. This
confirms what `iat_pre` is NOT, which is what mistake 13 was about.

---

### 14. THE APP'S FAULT DETECTOR WAS MEASURING THE THROTTLE — mistake 2, a third time

Found 14 September, while tuning what looked like an over-sensitive threshold.

`app/alerts.py` compared the manifold pressure **inverted from measured air
mass** against the pressure read from the vehicle's own `Boost pressure`
channel, and called a disagreement above 15 % a fault. On `7475b5d7` it raised
55 events, which reads like a threshold that needs raising.

It was not a threshold problem. The firing condition was true for **13669 of
14278 samples — 95.7 % of the drive, median −52 %.** It produced only 55 events
because a 60 s cooldown was collapsing a continuous, systematic disagreement
into a handful of discrete-looking ones. **A detector that fires on 96 % of
normal driving is not sensitive, it is measuring something else.**

What it was measuring: `Boost pressure` on this car sits **BEFORE THE THROTTLE**,
exactly like `Intake manifold absolute pressure` in mistake 2. At part throttle
the pressure before the plate and the pressure after it are different physical
quantities, and the throttle is the thing making them different. Binned by the
logged throttle angle:

| throttle | n | median disagreement |
|---|---|---|
| 0–25 % | 13431 | **−52.5 %** |
| 25–50 % | 222 | −61.1 % |
| 90–100 % | 236 | −33.1 % |

and binned by the pre-throttle pressure itself, the disagreement collapses
exactly where the throttle stops restricting:

| logged pre-throttle | n | median |
|---|---|---|
| 90–110 kPa | 8538 | −56.7 % |
| 110–130 kPa | 4782 | −44.0 % |
| **200–250 kPa** | **157** | **+7.7 %** |

That −52 % is the same 44–52 % this file's limitations section already records
for the 22 steady points. **It was never a fault and it was never news.**

**The fix is three validity gates, and the threshold was not where it went.**

1. **Wide-open throttle only**, expressed as a pressure ratio so it needs no
   extra channel and no extra budget: `logged / ambient >= 1.8`. Pooled over all
   nine drives of 14 September, MAF-unpinned *(this read "ten" from 19 Sep:
   commit `6e40cd8` forward-updated the count when drive10 arrived without
   re-running the measurement — mistake 11's shape; drive10 is not in these
   figures)*, the disagreement at that gate has a median of
   **+6.5 %**, and per drive **+7.7 / +6.8 / +3.6 / +1.2 %** — consistent with
   the **+1.9 %** that `plant.charge_temperature()` already records for this
   same comparison under boost.
2. **MAF not pinned** at its 1020 kg/h ceiling (mistake 7).
3. **Persistence counted in DISTINCT READINGS**, over a window spanning at least
   one measured 6.0 s channel refresh.

**Two things found on the way that are worth more than the fix.**

- **The suspected cause was the wrong one, and backwards.** The obvious
  hypothesis was MAF saturation (mistake 7). Pinned samples turn out to be the
  ones that **AGREE** — median −5.4 % against −52.5 % for the rest — because
  pinning only happens at wide-open throttle, which is the only place the
  comparison was ever valid. Excluding them is still right, for the separate
  reason that they are biased low by a known sensor limit. They were never the
  cause of the 55 events.
- **A forward-filled stream is not a stream of measurements.** The exporter
  writes every channel on every 0.15 s row and each one only changes when it is
  actually polled. The worst window found on a healthy drive, `cb67b01f` at
  t = 825 s, was **21 consecutive samples all reading +40.9 %, spanning 4.8 s,
  containing exactly ONE air-mass reading and ONE boost reading.** A median over
  those 21 samples is that one measurement, counted 21 times. Requiring the
  window to span a refresh interval is what makes persistence mean persistence:

  | span required | windows | worst healthy median |
  |---|---|---|
  | ≥ 0 s | 89 | 34.5 % |
  | ≥ 4 s | 74 | 16.6 % |
  | **≥ 6 s** | **45** | **13.6 %** |
  | ≥ 12 s | 16 | 6.9 % |

**A steadiness gate was tried and is actively wrong.** Requiring a *settled*
operating point selects cruise at a closed throttle with the compressor still
making pressure behind it — a genuine and blameless −60 % — and rejects the
wide-open pulls, which are the only valid samples and are transient by nature.
**On a road car the only place this comparison means anything is inherently
unsteady.**

**The threshold moved 15 % → 25 %, and the reason is a measurement.** The old
15 % was justified in the docstring by "the model's validated load residual is
1.4 %". Both halves of that were wrong: per **mistake 12** the 1.4 % residual
cannot bound this or any other comparison involving the breathing model, and
measured directly under the gates above, the worst windowed median on nine
healthy drives is **13.6 %** — so 15 % carried 1.4 points of margin. 25 % carries
11. **The gates removed the 55 events, not the threshold**; with the gates in
place and the threshold left at 15 %, `7475b5d7` still raises zero.

**The lesson: before tuning a detector, check that it is comparing two
measurements of the same physical quantity.** Three of this car's channels have
now been misread the same way.

### 15. THE APP REPORTED A TEMPERATURE ITS OWN PHYSICS SAID WAS IMPOSSIBLE

Same session, the neighbouring file. Two defects, one cause.

**First, the warm-up was a timer, and the timer used the wrong τ.**
`app/estimator.py` seeded the thermal state on connection and declared the seed
forgotten after a fixed `WARMUP_S = 145`, quoted as three turbine time constants
at τ = 48 s. But τ for the turbine node is `c_turb / (ua_gas_turb·ṁ_exh +
ua_turb_amb)`, so it depends on exhaust flow:

| condition | exhaust flow, g/s | UA, W/K | τ |
|---|---|---|---|
| hard climb | ~112 | 119 | **50 s** |
| cruise | ~24 | 40 | **151 s** |
| idle | ~8 | 25 | **239 s** |

*(Units live in the header on purpose. With the unit written next to each
number instead, the first row tripped `verify_docs.py`'s pattern for the hardest
sustained FUEL flow — a different quantity, an order of magnitude smaller, and
exactly the collision that file's docstring warns about.)*

**48 s is the LOADED time constant.** Sit in traffic and the seed is still
largely intact at 145 s, and the app would have been calling the estimate
trustworthy while it was mostly assumption. Measured on the replay of
`7475b5d7`, the seed actually takes **461 s** to be forgotten, not 145; on a
synthetic light-load stream **576 s** against **110 s** loaded.

**Second, and worse, the seed was outside its own physics.** The nominal seed
was a flat 500 °C, chosen "because we have nothing at all to go on". That was
not true — engine speed, air mass and coolant are all visible, so the operating
point is visible, and an operating point has a settled turbine temperature. And
the flat 500 °C was not merely imprecise: on `pull01` the housing at the seed
instant is bounded by ambient and the model's own exhaust temperature, which is
**35–193 °C**. The app was displaying a number **300 K above what its own model
said was possible**, and displaying it as the headline figure.

**The fix replaces the timer with a measured bound.** Three copies of the
thermal network are integrated with identical inputs, differing only in where
the turbine started — one at ambient, one at the model's own EGT. The width
between them is what the seed is still worth, it narrows at whatever rate the
driving allows, and thermal alerts stay suppressed until it is inside 25 K. The
nominal is now the steady state the current operating point implies — the fixed
point of the very equation `ThermalNetwork.step` integrates, so no new
parameter — clamped into the bracket so **the reported value can never sit
outside its own error bar**.

<!-- RETIRED-OK: 593.7, 673.5, 885.2, 884.9 -->
**What it cost, and be honest about it in the thesis.** `pull01`'s peak
estimated turbine reads **593.7 °C** where the old code said 673.5 °C, because
that drive is short and its peak falls inside the warm-up. `7475b5d7` moved
**885.2 → 884.9 °C**, essentially nothing, because a 40-minute drive forgets its
seed long before its peak. **The long drive was never wrong; the short one was,
and only the bound could tell them apart.**

**The limit the bound does NOT cover, and it is real.** The bracket holds under
steady operation. Connect within a few tens of seconds of lifting off a hard
pull and the housing can be hotter than the gas now flowing through it, because
the gas cooled first — so the upper bound will be too low. No channel on this
car would catch that. A cold start has the opposite and happier property:
coolant, ambient and exhaust are all low together, the bracket is narrow from
the first sample, and the estimate is trustworthy almost immediately.

**The lesson: a convergence claim needs a convergence measurement.** "Three time
constants" is a statement about a τ you have to name, and naming the wrong one
is invisible until something checks.

### 16. A RELEASE ARCHIVE TRIED TO DRAG THE TREE BACKWARDS

<!-- RETIRED-OK: section 113, 7 -->
*(This entry quotes the retired figures on purpose — naming them IS the
entry. The marker above is what tells `verify_docs.py` so, and it is the
same mechanism mistake 13 uses for the same reason.)*

Found 14 September, merging the v19 archive into a branch that had moved on.

This file already warns that documents *missing* from a release archive get left
behind while everything around them moves on. **The opposite is the worse
failure and it happened here.** The v19 archive was an OLDER snapshot of almost
everything, carrying one genuinely new thing — `app/` — so unzipping it over the
tree would have silently reverted a fortnight of document work:

- its `validation_table.md` was **335 lines against the branch's 429**, and
  contained "seven drives, 113 minutes", retired long ago;
- its `CLAUDE.md` re-introduced **33.9 %**, **"192 samples"** and **1.163**, all
  three of which the branch already had right;
- its `validate.py` dropped explanatory docstrings the branch still carried.

**All three of those figures had already been corrected once, and came back**,
because nothing was asserting them. That is mistake 11 recurring one level up:
a correction that is not guarded by a check has a short half-life. They are now
in `verify_docs.RETIRED`, and adding the guard immediately found a **fourth**
occurrence of 1.163 in `build_dataset.py` that a careful manual pass had missed.

**The rule: a release archive is a snapshot, not an authority.** Diff it against
the tree before applying it, take only what is genuinely new, and re-run
`verify_docs.py` afterwards. Never unzip one over a live branch.

**The same session also caught `verify_docs.py` crashing while reporting.** Its
new document scanner echoes the offending line back, `CHECKPOINT.md` line 54
contains a tick emoji, and on a cp1252 console that raised `UnicodeEncodeError`
and took the whole run down — **after every check had already been computed
correctly**. That is the `build_dataset.py` lambda bug for the third time, in
the one script whose entire job is to be trusted. **A checker that dies while
reporting is worse than one that stays quiet, because the traceback looks like a
data problem and hides the real finding underneath it.** Output is now encoded
defensively.

<!-- RETIRED-OK: 547, 6 -- the warm-filtered count of 16 September -->
<!-- RETIRED-OK: 517 -->
**And a third defect in the same scanner, from the same merge.** Its check
"drives showing that exact ceiling" counted raw files in `logs/raw/`, while the
"547 samples" check sitting beside it counted the warm-filtered dataset. `pull01`
hits the 1020 kg/h ceiling 56 times in its raw log, so the drive count became 6
while the sample count stayed 517 across 5. **Both numbers were true and the
sentence built from them was not.** Both halves now count the same population.
For the record, as written on 16 September (commit `4905498`): **573 pinned samples across 7 of the 10 raw
logs; 517 across 5 once the warm filter has run.** *(Since superseded for the
warm-filtered population: `verify_docs.py` now computes 547 samples across 6
drives.)*


### 18. `Actual gear` CLAMPS AT 6 ON AN EIGHT-SPEED — a fourth misread channel

Found 19 September 2026, while fitting the real gearbox. It is mistakes 2, 7 and
13 in one channel: a name that is not what it says, **and** a range limit that
keeps reporting past it.

The vehicle model ran a generic six-speed with invented ratios until today. The
car has a **ZF 8HP51**, an eight-speed torque-converter automatic, and Toyota
publishes every ratio (REFERENCES.md section 2b). Fitting it raised an obvious
check: the logs carry `Actual gear`, so compare.

**`Actual gear` never exceeds 6, on any drive.** Across 45 606 moving samples
from eight drives it reports 1 to 6 and nothing above. Taken at face value that
says the car is the six-speed manual.

**It is not.** Engine speed and road speed give the overall ratio the car is
actually running, and within the samples the channel labels "gear 6" there are
**three sharp clusters**:

| overall ratio | samples | what it is |
|---|---|---|
| ~2.016 | 19 290 (59.3 %) | **8th** (0.640 x 3.150) |
| ~2.589 | 5 406 (16.6 %) | **7th** (0.822 x 3.150) |
| ~3.15 | 4 833 (14.9 %) | 6th (1.000 x 3.150) |

The channel reports the true gear for 1st to 6th and then **saturates**, calling
7th and 8th "6" as well. Three quarters of the samples it labels top gear are
not in top gear.

**What it would have cost.** Anything scheduled on that channel — a gear-aware
filter, a shift-transient exclusion, a per-gear table — silently pools three
ratios spanning 2.016 to 3.15, a **56 % spread**, under one label. The knock
retard figure in the limitations section is filtered "to steady gear" using it.
That filter still works, because it only asks whether the gear CHANGED, and a
clamped channel still changes at every shift below 6th; but it cannot see a 6-7
or 7-8 shift at all, so the figure includes shift transients it was meant to
remove. **Re-derive it from the inferred gear before quoting the p99 again.**

**The fix is not to repair the channel but to stop needing it.** Overall ratio
from rpm and road speed recovers the true gear directly, and it validates the
ratio set at the same time: **86.7 % of 79 105 moving samples land within 4 % of
one of the eight published ratios.** That is a better measurement than the
channel would have been even if it worked.

**Fourth channel on this car that is not what its name says**, after the
pre-throttle pressure sold as manifold pressure, the MAF that saturates while
still reporting, and the compressor outlet sold as charge temperature. The rule
from mistake 13 now has four instances behind it: **treat every channel name as
a hypothesis, and check the range as well as the meaning.**

*(The tell was available without any of this analysis: the car is an
eight-speed and the channel's maximum is 6. A channel whose maximum equals a
round number that is ALSO a plausible count is the easiest kind of saturation to
miss -- mistake 7's 1020.0 kg/h at least looked like a sensor limit.)*
---

### 19. A FIX THAT READ A KEY NOBODY WROTE — AUDIT.md M12, never working

Found 28 September 2026. M12 asked `generality_test.py` to take the H/τ axis from
the climb's own exhaust flow instead of an assumed 112.5 g/s. The "fix" read
`info.get("mdot")` — a key the environment has never emitted — so the list it
averaged was always empty, and the script fell back to exactly the 112.5 g/s it
was meant to replace, printing "was an assumed 112.5" beside the assumed value.
`AUDIT_FIXES.md` recorded M12 as FIXED for twelve days.

**It is mistake 9's shape — a check that fails OPEN still prints a number.**
`.get(key, default)` on data you produced yourself is a place a bug hides: the
environment now reports `mdot_exh`, and the script indexes it, so a missing key
is an error. **After fixing something, look at what the fix PRINTS and ask
whether the number could have come from the fallback.**

### 20. THE OIL NODE HAD THE WRONG STRUCTURE, AND NO PARAMETER COULD FIX IT

Found 28 September 2026. For three weeks the thermal network heated the oil with
a fixed 5 % of fuel energy and cooled it through a constant 60 W/K, and every
attempt to match the car — halving the share, doubling the capacity, fitting
both on the light-load drives — traded one drive against another ("the drives
pull opposite ways"). They pulled opposite ways because the STRUCTURE was
wrong: tabulated minute by minute, the car runs its oil 11–15 K over coolant at
3700–4800 rpm and 70–100 km/h on moderate fuel, and 2–3 K under coolant at
2600 rpm and 130–140 km/h. Oil heat follows engine speed; the sump is cooled by
road speed. With that structure one parameter set fits 7 drives and
predicts the held-out one (drive10 oil 7.55 → 3.9 K).

**When fits of the same model to different data disagree, suspect the model's
form before its numbers. Tabulate the raw channels against the conditions
first; a parameter search cannot find a mechanism the equation does not have.**

### 21. A DRIVE PLANNED WITHOUT THE CHANNEL EVERY HEAT FLOW NEEDS

Drive B (28 September) was logged exactly to plan — seven channels, 1.05 s per
channel, 41 roll-ons — and the plan had left out `Ambient temperature`. Every
corrected flow, every charge temperature and every heat flow in the thermal
network is referenced to it. `build_dataset.py` then filled the gap SILENTLY
with 25 °C, and the charge-temperature check swallowed drive B's rows and moved
from +1.9 % to +1.0 % on an assumption.

Fixed three ways: the fallback is now a value taken from our own afternoon logs
and every such row is flagged `t_amb_assumed`; the charge-temperature check
excludes flagged rows; and **every channel list in `logs/DRIVE_PLAN.md` now
carries `Ambient temperature`.** A purpose-built drive answers its question only
if it also logs what the question is measured against.

### 22. TWO CLAIMS WRITTEN FROM A LOOK AT A FIGURE, NOT FROM A MEASUREMENT

Found 29 September 2026, while putting the 28 September results on the phone
page, where every figure has to come from a token. Two sentences had shipped in
five documents without a number behind them:

- **"The derived boost ceiling matches drive B at 1400–2400 rpm."** It was read
  off `fig22` as "the model's line sits inside the car's scatter". Inside the
  range is the wrong test for a CEILING: a ceiling is judged against the top of
  what the car did. Against the highest reading per 200 rpm band it is 9–20 %
  LOW at 1600–2000 rpm (193 kPa reached at 1800–2000 rpm where the model allows
  155). Re-pairing engine speed to each boost reading's own moment moved the
  points ~55 rpm and did not change that.
- **"About 6 K of row 8's miss is the coolant."** Never computed. Replaying
  drive10 with the block pinned to the measured coolant (`model_vs_data.
  row8_split`) gives 4.6 K of a 12.0 K miss; the larger share, 7.3 K, is the
  oil node itself.

**The lesson is the page's own rule: a sentence that carries a number needs the
run that printed it.** A figure is evidence for what it plots, not for the
sentence written under it. When a claim is a comparison, say what it is compared
against — "inside the range" and "at the top of the range" are different tests,
and for a limit only the second one means anything.

---

## Known limitations to state in the thesis, not fix quietly

- **Altitude is not modelled.** The scored climb rises 2 340 m in 720 s, but
  `p_baro` is a fixed 101.3 kPa that the plant never reads: compressor inlet,
  boost ceiling and exhaust backpressure all see sea-level air throughout. A
  standard atmosphere would give about 76 kPa at the top, and colder air. The
  scenario is sustained heavy load at sea level — say that, and do not describe
  it as a mountain.
- **The boosted inversion is now within 2 % of the car, and the old 28 % gap
  was the charge temperature, not the breathing model.** See mistake 13. What
  remains uncertain under boost is the MAF ceiling at 1020 kg/h and the logger's
  round-robin sampling, which pairs air mass with pressure taken seconds apart.
- **There is NO part-load test of `volumetric_efficiency()` against this car.**
  Both logged pressure channels sit before the throttle, so there is nothing to
  compare a modelled manifold pressure against at part load. The load residual
  cannot serve — it cancels `eta_v` entirely (mistake 12). State this plainly
  rather than letting the 1.4 % imply coverage it does not have.

- **Peak power is not a prediction.** Manifold pressure is an input.
  `plant.boost_ceiling_kpa` now bounds it to what the car was observed to do,
  but an operating line is not a compressor map — no efficiency islands, no
  speed lines, because the car has no turbo speed sensor and no pre-intercooler
  temperature.
- **Two residuals, both true, and the fitted one fits better.** Over the 26
  pooled points that survive the window checks, 30–75 kPa: **1.4 % with the
  derived k = 0.831 and zero free parameters**, **1.1 % with the fitted
  k = 0.839 and one**. Dropping the parameter makes the residual RISE, which is
  the honest direction — one free parameter should fit better than none. Quote
  the derived 1.4 % and say that it costs nothing; quote the fitted 1.1 % only
  next to the parameter it spends. And read mistake 12 first: neither number
  tests the breathing model.
- **Vehicle validation covers 30–75 kPa only.** Steady points need steady
  driving, and steady driving is light-load driving. The boosted region is
  validated against published correlations.
- **The compressor envelope is unmeasured above 0.314 kg/s corrected**, because
  that is where the MAF channel saturates. The 0.18–0.27 kg/s hole is filled;
  0.33–0.36 is still empty and no drive can fill it with this sensor.
  *(0.303 and 0.314 appear in different sections of `validation_table.md` for
  the same quantity under two different filters — AUDIT.md M5. `fit_envelope.py`
  prints the figure with the filter that produced it.)*
- **THE TOP OF THE ENVELOPE RESTS ON FOUR TO FIVE INDEPENDENT READINGS.** This
  is the sharpest consequence of AUDIT.md H4 and it was invisible while the
  table quoted row counts. `python fit_envelope.py` prints both:

  | flow kg/s | PR p95 | rows | **independent readings** |
  |---|---|---|---|
  | 0.225 | 2.415 | 36 | **5** |
  | 0.255 | 2.342 | 40 | **5** |
  | 0.285 | 2.515 | 53 | **4** |
  | 0.315 | 2.473 | 47 | **5** |

  **"PR 2.52", the number `plant.boost_ceiling_kpa` is built on and every boost
  claim inherits, is four measurements.** The low-flow bins are genuinely dense
  (1120 readings in the first), so the envelope is well determined where it does
  not matter and barely determined where it does. Say so in Chapter 3, and do
  not quote the top bins to three significant figures.
- **Turbine τ is 48.0 s on the climb, and it is ONE measurement, not two.**
  `validate.py` prints 48.0 s, inside the published 40–120 s band.

  This line used to say "`C/UA` gives 50.3 s; the step response gives 48.0 s",
  presenting two methods that nearly agree. **They are the same method.** The
  turbine node is decoupled from the block and oil (`thermal.py`), and
  `validate.py` holds fuel flow, exhaust flow and EGT CONSTANT for the whole
  step, so the response is an exact first-order exponential whose time constant
  IS `C/UA`. Perturbed in mistake 12's style — `c_turb` and `ua_gas_turb` each
  swept over three values — the step-response τ tracks analytic `C/UA` to within
  0.13 s in all nine cells. **The step response cannot corroborate C/UA; it
  recomputes it.** And the 50.3 s was `C/UA` at an exhaust flow of 112.5 g/s,
  the assumed constant `AUDIT.md` M12 condemned.

  **τ is also not one number.** Over the locked episode it runs from 40 to 239 s,
  a factor of six, because UA rises with exhaust flow: 48 s on the climb, 129 s
  on the flat approach. `app/estimator.py`'s table (50 s loaded, 151 s cruise,
  239 s idle) says the same. Quote τ with its operating point, always — that is
  mistake 15. And `c_turb = 6000 J/K` is ASSUMED, so every τ is an assumed
  number to within that constant.

  Corrected 22 September; see `results/PREREGISTRATION.md` limit 8.
  <!-- RETIRED-OK: 50.3, 39.5 -- the superseded figures, named so they are recognised -->
  The old 39.5 s figure came from the four-cylinder and is void.
- **The knock retard is measured, the baseline's cap is the right order, and
  THE PUBLISHED p99 IS UNDER RE-DERIVATION — do not quote it.**
  `Target ignition angle from torque intervention` minus `Actual ignition angle`
  gives the retard the ECU is applying. The figure this section used to state
  as settled was: steady gear (shifts and torque cuts removed, 10 896 samples),
  median 0°, **p99 9.8°**, more than 1° for 22 % of the time and more than 3°
  for 11 %. <!-- RETIRED-OK -->

  **Mistake 18 ordered it re-derived and 19 September did the work.** That
  filter used `Actual gear`, which clamps at 6, so it cannot see a 6→7 or 7→8
  shift and left those transients in. Re-derived from the gear INFERRED from
  rpm and road speed, over `data/master_samples.csv`, retard in [−5°, 45°],
  moving samples only:

  | gear filter | n | p95 | p99 | >1° | >3° |
  |---|---|---|---|---|---|
  | none | 15 780 | 13.50 | 21.75 | 27.4 % | 17.2 % |
  | steady CHANNEL gear | 15 654 | 12.75 | 21.75 | 27.3 % | 17.1 % |
  | **steady INFERRED gear** | **13 329** | **9.75** | **18.00** | **25.5 %** | **15.3 %** |

  The correction removes 2 325 further samples — the 6→7 and 7→8 shifts the
  clamped channel is blind to — and it is **not cosmetic**: p95 falls 12.75 →
  9.75 and p99 falls 21.75 → 18.00.

  **But this does not replace 9.8, because the shipped figure cannot be
  reproduced.** Neither its p99 nor its n = 10 896 comes out of the shipped
  data under a gear-steadiness filter alone, so the torque-cut half of the
  original filter is doing work that is not written down anywhere. Until
  whoever wrote it re-runs it with that filter stated, **the row has no
  quotable p99.**

  *(One hypothesis worth a single check and no more: the re-derived **p95** is
  **9.75**, which rounds to the 9.8 published as a **p99**. That would make the
  original a mislabelled percentile rather than a wrong filter. It is a
  coincidence, not a finding — do not write it down as one.)*

  What survives unchanged: `BaselineECU` caps its knock retard at 12°, which is
  the right order and slightly conservative rather than a strawman, on every
  filter above. **Do not use the raw channel difference** — unfiltered it
  reaches 45°, which is a gearshift torque cut, not knock.
- **The radiator is not identifiable ON THIS CAR, and the census proves it.**
  Every water-pump channel the vehicle offers is all-zero, so there is no
  coolant-flow signal and `Q = ṁ·cp·ΔT` cannot be formed. `Actual value of
  electric fan` and `Duty cycle electric fan` are also all-zero; `Setpoint
  electric fan` is live but sits at 28–31 % for a whole drive. The thermostat
  regulating 88–99 % of the time is the second reason, not the only one.
  `ua_block_oil` **is** identified (800 W/K, from the measured oil-minus-coolant
  gap) and has been changed; the radiator parameters were deliberately left
  alone. See `logs/CHANNEL_CENSUS.md`.

  A constrained fit was attempted on 8 September with 55 minutes at 45 °C
  ambient and far more excitation, and **it fails too**: R² = 0.157 with a
  negative ram coefficient. The only observable is ΔT across the radiator, and
  ΔT = Q/ṁ — both terms rise with road speed, so ΔT carries almost no
  information about UA. Assuming constant flow is not a mild approximation here.
  Stop trying; state it as a limitation.

  **28 September, evening: its SIZE is now derived, its SPLIT is not.** With the
  block's capacity pinned by 683640a0's warm-up, the stretches where the coolant
  climbs above its regulated point carry the radiator's overall size, and
  `derive_params.py` scales the reasoned 300 / 60 / 700 split by one factor
  (x1.42). The three terms still cannot be told apart, and the heat-management
  valve's control law (82-84 C after load on hot afternoons, 97-99 C on
  drive10's high-rpm stretch) is not modelled.
- **THE OIL BAND IS SUPPORTED BY OUR OWN CAR, AND THE MODEL MISSES IT LOW.**
  This is the most valuable thing `drive10` delivered (18 September).
  <!-- RETIRED-OK: 107 -->
  The hottest oil in the first nine drives was 107 °C, *below* the published
  115–140 °C band; `drive10` reaches **117 °C**, with **1320 rows above 110 °C
  and 60 above 115 °C**, so the band's lower end is inside our own measurement.
  Above 117 °C is still extrapolation.

  `validate.py` row 8 replays drive10 and compares model and car over the car's
  hottest ten minutes: **97.0 °C against 103–111 °C**. Row 9 finds the car's oil
  time constant at 70–100 s against the model's 60 s. Both are outside after the
  oil node was re-structured and derived (mistake 20), and the miss is measured,
  not tuned in: of row 8's 12.0 K, 4.6 K is the coolant (the car's
  heat-management valve holds it higher than the model's regulation) and 7.3 K
  is the oil node itself (`model_vs_data.row8_split`). Say it that way in the
  thesis. Drive A, logged with oil AND ambient, is the data that can move it.
- **Eleven drives in the manifest, eight with usable samples.** `3f64372e` and `f51686d7` are under
  a minute each and contain no warm running window; `fb988991` is a census log
  whose windows are all rejected for span or logger gaps (mistake 8), so it
  carries samples but contributes **zero** operating points, and drive B logged
  no spark or lambda, so it adds none either. Quote it as "eleven drives, 321.7
  minutes, eight carrying samples, 26 distinct operating points".

  <!-- RETIRED-OK: 113, 5, 7 -->
  This line read "seven drives, 113 minutes, five carrying samples" until
  9 September. It was written before `7475b5d7` arrived and simply never
  updated, while the current-state table at the top of this file, `verify_docs.py`
  and `build_dataset.py` all moved on. **A limitations section goes stale the
  same way a results section does, and nobody re-reads it.** `verify_docs.py`
  checks the figures in the DOCUMENTS; it does not check the prose in this file.
- **Steady points are steady for fast quantities only.** The 60 s window is
  fully settled for air, lambda, spark and manifold pressure, and reaches just
  **71 %** of a turbine thermal step (τ = 48 s). Never validate a thermal
  quantity at a steady point; drive `thermal.py` over the whole log instead.
- **Enrichment uses dwell above the 180 kPa gate as a proxy** for turbine inlet
  temperature, which this vehicle does not expose. (`ENR_LOAD` = 180 kPa on the
  corrected charge-temperature scale of mistake 13.) **Since 28 September the
  dwell thresholds are derived from the car on the timestamp axis**
  (`derive_params.py`: 1.5 → 3.0 s, were 2 → 9 s on the retired row-count
  axis), and eight of the nine cells are within 0.02 of the car. **The weakest
  cell is 3500–4500 rpm at long dwell, 0.033 lean** — the speed band and depth
  are held at the 8 September fit because ~100 genuine readings cannot identify
  them (REFERENCES.md 4b).
  <!-- RETIRED-OK -->
  *(Until the evening of 28 September the weakest cell was 4500–7000 rpm at
  4–8 s dwell: car 0.83, model 0.906 — 0.076 lean.)*
  <!-- RETIRED-OK -->
  *(Until 27 September this line said the weakest cell was 3500–4500 rpm at
  long dwell and that every cell was within 0.027. The 4500–7000 rpm, 4–8 s cell
  had been tabulated at 0.87 on the row-count dwell axis AUDIT.md H3 retired,
  and was never regenerated. `ENR_DWELL_LO/HI` were fitted on that axis too and
  are NOT refitted: the cell holds a few dozen independent readings at most.
  It does not touch Phase D — the locked climb runs 178 kPa at 2706 rpm and
  enrichment needs 180 kPa and 3300 rpm.)*
  <!-- RETIRED-OK -->
  *(This line read "short dwell, n=29, observed 0.94, model 1.00" until
  9 September — the seven-drive
  version, in which that cell held only 29 samples and read 0.94 by chance.
  `base_lambda()`'s docstring had the corrected cell all along.)*
- **AND ON THE LOCKED SCENARIO THE BASELINE NEVER ENRICHES AT ALL.** Measured
  19 September 2026, neutral policy, 12 % at 130 km/h, 42 °C, 720 s:
  **λ = 1.000 on every single step of the episode.** This is not a defect and
  it is not the gate: the climb sits at **2706 rpm** (7th gear), and
  `base_lambda` returns 1.000 there at **any** load and **any** dwell —
  178 kPa or 220 kPa, 0 s or 30 s, all 1.000. The first enrichment appears at
  3600 rpm. That is the map being faithful to the car, which mistake 4 records
  as not enriching below about 3300 rpm however long boost is held.

  **Say this in Chapter 4, because it changes what the ablation measures.**
  Enrichment is one of the four protection levers and one of the five actions
  the agent controls (action 1, λ trim, down to −0.15 → λ 0.85). On this
  scenario **the production-representative baseline does not use it and the
  agent can**, so part of any margin the agent shows is a lever the ECU would
  not have pulled here — not anticipation. The ablation is sighted-against-
  blinded and both agents hold that same lever, so it does not corrupt the
  preview comparison; it does inflate every "cuts damage N %" figure quoted
  against the baseline.

  The other protection paths ARE live on this scenario and were checked the
  same run: thermostat open 0.20 → 0.70 and never shut (~100 kW rejected),
  cooling fan on its 0.4 rung for 97.4 % of the climb, coolant pump at 1.0,
  charge cooler taking 42 °C ambient to 56.9 °C, knock retard peaking at 3.2°
  and active 3.8 % of the time.
- **The eleven validation bands are engineering-judgement bands, not sourced
  ones.** `validate.py` scores the model against eleven "published" ranges,
  and until 12 September the only citation behind any of them was the word
  "Heywood" in a code comment. `REFERENCES.md` now records, row by row, which
  bands have been checked against an opened source and which have not, and
  sorts them into general engine physics (a textbook settles them), facts
  specific to the B58 (only BMW or Toyota documentation can), and one band
  with no support at all: the knock-limited spark, row 4. Until a row is
  marked CONFIRMED there, describe its band in the thesis as engineering
  judgement. Never promote a row from memory; open the source and write down
  the page.
- **`c_turb` = 6000 J/K is ASSUMED, not measured, and it sets τ.** The
  turbine-housing heat capacity (how much heat it takes to warm the housing
  by one degree) divided by its heat-transfer coefficient (how fast heat gets
  in and out) is the housing's time constant τ, and τ is the denominator of
  H/τ, the project's whole claim. `generality_test.py` sweeps `c_turb` from
  800 to 60 000 J/K, a factor of 75, on purpose: the claim is about the RATIO
  H/τ, not about one engine's heat capacity, so if preview value collapses
  onto one curve across that sweep the exact value of `c_turb` does not
  matter. State this explicitly in Chapter 3. Unstated, it reads as an
  unexamined assumption; stated, it is the reason the experiment is designed
  the way it is. See `REFERENCES.md` section 4.
- **The B58 has no thermostat, so the 88 °C in `thermal.py` is a modelling
  equivalent.** BMW's own B58 training document (ST1505, 2015, section 4.2)
  says the conventional thermostat "is replaced by a so-called heat management
  module": a motor-driven rotary valve positioned by the engine computer from
  the coolant and cylinder-head temperatures, with no wax element and no
  published opening temperature. `t_stat_open` = 88 °C is identified from the
  car's own coolant channel (regulated 88–97 °C in every log) and cannot be
  cited to BMW. It is also a third reason the radiator cannot be identified
  from the logs: the radiator branch opening is a commanded valve angle, not a
  function of coolant temperature. See `REFERENCES.md` section 2.
- **The compression ratio question is SETTLED: this is the 285 kW car, so
  10.2:1 is right.** Confirmed by the team on 19 September 2026 — the car is the
  285 kW / ~386 hp B58B30O1, which is the engine every manufacturer sheet prints
  10.2:1 beside, and which is what `plant.py` runs. The 11.0:1 that Toyota UK's
  sheets print belongs to the **250 kW / 340 PS** European variant and does not
  apply here.

  <!-- RETIRED-OK -->
  This entry read "Nobody has yet recorded which version this car is" until
  19 September, and warned that if it were the 250 kW car the knock model would
  be running the wrong compression ratio. It is not, and the knock model's
  compression ratio is correct. **That does not rescue the knock model** — see
  the section below: its integral still has no detectable relationship with the
  car's own retard, and now that the compression ratio is excluded as the
  explanation, the remaining candidates are the Douaud-Eyzat tuning, the charge
  temperature or pressure under boost, or the assumption that `Actual ignition
  angle` is the final commanded angle. **Excluding a suspect is progress; it is
  not a fix.**


### THE KNOCK MODEL IS NOT VALIDATED AGAINST THIS CAR, AND THE DATA SAYS SO

Added 16 September 2026, from AUDIT.md H5. This is a negative result and it is
worth more than most of the positive ones.

The car publishes its own knock response: `Target ignition angle from torque
intervention` minus `Actual ignition angle` is the retard the ECU is applying.
Replaying `7475b5d7` through the app -- which feeds the car's MEASURED spark and
lambda into `predict()` -- gives a model knock integral to compare against it,
sample for sample. Over 13 592 paired samples:

| | model knock integral | car's own retard |
|---|---|---|
| median | 0.464 | 0.00 deg |
| p95 | 0.732 | 6.75 deg |
| max | 3.446 | 44.25 deg |
| active | KI > 0.85 on **1.6 %** | retard > 1 deg on **25.5 %** |

**Correlation between them: −0.149.** Where the model says the engine is
knocking, the car's median retard is 0 deg. Where the model says it is not, the
car's median retard is also 0 deg. **The two have no detectable relationship.**

**What that costs, stated rather than hidden:**

- `validate.py`'s knock-limited-spark row (11 deg at 3000 rpm / 200 kPa) is
  inside a band that REFERENCES.md already marks unsourced, and it is now also
  unsupported by the car's own behaviour. It still counts toward the literature rows' 6 of 7.
- `BaselineECU.knock_limited_spark` and the `40·max(0, KI − 0.85)²` term in the
  damage function rest on the same model.
- `check_map.py`'s entire knock-limited surface is model-internal.

**Do not quote a knock-limited spark or a knock damage term as calibrated.** One
of three things is wrong and the data here cannot say which: the Douaud-Eyzat
integral is mis-tuned for this engine, the modelled charge temperature or
inverted pressure are off under boost, or `Actual ignition angle` is not the
final commanded angle. Settling it needs a deliberate drive, not another
re-analysis of these logs.

**Why this did not show up before:** the premise numbers never exercised the
knock term, because the baseline was over-retarded by the scheduling error of
AUDIT.md C2 and sat at KI 0.3-0.4. Fixing C2 is what made the term live.

**28 September: this test could not have seen knock, so it is UNTESTED, not
refuted.** Counting genuine readings (AUDIT.md H4) instead of rows: the drive
holds **404 target and 410 actual ignition readings in 55 minutes**, one every
~8 s, and a third of the pairs in a row were read more than a second apart. A
knock retard lasts a second or two, so most were never sampled, and the ones
that were are paired with the wrong moment. Filtering to steady inferred gear
does not rescue it — above 120 kPa only 106 rows even have an inferable gear,
because engine speed and road speed were themselves read seconds apart. This is
mistake 13b exactly: the compressor-outlet hypothesis read +0.35 on slow data
and +0.95 once `pull01` logged 7 channels. The table above stands as a
measurement of THIS drive; it is not evidence against Douaud-Eyzat.

**What it costs Phase D, measured.** On the hand-written policies the knock
term is **6.4 % of the baseline's damage and 11–12 % of the protecting
policies'**, and it is all of preview's −0.4 against current-grade: on turbine
and oil damage alone the two tie. Report both until drive C settles it.

### Limits the LIVE APP adds, and they are the simulator's limits plus three

The app reuses `plant.predict`, `plant.map_from_airflow`,
`plant.charge_temperature` and `thermal.ThermalNetwork` **unchanged**, so every
limitation above applies to it word for word. It adds these:

- **The turbine temperature it displays is a model output, not a reading, and
  its heat capacity is an ASSUMED number.** `c_turb = 6000 J/K` is marked
  ASSUMED in `thermal.py` and in REFERENCES.md section 4, and it is the constant
  that sets τ, which is the denominator of this project's central ratio. The UI
  says so on every screen and the thesis must too. **A number on a dashboard
  looks like a measurement to everyone who did not write it.**
- **The warm-start bound holds under steady operation only.** Connect within a
  few tens of seconds of lifting off a hard pull and the housing can be hotter
  than the gas now flowing through it, so the upper bound is too low. There is
  no channel on this car that would catch it. See mistake 15.
- **The mismatch detector only has an opinion at wide-open throttle.** Below a
  pressure ratio of 1.8 the two quantities it compares sit on opposite sides of
  the throttle plate (mistake 14), so it is silent there — which means **a boost
  leak on a car that is never driven hard will not be found by it.** That is a
  coverage limit, not a bug, and it is the honest consequence of the only
  pressure channels this vehicle publishes being pre-throttle.
- **The alert counts are not evidence.** 14 thermal / 0 mismatch / 19 novel on
  `7475b5d7` is a property of thresholds this project chose, pinned so that a
  regression is visible. It is not a measurement of the car.

### THE 14 SEPTEMBER AUDIT FOUND SIX BUGS IN `app/` THAT ITS OWN TESTS PASSED — ALL SIX NOW FIXED

`AUDIT.md` is a full technical review of this branch. **Read it before quoting
anything the app prints.** It was the most important document of its week, and
it disagreed with the confident tone of the section above.

Six of its findings were against `app/`, and the app's own suite reported 46 of
46 while every one of them was live. That is the point worth internalising: **a test
suite pins the behaviour it was written to pin, and cannot see a defect nobody
thought to look for.** The same lesson as mistake 11, one more level down.

| id | what | why it matters |
|---|---|---|
| **H8** | the modelled-lambda fallback can never enrich — `base_lambda` is called without `dwell_s`, so λ = 1.00 always | the modelled EGT runs **80–110 K hot** under a sustained pull, and that feeds the DRIVER-FACING thermal alerts. This is the worst of the six |
| **M11** | the block node free-runs although coolant is measured every sample | drifts **14 K** from the sensor on `7475b5d7`, and the oil node inherits it |
| **M10** | the thermal warning projects the trend LINEARLY 30 s ahead | the housing is a first-order node with τ 27–51 s, so it reaches 61–75 % of that. Five of ten warns on `7475b5d7` project to the limit but fall **20–110 K short** of it in the model's own dynamics. "Threshold in about N s" is a quantitative claim the model contradicts |
| **M9** | one missed barometric reading retires the mismatch detector for the session | `_last_poll` is advanced before the query rather than after, so a single NO DATA silences the detector 7–15 s later |
| **M8** | BimmerLink's placeholder zeros are parsed as measurements | the first rows of every log read coolant 0, so the seed can start the block at 273 K |
| **M7** | nothing in the test suite imports `app/server.py` | "36 of 36 pass" therefore says nothing about whether the product starts |

**ALL SIX ARE NOW FIXED**, and `AUDIT_FIXES.md` carries a row per finding
saying what moved.

Verified by running the suite, not by reading the response document: it reports
**49 of 49** (three new regressions over the old 46), and five of the six carry a
test named after the finding — `H8: the modelled lambda reaches 0.81 after a
sustained pull`, `M11: the modelled block equals the measured coolant`,
`M10: no time-to-threshold when the limit is unreachable`, `M8: leading coolant
zeros are not read as 0 C`, `M7: app.server imports and serves its three pages`.
**M9 is the exception**: it is fixed in `app/reader.py` (the comments at `:530`
and `:581` name it) but carries no test of its own, so it is the one of the six
that could silently regress.

<!-- RETIRED-OK: 890.6, 608.0 -- the app pins of 17 September; 873.1 and 604.8 on the merged physics -->
**What moved on 17 September, and it was small:** `7475b5d7`'s peak estimated
turbine went to **890.6 °C** from the 884.9 °C of mistake 15, and `pull01`'s to
**608.0 °C** from 593.7. Both rises were the H1 crank-angle correction, not the
app fixes — see `AUDIT_FIXES.md`. Since the merge the pins have moved again,
with the exhaust-flow fix: the Numbers section has the current ones.

**The lesson the section title still carries is the one worth keeping:** the
suite reported 46 of 46 while all six defects were live. **A test suite pins the
behaviour it was written to pin.** Every fix above ships with a regression test
that would have failed before it, which is the only reason the count went up.

**Three of the audit's CRITICAL findings are about the simulator, not the app,
and they matter more than anything in this section** — in particular C3, which
argues the 13.4-point preview advantage is protection depth and that the
ablation identity is guaranteed by construction. That goes to the project's
central claim.

**C3 IS NOW ADDRESSED, and the answer is a null.** C3's demand was precisely a
trained blinded agent raced against a trained sighted one, and that ran on
21–22 September: eight paired seeds, preregistered before any agent started.
**Preview is not significant** — 5 of 8 positive, mean +4.8 damage units, sign
test p = 0.3633, permutation p = 0.4922. The blinded agents were trained blind
rather than zeroed at evaluation, so the comparison could have failed, and
across eight pairs it did not separate from seed noise.

C1 and C2 remain where they were.
---

## Repository layout

```
plant.py              0-D cycle model. predict() is the shared interface.
thermal.py            3-node lumped-capacitance thermal network.
engine_env.py         Gymnasium env. BaselineECU lives here. make_grade_climb is
                      the LOCKED scoring road; make_terrain / TerrainTrainingEnv
                      are the training roads, never used for scoring.
check_roads.py        Drives the baseline over sampled training roads; fails if
                      any is one the baseline cannot drive. Run before training.
evaluate.py           Phase D's protocol. Twenty frozen episodes. Never edit them.
                      Reports damage two ways since 28 Sep (total, thermal-only).
derive_params.py      Every constant the car's logs can set, recomputed from
                      them -> data/derived_params.json. build_dataset.py runs it.
derived.py            The ONE reader of data/derived_params.json. No fallback:
                      if the file is missing it says which command makes it.
calibrate_thermal.py  The thermal block + oil fit (and its structure), with
                      leave-one-drive-out scores. derive_params.py calls it.
car_thermal.py        thermal.py replayed over a logged drive, on measured fuel;
                      raw_grid() reads a whole raw log, warm-up included.
run_results.py        Regenerates results/traces_130kmh.json, sweep_speed_grade
                      .json and the Phase D files from the current plant.
compare_calibration.py  The 28 Sep before/after comparisons, for figures 20-25.
model_vs_data.py      Eleven comparisons of the simulator against the car.
make_figures.py       Thesis figures, results/figures/, from results/*.json.
make_page.py          The phone-readable results page, results/page/index.html,
                      from results/page/template.html. Numbers are tokens.
validate.py           Regenerates the published-figure validation table.
build_dataset.py      All drives -> data/manifest, master_points, master_samples.
extract_steady.py     Steady points from one CSV (build_dataset supersedes it).
compare_log.py        Model vs measurement at steady points.
check_map.py          MBT and knock-limited spark surfaces.
check_premise.py      Reactive vs predictive, hand-written. The premise check.
test_reward.py        Phase C sanity checks. Run after ANY reward change.
verify_docs.py        Recomputes the published figures from the shipped data,
                      then OPENS every tracked .md and .py and compares what it
                      finds written there against those figures, and against a
                      list of retired ones. Fails naming file and line. Run it
                      before quoting anything. Never edit its expected values.
train.py              SAC training, three designs: terrain (dt 1.0, a new road
                      every episode, runs/terrain_dt1/), fixed and random
                      (dt 0.2; runs/, runs_d2/, runs_c4/ are CLOSED). Writes
                      meta.json -- the plant fingerprint -- before the first
                      step and refuses a resume whose plant, dt, device or
                      budget differs; also config.json and train_record.npz
                      (EVERY training action; gitignored).
train_all.py          Every seed of both halves, one process each (10 seeds x
                      sighted/blinded = 20 runs by default).
record_agents.py      Scores agents on the twenty frozen episodes, recording
                      EVERY step (action, applied actuators, observation,
                      engine state), and documents each in results/agents/
                      <set>/<tag>/: config, curve, policy weights, records,
                      summary; README.md, index.json and figures per set.
knock_margin.py       The same agents with spark advance forbidden -- how much
                      of their gain rests on the untested knock model.
evaluate.py           The twenty frozen episodes. Prints the fingerprint from
                      the LIVE objects, writes it into the result file, and
                      REFUSES a model whose meta.json differs.
fingerprint.py        What plant produced this result. The fatal hash is over
                      the CODE with docstrings stripped, so the document sweep
                      cannot invalidate a trained agent; read its docstring
                      before touching it.
run_phase_d.py        Launches the sixteen runs, and the eight evaluations,
                      capped by MEASURED free memory. Cores say how many runs
                      can make progress; memory says how many can START.
analyse_phase_d.py    The preregistered statistic and nothing else. Does not
                      drop a seed, add a seed, or switch tails.
analyse_phase_d2.py   Phase D2's preregistered test -- Phase D's statistic,
                      IMPORTED not copied, plus the three-cell MEI rule (PREVIEW
                      HELPS / SMALLER THAN THE MEI / INCONCLUSIVE). Prints both
                      experiments side by side, Phase D's labelled post-hoc.
analyse_c4.py         C4's preregistered test -- D2's statistic, IMPORTED, plus
                      a certificate first: it refuses any agent that is not a
                      fresh 300 000-step run, read from the ZIP (fingerprint.
                      model_budget), because meta.json cannot tell C4 from D2.
check_c4_convergence.py  Had the C4 agents settled? Checkpoints 200k/250k/300k
                      on ten PRACTICE episodes, never the test set. The rule
                      was set by the team before any C4 agent trained.
check_c4_start.py     Run ~15 and ~80 min into C4: certificates, budgets, and
                      whether each C4 run retraces its D2 twin bit for bit.
power_analysis.py     What effect size eight seeds can detect, from Phase D's
                      measured spread. Nothing re-measured; the arithmetic is
                      the contribution.
random_road.py        Phase D2's randomised climb, as a WRAPPER. engine_env.py
                      is untouched on purpose -- editing it would move
                      plant_sha and lock out all sixteen Phase D agents.
                      (The merge of 30 Sep moved plant_sha anyway: every
                      Phase D, D2 and C4 agent is refused on the merged
                      plant; re-run them from tag sep17-before-merge.)
check_random_road.py  Does every D2 road bind, and is the blind arm blind.
                      Run before training; about 38 minutes.
prove_buffer.py       Proves the replay-buffer size changes nothing learned.
drift_test.py         The guard's own acceptance test: inject AUDIT2 Part 4a's
                      drifts and check each is CAUGHT. Currently 16 of 16.
full_run.py           Every script that prints a published figure, in one pass,
                      each block opening with its EXIT CODE -> FULL_RUN.txt.
                      Sweep the documents from that, not from memory.
plot_sim_vs_car.py    The simulator against the car's logs: five charts, each
                      labelled INDEPENDENT CHECK, FIT or CONSISTENCY CHECK, into
                      figures/sim_vs_car/ (SVG, PNG, a printable PDF, a web
                      page). SVG + headless Chrome, because Application Control
                      blocks matplotlib on Jad's machine. The web page is
                      published privately; its URL is in the docstring --
                      update that page, never publish a second one.
plot_agent_pairs.py   Phase D, D2 and C4 pair by pair: every agent a dot, every
                      verdict quoted by app/agent_catalog.py, nothing computed.
                      figures/agent_pairs/; its page is published the same way.
plot_study_page.py    The whole study on one page (summary, the ablations, every
                      policy, fuel, the roads, the simulator against the car,
                      the drives, the caveats), built from this branch's
                      results/. figures/study/; published the same way.
results/PREREGISTRATION.md  Phase D's rules, committed before any agent trained.
results/PREREGISTRATION_D2.md  Phase D2's rules, committed before any D2 agent
                      trained -- MEI set, power declared, ten limits, run log.
results/NEXT_EXPERIMENT_DESIGN.md  Why the climb is randomised the way it is.
results/PREREGISTRATION_C4.md  C4's rules -- D2's design at 300 000 steps, one
                      variable at a time -- committed before any C4 agent
                      trained: convergence rule, crash rule, six readings.
runs_d2/              Phase D2's trained agents. Gitignored, like runs/.
runs_c4/              C4's trained agents. Gitignored. A NEW budget always
                      gets its own directory: train.py refuses to resume a run
                      whose --steps differs (see its "A RESUME IS NOT A LONGER
                      RUN"), and run_phase_d.py never relaunches over final.zip.
results/void/         Result files that are NOT results, with a README saying
                      why. The +11.7 file lives here.
generality_test.py    The H/τ experiment. H1, H2, H2b.
README.md             The public-facing summary. Tracked by verify_docs.py.
CLAUDE.md             This file. The handoff and the mistake log.
handoff.md            The short entry point: what to run, what it prints today.
NEXT_SESSION_*.md     The prompt for the next session, one per session, dated.
                      Read its first lines for SUPERSEDED before pasting it.
SESSION_REPORT_*.md   One per session, dated. The newest date is the latest.
REFERENCES.md         Where every number we did not measure comes from. Written
                      for a non-specialist. Read before quoting a published band.
DOCUMENT_STATUS.md    Which team PDFs still carry void numbers, and why.
AUDIT.md              Full technical review, 14 Sep. THREE CRITICAL findings
                      against the headline claim and six against app/.
                      Read it before quoting any number in this file.
team/                 ONE PROFILE PER PERSON. Ask who you are talking to,
                      then read theirs before explaining anything.
  README.md           how the matching works and how to add yourself.
  _TEMPLATE.md        copy this.
logs/CHANNEL_SET_FINAL.md   What is recorded, what to add, and why.
logs/CHANNEL_CENSUS.md      All 656 channels the car offers, live vs dead.
logs/DRIVE_PLAN.md          The three drives that would settle what the logs
                            cannot: channels, and how to drive each one.
logs/raw/*.csv        Raw BimmerLink exports. Never edit these.
data/*.csv            Generated. Never edit by hand — re-run build_dataset.py.
data/derived_params.json  Generated by derive_params.py. Never edit by hand.
validation_table.md   Chapter 3's evidence. Regenerate after touching the plant.
app/                  THE LIVE SUPERVISOR. Runs this same physics alongside
                      the car in real time and estimates what it cannot report.
  estimator.py        The virtual sensor. Read its docstring before touching it.
  reader.py           OBD-II, or replay of the logs above. Channel budget here.
  alerts.py           thermal / mismatch / novel. The ONLY file that writes.
  server.py           localhost. /, /driver, /review; --simulation adds the 3D
                      replay lab and the agents page, with no vehicle connection.
  static/*.html       dashboard, driver mode, review view.
  test_replay.py      Replay-driven regression checks. Run after any app change.
  agent_api.py        The agent replay (--simulation only): trained agents on
                      finished episodes, and the hidden models panel.
  jev.py              Calls an external service: the model jev (api.typesafe.ai),
                      one paid call per press. Its key is read per call or held
                      in memory, and never logged, returned or written. Nothing
                      in it reaches the car.
  laya_bridge.py      Laya, a local model, run offline in its own interpreter
                      (laya_worker.py); no key.
  model_questions.py  The one question both models are asked. Their answers are
                      shown, never applied.
  review_log.jsonl    Generated, gitignored. Marked events only, never raw data.
```

**Two rules the app adds, and they are structural, not stylistic.** It never
transmits to the vehicle (the hard constraint above, in code), and it never
writes raw car data to disk -- only what the model marks. `app/test_replay.py`
asserts both, so breaking either fails a check rather than going unnoticed.


---

## Conventions

- **Never edit `data/` or `validation_table.md` by hand.** Regenerate them.
- **Run `verify_docs.py` before quoting a number in the thesis.** It recomputes
  the published figures from the shipped data, then opens every tracked `.md`
  and `.py` and compares what is written there against them, and against the
  list of figures this project has retired. It prints its own totals — read
  them off the run rather than quoting a count from here, because the count
  moves whenever a figure is added. It exists because figures had already
  drifted, mostly for the same reason: one computed on ONE drive and then quoted
  as if it were pooled. On 11 September it found 55 of them in one pass.
- **Never edit `logs/raw/`.** Those are measurements.
- After changing `plant.py` or `thermal.py`, re-run `validate.py` and update
  `validation_table.md` **in the same commit**.
- After changing the reward or the env, re-run `test_reward.py` and paste the
  output into the commit message.
- Change one thing, re-run, write down what happened. Two changes at once and
  you no longer know which one did it.
- Report numbers with the condition attached. "1.4 % load residual over 26
  points, 30–75 kPa" — not "the model is accurate".
- **After changing anything under `app/`, re-run `python -m app.test_replay`
  and paste the output into the commit message.** The app's numbers are a chain
  — reader, estimator, alert engine — and a change anywhere moves numbers
  everywhere without announcing it. Use `--full` before a release.
- **A threshold in `app/` changes only for a measurement, and the measurement
  goes in the docstring beside the number.** This is not decoration: the 15 %
  that became 25 % was justified for weeks by a residual that could not bound
  it (mistakes 12 and 14), and the docstring is where that was finally caught.
- **Never unzip a release archive over the working tree.** Diff it first and
  take only what is genuinely new. See mistake 16 — the v19 archive would have
  reverted a fortnight of document work, and it carried one file nobody else
  had.
- **Say which drive population you mean.** Eleven in the manifest, eight carrying
  samples, eight behind the fitted calibrations. All three are correct and they
  are not interchangeable.

---

## When a new drive CSV arrives

This is the routine, and it is the most likely reason someone opens this repo.

```bash
cp <new>.csv logs/raw/<descriptive-name>.csv
python new_drive.py logs/raw/<descriptive-name>.csv   # what did it buy?
python build_dataset.py "logs/raw/*.csv"     # rebuilds the data AND re-derives the plant
python compare_log.py data/master_points.csv # re-scores the model
python validate.py; python check_premise.py; python test_reward.py; python check_roads.py
python verify_docs.py                        # fails if anything quotes the old plant
```

**Since 28 September a new drive CHANGES THE SIMULATOR**: `build_dataset.py`
runs `derive_params.py`, which re-derives every constant the logs can set. That
is the point — nothing is frozen at one day's fit — and it means a drive added
after the Phase D retrain invalidates the trained agents. **The team's plan
(29 September): retrain after every drive — but not before the five steps Jad
and Ghassan agreed on 30 September** (the box at the top, and the live list
under "What to do next"). Until those land and the new preregistration is
committed, a new drive is re-derived and re-scored, not trained on. After that:
`python check_roads.py`, then `python train_all.py` (~4 h), then
`python record_agents.py runs/terrain_dt1`, `python run_results.py phase_d` and
`python knock_margin.py`. Move the previous `runs/terrain_dt1/` aside first:
train.py RESUMES any checkpoint it finds there.
Channel names are matched case-insensitively (exports differ). A drive with no
`Ambient temperature` channel gets `build_dataset.AMB_FALLBACK_C`, flagged.

Then check, in this order:

1. **Did the sanity floor or the fuel-cut filter drop anything?** Both print.
2. **Did the operating-point count go up?** If the new drive added zero distinct
   points, it was not steady enough — that is a driving problem, not a code one.
3. **Which compressor flow bins are still empty?** It prints them. Only
   0.33–0.36 kg/s remains, and the MAF sensor cannot reach it.
4. **Does the load residual stay near 1.4 %?** If it jumps, the new drive covers
   a region the model has not seen, which is information, not failure.
5. **Did any window get rejected for span or a logger gap?** It prints both. A
   drive that loses every window that way was logged with too many channels
   selected — see mistake 8.
6. **Did the new drive push any channel to a flat maximum?** See mistake 7.

If the drive changes a calibration — lambda, spark, the boost ceiling — **check
how many samples support the change, and check that the variable you are fitting
against actually correlates.** See mistakes 4 and 6.

---

## Open, and honest about it

### PHASE D, D2 AND C4 WERE SCORED IN A DISCRETISATION THEY DID NOT LEARN IN. Measured 19 Sep

`dt` was not consistent across this project until 27 September. Ghassan logged
it as an open question on 19 September; this measures it.

```
train.py         dt = 0.2   duration 900 s   ->  4500 steps per episode
evaluate.py      dt = 1.0   duration 720 s   ->   720 steps per episode
check_premise    dt = 1.0
generality_test  dt = 2.0
```

**The preview horizon is NOT the problem** — `_preview()` computes
`int(h / self.dt)`, so the 2/5/15/30 s horizons are the same wall-clock
horizons at every `dt`. That was checked first, because H is the numerator of
this project's central ratio.

**The damage integral IS.** Hand-written policies, locked scenario, 720 s,
identical seed and weights, the only difference being the step:

<!-- RETIRED-OK: 900.9 -->
| policy | dt = 1.0 | dt = 0.2 | cuts vs baseline |
|---|---|---|---|
| baseline ECU | 959.8 | 900.9 | — |
| current-grade | 633.2 | 567.8 | **34.0 % → 37.0 %** |
| reactive | 679.0 | 622.5 | **29.3 % → 30.9 %** |

Peak turbine is **dt-invariant** — 884.0 °C at both steps, 860.5 for
current-grade at both — and fuel moves 0.2 %. The physics is not in question.
The accumulated damage is, and so is everything computed from it.

**The sharpest form: the GAP between two fixed policies moves from 4.8 to 6.1
points, 1.3 points, on the step size alone.** Every preview effect this project
has measured with hand-written policies is between 0.4 and 2.3 points.
**`dt` sits inside the signal, not underneath it.**

The cause is one loop. `_track_torque`'s PI accumulates per STEP with no `dt` in
it, so it advances five times per second at 0.2 and once at 1.0. This is the
same defect AUDIT.md M16 fixed for `SLEW`, in the loop M16 did not touch.

**What this does and does not do to the ablation.** In Phase D, D2 and C4 the
sighted and the blinded agent both trained at 0.2 and were scored at 1.0, so the
handicap is shared and
is not a bias by construction. Whether it is SYMMETRIC is unmeasured, and there
is a reason to doubt it: a policy whose entire value is timing may lose more to
a coarser step than one with no preview at all. **Quote no ablation figure
without this paragraph beside it**, and note that the hand-written comparators
are unaffected — they have no `dt`, they are functions of the current state.

Three ways out were listed: train at 1.0 to match the protocol; score at 0.2 to
match the training; or leave it and state it as a limitation. **The team chose
the first on 27 September:** `train.py` passes dt = 1.0 for the terrain design
(`runs/terrain_dt1/`), so the 29 September agents and every run after them learn
in the step they are scored in. For Phase D, D2 and C4 this section stays a
stated limitation — written down rather than discovered by an examiner.

**Phase F's H2b threshold rule does not survive the correct engine.** It sets
the constraint at the 80th percentile of the unprotected trace, which assumes
the temperature spends a minority of the episode near its peak. The standard
scenario is a sustained climb: nine of its twelve minutes sit at the top, so p80
lands on the peak and the top three rows of the sweep saturate at 100 % for both
policies.

`check_premise.py` hit the same wall and solved it by anchoring the trigger to
the **damage model** instead — 1123 K, the knee of `exp((t_turb − 1123)/45)`,
above which damage stops being negligible. That is a statement about the
component rather than about one episode, and it transfers between scenarios.
**`generality_test.py` now imports the same constant** —
`engine_env.TURB_PROTECT_K` — so the two experiments cannot report different
protection limits. Until H2b's percentile rule is replaced, use the fixed-limit
H2 table — but **those figures are void too** (AUDIT.md C1: the whole sweep was
scored against the same cooling-disabled baseline, and M12: the τ axis assumed
112.5 g/s of exhaust where the climb makes about 103, so every τ was ~7 % low).
Re-run `generality_test.py` and read what it prints.

Those numbers were 0.0 / 0.1 / 0.2 at the old 930 K trigger. **Nothing about the
plant changed — only the threshold.** Report the threshold with every preview
figure; a preview advantage quoted without the limit it was measured against is
not a result.

---

## What to do next, in order

> **THE LIVE LIST — 30 September 2026, after the merge. Agreed by Jad and Ghassan**
> (`conflict.md` section 0 and Ghassan's reply). Before ANY training, in this order:
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

## Tone note for whoever writes the thesis

This project's advantage is that almost every number came out of running
something. Two calibrations have been corrected against measurement, one
hypothesis has been refuted and reported, and the validation table states what
it does *not* cover. Keep that. An examiner trusts a student who reports against
themselves, and punishes a validation table that implies coverage it lacks.
