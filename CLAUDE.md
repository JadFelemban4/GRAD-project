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

## Training gate — agreed by Jad and Ghassan, 30 September 2026

The six items of the live list of 30 September, verbatim (`conflict.md` section 0
and Ghassan's reply): "Before ANY training, in this order". Beside each, its
status and the commit that closed it, from Ghassan's note of 9 October. The list
as it stood, with that note, is `STATE_HISTORY.md` part E. `CHECKPOINT.md` never
restates it.

1. **Sub-step the thermal network** (or integrate it implicitly), then re-run
   `validate.py`, `check_premise.py`, `test_reward.py`, `check_roads.py`,
   `generality_test.py` and the app pins, and sweep the figures that move.
   — *Landed in `75ca65f` (8 October). One part is open: the fit that derives
   the thermal constants still steps at 1 s (mistake 25); re-fitting it is a
   plant change, so it waits for the next.*
2. **The fingerprint covers `data/derived_params.json`** (and `derived.py`).
   — *Closed in `75ca65f`: fingerprint schema 2.*
3. **Cap the spark trim at 0 for the next training**; report every result
   with and without the knock term until drive C.
   — *The cap closed in `75ca65f`; the reporting rule holds until drive C.*
4. **Ramp every grade change** (the one-step knock spike).
   — *Closed in `75ca65f`.*
5. **A new preregistration**, written before anything trains: D2-style
   randomised roads plus multi-climb roads as the test set, the blind-arm
   check, damage reported both ways.
   — *Open question: X1's preregistration was committed before X1 trained,
   but its test set is decision 12's, not this one. Whether X1 is step 5 is
   for Jad and Ghassan to answer.*
6. **Drive C (knock), before drive A** (`logs/DRIVE_PLAN.md`): read-only,
   six channels, roll-ons in a held gear, the passenger on the phone, its
   decision rule written before the drive.
   — *Open. X1 and X2 trained before it, on Ghassan's order
   (`PREREGISTRATION_X1.md` section 0).*

## Tone note for whoever writes the thesis

This project's advantage is that almost every number came out of running
something. Two calibrations have been corrected against measurement, one
hypothesis has been refuted and reported, and the validation table states what
it does *not* cover. Keep that. An examiner trusts a student who reports against
themselves, and punishes a validation table that implies coverage it lacks.
