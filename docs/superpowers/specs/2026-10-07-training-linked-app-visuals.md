# Visual requirements — training, decisions and results

User update: 7 October 2026. This adds explicit chart requirements to the training-linked app plan; it does not implement the app in this planning session.

## Reference inspected

[B58 Preview Study](https://claude.ai/artifact/16mUxgXuHMzLppvT9Df4rM), supplied by the user. Inspected its rendered page and chart navigation in the browser, including the policy comparison and the actuator selector switched to Boost. The page identifies its build as 30 September 2026, commit `a3656ac`.

Observed design features: a section navigator, dark bordered chart panels, titles and explanatory captions above plots, a legend near each plot, numerical tables in expandable sections, an episode zoom selector, actuator/channel selectors, and many complementary views of one experiment. The reference includes time series, horizontal policy comparisons with spread marks, paired comparisons, scatter plots, distributions, training curves, thermal comparisons and operating-region maps.

Borrow this density of useful evidence and its interaction patterns. Adapt to the existing app's Arabic/English, theme and mobile system. Do not copy the reference's old numbers, conclusions, manuscript prose, green agreement labels or fixed seed counts into current results. No dependency on Claude hosting, remote embedded pages or scraping that page at runtime.

## Visual organisation

Use five navigable groups: **Overview**, **Training**, **Agent decisions**, **Evaluation**, **Simulator versus car**. These may be sections within the existing routes; they do not require five new pages. Display a small overview and the selected group's figures, not 25 canvases rendering continuously above one another.

Each analytical panel has this fixed structure:

1. A plain question/title and one line explaining what the plot shows.
2. The plot, axis units and a consistent legend; source, experiment and revision remain identifiable.
3. Relevant controls: policy/seed/channel selection, time window, zoom reset, or total/thermal damage.
4. A tooltip and a keyboard/touch-accessible numbers table drawn from the same data.
5. A compact source/availability statement and the caveat that changes the interpretation.

Desktop: use a wide primary plot and two-column supporting plots where labels remain readable. Phone: one chart per row, readable labels outside SVG where needed, expandable details, large touch controls and accessible plot controls. Keep a chart's controls visible near it rather than off-screen above a long list. Retain blue/amber for the two agent arms from the existing app; encode measured/modelled and unknown values with line/marker styles as well as colour. Do not adopt the reference's palette if it collides with current roles.

## Required reference coverage: 25 analytical panels

The IDs below map the observed reference to implementable work. They are coverage requirements, not a claim that every file is current or complete. One panel may contain several plots. G03 is a comparison table with optional bars, not an obligation to turn every table into a chart.

Source paths are relative to the repository. The authoritative readers already documented in the old results design remain the starting point. Availability must be checked per experiment at runtime.

| ID / reference block | Required view and interaction | Data source / gate | Delivery |
|---|---|---|---|
| G01 `f-trace` | Component temperature over an episode; whole-window / peak-region zoom, threshold and climb interval, individual policy visibility | `results/traces_130kmh.json`, using the `make_page.phase_d()` read contract; mark historical plant/scenario | C1 / R2 |
| G02 `f-damage` | Accumulated damage versus time, synchronised to G01, endpoint comparison | The same trace file; use recorded cumulative series; missing thermal split stays unavailable | C1 / R2 |
| G03 `f-steps` | Before/after model-change comparison, with each step and its source preserved | `results/calibration_comparison.json`, `premise_steps`; historical record, not a fresh recomputation | C1 / R2 |
| G04 `f-htau` | H/τ versus preview benefit with both comparator definitions visible | `results/generality.json`; preserve validity restrictions tied to that file's numerical method and plant | C1 / R2 |
| G05 `f-sweep` | Speed × grade heatmap, cell value on tap/focus, threshold and chosen scenario identified | `results/sweep_speed_grade.json`; no invented interpolation between tested cells | C1 / R2 |
| G06 `f-roads` | Small road-profile plots plus the sampled roads' thermal peaks; select a road to highlight its summary | `results/training_roads.json`; sampled example roads are not the exact history of a training run | C1 / R2 |
| G07 `f-eval` | All evaluated policies, median and recorded spread, worst episode visible on demand | Set `index.json` / `eval_summary.json`; preserve the original R1a per-experiment figures too | B1 |
| G08 `f-abl` | Connect each sighted/blind seed pair; switch between total and thermal damage when available | Set summaries and existing evaluation text readers; never pool seeds across experiments | B1 |
| G09 `f-km` | Matched original / spark-capped outcome, per agent or arm summary, with the hand-written comparator | Set `knock_margin.json` after the old spec's consistency checks; diagnostic, not a retrained policy | B1 |
| G10 `f-act` | Five-way actuator selector; distribution/median of applied spark, lambda, boost, fan and pump, with baseline | `eval_summary.json.actions`; use recorded units/ranges; unavailable actuator statistics stay missing | B1 |
| G11 `f-ep1` | Selected episode time series with channel selector and a cursor shared with replay; episode/policy selectable | Available `eval_record.npz`, or a validated local episode extract, or an explicitly computed compatible replay; no assumed extract exists | B2 |
| G12 `f-trade` | Damage–fuel scatter; paired seeds highlighted together; selectable agents and exact-value table | Same-set evaluation summaries; axes identify absolute values or percent cuts without mixing them | B1 |
| G13 `f-curves` | Per-run learning curves / small multiples, selectable seed and displayed episode/step axis | Each run/set's `curve.csv`; road/weights change, so rising returns alone are not a convergence verdict | B1 |
| G14 `f-load` | Measured versus modelled load points with identity line and explicit comparison limits | `results/model_vs_data.json`, `load`, existing `make_page.model_vs_car()` contract | C1 / R2 |
| G15 `f-boost` | Pressure distribution comparison, with model/measurement sources and gauge/absolute units explicit | `results/model_vs_data.json`, `boost`; same published selection gates | C1 / R2 |
| G16 `f-enrich` | Mixture versus RPM/dwell cells; compare logged and simulated values, counts on demand | `results/model_vs_data.json`, `enrichment`; timestamp-based dwell; no silent reuse of retired row-count data | C1 / R2 |
| G17 `f-spark` | Spark comparison/residuals and documented pre/post calibration state | `results/model_vs_data.json` through the existing spark reader; reference advance/retard explicitly | C1 / R2 |
| G18 `f-th10` | Long-drive oil/coolant traces, logged and simulated, common time cursor and zoom | Published thermal comparisons read by `make_page.model_vs_car()` and `calibration()`; distinguish fit data from held-out data | C1 / R2 |
| G19 `f-thfit` | Error by drive, separating original parameters, fitted drive and held-out drive | `results/calibration_comparison.json`, `thermal.per_drive`; no averaging away individual drives | C1 / R2 |
| G20 `f-th74` | Thermal traces under hard pulls and the documented structure comparison | Published `model_vs_data.json` / `calibration_comparison.json` traces; do not mix different calibration generations | C1 / R2 |
| G21 `f-knock` | Knock indicator versus recorded retard, with sampling density and timing limitations | Published knock comparison in `model_vs_data.json`; weak sampling cannot support an agreement/refutation claim | C1 / R2 |
| G22 `f-gear` | Observed ratio distribution with the relevant published gear-ratio reference lines | Published gearbox comparison in `model_vs_data.json`; preserve gear-channel saturation caveat | C1 / R2 |
| G23 `f-env` | Airflow/pressure operating envelope plus low-RPM boost comparison where published | `model_vs_data.json` and `calibration_comparison.json` boost data; operating envelope is not a compressor map | C1 / R2 |
| G24 `f-duty` | Logged operating-region coverage, with the simulated scenario visibly marked | Published operating-region data in `model_vs_data.json`; no synthetic measured points | C1 / R2 |
| G25 `f-lit` | Validation values versus their stated bands, source and validation status per row | Existing `make_page.calibration()` rows / published validation records, reconciled with the latest validation plan | C1 / R2 |

The old results spec deliberately excluded its one-episode chart. The user's new graphics request adds **G11 as a data-gated viewer**. It does not authorize copying the old “5–6 times” claim, pretending missing episode files exist, or mixing a median across agents with a single selected agent. Label any aggregate precisely.

## Extra views specific to the requested app

In addition to reference coverage, B2 must make the decision chain visible:

- A five-lane command/applied-action timeline, each lane with its own physical units and optional constraint/held indication. Training records without `applied` show command only.
- Aligned panels for recorded observations/preview, reward and its fuel/life/response components, torque requested/delivered, and available thermal channels. Missing channels are listed and not synthesised.
- An event strip for events actually recorded or detected by an explicit documented rule. It is navigational; it does not claim the network's internal reason for acting.

Clicking a time-series point or using the shared keyboard cursor selects the same sample in these plots and the 3D agent view. Changing channel, theme or language keeps that sample. Synchronise only plots with the same run generation and valid time/episode alignment. A training-episode curve has an episode/step axis, not an interchangeable evaluation-time axis.

## Interaction and rendering requirements

- Every plot supports hover, tap and keyboard access to exact values, plus the expandable table; legends permit clear series selection. Preserve an honest axis scale and a visible restore-all action.
- Time-series zoom must name its domain and provide reset. Clicking/dragging never interpolates scientific readings between samples. Use one selection store per aligned dataset.
- Pair selection links the paired plot, damage–fuel scatter and policy table for the same experiment. Outlier and worst-episode inspection must remain possible.
- Raw training curves are the default. If smoothing is added, it is optional, labelled with its method/window, and never replaces access to raw values.
- Reference/threshold lines name their source and whether they are a project choice or recorded limit. A threshold must match the plotted result's generation; do not apply current action limits to an older run silently.
- Downsampling, when needed, preserves extremes and missing-data gaps; the numbers table/selected point resolves to the original sample. Axis units and scientific values do not change with viewport size.
- Lazily mount inactive/off-screen plots, share resize observers, and dispose old listeners on re-render. Refresh only charts whose source revisions changed; keep chosen series/zoom/selection where still valid.
- Loading, writing, unavailable, historical, incompatible and last-valid-snapshot states are visible. Do not fill an absent chart with illustrative data unless it is in an explicitly labelled fixture-only test session.
- Export is not required for this batch. Start with accurate on-screen figures and exact-value tables; avoid adding a separate report-generation subsystem.

## Verification and completion

Maintain a coverage table with one row for each G01–G25 panel: source, reader, route, implementation task, rendered state and verification evidence. For unavailable real data, record the specific missing artifact plus a tested fixture case; do not claim the real-data figure was verified.

Verify the shared cursor, pair selection, zoom reset, channel selector and tables at 1440×900 and 390×844, in both languages/themes. A meaningful value must be reachable without hover. Confirm no graph borrows another experiment's source, no graphic implies current validity for an older file, and idle refresh does not recreate every chart.

A1–A3 remain the first implementation session. B1 covers result graphics, B2 the decision timelines, B3 the mechanical view, and C1 the remaining R2/reference figures. The graphic requirements apply across these milestones; they are not satisfied by one generic chart or static screenshots of the reference.
