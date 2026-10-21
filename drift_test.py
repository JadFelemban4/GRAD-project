"""The acceptance test for AUDIT2.md fix 2.

Part 4a of AUDIT2.md injected fourteen realistic drifts into a copy of the tree
and measured which ones `verify_docs.py` caught. Twelve went through green.
Every row marked MISSED there must be CAUGHT here.

Each drift is applied to its own fresh copy of the WORKING TREE (not of HEAD --
the fix is uncommitted while this runs), verify_docs.py is run, and the exit
code plus the reported reason are recorded. The copy is deleted afterwards.
Nothing touches the real repository.

THE CONTROL RUNS FIRST (20 October 2026). A drift is CAUGHT when verify_docs.py
exits non-zero, and a copy that fails for any other reason -- a file the copy
lacks, a figure in a document only the copy scans -- would report every row
CAUGHT for the wrong reason (mistake 12). So an undrifted copy is checked
first, and must pass; if it does not, every row reports ERROR.

    python drift_test.py            run them all
    python drift_test.py 9 10       run only those rows
"""
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.abspath(__file__))
SKIP = {".git", "__pycache__", "runs", "runs_sixspeed_18sep", ".venv",
        "node_modules", ".pytest_cache"}

# (row number as AUDIT2 Part 4a prints it, description, file, old, new,
#  the audit's verdict before this fix)
DRIFTS = [
    (1, 'README.md "8 of 11" -> "9 of 11"',
     "README.md", "8 of 11", "9 of 11", "CAUGHT"),
    (2, 'README.md "ten drives, 295.0 minutes" -> "nine drives"',
     "README.md", "**ten drives, 295.0 minutes**",
     "**nine drives, 295.0 minutes**", "CAUGHT"),
    (3, "plant.DTHETA_DEG 0.25 -> 0.5",
     "plant.py", "DTHETA_DEG = 0.25", "DTHETA_DEG = 0.5", "CAUGHT"),
    # Rows 4, 5 and 14 follow their text, 14 October 2026 (the documentation
    # restructure): the phase table to README.md, what changed on 11 September
    # (historical, as row 5 means it) to STATE_HISTORY.md part D.
    (4, 'CLAUDE.md load residual "1.4 % with zero fitted parameters" -> 1.7 % (now in README.md)',
     "README.md", "1.4 % with zero fitted parameters",
     "1.7 % with zero fitted parameters", "MISSED"),
    (5, 'CLAUDE.md "295.0 min" (current-state table) -> 299.0 (now in STATE_HISTORY.md)',
     "STATE_HISTORY.md", "295.0 minutes", "299.0 minutes", "MISSED"),
    # Rows 6 and 13 re-anchored 30 September 2026, in the merge: the app pin
    # moved 890.6 -> 873.1 C and the premise 959.8 at 884 -> 920.1 at 883 C
    # with Ghassan's physics, and the old figures are now marked history, so
    # drifting them tested nothing (row 6 MISSED, row 13 anchor not found).
    # Same protection, on the live figure. Re-anchored again 8 October: the
    # sub-stepping moved the pin 873.1 -> 872.7 C.
    # Rows 6, 12 and 13 follow their text, 14 October 2026 (the documentation
    # restructure): the numbers to README.md, the drive replays to
    # thesis/LIMITATIONS.md, the live premise to the new CHECKPOINT.md.
    (6, "CLAUDE.md app peak 872.7 -> 877.2 (was 873.1 -> 877.6; now in README.md)",
     "README.md", "872.7", "877.2", "MISSED"),
    (7, 'results/README.md and CHECKPOINT.md "+11.7" -> "+13.7"',
     "results/README.md", "11.7", "13.7", "MISSED"),
    (8, 'engine_env.py docstring "12 % at 130 km/h" -> 120 km/h',
     "engine_env.py", "12 % at 130 km/h, 42 C", "12 % at 120 km/h, 42 C", "MISSED"),
    (9, "the locked climb's v_kmh 130.0 -> 120.0 (make_grade_climb's default; now engine_specs/a90_supra.toml)",
     "engine_specs/a90_supra.toml", "v_kmh = { value = 130.0,", "v_kmh = { value = 120.0,", "MISSED"),
    (10, "the turbine knee 1123 -> 1100 (engine_env.TURB_PROTECT_K; now engine_specs/b58.toml)",
     "engine_specs/b58.toml", "turb_knee_k = { value = 1123.0,", "turb_knee_k = { value = 1100.0,",
     "MISSED"),
    # Row 11 follows its text, 14 October 2026: CHECKPOINT.md was rotated
    # verbatim into STATE_HISTORY.md part B (the documentation restructure).
    (11, 'CHECKPOINT.md "959.8 at 884 C" -> 870 C (now in STATE_HISTORY.md)',
     "STATE_HISTORY.md", "959.8 at 884 C", "959.8 at 870 C", "MISSED"),
    (12, 'CLAUDE.md "0.206 %" -> 0.306 % (now in thesis/LIMITATIONS.md)',
     "thesis/LIMITATIONS.md", "0.206 %", "0.306 %", "MISSED"),
    # Anchor moved 22 September 2026. It drifted "294.2 at 812 °C", which the
    # fix-3 sweep corrected to the live premise figure, so the row reported
    # ERROR (anchor not found) rather than testing anything. It now drifts the
    # CURRENT premise peak in CLAUDE.md, which is the same protection.
    # Re-anchored again 8 October: the plant's premise is now 848.1 at 883 °C.
    (13, 'CLAUDE.md premise "848.1 at 883 °C" -> 870 (was "920.1 at 883", "959.8 at 884"; now in CHECKPOINT.md)',
     "CHECKPOINT.md", "848.1 at 883 °C", "848.1 at 870 °C", "MISSED"),
    (14, 'CLAUDE.md "derived k = 0.831" -> 0.851 (now in README.md)',
     "README.md", "derived k = 0.831", "derived k = 0.851", "CAUGHT"),
    # Rows 9, 10 and 16 follow their values, 20 October 2026 (the four-engine
    # build, decision 24): make_grade_climb lost its defaults, TURB_PROTECT_K
    # and Vehicle's class attributes went with them, and the values are the
    # B58's and the Supra's typed specs now -- engine_specs/a90_supra.toml
    # [scenario] v_kmh and [car] gears, engine_specs/b58.toml [damage]
    # turb_knee_k. verify_docs.py reads them from the plant engines.get builds.
    # Two more of the audit's own structural worries, added here because the
    # fix claims to close them and a claim without a test is a docstring.
    (15, "evaluate.EPISODES: one weight changed in the frozen set",
     "evaluate.py", "(1013, (0.592943, 0.187398, 0.219659))",
     "(1013, (0.592943, 0.187398, 0.319659))", "not in the audit table"),
    (16, "the car's gears: top gear 0.640 -> 0.680 (the invented six-speed's; Vehicle.gears, "
         "now engine_specs/a90_supra.toml)",
     "engine_specs/a90_supra.toml", "1.000, 0.822, 0.640]", "1.000, 0.822, 0.680]",
     "not in the audit table"),
    # Rows 17 and 18, 21 October 2026 (the review of build step 1): the training
    # step and episode the documents quote went unchecked when make_grade_climb's
    # defaults went; verify_docs.py reads them from train.py now (mistake 11).
    (17, "Phase D's training step: train.DESIGN_DT fixed 0.2 -> 0.5",
     "train.py", '"fixed": 0.2,', '"fixed": 0.5,', "not in the audit table"),
    (18, "the training episode: train.DURATION_S 900.0 -> 600.0",
     "train.py", "DURATION_S = 900.0", "DURATION_S = 600.0", "not in the audit table"),
]


def copy_tree(dest):
    """Copy exactly the set a commit of the working tree would hold -- the
    TRACKED files and the untracked ones git does not ignore -- with
    WORKING-TREE contents.

    The untracked ones joined on 20 October 2026: the four-engine build's
    engines.py and engine_specs/ are the plant, untracked until it is
    committed, and a copy without them cannot build the B58 at all. Once
    committed they are tracked, and the set is the tracked set again. The
    control run (main) shows the copy passes before any drift is applied.

    Not shutil.copytree. verify_docs.py builds its file list from
    `git ls-files`, and the copy has no .git, so it falls back to a glob --
    which would then scan untracked files the real run never sees. This
    repository currently carries a teammate's in-progress app/ work and an
    untracked docs/ tree; scanning those in the copy and not in the original
    makes every drift row report CAUGHT for the wrong reason.

    Copying that list with working-tree content gives the copy the file set
    the real run has once the working tree is committed, including this
    session's uncommitted fix.
    """
    files = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard"],
                           cwd=ROOT, capture_output=True, text=True, check=True).stdout.splitlines()
    for rel in files:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


def _verify(work):
    """verify_docs.py in the copy: (exit code, everything it printed)."""
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    # encoding: the merged tree's documents carry Arabic (conflict_ar.md),
    # and text=True alone decodes with the Windows code page (cp1252) and
    # crashed here on 30 September 2026. The child already writes UTF-8.
    r = subprocess.run([sys.executable, "verify_docs.py"], cwd=work,
                       capture_output=True, text=True, timeout=1800, env=env,
                       encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def control():
    """verify_docs.py on an undrifted copy: (passed, the line that says why)."""
    tmp = tempfile.mkdtemp(prefix="drift0_")
    work = os.path.join(tmp, "tree")
    try:
        copy_tree(work)
        code, out = _verify(work)
        lines = [line.strip() for line in out.splitlines() if line.strip()]
        why = next((line for line in lines if line.startswith("WRONG") or "checks failed" in line
                    or "checks pass" in line), lines[-1] if lines else "no output")
        return code == 0, f"exit {code}: {why[:120]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_one(row):
    n, desc, rel, old, new, before = row
    tmp = tempfile.mkdtemp(prefix=f"drift{n}_")
    work = os.path.join(tmp, "tree")
    try:
        copy_tree(work)
        path = os.path.join(work, rel)
        s = io.open(path, encoding="utf-8", newline="").read()
        if old not in s:
            return (n, desc, before, "ERROR", f"anchor not found in {rel}: {old!r}")
        s2 = s.replace(old, new)
        io.open(path, "w", encoding="utf-8", newline="").write(s2)
        n_changed = s.count(old)

        code, out = _verify(work)
        caught = code != 0
        why = ""
        for line in out.splitlines():
            if line.strip().startswith("WRONG") or "checks failed" in line:
                why = line.strip()[:120]
                break
        if caught and not why:
            # no WRONG line: verify_docs.py stopped before its report, on an
            # exception (row 9 since 20 October: random_road.py's import-time
            # check that its climb is the plant's locked climb). Say which.
            lines = [line.strip() for line in out.splitlines() if line.strip()]
            why = "stopped: " + (lines[-1][:112] if lines else "no output")
        if not caught:
            why = "green run, exit 0"
        return (n, desc, before, "CAUGHT" if caught else "MISSED",
                f"[{n_changed} edit(s)] {why}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    want = {int(a) for a in sys.argv[1:]} or {d[0] for d in DRIFTS}
    rows = [d for d in DRIFTS if d[0] in want]
    ok, why = control()
    print(f"  control    the undrifted copy {'passes' if ok else 'FAILS'} verify_docs.py | {why}")
    sys.stdout.flush()
    if not ok:
        print("\n" + "=" * 78)
        print(f"0 of {len(rows)} drifts CAUGHT: the undrifted copy already fails, so a "
              "non-zero exit says nothing about a drift (mistake 12)")
        for row in rows:
            print(f"  STILL ERROR: row {row[0]} -- {row[1]}")
        return 1
    results = []
    for row in rows:
        res = run_one(row)
        results.append(res)
        print(f"  row {res[0]:>2}  was {res[2]:<20} now {res[3]:<7} | {res[1]}")
        print(f"          {res[4]}")
        sys.stdout.flush()

    print("\n" + "=" * 78)
    missed = [r for r in results if r[3] != "CAUGHT"]
    print(f"{len(results) - len(missed)} of {len(results)} drifts CAUGHT")
    for r in missed:
        print(f"  STILL {r[3]}: row {r[0]} -- {r[1]}")
    return 1 if missed else 0


if __name__ == "__main__":
    sys.exit(main())
