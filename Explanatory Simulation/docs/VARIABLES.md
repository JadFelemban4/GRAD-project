# Variables and controls

Generated from `backend.catalog.metadata()` on 2026-10-04. Limits and source lines are read from the current project code where available.

## Supervisor actions

The policy emits five normalized values in `[-1, 1]`. The bridge converts them to physical values, then `engine_env.py` applies per-second slew limits and clips to the physical bounds. Fan and pump values are absolute duties; spark, lambda and MAP are additive trims.

| Action index | ID | Meaning | Physical range | Maximum slew | Normalized command | Sources |
|---:|---|---|---|---|---|---|
| 0 | `spark_trim` | Degrees added to or removed from baseline spark timing. | -8.0 to 4.0 deg BTDC | 1.5 deg/s | [-1.0, 1.0] | [`engine_env.py:644`](../../engine_env.py#L644), [`engine_env.py:645`](../../engine_env.py#L645), [`engine_env.py:864`](../../engine_env.py#L864) |
| 1 | `lambda_trim` | A trim to the baseline air-fuel equivalence ratio; lambda 1 is stoichiometric. | -0.15 to 0.06 lambda | 0.03 lambda/s | [-1.0, 1.0] | [`engine_env.py:644`](../../engine_env.py#L644), [`engine_env.py:645`](../../engine_env.py#L645), [`engine_env.py:864`](../../engine_env.py#L864) |
| 2 | `boost_trim` | A pressure offset requested by the supervisor; the torque loop and compressor envelope still constrain manifold pressure. | -40.0 to 15.0 kPa | 10.0 kPa/s | [-1.0, 1.0] | [`engine_env.py:644`](../../engine_env.py#L644), [`engine_env.py:645`](../../engine_env.py#L645), [`engine_env.py:864`](../../engine_env.py#L864) |
| 3 | `fan_duty` | Absolute fan duty from zero to one, not a trim to the ECU fan command. | 0.0 to 1.0 fraction | 0.25 fraction/s | [-1.0, 1.0] | [`engine_env.py:644`](../../engine_env.py#L644), [`engine_env.py:645`](../../engine_env.py#L645), [`engine_env.py:864`](../../engine_env.py#L864) |
| 4 | `pump_duty` | Absolute pump duty from its 0.3 lower bound to full duty, not a trim. | 0.3 to 1.0 fraction | 0.2 fraction/s | [-1.0, 1.0] | [`engine_env.py:644`](../../engine_env.py#L644), [`engine_env.py:645`](../../engine_env.py#L645), [`engine_env.py:864`](../../engine_env.py#L864) |

## Policy observations

The actor reads the `obs_in` vector that produced its current action. `obs` is the next observation. Entries below are in the exact 23-slot order. The environment clips the completed observation vector to `[-10, 10]`; physical values are transformed using the listed scale before clipping. Unless noted, observations are model values or generated scenario fields, not vehicle sensor readings.

| Slot | ID | Meaning | Unit | Normalization / scale | Limit or interpretation | Source |
|---:|---|---|---|---|---|---|
| 0 | `rpm` | Crankshaft revolutions per minute, centred around 3000 rpm. | rpm | rpm / 3000 - 1 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:790`](../../engine_env.py#L790) |
| 1 | `map` | Absolute pressure in the intake manifold after the throttle. | kPa abs | MAP / 120 - 1 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:791`](../../engine_env.py#L791) |
| 2 | `tps` | A model proxy based on achieved manifold pressure, not a measured throttle-position channel. | fraction | already in [0, 1] | Model proxy; not a measured TPS channel. | [`engine_env.py:792`](../../engine_env.py#L792) |
| 3 | `spark` | Actual model spark timing after the supervisory trim is added to the baseline schedule and clipped to ECU limits. | deg BTDC | spark / 20 - 1 | Actual timing after baseline plus supervisor trim and ECU clipping. | [`engine_env.py:793`](../../engine_env.py#L793) |
| 4 | `lam` | Actual modelled air-fuel equivalence ratio relative to stoichiometric mixture. | lambda | (lambda - 1) * 8 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:794`](../../engine_env.py#L794) |
| 5 | `t_block` | Temperature of the lumped block/coolant node. | K | (T - 363) / 25 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:795`](../../engine_env.py#L795) |
| 6 | `t_oil` | Temperature of the lumped sump and oil-gallery node. | K | (T - 373) / 30 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:796`](../../engine_env.py#L796) |
| 7 | `t_turb` | Modelled temperature of the turbine housing and exhaust manifold; the car has no sensor for it. | K | (T - 873) / 200 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:797`](../../engine_env.py#L797) |
| 8 | `charge_temp` | Modelled intake charge temperature after compression and charge cooling. | K | (T - 303) / 25 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:798`](../../engine_env.py#L798) |
| 9 | `ambient_temp` | Scenario air temperature used by vehicle, engine and thermal calculations. | K | (T - 293) / 15 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:799`](../../engine_env.py#L799) |
| 10 | `barometric_pressure` | Ambient barometric pressure; it changes air density and corrected compressor flow. | kPa abs | (pressure - 101.3) / 8 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:800`](../../engine_env.py#L800) |
| 11 | `humidity` | Specific humidity supplied by the generated road scenario; this is not relative humidity. | kg water/kg dry air | humidity * 40 - 0.5 | Fixed 0.012 kg/kg scenario field; actor observes it, but current plant equations do not use it. | [`engine_env.py:801`](../../engine_env.py#L801) |
| 12 | `speed` | Vehicle road speed, distinct from engine RPM. | m/s | speed / 25 - 1 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:802`](../../engine_env.py#L802) |
| 13 | `grade` | The slope under the car now; it remains visible to the blinded policy. | fraction | grade * 12 | Current grade remains visible with preview disabled. | [`engine_env.py:803`](../../engine_env.py#L803) |
| 14 | `preview_2s` | Road grade sampled two seconds ahead. | fraction | future grade * 12 | Zero when future-grade preview is disabled. | [`engine_env.py:805`](../../engine_env.py#L805) |
| 15 | `preview_5s` | Road grade sampled five seconds ahead. | fraction | future grade * 12 | Zero when future-grade preview is disabled. | [`engine_env.py:805`](../../engine_env.py#L805) |
| 16 | `preview_15s` | Road grade sampled fifteen seconds ahead. | fraction | future grade * 12 | Zero when future-grade preview is disabled. | [`engine_env.py:805`](../../engine_env.py#L805) |
| 17 | `preview_30s` | Road grade sampled thirty seconds ahead. | fraction | future grade * 12 | Zero when future-grade preview is disabled. | [`engine_env.py:805`](../../engine_env.py#L805) |
| 18 | `torque_req` | The torque request inferred from road load and the vehicle model. | Nm | torque request / 200 - 1 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:807`](../../engine_env.py#L807) |
| 19 | `aggression` | A normalized proxy for how quickly vehicle speed is changing. | fraction | clipped \|acceleration\| / 2.5 | Final normalized vector clipped to [-10, 10]. | [`engine_env.py:808`](../../engine_env.py#L808) |
| 20 | `weight_tracking` | Episode weight on requested-torque tracking, drawn uniformly from 0.45 to 0.70. | weight | Uniform episode draw in [0.45, 0.70] | Training reset draw: 0.45–0.70; locked scored bridge pins Episode 1 at 0.690154. | [`engine_env.py:809`](../../engine_env.py#L809) |
| 21 | `weight_fuel` | Episode preference share for fuel saving after the tracking floor is set. | weight | First of two Dirichlet(1,1) shares of remaining weight | One Dirichlet(1,1) share of the remaining preference; locked Episode 1 pins 0.012829. | [`engine_env.py:809`](../../engine_env.py#L809) |
| 22 | `weight_life` | Episode preference share for modeled damage reduction after the tracking floor is set. | weight | Second of two Dirichlet(1,1) shares of remaining weight | Other Dirichlet(1,1) share of the remaining preference; locked Episode 1 pins 0.297017. | [`engine_env.py:809`](../../engine_env.py#L809) |

## Other source-derived bounds

- Preview horizons: `[2.0, 5.0, 15.0, 30.0]` seconds ([`engine_env.py:648`](../../engine_env.py#L648)).
- Turbine damage knee: `1123.0` K ([`engine_env.py:621`](../../engine_env.py#L621)); oil knee: `408.0` K ([`engine_env.py:622`](../../engine_env.py#L622)). These are proxy-model knees, not certified safe limits.
- Torque tracking tolerance: `0.05` ([`engine_env.py:601`](../../engine_env.py#L601)).
- The completed observation vector is clipped to `[-10, 10]` ([`engine_env.py:811`](../../engine_env.py#L811)).
- Temperature observations are ordered block/coolant (slot 5), oil (slot 6), turbine housing (slot 7). The frame uses Kelvin for thermal fields; the inspector displays Celsius and Kelvin.
- Action and observation meanings, all concept units/ranges and current source links are also listed in [SOURCE_MAP.md](SOURCE_MAP.md).
