"""d3_rows.py -- C3 and C4 of the validation contract: the Mazda model against the CX-9 on Argonne D3,
and the same chain on the Accord, descriptive (results/ENGINE_THRESHOLDS.md section 5; PLAN.md 6.5;
decision 63; amendment C5). Written 23 October 2026, build step 2, WP3.

WHAT IT DOES
  1. read_trace reads one D3 test file: tab-separated latin-1 text, one header row with each channel's
     unit in its name (CATALOGUE.md:273-274). The header is checked FIRST: every channel of the car's
     CarChannels must be there exactly once, under one of the header strings pinned for it, or the read
     stops (HeaderDefect) before any value is converted. Only the pinned columns are ever converted; the
     clipped Eng_FuelFlow_Direct[ccps] is never one of them (mistake 7). Every row after the first
     occurrence of the maximum time is padding and is dropped (CATALOGUE.md:654-657).
  2. segments cuts a trace into the contract's segments: at least 3 s with engine speed within +-25 rpm,
     the PCM MAP refreshed at least twice, the converter locked (engine speed within 1 % of the turbine
     shaft), the A/C compressor off, one gear and coolant at or above 83.8 C, throughout. Every window is
     sized in SECONDS from the time stamps, never in samples (mistakes 8 and 13b: the PCM channels hold
     3-9 samples, CATALOGUE.md:662-663).
  3. channel_checks tests the channels before any comparison (mistake 13): Direct2's integral against
     the summary's modal fuel, the MAF against Direct2 x AFR_st x lambda on closed-loop segments, flat
     maxima repeated across tests found and dropped (mistake 7), and the PCM MAP below barometric at
     closed throttle (mistake 2 was a pressure channel before the throttle).
  4. demand_torque turns the wheel force into the engine's torque demand: Dyno_TractiveForce x r_N/V /
     (gear x final drive) / eta for a stepped box; for the Accord's CVT, whose ratio is not a gear, from
     engine and wheel speed (the power balance F v / (omega_e eta)).
  5. c3_evaluate runs the chain on one segment with a model that is PASSED IN (WP3_INTERFACES.md 3.1:
     this module imports no plant module): at the car's engine speed and coolant, the Mazda model's MAP
     that delivers the demand, by D1's pre-scan and bisection (JSON conventions.statistic_details.d1),
     with the model ECU's own spark at each trial MAP and the model ECU's lambda with its dwell timer run
     along the car's own PCM MAP trace (PLAN.md 6.5; decision 63), and the charge from the environment's
     model at the cell's temperature (MD section 5, chain item 4).
  6. c3_rows computes C3a-C3d (C3a, C3c descriptive; C3b, C3d at R = 16.6 %, deciding with >= 3
     segments and 2 u_stat <= R) and labels them through epa_stats, the one definition of every label
     (mistake 10). c4_accord is the same chain, every row descriptive (MD section 5, C4).

WHAT IT NEVER DOES. It never reads a D3 file in a test: test_d3_rows.py runs on synthetic traces only,
and the first real read is inside validate_epa.py run (amendment C5; MD:451). It opens only the paths it
is given. It imports no plant module and no epa_rows (WP3_INTERFACES.md 3.1): the model, the car record
and the contract's values are passed in. It prints nothing; numbers go to the caller's JSON.

WHAT IS NOT PINNED YET (WP3_INTERFACES.md section 11), and refuses instead of guessing:
  * the summary workbook's column headers. CATALOGUE.md:279 describes its columns in words only
    (test ID, cell temperature, fuel used by bag and modal, fuel heating value, ...). Argonne's
    documentation, ANL_APRF_DynoTestingReference_July2013.pdf (CATALOGUE.md:47, :270; section 5 item 12
    says it was not read for want of a PDF reader, but pdftotext is on this machine's Git Bash), was
    read on 23 October 2026: it is a 2013 presentation whose channel names are generic ("Dyno Tractive
    Effort [N]", "Time [s]", "Fuel flow modal [g/s]"), it prints no summary-workbook header, and it puts
    the fuel's density and net heating value "at the top of the test summary result sheet", not in a
    per-test column. So the heating value's place is open too: SummarySpec reads it as a column, as
    CATALOGUE.md:279 lists it, and whoever pins the spec must check that form first. The workbook is a
    D3 file, which may not be opened to pin them. SUMMARY_CX9 and SUMMARY_ACCORD hold the sheet names
    CATALOGUE.md:277-278 prints and None for every column: read_summary refuses (SummaryNotPinned)
    until each is typed from a source and the read entered in SEEN_BEFORE_THE_FIT.
  * the Accord's time and road-speed headers, taken by analogy and flagged below: the header check
    stops a file that does not carry them, before any value is converted.

The sources read to pin the channel names, 23 October 2026: results/ENGINE_THRESHOLDS.md section 5 and
appendix A; C:\\Users\\badcl\\Desktop\\GRAD-engine-data\\CATALOGUE.md lines 260-282 (the D3 file format and
the summaries), 283-405 (the CX-9's tests), 406-521 (the Accord's), 591-628 (the channels), 652-683 (the
problems); Argonne's reference presentation above (its data-file and summary pages); the CX-9's
engine_specs/cars/cx9_2016_25t.toml [gear_ratios] for the gear channel's codes. No D3 file and no
summary workbook was opened. SOURCES_READ records it for calibrate_epa.SEEN_BEFORE_THE_FIT.
"""
import csv
import dataclasses
import math
import os
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass, field
from typing import Mapping, Optional

import numpy as np

SOURCES_READ = (
    "results/ENGINE_THRESHOLDS.md section 5 and appendix A (23 October 2026, d3_rows.py's channel pins)",
    "GRAD-engine-data/CATALOGUE.md:260-282, 283-405, 406-521, 591-628, 652-683 (the D3 format, tests, "
    "channels and problems; no D3 file and no summary workbook opened)",
    "GRAD-engine-data/anl-d3-documentation/aprf-dyno-testing-reference/ANL_APRF_DynoTestingReference_July2013.pdf "
    "(23 October 2026, through pdftotext into a scratch file: generic 2013 channel names, no summary header; "
    "the fuel's heating value 'at the top of the test summary result sheet')",
    "engine_specs/cars/cx9_2016_25t.toml [gear_ratios] (six forward gears, NH519 Table 4): the gear codes",
)

MPH_TO_KPH = 1.609344          # exact, by the definition of the international mile
RAD_PER_REV_S = 2.0 * math.pi / 60.0


# ============================================================================ the dialect and channels

class HeaderDefect(Exception):
    """A D3 header that lacks a pinned channel, or carries one twice, or carries one in a unit the pin
    does not allow. Raised before any value is converted (WP3_INTERFACES.md 5.9): a coding defect at
    the first real read, recorded by validate_epa as a crash."""


class TraceDefect(Exception):
    """A D3 value that cannot be read as a number, or a time column that runs backwards after the
    padding is dropped. The message names the test, the row and the column, never a value."""


class SummaryNotPinned(Exception):
    """read_summary was asked to read a workbook whose column headers are not pinned from a source
    (WP3_INTERFACES.md section 11). It refuses rather than guess a header (mistake 13)."""


@dataclass(frozen=True)
class Dialect:
    """How a D3 file is written (CATALOGUE.md:273): tab-separated latin-1 text, one header row whose
    names carry the unit. unit_style says how: "bracket", name[unit], as the CX-9's channels print
    (Dyno_TractiveForce[N]; MD section 5), or "double_underscore", name__unit, as the Accord's do
    (Dyno_TractiveForce__N, CATALOGUE.md:617). WP3_INTERFACES.md 5.9 wrote one dialect, brackets after
    the name; CATALOGUE.md:274 and :616-628 show it holds for neither car exactly (the CX-9's time column
    is Time[s]_RawFacilities, the Accord's units follow two underscores), so each accepted header is
    pinned whole in its Channel below and the dialect only names the style."""
    delimiter: str
    encoding: str
    unit_style: str


D3_DIALECT = Dialect(delimiter="\t", encoding="latin-1", unit_style="bracket")
ACCORD_DIALECT = Dialect(delimiter="\t", encoding="latin-1", unit_style="double_underscore")


@dataclass(frozen=True)
class Channel:
    """One quantity a car's D3 file carries, by its role. headers lists every header string accepted for
    it, each with the factor that takes its unit to the role's unit (a speed in mph to km/h): exactly
    one of them must be in the file. A role name is a hypothesis about a channel (mistake 13); the
    checks of channel_checks test the ones a comparison rests on."""
    role: str
    headers: tuple
    unit: str
    source: str


@dataclass(frozen=True)
class CarChannels:
    """A D3 car's channels. lam_form says how the lambda-like channel gives lambda: "inverse",
    lambda = 1/channel (MD section 5: "lambda = 1/Eng_equiv_ratio_b1_s1_PCM[]"), or "afr", lambda =
    channel/AFR_st (the Accord's PGM reports an air-fuel ratio, CATALOGUE.md:624). A role a car does not
    carry is absent from channels, and every rule that needs it is reported as not applied, never
    passed (segment_census). gear_codes: the values of the gear channel that are forward gears of the
    car, required when the car carries one, None otherwise. A gear channel's range is a hypothesis as
    much as its name (mistakes 13 and 18): a sample whose code is not one of them (park, neutral,
    reverse, a shift in progress, whatever the TCM writes there) is not "one gear" and is cut, never
    turned into a demand through a ratio the car does not have."""
    car: str
    dialect: Dialect
    channels: tuple
    lam_form: str
    gear_codes: Optional[tuple]

    def __post_init__(self):
        if self.has("gear") and not self.gear_codes:
            raise ValueError(f"{self.car}: a gear channel needs its forward-gear codes (gear_codes)")
        if not self.has("gear") and self.gear_codes is not None:
            raise ValueError(f"{self.car}: gear_codes without a gear channel")

    def roles(self):
        return tuple(c.role for c in self.channels)

    def has(self, role):
        return role in self.roles()


def _bracket(name, *units):
    return tuple((f"{name}[{u}]", 1.0) for u in units)


# The CX-9's channels (C3). MD section 5 names nine; the time, road-speed and coolant channels it does
# not name are pinned from CATALOGUE.md (WP3_INTERFACES.md 5.9 and section 11), never from a D3 file.
CHANNELS = CarChannels(
    car="cx9_2016",
    dialect=D3_DIALECT,
    lam_form="inverse",
    # 1st to 6th: engine_specs/cars/cx9_2016_25t.toml [gear_ratios] prints six (NH519 Table 4), and
    # Trans_gear_actual_CAN is taken to count them from 1 (the C4 gear agreement compares it with the
    # shift law's gear number, MD section 5). test_d3_rows.Contract checks the six against the toml.
    gear_codes=(1, 2, 3, 4, 5, 6),
    channels=(
        Channel("time", (("Time[s]_RawFacilities", 1.0),), "s",
                "CATALOGUE.md:274, 'the first column, Time[s]_RawFacilities, starts at -30 s'"),
        Channel("force", (("Dyno_TractiveForce[N]", 1.0),), "N", "MD section 5, chain item 1"),
        Channel("gear", (("Trans_gear_actual_CAN[]", 1.0), ("Trans_gear_actual_CAN", 1.0)), "-",
                "MD section 5, chain item 1; JSON c3_segments 'one gear (Trans_gear_actual_CAN)'"),
        Channel("rpm", (("Eng_speed_CAN[rpm]", 1.0), ("Eng_speed_CAN", 1.0)), "rpm",
                "MD section 5 (Eng_speed_CAN); CATALOGUE.md:599 prints Eng_speed_CAN[rpm]"),
        Channel("turbine_rpm", (("Trans_turbine_shaft_speed_TCM", 1.0),)
                + _bracket("Trans_turbine_shaft_speed_TCM", "rpm"), "rpm",
                "MD section 5; CATALOGUE.md:612 (a transmission signal, not turbocharger speed)"),
        Channel("ac", (("HVAC_ACComp_cycling_switch_PCM", 1.0),)
                + _bracket("HVAC_ACComp_cycling_switch_PCM", ""), "-", "MD section 5"),
        Channel("map", (("Eng_ManifoldAir_pressure_sensor_PCM[kPa]", 1.0),), "kPa",
                "MD section 5, populations; CATALOGUE.md:603"),
        Channel("direct2", (("Eng_FuelFlow_Direct2[gps]", 1.0),), "g/s",
                "MD section 5, channels; CATALOGUE.md:601 (not clipped, max 20.56)"),
        Channel("maf", (("Eng_mass_air_flow_PCM[gps]", 1.0),), "g/s", "MD section 5, C3d; CATALOGUE.md:602"),
        Channel("lam", (("Eng_equiv_ratio_b1_s1_PCM[]", 1.0),), "-",
                "MD section 5 (lambda = 1/channel); CATALOGUE.md:606 calls it 'lambda-like, naming UNVERIFIED'"),
        Channel("coolant", (("Eng_coolant_temp_CAN[C]", 1.0),), "C", "CATALOGUE.md:608 (1 C steps)"),
        Channel("speed", (("Dyno_Spd[mph]", MPH_TO_KPH),), "km/h", "CATALOGUE.md:599 (vehicle: Dyno_Spd[mph])"),
    ),
)

# The Accord's channels (C4, descriptive). CATALOGUE.md:614-628 names them; the Accord has no live
# coolant (:625), no gear and no turbine-shaft speed (a CVT), and no A/C channel is named, so those rules
# are reported as not applied. The time and road-speed headers are NOT printed for the Accord:
# CATALOGUE.md:274 gives Time[s]_RawFacilities in the format block both sets share, and Dyno_Spd is the
# CX-9's (:599) written in the Accord's double-underscore style. Both are UNVERIFIED; the header check
# stops a file that lacks them, before any value is converted.
ACCORD_CHANNELS = CarChannels(
    car="accord_2018",
    dialect=ACCORD_DIALECT,
    lam_form="afr",
    gear_codes=None,
    channels=(
        Channel("time", (("Time[s]_RawFacilities", 1.0), ("Time__s_RawFacilities", 1.0)), "s",
                "CATALOGUE.md:274 (the shared format block); UNVERIFIED for the Accord"),
        Channel("force", (("Dyno_TractiveForce__N", 1.0),), "N", "CATALOGUE.md:617"),
        Channel("rpm", (("Eng_speed_CAN7__rpm", 1.0),), "rpm", "CATALOGUE.md:616"),
        Channel("map", (("Eng_MAP_sensor_highres_CAN7__kPa", 1.0),), "kPa", "CATALOGUE.md:621"),
        Channel("direct2", (("Eng_FuelFlow_Direct2__gps", 1.0),), "g/s",
                "CATALOGUE.md:618 (clips at 12.376 in 4 files: a flat maximum, dropped)"),
        Channel("maf", (("Eng_MAF_sensor_PGM__gps", 1.0),), "g/s", "CATALOGUE.md:620"),
        Channel("lam", (("Eng_airfuel_ratio_PGM", 1.0),), "AFR", "CATALOGUE.md:624 (an air-fuel ratio)"),
        Channel("speed", (("Dyno_Spd__mph", MPH_TO_KPH), ("Dyno_Spd__kph", 1.0)), "km/h",
                "by analogy with CATALOGUE.md:599; UNVERIFIED for the Accord"),
    ),
)

# Never converted, whatever the header holds (mistake 7: it clips at 17.385, CATALOGUE.md:665).
NEVER_READ = ("Eng_FuelFlow_Direct[ccps]", "Eng_FuelFlow_Direct__ccps")


def resolve_header(header, *, channels):
    """{role: (column index, factor)} for every channel of the car, from the header row alone. Stops with
    HeaderDefect when a channel has no accepted header in it, or more than one column matches it (the
    same name twice, or two accepted spellings): which column a role reads must be certain before any
    value is converted. A NEVER_READ name can never be resolved, by construction, and is asserted."""
    names = [h.strip() for h in header]
    out, problems = {}, []
    for ch in channels.channels:
        hits = [(i, f) for (h, f) in ch.headers for i, n in enumerate(names) if n == h]
        if len(hits) != 1:
            problems.append(f"{ch.role} ({' or '.join(h for h, _ in ch.headers)}): "
                            f"{'absent' if not hits else f'{len(hits)} columns'}")
            continue
        out[ch.role] = hits[0]
    if problems:
        raise HeaderDefect(f"{channels.car} header: " + "; ".join(problems))
    for role, (i, _) in out.items():
        assert names[i] not in NEVER_READ, (role, names[i])
    return out


# ============================================================================ the trace

@dataclass(frozen=True, eq=False)
class Trace:
    """One D3 test, in the roles of its CarChannels: float64 arrays of one length, None for a role the car
    does not carry. Units: s, N, gear number, rpm, rpm, switch, kPa, g/s, g/s, the lambda channel as read,
    degC, km/h. padding_dropped counts the rows dropped after the first maximum time. gear_codes are the
    car's (CarChannels.gear_codes)."""
    test: str
    car: str
    lam_form: str
    gear_codes: Optional[tuple]
    t_s: np.ndarray
    force_n: Optional[np.ndarray]
    gear: Optional[np.ndarray]
    rpm: Optional[np.ndarray]
    turbine_rpm: Optional[np.ndarray]
    ac: Optional[np.ndarray]
    map_kpa: Optional[np.ndarray]
    direct2_gps: Optional[np.ndarray]
    maf_gps: Optional[np.ndarray]
    lam_raw: Optional[np.ndarray]
    coolant_c: Optional[np.ndarray]
    speed_kph: Optional[np.ndarray]
    padding_dropped: int

    def __len__(self):
        return len(self.t_s)


# role -> Trace field
_FIELD = {"time": "t_s", "force": "force_n", "gear": "gear", "rpm": "rpm", "turbine_rpm": "turbine_rpm",
          "ac": "ac", "map": "map_kpa", "direct2": "direct2_gps", "maf": "maf_gps", "lam": "lam_raw",
          "coolant": "coolant_c", "speed": "speed_kph"}


def drop_padding(t_s):
    """How many leading rows to keep: everything up to and including the first occurrence of the maximum
    time. "17 files end with 298-300 rows whose timestamp is frozen at the last value ... Drop every row
    after the first occurrence of the maximum time" (CATALOGUE.md:654-657)."""
    t = np.asarray(t_s, dtype=float)
    if t.size == 0:
        return 0
    return int(np.nanargmax(t)) + 1


def make_trace(test, *, channels, arrays):
    """A Trace from role -> array (any role the car does not carry left out), with the padding dropped and
    the time checked strictly increasing afterwards (CATALOGUE.md:657: "elsewhere, time is monotonic").
    The one constructor read_trace and the synthetic traces of test_d3_rows.py share, so a test builds
    exactly what a real read builds."""
    if set(arrays) - set(channels.roles()):
        raise ValueError(f"{test}: roles {sorted(set(arrays) - set(channels.roles()))} are not {channels.car}'s")
    if set(channels.roles()) - set(arrays):
        raise ValueError(f"{test}: roles {sorted(set(channels.roles()) - set(arrays))} missing")
    t = np.asarray(arrays["time"], dtype=float)
    if any(len(a) != len(t) for a in arrays.values()):
        raise ValueError(f"{test}: the channels differ in length")
    keep = drop_padding(t)
    cols = {r: np.asarray(a, dtype=float)[:keep] for r, a in arrays.items()}
    tt = cols["time"]
    if not np.all(np.isfinite(tt)):
        raise TraceDefect(f"{test}: a time stamp is not a number at row {int(np.argmin(np.isfinite(tt))) + 2}")
    if tt.size > 1 and not np.all(np.diff(tt) > 0.0):
        raise TraceDefect(f"{test}: time does not increase at row {int(np.argmin(np.diff(tt) > 0.0)) + 3} "
                          "after the padding was dropped")
    kw = {f: None for f in _FIELD.values()}
    for r, a in cols.items():
        kw[_FIELD[r]] = a
    return Trace(test=str(test), car=channels.car, lam_form=channels.lam_form, gear_codes=channels.gear_codes,
                 padding_dropped=int(len(t) - keep), **kw)


def read_trace(path, *, test, channels):
    """Read one D3 test file at `path` as the car's `channels` say (no default car: the CX-9's CHANNELS for
    C3, ACCORD_CHANNELS for C4; mistake 1). The header row is resolved first (resolve_header) and a defect
    stops the read before any value is converted. Then only the resolved columns are converted, an empty
    cell to NaN; a cell that is not a number stops the read naming the test, row and column (TraceDefect),
    never the value. Rows are numbered as in the file (the header is row 1)."""
    d = channels.dialect
    with open(path, encoding=d.encoding, newline="") as fh:
        rd = csv.reader(fh, delimiter=d.delimiter)
        header = next(rd, None)
        if header is None:
            raise HeaderDefect(f"{test}: the file is empty")
        cols = resolve_header(header, channels=channels)
        values = {r: [] for r in cols}
        for k, rec in enumerate(rd, start=2):
            if not rec or all(not c.strip() for c in rec):
                continue
            for r, (i, f) in cols.items():
                cell = rec[i].strip() if i < len(rec) else ""
                if cell == "":
                    values[r].append(math.nan)
                    continue
                try:
                    values[r].append(float(cell) * f)
                except ValueError:
                    raise TraceDefect(f"{test}: row {k}, column {header[i].strip()!r} is not a number") from None
    return make_trace(test, channels=channels, arrays=values)


def lam_of(trace, *, afr_st):
    """lambda from the car's lambda channel, sample by sample: 1/channel on the CX-9 (MD section 5), the
    PGM's air-fuel ratio over AFR_st on the Accord. afr_st is the fuel's (decision 63: the D3 fuel's
    AFR_st taken as 14.559, the EPA Mazda batch's), passed by the caller, never typed here."""
    raw = trace.lam_raw
    with np.errstate(divide="ignore", invalid="ignore"):
        if trace.lam_form == "inverse":
            return np.where(raw > 0.0, 1.0 / raw, np.nan)
        if trace.lam_form == "afr":
            return raw / float(afr_st)
    raise ValueError(f"{trace.test}: unknown lambda form {trace.lam_form!r}")


# ============================================================================ segments

@dataclass(frozen=True)
class SegmentRules:
    """The contract's segment rules (MD section 5; JSON c3_segments), every window in seconds (mistakes 8,
    13b). min_s: the segment's span, last time stamp minus first. rpm_band: every sample within +-rpm_band
    of the segment's mid-range, so the range is at most 2 rpm_band. map_refreshes: the PCM MAP's value
    changes at least this often inside the segment (a refresh that repeats a value is invisible, so this
    counts a lower bound and never admits a segment the rule would refuse). converter_ratio:
    |rpm/turbine - 1| <= it at every sample (the speed ratio 0.99 of MD section 5). ac_off: the A/C switch
    reads 0 at every sample. one_gear: one of the car's forward gears (CarChannels.gear_codes) throughout,
    unchanged. coolant_min_c: the map's lowest,
    83.8 C. Two more, DESIGN, not the contract's: max_gap_s, a step between time stamps above which a
    segment may not reach across (CATALOGUE.md:657: no step over 0.10 s exists, so a larger one is a
    defect, never bridged), and min_speed_kph, applied only where the demand comes from the speed ratio
    (a car with no gear channel, the Accord), since the ratio needs the car to move."""
    min_s: float
    rpm_band: float
    map_refreshes: int
    converter_ratio: float
    ac_off: bool
    one_gear: bool
    coolant_min_c: float
    max_gap_s: float
    min_speed_kph: float


CONTRACT_SEGMENTS = SegmentRules(min_s=3.0, rpm_band=25.0, map_refreshes=2, converter_ratio=0.01, ac_off=True,
                                 one_gear=True, coolant_min_c=83.8, max_gap_s=0.15, min_speed_kph=5.0)


def check_rules_against_contract(rules, c3_segments_text):
    """The contract numbers of `rules` that the contract's own text does not state (JSON c3_segments), as
    strings: () when every one is there. validate_epa runs it on the contract it armed, so the rules this
    module applies are the contract's, not a copy that drifted (mistake 10)."""
    need = {"min_s": f"at least {rules.min_s:g} s", "rpm_band": f"+-{rules.rpm_band:g} rpm",
            "map_refreshes": "refreshed at least twice" if rules.map_refreshes == 2 else str(rules.map_refreshes),
            "converter_ratio": f"within {100 * rules.converter_ratio:g} %",
            "coolant_min_c": f"({rules.coolant_min_c:g} C)"}
    out = tuple(f"{k}: {v!r}" for k, v in need.items() if v not in c3_segments_text)
    if rules.ac_off and "A/C compressor off" not in c3_segments_text:
        out += ("ac_off",)
    if rules.one_gear and "one gear" not in c3_segments_text:
        out += ("one_gear",)
    return out


@dataclass(frozen=True)
class Segment:
    """One segment of a trace: samples i0..i1 inclusive, t0_s..t1_s. The means are over the segment's
    samples (a scan-tool channel's held values are a zero-order hold, CATALOGUE.md:662-663, and the window
    spans at least two of its refreshes). gear is None on a car without a gear channel; coolant_c_min and
    coolant_c_mean None without a coolant channel. power_w_mean is the mean of force x road speed (the
    CVT's demand). lam_d3 are the car's own lambda readings (lam_of), for the closed-loop test.
    direct2_max and maf_max let a saturated value inside the segment be found (channel_checks)."""
    test: str
    i0: int
    i1: int
    t0_s: float
    t1_s: float
    n: int
    gear: Optional[int]
    rpm_mean: float
    pcm_map_kpa_mean: float
    force_n_mean: float
    power_w_mean: Optional[float]
    speed_kph_mean: Optional[float]
    direct2_gps_mean: float
    maf_gps_mean: float
    equiv_ratio_mean: float
    lam_d3_mean: float
    lam_d3_min: float
    lam_d3_max: float
    coolant_c_min: Optional[float]
    coolant_c_mean: Optional[float]
    map_refreshes: int
    direct2_max: float
    maf_max: float

    def key(self):
        return (self.test, self.i0)

    def as_json(self):
        return {k: (float(v) if isinstance(v, (float, np.floating)) else v)
                for k, v in dataclasses.asdict(self).items()}


def sample_mask(trace, *, rules):
    """{rule: boolean array} of the per-sample rules, True where the sample passes, each over the whole
    trace; a rule whose channel the car lacks is absent here and listed by rules_not_applied. A NaN fails
    every rule it enters (an unknown A/C state is not "off")."""
    n = len(trace)
    out = {}
    fin = np.ones(n, dtype=bool)
    for arr in (trace.force_n, trace.rpm, trace.map_kpa, trace.direct2_gps, trace.maf_gps, trace.lam_raw):
        if arr is not None:
            fin &= np.isfinite(arr)
    out["finite"] = fin
    if trace.turbine_rpm is not None:
        with np.errstate(divide="ignore", invalid="ignore"):
            r = np.abs(trace.rpm / trace.turbine_rpm - 1.0)
        out["converter_locked"] = (trace.turbine_rpm > 0.0) & (r <= rules.converter_ratio)
    if trace.ac is not None and rules.ac_off:
        out["ac_off"] = trace.ac == 0.0
    if trace.gear is not None and rules.one_gear:
        # a forward gear of the car, by its code (CarChannels.gear_codes; mistake 18): NaN is none
        out["in_gear"] = np.isin(trace.gear, np.asarray(trace.gear_codes, dtype=float))
    if trace.coolant_c is not None:
        out["coolant"] = np.isfinite(trace.coolant_c) & (trace.coolant_c >= rules.coolant_min_c)
    if trace.gear is None:
        sp = trace.speed_kph
        out["moving"] = (np.isfinite(sp) & (sp >= rules.min_speed_kph)) if sp is not None else np.zeros(n, bool)
    return out


def rules_not_applied(trace, *, rules):
    """The contract's rules this trace cannot apply, because its car lacks the channel: reported beside
    the result (C4's Accord), never counted as passed."""
    out = []
    if trace.turbine_rpm is None:
        out.append("converter_locked (no turbine-shaft speed)")
    if rules.ac_off and trace.ac is None:
        out.append("ac_off (no A/C channel)")
    if rules.one_gear and trace.gear is None:
        out.append("one_gear (no gear channel: a CVT)")
    if trace.coolant_c is None:
        out.append("coolant (no live coolant channel)")
    return tuple(out)


def _runs(ok, t, gear, max_gap_s):
    """[(a, b)] inclusive index runs where ok holds, the gear does not change and no time step exceeds
    max_gap_s."""
    n = len(ok)
    brk = np.zeros(n, dtype=bool)
    if n > 1:
        brk[1:] = np.diff(t) > max_gap_s
        if gear is not None:
            brk[1:] |= gear[1:] != gear[:-1]
    runs, a = [], None
    for k in range(n):
        if not ok[k] or (a is not None and brk[k]):
            if a is not None:
                runs.append((a, k - 1))
                a = None
        if ok[k] and a is None:
            a = k
    if a is not None:
        runs.append((a, n - 1))
    return runs


def _windows(t, rpm, map_kpa, a, b, rules):
    """Non-overlapping windows inside run a..b, left to right: from each start the longest window whose
    rpm range is at most 2 rpm_band; it is a segment when it spans min_s seconds and the MAP changes
    map_refreshes times, and the next start is just past it; otherwise the start moves one sample on. Two
    pointers and monotone queues, so a run is scanned once."""
    from collections import deque
    changes = np.zeros(b - a + 1, dtype=np.int64)
    if b > a:
        changes[1:] = (map_kpa[a + 1:b + 1] != map_kpa[a:b]).astype(np.int64)
    cum = np.cumsum(changes)
    out = []
    i, j = a, a                      # window [i, j) over absolute indices
    qmax, qmin = deque(), deque()
    width = 2.0 * rules.rpm_band
    while i <= b:
        if j < i:
            j = i
            qmax.clear(); qmin.clear()
        while j <= b:
            x = rpm[j]
            hi = max(x, rpm[qmax[0]]) if qmax else x
            lo = min(x, rpm[qmin[0]]) if qmin else x
            if hi - lo > width:
                break
            while qmax and rpm[qmax[-1]] <= x:
                qmax.pop()
            qmax.append(j)
            while qmin and rpm[qmin[-1]] >= x:
                qmin.pop()
            qmin.append(j)
            j += 1
        last = j - 1
        refresh = int(cum[last - a] - cum[i - a])
        if last >= i and t[last] - t[i] >= rules.min_s and refresh >= rules.map_refreshes:
            out.append((i, last, refresh))
            i = j
            qmax.clear(); qmin.clear()
            continue
        if qmax and qmax[0] == i:
            qmax.popleft()
        if qmin and qmin[0] == i:
            qmin.popleft()
        i += 1
    return out


def segments(trace, *, rules, afr_st):
    """The trace's segments under `rules` (MD section 5; PLAN.md 6.5): runs of samples that pass every
    per-sample rule (sample_mask) in one gear without a time gap, cut into windows of at least min_s
    seconds with engine speed within +-rpm_band and the PCM MAP refreshed map_refreshes times. afr_st
    serves only the Accord's lambda (lam_of)."""
    masks = sample_mask(trace, rules=rules)
    ok = np.logical_and.reduce(list(masks.values()))
    t, rpm, mp = trace.t_s, trace.rpm, trace.map_kpa
    lam = lam_of(trace, afr_st=afr_st)
    power = trace.force_n * trace.speed_kph / 3.6 if trace.speed_kph is not None else None
    out = []
    for a, b in _runs(ok, t, trace.gear if rules.one_gear else None, rules.max_gap_s):
        for i0, i1, refresh in _windows(t, rpm, mp, a, b, rules):
            s = slice(i0, i1 + 1)
            out.append(Segment(
                test=trace.test, i0=int(i0), i1=int(i1), t0_s=float(t[i0]), t1_s=float(t[i1]),
                n=int(i1 - i0 + 1), gear=int(trace.gear[i0]) if trace.gear is not None else None,
                rpm_mean=float(np.mean(rpm[s])), pcm_map_kpa_mean=float(np.mean(mp[s])),
                force_n_mean=float(np.mean(trace.force_n[s])),
                power_w_mean=float(np.mean(power[s])) if power is not None else None,
                speed_kph_mean=float(np.mean(trace.speed_kph[s])) if trace.speed_kph is not None else None,
                direct2_gps_mean=float(np.mean(trace.direct2_gps[s])), maf_gps_mean=float(np.mean(trace.maf_gps[s])),
                equiv_ratio_mean=float(np.mean(trace.lam_raw[s])), lam_d3_mean=float(np.mean(lam[s])),
                lam_d3_min=float(np.min(lam[s])), lam_d3_max=float(np.max(lam[s])),
                coolant_c_min=float(np.min(trace.coolant_c[s])) if trace.coolant_c is not None else None,
                coolant_c_mean=float(np.mean(trace.coolant_c[s])) if trace.coolant_c is not None else None,
                map_refreshes=int(refresh), direct2_max=float(np.max(trace.direct2_gps[s])),
                maf_max=float(np.max(trace.maf_gps[s]))))
    return tuple(out)


def segment_census(trace, *, rules):
    """{rule: samples it cuts} for each per-sample rule on its own, the samples left after all of them,
    and the rules not applied: what each rule removed, reported beside C3 (WP3_INTERFACES.md 9.10: each
    rule shown to cut)."""
    masks = sample_mask(trace, rules=rules)
    ok = np.logical_and.reduce(list(masks.values()))
    return {"samples": int(len(trace)), "padding_dropped": int(trace.padding_dropped),
            "cut_by": {k: int(np.count_nonzero(~v)) for k, v in masks.items()},
            "pass_every_sample_rule": int(np.count_nonzero(ok)),
            "not_applied": list(rules_not_applied(trace, rules=rules))}


# ============================================================================ the summary workbook

@dataclass(frozen=True)
class SummarySpec:
    """Where a D3 test summary keeps what C3 reads (decision 63): the sheet, and for each role the header
    as the workbook prints it, None until pinned from a source (WP3_INTERFACES.md section 11). The modal
    fuel's factor takes its unit to grams; the heating value's to BTU/lbm; baro, where the summary has
    one (the Accord's, CATALOGUE.md:279), to kPa."""
    car: str
    sheet: str
    test_id: Optional[str]
    cell_temp_c: Optional[str]
    modal_fuel: Optional[str]
    modal_fuel_to_g: Optional[float]
    fuel_lhv: Optional[str]
    fuel_lhv_to_btu_per_lbm: Optional[float]
    baro: Optional[str]
    baro_to_kpa: Optional[float]

    def unpinned(self):
        need = ("test_id", "cell_temp_c", "modal_fuel", "modal_fuel_to_g", "fuel_lhv", "fuel_lhv_to_btu_per_lbm")
        return tuple(k for k in need if getattr(self, k) is None)


# The sheets are CATALOGUE.md:277-278's; the columns are NOT pinned (see the module docstring).
SUMMARY_CX9 = SummarySpec(car="cx9_2016", sheet="Extended Test Summary", test_id=None, cell_temp_c=None,
                          modal_fuel=None, modal_fuel_to_g=None, fuel_lhv=None, fuel_lhv_to_btu_per_lbm=None,
                          baro=None, baro_to_kpa=None)
SUMMARY_ACCORD = SummarySpec(car="accord_2018", sheet="G2_TestSummary", test_id=None, cell_temp_c=None,
                             modal_fuel=None, modal_fuel_to_g=None, fuel_lhv=None, fuel_lhv_to_btu_per_lbm=None,
                             baro=None, baro_to_kpa=None)


# Each engine's summary workbook spec (validate_epa.D3_ENGINE names the same objects; the Ford has no D3
# drive, contract section 5), and the pin check calibrate_epa.py t0 and fit and validate_epa.py arm make
# before anything starts (WP3's fix of 23 October 2026): a column pinned after the first fit is a change to
# this file, which only the defect route admits (amendment C10).
SUMMARY_FOR = {"mazda_25t": SUMMARY_CX9, "honda_l15b7": SUMMARY_ACCORD}


def unpinned_for(engine_name):
    """The summary columns of `engine_name`'s D3 chain not yet pinned from a source, as
    "SUMMARY_<car>.<field>" strings; () for an engine without a D3 chain. Reads no file."""
    spec = SUMMARY_FOR.get(engine_name)
    return () if spec is None else tuple(f"{spec.car}.{k}" for k in spec.unpinned())


@dataclass(frozen=True)
class SummaryRow:
    """One test of the summary, in SI-ish units: the cell temperature (degC), the modal fuel (g), the
    fuel's heating value (BTU/lbm, the unit CATALOGUE.md:291 and the contract print), barometric pressure
    (kPa) or None."""
    test: str
    cell_temp_c: float
    modal_fuel_g: float
    fuel_lhv_btu_per_lbm: float
    baro_kpa: Optional[float]


_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main",
       "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
       "p": "http://schemas.openxmlformats.org/package/2006/relationships"}


def _col_index(ref):
    letters = "".join(ch for ch in ref if ch.isalpha())
    k = 0
    for ch in letters.upper():
        k = k * 26 + (ord(ch) - 64)
    return k - 1


def _sheet_rows(path, sheet):
    """The cells of one worksheet as lists of strings (a number as its stored text), through zipfile and
    xml.etree, as epa_map.py reads its workbooks (never importing it: amendment C3)."""
    with zipfile.ZipFile(path) as z:
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rid = None
        for s in wb.find("m:sheets", _NS):
            if s.get("name") == sheet:
                rid = s.get(f"{{{_NS['r']}}}id")
        if rid is None:
            raise HeaderDefect(f"{os.path.basename(path)}: no sheet {sheet!r}")
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = next(r.get("Target") for r in rels.findall("p:Relationship", _NS) if r.get("Id") == rid)
        target = target.lstrip("/")
        target = target if target.startswith("xl/") else "xl/" + target
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        ws = ET.fromstring(z.read(target))
    rows = []
    for row in ws.iter(f"{{{_NS['m']}}}row"):
        cells = {}
        for k, c in enumerate(row.findall("m:c", _NS)):
            ref = c.get("r")
            col = _col_index(ref) if ref else k
            typ = c.get("t")
            v = c.find("m:v", _NS)
            if typ == "s" and v is not None:
                text = shared[int(v.text)]
            elif typ == "inlineStr":
                text = "".join(t.text or "" for t in c.iter(f"{{{_NS['m']}}}t"))
            else:
                text = v.text if v is not None and v.text is not None else ""
            cells[col] = text
        rows.append([cells.get(k, "") for k in range(max(cells) + 1)] if cells else [])
    return rows


def _test_id(text):
    s = text.strip()
    try:
        x = float(s)
    except ValueError:
        return s
    return str(int(x)) if x == int(x) else s


def read_summary(path, *, spec):
    """{test: SummaryRow} from a D3 test-summary workbook (decision 63: hashed at the arming against
    MANIFEST.csv; the cell temperature is the test's metadata). Refuses (SummaryNotPinned) while any of the
    spec's columns is not pinned, before the file is opened. The header row is the first row that holds
    every pinned header; a workbook without one stops (HeaderDefect) before any value is converted. Only
    the pinned columns are converted; a row without a test id ends nothing and is skipped."""
    miss = spec.unpinned()
    if miss:
        raise SummaryNotPinned(f"{spec.car} summary: {', '.join(miss)} not pinned from a source "
                               "(WP3_INTERFACES.md section 11)")
    rows = _sheet_rows(path, spec.sheet)
    want = [spec.test_id, spec.cell_temp_c, spec.modal_fuel, spec.fuel_lhv] + ([spec.baro] if spec.baro else [])
    hdr_at, idx = None, None
    for k, r in enumerate(rows):
        names = [c.strip() for c in r]
        if all(names.count(w) == 1 for w in want):
            hdr_at, idx = k, {w: names.index(w) for w in want}
            break
    if hdr_at is None:
        raise HeaderDefect(f"{os.path.basename(path)}: no row of sheet {spec.sheet!r} holds every pinned header once")
    out = {}
    for k, r in enumerate(rows[hdr_at + 1:], start=hdr_at + 2):
        def cell(name):
            i = idx[name]
            return r[i].strip() if i < len(r) else ""
        tid = cell(spec.test_id)
        if not tid:
            continue
        try:
            row = SummaryRow(
                test=_test_id(tid), cell_temp_c=float(cell(spec.cell_temp_c)),
                modal_fuel_g=float(cell(spec.modal_fuel)) * spec.modal_fuel_to_g,
                fuel_lhv_btu_per_lbm=float(cell(spec.fuel_lhv)) * spec.fuel_lhv_to_btu_per_lbm,
                baro_kpa=float(cell(spec.baro)) * spec.baro_to_kpa if spec.baro else None)
        except ValueError:
            raise TraceDefect(f"{os.path.basename(path)}: sheet row {k} holds a pinned cell that is not a number") from None
        if row.test in out:
            raise TraceDefect(f"{os.path.basename(path)}: test {row.test} appears twice")
        out[row.test] = row
    return out


# ============================================================================ the channel checks

@dataclass(frozen=True)
class ChannelRules:
    """The channel checks' settings, each DESIGN with its reason (none is a contract number but the
    lambda band):
    flat_min_s       a flat maximum is held at least this long in each test it marks: 1 s, ten samples,
                     beyond the 3-9 samples a PCM channel holds a value at the 90th percentile
                     (CATALOGUE.md:662-663), so a scan tool's hold is not taken for saturation;
    flat_min_tests   and it is the maximum of at least this many tests, to the bit (mistake 7: "a flat
                     maximum repeated across drives is the tell");
    closed_loop_band a segment is closed-loop when every sample's lambda is within this of 1: the width
                     of the contract's lambda~1 band, |lambda - lambda_ref| <= 0.02 (JSON
                     conventions.populations),
                     centred on 1 here, since lambda_ref is the EPA map's reference for its own sensor,
                     not the D3 car's;
    idle_max_kph, idle_min_rpm, idle_min_s
                     closed throttle is idle: the car standing, the engine running, for at least idle_min_s
                     seconds (a window in seconds, mistake 8);
    closed_throttle_max_ratio
                     the PCM MAP at idle must read below this fraction of barometric. A manifold sensor
                     reads about a third of an atmosphere at idle; a sensor before the throttle, mistake
                     2's, reads barometric there. 0.7 separates the two with room on both sides;
    integrate_from_s Direct2 is integrated from this time stamp: 0 s, the test's start, since every file
                     carries 30 s of pre-roll before it (CATALOGUE.md:274); the pre-roll's share is
                     reported beside the ratio;
    max_gap_s        an idle window never reaches across a larger step between time stamps (as
                     SegmentRules.max_gap_s)."""
    flat_min_s: float
    flat_min_tests: int
    closed_loop_band: float
    idle_max_kph: float
    idle_min_rpm: float
    idle_min_s: float
    closed_throttle_max_ratio: float
    integrate_from_s: float
    max_gap_s: float


CHANNEL_RULES = ChannelRules(flat_min_s=1.0, flat_min_tests=2, closed_loop_band=0.02, idle_max_kph=1.0,
                             idle_min_rpm=400.0, idle_min_s=3.0, closed_throttle_max_ratio=0.7,
                             integrate_from_s=0.0, max_gap_s=0.15)


def flat_maxima(traces, *, roles, rules):
    """{role: value} for each role whose maximum is a flat maximum repeated across tests (mistake 7): the
    same value, to the bit, is the maximum of at least flat_min_tests tests and is held for at least
    flat_min_s seconds in each (counted as samples at the value times the test's median time step). A
    role with none is absent."""
    out = {}
    for role in roles:
        tops = {}
        for tr in traces:
            a = getattr(tr, _FIELD[role])
            if a is None or not np.any(np.isfinite(a)):
                continue
            top = float(np.nanmax(a))
            dt = float(np.median(np.diff(tr.t_s))) if len(tr) > 1 else 0.0
            held = int(np.count_nonzero(a == top)) * dt
            if held >= rules.flat_min_s:
                tops.setdefault(top, []).append(tr.test)
        hits = sorted((v for v, ts in tops.items() if len(ts) >= rules.flat_min_tests), reverse=True)
        if hits:
            out[role] = hits[0]
    return out


def _integral(t, y, t_from):
    """Trapezoid integral of y over t >= t_from, skipping an interval with a NaN end, and how many were."""
    keep = t >= t_from
    t, y = t[keep], y[keep]
    if t.size < 2:
        return 0.0, 0
    good = np.isfinite(y[1:]) & np.isfinite(y[:-1])
    seg = 0.5 * (y[1:] + y[:-1]) * np.diff(t)
    return float(np.sum(seg[good])), int(np.count_nonzero(~good))


@dataclass(frozen=True)
class ChannelChecks:
    """What channel_checks found. direct2_vs_summary: per test (test, integral of Direct2 in g, the
    summary's modal fuel in g, ratio, the pre-roll's grams, NaN intervals skipped). u_d_fuel: |median
    ratio - 1|, the common part Direct2's disagreement with the facility adds to the fuel's u_D (MD section
    5). maf_ratio_median: r~, the median over closed-loop segments of MAF / (Direct2 x AFR_st x lambda);
    u_d_air: sqrt((r~ - 1)^2 + u_afr_st^2), with u_afr_st decision 63's unsourced AFR_st term, None when
    the caller did not size it (then listed in unsourced and the air's u_D carries |r~ - 1| alone, said
    so). maf_ratio_if_lambda_is_the_channel: the same median with lambda read as the channel itself, not
    its inverse, and the two medians on the open-loop segments beside them: the test of MD section 5's
    reading (lambda = 1/channel) against CATALOGUE.md:606 ("lambda-like"; first percentile 0.66-0.73 at
    WOT; clipped at 1.999 on fuel cut), reported and gating nothing (mistake 13). flat_maxima: {role:
    value}; flat_maxima_dropped: segments dropped for holding one. closed_throttle: the PCM MAP at idle."""
    direct2_vs_summary: tuple
    u_d_fuel: Optional[float]
    maf_ratio_median: Optional[float]
    maf_ratio_n: int
    u_afr_st: Optional[float]
    u_d_air: Optional[float]
    lambda_reading: Mapping
    flat_maxima: Mapping
    flat_maxima_dropped: int
    closed_throttle: Mapping
    unsourced: tuple

    def as_json(self):
        return {
            "direct2_vs_summary": [dict(test=t, integral_g=i, modal_g=m, ratio=r, preroll_g=p, nan_intervals=k)
                                   for (t, i, m, r, p, k) in self.direct2_vs_summary],
            "u_D_fuel": self.u_d_fuel,
            "maf_vs_direct2": {"median_ratio": self.maf_ratio_median, "n": self.maf_ratio_n,
                               "u_afr_st": self.u_afr_st, "u_D": self.u_d_air},
            "lambda_reading": dict(self.lambda_reading),
            "pcm_map_closed_throttle": dict(self.closed_throttle),
            "flat_maxima": {k: float(v) for k, v in self.flat_maxima.items()},
            "flat_maxima_dropped": int(self.flat_maxima_dropped),
            "unsourced": list(self.unsourced),
        }


def _median(x):
    return float(np.median(x)) if len(x) else None


def closed_loop(seg, *, rules):
    """Whether a segment ran closed loop: every sample's lambda within closed_loop_band of 1."""
    return (abs(seg.lam_d3_min - 1.0) <= rules.closed_loop_band
            and abs(seg.lam_d3_max - 1.0) <= rules.closed_loop_band)


def saturated(seg, *, flats):
    """The roles whose flat maximum the segment reaches ({"direct2", "maf"} or a part)."""
    out = set()
    if "direct2" in flats and seg.direct2_max >= flats["direct2"]:
        out.add("direct2")
    if "maf" in flats and seg.maf_max >= flats["maf"]:
        out.add("maf")
    return frozenset(out)


def channel_checks(traces, summary, *, segs, afr_st, baro_kpa, rules, u_afr_st):
    """The channel checks of MD section 5, run before any comparison (mistake 13). traces: the tests'
    Traces; summary: read_summary's rows; segs: every test's segments (segments()); afr_st: the D3
    fuel's (decision 63, from the caller); baro_kpa: the barometric pressure the closed-throttle MAP is
    judged against (the summary's per test where it has one, else this); u_afr_st: decision 63's
    unsourced relative uncertainty of the D3 fuel's AFR_st, or None when not sized (then reported so)."""
    flats = flat_maxima(traces, roles=("direct2", "maf"), rules=rules)
    # Direct2 against the summary's modal fuel, per test.
    d2 = []
    for tr in traces:
        s = summary.get(tr.test)
        if s is None:
            raise TraceDefect(f"{tr.test}: no summary row")
        g, nan_k = _integral(tr.t_s, tr.direct2_gps, rules.integrate_from_s)
        total, _ = _integral(tr.t_s, tr.direct2_gps, -math.inf)
        d2.append((tr.test, g, float(s.modal_fuel_g), g / s.modal_fuel_g if s.modal_fuel_g > 0 else None,
                   total - g, nan_k))
    ratios = [r for (_, _, _, r, _, _) in d2 if r is not None]
    u_d_fuel = abs(_median(ratios) - 1.0) if ratios else None
    # The MAF against Direct2 x AFR_st x lambda, on closed-loop segments without a flat maximum.
    by_test = {tr.test: tr for tr in traces}
    r_inv, r_chan, open_inv, open_chan, dropped = [], [], [], [], 0
    for sg in segs:
        if saturated(sg, flats=flats):
            dropped += 1
            continue
        tr = by_test[sg.test]
        s = slice(sg.i0, sg.i1 + 1)
        fuel_air = sg.direct2_gps_mean * float(afr_st)
        if fuel_air <= 0.0:
            continue
        lam_nom = sg.lam_d3_mean
        if tr.lam_form == "inverse":
            lam_alt = float(np.mean(tr.lam_raw[s]))
        else:
            lam_alt = lam_nom
        a = sg.maf_gps_mean / (fuel_air * lam_nom)
        b = sg.maf_gps_mean / (fuel_air * lam_alt)
        if closed_loop(sg, rules=rules):
            r_inv.append(a)
            r_chan.append(b)
        else:
            open_inv.append(a)
            open_chan.append(b)
    rmed = _median(r_inv)
    unsourced = []
    if u_afr_st is None:
        unsourced.append("u_afr_st not sized: the air's u_D carries |r~ - 1| alone (decision 63)")
        u_d_air = abs(rmed - 1.0) if rmed is not None else None
    else:
        unsourced.append("u_afr_st (decision 63: the D3 fuel's AFR_st taken as the EPA Mazda batch's)")
        u_d_air = math.hypot(rmed - 1.0, float(u_afr_st)) if rmed is not None else None
    # The PCM MAP at closed throttle (idle), per test, in seconds.
    idle_maps, per_test = [], []
    for tr in traces:
        if tr.speed_kph is None:
            continue
        idle = (np.isfinite(tr.speed_kph) & (tr.speed_kph <= rules.idle_max_kph)
                & np.isfinite(tr.rpm) & (tr.rpm >= rules.idle_min_rpm) & np.isfinite(tr.map_kpa))
        keep = np.zeros(len(tr), dtype=bool)
        for a_, b_ in _runs(idle, tr.t_s, None, rules.max_gap_s):
            if tr.t_s[b_] - tr.t_s[a_] >= rules.idle_min_s:
                keep[a_:b_ + 1] = True
        if np.any(keep):
            m = float(np.median(tr.map_kpa[keep]))
            s = summary.get(tr.test)
            baro = s.baro_kpa if s is not None and s.baro_kpa is not None else float(baro_kpa)
            per_test.append({"test": tr.test, "idle_s": float(np.count_nonzero(keep) * np.median(np.diff(tr.t_s))),
                             "median_map_kpa": m, "baro_kpa": baro,
                             "below": bool(m < rules.closed_throttle_max_ratio * baro)})
            idle_maps.append(m / baro)
    closed = {"n": len(per_test), "per_test": per_test,
              "median_map_over_baro": _median(idle_maps),
              "below_baro": bool(per_test) and all(p["below"] for p in per_test)}
    return ChannelChecks(
        direct2_vs_summary=tuple(d2), u_d_fuel=u_d_fuel, maf_ratio_median=rmed, maf_ratio_n=len(r_inv),
        u_afr_st=None if u_afr_st is None else float(u_afr_st), u_d_air=u_d_air,
        lambda_reading={"nominal": "1/channel" if any(t.lam_form == "inverse" for t in traces) else "AFR/AFR_st",
                        "closed_loop_median_nominal": rmed, "closed_loop_median_if_channel": _median(r_chan),
                        "open_loop_median_nominal": _median(open_inv), "open_loop_median_if_channel": _median(open_chan),
                        "open_loop_n": len(open_inv)},
        flat_maxima=flats, flat_maxima_dropped=dropped, closed_throttle=closed, unsourced=tuple(unsourced))


# ============================================================================ the chain

def demand_torque(seg, *, car, eta):
    """The engine's torque demand on a segment, N m (MD section 5, chain item 2; PLAN.md 6.5). A stepped
    box: Dyno_TractiveForce x r_N/V / (gear ratio x final drive) / eta, the gear the car's own
    (Trans_gear_actual_CAN) and r_N/V the car record's wheel_r (C2: never D3's radius). The CVT, which has
    no gear: the ratio from engine and wheel speed, which is the power balance F v / (omega_e eta) with v
    the road speed. It holds only with the converter locked, which the segments assure on the CX-9."""
    if hasattr(car, "gears"):
        if seg.gear is None or not 1 <= seg.gear <= len(car.gears):
            raise ValueError(f"{seg.test} at {seg.t0_s}: gear {seg.gear} is not one of {car.id}'s")
        ratio = float(car.gears[seg.gear - 1]) * float(car.final_drive)
        return float(seg.force_n_mean * float(car.wheel_r) / ratio / float(eta))
    if seg.power_w_mean is None:
        raise ValueError(f"{seg.test}: a CVT's demand needs the road speed")
    return float(seg.power_w_mean / (seg.rpm_mean * RAD_PER_REV_S * float(eta)))


def bmep_bar(torque_nm, *, displacement_l):
    """BMEP of a four-stroke engine's torque: 4 pi T / V_d, in bar."""
    return 4.0 * math.pi * float(torque_nm) / (float(displacement_l) * 1e-3) / 1e5


@dataclass(frozen=True)
class EcuAlong:
    """The model ECU run along a trace (PLAN.md 6.5: "the dwell timer run on the car's own PCM MAP
    trace"): its spark and lambda at every sample, the charge temperature fed to it, the one time step it
    was stepped at, and how many of the trace's steps differ from it by more than STEP_TOL_S."""
    test: str
    spark: np.ndarray
    lam: np.ndarray
    iat_k: np.ndarray
    dt_s: float
    nonuniform_steps: int


STEP_TOL_S = 1e-6


def ecu_along(trace, *, model, t_cell_k, ect_k_if_absent):
    """model.ecu_trace along the car's own engine speed and PCM MAP, sample by sample. The model steps its
    ECU at one time step (epa_fit.RowModel.ecu_trace passes dt to every BaselineECU.step), so it is given
    the trace's own, the median of its time steps: 0.10 s in every D3 file, with no step over it
    (CATALOGUE.md:285, :408, :657); a step that differs is counted, not hidden (nonuniform_steps). The charge
    temperature is the environment's model at the cell's temperature (MD section 5, chain item 4):
    model.charge(t_cell_k, block), the block taken as the car's coolant, the nearest measured temperature
    to the block metal (declared; mistake 23: a stand-in, not the same temperature). A car with no live
    coolant (the Accord) runs at ect_k_if_absent, declared by the caller, and its charge has no block
    coupling (None, the plant's own meaning)."""
    n = len(trace)
    if trace.coolant_c is not None:
        ect = trace.coolant_c + 273.15
        iat = np.array([model.charge(float(t_cell_k), float(e)) if np.isfinite(e) else math.nan for e in ect])
    else:
        if ect_k_if_absent is None:
            raise ValueError(f"{trace.test}: no coolant channel, and no declared coolant (ect_k_if_absent)")
        ect = np.full(n, float(ect_k_if_absent))
        iat = np.full(n, model.charge(float(t_cell_k), None))
    if n < 2:
        raise TraceDefect(f"{trace.test}: fewer than two samples, no time step")
    steps = np.diff(trace.t_s)
    dt = float(np.median(steps))
    spark, lam = model.ecu_trace(trace.rpm, trace.map_kpa, iat, ect, dt)
    return EcuAlong(test=trace.test, spark=np.asarray(spark, dtype=float), lam=np.asarray(lam, dtype=float),
                    iat_k=iat, dt_s=dt, nonuniform_steps=int(np.count_nonzero(np.abs(steps - dt) > STEP_TOL_S)))


@dataclass(frozen=True)
class C3Task:
    """One segment's chain inputs (picklable, for epa_fit.ordered_map). table and fuel select the model's
    fuel exactly as an EPA row's do (epa_stats.RowInputs; MD section 3): the Mazda table's fuel, the
    model's fuel being scaled to the D3 fuel's heating value afterwards (c3_rows). lam is the model ECU's
    lambda along the car's trace, the mean over the segment (lam_min, lam_max beside it); t_cell_k and
    ect_k feed the charge."""
    engine: str
    table: str
    fuel: object
    seg: Segment
    eta: float
    demand_nm: float
    rpm: float
    ect_k: float
    t_cell_k: float
    block_k: Optional[float]
    lam: float
    lam_min: float
    lam_max: float
    d3_lhv_btu_per_lbm: float


def c3_task(seg, *, car, eta, engine_name, table, fuel, ecu, t_cell_k, ect_k_if_absent, d3_lhv_btu_per_lbm):
    """The chain's inputs for one segment (MD section 5, chain items 1-4): the demand at eta, the car's
    engine speed and coolant, the model ECU's lambda over the segment from ecu (ecu_along of its trace),
    the cell temperature from the test's metadata (decision 63) and the D3 fuel's heating value."""
    if seg.coolant_c_mean is not None:
        ect_k, block = seg.coolant_c_mean + 273.15, seg.coolant_c_mean + 273.15
    else:
        if ect_k_if_absent is None:
            raise ValueError(f"{seg.test}: no coolant channel, and no declared coolant (ect_k_if_absent)")
        ect_k, block = float(ect_k_if_absent), None
    lam = ecu.lam[seg.i0:seg.i1 + 1]
    return C3Task(engine=str(engine_name), table=str(table), fuel=fuel, seg=seg, eta=float(eta),
                  demand_nm=demand_torque(seg, car=car, eta=eta), rpm=float(seg.rpm_mean), ect_k=float(ect_k),
                  t_cell_k=float(t_cell_k), block_k=block, lam=float(np.mean(lam)), lam_min=float(np.min(lam)),
                  lam_max=float(np.max(lam)), d3_lhv_btu_per_lbm=float(d3_lhv_btu_per_lbm))


# D1's inversion (JSON conventions.statistic_details.d1): a pre-scan of 20-400 kPa every 10 kPa, the first
# bracket from 20 kPa up bisected to 1e-3 kPa, the nearer bound when there is none. epa_stats.d1_invert is
# D1's own, and moves EPA's spark linearly with the MAP; C3 sets the model ECU's spark at every trial MAP
# (MD section 5, chain item 3), so it needs the search alone, as a function of a torque curve. These are
# epa_stats.D1_SCAN_KPA and D1_BISECT_KPA, and test_d3_rows.Chain shows invert_map gives d1_invert's MAP on
# the same curve (one definition of the search, mistake 10).
MAP_SCAN_KPA = tuple(float(p) for p in range(20, 401, 10))
MAP_TOL_KPA = 1e-3


def invert_map(torque_at, target_nm):
    """(MAP, bracketed, bound_kpa, n_evaluations) at which torque_at(MAP) equals target_nm, by D1's rule:
    pre-scan MAP_SCAN_KPA, take the first pair of neighbours from 20 kPa up between which the torque
    crosses the target (a scan point that equals it is the answer), bisect it to MAP_TOL_KPA and return the
    final bracket's midpoint; with no bracket, the end of the scan at which the torque is nearer the target,
    20 kPa on a tie. A NaN torque brackets nothing."""
    ps = MAP_SCAN_KPA
    ts = [float(torque_at(p)) for p in ps]
    n = len(ts)
    d = [t - target_nm for t in ts]
    for k in range(len(ps) - 1):
        if not (math.isfinite(d[k]) and math.isfinite(d[k + 1])):
            continue
        if d[k] == 0.0:
            return ps[k], True, None, n
        if d[k + 1] == 0.0:
            return ps[k + 1], True, None, n
        if d[k] * d[k + 1] < 0.0:
            lo, hi, dlo = ps[k], ps[k + 1], d[k]
            while hi - lo > MAP_TOL_KPA:
                mid = 0.5 * (lo + hi)
                dm = float(torque_at(mid)) - target_nm
                n += 1
                if dm == 0.0:
                    return mid, True, None, n
                if (dm < 0.0) == (dlo < 0.0):
                    lo, dlo = mid, dm
                else:
                    hi = mid
            return 0.5 * (lo + hi), True, None, n
    ends = [(abs(d[0]) if math.isfinite(d[0]) else math.inf, ps[0]),
            (abs(d[-1]) if math.isfinite(d[-1]) else math.inf, ps[-1])]
    bound = min(ends)[1]
    return bound, False, bound, n


@dataclass(frozen=True)
class C3Eval:
    """The model on one segment: the inverted MAP (bracketed or at its bound), the spark the model ECU
    sets there, the charge, and the model's torque, fuel and air there; beside them the car's
    measurements and the populations' raw inputs (c3_rows classifies)."""
    test: str
    i0: int
    eta: float
    demand_nm: float
    rpm: float
    ect_k: float
    iat_k: float
    lam: float
    map_kpa: float
    bracketed: bool
    bound_kpa: Optional[float]
    spark_btdc: float
    n_cycles: int
    model_torque_nm: float
    model_fuel_gps: float
    model_air_gps: float
    d3_lhv_btu_per_lbm: float
    direct2_gps: float
    maf_gps: float
    pcm_map_kpa: float
    direct2_max: float
    maf_max: float

    def key(self):
        return (self.test, self.i0)

    def as_json(self):
        return {k: (float(v) if isinstance(v, (float, np.floating)) else v)
                for k, v in dataclasses.asdict(self).items()}


def _row_inputs(task, *, map_kpa, iat_k, spark):
    """The model's input record for a chain point, the one type every statistic feeds the model
    (epa_stats.RowInputs, WP3_INTERFACES.md 5.2.1). source_row carries the segment's first sample."""
    import epa_stats
    return epa_stats.RowInputs(engine=task.engine, table=task.table, source_row=int(task.seg.i0),
                               rpm=task.rpm, map_kpa=float(map_kpa), iat_k=float(iat_k), ect_k=task.ect_k,
                               spark_btdc=float(spark), lam=task.lam, lam_source="model_ecu_trace",
                               spark_source="model_ecu", fuel=task.fuel)


def c3_evaluate(task, *, model, dtheta):
    """The chain on one segment (MD section 5, chain item 3): the charge from model.charge at the cell's
    temperature; at each trial MAP the model ECU's spark there (model.ecu_at: no knock retard; the spark
    does not depend on the dwell) and the ECU's lambda along the car's trace (task.lam); the MAP that
    delivers the demand by invert_map; the model's fuel and air at it. A picklable kernel: the model is
    passed in, dtheta has no default (WP3_INTERFACES.md 2.2)."""
    iat_k = float(model.charge(task.t_cell_k, task.block_k))

    def out_at(p):
        spark = float(model.ecu_at(task.rpm, p, iat_k, task.ect_k).spark_btdc)
        return spark, model.cycle(_row_inputs(task, map_kpa=p, iat_k=iat_k, spark=spark), dtheta=dtheta)

    p, bracketed, bound, n = invert_map(lambda q: out_at(q)[1].torque_nm, task.demand_nm)
    spark, out = out_at(p)
    s = task.seg
    return C3Eval(test=s.test, i0=s.i0, eta=task.eta, demand_nm=task.demand_nm, rpm=task.rpm, ect_k=task.ect_k,
                  iat_k=iat_k, lam=task.lam, map_kpa=float(p), bracketed=bool(bracketed),
                  bound_kpa=None if bound is None else float(bound), spark_btdc=spark, n_cycles=int(n + 1),
                  model_torque_nm=float(out.torque_nm), model_fuel_gps=float(out.fuel_gps),
                  model_air_gps=float(out.air_gps), d3_lhv_btu_per_lbm=task.d3_lhv_btu_per_lbm,
                  direct2_gps=s.direct2_gps_mean, maf_gps=s.maf_gps_mean, pcm_map_kpa=s.pcm_map_kpa_mean,
                  direct2_max=s.direct2_max, maf_max=s.maf_max)


# ============================================================================ the rows

def u_input_c3(*, eta_lo, eta_hi, eta, radius_gap, flow_per_pct_torque):
    """C3's input uncertainty, relative, common to every segment (MD section 5, "input uncertainty that no
    calibration absorbs"): eta's span eta_lo-eta_hi around eta, uniform, on the torque demand, with the
    N/V-to-D3 radius gap, uniform, carried to the flow at the demand by the B58's flow per torque
    (JSON propagation_b58.used.flow_pct_per_pct_torque). thresholds/contract.py:343-346 computes the same;
    on the contract's terms (0.86, 0.98, 0.92, 1.6 %, 1.353) it is 5.25 % to the contract's rounding."""
    u_eta = (float(eta_hi) - float(eta_lo)) / 2.0 / float(eta) / math.sqrt(3.0)
    u_rad = float(radius_gap) / math.sqrt(3.0)
    return math.hypot(u_eta, u_rad) * float(flow_per_pct_torque)


def row10_etas(perturbations_e6):
    """E6 row 10's two efficiencies, read from the contract's own band text (JSON perturbations_E6, the
    entry with n 10: "0.86-0.98 (...)"), so the values C3 is re-run at are the contract's. The parse is
    epa_stats.row10_etas since WP3's integration (23 October 2026), the one reading C3 and the completion's
    decision-44 sensitivity (calibrate_epa.py complete, the K3 knee and the delivery at both ends) share
    (mistake 10)."""
    import epa_stats
    return epa_stats.row10_etas(perturbations_e6)


@dataclass(frozen=True)
class C3Context:
    """The contract's values C3 reads, built by the caller from the contract (validate_epa): R per row
    (JSON thresholds, row -> R; None for a descriptive row), the hot MAP floor (engines.mazda_25t.
    hot_map_floor_kpa: the car's PCM MAP decides "hot", MD section 5), the fired floor in bar BMEP (2 bar,
    thresholds/split.py FIRED_BMEP), the engine's displacement, the EPA intake-temperature range the
    charge must fall in to be covered (MD section 5: 37.3-55.0 C, JSON engines.mazda_25t.coverage.
    fired_intake_temp_c), the least segments a row decides on (3, split.MIN_CLUSTERS), u_input (relative,
    u_input_c3), the EPA map fuel's heating value (BTU/lbm, 18,447: epa_engine.json alpha_fuel) the model's
    fuel is scaled from, and descriptive_only (C4)."""
    engine: str
    R: Mapping
    hot_map_floor_kpa: float
    fired_bmep_bar: float
    displacement_l: float
    charge_range_c: tuple
    min_segments: int
    u_input: float
    epa_lhv_btu_per_lbm: float
    descriptive_only: bool


def c3_context(*, engine_name, view, displacement_l, charge_range_c, fired_bmep_bar, min_segments, u_input,
               epa_lhv_btu_per_lbm, descriptive_only):
    """A C3Context from the contract view the caller holds: its R per row (view.R, row -> (R, unit), as
    WP3_INTERFACES.md 5.1's CalibrationView keeps it) and its hot MAP floor (view.hot_map_floor_kpa); the
    rest as C3Context says. Only C3's rows are taken from R. A row the view does not hold reads None, and
    None is "descriptive" downstream, so C3 (not descriptive_only) refuses a view without an R for C3b and
    C3d, the contract's two d rows, and any C3 R not in percent: a deciding row must never become
    descriptive because a lookup fell through (mistake 19)."""
    R, bad = {}, []
    for row, _, _, _ in C3_ROWS:
        v = view.R.get(row) if hasattr(view.R, "get") else None
        r, unit = (v[0], v[1]) if isinstance(v, (tuple, list)) else (v, "%")
        R[row] = None if r is None else float(r)
        if R[row] is not None and unit != "%":
            bad.append(f"{row}'s R is in {unit!r}, not %")
    if not descriptive_only:
        bad += [f"no R for {row}" for row in ("C3b", "C3d") if R[row] is None]
    if bad:
        raise ValueError(f"{engine_name}: " + "; ".join(bad))
    lo, hi = charge_range_c
    return C3Context(engine=str(engine_name), R=R, hot_map_floor_kpa=float(view.hot_map_floor_kpa),
                     fired_bmep_bar=float(fired_bmep_bar), displacement_l=float(displacement_l),
                     charge_range_c=(float(lo), float(hi)), min_segments=int(min_segments),
                     u_input=float(u_input), epa_lhv_btu_per_lbm=float(epa_lhv_btu_per_lbm),
                     descriptive_only=bool(descriptive_only))


C3_ROWS = (("C3a", "fuel", "hot", "signed"), ("C3b", "fuel", "fired", "absolute"),
           ("C3c", "air", "hot", "signed"), ("C3d", "air", "fired", "absolute"))


def _err(ev, what, ctx):
    """The segment's relative error of the model, or None when the car's measurement cannot be compared."""
    if what == "fuel":
        if not ev.direct2_gps > 0.0:
            return None
        return ev.model_fuel_gps * (ctx.epa_lhv_btu_per_lbm / ev.d3_lhv_btu_per_lbm) / ev.direct2_gps - 1.0
    if not ev.maf_gps > 0.0:
        return None
    return ev.model_air_gps / ev.maf_gps - 1.0


def populations(ev, *, ctx, flats):
    """{name: bool} for one segment's evaluation: hot (the car's PCM MAP at or above the hot floor: data,
    not the model's MAP, MD section 5), fired (the demand at or above 2 bar BMEP), covered (the modelled
    charge inside the EPA intake range; otherwise reported apart), and whether the fuel and the air may be
    compared (no flat maximum reached in the segment, mistake 7)."""
    lo, hi = ctx.charge_range_c
    t_c = ev.iat_k - 273.15
    return {"hot": ev.pcm_map_kpa >= ctx.hot_map_floor_kpa,
            "fired": bmep_bar(ev.demand_nm, displacement_l=ctx.displacement_l) >= ctx.fired_bmep_bar,
            "covered": lo <= t_c <= hi,
            "fuel_ok": not ("direct2" in flats and ev.direct2_max >= flats["direct2"]),
            "air_ok": not ("maf" in flats and ev.maf_max >= flats["maf"])}


def _stats():
    """epa_stats, the one definition of the u-terms and the labels (mistake 10), and the names this module
    uses from it, checked so that a missing one is named rather than met mid-run."""
    import epa_stats
    need = ("StatResult", "LineStat", "UTerms", "RowInputs", "combine", "line_label", "row_label", "kappa",
            "u_stat_line")
    miss = [k for k in need if not hasattr(epa_stats, k)]
    if miss:
        raise ImportError(f"epa_stats lacks {miss} (WP3_INTERFACES.md 5.2)")
    return epa_stats


def _values(evals, half, *, row, ctx, flats, covered):
    """(keys, values in %, values at half dtheta in % or None) of one row over its population."""
    _, what, pop, form = next(r for r in C3_ROWS if r[0] == row)
    hk = {e.key(): e for e in half} if half is not None else None
    keys, vals, hv = [], [], []
    for ev in evals:
        p = populations(ev, ctx=ctx, flats=flats)
        if not p[pop] or p["covered"] != covered or not p[f"{what}_ok"]:
            continue
        e = _err(ev, what, ctx)
        if e is None:
            continue
        keys.append(ev.key())
        vals.append(100.0 * (abs(e) if form == "absolute" else e))
        if hk is not None:
            h = _err(hk[ev.key()], what, ctx)
            hv.append(100.0 * (abs(h) if form == "absolute" else h))
    return keys, vals, (hv if hk is not None else None)


def _one_row(evals, half, *, row, ctx, checks, es, unreachable_keys):
    """One C3 row as an epa_stats.StatResult (WP3_INTERFACES.md 5.2.4), pooled over the segments: E the
    mean in %, u_val from u_num (the scatter of the change at half dtheta, E6 row 8), u_input (common, in
    full) and u_D (the channel checks: Direct2 against the summary for the fuel, the MAF against Direct2
    for the air), u_stat the standard error with each segment one cluster. A d row decides with at least
    min_segments segments and certifies only with 2 u_stat <= R (MD section 3: "a pooled statistic (D1,
    E4b, E8, C3) follows the same rule with its pooled u_stat"); C3a and C3c, and every row of C4, are
    descriptive and never labelled."""
    _, what, pop, form = next(r for r in C3_ROWS if r[0] == row)
    keys, vals, hv = _values(evals, half, row=row, ctx=ctx, flats=checks.flat_maxima, covered=True)
    R = None if ctx.descriptive_only else ctx.R.get(row)
    kind = "descriptive" if R is None else "d"
    n = len(vals)
    E = float(np.mean(vals)) if n else None
    u_stat = float(es.u_stat_line(vals)) if n >= 2 else None
    u_d_rel = checks.u_d_fuel if what == "fuel" else checks.u_d_air
    unsourced = list(checks.unsourced) if what == "air" else []
    if hv is not None and n >= 2:
        dv = np.asarray(hv) - np.asarray(vals)
        u_num, u_num_sd = float(es.u_stat_line(list(dv))), float(np.std(dv, ddof=1))
    else:
        u_num, u_num_sd = None, None
    u = None
    if E is not None and u_num is not None and u_d_rel is not None and u_stat is not None:
        u = es.combine(u_num, 100.0 * ctx.u_input, 100.0 * float(u_d_rel), u_stat, tuple(unsourced),
                       u_num_sd_undivided=u_num_sd)
    no_stat, reason = False, None
    if n < ctx.min_segments:
        no_stat, reason = True, f"{n} segments, fewer than {ctx.min_segments}"
    elif u is None:
        no_stat, reason = True, "u_val incomplete: " + ", ".join(
            k for k, v in (("u_num", u_num), ("u_D", u_d_rel), ("u_stat", u_stat)) if v is None)
    label = certifies = kappa = None
    if kind == "d" and not no_stat:
        label, certifies = es.line_label(E, u.u_val, u.u_stat, R)
    line = es.LineStat(line="pooled", clusters=n, E=E, u=u, label=label, certifies=certifies)
    if kind == "d" and not no_stat:
        label = es.row_label((line,))
        kappa = float(es.kappa(E, u.u_val, R, label))
    reach = [v for k, v in zip(keys, vals) if k not in unreachable_keys]
    ok, okv, _ = _values(evals, None, row=row, ctx=ctx, flats=checks.flat_maxima, covered=False)
    return es.StatResult(
        row=row, stage="held_out", R=R, unit="%", kind=kind, E=E, lines=(line,),
        deciding=("pooled",) if n >= ctx.min_segments else (),
        certifying=("pooled",) if certifies else (),
        worst_line="pooled" if n >= ctx.min_segments else None, u=u, label=label, kappa=kappa, passes=None,
        no_statistic=bool(no_stat and kind == "d"), reason=reason,
        without={"unreachable": float(np.mean(reach)) if reach else None},
        coverage_restricted=None,
        extra={"population": f"{pop} segments, {'mean |error|' if form == 'absolute' else 'mean signed error'} "
                             f"of the model's {what}",
               "outside_charge_range": {"n": len(okv), "E": float(np.mean(okv)) if okv else None},
               "unreachable": [list(k) for k in keys if k in unreachable_keys]},
        n_rows=n, n_clusters=n)


def c3_rows(evals, *, context, checks, evals_half):
    """{C3a, C3b, C3c, C3d: epa_stats.StatResult} (MD section 5; PLAN.md 6.5): C3a and C3c the mean signed
    relative error of the model's fuel and air over the hot segments, descriptive; C3b and C3d the mean
    absolute relative error over the fired segments, at R = 16.6 %. The model's fuel is scaled by the EPA
    map fuel's heating value over the D3 fuel's (18,447/18,659) before the comparison. Segments whose
    modelled charge falls outside the EPA intake range are not covered: they are left out and reported
    apart (extra.outside_charge_range). A segment the model cannot reach is counted at the nearer bound,
    as D1's (decision 57), and each row is also reported without such segments. evals_half: the same
    segments at half the crank-angle step, for u_num (E6 row 8), or None, when no row is labelled."""
    es = _stats()
    unreachable = {e.key() for e in evals if not e.bracketed}
    return {row: _one_row(evals, evals_half, row=row, ctx=context, checks=checks, es=es,
                          unreachable_keys=unreachable) for row, _, _, _ in C3_ROWS}


def c4_accord(evals, *, context, checks, evals_half):
    """C4's Accord chain (MD section 5, C4): the same rows as C3 on the Accord's D3 segments, every one
    descriptive, since the Accord's engine is not the EPA L15B7 (CATALOGUE.md:681). The context must say
    so (descriptive_only), and is refused otherwise."""
    if not context.descriptive_only:
        raise ValueError("C4 is descriptive only (MD section 5): pass a context with descriptive_only True")
    return c3_rows(evals, context=context, checks=checks, evals_half=evals_half)


def segment_counts(evals, *, context, flats):
    """The segment counts c3.json reports (WP3_INTERFACES.md 7.9): every segment evaluated, hot, fired,
    outside the charge range, unreachable, and dropped for a flat maximum, fuel and air apart."""
    pops = [populations(e, ctx=context, flats=flats) for e in evals]
    return {"n": len(evals), "hot": sum(p["hot"] for p in pops), "fired": sum(p["fired"] for p in pops),
            "outside_charge_range": sum(not p["covered"] for p in pops),
            "unreachable": sum(not e.bracketed for e in evals),
            "fuel_dropped_flat_maximum": sum(not p["fuel_ok"] for p in pops),
            "air_dropped_flat_maximum": sum(not p["air_ok"] for p in pops)}


def fuel_scaling(evals, *, context):
    """The heating-value scaling applied to the model's fuel (MD section 5: "the scaling is reported"):
    the one factor, a float, as WP3_INTERFACES.md 7.9 writes it, when every segment's test carries one
    D3 heating value, as the CX-9's first batch does (18,447/18,659). When the summary gives several,
    {BTU/lbm: factor}, one per value: every segment was still scaled by its own test's (_err), and the
    record shows the contract's one-batch premise did not hold, rather than a crash in the one run
    (amendment C5's run-once). None with no segment."""
    by = {repr(float(v)): context.epa_lhv_btu_per_lbm / v for v in sorted({e.d3_lhv_btu_per_lbm for e in evals})}
    if not by:
        return None
    return next(iter(by.values())) if len(by) == 1 else by


def check_channels_against_car(channels, car):
    """The ways a car's CarChannels and its car record disagree, as strings: () when they agree. A gear
    code beyond the car's ratios would reach demand_torque as a gear it cannot price (mistake 18);
    run_chain refuses it before any file is read."""
    out = []
    if channels.gear_codes is not None:
        if not hasattr(car, "gears"):
            out.append(f"{channels.car} reads a gear channel; {car.id} has no gears")
        elif not set(channels.gear_codes) <= set(range(1, len(car.gears) + 1)):
            out.append(f"{channels.car} gear codes {channels.gear_codes} are not 1..{len(car.gears)} ({car.id})")
    elif hasattr(car, "gears"):
        out.append(f"{car.id} has gears; {channels.car} reads no gear channel")
    return tuple(out)


def eta_rows(evals_by_eta, *, context, checks, base):
    """E6 row 10 (MD section 4; PLAN.md 6.4): C3b and C3d re-run at each efficiency of the band, and their
    change from the nominal, {eta: {C3b: dE, C3d: dE}} in % (None where either E is missing)."""
    out = {}
    for eta, evs in sorted(evals_by_eta.items()):
        rows = c3_rows(evs, context=context, checks=checks, evals_half=None)
        out[repr(float(eta))] = {r: (None if rows[r].E is None or base[r].E is None else float(rows[r].E - base[r].E))
                                 for r in ("C3b", "C3d")}
    return out


# ============================================================================ the whole chain, for validate_epa

def run_chain(files, *, summary, channels, car, model, context, rules, channel_rules, dtheta, eta, etas_row10,
              afr_st, baro_kpa, u_afr_st, engine_name, table, fuel, ect_k_if_absent, mapper):
    """C3 (or C4's Accord chain, context.descriptive_only) from the files to the body of c3.json or
    c4_accord.json (WP3_INTERFACES.md 7.9), without its provenance, which validate_epa adds. The one entry
    point validate_epa.py run calls: its first real read of a D3 file is here (amendment C5; MD:451).

    files: ((test, path), ...), the files ARMED.json hashed; summary: read_summary's {test: SummaryRow};
    channels: CHANNELS or ACCORD_CHANNELS; car: the car record (engines.EpaCar or CvtCar); model: the frozen
    plant as epa_fit.RowModel; context: c3_context's; rules, channel_rules: CONTRACT_SEGMENTS and
    CHANNEL_RULES; dtheta: the crank-angle step (u_num reruns at half of it, E6 row 8); eta: the car's
    driveline efficiency; etas_row10: E6 row 10's two (row10_etas); afr_st: the D3 fuel's (decision 63);
    baro_kpa: the closed-throttle check's barometric pressure where the summary has none; u_afr_st:
    decision 63's unsourced term, or None; engine_name, table, fuel: the model's (the Mazda table's fuel,
    an epa_rows.TableFuel); ect_k_if_absent: the declared coolant of a car with none live (None on the
    CX-9); mapper: mapper(fn, items) -> [fn(item) ...] in order, epa_fit.ordered_map with its jobs and
    worker initializer bound, or the built-in map. Every evaluation goes through mapper; nothing here
    prints."""
    import functools
    bad = check_channels_against_car(channels, car)
    if bad:
        raise ValueError("; ".join(bad))
    traces = tuple(read_trace(p, test=t, channels=channels) for t, p in files)
    missing = [tr.test for tr in traces if tr.test not in summary]
    if missing:
        raise TraceDefect(f"no summary row for {missing}")
    seg_by = {tr.test: segments(tr, rules=rules, afr_st=afr_st) for tr in traces}
    all_segs = tuple(s for tr in traces for s in seg_by[tr.test])
    checks = channel_checks(traces, summary, segs=all_segs, afr_st=afr_st, baro_kpa=baro_kpa, rules=channel_rules,
                            u_afr_st=u_afr_st)
    ecus = {tr.test: ecu_along(tr, model=model, t_cell_k=summary[tr.test].cell_temp_c + 273.15,
                               ect_k_if_absent=ect_k_if_absent) for tr in traces}

    def tasks(at_eta):
        return [c3_task(s, car=car, eta=at_eta, engine_name=engine_name, table=table, fuel=fuel, ecu=ecus[s.test],
                        t_cell_k=summary[s.test].cell_temp_c + 273.15, ect_k_if_absent=ect_k_if_absent,
                        d3_lhv_btu_per_lbm=summary[s.test].fuel_lhv_btu_per_lbm) for s in all_segs]

    def evaluate(ts, at_dtheta):
        return list(mapper(functools.partial(c3_evaluate, model=model, dtheta=at_dtheta), ts))

    nominal = tasks(eta)
    evals = evaluate(nominal, dtheta)
    half = evaluate(nominal, 0.5 * dtheta)
    by_eta = {float(e): evaluate(tasks(e), dtheta) for e in etas_row10}
    rows = (c4_accord if context.descriptive_only else c3_rows)(evals, context=context, checks=checks,
                                                                evals_half=half)
    return {
        "files": len(traces),
        "segments": segment_counts(evals, context=context, flats=checks.flat_maxima),
        "census": {tr.test: segment_census(tr, rules=rules) for tr in traces},
        "channel_checks": checks.as_json(),
        "ecu": {tr.test: {"dt_s": ecus[tr.test].dt_s, "nonuniform_steps": ecus[tr.test].nonuniform_steps}
                for tr in traces},
        "fuel_scaling": fuel_scaling(evals, context=context),
        "rows": {r: v.as_json() for r, v in rows.items()},
        "eta": eta_rows(by_eta, context=context, checks=checks, base=rows),
        "declarations": {
            "lambda": "1/channel (MD section 5)" if channels.lam_form == "inverse" else "AFR/AFR_st",
            "block_temperature": "the car's coolant (ecu_along)" if channels.has("coolant") else
                                 "no block coupling (no live coolant)",
            "ect_k_if_absent": None if ect_k_if_absent is None else float(ect_k_if_absent),
            "u_afr_st": None if u_afr_st is None else float(u_afr_st),
            "rules_not_applied": sorted({x for tr in traces for x in rules_not_applied(tr, rules=rules)}),
            "segment_rules": dataclasses.asdict(rules), "channel_rules": dataclasses.asdict(channel_rules)},
    }
