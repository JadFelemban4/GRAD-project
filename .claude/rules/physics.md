---
paths:
  - "plant.py"
  - "thermal.py"
  - "engine_env.py"
  - "derive_params.py"
  - "derived.py"
  - "engines.py"
  - "engine_specs/**"
  - "data/**"
---

# Physics: the plant, the thermal network, the derived constants

Loaded when one of the plant's files is read or edited. Procedures and pointers
only; the rules are in CLAUDE.md.

After any change to these files, in the same commit:

1. `python check_premise.py`, `python validate.py`, `python test_reward.py` and
   `python check_roads.py`. Update `validation_table.md` from `validate.py`, and
   paste `test_reward.py`'s output into the commit message (CLAUDE.md,
   conventions).
2. Record the new `plant_sha` (on the lock's Python, decision 32) and `derived_sha`. A change to
   either is a new plant, and every agent trained on the old one is refused.
3. Run every app suite that reads the plant (`.claude/rules/app.md`), and move
   the learning lab's pins in `Explanatory Simulation/tests/test_catalog.py` to
   the new plant, with a comment naming the plant they belong to.
4. `python verify_docs.py`: a figure the documents quote may have moved.

Before you change one, read mistakes 1, 6, 17, 20, 23 and 25 in
`docs/MISTAKES.md`. A new drive changes the plant too (`.claude/rules/data.md`).
