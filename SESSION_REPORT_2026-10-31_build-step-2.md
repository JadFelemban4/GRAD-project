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
| `f0ecf92` | docs | sections 8 and 9; ORDER's status and step 6; CHECKPOINT |
| `91c6ece` | 2, 3 | section N (row 134: W); `tools/device_step3.sh`; the runbook, ORDER, the Run 2 checklist, CHECKPOINT; section 10 |
| `b2151af` | 3 | Jad's: `tools/device_step3.sh` reads a newer driver's "CUDA UMD Version" line; his audit of step 3's path |
| `0fbc744` | 3 | Jad's: the record of step 3 on his PC (section 11) |
| `fefb7af` | (C0) | two `ScoredShareSYNTHETIC` fixtures that failed from R0 on (section 11) |
| `008f69f` | 7's rule, C1b | the benchmark protocol (row 135 names it): `--roads-record`, `--reward-knock`, B0/B1/B5 |
| this one | O1 | section O (rows 136-143), `docs/build_step_2/INTERFACES.md`, ORDER steps 12a-22, the cap README, CHECKPOINT; section 11 |

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

## 10. 2 November: W fixed (row 134), and step 3 made one command

**Ghassan's inputs.** The training device "has 5070 12gb ram", read as an RTX 5070 with 12 GB of video
memory; then "Memory: 32 GB DDR5; CPU: Ryzen 5 9600X or stronger"; and "training wind is hard to
give". He ended the three processes left hung since 31 October (PIDs 2640, 25540 and 17196; no
python.exe was running afterwards). The agents removed the empty `GRAD-step7` folder from the Desktop.
Section 9's item 2 is answered by row 134; items 1 and 3 still wait.

**W (row 134, section N).** 10 November 2026, 00:00 AST, to 20 November, 00:00: 240 hours of the
device's time, 24 hours a day. The agents set it under row 133 (2). The calendar chose it, not any rate:
the likely start is about 8 November, 10:00, with about 38 h of margin (the chain is in the row), and
W's end leaves 72 h before the team's end on 23 November. W falls after G5, the analysis freeze of 11
November. No four-engine result can exist by then under any start the steps allow, so moving G5 in
Notion is Ghassan's. Row 114's schedule row is now committed in two parts: W now, and the device, its
torch build and the protocol in row 135 after step 3. If CUDA cannot run on the card, the device is the
CPU (row 134 (3)).

**What W affords, for planning.** Four engines on the exact cycle at 20 seeds per arm need at least 125
steps/s across all runs at once in 240 h: 125 at a concurrency that divides 60 (12 or 6 at once on a
9600X, whose 6 cores and 12 threads are ASSUMED from its specification), more at one that does not (133
at 16, 144 at 23). The laptop's best many-run total is 82.4 steps/s (X1): 0.66 of 125. The plant runs on one CPU core
per run and was 84 % of a step on the laptop, so the device's CPU sets the rate, not its GPU. If step 3
shows the rule binds, it takes the Ford off the exact cycle first, and row 107 (6) says the agent study
then does not test H/τ against H. No table code exists, and changing the order or dropping without a
table is new contract text outside section I's list. Row 134's Why leaves that to a row of its own,
before the rehearsal, once the rate is known.

**Two findings on the way to the device.**

- *The CUDA build.* Of the nine PyTorch indexes queried, torch 2.14.0 is on cu126, cu130 and cu132 only,
  not on cu128 or cu129 (MEASURED, `pip index versions`). A plan drafted earlier in this session named
  cu128 for the RTX 5070, and it would have failed on the device. The card needs cu130 (a driver for
  CUDA 13.0) or cu132.
- *The lock's own install fails its own check.* The lock's header installs torch from `/whl/cpu`. A
  fresh install made that way reads `2.14.0+cpu` in its metadata, and `check_training_device.py` stops on
  it: "torch 2.14.0+cpu (lock: 2.14.0) <-- DIFFERENT, critical" (MEASURED in a throwaway clone). The
  laptop's own torch came from PyPI. Its metadata reads `2.14.0`, and its binaries are the same:
  `torch_cpu.dll` and `c10.dll` equal by sha256, the file lists equal. On Windows the device now takes
  torch from PyPI with the rest of the lock (`DEVICE_RUNBOOK.md`, A1). The lock is frozen until step 12,
  so its header stays as it is.

**`tools/device_step3.sh`.** Part A in one command:
`bash tools/device_step3.sh --python <python 3.13.2>`, from a clean clone at a pushed `GRA-test`
commit. Before its first long step it checks:

- the interpreter (3.13.2, 64-bit, not free-threaded);
- the clone (clean, pushed, carrying C1);
- nvidia-smi, the card's compute capability and the driver's CUDA version;
- the CUDA index;
- the free disk;
- the lock's environment against the lock (A2);
- the CUDA environment's exact build, and the CUDA probe.

Then it runs the selftest, the CPU benchmark, the CUDA benchmark and the merge, each with
`--window-days 10`, and packs everything into one `.tar.gz` to bring back. It asks Windows to keep the
machine awake while it runs and logs that request. It refuses Linux, where A1 has no route yet.

*The smoke tests* (`--smoke`: the benchmark's `--quick` at one concurrency, one repeat, no merge) ran on
the team laptop on 2 November, each in a throwaway clone that pushed to a throwaway bare repository, so
the script's own checks for a clean, pushed clone carrying C1 ran for real. The CUDA path ran on the
laptop's RTX 3050 Ti, compute capability 8.6, with a driver for CUDA 13.0. The first run stopped at A2
on the lock-install defect above. The second stopped on the smoke-only `--steps 300`, which is below the
benchmark's 1000-step minimum. The third ran to the end on the first version of the script. The fourth,
on the version committed here, also ran to the end, exit 0:

- the checks;
- A0-A2 ("VERSIONS: match the lock");
- the CUDA environment, torch `2.14.0+cu130` with CUDA 13.0, and its probe, before any long step;
- the selftest;
- the CPU benchmark, "cpu: IDENTICAL";
- the CUDA benchmark, "cuda: IDENTICAL";
- A6;
- the archive;
- the keep-awake request, which returned a non-zero state, and the loop, which ended with the script.

A negative test, `--cuda-index cu132` on that card's CUDA 13.0 driver, stopped in the checks as it
should. The smoke numbers decide nothing: `--quick`, and the laptop had 3.6-4.9 GB of memory free
(Windows Explorer held 8.1 GB), so no concurrency "fitted at 450 000-step size". One reading is still
worth keeping, the third run's section 2 on the CUDA build: the plant step took 64.39 ms against the
SAC update's 10.67 ms, "the plant is 85 % of a step". That is the current plant, against the 84 % of
29 September.

**The reviews.** The plan behind row 134 came from four read-only reports and three adversarial
reviews. The drafted row, script and documents had three more reviews: 40 findings, one blocking (the
smoke steps below the benchmark's 1000-step minimum, which the smoke test hit too). The material ones:

- an outcome that ignored row 114's table branch;
- a pointer to a crash rule that exists nowhere (ORDER step 20 now lists one, since X1's and X2's
  disagree);
- G5 not mentioned;
- a CUDA verdict read from any failure, not from the probe's own;
- the CUDA probe placed after the multi-hour CPU benchmark;
- a missing nvidia-smi read as "no GPU";
- a later row that would change the order of leaving without saying it is a contract change.

All were applied.

## 11. 2-5 November: step 3 on Jad's PC, the order of leaving (row 136), and the interfaces of the code still to write

**Step 3 ran on Jad's PC on 2 November**, by `tools/device_step3.sh` at `b2151af`, 13:37-14:46 AST
(Jad's record, `docs/build_step_2/STEP3_RUN_2026-11-02_JAD_PC.md`, `0fbc744`). His agent first fixed the
script: driver 617.42 prints "CUDA UMD Version: 13.4", which the pre-check did not read (`b2151af`,
with his audit). The PC had Python 3.13.15, and he installed 3.13.2 from python.org's NuGet package
beside it; `check_training_device.py` printed "VERSIONS: match the lock". The machine: a Ryzen 5 9600X
(6 cores, 12 logical), 31.2 GB of RAM, an RTX 5070 (12 227 MiB, compute capability 12.0), Windows 11 Pro
10.0.26300. The merge: "CPU with 12 runs at once (torch 2.14.0+cpu): its lowest lower bound, 106.19 (12
at once), beats CUDA's highest upper bound, 70.87 (6 at once)"; seed 0 trained identically twice on
both devices. 12 of the 14 rows started with the CPU 4-13 % busy (the IDE stayed open), the merge's one
caution. As a planning figure (the B58's rate on the extremes road, times four engines): 20 seeds per
arm take 11.8 days on four engines, and at most 16 fit W. With row 136, the Honda leaves, and three
engines at n = 20 take 15 waves of 450 000 / 8.85 s, about 212 h of W's 240 (arithmetic). The binding n
comes from each engine's rate at step 18.

**Row 136 is Ghassan's own answer, 2 November**, to "If the new device is too slow to train all 4 engines
x 20 seeds x 3 arms by 20 November, which engines give way?": "Keep the Ford (Recommended)". The Honda
leaves first, then the Mazda, each dropped with no table; "B58 + Ford is the minimum", which he
confirmed the same day reads: if even those two cannot reach 20 seeds per arm, the four-engine test does
not run and that is reported (MD:1611-1612). The agents proposed both readings as the recommended
options. It is contract version 6 for the order of leaving and the table route only, written before
step 3's rate was known. No table code is ever written.

**Section O and the interface sheet.** Eight read-only specs of the code still to write (C2, P in four
parts, G, V, T), a critic of them as a set, eight resolutions of their 88 open questions, one
consolidation, then five rounds of adversarial checks of the sheet, the rows and C1b, every blocking and
material finding applied (each round's findings are in the sheet's section 16). The three blocking conflicts the critic found first:
P's own re-verification would have refused P (P must edit `evaluate.py`); P's reader and T's writer
disagreed on `results/EPA_BACKEND.json`; and the benchmark protocol had to be frozen before Run 2 while
P edited it. The sheet, `docs/build_step_2/INTERFACES.md`, now fixes one definition of every shared name
and one owner of every shared edit, and ORDER's steps 12a-22 follow its commit order.

**C0 and C1b.** C0 (`fefb7af`) fixes two `test_four_engine_training` fixtures that had failed since R0
(`bb91848`): they mocked the commitment lines one way only, as `c6dfba5` had fixed for two others. That
suite is not in `epa_freeze.STEP2_TESTS`, which is why no gate showed it. C1b (`008f69f`) is the benchmark
protocol: `--roads-record` with the share on and decision 29's recipe but its average, `--reward-knock`
from P on, B1's attempts written outside the repository (inside it, every attempt would have recorded a
dirty tree), the CPU series on CUDA, B0's record. `--road extremes` stays byte-identical to the script
step 3 ran.

**The two measurements of the interface sheet's S** (for row 135, on scratch drafts, never pushed):
- the blinded arm bit for bit (row 117): on a minimal draft of P1's H parameter, 9 values of H gave one
  trajectory bit for bit on decision 34's road, the extremes road and the four-engine road, and a short
  training blinded at two H gave identical parameters (368 399 values) and replay buffer; the sighted
  control differed; the four engines' defaults equal their pinned digests (`test_preview_horizon.py`,
  14 tests OK). So three arms stay three;
- the SYNTHETIC part of the Honda's row-119 gate, on a scratch draft of C2: all 9 check lines PASS, and
  `check_training_device.py --compare` of the B58 before and after the draft read "VERDICT: IDENTICAL
  TRAINING" (96 tensors, 47 record fields).

**A stop.** The agents' usage limit stopped the work from the evening of 2 November to 5 November.

**Conventions and stale citations, recorded here and in no row** (the interface sheet's request):
- a line of `results/VALIDATION_DECISIONS.md` is cited as it stands in the commit that lands the citation,
  or by row number: O1's provenance line moves every VD line from :69 on by 4, O2's by 3 more (section I's
  note: :343 at `91c6ece`, :347 from O1, :350 from O2); a step of ORDER is cited by its number;
- code that C0 or C1b moved is cited by name from that commit on (`benchmark_training.py` throughout;
  `engine_gate.py`'s WHAT WAITS bullets; `test_device_gate.py`'s classes);
- stale, not edited: row 134's "(VD:340)" (the note is :343 at `91c6ece`) and its
  `benchmark_training.py:36-38` (moved by C1b; the paragraph "A training step is two jobs"); row 114's
  `benchmark_training.py:89-90` (now `bounds`); row 107 (5)'s and row 114's `train.py:487` and
  `benchmark_training.py:752-753` (row 139 (5) records where they point);
- read through row 136 and not edited: row 114's order of leaving and table route, row 134's "Not this
  row" passage, row 107 (5)'s S2b pilots, and `validate_epa.DROP_ORDER` (`validate_epa.py:165-167`,
  CODE_HASHED, kept; the schedule's order is `epa_backend.DROP_ORDER`);
- `results/training_roads.json` (`cbb8d09`) differs from what both `91c6ece` and C1b regenerate: an older
  drift, not C1b's.
