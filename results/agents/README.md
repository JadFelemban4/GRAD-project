# Trained agents — what they are, what they did

Every agent this project has trained, documented where anyone can read it
(`runs/`, where the models are saved, is gitignored). Written by
`python record_agents.py`; each set's own `README.md` is generated and holds
every table. Do not edit the files under a set by hand — re-run the script.

| set | what | status |
|---|---|---|
| [`terrain_dt1/`](terrain_dt1/README.md) | the retrain of 29 September 2026: seeds 0–9, sighted and blinded, 50 000 steps each, a new road every episode, 130 km/h, dt 1.0, the plant derived from the logs. [`KNOCK_MARGIN.md`](terrain_dt1/KNOCK_MARGIN.md): the same agents with spark advance forbidden | **Phase D's first result** |
| [`sep19_110kmh/`](sep19_110kmh/README.md) | the ten agents of 19 September: seeds 0–4, trained at 110 km/h on one road at dt 0.2, on the plant before 28 September | a record, not a result |

## What each agent folder holds

| file | what it is |
|---|---|
| `config.json` | how it was trained: every SAC setting, versions, commit, the plant's data fingerprint, wall time. For the 19 September set it is read back out of the saved model, and says so |
| `curve.csv` | one row per training episode: return, length, road |
| `train_record.npz` | **every training step**: `step`, `episode`, `action` (the network's output in [-1, 1], exactly what went to the environment), `obs` (what the action was chosen from), `reward` and its terms `r_fuel`, `r_life`, `r_resp`, and the engine (`t_turb`, `t_oil`, `t_block`, `torque`, `torque_req`, `mdot_fuel`, `ki`, `spark`, `lam`, `egt_c`). Only the 29 September set has it: training actions were never recorded before |
| `eval_record.npz` | **every step of the twenty frozen episodes**, arrays `[episode, step, ...]`: `action` (commanded), `applied` (what the actuators did after the slew limit, in physical units: spark trim deg, lambda trim, boost trim kPa, fan duty, pump duty), `obs`, `reward` and its terms, `rpm`, `map_kpa`, `grade`, `spark`, `lam`, `torque`, `torque_req`, `ki`, `egt_c`, `mdot_fuel`, `t_turb`, `t_oil`, `t_block`, the baseline's `t_turb_base` beside it, `damage_rate`, and `episode_seed`, `weights` |
| `eval_summary.json` | the twenty episodes scored exactly as `evaluate.py` scores them, the medians, the cut against the baseline, and what each actuator did on the flat and on the climb |
| `policy.npz` | the actor network's weights — the part that acts |

The hand-written policies (`baseline_ECU`, `reactive`, `current-grade`,
`predictive_hand`) are recorded in every set the same way, for comparison.

**The two `*_record.npz` kinds are NOT in git** (the team's decision, 29
September: 85 MB of binaries). They stay on the machine that trained the agents,
beside the models themselves (`runs/`, also gitignored): only there can
`python record_agents.py <set>` regenerate `eval_record.npz`, and
`train_record.npz` cannot be regenerated at all. Everything the page and the
READMEs need from them is kept in `eval_summary.json`, which is committed.

## Reading a record

```python
import numpy as np
r = np.load("results/agents/terrain_dt1/sighted_seed0/eval_record.npz")
r["applied"].shape          # (20 episodes, 719 steps, 5 actuators): 720 s at dt 1.0
r["t_turb"][0] - 273.15     # episode 1's turbine temperature, C
t = np.load("results/agents/terrain_dt1/sighted_seed0/train_record.npz")
t["action"].shape           # (50000, 5): every action it took while it learned
```
