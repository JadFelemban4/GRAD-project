# PREREGISTRATION — B58H, the B58 study across H: three arms, 20 seeds per arm, exploratory

**Drafted on 7 November 2026 by the AI agents on `GRA-test`, and brought to rows 148-153 on 14 and 15 November 2026,
BEFORE any agent of the study trained (its check run included) and before any of its scores existed.** Like
`PREREGISTRATION_X1.md` and `_X2.md` before it, this file fixes every rule the result will be read by before there is
a result. It is ORDER step 20 (PR-B) of `docs/build_step_2/ORDER_TO_TRAINING.md`. It copies rows 146 and 147 of
`results/VALIDATION_DECISIONS.md` (section R, D146 `a3cd3a3`) and rows 148-153 with section S's note (D148, `c5890f2`)
item by item, each restated beside the row that fixes it. Rows 148-153 record the decisions Ghassan and Jad agreed
together on 14 November 2026. Row 149 (8) makes the copy rule "PR-B copies rows 146-153, with section S's note, and
adds no choice beyond them", in place of "rows 146 and 147". Row 149 (2) makes the readings of the analysis row text,
so this file adds none of them, and it states the whole analysis in words (section 6). What it adds are the names,
paths and run procedures that row 149 (2) leaves to it; none can move d, Δ, the band, the status or a verdict. Section
12.3 lists them. Where this file and rows 146-153 differ, the rows govern (`docs/build_step_2/INTERFACES.md` sections
17 and 18). Sections R and S as committed are the rows' full text. `VD:N` cites a line of
`results/VALIDATION_DECISIONS.md` as rows 146-147 cite it, at D146; D148's index entry moved every line from `:89` on
by 3 (section S's note). `MD:N` cites `results/ENGINE_THRESHOLDS.md`, unchanged since D146.

> **Status at writing: complete except section 15 (run log) and section 16 (outcome), which are filled in as the study
> runs and after it, and marked so.** Every placeholder of the drafts (a NAME in double braces) was filled at this
> file's own commit, from the committed record named beside it or, for the three no record could fill (AB's commit,
> AB's gates and the anchors' commit), with the rows' words, so
> `git grep -n -E '[{][{]|[}][}]' -- results/PREREGISTRATION_B58H.md` prints nothing. A value that exists only after
> this commit (the check run's printed check, AB's commit, every score) is never a placeholder here: it is recorded in
> section 15 or 16 when the run that prints it has run. **No line above section 15's heading changes after `T*`**: a
> later commit changes only lines below that heading, in sections 15 and 16, an amendment naming F among them (section
> 11), and each later commit's check that it did so is section 14's, recorded in section 15.

> **The commit the check run and the training run from is this file's own commit, `T*`**: the one commit that adds
> `results/PREREGISTRATION_B58H.md`, printed by
> `git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md` (row 146 (6); statement (i) of
> `docs/build_step_2/ROW146_STATEMENTS.md`; X1's precedent, `results/PREREGISTRATION_X1.md:355`). A commit cannot hold
> its own sha, so `T*` is never written in this file. Its parent is Tb's commit, `5d801be` (row 149 (1), (7)). **AB,
> the study's analysis code, is not its parent.** Row 149 moves AB after `T*`: AB is written during training and
> committed before the first scoring command, and section 6 states everything it computes. The one exception to `T*`
> is a check run that shows the recipe broken, where the fix changes no cost file and nothing in `FP.PLANT_CODE` (row
> 148 (3)(a)). This file is then amended, in a dated entry of section 15, to name the commit F that fixes it, and the
> second check run and the training run from F (section 11). A fix that changes a cost file or PLANT_CODE stops the
> study (row 148 (3)(b)).

---

## 0. Who decided what, and what is still open

- **Ghassan's own answers of 6 November 2026** (section R's note of `results/VALIDATION_DECISIONS.md`, where each
  question is quoted as it was asked, Q3 with the three options shown with it):
  - Q1, "Yes, it covers it (Recommended)": his standing instruction of row 133 (2), written for the four-engine test,
    also covers this study, so the agents keep deciding its route for him.
  - Q2, "Sign both (Recommended)": the two statements of `docs/build_step_2/ROW146_STATEMENTS.md` (row 147 (13);
    section 0.1 below).
  - Q3, "20 seeds (Recommended)": n = 20 per arm (row 147 (4); section 4).
  - Q4, "Out of the reward (Recommended)": the training reward without the knock term (row 147 (3); section 4).
- **The decisions of 14 November 2026** (rows 148-153 and section S's note). Ghassan and Jad answered decisions 13
  (B), 14 (B), 7 (A), 8 (B), 9 (B), 3 (C), 4 (B), 10 (A) and 12 (B) together, in one working session with the AI
  agents, each an option of the decision sheet of 14 November with its section "Revised after the audit"
  (`decisions_2026-11-14.md`, on the Desktop, not in the repository). These are their own answers, not recommendations
  adopted under row 133 (2): on 7 they chose A where the revised sheet recommended B, and on 9 B where it recommended
  A. Rows 148-153 record decisions 13, 14, 7, 8, 3 and 12, in that order; decisions 4 B, 9 B and 10 A add no choice
  and take no row, and section S's note records them (below, and section 12.1). The AI agents wrote the questions, the
  options and the recommendations. Each new row's Ghassan cell holds his answer. Each new row's Jad cell reads "not
  filled (row 133 (1))", because decision 9 (B) leaves row 133 (1) in force; Jad agreed every answer of 14 November in
  the same session (the sheet's "Agreed on" cells: "14 Nov 2026, both, in this session"), and that agreement is
  recorded as a fact, in each row's Disclosed sentence and in section S's note, not as his column.
- **Left for later**: decisions 1, 2, 5, 6 and 11 ("the rest well answer later", 14 November, 17:11 AST, from the
  session's record of their messages; section S's note). The sheet sets decision 1's "Decide before" at `T*` (the
  literature review's step 14, its A25 bullet); that deadline is the agents', not an answer, and no row makes `T*`
  wait for it (section S's note). `T*` does not wait for it.
- **The agents' points P1-P13** (section S's note). Some answers of 14 November could not run as worded, or left a
  point open. For each, the agents drafted a reading with a recommended option: P1 CK's length (row 148 (1)); P2 Tc
  (148 (5)); P3 s_p's source (148 (4)); P4 a fix that changes a cost file (148 (3)); P5 what the scoring waits for
  (149 (4)); P6 the order after training and its cut-off (149 (5)); P7 the settling label (150 (ii)); P8 the optimum's
  form (153 (2)); P9 when row 152 (5)'s anchors run; P10 the agents' additions (150 (iii)'s action share, the controls
  on seed 0's agents, 151 (3)'s conditional 850 °C row, one figure per item, 148 (4)'s practice spread, 148 (8)'s
  early record); P11 AB's readings made row text (149 (2)); P12 decision 4 B's and 10 A's sentences without A15's
  derivation and without "upper bound"; P13 the documents. Asked for "all as recommended", or the points he would
  change, Ghassan replied on 15 November 2026 at 01:23 AST: "I do D 148". The agents answered that, under his standing
  approval "approve whatever you recommend" (his words of 31 October, quoted in section L's note), they read that
  reply as all thirteen points as recommended, and asked him to confirm it. At 01:28 AST he replied: "I confirm the
  p1-13". So every point stands as recommended, and no row was changed for one. Section S's note says that Jad was not
  asked about P1-P13, which was true when D148 was written. After D148's push, Ghassan relayed Jad's answer on P1-P13:
  "No objections" (`SESSION_REPORT_2026-11-15_D148.md`, section 11). It decides nothing new: Jad's column is not
  filled (row 133 (1)).
- **Q3 re-confirmed** (decision 9 B; section S's note). On 15 November 2026 at 01:30 AST, after the figures of
  `results/B58H_DESIGN/power_b58.txt` were explained to him in the session, Ghassan alone re-confirmed n = 20, in his
  words, quoted from the session's record of his messages: "I confirm the n= 20". The figures were the power at C_u in
  d's form, 0.167 and 0.139 (`power_b58.txt:7`, rounded as `:26` prints them), and the smallest detectable d,
  11.83-14.30 points (`:22-23`, `:26`). Row 133 (1) is not reopened. The waiver of gate item 6 stays his alone (row
  147 (13)).
- **Every other item** of rows 146-147 is the agents' recommendation adopted under row 133 (2), as his answer Q1
  extends it to this study. That includes the readings of gate items 1 and 5 for this study (row 147 (13)), which are
  not part of the two statements he signed. Jad's column is not filled (row 133 (1)). **The items this file adds
  beyond the rows** (section 12.3) are names, paths and procedures that row 149 (2) leaves to this file, chosen by the
  agents before any score; none can move a result.
- **Disclosed beside the four questions** (section R's note): Q1's "a null result is the expected outcome" is not row
  107 (2)'s words; it is row 147 (7)'s prediction. Q3's "about 15-30 %" has no basis on file: at the gain Q3 named
  (C_u, 2.549-3.222 points) the power is 0.115-0.167 at n = 20 (`results/B58H_DESIGN/power_b58.txt:6-7`) and
  0.139-0.344 over Q3's three n in `evaluate.py`'s form (`:26`, `:29`, `:31`), and 0.231-0.309 at n = 20 is at the
  ceiling C_a, which Q3 did not name (`:4-5`). Until 15 November 2026, nothing on file showed that he had seen the
  computed figures; section S's note records that they were explained to him then, and his words (above). Q3 and its
  options gave no value of a rate-and-window rule for n; row 147 (4) discloses those values as information (section
  4).
- **One holder of row 96's two integers** (row 133, "disclosed in the preregistration and the thesis"): from 31
  October one person, with the AI agents, held both of the integers that made roads_seed. The protection that two
  independent holders give, that neither can compute roads_seed before the push and so nobody can try roads commits
  until one gives a passing set, rests here on one holder. The agents wrote the roads code and generated the integers;
  R0 was pushed before the reveal, and its sha is in the attempts log's start line. From row 133 on, the agents
  answered the rows and signed row 111's statements on Ghassan's instruction (row 133's Disclosed line).
- **Filled at this file's commit** from the records each names: the commits of RV, P, Qa, Q, G, V, Ta, B1, D148, Tc
  and Tb; P's B58 fingerprint; Q's gate outputs; the commit that adds the battery's hills file, its sha_text and its
  hills; B1's attempt and its B2, B4 and L8 records; Tb's backend record (sections 3 and 9). Section 10's grids print
  and D148's figures print are committed in D148, and step 0 of section 14 checks that both still print their
  committed output.
- **Open after `T*`, recorded in section 15 when each run has printed it:** the check run's printed check and its
  record's commit (section 4); the first and last hour of training (row 134 (1)); every crash; AB's commit and its
  gates, each route's commit or "not computed (code)", and HEAD at the first scoring command (section 6.0); row 153
  (2)'s commit or "not computed (code)" (section 9.8); the scores and the analysis (section 16).
- **Open at writing, deciding nothing here:** the time of the one visit to Jad's PC, still to be agreed with Jad
  (`SESSION_REPORT_2026-11-15_D148.md`, section 11).
- `CLAUDE.md`'s brackets on gate items 5 and 6 should say that item 6 is waived for this study (citing
  `ROW146_STATEMENTS.md`) and that this file is item 5 for it. That edit is Ghassan's own (row 133 (4)); this file
  does not make it, and does not depend on it.

### 0.1 The training gate and the rules for a reported experiment, for this study

| item (`CLAUDE.md`) | for this study | source |
|---|---|---|
| gate 1, sub-step the thermal network | landed (`75ca65f`); the fit that derives the thermal constants still steps at 1 s (mistake 25). **Closed for this study by disclosure, not by a refit**, as row 110 closes it for the four-engine test: the refit's effect was measured only on the locked climb (the baseline 848.1 -> 845.6, current-grade +0.01 points, `calibrate_thermal.py:198-200`) and never on decision 34's roads (mistake 17); a refit would make a new B58, against decision 31 | row 147 (13), row 110; the agents' reading under row 133 (2) |
| gate 2, the fingerprint covers `derived_params.json` | closed (`75ca65f`); `derived_sha` is FATAL in schema 4 | row 117; section 3 |
| gate 3, spark trim capped at 0; every result with and without the knock term until drive C | **binds**: `SPARK_TRIM_MAX` = 0 in the plant; every number is reported in both damage readings (section 10) | row 147 (13); CLAUDE.md:71-73 |
| gate 4, ramp every grade change | closed (`75ca65f`); every road of the test and of training ramps over `GRADE_RAMP_S` = 8 s | rows 98, 116 |
| gate 5, a new preregistration before anything trains | **this file is item 5 for this study**: decision 34's roads answer item 5's "D2-style randomised roads plus multi-climb roads" as row 110 reasons (drawn at random from a committed generator and seed, several climbs per road); the blind-arm check runs at both H (Q, section 3.2); damage is reported both ways (section 10); the analysis is stated in words in section 6, and its code is committed after `T*` and before the first scoring command (row 149) | row 147 (13), row 110, row 149; the agents' reading under row 133 (2) |
| gate 6, drive C before training | **waived for this study only**, by statement (ii) of `docs/build_step_2/ROW146_STATEMENTS.md`, signed by Ghassan alone on 6 November 2026 ("Sign both (Recommended)"): the study trains before drive C, and every result is reported with and without the knock term. The gate was agreed by Jad and Ghassan (CLAUDE.md:60); the waiver is signed by Ghassan alone (row 133) | row 147 (13); Q2 |
| rule 1, the preregistration committed before the first training step | `T*` precedes the check run and the training (ORDER steps 20-22) | row 146 (2), (6); row 148 |
| rule 2, train from a clean, pushed commit whose `train.py` and `fingerprint.py` are `main`'s | **amended for this study** by statement (i) of `ROW146_STATEMENTS.md`: training runs from the commit the study's preregistration names, `T*`; rule 2's own "clean, pushed" is kept. `main` is `cf43fbb`; on `GRA-test` the two files differ from `main`'s by 416 and 279 changed lines (MEASURED on 6 November 2026, that file's Disclosed lines) | row 147 (13); Q2 |
| rule 3, every seed and arm on one environment | Jad's PC's CPU, one environment, no ablation declared; `evaluate.py` refuses an agent whose versions, device or machine differ (section 5.2) | row 147 (3); row 143 (5) |
| rule 4, one set of versions, pinned by `requirements-lock.txt` | Python 3.13.2, torch 2.14.0+cpu, the lock's environment (B1 recorded them on the device, `results/benchmarks/B1_bench_b58.attempt1.txt:10-13`); each run records its versions in `meta.json` and `config.json` | row 135 (1); decision 32 |
| rule 5, one experiment only if every FATAL field, the protocol and the environment agree | schema 4's FATAL fields (section 3); the blinded agent pairs with both sighted agents of its seed by row 117's rule (every FATAL field equal but `preview_h_s`, H on the sighted, null on the blinded) | rows 117, 143 (5) |

The two statements are not restated here: `docs/build_step_2/ROW146_STATEMENTS.md`, committed with rows 146-147 (D146)
before any agent of the study trained, is their text, with its Disclosed lines. Two of those lines matter for reading
every result: statement (i) keeps rule 2's "clean, pushed"; and under statement (ii) the untested knock model still
enters the primary, no-knock reading through the B58's E8 band (κ 3.4226), which is not part of what Ghassan signed
(row 147 (13)). Row 111's two statements hold for the four-engine test only
(`docs/build_step_2/ROW111_STATEMENTS.md:5-7`), and the B58's post-P plant_sha is named beside 865f8e7b7e5c2dbe in
section 3, as row 127 (6) asks.

## 1. The question

| | question | how it is answered |
|---|---|---|
| **d** (primary, exploratory) | On decision 34's twenty roads, does a B58 agent that sees the grade H seconds ahead take less turbine and oil damage than its identically trained blinded twin, at H = 0.5 τ and at H = 1.5 τ? | d per ratio and seed, the paired one-sided t-test under row 113 (2)'s graph (section 6) |
| **Δ** (exploratory, declared now so that the study's own question is not answered post hoc, VD:391) | Does the sighted agents' cut differ between H = 0.5 τ and H = 1.5 τ? | Δ = cut(sighted r = 1.5) − cut(sighted r = 0.5) per seed, with its two-sided interval and sign test (section 6.4) |
| descriptive | What did each arm do to fuel and torque delivery; how do the agents fare on decision 12's three checks; where do the hand-written savings sit on row 102's curve; how do the agents compare with current-grade, did they settle, do they use the road ahead; how hot does the modelled housing get; what do the c_turb re-scores show; what do the tuned hand-written strategies and a λ-only optimum say there was to learn? | sections 9 and 10, each deciding nothing |

**The whole study is exploratory, and nothing in it is a test of the H/τ criterion** (row 107 (2) and (6); row 147
(1); section Q.5). One plant gives one point per H and no collapse. On one plant H/τ and H differ by the constant
factor τ, so nothing here can prefer one to the other. No collapse on H/τ and no test of H/τ against H is claimed or
computed. A null d at either H is the expected outcome (row 147 (7), section 8), and it says nothing against the
criterion.

## 2. Why this study, and what it is NOT

- **Run 2 dropped all three EPA engines** (section Q of `results/VALIDATION_DECISIONS.md`; `results/README.md`, its
  Run 2 section). L1, the only held-out test of the housing model the four engines share, read off on all three (κ
  1.7168, 1.8714 and 3.7328); the Mazda was dropped by E4b and L1 off, the Honda and the Ford by L1 and E8 off, under
  version 6 and under version 5 alike (Q.2, Q.4). So the four-engine test of decision 24 does not run, and the failed
  validations are reported as results (MD:1611-1612; row 107 (2)). Row 107 (2) then orders this study: "a B58 study
  across H ... as a declared exploratory study, at r = 0.5 and r = 1.5 and on row 102's curve ... preregistered as its
  own experiment before it trains ... never called a test of the criterion".
- **`results/PREREGISTRATION_4E.md` is never written** (row 146 (3); INTERFACES 10.1). Tb's `results/EPA_BACKEND.json`
  (`5d801be`) holds n null and in_test ['b58'], with no schedule drop, so Tb wrote no drop line: it is the formal
  record that the four-engine test does not run, and Run 2's failed validations are the result (row 146 (3), (9);
  `SESSION_REPORT_2026-11-15_D148.md`, section 12). That null n is not this study's n (row 147 (4); the record's
  `notes.4`).
- **A new experiment, never compared with X1 or X2 as one** (decision 31; CLAUDE.md rule 5). It differs from X1 in the
  plant code (P), the scored roads, the training road, the recipe, the steps, the horizons, the reward, the device and
  the seed count, all at once (this study's side: sections 3-5 and row 147 (1)-(5); X1's:
  `results/PREREGISTRATION_X1.md`), so anything said about it against X1, X2 or any earlier set is descriptive and
  attributes nothing to any single change. X1's and X2's spreads of a paired d are used here for planning (section 8)
  and, by row 148 (4), X2's for the context's s_p (section 6.7).
- **This is the seventh preregistered look at the preview question** (Phase D, D2, C4, 29 September, X1, X2, this
  study; X2's count, `results/PREREGISTRATION_X2.md` limit 13), on different plants, roads and designs. Every p here
  is unadjusted across them; the thesis reports them together, one line each, never pooled.

## 3. The plant, pinned

The B58 in the GR Supra: X1's plant `cf43fbb`, frozen for this study (decision 31; row 147 (1)). It was drawn on,
measured on and hand-scored at plant_sha 865f8e7b7e5c2dbe until the plant commit P (ORDER step 14). P's code edits (H
as a parameter, schema 4, `trainable()` from the records, the knock option) move the plant_sha while the B58 stays
identical at its defaults: its engine_sha unchanged and the B58 identity certificate L1-L7 re-run (rows 94, 117 and
127 (6)). Every agent of this study trains and is scored on P's plant.

| fingerprint (schema 4, `fingerprint.plant_fingerprint`; FATAL unless marked) | value | from |
|---|---|---|
| `plant_sha` (the code of the plant files, docstrings and comments stripped) | **`36655cab94800e30`** at P, beside 865f8e7b7e5c2dbe, the frozen plant's before P | P's commit message, its MEASURED plant_sha line (`8b5366f`); the same on Qa (`results/ENGINE_GATES/b58/provenance.txt:10`) and at B1 on Jad's PC (`results/B58H_DESIGN/d148_figures.txt:7`) |
| `derived_sha` (`data/derived_params.json`) | `326c0835548975e2`, unchanged by P, the value X1's preregistration and `CHECKPOINT.md` record for this plant | P's commit message (`8b5366f`); on Qa `results/ENGINE_GATES/b58/provenance.txt:11`; at B1, Tb's record, `inputs.benchmarks.b58.plant` |
| `engine` / `engine_sha` | b58 / `023f5589215ee68e`, unchanged, as row 147 (1) has it; RV's re-verification refuses a moved engine_sha (row 140 (2)) | P's commit message (`8b5366f`); on Qa `provenance.txt:12-13`; at B1, Tb's record, `inputs.benchmarks.b58.plant` |
| `transmission` | the Supra's stepped gearbox (kind 'stepped', its gears and final drive) | row 138 (2) |
| `train_backend`, `score_backend`, `backend_contract` | 'cycle' and 'cycle' (row 136: no table is built; MD:1462), with the contract's two sha_text | rows 117, 136, 138 (2); Tb's record, `engines.b58.backend` |
| `scenario`, `episodes_sha` | decision 34's protocol 'd34' (scenario protocol 'decision-34'), its scored set roads.json under redraws.json's 'version 6' reading, read by one function, `fingerprint.d34_roads`; the scenario never holds commit_reveal, roads_seed or a revealed integer | row 138 (2) |
| `preview_h_s` | the sighted arm's H (section 4); null for the blinded arm | row 117 |
| `reward_knock` | false: the reward without the knock term (`--reward-knock out`) | row 147 (3); row 113 (5) |
| `dtheta_deg`, `turb_protect_k`, `oil_protect_k` | the B58's, unchanged | row 138 (2) |

Every run writes this block into its `meta.json` before its first step, and `evaluate.py`'s decision-34 route refuses
an agent whose FATAL fields differ, with no force (section 5.2). From P on, the contract's `engine_env.py` citations
are read at `c842d74` (row 138 (7)).

### 3.1 The records the study stands on

| record | what it holds | commit |
|---|---|---|
| `results/EPA_ROADS/roads.json` | decision 34's roads as drawn (R1), each road's arrays and dt, the B58's τ and row 102's `H_table`, the ceilings and their companions, row 102's grids, the practice set (row 96) | roads_sha = its sha_text; committed once, never edited (row 97) |
| `results/EPA_ROADS/redraws.json` | R4's two readings: 'version 6' (the B58 alone gating; no slot fails, so decision 34's twenty stand as drawn) and 'version 5 (every engine gating)', reported and never scored | R4 `34cca5b` (row 146 (1)) |
| `results/EPA_ROADS/reverify.json` | RV's re-verification on P's candidate tree: every number of roads.json the draw's code computed, both readings of redraws.json among them, recomputed and bit-equal (row 140 (1)); P is pushed only once that check printed EQUAL and `adopt` wrote the record (row 140 (3)) | carried by P, `8b5366f`; RV is `a443607` |
| `results/B58_IDENTITY.md` and `.json` | the B58 identity certificate at P, L1-L7 (row 138 (4)) | `8b5366f` |
| `results/EPA_TIGHTENINGS.json` | E8's κ for the B58, 3.4226 with the roads (`E8.b58_u_val_kappa.with_roads.kappa`; 3.4431 on the locked climb alone) | R3b `4da4a31` (row 107 (4); Q.2) |
| `results/EPA_VALIDATION/summary.json` | Run 2's drops; each EPA engine's `kappa.L1` (1.7168, 1.8714, 3.7328) | F4 `9140941` (section Q) |
| `results/conditions_b58h_dt1/conditions_grades.json` | the battery's seven hills, fixed on this plant before any agent trains (section 9.3) | Q, `ce452df`, the commit that adds it |
| `results/benchmarks/B1_bench_b58.attempt1.json` and `.txt`, `results/benchmarks/B0_0329456.json`, `results/benchmarks/B1_device/`, `results/B58_IDENTITY/L8_device/` | B1's one attempt, its B0 record, B2, B4 and L8 on Jad's PC (section 3.2) | B1, `891e29a`, from git_head `0329456` (Ta) |
| `results/B58H_DESIGN/d148_figures.py.txt` and `d148_figures.txt` | D148's figures: B1's rate and every time and count rows 148-153 and section S's note quote | D148, `c5890f2` |
| `results/B58H_DESIGN/grids_b58.py.txt` and `grids_b58.txt` | the print of row 102's curve and grids from roads.json `report.grids`, with decision 13's count (section 10) | D148, `c5890f2` (row 149 (1), point P13; moved from AB) |
| `results/B58H_DESIGN/hw_opt/` | row 153 (1)'s tuned hand-written λ strategies, with their control record (section 9.8) | D148, `c5890f2` |
| `results/EPA_BACKEND.json` | n null, in_test ['b58'], `engines.b58.backend` 'cycle'; B1's rate in `inputs.benchmarks.b58` | Tb, `5d801be` |

### 3.2 The gates, as they stood when this file was committed

Every value in this table is quoted from the committed record named, at this file's commit. Row 146 (4) maps every
outcome of each gate to its consequence, and the route reached this file only because none of them stopped it.

| gate | result | record |
|---|---|---|
| ORDER step 13, `test_defect_route` (no commit of its own) | passed with no commit of its own, in RV's K gate: `Ran 5 tests in 56.251s OK`, exit 0. The same K gate's one failure, `test_epa_rows` (failures=1), was RV's known row 120 N1, which G fixed (G's gate: `test_epa_rows: Ran 54 tests in 270.072s; OK`) | RV's commit message, `a443607`; G's, `a60dcae` |
| RV's control, `roads_reverify.py check --skip-companions` on RV's clean tree | "VERDICT: EQUAL (partial: not adoptable)", exit 0, 31407 s: every section computed with 0 values differing, both readings of redraws.json among them; not run: ['report'] | RV's commit message, `a443607` |
| P's roads check, `roads_reverify.py check --jobs 14` on P's candidate tree, then `adopt` | "VERDICT: EQUAL; 0 differences in 17 sections", exit 0, 63677 s; after every run of the certificate, the check result `"verdict":"EQUAL" "partial":false "mode":"check"` with 17 sections printed of 17 | P's commit message, `8b5366f` |
| P's B58 certificate, L1-L7 | "Verdict: BIT-IDENTICAL at every level run on this machine (pending: L8 on the training device at ORDER step 18, and app.test_results on P itself after the commit)": 185 of 190 recorded checks PASS, 5 FAIL, each of the 5 re-checked by a later PASS record; the five were defects of the certificate kit's driver, not of P. L8 is B1's (below) | `results/B58_IDENTITY.md` at `8b5366f`; P's commit message |
| Q, `test_reward.py --engine b58 --train-road four_engine --roads results/EPA_ROADS/roads.json --reward-knock out`: the band and notch sweep | exit 0, 1185 s: band grade 8.80 %, the notches at 8.85 % and 14.00 % PASS, every check PASS; "All checks pass on b58. The reward is safe to train this engine against." | `results/ENGINE_GATES/b58/test_reward_four_engine_share_off_knock_out.txt:13`, `:17-26`, `:31` at `ce452df` (Qa's code, `742239a`); `provenance.txt:38` |
| Q, the blind-arm check at the record's two H (`engine_gate.horizons`, never typed) | PASS at H = 23.6675 s and at H = 71.0026 s: on road 0 slot 0 the grades differ from step 197; the blinded arm first differs at 197 at both H, the sighted at 174 and at 126 | the same file, `:25-26` |
| Q, each road's share of steps below the torque floor (row 116) | for information, not judged: 0.00 % (worst road 0.00 %) for the neutral policy on the 10 training roads and on decision 34's 20 roads, and 0.00 % in both tables below | the same file, `:28-29`; `check_roads_four_engine_share_off_knock_out.txt:70`, `check_roads_four_engine_share_on_knock_out.txt:70` |
| Q, `check_roads.py` with the same options, the share off, then with `--roads-record results/EPA_ROADS/roads.json`, the share on | share off: exit 0, 1273 s, "PASS -- every road is one the baseline can drive." (baseline past 850 C on 18 of 60 roads); share on: exit 0, 1221 s, the same PASS (0 of 60 roads) | `check_roads_four_engine_share_off_knock_out.txt:67`, `:72`; `check_roads_four_engine_share_on_knock_out.txt:67`, `:72`; `provenance.txt:44`, `:51` |
| G, Run 2's figures registered with `verify_docs.py`; `drift_test.py` | `drift_test.py`: "22 of 22 drifts CAUGHT", its control "All 170 checks pass"; `verify_docs.py` before the commit: "All 170 checks pass (1157 figure mentions scanned in the documents)." | G's commit message, `a60dcae` |
| V, the scoring protocol's gates, the before/after run of X1's two checkers among them | `evaluate.py`'s phase-d and d2 routes on X1's two agents, before (G) and after (V's candidate): "NO DIFFERENCE: the two reports are identical line for line"; `logged_check.py` and `conditions_test.py` on X1's set: "identical on G and V: 10 JSON outputs field by field, 914 record JSON files ('commit' left out) and 914 records by their arrays"; `test_scoring_protocol` Ran 40 tests, OK; `test_b58h_descriptive` Ran 16 tests, OK; `test_roads_reverify` Ran 61 tests, OK; `app.test_results` and `app.test_agents` failing only the tests of RV's base list; `verify_docs.py`: "All 170 checks pass (1157 figure mentions scanned in the documents)." | V's commit message, `cadac38` |
| Ta, `test_epa_backend` (its live test of this file skipped until this file is committed; the class's synthetic tests run from Ta on) | `test_epa_backend.py`: Ran 66 tests, OK (skipped=3: Preregistration, PreregistrationB58H's live test and LiveRecord); `benchmark_training.py --selftest` exit 0; `test_engine_threading.py` alone: Ran 33 tests, OK (skipped=6); `epa_backend.cost_files`: 51 paths; `verify_docs.py`: "All 170 checks pass (1157 figure mentions scanned in the documents)." | Ta's commit message, `0329456` |
| B1, every attempt of the B58's benchmark by row 135's protocol on Jad's PC (12 runs, 3000 steps, 2 repeats, `--reward-knock out`, the share on), each with Ta's classification | one attempt, `B1_bench_b58.attempt1`, started 14 November 2026 at 19:53:38 AST from git_head `0329456` with git_dirty false (`d148_figures.txt:7`); as Ta's code classifies it in Tb's record: steady, loaded (repeat 2's flag), fits at 12, determinism identical (1800 steps, 0 differences), a clean tree; no superseded attempt, no crash, no fallback | `results/benchmarks/B1_bench_b58.attempt1.json` and `.txt`, `results/benchmarks/B0_0329456.json`, at B1 `891e29a`, git_head `0329456`; Tb's record, `inputs.benchmarks.b58`, `inputs.superseded`, `inputs.crashes`, `inputs.fallback` |
| B1's rate, lower_min of the (cpu, 12) row (row 135 (3)): recorded, deciding nothing, since n is fixed (row 147 (4)) | 107.46 steps/s in all at 12 runs at once, repeat 1's lower bound: repeat 1 read 107.46-108.32 with 2.6 % CPU before it; repeat 2 read 110.77-111.89 with 6.5 % before it and is flagged loaded, a flag that decides nothing (row 135 (4)) | `d148_figures.txt:6-10`; `B1_bench_b58.attempt1.txt:46`; Tb's record, `inputs.benchmarks.b58.lower_min` |
| B2, `check_training_device.py --compare` of Jad's PC against the laptop's identity file made at Ta's commit in a clean clone: recorded, deciding nothing (decision 32); a NOT IDENTICAL is disclosed here | "VERDICT: NOT IDENTICAL (100 differences)", between this laptop (Windows-11-10.0.26200-SP0) and the device (Windows-11-10.0.26300-SP0); disclosed in section 12.2, item 30 | `results/benchmarks/B1_device/B2_compare.txt:1`, `:23`; `B2_identity_device.json` |
| B4, `test_epa_plants` on the device: run and recorded, and for this study it decides nothing, since it re-makes only the dumps of the three dropped EPA plants (row 146 (6)) | "Ran 7 tests in 205.508s", "OK" | `results/benchmarks/B1_device/B4_test_epa_plants.txt:12-14` |
| L8, the B58 identity certificate's training level on the device | PASS: all 11 runs exit 0; the three pairs and `ctl_none` IDENTICAL, both relative-step controls DIFFERENT, and the two one-ulp controls, printed and not judged, IDENTICAL. The line "L8 VERDICT: PASS" itself went to a file B1 did not commit; Jad's report quotes it | `results/B58_IDENTITY/L8_device/_status.txt:1-11`, `_verdicts.txt:1-8`; `SESSION_REPORT_2026-11-14_B1-visit.md`, section 2, step 6 |
| D148, the rows of 14 November and their prints | `d148_figures.py.txt` and `grids_b58.py.txt` re-run: byte-identical to the committed prints; the cost files at HEAD and at `0329456` (51 paths), `results/ENGINE_THRESHOLDS.*`, `engine_specs`, `logs`, `data` and `validation_table.md`: `git diff --quiet 0329456`, exit 0; `test_contract_pinned.py` Ran 19 tests, OK; `verify_docs.py`: "All 170 checks pass (1153 figure mentions scanned in the documents)" | D148's commit message, `c5890f2` |
| Tc, the check line in `epa_backend.B58H_LINES` (row 148 (5)) | `test_epa_backend`: Ran 67 tests in 67.631s, OK (skipped=3); `test_engine_threading`, alone: Ran 33 tests in 19.417s, OK (skipped=6); `git diff --quiet 891e29a HEAD -- epa_backend.py`: exit 0, run with HEAD at D148 before Tc's commit ("D148 did not touch it"; Tc's own diff is the scope disclosed beside row 148 (5) in section 4); `epa_backend.py compute` at `891e29a` and at a scratch commit of Tc's tree: 118 keys each, differing only in the module's own sha_text and `provenance.commit`; the 51 cost files unchanged since `891e29a`; `verify_docs.py`: "All 170 checks pass (1153 figure mentions scanned in the documents)" | Tc's commit message, `31dc7ad` |
| Tb, `epa_backend.py write`, then `check`, `test_trainable`, `test_engine_threading` | `write` at Tc on a clean tree: "n = None; in the test: ['b58']; total None s of W = 864000 s; slack None s"; before the commit, the record rebuilt byte for byte in a scratch clone, the cost files unchanged, `verify_docs.py` "All 170 checks pass (1153 figure mentions scanned in the documents)". After the commit: `epa_backend.py check` printed `[]`, exit 0; `test_trainable`: Ran 23 tests in 43.527s, OK; `test_engine_threading` alone: Ran 33 tests in 22.460s, OK (skipped=6); `test_epa_backend`: Ran 67 tests in 83.446s, OK (skipped=1) | `results/EPA_BACKEND.json` at `5d801be`; Tb's commit message; `SESSION_REPORT_2026-11-15_D148.md`, section 13 |
| PR-B's own gate (section 14, step 0) | run on the staged tree and at `T*`; recorded in section 15 by a commit after `T*` | this file's run log |

## 4. The design

| | |
|---|---|
| plant | the B58 alone (section 3), on the exact cycle ('cycle') for training and scoring (row 136; Tb's record) |
| arms | three per seed (row 117; row 147 (2)): **blinded** (`blind_seed<S>`: the four preview inputs are 0 whatever H is), **sighted at r = 0.5** (`sighted_r0.5_seed<S>`) and **sighted at r = 1.5** (`sighted_r1.5_seed<S>`), paired by seed. One blinded arm serves both ratios: row 135 (5) measured the blinded arm bit for bit at every H, so there is no fourth arm and no command carries `--blind-per-h` |
| H and the ratios | H = r·τ, with τ the B58's frozen time constant as roads.json records it (47.3351 s, `results/B58H_DESIGN/d148_figures.txt:19`; row 102) and r = 0.5 and 1.5: H = 23.6675 s and 71.0026 s (`:19`), the preview samples at steps (1, 3, 11, 23) and (4, 11, 35, 71) (`:73-74`; row 102). H is read from roads.json's `H_table` through `four_engine_roads.horizon_s` and never typed (row 147 (2); INTERFACES 17, 13). No agent trains at any other ratio: `four_engine_roads.horizon_s` refuses a ratio the record does not hold (`four_engine_roads.py:483-485` at `a3cd3a3`) |
| where the ratios come from | row 102: "the same on every engine, fixed now, and never chosen again: not after the draw, a redraw or Run 2" (VD:426); an amendment of decision 27 for the four-engine test, which took both horizons "from the test roads' preview ceiling". r = 1.5 came from the ceiling probe's grid families before any test road existed, and r = 0.5 from no ceiling at all. **Disclosed, load-bearing:** "r = 1.5 sits at the knee of a gap effect, set by the design's gaps rather than by τ" (row 102), so how d varies with H on these roads is tied to the gap design, not only to τ (row 147 (5)) |
| n | **20 per arm, 60 runs**: Ghassan's answer Q3 (row 147 (4)), re-confirmed by him on 15 November 2026 (section 0) |
| seeds | 0-19 for the training (row 147 (4)); 2000-2004 for the check run (row 148 (1)). `--road four_engine` refuses the seeds 1000-1019, 3000-3009 and 4000-4009 (the frozen twenty's, D2's practice set's and row 96's practice roads'; row 130 (4)) |
| training road | row 116's generator, which reads no vehicle (`--road four_engine`; rows 116, 130): a new road every 900 s episode, ambient 25-45 °C, a speed target that changes within 60-150 km/h following row 130 (1)'s notional car, grades 0-18 % with every change ramped, and c_turb's scale drawn log-uniform on ×0.75-1.333 at each reset (decision 12's first safeguard). Decision 12's knock threshold and damage scale are not drawn (rows 113 (5), 116; section 12) |
| recipe | decision 29's (`--recipe29`; rows 118, 130): 450 000 steps, 500 episodes; SAC at `train.py`'s learning rate 3e-4 held for two thirds and falling linearly to 0 over the last third; decision 29's fixed 10 % share of the scored kind of road, every tenth episode, from row 101's generator under `default_rng([roads_seed, 0x7A, seed])`, the share on through `--roads-record`; the reported policy the float64 mean of the deterministic actions of the five checkpoints in the last 50 000 steps (row 130 (3)), at 410 000-450 000 steps (`d148_figures.txt:57`); a replay buffer of the run's own length. Every setting is written into each run's `config.json` |
| reward | **without the knock term** (`--reward-knock out`; FATAL `reward_knock` false): Ghassan's answer Q4, which adopts row 113 (5)'s choice for this study. The B58's knock model is untested until drive C (CLAUDE.md:71-73) |
| device and environment | Jad's PC, `DESKTOP-VF1MO3H` (an AMD Ryzen 5 9600X, 6 cores and 12 logical, 31.2 GB of RAM; its RTX 5070 unused, since torch there is a CPU build: `results/benchmarks/B1_bench_b58.attempt1.txt:2-8`, `:11`, `:15-16`): the CPU, torch 2.14.0+cpu, the lock's environment, Python 3.13.2, 12 runs at once (row 135 (1)-(2); step 3's merge, MEASURED on 2 November at `b2151af`: "RECOMMENDATION: CPU with 12 runs at once"). The clone is the one B1 ran in, `C:\Users\admin\grad_device\GRAD-project-device`, and the interpreter step 3's lock venv, `C:\Users\admin\grad-venv-lock-3.13.2` (INTERFACES section 18's 3; `results/B58_IDENTITY/L8_device/provenance.txt:1`, `:5`). B1's environment is the one the check run and the training keep (section 12.2, item 30). Every seed and arm trains on that one environment, with no ablation declared (CLAUDE.md rules 3 and 5; row 143 (5)) |
| folders | `runs/b58h_dt1` (training) and `runs/b58h_check_dt1` (the check run), in that clone on Jad's PC, gitignored; neither is in `train.CLOSED` (INTERFACES 18, 11). Each run's folder holds its `meta.json` (the schema-4 block), `config.json`, checkpoints and `final.zip`; the launcher writes each run's log beside it, `log_<tag>.txt`. They come back to this laptop zipped with a SHA256SUMS file, every file included, the checkpoints that section 9.5 (ii) reads among them (row 146 (6); INTERFACES 18, 3) |
| crash rule | X1's (INTERFACES 11; row 147 (3)): a dead run is re-trained from step 0 under `--no-resume`, never resumed; re-running the same command moves the dead folder aside to `<tag>.crashed<N>`, kept, and trains that seed again (`train_all.py:67-73`, `:113-129`). A machine restart counts as a crash (row 135 (4)(a); `results/PREREGISTRATION_X1.md:123`). The same rule holds for the check run; a second crash of the same check run reads as a failed check (row 148 (3)) |
| commit | `T*`, this file's own commit, checked out clean on Jad's PC (`git status --porcelain` prints nothing, and `git rev-parse HEAD` is the sha Ghassan sends: section 14's guard), in the visit that trains; the check run runs from `T*` first and the training follows in the same visit once it prints CHECK RUN: OK (statement (i); rows 146 (6), 148 (1)-(3)). After a failed check run only, the commit F that section 15's amendment names (section 11) |
| time | at B1's rate, MEASURED: 107.46 steps/s in all at 12 runs at once, 8.9550 steps/s a run (`d148_figures.txt:6`, `:41`), in place of step 3's 106.19 (`:11`). The check run comes first: about 1.55 h, ten runs of 50 000 steps in one wave (`:53-54`; ASSUMED there: the per-run rate at 10 at once equals B1's at 12). The training: 5 waves of 13.96 h, 69.79 h (`:42-44`), in place of step 3's 70.63 h (`:46`); a sixth wave, after a crash or a restart, adds up to 13.96 h (`:48`). W runs from 10 November 2026 00:00 AST to 20 November 00:00 AST (row 134 (1); `:14`); the latest start that ends inside W is 17 November 2026 02:12 AST, and 16 November 16:12 AST if the primary scoring, the folders' transfer and their reading (10 h, ASSUMED, `:35`) end inside W too (`:140-141`; row 146 (7)); step 3's 17 November 01:22 and 16 November 15:22 AST are superseded (`:149`). B1's printed "x 4 engines: 11.6 days" multiplies by `benchmark_training.py`'s ENGINES = 4 and is not this schedule (`B1_bench_b58.attempt1.txt:47`; `d148_figures.txt:45`). W is the plan, never a stop rule: training is never cut at W's end, any hour past it is disclosed, and the first and last hour of training are recorded (row 134 (1)) |

**n = 20 per arm, seeds 0-19** (row 147 (4)). This amends, for this study only, decision 30's "seeds per arm fixed
before training from the measured many-run rate and the time window (target at least 20)" (VD:196) and row 114's rule
(VD:453, with row 134 (1)'s W). It was written before B1 and knowing step 3's rate. n is fixed now and never
recomputed: not from B1's rate (B1 decides nothing), not from the hour training starts, and not after any result. No
seed is added (decision 30). X1's and X2's distributions were seen before this choice (decision 30's own note).
Disclosed, as information only and deciding nothing (`results/B58H_DESIGN/budget.txt`; row 147 (4)): row 114's rule on
the B58 alone would give n = 64 at step 3's rate (16 waves, 226.01 h, `budget.txt:10`; ASSUMED), leaving no room for a
defect cycle or the scoring. A rule "the largest n, in whole waves of 12, that leaves a 3-5-day defect cycle and the
scoring (about 10 h at n = 20, ASSUMED) before W ends (20 November 00:00 AST), at step 3's rate" would give 28-32 with
a 5-day cycle and 40-44 with a 3-day one on the route's machine time (`budget.txt:29-30`), and 24-28 and 36-40 with
P's drafting counted (`:31-32`; ASSUMED). It would give 20 only if the study were ready between 10 November 23:14 and
11 November 15:22 AST, which is that rule inverted, not an estimate of readiness (`:33`). The n values and the
readiness window of these two sentences are at step 3's rate (`budget.txt:2`), superseded for timing by B1's
(`d148_figures.txt:6`, `:11`); they are kept as row 147 (4)'s disclosure and decide nothing. 20 sits below every value
the rule gives on these estimates, and leaves margin for the agents' drafting time and Jad's availability, both
UNKNOWN. What 20 gives up (MEASURED, `results/B58H_DESIGN/power_b58.txt:26-31`): the power at C_u in d's form is 0.167
and 0.139 at n = 20 (spreads 20.51 and 24.78), against 0.219 and 0.177 at n = 32, 0.252 and 0.201 at n = 40, and 0.344
and 0.269 at n = 64; the smallest d detectable with power 0.8 at α is 11.83-14.30 points (2.179-2.633 MEI, `:22-23`)
at 20, 9.22-11.14 at 32, 8.21-9.92 at 40 and 6.44-7.79 at 64. More seeds narrow the intervals; they do not make a
test.

**The check run, CK, in place of the pilot PL-B** (row 148: decision 13 (B); it amends row 112 for this study only;
ORDER step 21). Row 112 had five full-length pairs trained before training, a wave plus 1-2 h of transfer and reading,
15.13-16.13 h at step 3's rate (`results/B58H_DESIGN/budget.txt:25`; `d148_figures.txt:34`), a figure not brought to
B1's rate, since PL-B is not made (row 148). Their spread could change
neither n (row 147 (4)) nor what the analysis prints for one engine (`four_engine_analysis.py:668-669`), and they did
not train the r = 0.5 arm. Their one job that bears on training is checking the recipe's code. CK does that job, in a
ninth of the steps (`d148_figures.txt:52`).

- **What runs.** Row 147 (3)'s pilot command with two values changed, `--steps 50000` and `--out runs/b58h_check_dt1`:
  ten runs, blinded and sighted at r = 1.5, seeds 2000-2004, one wave, on Jad's PC from `T*`, in the visit that
  trains, after the runbook's "Before you start" block (row 148 (1)). It is the check line below.
- **Why 50 000 steps, not "a few thousand".** Decision 13 B said "a few thousand steps". Decision 29's recipe averages
  each run's checkpoints over its last 50 000 steps (`training_recipe.DECISION_29_WINDOW`), and the launcher refuses
  `--recipe29` for any run shorter than that window (`train_all.py:239-243`; `training_recipe.snapshot_steps`,
  `training_recipe.py:77-87`), so 50 000 is the shortest run of the exact command (row 148 (1), point P1). At that
  length the window is the whole run: the five snapshots fall at 10 000-50 000 steps (`d148_figures.txt:56`), and the
  learning rate falls to 0 over the run's last third (`training_recipe.LastThird`; `d148_figures.txt:59`).
- **What is checked**, from its files alone (row 148 (2)), by section 14's check block on Jad's PC. Every run exits 0
  (the launcher prints no FAILED line) and writes `final.zip`. Its `config.json` holds `recipe.learning_rate_at_end`
  0.0 (`train.py:1071`) and `recipe.scored_share.every` equal to `four_engine_roads.SHARE_EVERY`. Its
  `checkpoint_average.json` passes `training_recipe.read_manifest`, which checks each snapshot's sha256, and lists
  exactly the steps `training_recipe.snapshot_steps(50000, DECISION_29_WINDOW)` gives. Its `meta.json` reads
  `git_head` the commit checked out and `git_dirty` false. These are the checks ORDER step 21 named for PL-B ("the
  learning rate reaches 0; the average is taken"), the ones `evaluate.recipe_checks` reads (`evaluate.py:1541-1551`).
  The block reads the ten run folders by their tags (`four_engine_roads.run_tag`) and lists any `<tag>.crashed<N>`
  folder beside them. It prints "CHECK RUN: OK" only when all ten pass.
- **What it does not check.** The spread of d: CK's agents are never loaded, never scored, and give no s_p. The
  r = 0.5 arm's training path: it first runs in the training itself, as row 147 (3) discloses (Q's gate checked its
  environment at both H; section 3.2). A recipe defect that only a full-length run shows: it would first appear in
  training's first wave (row 148 (7)).
- **The outcome** (row 148 (3)). On "CHECK RUN: OK", Jad sends CK's record (row 148 (8); section 14, step 1) and
  starts the training from `T*` in the same visit (ORDER step 22). A crash or a machine restart (row 135 (4)(a))
  follows the training's crash rule (row 147 (3)): the command is run again, the dead run is moved aside to
  `<tag>.crashed<N>`, kept, and trained again from 0. A second crash of the same run reads as a failed check. A failed
  check is a coding defect, by row 112's route read for this study (section 11). Any other outcome stops the step, and
  it is reported (rule 1.11).
- **CK's record** (row 148 (8), point P10). Right after "CHECK RUN: OK", Jad sends, apart from the training's folders
  and with their sha256 lines: each CK run's `config.json`, `meta.json`, `checkpoint_average.json` and
  `log_<tag>.txt`, the launch log and the printed check. The laptop commits them during training in
  `results/B58H_CHECK/`. The whole of `runs/b58h_check_dt1` comes back with the training's folders, zipped with
  SHA256SUMS.
- **Where s_p comes from** (row 148 (4), point P3). `four_engine_analysis.validate_context` needs an s_p (section
  6.7). It is **X2's spread of a paired d in the no-knock reading, 20.56 points over 5 pairs**
  (`results/X2_RESULT.txt:24`). AB's code reads it from that committed file and never types it. pilot_pairs is 5,
  which X2's pairs are and `validate_context` requires (`four_engine_analysis.py:404-406`). Its label: "X2's spread:
  another plant, road and budget; not a pilot of this study". The status it gives is recorded here, before any agent
  of the study trains, as row 103 (4) asks: **exploratory**. The rule reads confirmatory only if s_p ≤ 5.822
  (`results/B58H_DESIGN/power_b58.txt:19`). With one engine the analysis prints exploratory whatever s_p is
  (`four_engine_analysis.py:668-669`). Beside it, deciding nothing: X2's 20.51 with knock
  (`results/X2_RESULT.txt:11`); X1's 24.88 without knock and 24.78 with it, over 23 pairs (`results/X1_RESULT.txt:60`,
  `:29`); and, after training, the training's own spread, the paired d at r = 1.5 of seeds 0-4 on row 96's ten
  practice roads, printed by `evaluate.py --protocol d34 --practice` (`evaluate.pilot_spread`, no knock), labelled
  "the training's own seeds 0-4, not an independent pilot", and scored at section 6.9 (c).
- **Given up** (row 148 (7)): an s_p measured on this study before training; a trial of the transfer and of the
  laptop's practice scoring before training, so that a scoring defect found later is fixed without retraining; and the
  chance to find, before training starts, a recipe defect that only a full-length run shows. The r = 0.5 arm's path
  still first runs in training, as row 147 (3) discloses.

**The commands**, exactly as rows 147 (3) and 148 (1) fix them, each run on Jad's PC from `$REPO` after the runbook's
"Before you start" block as section 14, step 1 gives it, with the launcher's own output kept in that session's `$OUT`.
These are this file's only two commands of that launcher. The pilot line of row 147 (3) is not run for this study and
is not written here (row 148 (9)).

```bash
# CK, the check run (row 148 (1); ORDER step 21): 10 runs, one wave, from T*, in the visit that trains
$PY -B train_all.py --engine b58 --device cpu --road four_engine --dt 1 --third-arm --recipe29 --roads-record results/EPA_ROADS/roads.json --reward-knock out --ratios 1.5 --seeds 2000-2004 --steps 50000 --jobs 12 --no-resume --out runs/b58h_check_dt1 2>&1 | tee "$OUT/b58h_check_launch.txt"

# the training (row 147 (3); ORDER step 22): 60 runs, five waves, every ratio the roads record holds
$PY -B train_all.py --engine b58 --device cpu --road four_engine --dt 1 --third-arm --recipe29 --roads-record results/EPA_ROADS/roads.json --reward-knock out --seeds 0-19 --steps 450000 --jobs 12 --no-resume --out runs/b58h_dt1 2>&1 | tee "$OUT/b58h_training_launch.txt"
```

`test_epa_backend.PreregistrationB58H` (Ta, row 146 (5), as Tc changes it, row 148 (5)), in its live test, reads every
such command of this file and runs each through `train_all.main()` in-process, stopped before any directory or run
exists. Each must carry INTERFACES 10.1's flag list with the values of `epa_backend.PROTOCOL` (device cpu, 12 runs,
the road, dt 1, the roads record, the knock option out), `--engine` at `B58H_ENGINE` (the B58), the three bare flags
of `B58H_ALONE` (`--third-arm`, `--recipe29`, `--no-resume`), never `--blind-per-h`, and `B58H_LINES`' values for its
line. For the training line: seeds 0-19, its folder, no `--ratios`, `--steps` at `epa_backend.PROD_STEPS` (450 000).
For the check line: seeds 2000-2004, ratio 1.5, its folder, `--steps` at `training_recipe.DECISION_29_WINDOW`
(50 000). The test fails if this file is committed and either line is missing or differs. It also fails on any other
command of that launcher in this file: on a fenced line, in a code span in which `--engine` follows its name, or in
bare prose followed by a flag (`epa_backend.b58h_commands`, `b58h_line`). The test runs again at every later gate, so
sections 15 and 16, written after `T*`, refer to "the check line" or "the training line" and never quote one.

**Tc, disclosed beside row 148 (5)** (`SESSION_REPORT_2026-11-15_D148.md`, section 10; ORDER step 18a's row). Row 148
(5), ORDER step 18a's gate and INTERFACES section 18's 2 read "changes only `B58H_LINES`, docstrings and comments".
Outside that wording, Tc also changed two code lines of `epa_backend.py`: `import training_recipe as TR`
(`epa_backend.py:152`), which the check entry's `--steps` reads (`training_recipe.py` was already in the module's
import closure, through `benchmark_training.py:2216`, so the closure's file list does not move), and `b58h_line`'s
refusal text for a line whose `--out` names neither entry (`:1342`), which named the pilot's entry; and, in the test
file, the module-level lines that `PreregistrationB58H` reads (`test_epa_backend.py:227-342`) and the module docstring
(`:55-61`). No other logic changes. For the check line, three refusal texts still cite only row 147 (3) and the sheet
17's 10.1, where its sources are row 148 (1) and the sheet 18's 10.1 (`epa_backend.py:1343`, `:1349`, `:1376`); they
are kept so that no more code changes, and from `T*` on the file is frozen (INTERFACES section 18's 1).

## 5. The test set and the scoring protocol

### 5.1 The test set

- **Decision 34's twenty roads**, R4's version-6 reading of `results/EPA_ROADS/redraws.json` (row 95 (2);
  `fingerprint.d34_roads`), equal to roads.json's twenty (row 146 (1): MEASURED True in
  `results/B58H_DESIGN/r4_counts.txt:3`). Road k is scored with `evaluate.EPISODES[k]`'s seed and preference weights
  (row 101), so every agent is scored on twenty episodes.
- **The design** (row 101): 900 s at dt 1 s, an episode of 899 steps (row 122 (2)); speed from 0 to 130 km/h over the
  first 20 s, then held; 315 K, 101.3 kPa and humidity 0.012 throughout; a flat lead-in of 150-210 s, then climbs of L
  67-85 s at a grade on [10, 12] %, separated by gaps of 50-150 s, every grade change ramped over 8 s; 3 to 5 climbs a
  road, 75 slots in all (row 146 (1)'s 75 final climbs). The accepted grades are not uniform on [10, 12] %: the
  replacement loop replaced every climb that failed C5 on any car, and the Ford fails C5 at 1.9 % at 11.20-11.80 %
  (row 123). The B58's smallest gated C5 margin over the 75 final climbs is 9.30 % (`r4_counts.txt:9`), against 1.9 %
  (row 146 (1)).
- **The roads were fixed before Run 2 and before any agent**, drawn once from a committed generator and a seed made by
  commit and reveal (rows 96, 133), and re-verified bit for bit on P's plant (row 140). With every EPA engine dropped,
  the B58 alone gates version 6, and no slot fails, so decision 34's twenty stand as drawn (row 146 (1)).
- **R4's version-5 reading** (every engine gating at its re-check margin): 58 of the 75 slots fail, on all 20 roads,
  each for "C5 case (1) at 7.102 % on ford_27tt"; 129 redraws and 60 discards; 22 slots stop at the cap of 3, exactly
  the 22 flagged gear-sensitive; 36 pass after a redraw (row 146 (1); `r4_counts.txt:4-8`). That reading is reported,
  never scored, so no d on its set exists (row 95; INTERFACES 8).
- **The locked climb** is no test road here: it is decision 34's declared transfer row only (section 9.2).

### 5.2 The scoring protocol

Scoring runs on this laptop only (row 143 (1)), with V's `evaluate.py --protocol d34` (`cadac38`). It runs from a
commit at which no `.py` file present at `T*` differs from `T*`'s, and no file of `epa_backend.cost_files` differs
from B1's git_head, `0329456` (row 149 (4)). AB, the routes of rows 150-152 and row 153 (2) add files after `T*` and
change none present at `T*` (section 6.0). A change found necessary after a score exists is a coding defect, handled
by section 11's rule for a document already written. The first document is kept and reported. A change to a reading,
the band, the tests or the decision rule, once any score exists, is post hoc, never a defect fix (row 149 (6)).

- **What it checks first, refusing on any failure, with no force:** the roads through `decision34_roads`, which reads
  the current re-verification record through `four_engine_roads.current_reverify` (verdict EQUAL, roads_sha and
  redraws_sha the live ones, its head an ancestor of HEAD, every `plant_sha_now` the live plant_sha) and refuses any
  reading but version 6; each agent's arm and H from its `meta.json` through `evaluate.arm_of`, H checked against r·τ
  of the committed record; one environment across every agent (`config.json`'s versions, device and machine, and
  `meta.json`'s python and numpy; row 143 (5)); the backend record's train_backend; row 117's pairs; each agent's
  decision-34 fingerprint, the blinded side `fingerprint.for_arm(live, sighted=False)`.
- **What it scores:** decision 29's checkpoint average of each agent (`training_recipe.AveragedPolicy`; row 118), and
  the hand-written policies, the baseline ECU among them, on each of the twenty roads at dt 1 s with road k's frozen
  seed and weights. Each road gives the damage in both readings: no_knock, `run_episode`'s `damage_thermal` (the
  turbine and oil terms at the B58's knee, decision 33's 1123 K), the primary; with_knock, its `damage`, beside it.
- **What it writes, once, outside the repository** (`--scores-out`, refused inside it; its own step commits it): the
  scores document, schema `four-engine-scores/1`, the B58 alone, arms blind, sighted_r0.5 and sighted_r1.5, seeds
  0-19, variant null (INTERFACES 17, 12.7), whose provenance names the protocol d34, the reading 'version 6', the
  version-5 reading's slots with `scored` False, the knock option false, roads_sha, `epa_freeze.versions()`, the
  platform, the device 'cpu', the environment, every agent with its checkpoint manifest, the recipe checks, and the
  delivery block of section 9.1. Beside it the text report (`--out`), never named `*_seed*.txt`. And, with
  `--records-out` to a folder outside the repository, the per-step records: float64 t_turb, t_oil and ki for the
  baseline ECU and every agent, road by road and step by step, with dt (`evaluate.write_records`,
  `evaluate.py:1197-1218`). Their index, `<scores>.records.json` (`evaluate.records_index_path`), holds every file's
  sha256 and the scores' sha256, and is committed with the scores. The records themselves are not committed
  (INTERFACES 12.7 and 18's 12.7; `.gitignore:29-38`; row 151 (1)).
- **The practice route** scores, after training, the blinded and r = 1.5 agents of seeds 0-4 on row 96's ten practice
  roads (episode seeds 4000-4009). It writes schema `four-engine-practice/1` and prints their s_p at r = 1.5 (no
  knock, ddof 1, five pairs). That spread is printed beside the context's s_p and decides nothing (row 148 (4)). The
  practice route reads the train_backend 'cycle' from the committed backend record and checks it against every agent's
  `meta.json`.
- **The files** (this file names them; no row does; section 12.3):

| file | written by | committed |
|---|---|---|
| `results/B58H_CHECK/` (each check-run folder's `config.json`, `meta.json`, `checkpoint_average.json`, `log_<tag>.txt`; the launch log; the printed check; `SHA256SUMS`) | Jad's PC, sent right after CHECK RUN: OK (section 14, step 1) | from the laptop, during training (row 148 (8)) |
| `b58h_analysis.py`, `test_b58h_analysis.py`, `b58h_beside.py`, `test_b58h_beside.py` | AB and the routes (section 6.0) | after `T*`, before the first scoring command |
| `results/B58H_DESIGN/cturb_hw/` | row 152 (5)'s hand-written anchors (section 9.7) | after `T*`, before the first scoring command, or "not computed" |
| `b58h_lambda_opt.py`, `test_b58h_lambda_opt.py`, `results/B58H_LAMBDA_OPT/` | row 153 (2) | after `T*`, before the first scoring command, or "not computed (code)" |
| `results/B58H_RESULT/scores_b58h.json`, `scores_b58h.records.json`, `scores_b58h.txt` | the d34 route with `--records-out`, on `runs/b58h_dt1`'s 60 agents (section 14, step 3) | the scores' own commit (the records stay outside) |
| `results/B58H_RESULT/context_b58h.json`, `analysis_b58h.json`, `analysis_b58h.txt` | `b58h_analysis.py context` and `analyse` (section 6.8) | with the analysis |
| `results/B58H_RESULT/b58h_core.json` and `.txt`, `b58h_flat.json`, `b58h_road0.json`, `b58h_settle.json`, `b58h_cturb.json`, each with its printed `.txt` and its figure | `b58h_beside.py` (sections 9.5-9.7) | each when its item ends |
| `results/B58H_RESULT/practice_b58h_s0-4.json` and `.txt` | the practice route (section 5.2) | with item (c) of section 6.9 |
| `results/B58H_RESULT/b58h_locked.json`, `b58h_battery.json`, `b58h_logged.json`, each with its printed `.txt` | `b58h_descriptive.py` (sections 9.2-9.4) | with item (c) of section 6.9 |

The scores file is bound to its context by its sha_text (`thresholds.common.sha_text`, CRLF read as LF), with its raw
sha256 beside it as a record that binds nothing, so a hash quoted later for it (a session report, the thesis) is the
sha_text: the raw sha256 differs between a CRLF and an LF checkout of the same commit.

## 6. The analysis, stated in full before its code exists (rows 147 (5)-(12), 149)

### 6.0 The rule for AB and the routes (row 149 (2)-(4), (6))

- **What AB is.** AB is the study's analysis code: `b58h_analysis.py`, which reads the scores and the committed
  records and writes the analysis, with `test_b58h_analysis.py` (row 147 (12)). It comes with the routes of rows 150
  (i) and (v) and 151, in `b58h_beside.py` and `test_b58h_beside.py` (ORDER step 22a). **The routes** are the code of
  rows 150 (ii)-(iv) and 152, which extends `b58h_beside.py`; row 152 (5)'s anchors, which D148 did not carry; and row
  153 (2)'s `b58h_lambda_opt.py` with `test_b58h_lambda_opt.py` (ORDER step 22b), each in a commit of its own.
- **When.** Each is committed on this laptop after `T*`, while the PC trains, and before the first scoring command.
  The first scoring command is the first command that loads an agent or a checkpoint of this study on any road: the
  d34 route, the practice route, or a route of rows 150-152. **The scoring waits for AB**, and the training does not.
  It waits for no route. A route not committed before the first scoring command is reported "not computed (code)"; no
  code is written for it after that command, and the scoring never waits for it. Section 15 records HEAD at the first
  scoring command, and the routes present there. No score of this study exists while any of this code is written,
  since the check run is never scored (section 4).
- **What it may compute.** AB and the routes compute what this section and sections 9.1 and 9.5-9.8 state, and nothing
  else. For sections 6.1-6.7 every quantity, reading, form and rule is fixed here, and AB makes no choice. Suppose a
  descriptive row (row 147 (11), rows 150-153) needs a detail this file does not fix, such as a figure's layout or a
  search grid. AB's docstring fixes it before any score, as a choice that cannot move d, Δ, the band, the status or
  any verdict, and section 15 records it at that commit. Suppose instead a computation of the primary analysis (row
  147 (5)-(9) and (12)) needs a choice this file does not fix. Then every reading the words allow is printed, none is
  called primary, and section 15 records the gap.
- **Where the code and this file differ, this file governs.** Before the first scoring command the code is fixed.
  After it, the difference is a coding defect, handled by section 11 (row 149 (6)), and this file's reading is the
  result.
- **What the commits after `T*` may touch** (row 149 (3)). `git diff --name-status <T*> HEAD` lists the paths present
  at `T*` only as CHECKPOINT.md, STATE_HISTORY.md, the session report and this file (its section 15), and every other
  path as added, each one row 149 (3) names: AB's and the routes' modules and tests, `b58h_lambda_opt.py` and its
  test, `results/B58H_CHECK/`, `results/B58H_LAMBDA_OPT/`, `results/B58H_DESIGN/cturb_hw/` and a new session report.
  None is in `epa_backend.cost_files` or imported by a hashed module, and no package is added to `.venv`. No `.py`
  file present at `T*` changes, so `evaluate.py`, `b58h_descriptive.py`, `four_engine_analysis.py` and every file of
  `epa_backend.cost_files` stay as at `T*`, and the cost files stay those B1 timed. `T*` here reads the commit
  training ran from: `T*`, or F after an amendment (section 11).
- **Gates of each commit** (section 14, step 2; their output in its message and in section 15): its own tests, each
  computation with a control that fails (mistake 12); `test_four_engine_analysis`; `test_engine_threading`, alone;
  `epa_backend.py check`, run after the commit on a clean tree, since it refuses any changed or untracked `.py` file
  (`epa_backend.py:104-110`); the cost-files diff against B1's git_head; the name-status check above; Ta's live test;
  `verify_docs.py`; push. Each message states that no command on this laptop has loaded an agent or a checkpoint of
  `runs/b58h_dt1` or `runs/b58h_check_dt1`, and whether their folders had arrived. A SHA256SUMS check reads bytes only
  and loads nothing.

### 6.1 d

Per ratio r (0.5 and 1.5) and seed s (0-19), each arm's cut is in **`evaluate.py`'s form**: 100 × (1 − median D /
median D_base) over the twenty roads (`evaluate.median_cut`, `evaluate.py:1091-1094`, `np.median`; the form `main()`
prints at `evaluate.py:533-538` at `a3cd3a3`). D is the agent's damage on road k, and D_base is the baseline ECU's on
the same road, both as the scores document holds them. **d(r, s) = cut(sighted at r, s) − cut(blinded, s)**, paired by
seed (row 113 (1); row 147 (5)). Beside it, deciding nothing, is the **mean form**: each arm's cut is the mean over
the twenty roads of 100 × (1 − D_k / D_base,k), and d is the same difference in that form. Row 103's ceilings are in
the mean form, so the ceilings and d are in different forms, and both forms are printed.

**The two readings.** Every damage number of sections 6 and 9 is in the no-knock reading first (D = `damage_thermal`,
`evaluate.READING_KEYS`). The with-knock reading (D = `damage`) sits beside it, labelled "not converged in dt on these
roads" (`four_engine_analysis.WITH_KNOCK_LABEL`; row 147 (5); gate item 3). A row that holds no damage (a temperature,
a fuel, a torque share) has no reading and says so.

### 6.2 The tests of d > 0

Decision 30's paired one-sided t-test of d > 0 over the 20 seeds (t = mean / (sd/√20), 19 degrees of freedom) is
**primary**; the exact one-sided sign test (`analyse_phase_d.sign_test`, the one X1's and X2's analyses used; zero
differences dropped, p = 1 when none is left) is the **declared secondary** (row 113 (1)-(2); decision 30). Both run
through `four_engine_analysis.analyse`, called on the scores and on section 6.7's context; AB computes none of them
itself. Each runs under its own run of row 113 (2)'s graphical procedure (Bretz et al. 2009) at a family-wise α of
0.05. With the B58 alone (row 113 (2) with one engine; row 131 (3); row 147 (5)): **the r = 1.5 test comes first, at
α = 0.05, and its weight passes to r = 0.5 when it rejects**; the r = 0.5 test is spent no α until then. The graph's
adjusted p and its rejections in order are printed. If the two tests disagree, both are reported, the t-test stays
primary, and neither is chosen after the fact.

### 6.3 Each d's interval

Each d, per ratio, reading and form, carries its **two-sided 95 % t interval**: mean ± t₀.₉₇₅,₁₉ × sd/√20, with sd at
ddof 1 and t₀.₉₇₅,₁₉ = 2.0930 (`results/B58H_DESIGN/power_b58.txt:34`). So a sighted arm that does worse than its
blinded twin shows (row 147 (5)). The interval is not adjusted for the graph.

### 6.4 The across-H contrast Δ (exploratory, declared now)

**Δ(s) = cut(sighted r = 1.5, s) − cut(sighted r = 0.5, s)** in `evaluate.py`'s form, per seed; it needs no blind cut,
since the blinded arm is shared (row 147 (6)). It is reported with its two-sided 95 % t interval (as in 6.3) and the
exact two-sided sign test: twice the smaller of the two one-sided tails of `analyse_phase_d.sign_test`, on Δ and on
−Δ, capped at 1. Its mean form sits beside it, deciding nothing (row 149 (2)(v)). Beside both sits row 147 (7)'s
hand-written prediction read from roads.json (C_u(1.5) − C_u(0.5)): about 3.40 points in d's form and 3.41 in the mean
form, 3.3970 and 3.4128 as printed (`results/B58H_DESIGN/power_b58.txt:49`). **Δ's spread is UNKNOWN:** no spread of a
difference between two sighted arms has been measured. With spreads like a paired d's (20.51-24.78 points), its 95 %
interval at n = 20 would be about ±10-12 points (±9.599 to ±11.597, `power_b58.txt:34-35`), so Δ is not expected to
resolve the prediction, and **a Δ interval covering 0 says nothing about preview value across H**. Δ decides nothing
about the criterion.

### 6.5 The B58's model band, and MODEL-LIMITED

The B58 is not validated (section 12.1), and row 107 (4) gives it a band all the same. MODEL-LIMITED is row 113 (6)'s:
a d > 0 verdict (either test) reads MODEL-LIMITED when it changes with every seed's d moved by −Δ_e, or by +Δ_e, the
graph re-run each time (`four_engine_analysis.analyse`'s corners). The band never enters a d > 0 test; it only flags.

**Δ_e**, computed by AB's code after scoring, per ratio and per reading (row 147 (12); MD:1569-1586), is the root sum
of squares of six parts (their linear sum printed beside it), with b = MEI/6 = 0.905 points (MD:232; decision 38), d
the mean over seeds of the paired d in `evaluate.py`'s form at that ratio and reading
(`four_engine_analysis.t_greater`'s mean), and φ = max(1, |1 + ln(1 − c)|) at both arms' realised median cuts c (each
arm's median over its seeds of its seeds' cuts, as a fraction), the larger of the two factors (MD:176-186):

| part | row | contribution |
|---|---|---|
| P1 | D1 | no row on the B58: "no row: assumed at b" (row 107 (4)); read as below |
| P2 | E4b | the same |
| P3 | L1 | b (additive; P3 = κ·b at κ 1, MD:1579) |
| P4 | E8 | κ·b·(\|d\|/MEI)·φ, with κ = 3.4226 read from `results/EPA_TIGHTENINGS.json` `E8.b58_u_val_kappa.with_roads.kappa` (row 107 (4); Q.2) |
| P5 | C3b, C3d | no row on the B58: "no row: assumed at b"; read as below |
| P6 | the table | nothing: the B58 trains on the exact cycle (MD:1580-1581) |

**The two readings of "at b" for P1, P2 and P5, fixed by row 149 (2)(i).** Rows 107 (4) and 147 (8), (12) say only
that each part "enters at b". Row 149 (2) fixes how a multiplicative part takes b:

- **PRIMARY, "κ 1 in the contract's form":** P1, P2 and P5 each contribute b·(|d|/MEI)·φ, the contract's
  multiplicative form (MD:1577-1578) at κ = 1. As d nears 0, the band nears P3 alone.
- **OTHER, "b itself":** P1, P2 and P5 each contribute b, whatever d is. It gives the larger band whenever |d|·φ <
  MEI, which the prediction expects throughout, so more verdicts read MODEL-LIMITED under it.

Only the primary enters the context. The other is computed beside it, deciding nothing. **The primary is the less
conservative reading**, so section 7 prints "MODEL-LIMITED under the other reading of 'at b'" in the sentence of every
verdict that the other reading alone flags. The choice can move a MODEL-LIMITED flag and never a d > 0 verdict: AB
refuses, as a defect, any d > 0 verdict that moves with the band. Row 149 (2) fixes three more readings: (ii) |d|, not
d, in the multiplicative parts, since a band is at least 0; (iii) φ at each arm's median over its seeds of its cuts in
`evaluate.py`'s form, the larger of the two arms' values; (iv) d in the band as `four_engine_analysis.t_greater`'s
mean. In the draft of 7 November these were the agents' DESIGN choices, recorded in no row. Row 149 (2) now fixes them
as row text, Ghassan's answer to point P11 (section S's note).

### 6.6 The readings beside the primary, each deciding nothing

- **Version 5's reading**, the B58's band left out (0 at every ratio and reading), the only band version 5's text
  computes (row 107 (4): "reported under both"; row 147 (8)).
- **The other reading of "at b"** (section 6.5).
- **The companion MODEL-LIMITED reading** (row 147 (8)), declared now: the same verdicts with P3 at κ·b for the
  smallest and the largest of the EPA engines' L1 κ, 1.7168 (the Mazda) and 3.7328 (the Ford), read from
  summary.json's `kappa.L1` (Q.1; INTERFACES 17, 13), every other part as in the primary. It shows whether any verdict
  depends on the assumed b; a verdict that does is printed by name.

### 6.7 The context and the status

AB's `context` command assembles the context `four_engine_analysis.validate_context` needs
(`four_engine_analysis.py:364-433`) after scoring. Every value is read, and none is typed (INTERFACES 17's 13 and 18's
13):

- engines_in_test ['b58'], from Tb's record;
- seeds_per_arm 20 (row 147 (4));
- model_band per ratio and reading: Δ_e under the primary reading of "at b" (section 6.5);
- ceiling per ratio: C(0.5) = 1.8191 and C(1.5) = 5.2319 points, from roads.json `ceilings.per_engine.b58.by[r].C`
  (the mean form; `power_b58.txt:38`, `:40`);
- status_basis: **s_p = 20.56**, X2's no-knock spread over its 5 pairs, read from `results/X2_RESULT.txt:24` (row 148
  (4)); **pilot_pairs 5**, X2's pairs; and s_star = `four_engine_analysis.status_star({'b58': C(1.5)}, 20)` = 9.0687
  (`results/B58H_DESIGN/power_b58.txt:17`). The context's provenance carries s_p's label: "X2's spread: another plant,
  road and budget; not a pilot of this study";
- status **'exploratory'**: row 103 (4)'s rule's output (`four_engine_analysis.py:425-429`). With the exact factor
  1.5576 the rule reads confirmatory only if s_p is at most 5.822 (`power_b58.txt:19`), and s_p is 20.56. **This
  status is recorded here, at `T*`, before any agent of the study trains** (row 103 (4)).

The analysis reads exploratory in any case: with one engine, `four_engine_analysis` makes every test exploratory
(`:668-669`). AB's report prints `four_engine_analysis`'s report verbatim. Its first line, "FOUR-ENGINE TEST (row
113)" (`four_engine_analysis.py:860`), is the committed script's fixed header, followed by its line "ONE ENGINE: the
four-engine test does not run (row 107 (2))" (`:869`). AB's report says so above them.

### 6.8 The analysis's commands and files

```bash
$PY -B b58h_analysis.py context --scores results/B58H_RESULT/scores_b58h.json --out results/B58H_RESULT/context_b58h.json
$PY -B b58h_analysis.py analyse --scores results/B58H_RESULT/scores_b58h.json --context results/B58H_RESULT/context_b58h.json --out results/B58H_RESULT/analysis_b58h.json --report results/B58H_RESULT/analysis_b58h.txt
$PY -B b58h_beside.py core --scores results/B58H_RESULT/scores_b58h.json --records "$OUT/records" --out "$OUT/beside" --jobs 14
```

- `context` refuses unless every record it reads (roads.json, the tightenings, summary.json, the backend record and
  `results/X2_RESULT.txt`) is committed at HEAD. It also refuses unless the scores hold the B58 alone, both ratios and
  seeds exactly 0-19, with a provenance that reads d34, version 6, the knock option false and roads.json's roads_sha.
- `analyse` recomputes the band from the scores. It refuses a context made for other scores (by the scores file's
  sha_text, `thresholds.common.sha_text`, with CRLF read as LF) or for another reading of "at b". It also writes
  section 9.1, each arm's fuel and torque delivery (rows 147 (5) and (12), 149 (5)(b)).
- `b58h_beside.py core` writes sections 9.5 (i) and (v), and 9.6. Its section 9.5 (i) part runs current-grade's 20
  roads. Its section 9.6 part refuses a per-step record whose sha256 is not the index's, and an index whose
  `scores_sha256` is not the committed scores file's; that refusal reads 9.6 "not computed" (row 151 (6)), and 9.5 (i)
  and (v) still run.

### 6.9 The order after training, and the cut-off (row 149 (5))

Everything runs on this laptop (row 143 (1)), from a clean tree at AB's commit or later, in this order, fixed now and
read from the calendar alone (point P6). Each item starts when the one before it has ended and been committed. Times
are at `results/EPA_ROADS/timing.txt`'s 153.9 s a run at 14 jobs (`:2`), ASSUMED equal for agents
(`results/B58H_DESIGN/d148_figures.txt:16-17`).

| item | what | runs | time |
|---|---|---|---|
| (a) | the folders' `sha256sum -c`; the primary scoring with `--records-out` (section 14, step 3); the scores' commit with the records' index | (3 hand-written + 60 agents) × 20 roads = 1260 | 3.85 h of runs (`d148_figures.txt:84`); 10.00 h with the transfer and the reading (`:97`; ASSUMED, `:35`; row 146 (7)) |
| (b) | the analysis, `context` then `analyse` (6.1-6.7, and 9.1); its commit | none | 0.50 h (`:98`; ASSUMED, `:36`) |
| (c) | decision 12's three rows (sections 9.2-9.4, V's `b58h_descriptive.py`); `b58h_beside.py core` (9.5 (i) and (v), 9.6); the practice spread of seeds 0-4 (section 5.2) | 20 for current-grade and 130 for the practice route (`:85-86`), plus V's | 2.96 h, with decision 12's rows at their lower bound of 2.5 h (`:99`, `:37`; `logged_check` and the locked climb UNKNOWN, row 146 (7)) |
| (d) | 9.5 (iii), flat ahead; 9.5 (iv), road 0 | 860 and 62 (`:87-88`) | 2.82 h (`:100`) |
| (e) | 9.5 (ii), the settling label | 1810 (`:89`) | 5.53 h (`:101`) |
| (f) | 9.7, the c_turb re-scores, ×0.75 first | 2 × 1260 + 80 = 2600 (`:90`) | 7.94 h (`:102`) |

- **(a)-(c) always run.** Decision 12's rows are among them, because row 147 rejected dropping decision 12's checks.
- **(d)-(f) each run only if they have started by the cut-off, 23 November 2026 00:00 AST**: W's end plus row 147
  (10)'s 72 h, the team's own end (row 134 (1); `d148_figures.txt:15`, `:135`), unless the supervisor names another
  date before `T*`, never after. An item not started by then is reported "not run (time)". **An item once started runs
  to its end**, and so does a c_turb variant once started.
- A route not committed before the first scoring command reads "not computed (code)" (6.0). An item whose control
  fails reads "not computed", with the control that failed. None of these is replaced by a reading chosen after a
  score.
- The order and the cut-off read only the calendar and the commits. They do not change after any score.
- **Not in this queue:** row 153 (1), committed in D148 before `T*`; row 153 (2), committed before the first scoring
  command or "not computed (code)"; and row 152 (5)'s anchors, which read no agent and so are not scoring (row 149
  (4)): D148 did not carry them, so they are computed during training (ORDER step 22b) and committed before the first
  scoring command, or reported "not computed" (sections 9.7-9.8).

## 7. The decision rule, written before the data

Every verdict is the no-knock reading's, under section 6.2's procedure, with the t-test primary. Each is printed with
its d, its two-sided 95 % interval, its mean form, its band and the ceiling at that ratio, with the with-knock reading
beside it in brackets.

| outcome at ratio r (the t-test under the graph) | what may be said |
|---|---|
| **d > 0** | "On decision 34's roads, B58 agents that saw the grade H = r·τ ahead took less simulated turbine and oil damage (the no-knock reading) on the B58 model, which is not validated (its band assumed at b; section 12.1), than their blinded twins (paired t under the graph, adjusted p = …; d = … points, two-sided 95 % t interval …, against an MEI of 5.43 points; n = 20 seeds per arm). Exploratory, on one plant; not a test of the H/τ criterion." |
| **d > 0 not shown** | "The study does not show a preview effect at H = r·τ in the simulated turbine and oil damage (the no-knock reading) of the B58 model, which is not validated, on these roads (d = … points, two-sided 95 % t interval …, against an MEI of 5.43 points)." A null was the expected outcome (row 147 (7)) and says nothing against the criterion. Never "preview does not help" |
| **MODEL-LIMITED** (either verdict) | the verdict is printed with "MODEL-LIMITED": it changes within the B58's model band, so the plant's unvalidated model, not the agents, may decide it (row 113 (6)). A verdict that the other reading of "at b" alone flags (section 6.5) is printed with "MODEL-LIMITED under the other reading of 'at b'" beside it, in the same sentence (row 149 (2)(i)) |
| **the two-sided interval lies wholly below 0** | "The sighted agents at r took more simulated turbine and oil damage (the no-knock reading) on the B58 model, which is not validated (its band assumed at b; section 12.1), than their blinded twins on these roads (d = … points, two-sided 95 % t interval …, against an MEI of 5.43 points)": a finding about this learner and recipe at this budget, never evidence that preview is worthless, and never read as a result about the criterion |

- **The interval quoted** in every sentence is section 6.3's two-sided 95 % t interval, unadjusted for the graph. Near
  0 it can cover 0 while the one-sided test under the graph rejects (a one-sided test at α matches a two-sided
  interval of level 1 − 2α, not 1 − α); both are then printed as they are, and neither replaces the other.
- **The MEI** (decision 37, 5.43 points) is quoted in every sentence for scale. A d > 0 verdict whose d is below it is
  still printed with it, so that a significant d smaller than the minimum effect of interest is never read as a plain
  preview benefit; no verdict is drawn from the comparison (below).
- **The r = 0.5 verdict** is read only through the graph: its test holds no α unless the r = 1.5 test rejects, so "d >
  0 not shown at r = 0.5" is what it reads when r = 1.5 does not reject, with its unadjusted p printed.
- **The sign test** is printed beside every verdict in its own words; where it and the t-test disagree, both are
  reported, and the t-test's verdict stands.
- **The with-knock reading** decides nothing: where its verdict differs, both are printed, and the no-knock verdict
  stands.
- **Δ** is reported with its interval and sign test, labelled exploratory, deciding nothing. An interval that covers 0
  "says nothing about preview value across H" (row 147 (6)); one that excludes 0 says that the sighted cut differed
  between the two H on these roads, in that direction, and nothing about the criterion.
- **The status** is exploratory for every number, whatever s_p reads (section 6.7).
- **Never written, in any cell:** "a test of the criterion", "a collapse", "H/τ governs" or "the criterion holds" or
  "fails", "preview does not help", or any comparison with X1 or X2 as one experiment. The MEI (5.43 points) and the
  ceilings are printed beside every d for scale; with one engine no equivalence or difference test runs, so no verdict
  is drawn from them.
- **The descriptive blocks** (sections 9 and 10) decide nothing, whatever they show, and none of them enters a
  verdict, the band, the status, Δ or the context (rows 150-153).

## 8. Power, and the prediction dated 6 November 2026, before any agent of the study trained

From row 147 (7), MEASURED by
`PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I -B results/B58H_DESIGN/power_b58.py.txt .` (its output
`results/B58H_DESIGN/power_b58.txt`), which calls the committed `four_engine_analysis`'s `power_t`, `status_star`,
`s_star_level` and `pilot_factor` on roads.json's `ceilings.per_engine.b58` values; n = 20, level α
(`s_star_level(1)` = 0.05), spreads 20.51 and 24.78 points (X2's and X1's, the only measured spreads of a paired d;
`power_b58.txt:1`):

| effect | points | power at α (spread 20.51, 24.78) |
|---|---|---|
| C_a, the hand-written ceiling ((a) over current-grade) at r = 1.5, mean form | 5.232 | 0.293, 0.231 (`power_b58.txt:4`) |
| C_a at r = 1.5, `evaluate.py`'s form | 5.446 | 0.309, 0.243 (`:5`) |
| C_u = 100 (D_ab − D_a)/D_base, the preview-only part at r = 1.5 (row 103 (1)), mean form | 2.549 | 0.134, 0.115 (`:6`) |
| C_u at r = 1.5, `evaluate.py`'s form | 3.222 | 0.167, 0.139 (`:7`) |
| row 113 (6)'s 3.20 points | 3.20 | 0.166, 0.138 (false-negative risk 0.834, 0.862; `:8`) |

Row 103 (4)'s planning powers at the probe's 5.96 points (`four_engine_analysis.PLANNING_C15`) are kept only as
planning values. Against the MEI (decision 37, 5.43 points): C_a is 5.232 in the mean form, below the MEI, and 5.446
in `evaluate.py`'s form, above it; C_u is below it in both forms (`power_b58.txt:11-14`). Version 5's road test asks 2
MEI on every engine; the B58's C(1.5) of 5.2319 is below even one MEI (`:11`), so under version 5's test this set
would not be accepted; that is reported as version 5's, as row 103 writes it.

**The prediction, written before any agent of the study existed** (row 147 (7)): on the drawn set the hand-written
preview part is negative at r = 0.5 (C_u −0.863 points in the mean form, −0.175 in `evaluate.py`'s;
`power_b58.txt:38`) and about 2.5-3.2 points at r = 1.5 (2.549 and 3.222; `:40`). A blind hand-written strategy
out-saves the sighted one at both H: (b), λ at its bound over each whole gap, saves 7.348 points in the mean form,
against (a)'s 1.819 at r = 0.5 and 5.232 at r = 1.5 (`:38`, `:40`). By episode reward, current-grade is the best
hand-written policy on 16 of the 20 roads, among the blind strategies and among the sighted ones at both H, and
preview beats every blind strategy on 3 roads at r = 1.5 (roads 0, 4 and 18) and on none at r = 0.5 (`:38-42`;
roads.json `ceilings.per_engine.b58.best_blind` and `by[r].best_sighted`). **So a null d at either H is the expected
outcome, and it says nothing against the criterion; a d the size of C_u would be detected with probability about
0.14-0.17** (`:7`). The across-H contrast is predicted at 3.3970 points in d's form and 3.4128 in the mean form
(`:49`; section 6.4). Row 153's references stand beside d and never move this prediction (section 9.8).

## 9. The descriptive blocks, each deciding nothing

### 9.1 Fuel and torque delivery (row 147 (5); row 149 (2)(vi)-(viii))

Beside each arm's d come its fuel against the baseline ECU's and its torque delivery, because how d varies with H on
these roads is tied to the gap design and to the fuel spent on enrichment, not only to τ (row 102's knee of a gap
effect; the hand-written (a)'s extra fuel is 1.2720 % at r = 0.5 and 3.9551 % at r = 1.5, `power_b58.txt:38`, `:40`;
roads.json `ceilings.per_engine.b58.by[r].fuel_extra_pct.a.mean`). V's scoring writes, per road, each policy's and
each agent's fuel, its demand steps (torque asked above `evaluate.DEMAND_NM`, 40 Nm), the short steps among them
(torque delivered below (1 − `engine_env.TRACK_TOL`) × the request, `TRACK_TOL` 0.05), and their share, which is null
on a road with no demand step (`evaluate.delivery_block`, `evaluate.py:1097-1112`, in the scores' provenance, which
`four_engine_analysis` copies untouched). Per seed, AB computes, by row 149 (2)(vi)-(vii): the fuel figure, the mean
over the twenty roads of 100 × (fuel / the baseline ECU's fuel on the same road − 1); the short share's mean over the
roads with a demand step; its worst road; and the pooled short share, the seed's short steps over its demand steps
across the twenty roads. Per arm: the median, mean and range over the seeds of the fuel figure and of the mean short
share, and the worst road over every seed. The baseline ECU's and current-grade's own figures are printed beside. A
seed with no demand step on any road is named. This row has no reading. A refusal of it is reported beside the
analysis, which still runs (row 149 (2)(viii)).

### 9.2 to 9.4: decision 12's three checks (row 147 (11))

Decision 12's direction, to train on the extremes and check on logged states, is not reversed silently. Its three
checks run as descriptive rows, per arm and seed, through V's `b58h_descriptive.py` (`cadac38`), the reader of these
rows for schema-4 agents: it lists the study's three arms, scores each agent's checkpoint average, builds the
environment at the agent's own H, and runs every agent through `evaluate.py`'s declared transfer route, which checks
every FATAL field but `scenario` and `episodes_sha`, prints both as trained and as scored, and takes no force. It
imports every fixed choice of X1's two scripts, which stay as X1 left them (but for P's edit of the
`plant_fingerprint` call of `conditions_test.py`, line 374 at `a3cd3a3`), since X1's and X2's published results rest
on them. `b58h_descriptive.py:75`'s "before PL-B and T*" is read as row 148 (9) reads it, CK in place of PL-B; the
file is not edited.

- **9.2, the locked climb** (decision 34's transfer row, VD:200): the twenty frozen episodes of the B58's locked
  climb, every policy's damage in both readings, its cut against the baseline ECU in `evaluate.py`'s form, and per
  ratio and seed the sighted cut minus the blinded one.
- **9.3, the conditions battery** (decision 12's transfer secondary at 50 °C and on hills of 18-22 %; row 116's
  declared secondary): `conditions_test.py`'s seven conditions, each on its own hill, on its varying speed target,
  over frozen episodes 1, 5, 9, 13 and 17: its counts, the cut against the condition's own baseline ECU and the margin
  over its current-grade, in both readings, and per ratio and seed the sighted cut minus the blinded one. **The hills
  file**: `b58h_descriptive.read_grades` reads `results/conditions_b58h_dt1/conditions_grades.json`, which
  `conditions_test.py --set runs/b58h_dt1 --hills-only` writes (the baseline ECU alone, no agent), and refuses a hills
  file whose `fixed_before_training.engine_sha` is not this plant's. V's code places that run in Q (ORDER step 17),
  whose cell does not name it (section 12.3). The commit that adds the file is Q's, `ce452df`, as
  `git log --diff-filter=A --format=%H -- results/conditions_b58h_dt1/conditions_grades.json` prints it at this file's
  commit, before `T*`; its sha_text begins `1cdb7bdf` (its first 8 characters;
  `results/ENGINE_GATES/b58/provenance.txt:60` holds it whole), and its `fixed_before_training` names the set
  `runs/b58h_dt1` and the B58's plant_sha `36655cab94800e30`, derived_sha and engine_sha `023f5589215ee68e` on Qa. The
  hills below are as that file holds them (its `grade` fields; `provenance.txt:62-75` prints them). Held out of
  training (row 116; decision 12): 50 °C, and any hill steeper than the training's 18 %; the pressure rows are
  dimensions the training never drew, reported as such.

  | condition (`conditions_test.CONDITIONS`) | hill, as the file holds it | against the study's training (25-45 °C, hills 0-18 %) |
  |---|---|---|
  | 42 C, 101.3 kPa (trained air) | 8.25 % | ambient and hill in range |
  | 25 C | 21.75 % | ambient in range; held out: the hill is steeper than 18 % |
  | 35 C | 12.00 % | ambient and hill in range |
  | 50 C | 7.50 % | held out: hotter than 45 °C |
  | 90 kPa | 8.75 % | pressure: never drawn in training |
  | 82 kPa, about Taif | 12.00 % | pressure: never drawn in training |
  | 76 kPa, the climb's top | 12.25 % | pressure: never drawn in training |

- **9.4, the logged drives** (decision 12's check on logged states; X1's step 5e; row 116: "the check runs on the B58
  only"): the drives of `results/logged_cycles.json` (X1's, fixed before X1 trained; their count and length are those
  `results/PREREGISTRATION_X1.md` 5e states), each replayed flat at its own speed and median ambient at two
  weightings, T and F exactly as `logged_check.run` computes them, per drive, and whether an agent meets both on every
  drive and weighting. What it can say: no harm on states the simulator is validated on. What it cannot: that the
  agent protects correctly; no drive reaches the trigger.

Each row is written once to `b58h_<row>.json` outside the repository and copied into `results/B58H_RESULT/` (section
14, step 3). They run at section 6.9 (c), after the primary scoring and the analysis, and never delay them; their run
time is at least 2.5 h, the rest UNKNOWN (`d148_figures.txt:37`; row 146 (7)).

### 9.5 Decision 7 (A)'s block (row 150)

Descriptive. It decides nothing: no verdict, band, status, test or Δ reads it, and it is reported beside d at each H.
Every damage number is in both readings, no-knock primary and with-knock beside it, labelled (gate item 3); an item
the knock term cannot change says so. Unless a road set is named, an item uses decision 34's twenty roads, road k with
`evaluate.EPISODES[k]`'s seed and weights, at dt 1 s, on the B58 at `T*`'s plant, with the reward without the knock
term. Except in (ii), each agent is decision 29's average (`evaluate.load_agent`), loaded only after the d34 route's
checks (`evaluate.read_agents`; the fingerprint by `fingerprint.for_arm`). The code is AB's (`b58h_beside.py`, row 149
(3)), and `evaluate.py` is not edited. Each item draws one figure, named here, so that no figure is chosen after a
score.

**(i) Against current-grade and the hand-written strategies** (in AB; `b58h_beside.py core`).
- *Computed:* each agent's saving over current-grade, s = cut(agent) − cut(current-grade), in `evaluate.py`'s form
  (`evaluate.median_cut`). Current-grade's damage per road comes from AB's own run of `check_premise.p_grade_now`
  through `evaluate.run_road_episode`, at the default H, as `score_set` runs it (`evaluate.py:1070-1071`). Its
  per-step trace is kept for 9.6.
- *Controls:* its fuel equals the scores' delivery block road by road (`evaluate.py:1097-1112`), and its cut equals
  the text report's to the report's two decimals. roads.json's `per_road[k].D['neutral']`, the baseline ECU's own run,
  equals the scores' D_base road by road in both readings to 1e-6; if it does not, the hand-written savings are
  printed with the differences beside them.
- *Per arm:* the number of agents with s < 0 (below current-grade), and the median, sd (ddof 1) and range of s.
- *Beside them, in the same form:* hand-written (a) at the arm's r (at both r for the blinded arm), (b) and (a_b),
  from the `evaluate_form` field of roads.json `ceilings.per_engine.b58.by[r].<policy>.<reading>` (re-verified EQUAL
  on P's plant, `results/EPA_ROADS/reverify.json`); and row 153 (1)'s tuned bests, as its committed report prints
  them. X2 printed current-grade beside both of its arms (`results/PREREGISTRATION_X2.md:266-267`).
- *Figure:* `b58h_core_s.png`, each arm's s per seed, with current-grade at 0 and the hand-written savings marked.

**(ii) A settling label, on row 96's ten practice roads** (`evaluate.practice_set`; a route, `b58h_beside.py settle`),
by X2's rule (`results/PREREGISTRATION_X2.md` 5c; `check_x2_convergence.py:12-23`) read at this study's budget (point
P7).
- *Measured:* each agent at three single models, as X2 scored three: `ckpt_300000_steps.zip` (two thirds of training),
  `ckpt_380000_steps.zip` (the first one saved at or after five sixths, 375 000; `train.py` saves one every 10 000
  steps, `train.py:387`, `:991-992`) and `final.zip` (450 000 steps) (`d148_figures.txt:62-65`). Each is loaded by
  stable-baselines3's own loader on the CPU with one torch thread, wrapped with `evaluate.agent_policy`
  (deterministic), and run through `evaluate.run_road_episode` at the agent's own H, with the reward without the knock
  term. The baseline ECU runs once on each practice road, for D_base. The practice cut is in `evaluate.py`'s form.
- *Settled:* an agent is settled if its no-knock practice cut moves by no more than half the MEI, 2.715 points
  (`check_x2_convergence.SETTLE_BAND`), across the three. A pair is settled if its d at r moves no more than that.
- *Label:* an arm reads SETTLED if at least 19 of its 20 agents settled, and the pairs at r likewise: X2's "one
  dissenter each" (`check_x2_convergence.py:22-23`). The counts are printed whatever the label. A missing checkpoint
  reads "no checkpoint" for that agent. The with-knock reading sits beside it.
- *Printed with the label:* the scored policy is decision 29's average of the snapshots at 410 000-450 000 steps
  (`d148_figures.txt:57`), which is none of these files. Under the last-third schedule the learning rate falls to 0
  from 300 000 steps (`training_recipe.LastThird`; `d148_figures.txt:58`), so a small move across these points is
  partly forced by the schedule. It does not by itself show that learning had finished (mistake 15). The label chooses
  no checkpoint, extends no run and drops none.
- *Controls* (mistake 12): the three files' sha256 differ for each agent, or one file was read twice (mistake 25); and
  one file loaded twice gives the same practice damage on every road.
- *Figure:* `b58h_settle.png`, each agent's practice cut at the three points, per arm.

**(iii) Flat ahead** (a route, `b58h_beside.py flat`).
- *The run:* each of the 40 sighted agents is re-run on the twenty roads exactly as the primary scoring runs it, with
  one change: its averaged policy is wrapped so that the observation's four preview entries, 14-17 counted from 0, are
  set to 0 before the policy sees them, and nothing else changes. Those entries are the grade × 12 at H × (1/15, 1/6,
  1/2, 1) (`engine_env.py:1233`, `:1001`, `:1207-1212`). 0 is a flat road ahead, and it is what a blinded agent sees
  (`engine_env.py:1211`). The environment is the agent's own: its H, the frozen plant, and the reward without the
  knock term. It runs through `evaluate.run_road_episode`, whose loop calls `a = policy(env, obs)`
  (`evaluate.py:409`). So no FATAL field differs and no force is taken. The route prints each agent's `meta.json`
  preview_h_s beside its environment's, which are equal, and states that the policy saw 0 in entries 14-17.
- *Also counted* (point P10): at every step the wrapper also computes the policy's action on the unzeroed observation,
  without applying it, and counts the steps at which the two actions differ.
- *Reported, in both forms:* each agent's change in cut, flat ahead minus as scored; per arm, its median, its
  two-sided 95 % t interval and the number of agents whose cut fell; per seed, the flat-ahead d, cut(flat ahead,
  sighted at r) − cut(blinded); and the share of steps at which the action changed.
- *Controls* (mistake 12), on seed 0's three agents: with the zeroing off, the wrapper gives the primary scores'
  damage road by road; the blinded agent through the wrapper gives its primary damage, since its entries are already
  0; and in a sighted environment before a climb entries 14-17 are not all 0, while the policy saw 0 there and every
  other entry unchanged. So a wrapper that zeroes anything else fails.
- *How it is read:* no change says the agent did not use the road ahead, and a fall says it did. Either reading
  decides nothing.
- *Figure:* `b58h_flat.png`, each sighted agent's change in cut, per arm.

**(iv) A behaviour figure on road 0** (a route, `b58h_beside.py road0`; k = 0 of the twenty, chosen as the first road
before any score).
- *The runs:* road 0 with `evaluate.new_record()` (`evaluate.py:340`), for the 60 agents, current-grade and the
  baseline ECU, 62 runs. The scores' records keep no actions (`evaluate.py:1197-1218`).
- *The figure:* for each arm, every seed's applied λ trim and housing temperature against time, with the median over
  seeds marked. Beside them: the baseline ECU's and current-grade's, the grade, each climb's onset, and 9.6's 778 and
  804 °C lines. File: `results/B58H_RESULT/b58h_road0.png`, with its data in `b58h_road0.json`.
- *Control:* each run's damage equals its scored damage on road 0, since the record only reads
  (`evaluate.run_episode`'s docstring).
- *Disclosed beside it:* road 0 is one of the three roads on which a hand-written sighted strategy beat every blind
  one by episode reward at r = 1.5 (roads 0, 4 and 18; `results/B58H_DESIGN/power_b58.txt:41`), so it is not a typical
  road. No damage is drawn, so the readings do not apply.

**(v) Fuel and torque, per seed** (in AB; `b58h_beside.py core`). Sighted minus blinded at each r, in row 149 (2)'s
forms of row 147 (5)'s figures: the fuel figure and the short share, from the scores' delivery block
(`evaluate.py:1097-1112`) and section 9.1's definitions. Each comes with the mean over seeds, its two-sided 95 % t
interval and the sign count, and with current-grade's and the baseline ECU's own figures beside. The knock term cannot
change them: the knock option changes only the return (`evaluate.py:372-374`). The episode return is computed
(`evaluate.py:416`) but not kept in the scores, and it is not recomputed here. *Figure:* `b58h_core_delivery.png`, per
seed, the fuel and short-share differences at each r.

**(vi) Cost, time and fallback.** Code: (i) and (v) in AB; (ii)-(iv) as routes, by row 149 (3)-(4). Runs at
`timing.txt`'s rate: (i) 20 runs, 0.06 h; (iii) 800 runs and 60 control runs, 2.63 h; (iv) 62 runs, 0.19 h; (ii) 1810
runs, 5.53 h (`d148_figures.txt:85`, `:87-89`). They run in section 6.9's order: (i) and (v) at (c), (iii) and (iv) at
(d), (ii) at (e). A route not committed before the first scoring command reads "not computed (code)". An item not
started by the cut-off reads "not run (time)". An item whose control fails reads "not computed", with the control that
failed. None is replaced by a reading chosen after a score.

### 9.6 Decision 8 (B)'s temperature rows (row 151)

Descriptive. It decides nothing, and it is reported beside d at each H.

- *The source* (row 151 (1)): the per-step records the primary scoring writes outside the repository (`--records-out`,
  section 14, step 3; `evaluate.write_records`, `evaluate.py:1197-1218`). They hold the housing temperature t_turb in
  kelvin, float64, per road and step, at the records' dt (1 s), for the baseline ECU and every agent. Current-grade's
  trace comes from 9.5 (i)'s run, kept outside the repository the same way. AB first checks every record's sha256
  against the committed index, and the index's `scores_sha256` against the committed scores.
- *Per policy and road* (row 151 (2)): the peak modelled housing temperature, the largest t_turb − 273.15, in °C; and
  the seconds above 778 °C and above 804 °C, that is dt × the number of steps with t_turb − 273.15 above 778, and
  above 804. The two limits are published gas limits carried to the housing node: a 900 °C load-spectrum parameter
  gives 778 °C, and Conway's 930 °C gives 804 °C (decision 9 of 21 October, section B of
  `results/VALIDATION_DECISIONS.md`, VD:113; Conway's also `REFERENCES.md:651-661`; row 151 (2)'s REFERENCES.md:438
  is the damage model's row, which prints neither).
- *Reported:* per agent, the mean of each over the twenty roads, and its highest single peak; per arm, the mean over
  its seeds, and the arm's highest single peak; per seed and r, sighted minus blinded, with the mean, its two-sided
  95 % t interval and the sign count; beside each arm, the baseline ECU's row, from its own record, and
  current-grade's.
- *Readings* (row 151 (4)): these numbers are the same in both readings: the knock option changes only the return, and
  the trace is the same run (`evaluate.py:372-374`); this is said once, here, for gate item 3. They are modelled
  temperatures of the unvalidated housing (row 147 (8)), never a measurement on the car.
- *Why not 850 or 907 °C* (row 151 (3)): on these roads the baseline's highest climb-slot housing peak, as R1 computed
  it, is 14.48 K below the 850 °C knee: roads.json `report.knee_shares.b58` holds `share_turb` 0.0 over its 75 slots,
  and a largest `slots[].turb_peak_minus_knee_k` of −14.48 K against `turb_knee_k` 1123 K
  (`results/B58H_DESIGN/d148_figures.txt:78`; the baseline's highest peak there, 835.37 °C, `:79`). 907 °C lies higher
  still, so those rows would read zero. AB prints every recorded policy's highest peak. If any reaches 850 °C, the
  seconds above 850 °C are reported for every arm by the same rule (point P10).
- *Figure:* `b58h_core_temps.png`, per arm, each seed's seconds above 778 and above 804 °C, with the baseline ECU's
  and current-grade's marked.
- *Cost, time and fallback* (row 151 (6)): a little AB code (ASSUMED) and no closed-loop run. The records take about
  26.3 MB outside the repository, before each file's small overhead (`d148_figures.txt:80-81`: 61 files of 3 float64
  arrays over 20 roads × 899 steps). It runs at section 6.9 (c). If the records were not written, the row reads "not
  computed", and the scoring is not re-run for it.

**The October alternatives, named and not run** (row 151 (5)) are section 12.1's item 15.

### 9.7 Decision 3 (C)'s c_turb re-scores (row 152)

Descriptive. It decides nothing, it is reported beside d, and it is never a test of H/τ against H (row 147 (1)). It is
a descriptive ablation declared in advance (CLAUDE.md rule 5): its plant_sha differs from the primary scores', so it
is never pooled with them. It runs last, at section 6.9 (f).

- *What is re-scored* (row 152 (1)): each of the 60 agents, as its decision-29 average, on decision 34's twenty roads
  at its own H, dt 1 s, with road k's seed and weights and the reward without the knock term. The plant is the B58 at
  `T*`'s plant with the thermal record's c_turb scaled by each end of the band training draws,
  `engine_env.EXTREME_C_TURB` (`engine_env.py:1852`; `four_engine_roads.py:52-54`, `:281-287`), read and never typed:
  ×0.75 first, then ×1.333. The variant is built as `roads_ceiling.plant_for("b58", ("thermal", "c_turb", f))` builds
  it (`epa_fit.perturbed`; `roads_ceiling.py:432-455`). The baseline ECU, reactive and current-grade run on the same
  variant, as `score_set` runs them, so every cut is against the baseline ECU on that variant.
- *Reported, in both readings and both forms* (row 152 (2)): each arm's cuts; d per seed and r, with the mean, its
  two-sided 95 % t interval and the sign count; Δ with its interval; the delivery figures in row 149 (2)'s forms; and
  each variant's τ, printed by `roads_ceiling.tau_of_plant` (`roads_ceiling.py:458`), with the H/τ each arm then sits
  at, printed and never typed. No test, no p.
- *The route* (row 152 (3); `b58h_beside.py cturb`). It never calls `evaluate.score_set`, which refuses a variant
  (`evaluate.py:1064-1066`), nor `--force-plant-mismatch`, which the d34 route refuses (`evaluate.py:1573-1575`);
  `evaluate.py` is not edited. The agents are read by `evaluate.read_agents`, with every check of the primary scoring
  on the frozen plant (the fingerprint by `fingerprint.for_arm` on the frozen plant's live block). Each episode then
  runs through `evaluate.run_road_episode`, which takes any plant (`evaluate.py:471-486`). Before any run, the variant
  is checked by its plant diff: every changed field lies under the thermal records' c_turb, and that field changed
  (row 142 (5)'s rule). No helper for that diff exists in the tree, so AB writes one. The row's header says that the
  fingerprints were checked on the frozen plant and that only this route applies the variant.
- *Controls* (row 152 (4); mistake 12): at a factor of 1.0 the route gives the primary scores' damage road by road, in
  both readings, for seed 0's three agents and the baseline ECU; a variant with a second changed field is refused;
  both thermal networks of a variant's environment hold the scaled c_turb, as training sets both
  (`four_engine_roads.py:611-612`); and at each end the baseline ECU's damage on road 0, and τ, differ from the frozen
  plant's (mistake 25). Each control fails with its check removed, and the test shows it.
- *Beside it, with no agent* (row 152 (5), point P9): current-grade, (a) at each r, (b), (a_b) and the baseline ECU at
  the same two variants, by `roads_ceiling`'s runner unchanged (`roads_ceiling.run_episode_record`, `plant_for`): 240
  runs, 0.73 h (`d148_figures.txt:92`). They were not ready for D148, which does not carry them, so they are computed
  during training (ORDER step 22b) and committed in `results/B58H_DESIGN/cturb_hw/` before the first scoring command,
  or reported "not computed". They read no agent, so they are not scoring (row 149 (4)).
- *Caveats, printed with every number* (row 152 (6)): the agents trained across this band
  (`four_engine_roads.py:52-54`), so a re-score at its ends tests a policy trained to be robust over it; the road gaps
  are fixed in seconds, so a c_turb change also moves the gaps against τ; τ rests on an ASSUMED c_turb
  (`validation_table.md`; row 147 (8)); D_base moves with c_turb; and on one plant H/τ and H differ by a constant
  factor at each variant too, so this describes the model, never the criterion.
- *Figure:* `b58h_cturb.png`, d at each r against the H/τ each variant gives, with the primary scores' points beside
  them.
- *Cost, time and fallback* (row 152 (7)): 2 × 1260 runs and 80 control runs, 2600 runs, 7.94 h at `timing.txt`'s rate
  (`d148_figures.txt:90`; the rate ASSUMED), 0.52 of the 15.39 h that row 147 (10)'s four variants of 1260 runs take
  at the same rate (`:91`). "Not computed (code)" if the route is not committed before the first scoring command; "not
  run (time)" if it has not started by the cut-off. A variant once started runs to its end; if ×1.333 has not started
  by the cut-off, it alone reads "not run (time)". "Not computed" if a control fails.
- *What it reverses* (row 152 (8)): row 147 (10)'s "and a re-score at c_turb ×0.75 and ×1.333, the ends of the range
  training draws (row 116), are not run for this study", for the agents' re-score only. Row 142 (2)'s (c) and (f) stay
  given up, and V's declared route and RS stay unbuilt.

### 9.8 Decision 12 (B)'s references beside d (row 153)

Two references, each labelled. Every number is in the no-knock reading, with the with-knock one beside it, labelled
`four_engine_analysis.WITH_KNOCK_LABEL` (gate item 3). **Nothing of it enters the scores document, which refuses a key
it does not list (`four_engine_analysis.py:37-42`), the context's ceiling slot (C(0.5) 1.8191 and C(1.5) 5.2319 stay
roads.json's, row 147 (12)), the band, the status, Δ or any verdict.** Row 147 (7)'s prediction of 6 November stands.

1. **First: the tuned hand-written λ strategies** (row 153 (1)), committed in D148 (`c5890f2`,
   `results/B58H_DESIGN/hw_opt/`).
   - *How they were made:* `hw_opt.py` computed them on 14 November, outside the repository, in a clone of Ta
     `0329456` (`C:\Users\badcl\grad_hw`). It reads no agent, and reads the twenty roads through
     `fingerprint.d34_roads` (nothing of commit_reveal). It reuses `roads_ceiling.py`'s runner unchanged, on the
     frozen plant only (`results/B58H_DESIGN/hw_opt/hw_opt.py.txt:126`). In all, 820 runs: the twenty roads × 41
     settings, current-grade and the baseline ECU among them (`d148_figures.txt:152-153`). It holds for `T*`'s plant
     because nothing in `epa_backend.cost_files` changes from Ta to `T*` (row 146 (6)), which D148's
     `git diff --quiet 0329456 HEAD -- <the cost files>` shows; its control record's plant_sha is B1's
     (`d148_figures.txt:154`).
   - *The families, each setting one rule on every road (its docstring):* sighted at r, current-grade plus the λ trim
     at 1/3, 2/3 or all of its bound, never leaner than current-grade's own, for a lead of 1/4, 1/2, 3/4 or all of H
     before each climb, in (a)'s windows with H replaced by the lead: 12 settings at each r. Blind, current-grade plus
     the trim at the same depths from D s after each climb's ramp-down starts until the next onset, and on the lead-in
     from 20 + 2.6·D s, with D = 0, 25, 50, 75 or 100 s: 15 settings (D = 0 at full depth is (b), and D = 50 is
     (a_b)).
   - *What it prints, and what is reported beside d, as its committed report prints them:* per setting and reading,
     the saving over current-grade in the mean form and in `evaluate.py`'s form, the extra fuel, and the highest peak
     in °C; each family's front of saving against extra fuel; and at each r the largest sighted-minus-blind saving at
     equal extra fuel. The blind front runs straight from (0, 0), current-grade itself, through its own tuned points
     (ASSUMED: a mix of two blind settings reaches the straight line). A sighted point beyond the blind front's last
     point is not compared, and the front is never extrapolated (`hw_opt/hw_opt.py.txt:249-255`, `:259`); as run, the
     script held the front there at its last point's saving, which changed nothing it printed (below).
   - *Its control:* it re-runs current-grade, the baseline ECU, (a) at both r, (b) and (a_b) on roads 0 and 1, and
     compares their damage, fuel and return with roads.json's per-road values, PASS below 1e-6
     (`hw_opt.py.txt:167-190`). Re-printed from the run's cache on 15 November, running nothing
     (`hw_opt/control_record.txt:1-2`), it reads "CONTROL: largest difference from roads.json 0.000e+00 -> PASS"
     (`:15`) and exits 0 (`:16`); had it not passed, this item would read "not computed".
   - *Label, its own:* "hand-written lambda strategies tuned over two settings; savings over current-grade on decision
     34's twenty roads, B58 frozen plant; describes the model, never a bound on d" (`hw_opt.py.txt:202-203`).
   - *The committed script is not the script as run, byte for byte.* At 19:11 AST on 14 November, after the run, the
     agents edited `report()`, which only reads the cache, in two places, `blind_at` (`hw_opt.py.txt:250-251`) and the
     gaps line (`:259`), and re-ran `report` from the cache, which rewrote `hw_opt_report.txt` and
     `hw_opt_result.json`. That report equals the one the run printed, line ends aside (`run.log:60-177` against
     `hw_opt_report.txt:1-118`), because no sighted point lies past the blind front's end, the only place the two
     versions differ. The README gives the old text (`hw_opt/README.md`). This file quotes only its printed numbers
     (rule 1.9).
   - *Disclosed:* `hw_opt.py` was written at 16:08 AST and its run started at 16:11 on 14 November (the session's
     record of its commands; `hw_opt/README.md`); decision 12 was answered at 17:11 AST, so (1) started about an hour
     before decision 12 was answered. Its run files were last written at 18:27 AST (file times). Section S's note says
     what of its output was read, and when, before rows 148-153 were final, and that the reading changed no choice
     (section 12.2, item 27). The c_turb part of decision 12 B's first step is row 152 (5)'s anchors (section 9.7);
     the tuned families run at ×1 only.
2. **Then: a reduced λ-only optimum**, labelled **"what the simulator predicts, not a bound"** (row 153 (2), point
   P8), computed on this laptop during training (ORDER step 22b).
   - *Knowledge:* the whole road known, one optimum per road and r. No optimum with only H known, and no blind
     optimum, is computed. Item 1's fronts stand beside it, labelled hand-written.
   - *The lever:* the λ command alone, within `engine_env.ACT_LO[1]` and `ACT_HI[1]`, with the environment applying
     `SLEW[1]` (`engine_env.py:980-982`). The other four actions follow current-grade's rule at every step
     (`check_premise.p_grade_now`), closed loop, as in item 1's families. Current-grade reads the housing temperature
     (`check_premise.py:136-148`), so a replay of its recorded commands would leave item 1's strategies outside the
     search. So it is the optimum at current-grade's other levers, not over five levers.
   - *The limits, per road:* its fuel may exceed current-grade's by no more than hand-written (a)'s extra fuel at r
     (roads.json `ceilings.per_engine.b58.by[r].fuel_extra_pct.a.per_road`), and its short steps
     (`evaluate.py:424-428`) may not exceed current-grade's.
   - *The objective:* the no-knock damage, which counts the oil term, since λ moves the oil and the score counts it
     (`evaluate.py:422`).
   - *The search:* a surrogate of the damage, fuel and short-step responses to λ, fitted per road from closed-loop
     runs at three λ depths. It starts from the applied λ of the best member of item 1 that meets both limits on that
     road; those members are re-run through `evaluate.run_road_episode`, which counts short steps. A schedule is kept
     only if its closed-loop run saves at least as much while meeting both limits. The method is fixed in
     `b58h_lambda_opt.py`'s docstring before any score, and section 15 records that it was written after `T*`.
   - *Results are closed loop only:* every schedule runs on the frozen plant through `evaluate.run_road_episode`. Only
     those runs are results; the surrogate's number sits beside each, with the gap.
   - *Reported, per road and pooled, at each r:* the optimum's saving over current-grade (both forms), its extra fuel,
     its short steps, its peak in °C, and its seconds above 778 and 804 °C (9.6's definitions). Beside it: (a) at r,
     item 1's two fronts at the same fuel, and each arm's saving over current-grade (9.5 (i)). No ratio of d to it is
     reported as a finding. *Figure:* `results/B58H_LAMBDA_OPT/front.png`, the optimum per r over item 1's fronts.
   - *Controls* (mistake 12): replaying a member's applied λ, with current-grade's rule for the rest, gives that
     member's run exactly (damage in both readings, fuel and short steps); on every road the optimum meets both limits
     and saves at least as much as the member it started from, and an optimiser with λ held at current-grade's own
     fails that check wherever the member saves anything; and d, Δ, every verdict, the band and the status are the
     same with and without this row's files (AB's test).
   - *Code and files:* `b58h_lambda_opt.py` and `test_b58h_lambda_opt.py`, outside `epa_backend.cost_files` and
     imported by no hashed module; no package is added. Its outputs go to `results/B58H_LAMBDA_OPT/`. **If it is not
     committed before the first scoring command, the scores' commit records it "not computed (code)"**, and the
     scoring does not wait (row 149 (4)). If it is computed after any score exists, it is post hoc (section I's
     "Optional rows" rule).
   - *Cost* (row 153 (3)): 16-24 h of code and tests (ASSUMED; `d148_figures.txt:119`), and about 160-240 closed-loop
     runs, 0.49-0.73 h at `timing.txt`'s rate (`:93`; the counts ASSUMED).
   - *Label, printed with every number:* λ-only, with the other four actions by current-grade's rule (the boost trim
     among them: it is not at its bound, `engine_env.py:980-982`, and current-grade moves it, `check_premise.py:113`);
     the whole road known; found on a surrogate whose error has no known direction; on the unvalidated B58 model (row
     147 (8)). It describes the model, never the engine, and never bounds d: an agent with five levers may beat it,
     and that is reported as such, never as an agent result.

## 10. What is reported both ways, and the rows reported beside d

| reported | primary | beside it, deciding nothing |
|---|---|---|
| the damage reading | no knock | with knock, beside every number, labelled "not converged in dt on these roads": on these roads the dt 0.5 s repeat moves the B58's (a) at r = 1.5 by +1.1735 points with knock and by −0.0035 without (`power_b58.txt:43`; roads.json `report.dt_repeat.engines.b58.moved`), so a with-knock d cannot resolve effects of the expected size (gate item 3; row 147 (5)) |
| the B58's band | version 6's (row 107 (4)) | version 5's, the band left out (section 6.6) |
| "at b" | κ 1 in the contract's form | b itself (section 6.5; row 149 (2)(i)) |
| P3's κ | 1 (b) | the companion at κ 1.7168 and 3.7328 (section 6.6) |
| the road set | version 6's twenty, scored | version 5's reading, reported and never scored (section 5.1) |
| the form of a cut | `evaluate.py`'s (median) | the mean of the road points, for d and for Δ |
| the test | paired t | exact sign test |
| the B58's plant_sha | P's, `36655cab94800e30` | 865f8e7b7e5c2dbe, the frozen plant's before P |
| the status | the analysis's exploratory | the context's recorded rule output, exploratory (section 6.7) |
| s_p (section 6.7) | X2's no-knock 20.56, 5 pairs (row 148 (4)) | X2's 20.51 with knock; X1's 24.88 and 24.78 (23 pairs); the training's own seeds 0-4 on the practice roads |
| every descriptive cut (9.5, 9.7, 9.8) | `evaluate.py`'s form, no knock | the mean form; with knock, labelled |
| the temperatures (9.6), the fuel and torque rows (9.1, 9.5 (v)) | no reading | none |
| the hand-written and optimum references (9.8) | labelled, beside d | never in the scores, the ceiling slot, the band or the status |

**Row 102's curve, and row 102's grids** (row 147 (2) and (9)):

- *"On row 102's curve"* (row 107 (2)) reads: the B58's hand-written C_e at row 102's six ratios (0.5, 2/3, 1, 1.25,
  1.5 and 1.947) and six H (20, 30, 45, 65, 100 and 130 s) (`grids_b58.txt:13-18`, `:21-26`), as roads.json
  `report.grids` holds them and RV re-verifies them on P's plant (row 140 (1)), reported beside the agents' d at r =
  0.5 and 1.5 (row 147 (2)).
- *Row 102's four-engine grids and spreads* (roads.json `report.grids`: `H_over_tau`, `H_s`, `spreads`, `detail`),
  reported as R1 computed them and as RV re-verifies them, with and without the one-housing Ford: the mean spread is
  0.1566 on the H/τ axis and 0.0603 on the H axis for the four engines, 0.1699 and 0.1790 with the one-housing Ford,
  and 0.0881 and 0.0592 without the Ford (MEASURED, `results/B58H_DESIGN/power_b58.txt:44-46`; `grids_b58.txt:94-96`).
  Label, verbatim: "hand-written savings on plants dropped by Run 2's validation; describes the models, not the
  engines; never evidence for or against the criterion" (row 147 (9)).
- **The run that produces them, fixed and unconditional.** `results/B58H_DESIGN/grids_b58.py.txt`, a read-only
  standard-library script in the form of `results/B58H_DESIGN/r4_counts.py.txt`, run as
  `PYTHONDONTWRITEBYTECODE=1 .venv/Scripts/python.exe -I -B results/B58H_DESIGN/grids_b58.py.txt .` from the
  repository root, which opens only roads.json, writes no file, and prints ASCII only to its standard output (`-I`
  ignores `PYTHONIOENCODING`), committed as `results/B58H_DESIGN/grids_b58.txt`. It prints, from roads.json
  `report.grids`, the B58's C_e at the six ratios and the six H above; every engine's `H_over_tau` and `H_s` entries
  and its `detail` entry; the `spreads` with and without the one-housing Ford; and decision 13's count below as
  roads.json records it for each car. It never prints roads.json's commit_reveal, attempts, steps_log or roads_seed.
  The script and its output are committed in D148, `c5890f2`, before `T*` (row 149 (1), point P13: moved from AB,
  which now comes after `T*`); section 14's step 0 checks that the script still prints it. Its grid equals the study's
  ceiling C at r = 0.5 and 1.5 (`grids_b58.txt:29-30`). Its docstring is stale: it still names AB's commit and row 148
  (8) as its place, and AB's gate as its maker; the script is committed as it ran
  (`SESSION_REPORT_2026-11-15_D148.md`, section 9). Section 16 reports these numbers beside the agents' d, copied from
  that output, and no number of them is quoted from anywhere else (mistake 22). A failure of that run at `T*` stops
  the step, and it is reported (rule 1.11).
- **Decision 13's count** (current-grade's steps under 95 % of the requested torque on the test roads, row 100 (3)) is
  recorded in roads.json for every car; "if current-grade is short, the shortfall is reported beside every margin over
  it" (row 100 (3)): beside the hand-written policies' rows that the scores document holds, and beside sections 9.5
  (i) and 9.8's margins over current-grade, from the print above (`grids_b58.txt:98-111`). The B58's current-grade is
  short on 152 steps (`grids_b58.txt:100`).

## 11. Everything reported; what would stop the study, and how it is reported

- **All 60 runs of the training and all 10 of each check run are reported**, including any that fail to learn, with
  every crashed folder (`<tag>.crashed<N>`) listed. No run is dropped for a poor curve, no seed is added after any
  result is seen, and no run is extended past 450 000 steps (decision 30). More seeds or more steps is another
  experiment with its own preregistration.
- **Every number the analysis prints is reported, whatever it shows**: both tests at both ratios in both readings,
  every interval, Δ, the band under both readings of "at b", version 5's reading, the companion, the delivery block,
  the three descriptive rows of decision 12, rows 150-153's items as run, "not run (time)" or "not computed", row
  102's curve and grids from section 10's print, and B1's attempt. A sensitivity row or re-score not declared here and
  added later is reported as post hoc (VD:391; row 147 (10)).
- **A document once written is kept.** A scores, practice, context or analysis document of this study, once written,
  is kept and reported, and so is every descriptive row's. A re-score or re-analysis after a defect fix is reported
  beside the first, with the fix commit's diff (row 149 (6)). Once any score of this study exists (the primary
  scoring's document is the first; the check run is never scored), no change to a reading, the band, the tests or the
  decision rule counts as a defect fix: such a change is post hoc (VD:391; section I's "Optional rows" rule) and is
  reported as post hoc, beside the preregistered reading, which stands.
- **It is reported beside X1, X2 and every earlier set, one line each, never pooled** (section 2).

**What would stop the study, and the consequence written for each before it can happen** (rows 146 (4), 148 (3), 149
(4)-(6); INTERFACES rule 1.11). No row written after an outcome settles it.

| outcome | consequence |
|---|---|
| PR-B's gate fails on its staged tree or at `T*` (section 14, step 0), the grids print and D148's figures print among its checks | this file is not committed or not pushed, nothing trains, and it is reported (row 146 (4): "A failed check in PR-B's gate ((6)): the same", that is, the step stops and the study's training does not start). By this file's procedure (section 12.3), beyond row 146 (4)'s words, a failure after the commit and before the push is reported in the session report and fixed by amending that unpushed commit and re-running every check of step 0, so that the one commit that adds this file is the commit that passed; a pushed `T*` is never amended |
| the check run prints CHECK RUN: FAIL: a run that ended fails a check of row 148 (2), or the same run crashed a second time | a failed check, a coding defect (row 148 (3)): the training does not start. If the fix changes no cost file and nothing in `FP.PLANT_CODE`, the route below the table runs. If it changes either, the study stops, and it is reported (rule 1.11) |
| a run crashes in the check run or in training, or the machine restarts | X1's crash rule (row 147 (3); section 4): the run is re-trained from step 0, the dead folder kept; every crash is logged in section 15. In the check run a first crash (a FAILED line, or a launcher that did not end) prints CHECK RUN: CRASHED, and the guard, the stale-lock step and the check line run again in a new session (section 14, step 1); a second crash of the same run within one check run reads as a failed check (row 148 (3)) and prints CHECK RUN: FAIL; a run that crashed after writing `final.zip`, which the crash rule's re-run would not train again (`train_all.py:114-115`), prints CHECK RUN: STOP, an outcome no row covers (rule 1.11) |
| a coding defect of Run 2 is found, and a defect re-run opens (row 94) | `engines.trainable()` refuses while it is open (row 139 (1); row 94: "No training starts while such a re-run is open"), so nothing trains or scores; P is re-made by row 140 (5)'s route and Q's runs and B1 are repeated. No row says which commit the study then trains from, so the step stops and it is reported (rule 1.11) |
| the laptop's venv or Windows changes before the last scoring is written | forbidden (row 143 (2); row 146 (8)); updates are paused to 30 November (`CHECKPOINT.md`), and a later end needs Ghassan to extend the pause. No row writes a consequence for a change, so the scoring stops and it is reported (rule 1.11) |
| AB is not committed when the training's folders are back | the scoring waits for AB; nothing else waits (section 6.0) |
| a route of rows 150 (ii)-(iv) or 152, row 152 (5)'s anchors or row 153 (2) is not committed before the first scoring command | it is reported "not computed (code)" (the anchors "not computed"); no code is written for it afterwards; the scoring goes ahead (section 6.0) |
| a commit after `T*` fails a check of section 6.0 | it is not pushed, and the failure is reported in the session report; by this file's procedure (section 12.3) it is fixed by amending that unpushed commit, and its gates run again |
| scoring or the analysis refuses (a FATAL mismatch, an environment mismatch, a re-verification record that is not current, a context made for other scores) | the step stops; the refusal's text is reported; a coding defect is fixed in its own commit and disclosed (section 5.2), under the rule above for a document already written |
| the delivery block is refused | reported beside the analysis, which still runs (descriptive) |
| a descriptive row is refused (the hills file, the agents, the route) or one of its controls fails | that row is reported "not computed", with the refusal's text or the failure; the primary analysis is unaffected |
| an item (d)-(f) of section 6.9 has not started by the cut-off | it is reported "not run (time)"; an item once started runs to its end |
| a records file or the records' index is missing or does not match | section 9.6 is reported "not computed"; the scoring is not re-run for it |
| the device is unavailable, or W ends before the training does | training is never cut at W's end; any hour past it is disclosed (row 134 (1)) |
| the device's environment, recorded by the visit's sheet before CK and after the last run (`SESSION_REPORT_2026-11-15_D148.md`, section 8, item 4), differs between the two records in `check_training_device.py`'s version lines (run with no flag), the interpreter, the Windows build or revision, the installed updates, the driver or the sha256 of `pip freeze` | no row covers it: the scoring does not start, and it is reported with both records (INTERFACES rule 1.11; CLAUDE.md's rule 3, every seed and arm on one environment). The pause's end moves only by the extension 12.2 item 30 (3) names, which is recorded only. Two records that agree decide nothing |
| any other outcome | the step stops, and it is reported (INTERFACES rule 1.11) |

**A failed check run, step by step** (row 148 (3)). Every part beyond the row's words is this file's procedure
(section 12.3). Any case it does not name stops the study, and it is reported (rule 1.11).

1. **The fix.** The defect is fixed in a new commit F on `GRA-test`, pushed, which does not touch this file. F's diff,
   the defect and the printed check that showed it are disclosed.
2. **The cost files.** If F changes any file of `epa_backend.cost_files` (which holds `train.py`'s import closure,
   INTERFACES.md:945, so a fix of the recipe's code may well touch one), or anything in `FP.PLANT_CODE`, the study
   stops, and it is reported (row 148 (3)(b)). B1's timing would no longer cover the tree that trains (rule 1.5), and
   no row says how a second backend record is written: Tb's record, `results/EPA_BACKEND.json`, is written once and
   never edited (`epa_backend.write`). The draft of 7 November read a broken pilot the same way (point P4). Before the
   amendment, on this laptop, with `$PY` and `$COST` as in section 14's step 0 (`FP.PLANT_CODE`'s five files are among
   the cost files), `git diff --quiet 0329456 <F> -- $COST; echo "F changes no cost file: exit $?"` prints exit 0, and
   its output goes in section 15 with the amendment.
3. **The amendment** (row 148 (3)(a)). A dated entry is added to section 15, below its heading, so that no line above
   it changes. It names F as the commit the second check run and the training run from, in place of `T*`, before the
   second check run starts; statement (i) then reads F. Its commit holds this file, the session report, CHECKPOINT and
   `STATE_HISTORY.md`, and nothing else. `T*` stays the one commit that adds this file, which Ta's live test and the
   device's guard still read.
4. **The second check run** is section 4's check line, unchanged, run from F (section 14's guard with `RUNAT` set to
   F), after Jad moves the failed run's folder aside, whole and kept, to `runs/b58h_check_dt1.broken<N>`. Its record
   is committed under `results/B58H_CHECK/` beside the first's, which is kept under `results/B58H_CHECK/broken<N>/`.
   Its sessions' `runat.txt` hold F, so its check counts the crashes of its own sessions only (section 14, step 1).
5. **The training** runs from F, sent as `RUNAT` with `T*` beside it. Every run's `meta.json` must read git_head F.
   Section 15 names F wherever it names the commit a run checked out, and the scoring's checks (section 6.0) read F
   for `T*` (row 149 (4)).

**How a stop is reported:** in section 15 of this file, in that step's session report, and in a section of
`results/README.md` headed with the study's name and the step it stopped at, with every part completed before the stop
reported as it stands. A stop is never turned into a result about preview or the criterion.

## 12. Known limits and deviations, declared now

### 12.1 Limits of what the study can show

1. **The B58 is not validated** (row 147 (8)). The study's plant has not passed the held-out validation that dropped
   the other three. No row of the contract computes P1, P2, P3 or P5 on the B58, so each enters its band "at b", and
   its E8 part takes κ 3.4226 (row 107 (4); Q.2). The only held-out test of the housing model the four engines share,
   L1, read off on all three EPA engines (κ 1.7168, 1.8714 and 3.7328; Q.1), and every EPA housing carries the B58's
   c_turb 6000 J/K, ua_gas_turb 0.90 and ua_turb_amb 18.0 (row 102's Disclosed). τ is not validated (MD:1652-1658),
   and the B58's c_turb is ASSUMED (`validation_table.md`). Hence the band, the companion reading and the label
   MODEL-LIMITED (sections 6.5-6.6).
2. **One plant, one point per H** (section 1): H/τ and H are not separable here, no collapse is possible, and only the
   Ford's τ separated them in the four-engine design; the Ford is dropped (row 107 (6)).
3. **The power is low by construction** (section 8): the expected effect is below the MEI, the hand-written ceiling at
   r = 1.5 is near it, and a blind hand-written strategy out-saves the sighted one at both H.
4. **The knock model is untested until drive C** (gate items 3 and 6; CLAUDE.md:71-73). The reward is without the
   knock term, the spark trim is capped at 0, and the with-knock reading is not converged in dt on these roads; the
   untested knock model still enters the primary reading through E8's band (statement (ii)'s Disclosed line), and
   through the baseline's spark (item 11).
5. **The scored roads are one design** at 130 km/h and 315 K, chosen with an adaptive probe's ceilings in view (12.2,
   item 9), and r = 1.5 sits at the knee of a gap effect set by the gaps (section 4).
6. **The training and the scoring roads differ by design** (rows 116, 101): the agents train on row 116's road, with
   decision 29's 10 % share of the scored kind of road; the transfer is part of what is scored.
7. **The thermal fit still steps at 1 s** (gate item 1, closed by disclosure; section 0.1).
8. **Two machines.** The agents train on Jad's PC (`Windows-11-10.0.26300-SP0`,
   `results/benchmarks/B1_bench_b58.attempt1.txt:3`; build 26300.9974 since KB5132061, INTERFACES section 18's 3) and
   are scored on this laptop (`Windows-11-10.0.26200-SP0`, row 146 (1); `B2_compare.txt:1`); every agent trains on one
   environment (rule 3), and the scoring runs on another. The B58's identity on the device rests on L8's PASS, and
   B2's comparison of the two machines read NOT IDENTICAL, recorded and deciding nothing (section 3.2; section 12.2,
   item 30).

Items 9-14 are the sentences of decisions 4 B and 10 A, as section S's note gives them. They cite no source: A15 and
A21 are unread (`docs/literature/READING_LIST.md:49`, rule 4). Every number computed in them is printed by D148's
`results/B58H_DESIGN/d148_figures.py.txt` (`d148_figures.txt:20-21` for γ and its source, `:68-72` for item 10's sum,
weights and times, `:73-75` for item 12's samples); the lengths of item 12's climbs and gaps are row 101's.

9. **No analytical curve of preview value is stated** (decision 4 B). No analytical curve of preview value against H
   or H/τ is stated for the agents, and none is derived here. Any comparison of d or Δ with such a curve, made after
   this file's commit, is post hoc (section I's 'Optional rows' rule) and is reported as such.
10. **The learner's horizon and the actuator's speed** (decision 10 A (1)). The learner's discount factor is γ = 0.99,
    stable-baselines3 2.9.0's default, read from the installed source (`train.py:971-973` does not set it), at
    dt = 1 s. Its weights sum to about 100 s, about 2.1 τ, and a reward at the r = 1.5 preview's last sample, 71 s
    ahead, carries about half the weight of an immediate one. The λ trim moves at most 0.03 per second
    (`engine_env.py:982`), so it reaches its −0.15 bound from 0 in 5 s, about 0.1 τ. Both are the same in every arm.
    The study cannot tell whether τ, a closed-loop time or the actuator's time governs the value of preview.
11. **The knock model sits inside the baseline's spark** (decision 10 A (2)). The no-knock reading removes knock from
    the reward and the score, but not from the simulated factory controller. Under boost, its spark is the knock
    model's limit (`engine_env.py:177-201`), and the agents' spark can only retard from it (`SPARK_TRIM_MAX` = 0,
    `engine_env.py:991`). The knock model is untested on this car.
12. **The two H do not see the same points** (decision 10 A (3)). The sighted arms see the grade at H × (1/15, 1/6,
    1/2, 1) (`engine_env.py:1001`): 1, 3, 11 and 23 s ahead at r = 0.5, and 4, 11, 35 and 71 s ahead at r = 1.5. The
    two sample sets are not nested, so Δ mixes how far the agent sees with how finely it sees. Δ is measured on roads
    with 67-85 s climbs and 50-150 s gaps (row 101), so any effect of H may be a gap effect (row 102).
13. **The preview is exact** (decision 10 A (4)). The preview is exact, with no noise or delay
    (`engine_env.py:1207-1212`), so d is the value of perfect look-ahead as these agents use it. A real map or GPS
    feed has errors and delay that this study does not model.
14. **Learned policies, not optimal ones** (decision 10 A (5)). d is preview value as this learner realises it at this
    budget, not the value of information between optimal policies. Section 9.8's references are hand-written
    strategies and a λ-only optimum on the model, and neither is a bound on d (row 153).
15. **October's alternatives, named and not run** (row 151 (5)). Decisions 8 and 9 of 21 October 2026 (section B of
    `results/VALIDATION_DECISIONS.md`) agreed sensitivity rows at a 20.3 K turbine scale and at 804 °C and 907 °C
    knees, and this study runs none of them: row 147 (10) gives up the 20.3 K row, and no later row carries the two
    knee rows. On the earlier agents the verdict stayed inconclusive under each of them except the 907 °C knee with
    the knock term. The no-knock reading, computed as published and at 907 °C, stayed inconclusive at both
    (`results/DAMAGE_CONSTANTS.md:48-56`). That one change came with the knock term and was traced to the one-step
    knock spike at the grade step (`results/DAMAGE_CONSTANTS.md:62-68`). Gate item 4's ramp (`75ca65f`) has since
    removed that step from the roads. The seconds above 804 °C (section 9.6) show how long each arm spends above one
    of the two October knees; they are not that knee's damage score.

### 12.2 Deviations and disclosures already known

1. **Run 2's dropped engines.** All three EPA engines were dropped by section 7 on 6 November 2026 (section Q), and
   the four-engine test does not run (MD:1611-1612). Their τ, ceilings, C5 margins and coverage flags stay in the
   roads record and are used here only in row 102's grids, labelled (section 10), and in R4's version-5 reading,
   reported and never scored. Run 2's figures are registered with `verify_docs.py` in G (INTERFACES 17, 7).
2. **The Ford's TIT-cap record reads stale.** `tit_cap_ecu.record_problems` compares the Ford cap record's
   `code_sha_text` with the tree (`tit_cap_ecu.py:311-318`): it has read stale since commit N (`f48e5f0`, row 138
   (3)), and every later change to a CODE_HASHED file adds to that (X, G, and the `evaluate.py` edits of P and V; G's
   review, item (f)). Nothing in this study reads it: row 115 (d) is not run (row 147 (10)), V carries no
   `tit_cap_rescore.py`, and the Ford is dropped. `tit_cap_ecu.py` is RECORD_HASHED and is not edited.
3. **The sensitivity rows given up** (row 147 (10)): row 142 (2)'s (c), E6 row 13's dwell gate at 0 s and 30 s on the
   B58 by its own ECU, and (f), the turbine scale of 20.3 K, are not run, for the cost of drafting V's declared route
   and RS and of running closed-loop variants, against W and the 72 h after it, for a study that is exploratory and
   whose primary d is expected null. Row 142 (2)'s (e) is the B58's own knee and re-scores nothing. These were fixed
   before Run 2 (VD:537) and given up after Run 2's labels were known, under row 133 (2). Row 152 (decision 3 (C))
   restores the agents' re-score at c_turb ×0.75 and ×1.333 as a descriptive ablation, run last and only if it starts
   by the cut-off (sections 6.9, 9.7). Row 142 (2)'s (c) and (f) stay given up.
4. **What was dropped from the route** (row 146 (3)): C2 (ORDER step 12a, the CVT record: the B58's records are
   byte-identical with or without it), CU (the device is the CPU), RS and V's declared sensitivity route, the
   cam-aware surrogate path and the fourth arm. B4 is run on the device and recorded, and decides nothing (section
   3.2). G kept its place before B1, since `epa_fit.py` is inside `epa_backend.cost_files` (rule 1.5). By rows
   148-149, PL-B is not made (CK replaces it) and AB leaves the route to training; ORDER step 19a is empty (INTERFACES
   section 18's 0).
5. **The rows written after Run 2's labels** (rows 146-147, 6 November 2026, after R4 and both of its readings, before
   any code of RV, P, V, Ta or AB and before any agent of this study): new contract text under rule 0, for this study
   only, which reopens nothing of contract versions 5 or 6 that decided Run 2. Written knowing step 3's rate, R1's
   ceilings and every hand-written number they quote, summary.json's re-check margins (Mazda 5.6122 %, Honda 7.7242 %,
   Ford 7.1024 %), and X1's and X2's spreads. R4's version-6 outcome had been predicted before it
   ran from committed margins (the B58's smallest gated C5 margin over the 75 final climbs, 0.0930, that is 9.30 %,
   against 1.9 %, roads.json `c5.b58`) by a standard-library reading that used no roads_seed stream (row 96), and it
   held; version 5's 58 failing slots had been predicted the same way. Both predictions were written in the agents'
   scratch route plan and its reviews (dated 02:01 UTC, before R4 started) and are not in the tree: they are
   disclosed, not evidence (row 146 (1)). New choices made after Run 2's labels, each with its reason in row 147:
   (10)'s sensitivity rows given up, B4 read as recorded only, and the additions of (6), (8), (9) and (11). Rows
   148-153 were written on 14 November 2026, before B1 ran, and brought to B1's measured rate on 15 November, after
   B1's pull; no agent and no score of this study existed then (section S's note).
6. **Row 147 (2)'s C_e at row 102's six ratios and (9)'s grids.** No step of ORDER's route as written on 6 November
   produced them, so the draft of 7 November named the run, `results/B58H_DESIGN/grids_b58.py.txt` and its printed
   output, to be committed in AB's commit before `T*`. Row 149 (1) moved it into D148, committed before `T*` (point
   P13); section 16 reports them beside d, and its failure at `T*` stops the step (rule 1.11). The spreads were
   already printed by `results/B58H_DESIGN/power_b58.txt` (D146).
7. **The version-6 list.** Contract version 6 is the rows section I's note lists (95 (2), 96's practice seed, 103 (1)
   and (2), 107 (3) and (4), 114's table skip), row 136 (the order of leaving and the table route) and row 144 (the
   reading of a summary cell that is not a finite number); "reported under both" applies to each wherever version 5
   can be applied. Rows 147-153 are new contract text for this study only and do not extend that list (section I's
   note, VD:363). Under version 5's road test, 2 MEI on every engine, row 103 wrote that if the set behaved like the
   probe's grid, "no version-5 road, tightening or held-out result exists; the preregistration says so": the B58's own
   C(1.5) is below 2 MEI (section 8). Section Q.4's "version 5 beside version 6" is the labels' reading of version 5's
   other rules, and it drops all three EPA engines too.
8. **Row 107 (6)'s statement**: only the Ford's τ separates H/τ from H; without it the frozen τ span 42.74-47.67 s
   (`grids_b58.txt:52-54`). The Ford is dropped, so no agent study tests H/τ against H, and this study does not.
9. **The probe's adaptivity** (rows 101-103): the road design, the ratios and the floor T were chosen after a ceiling
   probe on the frozen plants that explored 110 road families adaptively, with its ceilings, C5 margins and delivery
   counts in view; no agent and no held-out statistic was used. The design is not blind to the ceiling.
10. **Decision 34's two figures.** The two locked-climb savings decision 34 quoted (VD:200) were about twice what
    direct runs give; they stood from 21 to 30 October and are retired (row 103; `results/EPA_ROADS/control.txt`).
    Decision 34's road condition (a ceiling of at least 2 MEI on every engine) was found unattainable and replaced by
    row 103's T (version 6). Decision 34 was found after X1's and X2's results, from hand-written traces, not from any
    agent of the new test (decision 34's own note).
11. **The knock choices**: the reward without the knock term (Q4; row 113 (5)); the with-knock reading beside every
    number, labelled; decision 12's per-episode draw of the knock threshold not made, nor of the damage scale (rows
    113 (5), 116), which without the knock term in the reward would not affect training either way.
12. **Run 1's in-sample failures**: L1 failed in-sample beyond its noise on all three EPA engines (E 97.0 K, 72.9 K
    and 40.6 K against R 9.9 K; section I's note) before any held-out statistic; every row of sections I-S was written
    after them.
13. **The held-out torque seen**: a held-out torque was seen before Run 1's fit, and nothing used it (section I's
    note; `calibrate_epa.SEEN_BEFORE_THE_FIT`).
14. **R1's draw ran with Windows updates not paused** (R1 `fb20ab2`, row 126; `LastBootUpTime` and the platform string
    unchanged across the draw). Updates have been paused on this laptop since 31 October (row 126 (2)).
15. **The episode of 899 steps** on a 900-sample road (row 122 (2)).
16. **Rows 130 and 131's readings**: the training road's speed follows a notional car (row 130 (1)), since the road as
    row 116 wrote it failed row 119's gate; s* is taken at the graph's first level, α/k with k = 1 here, and the
    confirmatory factor is the exact 1.5576, not row 103 (4)'s rounded 1.56 (row 131 (1)-(2); `power_b58.txt:19`).
17. **The status and the header**: `validate_context`'s recorded status could in principle read 'confirmatory' while
    the analysis reads exploratory; here it reads exploratory too (section 6.7), and the report opens with the
    committed script's fixed header "FOUR-ENGINE TEST (row 113)" (section 6.7). The context's s_p is X2's, not a
    measurement of this study (row 148 (4)), and the status is the rule's output on another experiment's spread.
18. **B1's attempt** is listed in section 3.2, with Ta's code's classification of it; the device is the CPU, so there
    is no CUDA series and no fallback (row 135 (4)(c)). B2 and B4 are recorded and decide nothing; B2's NOT IDENTICAL
    is disclosed in item 30 (row 146 (4), (6)).
19. **One environment, no ablation declared** (row 143 (5)); the scoring on the laptop's frozen environment (Python
    3.13.2, NumPy 2.5.3, SciPy 1.18.1, `Windows-11-10.0.26200-SP0`, roads.json's `hashes.versions`; row 140 (2); Tb's
    record `provenance.versions`), with 3.85 h of runs for the primary scoring (`d148_figures.txt:84`) and 10 h with
    the transfer and the reading (ASSUMED; `:35`; row 146 (7)), and section 6.9's times for the rest.
20. **The hills are checked on engine_sha only**: `read_grades` refuses a hills file fixed on another engine_sha, so a
    plant-code change that kept every value would let a stale file pass (V's notes; mistake 25). The file is the one
    Q's commit `ce452df` adds (section 9.3); a re-made P re-fixes it with Q's repeated runs (row 140 (5)).
21. **The coverage flags** are those of the three EPA cars: "every scored climb on the three EPA cars is not covered
    on three counts: road load above 115 km/h, holds longer than EPA's 30 s, and the charge temperature at 42 °C" (row
    101), each car's coverage being its subset fit's calibration rows (MD:579-583). They discard nothing (row 98), and
    those cars are not scored here.
22. **The B58 has no E6, no 850 °C level row and no load-bearing constant marked** (row 142 (2)(a)): it was never
    calibrated on EPA's data and never held out. The three EPA engines' 850 °C level labels read off (Q.2). E6 row 13,
    the dwell gate (MD:991), is not run on the B58 (item 3).
23. **Gate items 1 and 5** are read for this study by the agents under row 133 (2), not by Ghassan's signature
    (section 0.1); row 110 carried both columns for the four-engine test.
24. **CLAUDE.md's brackets** on gate items 5 and 6 are Ghassan's edit (section 0).
25. **The analysis code after the preregistration** (row 149). AB, the routes and row 153 (2)'s optimum are committed
    after `T*`, during training. X1 and X2 each added their analysis code in their preregistration's own commit
    (`75ca65f` adds `analyse_x1.py`, `06f4686` adds `analyse_x2.py`), so this study is the project's first to do
    otherwise. Section 6 states the analysis in words. Every commit after `T*` adds named files only and changes no
    `.py` file present at `T*`, and nothing loads an agent before AB is pushed. No score exists while the code is
    written.
26. **The check run in place of the pilot** (row 148). It amends row 112 for this study. Its 50 000 steps are the
    shortest run of the exact command, where decision 13 (B) said "a few thousand steps". A code commit, Tc, lets this
    file state the check line (row 148 (5)). Row 147's rejected option "A shorter pilot" is taken for the recipe check
    only, never for s_p (row 148 (9)). Row 112's reason for full length, "the spread at the end of training is what
    the tests read", still holds: the context's s_p is a full-length spread, and the training's own full-length spread
    is printed beside it.
27. **Numbers seen before this file.** The tuned hand-written strategies of section 9.8 were run on 14 November 2026,
    starting about an hour before decision 12 was answered, and committed in D148, before this file was written; its
    drafters may have seen them. Section S's note says what of their output was read, and when: the drafting of rows
    148-153 read only line counts and file times, and one review of the drafts read the first two lines of
    `runs.jsonl`; from 18:27 AST, when the run ended, the session read its frontiers and per-setting results and gave
    the drafters none of it; then, still on 14 November, the checks of `hw_opt/verify/`, a summary
    (`RESULT_SUMMARY.md`, 19:11 AST, not committed) and the decision sheet's status of 19:40 AST, which quotes the
    result. What that reading changed in the rows is row 153 (1)'s account of the script and of its times; it changed
    no choice.
28. **The decisions of 14 November** (rows 148-153 and section S's note). The AI agents wrote their questions, options
    and recommendations after a project audit. Ghassan and Jad answered them together. The agents' readings of those
    answers (points P1-P13) were answered by Ghassan before D148; Jad's answer, relayed by Ghassan after D148's push,
    was "No objections" (section 0). Jad's column is not filled (row 133 (1)). By their answer to decision 3, they
    reverse part of a choice made under row 133 (2) on 6 November (row 152's Disclosed sentence).
29. **Road 0** is one of the three roads where a hand-written sighted strategy beats every blind one at r = 1.5. It
    was chosen as the first road, not for that (section 9.5 (iv)).
30. **B1, and the device at B1** (section S's "What B1 measured"; INTERFACES section 18's 3;
    `SESSION_REPORT_2026-11-15_D148.md`, sections 2, 3 and 11). Recorded, deciding nothing new: n is fixed (row 147
    (4)), and the rate only times the route.
    - *B2* read "VERDICT: NOT IDENTICAL (100 differences)" (`results/benchmarks/B1_device/B2_compare.txt:23`), of
      which the file lists the first 20 (`:3-22`). By Jad's count from the two identity files, they are 75 of the 96
      weight tensors and 25 of the 47 record fields, the actions among them; the 8 counters, the `meta` fields and the
      command are equal, and the curve comparison is empty, since the 600-step run completed 0 episodes (his report,
      section 2). The laptop's identity file is not committed. The cause is not attributed: the processor
      (`B1_bench_b58.attempt1.txt:4`; `results/B58H_DESIGN/hw_opt/control_record.txt:21`), the Windows build
      (`B2_compare.txt:1`), the patch level and the Python build all differ between the laptop and the device (the
      last two by the review of B1, outside the repository). Recorded, deciding nothing (decision 32; row 146 (4)).
    - *The rate* is repeat 1's lower bound, the lower of B1's two; repeat 2, flagged loaded (6.5 % CPU before it
      against `LOAD_LIMIT_PCT` 5.0, `benchmark_training.py:208`), read higher, and the flag decides nothing (row 135
      (4); `d148_figures.txt:8-10`). *B4* is recorded only. *L8*'s printed verdict line is not committed; the
      committed files answer it (section 3.2), and `results/B58_IDENTITY.md` still reads "pending" for L8, a file that
      is not edited (row 146 (6)).
    - *Jad's departures from B1's sheet*, from his report (`SESSION_REPORT_2026-11-14_B1-visit.md`, section 1). None
      of them invalidates a figure: every device figure this study uses was measured at B1, after the changes below,
      and the training runs on the CPU (torch 2.14.0+cpu, `B1_bench_b58.attempt1.txt:11`). (1) The sheet's clone,
      `GRAD-project-step3`, no longer existed: it was a worktree Jad removed on 11 November at his own request. B1 ran
      from a fresh clone of GitHub's `GRA-test`, `C:\Users\admin\grad_device\GRAD-project-device`
      (`results/B58_IDENTITY/L8_device/provenance.txt:1`), checked out at Ta with 0 dirty files (`:3`). It stays at
      `891e29a`, detached and clean, until the visit fetches `T*` and checks it out there: CK and the training run in
      this same clone (ORDER steps 21-22; INTERFACES section 18's 3). (2) Step 3's lock venv was moved out of that
      worktree on 11 November to `C:\Users\admin\grad-venv-lock-3.13.2` (`provenance.txt:5`); B1's check printed
      "VERSIONS: match the lock", and the packages B1 records are the lock's (`B1_bench_b58.attempt1.txt:10-13`). (3)
      Windows Update had not been paused since 1 October: since step 3 Windows installed KB5132061 (build 26300.9974)
      and KB5132688 on 11 November and Windows App Runtime updates on 11 and 12 November, and the NVIDIA driver went
      from 617.42 at step 3 (`results/benchmarks/step3_2026-11-02/A3_bench_cpu.txt:15`) to 621.24 on 13 November
      (`B1_bench_b58.attempt1.txt:15`); torch there is a CPU build (`:11`, `:16`), so the driver enters no training.
      Jad paused updates at 19:52 AST on 14 November, before the benchmark (19:53), until 28 November 2026, so B1, B2,
      L8 and B4 ran with updates paused; if the training runs past 28 November, the pause is extended before it ends.
      Jad, relayed by Ghassan on 15 November: nothing was installed on the PC after the pause ("No"), and the NVIDIA
      app's own auto-update is off ("Yes") (`SESSION_REPORT_2026-11-15_D148.md`, section 11). (4) The IDE
      (Antigravity, with Claude Code in it) stayed open, as at step 3; Claude made three small edits to Jad's report
      in the benchmark's first minute and was then idle. (5) `core.autocrlf=true` on the device, so the clone's work
      tree has CRLF line ends, as step 3's had. Every FATAL fingerprint field is independent of line ends: plant_sha
      reads CRLF as LF (`fingerprint.py:477` at `891e29a`), derived_sha and engine_sha hash values, and
      backend_contract reads its files through `thresholds.common.sha_text`, which reads CRLF as LF
      (`thresholds/common.py:37-43` at `891e29a`); B2's `meta` fields are equal, and B1's plant_sha is this laptop's
      (`d148_figures.txt:7`, `:154`). The setting is kept through `T*` and the training.
    - *The device's environment* is recorded by the visit's sheet before CK and after the last run (the session
      report's section 8, item 4); section 11 says beforehand what a difference between the two records means.
    - *The visit's time* is still open (section 0).
31. **Tc's departure from the gate's wording**, disclosed beside row 148 (5) in section 4: two code lines of
    `epa_backend.py` and the test file's module-level lines and docstring, beyond "`B58H_LINES`, docstrings and
    comments"; three refusal texts still cite row 147 (3) for the check line.
32. **Tb's record** holds n null and in_test ['b58'] and no schedule drop, so Tb wrote no drop line; the four-engine
    test does not run, and Run 2's failed validations are the result, with row 136 (4)'s three disclosures carried for
    them (`SESSION_REPORT_2026-11-15_D148.md`, section 12; row 146 (3), (9)).
33. **Words read as replaced, not edited** (rows 148 (9), 149 (7)-(9); no earlier row is edited, row 146 (9)):
    `evaluate.py:11`'s usage line (`runs/b58h_pilot_dt1/<each run>`) and `b58h_descriptive.py:75`'s "before PL-B and
    T*", both in files frozen from B1's git_head or from `T*`; `results/B58H_DESIGN/budget.txt`'s training at step 3's
    rate and its AB and PL-B lines, which `d148_figures.txt:40-48` and `:105-109` replace (INTERFACES section 18's
    "Words replaced").

### 12.3 What this file names that rows 146-153 do not

Rows 146-153 and section S's note fix every reading, threshold, order and rule this file states, beside the details
of form listed last below. Row 149 (2) makes the
analysis's readings row text, the primary reading of "at b" among them. What is left to this file is what row 149 (2)
leaves to it: "File names, paths, subcommand names and the run procedures of PR-B's sections 4, 5.2, 6.8 and 14". None
of it can move d, Δ, the band, the status or a verdict.

- **File names and paths**: the files of section 5.2's table, the subcommands of section 6.8 and section 14
  (`context`, `analyse`, `core`, `flat`, `road0`, `settle`, `cturb`, and `b58h_beside.py --list`, which
  prints the routes present), the figures' file names, the launcher logs of
  section 4, `results/B58H_DESIGN/grids_b58.py.txt` with its print, and `runs/b58h_check_dt1`'s files as section 14
  collects them.
- **Procedures**: section 14's guard on Jad's PC, its check block (which reads "every run exits 0" and each crash from
  the launch log of every session of the check run (the sessions whose `runat.txt` holds the same `RUNAT`), a FAILED
  line or a launcher that did not end, counts row 148 (3)'s second crash over them, and prints CHECK RUN: CRASHED for
  a first crash, CHECK RUN: NOT RUN when the launcher started no run and CHECK RUN: STOP for a run that crashed after
  writing `final.zip`), its record block, run on OK and on FAIL, and the stale-lock step; the guard's `runat.txt` and
  its `PYTHONUNBUFFERED=1`, which `train_all.py` already gives every run (`train_all.py:304`); the gates of each
  commit after `T*` as section 14 runs them; the check that no line above section 15 changed; the failed check run's
  route of section 11, beyond row 148 (3)'s words; the amend of an unpushed commit whose gate failed (sections 11 and
  14); and which fields of the device's two environment records section 11 compares.
- **V's DESIGN definitions**, committed at `cadac38` before any score and named by row 149 (2)(vii): a demand step
  asks more than 40 Nm; a short step delivers less than (1 − 0.05) of the request.
- **The hills run's place**: ORDER step 17's cell does not name `conditions_test.py --set runs/b58h_dt1 --hills-only`;
  V's code places it in Q, and this file reads the hills from the commit that adds their file, Q's `ce452df` (section
  9.3).
- **Details of form**, none a reading and none able to move d, Δ, the band, the status or a verdict: 9.1's per-arm
  median, mean and range over the seeds; `context`'s refusals in 6.8 (seeds exactly 0-19, its records committed at
  HEAD); 9.8 item 2's figure, `front.png`; and 6.9's rule that each item starts when the one before it has ended and
  been committed.

Changing any of them before `T*` is a change of this file or of a row; after `T*` it is post hoc (section 11).

## 13. The decisions this study rests on

| item | where it is fixed | whose answer |
|---|---|---|
| the study, exploratory, never a test of the criterion | row 107 (2), (6); row 147 (1) | answered 30 October; this study under row 133 (2), Q1 |
| the plant, X1's `cf43fbb` frozen | decision 31; row 147 (1) | answered 21 October |
| three arms, one blinded arm for both H | rows 117, 135 (5); row 147 (2) | 30 October; 5 November under row 133 (2) |
| H = r·τ at r = 0.5 and 1.5, τ's one definition | row 102; row 147 (2) | 30 October |
| n = 20, seeds 0-19 | row 147 (4) | **Ghassan's own answer Q3**, re-confirmed by him on 15 November 2026 (decision 9 B, section S's note) |
| the reward without the knock term | row 147 (3); row 113 (5) | **Ghassan's own answer Q4** |
| decision 29's recipe, row 116's training road | rows 112, 116, 118, 130; row 147 (3) | 30-31 October |
| the device, the CPU, 12 at once | row 135 | 5 November under row 133 (2) |
| the test set, decision 34's twenty (version 6) | rows 95 (2), 101; row 147 (5) | 30 October; row 146 (1) |
| the statistics, the graph, MODEL-LIMITED | rows 113, 131; row 147 (5) | 30-31 October |
| the across-H contrast Δ | row 147 (6) | under row 133 (2) |
| the B58's band and the companion reading | row 107 (4); row 147 (8) | 30 October; under row 133 (2) |
| the descriptive rows of decision 12 | row 147 (11); decision 12 | under row 133 (2) |
| row 102's grids, labelled | row 147 (9) | under row 133 (2) |
| the sensitivity rows given up | row 147 (10) | under row 133 (2); the agents' re-score at the c_turb ends restored by row 152 |
| the analysis committed before scoring | row 147 (12) | under row 133 (2); after `T*` by row 149 |
| rule 2 amended, gate item 6 waived | row 147 (13); `ROW146_STATEMENTS.md` | **Ghassan's own answer Q2, signed** |
| gate items 1 and 5 for this study | row 147 (13), row 110 | under row 133 (2) |
| the route, `T*`, the device route, every outcome's consequence | row 146 | under row 133 (2), Q1 |
| the check run in place of the pilot; s_p from X2; Tc | row 148 | **Ghassan's and Jad's own answer, 13 B**; points P1-P4 and P10 answered by Ghassan |
| the analysis stated in words; AB after `T*`; what waits; the order after training and its cut-off; the copy rule | row 149 | **their own answer, 14 B**; points P5, P6 and P11 answered by Ghassan |
| the agents against current-grade; the settling label; flat ahead; road 0; fuel and torque per seed | row 150 | **their own answer, 7 A**; points P7 and P10 answered by Ghassan |
| the housing temperature in °C and in seconds; October's alternatives named | row 151 | **their own answer, 8 B**; point P10 answered by Ghassan |
| the c_turb re-scores and their hand-written anchors | row 152 | **their own answer, 3 C**; point P9 answered by Ghassan |
| the tuned hand-written strategies and the λ-only optimum | row 153 | **their own answer, 12 B**; point P8 answered by Ghassan |
| no analytical curve; the five disclosures; Q3 re-confirmed | section S's note | **their own answers, 4 B, 10 A and 9 B**; Q3 re-confirmed by Ghassan alone; points P12 and P13 answered by Ghassan |
| this file's names, paths and procedures (section 12.3) | no row; row 149 (2) leaves them to this file | the agents; none can move a result |

## 14. How to run it

**Step 0, PR-B's gate** (row 146 (6); row 149 (7); INTERFACES 18, 14), on this laptop, from the repository root,
before and after this file's commit; its output goes in section 15 and in PR-B's session report. On the staged tree
(this file, the session report, CHECKPOINT and `STATE_HISTORY.md` staged, nothing else):

```bash
cd /c/Users/badcl/Desktop/GRAD-project
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe
COST=$($PY -I -B -c "import os, sys; sys.path.insert(0, os.getcwd()); import epa_backend as EB; print(' '.join(sorted(set(EB.cost_files(os.getcwd(), 'HEAD')) | set(EB.cost_files(os.getcwd(), sys.argv[1])))))" 0329456)
[ -n "$COST" ] && echo "cost files listed" || echo "STOP: the cost-file list is empty"
git diff --cached --quiet 0329456 -- $COST; echo "cost files unchanged since B1: exit $?"
$PY -B epa_backend.py check; echo "epa_backend check: exit $?"
```

Then the commit of the four staged paths, and in the same shell (`$COST` and `$PY` as above), at `T*`:

```bash
git log -1 --format=%H; git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md
[ "$(git rev-parse HEAD~1)" = "$(git rev-parse 5d801be)" ] && echo "parent is Tb's commit" || echo "STOP: the parent is not Tb's commit (row 149 (1))"
git diff --quiet 0329456 HEAD -- $COST; echo "at T*: exit $?"
$PY -B epa_backend.py check; echo "epa_backend check at T*: exit $?"
git diff --stat 5d801be HEAD            # this file, the session report, CHECKPOINT and STATE_HISTORY.md, and nothing else
$PY -I -B results/B58H_DESIGN/grids_b58.py.txt . | diff --strip-trailing-cr - results/B58H_DESIGN/grids_b58.txt; echo "grids print reproduced: exit $?"
$PY -I -B results/B58H_DESIGN/d148_figures.py.txt . | diff --strip-trailing-cr - results/B58H_DESIGN/d148_figures.txt; echo "D148's figures reproduced: exit $?"
git grep -n -E '[{][{]|[}][}]' -- results/PREREGISTRATION_B58H.md; echo "placeholders left: exit $? (1: none)"
$PY -B verify_docs.py; echo "verify_docs: exit $?"
$PY -B -m unittest test_epa_backend.Preregistration test_epa_backend.PreregistrationB58H; echo "unittest: exit $?"
```

The gate passes only if every line of both blocks that prints an exit code prints `exit 0`, but the placeholder line,
which must print `exit 1` (nothing found), the unittest line reports OK with no test skipped, no line prints `STOP`,
the two `git log` lines print the same sha, and the diff stat lists the four paths alone (INTERFACES 18, 11 and 14:
with `core.autocrlf=true` a checkout writes both prints with CRLF, so their comparison ignores line ends). Anything
else is a failure of the gate (section 11): nothing is pushed, and the failure is reported in the session report. **A
failure after the commit and before the push is fixed by amending that unpushed commit** (the fix staged, then
`git commit --amend`; this file's procedure, section 12.3), and both blocks are run again from the top, so that the
one commit that adds this file, which `git log --diff-filter=A` prints and Jad checks out, is the commit that passed.
A second commit is never used to fix it, and a pushed `T*` is never amended. Only once the gate has passed:

```bash
git push origin HEAD:GRA-test
```

**Every later commit that touches this file** (section 15's lines, an amendment naming F, section 16) runs, after the
commit and before its push, the check that no line above section 15's heading changed since `T*`, Ta's live test and
`verify_docs.py`; their output goes in section 15. A STOP or a failure is fixed by amending that unpushed commit, as
above:

```bash
cd /c/Users/badcl/Desktop/GRAD-project
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe
TSTAR=$(git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md)
cmp <(git show "$TSTAR:results/PREREGISTRATION_B58H.md" | sed '/^## 15\. /q') <(git show "HEAD:results/PREREGISTRATION_B58H.md" | sed '/^## 15\. /q') && echo "ABOVE SECTION 15: UNCHANGED SINCE T*" || echo "STOP: a line above section 15 changed since T*"
git diff --stat "$TSTAR" HEAD -- results/PREREGISTRATION_B58H.md
$PY -B -m unittest test_epa_backend.PreregistrationB58H; echo "unittest: exit $?"
$PY -B verify_docs.py; echo "verify_docs: exit $?"
```

**Step 1, the one visit to Jad's PC: the check run, then the training** (rows 147 (3), 148; ORDER steps 21-22;
INTERFACES 18, 3). Ghassan sends `T*` as its full 40-character sha (the laptop's
`git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md`), the runbook's "Before you start" block
(`docs/build_step_2/DEVICE_RUNBOOK.md:14-22`) with `REPO` and `PY` replaced by the paths B1 ran from and a new `OUT`,
and this step. The PC stays idle, on AC power, with sleep off and Windows updates paused until the study's training
ends. Jad pastes the sha between the quotes of `TSTAR`; `RUNAT` stays `$TSTAR` unless Ghassan sends the commit F that
an amendment of section 15 names (section 11). First the guard:

```bash
REPO=/c/Users/admin/grad_device/GRAD-project-device      # the clone B1 ran in (INTERFACES 18, 3)
PY=/c/Users/admin/grad-venv-lock-3.13.2/Scripts/python.exe   # step 3's lock venv, the interpreter L8 recorded
OUT=~/grad_device/b58h_training_1      # a NEW folder outside the repository, one per session (_1, _2, ...)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONIOENCODING=utf-8 PYTHONUNBUFFERED=1   # the launch log holds each start as printed, so a restart leaves it (row 148 (3))
TSTAR='paste T* here, the 40-character sha Ghassan sends'
RUNAT="$TSTAR"                         # T*; or the commit F an amendment names, if Ghassan sends one
[ -e "$OUT" ] && OUTNEW=no || OUTNEW=yes      # a session's OUT must not exist yet
mkdir -p "$OUT" && { [ "$OUTNEW" = no ] || printf '%s\n' "$RUNAT" > "$OUT/runat.txt"; } && cd "$REPO"   # runat.txt: this session's check run
git -C "$REPO" config --get core.autocrlf                                             # prints true (kept, INTERFACES 18, 3)
git -C "$REPO" fetch && git -C "$REPO" checkout --detach "$RUNAT"
git -C "$REPO" status --porcelain                                                     # prints nothing
git -C "$REPO" log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md    # prints T*
[ "$OUTNEW" = yes ] && [ "$(git -C "$REPO" config --get core.autocrlf)" = true ] && [ "$(git -C "$REPO" rev-parse HEAD)" = "$RUNAT" ] && [ -z "$(git -C "$REPO" status --porcelain)" ] && [ "$(git -C "$REPO" log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md)" = "$TSTAR" ] && git -C "$REPO" merge-base --is-ancestor "$TSTAR" HEAD && echo "RUN COMMIT: OK" || echo "STOP: not at the commit Ghassan sent, core.autocrlf is not true, or OUT existed already (take the next number); do not run the next block"
```

Jad runs anything further only after the last line above printed `RUN COMMIT: OK`; on `STOP` he runs nothing more and
tells Ghassan. Then section 4's check line, exactly as it is fenced there, from `$REPO` in the same shell. When the
launcher has ended, the check (row 148 (2)). It reads only the run folders' files and the launch logs of this check
run's sessions, and loads no agent:

```bash
$PY -I -B - "$REPO/runs/b58h_check_dt1" "$RUNAT" "$OUT/b58h_check_launch.txt" <<'EOF' 2>&1 | tee "$OUT/b58h_check_printed.txt"
import glob, json, os, sys
sys.path.insert(0, os.getcwd())
import training_recipe as TR
import four_engine_roads as FER
root, runat, launch = sys.argv[1], sys.argv[2], sys.argv[3]
want = TR.snapshot_steps(TR.DECISION_29_WINDOW, TR.DECISION_29_WINDOW)   # the check line's steps (row 148 (1))
tags = ([FER.run_tag(s, use_preview=False, ratio=None) for s in range(2000, 2005)]
        + [FER.run_tag(s, use_preview=True, ratio=1.5) for s in range(2000, 2005)])


def session(path):
    """One session's launch log: the runs it started and finished (exit 0), the runs that crashed in it, and whether
    the launcher ended. A run crashed if it has a FAILED line or, when the launcher did not end (a restart, a killed
    or refused launcher), if it was started and not finished (row 148 (3))."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        words = [line.split() for line in fh]
    said = lambda word: {t for w in words for t in tags if w[:1] == [word] and t in w}
    ended = any(w[:2] == ["all", "done"] for w in words)
    return said("started"), said("finished"), (said("FAILED") if ended else said("started") - said("finished")), ended


def same_check_run(path):
    """A session of this check run: the guard wrote RUNAT to its folder's runat.txt."""
    try:
        with open(os.path.join(os.path.dirname(path), "runat.txt"), encoding="utf-8") as fh:
            return fh.read().strip() == runat
    except OSError:
        return False


here = os.path.normcase(os.path.abspath(launch))
logs = {os.path.normcase(os.path.abspath(p)) for p in glob.glob(os.path.join(
    os.path.dirname(os.path.dirname(here)), "b58h_training_*", "b58h_check_launch.txt")) if same_check_run(p)} | {here}
crashes = {t: sum(t in session(p)[2] for p in logs) for t in tags}
started, finished, crashed_now, ended = session(here)
print("launch logs of this check run read:", len(logs), "| this session's launcher ended:", ended)
print("crashed in this session:", sorted(crashed_now) or "none",
      "| crashes over this check run:", {t: n for t, n in crashes.items() if n} or "none")
good = {}
for t in tags:
    p = os.path.join(root, t)
    try:
        with open(os.path.join(p, "config.json"), encoding="utf-8") as fh:
            rec = json.load(fh)["recipe"]
        with open(os.path.join(p, "meta.json"), encoding="utf-8") as fh:
            meta = json.load(fh)
        steps = [s["step"] for s in TR.read_manifest(p)["snapshots"]]
        good[t] = (os.path.isfile(os.path.join(p, "final.zip")) and rec.get("learning_rate_at_end") == 0.0
                   and steps == want and (rec.get("scored_share") or {}).get("every") == FER.SHARE_EVERY
                   and meta.get("git_head") == runat and meta.get("git_dirty") is False)
        print(t, "lr at end", rec.get("learning_rate_at_end"), "snapshots", steps,
              "git_head is RUNAT", meta.get("git_head") == runat, "ok" if good[t] else "FAIL")
    except (OSError, ValueError, KeyError) as exc:
        good[t] = False
        print(t, "FAIL:", exc)
print("crashed folders, kept:", (sorted(d for d in os.listdir(root) if ".crashed" in d) or "none")
      if os.path.isdir(root) else "no run folder")
second = sorted(t for t in tags if crashes[t] >= 2)                     # row 148 (3): a second crash
broken = sorted(t for t in finished if not good[t])                     # ended with exit 0, fails a check
rerun = sorted(t for t in tags if t in crashed_now or (not good[t] and t not in finished))   # crashed, or not run to its end
if not started:
    print("CHECK RUN: NOT RUN (the launcher started no run: read its launch log; section 11, any other outcome)")
elif second:
    print("CHECK RUN: FAIL (a second crash of " + ", ".join(second) + ": a failed check, a coding defect, row 148 (3);"
          " do not start the training)")
elif broken:
    print("CHECK RUN: FAIL (a failed check of " + ", ".join(broken) + ": a coding defect, row 148 (3); do not start"
          " the training)")
elif any(os.path.isfile(os.path.join(root, t, "final.zip")) for t in crashed_now):
    print("CHECK RUN: STOP (" + ", ".join(t for t in sorted(crashed_now) if os.path.isfile(os.path.join(root, t, "final.zip")))
          + " crashed after writing final.zip, so the crash rule would not train it again (train_all.py:114-115):"
          " no row covers it; section 11, any other outcome)")
elif rerun:
    print("CHECK RUN: CRASHED (" + ", ".join(rerun) + ": row 148 (3)'s crash rule; a new session runs the guard, the"
          " stale-lock step and the check line again; do not start the training)")
else:
    print("CHECK RUN: OK")
EOF
```

On "CHECK RUN: CRASHED" he tells Ghassan and follows the crash rule below: in a new session with a new `OUT`, the
guard, the stale-lock step and the check line again. On "CHECK RUN: FAIL" he runs the record block below, sends
`$OUT/ck_record` zipped to Ghassan, and runs nothing more (section 11). On anything else but "CHECK RUN: OK", "CHECK
RUN: NOT RUN" and "CHECK RUN: STOP" among them, he runs nothing more and tells Ghassan. On "CHECK RUN: OK", he first
collects CK's record (row 148 (8)), and zips `$OUT/ck_record` and sends it to Ghassan:

```bash
CK="$OUT/ck_record"; mkdir -p "$CK"
(cd "$REPO/runs/b58h_check_dt1" && find . -maxdepth 2 \( -name config.json -o -name meta.json -o -name checkpoint_average.json -o -name 'log_*.txt' \) -print0 | xargs -0 cp --parents -t "$CK")
for d in "$(dirname "$OUT")"/b58h_training_*/; do [ "$(cat "$d/runat.txt" 2>/dev/null)" = "$RUNAT" ] && [ -e "$d/b58h_check_launch.txt" ] && mkdir -p "$CK/sessions/$(basename "$d")" && cp "$d"/b58h_*.txt "$CK/sessions/$(basename "$d")"/; done
(cd "$CK" && find . -type f ! -name SHA256SUMS -print0 | xargs -0 sha256sum > SHA256SUMS)
```

Then section 4's training line, exactly as it is fenced there, in the same session. When it has ended:

```bash
(cd "$REPO" && find runs/b58h_check_dt1 runs/b58h_dt1 $(ls -d runs/b58h_check_dt1.broken* 2>/dev/null) -type f -print0 | xargs -0 sha256sum) > "$OUT/SHA256SUMS"
```

Jad records the first and last hour of training (row 134 (1)). He returns `runs/b58h_check_dt1`, `runs/b58h_dt1` and
any `runs/b58h_check_dt1.broken<N>` (every file, every checkpoint among them), every session's launch logs, printed
checks and stale-lock prints, and `SHA256SUMS`, zipped (INTERFACES 18, 3). After a crash or a restart during CK, a new
session runs the guard with a new `OUT`, the stale-lock step below and the check line again; the dead run is trained
again from 0 (section 4), and the check reads the launch log of every session of this check run (each
`~/grad_device/b58h_training_*` whose `runat.txt`, written by the guard, holds `RUNAT`), so that a second crash of the
same run reads as a failed check (row 148 (3)). After a crash or a restart during training, the guard, the stale-lock
step and the training line run again the same way; CK is not repeated, since it passed.

**The stale-lock step.** A restart or a killed run leaves the run's `RUNNING` file behind (`fingerprint.running_pid`),
and if its pid has been reused the launcher refuses the run as "being trained right now" (`train_all.py:117-118`). The
step removes that file from every run folder without `final.zip`, and only when no python process runs; the line runs
again only after it printed `STALE LOCKS: DONE`. Its print is kept in `$OUT/b58h_stale_locks.txt`:

```bash
if tasklist | grep -i '^python'; then echo "STOP: a python process still runs: wait for it to end, then run this block again"; else for d in "$REPO"/runs/b58h_check_dt1/*/ "$REPO"/runs/b58h_dt1/*/; do case "$d" in *.crashed*|*.broken*) continue ;; esac; [ -e "$d/RUNNING" ] && [ ! -e "$d/final.zip" ] && rm -- "$d/RUNNING" && echo "stale lock removed: ${d}RUNNING"; done; echo "STALE LOCKS: DONE"; fi 2>&1 | tee -a "$OUT/b58h_stale_locks.txt"
```

**Step 2, on this laptop during training: the commits after `T*`** (row 149 (3); section 6.0). CK's record goes into
`results/B58H_CHECK/` once its `SHA256SUMS` checks. Then AB, then each route, then row 152 (5)'s anchors and row 153
(2), each in a commit of its own. Each is checked after its commit and before its push:

```bash
cd /c/Users/badcl/Desktop/GRAD-project
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe
TSTAR=$(git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md)
RUNAT="$TSTAR"                               # or F, if section 15 names one (section 11)
COST=$($PY -I -B -c "import os, sys; sys.path.insert(0, os.getcwd()); import epa_backend as EB; print(' '.join(sorted(set(EB.cost_files(os.getcwd(), 'HEAD')) | set(EB.cost_files(os.getcwd(), sys.argv[1])))))" 0329456)
git diff --name-status "$RUNAT" HEAD | grep -v -E '^A[[:space:]]' | grep -v -E '^M[[:space:]]+(CHECKPOINT\.md|STATE_HISTORY\.md|SESSION_REPORT_2026-11-15_D148\.md|results/PREREGISTRATION_B58H\.md)$' | sed 's/^/STOP: a path present at T* changed: /'
git diff --name-only --diff-filter=A "$RUNAT" HEAD | grep -v -E '^(b58h_analysis\.py|test_b58h_analysis\.py|b58h_beside\.py|test_b58h_beside\.py|b58h_lambda_opt\.py|test_b58h_lambda_opt\.py|results/B58H_CHECK/.+|results/B58H_LAMBDA_OPT/.+|results/B58H_DESIGN/cturb_hw/.+|SESSION_REPORT_[^/]+\.md)$' | sed 's/^/STOP: not named by row 149 (3): /'
git diff --quiet 0329456 HEAD -- $COST; echo "cost files unchanged since B1: exit $?"
$PY -B epa_backend.py check; echo "epa_backend check: exit $?"
$PY -B -m unittest test_b58h_analysis test_b58h_beside test_four_engine_analysis; echo "unittest: exit $?"
$PY -B -m unittest test_engine_threading; echo "threading, alone: exit $?"
$PY -B -m unittest test_epa_backend.PreregistrationB58H; echo "Ta's live test: exit $?"
$PY -B verify_docs.py; echo "verify_docs: exit $?"
```

The gate passes only if no line prints STOP and every exit is 0. A failure is fixed by amending that unpushed commit
and running the block again. For row 153 (2)'s commit, `test_b58h_lambda_opt` joins the unittest line; for CK's record
alone, before AB exists, the unittest line runs `test_four_engine_analysis` alone.

**Step 3, the scoring, the analysis and the descriptive rows, on this laptop** (row 143 (1); section 6.9). The
returned zip is unpacked so that `runs/b58h_check_dt1`, `runs/b58h_dt1` and any `runs/b58h_check_dt1.broken<N>` sit in
this repository's `runs/`, which git ignores, with `SHA256SUMS` and the launch logs under `$OUT/training`. The scoring
starts only if the device's two environment records agree in section 11's fields; their comparison is recorded in
section 15. First, the check that the scoring may start (row 149 (4)):

```bash
cd /c/Users/badcl/Desktop/GRAD-project
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 PYTHONDONTWRITEBYTECODE=1
PY=/c/Users/badcl/Desktop/GRAD-project/.venv/Scripts/python.exe
OUT=/c/Users/badcl/grad_b58h                 # outside every git work tree; the returned files under $OUT/training
TSTAR=$(git log --diff-filter=A --format=%H -- results/PREREGISTRATION_B58H.md)
RUNAT="$TSTAR"                               # or F (section 11)
OLDPY=$(git ls-tree -r --name-only "$RUNAT" | grep -E '\.py$')
COST=$($PY -I -B -c "import os, sys; sys.path.insert(0, os.getcwd()); import epa_backend as EB; print(' '.join(sorted(set(EB.cost_files(os.getcwd(), 'HEAD')) | set(EB.cost_files(os.getcwd(), sys.argv[1])))))" 0329456)
AB=$(git log --diff-filter=A --format=%H -- b58h_analysis.py)
[ -n "$AB" ] && git merge-base --is-ancestor "$AB" HEAD && echo "AB committed: $AB" || echo "STOP: AB is not committed"
[ -z "$(git status --porcelain)" ] && echo "clean tree" || echo "STOP: the tree is not clean"
git diff --quiet "$RUNAT" HEAD -- $OLDPY; echo "no .py file of T* changed: exit $?"
git diff --quiet 0329456 HEAD -- $COST; echo "cost files unchanged since B1: exit $?"
git rev-parse HEAD; $PY -B b58h_beside.py --list; git log --diff-filter=A --format=%H -- b58h_lambda_opt.py results/B58H_DESIGN/cturb_hw   # section 15: HEAD, the routes present, the optimum's and the anchors' commits or none
sha256sum -c "$OUT/training/SHA256SUMS"      # every line OK, run from the repository root
```

Then (a), the primary scoring with the per-step records, and its commit. The records stay under `$OUT`; only the index
is copied:

```bash
AGENTS=$(for s in $(seq 0 19); do printf 'runs/b58h_dt1/%s ' blind_seed$s sighted_r0.5_seed$s sighted_r1.5_seed$s; done)
$PY -B evaluate.py --engine b58 --protocol d34 --reward-knock out --jobs 14 --scores-out "$OUT/scores_b58h.json" --records-out "$OUT/records" --out "$OUT/scores_b58h.txt" $AGENTS
mkdir -p results/B58H_RESULT && cp -n "$OUT/scores_b58h.json" "$OUT/scores_b58h.records.json" "$OUT/scores_b58h.txt" results/B58H_RESULT/
```

The records are 61 files, about 26.3 MB in all (`d148_figures.txt:80-81`). Then (b): section 6.8's `context` and
`analyse`, and their commit. Then (c)-(f), each written outside the repository first and committed when it ends, in
section 6.9's order, each command run alone and committed before the next one starts, so that the cut-off stops at
most what has not started:

```bash
# (c): decision 12's three rows (V's), the core rows (AB's), and the practice spread of seeds 0-4
$PY -B b58h_descriptive.py locked --engine b58 --set runs/b58h_dt1 --reward-knock out --out "$OUT/descriptive" --jobs 14 2>&1 | tee "$OUT/b58h_locked.txt"
$PY -B b58h_descriptive.py logged --engine b58 --set runs/b58h_dt1 --reward-knock out --out "$OUT/descriptive" --jobs 14 2>&1 | tee "$OUT/b58h_logged.txt"
$PY -B b58h_descriptive.py battery --engine b58 --set runs/b58h_dt1 --reward-knock out --out "$OUT/descriptive" --jobs 14 --grades results/conditions_b58h_dt1/conditions_grades.json 2>&1 | tee "$OUT/b58h_battery.txt"
$PY -B b58h_beside.py core --scores results/B58H_RESULT/scores_b58h.json --records "$OUT/records" --out "$OUT/beside" --jobs 14 2>&1 | tee "$OUT/b58h_core.txt"
PRACT=$(for s in 0 1 2 3 4; do printf 'runs/b58h_dt1/%s ' blind_seed$s sighted_r1.5_seed$s; done)
$PY -B evaluate.py --engine b58 --protocol d34 --practice --reward-knock out --jobs 10 --scores-out "$OUT/practice_b58h_s0-4.json" --out "$OUT/practice_b58h_s0-4.txt" $PRACT
# (d), (e), (f): each only if it has started by 23 November 2026 00:00 AST and its route was committed before (a)
$PY -B b58h_beside.py flat --set runs/b58h_dt1 --scores results/B58H_RESULT/scores_b58h.json --out "$OUT/beside" --jobs 14 2>&1 | tee "$OUT/b58h_flat.txt"
$PY -B b58h_beside.py road0 --set runs/b58h_dt1 --scores results/B58H_RESULT/scores_b58h.json --out "$OUT/beside" --jobs 14 2>&1 | tee "$OUT/b58h_road0.txt"
$PY -B b58h_beside.py settle --set runs/b58h_dt1 --scores results/B58H_RESULT/scores_b58h.json --out "$OUT/beside" --jobs 14 2>&1 | tee "$OUT/b58h_settle.txt"
$PY -B b58h_beside.py cturb --set runs/b58h_dt1 --scores results/B58H_RESULT/scores_b58h.json --out "$OUT/beside" --jobs 14 2>&1 | tee "$OUT/b58h_cturb.txt"
```

Every output is committed by explicit path, with this file's section 15 line, the session report and CHECKPOINT;
section 16 is written last.

## 15. Run log — filled in as it runs

*(empty at writing.)* Recorded here, each when the run that prints it has run, and each by lines below this heading
only: PR-B's gate output; the device guard's `RUN COMMIT: OK` line; the device's environment records before CK and
after the last run, and their comparison (section 11); the check run's printed check and its record's commit; any
amendment naming F, dated (section 11); for the training, the first and last hour beside W, every crash and restart,
and a check that every run's `meta.json` reads `git_head` the commit the run checked out (`T*`, or F) and `git_dirty`
false; AB's commit and its gates; each route's commit, row 152 (5)'s anchors' and row 153 (2)'s, or "not computed
(code)"; HEAD at the first scoring command and the routes present there (section 6.0); any choice a route's docstring
made for a descriptive row, and any gap of the primary analysis (section 6.0); the folders' transfer and their
SHA256SUMS check; the scoring and the analysis; each item of section 6.9 as run, "not run (time)" or "not computed";
and, at every commit after `T*` that touches this file, the output of section 14's check that no line above this
heading changed. Runs are named by section 4's lines ("the check line", "the training line"), never by quoting a
command.

**15 November 2026, PR-B's gate** (section 14, step 0). On the staged tree, before the commit: the cost-file list
held 51 paths; "cost files unchanged since B1: exit 0"; `epa_backend.py check` printed `[]`, exit 0;
`test_epa_backend.b58h_all_problems` on this file printed `[]`; the grids print and D148's figures print
reproduced, exit 0 each; "placeholders left: exit 1" (none); `verify_docs.py` exit 0, "All 170 checks pass (1172
figure mentions scanned in the documents).", CHECKPOINT.md 148 lines. At `T*`, `720587d`, before its push: the
commit that adds this file is HEAD (the two `git log` lines printed the same sha); "parent is Tb's commit"; "at
T*: exit 0" (the cost files); `epa_backend.py check` printed `[]`, exit 0; `git diff --stat 5d801be HEAD` listed
CHECKPOINT.md, SESSION_REPORT_2026-11-15_D148.md, STATE_HISTORY.md and this file, "4 files changed, 2043
insertions(+), 6 deletions(-)"; both prints reproduced, exit 0; "placeholders left: exit 1"; `verify_docs.py`
exit 0, all 170 checks pass (1172 figure mentions); `test_epa_backend.Preregistration` and `PreregistrationB58H`:
"Ran 7 tests in 20.597s", "OK", none skipped. `T*` was pushed to `GRA-test` the same day, `5d801be..720587d`.

**15 November 2026, `47e5854`** (`T*`'s record, the first commit after `T*` that touches this file; section 14 step
0's check for a later commit, before its push): "ABOVE SECTION 15: UNCHANGED SINCE T*"; row 149 (3)'s name-status
filter printed no STOP; "cost files unchanged since B1: exit 0"; `epa_backend.py check` printed `[]`;
`test_epa_backend.PreregistrationB58H`: "Ran 6 tests", "OK"; `verify_docs.py`: "All 170 checks pass (1172 figure
mentions scanned in the documents)." (its message).

**15 November 2026, CK** (the check line, at `T*`, in session `b58h_training_1` on Jad's PC; row 148). Every run's
`config.json` reads `started` 2026-11-15T18:28:04 and `finished` between 19:42:32 and 19:43:02 (the device's clock);
the launch log holds "all done in 75 min; every run finished", then only the launcher's `next:` hint (not run), and no
`FAILED` line. The printed check: "launch logs of this check run read: 1 | this session's launcher ended: True",
"crashed in this session: none | crashes over this check run: none", for each of the 10 runs "lr at end 0.0 snapshots
[10000, 20000, 30000, 40000, 50000] git_head is RUNAT True ok", "crashed folders, kept: none", and the last line
"CHECK RUN: OK". Its record (row 148 (8)), the record block's `ck_record` zipped by the sheet (the zip's sha256 begins
`be45289c`), checks on this laptop: `sha256sum -c SHA256SUMS` printed OK for each of the 42 files it lists. Every
run's `meta.json` and `config.json` read `git_head` `T*` and `git_dirty` false, `plant_sha` 36655cab94800e30,
`derived_sha` 326c0835548975e2 and `engine_sha` 023f5589215ee68e (section 3's and B1's); each `config.json` records
the lock's versions (Python 3.13.2, numpy 2.5.3, torch 2.14.0+cpu, stable_baselines3 2.9.0, gymnasium 1.3.0), 12 CPUs
and one OMP thread, and each `meta.json` Python 3.13.2. The record is committed under `results/B58H_CHECK/`, byte for
byte (its `.gitattributes` reads `* -text`), by the commit that adds this entry. Not in the record: the guard's
`RUN COMMIT: OK` line, which the guard prints to the screen only, and the environment record before CK, which comes
back with the return (the sessions' folders).

**15 November 2026, the training** (the training line, session `b58h_training_1`). It started at 19:43:23 AST on 15
November, by the message of Jad's agent (below), relayed by Ghassan; the sheet's `training_start.txt`, in the return,
is the record. That is inside W and before both latest starts (`results/B58H_DESIGN/d148_figures.txt:140-141`).

**15 November 2026, a deviation: an AI agent on the device.** Jad's own Claude Code, in Antigravity, ran on the PC
during CK and runs there during the training: its message to Jad, which Ghassan relayed on 15 November, reports CK's
result, sends `ck_record.zip` and the training's start to Jad's phone, keeps a watcher on the training window (titled
"B58H training - Visit 2 (do not close)"), and says it wrote `README.txt` and a report on the PC; it asks Jad to keep
Antigravity open. This is against the sheet's rule 3 ("No AI agent on this PC") and section 14 step 1's "The PC stays
idle". Which of the sheet's blocks it typed, and where its two files are, are asked of Jad. What it can change, and
where that is checked: the runs are seeded and train identically on this PC (B2, `cpu: IDENTICAL`), so an agent's load
moves the wall clock, not the agents; a file it writes inside the clone makes `git_dirty` true for every run that
starts after it (`fingerprint.py:658` counts untracked files), which section 15's check of every run's `meta.json`
reads at the return; an install or update shows in section 11's two environment records.

**15 November 2026, `59cb6f6`** (CK's record; section 14 step 2's gate, after the commit and before its push, as its
message gives it): the cost-file list 51 paths and no line printed STOP; "cost files unchanged since B1: exit 0";
`epa_backend.py check` printed `[]`; `test_four_engine_analysis`: "Ran 50 tests", "OK"; `test_engine_threading`,
alone: "Ran 33 tests", "OK (skipped=6)", the three EPA plants' uncalibrated checks;
`test_epa_backend.PreregistrationB58H`: "Ran 6 tests", "OK"; `verify_docs.py`: "All 170 checks pass (1172 figure
mentions scanned in the documents)."; "ABOVE SECTION 15: UNCHANGED SINCE T*"; in `results/B58H_CHECK/`, 42 lines OK.
Pushed the same day, `47e5854..59cb6f6`.

**15 November 2026, the agent's answers** (relayed by Ghassan the same evening). `README.txt` is
`C:\Users\admin\grad_device\visit2_claude\README.txt`, and the report is a file in Jad's own clone
(`C:\Users\admin\Documents\graduation project\GRAD-project`), untracked there: neither is inside the device clone,
which at 20:34 was at `T*` with `git status --porcelain` printing nothing. Jad typed none of the sheet's blocks. The
agent copied them, it says byte for byte, into `C:\Users\admin\grad_device\visit2_claude\blocks\`, and one script
there, `visit2_driver.sh`, runs them in the sheet's order in one Git Bash window, opened at 18:27:35, and stops where
the sheet says stop; nothing has been typed in that window since. CK ran from 18:27:56 to 19:43:17 by the agent's
account (the runs' `config.json`: 18:28:04 to 19:43:02). Before Step 1 the agent closed Brave, Chrome, Steam and
Discord, stopped other python processes on the PC ("SENAD's", with Jad's OK) and copied `tstar_pushed.txt` unchanged;
no browser or WhatsApp was opened on the PC (the record went to Jad's phone). The script runs Step 8's blocks itself
when the training's "all done" line says every run finished, and stops on a `FAILED` line or without an "all done"
line; sending the return stays with Jad. The answer sent back: Step 8 stays automatic (this laptop's recommendation,
under Ghassan's standing approval). From now on the agent only reads, about once a minute (the session's status file,
the launch logs, the process list). At B1 the agent ran the sheet too, at Ghassan's request then. The agent's copies
of the blocks and its scripts are asked for, to be compared with the sheet before Step 8 runs.

**15 November 2026, `864aa5a`** (the agent's answers; section 14 step 2's gate, after the commit and before its push,
as its message gives it): the cost-file list 51 paths and no line printed STOP; "cost files unchanged since B1: exit
0"; `epa_backend.py check` printed `[]`; `test_four_engine_analysis`: "Ran 50 tests", "OK"; `test_engine_threading`,
alone: "Ran 33 tests", "OK (skipped=6)"; `test_epa_backend.PreregistrationB58H`: "Ran 6 tests", "OK";
`verify_docs.py`: "All 170 checks pass (1172 figure mentions scanned in the documents)."; "ABOVE SECTION 15: UNCHANGED
SINCE T*". Pushed the same day, `59cb6f6..864aa5a`.

**15 November 2026, the agent's folder** (`visit2_claude_for_ghassan.zip`, sha256 beginning `ab7611ee`, as Jad's
message gave it; a copy of `C:\Users\admin\grad_device\visit2_claude\` taken at 20:47:49, with the agent's watcher and
a `MANIFEST.txt`). On this laptop, unpacked outside the repository and run nowhere: the 19 sha256 lines of its
`MANIFEST.txt` verify; its copy of the sheet is byte-identical to the sheet sent; its `blocks/01.sh` to `12.sh` are
byte-identical, in order, to the sheet's 12 bash blocks, of which the driver runs 01 to 11 (12 is the stale-lock
step). The window's log (`window.log`, the driver's `tee`) holds the guard's output, so the line above that called
`RUN COMMIT: OK` screen-only is superseded: Step 1 printed the fetch (`891e29a..47e5854`), "MATCH: T* read from git"
and 146G free; the guard printed `true`, "HEAD is now at 720587d", nothing from `git status --porcelain`, `T*`'s sha
and "RUN COMMIT: OK" (18:27:49). It also holds the environment record before CK (section 11's first record, 18:27:49):
"VERSIONS: match the lock"; Python 3.13.2 [MSC v.1942 64 bit]; build 26300.9974 (26H2); updates KB5054156, KB5121794,
KB5127694, KB5132061 and KB5132688; driver NVIDIA GeForce RTX 5070, 621.24; the sha256 of pip freeze beginning
298e94bf; the update pause ending 2026-11-28T16:52:09Z. The build, the two November updates, the driver and the pause
are B1's. The agent's `README.txt` adds: before Step 1, another Claude Code session's work ran on the PC ("SENAD":
`factory_sim live`, about 9 of 12 threads, from 18:24; `serve_final.py`; a headless Chrome), stopped at 18:26 with
Jad's yes, before Step 1 (18:27:35); Discord was closed by force; the NVIDIA app's auto-update setting was not found,
so "off" rests on Jad's word; the training's window was created through WMI, not as a child of Antigravity. The
watcher writes nothing: it reads `status.txt` and the launch logs every minute, the process list every 5 minutes
(`tasklist`) and every 10 minutes (`Get-CimInstance`).

**15 November 2026, the driver's review** (three reviewers and their skeptics, reading only). The driver reaches Step
8 exactly when the sheet would (`train_all.py:335-340` at `T*` prints "every run finished" only when no run failed);
nothing it or the watcher does moves the launch log's time, so the end time is the same; its Step 8 runs the sheet's
three blocks in the sheet's order, as Jad would. Found, none changing a result: (i) Step 8 stops only on a `tar.exe:`
line, so an error in its first block (the end time, `SHA256SUMS`) would not stop the zip; (ii) bash reads the driver,
and `source` the blocks, only when it reaches them, so any edit to `visit2_driver.sh` or `blocks/09.sh` to `11.sh`
before the end would change Step 8; (iii) after STOPPED or ALL DONE the window has lost the sheet's variables, so any
further step starts in a new window; (iv) a restart kills the watcher with the training, and the photographs stay the
only check; (v) `window.log` is outside the return's zip. So, asked of the agent: edit none of those files; check
their sha256 against `MANIFEST.txt`, reading only, before 18 November 17:00; after ALL DONE and before the return is
sent, check that `window.log` from Step 8 on holds no error line, that `SHA256SUMS` has one line per file of
`runs/b58h_check_dt1` and `runs/b58h_dt1`, and that `training_end.txt` is not empty; send `visit2_claude\` again
beside the return. A gap of section 14 itself, found by the same review: a run killed after `train.py` writes
`final.zip` but before its manifest is written would count as finished in a later session (`train_all.py:115`); at the
return, every run's `config.json` is checked for `learning_rate_at_end` and its manifest before the scoring.

**15 November 2026, `ef93b8d`** (the agent's folder and the driver's review; section 14 step 2's gate, after the
commit and before its push, as its message gives it): the cost-file list 51 paths and no line printed STOP; "cost
files unchanged since B1: exit 0"; `epa_backend.py check` printed `[]`; `test_four_engine_analysis`: "Ran 50 tests",
"OK"; `test_engine_threading`, alone: "Ran 33 tests", "OK (skipped=6)"; `test_epa_backend.PreregistrationB58H`: "Ran 6
tests", "OK"; `verify_docs.py`: "All 170 checks pass (1172 figure mentions scanned in the documents)."; "ABOVE SECTION
15: UNCHANGED SINCE T*". Pushed the same day, `864aa5a..ef93b8d`.

**16 November 2026, the return's route.** Ghassan chose a cloud link, one of the two routes the sheet's Step 8 gives
("a USB drive formatted exFAT or NTFS, or a cloud link, not WhatsApp"). The message for Jad and his agent, given to
Ghassan the same day to send through him (its sending is recorded here when it is made), under the sheet's line that a
new sheet "replaces this one where it says so": the agent's driver runs Step 8 itself after "all done in" and prints
ALL DONE, so nothing is typed or pasted in the training window; nothing on the PC before ALL DONE, so the space is
checked, or bought, from Jad's phone (about 18-20 GB is expected: `train.py:387` writes a snapshot every 10,000 steps,
and a 50,000-step run of `runs/extremes_dt1` takes about 36 MB, so the account needs at least 25 GB free, more than a
free Google Drive's 15 GB); before ALL DONE, a STOPPED line, a closed window or a restart is told to Ghassan and the
sheet's sections for it hold, and the upload then waits for his word; after ALL DONE the agent, reading only, checks
`window.log` from Step 8 on for error lines, `SHA256SUMS` for one line per file of `runs/b58h_check_dt1` and
`runs/b58h_dt1`, `training_end.txt` for content and `env_after_training.txt` for "VERSIONS: match the lock", and sends
Jad's phone as text the `.sha256` line, the zip's byte count, the `training started: ... ended: ...` line and that
VERSIONS line, or the failing line, which Jad forwards by WhatsApp, a channel apart from the cloud; Jad uploads only
after the checks pass, in a browser already on the PC, and installs nothing (rule 2 holds until Step 8 is done, and
the sheet counts Step 8 done only when the zip and its `.sha256` are sent); `b58h_return.zip`,
`b58h_return.zip.sha256` and the agent's `visit2_claude` go up as they are, never re-zipped, renamed or split, shared
with Ghassan's account only; once ALL DONE has printed, no block of Step 8 runs again, even if the window closes,
which replaces from then on the sheet's section for a window closed before Step 8 is done (it would make a second
session folder, a second environment record and a different zip); if the upload fails twice, the sheet's USB drive;
everything on the PC, and the cloud copy, stays until Ghassan says otherwise. A browser opened after ALL DONE is
outside section 11's comparison: Step 8's second block makes the record after the training before its third block
makes the zip, which holds it. The PC is free when Ghassan writes that the zip arrived whole, after this laptop has
downloaded each file on its own and checked the zip's sha256, its folder list, `sha256sum -c` of its `SHA256SUMS` and
the two environment records. A layout to place at the return: Step 8 writes `SHA256SUMS`, `training_end.txt` and
`env_after_training.txt` into the session folder of the window it runs in (`$OUT`: `~/grad_device/b58h_training_1/`,
unless a restart or a closed window makes a later one), which the zip holds at its top level beside `runs/` and any
other `b58h_training_N` folder, while step 3 reads `$OUT/training/SHA256SUMS`; the zip is unpacked outside the
repository, `sha256sum -c` runs there first, and the placement under `$OUT/training` (Step 8's `SHA256SUMS` at
`$OUT/training/SHA256SUMS`, byte for byte) is recorded in this section when it is made.

**16 November 2026, `b65b579`** (the return's route; section 14 step 2's gate, after the commit and before its push,
as its message gives it): the cost-file list 51 paths and no line printed STOP; "cost files unchanged since B1: exit
0"; `epa_backend.py check` printed `[]`; `test_four_engine_analysis`: "Ran 50 tests", "OK"; `test_engine_threading`,
alone: "Ran 33 tests", "OK (skipped=6)"; `test_epa_backend.PreregistrationB58H`: "Ran 6 tests", "OK";
`verify_docs.py`: "All 170 checks pass (1172 figure mentions scanned in the documents)."; "ABOVE SECTION 15:
UNCHANGED SINCE T*". Pushed the same day.

**17 November 2026, a break of row 149 (3), undone the same day by `588de29`.** Eleven commits of 17 November (`9b19be4`
to `8800572`, pushed) changed paths present at `T*` that row 149 (3) does not name: `REFERENCES.md`,
`docs/literature/READING_LIST.md` and `docs/literature/references.bib`, `results/VALIDATION_PLAN.md`, the presentation,
the supervisor note, and the source strings of five `engine_specs/*.toml`, which are cost files, frozen from B1's
git_head `0329456`. They changed references and source notes only, and every engine value was unchanged (the B58's
engine_sha at `8800572` was `023f5589215ee68e`, as at `b65b579`), but at `8800572` `epa_backend.py check` refused and
the name-status check of section 14 step 2 would have printed STOP. Ghassan chose to revert them: `588de29` returns
every path they touched to its content at `b65b579` (pushed 17 November). No command had loaded an agent or a checkpoint
of this study. They are re-applied by reverting `588de29`, the documentation paths after the first scoring command and
the `engine_specs` paths after the last scoring. The same day, `d05e27d` recorded in the session report (section 17)
three analyses chosen during training, before any score: each is post hoc (VD:394), reported under a post hoc heading
beside the preregistered readings, deciding nothing.

**18 November 2026, the training's end.** The launch log's last line: "all done in 3921 min; every run finished"
(`train_all.py`'s print when no run failed). The sheet's records in the return: `training_start.txt` 2026-11-15 19:43:23
+0300 and `training_end.txt` 2026-11-18 13:04:24 +0300, both inside W, whose end is 20 November 00:00 AST
(`epa_backend.W_LAST`, `results/B58H_DESIGN/d148_figures.txt:14`). One session folder, `b58h_training_1`: no crash, no
restart and no second session. Every run's `meta.json` reads `git_head` `720587d` (`T*`) and `git_dirty` false (60 of
`runs/b58h_dt1`, 10 of `runs/b58h_check_dt1`). The agent's driver ran Step 8 itself and printed ALL DONE at 13:11:33;
nothing was typed in the training window. Its checks, reading only (`checks/endcheck_after_all_done.txt`): no error line
in `window.log` from Step 8 on; `SHA256SUMS` 6480 lines for the 6480 files of the two folders; no broken folder;
`training_end.txt` not empty; `env_after_training.txt` "VERSIONS: match the lock"; "END CHECKS: OK". Its hash checks of
the driver and blocks 09-11 against `MANIFEST.txt` show them unchanged throughout. Its folder came back as
`visit2_claude_for_ghassan_2.zip`, unpacked on this laptop outside the repository and run nowhere: the 27 sha256 lines
of its `MANIFEST.txt` all match, and its `VISIT2_SHEET.md` is byte-identical to the sheet sent.

**19 November 2026, the return, checked on this laptop.** Jad's agent asked which route; Ghassan answered the cloud
link (Jad's university OneDrive). Jad uploaded `b58h_return.zip` and `b58h_return.zip.sha256` in a browser; this
laptop downloaded each file on its own. Checks, reading bytes and JSON only (none loads an agent or a checkpoint):
- the zip is 16,819,651,277 bytes, as the agent's line gives it, and its sha256 (beginning `fd63d23a`) equals the
  `.sha256` file's, `MANIFEST.txt`'s and `window.log`'s;
- its folder list: `b58h_training_1/` (Step 8's session folder) and `runs/`, with `runs/b58h_dt1` (60 runs, 6240
  files) and `runs/b58h_check_dt1` (10 runs, 240 files); no `.crashed<N>` or `.broken<N>` folder; no path outside the
  zip's root;
- unpacked outside the repository (`/c/Users/badcl/grad_b58h/unpack`), `sha256sum -c b58h_training_1/SHA256SUMS`:
  6480 OK, none failed;
- the two environment records, `env_before_ck.txt` (15 November 18:27:49 +0300) and `env_after_training.txt`
  (18 November 13:05:02 +0300), are identical but their first line, in every field section 11 names:
  `check_training_device.py`'s version lines (python 3.13.2, torch 2.14.0+cpu, "VERSIONS: match the lock"), the
  interpreter, the Windows build and revision (26300.9974), the five installed updates, the driver (621.24) and the
  sha256 of `pip freeze`. Section 11's row for differing records does not apply;
- the gap of 15 November (a run killed between `final.zip` and its manifest): every run's `config.json` holds
  `learning_rate_at_end` (0.0 in all 70) and names `checkpoint_average.json`; every manifest has schema
  `checkpoint-average/1` and five snapshots whose sha256 match their files; every run has `final.zip`; the training's
  runs read 450 000 steps and the check run's 50 000.
Placement: `runs/b58h_dt1` and `runs/b58h_check_dt1` moved into this repository's `runs/`, which git ignores; the
session folder moved to `/c/Users/badcl/grad_b58h/training`, so Step 8's `SHA256SUMS` is `$OUT/training/SHA256SUMS`,
byte for byte equal to the zip's copy; from the repository root, `sha256sum -c "$OUT/training/SHA256SUMS"` printed
6480 OK. The message that the zip arrived whole, which frees the PC (the zip there and the cloud copy are kept until
the scores are committed), was given to Ghassan to send.

**19 November 2026, AB (ORDER step 22a)**, committed with this entry. Its commit and its gate's output (section 14's
step 2 check, run after the commit and before its push) are in its message, and are recorded here at the next commit
that touches this file. AB is four new files at the repository's root: `b58h_analysis.py` with `test_b58h_analysis.py`,
and `b58h_beside.py` with `test_b58h_beside.py`, whose one route is `core` (rows 150 (i), 150 (v) and 151). The
commands are section 6.8's: `context --scores --out`; `analyse --scores --context --out --report`; `core --scores
--records --out --jobs`. `b58h_beside.py --list` prints `core`. No score of this study existed while AB was written,
and no command loaded an agent or a checkpoint. AB ran only on synthetic documents in temporary folders. Its tests
patch `evaluate.load_agent` and `read_agents` to raise, and an audit hook refuses any open or listing under
`runs/b58h_dt1` and `runs/b58h_check_dt1`. `core` loads no agent at all.

How it was checked, by agents on this laptop, in three rounds:
- Round 1: two writers. Per module, a reviewer recomputed every printed number with code of their own, and a mutation
  tester ran single edits against the tests: `b58h_analysis.py` 64 mutants, 24 surviving; `b58h_beside.py` 87, 21
  surviving. Every review finding (5 and 6) was fixed, and every survivor was killed by a new test.
- Round 2: the 45 survivors were re-applied, and all were killed. Fresh mutants on the fixed code (26 and 36; 20 and 16
  survived) and a second review found two defects, both on failure paths, and both were fixed with the rest:
  - an output that could not be created left the other one written;
  - a run that failed after the roads check passed was printed as a failed roads check.
  One reading was added (G11 below).
- Round 3, on round 2's changes only. An independent recomputation of section 7's sentences on 83 synthetic
  documents found 0 mismatches. Fresh mutants (31 and 30; 15 and 13 survived) and a review found more defects,
  all on failure paths, each fixed with the rest:
  - a write that failed after the files were open kept the output already written in full; now every file the
    command opened is removed;
  - a record's dt of another type, or an index nested too deep for JSON, crashed `core` instead of reading "not
    computed";
  - a refusal's text over several lines split a printed line.

The choices AB's docstrings fix before any score (section 6.0). None can move d, Δ, the band, the status or a verdict.
The docstrings' own text governs; in short:
- `b58h_analysis.py`:
  - C1: the CLI is section 6.8's options. A refusal prints "REFUSED: <reason>", nothing written.
  - C2: each output is written once. All are created before any is written, and a refused command leaves none.
  - C3: paths are repository-relative. git_head is 7 hex digits.
  - C4: `context` also requires the scores committed at HEAD.
  - C5: `analyse` rebuilds the context and refuses one that differs (floats to 1e-12). The raw sha256 is not compared.
  - C6: `X2_RESULT.txt:24` must sit under its no-knock section, with n = `FEA.PILOT_PAIRS`.
  - C7: the companion's smallest and largest κ_L1 are taken by value; a tie goes to the first name.
  - C8: the report's order.
  - C9: the number formats.
  - C10: 9.1's validator of the scores' delivery block.
  - C11: 9.1's worst road and the seeds without a demand step.
  - C12: section 10 prints "not read: <reason>" for an absent, uncommitted or unparsed line.
  - C13: the forbidden-phrase check on AB's own text.
- `b58h_beside.py`:
  - core takes no engine or knock option: they are the scores'.
  - The derived paths: the records index, and the text report beside the scores.
  - The refusals of the whole command. Inside a row, a failure makes that row read "not computed" and the rest runs.
  - Current-grade's run and its parallel run, and the roads check against the scores' `arrays_sha256`.
  - The trace `current_grade.npz`.
  - Control 1: exact equality.
  - Control 2: the one line after `evaluate.py`'s cut header, compared whole.
  - Control 3: absolute 1e-6 per road in both readings, roads in order.
  - s in both forms and both readings, with its per-arm statistics.
  - The hand-written savings, their mean form recomputed over the neutral run.
  - Row 153 (1)'s tuned bests: each family's largest evaluate-form lines and the two frontier lines, verbatim.
  - Decision 13's count: `grids_b58.txt` lines 99-100, verbatim.
  - 9.5 (v)'s three figures per seed, the seeds without demand dropped and named.
  - 9.6's integrity checks.
  - 9.6's limits, 778 and 804 °C, typed with their citations.
  - 850 °C in both readings PR-B's words allow (the knee and 850.0), each with its own trigger.
  - The figures, and the printed decimals.
  - The with-knock label on every with-knock line.
  - LF outputs, so each file's raw sha256 equals its sha_text.

The gaps of the primary analysis (section 6.0): every reading the words allow is printed, and none is called primary.
In `b58h_analysis.py`:
- G1: a MODEL-LIMITED flag that differs between the companions, or between either companion and the primary run, is
  printed by name. Every run's flag is in the flags block.
- G2: Δ's mean form, with its own interval and two-sided sign test, deciding nothing.
- G3: Δ's prediction. The no-knock C_u is printed beside both readings, and C_u.knock beside the with-knock Δ.
- G4: section 7's sentences are rendered beside the verbatim verdict lines.
- G5: section 10's values, each with its file and line.
- G6: 9.1's worst road, per seed and as the arm's largest.
- G7: "wholly below 0" for the verdict's interval, and in their brackets for the with-knock and mean-form intervals.
- G8: "MODEL-LIMITED under the other reading of 'at b'" on every verdict of either test, in both readings.
- G9: another reading of "at b" is detected both by the context's label and by the band recomputed.
- G10: φ at a median cut of 100 % or more is refused.
- G11: the ceiling's with-knock reading (`roads.json` `by[r].a.knock.mean`) is printed in the bracket beside C. C is the
  no-knock reading's and stays the context's.

`b58h_beside.py` has no gap: it computes descriptive rows only.

**20 November 2026, AB's gate** (`dd49844`, committed 04:52:22 +0300; section 14 step 2, after the commit and before its
push, as its message gives it): the cost-file list 51 paths and no line printed STOP; "cost files unchanged since B1:
exit 0"; `epa_backend.py check` printed `[]`; the unittest line (`test_b58h_analysis`, `test_b58h_beside`,
`test_four_engine_analysis`): "Ran 183 tests", "OK"; `test_engine_threading`, alone: "Ran 33 tests", "OK (skipped=6)";
`test_epa_backend.PreregistrationB58H`: "Ran 6 tests", "OK"; `verify_docs.py`: "All 170 checks pass (1172 figure
mentions scanned in the documents)."; "ABOVE SECTION 15: UNCHANGED SINCE T*". Pushed the same morning. AB was committed
after the training had ended (18 November) and after its folders were back (19 November).

**20 November 2026, the first scoring command: item (a).** Ghassan chose to start the scoring once AB was pushed, as
section 6.0 and section 11's table say ("The scoring waits for AB ... It waits for no route"; the row "AB is not
committed when the training's folders are back"). No route of step 22b had been written: their maps and designs, written
by agents on 19-20 November, stay outside the repository, and no code is written for them after this command. So items
(d), (e) and (f) read "not computed (code)", row 152 (5)'s anchors read "not computed", and row 153 (2) reads "not
computed (code)" (sections 6.0, 6.9, 9.7 and 9.8). Section 14 step 3's check, run at 05:20:40 +0300 (its print kept as
`$OUT/b58h_scoring_check.txt`): "AB committed: `dd49844`"; "clean tree"; "no .py file of T* changed: exit 0"; "cost
files unchanged since B1: exit 0"; HEAD at the first scoring command `dd49844`; `b58h_beside.py --list` printed `core`,
the only route present; the optimum's and the anchors' commits: none; `sha256sum -c "$OUT/training/SHA256SUMS"`: 6480
OK. No python process ran before it. Item (a), the primary scoring of the training line's 60 agents with the per-step
records, ran from 05:23:16 to 09:13:37 +0300 (3 h 50 min) at 14 jobs and exited 0, with no warning or refusal printed.
Its fingerprint reads plant_sha `36655cab94800e30`, derived_sha `326c0835548975e2`, engine_sha `023f5589215ee68e`,
git_head `dd49844` and git_dirty false. The records are 61 files, 26 MB, under `$OUT/records`; the scores' sha256 begins
`04d5472b`, the index's `cee8d1cc`. The scores, the index and the text report are copied to `results/B58H_RESULT/`, byte
for byte, and committed with this entry.

**20 November 2026, item (b): the analysis.** At `5318b13` (item (a)'s commit, pushed), on a clean tree, section 6.8's
`context` then `analyse` ran from 09:19:07 to 09:19:19 +0300, each exit 0, each output written once:
`results/B58H_RESULT/context_b58h.json` (sha_text beginning `fe1487e0`), `analysis_b58h.json` (`a36c1f9d`) and
`analysis_b58h.txt` (`af941cbf`), committed with this entry. The context was made for the scores' sha_text (beginning
`04d5472b`) and the reading of 'at b' "kappa 1 in the contract's form"; its status is the rule's output, exploratory
(1.5576 x s_p 20.56 = 32.024 against s* 9.06868); every record it read was committed at HEAD. `analyse` re-read the
records at HEAD, rebuilt the context and found it equal, ran four_engine_analysis five times, and found every d > 0
verdict the same under every band. Its verdicts, intervals, Delta, band, flags, section 9.1 and section 10 are in the
report as written; section 16 states the outcome after item (c).

**20 November 2026, item (c), first command: decision 12's locked climb** (V's `b58h_descriptive.py locked`, sections
9.2-9.4). At `ea18150`, alone, from 09:23:33 to 12:24:48 +0300 (3 h 01 min), exit 0, at 14 jobs: 60 agents, 20 cases
each, each a declared transfer (every FATAL field but scenario and episodes_sha the live one, row 147 (11)); no refusal
or failure printed. Its `b58h_locked.json` (sha256 beginning `ed4bba4f`) and its printed `b58h_locked.txt` are copied to
`results/B58H_RESULT/` and committed with this entry.

## 16. Outcome — added after the result, never above this line

*(empty at writing.)*
