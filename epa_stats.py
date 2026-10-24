"""epa_stats.py -- every statistic of the validation contract, one definition for the in-sample
stage and the held-out run (build step 2, WP3; written 23 October 2026).

WHAT IT IS. Arithmetic over rows and over a model object it is given: the contract's section 3
(inputs, lambda, the rows without a reading, censoring, the line and cluster rules, u_val and its
three terms, the labels) and section 4 (E1-E5, D1, L0, L1, E8, E6's helpers), section 5's C5
margin, and section 7's labels and band factor kappa, as results/ENGINE_THRESHOLDS.md and .json
version 5 (commit c842d74, which kept every one of version 4's rules but the in-sample criterion and
added decision 77's) write them, with docs/build_step_2/AMENDMENTS.md, HANDOFFS.md, section H of
results/VALIDATION_DECISIONS.md (decisions 39-77) and docs/build_step_2/WP3_INTERFACES.md section 5.2,
which this module implements.

ONE DEFINITION (mistake 10). calibrate_epa.py's in-sample stage (through epa_fit) and
validate_epa.py's held-out run call the same row functions, row_E1a ... row_E8, on RowEvals of
calibration or held-out rows; nothing here knows which rows it was given except through `stage`,
which only picks the R (L1's tightening, E8's roads table) and whether u-terms and labels are
attached (held_out_row). The in-sample rows are fit residuals: no u_val, never labelled (contract
section 2.4; PLAN.md 5.5); their u_stat, the held-out run's own (each core's comp_se), enters the form
criterion only, by decision 77 (in_sample_outcome).

WHAT IT NEVER DOES. It opens no file, fits nothing, and runs no model itself: the model is the
object passed in (section 5.2.2 of WP3_INTERFACES.md; epa_fit.RowModel in production, a closed-form
toy in its tests). It imports no plant module but engine_env, for C5's gearbox only, and takes the
split's constants through epa_rows, never from thresholds/split.py itself (amendment C2).

UNITS. A relative error is reported in percent (the unit of its R: 1.9 % for E1a, 16.6 % for D1);
a temperature error in K; TIT in degC (plant.CycleResult.egt_c's unit, WP3_INTERFACES.md 2.9).
D1's delta_D and L0's delta-bar are fractions inside their formulas, as the contract writes them
(|f e + f(1 - f) G delta|).

Nothing in this file has seen an EPA table value: every number below is the contract's or a
declared DESIGN value with its reason, except the instrument uncertainties EPA's test reports state
(decision 56: U_INPUT and U_D, each CellPin quoting its report's Table 8 row; SOURCES_READ lists what
their author read, and no EPA table or workbook is among it).
"""
import dataclasses
import math
import re
from dataclasses import dataclass, replace
from typing import Mapping

import numpy as np

import engine_env
import epa_rows
from thresholds.contract import interp

# ---------------------------------------------------------------------------------------------
# The split's constants, through epa_rows (amendment C2: only epa_rows imports thresholds.split).
# ---------------------------------------------------------------------------------------------
LAM_BAND = epa_rows.LAM_BAND          # 0.02: |lambda - lambda_ref| <= LAM_BAND is lambda~1, and the snap
LAM_ENR = epa_rows.LAM_ENR            # 0.05: lambda <= lambda_ref - LAM_ENR is enriched
TOL = epa_rows.TOL                    # 1e-9: the split's comparison tolerance
MIN_CLUSTERS = epa_rows.MIN_CLUSTERS  # 3: a line decides with at least this many clusters
MAP_SPLIT = epa_rows.MAP_SPLIT        # 100 kPa: boosted against throttled (E4b, E5)
FIRED_BMEP = epa_rows.FIRED_BMEP      # 2 bar: fired (E5 window A)
MAP_BAND = epa_rows.MAP_BAND          # 20 kPa: the coverage bands (decision 58)

# ---------------------------------------------------------------------------------------------
# The contract's fixed numbers this module applies (version 5's, which are version 4's: no number moved)
# ---------------------------------------------------------------------------------------------
# D1's inversion (decision 57; conventions.statistic_details.d1): a pre-scan of the model's torque over
# 20-400 kPa every 10 kPa, bisection of the first bracket to 1e-3 kPa, the nearer bound when none.
D1_SCAN_KPA = tuple(float(p) for p in range(20, 401, 10))
D1_BISECT_KPA = 1e-3
# s = (base_spark(MAP_E + 2) - base_spark(MAP_E - 2)) / 4: the central difference +-2 kPa (contract section 4, D1)
D1_SPARK_DIFF_KPA = 2.0
# The label order of E6 row 12 and decision 59, worst last: off > untested > limited > validated.
LABEL_ORDER = ("validated", "limited", "untested", "off")
# Every d row carries this condition (contract section 1.2a; JSON rows, d entries).
D_CONDITION = "both arms' cuts in 0-0.865"
# The rows the contract computes, by kind (contract's table of thresholds). E6 and the C rows are elsewhere.
KIND = {"E1a": "level", "E2a": "level", "E3a": "level", "E4a": "level", "L0": "level",
        "D1": "d", "E4b": "d", "L1": "d", "E8": "d",
        "E1b": "descriptive", "E1i": "descriptive", "E2b": "descriptive", "E3b": "descriptive",
        "E5": "descriptive"}
LEVEL_ROWS = ("E1a", "E2a", "E3a", "E4a", "L0")
# Section 7's parts and their d rows (contract section 1.3; JSON budget.parts).
PARTS = (("P1", ("D1",)), ("P2", ("E4b",)), ("P3", ("L1",)), ("P4", ("E8",)), ("P5", ("C3b", "C3d")))
# The in-sample stage's statistics (contract section 2.4; PLAN.md 5.5), E8 reported outside the criterion.
IN_SAMPLE_ROWS = ("E1a", "E2a", "E3a", "E4a", "E4b", "D1", "L0", "L1", "E8")
IN_SAMPLE_CRITERION = ("each engine's form is the first of A, A+B, A+B+C, A+B+C+D at which no in-sample "
                       "statistic but E8 fails. A statistic fails a form only if |E_cal| - 2 u_stat > R, on its "
                       "pooled value or on any of its deciding lines, u_stat the standard error the held-out rows "
                       "compute (the standard error of the mean with one row or hold per cluster, the pooled "
                       "u_stat for pooled rows, L0 at its maximising f, L1 from its two extreme lines); it passes "
                       "if it does not fail and its pooled value or some deciding line has 2 u_stat <= R; "
                       "otherwise (2 u_stat > R, or u_stat undefined) it neither blocks a form nor passes it, "
                       "recorded per form, as a statistic with no calibration line that meets its population's "
                       "line minimum neither blocks nor passes (contract section 2.4; JSON "
                       "model_form.in_sample_rules: decisions 39(a), 49, 55; decision 77, 23 October 2026; L1 at "
                       "its untightened R, decision 71)")
# Decision 77's three outcomes of one in-sample component or statistic (in_sample_outcome; in_sample_judgement).
IN_SAMPLE_OUTCOMES = ("fails", "passes", "neither")
# Why a component neither blocks nor passes (decision 77): its noise exceeds R, or it has no standard error at all
# (E4b on fewer than 2 enriched rows: the held-out run's u_stat None, declared in epa_fit.NO_STATISTIC_OUTCOMES).
NOISE_EXCEEDS_R = "noise exceeds R: 2 u_stat > R"
NO_U_STAT = "no u_stat: the standard error is undefined (fewer than 2 rows on the side that needs one)"
FAILS_BEYOND_NOISE = "|E_cal| - 2 u_stat > R"
INPUT_CHANNELS = ("speed", "map", "imt", "ect", "spark", "lam")
NEEDS = frozenset({"at_epa", "d1", "lam1", "ecu"})


# =============================================================================================
# 5.2.6 (first): the uncertainty terms, pinned (decision 56)
# =============================================================================================
# EPA's own words are the source wherever a report states a channel's uncertainty (contract section 3: "u_D
# comes from EPA's stated accuracy where its reports give one"; PLAN.md 6.2: "u_j is EPA's stated accuracy if
# its instrument pages give one"). The reports state it per report, so the pins are per report: each test
# report has its own Table 8, "Standard Uncertainties for Signals", and the numbers differ between them (the
# torque's 0.127 N m on the Mazda against 1.591 N m on the Ford's HD1). A row reads the pin of the report its
# readings came from, which it carries as its provenance does: (engine, test_cell), the cell as epa_map.py
# writes each workbook's `cell` into every row (epa_rows.PROVENANCE; logs/epa/README.md). The Ford ran in two
# cells, Cell 9's steady state and HD1's steady state and high load, each with its own report. A cell label is
# not a table name (WP3_INTERFACES.md 2.8): the tables stay epa_rows.TABLES'.
#
# What the reports mean by the columns (each report's section Uncertainty, "Sensor/signal uncertainties"): "The
# uncertainties of the signals [u(signal)] in the data set can be based on (a) the uncertainty associated with
# the calibration standard, (b) the uncertainty of the sensor calibration [u(calibration)], and (c) the
# uncertainty of the signal during operation [u(operation)]", and u(signal) is their root sum of squares. A pin
# takes u(signal) where the report prints it, and u(calibration) where that is all it prints (HD1). The
# reports were read on 23 October 2026 (SOURCES_READ); a channel no report states keeps the contract's
# fallback, marked unsourced.
MAZDA_CELL9 = ("mazda_25t", "Test Cell 9")
HONDA_CELL7 = ("honda_l15b7", "Test Cell 7")
FORD_CELL9 = ("ford_27tt", "Test Cell 9")
FORD_HD1 = ("ford_27tt", "Test Cell HD1")
REPORTS = {
    MAZDA_CELL9: "logs/epa/mazda_25t/3a- 2016 Mazda 2.5L Turbo Skyactiv-G Engine Tier 2 Fuel - Test Report.docx",
    HONDA_CELL7: "logs/epa/honda_l15b7/3a- 2016 Honda 1.5L L15B7 Engine Tier 2 Fuel - Test Report.docx",
    FORD_CELL9: ("logs/epa/ford_27tt/3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel Cell 9 - Test "
                 "Report.docx"),
    FORD_HD1: "logs/epa/ford_27tt/3- 2015 Ford 2.7L EcoBoost V6 Engine Tier 2 Fuel HD1 - Test Report.docx",
}
REPORT_CELLS = tuple(REPORTS)
# Where each report's Table 8 is (the page its own table of contents prints for the section Uncertainty), its
# header line, and the sentence that introduces it, verbatim but for " | " between the table's cells.
_T8_WHERE = {
    MAZDA_CELL9: "section Uncertainty (table of contents: page 21), Table 8: Standard Uncertainties for Signals",
    HONDA_CELL7: "section Uncertainty (table of contents: page 26), Table 8: Standard Uncertainties for Signals",
    FORD_CELL9: "section Uncertainty (table of contents: page 13), Table 8: Standard Uncertainties for Signals",
    FORD_HD1: "section Uncertainty (table of contents: page 13), Table 8: Standard Uncertainties for Signals",
}
_T8_HEADER = {
    MAZDA_CELL9: "Signal | u(calibration) | u(correlation) average (ref) | u(operation) average (ref) | u(signal)",
    HONDA_CELL7: "Signal | u(calibration) | u(operation) average (ref) | u(signal)",
    FORD_CELL9: "Signal | u(calibration) | u(operation) | u(signal)",
    FORD_HD1: "Signal | u(calibration)",
}
_T8_NOTE = {
    MAZDA_CELL9: ("Table 8 provides standard uncertainties for each signal.  In the case of the operational "
                  "uncertainty of the signals and the transient correlation (when applicable), the average values "
                  "over the data set are given for reference. Within the data set, these uncertainties were "
                  "calculated individually for each mode."),
    HONDA_CELL7: ("The operational uncertainty of the signals is calculated for each mode.  The nominal "
                  "uncertainty for each signal is given in Table 8, using an average u(operation) for each "
                  "signal."),
    FORD_CELL9: "Assuming n = 70 (a minimum number), the standard uncertainty for each signal is given in Table 8.",
    FORD_HD1: ("The calibration uncertainty for each signal is given in Table 8. [...] Both the standard deviation "
               "and the number of data points vary from mode to mode. The standard uncertainty from each signal "
               "can be calculated as the geometric sum of the calibration and operation uncertainties"),
}


@dataclass(frozen=True)
class CellPin:
    """EPA's stated standard uncertainty of one channel in one test report (decision 56). `printed` is the
    number as the report prints it (value == float(printed)); `column` the Table 8 column it is read from,
    "u(signal)" or, where the report prints no other (HD1), "u(calibration)"; `row` that table row and `header`
    the table's header, verbatim but for " | " between cells; `note` the report's sentence on the table; `file`
    the report (REPORTS) and `where` the section and table. test_epa_stats.Pins reads each value back out of its
    own row."""
    value: float
    printed: str
    column: str
    file: str
    where: str
    header: str
    row: str
    note: str


def _t8(cell, row, column="u(signal)"):
    """((engine, test_cell), CellPin) for one Table 8 row of that report: the number is the row's own cell
    under `column`, never typed apart from the quote (mistake 10)."""
    head = _T8_HEADER[cell]
    printed = row.split(" | ")[head.split(" | ").index(column)]
    return (cell, CellPin(value=float(printed), printed=printed, column=column, file=REPORTS[cell],
                          where=_T8_WHERE[cell], header=head, row=row, note=_T8_NOTE[cell]))


def cell_of(x):
    """(engine, test_cell) of a row or a RowEval: the report its readings came from (decision 56). A synthetic
    row carries no report cell, and reads every term's fallback (or refuses one with none)."""
    return (getattr(x, "engine", None), getattr(x, "test_cell", None))


@dataclass(frozen=True)
class UInput:
    """One input channel's standard uncertainty of one reading (contract section 3, u_input; PLAN.md 6.2;
    decision 56), in the channel's unit (rpm, kPa, K, CAD BTDC, lambda). `cells` holds EPA's stated value per
    report, ((engine, test_cell), CellPin); `value`, `kind`, `source` and `unsourced` are the contract's
    fallback (the steady table's resolution/sqrt(12), or spark's declared floor), read by a row whose report
    states nothing for the channel, and marked unsourced. Also the step of the central difference: a shifted row
    is the row with this channel moved by +-u at its own report (input_shifts)."""
    value: float
    kind: str
    source: str
    unsourced: bool
    cells: tuple = ()

    def at(self, cell):
        """(u, unsourced) for a reading of `cell` ((engine, test_cell)): its report's pin, else the fallback."""
        for k, p in self.cells:
            if k == cell:
                return float(p.value), False
        return float(self.value), bool(self.unsourced)


@dataclass(frozen=True)
class UD:
    """One measured channel's u_D (contract section 3, u_D; PLAN.md 6.2). `cells` holds EPA's stated value per
    report, ((engine, test_cell), CellPin), absolute in the channel's unit; `value` (absolute) or `rel` (a
    fraction of |reading|, the thermocouple's class tolerance) is the fallback for a row whose report states
    nothing, `unsourced` its mark. A row with neither its report's pin nor a fallback is NOT PINNED, and any
    statistic that reads that channel refuses to compute its u_D (mistake 9: never hand back a number as if it
    held)."""
    value: float | None
    rel: float | None
    part: str          # "common" (every row moved together) or "random" (per cluster)
    kind: str
    source: str
    unsourced: bool
    cells: tuple = ()

    def at(self, cell):
        """(value, rel, unsourced) for a reading of `cell`: its report's pin (absolute), else the fallback; None
        when neither is pinned."""
        for k, p in self.cells:
            if k == cell:
                return float(p.value), None, False
        if self.value is None and self.rel is None:
            return None
        return self.value, self.rel, bool(self.unsourced)

    def pinned_for_every_report(self):
        """Whether every report's rows have a pin: a fallback, or a CellPin for each of REPORT_CELLS."""
        return (self.value is not None or self.rel is not None
                or set(REPORT_CELLS) <= {k for k, _ in self.cells})


_RES = "resolution/sqrt(12)"
_RES_SOURCE = ("docs/build_step_2/PLAN.md section 6.2: the steady table's printed resolution, as the plan types "
               "it (lambda 0.01, MAP 0.01 kPa, temperature 0.1 C, speed 1 rpm), never read from repr digits "
               "(epa_map.py:308-314); the fallback for a row whose report states nothing for the channel (the "
               "four test reports, their ALPHA pages and fuel analyses were read on 23 October 2026, "
               "SOURCES_READ)")
_NONE_STATED = ("not stated: the four Table 8s list speed, torque and fuel (the Ford Cell 9's adds temperature "
                "and pressure), and no other page of the reports, the ALPHA pages or the fuel analyses gives an "
                "accuracy for any channel")
# Pinned 23 October 2026 (decision 56): EPA's stated value where its report prints one (CellPin, quoted), else
# the contract's fallback, unsourced. Every report states speed; only the Ford's Cell 9 report states pressure
# and temperature, as generic rows ("Pressure (kPa)", "Temperature (deg C)"), here applied to MAP and to the
# intake and coolant temperatures of that cell's rows. A row of an unknown cell (a synthetic row) reads the
# fallback, and its statistic lists the channel as unsourced: in a real run, "u_input speed" in that list is the
# tell that a row missed its report (mistake 19).
U_INPUT = {
    "speed": UInput(1.0 / math.sqrt(12.0), _RES, _RES_SOURCE + "; speed 1 rpm", True, cells=(
        _t8(MAZDA_CELL9, "Speed (rpm) | 0.998 | - | 0.0676 | 1.000"),
        _t8(HONDA_CELL7, "Speed (rpm) | 0.289 | 0.0878 | 0.302"),
        _t8(FORD_CELL9, "Speed (rpm) | 1.183 | 0.178 | 1.197"),
        _t8(FORD_HD1, "Speed (rpm) | 0.637", column="u(calibration)"))),
    "map": UInput(0.01 / math.sqrt(12.0), _RES, _RES_SOURCE + "; MAP 0.01 kPa; the Mazda's, the Honda's and HD1's "
                  "reports: " + _NONE_STATED, True, cells=(
                      _t8(FORD_CELL9, "Pressure (kPa) | 0.321 | 0.0053 | 0.321"),)),
    "imt": UInput(0.1 / math.sqrt(12.0), _RES, _RES_SOURCE + "; intake temperature 0.1 C; the Mazda's, the Honda's "
                  "and HD1's reports: " + _NONE_STATED, True, cells=(
                      _t8(FORD_CELL9, "Temperature (deg C) | 0.549 | 0.225 | 0.593"),)),
    "ect": UInput(0.1 / math.sqrt(12.0), _RES, _RES_SOURCE + "; coolant temperature 0.1 C; the Mazda's, the "
                  "Honda's and HD1's reports: " + _NONE_STATED, True, cells=(
                      _t8(FORD_CELL9, "Temperature (deg C) | 0.549 | 0.225 | 0.593"),)),
    # WP3_INTERFACES.md 5.2.6, chosen there: no page states spark's accuracy, so a declared 0.1 CAD resolution
    "spark": UInput(0.1 / math.sqrt(12.0), "declared floor, unsourced",
                    "WP3_INTERFACES.md 5.2.6: a declared resolution of 0.1 CAD; " + _NONE_STATED, True),
    "lam": UInput(0.01 / math.sqrt(12.0), _RES, _RES_SOURCE + "; lambda 0.01; " + _NONE_STATED, True),
}
U_D = {
    # IEC 60584-1 class 2, +-0.0075 |t| as a uniform half-width, common (contract section 3: "the class is not
    # stated for EPA's sensors, and the standard was not opened in this project"): 3.5 K at 800 C. No report
    # states a thermocouple's class or accuracy. The Ford Cell 9 report's generic row "Temperature (deg C) |
    # 0.549 | 0.225 | 0.593" names no sensor and no range, and is NOT applied to the turbine-inlet thermocouple
    # at 490-900 C (the contract's ranges, finding 21): it would shrink the Ford Cell 9 rows' TIT u_D from 3.5 K
    # at 800 C to 0.593 K, a flattering reading of a row that does not say it covers that sensor (mistake 6).
    # Applied to the intake and coolant temperatures (U_INPUT) it only widens their u. Left to the team
    # (WP3_INTERFACES.md 11).
    "tit": UD(None, 0.0075 / math.sqrt(3.0), "common", "IEC 60584-1 class 2 as a uniform half-width, unsourced",
              "contract section 3 (u_D) and JSON conventions.u_D; no report states a thermocouple's accuracy (the "
              "Ford Cell 9's generic Temperature row is not read as the turbine inlet's)", True),
    # the Ford's inter-cell disagreement, 0.02, as a uniform half-width: 0.012 as the contract prints it,
    # common; read where EPA's lambda is compared (E8) or enters a reference (E4b)
    "lam": UD(0.012, None, "common", "the Ford's inter-cell lambda disagreement as a uniform half-width, unsourced",
              "contract sections 1.5 and 3 (u_D) and JSON conventions.u_D; " + _NONE_STATED, True),
    # The Coriolis meter (each report's Table 2 lists a Micro Motion Coriolis fuel meter, with no accuracy):
    # Table 8's fuel row of the meter, "steady" where the report splits it. Its "transient" row is the injector
    # correlation's ("where the injector calibration procedure was used to determine the final fuel flow"),
    # injector_fuel_gps's, never the meter's. A Final row's meter averages a window shorter than a steady
    # mode's (HD1: "typically two to five seconds in duration"), so its u(operation) is above the table's
    # average; the meter's u(calibration) dominates its u(signal) in every report that prints both. No fallback:
    # the table's printed resolution of the meter was not read.
    "meter": UD(None, None, "random", "EPA's stated standard uncertainty, per report",
                "decision 56: each report's Table 8 (U_D['meter'].cells)", False, cells=(
                    _t8(MAZDA_CELL9, "Fuel (g/sec) - steady | 0.00240 | - | 0.000240 | 0.00241"),
                    _t8(HONDA_CELL7, "Fuel (g/sec) - steady | 0.0100 | 0.000728 | 0.0100"),
                    _t8(FORD_CELL9, "Fuel (g/sec) | 0.00640 | 0.00365 | 0.00737"),
                    _t8(FORD_HD1, "Fuel (g/sec) | 0.00581", column="u(calibration)"))),
    # The torque sensor (each report's Table 2 lists an HBM torque sensor, with no accuracy): Table 8's torque
    # row. HD1 prints u(calibration) only, so its pin is below its u(signal) by the unprinted u(operation). No
    # fallback.
    "torque": UD(None, None, "random", "EPA's stated standard uncertainty, per report",
                 "decision 56: each report's Table 8 (U_D['torque'].cells)", False, cells=(
                     _t8(MAZDA_CELL9, "Torque (Nm) | 0.116 | - | 0.0519 | 0.127"),
                     _t8(HONDA_CELL7, "Torque (Nm) | 0.125 | 0.0512 | 0.135"),
                     _t8(FORD_CELL9, "Torque (Nm) | 0.0808 | 0.137 | 0.159"),
                     _t8(FORD_HD1, "Torque (Nm) | 1.591", column="u(calibration)"))),
}
# What the pins' author read, for calibrate_epa.SEEN_BEFORE_THE_FIT (amendment C13; WP3_INTERFACES.md 11: "each
# read entered in SEEN_BEFORE_THE_FIT"). Each entry names what was seen and where, and repeats no value.
SOURCES_READ = (
    "WP3's pin author, 23 October 2026 (decision 56): the four EPA test reports (logs/epa/<engine>/3- and 3a- ... "
    "Test Report.docx), every paragraph and table cell, through zipfile's word/document.xml into a scratch file: "
    "Table 2 (instrumentation), the setup and procedure sections and the section Uncertainty with its Table 8; "
    "the reports also print the rated power and torque, the fuel properties, the common-mode points and the "
    "BSFC and BTE uncertainty discussion; no EPA table, workbook or data file",
    "WP3's pin author, 23 October 2026: the three ALPHA Generation Process pages (logs/epa/<engine>/3- ... .html) "
    "for any instrument accuracy (none stated); the Mazda's page whole, including the engine definition it "
    "prints (the full-throttle, closed-throttle and naturally aspirated curves and the fuel map), the Honda's "
    "and the Ford's prose and code lines (their WOT, idle and estimated fueling points), their curve and map "
    "arrays filtered out; none used",
    "WP3's pin author, 23 October 2026: the four NVFEL Fuel Analysis Report PDFs (logs/epa/<engine>/6- ...), "
    "through pdftotext: fuel properties only, no instrument accuracy; none used",
)


class UnpinnedUncertainty(RuntimeError):
    """A statistic asked for a u_D term that decision 56 has not pinned yet (for the report a row came from)."""


# =============================================================================================
# 5.2.1 Conventions and inputs
# =============================================================================================
@dataclass(frozen=True)
class Conventions:
    """The conventions a row is fed under (contract section 3). snap: a row within LAM_BAND of lambda_ref runs
    at 1.00 (E6 row 12 runs without it); cell_referenced: every other row at lambda_meas - (lambda_ref - 1)
    (E6 row 1 runs as published, the snap kept); afr_st, lhv_j_per_kg: E6 rows 2 and 3 move the table's fuel
    to 14.7 and 44.0e6 (None keeps the table's own, decision 69)."""
    snap: bool
    cell_referenced: bool
    afr_st: float | None
    lhv_j_per_kg: float | None


NOMINAL = Conventions(snap=True, cell_referenced=True, afr_st=None, lhv_j_per_kg=None)


@dataclass(frozen=True)
class RowInputs:
    """What the model is fed at one row (contract section 3, "inputs fed"; PLAN.md 5.1): EPA's speed, MAP,
    intake temperature (the charge), coolant, spark as published or the model ECU's for a sentinel row, and
    lambda by the conventions; everything else is the model's own."""
    engine: str
    table: str
    source_row: int
    rpm: float
    map_kpa: float
    iat_k: float
    ect_k: float
    spark_btdc: float
    lam: float
    lam_source: str          # "snapped", "cell_referenced", "published", "missing_at_1.00", "lambda_1"
    spark_source: str        # "published", "model_ecu_sentinel"
    fuel: object             # the row's table's epa_rows.TableFuel, after the conventions' overrides


def _lam_ref(row, lam_ref):
    """The row's table's lambda_ref: the row's own field, or the value the caller passes for a row type that
    carries none (a held-out High Load Initial row, WP3_INTERFACES.md 5.1, has no lam_ref field)."""
    if lam_ref is not None:
        return float(lam_ref)
    ref = getattr(row, "lam_ref", None)
    if ref is None:
        raise AttributeError(f"{_row_name(row)} carries no lam_ref: pass its table's lambda_ref "
                             "(view.lambda_ref[table]) explicitly")
    return float(ref)


def _lam_missing(row):
    return bool(getattr(row, "lambda_missing", False)) or getattr(row, "lam_meas", None) is None


def _sentinel(row):
    return bool(getattr(row, "spark_sentinel", False)) or getattr(row, "spark_btdc", None) is None


def lam_cellref(row, *, lam_ref=None):
    """EPA's lambda, cell-referenced and unsnapped: lambda_meas - (lambda_ref - 1); None for a row without
    lambda. E8's EPA lambda (contract section 4, E8; decision 57) and the censoring test's scale."""
    if _lam_missing(row):
        return None
    return float(row.lam_meas) - (_lam_ref(row, lam_ref) - 1.0)


def lam_fed(row, *, conventions, lam_ref=None):
    """(lambda the model runs at, its source) by the contract's section 3: a row without lambda runs at 1.00
    (decision 54); under the snap a row whose PUBLISHED lambda lies within LAM_BAND (+ the split's TOL) of
    lambda_ref runs at 1.00 (the same test as the split's lambda~1 band, so every hot lambda~1 row is
    snapped); every other row at lambda_meas - (lambda_ref - 1), or as published under E6 row 1."""
    if _lam_missing(row):
        return 1.0, "missing_at_1.00"
    lm, ref = float(row.lam_meas), _lam_ref(row, lam_ref)
    if conventions.snap and abs(lm - ref) <= LAM_BAND + TOL:
        return 1.0, "snapped"
    if conventions.cell_referenced:
        return lm - (ref - 1.0), "cell_referenced"
    return lm, "published"


def fuel_of(row, *, view, conventions):
    """The row's own table's fuel (contract section 3, Fuel; decision 69: every row runs on its own table's
    LHV and AFR_st whatever the plant in use carries), with E6 rows 2-3's overrides. view.fuel_by_table holds
    the contract's records (epa_rows.TableFuel)."""
    base = view.fuel_by_table[row.table]
    changes = {}
    if conventions.afr_st is not None:
        changes["afr_st"] = float(conventions.afr_st)
    if conventions.lhv_j_per_kg is not None:
        changes["lhv_j_per_kg"] = float(conventions.lhv_j_per_kg)
    return replace(base, **changes) if changes else base


def air_cal(row, *, view, conventions):
    """The calibration's air (contract section 3; JSON conventions.air_for_calibration): fuel meter x AFR_st of
    the row's table x the lambda it is fed, on steady and Final rows only (High Load Initial carries no meter).
    None without a meter or without lambda: a row without lambda is excluded from every stage that feeds
    lambda (PLAN.md 5.2, "Excluded and listed"; decision 54)."""
    if _kind_of(row) == "initial":
        return None
    meter = getattr(row, "fuel_meter_gps", None)
    if meter is None or _lam_missing(row):
        return None
    lam, _ = lam_fed(row, conventions=conventions)
    return float(meter) * float(fuel_of(row, view=view, conventions=conventions).afr_st) * lam


def row_inputs(row, *, conventions, model, view=None, fuel=None, lam_ref=None):
    """The model's inputs at one row (contract section 3; PLAN.md 5.1). A sentinel row (spark exactly -120 or an
    empty Spark Timing cell) runs at the model ECU's spark, at a 30 s dwell, no knock retard and EPA's intake
    temperature (decision 54; model.ecu_at). The fuel is the row's table's after the conventions: from `view`
    (the interface's signature, fuel_of) or already resolved as `fuel` (a pool's PointTask carries it and no
    view); exactly one of the two. A row type without lam_ref (a held-out Initial row) takes its table's from
    `lam_ref`, or from the view."""
    if (view is None) == (fuel is None):
        raise TypeError("row_inputs takes exactly one of view= and fuel=")
    if fuel is None:
        fuel = fuel_of(row, view=view, conventions=conventions)
        if lam_ref is None and getattr(row, "lam_ref", None) is None:
            lam_ref = float(view.lambda_ref[row.table])
    lam, lsrc = lam_fed(row, conventions=conventions, lam_ref=lam_ref)
    if _sentinel(row):
        e = model.ecu_at(float(row.speed_rpm), float(row.map_kpa), float(row.imt_k), float(row.ect_k))
        spark, ssrc = float(e.spark_btdc), "model_ecu_sentinel"
    else:
        spark, ssrc = float(row.spark_btdc), "published"
    return RowInputs(engine=row.engine, table=row.table, source_row=int(row.source_row),
                     rpm=float(row.speed_rpm), map_kpa=float(row.map_kpa), iat_k=float(row.imt_k),
                     ect_k=float(row.ect_k), spark_btdc=spark, lam=float(lam), lam_source=lsrc,
                     spark_source=ssrc, fuel=fuel)


@dataclass(frozen=True)
class Censoring:
    """Censored lambda (contract section 3; decision 54 with amendment C1): defined on the calibration High
    Load Final rows themselves. value is on the cell-referenced scale."""
    censored: bool
    value: float | None
    n_at_min: int
    documented_floor: float | None
    rule: str
    n_rows: int


def censoring(rows):
    """Censoring of one engine's lambda from its calibration High Load Final rows: censored when at least 2 sit
    at their own minimum cell-referenced lambda within 1e-9, or at a documented sensor floor
    (epa_rows.DOCUMENTED_FLOORS, empty: none has been opened). Rows of any other kind are refused, so a
    caller cannot censor on all rows (amendment C1)."""
    rows = tuple(rows)
    for r in rows:
        if _kind_of(r) != "final":
            raise ValueError(f"censoring is defined on High Load Final rows only, not {_row_name(r)}")
    engines_seen = {r.engine for r in rows}
    if len(engines_seen) > 1:
        raise ValueError(f"censoring is per engine; got {sorted(engines_seen)}")
    floor = epa_rows.DOCUMENTED_FLOORS.get(next(iter(engines_seen))) if engines_seen else None
    lams = [lam_cellref(r) for r in rows if not _lam_missing(r)]
    if not lams:
        return Censoring(False, None, 0, floor, "no calibration Final row publishes a lambda", 0)
    lo = min(lams)
    n_at = sum(1 for x in lams if abs(x - lo) <= 1e-9)
    if n_at >= 2:
        return Censoring(True, lo, n_at, floor, "at least 2 calibration Final rows at their own minimum within "
                         "1e-9 (contract section 3)", len(lams))
    if floor is not None:
        # "at least 2 of its calibration High Load Final rows sit at their own minimum ... or at a documented
        # sensor floor": the two-row count, read here for the floor as for the minimum
        at_floor = sum(1 for x in lams if abs(x - floor) <= 1e-9)
        return Censoring(at_floor >= 2, float(floor), n_at, float(floor), "at least 2 calibration Final rows at "
                         "a documented sensor floor within 1e-9 (contract section 3)", len(lams))
    return Censoring(False, None, n_at, None, "fewer than 2 calibration Final rows at their own minimum, and no "
                     "documented sensor floor (contract section 3)", len(lams))


def held_out_censored(rows, *, censoring):
    """The held-out High Load Final rows at the censoring value (within 1e-9): E8 lists them and reports dl
    without them, gating nothing on the list. A row that reads BELOW the censoring value is not counted: it
    shows that the sensor reads lower (contract section 3, after version 4's seventh review)."""
    if not censoring.censored:
        return ()
    out = []
    for r in rows:
        if _kind_of(r) != "final" or _lam_missing(r):
            continue
        if abs(lam_cellref(r) - censoring.value) <= 1e-9:
            out.append((r.table, int(r.source_row)))
    return tuple(out)


# =============================================================================================
# 5.2.2 The model protocol: the records the model returns
# =============================================================================================
@dataclass(frozen=True)
class ModelOut:
    """What a model returns for one cycle: brake torque N m, fuel and air g/s, the gas temperature after the
    port loss in degC (plant.CycleResult.egt_c, compared with EPA's Turbine Inlet Temp, mistake 23), the knock
    integral and the volumetric efficiency."""
    torque_nm: float
    fuel_gps: float
    air_gps: float
    egt_c: float
    knock_integral: float
    eta_v: float


@dataclass(frozen=True)
class EcuOut:
    """The model ECU at one row: one BaselineECU.step at a 30 s dwell with no knock retard (contract section 4,
    E8): spark deg BTDC, lambda, and form D's cam (None otherwise)."""
    spark_btdc: float
    lam: float
    cam_deg: float | None


# =============================================================================================
# 5.2.3 Per-row evaluation
# =============================================================================================
@dataclass(frozen=True)
class InputShift:
    """One input channel of one row moved by delta, for u_input's central difference and for E6 row 11's
    +-6.3 K on the charge. The READING is moved: lambda before the snap and before cell-referencing, so a
    shifted row is the row a different reading would give (populations stay the row's own). `cells`,
    ((engine, test_cell), delta) pairs, moves a row of a listed report by that report's own delta (decision 56:
    the pins are per report, U_INPUT and U_D); any other row moves by `delta`, and with `delta` None (a term with
    no fallback, torque's) such a row refuses (UnpinnedUncertainty)."""
    channel: str
    delta: float | None
    cells: tuple = ()

    def __post_init__(self):
        if self.channel not in INPUT_CHANNELS + TORQUE_SHIFT_CHANNELS:
            raise ValueError(f"InputShift: channel {self.channel!r} is not one of "
                             f"{INPUT_CHANNELS + TORQUE_SHIFT_CHANNELS}")
        if self.delta is None and not self.cells:
            raise ValueError(f"InputShift: {self.channel!r} has neither a delta nor a report's")

    def delta_for(self, row):
        """The delta a row moves by: its report's (cell_of), else the shift's own."""
        c = cell_of(row)
        for k, d in self.cells:
            if k == c:
                return float(d)
        if self.delta is None:
            raise UnpinnedUncertainty(f"InputShift {self.channel!r}: no pin for {_row_name(row)} of {c} "
                                      f"(pinned: {[k for k, _ in self.cells]})")
        return float(self.delta)


# EPA's torque reading moved (WP3's second fix of 23 October 2026, on the contract review's finding that D1's
# inversion target had no u_D): "torque" by an absolute delta in N m, "torque_rel" by a fraction of the
# reading, as decision 56 pins torque's u_D (UD.value or UD.rel). Never a u_input channel: the reading is
# D1's inversion target and a measured quantity, so its uncertainty is u_D's (contract section 3, "meter and
# torque"), re-evaluated through the same kernel because the target moves the D1 point (torque_target_shift).
TORQUE_SHIFT_CHANNELS = ("torque", "torque_rel")


def torque_target_shift(terms):
    """The shift that moves every row's torque reading by torque's u_D, +1 sign (u_d_terms' random part reads
    |stat(x + u) - stat(x)| per cluster): InputShift("torque", value) for an absolute term, ("torque_rel", rel)
    for a relative one; with per-report pins (U_D["torque"].cells, absolute N m) each row moves by its own
    report's, and a row of no listed report by the fallback or, with none, refuses. A term decision 56 has not
    pinned refuses (UnpinnedUncertainty)."""
    t = terms["torque"]
    if t.cells:
        if t.rel is not None:
            raise ValueError("torque's u_D: per-report pins are absolute N m, and a relative fallback cannot "
                             "share one shift with them")
        return InputShift("torque", None if t.value is None else float(t.value),
                          tuple((k, float(p.value)) for k, p in t.cells))
    if t.value is not None:
        return InputShift("torque", float(t.value))
    if t.rel is not None:
        return InputShift("torque_rel", float(t.rel))
    raise UnpinnedUncertainty(f"u_D's 'torque' term is not pinned ({t.source})")


@dataclass(frozen=True)
class PointTask:
    """One row's evaluation, picklable for epa_fit.ordered_map. `needs` is a subset of NEEDS: "at_epa" (the
    model at EPA's MAP), "d1" (D1's inversion), "lam1" (the row at lambda = 1, E4b's lever), "ecu" (the model
    ECU, E8). Beside the interface's fields it carries the row's resolved `fuel` (fuel_of) and, for a row type
    without one, its table's `lam_ref`: kernel_point is given no view."""
    row: object
    conventions: Conventions
    dtheta: float
    needs: frozenset
    shift: InputShift | None
    fuel: object
    lam_ref: float | None

    def __post_init__(self):
        if not set(self.needs) <= NEEDS:
            raise ValueError(f"PointTask: needs {sorted(self.needs)} outside {sorted(NEEDS)}")


def default_needs(row):
    """What each row is evaluated for, by its populations (contract sections 3-4): every gated row at EPA's
    MAP; D1's inversion on the fired rows with a meter and on the hot lambda~1 rows with a meter (L0, L1);
    the row at lambda = 1 on the enriched hot rows (E4b);
    the model ECU on the High Load Final rows (E8). An Initial row at its own inputs only (E1i)."""
    kind = _kind_of(row)
    if kind == "initial":
        return frozenset({"at_epa"})
    p = row.pops
    need = {"at_epa"}
    # D1's inversion on the fired rows with a meter, and on the hot lambda~1 rows with a meter, which L0
    # and L1 read at D1's point whatever their BMEP (split.classify: hot_l1_meter does not imply fired;
    # WP3's fix of 23 October 2026: such a row would have stopped the one-shot run in _need)
    if p.fired_meter or p.hot_l1_meter:
        need.add("d1")
    if p.hot_enr:
        need.add("lam1")
    if kind == "final":
        need.add("ecu")
    return frozenset(need)


def make_task(row, *, view, conventions, dtheta, needs, shift):
    """A PointTask with the row's fuel resolved from the view (fuel_of) and its lambda_ref, for a row type that
    carries none, from view.lambda_ref."""
    lam_ref = None if getattr(row, "lam_ref", None) is not None else float(view.lambda_ref[row.table])
    return PointTask(row=row, conventions=conventions, dtheta=float(dtheta), needs=frozenset(needs), shift=shift,
                     fuel=fuel_of(row, view=view, conventions=conventions), lam_ref=lam_ref)


def input_shift(ch, sg, term):
    """The shift by sg * u_j of one channel: each listed report's rows by their report's u (UInput.cells), every
    other row by the fallback (UInput.value)."""
    return InputShift(ch, sg * float(term.value), tuple((k, sg * float(p.value)) for k, p in term.cells))


def input_shifts(*, terms=None):
    """The +-u_j shifts u_input's central difference needs, channel by channel (the step is the uncertainty
    itself, so s_jc * u_j = (S(+u_j) - S(-u_j)) / 2): ((channel, sign, InputShift), ...)."""
    terms = U_INPUT if terms is None else terms
    return tuple((ch, sg, input_shift(ch, sg, terms[ch])) for ch in INPUT_CHANNELS for sg in (+1, -1))


@dataclass(frozen=True)
class Measured:
    """EPA's side of a row: torque N m, the Coriolis meter g/s (None without), TIT degC, EPA's lambda
    cell-referenced (None without), spark as published (None on a sentinel row), MAP kPa, BMEP bar."""
    torque_nm: float
    meter_gps: float | None
    tit_c: float
    lam_cellref: float | None
    spark_btdc: float | None
    map_kpa: float
    bmep_bar: float


@dataclass(frozen=True)
class D1Point:
    """D1's point at one row (contract section 4, D1; decision 57): the inverted MAP, whether a bracket was
    found (else bound_kpa, the nearer of 20 and 400 kPa), the spark and cam there, the model's output there,
    delta_D = fuel/meter - 1 and e_D = TIT_m - TIT_E (records; every statistic recomputes them from `out` and
    the row's Measured, so a perturbation of either moves them), and the cycles it cost."""
    map_kpa: float
    bracketed: bool
    bound_kpa: float | None
    spark_btdc: float
    cam_deg: float | None
    out: ModelOut
    delta_d: float | None
    e_d: float | None
    n_cycles: int


@dataclass(frozen=True)
class RowEval:
    """One row, evaluated. `kind` is steady, final or initial; `pops` the row's epa_rows.Populations (None on an
    Initial row, which enters no gating population, finding 21). `flags` holds lambda_missing, spark_sentinel,
    snapped, and, once marked, censored and outside_calibration_map_coverage. Beside the interface's fields:
    `shift` (the InputShift it was evaluated under, so u_input checks its step), `dtheta` (so u_num checks
    which crank step each set ran at) and `test_cell`, the row's own (its provenance), so u_D reads the pins of
    the report the row came from (decision 56; cell_of); None on a RowEval typed without one."""
    engine: str
    table: str
    source_row: int
    line: str
    kind: str
    hold: int | None
    pops: object
    origin: str
    inputs: RowInputs
    measured: Measured
    out: ModelOut | None
    lam1: ModelOut | None
    d1: D1Point | None
    ecu: EcuOut | None
    flags: frozenset
    shift: InputShift | None
    dtheta: float
    test_cell: str | None = None


def _row_name(row):
    return f"{getattr(row, 'table', '?')} row {getattr(row, 'source_row', '?')}"


def _kind_of(row):
    """steady, final or initial, from the row's own type: a held-out row says so (HeldOutRow.kind), an Initial
    row is transient, and a calibration Final row carries its hold."""
    k = getattr(row, "kind", None)
    if k in ("steady", "final", "initial"):
        return k
    if getattr(row, "transient", False):
        return "initial"
    return "final" if getattr(row, "hold", None) is not None else "steady"


_SHIFT_FIELD = {"speed": "speed_rpm", "map": "map_kpa", "imt": "imt_k", "ect": "ect_k", "spark": "spark_btdc",
                "lam": "lam_meas", "torque": "torque_nm"}


def _shifted_row(row, shift):
    """The row with one reading moved, by its own report's delta where the shift lists one (InputShift.delta_for).
    A sentinel row publishes no spark and a row without lambda no lambda, so a shift of a reading the row does
    not have leaves it unchanged."""
    if shift.channel == "spark" and _sentinel(row):
        return row
    if shift.channel == "lam" and _lam_missing(row):
        return row
    d = shift.delta_for(row)
    if shift.channel == "torque_rel":
        return replace(row, torque_nm=float(row.torque_nm) * (1.0 + d))
    f = _SHIFT_FIELD[shift.channel]
    return replace(row, **{f: float(getattr(row, f)) + d})


def d1_invert(x, torque_target, *, model, dtheta, spark_slope):
    """D1's inversion at one row (contract section 4, D1; decision 57; conventions.statistic_details.d1): the
    model's torque pre-scanned over 20-400 kPa every 10 kPa, at EPA's speed, intake temperature, coolant and the
    row's lambda convention, with spark = x.spark_btdc + s (MAP - MAP_E) (EPA's spark, or a sentinel row's model
    spark at EPA's MAP: version 4's reading of decision 54, kept by version 5); the first bracket from 20 kPa up
    (the first neighbouring pair between which the torque crosses EPA's; a pre-scan point that equals it exactly is
    the answer) bisected to 1e-3 kPa and evaluated at the final bracket's midpoint; with no bracket, the nearer
    bound (the end whose torque is nearer EPA's; 20 kPa on a tie), counted there. The cam is the model's own at the
    MAP it is run at (form D's schedule at the inverted MAP, decision 41): model.cycle reads it."""
    n = 0

    def at(m):
        nonlocal n
        n += 1
        xm = replace(x, map_kpa=float(m), spark_btdc=float(x.spark_btdc + spark_slope * (m - x.map_kpa)))
        return xm, model.cycle(xm, dtheta=dtheta)

    scan = [(m,) + at(m) for m in D1_SCAN_KPA]
    g = [o.torque_nm - torque_target for (_, _, o) in scan]
    chosen = None
    for i in range(len(scan)):
        if g[i] == 0.0:
            chosen = ("exact", i)
            break
        if i + 1 < len(scan) and g[i] * g[i + 1] < 0.0:
            chosen = ("bracket", i)
            break
    if chosen is None:
        i = 0 if abs(g[0]) <= abs(g[-1]) else len(scan) - 1
        m, xm, out = scan[i]
        return D1Point(map_kpa=m, bracketed=False, bound_kpa=m, spark_btdc=xm.spark_btdc,
                       cam_deg=model.cam(x.rpm, m), out=out, delta_d=None, e_d=None, n_cycles=n)
    how, i = chosen
    if how == "exact":
        m, xm, out = scan[i]
    else:
        lo, hi, g_lo = scan[i][0], scan[i + 1][0], g[i]
        m = None
        while hi - lo > D1_BISECT_KPA:
            mid = 0.5 * (lo + hi)
            gm = at(mid)[1].torque_nm - torque_target
            if gm == 0.0:
                m = mid
                break
            if (gm < 0.0) == (g_lo < 0.0):
                lo, g_lo = mid, gm
            else:
                hi = mid
        if m is None:
            m = 0.5 * (lo + hi)
        xm, out = at(m)
    return D1Point(map_kpa=float(m), bracketed=True, bound_kpa=None, spark_btdc=xm.spark_btdc,
                   cam_deg=model.cam(x.rpm, float(m)), out=out, delta_d=None, e_d=None, n_cycles=n)


def kernel_point(model, task):
    """One row's RowEval (WP3_INTERFACES.md 5.2.3): picklable, run through epa_fit.ordered_map. The shift, if
    any, moves the row's reading before anything is computed from it."""
    row0 = task.row
    row = _shifted_row(row0, task.shift) if task.shift is not None else row0
    x = row_inputs(row, fuel=task.fuel, conventions=task.conventions, model=model, lam_ref=task.lam_ref)
    out = model.cycle(x, dtheta=task.dtheta) if "at_epa" in task.needs else None
    lam1 = model.cycle(replace(x, lam=1.0, lam_source="lambda_1"), dtheta=task.dtheta) \
        if "lam1" in task.needs else None
    kind = _kind_of(row0)
    meter = None if kind == "initial" else getattr(row, "fuel_meter_gps", None)
    meas = Measured(torque_nm=float(row.torque_nm), meter_gps=None if meter is None else float(meter),
                    tit_c=float(row.tit_c), lam_cellref=lam_cellref(row, lam_ref=task.lam_ref),
                    spark_btdc=None if _sentinel(row) else float(row.spark_btdc), map_kpa=float(row.map_kpa),
                    bmep_bar=float(row.bmep_bar))
    d1 = None
    if "d1" in task.needs:
        s = (model.base_spark(x.rpm, x.map_kpa + D1_SPARK_DIFF_KPA)
             - model.base_spark(x.rpm, x.map_kpa - D1_SPARK_DIFF_KPA)) / (2.0 * D1_SPARK_DIFF_KPA)
        d1 = d1_invert(x, meas.torque_nm, model=model, dtheta=task.dtheta, spark_slope=s)
        d1 = replace(d1, delta_d=None if meas.meter_gps is None else d1.out.fuel_gps / meas.meter_gps - 1.0,
                     e_d=d1.out.egt_c - meas.tit_c)
    ecu = model.ecu_at(x.rpm, x.map_kpa, x.iat_k, x.ect_k) if "ecu" in task.needs else None
    flags = set()
    if _lam_missing(row0):
        flags.add("lambda_missing")
    if _sentinel(row0):
        flags.add("spark_sentinel")
    if x.lam_source == "snapped":
        flags.add("snapped")
    return RowEval(engine=row0.engine, table=row0.table, source_row=int(row0.source_row), line=row0.line,
                   kind=kind, hold=getattr(row0, "hold", None), pops=getattr(row0, "pops", None),
                   origin=getattr(row0, "origin", ""), inputs=x, measured=meas, out=out, lam1=lam1, d1=d1,
                   ecu=ecu, flags=frozenset(flags), shift=task.shift, dtheta=float(task.dtheta),
                   test_cell=getattr(row0, "test_cell", None))


def mark_censored(evals, *, censoring):
    """The evals with the "censored" flag on every High Load Final row at the censoring value (within 1e-9):
    the calibration rows the two-row test found, or a held-out row at that value; a row below it is not
    flagged (contract section 3). E4a and E4b flag them, E8 lists them; nothing gates on the flag."""
    if not censoring.censored:
        return tuple(evals)
    out = []
    for e in evals:
        lam = e.measured.lam_cellref
        if e.kind == "final" and lam is not None and abs(lam - censoring.value) <= 1e-9:
            e = replace(e, flags=e.flags | {"censored"})
        out.append(e)
    return tuple(out)


def map_band_key(map_kpa):
    """The coverage band of a manifold pressure, as thresholds/split.py's coverage() names it (test_epa_stats
    checks the two agree): "<lo>-<hi> kPa" in MAP_BAND steps."""
    b = int(float(map_kpa) // MAP_BAND)
    return f"{int(b * MAP_BAND)}-{int((b + 1) * MAP_BAND)} kPa"


def mark_coverage(evals, *, view):
    """Decision 58: a held-out row whose MAP band holds no calibration row of its population (hot rows against
    engines.<id>.coverage.calibration_hot, the others against .calibration_fired) is flagged
    outside_calibration_map_coverage; every statistic is then also reported restricted to the coverage
    (StatResult.coverage_restricted), beside it and never instead. Moves no label, R, population or
    statistic."""
    out = []
    for e in evals:
        if e.pops is not None:
            cov = view.coverage_calibration_hot if e.pops.hot else view.coverage_calibration_fired
            if map_band_key(e.measured.map_kpa) not in cov:
                e = replace(e, flags=e.flags | {"outside_calibration_map_coverage"})
        out.append(e)
    return tuple(out)


# =============================================================================================
# 5.2.4 Results
# =============================================================================================
@dataclass(frozen=True)
class UTerms:
    """u_val = sqrt(u_num^2 + u_input^2 + u_D^2), V&V 20's three terms, each the uncertainty of the
    population's mean; u_stat beside it, which decides only whether a line may certify (contract section 3)."""
    u_num: float
    u_input: float
    u_D: float
    u_val: float
    u_stat: float
    u_num_sd_undivided: float
    unsourced: tuple

    def as_json(self):
        return dict(u_num=_jf(self.u_num), u_input=_jf(self.u_input), u_D=_jf(self.u_D), u_val=_jf(self.u_val),
                    u_stat=_jf(self.u_stat), u_num_sd_undivided=_jf(self.u_num_sd_undivided),
                    unsourced=list(self.unsourced))


@dataclass(frozen=True)
class LineStat:
    line: str
    clusters: int
    E: float | None
    u: UTerms | None
    label: str | None
    certifies: bool | None


@dataclass(frozen=True)
class StatResult:
    """One contract row on one population (WP3_INTERFACES.md 5.2.4). For a per-line row E is the worst deciding
    line's (decision 57: the largest |E_l|, of two equal the larger u_val); for a pooled row the pooled value.
    E and R share the row's unit (percent or K)."""
    row: str
    stage: str
    R: float | None
    unit: str
    kind: str
    E: float | None
    lines: tuple
    deciding: tuple
    certifying: tuple
    worst_line: str | None
    u: UTerms | None
    label: str | None
    kappa: float | None
    passes: bool | None
    no_statistic: bool
    reason: str | None
    without: Mapping
    coverage_restricted: float | None
    extra: Mapping
    n_rows: int
    n_clusters: int
    # In-sample, a gating statistic's decision 77 reading (in_sample_judgement): its u_stat, outcome and why, and
    # every component's (each deciding line, or the pooled value). None held out, for E8 (outside the criterion,
    # decision 39(a)) and for a statistic with no statistic.
    judgement: Mapping | None = None

    def as_json(self):
        """WP3_INTERFACES.md 7.6: the in-sample form, or the held-out one. In-sample, decision 77's record beside
        E and R: u_stat, outcome (fails, passes, neither) and why, and each component's (None and {} where the
        statistic has no judgement)."""
        base = dict(R=_jf(self.R), unit=self.unit, kind=self.kind, E=_jf(self.E), deciding=list(self.deciding),
                    worst_line=self.worst_line, no_statistic=bool(self.no_statistic), reason=self.reason,
                    without={k: _jf(v) for k, v in self.without.items()}, extra=_jsonable(self.extra),
                    n_rows=int(self.n_rows), n_clusters=int(self.n_clusters))
        if self.stage == "in_sample":
            base["lines"] = {ls.line: dict(E=_jf(ls.E), clusters=int(ls.clusters)) for ls in self.lines}
            base["passes"] = self.passes
            j = self.judgement
            base.update(u_stat=None if j is None else _jf(j["u_stat"]), outcome=None if j is None else j["outcome"],
                        why=None if j is None else j["why"],
                        components={} if j is None else {c: dict(E=_jf(v["E"]), u_stat=_jf(v["u_stat"]),
                                                                 outcome=v["outcome"], why=v["why"])
                                                         for c, v in j["components"].items()})
            return base
        base["lines"] = {ls.line: dict(E=_jf(ls.E), clusters=int(ls.clusters),
                                       u=None if ls.u is None else ls.u.as_json(), label=ls.label,
                                       certifies=ls.certifies) for ls in self.lines}
        base.update(u=None if self.u is None else self.u.as_json(), certifying=list(self.certifying),
                    label=self.label, kappa=_jf(self.kappa), coverage_restricted=_jf(self.coverage_restricted))
        if self.kind == "d":
            base["condition"] = D_CONDITION
        return base


def _jf(x):
    """A JSON-safe float: a Python float, or None for an absent or non-finite value (allow_nan=False)."""
    if x is None:
        return None
    x = float(x)
    return x if math.isfinite(x) else None


def _jsonable(o):
    if isinstance(o, Mapping):
        return {str(k): _jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [_jsonable(v) for v in o]
    if isinstance(o, (bool, np.bool_)):
        return bool(o)
    if isinstance(o, (int, np.integer)):
        return int(o)
    if isinstance(o, (float, np.floating)):
        return _jf(o)
    if dataclasses.is_dataclass(o):
        return _jsonable(dataclasses.asdict(o))
    return o


# =============================================================================================
# Shared arithmetic
# =============================================================================================
def _key(e):
    return (e.table, int(e.source_row))


def _line_order(name):
    return tuple(int(p) for p in str(name).split("/") if p.strip().lstrip("-").isdigit()) or (math.inf,)


def _mean(v):
    return math.fsum(v) / len(v)


def _sd(v):
    """The sample standard deviation (ddof 1); None below 2 values."""
    if len(v) < 2:
        return None
    m = _mean(v)
    return math.sqrt(math.fsum((x - m) ** 2 for x in v) / (len(v) - 1))


def u_stat_line(values):
    """u_stat of a mean: the standard error with one row per cluster, SD (ddof 1) / sqrt(n) (contract section
    3; PLAN.md 6.2). None below 2 clusters."""
    values = [float(v) for v in values]
    s = _sd(values)
    return None if s is None else s / math.sqrt(len(values))


def _in(e, pop):
    return e.pops is not None and bool(getattr(e.pops, pop))


def _group(evals):
    out = {}
    for e in evals:
        out.setdefault(e.line, []).append(e)
    return {k: out[k] for k in sorted(out, key=_line_order)}


def _need(e, what):
    v = getattr(e, what)
    if v is None:
        raise ValueError(f"{e.table} row {e.source_row}: the statistic needs its {what!r} evaluation, which is "
                         f"missing (PointTask.needs)")
    return v


def _torque_rel(e):
    return 100.0 * (_need(e, "out").torque_nm / e.measured.torque_nm - 1.0)


def _fuel_rel(e):
    if e.measured.meter_gps is None:
        raise ValueError(f"{e.table} row {e.source_row}: no meter reading")
    return 100.0 * (_need(e, "out").fuel_gps / e.measured.meter_gps - 1.0)


def _tit_err(e):
    return _need(e, "out").egt_c - e.measured.tit_c


def _d1_delta(e):
    """delta_D, a fraction: the model's fuel at the demanded torque over the meter, minus 1."""
    return _need(e, "d1").out.fuel_gps / e.measured.meter_gps - 1.0


def _d1_e(e):
    return _need(e, "d1").out.egt_c - e.measured.tit_c


def _house(e, d, G, f):
    return f * e + f * (1.0 - f) * G * d


def house_max(e, d, G):
    """max over 0 <= f <= 1 of |f e + f(1 - f) G d|, by its endpoints and its vertex (a quadratic's extremes
    on an interval are there): (value, f*, H(f*)). The contract's housing equivalent (sections 1.4, 4 L0;
    thresholds/contract.py build's house_bound); on a tie the smaller f."""
    cands = [0.0, 1.0]
    q = G * d
    if q != 0.0:
        fv = (e + q) / (2.0 * q)
        if 0.0 <= fv <= 1.0:
            cands.append(fv)
    best = None
    for f in sorted(cands):
        h = _house(e, d, G, f)
        if best is None or abs(h) > best[0]:
            best = (abs(h), f, h)
    return best


def _round_down(x, nd=1):
    """A requirement rounded down, never up (contract section 1.3: "Requirements are rounded down"), as
    thresholds/contract.py's rdown writes it (test_epa_stats compares the two on a grid)."""
    q = 10 ** nd
    return math.floor(x * q + 1e-9) / q


# =============================================================================================
# The cores: each row's statistic as components, so that one function serves the value, the in-sample
# stage, the held-out run and every perturbation of the u-terms (mistake 10)
# =============================================================================================
@dataclass(frozen=True)
class _Core:
    lines: dict          # line -> {"E", "clusters", "members"} for every line of the population (reporting)
    deciding: tuple      # lines that decide (per-line rows) or contribute (pooled rows)
    comps: dict          # component -> value: the quantities u-terms are computed for
    comp_members: dict   # component -> keys of the rows in it
    comp_se: dict        # component -> u_stat
    E: float | None      # the pooled value (None on a per-line row: the worst line is picked with its u)
    pooled: bool
    no_statistic: bool
    reason: str | None
    extra: dict
    population: tuple    # every key the statistic reads


def _core_per_line(evals, *, pop, value, min_clusters=MIN_CLUSTERS, kind=None):
    rows = [e for e in evals if (e.kind == kind if kind else _in(e, pop))]
    lines, comps, mem, se = {}, {}, {}, {}
    for line, evs in _group(rows).items():
        vals = [value(e) for e in evs]
        keys = tuple(_key(e) for e in evs)
        lines[line] = dict(E=_mean(vals), clusters=len(vals), members=keys)
        if len(vals) >= min_clusters:
            comps[line], mem[line], se[line] = _mean(vals), keys, u_stat_line(vals)
    deciding = tuple(comps)
    return _Core(lines=lines, deciding=deciding, comps=comps, comp_members=mem, comp_se=se, E=None, pooled=False,
                 no_statistic=not deciding, reason=None if deciding else
                 f"no line with at least {min_clusters} clusters in {pop or kind}",
                 extra={}, population=tuple(_key(e) for e in rows))


def _core_pooled_abs(evals, *, pop, value):
    rows = [e for e in evals if _in(e, pop)]
    vals = [abs(value(e)) for e in rows]
    keys = tuple(_key(e) for e in rows)
    lines = {ln: dict(E=_mean([abs(value(e)) for e in evs]), clusters=len(evs), members=tuple(_key(e) for e in evs))
             for ln, evs in _group(rows).items()}
    ok = len(vals) >= MIN_CLUSTERS
    return _Core(lines=lines, deciding=tuple(lines), comps={"pooled": _mean(vals)} if ok else {},
                 comp_members={"pooled": keys} if ok else {}, comp_se={"pooled": u_stat_line(vals)} if ok else {},
                 E=_mean(vals) if ok else None, pooled=True, no_statistic=not ok,
                 reason=None if ok else f"fewer than {MIN_CLUSTERS} rows in {pop}", extra={}, population=keys)


def _core_E1a(evals, view, tightening):
    return _core_per_line(evals, pop="hot", value=_torque_rel)


def _core_E2a(evals, view, tightening):
    return _core_per_line(evals, pop="hot_meter", value=_fuel_rel)


def _core_E3a(evals, view, tightening):
    return _core_per_line(evals, pop="hot_l1", value=_tit_err)


def _core_E4a(evals, view, tightening):
    c = _core_per_line(evals, pop="hot_enr", value=_tit_err)
    cens = [list(_key(e)) for e in evals if _in(e, "hot_enr") and "censored" in e.flags]
    return replace(c, extra=dict(censored_rows=cens))


def _core_E1b(evals, view, tightening):
    return _core_pooled_abs(evals, pop="fired", value=_torque_rel)


def _core_E2b(evals, view, tightening):
    return _core_pooled_abs(evals, pop="fired_meter", value=_fuel_rel)


def _core_E3b(evals, view, tightening):
    return _core_pooled_abs(evals, pop="fired_l1", value=_tit_err)


def _core_E1i(evals, view, tightening):
    """E1i: the held-out High Load Initial rows' torque per line at their own inputs, a transient (finding 21)."""
    c = _core_per_line(evals, pop=None, value=_torque_rel, kind="initial")
    return replace(c, extra=dict(label="transient"))


def _core_D1(evals, view, tightening):
    """D1: the mean |delta_D| over the fired rows with a meter, pooled, unreachable rows counted at the nearer
    bound: the D1 that gates, in-sample and held-out (decision 57; amendment D12)."""
    rows = [e for e in evals if _in(e, "fired_meter")]
    vals = [100.0 * abs(_d1_delta(e)) for e in rows]
    keys = tuple(_key(e) for e in rows)
    unreach = [[e.table, int(e.source_row)] for e in rows if not e.d1.bracketed]
    lines = {ln: dict(E=_mean([100.0 * abs(_d1_delta(e)) for e in evs]), clusters=len(evs),
                      members=tuple(_key(e) for e in evs)) for ln, evs in _group(rows).items()}
    ok = len(vals) >= MIN_CLUSTERS
    return _Core(lines=lines, deciding=tuple(lines), comps={"pooled": _mean(vals)} if ok else {},
                 comp_members={"pooled": keys} if ok else {}, comp_se={"pooled": u_stat_line(vals)} if ok else {},
                 E=_mean(vals) if ok else None, pooled=True, no_statistic=not ok,
                 reason=None if ok else f"fewer than {MIN_CLUSTERS} fired rows with a meter",
                 extra=dict(unreachable=unreach, n_unreachable=len(unreach),
                            bounds_kpa=sorted({e.d1.bound_kpa for e in rows if not e.d1.bracketed})),
                 population=keys)


def _l0_lines(evals, G):
    """Each line's e-bar, delta-bar, L0_l and f* over its hot lambda~1 rows with a meter, at the D1 point."""
    rows = [e for e in evals if _in(e, "hot_l1_meter")]
    out = {}
    for line, evs in _group(rows).items():
        es = [_d1_e(e) for e in evs]
        ds = [_d1_delta(e) for e in evs]
        eb, db = _mean(es), _mean(ds)
        val, f, h = house_max(eb, db, G)
        out[line] = dict(e=es, d=ds, ebar=eb, dbar=db, L0=val, f=f, H=h, members=tuple(_key(e) for e in evs))
    return out, tuple(_key(e) for e in rows)


def _h_se(L, f, G):
    """u_stat of H_l(f) at a fixed f: the SE of the per-row h_i = f e_i + f(1 - f) G delta_i (the envelope
    theorem: at the maximising f the maximum's sampling error is H's at that f)."""
    return u_stat_line([_house(e, d, G, f) for e, d in zip(L["e"], L["d"])])


def _G(view):
    return float(view.propagation_b58["G_gas_over_42C_k"])


def _core_L0(evals, view, tightening):
    G = _G(view)
    L, pop = _l0_lines(evals, G)
    lines = {ln: dict(E=v["L0"], clusters=len(v["e"]), members=v["members"]) for ln, v in L.items()}
    dec = tuple(ln for ln, v in L.items() if len(v["e"]) >= MIN_CLUSTERS)
    extra = dict(G_k=G, per_line={ln: dict(ebar_k=v["ebar"], deltabar=v["dbar"], f_star=v["f"], H_k=v["H"])
                                  for ln, v in L.items()})
    return _Core(lines=lines, deciding=dec, comps={ln: L[ln]["L0"] for ln in dec},
                 comp_members={ln: L[ln]["members"] for ln in dec},
                 comp_se={ln: _h_se(L[ln], L[ln]["f"], G) for ln in dec}, E=None, pooled=False,
                 no_statistic=not dec,
                 reason=None if dec else f"no line with at least {MIN_CLUSTERS} hot lambda~1 rows with a meter",
                 extra=extra, population=pop)


def l1_spread(lines, G):
    """max over 0 <= f <= 1 of [max_l H_l(f) - min_l H_l(f)], exactly: the maximum over ordered pairs (a, b) of
    the maximum over f of H_a - H_b, each difference a quadratic in f maximised by its endpoints and vertex
    (PLAN.md 6.3, L1). lines: {line: (ebar, deltabar)}. Returns (value, f*, a, b); ties keep the first pair in
    line order and the smaller f."""
    names = list(lines)
    best = None
    for a in names:
        for b in names:
            if a == b:
                continue
            de = lines[a][0] - lines[b][0]
            dd = lines[a][1] - lines[b][1]
            # the spread is the signed D_ab = H_a - H_b; the pair (b, a) carries -D, so every sign is seen
            cands = [0.0, 1.0]
            q = G * dd
            if q != 0.0:
                fv = (de + q) / (2.0 * q)
                if 0.0 <= fv <= 1.0:
                    cands.append(fv)
            for fc in sorted(cands):
                d = _house(de, dd, G, fc)
                if best is None or d > best[0]:
                    best = (d, fc, a, b)
    return best


def _core_L1(evals, view, tightening):
    G = _G(view)
    L, pop = _l0_lines(evals, G)
    dec = tuple(ln for ln, v in L.items() if len(v["e"]) >= MIN_CLUSTERS)
    lines = {ln: dict(E=None, clusters=len(v["e"]), members=v["members"]) for ln, v in L.items()}
    if len(dec) < 2:
        return _Core(lines=lines, deciding=dec, comps={}, comp_members={}, comp_se={}, E=None, pooled=True,
                     no_statistic=True, reason="L1 needs at least 2 deciding lines (L0's)", extra=dict(G_k=G),
                     population=pop)
    val, f, a, b = l1_spread({ln: (L[ln]["ebar"], L[ln]["dbar"]) for ln in dec}, G)
    for ln in dec:
        lines[ln]["E"] = _house(L[ln]["ebar"], L[ln]["dbar"], G, f)
    se = math.sqrt(_h_se(L[a], f, G) ** 2 + _h_se(L[b], f, G) ** 2)
    members = tuple(k for ln in dec for k in L[ln]["members"])
    return _Core(lines=lines, deciding=dec, comps={"L1": val}, comp_members={"L1": members}, comp_se={"L1": se},
                 E=val, pooled=True, no_statistic=False, reason=None,
                 extra=dict(G_k=G, f_star=f, extreme_lines=[a, b],
                            H_at_f_star={ln: lines[ln]["E"] for ln in dec}), population=pop)


def _ls_line(x, y):
    """Least squares y = a + b x: (a, b, xbar, sxx, residuals)."""
    n = len(x)
    xb, yb = _mean(x), _mean(y)
    sxx = math.fsum((xi - xb) ** 2 for xi in x)
    if sxx <= 0.0:
        raise ValueError("E4b: the boosted lambda~1 rows of a line share one MAP, so the reference line has no "
                         "slope")
    b = math.fsum((xi - xb) * (yi - yb) for xi, yi in zip(x, y)) / sxx
    a = yb - b * xb
    return a, b, xb, sxx, [yi - (a + b * xi) for xi, yi in zip(x, y)], n


def _core_E4b(evals, view, tightening):
    """E4b, the lambda lever's pooled fractional error (contract section 4): on each line with at least 3
    boosted lambda~1 rows (steady and Final, MAP >= 100 kPa) and an enriched hot row, e-hat from the line's
    least-squares line of the lambda~1 error against MAP, evaluated at each enriched row's own MAP (finding 9);
    L_S = S(lambda 1) - S(row); eps = sum L_S / sum(L_S + e_enr - e-hat) - 1, in percent. u_stat by the delta
    method on cluster sums: each enriched row through (a_i - eps' b_i)/B, and each boosted row through the
    line's least-squares weights on e-hat (its residual's variance with m - 2 degrees of freedom)."""
    by_line = _group(list(evals))
    A = B = 0.0
    used, rows_enr, dec, lines, extrap, extrap_below, pop, flat = {}, [], [], {}, {}, {}, [], []
    for line, evs in by_line.items():
        boost = [e for e in evs if _in(e, "l1_boost")]
        enr = [e for e in evs if _in(e, "hot_enr")]
        if not enr and not boost:
            continue
        lines[line] = dict(E=None, clusters=len(enr), members=tuple(_key(e) for e in enr + boost))
        if len(boost) < MIN_CLUSTERS or not enr:
            continue
        x = [e.measured.map_kpa for e in boost]
        # A line whose boosted lambda~1 rows share one MAP has no reference line to read e-hat off
        # (_ls_line's sxx is 0): it decides nothing, and is named in the result, never a crash (WP3's
        # integration, 23 October 2026: the one-shot held-out run, and the fit's in-sample stage, would
        # otherwise stop on a data layout, which only the defect route could follow; validate_epa's
        # implementer met it on synthetic tables).
        if math.fsum((xi - _mean(x)) ** 2 for xi in x) <= 0.0:
            flat.append(line)
            continue
        dec.append(line)
        y = [_tit_err(e) for e in boost]
        a, b, xb, sxx, res, m = _ls_line(x, y)
        L_line = []
        for e in enr:
            L = _need(e, "lam1").egt_c - _need(e, "out").egt_c
            ehat = a + b * e.measured.map_kpa
            bi = L + _tit_err(e) - ehat
            A += L
            B += bi
            L_line.append((e, L, bi))
            rows_enr.append((e, L, bi))
        used[line] = dict(x=x, res=res, xb=xb, sxx=sxx, m=m, enr=L_line)
        # the distance the line is extrapolated in MAP, above the boosted range and below it (contract
        # section 4, E4b: "reported per line"; the below side added by WP3's fix of 23 October 2026)
        extrap[line] = max(0.0, max(e.measured.map_kpa for e in enr) - max(x))
        extrap_below[line] = max(0.0, min(x) - min(e.measured.map_kpa for e in enr))
        pop.extend(_key(e) for e in enr + boost)
    if not dec:
        return _Core(lines=lines, deciding=(), comps={}, comp_members={}, comp_se={}, E=None, pooled=True,
                     no_statistic=True, reason=f"no line with at least {MIN_CLUSTERS} boosted lambda~1 rows at more "
                     "than one MAP and an enriched hot row" + (f" (one MAP only: {', '.join(flat)})" if flat else ""),
                     extra={"lines_one_map": flat}, population=tuple(pop))
    if B == 0.0:
        # eps = sum L_S / sum(L_S + e_enr - e-hat) - 1 is undefined when the data's lever sums to zero:
        # no statistic, with its reason (decision 55's reading: it neither blocks nor passes), never a
        # crash of the run that computes it (WP3's integration, 23 October 2026; validate_epa's
        # implementer met it on synthetic tables). It was a ValueError.
        return _Core(lines=lines, deciding=tuple(dec), comps={}, comp_members={}, comp_se={}, E=None, pooled=True,
                     no_statistic=True, reason="the data's lever sums to zero over the deciding lines, so eps is "
                     "undefined", extra={"sum_L_S_k": A, "sum_data_lever_k": B, "lines_one_map": flat},
                     population=tuple(pop))
    R = A / B
    eps = 100.0 * (R - 1.0)
    n = len(rows_enr)
    # one enriched row has no variance of its own, so the pooled u_stat would be the regression term alone,
    # and 2u_stat <= R could certify a pass the enriched side never tested: below 2 enriched rows the pooled
    # u_stat is None, the row cannot certify and reads untested unless it is off (WP3's second fix of 23
    # October 2026, on the contract review's finding; declared in epa_fit.NO_STATISTIC_OUTCOMES)
    t_enr = None if n < 2 else math.fsum((L - R * bi) ** 2 for (_, L, bi) in rows_enr) * n / (n - 1) / B ** 2
    t_reg = 0.0
    for line, u in used.items():
        # d eps / d y_j = (R / B) * c_j, c_j = sum over the line's enriched rows of w_ij
        cs = [math.fsum(1.0 / u["m"] + (xj - u["xb"]) * (e.measured.map_kpa - u["xb"]) / u["sxx"]
                        for (e, _, _) in u["enr"]) for xj in u["x"]]
        if u["m"] > 2:
            s2 = math.fsum(r * r for r in u["res"]) / (u["m"] - 2)
            t_reg += (R / B) ** 2 * math.fsum(c * c for c in cs) * s2
    se = None if t_enr is None else 100.0 * math.sqrt(t_enr + t_reg)
    cens = [list(_key(e)) for (e, _, _) in rows_enr if "censored" in e.flags]
    extra = dict(sum_L_S_k=A, sum_data_lever_k=B, extrapolation_kpa=extrap, extrapolation_below_kpa=extrap_below,
                 enriched_rows=n, censored_rows=cens, pair_estimate=_e4b_pair(evals), lines_one_map=flat)
    return _Core(lines=lines, deciding=tuple(dec), comps={"pooled": eps}, comp_members={"pooled": tuple(pop)},
                 comp_se={"pooled": se}, E=eps, pooled=True, no_statistic=False, reason=None, extra=extra,
                 population=tuple(pop))


def _e4b_pair(evals):
    """The Initial-to-Final pair estimate (contract section 4, E4b), descriptive: sum(dS - dD) / sum(dD) over
    the holds whose lambda drops by at least 0.05 from the Initial to the Final window, dS the model's TIT
    change and dD EPA's, each window at its own inputs. Finding 21 keeps it descriptive: the Initial window is
    a thermal transient. None when no hold carries both windows' evaluations."""
    ini = {(e.line, e.hold): e for e in evals if e.kind == "initial" and e.out is not None}
    num = den = 0.0
    n = 0
    for e in evals:
        if e.kind != "final" or e.out is None:
            continue
        i = ini.get((e.line, e.hold))
        if i is None or i.measured.lam_cellref is None or e.measured.lam_cellref is None:
            continue
        if i.measured.lam_cellref - e.measured.lam_cellref < LAM_ENR - TOL:
            continue
        dS = e.out.egt_c - i.out.egt_c
        dD = e.measured.tit_c - i.measured.tit_c
        num += dS - dD
        den += dD
        n += 1
    if n == 0 or den == 0.0:
        return dict(value_pct=None, holds=n, label="descriptive")
    return dict(value_pct=100.0 * num / den, holds=n, label="descriptive")


def _core_E5(evals, view, tightening):
    """E5, descriptive (finding 9): per window, sum over lines of cov(MAP, S) / sum of cov(MAP, D) - 1, np.cov
    with ddof 1 on each line with at least 3 rows in the window; A the throttled lambda~1 rows (MAP < 100 kPa,
    BMEP >= 2 bar), B the boosted (MAP >= 100 kPa). The boost lever is untested for every engine."""
    win = {}
    for w, pop in (("A", "l1_thr"), ("B", "l1_boost")):
        sS = sD = 0.0
        per = {}
        for line, evs in _group([e for e in evals if _in(e, pop)]).items():
            if len(evs) < MIN_CLUSTERS:
                continue
            m = np.array([e.measured.map_kpa for e in evs])
            S = np.array([_need(e, "out").egt_c for e in evs])
            D = np.array([e.measured.tit_c for e in evs])
            cs, cd = float(np.cov(m, S, ddof=1)[0, 1]), float(np.cov(m, D, ddof=1)[0, 1])
            per[line] = dict(cov_map_S=cs, cov_map_D=cd, n=len(evs))
            sS += cs
            sD += cd
        win[w] = dict(value_pct=None if (not per or sD == 0.0) else 100.0 * (sS / sD - 1.0), lines=per)
    return _Core(lines={}, deciding=(), comps={}, comp_members={}, comp_se={}, E=None, pooled=True,
                 no_statistic=False, reason=None, extra=dict(windows=win, boost_lever="untested"), population=())


# ---------------------------------------------------------------------------------------------
# E8
# ---------------------------------------------------------------------------------------------
def e8_response(view, *, tightening):
    """P, the measured relative change of the head-start pair under K3 per ECU shift (contract section 4, E8):
    in-sample (tightening None) the contract's B58 tables (JSON ecu_strategy_b58.k3_pair_change_vs_*, both
    damage readings, the larger); held-out, at each shift the larger |change| of the contract's and the roads'
    tables, its sign kept (decision 57; a tightening only). The roads' tables must sit on the contract's shift
    grid (validate_epa.arm checks it; this refuses otherwise)."""
    s = view.ecu_strategy_b58
    pl = [(float(a), float(b)) for a, b in s["k3_pair_change_vs_lambda"]]
    ps = [(float(a), float(b)) for a, b in s["k3_pair_change_vs_spark"]]
    if tightening is None:
        return pl, ps
    _check_tightening(tightening)
    out = []
    for base, key in ((pl, "k3_pair_change_vs_lambda_roads"), (ps, "k3_pair_change_vs_spark_roads")):
        roads = [(float(a), float(b)) for a, b in _tget(tightening, "E8", key)]
        if [a for a, _ in roads] != [a for a, _ in base]:
            raise ValueError(f"E8: the roads' {key} is not on the contract's shift grid")
        out.append([(a, b if abs(b) >= abs(c) else c) for (a, b), (_, c) in zip(base, roads)])
    return out[0], out[1]


def _tget(t, *path):
    for p in path:
        t = t[p] if isinstance(t, Mapping) else getattr(t, p)
    return t


def _check_tightening(t):
    """Decision 71 (amendment E5): the tightenings are the B58's, measured on decision 34's roads; the held-out
    run refuses a record measured on any other plant."""
    if _tget(t, "plant") != "b58":
        raise ValueError(f"the tightening record was measured on {_tget(t, 'plant')!r}, not the B58 (decision 71)")


def p_slope(pts, x):
    """P's local slope at a shift (contract section 4, E8; decision 57): the slope of the segment that holds
    the shift, as thresholds.contract.interp picks it (the first segment below the grid, the last above), and
    at a shift of exactly 0 the steeper of the two segments beside it."""
    xs = [p[0] for p in pts]

    def seg(i):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        return (y1 - y0) / (x1 - x0)
    if x == 0.0 and 0.0 in xs:
        i = xs.index(0.0)
        sides = [seg(j) for j in (i - 1, i) if 0 <= j < len(xs) - 1]
        return max(sides, key=abs)
    if x <= xs[0]:
        return seg(0)
    if x >= xs[-1]:
        return seg(len(xs) - 2)
    i = max(k for k in range(len(xs) - 1) if xs[k] <= x)
    return seg(i)


def _p(pts, x):
    """(P(x) through thresholds.contract.interp, extrapolated?, local slope)."""
    return interp(pts, x), (x < pts[0][0] or x > pts[-1][0]), p_slope(pts, x)


def _e8_parts(finals):
    dl = [(e, _need(e, "ecu").lam - e.measured.lam_cellref) for e in finals if e.measured.lam_cellref is not None]
    ds = [(e, _need(e, "ecu").spark_btdc - e.measured.spark_btdc) for e in finals if e.measured.spark_btdc is not None]
    return dl, ds


def _core_E8(evals, view, tightening):
    """E8 (contract section 4; decision 54 as version 4 reads it, which version 5 kept; decision 57): dl the mean
    signed model ECU lambda minus EPA's lambda, cell-referenced and unsnapped, over the High Load Final rows that
    publish a lambda; ds the same for spark over those that publish a spark; each subset needs view.e8_min_rows rows
    or E8 has no statistic (the engine is dropped held-out; in-sample it is reported outside the form criterion,
    decision 39(a)). E8 = |P_lambda(dl)| + |P_spark(ds)| in percent."""
    finals = [e for e in evals if e.kind == "final"]
    dl, ds = _e8_parts(finals)
    nmin = int(view.e8_min_rows)
    pl, ps = e8_response(view, tightening=tightening)
    vdl = _mean([d for _, d in dl]) if dl else None
    vds = _mean([d for _, d in ds]) if ds else None
    extra = dict(n_final=len(finals), n_dl=len(dl), n_ds=len(ds), dl=vdl, ds=vds,
                 worth_b=_jsonable(view.ecu_strategy_b58.get("worth_b")))
    terms = {}
    if vdl is not None:
        P, ex, sl = _p(pl, vdl)
        terms["lambda"] = dict(shift=vdl, P=P, extrapolated=ex, slope=sl, rows=len(dl))
    if vds is not None:
        P, ex, sl = _p(ps, vds)
        terms["spark"] = dict(shift=vds, P=P, extrapolated=ex, slope=sl, rows=len(ds))
    extra["terms"] = terms
    # dl and ds over every Final row, as decision 54 reads literally: lambda 1.00, a spark difference of 0
    if finals:
        dl_all = _mean([_need(e, "ecu").lam - (e.measured.lam_cellref if e.measured.lam_cellref is not None
                                                else 1.0) for e in finals])
        ds_all = _mean([(_need(e, "ecu").spark_btdc - e.measured.spark_btdc) if e.measured.spark_btdc is not None
                        else 0.0 for e in finals])
        extra["every_final_row"] = dict(dl=dl_all, ds=ds_all,
                                        E_pct=100.0 * (abs(interp(pl, dl_all)) + abs(interp(ps, ds_all))))
    # dl without the censored rows, reported beside the dl that gates (contract section 3)
    cens = [e for e, _ in dl if "censored" in e.flags]
    extra["censored_rows"] = [list(_key(e)) for e in cens]
    keep = [d for e, d in dl if "censored" not in e.flags]
    extra["dl_without_censored"] = _mean(keep) if keep else None
    # the snapped E8, descriptive (decision 57): EPA's lambda snapped to 1.00 within the band
    if dl:
        sn = [e.ecu.lam - (1.0 if abs((e.measured.lam_cellref) - 1.0) <= LAM_BAND + TOL else e.measured.lam_cellref)
              for e, _ in dl]
        dls = _mean(sn)
        extra["snapped"] = dict(dl=dls, E_pct=None if vds is None else
                                100.0 * (abs(interp(pl, dls)) + abs(interp(ps, vds))), label="descriptive")
    # per line, the lowest MAP at which the model's lambda and EPA's fall 0.05 below lambda_ref (cell-referenced)
    enr = {}
    for line, evs in _group(finals).items():
        mm = [e.measured.map_kpa for e in evs if _need(e, "ecu").lam <= 1.0 - LAM_ENR + TOL]
        me = [e.measured.map_kpa for e in evs
              if e.measured.lam_cellref is not None and e.measured.lam_cellref <= 1.0 - LAM_ENR + TOL]
        enr[line] = dict(model_kpa=min(mm) if mm else None, epa_kpa=min(me) if me else None)
    extra["enrichment_onset_kpa"] = enr
    short = [nm for nm, sub in (("dl", dl), ("ds", ds)) if len(sub) < nmin]
    lines = {ln: dict(E=None, clusters=len(evs), members=tuple(_key(e) for e in evs))
             for ln, evs in _group(finals).items()}
    pop = tuple(_key(e) for e in finals)
    if short:
        return _Core(lines=lines, deciding=tuple(lines), comps={}, comp_members={}, comp_se={}, E=None, pooled=True,
                     no_statistic=True, reason=f"E8's subset(s) {short} hold fewer than {nmin} rows "
                     "(conventions.statistic_details.e8_subsets)", extra=extra, population=pop)
    E = 100.0 * (abs(terms["lambda"]["P"]) + abs(terms["spark"]["P"]))
    se_l = u_stat_line([d for _, d in dl])
    se_s = u_stat_line([d for _, d in ds])
    return _Core(lines=lines, deciding=tuple(lines), comps={"dl": vdl, "ds": vds},
                 comp_members={"dl": tuple(_key(e) for e, _ in dl), "ds": tuple(_key(e) for e, _ in ds)},
                 comp_se={"dl": se_l, "ds": se_s}, E=E, pooled=True, no_statistic=False, reason=None, extra=extra,
                 population=pop)


_CORES = {"E1a": _core_E1a, "E2a": _core_E2a, "E3a": _core_E3a, "E4a": _core_E4a, "E1b": _core_E1b,
          "E2b": _core_E2b, "E3b": _core_E3b, "E1i": _core_E1i, "E4b": _core_E4b, "E5": _core_E5,
          "D1": _core_D1, "L0": _core_L0, "L1": _core_L1, "E8": _core_E8}
# The measured channels each row's u_D reads (contract section 3; PLAN.md 6.2): the meter and torque terms
# where they are compared, the thermocouple's where TIT is, lambda's where EPA's lambda is compared (E8, as
# "lam") or enters a reference (E4b, as "lam_reference", a model re-run with every reading moved together).
U_D_CHANNELS = {"E1a": ("torque",), "E2a": ("meter",), "E3a": ("tit",), "E4a": ("tit",), "E1b": ("torque",),
                "E2b": ("meter",), "E3b": ("tit",), "E1i": ("torque",), "E4b": ("tit", "lam_reference"),
                "D1": ("meter", "torque_target"), "L0": ("tit", "meter", "torque_target"),
                "L1": ("tit", "meter", "torque_target"), "E8": ("lam",)}
# "torque_target" (WP3's second fix of 23 October 2026, on the contract review's must-fix): EPA's torque
# reading is D1's inversion target, so its uncertainty moves delta_D and e_D, and L0 and L1, which read D1's
# point, as directly as the meter does; a measured-side move of Measured.torque_nm would leave D1 unmoved
# (D1 never reads it). So the term is a model re-run, as E4b's lambda reference is: every member re-evaluated
# through kernel_point with its torque reading moved by torque's u_D (torque_target_shift), the inversion
# re-run at the moved target, and the statistic's change taken per cluster, random (u_d_terms). It reads
# torque's u_D term, so the pin check (unpinned_u_d) lists D1, L0 and L1 under "torque" until decision 56
# pins it.
D1_TORQUE_TARGET_U_D = ("in u_val: EPA's torque reading moves D1's inversion target; each cluster re-evaluated at "
                        "its torque reading + torque's u_D (torque_target_shift), random")


# The u_D term each re-evaluated channel reads (u_d_terms; unpinned_u_d): E4b's lambda reference reads
# lambda's, D1's torque target torque's.
U_D_TERM_OF = {"lam_reference": "lam", "torque_target": "torque"}


def unpinned_u_d(*, terms):
    """{term: the gating rows that read it} for every u_D term decision 56 has not pinned for every report (no
    fallback, value and rel both None, and a CellPin missing for one of REPORT_CELLS) that a gating row's u_D
    reads (U_D_CHANNELS; E4b's lam_reference is lambda's term). A held-out row that reads one stops in
    u_d_terms (UnpinnedUncertainty) inside the one-shot run, and pinning it after the first fit is a code change
    only the defect route admits (amendment C10), so calibrate_epa.py t0 and fit and validate_epa.py arm refuse
    while any is listed (WP3's fix of 23 October 2026, on the contract review's finding). `terms` is U_D in
    production, required so that a test's pinned table is explicit."""
    out = {}
    for row, chans in U_D_CHANNELS.items():
        if KIND[row] == "descriptive":
            continue
        for ch in chans:
            t = U_D_TERM_OF.get(ch, ch)
            if not terms[t].pinned_for_every_report():
                out.setdefault(t, []).append(row)
    return {k: tuple(v) for k, v in sorted(out.items())}


def _R(view, row, stage, tightening):
    """(R, unit) of a row for this engine: the contract's (view.R, the engine's entries of `thresholds`), and
    held-out L1's tightened R when the B58's roads slope makes it smaller: min(R, b/slope rounded down), which
    is the contract's "if it is larger than 0.0905, R becomes b/that slope" without retyping the 0.0905
    (contract section 4, L1; decision 71; the in-sample stage keeps 9.9 K, section 2.4)."""
    R, unit = view.R[row]
    R = None if R is None else float(R)
    if row == "L1" and stage == "held_out" and tightening is not None:
        _check_tightening(tightening)
        slope = float(_tget(tightening, "L1", "slope_points_per_K"))
        # the slope is a magnitude, points of d per K (WP3's second fix of 23 October 2026, on the contract
        # review's finding: a negative slope made every L1 read off, a zero one crashed the run after
        # STARTED); validate_epa.tightening_problems refuses it at the arming, and this asserts it again
        if not (math.isfinite(slope) and slope > 0.0):
            raise ValueError(f"L1: the tightening's slope_points_per_K is a magnitude, finite and > 0, not {slope!r}")
        R = min(R, _round_down(float(view.b_points) / slope))
    return R, unit


def _filtered(evals, flag):
    return tuple(e for e in evals if flag not in e.flags)


def _worst(core, uval=None):
    """The worst deciding line (decision 57): the largest |E_l|, of two equal the larger u_val (held-out), then
    line order."""
    if not core.deciding:
        return None
    return sorted(core.deciding, key=lambda ln: (-abs(core.comps[ln]),
                                                 -(uval[ln] if uval is not None else 0.0), _line_order(ln)))[0]


def _reported_E(core):
    if core.no_statistic:
        return None
    if core.pooled:
        return core.E
    return core.comps[_worst(core)]


def _without(row, evals, view, tightening):
    """The readings every statistic is also reported without (decision 54): the rows without lambda, the
    sentinel rows; D1 without its unreachable rows (decision 57); E8 without its censored rows (its dl)."""
    core = _CORES[row]
    out = {"lambda_missing": _reported_E(core(_filtered(evals, "lambda_missing"), view, tightening)),
           "spark_sentinel": _reported_E(core(_filtered(evals, "spark_sentinel"), view, tightening))}
    if row == "D1":
        reach = tuple(e for e in evals if not (_in(e, "fired_meter") and not e.d1.bracketed))
        out["unreachable"] = _reported_E(core(reach, view, tightening))
    if row == "E8":
        out["censored"] = _reported_E(core(_filtered(evals, "censored"), view, tightening))
    return out


def _result(row, evals, view, stage, tightening):
    """One row's StatResult without u-terms: the value, its lines, the in-sample pass and the readings without.
    The held-out labels are attached by held_out_row."""
    if stage not in ("in_sample", "held_out"):
        raise ValueError(f"stage {stage!r}: in_sample or held_out")
    if stage == "in_sample" and tightening is not None:
        raise ValueError("the in-sample stage takes no tightening: L1 at 9.9 K, E8 on the contract's P "
                         "(contract section 2.4; decision 71)")
    evals = tuple(evals)
    core = _CORES[row](evals, view, tightening)
    R, unit = _R(view, row, stage, tightening)
    kind = KIND[row]
    E = _reported_E(core)
    worst = None if (core.pooled or core.no_statistic) else _worst(core)
    lines = tuple(LineStat(line=ln, clusters=int(v["clusters"]), E=v["E"], u=None, label=None, certifies=None)
                  for ln, v in core.lines.items())
    passes = judgement = None
    if kind != "descriptive" and stage == "in_sample" and not core.no_statistic:
        if row in IN_SAMPLE_GATING:
            # decision 77: the statistic counts against the form only when its failure exceeds its sampling noise,
            # each component's u_stat the core's comp_se, the one the held-out run labels with (_uterms, combine)
            comps = _in_sample_components(core)
            judgement = in_sample_judgement(comps, R, report=worst if worst is not None else next(iter(comps)))
            passes = IN_SAMPLE_PASSES[judgement["outcome"]]
        else:
            # E8, outside the form criterion (decision 39(a)): its literal reading, reported and never read by
            # the ladder (in_sample_stage counts no E8)
            passes = abs(E) <= R
    cov = None
    if stage == "held_out" and row != "E5":
        cov = _reported_E(_CORES[row](_filtered(evals, "outside_calibration_map_coverage"), view, tightening))
    extra = core.extra
    if row == "E5":
        # E5 is a pair of windows, not one number, so its readings without the lambda-less and sentinel rows
        # (decision 54) and its coverage-restricted reading (decision 58, held-out) are the windows again,
        # each through the same core (WP3's second fix of 23 October 2026, on the contract review's finding
        # that E5 alone was reported without them)
        extra = dict(extra, without={flag: _CORES[row](_filtered(evals, flag), view, tightening).extra["windows"]
                                     for flag in ("lambda_missing", "spark_sentinel")},
                     coverage_restricted=None if stage != "held_out" else _CORES[row](
                         _filtered(evals, "outside_calibration_map_coverage"), view, tightening).extra["windows"])
    keys = set(core.population)
    return StatResult(row=row, stage=stage, R=R, unit=unit, kind=kind, E=E, lines=lines, deciding=core.deciding,
                      certifying=(), worst_line=worst, u=None, label=None, kappa=None, passes=passes,
                      no_statistic=core.no_statistic, reason=core.reason,
                      without={} if row == "E5" else _without(row, evals, view, tightening),
                      coverage_restricted=cov, extra=extra, n_rows=len(keys), n_clusters=len(keys),
                      judgement=judgement)


# =============================================================================================
# 5.2.5 The statistics, one function per contract row (section 8 of WP3_INTERFACES.md maps each)
# =============================================================================================
def row_E1a(evals, *, view, stage, tightening):
    """E1a, R 1.9 % (level): the worst deciding line's mean signed relative torque error over its hot rows."""
    return _result("E1a", evals, view, stage, tightening)


def row_E2a(evals, *, view, stage, tightening):
    """E2a, R 4.0 % (level): the worst line's mean signed fuel/meter - 1 over its hot rows with a meter."""
    return _result("E2a", evals, view, stage, tightening)


def row_E3a(evals, *, view, stage, tightening):
    """E3a, R 10.0 K (level): the worst line's mean egt_c - TIT over its hot lambda~1 rows."""
    return _result("E3a", evals, view, stage, tightening)


def row_E4a(evals, *, view, stage, tightening):
    """E4a, R 10.0 K (level): as E3a over the enriched hot rows; censored rows flagged (decision 54)."""
    return _result("E4a", evals, view, stage, tightening)


def row_E1b(evals, *, view, stage, tightening):
    """E1b, descriptive: the mean |relative torque error| over every fired row, pooled; worth b at
    (b/MEI)/1.353, reported unrounded."""
    r = _result("E1b", evals, view, stage, tightening)
    flow = float(view.propagation_b58["used"]["flow_pct_per_pct_torque"])
    return replace(r, extra=dict(r.extra, worth_b_pct=100.0 * float(view.b_points) / float(view.mei_points) / flow))


def row_E2b(evals, *, view, stage, tightening):
    """E2b, descriptive: the mean |fuel/meter - 1| over every fired row with a meter; worth b at b/MEI."""
    r = _result("E2b", evals, view, stage, tightening)
    return replace(r, extra=dict(r.extra, worth_b_pct=100.0 * float(view.b_points) / float(view.mei_points)))


def row_E3b(evals, *, view, stage, tightening):
    """E3b, descriptive: the mean |egt_c - TIT| over every fired lambda~1 row."""
    return _result("E3b", evals, view, stage, tightening)


def row_E1i(evals_initial, *, view, stage, tightening):
    """E1i, descriptive (held-out only): the High Load Initial rows' mean signed torque error per line, at their
    own inputs, labelled a transient."""
    if stage != "held_out":
        raise ValueError("E1i is a held-out row only: the calibration reads no Initial row's TIT, lambda or fuel, "
                         "and its Initial torque only for the descriptive full-throttle comparison (amendment C7)")
    return _result("E1i", evals_initial, view, stage, tightening)


def row_E4b(evals, *, view, stage, tightening):
    """E4b, R 16.6 % (d, P2): the lambda lever's pooled fractional error (see _core_E4b)."""
    return _result("E4b", evals, view, stage, tightening)


def row_E5(evals, *, view, stage, tightening):
    """E5, descriptive: the pooled slope ratio - 1 of TIT on MAP, windows A and B (see _core_E5)."""
    return _result("E5", evals, view, stage, tightening)


def row_D1(evals, *, view, stage, tightening):
    """D1, R 16.6 % (d, P1): the mean |delta_D| at the demanded torque, pooled over the fired rows with a meter,
    unreachable rows at the nearer bound (the D1 that gates); also reported without them."""
    return _result("D1", evals, view, stage, tightening)


def row_L0(evals, *, view, stage, tightening):
    """L0, R 10.0 K (level): per deciding line max over f of |f e-bar + f(1 - f) G delta-bar| over its hot
    lambda~1 rows with a meter at the D1 point, G = propagation_b58.G_gas_over_42C_k; the worst line."""
    return _result("L0", evals, view, stage, tightening)


def row_L1(evals, *, view, stage, tightening):
    """L1, R 9.9 K in-sample, held-out the tightened R if the B58's roads make it smaller (d, P3, additive):
    max over f of [max_l H_l - min_l H_l] over L0's lines, at least 2."""
    return _result("L1", evals, view, stage, tightening)


def row_E8(evals, *, view, stage, tightening):
    """E8, R 16.6 % (d, P4): |P_lambda(dl)| + |P_spark(ds)| (see _core_E8). In-sample it is computed and
    reported, outside the form criterion (decision 39(a))."""
    return _result("E8", evals, view, stage, tightening)


ROW_FUNCTIONS = {"E1a": row_E1a, "E2a": row_E2a, "E3a": row_E3a, "E4a": row_E4a, "E1b": row_E1b,
                 "E2b": row_E2b, "E3b": row_E3b, "E1i": row_E1i, "E4b": row_E4b, "E5": row_E5, "D1": row_D1,
                 "L0": row_L0, "L1": row_L1, "E8": row_E8}


# =============================================================================================
# 5.2.6 The u-terms (contract section 3; PLAN.md 6.2; decision 56)
# =============================================================================================
def _replace_rows(evals, index, repl):
    out = list(evals)
    for k, e in repl.items():
        out[index[k]] = e
    return tuple(out)


def _index(evals):
    idx = {}
    for i, e in enumerate(evals):
        k = _key(e)
        if k in idx:
            raise ValueError(f"two evaluations of {k}")
        idx[k] = i
    return idx


_OUT_FIELDS = ("torque_nm", "fuel_gps", "air_gps", "egt_c", "knock_integral", "eta_v")


def _moved_num(base, fine, mean_d):
    """The base evaluation moved by its own crank-step change minus the population's mean change, field by
    field (u_num: "mean removed, random")."""
    ch = {}
    for name in ("out", "lam1"):
        b, f = getattr(base, name), getattr(fine, name)
        if b is not None:
            ch[name] = replace(b, **{x: getattr(b, x) + (getattr(f, x) - getattr(b, x)) - mean_d[(name, x)]
                                     for x in _OUT_FIELDS})
    if base.d1 is not None:
        b, f = base.d1.out, fine.d1.out
        ch["d1"] = replace(base.d1, out=replace(b, **{x: getattr(b, x) + (getattr(f, x) - getattr(b, x))
                                                      - mean_d[("d1", x)] for x in _OUT_FIELDS}))
    return replace(base, **ch)


def u_num(stat, evals_025, evals_0125, *, members=None):
    """u_num (contract section 3; E6 row 8): per row the change of the model's outputs when the crank step is
    halved, 0.25 to 0.125 deg, the population's mean change removed (constants fitted at the same step absorb
    it), as a random part: sqrt(n/(n-1)) sqrt(sum over clusters of (stat(that cluster moved) - stat)^2), n the
    members whose mean change was removed. For a mean that is SD/sqrt(n) exactly, SD with ddof 1 (PLAN.md
    6.2: "which for a mean is SD/sqrt(n)"; d3_rows' u_num the same): the sum of squares about the estimated
    mean has n - 1 degrees of freedom, so without the factor u_num read sqrt((n-1)/n) of it, 18 % low at n 3
    (WP3's second fix of 23 October 2026, on the contract review's finding). With one member the mean
    removed leaves nothing, and u_num is 0. Returns (u_num, u_num * sqrt(n)). `stat` maps evals to one
    number; `members` are the clusters of the statistic's population (every key of evals_0125 when None).
    evals_0125 maps each member's key to its evaluation at the finer step."""
    evals_025 = tuple(evals_025)
    idx = _index(evals_025)
    members = tuple(evals_0125) if members is None else tuple(members)
    for k in members:
        if evals_025[idx[k]].dtheta == evals_0125[k].dtheta:
            raise ValueError(f"u_num: {k} was evaluated at one crank step twice ({evals_0125[k].dtheta})")
    deltas = {}
    for k in members:
        b, f = evals_025[idx[k]], evals_0125[k]
        for name in ("out", "lam1"):
            if getattr(b, name) is not None:
                for x in _OUT_FIELDS:
                    deltas.setdefault((name, x), []).append(getattr(getattr(f, name), x) - getattr(getattr(b, name), x))
        if b.d1 is not None:
            for x in _OUT_FIELDS:
                deltas.setdefault(("d1", x), []).append(getattr(f.d1.out, x) - getattr(b.d1.out, x))
    mean_d = {k: _mean(v) for k, v in deltas.items()}
    s0 = stat(evals_025)
    acc = []
    for k in members:
        moved = _moved_num(evals_025[idx[k]], evals_0125[k], mean_d)
        acc.append((stat(_replace_rows(evals_025, idx, {k: moved})) - s0) ** 2)
    n = len(members)
    u = math.sqrt(math.fsum(acc)) * (math.sqrt(n / (n - 1.0)) if n > 1 else 0.0)
    return u, u * math.sqrt(n)


def u_input(stat, evals, shifted, *, members=None, terms=None):
    """u_input (contract section 3; PLAN.md 6.2): per input channel j and cluster c, the central difference of
    the WHOLE statistic (D1's bisection included, since the shifted rows were re-evaluated) with that cluster's
    reading moved by +-u_j: s_jc u_j = (stat(+u_j) - stat(-u_j)) / 2; u_input = sqrt(sum (s_jc u_j)^2).
    shifted maps (channel, sign, key) to the RowEval of that row so shifted; every member needs both signs of
    every channel, and each shifted evaluation must carry exactly the step +-u_j, each report's rows their own
    report's (input_shift; mistake 19). members: the clusters of the statistic's population (every key in
    `shifted` when None)."""
    terms = U_INPUT if terms is None else terms
    evals = tuple(evals)
    idx = _index(evals)
    if members is None:
        members = tuple(sorted({k for (_, _, k) in shifted}))
    acc = []
    for ch in INPUT_CHANNELS:
        for k in members:
            got = []
            for sg in (+1, -1):
                ev = shifted[(ch, sg, k)]
                want = input_shift(ch, sg, terms[ch])
                if ev.shift != want:
                    raise ValueError(f"u_input: the evaluation of {k} for ({ch}, {sg:+d}) was not shifted by "
                                     f"{want} ({ev.shift})")
                got.append(stat(_replace_rows(evals, idx, {k: ev})))
            acc.append(((got[0] - got[1]) / 2.0) ** 2)
    return math.sqrt(math.fsum(acc))


def input_unsourced(ch, evals, members, *, terms):
    """Whether u_input's channel `ch` entered unsourced for these members: a member whose report states nothing
    for it reads the fallback (UInput.at); with no member, the fallback's own mark."""
    t = terms[ch]
    evals = tuple(evals)
    idx = _index(evals)
    if not members:
        return bool(t.unsourced)
    return any(t.at(cell_of(evals[idx[k]]))[1] for k in members)


def _pin_at(e, ch, terms):
    """(value, rel, unsourced) of u_D's `ch` for a RowEval's report (UD.at); a row with neither its report's pin
    nor a fallback refuses (UnpinnedUncertainty: mistake 9)."""
    t = terms[ch]
    got = t.at(cell_of(e))
    if got is None:
        raise UnpinnedUncertainty(f"u_D's {ch!r} term is not pinned for {_row_name(e)} of {cell_of(e)} "
                                  f"({t.source})")
    return got


def _moved_measured(e, ch, terms, sign=1.0):
    value, rel, _ = _pin_at(e, ch, terms)
    m = e.measured
    if ch == "tit":
        if rel is not None:
            return replace(e, measured=replace(m, tit_c=m.tit_c + sign * rel * abs(m.tit_c)))
        return replace(e, measured=replace(m, tit_c=m.tit_c + sign * value))
    if value is None:
        raise ValueError(f"u_D's {ch!r} term moves its reading by an absolute value, and has only a relative one")
    if ch == "lam":
        return e if m.lam_cellref is None else replace(e, measured=replace(m, lam_cellref=m.lam_cellref + sign * value))
    if ch == "meter":
        return e if m.meter_gps is None else replace(e, measured=replace(m, meter_gps=m.meter_gps + sign * value))
    if ch == "torque":
        return replace(e, measured=replace(m, torque_nm=m.torque_nm + sign * value))
    raise KeyError(ch)


def u_d_terms(stat, evals, *, channels, members, terms=None, common_lam=None, torque_target=None):
    """u_D (contract section 3; PLAN.md 6.2), on the measured side only, no model re-run: a common part is
    |stat(x + u) - stat(x)| with every row moved together (the thermocouple's class tolerance, 0.0075 |t| /
    sqrt(3) on each row's TIT; EPA's lambda by 0.012); a random part is sqrt(sum over clusters of (stat(c moved)
    - stat)^2) (the meter, the torque). E4b's "lam_reference" is the one model re-run: common_lam maps every
    member to its evaluation with its lambda reading moved by +0.012 (kernel_point under InputShift("lam",
    0.012)). D1's "torque_target" (and L0's and L1's) is the other: torque_target maps every member to its
    evaluation with its torque reading moved by torque's u_D (kernel_point under torque_target_shift), the
    inversion re-run there, taken per cluster as a random part. Each member reads the pin of the report it came
    from (UD.at, cell_of; decision 56). Returns (u_D, the unsourced terms that entered: a term is unsourced when
    a member read its fallback). A channel whose term is not pinned for a member's report refuses, as one with
    no pin at all does."""
    terms = U_D if terms is None else terms
    evals = tuple(evals)
    idx = _index(evals)
    s0 = stat(evals)
    acc, unsourced = [], []
    for ch in channels:
        tname = U_D_TERM_OF.get(ch, ch)
        t = terms[tname]
        if t.value is None and t.rel is None and not t.cells:
            raise UnpinnedUncertainty(f"u_D's {tname!r} term is not pinned ({t.source})")
        pins = [_pin_at(evals[idx[k]], tname, terms) for k in members]
        if ch == "torque_target":
            if torque_target is None:
                raise ValueError("D1's u_D reads the torque reading through its inversion target: pass torque_target, "
                                 "every member re-evaluated with its torque reading moved by torque's term")
            want = torque_target_shift(terms)
            for k in members:
                ev = torque_target[k]
                if ev.shift != want:
                    raise ValueError(f"u_D: torque_target's {k} was not shifted by {want} ({ev.shift})")
                acc.append((stat(_replace_rows(evals, idx, {k: ev})) - s0) ** 2)
        elif ch == "lam_reference":
            if common_lam is None:
                raise ValueError("E4b's u_D reads lambda through its reference: pass common_lam, every member "
                                 "re-evaluated with its lambda reading moved by the lambda term")
            if t.cells:
                raise ValueError("E4b's lambda reference is one common shift (validate_epa's InputShift('lam', "
                                 "U_D['lam'].value)): lambda's u_D takes no per-report pins")
            for k in members:
                ev = common_lam[k]
                if ev.shift is None or ev.shift.channel != "lam" or ev.shift.delta != float(t.value):
                    raise ValueError(f"u_D: common_lam's {k} was not shifted by lambda {t.value!r} ({ev.shift})")
            acc.append((stat(_replace_rows(evals, idx, {k: common_lam[k] for k in members})) - s0) ** 2)
        elif t.part == "common":
            moved = {k: _moved_measured(evals[idx[k]], ch, terms) for k in members}
            acc.append((stat(_replace_rows(evals, idx, moved)) - s0) ** 2)
        else:
            for k in members:
                acc.append((stat(_replace_rows(evals, idx, {k: _moved_measured(evals[idx[k]], ch, terms)})) - s0) ** 2)
        if (any(p[2] for p in pins) if pins else t.unsourced):
            unsourced.append(f"u_D {tname}")
    return math.sqrt(math.fsum(acc)), tuple(unsourced)


def u_d(stat, evals, *, channels=None, members=None, terms=None, common_lam=None, torque_target=None):
    """u_D as one number (WP3_INTERFACES.md 5.2.6's signature): u_d_terms' value, over the channels named
    (every measured channel, tit, lam, meter and torque, when None: an unpinned one then refuses) and the
    members given (every row of `evals` when None)."""
    channels = ("tit", "lam", "meter", "torque") if channels is None else channels
    members = tuple(_key(e) for e in evals) if members is None else members
    return u_d_terms(stat, evals, channels=channels, members=members, terms=terms, common_lam=common_lam,
                     torque_target=torque_target)[0]


def combine(u_num, u_input, u_d, u_stat, unsourced, *, u_num_sd_undivided=None):
    """u_val = sqrt(u_num^2 + u_input^2 + u_D^2) (V&V 20; contract section 3), u_stat beside it, never in it
    (finding 6). The undivided SD of u_num (E6 row 8) is recorded when the caller has it (None otherwise). A
    u_stat of None (a pooled statistic whose standard error has too few clusters, E4b on one enriched row) is
    kept None: the statistic cannot certify (line_label), and reads untested unless it is off."""
    return UTerms(u_num=float(u_num), u_input=float(u_input), u_D=float(u_d),
                  u_val=math.sqrt(u_num ** 2 + u_input ** 2 + u_d ** 2),
                  u_stat=None if u_stat is None else float(u_stat),
                  u_num_sd_undivided=None if u_num_sd_undivided is None else float(u_num_sd_undivided),
                  unsourced=tuple(unsourced))


# =============================================================================================
# 5.2.7 Labels (contract sections 3 and 7; PLAN.md 6.2)
# =============================================================================================
def line_label(E, u_val, u_stat, R):
    """(label, certifies) of one line or pooled statistic: off if |E| - 2u_val > R; else untested if 2u_val >
    R; else validated if |E| + 2u_val <= R; else limited. A line certifies a pass only if 2u_stat <= R (decision
    4's own rule); it decides an off label whatever its scatter. A u_stat of None certifies nothing (no
    standard error, no certification: WP3's second fix of 23 October 2026)."""
    a = abs(E)
    if a - 2.0 * u_val > R:
        lab = "off"
    elif 2.0 * u_val > R:
        lab = "untested"
    elif a + 2.0 * u_val <= R:
        lab = "validated"
    else:
        lab = "limited"
    return lab, (u_stat is not None and 2.0 * u_stat <= R)


def worse(a, b):
    """The worse of two labels in the order off > untested > limited > validated (E6 row 12; decision 59)."""
    return a if LABEL_ORDER.index(a) >= LABEL_ORDER.index(b) else b


def row_label(lines):
    """A row's label from its deciding lines (contract section 3): off if any deciding line reads off;
    otherwise the worse of validated and limited among the lines that read one of them and certify (2 u_stat
    <= R); untested if no line does. `lines` are LineStats with label and certifies."""
    if any(ls.label == "off" for ls in lines):
        return "off"
    cert = [ls.label for ls in lines if ls.certifies and ls.label in ("validated", "limited")]
    if not cert:
        return "untested"
    out = cert[0]
    for lab in cert[1:]:
        out = worse(out, lab)
    return out


def kappa(E, u_val, R, label):
    """A part's band factor (contract section 7): 1 when its row reads validated, else (|E| + 2u_val)/R."""
    return 1.0 if label == "validated" else (abs(E) + 2.0 * u_val) / R


@dataclass(frozen=True)
class UncertaintyInputs:
    """What held_out_row needs beside the evaluations: each member re-evaluated at dtheta 0.125 (u_num, E6 row
    8), each member shifted by +-u_j per input channel (u_input), and, for E4b, every member with its lambda
    reading moved by the lambda u_D (common_lam), and, for D1, L0 and L1, every member with its torque reading
    moved by torque's u_D (torque_target); the two tables of terms (U_INPUT, U_D in production)."""
    evals_0125: Mapping
    shifted: Mapping
    common_lam: Mapping | None
    input_terms: Mapping
    d_terms: Mapping
    # every member with its torque reading moved by torque's u_D (torque_target_shift): D1's, L0's and L1's
    # torque target (WP3's second fix of 23 October 2026); None where no row that reads it is computed
    torque_target: Mapping | None = None


def _uterms(row, evals, view, tightening, core, unc):
    """UTerms per component of the row's core (a deciding line, the pooled value, E8's dl and ds, L1)."""
    out = {}
    pop_all = tuple(sorted({k for ks in core.comp_members.values() for k in ks}))
    for comp, members in core.comp_members.items():
        def stat(evs, comp=comp):
            return _CORES[row](evs, view, tightening).comps[comp]
        un, sd = u_num(stat, evals, unc.evals_0125, members=pop_all)
        sd = un * math.sqrt(len(members))
        ui = u_input(stat, evals, unc.shifted, members=members, terms=unc.input_terms)
        ud, uns = u_d_terms(stat, evals, channels=U_D_CHANNELS[row], members=members, terms=unc.d_terms,
                            common_lam=unc.common_lam, torque_target=unc.torque_target)
        # a u_input channel is unsourced where a member's report states nothing for it (decision 56)
        names = list(uns) + [f"u_input {ch}" for ch in INPUT_CHANNELS
                             if input_unsourced(ch, evals, members, terms=unc.input_terms)]
        # a component without a standard error (E4b's pooled value on one enriched row) carries u_stat None:
        # it is labelled, and cannot certify (combine, line_label; WP3's second fix of 23 October 2026, on the
        # contract review's finding that E4b's regression term alone could certify it)
        out[comp] = combine(un, ui, ud, core.comp_se[comp], names, u_num_sd_undivided=sd)
    return out


def held_out_row(row, evals, *, view, tightening, unc):
    """One gating row on the held-out rows with its u-terms, labels and kappa (contract sections 3 and 7). The
    value is the same function's as in-sample (row_<id>); the u-terms come from the perturbed evaluations in
    `unc`. Per-line rows: every deciding line labelled with its own u_val and u_stat, the row reports its worst
    deciding line's E and u. Pooled rows (D1, E4b, L1) and E8: one label from the pooled u; E8's u_val and
    u_stat propagate dl's and ds's through P's local slopes (decision 57)."""
    if KIND[row] == "descriptive":
        raise ValueError(f"{row} is descriptive: reported by row_{row}, never labelled")
    evals = tuple(evals)
    res = _result(row, evals, view, "held_out", tightening)
    if res.no_statistic:
        return res
    core = _CORES[row](evals, view, tightening)
    U = _uterms(row, evals, view, tightening, core, unc)
    R = res.R
    if row == "E8":
        sl = abs(core.extra["terms"]["lambda"]["slope"])
        ss = abs(core.extra["terms"]["spark"]["slope"])
        ul, us = U["dl"], U["ds"]

        def prop(a, b):
            if a is None or b is None:
                return None
            return 100.0 * math.sqrt((sl * a) ** 2 + (ss * b) ** 2)
        u = UTerms(u_num=prop(ul.u_num, us.u_num), u_input=prop(ul.u_input, us.u_input), u_D=prop(ul.u_D, us.u_D),
                   u_val=prop(ul.u_val, us.u_val), u_stat=prop(ul.u_stat, us.u_stat),
                   u_num_sd_undivided=prop(ul.u_num_sd_undivided, us.u_num_sd_undivided),
                   unsourced=tuple(dict.fromkeys(ul.unsourced + us.unsourced)))
        extra = dict(res.extra, u_dl=ul.as_json(), u_ds=us.as_json())
        U = {"pooled": u}
        res = replace(res, extra=extra)
    if core.pooled:
        u = U["pooled"] if "pooled" in U else U["L1"]
        lab, cert = line_label(res.E, u.u_val, u.u_stat, R)
        pooled = LineStat(line="pooled", clusters=res.n_clusters, E=res.E, u=u, label=lab, certifies=cert)
        label = row_label([pooled])
        lines = res.lines + (pooled,)
        return replace(res, lines=lines, u=u, label=label, certifying=("pooled",) if cert else (),
                       kappa=kappa(res.E, u.u_val, R, label))
    uval = {ln: U[ln].u_val for ln in core.deciding}
    worst = _worst(core, uval)
    lines = []
    for ls in res.lines:
        if ls.line in core.deciding:
            lab, cert = line_label(core.comps[ls.line], U[ls.line].u_val, U[ls.line].u_stat, R)
            ls = replace(ls, u=U[ls.line], label=lab, certifies=cert)
        lines.append(ls)
    label = row_label([ls for ls in lines if ls.line in core.deciding])
    E = core.comps[worst]
    return replace(res, lines=tuple(lines), u=U[worst], label=label, worst_line=worst, E=E,
                   certifying=tuple(ls.line for ls in lines if ls.certifies),
                   kappa=kappa(E, U[worst].u_val, R, label))


# E6 row 12's rows read both ways (contract section 4, E6 row 12: "E3a, E5, D1 and L0 both ways; each
# labelled by the worse of the two"): E5 is descriptive and carries no label, so the rule's labels are
# E3a's and L0's (level rows, the 850 C row's) and D1's (a d row, P1), and D1 also takes the larger kappa.
ROW12_LABELLED = ("E3a", "L0", "D1")
# Section 7's reading of a part no row of this engine computes (the Honda's and the Ford's P5: no C3b or
# C3d, contract section 5): a string, never a number, so that no consumer of the six-part sum reads it as
# a band of zero (WP3's fix of 23 October 2026, on the contract review's finding; the contract states no
# rule for it, raised with the team).
PART_WITHOUT_ROW = "NO_ROW: this engine computes no row of the part (no D3 drive, contract section 5)"


def both_ways(snapped, unsnapped):
    """E6 row 12's combination of one row's two readings (contract section 4): (label, kappa, how). The worse
    label of the two and the larger kappa when both have a statistic; the snapped reading alone otherwise,
    `how` saying which (a row with no unsnapped statistic cannot be read both ways, and is not made worse
    by it)."""
    if snapped is None or snapped.no_statistic:
        return None, None, "no statistic"
    if unsnapped is None or unsnapped.no_statistic or unsnapped.label is None:
        return snapped.label, snapped.kappa, "snapped only: the unsnapped reading has no statistic"
    k = [x for x in (snapped.kappa, unsnapped.kappa) if x is not None]
    return (worse(snapped.label, unsnapped.label), (max(k) if k else None),
            "the worse label and the larger kappa of the snapped and unsnapped readings (E6 row 12)")


def section7(results, *, engine, unsnapped, excluded_every):
    """Section 7's consequences for one engine (contract section 7; PLAN.md 6.6): each level row's label for
    the engine's 850 C row (absolute housing statements are not covered whatever it reads), the worst of them;
    each d row's band factor kappa, or DROP for an off d row and for one with no statistic (no deciding line,
    excluded for every constant it claims to test, or E8 with a short subset); each part's kappa, the larger
    of its rows'. A level row excluded for every constant it claims to test "has no statistic and counts as
    such in section 7" (contract section 4, E6), exactly as a d row: no label, listed without a statistic,
    out of the 850 C label (WP3's fix of 23 October 2026). E6 row 12's rows E3a, L0 and D1 take the worse
    label of their snapped and unsnapped readings, and D1 the larger kappa (both_ways; decision 59 as version
    4 reads it): the 850 C label is taken from E3a's and L0's combined labels. A d row that is not validated
    with kappa below 1 has a band narrower than a validated row's, a case section 7 does not write: flagged
    (kappa_below_1_not_validated), never changed here. A part no row of this engine computes reads
    PART_WITHOUT_ROW. The drop order (the Ford, then the Honda; the Mazda last) is applied by a person, from
    these. Both readings are required, so neither can be left out by default (test_engine_threading's rule
    beside `engine`): unsnapped maps E6 row 12's rows to their unsnapped StatResults ({} where none was
    computed), excluded_every maps each row to excluded_for_every_listed_constant's answer ({} where none was
    computed)."""
    level, level_how = {}, {}
    for r in LEVEL_ROWS:
        res = results.get(r)
        if res is not None and not res.no_statistic and excluded_every.get(r):
            level[r], level_how[r] = None, "excluded for every constant it claims to test"
            continue
        if r in ROW12_LABELLED:
            level[r], _k, level_how[r] = both_ways(res, unsnapped.get(r))
        else:
            level[r] = None if (res is None or res.no_statistic) else res.label
            level_how[r] = "no statistic" if level[r] is None else "as computed"
    labs = [x for x in level.values() if x is not None]
    worst_level = None
    for x in labs:
        worst_level = x if worst_level is None else worse(worst_level, x)
    d, drops, narrow = {}, [], []
    for part, rows in PARTS:
        for r in rows:
            res = results.get(r)
            if res is None:
                continue
            if res.no_statistic or excluded_every.get(r):
                d[r] = dict(label=None, kappa=None, drop=True,
                            reason=res.reason if res.no_statistic else "excluded for every constant it claims to test",
                            how="no statistic", kappa_below_1_not_validated=False)
                drops.append(r)
                continue
            if r in ROW12_LABELLED:
                lab, kap, how = both_ways(res, unsnapped.get(r))
            else:
                lab, kap, how = res.label, res.kappa, "as computed"
            low = lab != "validated" and kap is not None and kap < 1.0
            if low:
                narrow.append(r)
            d[r] = dict(label=lab, kappa=kap, drop=lab == "off", reason=None, how=how, kappa_below_1_not_validated=low)
            if lab == "off":
                drops.append(r)
    parts = {}
    for part, rows in PARTS:
        ks = [d[r] for r in rows if r in d]
        if not ks:
            parts[part] = PART_WITHOUT_ROW
        elif any(x["drop"] for x in ks):
            parts[part] = "DROP"
        else:
            parts[part] = max(x["kappa"] for x in ks)
    return dict(engine=engine, level=level, level_how=level_how, level_850c_label=worst_level,
                level_rows_without_statistic=[r for r, v in level.items() if v is None], d=d, parts=parts,
                drop=bool(drops), drop_rows=drops, kappa_below_1_not_validated=narrow)


def reported_labels(results, *, unsnapped, excluded_every):
    """Every gating row's label and kappa as the run reports them (rows.json's `reported`, read by the
    summary): E6 row 12's rows E3a, L0 and D1 by both_ways, every other row as computed (WP3's fix of 23
    October 2026: rows.json's per-row labels were the snapped reading alone); and a row excluded for every
    constant it claims to test with no label and no kappa, as section 7 reads it, since it "has no
    statistic and counts as such" (contract section 4, E6; WP3's second fix of 23 October 2026, on the
    contract review's finding that the summary could read "validated, kappa 1" for an E4b that drops the
    engine). `excluded_every` is excluded_for_every_listed_constant's answer per row, as section7 takes it."""
    out = {}
    for r, res in results.items():
        if KIND.get(r) == "descriptive":
            continue
        if res is not None and not res.no_statistic and excluded_every.get(r):
            out[r] = dict(label=None, kappa=None, how="excluded for every constant it claims to test")
            continue
        if r in ROW12_LABELLED:
            lab, kap, how = both_ways(res, unsnapped.get(r))
        elif res is None or res.no_statistic:
            lab, kap, how = None, None, "no statistic"
        else:
            lab, kap, how = res.label, res.kappa, "as computed"
        out[r] = dict(label=lab, kappa=None if kap is None else float(kap), how=how)
    return out


# =============================================================================================
# 5.2.8 The in-sample stage (contract section 2.4; JSON model_form.in_sample_rules; decision 77)
# =============================================================================================
# DECISION 77 (23 October 2026, adopted under Ghassan's delegation of 21 October, section H): THE IN-SAMPLE
# FORM CRITERION COUNTS A STATISTIC AGAINST A FORM ONLY WHEN ITS FAILURE EXCEEDS ITS SAMPLING NOISE. A gating
# statistic fails a form only if |E_cal| - 2 u_stat > R, u_stat computed exactly as for the held-out rows: the
# core's comp_se, which held_out_row passes to combine as each component's u_stat (the standard error of the
# mean with one row or hold per cluster; the pooled u_stat for pooled rows; L0 at its maximising f, L1 from its
# two extreme lines). A statistic whose 2 u_stat > R neither blocks nor passes, recorded per form (InSample.
# noise), as decision 55's gap is (InSample.no_line). WHY: T0 at the production crank step failed under the
# literal |E_cal| <= R: a form-A truth climbed to A+B+C+D because the in-sample E4b failed at every form from
# noise alone; the rule is the held-out off rule (|E| - 2 u_val > R) with the sampling term the in-sample stage
# has. It moves no R, split, population or statistic, and was decided before any fit, on synthetic data only.
IN_SAMPLE_GATING = tuple(r for r in IN_SAMPLE_ROWS if r != "E8")
# StatResult.passes in-sample from decision 77's outcome: None where the statistic neither blocks nor passes.
IN_SAMPLE_PASSES = {"fails": False, "passes": True, "neither": None}


def in_sample_outcome(E, u_stat, R):
    """Decision 77 on one in-sample component (a deciding line's mean, or a pooled statistic): (outcome, why).
    fails if |E| - 2 u_stat > R (the held-out off rule with the in-sample stage's sampling term); else neither
    if u_stat is undefined (None or NaN: no standard error, which certifies nothing, as held out) or 2 u_stat > R
    (its noise exceeds R); else passes. Each edge on line_label's side: |E| - 2u = R does not fail, 2u = R does
    not exceed R. A non-finite E fails, as it did under |E| <= R, so a broken evaluation never passes a form."""
    a, R = abs(float(E)), float(R)
    if not math.isfinite(a):
        return "fails", "E_cal is not finite"
    if u_stat is None or math.isnan(float(u_stat)):
        return "neither", NO_U_STAT
    u = float(u_stat)
    if u < 0.0:
        raise ValueError(f"u_stat {u!r} is a standard error, never negative")
    if a - 2.0 * u > R:
        return "fails", FAILS_BEYOND_NOISE
    if 2.0 * u > R:
        return "neither", NOISE_EXCEEDS_R
    return "passes", None


def in_sample_judgement(components, R, *, report):
    """Decision 77 on one gating in-sample statistic. `components` {component: (E_c, u_stat_c)}: each deciding
    line's mean (a per-line statistic) or the pooled value, with its u_stat as the held-out run computes it;
    `report` the component the statistic reports (its worst deciding line, decision 57, or its pooled value).
    The statistic fails if any component fails; else passes if any component passes; else neither -- row_label's
    structure held out (any off line makes the row off; a line that cannot certify does not decide; no line
    certifying reads untested). Returns {component, E, u_stat, R, outcome, why, components: {c: {E, u_stat,
    outcome, why}}}, E and u_stat the reported component's."""
    if not components:
        raise ValueError("in_sample_judgement: a statistic without a component has no statistic (decision 55)")
    if report not in components:
        raise ValueError(f"in_sample_judgement: the reported component {report!r} is not one of {sorted(components)}")
    comps = {}
    for c, (E_c, se) in components.items():
        out, why = in_sample_outcome(E_c, se, R)
        comps[c] = dict(E=float(E_c), u_stat=None if se is None else float(se), outcome=out, why=why)
    outs = [v["outcome"] for v in comps.values()]
    outcome = "fails" if "fails" in outs else ("passes" if "passes" in outs else "neither")
    why = None
    if outcome != "passes":
        hits = [(c, v["why"]) for c, v in comps.items() if v["outcome"] == outcome]
        why = hits[0][1] if len(comps) == 1 else "; ".join(f"{c}: {w}" for c, w in hits)
    return dict(component=report, E=comps[report]["E"], u_stat=comps[report]["u_stat"], R=float(R), outcome=outcome,
                why=why, components=comps)


def _in_sample_components(core):
    """{component: (E_c, u_stat_c)} of a core with a statistic: its deciding lines (a per-line row) or its pooled
    value ("pooled", L1's "L1"), u_stat_c the core's comp_se, the held-out run's u_stat (mistake 10)."""
    names = tuple(core.comps) if core.pooled else tuple(core.deciding)
    return {c: (float(core.comps[c]), None if core.comp_se.get(c) is None else float(core.comp_se[c])) for c in names}


@dataclass(frozen=True)
class InSample:
    """One form's in-sample stage (decision 77's criterion, IN_SAMPLE_CRITERION): `failing` the gating statistics
    that fail, `noise` those that neither block nor pass because their noise exceeds R (or they have no u_stat),
    `no_line` those with no statistic (decision 55); the form passes when none fails, and each statistic's record
    (E, u_stat, R, outcome, components) is its StatResult's judgement, written to in_sample.json with it.
    `scatter` is the judgements' components again, {row: {component: (E_c, u_stat_c)}} for every gating
    statistic, beside the criterion: T0 reads it (within_noise)."""
    results: Mapping
    passes: bool
    failing: tuple
    no_line: tuple
    criterion: str
    scatter: Mapping = None
    noise: tuple = ()

    def as_json(self):
        return dict(criterion=self.criterion, statistics={r: s.as_json() for r, s in self.results.items()},
                    passes=bool(self.passes), failing=list(self.failing), no_line=list(self.no_line),
                    noise=list(self.noise))


def in_sample_stage(results):
    """One form's InSample from its in-sample StatResults (`results` {row: StatResult} over rows of
    IN_SAMPLE_ROWS): decision 77's outcomes read off each gating statistic's judgement -- failing those that fail,
    noise those that neither block nor pass -- no_line the rows with no statistic, and the form passes when no
    gating statistic fails; E8 is never counted (decision 39(a)). The one aggregation, for in_sample and for a
    test's hand results."""
    extra = set(results) - set(IN_SAMPLE_ROWS)
    if extra:
        raise ValueError(f"in_sample_stage: {sorted(extra)} are not in-sample statistics ({IN_SAMPLE_ROWS})")
    rows = [r for r in IN_SAMPLE_ROWS if r in results]
    gating = [r for r in rows if r in IN_SAMPLE_GATING]
    for r in rows:
        s = results[r]
        if s.stage != "in_sample":
            raise ValueError(f"in_sample_stage: {r} is a {s.stage} result")
        if r in IN_SAMPLE_GATING and not s.no_statistic and s.judgement is None:
            raise ValueError(f"in_sample_stage: {r} has a statistic and no decision 77 judgement")
    outcome = {r: (None if results[r].judgement is None else results[r].judgement["outcome"]) for r in gating}
    failing = tuple(r for r in gating if outcome[r] == "fails")
    noise = tuple(r for r in gating if outcome[r] == "neither")
    no_line = tuple(r for r in rows if results[r].no_statistic)
    scatter = {r: ({} if results[r].judgement is None else
                   {c: (v["E"], v["u_stat"]) for c, v in results[r].judgement["components"].items()}) for r in gating}
    return InSample(results={r: results[r] for r in rows}, passes=not failing, failing=failing, no_line=no_line,
                    criterion=IN_SAMPLE_CRITERION, scatter=scatter, noise=noise)


def in_sample(evals, *, view):
    """The in-sample stage of one form on the calibration rows' evaluations: every gating statistic with its
    held-out definition (the same row functions), at the contract's R (L1 at 9.9 K, untightened; decision 71)
    and E8 on the contract's P. Fit residuals: no u_val, never labelled; each gating statistic judged by decision
    77 with its held-out u_stat (in_sample_judgement). The form passes when no statistic but E8 fails (decisions
    39(a), 49, 55, 77): in_sample_stage."""
    evals = tuple(evals)
    for e in evals:
        if e.kind == "initial":
            raise ValueError("the in-sample stage reads no High Load Initial row (finding 21)")
    return in_sample_stage({r: ROW_FUNCTIONS[r](evals, view=view, stage="in_sample", tightening=None)
                            for r in IN_SAMPLE_ROWS})


def within_noise(ins, *, z):
    """T0's reading of one form's in-sample stage (amendment D11's T0, its stop rule declared by WP3's fix of
    23 October 2026 before Run 1): a statistic is consistent with the form when every one of its components
    satisfies |E_c| <= R + z u_stat_c (u_stat None: |E_c| <= R), z the standard normal quantile of T0's 99 %
    (the chi-square's two-sided interval), so that sampling error at T0's declared noise cannot fail a seed
    whose rows the form can make; a statistic with no component neither blocks nor passes (decision 55).
    Returns {"ok", "beyond": the rows some component of which lies beyond, "by_row"}."""
    if ins.scatter is None:
        raise ValueError("within_noise reads InSample.scatter, which this in-sample stage does not carry")
    by_row, beyond = {}, []
    for r, comps in ins.scatter.items():
        R = ins.results[r].R
        rec = []
        for c, (E, se) in comps.items():
            edge = R if se is None else R + z * se
            rec.append({"component": c, "E": E, "u_stat": se, "edge": edge, "ok": abs(E) <= edge})
        by_row[r] = rec
        if any(not x["ok"] for x in rec):
            beyond.append(r)
    return {"ok": not beyond, "beyond": beyond, "z": float(z), "by_row": by_row}


# =============================================================================================
# 5.2.9 E6 and C5
# =============================================================================================
def row10_etas(perturbations_e6):
    """E6 row 10's two driveline efficiencies, read from the contract's own band text (JSON perturbations_E6,
    the entry with n 10: "0.86-0.98 (...)"): the efficiencies C3 is re-run at (d3_rows) and decision 44's
    sensitivity of the completion (calibrate_epa.py complete: the K3 knee and the delivery at both ends;
    amendment F3). Moved here from d3_rows by WP3's integration (23 October 2026), so the two callers read
    the band through one parse (mistake 10). `perturbations_e6` is the view's (or the contract's) list."""
    row = next(p for p in perturbations_e6 if p.get("n") == 10)
    lo, hi = row["band"].split()[0].split("-")
    return float(lo), float(hi)


# E6 row 9's two crank angles (engines.Geometry's IVC and EVO), whose "+-10 %" the contract states as "+-10
# crank degrees for IVC and EVO": the one list calibrate_epa's completion and validate_epa's d probe read.
E6_ANGLE_FIELDS = ("ivc_deg", "evo_deg")
_E6_D_PROBE = re.compile(r"every d row's probe is \+-\s*([0-9]+(?:\.[0-9]+)?)\s*%")
_E6_LEVEL_ELSE = re.compile(r"else \+-\s*([0-9]+(?:\.[0-9]+)?)\s*%")
_E6_CAD_ELSE = re.compile(r"\+-\s*([0-9]+(?:\.[0-9]+)?)\s*crank degrees for IVC and EVO")
_E6_ROW4 = re.compile(r"^x([0-9]+(?:\.[0-9]+)?) and x([0-9]+(?:\.[0-9]+)?) each")
_E6_ROW7 = re.compile(r"^KI ([0-9]+(?:\.[0-9]+)?) and ([0-9]+(?:\.[0-9]+)?)")
_E6_ROW13 = re.compile(r"at ([0-9]+(?:\.[0-9]+)?) s and at ([0-9]+(?:\.[0-9]+)?) s")


def e6_band_values(perturbations_e6):
    """The E6 sizes the contract states in its own band text (JSON perturbations_E6), never retyped (mistake
    10), each the decimal printed (a percentage scaled by 1e-2 in the parse, float("10e-2")):

      d_probe_rel    every d row's probe (row 5: "every d row's probe is +-10 %")
      else_rel       the level rows' probe where no consequence is computable (row 5: "... else +-10 %")
      else_cad       row 9's for IVC and EVO ("+-10 crank degrees for IVC and EVO")
      row4_factors   row 4's two factors on each housing constant ("x0.75 and x1.333 each")
      row7_ki        row 7's two knock scales ("KI 0.90 and 1.10")
      row13_dwell_s  row 13's two dwell gates ("the ECU's dwell gate at 0 s and at 30 s")

    A band that does not state one is refused, naming which. Shared by calibrate_epa.py complete (every one)
    and validate_epa.e6_sizes (the d probe); WP3's integration, 23 October 2026."""
    by_n = {p.get("n"): p for p in perturbations_e6}
    band = lambda n: by_n.get(n, {}).get("band", "")                     # noqa: E731
    m = {"d_probe_rel": _E6_D_PROBE.search(band(5)), "else_rel": _E6_LEVEL_ELSE.search(band(5)),
         "else_cad": _E6_CAD_ELSE.search(band(9)), "row4_factors": _E6_ROW4.search(band(4)),
         "row7_ki": _E6_ROW7.search(band(7)), "row13_dwell_s": _E6_ROW13.search(band(13))}
    missing = sorted(k for k, v in m.items() if v is None)
    if missing:
        raise ValueError(f"the contract's perturbations_E6 does not state {', '.join(missing)}")
    return {"d_probe_rel": float(m["d_probe_rel"].group(1) + "e-2"), "else_rel": float(m["else_rel"].group(1) + "e-2"),
            "else_cad": float(m["else_cad"].group(1)),
            "row4_factors": (float(m["row4_factors"].group(1)), float(m["row4_factors"].group(2))),
            "row7_ki": (float(m["row7_ki"].group(1)), float(m["row7_ki"].group(2))),
            "row13_dwell_s": (float(m["row13_dwell_s"].group(1)), float(m["row13_dwell_s"].group(2)))}


def excluded_for(base, probed):
    """A row is excluded for a constant when its statistic moves by less than its own u_val under the
    constant's visibility probe (contract section 4, E6): its pass then certifies nothing about the constant.
    base is the held-out result with its u; probed the same row on the probed plant."""
    if base.no_statistic or probed.no_statistic or base.u is None:
        raise ValueError(f"{base.row}: exclusion needs a statistic on both plants and the base's u_val")
    return abs(probed.E - base.E) < base.u.u_val


def excluded_for_every_listed_constant(row, exclusions, *, tests_lists):
    """Decision 59's counting rule (amendment E4; JSON tests_lists.rule): a row is excluded for every constant it
    claims to test only if every member of its list is perturbed by an E6 row and the row is excluded for each;
    a member no E6 row perturbs counts as not excluded, since the held-out statistic tests it directly; E8 has
    no list and is never excluded. tests_lists is the JSON's tests_lists.lists; exclusions maps each perturbed
    member's text to excluded_for's answer (a perturbed member missing from it is refused)."""
    members = tests_lists[row]
    if not members:
        return False
    for m in members:
        if m["perturbed_by_E6_row"] is None:
            return False
    for m in members:
        if m["member"] not in exclusions:
            raise KeyError(f"{row}: no exclusion recorded for {m['member']!r} (E6 row {m['perturbed_by_E6_row']})")
    return all(bool(exclusions[m["member"]]) for m in members)


def refit_movement(base, variant):
    """E6 rows 1, 3 and 7 (decision 59; amendment E2): every E row's change, no exclusion label. base and
    variant map rows to StatResults."""
    out = {}
    for r in base:
        if r in variant:
            b, v = base[r], variant[r]
            out[r] = None if (b.E is None or v.E is None) else v.E - b.E
    return out


def must_not_move(base, variant, rows):
    """E6 row 2 (contract section 4): E2, D1 and L0 cannot see AFR_st, so each must move by less than its u_val;
    a miss is a finding, not a stop. {row: (dE, u_val, ok)}."""
    out = {}
    for r in rows:
        b, v = base[r], variant[r]
        dE = v.E - b.E
        out[r] = (dE, b.u.u_val, abs(dE) < b.u.u_val)
    return out


@dataclass(frozen=True)
class C5Step:
    """C5 at one step of a scored climb (contract section 5; decisions 70 and 73). margins: (name, |demand /
    threshold - 1|, gates) for the held gear and every rejected higher gear (a stepped box), or T_eco against
    the kickdown threshold at N_eco (the CVT). held is the gear number (1-based) or the CVT's branch.
    no_margin_case names the three steps outside a transition at which no margin gates."""
    k: int
    transition: bool
    gated: bool
    held: str
    margins: tuple
    bar_rpm_margin: float | None
    bar_rpm_margin_frac: float | None
    no_margin_case: str | None
    v_mps: float
    grade: float
    demand_nm: float
    rpm: float


@dataclass(frozen=True)
class C5Climb:
    outcome: str
    gated_share: float
    transition_share: float
    failing_steps: tuple
    thin: bool
    n_steps: int
    n_gated: int


def _force_n(veh, v, accel, grade, rho):
    """The tractive force at one step, the expression the vehicle's own demand() evaluates (engine_env.py:
    Vehicle.demand, EpaVehicle.demand, CvtVehicle.demand). c5_steps checks, at every step, that the held gear's
    torque from it equals demand()'s to the bit, so this cannot drift from the code it copies (mistake 10)."""
    if type(veh) is engine_env.Vehicle:
        return (veh.mass * accel
                + 0.5 * rho * veh.cd_a * v ** 2
                + veh.crr * veh.mass * 9.81 * np.cos(np.arctan(grade))
                + veh.mass * 9.81 * np.sin(np.arctan(grade)))
    return veh.mass * accel + veh.road_force_n(v, grade, rho=rho)


def c5_steps(plant, cycle, *, first, last, dt):
    """C5's margins at every step first..last of a road (contract section 5; decisions 70 and 73), from the
    road's recorded arrays (cycle["v_mps"], cycle["grade"], its ambient and pressure) at the time step it is
    scored at, `dt` (required: the demand reads the speed's change to the next step over dt, and C5 never
    re-samples a road, decision 73). The threshold is the one the code applies: Vehicle.shift_ceiling_nm at
    the held gear's and every rejected higher gear's engine speed; a held gear whose next lower gear is barred
    by SHIFT_RPM_MAX does not gate its own margin, whether or not its demand exceeds its ceiling (the bar is
    tested here directly, not through gear_for's control flow); the held lowest gear has no decision; the
    CVT's T_eco against kickdown_threshold_nm(N_eco), none on its low-speed branch. A step is a transition when
    the grade differs from the step before, or the speed from the step before or after (exact inequality of
    the float64 arrays, a missing neighbour taken as the step itself)."""
    veh = engine_env.vehicle_for(plant.car)
    v_arr = np.asarray(cycle["v_mps"], dtype=float)
    g_arr = np.asarray(cycle["grade"], dtype=float)
    n = len(v_arr)
    if "t" in cycle and n > 1 and float(cycle["t"][1]) - float(cycle["t"][0]) != dt:
        raise ValueError(f"c5_steps: dt {dt!r} is not the road's own time step "
                         f"{float(cycle['t'][1]) - float(cycle['t'][0])!r}")
    if not (0 <= first <= last < n):
        raise ValueError(f"c5_steps: steps {first}..{last} outside the road's {n}")
    rho = cycle.get("p_baro", 101.3) * 1000.0 / (287.0 * cycle["t_amb"])    # SupervisoryTunerEnv.step's own
    cvt = isinstance(veh, engine_env.CvtVehicle)
    out = []
    for k in range(first, last + 1):
        v = float(v_arr[k])
        nxt = float(v_arr[min(k + 1, n - 1)])
        accel = (nxt - v) / dt
        grade = float(g_arr[k])
        kp, kn = max(k - 1, 0), min(k + 1, n - 1)
        transition = bool(g_arr[k] != g_arr[kp] or v_arr[k] != v_arr[kp] or v_arr[k] != v_arr[kn])
        f = _force_n(veh, v, accel, grade, rho)
        t_env, rpm_env = veh.demand(v, accel, grade, rho=rho)
        if cvt:
            ratio, rpm, branch, n_eco, t_eco = veh.ratio_for(v, f)
            t_held = float(f * veh.wheel_r / (ratio * veh.final_drive) / veh.driveline_eff)
            if t_held != t_env:
                raise AssertionError(f"c5_steps: step {k}: the CVT's torque {t_held!r} is not demand()'s {t_env!r}")
            if branch == "low-speed":
                margins, case = (), "cvt_low_speed"
            else:
                thr = veh.kickdown_threshold_nm(n_eco)
                margins, case = (("t_eco_vs_kickdown", abs(t_eco / thr - 1.0), True),), None
            gated = (not transition) and any(m[2] for m in margins)
            out.append(C5Step(k=k, transition=transition, gated=gated, held=branch, margins=margins,
                              bar_rpm_margin=None, bar_rpm_margin_frac=None, no_margin_case=case, v_mps=v,
                              grade=grade, demand_nm=t_held, rpm=float(rpm_env)))
            continue
        g_top = veh.gear_for(v)
        g_held = veh.gear_for(v, force_n=f)

        def rpm_of(g):
            return v / veh.wheel_r * (veh.gears[g] * veh.final_drive) * 60.0 / (2 * np.pi)

        def demand_of(g):
            return f * veh.wheel_r / max(veh.gears[g] * veh.final_drive, .1) / veh.driveline_eff
        t_held = float(demand_of(g_held))
        if t_held != t_env:
            raise AssertionError(f"c5_steps: step {k}: the held gear's torque {t_held!r} is not demand()'s {t_env!r}")
        margins = []
        bar = bar_frac = None
        barred = False
        if g_held > 0:
            bar = float(rpm_of(g_held - 1) - veh.SHIFT_RPM_MAX)
            bar_frac = bar / float(veh.SHIFT_RPM_MAX)
            barred = rpm_of(g_held - 1) > veh.SHIFT_RPM_MAX
        held_gates = g_held > 0 and not barred
        margins.append((f"gear{g_held + 1}_held", abs(demand_of(g_held) / veh.shift_ceiling_nm(rpm_of(g_held)) - 1.0),
                        held_gates))
        for g in range(g_held + 1, g_top + 1):
            margins.append((f"gear{g + 1}_rejected", abs(demand_of(g) / veh.shift_ceiling_nm(rpm_of(g)) - 1.0), True))
        case = None
        if not any(m[2] for m in margins):
            case = "lowest_gear_highest_allowed" if g_held == 0 else "barred_highest_allowed"
        gated = (not transition) and any(m[2] for m in margins)
        out.append(C5Step(k=k, transition=transition, gated=gated, held=str(g_held + 1),
                          margins=tuple((a, float(b), bool(c)) for a, b, c in margins), bar_rpm_margin=bar,
                          bar_rpm_margin_frac=bar_frac, no_margin_case=case, v_mps=v, grade=grade, demand_nm=t_held,
                          rpm=float(rpm_env)))
    return tuple(out)


def c5_margin(plant, cycle, *, dt):
    """The plan's name (PLAN.md 7.4): C5's steps over the whole road."""
    return c5_steps(plant, cycle, first=0, last=len(cycle["v_mps"]) - 1, dt=dt)


def c5_climb(steps, *, margin, thin_share):
    """C5's outcome for one scored climb on one car (contract section 5; decision 73, its cases after version
    4's seventh review): (1) fails when some gated margin is at or below `margin`; (2) thinly checked when none
    is and its gated steps are fewer than thin_share (the contract's 0.5, DESIGN) of its steps; (3) passes
    otherwise. thin flags a climb gated on fewer than thin_share of its steps whatever its case; a climb with
    no gated step is in case (2) or (1), never passes. `margin` is a FRACTION, as the margins are
    (|demand / threshold - 1|); validate_epa's rows.json records decision 64's re-check margin in percent
    beside its fraction (margin_fraction), and a margin of 1 or more is refused here as a percent passed by
    mistake (WP3's fix of 23 October 2026, the contract review's unit trap)."""
    steps = tuple(steps)
    if not steps:
        raise ValueError("c5_climb: a climb with no step")
    if not (0.0 <= float(margin) < 1.0):
        raise ValueError(f"c5_climb: margin {margin!r} is not a fraction in [0, 1): pass rows.json's "
                         "margin_fraction, not its percent")
    gated = [s for s in steps if s.gated]
    failing = tuple(s.k for s in gated if any(gates and m <= margin for (_, m, gates) in s.margins))
    n = len(steps)
    thin = len(gated) < thin_share * n
    outcome = "fails" if failing else ("thinly_checked" if thin else "passes")
    return C5Climb(outcome=outcome, gated_share=len(gated) / n,
                   transition_share=sum(1 for s in steps if s.transition) / n, failing_steps=failing, thin=thin,
                   n_steps=n, n_gated=len(gated))


def cvt_diagnostic(plant, *, v_mps, force_n, margin):
    """Decision 40's diagnostic, reported and never gated (contract section 5, the CVT): with the demand and
    T_del each scaled by (1 +- margin), whether the feasible set {N in the window: P_e/(omega N) <= target_load
    T_del(N)} on the law's own scan grid stays one interval, and whether N* stays on its branch. The branch is
    the law's own (CvtVehicle.ratio_for on a car whose table is scaled)."""
    veh = engine_env.vehicle_for(plant.car)
    if not isinstance(veh, engine_env.CvtVehicle):
        raise TypeError("cvt_diagnostic is the CVT's (decision 40)")
    car = plant.car
    base = veh.ratio_for(v_mps, force_n)[2]
    cases = []
    for sd in (1.0 - margin, 1.0 + margin):
        for st in (1.0 - margin, 1.0 + margin):
            car2 = replace(car, deliverable_torque=tuple((int(r), float(t * st)) for r, t in car.deliverable_torque))
            v2 = engine_env.CvtVehicle(car2)
            f = force_n * sd
            branch = v2.ratio_for(v_mps, f)[2]
            n_w = v_mps / v2.wheel_r * 60.0 / (2 * np.pi)
            n_low = n_w * v2.ratio_low * v2.final_drive
            intervals = None
            if n_low >= car2.cvt_rpm_min:
                n_lo = max(car2.cvt_rpm_min, n_w * v2.ratio_top * v2.final_drive)
                n_hi = min(car2.rpm_max, n_low)
                grid = [float(x) for x in np.arange(n_lo, n_hi, engine_env.CVT_SCAN_RPM)] + [n_hi]
                p_e = f * v_mps / v2.driveline_eff
                omega = 2 * np.pi / 60.0
                ok = [p_e / (x * omega) <= car2.target_load * v2.deliverable_nm(x) for x in grid]
                intervals = sum(1 for i, o in enumerate(ok) if o and (i == 0 or not ok[i - 1]))
            cases.append(dict(demand_scale=sd, t_del_scale=st, branch=branch, feasible_intervals=intervals))
    return dict(branch=base, margin=float(margin),
                connected=all(c["feasible_intervals"] in (None, 0, 1) for c in cases),
                stays_on_branch=all(c["branch"] == base for c in cases), cases=cases)
