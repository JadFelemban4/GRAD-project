# Prompt for the next chat

Copy everything inside the fence into a new Claude Code session opened in
`C:\Users\badcl\Desktop\GRAD-project`. Written 28 September 2026 (evening).

---

```
Continue the BMW B58 graduation project. Read CLAUDE.md first — it is the
handoff and the mistake log, and its FIRST current-state box (28 September,
evening) is current. Then handoff.md (the short entry point) and
SESSION_REPORT_2026-09-28_evening.md (the last session in full).

WHERE THINGS STAND

The working tree on branch JMF-2340550 may carry the evening's work
UNCOMMITTED — check `git status` first and ask the user before committing.

1. DRIVE B IS IN (logs/raw/driveB_rollons-20260928_140513.csv): full-throttle
   roll-ons in held gears. Dataset 321.7 min, eleven drives, eight carrying
   samples. It logged no ambient temperature and no oil.

2. THE DATA SETS THE CONSTANTS. derive_params.py recomputes everything the
   car's logs can set -> data/derived_params.json -> read through derived.py by
   thermal.py, plant.py and engine_env.py. build_dataset.py runs it at the end.
   Derived: the thermal block + oil nodes (calibrate_thermal.py), the boost
   ceiling (it IS the measured envelope now, no formula), SPARK_A, ENR_DWELL_LO
   / HI, the gearbox's DELIVERABLE_TORQUE, MAP_CEIL_KPA. What cannot be derived
   and why: REFERENCES.md section 4b. A NEW DRIVE CHANGES THE PLANT, and a
   plant change after the retrain means retraining.

3. THE OIL NODE WAS RE-STRUCTURED from the data: heated by engine speed,
   cooled by road speed (it was 5 % of fuel, constant cooling). Oil tau 14 ->
   57 s. validate.py 8 of 11 (6/7 literature, 2/4 car). Rows 10-11 (coolant)
   pass; rows 8-9 (oil) still miss — 97.0 C vs 103-111, 60 s vs 70-100 — and
   that was NOT tuned away. Drive A is the data that would settle it.

4. THE PREMISE on the derived plant: baseline 920.1 at 883 C, current-grade
   520.5, predictive 523.5; preview over current-grade -0.3 (it was -0.4 and
   did not move through any of the evening's changes). results/premise.json.

5. The Phase D retrain is READY and NOT RUN: TerrainTrainingEnv, dt = 1.0,
   output runs/terrain_dt1/. The ten agents in runs/ are a record (110 km/h,
   dt 0.2, one road, an older plant).

DO THESE, IN THIS ORDER

1. git status. If the evening's work is uncommitted, run verify_docs.py,
   test_reward.py, check_roads.py and python -m app.test_replay, show the user
   the results, and ask before committing.

2. ASK THE USER:
     - which fuel the car was logged on (95 or 98 RON) — REFERENCES.md 2c;
     - drive A before the retrain, or after. Drive A must log Ambient
       temperature and Oil temperature (logs/DRIVE_PLAN.md).
     - whether to merge origin/JMF-2340550-sep17 now: 7 conflicts, 4 in code
       (engine_env.py, train.py, evaluate.py, verify_docs.py). Resolve code
       toward THIS branch — sep17's engine_env.py has the six-speed gearbox.

3. RETRAIN (only with the user's go-ahead — ~3 h of machine time):
       python train.py --steps 50000 --seed 0..4
       python train.py --steps 50000 --seed 0..4 --no-preview
   Record the data/derived_params.json commit beside the result.

4. SCORE ONLY WITH evaluate.py (twenty frozen episodes, paired by seed; it now
   prints a thermal-only damage column too). Then run_results.py,
   compare_calibration.py, make_figures.py, make_page.py.

IF A NEW DRIVE CSV ARRIVES
   python new_drive.py <file>; then build_dataset.py (which re-derives the
   plant); then compare_log.py, model_vs_data.py, validate.py, check_premise.py,
   test_reward.py, check_roads.py, verify_docs.py. Header capitalisation varies
   between exports — the readers are case-insensitive now. A drive with no
   ambient channel gets build_dataset.AMB_FALLBACK_C and is excluded from the
   charge-temperature check.

HOUSE RULES THAT ARE NOT NEGOTIABLE
- The car is read-only. Nothing is ever written to its ECU.
- Run verify_docs.py before quoting any number. Never edit its expected values
  to make a check pass — only for a measured change, with the reason beside it.
- Never edit logs/raw/, data/ or data/derived_params.json by hand.
- No fitted number typed into a module where the data can set it: derive it
  (derive_params.py) or say why it cannot be derived (REFERENCES.md 4b).
- After changing the env, the plant, the gearbox, the reward or the roads:
  test_reward.py AND check_roads.py, output in the commit message.
- After changing plant.py or thermal.py: validate.py and validation_table.md
  in the same commit.
- After any change under app/: python -m app.test_replay; a moved pin gets the
  change that moved it written beside it (revert one change at a time).
- Count READINGS, not rows. Cite nothing from memory. One change at a time.
- Every comparison gets a figure (make_figures.py).

OPEN QUESTIONS WORTH YOUR ATTENTION
- The coolant regulation law: on the two 41-45 C afternoon drives the car's
  valve runs 82-84 C after load; on drive10's high-rpm stretch it let 97-99 C.
  A fixed stand-in setpoint does neither.
- Road load (mass, drag area, rolling resistance) is typed and unsourced; the
  wheel-torque channel could not identify it. Toyota's kerb weight needs to be
  opened from a spec sheet.
- The 850 C trigger cannot be validated on this car (no pre-catalyst exhaust
  channel).
- generality_test.py now reports preview over CURRENT-GRADE as well as over
  reactive; only the former is a preview measurement (AUDIT.md C3).
- presentation/ is out of date (banner on the page); it needs a rewrite.
```

---

## Files the next session should read, in order

| file | why |
|---|---|
| `CLAUDE.md` | the handoff, the mistake log, the improvement plan. Current-state boxes at the top |
| `handoff.md` | what to run first and what each command prints today |
| `SESSION_REPORT_2026-09-28_evening.md` | drive B, the derived constants, the oil node, every fix — in full |
| `SESSION_REPORT_2026-09-28.md` | 21–28 September (morning) in full, including the validation table's move onto car data (section 6) and the GCC / fuel check (section 7) |
| `validation_table.md` sections A and C | how each of the eleven rows is scored, and what the 28 Sep thermal derivation changed |
| `logs/DRIVE_PLAN.md` | the three drives still worth making, and how |
| `results/phase_d_130kmh.txt` | the latest scoring of the existing agents, with its caveats |
| `AUDIT.md` + `AUDIT_FIXES.md` | the 15 September review and what was done about it |
| `REFERENCES.md` | where every number comes from; section 4b says, constant by constant, whether the data sets it |
| `CHECKPOINT.md` | dated snapshots, newest last |
