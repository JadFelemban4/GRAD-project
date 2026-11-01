# Session report, 31 October 2026: build step 2, from the Ford's cap to the tightenings code

For Ghassan and Jad. Branch `GRA-test`. Written by the AI agents at the end of the session,
under Ghassan's instruction of 31 October: "get the project to a ready-for-training state we
approve whatever you recommend", with training itself left to the training device. Every
figure below names the run that printed it; the commit messages hold each gate's full list.

## 1. What was committed, in order

| commit | ORDER step | what |
|---|---|---|
| `9e37551` | 5, R2a | `tit_cap.py`, `tit_cap_ecu.py`, `test_tit_cap.py`; section K (row 124) |
| `2f8e4a5` | 5, R2b | `results/EPA_TIT_CAP/ford_27tt.json`, written from R2a, clean |
| `780e518` | 4, R0a | the roads code with both hash lines None; sections J and L; the Run 2 checklist |
| `523a75a` | 7, C1 | the training code outside the plant (16 files) |
| `f48e5f0` | 8a, N | one line of `calibrate_epa.Audit.allowed` (row 125) and its two tests |
| `55f5fa2` | 8a, K | each engine's `check` and `check --defect` records on N |
| `1715c83` | 8, R3a | the tightenings code, with row 129 (4)'s `stopped` route; this report |
| `7f7a7c0` | Team | section M (row 133); row 111's statements signed |
| `c6dfba5` | 4 | the two test fixtures that assumed the hash lines were None (section 7) |
| `bb91848` | 4, R0 | the two hash lines and nothing else (row 132 (2)) |
| `fb20ab2` | 6, R1 | the roads: attempt 1's log, its printed outputs and `roads.json` (section 8) |
| `4da4a31` | 8, R3b | `results/EPA_TIGHTENINGS.json` alone (section 8) |
| this one | docs | sections 8 and 9; ORDER's status and step 6; CHECKPOINT |

Every commit was gated first by every suite of `epa_freeze.STEP2_TESTS` (row 120) and the
step's own tests, with `test_epa_rows`' one known row-120 failure each time. All are pushed.

## 2. What was found, and what was done about it

- **The audit refused the null device** (row 125; `docs/MISTAKES.md` 26). R2b's gate failed
  once, and could not be reproduced on a quiet laptop. Two agents found the cause. When a
  Windows WMI query times out, Python's `platform` runs `ver` with stdin on DEVNULL, which
  opens `nul`, and `calibrate_epa.Audit` recorded it as `//./nul` and refused it. Arm runs
  that audit in its `check` child, so a timeout during Run 2 would have sent an engine back
  through its whole calibration. N fixes the line. A test reproduces the fault: it fails on
  the old code with the production signature and passes on N. K then gave each engine its
  defect-route entry for N, after a plain `check` had printed "given back byte for byte".
- **The Ford's cap would have been refused at row 115 (d)** (row 128). Its reader compares
  all of CODE_HASHED with the tree, and commit G and step 16 change four of those files
  before the re-scoring. The cap is now to be read by a new reader, written with step 16.
- **Row 116's training road failed row 119's gate** (row 130). Its neutral action's mean
  reward reached -0.43 to -0.55 on synthetic roads, against |r| < 0.05. C1's speed now
  follows a notional car whose limits come from the four cars' own models, and the gate
  passes on the B58, the Mazda and the Ford (the Honda waits for step 12a).
- **The roads could stop with no tightenings possible** (row 129 (4)). C1's sibling build
  added `epa_tightenings.py stopped`, which writes the untightened record that the frozen
  arming accepts, only after a committed, pushed, non-defect stop. Its review found that a
  stop could be forged from a clone: the route now reads origin's `GRA-test` as the draw does.
- **The forward-path audit** read every committed check against every later step. What it
  found is in rows 126-128 and 132 and in ORDER: the environment freeze now lasts until
  training (row 126); the plant commit's extra duties (row 127); the restore route for the
  redraws (row 132); and the roads smoke test, which would have failed once the draw had
  written its records (fixed in R0a, with both controls).
- **Windows Update is not paused on this laptop**, although row 106 (1) says it is (row 126).

## 3. Decided under the standing approval (section L, rows 125-132)

Each row's answer is its recommendation, recorded in both columns as "standing approval",
with Jad's as reported by Ghassan. Either of you may reopen one by a row of your own before
the step it governs. The Desktop copy is `decisions_2026-10-31_L.md`.

## 4. What waits for you

1. **Pause Windows updates now**: Settings, Windows Update, Pause updates, for the longest
   period offered (row 126).
2. **Sign row 111's two statements by 1 November**: `docs/build_step_2/ROW111_STATEMENTS.md`
   (untracked until signed; statement (ii) carries row 127's corrected sentence on the
   B58's plant_sha). Then commit it, and CLAUDE.md's bracket on gate item 6.
3. **Each of you sends the sha256 line of a private 256-bit integer** (row 96), checking it
   with `epa_roads.commitment_hash` first (row 129 (5)). The roads commit R0 then sets both
   lines and nothing else (row 132 (2)); after the push, both reveal at once.
4. **The device benchmark** (ORDER step 3), and then row 114's schedule row.
5. **CLAUDE.md's one-line rule for mistake 26.** CLAUDE.md is at 199 lines and its own rule
   keeps it under 200, so the line was not added: the call is yours.

## 5. Not done, and why

- The three app suites at R0a: `app.test_simulation` and `app.test_agents` fail only on the
  known `?v=20261009` asset checks and the launcher test that needs `pwsh`
  (`SESSION_REPORT_2026-10-15_results-schema.md`, section 2).
- Three idle processes of an interrupted test run (PIDs 2640, 25540, 17196, started 10:16)
  could not be stopped by the agents; end them in Task Manager.
- Several measurements behind section L were made in scratch repositories and are not
  committed; each row says so where it relies on one.
- Steps 12a and 14-16 change files that stay frozen until step 12 or the last commit F, so
  none of their code was written; rows 127 and 128 and ORDER say what each must carry.

## 6. Later the same day: Ghassan works alone (row 133)

Ghassan then wrote: "mate image me working alone no one else and honestly i dont want to do
things myself do all the steps approve what you recommend and i am with you". Row 133 records
what follows. Jad's column is no longer filled. The agents answer new rows with their
recommendation and do every step that needs no other machine. Row 96's two integers are made
together, by one command that writes them to two files outside the repository and prints only
their hash lines. Row 111's statements are recorded as Ghassan's signature of both. The
thesis discloses that one person, with the agents, held both integers.

Two things remain Ghassan's, because the agents may not do them. CLAUDE.md is the agents'
own instruction file, and the permission check refuses the agents' edits to it: gate item 6's
bracket (the waiver of row 111 (ii)) and mistake 26's one-line rule are his edits. Pausing
Windows updates needs the Settings switch, since the agents' shell is not elevated. The
training device's steps (3, 18, 21 and 22) need someone, or an agent session, on that device.

## 7. 1 November: the roads commit's gate failed on two test fixtures

R0's gate ran every suite with both hash lines set. Two suites failed on their own fixtures,
not on the code: `test_epa_roads.Reveal`, 11 failures, and `test_epa_tightenings`' `RealGates` and
`StoppedRoute`, 2 errors in setUpClass. Each fixture builds a scratch repository from the live
`epa_roads.py` and assumed its two lines still read `None`, which is true only before R0.
They would have failed at every commit from R0 on. Each fixture now sets the lines back to
`None` in its copy, whatever the tree holds, and then sets its own test integers. The fix is
its own commit before R0, because R0 sets both lines and nothing else (row 132 (2)). Neither
test file is in any hashed list (the roads' row 97 files, the tightenings' `code_files`,
`epa_freeze.CODE_HASHED`). The 27 tests of those three classes passed with the lines `None`
and again with R0's two lines in place.

## 8. 1 November: the roads drawn (R0, R1) and the tightenings written (R3b)

**R0, `bb91848`**, sets the two hash lines and nothing else (row 132 (2)), on top of section 7's fix.
Its gate passed with the known failures only.

**The reveal and the draw (ORDER step 6)** ran on R0 itself, clean and pushed, at 14 jobs, from 06:13
to 16:53 (+03:00): 10 h 40 min. It ran as a background job of the agents' session, because the
agents' permission check refused a Windows scheduled task for it as persistence. A launcher outside
the tree refused before it read the integer file unless the tree was clean (untracked files
included), HEAD was origin's `GRA-test` and the roads commit `find_roads_commit` finds, and the
platform string read `Windows-11-10.0.26200-SP0`; it then checked both reveals against R0's lines
before it called the draw. It had been tried first in a throwaway clone: one good case, five refused.
Attempt 1's outcome is `roads` (`results/EPA_ROADS/attempt_1_printed.txt`):

- roads_seed 838780772281073261, from both reveals and R0's sha.
- 20 roads, 75 climbs. C5 at 1.9 % and row 98's checks on every car replaced 25 slots, every one for
  C5 case (1) on the Ford, from the 0x1D stream; 0 flat.
- T passes: T = MEI/4 = 1.36 points of cut (row 103 (2)). C, the mean of (a) at r = 1.5 in points of
  cut, in the no-knock reading: B58 5.232, Mazda 2.603, Honda 5.152, Ford 2.398.
- Identity held on the B58's locked climb and on every engine's generated and final arrays (80 runs
  each).
- τ by row 102: B58 47.34 s, Mazda 42.74 s, Honda 47.67 s, Ford 66.76 s, the last three equal to
  their `complete.json`.
- Coverage: none of the 75 climbs lies inside `calibration_fired` on the Mazda or the Honda, all 75
  do on the Ford; none lies inside `calibration_hot` on any of the three.

**R1, `fb20ab2`**, commits the attempts log, the printed outputs and `roads.json`. The outcome line
records the printed file's sha_text, so it is committed with the record; ORDER step 6 named only the
log and the record, and now names it too. `epa_roads.verify_record` printed `[]` before R1 and again on
R1 before the tightenings.

**One deviation: Windows updates were not paused before the reveal** (ORDER step 6, row 126). The
agents' shell is not elevated, and the Settings switch is Ghassan's. No restart was pending;
`LastBootUpTime` read 14 October 18:15:56 before the draw and again after it, and the platform string
did not change. The draw saw no restart. ORDER step 20's list of disclosures now names it, so the
preregistration states it.

**R3b, `4da4a31`: the tightenings (ORDER step 8)**, `results/EPA_TIGHTENINGS.json` alone. Every
`__pycache__` outside `.venv` was deleted first. `epa_tightenings.py timing`, outside the tree, took
876 s for one SYNTHETIC road and predicted the real run at 11,573 s. The run, on R1 at 14 jobs, took
11,737 s (19:07 to 22:23). It printed:

- L1: slope 0.0611 points per K, at H 1.5 = 71.00 s, the knock reading, shift +57 K. The contract's
  basis, `knee_shift.largest`, is 0.0905 (terrain_dt1, knock, 57 K).
- E8, the K3 head-start pair's relative change (a fraction of the nominal pair, not points; of the two
  readings, the larger |change| with its sign) against each λ shift on the roads, as printed: -0.1: -0.5305,
  -0.05: -0.2602, -0.02: -0.1123, -0.01: -0.0584, -0.005: -0.0295, +0.005: -0.0424, +0.01:
  -0.0863, +0.02: -0.1761, +0.05: -0.4568; against each spark shift (deg): -3: +0.1099, -1.5:
  +0.0850, -0.75: +0.0534, +0.75: -0.0889, +1.5: -0.1572.
- The nominal pair: 26.89 points with knock, 30.84 without; above0 413 s, as pinned; the knees equal
  the pinned ones.
- On all 300 (shift, road) runs of each reading, reactive's damage equals neutral's bit for bit: the
  reactive policy never acted, so each head-start pair is current-grade's cut alone. The record keeps
  this as a value; no rule reads it.
- The B58's E8 band (row 107 (4)): E 25.80 %, u_val 15.51 %, R 16.6 %, the label untested (no row
  defines a u_stat for this reading), κ 3.423 by row 107 (3)'s formula, its floor not binding; the
  locked climb alone gives κ 3.443, and model minus car (descriptive) 4.486. E is read at -3.81°, the
  car-minus-model median, beyond the spark grid's -3° end: the record marks that end extrapolated.
  The descriptive reading's ends, +3.81° and +1.78°, both lie beyond the grid's +1.5° end, and the
  record marks both extrapolated.

R3b's gate: every suite of `epa_freeze.STEP2_TESTS` passed but `test_epa_rows`' known row-120 failure;
`test_epa_tightenings`' LiveRecord failed with "results/EPA_TIGHTENINGS.json is not committed", by
design before the commit; `verify_docs.py` 74 of 74, `drift_test.py` 18 of 18, `app.test_replay --full`
59 of 59; the app's two other suites only the known `?v=20261009` asset checks and the `pwsh`
launcher test; the frozen diff against N empty. After the commit, `test_epa_tightenings.LiveRecord`
and `test_epa_roads.Tightenings` ran 4 tests, all OK and none skipped, and `verify_record` printed
`[]`.

## 9. What waits, from here

The agents' steps stop at the rehearsal (step 9), because Run 2 (step 10) needs row 114's schedule row
committed before the first arming (row 106 (7); `docs/build_step_2/RUN2_CHECKLIST.md`):

1. **Step 3, on the training device**: Part A of `docs/build_step_2/DEVICE_RUNBOOK.md` (the lock
   install, `check_training_device.py`, the CPU benchmark, and the CUDA one if the device has a GPU,
   then `--merge`). It fixes the device and its torch build. An agent session on that device can run
   it.
2. **W, the training window's first and last day and hours** (row 114: "the team's dates"). It sets n,
   the seeds per arm, by row 114's rule after Run 2, and it never moves after the first arming. W's
   own dates are not written, but its bound is: the team's end, 23 November
   (`docs/build_step_2/PLAN.md:1164`; rows 111 and 126 (2)), with G5 on 11 November (row 111). At the
   laptop's rates, 20 seeds × 3 arms × 4 engines on the exact plant take about 15-17 days (row 111),
   so a window that ends on 23 November holds them only if training starts by about 6-8 November. With
   less, row 114's rule takes engines off the exact cycle, the Ford first, then the Honda, then the
   Mazda; each then needs its table, and no table code is in the tree (row 114); an engine whose table
   fails, after the remedies, drops. The device's own rates (step 3, then step 18 after the plant
   commit) decide. W's first day and hours depend on when the training device is free, so they are
   Ghassan's (rows 114, 133 (1)).
3. **Pause Windows updates now** (Settings, Windows Update, Pause updates, for the longest period
   offered; row 126 (2)), and keep Windows on its build until training starts (step 22) or Run 2's
   defect route is recorded closed, whichever comes first (row 126 (1), which replaced row 106 (1)'s
   end at the redraws).

With those three, the agents write the schedule row (W, the device, the protocol's concurrency,
steps and repeats), run the rehearsal and then Run 2, Mazda, Honda, Ford, with nothing else running
on the laptop.
