# Decisions for Ghassan and Jad, open on 8 October 2026

One sheet for every decision that is still open, each with the option
recommended and why. **Answer each line in your own column: *agree*, or what to
change.** When both columns of a decision are filled, Ghassan commits the
answers *before* anything that depends on them is computed: the labels, the
next preregistration, the next training. A required accuracy, a damage
constant or a test set chosen after seeing the results is the tuning this
project has refused since mistake 12.

> **8 October: X1 went ahead before both columns were filled, on Ghassan's
> order** ("add more seeds and retrain"). `results/PREREGISTRATION_X1.md`
> section 9 lists the recommended options it adopts provisionally (5, 8–13) and
> what a different answer would cost: a scoring decision is re-applied from the
> per-step records without retraining; decision 12 is the training itself, so a
> different answer to it is a new experiment. The columns below are still yours
> to fill; nothing here was filled for anyone.

Where each decision comes from:

> **21 October 2026: every decision on this sheet is answered.** Ghassan: "me and Jad agreed
> with what you decided", and, asked whether that covers decisions 1-13 too, "yes, covers
> everything". Both columns of 1-35 are filled (Jad's as reported by Ghassan). Where a later
> decision revises an earlier one, the later one governs: 33 (the knee per engine) over 9, and
> 29 and 34 (the training mix and the test roads) over the scored climb of 12.

- 1–7: `results/VALIDATION_PLAN.md` section 10, unchanged since Jad's review of
  7 October (section 12 there says how each of his eight points was taken).
- 8–10: `results/DAMAGE_CONSTANTS.md` (`python damage_constants.py`), 7–8 October.
- 11: the per-step records (`step_record.py`), 8 October.
- 12–13: `results/VALIDATION_PLAN.md` section 11 (`python conditions_test.py`),
  inputs to decision 7.
- 14–23 (added 19 October): drive C's decision rule, `results/DRIVE_C_RULE.md`
  (`python drive_c_rule_numbers.py`). **Answered 19 October: Jad and Ghassan agree
  to all ten** (Jad's answer as reported by Ghassan), before any retard was
  computed on a drive C file. Drive C is repeated once the rule's analysis script
  is committed.
- 24 (added 20 October, on branch `GRA-test`): the plants, four engines
  (section F). **Answered 21 October: both agree** (Jad's answer as reported by
  Ghassan).
- 25–35 (added 20 October, on branch `GRA-test`; 27, 32 and 34 revised on 21
  October): how the four-engine test trains (section F, second table).
  **Answered 21 October: Jad and Ghassan agree to every recommendation** (Jad's
  answer as reported by Ghassan), before any agent of the four-engine test
  trained.

## A. The validation plan

| # | decision | recommended | Ghassan | Jad |
|---|---|---|---|---|
| 1 | Standards | ASME V&V 20 for the comparisons; **NASA-STD-7009B** for the risk side (free, current, citable now); cite V&V 20's method through the OSTI overview and Oberkampf and Roy until the library has it | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 2 | Contexts of use | the four of section 3; COU-4 (the app) outside the thesis claim | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 3 | Required accuracies | R1 turbine-equivalent ≤ 10 K; R2 oil ≤ 20 K; R3 withdrawn; R4 waits for the app | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 4 | Label rules | section 7's rules in the order excluded, not covered, off, untested, validated, limited; k = 2 | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 5 | Relative damage only | agree, and restate the minimum effect of interest as 5.43 % of the baseline's damage (5.43 points of cut) | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 6 | Extrapolation | every COU-1 and COU-3 result labelled an extrapolation **in duration**: the operating point is in the data, the twelve-minute hold is not | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 7 | Preregistration | fold the plan, and decisions 8–13, into the next preregistration, so they are fixed before the next training | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |

## B. The damage formula

Two of its seven constants can be calculated once a mechanism is named; one is
bracketed by published limits; the knock knee waits for drive C; the weights are
valuations. Under every calculated value all twenty agents still beat
current-grade, and the ablation stays inconclusive unless the knock term is made
large (`DAMAGE_CONSTANTS.md`).

| # | decision | options | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|---|
| 8 | The turbine scale (45 K) | (a) keep 45 K, stated as oxidation-like (it is Q = 233 kJ/mol); (b) **20.3 K**, calculated for creep rupture (Larson–Miller, C = 20, 19.5–21.2 K over 10³–10⁵ h); (c) a thermo-mechanical-fatigue formula counted per heat-up cycle (new work) | **(a) for the next training, with (b) pre-declared as a sensitivity row.** One change at a time: the agreed steps (sub-stepping, spark cap, ramps) already change the experiment, and keeping 45 K keeps every earlier result comparable. Re-scoring under 20.3 K costs seconds from the per-step records. Name the mechanism in Chapter 3 either way | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 9 | What the turbine knee (850 °C housing) means | as a gas temperature at the climb's operating point it is 984 °C. Published limits carried to the housing: 900 °C load-spectrum parameter → 778 °C; Conway's 930 °C → 804 °C; the 1050 °C cast-steel rating → 907 °C | **Keep 850 °C** (it sits between Conway's limit and the cast-steel rating), **pre-declare 804 °C and 907 °C as sensitivity rows, and keep the no-knock column agreed on 30 September.** Moving the knee also moves the hand-written trigger, so it is a protocol change | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 10 | The oil scale (12 K) | (a) keep 12 K; (b) 14.4 K from the 10 °C doubling rule | **(a).** The rule is a rule of thumb shown not to be universal, and the oil term is 0.9–2.4 % of the damage on the climb: 14.4 K moves no cut by more than 0.5 points | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |

## C. The records

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 11 | Where the per-step records live | **Keep them out of git (the rule of 29 September) and back them up outside the repository after every run, sha-checked, as `runs_c4/` was** (`GRAD-agent-backups/<date>/`). They now hold every step of training (44 fields from the next run on; the twenty of 29 September completed by `training_roads.py`), the frozen episodes, the knock margin and the conditions test: 188 MB on Ghassan's laptop (training 53 MB and its regenerated roads 18 MB, the frozen episodes 28 MB, the knock margin 26 MB, the conditions test 63 MB), plus 70 MB of copies of the training records beside each agent, and the only copy | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |

## D. Inputs from the conditions test to decision 7

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 12 | Where the next agents train, and where they are checked | **As said on 7 October: train on the extremes the car never reached, so the agent knows them; check the trained agent on the states we have logs for, so we know it trained correctly.** *Train*: ambient drawn per episode over 25–45 °C, a speed target that changes mid-run (60–150 km/h), hills up to 18 %, and thin air once the plant reads pressure (a plant change, so a new fingerprint). *Check, on states we have*: the logged drives replayed through the simulator with their own speed and ambient, where the simulator is validated against the car; there the agent must deliver the torque asked for, burn no more fuel than the baseline, and not protect where the car never needed it (no logged drive reaches the trigger). The logs carry no road grade: either replay them flat, or rebuild the grade from the car's own air mass, which leans on the unidentified mass and drag area. *Transfer*: hold out 50 °C and the hills of 18–22 % as a test the agents never trained on. The locked climb's twenty frozen episodes stay the protocol. Why: the conditions test shows agents trained in one air fail outside it (at 25 °C on a 21.75 % hill 6 of 20 beat current-grade, and in thin air their torque delivery breaks down), and 98 % of their training was in 7th and 8th gear on nothing steeper than 14 %. Cost: wider training spreads the seeds, so the ablation may need more of them. **Three safeguards, because the extremes are where the simulator is least trusted:** (1) cap every lever whose physics is untested (the spark cap of 30 September) and draw the uncertain constants per episode too (the turbine housing's heat capacity, the knock threshold, the damage scale), so an agent cannot learn one wrong model value; (2) the logged drives can show the agent does no harm, not that it protects correctly, since none of them reaches the trigger: add physical sanity checks at the extremes (a hotter housing must never get less protection) and let drives A and C widen the region the simulator is validated in; (3) keep the held-out conditions unseen until the final test, and never tune on them | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 13 | The yardstick | **Make current-grade's torque shortfall a gate in the preregistration**: count its steps under 95 % of the requested torque on the new test set before any agent is scored; if it is short, report the shortfall beside every margin over it (or make it pull boost only within the tracking tolerance, decided before training). On the conditions test's speed profile it was short for 122–303 steps of 719 in four of seven conditions | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |

**An input from the per-step records, to 7 and 12 (not a decision of its own):**
blinded seed 6's failures, on the five frozen episodes that weight life least
and at 25 °C in the conditions test, are one behaviour: a hard spark retard,
which costs it fuel and life together (CLAUDE.md mistake 24). It is not for want
of training on low life weights: 124 of the 560 training episodes (22 %) weighted
life as low as its bad frozen episodes. It was described as a reward trade until
the records were read. A
preregistration that reports each agent's worst episode against the baseline,
not only its median, catches it.

## E. Drive C's decision rule (added 19 October 2026)

Proposed in Ghassan's session from blind research (no drive C log read, no
retard computed on any log); the full rule, its definitions and its disclosure
are `results/DRIVE_C_RULE.md`, and every number is printed by
`python drive_c_rule_numbers.py`. Drive C was first driven on 18–19 October,
before these numbers existed, and covered neither part. **Answered on
19 October: both agree to every recommendation below**, before anyone computed
target minus actual on any drive C log.

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 14 | C2: what counts as a load step (draft: air mass +50 % between two readings) | **Air above 1.2× its 20-s median, reaching 1.5× within one more reading and holding it for two more (+25 kg/h at least), from a steady light cruise (M ≤ 100 kg/h), held gear, warm engine, the target polled right after the actual; counted only where the model's own spike for that step exceeds KI 1.0** (rule section 3, V1–V8). The bare +50 % fires 1.6–1.8 times a minute in cruise; the KI 1.0 gate tests exactly the steps where the model predicts a pull | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 15 | C2: the windows and the pairing (draft: 3 s after against the 20 s before) | **Baseline = lower median of the 20 s before (within ±0.75°). Only the late window decides: t1 + 1 s to t1 + 5 s, ending 0.6 s before the pedal is released. Retard = min(target before, target after) − actual.** The first second is where pairing can manufacture a pull and where pre-emptive and torque-deficit retards sit; a knock-control retard lasts into the late window | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 16 | C2: what counts as pulling timing (draft: a rise of more than 2°) | **A late-window maximum of (retard − baseline) ≥ 2.25°, three counts of the 0.75° grid; above 12° the step is unreadable.** One Bosch knock event is 3°, its first recovery level 2.25°; light-cruise jitter reaches 2.25° on 1.3 % of readings and never 3° | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 17 | C2: the verdict (draft: does not < 1 in 5, does > 1 in 2) | **Cuts computed at freeze from the realised blocks (jitter 0.075, miss rate 0.45, ICC 0.1, each error ≤ 5 %); at 24 steps: pulls if ≥ 6 and more often than sham windows (Fisher, 5 %); does not if ≤ 3, the channel check passes and the baseline-excluded steps cannot overturn it; 4–5 inconclusive.** The logged actual angle is most likely one cylinder at a time, so about 45 % of one-cylinder pulls are missed; the draft's cuts would leave a car pulling on 60 % of steps inconclusive about half the time | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 18 | C2: the fewest valid steps (draft: none) | **16 valid steps; below that untested and not analysed. Plan 35 steps in 5 blocks of 7, 5 min apart, plus 8–10 min of step-free cruise for 40 sham windows. One analysis, after the repeat, pooling every drive C file.** At 16 steps both errors stay under 5 %; steps driven with no break count as one block and need far stricter cuts | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 19 | C2: the ambient the verdict covers (new) | **Only the logged range of the valid steps; neither verdict extends to hotter air; 42 °C stays untested.** The ECU's intake-temperature compensation sits inside the target channel, so the uncompensated knock sensitivity does not carry | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 20 | C2: half and full pedal (new) | **Drive the split (about 20 full, 15 half), keep one pooled verdict; large against moderate steps is a non-binding secondary (Fisher, 43–51 % power).** Step size cannot separate knock from a tip-in retard: knock, torque deficit and pairing artefacts all grow with it, and drivability retard cancels in target − actual. Timing and the C1 comparison separate them | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 21 | C1: the knee (draft: no trigger) | **Requirement 0.10 KI; retune the damage knee only if \|median onset KI − 0.85\| > max(0.10, 2·u_val), the median from confirmed onsets by an interval-censored estimator over all segments, u_input 0.032 KI; untested below 8 confirmed onsets; limited if the two rpm halves differ by more than 0.10. The model ECU's own 1.0 threshold is compared too, and moving it is a separate, later step.** A knee of 0.75 makes the baseline's climb knock damage ×3.93, 0.95 makes it ×0.15 | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 22 | C1: the spark in the climb's cell (draft: no trigger) | **Requirement 0.85° (not the plan's 1.3°): retune the boosted schedule only if \|E\| > max(0.85°, 2·u_val), E the mean of per-segment medians, u_input √(u_al² + 0.86²); at least 15 segments with 5 in-cell readings each (plan 25–30 × 10). An action rule, separate from the label.** −0.85° of schedule for every car is +9.95 K and ×1.248 damage on the locked climb, which is R1's own basis; 1.3° is the one-car trim conversion. In practice a retune needs \|E\| ≳ 1.7°, the resolution the model's charge temperature allows | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |
| 23 | What each verdict triggers, and the guards (new) | **Does not → schedule the baseline's spark on the current load. Pulls, but no more often than steady C1 running at the same load → the same remedy. Pulls and step-specific → keep a load-step knock cost sized with C1's knee. Only the first second pulls → current-load spark plus at most a 1-s protective retard. Drive C files stay out of `logs/raw`; `new_drive.py` withholds the retard; one blind count (stage A), a hash-frozen list, one analysis.** A late pull may be the car's steady knock limit, which is C1's question, not the step's | agree, 19 Oct | agree, 19 Oct (as reported by Ghassan) |

## F. The plants: four engines (added 20 October 2026, on branch `GRA-test`)

Ghassan's session, 20 October. The criterion says preview value falls on one
curve against H/τ *whatever the plant*, and one engine gives one point. Public
data that can set an engine's maps exist for three turbocharged gasoline
engines besides the B58: the US EPA's engine benchmarking test data packages
(steady-state map with turbine-inlet temperature, spark, lambda and boost, plus
high-load holds that show the ECU's protection) and Argonne's Downloadable
Dynamometer Database (10 Hz chassis-dyno driving data). The search is in
Ghassan's session report of 20 October.

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 24 | The plants of the H/τ test | **Four engines, each in its own car: the B58 (GR Supra, our logs); the Mazda 2.5 L turbo (2016 CX-9: EPA map, and Argonne driving data of the same car); the Honda 1.5 L turbo (EPA's L15B7 map, in the 2018 Accord body, whose Argonne driving data has a sibling 1.5 L turbo); the Ford 2.7 L twin-turbo V6 (2015 F-150: EPA map, no driving data). Built on branch `GRA-test`, off `main` at `cf43fbb`; `main`'s plant stays X1's so drive C's stage C can run, and the B58's drives continue. Nothing trains until both columns are filled and a preregistration names the engines, the collapse test and what it holds fixed.** The Mazda is the only engine with a map and driving data of the same engine; the Honda protects by deep enrichment at a low turbine-inlet temperature, the Ford by holding it near a fixed cap, so the engines differ where the criterion is tested. What it costs: no public source logs a turbine housing over time, so every engine's housing τ is assumed, as the B58's is; every agent is retrained, because the plant's fingerprint changes; and it adds scope against the team's 23 November end | agree, 20 Oct (four engines, `GRA-test`, each in its own car) | agree, 21 Oct (as reported by Ghassan) |

**How the four-engine test trains (decisions 25–35, added 20 October).** From a
research pass of the same day (Ghassan's session report of 20 October): the
project's own X1/X2 results, the literature on seeds and on SAC, timings on the
team laptop, and two reviews against the rules above. What it measured:
84–94 % of the variance of a seed pair's difference is seed to seed and pairing
removes none of it (the two arms' correlation is −0.14 in X1, +0.09 in X2);
twenty evaluation episodes are enough; X2's hot training cut stopped rising
after about 400–500 episodes (post hoc; X2's own preregistered check found no
convergence); a tabulated B58 trains 6–8 times faster per run, with every
frozen-twenty cut within 1.5 points of the exact plant; at today's spread one
comparison needs 143 seeds a side by the sign test, 90 by a paired t-test.

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 25 | When the four-engine training may start | **After drive C: repeat it, run stages A–C on `main`, then merge `GRA-test` into `main` (re-certifying the B58 if stage C retunes it) and train from `main`. Latest start 4 November; if stage C has not run by 1 November, both of you amend rule 2 in writing for this test only ("the commit the preregistration names"), disclosed in the preregistration.** Rule 2 needs `main`'s `train.py` and `fingerprint.py`, both change on `GRA-test`, and `main` must stay X1's plant until stage C; gate item 6 also puts drive C first | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 26 | Verdicts | **One verdict per engine per horizon, never pooled; the collapse is tested on the per-engine estimates as a cross-plant comparison declared in advance (do the engines differ, and are they equivalent). A pooled value only as a declared secondary.** Rule 5 makes each engine its own plant, and a pooled verdict would assume the collapse it tests | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 27 | Arms per engine (revised 21 October) | **Three: blinded, and sighted at two horizons taken from the test roads' preview ceiling (decision 34), up to about the time constant of the approach to a climb (about 130 s on the B58's flat), matched in H/τ across engines. H becomes a FATAL fingerprint field, and the blind-arm check runs for every H.** With one shared housing the four τ cluster at about 39–60 s (estimated), and one horizon cannot tell H/τ from τ; the proposal's evaluation asks for a second horizon. *The first version capped H at 150 s because the locked climb starts at 180 s; decision 34 no longer makes the locked climb the test road* | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 28 | Training and scoring backend | **Train on each engine's table only if it passes accuracy gates derived from the MEI (fixed before the table is built for a new engine); score every reported agent on the exact cycle model; record the training and the scoring backend as separate fingerprint fields.** The table is 6–8× faster per run (measured on a loaded machine, one process; its rate with many runs at once is not measured), but an agent trained on it could exploit its error | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 29 | Training recipe | **450 000 steps (500 episodes); the scored kind of road (12 % at 130 km/h, 42 °C) as a fixed share of training episodes (10 %); learning rate falling linearly to 0 over the last third; the reported policy is the action average of the checkpoints in the last 50 000 steps, declared in advance; the twenty frozen episodes unchanged. Before preregistering, a short pilot of the recipe on `main`'s plant into a new `--out`, read on practice episodes only.** X2's collapses sit in the scored corner its training drew on 1–2 % of episodes; constant-rate training kept wandering; averaging halved X2's checkpoint-to-checkpoint pair swings | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 30 | Seeds and test | **A paired t-test, one-sided, primary; the exact sign test a declared secondary; alpha split over engines and horizons; seeds per arm fixed before training from the measured many-run rate and the time window (target at least 20), with no interim looks; no seed added after the result.** The t-test needs about 0.63× the sign test's seeds; X1's and X2's distributions were seen before this choice, which the preregistration must say | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 31 | Which B58 the test uses | **X1's plant (`cf43fbb`), frozen for this test; new drives enter the B58 only after scoring; the four-engine B58 is a new experiment, never compared with X1/X2 as one. The Supra's road load from EPA's test-car data (ours is 15–22 % low) is not in this test; a declared ablation later.** Change one thing at a time; the B58 arm already differs from X1 in steps, recipe and horizons | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 32 | Python and the training device (revised 21 October twice: training runs on another device, Ghassan; CPU or GPU decided there by a benchmark) | **Amend rule 4 to "the exact versions the training device records in `meta.json`", pinned by a committed lock file (`requirements-lock.txt`, or its own if the benchmark picks a CUDA build). Before any training, on the training device: its versions match that lock (`check_training_device.py`); seed 0 trains the identical agent twice (`benchmark_training.py`, section 4); the B58 identity certificate is re-run there. Whether it also matches the team laptop bit for bit (`check_training_device.py --compare`) is recorded, not required. CPU or GPU is chosen there by `benchmark_training.py`, once, for every seed, arm and engine (rule 3).** X1 and X2 trained on Python 3.13.2 (their `config.json`) and the laptop has no 3.12. CPU and CUDA train different agents from one seed (`train.py`), and a different processor can round the last bit of vectorised maths differently even with identical software, so identity across machines cannot be the condition; one device for the whole experiment can | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 33 | The damage knee per engine | **Each engine's knee is set so its baseline spends as long above the knee on its locked climb as the B58's baseline does above 1123 K, computed on each calibrated plant before any agent trains; 850 °C for every engine as a sensitivity row re-scored from the records.** With the B58's housing-to-gas ratio, the hottest EPA turbine-inlet gas puts the three housings near 720–780 °C, under the 850 °C knee (an estimate, to recompute per engine) | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 34 | The test roads (revised 21 October; it read "the locked climb per car") | **Not the locked climb. Roads on which preview can be worth something: repeated short, hot climbs of about 1–2 τ each, chosen so that the preview ceiling (the most any use of the preview could save, from a current-grade trace, printed by a committed script) is at least twice the MEI on every engine; computed and committed before the preregistration; the locked climb kept only as a declared transfer row; the twenty frozen preference draws reused on the new roads.** Measured on 21 October (`python preview_ceiling.py` → `results/preview_ceiling.txt`, from the committed traces): on the locked climb the most a cooler housing at the climb start can save is 0.13 points of cut with the agent's own levers, 0.42 with unlimited preview, 1.19 even if the exhaust could be held at ambient for the 30 s, against the MEI of 5.43, because about 92 % of the turbine damage accrues more than 3 τ after the climb starts, when both arms know the same thing (on the ramped plant the knock term adds well under a point). Every engine would read about 0 there, and a collapse at zero tests nothing. Gate item 5 already named multi-climb roads as the test set. The preregistration must say that this was found after X1's and X2's results, from hand-written traces, not from any agent of the new test | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |
| 35 | Validation thresholds for the new engines | **Torque, fuel and turbine-inlet temperature against held-out EPA points, with each required accuracy derived from its consequence on the MEI (VALIDATION_PLAN.md's method) and committed before calibrating; the table gates likewise.** The first draft's thresholds equalled the B58 table's own measured errors, which is choosing R to fit E | agree, 21 Oct | agree, 21 Oct (as reported by Ghassan) |

## G. Before the three EPA engines are calibrated (added 21 October 2026, on branch `GRA-test`)

From the validation contract of decision 35 (`results/ENGINE_THRESHOLDS.md`, section 8),
written and reviewed before any engine was fitted. Ghassan delegated these on 21 October
("fix all the way you see fit"); the recommended option is adopted so that the contract can be
committed before calibration, as X1 went ahead on Ghassan's order on 8 October. Jad's column is
open; an answer that differs, given before the first fit, is applied before it.

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 36 | A validation row that can only read "untested" | **It enters the result as a preregistered error band, ((\|E\| + 2u)/R)·b, and the engine's verdict inside that band reads "model-limited"; a row with no statistic at all still drops the engine.** The ECU's boosted enrichment moves the head-start pair at first order (±0.02 of lambda: −16 % / −42 % under K3), and EPA's uncalibrated lambda cannot resolve that on any engine, the B58 included: if "untested" dropped the engine, no engine would survive | delegated 21 Oct ("fix all the way you see fit"): adopted | |
| 37 | The equivalence margin of the collapse test (decision 26) | **The MEI, 5.43 points.** It has a consequence behind it (decision 5); a margin chosen for what the seed budget can confirm is choosing R to fit E (the review of 20 October). At about 20 seeds per arm the test can refute a collapse but will rarely confirm one within the MEI, and the preregistration says so | delegated 21 Oct: adopted | |
| 38 | The model-error budget per part | **b = MEI/6 = 0.905 points per part, for six parts**, so the six aligned at their limits add to exactly the MEI (with MEI/5 they would add to 1.2 MEI, enough to manufacture an effect of the size the test looks for); every d-row R scales by 5/6; independent, they add to about 0.41 MEI | delegated 21 Oct: adopted | |

## H. Building the three EPA engines: build step 2 (added 22 October 2026, on branch `GRA-test`)

From the build-step-2 plan, `docs/build_step_2/PLAN.md`, and its review, `docs/build_step_2/AMENDMENTS.md`, whose
section 3 these are; where the two differ the amendments govern. Five readers mapped the contract and the code,
three independent designs were each reviewed adversarially, the plan was synthesized from them, and five more
reviewers checked it against the files (21-22 October). Ghassan delegated on 21 October ("fix all the way you see
fit"), and the recommended option of each is adopted under that delegation, so that the plant changes and the
scripts can be written; nothing in them fits a model. **The first fit (Run 1) waits for both columns.** Jad's
answers, and any different answer of Ghassan's, given before it, are applied before it: in the code, and through
contract version 4 where a decision is a rule of the contract (rule 0, `results/ENGINE_THRESHOLDS.md`, permits
that only before the first fit). Decision 66 of the plan was dropped by the review: it is a procedure, not a
choice.

*Before the plant changes (group 1).*

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 39 | Contract version 4, generated after the plant commit and before any script that names the EPA tables | **Yes, version 4.** Two of version 3's rules cannot be applied as written: C5's threshold "SHIFT_LOAD·T_wot" is not the one the gearbox applies (`engine_env.py:507-510`), and "the neutral action must reproduce the baseline exactly" holds on no engine, the B58 included, because the agent's trims are float32. Its rule text: (a) E8 computed in-sample and reported, but outside the cycle-form criterion, since only the ECU fit moves it; (b) the neutral action's identity on the λ and spark channels at float32, with no clip touching, checked on every locked climb and test road; (c) C5's threshold by decision 70; (d) decisions 49, 54, 55, 59's counting rule, 64 and 71 as rules; (e) the code citations moved to the new lines. A different answer of Jad's to 36-38 goes into it as well | delegated 21 Oct: adopted | |
| 40 | The Accord's ratio law (a CVT) | **A stateless kickdown law: hold the top ratio while the demand is at most 0.75 of the deliverable torque (ASSUMED); otherwise the lowest engine speed whose demand is at most 0.65 of it (DESIGN).** C5 then reads as the margin to that kickdown threshold, the law's one discrete decision. An economy line would put the demand exactly on its own threshold, and the Accord climbs on the power-limited branch, where the clause first drafted fails every step. Disclosed: 0.75 and 0.65 are points of the D3 strand's in-sample grid, and no gated row uses them | delegated 21 Oct: adopted | |
| 41 | Form D's cam | **Run by the ECU**, as the contract writes it: a schedule cam(rpm, MAP) the baseline ECU computes and every policy inherits, as it inherits the spark | delegated 21 Oct: adopted | |
| 42 | Car conventions | **Mass = EPA's equivalent test weight; road force (A + B·v)·cos θ + C·v²·ρ/ρ_ref + m·g·sin θ, ρ_ref at EPA's 98.21 kPa and 20 °C; the wheel radius from EPA's N/V and axle ratio, never from D3; η 0.92.** Each identity holds against its source to round-off. Disclosed: the CX-9's 4.41 against the published 4.411 (2.3e-4) | delegated 21 Oct: adopted | |
| 43 | Gearbox constants and the CX-9's peak torque | **The Supra's shift constants, ASSUMED and carried; the CX-9's peak torque from Mazda's published sheet, opened and recorded before the plant commit**; never from D3. Only if no published source prints it, a DERIVED value from the calibration High Load Initial rows | delegated 21 Oct: adopted | |
| 44 | The locked climb for each car | **12 %, 130 km/h and 42 °C for every car, the K3 knee set on that trace, and the delivery reported**: the tracking error over t ≥ 188 s, the gear or ratio, the rpm, the margins to the kickdown and rpm bars, and the knee also at η 0.86 and 0.98. The F-150 climbs in 3rd at η 0.92 and holds 4th from η 0.946, reported as gear-sensitive. A climb at the highest delivered speed stays the declared remedy | delegated 21 Oct: adopted | |
| 45 | B58 constants the EPA rigs cannot set (thermal network, ECU compensations, knock feedback, fan, housing) | **Typed in each EPA spec as ASSUMED, marked "CARRIED FROM THE B58" with the source, and tested against the B58's values** (derived_sha 326c0835548975e2) | delegated 21 Oct: adopted | |
| 46 | The load loop's gains | **Scaled by displacement** (`ff_kpa_per_nm` and `p_gain` × 1.2048 Mazda, 2.0028 Honda, 1.1125 Ford; DESIGN); the other loop fields carried unscaled; checked by the tracking test | delegated 21 Oct: adopted | |
| 47 | Training and scoring | **Refuse the EPA engines in `train.py`, `train_all.py`, `run_phase_d.py` and `evaluate.py` until schema 4 and a committed validation exist** (`engines.trainable()`), with a refusal test per entry point | delegated 21 Oct: adopted | |
| 48 | Re-runs at commits that touch only EPA files | **The full physics re-run list and the app suites**, as `.claude/rules/physics.md`'s paths require | delegated 21 Oct: adopted | |
| 61 | Where calibration and validation run | **This laptop's venv (Python 3.13.2, `requirements-lock.txt`), with SciPy pinned in `requirements.txt`.** The frozen-plant dump is re-made on the training device and the comparison recorded; the certificate's training level L8 runs on the device | delegated 21 Oct: adopted | |
| 67 | Old hashes after the plant commit (mistake 11) | **Grep and update every mention; the build-step-1 certificate page moves verbatim to `STATE_HISTORY.md`.** Hashes are not figures, so `verify_docs.RETIRED` is not used | delegated 21 Oct: adopted | |
| 68 | CLAUDE.md's re-run rule | **Name `engines.py` and `engine_specs/` in it**, as `.claude/rules/physics.md` does | delegated 21 Oct: adopted | |
| 69 | The Ford's fuel in use | **HD1's batch (FTAG 26864: AFR_st 14.559, 42.908 MJ/kg)**, the high-load cell; calibration rows still run on their own table's fuel, and Cell 9's batch (14.557) is reported as a variant | delegated 21 Oct: adopted | |
| 72 (added 22 Oct, the review of build step 2 P6) | The Mazda's stroke | **DERIVED_ONCE, 99.98 mm, from EPA's 2.488 L and its 89 mm bore, as `engine_specs/mazda_25t.toml` types it now**, so the plant displaces what EPA's map package states (PLAN.md 9.2). The other option is PUBLISHED, 100 mm: Mazda's 2019 CX-9 sheet (MZ19, opened 22 October 2026, PDF pages 2, 8, 14 and 21) prints "BORE X STROKE (MM) 89 x 100" and "DISPLACEMENT (CC) 2488", and 100 mm displaces 2.48846 L. The plan's reason, "EPA asserts no stroke", was written before MZ19 was opened; the two strokes differ by 0.018 %. The conrod follows the stroke (the B58's rod ratio), and both are frozen with the plant commit, commit A (amendment B5): an answer is applied before that commit, or the typed value stands | delegated 21 Oct: adopted | |

*Before version 4's text (group 2).*

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 49 | One model form for the three EPA engines, or one each | **One each** (the plan's draft had one for all three). The ridge is about 10⁴ times too weak to hold unneeded terms neutral, and the contract's "one model form" is the B58's cycle, calibrated per engine. Each engine's form and residual structure are reported (mistake 20) | delegated 21 Oct: adopted | |
| 54 | Rows without λ, the −120 spark sentinel, the Honda's λ floor | **A fired row without λ runs at λ 1.00, flagged, and every statistic is also reported without it. Sentinel rows enter no fit; in every statistic they run at the model ECU's spark, flagged, and are also reported without. "Censored" is defined on the calibration Final rows themselves.** Declared outcomes, never a stop | delegated 21 Oct: adopted | |
| 55 | An in-sample statistic with no calibration line | **Neither blocks nor passes; recorded per form** | delegated 21 Oct: adopted | |
| 57 | Statistic details | **As the plan states**; D1 with unreachable rows counted at the bound gates in-sample | delegated 21 Oct: adopted | |
| 58 | Held-out rows outside the calibration MAP range | **Flagged per row and reported restricted to the calibration coverage beside it; never relabelled** | delegated 21 Oct: adopted | |
| 59 | E6 readings | **As amended**: a refit row reports how far the model in use moves; row 9 takes the bracket, then the probe, then ±10 CAD, and includes the rich slope; the Tests lists are counted by a fixed rule; E8 is never excluded | delegated 21 Oct: adopted | |
| 64 | C5 against the held-out E1a | **Roads drawn at 1.9 %; after the validation, the scored climbs re-checked at max(1.9 %, \|E1a\| + 2u_val) and failures redrawn from a seed stream committed with the roads, with a cap on redraws; a car with no passing climb is reported as gear-sensitive, not dropped** | delegated 21 Oct: adopted | |
| 65 | Waive the tightenings to validate sooner? | **No**: the roads and the L1 and E8 tightenings come before the held-out run | delegated 21 Oct: adopted | |
| 70 | C5's threshold in the code | **`Vehicle.shift_ceiling_nm(rpm)`, the threshold the gearbox applies, at the held gear and every rejected higher gear; for the CVT, decision 40's kickdown threshold** | delegated 21 Oct: adopted | |
| 71 | L1's tightening: which plant | **The B58, on decision 34's roads**, as E8's tightening. An EPA engine's slope would let its own coefficients move its R after its fit | delegated 21 Oct: adopted | |

*Before the calibration scripts are committed (group 3).*

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 50 | The estimator | **The plan's section 5 as amended**: staged fits, residuals scaled by each row's R, a declared ridge (w = 0.01) toward the B58's values, `scipy.optimize.least_squares('trf')` from three starts, declared outcomes for a bound hit and non-convergence, no constant held | delegated 21 Oct: adopted | |
| 51 | The knock scale | **The geometric mean of the knock integral over the calibration Final rows set to 1**, the least-squares reading of "KI = 1 at the High Load Final spark"; E6 row 7's ±10 % are then exact rescalings | delegated 21 Oct: adopted | |
| 52 | Turbine-inlet pressure below the barometer | **Keep the rows, report their count and size, and refit without them as a sensitivity.** Excluding them selects on the outcome | delegated 21 Oct: adopted | |
| 53 | The boost envelope; HD1's barometer | **One point per calibration high-load line from its Final rows, anchored, flat past the last point; HD1's barometer the median of the Cell 9 calibration rows, swept over their range** | delegated 21 Oct: adopted | |
| 56 | Uncertainty terms | **The plan's section 6.2, every input resolution pinned as a number before the scripts are committed; EPA's instrument pages opened first and recorded** | delegated 21 Oct: adopted | |
| 60 | Computing the held-out statistics once | **As amended**: an armed commit; refusals in a linked worktree, a copy or a non-empty output folder; a STARTED record and crash records; the defect route (no refit, limited at best) | delegated 21 Oct: adopted | |
| 62 | The Ford's TIT-cap row | **An ECU variant outside the frozen form, enriching by the least amount that holds the model's TIT at or below a cap; the cap's rule fixed before the scripts are committed: the highest TIT on the Ford's calibration Final rows, or the 1223 K EGT limit** | delegated 21 Oct: adopted | |
| 63 | C3's and C4's inputs the contract does not pin | **Hashed at the arming against the data folder's `MANIFEST.csv`; `d3_rows.py` tested on synthetic traces only** | delegated 21 Oct: adopted | |

## What is already settled and needs no answer

- The five steps before any training, agreed on 30 September (`CLAUDE.md`, first
  box): sub-step the thermal network, fingerprint the derived constants, cap the
  spark trim, ramp every grade change, a new preregistration. Drive C before
  drive A.
- Recording does not change results: an agent trained with the new recorder is
  the agent trained without it (600 steps, largest weight difference 0.0), and
  every recorded episode equals its committed score.
