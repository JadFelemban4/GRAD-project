# Session report — 19 October 2026: drive C's decision rule, proposed blind

Ghassan's session, on `main`. Drive C had been driven on 18–19 October without
covering either part, and Jad's side asked for the decision rule's numbers to be
fixed before the repeat. This session researched and proposed them, without
reading any drive C log.

## 1. What was done

- **Research, blind.** A multi-agent workflow (nine agents): five research
  strands (Bosch knock-control documentation and papers; the retard channel's
  noise in the old logs; the statistics; the project's own sensitivity; the
  simulator's half and full steps), a synthesis, and three independent reviews
  (blindness, statistics, engine realism). Every strand was barred from drive C
  files and from computing the retard on any log; the shared reader refused
  drive C file names. The reviews changed the synthesis in four places that move
  numbers: the miss rate (the logged actual angle is most likely one cylinder at
  a time), only the late window decides (pairing can manufacture a pull in the
  first second and at the pedal release), the pairing itself (min of the
  bracketing targets), and the knee's estimator and uncertainty (censoring; one
  definition of u_D).
- **`results/DRIVE_C_RULE.md`**: the proposed rule, with its disclosure (the data
  predate the rule), the blindness guards, exact definitions, the C2 verdict and
  what each verdict triggers, C1's knee and spark triggers, what the repeat
  drive must deliver, and what is still open.
- **`drive_c_rule_numbers.py`** → `results/DRIVE_C_RULE_NUMBERS.txt`: every
  number the rule quotes. The C2 cuts (24 valid steps: pulls ≥ 6, does not ≤ 3,
  errors 2.9 % and 2.2 %) were recomputed independently in this session and
  agree with the engine review's table at 16, 20, 24 and 28 steps; the spark
  requirement (−0.85° of boosted schedule for every car: +9.95 K, ×1.248, R1's
  basis); the knee's effect on the climb's knock damage; the charge-temperature
  input uncertainty (0.86° spark, 0.032 KI).
- **`results/VALIDATION_DECISIONS.md`**: decisions 14–23 added (section E), each
  with a recommended answer and an empty column for Ghassan and for Jad; a copy
  on the Desktop, `decisions_2026-10-19.md`.
- **`logs/DRIVE_PLAN.md`**: drive C marked driven once and to be repeated; its
  instructions revised to match the rule (channel order, 35 steps in blocks,
  rpm bands per gear, 7 s holds, sham cruise, 25–30 C1 segments); the draft rule
  replaced by the proposed one; the post-drive routine excludes drive C files
  from `logs/raw`. One sentence corrected: a Bosch knock retard lasts about 12 s
  (3° recovered 0.75° per ~4 s), not "a second or two".
- **`new_drive.py`**: withholds the retard unless `--unblind`. It is the routine's
  first step on every new drive and printed the median and p95 of target minus
  actual: run on the 18–19 October files it would have un-blinded the rule.
  Checked on 7475b5d7: blind by default, the old output with `--unblind`.
- **`verify_docs.py`**: `results/DRIVE_C_RULE_NUMBERS.txt` added to the
  generated result tables kept out of the bare-number retired scan (the X1/X2
  precedent of 13 October): two of its error rates printed "2.3 %", the retired
  pre-correction load residual.

## 2. Found on the way

- `plot_sim_vs_car.py` no longer imports (`fit_envelope` has no `envelope`);
  found on 13 October, still open, untouched here.
- The research found that target minus actual may not be the knock retard at
  all (the Bosch documentation supports three readings); the rule's channel
  check and its disclosure carry that, and it is open item 1 of the rule.

## 3. What was not done, and why

- **The analysis script (stages A, B, C) is not written.** It implements the
  rule, so it waits for decisions 14–23; it must then be committed before the
  repeat drive, and stage A run blind on the 18–19 October files.
- **The 18–19 October files were not read.** They are not on this machine, and
  the rule must be fixed without them.
- Nothing was retrained, and no plant file changed (`plant_sha` and
  `derived_sha` unchanged).

## 4. Next

1. Jad and Ghassan answer decisions 14–23 (Desktop copy for sending).
2. The analysis script, committed with the answers.
3. Stage A, blind, on the 18–19 October files: how many valid steps and
   segments they already give.
4. The repeat drive (C2 on the coast, C1 on a climb, the warmest hours).

## 5. Later the same day: the answers, and the analysis script

- **Decisions 14–23 answered**: Jad and Ghassan agree to all ten (Jad's answer as
  reported by Ghassan), recorded in both columns before any retard was computed
  on a drive C file (`7ad649c`). Nobody watched the live angles during the
  18–19 October drive (Ghassan); the rule's disclosure says so (`2d17c0a`).
- **`drive_c_analysis.py`**, the rule as code, with `test_drive_c_analysis.py`
  (105 tests on synthetic BimmerLink-style logs, all pass). Built by a second
  workflow: one implementer, three independent reviews (fidelity to the rule,
  blindness and robustness, statistics), one agent applying the confirmed fixes.
  The reviews found real holes, all fixed: a sham or step window that overlapped
  another step's baseline could leak a response into the frozen list; one lost
  target poll could manufacture a 10° pull; stage C could have been run twice;
  the knee's "no onset" bound could sit above the car's own first knock. Every
  reading the rule leaves open is fixed in the module docstring as an
  implementation choice (IC1–IC41), each the conservative one.
- How it runs: `stage-a` reads only speed, air, coolant and ambient; `stage-b`
  reads the angles only in the baseline windows and writes `frozen.json` with
  its SHA-256; `stage-c` runs once, only when the scripts, the frozen list and
  every log are committed and unchanged and the plant is X1's. `dry-run-spark`
  reproduces −3.81 / 2.07 and −1.78.
- **Driving guidance added** (no rule number changed): press every 75–90 s. On
  synthetic logs the script keeps 60–61 valid sham windows at 60–67 s spacing
  and 91–94 at 75–95 s; at a minute the sham after each step lands in the next
  step's baseline.
- Stage A on the 18–19 October files has not run: they are not on this machine.

