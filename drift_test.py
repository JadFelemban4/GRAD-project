"""The acceptance test for AUDIT2.md fix 2.

Part 4a of AUDIT2.md injected fourteen realistic drifts into a copy of the tree
and measured which ones `verify_docs.py` caught. Twelve went through green.
Every row marked MISSED there must be CAUGHT here.

Each drift is applied to its own fresh copy of the WORKING TREE (not of HEAD --
the fix is uncommitted while this runs), verify_docs.py is run, and the exit
code plus the reported reason are recorded. The copy is deleted afterwards.
Nothing touches the real repository.

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
    (4, 'CLAUDE.md load residual "1.4 % with zero fitted parameters" -> 1.7 %',
     "CLAUDE.md", "1.4 % with zero fitted parameters",
     "1.7 % with zero fitted parameters", "MISSED"),
    (5, 'CLAUDE.md "295.0 min" (current-state table) -> 299.0',
     "CLAUDE.md", "295.0 minutes", "299.0 minutes", "MISSED"),
    (6, "CLAUDE.md app peak 890.6 -> 895.1",
     "CLAUDE.md", "890.6", "895.1", "MISSED"),
    (7, 'results/README.md and CHECKPOINT.md "+11.7" -> "+13.7"',
     "results/README.md", "11.7", "13.7", "MISSED"),
    (8, 'engine_env.py docstring "12 % at 130 km/h" -> 120 km/h',
     "engine_env.py", "12 % at 130 km/h, 42 C", "12 % at 120 km/h, 42 C", "MISSED"),
    (9, "engine_env.py DEFAULT v_kmh=130.0 -> 120.0",
     "engine_env.py", "v_kmh=130.0)", "v_kmh=120.0)", "MISSED"),
    (10, "engine_env.py TURB_PROTECT_K 1123 -> 1100",
     "engine_env.py", "TURB_PROTECT_K = 1123.0", "TURB_PROTECT_K = 1100.0", "MISSED"),
    (11, 'CHECKPOINT.md "959.8 at 884 C" -> 870 C',
     "CHECKPOINT.md", "959.8 at 884 C", "959.8 at 870 C", "MISSED"),
    (12, 'CLAUDE.md "0.206 %" -> 0.306 %',
     "CLAUDE.md", "0.206 %", "0.306 %", "MISSED"),
    # Anchor moved 22 September 2026. It drifted "294.2 at 812 °C", which the
    # fix-3 sweep corrected to the live premise figure, so the row reported
    # ERROR (anchor not found) rather than testing anything. It now drifts the
    # CURRENT premise peak in CLAUDE.md, which is the same protection.
    (13, 'CLAUDE.md premise "959.8 at 884 °C" -> 870 (was "294.2 at 812")',
     "CLAUDE.md", "959.8 at 884 °C", "959.8 at 870 °C", "MISSED"),
    (14, 'CLAUDE.md "derived k = 0.831" -> 0.851',
     "CLAUDE.md", "derived k = 0.831", "derived k = 0.851", "CAUGHT"),
    # Two more of the audit's own structural worries, added here because the
    # fix claims to close them and a claim without a test is a docstring.
    (15, "evaluate.EPISODES: one weight changed in the frozen set",
     "evaluate.py", "(1013, (0.592943, 0.187398, 0.219659))",
     "(1013, (0.592943, 0.187398, 0.319659))", "not in the audit table"),
    (16, "Vehicle.gears: top gear 0.640 -> 0.680 (the invented six-speed's)",
     "engine_env.py", "1.000, 0.822, 0.640)", "1.000, 0.822, 0.680)",
     "not in the audit table"),
]


def copy_tree(dest):
    """Copy exactly the TRACKED set, with WORKING-TREE contents.

    Not shutil.copytree. verify_docs.py builds its file list from
    `git ls-files`, and the copy has no .git, so it falls back to a glob --
    which would then scan untracked files the real run never sees. This
    repository currently carries a teammate's in-progress app/ work and an
    untracked docs/ tree; scanning those in the copy and not in the original
    makes every drift row report CAUGHT for the wrong reason.

    Copying the tracked list with working-tree content gives the copy the same
    file set the real run has, including this session's uncommitted fix.
    """
    files = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True,
                           text=True, check=True).stdout.splitlines()
    for rel in files:
        src = os.path.join(ROOT, rel)
        if not os.path.isfile(src):
            continue
        dst = os.path.join(dest, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)


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

        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        r = subprocess.run([sys.executable, "verify_docs.py"], cwd=work,
                           capture_output=True, text=True, timeout=1800, env=env)
        out = r.stdout + r.stderr
        caught = r.returncode != 0
        why = ""
        for line in out.splitlines():
            if line.strip().startswith("WRONG") or "checks failed" in line:
                why = line.strip()[:120]
                break
        if not caught:
            why = "green run, exit 0"
        return (n, desc, before, "CAUGHT" if caught else "MISSED",
                f"[{n_changed} edit(s)] {why}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    want = {int(a) for a in sys.argv[1:]} or {d[0] for d in DRIFTS}
    rows = [d for d in DRIFTS if d[0] in want]
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
