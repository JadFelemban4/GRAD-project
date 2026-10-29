# Interactive figures

Each folder here builds one interactive figure for the lab: a page that draws a
real object whose working is the idea, with every number taken from the
project's own code. They are drawn with the Anatomy kit (`kit/`, MIT, see
`kit/README.md`), the same kit the `anatomy` skill uses.

| figure | lesson | page |
|---|---|---|
| `housing-lag/` | `housing_lag`: the turbine housing lags the gas (τ) | `public/figures/housing-lag.html` |

## How one is made

1. **The numbers come from the parent repo, never typed.** `export_params.py`
   calls `plant.py` and `thermal.py` and writes `params.json`. A Python test
   (`tests/test_housing_figure.py`) recomputes it and fails when the plant moves.
2. **The page runs the same model.** `src/model/housing-lag.mjs` repeats
   `thermal.py`'s turbine-node lines in the same order; its test
   (`src/model/housing-lag.test.mjs`) proves it reproduces `ThermalNetwork`
   within 1e-9 K, every second of a 300 s run.
3. **The drawing.** `build.mjs` draws the object with the kit, inlines the kit
   and the model, and writes the page into `public/figures/`, which Vite copies
   into `dist/`. The built pages are not committed: `npm run figures` makes them,
   and `npm run build` and `npm run dev` run it first.
4. **The words.** `copy.mjs`, Arabic first. Units stay left-to-right inside
   `<bdi dir="ltr">`, as everywhere in the lab.

The lab shows a figure with `src/FigureFrame.tsx`: an iframe that passes the
lab's language and theme (`?lang=ar&theme=dark`) and takes the page's height.
Opened alone, a page falls back to the lab's saved preferences.

## After a change

```powershell
python figures\housing-lag\export_params.py   # only if the plant moved
npm run build
node --test src/model/housing-lag.test.mjs
..\.venv\Scripts\python.exe -m unittest tests.test_housing_figure -v
```

Then look at the page, as the kit asks: both themes, a phone width (390 px),
and the line check (`node <anatomy skill>/scripts/lines.mjs <page>`, which must
print `line ends: 0`). `docs/HOUSING_LAG_VALIDATION.md` records the first run.
