# Prompt for the next session — written 21 September 2026, after the second audit

Paste everything in the block below into a fresh Claude Code session. It is
accurate as of commit `fdba1b9` on `JMF-2340550-sep17` and it will go stale;
if a number here disagrees with a script, **the script is right**.

---

```
You are picking up a BSc graduation project after its second technical audit.

Branch: JMF-2340550-sep17. Confirm with `git rev-parse --abbrev-ref HEAD`.

READ FIRST, IN THIS ORDER
  AUDIT2.md   — the second audit, 21 Sep. 50 findings. Read "Which Phase D
                result is real", "Is the scenario locked or was it searched",
                and "Top 3 fixes". That is the whole brief.
  CLAUDE.md   — the mistake log. Read `team/` first and match
                `git config user.email` to a profile before explaining anything.
  CHECKPOINT.md — last entry, 20-21 Sep, is this audit's summary.

THE ONE THING THAT MATTERS
There is no usable Phase D result. `results/phase_d_seed0.txt` says +11.7 and
was produced on an invented six-speed gearbox that commit 27e720c replaced with
the real ZF 8HP51 seven hours later. Re-running the same two agents on HEAD
gives +7.5, and that is not a result either, because they are scored on a plant
they never saw. Do not quote either number.

ALREADY DONE — do not undo it
  runs/ was renamed to runs_sixspeed_18sep/ on 21 September. It holds the only
  copies of the two six-speed agents, it is gitignored, and `train.py --seed 0`
  would have resumed into it and overwritten the only record behind
  results/phase_d_seed0.txt. `train.py` now starts clean. Leave the old
  directory where it is until Phase D has produced a replacement.

WHAT TO DO, IN ORDER

1. FINGERPRINT RESULTS (AUDIT2.md C2-1, H2-3) — half a day.
   train.py writes runs/<tag>/meta.json: git rev-parse HEAD, Vehicle.gears,
   final_drive, plant.DTHETA_DEG, TURB_PROTECT_K, the make_grade_climb kwargs
   read from inspect.signature, dt, duration, a hash of evaluate.EPISODES.
   evaluate.py prints the same block FROM THE LIVE OBJECTS, writes it into the
   result file, and refuses a model whose meta.json differs. Also: on resume,
   append to curve.csv instead of overwriting it, and skip model.save when
   there is nothing to train.
   Until this exists, no Phase D number can be shown to belong to the plant it
   is quoted beside — which is exactly how +11.7 happened.

2. EXTEND THE GUARD (C2-2, C2-3, H2-6) — half a day.
   verify_docs.py currently misses 12 of 16 realistic drifts. Add a
   check_scenario() asserting make_grade_climb's defaults, TURB_PROTECT_K,
   Vehicle.gears/final_drive, evaluate.DT/DURATION, an EPISODES hash,
   check_premise's baseline damage and peak, and the app's pinned peak and
   alert counts. Share ONE file list between the figure scan and the retired
   scan, extended to **/*.py, **/*.html and presentation/*.js with tags
   stripped. Make RETIRED-OK figure-specific instead of paragraph-wide.
   The drift table in AUDIT2.md Part 4a is the acceptance test: every row
   marked MISSED must become CAUGHT.

3. SWEEP THE DOCUMENTS FROM A FRESH RUN (H2-1, H2-4, H2-8) — one day.
   Run the eight scripts, capture the output, and rewrite from it:
   CONTROL_SCOPE.md, CLAUDE.md's numbers block, README.md's box, handoff.md's
   table, results/README.md, presentation/README.md, and ABSTRACT.md, which
   currently carries a banner instead of a rewrite.
   The four figures that are wrong everywhere:
       175.5 min -> 295.0      nine drives -> ten
       22 points -> 26         30-74 kPa  -> 30-75
   Do this AFTER step 2 so the sweep is checked rather than trusted.

   THE ABSTRACTS ARE A SPECIAL CASE AND ARE NO LONGER FOUR. On 21 September the
   Arabic and simplified versions were deleted and DOC/Abstract_EN.docx plus
   DOC/Abstract_EN.pdf were SUBMITTED TO THE SUPERVISOR. Its dataset figures are
   correct. One sentence in it is not: it says preview is isolated "by
   re-evaluating that policy blind", which is the construction AUDIT.md C3
   voided -- it cannot fail and it is not evidence. evaluate.py trains and
   scores a SECOND agent, which is the defensible design. Raise the wording
   with the supervisor; do not silently re-submit. ABSTRACT.md's banner says
   the same thing.

4. THEN PHASE D, retrained on the current plant.
   Ten runs, five seeds each way, 63 min each. Before seed 1 runs, commit
   results/PREREGISTRATION.md naming the statistic (per-seed median damage over
   the twenty frozen episodes), the comparison (paired sighted-vs-blind by
   seed), the test (exact sign or paired permutation), alpha (0.05 one-sided)
   and the minimum effect. With five paired seeds the smallest attainable
   one-sided p is 1/32, so five is a floor, not a choice.

TRAPS THIS AUDIT MEASURED — do not rediscover them
  - M16 is NOT fixed. The headline "cuts N %" moves 37.0 -> 30.1 % on the time
    step alone, and 94 % of that is ONE knock spike at the grade discontinuity,
    not the PI loop CLAUDE.md blames. Ramp the grade; report the damage
    integral split into turbine / oil / knock.
  - generality_test.py still scores against the reactive comparator C3 retired,
    on a 520 s episode at dt 2.0 with its own damage(scale=25.0). Add
    p_grade_now and share one scenario before running it for the thesis.
  - presentation/index.html, plan.html and data.js still ship the void premise
    set as live figures -- the four numbers README.md's own box says never to
    quote. presentation/README.md records it; nothing enforces it.
  - Merging origin/JMF-2340550 as it stands brings a SECOND file labelled "the
    project's result", a docstring whose gearbox mechanism this branch measured
    as backwards, and a handoff banner that is false on the merged tree. See
    AUDIT2.md Part 6 before merging.

HOUSE RULES
  - The project never writes to the vehicle's ECU. Read-only OBD-II only.
  - Never edit data/ or validation_table.md by hand; regenerate them.
  - Run `python verify_docs.py` before quoting any number.
  - Change one thing, re-run, write down what happened.
  - Push to JMF-2340550-sep17, not main.
```
