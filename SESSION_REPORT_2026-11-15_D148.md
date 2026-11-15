# Session report, 15 November 2026: B1 pulled, and D148 (rows 148-153)

For Ghassan and Jad. Branch `GRA-test`. Written by the AI agents during D148, under Ghassan's reply of
15 November, "I do D 148". Every figure below names the file and line that print it. Where a figure comes from a
run that is not committed, or from a document outside the repository, this report says so. Jad's own report of
B1 is committed beside this one, unchanged: `SESSION_REPORT_2026-11-14_B1-visit.md`; its last bullet's next job on
the PC, PL-B, is replaced by CK under row 148 (ORDER step 21), and its section 4's "no checkout ... until the
study's training ends" by the visit's checkout of `T*` in that clone (ORDER steps 21-22; INTERFACES section 18's 3).

## 1. What was committed, in order

| commit | ORDER step | what |
|---|---|---|
| `891e29a` | 18, B1 | Jad's: the B58's benchmark on his PC, with B2, B4 and L8; 26 result files and nothing else, pushed from his PC on 14 November (his report, section 2) |
| this one | D148 | section S of `results/VALIDATION_DECISIONS.md` (rows 148-153); ORDER's edits; INTERFACES section 18; in `results/B58H_DESIGN/`, `d148_figures`, `grids_b58` and `hw_opt/`; CHECKPOINT, `STATE_HISTORY.md` part AQ, this report and Jad's; section 23 of the 31 October report, pointing here |

B1 measured Ta's tree: its git_head is `0329456`, and its commit `891e29a` adds only results files on top of
it. So "B1's git_head" is `0329456` and "B1's commit" is `891e29a`. Every gate that diffs the cost files reads
the git_head. Nothing was pushed from this laptop between Ta and B1 (row 146 (6)).

## 2. B1, pulled and reviewed

**The pull.** This laptop took `891e29a` with `git pull --ff-only` on 15 November at 00:39:46 AST (the reflog),
and the tree was clean after it.

**What B1 printed** (Jad's PC, `DESKTOP-VF1MO3H`, an AMD Ryzen 5 9600X with 12 logical CPUs,
`results/benchmarks/B1_bench_b58.attempt1.txt:2-5`):
- Seed 0 trains identically twice on the training configuration: `cpu: IDENTICAL` (`:31`).
- The rate is 107.46 steps/s at 12 runs at once. It comes from repeat 1, which read 107.46 to 108.32 with 2.6 % CPU
  load before it and is not flagged. Repeat 2 read 110.77 to 111.89 with 6.5 % before it, above
  `LOAD_LIMIT_PCT`, so it is flagged `loaded` (`results/B58H_DESIGN/d148_figures.txt:6-10`). Row 135 (4) makes
  `loaded` a flag only, and the flagged repeat was the faster one.
- L8 on the device: PASS. All 11 runs exit 0 (`results/B58_IDENTITY/L8_device/_status.txt:1-11`). The three pairs
  and the wrapper read IDENTICAL, and both relative-step controls read DIFFERENT, as required
  (`_verdicts.txt:1-4`, `:7-8`). The one-ulp controls `ctl_mass` and `ctl_cturb` are printed, not judged, and
  read IDENTICAL (`:5-6`). The printed line "L8 VERDICT: PASS" is in `B3_L8.txt` on Jad's PC, which no step
  commits. The verdict follows from the two committed files by `tools/run_l8.sh`'s rule.
  `results/B58_IDENTITY.md` still reads "pending" for L8. It is not edited (row 146 (6)): these files answer it.
- B4: `Ran 7 tests in 205.508s`, `OK` (`results/benchmarks/B1_device/B4_test_epa_plants.txt:12-14`). Recorded
  only; it decides nothing for this study.
- B2: `VERDICT: NOT IDENTICAL (100 differences)` (`results/benchmarks/B1_device/B2_compare.txt:23`), between this
  laptop, Windows build 26200, and the device, build 26300 (`:1`). Jad counted the 100 from both identity files:
  75 of the 96 weight tensors and 25 of the 47 record fields. The 8 counters, the 9 meta fields and the command
  are equal (his report, section 2). The curve compares nothing, because the 600-step run completed 0 episodes.
  B2 is recorded and decides nothing (decision 32). Its cause is not attributed: the processor, the Windows
  build, the patch level and the Python build all differ between the two machines. PR-B discloses it.

**The training at B1's rate.** 107.46/12 = 8.9550 steps/s per run (`d148_figures.txt:41`). One wave takes
13.96 h (`:42`), and the B58's 60 runs fill exactly 5 waves, 69.79 h (`:43-44`). Step 3's 106.19 gave 70.63 h, so
B1's training is 0.83 h shorter (`:46-47`). That gain is not margin to plan on: the 3000-step benchmark never
reaches a checkpoint save, so the time to write checkpoints is not in it. A sixth wave, after a crash or a restart,
adds up to 13.96 h (`:48`). The benchmark's own "x 4 engines" line multiplies by `ENGINES = 4`
(`benchmark_training.py:200`), not by the engines that train, so it is not this study's schedule
(`d148_figures.txt:45`).
`benchmark_training.py` is a cost file, frozen since C1b, so that display line is on the post-study list
(CHECKPOINT, item 13). Ta's code already writes into the backend record a note that those lines are not this
schedule (`epa_backend.py:898-899`).

**The review.** Five reviewers and two skeptics read B1 on 15 November, read-only. Their file is on the Desktop,
"B1 review (15 Nov 2026).md", and is not in the repository. What it found and this report keeps:
- Ta's own backend builder, run read-only on this tree, accepted attempt 1 as the measurement, with no crash, no
  superseded attempt and no operator fault. That run printed nothing that was committed. Tb's
  `epa_backend.py write` makes the record.
- B0's two raw code hashes are the CRLF forms of Ta's files, as step 3's were of its commit's. The backend compares
  them only with the same device's own B0 record, never with this laptop's (`epa_backend.py:75-77`). Every FATAL
  fingerprint field is independent of line ends (plant_sha and backend_contract read CRLF as LF, `fingerprint.py:477`
  and `thresholds/common.py:37-43` at `891e29a`; derived_sha and engine_sha hash values), and B2's meta (plant_sha, derived_sha, engine_sha) is
  equal on both machines. So line endings do not cause B2's differences.
- B2's 22 equal record fields include every road input (grade, speed, rpm, gear, the torque request, the ambient
  temperature) and every field of the baseline ECU's run. The differences start at the agent's action. In the
  review's reading, the plant runs bit for bit alike on both machines and torch's arithmetic diverges. Where the
  first difference falls was not measured: the identity files hold hashes only, and `--identity` deletes its runs.

## 3. Jad's deviations at B1, recorded

Jad listed six differences between the B1 sheet and his PC (his report, section 1). None of them invalidates a
figure: every device number this study uses was measured at B1 itself. That covers the rate, the determinism check,
L8, B4 and the versions, all measured after the updates of 11 and 13 November, with the update pause set at 19:52,
before the benchmark started (`d148_figures.txt:7`: 19:53:38). B1's environment is the reference for CK and the
training. Step 3's numbers come from an environment that no longer exists, and are history. Its CUDA series was
measured on driver 617.42 and is not measured again; the choice of the CPU does not rest on it.

1. **The clone.** The sheet's clone, `GRAD-project-step3`, was a worktree of Jad's `GRAD-project`, removed on
   11 November at his own request. B1 ran from a fresh clone of GitHub, `C:\Users\admin\grad_device\GRAD-project-device`,
   checked out at Ta by the sheet's step 2. That clone stays at `891e29a`, detached and clean,
   until the visit's sheet checks out `T*` in it: CK and the training run in this same clone.
2. **The interpreter.** Step 3's lock venv was moved out of the worktree on 11 November, to
   `C:\Users\admin\grad-venv-lock-3.13.2`. Its newest `site-packages` entries are dated 2 November 13:38, and the
   sheet's step 3 printed "VERSIONS: match the lock". L8's provenance records the interpreter path
   (`results/B58_IDENTITY/L8_device/provenance.txt:5`).
3. **Windows Update was not paused.** The sheet said it was paused until 25 November. On the PC the pause had
   expired on 1 October. Since step 3, Windows installed KB5132061 (build 26300.9974) and KB5132688 on
   11 November, Windows App Runtime updates on 11 and 12 November, and Defender definitions daily. Step 3 itself,
   on 2 November, also ran unpaused, and no record said so until now. Jad paused updates at 19:52 on 14 November,
   before the benchmark, until 28 November. From now on, each sheet reads the pause from the registry instead of
   stating it, as row 126 (2) did on this laptop.
4. **The IDE stayed open.** Claude Code runs inside Antigravity IDE, which stayed open, as at step 3. It made three
   small edits to Jad's report in the benchmark's first minute and was idle after. Brave, Discord and the Claude
   desktop app were closed before the benchmark.
5. **Line endings.** Git for Windows sets `core.autocrlf=true`, so the clone's work tree is CRLF, as step 3's was.
   It stays so (section 2).
6. **The NVIDIA driver** moved from 617.42 (step 3) to 621.24 (`B1_bench_b58.attempt1.txt:15`), installed on
   13 November. Torch there is a CPU build (`:11`, `:16`), so the driver enters no training. Whether it came through
   Windows Update or NVIDIA's own app is not yet known.

Also recorded: Jad approved the push to `GRA-test` after the destination was named to him; he was told 27 files
before the push, and the commit holds 26 (his report, section 2).

## 4. The hw_opt control record (row 153 (1))

Row 153 (1)'s record is `results/B58H_DESIGN/hw_opt/`, described by its `README.md`. The run itself was made on
14 November, outside the repository, from a clone of Ta at `C:\Users\badcl\grad_hw`. Before D148 its control was
re-printed from the run's cache on 15 November at 01:20 AST, running nothing (`control_record.txt:1-2`). It reads
"CONTROL: largest difference from roads.json 0.000e+00 -> PASS" (`:15`) and exits 0 (`:16`). The same record prints
the clone's HEAD `0329456` with 0 status lines (`:18-19`), the B58's plant_sha there (`:20`), equal to B1's
(`d148_figures.txt:154`), and the environment (`control_record.txt:21`). `run.log` prints no environment.

The 808 runs not already cached took 136.5 min (`hw_opt/run.log:1`, `:59`). The 820 runs are 41 settings on
20 roads (`d148_figures.txt:152-153`).

**The committed script is not exactly the script that ran.** At 19:11 AST on 14 November, after the run ended,
the agents changed two places in `report()`, which only reads the cache (`hw_opt/README.md`, "A change to
hw_opt.py after the run"). As run, past the blind front's last point, `blind_at` returned that point's saving. Now
it returns `None`, "not compared", and the gaps line skips such a point. The report was re-run from the cache at
19:11 and equals the one the run printed, line for line once line ends are ignored. The two cannot differ here,
because no sighted point lies past the blind front's end (the README gives the lines). A reconstruction of the
as-run file is kept outside the repository, in the agents' scratchpad. Any sentence that calls the committed file
"the script as run, byte for byte" is wrong in those two places.

The summary written beside the run on 14 November, `RESULT_SUMMARY.md`, is not committed: it quotes numbers worked
out by hand (rule 1.9).

## 5. D148's files

- **`results/VALIDATION_DECISIONS.md`**: the index entry and section S, with rows 148-153 (148 and 149 procedure,
  150-153 descriptive), from the draft of 14 November, with B1's rate in place of step 3's. In short: a check run
  CK, the pilot's command at 50 000 steps, replaces PL-B for this study (148). The analysis code AB moves after
  `T*`, and PR-B states the whole analysis in words (149). Four descriptive rows stand beside d (150-153).
- **`docs/build_step_2/ORDER_TO_TRAINING.md`** (steps 18a-22b) and **`docs/build_step_2/INTERFACES.md`** section 18.
- **`results/B58H_DESIGN/d148_figures.py.txt`** and its print **`d148_figures.txt`** (154 lines). It uses the
  standard library only and imports nothing from the repository. It reads its inputs from committed files and
  B1's JSON, by name, and prints every figure that rows 148-153 and section S's note quote. Inputs that no
  committed file holds are typed once, each printed with its label (ASSUMED, DEFINED or stated) and its source.
  It checks its output before writing it: ASCII only, no run of 12 or more digits, no 40- or 64-character hex
  value, no guarded field name. Two runs gave byte-identical output. It reads no VD, ORDER or INTERFACES text, so
  D148's edits to them cannot change what it prints.
- **`results/B58H_DESIGN/grids_b58.py.txt`** and **`grids_b58.txt`** (111 lines), moved from AB because AB now
  comes after `T*` (point P13). The grid equals the study's ceiling C at r = 0.5 and 1.5 (`grids_b58.txt:29-30`),
  and its three mean spreads equal `power_b58.txt:44-46` (`grids_b58.txt:94-96`).
- **`results/B58H_DESIGN/hw_opt/`**: section 4. Each `.py` is renamed `.py.txt`, so no scan of committed `.py` files
  runs it.
- **CHECKPOINT.md** rewritten (148 lines). The 22 lines it no longer holds are `STATE_HISTORY.md` part AQ,
  verbatim.
- **This report**, and **Jad's report** of B1, copied unchanged from his file. It holds no e-mail address and no
  full commit id, so nothing was masked.
- **`SESSION_REPORT_2026-10-31_build-step-2.md`**: section 23, which points here. From D148 on, "the session
  report" is this file (INTERFACES section 18's 11).

Not in D148: row 152 (5)'s hand-written anchors at c_turb x0.75 and x1.333 were not run. By point P9 they run
on this laptop during training and are committed before the first scoring command, or read "not computed".

## 6. Decided, and by whom

- **14 November, Ghassan and Jad together**, in a session with the agents: decisions 13 B, 14 B, 7 A, 8 B, 9 B,
  3 C, 4 B, 10 A and 12 B of the decision sheet of 14 November (`decisions_2026-11-14.md`, on the Desktop).
  Rows 148-153 record 13, 14, 7, 8, 3 and 12. Section S's note records 4 B, 9 B and 10 A. Decisions 1, 2, 5,
  6 and 11 were left for later ("the rest well answer later", 17:11 AST). The sheet asks for decision 1 before
  `T*`; that is the agents' deadline, and no row sets it.
- **15 November, Ghassan alone: points P1-P13, all as recommended.** Asked for "all as recommended" or the points
  he would change, he replied at 01:23 AST: "I do D 148". The agents answered that, under his standing approval
  "approve whatever you recommend" (his words of 31 October, quoted in section L's note), they read that reply as
  all thirteen points as recommended, and asked him to confirm it. At 01:28 AST he replied: "I confirm the p1-13".
  Section S's note quotes both from the session's record of his messages. No row was changed for a point. Jad was
  not asked about P1-P13; his agreement covers the answers of 14 November only.
- **15 November, Ghassan alone: Q3 (n = 20) re-confirmed.** After the figures of `results/B58H_DESIGN/power_b58.txt`
  were explained to him in the session (power 0.167 and 0.139 at C_u; smallest detectable d 11.83-14.30 points; `power_b58.txt:26`), he
  replied at 01:30 AST: "I confirm the n= 20". Section S's note quotes it from the session's record of his messages.
- **The agents**, under no new choice of the study: which CHECKPOINT lines moved to `STATE_HISTORY.md`, the form
  of D148's two printing scripts, and that "the session report" is this file from D148 on.

## 7. The schedule from here

Every time is AST and printed by `results/B58H_DESIGN/d148_figures.txt`. W ends on 20 November 2026 at 00:00
(`:14`). W is a plan, never a stop rule (row 146 (7)).

- **The route after B1's pull**: D148, Tc, Tb, PR-B and CK, 5.55-22.05 h (`:106`). From B1's start it is
  8.55-27.05 h (`:107`), 12.58 h shorter at both ends than the old route with AB and PL-B at step 3's rate
  (`:108-109`).
- **Latest starts**, which do not depend on when D148 starts: the training by 17 November 02:12 to end inside W,
  and by 16 November 16:12 for the primary scoring (a) to end inside W too (`:140-141`). For (b) to (f) to end
  inside W, the training would have to start by the times at `:142-146`; for (f) that needs D148 started by
  14 November 22:24 (`:146`), which has passed. Step 3's 01:22 and 15:22 are superseded (`:149`).
- **The forecast** of `:123-137` starts at 15 November 00:41 and assumes the high estimates, with every step back
  to back. Every hour by which D148 ends after 02:41 moves each of its dates by an hour. On it, the training starts
  15 November 22:44 and ends 18 November 20:31 (`:128`), and the slack is +17:28 (`:147`).
- **After training**, on this laptop: (a)-(f) take 29.74 h in all (`:97-103`). (d)-(f) start only if started by
  23 November 2026 00:00 (`:135`; row 149 (5)).
- **During training**, on this laptop: the code of AB and the routes, 34-56 h on ASSUMED estimates, against the
  training's 69.79 h (`:111-120`), and 400-480 runs, 1.22-1.47 h (`:94`). The calendar has run several times
  slower than such estimates on this project (the audit of 14 November, outside the repository), which is why AB's
  core is built first and the optimum last.
- **The device's pause** ends on 28 November. A training that ends inside W ends by 20 November 00:00; a sixth wave
  adds up to 13.96 h (`:48`).

## 8. What waits for you

1. **Done before D148's commit:** Ghassan's words on Q3 (n = 20), "I confirm the n= 20" (15 November, 01:30 AST),
   are in section S's note.
2. **Ghassan and Jad, before `T*` if you can** (the sheet's deadline, not a row's): decision 1 of the 14 November
   sheet (the literature review's step 14, its A25 bullet).
3. **Jad, before `T*`:**
   - Was anything installed after 14 November 19:52? "Everything is updated to the latest" can mean that nothing
     is waiting, or that updates were installed after B1. If anything was installed, say exactly what: the team
     then decides before `T*` whether B1 still describes the training's environment.
   - Did driver 621.24 come through Windows Update or NVIDIA's own app? Turn the app's automatic driver updates
     off until training ends; the Windows pause does not stop them.
   - The time of the visit, agreed with Ghassan (section 7's latest starts).
   - If you can, `B3_L8.txt` and `B0_versions.txt` from `~/grad_device/2026-11-14_B1/`, for the record. They stay
     outside the repository.
4. **Ghassan, the visit's sheet**, written after `T*` from PR-B's section 14 and from the review of B1:
   - `REPO=/c/Users/admin/grad_device/GRAD-project-device` and
     `PY=/c/Users/admin/grad-venv-lock-3.13.2/Scripts/python.exe` (the interpreter L8 recorded), in place of the
     runbook's `~/GRAD-project` and `$REPO/.venv`; a new `OUT`; `~/grad_device/B1` left as it is.
   - `git -C "$REPO" config --get core.autocrlf` must print `true`, or the sheet stops (`--show-origin` would also
     print the file's name). No re-clone, no config change, no `git add --renormalize`, no other clone.
   - `T*` read from git after a fetch and compared with a file Ghassan sends; never typed.
   - The Windows Update pause read from the registry; the environment recorded before CK and after the last run
     (`check_training_device.py`'s output, the interpreter, the Windows build and revision, the installed updates,
     the driver, the sha256 of `pip freeze`, the pause's end). PR-B says beforehand what a difference between the
     two records means.
   - Antigravity and Claude closed, or idle with no tool runs, and any agent command on the PC recorded. Jad
     launches CK and the training himself, in a Git Bash window that stays open.
   - Sleep on AC checked to be never; who re-runs `train_all.py` after a FAILED line or a restart, and how soon.
   - The PC's free disk, and how the zipped folders come back (not WhatsApp).
   - If the training runs late, the pause extended before 28 November.
5. **Before Tb, or else after the last scoring:** the laptop's B2 identity file and its `.sha256`, if the team
   wants it committed (no cost file; run `epa_backend.py compute` read-only first). The `REFERENCES.md` corrections, with
   verify_docs.py's retirements and `drift_test.py` (CHECKPOINT, item 13). After `T*`, no path present at `T*`
   changes but four documents until the first scoring command (row 149 (3)).
6. **PR-B discloses**: B2 NOT IDENTICAL, with its 75 and 25 and no cause attributed; the device's unpaused updates
   from 1 October to 14 November; Antigravity open at B1; repeat 2's `loaded` flag; B4 recorded only; and the
   device's clone and interpreter paths.
7. **Before PR-B:** check that no step of the scoring or the analysis demands bit equality between numbers the
   device wrote and numbers this laptop recomputes. B2 shows the two machines' torch arithmetic differs. Comparisons
   of `meta.json` fields are unaffected.

## 9. Not done, and why

- **D148 is not committed by this report's stage.** Its gate (the draft's section 4) runs on the staged tree once
  every file is in place.
- **Not established:** where B2's first difference falls; whether anything was installed on Jad's PC after the
  pause; which updater installed the driver; CK's rate at 10 runs at once, ASSUMED equal to the 12-run per-run rate
  (`d148_figures.txt:54`); how long checkpoint saves take; the PC's free disk; Jad's availability.
- **`grids_b58.py.txt`'s docstring is stale.** It still names AB's commit and row 148 (8) as its place, and AB's
  gate as its maker. Row 148 (8) is now CK's record, and the print moved to D148. The script is committed as it ran.
- **Line ends.** The two printed `.txt` files are LF on disk. With `core.autocrlf=true`, a later checkout writes
  them CRLF, so PR-B's check that they are reproduced compares them with line ends ignored.
- **Figures that no committed file prints**, which D148's documents therefore leave out: the schedule draft's
  140-235 h for the code (a ratio from the audit, outside the repository); "hw_opt took about 2.3 h" (`run.log:59`
  prints 808 runs in 136.5 min instead); and "683 of 820 at 18:04" (a line count). The decision sheet's 17:13 save
  time is quoted only as a file time read when the rows were drafted (row 153's Disclosed sentence;
  `hw_opt/README.md`): the sheet was saved again on 15 November at 01:33, so it cannot be read again.
- **The pull time.** The reflog records 00:39:46; the forecast starts at 00:41, an assumed start two minutes later (`d148_figures.txt:38`). Only
  `d148_figures.txt:123-137` depend on it.
- **The four-engine test does not run**, and Tb's session report gives Run 2's failed validations as the result
  (row 146 (3), (9)). That is Tb's, not D148's.
