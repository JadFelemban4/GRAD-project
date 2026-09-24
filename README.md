# Engine Supervisor — Phase A–F code

> **Opening this in Claude Code?** Read `CLAUDE.md` first — it carries the
> project's claim, its current state, and the mistakes already made.

Working code for the validated parts of the project. Every number quoted in the
handbook is this code's actual output, and `validate.py` regenerates the ones
that go in Chapter 3.

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Python 3.11 or newer.

> **PHASE D HAS RUN, 22 September 2026, AND THE RESULT IS A NULL.**
> Sixteen agents — eight seeds per arm, sighted and blinded — trained on the
> corrected ZF plant under `results/PREREGISTRATION.md`, which was committed
> **before any of them started**.
>
> ```
> positive (preview helped) : 5 of 8     mean difference : +4.8 damage units
> exact one-sided sign test   p = 0.3633
> exact paired permutation    p = 0.4922   alpha 0.05 -> NOT SIGNIFICANT
> ```
>
> **Preview cannot be shown to help.** Seed 3 says it saves 387 damage units;
> seed 5 says it costs 288. The spread between seeds is tens of times the
> effect, and that is precisely why eight were run instead of one.
>
> **A second and separate finding, which is positive:** the trained agent beats
> the `current-grade` comparator by **+29 to +34 points** on five of eight
> seeds. **Learned supervision works; PREVIEW specifically is what cannot be
> shown.** Two claims, not one.
>
> **Say the training budget in the same breath as the null.** These are C1
> agents — 50 000 steps, 11 training episodes each. The defensible sentence is
> *with agents trained to the C1 budget, preview does not separate from seed
> noise* — never *preview does not help*. Two more limits travel with it. The
> blinded arm was not blind: one fixed road plus a thermal clock, so a blind
> agent could memorise when the hill comes (`results/PREREGISTRATION.md`
> limit 7). And at Phase D's spread eight seeds have power 0.10 against the
> minimum effect of interest, 50 damage units — set on 22 September, after the
> result was known; the sign test never uses it, so the verdict stands.
>
> **Phase D2** ran the same ablation on a randomised climb, so that the blind
> arm is truly blind, preregistered (`results/PREREGISTRATION_D2.md`) before
> any D2 agent trained: **INCONCLUSIVE** (4 of 8 seeds, sign p = 0.6367).
> *(This line said "No D2 result exists yet" until 24 September -- a day
> after the result existed.)*
>
> **C4** ran D2's design at 300 000 steps -- one variable changed, the
> training budget -- preregistered (`results/PREREGISTRATION_C4.md`) before
> any C4 agent trained. Result, 24 September: **SMALLER THAN THE MEI** by the
> primary sign test (7 of 8 seeds below 50, p = 0.0352), with the
> permutation test disagreeing (p = 0.3867, one seed carrying +360.6) and
> the agents **not converged**. The preregistered reading: preview's effect
> is below the threshold at this budget; the agents were still changing, so
> the budget is not ruled out as the explanation. `python analyse_c4.py`.
>
> `python analyse_phase_d.py` reproduces every number above.
> Full account: `CHECKPOINT.md`, 21–22 September.

> **Updated 16 September 2026.** Two things arrived since the last pass. The
> dataset is now **ten drives, 295.0 minutes** (`pull01`, which contributes
> zero samples by design, so no calibration figure moved). And `app/` exists —
> a live supervisor that runs this same physics beside the car and estimates
> turbine temperature, which the vehicle has no sensor for. **It is a second
> deliverable and it is not the missing piece: Phase D still is.** *(Phase D
> ran on 21-22 September and returned a null -- see the box above this one.)* Three new
> entries in `CLAUDE.md`'s mistake log — 14, 15 and 16 — came out of building
> and merging it.

---

## Run these five, in this order, on day one

<!-- RETIRED-OK: section 829.2, 548.6, 437.6, 33.8, 47.2, 13.4 -->

```
python plant.py            #  ~30 s   spark, lambda and IAT sweeps
python validate.py         #  ~10 s   regenerates the validation table
python check_premise.py    #  ~3 min  the hand-written premise table (NOT the result)
python verify_docs.py      #  ~1 min  confirms the documents still match the data
python -m app.test_replay  #  ~1 min  confirms the live app still behaves
```

> ### ⚠️ THE PREMISE NUMBERS ARE VOID AS OF 16 SEPTEMBER 2026
>
> The 15 September audit (`AUDIT.md`) found three defects in how they were
> produced. **Do not quote 829.2 / 548.6 / 437.6, the 33.8 % / 47.2 % pair, or
> the 13.4-point preview advantage.** Run `check_premise.py` and read what it
> prints, including the warning at the bottom.
>
> **C1 — the baseline had its cooling switched off.** `check_premise.py` and
> `generality_test.py` each defined their own "neutral" as all five actions at
> zero. Actions 3 and 4 are not trims, they are absolute duties: zero means the
> radiator fan OFF and the coolant pump at its 0.3 floor, and the pump term came
> out at −1.857, outside the action space the environment declares.
> `engine_env.neutral_action()` exists to fix exactly this (mistake 10) and
> neither file called it. Every preview figure was therefore measured against a
> crippled baseline, while the protecting policies turned the pump back to 1.0
> whenever they acted — so part of their "protection" was cooling the baseline
> row never had.
>
> **C2 — the baseline ECU was scheduled on a load the engine was not at.** It
> looked spark and enrichment up at an open-loop *guess* of 224 kPa while the
> tracking loop actually settled at 175 kPa, commanding knock-limited spark for
> a phantom load and cooking the turbine with about ten degrees of retard that
> the engine never called for. **The 879 °C turbine peak this file used to quote
> was that scheduling error, not the engine.**
>
> **C3 — the reactive comparator protected less hard, not just later.** It
> saturated at k = 0.36 while the predictive policy held k ≥ 0.55, so the gap
> between them was partly depth and only partly timing.
>
> **And the ablation identity was never evidence.** With `use_preview=False` the
> preview term is literally zero, so the predictive policy *returns the reactive
> policy's vector on every step*. "548.6 = 548.6 to the decimal" could not have
> come out any other way. It becomes a real ablation only when a TRAINED blinded
> agent is raced against a trained sighted one — which is Phase D.
>
> **What the script prints today** (`check_premise.py`, `FULL_RUN.txt`
> 21 September; the locked scenario, 12 % at 130 km/h in 42 °C air on the ZF
> 8HP51 gearbox), with the true neutral, equal protection depth, and the ECU
> scheduled on the pressure the engine runs at:
>
> | policy | fuel g | damage | peak turbine |
> |---|---|---|---|
> | baseline ECU (true neutral) | 4664 | 959.8 | 884 °C |
> | reactive protection | 4843 | 679.0 | 862 °C |
> | current-grade protection | 4936 | 633.2 | 861 °C |
> | predictive protection | 4941 | 637.4 | 861 °C |
> | predictive, preview disabled | 4843 | 679.0 | 862 °C |
>
> **The constraint binds.** The baseline, 959.8 at 884 °C, crosses the 850 °C
> trigger by about 34 K, so every protecting policy acts: reactive cuts damage
> 29.3 %, current-grade 34.0 %, predictive 33.6 %. Preview gains **+4.3 points**
> over reactive, but against a policy that merely knows the grade it is on
> right now — information any car has from a nose-down accelerometer, and the
> comparator the audit asked for — it **loses by 0.4 points**. These are
> hand-written policies. The trained answer is Phase D, in the box at the top
> of this file.

> <!-- RETIRED-OK: 256.5, 801, 294.2, 812, 2.2, 1.8, 38, 78 -->
> *(This table read 256.5 / 801 °C and −2.2 points until 17 September — the
> figures from before the H1 crank-angle correction took `plant.DTHETA_DEG`
> from 0.5° to 0.25°, a move `AUDIT_FIXES.md` records in its own H1 section. It
> then read baseline 294.2 at 812 °C until 22 September, with the constraint
> not binding and preview at −1.8 points against current-grade: the run from
> before the scenario moved to 12 % at 130 km/h on the real ZF 8HP51 gearbox.
> On that run the synthetic climb missed the trigger by 38 K and a real drive
> on this car was 78 K hotter than the scenario built to stress it, which is
> the argument for re-choosing the scenario. The code moved and this box did
> not, twice. Mistake 11.)*

> **The replay, over every drive.** Replaying all ten through `app/`:
> `7475b5d7` peaks at **890.6 °C — 41 K ABOVE the trigger — for 36 s of its
> 55.1 minutes**, and no other drive gets within 69 K of it (`670063b2`
> 780.3 °C is next). Across **292.0 replayed minutes the housing is above the
> limit for 36 seconds: 0.206 % of the time.** Those peaks are MODEL OUTPUTS —
> the car has no turbine sensor — and the 0.206 % is itself a figure about how
> much preview could be worth on this vehicle, which is what H/τ is for.
>
> **A SUSTAINED MOUNTAIN CLIMB IS NOW IN THE SET, AND IT DOES NOT BIND.** This
> passage used to close "neither number describes a sustained-climb duty cycle,
> because no logged drive is one." One is, since 19 September: `drive10` is
> Jeddah to Taif and back, two hours, with the ambient channel falling 31.5 →
> 20.5 °C and recovering to 34.5 °C. It peaks at **797.6 °C, 52 K short, zero
> seconds above the trigger** — and that is with the driver reaching 167 km/h.
> The reason is road power, not altitude: the hottest moment of the whole drive
> is a brief acceleration at **137 km/h and 5792 rpm**, and a housing with a
> ~50 s time constant does not respond to bursts. The locked scenario holds
> **88.7 kW for twelve uninterrupted minutes**; the Taif climb asks roughly half
> that. **The hardest real climb we have recorded is 86 K cooler than the
> scenario**, which answers the objection that the scenario is contrived.
>
> **The scenario now binds — and say how it came to, because it was luck.**
> This passage used to say the scenario still had to be re-chosen so that the
> trigger is reached for a physical reason. That is not what happened. 130 km/h
> was picked because it was the only speed that bound on the invented six-speed
> gearbox, which this car does not have. On the real ZF 8HP51 the same 12 % at
> 130 km/h in 42 °C air peaks at 884 °C and binds by about 34 K — by luck, not
> by design (`CHECKPOINT.md`, "The locked scenario survived, and it survived BY
> LUCK"; `make_grade_climb`'s docstring records it as an accident, not as
> foresight). The trigger did not move. The rule stands for the NEXT scenario:
> choose it from something external — a real grade, a published towing cycle,
> a measured ambient — and never by turning a knob until the gap looks good.
> That would be mistake 12 happening to Phase D.

> **THESE NUMBERS CHANGED AGAIN ON 8 SEPTEMBER, AND THIS TIME BECAUSE THE
> SIMULATION WAS THE WRONG ENGINE.** `plant.Geometry` defaulted to a generic
> 2.0 L inline-**four**; `b58()`, the real 3.0 L inline-**six**, was an opt-in
> override that no call site ever passed. Everything downstream of `run_cycle()`
> — this environment, the premise check, the reward tests, the H/τ sweep, ten of
> the eleven validation rows — ran a 1998 cc four-cylinder. Torque was 33 % low.
>
> Phase B was not affected: `predict()` and `map_from_airflow()` always used the
> B58, so the load residual stands: **1.4 %** over the 26 pooled points,
> 30–75 kPa, with zero fitted parameters (**1.1 %** if k is fitted instead).
> Read section 2 below before quoting it — it tests less than its name suggests.
>
> Every earlier set of premise numbers is void — 527/357/199, and 52.7/29.9/27.8
> alike. Anything in a document dated before 8 September that did not come out of
> `compare_log.py` needs regenerating.

---

## Files

| File | What it is | Phase |
|---|---|---|
| `plant.py` | 0-D single-zone SI cycle model. `Geometry()` **is** the B58B30O1 inline-six from the 2023 GR Supra — 2997.5 cc; `b58()` is an alias for it. Wiebe burn, Woschni heat transfer, Chen-Flynn friction, Douaud-Eyzat knock integral. One cycle ≈ 4.6 ms. | B |
| `thermal.py` | 3-node lumped-capacitance network — block/coolant, oil, turbine housing — with a stand-in thermostat (the real B58 uses a heat-management valve; see REFERENCES.md section 2). | B |
| `validate.py` | **Regenerates the validation table.** Eleven quantities against published bands. Currently 8 of 11 inside; the three misses are explained in validation_table.md. | B |
| `extract_steady.py` | Finds steady operating points in a BimmerLink CSV and **de-duplicates** them. | B |
| `compare_log.py` | Runs the plant at those points and scores the error. | B |
| `check_map.py` | Derives MBT and knock-limited spark maps. Confirms the calibration surface has the right shape. | B |
| `engine_env.py` | Gymnasium environment. Baseline ECU, vehicle model, inner PI torque loop, baseline-relative reward, preview ablation switch. | C |
| `test_reward.py` | **The Phase C sanity checks.** Run before trusting any training curve. | C |
| `check_premise.py` | Races a reactive against a predictive hand-written policy. Run before writing any RL code. | C |
| `train.py` | **Trains a SAC agent.** A C1 run (50 000 steps) is about 45 minutes per seed run on its own — measured, see its docstring; Phase D's runs took 59–75 minutes each with several running at once (Phase D's run logs). | C |
| `analyse_phase_d.py` | **The project's result.** The preregistered Phase D statistic, and nothing else. | D |
| `build_dataset.py` | **All drives into one master dataset.** Run it whenever a new CSV arrives. | B |
| `generality_test.py` | The H/τ experiment. H1, H2, and H2b. | F |
| `verify_docs.py` | **Checks the documents against the data.** Every published figure recomputed from the shipped data, plus a check that no document still quotes a **retired** one. It prints its own total — read that rather than quoting a count from here. Run it before quoting anything. | all |
| `REFERENCES.md` | **Where every number we did not measure comes from.** Written for a non-specialist. Marks each published band and each thermal parameter CONFIRMED, UNVERIFIED, MEASURED or ASSUMED. Read before quoting a published band. | all |
| `DOCUMENT_STATUS.md` | Which team PDFs still quote void numbers. Read before handing one to the supervisor. | all |
| `logs/CHANNEL_CENSUS.md` | All 656 channels this car offers, live vs dead, from the two reconnaissance logs. Settles what can and cannot be measured. | B |
| `app/` | **The live supervisor.** Runs the plant and the thermal network alongside the car in real time and estimates what it has no sensor for. See below. | — |

---

## The live app

```bash
python -m app.server --replay logs/raw/7475b5d7-20260908_142743.csv --speed 8
python -m app.server --live                  # needs `pip install obd`
```

Then `http://localhost:8000` — the dashboard, `/driver` for the one-number
driving screen, `/review` for what was marked on past drives.

**Develop in replay. You do not need the car.** The 295 minutes in `logs/raw/`
are enough for five people to work against the same drives at once.

The point of it is `app/estimator.py`: this car cannot report turbine
temperature, so the app runs the validated physics next to the live stream and
estimates it. Everything else is supporting cast. Because it reuses
`plant.predict`, `plant.map_from_airflow`, `plant.charge_temperature` and
`thermal.ThermalNetwork` unchanged, it **inherits Phase B's validation and
Phase B's limits** — 8 of 11 bands, three documented misses, and a load range
checked only where the steady points sit. It must not imply more confidence
than that, and `t_turb_c` is a model output with an assumed heat capacity
(REFERENCES.md section 4), never a reading.

Three rules, and `app/test_replay.py` asserts all of them:

| rule | what it means |
|---|---|
| **read-only, permanently** | no write to the vehicle, ever. No mode 08, no bus writes. Suggesting an ECU parameter as text is a different product from applying one, and they must never share a code path. |
| **raw data never reaches disk** | the stream is memory → websocket → gone. Only what the model *marks* is persisted, to `app/review_log.jsonl`. |
| **the channel budget is the design constraint** | the adapter polls one channel per round trip, so the link's rate divides by the channel count: 26 channels → 7.5 s each, 7 → 1.45 s. Six channels are live because the estimator cannot work without them. A seventh costs every other channel ~14 %. |

```bash
python -m app.test_replay          # fast, pins pull01 + both product rules
python -m app.test_replay --full   # adds the whole 7475b5d7 replay
```

---

## Two entry points you will actually call

```python
from plant import predict, map_from_airflow

out = predict(rpm=2500, map_kpa=90, iat_k=313, ect_k=363,
              spark_btdc=22, lam=1.0)          # -> dict of named outputs
```

`predict()` is the shared plant interface. `battery.py` must expose the same
contract — keyword inputs in, a dict of named outputs out — so that the agent
code drives either plant unchanged. Do not rename it.

```python
map_kpa = map_from_airflow(mdot_air_gps, rpm, iat_k)
```

Use this to get the model's load input from **measured air mass flow** rather
than from a logged pressure channel. See the next section.

---

## Six things that are known to be wrong, and are not bugs to fix quietly

### 1. Never rely on a default geometry — settled the hard way

`Geometry()` and `b58()` now return the same object: one engine, the B58 I6.
They did not before, and the difference cost three weeks of results computed on
a four-cylinder. **Every `run_cycle()` call in this repo passes `geo=GEO`
explicitly**, and it should stay that way even though the default is now
correct. If a second plant is ever added, pass it.

### 2. Never feed the logged "manifold pressure" into the model — settled

The parked-idle test answered this on 7 September. At warm idle — 684 rpm,
coolant 81 °C, stationary — the channel named "Intake manifold absolute
pressure" reads **13.49** against an ambient of **14.23**. A throttled engine at
idle sits near a third of ambient. The air mass channel, on the same samples,
implies **31.2 kPa**, which is the textbook value.

**It is a pre-throttle sensor.** Near ambient at idle; equal to manifold pressure
only under boost, when the throttle is open and the two are the same thing.

Feeding that channel to the model as its load input was measured at about
**75 % air-mass error**, on the eleven-point set that predated the master
dataset. Inverting the air mass channel instead gives a load residual of
**1.4 %** over the 26 pooled points, 30–75 kPa. `compare_log.py` inverts the
air mass by default; `--map-from-log` exists only to reproduce the failure, and
it now needs `extract_steady.py`'s schema, because the master point file no
longer carries the logged pressure column.

**Be precise about what that 1.4 % is.** It compares BMW's `Relative air
filling` channel against the measured air mass flow, through the displacement
and three defined constants. The breathing model cancels out of that comparison
— `eta_v`, the residual-gas fraction and the charge temperature all drop out of
the algebra — so **it is not a test of the breathing model**. Delete the
breathing model entirely and the number does not move. See CLAUDE.md mistake 12.

Two things it does earn. It pins `Relative air filling` to the DIN reference
state, 1013 mbar and 0 °C: the derived k = 0.831 against a fitted 0.839, where
a 20 °C reference would demand 0.891, which the fit excludes. And it is
blind-sensitive to displacement — forced onto a 2.0 L inline-four the derived
residual goes to **48.1 %** while the fitted form still reports 1.1 %, which is
why the fitted form could never have caught the wrong-engine mistake.

Note the direction: **1.1 %** fitted, **1.4 %** derived. Dropping the one free
parameter makes the residual rise, which is the honest direction — one fitted
parameter should fit better. The claim is zero fitted parameters, not a smaller
number.

### 3. Peak power is not a prediction of this model

Manifold pressure is an **input**. `plant.boost_ceiling_kpa` now bounds it to
what the car was observed to do — refitted on 74 013 quasi-steady
samples — and `SupervisoryTunerEnv.MAP_CEIL_KPA` is the measured 250 kPa rather
than the round 240 that used to sit there. But an operating line is not a
compressor map: no efficiency islands, no speed lines, because the car has no
turbo speed sensor and no pre-intercooler temperature. Full-load points remain
outside the validated envelope. Say so rather than tuning towards a number.

**Two further things you must state.** The MAF channel saturates at exactly
1020 kg/h on six drives, so the envelope above 0.314 kg/s corrected flow is
unmeasured, not merely sparse. And the air-mass inversion used to disagree with
the logged boost channel by **+23.7 %** under boost — which this project blamed
on `volumetric_efficiency()` for two weeks. **It was the charge temperature.**
The channel feeding the inversion was a compressor-outlet reading, not the
charge; modelling the charge temperature instead (`plant.charge_temperature`)
brings the disagreement to **+1.9 %** and clears the breathing model entirely.
See CLAUDE.md mistake 13.

That comparison is 762 boosted model readings against 1097 logged readings of
the car's own `Boost pressure` channel — the counts `verify_docs.py` asserts on
the current dataset. The model side
is gated above 200 kPa on purpose, not by taste: the logged side filters at
15 psi gauge, and (15 + 14.23) × 6.894757 = 201.5 kPa absolute, so a 200 kPa
gate selects the same operating region by construction. `ambient + 8 K`
scored 0.7 % when the correction was made on 10 September, on the smaller
dataset of the time, and is rejected — it is a knob tuned to the target, and the shipped
formula carries no parameter fitted to the boost channel.

### 4. The turbine time constant

Stepping the load and reading 63.2 % off the response — which is what Phase F
step F1 tells you to do — gives **48.0 s** on the climb, inside the 40–120 s
published band. **That is ONE measurement, not two.** The turbine node is
decoupled from the block and oil, and `validate.py` holds fuel flow, exhaust
flow and EGT constant through the step, so the response is an exact
first-order exponential whose time constant IS `C/UA`. The step response
recomputes `C/UA`; it cannot corroborate it.

**τ is not one number.** Over the locked episode it runs from 40 to 239 s,
because UA rises with exhaust flow — 48.0 s on the climb, far longer at cruise
and idle. Quote τ with its operating point, always. And the housing's heat
capacity is ASSUMED (REFERENCES.md section 4), so every τ is an assumed number
to within that constant.

<!-- RETIRED-OK: 50.3, 39.5 -- the superseded figures, named so they are recognised -->
*(This section used to set a `C/UA` of 50.3 s beside the 48.0 s as two methods
that nearly agree, and explained the gap as the gas-side heat transfer
coefficient rising with exhaust flow, "so the node is not a pure first-order
system". Under `validate.py`'s constant-flow step that explanation cannot
apply: the 50.3 s was `C/UA` at an assumed exhaust flow that `AUDIT.md` M12
condemned. Corrected 22 September; see `CLAUDE.md`, Known limitations.)* The
old **39.5 s** figure was the four-cylinder's and is void.

### 5. The reward hack is closed — after being reopened by the engine fix

It was real: a policy that pinned boost trim to minimum — refusing to make
torque — scored **+0.285** against neutral's **+0.003**.

The cause was the preference vector. `self.w` was drawn from an unconstrained
Dirichlet over three terms, so the tracking weight could land near zero, and on
those episodes refusing torque was free. **Delivering the requested torque is the
job, not a preference.** Tracking now has a floor (`TRACK_W_MIN = 0.45`) and the
remainder is split over fuel and life, which is the two-dimensional trade-off the
Pareto stretch goal actually needs.

It came back. That fix was verified on the four-cylinder, in a scenario so light
the torque constraint never bound — at 244 Nm the real B58 answers with boost to
spare, so pinning the boost trim to minimum did not actually starve anything. On
the corrected engine at a grade that loads it, the starver scored **+0.011**
against neutral's **−0.027**.

A weight floor alone cannot close this, because a linear tracking penalty is
tradeable against damage at *some* exchange rate. The penalty now has a
tolerance band and a steep hinge — `TRACK_TOL = 0.05`, `TRACK_HINGE = 25` —
sized so that **no achievable damage saving pays for a sustained torque shortfall
beyond 10 %**. That sentence belongs in Chapter 4: it is why the Phase D numbers
mean what they claim.

<!-- RETIRED-OK: 0.004, 0.280 -- what the gate printed when the hinge landed -->
`test_reward.py` passes all four checks today (`FULL_RUN.txt`, 21 September):
neutral −0.00038, starver **−0.90349**, preview ablation live, all finite. When
the hinge landed it printed neutral −0.004 and starver −0.280; the scenario
and the gearbox have both moved since, which is why the next sentence exists.

**Run it after any change to the plant or the scenario, not just the reward.** A
reward is only safe relative to the dynamics it scores.

### 6. The MAF channel saturates, and it does not say so

`Air mass flow` tops out at exactly **1020.0 kg/h** on six separate drives,
**547 samples** — while `Air mass flow participating in combustion` reaches
1233 kg/h on those same samples, a median ratio of **1.095**. A pinned sample
under-reports air, so anything inverted from it is biased at the very top of
the envelope. `build_dataset.py` flags them as `maf_pinned` and excludes them
from `stable`; they are not repaired by substituting the other channel, because
that is the ECU's modelled trapped charge, a different quantity, and splicing
two definitions puts a step in the middle of the curve.

Before fitting anything to a channel, check whether it saturated. A flat
maximum repeated across drives is the tell.

---

## The headline numbers moved, and why

<!-- RETIRED-OK: section 527.2, 51.4, 26.9, 2.13, 1.38, 8.43, 244, 930 -- the version history of the headline; every figure named here is one it moved AWAY from -->

`BaselineECU` was guessed. It is now calibrated against the real car: its
enrichment and spark fits were built on eight drives of the ten in the
manifest (295.0 minutes in all). Two things were wrong, and the
second one was distorting every result.

**Its enrichment map has been wrong three times, and the third time it was the
variable that was wrong.** This is the clearest lesson in the project about the
cost of fitting to too little data.

| version | behaviour | verdict |
|---|---|---|
| v1, guessed | enriches from 120 kPa down to 0.82 | too early |
| v2, from the 41.8-min cruise | lambda 1.00 everywhere | never enriches |
| v3, from two drives | stoichiometric to 207 kPa, then down to 0.85 | right effect, wrong variable |
| **v4, from eight drives** | **function of engine speed and sustained dwell** | **current** |

v2 came from four seconds above 100 % load. v3 came from seventeen. The two
8 September drives took that to **208 seconds above 207 kPa**. Over the 1341
rows above `ENR_LOAD` = 180 kPa, what correlates with lambda is engine speed
(-0.47), air mass flow (-0.41), and how long the engine has been held above the
gate (-0.44) — and the correlation between lambda and manifold pressure is
**+0.11**, indistinguishable from zero. Read all four with their error bar:
the 1341 rows are forward-filled and hold only about 67 independent readings,
so the standard error is about 0.12. Manifold pressure carries no detectable
signal, which is enough to reject a load table; it is not evidence that load
points the other way.

<!-- RETIRED-OK: 0.23, -0.49, 1055 -->
*(This paragraph read +0.23, "with the wrong sign for a load table: more boost
goes with a leaner mixture", air mass flow at -0.49, and 1055 samples, until
22 September. At a standard error near 0.12 the wrong-sign argument never
held, and it is withdrawn — CLAUDE.md mistake 4.)*

(The gate reads 180 kPa, not 200, because manifold pressure changed definition
with the charge-temperature correction. On the corrected scale 180 kPa selects
exactly the samples that 200 kPa selected on the old one, and every figure below
reproduces without a refit. CLAUDE.md mistake 13.)

Median lambda, pooled, above 180 kPa:

| rpm / dwell | 0-4 s | 4-8 s | 8+ s | n |
|---|---|---|---|---|
| 1000-3500 rpm | 0.99 | 0.99 | 0.98 | 441 |
| 3500-4500 rpm | 0.99 | 0.98 | 0.90 | 235 |
| 4500-7000 rpm | 0.98 | 0.87 | 0.79 | 665 |

Read the bottom row across: at the same load the car runs stoichiometric for
the first seconds of a pull and enriches only once it has been up there a
while. Read the first column down: at 2000 rpm it never enriches at all.
**Enrichment on this engine is component protection, not a load table** — and
since enrichment is one of the actions the agent controls, a load-only baseline
would have enriched on the wrong signal and flattered the agent for the wrong
reason.

The remaining limitation: dwell above the 180 kPa gate stands in for turbine
inlet temperature, which this car does not expose. The weakest cell of the fit
is 3500–4500 rpm at long dwell — observed 0.90 against a modelled 0.93, on the
235 samples in that band. Say both in Chapter 3.

**Its spark map was not knock-limited.** At 3000 rpm and 140 kPa the old baseline
commanded 26.9° BTDC, giving a knock integral of **2.13**. Production engines sit
just under 1.0. Across the load range the old baseline ran KI 1.38–2.13 —
detonating continuously — and the damage model's knock penalty
(`40·max(0, KI−0.85)²`) turned that into 11–65 units per second.

That is where 527.2 came from. It was mostly a baseline that knocked.

The new spark map is two pieces: a straight-line fit to eleven measured steady
points below about 90 kPa (residual RMS 1.66° against the old map's 8.43°), and
above that the **knock limit computed from the plant's own Douaud-Eyzat
integral**, because that is what a real calibration is up there. Do not extend
the fitted line into boost — extrapolated, it puts the baseline at +21° at
240 kPa, which no turbo engine survives.

| | v1 guessed baseline | v2 calibrated, I4 | **v3 calibrated, correct I6** |
|---|---|---|---|
| engine | 2.0 L I4 | 2.0 L I4 | **3.0 L I6** |
| baseline damage | 527.2 | 51.4 | **829.2** |
| reactive damage reduction | −32 % | −42 % | **−33.8 %** |
| predictive damage reduction | −62 % | −46 % | **−47.2 %** |
| **preview advantage** | 30 points | 4 points | **13.4 points** |

**The v3 column is VOID** (`AUDIT.md` C1 and C3). It was measured against a
baseline with its cooling switched off, and its preview edge rests on an
ablation identity that could not fail. It stays in this table only as the
record of how the headline moved. What `check_premise.py` prints today is in
the box near the top of this file: baseline 959.8 at 884 °C, and hand-written
preview −0.4 points against current-grade.

<!-- RETIRED-OK: 110, 297, 879, 244 -->
Baseline damage was larger in v3 because the scenario finally loaded the
engine: a 12 % grade at 110 km/h in 42 °C air asked 297 Nm, and the turbine
reached 879 °C — a peak `AUDIT.md` C2 later traced to the baseline's
scheduling error, not to the engine. The old 10 % / 90 km/h scenario asked
244 Nm, which the real engine supplies without effort — the constraint never
bound, so there was no trade-off to study. The locked scenario is now 12 % at
130 km/h, and it binds.

<!-- RETIRED-OK: 13.4 -->
**Read that last row carefully, and read the whole row, not the number.** The
preview advantage has now been 30 points, 4 points and 13.4 points (void —
`AUDIT.md` C1: measured against a baseline with its cooling switched off; and
the identity it leaned on could not fail, C3). The first two were real
measurements of different systems; the 13.4 was not a measurement of preview
at all. The number is not the result; the *ablation* is.

> ### DO NOT TAKE THE NEXT PARAGRAPH INTO A VIVA. It is refuted twice over.
>
> It says preview-disabled landing on reactive "to the decimal, every single
> time" makes any gap "attributable to preview and nothing else", and calls that
> the sentence to defend.
>
> **It could not have come out any other way.** With `use_preview=False` the
> preview vector is zeros, so `p_predictive` computes `k_ahead = 0` and returns
> `p_reactive`'s own action on every step. The two rows are the same rollout.
> An identity that cannot fail is not evidence — `AUDIT.md` C3, 15 September.
>
> **And the real ablation has now been run, and it disagrees.** Phase D,
> 21–22 September: eight trained blinded agents against eight trained sighted
> ones, paired by seed, preregistered before any of them started. **Preview is
> not significant** — 5 of 8 positive, mean +4.8 damage units, sign test
> p = 0.3633, permutation p = 0.4922. Seed 3 says +387, seed 5 says −288.
>
> **The sentence to defend in the viva is the opposite one:** *we built the
> ablation that could fail, ran it eight times, and it did not separate.*
> Separately, and worth defending on its own: the trained agent beats the
> `current-grade` comparator by **+29 to +34 points** on five of eight seeds, so
> learned supervision works even though preview specifically does not separate
> from seed noise at the C1 budget.
>
> `python analyse_phase_d.py`.

<!-- RETIRED-OK: section 930, 1152, 0.3 -- the refuted viva claim and the old trigger, kept so they are recognisable -->

*The refuted paragraph, as it stood — quoted so it is recognisable, not to be defended:*
*"And the ablation has held exactly every single time — preview-disabled lands on
reactive to the decimal, across two engines, two scenarios and two protection
triggers. Whatever the gap is, it is attributable to preview and nothing else.
That is the sentence to defend in the viva."*

One caveat to carry into Phase D. The protection trigger in `check_premise.py`
used to be a hard-coded 930 K, and on the correct engine the turbine reached
1152 K, so both policies saturated and the gap collapsed to 0.3 points for
reasons that had nothing to do with preview. It is now anchored to the damage
model — 1123 K, the knee of `exp((t_turb − 1123)/45)` — which is a statement
about the component rather than about one episode. **If you change the damage
model, change the trigger with it.**

## The Phase F protocol changed

<!-- RETIRED-OK: section 16.5, 18.0, 26.0, 50.3, 57.0, 9.7 -->

> **EVERY PREVIEW FIGURE IN THIS SECTION IS VOID** (`AUDIT.md` C1 and M12).
> The whole sweep was scored against the same cooling-disabled baseline as the
> premise table, and its τ axis assumed an exhaust flow the climb does not
> make. Re-run `generality_test.py` and read what it prints; the tables below
> are kept only so the old values are recognisable. **And do not use H/τ to
> rescue Phase D's null** — that reading was drafted and refuted
> (`results/PREREGISTRATION.md` limit 8).

`generality_test.py` prints three tables. H2b was, when this section was
written, the one it told you to use; it no longer is — see below.

With a fixed constraint threshold, the two largest thermal masses never get hot
enough to violate it, so two of the five sweep points return nothing. H2b sets
the threshold per configuration to the 80th percentile of the *unprotected*
policy's own temperature trace, so every configuration spends the same fraction
of the drive in violation and every row yields a data point.

*Historical, and void with the tables:* that change was read at the time as
making the result more interesting — the void sweep showed a preview advantage
**peaked, not monotonic**, near zero at H/τ ≈ 4, largest around H/τ ≈ 0.6,
decaying again as H/τ → 0.06 — and the section called a peak a stronger claim
than a slope and exactly what the physical argument predicts. **That reading
rests on the void table and is withdrawn**, and it is not to be used to explain
Phase D's null (the box above; `results/PREREGISTRATION.md` limit 8).

**H2b's threshold rule does not survive the correct engine, and this is the
open Phase F problem.** The p80 rule assumes the temperature spends a minority of
the episode near its peak. The standard scenario is a sustained climb — nine of
its twelve minutes at the top — so p80 lands on the peak and the top *three* rows
now saturate at 100 % for both policies.

`check_premise.py` hit the same wall and solved it by anchoring to the damage
model instead of to a percentile. **`generality_test.py` now imports the same
constant** — `engine_env.TURB_PROTECT_K = 1123 K`, the knee of the turbine damage
term — so the two experiments cannot report different protection limits. Until
H2b's percentile rule is replaced, the fixed-limit **H2** table was the one to
use — and it is void too, per the box at the top of this section:

| C_turb J/K | τ s | H/τ | reactive | predictive | preview edge |
|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 79.6 % | 96.1 % | 16.5 pts |
| 2500 | 21.0 | 1.43 | 78.7 % | 96.7 % | 18.0 pts |
| 6000 | 50.3 | 0.60 | 73.2 % | 99.1 % | **26.0 pts** |
| 18000 | 150.9 | 0.20 | — | — | never exceeds the limit |

In that void table, preview edge rose as τ grew — 16.5 → 18.0 → 26.0 points as
H/τ fell from 4.47 to 0.60 — and then the component became so massive that the
constraint stopped binding at all. It was read as the direction the physical
argument predicts; that reading is void with the table.

**These numbers moved a long way when the trigger was unified**, from
0.0/0.1/0.2 points at the old 930 K to 16.5/18.0/26.0 at 1123 K. Nothing about
the plant changed; the threshold did. Say so in the methods, and report the
threshold with every figure. A preview advantage quoted without the limit it was
measured against is not a result.

H2b, for the record, was peaked rather than monotone: 0.0 points for the three
lightest masses (all saturated at 100 %), **57.0 points** at H/τ = 0.20, and 9.7
points at H/τ = 0.06. The saturation is the protocol flaw above, not physics.

---

## What is NOT here

The surrogate ensemble and the SAC-Lagrangian agent. Both are specified in the
handbook with reference code, neither has been built or run, and nothing ships
here that has not been verified.

`battery.py` is Phase E. When you write it, give it `predict()`.
