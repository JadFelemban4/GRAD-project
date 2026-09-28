# Prompt for the next chat

Copy everything inside the fence into a new Claude Code session opened in
`C:\Users\badcl\Desktop\GRAD-project`. Written 28 September 2026.

---

```
Continue the BMW B58 graduation project. Read CLAUDE.md first — it is the
handoff and the mistake log, and its current-state boxes (the two 28 September
boxes and 27 September) are current. Then handoff.md (the short entry point) and
SESSION_REPORT_2026-09-28.md (the last session in full).

WHERE THINGS STAND

The Phase D retrain is READY and has NOT been run. Everything it needs is
committed on branch JMF-2340550 (not pushed):

  - the locked scoring scenario: 12 % at 130 km/h, 42 C, which binds
    (baseline 884 C against the 850 C trigger). evaluate.py scores it on
    twenty frozen episodes. NEITHER may change.
  - TRAINING on a new road every episode (engine_env.TerrainTrainingEnv):
    the locked climb itself, single climbs of 4-14 %, rolling hills, double
    climbs, flat. check_roads.py PASSES: 11 of 40 roads push the baseline past
    the trigger; worst neutral reward about +0.004.
  - train.py passes dt = 1.0, the step evaluate.py scores at (it never passed
    dt before). 50 000 steps = 55 episodes. Output: runs/terrain_dt1/.

Two simulator fixes landed on 27 September, each with its measured effect:
  - GEARBOX: in 8th at 130 km/h the model sustains 333 Nm but the box only
    downshifted above 375 Nm, so ~9 % grades were undrivable by any policy.
    It now kicks down when the engine falls short
    (Vehicle.DELIVERABLE_TORQUE). A stated workaround: the boost ceiling is
    too low at low rpm because the car was never logged there.
  - SPARK: the car-fitted map sat above the model's knock limit at all 26
    steady points and was never used. SPARK_A 26.18 -> 13.33 (offset only):
    part-load bias +3.16 -> -0.08 deg. Boost stays knock-limited.

Hand-written premise now: baseline 951.9, reactive 671.1 (29.5 %),
current-grade 624.5 (34.4 %), predictive 628.4 (34.0 %).

The ten agents in runs/ are a record, not a result (110 km/h, dt 0.2, one
road). Scored on the locked climb anyway (results/phase_d_130kmh.txt):
training beats current-grade by +25.9 points; sighted minus blinded, paired by
seed, mean -0.5, 95 % CI -2.0 to +1.1 -- indistinguishable from zero.

THREE FINDINGS FROM 28 SEPTEMBER (model_vs_data.py prints all three)
  - The knock comparison could not have seen knock: 7475b5d7 holds ~404
    readings of each ignition angle in 55 min, one per ~8 s. UNTESTED, not
    refuted. Drive C tests it.
  - Preview's -0.4 against current-grade is ENTIRELY the knock term (6-12 %
    of damage). On turbine + oil damage alone the two tie. Report both.
  - The existing logs CANNOT calibrate the oil node: fitting it on the light-
    load drives fixes the hard pulls but breaks drive10. Drive A decides.

LATER ON 28 SEPTEMBER (uncommitted work is committed at the end of that session)
  - validate.py rows 8-11 (oil, coolant) are scored against bands computed
    from OUR OWN DRIVES, through car_thermal.py (thermal.py free-running over
    a logged drive, fed measured fuel = air mass / 14.7 lambda). validate.py
    now reads 7 of 11: 6 of 7 literature, 1 of 4 our car.
  - The car's oil time constant is 70-100 s; the model's is 14 s
    (= c_oil / (ua_block_oil + ua_oil_amb) = 12 000 / 860). The oil node is
    4-7x too light, or too tightly coupled -- only the ratio is known.
    thermal.py is NOT changed: it moves the locked scenario.
  - drive10's oil and coolant now read -6.1 K / -4.7 K (off), not agrees.
  - GCC spec: no admissible source for uprated cooling; 50 % stronger cooling
    moves the climb's turbine 0.5 K. REFERENCES.md section 2c.
  - FUEL: the manual says 95 RON minimum, 98 recommended; the model runs 95.
    98 moves only the knock term. Nobody has said which fuel the car was
    LOGGED on -- ask before the retrain.

Altitude is NOT modelled: the scored climb rises 2 340 m in sea-level air.
It is sustained load at sea level, not a mountain.

DO THESE, IN THIS ORDER

1. Run verify_docs.py, test_reward.py (8 of 8) and check_roads.py (PASS) to
   confirm the tree is sound.

2. ASK THE USER two things, then act on the answers:
     - which fuel the car was filled with while it was logged (95 or 98 RON),
       and the manual's page. If 98: refit BaselineECU.knock_limited_spark,
       re-run validate.py and check_map.py (REFERENCES.md 2c).
     - which order: (a) retrain now on the current plant, and again after
       drives A/B; or (b) wait for drives A and B (logs/DRIVE_PLAN.md),
       recalibrate -- including the oil node against the car's 70-100 s
       time constant -- then retrain.
   A plant change after the retrain means retraining again (~3 h each).

3. RETRAIN (only with the user's go-ahead -- it occupies the machine):
       python train.py --steps 50000 --seed 0..4
       python train.py --steps 50000 --seed 0..4 --no-preview
   Ten together, OMP_NUM_THREADS=1 each; ~3 h on the 20-core box.

4. SCORE ONLY WITH evaluate.py. Twenty frozen episodes, paired by seed, three
   rows (sighted, blinded, current-grade), and damage two ways: total and
   turbine + oil. Adding that second column is a reporting change, not a
   change to training or the episodes.

5. Update results/, make_figures.py, make_page.py and republish the page
   (Artifact, same file path results/page/index.html).

6. Merge origin/JMF-2340550-sep17 before reporting Phase D. The code it needs
   is already here; the merge is documents and history.

IF A NEW DRIVE CSV ARRIVES
   Follow logs/DRIVE_PLAN.md and CLAUDE.md's routine: new_drive.py, then
   build_dataset.py, compare_log.py, model_vs_data.py, validate.py. Drive A ->
   fit the oil node with the block pinned to measured coolant
   (model_vs_data.oil_identification), re-check ua_block_oil jointly, and
   require the car's oil time constant (validate.py row 9) to come out too. Drive B
   -> refit boost_ceiling_kpa at low flow and retire the gearbox workaround.
   Drive C -> re-run the knock comparison on readings, not rows.

HOUSE RULES THAT ARE NOT NEGOTIABLE
- The car is read-only. Nothing is ever written to its ECU.
- Run verify_docs.py before quoting any number. Never edit its expected
  values to make a check pass. When a figure changes, grep the tree for the
  OLD value yourself -- including sections marked RETIRED-OK, which the
  checker skips.
- Never edit logs/raw/ or data/ by hand. Regenerate with build_dataset.py.
- After changing the env, the plant, the gearbox, the reward or the roads:
  test_reward.py AND check_roads.py, output pasted into the commit message.
- After changing plant.py or thermal.py: validate.py and validation_table.md
  in the same commit.
- After any change under app/: python -m app.test_replay (49 of 49; --full
  59 of 59) in the commit message. A moved pin gets its reason written beside
  it, never a silent update.
- Count READINGS, not rows: the logger polls one channel per row.
- Cite nothing from memory. REFERENCES.md grades every number.
- One change at a time, each with its measured effect.

OPEN QUESTIONS WORTH YOUR ATTENTION
- The 850 C trigger cannot be validated on this car: every pre-catalyst
  exhaust channel reads zero. It needs a published source.
- Enrichment's worst cell (4500-7000 rpm, 4-8 s) is 0.076 lean; the dwell
  constants were fitted on a retired axis and are too thinly supported to
  refit. Irrelevant to Phase D (the climb never enriches).
- The knock-retard p99 (9.8 deg) was filtered with `Actual gear`, which clamps
  at 6 (mistake 18). Re-derive it from the inferred gear before quoting it.
- presentation/ is marked out of date and needs a rewrite, not a regeneration.
- AUDIT.md open items: M6 in part, M15, L8.
```

---

## Files the next session should read, in order

| file | why |
|---|---|
| `CLAUDE.md` | the handoff, the mistake log, the improvement plan. Current-state boxes at the top |
| `handoff.md` | what to run first and what each command prints today |
| `SESSION_REPORT_2026-09-28.md` | 21–28 September in full, including the validation table's move onto car data (section 6) and the GCC / fuel check (section 7) |
| `validation_table.md` section A | how each of the eleven rows is scored, and why rows 8–11 use our own drives |
| `logs/DRIVE_PLAN.md` | the three drives still worth making, and how |
| `results/phase_d_130kmh.txt` | the latest scoring of the existing agents, with its caveats |
| `AUDIT.md` + `AUDIT_FIXES.md` | the 15 September review and what was done about it |
| `REFERENCES.md` | where every number comes from |
| `CHECKPOINT.md` | dated snapshots, newest last |
