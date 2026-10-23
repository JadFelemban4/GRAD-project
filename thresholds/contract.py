"""contract.py -- step 6 of engine_thresholds.py: every R, and results/ENGINE_THRESHOLDS.json.

Reads the outputs of steps 1-5 (results/ENGINE_THRESHOLDS/), each engine's epa_engine.json (its
fuel analysis), the tables' fuel_report column, and the D3 files C3 may read, which it hashes and
checks against the team's data folder's MANIFEST.csv. Every R is computed here from those numbers,
the MEI and R1, so the arithmetic is in code. It reads no EPA torque, fuel or TIT value and runs no
model.

THE BUDGET IS DECISION 38 (results/VALIDATION_DECISIONS.md section G, adopted 21 October 2026 on
Ghassan's delegation): b = MEI/6 = 0.905 points per part, for six parts, so that the six aligned at
their limits add to exactly the MEI. N_SHARES holds it; every d-row R, the bands and S2 follow
from b. Version 2 of the contract had b = MEI/5; build() still computes those values, and the
JSON keeps them (budget.version_2_at_mei_over_5) so the 5/6 scaling can be checked.
Decision 36 is the rule for an untested row (on_failure.d), decision 37 the collapse test's
equivalence margin (collapse_test).

VERSION 4 (22 October 2026, corrected seven times on 23 October after its seven reviews; build step
2's WP2; decision 39 of results/VALIDATION_DECISIONS.md section H, written as docs/build_step_2/
AMENDMENTS.md A1-A3, E1-E6, F1-F3 and its section 3 word it). Written after the plant changes of
build step 2 and before any fit. It moves no R or split of version 3. Of the populations version 3
named it moves one, E8's: dl is taken over the held-out Final rows that publish a lambda and ds over
those that publish a spark, subsets of version 3's, each needing E8_MIN_ROWS rows or E8 has no
statistic (version 4's reading of decision 54). It writes three things version
3 did not name: one population, C5's steps (decision 73, which narrows the plan's reading of version
3, every scored-climb step), the inputs of the rows without a reading (decision 54), and the
statistic details version 3 left open (decision 57: conventions.statistic_details). Every number
computed from steps 1-5 is computed as version 3 computed it, from the same saved outputs. What it
changes is the statistic and rule text decision 39 names, decision 57's, and decisions 73-76, which
its reviews raised (their text is section H's rows of 23 October; section H adopts them under the
same delegation as 39-72): C5's statistic, steps and threshold, its climb slots, shared by the four
cars, a slot at the redraw cap, and the cap and the discard bound themselves (decisions 70, 40, 64,
73, 74, 75 and 76: CARS, on_failure.rule, order_of_work; REDRAW_CAP, REDRAW_DISCARDS, REDRAW_STREAM_TAG,
C5_THIN_SHARE), D1's and E8's statistic text (rows; so the D1 and E8 entries of thresholds), the
neutral-action identity (39(b):
model_form.neutral_action_identity), the in-sample stage (39(a), 49, 55: model_form), the rows
without a reading (54: conventions), the E6 readings and the Tests lists (59: perturbations_E6,
tests_lists, on_failure.perturbation), L1's tightening plant (71: rows, order_of_work), and every
code citation, moved to the lines of the tree it was written on (the .md's section 13 lists the
moves; step 7 checks each code citation's line). The JSON's schema is 4 because new keys hold the
new rules; version_4 lists them. plant_values() reads the few numbers the text takes from the plant
code itself (the neutral action, the shared rich slope, the B58's lambda clip), and version_4
records them, since no sha256 of the JSON covers the plant code.
"""
import csv
import glob
import json
import math
import os

from thresholds import common

MEI = 5.43                      # points of cut, decision 5 (VALIDATION_DECISIONS.md:55)
R1_K = 10.0                     # housing-equivalent K, decision 3 (VALIDATION_DECISIONS.md:53; VALIDATION_PLAN.md:116)
N_SHARES = 6                    # decision 38: b = MEI/6 per part, six parts (VALIDATION_DECISIONS.md section G)
N_SHARES_VERSION_2 = 5          # version 2's valuation, kept in the JSON for the record
T_AMB_C = 42.0                  # the scored roads' ambient
PARTS = [
    ("P1", "the operating point and its flows at the demanded torque", ["D1"]),
    ("P2", "the lambda lever on the gas temperature", ["E4b"]),
    ("P3", "the housing level's spread across operating points", ["L1"]),
    ("P4", "the baseline ECU's strategy at high load", ["E8"]),
    ("P5", "the car", ["C3b", "C3d"]),
    ("P6", "the table", ["S1a", "S1b", "S1c", "S2a", "S2b"]),
]
D_ROWS = ("D1", "E4b", "L1", "E8", "C3b", "C3d", "S1a", "S1b", "S1c", "S2a", "S2b")   # the R that follow from b
SHIFTS_K = (-57, -25, -10, -5, 5, 10, 25, 57)      # the knee shifts of step 4
ETA_LO, ETA_HI, ETA = 0.86, 0.98, 0.92              # the driveline efficiency's span (E6 row 10)
RADIUS_GAP = 0.016                                  # the N/V and D3 rolling radii differ by 1.6 %
D3_FIRST_BATCH = (61704001, 61704044)               # the CX-9 tests on the first fuel batch
M_C, M_H, M_O2, X_O2 = 12.011, 1.008, 31.998, 0.2314
BATCH = {"26864": "mazda_25t", "25842": "honda_l15b7", "25278": "ford_27tt"}
DECISIONS_DOC = "results/VALIDATION_DECISIONS.md"
V3_TREE = "ef5e14e"             # version 3's commit: the tree its code citations name
V3_LAM_CLIP = (0.70, 1.25)      # version 3's lambda clip, every engine: engine_env.py line 1006 of V3_TREE (step 7 checks it)
# Decisions 73-76 were raised on 23 October 2026 by the reviews of version 4 and written into section H by the
# agents writing it, two days after Ghassan's delegation of 21 October; section H adopts each under that
# delegation, as it adopts 39-72, which the agents wrote in on 22 October (version 4's fourth review; the second
# had marked 73 and 74 pending his own answer). His column records the delegation, not an answer to these rows,
# and since the fifth review each of their cells says so ("adopted by the agents 23 Oct, not yet seen").
RAISED_V4 = ("raised 23 October 2026 by the reviews of version 4 and adopted by the agents writing it under Ghassan's "
             "delegation of 21 October 2026, as every decision of section H is; no answer of his to it is recorded")
# Decision 76 (23 October 2026, raised by the fifth review of version 4): C5's redraw cap and a bound on the
# candidates a slot's redraws may discard, fixed here before any fit and from no data (DESIGN), so that the roads
# step commits this contract's values with the roads instead of choosing them after the first fit, with the
# in-sample E1a known. The sheet's row 76 states the same numbers (step 7 checks it).
REDRAW_CAP = 3                  # redraws per climb slot, counted over all cars (decision 75)
REDRAW_DISCARDS = 100           # candidates discarded per slot over its redraws; at the bound the slot stops, as at the cap
# After the sixth review of version 4: each slot's redraw stream is drawn from
# numpy.random.default_rng([roads_seed, REDRAW_STREAM_TAG, k]), k the slot's index in the redraw order, so the
# derivation is not left to the roads step. The tag is a label, as engine_env.TerrainTrainingEnv._TERRAIN_STREAM is,
# not a quantity.
REDRAW_STREAM_TAG = 0xC5
# Version 4's reading of decision 54 after its fifth review: each of E8's subsets (dl over the Final rows that
# publish a lambda, ds over those that publish a spark) needs this many rows, the clusters a line needs
# (thresholds/split.py MIN_CLUSTERS; step 7 checks they agree), or E8 has no statistic.
E8_MIN_ROWS = 3
# Decision 73 after the fifth review: a climb gated on less than this share of its steps on a car is flagged thin
# there (cars C5 steps.thin; its outcome there, after the seventh review: steps.outcome). DESIGN, chosen from no data
# (labelled after the sixth review): no road has been drawn.
C5_THIN_SHARE = 0.5


def plant_values():
    """The numbers version 4's text reads from the plant code, not from steps 1-5: the neutral
    action as the environment applies it (engine_env.neutral_action() through
    SupervisoryTunerEnv._rescale, called unbound: it reads no state of the environment), the shared
    rich slope of combustion_efficiency (engines.SHARED_RICH_SLOPE) and the B58's lambda clip
    (engines.get('b58').engine.ecu). Imported here, not at the top: only version 4 needs them."""
    import engine_env as E
    import engines
    act = E.SupervisoryTunerEnv._rescale(None, E.neutral_action())
    ecu = engines.get("b58").engine.ecu
    return dict(
        neutral_action_rescaled=dict(
            values=[float(x) for x in act], dtype=act.dtype.name,
            source="engine_env.SupervisoryTunerEnv._rescale(engine_env.neutral_action()): spark, lambda and boost trims, fan, pump"),
        shared_rich_slope=dict(value=engines.SHARED_RICH_SLOPE, source="engines.SHARED_RICH_SLOPE"),
        b58_lambda_clip=dict(lam_floor=ecu.lam_floor, lam_ceiling=ecu.lam_ceiling,
                             source="engines.get('b58').engine.ecu (engine_specs/b58.toml:143-144)"))


def rdown(x, nd=1):
    """Round a requirement DOWN (never looser than the arithmetic)."""
    q = 10 ** nd
    return math.floor(x * q + 1e-9) / q


def afr_from_carbon(wc):
    """Stoichiometric AFR of an oxygen-free C-H fuel with carbon weight fraction wc (hydrogen the balance),
    against air with an oxygen mass fraction of 0.2314."""
    wh = 1.0 - wc
    return (wc / M_C + wh / (4.0 * M_H)) * M_O2 / X_O2


def pair(rows, key):
    d = rows[key]
    return (1 - d["current-grade"] / d["baseline"]) - (1 - d["reactive"] / d["baseline"])


def cuts(rows, key):
    d = rows[key]
    return {p: 100.0 * (1 - d[p] / d["baseline"]) for p in ("reactive", "current-grade", "predictive")}


def response(table, var):
    """Relative change of the head-start pair (current-grade minus reactive) against a shift of the ECU's
    boosted output, both damage readings; returns sorted (shift, worst |change| signed) points."""
    pts = {0.0: 0.0}
    for name, j in table.items():
        if name == "nominal":
            continue
        s = j["dlambda"] if var == "lambda" else j["dspark"]
        other = j["dspark"] if var == "lambda" else j["dlambda"]
        if s == 0.0 or other != 0.0:
            continue
        ch = []
        for key in ("damage", "damage_thermal"):
            ch.append(pair(j, key) / pair(table["nominal"], key) - 1.0)
        pts[s] = max(ch, key=abs)
    return sorted(pts.items())


def interp(pts, x):
    """Piecewise-linear through the measured points; linear extrapolation from the last segment."""
    xs = [p[0] for p in pts]
    if x <= xs[0]:
        (x0, y0), (x1, y1) = pts[0], pts[1]
    elif x >= xs[-1]:
        (x0, y0), (x1, y1) = pts[-2], pts[-1]
    else:
        i = max(k for k in range(len(xs) - 1) if xs[k] <= x)
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def worth(pts, side, target):
    """The smallest shift on one side at which |change| reaches target: linear interpolation between the
    measured points, or, if the largest measured shift stays below target, linear extrapolation from the
    last measured segment, flagged."""
    seq = [p for p in pts if (p[0] >= 0 if side > 0 else p[0] <= 0)]
    seq = sorted(seq, key=lambda p: abs(p[0]))
    for (x0, y0), (x1, y1) in zip(seq, seq[1:]):
        if abs(y1) >= target:
            if abs(y1 - y0) < 1e-12:
                return dict(shift=round(x1, 4), extrapolated=False)
            return dict(shift=round(x0 + (x1 - x0) * (target - abs(y0)) / (abs(y1) - abs(y0)), 4), extrapolated=False)
    (x0, y0), (x1, y1) = seq[-2], seq[-1]
    return dict(shift=round(x1 + (x1 - x0) * (target - abs(y1)) / (abs(y1) - abs(y0)), 4), extrapolated=True,
                largest_measured=[x1, round(y1, 4)])


def requirements(n_shares, flow_per_pct, slope):
    """b = MEI/n_shares, b/MEI, every d-row R from b (section 1.3), and the errors worth b of the
    descriptive rows E1b and E2b. The level rows' R come from R1 alone (build())."""
    b = MEI / n_shares
    b_frac = b / MEI
    R = {}
    R["D1"] = rdown(100 * b_frac)                       # %: flow elasticity <= 1
    R["E4b"] = rdown(100 * b_frac)
    R["L1"] = rdown(b / slope)                          # K of spread: b / the largest knee-shift slope
    R["E8"] = rdown(100 * b_frac)                       # % of the head-start pair
    R["C3b"] = rdown(100 * b_frac)
    R["C3d"] = rdown(100 * b_frac)
    R["S1a"] = rdown(100 * b_frac)
    R["S1b"] = rdown(100 * b_frac / flow_per_pct)       # % torque, a screen: (b/MEI) / 1.353
    R["S1c"] = rdown(100 * b_frac)
    R["S2a"] = round(b, 3)
    R["S2b"] = round(b, 3)
    worth_b = {"E1b_torque_pct": rdown(100 * b_frac / flow_per_pct), "E2b_fuel_pct": rdown(100 * b_frac)}
    return b, b_frac, R, worth_b


def load_inputs():
    """The outputs of steps 1-5, as they sit in results/ENGINE_THRESHOLDS/."""
    d = common.OUT_DIR
    k3, fix = {}, {}
    for p in sorted(glob.glob(os.path.join(common.ECU_DIR, "*.json"))):
        j = common.load_json(p)
        if "seconds" in j:
            raise SystemExit(f"contract: {common.rel(p)} holds a wall-clock time, so its sha256 cannot be reproduced; "
                             "it was written before ecu_shift.py stopped recording one: re-run step 5")
        (k3 if j["mode"] == "k3" else fix)[j["name"]] = j
    run = common.load_json(os.path.join(d, "run.json")) if os.path.exists(os.path.join(d, "run.json")) else {}
    return dict(split=common.load_json(os.path.join(d, "split.json")),
                alpha=common.load_json(os.path.join(d, "alpha_nodes.json")),
                b58=common.load_json(os.path.join(d, "b58_propagation.json")),
                knee=common.load_json(os.path.join(d, "knee_shift.json")), K3=k3, FIX=fix, run=run)


def d3_files():
    """The D3 files C3 may read (the first fuel batch), hashed and checked against the data folder's
    manifest."""
    manifest = {}
    mpath = os.path.join(common.DATA_FOLDER, "MANIFEST.csv")
    if not os.path.isfile(mpath):
        raise SystemExit(f"no data folder at {common.DATA_FOLDER} (set GRAD_ENGINE_DATA): the D3 files of C3 "
                         "are pinned by hashing them against its MANIFEST.csv")
    with open(mpath, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            manifest[os.path.normcase(r["local_path"])] = r["sha256"]
    d3_dir = os.path.join(common.DATA_FOLDER, "anl-d3-2016-mazda-cx9", "extended-data-set")
    out = []
    for fn in sorted(os.listdir(d3_dir)):
        tid = fn.split()[0]
        if tid.isdigit() and D3_FIRST_BATCH[0] <= int(tid) <= D3_FIRST_BATCH[1]:
            p = os.path.join(d3_dir, fn)
            h = common.sha_raw(p)
            m = manifest.get(os.path.normcase(p))
            assert m == h, (fn, m, h)
            out.append(dict(test=tid, file=f"anl-d3-2016-mazda-cx9/extended-data-set/{fn}", sha256=h))
    return out


def build(inp, generators, d3, n_shares=N_SHARES):
    """The contract's JSON (a dict) and the namespace of every number the .md quotes.

    inp: load_inputs(); generators: {repository path: sha256} of the code that wrote it; d3: d3_files()."""
    split, alpha, b58, knee, K3, FIX = (inp[k] for k in ("split", "alpha", "b58", "knee", "K3", "FIX"))
    ENGS = common.EPA_ENGINES
    PV = plant_values()                       # version 4: the numbers its text reads from the plant code
    B58_CLIP = PV["b58_lambda_clip"]

    # ============================================================== 2. the B58 coefficients, ECU in the loop
    c = b58["climb"]
    hs = c["housing"]
    env = b58["env_torque_bias"]
    G_K = c["point"]["egt"] - T_AMB_C                                # 980.27 K: the B58 model's climb gas over 42 C
    GAS_PER_PCT = max(abs(env["+0.01"]["degt_k"]), abs(env["-0.01"]["degt_k"]))            # 3.317 K per 1 % torque
    FLOW_PER_PCT = 100.0 * max(abs(env["+0.01"]["dmdot_rel"]), abs(env["-0.01"]["dmdot_rel"]))   # 1.353 % per 1 % torque
    HOUSE_PER_PCT_B58 = max(abs(env["+0.01"]["dTh_median_k"]), abs(env["-0.01"]["dTh_median_k"]))  # 4.463 K (B58 f)

    def house_bound(gas_k, flow_rel):
        """max over 0 <= f <= 1 of |f*gas + f(1-f)*G*flow| (gas in K, flow relative): the steady housing
        T_h = f T_gas + (1 - f) T_amb moves by f*dT_gas + f(1 - f)(T_gas - T_amb) dln(mdot), and f is not known
        for an engine whose housing is assumed."""
        A, Bq = gas_k, G_K * flow_rel
        cands = [abs(A)]                                             # f = 1
        if abs(Bq) > 1e-12:
            fs = (A + Bq) / (2.0 * Bq)
            if 0.0 <= fs <= 1.0:
                cands.append(abs(fs * A + fs * (1.0 - fs) * Bq))
        return max(cands)

    HOUSE_PER_PCT_BOUND = house_bound(GAS_PER_PCT, FLOW_PER_PCT / 100.0)   # 5.183 K
    HOUSE_PER_PCT_FLOW = G_K / 4.0 / 100.0                                 # 2.451 K per 1 % of flow
    F_STAR = (GAS_PER_PCT + G_K * FLOW_PER_PCT / 100) / (2 * G_K * FLOW_PER_PCT / 100)

    # ============================================================== 3. the knee-shift slope (L1)
    slopes = []
    for st, res in knee.items():
        for knock in (True, False):
            r0 = res["rows"][f"knock={knock} shift=+0"]["d_mean"]
            for s in SHIFTS_K:
                r = res["rows"][f"knock={knock} shift={s:+d}"]["d_mean"]
                slopes.append(dict(slope=abs((r - r0) / s), set=st, knock=knock, shift_k=s))
    SLOPE = max(slopes, key=lambda x: x["slope"])
    SLOPE_10 = max((x for x in slopes if abs(x["shift_k"]) == 10), key=lambda x: x["slope"])

    # ============================================================== 1, 5. the budget and the Rs
    B, B_FRAC, R_D, WORTH_B = requirements(n_shares, FLOW_PER_PCT, SLOPE["slope"])
    LINEAR = len(PARTS) * B
    RSS = math.sqrt(len(PARTS)) * B
    R = {}
    R["E1a"] = rdown(R1_K / HOUSE_PER_PCT_BOUND)        # % torque: 10 / 5.183
    R["E2a"] = rdown(R1_K / HOUSE_PER_PCT_FLOW)         # % fuel: 10 / 2.451
    R["E3a"] = R1_K
    R["E4a"] = R1_K
    R["L0"] = R1_K
    R.update(R_D)
    _, _, R_V2, WORTH_B_V2 = requirements(N_SHARES_VERSION_2, FLOW_PER_PCT, SLOPE["slope"])

    # ============================================================== 4. the ECU strategy (E8): the pair under K3
    RESP_L = response(K3, "lambda")
    RESP_S = response(K3, "spark")
    RESP_L_FIX = response(FIX, "lambda")
    RESP_S_FIX = response(FIX, "spark")
    W = {"lambda_rich": worth(RESP_L, -1, B_FRAC), "lambda_lean": worth(RESP_L, +1, B_FRAC),
         "spark_retard": worth(RESP_S, -1, B_FRAC), "spark_advance": worth(RESP_S, +1, B_FRAC)}

    # ============================================================== 6. fuels, lambda floors, C3 input uncertainty
    FUEL = {}
    for eng in ENGS:
        af = common.load_json(os.path.join(common.ENGINE_DIR, eng, "epa_engine.json"))["alpha_fuel"]
        FUEL[eng] = dict(ftag=af["id"], lhv_mj_per_kg=af["energy_density_MJpkg"], carbon_weight_fraction=af["carbon_weight_fraction"],
                         afr_st=round(afr_from_carbon(af["carbon_weight_fraction"]), 3), alcohol_pct_vol=af.get("alcohol_pct_vol"))
    FUEL_BY_TABLE = {}
    for eng in ENGS:
        FUEL_BY_TABLE[eng] = {}
        for fn in split[eng]["tables"]:
            with open(os.path.join(common.ENGINE_DIR, eng, fn), newline="", encoding="utf-8") as fh:
                tags = sorted({r.get("fuel_report") for r in csv.DictReader(fh)})
            assert len(tags) == 1, (eng, fn, tags)
            src = BATCH[tags[0]]
            FUEL_BY_TABLE[eng][fn] = dict(FUEL[src], fuel_report=tags[0],
                                          source=f"epa_engine.json alpha_fuel of {src}" + ("" if src == eng else " (the same FTAG)"))

    LAM_FLOOR = {}
    for eng in ENGS:
        lm = split[eng]["lambda_min_cell_referenced"]["value"]
        LAM_FLOOR[eng] = dict(deepest_epa_lambda_cell_referenced=lm, floor=round(min(0.70, lm - 0.01), 3),
                              where=split[eng]["lambda_min_cell_referenced"])

    U_ETA = (ETA_HI - ETA_LO) / 2.0 / ETA / math.sqrt(3.0)          # relative, uniform over the span: 3.77 %
    U_RAD = RADIUS_GAP / math.sqrt(3.0)                             # the N/V and D3 radii differ by 1.6 %: 0.92 %
    U_C3_TORQUE = math.sqrt(U_ETA ** 2 + U_RAD ** 2)                 # on the torque demand
    U_C3_FUEL = U_C3_TORQUE * FLOW_PER_PCT                           # carried to the flow at the demand (x 1.353)

    # AFR_st sensitivity (E6 row 2): the convention is the table's fuel; the row moves to 14.7
    afr_conv = FUEL["mazda_25t"]["afr_st"]
    d_air = 14.7 / afr_conv - 1.0
    d_exh = (1.0 + 14.7) / (1.0 + afr_conv) - 1.0
    E6_AFR = dict(convention_afr=afr_conv, air_rel=d_air, exhaust_flow_rel=d_exh, tau_rel=-hs["f"] * d_exh,
                  housing_b58_k=hs["dTh_per_unit_ln_mdot"] * d_exh, housing_bound_k=G_K / 4.0 * d_exh)

    D3 = d3

    # ============================================================== 7. the rows
    SG = f"{DECISIONS_DOC} section G"
    LEVEL = ("level: the gas-side and operating-point input to the engine's 850 C sensitivity row (decision 33); a uniform "
             "level cancels from every cut and from d under K3; never drops the engine")
    DPART = lambda p: f"d: part {p} of the budget, b = MEI/{n_shares} = {B:.3f} points at d = MEI"  # noqa: E731
    LINE_RULE = ("per held-out line with >= 3 clusters (a steady row or a High Load Final row is one cluster); a line decides an OFF "
                 "label whatever its scatter, and a pass only if 2*u_stat <= R; the row reports the worst deciding line")
    HOT = "hot rows of held-out lines: High Load FINAL rows, and steady rows at or above the engine's hot MAP floor (High Load Initial rows never)"
    ROWS = [
        dict(id="E1a", kind="level", quantity="brake torque at EPA's inputs",
             statistic="largest |mean signed relative error| over the deciding held-out lines, per line over its hot rows; " + LINE_RULE,
             population=HOT, R=R["E1a"], unit="% of the measured torque", governs=LEVEL,
             basis=(f"a +1 % torque bias moves, in the environment with the ECU in the loop, the gas by {GAS_PER_PCT:.3f} K and the "
                    f"exhaust flow by {FLOW_PER_PCT:.3f} % (B58 locked climb, b58_propagation.json env_torque_bias); the housing "
                    f"equivalent is at most max_f [f*{GAS_PER_PCT:.3f} + f(1-f)*{G_K:.2f}*{FLOW_PER_PCT / 100:.5f}] = "
                    f"{HOUSE_PER_PCT_BOUND:.3f} K (f* = {F_STAR:.3f}); R1/{HOUSE_PER_PCT_BOUND:.3f} = {R1_K / HOUSE_PER_PCT_BOUND:.3f} %, "
                    f"rounded down. With the B58's own f (0.858) it would be 10/{HOUSE_PER_PCT_B58:.3f} = {R1_K / HOUSE_PER_PCT_B58:.2f} %")),
        dict(id="E1b", kind="descriptive", quantity="brake torque at EPA's inputs", statistic="mean absolute relative error over every fired held-out row (steady and Final)",
             population="held-out steady and High Load Final rows with BMEP >= 2 bar", R=None, unit="%",
             governs=f"descriptive since version 2: its d consequence is gated jointly with the flow by D1; worth b at {WORTH_B['E1b_torque_pct']} %",
             basis=f"{100 * B_FRAC:.2f} / {FLOW_PER_PCT:.3f} = {100 * B_FRAC / FLOW_PER_PCT:.2f} %, rounded down"),
        dict(id="E1i", kind="descriptive", quantity="brake torque, High Load INITIAL rows (a transient: the peak within 2 s of reaching the target)",
             statistic="mean signed relative error per held-out line", population="held-out High Load Initial rows", R=None, unit="%",
             governs="descriptive: the window is a thermal and sensor transient (logs/epa/README.md:101-104)", basis="no gate"),
        dict(id="E2a", kind="level", quantity="fuel mass flow (Coriolis meter) at EPA's inputs",
             statistic="largest |mean signed relative error| over the deciding held-out lines, per line over its hot rows with a meter reading; " + LINE_RULE,
             population=HOT + ", with fuel_meter_flow_gps", R=R["E2a"], unit="% of the measured flow", governs=LEVEL,
             basis=(f"a flow error alone moves the steady housing by f(1-f)(T_gas - T_amb) per unit ln(flow), at most "
                    f"{G_K:.2f}/4 = {G_K / 4:.2f} K, i.e. {HOUSE_PER_PCT_FLOW:.4f} K per 1 %; R1/{HOUSE_PER_PCT_FLOW:.4f} = "
                    f"{R1_K / HOUSE_PER_PCT_FLOW:.3f} %, rounded down (the B58's own f(1-f) = 0.122 would give 8.3 %)")),
        dict(id="E2b", kind="descriptive", quantity="fuel mass flow at EPA's inputs", statistic="mean absolute relative error over every fired held-out row with a meter reading",
             population="held-out steady and Final rows with BMEP >= 2 bar and a meter value", R=None, unit="%",
             governs=f"descriptive since version 2: the flow at the demanded torque (D1) is the d row; worth b at {WORTH_B['E2b_fuel_pct']} %",
             basis="no gate"),
        dict(id="E3a", kind="level", quantity="turbine-inlet gas temperature at lambda~1 (model t_exh after the port loss against EPA's Turbine Inlet Temp thermocouple)",
             statistic="largest |mean signed error| over the deciding held-out lines, per line over its hot lambda~1 rows; " + LINE_RULE,
             population=HOT + ", |lambda - lambda_ref| <= 0.02", R=R["E3a"], unit="K",
             governs=LEVEL, basis="R1 carried to the gas with f <= 1: a gas error e moves the steady housing by f*e <= e whatever the housing constants"),
        dict(id="E3b", kind="descriptive", quantity="turbine-inlet gas temperature at lambda~1", statistic="mean absolute error over every fired held-out lambda~1 row (steady and Final)",
             population="held-out rows with BMEP >= 2 bar and |lambda - lambda_ref| <= 0.02", R=None, unit="K", governs="descriptive", basis="no gate"),
        dict(id="E4a", kind="level", quantity="turbine-inlet gas temperature, enriched", statistic="largest |mean signed error| over the deciding held-out lines, per line over its enriched hot rows; " + LINE_RULE,
             population=HOT + ", lambda <= lambda_ref - 0.05", R=R["E4a"], unit="K", governs=LEVEL, basis="as E3a"),
        dict(id="E4b", kind="d", part="P2", quantity="the lambda lever: TIT change with lambda",
             statistic=("pooled fractional error eps = sum(L_S) / sum(L_S + e_enr - e_hat) - 1 over the enriched hot rows of held-out lines "
                        "with >= 3 boosted lambda~1 rows; L_S = S(row inputs, lambda 1) - S(row inputs); e_hat = the line's least-squares "
                        "line of the lambda~1 error against MAP (boosted lambda~1 rows, MAP >= 100 kPa), evaluated at the enriched row's MAP; "
                        "the distance by which that line is extrapolated in MAP is reported per line"),
             population="enriched hot rows (Final and steady) and boosted lambda~1 rows (steady and Final) of the same held-out line",
             R=R["E4b"], unit="% of the lever's effect", governs=DPART("P2"),
             basis=("a fraction eps on a lever's effect moves d by eps*(1 + ln(1 - c))*d to first order; |1 + ln(1 - c)| <= 1 holds only "
                    "for 0 <= c <= 1 - e^-2 = 0.865, so R = b/MEI holds the part to b there, and outside it the part's band is "
                    "multiplied by the realised max |1 + ln(1 - c)| (section 7)")),
        dict(id="E5", kind="descriptive", quantity="slope of TIT with MAP along rpm lines, on EPA's own ECU schedule",
             statistic="pooled slope ratio - 1: sum over lines of cov(MAP, S) / sum of cov(MAP, D), two windows",
             population="lambda~1 rows (steady and Final) of held-out lines with >= 3 rows in the window; A: MAP < 100 kPa and BMEP >= 2 bar; B: MAP >= 100 kPa",
             R=None, unit="%",
             governs=("descriptive since version 2: along the schedule the slope is about half spark term (B58: 1.473 K/kPa along it, "
                      "0.686 K/kPa at fixed spark), and the agents' boost lever acts at fixed spark (engine_env.py:1283, :1310, "
                      "SupervisoryTunerEnv.step: the ECU's spark is scheduled on the baseline's MAP and every policy takes it plus its trim); EPA has "
                      "no spark sweeps, so THE BOOST LEVER IS UNTESTED for every engine and is declared so"),
             basis="no gate"),
        dict(id="D1", kind="d", part="P1", quantity="the exhaust flow at the DEMANDED torque",
             statistic=("per fired held-out row with a meter reading: invert MAP so that the model delivers EPA's measured torque "
                        "(bisection over 20-400 kPa) at EPA's speed, intake temperature, coolant and the row's lambda convention, "
                        "with spark = EPA's spark + s*(MAP - MAP_EPA), s the engine's calibrated ECU's dspark/dMAP at the row (central "
                        "difference +-2 kPa of base_spark), as the environment's ECU responds; delta_D = fuel_model/fuel_meter - 1 and "
                        "e_D = TIT_model - TIT_EPA there; D1 = mean |delta_D| over the fired held-out rows (pooled). Version 4: "
                        "the inversion's pre-scan and bisection, the nearer bound for a row the model cannot reach, D1 also "
                        "reported without such rows, and form D's cam at the bisected MAP are conventions.statistic_details.d1 "
                        "(decision 57); a sentinel row's spark is conventions.spark_sentinel (version 4's reading of decision 54)"),
             population="held-out steady and Final rows with BMEP >= 2 bar and a meter value; a row whose torque the model cannot reach is listed and counted at the bound",
             R=R["D1"], unit="% of the measured flow", governs=DPART("P1"),
             basis=("the head start a preview buys is proportional to the flow and decays over tau, which shortens as the flow rises: "
                    f"|dln d/dln mdot| <= 1 (section 1.2b), so R = b/MEI = {100 * B_FRAC:.2f} %, rounded down. Torque and flow are one "
                    "part: D1 measures their in-use "
                    "combination (review finding 17); E1b and E2b are its descriptive components")),
        dict(id="L0", kind="level", quantity="the housing equivalent at the demanded torque",
             statistic=("per deciding held-out line: max over 0 <= f <= 1 of |f*e + f(1-f)*G*delta|, e and delta the line's mean e_D and "
                        f"delta_D (D1's inversion) over its hot lambda~1 rows with a meter, G = {G_K:.2f} K; the worst line; " + LINE_RULE),
             population=HOT + ", |lambda - lambda_ref| <= 0.02, with a meter value", R=R["L0"], unit="K of housing", governs=LEVEL,
             basis=("R1, on the sum the separate rows cannot see (version 1's E7a, now computed at the demanded torque on the rows "
                    "common to fuel and TIT, with f bounded as everywhere else)")),
        dict(id="L1", kind="d", part="P3", quantity="the spread of the housing level across operating points",
             statistic=("max over 0 <= f <= 1 of [the largest minus the smallest H_l(f) over the deciding held-out lines], "
                        "H_l(f) = f*e_l + f(1-f)*G*delta_l with L0's line means; u_stat of the spread from the two extreme lines"),
             population="L0's lines (at least 2 deciding lines)", R=R["L1"], unit="K of housing", governs=DPART("P3"),
             basis=(f"K3 sets the knee on the locked climb and d is scored on other roads, so a level that differs between operating "
                    f"points acts on d as a knee shift; the largest slope of d against a knee shift measured anywhere is "
                    f"{SLOPE['slope']:.4f} points per K ({SLOPE['set']}, knock term {'on' if SLOPE['knock'] else 'off'}, shift "
                    f"{SLOPE['shift_k']:+d} K; at +-10 K the largest is {SLOPE_10['slope']:.4f}); b/{SLOPE['slope']:.4f} = "
                    f"{math.floor(100 * B / SLOPE['slope']) / 100:.2f} K, rounded down. If the slope of the hand-written preview pair "
                    f"on decision 34's roads, "
                    f"measured before any held-out statistic, is larger, R = b/that slope (a tightening only). Version 4, decision 71: "
                    f"that slope is measured on the B58 plant, the plant of E8's tightening and of this basis; an EPA engine's own "
                    f"slope is reported and never used, since its coefficients would then move its R after its fit; the record of "
                    f"the tightenings names the plant, and the held-out run refuses one measured on any other")),
        dict(id="E8", kind="d", part="P4", quantity="the baseline ECU's strategy at high load: its lambda and spark at the held-out Final rows",
             statistic=("dl = mean signed (model ECU lambda - EPA lambda, cell-referenced) over those held-out High Load Final rows "
                        "that publish a lambda, and ds = mean signed (model ECU spark - EPA spark) over those that publish a spark "
                        "(version 4's reading of decision 54: conventions.lambda_missing, spark_sentinel), each subset of at least "
                        f"{E8_MIN_ROWS} rows, or E8 has no statistic and the engine is dropped (conventions.statistic_details."
                        "e8_subsets); the ECU evaluated at the row's speed and MAP with a 30 s dwell, "
                        "no knock retard and EPA's intake temperature; E8 = |P_lambda(dl)| + |P_spark(ds)|, P the measured relative "
                        "change of the hand-written head-start pair (current-grade minus reactive) under K3 for an ECU shift of that "
                        f"size (B58 locked climb, piecewise linear through {common.rel(common.ECU_DIR)}/k3_*.json, both damage readings, the "
                        "larger; the same shifts are re-run on the B58 on decision 34's roads before any held-out statistic, and at each "
                        "shift the larger response is used: a tightening only). Version 4: EPA's lambda in dl unsnapped, P's slope "
                        "at a zero shift and its extrapolation, and the tightening's sign are conventions.statistic_details.e8 "
                        "(decision 57)"),
             population=("held-out High Load Final rows: dl over those that publish a lambda, ds over those that publish a spark, "
                         f"each of at least {E8_MIN_ROWS} rows (version 4's reading of decision 54: conventions.lambda_missing, "
                         "spark_sentinel, statistic_details.e8_subsets)"),
             R=R["E8"], unit="% of the head-start pair", governs=DPART("P4"),
             basis=(f"measured, not assumed (mistake 24): under K3 a boosted-lambda shift of -0.02 / +0.02 moves the pair by "
                    f"{100 * interp(RESP_L, -0.02):+.1f} / {100 * interp(RESP_L, 0.02):+.1f} %, and a spark shift of -1.5 / +0.75 deg by "
                    f"{100 * interp(RESP_S, -1.5):+.1f} / {100 * interp(RESP_S, 0.75):+.1f} %; the shift worth b ({100 * B_FRAC:.1f} % of the "
                    f"pair) alone is lambda "
                    f"{W['lambda_rich']['shift']:+.4f} rich, {W['lambda_lean']['shift']:+.4f} lean, spark "
                    f"{W['spark_retard']['shift']:+.2f} deg{' (extrapolated)' if W['spark_retard']['extrapolated'] else ''} and "
                    f"{W['spark_advance']['shift']:+.2f} deg{' (extrapolated)' if W['spark_advance']['extrapolated'] else ''}")),
    ]

    CARS = [
        dict(id="C1", kind="identity", quantity="road load, level road, at EPA's test weight, 20 C, 98.21 kPa", engines=list(ENGS),
             statistic="largest |F_model/F_EPA - 1| at 15, 20, ..., 115 km/h", R=1e-6, unit="relative",
             basis="an identity: the car uses EPA's three-term target coefficients; above 115 km/h NOT COVERED (40 CFR 1066.305(a))"),
        dict(id="C2", kind="identity", quantity="gear ratios, final drive, CVT range, rolling radius (from EPA's N/V), mass", engines=list(ENGS),
             statistic="largest |model/source - 1|", R=1e-6, unit="relative", basis="an identity, as C1"),
        dict(id="C3a", kind="descriptive", quantity="CX-9 on D3: the Mazda model's fuel at the demanded torque, hot segments", engines=["mazda_25t"],
             statistic="mean signed relative error over the hot C3 segments", R=None, unit="%",
             basis=(f"descriptive since version 2: the driveline efficiency's span 0.86-0.98 alone gives u_input = "
                    f"{100 * U_C3_FUEL:.2f} % on the fuel (uniform: {100 * U_ETA:.2f} % on the torque demand, with the radius's "
                    f"{100 * U_RAD:.2f} %, x {FLOW_PER_PCT:.3f}), so 2u > E2a's {R['E2a']} % by construction"), blind=True),
        dict(id="C3b", kind="d", part="P5", quantity="CX-9 on D3: the Mazda model's fuel at the demanded torque", engines=["mazda_25t"],
             statistic="mean absolute relative error over the fired C3 segments", R=R["C3b"], unit="%", basis="as D1 (the flow at the demand); u_input carries the efficiency and radius spans", blind=True),
        dict(id="C3c", kind="descriptive", quantity="CX-9 on D3: the Mazda model's air against the car's MAF, hot segments", engines=["mazda_25t"],
             statistic="mean signed relative error over the hot C3 segments", R=None, unit="%", basis="descriptive, as C3a", blind=True),
        dict(id="C3d", kind="d", part="P5", quantity="CX-9 on D3: the Mazda model's air against the car's MAF (Eng_mass_air_flow_PCM)", engines=["mazda_25t"],
             statistic="mean absolute relative error over the fired C3 segments", R=R["C3d"], unit="%",
             basis="as D1; the only test of the air path itself for any EPA engine; the MAF's u_D includes its disagreement with fuel x AFR_st x lambda", blind=True),
        dict(id="C4", kind="descriptive", quantity="D3 figures already seen (gear agreement, rpm law, kickdown ratio, apparent driveline efficiency)", engines=["mazda_25t", "honda_l15b7"],
             statistic="as printed on 20 October", R=None, unit="-", basis="descriptive only: seen before this contract"),
        dict(id="C5", kind="rule", quantity="gear robustness on the scored climbs (a rule for decision 34's roads)", engines=list(ENGS) + ["b58"],
             statistic=("at every step of a scored climb outside its transitions, the ramps of its grade changes and its "
                        "changes of speed (version 4, decision 73; cars C5 steps), |demand / threshold - 1| at each gear the box "
                        "considers, the threshold the gearbox code applies (version 4, decision 70): for a stepped box "
                        "Vehicle.shift_ceiling_nm(rpm) at the held gear's engine speed and at each rejected higher gear's, the held "
                        "gear's own margin not gating while its next lower gear is barred by SHIFT_RPM_MAX, whose rpm margin is "
                        "reported (cars C5 threshold.rpm_bar); for the CVT decision 40's kickdown threshold at N_eco, "
                        "CvtVehicle.kickdown_threshold_nm(N_eco), against T_eco, with decision 40's diagnostic of N* reported "
                        "(cars C5 threshold.cvt_diagnostic); at a step at which the box takes no torque decision (the CVT's low-speed "
                        "branch, a stepped box's held lowest gear) the held gear's own margin does not gate and the rejected higher "
                        "gears' still do, reported (cars C5 threshold.no_decision); a scored climb runs from its ramp up to its ramp "
                        "down (cars C5 steps.range), at the time step its road is scored at (steps.dt); a gated step is one at "
                        "which at least one margin gates on the car (steps.gated_step); a scored climb with no gated step on a car "
                        "does not pass there (steps.no_gated_step), and one gated on fewer than half its steps on a car is flagged "
                        "thin there, never passed (steps.thin); C5's outcome for a scored climb on a car is one of three "
                        "exclusive cases, fails, thinly checked or passes (steps.outcome); the locked climb's transfer row "
                        "gates nothing (steps.transfer_row)"),
             R=R["E1a"], unit="% (the demand must sit MORE than max(R_E1a, |E1a| + 2u_val) from the threshold)",
             basis=("a torque error the validation accepts cannot change the gear a scored climb is driven in; the B58, which has no E1a, "
                    "uses R_E1a. Version 3's threshold, SHIFT_LOAD*T_wot (or the CVT law's lambda*T_wot), is not the one the box applies "
                    "(amendments F1, F2)"),
             steps=dict(
                 gated=("every step of a scored climb outside its transitions: a step is a transition step when the road's grade "
                        "there differs from its grade at the step before, or the road's speed there differs from its speed at the "
                        "step before or at the step after, since the demand at a step is computed from the road's speed, its change "
                        "to the next step and its grade (engine_env.py:1254-1257, SupervisoryTunerEnv.step); every grade change is a "
                        "ramp (training gate item 4, CLAUDE.md), GRADE_RAMP_S long on the locked climb (engine_env.py:1644). "
                        "'Differs' is exact inequality (!=) of the float64 values of the road's grade and speed arrays as the "
                        "roads step records them, the arrays the environment reads (c['grade'], c['v_mps']), with no tolerance "
                        "(version 4, decision 73, written after its fourth review)"),
                 dt=("a road's steps are its steps at the time step its scored climbs are scored at, which the roads step "
                     "records with the roads: the arrays the environment reads at that time step. The transition test and "
                     "every count of steps depend on it (engine_env.make_terrain and make_grade_climb take it), and C5 never "
                     "re-samples a road at another (version 4, decision 73, written after its fifth review)"),
                 gated_step=("a step is gated on a car when at least one margin gates there: a step outside the climb's "
                             "transitions at which the held gear's own margin gates or a rejected higher gear's does. A step "
                             "outside the transitions at which none does is not gated, and there are exactly three such steps: "
                             "the CVT's low-speed branch, which has no margin; a stepped box's lowest gear when it is also the "
                             "highest the road speed allows, so that no higher gear is rejected (threshold.no_decision); and a "
                             "stepped box's held gear whose next lower gear is barred by SHIFT_RPM_MAX (threshold.rpm_bar) when it "
                             "is also the highest the road speed allows, for the same reason. At every other step at least one "
                             "margin gates: on the CVT's economy, kickdown and power-limited branches T_eco's at N_eco, and on a "
                             "stepped box the held gear's or a rejected higher gear's. A step that is not gated is reported with "
                             "the car's gear or branch, and counts neither toward the gated-step minimum (no_gated_step) nor "
                             "toward the gated share (thin). These cases decide first, at any demand: a step whose demand is at "
                             "or below 0 is gated only where one of its margins gates, and that margin is then at least 1, which "
                             "passes (version 4, decision 73, written after its fifth review; the third case and the order of "
                             "the rules after its sixth)"),
                 share=("the share of each scored climb's steps that are transition steps, and on each car the share that are "
                        "gated, are reported with the climb, on every road kind: on a road whose speed changes at every step "
                        "of an acceleration or a coast, as the extremes kind's does (engine_env.extreme_speed_profile), most "
                        "of a climb can be transition steps, and C5 then gates a small part of it (version 4, decision 73, "
                        "written after its fourth review; the gated share after its fifth)"),
                 outcome=("C5's outcome for a scored climb on a car, at the margin it is checked at there (R_E1a at the "
                          "draw and at a redraw, the re-check margin after the held-out run: redraw.recheck), is exactly one "
                          "of three cases (version 4, decision 73, written after its seventh review): (1) it fails when some "
                          "gated margin, |demand / threshold - 1| at a gated step, is at or below the margin; (2) it is "
                          "thinly checked when no gated margin is at or below the margin and its gated steps on the car are "
                          "fewer than thin_below_share of its steps; (3) it passes when neither holds. The cases are "
                          "exclusive, and every climb is in one on every car (step 7 checks the case table). At the draw and "
                          "at a redraw a candidate in case (1) on any car fails a test of the first draw and is discarded, "
                          "as is one with no gated step on some car, which is in case (2) there (no_gated_step); one in case "
                          "(2) on a car with a gated step there is accepted and flagged thin there (thin). At the re-check "
                          "after the held-out run a scored climb in case (1) on any car is redrawn for every car "
                          "(redraw.redraw), and one in case (2) is not redrawn"),
                 thin=("a scored climb whose gated steps on a car are fewer than half its steps (thin_below_share) is flagged "
                       "thin on that car, whichever case of outcome it is in, and is never reported as passed there; the "
                       "flag is known at the draw, from the road, the car and its frozen plant, and is reported with the "
                       "roads, with the climb's gated share. A thin climb that fails at a gated step fails C5 there (outcome "
                       "case (1)): it is discarded at the draw and redrawn at its re-check, and a slot that keeps it at the "
                       "cap is flagged gear-sensitive and thin on that car (redraw.at_cap). A thin climb with no failing "
                       "gated step is thinly checked there (case (2)): it is reported so, scored and not redrawn, and it "
                       "neither passes nor fails C5, so it does not make its car gear-sensitive (redraw.no_passing_car). The "
                       "first draw and a redraw both accept a candidate in case (2) on a car, if it has a gated step there "
                       "(no_gated_step), and flag it thin; each car's results are reported with and without its thin climbs "
                       "(version 4, decision 73, written after its fifth review, which found that on a road whose speed "
                       "changes at every step C5 could gate almost none of a climb and pass it on one step; the cases after "
                       "its seventh). The share, one half (thin_below_share), is DESIGN, chosen from no data (labelled after "
                       "the sixth review): no road has been drawn, so no climb's gated share has been seen; it is the least "
                       "share at which a climb that C5 reports as passed was gated on at least as many of its steps as it "
                       "left ungated. It moves what is reported as passed and nothing else: a thin climb is still scored and "
                       "fails C5 as any climb does, and every car's results are reported with and without such climbs"),
                 thin_below_share=C5_THIN_SHARE,
                 range=("a scored climb's steps run from the first step of its ramp up to the last step of its ramp down, and the "
                        "roads step records each climb slot's first and last step with the roads, before any held-out statistic; the "
                        "road before and after a scored climb is not C5's. The neighbours the transition test compares are the "
                        "road's steps, inside the climb or not, so a climb's first and last steps are transition steps, its grade "
                        "ramping there, unless the climb starts at the road's first step or ends at its last. The road's first step has no step before it and its last no step after: a missing "
                        "neighbour is taken as the step itself, as the environment takes the step after the last "
                        "(engine_env.py:1255), where the speed's change to the next step is zero (version 4, decision 73, written "
                        "after its third review)"),
                 ramps=("the transition steps' margins and their gear sequence (the CVT's branch) are reported beside the result, "
                        "not gated: in a transition the box changes gear by design, and the margin at the steps around the change "
                        "depends on where the steps fall and can be arbitrarily small; the gear the climb is driven in is checked "
                        "at every step outside its transitions"),
                 steady_acceleration=("the reason not to gate a transition holds only near the steps at which the gear, or the "
                                      "CVT's branch, actually changes: between them a steady acceleration or coast holds its "
                                      "gear, and a torque error the validation accepts could still hand it back or take the "
                                      "next one there, which C5 does not check; the thin flag reports the climbs on which that "
                                      "matters. The other readings would gate those steps: a transition only where the grade or "
                                      "the acceleration changes, with a fixed neighbourhood (version 4's fourth review), or only "
                                      "within a fixed neighbourhood of a step at which a car's gear or the CVT's branch "
                                      "changes, and of the grade ramps (its fifth). Neither is taken in version 4, because "
                                      "neither has a width that follows from the reason for not gating a transition: the steps "
                                      "around a gear change made by design whose margin a torque error within the margin can "
                                      "cross are those over which the demand moves by about the margin against the threshold, "
                                      "so how many they are is set by how fast the demand crosses the threshold there, few on a "
                                      "ramp and many on a slow acceleration; the speed test's width of one step comes from the "
                                      "demand's own definition, which reads the speed's change to the next step, and not from "
                                      "that. A one-step neighbourhood would therefore gate, on a slow acceleration, steps at which "
                                      "a torque error within the margin only moves the timing of a gear change the box makes by "
                                      "design, and fail every such climb, which is what not gating a transition prevents; a width "
                                      "derived from the margin and the demand's rate would be a new rule no review has examined. "
                                      "Version 4's fifth correction also gave as a reason that the second reading makes the "
                                      "transition steps each car's; its sixth review found that no objection, since the gated "
                                      "steps are already each car's and known at the draw, and it is withdrawn. Decision 73's row "
                                      "records both readings as options, with this reason"),
                 no_gated_step=("a scored climb must have at least one gated step (gated_step) on every car: one with none on a "
                                "car has not been checked by C5 there and does not pass it (outcome case (2)); its gated steps are known at the "
                                "draw, from the road, the car and its frozen plant, so the roads step discards such a climb at "
                                "the draw and at a redraw, as a climb that fails a test of the first draw (redraw.redraw), and "
                                "reports it"),
                 transfer_row=("the locked climb, decision 34's declared transfer row, is not one of decision 34's roads: it is "
                               "never drawn or redrawn, and C5 gates nothing on it; its margins, computed as on a scored climb, "
                               "are reported as decision 44 asks, beside the gear or ratio, the rpm and the margins to the "
                               "kickdown and rpm bars (version 4's reading of decisions 34 and 44, written after its fifth "
                               "review); the locked-climb cases of threshold (amendments F2 and F3) illustrate the rule and "
                               "are not scored climbs"),
                 version_3=("'on every scored climb', which names the climbs and not their steps; docs/build_step_2/PLAN.md "
                            "section 7.4 reads 'every scored-climb step'; the changes of speed and the gated-step minimum were "
                            "added to decision 73 after version 4's second review, a scored climb's extent (range) after "
                            "its third, the exact comparison and the reported share after its fourth, and the time step, the "
                            "gated step, the thin flag and the transfer row after its fifth, before any road was drawn"),
                 decision=f"73 ({DECISIONS_DOC} section H, {RAISED_V4})"),
             threshold=dict(
                 stepped=("Vehicle.gear_for (engine_env.py:598-633) starts at the highest gear the road speed allows and hands one back "
                          "while the demand f*r/(ratio*eta) exceeds Vehicle.shift_ceiling_nm(rpm) = min(SHIFT_LOAD*PEAK_TORQUE_NM, the "
                          "deliverable-torque table at rpm) (:545-548), rpm the engine speed gear_for computes for that gear: the held "
                          "gear's demand must sit more than the margin BELOW its ceiling, unless its next lower gear is barred "
                          "(rpm_bar), and each rejected higher gear's more than the margin ABOVE its own"),
                 rpm_bar=("a downshift barred by SHIFT_RPM_MAX cannot be caused by a torque error. The bar applies whenever the next "
                          "lower gear's engine speed, as gear_for computes it, exceeds SHIFT_RPM_MAX (engine_env.py:630-631), whether "
                          "or not the held gear's demand exceeds its ceiling: gear_for keeps the held gear either way, by its "
                          "ceiling test or by the bar, so no torque error can hand it back. The held gear's own margin then does not "
                          "gate; it is reported beside the bar's rpm margin, the lower gear's engine speed minus SHIFT_RPM_MAX, in rpm "
                          "and as a fraction of SHIFT_RPM_MAX (positive while the bar holds). The rejected higher gears are still "
                          "checked, as for a held lowest gear (no_decision). A script must not follow gear_for's control flow here: "
                          "there, a held gear whose demand sits under its ceiling never reaches the bar's test, and would be gated "
                          "as an ordinary hold; docs/build_step_2/AMENDMENTS.md F3's CX-9, whose 3rd gear is barred on its locked "
                          "climb as F3 computes it, is such a case"),
                 cvt=("decision 40's stateless kickdown (CvtVehicle.ratio_for, engine_env.py:813-852): its one discrete decision is "
                      "at N_eco, so the threshold is kickdown_load*T_del(N_eco), CvtVehicle.kickdown_threshold_nm "
                      "(engine_env.py:803-807), against T_eco: on the economy branch T_eco must sit more than the margin below it, "
                      "on the kickdown and power-limited branches more than the margin above it"),
                 cvt_diagnostic=("decision 40's diagnostic, reported and not gated: on the kickdown branch N* is the lowest engine "
                                 "speed of the window whose demand is at most target_load*T_del(N), and on the power-limited branch, "
                                 "where none is, the speed of most deliverable power (engine_env.py:836-852); if that feasible set, "
                                 "{N in the window: P_e/(omega*N) <= target_load*T_del(N)}, is not one interval, a torque error "
                                 "inside the margin can move N* into another interval, a discrete change of engine speed the margin "
                                 "at N_eco does not see, and so can a switch between the two branches; at every gated step on either "
                                 "branch the roads step, which applies C5, reports whether, with the demand and T_del each scaled by "
                                 "(1 +- the margin), the feasible set stays one interval and N* stays on its branch: at the draw, at "
                                 "R_E1a, and again at the re-check after the held-out run, at the re-check margin (redraw), on every "
                                 "redrawn climb too (version 4's fourth review placed it there; docs/build_step_2/AMENDMENTS.md "
                                 "section 3, decision 40: 'Report as a diagnostic whether N* stays in one connected feasible "
                                 "interval under demand and T_del x (1 +- m)'); C5 gates the law's one discrete decision, at N_eco, "
                                 "and that N* moves continuously everywhere else is an assumption this diagnostic reports"),
                 no_decision=("at a step at which the box takes no torque decision the held gear's own margin is not gated, as at "
                              "a barred downshift, and the step is reported with the CVT's branch or the held gear and the road "
                              "speed: the CVT's low-speed branch, where ratio_for returns no N_eco (engine_env.py:820-821), which "
                              "has no other margin, so the step passes; and a stepped box's held gear when it is the lowest, since "
                              "gear_for compares the demand with a ceiling only while g > 0 (engine_env.py:624), whose rejected "
                              "higher gears' margins are still gated. A demand at or below 0 (f <= 0: the CVT's economy hold of "
                              "engine_env.py:833, or a stepped box on a descent) has |demand / threshold - 1| >= 1 against a positive "
                              "threshold, and passes unless the margin reaches 1, wherever a margin is taken: rpm_bar and the cases "
                              "above say first whether one is (version 4, written after its sixth review). At f <= 0 the CVT's "
                              "low-speed branch, which ratio_for returns before its test of f (engine_env.py:820-821), still has no "
                              "margin; a stepped box holds the highest gear the road speed allows, since the demand is under every "
                              "ceiling, so it rejects no higher gear, and the held gear's own margin gates only when that gear is "
                              "not its lowest and its next lower gear is not barred. Which of these steps are gated: steps.gated_step"),
                 decision=f"70 ({DECISIONS_DOC} section H, adopted under Ghassan's delegation of 21 October 2026)"),
             redraw=dict(
                 slot=("a climb slot is shared by the four cars (version 4, decision 75): decision 34 draws one set of test roads, "
                       "whose preview ceiling is at least 2 MEI on every engine, so each slot of it is one climb for every car, "
                       "the Supra's included"),
                 draw=("decision 64: the roads are drawn with the margin at R_E1a on every car, before any held-out statistic; "
                       "the roads' own seed, which fixes the redraw streams (stream), is committed with them by the roads step, "
                       "and the cap and the discard bound are this contract's numbers (cap, discards; decision 76)"),
                 stream=("each climb slot has its own stream, the sequence of candidate climbs the roads step's first-draw code "
                         "draws, one after another, from the generator numpy.random.default_rng([roads_seed, stream_tag, k]): "
                         "roads_seed is the non-negative integer the roads step draws the roads from and commits with them, "
                         "before any held-out statistic; stream_tag is a label that separates these streams from any other "
                         "drawn from that seed, as engine_env.TerrainTrainingEnv separates its road stream (_TERRAIN_STREAM), "
                         "and the roads step draws no other stream under it; and k is the slot's index, from 0, in the order "
                         "the slots are redrawn in (redraw). A slot's candidates therefore do not depend on how many another "
                         "slot used, and the streams are fixed by the roads' own seed and nothing else (decision 76; the "
                         "derivation fixed after version 4's sixth review, which found it left to the roads step, after the "
                         "first fit, with the in-sample E1a known). The freedom that remains is the roads' own seed, which "
                         "also picks the first draw: the roads step sets it after the freeze, as version 3 and decision 34 let it"),
                 stream_tag=REDRAW_STREAM_TAG,
                 recheck=("after the held-out run every scored climb is re-checked on every car, each EPA engine's at its own "
                          "max(R_E1a, |E1a| + 2u_val), |E1a| and u_val those of E1a's worst deciding line "
                          "(conventions.statistic_details.lines), and the B58's at R_E1a; each deciding line's |E_l| + 2u_val,l "
                          "is reported beside the margin, since a line with a smaller |E_l| and a larger u_val can leave more "
                          "than the worst line's |E1a| + 2u_val, which the margin, as decision 64 reads ('of the worst line', "
                          "docs/build_step_2/PLAN.md decision 64), does not see"),
                 redraw=("a scored climb that fails C5 (steps.outcome case (1)) on any car is redrawn from its slot's stream "
                         "for every car (decision 75). A "
                         "redraw is the next climb of the slot's stream that passes every test "
                         "the roads step applies to a climb of its first draw, with the same code: decision 34's preview "
                         "ceiling of at least 2 MEI on every engine, C5 at R_E1a with at least one gated step on every car, a test "
                         "a candidate passes when, on every car, it is in steps.outcome case (2) or (3) and has a gated step "
                         "(one in case (2) on a car is accepted and flagged thin there, as at the first draw), and "
                         "the roads step's own checks. Each test is applied as the first draw applies it: a test of a climb to "
                         "the candidate, and a test of a road or of the road set to that road or set with the candidate in the "
                         "slot and every other slot as it then stands; decision 34's ceiling is of the second kind, a property "
                         "of the roads ('chosen so that the preview ceiling ... is at least twice the MEI on every engine'), "
                         "not of one climb. A candidate that fails one is discarded, as at the first draw, is not a redraw and "
                         "is not counted against the cap, and the number discarded is reported. The slots are redrawn in "
                         "their order on the roads, the roads in the order the roads step records them and a road's slots by "
                         "their first step, each slot's redraws ending before the next slot's begin, and every car's "
                         "C5 is then checked again on the new climb at its re-check margin (version 4, decisions 75 and 76; "
                         "the tests' level and the order written after its fifth review, the order's definition after its "
                         "sixth)"),
                 extent=("a candidate fills its slot's recorded extent (version 4, decision 75, written after its sixth "
                         "review): the first draw's code draws it as a climb of the slot's length, from the slot's recorded "
                         "first step to its last (steps.range), joined to the road at both ends as a climb of the first draw "
                         "is; the road outside the slot, the slot's first and last steps and every other slot's record stay "
                         "as recorded, so a redraw moves the transition and gated-step counts of that slot alone, and the "
                         "road set decision 34's ceiling is computed on only inside it; a candidate that code cannot give at "
                         "the slot's length is discarded, as one that fails a test of the first draw"),
                 cap=(f"at most {REDRAW_CAP} redraws per climb slot, counted over all cars: one for each redraw, whichever car's "
                      "failure caused it (decisions 75 and 76); a number of this contract, fixed before any fit and from no "
                      "data (DESIGN), which the roads step commits with the roads as written here: three redraws bound how "
                      "far one engine's held-out E1a can move a slot, and leave a slot whose candidates each fail with "
                      "probability p without a passing climb with probability p**3, one in eight at p = 1/2"),
                 cap_redraws=REDRAW_CAP,
                 discards=(f"at most {REDRAW_DISCARDS} candidates discarded per slot, counted over its redraws: when the last of "
                           "them is discarded the slot stops redrawing and keeps its last climb for every car, as a slot at the "
                           "cap does (at_cap), and the stop is reported (decision 76). A slot's stream has no end and discarded "
                           "candidates are not counted against the cap, so without this bound a slot whose candidates kept "
                           "failing the first draw's tests would never be settled; the bound only ends such a stream"),
                 discards_max=REDRAW_DISCARDS,
                 at_cap=("a slot whose redraws reach the cap, or stop at the discard bound, keeps the last climb accepted for "
                         "it, its original or its last redraw and never a discarded candidate (named after version 4's sixth "
                         "review), for every car; on each car on "
                         "which that climb fails C5 (steps.outcome case (1)) the slot is scored, flagged gear-sensitive with "
                         "its margins listed, and flagged thin too where the climb is thin on that car (steps.thin), and "
                         "that car's results are reported with and without its flagged slots (decision 74, read with 75): "
                         "dropping the slot would shorten that car's scored set on the strength of a held-out statistic (E1a), "
                         "which decision 64 avoids for a whole car"),
                 no_passing_car=("a car with no passing climb is not dropped: C5 is a rule, not a gate; its scored climbs' "
                                 "margins are listed, each slot keeping its last accepted climb as every slot at the cap does "
                                 "(decisions 74 and 75), and it is reported by what its climbs are on it: gear-sensitive "
                                 "(decision 64) when a slot is flagged gear-sensitive on it, thinly checked when a climb is "
                                 "flagged thin on it (steps.thin), and both when it has both, as it has when a slot at the "
                                 "cap keeps a thin climb that fails there. A thin climb with no failing gated step "
                                 "(steps.outcome case (2)) neither passes nor fails C5: it is not a passing climb, and it does "
                                 "not make its car gear-sensitive; a thin climb that fails at a gated step (case (1)) fails C5 "
                                 "there, as any climb does (version 4's reading of decisions 64 and 73, written after its sixth "
                                 "review; the cases after its seventh)"),
                 disclosed=("a redraw moves every car's scored set on the strength of one engine's held-out E1a, the price of "
                            "decision 34's one road set (decision 75): the redraws are reported per slot, with the car and the "
                            "margin that caused each; and L1's and E8's tightenings were measured on the roads as first "
                            "drawn, which is disclosed"),
                 rule_0=("the streams are fixed by the roads' own seed, which the roads step sets and commits with the roads "
                         "after the freeze and before any held-out statistic, as decision 64 places it, through the derivation "
                         "written here (stream); that derivation, the cap and the discard bound are fixed here, before any fit "
                         "(decision 76); none of them changes after the held-out run. "
                         "Rule 0 freezes this rule and these numbers, as it lets the roads and the L1 and E8 tightenings, which "
                         "also come after the first fit, be set by the step this contract names. The one change after the "
                         "held-out run is the redraw itself: a climb that fails at its re-check margin is replaced from its "
                         "slot's committed stream, within the cap and the discard bound, which moves the scored climbs and nothing "
                         "else; the tightenings stay as measured on the roads as first drawn (disclosed)"),
                 decision=(f"64 ({DECISIONS_DOC} section H, adopted under Ghassan's delegation of 21 October 2026), 74, 75 and "
                           f"76 ({RAISED_V4})"))),
    ]
    SEG = ("C3 segments: at least 3 s; engine speed within +-25 rpm; the PCM MAP channel refreshed at least twice; the torque converter "
           "locked throughout (Eng_speed_CAN within 1 % of Trans_turbine_shaft_speed_TCM); the A/C compressor off throughout "
           "(HVAC_ACComp_cycling_switch_PCM); one gear (Trans_gear_actual_CAN); coolant at or above the map's lowest (83.8 C); padding "
           "rows dropped; hot = the car's PCM MAP (Eng_ManifoldAir_pressure_sensor_PCM) at or above the Mazda's hot MAP floor; fired = "
           "the chain's demanded torque at or above 2 bar BMEP; a row decides with >= 3 segments and 2*u_stat <= R")

    TABLE = [
        dict(id="S1a", kind="table", quantity="the table's lever effects on EGT: lambda -0.05, MAP -10 kPa, spark -0.75 deg",
             statistic="per lever: sum|dEGT_table - dEGT_exact| / sum|dEGT_exact| over the S1 points", R=R["S1a"], unit="%", basis="as E4b"),
        dict(id="S1b", kind="table", quantity="torque, table against exact cycle", statistic="95th percentile of |T_table - T_exact| / max(|T_exact|, 40 Nm)",
             R=R["S1b"], unit="%", basis=f"a SCREEN: the uniform-bias consequence of section 1.4 ({100 * B_FRAC:.2f} / {FLOW_PER_PCT:.3f}); a table's local errors do not follow it, and S2 is the closed-loop check"),
        dict(id="S1c", kind="table", quantity="air and fuel flow, table against exact cycle", statistic="95th percentile of |relative error|; 1e-6 (an identity) if computed in closed form",
             R=R["S1c"], unit="%", basis="a SCREEN, as D1's uniform consequence"),
        dict(id="S1d", kind="descriptive", quantity="EGT level, knock integral, knock flag", statistic="MAE, p95, max; flag agreement", R=None, unit="K; relative; fraction", basis="descriptive"),
        dict(id="S2a", kind="table", quantity="fixed policies on PRACTICE episodes of decision 34's roads, scored on table and exact cycle",
             statistic=("per preregistered horizon H: |d_table - d_exact| for the hand-written preview pair (the predictive policy reading "
                        "the largest grade within the next H seconds, minus current-grade), both damage readings; five random pairs "
                        "(an action drawn uniformly from the action box, redrawn every 30 s, seeds 0-9) reported, not gated"),
             R=R["S2a"], unit="points of cut", basis=f"b = MEI/{n_shares}"),
        dict(id="S2b", kind="table", quantity="pilot agents TRAINED ON THE TABLE (after the preregistration), scored on table and exact cycle on practice episodes",
             statistic=("per preregistered horizon H: the mean over pairs of (g_sighted,H - g_blinded), g = cut_table - cut_exact, and the "
                        "median over agents of g, both damage readings; 4 to 8 pilot seeds per engine, outside the experiment's list"),
             R=R["S2b"], unit="points of cut",
             basis=f"b = MEI/{n_shares}; it measures exploitation of the table, not the training backend's effect on the exact-cycle d (declared)"),
    ]

    REFIT_V4 = "every E row's change, and how far the model in use moves, with no exclusion label (a refit row; version 4, decision 59)"
    E6 = [
        dict(n=1, constant="the lambda convention", band="as published instead of cell-referenced: the offset lambda_ref - 1 (Mazda 0.000, Honda -0.010, Ford Cell 9 -0.020, HD1 0.000), the snap kept (row 12 moves the snap)", refit=True,
             must_show=f"{REFIT_V4}: the in-use hot TIT at lambda 1, the air and tau"),
        dict(n=2, constant="AFR_st (calibration air and plant fuel together)", band=f"the table's own fuel, {FUEL['mazda_25t']['afr_st']}-{FUEL['honda_l15b7']['afr_st']} (the convention) -> 14.7 (the B58's engines.Fuel.afr_st, engine_specs/b58.toml:202)", refit=True,
             must_show=(f"the air {100 * E6_AFR['air_rel']:+.2f} %, the exhaust flow {100 * E6_AFR['exhaust_flow_rel']:+.2f} %, tau "
                        f"{100 * E6_AFR['tau_rel']:+.2f} % (B58 f), the housing level {E6_AFR['housing_b58_k']:+.2f} K (B58 f) or at most "
                        f"{E6_AFR['housing_bound_k']:+.2f} K (f bounded); E2, D1 and L0 must NOT move (excluded for AFR_st by construction): "
                        "each moves by less than its u_val, and a miss is reported as a finding, not a stop (version 4, decision 59)")),
        dict(n=3, constant=("LHV, in the cycle's heat release (plant.py:233, plant.run_cycle) AND the thermal network's fuel heat "
                            "(thermal.py:255, ThermalNetwork._substep) together, through engines.with_fuel"),
             band="the table's own fuel, 42.898-42.908 MJ/kg (the convention) -> 44.0", refit=True,
             must_show=f"{REFIT_V4}: the in-use heat release per gram of fuel; the coolant and oil heat"),
        dict(n=4, constant="c_turb, ua_gas_turb, ua_turb_amb", band="x0.75 and x1.333 each, PROPOSED BY THIS CONTRACT (X1 drew only the heat capacity on that range, PREREGISTRATION_X1.md:119)", refit=False,
             must_show="tau moves by construction; no E-row can see them: excluded by construction; report tau, the 850 C baseline peak and decision 34's ceiling at each end, flagged if the ceiling falls below 2 MEI"),
        dict(n=5, constant="the back-pressure law", band=("+- its fit's standard uncertainty (reported); the visibility probe is sized by consequence: the change worth R1 on the engine's own in-use housing equivalent at its locked-climb cell (level rows) or worth b on d (d rows), else +-10 %; "
                   "every d row's probe is +-10 % (version 4, decision 59: d needs agents, and no EPA engine has one when the validation runs; order_of_work)"), refit=False, must_show="E1a, E3a and L0 must move under the probe"),
        dict(n=6, constant="UA_PORT", band="+- its fit's standard uncertainty (reported); the visibility probe is sized by consequence, as row 5", refit=False,
             must_show="E3a, E3b, E4a and L0 must move under the probe"),
        dict(n=7, constant="the knock scale (KI = 1 assumed at the High Load Final spark)", band="KI 0.90 and 1.10 (decision 21's +-0.10 KI)", refit=True,
             must_show=f"no E-row can see it; {REFIT_V4}: the knock term's share of the baseline's damage, and d both ways"),
        dict(n=8, constant="the crank-angle step", band="0.25 -> 0.125 deg", refit=False, must_show="u_num"),
        dict(n=9, constant=("the other ASSUMED cycle constants (conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, any burn constant "
                            "not fitted, the flame terms flame_lam, flame_width and flame_floor among them: engines.CycleCal, "
                            "engine_specs/b58.toml:67-69 on the B58) and, from version 4 (decision 59), the rich slope ce_rich_slope"),
             band=("in this order (version 4, decision 59): the bracket EPA's calculated valve channels give where one exists, and why "
                   "each bracket that cannot be computed cannot; else the probe sized by consequence (the change worth R1, or for a d row "
                   "+-10 %, as row 5); else +-10 % (+-10 crank degrees for IVC and EVO). ce_rich_slope: a probe under forms A and B, where it is the shared "
                   f"{PV['shared_rich_slope']['value']:g}; under C, where it is fitted, +- its fit's standard uncertainty (reported) and "
                   "the visibility probe, as rows 5 and 6; under every form exclusion is judged under the probe only: the change "
                   "worth R1 for E4a, +-10 % for E4b and every other d row (version 4's reading of docs/build_step_2/AMENDMENTS.md "
                   "E3, 'a probe under A and B, its sigma under C': a sigma alone would size the probe by the fit, which the "
                   "probe's rule forbids, and would leave E4a and E4b without a probe for the slope)"), refit=False,
             must_show="the rows the calibration says each one sets must move; report the error worth R1 and worth b"),
        dict(n=10, constant="the driveline efficiency, 0.92", band="0.86-0.98 (the CX-9's apparent efficiency on D3, seen); the Accord's 0.78 UNVERIFIED", refit=False,
             must_show=f"C3 moves; an efficiency error is a torque bias of the same fraction: worth R1 at {R['E1a']} %, worth b at {R['S1b']} %"),
        dict(n=11, constant="the charge temperature (E rows are fed EPA's measured value)", band="+-6.3 K (the B58's input uncertainty, DRIVE_C_RULE_NUMBERS.txt:56)", refit=False,
             must_show="report the hot TIT and the test roads' hand-written cuts"),
        dict(n=12, constant="the lambda snap (rows within 0.02 of lambda_ref run at 1.00)", band="every row at lambda_meas - (lambda_ref - 1), no snap", refit=False,
             must_show=("E3a, E5, D1 and L0 both ways; each labelled by the worse of the two (review finding 11), in the order "
                        "off > untested > limited > validated (version 4, decision 59); D1, the one d row among them, enters its "
                        "part's band with the larger kappa of its two readings, each computed as on_failure.d.band computes it for "
                        "its own label (version 4's reading of decision 59, which fixed the order of the labels and not the band; "
                        "written after its fourth review); E8 is unsnapped already, and its snapped reading is "
                        "reported (version 4, decision 57; conventions.statistic_details.e8)")),
        dict(n=13, constant="the enrichment timing within a hold (EPA publishes two windows only)", band="the ECU's dwell gate at 0 s and at 30 s, EPA's hold length", refit=False,
             must_show="a PREREGISTERED SENSITIVITY ROW of d for every engine (review finding 29)"),
    ]

    FAIL = {
        "label_domain": ("every E and C row is labelled on its own comparison's domain (the EPA held-out rows, or the D3 segments), in "
                         "decision 4's order with 'not covered' read on that domain: excluded, not covered, off, untested, validated, "
                         "limited. Coverage of the SCORED context (decision 34's roads at 42 C, holds longer than EPA's 30 s) is a separate "
                         "per-engine flag, reported beside every result and in the preregistration, never instead of a label"),
        "level": {"validated": "the engine's 850 C row may quote this accuracy", "limited": "850 C row labelled limited",
                  "untested": "850 C row labelled untested", "off": "850 C row labelled off", "always": "the engine is kept; absolute housing statements are NOT COVERED whatever the row reads (review finding 12)"},
        "d": {"validated": "the part's band is b", "limited": "the engine enters; the part's band is ((|E| + 2u_val)/R)*b",
              "untested": "the engine enters; the part's band is ((|E| + 2u_val)/R)*b with the measured E and u_val; a row with no statistic (no deciding line, or excluded for every constant it claims to test) DROPS the engine",
              "off": "the engine is dropped (amends decision 24)",
              "untested_why": ("an untested row WITH a statistic enters with its band, at least b*(1 + |E|/R), because E8 is expected "
                               "untested on every engine, the B58 included, and a drop would end the test before it began; decision 36 "
                               f"({SG}, adopted 21 October 2026): the verdict inside the band reads MODEL-LIMITED"),
              "band": ("kappa = 1 when a part's rows read validated, else (|E| + 2u_val)/R, the larger of its rows'; the multiplicative "
                       "parts P1 (D1), P2 (E4b), P4 (E8) and P5 (C3b, C3d) contribute kappa*b*(d/MEI)*phi, phi = max(1, |1 + ln(1 - c)|) "
                       "at both arms' realised median cuts; P3 (L1) contributes kappa*b; P6 contributes b when the engine trains on its "
                       "validated table and nothing on the exact cycle; the engine's model band is the RSS over its parts, the linear sum "
                       "beside it; a verdict that changes when d moves within the band is reported MODEL-LIMITED; the cross-plant "
                       "difference d_i - d_j carries sqrt(band_i^2 + band_j^2)")},
        "table": {"validated": "the engine trains on its table", "other": "the pre-declared remedies, then the exact cycle if the schedule test passes, else the engine is dropped (Ford, then Honda, the Mazda last; the B58 is never dropped and trains on the exact cycle)",
                  "remedies": "in order, each at most once, every attempt reported: (1) a knock-flag guard band (the exact cycle evaluates any step whose table knock integral lies within S1d's p95 relative error of the ECU's threshold); (2) the baseline car on the exact cycle; (3) a denser grid (measured on the B58 not to shrink the closed-loop differences)",
                  "schedule_test": "an engine trains on the exact cycle only if the seeds per arm that decision 30's window affords at the training device's measured many-run exact-cycle rate, with three arms of 450 000 steps, are at least decision 30's target of 20"},
        "identity": "a coding defect: fix and re-run (not a fit)",
        "rule": ("a climb slot is shared by the four cars (version 4, decision 75); a climb that fails C5 on any car is redrawn "
                 "for every car from its slot's stream, fixed by the roads' own seed, each redraw passing every test of a first draw "
                 f"and checked again on every car, at most {REDRAW_CAP} redraws per slot, counted over all cars, and at most "
                 f"{REDRAW_DISCARDS} discarded candidates per slot (decisions 64, 75 and 76; cars C5 redraw); a scored climb "
                 "with no gated step on a car does not pass C5 there, and the roads step discards it as a climb that fails a "
                 "test of the first draw, and one gated on fewer than half its steps on a car is flagged thin there and "
                 "never reported as passed, thinly checked when no gated margin fails and failing C5 when one does (C5's "
                 "outcome on a car is one of three exclusive cases, fails, thinly checked or passes: cars C5 "
                 "steps.outcome), that car's results reported with and without such climbs "
                 "(version 4, decision 73); a slot whose redraws reach the cap, or stop at the discard bound, keeps the last "
                 "climb accepted for it for every car, scored, and flagged gear-sensitive with its "
                 "margins listed on each car on which it fails, and thin too where it is thin there, and each such car's "
                 "results are reported with and without its "
                 "flagged slots (version 4, decision 74, read with 75); a car with no passing climb is never dropped, its "
                 "scored climbs' margins listed, each slot keeping its last accepted climb, and is reported as gear-sensitive "
                 "when a slot is flagged on it and thinly checked when a climb is thin on it, a thin climb with no failing "
                 "gated step neither passing nor failing (decision 64, read with 73); the locked climb's transfer row is never redrawn and gates nothing, its margins reported "
                 "(decisions 34 and 44, as version 4 reads them)"),
        "descriptive": "reported, never gating",
        "perturbation": ("labels (excluded for a constant) and preregistered sensitivity rows; never a drop. Version 4 (decision 59): "
                         "the refit rows 1, 3 and 7 report how far the model in use moves and label no exclusion; a row is excluded "
                         "for every constant it claims to test only by the counting rule of tests_lists. The refit rows' "
                         "calibrations (rows 1, 2, 3 and 7) run before the held-out run, at the frozen form, and their held-out "
                         "statistics are computed in that same single run (docs/build_step_2/PLAN.md section 6.4 and decision 59), "
                         "so no refit follows a held-out statistic (refit)"),
        "refit": ("no refit after any held-out statistic of an engine has been computed; a coding defect, a disagreement with a "
                  "specification committed before the comparison ran, may be fixed and the comparison re-run: both results reported, "
                  "the second limited at best"),
        "freeze": "no R, split, population, statistic, convention or form rule changes after any fit runs (rule 0); a change after that is a new contract, disclosed, every result under both",
    }

    # ============================================================== 7b. decision 59's Tests lists (version 4)
    # The lists of docs/build_step_2/PLAN.md decision 59, with the E6 row that perturbs each member
    # (None: no E6 row does), counted by amendment E4's rule. Members fitted by the calibration and moved
    # by no E6 row (VE, the burn and delay constants, FMEP) are "not perturbed": the refit rows 1 and 2 move
    # VE through the refit, and neither labels an exclusion for it.
    BURN, FMEP_, BP, VE_ = "the burn and delay constants (fitted)", "FMEP (fitted)", "the back-pressure law", "VE (fitted)"
    UAP, RICH, ETA_ = "UA_PORT", "the rich slope ce_rich_slope", "the driveline efficiency"
    FLAME = "the flame terms flame_lam, flame_width and flame_floor (ASSUMED)"
    PERTURBED_BY = {BURN: None, FMEP_: None, BP: 5, VE_: None, UAP: 6, RICH: 9, FLAME: 9, ETA_: 10}
    LISTS = {"E1a": [BURN, FMEP_, BP], "E2a": [VE_], "E3a": [UAP, BURN, BP], "E4a": [UAP, RICH], "E4b": [RICH, FLAME],
             "D1": [VE_, BURN, FMEP_, BP], "L0": [UAP, BP, VE_, BURN], "L1": [UAP, BP, VE_, BURN], "E8": [],
             "C3b": [VE_, ETA_], "C3d": [VE_, ETA_]}
    TESTS = {
        "decision": (f"59 ({DECISIONS_DOC} section H, adopted under Ghassan's delegation of 21 October 2026): the lists "
                     "of docs/build_step_2/PLAN.md decision 59 (E1 for E1a, E2 for E2a, E3 for E3a, L0/L1 for both), counted by "
                     "docs/build_step_2/AMENDMENTS.md E4's rule"),
        "rule": ("a gating row is excluded for every constant it claims to test (no statistic: on_failure.d) only if every member of "
                 "its list is perturbed by an E6 row and the row is excluded for each; a member no E6 row perturbs counts as not "
                 "excluded, because the held-out statistic tests it directly; a refit row (1, 3, 7) labels no exclusion; E8 has no "
                 "list and is never excluded"),
        "lists": {row: [dict(member=m, perturbed_by_E6_row=PERTURBED_BY[m]) for m in ms] for row, ms in LISTS.items()},
    }

    # ============================================================== 8. engines
    eng_out = {}
    for eng in ENGS:
        s = split[eng]
        eng_out[eng] = dict(
            lines=s["lines"], eligible=s["eligible"], offsets=s["offsets"], offset_chosen=s["offset_chosen"],
            held_out_lines=s["held_out_lines"], tables=s["tables"], hot_map_floor_kpa=s["hot_map_floor_kpa"],
            lambda_ref=s["lambda_ref"], per_held_out_line=s["per_held_out_line"], deciding_lines=s["deciding_lines"],
            pooled_counts=s["pooled_counts"], coverage=s["coverage"], n_rows=s["n_rows"], n_held_out_rows=s["n_held_out_rows"],
            held_out_rows=s["held_out_rows"], alpha_nodes_removed=[n for n in alpha[eng] if n["held_out"]],
            fuel_by_table=FUEL_BY_TABLE[eng], lambda_clip_floor=LAM_FLOOR[eng])

    flat = []
    for eng in ENGS:
        for r in ROWS:
            flat.append(dict(engine=eng, row=r["id"], kind=r["kind"], part=r.get("part"), quantity=r["quantity"], statistic=r["statistic"],
                             R=r["R"], unit=r["unit"], rows=f"engines.{eng}.held_out_rows (Final and steady; Initial only in E1i)",
                             on_fail=FAIL.get(r["kind"]) if r["kind"] in ("level", "d") else FAIL["descriptive"]))
        for r in CARS:
            if eng in r["engines"]:
                flat.append(dict(engine=eng, row=r["id"], kind=r["kind"], part=r.get("part"), quantity=r["quantity"], statistic=r["statistic"],
                                 R=r["R"], unit=r["unit"], rows="D3 segments, never used by the calibration" if r.get("blind") else "-",
                                 on_fail=FAIL[r["kind"]]))
        for r in TABLE:
            flat.append(dict(engine=eng, row=r["id"], kind=r["kind"], part="P6" if r["kind"] == "table" else None, quantity=r["quantity"],
                             statistic=r["statistic"], R=r["R"], unit=r["unit"], rows="table against exact cycle (no EPA rows)",
                             on_fail=FAIL["table"] if r["kind"] == "table" else FAIL["descriptive"]))
    for r in TABLE:
        flat.append(dict(engine="b58", row=r["id"], kind=r["kind"], part="P6" if r["kind"] == "table" else None, quantity=r["quantity"],
                         statistic=r["statistic"], R=r["R"], unit=r["unit"], rows="table against exact cycle",
                         on_fail=FAIL["table"] if r["kind"] == "table" else FAIL["descriptive"]))
    c5 = next(r for r in CARS if r["id"] == "C5")
    flat.append(dict(engine="b58", row="C5", kind="rule", part=None, quantity=c5["quantity"], statistic=c5["statistic"], R=c5["R"],
                     unit="% (the demand must sit MORE than R_E1a from the threshold: the B58 has no EPA E1a)", rows="-", on_fail=FAIL["rule"]))

    inputs = {fn: common.sha_text(os.path.join(common.OUT_DIR, fn))
              for fn in ("split.json", "alpha_nodes.json", "b58_propagation.json", "knee_shift.json")}
    for p in sorted(glob.glob(os.path.join(common.ECU_DIR, "*.json"))):
        inputs["ecu/" + os.path.basename(p)] = common.sha_text(p)
    run = inp.get("run") or {}
    py = run.get("python", "unrecorded")
    npv = run.get("numpy", "unrecorded")
    low_end = 1.0 - RSS / MEI
    SH = f"{DECISIONS_DOC} section H"
    ADOPTED_H = "adopted under Ghassan's delegation of 21 October 2026"

    # on_failure.d as the JSON states it: version 3's text with the third way a d row has no statistic named, E8's short
    # subset (after version 4's seventh review). The d entries of thresholds keep version 3's on_fail, FAIL["d"], which
    # step 7's digests of version 3 hold.
    fail_d = dict(FAIL["d"], untested=FAIL["d"]["untested"].replace(
        "(no deciding line, or excluded for every constant it claims to test)",
        "(no deciding line, excluded for every constant it claims to test, or, version 4, E8 with a subset short of "
        f"{E8_MIN_ROWS} rows: conventions.statistic_details.e8_subsets)"))
    assert fail_d["untested"] != FAIL["d"]["untested"]
    contract = {
        "_generated": ("the machine-readable half of results/ENGINE_THRESHOLDS.md (version 4, 22 October 2026, corrected seven times "
                       f"on 23 October after its seven reviews, of which the first, fourth and fifth raised decisions 73-76, written in on the same day and adopted "
                       f"under the delegation of 21 October as every decision of {SH} is: version 3 with the rule text of decisions "
                       f"39, 57 and 73-76 of {SH}, written after the plant changes of build step 2 and before any fit; "
                       f"version 3, 21 October 2026, was version 2 with decisions 36-38 of {SG} applied), written by "
                       "engine_thresholds.py before any calibration of the three EPA engines"),
        "schema": 4,
        "status": "binds from its first commit on GRA-test, which must precede calibrate_epa.py; every script that reads it records its sha256",
        "decisions": {"35": "thresholds from the MEI, committed before calibrating", "28": "table gates; score on the exact cycle; backends as fingerprint fields",
                      "33": "K3 knee per engine; 850 C as a sensitivity row", "34": "the test roads", "26": "one verdict per engine per horizon; the collapse as a declared cross-plant comparison",
                      "27": "three arms per engine, two horizons", "30": "seeds per arm from the measured rate and window, target >= 20",
                      "5": "MEI 5.43 points of cut", "3": "R1 10 K turbine-equivalent", "4": "label rules, k = 2",
                      "36": (f"an untested d row with a statistic enters as a preregistered band ((|E| + 2u)/R)*b and the verdict inside it "
                             f"reads MODEL-LIMITED; a row with no statistic drops the engine ({SG}, adopted 21 October 2026)"),
                      "37": f"the collapse test's equivalence margin is the MEI, {MEI} points ({SG}, adopted 21 October 2026)",
                      "38": f"b = MEI/6 = {MEI / 6:.3f} points per part, for six parts; every d-row R scales by 5/6 ({SG}, adopted 21 October 2026)",
                      "39": (f"contract version 4, written after the plant commit and before any script that names the EPA tables ({SH}, "
                             f"{ADOPTED_H}): (a) E8 in-sample, outside the form criterion; (b) the neutral-action identity; (c) C5's "
                             "threshold by decision 70; (d) decisions 49, 54, 55, 59's counting rule, 64 and 71 as rules; (e) the code "
                             "citations moved to the new lines"),
                      "40": (f"the Accord's ratio law, a stateless kickdown: hold the top ratio while the demand at N_eco is at most "
                             "kickdown_load of the deliverable torque there (ASSUMED), otherwise the lowest engine speed whose demand "
                             "is at most target_load of it (DESIGN); C5's CVT threshold is its kickdown threshold (cars C5 "
                             f"threshold.cvt; engines.CvtCar, CvtVehicle.ratio_for; {SH}, {ADOPTED_H})"),
                      "49":f"each engine its own model form (model_form.in_sample_rules; {SH}, {ADOPTED_H})",
                      "54": (f"rows without lambda, the -120 spark sentinel, censored lambda (conventions; {SH}, {ADOPTED_H}); "
                             "with version 4's readings of it, each with its reason, written after its fourth review: a sentinel "
                             "row's spark in D1, and the rows E8's dl and ds are taken over (conventions.lambda_missing, "
                             f"spark_sentinel); and, after its fifth, each subset's minimum of {E8_MIN_ROWS} rows, below which "
                             "E8 has no statistic and the engine is dropped (conventions.statistic_details.e8_subsets); and, after "
                             "its sixth, an empty Spark Timing cell read as the sentinel (spark_sentinel), a Ford HD1 row with an "
                             "empty bank read as a row without lambda (lambda_missing), and E8's list of the censored held-out "
                             "Final rows, dl reported without them (censored)"),
                      "55": f"an in-sample statistic with no calibration line neither blocks nor passes (model_form.in_sample_rules; {SH}, {ADOPTED_H})",
                      "57": (f"the statistic details of docs/build_step_2/PLAN.md decision 57 that version 3 left open, written as "
                             f"rules because each moves its statistic (conventions.statistic_details; {SH}, {ADOPTED_H}: 'As the plan "
                             f"states'; docs/build_step_2/AMENDMENTS.md A1 puts it in the group answered before version 4's text)"),
                      "59": f"the E6 readings and the Tests lists' counting rule (perturbations_E6, tests_lists; {SH}, {ADOPTED_H})",
                      "64": (f"C5 against the held-out E1a: the roads drawn at R_E1a, the re-check at max(R_E1a, |E1a| + 2u_val) "
                             "of E1a's worst deciding line, the redraw streams fixed by the roads' own seed, the cap "
                             f"decision 76's, gear-sensitive cars (cars C5 redraw; {SH}, {ADOPTED_H})"),
                      "70": f"C5's threshold is the one the gearbox code applies; the CVT's is decision 40's kickdown threshold (cars C5 threshold; {SH}, {ADOPTED_H})",
                      "71": f"L1's tightening is measured on the B58, on decision 34's roads (rows L1 basis; {SH}, {ADOPTED_H})",
                      "73": (f"C5's steps: every step of a scored climb outside its transitions (the ramps of its grade changes "
                             f"and its changes of speed, a change being exact inequality of the road's recorded arrays), the "
                             f"transition steps' margins and gear sequence reported beside the result, not gated, with each "
                             f"climb's share of transition steps; at least one gated step on every scored climb; a scored climb "
                             f"runs from the first step of its ramp up to the last of its ramp down, a missing neighbour at the "
                             f"road's ends taken as the step itself; and, after the fifth review, the steps at the time step the "
                             f"road is scored at, a gated step one at which at least one margin gates on the car, the minimum per "
                             f"car, a climb gated on fewer than half its steps on a car flagged thin there, never passed, "
                             f"and the locked climb's transfer row gating nothing; and, after the sixth, the half labelled DESIGN, "
                             f"the third step with no margin and the order the cases decide in, and the reason for not taking "
                             f"the fifth review's reading restated; and, after the seventh, C5's outcome on a car one of "
                             f"three exclusive cases, fails, thinly checked or passes, a thin climb that fails at a gated "
                             f"step failing C5 (cars C5 steps; {SH}, {RAISED_V4})"),
                      "74": (f"a climb slot whose redraws reach decision 64's cap keeps the last climb accepted for it, for every car (decision "
                             f"75), scored and flagged gear-sensitive, with its margins listed, on each car on which it fails, and "
                             f"each such car's results are reported with and without its flagged slots; a slot of a car with no "
                             f"passing climb keeps its last draw in the same way, so every slot at the cap keeps its last draw "
                             f"(cars C5 redraw; on_failure.rule; {SH}, {RAISED_V4})"),
                      "75": (f"a climb slot is shared by the four cars: decision 34 draws one set of test roads whose preview "
                             f"ceiling is at least 2 MEI on every engine, so a redraw replaces the climb for every car, every "
                             f"car's C5 is checked again on the new climb, the cap counts a slot's redraws over all cars, and a "
                             f"redrawn climb must pass every test of a first draw (decision 34's ceiling on every engine, applied "
                             f"to the road set with the candidate in the slot; C5 at R_E1a with at least one gated step on every "
                             f"car; and the roads step's own checks), the slots redrawn in their order on the roads, a candidate "
                             f"filling its slot's recorded extent (after the sixth review); the other "
                             f"option, per-car slots, was not taken (cars C5 redraw; on_failure.rule; {SH}, {RAISED_V4})"),
                      "76": (f"decision 64's cap on redraws, {REDRAW_CAP} per climb slot counted over all cars, and a bound of "
                             f"{REDRAW_DISCARDS} discarded candidates per slot, after which the slot keeps its last climb as at the "
                             f"cap, both fixed in this contract before any fit and from no data (DESIGN); each slot's stream drawn "
                             f"with the first draw's code from numpy.random.default_rng([roads_seed, 0x{REDRAW_STREAM_TAG:X}, k]), "
                             f"fixed by the roads' own seed alone (the derivation after the sixth review; cars C5 redraw cap, "
                             f"discards, stream; {SH}, {RAISED_V4})")},
        "mei_points": MEI, "r1_housing_k": R1_K,
        "budget": {"b_points": round(B, 3), "b_over_mei": round(B_FRAC, 6), "parts": [dict(id=p, what=w, rows=r) for p, w, r in PARTS],
                   "n_parts": len(PARTS), "linear_sum_points": round(LINEAR, 3), "rss_points": round(RSS, 3),
                   "rss_over_mei": round(RSS / MEI, 3),
                   "decision": f"38: b = MEI/{n_shares} per part ({SG})",
                   "version_2_at_mei_over_5": {k: R_V2[k] for k in D_ROWS}},
        "collapse_test": {
            "equivalence_margin_points": MEI, "equivalence_margin_over_mei": 1.0,
            "decision": f"37 ({SG}, adopted 21 October 2026)",
            "what": ("decision 26's cross-plant comparison of the per-engine d (one per engine and horizon): a difference d_i - d_j "
                     "counts as equivalent only within +-MEI, and it carries its model band sqrt(band_i^2 + band_j^2) beside its "
                     "seed uncertainty (section 7)"),
            "false_negative": (f"with the six parts at their limits and independent, a true d at the MEI reads {low_end:.2f}-"
                               f"{1.0 + RSS / MEI:.2f} MEI, so the preregistration's seed reasoning (decision 30) states its "
                               f"false-negative risk at d_obs = {low_end:.2f} MEI, not at the MEI (review finding 28); at about 20 seeds "
                               "per arm the test can refute a collapse but will rarely confirm one within the MEI, and the "
                               "preregistration says so (decision 37)")},
        "propagation_b58": {
            "source": (f"engine_thresholds.py step 3 (thresholds/b58_propagation.py) on the B58 plant (engines.get('b58'), Python {py}, "
                       f"NumPy {npv}): locked climb, neutral action, frozen episode 1, dt 1 s; no EPA data"),
            "climb_point": {k: round(v, 3) for k, v in c["point"].items()},
            "f_climb": round(hs["f"], 4), "tau_climb_s": round(hs["tau_s"], 2), "dTh_per_unit_ln_mdot_k_b58": round(hs["dTh_per_unit_ln_mdot"], 2),
            "G_gas_over_42C_k": round(G_K, 2),
            "fixed_spark_torque_bias_1pct": {k: round(v, 4) for k, v in c["fixed_spark"]["torque_bias_1pct"].items()},
            "ecu_schedule_torque_bias_1pct": {k: round(v, 4) for k, v in c["ecu_schedule"]["torque_bias_1pct"].items()},
            "ecu_spark_slope_deg_per_kpa": round(c["ecu_schedule"]["dspark_dmap_deg_per_kpa"], 4),
            "env_torque_bias": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in env.items()},
            "used": {"gas_k_per_pct_torque": round(GAS_PER_PCT, 3), "flow_pct_per_pct_torque": round(FLOW_PER_PCT, 3),
                     "housing_k_per_pct_torque_b58_f": round(HOUSE_PER_PCT_B58, 3), "housing_k_per_pct_torque_bound": round(HOUSE_PER_PCT_BOUND, 3),
                     "housing_k_per_pct_flow_bound": round(HOUSE_PER_PCT_FLOW, 4), "f_star": round(F_STAR, 3)},
            "lambda_egt_k": {k: round(v["degt"], 2) for k, v in c["lambda"].items()},
            "spark_egt_k_torque_pct": {k: [round(v["degt"], 2), round(100 * v["dtorque_rel"], 2)] for k, v in c["spark"].items()},
            "flat": {"point": {k: round(v, 3) for k, v in b58["flat"]["point"].items()}, "f": round(b58["flat"]["housing"]["f"], 4),
                     "tau_s": round(b58["flat"]["housing"]["tau_s"], 2),
                     "ecu_schedule_flow_pct_per_pct_torque": round(-100 * b58["flat"]["ecu_schedule"]["torque_bias_1pct"]["dmdot_rel"], 3)},
            "episode_damage_neutral_action": round(b58["episode_summary"]["damage"], 2), "peak_t_turb_c": round(b58["peak_t_turb_c"], 2),
        },
        "knee_shift": {"source": "engine_thresholds.py step 4 (thresholds/knee_shift.py): committed per-step records re-scored (results/agents/<set>/*/eval_record.npz)",
                       "largest": SLOPE, "largest_at_10k": SLOPE_10, "all": slopes},
        "ecu_strategy_b58": {"source": ("engine_thresholds.py step 5 (thresholds/ecu_shift.py): the B58's boosted ECU output shifted (MAP > 100 kPa), "
                                        "locked climb, frozen episode 1, dt 1 s, the four hand-written policies"),
                             "k3_pair_change_vs_lambda": RESP_L, "k3_pair_change_vs_spark": RESP_S,
                             "fixed_knee_pair_change_vs_lambda": RESP_L_FIX, "fixed_knee_pair_change_vs_spark": RESP_S_FIX,
                             "worth_b": W,
                             "k3_rows": {n: dict(knee_c=round(j["knee_k"] - 273.15, 2), base_lambda=round(j["base_lambda_median_400_718"], 3),
                                                 base_spark=round(j["base_spark_median_400_718"], 2),
                                                 cuts_pct={k: {p: round(v, 2) for p, v in cuts(j, k).items()} for k in ("damage", "damage_thermal")})
                                         for n, j in sorted(K3.items())}},
        "conventions": {
            "inputs_fed": "EPA's speed, intake manifold pressure, intake manifold temperature (as the charge temperature), coolant, spark (as published) and lambda (below); the rest is the calibrated model's, the back-pressure law included",
            "lambda": "rows within 0.02 of their table's lambda_ref run at 1.00; every other row at lambda_meas - (lambda_ref - 1); the Ford HD1 lambda is the mean of its two banks; E6 row 12 runs every row without the snap",
            "fuel": ("each table's own fuel: LHV and AFR_st from its fuel report's analysis (epa_engine.json alpha_fuel of that FTAG; AFR_st "
                     "from the carbon weight fraction, hydrogen the balance, oxygen-free); the plant and the thermal network take them per "
                     "engine (since build step 2: engines.Fuel, read at plant.py:220 and :233 and thermal.py:255; engines.with_fuel moves "
                     "both), and every calibration and validation row runs on its own table's LHV and AFR_st whatever fuel the "
                     "engine's plant in use carries (decision 69 sets the Ford's; it is not a rule of this contract); the convention "
                     "covers LHV and AFR_st, the two engines.with_fuel moves, and not the octane, which is engines.CycleCal's: how "
                     "the Ford's Cell 9 rows, of another batch than HD1's, treat it is declared by the calibration scripts before "
                     "they are committed (docs/build_step_2/HANDOFFS.md, WP3 item 5); 44.0 MJ/kg and 14.7 are E6 rows 2-3"),
            "lambda_missing": ("version 4, decision 54: a fired row without lambda runs at lambda 1.00, flagged, and every statistic is "
                               "also reported without such rows. It is in no lambda band: the lambda~1 and enriched bands are defined "
                               "on the row's own lambda, and the split classifies such a row into neither (thresholds/split.py, "
                               "classify); so it enters, at lambda 1.00, the statistics of the fired and hot populations (E1, E2, D1) "
                               "and none taken over a lambda band (E3, E4, E5, L0, L1). In E8, which compares the model ECU with "
                               "EPA's own lambda and spark, it enters ds only, and dl is taken over the Final rows that publish "
                               "lambda; the counts behind dl and ds are reported. That is version 4's reading of decision 54, "
                               "written after its fourth review: read literally, 'every statistic' would compare such a row's EPA "
                               "lambda as 1.00, a value EPA did not publish, so the dl that gates is the one without such rows, "
                               "and dl with them at 1.00 is reported beside it, so that dl is reported both ways as decision 54 "
                               f"asks. dl needs at least {E8_MIN_ROWS} rows that publish a lambda, or E8 has no statistic "
                               "(statistic_details.e8_subsets). A Ford HD1 row with either bank's lambda empty is a row without "
                               "lambda (version 4's reading of decision 54, written after its sixth review): the HD1 lambda is the "
                               "mean of its two banks (thresholds/split.py, lam), which then has none, and the split already "
                               "classifies such a row into no lambda band; one bank alone is not the lambda every other HD1 row is "
                               "given"),
            "spark_sentinel": ("version 4, decision 54: a row whose published spark is EPA's sentinel, exactly -120 (the Mazda's "
                               "fuel-cut points read so, epa_map.py:47-48), enters no fit; in every statistic, in-sample and held-out alike, it runs at "
                               "the model ECU's spark (30 s dwell, no knock retard, EPA's intake temperature), flagged, and every "
                               "statistic is also reported without it: a declared outcome, never a stop. Version 4's readings of "
                               "decision 54, written after its fourth review, each with its reason: (1) in E8 it has no published "
                               "spark to compare: it enters dl only, and the ds that gates is taken over the Final rows that publish "
                               "a spark, since run at the model ECU's spark it would add a difference of zero to ds by construction, "
                               "which is no measurement and would pull ds toward a pass; ds with those rows, at a difference of "
                               "zero, as decision 54 reads literally, is reported beside it, so that ds is reported both ways; (2) "
                               "in D1 it runs at the model ECU's spark at EPA's MAP, the spark it runs at in every other statistic, "
                               "plus s*(MAP - MAP_EPA), as a published spark is moved to the inverted MAP, so that D1 treats every "
                               "row alike; the other reading, the model ECU's spark at the inverted MAP, differs from it by the "
                               f"schedule's curvature over MAP - MAP_EPA. ds needs at least {E8_MIN_ROWS} rows that publish a spark, "
                               "or E8 has no statistic (statistic_details.e8_subsets). A row whose Spark Timing cell is empty is a "
                               "sentinel row: it enters no fit, and in every statistic, E8 and D1 included, it runs as above (version "
                               "4's reading of decision 54, written after its sixth review, its fit named after its "
                               "seventh): it publishes no spark either, and version 3, which fed every row "
                               "its spark as published, had no rule for it. Whether any fired row has an empty spark, or any HD1 "
                               "row an empty bank (lambda_missing), was not looked up when these readings were written: the session "
                               "that wrote them opened no EPA table, epa_channels.csv included, and each rule holds either way"),
            "held_out_counts": ("version 4, decision 54: the held-out rows' counts of lambda-less and sentinel rows are taken only "
                                "when the held-out run is armed, before any statistic; with them, whether each of E8's subsets "
                                "holds enough rows (statistic_details.e8_subsets) is decided before E8 is computed"),
            "censored": ("version 4, decision 54: an engine's lambda is censored when at least 2 of its calibration High Load Final "
                         "rows sit at their own minimum lambda within 1e-9, or at a documented sensor floor: defined on the "
                         "calibration Final rows themselves, never on all rows; censored rows are kept, treated one-sided in the "
                         "enrichment fit, and flagged in E4a and E4b. A sensor floor is documented only by a source opened and "
                         "cited before the fit that states the lower end of the range of the lambda sensor EPA used on that "
                         "engine (EPA's report of that test, or the datasheet of a sensor it names); with no such source, only "
                         "the two-row test applies. E8 lists them too, and gates nothing on the list (version 4, written after "
                         "its sixth review): its dl compares EPA's lambda on the held-out Final rows, and a reading held at the "
                         "sensor's floor sits above the lambda the engine ran, which biases dl. A held-out Final row is "
                         "censored when its engine's lambda is censored and the row's lambda sits at the censoring value, the "
                         "calibration rows' minimum within 1e-9 or the documented floor; one whose lambda reads below the "
                         "censoring value is not counted censored, since it shows that the sensor reads lower (after the "
                         "seventh review); E8 lists the censored rows and "
                         "reports dl without them beside the dl that gates, and the list moves no label, R, population or "
                         "statistic"),
            "statistic_details": {
                "decision": (f"57 ({SH}, {ADOPTED_H}): 'As the plan states', the details of docs/build_step_2/PLAN.md "
                             "decision 57 and sections 6.2-6.4 that version 3 left open; each is written here because it moves "
                             "its statistic, and none moves an R"),
                "d1": ("D1's inversion pre-scans the model's torque over 20-400 kPa every 10 kPa and bisects the first bracket (the "
                       "first pair of neighbouring pre-scan pressures, from 20 kPa up, between which the model's torque crosses "
                       "EPA's) to 1e-3 kPa; a row with no bracket is evaluated at the nearer bound, the end of 20-400 kPa at which "
                       "the model's torque is nearer EPA's, listed and counted there, and that D1 is the one that gates, in-sample "
                       "and held-out; D1 is also reported without those rows. On a form-D engine the intake cam is the model "
                       "ECU's schedule cam(rpm, MAP) at the inverted MAP, evaluated there, not moved linearly as the spark is "
                       "(docs/build_step_2/PLAN.md section 6.3, D1's row; decision 41: the cam is run by the ECU); in every "
                       "statistic at EPA's MAP it is the schedule at the row's MAP. A sentinel row's spark in D1 is "
                       "spark_sentinel's (version 4's reading of decision 54)"),
                "e8": ("EPA's lambda in dl is lambda_meas - (lambda_ref - 1), unsnapped: the snap (lambda) is a rule for the "
                       "lambda fed to the model, and E8 compares EPA's lambda, which it feeds to nothing; the snapped E8 is "
                       "reported beside it, descriptive, so E6 row 12 does not list E8. The rows dl and ds are taken over are "
                       "version 4's reading of decision 54 (lambda_missing, spark_sentinel), not decision 57's. P is piecewise linear "
                       "through the measured shifts; a shift beyond them is extrapolated linearly from the last segment "
                       "(thresholds.contract.interp), and flagged. u_val propagates u(dl) and u(ds) through the slope of the "
                       "segment that holds the shift, at a shift of exactly 0 the steeper of the two segments beside it. The "
                       "tightening keeps, at each shift, the larger |response|, with its sign"),
                "e8_subsets": ("version 4's reading of decision 54, written after its fifth review: dl and ds are each a pooled "
                               "mean over its own subset of the held-out High Load Final rows, dl over those that publish a "
                               f"lambda and ds over those that publish a spark, and each needs at least {E8_MIN_ROWS} rows "
                               f"({E8_MIN_ROWS} clusters, a Final row being one), the least on which this contract computes a "
                               "line's statistic (thresholds/split.py MIN_CLUSTERS; the line rule of rows). If either subset "
                               "has fewer, E8 has no statistic: it is a d row with no statistic, and the engine is dropped "
                               "(on_failure.d; decision 36). The term of a subset that is large enough, and dl and ds over "
                               "every Final row as decision 54 reads literally (lambda 1.00, a spark difference of zero), are "
                               "then reported, descriptive. Why: E8 is the sum of the baseline's two levers, and the term a "
                               "short subset leaves out would read that lever as exact, the guessed baseline of mistake 3; "
                               "taking it over every Final row instead would compare a lambda of 1.00, or a spark difference "
                               "of zero, that EPA did not publish. Version 3's one population, the held-out Final rows "
                               "(engines.<id>.pooled_counts.E8_final_rows), is at least that large on every engine; the counts "
                               "that decide the subsets are taken when the held-out run is armed (held_out_counts), so the "
                               "outcome is fixed before E8 is computed"),
                "e8_min_rows": E8_MIN_ROWS,
                "lines": ("a per-line row reports its worst deciding line's E with that line's u_val and u_stat, and every deciding "
                          "line is labelled and reported (the line rule of rows). The worst deciding line is the one with the "
                          "largest |E_l|, as the level rows' statistic takes it, and of two with equal |E_l| the one with the "
                          "larger u_val (defined after version 4's fourth review: C5's re-check margin reads it, cars C5 "
                          "redraw.recheck)"),
            },
            "air_for_calibration": "fuel_meter_flow x AFR_st(table) x lambda_model, on steady and Final rows only (High Load Initial carries no meter)",
            "populations": "fired: BMEP >= 2 bar; hot: Final rows and steady rows at or above the engine's lowest high-load MAP; lambda~1: |lambda - lambda_ref| <= 0.02; enriched: lambda <= lambda_ref - 0.05; High Load Initial rows only in E1i",
            "u_val": "sqrt(u_num^2 + u_input^2 + u_D^2) after V&V 20 (VALIDATION_PLAN.md:53), each term the uncertainty of the population's mean (random parts / sqrt(n_clusters), common parts in full); u_stat, the standard error of the mean with each hold one cluster, is reported beside it and decides only whether a line may certify a pass (2*u_stat <= R)",
            "u_D": "EPA's stated accuracy where its reports give one; else for thermocouples IEC 60584-1 class 2, 0.0075*|t| as a uniform half-width (UNSOURCED for EPA's sensors), for lambda the Ford's inter-cell disagreement 0.02 as a uniform half-width (0.012), otherwise resolution/sqrt(12), each marked unsourced",
            "labels": FAIL["label_domain"],
        },
        "model_form": {
            "base_A": "plant.run_cycle unchanged with the engine's geometry and fuel; fitted per engine on calibration rows: VE (ve_base, ve_amp, ve_rpm, ve_width), FMEP, burn and delay (burn_base, burn_rpm, delay_base, delay_rpm), UA_PORT, the back-pressure law (to Turbine Inlet Press where published), the knock scale (E6 row 7); shared and not fitted: combustion_efficiency(lambda), gamma(T), the residual-fraction law, t_head, port pickup, t_residual, cp_exh, the Wiebe shape; fixed valve events (no cam input); the ECU: spark = min(part-load map, knock-limited surface), lambda = an enrichment schedule, fitted to calibration rows",
            "alternatives_in_order": ["B: VE in rpm and MAP (a linear MAP term)", "C: a per-engine rich-side slope of combustion_efficiency, fitted on enriched hot calibration rows",
                                      "D: the intake cam phase as an input to VE through a schedule cam(rpm, MAP) fitted to EPA's Intake Cam Phase on calibration rows, scheduled by the ECU"],
            "in_sample_stage": ("every gating statistic computed on the calibration lines with the same definitions (fit residuals, never "
                                "labelled); each engine's form is the first of A, A+B, A+B+C, A+B+C+D at which every one of its own "
                                "in-sample statistics satisfies |E_cal| <= R, E8 aside and a statistic with no calibration line neither "
                                "blocking nor passing (in_sample_rules, version 4); if none does, A+B+C+D, with the failing statistics "
                                "reported; then the form and constants are frozen (sha256) and the held-out statistics are computed once"),
            "in_sample_rules": {
                "form_per_engine": (f"decision 49 ({SH}, {ADOPTED_H}): each engine its own form, the first that ITS in-sample statistics "
                                    "pass; the three EPA engines need not share one; each engine's form and its residual structure are "
                                    "reported (mistake 20)"),
                "e8": (f"decision 39(a) ({SH}): E8 is computed in-sample, with its held-out definition, and reported, but it is outside "
                       "the form criterion: its inputs are the ECU fit alone (the model ECU's lambda and spark at the Final rows), which "
                       "no form A-D changes, so counting it would force A+B+C+D for a reason no form addresses; its held-out row is unchanged"),
                "no_calibration_line": (f"decision 55 ({SH}, {ADOPTED_H}): an in-sample statistic with no calibration line that meets its "
                                        "population's line minimum neither blocks a form nor passes it, and is recorded per form; the "
                                        "held-out rule is unchanged (a d row with no statistic drops the engine, on_failure.d)"),
                "r_in_sample": (f"the R of the in-sample stage is the one this contract states for each row: L1's is {R['L1']} K, "
                                "since L1's tightening (rows L1 basis; decision 71) is measured on decision 34's roads, drawn on "
                                "the frozen plants after the in-sample stage (order_of_work); a tightened R gates the held-out L1 "
                                "only (version 4, written after its fourth review)"),
            },
            "plant_in_use": "the subset fit (calibration rows only) IS the plant that trains and scores; its coverage is the calibration rows' (engines.<id>.coverage.calibration_*), and the scored climbs must lie inside it (review finding 27, choice b)",
            "lambda_clip_floor": ("per engine min(0.70, the engine's deepest EPA lambda on the cell-referenced convention - 0.01), so the "
                                  "neutral action stays neutral (mistake 10; the environment clips every policy's lambda to the engine's "
                                  "ecu.lam_floor and ecu.lam_ceiling, engine_env.py:1316 in SupervisoryTunerEnv.step: "
                                  f"{B58_CLIP['lam_floor']:.2f} and {B58_CLIP['lam_ceiling']:.2f} on the B58, engine_specs/b58.toml:143-144 "
                                  "(version_4.plant_values); until build step 2 it clipped every engine at "
                                  f"{V3_LAM_CLIP[0]:.2f}-{V3_LAM_CLIP[1]:.2f}, the literals of version 3's engine_env.py line 1006 "
                                  f"({V3_TREE}), which the B58's spec keeps)"),
            "neutral_action_identity": {
                "decision": f"39(b) ({SH}, {ADOPTED_H}); docs/build_step_2/AMENDMENTS.md E1",
                "action": ("engine_env.neutral_action(): its spark, lambda and boost trims rescale to exactly 0.0 in float32 "
                           "(SupervisoryTunerEnv._rescale), its fan and pump to 1.0 (version_4.plant_values; step 7 checks both)"),
                "identity": ("at every step of the episode, the agent's lambda equals float32(lambda_b) and its spark float32(spark_b), "
                             "lambda_b and spark_b the baseline ECU's outputs of that step (BaselineECU.step, called at engine_env.py:1283); "
                             "reported: the largest |difference| on each channel over the episode, which must be 0, and the clip "
                             "contacts, which must be 0"),
                "contact": ("a step at which one of the two channel clips changed the value it was given, np.clip(x, lo, hi) != x, x the "
                            "float32 sum SupervisoryTunerEnv.step forms: lambda_b + trim against ecu.lam_floor and ecu.lam_ceiling "
                            "(engine_env.py:1316), spark_b + trim against ecu.spark_min and ecu.spark_max (engine_env.py:1310-1311). "
                            "The comparison is the environment's own, in float32: a Python float bound is cast to float32 against a "
                            "float32 sum (NEP 50), and a NumPy float64 one would make the comparison, and the result, float64. The "
                            "lambda bounds are Python floats by engines.Engine's own check (engines.py:598-602); the spark bounds have "
                            "no such check: the B58's are typed in its spec as floats (engine_specs/b58.toml:119-120), and an EPA "
                            "engine's are DERIVED, which engines._number converts to a Python float (engines.py:1032-1035). The "
                            "identity check therefore asserts, before it runs, that all four bounds are Python floats (type(x) is "
                            "float). A script that compares with float64 bounds counts float32(lam_floor) < lam_floor as a contact, "
                            "and is wrong. So could the environment, if a spark bound were a NumPy float64: at a step where "
                            "BaselineECU.step returns exactly spark_min, the clip would compare float32(spark_min), which can sit "
                            "below spark_min, in float64. A value equal to a "
                            "bound is not a contact: the build-step-2 invariant 1 - enr_depth >= lam_floor (engines.Engine, "
                            "engines.py:603) lets the baseline's deepest lambda sit exactly on float32(lam_floor), and equality would "
                            "count a contact only if that invariant were strict. Only the two channel clips count: the action box "
                            "(SupervisoryTunerEnv._rescale, engine_env.py:1031), the slew and action-range clips and the spark-trim "
                            "cap (engine_env.py:1249-1251) are not contacts, since the slew moves the fan and pump by design after "
                            "reset and a change any of them made to a trim shows as a difference of the identity. The certificate harness's HARNESS_BIND_COUNT, "
                            "which counts equality with float32(bound), is not this count (docs/build_step_2/HANDOFFS.md, WP2 item 2)"),
                "not_compared": ("the fan and pump: the neutral action's 1.0 each (slewed up from 0 after reset, engine_env.py:1223), not the baseline's "
                                 "scheduled fan and default pump; with the agent's charge temperature, which its own network sets, the "
                                 "thermal trajectories, and with them the agent's MAP, fuel, gas and damage, differ by design"),
                "where": ("each EPA engine's locked climb (the completion, docs/build_step_2/PLAN.md section 5.9 item 3); the B58's "
                          "locked climb, which has no completion step, in the roads step, which changes engine_env.py and so runs a "
                          "B58 certificate of its own (docs/build_step_2/PLAN.md, WP5); and every engine's test roads of decision 34 "
                          "(the roads step)"),
                "on_failure": "a coding defect (on_failure.identity)",
            },
        },
        "split_rule": "version 2: lines are the union of an engine's tables' nominal speeds (50 rpm merges); eligible lines are interior in the union, the steady lines and the high-load lines; positions o+1, o+4, ... held out, o chosen by structure (>= 2 held-out lines with >= 3 holds where possible; then most E4b-usable enriched rows; most rows; lowest o); a line goes with all its rows",
        "calibration_may_use": "every row of a non-held-out line (High Load Initial only for the WOT torque curve, labelled a transient peak); ALPHA's curves only at nodes whose measured source row is a calibration row; never the ALPHA fuel map, the Tier 3 / LEV III packages, the Steady State with Transmission sheets, the SAE 2018-01-0319 dataset, or any D3 file",
        "order_of_work": ["commit this contract", "calibrate each engine on its calibration rows (calibrate_epa.py, committed before it runs), the in-sample stage included; freeze",
                          ("draw decision 34's roads on the frozen plants, one set whose climb slots the four cars share (decision 75), "
                           "C5 applied at R_E1a on every car, with the roads' own seed, which fixes the redraw streams, committed with them and decision 76's "
                           "cap and discard bound (decisions 64 and 76); on them measure, on the B58 plant (decision 71), the hand-written preview "
                           "pair's knee-shift slope (L1's tightening) and re-run the B58 ECU shifts (E8's tightening)"),
                          ("compute every held-out statistic once; label; decide (section 7); re-check every scored climb's C5 on "
                           "every car at its max(R_E1a, |E1a| + 2u_val) and redraw the failures for every car, each redraw passing "
                           f"every test of a first draw, at most {REDRAW_CAP} redraws per slot counted over all cars and at "
                           f"most {REDRAW_DISCARDS} discarded candidates (decisions 64, 75 and 76)"),
                          "build and gate the tables (S1; S2a)", "write and commit the preregistration (the backend rule, the bands, the equivalence margin)",
                          "S2b pilots on the tables; train"],
        "engines": eng_out,
        "rows": ROWS, "cars": CARS, "c3_segments": SEG, "d3_files_c3": D3, "table_gates": TABLE, "perturbations_E6": E6,
        "tests_lists": TESTS,
        "on_failure": dict(FAIL, d=fail_d), "thresholds": flat,
        "open_for_the_team": [
            (f"Jad's column of decisions 36-38 ({SG}) and 39-76 ({SH}, 66 dropped) is empty. Ghassan's column of 39-76 "
             "records his delegation of 21 October, under which decisions 73-76, raised on 23 October by the reviews of "
             "version 4, and the readings the agents added the same day to decisions 54, 59 and 64 are adopted as 39-72 "
             "are; for these rows and readings it records only the delegation, no answer of his, and their cells say so "
             "('adopted by the agents 23 Oct, not yet seen'). The first fit (Run 1) waits for both: Jad's column, and "
             "Ghassan's own answer to those rows and readings, the four rule constants version 4 adds among them "
             f"(cars C5 redraw cap_redraws and discards_max, steps thin_below_share; conventions.statistic_details.e8_min_rows), "
             "as the sheet's note of 23 October says ('Both of them answer these rows and readings before the first fit'). "
             "They answer from the team's dated copy of the sheet on the Desktop, "
             "C:/Users/badcl/Desktop/decisions_2026-10-22_H.md, which holds section H as of 22 October, without decisions "
             "73-76 and the readings of 23 October: the commit step updates it with the sheet as committed, before either "
             "of them is asked (after version 4's seventh review). "
             "An answer of Jad's "
             "that differs from the adopted option, or a different answer of Ghassan's, given before the first fit, is "
             "applied before it: in the code, and, where the decision is a rule of this contract, through a new version written "
             "by this generator. Once calibrate_epa.py exists, step 7's claims that it does not and that only the generator, "
             "epa_map.py and test_epa_map.py name the EPA tables stop the generator, so such a version also edits those claims; "
             "the edited claims must still prove that no fit has run, from what a fit leaves behind, as the claims that nothing a "
             "fit writes exists do now (no results/EPA_CALIBRATION/, no EPA engine's data/engines/<id>/derived_params.json, no "
             "results/EPA_VALIDATION/; docs/build_step_2/PLAN.md section 8.1). A fit that crashed before writing an output would "
             "leave none of these, so calibrate_epa.py writes a STARTED record under results/EPA_CALIBRATION/ before its first "
             "model evaluation, as the held-out run writes one (decision 60), and the edited claims require that record to be "
             "absent; today's claim, that nothing exists under results/EPA_CALIBRATION/, already does. That version's own "
             "section says which claims it edited, and why"),
            ("commit A's tree: version 4 was written on 4461a91, before the plant commit, and its code citations are pinned to "
             "that tree (thresholds/document.py CODE_CITES), and its citations of the decision sheet to their rows' text "
             "(SHEET_CITES); it is committed only after python engine_thresholds.py --check "
             "exits 0 on commit A's tree, whose claims include the pins and the scan of every other citation (step 7; "
             "docs/build_step_2/AMENDMENTS.md A3: 'A citation scan resolves every file:line in the regenerated MD against the "
             "commit-A tree'), and if a pin or the scan fails there the citations are remapped and both files regenerated before "
             "the commit, still before any fit (docs/build_step_2/HANDOFFS.md, WP2 item 1)"),
            ("left to later steps by rules written here: the roads' own seed, which fixes C5's redraw streams through the "
             "derivation of cars C5 redraw.stream and is committed with decision 34's roads, after the freeze and before any "
             "held-out statistic, and never changed after the held-out run (cars C5 redraw.rule_0: rule 0 freezes the rule that "
             "fixes when and how it is set, as it does for the roads and the L1 and E8 tightenings; the derivation, the cap and "
             "the discard bound are decision 76's, fixed here), and the roads themselves, with the time step they are scored at, on which C5's steps are counted; "
             "how the Ford's Cell 9 rows treat the "
             "octane, declared by the calibration scripts before they are committed (conventions.fuel; "
             "docs/build_step_2/HANDOFFS.md, WP3 item 5); a documented lambda-sensor floor (conventions.censored)"),
            ("left by version 4's seventh review for a later version of this contract, written before any fit, since the "
             "roads step that needs the answers runs after it: whether a road of decision 34 is one grade array and one "
             "speed array read by every car, so that a generator whose arrays depend on the car, as the extremes kind's "
             "do (engine_env.extreme_speed_profile and grade_floor take the vehicle), cannot draw a shared slot (cars C5 "
             "redraw.slot); whether the cars and the preview ceilings of EPA engines the held-out run drops take part in "
             "the re-check and in a redraw's tests (redraw.recheck, redraw.redraw); by what rule, written before it runs, "
             "the roads step takes roads_seed, and whether it records every seed it ran (redraw.stream); and whether a "
             "candidate's extent is an input of the first draw's code or a property its draw must match (redraw.extent). "
             "The fifth item it left, four citations of lines outside the repository that the .md's appendix A does not "
             "quote, which the scan resolves by the file's name alone, leaves the roads step nothing to settle: such a "
             "version quotes those lines or tightens the scan"),
        ],
        "seen_before_writing": [
            "every channel's minimum and maximum (data/engines/<id>/epa_channels.csv), so the EPA maxima of Turbine Inlet Temp: 900.8 C (Mazda, High Load Final), 833.8 C (Honda, Steady State), 840.1 / 841.8 / 858.6 / 856.3 C (Ford Cell 9 SS / HD1 SS / HLI / HLF); the design notes' 904.0 / 833.8 / 863.3 C mix Tier 2 and Tier 3 workbooks (review_1)",
            "fe_out/design.md:180: 'Settled EPA TIT at 2500-3000 rpm and 13-16 bar is 723-816 C' (per-cell TIT values, not maxima)",
            "for the split and the populations: speed, manifold pressure, BMEP, lambda, intake and coolant temperature per row, the fuel report, and which columns are present; no torque, fuel or TIT value was compared with any model",
            "the B58 table's measured errors (20 Oct): torque 1.17 % p95, EGT 2.36 K p95, cuts within 1.47 points, pair differences within 1.14, hand-written cuts 0.35-0.59, knock flag 99.80-100 %; and 'the denser grid did not shrink these cut differences (max 1.48)' (fe_out/strand_repo-stats-timing.md:167)",
            "X1's and X2's results and the seed statistics behind decisions 29-30",
            "the preview ceiling: 0.13 / 0.42 / 1.19 points on the locked climb",
            "the D3 figures of the vehicles strand (20 Oct) and each car's locked-climb operating point (UNVERIFIED)",
            "the design notes' sections 2-4 (fe_out/design.md:59, :96, :104-116) and both reviews of 20 Oct; the 37 findings of the review of 21 October",
            "computed for this contract on the B58 plant alone: the sensitivities with the ECU in the loop, the ECU-strategy shifts under K3 and at a fixed knee, and the knee-shift re-scores of committed records",
            ("version 3's session (21 Oct), which turned version 2's scripts into this generator and ran it: version 2's two files, "
             "the decision sheet and the generator's outputs; one text search of the tree, for version 2's 1.086, printed a whole row "
             "of the Mazda's steady table (spreadsheet row 191, 4501 rpm, on the calibration line 4500); none of its values was "
             "compared with any model"),
            ("version 4's session (22 October 2026), which re-ran steps 6 and 7 only (--build-only, --check) and computed no number: "
             "the contract's two files and its generator, whose text prints all-row EPA aggregates (the TIT maxima and ranges of "
             "sections 3 and 9, each engine's deepest cell-referenced lambda and its floor, the lambda offsets of E6 row 1, the fuel "
             "analyses) and the generator's printouts; the build-step-2 plan, its amendments and hand-offs, of which "
             "docs/build_step_2/PLAN.md:524 prints the Honda's lambda minimum; the plant code, to move the citations. No EPA table "
             "was opened by the session, no row value was read, and nothing was compared with any model; the generator's own reads "
             "are version 3's (steps 6 and 7 read the tables' fuel_report column and their structure)"),
            ("the session of 23 October 2026 that corrected version 4 after its review, which also re-ran steps 6 and 7 only and "
             "computed no number from EPA data: the same kinds of files (version 3's two files at ef5e14e, version 4's draft of "
             "both, the generator and its printouts, the decision sheet, the build-step-2 plan, its amendments and hand-offs, the "
             "plant code and the B58's spec). No EPA table was opened, no row value was read, and nothing was compared with any "
             "model"),
            ("the session of 23 October 2026 that wrote decisions 73 and 74 into version 4, under the delegation, which also re-ran steps 6 and "
             "7 only and computed no number from EPA data: version 4's two files, version 3's JSON at ef5e14e (to compare), the "
             "generator and its printouts (which print, among other things, each engine's deepest cell-referenced lambda and its "
             "floor), the decision sheet, the build-step-2 plan and hand-offs, and the plant code that builds the grade ramps "
             "C5's steps are defined by (engine_env.py). No EPA table was opened, no row value was read, and nothing was "
             "compared with any model"),
            ("the session of 23 October 2026 that corrected version 4 after its second review, which also re-ran steps 6 and 7 "
             "only and computed no number from EPA data: version 4's two files and its generator, with their printouts (which "
             "print each engine's deepest cell-referenced lambda with its table and source row, its floor, the deciding "
             "lines and the pooled counts), and the review's and its verification's reports, which quote them; version 3's JSON and the plant files of its tree at ef5e14e (to pin section 13's "
             "version-3 lines); the decision sheet, the build-step-2 plan, its amendments and hand-offs, the rows of "
             "REFERENCES.md the contract cites, thresholds/split.py's classifier, and the plant code (engine_env.py, "
             "engines.py, the B58's spec). No EPA table was opened, no row value was read, and nothing was compared with any "
             "model"),
            ("the session of 23 October 2026 that corrected version 4 after its third review, which also re-ran steps 6 and 7 "
             "only and computed no number from EPA data: version 4's two files, its generator and their printouts (the same "
             "aggregates: each engine's deepest cell-referenced lambda with its table and source row, its floor, the deciding "
             "lines and the pooled counts); the third review's and its verification's reports, which quote them, and whose "
             "reviewer's disclosure quotes the intake-cam-phase ranges and row counts of the three epa_channels.csv lines the "
             "contract cites, as that reviewer read them (the ranges the .md's section 2.4 already prints, rounded); version "
             "3's two files at ef5e14e; the decision sheet, the build-step-2 plan, its amendments and hand-offs; and the plant "
             "code (engine_env.py's step, its locked climb and its training roads). No EPA table was opened, no row value was "
             "read, and nothing was compared with any model"),
            ("the session of 23 October 2026 that corrected version 4 after its fourth review and wrote decision 75 in, which "
             "also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files, its generator and "
             "their printouts (the same aggregates: each engine's deepest cell-referenced lambda with its table and source "
             "row, its floor, the deciding lines and the pooled counts); the fourth review's and its verification's reports "
             "and the third round's report, which name them; version 3's two files at ef5e14e, its JSON digested to pin what "
             "version 4 keeps; the decision sheet, the build-step-2 plan (its WP5, C5 and decision-64 lines, its cam lines), "
             "its amendments and hand-offs; and the plant code (engine_env.py's demand inputs and its extremes speed profile). "
             "No EPA table was opened, no row value was read, and nothing was compared with any model"),
            ("the session of 23 October 2026 that corrected version 4 after its fifth review and wrote decision 76 in, which "
             "also re-ran steps 6 and 7 only and computed no number from EPA data: version 4's two files, its generator and "
             "their printouts (the same aggregates: each engine's deepest cell-referenced lambda with its table and source "
             "row, its floor, the deciding lines and the pooled counts); the fifth review's and its verification's reports, "
             "which quote them; version 3's JSON at ef5e14e, to compare; the decision sheet, the build-step-2 plan (its "
             "sections 7.4-7.7, and the lines a search of it for the cap and the time step printed, its decision-62 and "
             "decision-64 rows among them), its amendments and hand-offs (the lines the same search printed, the "
             "amendments' decision-64 row among them); and the plant code "
             "(engine_env.py's road generators, its extremes speed profile and its note on the time step). No EPA table was "
             "opened, no row value was read, and nothing was compared with any model"),
            ("the session of 23 October 2026 that corrected version 4 after its sixth review, which also re-ran steps 6 and 7 "
             "only and computed no number from EPA data: version 4's two files, its generator and their printouts (the same "
             "aggregates: each engine's deepest cell-referenced lambda with its table and source row, its floor, the deciding "
             "lines and the pooled counts); the sixth review's and its verification's reports, which quote them; version 3's "
             "JSON at ef5e14e, to compare; the decision sheet; the lines a search of the build-step-2 plan and its amendments "
             "for censored lambda and for C5 printed (among them the plan's line 524, which prints the Honda's lambda minimum, "
             "and its E8 row, which prints each engine's count of Final rows), and the hand-offs' items; thresholds/split.py's "
             "loader and classifier; and the plant code (engine_env.py's gearbox, its CVT law and its road stream's seed). No "
             "EPA table was opened, no row value was read, and nothing was compared with any model"),
            ("the session of 23 October 2026 that corrected version 4 after its seventh review, which also re-ran steps 6 "
             "and 7 only and computed no number from EPA data: version 4's two files, its generator and their printouts "
             "(the same aggregates: each engine's deepest cell-referenced lambda with its table and source row, its floor, "
             "the deciding lines and the pooled counts); the seventh review's report and the sixth correction's, which "
             "quote them; version 3's two files at ef5e14e, to compare their numbers; the decision sheet, and the header "
             "and row numbers of the team's dated copy of its section H on the Desktop; the lines a search of the "
             "build-step-2 plan and its amendments for the values of decisions 54 and 57 printed (among them the plan's "
             "line 524, which prints the Honda's lambda minimum), the amendments' C1, whose lines print HD1's barometer "
             "and its sweep as the plan states them, and F3, and the hand-offs' commit A item 12; and the plant code "
             "(engine_env.py's extremes speed profile). No EPA table was opened, no row value was read, and nothing was "
             "compared with any model"),
        ],
        "version_4": {
            "written": ("22 October 2026, build step 2's WP2, by engine_thresholds.py --build-only from the outputs of steps 1-5 as "
                        "version 3 left them, after the plant changes of WP1 (4461a91) and before any fit; corrected seven times on "
                        "23 October 2026, after each of its seven reviews, by the same command, still before any fit; "
                        "decisions 73 and 74, which the first review raised, written into section H between the first two, "
                        "decision 75, which the fourth raised, with the fourth, and decision 76, which the fifth raised, with "
                        "the fifth, each as a rule into the contract by the same command, still before any fit"),
            "follows": (f"{SH}'s reading, as WP1 did (docs/build_step_2/HANDOFFS.md, commit A item 1): every decision of 39-76 but 66, "
                        "which the amendments dropped, adopted under Ghassan's delegation, the first fit waiting for both columns; "
                        "73-76 were raised by the reviews of version 4 two days after the delegation and written in by the agents "
                        "writing it, as 39-72 were on 22 October, and section H adopts them the same way (version 4's fourth review; "
                        "its second had marked 73 and 74 pending Ghassan's own answer), as it does the readings the agents added "
                        "on 23 October to decisions 54, 59 and 64; Ghassan's column records the delegation, not an answer of his "
                        "to these rows or readings, and since the fifth review each of their cells says so ('adopted by the "
                        "agents 23 Oct, not yet seen'), so the first fit waits for Jad's column and for Ghassan's own answer to "
                        "these rows and readings, as the sheet's note of 23 October asks of both of them (version 4's sixth "
                        "review); not docs/build_step_2/AMENDMENTS.md A1's "
                        "check, 'WP2 starts only when the G1 and G2 columns are filled', since Jad's column is empty"),
            "decision": (f"39 ({SH}, {ADOPTED_H}); docs/build_step_2/AMENDMENTS.md A1-A3, E1-E6, F1-F3 and its section 3 word "
                         f"39-71; the text of 73-76 is their rows of {SH} (23 October 2026), which the amendments do not hold; "
                         "decision 57's details are docs/build_step_2/PLAN.md decision 57's and its sections 6.2-6.4's"),
            "rules": {"39(a)": "model_form.in_sample_rules.e8", "39(b)": "model_form.neutral_action_identity",
                      "39(c), 70, 40": "cars C5 statistic and threshold", "49": "model_form.in_sample_rules.form_per_engine",
                      "54": ("conventions.lambda_missing, spark_sentinel, held_out_counts, censored; version 4's readings: "
                             "lambda_missing (E8's dl), spark_sentinel (E8's ds, D1's spark), statistic_details.e8_subsets "
                             "(each subset's minimum, after the fifth review), and, after the sixth, spark_sentinel (an empty "
                             "spark), lambda_missing (an HD1 row with an empty bank) and censored (E8's list); rows E8 statistic "
                             "and population"),
                      "55": "model_form.in_sample_rules.no_calibration_line",
                      "57": "conventions.statistic_details (D1's cam and the worst line included); rows D1 and E8 statistic; perturbations_E6 row 12",
                      "59": ("perturbations_E6 rows 1, 2, 3, 5, 7, 9 and 12 (row 12: D1's kappa, version 4's reading); "
                             "tests_lists; on_failure.perturbation"),
                      "64": "cars C5 redraw (draw, stream, recheck, no_passing_car, rule_0); on_failure.rule; order_of_work[2] and [3]",
                      "71": "rows L1 basis; order_of_work[2]; model_form.in_sample_rules.r_in_sample",
                      "73": ("cars C5 statistic and steps (range, share, dt, gated_step, outcome, thin, steady_acceleration and "
                             "transfer_row included); on_failure.rule"),
                      "74": "cars C5 redraw (at_cap, no_passing_car); on_failure.rule",
                      "75": "cars C5 redraw (slot, redraw, extent, cap, disclosed); on_failure.rule; order_of_work[2] and [3]",
                      "76": ("cars C5 redraw (stream and stream_tag, cap and cap_redraws, discards and discards_max, at_cap, "
                             "rule_0); on_failure.rule; order_of_work[2] and [3]; REDRAW_CAP, REDRAW_DISCARDS and "
                             "REDRAW_STREAM_TAG in thresholds/contract.py")},
            "moved": {
                "statistics_and_inputs": ("C5's threshold (decisions 70 and 40), steps (decision 73) and re-check margin, read "
                                          "from E1a's worst deciding line (decision 64); E6 rows 1, 2, 3, 7, 9 and 12 and "
                                          "the d rows' probe (decision 59); the in-sample stage's form criterion (decisions 39(a), 49, "
                                          "55) and its R, L1's untightened (decision 71); the inputs of the rows version 3 did not "
                                          "treat (decision 54: lambda 1.00 for a fired row "
                                          "without lambda, in no lambda band; the model ECU's spark for a sentinel row, in no fit; "
                                          "censored lambda on the calibration Final rows, with E8's list of the censored held-out "
                                          "Final rows, reported and not gated; and version 4's readings of it, a "
                                          "sentinel row's spark in D1, E8's dl without the lambda-less rows and ds without the "
                                          "sentinel rows, each reported with them too, an empty spark read as the sentinel and an "
                                          "HD1 row with an empty bank as a row without lambda); E6 row 9's rich slope probed under every "
                                          "form (decision 59, as amendment E3 is read); the details version 3 left open (decision "
                                          "57: D1's pre-scan, bisection and nearer bound, D1 also without its unreachable rows, "
                                          "form D's cam at the inverted MAP; E8's EPA lambda unsnapped, the snapped E8 reported, "
                                          "P's slope at a zero shift and its extrapolation, the tightening's sign; the worst line "
                                          "and its u); D1's and E8's statistic text, which points at them (rows, thresholds)"),
                "label_and_on_failure_rules": ("the refit rows 1, 3 and 7 label no exclusion and calibrate before the held-out run; "
                                               "the Tests lists and their counting rule; row 12's order of labels, and D1's kappa "
                                               "under it the larger of its two readings'; row 2's miss a "
                                               "finding, not a stop (decision 59); C5's slot shared by the four cars, a redraw "
                                               "for every car passing every test of a first draw, the cap counted over all cars "
                                               "(decision 75), a candidate filling its slot's recorded extent (decision 75); every "
                                               "slot at the cap keeping its last accepted climb, flagged on each car on which it "
                                               "fails, and a car with no passing climb gear-sensitive when a slot is flagged on it "
                                               "and thinly checked when a climb is thin on it (decisions 64, 73, 74); C5's outcome on a car one of "
                                               "three exclusive cases, fails, thinly checked or passes, a climb with no gated step on a car not "
                                               "passing, and one gated on fewer than half its steps flagged thin, never passed, and failing C5 "
                                               "when a gated margin fails (decision 73); the cap, "
                                               f"{REDRAW_CAP} redraws per slot, and the bound of {REDRAW_DISCARDS} discarded "
                                               "candidates, fixed here, and each slot's stream derived from the roads' own seed by "
                                               "a derivation fixed here (decision 76); the locked climb's transfer row gating nothing (decisions 34 and 44, as "
                                               "read); E8 with a subset of fewer than "
                                               f"{E8_MIN_ROWS} rows having no statistic, which drops the engine (decision 54, "
                                               "as read; named in on_failure.d's untested after the seventh review, the d entries of "
                                               "thresholds keeping version 3's on_fail, which the generator's digests hold); L1's "
                                               "tightening plant (decision 71)"),
                "populations": ("one that version 3 named: E8's, whose dl is taken over the held-out Final rows that publish "
                                "a lambda and ds over those that publish a spark, each a subset of version 3's held-out High Load "
                                f"Final rows and each needing at least {E8_MIN_ROWS} rows (version 4's reading of decision 54); and "
                                "one written where version 3 named none, C5's steps (decision 73, with a scored climb's extent, "
                                "its time step and its gated steps), which narrows docs/build_step_2/PLAN.md section 7.4's "
                                "reading of version 3, 'every scored-climb step'"),
            },
            "citations": ("every code citation moved to the lines of the tree version 4 was written on, most with the function or "
                          f"record beside it (results/ENGINE_THRESHOLDS.md section 13 lists the moves); version 3's lines are "
                          f"{V3_TREE}'s. Step 7 checks every citation into PLANT_CODE (fingerprint.PLANT_CODE) and engine_specs/, "
                          "which amendment B5 freezes after commit A, against a text its line must hold "
                          "(thresholds/document.py CODE_CITES), so a tree whose lines moved stops the generator, and every "
                          f"version-3 line of section 13's table against {V3_TREE}'s tree (V3_CITES); each citation of REFERENCES.md, "
                          "a document WP7 edits after the first fit, carries its row's own text beside the line, and each "
                          "citation of the decision sheet, results/VALIDATION_DECISIONS.md, is pinned to its row's text "
                          "(SHEET_CITES, after version 4's fourth review), so a sheet line that moves stops the generator. Step 7 also "
                          "resolves every other file:line of the .md and the JSON (amendment A3's scan): a file of the repository, "
                          "read as written or under results/, that holds the cited lines; a file the .md's Appendix A quotes from "
                          "outside the repository (CATALOGUE.md, fe_out/); or an EPA table, by its existence alone, never opened. "
                          "The docstrings of steps 3 and 5 (thresholds/b58_propagation.py, thresholds/ecu_shift.py) keep version "
                          "3's engine_env.py lines on purpose: those steps did not run again, and their sha256 in generators is "
                          "that of the code that wrote the outputs version 4 reads"),
            "unchanged": ("every R, split, population, statistic, convention and label rule not named in rules; the per-threshold "
                          "values of thresholds (engine, row, kind, part, R, unit), every entry of thresholds but C5's, D1's and "
                          "E8's, D1's and E8's but for their statistic, C5's but for its statistic and on_fail, and the engines "
                          "section are version 3's, checked by the generator against digests of version 3's"),
            "schema": ("4: new keys hold the rules version 3 had no field for (model_form.in_sample_rules and "
                       "neutral_action_identity, the four conventions of decision 54 and decision 57's statistic_details, tests_lists, "
                       "C5's steps, threshold and redraw in cars[7], decisions 39, 40, 49, 54, 55, 57, 59, 64, 70, 71, 73, 74, 75 and "
                       "76, this record); every key of version 3 is kept with "
                       "its meaning, and the generator checks the set of key paths, list entries included. That check sees "
                       "keys, not the strings a list holds: open_for_the_team grew from one entry to four, seen_before_writing "
                       "gained one entry for each of version 4's sessions, and order_of_work's entries were reworded, none of "
                       "which it covers. The contract's own numbering: not "
                       "the fingerprint's schema 4 of decisions 27-28 and 47"),
            "plant_values": PV,
            "not_contract_rules": {"69": "the Ford's fuel in use: each row runs on its own table's fuel (conventions.fuel)",
                                   "72": "the Mazda's stroke: the contract names no stroke",
                                   "65": ("reads the contract as version 3 wrote it (order_of_work puts the roads and the L1 "
                                          "and E8 tightenings before the held-out run), and adds no text"),
                                   "58": ("held-out rows outside the calibration MAP range, flagged per row and every statistic "
                                          "also reported restricted to the calibration coverage beside it, never relabelled: a "
                                          "reporting procedure of the validation script, which reads this contract's "
                                          "engines.<id>.coverage.calibration_fired and .calibration_hot (per 20 kPa band of "
                                          "MAP); decision 39(d) does not name it among the rules this contract "
                                          "takes, and it moves no R, population, statistic or label")},
            "reviewed": ("a first adversarial review of 23 October 2026, before commit, found six must-fix items, all corrected: C5's "
                         "step population left to the roads step (now decisions 73 and 74: cars C5 steps and redraw), C5's threshold where "
                         "the box takes no torque decision (cars C5 threshold.no_decision), the .md's misreading of 39(c), an "
                         "unqualified 'no statistic moved', decision 58 said to add nothing, and the B58's clip printed as literals "
                         "(now version_4.plant_values). A second, the same day, found two, both corrected: the .md's list of what "
                         "moved was incomplete (now version_4.moved), and C5's barred downshift could be read two ways, which give "
                         "opposite answers on docs/build_step_2/AMENDMENTS.md F3's CX-9 (now cars C5 threshold.rpm_bar); its "
                         "should-fix items were all taken. A third, the same day, found two, both corrected: under form C, E6 row 9 "
                         "gave the rich slope only its fit's sigma, so whether E4a and E4b are excluded for it was undefined (now "
                         "the probe under every form, perturbations_E6 row 9), and decision 57 was said to add no text, when it "
                         "adopts details version 3 left open, E8's snap among them (now conventions.statistic_details); its "
                         "should-fix items were all taken. A fourth, the same day, found one: decisions 64 and 74 never said "
                         "whether a climb slot is one car's or all four cars', so the redraw, the cap and decision 74's slot "
                         "could not be applied as written (now decision 75, slots shared by the four cars: cars C5 redraw); "
                         "its fifteen should-fix items were all taken. A fifth, the same day, found three: section 7 said that "
                         "nothing set after the first fit changes after the held-out run, when section 5 redraws failing "
                         "climbs then (now said: the redraw is the one change, and the tightenings stay); the redraw cap had "
                         "no value and no rule for one, left to a choice after the first fit (now decision 76, fixed here: "
                         "cars C5 redraw.cap and discards); and E8's subsets had no declared outcome when one is short (now "
                         "conventions.statistic_details.e8_subsets: E8 has no statistic). Of its eight should-fix items seven "
                         "were taken in full and one in its lesser form: decision 73 keeps its transitions, with a thin flag "
                         "(cars C5 steps.thin, steady_acceleration). A sixth, the same day, found two: the .md's sections 8 and "
                         "13 and this file said that the first fit waits for Jad's column alone, when the sheet asks Jad and "
                         "Ghassan both to answer decisions 73-76 and the readings of 23 October before it (now open_for_the_team "
                         "and version_4.follows); and the .md said that every number version 4 adds counts entries or comes "
                         "from the plant code, when it adds four rule constants, three of them DESIGN, chosen from no data (now named, the thin share "
                         "labelled DESIGN: cars C5 steps.thin). Of its eleven should-fix items ten were taken (cars C5 steps "
                         "gated_step, thin and steady_acceleration, threshold.no_decision, redraw stream, stream_tag, redraw, "
                         "extent, at_cap, no_passing_car and rule_0; conventions lambda_missing, spark_sentinel and censored); "
                         "the eleventh, the team's dated copy of the sheet, is left to the commit step "
                         "(results/ENGINE_THRESHOLDS.md section 13). A seventh, the same day, found two: a thin climb was said "
                         "both to fail C5 at a gated step and to neither pass nor fail it, so a slot at the cap that keeps a "
                         "thin climb failing on a car had opposite answers (now three exclusive cases: cars C5 steps.outcome, "
                         "thin, redraw.redraw, at_cap and no_passing_car, on_failure.rule); and the .md's list of the numbers "
                         "version 4 adds left out the values decisions 54 and 57 state (now listed, and checked by step 7 "
                         "against conventions). Of its eleven should-fix items six were taken (on_failure.d; conventions "
                         "spark_sentinel and censored; the .md's section 2.2; the sheet's row 73; the Desktop copy of the "
                         "sheet, open_for_the_team[0]), and five are left for a later version before any fit "
                         "(open_for_the_team[3])"),
        },
        "generators": {"entry_point": "python engine_thresholds.py",
                       "sha256": dict(generators),
                       "hash_rule": "sha256 of each file with CRLF read as LF (thresholds/common.sha_text)"},
        "generator_outputs": common.rel(common.OUT_DIR),
        "generator_run": {"python": py, "numpy": npv, "platform": run.get("platform", "unrecorded"),
                          "timings": (f"{common.rel(os.path.join(common.OUT_DIR, 'run.json'))}, not here: no file the contract "
                                      "hashes or writes holds a wall-clock time, so a re-run on one platform gives this file "
                                      "back byte for byte")},
        "generator_inputs_sha256": inputs,
        "epa_tables_sha256": split["sha256_inputs"],
    }

    ns = dict(MEI=MEI, R1_K=R1_K, n_shares=n_shares, B=B, B_FRAC=B_FRAC, LINEAR=LINEAR, RSS=RSS, R=R, R_V2=R_V2,
              WORTH_B=WORTH_B, WORTH_B_V2=WORTH_B_V2, G_K=G_K, GAS_PER_PCT=GAS_PER_PCT, FLOW_PER_PCT=FLOW_PER_PCT,
              HOUSE_PER_PCT_B58=HOUSE_PER_PCT_B58, HOUSE_PER_PCT_BOUND=HOUSE_PER_PCT_BOUND,
              HOUSE_PER_PCT_FLOW=HOUSE_PER_PCT_FLOW, F_STAR=F_STAR, SLOPE=SLOPE, SLOPE_10=SLOPE_10, slopes=slopes,
              RESP_L=RESP_L, RESP_S=RESP_S, RESP_L_FIX=RESP_L_FIX, RESP_S_FIX=RESP_S_FIX, W=W, FUEL=FUEL,
              FUEL_BY_TABLE=FUEL_BY_TABLE, LAM_FLOOR=LAM_FLOOR, U_ETA=U_ETA, U_RAD=U_RAD, U_C3_TORQUE=U_C3_TORQUE,
              U_C3_FUEL=U_C3_FUEL, E6_AFR=E6_AFR, D3=D3, K3=K3, FIX=FIX, interp=interp, pair=pair, cuts=cuts)
    return contract, ns


def report(contract, ns):
    """What the .md quotes, printed (build_contract.py's printout of version 2, with the budget of
    decision 38)."""
    R, B, MEI_ = ns["R"], ns["B"], ns["MEI"]
    print(f"b {B:.4f}  parts {len(PARTS)}  linear {ns['LINEAR']:.3f} ({ns['LINEAR'] / MEI_:.2f} MEI)  rss {ns['RSS']:.3f} ({ns['RSS'] / MEI_:.3f} MEI)")
    print(f"G {ns['G_K']:.3f} K; gas/% {ns['GAS_PER_PCT']:.4f}; flow/% {ns['FLOW_PER_PCT']:.4f}; housing/% B58 {ns['HOUSE_PER_PCT_B58']:.4f}; "
          f"bound {ns['HOUSE_PER_PCT_BOUND']:.4f} (f* {ns['F_STAR']:.4f}); flow-only bound {ns['HOUSE_PER_PCT_FLOW']:.4f} K/%")
    for k, v in R.items():
        print(f"  R {k:4s} {v}")
    print("  worth b:", ns["WORTH_B"], " version 2 (b = MEI/5):", ns["R_V2"], ns["WORTH_B_V2"])
    print("knee slope max", ns["SLOPE"], "at 10 K", ns["SLOPE_10"])
    print("E8 K3 lambda", [(x, round(100 * y, 1)) for x, y in ns["RESP_L"]])
    print("E8 K3 spark ", [(x, round(100 * y, 1)) for x, y in ns["RESP_S"]])
    print("E8 fixed lambda", [(x, round(100 * y, 1)) for x, y in ns["RESP_L_FIX"]])
    print("E8 fixed spark ", [(x, round(100 * y, 1)) for x, y in ns["RESP_S_FIX"]])
    print("E8 worth b", ns["W"])
    print("C3 u_eta %.4f u_rad %.4f u_torque %.4f u_fuel %.4f" % (ns["U_ETA"], ns["U_RAD"], ns["U_C3_TORQUE"], ns["U_C3_FUEL"]))
    print("AFR", {e: ns["FUEL"][e]["afr_st"] for e in common.EPA_ENGINES}, "E6 AFR", {k: round(v, 5) for k, v in ns["E6_AFR"].items()})
    print("fuel by table", {e: {fn: v["fuel_report"] for fn, v in t.items()} for e, t in ns["FUEL_BY_TABLE"].items()})
    print("lambda floors", ns["LAM_FLOOR"])
    print("D3 files", len(ns["D3"]), ns["D3"][0]["test"], ns["D3"][-1]["test"])
    flat = contract["thresholds"]
    print("thresholds", len(flat), "b58 rows", [r["row"] for r in flat if r["engine"] == "b58"])
    for e in common.EPA_ENGINES:
        s = contract["engines"][e]
        print(e, "deciding", s["deciding_lines"], "pooled", s["pooled_counts"])


def dumps(contract):
    """The JSON text exactly as it is written (indent 1, UTF-8, a final newline)."""
    return json.dumps(contract, indent=1, ensure_ascii=False) + "\n"
