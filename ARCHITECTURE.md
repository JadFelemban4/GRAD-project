# ARCHITECTURE.md — how the code fits together

Every symbol below was read out of the source. If you change a signature, change
this file in the same commit.

---

## The one-line summary

A 0-D engine cycle model feeds a 3-node thermal network; a Gymnasium environment
wraps both, runs a **calibrated baseline ECU in parallel** as the reference, and
scores an agent that only ever **trims** that baseline.

---

## Dependency graph

```
                 plant.py  (0-D cycle model, no dependencies)
                     |
        +------------+-------------+
        |                          |
   thermal.py                 engine_env.py
   (3-node network)          (Gymnasium env, BaselineECU,
        |                     Vehicle, PI torque loop)
        |                          |
        |          +---------------+---------------+---------+
        |          |               |               |         |
        |    check_premise.py  test_reward.py  train.py  generality_test.py
        |     (the premise)    (Phase C gate)   (SAC)      (the H/tau sweep)
        |
   validate.py                build_dataset.py  ->  data/*.csv
   (published bands)          (logs -> dataset)          |
                                                   compare_log.py
                                                   (model vs car)
                                                         |
                                                   verify_docs.py
                                                   (docs vs data)
```

`plant.py` imports nothing from this repo. Everything else flows downhill from
it. **That is why a wrong default in `plant.Geometry` silently corrupted five
downstream results for three weeks.**

---

## `plant.py` — the 0-D cycle model

Single-zone spark-ignition cycle. One cycle ≈ 4.6 ms.

| Symbol | Kind | Notes |
|---|---|---|
| `Geometry` | dataclass | **IS** the B58B30O1 inline-six, 2997.5 cc |
| `b58()` | function | alias — returns the same object as `Geometry()` |
| `Operating` | dataclass | rpm, map_kpa, iat_k, ect_k, spark_btdc, lam, p_exh_kpa |
| `CycleResult` | dataclass | torque_nm, mdot_fuel_gps, egt_c, knock_integral, … |
| `run_cycle(op, geo, dtheta=0.5)` | function | the crank-angle integration |
| `predict(rpm, map_kpa, iat_k, ect_k, spark_btdc, lam, …)` | **function** | **the shared plant interface — keyword in, dict out** |
| `map_from_airflow(mdot_air_gps, rpm, iat_k, geo)` | function | inverts air mass to manifold pressure |
| `corrected_flow(mdot_air_gps, t_inlet_k, p_inlet_kpa)` | function | compressor-map normalisation |
| `boost_ceiling_kpa(mdot_air_gps, …)` | function | measured envelope bound |

Physics: Wiebe burn, Woschni heat transfer, Chen-Flynn friction, Douaud-Eyzat
knock integral. `EXH_BACKPRESSURE_RATIO = 1.15` — exhaust backpressure is **not
measured on this vehicle**; state that as an assumption.

### The contract that must not break

```python
out = predict(rpm=2500, map_kpa=90, iat_k=313, ect_k=363,
              spark_btdc=22, lam=1.0)          # -> dict of named outputs
```

**`battery.py` (Phase E) must expose the same contract** — keyword inputs in, a
dict of named outputs out — so the agent code drives either plant unchanged. Do
not rename it.

### The trap that cost three weeks

`Geometry()` defaulted to a generic 2.0 L inline-four; `b58()` was an opt-in
override **no call site ever passed**. Torque was 33 % low across the entire
repo, and the one number everyone watched — the load residual — was computed on
the right engine, so the error survived.

`Geometry()` and `b58()` now return the same object, **and every `run_cycle()`
call passes `geo=GEO` explicitly** even though the default is now correct.

> A default that silently picks a different physical system is not a
> convenience, it is a trap. If a second engine is added, pass it.

---

## `thermal.py` — 3-node lumped-capacitance network

| Node | Capacity | Identified? |
|---|---|---|
| block + coolant | 105 000 J/K | thermostat-regulated |
| oil | 12 000 J/K | **yes** — `ua_block_oil = 800 W/K` from the measured oil-minus-coolant gap |
| turbine housing | 6 000 J/K | τ = 48.0 s measured by step response |

```python
ThermalNetwork.step(dt, mdot_fuel_gps, mdot_exh_gps, egt_k,
                    t_amb, vehicle_mps, fan_duty, coolant_pump_duty=1.0)
```

Thermostat: cracks at **361 K (88 °C)**, fully open 9 K later. It regulates for
88–99 % of every drive recorded, which is why the radiator parameters
(`ua_rad_min`, `ua_rad_ram`, `ua_rad_fan`) are **not identifiable** and were
deliberately left at their nominal values.

---

## `engine_env.py` — the Gymnasium environment

The largest file, and the one that carries the experimental design.

### Four objects

| Object | Role |
|---|---|
| `BaselineECU` | the reference controller, **calibrated against 41.8 min of the real car** |
| `Vehicle` | road load → torque demand and engine speed |
| `SupervisoryTunerEnv` | the Gymnasium env |
| `make_grade_climb(...)` | the standard scenario |

### The parallel-baseline design

This is the single most important structural decision in the repo.

`step()` runs the **baseline ECU and the agent side by side**, each with its own
`ThermalNetwork` (`thermal_base` and `thermal`), on the same drive cycle. Every
reward term is then **baseline-relative and dimensionless**.

Consequences:
- **Zero action reproduces the baseline exactly**, and reward at zero action ≈ 0.
- The agent's bounds must match the baseline's. If the agent is floored at 0
  while the baseline may retard to −10, the neutral action stops being neutral
  and every reward term is silently offset.

### Action space — `Box(-1, 1, shape=(5,))`

The network sees [−1, 1]; the env rescales to `ACT_LO … ACT_HI` and rate-limits
by `SLEW`.

| # | Trim | Range | Slew / step |
|---|---|---|---|
| 0 | spark, °BTDC | −8.0 … +4.0 | 1.5 |
| 1 | lambda | −0.15 … +0.06 | 0.03 |
| 2 | boost, kPa | −40.0 … +15.0 | 10.0 |
| 3 | fan duty | 0.0 … 1.0 | 0.25 |
| 4 | coolant pump duty | 0.3 … 1.0 | 0.2 |

> `neutral_action()` is **not** zeros. Zero in [−1,1] space is the midpoint of
> each range, not the zero trim. Use the helper.

### Observation space — `Box(-10, 10, shape=(23,))`

`OBS_DIM = 23`, all normalised:

1–5 · rpm, manifold pressure, tps, spark, lambda
6–8 · block, oil, turbine temperatures
9–12 · IAT, ambient, barometric, humidity
13–14 · vehicle speed, **current grade**
15–18 · **grade preview at 2 s, 5 s, 15 s, 30 s** (`PREVIEW_S`)
19–20 · torque request, aggression
21–23 · the preference vector `w`

**The preview ablation is these four elements.** With `use_preview=False`,
`_preview()` returns zeros and nothing else in the environment changes. That is
what makes the ablation clean, and `test_reward.py` asserts the observation
actually differs (max |Δobs| = 1.44).

### The inner PI torque loop

`_track_torque()` is a PI controller on manifold pressure, 3 inner iterations,
that makes delivered torque follow demand.

Real ECUs are structured this way: pedal → torque request → airflow target →
throttle and wastegate. **Without it the supervisory agent inherits a torque
error it cannot fix with spark and lambda alone**, and the tracking constraint is
violated from the first step for reasons unrelated to the policy.

`MAP_CEIL_KPA = 250.0` — measured, not guessed: the highest pressure ratio
observed across 43 853 quasi-steady samples is 2.52 against a 99.3 kPa inlet.

### The damage model

```python
d = exp((t_turb - 1123)/45) + 0.4*exp((t_oil - 408)/12) + 40*max(0, ki - 0.85)**2
```

`TURB_PROTECT_K = 1123.0` is the knee of the first term, and **every hand-written
policy in the repo imports it.** Change one, change the other.

### The reward

```python
reward = w[1]*r_fuel + w[2]*r_life + w[0]*r_resp - beta*unc - 0.05*smooth

r_fuel = (base_fuel - agent_fuel) / (base_fuel + eps)
r_life = (d_base - d_agent) / (d_base + 0.05)
r_resp = -(e + TRACK_HINGE * max(0, e - TRACK_TOL)),  e = |dT| / max(T_req, 40)
```

**Torque tracking is a constraint wearing the clothes of a reward term.**

A linear tracking penalty is tradeable at *some* exchange rate, so a weight floor
alone cannot close the hack. The tolerance band plus steep hinge
(`TRACK_TOL = 0.05`, `TRACK_HINGE = 25.0`) is sized so that:

> **No achievable damage saving pays for a sustained torque shortfall beyond
> 10 %.**

Derivation, in the source: the largest damage saving available is `r_life = 1`
weighted by at most `1 − TRACK_W_MIN = 0.55`, while tracking carries at least
`TRACK_W_MIN = 0.45`. Requiring
`0.45·(e + HINGE·(e − 0.05)) > 0.55` at `e = 0.10` gives `HINGE > 22.4`.

The preference vector `w` is resampled every episode so one agent spans the
Pareto front — but `w[0]` (tracking) is floored at 0.45 and only the remaining
0.55 is split by Dirichlet over fuel and life.

> **Run `test_reward.py` after any change to the reward, the plant, OR the
> scenario.** A reward is only safe relative to the dynamics it scores. The hack
> came back once precisely because the fix was verified on a scenario that never
> loaded the engine.

---

## The scripts, by phase

| Script | Phase | What it settles |
|---|---|---|
| `plant.py` (main) | B | spark / lambda / IAT sweeps |
| `validate.py` | B | 11 quantities against published bands |
| `check_map.py` | B | MBT and knock-limited spark surfaces |
| `build_dataset.py` | B | all drives → `data/` |
| `extract_steady.py` | B | one CSV → steady points (**superseded** by build_dataset) |
| `compare_log.py` | B | model vs the car at those points |
| `check_premise.py` | C | **reactive vs predictive. The premise** |
| `test_reward.py` | C | the four reward sanity checks |
| `train.py` | C | SAC training |
| `generality_test.py` | F | the H/τ experiment: H1, H2, H2b |
| `verify_docs.py` | all | recomputes 22 published figures from data |

---

## Cross-cutting: console encoding

Six scripts print `—` or `λ`. A Windows console defaults to cp1252 and cannot
encode either, and the script dies **on its own output, after the real work is
done** — `build_dataset.py` wrote all three CSVs and then crashed on its summary
table, which looks exactly like a failed run.

Each affected script now carries, immediately after its docstring:

```python
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
```

Patched: `build_dataset.py`, `validate.py`, `compare_log.py`,
`extract_steady.py`, `generality_test.py`, `train.py`.

Not needed: `plant.py`, `thermal.py`, `engine_env.py`, `check_premise.py`,
`check_map.py`, `test_reward.py`, `verify_docs.py` — their non-ASCII characters
are confined to comments and docstrings, which are never printed.

---

## Rules that keep this architecture honest

1. **Pass geometry explicitly.** Never rely on a default plant.
2. **`predict()` is the plant interface.** Phase E's `battery.py` implements it.
3. **One protection constant**, `engine_env.TURB_PROTECT_K`, imported everywhere.
4. **Zero action must reproduce the baseline.** Agent bounds mirror baseline
   bounds.
5. After changing `plant.py` or `thermal.py`: re-run `validate.py` **and update
   `validation_table.md` in the same commit**.
6. After changing the reward or the env: re-run `test_reward.py` and **paste the
   output into the commit message**.
