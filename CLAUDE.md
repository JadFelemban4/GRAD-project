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

## Where every phase stands

The phase table, the drive counts to quote and what a passing project means are
in `README.md` ("Where every phase stands"). What changed on 8 and 11 September
is `STATE_HISTORY.md` part D.

## The numbers that matter

Every figure the project quotes, with the command that prints it, is in
`README.md` ("The numbers that matter"). The void figures this file used to lead
with are `STATE_HISTORY.md` part C. The drive replays, the Taif drive, the
rolling road and the towing standard are in `thesis/LIMITATIONS.md`.

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

## Known limitations, and what is open

The limitations the thesis must state, and the open measurements (the
discretisation Phase D, D2 and C4 were scored in; Phase F's threshold rule), are
in `thesis/LIMITATIONS.md`, verbatim.

## Repository layout

Every script and file, and what it is for, is in `README.md` ("Repository
layout"). Two rules from it stay here: the app never writes to the vehicle, and
it never writes raw car data to disk; `app/test_replay.py` asserts both.

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
