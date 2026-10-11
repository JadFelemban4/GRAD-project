"""full_run.py — run every script that prints a published figure, and capture it.

    python full_run.py                  everything (about 90 minutes since 9 October;
                                        check_random_road.py and drift_test.py are most of it)
    python full_run.py --quick          skip the slow ones (app --full, premise)
    python full_run.py --out FILE       where to write the transcript

WHY THIS EXISTS
---------------
AUDIT2.md's fix 3 is "sweep the documents FROM A FRESH RUN": run the scripts,
capture the output, and rewrite the documents from what they actually printed.
Doing that by hand means eight terminals, eight scroll-backs and eight chances
to copy a figure from the wrong one -- which is how this project acquired the
document rot in the first place.

So the transcript is generated, not assembled. Whatever is in the file this
writes IS what the tree printed on that day, and a figure that is not in it is
a figure no script produces.

IT RECORDS THE EXIT CODE OF EVERY SCRIPT, AND THAT IS THE POINT.
Commit `0674f6d` claimed a green `verify_docs.py` run that had already failed,
because the claim came from a `python x.py | tail && git commit` chain -- which
tests `tail`, not the script. A transcript that shows output without status is
the same trap written down. Every block below opens with its exit code.

WHAT IS DELIBERATELY NOT RUN, and why each one:

    evaluate.py         the agents on this plant are X1's 46 (since 8 October),
                        and scoring them is about two hours (`x1_score.py`:
                        run_results.py phase_d, then record_agents.py), logged
                        in results/x1_score/SCORE_LOG.txt. What IS run is the
                        refusal: agents from an older plant, or without a
                        certificate, must be refused -- see REFUSAL below.
    generality_test.py  slow, and re-run on 8 October on the sub-stepped plant
                        (results/generality.json). Since then its figures are
                        quotable as a hand-written result; AUDIT.md C3 still
                        says hand-written policies cannot settle the criterion.
                        (Until 28 September it scored preview only against the
                        comparator C3 retired, AUDIT2.md H2-5.)
    timestep_study.py   slow; re-run on 8 October (results/timestep_study.json).
    analyse_c4.py       reads the C4 agents' ZIPs, which live only on the
                        machine C4 trained on (runs_c4/); its result is
                        captured in results/C4_RESULT.txt.
    train.py            hours, and no experiment is this task.

9 October 2026: the X1-era scripts were added (premise_split.py, check_roads.py
--road extremes, app.test_simulation, model_vs_data.py, analyse_phase_d.py,
analyse_x1.py), and the refusal now uses whichever older agents this machine
has, so it is refused for the reason it names, not for a missing folder. After
that day's pass, test_plant_guards.py and app.test_agents were added too: the
ramp had broken six tests of the second, which no list here ran.
"""
import argparse
import datetime
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# (label, argv, slow?, what a reader should take from it)
STEPS = [
    ("build_dataset.py — regenerates data/ from logs/raw/",
     ["build_dataset.py", "logs/raw/*.csv"], False,
     "minutes, drives, operating points, the span, pinned samples"),
    ("compare_log.py — model against the car at the steady points",
     ["compare_log.py", "data/master_points.csv"], False,
     "both load residuals and both values of k"),
    ("validate.py — eleven quantities against published bands",
     ["validate.py"], False,
     "N of 11 inside, and which three miss"),
    ("check_map.py — MBT and knock-limited spark surfaces",
     ["check_map.py"], False,
     "monotonicity in both directions; unreachable cells marked --"),
    ("fit_envelope.py — the compressor envelope",
     ["fit_envelope.py"], False,
     "the top bins and how many INDEPENDENT readings each rests on"),
    ("test_reward.py — the reward gate",
     ["test_reward.py"], False,
     "neutral near zero, the starver punished"),
    ("test_plant_guards.py — the sub-stepping and the derived fingerprint",
     ["test_plant_guards.py"], False,
     "6 tests OK: a step equals its sub-steps, the coolant settles at 2 s, one changed "
     "constant moves derived_sha and a timestamp does not"),
    ("check_premise.py — the premise table, five policies",
     ["check_premise.py"], True,
     "THE BASELINE ROW AND WHETHER THE CONSTRAINT BINDS. This is the block "
     "CLAUDE.md, README.md and handoff.md currently contradict"),
    # RETIRED-OK: 920.1, 917.6 -- the merged plant's premise: the split's first rows, by design
    ("premise_split.py — the plant changes of 8 October, one at a time",
     ["premise_split.py"], True,
     "the baseline 920.1 -> 917.6 (sub-stepping) -> 848.1 (with the ramp); preview over "
     "current-grade -0.32 -> -0.01"),
    ("check_roads.py --road extremes — X1's training roads",
     ["check_roads.py", "--road", "extremes"], True,
     "PASS over 40 roads; how many bind; the worst neutral reward and p95 tracking error"),
    ("app.test_replay --full — the live supervisor, both drives",
     ["-m", "app.test_replay", "--full"], True,
     "N of N, and the two pinned peaks"),
    ("app.test_simulation — the replay lab",
     ["-m", "app.test_simulation"], False,
     "the test count and OK"),
    ("app.test_agents — the agent replay pages, which read the plant's roads",
     ["-m", "app.test_agents"], True,
     "135 tests OK; 14 skipped on a machine without runs_c4/"),
    ("model_vs_data.py — the simulator against the car",
     ["model_vs_data.py"], True,
     "each comparison beside the figure the documents quote; writes results/model_vs_data.json"),
    ("verify_docs.py — the guard",
     ["verify_docs.py"], False,
     "the check total, and the known-stale ledger, which is the size of fix 3"),
    ("drift_test.py — the guard's own acceptance test",
     ["drift_test.py"], True,
     "N of 16 drifts CAUGHT"),
    # Added 22 September 2026 with Phase D2. Each prints figures that
    # results/PREREGISTRATION_D2.md quotes, so each belongs in the transcript
    # the documents are swept from.
    ("power_analysis.py — what effect size eight seeds can detect",
     ["power_analysis.py"], False,
     "power against the MEI (50 units) and the effect with 80 % power"),
    ("check_random_road.py — does every D2 road bind; is the blind arm blind",
     ["check_random_road.py"], True,
     "A False, B 150/120, C 0 of 121 non-binding, D 0 of 20, PASS"),
    ("analyse_phase_d2.py — the D2 preregistered test, both experiments",
     ["analyse_phase_d2.py"], False,
     "the D2 cell (PREVIEW HELPS / SMALLER THAN THE MEI / INCONCLUSIVE) "
     "beside Phase D's"),
    ("analyse_phase_d.py — Phase D's preregistered test",
     ["analyse_phase_d.py"], False,
     "5 of 8, sign p 0.3633, permutation p 0.4922: NOT SIGNIFICANT"),
    ("analyse_x1.py — X1's preregistered test",
     ["analyse_x1.py"], False,
     "the cell, total and thermal-only; 17 of 23 below 5.43 points, sign p 0.0173"),
]

# Run last and separately: it is a DEMONSTRATION of a refusal, not a measurement.
# Older agents this machine may hold, newest first: each must be REFUSED by
# evaluate.py on today's plant (no certificate, or a certificate for another
# plant). The first pair whose folders exist is the one run.
REFUSAL_CANDIDATES = [
    ("the twenty of 29 September", "runs/terrain_dt1/sighted_seed0", "runs/terrain_dt1/blind_seed0",
     "exit 1: they carry only a reconstructed certificate, which evaluate.py never reads"),
    ("the six-speed agents", "runs_sixspeed_18sep/sighted_seed0", "runs_sixspeed_18sep/blind_seed0",
     "exit 1 and a named plant mismatch"),
]


def run(argv, timeout):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable] + argv, cwd=HERE, env=env,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=timeout)
        return r.returncode, r.stdout, r.stderr, time.time() - t0
    except subprocess.TimeoutExpired:
        return None, "", f"TIMED OUT after {timeout} s", time.time() - t0
    except OSError as exc:
        return None, "", str(exc), time.time() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true",
                    help="skip the slow steps (premise, app --full, drift test)")
    ap.add_argument("--out", default="FULL_RUN.txt")
    ap.add_argument("--timeout", type=float, default=3600.0)
    a = ap.parse_args()

    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=HERE,
                          capture_output=True, text=True)
    dirty = subprocess.run(["git", "status", "--porcelain"], cwd=HERE,
                           capture_output=True, text=True).stdout.strip()

    out = []

    def w(line=""):
        out.append(line)
        print(line)
        sys.stdout.flush()

    w("=" * 78)
    w("FULL VERIFICATION RUN")
    w("=" * 78)
    w(f"date          {datetime.date.today().isoformat()}")
    w(f"commit        {head.stdout.strip() or 'unknown'}")
    w(f"working tree  {'DIRTY -- see below' if dirty else 'clean'}")
    if dirty:
        for line in dirty.splitlines():
            w(f"              {line}")
    w(f"python        {sys.version.split()[0]}")
    w("")
    w("Every block records its EXIT CODE. A block with a non-zero code is not a")
    w("source of figures, whatever it printed before it stopped.")
    w("")

    summary = []
    steps = [s for s in STEPS if not (a.quick and s[2])]
    for i, (label, argv, _slow, take) in enumerate(steps, 1):
        w("")
        w("=" * 78)
        w(f"[{i}/{len(steps)}]  {label}")
        w(f"         $ python {' '.join(argv)}")
        w(f"         read for: {take}")
        w("=" * 78)
        rc, so, se, secs = run(argv, a.timeout)
        w(f"EXIT CODE {rc}   ({secs:.0f} s)")
        w("")
        w(so.rstrip("\n"))
        if se.strip():
            w("--- stderr ---")
            w(se.rstrip("\n"))
        summary.append((label.split(" — ")[0], rc, secs))

    found = [c for c in REFUSAL_CANDIDATES
             if os.path.isdir(os.path.join(HERE, c[1])) and os.path.isdir(os.path.join(HERE, c[2]))]
    w("")
    w("=" * 78)
    if found:
        who, sighted, blind, take = found[0]
        argv = ["evaluate.py", sighted, blind]
        w(f"[extra]  evaluate.py against {who} — expected to REFUSE")
        w(f"         $ python {' '.join(argv)}")
        w(f"         read for: {take}, the CORRECT outcome here")
        w("=" * 78)
        rc, so, se, secs = run(argv, 300.0)
        w(f"EXIT CODE {rc}   ({secs:.0f} s)   -- non-zero is the PASS here")
        w("")
        w((so + se).rstrip("\n"))
        summary.append(("evaluate.py refusal (non-zero expected)", rc, secs))
    else:
        w("[extra]  evaluate.py refusal — SKIPPED: no older agents on this machine "
          f"({', '.join(c[1] for c in REFUSAL_CANDIDATES)})")
        w("=" * 78)

    w("")
    w("=" * 78)
    w("SUMMARY — exit code per script")
    w("=" * 78)
    for name, rc, secs in summary:
        w(f"  {rc if rc is not None else 'ERR':>4}   {secs:>6.0f} s   {name}")
    w("")
    w("A figure not printed above is a figure no script produces. Do not write")
    w("one into a document from memory -- that is what fix 3 is repairing.")

    with open(os.path.join(HERE, a.out), "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    print(f"\ntranscript written to {a.out}")


if __name__ == "__main__":
    main()
