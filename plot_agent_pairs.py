"""plot_agent_pairs.py -- the preview ablation, pair by pair: every agent, every seed.

    python plot_agent_pairs.py

Three preregistered experiments -- Phase D, Phase D2 and C4 -- each trained
eight pairs of agents. In a pair both agents come from the same seed, the same
code and the same budget; only the preview channel differs: the sighted agent
sees the road ahead, the blind one does not. This draws every agent of every
pair as a dot and writes figures/agent_pairs/:

    1_phase_d.svg, 2_d2.svg, 3_c4.svg     one chart per experiment (vector)
    1_phase_d.png, 2_d2.png, 3_c4.png     the same, 2000 x 1280 px
    index.html      the charts, each experiment's verdict quoted from results/,
                    and the numbers; open it in a browser, or print it
    page.html       the same page for the web (no document skeleton). Published
                    privately on 28 September 2026 at
                    https://claude.ai/artifact/6B2gRmzj4RT1ysLZoFNJMg
                    -- update THAT page (the Artifact tool's `url`); never
                    publish it again as a new one
    agent_pairs.pdf index.html printed, A4 landscape
    numbers.txt     this script's printed output

Written 28 September 2026 at Jad's request: "add the agents' points and the
seeds".

NOTHING HERE IS COMPUTED. Every damage figure is read by
analyse_phase_d2.load(prefix), the analysis scripts' own reader of
results/<prefix>_seed<k>.txt, and every verdict is QUOTED by
app.agent_catalog.verdict(prefix): the preregistered lines, word for word,
each cited as results/<file>:<line>. The page adds no statistic, no average
and no winner. It is the experiments' own numbers, drawn.

WHAT A READER MUST NOT TAKE FROM IT -- the charts and the page say so:

  * "Preview does not help." No experiment supports that sentence. Phase D and
    D2 are inconclusive; C4 is smaller than the MEI by the primary test, on
    one seed's margin, with the sensitivity test disagreeing and the agents
    not converged.
  * That C4 replicates D2. C4's agents are D2's agents trained longer.
  * That the agents beating the current-grade rule is evidence for preview.
    It is a different claim (AUDIT.md C3), and the blind agents beat it too.

READ-ONLY. It reads results/ and writes only into figures/agent_pairs/.
Everything it PRINTS is ASCII (CLAUDE.md mistake 16).
"""
from __future__ import annotations

import math
import os
import sys
import warnings
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import analyse_phase_d2  # noqa: E402
from analyse_phase_d2 import MEI  # noqa: E402
from app.agent_catalog import verdict  # noqa: E402
from plot_sim_vs_car import (  # noqa: E402
    Svg, Scale, esc, header, footer, legend_row, y_axis, x_axis, nice_ticks,
    page_css, html_table, find_browser, run_browser, png_size, fmt,
    MODEL, CAR, INK, INK2, MUTED, AXIS, W, H)

OUT = os.path.join(HERE, "figures", "agent_pairs")
SIGHTED, BLIND = MODEL, CAR        # palette slots 1 and 2, as on the first page
TITLE = "Eight Pairs, Three Experiments"
FIRST_PAGE = "https://claude.ai/artifact/YWSKwwCEPAwg1oMXCVXTec"

EXPERIMENTS = [
    dict(prefix="phase_d", anchor="phase-d", name="Phase D", file="1_phase_d",
         title="Phase D: eight pairs on a fixed climb",
         budget="C1 budget, 50 000 training steps · 21-22 September 2026",
         blind="the blind agent, which could memorise its one road",
         extra="Phase D's blind arm is not blind: the climb comes at the same second on every episode, "
               "so the blind agent could learn when it comes (results/PREREGISTRATION.md limit 7). "
               "Its minimum effect of interest was set after this result, so reading it against 50 "
               "units is post-hoc."),
    dict(prefix="d2", anchor="d2", name="Phase D2", file="2_d2",
         title="Phase D2: eight pairs on a randomised climb",
         budget="C1 budget, 50 000 training steps · 22-23 September 2026",
         blind="the blind agent",
         extra="The climb's start and grade were drawn per episode and the blind arm was checked "
               "blind before training (check_random_road.py). The minimum effect of interest, "
               "50 units, was set before this experiment."),
    dict(prefix="c4", anchor="c4", name="C4", file="3_c4",
         title="C4: Phase D2's design, trained to 300 000 steps",
         budget="C4 budget, 300 000 training steps, not converged · 23-24 September 2026",
         blind="the blind agent",
         extra="C4's agents are Phase D2's agents trained longer, not a replication: every one "
               "retraced its D2 twin bit for bit through 50 000 steps. By the preregistered rule "
               "they had not converged (results/C4_RESULT.txt)."),
]

LINES: list[str] = []


def say(s: str = "") -> None:
    if not s.isascii():
        raise ValueError(f"non-ASCII in printed output: {s!r}")
    print(s)
    LINES.append(s)


def pairs(prefix):
    """[(seed, sighted, blind, current-grade, baseline, blind - sighted)], as the
    result files print them (one decimal); nothing recomputed."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        rows, incomplete = analyse_phase_d2.load(prefix)
    if incomplete:
        raise SystemExit(f"{prefix}: incomplete result files for seeds {incomplete}")
    return [(int(seed), round(d["agent"], 1), round(d["agent (blind)"], 1),
             round(d["current-grade"], 1), round(d["baseline ECU"], 1), round(diff, 1))
            for seed, d, diff in rows]


def signed(v):
    return f"{v:+.1f}".replace("-", "−")


def chart(ex, rows, ver):
    cells = [c["cell"] for c in ver["cells"]]
    short = (ver["short"] or {}).get("en", "")
    seeds = [r[0] for r in rows]
    cg = sorted({r[3] for r in rows})
    base = sorted({r[4] for r in rows})
    top = max(max(max(r[1], r[2]) for r in rows), max(cg))
    lim = top * 1.12

    say(f"{ex['name'].upper()}  (results/{ex['prefix']}_seed*.txt, analyse_phase_d2.load)")
    # The results files' own column order. With 'baseline' last, verify_docs.py's
    # premise-baseline pattern read the next row's first damage figure as it.
    say(f"   {'seed':>4}{'baseline':>10}{'curr-grade':>12}{'sighted':>10}{'blind':>10}{'blind-sighted':>15}")
    for s, a, b, c, bl, d in rows:
        say(f"   {s:>4}{bl:>10.1f}{c:>12.1f}{a:>10.1f}{b:>10.1f}{d:>+15.1f}")
    say(f"   preregistered cell(s), quoted: {', '.join(cells) if cells else ver['state']}")
    for line in ver["lines"]:
        say(f"   quoted  results/{line['file']}:{line['line']}  ({line['key']})")
    say()

    sv = Svg()
    header(sv, ex["title"], short, cells[0] if cells else "NO VERDICT FOUND", ex["budget"])
    ftop = footer(sv, (
        "A pair is two agents trained from the same seed, with the same code and budget; only the "
        "preview channel differs. Each dot is one agent's median damage over the same 20 frozen test "
        "episodes (evaluate.py); lower is less damage. blind − sighted above zero means the blind agent "
        "took more damage, so preview helped in that pair; bold marks a pair at or above the 50-unit "
        f"minimum effect of interest. {ex['extra']} The unprotected baseline ECU scores "
        f"{' / '.join(f'{b:.1f}' for b in base)} here, off the top of the chart. "
        f"Data: results/{ex['prefix']}_seed*.txt."))
    box = (100, 170, W - 150, ftop - 78)
    legend_row(sv, 56, 146, [("dot", SIGHTED, "the sighted agent: sees the road ahead", 1.0),
                             ("dot", BLIND, ex["blind"], 1.0),
                             ("line", INK2, "the current-grade rule", 1.0)])
    xs = Scale(-0.5, len(seeds) - 0.5, box[0], box[2])
    ys = Scale(0.0, lim, box[3], box[1])
    y_axis(sv, ys, box, [(v, fmt(v)) for v in nice_ticks(0.0, lim, 6)],
           "median damage, 20 test episodes")
    # The current-grade rule: one fixed policy, so one value per experiment.
    for c in cg:
        sv.line(box[0], ys(c), box[2], ys(c), INK2, 1.3)
        sv.text(box[2] + 8, ys(c) + 4, f"current-grade {c:.1f}", size=11, color=INK2)
    # The minimum effect of interest, as a length the eye can hold a pair to.
    mx, m1 = box[2] + 38, lim * 0.32      # low in the margin, clear of every label
    sv.line(mx, ys(m1), mx, ys(m1 - MEI), INK, 2.0)
    sv.line(mx - 5, ys(m1), mx + 5, ys(m1), INK, 1.5)
    sv.line(mx - 5, ys(m1 - MEI), mx + 5, ys(m1 - MEI), INK, 1.5)
    sv.text(mx + 10, ys(m1) + 10, f"{MEI:.0f} units:", size=11, color=INK2)
    sv.text(mx + 10, ys(m1) + 24, "the smallest", size=11, color=INK2)
    sv.text(mx + 10, ys(m1) + 38, "effect of", size=11, color=INK2)
    sv.text(mx + 10, ys(m1) + 52, "interest", size=11, color=INK2)
    # The two agents of a pair sit a little apart sideways: when their scores
    # are within a few units, one dot would otherwise hide the other.
    for s, a, b, c, bl, d in rows:
        x = xs(s)
        sv.line(x - 7, ys(a), x + 7, ys(b), AXIS, 2.4)
        sv.dot(x - 7, ys(a), SIGHTED, r=6.0, title=f"seed {s}: sighted {a:.1f}")
        sv.dot(x + 7, ys(b), BLIND, r=6.0, title=f"seed {s}: blind {b:.1f}")
    x_axis(sv, xs, box, [(s, f"{s}") for s in seeds], None)
    sv.text((box[0] + box[2]) / 2, box[3] + 40, "pair, by its seed number", size=12.5,
            color=INK2, anchor="middle")
    yd = box[3] + 64
    sv.text(box[0] - 12, yd, "blind − sighted", size=11.5, color=INK2, anchor="end")
    for s, a, b, c, bl, d in rows:
        sv.text(xs(s), yd, signed(d), size=12.5, anchor="middle",
                weight=700 if d >= MEI else 400, color=INK if d >= MEI else INK2)
    svg = sv.render(f"{ex['name']}: each of eight pairs as two dots, the sighted and the blind "
                    "agent's median damage")
    table = (["seed", "baseline ECU", "current-grade", "sighted", "blind", "blind − sighted"],
             [[f"{s}", f"{bl:.1f}", f"{c:.1f}", f"{a:.1f}", f"{b:.1f}", signed(d)]
              for s, a, b, c, bl, d in rows])
    return svg, table, cells, short


EXTRA_CSS = """
.verdict { display: grid; gap: 10px; }
.cells { display: grid; gap: 8px; }
.cells div { display: flex; flex-wrap: wrap; align-items: baseline; gap: 4px 10px; color: var(--ink2); }
.quote { margin: 0; display: grid; gap: 3px; }
.quote blockquote { margin: 0; padding: 8px 12px; border-left: 3px solid var(--grid);
                    background: var(--surface); color: var(--ink); white-space: pre-wrap;
                    overflow-wrap: anywhere; font: 12.5px/1.5 var(--font-data); }
.quote figcaption { font: 12px var(--font-data); color: var(--muted); }
.say { border: 1.5px solid var(--ink); border-radius: 6px; padding: 12px 14px; display: grid; gap: 6px; }
.say p { color: var(--ink); max-width: none; }
a { color: var(--model); }
"""


def build_page(sections, web):
    ladder = "\n".join(
        f'<li><span class="kind">{esc((cells[0] if cells else "no verdict").lower())}</span>'
        f'<a href="#{ex["anchor"]}">{esc(ex["title"])}</a><span class="result">{esc(short)}</span></li>'
        for ex, _, _, cells, short, _ in sections)
    head = [f"<title>{TITLE}</title>"]
    if web:
        from plot_sim_vs_car import FONTS_URL
        head.append(f'<link rel="stylesheet" href="{esc(FONTS_URL)}">')
    head.append(f"<style>{page_css()}{EXTRA_CSS}</style>")
    body = [
        '<div class="wrap">',
        '<section class="cover">',
        "<header>",
        '<p class="meta">BSc graduation project, University of Jeddah · phase D, the preview ablation · '
        f'<a href="{FIRST_PAGE}">the simulator against the car</a></p>',
        "<h1>Eight pairs, three experiments</h1>",
        '<p class="lede">' + esc(
            "Each experiment trained eight pairs of agents. In a pair, both agents come from the same "
            "seed and the same code; one sees the road ahead and one does not. Each dot is one agent, "
            "each vertical line is one pair, and each experiment's verdict is quoted beside it from the "
            "file where it was fixed before the agents trained.") + "</p>",
        "</header>",
        f'<ol class="ladder">{ladder}</ol>',
        '<ul class="key">',
        "<li>A <b>blue</b> dot is the sighted agent and an <b>orange</b> dot the blind one. When orange "
        "sits higher, the blind agent took more damage: preview helped in that pair.</li>",
        "<li>The row under each chart is blind − sighted. The team set 50 damage units in advance as the "
        "smallest effect worth caring about; the black bar beside each chart is that length.</li>",
        "<li>The grey line is the current-grade rule, the best hand-written policy. Both agents beating "
        "it is a separate claim from preview (AUDIT.md C3): the blind agents beat it too.</li>",
        "</ul>",
        '<div class="say"><p><b>What may be said, and what may not.</b> The sentences that may be said '
        "are the preregistered readings quoted under each chart. \"Preview does not help\" is not one of "
        "them: no experiment here supports it (CLAUDE.md).</p></div>",
        "</section>",
    ]
    for ex, svg, _, cells, _, ver in sections:
        body += [f'<section id="{ex["anchor"]}">',
                 '<figure class="chart"><div class="scroll">', svg, "</div></figure>",
                 '<div class="verdict">']
        if ver["state"] != "found":
            body.append(f'<p class="say">{esc((ver["short"] or {}).get("en", ""))}</p>')
        body.append('<div class="cells">')
        for c in ver["cells"]:
            body.append(f'<div><span class="kind">{esc(c["cell"].lower())}</span>'
                        f'<span>{esc(c["gloss"]["en"])}</span></div>')
        body.append("</div>")
        for line in ver["lines"]:
            body.append(f'<figure class="quote"><blockquote>{esc(line["text"])}</blockquote>'
                        f'<figcaption>results/{esc(line["file"])}:{line["line"]}</figcaption></figure>')
        body += ["</div>", "</section>"]
    body += ['<section class="numbers">', "<h2>The numbers behind each chart</h2>"]
    for ex, _, (thead, trows), _, _, _ in sections:
        body += ["<div>", f"<h3>{esc(ex['title'])}</h3>",
                 f'<div class="scroll">{html_table(thead, trows)}</div>', "</div>"]
    body += ["</section>",
             "<footer><p>Built by <code>plot_agent_pairs.py</code>. Damage figures are read from "
             "<code>results/&lt;experiment&gt;_seed&lt;k&gt;.txt</code> by the analysis scripts' own reader, "
             "and every verdict line is quoted by <code>app/agent_catalog.py</code>; nothing on this page is "
             "computed. Every value is printed in <code>figures/agent_pairs/numbers.txt</code>.</p></footer>",
             "</div>"]
    if web:
        return "\n".join(head + body) + "\n"
    return "\n".join(["<!doctype html>", '<html lang="en">', "<head>", '<meta charset="utf-8">',
                      '<meta name="viewport" content="width=device-width, initial-scale=1">', *head,
                      "</head>", "<body>", *body, "</body>", "</html>"]) + "\n"


def main():
    os.makedirs(OUT, exist_ok=True)
    say("THE PREVIEW ABLATION, PAIR BY PAIR  (plot_agent_pairs.py)")
    say(f"minimum effect of interest (analyse_phase_d2.MEI): {MEI:.0f} damage units")
    say()
    sections = []
    for ex in EXPERIMENTS:
        rows = pairs(ex["prefix"])
        ver = verdict(ex["prefix"])
        svg, table, cells, short = chart(ex, rows, ver)
        sections.append((ex, svg, table, cells, short, ver))
        with open(os.path.join(OUT, ex["file"] + ".svg"), "w", encoding="utf-8", newline="\n") as fh:
            fh.write('<?xml version="1.0" encoding="UTF-8"?>\n' + svg + "\n")
    page = os.path.join(OUT, "index.html")
    with open(page, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(sections, web=False))
    with open(os.path.join(OUT, "page.html"), "w", encoding="utf-8", newline="\n") as fh:
        fh.write(build_page(sections, web=True))

    say("WRITTEN")
    say("   figures/agent_pairs/index.html and page.html")
    browser = find_browser()
    if browser is None:
        say("   NO CHROME OR EDGE FOUND: no PNG and no PDF. Open index.html and print it.")
    else:
        for ex in EXPERIMENTS:
            png = os.path.join(OUT, ex["file"] + ".png")
            if os.path.exists(png):
                os.remove(png)
            run_browser(browser, ["--hide-scrollbars", f"--window-size={W},{H}",
                                  "--force-device-scale-factor=2", f"--screenshot={png}",
                                  Path(OUT, ex["file"] + ".svg").as_uri()])
            size = png_size(png) if os.path.exists(png) else None
            say(f"   figures/agent_pairs/{ex['file']}.png   "
                + (f"{size[0]} x {size[1]} px" if size else "NOT WRITTEN"))
        pdf = os.path.join(OUT, "agent_pairs.pdf")
        if os.path.exists(pdf):
            os.remove(pdf)
        run_browser(browser, ["--no-pdf-header-footer", "--print-to-pdf-no-header",
                              f"--print-to-pdf={pdf}", Path(page).as_uri()])
        say("   figures/agent_pairs/agent_pairs.pdf   "
            + ("printed from index.html" if os.path.exists(pdf) else "NOT WRITTEN"))
    say("   figures/agent_pairs/numbers.txt      (this output)")
    with open(os.path.join(OUT, "numbers.txt"), "w", encoding="ascii", newline="\n") as fh:
        fh.write("\n".join(LINES) + "\n")


if __name__ == "__main__":
    main()
