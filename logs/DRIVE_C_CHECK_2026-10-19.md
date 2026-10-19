# Drive C, first attempt (night of 18–19 October 2026): what it covers

Checked 19 October 2026 by Jad, with Claude Code, at Ghassan's question: are
these logs enough, or does drive C need more driving? Every figure below is
printed by

```
python drive_c_check.py <the folder holding the six CSVs>
```

## 1. The answer

**Not enough. These logs close none of the planned drives, and drive C has to
be driven again, both parts.** The logging was right: drive C's six channels,
each angle read every 0.90–0.93 s. The driving was not drive C's: the loaded
driving ran at a median 4824 rpm in bursts of at most 5.5 s, where part C1 asks
for 20–30 s of firm throttle at 2000–3500 rpm, and the cruise held one load
step of the kind part C2 asks for, against twenty.

- **Drive C** stays open: neither C1 nor C2 is covered (section 3).
- **Drives A and D** cannot be served by these logs: they need channels drive
  C leaves out (oil, road speed, lambda, ambient pressure, boost, throttle,
  torque request).
- **Drive B** was done on 28 September.

## 2. Checked blind

`drive_c_check.py` never subtracts the two ignition angles and never prints an
angle's value. It counts readings and reads engine speed, air mass, coolant
and ambient. Drive C's decision rule is still the DRAFT of 13 October
(`logs/DRIVE_PLAN.md`), and the Training gate (item 6) asks for it to be
written before the drive. This check did not compute the retard, so if Jad and
Ghassan fix the rule's numbers before anyone does, these logs can still be
judged by a rule written before their result was seen.

## 3. What the logs hold, against the plan

Five logs, 00:13 to 01:54 on 19 October, 83.9 minutes, plus a false start of
3 seconds (`01-20-16`).

| | the plan (`logs/DRIVE_PLAN.md`, drive C) | these logs |
|---|---|---|
| channels | drive C's six | the six |
| each angle read | about every 0.9–1.25 s | every 0.90–0.93 s (median), 99 % within 1.47 s |
| engine warm | coolant 88 °C or more, then log | 82.0–96.0 °C, above `build_dataset.py`'s 75 °C throughout |
| when | the afternoon heat (C2 repeated in the cool if possible) | after midnight, ambient 17.5–31.5 °C |
| C1: loaded segments | twenty or more, 20–30 s of firm throttle at 2000–3500 rpm, held gear, on a climb | 6 at 2000–3500 rpm and 140 kPa or more, the longest 2.7 s; none of 20 s |
| C1: readings in the climb's cell, 2400–3000 rpm and 165–185 kPa | hundreds of each angle (the dataset holds 4) | 0 of each |
| C2: load steps | twenty or more, from a 1500–2500 rpm cruise in a held 6th–8th, held 5 s, a minute apart | 6 rises from a steady cruise; 1 meets all four conditions |
| logs | one per part, named for the part | named by the clock only |

**Where the load went.** 103 air-mass readings at 140 kPa or more, at a median
4824 rpm (13 of them at 3500 rpm or less), in 43 bursts, the longest 5.5 s.
Engine speed reached 6604 rpm, and air mass sat at its sensor's ceiling
(1019.9 kg/h, mistake 7) 21 times. Nothing in drive C needs more than
3500 rpm.

**The C2 rises**, all in the first two logs (the steady cruise was there):

| log | at | cruise rpm | cruise air, kg/h | peak air | held above 1.5× cruise | rpm jump within 6 s | after the last rise |
|---|---|---|---|---|---|---|---|
| 00-13-05 | 00:14:02 | 1706 | 70 | 248 | 2.8 s | +146 | — |
| 00-13-05 | 00:14:16 | 1725 | 64 | 416 | 3.6 s | +756 | 13.7 s |
| 00-13-05 | 00:14:48 | 1763 | 50 | 208 | 1.8 s | +117 | 32.8 s |
| 00-13-05 | 00:16:44 | 1852 | 40 | 172 | 4.5 s | +190 | 115.5 s |
| 00-13-05 | 00:22:12 | 1868 | 68 | 164 | 0.9 s | +52 | 327.9 s |
| 00-27-10 | 00:39:30 | 2327 | 104 | 1020 | 6.5 s | +2697 (a gear change) | — |

Only 00:16:44 meets all four conditions. The "steady cruise" and the 500 rpm
jump are this check's own thresholds, named in the script's header; the 50 %
rise and the 20 s before are the draft rule's.

**What cannot be checked from these logs:** the gear (no road speed), the
altitude (no ambient pressure), and who drove and who ran the phone. The
ambient in the last log runs from 25.5 °C down to 17.5 °C under load, which
looks like a climb; only Ghassan can say where the drive went.

## 4. What the logs do give

1. **The proof that drive C's channel set works on this car and app.** Each
   angle every 0.9 s, against about every 8 s on the 26-channel drive
   7475b5d7 (`logs/DRIVE_PLAN.md`, drive C, "Why"). The plan's premise holds;
   only the driving has to change.
2. **15 readings of each angle in `car_spark_boost.py`'s window**
   (2000–4000 rpm, 140–240 kPa), where the dataset holds 31, but none in the
   climb's cell.
3. **Air colder than the dataset has held:** 72 ambient readings below 19.0 °C,
   down to 17.5 °C. The plan listed air below 19.0 °C as not reachable this
   season (`logs/DRIVE_PLAN.md`, the box of 13 October).
4. **About a hundred boosted readings with both angles at 0.9 s**, mostly
   above 3500 rpm. They might serve C1's knee question (the knock integral at
   which the car starts to retard) outside the climb's cell, but only once the
   rule says how the knee is read.

## 5. What the repeat needs (for Ghassan)

The plan's own instructions, `logs/DRIVE_PLAN.md`, drive C. Where these logs
missed them:

1. **C2, the steps, first.** A straight, empty road. Gearbox in M, hold 6th,
   7th or 8th, cruise steady at 1500–2500 rpm. Press firmly, half to full
   pedal, **hold 5 seconds**, lift back to the same cruise. **A full minute of
   steady cruise** before the next. **Twenty or more.** Last night: one.
2. **C1, the loaded segments, on a climb.** Gearbox in M, a gear that keeps the
   engine at **2000–3500 rpm** (on the screen: engine speed near 2700, air
   mass near 400). Firm, near-full throttle for **20–30 seconds**, twenty
   segments or more. Last night: the load ran at a median 4824 rpm, in bursts
   of at most 5.5 s.
3. **In the afternoon heat.** Last night was 17.5–31.5 °C after midnight.
4. **One log per part, named for it** (`driveC2_steps-<date>.csv`), and the
   30-second wait after starting each log.

## 6. Decisions for Jad and Ghassan

1. **Fix the decision rule's numbers before the repeat** (and before anyone
   computes the retard on these logs, if they are to be used).
2. **Whether these logs go into `logs/raw/`.** Adding a drive and running
   `build_dataset.py` re-derives the plant, which moves the simulator and every
   figure the docs quote from it. Recommended: keep them out until the repeat,
   then add both at once, one re-derivation instead of two. They are kept, with
   their hashes, in section 7.

## 7. The files

As exported, in `C:\Users\admin\Downloads\2026-10-19` on Jad's machine. Not in
the repository.

| file | bytes | SHA-256 |
|---|---|---|
| `2026-10-19_00-13-05.csv` | 238809 | `d7832472242c2e0e06ad7a7594cb522476597d7e9761238dbd39012e36da0852` |
| `2026-10-19_00-27-10.csv` | 354690 | `09f740d7deaf50e760f4d263cfc01f9faa800e0f17e37306ed91f3d97653953b` |
| `2026-10-19_00-48-16.csv` | 450310 | `8b74102bd49598eace443c97d3f01c8f13f582c364270ea1d69a02d98ba7143d` |
| `2026-10-19_01-20-16.csv` | 928 | `cf92414011f5f8712c568f2cb4bb6cf3c4c06b1edbcbb320b7d5c851e0aaeb0e` |
| `2026-10-19_01-20-22.csv` | 249460 | `95d9d64fa5da58035c597c98e9fb3db9238724e4667c5cab899f27f94e953178` |
| `2026-10-19_01-42-36.csv` | 202056 | `f1eaded840bc7d86fbb62c72b22a6c6195d6e6d8fe4e0f6305b45053832baebb` |
