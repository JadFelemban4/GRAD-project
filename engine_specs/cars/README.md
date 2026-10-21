# `engine_specs/cars/` — the four cars of the H/τ test, as their sources print them

Decision 24 (`results/VALIDATION_DECISIONS.md`, section F) puts each engine in its own
car. One file per car holds what the manufacturer, Argonne, NHTSA and the US EPA
**publish** about it: gear ratios, final drive, tyres, curb weight, and EPA's
certification road load at EPA's test weight. **Nothing in these files is derived**:
not the rolling radius, not a drag area, not a mass in kilograms. The code that
builds a `Car` derives those, in the open, from what is here (below). A value no
source prints is listed under `[not_typed]` with the reason, never guessed.

| file | car | engine (`engine_id`) | gearbox | gaps |
|---|---|---|---|---|
| `a90_supra_2020.toml` | Toyota GR Supra 3.0, ZF 8HP51 | `b58` | 8-speed automatic | tyre fitment of our car; the plant keeps its own road load (decision 31, recommended, unanswered) |
| `cx9_2016_25t.toml` | 2016 Mazda CX-9 2.5 L turbo, FWD (the D3 car) | `mazda_25t` | 6-speed automatic | curb weight only for model year 2019 |
| `accord_2018_15t.toml` | 2018 Honda Accord LX 1.5 L turbo (the D3 car) | `honda_l15b7` | CVT | the engine map is the 2016 Civic's, not this car's engine |
| `f150_2015_27tt.toml` | 2015 Ford F-150 2.7 L EcoBoost 4x2 | `ford_27tt` | 6-speed automatic (6R80) | no tyre size, no curb weight, no driving data |

Read by nothing yet: build step 1 of the four-engine plants (20 October 2026) is
the data. `python test_epa_map.py` (class `CarSpecs`) checks every file's form,
checks each EPA row against the Test Car List file it cites, and checks the
Supra's `[repo_current]` against the plant `engines.get("b58")` builds.

**Not the plant's constants.** `engine_specs/<car>.toml` one folder up (for example
`a90_supra.toml`, read by `engines.py`, written in the same build step) holds what
the plant runs, each value labelled. The files here hold what the sources print. A
published value reaches the plant only through code that derives from it, or a
decision that adopts it — and for the Supra, decision 31 (recommended, both
columns still open) would adopt none of them.

## The fields

Every file starts with `schema`, `car_id`, `engine_id` and a `description`.

**A value table** — one per published quantity (`[gear_ratios]`, `[final_drive]`,
`[tyre_size]`, `[curb_weight]`, `[cvt_ratio_range]` …):

| key | meaning |
|---|---|
| `value` | the number, list or text exactly as the source prints it |
| `unit` | the source's unit: `"1"` for a ratio, `lb`, `kg` |
| `status` | `PUBLISHED`: printed by the source named in `source` |
| `source` | a key of `[sources]` |
| `note` | page or table, conflicts between sources, what the value is not |
| `model_year` | only where the source's model year is not the car's (the CX-9's curb weight) |

**`[epa_test_car]`** — the EPA Test Car List row of the tested configuration, with
`status`, `source` and `file_rows` (the spreadsheet rows of that file, header =
row 1; one row per test procedure, same coefficients) for the whole table, and the
unit in every key:

| key | EPA's column |
|---|---|
| `equivalent_test_weight_lb` | `Equivalent Test Weight (lbs.)`: a test-weight class, not a curb weight |
| `target_coef_a_lbf`, `target_coef_b_lbf_per_mph`, `target_coef_c_lbf_per_mph2` | `Target Coef A (lbf)`, `Target Coef B (lbf/mph)`, `Target Coef C (lbf/mph**2)` |
| `axle_ratio` | `Axle Ratio` |
| `n_over_v_rpm_per_mph` | `N/V Ratio`: engine rpm per mph in top gear |
| `test_vehicle_id`, `engine_code`, `represented_model`, `model_year`, `rated_hp` | the row's identity |

`[[epa_test_car_other_rows]]` holds other published rows of the same car in the
same form — a second coefficient set, another body, another model year — so a later
choice between them is visible, not silent.

**`[repo_current]`** (the Supra only): the values the plant runs today
(`engine_specs/a90_supra.toml` `[car]`, what `engines.get("b58").car` holds; until
build step 1 they were `engine_env.py`'s class `Vehicle`), status `REPO`, a copy
that `test_epa_map.py` checks against the plant. They are not published
(`REFERENCES.md` section 4b) and they differ from EPA's; decision 31 (recommended,
unanswered) would keep them for the four-engine test.

**`[not_typed]`**: quantity → why it is not here, and where it comes from instead.

**`[sources.<KEY>]`**: `url`, `what` (title, page, table), `opened` (date). The
repository's own values cite `path` instead of `url`.

There is no `DERIVED` and no `ASSUMED` status here. A derived value is computed by
code from these inputs, and an assumed one is labelled where the code uses it (a
fitted number typed into a data file freezes the fit: the project's rule, and
review 0's item 17 on the four-engine design).

## Deriving what the model needs (in code, not here)

- **Units.** 1 lb = 0.45359237 kg, 1 lbf = 4.4482216152605 N and 1 mph = 0.44704 m/s,
  all exact by definition.
- **Road load.** EPA's targets give F = A + B·v + C·v² (lbf, mph) for a level road at
  the test weight. The vehicles strand of 20 October 2026 read them as valid for
  15–115 km/h at 20 °C and 98.21 kPa (40 CFR 1066.305(a)), with the transmission in
  neutral, so they already hold tyre, bearing and driveline drag; 130 km/h is an
  extrapolation (mistake 6). With B ≠ 0 (the Accord's is negative) a split into a
  rolling coefficient and a drag area depends on the speed band fitted: say the band.
- **Mass.** `equivalent_test_weight_lb` is EPA's test-weight class for the loaded
  vehicle, curb plus 300 lb (40 CFR 86.1803-01 and 1066.805, per the same strand);
  the plant's B58 runs a kerb mass instead (`[repo_current]`).
- **Rolling radius.** From EPA's N/V of the tested car, with no converter slip:
  r = 26.8224 m/min × top gear × axle ratio / (2π × N/V), where 26.8224 m/min is
  1 mph. The vehicles strand measured the CX-9's on the D3 data and found it 1.6 %
  smaller than N/V gives (UNVERIFIED here: the D3 data are outside the repository
  and no committed script prints it); for the Accord, a CVT's N/V depends on the
  ratio it was in. Say which one the code uses.

## The sources' own conditions

Cite EPA's packages as `logs/epa/README.md` gives EPA's own citations, and a Test
Car List by its URL in `[sources]`. Argonne's D3 data, behind every
`D3CX9` and `D3ACC` value in `cx9_2016_25t.toml` and `accord_2018_15t.toml`, may
only be used with Argonne's attribution, as `fetch_engine_data.py` quotes it from
https://www.anl.gov/taps/downloadable-dynamometer-database (opened 20 October 2026):
*"This data is from the Downloadable Dynamometer Database and was generated at the
Advanced Mobility Technology Laboratory (AMTL) at Argonne National Laboratory under
the funding and guidance of the U.S. Department of Energy (DOE)"*. `REFERENCES.md`
section 8 lists every source of these files.

Added 20 October 2026, build step 1 of decision 24.
