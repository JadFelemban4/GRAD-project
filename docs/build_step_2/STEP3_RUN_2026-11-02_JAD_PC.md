# ORDER step 3 on Jad's PC (2 November 2026)

`bash tools/device_step3.sh --python C:/Users/admin/Python3132/python.exe --out ~/grad_device/2026-11-02_step3`,
run by Claude for Jad at Ghassan's request, at `b2151af` (`origin/GRA-test`, clean, pushed). It
finished (exit 0) in 69 minutes, 13:37 to 14:46 AST. The one file to bring back:
`C:\Users\admin\grad_device\2026-11-02_step3.tar.gz` (19 224 bytes), holding every A0-A6 file.

## The decision (A5, `A5_bench_merged.txt`)

`RECOMMENDATION: CPU with 12 runs at once (torch 2.14.0+cpu): its lowest lower bound, 106.19 (12 at
once), beats CUDA's highest upper bound, 70.87 (6 at once).` By the runbook's A6 a CPU recommendation
ends step 3: the device is the CPU, and the lock's environment is the experiment's.

- 12 at once is 8.85 steps/s per run, so a 450 000-step run takes 0.59 days; 20 seeds per arm take
  11.8 days for the four engines, and **at most 16 seeds per arm fit the 10-day window** (decision 30
  asks for at least 20). Valid for the cycle backend and the B58 only, as the line itself says.
- CUDA was capped at 6 runs at once by RAM at 450 000-step size (its single run took 1.6 GB of
  available memory against the CPU's 0.3 GB), about 317 MiB of video memory a run.
- Section 4: `cpu: IDENTICAL` and `cuda: IDENTICAL`; every CUDA row with two runs or more trained
  seed 0 twice identically.

## The machine

AMD Ryzen 5 9600X (6 cores, 12 logical), about 16-19 GB of RAM available during the run, NVIDIA
GeForce RTX 5070 (12 227 MiB, compute capability 12.0), driver 617.42 (`CUDA UMD Version: 13.4`),
Windows 11 Pro 10.0.26300. The full record is `A_machine.txt` in the archive.

## What to know before using these numbers

1. **The script needed a fix to start here** (`b2151af`, audit:
   `docs/build_step_2/AUDIT_PONYTAIL_STEP3_2026-11-02.md`): driver 617.42 prints "CUDA UMD Version",
   which the pre-check did not read. The benchmark code itself is `91c6ece`'s, unchanged.
2. **The Python is 3.13.2 from python.org's NuGet package** (`python` 3.13.2, its `python.exe`
   Authenticode-signed by the Python Software Foundation), unpacked in `C:\Users\admin\Python3132`,
   because the PC had 3.13.15 and the lock needs exactly 3.13.2. Same version string as the lock
   (`3.13.2 64 cpython gil`); not the same installer as the team laptop's.
3. **12 of the 14 rows are flagged "loaded"** (the CPU over 5 % busy before the batch; 4-13 %): the
   IDE that hosts the Claude Code session running the script (Antigravity) stayed open, about half a
   core. The merge carries this as its one CAUTION.
4. **The CPU's second repeat was slower at 3 and 6 at once**: 40.5 against 52.0 steps/s and 71.4
   against 85.3 (12 at once was not: 110.1 against 106.2). Claude ran a few short commands on the
   PC during the second 3-at-once row; nothing during the 6-at-once one. The rule takes each row's
   lowest repeat, so this could only make the CPU look slower; it still wins by 106.19 against 70.87.
5. The keep-awake loop worked (`keep_awake.log`: SetThreadExecutionState returned 2147483648, not 0).
