"""split.py -- step 1 of engine_thresholds.py: the held-out split of results/ENGINE_THRESHOLDS.md,
from the EPA tables' STRUCTURE only.

Reads data/engines/<id>/*.csv (epa_map.py's tables). Imports no model and computes no
model-versus-EPA error. A row's speed, manifold pressure, BMEP, lambda, intake and coolant
temperature, its source row and whether it carries a fuel-meter value are used only to NAME rows
(which line, which population), to count them and to state the data's coverage. No torque,
fuel-flow or turbine-inlet-temperature value is read as a number. Writes
results/ENGINE_THRESHOLDS/split.json.

THE RULE (contract version 2, fixed before any calibration; version 1 ran it per Ford cell):
  1. A row's nominal speed is its measured speed rounded to the nearest 50 rpm (every row lies within
     25 rpm of it; asserted).
  2. An engine's LINES are the nominal speeds of ALL its tables together (both Ford test cells, steady
     and high load), and speeds no more than 50 rpm apart are one line (Ford 1750/1800 and 2200/2250;
     Honda 1700/1750/1800). A line is held out in every table at once, so no held-out speed is a
     calibration speed in another cell or table (review of 21 October, findings 4 and 22).
  3. A line is ELIGIBLE only if it is interior in the engine's union of lines, in its steady lines (if it
     has steady rows) and in its high-load lines (if it has holds): never the first or the last, so every
     held-out population interpolates in rpm (mistake 6; findings 23 and 34).
  4. Among the eligible lines in ascending order, the lines at positions o+1, o+4, o+7, ... are held out.
     The offset o in {0, 1, 2} is chosen per engine by STRUCTURE, in this order (finding 6):
       a. at least 2 held-out lines with at least 3 high-load holds (required where any offset allows it);
       b. the most enriched hot rows usable by E4b (on held-out lines with >= 3 boosted lambda~1 rows);
       c. the most held-out rows;  d. the lowest offset.
     Every offset's counts are printed and kept, so the choice can be checked.
  5. With a line go all its rows: steady rows, and high-load holds (Initial and Final are one hold, one
     spreadsheet row, epa_map.py:20-21).

POPULATIONS (lambda as published; for the Ford HD1 the mean of its two banks):
  * lambda_ref: the median lambda of a steady table's rows at 2-8 bar BMEP; a high-load hold takes its
    cell's (the Ford's holds are HD1's)
  * lambda~1: |lambda - lambda_ref| <= 0.02;  enriched: lambda <= lambda_ref - 0.05
  * the hot MAP floor: the lowest manifold pressure of any high-load window of the engine
  * gating statistics use steady rows and High Load FINAL rows only; High Load Initial rows are a thermal
    and sensor transient (logs/epa/README.md:101-104) and carry no fuel meter, so they are descriptive
    (finding 21)
  * a line decides a statistic only with >= 3 clusters in its population (a steady row is a cluster, a
    hold is a cluster; finding 34)
  * L0 and L1 use the hot lambda~1 rows with a fuel-meter reading (finding 16: e from the hot lambda~1 rows)
  * coverage is printed for all rows and for the calibration rows (the plant in use is the subset fit,
    finding 27), per 20 kPa band of manifold pressure (finding 31)
"""
import csv
import os
import statistics as st
from collections import defaultdict

from thresholds import common

ENG = {
    "mazda_25t": dict(steady=["epa_steady.csv"], hli="epa_highload_initial.csv", hlf="epa_highload_final.csv"),
    "honda_l15b7": dict(steady=["epa_steady.csv"], hli="epa_highload_initial.csv", hlf="epa_highload_final.csv"),
    "ford_27tt": dict(steady=["epa_steady_cell9.csv", "epa_steady_hd1.csv"],
                      hli="epa_highload_initial_hd1.csv", hlf="epa_highload_final_hd1.csv"),
}
LAM_BAND, LAM_ENR, MAP_SPLIT, MERGE_RPM, MIN_CLUSTERS = 0.02, 0.05, 100.0, 50, 3
NOMINAL_RPM = 50         # a row's nominal speed: its speed to the nearest 50 rpm
FIRED_BMEP = 2.0         # bar
LAM_REF_BMEP = (2.0, 8.0)  # bar: the rows whose median lambda is a cell's closed-loop reading
OFF_REF = 0.005          # a hot lambda~1 row more than this from lambda_ref is moved by the snap
MAP_BAND = 20.0          # coverage bands of manifold pressure, kPa
TOL = 1e-9               # readings are printed to 0.01 (0.005 for the Ford HD1 bank mean)
OUT = os.path.join(common.OUT_DIR, "split.json")


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return float("nan")


def ok(x):
    return x == x


def load(eng, fn):
    with open(os.path.join(common.ENGINE_DIR, eng, fn), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def lam(r):
    if "exhaust_lambda" in r:
        return f(r["exhaust_lambda"])
    return 0.5 * (f(r["exhaust_lambda_left"]) + f(r["exhaust_lambda_right"]))


def nominal(r):
    s = f(r["speed_rpm"])
    n = int(round(s / float(NOMINAL_RPM)) * NOMINAL_RPM)
    assert abs(s - n) < NOMINAL_RPM / 2.0, (s, n)
    return n


def merge(speeds):
    s = sorted(set(speeds))
    out = [[s[0]]]
    for x in s[1:]:
        if x - out[-1][-1] <= MERGE_RPM:
            out[-1].append(x)
        else:
            out.append([x])
    return out


def name(g):
    return "/".join(str(x) for x in g)


def classify(r, ref, floor, kind):
    """The populations one row belongs to. kind: steady, final, initial."""
    L, mp, bm = lam(r), f(r["intake_manifold_press_kpa_abs"]), f(r["bmep_bar"])
    meter = ok(f(r.get("fuel_meter_flow_gps")))
    fired = bm >= FIRED_BMEP - TOL
    hot = kind == "final" or (kind == "steady" and mp >= floor - TOL)
    l1 = ok(L) and abs(L - ref) <= LAM_BAND + TOL
    enr = ok(L) and L <= ref - LAM_ENR + TOL
    gate = kind != "initial"
    return dict(
        fired=gate and fired, fired_meter=gate and fired and meter, hot=gate and hot,
        hot_meter=gate and hot and meter, hot_l1=gate and hot and l1, hot_enr=gate and hot and enr,
        hot_l1_meter=gate and hot and l1 and meter,
        l1_boost=gate and l1 and mp >= MAP_SPLIT - TOL, l1_thr=gate and l1 and mp < MAP_SPLIT and fired,
        l1_off_ref=gate and hot and l1 and abs(L - ref) > OFF_REF + TOL,
        final=kind == "final", initial=kind == "initial", initial_hot=kind == "initial")


def coverage(rows):
    """Joint coverage: per 20 kPa band of manifold pressure, the speed, intake and coolant ranges."""
    bands = defaultdict(list)
    for r in rows:
        bands[int(f(r["intake_manifold_press_kpa_abs"]) // MAP_BAND)].append(r)
    out = {}
    for b in sorted(bands):
        rr = bands[b]

        def rng(col):
            v = [f(x[col]) for x in rr if ok(f(x.get(col)))]
            return [round(min(v), 1), round(max(v), 1)] if v else None
        out[f"{int(b * MAP_BAND)}-{int((b + 1) * MAP_BAND)} kPa"] = dict(
            n=len(rr), speed_rpm=rng("speed_rpm"), intake_manifold_temp_c=rng("intake_manifold_temp_c"),
            coolant_temp_c=rng("coolant_temp_c"))
    return out


def compute():
    """The split of every engine, as split.json holds it."""
    out = {"rule": "version 2", "sha256_inputs": {}}
    for eng, spec in ENG.items():
        S = {fn: load(eng, fn) for fn in spec["steady"]}
        A, B = load(eng, spec["hli"]), load(eng, spec["hlf"])
        for fn in spec["steady"] + [spec["hli"], spec["hlf"]]:
            out["sha256_inputs"][f"{eng}/{fn}"] = common.sha_raw(os.path.join(common.ENGINE_DIR, eng, fn))
        assert len(A) == len(B)
        for a, b in zip(A, B):
            assert a["source_row"] == b["source_row"] and nominal(a) == nominal(b)
        ref = {}
        for fn, rows in S.items():
            lr = [lam(r) for r in rows if LAM_REF_BMEP[0] <= f(r["bmep_bar"]) <= LAM_REF_BMEP[1] and ok(lam(r))]
            ref[fn] = dict(lambda_ref=st.median(lr), n=len(lr))
        hl_ref = ref[spec["steady"][-1]]["lambda_ref"]
        floor = min(f(r["intake_manifold_press_kpa_abs"]) for r in A + B)
        st_speeds = sorted(set(nominal(r) for rows in S.values() for r in rows))
        hl_speeds = sorted(set(nominal(r) for r in A))
        G = merge(st_speeds + hl_speeds)

        def gid(n):
            return next(i for i, g in enumerate(G) if n in g)
        st_g = sorted(set(gid(n) for n in st_speeds))
        hl_g = sorted(set(gid(n) for n in hl_speeds))
        elig = [i for i in range(len(G)) if i not in (0, len(G) - 1)
                and not (i in st_g and i in (st_g[0], st_g[-1]))
                and not (i in hl_g and i in (hl_g[0], hl_g[-1]))]
        # every row, with its line and populations
        rows_all = []
        for fn, rows in S.items():
            for r in rows:
                rows_all.append(dict(table=fn, source_row=int(r["source_row"]), nominal_rpm=nominal(r),
                                     line=gid(nominal(r)), kind="steady",
                                     pop=classify(r, ref[fn]["lambda_ref"], floor, "steady"), raw=r))
        for fn, rows, kind in ((spec["hli"], A, "initial"), (spec["hlf"], B, "final")):
            for r in rows:
                rows_all.append(dict(table=fn, source_row=int(r["source_row"]), nominal_rpm=nominal(r),
                                     line=gid(nominal(r)), kind=kind,
                                     pop=classify(r, hl_ref, floor, kind), raw=r))
        P = defaultdict(lambda: defaultdict(int))
        for x in rows_all:
            P[x["line"]]["rows"] += 1
            P[x["line"]]["holds"] += int(x["kind"] == "final")
            P[x["line"]]["steady_rows"] += int(x["kind"] == "steady")
            for k, v in x["pop"].items():
                P[x["line"]][k] += int(v)

        def offset_stats(o):
            held = [elig[j] for j in range(o, len(elig), 3)]
            return dict(
                offset=o, held=[name(G[i]) for i in held],
                held_rows=sum(P[i]["rows"] for i in held),
                high_load_lines_ge3_holds=[name(G[i]) for i in held if P[i]["holds"] >= MIN_CLUSTERS],
                e4b_usable_enriched_rows=sum(P[i]["hot_enr"] for i in held if P[i]["l1_boost"] >= MIN_CLUSTERS),
                _held=held)
        cand = [offset_stats(o) for o in (0, 1, 2)]
        need = 2 if any(len(c["high_load_lines_ge3_holds"]) >= 2 for c in cand) else 0
        pool = [c for c in cand if len(c["high_load_lines_ge3_holds"]) >= need]
        best = sorted(pool, key=lambda c: (-c["e4b_usable_enriched_rows"], -c["held_rows"], c["offset"]))[0]
        held = set(best["_held"])
        res = dict(
            lambda_ref={**{fn: round(v["lambda_ref"], 3) for fn, v in ref.items()},
                        spec["hli"]: round(hl_ref, 3), spec["hlf"]: round(hl_ref, 3)},
            lambda_ref_rows={fn: v["n"] for fn, v in ref.items()},
            hot_map_floor_kpa=round(floor, 2),
            lines=[name(g) for g in G], eligible=[name(G[i]) for i in elig],
            offsets=[{k: v for k, v in c.items() if k != "_held"} for c in cand],
            offset_chosen=best["offset"], offset_rule="a. >= 2 held-out lines with >= 3 holds where any offset allows it; "
                                                       "b. most E4b-usable enriched hot rows; c. most held-out rows; d. lowest offset",
            held_out_lines=[name(G[i]) for i in sorted(held)],
            tables={}, per_held_out_line={}, held_out_rows=[], deciding_lines={})
        for fn in spec["steady"] + [spec["hli"], spec["hlf"]]:
            xs = [x for x in rows_all if x["table"] == fn]
            n_h = sum(1 for x in xs if x["line"] in held)
            res["tables"][fn] = dict(rows=len(xs), held_out=n_h, calibration=len(xs) - n_h,
                                     lambda_ref=res["lambda_ref"][fn])
        for x in rows_all:
            if x["line"] in held:
                res["held_out_rows"].append(dict(table=x["table"], source_row=x["source_row"],
                                                 nominal_rpm=x["nominal_rpm"], line=name(G[x["line"]]),
                                                 window={"steady": "steady", "final": "High Load Final",
                                                         "initial": "High Load Initial"}[x["kind"]]))
        for i in sorted(held):
            res["per_held_out_line"][name(G[i])] = dict(P[i])
            l1b = [f(x["raw"]["intake_manifold_press_kpa_abs"]) for x in rows_all if x["line"] == i and x["pop"]["l1_boost"]]
            enr = [f(x["raw"]["intake_manifold_press_kpa_abs"]) for x in rows_all if x["line"] == i and x["pop"]["hot_enr"]]
            res["per_held_out_line"][name(G[i])]["map_range_l1_boost_kpa"] = [round(min(l1b), 1), round(max(l1b), 1)] if l1b else None
            res["per_held_out_line"][name(G[i])]["map_range_hot_enr_kpa"] = [round(min(enr), 1), round(max(enr), 1)] if enr else None
            res["per_held_out_line"][name(G[i])]["e4b_extrapolation_kpa"] = (
                round(max(0.0, max(enr) - max(l1b)), 1) if (l1b and enr) else None)
        # which lines decide each per-line statistic (>= 3 clusters)
        POPS = dict(E1a="hot", E2a="hot_meter", E3a="hot_l1", E4a="hot_enr", L0="hot_l1_meter")
        for stat, pop in POPS.items():
            res["deciding_lines"][stat] = [name(G[i]) for i in sorted(held) if P[i][pop] >= MIN_CLUSTERS]
        res["deciding_lines"]["E4b"] = [name(G[i]) for i in sorted(held)
                                        if P[i]["l1_boost"] >= MIN_CLUSTERS and P[i]["hot_enr"] >= 1]
        res["pooled_counts"] = dict(
            D1_fired_with_meter=sum(P[i]["fired_meter"] for i in held),
            E1b_fired=sum(P[i]["fired"] for i in held),
            E4b_enriched_rows=sum(P[i]["hot_enr"] for i in held if P[i]["l1_boost"] >= MIN_CLUSTERS),
            E4b_lines=len(res["deciding_lines"]["E4b"]),
            E5A_rows=sum(P[i]["l1_thr"] for i in held), E5B_rows=sum(P[i]["l1_boost"] for i in held),
            E8_final_rows=sum(P[i]["final"] for i in held),
            L0_rows=sum(P[i]["hot_l1_meter"] for i in held),
            E1_initial_rows_descriptive=sum(P[i]["initial"] for i in held),
            hot_l1_rows_off_ref_by_more_than_0005=sum(P[i]["l1_off_ref"] for i in held),
            hot_l1_rows=sum(P[i]["hot_l1"] for i in held))
        # coverage, per population and jointly (finding 31)
        fired_rows = [x["raw"] for x in rows_all if x["pop"]["fired"]]
        hot_rows = [x["raw"] for x in rows_all if x["pop"]["hot"]]
        cal_fired = [x["raw"] for x in rows_all if x["pop"]["fired"] and x["line"] not in held]
        cal_hot = [x["raw"] for x in rows_all if x["pop"]["hot"] and x["line"] not in held]
        lam_conv = []
        for x in rows_all:
            L = lam(x["raw"])
            if ok(L):
                rr = ref[x["table"]]["lambda_ref"] if x["table"] in ref else hl_ref
                lam_conv.append((L - (rr - 1.0), x["table"], x["source_row"], x["kind"]))
        lmin = min(lam_conv)
        res["lambda_min_cell_referenced"] = dict(value=round(lmin[0], 4), table=lmin[1], source_row=lmin[2], window=lmin[3])
        res["coverage"] = dict(fired_steady_and_final=coverage(fired_rows), hot=coverage(hot_rows),
                               calibration_fired=coverage(cal_fired), calibration_hot=coverage(cal_hot),
                               fired_intake_temp_c=[round(min(f(r["intake_manifold_temp_c"]) for r in fired_rows), 1),
                                                    round(max(f(r["intake_manifold_temp_c"]) for r in fired_rows), 1)],
                               hot_intake_temp_c=[round(min(f(r["intake_manifold_temp_c"]) for r in hot_rows), 1),
                                                  round(max(f(r["intake_manifold_temp_c"]) for r in hot_rows), 1)])
        res["n_rows"] = len(rows_all)
        res["n_held_out_rows"] = len(res["held_out_rows"])
        res["max_torque_nm_structure_only"] = None   # not read in version 2
        out[eng] = res
    return out


def high_load_lines(eng):
    """The engine's lines that carry high-load holds, as names (rule 2's grouping). Section 2.2 says how
    many of them the split holds out."""
    spec = ENG[eng]
    S = {fn: load(eng, fn) for fn in spec["steady"]}
    A = load(eng, spec["hli"])
    G = merge(sorted(set(nominal(r) for rows in S.values() for r in rows)) + sorted(set(nominal(r) for r in A)))
    hl = {nominal(r) for r in A}
    return [name(g) for g in G if hl & set(g)]


def report(out):
    for eng in ENG:
        res = out[eng]
        print(f"== {eng}: rows {res['n_rows']}, held out {res['n_held_out_rows']}; lambda_ref {res['lambda_ref']}; "
              f"hot MAP floor {res['hot_map_floor_kpa']} kPa")
        print(f"   lines {res['lines']}")
        print(f"   eligible {res['eligible']}")
        for c in res["offsets"]:
            print(f"   offset {c['offset']}: held {c['held']}, rows {c['held_rows']}, high-load lines >= 3 holds "
                  f"{c['high_load_lines_ge3_holds']}, E4b-usable enriched rows {c['e4b_usable_enriched_rows']}")
        print(f"   CHOSEN offset {res['offset_chosen']}: held-out lines {res['held_out_lines']}")
        for fn, t in res["tables"].items():
            print(f"     {fn:30s} rows {t['rows']:4d} held out {t['held_out']:3d} calibration {t['calibration']:4d}")
        for ln, v in res["per_held_out_line"].items():
            print(f"     line {ln:14s} " + " ".join(f"{k} {v[k]}" for k in (
                "rows", "steady_rows", "holds", "fired", "fired_meter", "hot", "hot_meter", "hot_l1", "hot_enr",
                "hot_l1_meter", "l1_boost", "l1_thr", "l1_off_ref", "initial")) +
                  f" e4b_extrap {v.get('e4b_extrapolation_kpa')} kPa")
        print(f"   deciding lines {res['deciding_lines']}")
        print(f"   pooled {res['pooled_counts']}")
        print(f"   coverage: fired intake {res['coverage']['fired_intake_temp_c']} C, hot intake {res['coverage']['hot_intake_temp_c']} C; "
              f"deepest lambda (cell-referenced) {res['lambda_min_cell_referenced']}")


def run():
    out = compute()
    common.write_json(OUT, out)
    report(out)
    return out
