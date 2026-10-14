# Astra review — app after the 9 October implementation

Date: 2026-10-09. Branch: `JMF-2340550-results-tab`; HEAD: `3b6953a`, including the existing uncommitted app changes.

This is a review handoff for Sol. No application implementation was changed in this review. New writes are this report, reproduction/evidence files in `app/verification/`, and ignored review logs under `app/.superpowers/`. All subsequent edits must remain inside `app/`.

## Scope and result

Reviewed the record producer/reader contract, archive bounds, source revisions, results navigation, agent availability, simulation UI, launcher, monitoring/driver/review pages, and the complete app Python/JavaScript suites. This extends beyond the new engine geometry. It is not proof that every possible app defect has been found.

Seven actionable findings remain, numbered F09–F15 to avoid confusing them with the preceding review's F01–F08. The first five have deterministic numeric reproductions in `verification/review-2026-10-09-repro.py` and machine-readable observations in `verification/review-2026-10-09-repro.json`. These are review probes, not regression tests that assert buggy behavior as the desired contract.

## F09 — P1: block and turbine observation channels are swapped

Location: `record_reader.py:306–308`.

The reader labels observation column 5 as turbine temperature and column 7 as block temperature. The producer has the opposite order: `thermal.py:180–181` returns `[t_block, t_oil, t_turb]`; `engine_env.py:795–797` puts these into observation positions 5, 6 and 7. Thus the normalized observation plots and exact-value table attribute block input to the turbine and turbine input to the block. Both training and evaluation use this mapping. This finding concerns the observation channels; the separately recorded physical `t_turb`/`t_block` scalar mapping is correct.

Reproduction: input columns 5/6/7 = 11/22/33 produce `block=33, oil=22, turbine=11` instead of `block=11, oil=22, turbine=33`.

Fix and acceptance: align the app mapping with the documented producer ordering. Test the actual values for all three channels with distinct sentinels, for training and evaluation, and check the rendered names. A test that merely checks channel presence cannot catch this error. Do not change the producer outside `app/`.

## F10 — P1: recorded fuel flow is labelled kg/s instead of g/s

Location: `record_reader.py:352`.

`engine_env.py:691` exposes `mdot_fuel=r.mdot_fuel_gps`. The training recorder (`train.py:149,187–188`) and evaluation recorder (`evaluate.py:_record_step`) save that field without unit conversion. The reader also copies the numeric value without conversion, but advertises `kg/s`. A saved 10 g/s therefore appears as 10 kg/s, a thousandfold error in the stated physical quantity. The existing trip simulation correctly shows g/s; this defect is in the saved-record reader.

Reproduction: numeric `mdot_fuel=10` returns value 10 and unit `kg/s`.

Fix and acceptance: label it `g/s`, or perform and document an explicit conversion consistently. Verify value and unit together through metadata, frame response and visible table/chart. Preserve the normalized/physical actuator distinction.

## F11 — P2: archive replacement during a request can give new values an old revision

Locations: `record_api.py:210–212,228–230`.

`_resolve()` discovers and hashes an archive before the reader loads it. The reader returns the digest of the bytes it actually read, but the route overwrites it with the earlier discovery revision without comparing them. If an atomic replacement occurs in that interval, one frame window contains new data branded as the old archive/source revision. The frontend revision guard then cannot detect the change. The reader's internal stable-read check does not cover this earlier boundary.

Reproduction: invoke the actual installed frame endpoint, inserting an atomic replacement just before the real reader runs. The old archive has reward 1, the new archive reward 99. The response is HTTP-status 200 with reward 99, but `archive_revision` equals the old archive's hash and `source_revision` also matches the old discovery item. The reproducer invokes the endpoint directly; it does not claim to be a network load test.

Fix and acceptance: bind archive and relevant sidecars/config to one validated generation across discovery and decoding; compare the decoder's digest before composing the response. Discard/retry or explicitly reject a changed generation. Cover both metadata and frames, including sidecar changes. Do not overwrite the only evidence of what was actually decoded.

## F12 — P2: missing evaluation timing is silently borrowed from training

Location: `record_reader.py:238–258`.

`_dt()` always adds training config values, then gives the evaluation summary's parsed timestep priority when it exists. If an evaluation archive has no readable/recognized `eval_summary.json` timing, it falls back to `config.dt` or `train_dt`. These describe training, not evaluation. This project has historical training at 0.2 s and evaluation at 1 s; `record_agents.py:479` records the evaluation protocol separately. Discovery allows the archive without its summary, so this is reachable.

Reproduction: an evaluation archive with only training config `dt=0.2` is assigned seconds `[0.0, 0.2]` and no unavailable-timestep issue. There is no evaluation timing evidence in the fixture.

Fix and acceptance: use kind-specific authoritative timing. With no evaluation timing evidence, return `dt=null`, null frame times and a sample axis with an explicit limitation. Do not guess 1 s either. Test absent, malformed and valid evaluation timing next to a different training timestep.

## F13 — P2: valid long constant channels trip the compression-ratio rejection

Location: `record_reader.py:175–176`.

The fixed ratio ceiling of 1000 rejects ordinary NumPy compression of a sufficiently long constant numeric channel, even when every absolute size/shape limit is satisfied. Constant/zero channels are legitimate data, not evidence by themselves of a decompression attack.

Reproduction: a producer-shaped record of 1,000,000 samples, with varied observation/action/reward arrays and one zero-valued float32 reward component, totals 82,000,768 uncompressed bytes. This is below the 512 MiB total limit and the 2,000,000-sample limit. The 4,000,128-byte `r_resp.npy` member compresses at ratio 1006.57, and the whole record is rejected as `archive_compression_ratio_limit`. This is a synthetic boundary example, not a claim that an existing real archive was rejected; real archives are absent here.

Fix and acceptance: admit legitimate high-compression numeric arrays while keeping actual bounded decompression, verified NPY shape/size, member/aggregate limits, EOF/CRC validation, and `allow_pickle=False`. Test a large constant channel alongside malformed-size and oversized archive rejection. Do not solve this by removing the absolute safety bounds.

## F14 — P2: the complete acceptance suite is red, including asset-check regressions

Locations: `test_agents.py:3629–3632,3659,3827`; `test_simulation.py:254`; other stale catalog assertions in `test_agents.py`.

Fresh full Python discovery ran **363 tests: 19 failures, 1 error, 5 skipped**. These are unittest failure entries (including subtests), not a count of distinct product bugs. All 300 JavaScript tests passed.

Two asset checks interpret versioned module URLs such as `sim/main.mjs?v=20261009` and `sim/agents.mjs?v=20261009` as literal disk filenames. These checks now fail even though the browser loads the modules. The old JS catalog fixture also no longer matches the server shape. Other failures still assume historical models are compatible with the current plant, infer legacy protocols that the new catalog deliberately leaves unknown, or compare outdated problem lists. Two fixtures assert their temporary roots are outside the repo; this review deliberately locates temporary writes under `app/` to respect the user's boundary, exposing those assumptions.

Fix and acceptance: parse the path component of asset URLs before checking files, update catalog contract fixtures, and replace machine-dependent historical compatibility expectations with controlled app-local fixtures. Keep explicit refusal tests for mismatched plant fingerprints. Do not weaken compatibility checks or simply remove failing tests. Make temp-root isolation explicit without requiring writes outside `app/`. Run complete discovery after repairs and account for each remaining skip/failure; a selected green subset does not close acceptance.

Evidence logs:

- `.superpowers/training-linked-app/full-review-2026-10-09-tests.log`
- `.superpowers/training-linked-app/full-review-2026-10-09-node.log`

## F15 — P2: the launcher exposes monitoring pages that cannot connect in this mode

Locations: `server.py:330–350`, shared navigation in `static/simulation.html`, `static/agents.html`, `static/results.html`; connection status handling in `static/index.html:262–265` and `static/driver.html:160–167`.

The app launched by `start.cmd` is in `--simulation` mode. Its navigation still sends users to the live monitoring dashboard. On this installed runtime, neither `websockets` nor `wsproto` is available. The dashboard stays at `connecting…`, driver mode at `reconnecting…`, and the server repeatedly logs unsupported WebSocket upgrade / no supported library. Even adding a WebSocket library would not create a live reader: simulation mode intentionally does not start one. The UI therefore presents an unavailable operating mode as a connection problem the user could wait out.

Fix and acceptance: expose runtime/mode capability to these pages and display a clear inactive-in-simulation state with a return link. Avoid endless reconnect attempts when monitoring was not started. If a separate live/replay mode is supported, check/report its WebSocket dependency in that mode's setup. Do not start a vehicle connection, install packages, or invent live data merely to make the page appear connected. Test simulation-inactive, missing-dependency, and configured-reader states separately with fixtures.

Browser evidence: `verification/review-2026-10-09-monitor.jpg`. Runtime module probe: `websockets=False`, `wsproto=False`. These observations identify a current mode/setup UX gap, not a failure of the functioning trip/results pages.

## What was rechecked and what remains unproven

- The existing `/simulation` session renders the selected recorded trip, engine view, selected sample, uncertainty, and fuel flow in g/s without a captured console error.
- `/results` keeps independent experiments. In the real browser, D2 → training → evaluation successfully restores the legacy evaluation section, without horizontal overflow or captured console errors. F01 from the preceding review was not reproduced.
- `/agents` correctly reports **0 available / 86 expected** saved records and refuses the historical plant mismatch. No compatible policy inference was run. Absence of the records does not excuse the reader contract defects demonstrated by fixtures.
- `/review` correctly displays its empty event state. Monitoring and review pages still use the older English interface; unifying their navigation/language is a lower-priority usability follow-up, separate from F15's broken connection status.
- Fresh testing covered the full app discovery suite and all current JavaScript test files. The previous eight-case visual matrices remain previous evidence; this turn did not repeat the complete language/theme/viewport matrix.
- No training, evaluation job, hardware connection, external AI request, dependency installation, commit or push was started. The original localhost server and user simulation tab were left in place. The temporary review tab was closed.

## Execution order for Sol

1. Correct the producer/reader scientific contract (F09, F10, F12), using value-level fixtures grounded in producer definitions.
2. Close the generation race (F11), retaining automatic refresh and source-specific invalidation.
3. Correct the constant-channel boundary (F13) without reducing the bounded-reader protections.
4. Make monitoring availability explicit (F15), keeping live operation an intentional separate action.
5. Repair the full acceptance suite (F14), rerun it, and verify actual UI flows. Update the app-local implementation report with fresh results and the continuing missing-record limitation.

Reproduce the five numeric findings from the repository root with:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
.\.venv\Scripts\python.exe -B app/verification/review-2026-10-09-repro.py
```

The probe writes only app-local temporary fixtures and its evidence JSON. Implement fixes in `app/`; read the producer files as the contract, without editing them.
