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

VERSION 4'S CLAIMS (22 October 2026, corrected seven times on 23 October after its seven reviews;
section 13 of the .md). Version 4 moved no R or split of version 3, and of the populations it named
only E8's (dl over the rows that publish a lambda, ds over those that publish a spark, each of at
least C.E8_MIN_ROWS rows: version 4's reading of decision 54); it wrote three things version 3 did not name (one population, C5's steps, decision
73; the inputs of the rows without a reading, decision 54; the statistic details version 3 left
open, decision 57), and changed only the statistics and rule text decisions 39 and 57 name and
those of decisions 73-76, which its reviews raised (decision 76's two numbers, C.REDRAW_CAP and
C.REDRAW_DISCARDS, and the redraw streams' tag, C.REDRAW_STREAM_TAG, are checked against the sheet's row 76); claims() checks what it kept against digests of
version 3's JSON (ef5e14e), pinned in V3_DIGESTS, so a later edit that moves one stops this step
instead of passing silently. It also
checks the numbers the .md takes from the plant code (the neutral action's float32 trims, the
shared rich slope, the B58's lambda clip, which the JSON records as version_4.plant_values) and
version 3's lambda clip, read from ef5e14e's engine_env.py; C5's three outcomes against their case
table, and the values decisions 54 and 57 state against the JSON's conventions and section 13's list
of them (both after version 4's seventh review). And it checks every code citation into
PLANT_CODE and engine_specs/, which amendment B5 freezes after commit A: each is pinned in
CODE_CITES with a text its line must hold, so a tree whose cited lines moved stops this step and
names them. The version-3 lines of section 13's table of moves are pinned the same way in V3_CITES,
against ef5e14e's tree read through git, and the table's version-3 column must cite exactly them.
Citations of other files (documents, data, scripts outside PLANT_CODE) are not pinned to a text:
those files are not frozen, and a moved line there would stop a contract that rule 0 forbids
rewriting; the .md cites each REFERENCES.md row with its text beside the line instead. The one
exception is the decision sheet, results/VALIDATION_DECISIONS.md, whose cited lines are pinned to
their rows' text in SHEET_CITES (version 4's fourth review): the sheet is the file most likely to
be edited before version 4 is committed, and after the first fit the claims that nothing has been
fitted stop this step anyway. Since the
third review of version 4 every file:line of the .md and the JSON is resolved, though (amendment
A3's scan, _citation_scan): it must name a file of the repository that holds the cited lines, read
as written or under results/; or an EPA table, by its existence alone, since the generator opens no
epa_channels.csv; or a file the .md's Appendix A quotes from outside the repository (CATALOGUE.md,
fe_out/). The scan checks the file and the range, not the text. The last claims check that
nothing has been fitted: calibrate_epa.py does not exist, only epa_map.py, test_epa_map.py and the
generator name the EPA tables, and nothing a fit writes exists (results/EPA_CALIBRATION/,
results/EPA_VALIDATION/, an EPA engine's derived_params.json).
"""
import hashlib
import json
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
# Version 3's JSON (git show ef5e14e:results/ENGINE_THRESHOLDS.json), digested by _digest on 22
# October 2026 when version 4 was written: what version 4 keeps (section 13). per_threshold: [engine,
# row, kind, part, R, unit] of every entry of `thresholds`; non_c5_d1_e8: every entry but C5's, D1's
# and E8's, whole; d1_e8_rest: the D1 and E8 entries without statistic; c5_rest: the C5 entries
# without statistic and on_fail; engines: the `engines` section; inputs: [generator_inputs_sha256,
# epa_tables_sha256]; key_paths: every dict key path, list entries included by index (_key_paths;
# recomputed on 23 October 2026, when the check began to enter lists: the digest of the first draft,
# which did not, was f990a1c5...). non_c5_d1_e8 and d1_e8_rest were computed from the same JSON on 23
# October 2026, after version 4's fourth review, when D1's and E8's statistic text began to point at
# version 4's details; until then non_c5, every entry but C5's, was dcadb641..., and the same
# computation still gives it from version 3's JSON.
V3_DIGESTS = dict(
    per_threshold="4f426c41271d9dbb636f84d7ca24a216de57fec37f161e9526e4660c12d3f8ca",
    non_c5_d1_e8="47b2a2a8c85f41f29d879af062aa9d11671b29c2c32f4603df402e2473c8f079",
    d1_e8_rest="73572647187041e079f95dc051071c9a92096feba155e4e858ca5ad707414b26",
    c5_rest="a898d476ca419a0c4fbe1790bfcb11e4a74865120f7f19d9a2d7a28cbb730df3",
    engines="5346a77cf8d755378e8f84cb8a446924a92a5e42bc03c272e4aeff26ab088a01",
    inputs="8def6fba107c1b7b38990f468bf030f410baa5d5dd71bc757f099bfe23020b3a",
    key_paths="9c61b6c903cfa0749e65a4c0ec0ae2808c186bb64d04b87e93c62a3f1ae0d9f3")
# The key paths version 4 added (section 13; contract.py's version_4.schema): the rules version 3 had
# no field for. A path is new if it is one of these or lies under one; cars[7] is C5.
V4_NEW_KEYS = ("version_4", "tests_lists", "model_form.in_sample_rules", "model_form.neutral_action_identity",
               "conventions.lambda_missing", "conventions.spark_sentinel", "conventions.held_out_counts",
               "conventions.censored", "conventions.statistic_details", "cars[7].steps", "cars[7].threshold",
               "cars[7].redraw") + tuple(
                   f"decisions.{n}" for n in ("39", "40", "49", "54", "55", "57", "59", "64", "70", "71", "73",
                                               "74", "75", "76"))
# The values decisions 54 and 57 state, which version 4 writes and version 3 had no rule for (section 13's list,
# written after version 4's seventh review): the JSON's conventions entry, the phrase its string holds, and the
# phrase section 13 lists the value by. A convention whose value is edited stops step 7 until section 13 follows it.
V4_DECISION_VALUES = (
    ("lambda_missing", "a fired row without lambda runs at lambda 1.00", "λ 1.00 for a fired row without λ"),
    ("spark_sentinel", "EPA's sentinel, exactly -120", "the −120 spark sentinel"),
    ("censored", "at least 2 of its calibration High Load Final rows sit at their own minimum lambda within 1e-9",
     "at least 2 calibration Final rows sit at their own minimum λ within 1e-9"),
    ("statistic_details.d1", "every 10 kPa", "D1's pre-scan every 10 kPa"),
    ("statistic_details.d1", "to 1e-3 kPa", "its bisection to 1e-3 kPa"),
)
# Every code citation of the .md and the JSON into PLANT_CODE (fingerprint.PLANT_CODE) and engine_specs/,
# which amendment B5 freezes after commit A, with the text its first line must hold (and, for a range,
# its last): written on 23 October 2026 from the tree of 4461a91, each read at its line, engine_env.py:1644
# (GRADE_RAMP_S, cited by C5's steps) added the same day when decisions 73 and 74 were written in. claims()
# fails if a citation is not here, if a pin is no longer cited, or if a pinned line moved.
CODE_CITES = {
    "plant.py:58-72": ("def combustion_efficiency(lam, *, engine):", "return np.clip(1.0 - 0.55 * (lam - 1.08) ** 2"),
    "plant.py:99-99": "return np.clip(c.ve_base + c.ve_amp * np.exp(-((rpm - c.ve_rpm) / c.ve_width) ** 2)",
    "plant.py:220-220": "m_fuel = m_air / (fuel.afr_st * op.lam)",
    "plant.py:222-222": "t_wall = 0.5 * op.ect_k + 0.5 * (op.ect_k + c.t_head_k)",
    "plant.py:233-233": "q_total = min(m_fuel, m_air / fuel.afr_st) * fuel.lhv_j_per_kg * eta_comb",
    "plant.py:250-250": "theta = np.arange(geo.ivc_deg, geo.evo_deg + dtheta, dtheta)",
    "plant.py:335-338": ("# UA_PORT is the one openly empirical constant here", "UA_PORT = c.ua_port"),
    "plant.py:338-344": ("UA_PORT = c.ua_port", "t_exh = t_wall + (t_blowdown - t_wall) * retained"),
    "plant.py:343-344": ("retained = np.exp(-UA_PORT / max(mdot_exh * CP_EXH, 1.0))",
                         "t_exh = t_wall + (t_blowdown - t_wall) * retained"),
    "thermal.py:255-255": "q_fuel = mdot_fuel_gps * 1e-3 * p.fuel_lhv_j_per_kg",
    "thermal.py:275-285": ("# One housing per turbine", "self.t_turb += dt * (q_in_turb - q_out_turb) / p.c_turb"),
    "engines.py:603-603": "1.0 - ecu.enr_depth >= ecu.lam_floor > 0.0",
    "engine_env.py:177-201": ("def knock_limited_spark(self, rpm, map_kpa):", "c.spark_min, c.spark_max))"),
    "engine_env.py:394-414": ("def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):", "float(lam), fan)"),
    "engine_env.py:545-548": ("def shift_ceiling_nm(self, rpm):", "return min(self.SHIFT_LOAD * self.PEAK_TORQUE_NM"),
    "engine_env.py:598-633": ("def gear_for(self, v_mps, force_n=None):", "return g"),
    "engine_env.py:624-624": "while g > 0:",
    "engine_env.py:630-631": ("> self.SHIFT_RPM_MAX:", "the lower gear would hit the limiter"),
    "engine_env.py:803-807": ("def kickdown_threshold_nm(self, rpm):", "return self.car.kickdown_load * self.deliverable_nm(rpm)"),
    "engine_env.py:813-852": ("def ratio_for(self, v_mps, force_n):", '"power-limited", n_eco, t_eco'),
    "engine_env.py:820-821": ("if n_low < car.cvt_rpm_min:", '"low-speed", None, None'),
    "engine_env.py:833-833": "if force_n <= 0.0 or t_eco <= self.kickdown_threshold_nm(n_eco):",
    "engine_env.py:972-978": ("def damage_rate(t_turb_k, t_oil_k, knock_integral=None, *, cal):", "return float(d)"),
    "engine_env.py:980-980": "ACT_LO = np.array([-8.0, -0.15,",
    "engine_env.py:993-993": "PREVIEW_S = (",
    "engine_env.py:1031-1031": "a = np.clip(a, -1.0, 1.0)",
    "engine_env.py:1053-1053": "p_exh_kpa=exhaust_backpressure_kpa(map_kpa, engine=eng)",
    "engine_env.py:1076-1076": "def _track_torque(self, torque_req, rpm,",
    "engine_env.py:1223-1223": "self.prev_act = np.zeros(5, dtype=np.float32)",
    "engine_env.py:1249-1251": ("act = np.clip(raw, self.prev_act - slew, self.prev_act + slew)",
                                "act[0] = min(act[0], SPARK_TRIM_MAX)"),
    "engine_env.py:1283-1283": "sp_b, lam_b, fan_b = self.ecu.step(self.rpm, self.map_b_prev,",
    "engine_env.py:1310-1310": "self.spark = float(np.clip(sp_b + act[0],",
    "engine_env.py:1310-1311": ("self.spark = float(np.clip(sp_b + act[0],", "eng.ecu.spark_min, eng.ecu.spark_max))"),
    "engine_env.py:1310-1316": ("self.spark = float(np.clip(sp_b + act[0],",
                                "self.lam = float(np.clip(lam_b + act[1], eng.ecu.lam_floor, eng.ecu.lam_ceiling))"),
    "engine_env.py:1316-1316": "self.lam = float(np.clip(lam_b + act[1], eng.ecu.lam_floor, eng.ecu.lam_ceiling))",
    "engine_env.py:1330-1341": ('r_fuel = (base["mdot_fuel"] - out["mdot_fuel"])', "reward = (self.w[1] * r_fuel"),
    "engine_env.py:1332-1332": "t_ref = max(self.torque_req, 40.0)",
    "engine_env.py:1644-1644": "GRADE_RAMP_S = 8.0",
    "engine_specs/b58.toml:67-69": ("flame_lam = { value = 0.90,", "flame_floor = { value = 0.25,"),
    "engine_specs/b58.toml:90-90": 'ua_port = { value = 15.0, unit = "W/K"',
    "engine_specs/b58.toml:143-144": ("lam_floor = { value = 0.70,", "lam_ceiling = { value = 1.25,"),
    "engine_specs/b58.toml:166-167": ("ua_turb_amb = { value = 18.0,", "ua_gas_turb = { value = 0.90,"),
    "engine_specs/b58.toml:201-201": 'lhv_j_per_kg = { value = 44.0e6, unit = "J/kg"',
    "engine_specs/b58.toml:201-202": ("lhv_j_per_kg = { value = 44.0e6,", "afr_st = { value = 14.7,"),
    "engine_specs/b58.toml:202-202": "afr_st = { value = 14.7,",
    # Added 23 October 2026 after the second review of version 4, each read at its line in this tree: the
    # bounds' types (the neutral-action identity), the CVT's kickdown branch (decision 40's diagnostic) and
    # the demand's inputs (C5's transition steps).
    "engines.py:598-602": ('for name in ("lam_floor", "lam_ceiling"):', "NEP 50 makes the type load-bearing"),
    "engines.py:1032-1035": ("def _number(v):", "return float(v)"),
    "engine_specs/b58.toml:119-120": ("spark_min = { value = -10.0,", "spark_max = { value = 46.0,"),
    "engine_env.py:836-852": ("def holds(n):", '"power-limited", n_eco, t_eco'),
    "engine_env.py:1254-1257": ('self.v = float(c["v_mps"][self.k])', 'grade = float(c["grade"][self.k])'),
    # Added 23 October 2026 after the third review of version 4, read at its line in this tree: the step after
    # the last, taken as the step itself (C5's end steps).
    "engine_env.py:1255-1255": 'nxt = float(c["v_mps"][min(self.k + 1, n - 1)])',
}
# The version-3 lines of section 13's table of moves (its middle column), with the text each holds in
# version 3's tree (C.V3_TREE, read through git): written on 23 October 2026 after the second review of
# version 4, each read at its line in `git show ef5e14e:<file>`. claims() fails if the column cites a line
# that is not here, if a pin is not cited there, or if a pinned line does not hold its text.
V3_CITES = {
    "plant.py:42-42": "LHV = 44.0e6",
    "plant.py:43-43": "AFR_STOICH = 14.7",
    "plant.py:54-60": ("def combustion_efficiency(lam):", "return np.clip(1.0 - 0.55 * (lam - 1.08) ** 2"),
    "plant.py:63-66": ("def volumetric_efficiency(rpm, *, engine):", "return np.clip(c.ve_base + c.ve_amp"),
    "plant.py:160-160": "eta_v = volumetric_efficiency(op.rpm, engine=engine)",
    "plant.py:163-163": "m_fuel = m_air / (AFR_STOICH * op.lam)",
    "plant.py:165-165": "t_wall = 0.5 * op.ect_k + 0.5 * (op.ect_k + c.t_head_k)",
    "plant.py:193-193": "theta = np.arange(geo.ivc_deg, geo.evo_deg + dtheta, dtheta)",
    "plant.py:278-281": ("# UA_PORT is the one openly empirical constant here", "UA_PORT = c.ua_port"),
    "plant.py:281-287": ("UA_PORT = c.ua_port", "t_exh = t_wall + (t_blowdown - t_wall) * retained"),
    "plant.py:286-287": ("retained = np.exp(-UA_PORT / max(mdot_exh * CP_EXH, 1.0))",
                         "t_exh = t_wall + (t_blowdown - t_wall) * retained"),
    "thermal.py:245-245": "q_fuel = mdot_fuel_gps * 1e-3 * 44.0e6",
    "thermal.py:265-275": ("# One housing per turbine", "self.t_turb += dt * (q_in_turb - q_out_turb) / p.c_turb"),
    "engine_specs/b58.toml:124-125": ("ua_turb_amb = { value = 18.0,", "ua_gas_turb = { value = 0.90,"),
    "engine_env.py:169-193": ("def knock_limited_spark(self, rpm, map_kpa):", "c.spark_min, c.spark_max))"),
    "engine_env.py:356-376": ("def step(self, rpm, map_kpa, iat_k, ect_k, knock_observed, dt):", "float(lam), fan)"),
    "engine_env.py:690-696": ("def damage_rate(t_turb_k, t_oil_k, knock_integral=None, *, cal):", "return float(d)"),
    "engine_env.py:698-698": "ACT_LO = np.array([-8.0, -0.15,",
    "engine_env.py:711-711": "PREVIEW_S = (",
    "engine_env.py:761-761": "p_exh_kpa=exhaust_backpressure_kpa(map_kpa, engine=eng)",
    "engine_env.py:784-784": "def _track_torque(self, torque_req, rpm,",
    "engine_env.py:982-982": "sp_b, lam_b, fan_b = self.ecu.step(self.rpm, self.map_b_prev,",
    "engine_env.py:1004-1004": "self.spark = float(np.clip(sp_b + act[0],",
    "engine_env.py:1004-1006": ("self.spark = float(np.clip(sp_b + act[0],", "self.lam = float(np.clip(lam_b + act[1], 0.70, 1.25))"),
    "engine_env.py:1006-1006": "self.lam = float(np.clip(lam_b + act[1], 0.70, 1.25))",
    "engine_env.py:1020-1031": ('r_fuel = (base["mdot_fuel"] - out["mdot_fuel"])', "reward = (self.w[1] * r_fuel"),
    "engine_env.py:1022-1022": "t_ref = max(self.torque_req, 40.0)",
}
# What a fit writes (docs/build_step_2/PLAN.md section 8.1): none of it may exist while this contract is
# written (rule 0). The derived files are the EPA engines' only (the B58's is data/derived_params.json).
FIT_OUTPUTS = ("results/EPA_CALIBRATION", "results/EPA_VALIDATION") + tuple(
    f"data/engines/{e}/derived_params.json" for e in ("mazda_25t", "honda_l15b7", "ford_27tt"))


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

    # ---------------------------------------------------------------- 4 and 13, version 4
    pv = contract["version_4"]["plant_values"]
    act = pv["neutral_action_rescaled"]["values"]
    V["NEUTRAL_TRIM"], V["NEUTRAL_DUTY"] = act[0], act[3]
    V["SHARED_RICH_SLOPE"] = pv["shared_rich_slope"]["value"]
    V["B58_LAM_FLOOR"] = pv["b58_lambda_clip"]["lam_floor"]
    V["B58_LAM_CEIL"] = pv["b58_lambda_clip"]["lam_ceiling"]
    V["V3_CLIP_LO"], V["V3_CLIP_HI"] = C.V3_LAM_CLIP
    V["N_THRESHOLDS"] = len(contract["thresholds"])
    V["SCHEMA"] = contract["schema"]
    V["REDRAW_CAP"], V["REDRAW_DISCARDS"], V["E8_MIN_ROWS"] = C.REDRAW_CAP, C.REDRAW_DISCARDS, C.E8_MIN_ROWS
    V["REDRAW_STREAM_TAG"] = f"0x{C.REDRAW_STREAM_TAG:X}"
    # The lists of strings the key-path check does not enter (section 13), counted against version 3's JSON.
    v3 = json.loads(_git_show(C.V3_TREE, "results/ENGINE_THRESHOLDS.json"))
    V["V3_OPEN_N"] = word(len(v3["open_for_the_team"]))
    V["V4_OPEN_N"] = word(len(contract["open_for_the_team"]))
    V["V4_SESSIONS_N"] = word(len(contract["seen_before_writing"]) - len(v3["seen_before_writing"]))
    return V


def _sheet_row(n):
    """The decision sheet's row of decision n (its line that starts '| n ' or '| n (')."""
    with open(os.path.join(common.REPO, SHEET), encoding="utf-8") as fh:
        rows = [l for l in fh.read().splitlines() if l.startswith((f"| {n} |", f"| {n} ("))]
    return rows[0] if len(rows) == 1 else ""


def _neutral_action():
    """The neutral action as the environment applies it: engine_env.neutral_action() through
    SupervisoryTunerEnv._rescale, called unbound (it reads no state of the environment). Imported
    here, not at the top: only version 4's sentences need the environment."""
    import engine_env as E
    return E.SupervisoryTunerEnv._rescale(None, E.neutral_action())


def _git_show(rev, path):
    """A file as commit `rev` holds it (step 7 already needs git: tracked_py)."""
    try:
        return subprocess.run(["git", "show", f"{rev}:{path}"], cwd=common.REPO, capture_output=True,
                              text=True, encoding="utf-8", check=True).stdout
    except (OSError, subprocess.CalledProcessError) as e:
        raise SystemExit(f"document: step 7 reads {path} at {rev} (version 3's tree) and git could not ({e})") from e


def _v3_clip_holds():
    """Version 3's lambda clip, C.V3_LAM_CLIP, is the literal pair of its engine_env.py line 1006."""
    lines = _git_show(C.V3_TREE, "engine_env.py").splitlines()
    lo, hi = C.V3_LAM_CLIP
    return len(lines) >= 1006 and f"np.clip(lam_b + act[1], {lo:.2f}, {hi:.2f})" in lines[1005]


CITE_FILE = r"(?:[\w.\-]+/)*[\w.\-]+\.(?:py|toml|md|txt|csv|json)"
CITE = re.compile(r"(?P<file>" + CITE_FILE + r")(?::(?P<a>\d+)(?:-(?P<b>\d+))?)?"
                  r"|(?<![\w.\])])(?P<bare>:(?P<ba>\d+)(?:-(?P<bb>\d+))?)")


def _cites(text):
    """Every file:line of a text, as 'file:first-last': a bare ':NNN' cites the last file named before
    it in its paragraph (paragraphs are separated by blank lines)."""
    out = []
    for block in re.split(r"\n[ \t]*\n", text.replace("\r\n", "\n")):
        last = None
        for m in CITE.finditer(block):
            if m.group("file"):
                last = m.group("file")
                if m.group("a"):
                    out.append(f"{last}:{m.group('a')}-{m.group('b') or m.group('a')}")
            elif last:
                out.append(f"{last}:{m.group('ba')}-{m.group('bb') or m.group('ba')}")
    return out


def _strings(obj):
    """Every string leaf of a JSON value."""
    if isinstance(obj, dict):
        return [s for v in obj.values() for s in _strings(v)]
    if isinstance(obj, list):
        return [s for v in obj for s in _strings(v)]
    return [obj] if isinstance(obj, str) else []


def _code_cites(contract):
    """The citations of the template and of the JSON's strings into PLANT_CODE and engine_specs/."""
    from fingerprint import PLANT_CODE
    with open(common.TEMPLATE_MD, encoding="utf-8") as fh:
        texts = [fh.read()] + _strings(contract)
    return {c for t in texts for c in _cites(t)
            if c.split(":")[0] in PLANT_CODE or c.startswith("engine_specs/")}


def _pins_that_moved():
    """The pins of CODE_CITES whose line no longer holds its text in this tree."""
    bad, files = [], {}
    for cite, want in sorted(CODE_CITES.items()):
        path, rng = cite.split(":")
        a, b = (int(x) for x in rng.split("-"))
        if path not in files:
            with open(os.path.join(common.REPO, path), encoding="utf-8") as fh:
                files[path] = fh.read().splitlines()
        lines = files[path]
        first, last = (want, None) if isinstance(want, str) else want
        if not (1 <= a <= b <= len(lines) and first in lines[a - 1] and (last is None or last in lines[b - 1])):
            bad.append(cite)
    return bad


V3_TABLE_FILE = re.compile(r"`((?:[\w.\-]+/)*[\w.\-]+\.(?:py|toml))`")
V3_TABLE_LINES = re.compile(r"(?<![\w.])(\d+)(?:-(\d+))?(?![\w.])")


def _v3_table_cites():
    """The version-3 lines section 13's table of moves cites: its middle column, each number or range
    read against the last file named before it in the cell, as 'file:first-last'."""
    with open(common.TEMPLATE_MD, encoding="utf-8") as fh:
        text = fh.read().replace("\r\n", "\n")
    rows = text[text.index("## 13. Version 4:"):].split("\n")
    start = next(i for i, l in enumerate(rows) if l.startswith("| what is cited | version 3"))
    out = set()
    for line in rows[start + 2:]:
        if not line.startswith("|"):
            break
        cell, last = line.split("|")[2], None
        for m in re.finditer(V3_TABLE_FILE.pattern + "|" + V3_TABLE_LINES.pattern, cell):
            if m.group(1):
                last = m.group(1)
            elif last:
                out.add(f"{last}:{m.group(2)}-{m.group(3) or m.group(2)}")
    return out


def _v3_pins_that_fail():
    """The pins of V3_CITES whose line does not hold its text in version 3's tree."""
    bad, files = [], {}
    for cite, want in sorted(V3_CITES.items()):
        path, rng = cite.split(":")
        a, b = (int(x) for x in rng.split("-"))
        if path not in files:
            files[path] = _git_show(C.V3_TREE, path).splitlines()
        lines = files[path]
        first, last = (want, None) if isinstance(want, str) else want
        if not (1 <= a <= b <= len(lines) and first in lines[a - 1] and (last is None or last in lines[b - 1])):
            bad.append(cite)
    return bad


# Every citation of the decision sheet in the .md and the JSON, by its line range, with the text its first line
# must hold (and, for a range, its last): the row of the decision it cites, by number and name, which filling a
# column leaves in place, so that only a line that moved stops step 7. Written on 23 October 2026 after version
# 4's fourth review, each read at its line in this tree. claims() fails if a citation is not here, if a pin is no
# longer cited, or if a pinned line no longer holds its text.
SHEET = "results/VALIDATION_DECISIONS.md"
SHEET_CITES = {
    "53-53": "| 3 | Required accuracies |",
    "55-55": "| 5 | Relative damage only |",
    "132-132": "| 24 | The plants of the H/τ test |",
    "142-143": ("a tabulated B58 trains 6–8 times faster per run", "frozen-twenty cut within 1.5 points of the exact plant"),
    "149-149": "| 26 | Verdicts |",
    "151-151": "| 28 | Training and scoring backend |",
    "154-154": "| 31 | Which B58 the test uses |",
    "156-156": "| 33 | The damage knee per engine |",
    "157-157": "| 34 | The test roads (revised 21 October",
    "158-158": "| 35 | Validation thresholds for the new engines |",
}


def _sheet_cites(contract, V):
    """(not pinned, pinned but not cited, pinned lines that no longer hold their text): the citations of the
    decision sheet in the .md and the JSON's strings, against SHEET_CITES."""
    md = _rendered(V)
    cited = {cite.rsplit(":", 1)[1] for cite in _cites(md) + [c for s in _strings(contract) for c in _cites(s)]
             if cite.rsplit(":", 1)[0] in (SHEET, SHEET.split("/", 1)[1])}
    with open(os.path.join(common.REPO, SHEET), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    moved = []
    for rng, want in sorted(SHEET_CITES.items()):
        a, b = (int(x) for x in rng.split("-"))
        first, last = (want, None) if isinstance(want, str) else want
        if not (1 <= a <= b <= len(lines) and first in lines[a - 1] and (last is None or last in lines[b - 1])):
            moved.append(rng)
    return sorted(cited - set(SHEET_CITES)), sorted(set(SHEET_CITES) - cited), moved


# The files the .md's Appendix A quotes from outside the repository, which no scan of this tree can
# resolve: the team's data folder's catalogue and the scratch folder of section 9 (fe_out/), whose files
# the JSON also names without the folder.
OUTSIDE_CITED = ("CATALOGUE.md", "fe_out/design.md", "fe_out/strand_repo-stats-timing.md", "fe_out/strand_vehicles.md")
EPA_TABLE = re.compile(r"(^|/)epa_[^/]*\.csv$")


def _rendered(V):
    """The .md this step writes, from the template and the values (render_with fills it again)."""
    with open(common.TEMPLATE_MD, encoding="utf-8") as fh:
        template = fh.read().replace("\r\n", "\n")
    if template.startswith(TEMPLATE_NOTE):
        template = template.split("\n", 1)[1]
    return fill(template, V)


def _citation_scan(contract, V):
    """Every file:line of the .md and of the JSON's strings, resolved against this tree (amendment A3's
    scan): (failures, counts). A citation resolves if it names a file of the repository, as written or
    under results/, that has the cited lines; an EPA table (data/engines/<id>/epa_*.csv) by its existence
    alone, since the generator opens no epa_channels.csv; or a file of OUTSIDE_CITED, which Appendix A
    must name. Only the range is checked, not the text (the code citations' text is CODE_CITES')."""
    md = _rendered(V)
    appendix = md[md.index("## Appendix A."):]
    bad, counts, lines = [], dict(repository=0, epa_table=0, outside=0), {}
    for cite in _cites(md) + [c for s in _strings(contract) for c in _cites(s)]:
        path, rng = cite.rsplit(":", 1)
        a, b = (int(x) for x in rng.split("-"))
        outside = next((o for o in OUTSIDE_CITED if path == o or path == o.split("/")[-1]), None)
        if outside:
            folder = outside.rsplit("/", 1)[0] + "/" if "/" in outside else ""
            if outside.split("/")[-1] not in appendix or folder not in appendix:
                bad.append(f"{cite} (outside the repository, and not a file Appendix A quotes)")
            counts["outside"] += 1
            continue
        rel = next((p for p in (path, "results/" + path) if os.path.isfile(os.path.join(common.REPO, p))), None)
        if rel is None:
            bad.append(f"{cite} (no such file)")
            continue
        if EPA_TABLE.search(rel):
            counts["epa_table"] += 1
            continue
        if rel not in lines:
            with open(os.path.join(common.REPO, rel), encoding="utf-8", errors="replace") as fh:
                lines[rel] = len(fh.read().splitlines())
        if not 1 <= a <= b <= lines[rel]:
            bad.append(f"{cite} ({rel} has {lines[rel]} lines)")
        counts["repository"] += 1
    return bad, counts


def _digest(obj):
    """sha256 of a JSON value, keys sorted (V3_DIGESTS)."""
    return hashlib.sha256(json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()


def _key_paths(obj, pre=""):
    """Every dict key path of a JSON value, list entries included by index:
    'model_form.lambda_clip_floor', 'cars[7].threshold.cvt'."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{pre}.{k}" if pre else k
            out.append(p)
            out += _key_paths(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out += _key_paths(v, f"{pre}[{i}]")
    return out


def _c5_cases(share, n_max=12):
    """C5's outcome on a car (cars C5 steps.outcome, written after version 4's seventh review), as its three cases
    word it, over every climb of 1..n_max steps, every count of gated steps, and a failing gated margin or none:
    True if exactly one case holds each time and a passing climb has a gated step."""
    for n in range(1, n_max + 1):
        for g in range(n + 1):
            for fail in ((False, True) if g else (False,)):
                fails = fail                                    # (1) some gated margin at or below the margin
                thinly_checked = not fail and g < share * n     # (2) none, and gated steps fewer than share x steps
                passes = not fail and not g < share * n         # (3) neither
                if fails + thinly_checked + passes != 1 or (passes and g == 0):
                    return False
    return True


def _section_13(V):
    """Section 13 of the .md, its whitespace collapsed, so that a phrase the wrap splits is found."""
    md = _rendered(V)
    return " ".join(md[md.index("## 13. Version 4"):md.index("## Appendix A")].split())


def _version_3_kept(contract):
    """(what, holds) for each part of version 3's JSON that version 4 keeps (section 13)."""
    t = contract["thresholds"]
    old_paths = sorted(p for p in _key_paths(contract)
                       if not any(p == k or p.startswith(k + ".") or p.startswith(k + "[") for k in V4_NEW_KEYS))
    return [
        ("the per-threshold values (engine, row, kind, part, R, unit)",
         _digest([[x["engine"], x["row"], x["kind"], x["part"], x["R"], x["unit"]] for x in t]) == V3_DIGESTS["per_threshold"]),
        ("every thresholds entry but C5's, D1's and E8's",
         _digest([x for x in t if x["row"] not in ("C5", "D1", "E8")]) == V3_DIGESTS["non_c5_d1_e8"]),
        ("D1's and E8's entries but for statistic",
         _digest([{k: v for k, v in x.items() if k != "statistic"} for x in t if x["row"] in ("D1", "E8")])
         == V3_DIGESTS["d1_e8_rest"]),
        ("C5's entries but for statistic and on_fail",
         _digest([{k: v for k, v in x.items() if k not in ("statistic", "on_fail")} for x in t if x["row"] == "C5"])
         == V3_DIGESTS["c5_rest"]),
        ("the engines section", _digest(contract["engines"]) == V3_DIGESTS["engines"]),
        ("the step outputs and the EPA tables (generator_inputs_sha256, epa_tables_sha256)",
         _digest([contract["generator_inputs_sha256"], contract["epa_tables_sha256"]]) == V3_DIGESTS["inputs"]),
        ("every key of version 3, and no key but V4_NEW_KEYS added",
         hashlib.sha256("\n".join(old_paths).encode("utf-8")).hexdigest() == V3_DIGESTS["key_paths"]),
    ]


def claims(V, contract, ns, inp):
    """(sentence, holds) for every sentence whose words depend on a computed number."""
    import engines
    split, K3 = inp["split"], inp["K3"]
    resp_s_fix = dict(ns["RESP_S_FIX"])
    W = ns["W"]
    act = _neutral_action()
    cited = _code_cites(contract)
    unpinned, stale = cited - set(CODE_CITES), set(CODE_CITES) - cited
    moved = _pins_that_moved()
    v3_cited = _v3_table_cites()
    v3_unpinned, v3_stale = v3_cited - set(V3_CITES), set(V3_CITES) - v3_cited
    v3_bad = _v3_pins_that_fail()
    fit_outputs = [p for p in FIT_OUTPUTS if os.path.exists(os.path.join(common.REPO, p))]
    scan_bad, _ = _citation_scan(contract, V)
    sheet_unpinned, sheet_stale, sheet_moved = _sheet_cites(contract, V)
    row76 = _sheet_row(76)
    redraw = next(r for r in contract["cars"] if r["id"] == "C5")["redraw"]
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
        ("4: the neutral action's spark, lambda and boost trims rescale to exactly 0.0 in float32, its fan and pump to 1.0",
         act.dtype.name == "float32" and all(float(x) == 0.0 for x in act[:3]) and float(act[3]) == float(act[4]) == 1.0
         and (V["NEUTRAL_TRIM"], V["NEUTRAL_DUTY"]) == (0.0, 1.0)),
        ("4: E6 row 9's 'the shared 0.65' (the JSON's band) is engines.SHARED_RICH_SLOPE",
         f"the shared {V['SHARED_RICH_SLOPE']:g};" in next(r["band"] for r in contract["perturbations_E6"] if r["n"] == 9)
         and V["SHARED_RICH_SLOPE"] == engines.SHARED_RICH_SLOPE),
        ("4 and 13: version_4.plant_values is what the plant code gives in this tree",
         contract["version_4"]["plant_values"] == C.plant_values()),
        ("4: the B58 clips at version 3's shared bounds, the literals of ef5e14e's engine_env.py line 1006",
         (V["B58_LAM_FLOOR"], V["B58_LAM_CEIL"]) == C.V3_LAM_CLIP and _v3_clip_holds()),
        ("3 and 4: E8's subset minimum is the clusters a line needs (thresholds/split.py MIN_CLUSTERS)",
         C.E8_MIN_ROWS == S.MIN_CLUSTERS),
        ("4: 'Version 3's one population never fell short': every engine's held-out Final rows reach E8's subset minimum",
         all(split[e]["pooled_counts"]["E8_final_rows"] >= C.E8_MIN_ROWS for e in common.EPA_ENGINES)),
        ("5: 'fewer than half its steps': the JSON's thin_below_share is one half",
         C.C5_THIN_SHARE == 0.5 and next(r for r in contract["cars"] if r["id"] == "C5")["steps"]["thin_below_share"] == 0.5),
        ("5: the cap and the discard bound are the sheet's row 76 and the JSON's (decision 76)",
         f"**At most {C.REDRAW_CAP} redraws per climb slot" in row76
         and f"at most {C.REDRAW_DISCARDS} candidates discarded per slot" in row76
         and (redraw["cap_redraws"], redraw["discards_max"]) == (C.REDRAW_CAP, C.REDRAW_DISCARDS)),
        ("5: 'three redraws ... one in eight at p = 1/2' is the cap's arithmetic", C.REDRAW_CAP == 3 and 0.5 ** C.REDRAW_CAP == 1 / 8),
        ("5 and 13: the redraw streams' generator, default_rng([roads_seed, tag, k]), names the JSON's stream_tag, "
         "and the sheet's row 76 and the JSON's decision 76 name the same",
         redraw["stream_tag"] == C.REDRAW_STREAM_TAG
         and f"default_rng([roads_seed, {V['REDRAW_STREAM_TAG']}, k])" in row76
         and f"default_rng([roads_seed, {V['REDRAW_STREAM_TAG']}, k])" in contract["decisions"]["76"]
         and f"default_rng([roads_seed, {V['REDRAW_STREAM_TAG']}, k])" in " ".join(_rendered(V).split())),
        ("5: C5's three outcomes (cars C5 steps.outcome) are exclusive and every climb is in one, by their case table over "
         "climbs of 1-12 steps, every count of gated steps and a failing gated margin or none; a passing climb has a gated "
         "step; and the JSON words the three cases so",
         _c5_cases(C.C5_THIN_SHARE)
         and all(p in next(r for r in contract["cars"] if r["id"] == "C5")["steps"]["outcome"]
                 for p in ("(1) it fails when some gated margin", "(2) it is thinly checked when no gated margin is at or "
                           "below the margin and its gated steps on the car are fewer than thin_below_share of its steps",
                           "(3) it passes when neither holds"))),
        ("13: the values decisions 54 and 57 state are the JSON's conventions' (lambda 1.00 without lambda, the -120 "
         "sentinel, censoring at 2 rows within 1e-9, D1's 10 kPa pre-scan and 1e-3 kPa bisection), and section 13 lists each",
         all(js in (contract["conventions"][k] if "." not in k else contract["conventions"][k.split(".")[0]][k.split(".")[1]])
             and md in _section_13(V) for k, js, md in V4_DECISION_VALUES)),
        ("13: 'four rule constants': the cap, the discard bound, the thin share and E8's subset minimum are the JSON's",
         (redraw["cap_redraws"], redraw["discards_max"],
          next(r for r in contract["cars"] if r["id"] == "C5")["steps"]["thin_below_share"],
          contract["conventions"]["statistic_details"]["e8_min_rows"])
         == (C.REDRAW_CAP, C.REDRAW_DISCARDS, C.C5_THIN_SHARE, C.E8_MIN_ROWS)),
        ("1 and 13: 'version 4's nine' sessions are seen_before_writing's entries added since version 3",
         V["V4_SESSIONS_N"] == "nine" and "and version 4's nine, of 22 October" in _rendered(V)),
        ("13: the JSON's schema is 4, and version_4 is its record", V["SCHEMA"] == 4 and "version_4" in contract),
        ("13: every code citation into PLANT_CODE and engine_specs/ is pinned in CODE_CITES, and every pin is cited"
         + (f" (not pinned: {sorted(unpinned)}; pinned, not cited: {sorted(stale)})" if unpinned or stale else ""),
         not unpinned and not stale),
        ("13: every pinned code citation's line holds its text in this tree" + (f" (moved: {moved})" if moved else ""),
         not moved),
        ("13: the table's version-3 column cites exactly the lines pinned in V3_CITES"
         + (f" (not pinned: {sorted(v3_unpinned)}; pinned, not cited: {sorted(v3_stale)})" if v3_unpinned or v3_stale else ""),
         bool(v3_cited) and not v3_unpinned and not v3_stale),
        (f"13: every V3_CITES line holds its text in {C.V3_TREE}'s tree" + (f" (fails: {v3_bad})" if v3_bad else ""),
         not v3_bad),
        ("13: every file:line of the .md and the JSON resolves: a repository file that has the cited lines (as written "
         "or under results/), an EPA table by its existence alone, or a file Appendix A quotes from outside the repository"
         + (f" (fails: {scan_bad})" if scan_bad else ""), not scan_bad),
        ("13: every citation of the decision sheet is pinned in SHEET_CITES, every pin is cited, and each pinned line "
         "holds its row's text in this tree"
         + (f" (not pinned: {sheet_unpinned}; pinned, not cited: {sheet_stale}; moved: {sheet_moved})"
            if sheet_unpinned or sheet_stale or sheet_moved else ""),
         not sheet_unpinned and not sheet_stale and not sheet_moved),
    ] + [(f"13: version 3's {what} is version 4's", ok) for what, ok in _version_3_kept(contract)] + [
        ("Nothing has been fitted: calibrate_epa.py does not exist", not os.path.exists(os.path.join(common.REPO, "calibrate_epa.py"))),
        ("Nothing has been fitted: the .py files that name the EPA tables are epa_map.py, test_epa_map.py and "
         "this generator", {p for p in tracked_py() if _names_epa_tables(p) and not _is_generator(p)}
         == {"epa_map.py", "test_epa_map.py"}),
        ("Nothing has been fitted: nothing a fit writes exists (results/EPA_CALIBRATION/, results/EPA_VALIDATION/, an "
         "EPA engine's derived_params.json)" + (f" (exists: {fit_outputs})" if fit_outputs else ""), not fit_outputs),
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
    _, n = _citation_scan(contract, V)
    print(f"citations of the .md and the JSON: {sum(n.values())} resolved ({n['repository']} in the repository, "
          f"{n['epa_table']} of EPA tables by their existence, {n['outside']} of files outside it that Appendix A quotes)")
    return text
