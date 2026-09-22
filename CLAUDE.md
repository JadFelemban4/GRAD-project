# CLAUDE.md — read this first

Project context for Claude Code. If you are an AI assistant opening this repo,
this file is the handoff: it tells you what the project claims, what is already
proven, and which mistakes have already been made so you do not repeat them.

If you are a human, read it too. It is shorter than the handbook.

---

## Before anything else: find out who you are talking to

Five people share this repository and they do not share a background. **Read
`team/` first.** Run

```bash
git config user.email
```

and open the profile in `team/` whose `email:` line matches. It says what to
assume that person knows, what not to assume, and how they take an explanation
in. If no profile matches, ask once, then carry on without one — and say that
you are working without one.

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

## Current state — 22 September 2026 (after Phase D, which returned a NULL)

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

| Phase | Status |
|---|---|
| A · setup | done |
| B · match the simulator to the car | **passed** — load residual **1.4 % with zero fitted parameters** (derived k = 0.831), **1.1 % with the one fitted k** (0.839), over 26 pooled points from ten drives, 295.0 minutes, 30–75 kPa. **Read mistake 12 before quoting it:** that residual is a consistency check between two ECU channels, not a test of the cycle model. Thermal network calibrated; knock retard measured |
| C · get an agent to learn | **C1 done, C4 NOT done.** Sixteen agents trained on the ZF plant, seeds 0–7 both arms, each carrying a `meta.json` plant fingerprint. All sixteen curves improve. But **50 000 steps is what `train.py` itself calls "C1: the first bad run"** — 11 training episodes — against **300 000 for "C4: a real run"**. *(This row said "**next**, nothing has been trained yet" until 22 September, then briefly said "done", which was too generous: C1 is not C4 and the difference is load-bearing for Phase D's null — see `PREREGISTRATION.md` limit 6.)* |
| D · baselines and the ablation | **done, and the answer is a NULL.** Preview not significant (p = 0.36 sign, p = 0.49 permutation); the agent beats `current-grade` by +29 to +34 points on five of eight seeds. Preregistered before training. **One line outstanding: the minimum effect of interest is still TEAM DECISION**, and until it is set a null cannot be told apart from an underpowered study. *(This row said "not started. This is the floor of the project" until 22 September — the floor is now in.)* |
| E · battery plant | not started. `battery.py` does not exist |
| F · the H/τ sweep | preliminary result only, from hand-written policies |
| G · writing | not started |
| **APP · the live supervisor** | **runs; the six audit findings against it are now FIXED.** `app/` runs this same physics beside the car and estimates turbine temperature, which the vehicle has no sensor for. Its suite reports **49 of 49**, up from 46 because each fix shipped with a regression test. *(This row said "has six known bugs … passes 46 of 46" until 17 September; the fixes and the count both moved on 16 September and this row did not.)* The lesson still stands and is worth more than the fixes: **the suite reported 46 of 46 while all six were live.** Only M9 carries no test of its own. **Read `AUDIT.md` and `AUDIT_FIXES.md` before quoting anything it prints.** A SECOND DELIVERABLE, not a substitute for Phase D |

**Where the app sits, and what it must not be allowed to become.** The app is
the demonstrable, showable half of this project and it will be the first thing
anyone asks to see. It is still not the claim. The claim is the H/τ criterion,
and the claim is TESTED in Phase D. **Phase D has now run, and it did not prove
the claim — it returned a null on preview (p = 0.3633).** That is still the
project's result; what it is not is a confirmation. The rule that got us there
is worth keeping for E, F and G: treat time spent on `app/` past the point where
it works as time taken from the claim. *(This paragraph read "the claim is
proved in Phase D … if the app is finished and Phase D is not, the project has a
nice screen and no result" until 22 September. Note the verb: **tested**, not
proved. A phase that can only confirm is not an experiment.)*

What the app does earn, and it is worth saying plainly in the thesis: it is the
same validated plant, running forward in real time against a live stream rather
than in a scenario, and it inherits Phase B's validation *and* Phase B's limits
intact. That is an honest end-to-end demonstration that the model is usable
outside the notebook it was fitted in.

**What changed since 11 September.**

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
| drives in the manifest | **10**, 295.0 min | everything ever logged, `pull01` included |
| drives carrying usable samples | **7** | survive the warm-sample filter |
| drives behind the fitted calibrations | **8** | the set the enrichment and spark fits were built on |

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
baselines + an ablation isolating preview. That is Phase D, **and Phase D is
in.** The floor is down, with a SPLIT VERDICT that must be reported as two
claims and never as one:

- the agent **does** beat the comparators — **+29 to +34 points** over
  `current-grade` on five of eight seeds, positive on seven of eight;
- the ablation isolating preview is **NOT SIGNIFICANT** (p = 0.3633 sign,
  p = 0.4922 permutation).

Everything after it raises the ceiling, nothing after it protects the floor.

---

## The numbers that matter

Anyone can regenerate these. Do not quote a number that a script does not print.
**`python full_run.py` runs every one of them in a single pass and writes
`FULL_RUN.txt` with each block's EXIT CODE. Sweep documents from that file, not
from this list** — a list goes stale, a transcript is dated.

```
python analyse_phase_d.py  THE PROJECT'S RESULT. 5 of 8 seeds positive, mean
                           +4.8 damage units, exact one-sided sign p = 0.3633,
                           exact paired permutation p = 0.4922 -> NOT
                           SIGNIFICANT at alpha 0.05. Also prints the agent's
                           +29 to +34 points over current-grade, which is a
                           DIFFERENT claim -- see the box at the top of this file
python drift_test.py       16 of 16 injected drifts CAUGHT. The guard's own
                           acceptance test; every row AUDIT2 Part 4a marked
                           MISSED is now caught
python full_run.py         every script below, one pass, exit codes -> FULL_RUN.txt
python -m app.test_simulation   15 of 15. The replay lab. SEPARATE from
                           app.test_replay -- run both after touching app/
python check_premise.py    its pre-16-Sep figures are VOID -- see AUDIT.md C1,
                           C2, C3 and the box in README.md. It now prints
                           baseline 959.8 at 884 C: the constraint BINDS,
                           ~34 K over the 850 C trigger, and hand-written
                           preview loses to current-grade by 0.4 points. Run
                           it; do not quote a number from here. (Its history
                           is in the paragraph under this block.)
python validate.py         8 of 11 published quantities inside band
python test_reward.py      4 of 4 checks pass
python build_dataset.py "logs/raw/*.csv"    295.0 min, 10 drives, 26 operating points
python compare_log.py data/master_points.csv   PASS, 1.4 % load residual,
                           k derived 0.831 and zero free parameters. Read what
                           it prints, not what you hope: it compares two ECU
                           channels through the displacement and three defined
                           constants, and it does NOT measure the breathing
                           model — mistake 12
python verify_docs.py      recomputes the published figures from the shipped
                           data, then greps every tracked document and .py file
                           both for those figures and for retired ones. It
                           prints its own total; read that, do not quote a
                           count from here, because the count moves whenever a
                           figure is added
python check_map.py        spark falls with load in every row, rises with speed
                           in every column; 6 cells above the compressor ceiling
python -m app.test_replay  49 of 49. It replays 7475b5d7 and pins the app's own
                           numbers: peak estimated turbine 890.6 C. (This read
                           "36 of 36, --full for 46 of 46, peak 884.9 C" until
                           17 Sep. The audit fixes added three regressions and
                           the H1 crank-angle correction lifted the peak; both
                           are recorded in AUDIT_FIXES.md and neither reached
                           this block.)
```

<!-- RETIRED-OK: 256.5, 801 -->
*(The `check_premise.py` line above said 256.5 at 801 C until 17 Sep -- the
pre-H1 figures, superseded when DTHETA_DEG went 0.5 -> 0.25. AUDIT_FIXES.md H1
records the move and that line did not follow it. Until 22 Sep it then quoted a
baseline that did not bind at all; the scenario had moved on and the line again
did not follow.)*

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

**What replaces it:** run `check_premise.py`. It currently prints a baseline of
959.8 at 884 °C, the constraint binding by ~34 K against the 850 °C trigger, and
preview worth **−0.4 points** against a policy that only knows the grade it is on
now.

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
>
> *(This paragraph ended "**Until then this project has no measured preview
> advantage at all**" until 22 September. It is now measured, and the measured
> value is "not distinguishable from zero", which is a different statement from
> "unmeasured".)*

<!-- RETIRED-OK: 1.8, 252.3, 257.7, 2.2 -->
The honest comparator —
added 16 September — is a policy that acts on the grade the car is on right now,
with no preview, which currently BEATS the predictive one by **0.4 points**
(633.2 against 637.4 damage; it read 1.8 points, 252.3 against 257.7, until
22 September, and 2.2 until 17 September, on the pre-H1 crank-angle step).

**And the scenario is the thing to fix, not the threshold — measured
17 September over EVERY drive.** *(17 Sep conclusion, since done: the scenario
was rebuilt at 12 % / 130 km/h on the ZF 8HP51 and now binds by ~34 K, peak
884 C against the 850 C trigger. The do-not-lower-the-limit half still stands.)*
Replaying all nine through `app/` and reading
the peak estimated turbine housing against the 1123 K trigger:

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

## Eighteen mistakes already made. Do not remake them.

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

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on six
separate drives, **547 samples**. That is a sensor ceiling, and on the same
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

## Known limitations to state in the thesis, not fix quietly

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
- **THE OIL BAND IS NOW SUPPORTED BY OUR OWN CAR, AND THE MODEL MISSES IT LOW.**
  This is the most valuable thing `drive10` delivered (18 September, 119.5 min).
  <!-- RETIRED-OK: 107 -->
  The hottest oil in the logs was 107 °C across the first nine drives, which
  sat *below* the published 115–140 °C band — so the band was unverifiable from
  our own data and `validate.py`'s miss could not be interpreted. `drive10`
  reaches **117 °C**, with **1320 rows above 110 °C and 60 above 115 °C**.

  That changes what the miss means. The band's lower end is now inside our own
  measurement, and the model's **110.2 °C is confirmed about 7 K too cool on a
  sustained climb** rather than merely disagreeing with an unsourced number.
  Say it that way in the thesis: the miss is real, it is measured, and it points
  at the thermal network's oil path (`ua_block_oil`, the only MEASURED parameter
  in `thermal.py`) rather than at the band.

  Above 117 °C is still extrapolation.
- **Ten drives in the manifest, seven with usable samples.** `3f64372e` and `f51686d7` are under
  a minute each and contain no warm running window; `fb988991` is a census log
  whose windows are all rejected for span or logger gaps (mistake 8), so it
  carries samples but contributes **zero** operating points. Quote it as "ten
  drives, 295.0 minutes, seven carrying samples, 26 distinct operating points".

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
  corrected charge-temperature scale of mistake 13.) The weakest cell of the fit
  is 3500–4500 rpm at **long** dwell — observed 0.90 against a modelled 0.93,
  and that speed band is the thinnest of the three at n = 235 samples above the
  gate, against 441 and 665. Every one of the nine cells is within 0.027 of
  measurement.
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
  unsupported by the car's own behaviour. It still counts toward "8 of 11".
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
- **The alert counts are not evidence.** 15 thermal / 0 mismatch / 19 novel on
  `7475b5d7` is a property of thresholds this project chose, pinned so that a
  regression is visible. It is not a measurement of the car.

### THE 14 SEPTEMBER AUDIT FOUND SIX BUGS IN `app/`, AND THE APP'S OWN TESTS PASS ANYWAY

`AUDIT.md` is a full technical review of this branch. **Read it before quoting
anything the app prints.** It is the most important document added this week and
it disagrees with the confident tone of the section above.

Six of its findings are against `app/`, and the app's own suite reports 46 of 46
while every one of them is live. That is the point worth internalising: **a test
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
saying what moved. This paragraph said "none of these is fixed as of
16 September" until 17 September, which was already untrue when it was written:
the fixes landed in the same pass that produced `AUDIT_FIXES.md`. Mistake 11 for
the fifth time — the code moved and the prose did not.

Verified by running the suite, not by reading the response document: it reports
**49 of 49** (three new regressions over the old 46), and five of the six carry a
test named after the finding — `H8: the modelled lambda reaches 0.81 after a
sustained pull`, `M11: the modelled block equals the measured coolant`,
`M10: no time-to-threshold when the limit is unreachable`, `M8: leading coolant
zeros are not read as 0 C`, `M7: app.server imports and serves its three pages`.
**M9 is the exception**: it is fixed in `app/reader.py` (the comments at `:530`
and `:581` name it) but carries no test of its own, so it is the one of the six
that could silently regress.

**What moved, and it is small:** `7475b5d7`'s peak estimated turbine is
**890.6 °C** against the 884.9 °C this file quotes above, and `pull01` reads
**608.0 °C** against 593.7. Both rises are the H1 crank-angle correction, not
the app fixes — see `AUDIT_FIXES.md`. The 884.9 and 593.7 figures in the section
above are therefore superseded.

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

C1 and C2 remain where they were. *(This paragraph ended "it is not addressed
here and it is not addressed anywhere yet" until 22 September.)*
---

## Repository layout

```
plant.py              0-D cycle model. predict() is the shared interface.
thermal.py            3-node lumped-capacitance thermal network.
engine_env.py         Gymnasium env. BaselineECU lives here.
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
train.py              SAC training. Writes runs/<tag>/meta.json — the plant
                      fingerprint — before the first step, and refuses a resume
                      whose plant disagrees.
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
prove_buffer.py       Proves the replay-buffer size changes nothing learned.
drift_test.py         The guard's own acceptance test: inject AUDIT2 Part 4a's
                      drifts and check each is CAUGHT. Currently 16 of 16.
full_run.py           Every script that prints a published figure, in one pass,
                      each block opening with its EXIT CODE -> FULL_RUN.txt.
                      Sweep the documents from that, not from memory.
results/PREREGISTRATION.md  Phase D's rules, committed before any agent trained.
results/void/         Result files that are NOT results, with a README saying
                      why. The +11.7 file lives here.
generality_test.py    The H/τ experiment. H1, H2, H2b.
README.md             The public-facing summary. Tracked by verify_docs.py.
CLAUDE.md             This file. The handoff and the mistake log.
REFERENCES.md         Where every number we did not measure comes from. Written
                      for a non-specialist. Read before quoting a published band.
DOCUMENT_STATUS.md    Which team PDFs still carry void numbers, and why.
AUDIT.md              Full technical review, 14 Sep. THREE CRITICAL findings
                      against the headline claim and six against app/.
                      Read it before quoting any number in this file.
team/                 ONE PROFILE PER PERSON. Read the one matching
                      `git config user.email` before explaining anything.
  README.md           how the matching works and how to add yourself.
  _TEMPLATE.md        copy this.
logs/CHANNEL_SET_FINAL.md   What is recorded, what to add, and why.
logs/CHANNEL_CENSUS.md      All 656 channels the car offers, live vs dead.
logs/raw/*.csv        Raw BimmerLink exports. Never edit these.
data/*.csv            Generated. Never edit by hand — re-run build_dataset.py.
validation_table.md   Chapter 3's evidence. Regenerate after touching the plant.
app/                  THE LIVE SUPERVISOR. Runs this same physics alongside
                      the car in real time and estimates what it cannot report.
  estimator.py        The virtual sensor. Read its docstring before touching it.
  reader.py           OBD-II, or replay of the logs above. Channel budget here.
  alerts.py           thermal / mismatch / novel. The ONLY file that writes.
  server.py           localhost. /, /driver, /review.
  static/*.html       dashboard, driver mode, review view.
  test_replay.py      Replay-driven regression checks. Run after any app change.
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
- Report numbers with the condition attached. "1.4 % load residual over 22
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
- **Say which drive population you mean.** Ten in the manifest, seven carrying
  samples, eight behind the fitted calibrations. All three are correct and they
  are not interchangeable.

---

## When a new drive CSV arrives

This is the routine, and it is the most likely reason someone opens this repo.

```bash
cp <new>.csv logs/raw/
python build_dataset.py "logs/raw/*.csv"     # rebuilds all three data files
python compare_log.py data/master_points.csv # re-scores the model
```

Then check, in this order:

1. **Did the sanity floor or the fuel-cut filter drop anything?** Both print.
2. **Did the operating-point count go up?** If the new drive added zero distinct
   points, it was not steady enough — that is a driving problem, not a code one.
3. **Which compressor flow bins are still empty?** It prints them. Only
   0.33–0.36 kg/s remains, and the MAF sensor cannot reach it.
4. **Does the load residual stay near 1.4 %?** If it jumps, the new drive covers
   a region the model has not seen, which is information, not failure.
6. **Did any window get rejected for span or a logger gap?** It prints both. A
   drive that loses every window that way was logged with too many channels
   selected — see mistake 8.
5. **Did the new drive push any channel to a flat maximum?** See mistake 6.

If the drive changes a calibration — lambda, spark, the boost ceiling — **check
how many samples support the change, and check that the variable you are fitting
against actually correlates.** See mistakes 3 and 6.

---

## Open, and honest about it

### THE AGENT IS SCORED IN A DISCRETISATION IT DID NOT LEARN IN. Measured 19 Sep

`dt` is not consistent across this project and never has been. Ghassan logged it
as an open question on 19 September; this measures it.

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

**What this does and does not do to the ablation.** Both the sighted and the
blinded agent train at 0.2 and are scored at 1.0, so the handicap is shared and
is not a bias by construction. Whether it is SYMMETRIC is unmeasured, and there
is a reason to doubt it: a policy whose entire value is timing may lose more to
a coarser step than one with no preview at all. **Quote no ablation figure
without this paragraph beside it**, and note that the hand-written comparators
are unaffected — they have no `dt`, they are functions of the current state.

Three ways out, and the choice is the team's, not the next session's: train at
1.0 to match the protocol; score at 0.2 to match the training; or leave it and
state it as a limitation. The third is legitimate and is the only one that
costs nothing, but it has to be written down rather than discovered by an
examiner.

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

> **THIS LIST WAS THE ROUTE TO PHASE D AND PHASE D IS DONE.** Steps 1–5 below
> were followed on 21–22 September and are kept as the record of how, not as
> instructions. **The live list is now:**
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

   *(This said "about 4.6 hours on one CPU core … 3.0 steps/s once SAC's
   gradient updates are included" until 17 September. Wrong by 6.4x, and the
   "one CPU core" qualifier was meaningless — one thread is marginally FASTER
   than six, because the policy network is tiny. The gradient updates cost about
   2 %: the environment alone runs 19.5 steps/s and the training loop 19.2. Each
   env step runs six engine cycles at ~9 ms against ~1 ms for a gradient step,
   so the combustion model is the entire cost. **What sets it is
   `plant.DTHETA_DEG`** — halving the crank-angle step roughly doubles the run,
   and it was halved on 16 September. Re-time after touching it.)*
3. `python test_reward.py` before trusting any training curve.
4. Five seeds, one per team member, overnight — `--seed 0` through `--seed 4`.
   Then the same five with `--no-preview`. That is Phase D's input.
5. Phase D: three baselines, one fixed evaluation protocol of 20 episodes,
   median and interquartile range over five seeds. **Once the 20 episodes are
   fixed they never change.** Changing the test set after seeing results is the
   one mistake this project cannot recover from.

Do not start Phase E or F until D produces a table.

**Where the app fits in that order: nowhere.** It is finished enough to demo and
it is not on this path. If you have an hour, spend it on step 2, not on `app/`.
The app's own next steps, for when D is done and only then, are kept separately
below so they cannot be mistaken for the critical path.

### The app's backlog — AFTER Phase D, not before

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
3. **Wire the trained agent in.** Once Phase D has a policy, the app can display
   what the agent WOULD command beside what the baseline ECU commands. That is
   the honest bridge between the two halves of this project, and it is read-only
   in exactly the same way — a suggestion on a screen, never a write.
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
