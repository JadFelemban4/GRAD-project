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
M1 carries the C4 row only; the tables are keyed by result prefix so M2 adds
the d2 and phase_d rows without changing a signature.
"""
from __future__ import annotations

from collections import namedtuple
import os
from pathlib import Path
import re
import threading
import time

import fingerprint as FP
import run_phase_d as RPD
from analyse_c4 import BUDGET
from evaluate import DT, DURATION

ROOT = Path(__file__).resolve().parent.parent
RUNS_NAME = re.compile(r"^runs[A-Za-z0-9_]*$")
AGENT_NAME = re.compile(r"^(sighted|blind)_seed(\d+)$")
ARMS = ("sighted", "blind")


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
    """One agent directory's status. KeyError if either name is malformed."""
    m = AGENT_NAME.fullmatch(str(name))
    if not RUNS_NAME.fullmatch(str(runs)) or m is None:
        raise KeyError(f"{runs}/{name}")
    arm, seed = m.group(1), int(m.group(2))
    d = Path(root) / runs / name
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
    # run_phase_d.py:330 hands it, f"{runs}/{name}". Apply that exact rule.
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
    return dict(out, status="ready", protocol=protocol, budget=budget,
                budget_line=FP.format_budget(budget),
                zip_sha=budget["sha"] if budget else None,
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


def find_pair(runs, seed, root=ROOT):
    """The sighted and blind agent of one seed, checked. KeyError for a name
    that is malformed or not on disk; Refused for a pair that must not run."""
    if (not RUNS_NAME.fullmatch(str(runs)) or not isinstance(seed, int)
            or isinstance(seed, bool) or seed < 0):
        raise KeyError(f"{runs}/{seed}")
    root = Path(root)
    if not all((root / runs / f"{arm}_seed{seed}").is_dir() for arm in ARMS):
        raise KeyError(f"{runs}/{seed}")
    agents = [read_agent(runs, f"{arm}_seed{seed}", root) for arm in ARMS]
    problems = []
    for a in agents:
        if a["status"] != "ready":
            problems.append(f"{a['tag']}: {a['status']} -- {a['reason']}")
            problems.extend(f"{a['tag']}: {p}" for p in a["problems"])
    if problems:
        raise Refused(problems)
    if agents[0]["protocol"] != agents[1]["protocol"]:
        raise Refused([f"the two arms were trained on different protocols: "
                       f"{agents[0]['protocol']} and {agents[1]['protocol']}"])
    prefix = RPD.result_prefix(str(root / runs))
    shas = scored_shas(prefix, seed, root)
    for a in agents:
        recorded = None if shas is None else shas[a["arm"]]
        if recorded is not None and recorded != a["zip_sha"]:
            problems.append(f"{a['tag']}: not the scored artefact -- results/{prefix}_seed{seed}.txt "
                            f"records zip sha {recorded}, final.zip is {a['zip_sha']}")
        a["scored"] = "match" if recorded is not None and recorded == a["zip_sha"] else "not recorded"
    if problems:
        raise Refused(problems)
    return {"runs": runs, "seed": seed, "prefix": prefix,
            "experiment": RPD.CLOSED_PREFIX.get(prefix) or f"{runs} (no name recorded)",
            "protocol": agents[0]["protocol"], "result_file": shas is not None,
            "agents": agents}


# ---- verdicts: quoted from results/, cited by line --------------------------
Anchor = namedtuple("Anchor", "key file pattern n")

VERDICT_LINES = {
    "c4": (
        Anchor("result", "C4_RESULT.txt", r"^\s*RESULT: SMALLER THAN THE MEI\s*$", 1),
        Anchor("seeds", "C4_RESULT.txt", r"\(7 of 8 seeds below 50\)", 1),
        Anchor("disagree", "C4_RESULT.txt", r"^\s*THE TWO TESTS DISAGREE", 2),
        Anchor("convergence", "C4_RESULT.txt", r"^\s*NOT-CONVERGED ", 1),
        Anchor("reading", "C4_RESULT.txt", r"^THE READING, as declared", 4),
        Anchor("explanations", "PREREGISTRATION_C4.md", r"^\| \(i\) \|", 3),
        Anchor("one_seed", "PREREGISTRATION_C4.md",
               r"^2\. \*\*It rests on the sign test's threshold", 3),
    ),
}

# The anchor key that carries each quoted cell, in display order.
CELLS = {"c4": {"result": "SMALLER THAN THE MEI", "convergence": "NOT-CONVERGED"}}

SHORT_VERDICT = {
    "c4": {
        "ar": "أصغر من الحد الأدنى المهم (50 وحدة) عند 300 000 خطوة · بفارق بذرة واحدة "
              "· الاختباران مختلفان · لم يستقر التدريب",
        "en": "smaller than the MEI (50) at 300 000 steps · one seed wide "
              "· the two tests disagree · not converged",
        "requires": ("result", "seeds", "disagree", "convergence"),
    },
}

GLOSS = {
    "SMALLER THAN THE MEI": {
        "ar": "أثر الاستباق أقل من 50 وحدة ضرر، وهو حدّ اختاره الفريق مسبقاً، عند 300 000 "
              "خطوة تدريب، على طريق فيه تغيّر واحد في الميل لكل حلقة. التدريب لم يستقر، "
              "والنتيجة معلّقة على بذرة واحدة: لو انقلبت بذرة واحدة لصارت غير حاسمة.",
        "en": "Preview's effect is below 50 damage units, a threshold the team set in advance, "
              "at 300 000 training steps, on a road with one grade change per episode. "
              "Training had not settled, and the result hangs on one seed: if one seed "
              "flipped, it would be inconclusive.",
    },
    "NOT-CONVERGED": {"ar": "لم يستقر التدريب", "en": "Training had not settled"},
}

MISSING_TEXT = {
    "ar": "لم يُعثر على سطر الحكم في results/{file}: لا تقرأ هؤلاء الوكلاء بدونه",
    "en": "verdict line not found in results/{file}: do not read these agents without it",
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
        short = {lang: MISSING_TEXT[lang].format(file=missing[0]) for lang in MISSING_TEXT}
    elif authored is not None and set(authored["requires"]) <= found:
        short = {lang: authored[lang] for lang in ("ar", "en")}
    else:
        short = None
    cells = [{"cell": cell, "gloss": dict(GLOSS[cell])}
             for key, cell in CELLS.get(prefix, {}).items() if key in found]
    return {"state": "missing" if missing else "found", "lines": lines,
            "missing": missing, "short": short, "cells": cells}
