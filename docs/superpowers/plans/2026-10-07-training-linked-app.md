# Training-linked app Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: use `executing-plans` to implement this plan task by task. Steps use checkboxes. The user explicitly authorized the Sol/Luna/Astra workflow below on 7 October 2026; apply it when implementation starts without requesting delegation permission again.

**Goal:** Make the existing local app discover new training/evaluation artifacts and update open pages automatically, then improve inspection of the agent's recorded decisions and the mechanical display.

**Architecture:** A bounded read-only artifact registry publishes versioned in-memory snapshots to the existing FastAPI app. Native JavaScript modules poll a cheap revision endpoint and update only the affected views. Saved-record playback and explicit model inference remain distinct capabilities.

**Tech Stack:** Existing Python/FastAPI, standard-library filesystem APIs, NumPy for records, native JavaScript modules, Three.js 0.180.0; SB3/Torch only where actual policy inference requires them. No framework migration or new watcher service.

**Spec:** `docs/superpowers/specs/2026-10-07-training-linked-app-design.md` (proposed design based on the user's 7 October request). Start implementation only when the user starts/authorizes that work. The present deliverable is the plan.

**Graphics addendum:** `docs/superpowers/specs/2026-10-07-training-linked-app-visuals.md`, requested by the user after inspecting the [B58 reference](https://claude.ai/artifact/16mUxgXuHMzLppvT9Df4rM). It defines 25 analytical panels G01–G25 plus decision timelines, their sources and interactions. B1, B2 and C1 must track these IDs explicitly; B3 supplies their connection to the model view.

## Authorized development workflow

| Role | Exact model ID | Reasoning effort | Responsibility |
|---|---|---|---|
| Orchestrator/planner | `gpt-6.1-sol` | `high` | Own the plan, task boundaries, interfaces, integration, review, acceptance tests and user updates |
| Worker sub-agents | `gpt-6-luna` | `high` | Implement bounded tasks, run relevant tests and return evidence plus unresolved issues |
| Escalation only | `gpt-6-astra` | `high` | Resolve one difficult, specifically stated issue escalated by Sol; return a finding/recommendation for Sol to apply |

These are development-agent roles, not the SAC policies or the Jev/Laya models in the product. Saving this plan does not switch the current chat's model. The execution session should be opened on Sol with `high`; explicitly set `model` and `reasoning_effort` on each worker/escalation spawn rather than assuming the parent setting propagates.

**Dispatch and ownership**

1. Sol verifies the baseline and freezes the relevant interfaces before dispatch. Each Luna brief names the task ID, exact read/write paths, input/output contracts, constraints, test commands and acceptance conditions. Use a focused context packet (`fork_turns: "none"` with explicit file references and instructions) when passing a model override.
2. Run at most two Luna workers concurrently, only on independent files. Keep a single named writer for each file. Sol owns shared wiring/integration unless explicitly handed to one worker; no simultaneous edits from Sol or a second worker to that file. No worker silently expands scope or delegates further.
3. A1 establishes the artifact contract before dependent A2/A3 work. After that, A2's Python API and standalone browser-sync helper can run in parallel with disjoint ownership; Sol integrates them into existing pages. A3 changes shared catalog/replay files after those integrations are settled.
4. Each worker returns changed paths, actual commands/outcomes, missing evidence and remaining issues. Sol reads the diff, checks it against the spec, runs appropriate integration/UI checks, and directs a bounded fix when needed. Worker self-report alone is not acceptance.

**Astra escalation rules**

- Do not call Astra for routine coding, translation, CSS work or every end-of-task review. Sol handles ordinary review and integration.
- Escalate a specific unresolved scientific interpretation that affects display truth, a model/record generation mismatch that remains unexplained after targeted investigation, an unresolved architectural conflict, or a reproducible failure that remains after a focused Luna correction and Sol's own diagnosis. A first failing test by itself is not an escalation.
- Send the smallest useful packet: question, expected/observed behaviour, relevant source/diff, reproduction/test evidence, attempted correction and alternatives with trade-offs. Tell Astra to investigate and recommend, not edit unrelated code or start another review tree.
- Sol evaluates the finding, assigns any correction to Luna, integrates it and verifies the result. Escalation does not authorize changing physics, training protocols, scope or publishing results. Report a missing model capability to the user instead of silently substituting another model.

## Global constraints

- Work in `C:\Users\admin\Documents\graduation project\GRAD-project\app`; preserve `Explanatory Simulation/`.
- Keep the scientific plant, training settings, reward, evaluation protocol and existing fingerprint gates unchanged.
- Never launch training or evaluate/export results as a consequence of GET, polling, page startup or file arrival.
- Discovery and display do not write to `results/`, `runs*/`, raw logs or the vehicle. No ECU write path.
- Current metadata and scientific caveats accompany every plotted result. Missing fields stay unavailable.
- Preserve the current bilingual theme keys and measured/estimated/schematic distinctions.
- Use temporary directories for filesystem tests; never overwrite the team's artifacts to demonstrate refresh.
- Do not commit/push, reset/stash, change branches or alter another session's files without the user's authorization. Stage explicit paths if a commit is later requested.
- Full phase roadmap is in the spec. **The first implementation session targets A1–A3 below**, a working vertical slice. B1–B3 follow after that slice is verified; they are not prerequisites for proving file arrival.

## Files and responsibilities

| File | Action | Responsibility |
|---|---|---|
| `app/artifact_catalog.py` | Create | Bounded discovery, server IDs, revisions, immutable snapshot construction |
| `app/artifact_readiness.py` | Create | Stability and lifecycle classification; no model inference |
| `app/artifact_api.py` | Create | Simulation-only artifact snapshot/revision GET endpoints |
| `app/test_artifacts.py` | Create | Isolated filesystem, lifecycle, revision and route tests |
| `app/server.py` | Modify | Mount artifact routes only in `--simulation` |
| `app/agent_catalog.py`, `app/agent_api.py` | Modify | Resolve discovered IDs, preserve legacy addresses, guard source generations and replay cache |
| `app/static/sim/artifact-sync.mjs` | Create | Poll/backoff/visibility lifecycle, stale-response protection |
| `app/static/sim/artifact-sync.test.mjs` | Create | Clock/network/visibility tests with injected dependencies |
| `app/static/sim/artifact-view.mjs`, `artifact-strings.mjs` | Create | Pure display/status labels and bilingual strings |
| `app/static/sim/artifact-view.test.mjs` | Create | Availability/label/parity tests |
| `app/static/agents.html`, `sim/agents.mjs`, `sim/agent-picker.mjs`, `sim/agents.css` | Modify | Run summary strip and new catalog arrivals without resetting playback |
| `app/results_api.py`, `results_data.py`, `static/sim/results.mjs` | Modify | Coherent versioned result refresh, retaining R1a |
| `app/results_sets.py` | Create in B1 | Agent-set reader for existing R1b contract |
| `app/record_reader.py`, `record_api.py`, `test_records.py` | Create in B2 | Bounded saved-record access and schema validation |
| `app/static/sim/record-view.mjs`, `record-view.test.mjs` | Create in B2 | Record step selection and channel presentation |
| `app/static/sim/scene.mjs`, `agent-scene.mjs`, `agent-view.mjs` | Modify in B3 | Data-bound mechanical/road view; preserve scientific geometry |
| `app/static/sim/chart-selection.mjs`, `chart-selection.test.mjs` | Create across B1/B2 | Shared, source-scoped pair/time selection without mixing incompatible axes |
| `app/static/sim/charts-lib.mjs`, `charts-lib.test.mjs` | Extend across B1/C1 | Accessible plot interactions, domains, responsive mounting and disposal |
| `app/results_comparisons.py`, `app/test_results_comparisons.py` | Create in C1 | Read-only R2 simulation/car figure adapters and source fixtures |
| `app/static/sim/comparison-charts.mjs`, `comparison-charts.test.mjs` | Create in C1 | Remaining reference charts using existing drawing primitives |
| `docs/superpowers/verification/2026-10-07-training-linked-app-graphics.md` | Create during implementation | G01–G25 source/implementation/verification coverage |
| `app/start-simulation.ps1`, `app/README.md` | Modify | Reproducible interpreter selection, routes, actual capability/latency documentation |

Paths in this document are repository-relative. Names for new files are proposed interfaces, not claims that those modules already exist.

## A1. Establish the baseline and artifact registry

**Files:** create `artifact_catalog.py`, `artifact_readiness.py`, `test_artifacts.py`; read existing `agent_catalog.py`, `fingerprint.py`, `train.py`, `record_agents.py`, `results_provenance.py`; do not edit those producers.

- [ ] Record `git status --short` and `git log -3 --oneline`. At plan time the branch was `JMF-2340550-results-tab`, with pre-existing modifications to `team/jad.md` and untracked `NEXT_SESSION_2026-10-06_results-tab.md` and `VALIDATION_PLAN_REVIEW.md`. Recheck; do not treat these as your changes.
- [ ] Check the chosen Python interpreter actually imports the lab dependencies; separately report SB3/Torch capability. Do not assume that the system interpreter or `.venv` is the correct one from an old handoff.
- [ ] Run baseline tests listed at the end. Record skips and exact pre-existing failures, especially old-policy/plant mismatch tests. Do not loosen fingerprint checks to make the baseline green.
- [ ] Write tests for direct and one-level nested layouts, one-arm pairs, unknown protocols, results-only clones, invalid JSON, active/stale RUNNING, final ZIP before finished config, and symlink/junction escape rejection.

**Registry contract:**

```python
# app/artifact_catalog.py
# ArtifactCatalog(root: Path, *, clock: Callable[[], float] = time.monotonic,
#                 running_pid: Callable[[str], int | None] = FP.running_pid)
# .scan() -> dict: scans supported paths and publishes stable per-item state.
# .snapshot() -> dict: returns the last published snapshot without disk work.
# .resolve(artifact_id: str) -> Path: returns a discovered, contained path;
#                                 unknown IDs raise KeyError.
# .revisions() -> dict: the current revision values, no expensive rebuild.

snapshot = {
    "schema_version": 1,
    "revision": "opaque-content-revision",
    "training_revision": "opaque-training-revision",
    "results_revision": "opaque-results-revision",
    "plant_revision": "opaque-provenance-revision",
    "items": [],
    "issues": [],
}
# Each item: id, relative_path, kind, revision, lifecycle, compatibility,
#           capabilities, source_files, issues.
# kind: run_pair | evaluation_text | agent_set.
# lifecycle: running | finalizing | finished | interrupted | unknown.
# compatibility: {replay_allowed: bool, reason: str | None}.
# capabilities: model, training_curve, training_record,
#               evaluation_summary, evaluation_record, verdict (booleans).
# source_files: relative paths only; no arbitrary request path resolution.
```

Lifecycle and capability describe different evidence. For a run pair, report individual arms as well as the aggregate state; never call a half-pair ready to compare. For a result-only set, missing local model is normal.

**Concrete initial discovery test:**

```python
import json
import tempfile
import unittest
from pathlib import Path
from app.artifact_catalog import ArtifactCatalog

class DiscoveryTests(unittest.TestCase):
    def test_nested_run_is_discovered_while_training(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            d = root / "runs" / "future_set" / "sighted_seed0"
            d.mkdir(parents=True)
            (d / "config.json").write_text(json.dumps({
                "tag": "sighted_seed0", "seed": 0, "preview": True,
                "status": "running", "steps": 50000,
            }), encoding="utf-8")
            (d / "RUNNING").write_text('{"pid": 123}', encoding="utf-8")
            now = [0.0]
            catalog = ArtifactCatalog(root, clock=lambda: now[0],
                                      running_pid=lambda p: 123)
            catalog.scan()
            now[0] = 2.0
            snap = catalog.scan()
            run = next(x for x in snap["items"]
                       if x["relative_path"] == "runs/future_set")
            self.assertEqual(run["lifecycle"], "running")
            self.assertFalse(run["compatibility"]["replay_allowed"])
```

- [ ] Run `python -m unittest app.test_artifacts -v`; confirm the new behaviour fails before implementation.
- [ ] Implement bounded enumeration and readiness rules from spec §4. Treat filesystem races as an issue on the affected item. Unknown protocol and missing metadata must not abort discovery of other items.
- [ ] Read lightweight metadata before allocating expensive arrays. Reuse the existing ZIP budget inspection only after stability and only for changed models. Do not import `train`, `record_agents`, SAC or Torch in the scanner.
- [ ] Include source/provenance dependencies in revisions, including changed `data/derived_params.json` and model code identity. Separate current disk identity from what the server already loaded.
- [ ] Prove scans leave fixture input hashes unchanged and an unchanged scan neither re-hashes binaries nor advances the content revision. Do not include scan timestamps in content hashes.
- [ ] Repeat targeted tests; record actual timing/file counts for one scan of this repository.

**Done:** a nested future run appears safely, results-only artifacts remain discoverable, partial writers do not produce a false finished state, and unchanged scans are cheap.

## A2. Add automatic refresh without disturbing the selected evidence

**Files:** create `artifact_api.py`, `artifact-sync.mjs`, its tests, artifact view/strings/tests; modify `server.py`, `agents.html`, `agents.mjs`, `agent-picker.mjs`, `agents.css`, `results.mjs`, `results_api.py`/`results_data.py` as needed for snapshot assembly; extend `test_artifacts.py` and existing page tests.

**HTTP contract:**

```text
GET /api/artifacts
  200: complete published registry snapshot (schema_version 1)

GET /api/artifacts/revision
  200: {revision, training_revision, results_revision, plant_revision,
        updating, last_success_at, restart_needed}

Both: simulation mode only; local-host guard; Cache-Control: no-store.
No request contains a filesystem path. No request launches scientific work.
```

One app-owned service scans no more frequently than once every two seconds while subscribers are polling, using monotonic elapsed time and a lock. Coalesce concurrent clients; a slower scan cannot overlap another. Run filesystem/parse work outside the event loop. `last_success_at` is a timestamp for the UI, not part of the revision hash.

`/api/results` retains R1a's existing fields and gains a source revision. A rebuild is tied to a stable results/provenance input revision; unchanged polls do not rebuild it. Check the revision before and after a build. If it moved, keep the previous complete snapshot labelled updating; on initial load show updating and retry. Do not publish a mixed payload. A new checkpoint does not invalidate this snapshot.

**Browser helper interface:**

```javascript
// app/static/sim/artifact-sync.mjs
// createArtifactSync({
//   readRevision, onChange, onStatus,
//   schedule = setTimeout, cancel = clearTimeout,
//   isVisible = () => !document.hidden
// }) -> { start(), stop(), visibilityChanged() }
// readRevision(signal) -> Promise<revision response>
// onChange(previousRevisionResponse | null, nextRevisionResponse) -> Promise<void>
// onStatus({state: 'connected'|'updating'|'offline', lastSuccessAt})
// First success invokes onChange(null, next); later calls only on a change.
```

- [ ] Write Node tests with fake clock/fetch: initial fetch, no-change suppression, two-second polling, no overlap, hidden pause/resume, backoff, stop aborts, late response ignored, exactly one refresh per revision.
- [ ] Implement the helper using one scheduled timeout after each completed request, an AbortController and a generation token. A stopped generation cannot publish updates.
- [ ] Connect the existing result page and agent catalog. Initial bootstrap happens once; background refresh reconciles the current selection rather than applying `bootQuery` again.
- [ ] Add a small bilingual run/update strip to `/agents`: source, lifecycle, record availability, compatibility and last update. Use existing theme tokens; no full visual redesign in this task.
- [ ] Preserve selection, folds, focus and scroll on unchanged-source updates. Defer replacement of an actively open select until selection interaction completes; do not move a row underneath the pointer. On source replacement, show the reason and pause that source.
- [ ] Show newly discovered unsupported result kinds as available artifacts awaiting the relevant reader, not as fully rendered result sections. B1 supplies agent-set rendering.
- [ ] Test arrival, deletion and corrupt-then-complete JSON in a temporary fixture-backed app with the page left open. Assert visible state rather than only a 200 response.

**Done:** an already-open page detects a valid fixture publication within the measured target, does not require reload, and keeps the user's place when an unrelated run arrives.

## A3. Connect new identities to replay and make startup reproducible

**Files:** modify `agent_catalog.py`, `agent_api.py`, `agent-picker.mjs`, relevant agent page modules/tests, `start-simulation.ps1`, `README.md`, `test_results.py` launcher assertion; extend `test_artifacts.py`.

- [ ] Add a resolver from the server-issued run ID to a catalogued flat/nested location. Maintain old `?runs=runs_c4&seed=5&ep=1` links. Unknown IDs or escaping paths are refused before any load.
- [ ] Keep the protocol registry explicit. Register no new protocol by guessing from a folder name. New terrain-trained runs can be listed now; allow replay only when their recorded evaluation protocol, current fingerprint checks and existing episode builder agree.
- [ ] Make the internal episode identity include the two model hashes, relevant metadata/protocol, loaded plant identity and episode definition. Reusing a directory for a new model must yield a different identity.
- [ ] Bind streamed frames, cached traces and Jev/Laya answers to that identity. Preserve the external routes as far as practical, adding an opaque trace generation token where needed. An active build whose source changes is cancelled/invalidated before being published; the old trace cannot be fetched as the new generation.
- [ ] Add regression tests for replacement at the same path, unrelated run updates, changed source during a build, and stale model-panel responses. Verify existing scored-artifact and plant mismatch refusals still happen.
- [ ] Introduce explicit `-Python` selection in `start-simulation.ps1`; choose/check the default from actually available interpreters and print the selected path. Check imports, vendor assets and HTTP port; propagate server exit status. Do not automatically install large training dependencies.
- [ ] Update the two tests that currently pin the launcher's literal last line (`test_agents.py` and `test_results.py`) to test successful capability/argument/exit behaviour. Do not retain an obsolete assertion that forbids explicit interpreter selection.
- [ ] Verify launch from the repository root and via an absolute script path from another working directory. Port 8000 remains separate from explanatory port 8765.
- [ ] Update app documentation and a short session record with the actual test results and remaining B tasks.

**Done:** replacement models cannot inherit stale traces, supported nested identities work through the existing guards, unsupported ones explain their limitation, and the launch command consistently selects the intended interpreter.

## B1. Complete agent-set results coverage using the existing R1b contract

**Files:** create `app/results_sets.py`; modify `results_data.py`, `results-view.mjs`, `results-charts.mjs`, `results-strings.mjs`, `results.css` and tests. Read the old results spec §§3.2, 4.2–4.4, 5.2–5.6, 6.4 and the R1a deferred review notes first.

- [ ] Read the visual addendum and map **G07, G08, G09, G10, G12, G13** to this task. Keep the existing R1a figures and add the reference's distinct views rather than replacing them with one summary chart.
- [ ] Add fixture reader tests for a set with two agents and four hand-written policies, one missing member, stale directories, `NOT A RESULT`, `_TEST`, no recordings, and mismatched index/summary values.
- [ ] Implement `read_agent_set(set_dir: Path) -> dict` using published membership and per-member files. Output the section data required by the existing results view, with an explicit section kind and source revision; no import of the result-producing scripts.
- [ ] Render all specified R1b figures: agent pairs for both damage measures, evaluation/ablation/tradeoff/curves, recorded actuator behaviour and knock-margin comparison, incomplete and record folds, both provenance lines. Keep values from their own set and protocol.
- [ ] Implement linked pair selection between G07/G08/G12 and the policy table; implement G10's five-way actuator selector and G13's per-seed curves. Add exact-value tables and focusable/tappable data points. Reuse `charts-lib.mjs`; do not introduce a second chart framework.
- [ ] Create `chart-selection.mjs` with `createChartSelection({sourceRevision, axisKind})` returning `{get, set, subscribe, reset}`. `set({sourceRevision, axisKind, sampleIndex, pairSeed})` rejects a mismatched revision/axis and publishes an immutable selection; unused fields are null. Test subscriber cleanup, revision reset and cross-experiment rejection before connecting DOM controls.
- [ ] Integrate only an available, validated published post-hoc verdict. If the old R1b analysis script/capture still does not exist, display verdict unavailable and retain that specific analysis deliverable as unfinished; do not declare full R1b complete. Writing a new scientific capture is not a polling side effect.
- [ ] Replace real-tree tests that assume exactly three experiments with fixture assertions plus subset checks for the known historical records. A fourth valid experiment must be a successful discovery, not a failing test.
- [ ] Verify real `terrain_dt1` and `sep19_110kmh` summaries load without local models/NPZ files and label their status correctly. Inspect tooltip, touch and keyboard-accessible tables in both languages/themes.

**Done:** actual published agent sets appear automatically with honest evidence/provenance, and historical results remain separate. Mark full R1b complete only when its analysis and figure requirements are all met.

## B2. Inspect saved decisions without recomputing the experiment

**Files:** create `record_reader.py`, `record_api.py`, `test_records.py`, `record-view.mjs` and tests; modify agent page and translation modules. Keep existing compute replay separate.

- [ ] Implement **G11** and the visual addendum's extra command/applied-action, observation/preview, reward-component and torque/thermal timelines. One selected sample drives all correctly aligned panels. The missing `episode_trace.json` or NPZ file is an unavailable state, not permission to generate a demonstration trace.
**Reader/API contract:**

```text
read_record_meta(path: Path, kind: str, config: dict) -> dict
read_record_window(path: Path, kind: str, episode: int, start: int, count: int) -> dict

GET /api/records/{record_id}/meta
GET /api/records/{record_id}/frames?episode=0&start=0&count=200

record_id resolves through the registry; count is bounded to 1..500.
Response: {source_revision, kind, episode, start, channels, frames, issues}.
Channels carry units and evidence type. Missing channels are absent/null,
not arrays of manufactured zeros. Indexing is documented as zero-based.
```

- [ ] Create small NPZ fixtures with numeric arrays and known actions/units. Test missing files, malformed ZIPs, object arrays (`allow_pickle=False`), unequal shapes, non-finite values and unsupported schemas. Check decompressed-size/member limits before allocating large arrays.
- [ ] Derive training episode boundaries from saved `episode`/`step`; evaluation boundaries from the saved array shape and metadata. Use authoritative stored/configured dt, not a universal 719-step assumption. Where timing/road identity is missing, show it unavailable.
- [ ] Cache at most one decoded recording per active source revision initially; release it on selection/revision change. Serve bounded frame windows. Explain the initial decompression cost rather than claiming NPZ supports free random disk access.
- [ ] Implement step forward/back, seek, pause, and channel-linked highlight from a single selected sample. Training `action` is the issued normalised command; evaluation `applied` is physical applied action when present. Never label one as the other.
- [ ] Connect time-chart clicks and keyboard cursor changes to `chart-selection.mjs`; replay updates that same selection store. Test that channel changes, zoom/reset and language/theme changes preserve sample identity, while a source revision change invalidates it.
- [ ] Compare two lanes only when episode, protocol, weights and timestamps are demonstrably aligned. Training runs can have different episode boundaries; a shared step number is not sufficient alignment.
- [ ] Missing records show useful summaries and the missing filenames. Do not attempt to regenerate historical training actions from `policy.npz` or `final.zip`.
- [ ] Run browser checks with fixtures and with actual records only if they have arrived. Clearly report when only fixture record playback was verified.

**Done:** selecting a recorded step shows exactly its available observations, commands, applied actions and outcomes; no inference or external request occurs during passive playback.

## B3. Upgrade the visual model and validate the full experience

**Files:** `agents.html`, `simulation.html`, `sim/scene.mjs`, `agent-scene.mjs`, `agent-view.mjs`, `agents.css`, `style.css`, bilingual strings and targeted tests; read `Explanatory Simulation/src/Scene.tsx`, `TurboAssembly.tsx`, `VehicleAirflow.tsx` for visual reference only.

- [ ] Capture the current actual screens first. Identify model clipping, hidden controls and the information hierarchy before choosing geometry changes. Keep the existing vanilla-module stack.
- [ ] Implement the decision inspection layout: selected source/time always visible; large scene; compact requested/applied actuator comparison; synchronised plots; secondary details collapsible. On mobile show one lane with a persistent switch plus numeric comparison, avoiding two unreadably narrow 3D views.
- [ ] Apply the visual addendum's chart-panel hierarchy and five-group navigation. Ensure the plot cursor and the displayed 3D sample agree. Lazy-mount secondary graphs and keep their source/availability visible; do not replace the graphs with KPI cards or screenshots of the reference.
- [ ] Make turbo compressor/turbine/shaft, intake/exhaust and cooling paths legible through camera presets and part highlighting. Tie quantitative overlays only to available channels. The shaft transfers rotation; the gas streams remain separate. Label schematic animation at its point of use.
- [ ] Preserve the correct road/profile geometry from the episode. Do not fake a slowing car to dramatise engine load when speed was prescribed. Keep car-log decorative road separate from simulated episode grade.
- [ ] Preserve the numeric sample when language/theme/camera changes. Add reduced-motion behaviour and a readable non-WebGL fallback with the same evidence controls.
- [ ] Verify the matrix below and write `app/README.md` instructions for startup, artifact arrival, missing recordings and supported protocols. Describe actual limitations rather than a blanket “all working”.

**Done:** the user can identify which agent/run/time is shown, see what it observed and commanded, distinguish what was applied, and connect those changes to the visible engine channels on desktop and phone-sized layouts.

## C1. Complete the remaining reference graphics under R2

**Files:** create `app/results_comparisons.py`, `app/test_results_comparisons.py`, `sim/comparison-charts.mjs` and its tests; extend results data/view/strings/CSS and `charts-lib.mjs`; maintain the graphics coverage document. Read the old results spec §§3.3–3.4, 5, 6.4 and the latest validation decisions. This is a distinct milestone after B3, not extra work to squeeze into A1–A3.

**Adapter contract:**

```python
# read_comparison_panels(results_root: Path) -> list[dict]
# Each panel has:
panel = {
    "id": "G05",
    "source_revision": "content-derived-revision",
    "state": "ready",  # ready | updating | unavailable | historical
    "source_files": ["results/sweep_speed_grade.json"],
    "series": [],
    "units": {},
    "notes": [],
    "issues": [],
}
# series is chart-specific, documented and fixture-tested per panel.
# Unknown or absent fields do not receive fabricated values.
```

- [ ] Add the source adapters for **G01–G06 and G14–G25** from the visual inventory, using the existing `make_page` read/transform contracts where scientifically valid. Extract the needed readers into the app; do not execute producers or import a generator that changes process state.
- [ ] For each panel, write a small known-value fixture and assertions for units, count, source identity, missing-data gaps and unavailable states. Test fields drawn from two files against their generation/provenance before joining them. Existing historical figures can remain historical while refreshed sources arrive independently.
- [ ] Implement time-series/zoom plots, the speed–grade heatmap, distribution/scatter plots and validation-band views with the existing chart primitives. Define every series' schema beside its adapter and verify the plotted coordinates against fixture values. Use shared scales only for comparable quantities and preserve extrema during any downsampling.
- [ ] Provide pointer/touch/keyboard values, channel controls where applicable, a zoom reset and a numerical table for each panel. Use one source-scoped time selection only for truly aligned series; do not couple a calibration-drive time axis to an agent evaluation episode.
- [ ] Preserve the source-specific limitations on H/τ, knock sampling, training-road examples, gear inference, operating coverage and historical validation bands. The current validation protocol governs new status claims; the reference's old agreement pills are not new certificates.
- [ ] Populate one coverage row per G01–G25 with actual local source, implementation, runtime state and browser evidence. Verify the complete Arabic/English × dark/light × desktop/mobile matrix using representative plots of every type, plus pointer/tap/focus table access for each panel.

**Done:** all 25 reference panels have an implemented renderer and data reader or an explicit data-dependent unavailable state, with verified fixture behaviour. Report real-data verification separately. The requested analytical variety must be present; a generic placeholder does not satisfy coverage.

## Verification commands and evidence

Resolve the interpreter once, then use it consistently. From the repository root:

```powershell
# Set this to the interpreter actually verified during A1.
$appPython = (Get-Command python -ErrorAction Stop).Source
& $appPython -c "import sys, fastapi, uvicorn, numpy, gymnasium; print(sys.executable)"
& $appPython -m app.test_results
& $appPython -m app.test_agents
& $appPython -m app.test_simulation
& $appPython -m app.test_replay
node --test "app/static/sim/*.test.mjs"
& $appPython verify_docs.py
& $appPython drift_test.py
# After the respective new test modules exist:
& $appPython -m unittest app.test_artifacts -v
& $appPython -m unittest app.test_records -v
& $appPython -m unittest app.test_results_comparisons -v
```

Do not run expensive `--full` or opt-in external-model checks without a reason and the relevant authorization. Record baseline differences honestly. The previous learning app's 169 tests are not this app's test results. Prefer targeted suites while implementing; run the full relevant regression set at a completed milestone.

| Check | Expected evidence |
|---|---|
| 1440×900 and 390×844, Arabic/English, dark/light | Screenshots, usable controls, no horizontal overflow, correct units/RTL |
| Open page then publish a temporary run/result | Arrival observed without reload; measured small-artifact latency |
| Partial JSON/ZIP, live RUNNING, stale marker | Correct pending/interrupted states; other runs remain usable |
| Replace selected model at same path | Old frames/answers never labelled as the new model |
| Delete a published artifact | Explicit disappearance/unavailability, no silently current stale view |
| Unknown protocol / different plant | Discovery succeeds; replay remains refused with its reason |
| Hidden tab / server stop and restart | Pause, offline indication, recovery without duplicate poll loops |
| NPZ absent / WebGL absent | Useful summary/controls and explicit missing capability |
| No changes between polls | No repeated full ZIP/NPZ loads or full result rebuilds |
| Input file hashes before/after | App inspection does not mutate training/results/physics |
| G01–G25 coverage | Each panel mapped to source, renderer, runtime availability and verification evidence |
| Shared cursor / pair / channel / zoom controls | Exact sample identity preserved; incompatible datasets never linked |
| Charts without hover and after repeated refresh | Touch/keyboard/table access works; no accumulated listeners or wholesale idle redraw |

A phone-sized viewport is not a physical-phone connection test: the server binds to localhost. Do not broaden network access just to claim mobile support.

## Session handoff

Record completed task IDs, exact source changes, command outcomes, screenshots, measured refresh latency and unresolved limitations. Keep the next step singular: after A1–A3, start B1, followed by B2, B3 and C1. C1 explicitly covers the remaining reference graphics and R2 under the existing results design and latest validation decisions. Keep the G01–G25 coverage record current.
