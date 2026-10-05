"""The results tab's data: every evaluation experiment in results/, read on every request.

GET /api/results answers build(). Nothing is cached between requests and
nothing is computed that a committed script does not compute: the one
difference taken here is blind minus sighted per seed, as
analyse_phase_d2.load takes it. Verdicts are quoted through
app.agent_catalog.verdict, never computed.

DISCOVERY reads results/ only, never runs*/ (gitignored, absent on a
teammate's clone). Every file directly in results/ whose name matches
*_seed*.txt is a candidate. A name that fails results_eval.NAME_RE, a file
whose first line is not an evaluate.py header, a file with no plant
fingerprint block or no policy table, and a file that cannot be read at all
are listed under not_read with the reason, never dropped silently. So are two
files that name the same prefix and seed (the seed written with and without
a leading zero): both are listed with the reason duplicate_seed and neither
is read, because the names cannot say which of them is the experiment's
seed. A prefix left with no seed shows as missing when it is a known
experiment and not at all otherwise. A seed with one arm only is listed
under its section's unpaired.

FAILURE COSTS ONE SECTION. Each section is built inside its own try, which
catches Exception and SystemExit and nothing broader: a broken file or
reader costs its own section and never the tab, and a KeyboardInterrupt
still stops the server. A known experiment with no file at all is shown as
missing, with the command that makes its files.

A MODULE THAT CANNOT BE IMPORTED is named once in import_failures. Every
evaluation section needs run_phase_d (its name) and analyse_phase_d2 (its
MEI), and says so when one is missing; without analyse_phase_d the parse
check reads not compared; without app.agent_catalog every verdict reads
unavailable; without evaluate a file's protocol cannot come from its title.
Every one of them is imported inside build(), so importing this module
loads no agent code.

What this module never does: write (no file, no cache on disk), run a git
command that can write (results_provenance sets GIT_OPTIONAL_LOCKS before
its first call), or import derive_params, record_agents, knock_margin or
train.
"""
from __future__ import annotations

import importlib
import math
from pathlib import Path
import time

import numpy as np

from app import results_eval as E
from app import results_provenance as P

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
EVAL_COMMAND = "python run_phase_d.py (evaluate.py --out results/<prefix>_seed<N>.txt)"
# The experiments the team has run, in the order they ran, with the notes that
# no result file records (spec 5.4). A prefix not listed here is shown after
# them, by name, with only what its own files record.
KNOWN = {
    "phase_d": {"order": 0, "notes": ["blind_not_blind", "budget_c1", "spark_bound_jad",
                                      "spike_unmeasured"], "mei_after_result": True},
    "d2": {"order": 1, "notes": ["budget_c1", "spark_bound_jad", "spike_unmeasured"]},
    "c4": {"order": 2, "notes": ["c4_not_converged", "spark_bound_jad", "spike_unmeasured"],
           "continues": "d2"},
}
UNKNOWN_ORDER = 100
ARMS = ("sighted", "blind")
# Imported inside build(), each once per build; a failure is one import_failures line.
MODULES = ("run_phase_d", "analyse_phase_d", "analyse_phase_d2", "evaluate")
# What every evaluation section cannot be shown without: its name and its MEI.
SECTION_NEEDS = ("run_phase_d", "analyse_phase_d2")
CHECK = "parse_equals_analysis"


def jsonable(x):
    """A JSON-safe copy of `x`: numpy values become Python ones, NaN and
    infinity become None. bool is tested before int, being a subclass of it."""
    if isinstance(x, dict):
        return {str(k): jsonable(v) for k, v in x.items()}
    if isinstance(x, np.ndarray):
        return [jsonable(v) for v in x.tolist()]
    if isinstance(x, (list, tuple)):
        return [jsonable(v) for v in x]
    if isinstance(x, (bool, np.bool_)):
        return bool(x)
    if isinstance(x, (int, np.integer)):
        return int(x)
    if isinstance(x, (float, np.floating)):
        value = float(x)
        return value if math.isfinite(value) else None
    if x is None or isinstance(x, str):
        return x
    raise TypeError(f"not JSON-safe: {type(x).__name__}")


def _rel(path, results_root):
    """A result file as the page names it: results/<name>, forward slashes."""
    return f"{Path(results_root).name}/{Path(path).name}"


def _order(prefix):
    return (KNOWN.get(prefix, {}).get("order", UNKNOWN_ORDER), prefix)


def discover_evaluations(results_root):
    """({prefix: {seed: path}}, not_read) for every *_seed*.txt directly in results_root.

    Only the name is read here; a file is parsed by its section. A name that
    fails NAME_RE is listed with the reason "name". Two files that name the
    same prefix and seed (the seed written with and without a leading zero)
    are both listed with the reason "duplicate_seed" and neither is returned
    in the groups, so neither is read; a prefix left with no seed is not in
    the groups at all.
    """
    results_root = Path(results_root)
    named, not_read = {}, []
    for path in sorted(results_root.glob("*_seed*.txt")):
        if not path.is_file():
            continue
        got = E.parse_name(path.name)
        if got is None:
            not_read.append({"path": _rel(path, results_root), "reason": "name", "type": None})
            continue
        named.setdefault(got, []).append(path)
    groups = {}
    for (prefix, seed), paths in named.items():
        if len(paths) > 1:
            not_read.extend({"path": _rel(path, results_root), "reason": "duplicate_seed",
                             "type": None} for path in paths)
            continue
        groups.setdefault(prefix, {})[seed] = paths[0]
    return groups, not_read


def _unavailable(prefix, ctx, kind, file=None, command=None, type_=None, module=None):
    return {"id": f"exp-{prefix}", "kind": "evaluation", "state": "unavailable",
            "prefix": prefix, "name": ctx["names"].get(prefix), "order": _order(prefix)[0],
            "error": {"kind": kind, "file": file, "command": command, "type": type_,
                      "module": module}}


def _budget(models):
    """{steps, requested} when every model line of one file records the same pair."""
    pairs = {(m["steps"], m["requested"]) for m in models}
    if len(pairs) != 1:
        return None
    steps, requested = pairs.pop()
    if steps is None or requested is None:
        return None
    return {"steps": steps, "requested": requested}


def _notes(prefix, parsed, thermal_recorded):
    """The section's required notes, in the order the page shows them (spec 5.4)."""
    known = KNOWN.get(prefix)
    notes = [{"key": key, "values": {}} for key in (known["notes"] if known else [])]
    models = [m for p in parsed for m in p["models"]]
    steps = {m["steps"] for m in models}
    if models and None not in steps and len(steps) == 1:
        notes.append({"key": "budget_from_file", "values": {"steps": steps.pop()}})
    pairs = []
    for p in parsed:
        for dt in p["dt_notes"]:
            pair = (dt["train_dt"], dt["eval_dt"])
            if pair not in pairs:
                pairs.append(pair)
                notes.append({"key": "dt_mismatch",
                              "values": {"train_dt": pair[0], "eval_dt": pair[1]}})
    if thermal_recorded == "none":
        notes.append({"key": "no_thermal_only", "values": {}})
    notes.append({"key": "knock_model", "values": {}})
    notes.append({"key": "turbine_modelled", "values": {}})
    if known is None:
        notes.append({"key": "no_other_notes", "values": {}})
    return notes


def _verdict(prefix, ctx):
    """The quoted verdict, as app.agent_catalog.verdict returns it. Its 'none'
    text says nothing on its page is a result, so that short is never passed on."""
    verdict = ctx["verdict"]
    if verdict is None:
        return {"state": "unavailable"}
    got = verdict(prefix, root=ctx["results_root"].parent)
    out = {key: got.get(key) for key in ("state", "lines", "cells", "missing", "short")}
    if out["state"] == "none":
        out["short"] = None
    return out


def _parse_check(parsed, rels, analysis):
    """The medians read here against analyse_phase_d.parse's, file by file (spec 4.4)."""
    if analysis is None:
        return {"name": CHECK, "state": "not_compared", "detail": None}
    label = {role: prefix for prefix, role in E.ROLE_PREFIXES}
    bad = []
    for seed in sorted(parsed):
        ours = {label[role]: pol["median"] for role, pol in parsed[seed]["policies"].items()}
        theirs = analysis.parse(parsed[seed]["path"])
        if ours != theirs:
            names = sorted(k for k in set(ours) | set(theirs) if ours.get(k) != theirs.get(k))
            bad.append(f"{rels[seed]} ({', '.join(names)})")
    return {"name": CHECK, "state": "fail" if bad else "pass", "detail": "; ".join(bad) or None}


def evaluation_section(prefix, files, ctx):
    """One evaluation experiment from its result files, or None.

    None when the prefix is not a known experiment and none of its files
    could be read: those files are in not_read and there is nothing else to
    show. Files that cannot be read are appended to ctx["not_read"].
    """
    for module in SECTION_NEEDS:
        if ctx["modules"][module] is None:
            return _unavailable(prefix, ctx, "module", module=module)
    results_root = ctx["results_root"]
    if not files:
        return _unavailable(prefix, ctx, "missing",
                            file=f"{results_root.name}/{prefix}_seed<N>.txt",
                            command=EVAL_COMMAND.replace("<prefix>", prefix))
    parsed, rels, failed = {}, {}, []
    for seed in sorted(files):
        rel = _rel(files[seed], results_root)
        try:
            parsed[seed] = E.parse_eval_file(files[seed])
            rels[seed] = rel
        except E.NotEvaluationFile as exc:
            failed.append({"path": rel, "reason": exc.reason, "type": None})
        except (Exception, SystemExit) as exc:
            failed.append({"path": rel, "reason": "unreadable", "type": type(exc).__name__})
    ctx["not_read"].extend(failed)
    if not parsed:
        if prefix not in KNOWN:
            return None
        return _unavailable(prefix, ctx, "read", file=failed[0]["path"],
                            type_=failed[0]["type"] or "NotEvaluationFile")

    seeds, unpaired = [], []
    for seed in sorted(parsed):
        pol = parsed[seed]["policies"]
        if not all(arm in pol for arm in ARMS):
            unpaired.append({"seed": seed, "file": rels[seed],
                             "have": [role for role in E.ROLES if role in pol]})
            continue
        seeds.append({"seed": seed, "file": rels[seed],
                      "sighted": pol["sighted"], "blind": pol["blind"],
                      "baseline": pol.get("baseline"), "reactive": pol.get("reactive"),
                      "current_grade": pol.get("current_grade"),
                      "thermal": parsed[seed]["thermal"],
                      "diff": pol["blind"]["median"] - pol["sighted"]["median"],
                      "budget": _budget(parsed[seed]["models"])})
    thermal = [s for s in seeds if s["thermal"] and all(arm in s["thermal"] for arm in ARMS)]
    thermal_recorded = ("none" if not thermal else
                        "all" if len(thermal) == len(seeds) else "some")

    first = parsed[min(parsed)]
    protocol = (first["protocol"] or E.protocol_from_fingerprint(first["fingerprint"])
                or ctx["title_protocols"].get(first["title"]))
    per_file = {seed: P.classify_eval(parsed[seed], ctx["live"], ctx["git"], rels[seed],
                                      ctx["last"], ctx["status"], ctx["title_protocols"])
                for seed in sorted(parsed)}
    return {"id": f"exp-{prefix}", "kind": "evaluation", "state": "ok",
            "prefix": prefix, "name": ctx["names"].get(prefix),
            "known": prefix in KNOWN, "order": _order(prefix)[0],
            "continues": KNOWN.get(prefix, {}).get("continues"),
            "protocol": protocol, "episodes": first["n_episodes"], "frozen": first["frozen"],
            "scenario": first["scenario_line"],
            "seeds": seeds, "unpaired": unpaired,
            "mei": ctx["modules"]["analyse_phase_d2"].MEI,
            "mei_after_result": KNOWN.get(prefix, {}).get("mei_after_result", False),
            "thermal_recorded": thermal_recorded,
            "verdict": _verdict(prefix, ctx),
            "notes": _notes(prefix, [parsed[s] for s in sorted(parsed)], thermal_recorded),
            "provenance": P.section_provenance(per_file),
            "checks": [_parse_check(parsed, rels, ctx["modules"]["analyse_phase_d"])],
            "error": None}


def _load(name, failures):
    """The module `name`, or None after adding {module, type} to failures."""
    try:
        return importlib.import_module(name)
    except (Exception, SystemExit) as exc:
        failures.append({"module": name, "type": type(exc).__name__})
        return None


def build(results_root: Path = RESULTS, git_root: Path = ROOT, *, live: dict | None = None,
          verdict=None) -> dict:
    """Every section of the tab, rebuilt from the files.

    {built, import_failures, sections, not_read}, through jsonable. `live`
    replaces results_provenance.live_side(git_root) and `verdict` replaces
    app.agent_catalog.verdict; tests pass stand-ins. `verdict` is called as
    verdict(prefix, root=<the parent of results_root>). built.head is None
    whenever built.git reads unavailable, so no git fact survives a git lost
    part-way through the build.
    """
    started = time.perf_counter()
    results_root, git_root = Path(results_root), Path(git_root)
    failures = []
    modules = {name: _load(name, failures) for name in MODULES}
    if verdict is None:
        verdict = getattr(_load("app.agent_catalog", failures), "verdict", None)
    if live is None:
        live = P.live_side(git_root)
    failures += [{"module": e["module"], "type": e["type"]} for e in live["import_errors"]]
    git = P.Git(git_root)
    head = git.head_short()
    groups, not_read = discover_evaluations(results_root)
    rels = [_rel(path, results_root) for prefix in sorted(groups)
            for _, path in sorted(groups[prefix].items())]
    evaluate = modules["evaluate"]
    ctx = {"results_root": results_root, "live": live, "git": git,
           "status": (git.status(rels) if rels else None) or {},
           "last": (git.last_commits(rels) if rels else None) or {},
           "title_protocols": ({header: name for name, (_, header, _) in evaluate.PROTOCOLS.items()}
                               if evaluate is not None else {}),
           "names": (dict(modules["run_phase_d"].CLOSED_PREFIX)
                     if modules["run_phase_d"] is not None else {}),
           "modules": modules, "verdict": verdict, "not_read": not_read}
    sections = []
    for prefix in sorted(set(groups) | set(KNOWN), key=_order):
        try:
            section = evaluation_section(prefix, groups.get(prefix, {}), ctx)
        except (Exception, SystemExit) as exc:
            section = _unavailable(prefix, ctx, "build", type_=type(exc).__name__)
        if section is not None:
            sections.append(section)
    # Git's state at the END of the build decides: a git lost part-way (a status
    # it rejected, a timeout) takes the head with it, as it takes every commit fact.
    built = {"head": head if git.available else None, "python": live["python"],
             "plant_sha": live["plant_sha"], "restart_needed": live["restart_needed"],
             "derived_loaded_differs": live["derived_loaded_differs"],
             "git": "ok" if git.available else "unavailable",
             "elapsed_ms": int(round((time.perf_counter() - started) * 1000))}
    return jsonable({"built": built, "import_failures": failures, "sections": sections,
                     "not_read": not_read})
