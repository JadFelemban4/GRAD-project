"""analyse_c4.py — the test results/PREREGISTRATION_C4.md names, and only that.

    python analyse_c4.py

Reads `results/c4_seed<N>.txt` (N = 0-7), `results/c4_convergence.txt`,
`results/c4_tracking.txt` and `results/c4_identity.txt`, applies the
preregistered statistic, and prints the result beside Phase D2's and Phase D's
-- beside, never pooled with.

COMMITTED BEFORE ANY OF THE SIXTEEN C4 AGENTS WAS TRAINED, in the commit before
the preregistration, as `analyse_phase_d2.py` was for D2. The analysis is fixed
while the answer is unknown.

THE STATISTIC IS D2's, IMPORTED, NOT COPIED
-------------------------------------------
`classify()` and the minimum effect of interest come from `analyse_phase_d2`,
which takes its sign and permutation tests from `analyse_phase_d`. Three
experiments, one piece of arithmetic:

    primary outcome   per-seed median damage over the twenty frozen D2 episodes
    comparison        paired by seed, blind minus sighted; positive = preview
                      helped
    test              exact one-sided sign test, alpha 0.05
    sensitivity       exact paired permutation test on the same differences
    MEI               50 damage units, and D2's three-cell rule:
                      PREVIEW HELPS / SMALLER THAN THE MEI / INCONCLUSIVE

WHAT IS NEW
-----------
1. IT REFUSES A RESULT WHOSE AGENTS ARE NOT C4 AGENTS. The plant fingerprint
   cannot tell a C4 agent from a D2 one, and a resume never rewrites
   meta.json. So each result file must carry, for exactly its two agents, the
   line `evaluate.py` reads out of the zip itself -- trained 300 000 of
   300 000, from step 0, 300 000-slot buffer -- and those two lines must be
   the agents whose damage rows are in the same file. A file stamped by
   `evaluate.py` as a forced fingerprint mismatch is refused. Where a zip is
   still on this machine it must be readable and its hash must match the one
   scored; `runs_c4/` is gitignored, so on a teammate's clone the record in
   the result file is what certifies it, and the output says so.
2. IT TESTS ONLY THE PREREGISTERED SET: results/c4_seed0.txt ... c4_seed7.txt,
   all eight, each complete. Any other file matching c4_seed* is refused, and
   fewer than eight is printed as INTERIM, with no reading and a non-zero exit.
3. IT READS THE CONVERGENCE VERDICT only if it is about these agents -- the
   per-agent hashes in `results/c4_convergence.txt` must equal the hashes
   certified here -- and prints the reading the preregistration declared for
   that cell and verdict (section 2a), verbatim.
4. IT TESTS WHETHER THE BUDGET CHANGED PREVIEW'S EFFECT (section 5c), because
   "significant at 300 000, not significant at 50 000" is not itself a test.
   Per seed: (blind - sighted at C4) minus (blind - sighted at D2), exact
   one-sided sign test, permutation beside it. A C4 separation is attributed
   to the budget only if this rejects.
5. IT MAKES NO PREDICTION ABOUT THE SPREAD, and prints C4's beside D2's and
   Phase D's.

WHAT IT DELIBERATELY DOES NOT DO: drop, add or swap a seed; pool C4 with D2 or
Phase D (they share seeds and -- if `check_c4_start.py` found them identical
-- their first 50 000 steps); switch tails; pick a checkpoint; or read "the
agent beats current-grade" as "preview helps" (AUDIT.md C3).
"""
import glob
import os
import re
import sys
from statistics import median, stdev

import fingerprint as FP
from analyse_phase_d import ALPHA, parse, perm_test, sign_test
from analyse_phase_d2 import MEI, classify, load
from power_analysis import delta_for_power

HERE = os.path.dirname(os.path.abspath(__file__))
C4_STEPS = 300_000
SEEDS = tuple(range(8))
NEED = ("baseline ECU", "current-grade", "agent", "agent (blind)")

# results/PREREGISTRATION_C4.md section 3 -- the values D2 pinned, unchanged.
PINS = {"plant_sha": "b5a3069f32a83754", "episodes_sha": "1c5d49852290d27c",
        "road_sha": "1a29dc46db24f233"}
PROTOCOL = {"eval_dt": "1", "eval_duration": "720", "n_episodes": "20"}

OFF_MACHINE = "final.zip not on this machine"

BUDGET = re.compile(r"^model (.+?): trained (\d+) steps of (\d+) requested, "
                    r"from step (\d+), buffer (\d+), zip sha ([0-9a-f]{16})\s*$")

# What each (cell, convergence) outcome MEANS for the two explanations still
# standing after D2 -- (i) preview buys little here, (ii) the C1 budget.
# Declared in results/PREREGISTRATION_C4.md section 2a before any of the
# sixteen C4 agents trained; printed verbatim so the reading cannot drift from
# the declaration. The review of the draft rewrote four of them: a C4
# separation does not by itself show the budget was the cause (D2 was
# INCONCLUSIVE, not a shown absence), and an INCONCLUSIVE C4 at eight seeds
# weakens (ii) only for effects about as large as eight seeds can detect.
READING = {
    ("PREVIEW HELPS", "CONVERGED"):
        "Preview helps at 300 000 steps, with agents that had settled. At\n"
        "50 000 steps (Phase D2, same seeds and roads) the test was\n"
        "INCONCLUSIVE at power 0.24 against the MEI -- not a shown absence. So\n"
        "the contrast is CONSISTENT with (ii), the budget, and is attributed to\n"
        "it only if the paired budget-change test (section 5c) rejects. Whether\n"
        "preview is WORTH acquiring is the effect size against the MEI.",
    ("PREVIEW HELPS", "NOT-CONVERGED"):
        "Preview helps at 300 000 steps; report it as 'at 300 000 steps'.\n"
        "Consistent with (ii), and attributed to it only if the paired\n"
        "budget-change test rejects (section 5c). The agents were still\n"
        "changing, so the size of the effect at convergence is not known.",
    ("SMALLER THAN THE MEI", "CONVERGED"):
        "With agents that had settled, preview's effect is shown to be below\n"
        "the team's threshold. A positive finding for (i) at this\n"
        "configuration: preview buys little here. (ii) is not supported up to\n"
        "300 000 steps (limit 2).",
    ("SMALLER THAN THE MEI", "NOT-CONVERGED"):
        "Preview's effect is below the MEI at 300 000 steps: (i) is supported\n"
        "AT THIS BUDGET. The agents were still changing, so (ii) is not ruled\n"
        "out.",
    ("INCONCLUSIVE", "CONVERGED"):
        "The arms do not separate, and the agents had settled, so undertraining\n"
        "is no longer needed to explain the null at this budget. But eight\n"
        "seeds rule out only effects about as large as the one printed below\n"
        "(80 % power at C4's own spread); for effects near the MEI this outcome\n"
        "is about as likely with (ii) true as false. The next experiment is\n"
        "more seeds, planned from C4's spread, with its own preregistration.\n"
        "Still NOT 'preview does not help'.",
    ("INCONCLUSIVE", "NOT-CONVERGED"):
        "Nothing is resolved. The arms do not separate and the agents were\n"
        "still changing: (i) and (ii) both stand. The next experiment -- a\n"
        "longer budget or more seeds, one variable at a time relative to C4 --\n"
        "is the team's decision.",
}

# Section 5: D2's rule, restored -- a significant result in the other
# direction is reported as preview costing damage. classify() files such a
# result under SMALLER THAN THE MEI (every difference is below 50), and this
# replaces that cell's reading, which would otherwise call it evidence for (i).
COSTS = ("PREVIEW COSTS DAMAGE at 300 000 steps: the sighted agents took\n"
         "significantly more damage than their blind twins. That is a finding\n"
         "about this learner at this budget, reported as preview costing damage,\n"
         "never as a two-sided win -- and it is NOT evidence for (i).")


def lines_of(path):
    with open(path, encoding="utf-8") as fh:
        return [ln.rstrip("\n") for ln in fh]


def fingerprint_block(lines):
    """Field -> value, from the '(this run)' block only."""
    out, inside = {}, False
    for ln in lines:
        if ln.startswith("--- PLANT FINGERPRINT (this run)"):
            inside = True
            continue
        if inside and ln.startswith("-" * 20):
            break
        if inside:
            m = re.match(r"^\s+(\S+)\s+(.*)$", ln)
            if m:
                out[m.group(1)] = m.group(2).strip()
    return out


def certify(path, seed):
    """(problems, notes, shas) for one C4 result file."""
    lines = lines_of(path)
    bad, notes, shas = [], [], {}
    if not lines or not lines[0].startswith("C4 EVALUATION"):
        bad.append(f"title is {lines[0][:50]!r} -- not a C4 evaluation" if lines
                   else "empty file")
    fp = fingerprint_block(lines)
    road = re.search(r"road_sha=([0-9a-f]{16})", fp.get("scenario", ""))
    got = dict(fp, road_sha=road.group(1) if road else None)
    for k, want in list(PINS.items()) + list(PROTOCOL.items()):
        if got.get(k) != want:
            bad.append(f"{k} is {got.get(k)!r}; the preregistration pins {want}")
    if fp.get("git_dirty") != "False":
        notes.append(f"scored from a tree with git_dirty {fp.get('git_dirty')}")
    for ln in lines:
        if ln.startswith("!!") or "PLANT MISMATCH" in ln or "--force-plant-mismatch" in ln:
            bad.append(f"evaluate.py flagged the provenance: {ln.strip()[:70]}")
    budgets = {}
    for ln in lines:
        m = BUDGET.match(ln)
        if m:
            mdir, n, tot, start, buf, sha = m.groups()
            tag = os.path.basename(os.path.normpath(mdir.replace("\\", "/")))
            budgets[tag] = (mdir, (int(n), int(tot), int(start), int(buf)), sha)
    want = {f"sighted_seed{seed}", f"blind_seed{seed}"}
    if set(budgets) != want or sum(1 for ln in lines if BUDGET.match(ln)) != 2:
        bad.append(f"budget records name {sorted(budgets)}; exactly {sorted(want)} "
                   "are required")
    # The damage rows must be THOSE agents': one 'agent' row and one
    # 'agent (blind)' row, each naming the directory its budget line names.
    rows = {"agent": [], "agent (blind)": []}
    for ln in lines:
        for lab in ("agent (blind) ", "agent "):
            if ln.startswith(lab):
                rows[lab.strip()].append(ln[len(lab):].split()[0])
                break
    for lab, arm in (("agent", "sighted"), ("agent (blind)", "blind")):
        tag = f"{arm}_seed{seed}"
        if len(rows[lab]) != 1:
            bad.append(f"{len(rows[lab])} '{lab}' rows; exactly one is required")
        elif tag in budgets and rows[lab][0] != budgets[tag][0]:
            bad.append(f"the '{lab}' row scored {rows[lab][0]}, the budget line "
                       f"certifies {budgets[tag][0]}")
    for tag, (mdir, counts, sha) in budgets.items():
        if counts != (C4_STEPS, C4_STEPS, 0, C4_STEPS):
            bad.append(f"{tag}: trained {counts[0]} of {counts[1]}, from step "
                       f"{counts[2]}, buffer {counts[3]} -- not a fresh "
                       f"{C4_STEPS:,}-step run")
        shas[tag] = sha
        z = os.path.join(HERE, mdir.replace("\\", "/"), "final.zip")
        if not os.path.exists(z):
            notes.append(OFF_MACHINE)
            continue
        live = FP.model_budget(z)
        if live is None:
            bad.append(f"{tag}: the final.zip on disk is unreadable -- not the "
                       "artefact that was scored")
        elif live["sha"] != sha:
            bad.append(f"{tag}: the final.zip on disk (sha {live['sha']}) is NOT "
                       f"the one that was scored (sha {sha})")
    return bad, notes, shas


def collect():
    """The preregistered set, or the reasons it is not there."""
    problems, rows, incomplete = [], [], []
    for f in sorted(glob.glob(os.path.join(HERE, "results", "c4_seed*.txt"))):
        if not re.match(r"c4_seed[0-7]\.txt$", os.path.basename(f)):
            problems.append(f"{os.path.basename(f)} is not one of c4_seed0-7.txt "
                            "-- move it out of results/ before testing")
    for s in SEEDS:
        f = os.path.join(HERE, "results", f"c4_seed{s}.txt")
        if not os.path.exists(f):
            incomplete.append(s)
            continue
        d = parse(f)
        if not all(k in d for k in NEED):
            incomplete.append(s)
            continue
        rows.append((s, d, d["agent (blind)"] - d["agent"], f))
    return rows, incomplete, problems


def read_verdict(certified_shas):
    """(label, detail) or (None, why) from results/c4_convergence.txt."""
    p = os.path.join(HERE, "results", "c4_convergence.txt")
    if not os.path.exists(p):
        return None, "results/c4_convergence.txt does not exist"
    shas, verdict = {}, None
    for ln in lines_of(p):
        m = re.match(r"^AGENT (\S+) final\.zip sha (\S+)$", ln)
        if m:
            shas[m.group(1)] = m.group(2)
        if ln.startswith("VERDICT "):
            verdict = ln
    if verdict is None:
        return None, "no VERDICT line"
    label = verdict.split()[1]
    if label not in ("CONVERGED", "NOT-CONVERGED"):
        return None, f"unrecognised VERDICT label {label!r}"
    if "BUDGET-MISMATCH" in verdict:
        return None, "the convergence check found an agent that is not a fresh C4 run"
    if not verdict.rstrip().endswith("runs runs_c4"):
        return None, "the verdict is not about runs_c4/"
    if shas != certified_shas:
        return None, ("the verdict was computed on different final.zip files "
                      "from the ones certified in the result files")
    return label, verdict[len("VERDICT "):]


def read_tracking():
    """(flagged sighted tags, {seed: sighted-minus-blind tracking gap}) or None."""
    p = os.path.join(HERE, "results", "c4_tracking.txt")
    if not os.path.exists(p):
        return None
    flagged, gap = [], {}
    for ln in lines_of(p):
        m = re.match(r"^FLAGGED (\S+)$", ln)
        if m:
            flagged.append(m.group(1))
        m = re.match(r"^GAP seed(\d) ([+-][\d.]+)$", ln)
        if m:
            gap[int(m.group(1))] = float(m.group(2))
    return flagged, gap


def read_identity():
    p = os.path.join(HERE, "results", "c4_identity.txt")
    if not os.path.exists(p):
        return None
    for ln in lines_of(p):
        m = re.match(r"^IDENTITY compared (\d+) identical (\d+)$", ln)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None


def sd(xs):
    return stdev(xs) if len(xs) > 1 else float("nan")


def main():
    rows, incomplete, problems = collect()
    d2_rows, _ = load("d2")
    pd_rows, _ = load("phase_d")

    print("=" * 78)
    print("C4 -- the preregistered test: Phase D2's design at 300 000 steps")
    print("results/PREREGISTRATION_C4.md, committed before any C4 agent was trained")
    print("=" * 78)
    print()

    # ---- 1. is every scored agent a C4 agent, and is the set complete? ------
    notes, shas = [], {}
    for s, _, _, f in rows:
        b, n, sh = certify(f, s)
        problems += [f"seed {s}: {x}" for x in b]
        notes += [x if x == OFF_MACHINE else f"seed {s}: {x}" for x in n]
        shas.update(sh)
    off = notes.count(OFF_MACHINE)
    if off:
        print(f"  note  {off} of {2 * len(rows)} agents' final.zip are not on this "
              "machine (runs_c4/ is gitignored):")
        print("        certified from the record evaluate.py read out of each zip")
    for x in notes:
        if x != OFF_MACHINE:
            print(f"  note  {x}")
    if problems:
        for x in problems:
            print(f"  !!    {x}")
        print("\nREFUSING to test: the files are not the certified, preregistered")
        print("C4 set. Nothing below this line was computed.")
        return 1
    if not rows:
        print("  no results/c4_seed*.txt yet -- see PREREGISTRATION_C4.md section 9")
        return 1
    interim = bool(incomplete)
    print(f"  certified: {2 * len(rows)} agents, each a fresh {C4_STEPS:,}-step run "
          "on the pinned plant, road, episodes and protocol")
    if interim:
        print(f"\n  INTERIM -- seeds {incomplete} are missing or incomplete. The")
        print("  preregistered test is on all eight. What follows is NOT the result,")
        print("  no reading is printed, and this exits non-zero.")
    print()

    # ---- 2. the table and the test -----------------------------------------
    diffs = [r[2] for r in rows]
    print(f"{'seed':>5}{'baseline':>11}{'curr-grade':>12}"
          f"{'sighted':>10}{'blinded':>10}{'blind-sighted':>15}")
    print("-" * 78)
    for s, d, diff, _ in rows:
        print(f"{s:>5}{d['baseline ECU']:>11.1f}{d['current-grade']:>12.1f}"
              f"{d['agent']:>10.1f}{d['agent (blind)']:>10.1f}{diff:>+15.1f}")
    print("-" * 78)
    if len(diffs) < 2:
        print("  too few complete seeds to test")
        return 1
    cell, x = classify(diffs)
    c4_sd = sd(diffs)
    print(f"paired differences (blind - sighted), n = {len(diffs)}")
    print(f"  positive (preview helped) : {x['k']} of {x['n']}")
    print(f"  mean difference           : {x['mean']:+.1f} damage units")
    print(f"  median difference         : {median(diffs):+.1f}   seeds at or above "
          f"the MEI ({MEI:.0f}): {sum(d >= MEI for d in diffs)} of {len(diffs)}"
          "   (descriptive)")
    print(f"  sd of the differences     : {c4_sd:.1f}   (D2: {sd([r[2] for r in d2_rows]):.1f},"
          f" Phase D: {sd([r[2] for r in pd_rows]):.1f}) -- no direction was predicted")
    print()
    print("  H1: preview helps (difference > 0)")
    print(f"    exact one-sided sign test        p = {x['p_sign']:.4f}")
    print(f"    exact paired permutation test    p = {x['p_perm']:.4f}   (sensitivity)")
    print(f"  H1: the effect is smaller than the MEI ({MEI:.0f} units)")
    print(f"    exact one-sided sign test        p = {x['p_lt_sign']:.4f}"
          f"   ({x['k_lt']} of {x['n_lt']} seeds below {MEI:.0f})")
    print(f"    exact paired permutation test    p = {x['p_lt_perm']:.4f}   (sensitivity)")
    k_neg, n_neg, p_neg = sign_test([-d for d in diffs])
    costs = p_neg < ALPHA
    print(f"  the other direction, preview COSTS damage: sign test p = {p_neg:.4f}"
          f"   ({k_neg} of {n_neg} seeds)")
    print(f"  alpha {ALPHA}, one-sided")
    if (x["p_sign"] < ALPHA) != (x["p_perm"] < ALPHA):
        print("  THE TWO TESTS DISAGREE on 'preview helps'. Both reported; the sign")
        print("  test is primary; neither is chosen after the fact.")
    if (x["p_lt_sign"] < ALPHA) != (x["p_lt_perm"] < ALPHA):
        print("  THE TWO TESTS DISAGREE on 'smaller than the MEI'. Both reported;")
        print("  the sign test is primary.")

    # ---- 2b. section 5c: did the BUDGET change preview's effect? -----------
    d2_by = {s: (d, diff) for s, d, diff in d2_rows}
    change = [diff - d2_by[s][1] for s, _, diff, _ in rows if s in d2_by]
    k_ch, n_ch, p_ch = sign_test(change)
    p_ch_perm = perm_test(change) if change else 1.0
    budget_shown = p_ch < ALPHA
    print()
    print("  SECTION 5c -- did preview's effect GROW from 50 000 to 300 000 steps?")
    print("  per seed: (blind - sighted at C4) minus (blind - sighted at D2)")
    print("    " + "  ".join(f"s{s} {c:+.1f}" for (s, *_), c in zip(rows, change)))
    print(f"    exact one-sided sign test        p = {p_ch:.4f}   ({k_ch} of {n_ch} grew)")
    print(f"    exact paired permutation test    p = {p_ch_perm:.4f}   (sensitivity)")

    print()
    print(f"  RESULT: {cell}" + ("   [INTERIM -- not the preregistered result]"
                                  if interim else ""))
    if cell == "PREVIEW HELPS":
        reach = "reaches" if x["mean"] >= MEI else "does NOT reach"
        print(f"  The mean effect {reach} the minimum of interest ({MEI:.0f}).")
    if x["mean"] < 0:
        print("  The mean difference is NEGATIVE: the sighted agents took MORE")
        print("  damage than the blinded ones. Reported as what it is.")
    print("  This is the THIRD preregistered look at the preview question on these")
    print("  seeds (Phase D sign p 0.3633, Phase D2 0.6367); every p here is")
    print("  unadjusted, and the three are reported together.")
    if interim:
        return 1

    # ---- 3. the reading declared in advance, and what qualifies it ---------
    label, detail = read_verdict(shas)
    print()
    print("CONVERGENCE (PREREGISTRATION_C4.md section 5b)")
    if label is None:
        print(f"  NOT JUDGED: {detail}. Both readings of the cell are printed, marked")
        print("  CONDITIONAL, and the reason goes in section 6a.")
    else:
        print(f"  {detail}")
    print()
    print("THE READING, as declared before any C4 agent trained (section 2a):")
    for conv in ((label,) if label else ("CONVERGED", "NOT-CONVERGED")):
        if not label:
            print(f"  if {conv}:")
        text = COSTS if (costs and cell == "SMALLER THAN THE MEI") else READING[(cell, conv)]
        print("  " + text.replace("\n", "\n  "))
    if costs and cell != "SMALLER THAN THE MEI":
        print("  " + COSTS.replace("\n", "\n  "))
    if cell == "INCONCLUSIVE":
        d80 = delta_for_power(0.80, c4_sd, len(diffs))
        print(f"  At C4's spread (sd {c4_sd:.1f}) eight seeds had 80 % power only against")
        print(f"  an effect of about {d80:.0f} damage units.")
    if cell == "PREVIEW HELPS":
        print("  Section 5c: " + (
            f"the paired budget-change test REJECTS (p {p_ch:.4f}) -- the budget "
            "increased preview's effect." if budget_shown else
            f"the paired budget-change test does NOT reject (p {p_ch:.4f}) -- that "
            "preview helps MORE at 300 000 than at 50 000 steps is not shown."))
        idn = read_identity()
        if idn is None or idn[0] == 0 or idn[0] != idn[1]:
            print("  (Budget isolation not confirmed: results/c4_identity.txt is "
                  + ("missing." if idn is None else
                     f"{idn[1]} of {idn[0]} checkpoints identical to D2.") + ")")
        tr = read_tracking()
        if tr is None:
            print("  LIMIT 10 NOT YET CHECKED -- results/c4_tracking.txt is missing,")
            print("  so this reading is PROVISIONAL (python check_d2_tracking.py")
            print("  runs_c4 --out results/c4_tracking.txt).")
        else:
            flagged, gap = tr
            bought = [t for t in flagged if t.startswith("sighted")] + [
                f"seed {s}" for s, _, diff, _ in rows if diff > 0 and gap.get(s, 0) > 1.0]
            if bought:
                print("  LIMIT 10: damage PARTLY BOUGHT WITH TORQUE -- not established as")
                print(f"  protection ({', '.join(bought)}).")
            else:
                print("  Limit 10: no sighted agent refuses torque, and no positive seed's")
                print("  sighted agent tracks more than 1 point worse than its blind twin.")

    # ---- 4. beside, never pooled -------------------------------------------
    print()
    print("=" * 78)
    print("THE THREE EXPERIMENTS, ONE LINE EACH -- beside, never pooled")
    print("=" * 78)
    for name, dd, note in (
            ("Phase D ", [r[2] for r in pd_rows], "fixed climb, blind arm NOT blind, C1  "),
            ("Phase D2", [r[2] for r in d2_rows], "random climb, blind checked, C1       "),
            ("C4      ", diffs, "random climb, D2's design, 300 000 st.")):
        if len(dd) >= 2:
            c, y = classify(dd)
            print(f"  {name}  {note}  {y['k']} of {y['n']}  mean {y['mean']:+6.1f}  "
                  f"sd {sd(dd):5.1f}  {c}")
    print("  (Phase D's MEI cell is post-hoc: its MEI was set after its result.)")

    # ---- 5. what longer training did to each agent -- DESCRIPTIVE ----------
    print()
    print("  C4 minus D2 median damage, per seed and arm -- DESCRIPTIVE, no test.")
    print("  Negative = the longer-trained agent took less damage.")
    for s, d, _, _ in rows:
        if s in d2_by:
            b2 = d2_by[s][0]
            print(f"    seed {s}: sighted {d['agent'] - b2['agent']:+7.1f}"
                  f"   blinded {d['agent (blind)'] - b2['agent (blind)']:+7.1f}")

    # ---- 6. supervision, the SEPARATE claim --------------------------------
    print()
    print("  Preview must beat CURRENT-GRADE, not the baseline ECU. Per C4 seed:")
    for s, d, _, _ in rows:
        b = d["baseline ECU"]
        edge = 100 * (1 - d["agent"] / b) - 100 * (1 - d["current-grade"] / b)
        edge_b = 100 * (1 - d["agent (blind)"] / b) - 100 * (1 - d["current-grade"] / b)
        print(f"    seed {s}: sighted over current-grade {edge:+6.1f} points,"
              f" blinded {edge_b:+6.1f}")
    print("  That is learned SUPERVISION, a separate claim from preview")
    print("  (AUDIT.md C3). Do not read one as evidence for the other.")
    return 0 if label else 1


if __name__ == "__main__":
    sys.exit(main())
