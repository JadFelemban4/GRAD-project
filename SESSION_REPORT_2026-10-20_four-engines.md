# Session report — 20 October 2026: four engines, their data, and how much to train

Ghassan's session, on branch `GRA-test` (off `main` at `cf43fbb`, which carries
Jad's merge of 19 October). Started on `main` with drive C's analysis script
(`903da5a`, `SESSION_REPORT_2026-10-19_driveC-rule.md` section 5).

## 1. What was asked, in order

1. If more car data cannot be collected, what can the simulation do instead?
   Answered in the session: the H/τ test is simulated plants against each
   other, so it needs no more car data; what a data wall removes is plant 1's
   realism (knock, spark under boost, oil), which becomes stated limitations.
2. Find places with enough public data to build more plants, and then: the
   plants are to be **engines**, at least three.
3. Build all of them (B58, Mazda, Honda and the Ford), each in its own car, on
   a new branch `GRA-test`; the B58's drives continue.
4. How much training: episodes, agents, steps.

## 2. Decisions written (results/VALIDATION_DECISIONS.md section F; Desktop copy `decisions_2026-10-20.md`)

- **24, the plants:** four engines, each in its own car: the B58 (GR Supra, our
  logs); the Mazda 2.5 L turbo (2016 CX-9); the Honda 1.5 L turbo (EPA's L15B7
  map, in the 2018 Accord body); the Ford 2.7 L twin-turbo V6 (2015 F-150).
  Ghassan: agree, 20 Oct. Jad: open.
- **25–35, how the test trains:** when training may start relative to drive C
  and rule 2; per-engine verdicts, never pooled; three arms per engine at
  matched H/τ; the table backend with scoring on the exact plant; the training
  recipe; seeds and the test; the frozen B58; Python; the knee per engine; the
  climb per car; validation thresholds fixed before calibrating. Every row has
  a recommended answer; both columns open.

## 3. The data (outside git: `C:\Users\badcl\Desktop\GRAD-engine-data`)

152 files, 2,488,432,113 bytes, each hashed on arrival and listed with its URL
in `MANIFEST.csv`; `CATALOGUE.md` there says what every file holds.

| source | what it gives |
|---|---|
| EPA NCAT engine benchmarking packages, Mazda 2.5 T, Honda L15B7, Ford 2.7 TT | steady-state maps (210 / 190 / 180 points) with torque, fuel, manifold pressure, spark, lambda, turbine-inlet and catalyst-inlet temperature; high-load holds (61 / 65 / 19 pairs) that show each ECU's protection; the ALPHA engine files (displacement, cylinders, compression) |
| Argonne D3, 2016 Mazda CX-9 | 70 tests at 10 Hz, 37.2 h: WOT, 0/3/6 % grade, US06, hot cell; no exhaust temperature of any kind |
| Argonne D3, 2018 Honda Accord 1.5 T | 56 tests, 30.2 h, including a 25 % grade climb to derate with the ECU's catalyst temperature; its engine is a sibling of the Civic's L15B7 (143 kW against 130 kW), not the same calibration |
| EPA Test Car List, 2015–2020 | equivalent test weight and target road-load coefficients for all four cars |

What no source has: a turbine **housing** temperature over time, for any
engine; driving data for the Ford 2.7. So every engine's housing τ stays
assumed, as the B58's is.

One finding about our own car: EPA's 2020 Supra row gives a road load 15–22 %
above the model's (`engine_env.py` Vehicle: 1520 kg, Cd·A 0.66, crr 0.011,
which `REFERENCES.md` already marks unsourced). Decision 31 keeps the model's
values for the four-engine test; a change is a declared ablation later.

## 4. How much training — the research pass of 20 October

Six strands (the project's own results and timings; the statistics
literature on seeds; the SAC literature on steps; the code design; the data;
the cars), two syntheses and two reviews against the rules. Numbers marked
*scratch* were computed in the pass from committed files or local records and
are not yet printed by a committed script (mistake 22): treat them as
estimates until one is.

- **Seeds carry the error, not steps or episodes.** 84–94 % of the variance of a
  seed pair's difference is seed to seed (*scratch*, from the committed per-seed
  cuts and the twenty-episode bootstrap). Pairing the two arms by seed removes
  none of it: their correlation is −0.14 in X1 and +0.09 in X2 (*scratch*, from
  `results/X1_RESULT.txt` and `results/X2_RESULT.txt`). More evaluation
  episodes barely help.
- **Steps per agent: 450 000 (500 episodes).** X2's hot training cut stopped
  rising after about 400–500 episodes (*scratch*, post hoc); its preregistered
  check found no convergence (`results/x2_convergence.txt`), and its policies
  kept wandering at a constant learning rate. X1's 55 episodes ended
  mid-learning.
- **Seeds needed at today's spread** (one comparison, 80 % power at the MEI of
  5.43 points): 143 a side by the exact sign test at X2's paired sd of 20.51
  (`results/X2_RESULT.txt`), about 90 by a paired t-test; 209 and about 131 at
  X1's 24.78 (`power_analysis.py`; the t figures *scratch*).
- **Throughput:** about 82 steps/s in aggregate on the team laptop with 23 runs
  at once (`results/PREREGISTRATION_X1.md` section 10), about 58 with 10
  (`results/PREREGISTRATION_X2.md`). A tabulated B58 trains 6–8× faster per
  run, with every frozen-twenty cut within 1.5 points of the exact plant
  (*scratch*, one process on a loaded machine; its rate with many runs at once
  is not measured).
- **What fits before the analysis freeze of 11 November** (the team's gate G5):
  about 20 seeds per arm × 3 arms × 4 engines × 450 000 steps = 108 M steps,
  roughly 4–7 days on a table if its many-run rate holds, about 15–17 days on
  the exact plant. At today's spread that detects a preview benefit of about
  twice the MEI per engine and leaves small effects inconclusive; halving the
  spread would bring the MEI itself within reach of about 23 seeds a side
  (paired t). Decision 29 lists the three changes most likely to do that.

## 5. Build step 1 (in progress when this was written)

The plant takes an explicit engine and car (`engines.py`, `engine_specs/`),
with no silent default (mistake 1), and the B58 built that way must be
bit-identical to `cf43fbb`. Measured so far against a `git archive` of
`cf43fbb` on one interpreter, values compared byte for byte: units, seven
training-road episodes of each family, the premise, the random-road and
wide-air roads and three conditions rollouts all **BIT-IDENTICAL**, and
`test_reward.py` prints the same output. The check can fail: one ulp on the
housing heat capacity or on the car's mass, through the new objects, comes out
different. The certificate (`results/B58_IDENTITY.md`) and the reviews follow;
nothing of build step 1 is committed yet. The first attempt stopped on a usage
limit mid-work; its edits were kept and backed up, and the work resumed from
them.

The data are also in the branch's working tree: `logs/epa/` (18 EPA files,
15.5 MB, byte copies with their manifest), `epa_map.py` → `data/engines/`
(generated tables), `engine_specs/cars/` (published values with sources),
`fetch_engine_data.py` (re-downloads and verifies the outside data).

## 6. Found on the way

- The laptop's `.venv` is Python **3.13.2**, and X1 and X2 recorded 3.13.2 in
  their configs; rule 4 says 3.12 and `CHECKPOINT.md` quotes `plant_sha` "(Python
  3.12.10)" from another machine. Decision 32.
- With one shared housing, the four engines' τ cluster at about 39–60 s
  (estimated), so one preview horizon cannot tell H/τ from τ: decision 27.
- With the B58's housing-to-gas ratio, the hottest EPA turbine-inlet gas puts the
  three new housings at about 720–780 °C, under the 850 °C knee (an estimate to
  recompute on each calibrated plant): decision 33.

## 7. Not done, and why

- The three new engines are not calibrated yet (build step 2), and the cars'
  gearboxes, the Accord's CVT, the tables, the validation and the
  preregistration follow it.
- Nothing trained; nothing trains until decisions 24–35 have both columns, gate
  item 6 (drive C) is met or amended, and a preregistration is committed.

## 8. 21 October: why every trained agent fell short, and build step 1 committed

**Ghassan's question:** were the agents short of training, or short of data? His
view: they never trained as much as they should, and the data is not complete.
Tested against the committed results by four read-only strands (one of them
arguing his view); the answer given to him in the session, in plain terms:

- **"Not trained enough" is true as a fact and wrong as the cause.** Phase D and
  D2 trained 11 episodes and X1 55, and no run ever settled by its own rule. But
  the two experiments that trained longer changed nothing that mattered: C4 at
  six times D2's steps widened the paired spread (98.8 → 139.9 damage units,
  `results/C4_RESULT.txt`) and still read no preview effect; X2 at 21.6 times
  X1's steps read INCONCLUSIVE with the spread barely moved (24.78 → 20.51) and
  failed the logged-drive check more often (0 of 10 against 1 of 46). X2's agents
  reached about 70 % protection at some checkpoint and lost it at a constant
  learning rate (*scratch*).
- **"The data is not complete" is true as a fact and wrong as the cause.** The
  agents train on simulated roads without limit; car data sets the simulator's
  realism. Where a missing measurement does bite is one mechanism: the model
  ECU's one-second spark lag makes a knock spike at every sudden load rise, which
  carries most of the life reward in cool running and teaches the agents to burn
  4–10 % more fuel on the car's drives; with spark scheduled on the current load,
  0 of 300 sampled spikes cross the knee (*scratch*). Drive C part C2 decides it.
- **The main reason: the scored climb cannot show a preview effect.** `python
  preview_ceiling.py` (committed, `results/preview_ceiling.txt`, from the
  committed traces): the most a cooler housing at the climb start can save is
  0.13 points of cut with the agent's own levers, 0.42 with unlimited preview, 1.19
  even with the exhaust held at ambient for the 30 s, against the MEI of 5.43;
  about 92 % of the turbine damage accrues more than 3 τ after the climb starts,
  when both arms see the same grade. X1's and X2's nulls were the right answer
  for that road. The recommended four-engine test repeated the road, so decisions
  27 and 34 were revised (`e9e16ed`, then 34's figures from the script).
- **What bad training did cause:** the seed-to-seed spread and the collapses. The
  scored condition filled 0.42 % of X1's training steps and 0.028 % of X2's, and no
  training episode held it for three minutes (*scratch*); the learning rate never
  fell.

**Build step 1, committed on `GRA-test`.** Engine and car objects with no silent
default, fingerprint schema 3, every caller threaded, the learning lab included;
the B58 bit-identical to `cf43fbb` at every certificate level L1–L8, and the check
shown able to fail (`results/B58_IDENTITY.md`, with its tools archived beside
it). Two reviews (correctness and the project's rules) found 21 issues; all were
real, 17 fixed outright, three in part, one pre-existing on `main`
(`results/training_roads.json` stale since `75ca65f`). Suite failures that remain
also fail on `cf43fbb`, each named in the certificate.

**Training moves to another device** (Ghassan, 21 October): nothing trains on the
team laptop. `requirements-lock.txt` pins the laptop's environment, and `python
check_training_device.py` checks a machine against it; `--identity` and
`--compare` decide whether a second machine trains identical agents (decision 32).
Its comparison was checked both ways on X1's runs: a run against itself reads
IDENTICAL, two different agents read NOT IDENTICAL (103 differences). The
`--identity` run itself was not run here.

## 9. 21 October, later: the training device's benchmark, every decision answered, the validation contract, the reading list

**The benchmark runs on the training device, not here** (`499bd00`). Ghassan: the
benchmark is "to do on the new device and see if it's faster to train them on the
CPU or GPU". `python benchmark_training.py --device cpu` in a CPU environment and
`--device cuda` in a CUDA one, then `--merge` of the two files. It measures a lower
and an upper bound of each device's training rate, with the repeats interleaved,
and names a device only if its lower bound beats the other's highest upper bound;
otherwise its answer is to keep the CPU. It also checks that seed 0 trains the
identical agent twice. `train.py`, `train_all.py` and `run_phase_d.py` take a
required `--device` and refuse a mismatch; on CUDA they need
`CUBLAS_WORKSPACE_CONFIG=:4096:8` and deterministic algorithms. None of it was run
on this laptop.

**Every decision answered.** Ghassan, 21 October: "Me and jad agreed with what you
decided" and "Yes covers everything". Decisions 1-35 carry both columns, Jad's as
reported by Ghassan (Desktop copy `decisions_2026-10-21_answered.md`). The
contract's own review raised three more, 36-38 (section G): adopted on Ghassan's
delegation ("fix all the way you see fit"), Jad's column open (Desktop copy
`decisions_2026-10-21_G.md`).

**The validation contract of decision 35, committed before any fit**
(`results/ENGINE_THRESHOLDS.md` and `.json`, version 3, `ef5e14e`). It holds the
accuracy the Mazda, the Honda and the Ford must show on held-out EPA rpm lines,
each derived from its consequence on the MEI, and the gates of every engine's
table. Its generator, `engine_thresholds.py` and `thresholds/`, is committed beside
it; `--check` exits 1 if either file differs from what the code writes. An
independent re-run found three faults, none a threshold, and all three are fixed:
a bound rounded to nearest (section 1.5's thermal-only agreement, now rounded up to
0.48), wall-clock times written into what the contract hashes (they are now in
`run.json` only, and step 6 refuses an output that holds one), and step 7's need
for a git checkout (documented; it now stops with a message). After the fixes a
full re-run from scratch gave back every step output and both contract files byte
for byte. Nothing has been fitted: no model was run on an EPA row.

**The reading list** (`docs/literature/READING_LIST.md` and `references.bib`,
`e4e7e4a`). 183 sources for the literature review and for the systematic validation
of the simulator, each with its DOI or link, its free full text where one exists,
the way to get it from Jeddah and its price: 121 free, 13 through the Saudi
Digital Library, 18 that depend on what the SDL login shows, 31 to buy. $392.00
(SAR 1,470.00) has to be paid whatever the login shows: five ASME papers, five SAE
papers and ASME V&V 20. If SDL lacks ScienceDirect, SAGE and the other unconfirmed
databases, the MUST items cost $777.96; if the library or the authors supply the
papers, only V&V 20's $72.00 is left. Two checks by AI agents compiled and
re-checked it; no team member has read the sources yet, and none is cited until
someone has. Hu et al. 2019 (C18) was raised to MUST after the checks, because the
project's own notes call it the work closest to this one.

**Found on the way.**

- `verify_docs.py`'s retired pattern for the old 2.3 % load residual matched the
  contract's 12.3 % (S1b): `\b` added, `drift_test.py` 18 of 18 after it.
- `drift_test.py`'s first run was cut at row 7 of 18 by a time limit on the
  command, and the pipe still reported success (the exit code was `tail`'s). It was
  run again to the end. Mistake 19's kind: a result that could have come from the
  fallback.

**Not done, and why.**

- Build step 2, the calibration of the three EPA engines: designed first (five
  readers, three independent designs, an adversarial review of each, one plan),
  then implemented and reviewed before the in-sample stage, because the held-out
  statistics are computed once.
- The benchmark and the identity check on the training device: Ghassan runs them
  there.
- Drive C's repeat: Ghassan's, on `main`.
