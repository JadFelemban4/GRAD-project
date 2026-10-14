---
paths:
  - "build_dataset.py"
  - "extract_steady.py"
  - "compare_log.py"
  - "new_drive.py"
  - "logs/**"
---

# Data: when a new drive CSV arrives

Loaded when a data file is read or edited. Moved verbatim from CLAUDE.md on
14 October 2026 (the documentation restructure, plan v3 phase 4); CLAUDE.md
keeps the two lines that matter before anything runs. In the text below, "the
box at the top" and "the live list under What to do next" now mean CLAUDE.md's
Training gate; the list as it stood is STATE_HISTORY.md part E.

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

