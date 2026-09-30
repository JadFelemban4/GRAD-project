# conflict-evaluate -- evaluate.py (add/add, 1 hunk)

Written 29-30 September 2026. Every claim cites a file:line, a commit, or a
command run in a COPY under `scratchpad/work/conflict-evaluate/`. Nothing in
MERGE (`To main`) or in the main repository was modified; only read-only git.

Paths: BASE / JAD / GHASSAN = `scratchpad/trees/{base,jad,ghassan}`; MERGE =
`C:/Users/admin/Documents/graduation project/To main`. Work = `scratchpad/work/conflict-evaluate`.

## 0. Verdict

Keep JAD's evaluate.py as the skeleton and fold GHASSAN's three additions into
it. Jad's file is what 14 import statements in 11 files, `run_phase_d.py`'s
subprocess call (`--out --protocol --label`) and three preregistered parsers
depend on; Ghassan's additions (the per-step recorder, the knock-free
`damage_thermal`, the header read off the cycle) are what 9 import statements in
4 of his files depend on. They do not contradict each other; they cannot be
taken side by side as git wrote them (two `run_episode`, two `main`).

A proposed merged file is at `work/conflict-evaluate/proposed/evaluate.py`
(571 lines; diff against Jad's in `work/conflict-evaluate/proposed_vs_jad.diff`;
the smoke test ran on the 562-line state, before two dated comment additions).
It was smoke-tested on Ghassan's physics (section 6): both APIs present, recorder
changes nothing, Jad's parser reads its table correctly, a config.json-only agent
is refused.

Three things OUTSIDE evaluate.py must move in the same merge commit:

1. `results/phase_d_seed0_110kmh.txt` (Ghassan, 7f6c7f1) is already in MERGE and
   matches Jad's `results/phase_d_seed*.txt` glob. Measured on a copy of MERGE's
   results/: `analyse_phase_d.py` prints **n = 9, 6 of 9, mean +4.9, sign p 0.2539,
   permutation p 0.4902** instead of the preregistered n = 8, 5 of 8, +4.8,
   p 0.3633 / 0.4922; `analyse_phase_d2.py`'s Phase D column goes to n = 9,
   sd 200.5 (printed as 214.4 today). Move it to `results/void/`.
2. `app/agent_trace.run_lanes` must also return `damage_thermal`; measured, its
   dict otherwise stops equalling `run_episode`'s (`app/test_agents.py`
   ProofTests asserts whole-dict equality) although every shared value agrees.
3. `fingerprint.PLANT_FILES` = plant.py, thermal.py, engine_env.py does not cover
   Ghassan's `derived.py` + `data/derived_params.json`, which those three files
   import. On the merged tree a regenerated derived_params.json changes the plant
   without moving `plant_sha`, so evaluate.py's central promise ("EVERY RESULT
   CARRIES THE PLANT THAT PRODUCED IT") is false until it does.

## 1. What each side did (commits)

Base f6b46e9 has no evaluate.py.

JAD (`git log f6b46e9..origin/JMF-2340550-sep17 -- evaluate.py`):
- a68715f (19 Sep 00:46) creates it: 20 frozen (seed, weights), pinned after
  reset; header printed as the literal "12 % at 130 km/h, 42 C" (a68715f:143).
- 8bb7342 (21 Sep) AUDIT2 fixes 1-2: fingerprint block, `check_model_fingerprint`
  refuses a model whose meta.json disagrees or is missing, `--out`, capture via
  say(), `scenario_line()` from `inspect.signature(make_grade_climb)`, ablation
  sentence made conditional.
- 8e91276 (22 Sep) Phase D2: `EPISODES_D2`, `PROTOCOLS`, `--protocol d2`,
  `run_episode(road=)` via `random_road.climb`.
- f987049 (23 Sep) C4 traps: `--overwrite` refusal, `--label`, the model budget
  line from the zip (analyse_c4.py reads it back).

GHASSAN (`git log f6b46e9..origin/JMF-2340550 -- evaluate.py`):
- 3207727 (19 Sep 19:48) cherry-picks Jad's a68715f and replaces the literal
  header with one read off the cycle (`_c = make_grade_climb(...)`, max v_mps,
  max grade, t_amb). `diff a68715f:evaluate.py 3207727:evaluate.py` = that one
  change only.
- cbb8d09 (29 Sep 09:44) `damage_thermal` (damage_rate without the knock term),
  printed as a "thermal med" column between "worst" and "fuel med".
- 74de99a (29 Sep 20:07) `RECORD_STATE`, `_record_step`, `new_record`,
  `run_episode(record=)`.

So both files descend from a68715f. Regions of the single hunk (MERGE lines
6-689) that are byte-identical on both sides (checked with diff on MERGE):
docstring 41-87 = 453-499; DT/DURATION/EPISODES 99-125 = 506-532;
agent_policy/summarise 206-217 = 599-610. `EPISODES` hashes to 05a598a574268b20
on both (ast literal, `work/conflict-evaluate/ep_sha.py`), the value
verify_docs.py pins. EPISODES_D2 = 1c5d49852290d27c (Jad only).

## 2. Who imports what

JAD's tree (14 statements):
| file:line | names |
|---|---|
| app/agent_api.py:44 | agent_policy |
| app/agent_catalog.py:34 | DT, DURATION |
| app/agent_trace.py:26 | DT, DURATION, EPISODES, EPISODES_D2 |
| app/test_agents.py:47 | EPISODES, EPISODES_D2, agent_policy, run_episode (road= kw, whole-dict equality at :1252-1254, :1303-1305) |
| check_c4_convergence.py:153, :197 | agent_policy, run_episode(road=), EPISODES, EPISODES_D2 |
| check_d2_tracking.py:64 | agent_policy, EPISODES_D2, DT, DURATION |
| check_random_road.py:208 | EPISODES_D2 |
| fingerprint.py:192, :238 | EPISODES, EPISODES_D2, DT, DURATION |
| plot_study_page.py:52 | EPISODES_D2 |
| random_road.py:197, :266 | EPISODES, EPISODES_D2 |
| verify_docs.py:1128 | DT, DURATION, EPISODES (+ FP.episodes_sha() == 05a598a574268b20 at :1226) |
CLI: run_phase_d.py:337 (`evaluate.py --out res --protocol d2|phase-d [--label]`),
full_run.py:98 (expects a REFUSAL of runs_sixspeed_18sep). Result-file readers:
analyse_phase_d.parse (last five fields of each row that starts with a policy
name), imported by analyse_phase_d2.py:66 and analyse_c4.py:67;
plot_agent_pairs.py:129 CUT_ROW ("cuts median damage" lines); analyse_c4.py:83
BUDGET ("model ...: trained N steps of M requested").

GHASSAN's tree (9 statements):
| file:line | names |
|---|---|
| knock_margin.py:66, :88 | EPISODES, new_record, run_episode(record=), reads r["damage_thermal"] (:118, :128) |
| make_page.py:248 | EPISODES |
| record_agents.py:94, :103, :391, :541 | agent_policy, EPISODES, new_record, run_episode(record=), damage_thermal (:159, :161, :445) |
| run_results.py:101, :151 | agent_policy, run_episode(use_preview=), EPISODES, damage_thermal (:172, :183) |
CLI: train.py:385 prints `python evaluate.py {outdir}`; handoff.md:163 step 4
`python evaluate.py runs/terrain_dt1/sighted_seed0 runs/terrain_dt1/blind_seed0`.

Collisions:
- `run_episode`: same positional signature; Jad adds `road=None`, Ghassan
  `record=None` (every caller passes them by keyword -- grep above), Ghassan's
  returns one extra key `damage_thermal`. Unifiable; the key breaks Jad's mirror
  test unless run_lanes follows (section 6).
- `main`: different CLI and different OUTPUT FORMAT (5 vs 6 numeric columns,
  conditional vs unconditional "This is the project's result."). Not unifiable
  as is; choose Jad's and add Ghassan's column as a separate block.
- Same name, same meaning, identical text: EPISODES, DT, DURATION,
  agent_policy, summarise.
- Jad only: EPISODES_D2, PROTOCOLS, scenario_line, check_model_fingerprint.
  Ghassan only: RECORD_STATE, _record_step, new_record.
- Local name trap: Jad's main binds `a = ap.parse_args()` and names the agent
  median `am`; Ghassan's main names it `a`. Copying Ghassan's ablation block into
  Jad's main makes the closing `if a.out:` raise AttributeError AFTER the full
  evaluation (~76 min on Jad's measurement) and the result file is never written.

## 3. Measured on Ghassan's physics (the merged plant)

Why Ghassan's physics stands for the merged plant: code-only hashes with
fingerprint._code_only (`work/conflict-evaluate/codehash.py`):
merged engine_env.py = 26366fdea29174c7 whichever side its two docstring hunks
take = Ghassan's; merged plant.py = Ghassan's (9b3da69a706fbab0); thermal.py's
conflict is code (ua_block_oil 800 vs derived, ua_oil_ram new): "theirs" =
Ghassan's db478d4cb809d71d, "ours" = a hybrid 9a49682b154df8d0 that neither
branch ever ran. Jad's evaluate/random_road/fingerprint copied into a copy of
Ghassan's tree (`work/conflict-evaluate/gphys`):

- `python random_road.py` SELF-TEST PASSES (climb(180,12 %) == make_grade_climb
  at dt 0.2 and 1.0; EPISODES_D2 regenerates; road_sha 1a29dc46db24f233).
- plant_sha c236a8db3e201090 (Jad's agents were trained on b5a3069f32a83754 per
  8e91276's message): every agent in runs/, runs_d2/, runs_c4/ is REFUSED by the
  merged evaluate.py -- correct behaviour, and it also marks every pair
  "incompatible" on Jad's agent page (app/agent_catalog.py:131-135).
- scenario lines: Jad's `scenario: 12 % at 130 km/h, 42 C, 720 s, dt 1.0`;
  Ghassan-style from the cycle `scenario: 12 % at 130 km/h, 42 C` -- identical
  content (make_grade_climb's signature and body are the same on both tips:
  jad engine_env.py:834, ghassan :976, MERGE :1006).
- Phase D rows, episode 0 (hand-written policies ignore the weights, AUDIT2
  H2-13): Jad's run_episode and Ghassan's run_episode give identical numbers:
  baseline 920.1 / 883.0 C / fuel 4573; reactive 625.7 / 860.1 C; current-grade
  520.5 / 853.3 C; thermal-only 859.5 / 565.2 / 453.7 (= Ghassan's
  results/phase_d_130kmh.txt rows). On Jad's plant the baseline row is 959.8 at
  884 C (JAD results/phase_d_seed0.txt).
- D2's twenty frozen roads, neutral policy: ALL TWENTY BIND. Thinnest: 13.988 %
  (ep 1012) +12.2 K and 14.029 % (ep 1008) +13.1 K -- the same two roads as the
  comment names, at +12.5 / +13.3 K there. Baseline median 1093.6, IQR 694.4,
  worst 2316.4, fuel 4732, peak 924 (Jad's d2_seed0.txt:28: 1118.0 / 715.9 /
  2363.8 / 4818 / 924).
- NOTCH MOVED. check_random_road.neutral_episode at the worst-case start 300 s
  (`gphys/probe3.py`): 13.70 % +74.8 K, 13.73 % +75.5 K (Jad's comment: +6.9 K),
  13.76 % +76.2 K. The gear hand-back that made 13.73 % the deepest point on
  Jad's plant now falls between 13.76 % and 13.988 % (the frozen 13.651 % road
  is +73.8 K, the 13.988 % road +12.2 K). The merged plant's deepest point is
  UNMEASURED: re-run `check_random_road.py` section C on the merged tree before
  anything is trained or scored on D2 there.

Logs: `work/conflict-evaluate/gphys/probe1.py`, `probe2.log`, `probe2_out.json`,
`probe3.log`.

## 4. The parser hazard, measured

`work/conflict-evaluate/parsetest`: Jad's analyse_phase_d.parse on a six-column
table (Ghassan's layout) returns
`{'baseline ECU': 0.0, 'current-grade': 0.0, 'agent': 111.1, 'agent (blind)': 43.9}`
-- the IQR column -- for rows whose damage medians are 920.1 / 520.5 / 387.1 /
443.8. On the five-column table with an indented thermal block below it, it
returns the correct 920.1 / 520.5 / 387.1 / 443.8. No error either way.

## 5. The glob hazard, measured (outside evaluate.py, caused by its output names)

`work/conflict-evaluate/globtest`: MERGE's results/phase_d_seed*.txt (9 files,
including phase_d_seed0_110kmh.txt) + Jad's analyse_phase_d.py: seed 0 appears
twice (959.8 row and 462.7 row), n = 9, 6 of 9, +4.9, sign p = 0.2539,
permutation p = 0.4902. analyse_phase_d2.py on the same copy: D2 unchanged
(n = 8, p 0.6367), Phase D n = 9, sd 200.5, below-MEI sign p 0.5000 (5 of 9).
app/agent_catalog.table_rows("phase_d") would overwrite seed 0's +9.8 with the
110 km/h file's +5.7 (dict keyed by seed; by reading, not executed).

## 6. The proposed merged evaluate.py, smoke test

`work/conflict-evaluate/gmerged/smoke.py` (DURATION patched to 185 s and two
episodes in main -- a code-path and format test, not a result):
```
Jad-side names present    : True
Ghassan-side names present: True
run_episode signature     : (policy, seed, weights, use_preview=True, road=None, record=None)
keys                      : ['damage', 'damage_thermal', 'fuel', 'knock', 'peak_turb', 'ret', 'torque_viol']
record changes nothing    : True  steps recorded 184  fields 22
road + record             : True  thermal <= total: True
importer call styles      : ok
analyse_phase_d.parse     : {'baseline ECU': 62.2, 'reactive': 62.2, 'current-grade': 68.5}
equals the printed medians: True
plot_agent_pairs CUT_ROW  : ['reactive', 'current-grade']
no-meta agent             : REFUSED -> fake_terrain_agent has no meta.json.
EXIT 0
```
The cycle check caught a real case on the first attempt: with DURATION 30 s the
climb (t = 180 s) is never reached and the check refused to print "12 %".

`work/conflict-evaluate/gmerged/mirror.py` (Jad's app/agent_trace.py, 25 s):
run_lanes keys are the six, run_episode's the seven; all common values equal;
`[got] == [want]` is False. So ProofTests.test_tracer_equals_run_episode (runs in
both branches of its setUpClass) and test_phase_d_pair_full fail on the merged
tree until run_lanes adds `damage_thermal`.

What the proposal changes relative to Jad's file:
1. docstring: three short sections naming Ghassan's additions (header check,
   damage two ways and why it is not a column, recording).
2. imports: `damage_rate` from engine_env (no `sys`).
3. RECORD_STATE / _record_step / new_record verbatim from 74de99a.
4. `episode_cycle(road=None)`: one definition of the cycle, used by run_episode
   and by the header check.
5. `run_episode(policy, seed, weights, use_preview=True, road=None, record=None)`
   = Ghassan's body on Jad's cycle; returns damage_thermal.
6. `scenario_line`: Jad's, plus Ghassan's reading of the cycle as a refusal
   check (max grade, max v, t_amb must equal the declared defaults); for d2,
   every EPISODES_D2 road must lie inside random_road.RANGES.
7. the dt comment in check_model_fingerprint: "legitimate and permanent"
   -> legitimate for agents before 27 Sep (Ghassan's train.py passes dt 1.0);
   "37.0 -> 30.1 %" -> 37.0 -> 34.0 % (AUDIT2.md:602/:695 give 37.0/34.0/30.1
   at dt 0.2/1.0/2.0; the train/score pair is 0.2/1.0), 94 % of it the knock term
   (AUDIT2.md:695).
8. main: Jad's, unchanged table; after the "cuts median damage" lines an
   indented "WITHOUT THE KNOCK TERM" block (thermal med and thermal cut per
   policy), worded so neither parse() nor CUT_ROW can read it.

Not in the proposal, and needed before Ghassan's agents can be scored by the
CLI (a team decision; fingerprint.py and train.py are other agents' files):
a third protocol, e.g. `"terrain": (EPISODES, "PHASE D EVALUATION (agents trained
on varied roads)", "terrain")`, scored with road=None; fingerprint.plant_fingerprint
(protocol="terrain") returning scenario = {train: terrain spec (TERRAIN_* constants
+ code sha of make_terrain/TerrainTrainingEnv), score: make_grade_climb defaults}
and episodes_sha of EPISODES; train.py writing meta.json for terrain runs;
main's `frozen` label (Jad :374) extended. Without it Jad's fingerprint equates
"trained under protocol X" with "scored under X", which is exactly what
Ghassan's design (train on a distribution, score on the locked climb) breaks.
For the 20 agents already trained (config.json only, 74de99a): retrain on the
merged tree (the team already retrains after every drive), or a one-off
certificate computed from config.json's git_commit (plant_sha at that commit
via git show) and plant_inputs.data_sha1 -- never a meta.json stamped by hand
(Jad's train.py rule, 8bb7342 message).

## 7. Semantic issues (beyond the hunk)

See StructuredOutput `semantic_issues`; the list: glob hazard (critical),
parser hazard (critical if the six-column main is taken), mirror test
(high), fingerprint blind to derived params (high), Ghassan's agents refused by
the CLI / train-vs-score protocol model (high), `a` vs `am` crash (medium),
line-number references into evaluate.py (low; list in section 8), device (low),
Ghassan's run_results.py writes a literal scenario header (low), Ghassan
CLAUDE.md:180 says resolve evaluate.py toward his branch and that sep17 has
the six-speed (false: BASE, JAD and GHASSAN engine_env.py all carry the ZF
gears at :325/:326 and :402/:403), stale figures (section 9).

## 8. Line references into evaluate.py that shift under any merge

app/agent_api.py:50, :64 (evaluate.py:370); app/agent_catalog.py:110
(evaluate.py:369); app/agent_trace.py:3 (evaluate.py:175-202);
app/test_agents.py:386 (:369), :847 (:370); app/static/sim/agents.mjs:876
(:347); docs/superpowers/specs/2026-09-26-agent-replay-design.md:110, :127,
:132, :222, :244, :432, :640, :762; ...-recon.md:28, :43, :140, :158;
docs/superpowers/plans/2026-09-26-agent-replay-m1.md (many, e.g. :77 DT at :98,
EPISODES at :103, EPISODES_D2 at :145); ...-m2.md:735, :743. In the proposal
(571 lines) run_episode starts at 259, agent_policy at 295, `blind = ...` at
476, the SAC.load call at 477.
Recommend symbol references ("evaluate.run_episode", "evaluate.main's SAC.load")
instead of line numbers in code comments; the plan/spec files are dated records
and can stay.

## 9. Figures in the hunk that are not true on the merged plant

Jad side: docstring "baseline damage 572.8 -> 959.8, peak 857 -> 884 C" and
"+7.5" are the 19-21 Sep plant (plant_sha b5a3069f32a83754); merged: 920.1 at
883.0 C, +7.5 not reproducible (six-speed agents refused). Date the sentence.
D2 comment "+12.5 and +13.3 K" -> +12.2 and +13.1 K; "All twenty bind" still
true; "13.73 % at +6.9 K" -> +75.5 K on the merged plant, notch moved to
between 13.76 and 13.988 %, new deepest point unmeasured. dt comment "37.0 -> 30.1 %" misquotes the
train/score pair and is a Jad-plant figure. Docstring "the SHA of the three
physics files": the merged plant is five inputs.
Ghassan side: "<- THE ABLATION. This is the project's result." (retracted by
AUDIT2 C2-1, Jad 8bb7342); "on a branch whose default is 110" is history (both
tips default to 130).

## 10. AUDIT2 Part 6 re-checked

AUDIT2.md:279-280 ("The other branch's derives the scenario header from the
cycle; this branch's still prints a literal. The other branch's version is the
one to keep") was true against a68715f:143. It is stale since Jad's 8bb7342
(21 Sep), which removed the literal via inspect.signature. Today both derive
the header; on the merged tree they print the same sentence. Jad's source is
the one the fingerprint's FATAL scenario field uses (fingerprint.py:240-243) and
it covers D2; Ghassan's reads the object the episodes drive. Keep Jad's and add
Ghassan's as a check -- the proposal does. AUDIT2's other evaluate-related
Part 6 items: results/phase_d_seed0_110kmh.txt "arrives silently" -- still
true, and worse than AUDIT2 said (section 5); "a SECOND file labelled This is
the project's result" -- still true (its footer, and Ghassan's main prints the
sentence unconditionally).

## 11. Read coverage

Read in full: MERGE/evaluate.py (693 lines), JAD/evaluate.py (452), GHASSAN/
evaluate.py (246); BASE has none. Historical versions a68715f, 8bb7342,
8e91276, f987049 (Jad) and 3207727 (Ghassan) extracted; diffs of every commit
touching the file read with full messages (3207727, cbb8d09, 74de99a, a68715f,
8bb7342, 8e91276, f987049, plus 7f6c7f1's message). Importers read at their
evaluate call sites, not cover to cover: app/agent_trace.py (1-60, 150-215),
app/test_agents.py (180-200, 1218-1325), app/agent_catalog.py (100-145,
380-420), check_c4_convergence.py (140-215), fingerprint.py (185-330 and
_code_only/_sha_files), verify_docs.py (1120-1300), analyse_phase_d.py (40-130),
analyse_phase_d2.py (75-100), plot_agent_pairs.py (120-160), run_phase_d.py
(325-350), full_run.py (20-35, 90-110), random_road.py (structure),
check_random_road.py (1-81); Ghassan's run_results.py (1-200), record_agents.py
(1-170), knock_margin.py (1-135), train.py (1-120, 224-400), handoff.md
(140-185), CLAUDE.md (170-190, 355-372, 2000-2025), engine_env make_grade_climb
and damage_rate and the info dict on both sides, AUDIT2.md Part 6 and the
evaluate.py findings. Not read: the other 21 of Jad's 25 python files that
mention "evaluate" only in prose; make_figures.py beyond :858; make_page.py
beyond :248. Not executed: app/test_agents.py itself (the mirror failure was
reproduced directly instead), Ghassan's knock_margin/record_agents (need
gitignored agents), a full-length run of the proposed main (only 185 s).
