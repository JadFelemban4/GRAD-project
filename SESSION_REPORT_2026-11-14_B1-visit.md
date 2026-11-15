# Session report — 14 November 2026: visit 1 (B1) on Jad's PC

Jad's session. Ghassan sent `For Jad - B1.zip` (the sheet `B1_SHEET.md`, `ta_pushed.txt`, the
laptop's identity file and its `.sha256`) and asked Claude to start the benchmark. The sheet is made
from `docs/build_step_2/DEVICE_RUNBOOK.md` Part B, row 146 (6) of `results/VALIDATION_DECISIONS.md`
and step 18 of `docs/build_step_2/ORDER_TO_TRAINING.md`, all at Ta (`0329456`, GitHub's `GRA-test`).
Nothing in the physics, the data or the training changed. In `GRAD-project` only this report was
written. Ghassan's four files are saved, names unchanged, in `C:\Users\admin\grad_device\from_ghassan\`
(the laptop file's checksum: OK).

## 1. Where the sheet did not match the PC (for Ghassan)

1. **The sheet's clone does not exist.** Step 1 sets `REPO=".../graduation project/GRAD-project-step3"`.
   That folder was a worktree of `GRAD-project`, removed on 11 November at Jad's request (one project
   folder; the session report of 11 November). A fresh clone from GitHub was made instead, at
   `C:\Users\admin\grad_device\GRAD-project-device`, outside the `graduation project` folder; the
   sheet's Step 2 checked it out at Ta. Git's name and email were copied into the clone's local config
   from `GRAD-project`'s local config, because the global config holds neither and Step 8 checks both.
   Later sheets need this `REPO`.
2. **The interpreter moved.** Step 1 sets `PY="$REPO/.venv/Scripts/python.exe"`. Step 3's lock venv
   (made by `tools/device_step3.sh` A1 on 2 November) was moved out of the worktree on 11 November and
   is `C:\Users\admin\grad-venv-lock-3.13.2`; `PY` points there, unchanged. Its newest `site-packages`
   entries are dated 2 November 13:38, so nothing was installed into it since step 3, and Step 3 below
   printed `VERSIONS: match the lock`. Later sheets need this `PY`.
3. **Windows Update was not paused.** The sheet says it stays paused until 2026-11-25. On this PC the
   pause had expired on 2026-10-01 (`PauseUpdatesExpiryTime` in
   `HKLM\SOFTWARE\Microsoft\WindowsUpdate\UX\Settings`, read at 19:30). Since step 3 (2 November)
   Windows installed the 2026-11 security update KB5132061 (build 26300.9974) and KB5132688 on
   11 November, Windows App Runtime updates on 11 and 12 November, and Defender definitions daily. So
   B1's PC differs from step 3's in its OS patch level. Jad paused updates before Step 4, at 19:52
   (`PauseUpdatesStartTime 2026-11-14T16:52:13Z`, `PauseUpdatesExpiryTime 2026-11-28T16:52:09Z`).
4. **The IDE stayed open.** The sheet asks to close VS Code. Claude Code runs inside Antigravity IDE (a
   VS Code build), which stayed open, as it did in step 3. Before Step 4, Jad closed Brave, Discord and
   the Claude desktop app; total CPU just before Step 4: 4 to 6 % (three 1 s samples), 22.1 GB RAM free.
5. **Line endings.** Git for Windows' system config sets `core.autocrlf=true` and Ta has no
   `.gitattributes`, so the clone's text files are CRLF in the work tree (`git ls-files --eol`:
   `i/lf w/crlf`), as step 3's worktree's were. `code_info()` hashes those bytes: B0's record holds
   `benchmark_sha f5cb19ba238dbf0f` and `train_sha 54a4265c355af961`, which a checkout with LF
   endings would not reproduce.
6. **The NVIDIA driver changed.** Step 3 recorded driver 617.42 (`A_machine.txt`); B1's machine record
   shows 621.24 (its DriverStore folder was created on 13 November at 02:07; driver date 7 November).
   Training runs on the CPU (torch 2.14.0+cpu), so the driver does not enter it; it is recorded because
   the sheet's rule is no driver updates.

The commands ran through Claude Code's Bash tool (Git Bash), with Step 1's variables set from one
file before each command and every other line as the sheet writes it.

## 2. The steps, as run

| step | printed | where |
|---|---|---|
| 1 | `ls "$IN"` listed the four files | |
| 2 | `MATCH: GitHub's GRA-test is Ta`; `B0 OK: at Ta, clean` | `~/grad_device/2026-11-14_B1/B0_commit.txt`, `B0_status.txt` (empty) |
| 3 | `VERSIONS: match the lock` (python 3.13.2, torch 2.14.0+cpu); `wrote C:/Users/admin/grad_device/B1\B0_0329456.json` | `B0_versions.txt`; `~/grad_device/B1/B0_0329456.json` |
| 4 | Step 3's second block again (a new window): `already written, the same; not rewritten`; `b58`; 19:53:34 to 20:08:35; `4. DETERMINISM` `cpu: IDENTICAL`; repeat 1: 107.5 to 108.3 steps/s in all (342 s); repeat 2: 110.8 to 111.9 (332 s, flagged `loaded`); the `.txt` ends `written to C:\Users\admin\grad_device\B1\B1_bench_b58.attempt1.json` | `~/grad_device/B1/B1_bench_b58.attempt1.json` and `.txt` |
| 5 | 20:09:47 to 20:10:21: `B2_identity_laptop_0329456...json: OK`; `VERSIONS: match the lock`; `fingerprint written to C:/Users/admin/grad_device/2026-11-14_B1/B2_identity_device.json: 96 tensors, 47 record fields`; `VERDICT: NOT IDENTICAL (100 differences)` | `~/grad_device/2026-11-14_B1/B2_identity_device.json`, `B2_compare.txt` |
| 6 | dry run, 20:11:09 to 20:11:30: `DRY RUN: 11 commands ran with --help appended, 0 did not exit 0; nothing trained, nothing compared.` (the laptop's took 36 s); the real run, 20:11:37 to 20:15:00: 11 runs exit 0 (33 to 116 s each); extremes sighted, extremes blind, wideair sighted and `ctl_none` `IDENTICAL TRAINING` (expected IDENTICAL); `ctl_mass`, `ctl_cturb` `IDENTICAL TRAINING` (expected INFO); `ctl_mass1e-9`, `ctl_mass1e-6` `NOT IDENTICAL` (expected DIFFERENT); `L8 VERDICT: PASS (11 runs exit 0; three pairs and the wrapper IDENTICAL; both relative-step controls DIFFERENT)` | `~/grad_device/2026-11-14_B1/B3_L8_dry/`, `B3_L8/`, `B3_L8.txt` |
| 7 | 20:15:10 to 20:20:45: `Ran 7 tests in 205.508s`, `OK` | `~/grad_device/2026-11-14_B1/B4_test_epa_plants.txt` |
| 8, first block | 20:21:20: `CLEAN: go on`; `JadFelemban4`; the email set (masked in the display); the 26 files the copies take hold no e-mail address (`grep`) | `~/grad_device/2026-11-14_B1/end_status.txt` (empty) |
| 8 | 20:57:17: `STATUS OK: B1's files only`, 26 files staged, each `A `; 20:57:35: `[detached HEAD 891e29a] build step 2, ORDER step 18 (B1): the B58's benchmark on Jad's PC, with B2, B4 and L8`, `26 files changed, 2889 insertions(+)`; 20:57:49: `0329456..891e29a  HEAD -> GRA-test`, `PUSHED: GitHub's GRA-test is your B1 commit` | GitHub's `GRA-test` at `891e29a`; `~/grad_device/2026-11-14_B1/B5_status.txt` |

Reading Step 4:

- **`loaded` on repeat 2.** The CPU load before that batch was 6 %, above `LOAD_LIMIT_PCT = 5.0`
  (`benchmark_training.py` line 208); before repeat 1 it was 3 %. Claude Code made three small edits to
  this report in Step 4's first minute and was idle after. The sheet's done condition is met; the flag
  is recorded in the JSON.
- **The "x 4 engines: 11.6 days" line** multiplies by the constant `ENGINES = 4` (line 200), not by
  `engines.trainable()`, which is the B58 alone at Ta. From the same printed figures (5 waves of a
  0.58-day run per engine), the B58 alone is about 2.9 days of training before scoring: arithmetic on
  printed numbers, not a printed figure.
- **Against step 3** (2 November, commit `b2151af`, another road): 106.19 to 111.09 steps/s at 12 at
  once (`~/grad_device/2026-11-02_step3/A6_summary.txt`). B1, on the `four_engine` road: 107.46 to
  111.89.

Reading Step 5 (recorded, decides nothing: row 32, the sheet's Step 5):

- The two machines, as `--compare` names them: A, the laptop, `Windows-11-10.0.26200-SP0`; B, this PC,
  `Windows-11-10.0.26300-SP0`.
- The 100 differences are 75 of the 96 weight tensors and 25 of the 47 record fields (among them
  `action`, `applied`, `cost_torque`, `damage_cum`), so the two machines' runs took different actions.
  The 8 counters, the 9 `meta` fields, the command and the curve are the same; the 600-step run
  completed `0 episodes` (the `--identity` output). `device` differs in `machine` and `processor`,
  which the count does not include. Counted from the two JSON files with a short script;
  `B2_compare.txt` lists the first 20.

Reading Step 8:

- Jad approved the push to `GRA-test`, Ghassan's branch, after Claude named that destination to him
  («ايوه ارفع»). Claude had told him 27 files before the push; the count is 26.
- The commit message is row 146 (6)'s, word for word, so it carries no co-author line.
- Git stored every file with LF line endings (`core.autocrlf=true`). On disk, the files Python wrote
  through its text-mode output are CRLF (the attempt's `.json` and `.txt`, `B2_compare.txt`,
  `B2_identity_device.json`, `B4_test_epa_plants.txt`, `run_identities.json`, and the one
  `compare_*.txt` and one `cmp/*.json` checked); the four written with LF (`B0_0329456.json`,
  `_status.txt`, `_verdicts.txt`, `provenance.txt`) drew git's warning that a checkout here would write
  them CRLF. A committed file and its copy in `~/grad_device` can therefore differ in their line
  endings, which is all git's conversion changes.

## 3. Machine at the visit

AMD Ryzen 5 9600X, 6 cores, 12 threads; 31.2 GB RAM (17.8 GB free at 19:28); desktop, on AC; sleep on
AC: never (`powercfg`, index 0). The same host as step 3 (`DESKTOP-VF1MO3H`). Background load before
Step 4, measured over 5 s with Brave and Discord still open: about 0.7 of one thread in all (Claude
desktop app, Antigravity IDE, SteelSeries Sonar, Discord, audio).

## 4. After the visit

- The clone `C:\Users\admin\grad_device\GRAD-project-device` stays at `891e29a`, detached and clean: no
  `git pull`, no checkout, not deleted, until the study's training ends (the sheet's "What counts as
  done"). `~/grad_device/B1` and this visit's folders stay as they are.
- The PC keeps the sheet's settings: AC power, sleep never, Windows Update paused. The pause now ends on
  28 November; if the training runs past that date, the pause has to be extended before it ends.
- Ghassan's laptop takes the commit with `git pull --ff-only` and decides whether B1 stands. Jad tells
  him by WhatsApp, with the six differences of section 1.
- The console output of Step 3's second block and of Steps 4 to 7, as the background runs printed it
  (`--identity`'s output included, which no step tees), and the variables file `b1_env.sh` are in
  `~/grad_device/2026-11-14_B1/console/`.
- Nothing was trained for the study, and nothing touched a car.
- **"Something that runs 16 hours."** After the push Jad asked whether B1 was really done, because
  Ghassan had mentioned something that takes 16 hours. ORDER step 18's full row
  (`docs/build_step_2/ORDER_TO_TRAINING.md`, line 33), which is B1, holds the benchmark,
  `--identity` and `--compare`, L8 and `test_epa_plants`, then the commit and the push: all done, and
  GitHub's `GRA-test` was still at `891e29a` after a fetch. In `docs/build_step_2/`, "16 h" appears only
  for writing PR-B, the preregistration (`INTERFACES.md` line 1373: "up to 16 h from scratch"). The next
  job on the PC is ORDER step 21, PL-B, decision 29's pilot: 5 full-length seed pairs on the B58, after
  PR-B (step 20), from `T*`. At B1's printed rate for 12 runs at once (0.58 days for a 450,000-step run),
  a full-length run takes about 14 hours, if full length is 450,000 steps (ASSUMED here; the pilot runs
  10 at once, not 12). Which of the two Ghassan meant was not yet asked.
