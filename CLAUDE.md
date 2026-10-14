# CLAUDE.md — read this first

The handoff for anyone who opens this repository, person or AI: what the project
claims, the rules, and the mistakes not to repeat. Everything else is one link
away, in "Where everything is" at the end.

---

## Before anything else: ask who you are talking to

**Jad's rule, 28 September 2026: the first thing you do in every session is ask
who you are talking to**, before reading further, answering or explaining. One
short line, Arabic first:

```
مين معي؟
Who am I talking to?
```

If they said who they are in their first message, that is the answer. Then open
the file in `team/` whose `name:` matches (a first name or the student number)
and follow it for the whole session. A stub file: say so, and offer to fill it
in, one template question per message, never from a guess. No file: carry on
without a profile, say so, and point at `team/_TEMPLATE.md`. A subagent skips
this. Do not match `git config user.email` instead: it names whoever set up the
clone, and it failed (`AUDIT2.md` Part 6). Five people share this repository
and they do not share a background, so this is not a courtesy. The full text of
this rule is `STATE_HISTORY.md` part F.

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

## Hard constraint, no exceptions

**The project never writes to the vehicle's ECU.** Read-only OBD-II logging
only. No flashing, no CAN transmission, no tuning. If a task seems to require
writing to the car, it is the wrong task. Say so rather than finding a way.

The app adds two structural rules: it never transmits to the vehicle, and it
never writes raw car data to disk. `app/test_replay.py` asserts both.

## Training gate — agreed by Jad and Ghassan, 30 September 2026

The live list's six items, verbatim ("Before ANY training, in this order"), each status in brackets from
Ghassan's note of 9 October. The list as it stood: `STATE_HISTORY.md` part E; `CHECKPOINT.md` never restates it.

1. [landed `75ca65f`; the fit that derives the thermal constants still steps at
   1 s, mistake 25] **Sub-step the thermal network** (or integrate it
   implicitly), then re-run `validate.py`, `check_premise.py`, `test_reward.py`,
   `check_roads.py`, `generality_test.py` and the app pins, and sweep the
   figures that move.
2. [closed, `75ca65f`] **The fingerprint covers `data/derived_params.json`** (and `derived.py`).
3. [the cap closed, `75ca65f`; the reporting holds until drive C] **Cap the
   spark trim at 0 for the next training**; report every result with and
   without the knock term until drive C.
4. [closed, `75ca65f`] **Ramp every grade change** (the one-step knock spike).
5. [open question: X1's preregistration came before X1 trained but tests
   decision 12's set; is X1 step 5?] **A new preregistration**, written before
   anything trains: D2-style randomised roads plus multi-climb roads as the
   test set, the blind-arm check, damage reported both ways.
6. [open; X1 and X2 trained before it, on Ghassan's order] **Drive C (knock),
   before drive A** (`logs/DRIVE_PLAN.md`): read-only, six channels, roll-ons
   in a held gear, the passenger on the phone, its decision rule written
   before the drive.

## Rules for an experiment that will be reported (plan v3, 6.4, 6.6, 7)

1. The preregistration is committed before the first training step.
2. Train from a clean, pushed commit whose `train.py` and `fingerprint.py` are `main`'s.
3. Every seed and arm on one environment (one machine, one set of versions).
4. Python 3.12 for every fingerprint, test and run; NumPy 2; record the exact torch, stable-baselines3 and gymnasium versions.
5. Two results are one experiment only if every FATAL fingerprint field (`plant_sha` on one Python minor), `derived_sha`,
   the protocol and the environment agree; otherwise compare them only as an ablation declared in advance.

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

## When a new drive CSV arrives

`python new_drive.py <csv>`, then `python build_dataset.py "logs/raw/*.csv"`. A new
drive re-derives the plant: it changes the simulator and invalidates trained
agents. The full routine and its six checks: `.claude/rules/data.md`.

## Where things go

A permanent rule goes here; a procedure for one area in `.claude/rules/`; the current state in `CHECKPOINT.md`.
When the state changes, rewrite the checkpoint and move what is no longer current, verbatim, to the end of
`STATE_HISTORY.md`; never delete it. This file stays under 200 lines; `verify_docs.py` fails it above 300.

## Where everything is

| what | where |
|---|---|
| the current state, and the next actions | `CHECKPOINT.md` |
| every figure with the command that prints it; the phase table; the repository layout | `README.md` |
| the results, experiment by experiment | `results/README.md` |
| every mistake, in full | `docs/MISTAKES.md` |
| the limitations and open measurements for the thesis | `thesis/LIMITATIONS.md` |
| every superseded state, verbatim (part A the dated boxes, B the old checkpoint, C the void headline, D September's changes, E the old lists, F the full text of condensed sections) | `STATE_HISTORY.md` |
| an index of the dated documents | `HISTORY.md` |
| the procedure for one area, loaded when you touch its files | `.claude/rules/` |
| where every number we did not measure comes from | `REFERENCES.md` |
| the restructure of 14 October, move by move | `_merge_review/MIGRATION_LEDGER.md` |

## Tone note for whoever writes the thesis

This project's advantage is that almost every number came out of running
something. Two calibrations have been corrected against measurement, one
hypothesis has been refuted and reported, and the validation table states what
it does *not* cover. Keep that. An examiner trusts a student who reports against
themselves, and punishes a validation table that implies coverage it lacks.
