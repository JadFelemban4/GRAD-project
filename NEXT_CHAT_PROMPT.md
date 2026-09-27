# Prompt for the next chat

Copy everything inside the fence into a new Claude Code session opened in
`C:\Users\badcl\Desktop\GRAD-project`.

---

```
Continue the BMW B58 graduation project. Read CLAUDE.md first — it is the
handoff and the mistake log, and the current-state box at the top is current as
of 19 September 2026.

WHERE THINGS STAND

The scenario blocker is GONE. Fitting the car's real transmission (a ZF 8HP51,
where the model had a generic six-speed with invented ratios) made the protection
trigger reachable again:

    110 km/h, 12 % — this branch's default   839.7 C    0.0 % of the episode above 850 C
    130 km/h, 12 % — the locked scenario     884.0 C   66.3 % above 850 C

It bound because the model got MORE CORRECT, not because anything was tuned. The
130 km/h lock was decided 18 September, before any training existed.

Ten SAC agents were trained on 19 September — 5 sighted, 5 blinded, 50k steps,
173 min each — BUT AT 110 km/h, where nothing binds. They trained with nothing to
protect against, so they cannot settle Phase D. They are in runs/ and are kept as
a record, not as a result.

The scenario now DEFAULTS to 12 % at 130 km/h and the constraint binds. With
load, every hand-written policy does real work:

    baseline ECU (true neutral)   damage 951.9   peak 884 C
    reactive protection                  671.1   cuts 29.5 %
    current-grade protection             624.5   cuts 34.4 %
    predictive protection                628.4   cuts 34.0 %

    preview over current-grade: -0.4 points -- the closest to level it has been

WHY ELEVATION IS IN THE SCENARIO, and it is not a modelling convenience: the
car's own logs CANNOT load the engine. Median relative air filling is 24-40 %
per drive and only 2.0 % of 79 134 moving samples exceed 120 %. The driving is
fast -- median 95-137 km/h -- but it is straight-line flat-road cruising, which
asks for drag and rolling resistance and nothing else. Flat road at 90 km/h
leaves the turbine at 349 C against an 850 C trigger; 12 % at 130 km/h reaches
884 C. NO AMOUNT OF FURTHER LOGGING WILL FIX THAT -- the duty cycle is wrong,
not the model.

A FIRST TRAINED ABLATION EXISTS, and it is NOT the result. Scored with
evaluate.py, seed 0 both ways, at 110 km/h (see results/phase_d_seed0_110kmh.txt):

    baseline ECU      462.7      reactive  462.7 (identical -- never acts)
    current-grade     374.5      cuts 19.1 %
    agent sighted     301.9      cuts 34.8 %
    agent blinded     307.6      cuts 33.5 %

    AGENT over CURRENT-GRADE  +15.7 points
    SIGHTED over BLINDED       +1.2 points

TRAINING REVERSED THE SIGN. Hand-written, the predictive policy LOST to
current-grade by 0.4 points; the trained agent beats it by 15.7. That is
AUDIT.md C3 measured -- hand-written policies cannot settle this.

But it is not Phase D's number: it ran at 110 km/h where nothing binds, it is
ONE seed, and the +1.2 gap is far smaller than the within-policy IQRs of 25.6
and 29.9. sep17 measured +11.7 at 130 km/h on the six-speed; that is a different
scenario AND a different gearbox, so the two are not comparable. The retrain at
130 on the merged tree is what makes them one measurement.

DO THESE, IN THIS ORDER

1. MERGE origin/JMF-2340550-sep17 into JMF-2340550. They are twelve commits
   apart. sep17 has mistake 17 (the load-aware gearbox fix), the locked 130 km/h
   scenario, and Phase D's first point. This branch has the tenth drive
   (+119.5 min), the runtime 3 L verification, the ZF 8HP51 and mistake 18.
   Nothing is reportable until they are one branch. evaluate.py is already
   cherry-picked across.

   Expect conflicts in engine_env.py's Vehicle class — both branches changed
   gear_for. THEY ARE THE SAME RULE: sep17 added the load-aware downshift for
   the six-speed, this branch carried it into the eight-speed deliberately. Keep
   the eight-speed and sep17's constants.

2. (ALREADY DONE on 19 September — verify it survived the merge.)
   make_grade_climb now DEFAULTS to 12 % at 130 km/h. sep17 locked that on
   18 September before any training existed, so adopting it was catching up to
   a decision, not tuning one. Confirm after merging that the default is still
   130 and that its docstring is intact.

3. RETRAIN AT 130 -- READY SINCE 27 SEPTEMBER. Ten runs, 5 seeds each way:
       python check_roads.py                               # must PASS first
       python train.py --steps 50000 --seed 0..4
       python train.py --steps 50000 --seed 0..4 --no-preview
   Every episode is a new road (TerrainTrainingEnv); scoring stays on the
   locked climb. Output goes to runs/terrain_dt1/, NOT runs/ -- train.py
   resumes any checkpoint in its folder, and runs/ holds the 110 km/h agents.
   13.7 steps/s for one run alone; ten sharing a 20-core box took 173 min on
   19 September. Cap each with OMP_NUM_THREADS=1.

4. THE STEP BUDGET WAS DECIDED 27 SEPTEMBER: dt = 1.0. The episode is 900
   steps, not 4500, so 50 000 steps is 55 episodes instead of eleven for the
   same compute, and the agent trains in the step evaluate.py scores it in
   (train.py never passed dt before). If the ablation is still inside its
   noise, raise the steps; never change the twenty.

5. SCORE ONLY WITH evaluate.py. Twenty frozen episodes, median and IQR. THE
   TWENTY NEVER CHANGE. Changing the test set after seeing a result is the one
   mistake this project cannot recover from.

6. REPORT THREE ROWS, NOT TWO: sighted, blinded, and current-grade — a
   no-preview comparator that reads the gradient the car is on right now. It has
   beaten the predictive policy on every hand-written comparison so far
   (-0.4 points on the loaded scenario, the closest to level it has been). If
   the trained agent cannot beat it
   either, THAT IS A RESULT about H/tau, not a failure, and it should be
   reported as one.

HOUSE RULES THAT ARE NOT NEGOTIABLE

- Run verify_docs.py before quoting any number. It recomputes the published
  figures from the shipped data, opens every tracked .md and .py, and fails
  naming file and line. It is at 38 checks / 313 figure mentions.
- Never edit verify_docs.py's expected values to make a check pass. The only
  legitimate reason to change one is that the DATA genuinely changed.
- Never edit logs/raw/ or data/ by hand. Regenerate with build_dataset.py.
- After any change under app/, run python -m app.test_replay (49 of 49) and
  paste the output into the commit message.
- After changing plant.py or thermal.py, re-run validate.py and update
  validation_table.md in the SAME commit.
- A threshold changes only for a measurement, and the measurement goes in the
  docstring beside the number.
- Cite nothing from memory. REFERENCES.md sorts every number into CONFIRMED /
  UNVERIFIED / MEASURED / ASSUMED, and a fabricated citation is worse than a
  missing one.

OPEN QUESTIONS WORTH YOUR ATTENTION

- The 850 C trigger cannot be validated on this car. Its only exhaust channel is
  modelled, post-catalyst and CLAMPED at 645.3 C, and every pre-cat sensor is
  all-zero. The literature band (825-925 C for production component protection)
  is recorded UNVERIFIED because the primary sources would not open. Someone
  with library access should settle it.
- The knock model has no detectable relationship with the car's own retard
  (correlation -0.149 over 13 592 paired samples). Do not quote a knock-limited
  spark or knock damage term as calibrated.
- dt is inconsistent: premise 1.0, generality 2.0, training 0.2. The agent
  learns in a different discretisation than the hand-written policies were
  scored in. Fix it project-wide before quoting a comparison.
- The knock-retard p99 (9.8 deg) was filtered using `Actual gear`, which
  mistake 18 shows CLAMPS at 6 on an eight-speed. Re-derive it from the gear
  inferred from rpm and road speed before quoting it again.
- AUDIT.md has open items: M6 in part, M15, L8.

Start by running verify_docs.py, validate.py and python -m app.test_replay to
confirm the tree is sound, then do step 1.
```

---

## Files the next session should read, in order

| file | why |
|---|---|
| `CLAUDE.md` | the handoff and eighteen mistakes. Current-state box is at the top |
| `AUDIT.md` + `AUDIT_FIXES.md` | the 15 September review and what was done about it |
| `SESSION_REPORT_2026-09-19.md` | this session in full |
| `SESSION_REPORT_2026-09-18.md` | the `sep17` session — mistake 17, the scenario lock, Phase D's first point |
| `REFERENCES.md` | where every number comes from, including the gearbox (section 2b) |
| `CHECKPOINT.md` | dated snapshots, newest last |
