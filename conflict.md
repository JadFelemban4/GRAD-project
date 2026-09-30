# conflict.md — Ghassan's branch merged into Jad's: every conflict, and a recommendation for each

> **STATUS, 30 September 2026: DECIDED AND APPLIED.** Jad and Ghassan accepted the
> five decisions in section 0 (Ghassan's written reply, 30 September: all five, with
> "INCONCLUSIVE" as the wording for his retrain, and drive C before drive A). The
> merge commit applies the per-hunk recommendations below, the section 5 fixes and
> the fixes a–f of section 7. Decisions 1 (sub-stepping), 2 (fingerprint), 3 (spark
> cap) and 4 (ramps) are agreed for BEFORE the next training and are not in the merge
> itself: `CLAUDE.md`, the first box, lists them in order. The `_merge_review/proposed/`
> files named below are now the committed files.

Written 29–30 September 2026, for Jad and Ghassan to read and decide. Every figure below was printed by a script run on 29–30
September (on copies of the two branches, never on this folder), or it is marked
UNVERIFIED.

- **Jad's branch:** `JMF-2340550-sep17`, tip `086c519`
- **Ghassan's branch:** `JMF-2340550`, tip `74de99a`
- **Common ancestor:** `f6b46e9`, 19 September 06:30

---

## 0. The five decisions that change results — decide these first

| # | decision | recommendation | why |
|---|---|---|---|
| 1 | Whose physics goes into the merged simulator | **Ghassan's, with one fix added** (section 2) | His is more physical on every component where the code differs. The exception is numerical: his derived thermal constants make the coolant node ring above a 1.1 s step, so the thermal network needs sub-stepping |
| 2 | Whose experimental method goes into the merged branch | **Jad's** (preregistration, the MEI rule, fingerprints, the train.py guards), extended to cover Ghassan's data-derived constants | Ghassan's retrain has no written hypothesis, alpha, MEI or decision rule, and the fingerprint cannot see `data/derived_params.json` |
| 3 | What to do about spark advance, before anyone trains again | **Cap the spark trim at 0 (retard only), or at least report every result with and without the knock term** | All 68 trained agents on both branches push spark to the +4° action bound. With advance forbidden, their margin over `current-grade` disappears (section 3a) |
| 4 | What to do about the one-second knock spike at every grade step | **Ramp every grade change before the next ablation** (a new preregistration) | It is 34–102 damage units per D2 episode, the size of the 50-unit MEI, and it is the only place preview shows a "significant" effect (section 3b) |
| 5 | How to keep the finished experiments reproducible | **Tag both tips before committing the merge** | The merge changes `plant_sha`, so `evaluate.py` will refuse every Phase D, D2 and C4 agent on the merged tree. That refusal is correct, but those results can then only be re-run from the old commit |

Commands for decision 5, run in this folder before the merge commit:

```
git tag sep17-before-merge 086c519
git tag ghassan-before-merge 74de99a
```

---

## 1. Where the merge is, and what state it is in

| | |
|---|---|
| folder | `C:\Users\admin\Documents\graduation project\To main` — a fresh clone from GitHub. `GRAD-project` was not touched. |
| branch | `JMF-2340550-merge`, made from Jad's `JMF-2340550-sep17` at `086c519` |
| merged in | Ghassan's `JMF-2340550` at `74de99a` (`git merge --no-ff --no-commit origin/JMF-2340550`) |
| state | **merge in progress. Not committed. Nothing pushed.** |
| conflicted | 15 files, 91 hunks, 5 827 lines inside conflict blocks |
| merged automatically | 6 files both sides edited; 13 files only Ghassan edited; 5 only Jad edited |
| new files | 204 from Ghassan, 183 from Jad, and `evaluate.py`, which both created |
| deleted | **none.** Every file of both branches is in the merge: 454 of 454 (checked by listing both trees against the merge index) |

Conflict markers are in the zdiff3 style, which also shows what both started from:

```
<<<<<<< HEAD                  Jad
||||||| f6b46e9               the common ancestor
=======
>>>>>>> origin/JMF-2340550    Ghassan
```

### How to finish, once you have decided

1. Run the two `git tag` commands in section 0.
2. Open `To main` in VS Code. Source Control lists the 15 files under "Merge Changes".
3. Resolve each file as decided below. The proposed merged files are in `_merge_review/proposed/`.
   `git add <file>` for each one you finish.
4. Apply the silent-merge fixes in section 5 — git did not flag them, but they break things.
5. Run the checks in section 7 on the merged tree.
6. `git commit`. Git writes the merge message; add what you decided.
7. Push to a review branch first: `git push origin JMF-2340550-merge`. When both of you agree:
   `git push origin JMF-2340550-merge:main`. This is a fast-forward (checked: `origin/main`
   is an ancestor of both branches), so no force-push is needed.

To throw this attempt away: `git merge --abort`. `conflict.md` and `conflict_ar.md` are
untracked, so they survive an abort.

---

## 2. Whose simulation is more physical?

**Short answer: Ghassan's, on every component where the code differs — with one
numerical defect, and an oil node that is better on average but not at sustained
load.** Jad's expectation was right in direction. It was not right everywhere, and
the two simulators "agreeing" at 884 and 883 °C is a coincidence (section 2b).

### 2a. Component by component

| component | Jad | Ghassan | more physical | evidence |
|---|---|---|---|---|
| exhaust mass flow into the turbine node | fuel × 15 | air + fuel | **Ghassan, high confidence** | Mass conservation. Fuel × 15 is 4.5 % low at λ 1 and 11 % high at λ 0.85, and it hides about 22 % of the housing cooling that enrichment really buys. Jad's own `plant.py` and `validate.py` already use air + fuel; `AUDIT.md` M2 flagged it; `AUDIT_FIXES.md` marks M2 FIXED on Jad's branch although this item was never fixed |
| air density in aerodynamic drag | typed 1.2 kg/m³ | ideal gas at the cycle's ambient (1.12 at 42 °C) | **Ghassan** | unambiguous physics |
| boost ceiling: inlet temperature | charge temperature (~330 K) | ambient (315 K) | **Ghassan** | `plant.py`'s own docstring, on both branches, says the inlet is ambient |
| boost ceiling: shape | 2-parameter saturating fit (8 Sep) | running maximum of the measured envelope, from `data/derived_params.json` | **Ghassan, medium confidence** | Against drive B's 89 full-throttle readings, readings above the model's "ceiling" (impossible for a true ceiling): Jad 41 of 89, Ghassan 17 of 89. Caveat: the top bins rest on 5–8 independent readings, and a running maximum lets one high reading lift everything above it |
| BaselineECU part-load spark offset | 26.18 — the fitted line was never used (it sat above the knock limit at all 26 points) | derived 13.42 — the line now sets spark at 25 of 26 points, bias +0.00°, RMS 2.5° | **Ghassan** | reproduced exactly on both branches |
| gearbox ratios and upshift rule | ZF 8HP51 | ZF 8HP51 (same code) | **equal** | Jad's branch has had the real gearbox since `27e720c`, 19 September |
| downshift rule | flat 375 Nm | min(375 Nm, torque the model engine can deliver at that rpm) | **Ghassan, for the model** | On Jad's physics no policy can hold 130 km/h on a sustained 8–9.7 % grade (neutral reward −0.36 to −0.91 per step). That never touched D2/C4 (their grades are 12–16 %), but it would break any varied-road experiment. Neither rule is the real car's: both model engines make 4–46 % less than the real 500 Nm between 1800 and 5000 rpm |
| training and scoring time step | train 0.2 s, score 1.0 s | train 1.0 s, score 1.0 s | **Ghassan, for consistency** | But the defect is sidestepped, not fixed: the torque PI loop, the +3° knock pull and the one-step-late spark schedule are all per-step on both branches |
| thermal integration | stable at every step size tested | **unstable above ~1.1 s** | **Jad** | With Ghassan's derived constants the coolant node's explicit-Euler factor is −0.78 at dt 1.0, −1.67 at 1.5, −2.56 at 2.0. At dt 1.0 it rings and settles; at dt 2.0 (`generality_test.py` runs there on both branches) it never settles: 86.8–95.4 °C, the thermostat flipping 0 ↔ 1. **Fix before merging: sub-step the thermal network (e.g. 0.1 s inside each env step) or use an implicit update, then re-run `generality_test.py`** |
| turbine housing node | c_turb 6000 J/K, ua_gas_turb 0.90, ua_turb_amb 18 | identical | **equal** | All three are ASSUMED on both branches. c_turb sets τ, the denominator of H/τ |
| coolant / block node | assumed constants; regulates 88–90 °C | derived from the logs; regulates 92–93 °C like the car's median (~93 °C) | **Ghassan, medium confidence** | But the block ratio is identified by one warm-up drive (683640a0). Held out, that drive's coolant error is 14.2 K against Jad's 7.0 K, and held-out coolant is not better on average (4.91 against 4.79 K) |
| oil node | 5 % of fuel into oil, τ 14 s | heated by rpm, cooled by road speed, fitted, τ 57 s | **mixed** | See below |

**The oil node, in detail.** Replaying all seven usable drives through both
`thermal.py` modules with identical inputs:

- **Better for Ghassan:** lower oil RMSE on 6 of 7 drives free-running (7 of 7 with the
  block pinned to measured coolant, which is what the app does). Jad's node overshoots
  every hard pull by 22–32 K; on 7475b5d7 it spends 76 s above 110 °C where the car never
  passed 107 °C.
- **Worse for Ghassan:** at sustained load. On drive10 (Taif) the car spent 201 s above
  110 °C; Jad's model 6 s, Ghassan's 0 s. At the drive's 117 °C peak Ghassan's model reads
  −16.9 K, Jad's −4.1 K. `validate.py` row 8 (drive10's hottest ten minutes): Jad 96.4 °C,
  Ghassan 97.0 °C, car 103–111 °C. Both miss by the same amount.
- **A claim refuted:** Ghassan's `thermal.py` says oil heat "follows ENGINE SPEED ... not
  fuel". In every rpm bin the car's oil-minus-coolant gap rises with fuel (+1.5 to +2.8 K
  per g/s).
- **Not identified:** the logs do not pin the fuel share. Ghassan's own fit objective is
  flat from 0.05 % to 5 % of fuel (1.741–1.800 K); Jad's 5 % fits as well once the other
  oil constants refit. What the data rejected was Jad's whole combination, not his 5 %.
- **What it does to the experiments:** almost nothing. The oil term is 2.9 % of baseline
  damage on Jad's plant and 0.9 % on Ghassan's. Preview over current-grade stays between
  −0.31 and −0.45 points under every thermal and exhaust variant tried.

The locked climb's oil (110 °C Jad, 94 °C Ghassan) is an extrapolation on both: the logs
contain no sustained window at 2500–3000 rpm above 5 g/s of fuel. The car's 117 °C on
Taif came from 4000–4600 rpm in low gears, not from the kind of load the locked climb asks.

### 2b. Why the two simulators both say ~884 °C

The turbine peak barely moved (884.0 °C Jad, 883.0 °C Ghassan) because two of Ghassan's
fixes pull in opposite directions by about the same amount:

- the exhaust flow fix alone: **+5.5 K**
- air density at 42 °C (less drag, 340.2 → 335.5 Nm on the climb): **−6.2 K**

The damage the two simulators report differs by 12–13 %: baseline 959.8 against 920.1,
`current-grade` cutting 34.0 % against 43.4 %. 8.5 of those 9.4 points are the exhaust fix
alone, and the bias on Jad's branch is conservative, not flattering: fuel × 15 understates
the baseline, which runs at λ 1, and barely touches the protecting policies.

### 2c. What still holds on both

- `check_premise.py`: preview over `current-grade` is −0.4 points (Jad) and −0.3 (Ghassan).
- `test_reward.py` passes on both (4 of 4 Jad, 8 of 8 Ghassan).
- `validate.py` reads 8 of 11 on both, but Ghassan's rows 8–11 are scored against the car's
  own logs, which is the stricter and more honest test.

---

## 3. Two findings that matter more than any single conflict

Both apply to **both** branches, and both were found while checking this merge.

### 3a. Every trained agent exploits spark advance

- **Ghassan's 20 agents:** spark trim +3.5 to +4.0° on the climb, knock integral p95
  0.77–0.79 against the baseline's 0.61. With advance forbidden (`knock_margin.py`, 20
  frozen episodes) the median margin over `current-grade` falls from **+24.4 to −1.8
  points**; 9 of 20 still beat it. Reproduced from the committed `policy.npz` files, to
  within 0.05 %.
- **Jad's 48 agents (Phase D, D2, C4):** every one pushes the trim to 2.8–4.0° on the climb
  (median 3.8–4.0°), knock p95 0.68–0.79 against the baseline's 0.60–0.64. C4 on one frozen
  episode: margin **+15.7 → −1.2 points** with advance forbidden; two C4 agents on two D2
  episodes: damage rises 33–68 % with the cap. This is a first check (one or two episodes),
  not the 20-episode protocol.
- **What stops them is the action bound (+4°), not the knock knee.** In the model, the
  damage knee (KI 0.85) sits at 6.9° and the knock flag (KI 1.0) at 10.0°; the baseline
  runs at about 1°.
- **Is the benefit real?** In direction, yes: +4° at held torque lowers EGT by 28 K and fuel
  by 5 %. A constant +4° alone takes the locked-climb damage from 920.1 to 572.3 — about
  what the whole `current-grade` policy buys. But the car's own boosted logs put its real
  spark 3–8° *below* what the model's baseline would command at the same conditions (only
  31 genuine readings). That points against the extra 4° being margin the real engine has.
  The knock model itself is untested (`CLAUDE.md`; Ghassan showed the old test logged each
  ignition angle only once every ~8 s).
- **So:** the supervision claim ("the agent beats the hand-written rule") rests, on both
  branches, mostly on a lever that only the unvalidated knock model makes free. The preview
  ablation is not affected by this directly (both arms share the lever).

### 3b. A one-second knock spike at every grade step

At the instant the road steps from flat to the climb, the baseline ECU schedules spark on
the *previous* step's manifold pressure (cruise, ~66 kPa) while the load loop jumps to
~145 kPa in the same step. The knock integral reaches 2.1 for exactly one step.

- At dt 1.0 that one step is **66 damage units** on Jad's plant and **59** on Ghassan's —
  96 % of the whole episode's knock term. It scales with the step size (13 at dt 0.2, 133
  at dt 2.0).
- On D2's roads it is **34–102 units per episode — the size of the 50-unit MEI.**
- It is **all** of the hand-written "preview over `current-grade`" gap. On turbine-only
  damage the gap is +0.01 (Jad) and +0.04 (Ghassan) points.
- It is the **only significant preview effect in Ghassan's retrain**: on the knock term
  alone the sighted agent beats its blind twin in 10 of 10 seeds (sign p 0.0010), because
  the sighted agents learned to pre-retard for it. On thermal-only damage the sighted
  agents are slightly worse (4 of 10).
- Ramping the same grade over 8 s removes it (knock 69 → 3.5 on Jad's plant, 61 → 2.4 on
  Ghassan's; the turbine term unchanged).

Real grade changes are ramps and real ECUs schedule spark every cycle, so this "preview
benefit" would not exist on the car. It also sits inside Phase D, D2 and C4, whose roads
are all instantaneous steps. Whether it moved any of their preregistered results was not
measured.

---

## 4. The 15 conflicted files, hunk by hunk

"More logical" is judged on the merits: physics, measurement, internal consistency, and
consistency with the rest of the merged tree. Line numbers are in the merged file.

### 4.1 `thermal.py` — 1 hunk (code)

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 98–211 | the 8 September oil-cooler calibration: `ua_block_oil` 800 W/K "MEASURED", `ua_block_amb` 45 and `ua_oil_amb` 60 ASSUMED, with the comment updated for drive10 | every thermal constant read from `data/derived_params.json`, plus a new `ua_oil_ram` (sump cooled by road speed) | **Ghassan's code** | Take Ghassan's side. It is **required**: the silently merged `step()` uses `p.ua_oil_ram`, which exists only on his side, so Jad's side crashes on the first step. Keep Jad's 800 W/K rationale as a dated note. Add the sub-stepping fix (section 2a). Correct the docstring's "oil heat follows engine speed, not fuel" (refuted), and say that the fuel share is not identified |

### 4.2 `engine_env.py` — 2 hunks (docstring only)

The code merged silently and is Ghassan's in full, whichever way these two hunks go.

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 1009–1027 | "THIS IS PHASE D'S EVALUATION SCENARIO AND IT IS LOCKED ... 18 September" | the same, plus "12 % at 130 km/h, 42 °C ... adopted here on 19 September" | identical intent | Take Ghassan's (it states the scenario) |
| 2 | 1029–1085 | one line: "12 % at 130 km/h, 42 C, twelve minutes." | why the scenario needs a grade (the car's logs cannot load the engine), the 110 km/h history of his branch, and "the real box holds 7th ... so rpm and exhaust flow both rise" | **both, with a correction** | Keep Ghassan's text, but: date the 110 km/h paragraph as his branch's history; reconcile the gearbox paragraph with Jad's measured one (both are true against different six-speeds — Jad's had mistake 17's load guard, Ghassan's did not); "ten drives" becomes eleven. Also fix Jad's "96.4 kW at the wheels" elsewhere in the file: that is engine power; wheel power is 88.7 kW |

### 4.3 `evaluate.py` — add/add (both created it)

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 6–689 | 452 lines: the frozen protocols `EPISODES` and `EPISODES_D2`, the fingerprint refusal, `--out/--protocol/--label`, the model-budget line. Imported by 14 statements in 11 files | 246 lines: Jad's 19 September file plus the per-step recorder, `damage_thermal` (damage without the knock term), and a header read off the cycle. Imported by 9 statements in 4 files | **both needed** | **One file: Jad's skeleton, with Ghassan's three additions folded in.** A merged version exists and passed a smoke test: `_merge_review/proposed/evaluate.py` (copy it into this folder if you accept it). Do not take Ghassan's `main()` as written: its six-column table makes Jad's `analyse_phase_d.parse` silently read the IQR column as the median. The same file list must also move `results/phase_d_seed0_110kmh.txt` (section 5) |

### 4.4 `train.py` — 17 hunks

None of the 17 is a real either/or: Jad's side is the guard layer, Ghassan's the
training-design layer. **A candidate merged `train.py` reproduces Ghassan's terrain
training and Jad's D2 training bit for bit** (largest weight difference 0.0 for both), and
every guard fires: `_merge_review/proposed/train.py`.

| hunk | lines | topic | recommendation |
|---|---|---|---|
| 1 | 7–53 | usage and design sections | one usage block naming three designs (terrain dt 1.0 → `runs/terrain_dt1`; fixed dt 0.2 → `runs/`, closed; random dt 0.2 → `runs_d2/`, `runs_c4/`, closed). Rewrite Jad's "the sixteen Phase D agents still pass their fingerprint check" — false after the merge. Re-date Ghassan's "before any Phase D training" |
| 2 | 57–70 | timing introduction | keep both, each with its machine; Ghassan's "about five times better" is 3.3× (the 5.2× belongs to 29 September) |
| 3 | 72–81 | timing table | keep both rows, with machine and device |
| 4 | 83–93 | how long, who runs what | keep both; drop "agree who takes which seed" (both launchers run every seed on one machine) |
| 5 | 95–126 | surprises; ten seeds; GPU | keep both, each with its device: "the installed torch is a CPU build" is false on Jad's machine (CUDA, RTX 5070). Add: CPU and CUDA train different agents (measured) |
| 6 | 221–229 | imports | take both (`fingerprint`, `random_road`, `TerrainTrainingEnv`) |
| 7 | 244–303 | closed dirs, buffer size, `build_env` | keep Jad's `CLOSED` and `buffer_size`; one `build_env` with road ∈ {terrain, fixed, random} and an explicit `dt` (Ghassan) |
| 8 | 450–495 | argparse | the union: the silently merged code needs every argument of both sides; either side alone crashes |
| 9 | 498–505 | `--out` default and protocol | rewrite; `protocol` must exist (used at line 625) |
| 10 | 525–534 | prints | take both |
| 11 | 537–571 | steps per second | `19.2 if cuda else 13.7`, each with its provenance |
| 12 | 577–583 | `build_env` call | `build_env(not a.no_preview, a.seed, a.duration, a.road, a.dt)` |
| 13 | 789–795 | SAC constructor | both: `buffer_size=buffer_size(a)` and `device=a.device` |
| 14 | 854–883 | saves | both: Jad's atomic saves, then Ghassan's `merge_records` |
| 15 | 894–927 | `curve.csv` | rewrite: read 3- or 4-column files with the csv module and append. Jad's `loadtxt` cannot read Ghassan's road column; Ghassan's overwrite drops pre-resume episodes (AUDIT2 H2-3) |
| 16 | 929–985 | end-of-run summary | drop the first-5/last-5 verdict (Jad's `evaluate.py` says it is the weight draw, not learning). Ghassan's `cfg` / `cfg_path` must be passed into `_train_and_save`, or the run dies after saving |
| 17 | 1008–1021 | "next:" | by design: terrain → `train_all.py`, then `record_agents.py`; fixed/random → `run_phase_d.py` |

**The merged defaults matter more than any hunk.** Recommended: `--road` has no default
(refuse and list the three designs), because a terrain default would make Phase D's
preregistered `train.py --seed N` silently train a different design. `--dt` defaults to the
design's own (0.2 fixed/random, 1.0 terrain). `--device` defaults to `auto`, and the resolved
device goes into `meta.json`. `train_all.py` passes `--road terrain --dt 1.0 --device cpu`.

### 4.5 `test_reward.py` — 1 hunk

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 132–244 | the D2 gate (`D2_ROADS`, `main_random_road`) | the training-road roller (`road_roll`) | both | **Take both.** Proposed file: `_merge_review/proposed/test_reward.py`. Keep Ghassan's training-road starver check above all: on the merged plant the old fixed-road starver check passes on the 0–20 s launch alone (97 % of its penalty), so it no longer tests a sustained torque refusal. Update stale text: the D2 notch moved from 13.73 % to about 13.96 %; "16 % asks the most torque" should say most road power; "4 of 4" becomes "8 of 8" in the documents that quote it |

Why the starver margin collapsed (−0.90 Jad, −0.13 Ghassan): the starver cuts the boost
ceiling by 40 kPa. On Jad's plant the climb has 20 kPa of headroom, so the cut starves it; on
the merged plant the ceiling is the measured envelope evaluated at ambient, with 41 kPa of
headroom, so the cut never bites on the climb. Why random scores above neutral on Ghassan's
(+0.004): with air + fuel, the enrichment a random walk applies really cools the turbine;
revert only the exhaust formula and random falls to −0.017. It is not a torque hack.

### 4.6 `generality_test.py` — 2 hunks

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 124–135 | exhaust = fuel × 15, from the episode's fuel increments | `info["mdot_exh"]` (air + fuel, from the env) | **Ghassan** | take Ghassan's |
| 2 | 272–286 | refuse to run if no exhaust sample was measured (AUDIT M12: a silent 112.5 g/s fallback hid a bug for weeks) | a bare mean | **Jad** | Jad's refusal around Ghassan's source. Before trusting any H/τ output: fix the thermal stiffness at dt 2.0 (section 2a) |

### 4.7 `.gitignore` — 1 hunk

| hunk | lines | Jad | Ghassan | recommendation |
|---|---|---|---|---|
| 1 | 17–38 | `app/node_modules/`, `app/static/vendor/`, `.env`, `*typesafe_key*` (the jev key) | the per-step agent records `train_record.npz`, `eval_record.npz` (85 MB) | **take both** |

### 4.8 `verify_docs.py` — 6 hunks (the document guard)

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 463–474 | `read_lines(path)` | skip files marked retired | both | Jad's reader plus Ghassan's skip. **Taking Jad's side for the whole file crashes** (`NameError: check_derived`); the tested union is `_merge_review/proposed/verify_docs.py` |
| 2 | 754–855 | 71 lines of RETIRED patterns (university name, +11.7 shape and value, ...) | 27 lines of new RETIRED entries (enrichment 0.027 and 0.87, BSFC 241.2, pre-derivation premise figures, fitted k 0.837, "295.0 minutes") | both | take both lists |
| 3 | 860–890 | why `RETIRED_EXEMPT` governs both scans | exempt dated `SESSION_REPORT_*` files and generated agent reports under `results/agents/` | both | take both — **but see the name clash below** |
| 4 | 1190–1588 | `check_scenario` (351 lines: the experiment's own constants) | `check_derived` (44 lines: derived constants and premise figures are fresh) | both | take both functions |
| 5 | 1601–1619 | document list from `git ls-files`, with exemptions | glob with the new exemptions and `.venv` | both | Jad's `tracked_files` plus Ghassan's two exemptions |
| 6 | 1758–1789 | drive-count pattern up to "ten", with `(?<!adds )` | up to "eleven" | both | Jad's pattern with 11/eleven added |

**A clash git did not flag:** both sides define `RETIRED_EXEMPT_DIRS` — Jad as
`("results/void/",)`, Ghassan as `results/agents/` with the Windows separator. In the merged
file Jad's definition comes second and silently replaces Ghassan's, so Ghassan's exemption
of generated agent reports stops working. Rename one (for example
`GENERATED_AGENT_DIRS`), and normalise the path separator (Jad's file list uses `/`,
Ghassan's check uses `os.sep`).

Expected after the merge: Jad's guard, run on Ghassan's data, fails 10 of 67 checks and finds
**96 stale mentions in 21 files** (CLAUDE.md 13, validation_table.md 13,
presentation/index.html 10, REFERENCES.md 7, README.md 7, CHECKPOINT.md 7, handoff.md 6, ...).
They are the dataset figures: **11 drives, 321.7 minutes, 8 carrying samples, 568 pinned
samples across 7 drives** (was 10 / 295.0 / 7 / 547 across 6). The charge-temperature check
reads 3.8 % instead of 1.9 % unless drive B's assumed-ambient rows are excluded, as Ghassan's
build already does.

### 4.9 `validation_table.md` — 12 hunks

**Do not pick hunks: regenerate the table from the merged `validate.py` and
`compare_log.py`** (CLAUDE.md: never edit it by hand). The merged `validate.py` is
Ghassan's (Jad changed four comment lines), so the table must describe his rows 8–11, which
are scored against the car.

| hunk | lines | topic | Jad | Ghassan | recommendation |
|---|---|---|---|---|---|
| 1 | 12–36 | "last regenerated" | 22 Sep, section B from `compare_log.py` | 28 Sep evening, thermal derived, drive B added | regenerate, and date it |
| 2 | 44–51 | dataset history | "nine drives, 175.5 minutes" | "ten drives" | keep as history |
| 3 | 126–141 | the count | 8 of 11 | 8 of 11: 6 of 7 literature, 2 of 4 car | Ghassan's wording (it is what the merged script prints) |
| 4–7 | 145–287 | the misses and how car bands are built | EGT, oil 110.2 °C against 115–140, the after-filter note (pre-drive10) | the replay method, the car bands, EGT, oil rows 8–9 | Ghassan's content, since it describes the merged rows (his side carries the same EGT paragraph); Jad's after-filter note stays as dated history |
| 8 | 324–332 | points behind the residual | **26** | 22 | **Jad** — 26 is right on the merged data too |
| 9 | 357–367 | 20 °C reference separation | 6.2 % (0.891 / 0.839) | 6.3 % | recompute with `compare_log.py` on the merged data |
| 10 | 692–708 | the hottest oil | drive10, Taif | drive10 at 3700–4800 rpm; 7475b5d7 peaked 107 °C, not 117 | Ghassan (the correction is right) |
| 11–12 | 710–742 | drives without samples | ten drives, 295.0 min, seven of ten | eleven drives, 321.7 min, eight | **Ghassan** — these are the merged figures |

### 4.10 `CLAUDE.md` — 10 hunks (the handoff every session reads first)

| hunk | lines | topic | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|---|
| 1 | 85–519 | "Current state" | the C4, D2 and Phase D boxes (24 Sep) | the 29 Sep retrain, the 28 Sep evening and morning, the 27 Sep boxes | **both, rewritten** | Write ONE new box on top for the merged state, then keep every dated box of both sides below it, newest first. Correct in Ghassan's text: "PREVIEW ADDS NOTHING MEASURABLE" → INCONCLUSIVE under the MEI rule (power 0.26); "every agent advances spark to just under the knock knee" → they sit at the +4° action bound; "sep17's engine_env.py still has the six-speed box" → false; "7 conflicts, 4 in code" → 15 and 7. Add to Jad's text: all 48 of his agents use the same spark lever (section 3a), and the step spike sits inside D2 and C4 (section 3b) |
| 2 | 524–554 | the phase table | C1 and C4 done; D done three times; G started (Chapter 4 draft) | C done 29 Sep; D first result 29 Sep; G not started | **both** | Merge rows: each experiment labelled with its plant. G is started (Jad's draft exists). Delete Ghassan's "twelve commits apart ... merge before reporting": the merge is this |
| 3 | 591–607 | drive populations | 10 / 7 / 8 | 11 / 8 / 8 / 7 (drives behind the thermal derivation) | **Ghassan** | take Ghassan's (merged data) |
| 4 | 652–731 | "the numbers that matter" | Jad's analysis scripts; check_premise 959.8 at 884 °C; test_reward 4 of 4; 295.0 min, 10 drives | Ghassan's scripts; check_premise 920.1 at 883 °C; test_reward 8 of 8; 321.7 min, 11 drives | **both** | the union of scripts, with Ghassan's figures wherever they describe the merged plant. Jad's analysis-script figures stay (they read committed result files). `check_random_road`'s "weakest 13.73 % at +6.9 K" is stale on the merged plant (the notch moved to ~13.96 %; the deepest point is unmeasured) |
| 5 | 746–769 | `app.test_replay` | 49 of 49, peak 890.6 °C | 49 of 49, `--full` 59 of 59, peak 873.1 °C | **Ghassan** | the pins describe the merged physics (the exhaust fix moved the peak) |
| 6 | 2277–2295 | oil limitation | "Ten drives in the manifest, seven with usable samples" | the 28 Sep oil re-reading and the derived node | **Ghassan's content** | take it, and write "eleven drives, eight with usable samples" |
| 7 | 2315–2370 | the enrichment's worst cell | 4500–7000 rpm at 4–8 s misses by 0.076 (old dwell thresholds) | dwell thresholds derived on the timestamp axis; 8 of 9 cells within 0.02; weakest 0.033 | **Ghassan** | take Ghassan's for the merged plant (it fixes the open item Jad recorded); keep Jad's 0.076 as dated history |
| 8 | 2533–2539 | alert counts | 15 thermal | 14 thermal | **Ghassan** | the merged physics' count (pending the app test run) |
| 9 | 2647–2735 | repository layout | Jad's tools | Ghassan's tools | both | the union. Correct Jad's `random_road.py` line "engine_env.py is untouched on purpose -- editing it would move plant_sha": the merge moves it |
| 10 | 2945–3086 | "what to do next" | the C4 result and the live list | "the scenario changed on 19 September and now binds" | both | keep both as records, and write the new list from section 6 of this file |

Also merged silently: the heading now reads "Twenty-two mistakes" (Ghassan's 19–22 are in),
and the "ask who you are talking to" rule (Jad's, 28 September) is in. Both are correct.

### 4.11 `README.md` — 9 hunks

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 4–18 | "the mistakes already made" | "(twenty-two, numbered)" plus the 29 Sep retrain summary | both | Jad's count-free wording (counts go stale) plus Ghassan's summary, restated: +1.2 points is INCONCLUSIVE under the MEI rule; most of the margin rests on the knock model |
| 2 | 32–108 | Phase D, D2 and C4 status box | 28 Sep drive B and derived-constants updates | both | take both; label Jad's box "on the plant of `086c519`" |
| 3 | 168–183 | "what the script prints today" (21 Sep figures) | "what it printed on 16 September ... run `check_premise.py`" | **Ghassan** | date the table and point at `results/premise.json` |
| 4 | 389–396 | 20 °C reference k 0.891 | 0.890 | — | recompute on merged data |
| 5 | 517–536 | "eight drives of the ten (295.0 min)" | a HISTORY banner withdrawing the old closing argument | both | take both; 295.0 → 321.7 minutes, eleven drives |
| 6 | 551–583 | enrichment correlations with their error bar (1341 rows, ~67 independent readings, SE ~0.12) | the same correction, without the error bar | **Jad** | Jad's paragraph; recompute the row count on the merged data |
| 7 | 596–608 | the 4500–7000 rpm, 4–8 s cell: 0.87 | 0.83 (timestamp dwell) | **Ghassan** | Jad's own CLAUDE.md (28 Sep) says 0.87 is the retired axis |
| 8 | 619–632 | weakest cell 3500–4500 rpm, 0.90 against 0.93, 235 samples | derived dwell; weakest cell 0.033 lean | **Ghassan** | take Ghassan's |
| 9 | 727–749 | the H/τ section is void; do not rescue Phase D with H/τ | HISTORY; on the derived plant preview over current-grade is 0.0 points at every τ | both | take both warnings, and add: `generality_test.py` runs at dt 2.0, where Ghassan's coolant node oscillates |

### 4.12 `REFERENCES.md` — 5 hunks

| hunk | lines | Jad | Ghassan | more logical | recommendation |
|---|---|---|---|---|---|
| 1 | 86–92 | compression ratio settled (team, 19 Sep); no document cited yet | settled, and section 2c's Toyota Saudi Arabia page confirms the GCC car is the 382 hp engine | **Ghassan** | take Ghassan's — it puts a document behind the fact |
| 2 | 319–345 | validation rows 7–11 with literature bands (115–140 °C, 20–400 s, 88–108 °C, 1–600 s) | rows 8–11 with bands from our own car | **Ghassan** | take Ghassan's (they are what the merged `validate.py` scores); keep Jad's "48.0 s on the climb" in row 7 |
| 3 | 474–508 | the list of what is measured | the same, with the derived spark offset, the envelope as the ceiling, 568 samples across seven drives | **mostly Ghassan** | Ghassan's list, but Jad's knock line ("no p99 is quotable") and a recomputed enrichment count |
| 4 | 568–579 | engine version settled; the registration line still missing | settled | identical intent | Ghassan's, citing section 2c |
| 5 | 739–750 | the same, in the open-items list | the same | identical intent | Ghassan's |

### 4.13 `CHECKPOINT.md` — 3 hunks (the dated session log)

| hunk | lines | Jad | Ghassan | recommendation |
|---|---|---|---|---|
| 1 | 24–29 | `RETIRED-OK: 175.5, 9 -- ...` | a bare section-wide `RETIRED-OK` | Jad's (the guard reads the figure list) |
| 2 | 39–44 | the same | the same | Jad's |
| 3 | 745–2300 | 16 session entries, 17–28 September (1 344 lines) | 3 entries: 19 Sep; 21–28 Sep; 28 Sep evening (208 lines) | **Keep all 19 entries.** Put Ghassan's three after Jad's under a heading naming his branch, then add one entry for this merge. Nothing is deleted from a log. Flag inside Ghassan's 19 Sep entry: "rpm and exhaust flow both rise" is the reading Jad's CHECKPOINT calls backwards |

### 4.14 `handoff.md` — 20 hunks (the "start here" file)

Both sides rewrote the handoff for their own state, so hunk-picking gives a file that
describes neither. **Rewrite it once for the merged state**, using:

| hunks | Jad has | Ghassan has | take |
|---|---|---|---|
| 1 | "every mistake already made" | "everything already gone wrong" | either |
| 2 | "a project that works ... Phase D has now run" | a 28 Sep rewrite note | Jad's opening, with the merged state |
| 3 | a RETIRED-OK marker | a "READ THIS FIRST, 28 September evening" box about uncommitted work | drop Ghassan's box (it is committed now); keep the marker |
| 4 | what `check_premise.py` prints, and why the old four numbers are void | nothing | Jad's, with the merged figures (920.1 at 883 °C) |
| 5 | the command table with Jad's figures | the command table with Ghassan's (920.1, 8 of 8, `check_roads.py`, 2 of 4 car rows) | one table: Jad's analysis commands plus Ghassan's figures and commands |
| 6 | why 8 of 11 is expected (literature oil band) | the same, car bands | Ghassan's (the merged rows) |
| 7–12 | the Phase D route as a record | step 1 "drives first or retrain first", step 3 "DONE 29 Sep", timing, "ask the owner" | keep both as records; the new steps come from section 6 below |
| 13 | the "do not" table (no write path in `app/`, no raw samples on disk, ...) | the charge-temperature row | **keep Jad's table in full**, add Ghassan's row |
| 14–15 | "after changing the reward, the env, the plant or the scenario" | "... the gearbox or the roads", plus `check_roads.py` | Ghassan's wording (it covers more) |
| 16 | the H2b threshold explanation | a shorter one | either |
| 17–20 | "the project's result" as Phase D's null | the claim as a criterion; the evidence is a trained ablation | both; restate both results as INCONCLUSIVE and name the knock dependence |

### 4.15 `presentation/index.html` — 1 hunk

| hunk | lines | Jad | Ghassan | recommendation |
|---|---|---|---|---|
| 1 | 4740–4746 | "8 of 11 ... 26 operating points ... 295.0 minutes" | "7 of 11 ... 22 operating points ... 295.0 minutes" | **Both are stale.** The merged truth: 8 of 11 (6 of 7 literature, 2 of 4 car), 26 points, 321.7 minutes. This is the page an examiner is shown |

---

## 5. Things git merged without a conflict that still need fixing

Git reported no conflict in any of these. Each one breaks something or makes a document false.

| severity | what | fix |
|---|---|---|
| critical | `verify_docs.py` taken from Jad's side crashes (`NameError: check_derived`), because the silently merged code calls Ghassan's function | use the union file, `_merge_review/proposed/verify_docs.py` |
| critical | `results/phase_d_seed0_110kmh.txt` (Ghassan, 19 Sep) matches Jad's `results/phase_d_seed*.txt` glob. Measured: `analyse_phase_d.py` then prints n = 9, 6 of 9, sign p 0.2539 instead of the preregistered n = 8, 5 of 8, p 0.3633 | move it to `results/void/` (a move, not a deletion), and add a line to `results/void/README.md` |
| critical | `thermal.py` must take Ghassan's code (4.1), but his derived constants make the coolant node unstable above a ~1.1 s step | sub-step the thermal network, then re-run `generality_test.py` |
| high | `fingerprint.py` hashes only `plant.py`, `thermal.py`, `engine_env.py`. After the merge most constants live in `data/derived_params.json`, which `derive_params.py` rewrites whenever a drive is added. The physics can then change while `plant_sha` stays the same | add a hash of `data/derived_params.json` (values) as a fatal fingerprint field |
| high | on the merged plant, `plant_sha` is `c236a8db3e201090` (Jad's agents were trained on `b5a3069f32a83754`), so `evaluate.py` and the agents page refuse all 48 of Jad's agents | expected and correct; the section 0 tags keep the old results reproducible |
| high | `NEXT_CHAT_PROMPT.md` comes back (Jad's branch deleted it on purpose). It tells the next Claude session: "Resolve code toward THIS branch -- sep17's engine_env.py has the six-speed gearbox" (false), "7 conflicts" (15), "train.py RESUMES any checkpoint" (no longer true), "no measurable preview value" (INCONCLUSIVE) | do not delete: rename it to a dated `NEXT_SESSION_2026-09-29_ghassan.md` (Jad's convention) with a "superseded by the merge" banner, and correct the four sentences |
| high | `app/agent_trace.run_lanes` must also return `damage_thermal`, or `app/test_agents.py`'s whole-dict equality tests fail | add the key there and in `RESULT_KEYS` (`app/test_agents.py:199`): both patches in `_merge_review/proposed/` |
| high | `drift_test.py`, the guard's own test, crashes on the merged tree (`UnicodeDecodeError`, the Windows code page meeting Arabic text) | `encoding="utf-8", errors="replace"` at `drift_test.py:114` |
| high | Ghassan's 20 agents have no `meta.json` fingerprint (their `config.json` says `git_dirty true`) | score them only on the plant they trained on (commit `cbb8d09` + data sha `c4fdd4babfb3752a`), or retrain on the merged plant |
| medium | the D2 "notch" (the grade where the gearbox hands back 7th) moved from 13.73 % to about 13.96 %; `check_random_road.py`'s "+6.9 K" is the old plant's (on the merged plant 13.73 % runs at +75.5 K) | re-run `check_random_road.py` before any D2-design training on the merged tree |
| medium | pinned numbers move: `app.test_replay` peak 890.6 → 873.1 °C; alerts 15 → 14 thermal | take Ghassan's pins; the reason is in `app/test_replay.py` |
| medium | CPU and CUDA train different agents from the same seed (measured). Jad's ran on CUDA, Ghassan's on CPU; neither records the device | write the device into `meta.json`; refuse a resume on another device |
| medium | Jad's C4 follow-ups (a longer budget, or more seeds) can no longer change "one variable at a time" on the merged tree, because the plant changed too | run them from `sep17-before-merge`, or declare a new experiment |
| medium | `validate.py`, `app/test_replay.py`: Jad's comment edits still say "ten drives, 295.0 minutes" and "890.6 C" next to Ghassan's new figures | sweep with the figures in 4.8 |
| low | Ghassan's `engine_env.py` still says the neutral fan is "exactly neutral during the climb" — measured wrong on both plants | take Jad's corrected sentence |

---

## 6. The co-work plan, re-examined

### 6a. Its facts

| # | claim | verdict | what the evidence shows |
|---|---|---|---|
| C1 | Ghassan pushed 9 commits, the last at 8:07 pm | **confirmed** | 9 commits on 27–29 Sep (15 since the common ancestor); the last, `74de99a`, at 20:07:57 |
| C2 | Jad pushed 34 commits that night, mostly on the agents page | **confirmed as a push** | one push at 19:15 on 29 Sep carried 34 commits, authored from 28 Sep 11:24 to 29 Sep 18:43; 30 of the 34 are the agents page and its hidden models |
| C3 | exhaust was fuel × 15; Ghassan made it air + fuel; Jad's branch still has the old way | **confirmed** | section 2a |
| C4 | oil came closer to the car on the Taif drive, error 7.6 → below 4 °C | **partly** | the whole-drive RMSE 7.55 → 3.57 K (3.90 held out) reproduces. But at sustained load nothing improved (row 8: 97.0 against 96.4 °C, car 103–111), the Taif peak error got worse (−16.9 against −4.1 K), and one held-out drive (683640a0) got worse |
| C5 | Ghassan trains at the step he tests at; Jad's trained at 0.2 s, tested at 1 s | **confirmed** | but it sidesteps the per-step loops rather than fixing them |
| C6 | Ghassan trains on varied roads | **confirmed** | five families; the scored locked climb is itself 15 % of training |
| C7 | no rules written before training | **partly** | the design was committed (`cbb8d09`, 09:44) before training started (11:55). Not written: hypothesis direction, alpha, MEI, decision or stopping rule. Seeds were written as 5 and run as 10 |
| C8 | tested only on one road with one climb | **confirmed** | all 20 evaluation episodes are the locked climb; no rolling or two-climb road is scored |
| C9 | Ghassan's files say Jad has the old gearbox — wrong | **confirmed** | three sentences, all written 29 Sep in `cbb8d09`: `CLAUDE.md:181`, `NEXT_CHAT_PROMPT.md:54`, `SESSION_REPORT_2026-09-28_evening.md:290`. Jad's branch has had the ZF 8HP51 since `27e720c` (19 Sep) |
| C10 | turbo ~884 and 883 °C; preview adds nothing over current-grade on both | **confirmed, with a caveat** | the equal peaks are two corrections cancelling (section 2b); the −0.4 / −0.3 gap is entirely the one-second knock spike (section 3b) |
| C11 | agents advance spark to just before the knock limit | **confirmed, more precisely** | they stop at the +4° action bound, which happens to sit below the knee |
| C12 | spark advance forbidden: +24 points → −2 | **confirmed** | +24.4 → −1.8, reproduced |
| C13 | Jad's agents probably do the same; must check | **confirmed — now measured** | all 48; section 3a |
| C14 | the main result is firm: two branches, two methods, no preview effect | **overstated** | No experiment shows a preview effect, but none can be called firm. Ghassan's is INCONCLUSIVE under Jad's MEI rule (6 of 10, power 0.26); Phase D and D2 are INCONCLUSIVE; C4 is "smaller than the MEI" by the sign test only, not converged. And the two "methods" share the knock model, the damage function, the step roads and the step spike |
| C15 | the agents' advantage over the hand rule depends on the knock model | **confirmed on both branches** | section 3a |
| C16 | 15 conflicting files; three of five are not working; no battery | **confirmed on what git shows** | 15 files. No commit by Khaled, Abdulhadi or Mohammed on any branch; 4 of 5 team profiles are stubs; no battery file on any branch. Git cannot show work done outside the repository, so "not working" is not something this check can say |

### 6b. Its steps

| step | verdict | what I would change |
|---|---|---|
| 1 · one merged branch, half a day | **agree, but not half a day** | 91 hunks, 96 stale document figures and the section 5 fixes. Realistic: about one day for code and the checks, then one to three days for the documents. Rule of the merge: Ghassan's physics, Jad's method (section 0) |
| 2 · Ghassan's knock drive | **agree, with changes** | The drive cannot say whether the agents' +4° is safe, because nobody can command spark on the car. What it can say is whether the model's baseline spark is representative at the climb's operating point, and whether the real ECU is retarding there. Use drive C in `logs/DRIVE_PLAN.md`: six channels (rpm, air mass, actual and target ignition, coolant, ambient), firm roll-ons in a held gear through 2000–3500 rpm, afternoon heat, a straight empty road below the speed limit, the passenger on the phone, read-only logging only. Write the decision rule down before driving |
| 3 · Ghassan's 20 agents on multi-climb roads | **agree, with changes** | Preregister it first (road set frozen and hashed, primary test, MEI, thermal-only damage beside total). Run it on the plant the agents trained on (`cbb8d09`), before the merge re-derives anything. It runs from the committed `policy.npz` files on any machine; ~400 episodes is about an hour of compute |
| 4 · Chapter 4, two days | **agree, with changes** | The knock dependence now applies to Jad's own agents, and the step spike to D2 and C4. Keep the two branches' experiments side by side, never pooled, each labelled with its plant |
| 5 · the battery, for the other three | **agree** | The collapse test needs a second plant, and filling the profiles first is right (4 of 5 are stubs). Build it on the merged branch, and pick its H/τ range so that preview can matter there |
| pause the agents page | **agree** | After the merge the page refuses every agent it has anyway |

### 6c. What the plan is missing

1. **A decision on the spark lever before any new training** (section 0, decision 3) —
   otherwise the next training repeats the exploit.
2. **Removing the grade-step spike before any new preview claim** (decision 4).
3. **A 20-episode knock-capped rescoring of Jad's 48 agents.** Only one- and two-episode
   checks exist.
4. **The two git tags** (decision 5), and fingerprint coverage of `data/derived_params.json`.
5. **The merged branch's test set:** D2-style randomised roads plus multi-climb roads, with
   the blind-arm check — not the memorisable locked climb.
6. **Saying the results as they are:** every preview result so far is INCONCLUSIVE or
   one-seed-thin, not "firm", and every supervision result rests on the knock model.
7. **Fixing `NEXT_CHAT_PROMPT.md` and the six-speed sentences**, so the next session does not
   resolve code "toward" the wrong branch.

---

## 7. Checks to run on the merged tree, after resolving

`validate.py` (then regenerate `validation_table.md`) · `test_reward.py` · `check_roads.py`
· `check_premise.py` · `python random_road.py` (self-test) · `analyse_phase_d.py` and
`analyse_phase_d2.py` (must still print n = 8) · `python -m app.test_replay --full` ·
`python -m app.test_simulation` · `app/test_agents.py` · the node tests under
`app/static/sim/` · `verify_docs.py` (expected to fail on the stale figures in 4.8 until the
documents are swept) · `drift_test.py` (must stay 16 of 16).

### What these checks printed on a trial build of the recommendations

The recommended resolution was built in a throw-away copy (not in this folder): Ghassan's
`thermal.py`, both sides of every hunk where section 4 says so, the three proposed files,
the proposed `verify_docs.py`, and the two fixes marked "needed" below. Then every check was
run. Report: `_merge_review/reports/trial-merge.md`.

| check | result on the trial build |
|---|---|
| `random_road.py` self-test | passes (road sha `1a29dc46db24f233`, unchanged) |
| `analyse_phase_d.py` | 5 of 8, +4.8, sign p 0.3633, permutation p 0.4922 — **the preregistered figures**, but only after `results/phase_d_seed0_110kmh.txt` is moved (before: 6 of 9, p 0.2539) |
| `analyse_phase_d2.py` | 4 of 8, +6.4, sign p 0.6367, permutation p 0.4688 — unchanged |
| `analyse_c4.py` | matches `results/C4_RESULT.txt` |
| `validate.py` | 8 of 11 (6 of 7 literature, 2 of 4 car) |
| `test_reward.py` | 8 of 8 pass |
| `check_premise.py` | baseline 920.1 at 883 °C, preview over current-grade −0.3 |
| `check_roads.py` | passes: 40 roads, 14 bind |
| `generality_test.py` | runs; τ axis at the climb's measured 121.3 g/s (its docstring now contradicts the code and needs rewriting) |
| `python -m app.test_replay` / `--full` | 49 of 49 / 59 of 59 (pins 873.1 °C, 604.8 °C, 14 thermal alerts) |
| `python -m app.test_simulation` | 15 of 15 once `app/static/vendor` is populated (14 of 15 without it — the same on Jad's branch alone) |
| `app/test_agents.py` | 129 OK, 14 skipped (they need the gitignored `runs*/`) — **only with fix b below** |
| node tests (`app/static/sim/`) | 140 pass, 8 skipped, 0 failed, run through the `package.json` glob (Node 24 rejects a bare directory argument, a known issue) |
| `fingerprint` | `plant_sha` `c236a8db3e201090` (Ghassan's). Jad's agents carry `b5a3069f32a83754` |
| `verify_docs.py`, Jad's side alone | **crashes**: `NameError: name 'check_derived' is not defined` — the silently merged code calls Ghassan's function. Use the union |
| `verify_docs.py`, union | **7 of 73 checks fail**, all from the merge (each branch alone passes: Jad 67 of 67, Ghassan 44 of 44). Five are Jad's pinned values (959.8 / 884 / 890.6 / 608.0 / 15 against 920.1 / 883 / 873.1 / 604.8 / 14 on the merged tree). Two are the document scans: stale premise 959.8 (48 mentions), 295.0 minutes (26), "10 drives" (18), 884 (10) |
| `drift_test.py` | **crashes** on the merged tree: `UnicodeDecodeError` (cp1252), because the merged run echoes Arabic text and `drift_test.py:114` decodes the output as the Windows code page. Not a problem on Jad's branch alone |

**Fixes the trial showed are needed** (each was run once without the fix first):

- **a.** Move `results/phase_d_seed0_110kmh.txt` to `results/void/`, and add a line for it to
  `results/void/README.md`. (Its name says 110 km/h; its own header says 130.)
- **b.** `app/agent_trace.py` returns `damage_thermal`, **and** `app/test_agents.py:199` adds
  `"damage_thermal"` to `RESULT_KEYS`. Both patches: `_merge_review/proposed/agent_trace.patch`,
  `test_agents.patch`.
- **c.** `verify_docs.py` must be the union: `_merge_review/proposed/verify_docs.py`
  (it renames Ghassan's list to `RETIRED_EXEMPT_AGENT_DIRS` with `/` separators).
- **d.** `drift_test.py:114`: pass `encoding="utf-8", errors="replace"` to `subprocess.run`.
  Then re-run it only after `verify_docs.py` is green — until then its 16 of 16 means nothing.
- **e.** The 8 `results/phase_d_seed*.txt` files are frozen results scored on Jad's plant, so the
  document scan flags them. They need an exemption, not an edit.
- **f.** The five pinned values in `verify_docs.py` are a team decision: they pin Jad's plant.
  On the merged tree they become 920.1 / 883 / 873.1 / 604.8 / 14.

---

## 8. What was read, and how

- **The 15 conflicted files:** all 91 hunks were extracted with both sides and the common
  ancestor. The code hunks and the short document hunks were read in full. Three long
  document blocks were read by their headings and opening lines, not line by line:
  `CHECKPOINT.md` hunk 3 (the two sides' session logs, 1 344 + 208 lines, which are kept
  whole anyway), and the "current state" blocks of `CLAUDE.md` hunk 1 and `handoff.md`
  hunks 2–20, which are rewritten anyway. The three code files with the biggest conflicts
  (`evaluate.py`, `train.py`, `test_reward.py`) were read in full on both sides, with every
  commit that touched them, and a merged version of each was built and run.
- **The physics files** (`plant.py`, `thermal.py`, `engine_env.py`, `derive_params.py`,
  `derived.py`, `car_thermal.py`, `calibrate_thermal.py`, `validate.py`) and **Ghassan's
  experiment files** (`train_all.py`, `record_agents.py`, `knock_margin.py`,
  `results/agents/**`) were read in full and run: the premise, the reward gate, validation,
  the thermal replay over all drives, the knock cap, the step trace, dt 0.2 / 1.0 / 2.0.
- **Jad's experiment files** (the preregistrations, `analyse_*.py`, `evaluate.py`,
  `random_road.py`, `fingerprint.py`) were read in full; all 48 trained agents were probed.
- **Not read line by line:** the agent-replay design documents under `docs/superpowers/`
  (about 23 000 lines), the agents-page JavaScript, the generated HTML pages under
  `figures/`, and binary files (PNG, PDF, npz). They do not conflict and none of them sets
  physics; they depend on `evaluate.py`, `engine_env.py` and `random_road.py`, whose merge
  is covered above. A first attempt to read them with dedicated agents hit the usage limit
  and was not repeated.
- Full reports, with every command and its output, are in `_merge_review/reports/`, and the
  three proposed merged files in `_merge_review/proposed/`. That folder is **untracked** —
  it is evidence for this decision, not part of the project. Do not `git add` it unless you
  want it in history.
