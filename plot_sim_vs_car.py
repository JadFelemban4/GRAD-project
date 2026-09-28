"""plot_sim_vs_car.py -- the simulator against the car's own logs, as charts.

    python plot_sim_vs_car.py

Draws the comparisons between the model and the logged drives that this
repository already computes, one chart each, and prints every number it
draws. Writes into figures/sim_vs_car/:

    index.html           every chart, a cover and the numbers behind each
                         chart; open it in a browser, or print it
    page.html            the same page for the web: no document skeleton,
                         follows the viewer's light or dark theme. Published
                         privately on 28 September 2026 at
                         https://claude.ai/artifact/YWSKwwCEPAwg1oMXCVXTec
                         -- update THAT page (the Artifact tool's `url`);
                         never publish it again as a new one
    1_gear_ratios.svg ... 5_load_consistency.svg     one chart each (vector)
    1_gear_ratios.png ... 5_load_consistency.png     the same, 2000 x 1280 px
    sim_vs_car.pdf       index.html printed: A4 landscape, a chart per page
    numbers.txt          this script's printed output, so every figure on a
                         chart can be checked without reading the image

Written 28 September 2026 at Jad's request: "the charts comparing the
simulation's results with our data".

READ-ONLY, like everything in this repository. It reads data/ and logs/raw/
and writes only into figures/sim_vs_car/. It edits no model file and fits
nothing: every model value comes from the function the simulator itself calls.

WHY SVG AND NOT MATPLOTLIB. On Jad's machine Windows Application Control blocks
matplotlib's compiled `_image` module (measured 28 September 2026: "DLL load
failed while importing _image: An Application Control policy has blocked this
file"), so pyplot cannot even be imported. The charts are therefore written as
plain SVG text, which needs no compiled code, and a headless Chrome or Edge --
if one is installed -- turns them into the PNGs and the PDF. Without a
browser, the SVGs and index.html are still written; print index.html by hand.

EACH CHART SAYS WHAT KIND OF EVIDENCE IT IS, because they are not the same kind:

  INDEPENDENT CHECK   the model side came from a published source, or from a
                      model written without this data; the logs never touched it.
  FIT                 the model side was fitted to this car's logs. The chart
                      shows how the fit sits on the data; it tests nothing.
  CONSISTENCY CHECK   the comparison cancels the model it appears to test
                      (CLAUDE.md mistake 12).

NOT CHARTED, AND WHY -- say so wherever these charts are shown:

  * Turbine housing temperature, the quantity the whole project protects. The
    car has no sensor for it, so there is nothing to compare the model with.
  * Knock. AUDIT.md H5 found the model's knock integral and the car's own
    retard unrelated (CLAUDE.md, "THE KNOCK MODEL IS NOT VALIDATED"). It is a
    negative result, and no script computes it yet.
  * Oil temperature over a whole drive, modelled against measured. Not
    computed anywhere yet.
  * Air mass flow at the steady points. Identical by construction: manifold
    pressure is inverted FROM it (compare_log.py says so when it runs).
  * Coolant. The app pins the modelled block to the measured coolant (AUDIT.md
    M11), so the two agree by construction.

Everything this script PRINTS is ASCII on purpose: a non-ASCII character in a
print() has crashed a cp1252 console in this project more than once (CLAUDE.md
mistake 16, "the character is the bug"). The charts may carry any character.
"""
from __future__ import annotations

import csv
import glob
import math
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from xml.sax.saxutils import escape as _xml_escape

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

# One definition of everything, imported -- never re-typed. Where a
# computation lives inline in another script's main() and cannot be imported,
# it is repeated below and the comment names the original.
from plant import (predict, map_from_airflow, charge_temperature,  # noqa: E402
                   boost_ceiling_kpa, T_REF_CORR, P_REF_CORR)
from engine_env import BaselineECU, Vehicle  # noqa: E402
from compare_log import f as log_field, AIRFLOW_KGH_TO_GPS  # noqa: E402
from fit_envelope import envelope, BIN_KGS  # noqa: E402
from verify_docs import dwell_column  # noqa: E402
from build_dataset import fresh_readings  # noqa: E402

OUT = os.path.join(HERE, "figures", "sim_vs_car")
W, H = 1000, 640
FONT = "'Segoe UI', system-ui, -apple-system, sans-serif"

# ---- the chart palette: the dataviz reference palette, light mode ----------
# Slots 1-3 validate all-pairs for colour-vision deficiency (validate_palette.js,
# 28 Sep 2026: ALL CHECKS PASS). Only slots 1 and 2 are used.
MODEL = "#2a78d6"    # slot 1, blue: the simulator
CAR = "#eb6834"      # slot 2, orange: the car's logs
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
TAG_BG = "#f0efec"

LINES: list[str] = []


def say(s: str = "") -> None:
    """Print one line and keep it for numbers.txt. ASCII only -- see the
    module docstring."""
    if not s.isascii():
        raise ValueError(f"non-ASCII in printed output: {s!r}")
    print(s)
    LINES.append(s)


# =============================================================================
# A small SVG layer -- enough for these five charts and nothing more
# =============================================================================
def esc(s) -> str:
    return _xml_escape(str(s), {'"': "&quot;"})


class Scale:
    """Linear or log10 map from data to pixels."""

    def __init__(self, d0, d1, r0, r1, log=False):
        self.f = math.log10 if log else (lambda v: v)
        self.a0, self.a1 = self.f(d0), self.f(d1)
        self.r0, self.r1 = r0, r1

    def __call__(self, v):
        return self.r0 + (self.f(v) - self.a0) / (self.a1 - self.a0) * (self.r1 - self.r0)


# Every colour an element uses is ALSO named as a class (f-ink, s-grid, ...).
# A standalone SVG, and the PNG shot from it, ignores the classes and draws the
# light palette from the attributes. The web page styles the classes from its
# theme tokens, which beat presentation attributes, so the same charts follow
# the viewer into dark mode without a second drawing.
TOKEN = {MODEL: "model", CAR: "car", SURFACE: "surface", INK: "ink", INK2: "ink2",
         MUTED: "muted", GRID: "grid", AXIS: "axis", TAG_BG: "tag"}


def _cls(fill=None, stroke=None):
    c = [f"f-{TOKEN[fill]}"] if fill in TOKEN else []
    c += [f"s-{TOKEN[stroke]}"] if stroke in TOKEN else []
    return f' class="{" ".join(c)}"' if c else ""


class Svg:
    def __init__(self, w=W, h=H):
        self.w, self.h = w, h
        self.p = [f'<rect x="0" y="0" width="{w}" height="{h}" fill="{SURFACE}"{_cls(SURFACE)}/>']

    def text(self, x, y, s, size=12.5, color=INK, anchor="start", weight=400,
             rotate=None):
        rot = f' transform="rotate({rotate} {x:.1f} {y:.1f})"' if rotate else ""
        self.p.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}"{_cls(color)} '
                      f'text-anchor="{anchor}" font-weight="{weight}"{rot}>{esc(s)}</text>')

    def line(self, x1, y1, x2, y2, color, width=1.0, opacity=1.0):
        self.p.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                      f'stroke="{color}"{_cls(stroke=color)} stroke-width="{width}" '
                      f'stroke-opacity="{opacity}" stroke-linecap="round"/>')

    def rect(self, x, y, w, h, fill, opacity=1.0, rx=0):
        self.p.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{max(w, 0):.2f}" '
                      f'height="{max(h, 0):.2f}" rx="{rx}" fill="{fill}"{_cls(fill)} '
                      f'fill-opacity="{opacity}"/>')

    def path(self, pts, stroke="none", fill="none", width=2.0, fill_opacity=1.0, close=False):
        d = "M" + " L".join(f"{x:.1f} {y:.1f}" for x, y in pts) + (" Z" if close else "")
        self.p.append(f'<path d="{d}" stroke="{stroke}" stroke-width="{width}" fill="{fill}"'
                      f'{_cls(fill, stroke)} fill-opacity="{fill_opacity}" '
                      f'stroke-linejoin="round" stroke-linecap="round"/>')

    def dot(self, cx, cy, fill, r=5.0, title=None):
        tt = f"<title>{esc(title)}</title>" if title else ""
        self.p.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{fill}" '
                      f'stroke="{SURFACE}"{_cls(fill, SURFACE)} stroke-width="2">{tt}</circle>')

    def clip(self, cid, box):
        x0, y0, x1, y1 = box
        self.p.append(f'<clipPath id="{cid}"><rect x="{x0}" y="{y0}" width="{x1 - x0}" '
                      f'height="{y1 - y0}"/></clipPath><g clip-path="url(#{cid})">')

    def end_clip(self):
        self.p.append("</g>")

    def render(self, label) -> str:
        body = "\n".join(self.p)
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                f'width="{self.w}" height="{self.h}" role="img" aria-label="{esc(label)}" '
                f'font-family="{esc(FONT)}">\n{body}\n</svg>')


def text_width(s, size):
    """A rough width, enough to lay out a legend row or a tag."""
    return 0.56 * size * len(s)


def header(sv, title, subtitle, kind, note):
    sv.text(56, 42, title, size=20, weight=600)
    sv.text(56, 70, subtitle, size=13.5, color=INK2)
    tw = text_width(kind, 11.5) * 1.18 + 18
    sv.rect(56, 86, tw, 23, TAG_BG, rx=4)
    sv.text(56 + 9, 102, kind, size=11.5, weight=700)
    sv.text(56 + tw + 10, 102, note, size=12.5, color=INK2)


def footer(sv, foot, width=140):
    """The caveat travels with the chart. Returns the y of its first line."""
    lines = textwrap.wrap(foot, width)
    y0 = sv.h - 18 - 16 * (len(lines) - 1)
    for i, ln in enumerate(lines):
        sv.text(56, y0 + 16 * i, ln, size=11.3, color=MUTED)
    return y0 - 12


def legend_row(sv, x, y, items):
    """items: (kind, colour, label, opacity) laid out left to right."""
    for kind, color, label, op in items:
        if kind == "line":
            sv.line(x, y - 4, x + 22, y - 4, color, 2.0, op)
        elif kind == "patch":
            sv.rect(x, y - 10, 22, 12, color, op, rx=2)
        elif kind == "dot":
            sv.dot(x + 11, y - 4, color, r=4.5 if op >= 0.99 else 4.0)
        sv.text(x + 30, y, label, size=12.5, color=INK2)
        x += 30 + text_width(label, 12.5) + 28


def y_axis(sv, ys, box, ticks, label=None, labels=True):
    x0, y0, x1, y1 = box
    for v, lab in ticks:
        y = ys(v)
        sv.line(x0, y, x1, y, GRID, 1.0)
        if labels:
            sv.text(x0 - 9, y + 4, lab, size=11.5, color=INK2, anchor="end")
    if label:
        sv.text(x0 - 58, (y0 + y1) / 2, label, size=12.5, color=INK2, anchor="middle",
                rotate=-90)


def x_axis(sv, xs, box, ticks, label=None):
    x0, y0, x1, y1 = box
    sv.line(x0, y1, x1, y1, AXIS, 1.0)
    for v, lab in ticks:
        x = xs(v)
        sv.line(x, y1, x, y1 + 5, AXIS, 1.0)
        sv.text(x, y1 + 20, lab, size=11.5, color=INK2, anchor="middle")
    if label:
        sv.text((x0 + x1) / 2, y1 + 42, label, size=12.5, color=INK2, anchor="middle")


def nice_ticks(lo, hi, n=6):
    span = hi - lo
    mag = 10 ** math.floor(math.log10(span / n))
    for m in (1, 2, 2.5, 5, 10):
        step = m * mag
        if span / step <= n:
            break
    v = math.ceil(lo / step) * step
    out = []
    while v <= hi + 1e-9:
        out.append(round(v, 10))
        v += step
    return out


def fmt(v, nd=0):
    return f"{v:,.{nd}f}"


def step_points(edges, heights, ys, xs, base):
    pts = [(xs(edges[0]), ys(base))]
    for i, h in enumerate(heights):
        pts += [(xs(edges[i]), ys(h)), (xs(edges[i + 1]), ys(h))]
    pts.append((xs(edges[-1]), ys(base)))
    return pts


# =============================================================================
# 1. THE GEARBOX -- independent: Toyota's published ratios against the car
# =============================================================================
MOVING_KMH = 20.0      # below this the torque converter slips and launches blur
NEAR = 0.04            # the tolerance engine_env.Vehicle's own comment quotes


def chart_gears(S):
    ratios = np.array(Vehicle.gears, dtype=float) * Vehicle.final_drive
    mv = S[(S.v_kmh > MOVING_KMH) & (S.rpm > 0)]
    wheel_rpm = (mv.v_kmh.to_numpy() / 3.6) / (2.0 * np.pi * Vehicle.wheel_r) * 60.0
    overall = mv.rpm.to_numpy() / wheel_rpm
    overall = overall[np.isfinite(overall) & (overall > 0)]
    idx = np.argmin(np.abs(np.log(overall[:, None] / ratios[None, :])), axis=1)
    within = np.abs(overall / ratios[idx] - 1.0) <= NEAR
    share = float(within.mean())
    n_drives = int(mv.source.nunique())
    per_gear = [int(((idx == g) & within).sum()) for g in range(len(ratios))]

    say("1. GEARBOX  (engine_env.Vehicle: ZF 8HP51 ratios x final drive)")
    say(f"   moving samples (v > {MOVING_KMH:.0f} km/h): {len(overall)}  from {n_drives} drives")
    say(f"   within {NEAR:.0%} of a published overall ratio: {int(within.sum())}"
        f"  = {100 * share:.1f} %")
    say(f"   wheel radius used: {Vehicle.wheel_r} m (the model's constant)")
    for g, r in enumerate(ratios):
        say(f"   gear {g + 1}: overall ratio {r:6.3f}   samples within {NEAR:.0%}: {per_gear[g]}")
    say()

    sv = Svg()
    header(sv, "The gearbox: the ratios the car actually ran, against the eight Toyota publishes",
           f"{len(overall):,} moving samples (above {MOVING_KMH:.0f} km/h) from {n_drives} drives  ·  "
           f"{100 * share:.1f} % lie within ±{NEAR:.0%} of a published ratio",
           "INDEPENDENT CHECK",
           "the ratios and the final drive are Toyota's published figures; nothing was fitted to these logs")
    ftop = footer(sv, (
        "Overall ratio = engine rpm ÷ wheel rpm, the wheel's rpm taken from road speed and the model's wheel "
        f"radius ({Vehicle.wheel_r} m, whose source is not recorded). The radius shifts all eight peaks together, "
        "so the SPACING of the peaks is the independent part. Samples between the peaks are gear changes and "
        "torque-converter slip, which the model does not simulate: it assumes the converter locked. The car's "
        "own 'Actual gear' channel stops at 6, so it is not used (CLAUDE.md mistake 18). "
        "Data: data/master_samples.csv."))
    box = (86, 170, W - 36, ftop - 58)
    legend_row(sv, 56, 146, [("patch", CAR, "the car: the ratio it ran, per sample", 1.0),
                             ("line", MODEL, "published ratio × final drive (the model)", 1.0),
                             ("patch", MODEL, f"±{NEAR:.0%}", 0.2)])
    bins = np.geomspace(1.5, 22.0, 260)
    counts, _ = np.histogram(overall, bins)
    top = float(counts.max())
    xs = Scale(1.6, 21.0, box[0], box[2], log=True)
    ys = Scale(0.8, top * 6, box[3], box[1], log=True)
    y_axis(sv, ys, box, [(v, fmt(v)) for v in (1, 10, 100, 1000, 10000, 100000) if v <= top * 6],
           "samples per bin (log scale)")
    sv.clip("clip-gears", box)
    for r in ratios:
        sv.rect(xs(r * (1 - NEAR)), box[1], xs(r * (1 + NEAR)) - xs(r * (1 - NEAR)),
                box[3] - box[1], MODEL, 0.10)
    sv.path(step_points(bins, np.maximum(counts, 0.8), ys, xs, 0.8), fill=CAR, close=True)
    for g, r in enumerate(ratios):
        sv.line(xs(r), box[1], xs(r), box[3], MODEL, 1.6)
    sv.end_clip()
    for g, r in enumerate(ratios):
        sv.text(xs(r), ys(top * 2.4), f"{g + 1}", size=13, weight=600, color=INK2, anchor="middle")
    sv.text(xs(ratios[-1]) - 16, ys(top * 2.4), "gear", size=11.5, color=MUTED, anchor="end")
    x_axis(sv, xs, box, [(r, f"{r:.2f}") for r in ratios],
           "overall ratio = engine rpm ÷ wheel rpm   (log scale)")

    table = (["gear", "published overall ratio", f"samples within ±{NEAR:.0%}"],
             [[f"{g + 1}", f"{r:.3f}", fmt(per_gear[g])] for g, r in enumerate(ratios)])
    cover = ("The gearbox: the ratios the car ran, against the eight Toyota publishes",
             "INDEPENDENT CHECK", f"{100 * share:.1f} % of moving samples within ±{NEAR:.0%} of a published ratio")
    return "1_gear_ratios", sv.render("Histogram of the overall gear ratio the car ran, with the eight "
                                       "published ratios marked"), table, cover


# =============================================================================
# 2. BOOST PRESSURE UNDER BOOST -- independent: the charge-temperature model
# =============================================================================
# The same computation as verify_docs.py's CHARGE TEMPERATURE block, repeated
# here because that block is inline in its main(). The gate is not arbitrary:
# 15 psi gauge on the logged side is about 201.5 kPa absolute, so a 200 kPa
# gate on the model side selects the same operating region by construction.
GATE_KPA = 200.0
BOOST_MIN_PSI = 15.0
AMBIENT_PSI_DEFAULT = 14.23
PSI_TO_KPA = 6.894757


def logged_boost_kpa(sources):
    out = []
    for path in sorted(glob.glob(os.path.join(HERE, "logs", "raw", "*.csv"))):
        if os.path.basename(path) not in sources:
            continue
        d = pd.read_csv(path)
        bc = [c for c in d.columns if c.lower() == "boost pressure"]
        ac = [c for c in d.columns if "ambient" in c.lower() and "press" in c.lower()]
        if not bc:
            continue
        b = pd.to_numeric(d[bc[0]], errors="coerce").dropna()
        a = (pd.to_numeric(d[ac[0]], errors="coerce").median() if ac
             else AMBIENT_PSI_DEFAULT)
        out += list((b[b > BOOST_MIN_PSI] + a) * PSI_TO_KPA)
    return np.array(out, dtype=float)


def chart_boost(S):
    hi = S[(S.map_kpa > GATE_KPA) & (~S.maf_pinned.astype(bool))]
    car = logged_boost_kpa(set(hi.source))
    model = hi.map_kpa.to_numpy(dtype=float)
    # The same samples, inverted with the pre-throttle SENSOR as the charge
    # temperature -- what the dataset did before 10 September (mistake 13).
    sensor = np.array([map_from_airflow(g, r, t + 273.15) for g, r, t in
                       zip(hi.air_gps, hi.rpm, hi.iat_pre_c)], dtype=float)
    sensor = sensor[np.isfinite(sensor)]
    m_car, m_model, m_sensor = (float(np.median(x)) for x in (car, model, sensor))
    gap = 100.0 * (m_model - m_car) / m_car
    gap_sensor = 100.0 * (m_sensor - m_car) / m_car
    sensor_c = float(np.median(hi.iat_pre_c.dropna()))

    say("2. BOOST PRESSURE UNDER BOOST  (same computation as verify_docs.py, CHARGE TEMPERATURE)")
    say(f"   model samples above {GATE_KPA:.0f} kPa, MAF not pinned: {len(model)}"
        f"   median {m_model:.1f} kPa")
    say(f"   car rows, Boost pressure above {BOOST_MIN_PSI:.0f} psi gauge: {len(car)}"
        f"   median {m_car:.1f} kPa")
    say(f"   gap, model vs car: {gap:+.1f} %")
    say(f"   same samples with the pre-throttle sensor as charge temperature"
        f" (median {sensor_c:.0f} C): median {m_sensor:.1f} kPa, gap {gap_sensor:+.1f} %"
        f"  ({len(sensor)} samples with a sensor reading)")
    say()

    sv = Svg()
    header(sv, "Boost pressure under boost: the model's value against the car's own boost channel",
           f"above {GATE_KPA:.0f} kPa  ·  model {len(model):,} samples, car {len(car):,} logged rows  ·  "
           f"medians {m_model:.0f} and {m_car:.0f} kPa  ·  gap {gap:+.1f} %",
           "INDEPENDENT CHECK",
           "plant.charge_temperature() was written without this data and has no parameter fitted to it")
    ftop = footer(sv, (
        "The two sides are different samples, not pairs: the logger reads one channel per row, so air mass and "
        "boost are never read at the same instant, and two populations over the same region are compared by their "
        "medians. Model: manifold pressure inverted from the measured air mass, with the modelled charge "
        f"temperature. Grey: the same samples inverted with the pre-throttle sensor, "
        "which is a compressor outlet, not the charge -- the dataset's error until 10 September (CLAUDE.md "
        "mistake 13). Samples at the air-mass sensor's ceiling are excluded (mistake 7). "
        "Data: data/master_samples.csv, logs/raw/*.csv."))
    box = (86, 170, W - 36, ftop - 58)
    legend_row(sv, 56, 146, [("patch", CAR, "the car: its Boost pressure channel", 0.45),
                             ("line", MODEL, "the model: inverted with charge_temperature()", 1.0),
                             ("line", MUTED, "the old error: inverted with the sensor", 1.0)])
    lo = GATE_KPA - 10.0
    hi_edge = float(max(np.percentile(x, 99.5) for x in (car, model, sensor))) + 8.0
    edges = np.arange(lo, hi_edge + 4.0, 4.0)
    shares = {k: np.histogram(x, edges)[0] * 100.0 / len(x)
              for k, x in (("car", car), ("model", model), ("sensor", sensor))}
    ymax = float(max(v.max() for v in shares.values())) * 1.32
    xs = Scale(lo, edges[-1], box[0], box[2])
    ys = Scale(0.0, ymax, box[3], box[1])
    y_axis(sv, ys, box, [(v, f"{v:g}") for v in nice_ticks(0, ymax, 5)],
           "share of each side, % per 4 kPa")
    sv.path(step_points(edges, shares["car"], ys, xs, 0.0), fill=CAR, fill_opacity=0.22, close=True)
    sv.path(step_points(edges, shares["car"], ys, xs, 0.0), stroke=CAR, width=2.0)
    sv.path(step_points(edges, shares["sensor"], ys, xs, 0.0), stroke=MUTED, width=1.5)
    sv.path(step_points(edges, shares["model"], ys, xs, 0.0), stroke=MODEL, width=2.0)
    y_lab = ys(ymax * 0.86)
    for x, col, l1, l2, side in ((m_car, CAR, "car median", f"{m_car:.0f} kPa", "end"),
                                 (m_model, MODEL, "model median", f"{m_model:.0f} kPa", "start"),
                                 (m_sensor, MUTED, "with the sensor",
                                  f"{m_sensor:.0f} kPa, {gap_sensor:+.0f} %", "start")):
        sv.line(xs(x), box[3], xs(x), y_lab + 6, col, 1.3)
        if side == "start" and xs(x) > box[2] - 150:
            side = "end"
        dx = 6 if side == "start" else -6
        sv.text(xs(x) + dx, y_lab - 14, l1, size=11.5, color=INK2, anchor=side)
        sv.text(xs(x) + dx, y_lab + 2, l2, size=11.5, color=INK2, anchor=side, weight=600)
    x_axis(sv, xs, box, [(v, f"{v:g}") for v in nice_ticks(lo, edges[-1], 8)],
           "pressure, kPa absolute")

    table = (["side", "samples", "median, kPa", "gap to the car"],
             [["the car: Boost pressure channel", fmt(len(car)), f"{m_car:.1f}", "--"],
              ["the model: charge_temperature()", fmt(len(model)), f"{m_model:.1f}", f"{gap:+.1f} %"],
              ["the old error: the pre-throttle sensor", fmt(len(sensor)), f"{m_sensor:.1f}",
               f"{gap_sensor:+.1f} %"]])
    cover = ("Boost pressure under boost: the model against the car's own boost channel",
             "INDEPENDENT CHECK", f"medians {gap:+.1f} % apart; with the old sensor reading, {gap_sensor:+.0f} %")
    return "2_boost_pressure", sv.render("Distributions of boost pressure: the car's channel against the "
                                          "model's inversion"), table, cover


# =============================================================================
# 3. THE COMPRESSOR ENVELOPE -- a fit, shown on today's data
# =============================================================================
def chart_envelope(S):
    rows = envelope(S)                       # fit_envelope.py, unchanged
    c = np.array([r[0] for r in rows])
    p95 = np.array([r[1] for r in rows])
    n_rows = np.array([r[2] for r in rows])
    fresh = np.array([r[3] for r in rows])
    use = S[(S.stable == 1) & (S.maf_pinned == 0)]
    use = use[np.isfinite(use.corr_flow) & np.isfinite(use.press_ratio)
              & (use.corr_flow > 0.01)]
    mmax = float(max(c.max(), use.corr_flow.max())) + 0.02
    m = np.linspace(0.0, mmax, 300)

    def ceiling(x):
        # The simulator's own ceiling, called as the simulator calls it. At the
        # reference inlet state, corrected flow equals mass flow in kg/s.
        return boost_ceiling_kpa(x * 1000.0, T_REF_CORR, P_REF_CORR) / P_REF_CORR

    pr_model = np.array([ceiling(x) for x in m])
    model_at_bins = np.array([ceiling(x) for x in c])
    rms = float(np.sqrt(np.mean((model_at_bins - p95) ** 2)))

    say("3. COMPRESSOR ENVELOPE  (fit_envelope.envelope; plant.boost_ceiling_kpa)")
    say(f"   stable samples, MAF not pinned: {len(use)}")
    say(f"   {'flow kg/s':>10}{'car PR p95':>12}{'model PR':>10}{'rows':>7}{'readings':>10}")
    for ci, pi, mi, ni, fi in zip(c, p95, model_at_bins, n_rows, fresh):
        say(f"   {ci:>10.3f}{pi:>12.3f}{mi:>10.3f}{int(ni):>7d}{int(fi):>10d}")
    say(f"   RMS, model ceiling vs today's p95 bins: {rms:.3f} (pressure ratio)")
    say()

    sv = Svg()
    header(sv, "Boost against air flow: the simulator's ceiling on the car's measured envelope",
           f"{len(use):,} steady samples  ·  95th percentile per {BIN_KGS:.2f} kg/s bin  ·  "
           f"RMS gap {rms:.3f} in pressure ratio",
           "FIT",
           "the ceiling (plant.boost_ceiling_kpa) was fitted to this car's envelope; the chart shows the fit and tests nothing")
    ftop = footer(sv, (
        "Grey: every steady sample with the air-mass sensor below its ceiling; darker means more samples. Orange: "
        "the 95th percentile of pressure ratio in each bin (fit_envelope.py). Read the counts on the top bins: "
        "the rows are forward-filled, and the number beside each dot is how many INDEPENDENT readings it rests on "
        "(AUDIT.md H4). Beyond the last bin nothing is measured, because the air-mass sensor saturates "
        "(CLAUDE.md mistake 7). Data: data/master_samples.csv."))
    box = (86, 170, W - 36, ftop - 58)
    legend_row(sv, 56, 146, [("patch", MUTED, "the car: steady samples", 0.45),
                             ("dot", CAR, "the car: 95th percentile per bin", 1.0),
                             ("line", MODEL, "the model: boost ceiling", 1.0)])
    pr_top = float(max(p95.max(), pr_model.max())) + 0.3
    xs = Scale(0.0, mmax, box[0], box[2])
    ys = Scale(0.9, pr_top, box[3], box[1])
    y_axis(sv, ys, box, [(v, f"{v:.1f}") for v in nice_ticks(0.9, pr_top, 6)],
           "compressor pressure ratio")
    nx, ny = 150, 90
    hist, ex, ey = np.histogram2d(use.corr_flow, use.press_ratio, bins=[nx, ny],
                                  range=[[0.0, mmax], [0.9, pr_top]])
    cmax = math.log1p(float(hist.max()))
    sv.clip("clip-env", box)
    for i, j in zip(*np.nonzero(hist)):
        a = 0.07 + 0.55 * math.log1p(float(hist[i, j])) / cmax
        sv.rect(xs(ex[i]), ys(ey[j + 1]), xs(ex[i + 1]) - xs(ex[i]) + 0.3,
                ys(ey[j]) - ys(ey[j + 1]) + 0.3, MUTED, round(a, 3))
    sv.path([(xs(x), ys(y)) for x, y in zip(m, pr_model)], stroke=MODEL, width=2.0)
    sv.end_clip()
    for ci, pi, mi, ni, fi in zip(c, p95, model_at_bins, n_rows, fresh):
        sv.dot(xs(ci), ys(pi), CAR, r=5.5,
               title=f"{ci:.3f} kg/s: car p95 {pi:.3f}, model {mi:.3f}; {int(ni)} rows, "
                     f"{int(fi)} independent readings")
    for i in np.argsort(c)[-4:]:
        sv.text(xs(c[i]), ys(p95[i]) - 13, f"{int(fresh[i])} readings", size=11, color=INK2,
                anchor="middle")
    x_axis(sv, xs, box, [(v, f"{v:.2f}") for v in nice_ticks(0.0, mmax, 8)],
           "corrected air mass flow, kg/s")

    table = (["flow bin, kg/s", "car p95 PR", "model PR", "rows", "independent readings"],
             [[f"{ci:.3f}", f"{pi:.3f}", f"{mi:.3f}", fmt(int(ni)), fmt(int(fi))]
              for ci, pi, mi, ni, fi in zip(c, p95, model_at_bins, n_rows, fresh)])
    cover = ("Boost against air flow: the simulator's ceiling on the car's envelope", "FIT",
             f"RMS {rms:.3f} in pressure ratio; the top bins rest on a handful of readings each")
    return "3_compressor_envelope", sv.render("Pressure ratio against corrected air flow: the car's "
                                               "samples, their envelope and the model's ceiling"), table, cover


# =============================================================================
# 4. ENRICHMENT -- a fit: base_lambda v4 on the samples it was fitted to
# =============================================================================
BANDS = ((1000, 3500), (3500, 4500), (4500, 7000))   # the rpm bands of base_lambda's table
DWELL = ((0.0, 4.0), (4.0, 8.0), (8.0, math.inf))     # its dwell columns, seconds


def chart_enrichment(S):
    ecu = BaselineECU()
    gate = float(ecu.ENR_LOAD)
    S2 = dwell_column(S, thr=gate)
    h = S2[(S2.map_kpa > gate) & S2.lam.between(0.5, 1.3)].copy()
    h["lam_model"] = [ecu.base_lambda(r, p, d) for r, p, d in
                      zip(h.rpm, h.map_kpa, h.dwell)]
    cells = []
    for lo, hi in BANDS:
        b = h[(h.rpm > lo) & (h.rpm <= hi)]
        for d0, d1 in DWELL:
            x = b[(b.dwell >= d0) & (b.dwell < d1)]
            if len(x) == 0:
                cells.append(dict(lo=lo, hi=hi, d0=d0, d1=d1, n=0))
                continue
            cells.append(dict(lo=lo, hi=hi, d0=d0, d1=d1, n=len(x),
                              fresh=int(fresh_readings(x, "lam")),
                              med=float(x.lam.median()), q1=float(x.lam.quantile(0.25)),
                              q3=float(x.lam.quantile(0.75)),
                              mod=float(x.lam_model.median())))
    full = [cl for cl in cells if cl["n"]]
    wc = max(full, key=lambda cl: abs(cl["med"] - cl["mod"]))
    worst = abs(wc["med"] - wc["mod"])

    def dwell_label(cl):
        return (f"{cl['d0']:.0f}-{cl['d1']:.0f} s" if math.isfinite(cl["d1"])
                else f"{cl['d0']:.0f}+ s")

    say("4. ENRICHMENT  (engine_env.BaselineECU.base_lambda, v4)")
    say(f"   samples above the {gate:.0f} kPa gate with lambda 0.5-1.3: {len(h)}")
    say(f"   {'cell':<27}{'rows':>6}{'readings':>10}{'car med':>9}{'car IQR':>15}{'model':>8}")
    for cl in cells:
        if not cl["n"]:
            say(f"   cell {cl['lo']}-{cl['hi']} rpm {dwell_label(cl):<8}  no samples")
            continue
        say(f"   cell {cl['lo']}-{cl['hi']} rpm {dwell_label(cl):<8}{cl['n']:>6d}{cl['fresh']:>10d}"
            f"{cl['med']:>9.2f}   {cl['q1']:.2f}-{cl['q3']:.2f}{cl['mod']:>8.2f}")
    say(f"   largest |car median - model median| over the cells: {worst:.3f}"
        f"  (cell {wc['lo']}-{wc['hi']} rpm {dwell_label(wc)})")
    say()

    sv = Svg()
    header(sv, "Enrichment: the mixture the car ran under boost, against the model's map",
           f"{len(h):,} samples above the {gate:.0f} kPa gate  ·  nine cells by engine speed and seconds "
           f"of dwell  ·  largest gap {worst:.3f} in λ",
           "FIT",
           "base_lambda v4 was fitted to these same samples (engine_env.BaselineECU); it tests nothing")
    ftop = footer(sv, (
        "λ = 1 is the chemically exact mixture; below 1 is rich, fuel spent to cool the exhaust. Dwell = seconds "
        "of unbroken running above the gate, from the timestamps (verify_docs.dwell_column). Dots are medians "
        "over the cell; the orange bar is the middle half of the car's samples; the count under each cell is "
        "how many independent lambda readings it rests on (AUDIT.md H4). The map's dwell constants were "
        "fitted before AUDIT.md H3 corrected the dwell axis, and the worst cell shows it: "
        f"{wc['lo']}–{wc['hi']} rpm at {dwell_label(wc)}, car {wc['med']:.2f} against model {wc['mod']:.2f}. "
        "The locked scenario's climb runs in the first panel's band, where the map never enriches. "
        "Data: data/master_samples.csv."))
    box = (86, 188, W - 36, ftop - 58)
    legend_row(sv, 56, 146, [("dot", CAR, "the car: median, and its middle half", 1.0),
                             ("dot", MODEL, "the model: base_lambda on the same samples", 1.0)])
    gapx = 26
    pw = (box[2] - box[0] - 2 * gapx) / 3.0
    ys = Scale(0.72, 1.03, box[3], box[1])
    yt = [0.75, 0.8, 0.85, 0.9, 0.95, 1.0]
    for k, (lo, hi) in enumerate(BANDS):
        px0 = box[0] + k * (pw + gapx)
        pbox = (px0, box[1], px0 + pw, box[3])
        y_axis(sv, ys, pbox, [(v, f"{v:.2f}") for v in yt],
               "λ, air-fuel ratio relative to exact" if k == 0 else None, labels=(k == 0))
        sv.line(pbox[0], ys(1.0), pbox[2], ys(1.0), AXIS, 1.2)
        sv.line(pbox[0], pbox[3], pbox[2], pbox[3], AXIS, 1.0)
        sv.text((pbox[0] + pbox[2]) / 2, box[1] - 12, f"{lo}–{hi} rpm", size=13, weight=600,
                anchor="middle")
        mine = [cl for cl in cells if cl["lo"] == lo]
        for j, cl in enumerate(mine):
            cx = pbox[0] + pw * (j + 0.5) / 3.0
            sv.text(cx, pbox[3] + 20, ["0–4 s", "4–8 s", "8 s and more"][j], size=11.5,
                    color=INK2, anchor="middle")
            if not cl["n"]:
                continue
            sv.line(cx - 11, ys(cl["q1"]), cx - 11, ys(cl["q3"]), CAR, 2.2, 0.55)
            # Hover titles start with a word and end with one: verify_docs.py reads
            # any line that STARTS with an rpm band and ENDS with a number as a row
            # of base_lambda's sample-count table (its ENRICHMENT v4 pattern).
            sv.dot(cx - 11, ys(cl["med"]), CAR, r=5.5,
                   title=f"car median {cl['med']:.2f} at {lo}-{hi} rpm, {dwell_label(cl)}")
            sv.dot(cx + 11, ys(cl["mod"]), MODEL, r=5.5,
                   title=f"model {cl['mod']:.2f} at {lo}-{hi} rpm, {dwell_label(cl)}")
            sv.text(cx, pbox[3] - 9, f"{cl['fresh']} readings", size=10.5, color=MUTED,
                    anchor="middle")
    sv.text(box[0] + 4, ys(1.0) - 6, "λ = 1", size=11, color=MUTED)
    sv.text((box[0] + box[2]) / 2, box[3] + 42, "dwell: seconds of unbroken running above the gate",
            size=12.5, color=INK2, anchor="middle")

    table = (["cell", "rows", "independent readings", "car median", "car middle half", "model"],
             [[f"λ cell: {cl['lo']}–{cl['hi']} rpm, {dwell_label(cl)}", fmt(cl["n"]),
               fmt(cl.get("fresh", 0)),
               f"{cl['med']:.2f}" if cl["n"] else "--",
               f"{cl['q1']:.2f} to {cl['q3']:.2f}" if cl["n"] else "--",
               f"{cl['mod']:.2f}" if cl["n"] else "--"] for cl in cells])
    cover = ("Enrichment: the mixture under boost, against the model's map", "FIT",
             f"largest cell gap {worst:.3f} in λ")
    return "4_enrichment", sv.render("Lambda under boost in nine cells: the car's medians against the "
                                      "model's map"), table, cover


# =============================================================================
# 5. LOAD AT THE STEADY POINTS -- a consistency check, not a model test
# =============================================================================
DIN_REF = 100.0 * 273.15 / 101.3     # compare_log.py's derived constant: three defined numbers


def chart_load(points_csv):
    # compare_log.py's own loop, field for field, through its own field reader.
    with open(points_csv, newline="") as fh:
        rows = list(csv.DictReader(fh))
    pairs = []
    for r in rows:
        rpm = log_field(r, "Engine speed")
        ect_c = log_field(r, "Coolant temperature")
        amb_c = log_field(r, "Ambient temperature")
        lam = log_field(r, "Lambda actual value", 1.0)
        spark = log_field(r, "Actual ignition angle", 20.0)
        air_raw = log_field(r, "Air mass flow")
        load_meas = log_field(r, "Relative air filling")
        if not math.isfinite(rpm) or rpm < 500:
            continue
        air = air_raw * AIRFLOW_KGH_TO_GPS
        ect_k = (ect_c if math.isfinite(ect_c) else 90.0) + 273.15
        t_amb_k = (amb_c if math.isfinite(amb_c) else 25.0) + 273.15
        iat_k = charge_temperature(t_amb_k, ect_k)
        if not math.isfinite(lam) or lam <= 0:
            lam = 1.0
        map_kpa = map_from_airflow(air, rpm, iat_k)
        if not math.isfinite(map_kpa) or map_kpa < 15:
            continue
        out = predict(rpm=rpm, map_kpa=map_kpa, iat_k=iat_k, ect_k=ect_k,
                      spark_btdc=spark, lam=lam)
        load_model = 100.0 * out["eta_v"] * (1.0 - out["f_res"]) * map_kpa / 100.0
        if math.isfinite(load_meas) and load_meas > 0 and math.isfinite(load_model):
            pairs.append((load_meas, load_model, iat_k, map_kpa, rpm))
    meas, mod, t_in, maps, rpms = (np.array(v) for v in zip(*pairs))
    k_fit = float(np.sum(meas * mod) / np.sum(mod * mod))
    mape_fit = float(np.mean(100.0 * np.abs(k_fit * mod - meas) / meas))
    k_pred = DIN_REF / t_in
    mape_pred = float(np.mean(100.0 * np.abs(k_pred * mod - meas) / meas))
    y = k_pred * mod

    say("5. LOAD AT THE STEADY POINTS  (compare_log.py, default mode)")
    say(f"   points scored: {len(meas)}   manifold pressure {maps.min():.0f}-{maps.max():.0f} kPa")
    say(f"   derived k = {DIN_REF:.1f} / T_charge, mean {float(np.mean(k_pred)):.3f}"
        f"   residual MAPE {mape_pred:.1f} %   (0 free parameters)")
    say(f"   fitted k = {k_fit:.3f}   residual MAPE {mape_fit:.1f} %   (1 free parameter)")
    say("   CONSISTENCY CHECK: eta_v, residual gas and T cancel out (CLAUDE.md mistake 12)")
    say()

    sv = Svg()
    header(sv, "Engine load at the steady points: the model against the ECU's own load channel",
           f"{len(meas)} points, {maps.min():.0f}–{maps.max():.0f} kPa manifold pressure  ·  mean error "
           f"{mape_pred:.1f} % with nothing fitted  ·  {mape_fit:.1f} % with one fitted constant",
           "CONSISTENCY CHECK",
           "not a test of the breathing model: η_v, residual gas and intake temperature cancel out")
    ftop = footer(sv, (
        "Horizontal: the ECU's 'Relative air filling'. Vertical: the model's load from the measured air mass, "
        f"times k = {DIN_REF:.1f} / T_charge -- the DIN reference state, 1013 mbar and 0 °C -- with nothing fitted. "
        "Both sides are built from the same air-mass reading, so the agreement shows what the ECU channel means "
        "and that the model has the right displacement (a wrong engine misses badly); it cannot show that the "
        "model breathes like the car (CLAUDE.md mistake 12). 'Steady' means steady in road and engine speed only "
        "(AUDIT.md M3). Data: data/master_points.csv."))
    side = (ftop - 58) - 150
    x0 = (W - side) / 2 + 30
    box = (x0, 150, x0 + side, 150 + side)
    lim = float(max(meas.max(), y.max())) * 1.08
    xs = Scale(0.0, lim, box[0], box[2])
    ys = Scale(0.0, lim, box[3], box[1])
    ticks = nice_ticks(0.0, lim, 6)
    y_axis(sv, ys, box, [(v, f"{v:g}") for v in ticks], "the model: load × k, %")
    for v in ticks:
        sv.line(xs(v), box[1], xs(v), box[3], GRID, 1.0)
    sv.line(xs(0), ys(0), xs(lim), ys(lim), AXIS, 1.3)
    sv.text(xs(lim * 0.12) + 8, ys(lim * 0.12) + 4, "model = car", size=11, color=MUTED)
    # No '%' after a load value: verify_docs.py's RETIRED pattern for the old
    # load residual has no leading boundary, so a live model value of 52.3 per
    # cent, written with its sign, reads as a retired figure (found 28 Sep 2026).
    # The unit is in the axis titles.
    for a, b, p, r in zip(meas, y, maps, rpms):
        sv.dot(xs(a), ys(b), MODEL, r=5.5,
               title=f"{r:.0f} rpm, {p:.0f} kPa: ECU {a:.1f}, model {b:.1f} (relative air filling)")
    x_axis(sv, xs, box, [(v, f"{v:g}") for v in ticks], "the car: ECU relative air filling, %")

    order = np.argsort(meas)
    table = (["rpm", "manifold kPa", "ECU load, %", "model load × k, %", "error, %"],
             [[f"{rpms[i]:.0f}", f"{maps[i]:.0f}", f"{meas[i]:.1f}", f"{y[i]:.1f}",
               f"{100.0 * (y[i] - meas[i]) / meas[i]:+.1f}"] for i in order])
    cover = ("Engine load at the steady points: the model against the ECU's load channel",
             "CONSISTENCY CHECK", f"{mape_pred:.1f} % with nothing fitted -- and it cannot test the breathing model")
    return "5_load_consistency", sv.render("Scatter of the model's load against the ECU's relative air "
                                            "filling at the steady points"), table, cover


# =============================================================================
# The page, and the browser that prints it
# =============================================================================
NOT_CHARTED = [
    "Turbine housing temperature, the quantity the project protects: the car has no sensor for it.",
    "Knock: the model's knock integral and the car's own retard are unrelated (AUDIT.md H5). "
    "A negative result, and no script charts it yet.",
    "Oil temperature over a whole drive, modelled against measured: not computed yet.",
    "Air mass flow and coolant: equal by construction, so a chart of them would prove nothing.",
]

TITLE = "Simulator Against the Supra"
ANCHOR = {"1_gear_ratios": "gears", "2_boost_pressure": "boost",
          "3_compressor_envelope": "envelope", "4_enrichment": "enrichment",
          "5_load_consistency": "load"}
KIND_CLASS = {"INDEPENDENT CHECK": "independent", "FIT": "fit",
              "CONSISTENCY CHECK": "consistency"}
KIND_MEANS = [
    ("INDEPENDENT CHECK", "the model side came from a published source, or from a model written "
                          "without this data; the logs never touched it"),
    ("FIT", "the model side was fitted to this car's logs; the chart shows the fit and tests nothing"),
    ("CONSISTENCY CHECK", "the comparison cancels the model it appears to test (CLAUDE.md mistake 12)"),
]

# Page tokens. LIGHT is the chart palette above; DARK is the dataviz reference
# palette's dark column -- the same hues stepped for a dark surface, not an
# inversion of the light one.
LIGHT = dict(page="#f9f9f7", surface=SURFACE, ink=INK, ink2=INK2, muted=MUTED, grid=GRID,
             axis=AXIS, tag=TAG_BG, model=MODEL, car=CAR, rule="rgba(11,11,11,0.10)")
DARK = dict(page="#0d0d0d", surface="#1a1a19", ink="#ffffff", ink2="#c3c2b7", muted="#898781",
            grid="#2c2c2a", axis="#383835", tag="#2c2c2a", model="#3987e5", car="#d95926",
            rule="rgba(255,255,255,0.10)")
FONTS_URL = ("https://fonts.googleapis.com/css2?family=Barlow:wght@400;500;600"
             "&family=Barlow+Semi+Condensed:wght@600;700&family=IBM+Plex+Mono:wght@400;500"
             "&display=swap")


def tokens(d):
    return " ".join(f"--{k}: {v};" for k, v in d.items())


def page_css():
    marks = "\n".join(f".chart .f-{t} {{ fill: var(--{t}); }} .chart .s-{t} {{ stroke: var(--{t}); }}"
                      for t in TOKEN.values())
    return f"""
:root {{ {tokens(LIGHT)}
  --font-head: 'Barlow Semi Condensed', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --font-body: 'Barlow', 'Segoe UI', system-ui, -apple-system, sans-serif;
  --font-data: 'IBM Plex Mono', ui-monospace, 'Cascadia Mono', Consolas, monospace; }}
@media (prefers-color-scheme: dark) {{
  :root:not([data-theme="light"]) {{ color-scheme: dark; {tokens(DARK)} }}
}}
:root[data-theme="dark"] {{ color-scheme: dark; {tokens(DARK)} }}
@media print {{
  :root, :root:not([data-theme="light"]), :root[data-theme="dark"] {{ color-scheme: light; {tokens(LIGHT)} }}
}}
@page {{ size: A4 landscape; margin: 9mm; }}
* {{ box-sizing: border-box; }}
body {{ margin: 0; background: var(--page); color: var(--ink);
       font: 400 16px/1.55 var(--font-body); padding-inline: 16px; padding-block: 28px 56px; }}
.wrap {{ max-width: 1040px; margin: 0 auto; display: grid; gap: 36px;
         grid-template-columns: minmax(0, 1fr); }}
section {{ display: grid; gap: 18px; grid-template-columns: minmax(0, 1fr); }}
/* A grid item will not shrink below its content by default, so one 720px
   chart would widen the whole page on a phone; the scroll box must take it. */
.wrap > *, section > *, .numbers > div > * {{ min-width: 0; }}
h1, h2 {{ font-family: var(--font-head); font-weight: 700; text-wrap: balance; margin: 0; }}
h1 {{ font-size: clamp(32px, 5.2vw, 46px); line-height: 1.04; }}
h2 {{ font-size: 23px; line-height: 1.2; }}
p {{ margin: 0; max-width: 68ch; color: var(--ink2); }}
.lede {{ font-size: 18px; color: var(--ink); }}
.meta {{ font-family: var(--font-data); font-size: 12.5px; color: var(--muted); letter-spacing: .02em; }}
header {{ display: grid; gap: 12px; }}
.ladder {{ list-style: none; margin: 0; padding: 0; border-top: 1px solid var(--grid); }}
.ladder li {{ display: grid; grid-template-columns: 12rem minmax(0, 1fr); gap: 4px 18px;
             align-items: baseline; padding: 12px 0; border-bottom: 1px solid var(--grid); }}
.ladder a {{ color: var(--ink); font-weight: 600; text-decoration: none; }}
.ladder a:hover, .ladder a:focus-visible {{ text-decoration: underline; }}
.ladder .result {{ grid-column: 2; font-family: var(--font-data); font-size: 13px; color: var(--ink2); }}
.kind {{ justify-self: start; font-family: var(--font-head); font-size: 12.5px; font-weight: 700;
        letter-spacing: .06em; text-transform: uppercase; border-radius: 4px; padding: 1px 8px;
        border: 1.5px solid var(--ink); color: var(--ink); white-space: nowrap; }}
.kind.independent {{ background: var(--ink); color: var(--page); }}
.kind.consistency {{ border-style: dashed; border-color: var(--ink2); color: var(--ink2); }}
.key {{ margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; font-size: 14.5px; color: var(--ink2); }}
.key li {{ display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; }}
figure.chart {{ margin: 0; background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; }}
.scroll {{ overflow-x: auto; }}
.chart svg {{ display: block; width: 100%; height: auto; min-width: 720px; font-family: var(--font-body); }}
{marks}
ul.missing {{ margin: 0; padding-left: 20px; display: grid; gap: 6px; color: var(--ink2); max-width: 75ch; }}
.numbers > div {{ display: grid; gap: 6px; }}
.numbers h3 {{ font: 600 15.5px/1.3 var(--font-body); margin: 0; }}
table {{ border-collapse: collapse; font-size: 13px; }}
th, td {{ padding: 4px 12px; border-bottom: 1px solid var(--grid); text-align: right; white-space: nowrap; }}
td {{ font-family: var(--font-data); font-variant-numeric: tabular-nums; }}
th {{ color: var(--ink2); font-weight: 600; }}
th:first-child, td:first-child {{ text-align: left; font-family: var(--font-body); }}
code {{ font-family: var(--font-data); font-size: .92em; }}
footer p {{ font-size: 13.5px; color: var(--muted); }}
a:focus-visible {{ outline: 2px solid var(--model); outline-offset: 2px; }}
@media (max-width: 640px) {{
  .ladder li {{ grid-template-columns: minmax(0, 1fr); }}
  .ladder .result {{ grid-column: 1; }}
}}
@media print {{
  body {{ padding: 0; background: var(--surface); font-size: 13.5px; }}
  h1 {{ font-size: 32px; }}
  .lede {{ font-size: 15.5px; }}
  section {{ gap: 12px; }}
  .ladder li {{ padding: 7px 0; }}
  .wrap {{ display: block; }}
  section {{ break-after: page; }}
  section.numbers {{ break-after: auto; }}
  figure.chart {{ border: 0; }}
  .chart svg {{ min-width: 0; }}
}}
"""


def html_table(head, rows):
    out = ["<table>", "<tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr>"]
    for r in rows:
        out.append("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in r) + "</tr>")
    out.append("</table>")
    return "\n".join(out)


def build_page(charts, meta, web):
    """web=False: a whole document, for opening locally and for printing the PDF.
    web=True: the published page -- no doctype, html, head or body of its own
    (the artifact host wraps it), plus the Google Fonts link it may load."""
    ladder = "\n".join(
        f'<li><span class="kind {KIND_CLASS[k]}">{esc(k.lower())}</span>'
        f'<a href="#{ANCHOR[name]}">{esc(t)}</a><span class="result">{esc(n)}</span></li>'
        for name, _, _, (t, k, n) in charts)
    key = "\n".join(f'<li><span class="kind {KIND_CLASS[k]}">{esc(k.lower())}</span>'
                    f'<span>{esc(m)}</span></li>' for k, m in KIND_MEANS)
    missing = "\n".join(f"<li>{esc(m)}</li>" for m in NOT_CHARTED)
    lede = ("The engine simulator set beside the logged drives of the team's test car, a Toyota GR "
            "Supra. Five comparisons, one chart each, ordered from the strongest kind of evidence to "
            "the weakest.")
    head = [f"<title>{TITLE}</title>"]
    if web:
        head.append(f'<link rel="stylesheet" href="{esc(FONTS_URL)}">')
    head.append(f"<style>{page_css()}</style>")
    body = [
        '<div class="wrap">',
        '<section class="cover">',
        "<header>",
        '<p class="meta">BSc graduation project, University of Jeddah · phase B, the simulator '
        "against the car</p>",
        "<h1>The simulator against the Supra's logs</h1>",
        f'<p class="lede">{esc(lede)}</p>',
        f'<p class="meta">{esc(meta)}</p>',
        "</header>",
        f'<ol class="ladder">{ladder}</ol>',
        f'<ul class="key">{key}</ul>',
        "<h2>Not charted, and why</h2>",
        f'<ul class="missing">{missing}</ul>',
        "</section>",
    ]
    for name, svg, _, _ in charts:
        body += [f'<section id="{ANCHOR[name]}">', '<figure class="chart"><div class="scroll">', svg,
                 "</div></figure>", "</section>"]
    body += ['<section class="numbers">', "<h2>The numbers behind each chart</h2>"]
    for (name, _, (thead, rows), (title, _, _)) in charts:
        body += ["<div>", f"<h3>{esc(name[0])}. {esc(title)}</h3>",
                 f'<div class="scroll">{html_table(thead, rows)}</div>', "</div>"]
    body += ["</section>",
             "<footer><p>Built by <code>plot_sim_vs_car.py</code> from <code>data/master_samples.csv</code>, "
             "<code>data/master_points.csv</code> and <code>logs/raw/</code>. Every value on this page is "
             "printed, with its definition, in <code>figures/sim_vs_car/numbers.txt</code>. Read-only: "
             "nothing in this project writes to the car.</p></footer>",
             "</div>"]
    if web:
        return "\n".join(head + body) + "\n"
    return "\n".join(["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
                      '<meta name="viewport" content="width=device-width, initial-scale=1">', *head,
                      "</head>", "<body>", *body, "</body>", "</html>"]) + "\n"


def find_browser():
    cands = [os.environ.get("CHROME"),
             r"C:\Program Files\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
             r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
             r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
             shutil.which("chrome"), shutil.which("google-chrome"),
             shutil.which("chromium"), shutil.which("msedge")]
    for c in cands:
        if c and os.path.exists(c):
            return c
    return None


def run_browser(browser, args):
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as prof:
        subprocess.run([browser, "--headless=new", "--disable-gpu", "--no-first-run",
                        "--no-default-browser-check", f"--user-data-dir={prof}", *args],
                       capture_output=True, timeout=180, check=False)


def png_size(path):
    with open(path, "rb") as fh:
        head = fh.read(24)
    if head[:8] != b"\x89PNG\r\n\x1a\n":
        return None
    return int.from_bytes(head[16:20], "big"), int.from_bytes(head[20:24], "big")


def main():
    os.makedirs(OUT, exist_ok=True)
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
    say("THE SIMULATOR AGAINST THE CAR'S LOGS  (plot_sim_vs_car.py)")
    say(f"data/master_samples.csv: {len(S)} rows from {S.source.nunique()} drives")
    say()

    charts = [chart_gears(S), chart_boost(S), chart_envelope(S), chart_enrichment(S),
              chart_load(os.path.join(HERE, "data", "master_points.csv"))]

    for name, svg, _, _ in charts:
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n")
    n_points = len(pd.read_csv(os.path.join(HERE, "data", "master_points.csv")))
    meta = (f"{len(S):,} logged samples · {S.source.nunique()} drives · {n_points} steady points · "
            "gearbox ZF 8HP51 · engine B58, 3.0 L")
    page = os.path.join(OUT, "index.html")
    with open(page, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(charts, meta, web=False))
    with open(os.path.join(OUT, "page.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(charts, meta, web=True))

    say("WRITTEN")
    say("   figures/sim_vs_car/index.html       (every chart, a cover and the tables)")
    say("   figures/sim_vs_car/page.html        (the same, as the published web page)")
    for name, *_ in charts:
        say(f"   figures/sim_vs_car/{name}.svg")

    browser = find_browser()
    if browser is None:
        say("   NO CHROME OR EDGE FOUND: no PNG and no PDF. Open index.html and print it.")
    else:
        for name, *_ in charts:
            png = os.path.join(OUT, name + ".png")
            if os.path.exists(png):
                os.remove(png)
            run_browser(browser, ["--hide-scrollbars", f"--window-size={W},{H}",
                                  "--force-device-scale-factor=2", f"--screenshot={png}",
                                  Path(OUT, name + ".svg").as_uri()])
            size = png_size(png) if os.path.exists(png) else None
            say(f"   figures/sim_vs_car/{name}.png   "
                + (f"{size[0]} x {size[1]} px" if size else "NOT WRITTEN"))
        pdf = os.path.join(OUT, "sim_vs_car.pdf")
        if os.path.exists(pdf):
            os.remove(pdf)
        run_browser(browser, ["--no-pdf-header-footer", "--print-to-pdf-no-header",
                              f"--print-to-pdf={pdf}", Path(page).as_uri()])
        say("   figures/sim_vs_car/sim_vs_car.pdf   "
            + ("printed from index.html" if os.path.exists(pdf) else "NOT WRITTEN"))
    say("   figures/sim_vs_car/numbers.txt      (this output)")
    with open(os.path.join(OUT, "numbers.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    main()
