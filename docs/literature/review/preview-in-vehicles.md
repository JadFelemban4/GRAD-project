# Preview in vehicles and powertrain thermal management

First version, 17 November 2026: all three paragraphs approved by Jad.

Jad's section of the literature review, written by stage IV of Dr. Hammam's method
(one section per theme; `docs/literature/READING_METHOD.md`). It also feeds this theme's
part of the SP1 proposal's section 2.2. The words are Jad's: he says each paragraph in
Arabic, Claude writes it in plain English, and Jad reviews it before it counts.

Papers: B37, B40, B19, B18, B06, B31, each read in full and annotated by Jad in the Notion
tracker. Citations are tracker IDs for now; `docs/literature/references.bib` turns them
into IEEE numbers.

## Paragraph 1: the strength of the evidence (approved by Jad, 17 November 2026)

The six works reviewed here come from industry and research, and the evidence behind them
differs in strength. Three are patents [B37], [B40], [B19]: they describe a method but
report no test of it. Two were tested in simulation only. [B18] ran a single
proof-of-concept simulation and says its model was checked against a real vehicle, but
shows no data. [B06] simulated a car following recorded test drives and assumed a perfect
prediction of the car ahead. [B31] went one step further: its controller also ran on an
automotive computer, but the engine was still a model on a second machine. None of the six
tested its method on a real engine. The same holds for this project, which will also be
tested in simulation.

## Paragraph 2: how far each work looks ahead (approved by Jad, 17 November 2026)

The six works differ most in how far they look ahead, and in what sets that length.
[B37] uses a fixed distance of 0.5 to 2 km, the same for every part. [B18] looks 4 minutes
ahead but uses only about 1.5 minutes of it, because starting earlier would over-cool the
engine; it states this without a test. In [B31], the turbocharger's lag of about 1.4 s set
the shortest useful preview, but the computing time chose 2 s, and no other length was
tried. [B06] tried several lengths and found that 20 s gave the same fuel saving as full
knowledge of the car ahead, with a perfect prediction assumed in every run. [B40] has no
fixed length: it starts heating the battery at once if the trip is shorter than the
heating time, and waits otherwise. [B19] does not look ahead at all: its tables react to
the driver's demand at that moment, using the same kind of levers as this project, less
air and more fuel.

## Paragraph 3: the missing piece (approved by Jad, 17 November 2026)

This project needs four elements together: road preview used to protect a component from
heat, more than one preview length, a preview length chosen from how fast the protected
component heats up, and a learning agent. Each of the six works reviewed in this section
has at most part of this. [B37] and [B18] use preview to protect a component from heat,
but each with one fixed preview length. [B06] tests several preview lengths, but it
previews the car ahead to save fuel, with no component temperature. [B40] compares the
time to reach a charger with the battery's heating time, which is close to the third
element, but as a patent it reports no test. None of the six uses a learning agent. This
project will combine the four elements in one study.

## Rows for the proposal's comparison table, section 2.3 (draft, for Jad's review)

The outline's suggested columns, with "dataset" read as the system or data each work used.
Every entry comes from Jad's notes in the tracker.

| Ref | Dataset or system | Method | Metric | Reported result | Main limitation |
|---|---|---|---|---|---|
| [B37] | Truck cooling system (radiator, thermostat) | Route preview of 0.5-2 km and early cooling (patent) | None | No test of the method | One fixed preview distance for all parts |
| [B40] | Electric-vehicle battery before fast charging | Time to reach the charger compared with heating time (patent) | None | No test | The rule is never tested |
| [B19] | Engine component protection | Two lookup tables; less air, more fuel, water injection (patent) | None | No test; says table values can come from bench tests | No road preview; temperature computed, not measured |
| [B18] | Engine coolant and cylinder-wall temperature, GT-SUITE simulation | MPC with 4 min of GPS preview; coolant valve and fan | Fan and alternator energy | Savings below 5%; fuel not measured | One run; one fixed preview; knock left out |
| [B06] | Car following recorded EPA drives, fuel model of a 2013 Ford Escape | Braking and acceleration planned from a preview of the car ahead | Fuel use | 5-12% with 1.5 s; 20 s matched full knowledge (13-17%) | Perfect prediction assumed; horizon sweep on one drive |
| [B31] | Diesel air path (turbocharger, two EGR valves), engine model; desktop, then an automotive computer | Two-level economic MPC; the upper level looks 2 s ahead | NOx, soot, fuel, torque tracking | Better than a no-preview MPC (also different in structure) and a production controller; the gain vanished at about 13% preview error | One preview length, chosen for computation; no real engine |
