# Scientific and application limitations

**Checked 4 October 2026** against `backend.catalog.results()`, the current source tree and the generated result files. These limitations apply to this explainer and to claims made from the available model results.

## What the latest result says

The latest paired sighted/blind retrain is the `terrain_dt1` result set. Across ten seed pairs, the mean difference in damage-cut percentage points (sighted minus blind) is **+1.1693 pp**, with 95% CI **[−4.4391, +6.7777]**, paired t-test **p = 0.648406**, and exact Wilcoxon **p = 0.431641**. The confidence interval spans zero and both tests are nonsignificant, so the result is **INCONCLUSIVE**. It is not evidence that preview has no effect. Source: [`results/agents/terrain_dt1/index.json`](../../results/agents/terrain_dt1/index.json#L4632) (paired result begins at line 4632; values at 4705–4714) and the generated [set README](../../results/agents/terrain_dt1/README.md#L38).

A separate, one-scenario hand-policy comparison in [`results/premise.json`](../../results/premise.json) reports baseline damage 920.071, current-grade damage 520.549 (43.4% cut), and predictive damage 523.477 (43.1% cut). Predictive preview is **0.32 percentage points worse** than current-grade in that comparison. These figures are from a different comparison than the ten-pair trained-agent ablation; do not combine their sample sizes or treat either as the H/τ curve.

The generated set README reports that all twenty trained actors beat the hand-written policies on median damage in this simulated protocol. That margin is highly dependent on the unvalidated knock model. In [`KNOCK_MARGIN.md`](../../results/agents/terrain_dt1/KNOCK_MARGIN.md), a diagnostic caps spark advance on already-trained policies: median cuts fall from 67.9% to 41.6% for sighted actors and from 65.4% to 41.7% for blind actors, below the 43.4% current-grade median. This is an **out-of-distribution lower-bound diagnostic**, not a retraining result or a safe estimate of real-engine protection. Blind seed 6 exceeds baseline damage on five of twenty scored episodes; the README reports a worst proxy-damage score of 2,526.7 versus 920.1 baseline.

## Training and replay provenance

The 20 current actor weight exports (`policy.npz`) and per-policy `eval_summary.json` files are available under `results/agents/terrain_dt1/`. The set was trained for 50,000 steps per actor on newly generated roads and scored on twenty frozen episodes, each 720 seconds at dt=1 s on the locked 12% / 130 km/h / 42 °C evaluation scenario. The locked interactive bridge uses Episode 1 of that evaluation protocol: it pins the road and preference weights rather than changing them with the requested UI seed.

The saved training configs identify commit `cbb8d09`, a dirty training worktree and data fingerprint `c4fdd4babfb3752a`, but no `plant_sha`. The current source fingerprint is `c236a8db3e201090`. Therefore exported actors cannot be proven to match the exact source used for the scores. The actor files are not the scored Stable-Baselines `final.zip` artifacts. `eval_record.npz` and `train_record.npz` are not present in this working tree; the set README says those binary traces are gitignored and retained on the training machine. Live actor runs in this explainer are consequently **UNVERIFIED reenactments**, not exact scored traces. The committed JSON summaries are the available scored record.

The current result index was generated on 29 September, before the 30 September merge, and does not contain the missing source fingerprint. Treat it as the latest available experiment summary, not proof that the exact evaluated code is byte-identical to the current merged tree. The merged `check_premise.py` output and `results/premise.json` are a separate current-source hand-policy check.

## Model and validation limits

- The engine is a simplified single-zone, zero-dimensional cycle model coupled to a three-node thermal network. Simulated torque, EGT, knock integral, charge temperature, turbine temperature and damage are model outputs, not direct vehicle measurements.
- The dataset includes 321.7 minutes across eleven drives and 26 pooled operating points. The often-cited 1.4% load residual is a consistency check between two ECU channels; it does not independently validate the simulated cycle torque. Current [`validation_table.md`](../../validation_table.md#L12) reports 8 of 11 checks inside their bands: 6 of 7 literature checks and 2 of 4 checks against the car. Some literature bands are not well sourced; row 8 oil remains outside the car-derived band.
- The knock model has not been validated against sufficiently sampled knock data on this vehicle. The strongest agent-versus-hand-policy conclusions depend on its predicted knock margin. The 0.85 knock knee and 1123 K turbine / 408 K oil damage knees are model settings, not certified safety limits.
- Turbine-housing temperature has no matching sensor in the vehicle logs. Its thermal capacity and transfer coefficients are assumed, and its temperature is inferred from modeled exhaust flow and temperature. Do not label it measured.
- The block/coolant explicit integration oscillates by about 2 K per step at dt=1 s and is stiff above roughly 1.1 s. The agreed research state says no H/τ sweep output is quotable until the thermal integration is corrected. The current retrain is one scenario near H/τ ≈ 0.64 using an assumed turbine time constant; it does not establish a universal curve. A second plant and corrected preregistered sweep remain outstanding.
- The generated training roads and locked climb are synthetic scenarios. The locked score is not evidence from a road the vehicle logged, and hot-region extrapolation remains uncertain.
- The fixed specific-humidity field (0.012 kg/kg) appears in the actor observation, but the current plant equations do not use it. The throttle value is a model proxy, not a measured TPS channel. A source value being measurable on another vehicle does not make the simulation-frame value measured here.

## Application boundary

The bridge binds to loopback, runs imported project code in memory, and reads source through an allowlist. It does not connect to OBD/CAN, issue ECU commands, alter the vehicle, train agents, or rewrite project results. Logged-drive replay reads local files through the existing replay pipeline; missing channels remain unavailable. The simulation and labs are teaching tools, not calibration advice, diagnosis, component-life prediction or safety certification. Their 3D flow and engine geometry are explanatory visuals.

## Historical and document cautions

Use the current `terrain_dt1` index and `premise.json` for their respective comparisons. Phase D, D2, C4 and pre-merge plant figures are historical experiments with different code, roads, budgets or evaluation sets; they are not substitutes for the current paired result. The 30 September prompt audit records 28 proposed instruction-file patches but states that it changed no files. `CHECKPOINT.md` is a 28 September snapshot and explicitly defers to current scripts and `CLAUDE.md`. `DOCUMENT_STATUS.md` warns that team PDFs still contain retired figures and are not covered by `verify_docs.py`; regenerate or check a PDF before using it as a current source.
