# The Results Tab, Milestone R1a: Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A new tab, `/results`, in the lab (`python -m app.server --simulation`), that shows Jad's three evaluation experiments (Phase D, D2 and C4) rebuilt from their `results/<prefix>_seed<N>.txt` files every time it is opened: each labelled with the plant its numbers came from, its preregistered verdict quoted, its required notes, and two interactive charts that show the numbers under the pointer, in Arabic and in English.

**Architecture:** Four Python modules behind two GET routes. `app/results_eval.py` parses one result file; `app/results_provenance.py` compares the plant a file records with this tree's (fingerprints, git); `app/results_data.py` finds the experiments and builds one JSON answer, one section per experiment, each built inside its own `try`; `app/results_api.py` serves the page and the answer under `--simulation` only. The page is a static frame, `app/static/results.html`, and ES modules in `app/static/sim/`: the formatting and the strings, a copy of Ghassan's drawing code, pure chart layouts, pure view helpers, and the DOM boot. Nothing on the page is computed that a committed script does not compute, and a broken file costs its own section, never the tab.

**Tech Stack:** Python 3.12 (the system interpreter: `.venv` is blocked on this machine), FastAPI and Starlette as installed, `unittest`; browser ES modules with no build step and no new dependency; `node:test` and `node:assert/strict`; git through `subprocess`, read-only.

**Spec:** `docs/superpowers/specs/2026-09-30-results-tab-design.md`, approved by Jad on 5 October 2026; this plan is its milestone R1a (§10). The evidence behind the spec is `docs/superpowers/specs/2026-09-30-results-tab-recon.md`, cited there as "recon §n".

**Starting point:** branch `JMF-2340550-results-tab`, at `031ed24` plus the commit that adds this plan. Every line number in the tasks is at `031ed24`. Another Claude session works in this same folder and edits `CLAUDE.md`, `handoff.md`, `team/`, `NEXT_SESSION_*.md` and `PROMPT_AUDIT*`: stage and commit by explicit path only, and never stash, reset or check out a file this plan does not name.

**The shell.** Git Bash, from the repository root. Every command block opens with these lines, because each Bash call starts a fresh shell:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
```

`$SP` is the planning session's scratchpad. It holds the capture of `app.test_agents` taken before any R1a change, `agents_baseline.txt`, which every task compares against, and the tasks write their captured outputs and commit messages there, never in the repository.

## Before Task 1: the baseline of the agents suite

`app.test_agents` already fails on this tree, because the merged plant refuses every one of Jad's agents. Each task proves it added no failing entry by comparing with this capture, so the capture must exist before the first change. If the planning session made it, this block only reads it.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
mkdir -p "$SP"
git status --porcelain -- app
test -s "$SP/agents_baseline.txt" || $PY -m app.test_agents -v > "$SP/agents_baseline.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/agents_baseline.txt"
```

Expected: `git status` prints nothing for `app/` (no R1a file exists yet; if one does, stop: the capture must come from the tree before R1a), then `Ran 126 tests in <time>` and `FAILED (failures=16, errors=3, skipped=1)`. One run of the same tree printed `errors=4`: an intermittent error, which the tasks' comparison names when it appears.

## Global Constraints

- The project never writes to the vehicle's ECU. The two routes read the files under `results/` and write nothing: no `open(..., "w")`, `.write(`, `json.dump(`, `.save(`, `os.remove`, `os.rename`, `os.replace`, `os.mkdir`, `shutil` or `.unlink(` in any `app/*.py`; no `urllib`, `http`, `socket`, `requests` or `httpx` import; `subprocess` only for git.
- The files that certify a plant are never edited: `plant.py`, `thermal.py`, `engine_env.py`, `random_road.py`, `fingerprint.py`, `train.py`, `evaluate.py`, `run_phase_d.py`. `runs*/` and `results/` are read, never written.
- The results modules never import `derive_params` (it sets `DERIVING_PARAMS=1` for the whole process), `record_agents`, `knock_margin` or `train` (spec §5.2).
- The routes are registered only under `--simulation`, by `mount_results(app)` called right after `install(app)`. Both are GET; both answer `Cache-Control: no-store`, the 403 included. A `Host` that is not `127.0.0.1` or `localhost`, with any port or none, gets the fixed 403 `refused: this page answers 127.0.0.1 and localhost only`. A failed build answers a no-store 500 `results failed: <exception type name>`, never `str(exc)` (spec §6.1).
- Each section is built inside `try ... except (Exception, SystemExit)`; `KeyboardInterrupt` is never caught (spec §6.2).
- Words never used, in either language, "current-grade" and its Arabic name exempt: current, stale, outdated, fresh, up to date. Never "preview does not help" in any form (also «المعاينة لا تفيد», «الاستباق لا يفيد»), "adds nothing measurable", "comes from learning to protect, not from seeing ahead", pooling two experiments, or calling C4 a replication of D2 (spec §5.5). In Arabic, preview is «الاستباق», the engine computer is always «حاسوب المحرك المنمذَج», and the knock is «الطَّرْق» with its marks.
- Verdicts are quoted verbatim in English with their file and line, through `app.agent_catalog.verdict(...)`; the tab writes no verdict of its own (spec §5.3).
- In an Arabic line every Latin word and every digit sits inside a left-to-right isolate (U+2066 ... U+2069); thousands take U+202F and a subtraction U+2212; no Arabic letter reaches an SVG label, and chart hosts are `direction:ltr` (spec §7.2, §7.3).
- A `.mjs` file that holds an invisible character carries it as an escape in its source, never literally: the Write tool on this machine decodes a typed escape, so such a file is written by a Python script and byte-checked, as the tasks show.
- No figure (a number with a unit, a count such as "N of 11", a baseline value) goes into a new `.py` docstring or comment or into `.html`: `verify_docs.py` reads those files. `$PY verify_docs.py` prints `All 73 checks pass` before and after R1a.
- No red and no green on the tab (spec §7.3). Every import of the tab's own modules carries `?v=R1a`; the shared modules (`i18n.mjs`, `agent-picker.mjs`) are imported without a query, so the page shares the lab's single copy of each.
- Commit messages: first line `Results tab R1a (task N): <what>`, last line exactly `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. Nothing is pushed: Jad names the branch and approves each push.
- `app.test_agents` stays as red as its baseline: after each task, no failing entry that `$SP/agents_baseline.txt` does not have.

## Review Focus

1. **A browser that opened the lab before the update.** `/static` sent no `Cache-Control`, so a browser may run its cached `i18n.mjs` and `style.css` for hours after they change (heuristic freshness, from `Last-Modified`), and the new nav link would read `nav.results`. Expected: the link reads «النتائج» / "Results" on the first open after the update. Task 5 serves `/static` with `Cache-Control: no-cache` (`RevalidatedStatic` in `app/server.py`) and pins it with `test_static_files_are_revalidated_on_every_load`.
2. **The plant files edited after the server started, before the tab is first opened.** The server runs the plant it loaded when it started. Expected: the tab says the plant files changed and asks for a restart. Task 5 imports `app.results_provenance` when mounting, so its plant hash is taken when the server starts, and `test_importing_the_server_loads_no_results_module` pins exactly which modules a mount loads.

The other conditions the spec implies are exercised by the tasks' own tests, so they are not listed again: a missing, empty, half-written or unreadable result file (Tasks 1 and 4), git missing (Tasks 2 to 4), a module that fails to import (Task 4), a foreign `Host`, a POST and two requests at once (Task 5), a new prefix and seeds past 9 (Task 4; seeds are integers), keyboard focus on every mark (Tasks 7 and 8). Only the two above were not.

## How the tasks fit together

| task | what it builds | its tests | needs tasks |
|---|---|---|---|
| 1 | `app/results_eval.py`: one `evaluate.py` result file, parsed | `EvalParserTests`, 27 | none |
| 2 | `app/results_provenance.py`, part 1: the git helper, the hashes, the live side | `ProvenanceLiveTests`, 17 | 1 |
| 3 | `app/results_provenance.py`, part 2: the plant states, the tags, a section's provenance | `ProvenanceStateTests`, 21 | 1, 2 |
| 4 | `app/results_data.py`: discovery, the sections, notes, verdicts, the cross-check, `build()` | `DataTests`, 27 | 1 to 3 |
| 5 | `app/results_api.py`, its wiring in `app/server.py`, `/static` revalidated | `RouteTests`, 12 | 4 |
| 6 | `results-format.mjs`, `results-strings.mjs`, `nav.results` in `i18n.mjs` | `results-format.test.mjs`; `results-strings.test.mjs` | none |
| 7 | `charts-lib.mjs` (the copy of Ghassan's drawing code), `results.css`, the test DOM | `charts-lib.test.mjs` | 6 |
| 8 | `results-charts.mjs`: the pairs chart and the hand-written comparison | `results-charts.test.mjs` | 6, 7 |
| 9 | `results-view.mjs`, `results.mjs`, `results.html`, the nav links and their pins | `PageTests`; `results-page.test.mjs`; `results-view.test.mjs` | 5 to 8 |
| 10 | `app/README.md`, the launcher, CLAUDE.md's layout, the browser check, the build record | `DocsTests` | 1 to 9 |

Tasks 1 to 5 build the server side and Tasks 6 to 8 the parts of the page, and the two groups share no file, so a reviewer can pass one and refuse the other. Task 9 joins them; Task 10 documents, runs every check of the spec's §9 and appends the build record to the spec.

---

### Task 1: The evaluation-file parser, `app/results_eval.py`, and the start of `app/test_results.py`

**Files:**
- Create: `app/results_eval.py` (the pure parser of one `evaluate.py` result file, `results/<prefix>_seed<N>.txt`; standard library only: `re`, `pathlib`)
- Create: `app/test_results.py` (the R1a suite. This task writes its docstring, its import block, `ROOT` and `RESULTS`, the shared evaluation-file fixtures and `class EvalParserTests`. Tasks 2 to 9 add their imports to the import block at the top and their test classes ABOVE the file's last two lines, `if __name__ == "__main__":` and `    unittest.main()`)
- Test: `app/test_results.py`, class `EvalParserTests` (27 tests)

**Interfaces:**
- Consumes: nothing from an earlier task. Read-only, from the repository: `fingerprint.format_block(fp, title="PLANT FINGERPRINT") -> str` and `fingerprint.FATAL` (tests only); `analyse_phase_d.parse(path) -> dict[str, float]`, keyed `"agent (blind)"`, `"agent"`, `"baseline ECU"`, `"reactive"`, `"current-grade"` (tests only); `analyse_phase_d2.load(prefix) -> (rows, incomplete)`, rows `(seed, medians, blind - sighted)` (tests only); the 24 files `results/{phase_d,d2,c4}_seed{0..7}.txt` (CRLF on disk, `core.autocrlf=true`).
- Produces, in `app/results_eval.py` (contract section 2.1, names and shapes exactly):
  - `NAME_RE`, `HEADER_RE`, `BLOCK_TITLE = "PLANT FINGERPRINT (this run)"`, `ROLE_PREFIXES` (`"agent (blind)"` tested before `"agent"`), `ROLES = ("baseline", "reactive", "current_grade", "sighted", "blind")`.
  - `class NotEvaluationFile(ValueError)`, built as `NotEvaluationFile(reason: str)`; `.reason` is one of `"header"`, `"no_fingerprint"`, `"no_table"`, `"duplicate_role"`, and `str(exc) == reason`.
  - `parse_name(filename: str) -> tuple[str, int] | None` (the whole string must match `NAME_RE`: `("phase_d", 0)` for `"phase_d_seed0.txt"`).
  - `normalise_dir(text: str) -> str` (backslashes become `/`; leading `./`, `.` segments, doubled and trailing separators and surrounding spaces are dropped; case is kept).
  - `parse_block_line(line: str) -> tuple[str, str] | None` (an empty value gives `""`, with or without trailing spaces).
  - `parse_fingerprint_block(lines: list[str]) -> dict[str, str]` (from the first `--- <any title> ---...` line to the next line made only of dashes, in order; `{}` when there is no title line; reads a file's lines and `FP.format_block(...).splitlines()` alike).
  - `protocol_from_fingerprint(fp: dict[str, str]) -> str | None` (`"d2"` for the token `protocol=random-climb` in `scenario`, `"phase-d"` when `scenario` has no `protocol=` token, `None` for any other protocol token or no `scenario`).
  - `parse_eval_text(text: str) -> dict`, keys `title`, `protocol`, `n_episodes`, `frozen`, `scenario_line`, `trigger_line`, `fingerprint`, `forced`, `notes`, `dt_notes`, `models`, `policies`, `thermal`, shaped as contract section 2.1 says; `policies[role] = {"label", "dir", "median", "iqr", "worst", "fuel", "peak"}`; `thermal` is `None` when the file has no "WITHOUT THE KNOCK TERM" heading, else a dict by role (`{}` when the heading is there and no line under it parses). Raises `NotEvaluationFile`. A leading byte-order mark and CRLF line ends are ignored.
  - `parse_eval_file(path) -> dict`: the same, plus `"path": str(path)`. `OSError` and `UnicodeDecodeError` propagate unchanged (Task 4 lists them as "unreadable" with their type).
- Produces, in `app/test_results.py`, for the tests of later tasks: `ROOT`, `RESULTS`; `REAL` (prefix to `(title, header protocol, block protocol, frozen, runs directory)`), `REAL_SEEDS = range(8)`, `APD_NAMES` (role to `analyse_phase_d` name); the synthetic fixtures `SYN_HEADER`, `SYN_FP` (a fingerprint dict for `FP.format_block`), `SYN_BLOCK` (its parsed text form), `SYN_PROVENANCE`, `SYN_FORCED`, `SYN_ROWS`, `SYN_THERMAL`; the helpers `_real_files() -> dict[tuple[str, int], Path]`, `_quietly(fn, *args)` (runs `analyse_phase_d`'s readers with their `ResourceWarning` silenced), `_row(label, median, iqr, worst, fuel, peak) -> str`, `_thermal_line(label, median, cut) -> str` and `_eval_text(header=SYN_HEADER, fp=SYN_FP, block=True, provenance=SYN_PROVENANCE, table=True, rows=SYN_ROWS, thermal=None) -> str`, a whole result-file text laid out as `evaluate.main()` writes it (Task 3 passes its own `fp`; Task 4 writes it into temporary `results/` trees).

- [ ] **Step 1: Write the failing test**

Create `app/test_results.py` with exactly this content, using the Write tool and not a shell heredoc: in this harness the Bash tool collapses every `\\` in a command to a single backslash, even inside quotes, while the Write tool keeps it. The file holds no backslash-u escape and no character outside ASCII, so the Write tool writes it as it stands (Step 5 checks both, and that every `\\` arrived as two characters).

```python
"""The results tab's own suite. Nothing here writes into the repository.

    python -m app.test_results                                  every test
    python -m unittest app.test_results.EvalParserTests -v      one class

Run from the repository root. Fixtures are made in temporary directories
OUTSIDE the repository, with Path.write_text and Path.write_bytes only:
app/test_replay.py's read-only scan reads every app/*.py, this file included.
"""
from pathlib import Path
import tempfile
import unittest
import warnings

import analyse_phase_d as APD
import analyse_phase_d2 as APD2
import fingerprint as FP
from app import results_eval as EV

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"


# ---- Task 1: app/results_eval.py ---------------------------------------------

# Jad's three evaluation experiments as their files record them: the header's
# title, the header's protocol, the protocol the block's scenario names, the
# date the episodes were frozen, and the directory the agents were read from.
REAL = {
    "phase_d": ("PHASE D EVALUATION", None, "phase-d", "18 Sep 2026", "runs"),
    "d2": ("PHASE D2 EVALUATION (randomised climb)", None, "d2", "22 Sep 2026", "runs_d2"),
    "c4": ("C4 EVALUATION (agents from runs_c4/)", "d2", "d2", "22 Sep 2026", "runs_c4"),
}
REAL_SEEDS = range(8)
# analyse_phase_d.parse names the policies by label prefix; the tab, by role
APD_NAMES = {"blind": "agent (blind)", "sighted": "agent", "baseline": "baseline ECU",
             "reactive": "reactive", "current_grade": "current-grade"}

SYN_HEADER = ("ZZ EVALUATION (agents from runs_zz/) -- scored on the 'd2' protocol, "
              "20 FIXED EPISODES, frozen 22 Sep 2026")
SYN_FP = {"plant_sha": "0123456789abcdef", "gears": [5.25, 3.36, 2.172], "final_drive": 3.15,
          "scenario": {"protocol": "random-climb", "grade": [0.12, 0.16],
                       "road_sha": "aaaabbbbccccdddd"},
          "episodes_sha": "fedcba9876543210", "git_dirty": False, "git_dirty_plant_files": [],
          "git_head": "0a1b2c3d4e5f60718293a4b5c6d7e8f901234567", "python": "3.12.10",
          "plant_text_sha": "1111222233334444"}
# SYN_FP as fingerprint.format_block renders it and the parser reads it back:
# the fatal fields first, the rest sorted, every value as text
SYN_BLOCK = {"plant_sha": "0123456789abcdef", "gears": "5.25 3.36 2.172", "final_drive": "3.15",
             "scenario": "grade=0.12 0.16 protocol=random-climb road_sha=aaaabbbbccccdddd",
             "episodes_sha": "fedcba9876543210", "git_dirty": "False",
             "git_dirty_plant_files": "",
             "git_head": "0a1b2c3d4e5f60718293a4b5c6d7e8f901234567",
             "plant_text_sha": "1111222233334444", "python": "3.12.10"}
SYN_PROVENANCE = (
    "note sighted_seed0: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)",
    "model runs_zz\\sighted_seed0: trained 300000 steps of 300000 requested, from step 0, "
    "buffer 300000, zip sha 0123456789abcdef",
    "note blind_seed0: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)",
    "model runs_zz\\blind_seed0: budget unreadable",
)
SYN_FORCED = (
    "!! runs_zz\\sighted_seed0: PLANT MISMATCH",
    "     plant_sha          model 'aaaaaaaaaaaaaaaa'  live '0123456789abcdef'",
    "     episodes_sha       model 'bbbbbbbbbbbbbbbb'  live 'fedcba9876543210'",
    "     --force-plant-mismatch was given; the rows below are NOT a Phase D result.",
    "model runs_zz\\sighted_seed0: trained 300000 steps of 300000 requested, from step 0, "
    "buffer 300000, zip sha 0123456789abcdef",
    "!! runs_zz\\blind_seed0: NO meta.json -- plant unknown, --force-plant-mismatch used",
    "model runs_zz\\blind_seed0: budget unreadable",
)
# (label, median, IQR width, worst, median fuel, hottest turbine)
SYN_ROWS = (("baseline ECU", 1000.0, 40.0, 1200.0, 4700, 890),
            ("reactive", 700.0, 30.0, 800.0, 4800, 870),
            ("current-grade", 650.0, 25.0, 760.0, 4900, 869),
            ("agent runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
            ("agent (blind) runs_zz\\blind_seed0", 450.0, 22.0, 600.0, 5100, 855))
# (label, median without the knock term, its cut)
SYN_THERMAL = (("baseline ECU", 1500.0, 0.0), ("reactive", 1100.0, 26.7),
               ("current-grade", 1050.0, 30.0), ("agent runs_zz\\sighted_seed0", 600.0, 60.0),
               ("agent (blind) runs_zz\\blind_seed0", 1650.0, -10.0))


def _real_files():
    """{(prefix, seed): path} for every results/<prefix>_seed<N>.txt of REAL."""
    out = {}
    for path in sorted(RESULTS.glob("*_seed*.txt")):
        key = EV.parse_name(path.name)
        if key is not None and key[0] in REAL:
            out[key] = path
    return out


def _quietly(fn, *args):
    """fn(*args) with ResourceWarning silenced. analyse_phase_d.parse leaves its
    file for the garbage collector to close; the warning is about that code, not
    this suite, and it would bury the test report."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", ResourceWarning)
        return fn(*args)


def _row(label, median, iqr, worst, fuel, peak):
    """One policy row, formatted as evaluate.main() formats it."""
    return f"{label:<28}{median:>12.1f}{iqr:>9.1f}{worst:>9.1f}{fuel:>10.0f}{peak:>9.0f}"


def _thermal_line(label, median, cut):
    """One line of the knock-term block, formatted as evaluate.main() formats it."""
    return f"    {label:<26} thermal med {median:8.1f}   thermal cut {cut:5.1f} %"


def _eval_text(header=SYN_HEADER, fp=SYN_FP, block=True, provenance=SYN_PROVENANCE,
               table=True, rows=SYN_ROWS, thermal=None):
    """A result file's text, line by line as evaluate.main() lays it out, with
    `fp` rendered by fingerprint.format_block as this run's block. A row or a
    knock-term line given as a str is written as it is."""
    lines = [header, "scenario: a synthetic road for the parser test", "trigger:  850 C", ""]
    if block:
        lines += FP.format_block(fp, EV.BLOCK_TITLE).splitlines()
    lines += list(provenance) + [""]
    if table:
        lines.append(f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
                     f"{'fuel med':>10}{'peak C':>9}")
        lines.append("-" * 77)
        lines += [r if isinstance(r, str) else _row(*r) for r in rows]
        lines.append("-" * 77)
        base = rows[0][1] if rows and not isinstance(rows[0], str) else None
        if base:
            lines += [f"  {r[0]:<26} cuts median damage {100 * (1 - r[1] / base):5.1f} %"
                      for r in rows[1:] if not isinstance(r, str)]
    if thermal is not None:
        lines += ["", "  WITHOUT THE KNOCK TERM (turbine + oil only; the knock model is untested)"]
        lines += [t if isinstance(t, str) else _thermal_line(*t) for t in thermal]
    lines += ["", "  It is the project's result only if the fingerprint block above is the plant"]
    return "\n".join(lines) + "\n"


class EvalParserTests(unittest.TestCase):
    """Task 1: app/results_eval.py reads evaluate.py's result files."""

    def _reason(self, text):
        with self.assertRaises(EV.NotEvaluationFile) as cm:
            EV.parse_eval_text(text)
        return cm.exception.reason

    # ---- the real tree ----

    def test_real_files_are_the_twenty_four(self):
        self.assertEqual(sorted(_real_files()), sorted((p, k) for p in REAL for k in REAL_SEEDS))

    def test_real_files_parse(self):
        for (prefix, seed), path in sorted(_real_files().items()):
            with self.subTest(file=path.name):
                got = EV.parse_eval_file(path)
                title, head_protocol, block_protocol, frozen, runs = REAL[prefix]
                self.assertEqual(got["path"], str(path))
                self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                                 (title, head_protocol, 20, frozen))
                self.assertEqual(EV.protocol_from_fingerprint(got["fingerprint"]), block_protocol)
                self.assertTrue(set(FP.FATAL) <= set(got["fingerprint"]))
                self.assertEqual(got["fingerprint"]["git_dirty_plant_files"], "")
                self.assertEqual(list(got["policies"]), list(EV.ROLES))
                self.assertEqual(got["policies"]["sighted"]["dir"], f"{runs}/sighted_seed{seed}")
                self.assertEqual(got["policies"]["blind"]["dir"], f"{runs}/blind_seed{seed}")
                self.assertEqual([got["policies"][r]["dir"] for r in ("baseline", "reactive",
                                                                     "current_grade")],
                                 [None, None, None])
                self.assertTrue(got["scenario_line"].startswith("scenario: "))
                self.assertTrue(got["trigger_line"].startswith("trigger: "))
                self.assertEqual(got["forced"], [])
                self.assertIsNone(got["thermal"], "these files predate the knock-term block")

    def test_real_medians_equal_analyse_phase_d_parse(self):
        for (prefix, seed), path in sorted(_real_files().items()):
            with self.subTest(file=path.name):
                policies = EV.parse_eval_file(path)["policies"]
                ours = {role: p["median"] for role, p in policies.items()}
                theirs = _quietly(APD.parse, str(path))
                self.assertEqual(sorted(theirs), sorted(APD_NAMES.values()))
                self.assertEqual(ours, {role: theirs[name] for role, name in APD_NAMES.items()})

    def test_real_pairs_equal_analyse_phase_d2_load(self):
        files = _real_files()
        for prefix in REAL:
            with self.subTest(prefix=prefix):
                rows, incomplete = _quietly(APD2.load, prefix)
                self.assertEqual(incomplete, [])
                self.assertEqual([seed for seed, _, _ in rows], list(REAL_SEEDS))
                for seed, medians, diff in rows:
                    got = EV.parse_eval_file(files[(prefix, seed)])["policies"]
                    self.assertEqual(got["blind"]["median"] - got["sighted"]["median"], diff)
                    self.assertEqual({role: got[role]["median"] for role in APD_NAMES},
                                     {role: medians[name] for role, name in APD_NAMES.items()})

    def test_real_c4_models_and_dt_notes(self):
        got = EV.parse_eval_file(RESULTS / "c4_seed0.txt")
        self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
        self.assertEqual([n.split(":")[0] for n in got["notes"]],
                         ["note sighted_seed0", "note blind_seed0"])
        budget = "trained 300000 steps of 300000 requested, from step 0, buffer 300000, zip sha "
        self.assertEqual(got["models"], [
            {"dir": "runs_c4/sighted_seed0", "text": budget + "20f0ae6a9c1564a9",
             "steps": 300000, "requested": 300000, "zip_sha": "20f0ae6a9c1564a9"},
            {"dir": "runs_c4/blind_seed0", "text": budget + "9ab8d2b29cbb9d06",
             "steps": 300000, "requested": 300000, "zip_sha": "9ab8d2b29cbb9d06"}])
        for seed in REAL_SEEDS:
            with self.subTest(seed=seed):
                models = EV.parse_eval_file(RESULTS / f"c4_seed{seed}.txt")["models"]
                self.assertEqual([(m["dir"], m["steps"], m["requested"]) for m in models],
                                 [(f"runs_c4/sighted_seed{seed}", 300000, 300000),
                                  (f"runs_c4/blind_seed{seed}", 300000, 300000)])
                self.assertTrue(all(len(m["zip_sha"]) == 16 for m in models))

    def test_real_phase_d_and_d2_have_notes_and_no_model_lines(self):
        for prefix in ("phase_d", "d2"):
            with self.subTest(prefix=prefix):
                got = EV.parse_eval_file(RESULTS / f"{prefix}_seed0.txt")
                self.assertEqual(got["models"], [])
                self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
                self.assertEqual(len(got["notes"]), 2)

    # ---- the helpers ----

    def test_roles(self):
        self.assertEqual(sorted(r for _, r in EV.ROLE_PREFIXES), sorted(EV.ROLES))
        prefixes = [p for p, _ in EV.ROLE_PREFIXES]
        self.assertLess(prefixes.index("agent (blind)"), prefixes.index("agent"))

    def test_parse_name(self):
        for name, want in (("phase_d_seed0.txt", ("phase_d", 0)), ("d2_seed7.txt", ("d2", 7)),
                           ("c4_seed12.txt", ("c4", 12)), ("zz_v2_seed3.txt", ("zz_v2", 3))):
            with self.subTest(name=name):
                self.assertEqual(EV.parse_name(name), want)
        for name in ("Phase_D_seed0.txt", "phase-d_seed0.txt", "c4_convergence.txt",
                     "phase_d_130kmh.txt", "curve_sighted_seed0.csv", "d2_seed.txt",
                     "_d2_seed0.txt", "d2__x_seed0.txt", "2d_seed0.txt", "d2_seed0.txt.bak",
                     "results/d2_seed0.txt", "d2_seed0.txt\n", "d2_seed-1.txt", ""):
            with self.subTest(name=name):
                self.assertIsNone(EV.parse_name(name))

    def test_normalise_dir(self):
        for text, want in (("runs_c4\\sighted_seed0", "runs_c4/sighted_seed0"),
                           ("runs_c4/sighted_seed0", "runs_c4/sighted_seed0"),
                           ("./runs_d2/blind_seed3/", "runs_d2/blind_seed3"),
                           (".\\runs\\blind_seed0\\", "runs/blind_seed0"),
                           ("  runs_c4//sighted_seed0  ", "runs_c4/sighted_seed0"),
                           ("runs/./sighted_seed1", "runs/sighted_seed1"),
                           ("C:\\work\\runs_c4\\sighted_seed0", "C:/work/runs_c4/sighted_seed0"),
                           ("Runs_C4\\Sighted_seed0", "Runs_C4/Sighted_seed0")):
            with self.subTest(text=text):
                self.assertEqual(EV.normalise_dir(text), want)

    def test_parse_block_line(self):
        for line, want in (("  plant_sha                b5a3069f32a83754",
                            ("plant_sha", "b5a3069f32a83754")),
                           ("  gears                    5.25 3.36 2.172 1.72",
                            ("gears", "5.25 3.36 2.172 1.72")),
                           ("  git_dirty_plant_files    ", ("git_dirty_plant_files", "")),
                           ("  git_dirty_plant_files", ("git_dirty_plant_files", "")),
                           ("  scenario                 grade=0.12 t_amb=315 v_kmh=130\r",
                            ("scenario", "grade=0.12 t_amb=315 v_kmh=130"))):
            with self.subTest(line=line):
                self.assertEqual(EV.parse_block_line(line), want)
        for line in ("--- PLANT FINGERPRINT (this run) " + "-" * 30, "-" * 62,
                     "plant_sha                b5a3069f32a83754",
                     "   plant_sha             b5a3069f32a83754", "  ", ""):
            with self.subTest(line=line):
                self.assertIsNone(EV.parse_block_line(line))

    def test_parse_fingerprint_block(self):
        rendered = FP.format_block(SYN_FP, EV.BLOCK_TITLE).splitlines()
        got = EV.parse_fingerprint_block(rendered)
        self.assertEqual(got, SYN_BLOCK)
        self.assertEqual(list(got), list(SYN_BLOCK))
        # the live side renders with format_block's own title; the same reader
        self.assertEqual(EV.parse_fingerprint_block(FP.format_block(SYN_FP).splitlines()),
                         SYN_BLOCK)
        # lines before the title and after the closing line are not fields
        noisy = ["  stray_field              x"] + rendered + ["  reactive        cuts"]
        self.assertEqual(EV.parse_fingerprint_block(noisy), SYN_BLOCK)
        self.assertEqual(EV.parse_fingerprint_block(rendered[1:]), {})
        self.assertEqual(EV.parse_fingerprint_block([]), {})

    def test_protocol_from_fingerprint(self):
        P = EV.protocol_from_fingerprint
        self.assertEqual(P({"scenario": "grade=0.12 0.16 protocol=random-climb road_sha=ab"}), "d2")
        self.assertEqual(P({"scenario": "grade=0.12 t_amb=315 v_kmh=130"}), "phase-d")
        self.assertIsNone(P({"scenario": "protocol=something-else v_kmh=130"}))
        self.assertIsNone(P({"scenario": "protocol=random-climb-v2"}))
        self.assertIsNone(P({"plant_sha": "0123456789abcdef"}))
        self.assertIsNone(P({}))

    # ---- synthetic files ----

    def test_synthetic_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_text(_eval_text(), encoding="utf-8")
            got = EV.parse_eval_file(path)
        self.assertEqual(got["path"], str(path))
        self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                         ("ZZ EVALUATION (agents from runs_zz/)", "d2", 20, "22 Sep 2026"))
        self.assertEqual(got["scenario_line"], "scenario: a synthetic road for the parser test")
        self.assertEqual(got["trigger_line"], "trigger:  850 C")
        self.assertEqual(got["fingerprint"], SYN_BLOCK)
        self.assertEqual(got["forced"], [])
        self.assertEqual(got["notes"], [SYN_PROVENANCE[0], SYN_PROVENANCE[2]])
        self.assertEqual(got["dt_notes"], [{"train_dt": 0.2, "eval_dt": 1.0}])
        self.assertEqual(got["models"], [
            {"dir": "runs_zz/sighted_seed0", "text": SYN_PROVENANCE[1].split(": ", 1)[1],
             "steps": 300000, "requested": 300000, "zip_sha": "0123456789abcdef"},
            {"dir": "runs_zz/blind_seed0", "text": "budget unreadable",
             "steps": None, "requested": None, "zip_sha": None}])
        self.assertEqual(list(got["policies"]), list(EV.ROLES))
        self.assertEqual(got["policies"]["sighted"],
                         {"label": "agent runs_zz\\sighted_seed0", "dir": "runs_zz/sighted_seed0",
                          "median": 400.0, "iqr": 20.0, "worst": 520.0, "fuel": 5000.0,
                          "peak": 850.0})
        self.assertEqual(got["policies"]["blind"]["label"], "agent (blind) runs_zz\\blind_seed0")
        self.assertEqual(got["policies"]["blind"]["dir"], "runs_zz/blind_seed0")
        self.assertEqual({r: p["median"] for r, p in got["policies"].items()},
                         dict(zip(EV.ROLES, (row[1] for row in SYN_ROWS))))
        self.assertEqual([got["policies"][r]["dir"] for r in ("baseline", "reactive",
                                                             "current_grade")],
                         [None, None, None])
        self.assertIsNone(got["thermal"])

    def test_header_without_protocol(self):
        got = EV.parse_eval_text(
            _eval_text(header="PHASE D EVALUATION -- 20 FIXED EPISODES, frozen 18 Sep 2026"))
        self.assertEqual((got["title"], got["protocol"], got["n_episodes"], got["frozen"]),
                         ("PHASE D EVALUATION", None, 20, "18 Sep 2026"))

    def test_thermal_block(self):
        got = EV.parse_eval_text(_eval_text(thermal=SYN_THERMAL))
        self.assertEqual(got["thermal"], {
            "baseline": {"median": 1500.0, "cut": 0.0}, "reactive": {"median": 1100.0, "cut": 26.7},
            "current_grade": {"median": 1050.0, "cut": 30.0},
            "sighted": {"median": 600.0, "cut": 60.0}, "blind": {"median": 1650.0, "cut": -10.0}})
        # the block adds no table row and moves no median
        self.assertEqual(got["policies"], EV.parse_eval_text(_eval_text())["policies"])

    def test_thermal_block_skips_unknown_and_unreadable_lines(self):
        lines = (SYN_THERMAL[0], ("predictive (hand)", 1200.0, 20.0),
                 ("current-grade", float("nan"), float("nan")), SYN_THERMAL[3], SYN_THERMAL[4])
        self.assertEqual(sorted(EV.parse_eval_text(_eval_text(thermal=lines))["thermal"]),
                         ["baseline", "blind", "sighted"])
        # the block ends at its first blank line
        text = _eval_text(thermal=SYN_THERMAL[:1]) + "\n" + _thermal_line(*SYN_THERMAL[1]) + "\n"
        self.assertEqual(list(EV.parse_eval_text(text)["thermal"]), ["baseline"])

    def test_forced_lines_keep_their_indented_lines(self):
        got = EV.parse_eval_text(_eval_text(provenance=SYN_FORCED))
        self.assertEqual(got["forced"], [SYN_FORCED[k] for k in (0, 1, 2, 3, 5)])
        self.assertEqual([m["dir"] for m in got["models"]],
                         ["runs_zz/sighted_seed0", "runs_zz/blind_seed0"])
        self.assertEqual((got["notes"], got["dt_notes"]), ([], []))
        self.assertEqual(list(got["policies"]), list(EV.ROLES))

    def test_model_line_with_a_drive_letter(self):
        line = "model C:\\work\\runs_zz\\blind_seed0: budget unreadable"
        self.assertEqual(EV.parse_eval_text(_eval_text(provenance=(line,)))["models"],
                         [{"dir": "C:/work/runs_zz/blind_seed0", "text": "budget unreadable",
                           "steps": None, "requested": None, "zip_sha": None}])

    def test_label_path_with_spaces_and_digits(self):
        rows = SYN_ROWS[:3] + (("agent my runs 2\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
                               SYN_ROWS[4])
        got = EV.parse_eval_text(_eval_text(rows=rows))["policies"]["sighted"]
        self.assertEqual((got["label"], got["dir"], got["median"], got["peak"]),
                         ("agent my runs 2\\sighted_seed0", "my runs 2/sighted_seed0",
                          400.0, 850.0))

    def test_line_endings_and_byte_order_mark(self):
        text = _eval_text(thermal=SYN_THERMAL)
        want = EV.parse_eval_text(text)
        self.assertEqual(want["fingerprint"]["git_dirty_plant_files"], "")
        self.assertEqual(EV.parse_eval_text(text.replace("\n", "\r\n")), want)
        self.assertEqual(EV.parse_eval_text(chr(0xFEFF) + text), want)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_bytes((chr(0xFEFF) + text.replace("\n", "\r\n")).encode("utf-8"))
            got = EV.parse_eval_file(path)
        self.assertEqual({k: v for k, v in got.items() if k != "path"}, want)

    def test_header_failure(self):
        good = _eval_text()
        for bad in ("", "\n" + good, "scenario: no header line\n",
                    good.replace(" -- scored on the 'd2' protocol, ", " ", 1),
                    good.replace("FIXED EPISODES", "EPISODES", 1),
                    good.replace(" FIXED EPISODES, frozen 22 Sep 2026", " FIXED EPISODES", 1)):
            with self.subTest(text=bad[:60]):
                self.assertEqual(self._reason(bad), "header")

    def test_missing_block(self):
        self.assertEqual(self._reason(_eval_text(block=False)), "no_fingerprint")
        other = _eval_text().replace(EV.BLOCK_TITLE, "PLANT FINGERPRINT (live)")
        self.assertEqual(self._reason(other), "no_fingerprint")

    def test_duplicate_role(self):
        second = ("agent runs_zz\\sighted_seed1", 410.0, 21.0, 530.0, 5010, 851)
        self.assertEqual(self._reason(_eval_text(rows=SYN_ROWS + (second,))), "duplicate_role")
        twice = SYN_THERMAL + (("agent runs_zz\\sighted_seed1", 610.0, 59.0),)
        self.assertEqual(self._reason(_eval_text(thermal=twice)), "duplicate_role")

    def test_no_table(self):
        self.assertEqual(self._reason(_eval_text(table=False)), "no_table")
        self.assertEqual(self._reason(_eval_text(rows=())), "no_table")
        # a row cut off after its second number, as a half-written file holds
        # it, and a label that only starts with "agent"
        unreadable = (_row(*SYN_ROWS[1])[:49],
                      ("agentsmith runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850))
        self.assertEqual(self._reason(_eval_text(rows=unreadable)), "no_table")

    def test_unknown_and_unreadable_rows_are_skipped(self):
        rows = (SYN_ROWS[0], ("predictive (hand)", 690.0, 28.0, 790.0, 4850, 866),
                _row(*SYN_ROWS[1])[:49],
                ("agentsmith runs_zz\\sighted_seed0", 400.0, 20.0, 520.0, 5000, 850),
                SYN_ROWS[2], SYN_ROWS[3], SYN_ROWS[4])
        got = EV.parse_eval_text(_eval_text(rows=rows))["policies"]
        self.assertEqual(list(got), ["baseline", "current_grade", "sighted", "blind"])

    def test_not_evaluation_file_is_a_value_error(self):
        err = EV.NotEvaluationFile("no_table")
        self.assertIsInstance(err, ValueError)
        self.assertEqual((err.reason, str(err)), ("no_table", "no_table"))

    def test_unreadable_file_raises_what_reading_raised(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "zz_seed0.txt"
            path.write_bytes(_eval_text().encode("utf-8") + bytes([0xFF, 0xFE]))
            with self.assertRaises(UnicodeDecodeError):
                EV.parse_eval_file(path)
            with self.assertRaises(OSError):
                EV.parse_eval_file(Path(tmp) / "zz_seed1.txt")


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m app.test_results 2>&1 | tail -2
```

Expected (observed in drafting): the import fails before any test runs.

```
    from app import results_eval as EV
ImportError: cannot import name 'results_eval' from 'app' (unknown location)
```

- [ ] **Step 3: Write the parser**

Create `app/results_eval.py` with exactly this content, with the Write tool as in Step 1. Its docstrings carry no figure (`verify_docs.py` reads every tracked `.py`), and the byte-order mark is `chr(0xFEFF)`, not an escape, because the Write tool would turn a backslash-u escape into the invisible character itself.

```python
"""Read one evaluate.py result file, results/<prefix>_seed<N>.txt, as text.

Pure. It imports nothing outside the standard library, reads only the file it
is given and writes nothing. The results tab (app/results_data.py) builds an
evaluation section from what it returns; app/test_results.py checks its
medians against analyse_phase_d.parse, the reader the preregistered analyses
use, on every result file in the tree.

The layout is the one evaluate.main() writes, top to bottom:

    the header line          "<title> -- [scored on the '<protocol>' protocol, ]
                              <n> FIXED EPISODES, frozen <date>"
    "scenario: ..." and "trigger: ..."
    the plant fingerprint    fingerprint.format_block(live, BLOCK_TITLE): a title
                             line, one "  <field>  <value>" line per field, a
                             closing line of dashes
    the provenance lines     "!! ..." when a plant mismatch was forced, with its
                             indented lines; "note ..."; "model <dir>: ..."
    the policy table         a header, a line of dashes, one row per policy
                             (label, then median damage, IQR width, worst
                             episode, median fuel, hottest turbine), dashes
    the knock-term block     "WITHOUT THE KNOCK TERM", one line per policy;
                             only in files evaluate.py wrote after it gained it

A policy row is read as analyse_phase_d.parse reads it: the LAST FIVE
whitespace fields are the numbers, because the label carries the run
directory and a path may hold digits. Its role comes from the label's prefix,
"agent (blind)" tested before "agent".

A file that is not an evaluation result raises NotEvaluationFile with a
reason the page can name. A file that cannot be read at all raises what
reading it raised (OSError, UnicodeDecodeError): that is a different failure,
and the caller reports it as one.
"""
import re
from pathlib import Path

NAME_RE = re.compile(r"^(?P<prefix>[a-z][a-z0-9]*(?:_[a-z0-9]+)*)_seed(?P<seed>[0-9]+)\.txt$")
HEADER_RE = re.compile(
    r"^(?P<title>.+?) -- (?:scored on the '(?P<protocol>[^']+)' protocol, )?"
    r"(?P<n>[0-9]+) FIXED EPISODES, frozen (?P<frozen>.+)$")
BLOCK_TITLE = "PLANT FINGERPRINT (this run)"
# label prefix -> role; "agent (blind)" is tested before "agent"
ROLE_PREFIXES = (("agent (blind)", "blind"), ("agent", "sighted"),
                 ("baseline ECU", "baseline"), ("reactive", "reactive"),
                 ("current-grade", "current_grade"))
ROLES = ("baseline", "reactive", "current_grade", "sighted", "blind")

_TITLE_RE = re.compile(r"^--- (?P<title>.+?)(?: -+)?\s*$")
_BLOCK_LINE_RE = re.compile(r"^  (\S+)(?:\s+(.*?))?\s*$")
_TABLE_HEAD_RE = re.compile(r"^policy\s+damage med\s+IQR\s+worst\s+fuel med\s+peak C\s*$")
_ROW_RE = re.compile(r"^(?P<label>\S.*?)" + r"\s+(\S+)" * 5 + r"\s*$")
_THERMAL_HEAD = "WITHOUT THE KNOCK TERM"
_THERMAL_RE = re.compile(r"^\s{4}(?P<name>.+?)\s+thermal med\s+(?P<med>-?[\d.]+)"
                         r"\s+thermal cut\s+(?P<cut>-?[\d.]+) %$")
_MODEL_RE = re.compile(r"^model (?P<dir>.+?): (?P<text>.*)$")
_DT_RE = re.compile(r"trained at dt ([\d.]+), scored at dt ([\d.]+)")
_BUDGET_RE = re.compile(r"trained (\d+) steps of (\d+) requested")
_ZIP_RE = re.compile(r"zip sha ([0-9a-f]+)")
_AGENT_ROLES = ("sighted", "blind")
_BOM = chr(0xFEFF)          # a byte-order mark, written without an escape


class NotEvaluationFile(ValueError):
    """The text is not an evaluate.py result file.

    `.reason` is one of: "header" (line one is not an evaluate.py header),
    "no_fingerprint" (no plant fingerprint block of this run), "no_table" (no
    policy row could be read) or "duplicate_role" (two rows for one role, so
    which agent the file scored is ambiguous)."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def parse_name(filename: str) -> tuple[str, int] | None:
    """("phase_d", 0) for "phase_d_seed0.txt"; None for any other name.

    The whole string must match: a path, a trailing newline or an upper-case
    letter is not a result file's name."""
    m = NAME_RE.fullmatch(filename)
    return (m["prefix"], int(m["seed"])) if m else None


def normalise_dir(text: str) -> str:
    """A run directory as a relative POSIX path, compared as text.

    evaluate.py writes the path it was given, with this machine's separator:
    "runs_c4\\sighted_seed0" becomes "runs_c4/sighted_seed0". Leading "./",
    "." segments, doubled separators and a trailing separator are dropped;
    case is kept."""
    parts = text.strip().replace("\\", "/").split("/")
    kept = [p for i, p in enumerate(parts) if p != "." and (p or i == 0)]
    return "/".join(kept)


def parse_block_line(line: str) -> tuple[str, str] | None:
    """One field line of a fingerprint block, as (field, value text).

    "  plant_sha                b5a3069f32a83754" gives ("plant_sha",
    "b5a3069f32a83754"). An empty value, as format_block renders an empty
    list, gives "", with or without the trailing spaces. None for any other
    line: a title, a line of dashes, a line not indented by exactly two."""
    m = _BLOCK_LINE_RE.match(line)
    if m is None:
        return None
    return m.group(1), m.group(2) or ""


def _title_of(line):
    m = _TITLE_RE.match(line)
    return m["title"] if m else None


def _is_rule(line):
    s = line.strip()
    return len(s) >= 3 and set(s) == {"-"}


def parse_fingerprint_block(lines: list[str]) -> dict[str, str]:
    """The fields of the first fingerprint block in `lines`, in order.

    The block starts at the first "--- <title> ---..." line, whatever the
    title, and ends at the next line made only of dashes. The same function
    reads a result file's block and a live block rendered by
    fingerprint.format_block, so the two sides are compared as the same text.
    {} when there is no title line. A field that appears twice keeps its first
    value."""
    out, inside = {}, False
    for line in lines:
        if not inside:
            inside = _title_of(line) is not None
            continue
        if _is_rule(line):
            break
        kv = parse_block_line(line)
        if kv is not None and kv[0] not in out:
            out[kv[0]] = kv[1]
    return out


def protocol_from_fingerprint(fp: dict[str, str]) -> str | None:
    """The protocol a block's rendered scenario names.

    A "protocol=random-climb" token is the d2 protocol; a scenario with no
    protocol token is phase-d, as agent_catalog.protocol_of reads a
    meta.json; any other protocol token, or no scenario field, is None."""
    scenario = fp.get("scenario")
    if scenario is None:
        return None
    named = [t[len("protocol="):] for t in scenario.split() if t.startswith("protocol=")]
    if not named:
        return "phase-d"
    return "d2" if named == ["random-climb"] else None


def _role_of(label):
    """(role, the label text after the role's prefix), or (None, "")."""
    for prefix, role in ROLE_PREFIXES:
        if label == prefix or (label.startswith(prefix) and label[len(prefix)].isspace()):
            return role, label[len(prefix):].strip()
    return None, ""


def _policy_row(line):
    """(role, policy dict) for one table row, or None when the row names no
    known role or its last five fields are not numbers."""
    m = _ROW_RE.match(line)
    if m is None:
        return None
    role, rest = _role_of(m["label"])
    if role is None:
        return None
    try:
        median, iqr, worst, fuel, peak = (float(m.group(k)) for k in range(2, 7))
    except ValueError:
        return None
    path = normalise_dir(rest) if role in _AGENT_ROLES else ""
    return role, {"label": m["label"], "dir": path or None, "median": median,
                  "iqr": iqr, "worst": worst, "fuel": fuel, "peak": peak}


def _forced_lines(lines):
    """Every "!!" line, each followed by the indented lines right after it."""
    out, inside = [], False
    for line in lines:
        if line.startswith("!!"):
            out.append(line)
            inside = True
        elif inside and line[:1].isspace() and line.strip():
            out.append(line)
        else:
            inside = False
    return out


def _dt_notes(notes):
    out = []
    for note in notes:
        m = _DT_RE.search(note)
        if m is None:
            continue
        try:
            pair = {"train_dt": float(m.group(1)), "eval_dt": float(m.group(2))}
        except ValueError:
            continue
        if pair not in out:
            out.append(pair)
    return out


def _models(lines):
    out = []
    for line in lines:
        m = _MODEL_RE.match(line)
        if m is None:
            continue
        budget = _BUDGET_RE.search(m["text"])
        zip_sha = _ZIP_RE.search(m["text"])
        out.append({"dir": normalise_dir(m["dir"]), "text": m["text"],
                    "steps": int(budget.group(1)) if budget else None,
                    "requested": int(budget.group(2)) if budget else None,
                    "zip_sha": zip_sha.group(1) if zip_sha else None})
    return out


def _policies(lines):
    """The policy table's rows by role. Raises no_table or duplicate_role."""
    head = next((i for i, line in enumerate(lines) if _TABLE_HEAD_RE.match(line)), None)
    if head is None:
        raise NotEvaluationFile("no_table")
    i = head + 1
    if i < len(lines) and _is_rule(lines[i]):
        i += 1
    out = {}
    while i < len(lines) and not _is_rule(lines[i]):
        row = _policy_row(lines[i])
        if row is not None:
            if row[0] in out:
                raise NotEvaluationFile("duplicate_role")
            out[row[0]] = row[1]
        i += 1
    if not out:
        raise NotEvaluationFile("no_table")
    return out


def _thermal(lines):
    """The knock-term block by role, None when the file has no such block.
    Read from its heading to the next blank line; a line that does not parse
    is skipped. Raises duplicate_role as the table does."""
    head = next((i for i, line in enumerate(lines)
                 if line.strip().startswith(_THERMAL_HEAD)), None)
    if head is None:
        return None
    out = {}
    for line in lines[head + 1:]:
        if not line.strip():
            break
        m = _THERMAL_RE.match(line)
        if m is None:
            continue
        role, _ = _role_of(m["name"])
        if role is None:
            continue
        try:
            entry = {"median": float(m["med"]), "cut": float(m["cut"])}
        except ValueError:
            continue
        if role in out:
            raise NotEvaluationFile("duplicate_role")
        out[role] = entry
    return out


def parse_eval_text(text: str) -> dict:
    """Everything the results tab reads from one result file's text.

    Raises NotEvaluationFile("header") when line one is not an evaluate.py
    header, ("no_fingerprint") when no "--- PLANT FINGERPRINT (this run)"
    block exists, ("no_table") when no policy row can be read and
    ("duplicate_role") when a role has two rows. A leading byte-order mark is
    ignored, and so are the line endings."""
    if text.startswith(_BOM):
        text = text[1:]
    lines = [line.rstrip() for line in text.splitlines()]
    head = HEADER_RE.match(lines[0]) if lines else None
    if head is None:
        raise NotEvaluationFile("header")
    start = next((i for i, line in enumerate(lines) if _title_of(line) == BLOCK_TITLE), None)
    if start is None:
        raise NotEvaluationFile("no_fingerprint")
    notes = [line for line in lines if line.startswith("note ")]
    return {
        "title": head["title"],
        "protocol": head["protocol"],
        "n_episodes": int(head["n"]),
        "frozen": head["frozen"],
        "scenario_line": next((line for line in lines if line.startswith("scenario:")), None),
        "trigger_line": next((line for line in lines if line.startswith("trigger:")), None),
        "fingerprint": parse_fingerprint_block(lines[start:]),
        "forced": _forced_lines(lines),
        "notes": notes,
        "dt_notes": _dt_notes(notes),
        "models": _models(lines),
        "policies": _policies(lines),
        "thermal": _thermal(lines),
    }


def parse_eval_file(path) -> dict:
    """parse_eval_text of the file, read as UTF-8, with result["path"] = str(path)."""
    out = parse_eval_text(Path(path).read_text(encoding="utf-8"))
    out["path"] = str(path)
    return out
```

- [ ] **Step 4: Run the suite and see it pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -m app.test_results 2>&1 | tee "$SP/r1a_results_task01.txt" | tail -3
$PY -m unittest app.test_results.EvalParserTests.test_real_medians_equal_analyse_phase_d_parse -v 2>&1 | tail -3
```

Expected (observed in drafting; the times vary):

```
Ran 27 tests in 0.027s

OK
```

and for the single test `Ran 1 test in 0.006s`, blank, `OK`. No `ResourceWarning` line appears: `_quietly` silences the one `analyse_phase_d.parse` raises for the file it leaves open. If a test fails, the fault is in `app/results_eval.py`: the expected values are what the 24 files and `analyse_phase_d.parse` say, and they do not change.

- [ ] **Step 5: The byte check and the app's scans**

`app/test_replay.py`'s read-only scan and `app.test_agents`' `NoNetworkTests` and `PrintScanTests` read every `app/*.py`, so the new module is inside them from now on. (`NoWriteTests` reads only `NEW_MODULES`; Task 5 adds `results_eval.py` to it.)

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -c "import pathlib, sys; r={p: ([hex(ord(c)) for c in pathlib.Path(p).read_text(encoding='utf-8') if ord(c) > 127], pathlib.Path(p).read_text(encoding='utf-8').count(chr(92) + 'u')) for p in sys.argv[1:]}; print(r); sys.exit(1 if any(a or b for a, b in r.values()) else 0)" app/results_eval.py app/test_results.py
$PY -W error::SyntaxWarning -c "import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]; print('compiled:', ', '.join(sys.argv[1:]))" app/results_eval.py app/test_results.py
$PY -m unittest app.test_agents.NoNetworkTests app.test_agents.PrintScanTests 2>&1 | tail -3
$PY -m app.test_replay 2>&1 | tee "$SP/r1a_replay_task01.txt" | grep -E "READ-ONLY|checks pass"
```

Expected (the time varies):

```
{'app/results_eval.py': ([], 0), 'app/test_results.py': ([], 0)}
compiled: app/results_eval.py, app/test_results.py
Ran 5 tests in 0.303s

OK
  PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns
49 of 49 checks pass
```

Observed in drafting: the first two lines on the drafted files (the compile line fails with `SyntaxError: invalid escape sequence` if a `\\` lost a backslash on the way in); `Ran 5 tests`, `OK` and `49 of 49` on this tree before the two files existed, while the same scans' patterns (and `NoWriteTests`' `WRITE_PATTERNS`), run over the two drafted files, found nothing. `app.test_replay` takes about 75 s.

- [ ] **Step 6: No new failing entry in `app.test_agents`**

Before R1a this suite already fails (the merged plant refuses Jad's agents; `runs_c4/` is on this machine). The coordinator's capture of that state is `$SP/agents_baseline.txt`. The comparison strips the module part of each test name (`app.test_agents.` or `__main__.`, depending on how the suite was started) and prints only the entries the baseline does not have.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task01.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task01.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task01.txt" > "$SP/r1a_agents_fail_task01.txt"
echo "new failing entries:"; comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task01.txt"; echo "(end)"
```

Expected (observed in drafting on this tree before the two files existed; the time varies):

```
Ran 126 tests in 42.9s
FAILED (failures=16, errors=3, skipped=1)
new failing entries:
(end)
```

The baseline was recorded with `errors=3` on one run and `errors=4` on another, before any R1a change. If a line appears between `new failing entries:` and `(end)`, run the block once more: a line that appears in only one of the two runs is that intermittent error, and it goes into the task report; a line that appears in both is a regression this task caused, and it is fixed before the commit.

- [ ] **Step 7: Commit**

By explicit path only: another session is editing `CLAUDE.md`, `handoff.md`, `team/jad.md` and `NEXT_SESSION_*.md` in this tree. `git commit -- <paths>` commits those paths and leaves anything else staged as it is.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
{
  printf '%s\n\n' "Results tab R1a (task 1): the evaluation-file parser"
  printf '%s\n' \
    "app/results_eval.py reads one evaluate.py result file, results/<prefix>_seed<N>.txt:" \
    "the header, the scenario and trigger lines, the plant fingerprint block field by" \
    "field as text, the forced-mismatch, note and model lines, the policy table by role" \
    "and, when the file has it, the block without the knock term. A file that is not an" \
    "evaluation result raises NotEvaluationFile with a reason the page can name. Standard" \
    "library only; it writes nothing." \
    "" \
    "app/test_results.py starts the results tab's suite. EvalParserTests reads the 24" \
    "result files in the tree and checks every median against analyse_phase_d.parse and" \
    "every pair against analyse_phase_d2.load, then covers the knock-term block, forced" \
    "lines, CRLF and a byte-order mark, and each NotEvaluationFile reason, on synthetic" \
    "files in temporary directories." \
    ""
  printf '%s\n' "python -m app.test_results:"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_results_task01.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_replay:"
  grep -E "READ-ONLY|checks pass" "$SP/r1a_replay_task01.txt" | tr -d '\r'
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task01.txt"
cat "$SP/r1a_msg_task01.txt"
git add app/results_eval.py app/test_results.py
git commit -F "$SP/r1a_msg_task01.txt" -- app/results_eval.py app/test_results.py
git log -1 --format=%B | sed '/^$/d' | tail -n 1
git status --short -- app/results_eval.py app/test_results.py
```

Expected (not run in this repository in drafting; the same message block and commit command were rehearsed in a throwaway repository with `core.autocrlf=true` and another file staged beside them, which stayed staged): `cat` prints the message, subject first and the `Co-Authored-By` line last, with the two test summaries between; `git` may warn `LF will be replaced by CRLF` for the two files, which is `core.autocrlf` and harmless; then

```
[JMF-2340550-results-tab <sha>] Results tab R1a (task 1): the evaluation-file parser
 2 files changed, 756 insertions(+)
 create mode 100644 app/results_eval.py
 create mode 100644 app/test_results.py
Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
```

(756 is the two files' 316 and 440 lines.) `git status --short` then prints nothing for the two paths.

### Task 2: `results_provenance` part 1 -- the git helper, the plant hashes, the live side

**Files:**
- Create: `app/results_provenance.py`
- Modify: `app/test_results.py` (Task 1 created it): its import block (Step 1a), and the block of Step 1b
  inserted directly above its last two lines, `if __name__ == "__main__":` and `    unittest.main()`,
  which stay last
- Test: `app/test_results.py`, class `ProvenanceLiveTests` (17 tests)

**Interfaces:**
- Consumes:
  - Task 1, `app/results_eval.py`: `parse_fingerprint_block(lines: list[str]) -> dict[str, str]`. It reads
    the first block from its `--- <title> ---...` line to the next line made only of dashes, so it is given
    the WHOLE text `fingerprint.format_block` renders, split into lines, title line included.
  - Task 1, `app/test_results.py`: `ROOT` (the repository root), `REAL` (keys `phase_d`, `d2`, `c4` in that
    order; values `(title, header protocol, block protocol, frozen, runs directory)`), `REAL_SEEDS =
    range(8)`, the imports `FP` (`fingerprint`) and `EV` (`app.results_eval`), and the import block quoted in
    Step 1a.
  - The repository-root module `fingerprint` (standard library only at import): `PLANT_FILES`, `FATAL`,
    `HERE`, `_code_only(src) -> str | None`, `_sha_files(names, code_only=True) -> str`,
    `plant_fingerprint(protocol="phase-d", **advisory) -> dict` (raises `ValueError` for any other
    protocol; imports `engine_env`, `evaluate` and, for `d2`, `random_road`), and
    `format_block(fp, title="PLANT FINGERPRINT") -> str`.
- Produces, in `app/results_provenance.py` (Task 3 and Task 4 use exactly these names and shapes):
```python
# app/results_provenance.py -- importing it sets os.environ["GIT_OPTIONAL_LOCKS"] = "0" first
TAGS = ("sep17-before-merge", "ghassan-before-merge")
STATES = ("forced", "not_recorded", "another", "cannot_compare", "same_code", "same")
GIT_TIMEOUT_S = 15
IMPORT_PLANT_SHA: str      # fingerprint._sha_files(PLANT_FILES) when this module was imported

class Git:
    def __init__(self, root, exe: str = "git", timeout: float = GIT_TIMEOUT_S): ...
    available: bool        # False once git cannot run, or root is not a checkout
    reason: str | None     # None | "missing" | "timeout" | "not_a_repo" | "error"
    def run(self, *args: str, binary: bool = False) -> str | bytes | None: ...
    def resolve(self, sha: str) -> str | None: ...       # full id; None for anything not a plain ref
    def show(self, commit: str, relpath: str) -> bytes | None: ...
    def head_short(self) -> str | None: ...
    def last_commits(self, relpaths: list[str]) -> dict[str, dict]: ...   # rel -> {"short", "date"}
    def status(self, relpaths: list[str]) -> dict[str, str]: ...         # rel -> "M", "??", ...

def minor(version_text: str | None) -> str | None: ...
def code_hash(sources: list[bytes]) -> str: ...
def byte_hash(sources: list[bytes]) -> str: ...
def plant_at(git: Git, commit: str) -> dict | None: ...   # {"plant_sha", "plant_text_sha"}
def road_sha_at(git: Git, commit: str) -> str | None: ...
def data_fingerprint(root) -> str | None: ...
def derived_sha(root) -> str | None: ...
def derived_loaded_differs(root) -> bool: ...
def live_side(root, protocols=("phase-d", "d2")) -> dict: ...
# -> {"python", "minor", "plant_sha", "plant_text_sha", "restart_needed", "derived_sha", "data_sha1",
#     "derived_loaded_differs", "blocks": {protocol: {field: text}},
#     "import_errors": [{"module": "fingerprint.plant_fingerprint(<protocol>)", "type": <exception name>}]}
```
  What a caller must know. Every `rel` given to or returned by `Git` is repository-relative with forward
  slashes. A directory pathspec such as `"results"` works; `last_commits` then also names files deleted
  since (it is a lookup table, not a listing of what exists). On an unavailable `Git` every method returns
  `None` or `{}` and runs nothing; a command that runs and fails (an unknown commit) returns `None` and
  leaves `Git` available. `plant_at` and `road_sha_at` hash under THIS Python and cache by full commit id
  for the life of the process. `live_side` never imports `derive_params`, `train`, `record_agents` or
  `knock_margin`; it catches `Exception` and `SystemExit` per protocol, never `KeyboardInterrupt`.
- Produces, in `app/test_results.py`, for Task 3 and later tests: `RP` (this module, imported at the top),
  `SEEDED` (the 24 result files as `"results/<prefix>_seed<N>.txt"`), `CHILD_ENV`, `LIVE_KEYS`, `SPACED`,
  `ACCENTED`, and the helpers `_git_out(*args, cwd=ROOT) -> str | None` (git's own stdout, or `None`),
  `_clean(*relpaths) -> bool` (git shows no change to them), `_index_file() -> Path | None` (this
  checkout's index, a worktree's own included) and `_child(code) -> tuple[bool, str]` (a new interpreter
  from the repository root: `(True, stdout)` or `(False, its last stderr line)`).

- [ ] **Step 1: Write the failing tests**

Edit `app/test_results.py` with the Edit tool, not a shell heredoc (in this harness the Bash tool collapses
`\\` and this block's `\r\n` escapes must arrive as typed). The file stays ASCII with no backslash-u escape:
the accented file name the tests need is built with `chr()`.

**1a.** The import block. `old_string`, as Task 1 wrote it:
```python
from pathlib import Path
import tempfile
import unittest
import warnings

import analyse_phase_d as APD
import analyse_phase_d2 as APD2
import fingerprint as FP
from app import results_eval as EV
```
`new_string`:
```python
import ast
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
import warnings

import analyse_phase_d as APD
import analyse_phase_d2 as APD2
import fingerprint as FP
from app import results_eval as EV
from app import results_provenance as RP
```

**1b.** The tests, inserted directly above the file's last two lines. `old_string` is those two lines,
`if __name__ == "__main__":` and `    unittest.main()`; `new_string` is the code below, which ends with the
same two lines, so they stay last.

```python
# ---- Task 2: app/results_provenance.py, git and the live side -----------------

# The result files of Jad's three experiments, as git names them.
SEEDED = [f"results/{prefix}_seed{seed}.txt" for prefix in REAL for seed in REAL_SEEDS]
CHILD_ENV = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONDONTWRITEBYTECODE="1")
LIVE_KEYS = {"python", "minor", "plant_sha", "plant_text_sha", "restart_needed",
             "derived_sha", "data_sha1", "derived_loaded_differs", "blocks", "import_errors"}
# Two file names git would quote by default, the second built from its code
# points so that this file stays ASCII.
SPACED = "notes/b c.txt"
ACCENTED = "notes/" + chr(0xE9) + "t" + chr(0xE9) + ".txt"


def _git_out(*args, cwd=ROOT):
    """git's own answer, asked directly, to compare the helper with; None on failure."""
    try:
        r = subprocess.run(["git", *args], cwd=cwd, capture_output=True, timeout=60,
                           env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
    except (OSError, subprocess.SubprocessError):
        return None
    return r.stdout.decode("utf-8", errors="replace") if r.returncode == 0 else None


def _clean(*relpaths):
    """True when git shows no change to `relpaths` in this checkout."""
    out = _git_out("status", "--porcelain", "--", *relpaths)
    return out is not None and out.strip() == ""


def _index_file():
    """This checkout's index file (a worktree keeps its own), or None."""
    rel = _git_out("rev-parse", "--git-path", "index")
    if not rel:
        return None
    path = Path(rel.strip())
    return path if path.is_absolute() else ROOT / path


def _child(code):
    """(True, stdout) of `code` run by a new interpreter from the repository
    root, or (False, the last line it wrote to stderr)."""
    r = subprocess.run([sys.executable, "-B", "-c", code], cwd=ROOT, capture_output=True,
                       timeout=900, env=CHILD_ENV)
    if r.returncode != 0:
        lines = r.stderr.decode("utf-8", errors="replace").strip().splitlines()
        return False, lines[-1] if lines else f"exit code {r.returncode}"
    return True, r.stdout.decode("utf-8", errors="replace").strip()


class ProvenanceLiveTests(unittest.TestCase):
    """results_provenance part 1, against this checkout and against fixtures."""

    def _need_git(self):
        git = RP.Git(ROOT)
        if not git.available:
            self.skipTest(f"git is not usable here ({git.reason})")
        return git

    def test_optional_locks_are_set_before_fingerprint_is_imported(self):
        tree = ast.parse(Path(RP.__file__).read_text(encoding="utf-8"))
        order = []
        for node in tree.body:
            if isinstance(node, ast.Assign) and "GIT_OPTIONAL_LOCKS" in ast.dump(node):
                order.append("locks")
            elif isinstance(node, ast.Import) and any(a.name == "fingerprint" for a in node.names):
                order.append("fingerprint")
        self.assertEqual(order, ["locks", "fingerprint"])
        self.assertEqual(os.environ.get("GIT_OPTIONAL_LOCKS"), "0")

    def test_git_reads_this_checkout(self):
        git = self._need_git()
        self.assertIsNone(git.reason)
        self.assertEqual(git.head_short(), _git_out("rev-parse", "--short", "HEAD").strip())
        full = _git_out("rev-parse", "HEAD").strip()
        self.assertEqual(git.resolve("HEAD"), full)
        self.assertEqual(git.resolve(full[:12]), full)
        for refused in ("--output=x", "HEAD~1", "a b", ""):
            self.assertIsNone(git.resolve(refused), refused)
        self.assertIsNone(git.resolve("f" * 40))
        self.assertTrue(git.available, "an unknown commit is an answer, not a broken git")

    def test_last_commits_equal_a_per_file_log(self):
        git = self._need_git()
        rels = [r for r in SEEDED if (ROOT / r).is_file()]
        if not rels:
            self.skipTest("no results/<prefix>_seed<N>.txt in this checkout")
        got = git.last_commits(rels)
        self.assertEqual(sorted(got), sorted(rels))
        for rel in rels:
            one = _git_out("log", "-1", "--format=%h%x09%cI", "--", rel).strip()
            short, _, date = one.partition("\t")
            self.assertEqual(got[rel], {"short": short, "date": date}, rel)

    def test_status_leaves_out_a_clean_committed_file(self):
        git = self._need_git()
        rel = "results/phase_d_seed0.txt"
        if not (ROOT / rel).is_file() or not _clean(rel):
            self.skipTest(f"{rel} is absent or changed in this checkout")
        self.assertNotIn(rel, git.status([rel]))
        self.assertEqual(git.status([]), {})
        self.assertEqual(git.last_commits([]), {})

    def test_a_missing_git_is_unavailable_and_answers_none(self):
        git = RP.Git(ROOT, exe="git-does-not-exist")
        self.assertFalse(git.available)
        self.assertEqual(git.reason, "missing")
        self.assertIsNone(git.run("--version"))
        self.assertIsNone(git.head_short())
        self.assertIsNone(git.resolve("HEAD"))
        self.assertIsNone(git.show("HEAD", "plant.py"))
        self.assertEqual(git.last_commits(["results"]), {})
        self.assertEqual(git.status(["results"]), {})
        self.assertIsNone(RP.plant_at(git, "HEAD"))
        self.assertIsNone(RP.road_sha_at(git, "HEAD"))

    def test_a_folder_outside_any_checkout_is_not_a_repo(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            ceiling = {"GIT_CEILING_DIRECTORIES": str(Path(tmp).resolve().parent)}
            with mock.patch.dict(os.environ, ceiling):
                git = RP.Git(tmp)
            self.assertEqual((git.available, git.reason), (False, "not_a_repo"))
            self.assertIsNone(git.head_short())
            gone = RP.Git(Path(tmp) / "absent")
            self.assertEqual((gone.available, gone.reason), (False, "not_a_repo"))

    def test_a_temporary_repository_reads_back(self):
        self._need_git()
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)

            def git(*args):
                r = subprocess.run(["git", *args], cwd=repo, capture_output=True, timeout=60)
                self.assertEqual(r.returncode, 0, r.stderr.decode("utf-8", errors="replace"))
                return r.stdout.decode("utf-8", errors="replace").strip()

            git("init", "-q")
            for key, value in (("user.name", "results tab test"),
                               ("user.email", "test@example.invalid"),
                               ("commit.gpgsign", "false"), ("core.autocrlf", "false")):
                git("config", key, value)
            (repo / "notes").mkdir()
            (repo / "a.txt").write_bytes(b"one\n")
            (repo / SPACED).write_bytes(b"two\n")
            (repo / ACCENTED).write_bytes(b"three\n")
            git("add", "-A")
            git("commit", "-q", "-m", "first")
            first = git("rev-parse", "HEAD")
            (repo / "a.txt").write_bytes(b"one, again\n")
            git("commit", "-q", "-am", "second")
            second = git("rev-parse", "HEAD")
            (repo / SPACED).write_bytes(b"two, changed\n")
            (repo / "notes" / "new.txt").write_bytes(b"four\n")

            helper = RP.Git(repo)
            self.assertTrue(helper.available, helper.reason)
            last = helper.last_commits(["a.txt", "notes"])
            self.assertEqual(sorted(last), sorted(["a.txt", SPACED, ACCENTED]))
            self.assertTrue(second.startswith(last["a.txt"]["short"]))
            self.assertTrue(first.startswith(last[SPACED]["short"]))
            self.assertTrue(first.startswith(last[ACCENTED]["short"]))
            self.assertEqual(last["a.txt"]["date"], git("log", "-1", "--format=%cI", "--", "a.txt"))
            self.assertEqual(helper.status(["a.txt", "notes"]),
                             {SPACED: "M", "notes/new.txt": "??"})
            self.assertEqual(helper.resolve(first[:10]), first)
            self.assertEqual(helper.show(first, "a.txt"), b"one\n")
            self.assertIsNone(helper.show(first, "notes/new.txt"))
            self.assertTrue(helper.available)

    def test_hashes_equal_fingerprint_sha_files(self):
        sources = [(ROOT / n).read_bytes() for n in FP.PLANT_FILES]
        self.assertEqual(RP.code_hash(sources), FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(RP.byte_hash(sources), FP._sha_files(FP.PLANT_FILES, code_only=False))
        lf = [s.replace(b"\r\n", b"\n") for s in sources]
        crlf = [s.replace(b"\n", b"\r\n") for s in lf]
        self.assertEqual(RP.code_hash(lf), RP.code_hash(crlf))
        self.assertEqual(RP.byte_hash(lf), RP.byte_hash(crlf))
        commented = [lf[0] + b"\n# a comment the code hash does not see\n"] + lf[1:]
        self.assertEqual(RP.code_hash(commented), RP.code_hash(lf))
        self.assertNotEqual(RP.byte_hash(commented), RP.byte_hash(lf))
        # A file that does not parse is hashed as bytes, after the same CRLF rule.
        self.assertEqual(RP.code_hash([b"def (:\r\n"]), hashlib.sha256(b"def (:\n").hexdigest()[:16])

    def test_minor(self):
        self.assertEqual(RP.minor("3.12.10"), "3.12")
        self.assertEqual(RP.minor("3.13.2"), "3.13")
        self.assertEqual(RP.minor(platform.python_version()),
                         ".".join(platform.python_version_tuple()[:2]))
        for bad in (None, "", "None", "three"):
            self.assertIsNone(RP.minor(bad), bad)

    def test_plant_at_head_equals_the_files_on_disk(self):
        git = self._need_git()
        if not _clean(*FP.PLANT_FILES):
            self.skipTest("the plant files have uncommitted changes, so HEAD's plant is not the disk's")
        got = RP.plant_at(git, "HEAD")
        self.assertEqual(got, {"plant_sha": FP._sha_files(FP.PLANT_FILES),
                               "plant_text_sha": FP._sha_files(FP.PLANT_FILES, code_only=False)})
        self.assertEqual(RP.plant_at(git, git.resolve("HEAD")), got)
        self.assertIsNone(RP.plant_at(git, "f" * 40))

    def test_road_sha_at_head_equals_random_road(self):
        git = self._need_git()
        try:
            import random_road
        except (Exception, SystemExit) as exc:
            self.skipTest(f"random_road cannot be imported here ({type(exc).__name__})")
        if not _clean("random_road.py"):
            self.skipTest("random_road.py has uncommitted changes")
        self.assertEqual(RP.road_sha_at(git, "HEAD"), random_road.code_sha())

    def test_data_fingerprint_equals_derive_params(self):
        if importlib.util.find_spec("pandas") is None:
            self.skipTest("pandas is not installed, and derive_params imports it")
        ok, out = _child("import derive_params; print(derive_params.fingerprint()['data_sha1'])")
        if not ok:
            self.skipTest(f"derive_params could not be imported in a subprocess: {out}")
        self.assertEqual(RP.data_fingerprint(ROOT), out)

    def test_derived_sha_equals_train(self):
        missing = [m for m in ("torch", "stable_baselines3") if importlib.util.find_spec(m) is None]
        if missing:
            self.skipTest(f"{', '.join(missing)} not installed, and train imports them")
        ok, out = _child("import train; print(train.derived_sha())")
        if not ok:
            self.skipTest(f"train could not be imported in a subprocess: {out}")
        self.assertEqual(RP.derived_sha(ROOT), out)

    def test_data_hashes_on_a_temporary_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertIsNone(RP.data_fingerprint(root))
            self.assertIsNone(RP.derived_sha(root))
            (root / "data").mkdir()
            samples, points = b"a,b\r\n1,2\r\n", b"x\r\n3\r\n"
            (root / "data" / "master_samples.csv").write_bytes(samples)
            (root / "data" / "master_points.csv").write_bytes(points)
            want = hashlib.sha1(b"a,b\n1,2\nx\n3\n").hexdigest()[:16]
            self.assertEqual(RP.data_fingerprint(root), want)
            path = root / "data" / "derived_params.json"
            path.write_text(json.dumps({"b": [1, 2], "a": {"c": 0.5}, "_note": "kept out"}),
                            encoding="utf-8")
            kept = json.dumps({"a": {"c": 0.5}, "b": [1, 2]}, sort_keys=True)
            self.assertEqual(RP.derived_sha(root), hashlib.sha256(kept.encode()).hexdigest()[:16])
            for text in ("[1, 2]", "{not json"):
                path.write_text(text, encoding="utf-8")
                self.assertIsNone(RP.derived_sha(root), text)

    def test_derived_loaded_differs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "data").mkdir()
            (root / "data" / "derived_params.json").write_text(json.dumps({"a": 1, "_b": 2}),
                                                                encoding="utf-8")
            fake = types.SimpleNamespace(_CACHE={})
            with mock.patch.dict(sys.modules, {"derived": fake}):
                self.assertFalse(RP.derived_loaded_differs(root), "nothing loaded yet")
                fake._CACHE["d"] = {"a": 1, "_b": 99}
                self.assertFalse(RP.derived_loaded_differs(root), "underscore keys are not values")
                fake._CACHE["d"] = {"a": 2}
                self.assertTrue(RP.derived_loaded_differs(root))
            with mock.patch.dict(sys.modules):
                sys.modules.pop("derived", None)
                self.assertFalse(RP.derived_loaded_differs(root))

    def test_live_side(self):
        env_before = {k: os.environ.get(k) for k in ("DERIVING_PARAMS", "OMP_NUM_THREADS")}
        index = _index_file()
        index_before = index.stat().st_mtime_ns if index is not None and index.is_file() else None
        modules_before = set(sys.modules)
        live = RP.live_side(ROOT)
        self.assertEqual(set(live), LIVE_KEYS)
        self.assertEqual(live["python"], platform.python_version())
        self.assertEqual(live["minor"], RP.minor(platform.python_version()))
        self.assertEqual(live["plant_sha"], FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(live["plant_text_sha"], FP._sha_files(FP.PLANT_FILES, code_only=False))
        self.assertIs(live["restart_needed"], live["plant_sha"] != RP.IMPORT_PLANT_SHA)
        self.assertEqual(live["derived_sha"], RP.derived_sha(ROOT))
        self.assertEqual(live["data_sha1"], RP.data_fingerprint(ROOT))
        self.assertIsInstance(live["derived_loaded_differs"], bool)
        for protocol in ("phase-d", "d2"):
            module = f"fingerprint.plant_fingerprint({protocol})"
            if any(e["module"] == module for e in live["import_errors"]):
                self.assertNotIn(protocol, live["blocks"])
                continue
            block = live["blocks"][protocol]
            self.assertEqual(block["plant_sha"], live["plant_sha"])
            self.assertLessEqual(set(FP.FATAL), set(block), protocol)
        self.assertEqual({k: os.environ.get(k) for k in env_before}, env_before)
        new = set(sys.modules) - modules_before
        self.assertFalse({"derive_params", "train", "record_agents", "knock_margin"} & new)
        if index_before is not None:
            self.assertEqual(index.stat().st_mtime_ns, index_before, ".git/index was rewritten")

    def test_live_side_restart_and_import_errors(self):
        with mock.patch.object(RP, "IMPORT_PLANT_SHA", "0" * 16):
            self.assertIs(RP.live_side(ROOT, protocols=())["restart_needed"], True)

        def refuses(protocol="phase-d", **advisory):
            raise AssertionError("an import-time check failed")

        with mock.patch.object(RP.FP, "plant_fingerprint", refuses):
            live = RP.live_side(ROOT)
        self.assertEqual(live["blocks"], {})
        self.assertEqual(live["import_errors"], [
            {"module": "fingerprint.plant_fingerprint(phase-d)", "type": "AssertionError"},
            {"module": "fingerprint.plant_fingerprint(d2)", "type": "AssertionError"}])
        with mock.patch.object(RP.FP, "plant_fingerprint", side_effect=SystemExit(2)):
            got = RP.live_side(ROOT, protocols=("d2",))["import_errors"]
        self.assertEqual(got, [{"module": "fingerprint.plant_fingerprint(d2)", "type": "SystemExit"}])
        with mock.patch.object(RP.FP, "plant_fingerprint", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                RP.live_side(ROOT, protocols=("d2",))
        self.assertEqual(RP.live_side(ROOT, protocols=("phase-x",))["import_errors"],
                         [{"module": "fingerprint.plant_fingerprint(phase-x)", "type": "ValueError"}])


if __name__ == "__main__":
    unittest.main()
```

What these pin, one line each:
- `GIT_OPTIONAL_LOCKS` is set BEFORE `fingerprint` is imported: an AST order check over the module, so the
  shell's own export cannot make it pass;
- the helper on this checkout: `head_short`, `resolve` (full and short ids; an option, revision syntax, a
  space and an empty string refused without running git), and an unknown commit leaving git available;
- `last_commits` over the 24 result files equals a per-file `git log -1` for each one;
- `status` leaves out a clean committed file; empty pathspecs give `{}`;
- a missing executable: `available` False, reason `"missing"`, every call `None` or `{}`, `plant_at` and
  `road_sha_at` `None`;
- a folder outside any checkout, and one that does not exist: reason `"not_a_repo"` (with
  `GIT_CEILING_DIRECTORIES`, so a repository above the temporary folder cannot answer);
- a temporary repository: the newest commit per file, a path with a space, a non-ASCII path, a modified
  file (`M`) and an untracked one (`??`), `resolve` of a short id, `show` of a committed and an uncommitted
  file;
- `code_hash` and `byte_hash` equal `fingerprint._sha_files` on the three plant files and ignore CRLF; the
  code hash ignores a comment where the byte hash does not; a file that does not parse is hashed as bytes
  after the same CRLF rule;
- `minor`; `plant_at("HEAD")` equals the files on disk (skipped when the plant files are modified);
  `road_sha_at("HEAD")` equals `random_road.code_sha()` (skipped when `random_road` cannot be imported or
  is modified);
- the two data hashes equal `derive_params.fingerprint()["data_sha1"]` and `train.derived_sha()`, each
  computed in a SUBPROCESS (skipped, with the reason, when pandas, or torch and stable-baselines3, are not
  installed, or when the child cannot import the module), and on a temporary tree: CRLF, underscore keys
  left out, a list, broken JSON, missing files;
- `derived_loaded_differs` with a stand-in `derived` module in `sys.modules`;
- `live_side`: its exact keys, each value against its source, every FATAL field in each live block,
  `DERIVING_PARAMS` and `OMP_NUM_THREADS` unchanged, none of the four forbidden modules imported, and the
  index file (found with `git rev-parse --git-path index`, so a worktree's own index) not rewritten;
  `restart_needed` when the import-time hash differs; a `plant_fingerprint` that raises `AssertionError`,
  `SystemExit` or (unknown protocol) `ValueError` listed in `import_errors`; `KeyboardInterrupt` propagates.

- [ ] **Step 2: Run the tests and see them fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.ProvenanceLiveTests -v
```

Expected (observed in drafting):
```
ImportError: Failed to import test module: test_results
...
ImportError: cannot import name 'results_provenance' from 'app' (unknown location)
...
Ran 1 test in 0.000s

FAILED (errors=1)
```
Until Step 3 every class in `app/test_results.py` fails to load this way, Task 1's included, because the
import is at module level.

- [ ] **Step 3: Write `app/results_provenance.py`**

Create it with the Write tool (its `\x00` and `\r\n` escapes must arrive as typed):

```python
"""Where the numbers on the results tab came from: git, the live plant, the plant states.

READ-ONLY. Nothing here writes a file, and every git command it runs only
reads. GIT_OPTIONAL_LOCKS is set to "0" for the whole process the moment this
module is imported, before anything can call fingerprint.py: fingerprint._git
runs `git status` with the inherited environment, and a status allowed to
take its optional lock may rewrite .git/index.

THE GIT HELPER. One class, Git, makes every git call of a build, each with a
timeout. A missing git, a folder that is not a checkout, a timeout or any
other failure to run git leaves the helper unavailable, with a reason, and
every later call returns None without running anything: a build without git
omits the git facts and changes nothing else. A commit named in a result file
reaches git only after it matches a plain ref pattern, so the text of a file
can never become a git option.

THE LIVE SIDE. live_side() describes this tree: the plant hashes read from
disk, the hash of the derived constants and of the logs they were derived
from, and the live fingerprint block of each protocol, rendered by
fingerprint.format_block and parsed back by results_eval, so that a result
file's block and the live one are compared as the same text. The two data
hashes are copies of train.derived_sha and derive_params.fingerprint, each
tested equal to its original in a subprocess. This module never imports
derive_params (importing it sets DERIVING_PARAMS for the whole process, which
turns every missing derived constant into NaN), train, record_agents or
knock_margin.

THE PYTHON VERSION. fingerprint._code_only hashes the interpreter's own syntax
tree, so a plant hash depends on the Python minor version. A hash recorded
under another Python is compared only through git: the recorded commit's
plant files are read from git and hashed under this Python (plant_at,
road_sha_at), cached per commit, since a commit never changes.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import subprocess
import sys
from pathlib import Path

# Before the fingerprint import below, on purpose: see the module docstring.
os.environ["GIT_OPTIONAL_LOCKS"] = "0"

import fingerprint as FP  # the repository root; standard library only at import
from app import results_eval as EV

TAGS = ("sep17-before-merge", "ghassan-before-merge")
STATES = ("forced", "not_recorded", "another", "cannot_compare", "same_code", "same")
GIT_TIMEOUT_S = 15
# The plant code on disk when this module was imported, which is the plant the
# server runs when the module is imported at start. live_side compares the
# files on disk against it; a difference means the server needs a restart.
IMPORT_PLANT_SHA = FP._sha_files(FP.PLANT_FILES)

# A ref git may be asked about: a hex sha, a tag or HEAD. No leading dash (an
# option), no revision syntax, no spaces.
_REF = re.compile(r"^[0-9A-Za-z][0-9A-Za-z._/-]{0,199}$")
_OBJECT_ID = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_PLANT_AT = {}
_ROAD_AT = {}


class Git:
    """Every git call of a build: read-only, each with a timeout.

    `available` turns False, and `reason` says why, the first time git cannot
    be run ("missing", "timeout", "error") or the folder is not a checkout
    ("not_a_repo"); from then on every call returns None and runs nothing. A
    command that runs and fails, such as asking for a commit this clone does
    not have, returns None and leaves the helper available: an unknown commit
    is an answer, not a broken git.
    """

    def __init__(self, root, exe: str = "git", timeout: float = GIT_TIMEOUT_S):
        self.root = Path(root)
        self.exe = exe
        self.timeout = timeout
        self.available = True
        self.reason = None
        self._resolved = {}
        if not self.root.is_dir():
            self._lose("not_a_repo")
        elif self.run("rev-parse", "--git-dir") is None and self.available:
            self._lose("not_a_repo")

    def _lose(self, reason):
        self.available = False
        self.reason = reason

    def run(self, *args: str, binary: bool = False):
        """git's stdout (text, or bytes when `binary`), or None on any failure."""
        if not self.available:
            return None
        try:
            out = subprocess.run([self.exe, *args], cwd=self.root, capture_output=True,
                                 timeout=self.timeout,
                                 env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"))
        except FileNotFoundError:
            self._lose("missing")
            return None
        except subprocess.TimeoutExpired:
            self._lose("timeout")
            return None
        except (OSError, ValueError, subprocess.SubprocessError):
            self._lose("error")
            return None
        if out.returncode != 0:
            return None
        return out.stdout if binary else out.stdout.decode("utf-8", errors="replace")

    def resolve(self, sha: str):
        """The full commit id a recorded sha, a tag or HEAD names here, or None:
        unknown here, ambiguous, not a commit, or not a plain ref at all."""
        if not isinstance(sha, str) or not _REF.match(sha):
            return None
        if sha not in self._resolved:
            out = self.run("rev-parse", "--verify", "--quiet", sha + "^{commit}")
            full = (out or "").strip()
            self._resolved[sha] = full if _OBJECT_ID.match(full) else None
        return self._resolved[sha]

    def show(self, commit: str, relpath: str):
        """The bytes of `relpath` as `commit` holds it, or None."""
        if not isinstance(commit, str) or not _REF.match(commit):
            return None
        return self.run("show", f"{commit}:{relpath}", binary=True)

    def head_short(self):
        """The short id of HEAD, or None."""
        return (self.run("rev-parse", "--short", "HEAD") or "").strip() or None

    def last_commits(self, relpaths: list[str]) -> dict[str, dict]:
        """Each file's newest commit, from ONE log pass over `relpaths`.

        rel (forward slashes, from the repository root) -> {"short", "date"},
        the date being the committer date in ISO form. A merge names a file
        only when the merge itself changed it against every parent, so a file
        a merge only carried over keeps the commit that made it.
        """
        if not relpaths:
            return {}
        out = self.run("-c", "core.quotePath=false", "log", "--format=%x00%h%x09%cI",
                       "--name-only", "--diff-merges=dense-combined", "--",
                       *[str(p).replace("\\", "/") for p in relpaths])
        found = {}
        for record in (out or "").split("\x00")[1:]:
            head, _, names = record.partition("\n")
            short, _, date = head.partition("\t")
            for name in names.splitlines():
                if name and name not in found:
                    found[name] = {"short": short.strip(), "date": date.strip()}
        return found

    def status(self, relpaths: list[str]) -> dict[str, str]:
        """rel -> its git status code ("M", "??", ...) for every changed or
        untracked file under `relpaths`, from ONE status call; a clean file is
        absent. Read with -z, so no path is quoted and a rename is
        "XY to" followed by "from"."""
        if not relpaths:
            return {}
        out = self.run("status", "--porcelain=v1", "-z", "--untracked-files=all", "--",
                       *[str(p).replace("\\", "/") for p in relpaths])
        fields = (out or "").split("\x00")
        codes, i = {}, 0
        while i < len(fields):
            entry, i = fields[i], i + 1
            if len(entry) < 4:
                continue
            code = entry[:2]
            codes[entry[3:]] = code.strip()
            if "R" in code or "C" in code:
                i += 1
        return codes


def minor(version_text: str | None) -> str | None:
    """The minor version of a version text, or None when there is none."""
    m = re.match(r"\s*(\d+)\.(\d+)", version_text) if isinstance(version_text, str) else None
    return f"{m.group(1)}.{m.group(2)}" if m else None


def code_hash(sources: list[bytes]) -> str:
    """fingerprint._sha_files(code_only=True) over sources already read."""
    h = hashlib.sha256()
    for raw in sources:
        raw = raw.replace(b"\r\n", b"\n")
        code = FP._code_only(raw.decode("utf-8", errors="replace"))
        h.update(code.encode("utf-8") if code is not None else raw)
    return h.hexdigest()[:16]


def byte_hash(sources: list[bytes]) -> str:
    """fingerprint._sha_files(code_only=False) over sources already read."""
    h = hashlib.sha256()
    for raw in sources:
        h.update(raw.replace(b"\r\n", b"\n"))
    return h.hexdigest()[:16]


def _commit_id(git, commit):
    """A full object id as it is; anything else through git.resolve."""
    if isinstance(commit, str) and _OBJECT_ID.match(commit):
        return commit
    return git.resolve(commit)


def plant_at(git: Git, commit: str) -> dict | None:
    """{"plant_sha", "plant_text_sha"} of fingerprint.PLANT_FILES as `commit`
    holds them, hashed under THIS Python; None when git cannot read them."""
    full = _commit_id(git, commit)
    if full is None:
        return None
    if full not in _PLANT_AT:
        sources = []
        for name in FP.PLANT_FILES:
            raw = git.show(full, name)
            if raw is None:
                return None
            sources.append(raw)
        _PLANT_AT[full] = {"plant_sha": code_hash(sources), "plant_text_sha": byte_hash(sources)}
    return dict(_PLANT_AT[full])


def _road_code_sha(raw):
    """random_road.code_sha's rule over a file's bytes: the text as inspect
    reads it (UTF-8, a byte-order mark dropped, universal newlines), its code
    without docstrings by fingerprint._code_only, then SHA-256."""
    src = raw.decode("utf-8-sig", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
    code = FP._code_only(src)
    return hashlib.sha256((code if code is not None else src).encode("utf-8")).hexdigest()[:16]


def road_sha_at(git: Git, commit: str) -> str | None:
    """random_road.py's road_sha as `commit` holds the file, under THIS Python."""
    full = _commit_id(git, commit)
    if full is None:
        return None
    if full not in _ROAD_AT:
        raw = git.show(full, "random_road.py")
        if raw is None:
            return None
        _ROAD_AT[full] = _road_code_sha(raw)
    return _ROAD_AT[full]


def data_fingerprint(root) -> str | None:
    """derive_params.fingerprint()["data_sha1"], copied: the logs the derived
    constants were made from. None when either file cannot be read."""
    h = hashlib.sha1()
    try:
        for name in ("master_samples.csv", "master_points.csv"):
            h.update((Path(root) / "data" / name).read_bytes().replace(b"\r\n", b"\n"))
    except OSError:
        return None
    return h.hexdigest()[:16]


def _values_sha(d):
    """train.derived_sha's hash of a loaded derived_params.json."""
    vals = {k: v for k, v in d.items() if not k.startswith("_")}
    return hashlib.sha256(json.dumps(vals, sort_keys=True).encode()).hexdigest()[:16]


def derived_sha(root) -> str | None:
    """train.derived_sha(), copied, over root/data/derived_params.json."""
    try:
        d = json.loads((Path(root) / "data" / "derived_params.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return _values_sha(d) if isinstance(d, dict) else None


def derived_loaded_differs(root) -> bool:
    """True when derived.py holds constants in memory and they are not the
    ones in root/data/derived_params.json on disk. False when derived.py was
    never imported or has not loaded its file yet."""
    mod = sys.modules.get("derived")
    cache = getattr(mod, "_CACHE", None)
    if not isinstance(cache, dict) or "d" not in cache:
        return False
    loaded = cache["d"]
    if not isinstance(loaded, dict):
        return True
    try:
        return _values_sha(loaded) != derived_sha(root)
    except (TypeError, ValueError):
        return True


def live_side(root, protocols=("phase-d", "d2")) -> dict:
    """This tree as the results tab compares against it. See the module docstring.

    A protocol whose live fingerprint cannot be built (an import that fails,
    an assertion at import, an unknown protocol) is absent from "blocks" and
    listed in "import_errors" with the exception's type name; KeyboardInterrupt
    is never caught."""
    python = platform.python_version()
    plant_sha = FP._sha_files(FP.PLANT_FILES)
    blocks, errors = {}, []
    for protocol in protocols:
        try:
            text = FP.format_block(FP.plant_fingerprint(protocol))
        except (Exception, SystemExit) as exc:
            errors.append({"module": f"fingerprint.plant_fingerprint({protocol})",
                           "type": type(exc).__name__})
            continue
        blocks[protocol] = EV.parse_fingerprint_block(text.splitlines())
    return {
        "python": python,
        "minor": minor(python),
        "plant_sha": plant_sha,
        "plant_text_sha": FP._sha_files(FP.PLANT_FILES, code_only=False),
        "restart_needed": plant_sha != IMPORT_PLANT_SHA,
        "derived_sha": derived_sha(root),
        "data_sha1": data_fingerprint(root),
        "derived_loaded_differs": derived_loaded_differs(root),
        "blocks": blocks,
        "import_errors": errors,
    }
```

- [ ] **Step 4: Run the tests and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.ProvenanceLiveTests -v
$PY -m app.test_results 2>&1 | tail -n 3
git status --porcelain -- app
```

Expected (observed in drafting on this machine, Python 3.12.10, from a copy outside the repository built
from Task 1's planned files): seventeen lines ending `... ok`, then `Ran 17 tests in 3.6s` and `OK` (about
4 s: two of the tests start a new interpreter, one importing `train` and so torch); nothing is skipped
here. On another machine a test may print `skipped '...'` with its reason (no git; pandas, or torch and
stable-baselines3, not installed; plant files or `random_road.py` modified): read it, a skip is not a pass.
The whole file: `Ran 44 tests` (Task 1's 27 and these 17) and `OK`. `git status --porcelain -- app` lists
` M app/test_results.py` and `?? app/results_provenance.py`, nothing else.

If `test_live_side` fails ONLY on its last assertion (".git/index was rewritten"), check whether the other
session ran git in this tree during the run; re-run before suspecting the module.

- [ ] **Step 5: The byte check and the app's scans**

`app/test_replay.py`'s read-only scan and `app.test_agents`' `NoNetworkTests` and `PrintScanTests` read
every `app/*.py`, the new module and the test file included. (`NoWriteTests` reads only `NEW_MODULES`;
Task 5 adds `results_provenance.py` to it.)

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -c "import pathlib, sys; r={p: ([hex(ord(c)) for c in pathlib.Path(p).read_text(encoding='utf-8') if ord(c) > 127], pathlib.Path(p).read_text(encoding='utf-8').count(chr(92) + 'u')) for p in sys.argv[1:]}; print(r); sys.exit(1 if any(a or b for a, b in r.values()) else 0)" app/results_provenance.py app/test_results.py
$PY -W error::SyntaxWarning -c "import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]; print('compiled:', ', '.join(sys.argv[1:]))" app/results_provenance.py app/test_results.py
$PY -m unittest app.test_agents.NoNetworkTests app.test_agents.PrintScanTests 2>&1 | tail -3
$PY -m app.test_replay 2>&1 | tee "$SP/r1a_replay_task02.txt" | grep -E "READ-ONLY|checks pass"
```

Expected (the times vary):
```
{'app/results_provenance.py': ([], 0), 'app/test_results.py': ([], 0)}
compiled: app/results_provenance.py, app/test_results.py
Ran 5 tests in 0.377s

OK
  PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns
49 of 49 checks pass
```
Observed in drafting: the first two lines on the drafted files; `Ran 5 tests`, `OK` and `49 of 49` on this
tree before the module existed (`app.test_replay` took about 98 s), while the same scans, run over the
drafted module and test file from copies of `app/test_agents.py` and `app/test_replay.py` pointed at them
(`NoWriteTests` with `NEW_MODULES` set to the module), found nothing.

- [ ] **Step 6: Commit**

By explicit path only: another session is editing `CLAUDE.md`, `handoff.md`, `team/jad.md` and
`NEXT_SESSION_*.md` in this tree.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
cat > "$SP/r1a_msg_task02.txt" <<'EOF'
Results tab R1a (task 2): results_provenance part 1, the git helper and the live side

app/results_provenance.py: one read-only git helper (a timeout on every call,
a reason when git is unavailable, recorded refs filtered before they reach
git, paths read unquoted), the plant hashes of a commit under this Python,
copies of train.derived_sha and derive_params.fingerprint tested against the
originals in subprocesses, and live_side(). GIT_OPTIONAL_LOCKS is set before
fingerprint is imported. Tests: ProvenanceLiveTests in app/test_results.py.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
git add app/results_provenance.py app/test_results.py
git commit -F "$SP/r1a_msg_task02.txt" -- app/results_provenance.py app/test_results.py
git log -1 --format=%B | sed '/^$/d' | tail -n 1
git status --short -- app/results_provenance.py app/test_results.py
```

Expected (not run in this repository in drafting): `git` may warn `LF will be replaced by CRLF` for the two
files (`core.autocrlf`, harmless); then
`[JMF-2340550-results-tab <sha>] Results tab R1a (task 2): results_provenance part 1, the git helper and
the live side`, `2 files changed`, `create mode 100644 app/results_provenance.py`, and the last line of the
message, `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. `git status --short` then
prints nothing for the two paths.

### Task 3: `results_provenance` part 2 -- the plant state of each file and of each experiment

**Files:**
- Modify: `app/results_provenance.py`: the module docstring's last paragraph (Step 3), then
  `tag_for`, `classify_eval`, `section_provenance` and their helpers appended at the end (Step 4)
- Modify: `app/test_results.py`: one import (Step 1a), and the block of Step 1b inserted directly above
  the final `if __name__ == "__main__":` guard, below Task 2's block
- Test: `app/test_results.py`, class `ProvenanceStateTests` (21 tests)

**Interfaces:**
- Consumes:
  - Task 1, `app/results_eval.py`: `parse_eval_file(path) -> dict` (this task reads its `"title"`,
    `"protocol"`, `"fingerprint"` and `"forced"`; the fingerprint values are the text `format_block`
    wrote, `git_dirty_plant_files` reading `""` when the list was empty), and
    `protocol_from_fingerprint(fp: dict[str, str]) -> str | None`.
  - Task 1, `app/test_results.py`: `ROOT`, `REAL`, `REAL_SEEDS`, `EV`, `FP`.
  - Task 2: `Git`, `TAGS`, `STATES`, `minor`, `plant_at`, `road_sha_at`, `live_side` and its dict; in the
    test file, `RP`, `SEEDED` and `_clean`, and the import block Task 2 wrote (Step 1a edits it).
  - `fingerprint.FATAL`.
- Produces, in `app/results_provenance.py` (Task 4 calls these):
```python
def tag_for(git: Git, plant_sha: str | None) -> str | None: ...
def classify_eval(parsed: dict, live: dict, git: Git, rel: str,
                  last: dict, status: dict, title_protocols: dict[str, str]) -> dict: ...
# -> {"state": one of STATES,
#     "reason": None | "python" | "no_git_route" | "dirty" | "one_sided" | "restart"
#               | "protocol" | "import" | "derived_differs",
#     "route": None | "same_python" | "git",
#     "protocol": str | None,
#     "recorded": {"plant_sha", "python", "git_head", "derived_sha"},   # each str | None
#     "live": {"plant_sha": str, "python": str},
#     "differs": [FATAL field, ...],            # shared FATAL fields whose text differs
#     "tag": str | None,                        # only for state "another"
#     "forced": [the file's "!!" lines and their indented lines],
#     "file": {"rel": rel, "commit": {"short", "date"} | None, "changed": bool}}
def section_provenance(per_file: dict[int, dict]) -> dict: ...
# -> {"state": common state or "mixed", "reason": common reason or None, "tag": common tag or None,
#     "commits": sorted distinct recorded git_head[:7], "files": {str(seed): per_file[seed]}}
#    raises ValueError for an empty dict: call it only for a section with at least one parsed file
```
  How Task 4 calls them: once per build, `git = Git(git_root)`, `live = live_side(git_root)`,
  `last = git.last_commits(rels)` and `status = git.status(rels)` over the result files, where each
  `rel` is `"results/<name>"` relative to `git_root` with forward slashes, the same key
  `classify_eval(..., rel, last, status, ...)` looks up (on an unavailable `Git` both are `{}`).
  `title_protocols` maps a header title to its protocol, from `evaluate.PROTOCOLS`:
  `{header: name for name, (_episodes, header, _prefix) in evaluate.PROTOCOLS.items()}`, which is
  `{"PHASE D EVALUATION": "phase-d", "PHASE D2 EVALUATION (randomised climb)": "d2"}` today (a test pins
  the two equal).
- Produces, in `app/test_results.py`: `TITLE_PROTOCOLS`, `REASONS`, `CLASSIFIED_KEYS`, `D2_FILE`.

  The rules, in order (spec section 5.2 and contract section 2.2): `forced` when the file has `!!` lines;
  `not_recorded` without `plant_sha`; the protocol is the header's, else the block's scenario, else the
  title's; no live block for it gives `cannot_compare` with `"import"` when `live["import_errors"]` lists
  `fingerprint.plant_fingerprint(<protocol>)`, else `"protocol"`. A valid comparison is the same Python
  minor (`"same_python"`), or the git route (`"git"`): the recorded commit is here, its plant files' byte
  hash equals the recorded `plant_text_sha`, and `git_dirty_plant_files` is `""`; the copy compared then
  carries the commit's plant hashed under this Python and, in a d2 scenario, the commit's `road_sha`.
  Without one: `"python"` (no commit here, or git cannot read its plant), `"dirty"` (plant files listed as
  dirty), `"no_git_route"` (byte hash differs, cleanliness not recorded, or the commit's `random_road.py`
  cannot be read). Then `another` when a shared FATAL field differs (reason `None`) or only a recorded
  `derived_sha` differs from the live one (`"derived_differs"`), with the tag of the COMPARED plant hash;
  `cannot_compare` `"one_sided"` when a FATAL field is on one side only, or a `derived_sha` is recorded
  while the live one cannot be computed; `cannot_compare` `"restart"` when `live["restart_needed"]`;
  `same` when a recorded `derived_sha` equals the live one; else `same_code`.

- [ ] **Step 1: Write the failing tests**

Edit `app/test_results.py` with the Edit tool (ASCII only, as before).

**1a.** One import. `old_string`:
```python
import platform
import subprocess
```
`new_string`:
```python
import platform
import re
import subprocess
```

**1b.** The tests, inserted directly above the file's last two lines, below Task 2's block.
`old_string` is the two guard lines; `new_string` is the code below, which ends with them:

```python
# ---- Task 3: app/results_provenance.py, the plant state of a file -------------

# A header title to its protocol, as Task 4 builds it from evaluate.PROTOCOLS.
TITLE_PROTOCOLS = {"PHASE D EVALUATION": "phase-d",
                   "PHASE D2 EVALUATION (randomised climb)": "d2"}
REASONS = (None, "python", "no_git_route", "dirty", "one_sided", "restart", "protocol",
           "import", "derived_differs")
CLASSIFIED_KEYS = {"state", "reason", "route", "protocol", "recorded", "live", "differs",
                   "tag", "forced", "file"}
D2_FILE = "results/d2_seed0.txt"


class ProvenanceStateTests(unittest.TestCase):
    """results_provenance part 2: classify_eval, tag_for, section_provenance."""

    @classmethod
    def setUpClass(cls):
        cls.git = RP.Git(ROOT)
        cls.live = RP.live_side(ROOT)
        cls.rels = [r for r in SEEDED if (ROOT / r).is_file()]
        cls.last = cls.git.last_commits(cls.rels)
        cls.status = cls.git.status(cls.rels)

    def _parsed(self, rel=D2_FILE, **fields):
        """A real file's parse with fingerprint fields changed; None deletes one."""
        if not (ROOT / rel).is_file():
            self.skipTest(f"{rel} is not in this checkout")
        parsed = EV.parse_eval_file(ROOT / rel)
        for key, value in fields.items():
            if value is None:
                parsed["fingerprint"].pop(key, None)
            else:
                parsed["fingerprint"][key] = value
        return parsed

    def _live_like(self, parsed, **changes):
        """A live side whose blocks are `parsed`'s own block, under its Python:
        this tree as if it were the plant that file was made on."""
        fp = parsed["fingerprint"]
        live = {"python": fp["python"], "minor": RP.minor(fp["python"]),
                "plant_sha": fp["plant_sha"], "plant_text_sha": fp.get("plant_text_sha"),
                "restart_needed": False, "derived_sha": None, "data_sha1": None,
                "derived_loaded_differs": False,
                "blocks": {"phase-d": dict(fp), "d2": dict(fp)}, "import_errors": []}
        live.update(changes)
        return live

    def _classify(self, parsed, live=None, rel=D2_FILE, git=None, status=None):
        got = RP.classify_eval(parsed, self.live if live is None else live,
                               self.git if git is None else git, rel, self.last,
                               self.status if status is None else status, TITLE_PROTOCOLS)
        self.assertEqual(set(got), CLASSIFIED_KEYS)
        self.assertIn(got["state"], RP.STATES)
        self.assertIn(got["reason"], REASONS)
        self.assertIn(got["route"], (None, "same_python", "git"))
        self.assertEqual(set(got["recorded"]), {"plant_sha", "python", "git_head", "derived_sha"})
        self.assertEqual(set(got["file"]), {"rel", "commit", "changed"})
        return got

    def _need_commit(self, parsed):
        """Skip unless git here knows the commit the parsed file records."""
        if not self.git.available or self.git.resolve(parsed["fingerprint"].get("git_head")) is None:
            self.skipTest("the commit this file records is not in this clone")

    def _need_tags(self):
        if not self.git.available or any(self.git.resolve(t) is None for t in RP.TAGS):
            self.skipTest("the tags sep17-before-merge and ghassan-before-merge are not in this clone")

    def test_jads_files_are_made_on_another_plant(self):
        self._need_tags()
        if not self.rels:
            self.skipTest("no results/<prefix>_seed<N>.txt in this checkout")
        for prefix in REAL:
            for seed in REAL_SEEDS:
                rel = f"results/{prefix}_seed{seed}.txt"
                if not (ROOT / rel).is_file():
                    continue
                parsed = EV.parse_eval_file(ROOT / rel)
                got = self._classify(parsed, rel=rel)
                same_python = RP.minor(parsed["fingerprint"].get("python")) == self.live["minor"]
                with self.subTest(rel=rel):
                    self.assertEqual((got["state"], got["reason"]), ("another", None))
                    self.assertEqual(got["route"], "same_python" if same_python else "git")
                    self.assertEqual(got["tag"], "sep17-before-merge")
                    self.assertIn("plant_sha", got["differs"])
                    self.assertEqual(got["protocol"], REAL[prefix][1] or REAL[prefix][2])
                    self.assertEqual(got["recorded"]["plant_sha"], parsed["fingerprint"]["plant_sha"])
                    self.assertEqual(got["live"], {"plant_sha": self.live["plant_sha"],
                                                   "python": self.live["python"]})
                    self.assertEqual(got["file"], {"rel": rel, "commit": self.last.get(rel),
                                                   "changed": rel in self.status})
                    self.assertEqual(got["forced"], [])

    def test_title_protocols_are_evaluates(self):
        try:
            import evaluate
        except (Exception, SystemExit) as exc:
            self.skipTest(f"evaluate cannot be imported here ({type(exc).__name__})")
        self.assertEqual({header: name for name, (_episodes, header, _prefix)
                          in evaluate.PROTOCOLS.items()}, TITLE_PROTOCOLS)

    def test_forced_comes_before_everything(self):
        parsed = self._parsed(plant_sha=None)
        parsed["forced"] = ["!! runs_x/sighted_seed0: PLANT MISMATCH",
                            "     plant_sha                model 'aaaa'  live 'bbbb'"]
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]), ("forced", None, None))
        self.assertEqual(got["forced"], parsed["forced"])

    def test_not_recorded(self):
        got = self._classify(self._parsed(plant_sha=None))
        self.assertEqual((got["state"], got["reason"], got["route"]), ("not_recorded", None, None))
        self.assertIsNone(got["recorded"]["plant_sha"])

    def test_the_protocol_and_its_live_block(self):
        parsed = self._parsed("results/phase_d_seed0.txt", scenario=None)
        self.assertEqual(self._classify(parsed, rel="results/phase_d_seed0.txt")["protocol"],
                         "phase-d", "taken from the title through title_protocols")
        parsed = self._parsed(scenario=None)
        parsed["title"] = "SOME NEW EVALUATION"
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "protocol", None))
        broken = dict(self.live, blocks={k: v for k, v in self.live["blocks"].items() if k != "d2"},
                      import_errors=[{"module": "fingerprint.plant_fingerprint(d2)",
                                      "type": "AssertionError"}])
        got = self._classify(self._parsed(), broken)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "import", "d2"))
        parsed = self._parsed()
        parsed["protocol"] = "d9"
        got = self._classify(parsed, broken)
        self.assertEqual((got["state"], got["reason"], got["protocol"]),
                         ("cannot_compare", "protocol", "d9"))

    def test_another_python_with_no_route_through_git(self):
        got = self._classify(self._parsed(python="3.13.2", git_head="0" * 40))
        self.assertEqual((got["state"], got["reason"], got["route"]), ("cannot_compare", "python", None))
        got = self._classify(self._parsed(python="3.13.2", git_head=None))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "python"))
        nogit = RP.Git(ROOT, exe="git-does-not-exist")
        got = RP.classify_eval(self._parsed(python="3.13.2"), self.live, nogit, D2_FILE,
                               {}, {}, TITLE_PROTOCOLS)
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "python"))
        self.assertEqual(got["file"], {"rel": D2_FILE, "commit": None, "changed": False})

    def test_the_same_python_needs_no_git(self):
        parsed = self._parsed()
        live = self._live_like(parsed)
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        nogit = RP.Git(ROOT, exe="git-does-not-exist")
        got = RP.classify_eval(parsed, live, nogit, D2_FILE, {}, {}, TITLE_PROTOCOLS)
        self.assertEqual((got["state"], got["route"], got["differs"], got["tag"]),
                         ("another", "same_python", ["plant_sha"], None))

    def test_another_python_through_git(self):
        self._need_tags()
        parsed = self._parsed(python="3.13.2", plant_sha="0123456789abcdef")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"], got["tag"]),
                         ("another", None, "git", "sep17-before-merge"))
        self.assertIn("plant_sha", got["differs"])
        self.assertEqual(got["recorded"]["plant_sha"], "0123456789abcdef")

    def test_the_git_route_recomputes_plant_and_road(self):
        if "d2" not in self.live["blocks"] or not self.git.available:
            self.skipTest("no live d2 block, or no git, here")
        if not _clean(*FP.PLANT_FILES, "random_road.py"):
            self.skipTest("the plant files or random_road.py have uncommitted changes")
        fp = dict(self.live["blocks"]["d2"], python="3.13.2", plant_sha="0123456789abcdef",
                  git_head=self.git.resolve("HEAD"), git_dirty_plant_files="")
        fp["scenario"] = re.sub(r"road_sha=[0-9a-f]+", "road_sha=fedcba9876543210", fp["scenario"])
        parsed = {"title": "PHASE D2 EVALUATION (randomised climb)", "protocol": None,
                  "fingerprint": fp, "forced": []}
        live = dict(self.live, restart_needed=False, derived_sha=None)
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"], got["route"], got["differs"]),
                         ("same_code", None, "git", []))

    def test_the_bytes_at_the_commit_must_be_the_bytes_hashed(self):
        parsed = self._parsed(python="3.13.2", plant_text_sha="0123456789abcdef")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]),
                         ("cannot_compare", "no_git_route", None))

    def test_dirty_plant_files_have_no_git_route(self):
        parsed = self._parsed(python="3.13.2", git_dirty_plant_files="engine_env.py")
        self._need_commit(parsed)
        got = self._classify(parsed)
        self.assertEqual((got["state"], got["reason"], got["route"]), ("cannot_compare", "dirty", None))

    def test_same_plant_code_derived_not_recorded(self):
        parsed = self._parsed()
        got = self._classify(parsed, self._live_like(parsed))
        self.assertEqual((got["state"], got["reason"], got["route"], got["differs"], got["tag"]),
                         ("same_code", None, "same_python", [], None))

    def test_same_plant(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789"))
        self.assertEqual((got["state"], got["reason"]), ("same", None))
        self.assertEqual(got["recorded"]["derived_sha"], "abcdef0123456789")

    def test_only_the_derived_constants_differ(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="0123456789abcdef"))
        self.assertEqual((got["state"], got["reason"], got["differs"]),
                         ("another", "derived_differs", []))
        self.assertEqual(got["tag"], RP.tag_for(self.git, parsed["fingerprint"]["plant_sha"]))

    def test_a_fatal_difference_and_the_derived_constants(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        live = self._live_like(parsed, derived_sha="0123456789abcdef")
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"], got["differs"]), ("another", None, ["plant_sha"]))

    def test_a_field_on_one_side_only(self):
        parsed = self._parsed()
        live = self._live_like(parsed)
        del live["blocks"]["d2"]["dtheta_deg"]
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))
        parsed = self._parsed(episodes_sha=None)
        got = self._classify(parsed, self._live_like(self._parsed()))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))
        live = self._live_like(self._parsed())
        live["blocks"]["d2"]["plant_sha"] = "0000000000000000"
        got = self._classify(parsed, live)
        self.assertEqual((got["state"], got["differs"]), ("another", ["plant_sha"]),
                         "a shared field that differs comes before a field on one side only")
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha=None))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "one_sided"))

    def test_a_restart_is_needed(self):
        parsed = self._parsed(derived_sha="abcdef0123456789")
        got = self._classify(parsed, self._live_like(parsed, derived_sha="abcdef0123456789",
                                                     restart_needed=True))
        self.assertEqual((got["state"], got["reason"]), ("cannot_compare", "restart"))

    def test_a_changed_file_says_so(self):
        got = self._classify(self._parsed(), status={D2_FILE: "M"})
        self.assertTrue(got["file"]["changed"])
        self.assertEqual(got["file"]["commit"], self.last.get(D2_FILE))

    def test_tag_for(self):
        self._need_tags()
        sep17 = RP.plant_at(self.git, "sep17-before-merge")["plant_sha"]
        ghassan = RP.plant_at(self.git, "ghassan-before-merge")["plant_sha"]
        self.assertEqual(RP.tag_for(self.git, sep17), "sep17-before-merge")
        self.assertEqual(RP.tag_for(self.git, ghassan),
                         "sep17-before-merge" if ghassan == sep17 else "ghassan-before-merge")
        self.assertIsNone(RP.tag_for(self.git, "0" * 16))
        self.assertIsNone(RP.tag_for(self.git, None))
        self.assertIsNone(RP.tag_for(RP.Git(ROOT, exe="git-does-not-exist"), sep17))

    def test_section_provenance_of_phase_d(self):
        self._need_tags()
        per = {}
        for seed in REAL_SEEDS:
            rel = f"results/phase_d_seed{seed}.txt"
            if (ROOT / rel).is_file():
                per[seed] = self._classify(EV.parse_eval_file(ROOT / rel), rel=rel)
        if not per:
            self.skipTest("no Phase D result file in this checkout")
        got = RP.section_provenance(per)
        self.assertEqual((got["state"], got["reason"], got["tag"]),
                         ("another", None, "sep17-before-merge"))
        heads = sorted({p["recorded"]["git_head"][:7] for p in per.values()})
        self.assertEqual(got["commits"], heads)
        self.assertEqual(len(heads), 2, "Phase D's files record two commits")
        self.assertEqual(list(got["files"]), [str(s) for s in sorted(per)])
        self.assertIs(got["files"][str(min(per))], per[min(per)])

    def test_section_provenance_mixed_and_common(self):
        a = {"state": "another", "reason": None, "tag": "sep17-before-merge",
             "recorded": {"git_head": "a" * 40}}
        b = {"state": "same", "reason": None, "tag": None, "recorded": {"git_head": "b" * 40}}
        got = RP.section_provenance({1: b, 0: a})
        self.assertEqual((got["state"], got["reason"], got["tag"]), ("mixed", None, None))
        self.assertEqual(got["commits"], ["aaaaaaa", "bbbbbbb"])
        self.assertEqual(list(got["files"]), ["0", "1"])
        c = {"state": "cannot_compare", "reason": "python", "tag": None,
             "recorded": {"git_head": None}}
        got = RP.section_provenance({0: c, 3: dict(c)})
        self.assertEqual((got["state"], got["reason"], got["tag"], got["commits"]),
                         ("cannot_compare", "python", None, []))
        with self.assertRaises(ValueError):
            RP.section_provenance({})


if __name__ == "__main__":
    unittest.main()
```

What these pin: the 24 real files (Jad's Phase D, D2 and C4) are `another`, reason `None`, route
`same_python` under the Python they were recorded with (`git` under another), tag `sep17-before-merge`,
`plant_sha` among the differences, the protocol from the header or else the block (`phase-d` for Phase D,
`d2` for D2 and C4); the title-to-protocol table equal to the one built from `evaluate.PROTOCOLS`; every state and every
reason of the contract on a real file's parse with fields edited; the order of precedence (forced before not
recorded; a differing shared field before a one-sided field; one-sided before restart); the git route both
ways (another plant through `sep17-before-merge`, and the same plant code once the recorded plant hash and
`road_sha` are recomputed from HEAD); a missing git, which only loses the git facts; the file's own commit
and its `changed` flag; `tag_for`; `section_provenance` on Phase D's eight files (one state, two commits)
and on synthetic mixed and common sets.

- [ ] **Step 2: Run the tests and see them fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.ProvenanceStateTests -v
```

Expected (observed in drafting): `Ran 21 tests` and `FAILED (errors=20)`: eighteen
`AttributeError: module 'app.results_provenance' has no attribute 'classify_eval'`, one for `tag_for` and
one for `section_provenance`; `test_title_protocols_are_evaluates` already passes, since it pins the
table Task 4 builds, not this module.

- [ ] **Step 3: Add the plant states to the module docstring**

Edit `app/results_provenance.py`. `old_string` (the end of the module docstring):
```python
road_sha_at), cached per commit, since a commit never changes.
"""
```
`new_string`:
```python
road_sha_at), cached per commit, since a commit never changes.

THE PLANT STATES. classify_eval decides one evaluation file's plant state in
the design's order (forced, not recorded, another plant, cannot compare, same
plant code, same plant), and section_provenance sums one experiment's files:
one state when they agree, "mixed" with every file's own state when they do
not. The words the page shows for each state live in results-strings.mjs.
"""
```

- [ ] **Step 4: Append the plant-state functions to `app/results_provenance.py`**

Append this to the END of the file, after `live_side` (it starts with two blank lines):

```python


# ---------------------------------------------------------------------------
# The plant state of an evaluation file, in the design's order of precedence
# ---------------------------------------------------------------------------
_ROAD_TOKEN = re.compile(r"\broad_sha=[0-9a-f]+")
_RECORDED = ("plant_sha", "python", "git_head", "derived_sha")


def _given(fp, key):
    """A block field's text, or None when it is absent, empty or "None"."""
    value = fp.get(key)
    return None if value in (None, "", "None") else value


def tag_for(git: Git, plant_sha: str) -> str | None:
    """The first of TAGS whose plant, hashed under this Python, is `plant_sha`."""
    if not plant_sha:
        return None
    for tag in TAGS:
        plant = plant_at(git, tag)
        if plant is not None and plant["plant_sha"] == plant_sha:
            return tag
    return None


def _git_route(fp, git):
    """(the recorded block to compare, None), or (None, why there is no route).

    The route needs the recorded commit here, its plant files byte-equal to
    the recorded plant_text_sha, and no plant file dirty when the run was
    made. The copy then carries the commit's plant hashed under this Python,
    and the road_sha of a d2 scenario recomputed from the commit's
    random_road.py the same way."""
    head = _given(fp, "git_head")
    commit = git.resolve(head) if head else None
    plant = plant_at(git, commit) if commit else None
    if plant is None:
        return None, "python"
    dirty = fp.get("git_dirty_plant_files")
    if dirty not in ("", None, "None"):
        return None, "dirty"
    if dirty != "" or plant["plant_text_sha"] != fp.get("plant_text_sha"):
        return None, "no_git_route"
    rec = dict(fp, plant_sha=plant["plant_sha"])
    scenario = rec.get("scenario")
    if scenario is not None and _ROAD_TOKEN.search(scenario):
        road = road_sha_at(git, commit)
        if road is None:
            return None, "no_git_route"
        rec["scenario"] = _ROAD_TOKEN.sub(lambda m: "road_sha=" + road, scenario)
    return rec, None


def classify_eval(parsed: dict, live: dict, git: Git, rel: str,
                  last: dict, status: dict, title_protocols: dict[str, str]) -> dict:
    """The plant state of one parsed evaluation file against `live`.

    `parsed` is results_eval.parse_eval_file's dict, `live` is live_side's,
    `last` and `status` are Git.last_commits and Git.status over the files,
    and `title_protocols` maps a header title to its protocol (from
    evaluate.PROTOCOLS). The states, first match wins: forced, not_recorded,
    then a valid comparison or cannot_compare, then another, then
    cannot_compare for a one-sided field or a needed restart, then same or
    same_code. Each FATAL field is compared as the text format_block wrote."""
    fp = dict(parsed.get("fingerprint") or {})
    protocol = (parsed.get("protocol") or EV.protocol_from_fingerprint(fp)
                or title_protocols.get(parsed.get("title")))
    commit = last.get(rel)
    out = {"state": None, "reason": None, "route": None, "protocol": protocol,
           "recorded": {k: _given(fp, k) for k in _RECORDED},
           "live": {"plant_sha": live["plant_sha"], "python": live["python"]},
           "differs": [], "tag": None,
           "forced": list(parsed.get("forced") or []),
           "file": {"rel": rel, "commit": dict(commit) if commit else None,
                    "changed": rel in status}}

    def done(state, reason=None):
        out["state"], out["reason"] = state, reason
        return out

    if out["forced"]:
        return done("forced")
    if out["recorded"]["plant_sha"] is None:
        return done("not_recorded")
    block = live["blocks"].get(protocol) if protocol else None
    if block is None:
        module = f"fingerprint.plant_fingerprint({protocol})"
        listed = any(e.get("module") == module for e in live.get("import_errors", ()))
        return done("cannot_compare", "import" if protocol and listed else "protocol")
    if live["minor"] is not None and minor(out["recorded"]["python"]) == live["minor"]:
        rec, out["route"] = fp, "same_python"
    else:
        rec, why = _git_route(fp, git)
        if rec is None:
            return done("cannot_compare", why)
        out["route"] = "git"
    out["differs"] = [f for f in FP.FATAL if f in rec and f in block and rec[f] != block[f]]
    rec_d, live_d = out["recorded"]["derived_sha"], live.get("derived_sha")
    derived_differs = rec_d is not None and live_d is not None and rec_d != live_d
    if out["differs"] or derived_differs:
        out["tag"] = tag_for(git, rec.get("plant_sha"))
        return done("another", None if out["differs"] else "derived_differs")
    one_sided = any((f in rec) != (f in block) for f in FP.FATAL)
    if one_sided or (rec_d is not None and live_d is None):
        return done("cannot_compare", "one_sided")
    if live.get("restart_needed"):
        return done("cannot_compare", "restart")
    return done("same" if rec_d is not None else "same_code")


def section_provenance(per_file: dict[int, dict]) -> dict:
    """One experiment's plant label from its files' classify_eval results.

    The common state, or "mixed" when the files disagree (the page then shows
    them seed by seed); the common reason and tag, or None; the distinct
    recorded commits, short; and every file's own result by seed."""
    if not per_file:
        raise ValueError("section_provenance needs at least one file")
    seeds = sorted(per_file)
    items = [per_file[s] for s in seeds]

    def common(key):
        values = {item.get(key) for item in items}
        return values.pop() if len(values) == 1 else None

    states = {item["state"] for item in items}
    heads = {item["recorded"]["git_head"][:7] for item in items
             if item["recorded"].get("git_head")}
    return {"state": states.pop() if len(states) == 1 else "mixed",
            "reason": common("reason"),
            "tag": common("tag"),
            "commits": sorted(heads),
            "files": {str(s): per_file[s] for s in seeds}}
```

- [ ] **Step 5: Run the tests and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.ProvenanceStateTests -v
$PY -m app.test_results 2>&1 | tail -n 3
git status --porcelain -- app
```

Expected (observed in drafting on this machine, from a copy outside the repository built from Task 1's
planned files): twenty-one lines ending `... ok`, `Ran 21 tests in 0.677s`, `OK`; nothing skipped here. On
a clone without the two tags, or without the commits Jad's files record, the tests that need them print
`skipped '...'` with the reason. The whole file: `Ran 65 tests` (Task 1's 27, Task 2's 17, these 21) and
`OK`. `git status --porcelain -- app` lists ` M app/results_provenance.py` and ` M app/test_results.py`.

- [ ] **Step 6: The byte check, the scans and the agents suite against its baseline**

Before R1a the agents suite already fails (the merged plant refuses Jad's agents; `runs_c4/` is on this
machine); `$SP/agents_baseline.txt` is the coordinator's capture of that state. The comparison is Task 1's:
it strips the module part of each test name and prints only the entries the baseline does not have.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -c "import pathlib, sys; r={p: ([hex(ord(c)) for c in pathlib.Path(p).read_text(encoding='utf-8') if ord(c) > 127], pathlib.Path(p).read_text(encoding='utf-8').count(chr(92) + 'u')) for p in sys.argv[1:]}; print(r); sys.exit(1 if any(a or b for a, b in r.values()) else 0)" app/results_provenance.py app/test_results.py
$PY -W error::SyntaxWarning -c "import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]; print('compiled:', ', '.join(sys.argv[1:]))" app/results_provenance.py app/test_results.py
$PY -m unittest app.test_agents.NoNetworkTests app.test_agents.PrintScanTests 2>&1 | tail -3
$PY -m app.test_replay 2>&1 | tee "$SP/r1a_replay_task03.txt" | grep -E "READ-ONLY|checks pass"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task03.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task03.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task03.txt" > "$SP/r1a_agents_fail_task03.txt"
echo "new failing entries:"; comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task03.txt"; echo "(end)"
```

Expected (the times vary):
```
{'app/results_provenance.py': ([], 0), 'app/test_results.py': ([], 0)}
compiled: app/results_provenance.py, app/test_results.py
Ran 5 tests in 0.377s

OK
  PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns
49 of 49 checks pass
Ran 126 tests in 47.1s
FAILED (failures=16, errors=3, skipped=1)
new failing entries:
(end)
```
Observed in drafting: the first two lines on the drafted files; the scan, replay and agents lines on this
tree before the change (drafting never writes into the repository), while the scans those suites run over
every `app/*.py` passed over the drafted module and test file. The baseline has read `errors=3` on one run
and `errors=4` on another: if a line appears between `new failing entries:` and `(end)`, run the block once
more; a line in only one of the two runs is that intermittent error and goes into the task report, a line in
both is a regression of this task and is fixed before the commit. In a worktree without `runs_c4/` the
agents suite skips its C4 tests and fails fewer; the `comm` line is still the check.

- [ ] **Step 7: Commit**

By explicit path only, as in Task 2.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
cat > "$SP/r1a_msg_task03.txt" <<'EOF'
Results tab R1a (task 3): results_provenance part 2, the plant state of each file

classify_eval decides an evaluation file's plant state in the design's order:
forced, not recorded, then a valid comparison (the same Python minor, or the
git route that rehashes the recorded commit's plant and road under this
Python), another plant (with its tag), cannot compare (with its reason), same
plant code, same plant. section_provenance sums an experiment's files.
Tests: ProvenanceStateTests in app/test_results.py.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
git add app/results_provenance.py app/test_results.py
git commit -F "$SP/r1a_msg_task03.txt" -- app/results_provenance.py app/test_results.py
git log -1 --format=%B | sed '/^$/d' | tail -n 1
git status --short -- app/results_provenance.py app/test_results.py
```

Expected (not run in this repository in drafting): possibly the `LF will be replaced by CRLF` warnings;
`[JMF-2340550-results-tab <sha>] Results tab R1a (task 3): results_provenance part 2, the plant state of
each file`, `2 files changed`; the message's last line,
`Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`; and nothing from `git status
--short` for the two paths.

### Task 4: `app/results_data.py`: discovery, the evaluation sections and `build()`

**Files:**
- Create: `app/results_data.py` (discovery of `results/<prefix>_seed<N>.txt`, one section per experiment with its pairs, unpaired seeds, MEI, notes, quoted verdict, plant label and parse check, and `build()`; it imports `run_phase_d`, `analyse_phase_d`, `analyse_phase_d2`, `evaluate` and `app.agent_catalog` inside `build()` only, so importing it loads no agent code)
- Modify: `app/test_results.py`: insert the block of Step 1 directly above the file's final two lines, `if __name__ == "__main__":` and `    unittest.main()`, below Task 3's block; those two lines stay last
- Test: `app/test_results.py`, class `DataTests` (27 tests)

**Interfaces:**
- Consumes:
  - Task 1, `app/results_eval.py`: `parse_name(filename) -> (prefix, seed) | None`; `parse_eval_file(path) -> dict` (this task reads `title`, `protocol`, `n_episodes`, `frozen`, `scenario_line`, `fingerprint`, `dt_notes`, `models` (each `{"dir", "text", "steps", "requested", "zip_sha"}`), `policies` (role to `{"label", "dir", "median", "iqr", "worst", "fuel", "peak"}`), `thermal` (role to `{"median", "cut"}`, or `None`) and `path`); `NotEvaluationFile` and its `.reason`; `protocol_from_fingerprint(fp)`; `ROLE_PREFIXES`; `ROLES`. An empty file raises `NotEvaluationFile("header")`; `OSError` and `UnicodeDecodeError` propagate (this task lists them as `"unreadable"` with their type).
  - Tasks 2 and 3, `app/results_provenance.py`: `live_side(root) -> dict` (this task reads `python`, `plant_sha`, `restart_needed`, `derived_loaded_differs` and `import_errors`, and hands the whole dict to `classify_eval`); `Git(root)` with `.available`, `.head_short()`, `.last_commits(rels)` and `.status(rels)`; `classify_eval(parsed, live, git, rel, last, status, title_protocols)`, where `last` and `status` are the WHOLE dicts the two `Git` calls return over every evaluation file of the build, and `rel` is `"results/<name>"`; `section_provenance(per_file)` (never called with an empty dict).
  - The repository, each module imported inside `build()` once per build through `importlib.import_module`: `run_phase_d.CLOSED_PREFIX`; `analyse_phase_d.parse(path) -> dict[str, float]` keyed by `"agent (blind)"`, `"agent"`, `"baseline ECU"`, `"reactive"`, `"current-grade"`; `analyse_phase_d2.MEI`; `evaluate.PROTOCOLS` (`{name: (episodes, header, prefix)}`, read as `{header: name}` for the title fallback); `app.agent_catalog.verdict(prefix, root=...) -> {"state", "lines", "missing", "short", "cells"}`.
- Produces (Task 5 imports `build` inside its handler; Task 9's page reads the answer):

```python
ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
EVAL_COMMAND = "python run_phase_d.py (evaluate.py --out results/<prefix>_seed<N>.txt)"
KNOWN = {...}            # contract section 2.3, exactly
UNKNOWN_ORDER = 100      # the "order" of a prefix KNOWN does not name
def jsonable(x): ...     # dict, list, tuple, numpy -> plain; NaN and infinity -> None; TypeError otherwise
def discover_evaluations(results_root) -> tuple[dict[str, dict[int, Path]], list[dict]]: ...
def evaluation_section(prefix: str, files: dict[int, Path], ctx: dict) -> dict | None: ...
def build(results_root: Path = RESULTS, git_root: Path = ROOT, *, live: dict | None = None,
          verdict=None) -> dict: ...  # {"built", "import_failures", "sections", "not_read"}
```

  The answer is contract section 2.3 exactly. Decisions inside it that later tasks can rely on:
  - `verdict` is called as `verdict(prefix, root=<the parent of results_root>)`; a state `"none"` passes `"short": None`, never `agent_catalog.NONE_TEXT`;
  - a KNOWN prefix with no file at all: `"state": "unavailable"`, `"error": {"kind": "missing", "file": "results/<prefix>_seed<N>.txt", "command": EVAL_COMMAND with "<prefix>" replaced by the prefix, "type": None, "module": None}`;
  - a KNOWN prefix whose files all fail to parse: `"error": {"kind": "read", "file": <the lowest seed's file>, "command": None, "type": "NotEvaluationFile" or the exception's type name, "module": None}`. A prefix KNOWN does not name gets NO section in that case (`evaluation_section` returns `None`); its files are in `not_read`;
  - every evaluation section needs `run_phase_d` (its name) and `analyse_phase_d2` (its MEI): `"error": {"kind": "module", "module": <the first of the two that failed>}`. Without `analyse_phase_d` the check reads `not_compared`; without `app.agent_catalog` every verdict is `{"state": "unavailable"}`; without `evaluate` the title fallback of the protocol is `{}`;
  - any other exception inside a section (Exception or SystemExit, nothing broader): `"error": {"kind": "build", "type": <type name>}`, the other fields `None`;
  - `import_failures`: the imports this build could not make, then `live["import_errors"]`, each `{"module", "type"}`;
  - the section's `protocol`, `episodes`, `frozen` and `scenario` come from its lowest readable seed (`protocol`: the header group, else `protocol_from_fingerprint`, else the title through `evaluate.PROTOCOLS`);
  - a seed's `baseline`, `reactive` and `current_grade` are `None` when its file has no such row; its `budget` is `{"steps", "requested"}` when every model line of that file records the same pair, else `None`;
  - `thermal_recorded`, over the paired seeds: `"all"`, `"some"` or `"none"`, by whether a seed's thermal block holds both arms;
  - `checks[0]["detail"]` is `None` on a pass, and on a fail `"results/<file> (<analyse_phase_d names that differ>)"` per file, joined by `"; "`.

- [ ] **Step 1: Write the failing tests**

Insert this block into `app/test_results.py` directly above the final two lines (`if __name__ == "__main__":` and `    unittest.main()`), below Task 3's block, with the Edit tool (old string: those two lines; new string: this block, two blank lines, then the same two lines). Not through a shell heredoc: the Bash tool collapses `\\` into one backslash, and this block holds `\\` twice (the run directory `runs_x\\{arm}`), plus `\b`, `\n` and `\x..` escapes that must stay as written. It holds no backslash-u escape and no character outside ASCII, as Task 1's byte check requires of this file: the Arabic words of the wording rules are built from their code points by `_ar`. It imports what it uses itself, and its helpers are named so that none redefines Task 1's (`_eval_text` stays Task 1's).

```python
# ---- Task 4: app/results_data.py (discovery, sections, notes, verdicts, build) ----
import json  # noqa: E402
import os  # noqa: E402
import platform  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import unittest  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

import numpy as np  # noqa: E402

import analyse_phase_d2  # noqa: E402
import evaluate  # noqa: E402
import fingerprint as FP  # noqa: E402
import run_phase_d  # noqa: E402
from app import results_data as RD  # noqa: E402
from app import results_provenance as RP  # noqa: E402

HAND_ROWS = (("baseline ECU", 0), ("reactive", 1), ("current-grade", 2))
NOTE = "note {arm}_seed{seed}: trained at dt 0.2, scored at dt 1 (known, unresolved -- AUDIT2.md H2-2)"
MODEL = ("model runs_x\\{arm}_seed{seed}: trained 1000 steps of 1000 requested, from step 0, "
         "buffer 1000, zip sha 0123456789abcdef")
NEVER_READ = ("phase_d_130kmh.txt", "c4_convergence.txt")


def _ar(*points):
    """Arabic text from its code points, so that this file stays ASCII (Task 1's byte check)."""
    return "".join(map(chr, points))


# The wording rules (spec 5.2 and 5.5) for every text the tab shows from the
# server: current-grade is exempt, and quoted anchor lines are verbatim and
# exempt. Arabic is matched with its vowel marks dropped, so the order of a
# shadda and its vowel cannot hide a word.
AR_NEW = _ar(0x062D, 0x062F, 0x064A, 0x062B)                  # hadith: new, recent
AR_OLD = _ar(0x0642, 0x062F, 0x064A, 0x0645)                  # qadim: old
AR_UPDATED = _ar(0x0645, 0x062D, 0x062F, 0x062B)              # muhaddath: updated
AR_PREVIEW = _ar(0x0627, 0x0644, 0x0627, 0x0633, 0x062A, 0x0628, 0x0627, 0x0642)  # al-istibaq
AR_HELPS = _ar(0x064A, 0x0633, 0x0627, 0x0639, 0x062F)        # yusaid: helps
AR_NOT = _ar(0x0644, 0x0627)                                  # la: not
AR_AVAILS = _ar(0x064A, 0x0641, 0x064A, 0x062F)               # yufid: is of use
AR_INSPECTION = _ar(0x0627, 0x0644, 0x0645, 0x0639, 0x0627, 0x064A, 0x0646, 0x0629)  # al-muayana
AR_AVAILS_F = _ar(0x062A, 0x0641, 0x064A, 0x062F)             # tufid: is of use (feminine)
_AR_BLOCK = f"[{chr(0x0600)}-{chr(0x06FF)}]"
_AR_MARKS = re.compile(f"[{chr(0x064B)}-{chr(0x0652)}]")
_AR_PREFIX = "|".join((_ar(0x0627, 0x0644), _ar(0x0648), _ar(0x0628)))       # al-, wa-, bi-
_AR_SUFFIX = "|".join((_ar(0x0629), _ar(0x0648, 0x0646), _ar(0x064A, 0x0646), _ar(0x0627, 0x062A)))
BANNED = (
    re.compile(r"\b(?:current(?!-grade)|stale|outdated|fresh|up[ -]to[ -]date)\b", re.I),
    re.compile(r"preview (?:helps|does not help|doesn't help)|adds nothing measurable"
               r"|not from seeing ahead|replicat|pooled", re.I),
    re.compile(f"(?<!{_AR_BLOCK})(?:{_AR_PREFIX})?(?:{AR_NEW}|{AR_OLD}|{AR_UPDATED})"
               f"(?:{_AR_SUFFIX})?(?!{_AR_BLOCK})"),
    re.compile("|".join((f"{AR_PREVIEW} {AR_HELPS}", f"{AR_HELPS} {AR_PREVIEW}",
                         f"{AR_PREVIEW} {AR_NOT} {AR_AVAILS}", f"{AR_NOT} {AR_AVAILS} {AR_PREVIEW}",
                         f"{AR_PREVIEW} {AR_NOT} {AR_HELPS}",
                         f"{AR_INSPECTION} {AR_NOT} {AR_AVAILS_F}"))),
)


def _banned(text):
    """True when `text` breaks a wording rule (Arabic vowel marks dropped first)."""
    bare = _AR_MARKS.sub("", text)
    return any(rx.search(bare) for rx in BANNED)


def _texts(x, path=()):
    """(where, text) for every string in an answer, quoted verdict lines left out."""
    if isinstance(x, dict):
        for key, value in x.items():
            if not (key == "lines" and "verdict" in path):
                yield from _texts(value, path + (str(key),))
    elif isinstance(x, list):
        for value in x:
            yield from _texts(value, path)
    elif isinstance(x, str):
        yield "/".join(path), x


def _row_values(seed, k):
    """(median, IQR, worst, fuel, peak) made from the seed and the row, so that
    no damage figure is typed in this file (verify_docs.py reads it)."""
    return (1000.0 + 10 * k + seed, 10.0, 2000.0 + k, 4000.0 + k, 1100.0 + k)


def _data_text(seed, arms=("sighted", "blind"), *, thermal=False, header=None, block=True,
               table=True, models=True):
    """One results/<prefix>_seed<N>.txt in evaluate.py's own layout (its main()).

    The header, scenario, trigger and fingerprint block are copied from the
    real results/c4_seed0.txt, so the provenance code reads a real block.
    """
    real = (RD.RESULTS / "c4_seed0.txt").read_text(encoding="utf-8").splitlines()
    head = real[:real.index("-" * 62) + 1]
    if header is not None:
        head[0] = header
    if not block:
        head = head[:next(i for i, line in enumerate(head) if line.startswith("--- "))]
    lines = list(head)
    for arm in arms:
        lines.append(NOTE.format(arm=arm, seed=seed))
        if models:
            lines.append(MODEL.format(arm=arm, seed=seed))
    if table:
        rows = [(label, _row_values(seed, k)) for label, k in HAND_ROWS]
        rows += [(("agent (blind)" if arm == "blind" else "agent") + f" runs_x\\{arm}_seed{seed}",
                  _row_values(seed, 3 if arm == "sighted" else 4)) for arm in arms]
        lines += ["", f"{'policy':<28}{'damage med':>12}{'IQR':>9}{'worst':>9}"
                      f"{'fuel med':>10}{'peak C':>9}", "-" * 77]
        lines += [f"{label:<28}{v[0]:>12.1f}{v[1]:>9.1f}{v[2]:>9.1f}{v[3]:>10.0f}{v[4]:>9.0f}"
                  for label, v in rows]
        lines.append("-" * 77)
        if thermal:
            lines += ["", "  WITHOUT THE KNOCK TERM (turbine + oil only; the knock model is untested)"]
            lines += [f"    {label:<26} thermal med {v[0] - 5:8.1f}   thermal cut {2.0 + i:5.1f} %"
                      for i, (label, v) in enumerate(rows)]
    return "\n".join(lines) + "\n"


def _found_verdict(prefix, root=None):
    """A stand-in for app.agent_catalog.verdict with every anchor found."""
    return {"state": "found", "lines": [{"key": "result", "file": "X.txt", "line": 1,
                                         "text": "RESULT"}],
            "missing": [], "short": {"ar": "a reading (ar)", "en": "a reading"},
            "cells": [{"cell": "INCONCLUSIVE", "gloss": {"ar": "a gloss (ar)", "en": "a gloss"}}]}


class DataTests(unittest.TestCase):
    """app/results_data.py on a temporary tree and on the real one (spec 4.1, 4.4, 5.6, 9)."""

    @classmethod
    def setUpClass(cls):
        # analyse_phase_d.parse leaves each file it reads to the garbage
        # collector, and unittest shows that as a ResourceWarning per file.
        cls.quiet = warnings.catch_warnings()
        cls.quiet.__enter__()
        warnings.filterwarnings("ignore", category=ResourceWarning, module="analyse_phase_d")
        # One real build first: every module build() imports is then loaded, so
        # the mock.patch.dict(sys.modules, ...) tests below remove nothing else.
        cls.real = RD.build(RD.RESULTS, RD.ROOT)
        cls.live = RP.live_side(RD.ROOT)
        cls.tmp = tempfile.TemporaryDirectory()
        base = Path(cls.tmp.name)
        res = base / "results"
        (res / "nested").mkdir(parents=True)
        files = {
            "newexp_seed0.txt": _data_text(0, thermal=True),
            "newexp_seed1.txt": _data_text(1),
            "newexp_seed2.txt": _data_text(2, arms=("sighted",)),
            "Bad-Name_seed0.txt": _data_text(0),
            "hdr_seed0.txt": _data_text(0, header="not an evaluate.py header"),
            "noblock_seed0.txt": _data_text(0, block=False),
            "d2_seed0.txt": "",
            "c4_seed0.txt": _data_text(0, table=False),
            "nested/zz_seed0.txt": _data_text(0),
        }
        for name, text in files.items():
            (res / name).write_text(text, encoding="utf-8")
        (res / "bytes_seed0.txt").write_bytes(b"\xff\xfe\x00not utf-8\n")
        for name in NEVER_READ:
            (res / name).write_text((RD.RESULTS / name).read_text(encoding="utf-8"),
                                    encoding="utf-8")
        cls.tree = RD.build(res, base, live=cls.live)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
        cls.quiet.__exit__(None, None, None)

    def section(self, built, prefix):
        return next(s for s in built["sections"] if s["prefix"] == prefix)

    # ---- the temporary tree ---------------------------------------------
    def test_discovery_lists_every_file_it_does_not_read(self):
        got = sorted((n["path"], n["reason"], n["type"]) for n in self.tree["not_read"])
        self.assertEqual(got, [
            ("results/Bad-Name_seed0.txt", "name", None),
            ("results/bytes_seed0.txt", "unreadable", "UnicodeDecodeError"),
            ("results/c4_seed0.txt", "no_table", None),
            ("results/d2_seed0.txt", "header", None),
            ("results/hdr_seed0.txt", "header", None),
            ("results/noblock_seed0.txt", "no_fingerprint", None),
        ])
        text = json.dumps(self.tree)
        for name in NEVER_READ + ("zz_seed0",):
            self.assertNotIn(name, text, f"{name} must never be a candidate")

    def test_sections_in_order_known_first(self):
        self.assertEqual([s["prefix"] for s in self.tree["sections"]],
                         ["phase_d", "d2", "c4", "newexp"])
        self.assertEqual([s["id"] for s in self.tree["sections"]],
                         ["exp-phase_d", "exp-d2", "exp-c4", "exp-newexp"])

    def test_each_failure_kind_costs_only_its_section(self):
        phase_d = self.section(self.tree, "phase_d")
        self.assertEqual(phase_d["state"], "unavailable")
        self.assertEqual(phase_d["name"], run_phase_d.CLOSED_PREFIX["phase_d"])
        self.assertEqual(phase_d["error"], {
            "kind": "missing", "file": "results/phase_d_seed<N>.txt",
            "command": RD.EVAL_COMMAND.replace("<prefix>", "phase_d"), "type": None,
            "module": None})
        for prefix in ("d2", "c4"):
            sec = self.section(self.tree, prefix)
            self.assertEqual(sec["state"], "unavailable", prefix)
            self.assertEqual(sec["error"], {
                "kind": "read", "file": f"results/{prefix}_seed0.txt", "command": None,
                "type": "NotEvaluationFile", "module": None}, prefix)
        self.assertEqual(self.section(self.tree, "newexp")["state"], "ok")

    def test_a_new_prefix_appears_by_itself(self):
        sec = self.section(self.tree, "newexp")
        self.assertIsNone(sec["name"])
        self.assertFalse(sec["known"])
        self.assertEqual(sec["order"], RD.UNKNOWN_ORDER)
        self.assertIsNone(sec["continues"])
        self.assertEqual(sec["protocol"], "d2")
        self.assertEqual([s["seed"] for s in sec["seeds"]], [0, 1])
        self.assertEqual(sec["unpaired"], [{"seed": 2, "file": "results/newexp_seed2.txt",
                                            "have": ["baseline", "reactive", "current_grade",
                                                     "sighted"]}])
        for s in sec["seeds"]:
            self.assertEqual(s["diff"], s["blind"]["median"] - s["sighted"]["median"])
            self.assertEqual(s["budget"], {"steps": 1000, "requested": 1000})
            self.assertEqual(s["file"], f"results/newexp_seed{s['seed']}.txt")
        self.assertEqual(sec["seeds"][0]["sighted"]["dir"], "runs_x/sighted_seed0")
        self.assertIsNone(sec["seeds"][0]["baseline"]["dir"])
        self.assertEqual(sec["mei"], analyse_phase_d2.MEI)
        self.assertFalse(sec["mei_after_result"])
        self.assertEqual(sec["thermal_recorded"], "some")
        self.assertEqual(set(sec["seeds"][0]["thermal"]), set(RD.E.ROLES))
        self.assertIsNone(sec["seeds"][1]["thermal"])
        self.assertEqual(sorted(sec["provenance"]["files"]), ["0", "1", "2"])
        self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis", "state": "pass",
                                          "detail": None}])
        self.assertIsNone(sec["error"])

    def test_an_unknown_prefix_gets_only_what_its_files_record(self):
        sec = self.section(self.tree, "newexp")
        self.assertEqual(sec["notes"], [
            {"key": "budget_from_file", "values": {"steps": 1000}},
            {"key": "dt_mismatch", "values": {"train_dt": 0.2, "eval_dt": 1.0}},
            {"key": "knock_model", "values": {}},
            {"key": "turbine_modelled", "values": {}},
            {"key": "no_other_notes", "values": {}},
        ])

    def test_no_verdict_shows_no_short_line(self):
        verdict = self.section(self.tree, "newexp")["verdict"]
        self.assertEqual(verdict["state"], "none")
        self.assertIsNone(verdict["short"], "the 'none' text says nothing here is a result")
        self.assertEqual((verdict["lines"], verdict["cells"], verdict["missing"]), ([], [], []))

    def test_temporary_tree_has_no_git(self):
        self.assertEqual(self.tree["built"]["git"], "unavailable")
        self.assertIsNone(self.tree["built"]["head"])
        self.assertEqual(self.tree["import_failures"], [])

    # ---- failures --------------------------------------------------------
    def test_a_reader_raising_system_exit_costs_one_section(self):
        def verdict(prefix, root=None):
            if prefix == "d2":
                raise SystemExit("a reader gave up")
            return _found_verdict(prefix)

        got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=verdict)
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "unavailable", "ok"])
        self.assertEqual(self.section(got, "d2")["error"], {
            "kind": "build", "file": None, "command": None, "type": "SystemExit",
            "module": None})

    def test_keyboard_interrupt_is_not_caught(self):
        def verdict(prefix, root=None):
            raise KeyboardInterrupt

        with self.assertRaises(KeyboardInterrupt):
            RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=verdict)

    def test_catalog_import_failure_is_one_line_and_no_verdict(self):
        with mock.patch.dict(sys.modules, {"app.agent_catalog": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live)
        self.assertEqual(got["import_failures"],
                         [{"module": "app.agent_catalog", "type": "ModuleNotFoundError"}])
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "ok", "ok"])
        for sec in got["sections"]:
            self.assertEqual(sec["verdict"], {"state": "unavailable"}, sec["prefix"])

    def test_a_section_says_which_module_it_needs(self):
        with mock.patch.dict(sys.modules, {"analyse_phase_d2": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"],
                         [{"module": "analyse_phase_d2", "type": "ModuleNotFoundError"}])
        for sec in got["sections"]:
            self.assertEqual(sec["state"], "unavailable", sec["prefix"])
            self.assertEqual(sec["error"]["kind"], "module")
            self.assertEqual(sec["error"]["module"], "analyse_phase_d2")

    def test_without_analyse_phase_d_the_check_is_not_compared(self):
        with mock.patch.dict(sys.modules, {"analyse_phase_d": None}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"],
                         [{"module": "analyse_phase_d", "type": "ModuleNotFoundError"}])
        for sec in got["sections"]:
            self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis",
                                              "state": "not_compared", "detail": None}])

    def test_live_side_import_errors_reach_the_tab(self):
        live = dict(self.live, blocks={}, import_errors=[
            {"module": "fingerprint.plant_fingerprint(phase-d)", "type": "AssertionError"},
            {"module": "fingerprint.plant_fingerprint(d2)", "type": "AssertionError"}])
        got = RD.build(RD.RESULTS, RD.ROOT, live=live, verdict=_found_verdict)
        self.assertEqual(got["import_failures"], live["import_errors"])
        for sec in got["sections"]:
            self.assertEqual(sec["provenance"]["state"], "cannot_compare", sec["prefix"])
            self.assertEqual(sec["provenance"]["reason"], "import", sec["prefix"])

    def test_nan_becomes_null(self):
        parse = RD.E.parse_eval_file

        def with_nan(path):
            out = parse(path)
            if Path(path).name == "c4_seed3.txt":
                out["policies"]["sighted"]["median"] = float("nan")
            return out

        with mock.patch.object(RD.E, "parse_eval_file", with_nan):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        seed3 = next(s for s in self.section(got, "c4")["seeds"] if s["seed"] == 3)
        self.assertIsNone(seed3["sighted"]["median"])
        self.assertIsNone(seed3["diff"])
        check = self.section(got, "c4")["checks"][0]
        self.assertEqual(check["state"], "fail")
        self.assertIn("results/c4_seed3.txt", check["detail"])
        json.dumps(got, allow_nan=False)

    def test_jsonable(self):
        got = RD.jsonable({"a": float("nan"), 1: (np.float32(2.5), np.int64(3), np.bool_(True),
                                                   float("inf"), None, "x"),
                           "arr": np.array([1.0, np.nan])})
        self.assertEqual(got, {"a": None, "1": [2.5, 3, True, None, None, "x"],
                               "arr": [1.0, None]})
        self.assertIs(RD.jsonable(True), True)
        with self.assertRaises(TypeError):
            RD.jsonable(object())

    # ---- the real tree ---------------------------------------------------
    def test_real_tree_three_sections_in_order(self):
        secs = self.real["sections"]
        self.assertEqual([s["prefix"] for s in secs], ["phase_d", "d2", "c4"])
        self.assertEqual([s["state"] for s in secs], ["ok", "ok", "ok"])
        for sec in secs:
            self.assertEqual(sec["name"], run_phase_d.CLOSED_PREFIX[sec["prefix"]])
            self.assertTrue(sec["known"])
            self.assertEqual([s["seed"] for s in sec["seeds"]], list(range(8)))
            self.assertEqual(sec["unpaired"], [])
            self.assertEqual(sec["thermal_recorded"], "none")
            self.assertEqual(sec["episodes"], len(evaluate.EPISODES))
            self.assertTrue(sec["scenario"].startswith("scenario: "))
            self.assertEqual(sec["mei"], analyse_phase_d2.MEI)
        self.assertEqual([s["protocol"] for s in secs], ["phase-d", "d2", "d2"])
        self.assertEqual([s["mei_after_result"] for s in secs], [True, False, False])
        self.assertEqual([s["continues"] for s in secs], [None, None, "d2"])
        self.assertFalse([n for n in self.real["not_read"]
                          if n["path"].split("/")[-1].startswith(("phase_d_", "d2_", "c4_"))])

    def test_real_tree_diffs_equal_the_analysis(self):
        for sec in self.real["sections"]:
            rows, incomplete = analyse_phase_d2.load(sec["prefix"])
            self.assertEqual(incomplete, [], sec["prefix"])
            self.assertEqual([(s["seed"], s["diff"]) for s in sec["seeds"]],
                             [(seed, diff) for seed, _, diff in rows], sec["prefix"])

    def test_real_tree_checks_pass(self):
        for sec in self.real["sections"]:
            self.assertEqual(sec["checks"], [{"name": "parse_equals_analysis",
                                              "state": "pass", "detail": None}], sec["prefix"])

    def test_real_tree_is_made_on_another_plant(self):
        for sec in self.real["sections"]:
            prov = sec["provenance"]
            self.assertEqual(prov["state"], "another", sec["prefix"])
            self.assertTrue(prov["commits"], sec["prefix"])
            self.assertEqual(sorted(prov["files"]), [str(k) for k in range(8)])

    def test_real_tree_notes(self):
        import analyse_c4
        keys = {s["prefix"]: [n["key"] for n in s["notes"]] for s in self.real["sections"]}
        tail = ["dt_mismatch", "no_thermal_only", "knock_model", "turbine_modelled"]
        self.assertEqual(keys["phase_d"], RD.KNOWN["phase_d"]["notes"] + tail)
        self.assertEqual(keys["d2"], RD.KNOWN["d2"]["notes"] + tail)
        self.assertEqual(keys["c4"], RD.KNOWN["c4"]["notes"] + ["budget_from_file"] + tail)
        notes = {n["key"]: n["values"] for n in self.section(self.real, "c4")["notes"]}
        self.assertEqual(notes["budget_from_file"], {"steps": analyse_c4.C4_STEPS})
        self.assertEqual(notes["dt_mismatch"], {"train_dt": 0.2, "eval_dt": 1.0})
        for s in self.section(self.real, "c4")["seeds"]:
            self.assertEqual(s["budget"], {"steps": analyse_c4.C4_STEPS,
                                           "requested": analyse_c4.C4_STEPS})
        for prefix in ("phase_d", "d2"):
            self.assertEqual([s["budget"] for s in self.section(self.real, prefix)["seeds"]],
                             [None] * 8, prefix)

    def test_real_tree_verdicts_are_quoted(self):
        from app import agent_catalog
        for sec in self.real["sections"]:
            want = agent_catalog.verdict(sec["prefix"])
            self.assertEqual(sec["verdict"], {k: want[k] for k in
                                              ("state", "lines", "cells", "missing", "short")})
            self.assertEqual(sec["verdict"]["state"], "found", sec["prefix"])

    def test_real_tree_serialises_strictly(self):
        json.dumps(self.real, allow_nan=False)
        built = self.real["built"]
        self.assertEqual(set(self.real), {"built", "import_failures", "sections", "not_read"})
        self.assertEqual(self.real["import_failures"], [])
        self.assertEqual(built["python"], platform.python_version())
        self.assertEqual(built["plant_sha"], FP._sha_files(FP.PLANT_FILES))
        self.assertEqual(built["git"], "ok")
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=RD.ROOT,
                              capture_output=True, text=True, timeout=60,
                              env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout.strip()
        self.assertEqual(built["head"], head)
        self.assertIsInstance(built["elapsed_ms"], int)
        print(f"\n    build() on the real tree: {built['elapsed_ms']} ms", file=sys.stderr)

    def test_build_leaves_no_trace(self):
        # --git-path, because in a worktree .git is a file and the index lives elsewhere
        where = subprocess.run(["git", "rev-parse", "--git-path", "index"], cwd=RD.ROOT,
                               capture_output=True, text=True, timeout=60,
                               env=dict(os.environ, GIT_OPTIONAL_LOCKS="0")).stdout.strip()
        index = Path(where) if Path(where).is_absolute() else RD.ROOT / where
        self.assertTrue(index.is_file(), index)
        env = {k: os.environ.get(k) for k in ("DERIVING_PARAMS", "OMP_NUM_THREADS")}
        before = (index.stat().st_mtime_ns, index.stat().st_size)
        RD.build(RD.RESULTS, RD.ROOT)
        self.assertEqual((index.stat().st_mtime_ns, index.stat().st_size), before,
                         ".git/index moved during a build")
        self.assertEqual({k: os.environ.get(k) for k in env}, env)

    def test_without_git_only_the_git_facts_go(self):
        with mock.patch.dict(os.environ, {"PATH": ""}):
            got = RD.build(RD.RESULTS, RD.ROOT, live=self.live, verdict=_found_verdict)
        self.assertEqual(got["built"]["git"], "unavailable")
        self.assertIsNone(got["built"]["head"])
        self.assertEqual([s["state"] for s in got["sections"]], ["ok", "ok", "ok"])
        for sec, real in zip(got["sections"], self.real["sections"]):
            self.assertEqual(sec["seeds"], real["seeds"], sec["prefix"])
            self.assertEqual(sec["provenance"]["state"], "another", sec["prefix"])
            self.assertIsNone(sec["provenance"]["tag"], sec["prefix"])
            for item in sec["provenance"]["files"].values():
                self.assertIsNone(item["file"]["commit"], sec["prefix"])

    def test_wording_of_the_answer_and_of_the_quoted_verdicts(self):
        bad = ("an up to date figure", "a stale file", "the current plant", "pooled seeds",
               "preview does not help",
               _ar(0x0646, 0x062A, 0x064A, 0x062C, 0x0629) + " " + AR_OLD + _ar(0x0629),  # an old result
               _ar(0x0645, 0x062D, 0x062F, 0x064E, 0x0651, 0x062B),                      # updated, marked
               f"{AR_PREVIEW} {AR_NOT} {AR_AVAILS}")
        fine = ("current-grade", "Current-grade median",
                _ar(0x062A) + AR_NEW + " " + _ar(0x0627, 0x0644, 0x0645, 0x0644, 0x0641))  # updating the file
        self.assertEqual([text for text in bad if not _banned(text)], [])
        self.assertEqual([text for text in fine if _banned(text)], [])
        from app import agent_catalog
        texts = list(_texts(self.real))
        texts += [(f"SHORT_VERDICT[{k}][{lang}]", v[lang])
                  for k, v in agent_catalog.SHORT_VERDICT.items() for lang in ("ar", "en")]
        texts += [(f"GLOSS[{k}][{lang}]", v[lang])
                  for k, v in agent_catalog.GLOSS.items() for lang in ("ar", "en")]
        self.assertGreater(len(texts), 100)
        self.assertEqual([(where, text) for where, text in texts if _banned(text)], [])

    def test_known_matches_the_closed_prefixes(self):
        self.assertEqual(set(RD.KNOWN), set(run_phase_d.CLOSED_PREFIX))

    def test_imports_stay_light(self):
        """Importing results_data loads no agent code; a build never imports the
        four modules spec 5.2 forbids, nor sets DERIVING_PARAMS."""
        code = ("import json, os, sys\n"
                "import app.results_data as RD\n"
                "heavy = ('app.agent', 'evaluate', 'engine_env', 'random_road')\n"
                "first = sorted(m for m in sys.modules if m.startswith(heavy))\n"
                "RD.build(RD.RESULTS, RD.ROOT)\n"
                "banned = ('derive_params', 'record_agents', 'knock_margin', 'train')\n"
                "print(json.dumps([first, sorted(m for m in banned if m in sys.modules),\n"
                "                  os.environ.get('DERIVING_PARAMS')]))\n")
        run = subprocess.run([sys.executable, "-c", code], cwd=RD.ROOT, capture_output=True,
                             text=True, timeout=300,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        first, banned, deriving = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(first, [])
        self.assertEqual(banned, [])
        self.assertIsNone(deriving)
```

- [ ] **Step 2: Run the tests and see them fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.DataTests -v 2>&1 | grep -E "^(ImportError|Ran|FAILED|OK)"
```

Expected (observed in drafting, with Tasks 1 to 3 in place): the test module fails to import, so no test of the file runs until Step 3.

```
ImportError: Failed to import test module: test_results
ImportError: cannot import name 'results_data' from 'app' (unknown location). Did you mean: 'results_eval'?
Ran 1 test in 0.000s
FAILED (errors=1)
```

- [ ] **Step 3: Write `app/results_data.py`**

Create `app/results_data.py` with exactly this content, with the Write tool. Its docstrings and comments carry no figure (`verify_docs.py` reads every tracked `.py`), and it holds no backslash at all.

```python
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
are listed under not_read with the reason, never dropped silently. A seed
with one arm only is listed under its section's unpaired.

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
    "c4": {"order": 2, "notes": ["spark_bound_jad", "spike_unmeasured"], "continues": "d2"},
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
    fails NAME_RE is listed with the reason "name".
    """
    results_root = Path(results_root)
    groups, not_read = {}, []
    for path in sorted(results_root.glob("*_seed*.txt")):
        if not path.is_file():
            continue
        got = E.parse_name(path.name)
        if got is None:
            not_read.append({"path": _rel(path, results_root), "reason": "name", "type": None})
            continue
        prefix, seed = got
        groups.setdefault(prefix, {})[seed] = path
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
    verdict(prefix, root=<the parent of results_root>).
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
           "last": (git.last_commits(rels) if rels else None) or {},
           "status": (git.status(rels) if rels else None) or {},
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
    built = {"head": head, "python": live["python"], "plant_sha": live["plant_sha"],
             "restart_needed": live["restart_needed"],
             "derived_loaded_differs": live["derived_loaded_differs"],
             "git": "ok" if git.available else "unavailable",
             "elapsed_ms": int(round((time.perf_counter() - started) * 1000))}
    return jsonable({"built": built, "import_failures": failures, "sections": sections,
                     "not_read": not_read})
```

- [ ] **Step 4: Run the tests and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -m unittest app.test_results.DataTests -v 2>&1 | tee "$SP/r1a_data_task04.txt" | grep -E "^(Ran|OK|FAILED)|on the real tree"
$PY -m app.test_results 2>&1 | tee "$SP/r1a_results_task04.txt" | grep -E "^(Ran|OK|FAILED)"
```

Expected (observed in drafting with Tasks 1 to 3 as drafted; the times and the build figure vary, 282 to 385 ms in drafting, the first build of a fresh process included):

```
    build() on the real tree: 300 ms
Ran 27 tests in 1.570s
OK
Ran 92 tests in 5.539s
OK
```

92 is Task 1's 27, Task 2's 17, Task 3's 21 and this task's 27; if an earlier task's count moved, the total moves with it and must still end in `OK`. No `ResourceWarning` line appears: `DataTests` silences the one `analyse_phase_d.parse` raises for the file it leaves open, for this class only. A failing real-tree test names its section; the expected values are what the 24 files, `analyse_phase_d2.load` and `app.agent_catalog.verdict` say, and they do not change.

- [ ] **Step 5: The byte check and the app's scans**

`app/test_replay.py`'s read-only scan and `app.test_agents`' `NoNetworkTests` and `PrintScanTests` read every `app/*.py`, so the new module is inside them from now on (`NoWriteTests` reads only `NEW_MODULES`; Task 5 adds the four results modules to it).

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
for f in app/results_data.py app/test_results.py; do $PY -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" "$f"; done
$PY -W error::SyntaxWarning -c "import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]; print('compiled:', ', '.join(sys.argv[1:]))" app/results_data.py app/test_results.py
$PY -m unittest app.test_agents.NoNetworkTests app.test_agents.PrintScanTests 2>&1 | tail -3
$PY -m app.test_replay 2>&1 | tee "$SP/r1a_replay_task04.txt" | grep -E "READ-ONLY|checks pass"
```

Expected (the times vary):

```
literal invisible: []
literal invisible: []
compiled: app/results_data.py, app/test_results.py
Ran 5 tests in 0.303s

OK
  PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns
49 of 49 checks pass
```

Observed in drafting: the first three lines on the drafted files (the compile line fails with `SyntaxError: invalid escape sequence` if a `\\` lost a backslash on the way in); `Ran 5 tests` and `OK` with the drafted results modules among `app/*.py`; `49 of 49` on this tree before the file existed, while `test_replay`'s read-only patterns and the agents suite's `WRITE_PATTERNS`, network and `print(file=...)` scans, run over the drafted `app/results_data.py` and `DataTests`, found nothing. `app.test_replay` takes about 75 s.

- [ ] **Step 6: No new failing entry in `app.test_agents`**

Before R1a this suite already fails (the merged plant refuses Jad's agents; `runs_c4/` is on this machine). The coordinator's capture of that state is `$SP/agents_baseline.txt`. The comparison strips the module part of each test name (`app.test_agents.` or `__main__.`, depending on how the suite was started) and prints only the entries the baseline does not have.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task04.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task04.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task04.txt" > "$SP/r1a_agents_fail_task04.txt"
echo "new failing entries:"; comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task04.txt"; echo "(end)"
```

Expected (not run in drafting with this task's file in the tree, which drafting may not write to; this is what the suite printed on this tree before R1a, and nothing in `app.test_agents` imports `app.results_data`):

```
Ran 126 tests in 47.096s
FAILED (failures=16, errors=3, skipped=1)
new failing entries:
(end)
```

The baseline was recorded with `errors=3` on one run and `errors=4` on another, before any R1a change. If a line appears between `new failing entries:` and `(end)`, run the block once more: a line that appears in only one of the two runs is that intermittent error, and it goes into the task report; a line that appears in both is a regression this task caused, and it is fixed before the commit.

- [ ] **Step 7: Commit**

By explicit path only: another session is editing `CLAUDE.md`, `handoff.md`, `team/jad.md` and `NEXT_SESSION_*.md` in this tree. `git commit -- <paths>` commits those paths and leaves anything else staged as it is.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
{
  printf '%s\n\n' "Results tab R1a (task 4): results_data, the evaluation sections and build()"
  printf '%s\n' \
    "app/results_data.py reads every results/<prefix>_seed<N>.txt on each request." \
    "Discovery lists every file it does not read, with the reason. Each experiment" \
    "becomes one section: its pairs and unpaired seeds, the MEI, the required notes," \
    "the quoted verdict, the plant label from results_provenance and a check that the" \
    "medians equal analyse_phase_d.parse's. Each section is built inside its own try" \
    "(Exception and SystemExit), so a broken file or reader costs one section; a known" \
    "experiment with no file shows the command that makes it. Agent code is imported" \
    "inside build() only, and every failed import is one line of the answer." \
    "" \
    "DataTests run it on temporary trees (discovery, every failure kind, a new prefix," \
    "NaN, git missing) and on the real tree (three sections, the diffs of" \
    "analyse_phase_d2.load, the verdicts, another plant, the wording rules, strict JSON," \
    "the git index untouched)." \
    ""
  printf '%s\n' "python -m unittest app.test_results.DataTests:"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_data_task04.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_results:"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_results_task04.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_replay:"
  grep -E "READ-ONLY|checks pass" "$SP/r1a_replay_task04.txt" | tr -d '\r'
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task04.txt"
cat "$SP/r1a_msg_task04.txt"
git add app/results_data.py app/test_results.py
git commit -F "$SP/r1a_msg_task04.txt" -- app/results_data.py app/test_results.py
git log -1 --format=%B | sed '/^$/d' | tail -n 1
git status --short -- app/results_data.py app/test_results.py
```

Expected (not run in this repository in drafting, which may not commit here): `cat` prints the message, subject first and the `Co-Authored-By` line last, with the three test summaries between; `git` may warn `LF will be replaced by CRLF`, which is `core.autocrlf` and harmless; then a line `[JMF-2340550-results-tab <sha>] Results tab R1a (task 4): results_data, the evaluation sections and build()`, `2 files changed`, `create mode 100644 app/results_data.py`, and the last line of the message, `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. `git status --short` then prints nothing for the two paths.

### Task 5: `app/results_api.py`: the two GET routes, mounted in `app/server.py` under `--simulation`

**Files:**
- Create: `app/results_api.py` (`mount_results(app, build=None)`: `GET /results` and `GET /api/results`, the Host guard, one build at a time, no-store on every answer)
- Modify: `app/server.py:43-51` (the module docstring's route paragraph gains three lines after line 50) and `app/server.py:305-310` (`main()`'s `if a.simulation:` branch: the banner line after line 307, the mount after line 310), and `app/server.py:87-88` (`RevalidatedStatic`, a `StaticFiles` subclass whose every answer says `Cache-Control: no-cache`, defined just above `app = FastAPI(`, and the `/static` mount that uses it). The file has CRLF line ends in this checkout, and Step 5's script keeps them
- Modify: `app/test_agents.py:1658-1659` (`NEW_MODULES` gains the four results modules, so `NoWriteTests` reads them)
- Modify: `app/test_results.py`: insert the block of Step 1 directly above the final two lines, `if __name__ == "__main__":` and `    unittest.main()`, below Task 4's block
- Test: `app/test_results.py`, class `RouteTests` (12 tests); in `app.test_agents`, `RouteTests.test_routes_only_under_simulation`, `NoWriteTests`, `NoNetworkTests` and `PrintScanTests`

**Interfaces:**
- Consumes: Task 4, `app.results_data.build() -> dict` (the default `build`, imported inside the handler on the first request, never when mounting); Task 2, `app.results_provenance`, imported when mounting and only then, so that its `IMPORT_PLANT_SHA` is the plant the server started with (spec 5.2: `import app.server` already loads `plant`, `thermal`, `derived` and `engine_env`; measured in drafting, the import takes about 25 ms and adds `fingerprint` and `app.results_eval`, no agent code); Tasks 1 to 4: the four files `app/results_eval.py`, `app/results_provenance.py`, `app/results_data.py`, `app/results_api.py` exist (`NoWriteTests` reads each by name); `app/agent_api.py`'s `LOCAL_HOST` line, read by a test through `ast`, never imported.
- Produces (Task 9's page tests mount it on a fresh FastAPI app with a Host header; Task 10 repeats the banner in `app/start-simulation.ps1`):

```python
LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost)(:\d{1,5})?$")
NO_STORE = {"Cache-Control": "no-store"}
PAGE = Path(__file__).resolve().parent / "static" / "results.html"   # read on every request
def host_ok(request) -> bool: ...                # the raw Host header against LOCAL_HOST
def mount_results(app, build=None) -> None: ...  # app.add_api_route, synchronous handlers
```

  - `GET /results`: `HTMLResponse(PAGE.read_text(encoding="utf-8"), headers=NO_STORE)`. Until Task 9 writes `app/static/results.html` it raises `FileNotFoundError`; this task's tests patch `PAGE`.
  - `GET /api/results`: `JSONResponse(build(), headers=NO_STORE)` under one module-level `threading.Lock()`; a failure outside the sections (Exception or SystemExit) answers `500 {"detail": "results failed: <exception type name>"}`, no-store, never `str(exc)`.
  - Either route, a Host header that is not `127.0.0.1` or `localhost` (any port or none): `403`, the text `refused: this page answers 127.0.0.1 and localhost only`, no-store. A POST gets FastAPI's own `405`.
  - `app/server.py`: `mount_results(app)` exactly once, inside `if a.simulation:`, right after `install(app)`; the banner line `print(f'  results:       http://localhost:{a.http_port}/results')` right after the agent-replay line; importing `app.server` loads no `app.results*` module.
  - `app/server.py`: `class RevalidatedStatic(StaticFiles)`, whose `get_response` sets `Cache-Control: no-cache`, serves `/static` in every mode. Spec 7.1 records that `/static` sent no `Cache-Control`; R1a changes two files every lab page loads without a version query (`i18n.mjs`, Task 6; `style.css`, Task 9), and a browser may run its cached copy for hours (heuristic freshness, from `Last-Modified`), so the nav would show the key `nav.results`. `no-cache` keeps the cache and asks first; on this machine the answer is a 304.

- [ ] **Step 1: Write the failing tests**

Insert this block into `app/test_results.py` directly above the final two lines (`if __name__ == "__main__":` and `    unittest.main()`), below Task 4's block, with the Edit tool (old string: those two lines; new string: this block, two blank lines, then the same two lines). Its only backslashes are the `\n` escapes of the code string a test runs in a subprocess; it holds no `\\`, no backslash-u escape and no character outside ASCII. It imports what it uses itself, and reads `app/agent_api.py` and `app/server.py` from the folder of `app/results_api.py`.

```python
# ---- Task 5: app/results_api.py and its wiring in app/server.py ---------------
import ast  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import sys  # noqa: E402
import tempfile  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402
import unittest  # noqa: E402
import warnings  # noqa: E402
from pathlib import Path  # noqa: E402
from unittest import mock  # noqa: E402

from fastapi import FastAPI  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import results_api as RA  # noqa: E402

APP_DIR = Path(RA.__file__).resolve().parent
LOCAL = {"host": "127.0.0.1:8000"}
TOP_KEYS = {"built", "import_failures", "sections", "not_read"}
REFUSAL = "refused: this page answers 127.0.0.1 and localhost only"


def _results_client(build=None):
    app = FastAPI()
    RA.mount_results(app, build=build)
    return app, TestClient(app)


class RouteTests(unittest.TestCase):
    """app/results_api.py: two GET routes, the Host guard, the lock, no-store (spec 6.1)."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.page = Path(tmp.name) / "results.html"
        self.page.write_text("<!doctype html><title>a results page</title>\n", encoding="utf-8")
        patcher = mock.patch.object(RA, "PAGE", self.page)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_the_page_answers_this_machine_with_or_without_a_port(self):
        _, client = _results_client(build=lambda: {})
        for host in ("127.0.0.1:8000", "localhost:8765", "localhost", "127.0.0.1"):
            r = client.get("/results", headers={"host": host})
            self.assertEqual(r.status_code, 200, host)
            self.assertEqual(r.headers.get("cache-control"), "no-store", host)
            self.assertTrue(r.headers.get("content-type", "").startswith("text/html"), host)
            self.assertEqual(r.text, self.page.read_text(encoding="utf-8"), host)

    def test_the_page_is_read_on_every_request(self):
        _, client = _results_client(build=lambda: {})
        self.page.write_text("<!doctype html><title>changed</title>\n", encoding="utf-8")
        self.assertIn("changed", client.get("/results", headers=LOCAL).text)

    def test_a_foreign_host_is_refused_on_both_routes(self):
        calls = []
        _, client = _results_client(build=lambda: calls.append(1) or {})
        for host in ("evil.example:8000", "127.0.0.1.evil.example", "localhost.evil.example:8000",
                     "127.0.0.2:8000", "localhost:123456", "testserver"):
            for path in ("/results", "/api/results"):
                r = client.get(path, headers={"host": host})
                self.assertEqual(r.status_code, 403, (host, path))
                self.assertEqual(r.headers.get("cache-control"), "no-store", (host, path))
                self.assertEqual(r.text, REFUSAL, (host, path))
        self.assertEqual(calls, [], "a refused request must not build")
        self.assertFalse(RA.host_ok(types.SimpleNamespace(headers={})))

    def test_only_get(self):
        app, client = _results_client(build=lambda: {})
        for path in ("/results", "/api/results"):
            self.assertEqual(client.post(path, headers=LOCAL).status_code, 405, path)
        added = {r.path: set(r.methods) for r in app.routes
                 if getattr(r, "path", None) in ("/results", "/api/results")}
        self.assertEqual(added, {"/results": {"GET"}, "/api/results": {"GET"}})

    def test_the_answer_is_the_build_with_no_store(self):
        body = {"built": {"head": None}, "import_failures": [], "sections": [], "not_read": []}
        _, client = _results_client(build=lambda: body)
        r = client.get("/api/results", headers=LOCAL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(r.json(), body)

    def test_the_default_build_answers_the_contract_keys(self):
        _, client = _results_client()
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ResourceWarning, module="analyse_phase_d")
            r = client.get("/api/results", headers={"host": "localhost"})
        self.assertEqual(r.status_code, 200, r.text[:300])
        self.assertEqual(r.headers.get("cache-control"), "no-store")
        self.assertEqual(set(r.json()), TOP_KEYS)

    def test_a_failing_build_is_a_fixed_500(self):
        for exc in (RuntimeError("secret detail"), SystemExit("secret detail")):
            def boom(exc=exc):
                raise exc

            _, client = _results_client(build=boom)
            r = client.get("/api/results", headers=LOCAL)
            self.assertEqual(r.status_code, 500, type(exc).__name__)
            self.assertEqual(r.headers.get("cache-control"), "no-store")
            self.assertEqual(r.json(), {"detail": f"results failed: {type(exc).__name__}"})
            self.assertNotIn("secret", r.text)

    def test_one_build_at_a_time(self):
        state = {"inside": 0, "peak": 0}
        guard = threading.Lock()

        def slow():
            with guard:
                state["inside"] += 1
                state["peak"] = max(state["peak"], state["inside"])
            time.sleep(0.2)
            with guard:
                state["inside"] -= 1
            return {}

        app, _ = _results_client(build=slow)
        endpoint = next(r.endpoint for r in app.routes
                        if getattr(r, "path", None) == "/api/results")
        request = types.SimpleNamespace(headers=dict(LOCAL))
        threads = [threading.Thread(target=endpoint, args=(request,)) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join(10)
        self.assertEqual(state["peak"], 1)

    def test_the_host_pattern_is_agent_api_s_plus_no_port(self):
        tree = ast.parse((APP_DIR / "agent_api.py").read_text(encoding="utf-8"))
        theirs = next(re.compile(ast.literal_eval(n.value.args[0])) for n in ast.walk(tree)
                      if isinstance(n, ast.Assign)
                      and [getattr(t, "id", None) for t in n.targets] == ["LOCAL_HOST"])
        hosts = ["127.0.0.1:8000", "localhost:8765", "localhost:1", "127.0.0.1:65535",
                 "localhost", "127.0.0.1", "evil.example:8000", "127.0.0.1.evil.example:8000",
                 "localhost.evil.example", "LOCALHOST:8000", "127.0.0.1:", "localhost:123456",
                 "[::1]:8000", ""]
        ours = {h for h in hosts if RA.LOCAL_HOST.fullmatch(h)}
        self.assertEqual(ours, {h for h in hosts if theirs.fullmatch(h)} | {"localhost", "127.0.0.1"})

    def test_server_mounts_results_inside_simulation_after_install(self):
        tree = ast.parse((APP_DIR / "server.py").read_text(encoding="utf-8"))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Call)
                 and getattr(n.func, "id", getattr(n.func, "attr", None)) == "mount_results"]
        self.assertEqual(len(calls), 1, "mount_results( must be called exactly once")
        guarded = [n for n in ast.walk(tree) if isinstance(n, ast.If)
                   and isinstance(n.test, ast.Attribute) and n.test.attr == "simulation"
                   and getattr(n.test.value, "id", None) == "a"]
        self.assertEqual(len(guarded), 1)
        body = [ast.unparse(s) for s in guarded[0].body]
        at = body.index("install(app)")
        self.assertEqual(body[at + 1:at + 3], ["from app.results_api import mount_results",
                                               "mount_results(app)"])
        agents = body.index("print(f'  agent replay:  http://localhost:{a.http_port}/agents')")
        self.assertEqual(body[agents + 1],
                         "print(f'  results:       http://localhost:{a.http_port}/results')")
        top = [n for n in tree.body if isinstance(n, (ast.Import, ast.ImportFrom))]
        self.assertFalse([n for n in top if "results" in (getattr(n, "module", "") or "")],
                         "server.py must not import the results modules at module level")

    def test_static_files_are_revalidated_on_every_load(self):
        from app import server
        client = TestClient(server.app)
        first = client.get("/static/sim/i18n.mjs")
        self.assertEqual(first.status_code, 200)
        self.assertEqual(first.headers.get("cache-control"), "no-cache")
        again = client.get("/static/sim/i18n.mjs", headers={"if-none-match": first.headers["etag"]})
        self.assertEqual(again.status_code, 304)
        self.assertEqual(again.headers.get("cache-control"), "no-cache")

    def test_importing_the_server_loads_no_results_module(self):
        code = ("import json, sys\n"
                "import app.server\n"
                "from fastapi import FastAPI\n"
                "before = sorted(m for m in sys.modules if m.startswith('app.results'))\n"
                "from app.results_api import mount_results\n"
                "mount_results(FastAPI())\n"
                "after = sorted(m for m in sys.modules if m.startswith('app.results'))\n"
                "print(json.dumps([before, after]))\n")
        run = subprocess.run([sys.executable, "-c", code], cwd=APP_DIR.parent, capture_output=True,
                             text=True, timeout=180,
                             env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
        self.assertEqual(run.returncode, 0, run.stderr[-2000:])
        before, after = json.loads(run.stdout.strip().splitlines()[-1])
        self.assertEqual(before, [], "--live and --replay would load the readers")
        self.assertEqual(after, ["app.results_api", "app.results_eval", "app.results_provenance"],
                         "mounting takes the plant hash now, and loads no reader")
```

- [ ] **Step 2: Run the tests and see them fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.RouteTests -v 2>&1 | grep -E "^(ImportError|Ran|FAILED|OK)"
```

Expected (observed in drafting, with Tasks 1 to 4 in place):

```
ImportError: Failed to import test module: test_results
ImportError: cannot import name 'results_api' from 'app' (unknown location). Did you mean: 'results_data'?
Ran 1 test in 0.000s
FAILED (errors=1)
```

- [ ] **Step 3: Write `app/results_api.py`**

Create `app/results_api.py` with exactly this content, with the Write tool. Its only backslashes are the four of `LOCAL_HOST`'s raw pattern, `\.` three times and `\d` once (the Write tool keeps them); its docstring names hosts and routes and carries no figure.

```python
"""The results tab's two routes: GET /results (the page) and GET /api/results (its data).

Imported only from the --simulation branch of app/server.py, which calls
mount_results(app) right after app.agent_api.install(app), so --live and
--replay never load the readers, which import agent code through
app.agent_catalog. The function is not named install, so the route pin on a
single install( call in server.py still holds.

Mounting imports app.results_provenance and no other module of the tab. Its
plant hash is taken when it is imported, and the server loaded the plant
when it started, so the hash is taken then too: taken at the first request
instead, a plant file edited in between would read as the plant the server
runs (spec 5.2).

Both routes are GETs and synchronous: FastAPI runs them in its thread pool,
so a build never blocks the event loop, and one module-level lock lets one
build run at a time; a second request waits for it. Both answer
Cache-Control: no-store, the refusal included.

THE GUARD. A request whose raw Host header is not 127.0.0.1 or localhost,
with any port or none, gets a fixed-text refusal: that stops DNS rebinding.
No Origin is required, because a browser sends none on a same-origin GET.
The pattern is app.agent_api.LOCAL_HOST's, copied rather than imported
(importing it would load agent code) and widened to a host with no port.

Neither route takes a parameter, so nothing from a request reaches the
filesystem. A failure outside every section answers a server error with a
fixed text naming the exception's type, never str(exc).
"""
import re
import threading
from pathlib import Path

from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse

LOCAL_HOST = re.compile(r"^(127\.0\.0\.1|localhost)(:\d{1,5})?$")
NO_STORE = {"Cache-Control": "no-store"}
PAGE = Path(__file__).resolve().parent / "static" / "results.html"
_LOCK = threading.Lock()


def host_ok(request) -> bool:
    """True when the raw Host header names this machine, with any port or none."""
    return LOCAL_HOST.fullmatch(request.headers.get("host") or "") is not None


def _refused():
    return PlainTextResponse("refused: this page answers 127.0.0.1 and localhost only",
                             status_code=403, headers=NO_STORE)


def mount_results(app, build=None) -> None:
    """Add GET /results and GET /api/results to `app`.

    `build` replaces app.results_data.build; tests pass a stand-in. The
    default is imported inside the handler, on the first request, so
    mounting loads no reader. The plant hash is taken here, when mounting:
    see the module docstring.
    """
    from app import results_provenance  # noqa: F401  (its plant hash, taken now)

    def results_page(request: Request):
        """The tab's frame, read from app/static/results.html on every request."""
        if not host_ok(request):
            return _refused()
        return HTMLResponse(PAGE.read_text(encoding="utf-8"), headers=NO_STORE)

    def results_answer(request: Request):
        """Every section, rebuilt from the files, one build at a time."""
        if not host_ok(request):
            return _refused()
        try:
            with _LOCK:
                if build is None:
                    from app.results_data import build as run
                else:
                    run = build
                return JSONResponse(run(), headers=NO_STORE)
        except (Exception, SystemExit) as exc:
            return JSONResponse({"detail": f"results failed: {type(exc).__name__}"},
                                status_code=500, headers=NO_STORE)

    app.add_api_route("/results", results_page, methods=["GET"],
                      response_class=HTMLResponse)
    app.add_api_route("/api/results", results_answer, methods=["GET"])
```

- [ ] **Step 4: Run the tests: every route test passes but the two that need Step 5's edits to `app/server.py`**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.RouteTests -v 2>&1 | grep -E "^(FAIL:|AssertionError|Ran|OK|FAILED)"
```

Expected (observed in drafting): `app/server.py` neither mounts the routes nor revalidates `/static` yet.

```
FAIL: test_server_mounts_results_inside_simulation_after_install (app.test_results.RouteTests.test_server_mounts_results_inside_simulation_after_install)
AssertionError: 0 != 1 : mount_results( must be called exactly once
FAIL: test_static_files_are_revalidated_on_every_load (app.test_results.RouteTests.test_static_files_are_revalidated_on_every_load)
AssertionError: None != 'no-cache'
Ran 12 tests in 1.900s
FAILED (failures=2)
```

- [ ] **Step 5: Mount the routes in `app/server.py`, revalidate `/static`, and put the four modules in the write scan**

Run this script from the repository root. It applies six replacements (five in `app/server.py`: the docstring's route paragraph, the `RevalidatedStatic` class just above `app = FastAPI(`, the `/static` mount that uses it, the banner line, the mount of the results routes; one in `app/test_agents.py`: `NEW_MODULES`), each anchored on text that occurs exactly once, keeps each file's CRLF line ends, and skips a replacement already made, so a second run changes nothing. It holds no backslash at all, because the Bash tool collapses `\\` in a command: CR and LF are `chr(13)` and `chr(10)`. (The same six edits made with the Edit tool are equally right, if the tool keeps the files' CRLF.)

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY - <<'EOF'
from pathlib import Path

CR, LF = chr(13), chr(10)
EDITS = {
    "app/server.py": [
        ('''it sends nothing anywhere and has no path to the vehicle either.
''', '''it sends nothing anywhere and has no path to the vehicle either.
Two GET routes, /results and /api/results, are added by
app.results_api.mount_results() only under --simulation: they read the
result files under results/ and write nothing.
'''),
        ('''app = FastAPI(title="Engine Supervisor''', '''class RevalidatedStatic(StaticFiles):
    """/static, with Cache-Control: no-cache on every answer.

    Without it a browser may run a file from its cache for hours after the
    file changed (heuristic freshness, from Last-Modified), and the pages
    load i18n.mjs and style.css without a version query: after an update
    the nav could show the key nav.results instead of its name. no-cache
    keeps the cache but asks first, and on this machine the answer is a 304.
    """

    async def get_response(self, path, scope):
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache"
        return response


app = FastAPI(title="Engine Supervisor'''),
        ('''app.mount('/static', StaticFiles(directory=''',
         '''app.mount('/static', RevalidatedStatic(directory='''),
        ('''        print(f'  agent replay:  http://localhost:{a.http_port}/agents')
''', '''        print(f'  agent replay:  http://localhost:{a.http_port}/agents')
        print(f'  results:       http://localhost:{a.http_port}/results')
'''),
        ('''        install(app)
''', '''        install(app)
        from app.results_api import mount_results
        mount_results(app)
'''),
    ],
    "app/test_agents.py": [
        ('''NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py", "laya_worker.py", "laya_bridge.py")
''', '''NEW_MODULES = ("agent_trace.py", "agent_catalog.py", "agent_api.py", "model_questions.py",
               "jev.py", "laya_worker.py", "laya_bridge.py",
               "results_eval.py", "results_provenance.py", "results_data.py", "results_api.py")
'''),
    ],
}
for rel, edits in EDITS.items():
    path = Path(rel)
    raw = path.read_bytes().decode("utf-8")
    crlf = (CR + LF) in raw
    text = raw.replace(CR + LF, LF)
    done = 0
    for old, new in edits:
        if text.count(new) == 1:
            continue
        assert text.count(old) == 1, (rel, old.splitlines()[0], text.count(old))
        text = text.replace(old, new)
        done += 1
    if done:
        path.write_bytes((text.replace(LF, CR + LF) if crlf else text).encode("utf-8"))
    print(f"{rel}: {done} of {len(edits)} edits applied,", "CRLF kept" if crlf else "LF kept")
EOF

git diff -U0 -- app/server.py app/test_agents.py | grep -E "^[+-][^+-]"
```

Expected (observed: this script on copies of this tree's `app/server.py` and `app/test_agents.py`, CRLF as checked out, in a scratch repository; run a second time it prints `0 of 5` and `0 of 1` and changes nothing):

```
app/server.py: 5 of 5 edits applied, CRLF kept
app/test_agents.py: 1 of 1 edits applied, CRLF kept
+Two GET routes, /results and /api/results, are added by
+app.results_api.mount_results() only under --simulation: they read the
+result files under results/ and write nothing.
+class RevalidatedStatic(StaticFiles):
+    """/static, with Cache-Control: no-cache on every answer.
+    Without it a browser may run a file from its cache for hours after the
+    file changed (heuristic freshness, from Last-Modified), and the pages
+    load i18n.mjs and style.css without a version query: after an update
+    the nav could show the key nav.results instead of its name. no-cache
+    keeps the cache but asks first, and on this machine the answer is a 304.
+    """
+    async def get_response(self, path, scope):
+        response = await super().get_response(path, scope)
+        response.headers["Cache-Control"] = "no-cache"
+        return response
-app.mount('/static', StaticFiles(directory=os.path.join(HERE, 'static')), name='static')
+app.mount('/static', RevalidatedStatic(directory=os.path.join(HERE, 'static')), name='static')
+        print(f'  results:       http://localhost:{a.http_port}/results')
+        from app.results_api import mount_results
+        mount_results(app)
-               "jev.py", "laya_worker.py", "laya_bridge.py")
+               "jev.py", "laya_worker.py", "laya_bridge.py",
+               "results_eval.py", "results_provenance.py", "results_data.py", "results_api.py")
```

- [ ] **Step 6: Run the tests and the agents suite's pins, and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -m unittest app.test_results.RouteTests -v 2>&1 | tee "$SP/r1a_routes_task05.txt" | grep -E "^(FAIL:|AssertionError|Ran|OK|FAILED)"
$PY -m unittest app.test_agents.RouteTests.test_routes_only_under_simulation app.test_agents.NoWriteTests app.test_agents.NoNetworkTests app.test_agents.PrintScanTests -v 2>&1 | tee "$SP/r1a_pins_task05.txt" | grep -E "^(FAIL:|AssertionError|Ran|OK|FAILED)"
```

Expected (observed in drafting; the times vary):

```
Ran 12 tests in 1.792s
OK
Ran 8 tests in 0.597s
OK
```

The second command is the existing pin of the agents suite (one call named `install(`, inside `if a.simulation:`; importing `app.server` loads no `app.agent*` module; module-level routes GET or HEAD only) plus the write, network and print scans, `NoWriteTests` now reading the four results modules. In drafting it ran against copies of the edited `app/server.py` and `app/test_agents.py`, with Tasks 1 to 4's drafted modules beside them.

- [ ] **Step 7: The byte check and the whole suites**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
for f in app/results_api.py app/server.py app/test_agents.py app/test_results.py; do $PY -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" "$f"; done
$PY -W error::SyntaxWarning -c "import pathlib, sys; [compile(pathlib.Path(p).read_text(encoding='utf-8'), p, 'exec') for p in sys.argv[1:]]; print('compiled:', ', '.join(sys.argv[1:]))" app/results_api.py app/server.py app/test_agents.py app/test_results.py
$PY -m app.test_results 2>&1 | tee "$SP/r1a_results_task05.txt" | grep -E "^(Ran|OK|FAILED)"
$PY -m app.test_simulation 2>&1 | grep -E "^(Ran|OK|FAILED)"
$PY -m app.test_replay 2>&1 | tee "$SP/r1a_replay_task05.txt" | grep -E "M7: app.server imports|READ-ONLY|checks pass"
```

Expected (the times vary):

```
literal invisible: []
literal invisible: []
literal invisible: []
literal invisible: []
compiled: app/results_api.py, app/server.py, app/test_agents.py, app/test_results.py
Ran 104 tests in 7.168s
OK
Ran 15 tests in 1.075s
OK
  PASS  M7: app.server imports and serves its three pages   16 routes
  PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns
49 of 49 checks pass
```

Observed in drafting: the byte check and the compile line on the drafted and edited files; `Ran 104 tests`, `OK` for the whole file with Tasks 1 to 3 (27, 17 and 21) and Tasks 4 and 5 (27 and 12); `Ran 15 tests`, `OK` and `49 of 49` on this tree before R1a. `16 routes` does not move, because the two results routes are added in `main()`, never at import. `app.test_simulation` does not import `app.server`. `app.test_replay` takes about 75 s.

- [ ] **Step 8: No new failing entry in `app.test_agents`**

As in Task 4, Step 6: the whole agents suite, compared entry by entry with the coordinator's capture of its state before R1a.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task05.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task05.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task05.txt" > "$SP/r1a_agents_fail_task05.txt"
echo "new failing entries:"; comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task05.txt"; echo "(end)"
```

Expected (not run in drafting with this task's edits in the tree, which drafting may not write to; the pins this task touches passed in Step 6, and this is what the suite printed on this tree before R1a):

```
Ran 126 tests in 47.096s
FAILED (failures=16, errors=3, skipped=1)
new failing entries:
(end)
```

The baseline was recorded with `errors=3` on one run and `errors=4` on another, before any R1a change. If a line appears between `new failing entries:` and `(end)`, run the block once more: a line that appears in only one of the two runs is that intermittent error, and it goes into the task report; a line that appears in both is a regression this task caused, and it is fixed before the commit.

- [ ] **Step 9: Commit**

By explicit path only: another session is editing `CLAUDE.md`, `handoff.md`, `team/jad.md` and `NEXT_SESSION_*.md` in this tree.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
{
  printf '%s\n\n' "Results tab R1a (task 5): GET /results and /api/results under --simulation"
  printf '%s\n' \
    "app/results_api.py adds the two GET routes through mount_results(app): the page," \
    "read from app/static/results.html on every request, and every section rebuilt by" \
    "results_data.build(), one build at a time. Both refuse a Host that is not" \
    "127.0.0.1 or localhost (any port or none) with a fixed 403, both answer no-store," \
    "and a failed build is a fixed 500 naming the exception's type." \
    "" \
    "app/server.py mounts them inside 'if a.simulation:', right after install(app)," \
    "so --live and --replay never load the readers; its banner and docstring name them." \
    "Mounting imports results_provenance, so its plant hash is the one the server" \
    "started with. /static now answers Cache-Control: no-cache, in every mode: R1a" \
    "changes i18n.mjs and style.css, which the pages load without a version query," \
    "and a browser may otherwise run its cached copies for hours." \
    "app/test_agents.py: NEW_MODULES now holds the four results modules, so the write" \
    "scan reads them. RouteTests cover the guard, no-store, GET only, the lock, the" \
    "fixed 500, the wiring and the revalidated /static." \
    ""
  printf '%s\n' "python -m unittest app.test_results.RouteTests:"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_routes_task05.txt" | tr -d '\r'
  printf '%s\n' "" "python -m unittest (the agents suite's pins and scans):"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_pins_task05.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_results:"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_results_task05.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_replay:"
  grep -E "READ-ONLY|checks pass" "$SP/r1a_replay_task05.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_agents (against the capture before R1a):"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task05.txt" | tr -d '\r'
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task05.txt"
cat "$SP/r1a_msg_task05.txt"
git add app/results_api.py app/server.py app/test_agents.py app/test_results.py
git commit -F "$SP/r1a_msg_task05.txt" -- app/results_api.py app/server.py app/test_agents.py app/test_results.py
git log -1 --format=%B | sed '/^$/d' | tail -n 1
git status --short -- app/results_api.py app/server.py app/test_agents.py app/test_results.py
```

Expected (not run in this repository in drafting, which may not commit here): `cat` prints the message, subject first and the `Co-Authored-By` line last; `git` may warn `LF will be replaced by CRLF`, which is `core.autocrlf` and harmless; then a line `[JMF-2340550-results-tab <sha>] Results tab R1a (task 5): GET /results and /api/results under --simulation`, `4 files changed`, `create mode 100644 app/results_api.py`, and the last line of the message, `Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`. `git status --short` then prints nothing for the four paths.

To see it in the lab once Task 9 has written the page: `$PY -m app.server --simulation --http-port 8765` prints the `results:` banner line, and `http://localhost:8765/api/results` answers the JSON of Task 4 (`/results` answers 500 until `app/static/results.html` exists).

### Task 6: Number formatting, the tab's strings, and the nav key

The tab's typography and every word it shows. `results-format.mjs` writes every number the tab prints (U+2212 for a minus, U+202F between thousands, an em dash for a missing value, a left-to-right isolate around a number inside Arabic). `results-strings.mjs` holds every `results.*` key of contract section 5, the English word for word from the contract and the Arabic authored beside it, and merges them into the lab's `STRINGS` once, at import. `i18n.mjs` gains `nav.results` right after `nav.agents`, so Task 9's nav link has its words. No Python file changes. One Python test reads `i18n.mjs`: `app/test_agents.py` `PageTests.test_chase_is_optional` follows the agents page's static imports through it, and this task adds no import line; Step 10 runs it.

**The escape rule of this task.** On this machine the Write, Edit and Bash tools turn a typed backslash-u escape into the literal, often invisible, character, and the Bash tool also collapses a typed doubled backslash into one. So:

- the two test files contain no escape at all: they build every special character from its code point (`String.fromCodePoint`, and the escape TEXT from `String.fromCharCode(92)`). Create them with the Write tool exactly as written below; each one checks its own source for a decoded escape;
- the two `.mjs` modules that must carry escapes are written by Python scripts in which each escape is a marker `<U+XXXX>`; the script turns each marker into the escape text with `chr(92) + "u" + hex`, so no tool on the way can decode it. The short scripts (Steps 3 and 7) are quoted heredocs (`<<'PYEOF'`, so bash expands nothing in them): run each block in Git Bash exactly as it stands. The strings script of Step 8 is about 26 KB, and a heredoc that long does not survive the Bash tool here (in drafting, the whole block failed with `unexpected EOF while looking for matching` at about 8 KB, while 2 KB and 4 KB pieces of it passed byte for byte), so Step 8 has you create it as a file with the Write tool, which leaves it unchanged because it holds neither a backslash-u nor a doubled backslash. Never type an escape by hand;
- each such module is byte-checked right after it is written (contract section 0).

**The rounding decision** (the brief asked for it to be decided and tested). `fmtNum` and `fmtSigned` apply `toFixed` to the MAGNITUDE and add the sign afterwards, which is exactly what `formatDiff` on `/agents` does: a value stored exactly at a half rounds away from zero in both signs (`fmtNum(-1.25, 1)` is MINUS + `1.3`, `fmtNum(1.25, 1)` is `1.3`), a value stored just under a half rounds down (`fmtNum(1.005, 2)` is `1.00`), and a value that rounds to zero carries no minus (`fmtNum(-0.04, 1)` is `0.0`, `fmtSigned(-0.04, 1)` is `+0.0`). Python's `format()` rounds an exact half to even (`1.25` gives `1.2`); the tab prints a file's numbers at the digits the file printed them with, so the two never meet on a tie. `fmtInt` applies `Math.round` to the magnitude too, so `-2.5` gives MINUS + `3` as `2.5` gives `3` (`Math.round(-2.5)` alone would give `-2`).

**Arabic wording, for the reviewer.** The English of every key is the contract's. The Arabic follows the lab's and `/agents`' vocabulary: plant «المحاكي» (as in «بصمة المحاكي» on `/agents`); this tree «هذه النسخة»; seed «بذرة»; episode «حلقة», frozen episodes «حلقات مجمّدة»; sighted / blind «المُبصر» / «الأعمى»; median «الوسيط»; damage units «وحدات ضرر»; MEI «الحد الأدنى المهم» (as in `agent_catalog.SHORT_VERDICT`); the knock «الطَّرْق» WITH its marks, and the knock term «ضرر الطَّرْق» (unmarked «الطرق» reads as "the roads"); spark advance «تبكير الشرارة» (never «تقديم», which contains the banned «قديم»); spark trim «تعديل توقيت الشرارة» (as `agents.action.spark`); the engine computer «حاسوب المحرك المنمذَج»; reactive «السياسة التفاعلية» (beside «سياسة current-grade» in the legend); hand-written policies «السياسات المكتوبة يدوياً»; current-grade stays Latin inside an isolate (the legend reads «سياسة current-grade», so it carries an Arabic word); `git`, `Python` and `commit` stay Latin, as the team writes them. Inside an Arabic line every Latin word and every digit is a left-to-right isolate (U+2066 ... U+2069), and so is every placeholder that always holds ONE number, hash, commit, date, path, module or protocol; `{name}`, `{other}`, `{have}`, `{list}` and `{seeds}` stay bare because they may hold Arabic words or a list, and the caller isolates each Latin item it puts there. The test pins all of this. Only the window title («النتائج — GRAD», as `/agents`' title) and the footer index (`03 — RESULTS`, identical in both languages, inside the frame's `dir="ltr"` span) carry Latin outside an isolate.

**Files:**
- Create: `app/static/sim/results-format.mjs` (written by the Python script of Step 3)
- Create: `app/static/sim/results-strings.mjs` (written by the Python script of Step 8)
- Modify: `app/static/sim/i18n.mjs` — one line after line 57 (`'nav.agents': 'الوكلاء',`, Arabic) and one after line 275 (`'nav.agents': 'Agents',`, English), line numbers as before the edit
- Test: `app/static/sim/results-format.test.mjs` (new)
- Test: `app/static/sim/results-strings.test.mjs` (new)

**Interfaces:**
- Consumes: `isolateLtr(text)` (U+2066 + text + U+2069) from `./agent-picker.mjs`, and `formatDiff(v)` from the same file in the test only; `STRINGS`, `LANGS`, `t(lang, key, vars)`, `missingKeys()` from `./i18n.mjs`. Nothing from Tasks 1 to 5. The shared lab modules are imported WITHOUT a query, the tab's own WITH `?v=R1a` (contract section 4).
- Produces, `app/static/sim/results-format.mjs` (contract 4.1), imported by the tab as `./results-format.mjs?v=R1a`:
  - `EM_DASH` (U+2014), `MINUS` (U+2212), `NNBSP` (U+202F), `ltr` (the same function object as `isolateLtr`);
  - `fmtNum(v, digits) -> string`: `toFixed(digits)` of the magnitude, U+2212 for a negative, no sign when it rounds to zero, no thousands grouping; `EM_DASH` for anything but a finite number (`null`, `undefined`, `NaN`, infinities, strings, booleans, objects);
  - `fmtSigned(v, digits) -> string`: as `fmtNum`, always signed: `'+'` or U+2212, `'+0.0'` when it rounds to zero; `ltr(fmtSigned(v, 1)) === formatDiff(v)` for every finite `v`;
  - `fmtInt(v) -> string`: `Math.round` of the magnitude, grouped with U+202F from 1000 up (`fmtInt(300000)` is `300` + U+202F + `000`, `fmtInt(950)` is `950`), U+2212 for a negative;
  - `inline(lang, text) -> string`: `lang === 'ar' ? ltr(text) : text`.
- Produces, `app/static/sim/results-strings.mjs` (contract 4.2), imported ONCE by the page as `./results-strings.mjs?v=R1a` (the import merges):
  - `RESULTS_STRINGS = { ar: {...}, en: {...} }`: the 110 keys of contract section 5 in each language, in the contract's order;
  - `mergeInto(target, extra) -> number` (the keys each language gained): `agents-strings.mjs` `mergeStrings`' rules, its own copy; throws `results strings: unknown language "<lang>"`, `results strings: "<key>" is missing from <lang> (present in <langs>)`, `results strings: "<key>" collides with an existing <lang> string`, and writes nothing when it throws. A second copy of the module (any other `?v=` value, or none) therefore throws "collides" at import and leaves `STRINGS` as it was.
  - The slot convention Task 9's view relies on: Arabic lines isolate these slots themselves: `{command} {commit} {date} {detail} {episodes} {eval_dt} {file} {frozen} {head} {live} {mei} {module} {plant} {prefix} {protocol} {python} {recorded} {seed} {status} {steps} {tag} {train_dt} {type}` (an already-isolated value passed in nests harmlessly); `{name} {other} {have} {list} {seeds}` are bare, and the caller isolates each Latin item it puts there.
- Produces, `app/static/sim/i18n.mjs`: `STRINGS.ar['nav.results'] === 'النتائج'`, `STRINGS.en['nav.results'] === 'Results'`, each the key right after `nav.agents` (so `nav.agents` stays right after `nav.review`, as `agents-strings.test.mjs` pins).

- [ ] **Step 1: Write the failing test for the formatter**

Create `app/static/sim/results-format.test.mjs` with the Write tool, with exactly this content:

```js
// results-format.mjs: how the results tab writes a number, and the left-to-right
// isolates it puts around one inside an Arabic line (spec section 7.2).
//
// Characters that are invisible or look like ASCII (U+2066 and U+2069, the
// isolates; U+2212 MINUS SIGN; U+202F NARROW NO-BREAK SPACE) are built here from
// their code points, and an escape's TEXT from String.fromCharCode(92): the
// Write tool on this machine decodes a typed backslash-u escape into the
// character. The last test checks that this file keeps to that rule.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { isolateLtr, formatDiff } from './agent-picker.mjs';
import { EM_DASH, MINUS, NNBSP, ltr, fmtNum, fmtSigned, fmtInt, inline } from './results-format.mjs?v=R1a';

const cp = n => String.fromCodePoint(n);
const LRI = cp(0x2066);
const PDI = cp(0x2069);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;
// Invisible, or easily taken for ASCII: never literal in a source file.
const INVISIBLE = [0x061c, 0x200b, 0x200e, 0x200f, 0x2011, 0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x202f, 0x2066, 0x2067, 0x2068, 0x2069, 0x2212, 0xfeff];
const NOT_A_NUMBER = [null, undefined, NaN, Infinity, -Infinity, '12', true, {}];

test('the constants are the characters the spec names, and ltr is the isolate /agents uses', () => {
  assert.equal(EM_DASH, cp(0x2014));
  assert.equal(MINUS, cp(0x2212));
  assert.equal(NNBSP, cp(0x202f));
  assert.equal(ltr, isolateLtr);
  assert.equal(ltr('7'), `${LRI}7${PDI}`);
});

// The decision this file pins: toFixed on the MAGNITUDE. An exact binary half
// rounds away from zero, in both signs, as formatDiff on /agents does. Python's
// format() would give 1.2 for 1.25 (half to even); the tab never re-rounds a
// file's printed digits, so the two never meet on a tie.
test('fmtNum rounds the magnitude as toFixed does, writes U+2212 and never a negative zero', () => {
  assert.equal(fmtNum(920.1, 1), '920.1');
  assert.equal(fmtNum(-12.34, 1), `${MINUS}12.3`);
  assert.equal(fmtNum(-1.25, 1), `${MINUS}1.3`);
  assert.equal(fmtNum(1.25, 1), '1.3');
  assert.equal(fmtNum(0.125, 2), '0.13');
  assert.equal(fmtNum(1.005, 2), '1.00', '1.005 is stored just under the half, and toFixed reads the stored value');
  assert.equal(fmtNum(-0.04, 1), '0.0');
  assert.equal(fmtNum(-0, 1), '0.0');
  assert.equal(fmtNum(0, 0), '0');
  assert.equal(fmtNum(2527, 1), '2527.0', 'fmtNum does not group: a file\'s number keeps its printed shape');
  assert.ok(!fmtNum(-3, 1).includes('-'), 'an ASCII hyphen is not a minus sign');
});

test('fmtSigned always carries a sign, and agrees with formatDiff on /agents digit for digit', () => {
  assert.equal(fmtSigned(0, 1), '+0.0');
  assert.equal(fmtSigned(-2, 1), `${MINUS}2.0`);
  assert.equal(fmtSigned(2, 1), '+2.0');
  assert.equal(fmtSigned(-0.04, 1), '+0.0');
  assert.equal(fmtSigned(360.6, 1), '+360.6');
  assert.equal(fmtSigned(-1.25, 1), `${MINUS}1.3`);
  assert.equal(fmtSigned(-0.5, 0), `${MINUS}1`);
  for (const v of [-360.6, -9.8, -1.25, -0.04, 0, 0.04, 0.05, 1.25, 30.2]) {
    assert.equal(ltr(fmtSigned(v, 1)), formatDiff(v), `fmtSigned(${v}) differs from formatDiff`);
  }
});

test('fmtInt rounds, groups thousands with U+202F from 1000 up, and writes U+2212', () => {
  assert.equal(fmtInt(300000), `300${NNBSP}000`);
  assert.equal(fmtInt(50000), `50${NNBSP}000`);
  assert.equal(fmtInt(950), '950');
  assert.equal(fmtInt(999), '999');
  assert.equal(fmtInt(1000), `1${NNBSP}000`);
  assert.equal(fmtInt(1234567), `1${NNBSP}234${NNBSP}567`);
  assert.equal(fmtInt(-1234), `${MINUS}1${NNBSP}234`);
  assert.equal(fmtInt(999.5), `1${NNBSP}000`);
  assert.equal(fmtInt(2.5), '3');
  assert.equal(fmtInt(-2.5), `${MINUS}3`, 'the magnitude is rounded, so -2.5 mirrors 2.5');
  assert.equal(fmtInt(-0.4), '0');
  assert.equal(fmtInt(20), '20');
});

test('inline isolates in Arabic only', () => {
  assert.equal(inline('ar', 'x'), `${LRI}x${PDI}`);
  assert.equal(inline('en', 'x'), 'x');
  assert.equal(inline('ar', fmtInt(300000)), `${LRI}300${NNBSP}000${PDI}`);
  assert.equal(inline('en', fmtSigned(-2, 1)), `${MINUS}2.0`);
});

test('a missing or non-finite value is an em dash in every formatter', () => {
  for (const bad of NOT_A_NUMBER) {
    assert.equal(fmtNum(bad, 1), EM_DASH, `fmtNum(${String(bad)})`);
    assert.equal(fmtSigned(bad, 1), EM_DASH, `fmtSigned(${String(bad)})`);
    assert.equal(fmtInt(bad), EM_DASH, `fmtInt(${String(bad)})`);
  }
});

test('results-format.mjs carries its three characters as escapes, never literally', () => {
  const src = readFileSync(new URL('./results-format.mjs', import.meta.url), 'utf8');
  for (const code of INVISIBLE) {
    assert.equal(src.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in results-format.mjs: write the escape`);
  }
  for (const hex of ['2014', '2212', '202f']) {
    assert.equal(src.split(escapeText(hex)).length - 1, 1, `the escape of U+${hex} must appear exactly once`);
  }
  assert.match(src, /^import \{ isolateLtr \} from '\.\/agent-picker\.mjs';$/m, 'the isolate comes from agent-picker.mjs, unversioned');
});

test('this file builds its characters from code points, never from a typed escape', () => {
  const own = readFileSync(new URL(import.meta.url), 'utf8');
  for (const code of INVISIBLE) assert.equal(own.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in this test file`);
  assert.equal(own.split(escapeText('')).length - 1, 0, 'a typed backslash-u escape in this test file');
});
```

- [ ] **Step 2: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-format.test.mjs
```

Expected: FAIL. The file cannot load its module, so node reports one failing file and no test inside it ran:

```
  code: 'ERR_MODULE_NOT_FOUND',
  url: 'file:///…/app/static/sim/results-format.mjs?v=R1a'
}
✖ static\sim\results-format.test.mjs
ℹ tests 1
ℹ pass 0
ℹ fail 1
```

- [ ] **Step 3: Write `results-format.mjs` through Python, then byte-check it**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
"$PY" - <<'PYEOF'
import re
from pathlib import Path

# The source of app/static/sim/results-format.mjs. Each <U+XXXX> marker
# becomes the escape TEXT backslash-u-xxxx, built from chr(92) below, so no
# tool on the way can turn it into the literal character.
SRC = r"""
// Number formatting and bidi isolates for the results tab (/results).
//
// PURE: no DOM, no fetch, no physics. Every number the tab writes goes through
// here, so the spec's typographic rules (section 7.2) hold everywhere:
//  - a negative number takes U+2212 MINUS SIGN, never an ASCII hyphen;
//  - thousands are grouped with U+202F NARROW NO-BREAK SPACE, whose bidi class
//    (CS) keeps a grouped number whole inside an Arabic line, where U+2009
//    (WS) would split it;
//  - inside Arabic text a number, hash, date or path is a left-to-right
//    isolate, U+2066 ... U+2069: isolateLtr from agent-picker.mjs, exported
//    here as ltr so the tab has one source for it.
// The three constants are written as escapes, never as the characters: the
// Write tool on this machine decodes a typed escape, so this file is written
// by a Python script and byte-checked (results-format.test.mjs pins both).
//
// ROUNDING is toFixed's, applied to the magnitude, so a negative rounds as its
// positive does. A value stored exactly at a half rounds away from zero
// (1.25 -> 1.3, -1.25 -> -1.3), as agent-picker.mjs formatDiff rounds, so the
// two pages print the same digits for the same number; a value stored just
// under a half rounds down (1.005 -> 1.00). Python's format() rounds an exact
// half to even (1.25 -> 1.2); the tab prints a file's numbers at the digits
// the file printed them with, where no such tie can arise.
import { isolateLtr } from './agent-picker.mjs';

export const EM_DASH = '<U+2014>';
export const MINUS = '<U+2212>';
export const NNBSP = '<U+202F>';

/** `text` inside a left-to-right isolate, U+2066 ... U+2069 (agent-picker.mjs). */
export const ltr = isolateLtr;

const finite = v => typeof v === 'number' && Number.isFinite(v);

/**
 * `v` with `digits` decimals. A negative takes U+2212; a value that rounds to
 * zero carries no sign ("0.0", never "-0.0"); a missing or non-finite value is
 * an em dash. Not grouped: a file's numbers keep the shape the file printed.
 */
export function fmtNum(v, digits) {
  if (!finite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(digits);
  return v < 0 && Number(text) !== 0 ? `${MINUS}${text}` : text;
}

/**
 * As fmtNum, and always signed: '+' for a positive value or one that rounds
 * to zero ("+0.0"), U+2212 for a negative one.
 */
export function fmtSigned(v, digits) {
  if (!finite(v)) return EM_DASH;
  const text = Math.abs(v).toFixed(digits);
  return `${v < 0 && Number(text) !== 0 ? MINUS : '+'}${text}`;
}

/**
 * A whole number: Math.round of the magnitude (so -2.5 gives -3, as 2.5 gives
 * 3), grouped in thousands with U+202F from 1000 up, U+2212 for a negative.
 */
export function fmtInt(v) {
  if (!finite(v)) return EM_DASH;
  const n = Math.round(Math.abs(v));
  const text = String(n).replace(/\B(?=(\d{3})+(?!\d))/g, NNBSP);
  return v < 0 && n !== 0 ? `${MINUS}${text}` : text;
}

/** `text` isolated left to right inside an Arabic line; in English, as it is. */
export function inline(lang, text) {
  return lang === 'ar' ? ltr(text) : text;
}
""".lstrip()

out = re.sub(r"<U[+]([0-9A-F]{4})>", lambda m: chr(92) + "u" + m.group(1).lower(), SRC)
assert "<U+" not in out, "a marker was mistyped"
path = Path("app/static/sim/results-format.mjs")
path.write_bytes(out.encode("utf-8"))
print(path.as_posix(), "written,", out.count(chr(92) + "u"), "escapes")
PYEOF
"$PY" -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" app/static/sim/results-format.mjs
"$PY" -c "import sys; s=open(sys.argv[1],encoding='utf-8').read(); print({h: s.count(chr(92) + 'u' + h) for h in ('2014', '2212', '202f')})" app/static/sim/results-format.mjs
```

Expected, exactly: each of the three constants carries its escape once (a backslash, `u` and four hex digits), and no invisible character is in the file literally:

```
app/static/sim/results-format.mjs written, 3 escapes
literal invisible: []
{'2014': 1, '2212': 1, '202f': 1}
```

Any other count means an escape was decoded or a marker mistyped: delete the file and re-run the block as it stands.

- [ ] **Step 4: Run the formatter's test and see it pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-format.test.mjs
```

Expected:

```
✔ the constants are the characters the spec names, and ltr is the isolate /agents uses
✔ fmtNum rounds the magnitude as toFixed does, writes U+2212 and never a negative zero
✔ fmtSigned always carries a sign, and agrees with formatDiff on /agents digit for digit
✔ fmtInt rounds, groups thousands with U+202F from 1000 up, and writes U+2212
✔ inline isolates in Arabic only
✔ a missing or non-finite value is an em dash in every formatter
✔ results-format.mjs carries its three characters as escapes, never literally
✔ this file builds its characters from code points, never from a typed escape
ℹ tests 8
ℹ suites 0
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms …
```

- [ ] **Step 5: Write the failing test for the strings and the nav key**

Create `app/static/sim/results-strings.test.mjs` with the Write tool, with exactly this content (its `CONTRACT` table is contract section 5, key by key; the two lines with a subtraction build U+2212 from its code point):

```js
// The results tab's strings (results-strings.mjs), the merge that adds them to
// the lab's table, and the lab's one new key, nav.results (i18n.mjs).
// node --test runs every test file in its own process, so the merge this file
// triggers never reaches another test file.
//
// Characters that are invisible or look like ASCII (U+2066 / U+2068 / U+2069,
// the isolates; U+2212 MINUS SIGN; U+202F NARROW NO-BREAK SPACE) are built here
// from their code points, and an escape's TEXT from String.fromCharCode(92):
// the Write tool on this machine decodes a typed backslash-u escape into the
// character. One test checks that this file keeps to that rule.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { STRINGS, LANGS, missingKeys, t } from './i18n.mjs';

// Taken BEFORE results-strings.mjs is imported: the lab's strings as the lab ships them.
const before = structuredClone(STRINGS);
let mod = null;
let loadError = null;
try { mod = await import('./results-strings.mjs?v=R1a'); } catch (err) { loadError = err; }
const api = () => {
  assert.ok(mod, `results-strings.mjs must load: ${loadError?.message}`);
  return mod;
};

const cp = n => String.fromCodePoint(n);
const LRI = cp(0x2066);
const FSI = cp(0x2068);
const PDI = cp(0x2069);
const RLM = cp(0x200f);
const MINUS = cp(0x2212);
const NNBSP = cp(0x202f);
const escapeText = hex => `${String.fromCharCode(92)}u${hex}`;
const iso = text => `${LRI}${text}${PDI}`;
// Invisible, or easily taken for ASCII: never literal in a source file.
const INVISIBLE = [0x061c, 0x200b, 0x200e, 0x200f, 0x2011, 0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x202f, 0x2066, 0x2067, 0x2068, 0x2069, 0x2212, 0xfeff];
const ARABIC_LETTER = new RegExp(`[${cp(0x0621)}-${cp(0x064a)}]`);
const DIACRITICS = new RegExp(`[${cp(0x064b)}-${cp(0x0652)}${cp(0x0670)}]`, 'g');
const bare = text => text.normalize('NFC').replace(DIACRITICS, '');
const nfc = text => text.normalize('NFC');

// Contract section 5: every key, with its English exactly as the contract fixes it.
const CONTRACT = {
  'results.page.title': 'Results — GRAD',
  'results.intro.heading': 'Every experiment, as its files record it',
  'results.intro.note': 'Read from results/ every time this page opens. Nothing here is recomputed.',
  'results.footer.index': '03 — RESULTS',
  'results.loading': 'Reading the result files…',
  'results.error.fetch': 'Could not read the results ({status}).',
  'results.built.line': 'Read from commit {head} · Python {python} · plant {plant}',
  'results.built.git_unavailable': 'git is not available here, so the commit facts are left out.',
  'results.built.restart': 'The plant files changed after the server started: restart the server.',
  'results.built.derived_restart': 'The derived constants changed after the server started: restart the server.',
  'results.import_failure': 'Could not load {module} ({type}). Every section that needs it says so.',
  'results.summary.heading': 'Summary',
  'results.summary.note': 'Each row is a separate experiment, on its own plant and road; the rows are not to be counted together.',
  'results.summary.col.experiment': 'Experiment',
  'results.summary.col.plant': 'Plant',
  'results.summary.col.verdict': 'Verdict',
  'results.summary.no_verdict': 'No verdict recorded for this experiment',
  'results.summary.continues': "Continues {other}'s agents, on the same episodes",
  'results.section.no_name': '{prefix} (no name recorded)',
  'results.section.meta': '{episodes} frozen episodes · frozen {frozen} · protocol {protocol}',
  'results.section.unavailable.missing': 'Not available: {file} is missing. The command that makes it: {command}',
  'results.section.unavailable.read': 'Could not read {file}: {type}',
  'results.section.unavailable.module': 'Needs {module}, which could not be loaded.',
  'results.section.unavailable.build': 'Could not build this section: {type}',
  'results.plant.label': 'Plant',
  'results.plant.forced': 'Agents scored with a plant mismatch forced',
  'results.plant.not_recorded': 'Plant not recorded in this file',
  'results.plant.another': 'Made on another plant',
  'results.plant.cannot_compare': 'Cannot compare',
  'results.plant.same_code': 'Same plant code as this tree; derived constants not recorded',
  'results.plant.same': 'Same plant as this tree',
  'results.plant.mixed': 'The files of this experiment do not agree; per seed below',
  'results.plant.hashes': 'recorded {recorded} · this tree {live}',
  'results.plant.tag': 'the plant of {tag}',
  'results.plant.route_git': 'compared through git: recorded under another Python',
  'results.plant.reason.python': 'recorded under Python {recorded}; this server runs {live}, and git cannot reach the recorded commit',
  'results.plant.reason.no_git_route': "the recorded commit's plant files are not the ones that were hashed",
  'results.plant.reason.dirty': 'the plant files had uncommitted changes when it ran',
  'results.plant.reason.one_sided': 'a fingerprint field exists on one side only',
  'results.plant.reason.restart': 'the plant files changed after the server started; restart the server',
  'results.plant.reason.protocol': 'the protocol of this file is not known here',
  'results.plant.reason.import': 'the live fingerprint could not be built',
  'results.plant.reason.derived_differs': 'the derived constants differ',
  'results.plant.commits': 'from commits {list}',
  'results.plant.committed': 'last commit {commit} ({date})',
  'results.plant.changed': 'changed since its last commit ({date})',
  'results.plant.forced_lines': "The file's own lines:",
  'results.check.parse_equals_analysis.pass': "The medians read here equal analyse_phase_d.parse's.",
  'results.check.parse_equals_analysis.fail': "The medians read here differ from analyse_phase_d.parse's: {detail}",
  'results.check.parse_equals_analysis.not_compared': 'Not compared with analyse_phase_d.parse.',
  'results.verdict.heading': 'The preregistered verdict',
  'results.verdict.none': 'No verdict recorded for this experiment',
  'results.verdict.unavailable': 'The verdict could not be read here.',
  'results.verdict.lines': 'The text as written, with its file and line',
  'results.notes.heading': 'Not to be read without',
  'results.note.blind_not_blind': 'The blind agent was not fully blind: the climb came at the same second in every episode, so its thermal state could serve as a clock (results/PREREGISTRATION.md, limit 7).',
  'results.note.budget_c1': 'Trained for 50 000 steps, the C1 budget. The preregistration records it; these files do not.',
  'results.note.budget_from_file': "Trained for {steps} steps, as these files' model lines record.",
  'results.note.spark_bound_jad': 'Every agent pushes its spark trim to the +4° action bound (measured). The margin over current-grade with spark advance forbidden was measured for C4 on one episode, and not for Phase D or D2 (SESSION_REPORT_2026-09-30_merge.md).',
  'results.note.spike_unmeasured': "Every episode holds a one-step knock spike at the grade step; whether it moved this experiment's result was never measured (conflict.md).",
  'results.note.dt_mismatch': "Trained at a {train_dt} s step and scored at {eval_dt} s, as these files' note lines record.",
  'results.note.no_thermal_only': 'Damage without the knock term was not recorded in these files, so how much of each difference is the knock term is unknown.',
  'results.note.knock_model': 'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C).',
  'results.note.turbine_modelled': "Turbine temperatures are modelled, not measured: no sensor on this car reads them, and the housing's heat capacity, c_turb, is assumed; it sets τ.",
  'results.note.no_other_notes': 'No other notes recorded for this experiment.',
  'results.chart.pairs.title': 'The pairs, seed by seed',
  'results.chart.pairs.what': "Each seed has two marks, the sighted agent and the blind one, joined by a line. The dashed line is current-grade's median.",
  'results.chart.pairs_thermal.title': 'The pairs, without the knock term',
  'results.chart.thermal_none': 'Damage without the knock term: not recorded in these files.',
  'results.chart.thermal_some': 'Without the knock term only for seeds {seeds}; the others did not record it.',
  'results.chart.hand.title': 'Against the hand-written policies',
  'results.chart.hand.what': "Each agent's median damage beside the three hand-written policies, from the same file.",
  'results.chart.axis.seed': 'Seed',
  'results.chart.axis.damage': 'Median damage over the frozen episodes (damage units)',
  'results.chart.axis.damage_thermal': 'Median damage without the knock term (damage units)',
  'results.chart.mei': 'The bracket is the minimum effect of interest, {mei} damage units.',
  'results.chart.mei_after': 'It was set on 22 September, after this result.',
  'results.chart.unavailable': 'This figure could not be drawn.',
  'results.chart.aria.pairs': 'The pairs of {name}',
  'results.chart.aria.hand': '{name} against the hand-written policies',
  'results.legend.sighted': 'Sighted agent',
  'results.legend.blind': 'Blind agent',
  'results.legend.baseline': 'Engine computer (modelled)',
  'results.legend.reactive': 'Reactive',
  'results.legend.current_grade': 'Current-grade',
  'results.tip.seed': 'Seed {seed}',
  'results.tip.median': 'median',
  'results.tip.worst': 'worst episode',
  'results.tip.fuel': 'median fuel (g)',
  'results.tip.peak': 'hottest turbine (°C, modelled)',
  'results.tip.diff': `blind ${MINUS} sighted`,
  'results.table.toggle': 'The numbers',
  'results.table.seed': 'Seed',
  'results.table.sighted': 'Sighted median',
  'results.table.blind': 'Blind median',
  'results.table.diff': `Blind ${MINUS} sighted`,
  'results.table.sighted_worst': 'Sighted worst',
  'results.table.blind_worst': 'Blind worst',
  'results.table.current_grade': 'Current-grade median',
  'results.table.baseline': 'Engine computer median',
  'results.table.reactive': 'Reactive median',
  'results.unpaired': 'Seed {seed} has no pair ({have}); it is not drawn.',
  'results.not_read.heading': 'Files not read',
  'results.not_read.reason.name': 'the name is not <prefix>_seed<N>.txt',
  'results.not_read.reason.header': 'the first line is not an evaluate.py header',
  'results.not_read.reason.no_fingerprint': 'no plant fingerprint block',
  'results.not_read.reason.no_table': 'no policy table',
  'results.not_read.reason.duplicate_role': 'more than one agent per arm',
  'results.not_read.reason.unreadable': 'could not be read ({type})',
  'results.markers.continues': 'continues',
};

// Every string this task adds, both languages: the tab's own and nav.results.
const added = lang => [...Object.entries(api().RESULTS_STRINGS[lang]), ['nav.results', STRINGS[lang]['nav.results']]];

test('i18n.mjs carries nav.results in both languages, right after nav.agents', () => {
  assert.equal(before.ar['nav.results'], 'النتائج');
  assert.equal(before.en['nav.results'], 'Results');
  for (const lang of LANGS) {
    const keys = Object.keys(before[lang]);
    assert.equal(keys.indexOf('nav.results'), keys.indexOf('nav.agents') + 1, `${lang}: nav.results is not right after nav.agents`);
    assert.equal(keys.indexOf('nav.agents'), keys.indexOf('nav.review') + 1, `${lang}: nav.agents moved from after nav.review`);
  }
});

test('every key of the contract is present, with the contract\'s English', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, en] of Object.entries(CONTRACT)) {
    assert.equal(RESULTS_STRINGS.en[key], en, `en ${key} is not the contract's text`);
    assert.equal(typeof RESULTS_STRINGS.ar[key], 'string', `ar ${key} is missing`);
  }
});

test('both languages carry the same keys, every one namespaced results.', () => {
  const { RESULTS_STRINGS } = api();
  assert.deepEqual(Object.keys(RESULTS_STRINGS).sort(), [...LANGS].sort());
  assert.deepEqual(Object.keys(RESULTS_STRINGS.ar).sort(), Object.keys(RESULTS_STRINGS.en).sort());
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(RESULTS_STRINGS[lang])) {
      assert.ok(key.startsWith('results.'), `${key} is not namespaced results.`);
      assert.equal(typeof text, 'string', `${lang} ${key}`);
      assert.ok(text.length > 0 && text === text.trim(), `${lang} ${key} is empty or padded`);
    }
  }
});

test('the merge adds the tab\'s strings and leaves every lab string as it was', () => {
  const { RESULTS_STRINGS } = api();
  for (const lang of LANGS) {
    for (const [key, text] of Object.entries(before[lang])) assert.equal(STRINGS[lang][key], text, `${lang} ${key} changed`);
    for (const key of Object.keys(RESULTS_STRINGS[lang])) {
      assert.ok(!Object.prototype.hasOwnProperty.call(before[lang], key), `${key} already existed in the lab's ${lang}`);
      assert.equal(STRINGS[lang][key], RESULTS_STRINGS[lang][key]);
    }
    assert.equal(Object.keys(STRINGS[lang]).length,
      Object.keys(before[lang]).length + Object.keys(RESULTS_STRINGS[lang]).length);
  }
  assert.deepEqual(missingKeys(), []);
});

test('mergeInto refuses a collision, a one-language key and an unknown language, and changes nothing', () => {
  const { mergeInto } = api();
  const target = { ar: { a: 'أ' }, en: { a: 'A' } };
  const copy = structuredClone(target);
  assert.throws(() => mergeInto(target, { ar: { a: 'ب', b: 'ب' }, en: { a: 'B', b: 'B' } }), /collides/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب', c: 'ج' }, en: { b: 'B' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب' } }), /missing from en/);
  assert.deepEqual(target, copy);
  assert.throws(() => mergeInto(target, { ar: { b: 'ب' }, en: { b: 'B' }, fr: { b: 'B' } }), /unknown language/);
  assert.deepEqual(target, copy);
  assert.equal(mergeInto(target, { ar: { b: 'ب' }, en: { b: 'B' } }), 1);
  assert.deepEqual(target, { ar: { a: 'أ', b: 'ب' }, en: { a: 'A', b: 'B' } });
});

test('every key fills the same {placeholders} in both languages', () => {
  const { RESULTS_STRINGS } = api();
  const slots = text => [...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]).sort();
  for (const key of Object.keys(RESULTS_STRINGS.en)) {
    assert.deepEqual(slots(RESULTS_STRINGS.ar[key]), slots(RESULTS_STRINGS.en[key]), key);
  }
});

// Spec 5.5 and contract section 0, in both languages: an English phrase is
// caught in an Arabic line too. The Arabic is compared without its vowel marks.
const FORBIDDEN_EN = [
  /preview\s+(?:helps|does\s+not\s+help|doesn't\s+help|did\s+not\s+help|cannot\s+help|is\s+useless)/i,
  /adds nothing measurable/i, /not from seeing ahead/i, /learning to protect/i, /replicat/i, /pooled/i,
];
const FORBIDDEN_AR = ['الاستباق يساعد', 'يساعد الاستباق', 'الاستباق لا يفيد', 'لا يفيد الاستباق',
  'الاستباق لا يساعد', 'المعاينة لا تفيد', 'المعاينة'];
test('no line says preview helps or does not help, nor any phrase the project retired', () => {
  for (const lang of LANGS) {
    for (const [key, text] of added(lang)) {
      for (const re of FORBIDDEN_EN) assert.doesNotMatch(text, re, `${lang} ${key}`);
      for (const phrase of FORBIDDEN_AR) assert.ok(!bare(text).includes(phrase), `${lang} ${key} says «${phrase}»`);
    }
  }
});

// current-grade and its Arabic name «الميل الحالي» are exempt; nothing else may
// call a file or a result current, stale, outdated, fresh or up to date.
const BANNED_EN = [/\bcurrent/i, /\bstale\b/i, /\boutdated\b/i, /\bfresh/i, /\bup[\s-]+to[\s-]+date\b/i];
const BANNED_AR = ['حديث', 'قديم', 'محدث', 'حالي'];
test('none of the banned words, in either language, current-grade exempt', () => {
  for (const lang of LANGS) {
    for (const [key, text] of added(lang)) {
      const en = text.replace(/current-grade/gi, '');
      for (const re of BANNED_EN) assert.doesNotMatch(en, re, `${lang} ${key}`);
      const ar = bare(text).replace(/الميل الحالي/g, '');
      for (const word of BANNED_AR) assert.ok(!ar.includes(word), `${lang} ${key} uses «${word}»`);
    }
  }
});

test('the engine computer is always «حاسوب المحرك المنمذَج», the modelled one', () => {
  const { RESULTS_STRINGS } = api();
  const NAME = 'حاسوب المحرك';
  const FULL = 'حاسوب المحرك المنمذَج';
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    assert.equal(text.split(NAME).length, text.split(FULL).length, `ar ${key} names the engine computer without «المنمذَج»`);
    assert.ok(!text.includes('ECU') && !text.includes('وحدة التحكم'), `ar ${key} names the engine computer another way`);
  }
  assert.equal(RESULTS_STRINGS.ar['results.legend.baseline'], FULL);
  assert.ok(RESULTS_STRINGS.ar['results.table.baseline'].includes(FULL));
  assert.match(RESULTS_STRINGS.en['results.legend.baseline'], /\(modelled\)/);
});

test('current-grade stays Latin in Arabic, inside a left-to-right isolate', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, en] of Object.entries(RESULTS_STRINGS.en)) {
    if (/current-grade/i.test(en)) {
      assert.ok(RESULTS_STRINGS.ar[key].includes(iso('current-grade')), `ar ${key}: current-grade is not isolated`);
    }
  }
  assert.equal(RESULTS_STRINGS.ar['results.legend.current_grade'], `سياسة ${iso('current-grade')}`);
});

test('the knock is «الطَّرْق» with its marks, so it cannot be read as «الطرق», the roads', () => {
  const { RESULTS_STRINGS } = api();
  const forms = ['الطَّرْق', 'طَرْق'].map(nfc);
  for (const [key, en] of Object.entries(RESULTS_STRINGS.en)) {
    const ar = RESULTS_STRINGS.ar[key];
    assert.ok(!ar.includes('طرق'), `ar ${key}: an unmarked «طرق» reads as roads`);
    if (/knock/i.test(en)) assert.ok(forms.some(f => nfc(ar).includes(f)), `ar ${key} does not name the knock`);
  }
});

// The two lines that stay Latin in both languages, outside any isolate: the
// window title (as the lab's and /agents' titles are) and the footer index,
// which sits in a dir="ltr" span.
const LATIN_OK = new Set(['results.page.title', 'results.footer.index']);
const ISOLATE_RUN = new RegExp(`${LRI}[^${LRI}${FSI}${PDI}]*${PDI}`, 'g');
test('in Arabic every Latin letter and digit sits inside an isolate; English lines carry none', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    const outside = text.replace(ISOLATE_RUN, '');
    for (const c of [LRI, FSI, PDI]) assert.ok(!outside.includes(c), `ar ${key}: an isolate is not closed, or is nested`);
    if (LATIN_OK.has(key)) continue;
    assert.doesNotMatch(outside.replace(/\{\w+\}/g, ''), /[A-Za-z0-9]/, `ar ${key}: Latin or a digit outside an isolate`);
    assert.match(text, ARABIC_LETTER, `ar ${key} has no Arabic letter: is it translated?`);
  }
  for (const [key, text] of Object.entries(RESULTS_STRINGS.en)) {
    for (const c of [LRI, FSI, PDI, RLM]) assert.ok(!text.includes(c), `en ${key}: an English line needs no isolate`);
  }
});

// A slot that always holds ONE number, hash, commit, date, path, module or
// protocol is isolated by the Arabic line itself, so it keeps its order
// whatever the caller passes. A slot that may hold Arabic words or a list
// stays bare, and the caller isolates each Latin item in it (contract 4.5).
const ISOLATED_SLOTS = new Set(['command', 'commit', 'date', 'detail', 'episodes', 'eval_dt', 'file', 'frozen',
  'head', 'live', 'mei', 'module', 'plant', 'prefix', 'protocol', 'python', 'recorded', 'seed', 'status',
  'steps', 'tag', 'train_dt', 'type']);
const BARE_SLOTS = new Set(['have', 'list', 'name', 'other', 'seeds']);
const slotDepths = text => {
  const out = [];
  let depth = 0;
  for (let i = 0; i < text.length; i += 1) {
    const c = text[i];
    if (c === LRI || c === FSI) depth += 1;
    else if (c === PDI) depth -= 1;
    else if (c === '{') {
      const m = /^\{(\w+)\}/.exec(text.slice(i));
      if (m) out.push({ slot: m[1], isolated: depth > 0 });
    }
  }
  return out;
};
test('in Arabic a slot holding one number, hash or path is isolated; a list or a name is not', () => {
  const { RESULTS_STRINGS } = api();
  for (const [key, text] of Object.entries(RESULTS_STRINGS.ar)) {
    for (const { slot, isolated } of slotDepths(text)) {
      assert.ok(ISOLATED_SLOTS.has(slot) || BARE_SLOTS.has(slot), `ar ${key}: {${slot}} is in neither list; classify it`);
      assert.equal(isolated, ISOLATED_SLOTS.has(slot), `ar ${key}: {${slot}} ${isolated ? 'must not be' : 'must be'} isolated`);
    }
  }
});

test('the notes keep their clauses in Arabic, and their literal numbers are isolated', () => {
  const { RESULTS_STRINGS } = api();
  const AR = RESULTS_STRINGS.ar;
  const mustSay = {
    'results.note.blind_not_blind': ['لم يكن الوكيل الأعمى أعمى تماماً', 'الثانية نفسها في كل حلقة', 'كساعة', iso('results/PREREGISTRATION.md'), iso('7')],
    'results.note.budget_c1': [iso(`50${NNBSP}000`), iso('C1'), 'التسجيل المسبق', 'لا تذكرها هذه الملفات'],
    'results.note.budget_from_file': [iso('{steps}'), 'أسطر النموذج'],
    'results.note.spark_bound_jad': [iso('+4°'), 'تعديل توقيت الشرارة', 'منع تبكير الشرارة', iso('C4'), 'على حلقة واحدة',
      'ولم يُقَس', iso('Phase D'), iso('D2'), iso('SESSION_REPORT_2026-09-30_merge.md')],
    'results.note.spike_unmeasured': ['قفزة طَرْق', 'خطوة واحدة', 'لم يُقَس قطّ', iso('conflict.md')],
    'results.note.dt_mismatch': [iso('{train_dt}'), iso('{eval_dt}'), 'أسطر الملاحظات'],
    'results.note.no_thermal_only': ['لم تسجّل هذه الملفات', 'لا يُعرف'],
    'results.note.knock_model': [iso('current-grade'), 'نموذج الطَّرْق', 'لم يُختبر على السيارة', iso('C')],
    'results.note.turbine_modelled': ['منمذَجة لا مقيسة', 'لا حساس', iso('c_turb'), 'مفترَضة', iso('τ')],
    'results.summary.note': ['تجربة مستقلة', 'لا تُدمج الصفوف في نتيجة واحدة'],
    'results.intro.note': [iso('results/'), 'لا يُعاد هنا حساب أي شيء'],
    'results.chart.mei': [iso('{mei}'), 'الحد الأدنى المهم', 'وحدة ضرر'],
    'results.chart.mei_after': [iso('22'), 'بعد هذه النتيجة'],
    'results.plant.same_code': ['الثوابت المشتقة غير'],
    'results.tip.peak': ['منمذَجة'],
  };
  for (const [key, phrases] of Object.entries(mustSay)) {
    for (const phrase of phrases) assert.ok(nfc(AR[key]).includes(nfc(phrase)), `ar ${key} lost «${phrase}»`);
  }
  for (const lang of LANGS) {
    for (const key of ['results.tip.diff', 'results.table.diff']) {
      assert.ok(RESULTS_STRINGS[lang][key].includes(MINUS), `${lang} ${key}: subtract with U+2212`);
      assert.ok(!RESULTS_STRINGS[lang][key].includes(' - '), `${lang} ${key}: an ASCII hyphen is not a minus sign`);
    }
  }
});

test('the footer index is the same in both languages, and the title follows the lab\'s pattern', () => {
  const { RESULTS_STRINGS } = api();
  assert.equal(RESULTS_STRINGS.ar['results.footer.index'], '03 — RESULTS');
  assert.equal(RESULTS_STRINGS.en['results.footer.index'], RESULTS_STRINGS.ar['results.footer.index']);
  assert.equal(RESULTS_STRINGS.ar['results.page.title'], 'النتائج — GRAD');
});

test('t() fills a results line in both languages, leaving no placeholder', () => {
  api();
  for (const lang of LANGS) {
    const line = t(lang, 'results.built.line', { head: 'abc1234', python: '3.12.10', plant: 'f00dbabe' });
    for (const value of ['abc1234', '3.12.10', 'f00dbabe']) assert.ok(line.includes(value), `${lang}: ${line}`);
    assert.doesNotMatch(line, /\{\w+\}/, `${lang}: an unfilled placeholder in ${line}`);
  }
  assert.equal(t('en', 'results.unpaired', { seed: 3, have: 'sighted' }), 'Seed 3 has no pair (sighted); it is not drawn.');
  assert.equal(t('ar', 'results.tip.seed', { seed: 3 }), `بذرة ${iso('3')}`);
});

test('results-strings.mjs carries its invisible characters as escapes, never literally', () => {
  const src = readFileSync(new URL('./results-strings.mjs', import.meta.url), 'utf8');
  for (const code of INVISIBLE) {
    assert.equal(src.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in results-strings.mjs: write the escape`);
  }
  const count = hex => src.split(escapeText(hex)).length - 1;
  assert.ok(count('2066') > 0, 'the Arabic lines isolate their Latin runs');
  assert.equal(count('2066'), count('2069'), 'every isolate opened in the source is closed');
  assert.equal(count('2212'), 4, 'U+2212: blind minus sighted, in the tooltip and the table, in both languages');
  assert.equal(count('202f'), 1, 'U+202F: the Arabic 50 000 of results.note.budget_c1');
  assert.match(src, /^import \{ STRINGS \} from '\.\/i18n\.mjs';$/m, 'the lab table comes from i18n.mjs, unversioned');
});

test('this file builds its characters from code points, never from a typed escape', () => {
  const own = readFileSync(new URL(import.meta.url), 'utf8');
  for (const code of INVISIBLE) assert.equal(own.split(cp(code)).length - 1, 0, `a literal U+${code.toString(16)} in this test file`);
  assert.equal(own.split(escapeText('')).length - 1, 0, 'a typed backslash-u escape in this test file');
});

// The tab imports results-strings.mjs with ONE version query everywhere
// (contract section 4), so the browser keeps one copy. A second copy (another
// query, or none) must fail loudly, and must not touch the table. The second
// address is built at run time, so no import in this file's text carries a
// query other than the tab's own.
test('a second copy of the module refuses to merge again, and changes nothing', async () => {
  api();
  const snapshot = structuredClone(STRINGS);
  const second = new URL('./results-strings.mjs', import.meta.url);
  second.searchParams.set('v', 'second-copy');
  await assert.rejects(import(second.href), /collides/);
  assert.deepEqual(STRINGS, snapshot);
});
```

- [ ] **Step 6: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-strings.test.mjs
```

Expected: FAIL, 18 of 19. The nav test fails on its first assertion (`undefined` where `'النتائج'` is expected), every test that needs the module fails with `results-strings.mjs must load: Cannot find module '…results-strings.mjs'`, and only the file's check of its own source passes:

```
✖ i18n.mjs carries nav.results in both languages, right after nav.agents
✖ every key of the contract is present, with the contract's English
✖ both languages carry the same keys, every one namespaced results.
✖ the merge adds the tab's strings and leaves every lab string as it was
✖ mergeInto refuses a collision, a one-language key and an unknown language, and changes nothing
✖ every key fills the same {placeholders} in both languages
✖ no line says preview helps or does not help, nor any phrase the project retired
✖ none of the banned words, in either language, current-grade exempt
✖ the engine computer is always «حاسوب المحرك المنمذَج», the modelled one
✖ current-grade stays Latin in Arabic, inside a left-to-right isolate
✖ the knock is «الطَّرْق» with its marks, so it cannot be read as «الطرق», the roads
✖ in Arabic every Latin letter and digit sits inside an isolate; English lines carry none
✖ in Arabic a slot holding one number, hash or path is isolated; a list or a name is not
✖ the notes keep their clauses in Arabic, and their literal numbers are isolated
✖ the footer index is the same in both languages, and the title follows the lab's pattern
✖ t() fills a results line in both languages, leaving no placeholder
✖ results-strings.mjs carries its invisible characters as escapes, never literally
✔ this file builds its characters from code points, never from a typed escape
✖ a second copy of the module refuses to merge again, and changes nothing
ℹ tests 19
ℹ suites 0
ℹ pass 1
ℹ fail 18
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms …
```

- [ ] **Step 7: Add `nav.results` to `i18n.mjs`, right after `nav.agents` in both languages**

The script inserts one line after each `nav.agents` line and keeps the file's own line ending (the working tree checks out CRLF, `core.autocrlf=true`); it refuses to run twice.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
"$PY" - <<'PYEOF'
from pathlib import Path

# Adds one line after nav.agents in each language and keeps the file's own
# line ending (the working tree checks out CRLF; core.autocrlf=true).
path = Path("app/static/sim/i18n.mjs")
src = path.read_bytes().decode("utf-8")
nl = chr(13) + chr(10) if chr(13) + chr(10) in src else chr(10)
for old, new in (("    'nav.agents': 'الوكلاء',", "    'nav.results': 'النتائج',"),
                 ("    'nav.agents': 'Agents',", "    'nav.results': 'Results',")):
    assert src.count(old + nl) == 1, f"expected exactly one line {old!r}"
    assert new not in src, f"already there: {new!r}"
    src = src.replace(old + nl, old + nl + new + nl)
path.write_bytes(src.encode("utf-8"))
print(path.as_posix(), "now carries nav.results in both languages")
PYEOF
git diff --stat app/static/sim/i18n.mjs
git diff app/static/sim/i18n.mjs | grep "^[-+] "
```

Expected:

```
app/static/sim/i18n.mjs now carries nav.results in both languages
 app/static/sim/i18n.mjs | 2 ++
 1 file changed, 2 insertions(+)
+    'nav.results': 'النتائج',
+    'nav.results': 'Results',
```

- [ ] **Step 8: Write `results-strings.mjs` through Python, then byte-check it**

Create `C:/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad/r1a_task6_strings.py` with the Write tool, with exactly this content (the session scratchpad, never the repository; each `<U+XXXX>` is a marker the script turns into an escape):

```python
import re
from pathlib import Path

# Writes app/static/sim/results-strings.mjs; run from the repository root.
# The source of app/static/sim/results-strings.mjs. Each <U+XXXX> marker
# becomes the escape TEXT backslash-u-xxxx, built from chr(92) below, so no
# tool on the way can turn it into the literal character. <U+2066> ... <U+2069>
# is a left-to-right isolate, <U+202F> the narrow no-break space that groups
# thousands, <U+2212> the minus sign.
SRC = r"""
// Every string the results tab (/results) shows, in Arabic and English.
//
// The lab's i18n.mjs owns t(), applyTranslations() and STRINGS; this file only
// ADDS to STRINGS, once, at import, and refuses to overwrite anything. Its
// merge, mergeInto, keeps the rules of agents-strings.mjs mergeStrings but is
// its own copy: importing agents-strings.mjs would add every /agents string to
// this page. The same three rules as i18n.mjs apply (read its header): both
// languages carry the same keys, numbers go through {placeholders}, and the
// honesty notes are load-bearing text, not copy.
//
// The English lines are the R1a contract's (section 5), word for word; the
// Arabic lines say the same. Rules of this page, pinned by
// results-strings.test.mjs:
//  - no line says that preview helps or that it does not; where a line ever
//    names preview in Arabic, it is «الاستباق», the app's word for it;
//  - the engine computer is always «حاسوب المحرك المنمذَج», the MODELLED one;
//  - "current-grade" stays Latin in Arabic, inside a left-to-right isolate;
//  - none of the words current, stale, outdated, fresh or up to date, nor their
//    Arabic forms, is used: a file's facts are dated, never called recent;
//  - the knock is written with its vowel marks, so it cannot be read as roads;
//  - in an Arabic line every Latin word and every digit is a left-to-right
//    isolate, U+2066 ... U+2069, and so is a {placeholder} that always holds
//    ONE number, hash, commit, date, path, module or protocol. A placeholder
//    that may hold Arabic words or a list ({name}, {other}, {have}, {list},
//    {seeds}) stays bare: the caller isolates each Latin item in it;
//  - thousands take U+202F and a subtraction U+2212.
// The invisible characters are escapes, never the characters: the Write tool
// on this machine decodes a typed escape, so this file is written by a Python
// script and byte-checked.
import { STRINGS } from './i18n.mjs';

export const RESULTS_STRINGS = {
  ar: {
    // --- page, intro, footer and loading
    'results.page.title': 'النتائج — GRAD',
    'results.intro.heading': 'كل تجربة، كما تسجّلها ملفاتها',
    'results.intro.note': 'يُقرأ كل ما هنا من <U+2066>results/<U+2069> في كل مرة تُفتح فيها هذه الصفحة. لا يُعاد هنا حساب أي شيء.',
    'results.footer.index': '03 — RESULTS',
    'results.loading': 'جارٍ قراءة ملفات النتائج…',
    'results.error.fetch': 'تعذّرت قراءة النتائج (<U+2066>{status}<U+2069>).',

    // --- the build line and the tab-level warnings
    'results.built.line': 'قُرئت من <U+2066>commit {head}<U+2069> · <U+2066>Python {python}<U+2069> · المحاكي <U+2066>{plant}<U+2069>',
    'results.built.git_unavailable': 'لا يتوفر <U+2066>git<U+2069> هنا، فلا تُعرض معلومات الـ <U+2066>commits<U+2069>.',
    'results.built.restart': 'تغيّرت ملفات المحاكي بعد أن بدأ الخادم: أعد تشغيل الخادم.',
    'results.built.derived_restart': 'تغيّرت الثوابت المشتقة بعد أن بدأ الخادم: أعد تشغيل الخادم.',
    'results.import_failure': 'تعذّر تحميل <U+2066>{module}<U+2069> (<U+2066>{type}<U+2069>). كل قسم يحتاج إليه يذكر ذلك.',

    // --- the summary
    'results.summary.heading': 'الملخّص',
    'results.summary.note': 'كل صف تجربة مستقلة، لها محاكيها وطريقها؛ ولا تُدمج الصفوف في نتيجة واحدة.',
    'results.summary.col.experiment': 'التجربة',
    'results.summary.col.plant': 'المحاكي',
    'results.summary.col.verdict': 'الحكم',
    'results.summary.no_verdict': 'لا حكم مسجَّل لهذه التجربة',
    'results.summary.continues': 'تُكمل وكلاء {other}، على الحلقات نفسها',

    // --- a section's head, and a section that cannot be built
    'results.section.no_name': '<U+2066>{prefix}<U+2069> (لا اسم مسجَّل)',
    'results.section.meta': '<U+2066>{episodes}<U+2069> حلقة مجمّدة · جُمّدت في <U+2066>{frozen}<U+2069> · البروتوكول <U+2066>{protocol}<U+2069>',
    'results.section.unavailable.missing': 'غير متاح: الملف <U+2066>{file}<U+2069> غير موجود. الأمر الذي ينشئه: <U+2066>{command}<U+2069>',
    'results.section.unavailable.read': 'تعذّرت قراءة <U+2066>{file}<U+2069>: <U+2066>{type}<U+2069>',
    'results.section.unavailable.module': 'يحتاج إلى <U+2066>{module}<U+2069>، وتعذّر تحميله.',
    'results.section.unavailable.build': 'تعذّر بناء هذا القسم: <U+2066>{type}<U+2069>',

    // --- where the numbers came from (spec 5.2)
    'results.plant.label': 'المحاكي',
    'results.plant.forced': 'قُيِّم الوكلاء رغم اختلاف المحاكي، بتجاوزٍ قسري',
    'results.plant.not_recorded': 'المحاكي غير مسجَّل في هذا الملف',
    'results.plant.another': 'أُجريت على محاكٍ آخر',
    'results.plant.cannot_compare': 'لا يمكن المقارنة',
    'results.plant.same_code': 'شيفرة المحاكي نفسها التي في هذه النسخة؛ الثوابت المشتقة غير مسجَّلة',
    'results.plant.same': 'المحاكي نفسه الذي في هذه النسخة',
    'results.plant.mixed': 'ملفات هذه التجربة لا تتفق؛ التفصيل لكل بذرة أدناه',
    'results.plant.hashes': 'المسجَّل <U+2066>{recorded}<U+2069> · هذه النسخة <U+2066>{live}<U+2069>',
    'results.plant.tag': 'محاكي <U+2066>{tag}<U+2069>',
    'results.plant.route_git': 'قورن عبر <U+2066>git<U+2069>: سُجِّل تحت إصدار آخر من <U+2066>Python<U+2069>',
    'results.plant.reason.python': 'سُجِّل تحت <U+2066>Python {recorded}<U+2069>؛ وهذا الخادم يعمل بالإصدار <U+2066>{live}<U+2069>، ولا يصل <U+2066>git<U+2069> إلى الـ <U+2066>commit<U+2069> المسجَّل',
    'results.plant.reason.no_git_route': 'ملفات المحاكي في الـ <U+2066>commit<U+2069> المسجَّل ليست هي التي حُسبت بصمتها',
    'results.plant.reason.dirty': 'كانت في ملفات المحاكي تغييرات خارج أي <U+2066>commit<U+2069> حين شُغّل التقييم',
    'results.plant.reason.one_sided': 'حقل من البصمة موجود في جهة واحدة فقط',
    'results.plant.reason.restart': 'تغيّرت ملفات المحاكي بعد أن بدأ الخادم؛ أعد تشغيل الخادم',
    'results.plant.reason.protocol': 'بروتوكول هذا الملف غير معروف هنا',
    'results.plant.reason.import': 'تعذّر حساب بصمة هذه النسخة',
    'results.plant.reason.derived_differs': 'الثوابت المشتقة مختلفة',
    'results.plant.commits': 'من الـ <U+2066>commits<U+2069> {list}',
    'results.plant.committed': 'آخر <U+2066>commit {commit}<U+2069> (<U+2066>{date}<U+2069>)',
    'results.plant.changed': 'تغيّر منذ آخر <U+2066>commit<U+2069> له (<U+2066>{date}<U+2069>)',
    'results.plant.forced_lines': 'أسطر الملف نفسه:',

    // --- the cross-check of spec 4.4
    'results.check.parse_equals_analysis.pass': 'الوسيطات المقروءة هنا تساوي ما يقرؤه <U+2066>analyse_phase_d.parse<U+2069>.',
    'results.check.parse_equals_analysis.fail': 'الوسيطات المقروءة هنا تختلف عمّا يقرؤه <U+2066>analyse_phase_d.parse<U+2069>: <U+2066>{detail}<U+2069>',
    'results.check.parse_equals_analysis.not_compared': 'لم تُقارَن بما يقرؤه <U+2066>analyse_phase_d.parse<U+2069>.',

    // --- the verdict block
    'results.verdict.heading': 'الحكم المسجَّل مسبقاً',
    'results.verdict.none': 'لا حكم مسجَّل لهذه التجربة',
    'results.verdict.unavailable': 'تعذّرت قراءة الحكم هنا.',
    'results.verdict.lines': 'النص كما كُتب، مع ملفه وسطره',

    // --- the required notes (spec 5.4)
    'results.notes.heading': 'لا تُقرأ النتيجة دون ما يلي',
    'results.note.blind_not_blind': 'لم يكن الوكيل الأعمى أعمى تماماً: جاء الصعود في الثانية نفسها في كل حلقة، فأمكن أن تعمل حالته الحرارية كساعة (<U+2066>results/PREREGISTRATION.md<U+2069>، القيد <U+2066>7<U+2069>).',
    'results.note.budget_c1': 'دُرِّب الوكلاء <U+2066>50<U+202F>000<U+2069> خطوة، وهي ميزانية <U+2066>C1<U+2069>. يذكرها التسجيل المسبق؛ ولا تذكرها هذه الملفات.',
    'results.note.budget_from_file': 'دُرِّب الوكلاء <U+2066>{steps}<U+2069> خطوة، كما تسجّله أسطر النموذج في هذه الملفات.',
    'results.note.spark_bound_jad': 'كل وكيل يدفع تعديل توقيت الشرارة إلى الحدّ الأعلى للإجراء، <U+2066>+4°<U+2069> (هذا مقيس). والهامش فوق <U+2066>current-grade<U+2069> مع منع تبكير الشرارة قِيس لـ <U+2066>C4<U+2069> على حلقة واحدة، ولم يُقَس لـ <U+2066>Phase D<U+2069> ولا لـ <U+2066>D2<U+2069> (<U+2066>SESSION_REPORT_2026-09-30_merge.md<U+2069>).',
    'results.note.spike_unmeasured': 'في كل حلقة قفزة طَرْق مدّتها خطوة واحدة عند تغيّر الميل المفاجئ؛ ولم يُقَس قطّ هل حرّكت نتيجة هذه التجربة (<U+2066>conflict.md<U+2069>).',
    'results.note.dt_mismatch': 'دُرِّب الوكلاء بخطوة زمنية <U+2066>{train_dt}<U+2069> ث وقُيِّموا بخطوة <U+2066>{eval_dt}<U+2069> ث، كما تسجّل أسطر الملاحظات في هذه الملفات.',
    'results.note.no_thermal_only': 'لم تسجّل هذه الملفات الضرر دون ضرر الطَّرْق، فلا يُعرف كم من كل فرق يعود إلى ضرر الطَّرْق.',
    'results.note.knock_model': 'الهامش فوق <U+2066>current-grade<U+2069> قائم على نموذج الطَّرْق، الذي لم يُختبر على السيارة (الرحلة <U+2066>C<U+2069>).',
    'results.note.turbine_modelled': 'درجات حرارة التيربو منمذَجة لا مقيسة: لا حساس في هذه السيارة يقرؤها، والسعة الحرارية لغلاف التيربو، <U+2066>c_turb<U+2069>، مفترَضة؛ وهي التي تحدّد <U+2066>τ<U+2069>.',
    'results.note.no_other_notes': 'لا ملاحظات أخرى مسجَّلة لهذه التجربة.',

    // --- the figures
    'results.chart.pairs.title': 'الأزواج، بذرةً بذرةً',
    'results.chart.pairs.what': 'لكل بذرة علامتان، الوكيل المُبصر والوكيل الأعمى، يصل بينهما خط. الخط المتقطّع هو وسيط <U+2066>current-grade<U+2069>.',
    'results.chart.pairs_thermal.title': 'الأزواج، دون ضرر الطَّرْق',
    'results.chart.thermal_none': 'الضرر دون ضرر الطَّرْق: غير مسجَّل في هذه الملفات.',
    'results.chart.thermal_some': 'دون ضرر الطَّرْق للبذور {seeds} فقط؛ البذور الأخرى لم تسجّله.',
    'results.chart.hand.title': 'مقابل السياسات المكتوبة يدوياً',
    'results.chart.hand.what': 'وسيط ضرر كل وكيل بجانب السياسات الثلاث المكتوبة يدوياً، من الملف نفسه.',
    'results.chart.axis.seed': 'البذرة',
    'results.chart.axis.damage': 'وسيط الضرر عبر الحلقات المجمّدة (وحدات ضرر)',
    'results.chart.axis.damage_thermal': 'وسيط الضرر دون ضرر الطَّرْق (وحدات ضرر)',
    'results.chart.mei': 'القوس المرسوم هو الحد الأدنى المهم للأثر، <U+2066>{mei}<U+2069> وحدة ضرر.',
    'results.chart.mei_after': 'حُدِّد في <U+2066>22<U+2069> سبتمبر، بعد هذه النتيجة.',
    'results.chart.unavailable': 'تعذّر رسم هذا الشكل.',
    'results.chart.aria.pairs': 'أزواج {name}',
    'results.chart.aria.hand': '{name} مقابل السياسات المكتوبة يدوياً',

    // --- legend, tooltip and table
    'results.legend.sighted': 'الوكيل المُبصر',
    'results.legend.blind': 'الوكيل الأعمى',
    'results.legend.baseline': 'حاسوب المحرك المنمذَج',
    'results.legend.reactive': 'السياسة التفاعلية',
    'results.legend.current_grade': 'سياسة <U+2066>current-grade<U+2069>',
    'results.tip.seed': 'بذرة <U+2066>{seed}<U+2069>',
    'results.tip.median': 'الوسيط',
    'results.tip.worst': 'أسوأ حلقة',
    'results.tip.fuel': 'وسيط الوقود (غرام)',
    'results.tip.peak': 'أعلى حرارة للتيربو (°م، منمذَجة)',
    'results.tip.diff': 'الأعمى <U+2212> المُبصر',
    'results.table.toggle': 'الأرقام',
    'results.table.seed': 'البذرة',
    'results.table.sighted': 'وسيط المُبصر',
    'results.table.blind': 'وسيط الأعمى',
    'results.table.diff': 'الأعمى <U+2212> المُبصر',
    'results.table.sighted_worst': 'أسوأ حلقة للمُبصر',
    'results.table.blind_worst': 'أسوأ حلقة للأعمى',
    'results.table.current_grade': 'وسيط <U+2066>current-grade<U+2069>',
    'results.table.baseline': 'وسيط حاسوب المحرك المنمذَج',
    'results.table.reactive': 'وسيط السياسة التفاعلية',
    'results.unpaired': 'البذرة <U+2066>{seed}<U+2069> بلا زوج ({have})؛ لم تُرسم.',

    // --- files not read, and the summary's marker
    'results.not_read.heading': 'ملفات لم تُقرأ',
    'results.not_read.reason.name': 'الاسم ليس على صيغة <U+2066><prefix>_seed<N>.txt<U+2069>',
    'results.not_read.reason.header': 'السطر الأول ليس ترويسة من <U+2066>evaluate.py<U+2069>',
    'results.not_read.reason.no_fingerprint': 'لا كتلة لبصمة المحاكي',
    'results.not_read.reason.no_table': 'لا جدول للسياسات',
    'results.not_read.reason.duplicate_role': 'أكثر من وكيل واحد للذراع الواحدة',
    'results.not_read.reason.unreadable': 'تعذّرت قراءته (<U+2066>{type}<U+2069>)',
    'results.markers.continues': 'تكملة',
  },

  en: {
    // --- page, intro, footer and loading
    'results.page.title': 'Results — GRAD',
    'results.intro.heading': 'Every experiment, as its files record it',
    'results.intro.note': 'Read from results/ every time this page opens. Nothing here is recomputed.',
    'results.footer.index': '03 — RESULTS',
    'results.loading': 'Reading the result files…',
    'results.error.fetch': 'Could not read the results ({status}).',

    // --- the build line and the tab-level warnings
    'results.built.line': 'Read from commit {head} · Python {python} · plant {plant}',
    'results.built.git_unavailable': 'git is not available here, so the commit facts are left out.',
    'results.built.restart': 'The plant files changed after the server started: restart the server.',
    'results.built.derived_restart': 'The derived constants changed after the server started: restart the server.',
    'results.import_failure': 'Could not load {module} ({type}). Every section that needs it says so.',

    // --- the summary
    'results.summary.heading': 'Summary',
    'results.summary.note': 'Each row is a separate experiment, on its own plant and road; the rows are not to be counted together.',
    'results.summary.col.experiment': 'Experiment',
    'results.summary.col.plant': 'Plant',
    'results.summary.col.verdict': 'Verdict',
    'results.summary.no_verdict': 'No verdict recorded for this experiment',
    'results.summary.continues': "Continues {other}'s agents, on the same episodes",

    // --- a section's head, and a section that cannot be built
    'results.section.no_name': '{prefix} (no name recorded)',
    'results.section.meta': '{episodes} frozen episodes · frozen {frozen} · protocol {protocol}',
    'results.section.unavailable.missing': 'Not available: {file} is missing. The command that makes it: {command}',
    'results.section.unavailable.read': 'Could not read {file}: {type}',
    'results.section.unavailable.module': 'Needs {module}, which could not be loaded.',
    'results.section.unavailable.build': 'Could not build this section: {type}',

    // --- where the numbers came from (spec 5.2)
    'results.plant.label': 'Plant',
    'results.plant.forced': 'Agents scored with a plant mismatch forced',
    'results.plant.not_recorded': 'Plant not recorded in this file',
    'results.plant.another': 'Made on another plant',
    'results.plant.cannot_compare': 'Cannot compare',
    'results.plant.same_code': 'Same plant code as this tree; derived constants not recorded',
    'results.plant.same': 'Same plant as this tree',
    'results.plant.mixed': 'The files of this experiment do not agree; per seed below',
    'results.plant.hashes': 'recorded {recorded} · this tree {live}',
    'results.plant.tag': 'the plant of {tag}',
    'results.plant.route_git': 'compared through git: recorded under another Python',
    'results.plant.reason.python': 'recorded under Python {recorded}; this server runs {live}, and git cannot reach the recorded commit',
    'results.plant.reason.no_git_route': "the recorded commit's plant files are not the ones that were hashed",
    'results.plant.reason.dirty': 'the plant files had uncommitted changes when it ran',
    'results.plant.reason.one_sided': 'a fingerprint field exists on one side only',
    'results.plant.reason.restart': 'the plant files changed after the server started; restart the server',
    'results.plant.reason.protocol': 'the protocol of this file is not known here',
    'results.plant.reason.import': 'the live fingerprint could not be built',
    'results.plant.reason.derived_differs': 'the derived constants differ',
    'results.plant.commits': 'from commits {list}',
    'results.plant.committed': 'last commit {commit} ({date})',
    'results.plant.changed': 'changed since its last commit ({date})',
    'results.plant.forced_lines': "The file's own lines:",

    // --- the cross-check of spec 4.4
    'results.check.parse_equals_analysis.pass': "The medians read here equal analyse_phase_d.parse's.",
    'results.check.parse_equals_analysis.fail': "The medians read here differ from analyse_phase_d.parse's: {detail}",
    'results.check.parse_equals_analysis.not_compared': 'Not compared with analyse_phase_d.parse.',

    // --- the verdict block
    'results.verdict.heading': 'The preregistered verdict',
    'results.verdict.none': 'No verdict recorded for this experiment',
    'results.verdict.unavailable': 'The verdict could not be read here.',
    'results.verdict.lines': 'The text as written, with its file and line',

    // --- the required notes (spec 5.4)
    'results.notes.heading': 'Not to be read without',
    'results.note.blind_not_blind': 'The blind agent was not fully blind: the climb came at the same second in every episode, so its thermal state could serve as a clock (results/PREREGISTRATION.md, limit 7).',
    'results.note.budget_c1': 'Trained for 50 000 steps, the C1 budget. The preregistration records it; these files do not.',
    'results.note.budget_from_file': "Trained for {steps} steps, as these files' model lines record.",
    'results.note.spark_bound_jad': 'Every agent pushes its spark trim to the +4° action bound (measured). The margin over current-grade with spark advance forbidden was measured for C4 on one episode, and not for Phase D or D2 (SESSION_REPORT_2026-09-30_merge.md).',
    'results.note.spike_unmeasured': "Every episode holds a one-step knock spike at the grade step; whether it moved this experiment's result was never measured (conflict.md).",
    'results.note.dt_mismatch': "Trained at a {train_dt} s step and scored at {eval_dt} s, as these files' note lines record.",
    'results.note.no_thermal_only': 'Damage without the knock term was not recorded in these files, so how much of each difference is the knock term is unknown.',
    'results.note.knock_model': 'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C).',
    'results.note.turbine_modelled': "Turbine temperatures are modelled, not measured: no sensor on this car reads them, and the housing's heat capacity, c_turb, is assumed; it sets τ.",
    'results.note.no_other_notes': 'No other notes recorded for this experiment.',

    // --- the figures
    'results.chart.pairs.title': 'The pairs, seed by seed',
    'results.chart.pairs.what': "Each seed has two marks, the sighted agent and the blind one, joined by a line. The dashed line is current-grade's median.",
    'results.chart.pairs_thermal.title': 'The pairs, without the knock term',
    'results.chart.thermal_none': 'Damage without the knock term: not recorded in these files.',
    'results.chart.thermal_some': 'Without the knock term only for seeds {seeds}; the others did not record it.',
    'results.chart.hand.title': 'Against the hand-written policies',
    'results.chart.hand.what': "Each agent's median damage beside the three hand-written policies, from the same file.",
    'results.chart.axis.seed': 'Seed',
    'results.chart.axis.damage': 'Median damage over the frozen episodes (damage units)',
    'results.chart.axis.damage_thermal': 'Median damage without the knock term (damage units)',
    'results.chart.mei': 'The bracket is the minimum effect of interest, {mei} damage units.',
    'results.chart.mei_after': 'It was set on 22 September, after this result.',
    'results.chart.unavailable': 'This figure could not be drawn.',
    'results.chart.aria.pairs': 'The pairs of {name}',
    'results.chart.aria.hand': '{name} against the hand-written policies',

    // --- legend, tooltip and table
    'results.legend.sighted': 'Sighted agent',
    'results.legend.blind': 'Blind agent',
    'results.legend.baseline': 'Engine computer (modelled)',
    'results.legend.reactive': 'Reactive',
    'results.legend.current_grade': 'Current-grade',
    'results.tip.seed': 'Seed {seed}',
    'results.tip.median': 'median',
    'results.tip.worst': 'worst episode',
    'results.tip.fuel': 'median fuel (g)',
    'results.tip.peak': 'hottest turbine (°C, modelled)',
    'results.tip.diff': 'blind <U+2212> sighted',
    'results.table.toggle': 'The numbers',
    'results.table.seed': 'Seed',
    'results.table.sighted': 'Sighted median',
    'results.table.blind': 'Blind median',
    'results.table.diff': 'Blind <U+2212> sighted',
    'results.table.sighted_worst': 'Sighted worst',
    'results.table.blind_worst': 'Blind worst',
    'results.table.current_grade': 'Current-grade median',
    'results.table.baseline': 'Engine computer median',
    'results.table.reactive': 'Reactive median',
    'results.unpaired': 'Seed {seed} has no pair ({have}); it is not drawn.',

    // --- files not read, and the summary's marker
    'results.not_read.heading': 'Files not read',
    'results.not_read.reason.name': 'the name is not <prefix>_seed<N>.txt',
    'results.not_read.reason.header': 'the first line is not an evaluate.py header',
    'results.not_read.reason.no_fingerprint': 'no plant fingerprint block',
    'results.not_read.reason.no_table': 'no policy table',
    'results.not_read.reason.duplicate_role': 'more than one agent per arm',
    'results.not_read.reason.unreadable': 'could not be read ({type})',
    'results.markers.continues': 'continues',
  },
};

/**
 * Add `extra` ({lang: {key: text}}) into `target` (i18n's STRINGS) and return
 * how many keys each language gained. Everything is checked BEFORE anything is
 * written, so a refused merge leaves `target` exactly as it was. It throws on:
 *  - a language `target` does not have;
 *  - a key present in one language of `extra` and missing from another (or a
 *    language of `target` that `extra` leaves out);
 *  - a key `target` already has: this tab may add strings, never change the
 *    lab's or another page's. A second copy of this module (an import with
 *    another ?v= query) therefore fails loudly instead of merging twice.
 */
export function mergeInto(target, extra) {
  const langs = Object.keys(target);
  for (const lang of Object.keys(extra)) {
    if (!langs.includes(lang)) throw new Error(`results strings: unknown language "${lang}"`);
  }
  const keys = new Set(Object.values(extra).flatMap(table => Object.keys(table)));
  for (const lang of langs) {
    const table = extra[lang] ?? {};
    for (const key of keys) {
      if (!Object.prototype.hasOwnProperty.call(table, key)) {
        const has = Object.keys(extra).filter(l => Object.prototype.hasOwnProperty.call(extra[l], key));
        throw new Error(`results strings: "${key}" is missing from ${lang} (present in ${has.join(', ')})`);
      }
      if (Object.prototype.hasOwnProperty.call(target[lang], key)) {
        throw new Error(`results strings: "${key}" collides with an existing ${lang} string`);
      }
    }
  }
  for (const lang of langs) Object.assign(target[lang], extra[lang]);
  return keys.size;
}

mergeInto(STRINGS, RESULTS_STRINGS);
""".lstrip()

out = re.sub(r"<U[+]([0-9A-F]{4})>", lambda m: chr(92) + "u" + m.group(1).lower(), SRC)
assert "<U+" not in out, "a marker was mistyped"
path = Path("app/static/sim/results-strings.mjs")
path.write_bytes(out.encode("utf-8"))
print(path.as_posix(), "written,", out.count(chr(92) + "u"), "escapes")
```

Then run it from the repository root and byte-check what it wrote:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SCRATCH="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
"$PY" "$SCRATCH/r1a_task6_strings.py"
"$PY" -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" app/static/sim/results-strings.mjs
"$PY" -c "import sys; s=open(sys.argv[1],encoding='utf-8').read(); print({h: s.count(chr(92) + 'u' + h) for h in ('2066', '2069', '2212', '202f')})" app/static/sim/results-strings.mjs
```

Expected, exactly: 67 isolates opened and closed (one pair per isolated Latin run or slot), 4 minus signs (`results.tip.diff` and `results.table.diff`, both languages) and 1 narrow no-break space (the Arabic `50 000` of `results.note.budget_c1`; the contract's English keeps its ASCII space):

```
app/static/sim/results-strings.mjs written, 139 escapes
literal invisible: []
{'2066': 67, '2069': 67, '2212': 4, '202f': 1}
```

Any other count means an escape was decoded or a marker mistyped: delete the file and re-run the block as it stands.

- [ ] **Step 9: Run the strings test, the formatter's, and `/agents`' strings test, and see them pass**

`agents-strings.test.mjs` is run too because it pins `nav.agents` right after `nav.review`, and that every lab string survives its own merge.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-format.test.mjs static/sim/results-strings.test.mjs static/sim/agents-strings.test.mjs
```

Expected (the last lines):

```
ℹ tests 43
ℹ suites 0
ℹ pass 43
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms …
```

- [ ] **Step 10: Run the whole node suite**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test "static/sim/*.test.mjs"
```

Expected: the 148 tests of the baseline plus this task's 8 + 19:

```
ℹ tests 175
ℹ suites 0
ℹ pass 175
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms …
```

Then the one Python test that reads `i18n.mjs` (it walks the agents page's static import graph through it; it is not in the baseline's failing list):

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
"$PY" -m unittest app.test_agents.PageTests.test_chase_is_optional -v
```

Expected (observed in drafting against a copy of `app/static` with this task applied):

```
test_chase_is_optional (app.test_agents.PageTests.test_chase_is_optional)
Three.js is loaded on demand, so its failure cannot blank the page. ... ok

----------------------------------------------------------------------
Ran 1 test in …s

OK
```

The other Python suites read no file this task changes; the last task of R1a runs them all.

- [ ] **Step 11: Commit by explicit path**

Another session is editing `CLAUDE.md`, `handoff.md`, `team/jad.md` and `NEXT_SESSION_*.md` in this same tree: stage and commit only this task's five paths.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SCRATCH="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
cat > "$SCRATCH/r1a_task6_msg.txt" <<'EOF'
Results tab R1a (task 6): number formatting, the tab's strings, nav.results

results-format.mjs writes every number the tab prints: U+2212 for a minus,
U+202F between thousands, an em dash for a missing value, and a left-to-right
isolate around a number inside Arabic; it rounds the magnitude with toFixed,
as formatDiff on /agents does. results-strings.mjs holds every results.* key
of the R1a contract, the English as the contract fixes it and the Arabic
authored beside it, and merges them into the lab's table once, refusing any
collision. i18n.mjs gains nav.results right after nav.agents.

Both modules carry their escapes as text, written by Python and
byte-checked; the tests pin the wording rules in both languages.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
T6="app/static/sim/i18n.mjs app/static/sim/results-format.mjs app/static/sim/results-format.test.mjs app/static/sim/results-strings.mjs app/static/sim/results-strings.test.mjs"
git status --short -- $T6
git add $T6
git commit -q -F "$SCRATCH/r1a_task6_msg.txt" -- $T6
git show --stat --format=%s HEAD
```

Expected: before the commit, `git status` lists exactly the five paths (`git add` may also warn that LF will be replaced by CRLF in the four new files; that is the repository's `core.autocrlf=true` and harmless); after it, one commit with exactly these five files:

```
 M app/static/sim/i18n.mjs
?? app/static/sim/results-format.mjs
?? app/static/sim/results-format.test.mjs
?? app/static/sim/results-strings.mjs
?? app/static/sim/results-strings.test.mjs
warning: in the working copy of 'app/static/sim/results-format.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-format.test.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-strings.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-strings.test.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-format.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-format.test.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-strings.mjs', LF will be replaced by CRLF the next time Git touches it
warning: in the working copy of 'app/static/sim/results-strings.test.mjs', LF will be replaced by CRLF the next time Git touches it
Results tab R1a (task 6): number formatting, the tab's strings, nav.results

 app/static/sim/i18n.mjs                 |   2 +
 app/static/sim/results-format.mjs       |  69 ++++++
 app/static/sim/results-format.test.mjs  | 108 ++++++++
 app/static/sim/results-strings.mjs      | 335 +++++++++++++++++++++++++
 app/static/sim/results-strings.test.mjs | 426 ++++++++++++++++++++++++++++++++
 5 files changed, 940 insertions(+)
```

### Task 7: The drawing library (charts-lib.mjs) and the tab's stylesheet (results.css)

The tab draws with a COPY of the generic drawing code of Ghassan's page,
`results/page/template.html` lines 747-978 plus `sideLabel` (992-996), adapted
as design section 7.3 says: every class prefixed `rc-`, no axis titles in SVG
(they are HTML, design 7.2), no `role="img"` around focusable marks, a measured
`sideLabel`, and the mounting code turned into a factory (`createMounter`) with
one ResizeObserver, one document `pointerdown` listener, an error hook and a
teardown. The template's `f()` (number formatting: `results-format.mjs` does it)
and `mix()` (heat colours: no R1a figure is a heat map) are not copied.
`results.css` carries the `--rc-*` palette for both themes (no red, no green),
the resets for the lab's element rules (`style.css`'s bare `svg{width:20px;...}`
would otherwise shrink every chart to an icon), template.html's chart rules
(123-147) renamed `rc-`, and the styles of every id and class of the page that
Task 9 builds, so Task 9 needs no CSS of its own.

None of these four files contains a `\u` escape or an invisible character, so
the Write tool can write each one exactly as given here; Step 8 byte-checks them.
They touch no file a Python suite reads, so only the node suite runs here.

**Files:**
- Create: `app/static/sim/charts-fake-dom.mjs` (a test helper: not a `*.test.mjs` file, so the test glob never runs it on its own)
- Create: `app/static/sim/charts-lib.mjs`
- Create: `app/static/sim/results.css`
- Test: `app/static/sim/charts-lib.test.mjs`

**Interfaces:**
- Consumes: nothing from an earlier task. `results.css` reads the lab's tokens from
  `app/static/sim/style.css` (`--ink`, `--ink-2`, `--muted`, `--paper`, `--line`,
  `--hairline`, `--field-bg`, `--seed-bg`, `--warn-ink`, `--shadow`) and
  `--agent-sighted` / `--agent-blind` from `app/static/sim/agents.css`; `results.html`
  (Task 9) loads `style.css`, then `agents.css`, then `results.css?v=R1a`.
- Produces, `app/static/sim/charts-lib.mjs` (import it as `'./charts-lib.mjs?v=R1a'`):
  - `NS` (the SVG namespace); `S(tag, attrs, parent) -> SVGElement` (null/undefined attrs skipped);
    `T(parent, x, y, str, attrs) -> SVGTextElement`; `H(tag, attrs, parent) -> HTMLElement`
    (`attrs.text` sets textContent); `fin(v) -> boolean` (`v != null && Number.isFinite(v)`).
  - `lin(d0, d1, r0, r1)` and `logs(d0, d1, r0, r1)`: scales with `.inv`; `ticks(lo, hi, n) -> number[]`
    (round steps; `[]` for an empty or reversed range).
  - `plot(host, o) -> { svg, g, top, x, y, m, W, H, pw, ph, host }`, `o = { w, h, x: { d, ticks?, fmt?, log?, none? },
    y: { ... }, m?: { t, r, b, l }, xgrid?, aria? }`: an `<svg class="rc-plot">` appended to `host`; `o.x.label`
    and `o.y.label` are ignored (no axis titles in SVG); `role="group"` and `aria-label` only when `o.aria` is
    given, never `role="img"`; `g` is clipped to the plot area, `top` is not.
  - `line(P, xs, ys, st) -> path.rc-ln` (the pen lifts at a non-finite value); `hline(P, v, st)` and
    `vline(P, v, st)` return their `<line>`; `st = { c, w?, dash?, op?, label?, right?, below?, dy? }`.
  - `tip(host)`, `showTip(host, px, py, title, rows)` with `rows = [{ c?, v, k? }]` (one `div.rc-tip`
    `role="status"` per host, holding `div.rc-tt` and `div.rc-tr` > `span.rc-key` + `b` + `span.rc-tl`),
    `hideTip(host)`, `localXY(P, e)`, `onPointer(el, move, leave)`, `crosshair(P, xs, series, xfmt)`,
    `nearest(P, pts, rowsOf, radius)`, `markTip(P, el, cx, cy, title, rows)` (class `rc-mark`, `tabindex="0"`;
    shows on pointerenter, pointerdown and focus; hides on a mouse pointerleave and on blur),
    `sideLabel(P, x, y, str, style) -> SVGTextElement` (`rc-lbl`, measured width).
  - `createMounter({ onError } = {}) -> { mount(host, draw, hOf), renderAll(force = false), clear(), dispose() }`:
    `draw(host, w, h)` runs at mount and whenever the host's width changes, or on `renderAll(true)`; a host
    whose width is 0 is never drawn (the ResizeObserver draws it once it has one); `h = hOf ? hOf(w) :
    round(clamp(w * 0.56, 250, 400))`; before each draw the host's `:scope > svg` is removed and its tip
    hidden; a draw that throws has its half-drawn svg removed and calls `onError(host, err)` (default:
    `console.error`, nothing written) -- it can be called again on a later resize, so a note it writes into
    the host must replace its previous one. `clear()` forgets every chart (the page calls it before it
    rebuilds its sections); `dispose()` also disconnects the observer and removes the listener.
  - The classes it writes: `rc-plot rc-grid rc-axis rc-ln rc-lbl rc-hit rc-hair rc-hdot rc-ring rc-mark
    rc-tip rc-tt rc-tr rc-key rc-tl`; clip-path ids `rc-clip<N>`.
- Produces, `app/static/sim/results.css`:
  - tokens `--rc-sighted --rc-blind --rc-baseline --rc-reactive --rc-grade --rc-text --rc-muted --rc-grid
    --rc-axis --rc-tip-bg --rc-tip-fg --rc-mei`, both themes;
  - styles for `main.results-main`, `#built`, `#warnings`, `#summary`, `#not-read`, `#not-read-list`, the tab's
    tables, `.rc-section` (+ `h2`), `.rc-meta`, `.rc-plant[data-state]`, `.rc-plant-details`, `.rc-checks`,
    `.rc-verdict[data-state]` (+ `h3`, `details summary`; `.verdict-short`, `.verdict-cells` and `.quote`
    come from agents.css), `.rc-notes`, `.rc-note`, `.rc-figure` (+ `h3`), `.rc-what`, `.rc-axis-y`, `.rc-axis-x`,
    `.rc-legend`, `.rc-table`, `.rc-unpaired`, `.rc-chart`, and the chart and tooltip classes above;
  - the legend swatch convention: `<span><i class="rc-swatch rc-sw-dot" style="color:var(--rc-sighted)"></i>text</span>`,
    with `rc-sw-dot` (an agent), `rc-sw-square` (a hand-written policy), `rc-sw-dash` (the current-grade line)
    and `rc-sw-bracket` (the MEI, `color:var(--rc-mei)`).
- Produces, `app/static/sim/charts-fake-dom.mjs` (tests import it as `'./charts-fake-dom.mjs?v=R1a'`):
  `FakeEl` (an element: attrs, children, classList, style, listeners, `dispatch(type, init)`,
  `querySelector`/`querySelectorAll` for `:scope > .class` and `:scope > tag`, `closest('.class')`;
  `FakeEl.textWidth` sets what `getComputedTextLength()` returns), `installFakeDocument()`,
  `fakeHost(width, id = 'chart')`, `walk(node)`, `svgTexts(node)`.

- [ ] **Step 1: Write the test helper, a fake DOM for node**

Create `app/static/sim/charts-fake-dom.mjs`:

```js
// A fake DOM for the results tab's chart tests under node:test: just enough of
// document.createElementNS / createElement and of an element for
// charts-lib.mjs to build a chart, so a test can read back every attribute,
// every SVG text and every listener without a browser.
//
// NOT a *.test.mjs file, so the glob "static/sim/*.test.mjs" never runs it on
// its own. node --test runs each test file in its own process, so the
// globalThis.document a test installs never reaches another file.

export class FakeEl {
  constructor(tag, ns = null) {
    this.tagName = tag;
    this.namespaceURI = ns;
    this.attrs = {};
    this.children = [];
    this.parentNode = null;
    this.listeners = {};
    this.style = {};
    this.own = '';
    this.hidden = false;
    this.clientWidth = 0;
    this.offsetWidth = 120;
    this.offsetHeight = 60;
    const el = this;
    this.classList = {
      add(...names) {
        const have = el.classes();
        for (const n of names) if (!have.includes(n)) have.push(n);
        el.attrs.class = have.join(' ');
      },
      contains(name) { return el.classes().includes(name); },
    };
  }
  classes() { return String(this.attrs.class || '').split(/\s+/).filter(Boolean); }
  get textContent() { return this.own + this.children.map(c => c.textContent).join(''); }
  set textContent(v) { this.own = String(v); this.children = []; }
  setAttribute(name, value) { this.attrs[name] = String(value); }
  getAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name) ? this.attrs[name] : null; }
  hasAttribute(name) { return Object.prototype.hasOwnProperty.call(this.attrs, name); }
  appendChild(node) {
    if (node.parentNode) node.remove();
    node.parentNode = this;
    this.children.push(node);
    return node;
  }
  replaceChildren(...nodes) {
    for (const c of this.children) c.parentNode = null;
    this.children = [];
    for (const n of nodes) this.appendChild(n);
  }
  remove() {
    if (!this.parentNode) return;
    const kids = this.parentNode.children;
    kids.splice(kids.indexOf(this), 1);
    this.parentNode = null;
  }
  // Only the two selector shapes charts-lib.mjs uses: ":scope > .class" and
  // ":scope > tag".
  matchesDirect(sel) {
    const m = /^:scope > (\.)?([\w-]+)$/.exec(sel);
    if (!m) throw new Error(`fake DOM: unsupported selector ${sel}`);
    return el => (m[1] ? el.classes().includes(m[2]) : el.tagName === m[2]);
  }
  querySelector(sel) { return this.children.find(this.matchesDirect(sel)) || null; }
  querySelectorAll(sel) { return this.children.filter(this.matchesDirect(sel)); }
  closest(sel) {
    const m = /^\.([\w-]+)$/.exec(sel);
    if (!m) throw new Error(`fake DOM: unsupported selector ${sel}`);
    for (let el = this; el; el = el.parentNode) if (el.classes().includes(m[1])) return el;
    return null;
  }
  addEventListener(type, fn) { (this.listeners[type] ||= []).push(fn); }
  removeEventListener(type, fn) {
    this.listeners[type] = (this.listeners[type] || []).filter(f => f !== fn);
  }
  dispatch(type, init = {}) {
    for (const fn of [...(this.listeners[type] || [])]) fn({ type, target: this, ...init });
  }
  getBoundingClientRect() { return { left: 0, top: 0, width: this.clientWidth, height: 0 }; }
  // A text's rendered width, as the test sets it: FakeEl.textWidth(text) or 0.
  getComputedTextLength() {
    return typeof FakeEl.textWidth === 'function' ? FakeEl.textWidth(this.textContent) : 0;
  }
}
FakeEl.textWidth = null;

/** Install globalThis.document; returns it. Its listeners are recorded too. */
export function installFakeDocument() {
  const doc = new FakeEl('#document');
  doc.createElementNS = (ns, tag) => new FakeEl(tag, ns);
  doc.createElement = tag => new FakeEl(tag);
  globalThis.document = doc;
  return doc;
}

/** A chart host: a div of the given width, inside a .rc-chart parent chain. */
export function fakeHost(width, id = 'chart') {
  const host = new FakeEl('div');
  host.setAttribute('class', 'rc-chart');
  host.setAttribute('id', id);
  host.id = id;
  host.clientWidth = width;
  return host;
}

/** Every element under `node` (itself included), in document order. */
export function walk(node, out = []) {
  out.push(node);
  for (const c of node.children) walk(c, out);
  return out;
}

/** The text of every SVG <text> under `node`, in document order. */
export function svgTexts(node) {
  return walk(node).filter(el => el.tagName === 'text').map(el => el.textContent);
}
```

- [ ] **Step 2: Write the failing test**

Create `app/static/sim/charts-lib.test.mjs`:

```js
// charts-lib.mjs, the results tab's copy of Ghassan's drawing helpers: its
// scales and ticks (pure), plot / markTip / showTip / sideLabel / crosshair on
// a fake DOM (charts-fake-dom.mjs), and createMounter with plain fake hosts, a
// stub ResizeObserver and a stub document; then results.css, read as text.
// node --test runs this file in its own process, so the globals it installs
// reach no other test file.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { FakeEl, installFakeDocument, fakeHost, walk, svgTexts } from './charts-fake-dom.mjs?v=R1a';
import {
  NS, S, fin, lin, logs, ticks, plot, line, hline, vline, showTip, hideTip,
  crosshair, nearest, markTip, sideLabel, createMounter,
} from './charts-lib.mjs?v=R1a';

// A ResizeObserver that records what it watches; fire() is a resize.
class StubRO {
  static all = [];
  constructor(cb) { this.cb = cb; this.observed = new Set(); this.disconnects = 0; StubRO.all.push(this); }
  observe(el) { this.observed.add(el); }
  unobserve(el) { this.observed.delete(el); }
  disconnect() { this.observed.clear(); this.disconnects += 1; }
  fire() { this.cb([]); }
}
// A document that records its listeners.
function stubDocument() {
  const doc = {
    added: [], removed: [],
    addEventListener(type, fn) { doc.added.push([type, fn]); },
    removeEventListener(type, fn) { doc.removed.push([type, fn]); },
  };
  globalThis.document = doc;
  return doc;
}
// The smallest host createMounter can draw into: a width and two queries.
const plainHost = width => ({ id: `host${width}`, clientWidth: width,
  querySelector: () => null, querySelectorAll: () => [] });
function newMounter(options) {
  StubRO.all.length = 0;
  globalThis.ResizeObserver = StubRO;
  return createMounter(options);
}

test('lin maps a domain onto a range and inverts it, either way round', () => {
  const s = lin(0, 10, 100, 200);
  assert.equal(s(0), 100);
  assert.equal(s(5), 150);
  assert.equal(s(10), 200);
  assert.equal(s.inv(150), 5);
  const y = lin(0, 800, 300, 12); // a y axis: a larger value is a smaller pixel
  assert.equal(y(0), 300);
  assert.equal(y(800), 12);
  assert.equal(y(400), 156);
  for (const v of [0, 123.4, 800]) assert.ok(Math.abs(y.inv(y(v)) - v) < 1e-9, `inv(${v})`);
  const lg = logs(1, 100, 0, 200);
  assert.ok(Math.abs(lg(10) - 100) < 1e-9);
  assert.ok(Math.abs(lg.inv(100) - 10) < 1e-9);
});

test('ticks are round steps inside the range, and none for an empty or reversed one', () => {
  assert.deepEqual(ticks(0, 1000, 5), [0, 200, 400, 600, 800, 1000]);
  assert.deepEqual(ticks(0, 778.14, 5), [0, 200, 400, 600]);
  assert.deepEqual(ticks(0, 1207.44, 5), [0, 200, 400, 600, 800, 1000, 1200]);
  assert.deepEqual(ticks(-0.5, 7.5, 8), [0, 1, 2, 3, 4, 5, 6, 7]);
  assert.deepEqual(ticks(0.1, 0.9, 4), [0.2, 0.4, 0.6, 0.8]);
  assert.deepEqual(ticks(3, 3, 5), []);
  assert.deepEqual(ticks(5, 1, 5), []);
});

test('fin accepts finite numbers only', () => {
  for (const v of [0, -3.5, 1e9]) assert.equal(fin(v), true, String(v));
  for (const v of [null, undefined, NaN, Infinity, -Infinity, '5']) assert.equal(fin(v), false, String(v));
});

test('plot draws its ticks and no axis title, never role="img", and returns its scales', () => {
  installFakeDocument();
  const host = fakeHost(600);
  const P = plot(host, {
    w: 600, h: 300,
    x: { d: [-0.5, 2.5], ticks: [0, 1, 2], fmt: i => `s${i}`, label: 'Seed' },
    y: { d: [0, 100], ticks: [0, 50, 100], label: 'Damage' },
    m: { l: 50, r: 20, t: 10, b: 30 },
  });
  assert.deepEqual(Object.keys(P).sort(), ['H', 'W', 'g', 'host', 'm', 'ph', 'pw', 'svg', 'top', 'x', 'y']);
  assert.equal(P.svg.tagName, 'svg');
  assert.equal(P.svg.namespaceURI, NS);
  assert.equal(P.svg.getAttribute('class'), 'rc-plot');
  assert.equal(P.svg.getAttribute('width'), '600');
  assert.equal(P.svg.getAttribute('height'), '300');
  assert.equal(P.svg.getAttribute('viewBox'), '0 0 600 300');
  assert.equal(P.svg.getAttribute('role'), null);
  assert.equal(P.svg.getAttribute('aria-label'), null);
  assert.deepEqual(svgTexts(host), ['s0', 's1', 's2', '0', '50', '100'], 'the axis titles are HTML, not SVG');
  assert.equal(P.x(-0.5), 50);
  assert.equal(P.x(2.5), 580);
  assert.equal(P.y(0), 270);
  assert.equal(P.y(100), 10);
  assert.equal(P.pw, 530);
  assert.equal(P.ph, 260);
  for (const el of walk(host)) {
    for (const c of el.classes()) assert.match(c, /^rc-/, `<${el.tagName}> carries the class ${c}`);
  }
  const labelled = plot(fakeHost(400), { w: 400, h: 250, x: { d: [0, 1] }, y: { d: [0, 1] }, aria: 'The pairs of C4' });
  assert.equal(labelled.svg.getAttribute('role'), 'group');
  assert.equal(labelled.svg.getAttribute('aria-label'), 'The pairs of C4');
  const clip = walk(labelled.svg).find(el => el.tagName === 'clipPath');
  assert.match(clip.getAttribute('id'), /^rc-clip\d+$/);
  assert.equal(labelled.g.getAttribute('clip-path'), `url(#${clip.getAttribute('id')})`);
});

test('line lifts the pen at a missing value; hline and vline span the plot', () => {
  installFakeDocument();
  const P = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  const p = line(P, [0, 5, NaN, 10, 10], [0, 5, 7, 10, 0], { c: 'var(--rc-grade)', dash: '5 4' });
  assert.equal(p.getAttribute('d'), 'M0.0,200.0L150.0,100.0M300.0,0.0L300.0,200.0');
  assert.equal(p.getAttribute('class'), 'rc-ln');
  assert.equal(p.getAttribute('style'), 'stroke:var(--rc-grade);stroke-width:2;stroke-dasharray:5 4;');
  const h = hline(P, 5, { c: 'var(--rc-mei)' });
  assert.deepEqual(['x1', 'x2', 'y1', 'y2'].map(k => h.getAttribute(k)), ['0', '300', '100', '100']);
  const v = vline(P, 5, { c: 'var(--rc-mei)', label: 'x' });
  assert.deepEqual(['x1', 'x2', 'y1', 'y2'].map(k => v.getAttribute(k)), ['150', '150', '0', '200']);
  assert.deepEqual(svgTexts(P.top), ['x']);
});

test('markTip makes a mark focusable and shows its rows on focus, hover and tap; blur hides them', () => {
  installFakeDocument();
  const host = fakeHost(300);
  const P = plot(host, { w: 300, h: 200, x: { d: [0, 1] }, y: { d: [0, 1] } });
  const dot = S('circle', { cx: 100, cy: 50, r: 5 }, P.g);
  markTip(P, dot, 100, 50, 'Seed 0', [{ c: 'var(--rc-sighted)', v: '359.9', k: 'median' }, { v: '+360.6', k: 'blind minus sighted' }]);
  assert.equal(dot.getAttribute('tabindex'), '0');
  assert.ok(dot.classList.contains('rc-mark'));
  for (const type of ['focus', 'pointerenter', 'pointerdown']) {
    hideTip(host);
    dot.dispatch(type, { pointerType: 'touch' });
    assert.equal(host.querySelector(':scope > .rc-tip').hidden, false, type);
  }
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.getAttribute('role'), 'status');
  assert.equal(host.querySelectorAll(':scope > .rc-tip').length, 1, 'one tip per chart, reused');
  const [title, first, second] = tipEl.children;
  assert.equal(title.getAttribute('class'), 'rc-tt');
  assert.equal(title.textContent, 'Seed 0');
  assert.equal(first.getAttribute('class'), 'rc-tr');
  assert.deepEqual(first.children.map(c => c.getAttribute('class')), ['rc-key', null, 'rc-tl']);
  assert.equal(first.children[0].style.borderColor, 'var(--rc-sighted)');
  assert.equal(first.children[1].tagName, 'b');
  assert.equal(first.children[1].textContent, '359.9');
  assert.equal(first.children[2].textContent, 'median');
  assert.equal(second.children[0].style.borderColor, 'transparent');
  dot.dispatch('pointerleave', { pointerType: 'touch' });
  assert.equal(tipEl.hidden, false, 'a finger lifting off keeps the numbers up');
  dot.dispatch('pointerleave', { pointerType: 'mouse' });
  assert.equal(tipEl.hidden, true);
  dot.dispatch('focus');
  dot.dispatch('blur');
  assert.equal(tipEl.hidden, true);
});

test('showTip keeps the tip inside its chart', () => {
  installFakeDocument();
  const host = fakeHost(300); // the fake tip is 120 x 60
  showTip(host, 250, 100, 'T', [{ v: '1' }]);
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.style.left, '116px', 'right edge: left of the point (250 - 14 - 120)');
  assert.equal(tipEl.style.top, '28px', 'above the point (100 - 60 - 12)');
  showTip(host, 20, 30, 'T', [{ v: '1' }]);
  assert.equal(tipEl.style.left, '34px', 'right of the point (20 + 14)');
  assert.equal(tipEl.style.top, '46px', 'top edge: below the point (30 + 16)');
});

test('sideLabel flips left only when its MEASURED width would leave the plot', () => {
  installFakeDocument();
  const P = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 1] }, y: { d: [0, 1] }, m: { l: 0, r: 20, t: 0, b: 0 } });
  try {
    FakeEl.textWidth = () => 40;
    const a = sideLabel(P, 200, 50, 'MEI'); // 200 + 14 + 40 = 254 < 280
    assert.deepEqual([a.getAttribute('x'), a.getAttribute('text-anchor')], ['214', 'start']);
    assert.equal(a.getAttribute('class'), 'rc-lbl');
    const b = sideLabel(P, 230, 50, 'MEI'); // 230 + 14 + 40 = 284: the 6.8 px guess (20.4) would have kept it right
    assert.deepEqual([b.getAttribute('x'), b.getAttribute('text-anchor')], ['216', 'end']);
    FakeEl.textWidth = () => 0; // nothing measured: 6.8 px a character
    const c = sideLabel(P, 230, 50, 'MEI'); // 230 + 14 + 20.4 = 264.4 < 280
    assert.equal(c.getAttribute('text-anchor'), 'start');
    const d = sideLabel(P, 240, 50, 'a much longer label'); // 19 x 6.8 = 129.2
    assert.equal(d.getAttribute('text-anchor'), 'end');
  } finally {
    FakeEl.textWidth = null;
  }
});

test('crosshair and nearest show the numbers of the point under the pointer', () => {
  installFakeDocument();
  const host = fakeHost(300);
  const P = plot(host, { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  crosshair(P, [0, 5, 10], [{ name: 'a', ys: [1, 2, 3], c: 'var(--rc-grade)', f: v => `v${v}` }], x => `x${x}`);
  const hit = P.top.children.find(el => el.classes().includes('rc-hit'));
  hit.dispatch('pointermove', { clientX: 140, clientY: 50 }); // 140 px is x 4.67: the nearest x is 5
  const tipEl = host.querySelector(':scope > .rc-tip');
  assert.equal(tipEl.children[0].textContent, 'x5');
  assert.equal(tipEl.children[1].children[1].textContent, 'v2');
  hit.dispatch('pointerleave', { pointerType: 'mouse' });
  assert.equal(tipEl.hidden, true);
  const Q = plot(fakeHost(300), { w: 300, h: 200, x: { d: [0, 10] }, y: { d: [0, 10] }, m: { l: 0, r: 0, t: 0, b: 0 } });
  nearest(Q, [{ x: 2, y: 2, name: 'p' }, { x: 8, y: 8, name: 'q' }], p => ({ title: p.name, rows: [{ v: String(p.x) }] }));
  const hit2 = Q.top.children.find(el => el.classes().includes('rc-hit'));
  hit2.dispatch('pointermove', { clientX: 235, clientY: 45 }); // the point (8, 8) is at (240, 40)
  assert.equal(Q.host.querySelector(':scope > .rc-tip').children[0].textContent, 'q');
});

test('createMounter draws each chart at its width, with the default height rule or hOf', () => {
  stubDocument();
  const m = newMounter();
  const calls = [];
  const draw = (...args) => calls.push(args);
  const a = plainHost(600), b = plainHost(300), c = plainHost(1000), d = plainHost(800);
  m.mount(a, draw);
  m.mount(b, draw);
  m.mount(c, draw);
  m.mount(d, draw, w => w / 4);
  m.mount(null, draw); // a missing host is skipped
  assert.deepEqual(calls, [[a, 600, 336], [b, 300, 250], [c, 1000, 400], [d, 800, 200]]);
  m.dispose();
});

test('a zero width never draws; an unchanged width redraws only when forced; a resize redraws', () => {
  stubDocument();
  const m = newMounter();
  const calls = [];
  const host = plainHost(0);
  m.mount(host, (h, w, hh) => calls.push([w, hh]));
  m.renderAll();
  m.renderAll(true);
  assert.deepEqual(calls, [], 'a host with no width yet is not drawn, forced or not');
  host.clientWidth = 500;
  StubRO.all[0].fire();
  assert.deepEqual(calls, [[500, 280]], 'the observer draws it once it has a width');
  m.renderAll();
  assert.deepEqual(calls, [[500, 280]], 'same width: nothing to redraw');
  m.renderAll(true);
  assert.deepEqual(calls, [[500, 280], [500, 280]], 'forced (a language switch): redrawn');
  m.dispose();
});

test('a draw that throws reaches onError, and the other charts still draw', () => {
  stubDocument();
  const errors = [];
  const drawn = [];
  const m = newMounter({ onError: (host, err) => errors.push([host, err.message]) });
  const bad = plainHost(400), good = plainHost(400);
  m.mount(bad, () => { throw new Error('no data'); });
  m.mount(good, h => drawn.push(h));
  assert.deepEqual(errors, [[bad, 'no data']]);
  assert.deepEqual(drawn, [good]);
  m.dispose();
  const logged = [];
  const original = console.error;
  console.error = (...args) => logged.push(args);
  try {
    const quiet = newMounter();
    quiet.mount(plainHost(400), () => { throw new Error('boom'); });
    quiet.dispose();
  } finally {
    console.error = original;
  }
  assert.equal(logged.length, 1, 'the default hook logs and never throws');
});

test('one observer and one document listener; clear forgets every chart, dispose removes both', () => {
  const doc = stubDocument();
  const m = newMounter();
  assert.equal(StubRO.all.length, 1);
  assert.deepEqual(doc.added.map(([type]) => type), ['pointerdown']);
  const h1 = plainHost(400), h2 = plainHost(400);
  const drawn = [];
  m.mount(h1, h => drawn.push(h));
  m.mount(h2, h => drawn.push(h));
  assert.equal(StubRO.all.length, 1, 'still one observer for two charts');
  assert.deepEqual([...StubRO.all[0].observed], [h1, h2]);
  m.clear();
  assert.equal(StubRO.all[0].observed.size, 0);
  m.renderAll(true);
  assert.deepEqual(drawn, [h1, h2], 'a forgotten chart is not drawn again');
  m.mount(h1, h => drawn.push(h));
  assert.deepEqual([...StubRO.all[0].observed], [h1]);
  m.dispose();
  assert.equal(StubRO.all[0].disconnects, 1);
  assert.deepEqual(doc.removed, doc.added, 'the same listener is removed');
  m.renderAll(true);
  assert.equal(drawn.length, 3);
});

test('a pointerdown outside every chart hides every tip; one inside a chart does not', () => {
  const doc = installFakeDocument();
  const m = newMounter();
  const host = fakeHost(400);
  m.mount(host, (h, w, hh) => { plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } }); });
  showTip(host, 10, 10, 'T', []);
  const tipEl = host.querySelector(':scope > .rc-tip');
  doc.dispatch('pointerdown', { target: walk(host).find(el => el.tagName === 'svg') });
  assert.equal(tipEl.hidden, false, 'a tap inside a chart is the chart\'s own');
  doc.dispatch('pointerdown', { target: new FakeEl('p') });
  assert.equal(tipEl.hidden, true);
  m.dispose();
  assert.equal((doc.listeners.pointerdown || []).length, 0);
});

test('a redraw replaces the svg and hides the tip; a draw that throws leaves no half chart', () => {
  installFakeDocument();
  const m = newMounter();
  const host = fakeHost(400);
  m.mount(host, (h, w, hh) => plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } }));
  assert.equal(host.querySelectorAll(':scope > svg').length, 1);
  showTip(host, 5, 5, 'T', []);
  m.renderAll(true);
  assert.equal(host.querySelectorAll(':scope > svg').length, 1, 'one svg, not two');
  assert.equal(host.querySelector(':scope > .rc-tip').hidden, true);
  m.dispose();
  const errors = [];
  const m2 = newMounter({ onError: () => errors.push(1) });
  const half = fakeHost(400);
  m2.mount(half, (h, w, hh) => {
    plot(h, { w, h: hh, x: { d: [0, 1] }, y: { d: [0, 1] } });
    throw new Error('half drawn');
  });
  assert.equal(half.querySelectorAll(':scope > svg').length, 0);
  assert.equal(errors.length, 1);
  m2.dispose();
});

// Hue and saturation of a #rrggbb colour.
function hueSat(hex) {
  const [r, g, b] = [1, 3, 5].map(i => parseInt(hex.slice(i, i + 2), 16) / 255);
  const max = Math.max(r, g, b), min = Math.min(r, g, b), d = max - min, l = (max + min) / 2;
  if (d === 0) return { h: 0, s: 0 };
  const h = max === r ? 60 * (((g - b) / d) % 6) : max === g ? 60 * ((b - r) / d + 2) : 60 * ((r - g) / d + 4);
  return { h: (h + 360) % 360, s: d / (1 - Math.abs(2 * l - 1)) };
}

test('results.css: every token in both themes, the resets of design 7.3, and no red or green', () => {
  const css = readFileSync(new URL('./results.css', import.meta.url), 'utf8');
  const block = selector => {
    const at = css.indexOf(selector);
    assert.ok(at >= 0, `missing ${selector}`);
    return css.slice(at, css.indexOf('}', at));
  };
  const light = block(':root{--rc-');
  const dark = block(':root[data-theme="dark"]{');
  const system = block(':root:not([data-theme="light"]){');
  for (const name of ['sighted', 'blind', 'baseline', 'reactive', 'grade', 'text', 'muted', 'grid', 'axis', 'tip-bg', 'tip-fg', 'mei']) {
    assert.ok(light.includes(`--rc-${name}:`), `--rc-${name} in the light block`);
  }
  assert.ok(light.includes('--rc-sighted:var(--agent-sighted'), 'sighted is agents.css\'s blue');
  assert.ok(light.includes('--rc-blind:var(--agent-blind'), 'blind is agents.css\'s amber');
  const pairs = [['baseline', '#5b6470', '#b9c0c8'], ['reactive', '#8a8f98', '#8d939a'], ['grade', '#6b4fa0', '#b9a3e8'],
    ['grid', '#e3e6e1', '#2a2f2e'], ['axis', '#c9cdc6', '#3a403f'], ['mei', '#4b4f56', '#c7ccd2']];
  for (const [name, day, night] of pairs) {
    assert.ok(light.includes(`--rc-${name}:${day}`), `light --rc-${name}`);
    assert.ok(dark.includes(`--rc-${name}:${night}`), `dark --rc-${name}`);
    assert.ok(system.includes(`--rc-${name}:${night}`), `system-dark --rc-${name}`);
  }
  for (const rule of [
    '.rc-chart > svg{width:auto;height:auto;fill:#000;stroke:none;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter}',
    '.rc-chart{position:relative;width:100%;height:auto;direction:ltr;touch-action:pan-y}',
    '.rc-plot text{stroke:none;font-family:Consolas,ui-monospace,monospace;font-size:11px;fill:var(--rc-muted)}',
    'html[dir=rtl] .rc-tip{direction:rtl}',
    '.rc-tip .rc-tl{white-space:normal}',
  ]) assert.ok(css.includes(rule), `missing ${rule}`);
  assert.doesNotMatch(css, /ellipsis/, 'a tooltip label is never cut');
  for (const cls of ['rc-plot', 'rc-grid', 'rc-axis', 'rc-ln', 'rc-hit', 'rc-hair', 'rc-hdot', 'rc-mark', 'rc-ring',
    'rc-lbl', 'rc-tip', 'rc-tt', 'rc-tr', 'rc-tl', 'rc-key', 'rc-dot', 'rc-pair', 'rc-band', 'rc-mei', 'rc-mei-label']) {
    assert.ok(css.includes(`.${cls}`), `no rule for .${cls}, a class the chart code writes`);
  }
  for (const hex of new Set(css.match(/#[0-9a-fA-F]{6}\b/g))) {
    const { h, s } = hueSat(hex);
    const redOrGreen = h >= 345 || h <= 15 || (h >= 80 && h <= 165);
    assert.ok(s < 0.25 || !redOrGreen, `${hex} reads as red or green (hue ${h.toFixed(0)}, saturation ${s.toFixed(2)})`);
  }
});

test('the drawing code writes every colour as a token, so a theme switch redraws nothing', () => {
  for (const name of ['charts-lib.mjs']) {
    const src = readFileSync(new URL(`./${name}`, import.meta.url), 'utf8');
    assert.doesNotMatch(src, /#[0-9a-fA-F]{3,6}\b|rgba?\(/, `${name} carries a literal colour`);
  }
});
```

- [ ] **Step 3: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/charts-lib.test.mjs)
```

Expected: FAIL before any test runs, because the module does not exist yet:
`Error [ERR_MODULE_NOT_FOUND]: Cannot find module '...\app\static\sim\charts-lib.mjs' imported from
...\app\static\sim\charts-lib.test.mjs`, then `ℹ tests 1`, `ℹ pass 0`, `ℹ fail 1` (observed in drafting,
with the scratch folder in place of the repository path).

- [ ] **Step 4: Write the drawing library**

Create `app/static/sim/charts-lib.mjs`:

```js
// The results tab's drawing library (/results).
//
// A COPY, not an import: the generic drawing helpers of Ghassan's published
// page, results/page/template.html (lines 747-978, and sideLabel at 992-996, as
// of commit a7ce729). His page and make_page.py are never edited (design Q4),
// so the copy is adapted here instead (design 7.3):
//  - every class it writes carries the rc- prefix. The lab's style.css styles
//    bare svg elements and .chart/.grid, and results.css resets those for the
//    tab and styles these names only;
//  - plot() writes NO axis titles: they are HTML beside the chart (design 7.2),
//    so an Arabic word never reaches SVG text, and its svg gets no role="img"
//    (design 7.3: the focusable marks are never inside role=img). o.aria, when
//    given, labels the svg as a group;
//  - sideLabel MEASURES its label with getComputedTextLength() instead of
//    guessing 6.8 px a character, and falls back to that guess only where
//    nothing could be measured (a node that is not laid out);
//  - the mounting code is a factory, createMounter(): one ResizeObserver over
//    every chart, one document pointerdown listener, an error hook, and a
//    teardown, so the page can redraw every chart after a language switch and
//    drop them all when it rebuilds, without stacking listeners;
//  - the number formatter f() and the heat colour mix() of the template are
//    not copied: results-format.mjs formats numbers, and no R1a figure is a
//    heat map.
// Nothing here reads a result or a string: results-charts.mjs decides WHAT is
// drawn, this file only HOW.

export const NS = 'http://www.w3.org/2000/svg';
let UID = 0;

// ------------------------------------------------------------ dom helpers
export function S(tag, attrs, parent) {
  const e = document.createElementNS(NS, tag);
  if (attrs) for (const k in attrs) if (attrs[k] != null) e.setAttribute(k, attrs[k]);
  if (parent) parent.appendChild(e);
  return e;
}
export function T(parent, x, y, str, attrs) {
  const t = S('text', Object.assign({ x, y }, attrs || {}), parent);
  t.textContent = str;
  return t;
}
export function H(tag, attrs, parent) {
  const e = document.createElement(tag);
  if (attrs) for (const k in attrs) {
    if (k === 'text') e.textContent = attrs[k]; else e.setAttribute(k, attrs[k]);
  }
  if (parent) parent.appendChild(e);
  return e;
}
export const fin = v => v != null && Number.isFinite(v);

// ----------------------------------------------------------------- scales
export function lin(d0, d1, r0, r1) {
  const s = v => r0 + (v - d0) / (d1 - d0) * (r1 - r0);
  s.inv = p => d0 + (p - r0) / (r1 - r0) * (d1 - d0);
  return s;
}
export function logs(d0, d1, r0, r1) {
  const a = Math.log(d0), b = Math.log(d1);
  const s = v => r0 + (Math.log(v) - a) / (b - a) * (r1 - r0);
  s.inv = p => Math.exp(a + (p - r0) / (r1 - r0) * (b - a));
  return s;
}
export function ticks(lo, hi, n) {
  const raw = (hi - lo) / Math.max(1, n);
  const mag = Math.pow(10, Math.floor(Math.log10(raw)));
  const e = raw / mag;
  const step = (e >= 7.5 ? 10 : e >= 3.5 ? 5 : e >= 1.5 ? 2 : 1) * mag;
  const out = [];
  for (let v = Math.ceil(lo / step - 1e-9) * step; v <= hi + step * 1e-9; v += step)
    out.push(+v.toFixed(10));
  return out;
}

// ------------------------------------------------------------------- plot
export function plot(host, o) {
  const W = o.w, Hh = o.h;
  const m = Object.assign({ t: 12, r: 16, b: 42, l: 52 }, o.m || {});
  const svg = S('svg', { width: W, height: Hh, viewBox: `0 0 ${W} ${Hh}`, class: 'rc-plot',
                         role: o.aria ? 'group' : null, 'aria-label': o.aria || null }, host);
  const x = (o.x.log ? logs : lin)(o.x.d[0], o.x.d[1], m.l, W - m.r);
  const y = (o.y.log ? logs : lin)(o.y.d[0], o.y.d[1], Hh - m.b, m.t);
  const grid = S('g', { class: 'rc-grid' }, svg);
  const pw = W - m.l - m.r, ph = Hh - m.t - m.b;
  if (!o.x.none) {
    const xt = o.x.ticks || ticks(o.x.d[0], o.x.d[1], Math.max(2, Math.round(pw / 80)));
    for (const v of xt) {
      const px = x(v);
      if (o.xgrid !== false) S('line', { x1: px, x2: px, y1: m.t, y2: Hh - m.b }, grid);
      T(svg, px, Hh - m.b + 16, (o.x.fmt || String)(v), { 'text-anchor': 'middle' });
    }
  }
  if (!o.y.none) {
    const yt = o.y.ticks || ticks(o.y.d[0], o.y.d[1], Math.max(2, Math.round(ph / 48)));
    for (const v of yt) {
      const py = y(v);
      S('line', { x1: m.l, x2: W - m.r, y1: py, y2: py }, grid);
      T(svg, m.l - 7, py + 4, (o.y.fmt || String)(v), { 'text-anchor': 'end' });
    }
  }
  S('line', { x1: m.l, x2: W - m.r, y1: Hh - m.b, y2: Hh - m.b, class: 'rc-axis' }, svg);
  // o.x.label and o.y.label are ignored on purpose: axis titles are HTML.
  const id = 'rc-clip' + (++UID);
  S('rect', { x: m.l, y: m.t - 2, width: pw, height: ph + 4 }, S('clipPath', { id }, S('defs', {}, svg)));
  const g = S('g', { 'clip-path': `url(#${id})` }, svg);
  const top = S('g', {}, svg);
  return { svg, g, top, x, y, m, W, H: Hh, pw, ph, host };
}
export function line(P, xs, ys, st) {
  let d = '', pen = false;
  for (let i = 0; i < xs.length; i++) {
    if (!fin(ys[i]) || !fin(xs[i])) { pen = false; continue; }
    d += (pen ? 'L' : 'M') + P.x(xs[i]).toFixed(1) + ',' + P.y(ys[i]).toFixed(1);
    pen = true;
  }
  return S('path', { d, class: 'rc-ln', style: `stroke:${st.c};stroke-width:${st.w || 2};` +
    (st.dash ? `stroke-dasharray:${st.dash};` : '') + (st.op ? `opacity:${st.op};` : '') }, P.g);
}
export function hline(P, v, st) {
  const py = P.y(v);
  const el = S('line', { x1: P.m.l, x2: P.W - P.m.r, y1: py, y2: py,
              style: `stroke:${st.c};stroke-width:${st.w || 1.3};stroke-dasharray:${st.dash || '5 4'}` }, P.g);
  if (st.label) T(P.top, st.right ? P.W - P.m.r - 4 : P.m.l + 6, py + (st.below ? 14 : -6), st.label,
                  { class: 'rc-lbl', style: `fill:${st.c}`, 'text-anchor': st.right ? 'end' : 'start' });
  return el;
}
export function vline(P, v, st) {
  const px = P.x(v);
  const el = S('line', { x1: px, x2: px, y1: P.m.t, y2: P.H - P.m.b,
              style: `stroke:${st.c};stroke-width:${st.w || 1.3};stroke-dasharray:${st.dash || '5 4'}` }, P.g);
  if (st.label) T(P.top, px + 5, P.m.t + (st.dy || 12), st.label,
                  { class: 'rc-lbl', style: `fill:${st.c}` });
  return el;
}

// -------------------------------------------------------------- tooltip
export function tip(host) {
  let t = host.querySelector(':scope > .rc-tip');
  if (!t) { t = H('div', { class: 'rc-tip', role: 'status' }, host); t.hidden = true; }
  return t;
}
export function showTip(host, px, py, title, rows) {
  const t = tip(host);
  t.replaceChildren();
  if (title) H('div', { class: 'rc-tt', text: title }, t);
  for (const r of rows) {
    const row = H('div', { class: 'rc-tr' }, t);
    const k = H('span', { class: 'rc-key' }, row);
    k.style.borderColor = r.c || 'transparent';
    H('b', { text: r.v }, row);
    if (r.k) H('span', { class: 'rc-tl', text: r.k }, row);
  }
  t.hidden = false;
  const hw = host.clientWidth, tw = t.offsetWidth, th = t.offsetHeight;
  let left = px + 14;
  if (left + tw > hw) left = px - 14 - tw;
  if (left < 0) left = Math.max(0, Math.min(hw - tw, px - tw / 2));
  let top = py - th - 12;
  if (top < 0) top = py + 16;
  t.style.left = left + 'px';
  t.style.top = top + 'px';
}
export function hideTip(host) {
  const t = host.querySelector(':scope > .rc-tip');
  if (t) t.hidden = true;
}
export function localXY(P, e) {
  const r = P.svg.getBoundingClientRect();
  return [e.clientX - r.left, e.clientY - r.top];
}
export function onPointer(el, move, leave) {
  el.addEventListener('pointermove', move);
  el.addEventListener('pointerdown', move);
  el.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') leave(); });
}

// Crosshair: snaps to the nearest x, lists every series at that x.
export function crosshair(P, xs, series, xfmt) {
  const hair = S('line', { class: 'rc-hair', y1: P.m.t, y2: P.H - P.m.b, visibility: 'hidden' }, P.top);
  const dots = series.map(s => S('circle', { r: 4, class: 'rc-hdot', style: `fill:${s.c}`, visibility: 'hidden' }, P.top));
  const hit = S('rect', { x: P.m.l, y: P.m.t, width: P.pw, height: P.ph, class: 'rc-hit' }, P.top);
  const leave = () => {
    hair.setAttribute('visibility', 'hidden');
    dots.forEach(d => d.setAttribute('visibility', 'hidden'));
    hideTip(P.host);
  };
  onPointer(hit, e => {
    const [px, py] = localXY(P, e);
    const xv = P.x.inv(px);
    let lo = 0, hi = xs.length - 1;
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (xs[mid] < xv) lo = mid; else hi = mid; }
    const i = Math.abs(xs[lo] - xv) < Math.abs(xs[hi] - xv) ? lo : hi;
    const X = P.x(xs[i]);
    hair.setAttribute('x1', X); hair.setAttribute('x2', X); hair.setAttribute('visibility', 'visible');
    series.forEach((s, k) => {
      const v = s.ys[i];
      if (fin(v)) {
        dots[k].setAttribute('cx', X); dots[k].setAttribute('cy', P.y(v)); dots[k].setAttribute('visibility', 'visible');
      } else dots[k].setAttribute('visibility', 'hidden');
    });
    showTip(P.host, X, py, xfmt(xs[i]), series.map(s => ({ c: s.c, v: s.f(s.ys[i]), k: s.name })));
  }, leave);
}
// Nearest point: the pointer only has to be closest, not on the dot.
export function nearest(P, pts, rowsOf, radius) {
  const px = pts.map(p => p.px != null ? [p.px, p.py] : [P.x(p.x), P.y(p.y)]);
  const ring = S('circle', { r: 8, class: 'rc-ring', visibility: 'hidden' }, P.top);
  const hit = S('rect', { x: P.m.l, y: P.m.t, width: P.pw, height: P.ph, class: 'rc-hit' }, P.top);
  const leave = () => { ring.setAttribute('visibility', 'hidden'); hideTip(P.host); };
  onPointer(hit, e => {
    const [mx, my] = localXY(P, e);
    let best = -1, bd = (radius || 32) ** 2;
    for (let i = 0; i < px.length; i++) {
      const d = (px[i][0] - mx) ** 2 + (px[i][1] - my) ** 2;
      if (d < bd) { bd = d; best = i; }
    }
    if (best < 0) return leave();
    ring.setAttribute('cx', px[best][0]); ring.setAttribute('cy', px[best][1]); ring.setAttribute('visibility', 'visible');
    const r = rowsOf(pts[best]);
    showTip(P.host, px[best][0], px[best][1], r.title, r.rows);
  }, leave);
}
// Per-mark hover and keyboard focus for bars, dots and cells.
export function markTip(P, el, cx, cy, title, rows) {
  el.setAttribute('tabindex', '0');
  el.classList.add('rc-mark');
  const show = () => showTip(P.host, cx, cy, title, rows);
  el.addEventListener('pointerenter', show);
  el.addEventListener('pointerdown', show);
  el.addEventListener('focus', show);
  el.addEventListener('pointerleave', e => { if (e.pointerType === 'mouse') hideTip(P.host); });
  el.addEventListener('blur', () => hideTip(P.host));
}
// A label right of a point, or left of it when it would leave the plot. The
// width is measured; 6.8 px a character only where nothing could be measured.
export function sideLabel(P, x, y, str, style) {
  const t = T(P.top, x + 14, y, str, { class: 'rc-lbl', 'text-anchor': 'start', style });
  let w = 0;
  try { w = typeof t.getComputedTextLength === 'function' ? t.getComputedTextLength() : 0; } catch { w = 0; }
  if (!(w > 0)) w = String(str).length * 6.8;
  if (x + 14 + w >= P.W - P.m.r) {
    t.setAttribute('x', x - 14);
    t.setAttribute('text-anchor', 'end');
  }
  return t;
}

// ------------------------------------------------------------ mounting
// mount(host, draw, hOf): draw(host, w, h) now and on every width change.
// renderAll(force): redraw every chart whose width changed, or every chart
// when forced (a language switch). A zero width never draws: a host that is
// not laid out yet is drawn by the ResizeObserver once it has a width.
// clear(): forget every chart (the page rebuilds its sections); dispose():
// clear, disconnect the observer and remove the document listener.
export function createMounter({ onError } = {}) {
  const charts = [];
  const report = typeof onError === 'function'
    ? onError
    : (host, err) => console.error('results chart', host && host.id, err);
  const RO = globalThis.ResizeObserver;
  const ro = typeof RO === 'function' ? new RO(() => renderAll()) : null;
  const doc = globalThis.document;
  const onDown = e => {
    const target = e && e.target;
    if (target && typeof target.closest === 'function' && target.closest('.rc-chart')) return;
    for (const c of charts) hideTip(c.host);
  };
  if (doc && typeof doc.addEventListener === 'function') doc.addEventListener('pointerdown', onDown);

  function render(c, force) {
    const w = Math.floor(c.host.clientWidth) || 0;
    if (!w || (!force && w === c.w)) return;
    c.w = w;
    c.host.querySelectorAll(':scope > svg').forEach(s => s.remove());
    hideTip(c.host);
    const h = c.hOf ? c.hOf(w) : Math.round(Math.min(400, Math.max(250, w * 0.56)));
    try {
      c.draw(c.host, w, h);
    } catch (err) {
      c.host.querySelectorAll(':scope > svg').forEach(s => s.remove());
      report(c.host, err);
    }
  }
  function mount(host, draw, hOf) {
    if (!host) return;
    const c = { host, draw, hOf, w: 0 };
    charts.push(c);
    if (ro) ro.observe(host);
    render(c, false);
  }
  function renderAll(force = false) {
    for (const c of charts) render(c, force);
  }
  function clear() {
    if (ro) for (const c of charts) ro.unobserve(c.host);
    charts.length = 0;
  }
  function dispose() {
    clear();
    if (ro) ro.disconnect();
    if (doc && typeof doc.removeEventListener === 'function') doc.removeEventListener('pointerdown', onDown);
  }
  return { mount, renderAll, clear, dispose };
}
```

- [ ] **Step 5: Run it: everything but the stylesheet test passes**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/charts-lib.test.mjs)
```

Expected (observed in drafting): `✖ results.css: every token in both themes, the resets of design 7.3, and no
red or green` with `Error: ENOENT: no such file or directory, open '...\app\static\sim\results.css'`, then
`ℹ tests 17`, `ℹ pass 16`, `ℹ fail 1`.

- [ ] **Step 6: Write the stylesheet**

Create `app/static/sim/results.css`:

```css
/* The results tab (/results). Loaded AFTER style.css and agents.css: the
   tokens, the topbar, the nav, the toggles and the footer are the lab's; the
   sighted and blind colours, the verdict quote and the phone nav row are
   agents.css's; only what this tab adds lives here.

   COLOURS. One table for both themes, every role distinct from every other
   role on the same figure: sighted blue and blind amber are agents.css's own
   tokens, the three hand-written policies are slate, grey and violet, and the
   MEI bracket is an ink grey. NEVER red or green, here as on /agents: the tab
   shows no winner. The three blocks below are the same list three times, like
   style.css's palette: edit all three. charts-lib.test.mjs pins them.

   RESETS. style.css has element rules written for the lab's icons and panels:
   svg{width:20px;height:20px;fill:none;stroke:currentColor;stroke-width:1.6;
   stroke-linecap:round;stroke-linejoin:round}, h2{font-size:12px},
   a{text-decoration:none}, dt and dd as flex rows. They match this tab's
   elements too, whatever their class, so each is reset on the tab's own
   elements: a chart's svg takes its size from its width and height attributes
   and draws with SVG's own defaults (fill black, no stroke), so every shape
   states its own colour.

   CHARTS. The chart rules are those of results/page/template.html (lines
   123-147), renamed rc- and moved onto these tokens. A chart host is
   direction:ltr, because its SVG labels are numbers and Latin only; its
   tooltip turns back to rtl in Arabic. */

:root{--rc-sighted:var(--agent-sighted,#2f6db0);--rc-blind:var(--agent-blind,#b5761c);--rc-baseline:#5b6470;--rc-reactive:#8a8f98;--rc-grade:#6b4fa0;--rc-text:var(--ink);--rc-muted:var(--muted);--rc-grid:#e3e6e1;--rc-axis:#c9cdc6;--rc-tip-bg:var(--paper);--rc-tip-fg:var(--ink);--rc-mei:#4b4f56}
:root[data-theme="dark"]{--rc-baseline:#b9c0c8;--rc-reactive:#8d939a;--rc-grade:#b9a3e8;--rc-grid:#2a2f2e;--rc-axis:#3a403f;--rc-mei:#c7ccd2}
@media(prefers-color-scheme:dark){:root:not([data-theme="light"]){--rc-baseline:#b9c0c8;--rc-reactive:#8d939a;--rc-grade:#b9a3e8;--rc-grid:#2a2f2e;--rc-axis:#3a403f;--rc-mei:#c7ccd2}}

/* the page */
main.results-main{max-width:1180px;font-size:12px}
.results-main a{color:inherit;text-decoration:underline;text-decoration-color:var(--rc-axis);text-underline-offset:3px}
.results-main a:hover{text-decoration-color:currentColor}
.results-main dl{margin:0}
.results-main dt{display:block;font-size:inherit;color:var(--rc-muted)}
.results-main dd{display:block;margin:0;direction:inherit}
.results-main h3{margin:0;font-size:12px;font-weight:650;line-height:1.5}
#built{margin:0 0 6px;font-size:10px;line-height:1.7;color:var(--rc-muted)}
#warnings{margin:0 0 12px;padding:0;list-style:none;font-size:11px;line-height:1.7;color:var(--warn-ink)}
#warnings:empty{display:none}

/* the summary and the files not read */
#summary,#not-read{margin:0 0 17px;padding:16px 18px;background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
#summary h2,#not-read h2{margin:0 0 6px;font-size:14px;font-weight:650}
#summary>p{margin:0 0 8px;font-size:11px;line-height:1.75;color:var(--ink-2)}
#not-read-list{margin:0;padding-inline-start:18px;font:10px/1.75 Consolas,ui-monospace,monospace;color:var(--rc-muted);overflow-wrap:anywhere}

/* the tables: the summary and every "the numbers" table */
.results-main table{width:100%;border-collapse:collapse;font-size:11px;font-variant-numeric:tabular-nums}
.results-main th,.results-main td{text-align:start;padding:6px 8px;border-bottom:1px solid var(--hairline);vertical-align:top}
.results-main th{font-size:10px;font-weight:600;color:var(--rc-muted)}

/* one experiment */
.rc-section{margin:0 0 28px;padding:20px 0 0;border-top:1px solid var(--line);scroll-margin-top:16px}
.rc-section h2{margin:0;font-size:17px;font-weight:650;line-height:1.4}
.rc-meta{margin:4px 0 0;font-size:10px;line-height:1.7;color:var(--rc-muted)}
.rc-plant{margin:10px 0 0;padding:7px 10px;border-inline-start:3px solid var(--rc-axis);border-radius:4px;background:var(--field-bg);font-size:11px;line-height:1.75;color:var(--ink-2)}
.rc-plant[data-state="forced"],.rc-plant[data-state="another"],.rc-plant[data-state="mixed"]{border-inline-start-color:var(--warn-ink);color:var(--rc-text)}
.rc-plant[data-state="same"],.rc-plant[data-state="same_code"]{border-inline-start-color:var(--rc-muted)}
.rc-plant-details,.rc-checks,.rc-unpaired{margin:6px 0 0;padding-inline-start:18px;font-size:10px;line-height:1.75;color:var(--rc-muted)}
.rc-plant-details:empty,.rc-checks:empty,.rc-unpaired:empty{display:none}
.rc-verdict{margin:14px 0 0;padding:12px 14px;background:var(--paper);border:1px solid var(--line);border-radius:10px}
.rc-verdict h3{margin-bottom:6px}
.rc-verdict[data-state="none"] .verdict-short{color:var(--rc-muted)}
.rc-verdict[data-state="missing"] .verdict-short,.rc-verdict[data-state="unavailable"] .verdict-short{color:var(--warn-ink)}
.rc-verdict details summary{cursor:pointer;font-size:10px;color:var(--rc-muted)}
.rc-notes{margin:12px 0 0;padding-block:10px;padding-inline:28px 12px;background:var(--seed-bg);border-radius:8px;font-size:11px;line-height:1.8;color:var(--ink-2)}
.rc-notes:empty{display:none}
.rc-note{margin:12px 0 0;font-size:11px;line-height:1.75;color:var(--rc-muted)}

/* one figure */
.rc-figure{margin:17px 0 0;padding:16px 18px 12px;min-width:0;background:var(--paper);border:1px solid var(--line);border-radius:12px;box-shadow:var(--shadow)}
.rc-what{margin:4px 0 8px;font-size:11px;line-height:1.75;color:var(--ink-2)}
.rc-axis-y{margin:0 0 2px;font-size:10px;color:var(--rc-muted)}
.rc-axis-x{margin:2px 0 6px;font-size:10px;color:var(--rc-muted);text-align:center}
.rc-legend{display:flex;flex-wrap:wrap;gap:4px 16px;margin:4px 0 8px;font-size:10px;line-height:1.6;color:var(--ink-2)}
.rc-legend>span{display:inline-flex;align-items:center;gap:6px}
.rc-swatch{display:inline-block;flex:none}
.rc-sw-dot{width:9px;height:9px;border-radius:50%;background:currentColor}
.rc-sw-square{width:9px;height:9px;background:currentColor}
.rc-sw-dash{width:16px;height:0;border-top:2px dashed currentColor}
.rc-sw-bracket{width:5px;height:12px;border:1.6px solid currentColor;border-inline-start:0}
.rc-table{margin-top:8px;padding-top:6px;max-width:100%;overflow-x:auto;border-top:1px solid var(--hairline)}
.rc-table summary{cursor:pointer;font-size:10px;color:var(--rc-muted)}
.rc-table table{margin-top:6px}
.rc-table td{font-family:Consolas,ui-monospace,monospace;white-space:nowrap}

/* the chart: the resets, then template.html's rules, renamed */
.rc-chart{position:relative;width:100%;height:auto;direction:ltr;touch-action:pan-y}
.rc-chart > svg{width:auto;height:auto;fill:#000;stroke:none;stroke-width:1;stroke-linecap:butt;stroke-linejoin:miter}
.rc-chart > svg{display:block;overflow:visible}
.rc-plot text{stroke:none;font-family:Consolas,ui-monospace,monospace;font-size:11px;fill:var(--rc-muted)}
.rc-plot .rc-lbl{font-weight:600}
.rc-plot .rc-grid line{stroke:var(--rc-grid);stroke-width:1}
.rc-plot .rc-axis{stroke:var(--rc-axis);stroke-width:1}
.rc-plot .rc-ln{fill:none;stroke-linejoin:round;stroke-linecap:round}
.rc-plot .rc-hit{fill:transparent;cursor:crosshair}
.rc-plot .rc-hair{stroke:var(--rc-muted);stroke-width:1;stroke-dasharray:3 3;pointer-events:none}
.rc-plot .rc-hdot{stroke:var(--rc-tip-bg);stroke-width:2;pointer-events:none}
.rc-plot .rc-dot{stroke:var(--rc-tip-bg);stroke-width:1.5}
.rc-plot .rc-mark{cursor:pointer}
.rc-plot .rc-mark:hover,.rc-plot .rc-mark:focus{filter:brightness(1.12)}
.rc-plot .rc-mark:focus{outline:none}
.rc-plot .rc-mark:focus-visible{stroke:var(--rc-text);stroke-width:2}
.rc-plot .rc-ring{fill:none;stroke:var(--rc-text);stroke-width:1.5;pointer-events:none}
.rc-plot .rc-pair{stroke:var(--rc-muted);stroke-opacity:.55;stroke-width:2;stroke-linecap:round}
.rc-plot .rc-band{fill:var(--rc-grid);opacity:.5}
.rc-plot .rc-mei{stroke:var(--rc-mei);stroke-width:1.6}
.rc-plot .rc-mei-label{fill:var(--rc-mei)}

/* the tooltip */
.rc-tip{position:absolute;z-index:5;pointer-events:none;min-width:130px;max-width:260px;padding:8px 10px;background:var(--rc-tip-bg);color:var(--rc-tip-fg);border:1px solid var(--line);border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,.14);font-size:11.5px;line-height:1.45;text-align:start}
.rc-tip .rc-tt{margin-bottom:4px;font-size:11px;line-height:1.35;color:var(--rc-muted)}
.rc-tip .rc-tr{display:flex;align-items:center;gap:7px;white-space:nowrap}
.rc-tip .rc-tr b{font:600 12.5px/1.4 Consolas,ui-monospace,monospace;font-variant-numeric:tabular-nums;color:var(--rc-tip-fg)}
.rc-tip .rc-tl{min-width:0;color:var(--rc-muted)}
.rc-tip .rc-tl{white-space:normal}
.rc-tip .rc-key{display:inline-block;width:12px;height:0;border-top:2.5px solid;flex:none}
html[dir=rtl] .rc-tip{direction:rtl}

/* < 760 px: phone. The nav row is agents.css's. */
@media(max-width:760px){
main.results-main{padding:18px 16px 0}
#summary,#not-read,.rc-figure{padding:12px}
.rc-section h2{font-size:15px}
.rc-verdict{padding:10px 12px}
}
```

- [ ] **Step 7: Run the test, then the whole node suite**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/charts-lib.test.mjs)
(cd app && node --test "static/sim/*.test.mjs")
```

Expected (observed in drafting): the first run prints `ℹ tests 17`, `ℹ pass 17`, `ℹ fail 0`. The whole suite
passes every test: its count is Task 6's total plus 17. In drafting it read 148 before Task 6, 175 with Task 6's
draft, and `ℹ tests 192`, `ℹ pass 192`, `ℹ fail 0` after this task.

- [ ] **Step 8: Byte-check the four files**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
for f in app/static/sim/charts-lib.mjs app/static/sim/charts-fake-dom.mjs app/static/sim/charts-lib.test.mjs app/static/sim/results.css; do
  "$PY" -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" "$f" || echo "FAILED: $f"
done
```

Expected (observed in drafting): `literal invisible: []` four times, and no `FAILED:` line.

- [ ] **Step 9: Commit, by explicit path**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
MSG="C:/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad/r1a_task07_commit.txt"
cat > "$MSG" <<'EOF'
Results tab R1a (task 7): the drawing library and the tab's stylesheet

charts-lib.mjs is a copy of the generic drawing code of
results/page/template.html (lines 747-978 and sideLabel), adapted as design
7.3 says: rc- classes, no axis titles in SVG, no role="img" around focusable
marks, a measured sideLabel, and createMounter (one ResizeObserver, one
document listener, an error hook, a teardown; a zero width never draws).
results.css: the --rc- palette in both themes (no red, no green), the resets
for the lab's element rules, template.html's chart rules renamed rc-, and the
page's own styles. charts-fake-dom.mjs is a test helper for node.

node --test static/sim/charts-lib.test.mjs: 17 of 17 pass.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
git add app/static/sim/charts-lib.mjs app/static/sim/charts-fake-dom.mjs app/static/sim/charts-lib.test.mjs app/static/sim/results.css
git commit -F "$MSG" -- app/static/sim/charts-lib.mjs app/static/sim/charts-fake-dom.mjs app/static/sim/charts-lib.test.mjs app/static/sim/results.css
git show --stat --oneline HEAD
```

Expected: `git add` may warn, once per file, that LF will be replaced by CRLF (`core.autocrlf=true`); the
commit lists exactly the four files, `4 files changed` (not run in drafting: drafting never commits).

### Task 8: The two R1a figures: layouts, tooltips, tables and draw steps (results-charts.mjs)

Each figure is a PURE layout function plus a thin draw step (design 7.1). The pairs chart: per seed, the
sighted and the blind agent's median damage as two marks joined by a line, the current-grade median as a
dashed reference (one line when every file prints the same value, one dash per seed otherwise), and the MEI
as a bracket the height of the MEI, labelled with the Latin `MEI` only (its meaning, and for Phase D "set
after this result", is HTML: `results.chart.mei`, `results.chart.mei_after`). The same chart without the knock
term reads `seed.thermal[role].median` and keeps only the seeds that recorded both arms. The hand-written
comparison: per seed, the five policies of the file side by side (squares for the three hand-written
policies, dots for the two agents). Nothing is computed but blind minus sighted per seed, which the analysis
scripts print (design 5.1). SVG text is numbers and `MEI` only; every word is HTML; `layout.svgLabels` lists
every string a draw step writes as SVG text and the test holds the draw steps to it on a fake DOM.

Neither file contains a `\u` escape or an invisible character (the test file builds LRI and PDI from code
points), so the Write tool can write them exactly as given; Step 5 byte-checks them.

**Files:**
- Create: `app/static/sim/results-charts.mjs`
- Test: `app/static/sim/results-charts.test.mjs`

**Interfaces:**
- Consumes:
  - Task 6, `'./results-format.mjs?v=R1a'`: `fmtNum(v, digits)`, `fmtSigned(v, digits)`, `fmtInt(v)`,
    `inline(lang, text)`; the test also reads `EM_DASH`, `MINUS`, `NNBSP`.
  - Task 6, `'./results-strings.mjs?v=R1a'` (merges into `i18n.STRINGS` on import; the test imports it):
    `results.legend.{sighted,blind,baseline,reactive,current_grade}`, `results.tip.{seed,median,worst,fuel,peak,diff}`,
    `results.table.{seed,sighted,blind,diff,sighted_worst,blind_worst,current_grade,baseline,reactive}`;
    `t(lang, key, vars)` from `'./i18n.mjs'` (no query: a shared lab module).
  - Task 7, `'./charts-lib.mjs?v=R1a'`: `S, T, plot, line, hline, markTip, fin, ticks`; the test uses
    `'./charts-fake-dom.mjs?v=R1a'`: `installFakeDocument, fakeHost, walk, svgTexts`.
  - Task 4's evaluation section (`GET /api/results`, state "ok"): `seeds[]` with `seed`, `sighted`, `blind`,
    `baseline`, `reactive`, `current_grade` (each `{ median, worst, fuel, peak, ... }` or null) and `thermal`
    (`{ role: { median, cut } }` or null); `mei`; `mei_after_result`.
- Produces, `app/static/sim/results-charts.mjs` (import it as `'./results-charts.mjs?v=R1a'`):
  - `ROLE_VAR = { sighted: 'var(--rc-sighted)', blind: 'var(--rc-blind)', baseline: 'var(--rc-baseline)',
    reactive: 'var(--rc-reactive)', current_grade: 'var(--rc-grade)' }`;
    `HAND_ROLES = ['baseline', 'reactive', 'current_grade', 'sighted', 'blind']`.
  - `pairsLayout(section, measure = 'total') -> { empty, measure, seeds: [int], x: { d: [-0.5, n - 0.5],
    ticks: [0..n-1] }, y: { d: [lo, hi], ticks: [number] }, marks: [{ i, seed, role, x, value, worst, fuel, peak }],
    links: [{ i, seed, a, b, diff }], reference: { role: 'current_grade', values: [number|null] } | null,
    mei: { value: number|null, afterResult: boolean }, svgLabels: [string] }`. Seeds ascending, both arms
    present (for 'thermal', both thermal arms); `worst`/`fuel`/`peak` are null for 'thermal'; `diff = b - a`;
    `hi = max(values, reference) * 1.08`, at least `2 * mei`; `lo = 0` (or the lowest value * 1.08, were one
    ever negative); throws on an unknown measure; `empty: true` (and every list empty) when no seed qualifies.
  - `handLayout(section) -> { empty, seeds, roles, x, y, marks: [{ i, seed, role, x, value, worst, fuel, peak }],
    svgLabels }`: per seed index `i`, one mark per role of `HAND_ROLES` that has a median, at
    `x = i + {-0.3, -0.15, 0, 0.15, 0.3}[role]`; `y.d = [0, max * 1.08]`; `roles` are the roles drawn, in order.
  - `pairsTip(layout, mark, lang)` and `handTip(layout, mark, lang) -> { title, rows: [{ c?, v, k }] }`: title
    `"<legend name> · <results.tip.seed>"`; rows: the median (with the role colour), then for 'total' the worst
    episode, median fuel and hottest turbine, then (pairs only) the pair's blind minus sighted; every value
    isolated in Arabic through `inline`.
  - `pairsTable(layout, lang)` and `handTable(layout, lang) -> { head: [string], rows: [[string]] }`: pairs columns
    seed, sighted, blind, blind minus sighted, (total only) sighted worst, blind worst, then current-grade;
    hand columns seed, then the five policies' medians in `HAND_ROLES` order; a missing value is an em dash;
    every cell isolated in Arabic.
  - `drawPairs(host, w, h, layout, lang)` and `drawHand(host, w, h, layout, lang)`: draw into `host` and return the
    `plot()` object, or `null` (nothing drawn) for an empty layout. Every mark is a `.rc-mark` (focusable, its tip
    from `pairsTip`/`handTip`). Neither passes `aria` to `plot()`: the host's own `aria-label`
    (`results.chart.aria.pairs` / `.hand`) names the chart.
  - For Task 9: mount each figure with `mounter.mount(host, (h, w, hh) => drawPairs(h, w, hh, layout, lang))`;
    mount the second pairs figure from `pairsLayout(section, 'thermal')` only when `section.thermal_recorded !==
    'none'` (its `seeds` are the seeds of `results.chart.thermal_some`); the legend of the pairs chart is sighted
    and blind (`rc-sw-dot`, `ROLE_VAR`), current-grade (`rc-sw-dash`) when `layout.reference`, and the MEI
    (`rc-sw-bracket`, `var(--rc-mei)`) with `results.chart.mei`, plus `results.chart.mei_after` when
    `layout.mei.afterResult`; the hand chart's legend uses `layout.roles`, `rc-sw-square` for the three
    hand-written policies and `rc-sw-dot` for the agents.

- [ ] **Step 1: Write the failing test**

Create `app/static/sim/results-charts.test.mjs` (its fixture is C4 as `results/c4_seed0..7.txt` print it,
listed out of order on purpose):

```js
// results-charts.mjs: the layouts of the pairs chart and of the hand-written
// comparison (pure), their tooltip and table rows in both languages, and the
// two draw steps on a fake DOM (charts-lib.mjs through charts-fake-dom.mjs).
// The fixture is C4 as results/c4_seed0..7.txt print it.
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './results-strings.mjs?v=R1a';
import { EM_DASH, MINUS, NNBSP } from './results-format.mjs?v=R1a';
import { installFakeDocument, fakeHost, walk, svgTexts } from './charts-fake-dom.mjs?v=R1a';
import {
  ROLE_VAR, HAND_ROLES, pairsLayout, handLayout, pairsTip, handTip, pairsTable, handTable,
  drawPairs, drawHand,
} from './results-charts.mjs?v=R1a';

// Built from code points, so no editor can turn them into look-alikes here.
const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const iso = text => `${LRI}${text}${PDI}`;
const ARABIC = new RegExp(`[${String.fromCodePoint(0x600)}-${String.fromCodePoint(0x6ff)}]`);

// [seed, sighted, blind]: median, IQR width, worst, median fuel, peak, as each
// results/c4_seed<N>.txt prints them. Out of order on purpose.
const C4_ROWS = [
  [3, [336.1, 179.8, 964.1, 5264, 876], [349.5, 154.0, 721.0, 5225, 863]],
  [0, [359.9, 156.9, 674.3, 5162, 868], [720.5, 492.6, 1453.7, 4726, 912]],
  [7, [365.5, 344.7, 890.4, 5157, 866], [363.1, 233.9, 979.8, 5294, 874]],
  [1, [490.2, 263.7, 900.0, 4827, 876], [409.9, 246.4, 811.1, 5161, 875]],
  [5, [442.6, 326.8, 1399.8, 4862, 895], [442.3, 251.8, 984.8, 4840, 878]],
  [2, [602.2, 350.9, 1165.3, 4726, 890], [524.4, 299.2, 1598.4, 4786, 910]],
  [6, [357.6, 246.4, 967.1, 5049, 878], [347.6, 267.6, 1018.3, 5105, 876]],
  [4, [332.8, 164.0, 868.4, 5099, 875], [371.0, 151.6, 816.6, 4934, 868]],
];
// The hand-written rows: every C4 file prints the same three.
const C4_HAND = {
  baseline: ['baseline ECU', [1118.0, 715.9, 2363.8, 4818, 924]],
  reactive: ['reactive', [667.8, 214.5, 919.8, 5040, 871]],
  current_grade: ['current-grade', [653.5, 295.5, 907.0, 5158, 871]],
};
const policy = (label, dir, [median, iqr, worst, fuel, peak]) => ({ label, dir, median, iqr, worst, fuel, peak });

// An evaluation section as GET /api/results sends it (app/results_data.py).
function c4Section() {
  return {
    id: 'exp-c4', kind: 'evaluation', state: 'ok', prefix: 'c4', name: 'C4',
    mei: 50, mei_after_result: false, thermal_recorded: 'none',
    seeds: C4_ROWS.map(([seed, s, b]) => ({
      seed,
      file: `results/c4_seed${seed}.txt`,
      sighted: policy(`agent runs_c4\\sighted_seed${seed}`, `runs_c4/sighted_seed${seed}`, s),
      blind: policy(`agent (blind) runs_c4\\blind_seed${seed}`, `runs_c4/blind_seed${seed}`, b),
      baseline: policy(C4_HAND.baseline[0], null, C4_HAND.baseline[1]),
      reactive: policy(C4_HAND.reactive[0], null, C4_HAND.reactive[1]),
      current_grade: policy(C4_HAND.current_grade[0], null, C4_HAND.current_grade[1]),
      thermal: null,
      diff: b[0] - s[0],
      budget: { steps: 300000, requested: 300000 },
    })),
  };
}
const SEEDS = [0, 1, 2, 3, 4, 5, 6, 7];
const inside = (v, [lo, hi]) => v >= lo && v <= hi;

test('ROLE_VAR gives every role a colour token of results.css, and HAND_ROLES orders them as the files do', () => {
  assert.deepEqual(HAND_ROLES, ['baseline', 'reactive', 'current_grade', 'sighted', 'blind']);
  assert.deepEqual(Object.keys(ROLE_VAR).sort(), [...HAND_ROLES].sort());
  assert.deepEqual(ROLE_VAR, {
    sighted: 'var(--rc-sighted)', blind: 'var(--rc-blind)', baseline: 'var(--rc-baseline)',
    reactive: 'var(--rc-reactive)', current_grade: 'var(--rc-grade)',
  });
});

test('pairsLayout: the C4 pairs in seed order, every value inside the y domain', () => {
  const section = c4Section();
  const L = pairsLayout(section);
  assert.equal(L.empty, false);
  assert.equal(L.measure, 'total');
  assert.deepEqual(L.seeds, SEEDS);
  assert.deepEqual(L.x, { d: [-0.5, 7.5], ticks: SEEDS });
  assert.deepEqual(L.y.d, [0, 720.5 * 1.08]);
  assert.deepEqual(L.y.ticks, [0, 200, 400, 600]);
  const rows = new Map(C4_ROWS.map(([seed, s, b]) => [seed, { sighted: s, blind: b }]));
  assert.equal(L.marks.length, 16);
  for (const m of L.marks) {
    assert.equal(m.seed, L.seeds[m.i]);
    const [median, , worst, fuel, peak] = rows.get(m.seed)[m.role];
    assert.deepEqual([m.value, m.worst, m.fuel, m.peak], [median, worst, fuel, peak], `seed ${m.seed} ${m.role}`);
    assert.ok(Math.abs(m.x - m.i - (m.role === 'sighted' ? -0.12 : 0.12)) < 1e-12);
    assert.ok(inside(m.value, L.y.d), `seed ${m.seed} ${m.role} ${m.value} outside ${L.y.d}`);
  }
  assert.deepEqual(L.links.map(l => l.seed), SEEDS);
  for (const l of L.links) {
    const seed = section.seeds.find(s => s.seed === l.seed);
    assert.equal(l.a, seed.sighted.median);
    assert.equal(l.b, seed.blind.median);
    assert.equal(l.diff, l.b - l.a, 'blind minus sighted');
    assert.equal(l.diff, seed.diff, `seed ${l.seed}: the section's own difference`);
  }
  // As analyse_c4.py prints them: 3 of 8 positive.
  assert.deepEqual(L.links.map(l => Math.round(l.diff * 10) / 10), [360.6, -80.3, -77.8, 13.4, 38.2, -0.3, -10, -2.4]);
  assert.deepEqual(L.reference, { role: 'current_grade', values: Array(8).fill(653.5) });
  for (const v of L.reference.values) assert.ok(inside(v, L.y.d));
  assert.deepEqual(L.mei, { value: 50, afterResult: false });
  assert.deepEqual(L.svgLabels, [...SEEDS.map(String), '0', '200', '400', '600', 'MEI']);
  for (const s of L.svgLabels) assert.doesNotMatch(s, ARABIC);
  const phaseD = { ...section, mei_after_result: true };
  assert.deepEqual(pairsLayout(phaseD).mei, { value: 50, afterResult: true });
});

test('pairsLayout: the y domain reaches at least twice the MEI, so the bracket fits', () => {
  const section = c4Section();
  for (const s of section.seeds) {
    s.sighted.median = 10;
    s.blind.median = 12;
    s.current_grade.median = 20;
  }
  assert.deepEqual(pairsLayout(section).y.d, [0, 100]);
  const noMei = { ...section, mei: null };
  const L = pairsLayout(noMei);
  assert.deepEqual(L.y.d, [0, 20 * 1.08]);
  assert.equal(L.mei.value, null);
  assert.ok(!L.svgLabels.includes('MEI'));
  // No damage median is below zero, but the domain would still hold one.
  section.seeds[0].blind.median = -5;
  const below = pairsLayout(section);
  assert.equal(below.y.d[0], -5 * 1.08);
  for (const m of below.marks) assert.ok(inside(m.value, below.y.d), `${m.value} outside ${below.y.d}`);
  const hand = handLayout(section);
  for (const m of hand.marks) assert.ok(inside(m.value, hand.y.d), `${m.value} outside ${hand.y.d}`);
});

test('pairsLayout thermal: only the seeds whose files recorded both arms; none at all is empty', () => {
  const section = c4Section();
  const bySeed = Object.fromEntries(section.seeds.map(s => [s.seed, s]));
  bySeed[0].thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 }, current_grade: { median: 600, cut: 40 } };
  bySeed[2].thermal = { sighted: { median: 280, cut: 62 }, blind: { median: 250, cut: 66 }, current_grade: { median: 600, cut: 40 } };
  bySeed[1].thermal = { sighted: { median: 290, cut: 61 } };
  const L = pairsLayout(section, 'thermal');
  assert.equal(L.measure, 'thermal');
  assert.deepEqual(L.seeds, [0, 2]);
  assert.deepEqual(L.x, { d: [-0.5, 1.5], ticks: [0, 1] });
  assert.deepEqual(L.marks.map(m => [m.seed, m.role, m.value]),
    [[0, 'sighted', 300], [0, 'blind', 310.5], [2, 'sighted', 280], [2, 'blind', 250]]);
  for (const m of L.marks) assert.deepEqual([m.worst, m.fuel, m.peak], [null, null, null], 'no thermal worst, fuel or peak is recorded');
  assert.deepEqual(L.links.map(l => l.diff), [10.5, -30]);
  assert.deepEqual(L.reference, { role: 'current_grade', values: [600, 600] });
  assert.deepEqual(L.y.d, [0, 600 * 1.08]);
  for (const m of L.marks) assert.ok(inside(m.value, L.y.d));
  const none = pairsLayout(c4Section(), 'thermal');
  assert.equal(none.empty, true);
  assert.deepEqual([none.seeds, none.marks, none.links, none.svgLabels], [[], [], [], []]);
  assert.equal(none.reference, null);
});

test('pairsLayout refuses a measure it does not know', () => {
  assert.throws(() => pairsLayout(c4Section(), 'cut'), /unknown measure "cut"/);
});

test('handLayout: five policies per seed at their offsets, every value inside the domain', () => {
  const L = handLayout(c4Section());
  assert.equal(L.empty, false);
  assert.deepEqual(L.seeds, SEEDS);
  assert.deepEqual(L.roles, HAND_ROLES);
  assert.deepEqual(L.x, { d: [-0.5, 7.5], ticks: SEEDS });
  assert.deepEqual(L.y.d, [0, 1118.0 * 1.08]);
  assert.equal(L.marks.length, 40);
  const offset = { baseline: -0.3, reactive: -0.15, current_grade: 0, sighted: 0.15, blind: 0.3 };
  for (const m of L.marks) {
    assert.ok(Math.abs(m.x - (m.i + offset[m.role])) < 1e-12, `${m.role} at ${m.x}`);
    assert.ok(inside(m.value, L.y.d));
    assert.equal(m.seed, L.seeds[m.i]);
  }
  assert.deepEqual(L.marks.slice(0, 5).map(m => [m.role, m.value]),
    [['baseline', 1118.0], ['reactive', 667.8], ['current_grade', 653.5], ['sighted', 359.9], ['blind', 720.5]]);
  assert.deepEqual(L.svgLabels, [...SEEDS.map(String), '0', '200', '400', '600', '800', '1000', '1200']);
  const section = c4Section();
  section.seeds.find(s => s.seed === 4).reactive = null;
  const fewer = handLayout(section);
  assert.equal(fewer.marks.length, 39);
  assert.ok(!fewer.marks.some(m => m.seed === 4 && m.role === 'reactive'), 'a missing policy is left out, never drawn at zero');
  assert.equal(handLayout({ seeds: [] }).empty, true);
});

test('pairsTip: the median, worst, fuel, peak and the pair\'s difference, isolated in Arabic', () => {
  const L = pairsLayout(c4Section());
  const sighted0 = L.marks.find(m => m.seed === 0 && m.role === 'sighted');
  const en = pairsTip(L, sighted0, 'en');
  assert.equal(en.title, 'Sighted agent · Seed 0');
  assert.deepEqual(en.rows, [
    { c: 'var(--rc-sighted)', v: '359.9', k: t('en', 'results.tip.median') },
    { v: '674.3', k: t('en', 'results.tip.worst') },
    { v: `5${NNBSP}162`, k: t('en', 'results.tip.fuel') },
    { v: '868', k: t('en', 'results.tip.peak') },
    { v: '+360.6', k: t('en', 'results.tip.diff') },
  ]);
  const ar = pairsTip(L, sighted0, 'ar');
  assert.equal(ar.title, `${t('ar', 'results.legend.sighted')} · ${t('ar', 'results.tip.seed', { seed: iso('0') })}`);
  assert.deepEqual(ar.rows.map(r => r.v), [iso('359.9'), iso('674.3'), iso(`5${NNBSP}162`), iso('868'), iso('+360.6')]);
  assert.deepEqual(ar.rows.map(r => r.k), ['median', 'worst', 'fuel', 'peak', 'diff'].map(k => t('ar', `results.tip.${k}`)));
  const blind1 = L.marks.find(m => m.seed === 1 && m.role === 'blind');
  assert.equal(pairsTip(L, blind1, 'en').rows[0].c, 'var(--rc-blind)');
  assert.equal(pairsTip(L, blind1, 'en').rows.at(-1).v, `${MINUS}80.3`);
  assert.equal(pairsTip(L, blind1, 'ar').rows.at(-1).v, iso(`${MINUS}80.3`));
  const section = c4Section();
  section.seeds.find(s => s.seed === 0).thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 } };
  const T = pairsLayout(section, 'thermal');
  assert.deepEqual(pairsTip(T, T.marks[0], 'en').rows,
    [{ c: 'var(--rc-sighted)', v: '300.0', k: t('en', 'results.tip.median') }, { v: '+10.5', k: t('en', 'results.tip.diff') }]);
});

test('handTip: each policy\'s median, worst, fuel and peak, the engine computer by its legend name', () => {
  const L = handLayout(c4Section());
  const base = L.marks.find(m => m.seed === 0 && m.role === 'baseline');
  const en = handTip(L, base, 'en');
  assert.equal(en.title, 'Engine computer (modelled) · Seed 0');
  assert.deepEqual(en.rows, [
    { c: 'var(--rc-baseline)', v: '1118.0', k: t('en', 'results.tip.median') },
    { v: '2363.8', k: t('en', 'results.tip.worst') },
    { v: `4${NNBSP}818`, k: t('en', 'results.tip.fuel') },
    { v: '924', k: t('en', 'results.tip.peak') },
  ]);
  const ar = handTip(L, base, 'ar');
  assert.equal(ar.title, `${t('ar', 'results.legend.baseline')} · ${t('ar', 'results.tip.seed', { seed: iso('0') })}`);
  assert.deepEqual(ar.rows.map(r => r.v), [iso('1118.0'), iso('2363.8'), iso(`4${NNBSP}818`), iso('924')]);
  const grade = L.marks.find(m => m.seed === 7 && m.role === 'current_grade');
  assert.equal(handTip(L, grade, 'en').rows[0].c, 'var(--rc-grade)');
});

test('pairsTable and handTable: headers from the strings, one row per seed, cells isolated in Arabic', () => {
  const L = pairsLayout(c4Section());
  const keys = ['seed', 'sighted', 'blind', 'diff', 'sighted_worst', 'blind_worst', 'current_grade'];
  const en = pairsTable(L, 'en');
  assert.deepEqual(en.head, keys.map(k => t('en', `results.table.${k}`)));
  assert.equal(en.rows.length, 8);
  assert.deepEqual(en.rows[0], ['0', '359.9', '720.5', '+360.6', '674.3', '1453.7', '653.5']);
  assert.deepEqual(en.rows[1], ['1', '490.2', '409.9', `${MINUS}80.3`, '900.0', '811.1', '653.5']);
  const ar = pairsTable(L, 'ar');
  assert.deepEqual(ar.head, keys.map(k => t('ar', `results.table.${k}`)));
  assert.deepEqual(ar.rows[1], en.rows[1].map(iso));
  const section = c4Section();
  section.seeds.find(s => s.seed === 0).thermal = { sighted: { median: 300, cut: 60 }, blind: { median: 310.5, cut: 58 } };
  const thermal = pairsTable(pairsLayout(section, 'thermal'), 'en');
  assert.deepEqual(thermal.head, ['seed', 'sighted', 'blind', 'diff', 'current_grade'].map(k => t('en', `results.table.${k}`)));
  assert.deepEqual(thermal.rows, [['0', '300.0', '310.5', '+10.5', EM_DASH]], 'no thermal current-grade recorded: a dash');
  const H = handLayout(c4Section());
  const hand = handTable(H, 'en');
  assert.deepEqual(hand.head, ['seed', 'baseline', 'reactive', 'current_grade', 'sighted', 'blind']
    .map(k => t('en', `results.table.${k}`)));
  assert.deepEqual(hand.rows.map(r => r[0]), SEEDS.map(String));
  assert.deepEqual(hand.rows[0], ['0', '1118.0', '667.8', '653.5', '359.9', '720.5']);
  assert.deepEqual(handTable(H, 'ar').rows[0], hand.rows[0].map(iso));
  const missing = c4Section();
  missing.seeds.find(s => s.seed === 0).reactive = null;
  assert.equal(handTable(handLayout(missing), 'en').rows[0][2], EM_DASH);
});

test('drawPairs writes exactly its layout\'s SVG labels, none of them Arabic, and one focusable mark per agent', () => {
  installFakeDocument();
  for (const lang of ['ar', 'en']) {
    const L = pairsLayout(c4Section());
    const host = fakeHost(640);
    const P = drawPairs(host, 640, 358, L, lang);
    assert.equal(P.svg.getAttribute('role'), null, 'the host, not the svg, carries the label');
    assert.deepEqual(svgTexts(host), L.svgLabels);
    for (const text of svgTexts(host)) assert.doesNotMatch(text, ARABIC, `${lang}: ${text}`);
    const marks = walk(host).filter(el => el.classes().includes('rc-mark'));
    assert.equal(marks.length, 16);
    marks.forEach((el, k) => {
      assert.equal(el.tagName, 'circle');
      assert.equal(el.getAttribute('tabindex'), '0');
      assert.equal(el.getAttribute('style'), `fill:${ROLE_VAR[L.marks[k].role]}`);
    });
    assert.equal(walk(host).filter(el => el.classes().includes('rc-pair')).length, 8, 'one link per pair');
    assert.equal(walk(host).filter(el => el.classes().includes('rc-mei')).length, 3, 'the MEI bracket');
    marks[0].dispatch('focus');
    const tipEl = host.querySelector(':scope > .rc-tip');
    assert.equal(tipEl.hidden, false);
    assert.equal(tipEl.children[0].textContent, pairsTip(L, L.marks[0], lang).title);
    assert.equal(tipEl.children[1].children[1].textContent, pairsTip(L, L.marks[0], lang).rows[0].v);
  }
});

test('drawPairs draws current-grade as one dashed line, or one dash per seed where the files differ', () => {
  installFakeDocument();
  const same = fakeHost(640);
  drawPairs(same, 640, 358, pairsLayout(c4Section()), 'en');
  const dashed = walk(same).filter(el => /stroke:var\(--rc-grade\)/.test(el.getAttribute('style') || ''));
  assert.deepEqual(dashed.map(el => el.tagName), ['line']);
  const section = c4Section();
  section.seeds.find(s => s.seed === 5).current_grade.median = 640.0;
  const differ = fakeHost(640);
  drawPairs(differ, 640, 358, pairsLayout(section), 'en');
  const path = walk(differ).find(el => el.tagName === 'path' && /--rc-grade/.test(el.getAttribute('style') || ''));
  assert.equal((path.getAttribute('d').match(/M/g) || []).length, 8);
});

test('drawHand writes exactly its SVG labels; squares for the hand-written policies, dots for the agents', () => {
  installFakeDocument();
  for (const lang of ['ar', 'en']) {
    const L = handLayout(c4Section());
    const host = fakeHost(900);
    drawHand(host, 900, 400, L, lang);
    assert.deepEqual(svgTexts(host), L.svgLabels);
    for (const text of svgTexts(host)) assert.doesNotMatch(text, ARABIC, `${lang}: ${text}`);
    const marks = walk(host).filter(el => el.classes().includes('rc-mark'));
    assert.equal(marks.length, 40);
    marks.forEach((el, k) => {
      const role = L.marks[k].role;
      assert.equal(el.tagName, role === 'sighted' || role === 'blind' ? 'circle' : 'rect', role);
      assert.equal(el.getAttribute('tabindex'), '0');
    });
    assert.equal(walk(host).filter(el => el.classes().includes('rc-band')).length, 4, 'every other seed banded');
    marks[2].dispatch('focus');
    assert.equal(host.querySelector(':scope > .rc-tip').children[0].textContent, handTip(L, L.marks[2], lang).title);
  }
});

test('an empty layout draws nothing', () => {
  installFakeDocument();
  const host = fakeHost(640);
  assert.equal(drawPairs(host, 640, 358, pairsLayout(c4Section(), 'thermal'), 'en'), null);
  assert.equal(drawHand(host, 640, 358, handLayout({ seeds: [] }), 'en'), null);
  assert.equal(host.children.length, 0);
});

test('no literal invisible character in the chart modules or their tests', () => {
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200e, 0x200f, 0x202f, 0x2212, 0x2011];
  for (const name of ['charts-lib.mjs', 'results-charts.mjs', 'charts-fake-dom.mjs', 'charts-lib.test.mjs', 'results-charts.test.mjs']) {
    const src = readFileSync(new URL(`./${name}`, import.meta.url), 'utf8');
    const found = [...src].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
    assert.deepEqual(found, [], `${name} carries a literal invisible character`);
  }
  const charts = readFileSync(new URL('./results-charts.mjs', import.meta.url), 'utf8');
  assert.doesNotMatch(charts, /#[0-9a-fA-F]{3,6}\b|rgba?\(/, 'a literal colour would not follow the theme');
});
```

- [ ] **Step 2: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/results-charts.test.mjs)
```

Expected: FAIL before any test runs: `Error [ERR_MODULE_NOT_FOUND]: Cannot find module
'...\app\static\sim\results-charts.mjs' imported from ...\app\static\sim\results-charts.test.mjs`, then
`ℹ tests 1`, `ℹ pass 0`, `ℹ fail 1` (observed in drafting).

- [ ] **Step 3: Write the layouts and the draw steps**

Create `app/static/sim/results-charts.mjs`:

```js
// The results tab's two R1a figures (/results): the pairs chart (each seed's
// sighted and blind agent, joined, beside current-grade and the MEI) and the
// comparison with the hand-written policies from the same files.
//
// Each figure is a PURE layout function (domains, marks, tooltip rows, table
// rows), tested under node without a browser, and a thin draw step that turns
// a layout into SVG through charts-lib.mjs. Nothing here computes a statistic:
// every value is a median, a worst episode, a fuel or a peak that a result
// file records (GET /api/results), and the one difference, blind minus sighted
// per seed, is the one the analysis scripts print (design 5.1). No mean, no
// winner, nothing summed or averaged across experiments.
//
// SVG text holds numbers and the Latin "MEI" only. Every word of a figure, in
// either language, is HTML (the title, the axis titles, the legend, the
// tooltip, the table), so the bidi algorithm never reorders a chart label
// (design 7.3). layout.svgLabels lists every string a draw step writes as SVG
// text, and results-charts.test.mjs holds both draw steps to it.
//
// Every mark carries its x, and y carries its ticks, so a layout knows every
// SVG label before anything is drawn; handLayout also lists the roles it drew,
// for the legend.
import { t } from './i18n.mjs';
import { fmtNum, fmtSigned, fmtInt, inline } from './results-format.mjs?v=R1a';
import { S, T, plot, line, hline, markTip, fin, ticks } from './charts-lib.mjs?v=R1a';

export const ROLE_VAR = {
  sighted: 'var(--rc-sighted)', blind: 'var(--rc-blind)',
  baseline: 'var(--rc-baseline)', reactive: 'var(--rc-reactive)', current_grade: 'var(--rc-grade)',
};
export const HAND_ROLES = ['baseline', 'reactive', 'current_grade', 'sighted', 'blind'];

const MEASURES = ['total', 'thermal'];
// The sighted mark sits this far left of its seed and the blind one this far
// right, so two close medians never hide each other.
const PAIR_DX = 0.12;
const HAND_DX = { baseline: -0.3, reactive: -0.15, current_grade: 0, sighted: 0.15, blind: 0.3 };
const AGENTS = new Set(['sighted', 'blind']);
const Y_TICKS = 5;
const SEP = ' · ';
const HAND_HEAD = {
  baseline: 'results.table.baseline', reactive: 'results.table.reactive',
  current_grade: 'results.table.current_grade', sighted: 'results.table.sighted', blind: 'results.table.blind',
};

const orNull = v => (fin(v) ? v : null);
const medianOf = p => (p && fin(p.median) ? p.median : null);
const valueOf = (seed, role, measure) =>
  (measure === 'thermal' ? medianOf(seed?.thermal?.[role]) : medianOf(seed?.[role]));
const seedsOf = section => (section?.seeds || []).filter(s => s && Number.isInteger(s.seed));

// Zero (or the lowest value, were one ever below zero) to the highest value
// plus 8 %; with an MEI, at least twice the MEI, so its bracket always fits.
function yDomain(values, mei) {
  const vals = values.filter(fin);
  const lo = Math.min(0, ...vals);
  let hi = Math.max(0, ...vals) * 1.08;
  if (fin(mei) && mei > 0) hi = Math.max(hi, 2 * mei);
  if (!(hi > lo)) hi = lo + 1;
  return [lo < 0 ? lo * 1.08 : 0, hi];
}

// One format for every tick of an axis: as many decimals as the finest tick.
function tickFormat(yt) {
  const digits = Math.max(0, ...yt.map(v => (String(v).split('.')[1] || '').length));
  return v => fmtNum(v, Math.min(digits, 3));
}

function axes(seeds, yd) {
  const yt = seeds.length ? ticks(yd[0], yd[1], Y_TICKS) : [];
  return {
    x: { d: [-0.5, seeds.length - 0.5], ticks: seeds.map((_, i) => i) },
    y: { d: yd, ticks: yt },
    labels: seeds.length ? [...seeds.map(String), ...yt.map(tickFormat(yt))] : [],
  };
}

/**
 * The pairs of one evaluation section. measure 'total' reads each policy's
 * median damage; 'thermal' reads the median without the knock term
 * (seed.thermal[role].median) and keeps only the seeds whose files recorded it
 * for both arms. Seeds ascending; a seed without both arms is not drawn (the
 * section lists it as unpaired).
 */
export function pairsLayout(section, measure = 'total') {
  if (!MEASURES.includes(measure)) throw new Error(`pairsLayout: unknown measure "${measure}"`);
  const total = measure === 'total';
  const rows = seedsOf(section)
    .map(s => ({ s, a: valueOf(s, 'sighted', measure), b: valueOf(s, 'blind', measure) }))
    .filter(r => r.a !== null && r.b !== null)
    .sort((p, q) => p.s.seed - q.s.seed);
  const seeds = rows.map(r => r.s.seed);
  const marks = [];
  const links = [];
  rows.forEach(({ s, a, b }, i) => {
    for (const [role, value, dx] of [['sighted', a, -PAIR_DX], ['blind', b, PAIR_DX]]) {
      const p = s[role] || {};
      marks.push({
        i, seed: s.seed, role, x: i + dx, value,
        worst: total ? orNull(p.worst) : null,
        fuel: total ? orNull(p.fuel) : null,
        peak: total ? orNull(p.peak) : null,
      });
    }
    links.push({ i, seed: s.seed, a, b, diff: b - a });
  });
  const refs = rows.map(({ s }) => valueOf(s, 'current_grade', measure));
  const reference = refs.some(v => v !== null) ? { role: 'current_grade', values: refs } : null;
  const mei = { value: orNull(section?.mei), afterResult: Boolean(section?.mei_after_result) };
  const ax = axes(seeds, yDomain([...rows.flatMap(r => [r.a, r.b]), ...refs], mei.value));
  return {
    empty: seeds.length === 0, measure, seeds,
    x: ax.x, y: ax.y, marks, links, reference, mei,
    svgLabels: seeds.length ? [...ax.labels, ...(mei.value !== null ? ['MEI'] : [])] : [],
  };
}

/**
 * Every policy of each seed's file, side by side: per seed index i, one mark
 * per role of HAND_ROLES that has a median, at x = i + its offset.
 */
export function handLayout(section) {
  const rows = seedsOf(section).sort((p, q) => p.seed - q.seed);
  const seeds = rows.map(s => s.seed);
  const marks = [];
  rows.forEach((s, i) => {
    for (const role of HAND_ROLES) {
      const p = s[role];
      const value = medianOf(p);
      if (value === null) continue;
      marks.push({ i, seed: s.seed, role, x: i + HAND_DX[role], value,
        worst: orNull(p.worst), fuel: orNull(p.fuel), peak: orNull(p.peak) });
    }
  });
  const ax = axes(marks.length ? seeds : [], yDomain(marks.map(m => m.value), null));
  return {
    empty: marks.length === 0, seeds: marks.length ? seeds : [],
    roles: HAND_ROLES.filter(r => marks.some(m => m.role === r)),
    x: ax.x, y: ax.y, marks, svgLabels: ax.labels,
  };
}

// "<role> · Seed <n>": two labels side by side, the seed number isolated in
// Arabic like every number in an Arabic line.
function tipTitle(role, seed, lang) {
  return `${t(lang, `results.legend.${role}`)}${SEP}${t(lang, 'results.tip.seed', { seed: inline(lang, String(seed)) })}`;
}
function medianRow(mark, lang) {
  return { c: ROLE_VAR[mark.role], v: inline(lang, fmtNum(mark.value, 1)), k: t(lang, 'results.tip.median') };
}
function detailRows(mark, lang) {
  return [
    { v: inline(lang, fmtNum(mark.worst, 1)), k: t(lang, 'results.tip.worst') },
    { v: inline(lang, fmtInt(mark.fuel)), k: t(lang, 'results.tip.fuel') },
    { v: inline(lang, fmtInt(mark.peak)), k: t(lang, 'results.tip.peak') },
  ];
}

/** The tooltip of one pairs mark: its median, (total only) worst, fuel, peak, and its pair's blind minus sighted. */
export function pairsTip(layout, mark, lang) {
  const rows = [medianRow(mark, lang)];
  if (layout.measure === 'total') rows.push(...detailRows(mark, lang));
  const link = layout.links.find(l => l.i === mark.i);
  if (link) rows.push({ v: inline(lang, fmtSigned(link.diff, 1)), k: t(lang, 'results.tip.diff') });
  return { title: tipTitle(mark.role, mark.seed, lang), rows };
}

/** The tooltip of one mark of the hand-written comparison. */
export function handTip(layout, mark, lang) {
  return { title: tipTitle(mark.role, mark.seed, lang), rows: [medianRow(mark, lang), ...detailRows(mark, lang)] };
}

/** "The numbers" under the pairs chart: one row per drawn seed. */
export function pairsTable(layout, lang) {
  const total = layout.measure === 'total';
  const head = ['results.table.seed', 'results.table.sighted', 'results.table.blind', 'results.table.diff',
    ...(total ? ['results.table.sighted_worst', 'results.table.blind_worst'] : []),
    'results.table.current_grade'].map(k => t(lang, k));
  const rows = layout.links.map(l => {
    const worst = role => layout.marks.find(m => m.i === l.i && m.role === role)?.worst ?? null;
    const ref = layout.reference ? layout.reference.values[l.i] : null;
    return [String(l.seed), fmtNum(l.a, 1), fmtNum(l.b, 1), fmtSigned(l.diff, 1),
      ...(total ? [fmtNum(worst('sighted'), 1), fmtNum(worst('blind'), 1)] : []),
      fmtNum(ref, 1)].map(text => inline(lang, text));
  });
  return { head, rows };
}

/** "The numbers" under the hand-written comparison: every policy's median per seed. */
export function handTable(layout, lang) {
  const head = ['results.table.seed', ...HAND_ROLES.map(r => HAND_HEAD[r])].map(k => t(lang, k));
  const rows = layout.seeds.map((seed, i) => [String(seed), ...HAND_ROLES.map(role => {
    const m = layout.marks.find(x => x.i === i && x.role === role);
    return fmtNum(m ? m.value : null, 1);
  })].map(text => inline(lang, text)));
  return { head, rows };
}

function frame(host, w, h, layout, right) {
  return plot(host, {
    w, h,
    x: { d: layout.x.d, ticks: layout.x.ticks, fmt: i => String(layout.seeds[i]) },
    y: { d: layout.y.d, ticks: layout.y.ticks, fmt: tickFormat(layout.y.ticks) },
    xgrid: false,
    m: { t: 12, r: right, b: 28, l: 52 },
  });
}

// The MEI as a length beside the plot: a bracket as tall as the MEI, labelled
// with the Latin abbreviation only; the HTML legend says what it is.
function drawMei(P, layout) {
  const mei = layout.mei.value;
  const lo = Math.max(layout.y.d[0], 0);
  const base = lo + (layout.y.d[1] - lo - mei) * 0.25;
  const x = P.W - P.m.r + 14;
  const y0 = P.y(base), y1 = P.y(base + mei);
  S('line', { x1: x, x2: x, y1: y0, y2: y1, class: 'rc-mei' }, P.top);
  S('line', { x1: x - 4, x2: x + 4, y1: y0, y2: y0, class: 'rc-mei' }, P.top);
  S('line', { x1: x - 4, x2: x + 4, y1: y1, y2: y1, class: 'rc-mei' }, P.top);
  T(P.top, x + 7, (y0 + y1) / 2 + 4, 'MEI', { class: 'rc-lbl rc-mei-label' });
}

/** The pairs chart into `host` at w x h. Returns the plot, or null for an empty layout. */
export function drawPairs(host, w, h, layout, lang) {
  if (!layout || layout.empty) return null;
  const P = frame(host, w, h, layout, w < 520 ? 46 : 64);
  const ref = layout.reference;
  if (ref) {
    const style = { c: ROLE_VAR.current_grade, w: 1.6, dash: '6 4' };
    const vals = ref.values.filter(fin);
    if (vals.length === ref.values.length && vals.every(v => v === vals[0])) {
      hline(P, vals[0], style);
    } else {
      const xs = [], ys = [];
      ref.values.forEach((v, i) => { xs.push(i - 0.42, i + 0.42, NaN); ys.push(v, v, NaN); });
      line(P, xs, ys, style);
    }
  }
  for (const l of layout.links) {
    S('line', { x1: P.x(l.i - PAIR_DX), y1: P.y(l.a), x2: P.x(l.i + PAIR_DX), y2: P.y(l.b), class: 'rc-pair' }, P.g);
  }
  const r = Math.max(3.5, Math.min(6.5, (P.pw / Math.max(1, layout.seeds.length)) * 0.09));
  for (const m of layout.marks) {
    const cx = P.x(m.x), cy = P.y(m.value);
    const dot = S('circle', { cx, cy, r, class: 'rc-dot', style: `fill:${ROLE_VAR[m.role]}` }, P.g);
    const tipRows = pairsTip(layout, m, lang);
    markTip(P, dot, cx, cy, tipRows.title, tipRows.rows);
  }
  if (layout.mei.value !== null) drawMei(P, layout);
  return P;
}

/** The hand-written comparison into `host` at w x h. Returns the plot, or null for an empty layout. */
export function drawHand(host, w, h, layout, lang) {
  if (!layout || layout.empty) return null;
  const P = frame(host, w, h, layout, 16);
  layout.seeds.forEach((_, i) => {
    if (i % 2) S('rect', { x: P.x(i - 0.5), y: P.m.t, width: P.x(i + 0.5) - P.x(i - 0.5), height: P.ph, class: 'rc-band' }, P.g);
  });
  const r = Math.max(2.5, Math.min(5.5, (P.pw / Math.max(1, layout.seeds.length)) * 0.06));
  for (const m of layout.marks) {
    const cx = P.x(m.x), cy = P.y(m.value);
    const style = `fill:${ROLE_VAR[m.role]}`;
    const el = AGENTS.has(m.role)
      ? S('circle', { cx, cy, r, class: 'rc-dot', style }, P.g)
      : S('rect', { x: cx - r, y: cy - r, width: 2 * r, height: 2 * r, class: 'rc-dot', style }, P.g);
    const tipRows = handTip(layout, m, lang);
    markTip(P, el, cx, cy, tipRows.title, tipRows.rows);
  }
  return P;
}
```

- [ ] **Step 4: Run the test, the tab's node tests, and the whole node suite**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/results-charts.test.mjs)
(cd app && node --test "static/sim/results-*.test.mjs")
(cd app && node --test "static/sim/*.test.mjs")
```

Expected (observed in drafting, with Task 6's draft in place): `ℹ tests 14`, `ℹ pass 14`, `ℹ fail 0`; then the
`results-*` glob, Task 6's two files plus this one, `ℹ tests 41`, `ℹ pass 41`, `ℹ fail 0` (Task 6's own count
plus 14); then the whole suite `ℹ tests 206`, `ℹ pass 206`, `ℹ fail 0` (Task 7's total plus 14).

- [ ] **Step 5: Byte-check the two files**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
for f in app/static/sim/results-charts.mjs app/static/sim/results-charts.test.mjs; do
  "$PY" -c "import re,sys; s=open(sys.argv[1],encoding='utf-8').read(); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print('literal invisible:', bad); sys.exit(1 if bad else 0)" "$f" || echo "FAILED: $f"
done
```

Expected (observed in drafting): `literal invisible: []` twice, and no `FAILED:` line.

- [ ] **Step 6: Commit, by explicit path**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
MSG="C:/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad/r1a_task08_commit.txt"
cat > "$MSG" <<'EOF'
Results tab R1a (task 8): the pairs chart and the hand-written comparison

results-charts.mjs: pure layouts (pairsLayout, total and without the knock
term; handLayout), their tooltip and table rows in both languages, and two
thin draw steps through charts-lib.mjs. SVG text is numbers and MEI only;
layout.svgLabels lists it and the test holds the draw steps to it on a fake
DOM. Nothing is computed but blind minus sighted per seed, which the
analysis scripts print.

node --test static/sim/results-charts.test.mjs: 14 of 14 pass.

Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>
EOF
git add app/static/sim/results-charts.mjs app/static/sim/results-charts.test.mjs
git commit -F "$MSG" -- app/static/sim/results-charts.mjs app/static/sim/results-charts.test.mjs
git show --stat --oneline HEAD
```

Expected: `git add` may warn that LF will be replaced by CRLF; the commit lists exactly the two files,
`2 files changed` (not run in drafting: drafting never commits).

### Task 9: The page: its view helpers, its frame, its boot module, and the nav link

The tab a person opens. `results-view.mjs` decides what every line of a section says, in Arabic or English, from the values `GET /api/results` sent (pure, tested under Node). `results.html` is the frame, copied from `agents.html` (pre-paint script, icon library, top bar, nav, the two toggles, footer), with no figure in it. `results.mjs` is the only file that touches the DOM: it fetches `/api/results` once, builds the summary and one `article.rc-section` per experiment, mounts each chart through Task 7's mounter and Task 8's draw steps, rebuilds everything on a language switch and redraws nothing on a theme switch. Then the lab's two pages gain the third nav link, and their two pinned nav tests move in the same commit (spec 7.4).

**What drafting found, and this task carries:**

- **The phone row (spec 7.4's condition is met).** Measured in headless Chrome in a 390 px frame: with the fifth link, `/simulation`'s top bar runs wider than the screen, so the page scrolls sideways by 33 px in English and 1 px in Arabic (0 px before the link). So this task also appends to `app/static/sim/style.css` the own-row rule `agents.css` already has for `/agents`; with it, all three lab pages measure 0 px. The browser check of Task 10 measures it again.
- **No CSS of its own otherwise.** Task 7's `results.css` styles every id and class this page builds (`#built`, `#warnings`, `#summary`, `#not-read`, `.rc-section`, `.rc-meta`, `.rc-plant`, `.rc-verdict`, `.rc-notes`, `.rc-note`, `.rc-figure`, `.rc-what`, `.rc-axis-y`, `.rc-axis-x`, `.rc-legend` and its swatches `rc-sw-dot`, `rc-sw-square`, `rc-sw-dash`, `rc-sw-bracket`, `.rc-table`); the verdict's `.verdict-short`, `.verdict-cells` and `.quote` are `agents.css`'s.
- **The chart host is `role="group"`, not `role="img"`.** Spec 7.3: the focusable marks are not placed inside `role=img`; Task 7's `plot()` writes no `role="img"` either. The host carries the translated `aria-label`.
- **The markup's Arabic is Task 6's.** Before the script runs, the page reads in Arabic, so each `data-i18n` element holds its Arabic string; `results-page.test.mjs` fails if one differs from `STRINGS.ar`. An isolate in the markup is written `&#x2066;`...`&#x2069;`, never as the character.

**The escape rule.** No file of this task contains a backslash-u escape, a doubled backslash or a literal invisible character: the tests build LRI, PDI, NNBSP and MINUS from code points, and the markup writes an isolate as a character reference. So the Write tool and the Edit tool can create and edit each one exactly as given here; Step 13 byte-checks them. No file here is typed through a Bash heredoc (the Bash tool collapses a doubled backslash).

**Files:**
- Create: `app/static/sim/results-view.mjs`
- Create: `app/static/sim/results.mjs`
- Create: `app/static/results.html`
- Modify: `app/static/simulation.html:39` (the `<nav>` line: one link inserted)
- Modify: `app/static/agents.html:35` (the `<nav>` line: one link inserted)
- Modify: `app/static/sim/style.css` (a block appended after its last line, `body.limit-near .world-panel{...}`, line 163)
- Modify: `app/test_results.py` (`class PageTests` added above the file's last two lines)
- Modify: `app/test_agents.py:3778-3802` (`PageTests.test_the_lab_links_to_agents_where_phones_keep_it`, the nav pin)
- Modify: `app/static/sim/agents-page.test.mjs:100-109` (the nav pin)
- Test: `app/static/sim/results-view.test.mjs` (new), `app/static/sim/results-page.test.mjs` (new), `app/test_results.py` `PageTests`

**Interfaces:**
- Consumes:
  - Task 5: `mount_results(app, build=None)` from `app.results_api` (`GET /results` reads `app/static/results.html` on every request, `no-store`, 403 for a foreign `Host`).
  - Task 4's answer (contract 2.3, 3): `{built: {head, python, plant_sha, restart_needed, derived_loaded_differs, git, elapsed_ms}, import_failures: [{module, type}], sections: [...], not_read: [{path, reason, type}]}`; an "ok" section `{id, kind, state, prefix, name, known, order, continues, protocol, episodes, frozen, scenario, seeds, unpaired, mei, mei_after_result, thermal_recorded, verdict, notes, provenance, checks, error}`; an "unavailable" one `{id, kind, state, prefix, name, order, error: {kind, file, command, type, module}}`; `provenance` is `section_provenance`'s `{state, reason, tag, commits, files: {seed: classify_eval(...)}}` (contract 2.2).
  - Task 6: `'./results-format.mjs?v=R1a'` `EM_DASH`, `MINUS`, `fmtInt(v)`, `inline(lang, text)`; `'./results-strings.mjs?v=R1a'` (its import merges every `results.*` key into `STRINGS`; imported ONCE, by `results.mjs`); `nav.results` in `i18n.mjs`; `t`, `LANGS`, `DEFAULT_LANG`, `resolveLang`, `applyTranslations` from `'./i18n.mjs'`. Task 6's slot convention: its Arabic lines isolate single-value slots themselves; `{name}`, `{other}`, `{have}`, `{list}`, `{seeds}` are bare and the caller isolates each Latin item (this task's `nameSlot`).
  - Task 7: `createMounter({ onError })` from `'./charts-lib.mjs?v=R1a'` (`mount(host, draw, hOf)`, `clear()`; `onError(host, err)` may run again on a resize, so the note it writes replaces its previous one); `results.css?v=R1a`.
  - Task 8: `ROLE_VAR`, `HAND_ROLES`, `pairsLayout(section, measure)`, `handLayout(section)` (with `roles`), `pairsTable(layout, lang)`, `handTable(layout, lang)`, `drawPairs(host, w, h, layout, lang)`, `drawHand(host, w, h, layout, lang)` from `'./results-charts.mjs?v=R1a'`.
- Produces:
  - `app/static/sim/results-view.mjs` (contract 4.5, all pure, all `(…, lang) -> string | object`): `sectionName(section, lang)`, `plantView(prov, lang) -> {state, text, details: [string]}`, `verdictView(verdict, lang) -> {state, short, cells: [{cell, gloss}], lines: [{cite, text}]}` (`cite` is `results/<file>:<line>`, or `<first>-<last>` for a quote of several lines, as `/agents` cites), `noteItems(notes, lang) -> [string]`, `summaryRows(payload, lang) -> [{id, name, plant, verdict, markers: [string]}]`, `unavailableText(error, lang)`, `notReadItems(notRead, lang) -> [{path, reason}]`, `builtView(built, failures, lang) -> {line, warnings: [string]}`, `checkItems(checks, lang) -> [string]`; and, beyond the contract, `nameSlot(section, lang)` (the name for a bare `{name}`/`{other}` slot), `metaText(section, lang)` (`results.section.meta`), `unpairedItems(unpaired, lang) -> [string]`, `thermalNote(section, lang) -> string | null`, `meiLines(section, lang) -> [string]`.
  - `app/static/results.html`: the static ids `error`, `built`, `warnings`, `summary`, `summary-rows`, `sections`, `not-read`, `not-read-list`, `theme-toggle`, `lang-toggle`, `footer-index` (every one but `footer-index` is read by `results.mjs`; `footer-index` carries `results.footer.index` for `applyTranslations`), and the icon symbols `i-sun`, `i-moon`.
  - The DOM `results.mjs` builds, per section: `article.rc-section#exp-<prefix>[data-state]` > `h2`, `p.rc-meta` (the header facts), `p.rc-meta` per summary marker, `p.rc-meta.rc-scenario[dir=ltr]`, `p.rc-plant[data-state]` > `b` + `span`, `ul.rc-plant-details`, `ul.rc-checks`, `section.rc-verdict[data-state]` > `h3`, `p.verdict-short`, `ul.verdict-cells` > `li` > `b.cell[dir=ltr]` + `span.gloss`, `details.rc-verdict-lines` > `figure.quote` > `pre[dir=ltr]` + `figcaption[dir=ltr]`; `p.rc-note.rc-notes-heading` > `b`, `ul.rc-notes`; per figure `figure.rc-figure[data-figure=pairs|pairs-thermal|hand]` > `h3`, `p.rc-what`, (`p.rc-note`), `div.rc-axis-y`, `div.rc-chart[role=group][aria-label]`, `div.rc-axis-x`, `div.rc-legend` > `span.rc-legend-item` > `i.rc-swatch.rc-sw-*` + `span`, `details.rc-table` > `summary` + `table`; and `ul.rc-unpaired`. The browser check of Task 10 reads `.rc-section`, `.rc-verdict .verdict-short`, `.rc-chart > svg`, `.rc-mark`, `.rc-tip`, `[data-figure="hand"]`, `#summary-rows tr`, `#error`, `#summary`, `#built`.

- [ ] **Step 1: Write the failing test for the view helpers**

Create `app/static/sim/results-view.test.mjs` with the Write tool:

```js
// results-view.mjs, without a browser: which string each line of a section
// uses, which values go into it, and that every value inside an Arabic
// sentence sits in a left-to-right isolate. English is asserted as the
// contract writes it; Arabic through t() with the isolated values, so these
// tests check the choice and the isolation, not the Arabic wording (which
// results-strings.test.mjs owns).
import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { t } from './i18n.mjs';
import './results-strings.mjs?v=R1a';
import {
  sectionName, nameSlot, metaText, plantView, verdictView, noteItems, summaryRows, unavailableText,
  notReadItems, builtView, checkItems, unpairedItems, thermalNote, meiLines,
} from './results-view.mjs?v=R1a';

const LRI = String.fromCodePoint(0x2066);
const PDI = String.fromCodePoint(0x2069);
const NNBSP = String.fromCodePoint(0x202f);
const MINUS = String.fromCodePoint(0x2212);
const EM_DASH = String.fromCodePoint(0x2014);
const iso = s => `${LRI}${s}${PDI}`;

// One file's classify_eval answer, as contract 2.2 shapes it.
function file(seed, over = {}) {
  return {
    state: 'another', reason: null, route: 'same_python', protocol: 'd2',
    recorded: { plant_sha: 'b5a3069f32a83754', python: '3.12.10', git_head: 'c5a5341548040f69', derived_sha: null },
    live: { plant_sha: 'c236a8db3e201090', python: '3.12.10' },
    differs: ['plant_sha'], tag: 'sep17-before-merge', forced: [],
    file: { rel: `results/c4_seed${seed}.txt`, commit: { short: 'a3a048e', date: '2026-09-22T03:02:51+03:00' }, changed: false },
    ...over,
  };
}
const PROV = {
  state: 'another', reason: null, tag: 'sep17-before-merge', commits: ['c5a5341'],
  files: { 0: file(0), 1: file(1) },
};
const VERDICT = {
  state: 'found',
  lines: [
    { key: 'result', file: 'C4_RESULT.txt', line: 40, text: '  RESULT: SMALLER THAN THE MEI' },
    { key: 'seeds', file: 'C4_RESULT.txt', line: 30, text: 'a\nb\nc' },
  ],
  missing: [],
  short: { ar: 'نص قصير', en: 'smaller than the MEI (50) at 300 000 steps' },
  cells: [{ cell: 'SMALLER THAN THE MEI', gloss: { ar: 'شرح', en: 'Preview effect below the threshold' } }],
};
function section(prefix, over = {}) {
  return {
    id: `exp-${prefix}`, kind: 'evaluation', state: 'ok', prefix, name: { phase_d: 'Phase D', d2: 'Phase D2', c4: 'C4' }[prefix] ?? null,
    known: true, order: 0, continues: null, protocol: 'd2', episodes: 20, frozen: '22 Sep 2026', scenario: 'climb',
    seeds: [], unpaired: [], mei: 50, mei_after_result: false, thermal_recorded: 'none',
    verdict: VERDICT, notes: [], provenance: PROV, checks: [], error: null, ...over,
  };
}

test('a section is named by run_phase_d, or by its prefix said to have no name; a name slot isolates only Latin', () => {
  assert.equal(sectionName(section('c4'), 'en'), 'C4');
  assert.equal(sectionName(section('zz', { name: null }), 'en'), 'zz (no name recorded)');
  assert.equal(sectionName(section('zz', { name: null }), 'ar'), t('ar', 'results.section.no_name', { prefix: iso('zz') }));
  // For a bare {name} slot: a recorded (Latin) name isolated, the no-name line as it is.
  assert.equal(nameSlot(section('c4'), 'ar'), iso('C4'));
  assert.equal(nameSlot(section('c4'), 'en'), 'C4');
  assert.equal(nameSlot(section('zz', { name: null }), 'ar'), sectionName(section('zz', { name: null }), 'ar'));
});

test('the meta line carries the header facts, isolated in Arabic', () => {
  assert.equal(metaText(section('c4'), 'en'), '20 frozen episodes · frozen 22 Sep 2026 · protocol d2');
  assert.equal(metaText(section('c4'), 'ar'),
    t('ar', 'results.section.meta', { episodes: iso('20'), frozen: iso('22 Sep 2026'), protocol: iso('d2') }));
  assert.equal(metaText(section('phase_d', { protocol: null }), 'en'), `20 frozen episodes · frozen 22 Sep 2026 · protocol ${EM_DASH}`);
});

test('a common plant state lists both hashes, the tag, the commits and each file commit once', () => {
  const v = plantView(PROV, 'en');
  assert.equal(v.state, 'another');
  assert.equal(v.text, 'Made on another plant');
  assert.deepEqual(v.details, [
    'recorded b5a3069f32a83754 · this tree c236a8db3e201090',
    'the plant of sep17-before-merge',
    'from commits c5a5341',
    'last commit a3a048e (2026-09-22T03:02:51+03:00)',
  ]);
  const ar = plantView(PROV, 'ar');
  assert.equal(ar.text, t('ar', 'results.plant.another'));
  assert.equal(ar.details[0], t('ar', 'results.plant.hashes', { recorded: iso('b5a3069f32a83754'), live: iso('c236a8db3e201090') }));
  assert.equal(ar.details[3], t('ar', 'results.plant.committed', { commit: iso('a3a048e'), date: iso('2026-09-22T03:02:51+03:00') }));
});

test('every state has its own label, and an unknown one claims nothing', () => {
  const want = {
    forced: 'Agents scored with a plant mismatch forced', not_recorded: 'Plant not recorded in this file',
    another: 'Made on another plant', cannot_compare: 'Cannot compare',
    same_code: 'Same plant code as this tree; derived constants not recorded', same: 'Same plant as this tree',
    mixed: 'The files of this experiment do not agree; per seed below', invented: 'Cannot compare',
  };
  for (const [state, text] of Object.entries(want)) {
    assert.equal(plantView({ ...PROV, state, files: {} }, 'en').text, text, state);
  }
});

test('a mixed section is told seed by seed, with each reason', () => {
  const prov = { state: 'mixed', reason: null, tag: null, commits: ['c5a5341'],
    files: { 1: file(1, { state: 'cannot_compare', reason: 'python', recorded: { ...file(1).recorded, python: '3.13.2' } }), 0: file(0) } };
  assert.deepEqual(plantView(prov, 'en').details, [
    'Seed 0 · Made on another plant',
    'Seed 1 · Cannot compare · recorded under Python 3.13.2; this server runs 3.12.10, and git cannot reach the recorded commit',
  ]);
});

test('a forced file quotes its own lines and shows no hash comparison', () => {
  const line = '!! runs_c4/blind_seed0: PLANT MISMATCH';
  const prov = { state: 'forced', reason: null, tag: null, commits: [], files: { 0: file(0, { state: 'forced', forced: [line], tag: null }) } };
  const v = plantView(prov, 'en');
  assert.equal(v.text, 'Agents scored with a plant mismatch forced');
  assert.deepEqual(v.details.slice(0, 2), ["The file's own lines:", line]);
  assert.ok(!v.details.some(d => d.startsWith('recorded ')), 'a forced file never reads as a comparison');
  assert.equal(plantView(prov, 'ar').details[1], iso(line));
});

test('the git route, the reasons and a changed file are each said', () => {
  const routed = { ...PROV, state: 'same_code', tag: null, files: { 0: file(0, { route: 'git', state: 'same_code' }) } };
  assert.ok(plantView(routed, 'en').details.includes('compared through git: recorded under another Python'));
  const why = { ...PROV, state: 'another', reason: 'derived_differs' };
  assert.ok(plantView(why, 'en').details.includes('the derived constants differ'));
  const changed = { ...PROV, files: { 0: file(0, { file: { rel: 'results/c4_seed0.txt', commit: { short: 'a3a048e', date: '2026-09-22T03:02:51+03:00' }, changed: true } }) } };
  const details = plantView(changed, 'en').details;
  assert.ok(details.includes('results/c4_seed0.txt: changed since its last commit (2026-09-22T03:02:51+03:00)'));
  assert.ok(!details.some(d => d.startsWith('last commit')), 'a changed file never shows its last commit as a fact about it');
  const untracked = { ...PROV, files: { 0: file(0, { file: { rel: 'results/c4_seed0.txt', commit: null, changed: true } }) } };
  assert.ok(plantView(untracked, 'en').details.includes(`results/c4_seed0.txt: changed since its last commit (${EM_DASH})`));
});

test('a found verdict quotes its lines with file and line, a range for several lines', () => {
  const v = verdictView(VERDICT, 'en');
  assert.equal(v.state, 'found');
  assert.equal(v.short, 'smaller than the MEI (50) at 300 000 steps');
  assert.deepEqual(v.cells, [{ cell: 'SMALLER THAN THE MEI', gloss: 'Preview effect below the threshold' }]);
  assert.deepEqual(v.lines, [
    { cite: 'results/C4_RESULT.txt:40', text: '  RESULT: SMALLER THAN THE MEI' },
    { cite: 'results/C4_RESULT.txt:30-32', text: 'a\nb\nc' },
  ]);
  assert.equal(verdictView(VERDICT, 'ar').short, 'نص قصير');
});

test('no verdict and an unreadable verdict say so in this tab\'s words, never the catalog\'s', () => {
  const none = verdictView({ state: 'none', lines: [], missing: [], short: null, cells: [] }, 'en');
  assert.equal(none.short, 'No verdict recorded for this experiment');
  assert.equal(verdictView({ state: 'unavailable' }, 'en').short, 'The verdict could not be read here.');
  assert.equal(verdictView(undefined, 'en').state, 'unavailable');
  const missing = { state: 'missing', lines: [], missing: ['C4_RESULT.txt'], cells: [],
    short: { ar: 'م', en: 'verdict line not found in results/C4_RESULT.txt: do not read these agents without it' } };
  assert.equal(verdictView(missing, 'en').short, missing.short.en);
  for (const lang of ['ar', 'en']) {
    assert.doesNotMatch(none.short + verdictView({ state: 'none', short: null }, lang).short, /Nothing on this page is a result/);
  }
});

test('notes are filled from their values, numbers as the files record them', () => {
  const notes = [
    { key: 'budget_from_file', values: { steps: 300000 } },
    { key: 'dt_mismatch', values: { train_dt: 0.2, eval_dt: 1 } },
    { key: 'knock_model', values: {} },
  ];
  assert.deepEqual(noteItems(notes, 'en'), [
    `Trained for 300${NNBSP}000 steps, as these files' model lines record.`,
    'Trained at a 0.2 s step and scored at 1 s, as these files\' note lines record.',
    'The margin over current-grade rests on the knock model, which has not been tested on the car (drive C).',
  ]);
  const ar = noteItems(notes, 'ar');
  assert.equal(ar[0], t('ar', 'results.note.budget_from_file', { steps: iso(`300${NNBSP}000`) }));
  assert.equal(ar[1], t('ar', 'results.note.dt_mismatch', { train_dt: iso('0.2'), eval_dt: iso('1') }));
  assert.deepEqual(noteItems([{ key: 'not_a_note', values: {} }], 'en'), ['results.note.not_a_note']);
  assert.deepEqual(noteItems(undefined, 'en'), []);
});

test('the summary has one row per section: name, plant, short verdict, marks', () => {
  const payload = { sections: [
    section('phase_d', { verdict: { state: 'none', lines: [], missing: [], short: null, cells: [] } }),
    section('d2'),
    section('c4', { continues: 'd2' }),
    { id: 'exp-zz', kind: 'evaluation', state: 'unavailable', prefix: 'zz', name: null, order: 100,
      error: { kind: 'build', file: null, command: null, type: 'ValueError', module: null } },
  ] };
  assert.deepEqual(summaryRows(payload, 'en'), [
    { id: 'exp-phase_d', name: 'Phase D', plant: 'Made on another plant', verdict: 'No verdict recorded for this experiment', markers: [] },
    { id: 'exp-d2', name: 'Phase D2', plant: 'Made on another plant', verdict: VERDICT.short.en, markers: [] },
    { id: 'exp-c4', name: 'C4', plant: 'Made on another plant', verdict: VERDICT.short.en,
      markers: ["Continues Phase D2's agents, on the same episodes"] },
    { id: 'exp-zz', name: 'zz (no name recorded)', plant: EM_DASH, verdict: 'Could not build this section: ValueError', markers: [] },
  ]);
  const ar = summaryRows(payload, 'ar');
  assert.equal(ar[2].markers[0], t('ar', 'results.summary.continues', { other: iso('Phase D2') }));
  assert.equal(ar[0].verdict, t('ar', 'results.summary.no_verdict'));
  assert.deepEqual(summaryRows({}, 'en'), []);
});

test('an unavailable section names a command only when its file is missing', () => {
  assert.equal(unavailableText({ kind: 'missing', file: 'results/c4_seed0.txt', command: 'python run_phase_d.py' }, 'en'),
    'Not available: results/c4_seed0.txt is missing. The command that makes it: python run_phase_d.py');
  assert.equal(unavailableText({ kind: 'read', file: 'results/c4_seed0.txt', type: 'UnicodeDecodeError', command: 'x' }, 'en'),
    'Could not read results/c4_seed0.txt: UnicodeDecodeError');
  assert.equal(unavailableText({ kind: 'module', module: 'evaluate' }, 'en'), 'Needs evaluate, which could not be loaded.');
  assert.equal(unavailableText({ kind: 'build', type: 'SystemExit' }, 'en'), 'Could not build this section: SystemExit');
  assert.equal(unavailableText(null, 'en'), `Could not build this section: ${EM_DASH}`);
  assert.equal(unavailableText({ kind: 'module', module: 'evaluate' }, 'ar'),
    t('ar', 'results.section.unavailable.module', { module: iso('evaluate') }));
});

test('files not read keep their path and say why', () => {
  assert.deepEqual(notReadItems([
    { path: 'results/Bad_seed0.txt', reason: 'name', type: null },
    { path: 'results/x_seed1.txt', reason: 'unreadable', type: 'UnicodeDecodeError' },
    { path: 'results/y_seed2.txt', reason: 'weird', type: null },
  ], 'en'), [
    { path: 'results/Bad_seed0.txt', reason: 'the name is not <prefix>_seed<N>.txt' },
    { path: 'results/x_seed1.txt', reason: 'could not be read (UnicodeDecodeError)' },
    { path: 'results/y_seed2.txt', reason: 'weird' },
  ]);
  assert.deepEqual(notReadItems(undefined, 'en'), []);
});

test('the build line and every warning above the summary', () => {
  const built = { head: '031ed24', python: '3.12.10', plant_sha: 'c236a8db3e201090', restart_needed: false,
    derived_loaded_differs: false, git: 'ok', elapsed_ms: 412 };
  assert.deepEqual(builtView(built, [], 'en'),
    { line: 'Read from commit 031ed24 · Python 3.12.10 · plant c236a8db3e201090', warnings: [] });
  const bad = builtView({ ...built, head: null, git: 'unavailable', restart_needed: true, derived_loaded_differs: true },
    [{ module: 'app.agent_catalog', type: 'AssertionError' }], 'en');
  assert.equal(bad.line, `Read from commit ${EM_DASH} · Python 3.12.10 · plant c236a8db3e201090`);
  assert.deepEqual(bad.warnings, [
    'git is not available here, so the commit facts are left out.',
    'The plant files changed after the server started: restart the server.',
    'The derived constants changed after the server started: restart the server.',
    'Could not load app.agent_catalog (AssertionError). Every section that needs it says so.',
  ]);
  assert.equal(builtView(built, [], 'ar').line,
    t('ar', 'results.built.line', { head: iso('031ed24'), python: iso('3.12.10'), plant: iso('c236a8db3e201090') }));
});

test('cross-checks say pass, fail with the detail, or not compared', () => {
  assert.deepEqual(checkItems([
    { name: 'parse_equals_analysis', state: 'pass', detail: null },
    { name: 'parse_equals_analysis', state: 'fail', detail: 'seed 3 sighted 359.9 != 360.0' },
    { name: 'parse_equals_analysis', state: 'not_compared', detail: null },
    { name: 'unknown_check', state: 'pass', detail: null },
  ], 'en'), [
    "The medians read here equal analyse_phase_d.parse's.",
    "The medians read here differ from analyse_phase_d.parse's: seed 3 sighted 359.9 != 360.0",
    'Not compared with analyse_phase_d.parse.',
    'unknown_check: pass',
  ]);
});

test('unpaired seeds, the thermal-only note and the MEI lines', () => {
  assert.deepEqual(unpairedItems([{ seed: 3, file: 'results/c4_seed3.txt', have: ['baseline', 'reactive', 'sighted'] }], 'en'),
    ['Seed 3 has no pair (Sighted agent); it is not drawn.']);
  assert.deepEqual(unpairedItems([{ seed: 4, have: ['baseline'] }], 'en'), [`Seed 4 has no pair (${EM_DASH}); it is not drawn.`]);
  assert.equal(thermalNote(section('c4', { thermal_recorded: 'none' }), 'en'), 'Damage without the knock term: not recorded in these files.');
  assert.equal(thermalNote(section('c4', { thermal_recorded: 'all' }), 'en'), null);
  const some = section('c4', { thermal_recorded: 'some', seeds: [
    { seed: 0, thermal: { sighted: { median: 1 }, blind: { median: 2 } } },
    { seed: 1, thermal: null },
    { seed: 2, thermal: { sighted: { median: 1 }, blind: { median: 2 } } },
  ] });
  assert.equal(thermalNote(some, 'en'), 'Without the knock term only for seeds 0, 2; the others did not record it.');
  assert.deepEqual(meiLines(section('phase_d', { mei_after_result: true }), 'en'), [
    'The bracket is the minimum effect of interest, 50 damage units.',
    'It was set on 22 September, after this result.',
  ]);
  assert.deepEqual(meiLines(section('d2'), 'en'), ['The bracket is the minimum effect of interest, 50 damage units.']);
  assert.deepEqual(meiLines(section('d2', { mei: null }), 'en'), []);
});

test('negative numbers keep U+2212 and every Arabic value sits in an isolate', () => {
  assert.deepEqual(noteItems([{ key: 'dt_mismatch', values: { train_dt: -0.5, eval_dt: 1 } }], 'en'),
    [`Trained at a ${MINUS}0.5 s step and scored at 1 s, as these files' note lines record.`]);
  const ar = noteItems([{ key: 'budget_from_file', values: { steps: 300000 } }], 'ar')[0];
  assert.ok(ar.includes(iso(`300${NNBSP}000`)), ar);
});

test('nothing the view writes uses a banned word or says preview helps, in either language', () => {
  const payload = { sections: [section('phase_d', { notes: [{ key: 'knock_model', values: {} }] }), section('c4', { continues: 'phase_d' })] };
  const out = [];
  for (const lang of ['ar', 'en']) {
    for (const row of summaryRows(payload, lang)) out.push(row.name, row.plant, row.verdict, ...row.markers);
    out.push(...plantView(PROV, lang).details, ...noteItems(payload.sections[0].notes, lang),
      builtView({ git: 'unavailable', restart_needed: true, derived_loaded_differs: true }, [], lang).warnings.join(' '));
  }
  const text = out.join('\n').replace(/current-grade/gi, '');
  assert.doesNotMatch(text, /\b(current|stale|outdated|fresh)\b|up to date|preview (does not |doesn't )?help/i);
  assert.doesNotMatch(text, /حديث|قديم|محدَّث|محدث|الاستباق يساعد|يساعد الاستباق|الاستباق لا يفيد|لا يفيد الاستباق|الاستباق لا يساعد/);
});

test('the view carries no literal invisible character', () => {
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200f, 0x200e, 0x202f, 0x2212, 0x2011];
  const src = readFileSync(new URL('./results-view.mjs', import.meta.url), 'utf8');
  const found = [...src].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
  assert.deepEqual(found, [], 'results-view.mjs holds literal invisible characters');
});
```

- [ ] **Step 2: Run it and see it fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-view.test.mjs 2>&1 | grep -E "ERR_MODULE_NOT_FOUND\]|^ℹ (tests|pass|fail)"
```

Expected (observed in drafting): the module does not exist yet.

```
Error [ERR_MODULE_NOT_FOUND]: Cannot find module '...\app\static\sim\results-view.mjs' imported from ...\app\static\sim\results-view.test.mjs
ℹ tests 1
ℹ pass 0
ℹ fail 1
```

- [ ] **Step 3: Write the view helpers**

Create `app/static/sim/results-view.mjs` with the Write tool:

```js
// The results tab's view helpers (/results): what each line of a section
// says, in Arabic or English, from the values GET /api/results sent.
//
// PURE: no DOM, no fetch, no physics, and no statistic. Every number here is
// a value the server read from a file; this module only chooses the string
// (results-strings.mjs) and formats the values put into it. results.mjs owns
// the DOM and calls these.
//
// Two rules, pinned by results-view.test.mjs:
//  - Every value that lands inside a sentence (a number, hash, commit, file
//    path, date, module or Python version) goes through inline(), so in
//    Arabic it sits in a left-to-right isolate and keeps its order.
//  - A state or key this module does not know is never dressed up as a known
//    one: an unknown plant state reads "cannot compare", an unknown check or
//    file reason is shown as its own words, and a note without a string shows
//    its key, so the gap is visible.
import { t } from './i18n.mjs';
import { EM_DASH, MINUS, fmtInt, inline } from './results-format.mjs?v=R1a';

const PLANT_STATES = ['forced', 'not_recorded', 'another', 'cannot_compare', 'same_code', 'same', 'mixed'];
const ARMS = ['sighted', 'blind'];

// t() returns the key itself when no language has it.
const known = (lang, key) => t(lang, key) !== key;

// A recorded number as the file wrote it: integers whole and grouped, other
// numbers as they came (0.2 stays 0.2, 1.0 reads 1), the minus as U+2212.
function numText(v) {
  if (typeof v !== 'number' || !Number.isFinite(v)) return EM_DASH;
  if (Number.isInteger(v)) return fmtInt(v);
  return String(v).replace('-', MINUS);
}

// Any value bound for a {placeholder}: formatted, then isolated in Arabic.
function slot(lang, v) {
  if (v === null || v === undefined || v === '') return inline(lang, EM_DASH);
  return inline(lang, typeof v === 'number' ? numText(v) : String(v));
}

function slots(lang, values) {
  const out = {};
  for (const [k, v] of Object.entries(values || {})) out[k] = slot(lang, v);
  return out;
}

/** The section's heading: run_phase_d's name, or the prefix said to have none. */
export function sectionName(section, lang) {
  if (section && typeof section.name === 'string' && section.name) return section.name;
  return t(lang, 'results.section.no_name', { prefix: slot(lang, section?.prefix) });
}

/**
 * The section's name for a sentence's bare {name} or {other} slot: a recorded
 * name is Latin and goes in an isolate; the "no name recorded" line already
 * isolates its prefix and is Arabic in Arabic, so it goes in as it is.
 */
export function nameSlot(section, lang) {
  if (section && typeof section.name === 'string' && section.name) return slot(lang, section.name);
  return sectionName(section, lang);
}

/** "20 frozen episodes · frozen 22 Sep 2026 · protocol d2", from the header. */
export function metaText(section, lang) {
  return t(lang, 'results.section.meta', {
    episodes: slot(lang, section?.episodes),
    frozen: slot(lang, section?.frozen),
    protocol: slot(lang, section?.protocol),
  });
}

function stateText(state, lang) {
  return t(lang, `results.plant.${PLANT_STATES.includes(state) ? state : 'cannot_compare'}`);
}

function reasonText(reason, recordedPython, livePython, lang) {
  const key = `results.plant.reason.${reason}`;
  if (!known(lang, key)) return slot(lang, reason);
  return t(lang, key, { recorded: slot(lang, recordedPython), live: slot(lang, livePython) });
}

const distinct = values => [...new Set(values.filter(v => v !== null && v !== undefined && v !== ''))];

/**
 * The plant line of a section and its details, from section_provenance's
 * answer: {state, reason, tag, commits, files: {seed: classify_eval(...)}}.
 * A common state lists both hashes, the tag, the git route, the reason, the
 * recorded commits and each file's own commit; "mixed" lists every seed.
 */
export function plantView(prov, lang) {
  const files = Object.entries(prov?.files || {})
    .sort((a, b) => Number(a[0]) - Number(b[0])).map(([seed, f]) => ({ seed, ...f }));
  const state = prov?.state || 'cannot_compare';
  const details = [];
  if (state === 'mixed') {
    for (const f of files) {
      const parts = [t(lang, 'results.tip.seed', { seed: slot(lang, Number(f.seed)) }), stateText(f.state, lang)];
      if (f.reason) parts.push(reasonText(f.reason, f.recorded?.python, f.live?.python, lang));
      details.push(parts.join(' · '));
    }
    return { state, text: stateText(state, lang), details };
  }
  const forced = distinct(files.flatMap(f => f.forced || []));
  if (state === 'forced' && forced.length) {
    details.push(t(lang, 'results.plant.forced_lines'));
    for (const line of forced) details.push(slot(lang, line));
  }
  const recorded = distinct(files.map(f => f.recorded?.plant_sha));
  const live = distinct(files.map(f => f.live?.plant_sha));
  if (recorded.length && state !== 'forced' && state !== 'not_recorded') {
    details.push(t(lang, 'results.plant.hashes', { recorded: slot(lang, recorded.join(', ')), live: slot(lang, live.join(', ')) }));
  }
  if (prov?.tag) details.push(t(lang, 'results.plant.tag', { tag: slot(lang, prov.tag) }));
  if (files.length && files.every(f => f.route === 'git')) details.push(t(lang, 'results.plant.route_git'));
  if (prov?.reason) {
    details.push(reasonText(prov.reason, distinct(files.map(f => f.recorded?.python)).join(', '),
      distinct(files.map(f => f.live?.python)).join(', '), lang));
  }
  if ((prov?.commits || []).length) details.push(t(lang, 'results.plant.commits', { list: slot(lang, prov.commits.join(', ')) }));
  const committed = new Map();
  for (const f of files) {
    const c = f.file?.commit;
    if (f.file?.changed) {
      details.push(`${slot(lang, f.file.rel)}: ${t(lang, 'results.plant.changed', { date: slot(lang, c?.date) })}`);
    } else if (c && c.short) {
      committed.set(`${c.short} ${c.date}`, c);
    }
  }
  for (const c of committed.values()) {
    details.push(t(lang, 'results.plant.committed', { commit: slot(lang, c.short), date: slot(lang, c.date) }));
  }
  return { state, text: stateText(state, lang), details };
}

/**
 * The verdict block, from app.agent_catalog.verdict as the server passed it.
 * 'none' gets this tab's own line, never the catalog's NONE_TEXT (the server
 * already sends its short as null); a verdict the build could not import is
 * 'unavailable'. Each quoted line is cited results/<file>:<line>, a range when
 * the quote holds several lines, as /agents cites them.
 */
export function verdictView(verdict, lang) {
  const state = verdict?.state || 'unavailable';
  let short;
  if (state === 'unavailable') short = t(lang, 'results.verdict.unavailable');
  else if (state === 'none') short = t(lang, 'results.verdict.none');
  else short = verdict?.short?.[lang] || EM_DASH;
  const cells = (verdict?.cells || []).map(c => ({ cell: String(c.cell), gloss: c.gloss?.[lang] || '' }));
  const lines = (verdict?.lines || []).map(l => {
    const n = String(l.text).split('\n').length;
    const where = n > 1 ? `${l.line}-${l.line + n - 1}` : String(l.line);
    return { cite: `results/${l.file}:${where}`, text: String(l.text) };
  });
  return { state, short, cells, lines };
}

/** The required notes, in the server's order, each with its values filled. */
export function noteItems(notes, lang) {
  return (notes || []).map(n => t(lang, `results.note.${n.key}`, slots(lang, n.values)));
}

/**
 * One row per section, in the server's order: name, plant state, short
 * verdict only, and the "continues" mark. A section that could not be built
 * shows why in the verdict column and claims no plant state.
 */
export function summaryRows(payload, lang) {
  const sections = payload?.sections || [];
  const nameOf = prefix => {
    const other = sections.find(s => s.prefix === prefix);
    return other ? nameSlot(other, lang) : slot(lang, prefix);
  };
  return sections.map(s => {
    if (s.state !== 'ok') {
      return { id: s.id, name: sectionName(s, lang), plant: EM_DASH, verdict: unavailableText(s.error, lang), markers: [] };
    }
    const v = verdictView(s.verdict, lang);
    return {
      id: s.id,
      name: sectionName(s, lang),
      plant: plantView(s.provenance, lang).text,
      verdict: v.state === 'none' ? t(lang, 'results.summary.no_verdict') : v.short,
      markers: s.continues ? [t(lang, 'results.summary.continues', { other: nameOf(s.continues) })] : [],
    };
  });
}

/** Why a section is not shown: a missing file names its command; nothing else does. */
export function unavailableText(error, lang) {
  const e = error || {};
  switch (e.kind) {
    case 'missing':
      return t(lang, 'results.section.unavailable.missing', { file: slot(lang, e.file), command: slot(lang, e.command) });
    case 'read':
      return t(lang, 'results.section.unavailable.read', { file: slot(lang, e.file), type: slot(lang, e.type) });
    case 'module':
      return t(lang, 'results.section.unavailable.module', { module: slot(lang, e.module) });
    default:
      return t(lang, 'results.section.unavailable.build', { type: slot(lang, e.type) });
  }
}

/** Every file the build did not read, with the reason in words. */
export function notReadItems(notRead, lang) {
  return (notRead || []).map(item => {
    const key = `results.not_read.reason.${item.reason}`;
    return {
      path: String(item.path),
      reason: known(lang, key) ? t(lang, key, { type: slot(lang, item.type) }) : slot(lang, item.reason),
    };
  });
}

/** The line under the intro, and the warnings above the summary. */
export function builtView(built, failures, lang) {
  const b = built || {};
  const line = t(lang, 'results.built.line', { head: slot(lang, b.head), python: slot(lang, b.python), plant: slot(lang, b.plant_sha) });
  const warnings = [];
  if (b.git === 'unavailable') warnings.push(t(lang, 'results.built.git_unavailable'));
  if (b.restart_needed) warnings.push(t(lang, 'results.built.restart'));
  if (b.derived_loaded_differs) warnings.push(t(lang, 'results.built.derived_restart'));
  for (const f of failures || []) {
    warnings.push(t(lang, 'results.import_failure', { module: slot(lang, f.module), type: slot(lang, f.type) }));
  }
  return { line, warnings };
}

/** Each cross-check's outcome; a check without a string is shown as its own words. */
export function checkItems(checks, lang) {
  return (checks || []).map(c => {
    const key = `results.check.${c.name}.${c.state}`;
    return known(lang, key) ? t(lang, key, { detail: slot(lang, c.detail) }) : slot(lang, `${c.name}: ${c.state}`);
  });
}

/** "Seed 3 has no pair (Sighted agent); it is not drawn." Arms only. */
export function unpairedItems(unpaired, lang) {
  const sep = lang === 'ar' ? '، ' : ', ';
  return (unpaired || []).map(u => {
    const have = (u.have || []).filter(r => ARMS.includes(r)).map(r => t(lang, `results.legend.${r}`));
    return t(lang, 'results.unpaired', { seed: slot(lang, u.seed), have: have.length ? have.join(sep) : EM_DASH });
  });
}

/** The thermal-only panel's note: null when every seed recorded it. */
export function thermalNote(section, lang) {
  if (section?.thermal_recorded === 'none') return t(lang, 'results.chart.thermal_none');
  if (section?.thermal_recorded !== 'some') return null;
  const seeds = (section.seeds || []).filter(s => s.thermal?.sighted && s.thermal?.blind).map(s => s.seed);
  return t(lang, 'results.chart.thermal_some', { seeds: slot(lang, seeds.join(', ')) });
}

/** What the MEI bracket is, and, where it applies, that it came after the result. */
export function meiLines(section, lang) {
  if (typeof section?.mei !== 'number' || !Number.isFinite(section.mei)) return [];
  const out = [t(lang, 'results.chart.mei', { mei: slot(lang, section.mei) })];
  if (section.mei_after_result) out.push(t(lang, 'results.chart.mei_after'));
  return out;
}
```

- [ ] **Step 4: Run the view test and see it pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
cd app && node --test static/sim/results-view.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)"
```

Expected (observed in drafting, with Task 6's strings):

```
ℹ tests 19
ℹ pass 19
ℹ fail 0
```

- [ ] **Step 5: Write the failing page tests, Node and Python**

Create `app/static/sim/results-page.test.mjs` with the Write tool:

```js
// The /results page shell, checked without a browser: every stylesheet and
// module it names exists, every id results.mjs reads is declared once, every
// import resolves, the tab's own modules carry one version query and the
// lab's shared modules none (a second query would load a second copy of
// results-strings.mjs, whose merge then refuses), every key the markup and
// the page name exists in both languages, and the nav reads simulation,
// agents, results (active), monitor, review. The lab was dead for a day once
// because one module did not exist; these are the checks that catch it.
import test from 'node:test';
import assert from 'node:assert/strict';
import { existsSync, readFileSync } from 'node:fs';
import { STRINGS, LANGS } from './i18n.mjs';
import './results-strings.mjs?v=R1a';

const STATIC = new URL('../', import.meta.url);
const HTML = new URL('../results.html', import.meta.url);
const VERSION = 'v=R1a';
const OWN = ['results.mjs', 'results-view.mjs', 'results-charts.mjs', 'results-format.mjs',
  'results-strings.mjs', 'charts-lib.mjs'];
const SHARED = ['i18n.mjs', 'agent-picker.mjs'];
const IDS = ['error', 'built', 'warnings', 'summary', 'summary-rows', 'sections', 'not-read', 'not-read-list',
  'theme-toggle', 'lang-toggle', 'footer-index'];

function read(url) {
  assert.ok(existsSync(url), `${url.pathname} does not exist`);
  return readFileSync(url, 'utf8');
}
const has = key => LANGS.every(lang => Object.prototype.hasOwnProperty.call(STRINGS[lang], key));
const slots = text => new Set([...text.matchAll(/\{(\w+)\}/g)].map(m => m[1]));
// Every relative import of a module: static, side-effect and dynamic.
const importsOf = src => [
  ...[...src.matchAll(/\bfrom\s+'(\.\/[^']+)'/g)].map(m => m[1]),
  ...[...src.matchAll(/^import\s+'(\.\/[^']+)'/gm)].map(m => m[1]),
  ...[...src.matchAll(/\bimport\(\s*'(\.\/[^']+)'\s*\)/g)].map(m => m[1]),
];
const split = spec => {
  const [path, query = ''] = spec.split('?');
  return { file: path.slice(2), query };
};

test('every stylesheet and script results.html names exists, the tab\'s own with the version query', () => {
  const html = read(HTML);
  const links = [...html.matchAll(/<link[^>]+href="\/static\/([^"]+)"/g)].map(m => m[1]);
  const scripts = [...html.matchAll(/<script[^>]+src="\/static\/([^"]+)"/g)].map(m => m[1]);
  assert.deepEqual(links, ['sim/style.css', 'sim/agents.css', `sim/results.css?${VERSION}`]);
  assert.deepEqual(scripts, [`sim/results.mjs?${VERSION}`]);
  for (const ref of [...links, ...scripts]) {
    assert.ok(existsSync(new URL(ref.split('?')[0], STATIC)), `${ref} is referenced by the page and does not exist`);
  }
  assert.doesNotMatch(html, /type="importmap"/, 'this page loads no Three.js, so it carries no import map');
});

test('ids are declared once, and every id results.mjs reads is declared', () => {
  const html = read(HTML);
  const ids = [...html.matchAll(/\sid="([^"]+)"/g)].map(m => m[1]);
  assert.equal(ids.length, new Set(ids).size, 'an id is declared twice in results.html');
  for (const id of IDS) assert.ok(ids.includes(id), `#${id} is missing from results.html`);
  const used = new Set([...read(new URL('./results.mjs', import.meta.url)).matchAll(/\$\('([^']+)'\)/g)].map(m => m[1]));
  assert.ok(used.size > 5, 'the id scan found almost nothing; the pattern has drifted');
  assert.deepEqual([...used].filter(id => !ids.includes(id)), []);
  for (const symbol of ['i-sun', 'i-moon']) assert.ok(ids.includes(symbol), `#${symbol} is not in the icon library`);
});

test('every import of the tab\'s modules resolves: its own with ?v=R1a, the shared ones bare', () => {
  for (const name of OWN) {
    const src = read(new URL(`./${name}`, import.meta.url));
    for (const spec of importsOf(src)) {
      const { file, query } = split(spec);
      assert.ok(existsSync(new URL(`./${file}`, import.meta.url)), `${name} imports missing ${spec}`);
      if (OWN.includes(file)) assert.equal(query, VERSION, `${name} imports ${spec}: the tab's modules carry ?${VERSION}`);
      else if (SHARED.includes(file)) assert.equal(query, '', `${name} imports ${spec}: a shared lab module carries no query`);
      else assert.fail(`${name} imports ${spec}, which is neither the tab's nor a shared lab module`);
    }
  }
  const page = importsOf(read(new URL('./results.mjs', import.meta.url))).map(s => split(s).file);
  for (const name of ['results-strings.mjs', 'results-view.mjs', 'results-charts.mjs', 'charts-lib.mjs', 'i18n.mjs']) {
    assert.ok(page.includes(name), `results.mjs does not import ${name}`);
  }
});

test('every key results.html names exists in both languages, carries no placeholder, and the markup holds its Arabic', () => {
  const html = read(HTML);
  const keys = [...new Set([...html.matchAll(/data-i18n(?:-aria|-title)?="([^"]+)"/g)].map(m => m[1]))];
  assert.ok(keys.length > 15, 'the key scan found almost nothing; the pattern has drifted');
  assert.deepEqual(keys.filter(k => !has(k)), []);
  assert.deepEqual(keys.filter(k => LANGS.some(lang => slots(STRINGS[lang][k]).size)), []);
  // Before the script runs the page reads in Arabic: each marked element's own
  // text is its Arabic string (character references decoded).
  const decode = s => s.replace(/&#x([0-9a-f]+);/gi, (_, h) => String.fromCodePoint(parseInt(h, 16)));
  const marked = [...html.matchAll(/<(\w+)\b[^>]*\bdata-i18n="([^"]+)"[^>]*>([^<]*)<\/\1>/g)];
  assert.ok(marked.length > 15, 'the text scan found almost nothing; the pattern has drifted');
  for (const [, , key, text] of marked) assert.equal(decode(text), STRINGS.ar[key], `the markup's text for ${key}`);
});

test('every key results.mjs names exists, and each t() call fills exactly its placeholders', () => {
  const src = read(new URL('./results.mjs', import.meta.url));
  const calls = [...src.matchAll(/\bt\(\s*currentLang\s*,\s*'([^']+)'\s*(?:,\s*\{([^}]*)\})?/g)]
    .map(m => ({ key: m[1], names: m[2] ? [...m[2].matchAll(/(\w+)\s*:/g)].map(n => n[1]) : [] }));
  assert.ok(calls.length > 10, 'the t() scan found almost nothing; the pattern has drifted');
  const literals = [...src.matchAll(/'((?:results|nav|theme|lang)\.[\w.]+)'/g)].map(m => m[1]);
  assert.deepEqual([...new Set([...calls.map(c => c.key), ...literals])].filter(k => !has(k)), []);
  const problems = [];
  for (const { key, names } of calls) {
    for (const lang of LANGS) {
      const want = slots(STRINGS[lang][key] || '');
      for (const s of want) if (!names.includes(s)) problems.push(`${key} [${lang}] is never given {${s}}`);
      for (const g of names) if (!want.has(g)) problems.push(`${key} [${lang}] has no {${g}}`);
    }
  }
  assert.deepEqual(problems, []);
});

test('the nav reads simulation, agents, results (active), monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'results.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/results', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.results', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, false, true, false, false]);
  assert.deepEqual(links.map(a => attr(a, 'aria-current') || null), [null, null, 'page', null, null]);
});

test('the page module and the markup carry no literal invisible character', () => {
  // An isolate in the markup is a character reference (&#x2066;), never the
  // character: an editor shows neither, and the Write tool decodes escapes.
  const banned = [0x2066, 0x2067, 0x2068, 0x2069, 0x200f, 0x200e, 0x202f, 0x2212, 0x2011];
  for (const url of [new URL('./results.mjs', import.meta.url), HTML]) {
    const found = [...read(url)].filter(c => banned.includes(c.codePointAt(0))).map(c => c.codePointAt(0).toString(16));
    assert.deepEqual(found, [], `${url.pathname} holds literal invisible characters`);
  }
});

test('results.html carries no figure of its own', () => {
  // verify_docs.py reads .html: the numbers live in the data, never in the
  // markup. The lab's footer (B58, the page index) is the only exception.
  const text = read(HTML)
    .replace(/<script[\s\S]*?<\/script>/g, '')
    .replace(/<footer[\s\S]*?<\/footer>/g, '')
    .replace(/<[^>]+>/g, ' ')
    .replace(/&#x[0-9a-f]+;/gi, '');
  assert.deepEqual(text.match(/\d+/g) || [], []);
});
```

Then add `class PageTests` to `app/test_results.py` with the Edit tool. Task 1 ends the file with the two lines `if __name__ == "__main__":` and `    unittest.main()`, and every task adds its classes above them: `old_string` is the line `if __name__ == "__main__":` (it occurs once; check with `grep -n '__main__' app/test_results.py`), `new_string` is the class below followed by that same line. The class uses the module's `ROOT` and `unittest` (Task 1) and imports `re` and FastAPI inside its tests.

```python
class PageTests(unittest.TestCase):
    """The /results page can load every asset, id and module it names, and
    the route serves it (results-tab design, the tests section, routes).

    The lab was dead for a day once because main.mjs did not exist: both
    suites passed, the route returned 200 and the browser 404'd one module.
    These are the same checks for this page, plus the version query: the
    tab's own modules carry one query and the lab's shared modules none, or a
    browser loads two copies of results-strings.mjs and its merge refuses.
    """

    STATIC = ROOT / "app" / "static"
    OWN = ("results.mjs", "results-view.mjs", "results-charts.mjs", "results-format.mjs",
           "results-strings.mjs", "charts-lib.mjs")
    SHARED = ("i18n.mjs", "agent-picker.mjs")
    VERSION = "v=R1a"
    IDS = ("error", "built", "warnings", "summary", "summary-rows", "sections", "not-read",
           "not-read-list", "theme-toggle", "lang-toggle", "footer-index")

    def read(self, rel):
        path = self.STATIC / rel
        self.assertTrue(path.is_file(), f"{rel} does not exist")
        return path.read_text(encoding="utf-8")

    def test_page_assets_ids_and_imports(self):
        import re
        html = self.read("results.html")
        page = self.read("sim/results.mjs")
        refs = (re.findall(r'<script[^>]+src="/static/([^"]+)"', html)
                + re.findall(r'<link[^>]+href="/static/([^"]+)"', html))
        self.assertIn(f"sim/results.mjs?{self.VERSION}", refs)
        self.assertIn(f"sim/results.css?{self.VERSION}", refs)
        for ref in refs:
            self.assertTrue((self.STATIC / ref.split("?")[0]).is_file(),
                            f"{ref} is referenced by the page and does not exist")
        self.assertNotIn('type="importmap"', html, "this page loads no Three.js")

        ids = re.findall(r'\sid="([^"]+)"', html)
        self.assertEqual(len(ids), len(set(ids)), "an id is declared twice in results.html")
        self.assertFalse(set(self.IDS) - set(ids), f"missing ids: {sorted(set(self.IDS) - set(ids))}")
        used = set(re.findall(r"\$\('([^']+)'\)", page))
        self.assertTrue(used, "the id scan found nothing; the pattern has drifted")
        self.assertFalse(used - set(ids), f"results.mjs reads ids the page does not define: {sorted(used - set(ids))}")
        for symbol in set(re.findall(r"'#(i-[a-z]+)'", page)):
            self.assertIn(f'id="{symbol}"', html, f"#{symbol} is not in the icon library")

        for name in self.OWN:
            src = self.read(f"sim/{name}")
            specs = (re.findall(r"\bfrom\s+'(\./[^']+)'", src)
                     + re.findall(r"^import\s+'(\./[^']+)'", src, flags=re.M)
                     + re.findall(r"\bimport\(\s*'(\./[^']+)'\s*\)", src))
            for spec in specs:
                path, _, query = spec[2:].partition("?")
                self.assertTrue((self.STATIC / "sim" / path).is_file(), f"{name} imports missing {spec}")
                if path in self.OWN:
                    self.assertEqual(query, self.VERSION, f"{name} imports {spec} without ?{self.VERSION}")
                else:
                    self.assertIn(path, self.SHARED, f"{name} imports {spec}, neither the tab's nor a lab module")
                    self.assertEqual(query, "", f"{name} imports the shared {spec} with a query")

    def test_the_route_serves_the_page_to_a_local_host_only(self):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from app.results_api import mount_results
        app = FastAPI()
        # GET /results reads only the page: the build is never called here.
        mount_results(app, build=lambda: {"built": {}, "import_failures": [], "sections": [], "not_read": []})
        html = (self.STATIC / "results.html").read_text(encoding="utf-8")
        with TestClient(app) as client:
            for host in ("127.0.0.1:8000", "localhost"):
                r = client.get("/results", headers={"host": host})
                self.assertEqual(r.status_code, 200, host)
                self.assertEqual(r.headers.get("cache-control"), "no-store", host)
                self.assertEqual(r.text, html, host)
                self.assertIn(f'src="/static/sim/results.mjs?{self.VERSION}"', r.text)
            refused = client.get("/results", headers={"host": "evil.example:8000"})
        self.assertEqual(refused.status_code, 403)
        self.assertEqual(refused.headers.get("cache-control"), "no-store")
        self.assertNotIn("<html", refused.text)


if __name__ == "__main__":
```

- [ ] **Step 6: Run both and see them fail**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/results-page.test.mjs 2>&1 | grep -E "^ℹ (tests|pass|fail)")
$PY -m unittest app.test_results.PageTests 2>&1 | grep -E "^(FAIL|ERROR|AssertionError|FileNotFoundError|Ran|FAILED)" | cut -c1-110
```

Expected (observed in drafting): every node test fails, because `results.html` and `results.mjs` do not exist; the Python asset test fails on the missing page and the route test errors on it.

```
ℹ tests 8
ℹ pass 0
ℹ fail 8
ERROR: test_the_route_serves_the_page_to_a_local_host_only (app.test_results.PageTests.test_the_route_serves_t
FileNotFoundError: [Errno 2] No such file or directory: 'C:\\Users\\admin\\...
FAIL: test_page_assets_ids_and_imports (app.test_results.PageTests.test_page_assets_ids_and_imports)
AssertionError: False is not true : results.html does not exist
Ran 2 tests in 0.001s
FAILED (failures=1, errors=1)
```

(The `FileNotFoundError` line is cut at 110 characters; the path in it ends with this tree's `app\static\results.html`.)

- [ ] **Step 7: Write the frame**

Create `app/static/results.html` with the Write tool. Its Arabic is Task 6's `STRINGS.ar`, character for character (`results-page.test.mjs` checks it), and the one isolate in it is written as character references:

```html
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <meta name="theme-color" content="#f4f3ed">
  <title data-i18n="results.page.title">النتائج — GRAD</title>
  <link rel="stylesheet" href="/static/sim/style.css">
  <link rel="stylesheet" href="/static/sim/agents.css">
  <link rel="stylesheet" href="/static/sim/results.css?v=R1a">
  <script>
    // The lab's own pre-paint block, unchanged: the same two keys, wrapped
    // because localStorage throws in private mode. Nothing else is stored.
    try {
      var s = localStorage.getItem('grad.sim.theme');
      if (s === 'dark' || s === 'light') document.documentElement.dataset.theme = s;
      var l = localStorage.getItem('grad.sim.lang');
      if (l === 'en' || l === 'ar') {
        document.documentElement.lang = l;
        document.documentElement.dir = l === 'en' ? 'ltr' : 'rtl';
      }
    } catch (e) { /* no stored preference is not an error */ }
  </script>
</head>
<body>
  <svg class="icon-library" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
    <symbol id="i-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.9 4.9l1.5 1.5m11.2 11.2 1.5 1.5M19.1 4.9l-1.5 1.5M6.4 17.6l-1.5 1.5"/></symbol>
    <symbol id="i-moon" viewBox="0 0 24 24"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5Z"/></symbol>
  </svg>
  <header class="topbar">
    <a href="/simulation" class="brand" data-i18n-aria="brand.aria" aria-label="مختبر GRAD"><span class="brand-mark">G<span>╱</span></span><div><strong dir="ltr">GRAD<span class="brand-point">.</span></strong><small data-i18n="brand.tagline">مختبر الأنظمة الهندسية</small></div></a>
    <nav data-i18n-aria="nav.aria" aria-label="التنقل الرئيسي"><a href="/simulation" data-i18n="nav.simulation">مختبر الرحلة</a><a href="/agents" data-i18n="nav.agents">الوكلاء</a><a class="active" href="/results" aria-current="page" data-i18n="nav.results">النتائج</a><a href="/" data-i18n="nav.monitor">المراقبة</a><a href="/review" data-i18n="nav.review">مراجعة التنبيهات</a></nav>
    <div class="topbar-tools">
      <button id="theme-toggle" type="button" data-i18n-title="theme.to_dark" data-i18n-aria="theme.aria" aria-label="تبديل الوضع الليلي" title="الوضع الليلي"><svg><use href="#i-moon"/></svg></button>
      <button id="lang-toggle" type="button" data-i18n-title="lang.switch_to_english" data-i18n-aria="lang.aria" aria-label="تغيير اللغة" title="English"><span dir="ltr">EN</span></button>
    </div>
  </header>
  <main class="results-main">
    <section class="page-intro results-intro">
      <div><p class="eyebrow"><span class="small-rule"></span><span data-i18n="intro.eyebrow">المحرك · الطريق · الزمن</span></p><h1><span data-i18n="results.intro.heading">كل تجربة، كما تسجّلها ملفاتها</span><span>.</span></h1><p class="intro-note" data-i18n="results.intro.note">يُقرأ كل ما هنا من &#x2066;results/&#x2069; في كل مرة تُفتح فيها هذه الصفحة. لا يُعاد هنا حساب أي شيء.</p></div>
    </section>
    <div id="error" class="error" role="alert" hidden></div>
    <p id="built" class="rc-built" role="status" aria-live="polite" data-i18n="results.loading">جارٍ قراءة ملفات النتائج…</p>
    <ul id="warnings" class="rc-warnings" hidden></ul>
    <section id="summary" class="rc-summary" hidden>
      <h2 data-i18n="results.summary.heading">الملخّص</h2>
      <p class="rc-summary-note" data-i18n="results.summary.note">كل صف تجربة مستقلة، لها محاكيها وطريقها؛ ولا تُدمج الصفوف في نتيجة واحدة.</p>
      <table class="rc-summary-table">
        <thead><tr><th scope="col" data-i18n="results.summary.col.experiment">التجربة</th><th scope="col" data-i18n="results.summary.col.plant">المحاكي</th><th scope="col" data-i18n="results.summary.col.verdict">الحكم</th></tr></thead>
        <tbody id="summary-rows"></tbody>
      </table>
    </section>
    <div id="sections" class="rc-sections"></div>
    <section id="not-read" class="rc-not-read" hidden>
      <h2 data-i18n="results.not_read.heading">ملفات لم تُقرأ</h2>
      <ul id="not-read-list"></ul>
    </section>
    <footer><span dir="ltr" data-i18n="footer.brand">GRAD / ENGINEERING REPLAY LAB</span><span data-i18n="footer.note">مشروع تخرّج · محرك B58 · عرض علمي استكشافي</span><span id="footer-index" class="footer-index" dir="ltr" data-i18n="results.footer.index">03 — RESULTS</span></footer>
  </main>
  <noscript><p data-i18n="noscript">يحتاج المختبر إلى JavaScript لعرض بيانات الرحلة والمشهد ثلاثي الأبعاد.</p></noscript>
  <script type="module" src="/static/sim/results.mjs?v=R1a"></script>
</body>
</html>
```

- [ ] **Step 8: Write the page module**

Create `app/static/sim/results.mjs` with the Write tool:

```js
// The results tab (/results): fetch, render, language, theme.
//
// PRESENTATION ONLY. The server (app/results_data.py) reads results/ on every
// request and sends values; results-view.mjs chooses each sentence and
// results-charts.mjs lays out and draws each figure. This file builds the DOM
// from them and computes nothing: no statistic, no average across
// experiments, no winner. Each experiment is its own section, never counted
// together with another.
//
// A language switch rebuilds every section and redraws every chart (the SVG
// labels hold no words, but the tooltips and tables do); a theme switch
// redraws nothing, because every colour is a CSS variable. Nothing is stored
// in the browser except the lab's own theme and language preferences.
import './results-strings.mjs?v=R1a';
import { t, LANGS, DEFAULT_LANG, resolveLang, applyTranslations } from './i18n.mjs';
import { inline } from './results-format.mjs?v=R1a';
import { createMounter } from './charts-lib.mjs?v=R1a';
import {
  ROLE_VAR, HAND_ROLES, pairsLayout, handLayout, pairsTable, handTable, drawPairs, drawHand,
} from './results-charts.mjs?v=R1a';
import {
  sectionName, nameSlot, metaText, plantView, verdictView, noteItems, summaryRows, unavailableText,
  notReadItems, builtView, checkItems, unpairedItems, thermalNote, meiLines,
} from './results-view.mjs?v=R1a';

const $ = id => document.getElementById(id);
const THEMES = ['light', 'dark'];
const STORE = { theme: 'grad.sim.theme', lang: 'grad.sim.lang' };
const ARMS = ['sighted', 'blind'];

let currentLang = DEFAULT_LANG;
const state = {
  payload: null,   // GET /api/results, once it has arrived
  failure: null,   // what to put in {status} when it did not
};
const mounter = createMounter({ onError: chartFailed });

function remember(key, value) {
  try { localStorage.setItem(key, value); } catch (e) { /* a preference is a convenience */ }
}
function recall(key, allowed, fallback) {
  try {
    const v = localStorage.getItem(key);
    return allowed.includes(v) ? v : fallback;
  } catch (e) { return fallback; }
}
function setText(node, value) {
  if (node && node.textContent !== value) node.textContent = value;
}
function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function list(className, items) {
  const ul = el('ul', className);
  for (const item of items) ul.appendChild(el('li', '', item));
  return ul;
}

// A chart whose drawing throws says so in its own host, in the page's language.
function chartFailed(host, err) {
  console.error(err);
  host.querySelector(':scope > .rc-chart-error')?.remove();
  host.appendChild(el('p', 'rc-chart-error', t(currentLang, 'results.chart.unavailable')));
}

// ------------------------------------------------------------- the frame
function renderBuilt() {
  const built = $('built');
  const warnings = $('warnings');
  if (!built || !warnings) return;
  if (state.failure !== null) {
    built.hidden = true;
    warnings.hidden = true;
    return;
  }
  if (!state.payload) return;   // still loading: the markup's own line stands
  built.removeAttribute('data-i18n');
  const view = builtView(state.payload.built, state.payload.import_failures, currentLang);
  setText(built, view.line);
  warnings.textContent = '';
  for (const w of view.warnings) warnings.appendChild(el('li', '', w));
  warnings.hidden = view.warnings.length === 0;
}

function renderError() {
  const box = $('error');
  if (!box) return;
  box.hidden = state.failure === null;
  setText(box, state.failure === null ? ''
    : t(currentLang, 'results.error.fetch', { status: inline(currentLang, state.failure) }));
}

function renderSummary() {
  const rows = $('summary-rows');
  const summary = $('summary');
  if (!rows || !summary) return;
  rows.textContent = '';
  if (!state.payload) { summary.hidden = true; return; }
  for (const row of summaryRows(state.payload, currentLang)) {
    const tr = el('tr');
    const name = el('td', 'rc-summary-name');
    const link = el('a', 'rc-summary-link', row.name);
    link.href = `#${row.id}`;
    name.appendChild(link);
    for (const marker of row.markers) name.appendChild(el('p', 'rc-meta', marker));
    tr.append(name, el('td', 'rc-summary-plant', row.plant), el('td', 'rc-summary-verdict', row.verdict));
    rows.appendChild(tr);
  }
  summary.hidden = false;
}

function renderNotRead() {
  const box = $('not-read');
  const ul = $('not-read-list');
  if (!box || !ul) return;
  ul.textContent = '';
  const items = state.payload ? notReadItems(state.payload.not_read, currentLang) : [];
  for (const item of items) {
    const li = el('li');
    const path = el('code', '', item.path);
    path.dir = 'ltr';
    li.append(path, el('span', '', item.reason));
    ul.appendChild(li);
  }
  box.hidden = items.length === 0;
}

// ----------------------------------------------------------- a section
function verdictBlock(verdict) {
  const view = verdictView(verdict, currentLang);
  const box = el('section', 'rc-verdict');
  box.dataset.state = view.state;
  box.appendChild(el('h3', '', t(currentLang, 'results.verdict.heading')));
  box.appendChild(el('p', 'verdict-short', view.short));
  const cells = el('ul', 'verdict-cells');
  for (const c of view.cells) {
    const li = el('li');
    const cell = el('b', 'cell', c.cell);
    cell.dir = 'ltr';
    li.append(cell, el('span', 'gloss', c.gloss));
    cells.appendChild(li);
  }
  box.appendChild(cells);
  if (view.lines.length) {
    const more = el('details', 'rc-verdict-lines');
    more.appendChild(el('summary', '', t(currentLang, 'results.verdict.lines')));
    for (const line of view.lines) {
      const fig = el('figure', 'quote');
      const pre = el('pre', '', line.text);
      pre.dir = 'ltr';
      const cite = el('figcaption', '', line.cite);
      cite.dir = 'ltr';
      fig.append(pre, cite);
      more.appendChild(fig);
    }
    box.appendChild(more);
  }
  return box;
}

// The legend, in HTML because every word of a chart is HTML (spec 7.3): the
// agents are dots, the hand-written policies squares, current-grade's
// reference a dash, and the MEI bracket is explained beside its own sign.
function legend(kind, layout, section) {
  const box = el('div', 'rc-legend');
  const item = (shape, colour, text) => {
    const span = el('span', 'rc-legend-item');
    const swatch = el('i', `rc-swatch ${shape}`);
    swatch.style.color = colour;
    span.append(swatch, el('span', '', text));
    box.appendChild(span);
  };
  if (kind === 'hand') {
    const roles = layout.roles || HAND_ROLES.filter(role => layout.marks.some(m => m.role === role));
    for (const role of roles) {
      item(ARMS.includes(role) ? 'rc-sw-dot' : 'rc-sw-square', ROLE_VAR[role], t(currentLang, `results.legend.${role}`));
    }
    return box;
  }
  for (const role of ARMS) item('rc-sw-dot', ROLE_VAR[role], t(currentLang, `results.legend.${role}`));
  if (layout.reference) item('rc-sw-dash', ROLE_VAR.current_grade, t(currentLang, 'results.legend.current_grade'));
  const mei = meiLines(section, currentLang);
  if (mei.length) item('rc-sw-bracket', 'var(--rc-mei)', mei.join(' '));
  return box;
}

function numbersTable(table) {
  const details = el('details', 'rc-table');
  details.appendChild(el('summary', '', t(currentLang, 'results.table.toggle')));
  const tbl = el('table');
  const head = el('tr');
  for (const h of table.head) head.appendChild(el('th', '', h));
  const thead = el('thead');
  thead.appendChild(head);
  const tbody = el('tbody');
  for (const row of table.rows) {
    const tr = el('tr');
    for (const cell of row) tr.appendChild(el('td', '', cell));
    tbody.appendChild(tr);
  }
  tbl.append(thead, tbody);
  details.appendChild(tbl);
  return details;
}

const FIGURES = {
  pairs: { title: 'results.chart.pairs.title', what: 'results.chart.pairs.what', axis: 'results.chart.axis.damage',
    aria: 'results.chart.aria.pairs', measure: 'total' },
  'pairs-thermal': { title: 'results.chart.pairs_thermal.title', what: 'results.chart.pairs.what',
    axis: 'results.chart.axis.damage_thermal', aria: 'results.chart.aria.pairs', measure: 'thermal' },
  hand: { title: 'results.chart.hand.title', what: 'results.chart.hand.what', axis: 'results.chart.axis.damage',
    aria: 'results.chart.aria.hand' },
};

// One figure: title, what it shows, axis titles, the chart host, legend and
// the folded numbers. Returns the chart to mount once the node is in the page.
function figure(section, kind) {
  const spec = FIGURES[kind];
  const fig = el('figure', 'rc-figure');
  fig.dataset.figure = kind;
  fig.appendChild(el('h3', '', t(currentLang, spec.title)));
  fig.appendChild(el('p', 'rc-what', t(currentLang, spec.what)));
  try {
    const hand = kind === 'hand';
    const layout = hand ? handLayout(section) : pairsLayout(section, spec.measure);
    if (kind === 'pairs-thermal') {
      const note = thermalNote(section, currentLang);
      if (note) fig.appendChild(el('p', 'rc-note', note));
    }
    fig.appendChild(el('div', 'rc-axis-y', t(currentLang, spec.axis)));
    const host = el('div', 'rc-chart');
    // A group, not an image: the marks inside are focusable (spec 7.3).
    host.setAttribute('role', 'group');
    host.setAttribute('aria-label', t(currentLang, spec.aria, { name: nameSlot(section, currentLang) }));
    fig.appendChild(host);
    fig.appendChild(el('div', 'rc-axis-x', t(currentLang, 'results.chart.axis.seed')));
    fig.appendChild(legend(kind, layout, section));
    fig.appendChild(numbersTable(hand ? handTable(layout, currentLang) : pairsTable(layout, currentLang)));
    if (layout.empty) {
      host.appendChild(el('p', 'rc-chart-error', t(currentLang, 'results.chart.unavailable')));
      return { node: fig, chart: null };
    }
    const lang = currentLang;
    const draw = hand
      ? (node, w, h) => drawHand(node, w, h, layout, lang)
      : (node, w, h) => drawPairs(node, w, h, layout, lang);
    return { node: fig, chart: { host, draw } };
  } catch (err) {
    console.error(err);
    fig.appendChild(el('p', 'rc-note', t(currentLang, 'results.chart.unavailable')));
    return { node: fig, chart: null };
  }
}

function okSection(section, markers) {
  const node = el('article', 'rc-section');
  node.id = section.id;
  node.dataset.state = 'ok';
  node.appendChild(el('h2', '', sectionName(section, currentLang)));
  node.appendChild(el('p', 'rc-meta', metaText(section, currentLang)));
  for (const marker of markers) node.appendChild(el('p', 'rc-meta', marker));
  if (section.scenario) {
    // The scenario line as evaluate.py printed it: quoted, left to right.
    const quote = el('p', 'rc-meta rc-scenario', section.scenario);
    quote.dir = 'ltr';
    node.appendChild(quote);
  }
  const plant = plantView(section.provenance, currentLang);
  const line = el('p', 'rc-plant');
  line.dataset.state = plant.state;
  line.append(el('b', '', t(currentLang, 'results.plant.label')), ' ', el('span', '', plant.text));
  node.appendChild(line);
  node.appendChild(list('rc-plant-details', plant.details));
  node.appendChild(list('rc-checks', checkItems(section.checks, currentLang)));
  node.appendChild(verdictBlock(section.verdict));
  const notesHeading = el('p', 'rc-note rc-notes-heading');
  notesHeading.appendChild(el('b', '', t(currentLang, 'results.notes.heading')));
  node.appendChild(notesHeading);
  node.appendChild(list('rc-notes', noteItems(section.notes, currentLang)));
  const charts = [];
  const add = kind => {
    const f = figure(section, kind);
    node.appendChild(f.node);
    if (f.chart) charts.push(f.chart);
  };
  add('pairs');
  if (section.thermal_recorded !== 'none') add('pairs-thermal');
  else node.appendChild(el('p', 'rc-note', t(currentLang, 'results.chart.thermal_none')));
  add('hand');
  node.appendChild(list('rc-unpaired', unpairedItems(section.unpaired, currentLang)));
  return { node, charts };
}

function unavailableSection(section, text) {
  const node = el('article', 'rc-section');
  node.id = section.id;
  node.dataset.state = 'unavailable';
  node.append(el('h2', '', sectionName(section, currentLang)), el('p', 'rc-note rc-unavailable', text));
  return { node, charts: [] };
}

// A section that cannot be built costs only itself, never the tab.
function buildSection(section, markers) {
  if (section.state !== 'ok') return unavailableSection(section, unavailableText(section.error, currentLang));
  try {
    return okSection(section, markers);
  } catch (err) {
    console.error(err);
    return unavailableSection(section, unavailableText({ kind: 'build', type: err?.name }, currentLang));
  }
}

function renderSections() {
  const host = $('sections');
  if (!host) return;
  host.textContent = '';
  const rows = summaryRows(state.payload, currentLang);
  for (const section of state.payload?.sections || []) {
    const markers = rows.find(r => r.id === section.id)?.markers || [];
    const built = buildSection(section, markers);
    host.appendChild(built.node);
    // Mounted once the node is in the page, so each host has its width.
    for (const chart of built.charts) mounter.mount(chart.host, chart.draw);
  }
}

function render() {
  mounter.clear();
  renderError();
  renderBuilt();
  renderSummary();
  renderSections();
  renderNotRead();
}

// ---------------------------------------------------- theme and language
// Presentation only: switching either never changes a value on this page.
function syncThemeButton() {
  const theme = document.documentElement.dataset.theme === 'dark' ? 'dark' : 'light';
  const button = $('theme-toggle');
  if (!button) return;
  button.title = t(currentLang, theme === 'dark' ? 'theme.to_light' : 'theme.to_dark');
  button.setAttribute('aria-pressed', String(theme === 'dark'));
  button.querySelector('use')?.setAttribute('href', theme === 'dark' ? '#i-sun' : '#i-moon');
}

function applyTheme(name) {
  const theme = THEMES.includes(name) ? name : 'light';
  document.documentElement.dataset.theme = theme;
  const meta = document.querySelector('meta[name="theme-color"]');
  if (meta) {
    meta.setAttribute('content',
      getComputedStyle(document.documentElement).getPropertyValue('--bg').trim() || '#f4f3ed');
  }
  syncThemeButton();
  remember(STORE.theme, theme);
}

function applyLanguage(name) {
  currentLang = resolveLang(name);
  applyTranslations(document, currentLang);
  const button = $('lang-toggle');
  if (button) {
    const other = currentLang === 'ar' ? 'en' : 'ar';
    button.title = t(currentLang, other === 'en' ? 'lang.switch_to_english' : 'lang.switch_to_arabic');
    setText(button.querySelector('span'), other === 'en' ? 'EN' : 'AR');
  }
  syncThemeButton();
  render();
  remember(STORE.lang, currentLang);
}

// ---------------------------------------------------------------- boot
async function load() {
  let response;
  try {
    response = await fetch('/api/results', { cache: 'no-store' });
  } catch (err) {
    state.failure = err?.name || 'Error';
    render();
    return;
  }
  if (response.status !== 200) {
    state.failure = String(response.status);
    render();
    return;
  }
  state.payload = await response.json();
  render();
}

function start() {
  $('theme-toggle')?.addEventListener('click', () => {
    applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
  });
  $('lang-toggle')?.addEventListener('click', () => {
    applyLanguage(currentLang === 'ar' ? 'en' : 'ar');
  });
  applyTheme(recall(STORE.theme, THEMES,
    window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'));
  applyLanguage(recall(STORE.lang, LANGS, DEFAULT_LANG));
  load().catch(err => {
    console.error(err);
    state.failure = err?.name || 'Error';
    render();
  });
}

start();
```

- [ ] **Step 9: Run the page tests and the tab's whole node set, and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/results-view.test.mjs static/sim/results-page.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)")
(cd app && node --test "static/sim/results-*.test.mjs" static/sim/charts-lib.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)")
$PY -m unittest app.test_results.PageTests 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"
```

Expected (observed in drafting, on a scratchpad clone of this tree with Tasks 6 to 8 applied from their plan text and Tasks 1 to 5 from their drafters' working copies; the time varies):

```
ℹ tests 27
ℹ pass 27
ℹ fail 0
ℹ tests 85
ℹ pass 85
ℹ fail 0
Ran 2 tests in 0.019s
OK
```

If `results-page.test.mjs` reports "the markup's text for <key>", the frame's Arabic and Task 6's string differ: copy the string from `results-strings.mjs` into `results.html` (an isolate as `&#x2066;`...`&#x2069;`), never the other way round.

- [ ] **Step 10: Move the two nav pins to five links, and see them fail**

The pins change first, so they fail on today's markup. In `app/static/sim/agents-page.test.mjs`, with the Edit tool, `old_string`:

```js
test('the nav reads simulation, agents (active), monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'agents.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, true, false, false]);
});
```

`new_string`:

```js
test('the nav reads simulation, agents (active), results, monitor, review', () => {
  const nav = read(HTML).match(/<nav[^>]*>([\s\S]*?)<\/nav>/);
  assert.ok(nav, 'agents.html has no <nav>');
  const links = [...nav[1].matchAll(/<a\b([^>]*)>/g)].map(m => m[1]);
  const attr = (a, name) => (a.match(new RegExp(`${name}="([^"]+)"`)) || [])[1];
  assert.deepEqual(links.map(a => attr(a, 'href')), ['/simulation', '/agents', '/results', '/', '/review']);
  assert.deepEqual(links.map(a => attr(a, 'data-i18n')),
    ['nav.simulation', 'nav.agents', 'nav.results', 'nav.monitor', 'nav.review']);
  assert.deepEqual(links.map(a => /\bclass="[^"]*\bactive\b/.test(a)), [false, true, false, false, false]);
});
```

In `app/test_agents.py`, with the Edit tool, `old_string` (the method as it stands, lines 3778-3802):

```python
    def test_the_lab_links_to_agents_where_phones_keep_it(self):
        """The replay lab's one link to /agents (design section 2, edit 4).

        Jad found on 28 Sep that the lab had no way to /agents. The link sits
        right AFTER the lab's first link, never at the end: the lab's phone
        rule hides .topbar nav a:last-child below 760 px (sim/style.css), so a
        link at the end would vanish on phones.
        """
        html = self.read("simulation.html")
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", html, flags=re.S)
        self.assertIsNotNone(nav, "simulation.html has no <nav>")
        links = re.findall(r"<a\b([^>]*)>", nav.group(1))

        def attr(tag, name):
            m = re.search(rf'\b{name}="([^"]*)"', tag)
            return m.group(1) if m else None

        self.assertEqual([attr(a, "href") for a in links], ["/simulation", "/agents", "/", "/review"])
        agents = links[1]
        self.assertEqual(attr(agents, "data-i18n"), "nav.agents")
        self.assertNotIn("active", attr(agents, "class") or "", "the lab's page stays the active one")
        self.assertIn("active", attr(links[0], "class") or "")
        self.assertIsNot(links[-1], agents, "the last link is hidden on phones")
        self.assertTrue(".topbar nav a:last-child{display:none}" in self.read("sim/style.css"),
                        "the phone rule this placement answers has moved; re-check where the link sits")
```

`new_string`:

```python
    def test_the_lab_links_to_agents_where_phones_keep_it(self):
        """The replay lab's links to /agents (design section 2, edit 4) and to
        /results (the results-tab design, its nav section).

        Jad found on 28 Sep that the lab had no way to /agents. The link sits
        right AFTER the lab's first link, never at the end: the lab's phone
        rule hides .topbar nav a:last-child below 760 px (sim/style.css), so a
        link at the end would vanish on phones. /results comes right after
        /agents, for the same reason. With five links the top bar ran wider
        than a phone, so style.css's last block now gives the nav a row of its
        own there and shows the last link again, as agents.css does on /agents;
        both links still sit before the last one, should that block ever go.
        """
        html = self.read("simulation.html")
        nav = re.search(r"<nav[^>]*>(.*?)</nav>", html, flags=re.S)
        self.assertIsNotNone(nav, "simulation.html has no <nav>")
        links = re.findall(r"<a\b([^>]*)>", nav.group(1))

        def attr(tag, name):
            m = re.search(rf'\b{name}="([^"]*)"', tag)
            return m.group(1) if m else None

        self.assertEqual([attr(a, "href") for a in links],
                         ["/simulation", "/agents", "/results", "/", "/review"])
        for i, key in ((1, "nav.agents"), (2, "nav.results")):
            self.assertEqual(attr(links[i], "data-i18n"), key)
            self.assertNotIn("active", attr(links[i], "class") or "", "the lab's page stays the active one")
            self.assertLess(i, len(links) - 1, "the last link is hidden on phones")
        self.assertIn("active", attr(links[0], "class") or "")
        style = self.read("sim/style.css")
        self.assertTrue(".topbar nav a:last-child{display:none}" in style,
                        "the phone rule this placement answers has moved; re-check where the link sits")
        self.assertTrue(".topbar nav{order:3;width:100%;height:40px;gap:16px}.topbar nav a:last-child{display:flex}"
                        in style, "five links need the nav's own row on phones (style.css, its last block)")
```

Run both:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/agents-page.test.mjs 2>&1 | grep -E "^✖ the nav|^ℹ (pass|fail)|actual: \[|expected: \[" | sort -u)
$PY -m unittest app.test_agents.PageTests.test_the_lab_links_to_agents_where_phones_keep_it 2>&1 | grep -E "^(FAIL|AssertionError|Ran|FAILED)"
```

Expected (observed in drafting):

```
    actual: [ '/simulation', '/agents', '/', '/review' ],
    expected: [ '/simulation', '/agents', '/results', '/', '/review' ],
ℹ fail 1
ℹ pass 9
✖ the nav reads simulation, agents (active), results, monitor, review (1.0ms)
FAIL: test_the_lab_links_to_agents_where_phones_keep_it (app.test_agents.PageTests.test_the_lab_links_to_agents_where_phones_keep_it)
AssertionError: Lists differ: ['/simulation', '/agents', '/', '/review'] != ['/simulation', '/agents', '/results', '/', '/review']
Ran 1 test in 0.155s
FAILED (failures=1)
```

- [ ] **Step 11: Add the link to both lab pages, and the nav's own row on phones**

In `app/static/simulation.html` (line 39), with the Edit tool, `old_string`:

```html
<a href="/agents" data-i18n="nav.agents">الوكلاء</a><a href="/" data-i18n="nav.monitor">المراقبة</a>
```

`new_string`:

```html
<a href="/agents" data-i18n="nav.agents">الوكلاء</a><a href="/results" data-i18n="nav.results">النتائج</a><a href="/" data-i18n="nav.monitor">المراقبة</a>
```

In `app/static/agents.html` (line 35), with the Edit tool, `old_string`:

```html
<a class="active" href="/agents" aria-current="page" data-i18n="nav.agents">الوكلاء</a><a href="/" data-i18n="nav.monitor">المراقبة</a>
```

`new_string`:

```html
<a class="active" href="/agents" aria-current="page" data-i18n="nav.agents">الوكلاء</a><a href="/results" data-i18n="nav.results">النتائج</a><a href="/" data-i18n="nav.monitor">المراقبة</a>
```

In `app/static/sim/style.css`, with the Edit tool, `old_string` is its last line:

```css
body.limit-near .world-panel{box-shadow:inset 0 0 0 2px var(--limit-near)}
```

`new_string`:

```css
body.limit-near .world-panel{box-shadow:inset 0 0 0 2px var(--limit-near)}

/* Five links since the results tab (results-tab design, the nav section). In
   one row on a phone they made the replay lab's top bar wider than the screen:
   measured in headless Chrome in a 390 px frame, the page scrolled sideways by
   33 px in English and 1 px in Arabic. So the nav takes a row of its own there,
   as agents.css has done for /agents, and with the room the last link, which
   the rule above hides, is shown again. With this block: no sideways scroll. */
@media(max-width:760px){.topbar{height:auto;flex-wrap:wrap;row-gap:0;padding:10px 16px 0}.topbar nav{order:3;width:100%;height:40px;gap:16px}.topbar nav a:last-child{display:flex}}
```

- [ ] **Step 12: Run the pins and the page test again, and see them pass**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
(cd app && node --test static/sim/agents-page.test.mjs static/sim/results-page.test.mjs 2>&1 | grep -E "^✖|^ℹ (tests|pass|fail)")
$PY -m unittest app.test_agents.PageTests.test_the_lab_links_to_agents_where_phones_keep_it 2>&1 | grep -E "^(FAIL|Ran|OK|FAILED)"
```

Expected (observed in drafting):

```
ℹ tests 18
ℹ pass 18
ℹ fail 0
Ran 1 test in 0.137s
OK
```

`agents-page.test.mjs` also checks that every key `agents.html` names exists in both languages: `nav.results` is Task 6's lab key in `i18n.mjs`.

- [ ] **Step 13: Byte-check, then the whole node suite, the lab's suites, and no new failing entry in `app.test_agents`**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
for f in app/static/sim/results-view.mjs app/static/sim/results.mjs app/static/sim/results-view.test.mjs app/static/sim/results-page.test.mjs app/static/results.html app/static/sim/style.css; do
  $PY -c "import sys; s=open(sys.argv[1],encoding='utf-8').read(); bs=chr(92); bad=[hex(ord(c)) for c in s if ord(c) in (0x2066,0x2067,0x2068,0x2069,0x200f,0x200e,0x202f,0x2212,0x2011)]; print(sys.argv[1], 'literal invisible:', bad, 'u-escapes:', s.count(bs+'u'), 'doubled backslashes:', s.count(bs+bs)); sys.exit(1 if bad else 0)" "$f"
done
(cd app && node --test "static/sim/*.test.mjs" > "$SP/r1a_node_task09.txt" 2>&1); grep -E "^ℹ (tests|pass|fail|skipped)" "$SP/r1a_node_task09.txt"
$PY -m app.test_simulation > "$SP/r1a_sim_task09.txt" 2>&1; tail -3 "$SP/r1a_sim_task09.txt"
$PY -m app.test_replay > "$SP/r1a_replay_task09.txt" 2>&1; grep -E "READ-ONLY|checks pass" "$SP/r1a_replay_task09.txt"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task09.txt" 2>&1
grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task09.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task09.txt" > "$SP/r1a_agents_fail_task09.txt"
echo "new failing entries:"; comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task09.txt"; echo "(end)"
```

Expected. Each byte-check line ends `literal invisible: [] u-escapes: 0 doubled backslashes: 0` (`style.css` too). The node suite: `ℹ tests 233`, `ℹ pass 225`, `ℹ fail 0`, `ℹ skipped 8` observed in drafting, on a scratchpad clone of this tree, which has no `app/node_modules` (the eight tests of `agent-scene.test.mjs` skip without `three`, as they did there before R1a: 148 tests, 140 pass, 8 skipped); on this tree, whose baseline is 148 of 148, expect `ℹ tests 233` and `ℹ pass 233`: 148 before R1a, and 85 from Tasks 6 to 9. `app.test_simulation`: `Ran 15 tests` and `OK`. `app.test_replay`: `PASS  READ-ONLY: no write path to the vehicle exists in app/   checked 5 patterns` and `49 of 49 checks pass` (its read-only scan reads `app/test_results.py` too, and `PageTests` holds no write). `app.test_agents` (not run on this tree in drafting; its count does not move, because this task edits one of its tests and adds none):

```
Ran 126 tests in 47.1s
FAILED (failures=16, errors=3, skipped=1)
new failing entries:
(end)
```

The baseline recorded `errors=3` on one run and `errors=4` on another. A line between `new failing entries:` and `(end)` that does not come back on a second run is that intermittent error, and goes in the task report; one that comes back is a regression of this task, fixed before the commit.

- [ ] **Step 14: Commit, by explicit path**

Another session edits `CLAUDE.md`, `handoff.md`, `team/jad.md` and `NEXT_SESSION_*.md` in this tree: `git commit -- <paths>` commits exactly these paths.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
PATHS="app/static/sim/results-view.mjs app/static/sim/results-view.test.mjs app/static/sim/results.mjs app/static/results.html app/static/sim/results-page.test.mjs app/test_results.py app/static/simulation.html app/static/agents.html app/static/sim/style.css app/test_agents.py app/static/sim/agents-page.test.mjs"
{
  printf '%s\n\n' "Results tab R1a (task 9): the page, its view helpers, and the nav link"
  printf '%s\n' \
    "app/static/results.html is the tab's frame, copied from agents.html, with no figure" \
    "in it. app/static/sim/results-view.mjs chooses every sentence of a section from the" \
    "values /api/results sends (pure); results.mjs fetches once, builds the summary and" \
    "one section per experiment, mounts each chart, rebuilds on a language switch and" \
    "redraws nothing on a theme switch. The chart host is a group, not an image: its" \
    "marks are focusable (spec 7.3)." \
    "" \
    "The lab's two pages gain the results link, third, and the two nav pins move with" \
    "them. With five links the lab's top bar ran wider than a phone, measured in a" \
    "390 px frame (spec 7.4), so style.css gives its nav a row of its own there, as" \
    "agents.css does for /agents." \
    ""
  printf '%s\n' "node --test static/sim/*.test.mjs:"
  grep -E "^ℹ (tests|pass|fail)" "$SP/r1a_node_task09.txt" | tr -d '\r'
  printf '%s\n' "" "python -m app.test_agents (new failing entries against the baseline: none):"
  grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task09.txt" | tr -d '\r'
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task09.txt"
cat "$SP/r1a_msg_task09.txt"
git add $PATHS
git commit -F "$SP/r1a_msg_task09.txt" -- $PATHS
git show --stat --format='%h %s' HEAD | head -15
```

Expected: the commit lists exactly these eleven paths (five new, six modified), and `git status --short` afterwards shows none of them.

### Task 10: The documents, the browser check, the full checks, and the build record

R1a is done when Jad opens `/results` and sees Phase D, D2 and C4, each labelled and quoted, in both languages (spec 10). This task names the tab where a person looks for it (`app/README.md`, the launcher's banner, CLAUDE.md's repository layout when no other session holds that file), drives the real page in headless Chrome at 1440 px and in a 390 px frame, runs every check of spec 9 once more, and appends the build record to the design.

**Three things drafting measured, which this task's steps already answer:**

- **Port 8765 is taken on this machine** by an unrelated program (a Codex runtime's `backend.server`, seen listening on `127.0.0.1:8765` on 5 October). The browser check starts the server on 8765 when it is free and otherwise on the next free port, and prints which (`INFO  server port 8766` in drafting).
- **The 390 px frame must sit on a left-to-right page.** The frame is placed on a page of the app's own origin (so the checks can read inside it); that page is `/results` with `dir="rtl"`, which pushed the frame to the right edge and every Arabic phone screenshot came out empty. The script sets the host page to `dir="ltr"` and checks the frame was captured where it was drawn.
- **A tab driven over the DevTools protocol never has the window's focus**, so `focus` events did not fire for the keyboard check until the script turned on focus emulation (`Emulation.setFocusEmulationEnabled`). The browser's own request for `/favicon.ico` answers 404 on every lab page; the console check ignores that one URL and nothing else.

`/simulation` at 1440 px is a little wider than the window (21 px in Arabic, 52 px in English): measured on the page as it was before R1a too, unchanged by the fifth link, and not this task's to change. The browser check measures sideways scroll at 390 px only, where R1a's nav change acts.

**Files:**
- Modify: `app/README.md:10-13` (the page table and the sentence under it) and after line 74 (a new section, "Opening the results tab, `/results`")
- Modify: `app/start-simulation.ps1:62-64` (two banner lines, above the blank line before the last line)
- Modify: `app/test_results.py` (`class DocsTests` above the file's last two lines)
- Modify: `CLAUDE.md`, the `app/` block of its repository layout (lines 2702-2716 at `031ed24`): ONLY when `git status --porcelain=v1 -- CLAUDE.md` prints nothing at that moment; otherwise it is skipped and the build record says so
- Modify: `docs/superpowers/specs/2026-09-30-results-tab-design.md` (`## Build record, R1a` appended at the end)
- Scratchpad only, never in the repository: `$SP/r1a_claude_layout.py`, `$SP/r1a-browser/results-browser-check.mjs` and its screenshots, `$SP/r1a_build_record.py`, and the captured outputs `$SP/r1a_*_task10.txt`

**Interfaces:**
- Consumes: Tasks 1 to 9 as running code: `python -m app.server --simulation` serves `/results` and `/api/results` (Task 5); the DOM of Task 9 (`.rc-section`, `.rc-verdict .verdict-short`, `#summary-rows tr`, `.rc-chart > svg`, `[data-figure="hand"]`, `#error`, `#summary`, `#built`, `#lang-toggle`, `#theme-toggle`); Task 7's `.rc-mark` (focusable, its tip on `pointerenter` and `focus`) and `.rc-tip`; the commit subjects `Results tab R1a (task N): ...` (contract section 0); `$SP/agents_baseline.txt` and Task 1's `norm()` comparison.
- Produces: `DocsTests` in `app/test_results.py`; the README section and table row; the banner line; the build record, whose headings are `## Build record, R1a`, `### What was built`, `### Commits`, `### The checks, as printed`, `### The build time of /api/results`, `### Left for R1b and R2`.

- [ ] **Step 1: Write the failing test for the documents**

Add `class DocsTests` to `app/test_results.py` with the Edit tool, above its last two lines as in Task 9 Step 5: `old_string` is the line `if __name__ == "__main__":`, `new_string` is the class below followed by that same line.

```python
class DocsTests(unittest.TestCase):
    """The lab's own documents name the results tab where a person looks for
    it: the launcher's banner and app/README.md's page table and its section
    (results-tab design, what else the change touches)."""

    def read(self, rel):
        path = ROOT / "app" / rel
        self.assertTrue(path.is_file(), f"app/{rel} does not exist")
        return path.read_text(encoding="utf-8")

    def test_the_launcher_names_the_results_tab_and_keeps_its_last_line(self):
        text = self.read("start-simulation.ps1")
        self.assertTrue("localhost:$Port/results" in text, "the banner does not name /results")
        self.assertLess(text.index("localhost:$Port/agents"), text.index("localhost:$Port/results"),
                        "the results line follows the agent replay's")
        self.assertEqual(text.rstrip().splitlines()[-1],
                         "python -m app.server --simulation --http-port $Port")

    def test_the_readme_lists_the_page_and_says_how_to_open_it(self):
        text = self.read("README.md")
        rows = [line for line in text.splitlines() if line.startswith("| `/")]
        self.assertEqual([row.split("|")[1].strip() for row in rows],
                         ["`/` and `/driver`", "`/review`", "`/simulation`", "`/agents`", "`/results`"])
        self.assertIn("**none, ever**", rows[-1], "the results tab has no vehicle connection")
        self.assertIn("### Opening the results tab, `/results`", text)
        section = text.split("### Opening the results tab, `/results`", 1)[1].split("\n---", 1)[0]
        for needed in ("--simulation", "http://localhost:8000/results", "python -m app.test_results"):
            self.assertIn(needed, section, f"the section does not say {needed}")


if __name__ == "__main__":
```

Run it:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.DocsTests 2>&1 | grep -E "^(FAIL|AssertionError|Ran|FAILED)" | cut -c1-140
```

Expected (observed in drafting; `cut` keeps the first 140 characters of a line):

```
FAIL: test_the_launcher_names_the_results_tab_and_keeps_its_last_line (app.test_results.DocsTests.test_the_launcher_names_the_results_tab_an
AssertionError: False is not true : the banner does not name /results
FAIL: test_the_readme_lists_the_page_and_says_how_to_open_it (app.test_results.DocsTests.test_the_readme_lists_the_page_and_says_how_to_open
AssertionError: Lists differ: ['`/` and `/driver`', '`/review`', '`/simulation`', '`/agents`'] != ['`/` and `/driver`', '`/review`', '`/simu
Ran 2 tests in 0.001s
FAILED (failures=2)
```

- [ ] **Step 2: Name the tab in the README and the launcher**

`app/README.md`, first edit, with the Edit tool. `old_string`:

````markdown
| `/agents` | **the agent replay page** — two trained agents on one simulated episode | **none, ever** |

Everything below is about `/simulation`, except the section on opening
`/agents`. For the supervisor read `CLAUDE.md` and `AUDIT.md` first.
````

`new_string`:

````markdown
| `/agents` | **the agent replay page** — two trained agents on one simulated episode | **none, ever** |
| `/results` | **the results tab** — every experiment in `results/`, as its files record it | **none, ever** |

Everything below is about `/simulation`, except the sections on opening
`/agents` and `/results`. For the supervisor read `CLAUDE.md` and `AUDIT.md` first.
````

`app/README.md`, second edit (the end of the section "Opening the agents page"), with the Edit tool. `old_string`:

````markdown
it has been computed. Everything on the page is a simulation, and nothing is
written to disk.

---
````

`new_string`:

````markdown
it has been computed. Everything on the page is a simulation, and nothing is
written to disk.

### Opening the results tab, `/results`

Like `/agents`, the tab exists only when the server runs with `--simulation`.
It replays nothing and needs neither stable-baselines3 nor torch, so any
interpreter that runs the lab runs it, `app\start-simulation.ps1` included:

```powershell
C:\Users\admin\AppData\Local\Programs\Python\Python312\python.exe -m app.server --simulation
```

Then open <http://localhost:8000/results>. Every time the page opens, the
server reads `results/` again: each experiment is its own section, never
counted together with another, labelled with the plant its files record, its
preregistered verdict quoted word for word with its file and line, and its
charts show their numbers under the pointer, on a tap and in a folded table.
Nothing is recomputed and nothing is written. After a new drive, a retrain or a
new experiment, re-run the scripts that write `results/` and reload the page.
It answers only a browser on this machine (`127.0.0.1` or `localhost`). Its
own suite is `python -m app.test_results`.

---
````

(The claim "needs neither stable-baselines3 nor torch" was measured in drafting: `app.results_data.build()` ran in a process where both imports were blocked, `sys.modules["torch"] = sys.modules["stable_baselines3"] = None`, and returned all three sections with their verdicts found.)

`app/start-simulation.ps1`, with the Edit tool. `old_string`:

```powershell
    Write-Host '      <that python> -m app.server --simulation'
}
Write-Host ''
```

`new_string`:

```powershell
    Write-Host '      <that python> -m app.server --simulation'
}
Write-Host '  results tab    ->  ' -NoNewline
Write-Host "http://localhost:$Port/results"
Write-Host ''
```

Run the test, and `app.test_agents`' own pin on the launcher (its last line must not move):

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
$PY -m unittest app.test_results.DocsTests app.test_agents.PageTests.test_the_lab_launcher_names_the_agents_page 2>&1 | grep -E "^(FAIL|ERROR|Ran|OK|FAILED)"
```

Expected (observed in drafting; the time varies):

```
Ran 3 tests in 0.002s
OK
```

- [ ] **Step 3: CLAUDE.md's repository layout, only if no other session holds the file**

Another session edits `CLAUDE.md` in this tree. Check first; if `git status` names the file, do not touch it, and the build record will say it was skipped.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
GIT_OPTIONAL_LOCKS=0 git status --porcelain=v1 -- CLAUDE.md; echo "(status end)"
```

**If a line appears before `(status end)`:** skip the rest of this step and record why:

```bash
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
printf '%s\n' "skipped (another session had CLAUDE.md modified when this task ran)" > "$SP/r1a_claude_task10.txt"
```

**If nothing appears:** create `$SP/r1a_claude_layout.py` with the Write tool (a scratchpad file, not the repository; it holds no backslash, so no tool can change it on the way):

```python
from pathlib import Path

# CLAUDE.md's repository layout gains the results tab's files, inside its app/
# block, right above review_log.jsonl. The working tree checks out CRLF; the
# file's own line ending is kept. Refuses if an anchor is missing or if the
# lines are already there.
path = Path("CLAUDE.md")
src = path.read_bytes().decode("utf-8")
nl = chr(13) + chr(10) if chr(13) + chr(10) in src else chr(10)
SERVER_OLD = [
    "  server.py           localhost. /, /driver, /review; --simulation adds the 3D",
    "                      replay lab and the agents page, with no vehicle connection.",
]
SERVER_NEW = [
    "  server.py           localhost. /, /driver, /review; --simulation adds the 3D",
    "                      replay lab, the agents page and the results tab, with no",
    "                      vehicle connection.",
]
ANCHOR = "  review_log.jsonl    Generated, gitignored. Marked events only, never raw data."
ADDED = [
    "  results_api.py      The results tab (--simulation only): GET /results and",
    "                      GET /api/results, answered to this machine only.",
    "  results_data.py     Reads results/ on every request: one section per",
    "                      experiment, its verdict quoted, nothing recomputed.",
    "  results_provenance.py  Where a result file's numbers came from: the plant",
    "                      states, the git facts, this tree's fingerprint.",
    "  results_eval.py     Parses one evaluate.py result file, results/<prefix>_seed<N>.txt.",
    "  test_results.py     The results tab's suite.",
    "  static/results.html, static/sim/results*.mjs, charts-lib.mjs",
    "                      The results tab's page: view, charts, strings, styles.",
]
assert ADDED[0] not in src, "CLAUDE.md already lists the results tab"
old = nl.join(SERVER_OLD) + nl
assert src.count(old) == 1, "the server.py lines of the layout have moved"
src = src.replace(old, nl.join(SERVER_NEW) + nl)
assert src.count(ANCHOR + nl) == 1, "the review_log.jsonl line of the layout has moved"
src = src.replace(ANCHOR + nl, nl.join(ADDED) + nl + ANCHOR + nl)
path.write_bytes(src.encode("utf-8"))
print("CLAUDE.md: the layout names the results tab (", len(ADDED), "lines added )")
```

and run it from the repository root:

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
if $PY "$SP/r1a_claude_layout.py"; then
  git diff --stat -- CLAUDE.md
  printf '%s\n' "edited (its app/ block lists the results modules and the page)" > "$SP/r1a_claude_task10.txt"
else
  printf '%s\n' "skipped (the layout script refused: an anchor had moved)" > "$SP/r1a_claude_task10.txt"
fi
cat "$SP/r1a_claude_task10.txt"
```

Expected (observed in drafting, on `031ed24`'s CLAUDE.md):

```
CLAUDE.md: the layout names the results tab ( 10 lines added )
 CLAUDE.md | 13 ++++++++++++-
 1 file changed, 12 insertions(+), 1 deletion(-)
edited (its app/ block lists the results modules and the page)
```

The script refuses, and changes nothing, when either anchor has moved or the lines are already there (`AssertionError: ...`); the branch above then records the skip, and `CLAUDE.md` stays out of the commit.

- [ ] **Step 4: Commit the documents, by explicit path**

`CLAUDE.md` is in the list only when Step 3 edited it.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
PATHS="app/README.md app/start-simulation.ps1 app/test_results.py"
grep -q '^edited' "$SP/r1a_claude_task10.txt" && PATHS="$PATHS CLAUDE.md"
{
  printf '%s\n\n' "Results tab R1a (task 10): the tab in the README, the launcher and the layout"
  printf '%s\n' \
    "app/README.md lists /results in its page table and says how to open it: under" \
    "--simulation only, with any interpreter that runs the lab, read from results/ on" \
    "every open, answered to this machine only. app/start-simulation.ps1 names it in its" \
    "banner; its last line is unchanged. DocsTests in app/test_results.py pins both." \
    "CLAUDE.md's repository layout: $(cat "$SP/r1a_claude_task10.txt")." \
    ""
  printf '%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task10_docs.txt"
cat "$SP/r1a_msg_task10_docs.txt"
git add $PATHS
git commit -F "$SP/r1a_msg_task10_docs.txt" -- $PATHS
git show --stat --format='%h %s' HEAD | head -8
```

Expected: one commit with three paths (four with `CLAUDE.md`).

- [ ] **Step 5: Write the browser check (scratchpad only)**

Create `$SP/r1a-browser/results-browser-check.mjs` with the Write tool, where `$SP` is the scratchpad above. It is not repository code. It holds no backslash-u escape and no doubled backslash.

```js
// R1a browser check for the results tab (scratchpad only, NOT repository code).
// Starts `<python> -m app.server --simulation --http-port 8765` from the
// repository root, drives the installed Chrome over the DevTools protocol with
// Node's built-in fetch and WebSocket, checks /results, takes screenshots of
// /results, /simulation and /agents at 1440 px and inside a 390 px frame (this
// headless Chrome will not lay out below 500 px), both languages and both
// themes, then stops the server and Chrome and deletes Chrome's profile.
//   node results-browser-check.mjs <repo> <out-dir> <python>
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync, openSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createServer } from 'node:net';

const REPO = resolve(process.argv[2] || '.');
const OUT = resolve(process.argv[3] || '.');
const PY = process.argv[4] || 'python';
const CHROME = process.env.CHROME || 'C:/Program Files/Google/Chrome/Application/chrome.exe';
// 8765 unless something on this machine already holds it, then the next free one.
const bindable = port => new Promise(ok => {
  const probe = createServer().once('error', () => ok(false))
    .once('listening', () => probe.close(() => ok(true))).listen(port, '127.0.0.1');
});
let HTTP = 8765;
while (!(await bindable(HTTP))) HTTP += 1;
const CDP = 9365;
const BASE = `http://127.0.0.1:${HTTP}`;
console.log(`INFO  server port ${HTTP}`);
const PROFILE = join(OUT, 'chrome-profile-r1a');
const sleep = ms => new Promise(r => setTimeout(r, ms));
const results = [];
function check(name, ok, detail = '') {
  results.push({ name, ok: Boolean(ok), detail: String(detail).slice(0, 500) });
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}${ok ? '' : `  -- ${detail}`}`);
}

mkdirSync(OUT, { recursive: true });
const log = openSync(join(OUT, 'server.log'), 'w');
const server = spawn(PY, ['-B', '-m', 'app.server', '--simulation', '--http-port', String(HTTP)], {
  cwd: REPO, stdio: ['ignore', log, log],
  env: { ...process.env, PYTHONIOENCODING: 'utf-8', GIT_OPTIONAL_LOCKS: '0', PYTHONDONTWRITEBYTECODE: '1' },
});
let chrome = null;
let ws = null;

async function waitForServer() {
  for (let i = 0; i < 600; i++) {
    try {
      const r = await fetch(`${BASE}/results`);
      if (r.status === 200) return true;
    } catch { /* not listening yet */ }
    await sleep(200);
  }
  return false;
}

let id = 0;
const pending = new Map();
const errors = [];
const send = (method, params = {}) => new Promise((ok, bad) => {
  id += 1;
  pending.set(id, m => (m.error ? bad(new Error(`${method}: ${m.error.message}`)) : ok(m.result)));
  ws.send(JSON.stringify({ id, method, params }));
});
const ev = async expression => {
  const r = await send('Runtime.evaluate', { expression, returnByValue: true, awaitPromise: true });
  if (r.exceptionDetails) throw new Error(r.exceptionDetails.exception?.description || r.exceptionDetails.text);
  return r.result.value;
};
const until = async (expr, ms) => {
  const t0 = Date.now();
  while (Date.now() - t0 < ms) {
    try { if (await ev(expr)) return true; } catch { /* the page is between documents */ }
    await sleep(150);
  }
  return false;
};
async function prefs(theme, lang) {
  await ev(`localStorage.setItem('grad.sim.theme', '${theme}'); localStorage.setItem('grad.sim.lang', '${lang}'); true`);
}
async function go(path, settle = 1500) {
  await send('Page.navigate', { url: `${BASE}${path}` });
  await sleep(settle);
}
async function shotFull(name) {
  const size = await ev(`({ w: document.documentElement.scrollWidth, h: document.documentElement.scrollHeight })`);
  const res = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: size.w, height: Math.min(size.h, 16000), scale: 1 } });
  writeFileSync(join(OUT, name), Buffer.from(res.data, 'base64'));
  console.log(`SHOT  ${join(OUT, name)}`);
}
// The page at `path` inside a 390 px frame on a same-origin page; returns
// what the nav and the document measure inside it, then screenshots it whole.
async function shotPhone(path, name, ready) {
  await go('/results', 1200);
  await ev(`(() => { document.documentElement.innerHTML = '<head></head><body style="margin:0;background:#888"></body>';
    document.documentElement.setAttribute('dir', 'ltr');
    const f = document.createElement('iframe'); f.id = 'phone'; f.src = '${path}';
    f.style.cssText = 'width:390px;height:844px;border:0;display:block;background:#fff';
    document.body.appendChild(f); return true; })()`);
  const doc = `document.getElementById('phone').contentDocument`;
  await until(`${doc} && ${doc}.readyState === 'complete' && (${ready.replace(/document/g, doc)})`, 30000);
  await sleep(800);
  const m = await ev(`(() => { const d = ${doc}; const nav = d.querySelector('.topbar nav');
    const link = d.querySelector('.topbar nav a[href="/results"]');
    return { navOverflow: nav ? nav.scrollWidth - nav.clientWidth : null,
      resultsLink: link ? Math.round(link.getBoundingClientRect().width) : null,
      pageOverflow: d.documentElement.scrollWidth - d.documentElement.clientWidth,
      height: d.documentElement.scrollHeight }; })()`);
  await ev(`(() => { const f = document.getElementById('phone'); f.style.height = '${Math.min(m.height, 15000)}px'; return true; })()`);
  await sleep(600);
  const res = await send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: true,
    clip: { x: 0, y: 0, width: 390, height: Math.min(m.height, 15000), scale: 1 } });
  writeFileSync(join(OUT, name), Buffer.from(res.data, 'base64'));
  console.log(`SHOT  ${join(OUT, name)}`);
  m.frameLeft = await ev(`Math.round(document.getElementById('phone').getBoundingClientRect().left)`);
  return m;
}

const READY = {
  '/results': `document.querySelectorAll('.rc-section').length > 0 && document.querySelectorAll('.rc-chart > svg').length > 0`,
  '/simulation': `document.querySelector('.topbar nav') !== null`,
  '/agents': `document.querySelector('.topbar nav') !== null`,
};

try {
  const up = await waitForServer();
  check('the server answers /results', up, 'no 200 from /results within 120 s; see server.log');
  if (!up) throw new Error('server did not start');
  // The build's own clock (built.elapsed_ms) and the wall clock, on the first
  // request after the server started and on the next one.
  const timed = async () => {
    const t0 = Date.now();
    const r = await fetch(`${BASE}/api/results`);
    const body = await r.json();
    return { status: r.status, cache: r.headers.get('cache-control'), build: body.built?.elapsed_ms, wall: Date.now() - t0 };
  };
  const cold = await timed();
  const warm = await timed();
  console.log(`INFO  /api/results build: cold ${cold.build} ms (wall ${cold.wall} ms), warm ${warm.build} ms (wall ${warm.wall} ms)`);
  check('/api/results answers 200 with no-store', cold.status === 200 && cold.cache === 'no-store' && warm.status === 200,
    JSON.stringify({ cold, warm }));

  mkdirSync(PROFILE, { recursive: true });
  chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${CDP}`, `--user-data-dir=${PROFILE}`,
    '--no-first-run', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--hide-scrollbars', 'about:blank'],
  { stdio: 'ignore' });
  for (let i = 0; i < 400; i++) { try { await fetch(`http://127.0.0.1:${CDP}/json/version`); break; } catch { await sleep(100); } }
  const target = await (await fetch(`http://127.0.0.1:${CDP}/json/new?about:blank`, { method: 'PUT' })).json();
  ws = new WebSocket(target.webSocketDebuggerUrl);
  await new Promise(r => ws.addEventListener('open', r, { once: true }));
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
      errors.push(`console.error: ${m.params.args.map(a => a.value ?? a.description).join(' ')}`);
    }
    if (m.method === 'Runtime.exceptionThrown') errors.push(`exception: ${m.params.exceptionDetails.exception?.description || m.params.exceptionDetails.text}`);
    // The browser asks for /favicon.ico by itself; no lab page has one, and its 404 is not the page's.
    if (m.method === 'Log.entryAdded' && m.params.entry.level === 'error' && !/\/favicon\.ico$/.test(m.params.entry.url || '')) errors.push(`log: ${m.params.entry.text} ${m.params.entry.url || ''}`);
  });
  await send('Runtime.enable'); await send('Page.enable'); await send('Log.enable');
  // A tab driven over the protocol never has the window's focus, so focus
  // events would not fire for the keyboard check; this emulates it.
  await send('Emulation.setFocusEmulationEnabled', { enabled: true });
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

  // ---- the checks, at 1440 px, Arabic and light first
  await go('/results', 800);
  await prefs('light', 'ar');
  const t0 = Date.now();
  await go('/results', 300);
  const drawn = await until(READY['/results'], 60000);
  check('the page draws its charts', drawn, `no .rc-chart > svg after ${Date.now() - t0} ms`);
  console.log(`INFO  first draw after ${Date.now() - t0} ms`);
  const sections = await ev(`[...document.querySelectorAll('.rc-section')].map(s => ({ id: s.id,
    short: s.querySelector('.rc-verdict .verdict-short')?.textContent || '', charts: s.querySelectorAll('.rc-chart > svg').length }))`);
  check('three .rc-section elements', sections.length === 3, JSON.stringify(sections.map(s => s.id)));
  check('each section has a verdict short line', sections.length > 0 && sections.every(s => s.short.trim() && s.short.trim() !== '—'),
    JSON.stringify(sections.map(s => s.short)));
  check('the summary has one row per section', await ev(`document.querySelectorAll('#summary-rows tr').length`) === sections.length);
  const sizes = await ev(`[...document.querySelectorAll('.rc-chart > svg')].map(s => ({ attr: Number(s.getAttribute('width')),
    shown: s.getBoundingClientRect().width }))`);
  check('every .rc-chart > svg is drawn at its width attribute',
    sizes.length > 0 && sizes.every(s => Math.abs(s.attr - s.shown) < 0.5), JSON.stringify(sizes.slice(0, 4)));
  check('a chart label has no stroke', await ev(`getComputedStyle(document.querySelector('.rc-chart > svg text')).stroke`) === 'none',
    await ev(`getComputedStyle(document.querySelector('.rc-chart > svg text')).stroke`));
  check('no Arabic letter in any chart label', await ev(`[...document.querySelectorAll('.rc-chart svg text')].every(t =>
    ![...t.textContent].some(c => c.codePointAt(0) >= 0x600 && c.codePointAt(0) <= 0x6ff))`));

  const tipShown = await ev(`(() => { const m = document.querySelector('.rc-mark');
    m.dispatchEvent(new PointerEvent('pointerenter', { pointerType: 'mouse' }));
    const tip = m.closest('.rc-chart').querySelector(':scope > .rc-tip');
    return { hidden: tip ? tip.hidden : null, text: tip ? tip.textContent : '' }; })()`);
  check('a pointerenter on the first .rc-mark shows a .rc-tip with a digit', tipShown.hidden === false && /\d/.test(tipShown.text),
    JSON.stringify(tipShown));
  const keyTip = await ev(`(() => { const marks = document.querySelectorAll('[data-figure="hand"] .rc-mark');
    const m = marks[marks.length - 1]; m.focus();
    const tip = m.closest('.rc-chart').querySelector(':scope > .rc-tip');
    return { focused: document.activeElement === m, hidden: tip ? tip.hidden : null, text: tip ? tip.textContent : '' }; })()`);
  check('keyboard focus on a mark of the hand chart shows its tip', keyTip.focused && keyTip.hidden === false && /\d/.test(keyTip.text),
    JSON.stringify(keyTip));
  await ev(`document.activeElement.blur(); document.body.dispatchEvent(new PointerEvent('pointerdown', { bubbles: true })); true`);

  const mark = `[...document.querySelectorAll('.rc-chart > svg')].forEach(s => { s.__r1a = true; }); true`;
  const before = await ev(`({ dir: document.documentElement.dir, n: document.querySelectorAll('.rc-chart > svg').length, title: document.title })`);
  await ev(mark);
  await ev(`document.getElementById('lang-toggle').click(); true`);
  await sleep(600);
  const afterLang = await ev(`({ dir: document.documentElement.dir, lang: document.documentElement.lang,
    n: document.querySelectorAll('.rc-chart > svg').length,
    kept: [...document.querySelectorAll('.rc-chart > svg')].filter(s => s.__r1a).length, title: document.title,
    h2: document.querySelector('.rc-section h2')?.textContent, short: document.querySelector('.rc-verdict .verdict-short')?.textContent })`);
  check('the language button switches dir and redraws every chart',
    before.dir === 'rtl' && afterLang.dir === 'ltr' && afterLang.lang === 'en' && afterLang.n === before.n && afterLang.kept === 0,
    JSON.stringify({ before, afterLang }));
  await ev(mark);
  const themeBefore = await ev(`document.documentElement.dataset.theme`);
  await ev(`document.getElementById('theme-toggle').click(); true`);
  await sleep(400);
  const afterTheme = await ev(`({ theme: document.documentElement.dataset.theme, n: document.querySelectorAll('.rc-chart > svg').length,
    kept: [...document.querySelectorAll('.rc-chart > svg')].filter(s => s.__r1a).length,
    sighted: getComputedStyle(document.documentElement).getPropertyValue('--rc-sighted').trim() })`);
  check('the theme button switches data-theme and redraws nothing',
    themeBefore === 'light' && afterTheme.theme === 'dark' && afterTheme.kept === afterTheme.n && afterTheme.n > 0,
    JSON.stringify({ themeBefore, afterTheme }));

  // ---- the screenshots: three pages x two languages x two themes, at 1440 and at 390
  const phone = {};
  for (const path of ['/results', '/simulation', '/agents']) {
    for (const lang of ['ar', 'en']) {
      for (const theme of ['light', 'dark']) {
        const tag = `${path.slice(1)}-${lang}-${theme}`;
        await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
        await prefs(theme, lang);
        await go(path, 300);
        await until(READY[path], 60000);
        await sleep(path === '/results' ? 800 : 2500);
        await shotFull(`r1a-1440-${tag}.png`);
        phone[tag] = await shotPhone(path, `r1a-390-${tag}.png`, READY[path]);
      }
    }
  }
  for (const [tag, m] of Object.entries(phone)) {
    console.log(`INFO  390 ${tag}: nav overflow ${m.navOverflow} px, results link ${m.resultsLink} px wide, page overflow ${m.pageOverflow} px`);
  }
  check('at 390 px every nav keeps its results link visible and inside its row',
    Object.values(phone).every(m => m.resultsLink > 0 && m.navOverflow <= 1), JSON.stringify(phone));
  check('at 390 px no page scrolls sideways', Object.values(phone).every(m => m.pageOverflow === 0), JSON.stringify(phone));
  check('every 390 px frame was captured where it was drawn', Object.values(phone).every(m => m.frameLeft === 0), JSON.stringify(phone));
  check('no console error, exception or failed load', errors.length === 0, errors.join(' | '));

  // ---- last: a failing /api/results shows the error line and nothing else.
  // Answered by the browser itself (the server is never asked), so this run's
  // own 500 is expected in the console and is not counted above.
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await prefs('light', 'en');
  await send('Fetch.enable', { patterns: [{ urlPattern: '*/api/results*' }] });
  const onPaused = e => {
    const m = JSON.parse(e.data);
    if (m.method !== 'Fetch.requestPaused') return;
    send('Fetch.fulfillRequest', { requestId: m.params.requestId, responseCode: 500,
      responseHeaders: [{ name: 'Content-Type', value: 'application/json' }],
      body: Buffer.from('{"detail": "results failed: RuntimeError"}').toString('base64') }).catch(() => {});
  };
  ws.addEventListener('message', onPaused);
  await go('/results', 1500);
  const failed = await ev(`({ error: document.getElementById('error').hidden ? null : document.getElementById('error').textContent,
    sections: document.querySelectorAll('.rc-section').length, summary: document.getElementById('summary').hidden,
    built: document.getElementById('built').hidden })`);
  ws.removeEventListener('message', onPaused);
  await send('Fetch.disable');
  check('a 500 from /api/results shows only the error line, with its status',
    failed.error !== null && failed.error.includes('500') && failed.sections === 0 && failed.summary && failed.built,
    JSON.stringify(failed));
} catch (err) {
  check('the check ran to the end', false, err && err.stack);
} finally {
  try { ws?.close(); } catch { /* already closed */ }
  try { chrome?.kill(); } catch { /* already gone */ }
  try { server.kill(); } catch { /* already gone */ }
  await sleep(2000);
  try { rmSync(PROFILE, { recursive: true, force: true }); console.log('INFO  chrome profile deleted'); } catch (e) { console.log(`INFO  profile not deleted: ${e.message}`); }
  writeFileSync(join(OUT, 'r1a-browser-report.json'), JSON.stringify(results, null, 1));
  const failed = results.filter(r => !r.ok).length;
  console.log(`${results.length - failed} of ${results.length} browser checks pass`);
  process.exit(failed ? 1 : 0);
}
```

- [ ] **Step 6: Run the browser check**

It starts the server itself from the repository root (`$PY -B -m app.server --simulation --http-port 8765`, or the next free port), opens headless Chrome with a profile inside `$SP/r1a-browser`, checks, takes 24 screenshots (three pages, two languages, two themes, at 1440 px and in a 390 px frame), and stops both and deletes the profile in its `finally`, pass or fail. About four minutes: opening `/simulation` starts the lab's first drive computation, which the server's stop ends.

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
node "$SP/r1a-browser/results-browser-check.mjs" "$PWD" "$SP/r1a-browser" "$PY" 2>&1 | tee "$SP/r1a_browser_task10.txt" | grep -v "^SHOT"
ls "$SP/r1a-browser"/*.png | wc -l
netstat -ano | grep -E ":876[5-9] .*LISTENING|:9365 .*LISTENING"; echo "(listeners end)"
```

Git Bash turns the POSIX paths `$PWD`, `$SP/...` and `$PY` into Windows paths for `node` (do not set `MSYS_NO_PATHCONV`). Expected (observed in drafting on a scratchpad clone of this tree with Tasks 6 to 8 applied from their plan text and Tasks 1 to 5 from their drafters' working copies, and Task 9 from this plan; the times and the port vary):

```
INFO  server port 8766
PASS  the server answers /results
INFO  /api/results build: cold 604 ms (wall 631 ms), warm 528 ms (wall 540 ms)
PASS  /api/results answers 200 with no-store
PASS  the page draws its charts
INFO  first draw after 776 ms
PASS  three .rc-section elements
PASS  each section has a verdict short line
PASS  the summary has one row per section
PASS  every .rc-chart > svg is drawn at its width attribute
PASS  a chart label has no stroke
PASS  no Arabic letter in any chart label
PASS  a pointerenter on the first .rc-mark shows a .rc-tip with a digit
PASS  keyboard focus on a mark of the hand chart shows its tip
PASS  the language button switches dir and redraws every chart
PASS  the theme button switches data-theme and redraws nothing
INFO  390 results-ar-light: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 results-ar-dark: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 results-en-light: nav overflow 0 px, results link 31 px wide, page overflow 0 px
INFO  390 results-en-dark: nav overflow 0 px, results link 31 px wide, page overflow 0 px
INFO  390 simulation-ar-light: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 simulation-ar-dark: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 simulation-en-light: nav overflow 0 px, results link 31 px wide, page overflow 0 px
INFO  390 simulation-en-dark: nav overflow 0 px, results link 31 px wide, page overflow 0 px
INFO  390 agents-ar-light: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 agents-ar-dark: nav overflow 0 px, results link 24 px wide, page overflow 0 px
INFO  390 agents-en-light: nav overflow 0 px, results link 31 px wide, page overflow 0 px
INFO  390 agents-en-dark: nav overflow 0 px, results link 31 px wide, page overflow 0 px
PASS  at 390 px every nav keeps its results link visible and inside its row
PASS  at 390 px no page scrolls sideways
PASS  every 390 px frame was captured where it was drawn
PASS  no console error, exception or failed load
PASS  a 500 from /api/results shows only the error line, with its status
INFO  chrome profile deleted
18 of 18 browser checks pass
24
(listeners end)
```

The listener check may still show the unrelated program on 8765; it must show nothing on the port the script printed, nor on 9365. Look at a few screenshots (the Read tool shows PNG files): `r1a-1440-results-ar-light.png`, `r1a-390-results-ar-dark.png`, `r1a-390-simulation-en-light.png` (the lab's nav on its own row, five links). A FAIL line names its check and what it saw; fix the task that owns it, re-run this step, and only then continue.

- [ ] **Step 7: Run every check of spec 9 once, each captured**

`drift_test.py` takes more than ten minutes here (sixteen copies of the tree, each scanned by `verify_docs.py`): the whole block runs past the Bash tool's ten-minute limit for a command (its timeout cannot be set higher), so run it in the background and wait for it (in the integration run, with other work beside it, the block took about 35 minutes).

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY -m app.test_results > "$SP/r1a_results_task10.txt" 2>&1; grep -E "^(Ran|OK|FAILED)" "$SP/r1a_results_task10.txt"
norm() { grep -E "^(FAIL|ERROR):" "$1" | sed -E 's/\((app\.test_agents|__main__)\./(/' | sort; }
$PY -m app.test_agents -v > "$SP/r1a_agents_task10.txt" 2>&1; grep -E "^(Ran|OK|FAILED)" "$SP/r1a_agents_task10.txt"
norm "$SP/agents_baseline.txt" > "$SP/r1a_agents_fail_before.txt"
norm "$SP/r1a_agents_task10.txt" > "$SP/r1a_agents_fail_task10.txt"
comm -13 "$SP/r1a_agents_fail_before.txt" "$SP/r1a_agents_fail_task10.txt" > "$SP/r1a_agents_new_task10.txt"
echo "new failing entries:"; cat "$SP/r1a_agents_new_task10.txt"; echo "(end)"
$PY -m app.test_simulation > "$SP/r1a_sim_task10.txt" 2>&1; tail -3 "$SP/r1a_sim_task10.txt"
$PY -m app.test_replay > "$SP/r1a_replay_task10.txt" 2>&1; grep -E "READ-ONLY|checks pass" "$SP/r1a_replay_task10.txt"
(cd app && node --test "static/sim/*.test.mjs" > "$SP/r1a_node_task10.txt" 2>&1); grep -E "^ℹ (tests|pass|fail|skipped)" "$SP/r1a_node_task10.txt"
$PY verify_docs.py > "$SP/r1a_verify_docs_task10.txt" 2>&1; tail -1 "$SP/r1a_verify_docs_task10.txt"
$PY drift_test.py > "$SP/r1a_drift_task10.txt" 2>&1; tail -3 "$SP/r1a_drift_task10.txt"
```

Expected. `app.test_results`: `Ran 108 tests` and `OK` (every task's tests together: 27, 17, 21, 27, 12, 2 and 2; drafting saw `Ran 42 tests` with only Tasks 4, 5, 9 and 10, when Task 5 had 11). `app.test_agents`: `Ran 126 tests`, `FAILED (failures=16, errors=3, skipped=1)` (the baseline; `errors=4` on some runs), and nothing between `new failing entries:` and `(end)` (not run on this tree in drafting; see Task 9 Step 13 for a line that appears once). `app.test_simulation`: `Ran 15 tests` and `OK`. `app.test_replay`: the READ-ONLY line and `49 of 49 checks pass`. Node: `ℹ tests 233`, `ℹ pass 225`, `ℹ fail 0`, `ℹ skipped 8` observed in drafting, on a scratchpad clone of this tree, which has no `app/node_modules` (the eight tests of `agent-scene.test.mjs` skip without `three`, as they did there before R1a: 148 tests, 140 pass, 8 skipped); on this tree, whose baseline is 148 of 148, expect `ℹ tests 233` and `ℹ pass 233`: 148 before R1a, and 85 from Tasks 6 to 9. `verify_docs.py`: `All 73 checks pass (849 figure mentions scanned in the documents).` (observed in drafting with Tasks 1 to 10 applied, every new file tracked; the mention count moves when a document does). `drift_test.py`: `16 of 16 drifts CAUGHT` (observed in drafting on the same clone).

Any failure here is fixed in the task that owns it, in a new commit by explicit path (never an amend), and this step is re-run before the record is written.

- [ ] **Step 8: Append the build record to the design**

Create `$SP/r1a_build_record.py` with the Write tool (scratchpad only; it holds no backslash):

```python
import datetime
import re
import subprocess
import sys
from pathlib import Path

# Appends "Build record, R1a" to the design, from the outputs Task 10 captured
# in the scratchpad (argv[1]). Every figure in it is copied from a run; the
# script refuses to run twice and refuses a missing capture.
SP = Path(sys.argv[1])
SPEC = Path("docs/superpowers/specs/2026-09-30-results-tab-design.md")
NL = chr(10)


def read(name):
    path = SP / name
    assert path.is_file(), f"missing capture {path}: run the step that writes it"
    return path.read_text(encoding="utf-8", errors="replace").replace(chr(13), "")


def last(name, pattern):
    hits = [line.strip() for line in read(name).splitlines() if re.search(pattern, line)]
    assert hits, f"{name}: no line matches {pattern}"
    return hits[-1]


def git(*args):
    run = subprocess.run(["git", *args], capture_output=True, text=True, encoding="utf-8")
    return run.stdout.strip()


src = SPEC.read_text(encoding="utf-8")
assert "## Build record, R1a" not in src, "the build record is already there"

commits = [line for line in git("log", "--format=%h %s", "a0ab79b..HEAD").splitlines()
           if line.split(" ", 1)[1].startswith("Results tab R1a")]
assert commits, "no 'Results tab R1a' commit since a0ab79b"
new_entries = [line for line in read("r1a_agents_new_task10.txt").splitlines() if line.strip()]
browser = read("r1a_browser_task10.txt")
timing = last("r1a_browser_task10.txt", r"^INFO  /api/results build:")
browser_total = last("r1a_browser_task10.txt", r"browser checks pass$")
browser_fail = [line for line in browser.splitlines() if line.startswith("FAIL")]
claude = read("r1a_claude_task10.txt").strip()

rows = [
    ("`python -m app.test_results`", last("r1a_results_task10.txt", r"^Ran ") + " · "
     + last("r1a_results_task10.txt", r"^(OK|FAILED)")),
    ("`python -m app.test_agents`", last("r1a_agents_task10.txt", r"^Ran ") + " · "
     + last("r1a_agents_task10.txt", r"^(OK|FAILED)")),
    ("`python -m app.test_simulation`", last("r1a_sim_task10.txt", r"^Ran ") + " · "
     + last("r1a_sim_task10.txt", r"^(OK|FAILED)")),
    ("`python -m app.test_replay`", last("r1a_replay_task10.txt", r"checks pass")),
    ('`node --test "static/sim/*.test.mjs"`', " · ".join(
        last("r1a_node_task10.txt", rf"^. {k} ") for k in ("tests", "pass", "fail"))),
    ("`python verify_docs.py`", last("r1a_verify_docs_task10.txt", r"checks pass|FAIL")),
    ("`python drift_test.py`", last("r1a_drift_task10.txt", r"CAUGHT|caught")),
    ("the browser check (scratchpad script)", browser_total),
]
table = ["| check | as printed |", "|---|---|"] + [f"| {a} | {b} |" for a, b in rows]

record = [
    "",
    "---",
    "",
    "## Build record, R1a",
    "",
    f"Built on {datetime.date.today().isoformat()}, branch `{git('rev-parse', '--abbrev-ref', 'HEAD')}`, "
    "by the R1a plan, task by task. Every figure in this record is copied from the run it names; "
    "the outputs themselves stay in the session scratchpad.",
    "",
    "### What was built",
    "",
    "- **The server side, under `--simulation` only.** `app/results_eval.py` parses an `evaluate.py` "
    "result file; `app/results_provenance.py` gives each file its plant state (§5.2), with git and the "
    "fingerprint of this tree; `app/results_data.py` finds the experiments in `results/` (§4.1), builds "
    "one section each with its notes, its quoted verdict and the cross-check against "
    "`analyse_phase_d.parse` (§4.4); `app/results_api.py` serves `GET /results` and `GET /api/results` "
    "behind the Host guard, one build at a time, `no-store`. `app/server.py` mounts them right after "
    "`install(app)`.",
    "- **Two changes the spec did not name, from the plan's review.** Mounting imports "
    "`app.results_provenance`, so the plant hash the tab compares against is taken when the server "
    "starts, which is when the server loaded the plant (§5.2). And `/static` now answers "
    "`Cache-Control: no-cache` in every mode: §7.1 records that it sent none, and R1a changes "
    "`i18n.mjs` and `style.css`, which the pages load without a version query, so a browser could run "
    "its cached copies after the update and show the key `nav.results` in the nav.",
    "- **The page.** `app/static/results.html`, and in `app/static/sim/`: `results.mjs` (the DOM), "
    "`results-view.mjs` (every sentence), `results-charts.mjs` (the pairs chart and the hand-written "
    "comparison), `charts-lib.mjs` (the copy of Ghassan's drawing code), `results-format.mjs`, "
    "`results-strings.mjs` (Arabic and English) and `results.css`.",
    '- **The nav.** «النتائج» / "Results" is the third link of `simulation.html` and `agents.html`. '
    "With five links the lab's top bar ran wider than a phone, so `style.css` now gives its nav a row "
    "of its own there, as `agents.css` does (§7.4); the browser check measures it.",
    "- **Tests.** `app/test_results.py`; `results-format`, `results-strings`, `charts-lib`, "
    "`results-charts`, `results-view` and `results-page` under `app/static/sim/`; the two nav pins "
    "(`app/test_agents.py`, `agents-page.test.mjs`).",
    f'- **Documents.** `app/README.md` (the page table, "Opening the results tab"), '
    f"`app/start-simulation.ps1` (the banner); CLAUDE.md's repository layout: {claude}.",
    "",
    "### Commits",
    "",
] + [f"- `{line.split(' ', 1)[0]}` {line.split(' ', 1)[1]}" for line in reversed(commits)] + [
    "",
    "### The checks, as printed",
    "",
] + table + [
    "",
    "**The agents suite against its baseline.** Before R1a the suite already failed, because the merged "
    "plant refuses Jad's agents; the coordinator captured that list before any R1a change. Entries this "
    "run has and the baseline does not: "
    + ("none." if not new_entries else "; ".join(f"`{e}`" for e in new_entries) + "."),
    "",
    "**The browser check.** " + (
        "Every check passed." if not browser_fail else
        "These failed: " + "; ".join(f"`{line[6:].strip()}`" for line in browser_fail) + ".")
    + " Screenshots at 1440 px and in a 390 px frame, both languages and both themes, of `/results`, "
    "`/simulation` and `/agents`, are in the scratchpad, not in the repository.",
    "",
    "### The build time of `/api/results`",
    "",
    f"`{timing}` (the build's own `elapsed_ms`, and the wall clock seen by the client, on the first "
    "request after the server started and on the next).",
    "",
    "### Left for R1b and R2",
    "",
    "- **R1b, Ghassan's set:** `analyse_agent_set.py`, its committed capture and the `posthoc:` anchors; "
    "the agent-set reader and port; the pairs chart both ways; `f-eval`, `f-abl`, `f-trade`, `f-curves`; "
    "the two new figures; the incomplete box; the two provenance lines; the record fold.",
    "- **R2, the simulator and the car:** every figure of §3.3 and §3.4, their readers, strings and "
    "tests, and the defect fixes that belong to them.",
    "- **Not in R1a, by its contract:** stepping a crosshair or nearest-point chart with the arrow keys "
    "(§7.3); R1a's figures are per-mark charts, whose marks take keyboard focus.",
    "",
]
SPEC.write_text(src.rstrip(NL) + NL + NL.join(record), encoding="utf-8", newline=NL)
print(f"{SPEC.as_posix()}: build record appended ({len(commits)} commits, {len(rows)} checks)")
```

Run it from the repository root, read what it wrote, and check the guard still passes with the record in the design (it is a tracked `.md` that `verify_docs.py` scans):

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
$PY "$SP/r1a_build_record.py" "$SP"
sed -n '/^## Build record, R1a/,$p' docs/superpowers/specs/2026-09-30-results-tab-design.md
$PY verify_docs.py > "$SP/r1a_verify_docs_task10_record.txt" 2>&1; tail -1 "$SP/r1a_verify_docs_task10_record.txt"
```

Expected: `docs/superpowers/specs/2026-09-30-results-tab-design.md: build record appended (<N> commits, 8 checks)`, where N is the number of commits since `a0ab79b` whose subject starts `Results tab R1a` (ten when every task committed once and this record is not yet committed); then the record itself, ending with the "Left for R1b and R2" list; then `All 73 checks pass (...)`. Observed in drafting on a scratchpad clone where Tasks 1 to 8 were one commit: `build record appended (3 commits, 8 checks)`, the record as specified, and `All 73 checks pass (849 figure mentions scanned in the documents).` with the record in the design. The script refuses to run twice (`AssertionError: the build record is already there`) and refuses a missing capture, naming the step that writes it. Read the record once: every line in its table must be a line some command above printed.

- [ ] **Step 9: Commit the build record, by explicit path**

```bash
cd "/c/Users/admin/Documents/graduation project/GRAD-project"
PY="/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe"
export PYTHONIOENCODING=utf-8 GIT_OPTIONAL_LOCKS=0 PYTHONDONTWRITEBYTECODE=1
SP="/c/Users/admin/AppData/Local/Temp/claude/c--Users-admin-Documents-graduation-project-GRAD-project/3ceacbd0-c593-4033-801a-fae5729f96d9/scratchpad"
SPEC=docs/superpowers/specs/2026-09-30-results-tab-design.md
{
  printf '%s\n\n' "Results tab R1a (task 10): the build record"
  printf '%s\n' \
    "The design gains its R1a build record: what was built, the commits, every check" \
    "as it printed, the build time of /api/results, the agents suite against its" \
    "baseline, and what is left for R1b and R2. The browser check and its screenshots" \
    "stay in the session scratchpad." \
    ""
  grep -E "browser checks pass$" "$SP/r1a_browser_task10.txt" | tr -d '\r'
  tail -1 "$SP/r1a_verify_docs_task10_record.txt" | tr -d '\r'
  printf '\n%s\n' "Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>"
} > "$SP/r1a_msg_task10_record.txt"
cat "$SP/r1a_msg_task10_record.txt"
git add "$SPEC"
git commit -F "$SP/r1a_msg_task10_record.txt" -- "$SPEC"
git log --oneline -13 | grep "Results tab R1a"
GIT_OPTIONAL_LOCKS=0 git status --short | head -20
```

Expected: the commit holds the design only; `git log` lists the R1a commits, newest first; `git status` shows nothing of R1a's paths (the other session's files may show, and stay as they are).

R1a is then done in the sense of spec 10: Jad opens `/results` in the lab and sees Phase D, D2 and C4, each labelled and quoted, in both languages. Tell him in one short note what now works, and point at the build record.
