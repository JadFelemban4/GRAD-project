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
                      "0.686 K/kPa at fixed spark), and the agents' boost lever acts at fixed spark (engine_env.py:982, :1004); EPA has "
                      "no spark sweeps, so THE BOOST LEVER IS UNTESTED for every engine and is declared so"),
             basis="no gate"),
        dict(id="D1", kind="d", part="P1", quantity="the exhaust flow at the DEMANDED torque",
             statistic=("per fired held-out row with a meter reading: invert MAP so that the model delivers EPA's measured torque "
                        "(bisection over 20-400 kPa) at EPA's speed, intake temperature, coolant and the row's lambda convention, "
                        "with spark = EPA's spark + s*(MAP - MAP_EPA), s the engine's calibrated ECU's dspark/dMAP at the row (central "
                        "difference +-2 kPa of base_spark), as the environment's ECU responds; delta_D = fuel_model/fuel_meter - 1 and "
                        "e_D = TIT_model - TIT_EPA there; D1 = mean |delta_D| over the fired held-out rows (pooled)"),
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
                    f"measured before any held-out statistic, is larger, R = b/that slope (a tightening only)")),
        dict(id="E8", kind="d", part="P4", quantity="the baseline ECU's strategy at high load: its lambda and spark at the held-out Final rows",
             statistic=("dl = mean signed (model ECU lambda - EPA lambda, cell-referenced) and ds = mean signed (model ECU spark - EPA "
                        "spark) over the held-out High Load Final rows, the ECU evaluated at the row's speed and MAP with a 30 s dwell, "
                        "no knock retard and EPA's intake temperature; E8 = |P_lambda(dl)| + |P_spark(ds)|, P the measured relative "
                        "change of the hand-written head-start pair (current-grade minus reactive) under K3 for an ECU shift of that "
                        f"size (B58 locked climb, piecewise linear through {common.rel(common.ECU_DIR)}/k3_*.json, both damage readings, the "
                        "larger; the same shifts are re-run on the B58 on decision 34's roads before any held-out statistic, and at each "
                        "shift the larger response is used: a tightening only)"),
             population="held-out High Load Final rows", R=R["E8"], unit="% of the head-start pair", governs=DPART("P4"),
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
             statistic="on every scored climb, |demand / kickdown threshold - 1| (SHIFT_LOAD*T_wot, or the CVT law's lambda*T_wot)",
             R=R["E1a"], unit="% (the demand must sit MORE than max(R_E1a, |E1a| + 2u_val) from the threshold)",
             basis="a torque error the validation accepts cannot change the gear a scored climb is driven in; the B58, which has no E1a, uses R_E1a"),
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

    E6 = [
        dict(n=1, constant="the lambda convention", band="as published instead of cell-referenced: the offset lambda_ref - 1 (Mazda 0.000, Honda -0.010, Ford Cell 9 -0.020, HD1 0.000)", refit=True,
             must_show="every row's change; the in-use hot TIT at lambda 1, the air and tau"),
        dict(n=2, constant="AFR_st (calibration air and plant fuel together)", band=f"the table's own fuel, {FUEL['mazda_25t']['afr_st']}-{FUEL['honda_l15b7']['afr_st']} (the convention) -> 14.7 (plant.py:43)", refit=True,
             must_show=(f"the air {100 * E6_AFR['air_rel']:+.2f} %, the exhaust flow {100 * E6_AFR['exhaust_flow_rel']:+.2f} %, tau "
                        f"{100 * E6_AFR['tau_rel']:+.2f} % (B58 f), the housing level {E6_AFR['housing_b58_k']:+.2f} K (B58 f) or at most "
                        f"{E6_AFR['housing_bound_k']:+.2f} K (f bounded); E2, D1 and L0 must NOT move (excluded for AFR_st by construction)")),
        dict(n=3, constant="LHV, in plant.py:42 AND thermal.py:245 together", band="the table's own fuel, 42.898-42.908 MJ/kg (the convention) -> 44.0", refit=True,
             must_show="every row's change; the in-use heat release per gram of fuel; the coolant and oil heat"),
        dict(n=4, constant="c_turb, ua_gas_turb, ua_turb_amb", band="x0.75 and x1.333 each, PROPOSED BY THIS CONTRACT (X1 drew only the heat capacity on that range, PREREGISTRATION_X1.md:119)", refit=False,
             must_show="tau moves by construction; no E-row can see them: excluded by construction; report tau, the 850 C baseline peak and decision 34's ceiling at each end, flagged if the ceiling falls below 2 MEI"),
        dict(n=5, constant="the back-pressure law", band="+- its fit's standard uncertainty (reported); the visibility probe is sized by consequence: the change worth R1 on the engine's own in-use housing equivalent at its locked-climb cell (level rows) or worth b on d (d rows), else +-10 %", refit=False, must_show="E1a, E3a and L0 must move under the probe"),
        dict(n=6, constant="UA_PORT", band="+- its fit's standard uncertainty (reported); the visibility probe is sized by consequence, as row 5", refit=False,
             must_show="E3a, E3b, E4a and L0 must move under the probe"),
        dict(n=7, constant="the knock scale (KI = 1 assumed at the High Load Final spark)", band="KI 0.90 and 1.10 (decision 21's +-0.10 KI)", refit=True,
             must_show="no E-row can see it; report the knock term's share of the baseline's damage and d both ways"),
        dict(n=8, constant="the crank-angle step", band="0.25 -> 0.125 deg", refit=False, must_show="u_num"),
        dict(n=9, constant="the other ASSUMED cycle constants (conrod, IVC, EVO, t_head, port pickup, t_residual, cp_exh, any burn constant not fitted)",
             band="the bracket EPA's calculated valve channels give where one exists; else the change worth R1 or b, else +-10 % (+-10 crank degrees for IVC and EVO)", refit=False,
             must_show="the rows the calibration says each one sets must move; report the error worth R1 and worth b"),
        dict(n=10, constant="the driveline efficiency, 0.92", band="0.86-0.98 (the CX-9's apparent efficiency on D3, seen); the Accord's 0.78 UNVERIFIED", refit=False,
             must_show=f"C3 moves; an efficiency error is a torque bias of the same fraction: worth R1 at {R['E1a']} %, worth b at {R['S1b']} %"),
        dict(n=11, constant="the charge temperature (E rows are fed EPA's measured value)", band="+-6.3 K (the B58's input uncertainty, DRIVE_C_RULE_NUMBERS.txt:56)", refit=False,
             must_show="report the hot TIT and the test roads' hand-written cuts"),
        dict(n=12, constant="the lambda snap (rows within 0.02 of lambda_ref run at 1.00)", band="every row at lambda_meas - (lambda_ref - 1), no snap", refit=False,
             must_show="E3a, E5, D1 and L0 both ways; each labelled by the worse of the two (review finding 11)"),
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
        "rule": "a climb that fails C5 is redrawn",
        "descriptive": "reported, never gating",
        "perturbation": "labels (excluded for a constant) and preregistered sensitivity rows; never a drop",
        "refit": ("no refit after any held-out statistic of an engine has been computed; a coding defect, a disagreement with a "
                  "specification committed before the comparison ran, may be fixed and the comparison re-run: both results reported, "
                  "the second limited at best"),
        "freeze": "no R, split, population, statistic, convention or form rule changes after any fit runs (rule 0); a change after that is a new contract, disclosed, every result under both",
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

    contract = {
        "_generated": ("the machine-readable half of results/ENGINE_THRESHOLDS.md (version 3, 21 October 2026: version 2 with "
                       f"decisions 36-38 of {SG} applied), written by engine_thresholds.py before any calibration of the three EPA engines"),
        "schema": 3,
        "status": "binds from its first commit on GRA-test, which must precede calibrate_epa.py; every script that reads it records its sha256",
        "decisions": {"35": "thresholds from the MEI, committed before calibrating", "28": "table gates; score on the exact cycle; backends as fingerprint fields",
                      "33": "K3 knee per engine; 850 C as a sensitivity row", "34": "the test roads", "26": "one verdict per engine per horizon; the collapse as a declared cross-plant comparison",
                      "27": "three arms per engine, two horizons", "30": "seeds per arm from the measured rate and window, target >= 20",
                      "5": "MEI 5.43 points of cut", "3": "R1 10 K turbine-equivalent", "4": "label rules, k = 2",
                      "36": (f"an untested d row with a statistic enters as a preregistered band ((|E| + 2u)/R)*b and the verdict inside it "
                             f"reads MODEL-LIMITED; a row with no statistic drops the engine ({SG}, adopted 21 October 2026)"),
                      "37": f"the collapse test's equivalence margin is the MEI, {MEI} points ({SG}, adopted 21 October 2026)",
                      "38": f"b = MEI/6 = {MEI / 6:.3f} points per part, for six parts; every d-row R scales by 5/6 ({SG}, adopted 21 October 2026)"},
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
            "fuel": "each table's own fuel: LHV and AFR_st from its fuel report's analysis (epa_engine.json alpha_fuel of that FTAG; AFR_st from the carbon weight fraction, hydrogen the balance, oxygen-free); the plant and thermal.py must take them per engine; 44.0 MJ/kg and 14.7 are E6 rows 2-3",
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
            "in_sample_stage": "every gating statistic computed on the calibration lines with the same definitions (fit residuals, never labelled); the form is the first of A, A+B, A+B+C, A+B+C+D at which every one satisfies |E_cal| <= R; if none does, A+B+C+D, with the failing statistics reported; then the form and constants are frozen (sha256) and the held-out statistics are computed once",
            "plant_in_use": "the subset fit (calibration rows only) IS the plant that trains and scores; its coverage is the calibration rows' (engines.<id>.coverage.calibration_*), and the scored climbs must lie inside it (review finding 27, choice b)",
            "lambda_clip_floor": "per engine min(0.70, the engine's deepest EPA lambda on the cell-referenced convention - 0.01), so the neutral action stays neutral (mistake 10; engine_env.py:1006 clips at 0.70)",
        },
        "split_rule": "version 2: lines are the union of an engine's tables' nominal speeds (50 rpm merges); eligible lines are interior in the union, the steady lines and the high-load lines; positions o+1, o+4, ... held out, o chosen by structure (>= 2 held-out lines with >= 3 holds where possible; then most E4b-usable enriched rows; most rows; lowest o); a line goes with all its rows",
        "calibration_may_use": "every row of a non-held-out line (High Load Initial only for the WOT torque curve, labelled a transient peak); ALPHA's curves only at nodes whose measured source row is a calibration row; never the ALPHA fuel map, the Tier 3 / LEV III packages, the Steady State with Transmission sheets, the SAE 2018-01-0319 dataset, or any D3 file",
        "order_of_work": ["commit this contract", "calibrate each engine on its calibration rows (calibrate_epa.py, committed before it runs), the in-sample stage included; freeze",
                          "draw decision 34's roads on the frozen plants; on them measure the hand-written preview pair's knee-shift slope (L1's tightening) and re-run the B58 ECU shifts (E8's tightening)",
                          "compute every held-out statistic once; label; decide (section 7)", "build and gate the tables (S1; S2a)", "write and commit the preregistration (the backend rule, the bands, the equivalence margin)",
                          "S2b pilots on the tables; train"],
        "engines": eng_out,
        "rows": ROWS, "cars": CARS, "c3_segments": SEG, "d3_files_c3": D3, "table_gates": TABLE, "perturbations_E6": E6,
        "on_failure": FAIL, "thresholds": flat,
        "open_for_the_team": [f"Jad's column of decisions 36-38 ({SG}) is open; an answer that differs, given before the first fit, "
                              "is applied before it (this generator, then a new version of this file)"],
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
        ],
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
