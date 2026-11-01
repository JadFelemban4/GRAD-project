# Run 2 checklist (row 106), for the operator on this laptop

Row 106 of `results/VALIDATION_DECISIONS.md` asks for this checklist in `CHECKPOINT.md`. It
lives here instead because `CHECKPOINT.md` stays within 150 lines (ORDER step 7's test), and
`CHECKPOINT.md` points here. Every item is a refusal or a deadlock that the code already
contains (row 106's Why), but for row 114's schedule row, which is a written rule only: arm does
not check it (`validate_epa.py`'s arm steps hold no schedule step; corrected 2 November 2026).
Written by the AI agents on 31 October 2026, before the first arming. Tick each box in the copy
you work from, not in this file.

**Who and where.** One operator, this laptop only, on AC power, one engine at a time, in the
order **Mazda (`mazda_25t`), Honda (`honda_l15b7`), Ford (`ford_27tt`)**. Run 2 never runs on
the training device, because the platform is pinned (decision 61).

## Before the first arming (ORDER steps 8 and 9)

- [ ] The tightenings are committed (R3a, the code, and R3b, `results/EPA_TIGHTENINGS.json`; ORDER
      step 8), and so is the roads record (R1). Arm checks the tightenings' plant is the B58
      (decision 71); `test_epa_tightenings.py`'s LiveRecord checks the rest of the record.
- [ ] Row 114's schedule row is committed: the window W, the device and its torch build, and the
      benchmark protocol (row 106 (7)).
- [ ] Windows feature and quality updates are paused, and the venv has not been touched since the
      fit. From now until training starts (ORDER step 22) or Run 2's defect route is recorded
      closed, whichever comes first, neither changes (row 126 (1), which replaced row 106 (1)'s end,
      the commit that records the last redraw). Check that the platform string reads
      `Windows-11-10.0.26200-SP0`:
      `python -I -c "import platform; print(platform.platform())"`. All three freeze.json files
      record that string, and `epa_freeze.py:511-517` compares it.
- [ ] Nothing on `GRA-test` has changed the B58's derived file since the fit: no new drive, no
      `new_drive.py`, no `build_dataset.py` (row 106 (5)).
- [ ] The rehearsal, on the final tree (row 106 (6); ORDER step 9): every suite of
      `epa_freeze.STEP2_TESTS`, `test_validate_guards`'s `HeldOutRun` among them, then
      `test_epa_roads.py`, then `verify_docs.py`. The only expected failure is `test_epa_rows`'
      row-120 hit (`calibrate_epa.py`, N1); record it as the known one.
- [ ] The tree is clean and pushed.

## The environment of every command (row 106 (2)-(3))

```
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1
unset OPENBLAS_NUM_THREADS        # or set it to 1
export GRAD_ENGINE_DATA=<the team's data folder, the one holding MANIFEST.csv>
PY=.venv/Scripts/python.exe
```

`--jobs 16` goes to both arm and run. Every Run 1 `e6`, `complete` and `check` ran at 16, and
WP3 asks for one `--jobs` for Run 1 and any reproduction.

## The audit's null device (row 125)

`calibrate_epa.Audit.allowed` refuses the null device under the only spelling its `norm()`
records, `//./nul` (`calibrate_epa.py:312`, `:370`). Python's `platform` module opens it when a
WMI query times out, because it then runs `ver` with stdin on DEVNULL (`platform.py:287`). Arm's
in_sample step runs `calibrate_epa.py check` with that audit active from its first line
(`validate_epa.py:1216`; `calibrate_epa.py:762`), so one timeout there writes an audit defect
into the engine's `run.json`, and `epa_freeze.audit_problems` then refuses every later arming of
that engine (`epa_freeze.py:521-538`). The timeouts come with load: on 31 October they hit
fresh processes only while other workflows ran on the laptop, and none once those workflows had
stopped (a scratch measurement, not committed; row 125). `calibrate_epa.py` is frozen until the
last commit F, so the fix waits (row 125). Until then:

- [ ] Nothing else runs on the laptop from each arm to its run: no agent, no test suite, no
      benchmark, no other Python.
- [ ] Right before each arm, the WMI check prints `20 ok, 0 failed`:
      ```
      ok=0; bad=0; for i in $(seq 1 20); do if $PY -I -c "import _wmi; _wmi.exec_query('SELECT Version FROM Win32_OperatingSystem')" 2>/dev/null; then ok=$((ok+1)); else bad=$((bad+1)); fi; done; echo "$ok ok, $bad failed"
      ```
- [ ] If arm stops with `calibrate_epa.py check exited 3`, read the last invocation of
      `results/EPA_CALIBRATION/<id>/run.json` before anything else. If `outside_allowlist` is
      exactly `["//./nul"]` and `subprocesses` holds `cmd.exe /c "ver"`, it is this defect. Do not
      re-arm and do not run `check` by hand. Commit that `run.json` alone, and follow row 125's rule.

## For each engine in turn (ORDER step 10)

1. [ ] `$PY -B validate_epa.py arm --engine <id> --jobs 16`
2. [ ] **Commit E**: `results/EPA_VALIDATION/<id>/ARMED.json` and the calibration file
       `results/EPA_CALIBRATION/<id>/run.json`, which arm's check appends to, committed by
       explicit path. Nothing else goes in this commit (row 106: "alone of the validation
       folder's files").
3. [ ] **Between arm and run, nothing happens but commit E** (row 106 (4)): no other commit, no
       pull, no checkout, no re-clone. The arming's nonce lives in `.git`, a re-arming is
       refused, and an engine disturbed after arming has no route.
4. [ ] `$PY -B validate_epa.py run --engine <id> --jobs 16`
5. [ ] **Commit F**, pushed at once: the run's outputs in `results/EPA_VALIDATION/<id>/`, and
       `results/EPA_VALIDATION/<id>.invocations.json` once it has stopped changing. On the third
       engine, `summary.json` too (`$PY -B validate_epa.py summary`).
6. [ ] Between this commit F and the next arming, only the label record changes (row 106 (8)).

**If arm fails after its in_sample step**, commit that engine's calibration `run.json` before
the next arming (`validate_epa.py:907-908`).

**If a defect is found after an engine's held-out statistic**, the fix reaches every engine not
yet run through the defects.json route (`validate_epa.py:1059-1066`). Each later engine's
records, and the preregistration, say it was made after that statistic. A run may be executed
again only while STARTED is its only record. Otherwise only the defect route runs:
`arm --defect-rerun "<reason>" --fix-commit <sha>`, then `run --defect-rerun ...`. Row 122 (1)
gives the restore set.

## After the third engine

- [ ] ORDER step 11, the labels: a person records each engine's labels, section 7's
      consequences, any drops, and κ (row 107 (3)-(4)).
- [ ] Windows updates stay paused until training starts (ORDER step 22) or Run 2's defect route is
      recorded closed, whichever comes first (row 126 (1)).
