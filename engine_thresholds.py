"""engine_thresholds.py -- the validation contract of decision 35, every step from the EPA tables'
structure to its two files: results/ENGINE_THRESHOLDS.md and results/ENGINE_THRESHOLDS.json.

    python engine_thresholds.py                 every step in order: about 26 minutes on 20 CPUs, nearly
                                                all of it step 5's 24 B58 runs (each step's time:
                                                results/ENGINE_THRESHOLDS/run.json)
    python engine_thresholds.py --jobs 8        the same, step 5 eight runs at a time (default: one per
                                                CPU, at most 24)
    python engine_thresholds.py --build-only    steps 6 and 7 only, from the outputs of steps 1-5 already
                                                in results/ENGINE_THRESHOLDS/ (seconds)
    python engine_thresholds.py --check         steps 6 and 7 in memory, writing nothing; exit 1 if either
                                                file differs from what they would write

WHAT THIS IS
------------
Decision 35 (results/VALIDATION_DECISIONS.md, section F) asks that the three EPA engines' torque,
fuel and turbine-inlet temperature be checked against held-out EPA points, "with each required
accuracy derived from its consequence on the MEI ... and committed before calibrating; the table
gates likewise"; decision 28 lets an engine train on its table only through gates fixed before the
table is built. The contract that answers both was derived and reviewed on 21 October 2026, before
any calibration, by scripts that lived only in a session's scratch folder (version 2; the JSON
carried their sources and sha256). This file and the package thresholds/ are those scripts,
committed and run as one, with decisions 36-38 of section G of the decision sheet applied in the
code: b = MEI/6 per part (every d-row R x 5/6), the collapse test's equivalence margin the MEI, and
an untested row with a statistic entering as a preregistered band (thresholds/contract.py).

THE STEPS, in the order they run. Each writes its output, and its printout as <step>.txt, into
results/ENGINE_THRESHOLDS/; run.json records the Python, NumPy and platform that ran them and each
step's wall-clock time. It is the only file that holds a time: every step output, and both contract
files, are functions of the code and its inputs, so a re-run on one platform gives each back byte
for byte, and the JSON's sha256 of each step output with it.

  1. split (thresholds/split.py). The held-out split: which rpm lines of each EPA engine only the
     validation sees, the populations (fired, hot, lambda~1, enriched), the deciding lines and the
     coverage. Reads data/engines/<id>/epa_steady*.csv and epa_highload_*.csv for their STRUCTURE
     only: speed, manifold pressure, BMEP, lambda, intake and coolant temperature, the fuel report,
     the source row and whether a fuel-meter value is present. Writes split.json.
  2. alpha nodes (thresholds/alpha_nodes.py). Which ALPHA curve nodes sit on held-out rows, so the
     calibration may not use them. Reads data/engines/<id>/epa_engine.json and split.json.
  3. B58 propagation (thresholds/b58_propagation.py, about three minutes). The B58's sensitivities
     with its baseline ECU in the loop, at its locked climb's cell: a torque bias's gas, flow and
     housing response, the lambda and spark levers, the housing node's f and tau. The B58 plant only
     (engines.get("b58")). Writes b58_propagation.json.
  4. knee shift (thresholds/knee_shift.py). The slope of d against a knee shift, re-scored from the
     committed per-step records of results/agents/terrain_dt1 and extremes_dt1 (gitignored, so this
     step runs only where they are). No model run. Writes knee_shift.json.
  5. ECU shifts (thresholds/ecu_shift.py). The B58 baseline ECU's boosted lambda and spark shifted,
     24 runs (9 at the fixed 1123 K knee, 15 under decision 33's K3), each in its own process: the
     head-start pair's response that E8 is measured against. The B58 plant only. Writes ecu/*.json.
  6. contract (thresholds/contract.py). Every R, from the MEI, R1 and steps 1-5, and the JSON. Also
     reads each engine's epa_engine.json for its fuel analysis, the tables' fuel_report column, and
     the D3 files C3 may read, hashed and checked against the team's data folder's MANIFEST.csv
     (GRAD_ENGINE_DATA, else C:\\Users\\badcl\\Desktop\\GRAD-engine-data). Writes
     results/ENGINE_THRESHOLDS.json.
  7. document (thresholds/document.py). The .md, from thresholds/document_template.md: every number
     that steps 1-6 compute is filled in from them, and every sentence whose wording depends on one
     is checked against it first. Writes results/ENGINE_THRESHOLDS.md. It needs git and a git
     checkout of the repository: its last claim, that nothing has been fitted, is checked against
     the .py files a commit would hold (git ls-files), and in a copy without .git it stops there.

WHAT IT NEVER DOES
------------------
It never compares a model with EPA data. No EPA torque, fuel-flow or turbine-inlet-temperature value
is read as a number, no model is run on an EPA row, and no model-versus-EPA error is computed:
steps 1, 2, 6 and 7 read the EPA tables' structure, and steps 3-5 run the B58 plant alone. It fits
nothing, calibrates nothing and trains nothing; calibrate_epa.py, which will, must record the JSON's
sha256. It writes only into results/ENGINE_THRESHOLDS/ and the two contract files. Every plant call
passes its engine explicitly (mistake 1; test_engine_threading.py scans this file and the package).

Rule 0 of the contract: nothing in it changes after any fit runs. A run of this file after that point
writes a new contract, which is disclosed and under which every result is reported beside the old.
"""
import argparse
import os
import platform
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from thresholds import common  # noqa: E402

# The files whose sha256 the JSON records as its generators (step 6 hashes them, CRLF read as LF).
GENERATORS = ("engine_thresholds.py", "thresholds/__init__.py", "thresholds/common.py", "thresholds/split.py",
              "thresholds/alpha_nodes.py", "thresholds/b58_propagation.py", "thresholds/knee_shift.py",
              "thresholds/ecu_shift.py", "thresholds/contract.py", "thresholds/document.py",
              "thresholds/document_template.md")


def run_steps(jobs):
    """Steps 1-5, in order, each output and printout into results/ENGINE_THRESHOLDS/."""
    import numpy as np
    seconds = {}

    def timed(name, fn, *args):
        t0 = time.time()
        print(f"\n== step {len(seconds) + 1}: {name}", flush=True)
        with common.printout(name):
            out = fn(*args)
        seconds[name] = round(time.time() - t0, 1)
        return out

    from thresholds import split as S
    sp = timed("split", S.run)
    from thresholds import alpha_nodes as A
    timed("alpha_nodes", A.run, sp)
    from thresholds import b58_propagation as P
    timed("b58_propagation", P.run)
    from thresholds import knee_shift as K
    timed("knee_shift", K.run)
    from thresholds import ecu_shift as U
    timed("ecu", U.run_all, jobs)
    common.write_json(os.path.join(common.OUT_DIR, "run.json"), dict(
        python=platform.python_version(), numpy=np.__version__, platform=platform.platform(), jobs=jobs,
        steps=seconds))


def build(write):
    """Steps 6 and 7: the JSON and the .md, as text. With write, both files and the steps'
    printouts are written; without, nothing is."""
    from thresholds import contract as C
    from thresholds import document as D
    gens = {g: common.sha_text(os.path.join(HERE, g)) for g in GENERATORS}
    inp = C.load_inputs()
    with common.printout("contract", write=write):
        print("\n== step 6: contract")
        contract, ns = C.build(inp, gens, C.d3_files())
        C.report(contract, ns)
    json_text = C.dumps(contract)
    with common.printout("document", write=write):
        print("\n== step 7: document")
        md_text = D.render(contract, ns, inp)
    return json_text, md_text


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--build-only", action="store_true", help="steps 6 and 7 only, from the saved outputs of steps 1-5")
    g.add_argument("--check", action="store_true", help="steps 6 and 7 in memory; exit 1 if a contract file differs")
    ap.add_argument("--jobs", type=int, default=None, help="step 5's runs at a time (default: one per CPU, at most 24)")
    a = ap.parse_args()
    os.chdir(HERE)
    if not (a.build_only or a.check):
        from thresholds import ecu_shift as U
        jobs = a.jobs or min(len(U.RUNS), os.cpu_count() or 1)
        run_steps(jobs)
    json_text, md_text = build(write=not a.check)
    if a.check:
        bad = []
        for path, text in ((common.CONTRACT_JSON, json_text), (common.CONTRACT_MD, md_text)):
            try:
                with open(path, "rb") as fh:
                    have = fh.read().replace(b"\r\n", b"\n").decode("utf-8")
            except OSError:
                have = None
            if have != text:
                bad.append(common.rel(path))
        print("\nCHECK: " + ("both contract files are what steps 6 and 7 write" if not bad
                             else "differs from what steps 6 and 7 write: " + ", ".join(bad)))
        sys.exit(1 if bad else 0)
    common.write_text(common.CONTRACT_JSON, json_text)
    common.write_text(common.CONTRACT_MD, md_text)
    print(f"\nwritten: {common.rel(common.CONTRACT_JSON)} (sha256 {common.sha_text(common.CONTRACT_JSON)}), "
          f"{common.rel(common.CONTRACT_MD)} (sha256 {common.sha_text(common.CONTRACT_MD)})")


if __name__ == "__main__":
    main()
