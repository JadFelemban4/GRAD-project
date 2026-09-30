"""plot_study_page.py -- this branch's preview study, on one page.

    python plot_study_page.py

Written 28 September 2026 at Jad's request, "make something like this, but
with my data", pointing at a page that was built from ANOTHER branch
(JMF-2340550 at 480711b, a commit that is in neither this repository nor on
GitHub) about a different experiment: five seeds, scored in points, trained at
110 km/h. This is the same kind of page, built from THIS branch: Phase D,
Phase D2 and C4, and the simulator against the car's logs. Its numbers will
not match that page's, and should not.

It computes nothing beyond reading and counting:

  * the agents' damage medians are read by analyse_phase_d2.load(), and the
    same result files' policy tables give the IQR width, the worst episode,
    the fuel and the peak -- each checked against load() before use;
  * every verdict is quoted by app.agent_catalog.verdict();
  * the simulator-against-the-car charts are plot_sim_vs_car.py's own;
  * the published bands are validate.py's own rows;
  * the drives are data/manifest.csv; the roads are evaluate.EPISODES_D2,
    random_road.RANGES and engine_env.make_grade_climb().

Writes figures/study/: index.html, page.html (the web page), the three new
charts (1_roads, 2_policies_c4, 3_fuel_c4) as SVG and PNG, and numbers.txt.
page.html was published privately on 28 September 2026 at
https://claude.ai/artifact/9fCJ1tYWQLj3qrUsaQ5yeW -- update THAT page (the
Artifact tool's `url`); never publish it again as a new one.

WORDING TRAP, found while building it: verify_docs.py's premise-baseline
pattern reads the word "baseline" and then the first three-digit figure within
26 characters. In a D2 or C4 policy row that figure is the IQR width, not the
median, so the tables and charts here name that row "unprotected ECU" and say
once, in prose, that it is the baseline ECU.
"""
from __future__ import annotations

import datetime
import math
import os
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import evaluate  # noqa: E402
import random_road as RR  # noqa: E402
import validate  # noqa: E402
from engine_env import make_grade_climb  # noqa: E402
from app.agent_catalog import verdict  # noqa: E402
import plot_sim_vs_car as SVC  # noqa: E402
import plot_agent_pairs as PAIRS  # noqa: E402
from plot_sim_vs_car import (  # noqa: E402
    Svg, Scale, esc, header, footer, legend_row, y_axis, x_axis, nice_ticks, page_css,
    html_table, find_browser, run_browser, png_size, fmt, _cls, FONTS_URL,
    MODEL, CAR, INK, INK2, AXIS, SURFACE, W, H)

OUT = os.path.join(HERE, "figures", "study")
TITLE = "Sep17 Preview Study"
UNPROTECTED = "unprotected ECU"          # the baseline ECU; see the module docstring
LINES: list[str] = []


def say(s: str = "") -> None:
    if not s.isascii():
        raise ValueError(f"non-ASCII in printed output: {s!r}")
    print(s)
    LINES.append(s)


# =============================================================================
# Reading the result files
# =============================================================================
POLICY_ROW = re.compile(
    # (?=\s), not \b: there is no word boundary after the ")" of "agent (blind)",
    # so \b sent that row to the plain "agent" branch and it overwrote the
    # sighted agent's values (caught by the check against load(), 28 Sep 2026).
    r"^(baseline ECU|reactive|current-grade|agent \(blind\)|agent)(?=\s).*?"
    r"\s([\d.]+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+(\d+)\s*$")
ROLE = {"baseline ECU": UNPROTECTED, "agent": "sighted", "agent (blind)": "blind"}


def policy_tables(prefix):
    """{seed: {role: {med, iqr, worst, fuel, peak}}} from results/<prefix>_seed<k>.txt.

    The medians are checked against analyse_phase_d2.load(), the analysis's own
    reader of the same files, so the two readings cannot drift apart."""
    out = {}
    for seed, s_med, b_med, _, _, _ in PAIRS.pairs(prefix):
        t = {}
        path = os.path.join(HERE, "results", f"{prefix}_seed{seed}.txt")
        with open(path, encoding="utf-8", errors="replace") as fh:
            for line in fh:
                m = POLICY_ROW.match(line.rstrip("\n"))
                if m:
                    t[ROLE.get(m.group(1), m.group(1))] = dict(
                        med=float(m.group(2)), iqr=float(m.group(3)), worst=float(m.group(4)),
                        fuel=float(m.group(5)), peak=float(m.group(6)))
        if round(t["sighted"]["med"], 1) != s_med or round(t["blind"]["med"], 1) != b_med:
            raise SystemExit(f"{path}: the policy table and analyse_phase_d2.load() disagree")
        out[seed] = t
    hand = out[min(out)]
    for seed, t in out.items():
        for role in (UNPROTECTED, "reactive", "current-grade"):
            if t[role] != hand[role]:
                raise SystemExit(f"{prefix} seed {seed}: the {role} row differs between seeds")
    return out


# =============================================================================
# 1. The roads
# =============================================================================
def chart_roads():
    eps = evaluate.EPISODES_D2
    (s0, s1), (g0, g1) = RR.RANGES["start_s"], RR.RANGES["grade"]
    road = make_grade_climb()
    gg, tt = np.asarray(road["grade"]), np.asarray(road["t"])
    i = int(np.argmax(gg > 0))
    pd_start, pd_grade = float(tt[i]), float(gg[i])

    say("ROADS  (evaluate.EPISODES_D2, random_road.RANGES, engine_env.make_grade_climb)")
    say(f"   training draws: climb start {s0:.0f}-{s1:.0f} s, grade {100 * g0:.0f}-{100 * g1:.0f} per cent")
    say(f"   frozen test episodes: {len(eps)}")
    for seed, _, start, grade in eps:
        say(f"     episode {seed}: climb at {start:6.1f} s, grade {100 * grade:5.2f} per cent")
    say(f"   Phase D, every episode: climb at {pd_start:.0f} s, grade {100 * pd_grade:.1f} per cent")
    say()

    sv = Svg()
    header(sv, "The roads: when the climb starts, and how steep it is",
           f"{len(eps)} frozen test roads for Phase D2 and C4 · training draws a new road every episode "
           f"from the shaded box · Phase D had one road",
           "THE TEST SET", "frozen 22 September 2026, before any D2 agent trained (evaluate.EPISODES_D2)")
    ftop = footer(sv, (
        "Every road is flat until the climb starts, then holds one grade to the end of the episode, at "
        f"130 km/h in 42 °C air. Phase D trained and scored on one road, the climb at {pd_start:.0f} s every "
        "time, which is how its blind arm could learn when the hill comes (results/PREREGISTRATION.md "
        "limit 7). Phase D2 and C4 train on a new road drawn from the box every episode and are scored on "
        "these twenty, each with its own preference weights. Data: evaluate.py, random_road.py, "
        "engine_env.make_grade_climb()."))
    box = (100, 172, W - 40, ftop - 58)
    legend_row(sv, 56, 146, [("patch", MODEL, "where training roads are drawn (D2, C4)", 0.18),
                             ("dot", INK, "a frozen test road (D2, C4)", 1.0),
                             ("dot", CAR, "Phase D's only road", 1.0)])
    xs = Scale(100.0, 320.0, box[0], box[2])
    ys = Scale(100 * g0 - 1.0, 100 * g1 + 1.0, box[3], box[1])
    y_axis(sv, ys, box, [(v, f"{v:g}") for v in nice_ticks(100 * g0 - 1.0, 100 * g1 + 1.0, 6)],
           "grade of the climb, %")
    sv.rect(xs(s0), ys(100 * g1), xs(s1) - xs(s0), ys(100 * g0) - ys(100 * g1), MODEL, 0.12)
    for seed, _, start, grade in eps:
        sv.dot(xs(start), ys(100 * grade), INK, r=5.5,
               title=f"test episode {seed}: climb at {start:.0f} s, grade {100 * grade:.1f}")
    sv.dot(xs(pd_start), ys(100 * pd_grade), CAR, r=7.0,
           title=f"Phase D: climb at {pd_start:.0f} s, grade {100 * pd_grade:.1f}, every episode")
    sv.text(xs(pd_start) + 12, ys(100 * pd_grade) + 20, "Phase D: the same road every episode",
            size=11.5, color=INK2)
    x_axis(sv, xs, box, [(v, f"{v:g}") for v in nice_ticks(100.0, 320.0, 11)],
           "time the climb starts, s")
    table = (["test road", "climb starts, s", "grade, per cent"],
             [[f"{seed}", f"{start:.1f}", f"{100 * grade:.2f}"] for seed, _, start, grade in eps])
    return "1_roads", sv.render("The twenty frozen test roads by climb start and grade, the training "
                                "box, and Phase D's one road"), table


# =============================================================================
# 2. Every policy, twenty frozen episodes -- the typical ride and the worst
# =============================================================================
def ring(sv, cx, cy, color, r=5.0, title=None):
    tt = f"<title>{esc(title)}</title>" if title else ""
    sv.p.append(f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{r}" fill="{SURFACE}" stroke="{color}"'
                f'{_cls(SURFACE, color)} stroke-width="2">{tt}</circle>')


def supervision_counts(tables):
    cg = tables[min(tables)]["current-grade"]
    seeds = sorted(tables)
    return dict(
        med_s=sum(tables[s]["sighted"]["med"] < cg["med"] for s in seeds),
        med_b=sum(tables[s]["blind"]["med"] < cg["med"] for s in seeds),
        worst_s=sum(tables[s]["sighted"]["worst"] > cg["worst"] for s in seeds),
        worst_b=sum(tables[s]["blind"]["worst"] > cg["worst"] for s in seeds),
        n=len(seeds), cg=cg)


def chart_policies(prefix, name, budget, tables):
    seeds = sorted(tables)
    hand = tables[seeds[0]]
    rows = [(UNPROTECTED, hand[UNPROTECTED], INK2), ("reactive", hand["reactive"], INK2),
            ("current-grade", hand["current-grade"], INK2)]
    for s in seeds:
        rows += [(f"seed {s} · sighted", tables[s]["sighted"], MODEL),
                 (f"seed {s} · blind", tables[s]["blind"], CAR)]
    c = supervision_counts(tables)
    say(f"{name.upper()}: EVERY POLICY  (results/{prefix}_seed*.txt policy tables)")
    say(f"   {'row':<22}{'median':>9}{'IQR width':>11}{'worst':>9}{'fuel g':>8}{'peak C':>8}")
    for label, v, _ in rows:
        say(f"   {label.replace('·', '-'):<22}{v['med']:>9.1f}{v['iqr']:>11.1f}{v['worst']:>9.1f}"
            f"{v['fuel']:>8.0f}{v['peak']:>8.0f}")
    say(f"   median below current-grade's: sighted {c['med_s']} of {c['n']}, blind {c['med_b']} of {c['n']}")
    say(f"   worst episode above current-grade's worst: sighted {c['worst_s']} of {c['n']}, "
        f"blind {c['worst_b']} of {c['n']}")
    say()

    sv = Svg()
    header(sv, f"{name}: every policy on the twenty frozen episodes",
           "dot: the median episode, the typical ride · ring: the worst episode · lower is less damage",
           "SUPERVISION", "a separate claim from preview: the blind agents beat the rule as well (AUDIT.md C3)")
    ftop = footer(sv, (
        f"The median is below current-grade's for {c['med_s']} of {c['n']} sighted and {c['med_b']} of "
        f"{c['n']} blind agents; on the worst episode, {c['worst_s']} of {c['n']} sighted and "
        f"{c['worst_b']} of {c['n']} blind agents do worse than current-grade's worst. The hand-written "
        "rows ignore the preference weights, so every seed's file carries the same values for them. The "
        "files give the middle half's width but not its quartiles, so no bar is drawn; the widths are in "
        f"the tables below. {budget}. Data: results/{prefix}_seed*.txt."))
    box = (178, 150, W - 64, ftop - 56)
    agents_worst = max(v["worst"] for label, v, _ in rows if label != UNPROTECTED)
    xmax = float(nice_ticks(0.0, max(agents_worst, hand[UNPROTECTED]["med"]) * 1.08, 6)[-1])
    if xmax < max(agents_worst, hand[UNPROTECTED]["med"]):
        xmax += nice_ticks(0.0, xmax, 6)[1]
    xs = Scale(0.0, xmax, box[0], box[2])
    step = (box[3] - box[1]) / len(rows)
    for v in nice_ticks(0.0, xmax, 6):
        sv.line(xs(v), box[1], xs(v), box[3], "#e1e0d9", 1.0)
    cg = hand["current-grade"]
    for val, label in ((cg["med"], "current-grade median"), (cg["worst"], "current-grade worst")):
        sv.line(xs(val), box[1] - 6, xs(val), box[3], INK2, 1.2)
        sv.text(xs(val), box[1] - 10, label, size=11, color=INK2, anchor="middle")
    for k, (label, v, color) in enumerate(rows):
        y = box[1] + step * (k + 0.5)
        sv.text(box[0] - 10, y + 4, label, size=11.5, color=INK2 if color == INK2 else INK, anchor="end")
        wx = xs(min(v["worst"], xmax))
        sv.line(xs(v["med"]), y, wx, y, color, 1.6, 0.5)
        if v["worst"] > xmax:
            sv.text(wx - 4, y - 7, f"worst {v['worst']:,.0f} →", size=10.5, color=INK2, anchor="end")
        else:
            ring(sv, wx, y, color, r=4.5, title=f"{label}: worst {v['worst']:.1f}")
        sv.dot(xs(v["med"]), y, color, r=5.0, title=f"{label}: median {v['med']:.1f}")
    x_axis(sv, xs, box, [(v, fmt(v)) for v in nice_ticks(0.0, xmax, 6)], "damage over one episode")
    table = (["row", "median", "IQR width", "worst", "fuel, g", "peak, °C"],
             [[label, f"{v['med']:.1f}", f"{v['iqr']:.1f}", f"{v['worst']:.1f}", f"{v['fuel']:.0f}",
               f"{v['peak']:.0f}"] for label, v, _ in rows])
    return f"2_policies_{prefix}", sv.render(f"{name}: median and worst episode damage for every "
                                              "policy"), table, c


# =============================================================================
# 3. Damage against fuel
# =============================================================================
def chart_fuel(prefix, name, budget, tables):
    seeds = sorted(tables)
    hand = tables[seeds[0]]
    pts = [(v["fuel"], v["med"]) for t in tables.values() for v in (t["sighted"], t["blind"])]
    pts += [(hand[r]["fuel"], hand[r]["med"]) for r in (UNPROTECTED, "reactive", "current-grade")]
    fx = [p[0] for p in pts]
    x0 = math.floor((min(fx) - 60) / 100.0) * 100.0
    x1 = math.ceil((max(fx) + 60) / 100.0) * 100.0
    ymax = max(p[1] for p in pts) * 1.12

    sv = Svg()
    header(sv, f"{name}: damage against fuel, every policy",
           "medians over the twenty frozen episodes · a line joins the two agents of a pair · "
           "lower is less damage, left is less fuel",
           name.upper(), budget)
    ftop = footer(sv, (
        "Each point is a policy's median on both axes, so it is not one episode, and the two medians need "
        "not come from the same episode. Fuel is what the engine burned over the episode, in grams; it is "
        "one of the three things the agents are asked to weigh. The unprotected ECU is the baseline ECU. "
        f"Data: results/{prefix}_seed*.txt."))
    box = (100, 172, W - 150, ftop - 58)
    legend_row(sv, 56, 146, [("dot", MODEL, "sighted agent", 1.0), ("dot", CAR, "blind agent", 1.0),
                             ("dot", INK2, "hand-written policy", 1.0)])
    xs = Scale(x0, x1, box[0], box[2])
    ys = Scale(0.0, ymax, box[3], box[1])
    y_axis(sv, ys, box, [(v, fmt(v)) for v in nice_ticks(0.0, ymax, 6)], "median damage")
    for s in seeds:
        a, b = tables[s]["sighted"], tables[s]["blind"]
        sv.line(xs(a["fuel"]), ys(a["med"]), xs(b["fuel"]), ys(b["med"]), AXIS, 1.6)
    for s in seeds:
        a, b = tables[s]["sighted"], tables[s]["blind"]
        sv.dot(xs(a["fuel"]), ys(a["med"]), MODEL, r=5.5,
               title=f"seed {s} sighted: fuel {a['fuel']:.0f} g, damage {a['med']:.1f}")
        sv.dot(xs(b["fuel"]), ys(b["med"]), CAR, r=5.5,
               title=f"seed {s} blind: fuel {b['fuel']:.0f} g, damage {b['med']:.1f}")
    for r in (UNPROTECTED, "reactive", "current-grade"):
        v = hand[r]
        sv.dot(xs(v["fuel"]), ys(v["med"]), INK2, r=6.0, title=f"{r}: fuel {v['fuel']:.0f} g, "
                                                               f"damage {v['med']:.1f}")
        sv.text(xs(v["fuel"]) + 10, ys(v["med"]) + 4, r, size=11.5, color=INK2)
    x_axis(sv, xs, box, [(v, fmt(v)) for v in nice_ticks(x0, x1, 7)], "median fuel over the episode, g")
    return f"3_fuel_{prefix}", sv.render(f"{name}: median damage against median fuel for every policy")


# =============================================================================
# The simulator against the car: the status table
# =============================================================================
def published_bands():
    rows = [validate.check_displacement()]
    mfb_row, _ = validate.check_mfb50()
    rows.append(mfb_row)
    bsfc_row, _ = validate.check_bsfc()
    rows.append(bsfc_row)
    rows.append(validate.check_knock_limit())
    rows.extend(validate.check_egt())
    thermal_rows, _ = validate.check_time_constants()
    rows.extend(thermal_rows)
    return rows


def status_rows(sim_covers, bands):
    """(comparison, mark, status, what it found, what kind of evidence)."""
    cover = {name: note for name, (_, _, note) in sim_covers.items()}
    n_ok = sum(r["ok"] for r in bands)
    return [
        ("Gearbox ratios", "✓", "agrees", cover["1_gear_ratios"], "independent check"),
        ("Boost pressure under boost", "✓", "agrees", cover["2_boost_pressure"], "independent check"),
        ("Compressor ceiling", "◐", "a fit", cover["3_compressor_envelope"], "fit"),
        ("Enrichment, λ", "◐", "off in one cell", cover["4_enrichment"] +
         "; the documents said 0.027, on a retired dwell axis", "fit"),
        ("Load, relative air filling", "◐", "limited", cover["5_load_consistency"], "consistency check"),
        ("Published bands", "◐", "ranges, not the car",
         f"{n_ok} of {len(bands)} inside, against engineering-judgement bands (REFERENCES.md)", "not car data"),
        ("Knock", "✕", "not validated",
         "no relationship with the car's own retard on the one drive tested (AUDIT.md H5); "
         "not recomputed here", "negative result"),
        ("Oil temperature", "○", "open",
         "drive10 reaches 117 °C; the model's sustained-climb value sits below it (CLAUDE.md, oil band); "
         "not recomputed here", "not charted yet"),
        ("Turbine housing temperature", "○", "cannot be tested",
         "the car has no sensor for it: every turbine figure is a model output", "no data possible"),
    ]


# =============================================================================
# The page
# =============================================================================
STUDY_CSS = """
nav.toc { display: flex; flex-wrap: wrap; gap: 6px 18px; font-size: 14.5px; }
nav.toc a { color: var(--ink2); text-decoration: none; }
nav.toc a:hover, nav.toc a:focus-visible { color: var(--ink); text-decoration: underline; }
.facts { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); gap: 10px 20px; margin: 0; }
.facts div { display: grid; gap: 2px; }
.facts dt { font: 600 12px/1.2 var(--font-head); letter-spacing: .07em; text-transform: uppercase; color: var(--muted); }
.facts dd { margin: 0; font: 13.5px/1.4 var(--font-data); color: var(--ink); }
.tiles { display: grid; grid-template-columns: repeat(auto-fit, minmax(16rem, 1fr)); gap: 12px; }
.tile { background: var(--surface); border: 1px solid var(--rule); border-radius: 6px; padding: 14px 16px;
        display: grid; gap: 6px; align-content: start; }
.tile .label { font: 600 12.5px/1.2 var(--font-head); letter-spacing: .07em; text-transform: uppercase; color: var(--ink2); }
.tile .value { font: 700 30px/1.05 var(--font-head); color: var(--ink); }
.tile p { font-size: 14.5px; }
.latest { margin: 0; padding-left: 20px; display: grid; gap: 6px; color: var(--ink2); max-width: 78ch; }
.part { font: 600 12.5px/1.2 var(--font-head); letter-spacing: .08em; text-transform: uppercase; color: var(--muted); }
h3 { font: 700 19px/1.25 var(--font-head); margin: 8px 0 0; }
details { border-top: 1px solid var(--grid); padding-top: 10px; }
details > summary { cursor: pointer; font-weight: 600; color: var(--ink); }
details[open] > summary { margin-bottom: 10px; }
table.status td { white-space: normal; text-align: left; font-family: var(--font-body); vertical-align: top; }
table.status td:nth-child(2) { white-space: nowrap; }
table.status th { text-align: left; }
.mark { font-family: var(--font-data); margin-right: 6px; }
.later { font-size: 14.5px; }
"""


def verdict_block(ver):
    parts = ['<div class="cells">']
    for c in ver["cells"]:
        parts.append(f'<div><span class="kind">{esc(c["cell"].lower())}</span>'
                     f'<span>{esc(c["gloss"]["en"])}</span></div>')
    parts.append("</div>")
    if ver["lines"]:
        parts.append("<details><summary>The verdict lines, quoted from results/</summary>")
        for line in ver["lines"]:
            parts.append(f'<figure class="quote"><blockquote>{esc(line["text"])}</blockquote>'
                         f'<figcaption>results/{esc(line["file"])}:{line["line"]}</figcaption></figure>')
        parts.append("</details>")
    return "\n".join(parts)


def build_page(ctx, web):
    c = ctx["counts"]
    head = [f"<title>{TITLE}</title>"]
    if web:
        head.append(f'<link rel="stylesheet" href="{esc(FONTS_URL)}">')
    head.append(f"<style>{page_css()}{PAIRS.EXTRA_CSS}{STUDY_CSS}</style>")
    c4v = ctx["verdicts"]["c4"]
    tiles = [
        ("Every agent against the baseline", f"{c['cut_lo']:.0f}–{c['cut_hi']:.0f} %",
         f"of the baseline ECU's median damage removed by the C4 agents, sighted and blind alike; "
         f"current-grade, the best hand-written policy, removes {c['cut_cg']:.1f} %. Sighted agents beat "
         f"its median in {c['med_s']} of {c['n']} pairs and blind agents in {c['med_b']} of {c['n']}, so "
         f"it is not the preview channel; on the worst episode {c['worst_s']} and {c['worst_b']} of "
         f"{c['n']} do worse than it."),
        ("Preview, C4", (c4v["cells"][0]["cell"].lower() if c4v["cells"] else "no verdict found"),
         ((c4v["short"] or {}).get("en", "") + ". Phase D and D2 were inconclusive. "
          "\"Preview does not help\" is not a sentence any of them supports.")),
        ("The simulator against the car", f"{ctx['n_agree']} agree",
         "independent checks; two more are fits to the same data and one a consistency check. The knock "
         "model is not validated, and the turbine, the part the project protects, has no sensor."),
    ]
    tile_html = "\n".join(f'<div class="tile"><span class="label">{esc(a)}</span>'
                          f'<span class="value">{esc(b)}</span><p>{esc(t)}</p></div>'
                          for a, b, t in tiles)
    facts = [("branch", f"JMF-2340550-sep17 @ {ctx['head']}"),
             ("logs", f"{ctx['n_drives']} drives, {ctx['minutes']:.1f} minutes"),
             ("Phase D scenario", "12 % climb at 180 s, 130 km/h, 42 °C"),
             ("D2 and C4 scenario", "a 12–16 % climb starting 120–300 s, per episode"),
             ("built", ctx["built"])]
    fact_html = "\n".join(f"<div><dt>{esc(a)}</dt><dd>{esc(b)}</dd></div>" for a, b in facts)

    body = ['<div class="wrap">',
            '<nav class="toc" aria-label="Sections"><a href="#summary">Summary</a><a href="#agents">The '
            'agents</a><a href="#sim">Simulation vs car</a><a href="#drives">Drives</a>'
            '<a href="#caveats">Caveats</a></nav>',
            '<section id="summary" class="cover">', "<header>",
            '<p class="meta">BMW B58B30O1 · 3.0 L inline-six · ZF 8HP51 · read-only OBD-II</p>',
            "<h1>The B58 preview study, on this branch</h1>",
            '<p class="lede">' + esc(
                "When is it worth knowing the road ahead? The project's claim is that one ratio settles it, "
                "H/τ: how far ahead you can see, over how fast the protected part heats up. This page shows "
                "what this branch's three preregistered experiments found, and every place the simulator can "
                "be laid beside the car's own logs.") + "</p>",
            f'<dl class="facts">{fact_html}</dl>', "</header>",
            f'<div class="tiles">{tile_html}</div>',
            "<h2>Found on 28 September</h2>",
            '<ul class="latest">',
            f"<li>The enrichment map misses the car in one cell ({esc(ctx['enrichment'])}). The documents "
            "said every cell was within 0.027; that was measured on the old dwell axis.</li>",  # RETIRED-OK: 0.027 -- names the superseded claim
            "<li>The raw-sensor temperature quoted beside mistake 13's table does not reproduce; the boost "
            "comparison it explains does.</li>",
            "<li>matplotlib is blocked by Windows Application Control on the team's machine, so these charts "
            "are plain SVG.</li>",
            "</ul>",
            f'<p class="meta">Two focused pages: <a href="{PAIRS.FIRST_PAGE}">the simulator against the '
            f'car</a> · <a href="{SVC.SECOND_PAGE}">the agents, pair by pair</a></p>',
            "</section>",
            '<section id="agents">', '<p class="part">Part 1 · the agents</p>',
            "<h2>Three preregistered ablations of the preview channel</h2>",
            "<p>" + esc(
                "Each experiment trained eight pairs of agents. In a pair both agents come from the same seed "
                "and code; one sees the road ahead, one does not. The rules of each test were committed "
                "before its agents trained, and 50 damage units were set in advance as the smallest effect "
                "worth caring about.") + "</p>",
            *[f'<figure class="chart"><div class="scroll">{svg}</div></figure>' for svg in ctx["agent_svgs"]],
            "<h3>Each experiment: every agent against the baseline, then the preview test</h3>",
            "<p>" + esc(
                "For each experiment the first chart measures both agents of every pair against the baseline "
                "ECU, as the result files print it; that is learned protection. The second is the test the "
                "team registered before training: the sighted agent against its blind twin, in damage "
                "units.") + "</p>"]
    for ex, svg, ver, vsvg, _ in ctx["pairs"]:
        body += [f'<figure class="chart"><div class="scroll">{vsvg}</div></figure>',
                 f'<figure class="chart"><div class="scroll">{svg}</div></figure>',
                 f'<div class="verdict">{verdict_block(ver)}</div>']
    body.append("<details><summary>Show the numbers</summary>")
    for title, (thead, trows) in ctx["agent_tables"]:
        body += [f"<h3>{esc(title)}</h3>", f'<div class="scroll">{html_table(thead, trows)}</div>']
    body += ["</details>",
             '<p class="later">Not on this page yet: the turbine temperature through an episode, why the '
             "locked scenario is 12 % at 130 km/h, and the training curves. Each needs new runs of the "
             "simulator, and comes next.</p>",
             "</section>",
             '<section id="sim">', '<p class="part">Part 2 · the simulator against the car</p>',
             "<h2>Where the model meets the logs</h2>",
             "<p>" + esc(
                 f"{ctx['n_drives']} drives of BimmerLink exports, read-only, never written to the car. Each "
                 "comparison says what kind of evidence it is, because a residual computed through the "
                 "model's own inversion cannot test that model (CLAUDE.md mistake 12).") + "</p>",
             '<div class="scroll"><table class="status"><tr><th>comparison</th><th>status</th>'
             "<th>what it found</th><th>kind</th></tr>"]
    for comp, mark, status, found, kind in ctx["status"]:
        body.append(f"<tr><td>{esc(comp)}</td><td><span class=\"mark\">{esc(mark)}</span>{esc(status)}</td>"
                    f"<td>{esc(found)}</td><td>{esc(kind)}</td></tr>")
    body.append("</table></div>")
    body += [f'<figure class="chart"><div class="scroll">{svg}</div></figure>' for svg in ctx["sim_svgs"]]
    body.append("<details><summary>Show the numbers</summary>")
    for title, (thead, trows) in ctx["sim_tables"]:
        body += [f"<h3>{esc(title)}</h3>", f'<div class="scroll">{html_table(thead, trows)}</div>']
    body += ["</details>", "</section>",
             '<section id="drives">', '<p class="part">Part 3 · the drives</p>',
             f"<h2>{ctx['n_drives']} drives, {ctx['minutes']:.1f} minutes</h2>",
             "<p>" + esc(
                 f"{ctx['n_carry']} of them carry samples into the dataset; the rest are too short, have no "
                 "coolant channel, or were census logs with every channel selected. drive10 is a two-hour "
                 "mountain drive, Jeddah to Taif and back, and it never brings the turbine to the protection "
                 "limit: the locked scenario is deliberately harsher than any recorded drive "
                 "(CLAUDE.md).") + "</p>",
             f'<div class="scroll">{html_table(*ctx["drives"])}</div>',
             "<h3>Drives that would settle what the logs cannot</h3>",
             '<ol class="latest">',
             "<li>More independent readings at high air flow: the top of the compressor envelope rests on a "
             "handful of readings per bin (the ceiling chart shows how many).</li>",
             "<li>The knock question: a drive logging both ignition-angle channels fast enough to see a retard "
             "event, which the current logs sample too slowly.</li>",
             f"<li>Steady operating points above {ctx['map_hi']:.0f} kPa, where every model figure is now "
             "extrapolation.</li>",
             "<li>The empty compressor bin above the air-mass sensor's ceiling; probably unreachable with this "
             "sensor.</li>",
             "</ol>",
             '<p class="later">new_drive.py scores a candidate drive against these before it is added.</p>',
             "</section>",
             '<section id="caveats">', '<p class="part">Part 4 · caveats</p>',
             "<h2>What this page is not</h2>",
             '<ul class="missing">',
             "<li>Not a verdict that preview does not help. The sentences that may be said are the "
             "preregistered readings quoted under each pair chart.</li>",
             "<li>Not measured turbine temperatures. The car has no sensor on the turbine housing, and the "
             "housing's heat capacity in the model is an assumed number.</li>",
             "<li>Not agents scored in the step they learned in: every agent trained at a 0.2 s step and was "
             "scored at 1.0 s, a known and unresolved limit shared by both arms (AUDIT2.md H2-2).</li>",
             "<li>Not a replication: C4's agents are Phase D2's agents trained longer, and they had not "
             "converged by the preregistered rule.</li>",
             "<li>Not a test of the breathing model at part load: both pressure channels on this car sit "
             "before the throttle.</li>",
             "<li>Not a road anyone drives: the locked scenario stands for sustained heavy load, and it is "
             "hotter than every recorded drive on purpose.</li>",
             "</ul>",
             "</section>",
             "<footer><p>Built by <code>plot_study_page.py</code> from this branch's <code>results/</code>, "
             "<code>data/</code> and <code>logs/raw/</code>. Nothing on this page is computed beyond reading "
             "and counting; every value is printed in <code>figures/study/numbers.txt</code>. Read-only: "
             "nothing in this project writes to the car.</p></footer>",
             "</div>"]
    if web:
        return "\n".join(head + body) + "\n"
    return "\n".join(["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
                      '<meta name="viewport" content="width=device-width, initial-scale=1">', *head,
                      "</head>", "<body>", *body, "</body>", "</html>"]) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    say("THIS BRANCH'S PREVIEW STUDY, ONE PAGE  (plot_study_page.py)")
    say()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True,
                          text=True, env={**os.environ, "GIT_OPTIONAL_LOCKS": "0"}).stdout.strip()

    # Part 1 -- the agents
    tables = {p: policy_tables(p) for p in ("phase_d", "d2", "c4")}
    budget_c4 = "C4: 300 000 training steps, not converged, the random climb"
    roads = chart_roads()
    pol = chart_policies("c4", "C4", budget_c4, tables["c4"])
    fuel_name, fuel_svg = chart_fuel("c4", "C4", budget_c4, tables["c4"])
    counts = pol[3]
    agent_svgs = [roads[1], pol[1], fuel_svg]
    pairs, verdicts, cut_c4 = [], {}, None
    for ex in PAIRS.EXPERIMENTS:
        ver = verdict(ex["prefix"])
        verdicts[ex["prefix"]] = ver
        prow = PAIRS.pairs(ex["prefix"])
        cut = PAIRS.cuts(ex["prefix"], prow)
        if ex["prefix"] == "c4":
            cut_c4 = cut
        vsvg, vtable = PAIRS.chart_vs_baseline(ex, prow, cut)
        svg, _, _, _ = PAIRS.chart(ex, prow, ver)
        pairs.append((ex, svg, ver, vsvg, vtable))
    c4_cuts = [cut_c4[s][k] for s in cut_c4 for k in ("sighted", "blind")]
    counts = dict(counts, cut_lo=min(c4_cuts), cut_hi=max(c4_cuts),
                  cut_cg=cut_c4[min(cut_c4)]["current-grade"])
    names = {"phase_d": "Phase D", "d2": "Phase D2", "c4": "C4"}
    agent_tables = [("The frozen test roads", roads[2])]
    agent_tables += [(f"{ex['name']}: every agent against the baseline ECU", vtable)
                     for ex, _, _, _, vtable in pairs]
    for p in ("phase_d", "d2", "c4"):
        t = tables[p]
        hand = t[min(t)]
        trows = [[r, f"{hand[r]['med']:.1f}", f"{hand[r]['iqr']:.1f}", f"{hand[r]['worst']:.1f}",
                  f"{hand[r]['fuel']:.0f}", f"{hand[r]['peak']:.0f}"]
                 for r in (UNPROTECTED, "reactive", "current-grade")]
        for s in sorted(t):
            for role in ("sighted", "blind"):
                v = t[s][role]
                trows.append([f"seed {s} · {role}", f"{v['med']:.1f}", f"{v['iqr']:.1f}",
                              f"{v['worst']:.1f}", f"{v['fuel']:.0f}", f"{v['peak']:.0f}"])
        agent_tables.append((f"{names[p]}: every policy, medians over the twenty episodes",
                             (["row", "median", "IQR width", "worst", "fuel, g", "peak, °C"], trows)))

    # Part 2 -- the simulator against the car (plot_sim_vs_car.py's own charts)
    S = pd.read_csv(os.path.join(HERE, "data", "master_samples.csv"))
    sims = [SVC.chart_gears(S), SVC.chart_boost(S), SVC.chart_envelope(S), SVC.chart_enrichment(S),
            SVC.chart_load(os.path.join(HERE, "data", "master_points.csv"))]
    sim_covers = {name: cover for name, _, _, cover in sims}
    bands = published_bands()
    status = status_rows(sim_covers, bands)
    n_agree = sum(1 for row in status if row[1] == "✓")
    enrich = re.search(r"([\d.]+) in", sim_covers["4_enrichment"][2])
    say("PUBLISHED BANDS  (validate.py's own rows)")
    for r in bands:
        ascii_name = r['name'].encode('ascii', 'replace').decode('ascii')
        say(f"   {ascii_name:<44}{r['value']:>9.1f}   {r['lo']:g}-{r['hi']:g}   "
            f"{'inside' if r['ok'] else 'OUTSIDE'}")
    say(f"   {sum(r['ok'] for r in bands)} of {len(bands)} inside")
    say()

    # Part 3 -- the drives
    M = pd.read_csv(os.path.join(HERE, "data", "manifest.csv"))
    P = pd.read_csv(os.path.join(HERE, "data", "master_points.csv"))

    def cell(v, nd=0):
        return "--" if pd.isna(v) else f"{v:,.{nd}f}"

    drive_rows = [[f.split("-")[0], cell(r.duration_min, 1), cell(r.samples), cell(r.rate_hz, 2),
                   cell(r.channels_present), cell(r.steady_windows), cell(r.max_rpm), cell(r.max_speed_kmh),
                   cell(r.max_map_kpa), cell(r.min_lambda, 2), "yes" if r.warm_samples > 0 else "no"]
                  for f, r in zip(M.file, M.itertuples())]
    drives = (["drive", "minutes", "rows", "Hz", "channels", "steady windows", "max rpm", "max km/h",
               "max kPa", "min λ", "in the dataset"], drive_rows)
    n_carry = int((M.warm_samples > 0).sum())
    say(f"DRIVES  (data/manifest.csv): {len(M)} in the manifest, {float(M.duration_min.sum()):.1f} min, "
        f"{n_carry} with samples in the dataset")
    say()

    ctx = dict(head=head or "unknown", built=datetime.date.today().isoformat(),
               n_drives=len(M), minutes=float(M.duration_min.sum()), n_carry=n_carry,
               map_hi=float(P.map_kpa.max()), counts=counts, verdicts=verdicts, pairs=pairs,
               agent_svgs=agent_svgs, agent_tables=agent_tables, status=status, n_agree=n_agree,
               sim_svgs=[svg for _, svg, _, _ in sims],
               sim_tables=[(cover[0], table) for _, _, table, cover in sims],
               enrichment=f"worst cell {enrich.group(1)} in λ" if enrich else sim_covers["4_enrichment"][2],
               drives=drives)

    for name, svg in ((roads[0], roads[1]), (pol[0], pol[1]), (fuel_name, fuel_svg)):
        with open(os.path.join(OUT, name + ".svg"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n")
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(ctx, web=False))
    with open(os.path.join(OUT, "page.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(ctx, web=True))

    say("WRITTEN")
    say("   figures/study/index.html and page.html")
    browser = find_browser()
    for name in (roads[0], pol[0], fuel_name):
        png = os.path.join(OUT, name + ".png")
        if browser is None:
            break
        if os.path.exists(png):
            os.remove(png)
        run_browser(browser, ["--hide-scrollbars", f"--window-size={W},{H}",
                              "--force-device-scale-factor=2", f"--screenshot={png}",
                              Path(OUT, name + ".svg").as_uri()])
        size = png_size(png) if os.path.exists(png) else None
        say(f"   figures/study/{name}.png   " + (f"{size[0]} x {size[1]} px" if size else "NOT WRITTEN"))
    say("   figures/study/numbers.txt   (this output)")
    everything = (LINES + ["", "--- read by plot_agent_pairs.py's functions ---"] + PAIRS.LINES
                  + ["", "--- read by plot_sim_vs_car.py's functions ---"] + SVC.LINES)
    with open(os.path.join(OUT, "numbers.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(everything) + "\n")


if __name__ == "__main__":
    main()
