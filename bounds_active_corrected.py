"""bounds_active_corrected.py -- decision 92's corrected bound lists: S2's and S4's bounds_active of each EPA engine's
frozen form, recomputed from the frozen calibration records by epa_fit.bounds_at, beside every fitted parameter's
distance to its bound, written once to results/EPA_CALIBRATION/bounds_active_corrected.json.

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B bounds_active_corrected.py write
    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B bounds_active_corrected.py check

    write   computes the record and writes it through epa_freeze.write_json_atomic; refused if the file exists (it
            is written once). Prints, per engine and stage, the names added and the separation, then the
            separation over every engine. Exit 0 written, 2 refused.
    check   recomputes the record and compares it with the file, every key but `versions` (the platform string
            changes by design at ORDER step 22, row 126, and float64 subtraction and division are correctly
            rounded, so no distance depends on it); a versions difference is printed and not counted. Prints the
            same lines as write. Exit 0 no differences, 1 differences, 2 refused.

Build step 2, ORDER step 15, commit G (results/VALIDATION_DECISIONS.md decision 92 and rows 109 and 141;
docs/build_step_2/INTERFACES.md sections 7 and 12.6). Decisions and rows are cited by number, never by line: the
decisions file grows, and row 109's own "VD:317" and "validate_epa.py:30-31" are stale (row 141 (6)).

THE DEFECT (decision 92). S4's bounds_active named only what scipy's active_mask marks, and missed four parameters
that sit on their bounds, the Ford's burn_rpm, fmep_0 and fmep_sp and the Honda's burn_rpm; each list named only
delay_rpm. S2 took its list the same way. epa_fit's section "Decision 92's correction" says why the mask misses
them (trf's threshold, xtol * max(1, |bound|), against iterates kept strictly inside the bounds) and holds the
correction, epa_fit.bounds_at, which s2_breathing and s4_burn call from commit G on; this script applies the same
function to the frozen records, which are never refitted and never rewritten (row 109: "No fit runs, and no frozen
record is rewritten").

WHAT IT READS (row 141 (1), which replaces row 109's "computed from the frozen parameter vectors and
`epa_fit.BOUNDS` alone": the inputs are those, epa_fit.X_SCALE, and settings.bounds for ve_rpm). For each engine of
thresholds.common.EPA_ENGINES, two committed records, through epa_freeze.read_json, which reads a calibration
record and nothing else: results/EPA_CALIBRATION/<id>/freeze.json (epa_freeze.freeze_relpath), and the fit record
of the form it froze, fit_<form>.json. Every check below refuses the whole record, and nothing is written:
  * the fit record's sha_text is freeze.json's `fits` entry for it, and engines.frozen_sections_sha256 of its
    `values` equals both freeze.json's frozen_sections_sha256 and the record's own: the vector read is provably
    the frozen one (engines.py's one definition of that hash);
  * its settings.bounds equal epa_fit.BOUNDS bit for bit wherever BOUNDS holds a pair, and its settings.x_scale
    epa_fit.X_SCALE. ve_rpm's ends, which BOUNDS holds as None (the engine's end lines, read from the calibration
    view at the fit: epa_fit._rpm_ends, amendment D9), are read from settings.bounds, which must be bit-equal to
    S2's report bounds (row 141 (3)); this script never calls _rpm_ends or an epa_rows loader;
  * S2's and S4's report params are epa_fit.s2_names(form) and epa_fit.S4_PARAMS, and for each of them
    values.cycle equals the stage's own values bit for bit (the stage's point is the frozen point);
  * each recorded list holds only its stage's params, and its flag (S2_bound_active, S4_bound_active) is raised
    exactly when the list is not empty, as epa_fit wrote them.
It opens no EPA table and no held-out row, and builds no plant: the frozen vectors are numbers. It imports no
fingerprint and calls no fingerprint function; epa_freeze imports fingerprint at module level (epa_freeze.py:65),
so test_bounds_active_corrected checks this file's own AST, never an import closure.

WHAT IT CORRECTS. Only the frozen form, A+B+C+D on all three engines (row 141 (4)); freeze.json's other fit records
are listed as "not corrected" and not opened. S2 and S4 are the stages whose lists came from active_mask
(epa_fit.py:1727 and :2002, the two lines commit G changes). Each recorded list is read back as the mask (1 where
recorded, as epa_fit wrote it from the mask), and corrected = epa_fit.bounds_at(the stage's params, values.cycle,
that mask, settings' bounds, epa_fit.X_SCALE): every recorded name stays, and the tolerance,
epa_fit.BOUND_TOL_SCALE_UNITS, adds the rest (row 141 (2)). S1 (exact membership), S3b (the grid's edges) and S5
(Brent within S5_XATOL) keep their own rules: their recorded lists are copied, each with its rule named. If the
corrected lists are not row 109's, they are committed as found and disclosed beside row 109's; the tolerance never
moves to fit them (row 141 (1)).

THE RECORD (INTERFACES.md 12.6): schema, decisions, rule, tolerance, bounds (epa_fit.BOUNDS, ve_rpm null), x_scale,
engines {id: {form, inputs {path: sha_text}, frozen_sections_sha256, ve_rpm_bounds_from, distances {name:
epa_fit.bound_distances' entry plus its stage}, stages, other_forms}}, code_sha_text, versions, fit_run false,
frozen_records_rewritten false and not_rewritten_note. No timestamp and no git HEAD, so that check recomputes it
exactly; code_sha_text (thresholds.common.sha_text of epa_fit.py and of this file) ties it to the code that wrote
it, so a later change to either is a difference check prints. The file lies beside the engines' folders, outside
every engine's CAL_RECORDS (validate_epa.py:124-126) and outside what epa_freeze.read_json reads.

WHERE IT CANNOT RUN. On row 94's restored branch (epa_fit.py back to the third commit F's version, row 141 (5)) there
is no bounds_at, and neither this script nor its test runs there. No hashed module imports this one
(test_bounds_active_corrected), and its name ends with no plant file's name (row 127 (5): fingerprint's
dirty-file match).
"""
import argparse
import json
import math
import os
import sys

import engines
import epa_fit
import epa_freeze
from thresholds import common

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_REL = "results/EPA_CALIBRATION/bounds_active_corrected.json"
SCHEMA = "epa-bounds-active-corrected/1"
ENGINES = common.EPA_ENGINES                       # thresholds/common.py, the one list of the EPA engines
EXIT_OK, EXIT_DIFFERENCES, EXIT_REFUSED = 0, 1, 2
DECISIONS = ["decision 92", "row 109", "row 141"]
CORRECTED_STAGES = ("S2", "S4")                    # the two stages whose lists came from active_mask
# The stages that keep their own rule (row 141 (2)), each named as epa_fit applies it.
COPIED_RULES = {
    "S1": "exact membership (epa_fit.s1_backpressure): exh_bp_ratio when the ratio is an end of "
          "epa_fit.BOUNDS['exh_bp_ratio'], exh_bp_min_kpa when the hinge is an end of its grid",
    "S3b": "the grid's edges (epa_fit.s3b_lambda, amendment C1): the gate or an rpm breakpoint at an extreme of "
           "S3b's grid, at the optimum or over the flat interval",
    "S5": "Brent within epa_fit.S5_XATOL (epa_fit.s5_rich_slope): ce_rich_slope when the slope lies within S5_XATOL "
          "of an end of epa_fit.BOUNDS['ce_rich_slope']",
}
STAGE_ORDER = ("S1", "S2", "S3b", "S4", "S5")
DISTANCE_STAGES = ("S1", "S2", "S4", "S5")         # the stages whose values carry a bound in settings.bounds
RULE = ("A parameter of S2 or S4 is at its bound when scipy's active_mask marked it (the recorded list) or when "
        "min(x - lb, ub - x) <= epa_fit.BOUND_TOL_SCALE_UNITS x its epa_fit.X_SCALE, both bounds finite "
        "(epa_fit.bounds_at; rows 109 and 141 (1)-(2)). x is the frozen vector, values.cycle of the frozen form's fit "
        "record; lb and ub are its settings.bounds: epa_fit.BOUNDS bit for bit, and ve_rpm's end lines, which BOUNDS "
        "holds as None, from settings.bounds (row 141 (3)). S1, S3b and S5 keep their own rules and are copied. Only "
        "the frozen form is corrected (row 141 (4)). Nothing is refitted and no frozen record is rewritten (row 109).")
NOT_REWRITTEN_NOTE = (
    "No frozen record is rewritten (row 109): every fit_<form>.json keeps its recorded bounds_active and flags, and "
    "the three stage0.json files keep calibrate_epa.SEEN_BEFORE_THE_FIT's diagnostic-C entry as the fit wrote it, "
    "with the Mazda's derived file named by its path, while from commit G on the code's entry reads \"the Mazda's "
    "derived file\" (row 120; row 141 (7)). test_epa_rows' rule N1 scans .py files only, and no code compares the "
    "JSON copies with the code's tuple. On row 94's restored branch calibrate_epa.py is the third commit F's again, "
    "with the old label.")


class Refused(Exception):
    """A check of the inputs failed: nothing was written. `problems` lists every one found."""

    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


def _bits(v):
    """A JSON number's float64 bits, as text (float.hex: -0.0 and 0.0 differ, a NaN never reaches here)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise TypeError(f"not a number: {v!r}")
    return float(v).hex()


def _same(a, b):
    """Bit for bit: two numbers, or two lists of numbers of one length."""
    try:
        if isinstance(a, (list, tuple)) or isinstance(b, (list, tuple)):
            return (isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)) and len(a) == len(b)
                    and all(_bits(x) == _bits(y) for x, y in zip(a, b)))
        return _bits(a) == _bits(b)
    except TypeError:
        return False


def engine_part(engine, *, root):
    """One engine's entry of the record (the module docstring's WHAT IT READS and WHAT IT CORRECTS), from its two
    frozen records in the work tree `root`. Refused, naming every failed check, if any fails."""
    out = []
    fz_rel = epa_freeze.freeze_relpath(engine)
    fz = epa_freeze.read_json(fz_rel, root=root)
    form = fz.get("form")
    fits = fz.get("fits") or {}
    fit_name = f"fit_{form}.json"
    fit_rel = f"{os.path.dirname(fz_rel)}/{fit_name}"
    if fit_name not in fits:
        raise Refused([f"{engine}: freeze.json's fits does not name {fit_name}, the form it froze"])
    fit_sha = epa_freeze.file_sha_text(fit_rel, root=root)
    if fit_sha != fits[fit_name]:
        out.append(f"{engine}: {fit_rel} is not the file freeze.json's fits names (sha_text {fit_sha})")
    rec = epa_freeze.read_json(fit_rel, root=root)
    fss = engines.frozen_sections_sha256(rec["values"])
    if not fss == fz.get("frozen_sections_sha256") == rec.get("frozen_sections_sha256"):
        out.append(f"{engine}: frozen_sections_sha256 of {fit_name}'s values ({fss}) is not freeze.json's and the "
                   "record's own: the vector is not the frozen one")
    if rec.get("form") != form or rec["settings"].get("engine") != engine:
        out.append(f"{engine}: {fit_name} is the fit of {rec['settings'].get('engine')!r} at form "
                   f"{rec.get('form')!r}, not of {engine} at {form!r}")
    st, bounds, xsc = rec["stages"], rec["settings"]["bounds"], rec["settings"]["x_scale"]
    for n, b in bounds.items():
        if n not in epa_fit.BOUNDS:
            out.append(f"{engine}: settings.bounds names {n}, which epa_fit.BOUNDS does not")
        elif epa_fit.BOUNDS[n] is None:
            if n != "ve_rpm":
                out.append(f"{engine}: epa_fit.BOUNDS holds None for {n}; only ve_rpm's ends are read from the fit")
        elif not _same(b, list(epa_fit.BOUNDS[n])):
            out.append(f"{engine}: settings.bounds[{n!r}] {b!r} is not epa_fit.BOUNDS' {list(epa_fit.BOUNDS[n])!r}")
        if not (isinstance(b, list) and len(b) == 2 and all(isinstance(v, (int, float)) and math.isfinite(v)
                                                            for v in b) and b[0] < b[1]):
            out.append(f"{engine}: settings.bounds[{n!r}] {b!r} is not two finite ends in order")
    for n, s in xsc.items():
        if n not in epa_fit.X_SCALE or not _same(s, epa_fit.X_SCALE[n]):
            out.append(f"{engine}: settings.x_scale[{n!r}] {s!r} is not epa_fit.X_SCALE's")
    want = {"S2": list(epa_fit.s2_names(form)), "S4": list(epa_fit.S4_PARAMS)}
    for s in CORRECTED_STAGES:
        rep = st[s]["report"]
        if list(rep["params"]) != want[s]:
            out.append(f"{engine}: {s}'s report params {rep['params']} are not epa_fit's {want[s]}")
        for n in rep["params"]:
            if n not in bounds or n not in xsc:
                out.append(f"{engine}: {s}'s {n} has no settings.bounds or settings.x_scale entry")
            if not _same(rec["values"]["cycle"].get(n), st[s]["values"].get(n)):
                out.append(f"{engine}: values.cycle[{n!r}] is not {s}'s own value bit for bit")
        recorded = list(st[s]["bounds_active"])
        if [n for n in rep["params"] if n in recorded] != recorded:
            out.append(f"{engine}: {s}'s recorded list {recorded} is not a list of its params in their order")
        if (f"{s}_bound_active" in st[s]["flags"]) != bool(recorded):
            out.append(f"{engine}: {s}'s flag {s}_bound_active disagrees with its recorded list {recorded}")
    for n in st["S2"]["report"]["params"]:
        if not _same(st["S2"]["report"]["bounds"].get(n), bounds.get(n)):
            out.append(f"{engine}: S2's report bounds for {n} are not settings.bounds' bit for bit")
    stage_of = {}
    for s in DISTANCE_STAGES:
        for n in st[s]["values"]:
            if n in bounds:
                stage_of.setdefault(n, []).append(s)
    for n in bounds:
        if len(stage_of.get(n, [])) != 1:
            out.append(f"{engine}: settings.bounds' {n} is fitted by {stage_of.get(n, [])}, not by exactly one stage")
    if out:
        raise Refused(out)
    names = list(bounds)
    cyc = rec["values"]["cycle"]
    dist = epa_fit.bound_distances(names, [cyc[n] for n in names], lb=[bounds[n][0] for n in names],
                                   ub=[bounds[n][1] for n in names], x_scale=[epa_fit.X_SCALE.get(n) for n in names])
    stages = {}
    for s in STAGE_ORDER:
        recorded = list(st[s]["bounds_active"])
        if s not in CORRECTED_STAGES:
            stages[s] = {"recorded": recorded, "rule": COPIED_RULES[s]}
            continue
        params = list(st[s]["report"]["params"])
        corrected = epa_fit.bounds_at(params, [cyc[n] for n in params], [1 if n in recorded else 0 for n in params],
                                      lb=[bounds[n][0] for n in params], ub=[bounds[n][1] for n in params],
                                      x_scale=[epa_fit.X_SCALE[n] for n in params])
        stages[s] = {"params": params, "recorded": recorded, "corrected": corrected,
                     "added": [n for n in corrected if n not in recorded],
                     "flag_recorded": f"{s}_bound_active" in st[s]["flags"], "flag_corrected": bool(corrected)}
    return {"form": form,
            "inputs": {fz_rel: epa_freeze.file_sha_text(fz_rel, root=root), fit_rel: fit_sha},
            "frozen_sections_sha256": fss,
            "ve_rpm_bounds_from": f"{fit_rel} settings.bounds (bit-equal to stages.S2.report.bounds)",
            "distances": {n: dict(dist[n], stage=stage_of[n][0]) for n in names},
            "stages": stages,
            "other_forms": {f"{os.path.dirname(fz_rel)}/{f}": "not corrected"
                            for f in sorted(fits) if f.startswith("fit_") and f != fit_name}}


def compute(root):
    """The whole record (THE RECORD), from the frozen records in the work tree `root` and the code beside this file.
    Refused, naming every failed check of every engine, if any fails."""
    parts, out = {}, []
    for e in ENGINES:
        try:
            parts[e] = engine_part(e, root=root)
        except Refused as exc:
            out += exc.problems
    if out:
        raise Refused(out)
    return {"schema": SCHEMA, "decisions": list(DECISIONS), "rule": RULE,
            "tolerance": {"value": epa_fit.BOUND_TOL_SCALE_UNITS, "unit": "epa_fit.X_SCALE units",
                          "constant": "epa_fit.BOUND_TOL_SCALE_UNITS",
                          "chosen_after": "the distances were read (disclosed)"},
            "bounds": {n: None if b is None else list(b) for n, b in epa_fit.BOUNDS.items()},
            "x_scale": dict(epa_fit.X_SCALE),
            "engines": parts,
            "code_sha_text": {"epa_fit.py": common.sha_text(os.path.abspath(epa_fit.__file__)),
                              "bounds_active_corrected.py": common.sha_text(os.path.abspath(__file__))},
            "versions": epa_freeze.versions(),
            "fit_run": False, "frozen_records_rewritten": False, "not_rewritten_note": NOT_REWRITTEN_NOTE}


def out_path(root):
    return os.path.join(root, *OUT_REL.split("/"))


def write(root):
    """`write`: the record computed and written once into `root`; returns (record, sha_text written)."""
    path = out_path(root)
    if os.path.exists(path):
        raise Refused([f"{OUT_REL} exists: the record is written once (check compares it)"])
    rec = compute(root)
    return rec, epa_freeze.write_json_atomic(path, rec)


def _differences(a, b, where, out):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in list(a) + [k for k in b if k not in a]:
            if k not in b:
                out.append(f"{where}{k}: in the committed record, not in the recomputation")
            elif k not in a:
                out.append(f"{where}{k}: in the recomputation, not in the committed record")
            else:
                _differences(a[k], b[k], f"{where}{k}.", out)
    elif json.dumps(a, sort_keys=True) != json.dumps(b, sort_keys=True):
        out.append(f"{where[:-1]}: committed {a!r}, recomputed {b!r}")


def _committed(root):
    path = out_path(root)
    if not os.path.isfile(path):
        raise Refused([f"{OUT_REL} is absent: `write` has not run"])
    return common.load_json(path)


def problems(root):
    """`check`'s differences between the committed record and compute(root), every key but `versions`; [] when they
    agree. Refused if the record is absent or an input check fails."""
    have = _committed(root)
    fresh = json.loads(json.dumps(compute(root), allow_nan=False))
    out = []
    _differences({k: v for k, v in have.items() if k != "versions"},
                 {k: v for k, v in fresh.items() if k != "versions"}, "", out)
    return out


def versions_note(root):
    """The committed record's versions against this interpreter's, printed by check and never counted: None when
    equal."""
    have, now = _committed(root).get("versions"), epa_freeze.versions()
    return None if have == now else f"versions: the record's {have!r}, this interpreter's {now!r}"


def separation(rec):
    """Over S2 and S4 of every engine: the named parameter farthest from its bound and the unnamed one nearest to
    it, each (engine, stage, name, distance in X_SCALE units); the commit quotes these from the printout (row 141
    (1)). Also per (engine, stage)."""
    rows = []
    for e, part in rec["engines"].items():
        for s in CORRECTED_STAGES:
            g = part["stages"][s]
            for n in g["params"]:
                rows.append((e, s, n, part["distances"][n]["distance_x_scale_units"], n in g["corrected"]))
    named = [r for r in rows if r[4]]
    others = [r for r in rows if not r[4]]
    return (max(named, key=lambda r: r[3])[:4] if named else None,
            min(others, key=lambda r: r[3])[:4] if others else None, rows)


def report_lines(rec):
    """What write and check print: per engine and stage the lists and the separation, then the overall separation."""
    lines = [f"tolerance {rec['tolerance']['value']!r} {rec['tolerance']['unit']} ({rec['tolerance']['constant']})"]
    far, near, rows = separation(rec)
    for e, part in rec["engines"].items():
        for s in STAGE_ORDER:
            g = part["stages"][s]
            if s not in CORRECTED_STAGES:
                lines.append(f"{e} {s}: recorded {g['recorded']} (its own rule, copied)")
                continue
            mine = [r for r in rows if r[0] == e and r[1] == s]
            nf = max((r for r in mine if r[4]), key=lambda r: r[3], default=None)
            nn = min((r for r in mine if not r[4]), key=lambda r: r[3], default=None)
            lines.append(f"{e} {s}: recorded {g['recorded']}, corrected {g['corrected']}, added {g['added']}; "
                         f"flag {g['flag_recorded']} -> {g['flag_corrected']}; named farthest "
                         + ("none" if nf is None else f"{nf[2]} {nf[3]!r}") + ", unnamed nearest "
                         + ("none" if nn is None else f"{nn[2]} {nn[3]!r}") + " (X_SCALE units)")
    lines.append("separation over every engine's S2 and S4: the named farthest from its bound "
                 + ("none" if far is None else f"{far[0]} {far[1]} {far[2]} {far[3]!r}")
                 + ", the unnamed nearest to one "
                 + ("none" if near is None else f"{near[0]} {near[1]} {near[2]} {near[3]!r}") + " (X_SCALE units)")
    return lines


def main(argv):
    ap = argparse.ArgumentParser(prog="bounds_active_corrected.py",
                                 description="decision 92's corrected bound lists (see the docstring)")
    ap.add_argument("cmd", choices=("write", "check"))
    args = ap.parse_args(argv)
    try:
        if args.cmd == "write":
            rec, sha = write(HERE)
            for line in report_lines(rec):
                print(f"  {line}")
            print(f"bounds_active_corrected.py write: written {OUT_REL} (sha_text {sha})")
            return EXIT_OK
        diffs = problems(HERE)
        note = versions_note(HERE)
        rec = _committed(HERE)
    except Refused as exc:
        print(f"bounds_active_corrected.py {args.cmd}: refused: " + "; ".join(exc.problems))
        return EXIT_REFUSED
    for line in report_lines(rec):
        print(f"  {line}")
    if note:
        print(f"  {note} (not counted)")
    print(f"bounds_active_corrected.py check: {diffs}")
    return EXIT_DIFFERENCES if diffs else EXIT_OK


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
