"""make_figures.py -- the figures for Phase D, regenerated from results/.

    python make_figures.py

It reads ONLY the JSON that the simulation runs wrote into results/ and writes
PNGs into results/figures/. It computes nothing about the plant itself, so a
figure can never disagree with the run that produced it -- if a number on a
figure looks wrong, re-run the simulation, not this.

Inputs, all written by the simulation runs:
    results/traces_130kmh.json      per-step traces, four hand-written policies
    results/sweep_speed_grade.json  peak turbine over speed x grade, baseline
    results/phase_d_130kmh_raw.json per-episode rows, frozen 20-episode protocol
    runs/*/curve.csv                training returns, one row per episode

Palette and mark rules follow the project data-visualisation conventions:
categorical hues assigned in fixed order and never cycled, one axis per chart,
a legend whenever there is more than one series, and direct labels so identity
is never carried by colour alone.
"""
import json
import os
import glob

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
FIG = os.path.join(RES, "figures")
os.makedirs(FIG, exist_ok=True)

# Categorical slots, fixed order. Validated as a set against the light surface.
BLUE, ORANGE, AQUA, VIOLET = "#2a78d6", "#eb6834", "#1baf7a", "#4a3aa7"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8a85"
SURFACE = "#fcfcfb"
GRID = "#e4e3df"
CRIT = "#e34948"

POLICIES = [("baseline ECU", BLUE), ("reactive", ORANGE),
            ("current-grade", AQUA), ("predictive (hand)", VIOLET)]
TRIGGER_C = 850.0


def _style(ax, title=None, xlabel=None, ylabel=None):
    ax.set_facecolor(SURFACE)
    ax.grid(True, color=GRID, lw=0.7, zorder=0)
    ax.set_axisbelow(True)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=9, length=3)
    if title:
        ax.set_title(title, color=INK, fontsize=12, loc="left", pad=12,
                     fontweight="bold")
    if xlabel:
        ax.set_xlabel(xlabel, color=INK2, fontsize=10)
    if ylabel:
        ax.set_ylabel(ylabel, color=INK2, fontsize=10)


def _save(fig, name):
    path = os.path.join(FIG, name)
    fig.savefig(path, dpi=150, facecolor=SURFACE, bbox_inches="tight")
    plt.close(fig)
    print(f"  wrote {os.path.relpath(path, HERE)}")
    return path


# ---------------------------------------------------------------- fig 1-3
def traces():
    with open(os.path.join(RES, "traces_130kmh.json")) as f:
        tr = json.load(f)

    t = np.array(tr["baseline ECU"]["t"])
    grade = np.array(tr["baseline ECU"]["grade"])
    climb_from = float(t[np.argmax(grade > 0)])

    # --- fig 1: turbine housing temperature, whole episode + the zoom -----
    # The four policies are indistinguishable at full scale and separate by
    # about 25 K at the top, which is the entire subject of the experiment, so
    # the zoom is not decoration. Linestyle carries identity as well as colour
    # because current-grade and predictive overlap to within a degree.
    fig, axes = plt.subplots(1, 2, figsize=(12.4, 5.0),
                             gridspec_kw=dict(width_ratios=(1.35, 1.0)))
    ax, az = axes
    _style(ax, "Whole episode", "time into episode (s)", "turbine housing (C)")
    _style(az, "The top, magnified -- where the policies differ",
           "time into episode (s)", None)

    zx, zy = (240, t[-1]), (825, 900)
    for a in (ax, az):
        a.axvspan(climb_from, t[-1], color="#f3f2ee", zorder=0)
        a.axhline(TRIGGER_C, color=CRIT, lw=1.4, ls=(0, (5, 3)), zorder=2)
    ax.text(climb_from + 10, 320, "12 % grade begins", color=INK3, fontsize=9,
            style="italic")
    ax.text(t[-1] * 0.99, TRIGGER_C - 14,
            f"{TRIGGER_C:.0f} C protection trigger", color=CRIT, fontsize=9,
            ha="right", va="top")
    ax.add_patch(Rectangle((zx[0], zy[0]), zx[1] - zx[0], zy[1] - zy[0],
                           fill=False, ec=INK3, lw=1.1, ls=(0, (3, 3)),
                           zorder=5))

    styles = ["-", "-", "-", (0, (4, 2.2))]
    for i, ((name, col), ls) in enumerate(zip(POLICIES, styles)):
        y = np.array(tr[name]["t_turb"])
        for a in (ax, az):
            a.plot(t, y, color=col, lw=2.0, ls=ls, zorder=3, label=name,
                   solid_capstyle="round")
        az.annotate(f"{name}   peak {y.max():.1f} C",
                    xy=(t[-1], y[-1]), xytext=(8, (1 - i) * 11),
                    textcoords="offset points", color=col, fontsize=8.5,
                    va="center", fontweight="bold")
    ax.set_xlim(0, t[-1])
    az.set_xlim(*zx)
    az.set_ylim(*zy)
    az.set_xlim(zx[0], zx[1] * 1.62)
    az.set_xticks([300, 400, 500, 600, 700])
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
    fig.suptitle("Turbine housing temperature over the locked scenario "
                 "-- 12 % at 130 km/h, 42 C",
                 color=INK, fontsize=13, x=0.012, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, "fig1_turbine_trace.png")

    # --- fig 2: cumulative damage ----------------------------------------
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    _style(ax, "Cumulative thermal damage -- the whole cost is paid on the climb",
           "time into episode (s)", "cumulative damage (model units)")
    ax.axvspan(climb_from, t[-1], color="#f3f2ee", zorder=0)
    ax.text(climb_from + 10, 40, "12 % grade begins", color=INK3, fontsize=9,
            style="italic")
    styles = ["-", "-", "-", (0, (4, 2.2))]
    ends = []
    for (name, col), ls in zip(POLICIES, styles):
        y = np.array(tr[name]["dmg_cum"])
        ax.plot(t, y, color=col, lw=2.0, ls=ls, zorder=3, label=name,
                solid_capstyle="round")
        ends.append((name, col, float(y[-1])))
    # stagger the direct labels so the three protecting rows do not collide
    for i, (name, col, v) in enumerate(sorted(ends, key=lambda e: -e[2])):
        ax.annotate(f"{name}   {v:.1f}",
                    xy=(t[-1], v), xytext=(8, (1 - i) * 10),
                    textcoords="offset points", color=col, fontsize=8.5,
                    va="center", fontweight="bold")
    ax.set_xlim(0, t[-1] * 1.36)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
    _save(fig, "fig2_cumulative_damage.png")

    # --- fig 3: what protection buys and what it costs --------------------
    fig, axes = plt.subplots(1, 2, figsize=(11.0, 4.6))
    base_d = tr["baseline ECU"]["summary"]["damage"]
    base_f = tr["baseline ECU"]["summary"]["fuel"]
    names = [n for n, _ in POLICIES][1:]
    cols = [c for _, c in POLICIES][1:]
    cut = [100 * (1 - tr[n]["summary"]["damage"] / base_d) for n in names]
    pen = [100 * (tr[n]["summary"]["fuel"] / base_f - 1) for n in names]

    for ax, vals, lbl, ttl in ((axes[0], cut, "damage removed (%)",
                                "What protection buys"),
                               (axes[1], pen, "extra fuel burned (%)",
                                "What it costs")):
        _style(ax, ttl, None, lbl)
        b = ax.bar(names, vals, color=cols, width=0.55, zorder=3)
        for r, v in zip(b, vals):
            ax.annotate(f"{v:.1f} %",
                        xy=(r.get_x() + r.get_width() / 2, r.get_height()),
                        xytext=(0, 5), textcoords="offset points",
                        ha="center", color=INK, fontsize=10, fontweight="bold")
        ax.set_ylim(0, max(vals) * 1.30)
        ax.tick_params(axis="x", labelrotation=10)
    fig.suptitle("Hand-written protection on the locked scenario "
                 "(single rollout, seed 0)",
                 color=INK, fontsize=12, x=0.02, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    _save(fig, "fig3_protection_cost.png")


# ------------------------------------------------------------------- fig 4
def sweep():
    with open(os.path.join(RES, "sweep_speed_grade.json")) as f:
        sw = json.load(f)
    speeds = sorted({r["v_kmh"] for r in sw})
    grades = sorted({r["grade"] for r in sw})
    M = np.array([[next(r["peak_c"] for r in sw
                        if r["v_kmh"] == v and r["grade"] == g)
                   for g in grades] for v in speeds])

    fig, ax = plt.subplots(figsize=(7.8, 4.6))
    _style(ax, "Peak turbine temperature over the speed x grade sweep",
           "road gradient (%)", "road speed (km/h)")
    ax.grid(False)
    im = ax.imshow(M, cmap="Blues", vmin=300, vmax=950, aspect="auto",
                   origin="lower")
    ax.set_xticks(range(len(grades)), [f"{g}" for g in grades])
    ax.set_yticks(range(len(speeds)), [f"{v}" for v in speeds])
    for i in range(len(speeds)):
        for j in range(len(grades)):
            v = M[i, j]
            binds = v > TRIGGER_C
            ax.text(j, i, f"{v:.0f}", ha="center", va="center", fontsize=11,
                    color="#ffffff" if v > 780 else INK,
                    fontweight="bold" if binds else "normal")
            if binds:
                ax.add_patch(Rectangle((j - .5, i - .5), 1, 1, fill=False,
                                       ec=CRIT, lw=2.4, zorder=4))
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("peak turbine housing (C)", color=INK2, fontsize=9)
    cb.ax.tick_params(colors=INK2, labelsize=8)
    cb.outline.set_visible(False)
    ax.text(0, -0.28,
            f"red outline = peak above the {TRIGGER_C:.0f} C trigger, "
            "so the constraint binds and there is something to protect",
            transform=ax.transAxes, color=CRIT, fontsize=9)
    ax.text(0, -0.40, "baseline ECU, 900 s episode, 42 C ambient",
            transform=ax.transAxes, color=INK3, fontsize=9)
    _save(fig, "fig4_speed_grade_sweep.png")


# ------------------------------------------------------------------- fig 5
def curves():
    files = sorted(glob.glob(os.path.join(HERE, "runs", "*", "curve.csv")))
    if not files:
        print("  (no training curves found)")
        return
    fig, ax = plt.subplots(figsize=(9.6, 5.0))
    _style(ax, "Every training run this project has -- eleven episodes each",
           "episode", "episode return")
    ax.axhline(0, color=INK3, lw=0.9, ls="--", zorder=2)
    seen = set()
    for f in files:
        tag = os.path.basename(os.path.dirname(f))
        blind = tag.startswith("blind")
        col = ORANGE if blind else BLUE
        lbl = "blinded (no preview)" if blind else "sighted (preview)"
        d = np.loadtxt(f, delimiter=",", skiprows=1, usecols=(0, 1, 2))
        ax.plot(d[:, 0], d[:, 1], color=col, lw=1.6, alpha=0.65, zorder=3,
                marker="o", ms=4, label=None if lbl in seen else lbl)
        seen.add(lbl)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
    ax.text(0.02, 0.97,
            "50 000 steps against a 4 500-step episode is eleven points, and the\n"
            "preference weights are redrawn at every reset -- so consecutive\n"
            "points are not scored with the same ruler. These ran at 110 km/h,\n"
            "where the constraint does not bind.",
            transform=ax.transAxes, va="top", color=INK2, fontsize=9,
            bbox=dict(fc=SURFACE, ec=GRID, lw=0.8, boxstyle="round,pad=0.5"),
            zorder=6)
    _save(fig, "fig5_training_curves.png")


# ------------------------------------------------------------------- fig 6
def phase_d():
    path = os.path.join(RES, "phase_d_130kmh_raw.json")
    if not os.path.exists(path):
        print("  (phase D rows not present yet -- skipping figs 6 and 7)")
        return
    with open(path) as f:
        rows = json.load(f)
    names = []
    for r in rows:
        if r["policy"] not in names:
            names.append(r["policy"])

    def col(n, k):
        return np.array([r[k] for r in rows if r["policy"] == n], dtype=float)

    base = float(np.median(col("baseline ECU", "damage")))
    base_f = float(np.median(col("baseline ECU", "fuel")))

    def cut(n):
        return 100.0 * (1.0 - float(np.median(col(n, "damage"))) / base)

    cols = [BLUE if n.startswith("runs/sighted")
            else ORANGE if n.startswith("runs/blind")
            else AQUA if n == "current-grade"
            else VIOLET if n == "predictive (hand)"
            else INK3 if n == "reactive"
            else INK2 for n in names]
    med = np.array([float(np.median(col(n, "damage"))) for n in names])
    q1 = np.array([float(np.percentile(col(n, "damage"), 25)) for n in names])
    q3 = np.array([float(np.percentile(col(n, "damage"), 75)) for n in names])

    # ---------------- fig 6: every policy, and the paired ablation --------
    fig, axes = plt.subplots(1, 2, figsize=(13.6, 6.6),
                             gridspec_kw=dict(width_ratios=(1.55, 1.0)))
    ax, ar = axes
    _style(ax, "Every policy, median damage with IQR",
           "median episode damage (lower is better)", None)
    y = np.arange(len(names))
    ax.barh(y, med, color=cols, height=0.62, zorder=3)
    ax.errorbar(med, y, xerr=[med - q1, q3 - med], fmt="none", ecolor=INK2,
                elinewidth=1.4, capsize=4, zorder=4)
    ax.set_yticks(y, [n.replace("runs/", "") for n in names])
    ax.invert_yaxis()
    ax.axvline(base, color=CRIT, lw=1.3, ls=(0, (5, 3)), zorder=2)
    ax.text(base, -0.80, " baseline median", color=CRIT, fontsize=9,
            va="center")
    for yi, m in zip(y, med):
        ax.annotate(f"{m:.0f}   cuts {100 * (1 - m / base):.1f} %",
                    xy=(m, yi), xytext=(8, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=9)
    ax.set_xlim(0, max(q3) * 1.34)

    # The IQR of the four hand-written rows is zero BY CONSTRUCTION, and that
    # has to be said or the figure flatters them: those policies never read the
    # preference vector, so all twenty episodes are the same rollout. Only the
    # agents, which carry w in the observation, actually vary across episodes.
    ax.text(0, -0.085,
            "the four hand-written rows have zero IQR by construction -- they "
            "do not read the preference vector,\nso all twenty episodes are one "
            "rollout. Only the agents see w and therefore vary.",
            transform=ax.transAxes, color=INK3, fontsize=8.5, va="top")

    _style(ar, "The ablation, PAIRED by seed",
           "damage cut vs baseline (%)", None)
    s_cut = [cut(f"runs/sighted_seed{s}") for s in range(5)]
    b_cut = [cut(f"runs/blind_seed{s}") for s in range(5)]
    yy = np.arange(5)
    ar.barh(yy - 0.19, s_cut, height=0.34, color=BLUE, zorder=3,
            label="sighted (preview)")
    ar.barh(yy + 0.19, b_cut, height=0.34, color=ORANGE, zorder=3,
            label="blinded (no preview)")
    ar.set_yticks(yy, [f"seed {s}" for s in range(5)])
    ar.invert_yaxis()
    g_cut = cut("current-grade")
    ar.axvline(g_cut, color=AQUA, lw=2.0, ls=(0, (5, 3)), zorder=5)
    ar.text(g_cut - 1.2, -0.62, "current-grade\nno preview at all", color=AQUA,
            fontsize=8.5, va="center", ha="right", fontweight="bold")
    for yi, (sv, bv) in enumerate(zip(s_cut, b_cut)):
        ar.annotate(f"{sv - bv:+.1f} pts", xy=(max(sv, bv), yi),
                    xytext=(9, 0), textcoords="offset points", va="center",
                    color=INK, fontsize=9.5, fontweight="bold")
    d = np.array(s_cut) - np.array(b_cut)
    ar.set_xlim(0, max(max(s_cut), max(b_cut)) * 1.32)
    ar.legend(loc="upper right", frameon=False, fontsize=9, labelcolor=INK2)
    ar.text(0, -0.085,
            f"paired difference: median {np.median(d):+.1f}, mean {d.mean():+.1f}, "
            f"sd {d.std(ddof=1):.1f} points (n = 5)\n"
            f"95 % CI {d.mean() - 2.776 * d.std(ddof=1) / np.sqrt(5):+.1f} to "
            f"{d.mean() + 2.776 * d.std(ddof=1) / np.sqrt(5):+.1f} -- "
            "indistinguishable from zero",
            transform=ar.transAxes, color=INK2, fontsize=8.5, va="top")

    fig.suptitle("Phase D protocol -- twenty frozen episodes, 12 % at 130 km/h",
                 color=INK, fontsize=13, x=0.012, ha="left", fontweight="bold")
    fig.text(0.012, 0.005,
             "THESE AGENTS ARE OUT OF DISTRIBUTION TWICE OVER: trained at "
             "110 km/h where the constraint never binds, and at dt = 0.2 s "
             "while this protocol runs dt = 1.0 s.\nThis is what the existing "
             "runs are worth, not Phase D's answer.",
             color=CRIT, fontsize=9)
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    _save(fig, "fig6_phase_d.png")

    # ---------------- fig 7: what the damage cut costs in fuel ------------
    # Fourteen labelled points collide, so each sighted/blinded PAIR is joined
    # by a tie and labelled once. The tie is the ablation drawn in the
    # trade-off plane: a long tie would be a preview effect, and none is long.
    def xy(n):
        return (100.0 * (float(np.median(col(n, "fuel"))) / base_f - 1.0),
                cut(n))

    fig, ax = plt.subplots(figsize=(10.0, 6.4))
    _style(ax, "Damage against fuel -- and the ablation drawn as a tie",
           "extra fuel burned vs baseline (%)", "damage cut vs baseline (%)")
    ax.axhline(0, color=INK3, lw=0.9, ls="--", zorder=2)
    ax.axvline(0, color=INK3, lw=0.9, ls="--", zorder=2)

    for i in range(5):
        xs, ys = xy(f"runs/sighted_seed{i}")
        xb, yb = xy(f"runs/blind_seed{i}")
        ax.plot([xs, xb], [ys, yb], color=INK3, lw=1.2, zorder=3)
        ax.scatter([xs], [ys], s=130, color=BLUE, zorder=5, marker="o",
                   edgecolor=SURFACE, linewidth=1.8,
                   label="trained, sighted" if i == 0 else None)
        ax.scatter([xb], [yb], s=130, color=ORANGE, zorder=5, marker="o",
                   edgecolor=SURFACE, linewidth=1.8,
                   label="trained, blinded" if i == 0 else None)
        ax.annotate(f"seed {i}", xy=((xs + xb) / 2, (ys + yb) / 2),
                    xytext={0: (0, -24), 1: (0, 16), 2: (0, 16),
                            3: (-26, -24), 4: (0, -24)}[i],
                    textcoords="offset points", ha="center",
                    color=INK2, fontsize=9, fontweight="bold")

    hand = [("baseline ECU", INK2, (0, -20)), ("reactive", INK3, (0, -20)),
            ("current-grade", AQUA, (-62, 2)),
            ("predictive (hand)", VIOLET, (62, 2))]
    for n, c, off in hand:
        x, yv = xy(n)
        ax.scatter([x], [yv], s=150, color=c, zorder=5, marker="s",
                   edgecolor=SURFACE, linewidth=1.8,
                   label="hand-written" if n == "baseline ECU" else None)
        ax.annotate(n, xy=(x, yv), xytext=off, textcoords="offset points",
                    ha="center", color=c, fontsize=9, fontweight="bold")

    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
    ax.text(0, -0.13,
            "Seeds 0 and 1 cut damage by about 45 % while burning LESS fuel "
            "than the baseline -- the only points in the figure that beat it "
            "on both axes.",
            transform=ax.transAxes, color=INK2, fontsize=9)
    ax.margins(0.17)
    _save(fig, "fig7_damage_vs_fuel.png")


# ================================================== MODEL AGAINST THE CAR
# One encoding across every figure below: CAR = blue, SIMULATION = orange, and
# aqua for a third series where one exists. The first three palette slots are
# the ones validated for all pairs, which is what an overlapping scatter needs.
CAR, SIM, THIRD = BLUE, ORANGE, AQUA


def _mvd():
    path = os.path.join(RES, "model_vs_data.json")
    if not os.path.exists(path):
        print("  (results/model_vs_data.json missing -- run model_vs_data.py)")
        return None
    with open(path) as f:
        return json.load(f)


def _parity(ax, lo, hi):
    ax.plot([lo, hi], [lo, hi], color=INK3, lw=1.0, ls=(0, (4, 3)), zorder=2)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")


def model_vs_data():
    R = _mvd()
    if R is None:
        return

    # ---------------- fig 8: load residual, and what it can see -----------
    L = R["load"]
    fig, axes = plt.subplots(1, 2, figsize=(12.0, 5.4),
                             gridspec_kw=dict(width_ratios=(1.0, 1.0)))
    ax, ab = axes
    _style(ax, "Relative air filling, 26 operating points",
           "car -- Relative air filling (%)", "simulation (%)")
    m = np.array([p["meas"] for p in L["points"]])
    s = np.array([p["model"] for p in L["points"]])
    _parity(ax, 10, 70)
    ax.scatter(m, s, s=70, color=SIM, edgecolor=SURFACE, lw=1.5, zorder=4)
    ax.text(0.04, 0.94, f"mean |error| {L['mape']:.1f} %\nzero fitted parameters",
            transform=ax.transAxes, va="top", color=INK, fontsize=10,
            fontweight="bold")
    _style(ab, "What that residual can and cannot see", None,
           "load residual (%)")
    cats = ["as shipped\n3.0 L six", "the 2.0 L four\nof mistake 1"]
    vals = [L["mape"], L["wrong_engine_mape"]]
    b = ab.bar(cats, vals, color=[SIM, INK3], width=0.5, zorder=3)
    for r, v in zip(b, vals):
        ab.annotate(f"{v:.1f} %", xy=(r.get_x() + r.get_width() / 2, v),
                    xytext=(0, 5), textcoords="offset points", ha="center",
                    color=INK, fontsize=11, fontweight="bold")
    ab.set_ylim(0, max(vals) * 1.25)
    ab.text(0.02, -0.20,
            "Sensitive to displacement -- it would have caught mistake 1 on day "
            "one.\nBLIND to the breathing model: eta_v, residual fraction and "
            "charge\ntemperature all cancel out of it (CLAUDE.md mistake 12).",
            transform=ab.transAxes, color=INK2, fontsize=9, va="top")
    fig.suptitle("Load: the simulator against BMW's relative air filling channel",
                 color=INK, fontsize=13, x=0.012, ha="left", fontweight="bold")
    fig.tight_layout(rect=(0, 0.02, 1, 0.93))
    _save(fig, "fig8_load_residual.png")

    # ---------------- fig 9: boosted manifold pressure --------------------
    B = R["boost"]
    # Cumulative, not histograms: the logs are forward-filled round-robin, so
    # any binning shows the poll pattern as spikes. On a CDF the median gap is
    # simply the horizontal distance between curves at 0.5.
    fig, ax = plt.subplots(figsize=(10.0, 5.6))
    _style(ax, "Manifold pressure under boost -- simulation against the car",
           "manifold pressure, kPa absolute", "share of samples at or below")
    ax.axhline(0.5, color=INK3, lw=0.9, ls=(0, (4, 3)), zorder=2)
    series = ((B["logged"], CAR, "car -- its own Boost pressure channel",
               B["median_logged"], None),
              (B["model"], SIM, "simulation -- modelled charge temperature",
               B["median_model"], B["gap_model_pct"]),
              (B["raw_sensor"], THIRD,
               "simulation -- raw pre-throttle sensor (before mistake 13)",
               B["median_raw"], B["gap_raw_pct"]))
    for vals, col, lbl, med, gap in series:
        v = np.sort(np.asarray(vals, dtype=float))
        ax.step(v, np.arange(1, len(v) + 1) / len(v), where="post", color=col,
                lw=2.2, label=lbl, zorder=3)
        ax.scatter([med], [0.5], s=55, color=col, edgecolor=SURFACE, lw=1.5,
                   zorder=5)
        ax.annotate(f"{med:.0f} kPa" + ("" if gap is None else f"   {gap:+.1f} %"),
                    xy=(med, 0.5), xytext=(8, -14 if gap is None else 10),
                    textcoords="offset points", color=col, fontsize=9.5,
                    fontweight="bold")
    ax.set_xlim(195, 345)
    ax.set_ylim(0, 1.02)
    ax.legend(loc="lower right", frameon=False, fontsize=9, labelcolor=INK2)
    ax.text(0, -0.17,
            f"{B['n_model']} boosted, MAF-unpinned model samples above 200 kPa "
            f"against {B['n_logged']} logged boost readings above 15 psi gauge -- "
            "the two gates select the same region by construction.",
            transform=ax.transAxes, color=INK3, fontsize=8.5)
    _save(fig, "fig9_boost_pressure.png")

    # ---------------- fig 10: enrichment, cell by cell --------------------
    E = R["enrichment"]
    cells = E["cells"]
    fig, ax = plt.subplots(figsize=(10.4, 5.8))
    _style(ax, "Enrichment: base_lambda against the car, above 180 kPa",
           "lambda (lower = richer)", None)
    y = np.arange(len(cells))[::-1]
    hollow_labelled = False
    for yi, c in zip(y, cells):
        ax.plot([c["meas"], c["model"]], [yi, yi], color=GRID, lw=5, zorder=2,
                solid_capstyle="round")
        ax.scatter([c["meas"]], [yi], s=90, color=CAR, zorder=4, edgecolor=SURFACE,
                   lw=1.5, label="car (median)" if yi == y[0] else None)
        ax.scatter([c["model"]], [yi], s=90, color=SIM, zorder=4, edgecolor=SURFACE,
                   lw=1.5, marker="D",
                   label="simulation (median)" if yi == y[0] else None)
        if abs(c["meas_rows_axis"] - c["meas"]) > 0.005:
            ax.scatter([c["meas_rows_axis"]], [yi], s=90, facecolor="none",
                       edgecolor=CAR, lw=1.6, zorder=4,
                       label=(None if hollow_labelled
                              else "car, on the retired row-count dwell axis"))
            hollow_labelled = True
        d = c["model"] - c["meas"]
        ax.annotate(f"{d:+.3f}   n={c['n']}", xy=(max(c["meas"], c["model"]), yi),
                    xytext=(12, 0), textcoords="offset points", va="center",
                    color=INK if abs(d) > 0.03 else INK2, fontsize=9,
                    fontweight="bold" if abs(d) > 0.03 else "normal")
    ax.set_yticks(y, [f"{c['rpm']} rpm, dwell {c['dwell']}" for c in cells])
    ax.set_xlim(0.76, 1.06)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
    ax.text(0, -0.16,
            "The 0.87 CLAUDE.md quotes for 4500-7000 rpm at 4-8 s is the hollow "
            "circle: dwell counted in ROWS at an assumed 4.6 Hz, which AUDIT.md "
            "H3 retired.\nOn real timestamps the car reads 0.83 there, and the "
            "model sits lean of it by more than the documented 0.027.",
            transform=ax.transAxes, color=INK2, fontsize=8.5, va="top")
    _save(fig, "fig10_enrichment.png")

    # ---------------- fig 11: spark ---------------------------------------
    Sp = R["spark"]
    fig, ax = plt.subplots(figsize=(8.0, 7.0))
    _style(ax, "Part-load spark: commanded against logged",
           "car -- Actual ignition angle (deg BTDC)", "simulation (deg BTDC)")
    m = np.array([p["meas"] for p in Sp["points"]])
    _parity(ax, 10, 45)
    ax.scatter(m, [p["at_fit"] for p in Sp["points"]], s=60, color=THIRD,
               edgecolor=SURFACE, lw=1.4, zorder=4,
               label=f"as fitted, 7 Sep (IAT comp. on the sensor)   "
                     f"RMS {Sp['at_fit']['rmse']:.1f}, bias {Sp['at_fit']['mean']:+.1f}")
    ax.scatter(m, [p["as_run"] for p in Sp["points"]], s=60, color=SIM,
               edgecolor=SURFACE, lw=1.4, zorder=5, marker="D",
               label=f"as the simulator runs it (IAT comp. on the charge)   "
                     f"RMS {Sp['as_run']['rmse']:.1f}, bias {Sp['as_run']['mean']:+.1f}")
    ax.legend(loc="upper left", frameon=False, fontsize=8.5, labelcolor=INK2)
    ax.text(0, -0.13,
            "Mistake 13 moved the IAT compensation's input from the compressor-"
            "outlet sensor\nto the modelled charge temperature. The map's "
            "constants were not refitted, so the\nbaseline now runs about 3 deg "
            "advanced of the car at part load.",
            transform=ax.transAxes, color=INK2, fontsize=8.5, va="top")
    _save(fig, "fig11_spark.png")

    # ---------------- fig 12: thermal, both drives ------------------------
    for key, tag, name in (("drive10-20260918_233912.csv", "fig12", "drive10"),
                           ("7475b5d7-20260908_142743.csv", "fig13", "7475b5d7")):
        th = R["thermal"][key]
        t = np.array(th["t"]) / 60.0
        fig, axes = plt.subplots(2, 1, figsize=(11.0, 7.0), sharex=True)
        for ax, meas, mod, lbl in ((axes[0], th["oil_meas"], th["oil_model"], "oil"),
                                   (axes[1], th["ect_meas"], th["ect_model"], "coolant")):
            _style(ax, None, None, f"{lbl} temperature (C)")
            mo = np.array(meas, dtype=float)
            mo[mo == 0.0] = np.nan        # BimmerLink placeholder, AUDIT.md M8
            md = np.array(mod, dtype=float)
            ax.plot(t, mo, color=CAR, lw=1.8, zorder=3, label=f"car -- {lbl} channel")
            ax.plot(t, md, color=SIM, lw=1.4, zorder=4,
                    label="simulation -- thermal.py, free-running")
            ok = np.isfinite(mo) & np.isfinite(md)
            ax.text(0.99, 0.95,
                    f"median {np.median(md[ok] - mo[ok]):+.1f} K   "
                    f"peak: car {np.nanmax(mo):.0f} C, model {np.nanmax(md):.0f} C",
                    transform=ax.transAxes, ha="right", va="top", color=INK,
                    fontsize=9.5, fontweight="bold",
                    bbox=dict(fc=SURFACE, ec=GRID, lw=0.8, boxstyle="round,pad=0.4"))
        axes[0].legend(loc="lower left", bbox_to_anchor=(0.0, 1.0), ncol=2,
                       frameon=False, fontsize=9.5, labelcolor=INK2)
        axes[1].set_xlabel("minutes into the drive", color=INK2, fontsize=10)
        cap = ("drive10 reaches 117 C of oil -- the only drive inside the published "
               "115-140 C band -- and the model runs a few K cool of it, as "
               "validate.py's climb row does."
               if name == "drive10" else
               "The oil spikes are the model's oil time constant: 16 s, against a "
               "20-400 s band (validate.py). The real sump barely moves on a "
               "230 km/h pull; the model's oil node chases it.")
        fig.suptitle(f"Thermal network driven over {name}, against the car's own "
                     "sensors", color=INK, fontsize=13, x=0.012, ha="left",
                     fontweight="bold")
        fig.text(0.012, 0.005, cap, color=INK2, fontsize=9)
        fig.tight_layout(rect=(0, 0.03, 1, 0.95))
        _save(fig, f"{tag}_thermal_{name}.png")

    # ---------------- fig 14: knock ---------------------------------------
    K = R["knock"]
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    _style(ax, "Knock: the model's integral against the car's own retard",
           "simulation -- knock integral", "car -- retard applied (deg)")
    ki = np.array(K["ki"])
    rt = np.array(K["retard"])
    hb = ax.hexbin(ki, rt, gridsize=(60, 40), extent=(0, 1.6, -2, 20),
                   bins="log", cmap="Blues", mincnt=1, zorder=3)
    cb = fig.colorbar(hb, ax=ax, pad=0.02)
    cb.set_label("samples (log)", color=INK2, fontsize=9)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, labelsize=8)
    ax.axvline(0.85, color=CRIT, lw=1.2, ls=(0, (4, 3)), zorder=4)
    ax.text(0.87, 7.5, "damage-term\nknee, KI 0.85", color=CRIT, fontsize=9)
    ax.text(0.97, 0.60, f"correlation {K['corr']:+.3f}\n{K['n']:,} paired samples",
            transform=ax.transAxes, ha="right", va="top", color=INK, fontsize=11,
            fontweight="bold",
            bbox=dict(fc=SURFACE, ec=GRID, lw=0.8, boxstyle="round,pad=0.4"))
    above = int((rt > 20).sum())
    ax.text(0, -0.15,
            "A NEGATIVE RESULT. The model's knock integral carries no detectable "
            "information about the retard the car applies. Do not quote a "
            "knock-limited\nspark or knock damage term as calibrated. "
            f"({above} samples above 20 deg -- gearshift torque cuts, not knock -- "
            "sit off the top. Drive 7475b5d7.)",
            transform=ax.transAxes, color=INK2, fontsize=8.5, va="top")
    _save(fig, "fig14_knock.png")

    # ---------------- fig 15: gearbox -------------------------------------
    G = R["gearbox"]
    fig, ax = plt.subplots(figsize=(11.0, 5.0))
    _style(ax, "Gearbox: the ratio the car actually ran, against the published "
           "ZF 8HP51", "overall ratio, engine speed / wheel speed (log scale)",
           "samples")
    e = np.array(G["edges"])
    ax.bar(e[:-1], G["hist"], width=np.diff(e), align="edge", color=CAR,
           zorder=3, label="car -- from rpm and road speed")
    for i, r in enumerate(G["published"]):
        ax.axvline(r, color=SIM, lw=1.6, ls=(0, (4, 3)), zorder=4,
                   label="published ratio x final drive" if i == 0 else None)
        ax.text(r, max(G["hist"]) * 1.02, f"{i + 1}", ha="center", color=SIM,
                fontsize=10, fontweight="bold")
    ax.set_xscale("log")
    ax.set_xlim(1.7, 20)
    from matplotlib.ticker import NullFormatter
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([2, 3, 4, 5, 7, 10, 15], ["2", "3", "4", "5", "7", "10", "15"])
    ax.legend(loc="center right", frameon=False, fontsize=9, labelcolor=INK2)
    ax.text(0, -0.18,
            f"{G['within4_pct']:.1f} % of {G['n']:,} moving samples sit within 4 % of "
            "a published ratio. The car's own 'Actual gear' channel never reports "
            f"above {G['gear_channel_max']:.0f} -- it clamps, and calls 7th and 8th "
            "'6' (mistake 18).",
            transform=ax.transAxes, color=INK2, fontsize=9)
    _save(fig, "fig15_gearbox.png")

    # ---------------- fig 16: compressor envelope -------------------------
    V = R["envelope"]
    fig, ax = plt.subplots(figsize=(9.6, 5.6))
    _style(ax, "Compressor envelope: what the car did, and the ceiling the "
           "simulator enforces", "corrected mass flow (kg/s)", "pressure ratio")
    ax.scatter(V["flow"], V["pr"], s=6, color=CAR, alpha=0.35, zorder=3,
               lw=0, label=f"car -- {len(V['flow']):,} of {V['n']:,} quasi-steady samples")
    ax.plot(V["curve_flow"], V["curve_pr"], color=SIM, lw=2.4, zorder=4,
            label="simulation -- plant.boost_ceiling_kpa")
    ax.axvspan(0.314, 0.36, color="#f3f2ee", zorder=1)
    ax.text(0.316, 1.05, "MAF\nsaturates", color=INK3, fontsize=8.5)
    ax.legend(loc="upper left", frameon=False, fontsize=9, labelcolor=INK2)
    ax.set_xlim(0, 0.36)
    ax.text(0, -0.15,
            "The top of this curve rests on four to five independent readings "
            "per flow bin (AUDIT.md H4). It is an operating ceiling, not a "
            "compressor map.",
            transform=ax.transAxes, color=INK2, fontsize=8.5)
    _save(fig, "fig16_envelope.png")

    # ---------------- fig 17: duty cycle ----------------------------------
    D = R["duty"]
    H = np.array(D["H"]).T
    fig, ax = plt.subplots(figsize=(10.0, 5.8))
    _style(ax, "Where the car was driven, against where Phase D is scored",
           "engine speed (rpm)", "manifold pressure (kPa)")
    ax.grid(False)
    Hm = np.ma.masked_where(H <= 0, H)
    im = ax.pcolormesh(D["rpm_edges"], D["map_edges"], np.log10(Hm), cmap="Blues",
                       zorder=2)
    cb = fig.colorbar(im, ax=ax, pad=0.02)
    cb.set_label("car samples (log10)", color=INK2, fontsize=9)
    cb.outline.set_visible(False)
    cb.ax.tick_params(colors=INK2, labelsize=8)
    ax.scatter([D["scenario_rpm"]], [D["scenario_map"]], s=280, marker="*",
               color=SIM, edgecolor=INK, lw=0.8, zorder=5)
    ax.axhline(D["scenario_map"], color=SIM, lw=1.0, ls=(0, (4, 3)), zorder=3)
    ax.annotate("simulation: the locked climb\n12 % at 130 km/h, "
                f"{D['scenario_rpm']:.0f} rpm, {D['scenario_map']:.0f} kPa",
                xy=(D["scenario_rpm"], D["scenario_map"]), xytext=(-150, 34),
                textcoords="offset points", color=SIM, fontsize=9.5,
                fontweight="bold",
                bbox=dict(fc=SURFACE, ec=SIM, lw=0.8, boxstyle="round,pad=0.35"),
                arrowprops=dict(arrowstyle="-", color=SIM, lw=1.0))
    ax.text(0, -0.15,
            f"Only {D['frac_logs_at_or_above_scenario']:.1f} % of "
            f"{D['n']:,} moving samples reach the climb's manifold pressure. The "
            "car was driven fast on flat road; the scenario needs a grade to load "
            "it.\nThat is why elevation is in the scenario, and why no amount of "
            "further logging validates the hot region.",
            transform=ax.transAxes, color=INK2, fontsize=8.5, va="top")
    _save(fig, "fig17_duty_cycle.png")

    # ---------------- fig 18: literature bands ----------------------------
    Lr = R["literature"]
    fig, ax = plt.subplots(figsize=(11.0, 6.0))
    _style(ax, "validate.py: eleven model outputs against published bands",
           "position inside the band (0 = low edge, 1 = high edge)", None)
    y = np.arange(len(Lr))[::-1]
    ax.axvspan(0, 1, color="#eef3fb", zorder=1)
    for yi, r in zip(y, Lr):
        span = (r["hi"] - r["lo"]) or 1.0
        pos = (r["value"] - r["lo"]) / span
        col = SIM if r["ok"] else CRIT
        ax.scatter([np.clip(pos, -0.6, 1.6)], [yi], s=90, color=col, zorder=4,
                   edgecolor=SURFACE, lw=1.5, marker="o" if r["ok"] else "X")
        ax.annotate(f"{r['value']:.1f} {r['unit']}   band {r['lo']:g}-{r['hi']:g}",
                    xy=(np.clip(pos, -0.6, 1.6), yi), xytext=(10, 0),
                    textcoords="offset points", va="center", fontsize=8.5,
                    color=INK if r["ok"] else CRIT)
    ax.set_yticks(y, [r["name"] for r in Lr])
    ax.set_xlim(-0.7, 2.5)
    ax.axvline(0, color=INK3, lw=0.8)
    ax.axvline(1, color=INK3, lw=0.8)
    ax.text(0, -0.13,
            f"{sum(r['ok'] for r in Lr)} of {len(Lr)} inside. These are PUBLISHED "
            "RANGES, not measurements from this car, and REFERENCES.md records "
            "which of them are sourced.",
            transform=ax.transAxes, color=INK2, fontsize=8.5)
    _save(fig, "fig18_literature_bands.png")


if __name__ == "__main__":
    print("writing figures to results/figures/")
    traces()
    sweep()
    curves()
    phase_d()
    model_vs_data()
    print("done")
