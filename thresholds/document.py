"""document.py -- step 7 of engine_thresholds.py: results/ENGINE_THRESHOLDS.md, from
thresholds/document_template.md and the contract of step 6.

THE TEMPLATE is the .md with every number that steps 1-6 compute replaced by a placeholder,
{{NAME}} or {{NAME:SPEC}}. SPEC is a Python format spec, or one of
  s2   two decimals, trailing zeros dropped (20.00 -> 20, 16.67 -> 16.67);
  t2   two decimals, truncated (9.9955 -> 9.99), beside a requirement that is rounded down;
  c2   two decimals, rounded up (0.4748 -> 0.48), for a bound the prose states ("within"): rounded
       to nearest, a bound can print below the value it bounds.
values() computes every placeholder from the contract and the step outputs. A negative number is
written with the minus sign the prose uses (U+2212), and a number that prints as zero is unsigned.
An unknown placeholder stops the step. The tables whose rows depend on the split or the runs
(section 2.2's, section 1.5's) are built here whole.

THE CLAIMS. Some sentences carry a number's meaning in words ("halves the pair", "one line", "the
same order as b", "above every EPA map's intake temperature"), or set a computed number beside a
committed one ("848.05 (848.1 in results/DRIVE_C_RULE_NUMBERS.txt:42)"). claims() checks each against
the run; if one fails, the .md is not written and the message names the sentence to rewrite (mistake
22: a sentence that carries a number needs the run that printed it).

It reads no EPA torque, fuel or TIT value. The EPA ranges the .md quotes (the TIT windows of section
3, the cam phases of section 2.4) are citations of epa_channels.csv, written in the template as text.
"""
import math
import os
import re
import subprocess
import textwrap

from thresholds import common
from thresholds import contract as C
from thresholds import ecu_shift as U
from thresholds import split as S

ENG_NAME = {"mazda_25t": "Mazda", "honda_l15b7": "Honda", "ford_27tt": "Ford"}
SHORT = {"mazda_25t": "mazda", "honda_l15b7": "honda", "ford_27tt": "ford"}
TABLE_NAME = {"epa_steady.csv": "steady", "epa_highload_initial.csv": "High Load Initial",
              "epa_highload_final.csv": "High Load Final", "epa_steady_cell9.csv": "Cell 9",
              "epa_steady_hd1.csv": "HD1 steady", "epa_highload_initial_hd1.csv": "HD1 High Load Initial",
              "epa_highload_final_hd1.csv": "HD1 High Load Final"}
WORDS = ("no", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
         "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen", "twenty")
MINUS = "−"
PLACEHOLDER = re.compile(r"\{\{([A-Za-z0-9_]+)(?::([^}]*))?\}\}")
WRAP = "@wrap "          # a template line that is wrapped after it is filled in
WIDTH = 100              # the .md's line width
TEMPLATE_NOTE = "<!-- template:"   # the template's first line, for its readers only: not written to the .md
# Values the .md cites from committed files, beside the numbers this run computes (section 1.4).
CITED = dict(damage=848.1, peak_c=883.02, tau_climb_s=47.3, one_minus_f=0.142)
B58_SPARK_ROW = (-1.78, -3.81)     # car minus model spark under boost: the climb's cell, all readings (VALIDATION_PLAN.md:292)
EPA_HOTTEST_TIT_C = 900.8          # the hottest EPA TIT on the tables used here (section 9), plus 100 K of mass averaging
E5_V1_LIMIT = 0.20                 # E5's version-1 R, a slope error of 20 %
V1_REFERENCE_GAP_KPA = (33.0, 78.0)  # how far version 1's lambda = 1 reference sat below the Mazda's enriched rows
X2_TABLE_PAIR_GAP = 1.14           # the largest X1/X2 pair difference, exact plant against the table (section 9)
CUT_EXAMPLES = (0.43, 0.68)        # current-grade's cut and the agents' (section 8)


def word(n):
    return WORDS[n] if 0 <= n < len(WORDS) else str(n)


def join_and(items):
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def fmt(value, spec):
    """One placeholder's text."""
    if isinstance(value, str):
        if spec:
            raise ValueError(f"a text value takes no format spec ({spec!r})")
        return value
    if spec == "s2":
        text = f"{value:.2f}".rstrip("0").rstrip(".")
    elif spec == "t2":
        text = f"{math.floor(abs(value) * 100 + 1e-9) / 100 * (1 if value >= 0 else -1):.2f}"
    elif spec == "c2":
        if value < 0:
            raise ValueError(f"c2 is for a bound, which is not negative ({value!r})")
        text = f"{math.ceil(value * 100 - 1e-9) / 100:.2f}"
    elif spec:
        text = format(value, spec)
    else:
        text = str(value)
    digits = text.lstrip("+-")
    if text.startswith("-") and not re.fullmatch(r"[0.]*", digits.split("e")[0]):
        text = MINUS + text[1:]
    elif text.startswith("-"):
        text = digits
    return text


def wrap(line):
    """A paragraph or list item on one line, wrapped at the .md's 100 columns with its hanging indent."""
    m = re.match(r"( *)(- |\d+\. )?", line)
    lead, bullet = m.group(1), m.group(2) or ""
    return textwrap.fill(line[len(lead) + len(bullet):], width=WIDTH, initial_indent=lead + bullet,
                         subsequent_indent=lead + " " * len(bullet), break_long_words=False, break_on_hyphens=False)


def fill(template, V):
    """The template with every placeholder replaced; an unknown one stops the step. A line that
    starts with WRAP is a paragraph whose length depends on what was filled in: it is wrapped after."""
    missing = sorted({m.group(1) for m in PLACEHOLDER.finditer(template)} - set(V))
    if missing:
        raise SystemExit(f"document: the template names values this step does not compute: {missing}")
    text = PLACEHOLDER.sub(lambda m: fmt(V[m.group(1)], m.group(2) or ""), template)
    return "\n".join(wrap(l[len(WRAP):]) if l.startswith(WRAP) else l for l in text.split("\n"))


def pct_label(name):
    """'lam-0.005' -> 'λ −0.005', 'spark+1.5' -> 'spark +1.5°'."""
    if name.startswith("lam"):
        return "λ " + name[3:].replace("-", MINUS)
    return "spark " + name[5:].replace("-", MINUS) + "°"


def offsets_rule(offsets, chosen):
    """Which of rules a-d chose the offset (section 2.1, rule 4): those that removed a candidate."""
    pool = list(offsets)
    need = 2 if any(len(c["high_load_lines_ge3_holds"]) >= 2 for c in pool) else 0
    used = []
    for rule, key in (("a", None), ("b", "e4b_usable_enriched_rows"), ("c", "held_rows")):
        if len(pool) == 1:
            break
        if rule == "a":
            keep = [c for c in pool if len(c["high_load_lines_ge3_holds"]) >= need]
        else:
            top = max(c[key] for c in pool)
            keep = [c for c in pool if c[key] == top]
        if len(keep) < len(pool):
            used.append(rule)
        pool = keep
    if len(pool) > 1:
        pool = [min(pool, key=lambda c: c["offset"])]
        used.append("d")
    assert pool[0]["offset"] == chosen, (pool, chosen)
    return ("rule " if len(used) == 1 else "rules ") + " then ".join(used)


def alpha_bullets(alpha):
    """Section 2.3's list of the removed ALPHA nodes, one bullet per engine."""
    curves = (("wot_torque_curve", "full-throttle"), ("closed_throttle_torque_curve", "closed-throttle"))
    out = []
    for i, eng in enumerate(common.EPA_ENGINES):
        parts = []
        for key, label in curves:
            nodes = sorted((n for n in alpha[eng] if n["held_out"] and n["curve"] == key), key=lambda n: n["node_rpm"])
            if not nodes:
                continue
            groups = []
            for n in nodes:
                if groups and groups[-1][0]["table"] == n["table"]:
                    groups[-1].append(n)
                else:
                    groups.append([n])
            texts = []
            for g in groups:
                rpms = join_and([format(m["node_rpm"], ".0f") for m in g])
                srcs = ", ".join(str(m["source_row"]) for m in g)
                texts.append(f"{rpms} rpm ({TABLE_NAME[g[0]['table']]} row{'s' if len(g) > 1 else ''} {srcs})")
            parts.append(f"{label} node{'s' if len(nodes) > 1 else ''} at {', '.join(texts)}")
        sep = ", and " if "), " in parts[0] else " and "
        end = "." if i == len(common.EPA_ENGINES) - 1 else ";"
        out.append(f"{WRAP}  - the {ENG_NAME[eng]}'s {sep.join(parts)}{end}")
    return "\n".join(out)


def tracked_py():
    """Every .py a commit of this tree would hold (test_engine_threading.tracked_py's rule). It asks
    git, so step 7 needs git and a git checkout of the repository: the claim 'Nothing has been fitted'
    is checked against these files, and a copy without .git (an unzipped archive) cannot check it."""
    try:
        out = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.py"],
                             cwd=common.REPO, capture_output=True, text=True, check=True).stdout.splitlines()
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit("document: step 7 needs git and a git checkout of this repository, because the claim "
                         "'Nothing has been fitted' is checked against the .py files a commit would hold; "
                         f"git ls-files failed here ({e})") from e
    return sorted(out)


def values(contract, ns, inp):
    """Every placeholder of the template, from the contract (step 6) and the step outputs."""
    R, MEI, B = ns["R"], ns["MEI"], ns["B"]
    split, alpha, b58, K3, FIX = inp["split"], inp["alpha"], inp["b58"], inp["K3"], inp["FIX"]
    c = b58["climb"]
    hs, env, pt = c["housing"], b58["env_torque_bias"], c["point"]
    fl = b58["flat"]
    V = {"N_SHARES": ns["n_shares"], "MEI": MEI, "R1_K": ns["R1_K"], "B": B, "BFRAC_PCT": 100 * ns["B_FRAC"],
         "T_AMB_C": C.T_AMB_C}
    for k, v in R.items():
        V[f"R_{k}"] = v
    for k, v in ns["R_V2"].items():
        V[f"R2_{k}"] = v
    V["B2"] = MEI / C.N_SHARES_VERSION_2
    V["WB_E1b"], V["WB_E2b"] = ns["WORTH_B"]["E1b_torque_pct"], ns["WORTH_B"]["E2b_fuel_pct"]
    V["WB2_E1b"], V["WB2_E2b"] = ns["WORTH_B_V2"]["E1b_torque_pct"], ns["WORTH_B_V2"]["E2b_fuel_pct"]

    # ---------------------------------------------------------------- 1.3, the budget
    LIN, RSS = ns["LINEAR"], ns["RSS"]
    V.update(LINEAR=LIN, LINEAR_MEI=LIN / MEI, RSS=RSS, RSS_MEI=RSS / MEI, IND_LO=1 - RSS / MEI, IND_HI=1 + RSS / MEI,
             ALN_LO=1 - LIN / MEI, ALN_HI=1 + LIN / MEI, RSS2=math.sqrt(2) * B, LIN2=2 * B)
    lin2, rss2 = len(C.PARTS) * V["B2"], math.sqrt(len(C.PARTS)) * V["B2"]
    V.update(LINEAR_MEI_V2=lin2 / MEI, RSS_MEI_V2=rss2 / MEI, IND_LO_V2=1 - rss2 / MEI, IND_HI_V2=1 + rss2 / MEI,
             ALN_LO_V2=1 - lin2 / MEI, ALN_HI_V2=1 + lin2 / MEI, N_SHARES_V2=C.N_SHARES_VERSION_2)
    SL = ns["SLOPE"]
    V.update(SLOPE=SL["slope"], SLOPE_SET=SL["set"], SLOPE_KNOCK="on" if SL["knock"] else "off",
             SLOPE_SHIFT=f"{SL['shift_k']:+d}", SLOPE_10=ns["SLOPE_10"]["slope"], L1_RAW=B / SL["slope"],
             KNEE_WORST=max(v["worst_reproduction"] for v in inp["knee"].values()))

    # ---------------------------------------------------------------- 1.4, the B58 propagation
    fx, sc = c["fixed_spark"]["torque_bias_1pct"], c["ecu_schedule"]["torque_bias_1pct"]
    up, dn = env["+0.01"], env["-0.01"]
    V.update(DMG0=b58["episode_summary"]["damage"], PEAK0=b58["peak_t_turb_c"], TAU_CLIMB=hs["tau_s"],
             ONE_MINUS_F=1 - hs["f"], SPARK_SLOPE=c["ecu_schedule"]["dspark_dmap_deg_per_kpa"],
             FX_DMAP=fx["dmap_kpa"], FX_DEGT=fx["degt_k"], FX_FLOW=100 * fx["dmdot_rel"], FX_DTH=fx["dTh_ss_k"],
             SC_DMAP=sc["dmap_kpa"], SC_DSPARK=c["ecu_schedule"]["dspark_dmap_deg_per_kpa"] * sc["dmap_kpa"],
             SC_DEGT=sc["degt_k"], SC_FLOW=100 * sc["dmdot_rel"], SC_DTH=sc["dTh_ss_k"],
             UP_DMAP=up["dmap_kpa"], UP_DSPARK=up["dspark_deg"], UP_DEGT=up["degt_k"], UP_FLOW=100 * up["dmdot_rel"],
             UP_DTH=up["dTh_median_k"], DN_DMAP=dn["dmap_kpa"], DN_DSPARK=dn["dspark_deg"], DN_DEGT=dn["degt_k"],
             DN_FLOW=100 * dn["dmdot_rel"], DN_DTH=dn["dTh_median_k"],
             GAS_PER_PCT=ns["GAS_PER_PCT"], FLOW_PER_PCT=ns["FLOW_PER_PCT"], HOUSE_B58=ns["HOUSE_PER_PCT_B58"],
             HOUSE_BOUND=ns["HOUSE_PER_PCT_BOUND"], HOUSE_FLOW=ns["HOUSE_PER_PCT_FLOW"], F_STAR=ns["F_STAR"],
             RATIO_HOUSE=ns["HOUSE_PER_PCT_B58"] / abs(fx["dTh_ss_k"]),
             RATIO_FLOW=ns["FLOW_PER_PCT"] / abs(100 * fx["dmdot_rel"]),
             CL_RPM=pt["rpm"], CL_MAP=pt["map"], CL_IAT=pt["iat"], CL_IAT_C=pt["iat"] - 273.15, CL_SPARK=pt["spark"],
             CL_LAM=pt["lam"], CL_EGT=pt["egt"], CL_MDOT=pt["mdot"], CL_TQ=pt["torque"], F_CLIMB=hs["f"],
             UA_G=hs["ua_gas_turb"], UA_GT=hs["ua_gas_turb"] * pt["mdot"], UA_A=hs["ua_turb_amb"], G_K=ns["G_K"],
             FL_RPM=fl["point"]["rpm"], FL_MAP=fl["point"]["map"], F_FLAT=fl["housing"]["f"],
             TAU_FLAT=fl["housing"]["tau_s"], TAU_FLAT_ABOUT=round(fl["housing"]["tau_s"] / 10.0) * 10,
             FL_FLOW=100 * fl["ecu_schedule"]["torque_bias_1pct"]["dmdot_rel"],
             LAM_EGT_LIST=", ".join(fmt(c["lambda"][k]["degt"], ".2f") for k in ("-0.01", "-0.02", "-0.05", "-0.10", "-0.15")),
             LAM010=abs(c["lambda"]["-0.10"]["degt"]), LAM015=abs(c["lambda"]["-0.15"]["degt"]),
             SPK_EGT=c["spark"]["-0.75"]["degt"], SPK_TQ=abs(100 * c["spark"]["-0.75"]["dtorque_rel"]),
             BQ=ns["G_K"] * ns["FLOW_PER_PCT"] / 100, F1MF=hs["f"] * (1 - hs["f"]),
             E1A_RAW=ns["R1_K"] / ns["HOUSE_PER_PCT_BOUND"], E2A_RAW=ns["R1_K"] / ns["HOUSE_PER_PCT_FLOW"],
             E1B_RAW=100 * ns["B_FRAC"] / ns["FLOW_PER_PCT"],
             SC_EGT_PER_KPA=c["ecu_schedule"]["per_kpa"]["egt"], FX_EGT_PER_KPA=c["fixed_spark"]["per_kpa"]["egt"],
             SPARK_SHARE=100 * (1 - c["fixed_spark"]["per_kpa"]["egt"] / c["ecu_schedule"]["per_kpa"]["egt"]),
             E5V1_SLOPE_ERR=E5_V1_LIMIT * c["ecu_schedule"]["per_kpa"]["egt"],
             MISPLACE_LO=E5_V1_LIMIT * c["ecu_schedule"]["per_kpa"]["egt"] * V1_REFERENCE_GAP_KPA[0],
             MISPLACE_HI=E5_V1_LIMIT * c["ecu_schedule"]["per_kpa"]["egt"] * V1_REFERENCE_GAP_KPA[1],
             TAU_FLOW_PART=hs["f"] * R["D1"])

    # ---------------------------------------------------------------- 1.5, the ECU's strategy
    nom = K3["nominal"]
    resp_l = dict(ns["RESP_L"])
    resp_s = dict(ns["RESP_S"])
    fix_l, fix_s = dict(ns["RESP_L_FIX"]), dict(ns["RESP_S_FIX"])
    rows = []
    for mode, name, ds, dl in U.RUNS:
        if mode != "k3":
            continue
        j = K3[name]
        pair = 100 * C.pair(j, "damage")
        if name == "nominal":
            ch, fx_ch, label = "—", "—", "none"
        else:
            r = resp_l[dl] if dl != 0.0 else resp_s[ds]
            ch = fmt(100 * r, "+.1f") + " %"
            f = (fix_l.get(dl) if dl != 0.0 else fix_s.get(ds)) if name in FIX else None
            fx_ch = fmt(100 * f, "+.1f") + " %" if f is not None else ""
            label = pct_label(name)
        rows.append(f"| {label} | {j['knee_k'] - 273.15:.2f} °C | {j['base_lambda_median_400_718']:.3f}, "
                    f"{fmt(j['base_spark_median_400_718'], '+.2f')}° | {pair:.2f} | {ch} | "
                    + (f"{fx_ch} |" if fx_ch else "|"))
    V["ECU_TABLE"] = "\n".join(rows)
    agree = 0.0
    for name, j in K3.items():
        if name == "nominal":
            continue
        t = C.pair(j, "damage") / C.pair(nom, "damage") - 1.0
        th = C.pair(j, "damage_thermal") / C.pair(nom, "damage_thermal") - 1.0
        agree = max(agree, abs(t - th))
    cuts0 = C.cuts(nom, "damage")
    W = ns["W"]
    V.update(K3_ABOVE_S=nom["time_above_nominal_s"], PAIR0=100 * C.pair(nom, "damage"),
             PREV_PAIR0=cuts0["predictive"] - cuts0["current-grade"], THERMAL_AGREE=100 * agree,
             SPK_NOM=nom["base_spark_median_400_718"], SPK_LAMP002=K3["lam+0.02"]["base_spark_median_400_718"],
             K3_SPK_M075_ABS=abs(100 * resp_s[-0.75]), W_LEAN=W["lambda_lean"]["shift"], W_RICH=W["lambda_rich"]["shift"],
             FORD_CELL_GAP=split["ford_27tt"]["lambda_ref"]["epa_steady_hd1.csv"] - split["ford_27tt"]["lambda_ref"]["epa_steady_cell9.csv"],
             LEAN_001=abs(100 * resp_l[0.01]),
             B58_SPK_LO=100 * C.interp(ns["RESP_S"], B58_SPARK_ROW[0]), B58_SPK_HI=100 * C.interp(ns["RESP_S"], B58_SPARK_ROW[1]),
             ECU_LOAD_KPA=U.ECU_LOAD_KPA)
    V["U_LAM"] = V["FORD_CELL_GAP"] / math.sqrt(3.0)
    V["U_E8"] = V["U_LAM"] / 0.01 * V["LEAN_001"]
    V["U2_E8"] = 2 * V["U_E8"]

    def spark_sentence(w):
        r, a = w["spark_retard"], w["spark_advance"]
        if r["extrapolated"] and a["extrapolated"]:
            return (f"For spark it is about {fmt(r['shift'], '+.1f')}° or {fmt(a['shift'], '+.1f')}°, extrapolated "
                    f"beyond the measured {fmt(r['largest_measured'][0], '+.1f')}° and "
                    f"{fmt(a['largest_measured'][0], '+.1f')}°.")
        if a["extrapolated"]:
            return (f"For spark it is {fmt(r['shift'], '+.1f')}° by interpolation, or about "
                    f"{fmt(a['shift'], '+.1f')}°, extrapolated beyond the measured "
                    f"{fmt(a['largest_measured'][0], '+.1f')}°.")
        if r["extrapolated"]:
            return (f"For spark it is about {fmt(r['shift'], '+.1f')}°, extrapolated beyond the measured "
                    f"{fmt(r['largest_measured'][0], '+.1f')}°, or {fmt(a['shift'], '+.1f')}° by interpolation.")
        return f"For spark it is {fmt(r['shift'], '+.1f')}° or {fmt(a['shift'], '+.1f')}°, by interpolation."
    V["SPARK_WORTH"] = spark_sentence(W)
    # the same shifts at version 2's b, for section 12
    W2 = {k: C.worth(ns["RESP_L"] if k.startswith("lambda") else ns["RESP_S"], -1 if k in ("lambda_rich", "spark_retard") else 1,
                     1.0 / C.N_SHARES_VERSION_2)
          for k in ("lambda_rich", "lambda_lean", "spark_retard", "spark_advance")}

    # ---------------------------------------------------------------- 2, the split
    off_rows, tab_rows, line_rows, dec_rows = [], [], [], []
    first = True
    for eng in common.EPA_ENGINES:
        s, e = split[eng], ENG_NAME[eng]
        cells = []
        for o in s["offsets"]:
            lab = (f" ({o['held_rows']} rows; {len(o['high_load_lines_ge3_holds'])} lines with ≥ 3 holds; "
                   f"{o['e4b_usable_enriched_rows']} E4b rows)") if first else (
                f" ({o['held_rows']}; {len(o['high_load_lines_ge3_holds'])}; {o['e4b_usable_enriched_rows']})")
            first = False
            cells.append(", ".join(o["held"]) + lab)
        off_rows.append(f"| {e} | " + " | ".join(cells) + f" | **{s['offset_chosen']}**, by "
                        f"{offsets_rule(s['offsets'], s['offset_chosen'])} |")
        steady = [fn for fn in s["tables"] if "steady" in fn]
        hl = [fn for fn in s["tables"] if "highload" in fn]
        for fn in steady:
            t = s["tables"][fn]
            tab_rows.append(f"| {e} | `{fn}` | {t['rows']} | {t['held_out']} | {t['calibration']} |")
        a, b = (s["tables"][fn] for fn in hl)
        tab_rows.append(f"| {e} | High Load Initial / Final{' (HD1)' if hl[0].endswith('_hd1.csv') else ''} | "
                        f"{a['rows']} / {b['rows']} | {a['held_out']} / {b['held_out']} | {a['calibration']} / {b['calibration']} |")
        V[f"HO_{SHORT[eng]}"] = s["n_held_out_rows"]
        V[f"NROWS_{SHORT[eng]}"] = s["n_rows"]
        for ln, p in s["per_held_out_line"].items():
            line_rows.append(f"| {e} | {ln} | {p['steady_rows']} | {p['holds']} | {p['fired']} ({p['fired_meter']}) | "
                             f"{p['hot']} | {p['hot_l1']} | {p['hot_enr']} | {p['l1_boost']} | {p['l1_thr']} |")
        d, pc = s["deciding_lines"], s["pooled_counts"]
        dec_rows.append(f"| {e} | {', '.join(d['E1a'])} | {', '.join(d['E2a'])} | {', '.join(d['E3a'])} | "
                        f"{', '.join(d['E4a'])} | {', '.join(d['E4b'])} ({pc['E4b_enriched_rows']}) | "
                        f"{pc['D1_fired_with_meter']} | {pc['E8_final_rows']} |")
        k = SHORT[eng]
        V[f"E4B_EXTRAP_{k}"] = join_and([fmt(s["per_held_out_line"][ln]["e4b_extrapolation_kpa"], ".1f") for ln in d["E4b"]])
        V[f"D1_{k}"] = pc["D1_fired_with_meter"]
        V[f"E8ROWS_{k}"] = pc["E8_final_rows"]
        V[f"L0LINES_{k}"] = len(d["L0"])
        V[f"FLOOR_{k}"] = s["hot_map_floor_kpa"]
        V[f"SNAP_{k}"] = pc["hot_l1_rows_off_ref_by_more_than_0005"] if pc["hot_l1_rows_off_ref_by_more_than_0005"] else "none"
        V[f"HL1_{k}"] = pc["hot_l1_rows"]
        V[f"FIRED_IAT_MAX_{k}"] = s["coverage"]["fired_intake_temp_c"][1]
        V[f"FIRED_IAT_MIN_{k}"] = s["coverage"]["fired_intake_temp_c"][0]
        V[f"HOT_IAT_MAX_{k}"] = s["coverage"]["hot_intake_temp_c"][1]
        hl_all = S.high_load_lines(eng)
        V[f"HL_ALL_{k}"] = len(hl_all)
        V[f"HL_HELD_{k}"] = sum(1 for ln in s["held_out_lines"] if s["per_held_out_line"][ln]["holds"] > 0)
        lf = contract["engines"][eng]["lambda_clip_floor"]
        V[f"LAMFLOOR_{k}"] = lf["floor"]
        V[f"DEEP_{k}"] = lf["deepest_epa_lambda_cell_referenced"]
    V["OFFSETS_TABLE"], V["TABLES_TABLE"] = "\n".join(off_rows), "\n".join(tab_rows)
    V["LINES_TABLE"], V["DECIDING_TABLE"] = "\n".join(line_rows), "\n".join(dec_rows)
    mz, fd = split["mazda_25t"], split["ford_27tt"]
    V["MAZDA_E4A_LINE"] = mz["deciding_lines"]["E4a"][0]
    V["MAZDA_E4A_ROWS"] = mz["per_held_out_line"][mz["deciding_lines"]["E4a"][0]]["hot_enr"]
    V["FORD_L0_RANGE"] = f"{fd['deciding_lines']['L0'][0]}–{fd['deciding_lines']['L0'][-1]}"
    V["FORD_HL_HOT_L1"] = join_and([str(fd["per_held_out_line"][ln]["hot_l1"]) for ln in fd["held_out_lines"]
                                    if fd["per_held_out_line"][ln]["holds"] > 0])
    e4a = []
    for i, eng in enumerate(common.EPA_ENGINES):
        s = split[eng]
        lines = s["deciding_lines"]["E4a"]
        n = [str(s["per_held_out_line"][ln]["hot_enr"]) for ln in lines]
        e4a.append(f"the {ENG_NAME[eng]}'s {join_and(lines)} ({join_and(n)}{' rows' if i == 0 else ''})")
    V["E4A_LINES"] = ", ".join(e4a[:-1]) + ", and " + e4a[-1]
    removed = sum(1 for eng in common.EPA_ENGINES for n in alpha[eng] if n["held_out"])
    V["ALPHA_COUNT_WORD"] = word(removed).capitalize()
    V["ALPHA_BULLETS"] = alpha_bullets(alpha)

    # ---------------------------------------------------------------- 3, conventions; 4, the rows
    lr = {fn: v for eng in common.EPA_ENGINES for fn, v in split[eng]["lambda_ref"].items()}
    V.update(LREF_mazda=split["mazda_25t"]["lambda_ref"]["epa_steady.csv"],
             LREF_N_mazda=split["mazda_25t"]["lambda_ref_rows"]["epa_steady.csv"],
             LREF_honda=split["honda_l15b7"]["lambda_ref"]["epa_steady.csv"],
             LREF_N_honda=split["honda_l15b7"]["lambda_ref_rows"]["epa_steady.csv"],
             LREF_cell9=lr["epa_steady_cell9.csv"], LREF_N_cell9=split["ford_27tt"]["lambda_ref_rows"]["epa_steady_cell9.csv"],
             LREF_hd1=lr["epa_steady_hd1.csv"], LREF_N_hd1=split["ford_27tt"]["lambda_ref_rows"]["epa_steady_hd1.csv"])
    F = ns["FUEL"]
    for eng in common.EPA_ENGINES:
        V[f"FUEL_{SHORT[eng]}"] = f"({F[eng]['ftag']}): {F[eng]['lhv_mj_per_kg']:.3f} MJ/kg, AFR_st {F[eng]['afr_st']:.3f}"
    V["FORD_HD1_FTAG"] = ns["FUEL_BY_TABLE"]["ford_27tt"]["epa_steady_hd1.csv"]["fuel_report"]
    afrs = [F[e]["afr_st"] for e in common.EPA_ENGINES]
    lhvs = [F[e]["lhv_mj_per_kg"] for e in common.EPA_ENGINES]
    V.update(AFR_MIN=min(afrs), AFR_MAX=max(afrs), LHV_MIN=min(lhvs), LHV_MAX=max(lhvs))
    V["LAM_OFFSETS"] = (f"{fmt(V['LREF_mazda'] - 1, '.3f')} (Mazda), {fmt(V['LREF_honda'] - 1, '.3f')} (Honda), "
                        f"{fmt(V['LREF_cell9'] - 1, '.3f')} (Ford Cell 9), {fmt(V['LREF_hd1'] - 1, '.3f')} (HD1)")
    a6 = ns["E6_AFR"]
    V.update(E6_AIR=100 * a6["air_rel"], E6_EXH=100 * a6["exhaust_flow_rel"], E6_TAU=100 * a6["tau_rel"],
             E6_HB58=a6["housing_b58_k"], E6_HBOUND=a6["housing_bound_k"])
    V["HONDA_RAW_DEEP"] = V["DEEP_honda"] + (V["LREF_honda"] - 1)
    V["DEEP_NOTE_mazda"] = ", an Initial row" if split["mazda_25t"]["lambda_min_cell_referenced"]["window"] == "initial" else ""
    V.update(U_ETA_PCT=100 * ns["U_ETA"], U_RAD_PCT=100 * ns["U_RAD"], U_TQ_PCT=100 * ns["U_C3_TORQUE"],
             U_FUEL_PCT=100 * ns["U_C3_FUEL"], U2_FUEL_PCT=200 * ns["U_C3_FUEL"], N_D3=len(ns["D3"]))

    # ---------------------------------------------------------------- 8, 9
    eps = R["E4b"] / 100.0
    errs = [100 * eps * (1 - cc) * abs(math.log(1 - cc)) for cc in CUT_EXAMPLES]
    largest = 100 * eps * math.exp(-1.0)          # at c = 1 - 1/e: the most a lever error moves a cut
    V.update(CUT_ERR_043=errs[0], CUT_ERR_068=errs[1], S2_EXCESS=X2_TABLE_PAIR_GAP - R["S2a"])
    if min(errs) > MEI:
        V["CUT_LEVEL_PHRASE"] = "by more than the MEI"
    elif largest >= 0.8 * MEI:
        V["CUT_LEVEL_PHRASE"] = "by about the MEI"
    else:
        V["CUT_LEVEL_PHRASE"] = "by less than the MEI"
    V["ECU_DIR"] = common.rel(common.ECU_DIR)
    V["OUT_DIR"] = common.rel(common.OUT_DIR)
    V["N_RUNS"] = len(U.RUNS)
    V["N_RUNS_FIXED"] = sum(1 for r in U.RUNS if r[0] == "fixed")
    V["N_RUNS_K3"] = sum(1 for r in U.RUNS if r[0] == "k3")
    row191 = next(r for r in S.load("mazda_25t", "epa_steady.csv") if r["source_row"] == "191")
    V["MAZDA_ROW191_LINE"] = next(g for g in split["mazda_25t"]["lines"]
                                  if str(S.nominal(row191)) in g.split("/"))

    def e8_change(w2, w):
        out = [f"λ {fmt(w2['lambda_lean']['shift'], '+.4f')} → {fmt(w['lambda_lean']['shift'], '+.4f')} lean and "
               f"{fmt(w2['lambda_rich']['shift'], '+.4f')} → {fmt(w['lambda_rich']['shift'], '+.4f')} rich"]
        for key, side in (("spark_retard", "retard"), ("spark_advance", "advance")):
            a, b = w2[key], w[key]
            tag = lambda x: ", extrapolated" if x["extrapolated"] else ", interpolated"  # noqa: E731
            out.append(f"spark {side} {fmt(a['shift'], '+.1f')}°{tag(a)} → {fmt(b['shift'], '+.1f')}°{tag(b)}")
        return "; ".join(out)
    V["E8_WORTH_CHANGE"] = e8_change(W2, W)
    return V


def claims(V, contract, ns, inp):
    """(sentence, holds) for every sentence whose words depend on a computed number."""
    split, K3 = inp["split"], inp["K3"]
    resp_s_fix = dict(ns["RESP_S_FIX"])
    W = ns["W"]
    out = [
        ("1.4: the damage reproduces DRIVE_C_RULE_NUMBERS.txt:42's 848.1", round(V["DMG0"], 1) == CITED["damage"]),
        ("1.4: the peak reproduces DRIVE_C_RULE_NUMBERS.txt:42's 883.02 C", round(V["PEAK0"], 2) == CITED["peak_c"]),
        ("1.4: tau on the climb reproduces preview_ceiling.txt:27's 47.3 s", round(V["TAU_CLIMB"], 1) == CITED["tau_climb_s"]),
        ("1.4: 1 - f reproduces DAMAGE_CONSTANTS.md:35's 0.142", round(V["ONE_MINUS_F"], 3) == CITED["one_minus_f"]),
        ("1.4: 'ua_g x mdot' is the flow per housing (the B58 has one turbine)",
         abs(V["UA_GT"] * (1 - V["F_CLIMB"]) / (V["F_CLIMB"] * V["UA_A"]) - 1.0) < 1e-9),
        ("1.4: the bound's maximum lies inside 0 <= f <= 1 ((A + B)^2/(4B))", 0.0 <= V["F_STAR"] <= 1.0),
        ("1.4: 'G ... errs tight': G exceeds the hottest EPA TIT + 100 K over 42 C",
         V["G_K"] > EPA_HOTTEST_TIT_C + 100.0 - C.T_AMB_C),
        ("1.2a: 1 - e^-2 = 0.865", abs(1 - math.exp(-2) - 0.865) < 5e-4),
        ("1.2c: 'from one 57 K shift ... still the largest slope measured'", abs(ns["SLOPE"]["shift_k"]) == 57),
        ("1.5: 'its spark falls ... at +0.02' (a leaner baseline knock-retards)", V["SPK_LAMP002"] < V["SPK_NOM"]),
        ("1.5: 'at a fixed knee, spark -0.75 deg halves the pair'", -0.6 <= resp_s_fix[-0.75] <= -0.4),
        ("1.5: 'Every lambda shift from the nominal 1.00 shrinks the pair'",
         all(y < 0 for x, y in ns["RESP_L"] if x != 0.0)),
        ("1.5: the lambda shifts worth b are interpolated", not (W["lambda_lean"]["extrapolated"] or W["lambda_rich"]["extrapolated"])),
        ("1.5: 'Then 2u > R' for E8", V["U2_E8"] > V["R_E8"]),
        ("1.5: 'It is the same order as b'", all(1 / 3 <= abs(x) / V["BFRAC_PCT"] <= 3 for x in (V["B58_SPK_LO"], V["B58_SPK_HI"]))),
        ("1.5: the ECU shift acts above 100 kPa", U.ECU_LOAD_KPA == 100.0),
        ("2.1: the split's constants are the ones the rule states",
         (S.NOMINAL_RPM, S.MERGE_RPM, S.LAM_BAND, S.LAM_ENR, S.MAP_SPLIT, S.MIN_CLUSTERS, S.FIRED_BMEP, S.OFF_REF)
         == (50, 50, 0.02, 0.05, 100.0, 3, 2.0, 0.005)),
        ("2.2: 'The Mazda's E4a rests on one line'", len(split["mazda_25t"]["deciding_lines"]["E4a"]) == 1),
        ("2.2: the merged column 'E3a, L0' (both have the same deciding lines)",
         all(split[e]["deciding_lines"]["E3a"] == split[e]["deciding_lines"]["L0"] for e in common.EPA_ENGINES)),
        ("2.2: 'The Ford's L0 and L1 rest on its steady hot rows'",
         all(split["ford_27tt"]["per_held_out_line"][ln]["holds"] == 0 for ln in split["ford_27tt"]["deciding_lines"]["L0"])),
        ("2.2: 'The Ford's 3500 rpm line ... is held out'", "3500" in split["ford_27tt"]["held_out_lines"]),
        ("2.5: the CX-9's 4173 rpm sits between the Mazda's calibration lines at 4000 and 4500 rpm",
         {"4000", "4500"} <= set(split["mazda_25t"]["lines"]) - set(split["mazda_25t"]["held_out_lines"])
         and split["mazda_25t"]["lines"].index("4500") == split["mazda_25t"]["lines"].index("4000") + 1),
        ("3: 'The 0.02 is how far one engine's two cells disagree'", abs(V["FORD_CELL_GAP"] - S.LAM_BAND) < 1e-9),
        ("3: the Ford's HD1 tables ran on FTAG 26864, the Mazda's batch",
         V["FORD_HD1_FTAG"] == "26864" and C.BATCH["26864"] == "mazda_25t"),
        ("3: 'the charge sits above every EPA map's intake temperature'",
         V["CL_IAT_C"] > max(V[f"FIRED_IAT_MAX_{k}"] for k in SHORT.values())),
        ("3: the thermocouple's u_D is 3.5 K at 800 C", round(0.0075 * 800 / math.sqrt(3), 1) == 3.5),
        ("4: 'An ECU fitted to the Honda's enrichment (lambda 0.61 ...)'", round(V["HONDA_RAW_DEEP"], 2) == 0.61),
        ("5: C1 and C2 are identities at 1e-6", all(r["R"] == 1e-6 for r in contract["cars"] if r["id"] in ("C1", "C2"))),
        ("5: 2u_input exceeds E2a's R, so C3a and C3c are descriptive", V["U2_FUEL_PCT"] > V["R_E2a"]),
        ("5: the D3 files are tests 61704001-044", (ns["D3"][0]["test"], ns["D3"][-1]["test"]) == ("61704001", "61704044")),
        ("5: the EPA map's heating value is 18,447 BTU/lbm",
         round(common.load_json(os.path.join(common.ENGINE_DIR, "mazda_25t", "epa_engine.json"))["alpha_fuel"]["energy_density_BTUplbm"]) == 18447),
        ("9: 'as one it would exceed S2's R'", V["S2_EXCESS"] > 0),
        ("9: the Mazda's spreadsheet row 191 sits on a calibration line", V["MAZDA_ROW191_LINE"] not in split["mazda_25t"]["held_out_lines"]),
        ("12: 'the agreement's largest exact difference is at spark -3.0 deg'", _largest_disagreement(K3) == "spark-3.0"),
        ("12: 'four pair entries move by 0.01' against version 2's differenced rounded cuts", _pair_rounding_moves(K3) == 4),
        ("12: 'the Honda has 11 high-load lines, not 12: version 2 counted its hold speeds'",
         (V["HL_ALL_honda"], _hold_speeds("honda_l15b7")) == (11, 12)),
        ("Nothing has been fitted: calibrate_epa.py does not exist", not os.path.exists(os.path.join(common.REPO, "calibrate_epa.py"))),
        ("Nothing has been fitted: the .py files that name the EPA tables are epa_map.py, test_epa_map.py and "
         "this generator", {p for p in tracked_py() if _names_epa_tables(p) and not _is_generator(p)}
         == {"epa_map.py", "test_epa_map.py"}),
    ]
    return out


def _largest_disagreement(K3):
    """The shift at which the thermal-only reading of the pair's change differs most from the total."""
    nom = K3["nominal"]
    gap = {n: abs(C.pair(j, "damage") / C.pair(nom, "damage") - C.pair(j, "damage_thermal") / C.pair(nom, "damage_thermal"))
           for n, j in K3.items() if n != "nominal"}
    return max(gap, key=gap.get)


def _pair_rounding_moves(K3):
    """How many pair entries of section 1.5 differ, by 0.01, from version 2's difference of rounded cuts."""
    n = 0
    for j in K3.values():
        cr = {k: round(v, 2) for k, v in C.cuts(j, "damage").items()}
        old, new = f"{cr['current-grade'] - cr['reactive']:.2f}", f"{100 * C.pair(j, 'damage'):.2f}"
        if old != new:
            assert abs(float(old) - float(new)) < 0.0101, (old, new)
            n += 1
    return n


def _hold_speeds(eng):
    return len({S.nominal(r) for r in S.load(eng, S.ENG[eng]["hli"])})


def _is_generator(rel):
    return rel == "engine_thresholds.py" or rel.startswith("thresholds/")


def _names_epa_tables(rel):
    try:
        with open(os.path.join(common.REPO, rel), encoding="utf-8") as fh:
            src = fh.read()
    except (OSError, UnicodeDecodeError):
        return False
    return "epa_steady" in src or "epa_highload" in src


def render_with(template, contract, ns, inp):
    """The .md from a template: every claim checked first, then every placeholder filled."""
    V = values(contract, ns, inp)
    checked = claims(V, contract, ns, inp)
    bad = [what for what, ok in checked if not ok]
    if bad:
        raise SystemExit("document: these sentences no longer match the run; rewrite them in "
                         "thresholds/document_template.md before writing the .md:\n  " + "\n  ".join(bad))
    return fill(template, V), V, checked


def render(contract, ns, inp):
    """Step 7: the .md's text, from thresholds/document_template.md."""
    with open(common.TEMPLATE_MD, encoding="utf-8") as fh:
        template = fh.read().replace("\r\n", "\n")
    if template.startswith(TEMPLATE_NOTE):
        template = template.split("\n", 1)[1]
    text, V, checked = render_with(template, contract, ns, inp)
    used = {m.group(1) for m in PLACEHOLDER.finditer(template)}
    print(f"template {common.rel(common.TEMPLATE_MD)}: {len(PLACEHOLDER.findall(template))} placeholders "
          f"({len(used)} values), {len(checked)} claims checked against the run, all hold")
    return text
