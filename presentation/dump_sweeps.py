"""Dump real plant sweeps for the explainer site. Read-only."""
import json, sys, os
import numpy as np
# AUDIT.md L11: was a hard-coded absolute path from one
# machine, so these scripts ran for exactly one person.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from plant import predict, b58, run_cycle, Operating

GEO = b58()
out = {}

# --- spark sweep at a boosted mid-range point -------------------------------
CASES = [
    ("part",  dict(rpm=2000, map_kpa=60,  iat_k=308, ect_k=363, lam=1.0)),
    ("mid",   dict(rpm=3000, map_kpa=140, iat_k=323, ect_k=363, lam=1.0)),
    ("boost", dict(rpm=3000, map_kpa=200, iat_k=333, ect_k=363, lam=1.0)),
]
for name, op in CASES:
    rows = []
    for sp in np.arange(-6, 44.5, 1.0):
        r = predict(spark_btdc=float(sp), geo=GEO, **op)
        rows.append([round(float(sp),1), round(r["torque_nm"],1),
                     round(r["knock_integral"],4), round(r["egt_c"],1),
                     round(r["p_max_bar"],1), round(r["mfb50_deg"],2)])
    out["spark_" + name] = dict(op=op, cols=["spark_btdc","torque_nm","ki","egt_c","pmax_bar","mfb50"], rows=rows)

# --- lambda sweep at the boosted point --------------------------------------
rows = []
for lam in np.arange(0.75, 1.181, 0.01):
    r = predict(rpm=4500, map_kpa=200, iat_k=333, ect_k=363, spark_btdc=12.0,
                lam=float(lam), geo=GEO)
    rows.append([round(float(lam),3), round(r["torque_nm"],1), round(r["egt_c"],1),
                 round(r["knock_integral"],4), round(r["mdot_fuel_gps"],2)])
out["lambda_sweep"] = dict(op=dict(rpm=4500, map_kpa=200, spark_btdc=12.0),
                           cols=["lam","torque_nm","egt_c","ki","fuel_gps"], rows=rows)

# --- in-cylinder pressure trace, three spark timings ------------------------
import plant as P
traces = {}
for label, sp in [("retarded", 4.0), ("mbt_ish", 18.0), ("knocking", 32.0)]:
    op = Operating(rpm=3000, map_kpa=200, iat_k=333, ect_k=363,
                   spark_btdc=sp, lam=1.0, p_exh_kpa=max(105.0, 200*P.EXH_BACKPRESSURE_RATIO))
    r = run_cycle(op, geo=GEO, dtheta=0.5)
    traces[label] = dict(spark=sp, ki=round(r.knock_integral,3),
                         torque=round(r.torque_nm,1), pmax=round(r.p_max_bar,1),
                         mfb50=round(r.mfb50_deg,2))
out["pressure_meta"] = traces

# --- thermal first-order: real tau values from the repo ---------------------
from thermal import ThermalParams
tp = ThermalParams()
out["thermal"] = dict(c_block=tp.c_block, c_oil=tp.c_oil, c_turb=tp.c_turb,
                      ua_turb_amb=tp.ua_turb_amb, ua_gas_turb=tp.ua_gas_turb,
                      ua_block_oil=tp.ua_block_oil, ua_block_amb=tp.ua_block_amb,
                      ua_oil_amb=tp.ua_oil_amb)

dst = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sweeps.json")
json.dump(out, open(dst,"w"), separators=(",",":"))
print("wrote", dst, os.path.getsize(dst), "bytes")
for k,v in out.items():
    if isinstance(v, dict) and "rows" in v:
        print(" ", k, len(v["rows"]), "rows")
print(json.dumps(out["pressure_meta"], indent=1))
