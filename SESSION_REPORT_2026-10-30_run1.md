# Session report — 23 to 30 October 2026: Run 1, the three EPA engines calibrated and frozen

Ghassan's session, on branch `GRA-test`. It starts after contract version 4
on commit A (`cfe6211`, 23 October) and ends at commit D (`25437ba`,
30 October), pushed. Training runs on another device and none ran here; no
held-out EPA row was read, and `validate_epa.py run` (Run 2) was not run.

## 1. What was asked

1. Run 1 before Jad fills his column ("go ahead without it", 23 October):
   the calibration of the Mazda 2.5 T, the Honda L15B7 and the Ford 2.7 TT
   against EPA's calibration rows, frozen.
2. On each question Run 1 raised, a ruling. Ghassan chose the recommended
   option every time: decisions 82–85 and 86–89 (29 October), 90–93
   (30 October).
3. Fix what is found along the way, and document it.

## 2. Commits

| commit | what |
|---|---|
| `c842d74` | contract version 5: decision 77, the in-sample form criterion \|E\| − 2u_stat > R; the Run 1 go-ahead recorded |
| `d7f5c00` | commit C: the calibration and validation scripts (WP3), tested on synthetic data |
| `2d107e6` | the D3 channel pins, from the catalogue (decisions 78–81) |
| `7ee7408` | coding defect D-1: the Mazda's valve brackets from EPA's Atkinson ratio |
| `0147f93` | decisions 82–85 and a disclosure |
| `21cc7d4` | coding defect D-2: a row-9 bracket applied as its two edges |
| `891331c` | decisions 86–89 |
| `a5a3e6b` | decisions 90–93, and the two test checks commit D needed |
| `25437ba` | commit D: Run 1's records and the three derived files |

The contract, version 5, did not change after the first fit (rule 0). None of
decisions 82–93 is a contract rule.

## 3. How Run 1 went

- **First pass (24 October).**
  - The Mazda froze at A+B+C+D. Every gating in-sample statistic failed
    except E4a and D1.
  - The Honda stopped at T0 on `d2_gate`, seed 1. The Ford did not start.
- **The defect hunt.** It reproduced every in-sample value bit for bit and
  traced the Mazda's misses to the model's form:
  - scavenging on the hot 1300 and 1500 lines;
  - fixed valve events where EPA's move;
  - a back-pressure law without an rpm term;
  - fits sitting on their bounds.
- **Its findings.** One coding defect, D-1: the Mazda had no IVC or EVO
  bracket for E6 row 9, for a false reason. One population question, F-1:
  Final TIT and steady TIT are not the same temperature, which became
  decision 83.
- **Decisions 82–85 (29 October).**
  - 82: the Mazda keeps A+B+C+D, as section 2.4 fixes it.
  - 83: a steady-only TIT reading is declared as a sensitivity.
  - 84: T0's `d2_gate` check is widened to the data's resolution.
  - 85: a probe below its numerical noise falls back to ±10 %.
- **Second pass.**
  - The Mazda re-ran through the defect route.
  - The Honda failed `d2_gate` again: decision 84, read as written, does not
    reach its seed 1.
  - The Ford failed T0 on seed 1's χ², 42.40 on 13, above its 99 % band
    3.57–29.82.
- **Diagnostics behind 86–88.** Read-only diagnostics, each checked
  independently, measured the three questions
  (`docs/build_step_2/RUN1_DIAGNOSTICS.md` and its archive):
  - The Honda's gate was a test-resolution artefact: one row's λ moves by
    3.2e-5, 0.0064 of the noise sd.
  - The Ford's seed 1 is a sampling tail. 400 diagnostic draws exceed χ²(4)'s
    0.99 point 4 times, against 4 expected.
  - Eight of the Mazda's probes sized by R1 cross zero, and one gives a
    negative volume.
  - One more coding defect, D-2: brackets were applied symmetrically about
    the value. No document of the specification says so.
- **Decisions 86–89 (29 October).**
  - 86: `d2_gate` also passes when the truth's gate is indistinguishable at
    T0's noise.
  - 87: the Ford's seed 1 is ruled sampling, with seed 5 in its place. Had
    seed 5 failed, the Ford would have stopped for good.
  - 88: a probe sized by R1 that leaves its constant's range falls back to
    ±10 %.
  - 89: a byte-for-byte reproduction from a fresh worktree before commit D.
- **Third pass (29–30 October, on `891331c`).** All three engines completed.
- **The freeze review.** It blocked on one item, decision 90.
- **Decisions 90–93 (30 October).**
  - 90: the Ford's back-pressure ratio keeps the contract's ±10 %, although
    its minus side lies below the fit's bound.
  - 91: B17's CVT refusal holds until fingerprint schema 4.
  - 92: S4's list of bounds-active parameters is incomplete; disclosed.
  - 93: the Honda and the Ford keep A+B+C+D, as 82 rules for the Mazda.

## 4. Results (each from `results/EPA_CALIBRATION/<id>/`)

**Form.** No form passes in-sample on any engine, so all three froze at
A+B+C+D (contract section 2.4).

| engine | fails at A+B+C+D | passes | E4b |
|---|---|---|---|
| Honda L15B7 | E1a, E2a, E3a, E4a, L0, L1 | D1 | neither (noise exceeds R) |
| Ford 2.7 TT | E1a, E2a, E3a, L0, L1 | E4a, D1 | neither |
| Mazda 2.5 T | E1a, E2a, E3a, L0, L1 | E4a, D1 | neither |

**T0.** It passes on all three engines. The out-of-form seed 4 is detected
every time: χ² 4970 (Honda), 75.0 (Ford), 20226 (Mazda), all on 13.

| engine | in-form seeds and χ² | note |
|---|---|---|
| Honda | 16.60 / 13, 6.05 / 13, 20.71 / 14 | seed 1 passes `d2_gate` under decision 86, sum 4.05e-5 over 164 rows |
| Ford | seeds 2, 3 and 5: 8.24, 25.01, 6.64 | seed 1's 42.40 is kept, marked replaced |
| Mazda | 9.41, 11.39, 15.96 | |

**Poison and completion.**
- Poison `--full`: all equal on all three engines.
- K3 knee: Honda 911.80 K, Ford 937.17 K, Mazda 1030.32 K.
- Delivery check: share over the tracking tolerance 0 on all three. The
  largest shortfall is 2.096 N m on the Honda's CVT at 5000 rpm.

**Reproduction (decision 89).** All 51 compared files (17 per engine) came out
byte-for-byte identical from a fresh worktree of `891331c`.

**The B58 (decision 48's re-runs).** Nothing moved.
- Unchanged: plant_sha 865f8e7b7e5c2dbe, derived_sha 326c0835548975e2.
- Byte-identical to commit A's: `validate.py`, `test_reward.py`,
  `check_premise.py`, `check_roads.py` and `app.test_replay --full` (59 of 59).

## 5. Disclosed, for the thesis

**Rulings written after the result they rule on.**
- Decision 86 was written after the Honda's failure, and the Honda's second
  T0 ran before the team chose a wording.
- Decision 90 was written after the freeze review saw the probe.

**Findings the frozen record carries.**
- The Ford's back-pressure ratio is frozen at its bound, 1.0. Run 2 probes it
  at 0.9 and at 0.98625, both below that bound (decision 90).
- S4's `bounds_active` misses the Ford's `burn_rpm`, `fmep_0` and `fmep_sp`,
  and the Honda's `burn_rpm`. The flag itself is raised. The list will be
  corrected after Run 2 (decision 92).
- The Honda's frozen EVO, 140°, lies below its own bracket of
  145.25–174.30°. It is load-bearing (21.24 K), so it becomes a preregistered
  sensitivity row.
- Some probes respond almost entirely on one side: `n_poly` on all three
  engines, the Honda's `octane`, and the Mazda's `flame_lam` and `wiebe_m`.
- The Honda's torque table steps +43.6 N m from 1900 to 2000 rpm, where the
  load loop changes operating point.

**Seen before the fit.** A held-out torque was seen before the fit (the
disclosure of 29 October). It is recorded in
`calibrate_epa.SEEN_BEFORE_THE_FIT`, and nothing used it.

## 6. Not done, and why

- Run 2, the held-out validation, waits for decision 34's test roads and the
  L1/E8 tightenings (decision 65).
- Fingerprint schema 4 (decisions 27–28) is due before any EPA engine trains.
- The benchmark and identity check on the training device are the user's to
  run there.
- Jad's column of decisions 36–93 is open. The Desktop copies are
  `decisions_2026-10-21_G.md`, `decisions_2026-10-22_H.md` (36–76) and
  `decisions_2026-10-30_H.md` (77–93).
