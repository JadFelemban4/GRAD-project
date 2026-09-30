# conflict-train -- adjudication of train.py (17 hunks)

Label: conflict-train. File: train.py. Merge clone: `C:/Users/admin/Documents/graduation project/To main`
(branch JMF-2340550-merge, uncommitted, zdiff3). Nothing in MERGE or the main repository was modified.
All code was run in copies under `scratchpad/work/conflict-train/`.

## 0. Verdict in one paragraph

Both feature sets can and should coexist in one train.py; none of the 17 hunks is a genuine
either/or on the merits. Jad's side is the guard layer (meta.json fingerprint, closed
experiments, resume refusals, atomic saves, sized buffer, curve append, no-op that is a
no-op). Ghassan's side is the training-design layer (dt passed explicitly, the terrain road
family, the action recorder, config.json, --device). On the physics of training, Ghassan is
more logical on dt (training at evaluate.py's step removes the discretisation mismatch that
Jad himself measured "sits inside the signal"); on method, Jad's guards are strictly
necessary and Ghassan's code, taken as written, re-opens two defects Jad fixed (AUDIT2 H2-3:
curve overwrite and a no-op that rewrites files). A naive resolution crashes: auto-merged
lines reference names that exist only in one side's hunk (`protocol` line 625, `a.dt` /
`a.fixed_road` lines 422-424, `a.device` line 733, `curve` lines 991-995) and Ghassan's
hunk-16 code uses `cfg`/`cfg_path`, which live in `main()` while that code now sits in Jad's
`_train_and_save()`. A candidate merged train.py was written and run: it reproduces
Ghassan's terrain training and Jad's D2 training bit for bit (largest weight difference 0.0
for both) on the merged physics, and every guard fires as intended.

## 1. What each side did (commits read in full, diffs read with `git show <hash> -- train.py`)

BASE f6b46e9 train.py: 182 lines. Fixed climb only, `--out runs`, no dt passed (env default 0.2),
STEPS_PER_S 3.0, curve.csv overwritten, first-5/last-5 verdict.

JAD (JMF-2340550-sep17, tip 086c519), 623 lines, seven commits touch train.py:
- 6fff693 (18 Sep) timing re-measured: 19.19 steps/s at OMP=1, 18.14 at OMP=6; STEPS_PER_S 3.0 -> 19.2.
- 8bb7342 (21 Sep) AUDIT2 fixes 1-2: meta.json fingerprint (fingerprint.py), refuse resume on plant
  mismatch, refuse fresh start over final.zip, curve.csv appended, no-op returns before save.
- f3da0b9 (21 Sep) replay buffer sized to the run (`buffer_size(a)`), proven non-behavioural
  (prove_buffer.py: largest difference 0.0).
- 8e91276 (22 Sep) Phase D2: `--road random` via random_road.RandomClimb wrapper; `--out` default
  runs/ or runs_d2/; `protocol` into the fingerprint.
- f987049 (23 Sep) the C4 traps: resume at a different --steps refused unless --extend; done_steps read
  from the zip; CLOSED runs/ runs_d2/; --no-resume; RUNNING mark; atomic saves; `_train_and_save` split.
- 5d75707 (24 Sep) runs_c4 CLOSED; case-insensitive closed check.
- 5ef1aa2 (17 Sep) a merge commit listed by `git log -- train.py`; no train.py diff of its own.

GHASSAN (JMF-2340550, tip 74de99a), 415 lines, two commits touch train.py:
- c6e9e03 (27 Sep) dt = 1.0 passed explicitly to cycle and env; TerrainTrainingEnv (new road every
  episode) as default, `--fixed-road` for the locked climb; `--out` default runs/terrain_dt1; curve.csv
  gains a road column; first-5/last-5 verdict removed; STEPS_PER_S 13.7.
- 74de99a (29 Sep) ActionRecorder (every training step into record/rec_*.npz -> train_record.npz),
  config.json (run_config), `--device` default cpu, "TEN SEEDS, NOT FIVE", GPU measurement, train_all.py.

Ghassan's train.py never received any of Jad's guards; Jad's never received dt, terrain, recorder,
config.json or --device.

## 2. Measurements made for this adjudication

All with `/c/Users/admin/AppData/Local/Programs/Python/Python312/python.exe`, OMP_NUM_THREADS=1,
in copies. The machine was at 100 % CPU from other agents' runs (Get-CimInstance: LoadPercentage 100,
about 40 python processes), so NO timing figure below is quotable; only equalities and hashes are.

M1. plant_sha, computed with Jad's own fingerprint._sha_files on each tree:
```
base: plant_sha aade4a59e9647b93
jad:  plant_sha b5a3069f32a83754   (plant 72c519c953597f12, thermal 0f36b0b5e6b94203, engine_env 256931c9e302fc58)
ghassan: plant_sha c236a8db3e201090 (plant 9b3da69a706fbab0, thermal db478d4cb809d71d, engine_env 26366fdea29174c7)
MERGE plant.py (auto-merged, Ghassan's): 9b3da69a706fbab0
MERGE engine_env.py resolved either way (its 2 hunks are docstring-only): 26366fdea29174c7 (= Ghassan)
MERGE thermal.py resolved to Ghassan: db478d4cb809d71d ; to Jad: 9a49682b154df8d0
```
So the merged plant_sha is Ghassan's c236a8db3e201090 under any sensible resolution, and never
b5a3069f32a83754 (the value pinned by PREREGISTRATION_D2/C4 and check_c4_start.py:69). All 48
Phase D / D2 / C4 agents fail the fatal check in the merged tree.

M2. `import random_road` on Ghassan's engine_env: its import-time `_check_phase_d_road()` PASSES
(the make_grade_climb body is identical on both sides). `FP.plant_fingerprint(protocol="phase-d")`
works with either evaluate.py (episodes_sha 05a598a574268b20 on both = PREREGISTRATION.md's pin);
`protocol="d2"` works with Jad's evaluate.py (episodes_sha 1c5d49852290d27c, road_sha
1a29dc46db24f233, unchanged) and FAILS with Ghassan's: `AttributeError: module 'evaluate' has no
attribute 'EPISODES_D2'`.

M3. Determinism and device (engine env, seed 5, 250 steps, 30 s episodes unless noted):
```
Jad train.py, GPU hidden (CUDA_VISIBLE_DEVICES=-1), twice   return -47.91049385 both  (identical)
Jad train.py, SB3 default device (log: "Using cuda device"), twice  -48.14763958705589 both (identical)
minimal SAC script, cuda x10 variants (verbose, checkpoint callback, fingerprint import, auto)  all d4dafa313d13e0c3
minimal SAC script, cpu x2   ab27b516fd05b5d2 both
```
CPU and CUDA give different agents: 600 steps, seed 3, Jad's train.py: plain_cuda vs plain_cpu
largest weight difference 1.952e-01, episode returns diverge in episode 2 (-5.317 vs -4.671).
Test artefact worth knowing: exporting CUDA_VISIBLE_DEVICES="" in Git Bash did NOT hide the GPU and
made CUDA runs non-reproducible (e1 2d6cc0658c6eda9d vs e2 45e235afc24e3391); `=-1` hides it cleanly.

M4. The ActionRecorder does not change what is learned. Jad's train.py vs the same file with
Ghassan's ActionRecorder added to the callback list, 600 steps, seed 3, 60 s episodes:
```
plain_cuda vs rec_cuda   largest weight difference 0.000e+00 (32 tensors, 368,398 values)
plain_cpu  vs rec_cpu    largest weight difference 0.000e+00
```
With Jad's engine_env the recorder's t_block and mdot_fuel columns are all NaN (Jad's step() info has
no such keys); MERGE/engine_env.py:973-974 auto-merges Ghassan's info keys, so the merged tree records them.

M5. A candidate merged train.py (scratchpad/work/conflict-train/m/train_merged.py) on a merged-physics
tree (Ghassan's plant/thermal/engine_env/data + Jad's fingerprint.py, random_road.py, evaluate.py):
```
terrain: merged (--device cpu) vs Ghassan's original train.py   largest weight difference 0.000e+00
random : merged (default dt 0.2, auto=cuda) vs Jad's original    largest weight difference 0.000e+00
buffer 10 000 (merged) vs 1 000 000 (Ghassan's SB3 default): identical weights (no eviction)
curve.csv identical to Ghassan's for terrain (road column: single, single, double); D2 row gains
  "climb 154s 13.88%"
T2 no-op re-run: config.json, final.zip, curve.csv, meta.json sha1 unchanged
T5 --road fixed with no --out: "REFUSING: runs/ is Phase D's, a closed experiment", nothing created
T6 resume with --dt 0.2 / --device cuda / --steps 900: all REFUSED (train_dt, train_device, budget)
T3 --steps 1200 --extend: "3 earlier episodes kept, 3 appended"; meta.json extensions recorded;
   config.json previous_sessions 1; train_record.npz 1200 rows
T7 --fixed-road: runs/locked_dt1, dt 1.0, road "locked", train_road fixed
```
T3 also shows the terrain road stream restarting on a resume: the family sequence single, single,
double repeated exactly after the resume -- Jad's "A RESUME IS NOT A LONGER RUN" applies to terrain.

## 3. Hunk by hunk (merged-file line ranges)

H1 7-53 docstring usage and design sections. BASE three usage lines. JAD (8e91276, f987049): C1/D2/C4
usage, "A NEW BUDGET NEEDS ITS OWN --out", PHASE D2 section ending "The environment itself is untouched,
which is why the sixteen Phase D agents still pass their fingerprint check". GHASSAN (c6e9e03): terrain
usage, `--fixed-road`, "Output goes to runs/terrain_dt1/<tag>/", "WHAT CHANGED ON 27 SEPTEMBER ... Two
things, both before any Phase D training on the locked 130 km/h climb". Relation rewrite-needed; both
valid. Stale in the merged tree: Jad's fingerprint sentence (M1); Ghassan's "before any Phase D training
on the locked 130 km/h climb" (Phase D, D2, C4 trained there 21-24 Sep on sep17). Keep Jad's usage line
"C1: the first bad run": analyse_phase_d.py:157-162, analyse_phase_d2.py:219 and CLAUDE.md:179/214 quote
train.py as calling 50 000 steps that. Resolution: one usage block naming the three designs (terrain dt
1.0 -> runs/terrain_dt1; fixed dt 0.2 -> runs/ CLOSED; random dt 0.2 -> runs_d2/ runs_c4/ CLOSED), Jad's
two sections kept with the fingerprint sentence rewritten to "held on sep17 at plant_sha
b5a3069f32a83754; the merge replaced the physics (c236a8db3e201090), so Phase D, D2 and C4 re-score only
from 086c519", Ghassan's section kept with its first line re-dated to "the 27 September design" and D2
named as the other answer to "the road ahead never changes".

H2 57-70 timing intro. JAD (6fff693) "MEASURED 17 September 2026, 2000 SAC steps ...". GHASSAN (c6e9e03)
"MEASURED 27 September 2026 on the 20-core team machine: 13.7 steps/s ... Ten runs ... 4.5 steps/s each on
19 September, 173 min for the lot -- about five times better". Take both; two machines, devices, plants,
dt. Stale: "about five times": 10 x 4.5 = 45 steps/s against 13.7 is 3.3x; the 5.2x figure belongs to 29
Sep (20 runs, 1 000 000 steps in 234 min = 71.2 steps/s against 13.6).

H3 72-81 timing table. JAD 19.19 / 18.14 steps/s -> 0.72 / 0.77 h. GHASSAN "~1 h alone, ~3 h with ten
sharing; 300,000 ~6 h". Arithmetic checks on both. Take both as a two-row table with machine and device.

H4 83-93. JAD "50,000 ~45 minutes / 300,000 ~4.5 hours" (19.2 steps/s). GHASSAN (c6e9e03+74de99a) "Agree
who takes which seed BEFORE anyone starts ... `python train_all.py` launches every seed". Take both but
drop "Agree who takes which seed" (both launchers run every seed on one machine; Jad already retired the
per-person plan, merged 143-145); name both launchers and require them to pass --road and --dt. Also edit
merged 143-145 "which is how every experiment since has been launched" (false: train_all.py launched the
29 Sep retrain).

H5 95-126. JAD "TWO THINGS THAT SURPRISED US" (+ auto-merged 128-137: gradient updates ~2 %, ~1 ms).
GHASSAN (74de99a) TEN SEEDS / GPU DOES NOT HELP (plant 61.6 ms, update 11.5 ms, 16 %, "the installed torch
is a CPU build anyway") / WHAT IS RECORDED. The two cost claims contradict unless the device is named:
Jad's machine has torch 2.11.0+cu128 on an RTX 5070 and SB3 "auto" prints "Using cuda device"; Ghassan's
laptop has a CPU build. "the installed torch is a CPU build anyway" is false on Jad's machine. Take both,
each with its device; add the CPU-vs-CUDA fact (M3); give the Wilcoxon floor for n = 8 too (2/256); add
meta.json and RUNNING to WHAT IS RECORDED.

H6 221-229 imports. Take both: `fingerprint`, `random_road`, `TerrainTrainingEnv`. M2 shows all three
import cleanly on the merged physics.

H7 244-303 CLOSED, buffer_size, build_env. Rewrite: keep CLOSED and buffer_size (Jad); one build_env with
`road` in {terrain, fixed, random} and an explicit `dt` passed to cycle and env (Ghassan). At dt 0.2 the
fixed/random objects are exactly Jad's (make_grade_climb's default dt is 0.2) -- verified bit-identical
(M5). Stale: Ghassan's "as every run before 27 September did" (D2 and C4 trained on random climbs).

H8 450-495 argparse. Rewrite as the union. The auto-merged code needs every attribute of both sides:
a.dt (422-423), a.fixed_road (424), a.device (733), a.road (499), a.buffer (258), a.extend (614),
a.no_resume (768), a.force_plant_mismatch (663). Either side alone crashes with AttributeError.
Stale: Ghassan's comment "runs/ holds the ten agents trained at 110 km/h ... would silently CONTINUE one"
(on Jad's machine runs/ is Phase D's; with Jad's guards nothing continues silently).

H9 498-505 --out default and protocol. Rewrite. `protocol` must exist (used at 625). Recommended: terrain
-> runs/terrain_dt<dt>; fixed/random at their design dt -> runs/ and runs_d2/ (closed: refuse); any other
(road, dt) -> runs/<locked|random|terrain>_dt<dt>; protocol "d2" for random, else "phase-d".

H10 525-534 prints. Take both (road with its description, the dt/episodes line, the device).

H11 537-571 STEPS_PER_S. Rewrite: `19.2 if device.type == "cuda" else 13.7`, each with its provenance
(17 Sep, Jad's machine, CUDA, dt 0.2; 27 Sep, team laptop, CPU, dt 1.0). Neither is measured on the merged
plant on Jad's machine (UNVERIFIED; this machine was saturated).

H12 577-583 build_env call: `build_env(not a.no_preview, a.seed, a.duration, a.road, a.dt)`.

H13 789-795 SAC constructor: take both -- `buffer_size=buffer_size(a), ..., device=a.device`.

H14 854-883 saves. Take both: Jad's `_save_atomic` for final.zip and checkpoint.zip and the --extend
record; Ghassan's `merged = merge_records(outdir)` after the saves.

H15 894-927 curve.csv. Rewrite: Jad's np.loadtxt cannot read Ghassan's road column (ValueError -> prior
discarded -> the AUDIT2 H2-3 blanking returns); Ghassan's overwrite drops pre-resume episodes (H2-3).
Use the csv module, read 3- or 4-column files, append, write episode,return,length,road (verified T3).

H16 929-985 end-of-run summary. Rewrite. Drop the first-5/last-5 verdict (Ghassan): Jad's own
evaluate.py:54-59 says it "is not evidence of learning. It is the weight draw", and
DOC/SESSION_REPORT_2026-09-18.md:526-528 says the same. Keep Jad's whole-curve `curve` (the plot at
991-1000 needs it). Ghassan's cfg update must receive cfg and cfg_path as parameters of
`_train_and_save` (NameError otherwise). Stale: Ghassan's "On 19 September eleven episodes ranged -506
to +644" -- the run was 18 September (SESSION_REPORT_2026-09-18.md:488-528).

H17 1008-1021 "next:". Rewrite by design: terrain -> train_all.py then record_agents.py <out>; fixed/random
-> run_phase_d.py with the same --steps, --road, --dt, --out.

## 4. Default behaviour of the merged train.py (the orchestrator's question)

Every recorded command line relies on a default: PREREGISTRATION.md section 4/9 (`train.py --seed N`,
`--steps 50000 --seed $s`), PREREGISTRATION_D2.md section 4 (`train.py --road random --seed N`, "900 s at
dt 0.2"), run_phase_d.py:377-384 (passes --road, never --dt or --device), train_all.py:49 (passes none of
--road, --dt, --device), prove_buffer.py:28-29 (passes none). Any single default changes one side's
recorded commands silently. Recommendation:
- `--road`: no default -- refuse with the three designs listed (or, if a default is wanted, `fixed`,
  which lands in the closed runs/ and is refused). Never terrain-by-default: Phase D's preregistered
  `train.py --seed N` would then train the terrain design at dt 1.0 without a word.
- `--dt`: default is the design's own -- 0.2 for fixed and random (as Phase D, D2 and C4 ran), 1.0 for
  terrain (evaluate.py's step). `--fixed-road` stays as `--road fixed --dt 1.0`.
- `--out`: as H9.
- `--device`: default `auto` (the status quo on both machines: cuda on Jad's, cpu on a CPU torch);
  write the resolved device into meta.json and refuse a resume on another device (M3).
- Launchers edited in the merge commit: train_all.py passes `--road terrain --dt 1.0 --device cpu`;
  run_phase_d.py adds `--dt 0.2`; prove_buffer.py passes `--road fixed --dt 0.2`.
- fingerprint: add a hash of data/derived_params.json (values only) as a FATAL field in fingerprint.py
  (the candidate records it as `derived_sha`, 326c0835548975e2 today, and refuses a resume when it moves).

## 5. Semantic problems beyond the hunks

S1 (high, breakage) cross-hunk names: see H8, H9, H16; `cfg`/`cfg_path` (801-802, main) used at 964-970
inside `_train_and_save` -> NameError after final.zip is saved: exit 1, config.json stuck "running".
S2 (high, breakage) config.json is written at 801-806, BEFORE the no-op return at 815-821, and
ActionRecorder(outdir) at 799 creates record/: a re-run of a finished run (train_all.py relaunches every
seed without checking final.zip) overwrites the finished config.json with status "running". Move both
after the no-op check (verified T2).
S3 (high, semantic-conflict) fingerprint.py hashes only plant.py, thermal.py, engine_env.py; in the merged
tree the thermal, boost, spark, enrichment and gearbox constants are read from data/derived_params.json
(derived.py; thermal.py:38-44, plant.py:455-457, engine_env.py:121,202,207,455). A new drive re-derives
them without moving plant_sha, so the resume guard and evaluate.py's refusal pass an agent across a
changed plant -- AUDIT2 C2-1's failure with a certificate attached.
S4 (high, hazard) defaults select experiments (section 4).
S5 (high, method) after the merge, Jad's pending option A/B (longer budget or new seeds of C4's design)
cannot be run "one variable at a time" on the merged tree: the plant changed too (M1). Run it from
086c519 or declare it a new experiment.
S6 (medium, breakage) `--road random` needs evaluate.EPISODES_D2 (fingerprint line 196): if evaluate.py
(add/add conflict) resolves to Ghassan's, every D2-design run dies at merged line 625.
S7 (medium, reproducibility) device: CPU and CUDA train different agents (M3); Jad's experiments ran on
SB3's default (cuda here; 8e91276: "cuda, as all 16 Phase D runs were"), Ghassan's on cpu; neither
meta.json nor the result files record it.
S8 (medium, stale-claim) Jad's fingerprint sentence (H1); all 48 closed agents refused in the merged tree.
S9 (medium, claim-about-other-branch) NEXT_CHAT_PROMPT.md (auto-added from Ghassan): "7 conflicts, 4 in
code ... sep17's engine_env.py has the six-speed gearbox" -- false: Jad's Vehicle.gears = (5.250, 3.360,
2.172, 1.720, 1.316, 1.000, 0.822, 0.640), final_drive 3.150, identical to Ghassan's; the merge has 15
conflicted files, 7 of them code. Its "train.py RESUMES any checkpoint it finds there" is also no longer
true (merged guards refuse a resume without meta.json).
S10 (medium, hazard) `runs/` means Phase D's 16 agents on Jad's machine and the 19 Sep 110 km/h agents on
Ghassan's: CLOSED labels Ghassan's as "Phase D"; `record_agents.py runs --name sep19_110kmh` on Jad's
machine would stamp Phase D's agents with the 110 km/h PROVENANCE.
S11 (low, stale-claim) Jad's docstring (merged 204-205) says --extend "records the extension in meta.json
before the first new step"; the code (858-862) records it only after completion.
S12 (low) recorder episode numbers differ from curve.csv's after a resume (T3: 0-7 vs 0-5); two git_dirty
definitions (run_config excludes untracked, fingerprint includes them); run_config reads
data/derived_params.json relative to the CWD.
S13 (info, method) the 29 Sep retrain changed plant, roads, dt, device, seed count and buffer at once,
without a preregistration, and is scored on the single locked road, which is also 15 % of its training
roads (TERRAIN_WEIGHTS[0] = 0.15). At dt 1.0, 50 000 steps is 55 episodes (11 at dt 0.2; C4's 300 000 at
0.2 is 66): budget labels by steps alone mean different things across dt.
S14 (info) verified: the recorder is non-behavioural (M4); the candidate reproduces both sides (M5).

## 6. Read coverage

Read in full: MERGE/train.py (1025 lines), JAD/train.py (623), GHASSAN/train.py (415), BASE/train.py
(182); ghassan_commits.txt; the messages and train.py diffs of 6fff693, 8bb7342, f3da0b9, 8e91276,
f987049, 5d75707, c6e9e03, 74de99a (5ef1aa2 has no train.py diff); jad/run_phase_d.py, jad/prove_buffer.py,
jad/check_c4_start.py, jad/fingerprint.py, jad/random_road.py, ghassan/train_all.py,
ghassan/record_agents.py, MERGE/NEXT_CHAT_PROMPT.md. Read in part: both engine_env.py (env class, step,
make_grade_climb, terrain section), jad/evaluate.py lines 1-100 plus greps, ghassan/evaluate.py by grep,
jad/AUDIT2.md Part 6 and greps, jad/app/agent_catalog.py discover(), ghassan/derived.py head, the
preregistrations' design and command sections, MERGE/engine_env.py and thermal.py conflict regions.
Not read: jad_commits.txt in full (421 KB) -- the seven train.py commits were read with git show instead.
