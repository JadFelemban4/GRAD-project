"""alpha_nodes.py -- step 2 of engine_thresholds.py: which ALPHA curve nodes sit on held-out rows.

Structure only. Reads each engine's epa_engine.json (epa_map.py: every node of the full-throttle and
closed-throttle curves, with the table and spreadsheet row it was measured at, or none) and step 1's
split.json. No model, no error. Writes results/ENGINE_THRESHOLDS/alpha_nodes.json; a node on a
held-out row is removed from what the calibration may use (section 2.3 of the contract).
"""
import os

from thresholds import common

OUT = os.path.join(common.OUT_DIR, "alpha_nodes.json")


def compute(split):
    out = {}
    for eng in common.EPA_ENGINES:
        held = {(r["table"], r["source_row"]) for r in split[eng]["held_out_rows"]}
        e = common.load_json(os.path.join(common.ENGINE_DIR, eng, "epa_engine.json"))
        rows = []
        for curve in ("wot_torque_curve", "closed_throttle_torque_curve"):
            c = e[curve]
            for rpm, m in zip(c["speed_rpm"], c["measured_at_speed"]):
                if m is None:
                    continue
                rows.append(dict(curve=curve, node_rpm=round(rpm, 1), table=m["table"], source_row=m["source_row"],
                                 held_out=(m["table"], m["source_row"]) in held))
        out[eng] = rows
    return out


def report(out):
    for eng, rows in out.items():
        print(eng)
        for r in rows:
            if r["held_out"]:
                print("   HELD OUT", r)
        print("   nodes", len(rows), "held out", sum(r["held_out"] for r in rows))


def run(split):
    out = compute(split)
    common.write_json(OUT, out)
    report(out)
    return out
