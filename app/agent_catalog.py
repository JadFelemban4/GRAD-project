"""Which trained agents the replay page may run, and what results/ says of them.

READ-ONLY. This module opens meta.json, final.zip and files under results/
for reading and nothing else: no training, no evaluation, no file written, no
directory created. Names from a request are matched against two patterns
before any path is built from them, so a request can never choose a path.

The status of an agent is decided in the order of design section 4:
training, then no meta.json, then no final.zip, then evaluate.py's own arm
rule, then the protocol, then the fatal fingerprint fields. A pair runs only
when both arms are ready AND each final.zip is the one results/ recorded as
scored, where results/ records one (only C4 does today).

Verdicts are QUOTED, never computed: each anchor is a pattern searched in a
file under results/, returned with its line number so the page can cite it as
results/<file>:<line>. The short line and the glosses are authored text, and
the short line is shown only when every anchor it summarises was found.
The tables carry the c4, d2 and phase_d rows, keyed by result prefix; a
prefix with no row (a future runs_X) has the verdict state 'none'.
"""
from __future__ import annotations

from collections import namedtuple
import os
from pathlib import Path
import re
import threading
import time
import warnings

import fingerprint as FP
import run_phase_d as RPD
from analyse_c4 import BUDGET
from evaluate import DT, DURATION

ROOT = Path(__file__).resolve().parent.parent
# Lowercase only: NTFS is case-insensitive, so "runs_C4" would otherwise
# resolve to the same directory as "runs_c4" while carrying no verdict --
# the sixteen real C4 agents (eight pairs) would come back ready with no C4
# caveats attached.
RUNS_NAME = re.compile(r"^runs[a-z0-9_]*$")
AGENT_NAME = re.compile(r"^(sighted|blind)_seed(\d+)$")
ARMS = ("sighted", "blind")
UNREADABLE_ZIP = "final.zip is not a readable stable-baselines3 zip"


class Refused(Exception):
    """A pair that must not run. `problems` says why, one line per reason."""

    def __init__(self, problems):
        self.problems = [str(p) for p in problems]
        super().__init__("; ".join(self.problems))


_FINGERPRINTS = {}
FINGERPRINT_TAKEN = {}
_FINGERPRINT_LOCK = threading.Lock()


def live_fingerprint(protocol):
    """The live plant fingerprint for 'phase-d' or 'd2', taken once and cached.

    plant_fingerprint runs `git status`, which may rewrite .git/index unless
    GIT_OPTIONAL_LOCKS is 0, so that is set before the first call, here
    rather than in install(), so that tests calling this module directly are
    covered too. Restart the server after changing a hashed file.
    """
    os.environ.setdefault("GIT_OPTIONAL_LOCKS", "0")
    with _FINGERPRINT_LOCK:
        if protocol not in _FINGERPRINTS:
            _FINGERPRINTS[protocol] = FP.plant_fingerprint(
                protocol=protocol, eval_dt=DT, eval_duration=DURATION)
            FINGERPRINT_TAKEN[protocol] = time.strftime("%H:%M")
        return _FINGERPRINTS[protocol]


def protocol_of(meta):
    """'phase-d' when meta.scenario has no protocol, 'd2' for random-climb,
    None for anything else (refused as an unknown protocol)."""
    scenario = meta.get("scenario") or {}
    if "protocol" not in scenario:
        return "phase-d"
    if scenario["protocol"] == "random-climb":
        return "d2"
    return None


def read_agent(runs, name, root=ROOT):
    """One agent directory's status. KeyError if either name is malformed or
    the directory is not there: a missing directory is not an agent at all."""
    m = AGENT_NAME.fullmatch(str(name))
    if not RUNS_NAME.fullmatch(str(runs)) or m is None:
        raise KeyError(f"{runs}/{name}")
    arm, seed = m.group(1), int(m.group(2))
    d = Path(root) / runs / name
    if not d.is_dir():
        raise KeyError(f"{runs}/{name}")
    out = {"runs": runs, "tag": name, "arm": arm, "seed": seed, "status": None,
           "reason": None, "problems": [], "protocol": None, "budget": None,
           "budget_line": None, "zip_sha": None, "train_dt": None}

    if FP.running_pid(str(d)) is not None:
        return dict(out, status="training", reason="training now")
    meta = FP.read(str(d / "meta.json"))
    if meta is None:
        return dict(out, status="incompatible",
                    reason="no meta.json: plant unknown (AUDIT2 C2-1)")
    if not (d / "final.zip").is_file():
        return dict(out, status="incomplete", reason="no final.zip")
    # evaluate.py:369 decides the arm by "blind" in the path string that
    # run_phase_d.py:330 hands it, os.path.join(out, tag) -- a backslash on
    # Windows. "blind" in a path gives the same answer for either separator,
    # so f"{runs}/{name}" applies that exact rule here.
    scored_blind = "blind" in f"{runs}/{name}"
    if scored_blind != (arm == "blind") or scored_blind != (not meta.get("use_preview", True)):
        return dict(out, status="incompatible",
                    reason="evaluate.py would have scored this agent as the other arm")
    protocol = protocol_of(meta)
    if protocol is None:
        return dict(out, status="incompatible", reason="unknown protocol")
    bad = FP.compare(meta, live_fingerprint(protocol))
    if bad:
        return dict(out, status="incompatible", protocol=protocol,
                    reason="plant mismatch: " + ", ".join(f for f, _, _ in bad),
                    problems=[f"{f}: stored {a!r} live {b!r}" for f, a, b in bad])
    budget = FP.model_budget(str(d / "final.zip"))
    if budget is None:
        # Not an SB3 zip (FP.model_budget reads its 'data' member). M1 called
        # it ready with 'budget unreadable' and let SAC.load fail at build time.
        return dict(out, status="incomplete", reason=UNREADABLE_ZIP, protocol=protocol,
                    train_dt=meta.get("train_dt"))
    return dict(out, status="ready", protocol=protocol, budget=budget,
                budget_line=FP.format_budget(budget), zip_sha=budget["sha"],
                train_dt=meta.get("train_dt"))


def scored_shas(prefix, seed, root=ROOT):
    """The zip sha results/<prefix>_seed<seed>.txt recorded per arm, or None
    when there is no such file. evaluate.py wrote the model path with the
    platform separator (runs_c4\\sighted_seed0 on this machine), so the path
    is normalised to '/' before its last component is compared."""
    path = Path(root) / "results" / f"{prefix}_seed{seed}.txt"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return None
    out = {arm: None for arm in ARMS}
    for line in lines:
        m = BUDGET.match(line)
        if m is None:
            continue
        base = m.group(1).replace("\\", "/").rstrip("/").rsplit("/", 1)[-1]
        for arm in ARMS:
            if base == f"{arm}_seed{seed}":
                out[arm] = m.group(6)
    return out


def _agent_problems(agent):
    """One agent's lines in a pair's problem list: '<tag>: <status> --
    <reason>', then '<tag>: <line>' for each of its own problems (a plant
    mismatch's stored and live fields). [] for a ready agent. check_pair and
    discover both build a pair's list from it, so every line of both arms
    reaches the catalog in one format."""
    if agent["status"] == "ready":
        return []
    return ([f"{agent['tag']}: {agent['status']} -- {agent['reason']}"]
            + [f"{agent['tag']}: {p}" for p in agent["problems"]])


def check_pair(runs, seed, root=ROOT):
    """The sighted and blind agent of one seed, checked, with the problems
    RETURNED rather than raised: the catalog lists a refused pair with its
    reason, and find_pair raises on the same list, so both share one rule.

    KeyError for a name that is malformed or an arm directory not on disk.
    Otherwise 'problems' is [] when the pair may run. 'protocol' is the arms'
    shared protocol once both are ready and agree, else None. Each agent
    gains 'scored' once the sha check has run: 'match', 'mismatch' (results/
    records a different sha; the pair is refused) or 'not recorded'. It is
    None when an earlier check refused the pair first.
    """
    if (not RUNS_NAME.fullmatch(str(runs)) or not isinstance(seed, int)
            or isinstance(seed, bool) or seed < 0):
        raise KeyError(f"{runs}/{seed}")
    root = Path(root)
    if not all((root / runs / f"{arm}_seed{seed}").is_dir() for arm in ARMS):
        raise KeyError(f"{runs}/{seed}")
    agents = [dict(read_agent(runs, f"{arm}_seed{seed}", root), scored=None) for arm in ARMS]
    prefix = RPD.result_prefix(str(root / runs))
    pair = {"runs": runs, "seed": seed, "prefix": prefix,
            "experiment": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "protocol": None,
            "result_file": (root / "results" / f"{prefix}_seed{seed}.txt").is_file(),
            "agents": agents, "problems": []}
    problems = [line for a in agents for line in _agent_problems(a)]
    if problems:
        return dict(pair, problems=problems)
    if agents[0]["protocol"] != agents[1]["protocol"]:
        return dict(pair, problems=[f"the two arms were trained on different protocols: "
                                    f"{agents[0]['protocol']} and {agents[1]['protocol']}"])
    shas = scored_shas(prefix, seed, root)
    for a in agents:
        recorded = None if shas is None else shas[a["arm"]]
        if recorded is None:
            a["scored"] = "not recorded"
        elif recorded == a["zip_sha"]:
            a["scored"] = "match"
        else:
            a["scored"] = "mismatch"
            problems.append(f"{a['tag']}: not the scored artefact -- results/{prefix}_seed{seed}.txt "
                            f"records zip sha {recorded}, final.zip is {a['zip_sha']}")
    return dict(pair, protocol=agents[0]["protocol"], problems=problems)


def find_pair(runs, seed, root=ROOT):
    """check_pair, raising Refused(problems) for a pair that must not run.
    KeyError for a name that is malformed or not on disk."""
    pair = check_pair(runs, seed, root)
    if pair["problems"]:
        raise Refused(pair["problems"])
    return pair


# ---- verdicts: quoted from results/, cited by line --------------------------
Anchor = namedtuple("Anchor", "key file pattern n")

VERDICT_LINES = {
    "c4": (
        Anchor("result", "C4_RESULT.txt", r"^\s*RESULT: SMALLER THAN THE MEI\s*$", 1),
        # The heading and both tests under it: the sign test's p is never
        # shown alone, and never without the permutation test's p.
        Anchor("seeds", "C4_RESULT.txt",
               r"^\s*H1: the effect is smaller than the MEI \(50 units\)\s*$", 3),
        Anchor("disagree", "C4_RESULT.txt", r"^\s*THE TWO TESTS DISAGREE", 2),
        Anchor("convergence", "C4_RESULT.txt", r"^\s*NOT-CONVERGED ", 1),
        Anchor("reading", "C4_RESULT.txt", r"^THE READING, as declared", 4),
        Anchor("explanations", "PREREGISTRATION_C4.md", r"^\| \(i\) \|", 3),
        # Item 2 of section 11 WHOLE, through "...is not settled.**": a quote
        # cut before its caveat reads as selective quoting.
        Anchor("one_seed", "PREREGISTRATION_C4.md",
               r"^2\. \*\*It rests on the sign test's threshold", 11),
    ),
    "d2": (
        # :30-35 whole: the item ends on the prediction power_analysis.py made
        # BEFORE the experiment ran. The pattern ends at the line's end, so the
        # bracketed Phase D line (:65) can never be taken for it.
        Anchor("result", "PHASE_D2_RESULT.txt", r"^\s*RESULT: INCONCLUSIVE\s*$", 6),
        Anchor("c1", "PHASE_D2_RESULT.txt", r"^\s*Both are C1 agents", 4),
    ),
    "phase_d": (
        Anchor("result", "PHASE_D_RESULT.txt",
               r"^\s*RESULT: NOT SIGNIFICANT at alpha 0\.05\.\s*$", 6),
        Anchor("not_blind", "PHASE_D_RESULT.txt", r"^\s*AND THE BLINDED ARM IS NOT BLIND\.", 8),
        # Phase D under D2's MEI rule, :65-76 whole: the paragraph after the
        # blank line (:72-76) is what says the reading is post-hoc.
        Anchor("post_hoc", "PHASE_D2_RESULT.txt",
               r"^\s*RESULT: INCONCLUSIVE\s+\[MEI set AFTER this result", 12),
    ),
}

# The anchor key that carries each quoted cell, in display order. The cell
# names are authored: 'INCONCLUSIVE (post-hoc)' is PHASE_D2_RESULT.txt:65,
# whose own text is 'INCONCLUSIVE   [MEI set AFTER this result -- see below]'.
CELLS = {
    "c4": {"result": "SMALLER THAN THE MEI", "convergence": "NOT-CONVERGED"},
    "d2": {"result": "INCONCLUSIVE"},
    "phase_d": {"result": "NOT SIGNIFICANT", "post_hoc": "INCONCLUSIVE (post-hoc)"},
}

SHORT_VERDICT = {
    "c4": {
        "ar": "أصغر من الحد الأدنى المهم (50 وحدة) عند 300\u202f000 خطوة · بفارق بذرة واحدة "
              "· الاختباران لا يتفقان · لم يستقر التدريب",
        "en": "smaller than the MEI (50) at 300\u202f000 steps · one seed wide "
              "· the two tests disagree · not converged",
        "requires": ("result", "seeds", "disagree", "convergence"),
    },
    "d2": {
        "ar": "غير حاسم · وكلاء C1 \u200f(50\u202f000 خطوة)",
        "en": "inconclusive · C1 agents, 50\u202f000 steps",
        "requires": ("result", "c1"),
    },
    "phase_d": {
        "ar": 'غير دال إحصائياً · غير حاسم (قراءة لاحقة) · الذراع "العمياء" ليست عمياء · وكلاء C1',
        "en": 'not significant · inconclusive (post-hoc) · the "blind" arm is not blind · C1 agents',
        "requires": ("result", "not_blind", "post_hoc"),
    },
}

GLOSS = {
    "SMALLER THAN THE MEI": {
        "ar": "أثر الاستباق أقل من 50 وحدة ضرر، وهو حدّ اختاره الفريق مسبقاً، عند 300\u202f000 "
              "خطوة تدريب، على طريق فيه تغيّر واحد في الميل لكل حلقة. التدريب لم يستقر، "
              "والنتيجة معلّقة على بذرة واحدة: لو انقلبت بذرة واحدة لصارت غير حاسمة.",
        "en": "Preview's effect is below 50 damage units, a threshold the team set in advance, "
              "at 300\u202f000 training steps, on a road with one grade change per episode. "
              "Training had not settled, and the result hangs on one seed: if one seed "
              "flipped, it would be inconclusive.",
    },
    "NOT-CONVERGED": {"ar": "لم يستقر التدريب", "en": "Training had not settled"},
    # PHASE_D2_RESULT.txt:31-33, in the team's words.
    "INCONCLUSIVE": {
        "ar": 'غير حاسم: التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"',
        "en": 'Inconclusive: the experiment cannot tell "no effect" from '
              '"an effect the team cares about"',
    },
    "NOT SIGNIFICANT": {
        "ar": "غير دال إحصائياً، مع وكلاء بميزانية C1",
        "en": "Not statistically significant, with agents at the C1 budget",
    },
    # PHASE_D2_RESULT.txt:72-76: the MEI was set after Phase D's result.
    "INCONCLUSIVE (post-hoc)": {
        "ar": "غير حاسم، وهي قراءة لاحقة: الحد الأدنى المهم (50 وحدة) حُدِّد بعد أن عُرفت "
              "نتيجة Phase D، فهذا التصنيف لم يُسجَّل مسبقاً. "
              'التجربة لا تميّز بين "لا أثر" و"أثر يهمّ الفريق"',
        "en": "Inconclusive, and a post-hoc reading: the MEI (50 units) was set after "
              "Phase D's result was known, so this classification was not preregistered. "
              'The experiment cannot tell "no effect" from "an effect the team cares about"',
    },
}

# {files}: every missing file, as results/<file>, joined by ' · '.
MISSING_TEXT = {
    "ar": "لم يُعثر على سطر الحكم في {files}: لا تقرأ هؤلاء الوكلاء بدونه",
    "en": "verdict line not found in {files}: do not read these agents without it",
}
NONE_TEXT = {
    "ar": "لا يوجد حكم مسجَّل مسبقاً لهذه التجربة في results/. ما تعرضه هذه الصفحة ليس نتيجة.",
    "en": "No preregistered verdict for this experiment in results/. "
          "Nothing on this page is a result.",
}


def verdict(prefix, root=ROOT):
    """{state, lines, missing, short, cells} for one result prefix.

    state is 'found' when every anchor matched, 'missing' when a file or an
    anchor is gone, 'none' when the prefix has no row. Each line is
    {key, file, line (1-based), text (the n lines joined by newline)}.
    """
    anchors = VERDICT_LINES.get(prefix)
    if anchors is None:
        return {"state": "none", "lines": [], "missing": [], "short": dict(NONE_TEXT),
                "cells": []}
    texts, lines, missing = {}, [], []
    for a in anchors:
        if a.file not in texts:
            try:
                texts[a.file] = (Path(root) / "results" / a.file).read_text(
                    encoding="utf-8").splitlines()
            except OSError:
                texts[a.file] = None
        src = texts[a.file]
        rx = re.compile(a.pattern)
        hit = None if src is None else next(
            (i for i, line in enumerate(src) if rx.search(line)), None)
        if hit is None:
            missing.append(a.file)
            continue
        lines.append({"key": a.key, "file": a.file, "line": hit + 1,
                      "text": "\n".join(src[hit:hit + a.n])})
    missing = sorted(set(missing))
    found = {line["key"] for line in lines}
    authored = SHORT_VERDICT.get(prefix)
    if missing:
        files = " · ".join(f"results/{f}" for f in missing)
        short = {lang: MISSING_TEXT[lang].format(files=files) for lang in MISSING_TEXT}
    elif authored is not None and set(authored["requires"]) <= found:
        short = {lang: authored[lang] for lang in ("ar", "en")}
    else:
        short = None
    cells = [{"cell": cell, "gloss": dict(GLOSS[cell])}
             for key, cell in CELLS.get(prefix, {}).items() if key in found]
    return {"state": "missing" if missing else "found", "lines": lines,
            "missing": missing, "short": short, "cells": cells}


# ---- the catalog: every runs*/ experiment, every pair, for the picker --------
# What the page may show of each agent. 'budget' (the whole dict) stays here.
CATALOG_AGENT_KEYS = ("tag", "arm", "status", "reason", "problems", "budget_line",
                      "train_dt", "zip_sha", "scored")


def table_rows(prefix):
    """{'diffs': {seed: blind - sighted}, 'incomplete': [seed]} for one prefix.

    QUOTED from analyse_phase_d2.load(prefix), the analysis's own reader of
    the repository's results/<prefix>_seed<k>.txt, and rounded to the one
    decimal the printed tables show; nothing is recomputed here. An unknown
    prefix gives both empty. Imported here, not at the top, so that importing
    this module never loads the analysis scripts.

    analyse_phase_d.parse reads with `for line in open(path)`, leaving each
    file for CPython to close as soon as the loop ends; under unittest that
    prints a ResourceWarning per result file. The script is not ours to edit,
    so that one category is silenced for the call.
    """
    import analyse_phase_d2
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        rows, incomplete = analyse_phase_d2.load(prefix)
    return {"diffs": {int(seed): round(float(diff), 1) for seed, _, diff in rows},
            "incomplete": [int(seed) for seed, _ in incomplete]}


def _missing_agent(arm, seed):
    """The half of a pair whose directory is not there, as the catalog lists it."""
    return {"tag": f"{arm}_seed{seed}", "arm": arm, "status": "missing",
            "reason": "no such directory", "problems": [], "budget_line": None,
            "train_dt": None, "zip_sha": None, "scored": None}


def discover(root=ROOT):
    """Every experiment under `root` and every pair in it, for the picker.

    Lists root/runs*/ directories whose name matches RUNS_NAME, sorted by
    name, so a future runs_X appears with no code change; inside each, only
    children that are directories matching AGENT_NAME (_logs, checkpoints and
    files are ignored). EVERY seed is listed: a pair that cannot run carries
    every one of its problems, both arms, and a seed with one arm missing
    lists that arm as 'missing'. Never raises for an agent or a pair that
    cannot run; reads only; starts no thread.
    """
    root = Path(root)
    out = []
    for d in sorted((p for p in root.glob("runs*") if p.is_dir() and RUNS_NAME.fullmatch(p.name)),
                    key=lambda p: p.name):
        runs = d.name
        prefix = RPD.result_prefix(str(d))
        diffs = table_rows(prefix)["diffs"]
        seeds = set()
        for child in d.iterdir():
            m = AGENT_NAME.fullmatch(child.name)
            if m is not None and child.is_dir():
                seeds.add(int(m.group(2)))
        pairs = []
        for seed in sorted(seeds):
            here = {arm: (d / f"{arm}_seed{seed}").is_dir() for arm in ARMS}
            if all(here.values()):
                pair = check_pair(runs, seed, root)
            else:
                agents = [dict(read_agent(runs, f"{arm}_seed{seed}", root), scored=None)
                          if here[arm] else _missing_agent(arm, seed) for arm in ARMS]
                pair = {"protocol": None,
                        "result_file": (root / "results" / f"{prefix}_seed{seed}.txt").is_file(),
                        "agents": agents,
                        "problems": [line for a in agents for line in _agent_problems(a)]}
            problems = pair["problems"]
            pairs.append({
                "seed": seed,
                "runnable": not problems,
                "reason": problems[0] if problems else None,
                "problems": problems,
                "protocol": None if problems else pair["protocol"],
                "result_file": pair["result_file"],
                "table_diff": diffs.get(seed),
                "agents": [{k: a.get(k) for k in CATALOG_AGENT_KEYS} for a in pair["agents"]],
            })
        protocols = {p["protocol"] for p in pairs if p["runnable"]}
        out.append({
            "runs": runs,
            "name": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "prefix": prefix,
            "protocol": protocols.pop() if len(protocols) == 1 else None,
            "verdict": verdict(prefix, root),
            "pairs": pairs,
        })
    return out
