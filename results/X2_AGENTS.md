# X2's agents: what they did, and why X2 failed

**Written 13 October 2026, after X2's result.** Everything here is description,
after the fact: it changes nothing in `PREREGISTRATION_X2.md`'s reading
(INCONCLUSIVE). Every number comes from `python x2_agents.py`
(`results/x2_agents.json`) or from the scoring scripts named beside it, and each
explanation was measured on the agents' outputs before it was written (mistake 24).
One of them changed in the measuring: see section 5.

## 1. What failed

| check | X2 | X1, for comparison |
|---|---|---|
| **P** preview, paired by seed | **INCONCLUSIVE**: 1 of 5 pairs favour preview, mean −4.40 points, sd 20.51 | SMALLER THAN THE MEI, sd 24.78 |
| **C** convergence (C4's rule) | **NOT-CONVERGED**: 0 of 5 sighted, 1 of 5 blinded, 0 of 5 pairs settled | not tested (50 000 steps) |
| **S** beat `current-grade` | 7 of 10 | 39 of 46 |
| worse than the baseline ECU on some frozen episode | 4 of 10 | 19 of 46 |
| **L** the car's own drives, no harm | **0 of 10** | 1 of 46 |
| safeguard 2's probe | 0 of 10 pass | 0 of 46 |
| **T** held out: 50 °C / 76 kPa / 25 °C on 21.75 % | 8 / 6 / 5 of 10 beat that condition's `current-grade` (at 76 kPa partly by refusing torque: section 8) | 26 / 25 / 30 of 46 (X1 trained at 101.3 kPa only) |

Three failures need explaining: why preview reads INCONCLUSIVE on a spread this
wide, why the agents never settled, and why they burn fuel on the car's own
drives. They have different causes.

## 2. The agents one by one

`current-grade` cuts 46.98 % on the scored climb.

| agent | cut % | over current-grade | hot training cut by third % | on the climb: lambda / boost kPa / spark ° | before the climb: Δlambda / Δboost kPa | car's drives, fuel over the ECU (life most) |
|---|---|---|---|---|---|---|
| sighted 0 | 71.7 | +24.7 | 41.3 / 50.3 / 53.5 | −0.147 / +10.5 / +0.0 | +0.018 / +15.3 | +6.58 % |
| blind 0 | 72.0 | +25.0 | 37.7 / 47.1 / 52.2 | −0.147 / +8.8 / +0.0 | +0.002 / −0.3 | +6.91 % |
| sighted 1 | 39.3 | −7.7 | 40.0 / 52.9 / 49.4 | −0.039 / +2.0 / +0.0 | +0.057 / +26.9 | +5.42 % |
| blind 1 | 70.6 | +23.6 | 46.5 / 47.3 / 49.7 | −0.149 / −3.3 / +0.0 | −0.000 / −0.1 | +5.96 % |
| sighted 2 | 35.4 | −11.6 | 41.1 / 51.8 / 45.0 | −0.042 / +9.3 / +0.0 | +0.005 / +13.0 | +11.61 % |
| blind 2 | 47.6 | +0.7 | 39.1 / 50.0 / 47.5 | −0.149 / +12.6 / −0.8 | −0.005 / +1.2 | +8.68 % |
| sighted 3 | 71.3 | +24.3 | 45.1 / 52.3 / 44.9 | −0.135 / +1.0 / +0.0 | −0.011 / −11.4 | +7.08 % |
| blind 3 | 46.0 | −1.0 | 31.9 / 40.3 / 48.4 | −0.122 / +9.5 / −2.0 | +0.001 / −2.8 | +7.12 % |
| sighted 4 | 48.4 | +1.5 | 51.2 / 54.9 / 50.7 | −0.055 / −12.8 / +0.0 | −0.053 / −3.8 | +6.08 % |
| blind 4 | 51.8 | +4.8 | 42.4 / 51.0 / 50.4 | −0.089 / −20.7 / +0.0 | +0.013 / +0.8 | +8.32 % |

Columns: the cut over the twenty frozen episodes; the training cut on episodes
where the parallel baseline car passed 850 °C, by thirds of training; what the
agent applied on the climb (medians, from 190 s); how its lambda and boost trims
changed from 90–119 s to 150–179 s, as the climb came into the preview's 30 s;
and its fuel over the baseline ECU on the car's own drives with life weighted
most.

## 3. Why the preview reading is INCONCLUSIVE

**The sighted agents read the preview.** As the climb comes into view, every
blinded agent's trims stay where they were (lambda moves by at most 0.013,
boost by at most 2.8 kPa: drift, since it cannot see the hill), while every
sighted agent changes its actuators.

**But they use it in opposite directions.** Sighted seeds 3 and 4 add protection
ahead of the hill (lambda −0.011 and −0.053, boost −11.4 and −3.8 kPa). Sighted
seeds 0, 1 and 2 do the reverse: seeing the hill, they lean out (+0.018, +0.057,
+0.005) and raise boost (+15.3, +26.9, +13.0 kPa). Seeds 1 and 2 then enrich far
less on the climb than their blind twins — lambda trim −0.039 and −0.042 against
−0.149 and −0.149 (the twins sit at the −0.15 limit) — and they are the two
agents that cut least: 39.3 % and 35.4 %, against 70.6 % and 47.6 %. Sighted seed
3 protects much more than its twin (+25.3 points). Five differences from −31.3 to
+25.3 have no consistent sign: INCONCLUSIVE.

**What the preview bought instead.** Torque shortfalls at the start of the climb
are near zero for every agent, but the reward's tracking term over 175–240 s is
less negative for the sighted agent than for its twin in 4 of 5 pairs (−0.086 to
−0.118 against −0.088 to −0.508): anticipating the hill, the sighted agents
follow the rising torque request more closely. The preregistered outcome is
damage alone, so a preview used for the job (tracking) rather than for
protection reads as nothing, or as a cost. This is a description, not a test.

**The scored climb is a corner of training.** X2 drew 136–154 hot episodes per
run (11–13 % of about 1200; the road gate's sample had suggested 5 %), and only
12–22 (1–2 %) in the scored climb's air (38 °C or more, 97 kPa or more, hot).
The scored climb's constant 130 km/h is never drawn. On the scored-like training
episodes of the last third (five each; a pair's twins drive the same roads),
sighted seeds 1 and 2 cut 63.3 % and 44.1 %, against their blind twins' 51.5 % and
43.0 %: in training they protected as well as their twins or better, and on the
scored climb they did not (39.3 % and 35.4 %, against 70.6 % and 47.6 %). X1 showed
the same thing (six sighted agents under 40 %, no blinded one); X2 repeats it
with two sighted and no blinded. Post hoc, twice, not a test.

## 4. Why they did not settle

**The agents' practice cut, all along training.** Each agent on check_x2_convergence's ten practice
episodes of the locked climb at six points of its training (the first three scored for this report, the last
three by the convergence check):

| agent | 180 000 | 360 000 | 540 000 | 720 000 | 900 000 | 1 080 000 | range |
|---|---|---|---|---|---|---|---|
| sighted 0 | 64.0 | 54.4 | 62.5 | 66.2 | 59.8 | 71.7 | 17.4 |
| blind 0 | 66.4 | 70.2 | 69.8 | 72.4 | 72.3 | 72.1 | 6.0 |
| sighted 1 | 64.9 | 66.7 | 53.2 | 54.2 | 58.5 | 48.2 | 18.5 |
| blind 1 | 33.9 | 50.2 | 71.1 | 70.2 | 68.9 | 71.7 | 37.8 |
| sighted 2 | 69.0 | 58.4 | 37.0 | 55.3 | 70.6 | 57.5 | 33.6 |
| blind 2 | 29.0 | −17.4 | 26.7 | 71.0 | 66.5 | 37.5 | 88.5 |
| sighted 3 | 55.9 | 59.9 | 62.6 | 71.8 | 65.6 | 71.1 | 15.9 |
| blind 3 | 60.0 | 71.1 | 33.1 | 18.7 | 51.8 | 47.5 | 52.4 |
| sighted 4 | 38.8 | 68.8 | 70.6 | 71.6 | 72.6 | 42.2 | 33.7 |
| blind 4 | 57.3 | 69.7 | 72.2 | 60.6 | 70.1 | 64.4 | 14.9 |

Across the six points each agent's practice cut spans 6.0–88.5 points, and from one point to the next it moves by a median of 8.6 points (largest 46.5) — against the 2.7-point band that would call it settled. The agents were not converging slowly; they kept moving across the whole of training.

**And so the pairs.** The same practice set, sighted minus blinded, seed by seed at each point:

| seed | 180 000 | 360 000 | 540 000 | 720 000 | 900 000 | 1 080 000 |
|---|---|---|---|---|---|---|
| 0 | −2.4 | −15.8 | −7.3 | −6.2 | −12.5 | −0.4 |
| 1 | +31.0 | +16.5 | −18.0 | −16.0 | −10.4 | −23.5 |
| 2 | +40.0 | +75.9 | +10.2 | −15.8 | +4.0 | +20.1 |
| 3 | −4.1 | −11.1 | +29.5 | +53.1 | +13.9 | +23.6 |
| 4 | −18.4 | −1.0 | −1.6 | +10.9 | +2.5 | −22.2 |

A seed's difference changes sign 6 times in the 25 steps between points, and the count of pairs favouring preview runs 2–3 of 5 at every point. Which way a pair reads depends on where each twin happens to be in its swing when training stops: the spread of X2's paired differences is, in large part, this.
Even the same final agents read differently on two episode sets: on the practice ten, seed 2's pair
is +20.1 points and seed 4's −22.2; on the frozen twenty that score X2, −12.3 and −3.3.

**Learning did not diverge.** In stable-baselines3's statistics (one entry every four
episodes) the median critic loss over the first, middle and last tenth of training is
0.012–0.029 in every run; single entries reach 0.34–1.64 and fall back. The entropy
coefficient fell from 0.35 at the first entry to about 0.003 by a tenth of training
and to 0.001 by the end, so the policies were nearly deterministic early.

**Protection on hot training episodes stopped improving after the first third.**
Median cut on the hot training episodes rose in every run, from 32–51 % in the first
third to 40–55 % in the second, then moved by −7.4 to +8.1 points in the last (45–54 %),
four agents up and six down: no steady gain after about 400 episodes.

**What most updates were about.** 41–45 % of X2's training episodes were below
19 °C and 45–49 % below 90 kPa; 87–89 % never passed 850 °C. On those cool
episodes the life term is mostly knock (section 5: it is the baseline car's
largest damage term there), beside fuel and tracking. The scored
climb's behaviour is a small corner of what the critic learns, moved by updates
made for the rest. That reading names quantities this script does not measure
(how much each update moves the climb), so it is offered as the likeliest
account, not as a measurement.

## 5. Why they burn fuel on the car's own drives

**Where the extra fuel goes.** With life weighted most (frozen episode 4), 59
of 60 agent runs burn more than 1 % over the baseline ECU (median +6.92 %, worst
+20.12 %). Split step by step by how hot the baseline car's housing was, 56.1–97.0 % of each agent's extra fuel (median 76.4 %) goes while that housing is under 500 °C, where no protection of the turbine is needed.

**What the agents avoid there: knock.** On those cold steps the baseline car's
damage rate is 0.060 a second of knock, 0.010 of oil and 0.0001 of turbine. The
agents cut the knock term to 0.009–0.037 a second and leave oil and turbine
where they were. Every agent keeps at least one lever on there (medians): nine of
ten cut boost by 10–36 kPa, seven retard spark by 1.0–6.9°, six enrich. In
training the same holds: on the episodes that never passed 850 °C (last third),
knock is the baseline car's largest damage term (0.039–0.041 a second, against
0.027–0.031 turbine, 0.010 oil), and the agents cut it to 0.017–0.020, their
largest saving (turbine falls to 0.018–0.022).

**Where the knock comes from — and the measurement corrected the first reading.**
The first reading was that the model's ECU runs just above the knock knee (0.85)
in ordinary driving. It does not: in cold running on the car's drives its knock
integral has a median of 0.40 and passes 0.85 on 1.4 % of steps. The term lives
on those few steps: 16.1 % of it on each replay's first step (a start from rest,
with no step into it), and the other 83.9 % on 194 steps, **every one of them a
one-step rise in the torque request of 20 Nm or more** (median +75 Nm, against a
median step of 4 Nm), with manifold pressure up a median 30 kPa in the step.

In training (last third; five road sequences, since a pair's twins drive the same
roads beside the same baseline car), the steps where the baseline car's knock term
passes 0.5 a second are 0.67–0.70 % of all steps and carry 97.7–98.0 % of its
knock damage, and all but one of those 12 378 steps are torque rises of 20 Nm or
more (median +84 to +87 Nm). By share of that knock damage they fall on the first
step of a speed-up, 60.0–63.2 % (training ramps a speed change at 0.8 m/s², so the
torque request jumps when the ramp starts); on the step a slow-down ends,
22.5–25.0 %; on a gear shift alone, 10.2–11.0 %; on a grade ramp alone, 1.9–2.4 %;
on none of these, 0.0–0.2 %.

This is the one-step knock spike the merge review found at grade steps
(30 September): the baseline ECU schedules spark on the previous step's manifold
pressure (`engine_env`, AUDIT.md C2's fix), so on a sudden rise in load its spark
is too far advanced for one step. The 8 s grade ramp removed it from the scored
climb; training's speed changes and gear shifts, and the car's own driving, still
produce it.

**What the reward pays for, and what it does not.** The agent picks each step's
action from the state at the end of the step before, which carries that step's
torque request and acceleration but no speed target, and the preview carries
grade only. A speed change is unseen until the step it starts in, which is the
spike's step, so a lever helps against it only if it is already on. Keeping it
on costs fuel on every step and saves knock on a few:

- On the car's drives with life weighted most, the trade pays for 8 of 10
  agents: in cold running the life term they earn (+0.0021 to +0.0044 a step)
  exceeds the fuel term they lose (−0.0011 to −0.0033; sighted seed 2: +0.0025
  against −0.0016). For sighted seed 0 and blinded seed 4 it does not.
- Averaged over training's preference weights, it does not pay in cold running.
  On the episodes that never passed 850 °C (last third), the fuel term exceeds
  the life term under 500 °C in 9 of 10 runs (−0.0019 to −0.0030 a step against
  +0.0016 to +0.0021), and between 500 and 715 °C in all ten (−0.0045 to −0.0057
  against +0.0000 to +0.0033). It pays when the housing is hot: at 715 °C and
  over, the life term (+0.048 to +0.071) is three to five times the fuel term
  (−0.012 to −0.018).
- With life weighted least (frozen episode 15) they let go: the median overspend
  on the car's drives is +0.39 % (21 of 60 runs over 1 %), and every agent runs
  lean in cold running (lambda trim +0.017 to +0.056, no spark retard).

So the agents keep levers on where those levers cost, and are paid where the
housing is hot. Whether they cannot tell the two apart or have not yet learned
to is not measured here. Whether the real engine knocks on these steps is what the
untested knock model cannot say and drive C would. The merge review of
30 September treated the same spike at grade steps as an artefact of the 1 s step
(one step of lag is a full second at the old load), and the agreed fix there was
a ramp.

## 6. The episodes worse than the baseline ECU

All on the six lowest life weights of the twenty (0.029–0.136):

- **blinded seed 3**, frozen episodes 13, 15, 16 and 17 (life 0.029–0.062):
  retards spark 4.5–5.8° and adds 9.7–11.2 kPa of boost on the climb; damage
  1170–1713 against 848, fuel 7.7–8.8 % more. Blinded seed 6's pattern of 29
  September (mistake 24): it loses on fuel and life together.
- **blinded seed 1**, episodes 8, 13, 15, 16 and 17 (life 0.029–0.089): runs
  lean on the climb (lambda trim +0.046 to +0.058); damage 872–918, fuel 2.0–2.9 %
  more.
- **sighted seeds 2 and 4**, one episode each: seed 2 on episode 13 (life 0.034)
  runs lean on the climb (+0.033) with 26.5 kPa less boost, damage 865, fuel 1.4 %
  more; seed 4 on episode 2 (life 0.136) cuts boost 11.3 kPa, damage 871, fuel
  1.3 % more; against 848. Why either costs damage is not measured here.

## 7. The probe

A 50 K hotter housing gets less protection on 22.3–72.9 % of probed climb states
for the sighted agents (median 32.5 %) and 55.5–93.1 % for the blinded (median
64.9 %), so no agent passes (`results/agents/wideair_dt1/sanity_probe.json`). The
probe says the agents' protection does not follow the housing's temperature
consistently; it does not say why. Section 5 (levers kept on against knock spikes
at load steps, and set by the preference weights) is consistent with it: a
reading, not a measurement.

## 8. The transfer test (five episodes a condition: descriptive)

| condition | hill % | for X2 | sighted beating current-grade | blinded | worse than its ECU |
|---|---|---|---|---|---|
| 42 °C, 101.3 kPa (trained air) | 8.25 | in range | 4 of 5 | 3 of 5 | 0 |
| 25 °C | 21.75 | held out: hill > 18 % | 2 of 5 | 3 of 5 | 1 |
| 35 °C | 12.00 | in range | 5 of 5 | 4 of 5 | 0 |
| 50 °C | 7.50 | held out: air > 45 °C | 5 of 5 | 3 of 5 | 0 |
| 90 kPa | 8.75 | in range | 4 of 5 | 0 of 5 | 0 |
| 82 kPa, about Taif | 12.00 | in range | 5 of 5 | 5 of 5 | 0 |
| 76 kPa, the climb's top | 12.25 | held out: air < 80 kPa | 3 of 5 | 3 of 5 | 0 |

X1's seven conditions on X2's agents, each on its own hill, frozen episodes 1, 5, 9, 13 and 17, against each
condition's own baseline ECU and `current-grade` (`results/conditions_wideair_dt1/conditions_test.json`).
Read the counts with the torque beside them. Only at 25 and 35 °C does `current-grade` deliver its torque;
in the other five conditions it falls under 95 % of the request on 16–297 of 719 steps, so its cut there is
partly torque refused. The agents fall short on a median of 1–6 steps in six conditions, but at 76 kPa,
below any air X2 trained in, on a median of 48: their cuts there are partly torque refused too. The worst
single run is sighted seed 4 on frozen episode 5, short on 525 of 719 steps at 76 kPa, and the same agent on
the same episode is the worst at 42 °C (272) and at 50 °C (323).
The one agent worse than its baseline ECU is sighted seed 2, at 25 °C on the 21.75 % hill. Sighted minus
blinded per condition (mean of the five pairs, 95 % interval) runs from −12.4 [−47.1, +22.4] at 25 °C to
+17.5 [−16.3, +51.2] at 50 °C; only 90 kPa's interval excludes zero (+15.2 [+5.0, +25.3]), one of seven.
With five episodes a condition, all of this is description.

## 9. What this says for the next experiment — proposals for Jad and Ghassan

Not decisions; each would be written into a new preregistration first.

1. **Deal with the knock spike before training again.** The baseline ECU's
   spark on the previous step's manifold pressure makes a knock spike wherever
   the torque request jumps: the first step of a speed-up, the end of a
   slow-down, a gear shift. The reward charges every agent for it, and they
   spend fuel everywhere to avoid it. Two candidates, neither tried: schedule the
   baseline's spark on the current step's load, or ramp the torque request's
   changes (the acceleration as well as the grade). Either is a plant change:
   new fingerprint, retrain.
2. **Drive C before trusting any knock term.** Whether the car knocks where the
   model says decides whether the knock term should be in the reward at all.
3. **Put the scored condition into training.** A constant speed on a long
   climb, and more hot episodes: X2's design gave the scored climb's air on 1–2 %
   of episodes and its speed profile never.
4. **Settle before scoring.** Across the last three checkpoints (720 000 to
   1 080 000 steps) the agents' practice cuts still moved by up to 33.6 points.
   A lower or decaying learning rate, a larger batch, or a checkpoint chosen on
   a preregistered validation set.
5. **Measure what preview is used for.** A preregistered secondary reading of
   tracking error or total reward would see a preview used for the job.
6. **Seeds last.** At X2's spread a sign test needs 143 seeds a side for 80 %
   power against the MEI (`analyse_x2.py`); reduce the spread first.

## 10. Reproduce

```bash
python analyse_x2.py                  # section 1: the preregistered reading
python check_x2_convergence.py        # sections 1 and 4: the convergence verdict, 720 000-1 080 000
python x2_agents.py                   # sections 2-6 -> results/x2_agents.json
python x2_agents.py --trajectory      # the same, re-scoring section 4's 180 000-540 000 checkpoints
python sanity_probe.py runs/wideair_dt1                          # section 7
python conditions_test.py --set runs/wideair_dt1 --report-only   # section 8
python logged_check.py --set runs/wideair_dt1                    # the logged-drive check behind section 5
```

The per-step records these read stay on the training laptop (decision 11).
