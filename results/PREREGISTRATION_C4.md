# PREREGISTRATION — C4, the preview ablation at the C4 training budget

**Written 23 September 2026, BEFORE any of the sixteen C4 agents was trained.**
Committed before seed 0 of either arm started. That ordering is the point of
this file, exactly as it was for `PREREGISTRATION.md` and
`PREREGISTRATION_D2.md`: a hypothesis declared after the numbers are in is a
description. One identity probe — sighted seed 0, stopped at 10 000 steps,
never evaluated on any episode set — ran before the commit; section 3a says what
it was and why it carries no result.

> **Status: complete at commit. No line above section 6a is open.** The
> minimum effect of interest is inherited from D2 (set before D2 ran), and the
> convergence rule — the new decision, with the pair condition added to it after
> calibration — was set by the team on 23 September, before this file was
> committed (section 5b). The draft was
> reviewed adversarially before commit (section 12); every finding the review
> confirmed is answered in the text or in the code this file pins.

---

## 1. The question

The same question as Phase D and Phase D2, with agents trained six times longer:

**Does an agent that can see the road ahead protect the turbine better than an
identically trained agent that cannot?**

This file preregisters the PREVIEW question only. Whether learned supervision
beats the `current-grade` comparator is a different claim, and a yes to it is
not evidence for preview (`AUDIT.md` C3).

## 2. Why a third experiment, and why only one thing changes

Phase D2 removed the design flaw that let Phase D's blind arm memorise the road
(explanation iv), and the arms still did not separate — INCONCLUSIVE, 4 of 8
seeds, sign p = 0.6367 (`PREREGISTRATION_D2.md` section 11). Two explanations
remain standing:

| | explanation | does C4 address it? |
|---|---|---|
| (i) | preview genuinely buys little at this configuration | tested jointly with (ii) — see 2a |
| (ii) | **the agents are undertrained** — C1, 50 000 steps, 11 training episodes | **yes — this is the one thing C4 changes** |
| (iii) | the preview carries little: one grade step per episode | a special case of (i) at this configuration. C4 inherits D2's road unchanged, so any (i) finding reads "with one grade step per episode" |
| (iv) | the blinded arm is not blind | already removed by D2, and kept removed |

**C4 changes the training budget and nothing else:** 50 000 → **300 000 steps**,
about **11 → 66 training climbs** per agent (900 s episodes at dt 0.2, 4500
steps each). Same plant, same road distribution, same seeds, same preference
draws, same network and learning rate, same test set, same statistic.

**One variable at a time — the team's rule, Jad, 23 September 2026:**

> «ولا كذا ما نعرف مين السبب، فنسويهم واحد واحد عشان نقدر نحدد»
> — otherwise we cannot tell which one was the cause, so we do them one at a
> time, so that we can tell.

C4 first. **More seeds is a SEPARATE, later experiment**, with its own
preregistration, and only if C4 leaves the question open. Never both at once:
if C4 changed the budget AND the seed count, a change in the result could not
be attributed to either.

### 2a. What each outcome will mean — declared now, printed verbatim by `analyse_c4.py`

The result is one of D2's three cells (section 5), read together with the
convergence verdict (section 5b). All six combinations are interpreted here,
before any C4 agent exists:

| cell | agents converged (5b) | reading |
|---|---|---|
| **PREVIEW HELPS** | yes | Preview helps at 300 000 steps, with agents that had settled. At 50 000 steps (Phase D2, same seeds and roads) the test was INCONCLUSIVE at power 0.24 against the MEI — not a shown absence. So the contrast is CONSISTENT with (ii), the budget, and is attributed to it only if the paired budget-change test (section 5c) rejects. Whether preview is WORTH acquiring is the effect size against the MEI. |
| **PREVIEW HELPS** | no | Preview helps at 300 000 steps; report it as "at 300 000 steps". Consistent with (ii), and attributed to it only if the paired budget-change test rejects (section 5c). The agents were still changing, so the size of the effect at convergence is not known. |
| **SMALLER THAN THE MEI** | yes | With agents that had settled, preview's effect is shown to be below the team's threshold. A positive finding for (i) at this configuration: preview buys little here. (ii) is not supported up to 300 000 steps (limit 2). |
| **SMALLER THAN THE MEI** | no | Preview's effect is below the MEI at 300 000 steps: (i) is supported AT THIS BUDGET. The agents were still changing, so (ii) is not ruled out. |
| **INCONCLUSIVE** | yes | The arms do not separate, and the agents had settled, so undertraining is no longer needed to explain the null at this budget. But eight seeds rule out only effects about as large as the one printed below (80 % power at C4's own spread); for effects near the MEI this outcome is about as likely with (ii) true as false. The next experiment is more seeds, planned from C4's spread, with its own preregistration. Still NOT "preview does not help". |
| **INCONCLUSIVE** | no | Nothing is resolved. The arms do not separate and the agents were still changing: (i) and (ii) both stand. The next experiment — a longer budget or more seeds, one variable at a time relative to C4 — is the team's decision. |

**What is printed beside the reading, and changes what it may say** — all
decided now:

- **Preview costs damage.** If the one-sided sign test for the OTHER direction
  (sighted takes more damage) has p < 0.05, the classification's reading is
  replaced by: *"PREVIEW COSTS DAMAGE at 300 000 steps: the sighted agents took
  significantly more damage than their blind twins. That is a finding about this
  learner at this budget, reported as preview costing damage, never as a
  two-sided win — and it is NOT evidence for (i)."* (D2's rule, restored:
  `classify()` would otherwise file such a result under SMALLER THAN THE MEI and
  call it evidence for (i).)
- **INCONCLUSIVE:** the effect with 80 % power at eight seeds, from C4's own
  spread (`power_analysis.delta_for_power`), so the strength of "rules out" is
  measured, not asserted.
- **PREVIEW HELPS:** the section 5c test's verdict, which decides whether the
  budget is named as the reason; the torque qualifier of limit 10 (if a sighted
  agent refuses torque, or a positive seed's sighted agent tracks more than one
  point worse than its blind twin, the reading adds *"damage partly bought with
  torque — not established as protection"*, and if the torque check has not been
  run the reading is marked PROVISIONAL); and whether `check_c4_start.py`
  confirmed the identity with D2 (section 3a).
- **Convergence not judged.** If no verdict can be used — no file, a checkpoint
  missing, an agent that is not a fresh C4 run, or a verdict computed on
  different `final.zip` files from the ones scored — both readings of the cell
  are printed, marked CONDITIONAL, and the reason is recorded in 6a. No
  checkpoint is regenerated to obtain a verdict.

In no cell may the result be written as "preview does not help". The sentences
available are the ones in this section.

## 3. The plant, pinned — identical to Phase D2 in every fatal field

Every run carries a `meta.json` fingerprint and `evaluate.py` refuses a model
whose plant differs. **C4's fingerprint equals D2's in every FATAL field** —
`plant_sha`, gears, final drive, `dtheta_deg`, `turb_protect_k`,
`oil_protect_k`, scenario (with `road_sha`) and `episodes_sha` — so C4 agents
are scored under D2's protocol with no override. Advisory fields differ:
`steps_requested` (300 000), `git_head`, `resume_allowed` (false), and
`plant_text_sha`, which moved with the comments-only sweep of `thermal.py` in
`3f4627d` and does not enter `plant_sha`.

| field | value |
|---|---|
| gearbox | ZF 8HP51, ratios 5.250 3.360 2.172 1.720 1.316 1.000 0.822 0.640 |
| final drive | 3.150 |
| crank-angle step | `plant.DTHETA_DEG` = 0.25° |
| protection trigger | `TURB_PROTECT_K` = 1123 K (850 °C) |
| `plant_sha` | **`b5a3069f32a83754`** — as Phase D and D2 |
| scenario | climb start uniform on [120, 300] s, grade uniform on [12, 16] %, drawn per episode; 130 km/h, 42 °C |
| `road_sha` | **`1a29dc46db24f233`** — `random_road.py`, as D2 |
| training episode | 900 s at dt 0.2, a fresh road every episode, seeded from `--seed` |
| evaluation | 720 s at dt 1.0, the twenty frozen episodes `evaluate.EPISODES_D2`, hash **`1c5d49852290d27c`** |
| libraries | Python 3.12.10, stable-baselines3 2.9.0, torch 2.11.0+cu128, numpy 2.5.3, gymnasium 1.3.0 — the versions D2's zips record in their own `system_info.txt` |
| code | commit **`a1af19a`** — the trap fixes and `analyse_c4.py`, `check_c4_convergence.py`, `check_c4_start.py` (`f987049`), then the calibrated rule with its pair condition (`a1af19a`). This file is committed next, touching no code; the launch is from that commit, or a descendant that changes only documents, on a clean tree |

`analyse_c4.py` refuses any result file whose fingerprint block does not carry
the three hashes, dt 1, 720 s and twenty episodes. `check_c4_start.py` checks
that every run's `git_head` descends from the commit that added this file — so
"preregistered before training" is something git shows, not something this
file asserts.

### 3a. What moves, and only this

| | D2 | C4 |
|---|---|---|
| `--steps` | 50 000 | **300 000** |
| replay buffer | 50 000 slots | **300 000 slots** — `train.buffer_size` sizes it to the run, so it never evicts |
| resuming | allowed | **refused** — `--no-resume`, section 6 |
| output | `runs_d2/`, `results/d2_seed<N>.txt` | **`runs_c4/`, `results/c4_seed<N>.txt`** |
| tooling code | as at `8e91276` | the trap fixes in `train.py`, `run_phase_d.py`, `evaluate.py`, `fingerprint.py`, `check_d2_tracking.py` — guards, a `--label` title, a budget provenance line, a `RUNNING` mark, atomic saves. Non-behavioural for learning: the training path is covered by the probe below; `evaluate.py`'s scoring is unchanged (its diff adds a title option, a provenance line and an overwrite guard) |

**The buffer size is non-behavioural, and that was measured, not assumed.** A
buffer changes what is learned only when it evicts, and neither size evicts
within its own run. `prove_buffer.py` showed it on Phase D (32 tensors,
368 398 values, largest difference 0).

**The identity probe.** On 23 September, 13:38–13:47, one C4 run — seed 0,
sighted, `--steps 300000`, on the uncommitted working tree at `9162527`, into a
scratch directory, never evaluated on any episode set — was stopped at its
first checkpoint. **Its weights at 10 000 steps are bit-identical to D2's
`sighted_seed0` at 10 000 steps**: 32 tensors, 368 398 values, largest
difference 0.0, despite the 300 000-slot buffer and the later code. Its zip
(sha `7ebcd9872b56738f`) and `meta.json` are kept with the agent backups,
outside the repository (`GRAD-agent-backups/2026-09-23/c4_probe/`), so the
comparison can be re-run.

That is **consistent with the budget being the only variable**, for one run of
sixteen, to its first checkpoint. `check_c4_start.py` tests all sixteen runs
against their D2 twins at 10 000 to 50 000 steps — 80 checkpoint pairs — and
writes the final count to `results/c4_identity.txt`. Beyond 50 000 steps there
is no twin, and identity rests on the code path being unchanged. If any pair
differs, C4 continues — it is still D2's design at a larger budget — but the
difference is recorded in 6a, the (ii) readings carry the note printed in 2a,
and the two experiments can no longer be read as the same agents at two ages.

## 4. The design

| | |
|---|---|
| arms | **sighted** and **blinded** (`--no-preview`), as D2 |
| seeds | **0 … 7** per arm — sixteen runs, the same seeds as D2 |
| steps | **300 000 per run** |
| pairing | by seed: sighted seed *k* against blinded seed *k* |
| training roads | iid from the two ranges, a new road every episode, stream seeded by `--seed` — the same stream as D2's |
| test set | **`evaluate.EPISODES_D2`, hash `1c5d49852290d27c`. It does not change.** |
| agents | `runs_c4/` (gitignored, like `runs/` and `runs_d2/`) |
| results | `results/c4_seed<N>.txt`, titled "C4 EVALUATION", each carrying the steps its two agents were trained for, read out of the zips |

## 5. The statistic — D2's, unchanged

- **Primary outcome:** per-seed median damage over the twenty frozen D2
  episodes.
- **Comparison:** paired by seed, `damage_blind[k] − damage_sighted[k]`;
  positive means preview helped.
- **Test:** exact one-sided sign test, with the exact paired permutation test
  beside it as a sensitivity check. If they disagree, both are reported and
  neither is chosen after the fact.
- **α = 0.05, one-sided.** A significant result in the other direction is
  reported as preview costing damage (the sentence in 2a), never turned into a
  two-sided win.
- **Minimum effect of interest: 50 damage units**, inherited from D2, where the
  team set it before any D2 agent trained.
- **The three cells** — PREVIEW HELPS / SMALLER THAN THE MEI / INCONCLUSIVE —
  with D2's rule, applied by D2's code: `analyse_c4.py` IMPORTS `classify` and
  `MEI` from `analyse_phase_d2.py`, unchanged since the commit D2 pinned
  (`8e91276`), which imports its tests from `analyse_phase_d.py`.
- **The test is on the preregistered set only:** `results/c4_seed0.txt` …
  `c4_seed7.txt`, all eight, each complete. Any other `c4_seed*` file is
  refused; fewer than eight is printed as INTERIM with no reading.

**Before the statistic, every agent is certified.** `analyse_c4.py` refuses to
test unless each result file names exactly its two agents with the line
`evaluate.py` reads out of the zip itself — *trained 300000 steps of 300000
requested, from step 0, buffer 300000* — those two lines name the directories
of the file's two damage rows, the file carries no forced-mismatch stamp, and
any zip still on the machine is readable and has the scored hash. A D2 agent
resumed to 300 000 steps would read "from step 50000, buffer 50000" and is
refused.

### 5a. Power — declared before the run, from D2's spread

`python power_analysis.py`, the D2 section:

| | |
|---|---|
| D2 paired differences | sd **98.8** (Phase D: 214.4) |
| the sign test at 8 seeds | needs **7 of 8** to agree |
| power against the MEI (50) at 8 seeds, at D2's spread | **0.24** |
| effect with 80 % power at 8 seeds | **~124 damage units** — 11.1 points of the D2 episodes' baseline (1118.0); the script prints 12.9 points, against Phase D's baseline (959.8) |
| seeds per arm for 80 % power against 50 | **~42** |

At D2's spread the expected cell is still **INCONCLUSIVE**, unless the effect is
large or the spread changes a great deal.

**This file makes NO prediction about the spread.** D2's preregistration
predicted the spread would not shrink and it halved. Longer training might
shrink it (different seeds converging to the same place) or might not (to
different places). `analyse_c4.py` prints C4's spread beside D2's and
Phase D's, and that is where the question is answered.

### 5b. Convergence — the rule, set by the team (Jad) on 23 September 2026

The question a C4 null would face first is "were THESE agents still
undertrained?" — and an answer invented after the result would be worth
nothing. So it is answered by a rule fixed now, implemented in
`check_c4_convergence.py`, committed in `a1af19a`, the commit before this
file:

- **What is measured.** Every agent is scored at three points in the last third
  of its training — the checkpoints at **200 000** and **250 000** steps and the
  final model at **300 000** — on the SAME ten **practice episodes**:
  deterministic policy, fixed weights, fixed roads. With the ruler fixed, a
  change between checkpoints is a change in the agent.
- **Settled:** the agent's median damage over the practice set moves by **no
  more than 25 units** (half the MEI) across the three points.
- **Pair settled:** the seed's paired difference — blind minus sighted median
  damage on the practice set — moves by **no more than 25 units** across the
  same three points.
- **Converged:** at least **6 of the 8 agents in EACH arm** are settled, **AND
  at least 7 of the 8 seed pairs** are settled.
  - Per arm, because the objection is specific — "the sighted agents had not
    yet learned to use the preview" — and an experiment where one arm settled
    and the other did not is not converged, whatever the total. This condition
    also catches two twins still improving TOGETHER, which leaves their pair
    looking steady.
  - Per pair, because the test is on pairs. Settling judged per agent alone
    lets two settled agents moving 25 units in opposite directions move their
    pair by 50 — the whole MEI — and lets four unsettled agents sit in four
    different seeds. 7 of 8 is the sign test's own one-dissenter tolerance at
    eight seeds.
- **The practice set is not the test set.** Ten episodes drawn once from
  `numpy.default_rng(20260923)`: episode seeds 3000–3009 (no frozen set uses
  them), weights drawn as `reset()` draws them, roads a Latin hypercube over the
  training ranges. `check_c4_convergence.py --selftest` regenerates the literal.
  Judging convergence on `EPISODES_D2` would be looking at the test before the
  test.
- **The rule's noise floor was measured before commit**, on D2's own agents and
  the practice set (`python check_c4_convergence.py --calibrate`,
  `results/c4_convergence_calibration.txt`, 74.7 min):

  | | median | max | beyond 25 |
  |---|---|---|---|
  | ONE gradient step (`final.zip` against `ckpt_50000`), per agent | 1.5 | 7.9 | 0 of 16 |
  | the same, per seed pair | 4.1 | 8.5 | 0 of 8 |
  | 30 000 → 50 000 steps, C1 agents still learning, per agent | 118.2 | 489.8 | 15 of 16 |

  So the 25-unit band is about three times the largest movement that has
  nothing to do with learning — the verdict is not decided by optimiser noise —
  and it does separate an agent that is still learning from one that is not.
  One reading of the last row, stated as a reading and not a result: **by the
  measure C4 uses, D2's C1 agents were still changing fast**, which is what
  explanation (ii) proposes. It is over a shorter span (20 000 steps, earlier in
  training) than C4's rule uses, so it is context for (ii), not a test of it.
- **Why not the learning curve**, which the session plan first suggested: every
  training episode in `curve.csv` is scored under a different preference draw
  and a different road, so its returns scatter widely by construction (eleven
  C1 episodes ranged from −506 to +644, `evaluate.py`'s docstring). A flatness
  test on them passes on noise. The curve's trend is printed beside the verdict
  as supporting evidence only.
- **What the verdict does and cannot do.** It labels the result, choosing the
  row of the table in 2a. It does not select a checkpoint, extend a run, drop
  an agent or touch the test: the agent scored is always the final one. "Not
  converged" is reported, not repaired — more training is a new experiment.
  **It is computed, and committed, BEFORE the test set is scored** (section 9),
  and `analyse_c4.py` uses it only if the per-agent `final.zip` hashes it
  records are the ones the result files certify.

Chosen by Jad on 23 September 2026 from three options — the per-agent rule
(recommended), the learning curve alone, or the per-agent rule with all sixteen
agents required to settle. **The pair condition was added by Jad the same day**,
after the review of the draft found the per-agent rule's allowance at the pair
level and after the calibration above showed a pair's noise floor (max 8.5) is
far inside the band — offered with the alternative of keeping the rule and only
printing the paired movement. Both decisions were made before this file was
committed and before any of the sixteen C4 agents trained.

### 5c. Did the budget change preview's effect? — a secondary test, fixed now

"Significant at 300 000 steps, not significant at 50 000" is not itself a test
of a difference: D2 was INCONCLUSIVE at power 0.24, which is not a shown
absence. The per-seed change IS testable, because the pairing is exact — same
seeds, same roads, same episodes:

- **per seed:** `change[k] = (blind − sighted at C4) − (blind − sighted at D2)`
- **test:** exact one-sided sign test, H1 "the change is positive" (preview's
  effect grew with the budget), the paired permutation test beside it,
  α = 0.05.
- **use:** it decides one sentence only — whether a PREVIEW HELPS result is
  attributed to the budget (2a). It is not a fourth cell, and it is printed
  whatever the cell. At eight seeds it has low power; a non-rejection says the
  attribution is not shown, never that the budget did nothing.

## 6. Everything reported, whatever it says

As `PREREGISTRATION_D2.md` section 6, without exception, plus the crash rule:

- All sixteen runs are reported, including any that fail to learn or to
  settle. A run is **not** dropped for a poor curve.
- **A crashed run is re-run FROM SCRATCH, with the same seed, never resumed.**
  Once its process is gone:
  `python run_phase_d.py --road random --steps 300000 --out runs_c4 --seeds <k>
  --restart-crashed` — naming ONLY the crashed seed. The launcher moves the
  crashed directory to `runs_c4/_crashed/` and trains that seed from step 0,
  and it refuses to move a directory that a live process holds (`train.py`'s
  `RUNNING` mark) or that has changed in the last 30 minutes. A resume is not
  the same agent — its replay buffer restarts empty and its road stream
  restarts from the seed — and every C4 run is started with `--no-resume`, so
  `train.py` itself refuses one. A from-scratch re-run should reproduce the
  uninterrupted agent exactly: training on this machine has been deterministic
  in every check made — two runs in `prove_buffer.py` (2 500 steps), and the
  probe of section 3a (10 000 steps, run essentially alone) against a D2 run
  whose first 10 000 steps shared the machine with up to five others
  (`runs_d2/LAUNCH.txt`). `check_c4_start.py` shows whether a re-run retraced
  its D2 twin; if it did not, it is still that seed's agent and is scored, and
  6a says so. A machine restart during training (a Windows update) counts as
  a crash. A run that dies before its first checkpoint is handled the same way.
- **Every 6a entry is committed before relaunching or evaluating**, and no C4
  run or evaluation uses `--allow-dirty`: the launcher holds its queue while
  the tree is dirty, so a record left uncommitted delays the experiment rather
  than stamping it.
- Median, interquartile range **and worst episode** are reported for every arm;
  `current-grade` is reported beside both.
- **C4 is reported BESIDE Phase D2 and Phase D, never pooled with them.**
  `analyse_c4.py` prints all three, one line each.
- **Limit 10's torque check is run on the C4 agents before the reading:**
  `python check_d2_tracking.py runs_c4 --out results/c4_tracking.txt`.

## 6a. Run log — failures, re-runs, and the identity check

*(Empty at commit. Filled during the run, as section 6 requires; its first
entry is the dry-run of section 9, step 0.)*

**23 September 2026, 16:42 +03:00 — launched from `79568e2`, the commit that
added this file, on a clean tree.** Section 9, step 0, immediately before:

```
python run_phase_d.py --road random --steps 300000 --out runs_c4 --dry-run   EXIT 0
16 runs, 300,000 steps each to launch
  tree     clean at 79568e2
  12 cores, 21.3 GB free  ->  10 at a time
```

- The launcher was started at 16:42:50 as a process of its own (through
  Windows WMI, not as a child of the Claude session), so that closing the
  session or the editor cannot stop the experiment. Its output is
  `runs_c4/launcher_train.log`; its launches are in `runs_c4/LAUNCH.txt`.
- First wave: **10 runs**, seeds 0–4, both arms. Seeds 5–7 queued (6 runs),
  started as first-wave runs finish.
- Every first-wave `meta.json`, read a minute after launch: `steps_requested`
  300 000, `git_dirty` False, `git_head` 79568e2, `resume_allowed` False, a
  live `RUNNING` mark. No 6a entry was written until all ten existed.
- **Peak memory per run: 1519 MB**, measured on all ten — the launcher's
  `PEAK_GB` of 1.5 still holds with a 300 000-slot buffer. 8.1 GB free with
  the ten running.
- Known exposure, stated: Windows Update was not confirmed paused. Its active
  hours end at 03:00, and a restart after that would stop every live run. By
  section 6 that is a crash, re-run from scratch per seed.

**23 September, 17:00 — first identity check: 10 of 10 IDENTICAL.**

```
python check_c4_start.py   EXIT 0
preregistration committed in 79568e2
sighted/blind seed 0-4: meta ok, budget ok, 10k =        (ten rows)
seeds 5-7: not started
IDENTITY compared 10 identical 10
```

Every first-wave run's 10 000-step checkpoint holds the same weights as its
D2 twin's, to the last bit, and every certificate passes, including the git
ancestry check (each run's `git_head` descends from `79568e2`). The pace:
10 000 steps in about 17 minutes per run with ten running, so the first wave
is expected to finish around 01:00–01:30 on 24 September and the second
around 07:00.

## 7. Stopping rule

Sixteen runs, then stop. **No seed is added after any C4 result is seen**, and
no run is extended past 300 000 steps. More seeds, or a longer budget, is a
fourth experiment with its own preregistration — changing one variable relative
to C4, by the team's rule.

## 8. Known limits that apply to whatever comes out

Declared now so none of them can be discovered later as an excuse.

1. **Underpowered, probably — at D2's spread.** Power 0.24 against the MEI at
   eight seeds (section 5a). Whether the C4 budget changes the spread is
   unknown and is not predicted; C4 measures it.
2. **The budget limit, C4's own.** 300 000 steps is about 66 training climbs.
   "Converged" means settled by the rule in 5b — damage on ten practice
   episodes, over the last third of training, for this network, this learning
   rate and this algorithm. It is not a proof that no longer run or different
   learner would do better. And C4 tests ONE budget: a separation says preview
   helps at this budget; that the budget is WHY is tested separately
   (section 5c), and neither says where a threshold lies.
3. **The blind agent is blind to the road AHEAD, not to everything** — it sees
   the grade it is on, and it can learn the distribution of climbs and hedge.
   As D2 limit 3.
4. **Grade is not a hotter knob** — the gearbox notch near 14 %. No figure is
   binned by grade. As D2 limit 4.
5. **Severity is not realistic, and cannot be** on this car; C4 is realistic in
   variability, not severity. As D2 limit 5.
6. **dt mismatch** — trained at 0.2, scored at 1.0, shared by both arms,
   symmetry unmeasured. As D2 limit 6. Longer training at 0.2 could make the
   agents more specialised to that step; that too is unmeasured.
7. **The baseline never enriches on the 12 % climb; at other grades this is
   unmeasured.** Both arms hold the lever. As D2 limit 7.
8. **The knock model is not validated against this car, and `c_turb` =
   6000 J/K is assumed.** As D2 limit 8.
9. **Do not rescue a null with H/τ.** As `PREREGISTRATION.md` limit 8 and D2
   limit 9.
10. **The reward barely punishes torque refusal on the steepest roads** — at
    16 % the torque-starver clears the gate by 0.006 (D2 section 10). A longer
    budget gives an agent more time to find that lever, and the arms can use it
    DIFFERENTLY: only the sighted agent can see a climb coming and cut boost
    early. So "both arms face the same reward" does not make the ablation
    immune. `check_d2_tracking.py runs_c4` prints each agent's tracking and
    each seed's sighted-minus-blind tracking gap, and 2a fixes what a flagged
    agent does to a PREVIEW HELPS reading.
11. **C4 and D2 are not independent samples.** C4 agent *k* continues D2 agent
    *k* — same seed, same road stream, and, if `check_c4_start.py` confirms it,
    the same first 50 000 steps — so C4 adds no new seed-level draws and is not
    a replication; the two are never pooled or counted as independent
    confirmations. Both are scored on the same twenty episodes with identical
    comparator rows, so any peculiarity of `EPISODES_D2` is common to both.
    Because the pairing is exact, the D2 → C4 change is tested (section 5c);
    what is forbidden is reading it off the two cells.
12. **The convergence verdict is only as good as its ten practice episodes and
    three checkpoints.** A policy can change in ways ten episodes do not show,
    or swing between checkpoints. This limit does not license overriding the
    verdict: the reading is the row of 2a the verdict selects.
13. **This is the third preregistered look at the same question on the same
    seeds** (Phase D sign p 0.3633, D2 0.6367). Every p here is unadjusted; the
    thesis reports the three together, one line each, as `analyse_c4.py`
    prints them.

## 9. How to run it

```bash
# 0. immediately before step 1, on the committed tree -- record in 6a
python run_phase_d.py --road random --steps 300000 --out runs_c4 --dry-run
                              # must print "tree     clean at <hash>" and 16 runs

# 1. sixteen runs, memory-capped, into runs_c4/ -- runs/ and runs_d2/ untouched
python run_phase_d.py --road random --steps 300000 --out runs_c4 [--jobs N]
python check_c4_start.py      # ~15 and ~80 min in, and after the second wave
                              # reaches 50 000 steps: certificates, budgets,
                              # identity with D2

# 2. BEFORE the test set is scored: identity and convergence, committed
python check_c4_start.py --out results/c4_identity.txt
python check_c4_convergence.py            # -> results/c4_convergence.txt
git add results/c4_identity.txt results/c4_convergence.txt && git commit

# 3. eight evaluations into results/c4_seed<N>.txt; then limit 10
python run_phase_d.py --road random --out runs_c4 --evaluate [--jobs 8]
python check_d2_tracking.py runs_c4 --out results/c4_tracking.txt

# 4. the preregistered test, beside D2 and Phase D
python analyse_c4.py
```

The eight evaluations start together where memory allows (`--jobs 8`), so that
none records the others' fresh result files as a dirty tree.

## 10. The gates, as they stood at commit

The environment, the road and the reward are unchanged in code: `plant_sha`
(which covers `engine_env.py`, where the reward lives) and `road_sha` are
D2's, computed live on this tree. D2's own gates — `check_random_road.py` (every
road binds; the blind arm is blind) and `test_reward.py --road random` — were
run on that code and passed (`PREREGISTRATION_D2.md` section 10); they are not
re-run, because nothing they measure has moved.

Run at `a1af19a`, the commit this file pins, 23 September 2026:

```
python random_road.py                        EXIT 0 -- SELF-TEST PASSES
    evaluate.EPISODES_D2 regenerates from seed 20260922 : True
    road_sha                                            : 1a29dc46db24f233
python check_c4_convergence.py --selftest    EXIT 0 -- SELF-TEST PASSES
    PRACTICE regenerates from seed 20260923; MEI = analyse_phase_d2.MEI (50);
    no episode seed shared with a frozen test set
live fingerprint, protocol d2                EXIT 0
    plant_sha b5a3069f32a83754  road_sha 1a29dc46db24f233
    episodes_sha 1c5d49852290d27c  git_dirty_plant_files []
git diff 8e91276 a1af19a -- analyse_phase_d2.py analyse_phase_d.py
    engine_env.py random_road.py plant.py      (empty: unchanged since D2's pin)
python check_c4_convergence.py --calibrate   EXIT 0 -- section 5b's table
python verify_docs.py                        EXIT 0 -- All 67 checks pass
python drift_test.py                         EXIT 0 -- 16 of 16 drifts CAUGHT
```

The launch dry-run is not here: it can only report a clean tree once this
file is committed, so it is the first entry of section 6a.

## 11. Outcome

*(Empty at commit. Added after the result, marked as coming after, the way
`PREREGISTRATION_D2.md` section 11 is.)*

## 12. The review before commit

Two adversarial reviews ran before this file was committed — one of the code
that disarms the traps and runs C4, one of this file's draft — each finding
checked by a second reviewer who tried to refute it. What they changed,
summarised; the record is `CHECKPOINT.md`, session of 23 September:

- **The draft's readings over-claimed (ii).** A C4 separation was read as
  "the budget was hiding an effect", and an INCONCLUSIVE C4 as weakening (ii),
  neither of which the design supports at power 0.24. Rewritten (2a), with the
  paired budget-change test added (5c).
- **"Preview costs damage" had no sentence** and would have been read as
  evidence for (i). D2's rule restored (2a, 5).
- **The crash command would have moved runs that were still training** —
  a live run and a crashed one look the same on disk. `train.py` now holds a
  `RUNNING` mark; the launcher refuses to move a live or recently changed
  directory and requires `--seeds` (section 6).
- **A finished run with only `checkpoint.zip` left resumed "at 0 steps" and
  trained over itself** — a defect older than C4. `train.py` now reads the step
  count from the zip.
- **The analysis could be fed the wrong files** — an extra `c4_seed*` file, a
  third agent, a forced mismatch, a stale convergence verdict. Each is refused
  (5, 5b).
- **The convergence rule judged settling per agent while the test is on
  pairs**, and nobody had measured its noise floor. Calibrated on D2's agents,
  and a pair condition added by the team (5b).
- **Four factual slips** — the determinism evidence ("a load of ten"), 12.9
  points on the wrong baseline, "field for field", and two commits named for
  one pin. Corrected (3, 5a, 6).

---

## Signed off

| | |
|---|---|
| written | 23 September 2026 |
| C4 — D2's design at 300 000 steps — decided by | **the team (Jad), 23 September 2026** |
| one variable at a time; seeds only after C4 | **the team (Jad), 23 September 2026** |
| convergence rule (5b) chosen by | **the team (Jad), 23 September 2026, before any of the sixteen C4 agents trained** |
| minimum effect of interest | **50 damage units — inherited from D2, set 22 September before D2 ran** |
| code it pins | **`a1af19a`** (after `f987049`) — `analyse_c4.py`, `check_c4_convergence.py`, `check_c4_start.py`, the trap fixes; `plant_sha` `b5a3069f32a83754`, `road_sha` `1a29dc46db24f233`, episodes `1c5d49852290d27c` |
