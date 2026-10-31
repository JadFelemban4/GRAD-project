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
| this one | 8, R3a | the tightenings code, with row 129 (4)'s `stopped` route; this report |

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
