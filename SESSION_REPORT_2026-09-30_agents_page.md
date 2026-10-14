# Session report — 30 September 2026, the replay pages on Ghassan's laptop

Branch `GRA-2340394`, cut from `main` at `a7ce729` (the merge). **Nothing here is
committed and nothing is pushed.** It is a draft for Jad to read: the second half
changes a rule of his, the one that refuses an agent with no `meta.json`.

Written for Jad and Ghassan. Ghassan asked for the site to be started, then for
the agent replay page to show his agents.

---

## 1. What was wrong, in the order it was found

| # | symptom | cause | state |
|---|---|---|---|
| 1 | `/simulation` and `/agents` load their frame and nothing else: no drives, no experiments | the page scripts were served as plain text, and a browser will not run a module that is not JavaScript | **fixed** |
| 2 | the pages stay empty after the fix | the browser kept its cached copy of the broken scripts | worked around on this laptop; see 2.2 |
| 3 | `/agents` lists no agent that can run | no certified agent is on this laptop, and the twenty that are here sit where the page does not look | **draft change**, section 3 |
| 4 | — | `plant_sha` changes with the Python version | **found, not fixed**, section 4 |

No `.env` file is involved in any of it. The project loads no data from one.

## 2. The empty pages

### 2.1 The scripts were served as text

`StaticFiles` takes a file's type from Python's `mimetypes`, and on Windows that
reads the registry. This laptop's registry maps `.mjs` to `text/plain`, so every
script of both pages went out as text. Every route answered 200 and both suites
passed; only the browser's console said why.

`app/server.py` now pins `.mjs` to `text/javascript` before the static mount.
`app/test_simulation.py` has a test for it that failed before the fix and passes
after it. It needs no HTTP client, so it runs on any machine.

### 2.2 A browser that met the bug keeps it

A reload asks the server whether the script changed, the server answers "not
modified", and that answer carries no content type — so the browser keeps the
plain-text copy it cached. Measured with a browser profile that had loaded the
broken page: still broken against the fixed server.

On this laptop the script files' timestamps were refreshed (no content change),
which changes what the server answers, and the page is opened at
`http://127.0.0.1:8000`, an address the browser had never cached. **Nothing in the
code prevents this for another machine that met the bug**; a hard reload
(Ctrl+Shift+R) is the cure there.

## 3. The agent replay page and the twenty agents of 29 September

### 3.1 Why it listed nothing

The page shows an agent only if it is in a top-level `runs*/` folder and carries
`meta.json`, the plant fingerprint `train.py` writes before the first step.

| agents | on this laptop | why the page could not show them |
|---|---|---|
| the twenty of `runs/terrain_dt1/` | yes | one folder below where the page looks; `config.json` and no `meta.json` |
| the five pairs of 19 September in `runs/` | yes | no `meta.json`; listed under the name "Phase D", which they are not |
| Jad's 48 (`runs/`, `runs_d2/`, `runs_c4/`) | no | never in git |

The first row is not only about old agents: `train.py`'s default output for the
terrain design is still `runs/terrain_dt1`, so **the agents of the next retrain
would not have been listed either.**

### 3.2 What was measured before anything was written

The decision Jad and Ghassan agreed for these twenty is `conflict.md`:428 — score
them only on the plant they trained on. So the first question was whether `main`
IS that plant.

- The plant's code (`plant.py`, `thermal.py`, `engine_env.py`, docstrings
  stripped, as `fingerprint.py` hashes it) is identical at `cbb8d09` (the commit
  each `config.json` names), at `74de99a` (the commit that added the scores) and
  on this branch.
- `data/derived_params.json` is identical, by value, at `74de99a` and now, and the
  data fingerprint in each `config.json` is the one the live constants were
  derived from.
- **All twenty agents reproduce their committed scores exactly.** Episodes 1 and
  20 of each were re-run through `evaluate.run_episode` on the live plant, and
  every number of every result equals the row committed in
  `results/agents/terrain_dt1/<tag>/eval_summary.json`: 40 episodes of 40, equal
  and not merely close.

What this cannot show: that the tree was clean while the agents trained. Each
`config.json` records `git_dirty: true`. The evidence is that the plant was the
same before training, after it and now, and that the scores made in that session
are reproduced to the digit.

### 3.3 The change

**`reconstruct_meta.py`** (new). Writes `meta_reconstructed.json` beside an agent
that has `config.json` and no `meta.json`, and only after every check of 3.2
holds for that agent. It refuses rather than guesses, and `--check` verifies
without writing. The file holds the live fingerprint, the training fields from
`config.json`, and a `reconstructed` block: a statement that it was not written
at training, when it was written, the sha of the one `final.zip` it re-ran, the
device the scores were reproduced on, and the evidence.

**It is never named `meta.json`, and that is the design.** `evaluate.py` and
`train.py` read `meta.json`; they still refuse these twenty exactly as before.
No scoring path and no resume path changed. `app/test_agents.py` asserts both.

**`app/agent_catalog.py`**, the only reader of the new file:

- an agent with no `meta.json` and a valid `meta_reconstructed.json` is `ready`
  with `certificate: "reconstructed"`; with a genuine `meta.json` it is
  `certificate: "training"`, and a genuine one always wins;
- the certificate covers one `final.zip` by sha — another zip in its place is
  refused — and it moves with the plant like any fingerprint, so after the next
  plant change these agents are refused again;
- a runs name may stand for a set one level down: `runs_terrain_dt1` is
  `runs/terrain_dt1`. A top-level directory of that name wins, and a name is
  still matched against the same pattern before any path is built from it.

**The page** (`agents.mjs`, `agent-picker.mjs`, `agents-strings.mjs`). Three
sentences it says of the closed experiments were false of these agents:

| the page said | true of these twenty | now |
|---|---|---|
| "No result file for this pair" | their scores are committed, under `results/agents/` | the line says the certificate was reconstructed, the day, the scores file and the episodes re-run |
| the blind car "may have memorised it: the same road in every episode" | they trained on a new road every episode | said only where the certificate does not record the terrain design |
| scored on cuda; warn if this episode is not on cuda | trained, scored and reproduced on the CPU | names the device the scores were reproduced on, warns only on another |

The experiment reads "runs/terrain_dt1 (no name recorded)" with the page's own
line for an experiment that has no preregistered verdict: *nothing on this page
is a result.*

### 3.4 What was run

| check | result |
|---|---|
| `python reconstruct_meta.py` | 20 written, 0 refused; 40 of 40 re-run episodes equal the committed scores |
| one episode through the page's own route (seed 0, episode 1) | final damage equals the committed value for both arms, digit for digit |
| `npm test` in `app/` | 153 of 153 (148 before; 5 new) |
| `python -m app.test_agents` | 135 run, 0 failed, **14 skipped** (129 before; 6 new) |
| `python -m app.test_simulation` | 16 of 16 (15 before; 1 new) |
| `python -m app.test_replay` | 49 of 49 |
| `python verify_docs.py` | all checks pass, with the new files visible to it |

### 3.5 What could NOT be run here, and what that leaves unproven

- **The 14 skipped tests need Jad's agents** (`runs_c4/` and the others). They
  exercise the catalog on real certified agents. They were read for anything
  this change would break, and one pin was moved for it (`META_KEYS` gained
  `train_road`), but they have not run against this change on any machine.
- **`agent-catalog.fixture.json` was not regenerated.** Its header says it is
  generated on a machine that holds all four runs directories. The three new
  agent keys were added to it by a script that applies what the catalog now
  returns for each agent already in it. Regenerate it on Jad's machine.
- **A certificate written here is good on Python 3.13 only** — section 4.

## 4. `plant_sha` depends on the Python version

Found while asking why this laptop's fingerprint is not the documented one.
Measured on a clean tree, same files:

| Python | `plant_sha` of `main` |
|---|---|
| 3.13 (this laptop's `.venv`) | `11388331420d8ba4` |
| 3.11 (also on this laptop) | `4f06aa543f54dfcb` |
| as documented for the merged plant | `c236a8db3e201090` |

The third row was not measured here; Jad's result files record Python 3.12. A
second check agrees: `sep17-before-merge` hashes to `b4a481884fba945d` under
Python 3.13, where Jad's agents carry `b5a3069f32a83754`.

The fatal hash is over `ast.dump` of the source, and `ast.dump` prints
differently from one Python version to the next. So **an agent trained on one
laptop is refused on another that runs a different Python, on identical code** —
which is the workflow the fingerprint exists to allow. It belongs with agreed
step 2 (the fingerprint covers `data/derived_params.json`), and it should land
before anyone trains. Nothing was changed in `fingerprint.py`.

## 5. For Jad to decide

1. **Is a reconstructed certificate acceptable at all?** It is confined to the
   replay page, labelled on the page, and written only after the scores are
   reproduced exactly. The alternative is to leave the page empty until the
   retrain.
2. **Two episodes or all twenty?** `reconstruct_meta.py --episodes all --force`
   re-runs every frozen episode. The 40 episodes took 395 s on ten workers, so
   all 400 would take about an hour on this laptop.
3. **The nested set.** Listing `runs/<set>/` as `runs_<set>` is needed for the
   next retrain whatever is decided about the certificates, unless `train.py`'s
   default output moves to a top-level folder.
4. **`runs/` on this laptop reads "Phase D".** It holds Ghassan's five pairs of
   19 September, not Phase D's. They are refused, so nothing is shown under the
   wrong name, but the name is wrong. Not changed.
5. **Section 4**, before any training.

## 6. Left on this laptop, outside git

- `runs/terrain_dt1/<tag>/meta_reconstructed.json`, twenty files (`runs/` is
  gitignored).
- `httpx` installed in `.venv`: the app's own test suite imports FastAPI's test
  client, which needs it, and 31 tests could not start without it.
- `app/node_modules/` and `app/static/vendor/` (Three.js, the lab's own
  first-run step; both gitignored).

`CLAUDE.md`, `handoff.md` and `app/README.md` are NOT updated: the change is a
draft until Jad agrees to it.
