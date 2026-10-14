---
paths:
  - "app/**"
  - "Explanatory Simulation/**"
---

# The app and the learning lab

Loaded when a file under `app/` or `Explanatory Simulation/` is read or edited.
The app never transmits to the vehicle and never writes raw car data to disk
(CLAUDE.md, the hard constraint).

After a change under `app/`, from the repository root, on Python 3.12:

```
python -m app.test_replay            # add --full before a release
python -m app.test_simulation
python -m app.test_results
python -m app.test_agents
cd app && node --test "static/sim/*.test.mjs" && cd ..
```

Paste `app.test_replay`'s output into the commit message. After a change to the
plant or the roads, run all of them (CLAUDE.md, conventions; mistake 25).

The learning lab, inside `Explanatory Simulation/`: `npm ci`, `npm run build`,
`python -m unittest discover -s tests -v`; then `python launch.py --no-browser`
in one window and `python launch.py --check` in another. `tests/test_catalog.py`
pins the plant's figures: move them when the plant moves
(`.claude/rules/physics.md`).
