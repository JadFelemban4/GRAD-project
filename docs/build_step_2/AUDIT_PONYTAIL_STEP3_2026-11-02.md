# Ponytail audit: the step-3 code path (2 November 2026)

Scope: `tools/device_step3.sh`, `benchmark_training.py`, `check_training_device.py` and
`requirements-lock.txt` at `91c6ece` (`origin/GRA-test`). All three code files were read in full.
Report only; the fix of finding 1 is in the commit that adds this file.

**What this code does:** `tools/device_step3.sh` runs Part A of
`docs/build_step_2/DEVICE_RUNBOOK.md` in one command. It checks the machine, builds two Python
environments (the lock's CPU one and a CUDA one), times training on the CPU and on the GPU with
`benchmark_training.py`, merges the two timings into one decision (which device trains Run 2), and
packs everything into one archive. Load assumed: one person, one machine, one run of several
hours, nothing shared with other processes.

## Must fix

1. **The script stops before it starts on a newer NVIDIA driver** (`tools/device_step3.sh:122`, `:132-133`)
   - **What this is:** before any long step, the script reads from `nvidia-smi`'s header which CUDA
     version the driver supports, to pick the torch build (cu130, cu132 or cu126).
   - **Problem:** driver 617.42 (Jad's PC, RTX 5070) prints `CUDA UMD Version: 13.4`, not
     `CUDA Version: 13.4`. The grep finds nothing, `drv` is empty, and the script dies with
     "nvidia-smi lists a GPU but prints no CUDA Version: update the NVIDIA driver", on a driver
     newer than any the script asks for. MEASURED on Jad's PC, 2 November 2026: the old pattern
     prints an empty string, the new one `13.4`.
   - **Fix:** match both spellings, `grep -oE "CUDA (UMD )?Version: [0-9.]+"`, and take the last
     field (`awk '{print $NF}'`). The same pattern on line 122, the machine record. An old
     driver's header (`CUDA Version: 13.0`) still reads `13.0` (tested on that line).
   - **If we skip it:** step 3 cannot run on this device, and the stop message sends the team to
     update a driver that is already new enough.

## Nice to have

2. **The "outside the repository" checks compare spellings, not folders** (`tools/device_step3.sh:76-77`)
   - **What this is:** `--out` and `--cuda-venv` must be outside the repository, so nothing is
     written into it.
   - **Problem:** the check runs on the text as typed. `--cuda-venv "C:/Users/admin/Documents/graduation project/GRAD-project-step3/cuda"`
     is inside the repository written the Windows way; `$REPO` reads `/c/Users/...`, so the check
     passes and the CUDA environment is made inside the repository (only `.venv/` is ignored).
   - **Fix:** compare after `cygpath -u` (move the `--out` check below line 79, where `$OUT` is
     resolved, and resolve `$CUDA_VENV` the same way).
   - **If we skip it:** only a mistyped argument triggers it. The defaults are safe. Not fixed here.

## Blocks the run here, but is not a code defect

- **The Python.** The lock needs exactly Python 3.13.2 (`requirements-lock.txt:4`, decision 32,
  rule 3: one environment). Jad's PC has 3.13.15, so the script stops at its first check, as
  designed. The remedy is a Python 3.13.2 beside the existing one, not a looser check.

## Checked and fine

- The script is checked out with CRLF line ends here (`core.autocrlf=true`, the blob is LF). This
  machine's Git Bash 5.3.15 drops the CR (tested: a CRLF script assigning `B=GRA-test` gives
  exactly `GRA-test`, and a blank CRLF line raises nothing), and `--help` runs.
- `torch==2.14.0` in the lock is met by `2.14.0+cu130` (PEP 440 ignores a local label), so the CUDA
  environment keeps its build when the lock is installed over it, as the script's comment says.
- `--merge` refuses two files that differ in Python, a critical package, `train.py` or the plant,
  and leaves the CUDA environment's CPU rows out. The probe's "CUDA does not run here" text is what
  `device_step3.sh` greps for (`benchmark_training.py:472`, `tools/device_step3.sh:56`).

**Verdict:** fix 1 first; without it step 3 cannot start on this device.

**Not checked:** `train.py`, the plant and `engines.py` (what the benchmark times), and the run
itself, which had not been made on this machine when this was written.
