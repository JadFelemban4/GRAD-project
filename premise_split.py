"""premise_split.py -- the 8 October plant changes on the locked climb, one at a time.

    python premise_split.py      -> results/premise_split.json  (about two minutes)

Two of the four steps Jad and Ghassan agreed on 30 September change the physics
the hand-written premise runs on: the thermal network's sub-stepping
(thermal.DT_SUB_MAX) and the 8 s ramp on every grade change (engine_env.
GRADE_RAMP_S). This switches each on in turn, in its own process, and runs
check_premise.py's four policies on the locked climb each time:

    merged plant     one explicit Euler step per environment step, the climb a step at 180 s
    + sub-stepping   the thermal network at most 0.1 s per sub-step
    + ramp           the climb ramped over 8 s from 180 s
    both             the plant of 8 October, the one X1 trains on

RETIRED-OK: 920.1 -- the merged plant's premise: this script's first row, by design
The first row must reproduce the merged plant's published premise (920.1 at
883 C) and the last today's results/premise.json; the script checks both and
fails loudly otherwise. compare_calibration.py's record of 28 September ends
at the merged plant; these four rows carry it on, and make_page.py draws them
on the same chart. The spark cap (the third step) does not touch a hand-written
policy -- none of them trims spark -- and the fingerprint (the second) is not
physics.
"""
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "results", "premise_split.json")
STATES = ((False, False, "merged plant, 30 September"),
          (True, False, "+ thermal network sub-stepped"),
          (False, True, "+ every grade change ramped over 8 s"),
          (True, True, "both: the plant of 8 October"))
MERGED_BASELINE = 920.1


def run(state):
    substep, ramp, name = state
    sys.path.insert(0, HERE)
    import thermal
    import engine_env as E
    import check_premise as C
    if not substep:
        thermal.DT_SUB_MAX = 1e9                      # one step per environment step, as before
    if not ramp:
        ramped = E.make_grade_climb

        def stepped(*a, **k):
            c = ramped(*a, **k)
            g = np.zeros_like(c["grade"])
            g[int(180.0 / float(k.get("dt", 1.0))):] = k.get("grade", 0.12)
            c["grade"] = g
            return c
        C.make_grade_climb = stepped
    out, raw = {}, {}
    for key, pol in (("baseline", C.p_neutral), ("reactive", C.p_reactive),
                     ("current_grade", C.p_grade_now), ("predictive", C.p_predictive)):
        r = C.rollout(pol)
        raw[key] = float(r["damage"])
        out[key] = round(raw[key], 1)
        if key == "baseline":
            out["peak_turb"] = round(float(r["peak_turb"]), 1)
            out["peak_oil"] = round(float(r["peak_oil"]), 1)
            out["knock_events"] = int(r["knock"])
    # from the UNROUNDED damages, as check_premise.py computes its own lines
    b = raw["baseline"]
    out["preview_vs_grade"] = round(100.0 * (raw["current_grade"] - raw["predictive"]) / b, 2)
    out["grade_cut"] = round(100.0 * (1.0 - raw["current_grade"] / b), 1)
    out.update(step=name, substep=substep, ramp=ramp)
    return out


def main():
    with ProcessPoolExecutor(len(STATES)) as ex:
        rows = list(ex.map(run, STATES))
    for r in rows:
        print(f"{r['step']:40s} baseline {r['baseline']:6.1f} at {r['peak_turb']:5.1f} C   "
              f"current-grade cuts {r['grade_cut']:4.1f} %   preview over it {r['preview_vs_grade']:+.2f} pts")
    with open(os.path.join(HERE, "results", "premise.json"), encoding="utf-8") as fh:
        today = json.load(fh)
    want = today["baseline ECU (true neutral)"]["damage"]
    if abs(rows[0]["baseline"] - MERGED_BASELINE) > 0.05:
        raise SystemExit(f"the merged-plant row reads {rows[0]['baseline']}, not {MERGED_BASELINE}: "
                         "this script no longer reproduces that plant")
    if abs(rows[-1]["baseline"] - float(want)) > 0.05:
        raise SystemExit(f"the last row reads {rows[-1]['baseline']}, results/premise.json {want}")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(dict(steps=rows, note=__doc__.split("\n\n")[1].strip()), fh, indent=1)
        fh.write("\n")
    print(f"wrote {os.path.relpath(OUT, HERE)}")


if __name__ == "__main__":
    main()
