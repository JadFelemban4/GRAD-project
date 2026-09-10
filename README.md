# Engine Supervisor — Phase A–F code

> **Opening this in Claude Code?** Read `CLAUDE.md` first — it carries the
> project's claim, its current state, and the eleven mistakes already made.

Working code for the validated parts of the project. Every number quoted in the
handbook is this code's actual output, and `validate.py` regenerates the ones
that go in Chapter 3.

```
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Python 3.11 or newer.

---

## Run these four, in this order, on day one

```
python plant.py            #  ~30 s   spark, lambda and IAT sweeps
python validate.py         #  ~4 min  regenerates the validation table
python check_premise.py    #  ~90 s   the result the whole project rests on
python verify_docs.py      #  ~20 s   confirms the documents still match the data
```

All five of you should see the same numbers from `check_premise.py`:
**baseline 829.2 · reactive 548.6 · predictive 437.6 · preview-disabled 548.6.**

That last pair matters most. Disabling preview collapses the predictive policy
onto the reactive one exactly, which means whatever gap exists is attributable
to preview information and nothing else. Preview advantage: reactive cuts damage
33.9 %, predictive 47.2 % — **13.4 points**.

> **THESE NUMBERS CHANGED AGAIN ON 8 SEPTEMBER, AND THIS TIME BECAUSE THE
> SIMULATION WAS THE WRONG ENGINE.** `plant.Geometry` defaulted to a generic
> 2.0 L inline-**four**; `b58()`, the real 3.0 L inline-**six**, was an opt-in
> override that no call site ever passed. Everything downstream of `run_cycle()`
> — this environment, the premise check, the reward tests, the H/τ sweep, ten of
> the eleven validation rows — ran a 1998 cc four-cylinder. Torque was 33 % low.
>
> Phase B was not affected: `predict()` and `map_from_airflow()` always used the
> B58, so the load residual (now 2.3 %) stands.
>
> Every earlier set of premise numbers is void — 527/357/199, and 52.7/29.9/27.8
> alike. Anything in a document dated before 8 September that did not come out of
> `compare_log.py` needs regenerating.

---

## Files

| File | What it is | Phase |
|---|---|---|
| `plant.py` | 0-D single-zone SI cycle model. `Geometry()` **is** the B58B30O1 inline-six from the 2023 GR Supra — 2997.5 cc; `b58()` is an alias for it. Wiebe burn, Woschni heat transfer, Chen-Flynn friction, Douaud-Eyzat knock integral. One cycle ≈ 4.6 ms. | B |
| `thermal.py` | 3-node lumped-capacitance network — block/coolant, oil, turbine housing — with a thermostat. | B |
| `validate.py` | **Regenerates the validation table.** Eleven quantities against published bands. Currently 8 of 11 inside; the three misses are explained in validation_table.md. | B |
| `extract_steady.py` | Finds steady operating points in a BimmerLink CSV and **de-duplicates** them. | B |
| `compare_log.py` | Runs the plant at those points and scores the error. | B |
| `check_map.py` | Derives MBT and knock-limited spark maps. Confirms the calibration surface has the right shape. | B |
| `engine_env.py` | Gymnasium environment. Baseline ECU, vehicle model, inner PI torque loop, baseline-relative reward, preview ablation switch. | C |
| `test_reward.py` | **The Phase C sanity checks.** Run before trusting any training curve. | C |
| `check_premise.py` | Races a reactive against a predictive hand-written policy. Run before writing any RL code. | C |
| `train.py` | **Trains a SAC agent.** One seed per person, overnight — see its docstring for why. | C |
| `build_dataset.py` | **All drives into one master dataset.** Run it whenever a new CSV arrives. | B |
| `generality_test.py` | The H/τ experiment. H1, H2, and H2b. | F |
| `verify_docs.py` | **Checks the documents against the data.** Twenty-five published figures recomputed, plus a check that no document still quotes a **retired** one. Run it before quoting anything. | all |
| `DOCUMENT_STATUS.md` | Which team PDFs still quote void numbers. Read before handing one to the supervisor. | all |
| `logs/CHANNEL_CENSUS.md` | All 656 channels this car offers, live vs dead, from the two reconnaissance logs. Settles what can and cannot be measured. | B |

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

On the same eleven operating points: using that channel gives 75.3 % air-mass
error and a 17.2 % load residual. Using `map_from_airflow()` gives **2.3 %**
over the seventeen pooled points that survive the window checks.

`compare_log.py` inverts the air mass by default. `--map-from-log` exists only to
reproduce the failure for the report.

### 3. Peak power is not a prediction of this model

Manifold pressure is an **input**. `plant.boost_ceiling_kpa` now bounds it to
what the car was observed to do — refitted 8 September on 30 534 quasi-steady
samples — and `SupervisoryTunerEnv.MAP_CEIL_KPA` is the measured 250 kPa rather
than the round 240 that used to sit there. But an operating line is not a
compressor map: no efficiency islands, no speed lines, because the car has no
turbo speed sensor and no pre-intercooler temperature. Full-load points remain
outside the validated envelope. Say so rather than tuning towards a number.

**Two further things you must state.** The MAF channel saturates at exactly
1020 kg/h on four drives, so the envelope above 0.303 kg/s corrected flow is
unmeasured, not merely sparse. And above 200 g/s the air-mass inversion and the
logged boost channel disagree by 28 % — 297 kPa against 233 kPa — because
`volumetric_efficiency()` is fitted at part load and the pre-throttle
temperature sensor lags during a pull. The inversion is right at part load and
wrong under boost.

### 4. The turbine time constant

`C/UA` gives **50.3 s**. Stepping the load and reading 63.2 % off the response —
which is what Phase F step F1 tells you to do — gives **48.0 s** on the correct
engine, inside the 40–120 s published band. They differ slightly because the
gas-side heat transfer coefficient rises with exhaust flow, so the node is not a
pure first-order system. <!-- RETIRED-OK -->
The old **39.5 s** figure was the four-cylinder's and is void.

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

`test_reward.py` now passes all four checks: neutral −0.004, starver **−0.280**,
preview ablation live, all finite.

**Run it after any change to the plant or the scenario, not just the reward.** A
reward is only safe relative to the dynamics it scores.

### 6. The MAF channel saturates, and it does not say so

`Air mass flow` tops out at exactly **1020.0 kg/h** — the same number on four
separate drives, 192 samples — while `Air mass flow participating in
combustion` reaches 1233 kg/h on those same samples. A pinned sample
under-reports air, so anything inverted from it is biased at the very top of
the envelope. `build_dataset.py` flags them as `maf_pinned` and excludes them
from `stable`; they are not repaired by substituting the other channel, because
that is a different quantity and splicing the two puts a step in the curve.

Before fitting anything to a channel, check whether it saturated. A flat
maximum repeated across drives is the tell.

---

## The headline numbers moved, and why

`BaselineECU` was guessed. It is now calibrated against 41.8 minutes of the real
car. Two things were wrong, and the second one was distorting every result.

**Its enrichment map has been wrong three times, and the third time it was the
variable that was wrong.** This is the clearest lesson in the project about the
cost of fitting to too little data.

| version | behaviour | verdict |
|---|---|---|
| v1, guessed | enriches from 120 kPa down to 0.82 | too early |
| v2, from the 41.8-min cruise | lambda 1.00 everywhere | never enriches |
| v3, from two drives | stoichiometric to 230 kPa, then down to 0.85 | right effect, wrong variable |
| **v4, from eight drives** | **function of engine speed and sustained dwell** | **current** |

v2 came from four seconds above 100 % load. v3 came from seventeen. The two
8 September drives took it to **198 seconds**, and at that sample size the
correlation between lambda and manifold pressure is **-0.05 — none at all**.
What correlates is engine speed (-0.56), air mass flow (-0.49), and how long the
engine has been held above 200 kPa (-0.47), over the 1055 samples above 200 kPa.

Median lambda, pooled, above 200 kPa:

| rpm / dwell | 0-4 s | 4-8 s | 8+ s | n |
|---|---|---|---|---|
| 1000-3500 rpm | 0.99 | 0.99 | 0.98 | 422 |
| 3500-4500 rpm | 0.99 | 0.98 | 0.90 | 168 |
| 4500-7000 rpm | 0.98 | 0.87 | 0.79 | 465 |

Read the bottom row across: at the same load the car runs stoichiometric for
the first seconds of a pull and enriches only once it has been up there a
while. Read the first column down: at 2000 rpm it never enriches at all.
**Enrichment on this engine is component protection, not a load table** — and
since enrichment is one of the actions the agent controls, a load-only baseline
would have enriched on the wrong signal and flattered the agent for the wrong
reason.

The remaining limitation: dwell above 200 kPa stands in for turbine inlet
temperature, which this car does not expose. Say so in Chapter 3.

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
| reactive damage reduction | −32 % | −42 % | **−33.9 %** |
| predictive damage reduction | −62 % | −46 % | **−47.2 %** |
| **preview advantage** | 30 points | 4 points | **13.4 points** |

Baseline damage is larger now because the scenario finally loads the engine: a
12 % grade at 110 km/h in 42 °C air asks 297 Nm, and the turbine reaches 879 °C.
The old 10 % / 90 km/h scenario asked 244 Nm, which the real engine supplies
without effort — the constraint never bound, so there was no trade-off to study.

**Read that last row carefully, and read the whole row, not the number.** The
preview advantage has now been 30 points, 4 points and 13.4 points. Every one of
those was a real measurement of a different system. The number is not the
result; the *ablation* is.

And the ablation has held exactly every single time — preview-disabled lands on
reactive to the decimal, across two engines, two scenarios and two protection
triggers. Whatever the gap is, it is attributable to preview and nothing else.
That is the sentence to defend in the viva.

One caveat to carry into Phase D. The protection trigger in `check_premise.py`
used to be a hard-coded 930 K, and on the correct engine the turbine reaches
1152 K, so both policies saturated and the gap collapsed to 0.3 points for
reasons that had nothing to do with preview. It is now anchored to the damage
model — 1123 K, the knee of `exp((t_turb − 1123)/45)` — which is a statement
about the component rather than about one episode. **If you change the damage
model, change the trigger with it.**

## The Phase F protocol changed

`generality_test.py` now prints three tables. H2b is the one to use.

With a fixed constraint threshold, the two largest thermal masses never get hot
enough to violate it, so two of the five sweep points return nothing. H2b sets
the threshold per configuration to the 80th percentile of the *unprotected*
policy's own temperature trace, so every configuration spends the same fraction
of the drive in violation and every row yields a data point.

That change also makes the result more interesting. The preview advantage is
**peaked, not monotonic** — near zero at H/τ ≈ 4 where a reactive policy already
copes, largest around H/τ ≈ 0.6, decaying again as H/τ → 0.06 where the horizon
is far too short to matter. A peak is a stronger claim than a slope, and it is
exactly what the physical argument predicts.

**H2b's threshold rule does not survive the correct engine, and this is the
open Phase F problem.** The p80 rule assumes the temperature spends a minority of
the episode near its peak. The standard scenario is a sustained climb — nine of
its twelve minutes at the top — so p80 lands on the peak and the top *three* rows
now saturate at 100 % for both policies.

`check_premise.py` hit the same wall and solved it by anchoring to the damage
model instead of to a percentile. **`generality_test.py` now imports the same
constant** — `engine_env.TURB_PROTECT_K = 1123 K`, the knee of the turbine damage
term — so the two experiments cannot report different protection limits. Until
H2b's percentile rule is replaced, the fixed-limit **H2** table is the one to use:

| C_turb J/K | τ s | H/τ | reactive | predictive | preview edge |
|---|---|---|---|---|---|
| 800 | 6.7 | 4.47 | 79.6 % | 96.1 % | 16.5 pts |
| 2500 | 21.0 | 1.43 | 78.7 % | 96.7 % | 18.0 pts |
| 6000 | 50.3 | 0.60 | 73.2 % | 99.1 % | **26.0 pts** |
| 18000 | 150.9 | 0.20 | — | — | never exceeds the limit |

Preview edge rises as τ grows — 16.5 → 18.0 → 26.0 points as H/τ falls from 4.47
to 0.60 — and then the component becomes so massive that the constraint stops
binding at all. That is the direction the physical argument predicts.

**These numbers moved a long way when the trigger was unified**, from
0.0/0.1/0.2 points at the old 930 K to 16.5/18.0/26.0 at 1123 K. Nothing about
the plant changed; the threshold did. Say so in the methods, and report the
threshold with every figure. A preview advantage quoted without the limit it was
measured against is not a result.

H2b, for the record, is peaked rather than monotone: 0.0 points for the three
lightest masses (all saturated at 100 %), **57.0 points** at H/τ = 0.20, and 9.7
points at H/τ = 0.06. The saturation is the protocol flaw above, not physics.

---

## What is NOT here

The surrogate ensemble and the SAC-Lagrangian agent. Both are specified in the
handbook with reference code, neither has been built or run, and nothing ships
here that has not been verified.

`battery.py` is Phase E. When you write it, give it `predict()`.
