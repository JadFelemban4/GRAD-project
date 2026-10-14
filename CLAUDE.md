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

## State history

The dated state boxes that stood here, from Ghassan's X2 box of 11–13 October
back to Phase D's of 21–22 September, are in `STATE_HISTORY.md`, part A,
verbatim and newest first. The current state is `CHECKPOINT.md`.

### Where every phase stands — current, 30 September (after the merge); C, D and F updated 8 October

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — load residual **1.4 % with zero fitted parameters** (derived k = 0.831), **1.1 % with the one fitted k** (0.839), over 26 pooled points, 30–75 kPa, from a dataset of eleven drives, 321.7 minutes. **Read mistake 12 before quoting it:** that residual is a consistency check between two ECU channels, not a test of the cycle model. **Since 28 Sep the thermal network, boost ceiling, spark offset and enrichment dwell are DERIVED from the logs** (`derive_params.py`); `validate.py` 8 of 11 (6 of 7 literature, 2 of 4 against our car). The knock model is NOT validated |
| C · get an agent to learn | **Two sets, each on its own plant.** On sep17's plant: C1 (16 agents, 50 000 steps) and C4 (16 agents, 300 000 steps, NOT converged by C4's preregistered rule, `PREREGISTRATION_C4.md` 5b). On Ghassan's derived plant: twenty agents, ten seeds a side, 50 000 steps (55 episodes), a new road every episode, dt 1.0 (`results/agents/terrain_dt1/`). **X1, trained 8 October and scored 9 October:** 23 seeds a side, 50 000 steps, on the plant with the agreed fixes (sub-stepping, spark cap, ramps) and the extremes design (`results/PREREGISTRATION_X1.md`; `runs/extremes_dt1/`, CLOSED in `train.py` since its result). **X2, trained 11–13 October (51 hours):** 5 seeds a side, 1 080 000 steps (1200 episodes) each, X1's plant, the extremes roads in wider air (0–45 °C, 80–101.3 kPa; `wide_air.py`, `results/PREREGISTRATION_X2.md`, `runs/wideair_dt1/`). **NOT converged** by C4's rule (0 of 5 sighted, 1 of 5 blinded, 0 of 5 pairs settled) |
| D · baselines and the ablation | **done four times, never decisively.** Phase D and D2 INCONCLUSIVE; C4 SMALLER THAN THE MEI by the sign test only (p 0.0352), the permutation test disagreeing (0.3867), not converged; Ghassan's retrain INCONCLUSIVE under the MEI rule (6 of 10, power 0.26). Supervision beats `current-grade` on the median in every set — **but with spark advance forbidden that margin disappears** (the box at the top). The MEI is 50 damage units (set 22 Sep); X1 restates it as 5.43 points of cut (decision 5) and is the fifth look, preregistered and scored by `x1_score.py`: **SMALLER THAN THE MEI** (17 of 23 pairs below it, sign p 0.0173, the permutation test agreeing), with six sighted agents and no blinded one protecting little on the scored climb (post hoc). X2 is the sixth: **INCONCLUSIVE** (1 of 5 positive, mean −4.40, sd 20.51, so 143 seeds for 80 % power against the MEI), its agents not converged at 1200 episodes |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary, hand-written policies only. **Re-run on 8 October on the sub-stepped plant:** preview over current-grade 0.0 points at every τ where the limit binds (H2), 0.0 to +0.3 with the limit kept binding (H2b), as before. `timestep_study.py` on the same plant: stepping the network 50 times finer moves a cut by 0.00 points at the sweep's 2 s step (it was the reason the sweep was not quotable). Quotable now as a hand-written result; AUDIT.md C3 still says hand-written policies cannot settle the criterion |
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
                           merged plant the notch moved to ~13.96 %. Re-run
                           9 Oct on X1's plant (ramped, sub-stepped): PASS,
                           0 of 121 (weakest 13.97 % at +11.9 K), 0 of 20
python analyse_c4.py       C4's preregistered test, D2 and Phase D beside it:
                           3 of 8, below-MEI sign p 0.0352 / permutation
                           0.3867 (disagree), SMALLER THAN THE MEI, NOT
                           CONVERGED. Captured in results/C4_RESULT.txt
python analyse_phase_d2.py D2's result beside Phase D's, each classified by the
                           MEI rule
python full_run.py         every script below, one pass, exit codes -> FULL_RUN.txt
python -m app.test_simulation   16 of 16 (9 Oct). The replay lab. SEPARATE from
                           app.test_replay -- run both after touching app/
python -m app.test_agents  135 tests OK, 14 skipped without runs_c4/ (9 Oct).
                           The agent replay pages; they read the plant's roads,
                           so run it after a plant or road change (mistake 25)
python test_plant_guards.py  6 tests: a 1 s step equals ten 0.1 s steps, the
                           coolant settles at the sweep's 2 s step, and one
                           changed derived constant moves derived_sha while
                           the file's timestamp does not. Each fails with its
                           guard removed (checked 9 Oct)
python substep_fit_check.py  DIAGNOSTIC: the thermal fit re-run with the
                           plant's sub-steps (mistake 25): radiator scale +61 %,
                           the locked climb's baseline -2.4 units, current-
                           grade's cut +0.01 points. Writes nothing the plant reads
python check_premise.py    the hand-written policies on the locked climb:
                           baseline 848.1 at 883 C, current-grade cuts 47.0 %,
                           preview -0.0 points against it (8 Oct). Writes
                           results/premise.json. HAND-WRITTEN -- read AUDIT.md
                           C1 and C3 before quoting any of it
python validate.py         8 of 11 inside their band: 6 of 7 against literature,
                           2 of 4 against our own car (rows 8-11, since 28 Sep)
python derive_params.py    every constant the car's logs set, recomputed from
                           them -> data/derived_params.json (build_dataset.py
                           runs it). REFERENCES.md 4b: what is still typed, why
python calibrate_thermal.py  the thermal fit, per drive, with every drive also
                           scored HELD OUT; results/thermal_calibration.json
python test_reward.py      12 of 12 checks pass, eight of them on the TRAINING
                           roads (two on X1's extremes roads, two on X2's wideair
                           corners, 11 Oct) -- run it after any change to the
                           reward, the plant, the gearbox or the roads
python analyse_x1.py       X1's preregistered test (results/PREREGISTRATION_X1.md):
                           SMALLER THAN THE MEI, 17 of 23 pairs below 5.43 points
                           of cut, sign p 0.0173, permutation 0.0027; the same
                           thermal-only. --set terrain_dt1 is its dry run on the
                           twenty of 29 September
python analyse_x2.py       X2's preregistered test: INCONCLUSIVE, 1 of 5 pairs
                           positive, mean -4.40, sd 20.51 -> 143 seeds for 80 %
                           power against the MEI; the same thermal-only. X1's
                           rule, imported; --set extremes_dt1 --seeds 0-4 is its
                           dry run (INCONCLUSIVE, sd 26.82)
python check_x2_convergence.py   X2's agents: NOT-CONVERGED (0 of 5 sighted, 1 of
                           5 blinded, 0 of 5 pairs settled) -> results/x2_convergence.txt
python x2_agents.py        what X2's agents did and why X2 failed, measured after
                           the result (description, never a test): preview used in
                           opposite directions, practice cuts spanning 6.0-88.5
                           points along training, 56.1-97.0 % of the extra fuel on
                           the car's drives spent where the housing is cool, against
                           the baseline ECU's one-step knock spike ->
                           results/x2_agents.json, written up in results/X2_AGENTS.md;
                           --trajectory also re-scores the 180k-540k checkpoints
python test_wide_air.py    16 tests: X2's roads reduce to the plant at sea level,
                           leave every other environment alone, and follow the air
                           (inlet, torque floor, kickdown table); about 6 min
python check_roads.py --road wideair   X2's roads: PASS, 2 of 40 bind
python train_all.py        the twenty agents: seeds 0-9 x sighted/blinded, one
                           process each on the CPU, ~4 h; writes runs/terrain_dt1/
python record_agents.py runs/terrain_dt1   scores them on the twenty frozen
                           episodes, records EVERY step, and documents each agent
                           in results/agents/terrain_dt1/ (README.md: every table)
python knock_margin.py     the twenty with spark advance forbidden, a diagnostic:
                           median cut 67.9 -> 41.6 % sighted, 65.4 -> 41.7 %
                           blinded, against current-grade's 43.4 % (all on the
                           merged plant, which those agents trained on)
python damage_constants.py  every constant of the damage formula: creep rupture
                           gives a 20.3 K turbine scale (the formula uses 45 K);
                           the 850 C knee is 984 C of gas; re-scored, every agent
                           still beats current-grade (results/DAMAGE_CONSTANTS.md)
python training_roads.py runs/terrain_dt1   the road, weights and actuators under
                           every step of the 29 Sep training runs, regenerated and
                           checked: 20 of 20 runs (results/train_roads_check.json)
python show_record.py <record>   draws one recorded episode; --table, --list,
                           --zigzag (the coolant node's step-to-step swing)
python check_roads.py      drives the baseline over 40 training roads and fails
                           if any is one the baseline cannot drive; 14 bind
                           (on the merged plant); --road extremes: X1's roads,
                           PASS, 10 of 40 bind, worst neutral -0.0043
python premise_split.py    the plant changes of 8 October on the locked climb,
                           one at a time: 920.1 -> 917.6 (sub-stepping) ->
                           848.1 (with the ramp) -> results/premise_split.json
python x1_score.py         waits for X1's 46 runs, then scores them in the order
                           PREREGISTRATION_X1.md section 10 fixes; one line per
                           step in results/x1_score/SCORE_LOG.txt
python x2_score.py         the same for X2's 10 runs (results/x2_score/); ran
                           13 October, every step but the transfer test, whose
                           harness named seeds X2 lacks (fixed and re-run)
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
                           peak estimated turbine 872.7 C, 14 thermal / 0
                           mismatch / 19 novel alerts. The reason for every
                           move of a pin is written beside it in the file
                           (28 Sep: the exhaust-flow fix moved 7475b5d7; the
                           derived enrichment dwell moved pull01; 8 Oct: the
                           thermal sub-stepping moved both by 0.4-0.6 K)
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
  knob the audit named. *(Corrected 8 October: the "80 K more conservative"
  half is mistake 23 -- a housing temperature set against a gas temperature.
  Like for like the knee is 984 C of gas, 54 K HOTTER than Conway's limit. The
  "do not turn the knob after seeing results" half stands; whether the knee
  moves is decision 9 of results/VALIDATION_DECISIONS.md, before training.)*
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

## Mistakes already made: one rule each

The story and the evidence of each are in `docs/MISTAKES.md`, under the same
number. Read the entry before you touch what it names.

1. A default that silently picks a different physical system is a trap: pass the engine geometry explicitly.
2. This car's manifold-pressure channel sits before the throttle: invert the pressure from air mass with `plant.map_from_airflow()`.
3. A baseline you guessed flatters you, and the flattery shows up as a large headline number: calibrate it against the car.
4. One drive is not evidence: count the samples behind a fit, and check that the variable you fitted against actually correlates.
5. Delivering the requested torque is the job: run `test_reward.py` after any change to the reward, the plant, the gearbox or the roads.
6. Do not extend a fit beyond the data that produced it; say where it stops.
7. Before fitting, check whether the channel saturated: a flat maximum repeated across drives is the tell.
8. A window sized in samples is not a window in seconds: check its span and its gaps. Census once with every channel, then log a small set.
9. A limiter that publishes the unlimited value when it finds no safe one is worse than none; if a table should have a shape, check the shape.
10. A fix that lives in the test file is not a fix: correct the helper itself.
11. When a figure changes, grep the whole tree for the old value, read every hit and add it to `verify_docs.RETIRED`; after touching the guard, run `drift_test.py`.
12. A residual computed through an inversion of the same model cannot test that model: perturb the parameter and check the number moves.
13. Treat every channel name as a hypothesis.
13b. A lagged sensor cannot be characterised from samples slower than its lag: log fewer channels to read each one faster.
14. Before tuning a detector, check that it compares two measurements of the same physical quantity.
15. A convergence claim needs a convergence measurement, at a named operating point.
16. A release archive is a snapshot, not an authority: diff it against the tree, and never unzip it over a branch.
17. A plant simplification is only safe at the operating points it has been used at: re-check it when the scenario gets harder.
18. Check a channel's range as well as its meaning: the gear is inferred from engine speed and road speed.
19. After a fix, look at what it prints and ask whether the number could have come from the fallback.
20. When fits of one model to different data disagree, suspect the model's form before its numbers.
21. A purpose-built drive answers its question only if it also logs what the question is measured against.
22. A sentence that carries a number needs the run that printed it; a limit is judged against the top of the range.
23. Before comparing two temperatures, check that they are the same temperature (housing, gas, thermocouple, cycle mean).
24. An explanation names quantities: measure every one it names before writing it.
25. An output that does not move after its input changed means: check the input reached it. After a plant change, run every suite that reads the plant.

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
step_record.py        What a recorded step holds: ONE definition for every
                      script that runs episodes (7 Oct). Read it first.
show_record.py        Draws or tabulates one episode of any record: the road,
                      the gear, the engine, every actuator asked and applied,
                      the heat against the parallel baseline car, the damage.
training_roads.py     The road, weights and applied actuators under every step
                      of the 29 Sep training runs, regenerated and checked.
record_extracts.py    Small committed extracts of the gitignored records for the
                      results page (conditions_traces.json, bad_episode_trace
                      .json). Re-run after the records are re-made, then
                      make_page.py.
conditions_test.py    The twenty agents at 25-50 C and 76-101 kPa, on a speed
                      target that changes mid-run; every step recorded.
damage_constants.py   Every damage constant: what can set it, the value where
                      something can, and the frozen episodes re-scored.
                      --set <name> re-scores another set (X1's sensitivity rows).
analyse_x1.py         X1's preregistered test: the MEI rule at 5.43 points,
                      total and thermal-only; --set terrain_dt1 is its dry run.
logged_check.py       X1's check on the car's own drives, replayed flat: torque
                      within 5 %, fuel within 1 % of the baseline (--build
                      fixed the drives before training).
sanity_probe.py       A hotter housing must never get less protection: 50 K
                      added to the housing input on each agent's climb states.
premise_split.py      The 8 October plant changes on the locked climb, one at a time.
x1_score.py           Scores X1 once its training has finished, in the
                      preregistered order, unattended.
wide_air.py           X2's training roads (train.py --road wideair): the extremes
                      design at 0-45 C and 80-101.3 kPa, the compressor inlet,
                      the kickdown table and the torque floor following the air.
                      No hashed plant file: plant_sha stays X1's.
test_wide_air.py      Its 16 tests; read its docstring for what each guards.
analyse_x2.py         X2's preregistered test (X1's rule, five pairs).
check_x2_convergence.py  Had X2's agents settled? C4's rule at 720k/900k/1080k
                      steps, on ten practice episodes of the locked climb.
x2_score.py           Scores X2 once its training has finished, unattended.
x2_agents.py          What X2's agents did and why X2 failed, measured after
                      the result -> results/x2_agents.json, written up in
                      results/X2_AGENTS.md. Description, never a test.
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
NEXT_CHAT_PROMPT.md   The prompt to paste into a new session. Not on this branch
                      since the merge of 30 September: handoff.md is the entry point.
SESSION_REPORT_*.md   One per session, dated. 2026-10-08_records is the latest
                      (it runs to 13 October: X1 trained, scored and transferred;
                      X2 preregistered, trained, scored and explained).
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
                      replay lab, the agents page and the results tab, with no
                      vehicle connection.
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
  results_api.py      The results tab (--simulation only): GET /results and
                      GET /api/results, answered to this machine only.
  results_data.py     Reads results/ on every request: one section per
                      experiment, its verdict quoted, nothing written; the
                      one figure computed is blind minus sighted per seed.
  results_provenance.py  Where a result file's numbers came from: the plant
                      states, the git facts, this tree's fingerprint.
  results_eval.py     Parses one evaluate.py result file, results/<prefix>_seed<N>.txt.
  test_results.py     The results tab's suite.
  static/results.html, static/sim/results*.mjs, charts-lib.mjs
                      The results tab's page: view, charts, strings, styles.
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
  everywhere without announcing it. Use `--full` before a release. **After a
  change to the PLANT or the ROADS, run all three app suites** —
  `app.test_replay --full`, `app.test_simulation` and `app.test_agents` (about
  9 min; it skips 14 tests on a machine without `runs_c4/`): the ramp of
  8 October broke six tests of the third and nobody ran it (mistake 25).
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

## Tone note for whoever writes the thesis

This project's advantage is that almost every number came out of running
something. Two calibrations have been corrected against measurement, one
hypothesis has been refuted and reported, and the validation table states what
it does *not* cover. Keep that. An examiner trusts a student who reports against
themselves, and punishes a validation table that implies coverage it lacks.
