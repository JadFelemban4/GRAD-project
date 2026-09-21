# AUDIT2.md — second technical review of `GRAD-project`, branch `JMF-2340550-sep17`

**Date:** 20 September 2026. **Auditor:** Claude (Fable 5.1), read-only session; nothing in the
repository was modified except this file, and no scratch file was left inside the tree.
**Baseline:** `AUDIT.md` (3 CRITICAL, 8 HIGH, 16 MEDIUM, 14 LOW) and `AUDIT_FIXES.md`.

Branch confirmed at the start of the session:

```
$ git rev-parse --abbrev-ref HEAD
JMF-2340550-sep17
$ git status --short
 D DOC/Abstract_AR.docx
 M DOC/Abstract_EN.docx
 D DOC/Abstract_Simplified.docx
?? DOC/Abstract_EN.pdf
$ git rev-list --left-right --count HEAD...origin/JMF-2340550-sep17
0	0
$ git rev-list --left-right --count HEAD...origin/JMF-2340550
18	6
```

HEAD is `c59346f`, in sync with `origin/JMF-2340550-sep17`. The working tree was NOT clean when the
audit began: two of the three abstracts the brief asked to be audited are deleted in the working
tree (uncommitted), the English one is modified (uncommitted), and an untracked PDF has appeared.
Those files were audited from `HEAD` and from the working tree separately (Part 4c).

**Method.** Every part below was executed by an independent agent under a read-only rule, with
commands and real output; every finding was then handed to two further agents — one instructed to
reproduce it from scratch, one instructed to refute it — and carries the verdict of that pass
(CONFIRMED = reproduced and not refuted; PLAUSIBLE = one of the two; WEAK = contradicted by one).
Historical trees were exercised with `git archive`, never by checking out. `train.py` was never
run against `runs/`. The full `evaluate.py` re-run on this branch's current code, with the trained
agents in `runs/`, was run once by the orchestrator and is quoted in Part 1.

Finding IDs are `C2-n`, `H2-n`, `M2-n`, `L2-n`, `N2-n` so they never collide with `AUDIT.md`.

## Which Phase D result is real

**Neither.** Both files were produced by a plant that this branch does not run, and the number
this branch's documents quote (+11.7 points) does not reproduce on this branch's code. Evidence,
all executed in this session:

**1. What each run actually used, read from the trained models, not from the headers.**
The SB3 checkpoint zips in `runs/` carry `start_time` and the last observation seen. Decoded:

```
runs/sighted_seed0/final.zip  start_time=2026-09-18 20:33:12 +03  num_timesteps=50000
runs/blind_seed0/final.zip    start_time=2026-09-18 22:30:11 +03  num_timesteps=50000
last obs, sighted ckpt_10000: v=130.0 km/h  rpm=2913  grade_now=0.120  preview=[0.12 0.12 0.12 0.12]
last obs, blind   ckpt_10000: v=130.0 km/h  rpm=2913  grade_now=0.120  preview=[0. 0. 0. 0.]
```

130 km/h at 2913 rpm on a 12 % grade is the **invented six-speed** (0.82 × 3.4) after the load-aware
downshift of `1df41a2`. The ZF 8HP51 that this branch runs since the merge `27e720c` sits in 7th at
~2706 rpm at the same point. So `results/phase_d_seed0.txt` is: scenario 12 % / 130 km/h (header
correct), plant = six-speed gearbox (header silent). The other branch's
`results/phase_d_seed0_110kmh.txt` is: scenario 12 % / **110** km/h (header wrong, as its own caveat
block says), plant = ZF eight-speed. The two files differ in **both** speed and gearbox, not in speed
alone.

**2. Timeline, from git and from the checkpoint metadata (all +03:00).**

| when | what |
|---|---|
| 18 Sep 17:26 `9f41082` | speed-by-grade sweep documented; 12 % / 130 km/h row reads +49.5 K on the six-speed |
| 18 Sep 20:33:12 | sighted training starts (SB3 `start_time`) |
| 18 Sep 20:33:38 `1df41a2` | `make_grade_climb` default 110 → 130 committed, with load-aware `gear_for` on the six-speed |
| 18 Sep 21:36 / 23:34 | sighted / blind runs finish (checkpoint mtimes) |
| 19 Sep 00:46 `a68715f` | `evaluate.py` + `results/phase_d_seed0.txt` committed (+11.7) |
| 19 Sep 05:50 `5c859f0` (other branch) | gearbox replaced by ZF 8HP51 |
| 19 Sep 07:35 `27e720c` | ZF merged into this branch — the plant behind `results/phase_d_seed0.txt` ceases to exist here |
| 19 Sep 20:13 `3d4f801` (other branch) | that branch's default 110 → 130, after its 110 km/h run |
| 19 Sep 21:42 `7f6c7f1` (other branch) | `results/phase_d_seed0_110kmh.txt` committed (+1.2) |

**3. The re-run on this branch's current code, same trained agents.**
`python evaluate.py runs/sighted_seed0 runs/blind_seed0` on HEAD, 76 minutes:

```
policy                        damage med      IQR    worst  fuel med   peak C
baseline ECU                       959.8      0.0    959.8      4664      884
reactive                           679.0      0.0    679.0      4843      862
current-grade                      633.2      0.0    633.2      4936      861
agent runs/sighted_seed0           279.3      9.6    360.6      5444      832
agent (blind) runs/blind_seed0     351.1     31.8    435.0      5171      845
  AGENT over CURRENT-GRADE: +36.9 points
  SIGHTED over BLINDED:     +7.5 points   <- THE ABLATION. This is the project's result.
```

against the file this branch ships:

| row | `results/phase_d_seed0.txt` | re-run on HEAD |
|---|---|---|
| baseline damage / peak | 572.8 / 857 °C | 959.8 / 884 °C |
| sighted median (IQR, worst) | 194.7 (35.6, 378.8) | 279.3 (9.6, 360.6) |
| blinded median (IQR, worst) | 261.4 (19.9, 336.9) | 351.1 (31.8, 435.0) |
| sighted over blinded | **+11.7** | **+7.5** |
| agent over current-grade | +36.3 | +36.9 |

The +7.5 is not a Phase D point either: it scores agents on a plant they were not trained on. The
+11.7 cannot be regenerated from this tree at all, because the six-speed `engine_env.py` it needs
exists only at `a68715f`. `evaluate.py` still prints `This is the project's result` under both.

**4. Which figure the documents should quote.** None, as a result. `CHECKPOINT.md` (19 Sep merge
entry) already says so in its own words — *"All twelve are on trees that no longer exist … Phase D
restarts from zero on this tree"* — and `results/README.md` says *"Do not quote it yet"*. But
`results/phase_d_seed0.txt` itself carries no such caveat, its header cannot distinguish the plant,
and the +11.7 is repeated as a measured advantage in `CHECKPOINT.md` (18–19 Sep entry, lines 857–873,
and the merge entry at line 907) and `DOC/SESSION_REPORT_2026-09-18.md` (Parts 12.3–12.5). `CLAUDE.md`
and `handoff.md` do not carry the figure at all (`git grep -n '11\.7'`: the only `CLAUDE.md` hit is an
unrelated +11.7 K heat-soak offset), which leaves the project's top-level handoff silent about the one
trained result while its current-state table still says Phase C is *next* and *nothing has been
trained yet*. The only quotable statements
today are the hand-written rows on HEAD (`check_premise.py`: baseline 959.8 at 884 °C, the constraint
binds by 34 K, preview over current-grade −0.4 points), and they are not the ablation.

**5. The four limitations from the superseded file, applied to the live one.**

| limitation on `phase_d_seed0_110kmh.txt` | applies to `phase_d_seed0.txt`? | disclosed on this branch? |
|---|---|---|
| header is a hardcoded string that can lie | **Yes, structurally.** `evaluate.py:143` still prints a literal; the other branch derives it from the cycle. The header was true here by coincidence and says nothing about the gearbox | No — not in the file, not in `results/README.md` |
| constraint does not bind | Bound by 7 K on the plant that produced it; binds by 34 K on HEAD. Not a defect of the file, but the 7 K margin is not stated in it | `CLAUDE.md` mistake 17 states 7 K; the file does not |
| one seed, gap inside the spread | Gap (66.7 damage units) exceeds both IQRs, but n = 1 training seed either way; the worst episode reverses the ranking (378.8 vs 336.9); on HEAD the IQRs swap (9.6 vs 31.8), which is itself evidence of seed-level variance | `results/README.md` and `CHECKPOINT.md` state n = 1 and the worst-episode reversal; the result file does not |
| eleven episodes of training | **Yes, identical:** 50 000 / 4 500 = 11.1 episodes, weight-conditioned policy | `SESSION_REPORT_2026-09-19.md` §4.1 and `CHECKPOINT.md`; the result file does not |

A fifth limitation applies to the live file only and to no document: **the plant is not the
plant.** The superseded file was at least produced on the gearbox its branch shipped. The live one
was produced on a gearbox this branch deleted seven hours later, and nothing in `results/` records
which gearbox, which `engine_env.py` commit, or which `DTHETA_DEG` produced it.

**6. The two causes, isolated by execution.** One neutral-baseline episode (720 s, dt 1.0; the
hand-written rows have IQR 0.0 because those policies ignore the episode weights, so one episode
is the median) on three exported trees, passing `v_kmh` explicitly:

```
tree_a68715f  six-speed (3.6…0.68 / 3.4)     v_kmh=110  damage=294.2 fuel=3620 peak=812.3 C
tree_a68715f  six-speed                       v_kmh=130  damage=572.8 fuel=4528 peak=857.0 C
tree_f6b46e9  ZF 8HP51 (5.25…0.64 / 3.15)     v_kmh=110  damage=462.7 fuel=3739 peak=839.7 C
tree_f6b46e9  ZF 8HP51                        v_kmh=130  damage=959.8 fuel=4664 peak=884.0 C
tree_HEAD     ZF 8HP51                        v_kmh=110  damage=462.7 fuel=3739 peak=839.7 C
tree_HEAD     ZF 8HP51                        v_kmh=130  damage=959.8 fuel=4664 peak=884.0 C
```

Every published baseline row is on that grid: 572.8 / 857 is six-speed at 130 (this branch's
file); 462.7 / 840 is ZF at 110 (the other branch's file); 294.2 / 812 is six-speed at 110 (the
premise figure `CLAUDE.md`, `README.md` and `handoff.md` still quote as "what the script prints
now"); 959.8 / 884 is what HEAD actually prints. Between the two result files, speed is worth
−44.3 K (130 → 110 on the ZF) and the gearbox +27.4 K (six-speed → ZF at 110); the two effects add
to the observed −17 K within 0.4 K, so nothing else in the 209-line `engine_env.py` divergence
moves the baseline. HEAD and `f6b46e9` are bit-identical on this grid, which confirms the merge
`27e720c` took the ZF plant unchanged.

## Is the scenario locked or was it searched

**Neither word fits, and the history is clear enough to say which parts of each are true.**
The scenario parameters (12 % / 130 km/h) were chosen from an envelope measured three hours
earlier, on engineering grounds that the repository states in full, and they have not moved since.
That is not a search for the preview effect: every hand-written sweep on the row shows preview
*losing* (−0.6 and −0.4 points), so nobody picked 130 because the claim survived there. But the
choice criterion was "the row binds", it was measured on a gearbox the project then replaced, and
the result produced on that gearbox is still shipped as the result after the plant under it
changed. The parameters are locked. The experiment is not.

**What git and the artefacts show, sentence by sentence against the docstring at
`engine_env.py:838-905`:**

| docstring claim | evidence | verdict |
|---|---|---|
| "The envelope was measured before a row was chosen" | `9f41082` (18 Sep 17:26) adds the eight-row sweep with `12 % / 130 → 899.4 °C, +49.5 K` and "three combinations bind"; the lock commit `1df41a2` is 20:33 | **supported** |
| "Decided … BEFORE any training run existed" | SB3 `start_time` of the sighted run is 20:33:12; `1df41a2` is 20:33:38. The run started 26 s *before* the commit, from the uncommitted working tree. The commit message quotes a `test_reward.py` pass (+0.00048) that takes ~5 min to produce, so the edit predates the run by at least that. The trained model's last observation reads 130 km/h at 2913 rpm, which only the edited six-speed produces | **supported in substance, false by 26 seconds.** The run used the new scenario, but a commit cannot prove what a working tree held 26 s before it |
| "Decided by the team" | one author identity (`endo.felemban@gmail.com`), Co-Authored-By Claude; no other identity touches the scenario until `3d4f801` a day later | **cannot settle** from git |
| "LOCKED … DO NOT CHANGE IT AFTER SEEING A RESULT" | `v_kmh=130.0` unchanged on this branch since `1df41a2`; the other branch adopted the same value in `3d4f801`. But `27e720c` (19 Sep 07:35) replaced the gearbox under the locked scenario, seven hours after `results/phase_d_seed0.txt` was committed, and that file was kept as the result. Baseline peak moved 857 → 884 °C; the agents' own ablation moves +11.7 → +7.5 when re-scored (Part 1) | **parameters locked; experiment changed after the result was seen.** The rule was breached from the plant side, not the scenario side, and the documents say so only in `CHECKPOINT.md` and this docstring |
| "It was chosen on the wrong gearbox … survived by luck" (added after the merge) | reproduced on the three-tree grid in Part 1: 857 °C on the six-speed, 884 °C on the ZF at the same row | **supported**, and it is the honest sentence. It is also an admission that the choice criterion was met on a plant that did not exist |
| "12 % at 130 was taken because it moves ONE variable … and because the car's own driving is hotter" | 110 → 130 is one variable; "hotter" rests on the app's estimate of `7475b5d7` at 890.6 °C, which is a model output (CLAUDE.md says so) | **physical, not circular**, but the second half is model-on-model |
| "What was tried and rejected: SAE J2807" | `9f41082` and CLAUDE.md carry the table (756.3 °C behind two tonnes) | **disclosed** |

**Where the history is silent.** Git cannot show when the decision was *made*, only when it was
committed; it cannot show who was in the room; and it cannot show the working tree at 20:33:12.
`git reflog` shows no amend or rebase around any of these commits, so the timestamps are the
original ones.

**Why this is a third thing, not "searched".** The sequence on 18 September was: the first audit's
C1/C2 fixes removed a phantom ten degrees of retard → the old scenario (12 % / 110) stopped
binding → a towing standard was tried and did not bind → an eight-row grade-by-speed envelope
was measured → the nearest binding row was taken → a rolling-road variant was tried and made
preview worse → the row was committed → training started. Every step is in the tree
(`9f41082`, `5923e29`, `1df41a2`, CLAUDE.md, `DOC/SESSION_REPORT_2026-09-18.md` Parts 6–10). A
search for the claim would have kept the variant where preview won; the project kept the ones
where it lost and wrote them up. What it did instead is subtler and an examiner will still ask
about it: **the selection criterion was "binds", binding is a precondition for the experiment and
not the effect, and the criterion was evaluated on a plant that was wrong by 27 K.** The
project's own rule for this case is in `AUDIT_FIXES.md:234` and `README.md:127` — choose the
scenario "from something external — a real grade, a published towing cycle, a measured ambient —
and never by turning a knob until the gap looks good." The chosen row is a grid point, not an
external cycle; the external candidates (J2807, the Taif drive) were tried and do not bind, and
that is disclosed. The defensible sentence for the thesis is therefore not "the scenario was
locked before training" but: *the scenario was selected as the mildest grid row that reaches the
damage knee on the model available on 18 September, disclosed alternatives were rejected because
they do not reach it, the model under it was corrected the next day, and every result produced
before that correction was re-run on the corrected model.* The last clause is currently false
(Part 1) and is the thing to fix.

## Part 7 — data integrity (executed by the orchestrator)

**The 26 points and both residuals reproduce.** `python compare_log.py data/master_points.csv`:

```
26 operating points from data/master_points.csv
  FITTED     k = 0.839            residual MAPE 1.1 %   (1 free parameter)
  DERIVED    k = 269.6 / T_in     residual MAPE 1.4 %   (0 free parameters)
             mean of the derived k over these points = 0.831
  HEADLINE: residual MAPE 1.4 %   target < 15 %   PASS   (zero fitted parameters)
WHAT 'STEADY' COVERS  (AUDIT.md M3)
    median 0.53   max 1.36
  points whose load held within 25 %: 5 of 26
```

Two small document mismatches follow from that output. The script prints the fitted constant as
**0.839**, while `CLAUDE.md`, `handoff.md` and `validation_table.md` quote **0.837** (the 22-point
value); `verify_docs.py` asserts only the derived 0.831, so the drift is invisible to it. And the
derived residual is written as "1.3 %" in `CLAUDE.md`'s limitations bullet and "1.4 %" everywhere
else, for a printed 1.4. M3's steadiness line now reads **5 of 26** where `AUDIT_FIXES.md` records
"2 of 23"; the script's wording ("steady in ROAD SPEED and ENGINE SPEED only … do not call these
'steady operating points' without saying steady in what") is honest, and `compare_log.py` prints
it on every run.

**`build_dataset.py` is order-independent where it matters, and the shipped `data/` is
reproducible.** Run into scratch directories with `--out`, never in place:

```
$ python build_dataset.py "logs/raw/*.csv" --out <scratch>/data_glob      # NO PYTHONUTF8: no console crash, exit 0
TOTAL  295.0 min across 10 drives, 26 distinct operating points ; span 30 - 75 kPa
$ python build_dataset.py <the ten files in REVERSE order> --out <scratch>/data_rev
TOTAL  295.0 min across 10 drives, 26 distinct operating points ; span 30 - 75 kPa
data_glob/manifest.csv        IDENTICAL to shipped
data_glob/master_points.csv   IDENTICAL to shipped
data_glob/master_samples.csv  IDENTICAL to shipped
data_rev/master_points.csv    IDENTICAL to shipped
data_rev/manifest.csv         differs from shipped — row order only (sorted md5 da4c9b46… both)
data_rev/master_samples.csv   differs from shipped — row order only (sorted md5 ba4f0008… both)
```

The mechanism is the one `AUDIT_FIXES.md` H7 names: `build_dataset.py:447` clusters "over
`sorted(glob(...))` order" and the CLI (`:517-525`) sorts each glob expansion, so the de-duplicated
points are a property of the data. What is NOT order-independent is the row order of the two
non-point files, which only matters to a byte-comparison; a consumer that indexes `master_samples`
by position would be order-dependent, and none in the repository does.

## Part 6 — branch state and team (executed by the orchestrator)

**What merging `origin/JMF-2340550` into this branch would do.** Simulated in a throwaway clone
(`git clone --no-hardlinks`, `git merge --no-commit --no-ff other`, then `--abort`); the repository
itself was not touched:

```
CONFLICT (content): CHECKPOINT.md      1 hunk
CONFLICT (content): CLAUDE.md          2 hunks
CONFLICT (content): engine_env.py      1 hunk   -- the make_grade_climb DOCSTRING only; the code merges clean
CONFLICT (add/add): evaluate.py        1 hunk   -- both branches added the file
auto-merged, taken silently:
  NEXT_CHAT_PROMPT.md              +169   resurrected (deleted on this branch)
  SESSION_REPORT_2026-09-19.md     +153   the other branch's longer version of the same file
  handoff.md                       +25
  results/phase_d_seed0_110kmh.txt +47    a SECOND file labelled "This is the project's result"
```

Nothing on this branch is overwritten silently, but four things would coexist that contradict each
other and must be reconciled by hand before either branch is called authoritative:

1. **Two Phase D result files**, each ending `<- THE ABLATION. This is the project's result.`
   (+11.7 on the six-speed at 130; +1.2 on the ZF at 110). Neither is a result of the merged tree
   (Part 1).
2. **Two accounts of why 130 km/h binds.** This branch's docstring and `CHECKPOINT.md` say the real
   gearbox is *taller* on the climb (7th, 2706 rpm, more load per cycle) and that 130 "survived by
   luck"; the other branch's docstring (`3d4f801`) says the real box "holds 7th … so rpm and
   exhaust flow both rise" and that the scenario "began binding because the MODEL BECAME MORE
   CORRECT". The first is the measured one (Part 1 grid: 2913 → 2706 rpm); the second is the
   reading `CHECKPOINT.md:939` explicitly calls backwards.
3. **Two `evaluate.py` files.** The other branch's derives the scenario header from the cycle; this
   branch's still prints a literal. The other branch's version is the one to keep.
4. **`NEXT_CHAT_PROMPT.md`** was deleted here on purpose (`git log --diff-filter=D`) and comes back.

**Recommendation.** Make `JMF-2340550-sep17` authoritative for code (it has the merged gearbox, the
locked scenario and the twenty frozen episodes) but take the other branch's `evaluate.py` header
derivation, then delete BOTH result files from `results/` and replace them with results produced on
the merged tree, each stamped with the `engine_env.py` commit hash, the gear ratios, `DTHETA_DEG`,
`TURB_PROTECT_K` and the scenario tuple. Resolve the docstring conflict toward the measured
mechanism. Keep `NEXT_CHAT_PROMPT.md` deleted.

**`JMF-new-plan` does not diverge.** `git rev-list --left-right --count HEAD...origin/JMF-new-plan`
prints `15 0`: every commit on it is already here (merged at `5ef1aa2`). The brief's premise is
stale. Its tree still defaults to `v_kmh=110.0` and the six-speed, so anyone who checks it out runs
the pre-audit experiment, but nothing on it changes a number on this branch.

**Identity and profile matching.**

```
$ git shortlog -sne --all
    19  badcloor <badcloor@gmail.com>
    17  JadFelemban4 <endo.felemban@gmail.com>
    12  JMF <jadfelemban4@gmail.com>
```

`team/README.md` says the assistant opens the profile whose `email:` line matches
`git config user.email`. Two of the three identities match nothing: `jadfelemban4@gmail.com` (12
commits, including `aca526d` which added `CONTROL_SCOPE.md`) is Jad under a second address that
`team/jad.md` does not list, and `badcloor@gmail.com` (19 commits: the tenth drive, the ZF gearbox,
mistake 18, the 3.0 L runtime check, the 110 km/h Phase D run) matches nothing because
`team/ghassan.md` still reads `email: <set this to your git config user.email>`. The matching is an
instruction to the assistant, not tooling: `git grep -n 'user.email'` finds it only in `team/`,
`CLAUDE.md` and `DOC/SESSION_REPORT_2026-09-18.md`. Consequence: on Ghassan's machine, and on
whichever of Jad's machines uses the second address, the assistant works without a profile — which
`CLAUDE.md` calls "not a courtesy". `team/README.md` says five people share the repository; git
shows two humans, and the five names appear only in the working-tree `DOC/Abstract_EN.docx` cover
page (Khaled Alotaibi 2340507, Abdulhadi Alfadli 2342863, Jad Felemban 2340550, Ghassan Alrefaei
2340394, Mohammed Alnejidi 2341614).

**Attribution.** The documents attribute the gearbox, the tenth drive, mistake 18 and the 110 km/h
run to Ghassan, and git attributes the same commits to `badcloor`, whom `team/ghassan.md` names as
Ghassan's GitHub handle; that is consistent. The 18 September session (scenario lock, `evaluate.py`,
the two training runs in `runs/`, `results/phase_d_seed0.txt`) is committed under Jad's primary
address and the documents say "the team decided"; git cannot confirm or deny the plural. Every
commit on both branches carries a `Co-Authored-By: Claude …` trailer, which the thesis's
authorship statement will need to address explicitly, because the mistake log, the session reports
and the audit responses are largely assistant-written prose committed under student identities.

## Part 4a — `verify_docs.py`, the guard (executed by the orchestrator)

**It runs, it is ordered correctly now, and it is narrower than its green line suggests.**
`python verify_docs.py` on HEAD, without `PYTHONUTF8` (no console crash this time):

```
SIMULATION FIGURES  (AUDIT.md H2 -- these were unchecked entirely)
  ok    validate.py rows inside the published band  data 8  docs 8
  ok    turbine time constant                        data 48.0
  ok    displacement                                 data 2997.5
  ok    crank-angle step is the studied one          data 0.25
CRANK-ANGLE CONVERGENCE  (AUDIT.md H1) … ok
DOCUMENTS vs DATA  … 311 figure mentions across 15 tracked files all agree with the data
RETIRED FIGURES   … none of the 39 retired figures appear as a live claim in 35 tracked files
All 38 checks pass (311 figure mentions scanned in the documents).
```

`check_simulation()` now prints before `report_documents()` and its four checks are inside the
38, so the ordering defect the first audit found (H2) is closed.

**Coverage, measured by injecting drifts into a `git archive` copy** (the real documents were
never touched; each drift was reverted before the next):

| drift injected in the copy | caught? |
|---|---|
| `README.md` "8 of 11" → "9 of 11" | **CAUGHT** (`WRONG README.md:154`) |
| `README.md` "ten drives, 295.0 minutes" → "nine drives" | **CAUGHT** (`WRONG README.md:19`) |
| `plant.DTHETA_DEG` 0.25 → 0.5 | **CAUGHT** (convergence check fails) |
| `CLAUDE.md` load residual "1.4 % with zero fitted parameters" → 1.7 % | MISSED |
| `CLAUDE.md` "295.0 min" (current-state table) → 299.0 | MISSED |
| `CLAUDE.md` app peak 890.6 → 895.1 (three mentions) | MISSED — never asserted |
| `results/README.md` and `CHECKPOINT.md` "+11.7" → "+13.7" | MISSED — never asserted, and `results/` is not tracked |
| `engine_env.py` docstring "12 % at 130 km/h" → 120 km/h | MISSED — no scenario figure is asserted |
| **`engine_env.py` DEFAULT `v_kmh=130.0` → 120.0** | **MISSED — the Phase D scenario can change silently and the checker stays green** |
| **`engine_env.py` `TURB_PROTECT_K` 1123 → 1100** | **MISSED — the protection trigger can move and the checker stays green** |
| `CHECKPOINT.md` "959.8 at 884 C" → 870 C | MISSED — no premise figure is asserted |
| `CLAUDE.md` "0.206 %" → 0.306 % (three mentions) | MISSED — never asserted |
| `CLAUDE.md` "294.2 at 812 °C" → 799 °C (the premise line in the numbers block) | MISSED — no premise figure is asserted |
| `CLAUDE.md` "derived k = 0.831" → 0.851 | **CAUGHT** (`WRONG CLAUDE.md:69`) |

So the guard protects the *dataset* figures (minutes, drives, points, span, pinned samples,
envelope, enrichment correlations, thermal calibration, charge temperature) and four simulation
figures (8 of 11, τ, displacement, `DTHETA_DEG`). It protects **none** of: the scenario
parameters, the trigger, the premise table, the app's pinned numbers, any Phase D figure, or
`results/`, `ABSTRACT.md`, `CONTROL_SCOPE.md`, `DOC/*`, `team/*`, `presentation/plan.html`,
`validate.py`, `new_drive.py`. The retired-figure scan is wider (35 files) but its list does not
include the figures retired on 19 September — **175.5, nine drives, 22 points, 30–74 kPa, 517
pinned samples on five drives** — which is why all of those still ship (Part 4c). Worse, six of
the RETIRED entries' own "use instead" strings are themselves stale (`verify_docs.py:355, 362,
364, 376, 378, 388`: "nine drives, 175.5 minutes, six carrying", "22 pooled points", "30-74 kPa",
"derived 0.829, fitted 0.837", "517 samples on five drives"), so a failure message today would
tell the reader to write the wrong figure — the 14 September lesson ("a retired-value list has to
be swept when the value that replaced it moves on") has recurred inside the list itself.

Two anchoring holes seen in the same run and already named by CLAUDE.md mistake 11: `presentation/index.html`
is a tracked file and carries "175.5" and "22 operating points" in Arabic and English sentences
(`index.html:583, 1865, 1994, 2495, 3015 …`) that match none of the anchored patterns, so the
scan reports it clean; and `build_dataset.py:175` writes "22 pooled operating points", which
"22 pooled points" and "distinct operating points" both fail to match.

## Part 3 — defaults that select an experiment (executed by the orchestrator)

An AST sweep over every `.py` in the root, `app/` and `presentation/` (parameters with defaults,
dataclass fields, class and module constants whose name or value selects a model, scenario,
calibration, dataset or threshold; call sites counted by name and by keyword) on HEAD and on the
three other branches. The rows that matter:

| default | file | HEAD | JMF-2340550 | JMF-new-plan | main | callers overriding | runtime guard |
|---|---|---|---|---|---|---|---|
| `make_grade_climb(v_kmh=)` | engine_env.py:834 | **130.0** | 130.0 | **110.0** | **110.0** | **0 of 10** | none |
| `make_grade_climb(grade=)` | engine_env.py:834 | 0.12 | 0.12 | 0.12 | 0.12 | **0 of 10** | none |
| `make_grade_climb(t_amb=)` | engine_env.py:834 | 315.0 | 315.0 | 315.0 | 315.0 | **0 of 10** | none |
| `make_grade_climb(dt=)` / `duration=` | engine_env.py:834 | 0.2 / 900 | same | same | same | 7 of 10 pass `duration`; evaluate/check_premise/generality pass `dt`; **train.py passes neither `dt` nor the scenario** | none |
| `Vehicle.gears`, `final_drive` | engine_env.py:325 | ZF 8HP51 / 3.150 | same | **six-speed / 3.4** | **six-speed / 3.4** | class constants | none |
| `Vehicle.SHIFT_LOAD`, `SHIFT_RPM_MAX`, `UPSHIFT_MIN_RPM`, `PEAK_TORQUE_NM` | engine_env.py:330-337 | 0.75 / 6000 / 2000 / 500 | same | **absent** | **absent** | class constants | none |
| `TURB_PROTECT_K` | engine_env.py:490 | 1123.0 | same | same | same | imported by 4 scripts + app | **none that pins the value** — `app/server.py LIMITS` derives from the same constant, so `test_replay`'s "served limits match engine_env" would follow a change (drift test: 1123 → 1100 stays green) |
| `BaselineECU.ENR_LOAD` | engine_env.py | 180.0 | 180.0 | 180.0 | **200.0** | class constant | `verify_docs` asserts 180 |
| `plant.DTHETA_DEG` | plant.py:183 | 0.25 | same | same | same | module constant | **`verify_docs` convergence check** (drift 0.25 → 0.5 caught) |
| `GEO = b58()` | engine_env/estimator/check_map/dump_sweeps | b58 | same | same | same | every `run_cycle` call passes it | **runtime check from 926b6f5** (`plant.py`, 17 of 17 call sites) |
| `SupervisoryTunerEnv(dt=)` | engine_env.py:524 | 0.2 | same | same | same | evaluate 1.0, check_premise 1.0, generality 2.0, dump_traces 1.0; **train.py and test_reward.py take the default 0.2** | none |
| `evaluate.DT`, `DURATION`, `EPISODES` | evaluate.py:60-86 | 1.0 / 720 / 20 literals | same | absent | absent | module constants | none — nothing hashes `EPISODES` |
| `generality_test.damage(scale=)` | generality_test.py:110 | 25.0 | same | same | same | **0 of 9** | none |
| `BaselineECU.base_lambda(dwell_s=)` | engine_env.py | 0.0 | same | same | same | 0 of 2 by keyword (positional use in the ECU path) | H8 regression test in `app/test_replay` |
| `plant.predict(p_exh_kpa=)` | plant.py | None → 1.15 × MAP | same | same | same | 0 of 6 | none |
| `check_premise.rollout(seed=)`, `generality_test.trajectory(seed=)`, `test_reward.roll(seed=)`, `dump_traces.rollout(seed=)` | — | 0 / 0 / 1 / 0 | same | same | same | 0 callers | none |

Two things follow. **First, the experiment's identity is a default at every level of the stack**:
the scenario (three defaults nobody passes), the gearbox (class constants), the trigger (a module
constant nothing pins), the step (a constructor default that two of the five callers take without
saying so — which is exactly how `train.py` came to train at 0.2 s while `evaluate.py` scores at
1.0 s), and the twenty episodes (literals nothing hashes). Standing on `JMF-new-plan` or `main`
today runs a different experiment (110 km/h, six-speed, and on `main` the pre-correction
enrichment gate) with no error. **Second, the 926b6f5 guard is correct and does not generalise**:
it asserts that every `run_cycle` call site passes a geometry, by AST sweep at runtime — one
parameter, the one that already burned the project. Of the sixteen defaults above, three have any
guard (geometry, `DTHETA_DEG`, `ENR_LOAD`) and the rest are protected by docstrings.

**Structural fix, described not applied.** (1) Remove the defaults for `grade`, `v_kmh` and
`t_amb` from `make_grade_climb` and define one module-level `LOCKED_SCENARIO = Scenario(grade=0.12,
v_kmh=130.0, t_amb_k=315.0, duration_s=720.0, dt_s=1.0, trigger_k=TURB_PROTECT_K)` that every
experiment script imports and passes explicitly; an omitting caller then fails at the call.
(2) Make `evaluate.py` print its header *from the cycle object* (as the other branch already does)
and write a fingerprint line into every result file: `engine_env` git hash, `Vehicle.gears`,
`final_drive`, `DTHETA_DEG`, `TURB_PROTECT_K`, `dt`, `duration`, and a hash of `EPISODES`; refuse
to evaluate a `runs/<tag>` whose saved fingerprint (written by `train.py`) differs. (3) Add the
scenario tuple, the eight gear ratios, `TURB_PROTECT_K`, `evaluate.DT/DURATION` and the
`EPISODES` hash to `verify_docs.check_simulation()` as value assertions, so the drift rows marked
MISSED in Part 4a become CAUGHT. (4) Give `SupervisoryTunerEnv.__init__` no default `dt`.

## Part 5 — the rest of the method question (executed by the orchestrator)

### Discarded scenario variants, and where each is disclosed

| variant | outcome | disclosed at |
|---|---|---|
| 10 % at 90 km/h (pre-8 Sep default, sized for the wrong engine) | void with mistake 1 | `engine_env.py` docstring (RETIRED-OK), CLAUDE.md mistake 1 |
| 12 % at 110 km/h, six-speed, pre-C2 | bound only through the phantom-retard bug | AUDIT.md C2, AUDIT_FIXES.md, README box, `engine_env.py` "WHY 130 AND NOT 110" |
| 12 % at 110 km/h, six-speed, post-fix | 812 °C, does not bind | CLAUDE.md numbers block, README box, handoff.md (all still quoting it as current — see Part 4c) |
| SAE J2807 Davis Dam, 0/1000/2000 kg trailer | 432 / 587 / 756 °C, does not bind | CLAUDE.md "published towing standard", `9f41082`, `engine_env.py` docstring |
| eight-row grade × speed envelope (12 % @ 90/110/130/150; 7 % @ 130/150; 16 % @ 110; 4 % @ 150) | three rows bind | CLAUDE.md, `engine_env.py` docstring, DOC/SESSION_REPORT_2026-09-18.md §6.2 |
| rolling road 8 % ↔ 16 % (first attempt, blind to both policies) | every row −0.1, zero information | CLAUDE.md "FIRST ATTEMPT … WAS BLIND", session report §8.1 |
| rolling road 2 % ↔ 16 %, periods 60/120/240/480 s | preview worse at every period | CLAUDE.md, `5923e29`, session report §8.2 |
| 12 % at 150 and 16 % at 110 ("second and third scenarios") | bind; declared but never run | `engine_env.py` docstring, CLAUDE.md mistake 17 |
| the nine/ten real drives replayed through `app/` incl. the Taif climb | one drive binds for 36 s; Taif does not | CLAUDE.md, README, handoff, `c59346f` |
| 12 % at 110 km/h on the ZF (the other branch's Phase D run, ten agents) | 840 °C, does not bind; +1.2 | `results/phase_d_seed0_110kmh.txt` on the other branch only; `SESSION_REPORT_2026-09-19.md` here says ten runs were "in flight" and gives no result |
| `generality_test.py`'s 520 s variant and its H2 sweep | figures void since C1 (AUDIT_FIXES) and not re-run since the gearbox | CLAUDE.md "Open, and honest about it" |

Every discarded variant is disclosed somewhere in the tree; none is hidden. That is the
project's genuine strength on this question and the thesis should say it in one table like the
one above. Two of them are disclosed in the wrong tense — the 812 °C row is presented as "what
the script prints now" in three top-level documents when it is the pre-gearbox figure — and one
(the 110 km/h ZF run with ten trained agents) is disclosed only on the other branch.

### Statistical power: what the experiment must become before +anything is a result

The number that decides "does preview help" is the difference between two *training* arms, and
its noise is the seed-to-seed variance of trained policies, not the episode-to-episode spread
inside one policy. The evidence that seed variance is large is already in the tree: the same two
agents, scored on the plant they were trained on and then on the corrected plant, moved from
+11.7 to +7.5 and their IQRs swapped (35.6 / 19.9 → 9.6 / 31.8). One seed per arm cannot bound
that. Concretely, before any ablation figure enters the thesis:

1. **Same plant throughout.** Train and score on the tree that ships, with a fingerprint
   (`engine_env` hash, gear ratios, `DTHETA_DEG`, trigger, scenario, `dt`, `EPISODES` hash)
   written by `train.py` into `runs/<tag>/` and checked by `evaluate.py`. Every run in `runs/`
   today fails this test and must be moved aside (CHECKPOINT.md already says so).
2. **Same `dt`, or a stated correction.** Train at 0.2 s and score at 1.0 s is a shared handicap
   whose symmetry is unmeasured (CLAUDE.md, "dt sits inside the signal"); Part 2b below shows the
   damage integral moves 6–8 % per doubling of the step. Either score at 0.2 s or make the
   per-step terms per-second first (M16) and re-measure.
3. **Unit of analysis = one trained seed.** For each seed, one number: the median damage over the
   twenty frozen episodes. Report the median and IQR of those per-seed medians across seeds, per
   arm, and the paired difference per seed (sighted_k − blinded_k, same seed index) since the
   arms share seeds.
4. **Pre-registered test and threshold, committed before seed 1 runs.** A one-sided Wilcoxon
   signed-rank (or exact permutation) test on the five paired per-seed differences at α = 0.05,
   with a minimum effect declared in advance in the units already used — e.g. "sighted cuts
   median damage at least 5 points more than blinded, relative to the baseline" — written into
   `evaluate.py` beside `EPISODES` and into CHECKPOINT.md with the commit hash. With n = 5 pairs
   the smallest attainable one-sided p is 1/32 ≈ 0.031, so five seeds can reach significance only
   if *all five* pairs point the same way; that is the honest reason five is a floor, not a
   choice. If a pilot of five shows a per-seed standard deviation of the paired difference
   comparable to the mean difference, plan for ten.
5. **Report the per-seed table, not the pooled one**, and report the worst seed the way the
   protocol already reports the worst episode.

### Every document that quotes +11.7 today, and how

| file:line | how it is presented |
|---|---|
| `results/phase_d_seed0.txt:19` | `<- THE ABLATION. This is the project's result.` — **established** |
| `results/README.md:15-19` | "THE FIRST MEASURED PREVIEW ADVANTAGE … One seed against one seed … Do not quote it yet" — provisional, but headed as a measured advantage |
| `CHECKPOINT.md:860` | "**SIGHTED over BLINDED: +11.7 points.**" then "Four limits on the +11.7, all of them stated" — provisional |
| `CHECKPOINT.md:907` | "Phase D's first ablation, +11.7 points" in the merge table — established in tone |
| `CHECKPOINT.md:971-981` | "All twelve are on trees that no longer exist … Phase D restarts from zero" — retracted |
| `DOC/SESSION_REPORT_2026-09-18.md:19, 476-477, 527, 541-544` | "Sighted beats blinded by +11.7 points. One seed each — not quotable yet"; "With trained agents it **wins by 11.7** … now measured" — mixed; §12.5 reads as a finding |
| `CLAUDE.md`, `README.md`, `handoff.md`, `ABSTRACT.md`, `CONTROL_SCOPE.md`, `team/*`, the three abstracts, `presentation/plan.html`, the meeting-update page | do not carry the figure |

So the figure is quoted in four files, hedged in three of them, retracted in one (the same
CHECKPOINT.md that also quotes it as the first ablation 50 lines earlier), and stated as the
project's result in the one file a script wrote. The retraction and the claim coexist in the
same document and nothing reconciles them.

## Part 4c — document claims the code does not support (executed by the orchestrator)

**The three abstracts.** Extracted from the `.docx` XML (python-docx is not installed) at `HEAD`
and, for the English one, from the modified working-tree file and the new untracked PDF:

| figure | EN docx @ HEAD | EN docx working tree (uncommitted, 20 Sep) | EN pdf (untracked) | AR docx @ HEAD (deleted in tree) | Simplified @ HEAD (deleted in tree) | `ABSTRACT.md` | data on this branch |
|---|---|---|---|---|---|---|---|
| minutes | 175.5 | **295.0** | 295.0 | ١٧٥٫٥ | 175.5 | 175.5 | **295.0** |
| drives | nine | — | — | تسع | nine trips | nine | **ten** |
| operating points | 22 | **26** | 26 | ٢٢ | — | 22 | **26** |
| span | 30–74 kPa | **30–75** | 30–75 | ٣٠–٧٤ | — | 30–74 | **30–75** |
| residual | 1.4 % | 1.4 % | 1.4 % | ١٫٤ ٪ | 1.4 % | 1.4 % | 1.4 % |
| ablation design | "re-evaluating the identical trained policy with its preview channel disabled" | "isolating preview by re-evaluating that policy blind" | same | "تُعاد تقييم السياسة المدرَّبة نفسها بعد تعطيل قناة الاستباق" | — | same as EN @ HEAD | **`evaluate.py` scores two separately trained agents; re-evaluating one policy with preview zeroed is the design AUDIT.md C3 voided** |
| training status | "is then evaluated" (present) | "will be trained" (future) | future | present | "Next we teach the software" | present | two agents trained 18 Sep; results file shipped |
| university | none named | none (college + department only) | none | none | none | — | University of Jeddah |
| team | — | five names + numbers, Group 3, CCAI-411 | same | — | — | — | git shows two humans |

Three consequences. (a) **Every committed abstract carries the figures this branch retired on
19 September** (175.5 / nine / 22 / 30–74). `ABSTRACT.md:12` says "Figures used here, and only
these: nine drives, 175.5 minutes, 22 operating points" and `CONTROL_SCOPE.md:204` says those are
"what is safe to quote today". Neither the figure scan nor the retired scan of `verify_docs.py`
can see any of these files, and 175.5 / nine / 22 / 30–74 are not in `RETIRED`. (b) **The
working tree is mid-repair and inconsistent**: the English abstract was rewritten on 20 September
to the current figures and a new template (five-member cover page), while the Arabic and
simplified abstracts were *deleted* rather than updated and `ABSTRACT.md` — which says "if the
two ever disagree, the .docx files win — regenerate this file" — still mirrors the old text. If
that state is committed, the project hands in one abstract with the current figures and loses
the other two. (c) **All versions describe an ablation the code does not perform.** The sentence
"the identical trained policy with its preview channel disabled" describes zeroing the preview of
one network, which for hand-written policies is the identity AUDIT.md C3 dismissed and for a
trained network is a policy evaluated out of distribution; `evaluate.py` and `train.py` do the
defensible thing — a second agent trained with the channel zeroed — and no abstract says so.

**`CONTROL_SCOPE.md`.** Lines 195-196 ("Nothing has been trained. `train.py` has never run past
its import guard") and 204 (the 175.5 figures) are dated 16 September and are false on this
tree: two agents trained on 18 September sit in `runs/` and a result file is shipped. The
read-only claims (no write path, no raw data on disk, one file per replay) are asserted by
`app/test_replay.py` and pass (59 of 59 with `--full`). The "six-channel live set" claim is
asserted and passes.

**`presentation/index.html`, `plan.html`, `data.js`.** The examiner-facing page still carries the
premise figures the first audit voided, as live numbers with no marker: `829.2` × 18, `548.6` ×
38, `437.6` × 16, `13.4` × 29, `33.8` × 13, `47.2` × 17, and the C1-era baseline row
`4091 / 829.2 / 879 / 128` at `index.html:1695`; `plan.html:868, 1429` print
"829.2 · 548.6 · 437.6 · 548.6" as the damage table and "175.5 min · 9 · 22 · 30–74 kPa" as the
dataset row; `data.js` still holds `"summary":{"damage":829.2,"peak_turb":879.4,"peak_oil":128.1}`
— the cooling-disabled trace — although its last commit (`52846ed`, 17 Sep) is the audit-fix
commit itself. `presentation/README.md:57-73` discloses all of this ("Every one of them is void …
Regenerate `data.js` … before showing it"), so it is disclosed, not fixed, and the guard cannot
help: `check_retired()` globs `**/*.md` and root `*.py` only, so `829.2` in an `.html` file is
invisible to the very list that retires it. `sweeps.json` (regenerated 18 Sep 21:08, `926b6f5`)
is post-fix but pre-gearbox. An untracked page `presentation/meeting-update-2026-09-20/` appeared
in the working tree during this audit (created 20 Sep 17:17, not by this session); it quotes
HEAD's figures (884 °C, +34 K, 295.0 / 292.0 min, 0.206 %, 890.6 °C flagged as a model value,
ZF 8HP51) and no retired one.

**`results/README.md`.** "Regenerate any of it with … `python evaluate.py runs/sighted_seed0
runs/blind_seed0`" — on this tree that command prints +7.5, not the +11.7 the file beside it
holds (Part 1). The README's caveats (n = 1, worst episode reverses, fuel +6.6 %) are honest and
the "Do not quote it yet" is right; the missing caveat is the plant.

**Top-level documents quoting the pre-gearbox premise as current.** `CLAUDE.md:143-147` ("It now
prints baseline 294.2 at 812 C, and a warning that the constraint does not bind on this scenario
at all"), `README.md` box ("What the corrected script prints now … 294.2 … 812 °C … The
constraint no longer binds") and `handoff.md:59-78, 133` ("What it prints now … 294.2 … 812 …
the constraint does not bind"). `python check_premise.py` on HEAD prints 959.8 at 884 °C and the
constraint binds by 34 K. The three entry-point documents therefore tell a reader the opposite of
what the script prints on the question the whole experiment turns on, while `CLAUDE.md`'s own
19 September checkpoint entry (`CHECKPOINT.md:958-964`) has the right numbers. `handoff.md:136`
also quotes `test_reward.py`'s neutral as −0.00888 (prints −0.00038; both inside the band).
`CLAUDE.md:1664` and `CHECKPOINT.md:657` pin the app's `7475b5d7` alert count at "13 thermal";
the suite expects and prints **15**.

## Part 2 — regression verification (executed by the orchestrator)

Reconstructed condition → what this branch does, by execution. "Holds" means the defect the first
audit described is absent here.

| id | condition described in AUDIT.md | what this branch does (command → output) | status |
|---|---|---|---|
| C1 | experiment scripts carry their own `NEUTRAL` with fan 0 / pump 0.3 | `git grep NEUTRAL` → `check_premise.py:25 NEUTRAL = neutral_action()`, `generality_test.py:31` same, `test_reward.true_neutral()` is a pass-through; `test_reward.py` prints `neutral action : [0.333 0.429 0.455 1. 1.]` = trims at zero, fan 1.0, pump 1.0 | **holds** |
| C2 | ECU scheduled on `_map_for()` open-loop guess (224 kPa vs 175 actual) | `reset()` seeds `self.map_b_prev = 40.0  # lagged baseline load for ecu.step -- C2`; instrumented baseline episode: tracked MAP median 178.2 kPa, ECU scheduled on 178.2 kPa; knock retard peak 3.20°, active 3.3 % of steps, spark median +0.7° on the climb; λ = 1.000 every step | **holds** |
| C3 | reactive protects less deeply than predictive; identity presented as evidence | `check_premise.py` prints "The three protecting rows now use the SAME protection DEPTH" and "equals reactive BY CONSTRUCTION, not as a finding"; preview-disabled row = reactive row (679.0) as expected; `p_grade_now` printed as "THE HONEST ONE" | **holds** — but see Part 4c: `presentation/` still shows the C1-era table |
| H1 | `dtheta = 0.5°`, not converged | `plant.DTHETA_DEG = 0.25`; `verify_docs` convergence block passes (EGT moves 4.0–5.9 K, torque ≤ 0.53 % on halving); drift 0.25 → 0.5 is caught | **holds** |
| H2 | checker cannot see simulation figures; `check_simulation()` ran after reporting | four simulation figures asserted and printed before `DOCUMENTS vs DATA`; total 38 includes them; "8 of 11" drift caught | **holds for the four figures it asserts; the guard is still blind to the scenario, trigger, premise and Phase D figures (Part 4a)** |
| H3 | dwell at an assumed 4.6 Hz | `verify_docs` prints corr(λ, dwell) −0.44 from timestamps and documents agree | **holds** |
| H4 | "n samples" are forward-filled rows | `verify_docs` prints "1341 forward-filled rows but only ~67 independent readings, standard error about 0.12" beside the correlations; `fit_envelope.py` prints a `readings` column (5 / 5 / 4 / 5 at the top) | **holds** |
| H5 | knock integral unvalidated | documented as a limitation in CLAUDE.md; no document calls the knock-limited spark calibrated (`git grep`) | **holds as a limitation; still unfixable here** |
| H6 | `train.py` cannot resume | resume path exists and loads the newest `ckpt_*_steps.zip`. Exercised on a scratch copy: `--steps 50000 --seed 0` on a finished run printed `resuming from …ckpt_50000_steps.zip at 50000 steps` / `already at 50000 of 50000 steps; nothing to do` and then **overwrote `curve.csv` with a header-only file (12 lines → 1) and re-saved `final.zip` (md5 a9d55ed2… → 55683eac…)**. A mid-run resume loses every pre-resume episode from the curve for the same reason (`Monitor` only holds this process's episodes) | **incomplete** — resume works for the weights, destroys the curve, and rewrites the final model on a no-op run; on the real `runs/` that is the only record of the trained agents |
| H7 | de-duplication order-dependent | Part 7: `master_points.csv` byte-identical in two input orders | **holds** |
| H8 | app's modelled λ never enriches | `app.test_replay`: `PASS H8: the modelled lambda reaches 0.81 after a sustained pull   lambda 0.810 at dwell 19.5 s` | **holds** |
| M2 | two sources of truth for damage | `engine_env.damage_rate` is the only `exp((T−1123)/45)`; `app/estimator.py:109` imports it. `generality_test.py:110 damage(temps, p, scale=25.0)` is a deliberate cost *family* for the H1 curvature sweep, but its `"exp"` row is `Σ(exp((T−1123)/25) − 1)` — a different exponential from the project's damage model, with no oil or knock term — and every H1/H2 row in the documents was scored with it | **holds for the env and the app; the generality sweep still scores with its own function** |
| M16 | per-step terms scale with `dt` | `SLEW` and the smoothness penalty are per second. But same policy, same seed, same weights, only the step changed (720 s, HEAD): baseline damage **900.9 / 959.8 / 1034.9** at dt 0.2 / 1.0 / 2.0; current-grade **567.8 / 633.2 / 723.2**; "cuts vs baseline" **37.0 % → 34.0 % → 30.1 %**. Peak turbine is invariant (884.0 / 884.0 / 884.2; 860.5 / 860.5 / 860.7) and fuel moves 0.5 %, so the physics is fine; the tracking loop is not: `_track_torque`'s PI advances per step, and `episode_summary["torque_viol"]` (0.507 / 0.059 / 0.031), `knock_events` and `steps` are per-step counts (`engine_env.py:812-815`) | **not fixed** — a 7-point swing in the headline percentage on the step alone, larger than any preview effect this project has measured with hand-written policies |
| M12 | `generality_test` wrong damage fn, τ, runs at import | `main()` guard present; τ from exhaust flow per AUDIT_FIXES; damage function see M2 | **partly** |
| M15 | stale document figures the checker cannot see | see Part 4a/4c: still open and larger than recorded | **open** |

Nothing in the 18 commits unique to this branch reverts a fix: the merge `27e720c` carries both
the ZF ratios and the load-aware `gear_for` guard (`engine_env.py:325-337`), HEAD and the
pre-merge ZF tree are bit-identical on the Part 1 grid, and the only code files that differ from
the other branch are `engine_env.py` (docstring plus the shift constants both sides share),
`evaluate.py` (this branch keeps the literal scenario header the other branch removed — the one
place this branch is *weaker*), `train.py` (+60 lines, all docstring and comments — the H6 resume path is identical on both branches) and
`verify_docs.py` (+28: the university-name guard and the Taif retirements).

---

## Did the fixes hold on this branch

`AUDIT_FIXES.md` claims 39 of 41 FIXED, M6 PARTLY, M15 OPEN. On this branch, by execution in
this session (commands and outputs in Part 2 above and in the per-part sections):

| how verified | findings | count |
|---|---|---|
| **by execution** (the condition reconstructed and the script or probe run here) | C1, C2, C3, H1, H2, H3, H4, H6, H7, H8, M2, M3, M5, M7, M8, M10, M11, M16, L11 | 19 |
| **by reading the code, or by an agent's cited command** (not independently re-run by the orchestrator) | M1, M4, M9, M12, M13, M14, L1, L2, L3, L4, L5, L6, L7, L8, L9, L10, L12, L13, L14 | 19 |
| **not verifiable here / status unchanged by design** | H5 (measured, not fixable), M6 (partly, by the response's own account), M15 (open) | 3 |

Of the 19 executed, **13 hold cleanly** (C1, C2, C3, H1, H3, H4, H7, H8, M5, M7, M8, M10, M11).
**Six are incomplete or not fixed on this branch:**

| id | status here | what the run showed |
|---|---|---|
| **M16** | **not fixed** | per-step terms still scale the outcome: baseline damage 900.9 / 959.8 / 1034.9 and current-grade 567.8 / 633.2 / 723.2 at dt 0.2 / 1.0 / 2.0; the headline "cuts" moves 37.0 → 34.0 → 30.1 %. `SLEW` was made per-second; `_track_torque`'s PI, `torque_viol`, `knock_events` were not |
| **H6** | **incomplete** | resume loads the newest checkpoint correctly, but re-running a finished seed wipes `curve.csv` (12 lines → header only) and re-saves `final.zip`; a mid-run resume truncates the curve to post-resume episodes |
| **M2 / M12** | **partly** | one `damage_rate` in the env and the app; `generality_test.py` still scores with its own `damage(…, scale=25.0)` whose "exponential" row is not the project's damage model, on a 520 s / dt 2.0 episode, against the reactive comparator C3 retired |
| **M3** | **script yes, documents no** | `compare_log.py` prints the caveat (5 of 26 within 25 %); `validation_table.md` never received it and pairs a stale n = 22 with the current residuals |
| **H2** | **partial** | the four asserted simulation figures are guarded and ordered correctly; the residual, τ-in-prose, the scenario, the trigger, the premise and Phase D figures are not (drift test, Part 4a) |
| **L11** | **half** | `presentation/index.html` was added to the figure scan (which cannot read HTML) and not to the retired scan (which could have caught the void figures it carries) |

**M15** is open and larger than recorded: this audit's document sweep found the retired dataset in
the three abstracts, `CONTROL_SCOPE.md`, `plan.html`, `team/jad.md`, `validate.py`, `new_drive.py`
and inside `verify_docs.RETIRED`'s own replacement strings, and the pre-gearbox premise in the
three entry-point documents (Part 4c).

**No commit unique to this branch undid a fix.** The merge `27e720c` carries both gearbox
changes; `train.py` differs from the other branch only in docstring; `verify_docs.py` only gained
retirements and the university guard. The one place this branch is *weaker* than the other is
`evaluate.py:143`, which still prints the scenario as a literal — the other branch derives it from
the cycle, and a plain merge reports that file as an add/add conflict, so the fix is one `--ours`
away from being lost.

## Regressions and incomplete fixes

| AUDIT.md id | on this branch | evidence |
|---|---|---|
| M16 per-step terms | not fixed for the tracking loop and the episode counters | Part 2 table; `engine_env.py:808-815` |
| H6 `train.py` resume | works for weights, destroys the learning curve, rewrites `final.zip` on a no-op | Part 2, scratch-copy run |
| M2 / M12 second damage function | live in `generality_test.py:110` and used at `:144-146, :209, :246-248` | agent run: H1 prints +18.2 / +13.0 pts *against reactive* on HEAD |
| C3 comparator | `generality_test.py` never received `p_grade_now` | `grep '^def p_' generality_test.py` → neutral, reactive, predictive only |
| M3 steadiness | caveat absent from `validation_table.md`, `README.md`, `CLAUDE.md`, `CHECKPOINT.md` | Part 7; `validation_table.md:142-143` |
| H2 checker blind spots | residual, τ prose, scenario, trigger, premise, Phase D, app figures all unasserted | Part 4a drift table |
| L11 presentation | retired scan globs `**/*.md` + root `*.py` only; `index.html`, `plan.html`, `data.js`, `app/*.py` outside it | `verify_docs.py:555-558` |
| M15 stale figures | see Part 4c and the findings below | — |
| H4 independent readings | the "1055 rows / 39 readings / ±0.17" triple in CLAUDE.md is the pre-drive10 population; the checker now computes 1341 / 67 / ±0.12 beside it | `verify_docs.py` note line; CLAUDE.md:569-575 |
| C1 / C3 in the presentation | `data.js` still ships the cooling-disabled baseline (829.2 / 879.4 / oil 128.1) and a blinded trace byte-identical to the reactive one | Part 4c; regeneration in a scratch tree gives 959.8 / 884 |

## New findings

IDs `C2-n` / `H2-n` / `M2-n` / `L2-n` / `N2-n`. Verdict: **CONFIRMED** = reproduced by the
orchestrator's own execution and/or by an independent verifier agent and not refuted;
**PLAUSIBLE** = an agent's cited command output, not independently re-run. Label after the
verdict. Evidence is the decisive line only; the full command output is in the part named.

### CRITICAL

**C2-1 · The only trained Phase D result was produced on a plant this branch has replaced, does not reproduce here, and nothing records which plant produced it.** CONFIRMED · Confirmed bug
`results/phase_d_seed0.txt:19`, `evaluate.py:143`, `train.py` (writes no metadata).
*What:* the two agents in `runs/` were trained 18 Sep on the invented six-speed (SB3 `_last_obs`: 130 km/h at 2913 rpm); the ZF 8HP51 landed 19 Sep 07:35; the file says `<- THE ABLATION. This is the project's result.` *Why:* the same command on HEAD prints +7.5, not +11.7, with every row moved (baseline 572.8 → 959.8), and the header is a literal that is byte-identical on both plants. *Evidence:* Part 1, items 1, 3 and 6. *Fix:* `evaluate.py` prints a fingerprint block from the objects (git hash, `Vehicle.gears`, `final_drive`, `DTHETA_DEG`, `TURB_PROTECT_K`, scenario tuple read from the cycle, `dt`, `duration`, hash of `EPISODES`, SB3 `start_time` of each model) and writes it into `results/`; `train.py` writes the same into `runs/<tag>/meta.json`; `evaluate.py` refuses a model whose fingerprint differs; move both existing result files under `results/void/` with the fingerprint that explains them.

**C2-2 · The scenario, the trigger, the premise table, the app's pinned numbers and every Phase D figure are outside the guard: `v_kmh` 130 → 120 and `TURB_PROTECT_K` 1123 → 1100 leave `verify_docs.py` green.** CONFIRMED · Confirmed bug
`engine_env.py:834`, `engine_env.py:490`, `verify_docs.py:485-551`.
*What:* the only `engine_env` constant asserted is `ENR_LOAD`; no figure of `check_premise`, `evaluate`, `app.test_replay` or the scenario is asserted or scanned. *Why:* a default edit re-bases every damage and peak figure while every document keeps saying 130 km/h, which is exactly how C2-1 happened, and CLAUDE.md's own rule is "a preview advantage quoted without the limit it was measured against is not a result". *Evidence:* Part 4a drift table (12 of 14 realistic drifts MISSED). *Fix:* a `check_scenario()` beside `check_simulation()` asserting `inspect.signature(make_grade_climb)` defaults, `TURB_PROTECT_K`, `Vehicle.gears` / `final_drive`, `evaluate.DT` / `DURATION`, an `EPISODES` hash, `check_premise`'s baseline damage and peak, and `app/test_replay`'s pinned peak and alert counts (written to a JSON the suite emits); pattern-scan the documents for each.

**C2-3 · The examiner-facing presentation ships the void premise set as live figures, and the retired-figure scan cannot see `.html` or `.js`.** CONFIRMED · Confirmed bug (disclosed for `index.html` in `presentation/README.md:54-85`; not for `plan.html` or `data.js`)
`presentation/index.html` (829.2 on 18 lines, 548.6 on 37, 437.6 on 15, 13.4 on 29, `:1695` the C1 baseline row 4091 / 829.2 / 879 / 128), `presentation/plan.html:868, 1429-1430` ("value today · printed by check_premise.py": 829.2 · 548.6 · 437.6 · 548.6; 33.8 % · 47.2 % · 13.4 pts), `presentation/data.js:4` (`"damage":829.2,"peak_turb":879.4,"peak_oil":128.1`; blinded trace byte-identical to reactive), `verify_docs.py:555-558`.
*Why:* README.md's box says "DO NOT QUOTE 829.2 / 548.6 / 437.6 … or the 13.4-point preview advantage" and the deck a supervisor sees says them on more than a hundred lines with zero markers; `verify_docs.py` prints green because `check_retired` globs `**/*.md` and root `*.py` only, so the one file added after L11 landed in the list that has no premise figure to compare against. `data.js` cannot be regenerated by any shipped script (the "pack" step has none) and was not regenerated in the audit-fix commit. *Evidence:* Part 4c; the scratch-tree `dump_traces.py` run gives 959.8 / 884 where the shipped file holds 829.2 / 879. *Fix:* make `check_retired` iterate `TRACKED_DOCS` plus `**/*.md`, `**/*.py`, `**/*.html`, `presentation/*.js`, with a self-test that every `TRACKED_DOCS` entry is in the retired list; strip tags before scanning HTML; then either regenerate `data.js` (write the pack step as a script) and rewrite the affected lines, or put the README's void banner on both pages and delete the live card in `plan.html`.

### HIGH

**H2-1 · The committed abstracts and the two scope documents carry the dataset this branch retired on 19 September, and describe the ablation design the first audit voided as the project's method.** CONFIRMED · Confirmed bug
`ABSTRACT.md:12, 28, 82, 128`; `DOC/Abstract_EN.docx` at HEAD, `DOC/Abstract_AR.docx` at HEAD, `DOC/Abstract_Simplified.docx` at HEAD; `CONTROL_SCOPE.md:69, 140, 153-154, 170, 183, 204-206`; `team/jad.md:102`; `validate.py:129`; `new_drive.py:146`; `presentation/plan.html:873, 1434`.
*What:* 175.5 min / nine drives / 22 points / 30–74 kPa against a shipped 295.0 / ten / 26 / 30–75; "the contribution of preview is isolated by re-evaluating the identical trained policy with its preview channel disabled" (the C3 identity) against `evaluate.py`, which trains and scores a second agent. The working tree holds a rewritten English abstract with the current figures (uncommitted) and the Arabic and simplified ones *deleted*; `ABSTRACT.md` still mirrors HEAD and says the `.docx` win. *Why:* the submitted artefact understates the evidence by 40 % of the minutes and states a method the code does not perform; `git checkout -- DOC/` reinstates the stale set. None of these files is in `TRACKED_DOCS`; 175.5 / nine / 22 / 30–74 are not retired patterns and are still named as the *replacement* values at `verify_docs.py:355, 362, 364, 376`. *Evidence:* Part 4c table. *Fix:* sweep all four figures in all four abstracts and `CONTROL_SCOPE.md`; change the ablation sentence to "a second agent trained identically with its preview channel zeroed, compared under the same fixed protocol"; put the battery plant in the future tense; commit the `DOC/` state actually being submitted and regenerate `ABSTRACT.md` from it; add `ABSTRACT.md` and `CONTROL_SCOPE.md` to `TRACKED_DOCS`; retire 175.5, "nine drives", "22 pooled/operating points", "30–74 kPa" and sweep the six stale replacement strings.

**H2-2 · M16 is not fixed: the outcome, and the headline percentage, still depend on the step size.** CONFIRMED · Confirmed bug (regression of M16)
`engine_env.py` `_track_torque` (PI per step), `:812-815` (`knock_events`, `torque_viol`, `egt_viol`, `steps` per step).
*What:* same policy, seed, weights, only `dt` changed: baseline 900.9 / 959.8 / 1034.9, current-grade 567.8 / 633.2 / 723.2 at dt 0.2 / 1.0 / 2.0; "cuts vs baseline" 37.0 → 34.0 → 30.1 %; `torque_viol` 0.507 / 0.059 / 0.031. Peaks invariant, fuel within 0.5 %. **The mechanism is not the one CLAUDE.md names.** Splitting the baseline integral by term (orchestrator re-run, reproducing the Part 4b agent): turbine 862.26 → 858.87 (−0.4 %), oil 28.16 → 28.16, **knock 69.33 → 13.85** between dt 1.0 and 0.2 — 55.5 of the 58.9-point shift, 94 %, is a one-step-wide knock spike (KI 2.14, 66.3 damage/s) at t = 181 s where the grade steps from 0 to 12 %, charged for one step whatever the step is. The PI in `_track_torque` is per-step, but its effect on the integral is inside the remaining 0.4 %. See H2-14. *Why:* a 7-point swing on the step alone, larger than any preview effect measured with hand-written policies; agents train at 0.2 s and are scored at 1.0 s; and the swing comes from the term the project has already declared uncalibrated. *Fix:* report the integral split by term; ramp the grade instead of stepping it; integrate the PI and the counters with `dt`; add a `dt`-invariance check (0.2 against 1.0 within a stated tolerance) to `test_reward.py`; re-state CLAUDE.md's dt paragraph.

**H2-3 · `train.py`'s resume path destroys the learning curve and rewrites `final.zip` on a no-op re-run.** CONFIRMED · Confirmed bug (H6 incomplete)
`train.py:127-161`.
*What:* on a scratch copy of a finished run, `--steps 50000 --seed 0` printed "already at 50000 … nothing to do", then wrote `curve.csv` as a header-only file (12 lines → 1) and re-saved `final.zip` (md5 changed). A mid-run resume keeps only post-resume episodes in the curve. *Why:* `runs/` holds the only copies of the trained agents and `CHECKPOINT.md:1093` already warns that `--seed 0` "would … write a `final.zip` holding an agent from a gearbox that no longer exists"; the curve is the only training record and it is silently blanked. *Fix:* on resume, load the existing `curve.csv` and append; skip `model.save` when `remaining == 0`; refuse to resume into a directory whose `meta.json` fingerprint differs from the current plant.

**H2-4 · The three entry-point documents tell a reader the opposite of what `check_premise.py` prints on the binding question, and quote four other figures the scripts no longer print.** CONFIRMED · Confirmed bug
`CLAUDE.md:143-147` ("It now prints baseline 294.2 at 812 C, and a warning that the constraint does not bind"), `README.md:96-110` ("What the corrected script prints now … 294.2 … 812 °C … The constraint no longer binds"), `handoff.md:59-78, 133-138` (same, plus neutral −0.00888, fitted k 0.837, 20 °C reference 0.890, "49 of 49 … 890.6"), `presentation/README.md:67-68`, `CLAUDE.md:1664` and `CHECKPOINT.md:657` ("13 thermal").
*What:* on HEAD the script prints 959.8 at 884 °C and the constraint binds by 34 K; `test_reward` prints −0.00038; `compare_log` prints 0.839 / 0.891; the app suite prints 15 thermal alerts and 59 of 59 with `--full`. The correct premise numbers exist only in `CHECKPOINT.md:958-964`. *Why:* the binding question is the one the whole experiment turns on, and "what each script should print today" is the reproduction reference; none of these figures is asserted by the checker (drift test rows 11 and 13). *Fix:* rewrite the three blocks from a fresh run in one commit and add the figures to `check_scenario()` (C2-2).

**H2-5 · The H/τ experiment still scores preview against the comparator C3 retired, on a different episode, step and cost function from every other script, and prints a large advantage that `check_premise.py` contradicts on the same plant.** CONFIRMED · Confirmed bug (M12 / M2 / C3 incomplete)
`generality_test.py:41-61` (no `p_grade_now`), `:93` (520 s, dt 2.0), `:110` (`damage(…, scale=25.0)`; "exp" = Σ(exp((T−1123)/25)−1)), used at `:144-146, :209, :246-248`.
*What:* the agent's time-boxed run on HEAD printed H1 rows `linear 57.1 % / 75.3 % / 18.2 pts` and `exponential 71.7 % / 84.7 % / 13.0 pts` — predictive over *reactive* — where `check_premise.py` prints +4.3 over reactive and **−0.4 over current-grade**. No document states the 520 s / dt 2.0 / scale-25 divergence; `DOC/SESSION_REPORT_2026-09-18.md:343` claims "no two places can say different things". *Why:* this is the project's central experiment and it is measured against the baseline the first audit declared unusable, with a cost model that is not the damage model. *Fix:* add `p_grade_now` and report against it; take `DURATION`, `DT` and the damage function from one shared module; keep the curvature family only as an explicitly separate H1 sensitivity table.

**H2-6 · A `RETIRED-OK` marker switches off the data comparison too, exempting 51 % of `README.md`, and one exempt section carries a live instruction to use a table CLAUDE.md declares void.** CONFIRMED · Confirmed bug
`verify_docs.py:283` (`_paragraph_is_historical` consulted by `scan_documents`), `verify_docs.py:207` (section mode triggers on the substring "section"), `README.md:31` (section marker running to line 148), `CHECKPOINT.md:183-211` ("Until the percentile rule is replaced, use the fixed-limit H2 table: 16.5 → 18.0 → 26.0").
*What:* measured exemption: README.md 267 of 522 lines, CHECKPOINT.md 251 of 1101, handoff.md 21.5 %, CLAUDE.md 18.0 %; an "8 of 11 → 9 of 11" edit inside an exempt paragraph passes, the same edit on a live line is caught. *Why:* the file's own docstring calls the old whole-section rule the failure it exists to prevent; the narrowed rule leaves the public README worse than the 36 % it quotes. *Fix:* make the exemption figure-specific (`<!-- RETIRED-OK: 168.1, 113 -->`), require the exact `: section` token, print the exempted line count per file, and delete the CHECKPOINT.md instruction.

**H2-7 · `CLAUDE.md`'s own drive-population table — written to stop miscounting — is wrong on both counted rows, and the "six drives carrying samples" contradiction spans seven files the patterns cannot reach.** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug
`CLAUDE.md:106-108` (manifest **9** / carrying **6**; data 10 / 7; 6 is the count of drives carrying *points*), `CHECKPOINT.md:626-630` (clone), `CLAUDE.md:1495` ("Eight drives, six with usable samples"), `validation_table.md:24`, `engine_env.py:38`, `build_dataset.py:93`, `presentation/index.html:3971-3972, 4601`, `DOCUMENT_STATUS.md:99`, `logs/DRIVE_1_card_v*.md`.
*Why:* the line under the table says "`verify_docs.py` asserts the first two separately for exactly this reason"; it asserts them (data 10 / 7) and passes, because neither pattern reaches a table cell or a bolded number. *Fix:* set 10 / 7, add a fourth row "6 — drives carrying operating points", strip `**` before matching and add table-cell and "N of which carry" patterns.

**H2-8 · `CONTROL_SCOPE.md` restates mistake 10 as a claim to a car company and says nothing has been trained.** CONFIRMED · Confirmed bug
`CONTROL_SCOPE.md:55-57` ("The zero action reproduces the baseline ECU exactly"), `:195-197` ("Nothing has been trained. `train.py` has never run past its import guard … Phase D … has not started"), `:140` ("validated by … replay against our own nine drives"; the suite replays two), `:71` ("all 656 channels … all of them readable"; 338 are all-zero), `:279` (open item CLAUDE.md records as settled).
*What:* the zero action scales to spark −2°, λ −0.045, boost −12.5 kPa, fan 0.5, pump 0.65; `neutral_action()`'s docstring opens "NOT zeros". Two agents and a Phase D table exist. *Why:* section 6 is titled "Before anyone shows this to anyone — the honest current state" and its own open item predicted it "goes stale fastest". *Fix:* the sentence becomes "`engine_env.neutral_action()` — not the zero vector — reproduces the baseline; see mistake 10"; rewrite section 6 with a date; correct the four other claims.

**H2-9 · The scenario's parameters are locked; the experiment under them is not, and the lock claim as written is 26 seconds from being false.** CONFIRMED · Potential risk (methodological)
`engine_env.py:838-905`; `README.md:124-128` ("never by turning a knob until the gap looks good"); `AUDIT_FIXES.md:234`.
*What:* the row was chosen by a one-variable sweep for constraint activity on the six-speed, both external candidates (J2807, Taif) were rejected because they do not bind, the plant was replaced the next morning and the result kept; the sighted run started 26 s before the lock commit (the edit demonstrably preceded it — the run used 130 km/h and the load-aware 5th gear — but no artefact proves the working tree). The other branch's docstring (`3d4f801`) gives a different account of the mechanism and would spread the "before any training run" sentence to nine places on merge. *Why:* an examiner will read the docstring and the README's rule three lines apart. The saving fact is measured and should lead: preview *loses* on this row under every hand-written policy (−0.6, −2.3, −0.4), so the choice cannot have been made to favour the claim. *Fix:* rewrite the header to what is checkable — chosen by a disclosed sweep for constraint activity (cite `9f41082`, `5923e29`), not from an external cycle; corrected plant on `27e720c`; every pre-correction result re-run — and cite commit hashes instead of "before any training run existed".

**H2-10 · Merging `origin/JMF-2340550` as it stands produces two "project's result" files, two contradictory mechanism accounts, a false banner and an add/add conflict that hides the one fix this branch lacks.** CONFIRMED · Potential risk
`engine_env.py:837` (docstring conflict; "other" says "rpm and exhaust flow both rise", the measured direction is the opposite: 2913 → 2706 rpm), `evaluate.py:143` (add/add; "other" derives the header from the cycle), `handoff.md:36` (incoming banner "at this branch's 110 km/h default it never binds" lands above the untouched stale 294.2 table), `CHECKPOINT.md:711` (521-line conflict; a `--theirs` resolution deletes four session records), `results/phase_d_seed0_110kmh.txt` (arrives silently), `NEXT_CHAT_PROMPT.md` (resurrected; says ten agents are in `runs/`), `SESSION_REPORT_2026-09-19.md:294-298` (carries the refuted "6th at 2416 rpm, higher rpm" mechanism now).
*Evidence:* Part 6 merge simulation. *Fix:* Part 6 recommendation; resolve `CHECKPOINT.md` by concatenation and say so in the conventions.

**H2-11 · The team-profile mechanism fails for two of three git identities, and the attribution record is what an examiner will read.** CONFIRMED · Maintainability issue
`team/ghassan.md:3` (placeholder email), `team/jad.md:3` (one of Jad's two addresses), `team/README.md:3` ("five people"), every commit (48 of 48 carry `Co-Authored-By: Claude …`, none a human co-author; no deliverable document has a byline).
*Why:* 31 of 48 commits match no profile — including all of the engine-literate contributor's — and CLAUDE.md calls the profile "not a courtesy"; on a project marked on individual contribution the record says five claimed authors, three identities, two unmatched, an AI co-author on 100 % of commits. *Fix:* fill the two email lines; add a `verify_docs` check that every `git log --format=%ae` address matches a profile; add an authorship note to the thesis and bylines to `AUDIT.md`, `AUDIT_FIXES.md` and the session reports.

**H2-12 · M3's steadiness caveat never reached the evidence document, which states the point count three ways and pairs a stale n = 22 with the current residuals.** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug (M3 incomplete)
`validation_table.md:142-143` (n = 22 beside 1.4 % / 1.1 %), `:136` (26), `:160` (23), `:210, :387, :459` (22), `:144` (fitted k 0.837), `:218` (52 °C mean; script 51 °C); `AUDIT_FIXES.md:146, 216` ("2 of 23"; today 5 of 26).
*Fix:* put the runtime caveat into the table with today's numbers, sweep 22/23 → 26, retire "22 steady|23 points|22 windows".

### MEDIUM

**M2-1 · Phase B's own figures drift unasserted: derived residual written as 1.3 % and 1.4 % in one bullet; fitted k 0.837 in eleven places where the script prints 0.839; 0.890 → 0.891; "6.3 % separation" → 6.2 %.** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug
`CLAUDE.md:1388` (1.3 %) against `:1392` (1.4 %), also `:543`, `logs/CHANNEL_SET_FINAL.md:27`, `presentation/index.html:956` (1.3 %); 0.837 at `CLAUDE.md:69, 1390`, `README.md:269`, `CHECKPOINT.md:48, 415`, `handoff.md:30, 138`, `validation_table.md:144, 157, 176`, `compare_log.py:221`; `verify_docs.py:378-379` (replacement text "derived 0.829, fitted 0.837"; expected 0.890 with a `dtol` of 0.002 that absorbs the move). *Why:* the residual is Phase B's headline and neither it nor the fitted constant is asserted; the bullet has been self-contradictory across two data eras (at `6e40cd8^` the lead was right and the trailer wrong). *Fix:* assert both residuals and the fitted k by importing `compare_log`; sweep; tighten the 20 °C `dtol`.

**M2-2 · Both pinned-MAF populations are misstated wherever the raw-log figure is quoted, and the sentence is unreachable by the checker.** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug
`CLAUDE.md:1310`, `REFERENCES.md:317` ("573 … 7 of the 10 raw logs; 517 across 5"), `handoff.md:335`, `build_dataset.py:221`, `verify_docs.py:711-712`, `presentation/index.html:957, 1932, 3056, 4038, 4153`. Measured: 603 across 7 of 10 raw logs; 547 across 6 after the warm filter (both stale by drive10's 30 pins). *Fix:* sweep and add a `NUM pinned samples` pattern with a per-drive guard.

**M2-3 · The enrichment population is quoted as 1055 rows in fifteen places while the checker computes 1341 (1446 unfiltered), and the independent-readings / standard-error argument built on it (39 / ±0.17) is stale (67 / ±0.12).** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug (H4 incomplete)
`CLAUDE.md:569-575, 1028`, `README.md:389`, `REFERENCES.md:293`, `CHECKPOINT.md:250, 417`, `engine_env.py:42, 129, 163, 166`, `handoff.md:285`, `build_dataset.py:429`, `verify_docs.py:317, 777`; also `CLAUDE.md:580` argues with "−0.56 and −0.49" and `README.md:387-388` with "+0.23" (retracted at `CLAUDE.md:582`). *Fix:* replace with the computed figures (state the λ-window filter), re-derive the effective n and the standard error, assert the row count.

**M2-4 · `AUDIT_FIXES.md` contradicts itself on the residual and its "what the scripts print now" table quotes two-generations-old premise figures.** CONFIRMED (verifier: REPRODUCED, keep) · Confirmed bug
`AUDIT_FIXES.md:25` (1.3 %) against `:305` (1.4 %), `:21` (256.5 at 801 °C), `:11` (2.2 points). Both residual rows were last touched by the same commit (`6e40cd8`). *Fix:* correct `:25`, `:21`, `:11`; do **not** add the whole file to `TRACKED_DOCS` (it is in `RETIRED_EXEMPT` for a reason) — split the live table into its own tracked file.

**M2-5 · `results/README.md` gives a regeneration time wrong by five times, points at caveats in `CLAUDE.md` that do not exist, and never names the plant.** CONFIRMED · Confirmed bug
`results/README.md:12` ("~15 min"; measured 76 min), `:19` (+11.7 as "THE FIRST MEASURED PREVIEW ADVANTAGE"), `:24` ("Read the caveats in `CLAUDE.md`"; CLAUDE.md carries none and its current-state row still says nothing has been trained, `CLAUDE.md:70, 227`). *Fix:* one provenance line (commit `1df41a2`, six-speed, +7.5 on HEAD), the real time, and a pointer to `CHECKPOINT.md:873`.

**M2-6 · Two tracked documents give the refuted account of why the real gearbox runs hotter.** CONFIRMED · Confirmed bug
`SESSION_REPORT_2026-09-19.md:294-298` ("invented six-speed sat in 6th at 2416. Higher rpm, more exhaust flow") against `engine_env.py:866-880` and the Part 1 grid (invented box 5th at 2913 rpm; ZF 7th at 2706, *lower* rpm, more load per cycle); the other branch's docstring gives a third figure (2.312). *Fix:* correct in place with a dated note; retire "2416 rpm" and "sat in top (2.312)".

**M2-7 · `verify_docs.py` coverage defects beyond C2-2 and H2-6.** CONFIRMED · Confirmed bug
(a) the "total minutes" pattern anchors on `6|7|8|six|seven|eight` drives and matches none of CLAUDE.md's five live 295.0 mentions (`verify_docs.py:645-649`); (b) `presentation/index.html` is in the figure scan but HTML defeats the prose patterns — 8 of 25 figures reach it and six live figures on it are wrong ("8 drives · 22 operating points" `:2677`, "295.0 minutes, 8 drives, 6 of them carrying" `:3971`, "22 steady … 30 and 74 kPa" `:3015, :4601`, 517 against 547 `:4038 / :3056`, "−0.56 … −0.49 … −0.47" `:2981`, "p99 9.8°" `:3847`, which CLAUDE.md marks unquotable); (c) `logs/CHANNEL_SET_FINAL.md`, `app/alerts.py`, `app/reader.py` contribute zero hits — `alerts.py` was added to guard a figure (+1.9 %) its only pattern cannot match in prose; (d) `app/*.py` are figure-scanned but retired-unscanned (`:557`, non-recursive glob); (e) all document drifts collapse to "1 of 38 checks failed" (`:609`); (f) six `RETIRED` replacement strings are stale (`:355, 362, 364, 371, 376, 378, 388`) and the comment at `:665-667` still says "23, stable in 8 orders"; (g) `CHECKPOINT.md:639` quotes a stale checker total ("All 33 checks pass, 228 figure mentions"). *Fix:* per (a)–(g): add `9|10|nine|ten`; strip tags before scanning; a prose pattern for the boosted gap and a per-file hit count in the output; recursive `**/*.py`; print the drift count; sweep the replacement strings; retire `All \d+ checks pass` outside `RETIRED-OK`.

**M2-8 · `presentation/README.md` and `plan.html` contradict the scripts they cite.** CONFIRMED · Confirmed bug
`presentation/README.md:25` ("the log now holds sixteen"; eighteen), `:67-68` ("the constraint does not bind … 812 °C" inside a `RETIRED-OK: section`), `:128` ("13 thermal"; the suite pins 15); `presentation/plan.html:1437-1442` (reward gate −0.00438 / −0.28044 → today −0.00038 / −0.90349; "Live app tests 36 / 36" → 59 of 59; "Phase C cost 4.6 h × 10" citing `handoff.md`, which retracts 4.6 h; "+3.0 %" citing mistake 13, which says +1.9 %; "16.5 → 18.0 → 26.0" is a retired pattern). *Fix:* regenerate the card from a run or delete it; move the live sentence out of the exempt section.

**M2-9 · Five seeds per arm is exactly the floor at which the planned comparison can reach p < 0.05, and no statistic, test or threshold is pre-registered.** CONFIRMED · Potential risk
`results/README.md:19`, `evaluate.py:65-88` (the twenty episodes vary the preference weights only; every hand-written policy has IQR 0.0). Paired sign test, n = 5: smallest one-sided p = 1/32 = 0.031, reachable only if all five pairs agree; n = 4 cannot reach 0.05. *Fix:* Part 5 "Statistical power" — commit `results/PREREGISTRATION.md` before seed 1; pilot three paired seeds and size n from the paired standard deviation.

**M2-10 · The incoming `NEXT_CHAT_PROMPT.md` tells the next session that ten agents are in `runs/`; this machine holds two six-speed agents that `train.py --seed 0` would resume into and rewrite.** CONFIRMED · Potential risk
`NEXT_CHAT_PROMPT.md` (other branch, arrives on merge with no conflict), `train.py:127-135`, `CHECKPOINT.md:1093` (the warning exists, for the two, not the ten). *Fix:* do not take the file, or rewrite its steps 1–3 in the merge commit; move `runs/*_seed0` aside now (they are irreplaceable and already superseded).

**M2-11 · `CHECKPOINT.md` carries three stale statements about its own verification.** CONFIRMED · Confirmed bug
`CHECKPOINT.md:974` ("Ghassan's ten were … without `evaluate.py`" — false since `7f6c7f1`, 21:42 the same day), `:639` (stale checker total), `:74, 354, 413, 732` ("23 points" beside "295.0 min, 10 drives" — self-refuting, since drive10 is what took 23 → 26), `:54, 642` ("46 of 46"). *Fix:* correct in the next checkpoint entry rather than editing history; retire "23 points".

**M2-12 · `app/alerts.py`'s validity gate stops 0.94 kPa below the span it cites and calls 26 points 22.** CONFIRMED (agent-executed) · Potential risk
`app/alerts.py:224-227` (`VALID_MAP_HI = 74.0`; data 74.94; comment "22 steady operating points"), `:467`. The project's own rule: an `app/` threshold changes only for a measurement written beside it, and the measurement written beside this one matches neither the constant nor the data. *Fix:* 75.0 (or the measured 74.94) and 26.

**M2-13 · `origin/JMF-new-plan` is fully merged but its pointer still selects the pre-lock experiment with mistake 17 live, and nothing says so.** CONFIRMED · Potential risk
`origin/JMF-new-plan:engine_env.py:653` (`v_kmh=110.0`), `:262-265` (six-speed, `gear_for(self, v_mps)` with no load term). *Fix:* delete or fast-forward the branch; one line in CLAUDE.md's layout section if it must stay.

### LOW

**L2-1 · `CLAUDE.md:1495` leads a limitations bullet with "Eight drives, six with usable samples" and corrects itself four lines later; `CLAUDE.md:1140` cross-references "the 22 steady points" the file no longer contains.** CONFIRMED · Confirmed bug. *Fix:* "Ten drives, seven with usable samples, six carrying operating points."

**L2-2 · `verify_docs.py:207` upgrades a paragraph exemption to a whole section on the substring "section" anywhere in the marker's first 24 characters; 22 section-mode markers exist.** CONFIRMED · Potential risk. *Fix:* require the exact `: section` token and warn on anything else.

**L2-3 · The working-tree English abstract drops the hedge the script asks for ("26 steady points"), puts the battery plant in the present tense ("A battery plant tests transfer"; `battery.py` does not exist), and no `DOC/` file names the university in either language; the untracked PDF is one revision behind the `.docx`.** CONFIRMED · Potential risk. `DOC/Abstract_EN.docx` paragraph 22; `ABSTRACT.md:26, 44, 78`; `DOC/Abstract_EN.pdf`. *Fix:* "quasi-steady" or "steady in road and engine speed"; future tense; decide the cover-page name once; re-export the PDF from the final `.docx`.

**L2-4 · `new_drive.py:146` prints "validated span is 30-74 kPa" as live script output; the shipped span is 30.4–74.9 kPa and every document says 30–75.** CONFIRMED (read; the constant values) · Maintainability issue. *(An earlier draft of this entry also objected to `MAF_CEILING_KGH` = 1019.9 against 1020.0 in `app/alerts.py`; the Part 4b agent showed both select the identical sample set on every drive, so that clause is withdrawn.)* *Fix:* read the span from `data/master_points.csv`.

**L2-5 · Training episodes contain 720 s of climb and evaluation episodes 540 s (grade steps at t = 180 s; `train.py` 900 s, `evaluate.py` 720 s), on top of the dt mismatch CLAUDE.md already admits.** CONFIRMED · Potential risk. `engine_env.py:834`, `train.py:82`, `evaluate.py:61`. Not a defect on its own; it is one more axis on which the scored episode differs from the trained one and it is stated nowhere. *Fix:* one shared `DURATION`, or state it beside the dt paragraph.

### NITPICK

**N2-1 · `results/README.md` says the policies are "3 MB each"; the zips are 3.29 MB. `CLAUDE.md:167-171` says `app.test_replay` "49 of 49" without saying that `--full` (the pre-release form the conventions require) prints 59 of 59.** Style preference.

**N2-2 · `CHECKPOINT.md:443` is prose that a naive scan reads as a `RETIRED-OK` marker.** Style preference.

## Document claims not supported by code

Consolidated from Parts 4c, 5 and 7. "Script prints today" is the value on HEAD in this session.

| document | claim | script prints today | finding |
|---|---|---|---|
| `DOC/Abstract_EN.docx` @HEAD, `DOC/Abstract_AR.docx` @HEAD, `DOC/Abstract_Simplified.docx` @HEAD, `ABSTRACT.md:12, 28, 82, 128` | 175.5 min · nine drives · 22 points · 30–74 kPa | 295.0 · ten · 26 · 30–75 (`build_dataset.py`, `compare_log.py`) | H2-1 |
| all four abstracts | "re-evaluating the identical trained policy with its preview channel disabled" | `evaluate.py` scores a *second* trained agent; the identity design is the one C3 voided | H2-1 |
| `DOC/Abstract_EN.docx` (working tree), `DOC/Abstract_EN.pdf` | "26 steady points" | `compare_log.py`: steady in road and engine speed only; 5 of 26 hold load within 25 % | L2-3 |
| all four abstracts | the battery plant "tests" the criterion (present tense) | `battery.py` does not exist | L2-3 |
| `CONTROL_SCOPE.md:56` | "The zero action reproduces the baseline ECU exactly" | `neutral_action()` = trims 0, fan 1.0, pump 1.0; the zero vector is spark −2°, λ −0.045, boost −12.5 kPa, fan 0.5, pump 0.65 | H2-8 |
| `CONTROL_SCOPE.md:195-197` | "Nothing has been trained … Phase D has not started" | `runs/` holds two agents; `results/phase_d_seed0.txt` exists | H2-8 |
| `CONTROL_SCOPE.md:140` | app "validated by replay against our own nine drives" | `app/test_replay.py` replays `pull01` and (with `--full`) `7475b5d7` | H2-8 |
| `CONTROL_SCOPE.md:71` | "all 656 channels … all of them readable" | `logs/CHANNEL_CENSUS.md`: 338 all-zero | H2-8 |
| `CONTROL_SCOPE.md:69, 153-154, 170, 183, 204-206` | 175.5 / nine / 22 / 30–74 as "what is safe to quote today" | 295.0 / ten / 26 / 30–75 | H2-1 |
| `presentation/plan.html:868, 1429-1430` | "value today, printed by check_premise.py": 829.2 · 548.6 · 437.6 · 548.6; 33.8 % · 47.2 % · 13.4 pts | 959.8 · 679.0 · 637.4 · 679.0; 29.3 % · 33.6 %; −0.4 pts over current-grade | C2-3 |
| `presentation/plan.html:873, 1434` | "175.5 min · 9 · 22 · 30–74 kPa · build_dataset.py" | 295.0 · 10 · 26 · 30–75 | H2-1 |
| `presentation/plan.html:1437-1442` | neutral −0.00438 / starver −0.28044; "36 / 36"; "4.6 h × 10"; "+3.0 %"; "16.5 → 18.0 → 26.0" | −0.00038 / −0.90349; 49 of 49 (59 with `--full`); ~45 min × 10; +1.9 %; H2 table void | M2-8 |
| `presentation/index.html` (≈100 lines) | 829.2 / 548.6 / 437.6 / 13.4 / 33.8 % / 47.2 % / 879 °C / 128 °C oil as live figures; "8 drives · 22 operating points"; 517 across five drives; −0.56 / −0.49 / −0.47; p99 9.8° | void (C1/C2/C3); 10 · 26; 547 across six; −0.47 / −0.41 / −0.44; p99 under re-derivation | C2-3, M2-7 |
| `presentation/data.js` | `"damage":829.2,"peak_turb":879.4,"peak_oil":128.1`; blinded trace = reactive trace | `dump_traces.py` on HEAD: 959.8 / 884.0 / 109.9; no shipped script packs `data.js` | C2-3 |
| `presentation/README.md:25, 67-68, 128` | sixteen mistakes; "the baseline peaks at 812 °C … does not bind"; 13 thermal alerts | eighteen; 884 °C, binds by 34 K; 15 | M2-8 |
| `CLAUDE.md:143-147`, `README.md:96-110`, `handoff.md:59-78, 133-135` | `check_premise.py` prints 294.2 at 812 °C and "the constraint does not bind" | 959.8 at 884 °C; binds by 34 K | H2-4 |
| `CLAUDE.md:70`, `CLAUDE.md:227` | Phase C "next … nothing has been trained yet"; the trained ablation "has not been run" | two agents trained 18 Sep; one-seed ablation run on a since-replaced plant | M2-5 |
| `CLAUDE.md:106-108`, `CHECKPOINT.md:626-630` | manifest **9** drives; **6** carrying samples | 10; 7 | H2-7 |
| `CLAUDE.md:1388` | derived residual 1.3 % | 1.4 % | M2-1 |
| `CLAUDE.md:69, 1390`, `handoff.md:30, 138`, `README.md:269`, `CHECKPOINT.md:48, 415`, `validation_table.md:144, 157, 176`, `compare_log.py:221` | fitted k 0.837; 20 °C reference 0.890; "6.3 % separation" | 0.839; 0.891; 6.2 % | M2-1 |
| `CLAUDE.md:1310`, `REFERENCES.md:317`, `handoff.md:335`, `build_dataset.py:221` | 573 pinned across 7 of 10 raw logs; 517 across 5 after the warm filter | 603 across 7 of 10; 547 across 6 | M2-2 |
| `CLAUDE.md:569-575` and 14 other places | 1055 rows above 180 kPa; ~39 independent air-mass readings; SE ±0.17 | 1341 (1446 unfiltered); 67; ±0.12 (`verify_docs.py` note line) | M2-3 |
| `CLAUDE.md:1664`, `CHECKPOINT.md:657` | 13 thermal / 0 mismatch / 19 novel on `7475b5d7` | 15 / 0 / 19 (`app/test_replay --full`) | H2-4 |
| `handoff.md:136` | neutral scores −0.00888 | −0.00038 (inside the band either way) | H2-4 |
| `results/README.md:12` | `evaluate.py …` "~15 min" | 76 min 11 s | M2-5 |
| `results/README.md:19-24`, `results/phase_d_seed0.txt:19` | +11.7 "THE FIRST MEASURED PREVIEW ADVANTAGE" / "This is the project's result"; "Read the caveats in `CLAUDE.md`" | +7.5 on HEAD with the same agents; CLAUDE.md carries no caveat | C2-1, M2-5 |
| `CHECKPOINT.md:201-211` | "use the fixed-limit H2 table: 16.5 → 18.0 → 26.0" | void per `CLAUDE.md:1913-1917`; `generality_test.py` not re-run on the ZF | H2-6 |
| `CHECKPOINT.md:974` | Ghassan's ten runs scored "without `evaluate.py`" | `results/phase_d_seed0_110kmh.txt` on the other branch, produced by `evaluate.py` | M2-11 |
| `CHECKPOINT.md:74, 354, 413, 732` | "23 points" beside "295.0 min, 10 drives" | 26 | M2-11 |
| `SESSION_REPORT_2026-09-19.md:294-298` | invented six-speed "sat in 6th at 2416 … higher rpm" | 5th at 2913 rpm; the ZF is the *lower*-rpm box | M2-6 |
| `DOC/SESSION_REPORT_2026-09-18.md:343` | "no two places can say different things" about the scenario | `generality_test.py` runs 520 s at dt 2.0 with its own cost function | H2-5 |
| `validation_table.md:142-143, 160, 210, 387, 459` | 22 / 23 points | 26 | H2-12 |
| `AUDIT_FIXES.md:11, 21, 25` | "2.2 points"; "256.5 at 801 °C"; "1.3 % derived" | −0.4 over current-grade; 959.8 at 884 °C; 1.4 % | M2-4 |
| `team/jad.md:102` | "the figure is 175.5 over nine" | 295.0 over ten | H2-1 |
| `app/alerts.py:224-227` | "30–75 kPa is the span of the 22 steady operating points" / `VALID_MAP_HI = 74.0` | 26 points; 30.42–74.94 kPa | M2-12 |
| `new_drive.py:146` | "validated span is 30-74 kPa" (printed) | 30–75 | L2-4 |
| `presentation/meeting-update-2026-09-20/index.html` (untracked, user-created 20 Sep) | 884 °C, +34 K, 295.0 / 292.0 min, 0.206 %, 890.6 °C as a model value, ZF 8HP51, 2706 rpm | all match HEAD; the 340 Nm figure has no script that prints it | none — noted for completeness |

## Part 4b — code review of the unreviewed surface (agent-executed; verdicts as marked)

The code-review agent ran after the verification stage had been killed by the account limit, so
its findings carry its own pasted command output and the orchestrator's re-run where stated.
Its probe scripts are in the session scratchpad, outside the tree.

**What it verified as fine (one line each, with the probe):** the simulation does not clamp at
six gears (`_upshift_speeds()` yields seven boundaries, a 50 → 160 km/h sweep uses gears 1–8);
the ZF ratios and 3.150 final drive match `REFERENCES.md` §2b; on the ZF box nothing in
115–125 km/h over-asks (115 → 7th, 2394 rpm, 324.7 Nm; worst in 7th is 370.4 Nm at 155 km/h,
under the 375 Nm ceiling) and all three team scenarios clear it (12 %/130 → 340.2 Nm; 12 %/150 →
363.9; 16 %/110 → 328.8); no gear oscillation on the locked scenario (gear 7 throughout the
climb, 8 changes all in the launch ramp); no observation channel saturates at ±10; `w` is read
live in `step()` and `_obs()` (nothing caches it); blinding zeroes only the four preview slots
and obs 13 (current grade) stays live, matching training; an observation-space mismatch would
crash SB3's `predict`, not go silent; AUDIT M1's flow-dependent ceiling is applied (4314 calls
per episode, 110.6–211.1 kPa, always under `MAP_CEIL_KPA`); L14 is fixed (`iat_b` from
`thermal_base`); `check_premise` carries no second neutral; `new_drive.py` writes nothing; the
merge `27e720c` is a clean union (the only non-comment delta against the ZF parent is
`v_kmh 110 → 130`); `fit_envelope.py`'s printed bins match CLAUDE.md's table exactly; the
`MAF_CEILING_KGH` 1019.9 / 1020.0 pair selects the identical sample set on every drive, so the
second clause of L2-4 above is withdrawn.

### Additional findings from Part 4b

**H2-13 · The twenty "fixed episodes" are one physical rollout scored with twenty weight vectors; the seed does no physical work, so the IQR and "worst" columns are not robustness statistics.** CONFIRMED (the orchestrator's re-run shows IQR 0.0 and worst = median on every hand-written row over twenty seeds) · Confirmed bug — disclosed as a limitation at `CHECKPOINT.md:879-881` and `DOC/SESSION_REPORT_2026-09-18.md:534-538`, not in `evaluate.py`'s docstring or in `results/`
`evaluate.py:65-107, 118-121`; `engine_env.py:532, 677, 696-697` (`self.rng` draws `w` and nothing else).
*Why:* the docstring sells "twenty (seed, weights) pairs … the interquartile range says how much the policy varies"; for the agents the IQR measures sensitivity to the preference vector and nothing else, and Chapter 4 will print that column as spread. *Fix:* make the seed do physical work (per-episode ambient, grade amplitude, start speed, or a small sensor-noise term drawn from `self.rng`), or relabel the columns "spread over the preference front" and say in Chapter 4 that the scenario is one deterministic rollout.

**H2-14 · The uncalibrated knock-damage term is 7–12 % of the episode damage, all of it in five transient steps (four in the standing-start launch, one at the 0 → 12 % grade discontinuity), and it — not the tracking loop — is 94 % of the dt dependence CLAUDE.md attributes to `_track_torque`.** CONFIRMED (orchestrator re-run: dt 1.0 → turbine 862.26 / oil 28.16 / knock 69.33 = 959.75; dt 0.2 → 858.87 / 28.16 / 13.85 = 900.88; the same five knock steps at t = 1, 7, 8, 10 and 181 s) · Confirmed bug (extends H5 and M16)
`engine_env.py:505-512` (`40·max(0, KI − 0.85)²`), `:810` (`e["damage"] += d_a·dt`), `:834` (grade is a step at t = 180 s, no ramp).
*What the agent measured (baseline, dt 1.0 vs 0.2):* total 959.75 → 900.88; turbine term 862.26 → 858.87 (−0.4 %); oil 28.16 → 28.16; **knock 69.33 → 13.85** — a one-step spike of 66.3 damage/s at t = 181 s (KI 2.14, turbine damage rate 0.000 at that instant) charged for 1.0 s at dt 1.0 and 0.2 s at dt 0.2. Per policy the knock share is 7.2 % (baseline), 10.2 % (reactive), 12.2 % (current-grade); removing it moves the headline cuts 29.3 → 31.5 % and 34.0 → 37.6 %. *Why:* CLAUDE.md says of exactly this term "Do not quote a knock damage term as calibrated" (corr −0.149 with the car's own retard), and a trained agent holds spark and λ trims that can suppress those five steps and book up to ~7–12 points of "damage cut" that is model-internal and unrelated to preview. It also re-diagnoses the open dt question: none of the three remedies CLAUDE.md offers (train at 1.0 / score at 0.2 / declare it) addresses a one-step-wide spike. *Fix:* report the damage integral split into its three terms in `episode_summary` and in every Phase D table; ramp the grade over 10–20 s instead of stepping it; re-state the dt paragraph as "the knock spike is one step wide"; consider excluding the launch ramp from the scored window.

**M2-14 · `fit_envelope.py` fits a different functional form from the one `plant.py` ships and prints an RMS its docstring calls comparable to the published ones.** PLAUSIBLE (agent-executed) · Confirmed bug (M5/M6 — the file written to close them does not)
`fit_envelope.py:48-67, 107-111`. It fits `PR = 1 + A·m^B` (unbounded) and prints `A = 4.6641, B = 0.7963, RMS = 0.2077`; `plant.py` ships `PR = 1 + A·m/(1 + B·m)` (saturating, `14.5023 / 6.4019`). Evaluated on the script's own bins the shipped form gives RMS 0.1352 (= `validation_table.md`'s 0.135) and a refit gives 0.1275 (= `plant.py`'s 0.129). At 0.35 kg/s the printed form gives PR 3.02 against the shipped 2.57 and rises without bound. *Fix:* fit the saturating form (linear in `m/(PR−1)`), print the shipped constants beside the refit, and state that 0.135 and 0.129 differ only by refit-versus-evaluate on the same bins.

**M2-15 · `fit_envelope.py`'s "independent readings" column counts a derived quantity, and in the four top bins the p95 is the maximum.** PLAUSIBLE (agent-executed) · Confirmed bug (H4 — the column written to expose H4 under-reports it)
`fit_envelope.py:81-86`. `fresh = (corr_flow.diff() != 0).sum()` ticks when any of three forward-filled channels is polled; counted on the binding channel (`air_gps`) the top bins hold **2, 2, 3, 3** readings, not 5, 5, 4, 5, and each has only three distinct pressure-ratio values, so p95 = max in every one (the docstring's "not the maximum, so one decode glitch cannot define the envelope" is absent exactly where it matters); the 0.225 bin comes from a single drive. CLAUDE.md's "PR 2.52 … is four measurements" is three. *Fix:* import `build_dataset.fresh_readings` (a third copy of the definition exists here), count on `air_gps`, print both counts and a "p95 == max" flag, correct CLAUDE.md to three.

**M2-16 · A 50 000-step run is eleven episodes, i.e. eleven preference-weight draws, scored on twenty; and `learning_starts = 100` against a grade that begins at step 900.** PLAUSIBLE (agent-read; episode counts confirmed by the orchestrator's `curve.csv` line counts) · Potential risk
`train.py:70-73, 116`; `evaluate.py:65-86`. Both shipped agents are the run `train.py`'s own docstring labels "C1: the first bad run", and the agents' non-zero IQRs (9.6, 31.8) are sensitivity to weight vectors they saw eleven of; the first ~800 gradient updates of every run see flat-cruise transitions only. *Fix:* do not report an ablation off two 50k runs; either the 300k runs the docstring prescribes, or freeze `w` for the ablation pair; state the episode count beside every figure.

**L2-6 · `boost_ceiling_kpa` is called with the charge temperature, which its own docstring forbids.** PLAUSIBLE (agent-executed) · Confirmed bug (M1, with the wrong argument)
`engine_env.py:630-631` passes `iat_k` (post-intercooler) where `plant.boost_ceiling_kpa` documents "t_inlet_k IS THE COMPRESSOR INLET — ambient air … passing the downstream temperature inflates corrected flow and raises the ceiling by about 10 %". Measured inflation here 1.17 kPa (0.63 %), because the charge temperature lands near ambient on this scenario; it grows with block temperature. *Fix:* pass `c["t_amb"]` (and `p_baro`).

**L2-7 · `new_drive.py` scores three of the four things its docstring says it scores, cannot see a logger gap, and prints the wrong validated span.** PLAUSIBLE (agent-executed on `fb988991`) · Confirmed bug
`new_drive.py:26-31, 216-218` (item 4, the empty 0.33–0.36 kg/s compressor bin, has no code; the verdict says "on N of the four things"); `:183-205` (60 s windows by wall-clock span only — mistake 8's gap rule is absent, so `fb988991`, the drive known to contribute zero points, is reported with "4 steady windows" and no warning); `:46, :146` (`VALID_HI = 74.0`; the shipped span is 30.4–74.9 → "30–75 kPa"). *Fix:* implement or delete item 4; add the four-median-interval gap test; read the span from `data/master_points.csv`.

**L2-8 · `BaselineECU`'s knock-retard attack is per step while its restore is per second.** PLAUSIBLE (agent-executed: max retard 3.20° at dt 1.0, 3.00° at dt 0.2) · Confirmed bug (M16 family, in the baseline)
`engine_env.py:254-257` (`+ 3.0` with no `dt`; `− 0.35·dt`). *Fix:* `+ 3.0·dt` with a named constant; add the loop to the dt inventory.

**L2-9 · The gear ladder has no hysteresis, and the `SHIFT_RPM_MAX` guard fails open above ~158 km/h on a 12 % grade.** PLAUSIBLE (agent-executed) · Potential risk (mistake 17's residue)
`engine_env.py:386-421`. Torque demand steps 25–49 Nm (29 %) across the 7 → 8 boundary at 123.4 km/h on flat and 4 % roads; at 16 % / 180 km/h the loop keeps an over-asked gear at 400 Nm against the 375 Nm ceiling. Harmless on the three locked scenarios; live on any varying-speed cycle. *Fix:* a small hysteresis band and a docstring line naming where the guard is inactive; do not touch `SHIFT_LOAD`.

**L2-10 · `evaluate.py` decides "blind" by substring of the path.** CONFIRMED (read) · Potential risk
`evaluate.py:137` — a sighted run under any path containing "blind" is scored with `use_preview=False`, silently zeroing its preview channels; nothing cross-checks the run's own configuration because none is stored. *Fix:* read the flag from the manifest of C2-1, or an explicit `--blind` argument.

**L2-11 · `_map_for`'s feed-forward is dead after the first step of an episode, so `boost_trim`'s positive half is inert.** PLAUSIBLE (agent-executed: neutral 959.75 vs +15 kPa trim 959.56 damage; −40 kPa trim 363.75 with `torque_viol` 89.8) · Maintainability issue
`engine_env.py:572-587`. `state.get("map", ff)` uses the feed-forward only when `state["map"]` is absent; from step 2 the trim acts only as a cap. One of the agent's five actions is one-sided and the docstring does not say so. *Fix:* say so, or apply `ff` as a per-step target bias.

**L2-12 · CLAUDE.md's "115–125 km/h still over-ask at 364–375 Nm at 2137 rpm" is the six-speed figure; on the ZF box nothing in that band over-asks.** PLAUSIBLE (agent-executed) · Maintainability issue
CLAUDE.md mistake 17, "A KNOWN LIMIT OF THE FIX". The limitation (a flat ceiling on an rpm-dependent quantity) is real; its stated band and numbers are void. *Fix:* re-derive on the ZF box or mark the paragraph `RETIRED-OK` with the six-speed label.

**L2-13 · `train.py` resume does not pass the seed to `SAC.load`, and the curve written after a mid-run resume holds only post-resume episodes.** CONFIRMED (the curve half is the orchestrator's H2-3 test) · Confirmed bug (H6, second half)
`train.py:135, 157-161`. *Fix:* `seed=a.seed` on load; append to `curve.csv`.

**N2-3 · `evaluate.py`'s "baseline ECU" row is the neutral-action agent path (959.75), not the environment's own `damage_base` (964.07); every "cuts median damage" percentage uses the smaller denominator (worth 0.1–0.3 points).** PLAUSIBLE · Style/accuracy. *Fix:* say which it is, or report both.

**N2-4 · Two dead parameters and redundant observation channels: `uncertainty_beta` multiplies a term that is identically zero (`_evaluate` hard-codes `unc = 0.0`); `engine_model`'s surrogate contract does not match `plant.predict`'s keys (would raise `KeyError`; no caller passes it); obs 2 (`tps`) is a monotone rescaling of obs 1, and obs 9–11 are constant on every episode of the locked scenario; `agent_policy(use_preview=)` is never used.** PLAUSIBLE · Maintainability issue. `engine_env.py:525, 531, 548-563, 651, 799`; `evaluate.py:110`.

## Confidence ledger

**Fifty new findings.** By label:

| label | count | ids |
|---|---|---|
| Confirmed bug | 30 | C2-1, C2-2, C2-3, H2-1, H2-2, H2-3, H2-4, H2-5, H2-6, H2-7, H2-8, H2-12, H2-13, H2-14, M2-1, M2-2, M2-3, M2-4, M2-5, M2-6, M2-7, M2-8, M2-11, M2-14, M2-15, L2-1, L2-6, L2-7, L2-8, L2-13 |
| Highly likely bug | 0 | — |
| Potential risk | 12 | H2-9, H2-10, M2-9, M2-10, M2-12, M2-13, M2-16, L2-2, L2-3, L2-5, L2-9, L2-10 |
| Maintainability issue | 5 | H2-11, L2-4, L2-11, L2-12, N2-4 |
| Style preference | 3 | N2-1, N2-2, N2-3 |

By verdict: **34 CONFIRMED** — reproduced by the orchestrator's own execution in this session
and/or by an independent verifier agent, none refuted — and **16 PLAUSIBLE** — a single agent's
pasted command output that no second process re-ran: H2-6, M2-7 (parts b–g), M2-8, M2-12,
M2-14, M2-15, M2-16, L2-2, L2-6, L2-7, L2-8, L2-9, L2-11, L2-12, N2-3, N2-4. Nothing was
dropped or refuted; the two severity adjustments the verifiers proposed ("lower" on C2-3 for
`index.html` because `presentation/README.md` discloses it, and on the ABSTRACT/CONTROL_SCOPE
staleness because the working-tree English abstract is already corrected) are recorded in the
entries and did not change the ranking.

**What the orchestrator ran itself** (outputs quoted in Parts 1–7): `evaluate.py` with both
trained agents on HEAD (76 min); single-episode baselines on three exported trees at 110 and
130 km/h; `check_premise.py`, `test_reward.py`, `validate.py`, `compare_log.py`, `check_map.py`,
`fit_envelope.py`, `verify_docs.py` (with and without `PYTHONUTF8`), `app.test_replay` (fast and
`--full`); `build_dataset.py` twice into scratch in two input orders; 16 drift injections into a
`git archive` copy; the M16 dt sweep (two policies × three steps); the knock-term decomposition
at two steps; a baseline-ECU instrumentation probe; `train.py` resume on a scratch copy of a
finished run; `dump_traces.py` in a scratch tree; a merge simulation in a throwaway clone; the
AST defaults sweep on four branches; SB3 checkpoint metadata and `_last_obs` decoding; `.docx`
and PDF text extraction; the `EPISODES` reproduction.

**Verification coverage, honestly.** The plan was one reproduce-and-refute agent per
CRITICAL/HIGH/MEDIUM finding. Two full workflow runs on the default model were killed by the
account's usage limit with nothing returned; the third, on Opus, completed five of nine audit
parts and **nine** verifier agents (all REPRODUCED, none refuted) before the limit closed again.
Parts 1, 2a, 2b, 3 and 4b therefore rest on the orchestrator's own execution (1, 2a, 2b, 3) and on
one agent's execution (4b). Every number in this report that was not run by the orchestrator is
marked PLAUSIBLE above.

**Could not run or verify, and why:**

- Whether the 12 % / 130 km/h decision predates the first training run by more than the 26 s
  between the run's `start_time` and the lock commit: the run demonstrably used the new code
  (130 km/h, load-aware 5th gear at 2913 rpm), but git records nothing about an uncommitted
  working tree. Supported in substance, unprovable to the second.
- "Decided by the team", "confirmed by the team" (compression ratio), whether `badcloor` is
  Ghassan Alrefaei and `JMF` is Jad Felemban's second address, and whether five people work on
  the project: each rests on one line written by one identity; nothing in git can settle them.
- Ghassan's ten 110 km/h training runs: not in this repository (`runs/` is gitignored and holds
  only the two 18 September agents).
- `generality_test.py`'s H2 table on HEAD: two time-boxed runs (15 min) completed H1 only, under
  CPU contention from concurrent agents; the H1 rows are quoted in H2-5, the H2 rows are not
  measured on this tree.
- Whether the dt handicap is symmetric between the sighted and blinded agents, and whether a
  trained agent exploits the five transient knock steps of H2-14: both need training or a
  per-step policy trace through `evaluate.py`; neither was run.
- `validation_table.md` §D's bin centres (0.289, 0.303) against `fit_envelope.py`'s (0.285,
  0.315): the RMS reconciliation in M2-14 holds under the saturating form; the binning offset was
  not chased.
- `new_drive.py` against a high-flow drive: its per-row inversion loop did not finish in the time
  allotted; L2-7 rests on `fb988991` and on reading.
- `DOC/Project_Proposal_5.pptx`, `DOC/Novelty_Statement.pdf`, `DOC/Roadmap_Two_Plants.pdf`,
  `DOC/Slide_By_Slide_Team_Brief.pdf`, `DOC/What_To_Do_In_Order.pdf`, `DOC/Project_Vocabulary.pdf`:
  not parsed (outside the brief's list; `DOCUMENT_STATUS.md` says which carry void numbers).
  The EMF logo in the English abstract's cover page could not be rendered, so whether it names
  the university visually is unknown.
- Whether the deletion of `DOC/Abstract_AR.docx` and `DOC/Abstract_Simplified.docx` in the
  working tree is intentional retirement or an accident: uncommitted, unnoted, only the team can
  say.
- A full reading of the Arabic passages in `presentation/index.html` and `plan.html` to separate
  retrospective narration from live claims: the sampled lines read as live and the pages carry
  zero `RETIRED-OK` markers, but 569 KB of Arabic was not read end to end.
- The "drives behind the fitted calibrations = 8" population in CLAUDE.md's table: nothing in the
  repository records which eight files the enrichment and spark fits used; not recomputable.
- The other branch's "79 134 moving samples, 24–40 % median relative filling" justification for
  elevation in the scenario: cited in `3d4f801`'s docstring, printed by no script on either
  branch; not reproduced.
- `python -m app.test_replay` was run by the orchestrator (49 of 49, and 59 of 59 with `--full`);
  it creates and removes `app/review_log.jsonl` (gitignored) as its own test asserts. One
  workflow agent's import created `presentation/__pycache__/` (gitignored); the orchestrator
  removed it. No other file inside the repository was created or changed by this audit.

**Working tree at the end** (identical to the start plus this report):

```
$ git rev-parse --abbrev-ref HEAD && git rev-parse --short HEAD && git status --short
JMF-2340550-sep17
c59346f
 D DOC/Abstract_AR.docx
 M DOC/Abstract_EN.docx
 D DOC/Abstract_Simplified.docx
?? AUDIT2.md
?? DOC/Abstract_EN.pdf
?? presentation/meeting-update-2026-09-20/
```

(`presentation/meeting-update-2026-09-20/` appeared during the audit, created 20 Sep 17:17 by the
user, not by this session; its figures match HEAD.) No scratch file was left inside the tree; the
scratch directory used is the session scratchpad outside the repository.

## Top 3 fixes

In this order, because each one removes the largest remaining way for a wrong number to reach an
examiner without anyone noticing:

1. **Fingerprint every result and refuse a mismatch (C2-1, H2-3).** `train.py` writes
   `runs/<tag>/meta.json` (engine_env commit, gear ratios, `DTHETA_DEG`, trigger, scenario tuple,
   `dt`, `duration`, `EPISODES` hash, SB3 start time); `evaluate.py` prints the same block from
   the live objects, refuses a model whose `meta.json` differs, and writes the block into the
   result file. Then move `runs/*_seed0` and both result files under `void/` and retrain on the
   ZF plant. Until this exists, no Phase D number can be trusted to belong to the plant it is
   quoted beside, and the one number the project has does not.
2. **Give the guard the figures that decide the project (C2-2, C2-3, H2-6).** A `check_scenario()`
   asserting the scenario defaults, `TURB_PROTECT_K`, the gear ratios, `check_premise`'s baseline
   damage and peak, the app's pinned peak and alert counts, both residuals and the fitted k; one
   shared file list for both scans, extended to `.html` and `presentation/*.js` with tags stripped;
   figure-specific `RETIRED-OK`. The drift table in Part 4a is the acceptance test: every MISSED
   row must become CAUGHT. This is the fix that stops the next twenty findings in this report from
   recurring.
3. **Sweep the handed-in and entry-point documents from a fresh run, in one commit (H2-1, H2-4,
   H2-8).** The four abstracts, `CONTROL_SCOPE.md`, `CLAUDE.md`'s numbers block, `README.md`'s box,
   `handoff.md`'s table, `results/README.md` and `presentation/README.md`, each rewritten from the
   script output captured that day, with the ablation sentence corrected to what `evaluate.py`
   does, the scenario account corrected to what git shows (H2-9), and the retired dataset figures
   added to `RETIRED` with the six stale replacement strings swept. Do it after fix 2 so the
   sweep is checked by the guard rather than by the next audit.

After those: H2-2 (make the tracking loop and the counters per-second, then re-measure the dt
symmetry before scoring any agent at a step it was not trained at), H2-5 (put `p_grade_now` and
the shared scenario into `generality_test.py` before it is run for the thesis), H2-11 (two email
lines and an authorship note), and the merge plan in Part 6.
