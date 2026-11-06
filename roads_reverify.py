"""roads_reverify.py -- roads.json re-verified on the code as it stands (rows 94, 97, 127 (1), 140).

    OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 .venv/Scripts/python.exe -B roads_reverify.py check --jobs J --out DIR
                                                        [--skip-companions] [--keep-going]
                    any tree, P's uncommitted one included; DIR lies outside every git work tree and only
                    DIR/reverify_CHECK.json is written; fail-fast by section unless --keep-going;
                    --skip-companions leaves roads_ceiling.report out and marks the result partial
    ... roads_reverify.py adopt FILE
                    a complete EQUAL check result whose head is HEAD and pushed, re-hashed against the tree,
                    written once to results/EPA_ROADS/reverify.json (P carries it, row 140 (3))
    ... roads_reverify.py record --jobs J [--supersede ROW]
                    on a clean HEAD in origin's GRA-test: results/EPA_ROADS/reverify.json, or with --supersede
                    the next free reverify_<n>.json (a re-made P, row 140 (5)), from a complete EQUAL result only
    exit 0 EQUAL, 1 DIFFERENT, 2 REFUSED; 3 a crash, which is no verdict and writes nothing

Row 140 governs this file, with rows 94, 96, 97, 102, 127 (1) and 146 (3); docs/build_step_2/INTERFACES.md
section 5 defines its names, 12.4 its record and section 17 (rows 146-147) its place: ORDER step 14 puts it
between step 13 and the plant commit P, C2 (step 12a) being not built (row 146 (3)).

WHAT IT IS (row 127 (1), row 140 (1)). The plant commit changes engine_env.py, engines.py, evaluate.py and
fingerprint.py (row 138 (1)), so every engine's plant_sha moves and epa_roads.verify_record refuses
roads.json on P's tree. (Row 140 (2) lets step_record.py differ too, for step 12a's edit; C2 is not built,
so it is not expected to, and MAY_DIFFER keeps it as the row lists it.) This module recomputes, on the code
as it stands, every number of roads.json that the draw's code computed, from roads.json's own arrays and
recorded draws, and requires each to be equal to the draw's: the same type and the same float bits. In row
98's order: the generated roads rebuilt from their recorded draws; the neutral-action identity on the B58's
locked climb, on every engine's generated arrays and on the final arrays; every replacement candidate's climb
tests and C5 margins and case, and the final C5 with its steps; the ceilings and passes_T; everything
roads_ceiling.report returns (row 102's grids with the one-housing Ford, E6 rows 4 and 11, the dt 0.5 s
repeat, decision 13's count, the observation ranges), but its provenance and wall_s; decision 40's
diagnostic, the coverage flags, the episode length and row 102's table of H; and each reading of
results/EPA_ROADS/redraws.json (R4, 34cca5b): the re-check at its recorded margins and every redraw. Run 2
dropped all three EPA engines (VALIDATION_DECISIONS section Q), so redraws.json holds both of
epa_roads.redraw's readings: 'version 6', the B58 alone gating, and 'version 5 (every engine gating)';
both are sections (row 140 (1): "and 'version 5 (every engine gating)' when present"), and every engine,
the dropped ones included, is recomputed in every section (row 140 (6): "The full check cannot be cut";
row 146: "RV cut to the B58: rejected"). It writes results/EPA_ROADS/reverify.json (12.4), naming
roads_sha, redraws_sha, the commit it ran on and each input file P changed, with its sha_text.

IT USES NO ROADS_SEED (row 96: any computation that uses roads_seed is an attempt). The generated roads
come back through epa_roads.layout fed a scripted stream of each road's recorded draws (lead_s, then L, g
and G of each climb, then the discarded triple), and their arrays must hash to what the draw's steps_log
printed. The replacement loop (epa_roads.replacement_loop) and the redraws (epa_roads.recheck_slots,
redraw_slot) run unchanged, the first draw's own code (row 97), with their 0x1D and 0xC5 streams swapped
for the recorded grades (scripted_streams, epa_roads.py:392-397) and roads_seed passed as None; a stream
asked for a draw the record does not hold raises NotRecorded, and that section is DIFFERENT. Nothing here
reads commit_reveal, and nothing is written to attempts.jsonl: this is not an attempt.

TAU IS READ, NEVER RECOMPUTED (row 102). roads_ceiling.use_recorded_taus is called with roads.json's tau
block before any other roads_ceiling call, as epa_roads.redraw does (epa_roads.py:1868). The perturbed
plants' taus inside report() (the one-housing Ford, E6 row 4) are part of what report() returns, and are
recomputed with it. Neither P's H nor its knock option is passed: roads.json's rewards were computed at
H = 30 s with the knock term (row 117; row 113 (5) covers training, gate and benchmark commands).

THE COMPARISON (compare). The new side goes through json.loads(json.dumps(x, allow_nan=False)), as the
record went through epa_roads.write_once. type(a) is type(b), so 1 and 1.0 differ and True and 1 differ;
floats are compared as struct.pack('<d', x), so -0.0 and 0.0 differ (HANDOFFS.md:65); dicts both ways;
lists by length, then item by item. Only IGNORED_PATHS are skipped: report.provenance (roads_ceiling.py:
1361-1377: the commit, the tree's changes, the versions, the cpu count, the plant_sha) and report.wall_s
(:1423), a time. Neither is step 12a's: row 140 (1) replaces row 127 (1)'s "ignoring only fields that step
12a adds", and ADDED_BY_STEP_12A is empty, since no number roads.json holds passes through step_record
(evaluate.run_episode records a step only when it is given a record, evaluate.py:279-280).

THE PRECONDITIONS, each refused with exit 2 before anything runs (row 140 (2); preconditions): the
versions of roads.json's hashes.versions (Python, NumPy, SciPy, the platform: bit equality is not expected
across versions, row 126); OMP_NUM_THREADS and MKL_NUM_THREADS at 1, python -B, and no bytecode cache
beside a hashed file or this module's closure; every engine_sha roads.json's, and each EPA engine's its
complete.json's (row 94); of roads.json's 35 hashed files only MAY_DIFFER may differ; the import-closure
set, the contract's two files and every data input unchanged; evaluate.EPISODES unchanged whole, its length
and every entry against the draw's evaluate.py (the tree's when its sha_text is roads.json's, otherwise that
version from HEAD's history, draw_episodes), every road paired with its entry; a tau for every engine;
from P on, when engine_env defines them, REWARD_KNOCK_DEFAULT True and preview_samples(PREVIEW_H_S) ==
PREVIEW_S. For the committed record also: roads.json committed at HEAD, in one commit, and named by the
attempts log's one roads outcome; a REAL record asks for the whole of row 103 (1); redraws.json, when it
exists, committed at HEAD in one commit, naming roads.json's roads_sha, seed_kind and taus, holding exactly
the readings epa_roads.redraw writes for its 'dropped', and, for a REAL record, named by the attempts log's
one redraws outcome, whose start line holds its margins and dropped list (and redraws.json is required
once that outcome exists). Its one data input is checked as roads.json's are (redraws_problems): Run 2's
summary.json, opened through the guard's one exception as epa_roads' recheck and redraw open it, must be
the sha_text redraws.json's margins_source names, give redraws.json's margins bit for bit
(epa_roads.margins_from_summary) and drop exactly its dropped engines (epa_roads.dropped_problems, the
redraw's own refusal). A hashed file, version, engine_sha or plant_sha that changes while it runs (and
summary.json, when redraws.json exists), or a file the run opened that neither the draw nor the redraws
did, makes the verdict REFUSED (as epa_roads.first_draw's unchanged(), epa_roads.py:1321-1328).

THE ROUTE (row 140 (3)-(5); INTERFACES 17). RV, this commit, after step 13 (row 146 (3) reads row 140 (3)'s
"after C2 and step 13" as "after step 13"), with its control `check --skip-companions` on RV's clean tree,
which must print EQUAL; it computes both readings of redraws.json, so it takes about 9.2 h (2.2 h plus
R4's 7.0 h; INTERFACES 17 0.2, ASSUMED but R4's 25 312 s). P's gate is the full fail-fast `check --jobs 14`
on P's uncommitted candidate tree (about 17.7 h, ibid.); once it prints EQUAL and every other gate of P has
passed, `adopt` re-hashes every input against that run's result and writes reverify.json once, and P
carries it. Before each of the two checks, from the repository's root, every __pycache__ folder outside
.git and .venv is deleted (INTERFACES 17, rule 1.10; the venv stays as it is, row 146 (8)):
    find . -path ./.git -prune -o -path ./.venv -prune -o -name __pycache__ -type d -exec rm -rf {} +
after which the same find with -print in place of -exec rm -rf {} + prints nothing. (The precondition
bytecode_caches looks only beside the hashed files and this module's closure, never inside .venv.) Then
`git status --porcelain` prints nothing before RV's control, on RV's clean tree, and before P's gate lists
P's candidate files and nothing else: P's check runs on P's uncommitted tree by design (row 140 (3)), and
check asks for no clean tree (record does).
A DIFFERENT or REFUSED result never enters results/ (row 140 (4)): it is a defect of P before P exists. A
P re-made after G or V is re-verified by `record --supersede <row>` on a restore commit (row 132's route),
which writes reverify_2.json, then _3, naming the record it supersedes.

WHAT IT NEVER DOES. It never calls fingerprint.plant_fingerprint, epa_roads.verify_record or
frozen_problems (plant_sha comes only through epa_freeze.plant_sha), nor generate, practice_roads,
training_share_road, draw, first_draw, redraw, recheck_or_redraw or roads_seed_from
(test_roads_reverify.Isolation scans for each). It opens no held-out record but summary.json, and that one
only through summary_opened: epa_roads' guard exception for exactly that path, given to roads_ceiling's guard
too for as long as the read lasts. No module of roads.json's 35, epa_freeze.CODE_HASHED or
fingerprint.PLANT_CODE imports it, so it can change without moving a plant_sha; the one reader of its
records is four_engine_roads.current_reverify, which every consumer calls (row 140 (5)), because a hashed
module (evaluate.py, at V) may not import this one.
"""
import argparse
import ast
import contextlib
import copy
import json
import os
import re
import struct
import subprocess
import sys
import traceback

import epa_roads as R
import four_engine_roads as FR
import roads_ceiling as RC

HERE = os.path.dirname(os.path.abspath(__file__))
MODULE_REL = "roads_reverify.py"
# The one definition of the record's path is the reader's (four_engine_roads.REVERIFY_REL): no hashed module
# may import this one, and four_engine_roads joins evaluate.py's closure at V (the interface sheet, section 5)
OUT_REL = FR.REVERIFY_REL
SCHEMA = "epa-roads-reverify/1"
ROW = "rows 94, 97, 127 (1), 140"
CHECK_NAME = "reverify_CHECK.json"
MAX_REPORTED = 50                     # at most 50 differences listed per section (the interface sheet, section 5)

# What is never compared, and why (row 140 (1)): roads_ceiling.provenance and report's wall_s
IGNORED_PATHS = (("report", "provenance"), ("report", "wall_s"))
IGNORED_WHY = ("roads_ceiling.report's provenance (roads_ceiling.py:1361-1377: git_head, tree_changes, versions, "
               "cpu_count, each plant's plant_sha, module_sha256) and its wall_s (:1423) are provenance and time, "
               "not numbers of the plant; P moves every plant_sha by design, and engine_sha is checked apart (row 140 "
               "(1)). Neither is step 12a's (row 140 (1) replaces row 127 (1)'s 'ignoring only fields that step 12a "
               "adds')")
# Row 127 (1)'s allowance for step 12a: empty, since no number roads.json holds passes through step_record
# (evaluate.run_episode calls _record_step only with a record, evaluate.py:279-280; roads_ceiling.run_episode_record
# is its own loop, roads_ceiling.py:530; k3_knee.neutral_run calls run_episode without one); and C2, step 12a,
# is not built (row 146 (3)), so no field of step 12a's exists
ADDED_BY_STEP_12A = ()
# Of roads.json's 35 hashed files, the five row 140 (2) lets differ: P's four (row 138 (1)) and step_record.py,
# which C2 would have changed (C2 is not built, row 146 (3); the list stands as the row fixes it). Every other
# one keeps its recorded sha_text
MAY_DIFFER = ("engine_env.py", "engines.py", "evaluate.py", "fingerprint.py", "step_record.py")

# What roads.json holds that is not recomputed, each with the reason (the interface sheet, section 5)
NOT_RECOMPUTED = {
    "practice": "row 96: the practice set is default_rng([roads_seed, 0x50]); recomputing it would use roads_seed, "
                "an attempt",
    "tau": "row 102: each tau is computed once at the draw and read from the record (roads_ceiling.use_recorded_taus)",
    "roads": "the input: every number is recomputed from these arrays, and the scripted replacement loop must give "
             "them back exactly (section slots)",
    "hashes": "the draw's provenance (the preconditions compare it with the tree)",
    "attempts": "the draw's provenance", "steps_log": "the draw's provenance (its two arrays hashes are read)",
    "printed": "the draw's provenance", "printed_earlier": "the draw's provenance",
    "files_opened": "the draw's provenance (a file this run opens beyond it is refused)",
    "data_inputs": "the draw's provenance (the preconditions compare it with the tree)",
    "frozen_check": "the draw's provenance", "commit_reveal": "the draw's provenance: never read (row 96)",
    "started": "the draw's provenance", "finished": "the draw's provenance",
    "changed_during_run": "the draw's provenance",
}
# What the draw was asked for, read as given (first_draw's arguments, epa_roads.py:1431-1434)
RECORD_INPUTS = ("schema", "seed_kind", "engines", "ratios", "variants", "readings", "companions")
# The sections, in row 98's order, each logged before the next one runs (the interface sheet, section 5)
SECTIONS = ("reconstruction", "identities.locked_climb_b58", "identities.generated", "slots", "c5", "ceilings",
            "passes_T", "report", "identities.final", "cvt_diagnostic", "coverage", "episode_steps", "H_table",
            "design", "streams")
# The record keys the sections recompute (with the NOT_RECOMPUTED and RECORD_INPUTS keys, every key roads.json
# holds: a key that is none of them is refused, so nothing is left out unseen)
SECTION_KEYS = ("identities", "slots", "c5", "ceilings", "passes_T", "report", "cvt_diagnostic", "coverage",
                "episode_steps", "H_table", "design", "streams")
# A reading of redraws.json is a section "redraws.<name>", recomputed; every other key of the file is read, not
# recomputed, each with the reason and what checks it (redraws_problems). A key that is neither is refused
REDRAWS_NOT_RECOMPUTED = {
    "schema": "the record's form: checked to be epa_roads.REDRAWS_SCHEMA",
    "roads_sha": "the roads.json it redrew: checked to be this roads.json's",
    "seed_kind": "checked to be roads.json's",
    "margins": "the redraws' input, read from summary.json by epa_roads.margins_from_summary: checked bit for "
               "bit against that function on summary.json now and against the attempts log's redraw start line",
    "margins_source": "summary.json's path and sha_text: checked against summary.json now",
    "dropped": "the redraws' input, Run 2's section-7 drops: it sets each reading's gating (version 6 without "
               "them, version 5 with every engine); checked against summary.json (epa_roads.dropped_problems, the "
               "redraw's own refusal) and the attempts log's redraw start line",
    "started": "the redraws' provenance", "finished": "the redraws' provenance",
    "files_opened": "the redraws' provenance (a file this run opens beyond it and the draw's is refused)",
    "changed_during_run": "the redraws' provenance: checked empty",
    "taus_read_from_the_record": "checked to be roads.json's tau (row 102)",
    "steps_log": "the redraws' provenance",
}
# The SYNTHETIC smoke run redraws its first failing slot only (epa_roads.py:1708); the real redraws every
# failing slot (max_slots None, epa_roads.py:1991)
SYNTHETIC_REDRAW_SLOTS = 1
REAL_SHAPE = {"engines": R.ENGINES, "ratios": RC.RATIOS, "variants": R.DRAW_VARIANTS, "readings": R.DRAW_READINGS}
EXIT = {"EQUAL": 0, "DIFFERENT": 1, "REFUSED": 2}
EXIT_CRASH = 3
# The record's keys (the interface sheet, 12.4); a check result carries a few more, for the person reading it
RECORD_KEYS = ("schema", "row", "mode", "verdict", "partial", "roads_sha", "redraws_sha", "head", "pushed", "clean",
               "tree_changes", "started", "finished", "jobs", "env", "versions", "plants", "hashed_files",
               "contract_equal", "data_inputs_equal", "files_opened_new", "taus_read_from_the_record",
               "reconstruction", "sections", "ignored", "added_by_step_12a", "not_recomputed", "changed_during_run",
               "code", "supersedes", "steps_log")
_STEP2_HASH = re.compile(r"step 2, arrays generated: .* arrays sha256 ([0-9a-f]{64})$")
_STEP4A_HASH = re.compile(r"step 4a, .* final arrays sha256 ([0-9a-f]{64})$")


class NotRecorded(Exception):
    """A stream asked for a draw the record does not hold, or one it holds in another form: the code as it
    stands decides otherwise than the draw's did, and the section is DIFFERENT."""


# =====================================================================================================
# The scripted streams (row 96: no roads_seed)
# =====================================================================================================
class ScriptedRng:
    """A stand-in for numpy's Generator that hands back recorded draws in order: integers(lo, hi) an int and
    uniform(lo, hi) a float in [lo, hi), as numpy draws them. A draw of the wrong type, outside [lo, hi), or
    past the last recorded one raises NotRecorded, naming `label`. left() counts the draws not yet used."""

    def __init__(self, values, *, label):
        self._values = list(values)
        self._i = 0
        self.label = label

    def _next(self, want, lo, hi):
        if self._i >= len(self._values):
            raise NotRecorded(f"{self.label}: draw {self._i + 1} was asked for, the record holds {len(self._values)}")
        v = self._values[self._i]
        if type(v) is not want:
            raise NotRecorded(f"{self.label}: draw {self._i + 1} is recorded as {type(v).__name__} {v!r}, and the "
                              f"code asks for a {want.__name__}")
        if not lo <= v < hi:
            raise NotRecorded(f"{self.label}: draw {self._i + 1}, {v!r}, lies outside [{lo!r}, {hi!r})")
        self._i += 1
        return v

    def integers(self, lo, hi):
        return self._next(int, lo, hi)

    def uniform(self, lo, hi):
        return self._next(float, lo, hi)

    def left(self):
        return len(self._values) - self._i


@contextlib.contextmanager
def scripted_streams(record, redraws=None):
    """epa_roads.replacement_rng and redraw_rng (epa_roads.py:392-397) swapped, inside, for functions that
    give slot k's recorded grades: record['slots'][j]['candidates'][1:] for the 0x1D stream at the first draw
    (replacement_loop draws a grade per candidate after the first), and, when `redraws` is one reading of
    redraws.json (readings[name]), its slots' candidates' grades for the 0xC5 stream (redraw_slot draws one
    per candidate). Each asserts that it is called with roads_seed None: nothing here is seeded. Yields the
    list of streams made, so a caller can see what each left unused; the originals come back in finally."""
    first = {int(s["slot"]): [c["grade"] for c in s["candidates"][1:]] for s in record["slots"]}
    later = {} if redraws is None else {int(s["slot"]): [c["grade"] for c in s["candidates"]]
                                        for s in redraws["slots"]}
    made = []

    def replacement_rng(roads_seed, k):
        assert roads_seed is None, "the re-verification passes no roads_seed (row 96)"
        rng = ScriptedRng(first.get(int(k), []), label=f"slot {int(k)}'s replacement stream (0x1D)")
        made.append(rng)
        return rng

    def redraw_rng(roads_seed, k):
        assert roads_seed is None, "the re-verification passes no roads_seed (row 96)"
        rng = ScriptedRng(later.get(int(k), []), label=f"slot {int(k)}'s redraw stream (0xC5)")
        made.append(rng)
        return rng
    old = (R.replacement_rng, R.redraw_rng)
    R.replacement_rng, R.redraw_rng = replacement_rng, redraw_rng
    try:
        yield made
    finally:
        R.replacement_rng, R.redraw_rng = old


def _logged_hash(record, pattern, what):
    """The arrays hash one line of the draw's steps_log printed (epa_roads.py:1349-1350, :1363-1364): (hash or
    None, problems). Exactly one line must carry it."""
    hits = [m.group(1) for line in record.get("steps_log") or [] for m in [pattern.search(line)] if m]
    if len(hits) != 1:
        return None, [f"the steps_log holds {len(hits)} '{what}' lines with an arrays hash, not one"]
    return hits[0], []


def reconstruct_generated(record, *, root):
    """The generated roads, before the replacement loop, rebuilt from the record (generate()'s code path,
    epa_roads.py:342-357, without its default_rng(roads_seed)): each road's recorded draws through
    epa_roads.layout on a ScriptedRng, then epa_roads.make_road with road k's frozen seed and weights
    (evaluate.EPISODES as epa_roads.frozen_episodes reads it) and its first slot after the earlier roads'
    climbs, labelled as first_draw labels them (epa_roads.py:1346-1347). Returns (roads, problems): a road
    whose draws the layout does not consume exactly, whose seed, weights or label are not the record's, and
    arrays that do not hash to the steps_log's step-2 line, or a record whose roads do not hash to its step-4a
    line, are problems."""
    problems, roads, slot = [], [], 0
    eps = R.frozen_episodes(root=root)
    for i, rec_road in enumerate(record["roads"]):
        d = rec_road["draws"]
        values = ([d["lead_s"]] + [x for c in d["climbs"] for x in (c["L_s"], c["grade"], c["gap_s"])]
                  + [d["discarded"]["L_s"], d["discarded"]["grade"], d["discarded"]["gap_s"]])
        rng = ScriptedRng(values, label=f"road {i}'s first-draw stream")
        try:
            lead, climbs, discarded = R.layout(rng)
        except NotRecorded as exc:
            problems.append(f"road {i}: {exc}")
            continue
        if rng.left():
            problems.append(f"road {i}: the layout used {len(values) - rng.left()} of its {len(values)} recorded "
                            "draws (the fit rule decides otherwise)")
        if i >= len(eps):
            problems.append(f"road {i}: evaluate.EPISODES holds {len(eps)} episodes")
            continue
        seed, w = eps[i]
        road = R.make_road(k=i, episode_seed=seed, weights=w, lead=lead, climbs=climbs, discarded=discarded,
                           first_slot=slot)
        road["label"] = f"{record['seed_kind']} road {road['k']}"
        for key in ("k", "episode_seed", "weights", "label"):
            if road[key] != rec_road.get(key):
                problems.append(f"road {i}: {key} {road[key]!r} is not the record's {rec_road.get(key)!r}")
        slot += len(climbs)
        roads.append(road)
    step2, p2 = _logged_hash(record, _STEP2_HASH, "step 2")
    step4a, p4 = _logged_hash(record, _STEP4A_HASH, "step 4a")
    problems += p2 + p4
    if step2 is not None and len(roads) == len(record["roads"]) and R.arrays_sha256(roads) != step2:
        problems.append("the generated roads' arrays sha256 is not the steps_log's step-2 hash")
    if step4a is not None and R.arrays_sha256(record["roads"]) != step4a:
        problems.append("the record's roads' arrays sha256 is not the steps_log's step-4a hash")
    return roads, problems


def reconstruction_block(record, generated):
    """12.4's reconstruction: both arrays hashes beside the steps_log's, and whether both are equal."""
    step2, _ = _logged_hash(record, _STEP2_HASH, "step 2")
    step4a, _ = _logged_hash(record, _STEP4A_HASH, "step 4a")
    gen = R.arrays_sha256(generated) if len(generated) == len(record["roads"]) else None
    fin = R.arrays_sha256(record["roads"])
    return {"generated_arrays_sha256": gen, "steps_log_step2": step2, "final_arrays_sha256": fin,
            "steps_log_step4a": step4a, "equal": gen is not None and gen == step2 and fin == step4a}


# =====================================================================================================
# The comparison (row 140 (1): exact, the same type and the same float bits)
# =====================================================================================================
def _brief(x):
    if isinstance(x, dict):
        return f"<a dict of {len(x)} keys>"
    if isinstance(x, list):
        return f"<a list of {len(x)}>"
    if isinstance(x, str) and len(x) > 200:
        return x[:200] + "..."
    return x


def _under(path, roots):
    return any(path[:len(q)] == q for q in roots)


def _walk(a, b, path, acc, ignore, added_ok):
    def differ(at, old, new):
        acc["differences"] += 1
        if len(acc["first"]) < MAX_REPORTED:
            acc["first"].append({"path": list(at), "at_draw": _brief(old), "now": _brief(new)})
    if path in ignore:
        return
    if type(a) is not type(b):
        acc["values"] += 1
        differ(path, a, b)
        return
    if isinstance(a, dict):
        for k in a:
            if k not in b:
                if path + (k,) not in ignore:
                    differ(path + (k,), a[k], "<missing>")
            else:
                _walk(a[k], b[k], path + (k,), acc, ignore, added_ok)
        for k in b:
            if k not in a and path + (k,) not in ignore and not _under(path + (k,), added_ok):
                differ(path + (k,), "<missing>", b[k])
        return
    if isinstance(a, list):
        if len(a) != len(b):
            differ(path, a, b)
        for i, (x, y) in enumerate(zip(a, b)):
            _walk(x, y, path + (i,), acc, ignore, added_ok)
        return
    acc["values"] += 1
    if isinstance(a, float):
        if struct.pack("<d", a) != struct.pack("<d", b):
            differ(path, a, b)
    elif a != b:
        differ(path, a, b)


def compare(old, new, *, path=(), ignore=IGNORED_PATHS, added_ok=ADDED_BY_STEP_12A):
    """The recorded value `old` (at `path` in the record) against the recomputed `new`: {'values': leaves
    compared, 'differences': how many differ, 'first': up to 50 of them as {path, at_draw, now}}. The new
    side goes through json.loads(json.dumps(x, allow_nan=False)) first, as the record went through
    write_once (a value that cannot is one difference). Types must match exactly (1 and 1.0 differ, True and
    1 differ); floats are compared as struct.pack('<d', x) (-0.0 and 0.0 differ); dicts both ways (a key
    missing on either side differs, unless an added key lies under added_ok); lists by length, then item by
    item. A path in `ignore` is skipped."""
    try:
        new = json.loads(json.dumps(new, allow_nan=False))
    except (TypeError, ValueError) as exc:
        return {"values": 0, "differences": 1,
                "first": [{"path": list(path), "at_draw": _brief(old), "now": f"not JSON as a record holds it ({exc})"}]}
    acc = {"values": 0, "differences": 0, "first": []}
    _walk(old, new, tuple(path), acc, {tuple(p) for p in ignore}, {tuple(p) for p in added_ok})
    return acc


def _merged(*results, problems=()):
    out = {"values": 0, "differences": 0, "first": []}
    for r in results:
        out["values"] += r["values"]
        out["differences"] += r["differences"]
        out["first"] += r["first"]
    for p in problems:
        out["differences"] += 1
        out["first"].append({"path": ["problem"], "at_draw": None, "now": p})
    out["first"] = out["first"][:MAX_REPORTED]
    return out


# =====================================================================================================
# The preconditions (row 140 (2))
# =====================================================================================================
def bytecode_caches(files, *, root):
    """Every compiled file Python could load in place of a code file's source: __pycache__/<stem>.*.pyc beside
    each .py of `files`, repository-relative (epa_tightenings.bytecode_caches, epa_tightenings.py:891-906,
    written here because epa_tightenings imports validate_epa). python -B stops Python writing them, not
    reading them. It looks in no other folder: the caches inside .venv (frozen, row 146 (8)) are never
    looked at, since no hashed file or closure module lies there (epa_roads.import_closure follows the
    project's own modules only), so the venv's caches are not refused and need not be deleted."""
    out = []
    for f in files:
        if not f.endswith(".py"):
            continue
        d, name = os.path.split(os.path.join(root, *f.split("/")))
        cache = os.path.join(d, "__pycache__")
        if not os.path.isdir(cache):
            continue
        stem = name[:-3] + "."
        out += [os.path.relpath(os.path.join(cache, c), root).replace(os.sep, "/") for c in sorted(os.listdir(cache))
                if c.startswith(stem) and c.endswith(".pyc")]
    return sorted(out)


def _sha_now(root, rel):
    from thresholds import common
    p = os.path.join(root, *rel.split("/"))
    return common.sha_text(p) if os.path.isfile(p) else None


def code_files(*, root):
    """This module and every project module it imports at any depth (epa_roads.import_closure)."""
    return R.import_closure(MODULE_REL, root=root)


def _inside_work_tree(path):
    p = os.path.abspath(path)
    while not os.path.isdir(p):
        parent = os.path.dirname(p)
        if parent == p:
            return False
        p = parent
    r = subprocess.run(["git", "-C", p, "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    return r.returncode == 0 and r.stdout.strip() == "true"


def out_problems(out_dir, *, root):
    """check's --out (the interface sheet, section 5): a folder outside every git work tree, root's included,
    that holds no earlier reverify_CHECK.json (a check result is written once), and whose result path the audit
    guards let open (an --out whose path holds logs/epa, epa_validation or data/engines/<id>/epa_ would be
    refused only at the write, after the whole run: the fix review, 7 November). [] when it may be written."""
    if out_dir is None:
        return ["check writes its result under --out DIR"]
    probs = []
    if _inside_work_tree(out_dir) or os.path.normcase(os.path.abspath(out_dir)).startswith(
            os.path.normcase(os.path.abspath(root)) + os.sep):
        probs.append(f"--out {out_dir} lies inside a git work tree: a check writes outside every one")
    if os.path.exists(os.path.join(out_dir, CHECK_NAME)):
        probs.append(f"--out {out_dir} holds a {CHECK_NAME} already: a check result is written once")
    target = os.path.join(out_dir, CHECK_NAME)
    if R.refused_path(target) or R.refused_path(target + ".partial"):    # roads_ceiling._forbidden is the same test
        probs.append(f"--out {out_dir} is a path the audit guards refuse to open (epa_roads.refused_path): the "
                     "result could not be written after the run")
    return probs


def _is_committed_record(record, *, root):
    """Whether `record` is what root's results/EPA_ROADS/roads.json holds: the committed-record checks run on
    that one; a record a test passes is no record of the tree, and its result is partial."""
    p = os.path.join(root, *R.ROADS_REL.split("/"))
    return os.path.isfile(p) and R.load_record(p) == record


def _git_state(root):
    """(HEAD or None, clean or None): None where root is no git work tree (a test's copy)."""
    try:
        head, clean, _ = R.tree_state(root)
    except R.Refused:
        return None, None
    return head, clean


def _episodes_of(text):
    """evaluate.EPISODES from evaluate.py's text, read as epa_roads.frozen_episodes reads the file
    (epa_roads.py:265-274: the literal, through ast.literal_eval, nothing imported)."""
    for node in ast.parse(text).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == "EPISODES" for t in node.targets):
            return tuple((int(s), tuple(float(x) for x in w)) for s, w in ast.literal_eval(node.value))
    raise KeyError("evaluate.py holds no EPISODES literal")


def draw_episodes(record, *, root):
    """evaluate.EPISODES whole, as the draw read it (epa_roads.generate reads the whole literal and pairs road
    k with entry k, epa_roads.py:342-357): (episodes, None), or (None, why) when it cannot be read. The
    tree's when evaluate.py's sha_text is roads.json's; otherwise (P edits evaluate.py, row 138 (1)) the
    newest version of evaluate.py in HEAD's history whose sha_text (blob_sha_text) is roads.json's. Outside
    a git work tree, or when no committed version has that sha_text, the draw's tuple cannot be read whole,
    and that is refused."""
    rel = "evaluate.py"
    want = record["hashes"]["files"].get(rel)
    if want is not None and _sha_now(root, rel) == want:
        return R.frozen_episodes(root=root), None
    r = subprocess.run(["git", "log", "--full-history", "--format=%H", "HEAD", "--", rel], cwd=root,
                       capture_output=True, text=True)
    for commit in (r.stdout.split() if r.returncode == 0 else []):
        if blob_sha_text(commit, rel, root=root) == want:
            blob = subprocess.run(["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=root, capture_output=True)
            try:
                return _episodes_of(blob.stdout.replace(b"\r\n", b"\n").decode("utf-8")), None
            except (KeyError, SyntaxError, ValueError, UnicodeDecodeError) as exc:
                return None, (f"the draw's evaluate.py ({commit}) holds no EPISODES that can be read "
                              f"({type(exc).__name__}: {exc})")
    return None, ("evaluate.py is not the draw's, and no version of it in HEAD's history has roads.json's sha_text: "
                  "evaluate.EPISODES cannot be compared whole with the draw's (row 140 (2))")


def preconditions(record, *, root, mode, out_dir):
    """Every refusal of row 140 (2) and of the mode, checked before anything runs: (problems, context), the
    context holding what the record names of the tree (12.4: env, versions, plants, hashed_files,
    contract_equal, data_inputs_equal, taus_read_from_the_record, code, head, clean, pushed, tree_changes,
    roads_sha, redraws_sha). mode 'check' needs out_dir outside every git work tree and no earlier
    reverify_CHECK.json there; mode 'record' a clean tree whose HEAD is in origin's GRA-test."""
    import engines as ENG
    import epa_freeze
    import engine_env as E
    probs, ctx = [], {}
    h = record["hashes"]
    engines = tuple(record["engines"])
    # what the record is: every key recomputed, read as given or named as not recomputed
    known = set(SECTION_KEYS) | set(NOT_RECOMPUTED) | set(RECORD_INPUTS)
    probs += [f"roads.json holds {k!r}, which this module neither recomputes nor names (NOT_RECOMPUTED)"
              for k in sorted(set(record) - known)]
    probs += [f"roads.json holds no {k!r}" for k in SECTION_KEYS + ("roads", "tau", "hashes") if k not in record]
    # the environment: threads, -B, the versions (row 126; row 140 (2))
    ctx["env"] = {"OMP_NUM_THREADS": os.environ.get("OMP_NUM_THREADS"),
                  "MKL_NUM_THREADS": os.environ.get("MKL_NUM_THREADS"), "python_B": bool(sys.dont_write_bytecode)}
    for k in ("OMP_NUM_THREADS", "MKL_NUM_THREADS"):
        if ctx["env"][k] != "1":
            probs.append(f"{k} is {ctx['env'][k]!r}, not '1' (rows 118, 126)")
    if not ctx["env"]["python_B"]:
        probs.append("Python runs without -B: run it as `.venv/Scripts/python.exe -B` (rule 1.10)")
    ctx["versions"] = epa_freeze.versions()
    probs += [f"versions.{k} {ctx['versions'].get(k)!r} is not roads.json's {v!r} (row 126; row 140 (2))"
              for k, v in sorted(h["versions"].items()) if ctx["versions"].get(k) != v]
    probs += [f"versions.{k} {v!r} is not in roads.json's versions" for k, v in sorted(ctx["versions"].items())
              if k not in h["versions"]]
    # the 35 hashed files: only MAY_DIFFER may differ (row 140 (2))
    now = {f: _sha_now(root, f) for f in sorted(h["files"])}
    changed = sorted(f for f, s in now.items() if s != h["files"][f])
    probs += [f"{f}: missing (roads.json hashes it)" for f in changed if now[f] is None]
    probs += [f"{f}: its sha_text is not roads.json's, and only {', '.join(MAY_DIFFER)} may differ (row 140 (2))"
              for f in changed if now[f] is not None and f not in MAY_DIFFER]
    ctx["hashed_files"] = {"may_differ": list(MAY_DIFFER), "changed_since_draw": changed, "sha_text_now": now}
    try:
        closure = set(R.hashed_files(root=root, engines=tuple(h["plants"])))
    except R.Refused as exc:
        probs += [f"the import closure: {p}" for p in exc.args[0]]
    else:
        probs += [f"{f}: reached by the code as it stands, not hashed by roads.json" for f in sorted(closure - set(h["files"]))]
        probs += [f"{f}: hashed by roads.json, no longer reached by the code" for f in sorted(set(h["files"]) - closure)]
    contract = {f: _sha_now(root, f) for f in sorted(h["contract"])}
    ctx["contract_equal"] = contract == h["contract"]
    probs += [f"{f}: the contract's sha_text is not roads.json's" for f in sorted(h["contract"]) if contract[f] != h["contract"][f]]
    data = record.get("data_inputs") or {}
    data_now = {f: _sha_now(root, f) for f in sorted(data)}
    ctx["data_inputs_equal"] = data_now == data
    probs += [f"{f}: the data input's sha_text is not roads.json's" for f in sorted(data) if data_now[f] != data[f]]
    # evaluate.EPISODES, read as text (epa_roads.frozen_episodes), pairs every road with its seed and weights,
    # and is the whole tuple the draw read (draw_episodes): its length and every entry, those no road uses too
    try:
        eps = R.frozen_episodes(root=root)
    except (OSError, KeyError, SyntaxError, ValueError) as exc:
        probs.append(f"evaluate.EPISODES cannot be read ({type(exc).__name__}: {exc})")
    else:
        unpaired = set()
        for i, r in enumerate(record.get("roads") or []):
            if i >= len(eps) or (r.get("episode_seed"), r.get("weights")) != (eps[i][0], [float(w) for w in eps[i][1]]):
                probs.append(f"road {i}: its episode seed and weights are not evaluate.EPISODES[{i}]")
                unpaired.add(i)
        drawn, why = draw_episodes(record, root=root)
        if why:
            probs.append(why)
        else:
            if len(eps) != len(drawn):
                probs.append(f"evaluate.EPISODES holds {len(eps)} episodes, and the draw's held {len(drawn)}: the "
                             "whole tuple is the draw's (row 140 (2))")
            probs += [f"evaluate.EPISODES[{i}] is not the draw's" for i in range(min(len(eps), len(drawn)))
                      if eps[i] != drawn[i] and i not in unpaired]
    # the plants: engine_sha unchanged (row 127 (1)), each EPA engine's its complete.json's (row 94); the
    # plant_sha now, which P moves by design, recorded beside the draw's
    from thresholds import common
    ctx["plants"] = {}
    for e in engines:
        es_now = ENG.engine_sha(R.plant_of(e))
        cj = None
        if e in R.EPA_ENGINES:
            cp = os.path.join(root, R.CALIBRATION_REL, e, "complete.json")
            cj = common.load_json(cp).get("engine_sha") if os.path.isfile(cp) else None
            if es_now != cj:
                probs.append(f"{e}: engine_sha {es_now} is not its complete.json's {cj} (row 94)")
        ctx["plants"][e] = {"plant_sha_at_draw": h["plants"][e]["plant_sha"], "plant_sha_now": epa_freeze.plant_sha(e),
                            "engine_sha_at_draw": h["plants"][e]["engine_sha"], "engine_sha_now": es_now,
                            "engine_sha_complete_json": cj}
        if es_now != h["plants"][e]["engine_sha"]:
            probs.append(f"{e}: engine_sha {es_now} is not roads.json's {h['plants'][e]['engine_sha']} (row 127 (1))")
    # tau read from the record (row 102)
    taus = record.get("tau") or {}
    ctx["taus_read_from_the_record"] = {e: taus[e]["tau_s"] for e in engines if isinstance(taus.get(e), dict)
                                        and type(taus[e].get("tau_s")) is float}
    probs += [f"roads.json holds no tau for {e} (row 102: it is read from the record)" for e in engines
              if e not in ctx["taus_read_from_the_record"]]
    # the one road shape the roads share with the plant, as first_draw checks it before anything else
    # (epa_roads.py:1316): an engine_env whose ramp or make_grade_climb moved is refused here, not crashed on
    try:
        R.check_engine_env()
    except AssertionError as exc:
        probs.append(f"{exc} (epa_roads.check_engine_env, which the draw ran first)")
    # from P on (row 140 (2)): the defaults the record was drawn under; the re-verifier passes neither option.
    # Read by name, since before P engine_env holds neither (test_engine_threading.Names scans E.<name> reads)
    knock = getattr(E, "REWARD_KNOCK_DEFAULT", None)
    if hasattr(E, "REWARD_KNOCK_DEFAULT") and knock is not True:
        probs.append(f"engine_env.REWARD_KNOCK_DEFAULT is {knock!r}, not True (row 117)")
    if hasattr(E, "preview_samples") or hasattr(E, "PREVIEW_H_S"):
        try:
            same = tuple(getattr(E, "preview_samples")(getattr(E, "PREVIEW_H_S"))) == tuple(E.PREVIEW_S)
        except (AttributeError, TypeError, ValueError) as exc:
            same = False
            probs.append(f"engine_env's H default cannot be read ({type(exc).__name__}: {exc})")
        if not same:
            probs.append("engine_env.preview_samples(PREVIEW_H_S) is not PREVIEW_S: the record was drawn at H = 30 s "
                         "(row 117)")
    # this module and its closure, and no bytecode beside any code file
    try:
        code = code_files(root=root)
    except (OSError, R.Refused) as exc:
        code = []
        probs.append(f"{MODULE_REL}'s import closure cannot be read under {root} ({type(exc).__name__}: {exc})")
    ctx["code"] = {f: _sha_now(root, f) for f in code}
    caches = bytecode_caches(sorted(set(h["files"]) | set(code)), root=root)
    probs += [f"{c}: a bytecode cache beside a hashed file; delete it and run with -B (rule 1.10)" for c in caches]
    # the records
    roads_path = os.path.join(root, *R.ROADS_REL.split("/"))
    red_path = os.path.join(root, *R.REDRAWS_REL.split("/"))
    committed = _is_committed_record(record, root=root)
    ctx["record_source"] = R.ROADS_REL if committed else "passed by a test: not the tree's roads.json"
    ctx["roads_sha"] = R.roads_sha(roads_path) if committed else None
    ctx["redraws_sha"] = _sha_now(root, R.REDRAWS_REL) if committed else None
    if committed:
        probs += record_problems(record, root=root)
    elif mode == "record":
        probs.append("record mode re-verifies the tree's own roads.json only")
    # the tree and the mode
    head, clean = _git_state(root)
    pushed = False
    if head is not None:
        pushed, _, why = R.remote_state(root, head)
    ctx.update(head=head, clean=clean, pushed=pushed)
    # git answers only for paths inside the work tree: a record's inputs are repository-relative, and a test's
    # SYNTHETIC stand-ins for the contract, named by absolute path outside it, are hashed above instead
    inputs = sorted(f for f in set(h["files"]) | set(h["contract"]) | set(data) | set(code) | {R.ROADS_REL}
                    | ({R.REDRAWS_REL} if os.path.isfile(red_path) else set()) if not os.path.isabs(f))
    ctx["tree_changes"] = []
    if head is not None:
        import epa_freeze as EF
        _, dirty = EF.git_clean(inputs, root=root)
        ctx["tree_changes"] = [{"path": p, "sha_text": _sha_now(root, p)} for p in dirty]
    if mode == "check":
        probs += out_problems(out_dir, root=root)
    elif mode == "record":
        if head is None or not clean:
            probs.append("record mode needs a clean tree (git status shows changes or untracked files)")
        if head is not None and not pushed:
            probs.append(why)
        ctx["tree_changes"] = []
    else:
        probs.append(f"mode {mode!r} is neither check nor record")
    return probs, ctx


def _attempts(root):
    p = os.path.join(root, *R.ATTEMPTS_REL.split("/"))
    return R.read_attempts(p) if os.path.isfile(p) else []


def _redraws_outcomes(root):
    """The attempts log's redraw lines that wrote a redraws.json: [(start line or None, outcome line)], each
    outcome 'redraws' paired with the start line of its attempt number (epa_roads.recheck_or_redraw)."""
    lines = [x for x in _attempts(root) if x.get("step") == "redraw"]
    starts = [x for x in lines if x.get("event") == "start"]
    out = []
    for o in (x for x in lines if x.get("event") == "outcome" and x.get("outcome") == "redraws"):
        mine = [s for s in starts if s.get("attempt") == o.get("attempt")]
        out.append((mine[0] if len(mine) == 1 else None, o))
    return out


def record_problems(record, *, root):
    """The committed record's own refusals: roads.json committed at HEAD and in one commit (written once, row
    97); a REAL one named by the attempts log's one draw outcome (as epa_tightenings.real_problems,
    epa_tightenings.py:946-951) and asking for the whole of row 103 (1); redraws.json, when it exists, as
    redraws_problems refuses it, and, for a REAL record whose attempts log holds a redraws outcome (R4),
    required: without it the redraws' readings would go unchecked."""
    import epa_freeze
    probs = []
    path = os.path.join(root, *R.ROADS_REL.split("/"))
    sha = R.roads_sha(path)
    if not epa_freeze.committed_at_head(R.ROADS_REL, root=root):
        probs.append(f"{R.ROADS_REL} is not committed at HEAD")
    if len(R.committed_versions(root, R.ROADS_REL)) != 1:
        probs.append(f"{R.ROADS_REL} is not committed in exactly one commit: it is written once (row 97)")
    if record["seed_kind"] == "REAL":
        outs = [x for x in _attempts(root)
                if x.get("step", "draw") == "draw" and x.get("event") == "outcome" and x.get("outcome") == "roads"]
        if len(outs) != 1 or outs[0].get("roads_sha") != sha:
            probs.append(f"the attempts log does not name this roads.json's roads_sha in its one roads outcome")
        for key, want in REAL_SHAPE.items():
            if sorted(record[key]) != sorted(want):
                probs.append(f"a REAL record asks for {key} {tuple(want)} (row 103 (1)), not {tuple(record[key])}")
        if record["companions"] is not True:
            probs.append("a REAL record computes the companions (row 103 (1))")
    red = os.path.join(root, *R.REDRAWS_REL.split("/"))
    if os.path.isfile(red):
        probs += redraws_problems(record, R.load_record(red), root=root)
    elif record["seed_kind"] == "REAL" and _redraws_outcomes(root):
        probs.append(f"the attempts log holds a redraws outcome (R4) and {R.REDRAWS_REL} does not exist: every "
                     "reading of it is re-verified (row 140 (1))")
    return probs


@contextlib.contextmanager
def summary_opened(root):
    """Inside, epa_roads' audit guard lets open exactly <root>/results/EPA_VALIDATION/summary.json, its one
    exception (epa_roads.summary_path_allowed), as epa_roads' main installs it for recheck and redraw; after,
    nothing it refuses, as this module's main installs it (install_guard(())). Yields the path.

    roads_ceiling has a guard of its own (roads_ceiling.py:178-221), which refuses the same file with no
    exception, and it stays installed for the rest of the process once one of its runs goes in-process
    (roads_ceiling.execute with one task to do, or jobs 1, :692-694; tau_s for a tau not recorded, :474).
    Section 'report' does that at any --jobs: use_recorded_taus (recompute) holds every frozen tau, so
    roads_ceiling.report's tau pairs (:1391-1392) leave one to run, the one-housing Ford's, a single task
    (:735). After it, the second read of summary.json, _provenance_now's after the recomputation, was
    refused, so `record` and a `check` without --skip-companions (P's gate's) would have ended in CRASH after
    the whole run. Found by RV's gate on the main tree (7 November), which refused the first reads and the
    writes of summary.json in six tests of test_roads_reverify, run after an earlier class had installed that
    guard in the same process; the second read was then found by reading reverify. Its hook looks up
    roads_ceiling._forbidden at each open (:209), so inside this block the name is bound to the same test but
    for this one path, and it is put back after. The open is not left in roads_ceiling.OPENED, as when that
    guard is not installed; epa_roads' hook still adds it to epa_roads.OPENED, so files_opened lists it either
    way (redraws.json's files_opened does). roads_ceiling.py itself is unchanged (roads.json hashes it)."""
    path = R.summary_path_allowed(os.path.join(root, *R.SUMMARY_REL.split("/")), root=root)
    one = os.path.normcase(os.path.abspath(path))
    forbidden, noted = RC._forbidden, set(RC.OPENED)

    def _forbidden_but_the_summary(p):
        try:
            if os.path.normcase(os.path.abspath(os.fsdecode(p))) == one:
                return False
        except (TypeError, ValueError):
            pass
        return forbidden(p)

    R.install_guard((path,))
    RC._forbidden = _forbidden_but_the_summary
    try:
        yield path
    finally:
        RC._forbidden = forbidden
        RC.OPENED.intersection_update(noted)
        R.install_guard(())


def summary_sha(root):
    """summary.json's sha_text, read through summary_opened, or None when it does not exist."""
    with summary_opened(root) as path:
        return _sha_now(root, R.SUMMARY_REL) if os.path.isfile(path) else None


def redraws_problems(record, rd, *, root):
    """redraws.json's own refusals (rows 95 (2), 97; row 140 (2)'s "every data input unchanged", read for
    its one data input), [] when its readings may be re-verified: committed at HEAD in one commit; its schema
    epa_roads.REDRAWS_SCHEMA; its roads_sha this roads.json's, its seed_kind and taus roads.json's; every key a
    reading or named in REDRAWS_NOT_RECOMPUTED; 'dropped' a sorted list of the record's EPA engines, the B58
    never among them; its readings exactly those epa_roads.redraw writes for it (redraw_readings); a margin
    for every engine, the B58's at C5_MARGIN (epa_roads.margins_from_summary); changed_during_run empty;
    summary.json, opened through summary_opened, the sha_text margins_source names, giving its margins bit for
    bit and dropping exactly its dropped engines (epa_roads.dropped_problems, the redraw's own refusal); and,
    for a REAL record, the attempts log's one redraws outcome naming its sha_text, after its start line, which
    holds the same roads_sha, margins (bit for bit), dropped list and summary."""
    import epa_freeze
    from thresholds import common
    probs, name = [], R.REDRAWS_REL
    if not epa_freeze.committed_at_head(name, root=root):
        probs.append(f"{name} is not committed at HEAD")
    if len(R.committed_versions(root, name)) != 1:
        probs.append(f"{name} is not committed in exactly one commit: it is written once (row 97)")
    sha = R.roads_sha(os.path.join(root, *R.ROADS_REL.split("/")))
    if rd.get("roads_sha") != sha:
        probs.append(f"{name} names roads_sha {rd.get('roads_sha')!r}, not this roads.json's")
    if rd.get("schema") != R.REDRAWS_SCHEMA:
        probs.append(f"{name}'s schema is {rd.get('schema')!r}, not {R.REDRAWS_SCHEMA!r}")
    if rd.get("seed_kind") != record["seed_kind"]:
        probs.append(f"{name}'s seed_kind is {rd.get('seed_kind')!r}, not roads.json's {record['seed_kind']!r}")
    # every key recomputed (its readings) or named as read (REDRAWS_NOT_RECOMPUTED), as for roads.json
    probs += [f"{name} holds {k!r}, which this module neither recomputes nor names (REDRAWS_NOT_RECOMPUTED)"
              for k in sorted(set(rd) - set(REDRAWS_NOT_RECOMPUTED) - {"readings"})]
    probs += [f"{name} holds no {k!r}" for k in sorted(set(REDRAWS_NOT_RECOMPUTED) | {"readings"}) if k not in rd]
    engines = tuple(record["engines"])
    dropped = rd.get("dropped")
    if isinstance(dropped, list) and R.NEVER_DROPPED in dropped:
        probs.append(f"{name} drops the B58, which is never dropped (MD:1587-1592)")
    if not (isinstance(dropped, list) and all(isinstance(e, str) for e in dropped)
            and dropped == sorted(set(dropped)) and all(e in R.EPA_ENGINES and e in engines for e in dropped)):
        probs.append(f"{name}'s dropped {dropped!r} is not a sorted list of the record's EPA engines")
        dropped = []
    want = [n for n, _ in redraw_readings(record, dict(rd, dropped=dropped))]
    if sorted(rd.get("readings") or {}) != sorted(want):
        probs.append(f"{name} holds the readings {sorted(rd.get('readings') or {})}, and epa_roads.redraw writes "
                     f"{want} for dropped {dropped}")
    margins = rd.get("margins") if isinstance(rd.get("margins"), dict) else {}
    if sorted(margins) != sorted(engines) or (R.NEVER_DROPPED in margins and margins[R.NEVER_DROPPED] != R.C5_MARGIN):
        probs.append(f"{name}'s margins are not one per engine with the B58's at {R.C5_MARGIN}")
    if rd.get("changed_during_run") != []:
        probs.append(f"{name}'s changed_during_run is {rd.get('changed_during_run')!r}, not []")
    taus = {e: (record.get("tau") or {}).get(e, {}).get("tau_s") for e in engines}
    if compare(taus, rd.get("taus_read_from_the_record"))["differences"]:
        probs.append(f"{name}'s taus_read_from_the_record are not roads.json's tau (row 102)")
    # its one data input, summary.json (row 140 (2), as for roads.json's data inputs)
    src = rd.get("margins_source") if isinstance(rd.get("margins_source"), dict) else {}
    if src.get("path") != R.SUMMARY_REL:
        probs.append(f"{name}'s margins_source names {src.get('path')!r}, not {R.SUMMARY_REL}")
    try:
        with summary_opened(root) as path:
            if not os.path.isfile(path):
                raise OSError(f"{R.SUMMARY_REL} does not exist")
            now = common.sha_text(path)
            summary = common.load_json(path)
    except (OSError, ValueError, R.Refused) as exc:
        probs.append(f"{R.SUMMARY_REL}, the redraws' one data input, cannot be read ({type(exc).__name__}: {exc})")
    else:
        if src.get("sha_text") != now:
            probs.append(f"{R.SUMMARY_REL}'s sha_text is not the one {name}'s margins_source names: the redraws' "
                         "data input changed (row 140 (2))")
        try:
            got = R.margins_from_summary(summary, engines=engines)
            drops = R.dropped_problems(summary, dropped)
        except (R.Refused, KeyError, TypeError, ValueError, AttributeError) as exc:
            probs.append(f"{R.SUMMARY_REL} gives no margins or drops ({type(exc).__name__}: {exc})")
        else:
            if compare(margins, got)["differences"]:
                probs.append(f"{name}'s margins are not epa_roads.margins_from_summary({R.SUMMARY_REL}) bit for bit")
            probs += [f"{name}'s dropped: {p}" for p in drops]
    if record["seed_kind"] == "REAL":
        outs = _redraws_outcomes(root)
        here = common.sha_text(os.path.join(root, *name.split("/")))
        if len(outs) != 1 or outs[0][1].get("sha_text") != here:
            probs.append(f"the attempts log does not name this {name}'s sha_text in its one redraws outcome")
        elif outs[0][0] is None:
            probs.append(f"the attempts log holds no one start line for the redraws outcome's attempt")
        else:
            start = outs[0][0]
            if start.get("roads_sha") != sha or start.get("dropped") != rd.get("dropped") \
                    or start.get("summary") != rd.get("margins_source") \
                    or compare(start.get("margins"), margins)["differences"]:
                probs.append(f"the attempts log's redraw start line does not hold {name}'s roads_sha, dropped, "
                             "summary and margins")
    return probs


# =====================================================================================================
# The recomputation, in row 98's order
# =====================================================================================================
def _identities(roads, *, engines, jobs, keep):
    """The identity on every engine's arrays of every road, keyed {road k: {engine: result}}, the files each
    worker opened merged into the module's list: epa_roads.identities (epa_roads.py:795-807) without its
    stop, so that an identity that no longer holds is a difference here, not a crash."""
    res = R.pool_map(R._identity_task, [(e, r, keep) for r in roads for e in engines], jobs=jobs)
    out = {}
    for x in res:
        R.OPENED.update(x.pop("opened"))
        out.setdefault(str(x["road"]), {})[x["engine"]] = x
    return out


def _without_arrays(ident):
    return {k: {e: {kk: vv for kk, vv in x.items() if kk != "arrays"} for e, x in road.items()}
            for k, road in ident.items()}


def _reported(final, fin_id, *, engines, plants):
    """What first_draw reports beside the identities and discards nothing (epa_roads.py:1381-1398, the loop
    as written): decision 40's diagnostic on the Honda's car and each EPA engine's coverage flags on every
    scored climb, from the final identities' neutral runs, and the CVT totals."""
    from thresholds import common
    contract = common.load_json(common.CONTRACT_JSON)
    cvt, cov = {}, {}
    for i, slot in R.slots_of(final):
        if slot.get("flat"):
            continue
        road = final[i]
        for e in engines:
            run = fin_id[str(road["k"])][e]["arrays"]
            if e == R.CVT_ENGINE:
                steps, _ = R.c5_on_car(plants[e], road, slot, margin=R.C5_MARGIN)
                cvt[str(slot["slot"])] = R.cvt_diagnostics(plants[e], road, slot, steps, run, margin=R.C5_MARGIN)
            if e in R.EPA_ENGINES:
                cov.setdefault(e, {})[str(slot["slot"])] = R.coverage_flags(
                    e, road, slot, run, coverage=contract["engines"][e]["coverage"])
    return ({R.CVT_ENGINE: cvt, "totals": R.cvt_totals(cvt.values())} if R.CVT_ENGINE in engines else None), cov


def redraw_readings(record, redraws):
    """The readings redraws.json must hold, as epa_roads.redraw builds them (epa_roads.py:1871-1872): version
    6 with the recorded drops out of the gating, and, when an engine was dropped, version 5's reading with
    every engine gating. [(name, gating)]."""
    engines = tuple(record["engines"])
    dropped = tuple(redraws.get("dropped") or ())
    return ([("version 6", set(engines) - set(dropped))]
            + ([("version 5 (every engine gating)", set(engines))] if dropped else []))


def _redraw_reading(record, redraws, name, gating, *, plants, jobs, log):
    """One reading of redraws.json recomputed: epa_roads.redraw's loop (epa_roads.py:1876-1888) on a copy of
    the record's roads, at redraws.json's recorded margins, without its verify_record (:1858) and without
    roads_seed (:1869): every redraw_slot runs under scripted 0xC5 streams of the reading's own candidates."""
    reading = (redraws.get("readings") or {}).get(name) or {"slots": []}
    roads = copy.deepcopy(record["roads"])
    margins = redraws["margins"]
    with scripted_streams(record, reading):
        rc, failing = R.recheck_slots(roads, margins=margins, plants=plants, gating=gating, jobs=jobs)
        log(f"{name}: re-check on every car; slots failing: {failing}")
        todo = failing if record["seed_kind"] == "REAL" else failing[:SYNTHETIC_REDRAW_SLOTS]
        slots = []
        for i, slot in R.slots_of(roads):
            if slot["slot"] in todo:
                slots.append(R.redraw_slot(roads, i, slot, roads_seed=None, plants=plants, gating=gating,
                                           margins=margins, kept_recheck=rc[str(slot["slot"])], jobs=jobs, RC=RC,
                                           log=log))
    return {"gating": sorted(gating), "recheck": rc, "failing": failing, "slots": slots, "roads": roads}


def all_sections(record, redraws=None):
    """Every section name a full run computes for this record: SECTIONS, then one per reading of redraws."""
    out = list(SECTIONS)
    if redraws is not None:
        out += [f"redraws.{name}" for name, _ in redraw_readings(record, redraws)]
    return out


def recompute(record, *, root, jobs, log, sections, keep_going, redraws=None):
    """Every section of `sections` (all_sections when None) recomputed in row 98's order and compared with the
    record as it is computed, each logged before the next starts: {'sections': {name: compare result},
    'reconstruction': 12.4's block, 'not_run': [names], 'stopped_at': name or None}. Fail-fast: the first
    section with a difference stops the rest unless keep_going. A NotRecorded, or a coding-defect stop
    inside epa_roads (an identity that fails on a redrawn climb), ends its section as DIFFERENT, named.
    Every number after the reconstruction is computed from the record's own roads (row 127 (1)); the
    replacement loop's final roads are compared with them (section slots)."""
    want = all_sections(record, redraws) if sections is None else list(sections)
    full = all_sections(record, redraws)
    unknown = [s for s in want if s not in full]
    if unknown:
        raise ValueError(f"unknown sections {unknown}; this record has {full}")
    want = [s for s in full if s in want]                  # always row 98's order
    engines = tuple(record["engines"])
    R.check_engine_env()
    log(f"check_engine_env: the road shape is make_grade_climb's, ramp {R.RAMP_S} s")
    RC.use_recorded_taus({e: (float(record["tau"][e]["tau_s"]), record["tau"][e].get("cell")) for e in engines})
    log("tau read from roads.json for " + ", ".join(f"{e} {record['tau'][e]['tau_s']!r} s" for e in engines)
        + " (row 102)")
    plants = {e: R.plant_of(e) for e in engines}
    roads = copy.deepcopy(record["roads"])
    st = {}

    def generated():
        if "generated" not in st:
            st["generated"], st["reconstruction_problems"] = reconstruct_generated(record, root=root)
        return st["generated"]

    def replaced():
        if "replaced" not in st:
            with scripted_streams(record) as made:
                st["replaced"] = R.replacement_loop(generated(), None, plants=plants, gating=set(engines), log=log)
            st["streams_left"] = [f"{m.label}: {m.left()} recorded draws not used" for m in made if m.left()]
        return st["replaced"]

    def ceiling():
        if "ceilings" not in st:
            c = RC.ceilings(roads, engines=engines, ratios=tuple(record["ratios"]), dt=R.DT, jobs=jobs,
                            variants=tuple(record["variants"]), readings=tuple(record["readings"]))
            st["ceilings"] = (c, RC.passes_T(c, engines=engines))
        return st["ceilings"]

    def final_identities():
        if "final" not in st:
            st["final"] = _identities(roads, engines=engines, jobs=jobs, keep=True)
        return st["final"]

    def reported():
        if "reported" not in st:
            st["reported"] = _reported(roads, final_identities(), engines=engines, plants=plants)
        return st["reported"]

    def drawn(rs):
        return [{k: r.get(k) for k in ("k", "episode_seed", "weights", "dt", "label", "draws")} for r in rs]

    def section(name):
        ident = record["identities"]
        if name == "reconstruction":
            gen = generated()
            old = {"generated_arrays_sha256": _logged_hash(record, _STEP2_HASH, "step 2")[0],
                   "final_arrays_sha256": _logged_hash(record, _STEP4A_HASH, "step 4a")[0], "roads": drawn(record["roads"])}
            new = {"generated_arrays_sha256": R.arrays_sha256(gen) if len(gen) == len(record["roads"]) else None,
                   "final_arrays_sha256": R.arrays_sha256(roads), "roads": drawn(gen)}
            return _merged(compare(old, new, path=("reconstruction",)), problems=st["reconstruction_problems"])
        if name == "identities.locked_climb_b58":
            locked = None
            if "b58" in engines:
                locked = R._locked_task("b58")
                R.OPENED.update(locked.pop("opened"))
            return compare(ident["locked_climb_b58"], locked, path=("identities", "locked_climb_b58"))
        if name == "identities.generated":
            gen_id = _identities(generated(), engines=engines, jobs=jobs, keep=False)
            return compare(ident["generated"], gen_id, path=("identities", "generated"))
        if name == "slots":
            final, recs, _ = replaced()
            return _merged(compare(record["slots"], recs, path=("slots",)), compare(record["roads"], final, path=("roads",)),
                           problems=st["streams_left"])
        if name == "c5":
            return compare(record["c5"], replaced()[2], path=("c5",))
        if name == "ceilings":
            return compare(record["ceilings"], R.jsonable(ceiling()[0]), path=("ceilings",))
        if name == "passes_T":
            passes, at_15 = ceiling()[1]
            return compare(record["passes_T"], {"passes": bool(passes), "at_r_1.5": R.jsonable(at_15)}, path=("passes_T",))
        if name == "report":
            rep = (R.jsonable(RC.report(roads, engines=engines, dt=R.DT, jobs=jobs)) if record["companions"]
                   else "not computed (smoke)")
            return compare(record["report"], rep, path=("report",))
        if name == "identities.final":
            return compare(ident["final"], _without_arrays(final_identities()), path=("identities", "final"))
        if name == "cvt_diagnostic":
            return compare(record["cvt_diagnostic"], reported()[0], path=("cvt_diagnostic",))
        if name == "coverage":
            return compare(record["coverage"], reported()[1], path=("coverage",))
        if name == "episode_steps":
            steps = sorted({int(x["identity"]["steps"]) for road in final_identities().values() for x in road.values()
                            if x.get("identity")})
            return compare(record["episode_steps"], {"measured": steps, "note": R.EPISODE_STEPS_NOTE},
                           path=("episode_steps",))
        if name == "H_table":
            return compare(record["H_table"], R.h_table({e: record["tau"][e]["tau_s"] for e in engines}, RC.RATIOS,
                                                        dt=R.DT), path=("H_table",))
        if name == "design":
            return compare(record["design"], R.design(), path=("design",))
        if name == "streams":
            return compare(record["streams"], R.streams(), path=("streams",))
        reading = name[len("redraws."):]
        gating = dict(redraw_readings(record, redraws))[reading]
        got = (redraws.get("readings") or {}).get(reading)
        if got is None:
            return _merged(problems=[f"redraws.json holds no reading {reading!r}"])
        new = _redraw_reading(record, redraws, reading, gating, plants=plants, jobs=jobs, log=log)
        extra = [f"redraws.json holds a reading {n!r} epa_roads.redraw would not write" for n in
                 sorted(set(redraws.get("readings") or {}) - {n for n, _ in redraw_readings(record, redraws)})]
        return _merged(compare(got, new, path=("redraws", "readings", reading)), problems=extra)

    out = {"sections": {}, "reconstruction": None, "not_run": [], "stopped_at": None}
    for name in want:
        if out["stopped_at"] is not None:
            out["not_run"].append(name)
            continue
        log(f"section {name}: recomputing")
        try:
            res = section(name)
        except (NotRecorded, R.CodingDefect) as exc:
            res = _merged(problems=[f"{type(exc).__name__}: {exc}"])
        out["sections"][name] = res
        log(f"section {name}: {res['values']} values compared, {res['differences']} differ"
            + "".join(f"\n    {d['path']}: at the draw {d['at_draw']!r}, now {d['now']!r}" for d in res["first"][:5]))
        if res["differences"] and not keep_going:
            out["stopped_at"] = name
    out["not_run"] += [s for s in full if s not in want]
    if "generated" in st:
        out["reconstruction"] = reconstruction_block(record, st["generated"])
    return out


# =====================================================================================================
# The verdict and the record (12.4)
# =====================================================================================================
def _provenance_now(record, *, root, code, redraws=None):
    """What must not move while the run lasts: every hashed, contract, data and code file's sha_text, the
    versions, each engine's engine_sha and plant_sha (as first_draw's unchanged(), epa_roads.py:1321-1328),
    and, when redraws.json is re-verified from the tree, its data input summary.json (read through
    summary_opened; the roads records themselves are named by roads_sha and redraws_sha)."""
    import engines as ENG
    import epa_freeze
    h = record["hashes"]
    files = sorted(set(h["files"]) | set(h["contract"]) | set(record.get("data_inputs") or {}) | set(code))
    out = {"files": {f: _sha_now(root, f) for f in files}, "versions": epa_freeze.versions(),
           "plants": {e: {"engine_sha": ENG.engine_sha(R.plant_of(e)), "plant_sha": epa_freeze.plant_sha(e)}
                      for e in record["engines"]}}
    if redraws is not None:
        out["files"][R.SUMMARY_REL] = summary_sha(root)
    return out


def _changed(before, after):
    out = sorted(f for f in set(before["files"]) | set(after["files"]) if before["files"].get(f) != after["files"].get(f))
    return out + [k for k in ("versions", "plants") if before[k] != after[k]]


def files_opened_new(record, opened, *, root, ctx, redraws=None):
    """The repository files this run opened that neither the draw nor, when they are re-verified, the redraws
    opened, and that are none of the known inputs (the hashed files, the contract, the data inputs, this
    module's closure, the roads records): an input the code now reads that roads.json and redraws.json do not
    name. None when the record lists no files_opened (a test's record)."""
    if "files_opened" not in record:
        return None
    h = record["hashes"]
    known = (set(record["files_opened"]) | set(h["files"]) | set(h["contract"]) | set(record.get("data_inputs") or {})
             | set(ctx.get("code") or {}) | set((redraws or {}).get("files_opened") or ()))
    return sorted(f for f in opened if f not in known and not f.startswith(R.ROADS_DIR_REL + "/"))


def reverify(*, root, jobs, mode, out_dir, log, record=None, redraws=None, sections=None, keep_going=False,
             skip_companions=False):
    """The re-verification of roads.json (and of each reading of redraws.json, when it exists) on the code at
    `root`: the preconditions, then recompute, then the provenance again. Returns the result, 12.4's fields
    and, for the person reading it, refused, not_run, stopped_at and record_source. Verdict EQUAL only when
    every section computed has no difference, the reconstruction holds and nothing changed; REFUSED when a
    precondition fails, when an input changed during the run or when the run opened a file neither the draw
    nor the redraws did; DIFFERENT otherwise. partial is True when any section was not computed (fail-fast,
    --skip-companions, a test's `sections`) or a record is not the tree's (a test's roads.json or
    redraws.json): a partial result is never adopted or recorded. `record`, `redraws` and `sections` are
    passed by tests only; the command line reads the tree's roads.json and, when it exists, its
    redraws.json."""
    started = R.now_utc()
    committed_path = os.path.join(root, *R.ROADS_REL.split("/"))
    rec = record if record is not None else R.load_record(committed_path)
    tree_redraws = None                       # redraws.json read from the tree: its data input is watched too
    if redraws is None and record is None:
        red = os.path.join(root, *R.REDRAWS_REL.split("/"))
        redraws = tree_redraws = R.load_record(red) if os.path.isfile(red) else None
    log(f"roads_reverify {mode}: {ROW}; roads.json's {len(rec['roads'])} roads on {', '.join(rec['engines'])}"
        + ("; redraws.json's readings " + ", ".join(sorted(redraws.get("readings") or {})) if redraws else "; no redraws.json"))
    opened_before = set(R.files_opened())
    problems, ctx = preconditions(rec, root=root, mode=mode, out_dir=out_dir)
    result = {"schema": SCHEMA, "row": ROW, "mode": mode, "verdict": None, "partial": True,
              "roads_sha": ctx.get("roads_sha"), "redraws_sha": ctx.get("redraws_sha"), "head": ctx.get("head"),
              "pushed": ctx.get("pushed"), "clean": ctx.get("clean"), "tree_changes": ctx.get("tree_changes"),
              "started": started, "finished": None, "jobs": int(jobs), "env": ctx.get("env"),
              "versions": ctx.get("versions"), "plants": ctx.get("plants"), "hashed_files": ctx.get("hashed_files"),
              "contract_equal": ctx.get("contract_equal"), "data_inputs_equal": ctx.get("data_inputs_equal"),
              "files_opened_new": None, "taus_read_from_the_record": ctx.get("taus_read_from_the_record"),
              "reconstruction": None, "sections": {}, "ignored": {"paths": [list(p) for p in IGNORED_PATHS],
                                                                   "why": IGNORED_WHY},
              "added_by_step_12a": list(ADDED_BY_STEP_12A), "not_recomputed": not_recomputed(redraws),
              "changed_during_run": [], "code": ctx.get("code"), "supersedes": None, "steps_log": None,
              "refused": problems, "not_run": [], "stopped_at": None, "record_source": ctx.get("record_source")}
    if problems:
        log("REFUSED before anything ran:\n  " + "\n  ".join(problems))
        result.update(verdict="REFUSED", finished=R.now_utc(), not_run=all_sections(rec, redraws))
        return result
    want = sections
    if skip_companions:
        want = [s for s in (sections or all_sections(rec, redraws)) if s != "report"]
    before = _provenance_now(rec, root=root, code=ctx["code"], redraws=tree_redraws)
    computed = recompute(rec, root=root, jobs=jobs, log=log, sections=want, keep_going=keep_going, redraws=redraws)
    after = _provenance_now(rec, root=root, code=ctx["code"], redraws=tree_redraws)
    changed = _changed(before, after)
    new_files = files_opened_new(rec, set(R.files_opened()) - opened_before, root=root, ctx=ctx, redraws=redraws)
    differences = sum(s["differences"] for s in computed["sections"].values())
    recon = computed["reconstruction"]
    result.update(sections=computed["sections"], reconstruction=recon, not_run=computed["not_run"],
                  stopped_at=computed["stopped_at"], changed_during_run=changed, files_opened_new=new_files,
                  partial=(bool(computed["not_run"]) or record is not None or sections is not None
                           or redraws is not tree_redraws),
                  finished=R.now_utc())
    if changed or new_files:
        result["verdict"] = "REFUSED"
        result["refused"] = ([f"changed while the run lasted: {changed}"] if changed else []) + (
            [f"opened by this run and neither by the draw nor by the redraws: {new_files}"] if new_files else [])
    elif differences or (recon is not None and not recon["equal"]):
        result["verdict"] = "DIFFERENT"
    else:
        result["verdict"] = "EQUAL"
    log(f"VERDICT: {result['verdict']}" + (" (partial)" if result["partial"] else "")
        + f"; {differences} differences in {len(computed['sections'])} sections"
        + (f"; not run: {computed['not_run']}" if computed["not_run"] else ""))
    return result


def not_recomputed(redraws):
    """12.4's not_recomputed: NOT_RECOMPUTED (roads.json's keys, each with its reason) and, when redraws.json
    is re-verified, its keys that are read and checked, not recomputed (REDRAWS_NOT_RECOMPUTED)."""
    out = dict(NOT_RECOMPUTED)
    if redraws is not None:
        out[R.REDRAWS_REL] = dict(REDRAWS_NOT_RECOMPUTED)
    return out


def as_record(result, *, mode, supersedes):
    """12.4's record from a result: its fields only, the mode it is written in and what it supersedes."""
    out = {k: result[k] for k in RECORD_KEYS}
    out.update(mode=mode, supersedes=supersedes)
    return out


def reference_commit(rel, *, root):
    """The one definition of Live's reference (the interface sheet, section 5): the commit that added `rel`,
    `git log --diff-filter=A --format=%H -- <rel>`, which must print exactly one line. From P on,
    test_roads_reverify.Live compares every file the current record names with its blob there, never with
    HEAD or the work tree, so G's and V's later edits leave it passing (row 140 (3))."""
    r = subprocess.run(["git", "log", "--diff-filter=A", "--format=%H", "--", rel], cwd=root, capture_output=True,
                       text=True)
    lines = [x for x in r.stdout.splitlines() if x.strip()]
    if r.returncode != 0 or len(lines) != 1 or not re.fullmatch(r"[0-9a-f]{40}", lines[0]):
        raise R.Refused([f"{rel}: git log --diff-filter=A names {len(lines)} commits that added it, not one "
                         f"({r.stderr.strip()[:200]})"])
    return lines[0]


def blob_sha_text(commit, rel, *, root):
    """thresholds.common.sha_text of the blob `rel` holds at `commit` (CRLF read as LF), or None when the
    commit holds no such file."""
    import hashlib
    r = subprocess.run(["git", "cat-file", "blob", f"{commit}:{rel}"], cwd=root, capture_output=True)
    if r.returncode != 0:
        return None
    return hashlib.sha256(r.stdout.replace(b"\r\n", b"\n")).hexdigest()


def record_target(*, root, supersede):
    """Where record mode writes (row 140 (5)): OUT_REL, refused when it exists or was ever committed; or, with
    --supersede ROW, the next free reverify_<n>.json after every record four_engine_roads.reverify_paths
    lists, refused unless a current record exists (four_engine_roads.current_reverify) to supersede. Returns
    (rel, supersedes block or None, problems)."""
    from thresholds import common
    if supersede is None:
        probs = []
        if os.path.exists(os.path.join(root, *OUT_REL.split("/"))):
            probs.append(f"{OUT_REL} exists: it is written once; a re-made P writes its successor (--supersede ROW)")
        if R.committed_versions(root, OUT_REL):
            probs.append(f"{OUT_REL} was committed in HEAD's history: it is written once (row 140 (5))")
        return OUT_REL, None, probs
    cur = FR.current_reverify(root=root)
    if cur is None:
        return None, None, ["--supersede: no current re-verification record (four_engine_roads.current_reverify) to "
                            "supersede"]
    n = max([n for n, _ in FR.reverify_paths(root=root)] + [1]) + 1
    rel = f"{R.ROADS_DIR_REL}/reverify_{n}.json"
    probs = [f"{rel} exists or was committed: it is written once"] if (
        os.path.exists(os.path.join(root, *rel.split("/"))) or R.committed_versions(root, rel)) else []
    return rel, {"path": cur[0], "sha_text": common.sha_text(os.path.join(root, *cur[0].split("/"))),
                 "row": int(supersede)}, probs


def adopt(path, *, root, log):
    """`adopt FILE` (row 140 (3)): the check result at `path`, refused unless it is a complete EQUAL check
    (schema, mode check, partial False, nothing changed during it) whose head is HEAD and in origin's
    GRA-test, and unless everything it re-verified is still what it recorded: every hashed file's, this
    module's and its closure's, every changed input's (tree_changes), the contract's and the data inputs'
    sha_text, the versions, roads_sha, redraws_sha, every engine_sha and plant_sha; unless it computed every
    section of the tree's roads.json and redraws.json (both readings) with no difference and an equal
    reconstruction; and unless the records' own refusals (record_problems, summary.json's among them) still
    find nothing. Refused when reverify.json exists or was committed. Then written once to OUT_REL as mode
    'adopted-check'. Returns the record's sha_text."""
    import engines as ENG
    import epa_freeze
    res = R.load_record(path)
    probs = []
    for key, want in (("schema", SCHEMA), ("mode", "check"), ("verdict", "EQUAL"), ("partial", False),
                      ("changed_during_run", []), ("files_opened_new", [])):
        if res.get(key) != want:
            probs.append(f"the result's {key} is {res.get(key)!r}, not {want!r}: only a complete EQUAL check is adopted")
    head, _ = _git_state(root)
    if head is None or res.get("head") != head:
        probs.append(f"the result ran on {res.get('head')}, and HEAD is {head}: it is stale")
    if head is not None:
        pushed, _, why = R.remote_state(root, head)
        if not pushed:
            probs.append(why)
    _, _, tp = record_target(root=root, supersede=None)
    probs += tp
    rec = R.load_record(os.path.join(root, *R.ROADS_REL.split("/")))
    # complete: every section of this roads.json and redraws.json computed, none with a difference
    red_path = os.path.join(root, *R.REDRAWS_REL.split("/"))
    full = all_sections(rec, R.load_record(red_path) if os.path.isfile(red_path) else None)
    secs = res.get("sections") or {}
    if sorted(secs) != sorted(full) or any(s.get("differences") for s in secs.values()):
        probs.append(f"the result's sections {sorted(secs)} are not every section of the tree's records, each "
                     f"equal ({full})")
    if res.get("refused") or not (res.get("reconstruction") or {}).get("equal"):
        probs.append("the result names refusals, or its reconstruction is not equal")
    # the records' own refusals again, redraws.json's data input (summary.json) among them
    probs += record_problems(rec, root=root)
    if res.get("roads_sha") != R.roads_sha(os.path.join(root, *R.ROADS_REL.split("/"))):
        probs.append("the result's roads_sha is not roads.json's")
    if res.get("redraws_sha") != _sha_now(root, R.REDRAWS_REL):
        probs.append("the result's redraws_sha is not redraws.json's")
    named = dict((res.get("hashed_files") or {}).get("sha_text_now") or {})
    named.update(res.get("code") or {})
    named.update({c["path"]: c["sha_text"] for c in res.get("tree_changes") or []})
    named.update(rec["hashes"]["contract"])
    named.update(rec.get("data_inputs") or {})
    try:
        code_now = set(code_files(root=root))
    except (OSError, R.Refused) as exc:
        code_now = set()
        probs.append(f"{MODULE_REL}'s closure cannot be read ({exc})")
    probs += [f"{f}: in this module's closure now, not in the result's" for f in sorted(code_now - set(res.get("code") or {}))]
    probs += [f"{f}: its sha_text is not the result's" for f, s in sorted(named.items()) if _sha_now(root, f) != s]
    if epa_freeze.versions() != res.get("versions"):
        probs.append("the versions are not the result's")
    for e, p in sorted((res.get("plants") or {}).items()):
        if ENG.engine_sha(R.plant_of(e)) != p["engine_sha_now"] or epa_freeze.plant_sha(e) != p["plant_sha_now"]:
            probs.append(f"{e}: engine_sha or plant_sha is not the result's")
    if probs:
        raise R.Refused(probs)
    sha = R.write_once(os.path.join(root, *OUT_REL.split("/")), as_record(res, mode="adopted-check", supersedes=None))
    log(f"{OUT_REL} written: sha_text {sha} (adopted from {path})")
    return sha


# =====================================================================================================
# The command line
# =====================================================================================================
def _print_result(res):
    print(f"VERDICT: {res['verdict']}" + (" (partial: not adoptable)" if res["partial"] else ""), flush=True)
    for p in res.get("refused") or []:
        print(f"  REFUSED: {p}")
    for name, s in res["sections"].items():
        print(f"  {name}: {s['values']} values compared, {s['differences']} differ")
        for d in s["first"][:10]:
            print(f"      {d['path']}: at the draw {d['at_draw']!r}, now {d['now']!r}")
    if res.get("not_run"):
        print(f"  not run: {res['not_run']}")


def run_check(*, root, jobs, out_dir, skip_companions, keep_going, log, steps):
    """`check` (row 140 (3)): the re-verification of the tree at root, its result written once to
    out_dir/reverify_CHECK.json whatever the verdict, and only there (out_problems refuses any other place).
    `steps` is the list `log` appends to: the result's steps_log. Returns the exit code."""
    res = reverify(root=root, jobs=jobs, mode="check", out_dir=out_dir, log=log, keep_going=keep_going,
                   skip_companions=skip_companions)
    res["steps_log"] = list(steps)
    _print_result(res)
    if not out_problems(out_dir, root=root):
        os.makedirs(out_dir, exist_ok=True)
        sha = R.write_once(os.path.join(out_dir, CHECK_NAME), res)
        print(f"{os.path.join(out_dir, CHECK_NAME)} written: sha_text {sha}")
    return EXIT[res["verdict"]]


def run_record(*, root, jobs, supersede, log, steps):
    """`record` (row 140 (5)): on a clean HEAD in origin's GRA-test, the re-verification written once to
    OUT_REL, or with `supersede` (the row that re-made P) to the next free reverify_<n>.json naming the
    record it supersedes, from a complete EQUAL result only (row 140 (4): nothing else enters results/).
    Returns the exit code."""
    target, supersedes, probs = record_target(root=root, supersede=supersede)
    if probs:
        raise R.Refused(probs)
    res = reverify(root=root, jobs=jobs, mode="record", out_dir=None, log=log)
    res["steps_log"] = list(steps)
    _print_result(res)
    if res["verdict"] == "EQUAL" and not res["partial"]:
        sha = R.write_once(os.path.join(root, *target.split("/")), as_record(res, mode="record", supersedes=supersedes))
        print(f"{target} written: sha_text {sha}")
    else:
        print("nothing written: a DIFFERENT, REFUSED or partial result never enters results/ (row 140 (4))")
    return EXIT[res["verdict"]]


def main(argv=None):
    ap = argparse.ArgumentParser(prog="roads_reverify.py", description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("check")
    s.add_argument("--jobs", type=int, required=True)
    s.add_argument("--out", required=True, help="a folder outside every git work tree")
    s.add_argument("--skip-companions", action="store_true", help="leave roads_ceiling.report out (partial)")
    s.add_argument("--keep-going", action="store_true", help="compute every section after a difference")
    s = sub.add_parser("adopt")
    s.add_argument("file", help="a check's reverify_CHECK.json")
    s = sub.add_parser("record")
    s.add_argument("--jobs", type=int, required=True)
    s.add_argument("--supersede", type=int, default=None, help="the row that re-made P (row 140 (5))")
    a = ap.parse_args(argv)
    R.install_guard(())
    steps = []
    log = R.make_log(steps)
    try:
        if a.cmd == "adopt":
            adopt(a.file, root=HERE, log=log)
            return 0
        if a.cmd == "record":
            return run_record(root=HERE, jobs=a.jobs, supersede=a.supersede, log=log, steps=steps)
        return run_check(root=HERE, jobs=a.jobs, out_dir=a.out, skip_companions=a.skip_companions,
                         keep_going=a.keep_going, log=log, steps=steps)
    except R.Refused as exc:
        print("REFUSED:\n  " + "\n  ".join(exc.args[0] if exc.args and isinstance(exc.args[0], list)
                                           else [str(exc)]), file=sys.stderr)
        return EXIT["REFUSED"]
    except Exception:
        print("CRASH (no verdict, nothing written):\n" + traceback.format_exc(), file=sys.stderr)
        return EXIT_CRASH


if __name__ == "__main__":
    sys.exit(main())
