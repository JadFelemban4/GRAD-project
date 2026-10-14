# A superseded design, kept as the record

Two conditions of the first design of `conditions_test.py` (7 October 2026):
the twenty agents and the four hand-written policies on the LOCKED climb, 12 %
at a constant 130 km/h, in other air. 25 C (`part1_25C.json`) and 35 C
(`part2_35C.json`) finished; the run was then stopped, because on a 12 % hill
cooler air never reaches the 850 C trigger, so there was nothing to protect
and no protection to see.

Ghassan replaced the design the same day: each condition on its own hill, steep
enough that the baseline ECU reaches the locked climb's severity, with a speed
target that changes during the run. That is `results/conditions_test.json` and
section 11 of `results/VALIDATION_PLAN.md`.

What these two files still show, and the reason they are kept: at 25 C, where
the baseline ECU never reached the trigger, blinded seed 6 on frozen episodes
13 and 17 (the two with the least weight on component life) ran its turbine
housing about 60 K hotter than the baseline did. It is the agent already known
to fail on the frozen episodes that weight life least
(`results/agents/terrain_dt1/README.md`). *(Corrected 8 October: this said it
trades component life for fuel. The per-step records show it retarding spark on
those episodes and burning more fuel than the baseline too.)*

Each file is a list of episode rows in `conditions_test.py`'s first format:
policy, frozen episode, ambient (K), pressure (kPa), and the episode's scores.
