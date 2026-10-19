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

## A. The validation plan

| # | decision | recommended | Ghassan | Jad |
|---|---|---|---|---|
| 1 | Standards | ASME V&V 20 for the comparisons; **NASA-STD-7009B** for the risk side (free, current, citable now); cite V&V 20's method through the OSTI overview and Oberkampf and Roy until the library has it | | |
| 2 | Contexts of use | the four of section 3; COU-4 (the app) outside the thesis claim | | |
| 3 | Required accuracies | R1 turbine-equivalent ≤ 10 K; R2 oil ≤ 20 K; R3 withdrawn; R4 waits for the app | | |
| 4 | Label rules | section 7's rules in the order excluded, not covered, off, untested, validated, limited; k = 2 | | |
| 5 | Relative damage only | agree, and restate the minimum effect of interest as 5.43 % of the baseline's damage (5.43 points of cut) | | |
| 6 | Extrapolation | every COU-1 and COU-3 result labelled an extrapolation **in duration**: the operating point is in the data, the twelve-minute hold is not | | |
| 7 | Preregistration | fold the plan, and decisions 8–13, into the next preregistration, so they are fixed before the next training | | |

## B. The damage formula

Two of its seven constants can be calculated once a mechanism is named; one is
bracketed by published limits; the knock knee waits for drive C; the weights are
valuations. Under every calculated value all twenty agents still beat
current-grade, and the ablation stays inconclusive unless the knock term is made
large (`DAMAGE_CONSTANTS.md`).

| # | decision | options | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|---|
| 8 | The turbine scale (45 K) | (a) keep 45 K, stated as oxidation-like (it is Q = 233 kJ/mol); (b) **20.3 K**, calculated for creep rupture (Larson–Miller, C = 20, 19.5–21.2 K over 10³–10⁵ h); (c) a thermo-mechanical-fatigue formula counted per heat-up cycle (new work) | **(a) for the next training, with (b) pre-declared as a sensitivity row.** One change at a time: the agreed steps (sub-stepping, spark cap, ramps) already change the experiment, and keeping 45 K keeps every earlier result comparable. Re-scoring under 20.3 K costs seconds from the per-step records. Name the mechanism in Chapter 3 either way | | |
| 9 | What the turbine knee (850 °C housing) means | as a gas temperature at the climb's operating point it is 984 °C. Published limits carried to the housing: 900 °C load-spectrum parameter → 778 °C; Conway's 930 °C → 804 °C; the 1050 °C cast-steel rating → 907 °C | **Keep 850 °C** (it sits between Conway's limit and the cast-steel rating), **pre-declare 804 °C and 907 °C as sensitivity rows, and keep the no-knock column agreed on 30 September.** Moving the knee also moves the hand-written trigger, so it is a protocol change | | |
| 10 | The oil scale (12 K) | (a) keep 12 K; (b) 14.4 K from the 10 °C doubling rule | **(a).** The rule is a rule of thumb shown not to be universal, and the oil term is 0.9–2.4 % of the damage on the climb: 14.4 K moves no cut by more than 0.5 points | | |

## C. The records

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 11 | Where the per-step records live | **Keep them out of git (the rule of 29 September) and back them up outside the repository after every run, sha-checked, as `runs_c4/` was** (`GRAD-agent-backups/<date>/`). They now hold every step of training (44 fields from the next run on; the twenty of 29 September completed by `training_roads.py`), the frozen episodes, the knock margin and the conditions test: 188 MB on Ghassan's laptop (training 53 MB and its regenerated roads 18 MB, the frozen episodes 28 MB, the knock margin 26 MB, the conditions test 63 MB), plus 70 MB of copies of the training records beside each agent, and the only copy | | |

## D. Inputs from the conditions test to decision 7

| # | decision | recommended, and why | Ghassan | Jad |
|---|---|---|---|---|
| 12 | Where the next agents train, and where they are checked | **As said on 7 October: train on the extremes the car never reached, so the agent knows them; check the trained agent on the states we have logs for, so we know it trained correctly.** *Train*: ambient drawn per episode over 25–45 °C, a speed target that changes mid-run (60–150 km/h), hills up to 18 %, and thin air once the plant reads pressure (a plant change, so a new fingerprint). *Check, on states we have*: the logged drives replayed through the simulator with their own speed and ambient, where the simulator is validated against the car; there the agent must deliver the torque asked for, burn no more fuel than the baseline, and not protect where the car never needed it (no logged drive reaches the trigger). The logs carry no road grade: either replay them flat, or rebuild the grade from the car's own air mass, which leans on the unidentified mass and drag area. *Transfer*: hold out 50 °C and the hills of 18–22 % as a test the agents never trained on. The locked climb's twenty frozen episodes stay the protocol. Why: the conditions test shows agents trained in one air fail outside it (at 25 °C on a 21.75 % hill 6 of 20 beat current-grade, and in thin air their torque delivery breaks down), and 98 % of their training was in 7th and 8th gear on nothing steeper than 14 %. Cost: wider training spreads the seeds, so the ablation may need more of them. **Three safeguards, because the extremes are where the simulator is least trusted:** (1) cap every lever whose physics is untested (the spark cap of 30 September) and draw the uncertain constants per episode too (the turbine housing's heat capacity, the knock threshold, the damage scale), so an agent cannot learn one wrong model value; (2) the logged drives can show the agent does no harm, not that it protects correctly, since none of them reaches the trigger: add physical sanity checks at the extremes (a hotter housing must never get less protection) and let drives A and C widen the region the simulator is validated in; (3) keep the held-out conditions unseen until the final test, and never tune on them | | |
| 13 | The yardstick | **Make current-grade's torque shortfall a gate in the preregistration**: count its steps under 95 % of the requested torque on the new test set before any agent is scored; if it is short, report the shortfall beside every margin over it (or make it pull boost only within the tracking tolerance, decided before training). On the conditions test's speed profile it was short for 122–303 steps of 719 in four of seven conditions | | |

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

## What is already settled and needs no answer

- The five steps before any training, agreed on 30 September (`CLAUDE.md`, first
  box): sub-step the thermal network, fingerprint the derived constants, cap the
  spark trim, ramp every grade change, a new preregistration. Drive C before
  drive A.
- Recording does not change results: an agent trained with the new recorder is
  the agent trained without it (600 steps, largest weight difference 0.0), and
  every recorded episode equals its committed score.
