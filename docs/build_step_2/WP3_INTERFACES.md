<!-- RETIRED-OK: file -- a dated design record of WP3 (23 October 2026), kept as written; verify_docs.py reports it as skipped on every run. -->
> **What this is.** The interface specification that every module and test of WP3 of build step 2 is built against, written on 23 October 2026 on branch `wp3-work` (from `GRA-test` at `cfe6211`: commit A `7a40b9f`, contract version 4 `a1b88e6`), before any WP3 code exists. It fixes the signatures, the record types, the files each module reads and writes with every key of their JSON, the import rules, the hash rules, the shared synthetic fixtures, and the function behind each contract row. It holds no code. Its authorities, in order: `results/ENGINE_THRESHOLDS.md` and `.json` version 5 (cited **MD §n**, **JSON** `key`; repinned from version 4 on 23 October 2026, see below), `docs/build_step_2/AMENDMENTS.md` (**A1**–**G1**, "wrong claim n"), `docs/build_step_2/HANDOFFS.md` (**HO WP3.n**, **HO P7.n**), `results/VALIDATION_DECISIONS.md` section H (**decision n**), `docs/build_step_2/PLAN.md` (**plan §n**). Where these leave a choice open, this file makes it, and says **Chosen here** with the reason. Nothing was fitted, no cycle ran, and no EPA table was opened while writing it (§1.2 lists what was read).
>
> **Repinned to version 5** (23 October 2026, before commit C and before any fit): the contract WP3 is held to is version 5, committed as `c842d74` (`c842d746ab8d50606dc5a3ae70c24bcc16f5f6c8`) on `cfe6211`, version 4's checkpoint, so it descends from version 4 (`a1b88e6`). Version 5 writes decision 77 as the in-sample stage's form criterion (MD §2.4 and §14; JSON `model_form.in_sample_rules.sampling_noise`) and records Ghassan's order of 23 October that Run 1 go ahead before Jad's column is filled (JSON `version_5.go_ahead`); it keeps every R, split, population, statistic and label rule of version 4, MD §3–§5 and §7 unchanged, and the JSON's `schema` 4. `epa_rows.CONTRACT_COMMIT` and `test_contract_pinned.VERSION_5` name it; version 4's commit stays named where a test checks the history (`test_contract_pinned`: version 5's parent chain holds it, and the files are not its blobs) or a sentence tells it. An MD §n below names the same section in version 5, whose numbering is version 4's with §14 added (its header, §2.4, §8, §9 and §10 reworded, every other section as version 4 wrote it); a "version 4" that names where a rule or a reading was written still names it, since version 5 kept it.

# WP3 of build step 2: the interfaces (23 October 2026)

## 1. Scope

### 1.1 What WP3 builds, and what it does not run

WP3 writes, and commit C commits, nine modules and their tests (plan §2 WP3, §8.1): `epa_rows.py`, `epa_stats.py`, `epa_fit.py`, `epa_freeze.py`, `calibrate_epa.py`, `k3_knee.py`, `epa_coefficients.py`, `validate_epa.py`, `d3_rows.py`. Nothing in WP3 runs on EPA data:

- **No fit, no cycle at an EPA row, no statistic on EPA outputs.** Every test of a fit, a statistic, the validation or the D3 reader runs on synthetic tables, contracts, rows and traces (§9), the validation's guards inside temporary git repositories (C5).
- **One exception, structural:** `test_epa_rows.Structural` opens the real tables the way `thresholds/split.py` does (provenance, line, counts against the contract JSON's own counts). It never converts or prints a held-out row's value, and never prints any EPA value. It is the only test that opens `data/engines/*/epa_*.csv`. **Its one call of the generator** (amended 23 October 2026, the second isolation review): `test_split_compute_reproduces_split_json` runs `split.compute()`, the generator's own code, which converts every row in memory, held-out rows included; only the sha256 of its JSON leaves it, and nothing it computes is read, kept or printed. The floor test checks the calibration rows' populations over the printed hot floor's rounding interval, and wraps the generator's classify for one boolean alone (every lambda_ref it classifies with is a printed double): no unrounded value is kept.
- **S0 and T0 belong to Run 1** (A1): `calibrate_epa.py fit` runs S0 as its first stage, and `calibrate_epa.py t0` runs T0 as its own step on committed code. Both evaluate at EPA rows' inputs, so both wait on the Run 1 gate (§5.5.1): version 4 held them for both columns of the decision sheet (section H's header; MD §13 "What is open"); version 5 records Ghassan's order that Run 1 go ahead before Jad's column is filled (MD §14; JSON `version_5.go_ahead`), and the gate holds them until `EPA_RUN1_GO` names the engine.
- **No plant change.** PLANT_CODE and `engine_specs/**` are frozen after commit A (B5). Nothing below needs a plant change; §11 records the one place where WP3 reads plant internals without editing them (the identity check wraps an `engine_env.BaselineECU` instance's `step`, it edits no file).
- **Never** run `engine_thresholds.py`: once `calibrate_epa.py` exists its step 7 refuses by design (`thresholds/document.py`, its claim "calibrate_epa.py does not exist"). `test_contract_pinned.py` replaces `--check` (plan §8.4; decision 66 dropped).

### 1.2 What was read to write this, and what was not (C13)

Read: the five authorities above whole; `thresholds/common.py`, `split.py`, `ecu_shift.py`, `alpha_nodes.py`, `b58_propagation.py`, and parts of `contract.py` and `document.py`; the parts of `engines.py`, `plant.py`, `engine_env.py`, `fingerprint.py`, `derived.py`, `evaluate.py`, `epa_map.py` (its docstring and its channel map `CHANNELS`, `KEY_COLUMNS`, `PROVENANCE`), `test_engine_threading.py` and `test_carried.py` that define the interfaces used here. From the contract JSON, printed: its key paths and value types; its rule texts (`conventions.statistic_details`, `model_form.in_sample_rules`, `model_form.neutral_action_identity`, `tests_lists`, the `rows` populations); `version_4.plant_values` (the neutral action, the shared rich slope, the B58's clip: no EPA value); the first two points of `ecu_strategy_b58.k3_pair_change_vs_lambda` (B58 measurements); the keys, never the values, of `engines.mazda_25t` and its `per_held_out_line` and `lambda_clip_floor`; the keys of one `held_out_rows` record, never a record. `results/ENGINE_THRESHOLDS/ecu/k3_nominal.json`'s keys and its `time_above_nominal_s` and `knee_k` (B58). From the data folder: `MANIFEST.csv`'s header and the local paths and byte counts of its `anl-d3-*` rows; no D3 file was opened.

Not read: no EPA table, not even its header; `epa_channels.csv`; `epa_engine.json`; any `held_out_rows` record; `per_held_out_line`'s values; any ALPHA curve. This list goes into `calibrate_epa.SEEN_BEFORE_THE_FIT` (§5.5).

## 2. Conventions every module follows

1. **Docstrings say why**, cite the contract section, amendment or decision, and are dated 23 October 2026, as the surrounding code is (`thresholds/split.py`, `engines.py`).
2. **No default engine, anywhere** (mistake 1). A parameter called `engine`, `plant`, `cal` or `car` never has a default, and in a function that takes one every other default is one of `test_engine_threading.PROTOCOL_DEFAULTS` (in practice only `dtheta`) or `None` standing for the plant's own value (`PLANTS_OWN_IF_NONE`). **Chosen here:** every such parameter below is keyword-only and required, `dtheta` included, so no call relies on a default; `test_engine_threading.py` (run alone, it writes `_scan_probe_*.py`) scans every new file.
3. **Python scalars only** in any value that becomes a record field or a candidate's values: `float`, `int`, `str` (B10). Every fitted NumPy value is converted with `float()` before it reaches `engines.build_candidate`, which refuses anything else.
4. **Numbers live in `.json` outputs**, never in a `.txt` printout `verify_docs.py` scans (plan §8.1). **Chosen here:** `calibrate_epa.py` prints counts, stage names, flags and paths, never a fitted constant or a statistic; `validate_epa.py run` prints counts and paths only (plan §6.1); no step-2 code writes a `.txt` except `crash_<k>.txt` (C6), which holds a traceback and no figure. New code avoids `verify_docs.py`'s retired patterns `n_cyl\s*=\s*4\b` and `[-−]0\.60|[-−]0\.52|[-−]0\.38` (plan §2 WP3).
5. **No wall-clock time in any output except `run.json`** (plan §5.1), so a re-run gives every other output back byte for byte.
6. **Every JSON output** is written by `epa_freeze.write_json_atomic` (§5.4): `thresholds.common.write_json`'s form (indent 1, LF, ASCII, floats as `repr`) to a temporary file in the same folder, then `os.replace` (plan §6.1 "each output is written atomically"), with `allow_nan=False`. A `None` stands for an absent value; NaN never reaches a file.
7. **Determinism** (plan §5.1): no random number in the fit; fixed grids and starts; an ordered spawn pool that gathers results in submission order; `OMP_NUM_THREADS=1` and `MKL_NUM_THREADS=1` asserted in the parent before any NumPy import and inherited by the workers. T0's noise and C5's redraw streams are the only random numbers, each from a named `numpy.random.default_rng` seed (§5.3, §5.2).
8. **The table names are never literals in a `.py`** (C3; the generator's claim). They come from `epa_rows.TABLES` (built from `thresholds.split.ENG` and cross-checked against the contract JSON's table keys) and are passed as data. Any scan pattern for them is built from parts (`"epa_" + "steady"`).
9. **Units:** speed rpm; pressure kPa absolute; intake and coolant and oil temperature K (`+ 273.15` on the published °C); turbine-inlet temperature °C, the unit of `plant.CycleResult.egt_c` it is compared with (**Chosen here**: a difference of temperatures needs no offset, and keeping the thermocouple in the model's own unit avoids a conversion on both sides; mistake 23 is about which temperature, and the field name says it: `tit_c`); spark degrees BTDC; flows g/s; torque N m; BMEP bar; LHV J/kg; λ dimensionless.

## 3. Which module may import which (C2–C5, C12; plan §4.6 item 7)

### 3.1 The import matrix

A project import not listed for a module is refused by `test_epa_rows.Scans` (§9.4). Standard library, NumPy and SciPy imports are free unless a row says otherwise.

| module | may import from the project | never imports |
|---|---|---|
| `epa_rows` | `thresholds.common` (`REPO`, `ENGINE_DIR`, `CONTRACT_JSON`, `CONTRACT_MD`, `OUT_DIR`, `sha_raw`, `sha_text`); `thresholds.split`: the pure helpers `f`, `ok`, `lam`, `nominal`, `merge`, `name`, `classify`, `coverage`, the data `ENG`, and the constants `LAM_BAND`, `LAM_ENR`, `TOL`, `MIN_CLUSTERS`, `MAP_SPLIT`, `FIRED_BMEP`, `OFF_REF`, `MAP_BAND`, `NOMINAL_RPM` (C2, C3) | any plant module; `split.load`, `compute`, `run`, `report`, `high_load_lines` |
| `epa_stats` | `epa_rows` (row types, constants, `canonical_json`); `thresholds.contract` (`interp`, `T_AMB_C` only); `engines`, `engine_env` (C5's margins only, §5.2.9) | `plant`, `epa_fit`, `thresholds.split`, `validate_epa`; it opens no file |
| `epa_fit` | `epa_rows` (types, constants), `epa_stats`, `engines`, `plant`, `engine_env` | `validate_epa`, `thresholds.split`, `thresholds.contract`; it opens no file |
| `epa_freeze` | `thresholds.common` (`sha_text`, `sha_raw`, `write_json`, `REPO`), `epa_rows`, `engines`, `fingerprint`, `derived`, `plant`, `engine_env`, `thermal` | `validate_epa`, `thresholds.split` |
| `calibrate_epa` | `epa_rows`, `epa_stats`, `epa_fit`, `epa_freeze`, `k3_knee`, `epa_coefficients`, `engines`, `derived`; `d3_rows.unpinned_for` only (its pin check, N11 as amended 23 October 2026) | `validate_epa`, `thresholds.split`, every other name of `d3_rows` |
| `k3_knee` | `engine_env`, `engines`, `evaluate`; `thresholds.ecu_shift` for its constants `ECU_LOAD_KPA` and `SEL` only | `thresholds.b58_propagation`; `ecu_shift.one`, `run_all`, `main`, `path` |
| `epa_coefficients` | `engine_env`, `engines`, `evaluate`, `plant`; `thresholds.contract.T_AMB_C` | `thresholds.b58_propagation` (it builds the B58 at import, C12) |
| `validate_epa` | every module above except `calibrate_epa`, which it runs as a subprocess (`check`, §5.8); `thresholds.split` (`compute`, inside `arm` only, C2); `thresholds.contract` (`interp`); `thresholds.common`; `d3_rows` | `epa_map`, `test_epa_map` |
| `d3_rows` | `epa_stats` (labels and the statistic helpers) | `epa_rows`, every plant module (the model is passed in, §5.9) |

Everywhere: no step-2 module or test imports `epa_map`, `test_epa_map`, `thresholds.alpha_nodes`, `thresholds.knee_shift`, `thresholds.document` or `thresholds.b58_propagation`, nor calls `thresholds.contract.build`, `load_inputs`, `d3_files`, `report` or `dumps` (C3, C12).

### 3.2 The name and call rules (each with a control, mistake 12)

| # | rule | allowed in | source |
|---|---|---|---|
| N1 | the attribute or name `ENGINE_DIR`, `ENGINES_DIR`; a string constant holding `data/engines` or `data\engines`; the string `"tables"` as a subscript or dict key | `epa_rows.py` (and `test_epa_fixtures.py`, which writes synthetic tables under a temporary root) | C3 |
| N2 | `Token`, `verify_for_validation`; every reference to `read_held_out`, `held_out_counts`, `held_out_population_counts` and `held_out_keys` -- a call, a name or attribute (an alias), an `ImportFrom` (under any name), a `getattr` naming one -- and a `getattr` on `epa_rows` whose name is not a literal (amended 23 October 2026: a scan of call names alone passed an alias) | `validate_epa.py`, `test_validate_guards.py`; `held_out_keys` also in `test_epa_rows.py` (the functions are *defined* in `epa_rows.py`; the definitions are the exception). The two count functions also refuse at run time until the calibration's `freeze.json` and `complete.json` are committed at HEAD | C3, C5, plan §4.6 item 7 |
| N3 | reading the contract: the names `CONTRACT_JSON`, `CONTRACT_MD`, a string naming `ENGINE_THRESHOLDS.json`, a `json.load` of it; and (amended 23 October 2026, the second isolation review) a read of a Source's `contract_json`, `contract_md` or `engine_dir` in a step-2 module | `epa_rows.py`, `validate_epa.py`, `epa_freeze.py` (sha_text only: the name may appear only as an argument of `sha_text`), `test_contract_pinned.py`; `test_epa_fixtures.py` writes synthetic ones and never reads the real one. The Source attributes: `epa_rows.py` and `validate_epa.py` only (calibrate_epa and epa_freeze reach the paths through `epa_rows.garbled_source`, `tables_moved`, `engine_file_path`, `table_path` and `audit_paths`) | C4 |
| N4 | `epa_rows.Source.repository()` | production modules; in tests only inside `test_epa_rows.Structural`, `test_epa_rows.CarriedPins` (HO WP3.6: the real contract's view and the real `epa_engine.json`'s facts, never an EPA table; amended 23 October 2026) and `test_contract_pinned.py`. No other test passes the real `ENGINE_DIR`, `CONTRACT_JSON` or `REPO` | C5 |
| N5 | calls of `split.compute`, `split.load` | `validate_epa.arm` (compute); `test_epa_rows.Structural` (compute, load). `split.run`, `split.report`, `alpha_nodes.run`, `b58_propagation.run`, `ecu_shift.one`, `ecu_shift.run_all`, `common.printout` nowhere | C2, C12 |
| N6 | `common.write_json`, `common.write_text` | `epa_freeze.py` only (every other writer goes through `write_json_atomic`) | C12, §2.6 |
| N7 | `Source(..., allow_poisoned_tables=True)` | `calibrate_epa.py` (`poison`) and tests | C8 |
| N8 | an `open(` call, any reader of `OPENERS` (`getlines`, `FileIO`, `load` among them since the second fix), an import of `linecache`, `fileinput`, `io`, `codecs`, `pathlib`, `shutil`, `mmap`, `tokenize` or `urllib`, or one reached through another module's re-export (`epa_rows.io`) | `epa_rows.py`, `epa_freeze.py`, `validate_epa.py` (its `crash_<k>.txt`), `d3_rows.py`, and tests; `calibrate_epa.py` opens nothing itself, its outputs going through `epa_freeze` | §3.1 |
| N9 | the table-name literals `"epa_" "steady"` and `"epa_" "highload"` joined | no new `.py` (the generator's claim, checked over `git ls-files --cached --others --exclude-standard`) | C3, plan §2 WP3, wrong claim 10 |
| N10 | importing `validate_epa` | no module but `test_validate_guards.py` | plan §4.6 item 7 |
| N11 | importing `d3_rows` | `validate_epa.py`, `test_d3_rows.py`, and the two tests that patch its pin check (`test_calibrate_epa.py`, `test_validate_guards.py`); `calibrate_epa.py` for `d3_rows.unpinned_for` alone (amended 23 October 2026: t0 and fit refuse while a D3 summary column is unpinned, since a pin after the first fit is a code change only the defect route admits, C10) | C5 ("its first real read is inside `validate_epa.py run`") |
| N12 | every underscore-prefixed name of `epa_rows` (a dunder excepted; a hand list of readers until the second fix, which passed `_load_json` and `_engine_block`): a reference, an import or a `getattr` naming one; and (widened 24 October 2026, the third isolation review: `epa_freeze._git` and `_read_json` read the contract through git or whole and passed) every underscore-prefixed name of `epa_freeze` | `epa_rows`' names: `epa_rows.py`, `test_epa_rows.py`, `test_epa_fixtures.py`, and `test_calibrate_epa.py`, whose Poison and Seal tests replay the leaks (added 23 October 2026: the isolation review's leak read held-out cells through them and passed every other scan); `epa_freeze`'s: `epa_freeze.py` and `test_epa_freeze.py` | C3 |
| N13 | in a file that opens nothing itself (N8's list: `epa_stats`, `epa_fit`, `calibrate_epa`, `k3_knee`, `epa_coefficients`): an import of `subprocess`, `ctypes`, `_winapi`, `_posixsubprocess`, `concurrent`, `multiprocessing`, `pty`, `builtins`, `importlib`, `runpy`, `code`, `msvcrt`, `_thread`, `threading` or `asyncio`, or one of them reached through a re-export (`epa_freeze.subprocess`); an `os` function that makes a process (`system`, `popen`, `startfile`, `exec*`, `spawn*`, `posix_spawn*`, `fork*`); a `getattr` on `os` or such a module; `__import__`, `eval`, `exec`, `compile`, `__builtins__` (added 24 October 2026, the third isolation review: a child process has no audit hook, and `import subprocess` in a stage, `epa_freeze`'s re-exported `subprocess`, a raw spawn pool and `ctypes` passed every scan) | `epa_fit.py`'s `import multiprocessing`, named only inside its pool helper `_pool`, whose workers run the audit's initializer (§3.3) | C3 |

### 3.3 The runtime audit (C3)

`calibrate_epa.py` installs `sys.addaudithook` before its first project import, for every subcommand, and `epa_fit.ordered_map`'s pool initializer installs the same hook in every spawn worker (a parent's hook does not see a worker, C3's `audit_spawn.py`). `validate_epa.py` installs it in record mode: it records, refuses nothing of the list below, and checks its own allowlist at exit (§5.8.5). In `calibrate_epa.py` the hook:

- records every `open` event's path, normalised to repository-relative with forward slashes, or `<python>/…` under `sys.base_prefix` or `sys.prefix`;
- **refuses at once** (raises `PermissionError` inside the hook) an open of `logs/**`, `data/engines/*/epa_channels.csv`, another engine's `data/engines/<other>/**`, `results/EPA_VALIDATION/**`, any `results/ENGINE_THRESHOLDS/**` but `ecu/k3_nominal.json`, and anything under `thresholds.common.DATA_FOLDER`;
- refuses `subprocess.Popen`, `os.system`, `os.exec*` and `os.spawn*` events whose argv names `data/engines/` or `logs/epa/`, except `git ls-files` and `git hash-object` (C3); and a git command that prints an object's contents (`show`, `cat-file` but its `-t`, `-s`, `-e` and `--batch-check` forms, `diff` but its `--quiet`, `--name-only` and `--stat` forms, `grep`, `blame`, `archive`, `log -p`) unless every path it names (a `<rev>:<path>` word, or a word after `--`) is on the allowlist (23 October 2026: `git cat-file -p <sha>` names no folder);
- **the seal** (amended 23 October 2026, the second isolation review: the contract was on every allowlist, workers included, and a stage could load it whole): refuses the contract's two files, the engine's own tables and `epa_engine.json` in every pool worker, and in the parent once each subcommand has loaded the view, the yield, `engine_facts` and the provenance -- through T0, S0 and the whole ladder with its in-sample stage, poison's reference and poisoned stages and its full fit, e6's refits, complete's measurements and check's recompute (`Audit.sealed`, `seal_now`, `sealed`); the records written after it hash nothing it refuses (the freeze record takes the contract's hashes from the provenance). `refuse_tables`, the tables alone, is the harness the gate's test on this tree sets from the prelude on;
- **the seal over child processes** (added 24 October 2026, the third isolation review: a sealed stage read the contract through `git show HEAD:<contract>` and a held-out cell through a child interpreter, which has no hook, and the poison still read `all_equal` true): while sealed, a child is refused unless it is `subprocess`'s git in one of `SEALED_GIT_SHAPES`, word for word (amended 24 October 2026, the fourth isolation review: the subcommand list `SEALED_GIT` was, and `git diff --exit-code <empty tree> HEAD -- <contract>`, `git log -U0`, `--unified=0`, `--binary`, `-L a,b:<file>`, `--cc`, a `:(glob)` pathspec reaching a table, and `-c core.fsmonitor=<cmd> status` and `-c diff.external=<cmd> diff --ext-diff`, which start a child with no hook, each passed it): the fifteen argv shapes `epa_freeze._git` and `epa_rows._git` run, no other option, no pathspec magic or glob character, no `..`, in the work tree (its cwd and every `-C`), with no executable and no environment of its own; `os.system`, `os.exec*`, `os.spawn*` and `os.posix_spawn` are refused while sealed, and so is a change of the process's environment (`os.putenv`, `os.unsetenv`: `GIT_CONFIG_*`, `HOME` or `PATH` would reach the next git). Sealed or not, a git `-c` other than `core.safecrlf=false`, `--config-env`, `--exec-path` and a pager are refused, and the unsealed content rule reads diff as printing contents unless `--quiet`, and log as printing them with any patch flag (`-U<n>`, `--unified`, `--binary`, `-L`, `--cc`, `-W`, `--word-diff`, `--color-words` among them, and the pickaxe, an oracle on a cell); a git content read of a path the audit refuses to open at that moment (while sealed, the contract, the tables and `epa_engine.json` among them) is refused like the open; Windows' `_winapi.CreateProcess`, whose event carries no usable command line, is admitted while sealed only from `subprocess.Popen` (already judged by its own event) or from `epa_fit._pool` creating workers whose initializer is `worker_init` (read off the calling frames: a pool a stage makes itself, or one without the audit's initializer, is refused); `os.startfile` is refused. A worker's refused child reaches `run.json` beside its opens (`REFUSED_PROCESS_TAG`), so a refusal the task caught is still a defect;
- **another spelling of a sealed file** (the same review): the seal strips Windows' `\\?\` prefix before it compares, and compares each opened file's `(st_dev, st_ino)` with the sealed files' (taken at `bind`), so a hard link or an 8.3 short name is refused at once, not only judged outside the allowlist at the end (`os.stat` raises no audit event); since 24 October 2026 (the fourth isolation review) also with every always-refused file's (another engine's folder, every `epa_channels.csv`, `results/EPA_VALIDATION/`, the generator's outputs but `ecu/k3_nominal.json`, `logs/`; the team's data folder is not walked), and a link made while the audit is active (`os.link`, `os.symlink`, `_winapi.CreateJunction`) is refused, sealed or not;
- **the hook fails closed while sealed** (24 October 2026, the same review): an event the audit cannot read is refused and recorded, not admitted;
- **the seal is the only control for a read of committed git objects or of the repository's own tables** (24 October 2026, the same review): the poison cannot see such a leak by design, since its reference and its poisoned runs read the same committed blob and the same real tables (`all_equal` stays true); `test_calibrate_epa.Seal` keeps a planted form of each content-printing git argv, refused in the fit, the poison and a pool worker, with the step-2 code's own forms as the control;
- in a worker, returns the paths it saw since the last task beside each task's result, and `ordered_map` merges them into the parent's set (**Chosen here**: no queue or file is written from inside a hook, and the merged set is in task order, so `run.json` is deterministic).

At exit the sorted set is written to `run.json` and compared with the subcommand's allowlist (§5.5.4); a path outside it is a coding defect (plan §5.6) and the subcommand exits non-zero. A later step does not build on such an invocation, nor on a crash or a mismatch: `poison`, `e6`, `complete` and `check` refuse while `run.json` holds one (`epa_freeze.audit_problems`), and `validate_epa.py arm` requires `run.json` committed and clean of them; only the defect route (which moves `run.json` with the run) follows.

## 4. The hash rules (plan §8.3, C3, C10)

| what | hash | function |
|---|---|---|
| the contract JSON and MD, every code file, every `results/` output, every spec | sha_text: sha256 with CRLF read as LF | `thresholds.common.sha_text(path)` |
| the EPA tables, `epa_engine.json`, the D3 files, the D3 summary workbook | raw sha256 (stored byte for byte: `data/engines/.gitattributes` is `* -text`; the D3 files are pinned by `MANIFEST.csv`) | `thresholds.common.sha_raw(path)` |
| `epa_channels.csv` | its git blob id from `git ls-files -s`, never opened (its minima and maxima span all rows, plan §4.5; C3) | `epa_freeze.git_blob(path)` |
| a derived file | `fingerprint.derived_sha(path)` (top-level `_` keys dropped) **and** its sha_text | `epa_freeze.derived_record(path)` |
| the frozen sections | `engines.frozen_sections_sha256(values)`, never a copy (its docstring; mistake 10) | — |
| a plant as built | `engines.engine_sha(plant)` | — |
| a plant's code and specs | `fingerprint._sha_files(fingerprint.plant_files(id))` (plan §5.8 "plant"); it is never the validation's guard (RF-3) | `epa_freeze.plant_sha(name)` |
| the frozen-plant dump | sha256 of the float64 `tobytes()` of every array, concatenated in a fixed key order | `epa_freeze.frozen_plant_dump(plant)` |
| the manifest, the yield, the calibration view, any record set | sha256 of `epa_rows.canonical_json(obj)`: `json.dumps(obj, sort_keys=True, allow_nan=False)` UTF-8, the form `engines.frozen_sections_sha256` uses (**Chosen here**: one canonical form for every hash a JSON record carries) | `epa_rows.canonical_sha256(obj)` |

A blob at a commit is compared as `sha256(git show <commit>:<path>)`, which equals the working file's sha_text (the blob is LF; `core.autocrlf=true`, plan §1.1).

## 5. The modules

Each subsection gives the public functions and classes with their signatures, the record types (all `@dataclass(frozen=True)`), what the module reads and writes, and why. A leading `_` marks a private helper named only where a rule depends on it.

### 5.1 `epa_rows.py`: the leak-proof loader (plan §4, C1–C5, C7–C9, C13)

**Constants.**

| name | value or source | why |
|---|---|---|
| `CONTRACT_COMMIT` | `"c842d746ab8d50606dc5a3ae70c24bcc16f5f6c8"` (version 5; version 4's `a1b88e6` before the repin of 23 October 2026) | plan §4.2 guard 1 |
| `CONTRACT_SCHEMA` | `4` (the contract's numbering, MD §13; kept by version 5, MD §14; the plan's `3` was version 3's) | plan §4.2 |
| `LAM_BAND`, `LAM_ENR`, `TOL`, `MIN_CLUSTERS`, `MAP_SPLIT`, `FIRED_BMEP`, `OFF_REF`, `MAP_BAND`, `NOMINAL_RPM` | imported from `thresholds.split`, re-exported so that `epa_stats` and `epa_fit` never import `split` | mistake 10; C2 |
| `SENTINEL_SPARK` | `-120.0`, the published sentinel (`epa_map.py:47-48`); a row whose spark cell is exactly that, or empty, is a sentinel row | decision 54 and its reading of 23 October (MD §3) |
| `ROLES` | `("steady", "initial", "final")` | |
| `TABLES` | `{engine: (TableSpec, ...)}` built at import from `split.ENG` (Ford: steady index 0 is Cell 9, index 1 HD1; holds are HD1's) | §2.8: the names are data |
| `HEADERS` | `{(engine, role, index): (column, ...)}`: each table's header, pinned | mistake 13 (plan §4.2 guard 3) |
| `FIELD_OF_COLUMN` | `{column: field}` for every converted column | |
| `DROPPED_COLUMNS` | the columns tokenised and never converted: `source_file`, `source_sheet`, `bsfc_g_per_kwh`, `bte_pct`, `fuel_rail_press_mpa_gauge`, the `cac_*` and `catalyst_*` columns | every pinned column is in exactly one of the two, checked (§9.4) |
| `DOCUMENTED_FLOORS` | `{}` | a λ-sensor floor is documented only by a source opened and cited before the fit (MD §3); none has been opened |

**Chosen here (the header pins).** `HEADERS` are typed by WP3's implementer from each table's first line, read once and before commit C (structure, as plan §0's authors read "the header structure of the tables"), and that read is entered in `SEEN_BEFORE_THE_FIT`. Keys are `(engine, role, index)`, never a table name (§2.8).

**Records.**

`TableSpec`: `engine: str`, `name: str` (the file name, as the contract's `engines.<id>.tables` keys hold it), `role: str` (one of `ROLES`), `index: int` (the position among the engine's tables of that role).

`Source`: where the tables and the contract live.

| field | type | meaning |
|---|---|---|
| `root` | `str` | a git work tree (the repository, or a test's temporary repository) |
| `engine_dir` | `str` | the folder holding `<id>/epa_*` |
| `contract_json`, `contract_md` | `str` | the contract's two files |
| `contract_commit` | `str` | the commit whose blobs they must equal |
| `allow_poisoned_tables` | `bool` | `True` only for C8's poison run: the table-hash guard is replaced by "the calibration rows' raw records equal the real tables' (manifest equality)", a stronger check; N7 |

`Source.repository() -> Source` (classmethod): `thresholds.common`'s `REPO`, `ENGINE_DIR`, `CONTRACT_JSON`, `CONTRACT_MD` and `CONTRACT_COMMIT`, `allow_poisoned_tables=False`. **Chosen here:** an explicit source instead of module paths, so that every test of the reader runs on a temporary root (C5) while production code names the repository once.

`Populations` (the keys of `split.classify`, computed by `split.classify` on a minimal dict of the row's raw strings, so the populations are the generator's own, mistake 10): `fired`, `fired_meter`, `hot`, `hot_meter`, `hot_l1`, `hot_enr`, `hot_l1_meter`, `l1_boost`, `l1_thr`, `l1_off_ref`, all `bool`, and `fired_l1: bool` (E3b's population, "fired λ≈1"), taken as `classify(r, ref, -math.inf, kind)["hot_l1"] and fired`, so that the λ≈1 test is `split`'s own expression (**Chosen here**: `classify` has no fired-λ≈1 key, and re-writing its λ test would be a second definition).

`PointRow`, the fields a steady or Final row carries (plan §4.3, as C1, C9 and decision 54 correct it). No field exists for a dropped column.

| field | type | unit, source column, rule |
|---|---|---|
| `engine`, `table` | `str` | |
| `source_row` | `int` | the spreadsheet row (`epa_map.py` writes data from row 6) |
| `test_cell`, `fuel_report` | `str` | provenance |
| `origin` | `str` | `"epa"`; `"t0"` for T0's synthetic outputs; `"fixture"` in tests. **Chosen here**: a calibration function can refuse a row that is not what it expects |
| `line` | `str` | the contract line it belongs to (`engines.<id>.lines`, merged names split on `/`) |
| `nominal_rpm` | `int` | `split.nominal` |
| `hold` | `int` or `None` | a Final row's hold id (its `source_row`, shared with its Initial row); `None` on a steady row |
| `speed_rpm` | `float` | rpm, `speed_rpm` |
| `map_kpa` | `float` | kPa abs, `intake_manifold_press_kpa_abs` |
| `imt_k`, `ect_k`, `oil_k` | `float` | K, `intake_manifold_temp_c`, `coolant_temp_c`, `oil_sump_temp_c` + 273.15 |
| `spark_btdc` | `float` or `None` | deg BTDC, `spark_timing_cad_btdc`; `None` on a sentinel row |
| `spark_sentinel` | `bool` | exactly `SENTINEL_SPARK`, or an empty cell (decision 54, reading of 23 October) |
| `lam_meas` | `float` or `None` | `split.lam` (HD1: the mean of both banks); `None` when missing, and on HD1 when either bank is empty (decision 54's reading) |
| `lam_banks` | `(float or None, float or None)` or `None` | HD1 only |
| `lambda_missing` | `bool` | |
| `lam_ref` | `float` | the table's λ_ref from the contract (never recomputed, plan §4.1) |
| `torque_nm` | `float` | N m |
| `bmep_bar` | `float` | bar (populations need it, wrong claim 25) |
| `fuel_meter_gps` | `float` or `None` | g/s, `fuel_meter_flow_gps`; `meter_missing: bool` beside it |
| `injector_fuel_gps` | `float` or `None` | g/s: EPA's calculated estimate, flagged, never a stand-in for the meter (mistakes 9, 19) |
| `tit_c` | `float` | °C, `turbine_inlet_temp_c`: the gas-side thermocouple (mistake 23) |
| `tip_kpa` | `float` | kPa abs, `turbine_inlet_press_kpa_abs` |
| `baro_kpa`, `cell_temp_k` | `float` or `None` | `cell_press_kpa_abs`, `cell_temp_c` + 273.15; `None` on HD1, which publishes neither |
| `cam_cad`, `cam_channel`, `cam_missing` | `float` or `None`, `str` or `None`, `bool` | the intake cam as published, by its channel name (`intake_cam_phase_cad_ret` or `_adv`; mistake 13): no sign is assumed (plan §5.3) |
| `exhaust_cam_cad`, `valve_overlap_cad`, `atkinson_ratio`, `eff_compression_stroke_mm`, `eff_expansion_stroke_mm`, `eff_compression_ratio`, `eff_expansion_ratio` | `float` or `None` | EPA's valve channels, for E6 row 9's brackets (plan §5.9 item 6; E3) |
| `pops` | `Populations` | |

`SteadyRow(PointRow)` and `FinalRow(PointRow)`: the calibration rows. `HeldOutRow(PointRow)` adds `kind: str` (`"steady"` or `"final"`). **Chosen here:** the held-out rows are a different type with the same fields, so `epa_fit` refuses any row whose type is not exactly `SteadyRow` or `FinalRow` (a held-out row cannot slip into a fit by being the same class), while `epa_stats` accepts all three.

`InitialRow` (calibration High Load Initial; plan §4.3): `engine`, `table`, `source_row`, `test_cell`, `line`, `nominal_rpm`, `hold`, `speed_rpm`, `torque_nm`, `origin`, `transient: bool` (always `True`). It has no TIT, λ, MAP or fuel field: asking for one raises `AttributeError` (MD §2.3; `turbine_inlet_temp_c` is never read from an Initial row in the calibration). Its torque serves only C7's descriptive full-throttle comparison and decision 43's fallback.

`HeldOutInitialRow`: `InitialRow`'s fields plus `map_kpa`, `imt_k`, `ect_k`, `spark_btdc`, `spark_sentinel`, `lam_meas`, `lambda_missing`, `bmep_bar`, `tit_c`, `tip_kpa` (E1i at its own inputs; the descriptive Initial-to-Final pair estimate, MD §4 E4b; plan §4.3).

`TableCount`: `name`, `role`, `rows`, `calibration`, `held_out_skipped` (all `int` but the strings).

`Manifest`: `engine: str`, `tables: Mapping[str, ManifestTable]`, `sha256: str` (of the canonical JSON of the rest). `ManifestTable`: `header_sha256: str`, `keys: tuple[int, ...]` (sorted calibration `source_row`s), `rows_sha256: str` (sha256 of the calibration rows' raw cell strings, re-serialised with `csv.writer(lineterminator="\n")` in file order). **Chosen here:** the manifest is computed from raw strings and keys alone, so it needs no conversion of any value, and a poisoned held-out cell cannot move it.

`Yield`: `engine: str`, `rows: tuple[SteadyRow | FinalRow | InitialRow, ...]` (table order, then file order), `counts: tuple[TableCount, ...]`, `manifest: Manifest`, `sha256: str` (canonical JSON of `dataclasses.asdict` of every row).

`TableFuel`: `ftag: str`, `fuel_report: str`, `lhv_j_per_kg: float`, `afr_st: float`. **Chosen here:** `lhv_j_per_kg` is `float(repr(lhv_mj_per_kg) + "e6")`, the correctly rounded double of the decimal the contract prints, which is the double TOML gives for `42.908e6`; a product by `1e6` can differ by an ulp. `test_epa_rows` shows the Mazda's table fuel equals `engines.typed_engine("mazda_25t").fuel` to the bit, where the two are the same batch (decision 69).

`CalibrationView` (C4: the one accessor's allowlist, deep-copied):

| field | type | from the contract JSON |
|---|---|---|
| `engine`, `contract_commit`, `contract_sha_text` | `str` | |
| `lines`, `held_out_lines` | `tuple[str, ...]` | `engines.<id>.lines`, `.held_out_lines` |
| `table_counts` | `tuple[TableCount, ...]` | `engines.<id>.tables` (rows, held out, calibration) |
| `lambda_ref` | `Mapping[str, float]` | `engines.<id>.lambda_ref` |
| `hot_map_floor_kpa` | `float` | `engines.<id>.hot_map_floor_kpa` |
| `fuel_by_table` | `Mapping[str, TableFuel]` | `engines.<id>.fuel_by_table` |
| `lam_floor` | `float` | `engines.<id>.lambda_clip_floor.floor` (never `.where` or `.deepest_epa_lambda_cell_referenced`, which are all-row facts) |
| `coverage_calibration_fired`, `coverage_calibration_hot` | `Mapping` | `engines.<id>.coverage.calibration_*` |
| `conventions`, `model_form` | `Mapping` | `conventions`, `model_form` |
| `R` | `Mapping[str, (float, str)]` | the engine's entries of `thresholds` (row → R, unit) |
| `mei_points`, `r1_housing_k`, `b_points` | `float` | `mei_points`, `r1_housing_k`, `budget.b_points` |
| `propagation_b58` | `Mapping` | `propagation_b58` (G = `G_gas_over_42C_k`) |
| `ecu_strategy_b58` | `Mapping` | `ecu_strategy_b58`: **chosen here**, added to C4's list, since in-sample E8 needs P and the table holds B58 measurements only |
| `perturbations_e6` | `tuple[Mapping, ...]` | `perturbations_E6`: **chosen here**, added (the bands, rule text and λ offsets already in the list) |
| `e8_min_rows` | `int` | `conventions.statistic_details.e8_min_rows` |
| `k3_seconds` | `int` | `results/ENGINE_THRESHOLDS/ecu/k3_nominal.json` `time_above_nominal_s`, its sha_text checked against `generator_inputs_sha256["ecu/k3_nominal.json"]` (plan §5.9 item 4) |

Never in the view: `held_out_rows`, `per_held_out_line`, `deciding_lines`, `pooled_counts`, `offsets`, `eligible`, `alpha_nodes_removed`, the all-row coverage blocks, `lambda_clip_floor.where` (C4, C7). `CalibrationView.as_json() -> dict` and `.sha256 -> str` exist for the poison comparison.

`EngineFacts` (plan §4.2 guard 4; C7): `displacement_l`, `n_cylinders`, `compression_ratio`, `bore_mm`, `stroke_mm` (each `float`/`int` or `None`), `geometry_notes: str`, `alpha_fuel: Mapping`, `table_sources: Mapping[str, (fuel_report, test_cell)]`, `reference_only_columns: tuple[str, ...]`. The two ALPHA curves are never returned.

`ContractCheck`: `commit`, `json_sha_text`, `md_sha_text: str`, `schema: int`, `generators: Mapping[str, str]`.

`HeldOut`: `engine: str`, `rows: tuple[HeldOutRow | HeldOutInitialRow, ...]`, `counts: Mapping[str, int]`.

`HeldOutCounts`: `fired_lambda_missing`, `fired_spark_sentinel`, `final_rows`, `final_lambda_published`, `final_spark_published: int`; `e8_subsets_enough: bool` (each subset ≥ `e8_min_rows`, MD §4 E8).

Exceptions: `LoaderStop(Exception)` (a count, hash, header or id mismatch: "a re-derivation must reproduce the counts of section 2.2, or stop", MD §10); `SplitViolation(LoaderStop)` (a calibration row on a held-out line); `NotArmed(Exception)`.

**Functions.**

- `canonical_json(obj) -> bytes`; `canonical_sha256(obj) -> str` (§4).
- `check_contract(*, source) -> ContractCheck`: guard 1, the contract's sha_text equals the blobs at `source.contract_commit`, that commit is an ancestor of HEAD (`git merge-base --is-ancestor`), `schema == CONTRACT_SCHEMA`; guard 2, every file of `generators.sha256` hashes to its value, both the imported module's file (`split.__file__`, `common.__file__`: the code that runs) and `source.root`'s copy (plan §4.2).
- `check_tables(engine, *, source) -> tuple[TableSpec, ...]`: guard 3, each table's `sha_raw` equals `epa_tables_sha256["<id>/<name>"]` (or, under `allow_poisoned_tables`, the manifest-equality check), its header equals `HEADERS`, and the contract's table keys equal `TABLES[engine]`'s names.
- `calibration_contract(engine, *, source) -> CalibrationView` (C4).
- `engine_facts(engine, *, source) -> EngineFacts`.
- `calibration_rows(engine, *, source) -> Yield`: streams each table with `csv.reader` (not `split.load`, plan §4.3). For each record `source_row` is read first; **a key in H is counted and skipped, its other cells never parsed, converted, yielded or cached** (the row is tokenised by `csv.reader`, never converted: C9, wrong claim 15). Otherwise the line is recomputed from the row's own speed (`split.nominal`): a speed in no line raises `KeyError`, a held-out line `SplitViolation`. After each table: the held keys seen equal that table's share of H; the counts equal the contract's `tables`; the ids are exactly 6…N+5; the High Load Initial and Final calibration ids are identical. A required column (`epa_map.KEY_COLUMNS`, as pinned) that is not finite on a calibration row stops the loader naming the table, row and column, never the value.
- `manifest(engine, *, source) -> Manifest` (plan §4.3).
- `calibration_coverage(engine, *, source) -> Mapping[str, Mapping]`: `split.coverage` over the fired and hot calibration rows, built from their raw °C strings (C9), returned as `{"calibration_fired": …, "calibration_hot": …}` for comparison with the contract (plan §4.6 item 3).
- `garbled_contract(src_json, dst_json) -> None`: a copy of a contract with every forbidden key's values garbled (C4's poison of the keys), for `calibrate_epa.py poison` and the tests.
- `held_out_counts(engine, *, source) -> HeldOutCounts` (N2; `validate_epa.arm` only): tokenises the held-out rows and converts only BMEP, the λ cells' presence and the spark cell's sentinel test (C2: "held-out counts move to `validate_epa.py arm`"; MD §3, "the held-out rows' counts of both are taken only when the held-out run is armed").
- `read_held_out(engine, *, source, token) -> HeldOut` (N2): **refuses, whatever token is passed, unless `<root>/results/EPA_VALIDATION/<id>/ARMED.json` is committed at HEAD with table, derived-file and code hashes that match the tree** (C5), and unless `token.engine == engine` and `token.armed_blob` is ARMED.json's blob at HEAD. **Chosen here:** the reader is defined here, the only module that opens the tables (C3 N1), and checks the token by its fields, not its class, so it needs no import of `validate_epa`.

### 5.2 `epa_stats.py`: every statistic, one definition for in-sample and held-out (plan §5.5, §6.2–6.4; MD §3–4)

`epa_stats` is arithmetic over rows and a model object it is given; it imports no plant module but `engines` and `engine_env` for C5 (§3.1), and opens no file. The in-sample stage and the held-out run call the same functions (mistake 10).

**5.2.1 Conventions and inputs.**

`Conventions`: `snap: bool` (MD §3's snap; E6 row 12 `False`), `cell_referenced: bool` (λ_meas − (λ_ref − 1); E6 row 1 `False`: as published, the snap kept), `afr_st: float | None` (E6 row 2: 14.7 in the calibration air and the plant's fuel), `lhv_j_per_kg: float | None` (E6 row 3: 44.0e6 through `engines.with_fuel`). `NOMINAL = Conventions(True, True, None, None)`.

`RowInputs` (MD §3 "inputs fed"; plan §5.1): `engine`, `table: str`, `source_row: int`, `rpm`, `map_kpa`, `iat_k`, `ect_k`, `spark_btdc`, `lam: float`, `lam_source: str` (`"snapped"`, `"cell_referenced"`, `"published"`, `"missing_at_1.00"`), `spark_source: str` (`"published"`, `"model_ecu_sentinel"`), `fuel: TableFuel` (after the conventions' overrides).

Functions:
- `lam_cellref(row) -> float | None`: λ_meas − (λ_ref − 1), unsnapped (E8's EPA λ; MD §4 E8, decision 57).
- `lam_fed(row, *, conventions) -> (float, str)`: 1.00 if missing (decision 54) or, under `snap`, within `LAM_BAND + TOL` of λ_ref; else the cell-referenced (or published) λ.
- `fuel_of(row, *, view, conventions) -> TableFuel`: the row's own table's fuel (MD §3, decision 69), with E6 rows 2–3's overrides.
- `air_cal(row, *, view, conventions) -> float | None`: meter × AFR_st × `lam_fed`, steady and Final rows only; `None` without a meter or a λ (MD §3; plan §4.3).
- `row_inputs(row, *, view, conventions, model) -> RowInputs`: a sentinel row runs at `model.ecu_at(...)`'s spark (dwell 30 s, no knock retard, EPA's IMT; decision 54).
- `censoring(rows) -> Censoring` (`censored: bool`, `value: float | None`, `n_at_min: int`, `documented_floor: float | None`, `rule: str`): on the calibration Final rows themselves, ≥ 2 within 1e-9 of their own minimum λ, or a `DOCUMENTED_FLOORS` entry (C1, decision 54, MD §3).
- `held_out_censored(rows, *, censoring) -> tuple[(str, int), ...]`: a held-out Final row at the censoring value; one below it is not counted (MD §3, after the seventh review).

**5.2.2 The model protocol.** Any object passed as `model` provides (implemented by `epa_fit.RowModel`, §5.3; `test_epa_fixtures.ToyModel` for hand answers):

- `cycle(x: RowInputs, *, dtheta: float) -> ModelOut` — plan §5.1's call;
- `ecu_at(rpm, map_kpa, iat_k, ect_k) -> EcuOut` — a fresh `BaselineECU`, one `step(rpm, map_kpa, iat_k, ect_k, False, 30.0)`: dwell 30 s, no knock retard (MD §4 E8; D3);
- `base_spark(rpm, map_kpa) -> float`; `cam(rpm, map_kpa) -> float | None`;
- `ecu_trace(rpm, map_kpa, iat_k, ect_k, dt) -> (spark, lam)` arrays, the dwell timer run along a trace (C3's chain, MD §5);
- `charge(t_amb_k, t_block_k) -> float` (`plant.charge_temperature`; C3).

`ModelOut`: `torque_nm`, `fuel_gps`, `air_gps`, `egt_c`, `knock_integral`, `eta_v` (`float`). `EcuOut`: `spark_btdc`, `lam: float`, `cam_deg: float | None`.

**5.2.3 Per-row evaluation (picklable kernels, run through `epa_fit.ordered_map`).**

`PointTask`: `row`, `conventions`, `dtheta: float`, `needs: frozenset[str]` (`"at_epa"`, `"d1"`, `"lam1"`, `"ecu"`), `shift: InputShift | None`. `InputShift`: `channel: str` (one of `speed`, `map`, `imt`, `ect`, `spark`, `lam`), `delta: float`.

`Measured`: `torque_nm`, `meter_gps: float | None`, `tit_c`, `lam_cellref: float | None`, `spark_btdc: float | None`, `map_kpa`, `bmep_bar`.

`D1Point`: `map_kpa: float` (the inverted MAP), `bracketed: bool`, `bound_kpa: float | None` (20 or 400 when unbracketed), `spark_btdc: float`, `cam_deg: float | None`, `out: ModelOut`, `delta_d: float | None` (fuel/meter − 1), `e_d: float` (TIT_m − TIT_E), `n_cycles: int`.

`RowEval`: `engine`, `table`, `source_row`, `line`, `kind` (`steady`, `final`, `initial`), `hold`, `pops: Populations`, `origin`, `inputs: RowInputs`, `measured: Measured`, `out: ModelOut | None` (at EPA's MAP), `lam1: ModelOut | None` (the row at λ = 1: enriched hot rows, E4b), `d1: D1Point | None` (fired rows with a meter), `ecu: EcuOut | None` (Final rows: E8), `flags: frozenset[str]` (`lambda_missing`, `spark_sentinel`, `censored`, `outside_calibration_map_coverage`, `snapped`).

Kernels: `kernel_point(model, task) -> RowEval`; `d1_invert(x, torque_target, *, model, dtheta, spark_slope) -> D1Point` — the pre-scan 20–400 kPa every 10 kPa, bisection of the first bracket to 1e-3 kPa, nearer bound when unbracketed; spark = EPA's (or the sentinel row's model spark at EPA's MAP) + s·(MAP − MAP_E), s = (`base_spark`(MAP_E+2) − `base_spark`(MAP_E−2))/4; form D's cam at the inverted MAP (MD §4 D1; decisions 41, 54, 57).

**5.2.4 Results.**

`UTerms`: `u_num`, `u_input`, `u_D`, `u_val`, `u_stat: float`, `u_num_sd_undivided: float`, `unsourced: tuple[str, ...]`.

`LineStat`: `line: str`, `clusters: int`, `E: float`, `u: UTerms | None`, `label: str | None`, `certifies: bool | None`.

`StatResult`:

| field | type | meaning |
|---|---|---|
| `row` | `str` | the contract row (`E1a` …) |
| `stage` | `str` | `"in_sample"` or `"held_out"` |
| `R`, `unit`, `kind` | `float or None`, `str`, `str` | from the view; kind `level`, `d`, `descriptive` |
| `E` | `float or None` | the reported E: the worst deciding line's for a per-line row (decision 57: the largest \|E_l\|, of two equal the larger u_val), or the pooled value |
| `lines` | `tuple[LineStat, ...]` | every line with its population |
| `deciding`, `certifying` | `tuple[str, ...]` | lines with ≥ `MIN_CLUSTERS` clusters; lines with 2u_stat ≤ R |
| `worst_line` | `str or None` | |
| `u` | `UTerms or None` | held-out only (in-sample rows are fit residuals: no u, plan §5.5) |
| `label`, `kappa` | `str or None`, `float or None` | held-out only; κ = 1 if validated, else (\|E\| + 2u_val)/R (MD §7) |
| `passes` | `bool or None` | in-sample only: \|E_cal\| ≤ R; `None` for no deciding line (decision 55) |
| `no_statistic`, `reason` | `bool`, `str or None` | a d row with no statistic drops the engine (MD §7) |
| `without` | `Mapping[str, float or None]` | the readings "also reported without": λ-less rows, sentinel rows, D1's unreachable rows, E8's censored rows (decision 54, 57; MD §3) |
| `coverage_restricted` | `float or None` | the statistic restricted to calibration MAP coverage (decision 58) |
| `extra` | `Mapping` | row-specific reports (below) |
| `n_rows`, `n_clusters` | `int` | |

`StatResult.as_json() -> dict` (§7.6).

**5.2.5 The statistics.** Each has the signature `row_<id>(evals, *, view, stage, tightening) -> StatResult`, where `evals` are `RowEval`s of one population source (calibration or held-out), `stage` is `"in_sample"` or `"held_out"`, and `tightening` is `None` in-sample and the parsed `EPA_TIGHTENINGS.json` held-out (§7.5). §8 maps every contract row to its function.

- `row_E1a`, `row_E2a`, `row_E3a`, `row_E4a`: worst deciding line's mean signed error over `hot`, `hot_meter`, `hot_l1`, `hot_enr` (T_m/T_E − 1; F_m/F_meter − 1; `egt_c` − TIT; the same) (MD §4). `E4a`'s `extra.censored_rows` flags censored rows (decision 54).
- `row_E1b`, `row_E2b`, `row_E3b`: pooled mean |·| over `fired`, `fired_meter`, `fired_l1`; descriptive, `extra.worth_b` from the view.
- `row_E1i(evals_initial, …)`: per line mean signed torque error at the Initial rows' own inputs, labelled transient (held-out only).
- `row_E4b`: L_S = S(λ=1) − S(row); ê from the line's least-squares line of the λ≈1 error on MAP over its boosted λ≈1 rows (MAP ≥ 100, n ≥ 3), at the row's MAP; ε = ΣL_S/Σ(L_S + e_enr − ê) − 1; `extra`: the extrapolation distances, and (held-out) the Initial-to-Final pair estimate over holds whose λ drops ≥ 0.05, descriptive (MD §4 E4b). u_stat by the delta method on cluster sums.
- `row_E5`: windows A (MAP < 100, BMEP ≥ 2) and B (MAP ≥ 100), Σcov(MAP,S)/Σcov(MAP,D) − 1, `np.cov(ddof=1)` per line with ≥ 3 rows in the window; descriptive.
- `row_D1`: mean |δ_D| pooled over `fired_meter`, unreachable rows counted at the nearer bound (the gating D1, in-sample and held-out: D12, decision 57); `without["unreachable"]`; `extra.unreachable: [[table, row], ...]`.
- `row_L0`: per deciding line ē, δ̄ over `hot_l1_meter` at the D1 point; max over f ∈ [0,1] of |fē + f(1−f)Gδ̄| by its endpoints and vertex, G from `view.propagation_b58`; worst line. u_stat at the maximising f* (envelope theorem).
- `row_L1`: max over f of [max_l H_l − min_l H_l], exact over ordered pairs (each difference quadratic in f), ≥ 2 deciding lines; R = 9.9 K in-sample (decision 71's untightened R, MD §2.4), b/slope held-out if the B58's roads slope exceeds 0.0905; u_stat √(u_a² + u_b²) of the two extreme lines at the maximising f.
- `row_E8`: dl over the Final rows that publish a λ (EPA's λ cell-referenced, unsnapped), ds over those that publish a spark, each needing ≥ `view.e8_min_rows` rows or `no_statistic` (decision 54's readings, MD §4); E8 = |P_λ(dl)| + |P_s(ds)| through `thresholds.contract.interp` (linear extrapolation flagged); held-out P per shift the larger |·| of the contract's and the roads' tables, sign kept (decision 57); u through the slope of the segment holding the shift, at 0 the steeper side. `extra`: dl and ds alone; dl and ds over every Final row (λ 1.00, difference 0); dl without the censored rows; the error worth b (`view.ecu_strategy_b58.worth_b`); per line the lowest MAP where the model's λ falls 0.05 below λ_ref, beside EPA's; the snapped E8, descriptive. In-sample it is computed and reported, outside the form criterion (decision 39(a)).
- `e8_response(view, *, tightening) -> (points_lambda, points_spark)`.

**5.2.6 The u-terms (MD §3; plan §6.2; decision 56).**

- `U_INPUT: Mapping[str, UInput]` for `speed`, `map`, `imt`, `ect`, `spark`, `lam`; `UInput`: `value: float` (the standard uncertainty of one reading), `kind: str` (`"stated accuracy"`, `"resolution/sqrt(12)"`, `"declared floor, unsourced"`), `source: str`, `unsourced: bool`, `cells` (amended 23 October 2026, decision 56's pins: EPA states the uncertainties per test report, so each report's pin is a `((engine, test_cell), CellPin)` pair and `value` is the fallback a row whose report states nothing reads). The values are pinned as numbers before commit C (decision 56), from EPA's instrument pages if they state one, else the steady table's printed resolution/√12 (plan §6.2: λ 0.01, MAP 0.01 kPa, temperature 0.1 °C, speed 1 rpm), never from `repr` digits. **Chosen here** for spark, if no page states it: a declared resolution of 0.1 CAD, marked unsourced.
- `U_D: Mapping[str, UD]` for `tit` (0.0075·|t̄|/√3, common), `lam` (0.012, common, where EPA's λ is compared, E8, or enters a reference, E4b), `meter`, `torque` (stated accuracy, else resolution/√12, random), each with `unsourced: bool` (MD §3) and `cells` as `UInput`'s; `UD.at(cell)` gives the pin of a row's report (`epa_stats.cell_of(row)`, the row's `(engine, test_cell)`), and a row with neither its report's pin nor a fallback refuses (`UnpinnedUncertainty`). `CellPin`: `value`, `printed` (the number as the report prints it), `column` (`"u(signal)"`, or `"u(calibration)"` where the report prints no other), `file`, `where`, `header`, `row` (the Table 8 row, verbatim), `note`. `InputShift` carries the same per-report deltas (`cells`, `delta_for(row)`), and `RowEval` the row's `test_cell`.
- `u_num(stat, evals_025, evals_0125) -> (float, float)`: per row ΔS = S(0.125°) − S(0.25°), mean removed, random; the undivided SD beside it (E6 row 8).
- `u_input(stat, evals, shifted) -> float`: per channel j and cluster c, s_jc = central difference of the whole statistic (D1's bisection included) with that cluster's inputs shifted by ±h; √Σ (s_jc·u_j)². `shifted: Mapping[(channel, sign, key), RowEval]`.
- `u_d(stat, evals) -> float`: common parts |stat(x + u) − stat(x)| with every row moved together; random parts per cluster; on the measured side only, no model re-run.
- `u_stat_line(values) -> float`: SE of the mean, one row per cluster.
- `combine(u_num, u_input, u_d, u_stat, unsourced) -> UTerms`: u_val = √(u_num² + u_input² + u_D²).

**5.2.7 Labels (MD §3, §7; plan §6.2).**

- `line_label(E, u_val, u_stat, R) -> (str, bool)`: off if |E| − 2u_val > R; else untested if 2u_val > R; else validated if |E| + 2u_val ≤ R; else limited; certifies only if 2u_stat ≤ R.
- `row_label(lines) -> str`: off if any deciding line is off; else the worse of the certifying lines' labels; untested if none certifies.
- `worse(a, b) -> str` in the order off > untested > limited > validated (E6 row 12, decision 59).
- `kappa(E, u_val, R, label) -> float`.
- `section7(results, *, engine) -> Mapping`: the level rows' label for the engine's 850 °C row; each d row's band factor; `DROP` for an off d row or one with no statistic (MD §7).

**5.2.8 The in-sample stage (MD §2.4; JSON `model_form.in_sample_rules`).**

`in_sample(evals, *, view) -> InSample`, with `InSample`: `results: Mapping[str, StatResult]` (E1a, E2a, E3a, E4a, E4b, D1, L0, L1, E8), `passes: bool` (every result but E8 has `passes` true or `None`), `failing: tuple[str, ...]`, `no_line: tuple[str, ...]`, `criterion: str`. No u-terms, never labelled (plan §5.5).

**5.2.9 E6 and C5.**

- `excluded_for(base, probed) -> bool`: |ΔE| < u_val under the probe (MD §4 E6).
- `excluded_for_every_listed_constant(row, exclusions, *, tests_lists) -> bool`: decision 59's counting rule (E4): a member no E6 row perturbs counts as not excluded; E8 is never excluded.
- `refit_movement(base, variant) -> Mapping[str, float]`: every E row's ΔE, no exclusion label (rows 1, 3, 7; E2).
- `must_not_move(base, variant, rows) -> Mapping[str, (float, float, bool)]`: row 2's E2, D1, L0 within their u_val; a miss is a finding, not a stop (MD §4 E6).
- **C5** (MD §5; decisions 64, 70, 73–76; plan §7.4 "this step supplies `c5_margin(plant, cycle)` and its test"). **Chosen here:** C5 lives here, beside every other contract row's definition, though the roads step applies it.
  - `C5Step`: `k: int`, `transition: bool`, `gated: bool`, `held: str` (gear number or CVT branch), `margins: tuple[(str, float, bool), ...]` (name, |demand/threshold − 1|, gates), `bar_rpm_margin: float | None`, `no_margin_case: str | None` (the three cases of MD §5).
  - `c5_steps(plant, cycle, *, first, last) -> tuple[C5Step, ...]`: the held gear's and every rejected higher gear's margin against `Vehicle.shift_ceiling_nm(rpm)` at the rpm `gear_for` computes; a downshift barred by `SHIFT_RPM_MAX` gates no held margin (evaluated whether or not the held demand exceeds its ceiling, MD §5); the CVT's T_eco against `kickdown_threshold_nm(N_eco)`; the transition test by exact inequality of the recorded float64 arrays, a missing neighbour taken as the step itself.
  - `c5_climb(steps, *, margin, thin_share) -> C5Climb` (`outcome: str` one of `fails`, `thinly_checked`, `passes`; `gated_share`, `transition_share: float`; `failing_steps: tuple[int, ...]`); `thin_share` is the contract's 0.5 (DESIGN).
  - `c5_margin(plant, cycle) -> tuple[C5Step, ...]` = `c5_steps(plant, cycle, first=0, last=len−1)` (the plan's name).
  - `cvt_diagnostic(plant, *, v_mps, force_n, margin) -> Mapping`: decision 40's report, the feasible set's connectedness under demand and T_del × (1 ± m).

### 5.3 `epa_fit.py`: the fitting procedure (plan §5, as C1, D1–D14, decisions 49–53 amend it)

**Constants**, each with its source in its docstring: `RIDGE_W = 0.01`; `SCALES` (plan §5.2: burn_base 10, burn_rpm 0.002, delay_base 5, delay_rpm 0.001, fmep_0 0.4, fmep_pmax 0.005, fmep_sp 0.09, fmep_sp2 0.0009, ua_port 50, ve_rpm 1000, ve_width 1000, ve_map 1e-3, ve_cam 1e-3, ce_rich_slope 0.65); `BOUNDS` (plan §5.2, D9); `RIDGE_CENTRE` read from `engines.typed_engine("b58")` at call time, 0 for the B and D terms, 0.65 for C (plan §5.2: the B58's own values, never retyped); `X_SCALE` = `SCALES` (D5); `TOLERANCES` (`ftol`, `xtol`, `gtol`), pinned before commit C above the finite-difference noise measured on synthetic B58 rows, the measurement in the docstring (D5; CLAUDE.md's threshold rule); `MAX_NFEV = 60`, one declared second attempt at 120 from the best iterate (plan §5.6); `SPARK_REF_KPA = 40.0` (DESIGN); `PROVISIONAL_COMPLETION = {"deliverable_torque": [], "k3": {"turb_knee_k": 1123.0}, "loop": {"torque_floor_nm": 0.0}}`. **Chosen here:** a candidate needs every DERIVED field (`build_candidate`), and these three move no row output (no cycle or ECU call reads them); `test_epa_fit` shows two provisional sets give bit-identical row outputs (the control F7 asks for, applied to the fit).

**Records.**

`RowModel(plant, *, fuels)`, picklable: `fuels: Mapping[str, TableFuel]`; one `engines.with_fuel(plant.engine, engines.Fuel(...))` per table (MD §3); methods of §5.2.2. `cycle` runs `plant.run_cycle(Operating(rpm, map_kpa, iat_k, ect_k, spark_btdc, lam, exhaust_backpressure_kpa(map_kpa, engine=e)), engine=e, dtheta=dtheta, cam_deg=BaselineECU(e.ecu).cam_deg(rpm, map_kpa))` (plan §5.1; the cam is `None` unless form D).

`StageResult`: `stage: str`, `values: Mapping[str, float | int | str | tuple]` (Python scalars, B10), `rows_used: int`, `rows_excluded: Mapping[str, tuple[(str, int), ...]]` (reason → keys), `flags: tuple[str, ...]`, `bounds_active: tuple[str, ...]`, `convergence: Convergence | None`, `report: Mapping` (stage-specific, §7.2).

`Convergence`: `nfev`, `njev: int`, `status: int`, `message: str`, `cost`, `grad_norm`, `last_step_norm`, `cost_change: float`, `second_attempt: bool` (mistake 15).

`FormFit`: `engine`, `form: str`, `stages: Mapping[str, StageResult]`, `values: Mapping` (the derived-file shape: `cycle`, `ecu`, `boost_ceiling`; terms the form does not use at their neutral values, plan §5.8), `frozen_sections_sha256: str`, `flags: tuple[str, ...]`.

`Ladder`: `engine`, `fits: tuple[FormFit, ...]`, `in_sample: Mapping[str, epa_stats.InSample]`, `chosen: str`, `reason: str`.

**Functions.**

- `ordered_map(fn, items, *, jobs, initializer) -> list`: a spawn pool, results in submission order, `jobs == 1` in-process; each worker's initializer installs the audit hook (§3.3) and asserts one BLAS thread.
- `cal_rows(yield_) -> tuple[SteadyRow | FinalRow, ...]`: refuses any row whose type is not exactly one of the two.
- `s0(yield_, *, view) -> StageResult` (plan §5.2 S0, C2: on the yield only): the λ-less fired rows by population; fired sentinel rows (a declared outcome, decision 54, never asserted to be zero); `censoring`; TIP below the barometer (count and largest deficit; decision 52), HD1 judged against decision 53's barometer; coolant against oil (mistake 13); meter against injector (mistake 14); the cam channel's sign and range; and the bounds C1 derives (lowest calibration Final MAP, S3b's depth edges, S3d's domain and clamp).
- `s1_backpressure(rows, *, view) -> StageResult`: hinge profiled on a 0.1 kPa grid over the rows' MAP range, r in closed form, floor = r·h; σ for E6 row 5; the residual against rpm reported; decision 52's refit without the TIP-below-barometer rows as a sensitivity.
- `s2_breathing(rows, *, plant, view, form) -> StageResult`: variable projection (`ve_rpm` over the calibration lines × `ve_width` on a log grid 300–20 000), `scipy.optimize.lsq_linear` for base and amp inside the projection (D9), then a `least_squares('trf')` polish with `x_scale` declared (D5); `ve_map` under B, `ve_cam` at the schedule's cam under D; verify `run_cycle(...).mdot_air_gps` = VE·A_r within 1e-12 (mistake 10).
- `s3a_spark(rows, *, plant, view) -> StageResult`: alternating piecewise OLS with D7's minimum row count and rank per piece, starting with the rows below the lowest calibration Final MAP on the plane (C1: S3a's start; **chosen here** over DESIGN 100 kPa, its alternative, since the start is a point of the data the pieces are fitted to); target spark_EPA − `iat_compensation(IMT)` with `cold_retard` added back where it applies (D3's sign); `spark_min = floor(min{spark_EPA, base, base + comp}) − 1` (D3), `spark_max` by the same principle; asserts `BaselineECU.step` at dwell 30 s returns base + comp unclipped at every calibration row (D3's check).
- `s3b_lambda(rows, *, view, censoring, lam_floor) -> StageResult`: calibration Final rows with λ plus steady rows with λ (dwell ≥ 30 s, t = 1, D2); gate grid from the lower of the lowest calibration Final MAP and DESIGN 100 kPa to the largest Final MAP in 1 kPa steps (**chosen here**: C1 names both as the edge's sources and replaces the plan's all-row "hot floor − 20"; the lower of the two leaves room for D2's gate between the steady and the Final rows); ties to the highest gate, the flat width reported; `rpm_lo` may lie below the lowest line; the depth a 1-D convex piecewise-quadratic minimisation (censored rows one-sided; wrong claim 23) bounded by **min(1 − (min over calibration Final λ_cellref − 0.01), 1 − lam_floor)**, built through `build_candidate` so `Engine`'s invariant is checked, and the active edge reported (C1; HO WP3.1; `lam_floor > 0`, P2.4).
- `s3c_envelope(rows, *, view) -> StageResult`: one point per calibration high-load line, its highest-MAP Final row with a meter; corrected flow from `air_cal`, cell temperature and (barometer − 2); PR = MAP/`inlet_sea_kpa`; sorted by flow, strictly increasing asserted (ties refused), anchor (0, 1), flat past the last point; lines without holds give no point and are listed; HD1's barometer the median of the Cell 9 calibration rows' cell pressure, swept over their range (D1, decision 53, C1).
- `s3d_cam(rows, *, view) -> StageResult`: the full quadratic in (rpm/1000, MAP/100) by OLS in `BaselineECU.cam_deg`'s term order, on calibration rows carrying a cam value; domain and clamp from those rows (C1); extrapolated rows flagged (mistake 6); corr(`ve_cam`, `ve_map`) reported (D8).
- `s4_burn(rows, *, name, values, view, form, jobs) -> StageResult`: the nine parameters jointly in trf (D4), outer columns by 0.5 CAD forward difference with the per-row chain rule, FMEP and UA columns analytic; efficiency residual (T_m·F_meter/(T_E·F_m) − 1)/0.019; three starts (the B58's, ×0.8, ×1.2) plus two at ± the weakest direction (D6); residuals per line and per population reported (D13).
- `s5_rich_slope(rows, *, name, values, s4, jobs) -> StageResult`: bounded Brent on [0, 1.5] over enriched hot calibration rows; bound hit and η_comb ≥ 0.5 at the deepest calibration λ flagged (plan §5.3).
- `s6_knock(rows, *, name, values, jobs) -> StageResult`: knock_a ← 0.01768·exp(mean ln KI) over the Final rows, re-run to |mean ln KI| < 1e-12 (decision 51); KI's spread reported.
- `verify(rows, *, name, values, jobs) -> StageResult`: every shortcut equals a direct `run_cycle` within 1e-9 relative; every Jacobian column non-zero at the start values, zero columns at the optimum reported (D10).
- `fit_form(name, yield_, *, view, form, start, jobs) -> FormFit`.
- `ladder(name, yield_, *, view, jobs) -> Ladder`: **per engine** (decision 49; MD §2.4 supersedes plan §5.4's common ladder): A; then A+B from A's solution with the new term at 0; and so on; the first form whose in-sample statistics but E8 pass is chosen; if none, A+B+C+D with its failing statistics; forms after the chosen one are not fitted.
- E6 variants (plan §5.7, E2, E3): `refit_variant(name, yield_, *, view, form, conventions, start, jobs) -> FormFit` (rows 1–3; S1–S6 at the frozen form, no new ladder); `knock_rescale(values, *, factor) -> Mapping` (row 7: knock_a/0.90 and /1.10, exact since KI ∝ 1/knock_a); `perturbed(plant, *, record, field, value) -> engines.Plant` (rows 4, 5, 6, 9, 10); `with_rich_slope_probe(plant, *, slope) -> engines.Plant`, run as form A+B+C at the engine's own breathing terms (HO WP3.3), after `retag_identity(plant, *, grid) -> bool` has shown the retag at 0.65 gives the engine's own doubles bit for bit (asserted, never relaxed).
- `octane_moves_only_knock(plant, *, octane) -> bool` and `FORD_CELL9_OCTANE: str`. **Chosen here** (HO WP3.5): the Ford's Cell 9 rows run at the engine's typed octane (HD1's FTAG 26864). The octane enters the cycle only through the knock delay (`plant.run_cycle`: τ ∝ (octane/100)^knock_on), so it moves only `knock_integral` and `knock_prob`; no Cell 9 row is compared on either (S6 and E6 row 7 use the HD1 Final rows, on that batch). The check is run at the fit and written to `fit_<form>.json` (mistake 24: the explanation names a quantity, so it is measured).
- T0 (plan §5.10, D11, A1): `t0_truths(name, *, view) -> tuple[Truth, ...]` (three seeds: burn ×1.15, delay ×0.9, FMEP ×1.2, UA ×3, VE moved, back-pressure 1.45 and 102 kPa; one seed with `ve_map = 2e-3`; one seed whose truth lies outside the model's form); `t0_rows(yield_, *, truth, seed) -> tuple[SteadyRow | FinalRow, ...]` (the rows' input columns kept, every output replaced from the truth by `run_cycle`, the ECU forms and the law, noise torque 0.5 %, meter 0.5 %, TIT 3 K, spark 0.5°, λ 0.005, from `numpy.random.default_rng([0x70, seed])`, **chosen here**, a labelled stream as the contract's 0xC5 is; `origin = "t0"`); `t0_judge(ladders, truths) -> Mapping` (two-sided χ² with the covariance scaled by the residual variance, per-parameter standardised errors, the ladders' stopping forms, and D1–D3's cases).

### 5.4 `epa_freeze.py`: hashes, the derived file, the freeze record, the dump (plan §5.8, F7)

The token is not here: C3 confines `Token` and `verify_for_validation` to `validate_epa.py` (plan §4.3 and §6.1 put them here; the amendments govern).

- `STEP2_CODE: tuple[str, ...]`: the nine modules; `STEP2_TESTS`: the eleven test files of §9 and `test_epa_fixtures.py`; `CODE_HASHED = STEP2_CODE + ("thresholds/split.py", "thresholds/common.py") + RUN1_INPUTS`, `RUN1_INPUTS = ("evaluate.py", "engine_specs/b58.toml", "requirements-lock.txt")` (24 October 2026, the fourth Run 1 review: the fit reads the B58's spec, the completion reads `evaluate.py`, every subcommand reads the lock file, and none was hashed).
- `write_json_atomic(path, obj) -> str` (returns the sha_text written).
- `code_shas() -> Mapping[str, str]`; `git_head() -> str`; `git_clean(paths) -> (bool, tuple[str, ...])`; `git_blob(path) -> str`; `committed_at_head(path) -> bool`.
- `plant_sha(name) -> str` (§4).
- `data_shas(name, *, source) -> Mapping` (tables raw sha256, equal to the contract's; `epa_engine.json` raw; `epa_channels.csv` git blob; the manifest's sha256).
- `derived_path(name) -> str`: the engine spec's `derived` key, asserted equal to `derived.engine_path(name)`.
- `derived_values(fit, *, provenance) -> dict`: the file's dict (§7.3).
- `derived_record(path) -> DerivedRecord` (`path`, `sha_text`, `derived_sha`), the §4 pair.
- `write_derived(name, values, *, allow_defect) -> DerivedRecord` (`path`, `sha_text`, `derived_sha`); refuses to overwrite frozen sections unless the defect route names a fix commit (plan §5.6).
- `freeze_record(name, *, fit, ladder, files, provenance) -> dict`; `write_freeze(name, record) -> str` (refuses if `freeze.json` exists: a re-freeze is the defect route).
- `check_frozen(name, values) -> None`: `engines.frozen_sections_sha256(values)` equals `freeze.json`'s (plan §5.9 item 10).
- `frozen_plant_dump(plant) -> Dump` (`sha256: str`, `n_values: int`, `keys: tuple[str, ...]`), on synthetic inputs only (plan §5.8): `run_cycle` on 9 speeds over [`rpm_min`, `rpm_max`] × MAP {30, 60, 100, 140, 180, 220} clipped to the calibration range × spark {−5, 5, 15, 25} × λ {max(0.70, `lam_floor`), 0.85, 1.0} × IMT {310, 330} K at ECT 365 K, the in-use fuel, the ECU's cam, the 16 fields of `CycleResult`; `exhaust_backpressure_kpa`; `BaselineECU`'s `base_spark`, `knock_limited_spark`, `base_lambda` at dwell 0, 3 and 30 s, `iat_compensation` and `cam_deg` on an (rpm, MAP) grid; `boost_ceiling_kpa` on a flow grid; `charge_temperature`; the vehicle's `road_force_n` and `demand` on a (v, a, grade) grid; a fixed `ThermalNetwork` sequence (**chosen here**: 600 steps of fixed inputs, since the certificate harness's own sequence lives in an archive the code may not import).
- `provenance(name, *, source, view) -> dict` (§7.1).

### 5.5 `calibrate_epa.py`: the entry point (JSON `order_of_work[1]`; plan §2 WP4, §5; C3, C6, C8, C10, C11, C13)

**5.5.1 The command line.** `--engine` and `--jobs` are required; there is no default engine or job count (mistake 1).

```
python -B calibrate_epa.py dry-load --engine <id> --out <scratch>
python -B calibrate_epa.py t0       --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]
python -B calibrate_epa.py fit      --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]
python -B calibrate_epa.py poison   --engine <id> --jobs <n> --scratch <dir> [--full]
python -B calibrate_epa.py e6       --engine <id> --jobs <n>
python -B calibrate_epa.py complete --engine <id> --jobs <n>
python -B calibrate_epa.py check    --engine <id> --jobs <n> [--defect "<reason>" --fix-commit <sha>]
```

Exit codes: 0 ok, 1 crash, 2 refused, 3 an audit defect, 4 Run 1 waits, 5 check's mismatch (`validate_epa.CHECK_EXITS` reads them by name). **The Run 1 gate** (23 October 2026, amended; repinned to version 5 the same day): while the contract holds a Run 1 rule (`epa_rows.run1_wait`, which fails closed: the commit `epa_rows` pins, `CONTRACT_COMMIT`, always holds it, with the text `RUN1_PINNED_COMMIT`, and so does any `open_for_the_team` entry naming Run 1, as version 5's entries 0 and 3 do; so the gate still holds under version 5, and Ghassan's go-ahead is given as the switch), the first evaluation at an EPA row's inputs waits -- `dry-load`, and `t0` or `fit` while `STARTED` is absent -- unless `EPA_RUN1_GO` names the engine (`EPA_RUN1_GO=<id>` or a comma-separated list); every later subcommand builds on a run that started and is not gated. The rule's text and the switch are recorded in `STARTED` and in every `run.json` entry.

| subcommand | does | requires | writes |
|---|---|---|---|
| `dry-load` | loads the view and the yield, no model evaluation (plan §4.6 item 8) | `--out` outside the work tree (else refused, nothing written) | `<scratch>/run.json` only |
| `t0` | T0 at the calibration rows' inputs (A1: its own step on committed code); `--defect` moves a failed T0 to `defect_<k>/` and re-runs it on the fix, and is refused once a fit has run (its route is then `fit --defect`) | a clean tree, the plant's code and specs included (`epa_freeze.plant_files`); every pin set, every engine's D3 summary columns among them (`epa_stats.unpinned_u_d`, `d3_rows.unpinned_for`: the code is shared); no audited defect or crash in `run.json` (unless the defect route); no held-out run started | `STARTED` (if absent), `t0.json`, `run.json` |
| `fit` | S0, the ladder (S1–S6, verify, in-sample per form), the freeze; `--defect` moves the run to `defect_<k>/` and re-runs from T0 | `t0.json` passed; `STARTED` absent or written by `t0`; no `freeze.json` (unless the defect route); a clean tree and plant; every pin set; no held-out run started | `STARTED`, `stage0.json`, `fit_<form>.json` per form fitted, `in_sample.json`, the derived file's frozen sections, `freeze.json`, `run.json` |
| `poison` | C8, mandatory: the yield, the view, the manifest, `engine_facts` and S0–S3d and S6 on held-out cells poisoned three ways (the copies shown not to be the tables, the real tables unreadable while the poisoned stages run, the reference tied to the fit's recorded S1 and S3a–S3c); with `--full` (mandatory on `mazda_25t`), the whole form-A fit | `freeze.json`; the step-2 code and the plant committed, clean and freeze.json's (`code`, `plant_sha`); `--scratch` outside the work tree; no audited defect in `run.json`; no held-out run started | `poison.json`, `run.json` |
| `e6` | the refit variants rows 1, 2, 3 (the frozen form's own fit re-run as the ladder ran it) and 7 (plan §5.7) | `freeze.json`; the code and the plant freeze.json's, committed and clean; `poison.json` the proof (`epa_freeze.poison_problems`); no audited defect; no held-out run started | `e6/row1.json`, `row2.json`, `row3.json`, `row7_090.json`, `row7_110.json`, `run.json` |
| `complete` | plan §5.9 items 1–10, in a fresh process with `DERIVING_PARAMS=1` set before any project import (`derived.py`'s docstring) | the five `e6` files; the code and the plant freeze.json's, committed and clean; `poison.json` the proof; no audited defect; no held-out run started | the derived file's completion sections, `complete.json`, `run.json` |
| `check` | recomputes the in-sample stage in memory and compares `in_sample.json` (or the latest `in_sample_rerun<k>.json`) and the frozen sections byte for byte (plan §6.1); `--defect` writes `in_sample_rerun<k>.json` (C11) | `complete.json`; no audited defect | `run.json` only (and the re-run file) |

**Chosen here:** `t0`, `poison` and `dry-load` are subcommands beside the four the plan names (wrong claim 7): T0 is a step on committed code (A1), C8's poison fit is mandatory in Run 1, and the runtime audit needs a command that loads without evaluating (plan §4.6 item 8). **Chosen here:** the full form-A poison fit runs on `mazda_25t`, the engine the drop order keeps last (MD §7), so the most consequential calibration carries the strongest proof. The three poisons write every non-provenance cell of every held-out row as `-1e+06`, `1e+06` and the empty string, with `csv.writer` (DESIGN extremes, finite, far outside any channel's range without reading one: C8).

Completion order (plan §5.9 as F7, F8, E1, E3, F3, F5 amend it): finiteness asserted before each step except the named completion fields still to come; (1) the deliverable-torque table, re-measured at 60 settling steps, the knock-flag duty, the descriptive comparison with the calibration High Load Initial torque, labelled transient (C7); (2) the torque floor; (3) the delivery check on the locked climb with a provisional knee, steps t ≥ 188 s, `e_track` against `TRACK_TOL` (F8), the gear or ratio, rpm, demand and the margins to `shift_ceiling_nm` or the kickdown threshold and to the `SHIFT_RPM_MAX` bar (F3, decision 44), and **the neutral-action identity** (E1, decision 39(b); `k3_knee.neutral_identity`); (4) the K3 knee, re-run under a second provisional knee bit-identical, and at η 0.86 and 0.98 (decision 44); the control that the table and the floor are bit-identical under two provisional knees (F7); (5) the engine's own coefficients (`epa_coefficients`); (6) the E6 probe sizes (level rows by the R1 consequence, d rows ±10 %, row 9 by bracket, then probe, then ±10 CAD, each unreachable bracket with its reason: E3, decision 59); (7) row 4; (8) row 7 at KI 1.00, 0.90, 1.10, both readings; (9) row 13's variants; (10) the frozen-plant dump and the final derived file, the frozen sections asserted unchanged.

**5.5.2 Records each subcommand leaves.** `STARTED` is written atomically before the first model evaluation at an EPA row's inputs, by `t0` or `fit`, whichever runs first, and is never rewritten (MD §13 "What is open": a crashed fit leaves it, so the claims that no fit has run can require it absent). `run.json` gets one entry per invocation, refused ones included. A coding defect (plan §5.6) moves the whole engine folder's outputs, verbatim, to `results/EPA_CALIBRATION/<id>/defect_<k>/` and appends to `defects.json` (no wall-clock date: the entry names its `run.json` invocation); the fix is committed and the calibration re-runs from T0 with `fit --defect "<reason>" --fix-commit <sha>` (or `t0 --defect` for a T0 failure) (plan §5.6; C10). Once `results/EPA_VALIDATION/<id>/` holds anything but ARMED.json, on the disk or in `git log --all`, `t0`, `fit` (its defect route included), `poison`, `e6` and `complete` refuse (MD §7: no refit after any held-out statistic; `epa_freeze.held_out_started`). An arm-guard failure after the roads step repeats Run 1 from S0; an `epa_stats` defect found after the held-out run recomputes `in_sample.json` beside the old one as `in_sample_rerun<k>.json`, re-makes ARMED.json and refits nothing (C11).

**5.5.3 Public functions** (each subcommand is a function the CLI calls; the tests call them on temporary repositories; each returns the dict `run.json` records as its `result`): `dry_load(name, *, source, out)`, `t0(name, *, source, jobs, defect)`, `fit(name, *, source, jobs, defect)`, `poison(name, *, source, jobs, scratch, full)`, `e6(name, *, source, jobs)`, `complete(name, *, source, jobs)`, `check(name, *, source, jobs, defect)` (a failed comparison raises `CheckFailed`, exit 5); `invoke(subcommand, name, *, source, argv, body, scratch, audit) -> int`; `install_audit(*, subcommand, engine, root, scratch) -> Audit`; `worker_init(subcommand, engine, root, scratch, paths) -> None` (the pool initializer); `run1_waits(*, source, environ, engine)`, `gated(subcommand, name, *, source)`; `SEEN_BEFORE_THE_FIT: tuple[str, ...]` (C13): P2's implementer's read of MD:789-797; P7's prints of MD:755, :789-797 and `thresholds/contract.py:440-447` (HO WP3.2, HO P7.3); the plan's TIP-below-barometer boolean and its all-row channel ranges (C13; wrong claims 11, 16); the contract's own all-row TIT ranges (the amendments' disclosure); the end lines cited to JSON `lines` (C13); WP3's header reads (§5.1); and this file's reads (§1.2). Each entry names what was seen and where, and repeats no value.

**5.5.4 The audit allowlists.** Every subcommand may open the Python installation's files, the repository's `*.py` and `__pycache__`, `engine_specs/*.toml`, `engine_specs/cars/*.toml`, `thresholds/*.py`, `engine_thresholds.py` (hashing only), the contract's two files and `results/ENGINE_THRESHOLDS/ecu/k3_nominal.json`, `os.devnull`, and the B58's derived file `data/derived_params.json` (`derived.B58_PATH`), read only: the project's import chain reads it (engines → derived.py) before the subcommand starts (added 23 October 2026: with the audit installed before the imports, as the command line installs it, every subcommand was otherwise a defect). Then:

| subcommand | also | |
|---|---|---|
| `dry-load` | the engine's own tables and `epa_engine.json`; `<scratch>/` | |
| `t0`, `fit`, `e6`, `check` | the same; `results/EPA_CALIBRATION/<id>/**`; `data/engines/<id>/derived_params.json` | |
| `poison` | the same; `<scratch>/**` (the poisoned copies and the garbled contract) | |
| `complete` | the same as `fit` (the tables for C7's comparison and row 9's valve brackets, calibration rows only) | |

### 5.6 `k3_knee.py`: the K3 knee and the neutral run (plan §5.9 items 3–4, §7.7; decision 33; E1; F8)

Lifted from `thresholds/ecu_shift.py:80-101`, which stays untouched because JSON `generators` pins it.

- `baseline_trace(plant) -> BaselineTrace` (`t_turb_k`, `lam`, `spark: np.ndarray`): frozen episode 1, `evaluate.episode_cycle(None, plant=plant)`, `evaluate.DT`, the neutral action, exactly as `ecu_shift.one.baseline_trace`.
- `knee_for(trace, seconds) -> float`: the midpoint of the `seconds`-th and next highest values, as `ecu_shift.py:93-97`.
- `with_knee(plant, knee_k) -> engines.Plant`.
- `shifted_ecu(ds, dl)`: a context manager patching `engine_env.BaselineECU.step` exactly as `ecu_shift.py:70-78` (above `ECU_LOAD_KPA`, imported) and restoring it.
- `k3(plant, *, seconds, provisional) -> K3` (`knee_k`, `time_above_knee_s`, `trace_sha256: str`, `second_knee_identical: bool`).
- `NeutralRun`: per-step arrays `t`, `t_turb_k`, `lam`, `spark`, `lam_b`, `spark_b`, `act` (n × 5, float32), `torque`, `torque_req`, `e_track`, `rpm`, `map_kpa`, `held` (gear or CVT branch), `ceiling_kpa`.
- `neutral_run(plant, *, cycle, seed, weights) -> NeutralRun`: records `lam_b`, `spark_b` by wrapping the environment's own `BaselineECU` **instance**'s `step` (an instance attribute; no class or file is edited, B5), and `act` from `env.prev_act` after each step.
- `neutral_identity(run, *, ecu) -> Identity` (`max_abs_dlam`, `max_abs_dspark: float`, `contacts_lam`, `contacts_spark: int`, `bounds_are_python_floats: bool`, `steps: int`): λ = float32(λ_b) and spark = float32(spark_b) at every step; a contact is `np.clip(x, lo, hi) != x` on the float32 sums against the four bounds, compared in float32 as the environment compares; the four bounds asserted `type(x) is float` first (MD §4, decision 39(b), HO WP2.2). A difference or a contact is a coding defect (MD §7).
- `delivery(run, *, plant, t_from_s) -> Delivery` (`share_over_track_tol`, `largest_shortfall_nm`, `held`, `rpm`, `demand_nm`, `margin_to_threshold`, `bar_rpm_margin`, `map_vs_ceiling_kpa`): t_from_s 188 (F8).
- `with_driveline_eff(plant, eta) -> engines.Plant` (decision 44's η sensitivity).

### 5.7 `epa_coefficients.py`: an engine's own coefficients, descriptive (plan §5.9 item 5; MD §1.4; F5; HO WP3.4)

`thresholds/b58_propagation.py:43-155` as functions of any plant; it never moves an R (MD §1.4).

- `cyc(plant, rpm, map_kpa, iat_k, ect_k, spark, lam) -> Mapping` — with the ECU's cam, `BaselineECU(plant.engine.ecu).cam_deg(rpm, map_kpa)` (HO WP3.4).
- `run_climb(plant, *, bias) -> (list[Mapping], Mapping)` — `make_grade_climb(duration=evaluate.DURATION, dt=evaluate.DT, t_amb=plant.scenario.t_amb, grade=plant.scenario.grade, v_kmh=plant.scenario.v_kmh)` (F5).
- `median_point(rec, t0, t1) -> Mapping`; `housing(plant, egt_c, mdot_gps, *, t_amb_c) -> Mapping`; `chain(plant, point, hs, dsp) -> (Mapping, Mapping)`; `partials(plant, point, hs) -> Mapping`.
- `coefficients(plant) -> Mapping`: `b58_propagation.compute()`'s structure.
- Constants `CLIMB_S = (400, 718)`, `FLAT_S = (100, 179)`, `H_KPA = 2.0`.

**Chosen here (F5).** The climb's ambient is the plant's own (`plant.scenario.t_amb`, 315 K on the B58), and the housing's G reference stays the contract's 42 °C (`thresholds.contract.T_AMB_C`, the "42C" of `propagation_b58.G_gas_over_42C_k`). On the B58 the two are 315.0 K and 42.0 °C, which `b58_propagation.py` types separately (`:40`, `:60`), so the lifted code gives `b58_propagation.json` back bit for bit; a plant with another scenario ambient moves the climb, which is F5's test.

### 5.8 `validate_epa.py`: the held-out validation, run once (plan §6; C2, C5, C6, C10, C11, E5–E7; decisions 54, 57–60, 63, 64, 71)

**5.8.1 The command line.**

```
python -B validate_epa.py arm     --engine <id> --jobs <n> [--defect-rerun "<reason>" --fix-commit <sha>]
python -B validate_epa.py run     --engine <id> --jobs <n> [--defect-rerun "<reason>" --fix-commit <sha>]
python -B validate_epa.py summary
```

**5.8.2 `arm(name, *, source) -> Mapping`** checks, prints counts only, and writes `results/EPA_VALIDATION/<id>/ARMED.json` (§7.9); the person commits it, and that commit is the arming (plan §6.1):

- `freeze.json` and `complete.json` committed and clean; the derived file's sha_text and `derived_sha`, the engine, car and published-car files' sha_text, and `engines.engine_sha(engines.get(name))` equal the recorded values;
- the frozen-plant dump recomputed now is bit-identical (`epa_freeze.frozen_plant_dump`);
- `calibrate_epa.py check --engine <id> --jobs <n>` run as a subprocess exits 0 (the in-sample stage given back byte for byte); its exit read by name (`CHECK_EXITS`): only a mismatch (5) is C11's "repeat Run 1 from S0", a crash, a refusal, an audit defect or a wait is named as what it is;
- Run 1's proofs (23 October 2026): `t0.json` passed, `poison.json` C8's proof at the frozen sections (the full form-A fit on `mazda_25t`; `epa_freeze.poison_problems`), and `run.json` committed with no invocation the audit judged a defect, a crash or a mismatch (`epa_freeze.audit_problems`); every u_D term a gating row reads and the engine's D3 summary columns pinned (`arm/pins`);
- on the defect route, freeze.json, complete.json, the derived file, `engine_sha` and the dump equal the previous ARMED.json's (`arm/rearm`; C11: nothing is refitted; only `in_sample_rerun<k>.json` and the fixed code may differ);
- the contract's sha_text equals the freeze's; the code's sha_text equals `freeze.json`'s, or each change since `fit_A.json`'s `git_head` is listed with its `defects.json` entry (C10);
- `results/EPA_TIGHTENINGS.json` committed, its `plant` equal to `"b58"` (decision 71, E5) and its shift grids equal to the contract's (§7.5);
- the 43 D3 files' raw sha256 equal JSON `d3_files_c3` and the data folder's `MANIFEST.csv`; the D3 summary workbook and the Accord's D3 files hashed against `MANIFEST.csv` (decision 63);
- no `rows.json` for this engine in the tree or in `git log --all`;
- the populations reproduce JSON `per_held_out_line`, `deciding_lines` and `pooled_counts` through `split.compute()` (structure only; C2);
- `epa_rows.held_out_counts`: the fired held-out rows without λ and with the sentinel are counted, and whether each of E8's subsets holds `e8_min_rows` rows is decided here (MD §3, §4). A fired sentinel row is a declared outcome, never a stop (decision 54 supersedes plan §6.1's "stops here").

**5.8.3 `Token`**: `engine: str`, `armed_blob: str`, `head: str`, `root: str`. **`verify_for_validation(name, *, source) -> Token`** issues it only after `refusals` is empty.

**5.8.4 `refusals(name, *, source, defect) -> tuple[str, ...]`** (C6): in a linked worktree (`git rev-parse --git-dir` ≠ `--git-common-dir`); without `.git`; outside the path ARMED.json records; unless the output folder holds ARMED.json alone, counting tracked, untracked and ignored files; if `git log --all` holds any other path under that folder; unless ARMED.json is committed at HEAD with matching hashes and the validation code is clean; unless the arming's nonce, written into the work tree's own git directory and hashed in ARMED.json, is there (a clone or copy of the armed commit holds none); and, on the normal route, when the invocation log (outside the folder) records this arming's start while the folder holds no STARTED (23 October 2026). On the defect route the folder must hold exactly the first run's outputs and its crash records, and the fix commit must descend from the armed commit (plan §6.1).

**5.8.5 `run(name, *, source, jobs, defect) -> Mapping`**: `warnings.simplefilter("error")` (C6: warnings are errors), in every spawn worker too (`worker_audit`); the token; **STARTED written atomically before the first held-out read**, and the start appended to the invocation log; `epa_rows.read_held_out`; the frozen plant, the E6 variant plants (rows 1, 2, 3 and 7 by `engines.build_candidate` from each `e6/row*.json`'s frozen sections with the frozen plant's completion sections; rows 5, 6, 9 and 11 by `epa_fit.perturbed` and `with_rich_slope_probe`, with σ from `fit_<form>.json` and the probe sizes from `complete.json`), the tightenings; every row of §8 with its u-terms, labels, κ and coverage flags; E6 in the same single run (plan §6.4); C3 (Mazda) or C4's Accord chain (Honda) through `d3_rows`; then `rows.json`, `e6.json`, `c3.json` or `c4_accord.json`, and `run.json` last. It prints counts and paths only; no statistic reaches a screen before the file holding it exists. An exception writes `crash_<k>.txt` (it counts as written) and prints only the exception's type. Before the first output is written, `run` writes the run-once marker `epa_writing_<id>_<blob>` and a "writing" event in the invocation log (24 October 2026, the fourth isolation review: a run killed after `rows.json` was written, the folder cut back to STARTED alone, otherwise ran again on the normal route); either refuses the normal route, and a re-run's own refuses that re-run. Re-execution is allowed only when STARTED is the only record and nothing was being written; otherwise only the defect route runs, writing `rows_rerun<k>.json` beside the first and capping that re-run's labels at limited (MD §7; plan §6.1). The audit hook runs in record mode (§3.3) with an allowlist that adds the engine's tables, the D3 files of ARMED.json, and `results/EPA_VALIDATION/<id>/**`.

**5.8.6 `summary(*, source) -> Mapping`** writes `results/EPA_VALIDATION/summary.json` (§7.13) from the three `rows.json`.

**5.8.7 Helpers.** `load_tightenings(path) -> Tightenings` with `TIGHTENINGS_KEYS` (plan §2 WP5, fixed now: `roads_sha`, `roads_seed`, `plant`, `L1.slope_points_per_K` with its set, shift and damage reading, `E8.k3_pair_change_vs_lambda_roads` and `E8.k3_pair_change_vs_spark_roads` in `ecu_strategy_b58`'s format, the provenance hashes); `e6_rows(...) -> Mapping` (§8's E6 lines); `c5_recheck_margin(e1a) -> Mapping` (decision 64: the worst deciding line's |E1a| + 2u_val, every line's beside it).

### 5.9 `d3_rows.py`: C3 and C4 (MD §5; plan §6.5; decision 63; C5)

Tested on synthetic traces only; its first real read is inside `validate_epa.py run` (MD:451; C5). It opens only the paths it is given.

- `D3_DIALECT`: tab-delimited text, one header row, each channel's unit in brackets after its name. **Chosen here** from the contract's own channel names (`Dyno_TractiveForce[N]`, MD §5) and the files' names in `MANIFEST.csv` (`<test> Test Data.txt`); no D3 file was opened. A header without every channel of `CHANNELS`, or with one twice, stops `run` before any value is converted (a coding defect, recorded as a crash).
- `CHANNELS`: the names MD §5 gives (`Dyno_TractiveForce[N]`, `Trans_gear_actual_CAN[]`, `Eng_speed_CAN`, `Trans_turbine_shaft_speed_TCM`, `HVAC_ACComp_cycling_switch_PCM`, `Eng_ManifoldAir_pressure_sensor_PCM[kPa]`, `Eng_FuelFlow_Direct2[gps]`, `Eng_mass_air_flow_PCM[gps]`, `Eng_equiv_ratio_b1_s1_PCM[]`), each matched as `name` or `name[unit]`; the time, road-speed and coolant channels, which MD §5 does not name, are pinned before commit C from `CATALOGUE.md`'s D3 section or Argonne's documentation, never from a D3 file, and the read is entered in `SEEN_BEFORE_THE_FIT`. `Eng_FuelFlow_Direct[ccps]` is never read (mistake 7).
- `Trace`: `test: str`, `t_s: np.ndarray` and one array per channel; `read_trace(path, *, test) -> Trace` drops every row after the first occurrence of the maximum time (the padding rows, MD §5).
- `SegmentRules`: `min_s = 3.0`, `rpm_band = 25.0`, `map_refreshes = 2`, `converter_ratio = 0.01`, `ac_off = True`, `one_gear = True`, `coolant_min_c = 83.8` (MD §5: every window in seconds, mistakes 8, 13b). `CONTRACT_SEGMENTS = SegmentRules(...)` holds the contract's values.
- `Segment`: `test`, `t0_s`, `t1_s`, `n`, `gear`, `rpm_mean`, `pcm_map_kpa_mean`, `force_n_mean`, `direct2_gps_mean`, `maf_gps_mean`, `equiv_ratio_mean`, `coolant_c_min`, `map_refreshes`.
- `segments(trace, *, rules) -> tuple[Segment, ...]`.
- `read_summary(path) -> Mapping[str, SummaryRow]`: the summary workbook through `zipfile` and `xml.etree` (the standard library, as `epa_map.py` reads its workbooks, never importing it, C3); its column names pinned as `CHANNELS` are.
- `channel_checks(traces, summary, *, afr_st) -> ChannelChecks`: Direct2's integral against the summary's modal fuel (into u_D); the MAF against Direct2 × AFR_st × 1/equivalence ratio on closed-loop segments, |r̃ − 1| into u_D, flat maxima dropped (mistake 7); the PCM MAP below barometric at closed throttle (mistake 2).
- `demand_torque(seg, *, car, eta) -> float`: `Dyno_TractiveForce` × r_N/V ÷ (gear × final drive) ÷ η; the Accord's ratio from engine and wheel speed.
- `c3_task(seg) -> D1-style task` and `c3_rows(evals, *, view, u_input) -> Mapping[str, StatResult]`: C3a and C3c descriptive, C3b and C3d at 16.6 % deciding with ≥ 3 segments and 2u_stat ≤ R; hot = PCM MAP ≥ the Mazda's hot floor (data, not the model's MAP); fired = demand ≥ 2 bar; segments with a modelled charge outside the Mazda's EPA intake range reported apart; the model's fuel × 18 447/18 659; u_input 5.25 % common (MD §5).
- `c4_accord(evals, *, view) -> Mapping`: the same chain, descriptive (MD §5 C4).

## 6. Where everything is written

| path | written by | committed in |
|---|---|---|
| `results/EPA_CALIBRATION/<id>/STARTED` | `t0` or `fit` | commit D |
| `results/EPA_CALIBRATION/<id>/t0.json`, `stage0.json`, `fit_<form>.json`, `in_sample.json`, `freeze.json`, `poison.json`, `e6/row{1,2,3,7_090,7_110}.json`, `complete.json`, `run.json`, `defects.json`, `defect_<k>/` | `calibrate_epa.py` | commit D |
| `data/engines/<id>/derived_params.json` | `calibrate_epa.py fit` (frozen sections), `complete` (completion sections) | commit D (CLAUDE.md: never by hand) |
| `results/EPA_VALIDATION/<id>/ARMED.json` | `validate_epa.py arm` | commit E |
| `results/EPA_VALIDATION/<id>/STARTED`, `rows.json`, `e6.json`, `c3.json` or `c4_accord.json`, `run.json`, `crash_<k>.txt`, `rows_rerun<k>.json` | `validate_epa.py run` | commit F |
| `results/EPA_VALIDATION/summary.json` | `validate_epa.py summary` | commit F |

`<form>` is the form's tag as `engines.CYCLE_FORMS` writes it (`A`, `A+B`, `A+B+C`, `A+B+C+D`).

## 7. The JSON layouts

Every key is listed; a `schema` string names each layout's version. Values are Python floats, ints, strings, booleans, lists and dicts; `null` for absent.

### 7.1 `provenance`, in every output of both scripts

- `engine` (str)
- `contract`: `commit`, `json_sha_text`, `md_sha_text` (str), `schema` (int)
- `git`: `head` (str), `step2_clean` (bool), `dirty` (list of paths)
- `code_sha_text`: {path: sha_text} over `epa_freeze.CODE_HASHED`
- `plant_sha` (str)
- `data`: `tables_sha256` ({name: hex}), `epa_engine_sha256`, `epa_channels_blob`, `manifest_sha256` (str)
- `view_sha256` (str)
- `versions`: `python`, `numpy`, `scipy`, `platform` (str)

### 7.2 Calibration (`results/EPA_CALIBRATION/<id>/`)

**`STARTED`** (JSON): `engine`, `first_subcommand`, `git_head`, `contract_commit`, `view_sha256` (str), `code_sha_text` ({path: sha_text}), `run1_gate` ({`rule` (str or null), `switch` (str or null)}).

**`stage0.json`**:
- `schema`: `"epa-stage0/1"`; `provenance`
- `yield`: `tables` ({name: {`role`, `rows`, `calibration`, `held_out_skipped`}}), `yield_sha256`, `manifest_sha256`, `initial_final_ids_identical` (bool)
- `checks`:
  - `lambda_missing`: `fired`, `fired_meter`, `hot` (int), `keys` ([[table, row]])
  - `spark_sentinel`: `sentinel_value`, `empty_cell`, `fired` (int), `keys`
  - `censoring`: `final_rows_with_lambda` (int), `min_lambda_cellref` (float), `n_at_min_within_1e-9` (int), `censored` (bool), `documented_floor` (null), `rule` (str)
  - `tip_below_barometer`: `fired_rows_with_barometer`, `below` (int), `largest_deficit_kpa` (float or null), `keys`, `hd1_barometer`: {`median_kpa`, `sweep_kpa` [lo, hi], `from_rows` (int)}
  - `coolant_vs_oil`: {table: {`rows`, `identical` (int), `all_identical` (bool)}}
  - `meter_vs_injector`: {table: {`n` (int), `median_ratio`, `p10`, `p90` (float)}}
  - `cam`: `channel` (str or null), `direction` (`"ret"`, `"adv"` or null), `rows_with_cam`, `rows_without` (int), `rpm_range`, `map_range_kpa`, `cam_range_cad` ([lo, hi] or null), `median_cad`
  - `bounds`: `lowest_final_map_kpa`, `s3a_start_map_kpa`, `s3b_gate_lo_kpa`, `s3b_depth_upper_c1`, `s3b_depth_upper_invariant`, `s3b_depth_upper` (float), `s3b_edge_active` (`"C1"` or `"invariant"`), `s3d_domain` ({`rpm`, `map_kpa`}), `s3d_clamp_cad`
- `seen_before_the_fit` (list of str)
- `declarations`: `ford_cell9_octane` (str or null), `hd1_barometer` (str or null), `spark_ref_kpa` ({`value`: 40.0, `label`: `"DESIGN"`}), `provisional_completion` (the dict of §5.3)

**`t0.json`**: `schema` `"epa-t0/1"`; `provenance`; `seeds`: [{`seed` (int), `truth` (dict), `ladder_stops_at` (str), `expected_form` (str), `judged_at` (str), `reached_expected_form`, `stopped_at_expected_form`, `stopped_beyond_expected_form` (bool), `within_noise` ({`ok`, `beyond`, `z`, `by_row`}), `chi2`: {`params` (list), `value`, `dof`, `quantile_99_lo`, `quantile_99_hi` (null when empty), `empty`, `ok`}, `z` ({param: float}), `ok`}]; `out_of_form_seed` (same shape); `out_of_form_detected`; `chi2_empty_seeds` (list); `cases`: {`d1_envelope`, `d2_gate`, `d3_spark_min`, `s1_law`: {`ok` (bool), `detail` (dict)}}; `stop_rule` ({`z`, `rule`, `on_sampling_failure`}); `ladders`; `pass` (bool). **T0's stop rule is PLAN.md 5.10's** (restored 23 October 2026 by the second fix, on the fit review's must-fix; the first fix's "reached the form, within R + z u_stat there" was this file's own change, which no amendment authorised): an in-form seed passes only when its ladder chose the truth's form and the chi-square there lies within its 99 %; `within_noise` and `stopped_beyond_expected_form` are diagnostics beside it; a chi-square over no parameter is empty, fails the seed, is never a detection, and fails T0. The fit review found the real ladder on synthetic rows climbing a form-A truth to A+B+C+D on an in-sample E4b that sampling error pushes past R: a contract question for the team before Run 1 (§11). A T0 failure traced to sampling stops Run 1 for the engine; the seeds are never changed after a result; the team decides, in `defects.json`, and any further seeds are `T0_STREAM`'s next ones in order (`T0_ON_SAMPLING_FAILURE`).

**`fit_<form>.json`**:
- `schema` `"epa-fit/1"`; `provenance` (in `fit_A.json` this is C10's record of the code at the first fit)
- `form`; `start`: {`from` (`"B58"` or a form), `values_sha256`}
- `settings`: `ridge_w`, `ridge_centre`, `ridge_scale`, `bounds`, `starts`, `x_scale`, `ftol`, `xtol`, `gtol`, `max_nfev`, `second_attempt_nfev`, `dtheta_deg`, `jobs`
- `stages`: {`S1`, `S2`, `S3a`, `S3b`, `S3c`, `S3d` (form D), `S4`, `S5` (form C), `S6`, `verify`}: each {`values`, `rows_used`, `rows_excluded` ({reason: keys}), `flags`, `bounds_active`, `convergence` ({`nfev`, `njev`, `status`, `message`, `cost`, `grad_norm`, `last_step_norm`, `cost_change`, `second_attempt`} or null), `report`}, where `report` holds:
  - `S1`: `hinge_kpa`, `ratio`, `floor_kpa`, `sigma` ({`ratio`, `floor_kpa`}), `residual_vs_rpm` ({`slope_k_per_krpm`, `n`}), `without_tip_below_barometer` ({`values`, `rows_removed`})
  - `S2`: `grid` ({`ve_rpm`, `ve_width`}), `profile_min_cost`, `verify_max_rel`, `clip_rows`, `corr_ve_cam_ve_map`
  - `S3a`: `iterations`, `converged`, `pieces` ({`part_load`, `knock_limited`: {`n`, `rank`}}), `spark_min_rule`, `spark_max_rule`, `unclipped_at_every_row`, `cold_rows`
  - `S3b`: `grid` ({`gate_lo_kpa`, `gate_hi_kpa`, `step_kpa`, `rpm_breakpoints`}), `flat_width_kpa`, `tie_rule`, `rows_behind` ({constant: int}), `censored_rows`, `steady_rows`, `depth_edge` ({`c1`, `invariant`, `active`}), `bounds_active_on_grid`, `steady_hot_rows_enriched`
  - `S3c`: `points` ([{`line`, `key`, `corrected_flow`, `pr`}]), `lines_without_holds`, `anchor`, `pr_cap`, `hd1_barometer`
  - `S3d`: `domain`, `clamp_cad`, `rows`, `empty_cells`, `extrapolated_rows`, `term_order`
  - `S4`: `starts`, `best_start`, `weakest_direction` ({`vector`, `sd`, `ki_at_climb_cell`, `lambda_lever`}), `condition_number`, `correlations`, `data_or_prior` ({param: label}), `residuals` ({`by_line`, `by_population`}), `physical_checks`
  - `S5`: `slope`, `bound_hit`, `eta_comb_at_deepest_lambda`, `rows`
  - `S6`: `knock_a`, `mean_ln_ki`, `ki_spread` ({`min`, `p50`, `max`}), `rows`
  - `verify`: `max_rel_shortcut`, `nonzero_columns_at_start`, `zero_columns_at_optimum`
- `values` ({`cycle`, `ecu`, `boost_ceiling`}); `frozen_sections_sha256`
- `declarations`: `octane_moves_only_knock` (bool), `ford_cell9_octane` (str or null)
- `flags` (plan §5.6's pre-declared outcomes)

**`in_sample.json`**: `schema` `"epa-in-sample/1"`; `provenance`; `criterion` (str, `model_form.in_sample_rules`); `forms`: {form: {`statistics`: {row: in-sample StatResult (§7.6)}, `passes` (bool), `failing`, `no_line` (lists), `e8` (the E8 result, reported)}}; `chosen_form`; `reason`.

**`freeze.json`** (the keys `engines._check_freeze` reads are top-level): `schema` `"epa-freeze/1"`; `form`; `frozen_sections_sha256`; `derived` ({`path`, `sha_text`, `derived_sha`}); `contract` ({`commit`, `json_sha_text`, `md_sha_text`}); `data` (as §7.1); `code` ({path: sha_text}); `plant` ({`plant_sha`}); `fits` ({`stage0.json`, `fit_<form>.json` …, `in_sample.json`: sha_text}); `versions`; `git_head`; since the second fix `flags` (the chosen fit's) and `all_row_depth_edge` ({`active`, `flag`, `why`}: S3b's depth set by `1 - lam_floor`, an all-row quantity, FS4), which ARMED.json carries as `fit_flags` and `all_row_depth_edge`.

**`poison.json`**: `schema` `"epa-poison/1"`; `provenance`; `runs`: {`low`, `high`, `blank`: {`copies_are_not_the_tables`, `stage0_equal`, `view_equal`, `yield_equal`, `manifest_equal`, `engine_facts_equal` (bool), `stages` ({`S0`, `S1`, `S2`, `S3a`, `S3b`, `S3c`, `S3d`, `S6`: bool}), `full_form_a` ({`frozen_sections_sha256_equal`: bool} or null)}}; `frozen_sections_sha256`; `form`; `reference_equals_fit` ({`S1`, `S3a`, `S3b`, `S3c` (and `S3d` under D): bool}); `garbled_contract_view_equal`, `garbled_contract_yield_equal`, `all_equal` (bool).

**`e6/row<n>.json`**: `schema` `"epa-e6/1"`; `provenance`; `row` (int); `variant` (`"1"`, `"2"`, `"3"`, `"7_090"`, `"7_110"`); `conventions` ({`snap`, `cell_referenced`, `afr_st`, `lhv_j_per_kg`}) or `knock_factor` (float); `form`; `values` ({`cycle`, `ecu`, `boost_ceiling`}); `frozen_sections_sha256`; `fit` (the stages as in `fit_<form>.json`, or null for row 7's rescale).

**`complete.json`**: `schema` `"epa-complete/1"`; `provenance`; `frozen_sections_sha256` (asserted unchanged); `deliverable_torque` ({`table` [[rpm, Nm]], `grid` ({`lo`, `hi`, `step`}), `settle_steps`, `remeasured_60_max_abs_diff_nm`, `knock_flag_duty`, `wot_comparison` ([{`line`, `key`, `initial_torque_nm`, `model_nm`, `label`: `"transient"`}])}); `torque_floor` ({`nm`, `rpm`, `t_amb_k`, `rule`, `extrapolation`}); `delivery` ({`t_from_s`, `share_over_track_tol`, `largest_shortfall_nm`, `held`, `rpm`, `demand_nm`, `margin_to_threshold`, `bar_rpm_margin`, `map_vs_ceiling_kpa`, `identity` ({`max_abs_dlam`, `max_abs_dspark`, `contacts_lam`, `contacts_spark`, `bounds_are_python_floats`, `steps`}), `eta` ({`0.86`, `0.98`: same keys})}); `k3` ({`seconds`, `knee_k`, `time_above_knee_s`, `trace_sha256`, `second_knee_identical`, `knee_k_at_eta` ({`0.86`, `0.98`: float})}); `f7_table_and_floor_identical_under_two_knees` (bool); `coefficients` (`epa_coefficients.coefficients`); `e6_probes` ({`d_rows`: `"±10 %"`, `row5`, `row6`: {`sigma`, `probe`, `housing_change_k`}, `row9`: {constant: {`method`, `why_not_bracket`, `size`, `housing_change_k`, `load_bearing`}}}); `e6_row4` ({constant: {`x0.75`, `x1.333`: {`tau_s`, `peak_c`}}}); `e6_row7` ({`1.00`, `0.90`, `1.10`: {`total`, `thermal`}}); `e6_row13` ({`dwell_0s`, `dwell_30s`: variant}); `e6_in_use` ({variant: {row 1: `hot_tit_at_lambda1_c`, `air_gps`, `tau_s`; row 3: `heat_per_gram_j`, `coolant_heat_w`, `oil_heat_w`; row 7: `knock_share`}}); `dump` ({`sha256`, `n_values`, `keys`}); `derived` ({`path`, `sha_text`, `derived_sha`}); `engine_sha`; `e6_files` ({path: sha_text}); `finiteness` ({`asserted_before`, `excluded_fields`}).

**`run.json`** (calibration and validation alike): `engine`; `invocations`: [{`k` (int), `subcommand`, `argv`, `started_utc`, `ended_utc` (ISO 8601), `seconds` (float), `outcome` (`"ok"`, `"refused: <reason>"`, `"crash: <ExceptionType>"`, `"defect: ..."`, `"mismatch: ..."`), `opened` (sorted paths), `subprocesses` ([argv]), `outside_allowlist`, `refused_by_audit`, `git_head`, `step2_clean`, `run1_gate` ({`rule`, `switch`, `gated`, `waits`}; calibration), `versions`}].

**`defects.json`**: [{`k`, `run_invocation` (the `run.json` k of the invocation that took the route, which carries its time: plan §5.1 allows a wall-clock time in run.json only), `found_by` (subcommand or test), `assertion` (str), `fix_commit`, `previous_run` (`"defect_<k>/"`)}].

### 7.3 The derived file (`data/engines/<id>/derived_params.json`; plan §5.8; `engines.EPA_DERIVED_FIELDS`)

Top-level `_about` (str) and `_inputs` ({`contract_commit`, `freeze_record`, `view_sha256`, `manifest_sha256`}): bookkeeping, dropped by `derived_sha`. `cycle`: the 20 fields of `EPA_DERIVED_FIELDS`' cycle set (`form` a str). `ecu`: its 14 fields and the 12 of `engines.CAM_SCHEDULE` (`cam_on` an int). `boost_ceiling`: `envelope_flow`, `envelope_pr` (lists of float), `pr_cap`. After completion: `deliverable_torque` ([[rpm int, Nm float]]), `k3` ({`turb_knee_k`}), `loop` ({`torque_floor_nm`}). No timestamp.

### 7.4 `results/EPA_VALIDATION/<id>/ARMED.json` (plan §6.1; C5, C6, C10; decisions 63, 71)

`schema` `"epa-armed/1"`; `engine`; `armed_at_head` (the commit ARMED.json is made on); `repo_path` (the main work tree, realpath); `contract`; `freeze` ({`path`, `sha_text`, `commit`}); `complete` (same); `derived` ({`path`, `sha_text`, `derived_sha`}); `specs` ({path: sha_text}: engine, car, published car); `engine_sha`; `dump_sha256`; `in_sample_check` ({`in_sample_sha_text`, `check_exit`: 0}); `code` ({path: sha_text}); `code_changes_since_fit` ([{`path`, `defect_k`}]); `tightenings` ({`path`, `sha_text`, `commit`, `plant`}); `d3` ({`c3_files` [{`file`, `sha256`}], `summary` ({`file`, `sha256`}), `accord` [{`file`, `sha256`}]}); `data` (as §7.1); `held_out_structure` ({`per_held_out_line_equal`, `deciding_lines_equal`, `pooled_counts_equal`: bool}); `held_out_counts` (`epa_rows.HeldOutCounts`' fields); `versions`.

### 7.5 `results/EPA_TIGHTENINGS.json`, the schema `validate_epa` fixes now (plan §2 WP5; E5; decision 71)

`schema` `"epa-tightenings/1"`; `plant` (`"b58"`, required, checked at arm); `roads_sha`; `roads_seed` (int); `L1`: {`slope_points_per_K` (float), `set`, `shift_k`, `damage_reading`}; `E8`: {`k3_pair_change_vs_lambda_roads`, `k3_pair_change_vs_spark_roads`: [[shift, change]] on the contract's shift grid}; `provenance`: {`commit`, `code_sha_text`, `plant_sha`, `engine_sha`}.

### 7.6 A `StatResult` in JSON

In-sample: {`R`, `unit`, `kind`, `E`, `lines` ({line: {`E`, `clusters`}}), `deciding`, `worst_line`, `passes`, `no_statistic`, `reason`, `without`, `extra`, `n_rows`, `n_clusters`}. Held-out: those keys but `passes`, and `u` ({`u_num`, `u_input`, `u_D`, `u_val`, `u_stat`, `u_num_sd_undivided`, `unsourced`}), `lines` with every line's `u`, `label` and `certifies`, `certifying`, `label`, `kappa`, `coverage_restricted`, `condition` (d rows: `"both arms' cuts in 0-0.865"`, MD §1.2).

### 7.7 `rows.json`

`schema` `"epa-rows/1"`; `provenance`, with `freeze` and `complete` ({`sha_text`, `commit`}), `derived_sha`, `engine_sha`, `dump_sha256`, `tightenings` ({`sha_text`, `commit`, `plant`}), `armed_blob`; `counts` ({`held_out_rows`, `by_table`, `fired_lambda_missing`, `fired_spark_sentinel`}); `rows` ({row: held-out StatResult}); `coverage_flags` ({`engine` (the JSON's `coverage` blocks, the 42 °C charge, holds over 30 s, speeds over 115 km/h, the barometer), `per_row` ({key: [flags]})}); `section7` (`epa_stats.section7`); `c5_recheck_margin` ({`worst_line`, `E`, `u_val`, `margin`, `lines` ({line: |E| + 2u_val})}).

### 7.8 `e6.json`

`schema` `"epa-e6-held-out/1"`; `provenance`; `rows`: {`1`, `3`, `7`: {`variants` ({variant: {`delta_E` ({row: float}), `in_use`}})}; `2`: {`delta_E`, `must_not_move` ({`E2a`, `D1`, `L0`: {`dE`, `u_val`, `ok`}}), `findings`}; `4`: {from `complete.json`, `ceiling_below_2_mei`: null (the roads step's)}; `5`, `6`: {`sigma` ({row: dE}), `probe` ({row: dE}), `excluded_for` ({row: bool})}; `8`: {`u_num` ({row: float})}; `9`: {constant: {`method`, `size`, `delta_E`, `excluded_for`, `worth_r1`, `worth_b`}}; `10`: {`0.86`, `0.98`: {`C3b`, `C3d`: dE}}; `11`: {`plus`, `minus`: {`hot_tit`}}; `12`: {row: {`snapped`, `unsnapped`, `label_worse`}, `d1_kappa`}; `13`: {`handed_on`: true, `variants`}}; `exclusions` ({row: [constants]}); `excluded_for_every_listed_constant` ({row: bool}).

### 7.9 `c3.json` and `c4_accord.json`

`c3.json`: `schema` `"epa-c3/1"`; `provenance`; `files` (int); `segments` ({`n`, `hot`, `fired`, `outside_charge_range`}); `channel_checks` ({`direct2_vs_summary` ([{`test`, `ratio`}]), `maf_vs_direct2` ({`median_ratio`, `u_D`}), `pcm_map_closed_throttle` ({`below_baro`: bool, `n`}), `flat_maxima_dropped` (int)}); `fuel_scaling` (float); `rows` ({`C3a`, `C3b`, `C3c`, `C3d`: StatResult}); `eta` ({`0.86`, `0.98`: {`C3b`, `C3d`}}). `c4_accord.json`: the same keys, every row descriptive.

### 7.10 `STARTED` and `crash_<k>.txt` (validation)

`STARTED`: {`engine`, `head`, `armed_blob`, `defect_rerun` (null or {`k`, `reason`, `fix_commit`})}. `crash_<k>.txt`: the traceback; no statistic, since none reaches memory outside the computing frames before a file holds it.

### 7.11 `results/EPA_VALIDATION/summary.json`

`schema` `"epa-summary/1"`; `engines`: {id: {`rows_sha_text`, `labels` ({row: label}), `kappa` ({row: float}), `level_850c_label`, `drop` (bool), `drop_rows`, `c5_recheck_margin`}}; `drop_order` (MD §7's, as text); `inputs` ({path: sha_text}).

## 8. Each contract row, and the function that computes it

Held-out rows are computed by `validate_epa.run`, in-sample rows by `calibrate_epa.fit` (through `epa_fit.ladder`) and `check`, both through the same `epa_stats` function.

| contract row (MD) | function | population (`Populations` key) | stages |
|---|---|---|---|
| E1a (§4) | `epa_stats.row_E1a` | `hot` | in-sample, held-out |
| E1b | `row_E1b` | `fired` | held-out (descriptive) |
| E1i | `row_E1i` | held-out `HeldOutInitialRow`s | held-out (descriptive, transient) |
| E2a | `row_E2a` | `hot_meter` | in-sample, held-out |
| E2b | `row_E2b` | `fired_meter` | held-out (descriptive) |
| E3a | `row_E3a` | `hot_l1` | in-sample, held-out |
| E3b | `row_E3b` | `fired_l1` | held-out (descriptive) |
| E4a | `row_E4a` | `hot_enr` | in-sample, held-out |
| E4b | `row_E4b` | `hot_enr` on lines with ≥ 3 `l1_boost` rows | in-sample, held-out |
| E5 | `row_E5` | `l1_thr` (window A), `l1_boost` (window B) | held-out (descriptive) |
| D1 | `row_D1`, its per-row point `d1_invert` | `fired_meter` | in-sample (gating D1), held-out |
| L0 | `row_L0` | `hot_l1_meter` at the D1 point | in-sample, held-out |
| L1 | `row_L1` | L0's lines | in-sample (R 9.9 K), held-out (tightened R if any) |
| E8 | `row_E8`, `e8_response` | Final rows: dl over those with λ, ds over those with spark | in-sample (reported, outside the criterion), held-out |
| E6 row 1, 2, 3, 7 (refit) | `epa_fit.refit_variant`, `knock_rescale` (`calibrate_epa e6`); `epa_stats.refit_movement`, `must_not_move` (`validate_epa`) | | refits before the held-out run; statistics in the single run |
| E6 row 4 | `calibrate_epa.complete` (step 7) with `epa_fit.perturbed` | | completion |
| E6 rows 5, 6 | `epa_stats.excluded_for` on `epa_fit.perturbed` plants; σ from S1, S4; probe from completion | | held-out |
| E6 row 8 | `epa_stats.u_num` | | held-out (it is u_num) |
| E6 row 9 | completion's brackets and probes; `epa_fit.with_rich_slope_probe` after `retag_identity` | | completion, held-out |
| E6 row 10 | `d3_rows.c3_rows` with `demand_torque`'s η at 0.86 and 0.98 | D3 segments | held-out (C3) |
| E6 row 11 | `kernel_point` with `InputShift("imt", ±6.3)` | hot TIT rows | held-out |
| E6 row 12 | every row at `Conventions(snap=False, …)`; `epa_stats.worse`; D1's larger κ | | held-out |
| E6 row 13 | `calibrate_epa.complete` (step 9) | | handed to the preregistration |
| Tests lists (§4 E6) | `epa_stats.excluded_for_every_listed_constant` | | held-out |
| the λ clip floor (§4) | `view.lam_floor` (typed in each spec; `test_carried.py` pins it; §9.4 cross-checks) | | — |
| the neutral-action identity (§4, decision 39(b)) | `k3_knee.neutral_run` + `neutral_identity` | each EPA engine's locked climb | completion; the roads step for the B58 and the test roads |
| C1, C2 (§5) | `test_cars.py` (WP1) | | — |
| C3a–C3d | `d3_rows.c3_rows` | D3 segments | held-out run (Mazda) |
| C4 | `d3_rows.c4_accord` | | held-out run (Honda), descriptive |
| C5 | `epa_stats.c5_steps`, `c5_climb`, `c5_margin`, `cvt_diagnostic`; re-check margin `validate_epa.c5_recheck_margin` | scored climbs' steps outside transitions | the roads step; re-check after the held-out run |
| section 7 labels | `epa_stats.section7` | | held-out |

## 9. The tests

Each test proves its point with a control that must fail (mistake 12). No test but `test_epa_rows.Structural` opens a real EPA table, and none prints an EPA value. Every test runs with the venv's Python 3.13.2 and `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1`. **Chosen here:** two files beyond plan §8.1's list, `test_d3_rows.py` (C5 asks for synthetic traces) and `test_calibrate_epa.py` (C3's per-subcommand allowlist test, C6's records), and the shared `test_epa_fixtures.py` the task asks for.

### 9.1 `test_epa_fixtures.py`: the shared synthetic fixtures

Imported by every other test; run alone (`python test_epa_fixtures.py`) it checks itself.

- `CODE_FILES: tuple[str, ...]`: the files a temporary repository needs (`fingerprint.PLANT_CODE`, `fingerprint.py`, `evaluate.py`, `check_premise.py`, `engine_specs/**`, `data/derived_params.json`, `thresholds/**`, `engine_thresholds.py`, the nine modules), copied byte for byte from the working tree; never `data/engines/**` or `logs/**`.
- `table_names(engine) -> Mapping[str, str]`: role and index → name, from `epa_rows.TABLES` (no literal, §2.8).
- `SyntheticEngine`: `engine`, `lines` (tuple of str), `held_out_lines`, `steady_rows_per_line`, `holds_per_line` (Mapping), `lam_ref` (Mapping per role), `hot_map_floor_kpa`, `values` (a callable from (role, line, i) to a row's cells).
- `point_row(**fields) -> SteadyRow | FinalRow`, `held_out_row(**fields) -> HeldOutRow`, `initial_row(**fields) -> InitialRow`: in-memory rows with every field defaulted to a plausible synthetic value and `origin = "fixture"`.
- `write_tables(root, spec) -> Mapping[str, str]`: synthetic tables under `<root>/data/engines/<id>/` with `epa_rows.HEADERS`, written with `csv.writer`, rows from 6; `write_engine_json(root, spec)`; `write_channels_csv(root, spec)` (names, units, statuses; no ranges of real data).
- `synthetic_contract(root, specs, *, contract_commit) -> dict`: schema 4, the keys the loader and the validation read, `generators.sha256` from the real `thresholds/` files, `epa_tables_sha256` from the written tables, the held-out structure from `split_of`.
- `split_of(root) -> dict`: the generator's own `split.compute()` run in `root`'s interpreter as a subprocess (`python -c` in the temporary repository, so `thresholds.common.REPO` is that repository). **The one sanctioned exception** to N5: the synthetic contract's populations must be the generator's own (mistake 10), and the subprocess reads only the synthetic tables.
- `make_repo(tmp, specs) -> Repo` (`root`, `contract_commit`, `head`): `git init`, `data/engines/.gitattributes` `* -text`, the code, the synthetic tables and contract, committed with fixed `GIT_AUTHOR_*` and `GIT_COMMITTER_*` names, emails and dates, so every sha is reproducible.
- `synthetic_source(repo) -> epa_rows.Source`.
- `commit_armed(repo, engine, armed) -> str`; `add_worktree(repo) -> str`; `synthetic_tightenings(repo, *, plant) -> str`.
- `ToyModel`: closed-form torque, fuel, air, TIT and ECU laws satisfying §5.2.2, for hand answers.
- `truth_candidate(name, *, theta) -> engines.Plant`: `engines.build_candidate` from the B58's typed values moved by `theta`, for recovery tests on synthetic inputs (no EPA input).
- `rows_from_plant(plant, *, inputs, seed) -> tuple[SteadyRow | FinalRow, ...]`: synthetic rows whose outputs are `run_cycle`'s at synthetic inputs.
- `synthetic_trace(**kw) -> d3_rows.Trace`; `write_trace(path, trace)`; `write_summary_xlsx(path, rows)`.
- `forbid_real_data()`: a context manager installing an audit hook that fails the test on an open of the real `data/engines/*/epa_*`, `logs/**`, the real contract, `results/ENGINE_THRESHOLDS/split.json` or the data folder. Every test class runs inside it but these, each named: `test_epa_rows.Structural` (the loader's structural self-test), `test_epa_rows.CarriedPins` (the real contract's view and the real `epa_engine.json`'s facts, never a table; N4), `test_contract_pinned`, and `test_calibrate_epa.Gate.test_this_trees_contract_holds_the_first_evaluation`, whose subprocesses read the real contract (rule text only) and run only once a one-line probe shows the Run 1 rule standing, so they read no EPA table. `test_epa_stats` keeps its own hook, which records each refused open and fails the module at its end.
- `pinned_terms()`: synthetic values for the u_D terms decision 56 has not pinned and no D3 summary column unpinned, for a synthetic Run 1 or arming; `pin_contract_commit(repo)`: the repository's copy of `epa_rows` pinning its own contract, so the command line itself runs there in a subprocess.

Self-test: a synthetic repository passes `epa_rows.check_contract` and `check_tables`; `forbid_real_data` catches an open of a real table's path (control).

### 9.2 `test_contract_pinned.py` (plan §8.4; C12; decision 66)

Both contract files' sha_text equal the blobs at `epa_rows.CONTRACT_COMMIT` (version 5, `c842d74`, pinned a second time as `VERSION_5`) and, once it exists, `freeze.json`'s record, and no later commit touches either; that commit is an ancestor of HEAD and of `calibrate_epa.py`'s first commit (`git merge-base --is-ancestor`), and version 4's `a1b88e6` is in its parent chain; JSON `generators.sha256` equal the generator files; JSON `generator_inputs_sha256` equal `results/ENGINE_THRESHOLDS/*`; `git diff --quiet -- results/ENGINE_THRESHOLDS/` (C12). Control: a one-byte change in a scratch copy is caught.

### 9.3 `test_epa_rows.py` (plan §4.6; C2–C5, C8, C9; HO WP3.6)

- **`Synthetic`** (temporary repositories): counts and partition (yielded ∩ H = ∅, yielded ∪ H = every id; every yielded line outside L); each corruption stops the loader and passes with its guard monkeypatched off: a held id deleted, a held id shifted by one, a line removed from L with its rows kept, one byte of a table changed, a different `split.py` hash, a contract differing from its commit, a calibration id at a held line's speed, a held row parsed (plan §4.6 item 5); masks (`InitialRow.tit_c` raises; no ALPHA curve reachable); poison three ways (C8): the yield, the view and the manifest byte-identical, and one calibration cell changed moves them; the garbled-key contract gives the same view (C4); a sentinel cell, an empty spark cell, an empty HD1 bank and a missing λ each set their flag (decision 54); `TableFuel`'s LHV from the decimal string (§5.1).
- **`Structural`** (the real tables, the only class that opens them): the guards pass; counts equal the contract's `tables`; yielded ∩ H = ∅ by keys; `calibration_coverage` equals JSON `coverage.calibration_*` exactly (C9); `split.compute()` serialised as `json.dumps(…, indent=1, ensure_ascii=True)` hashes to `generator_inputs_sha256["split.json"]` (plan §4.6 item 2); the manifest is unchanged when every held-out cell of scratch copies is poisoned (no conversion: §5.1's manifest); `HEADERS` equal the tables' headers. It prints booleans and counts only.
- **`CarriedPins`** (HO WP3.6): `test_carried.py`'s `OWN_ENGINE`, `LINE_ENDS` and the fuel and `lam_floor` pins against `epa_rows.calibration_contract` and `epa_rows.engine_facts`' non-curve fields; the Mazda's table fuel equals its typed fuel to the bit.
- **`Scans`**: every rule of §3.1 and §3.2 over every step-2 module and test (and N9 over every `.py` git would commit), each run once on a scratch source that breaks it and must be flagged; the patterns are built from parts.
- **`Columns`**: every pinned header column is in exactly one of `FIELD_OF_COLUMN` and `DROPPED_COLUMNS`.

### 9.4 `test_epa_stats.py` (plan §2 WP3; MD §3–5)

Synthetic rows with hand answers through `ToyModel`: every population; every label branch of `line_label` and `row_label`, and certification; `worse`'s order; κ; L0's and L1's closed forms against a 10 001-point grid in f; the contract's own 5.183 K from (3.317, 0.01353) (JSON `propagation_b58.used`); E8's P equal to `thresholds.contract.interp`, its extrapolation flagged and the steeper slope at 0; E8's subsets below 3 rows give no statistic; λ-less and sentinel rows in the populations decision 54 puts them in and in the "without" readings; D1's pre-scan, bisection and nearer bound on a toy torque curve with and without a bracket; E4b's ε against a hand sum; the u-terms against hand propagation (SD/√n for a mean); `censoring` at exactly 2 rows within 1e-9 and at 1 (control); the Tests-list counting rule (E4); C5 on the B58: the 7th-to-6th notch at 130 km/h between 13.96 and 13.97 % (`test_reward.py:229`; decision 70), a barred downshift whose held demand is under its ceiling gated as barred, the transition test's exact inequality and end steps, and the three outcome cases.

### 9.5 `test_epa_fit.py` (plan §5; C1; D1–D14; HO WP3.1, 3.3, 3.5)

On rows from `test_epa_fixtures.rows_from_plant` (synthetic inputs, a known truth): each stage recovers its truth; two runs byte-identical (canonical JSON of the `FormFit`); every shortcut equal to `run_cycle` within 1e-9; S3c: a line without holds cannot lower the ceiling, ties refused (D1); S3b: a true gate between the steady and the Final rows is found, ties go to the highest gate (D2); the depth's upper edge is `1 − lam_floor` when that is lower than C1's bound, is reported active, and builds through `build_candidate` (HO WP3.1); S3a: `spark_min` holds `base + comp` unclipped at IMT ≥ 37.5 °C (D3); S4's weakest direction and the two extra starts (D6); the empty-piece rule (D7); zero columns at the optimum reported, not asserted (D10); the per-engine ladder stops at A for an A truth and at A+B for a `ve_map` truth (decision 49); the retag identity at 0.65, bit for bit, and a slope one ulp above 0.65 seen at λ 0.95 (HO WP3.3; B2); the octane moves only `knock_integral` and `knock_prob` (HO WP3.5); the provisional completion values move no row output; `t0_judge` passes a known recovery and fails the out-of-form seed's (D11); `cal_rows` refuses a `HeldOutRow` (control).

### 9.6 `test_epa_freeze.py` (plan §5.8)

Every refusal shown, and shown to pass once its cause is removed: a second freeze, a frozen section edited after the freeze (`engines._check_freeze` and `check_frozen`), a derived path different from the spec's, a NumPy value in the values (B10); `freeze.json`'s `frozen_sections_sha256` is `engines.frozen_sections_sha256`'s; the dump of a synthetic candidate is reproducible and moves with a one-ulp change of one constant (control); `write_json_atomic` leaves no partial file when interrupted.

### 9.7 `test_k3_knee.py` (plan §7.7)

On the B58: `baseline_trace` plus `knee_for`, under `shifted_ecu` exactly as `ecu_shift.py:70-78`, reproduce `results/ENGINE_THRESHOLDS/ecu/k3_lam-0.02.json` and `k3_spark-0.75.json`'s `knee_k`; the nominal trace gives `time_above_knee_s` 413 at 1123 K; `neutral_identity` on the B58's locked climb reads 0 and 0 with Python-float bounds; a control with a NumPy float64 bound counts a contact at a binding step (MD §4); `delivery` reports the B58's 7th gear on the locked climb.

### 9.8 `test_epa_coefficients.py` (plan §2 WP3; F5; HO WP3.4)

Pointed at the B58, `coefficients` reproduces `results/ENGINE_THRESHOLDS/b58_propagation.json`'s values bit for bit; a B58 variant with another scenario ambient moves the climb (F5); `cyc` passes the ECU's cam and a form-D candidate is evaluated, not refused (HO WP3.4).

### 9.9 `test_validate_guards.py` (plan §6.1; C5, C6, C10, C11)

In temporary git repositories only (C5): `read_held_out` refuses without ARMED.json committed at HEAD whatever token is passed, and with a forged token; it yields only after `verify_for_validation`; `run` refuses in a linked worktree, without `.git`, outside the recorded path, with any extra file (tracked, untracked or ignored) in the output folder, with another path of that folder in `git log --all`, and with dirty validation code; STARTED is written before the first held-out read; a crash writes `crash_<k>.txt` and blocks re-execution; re-execution with STARTED alone is allowed; the defect route writes `rows_rerun<k>.json` and caps labels; arm refuses a tightening record whose `plant` is not `"b58"` (E5) and a code change since the fit without its defect entry (C10); arm's held-out counts on synthetic tables equal the fixture's; each refusal passes once its cause is removed. Since 23 October 2026: arm refuses an open pin, a T0 not passed, a poison proof not equal, an audited defect in `run.json`, and on the defect route a calibration other than the previous arming's; check's exits are read by name; a clone without the arming's nonce and a run whose STARTED was removed are refused; a worker's warning is an error; and one arming runs the REAL `calibrate_epa.py check` (RealCheck) on a Run 1 with the real in-sample stage.

### 9.10 `test_d3_rows.py` (C5; MD §5)

On synthetic traces: the padding rows dropped; each segment rule shown to cut (3 s, ±25 rpm, two MAP refreshes, the converter within 1 %, A/C, one gear, coolant); `demand_torque` against a hand value; the MAF check and a flat maximum dropped; the summary workbook read; a header missing a channel stops before any value is converted; C3's labels through `epa_stats`.

### 9.11 `test_calibrate_epa.py` (C3, C6, C10, C13)

In temporary repositories with synthetic tables: `dry-load`'s opened set is a subset of its allowlist and an extra open is flagged (plan §4.6 item 8), also with the audit installed before the imports as the command line installs it; a worker of the pool reports its opens and refuses the tables (C3); a forbidden open, a forbidden `Popen` argv and a git command reading contents are refused; the gate holds the first evaluation (on this tree only after a probe shows the rule standing, and as the command line in a synthetic repository); STARTED precedes the first model evaluation and survives a crash; `run.json` lists refused invocations; the subcommand order and Run 1's proofs are enforced; `stage0.json` carries `SEEN_BEFORE_THE_FIT`; the defect route moves the old run to `defect_<k>/`; C8's proof can fail (a held-out cell reaching a stage, a stage reading the repository's own tables, copies that are the tables, a reference that is not the fit's); an audited defect and a started held-out run hold every later step; each guard of the completion and of check is shown able to fire; and, since the fourth fix (§14), each of the fourth isolation review's eleven planted git forms is refused sealed (in the fit, the poison and a pool worker) while every own git run of the step-2 code passes sealed, each of poison.json's comparisons fails alone when its input moves, the Run 1 inputs outside the code and the plant are bound, an interrupted body with a dead pool worker still writes its crash, and a loader guard that stops is a refusal.

### 9.12 `test_epa_plants.py` (plan §7.6, WP4)

Written in WP3, run at commit D: for each EPA plant whose derived file and freeze record exist, `python engines.py`'s line, `engines.get` building it, `fingerprint.py --engine <id>` no longer refusing it, the deliverable-torque table against a fresh `measure_deliverable_torque`, and the dump against `complete.json`; until then each check skips by name (`uncalibrated_or_skip`'s pattern, HO WP4.1), and the same checks run on a synthetic frozen candidate in a temporary repository so that they are shown able to fail.

### 9.13 Before commit C

`python -B test_engine_threading.py` alone; `test_contract_pinned.py`; every file of this section; `test_carried.py`, `test_fuel_forms.py`, `test_cars.py`, `test_trainable.py`, `test_plant_guards.py` (HO P7.1); `python verify_docs.py`, and `drift_test.py` only if its guard is touched (CLAUDE.md). S0, T0 and everything that reads an EPA row wait for Run 1 (A1).

## 10. The choices this file makes, in one list

1. `Token` and `verify_for_validation` live in `validate_epa.py`, not `epa_freeze.py` (C3 over plan §4.3, §6.1).
2. `read_held_out` and `held_out_counts` are defined in `epa_rows.py`, called only by `validate_epa.py` and its test; the reader checks ARMED.json itself and the token by its fields (C3, C5).
3. An explicit `epa_rows.Source`, so every test of the reader runs on a temporary root (C5).
4. The table roles come from `split.ENG`, cross-checked with the contract's keys; `HEADERS` are keyed by (engine, role, index) and typed from the header lines before commit C.
5. TIT in °C, the unit of the model's `egt_c`.
6. A table's LHV in J/kg from the contract's decimal, never a product by 1e6.
7. Held-out rows are their own types with the same fields, so a fit refuses them by type.
8. `ecu_strategy_b58`, `perturbations_E6` and `k3_seconds` join C4's allowlist (B58 measurements and rule text only).
9. The Ford's Cell 9 rows run at the engine's typed octane, its effect measured as knock only (HO WP3.5).
10. `epa_coefficients` keeps the contract's 42 °C for G and the plant's own ambient for the climb (F5), so the B58 reproduces bit for bit.
11. C5's functions live in `epa_stats.py`.
12. Subcommands `dry-load`, `t0` and `poison` beside `fit`, `e6`, `complete` and `check`; `summary` beside `arm` and `run`.
13. STARTED per engine, written by the first subcommand that evaluates at an EPA row's inputs, T0 included.
14. Poison values `-1e+06`, `1e+06` and empty; the full form-A poison fit on `mazda_25t`.
15. T0's noise from `default_rng([0x70, seed])`.
16. Provisional completion values during the fit (knee 1123.0, floor 0.0, table []), shown to move no row output.
17. One canonical JSON form for every record hash, `engines.frozen_sections_sha256`'s.
18. `calibrate_epa.py` prints no fitted number; `validate_epa.py` prints no statistic.
19. Spark's u_input fallback, if no instrument page states one: 0.1 CAD resolution, unsourced.
20. The D3 dialect: tab-delimited with bracketed units, checked at the first real read.
21. The completion's `DERIVING_PARAMS=1` process evaluates `build_candidate` plants built from the frozen sections and the completion values measured so far, so the plant measured is the plant `get()` will build.
22. Two extra test files, `test_d3_rows.py` and `test_calibrate_epa.py`, and `test_epa_fixtures.split_of` as the one sanctioned subprocess use of the generator's split.
23. S3a starts at the lowest calibration Final MAP; S3b's gate grid starts at the lower of that MAP and DESIGN 100 kPa (both C1's sources).
24. `arm` takes `--jobs`, since it runs `calibrate_epa.py check` as a subprocess.

## 11. What WP3's implementer pins before commit C, and what this file does not settle

- **Pinned from a source, before commit C, each read entered in `SEEN_BEFORE_THE_FIT`:** `epa_rows.HEADERS` (each table's header line); `epa_stats.U_INPUT` and `U_D` (EPA's instrument pages, opened first and recorded, decision 56); `d3_rows.CHANNELS`' time, speed and coolant names and the summary's columns (`CATALOGUE.md` or Argonne's documentation, never a D3 file); `epa_fit.TOLERANCES` (measured on synthetic B58 rows, D5).
- **Decision 56's pins, 23 October 2026** (`epa_stats.U_INPUT`, `U_D`; `test_epa_stats.Pins`). Read: the four test reports (`logs/epa/<engine>/3- and 3a- … Test Report.docx`, every paragraph and table), the three ALPHA Generation Process pages and the four NVFEL fuel analyses; no EPA table or workbook (`epa_stats.SOURCES_READ`, which `calibrate_epa.SEEN_BEFORE_THE_FIT` carries entry by entry since 24 October 2026, `test_calibrate_epa.Pieces`). Each report has its own Table 8, "Standard Uncertainties for Signals", in its section Uncertainty (table of contents: Mazda page 21, Honda 26, Ford Cell 9 13, Ford HD1 13); a pin takes its u(signal) (u(calibration) and the average u(operation) combined, EPA's own sum), and on HD1, which prints u(calibration) only ("Both the standard deviation and the number of data points vary from mode to mode"), its u(calibration). Each report's Table 2 lists an HBM torque sensor and a Micro Motion Coriolis fuel meter, with no accuracy. A row reads the pin of its own report, `(engine, test_cell)`.

  | channel | Mazda, Test Cell 9 | Honda, Test Cell 7 | Ford, Test Cell 9 | Ford, Test Cell HD1 | where none is stated |
  |---|---|---|---|---|---|
  | torque (u_D, random) | 0.127 N m ("Torque (Nm) \| 0.116 \| - \| 0.0519 \| 0.127") | 0.135 ("Torque (Nm) \| 0.125 \| 0.0512 \| 0.135") | 0.159 ("Torque (Nm) \| 0.0808 \| 0.137 \| 0.159") | 1.591, u(calibration) ("Torque (Nm) \| 1.591") | no fallback: a row of no report refuses |
  | meter (u_D, random) | 0.00241 g/s ("Fuel (g/sec) - steady \| 0.00240 \| - \| 0.000240 \| 0.00241") | 0.0100 ("Fuel (g/sec) - steady \| 0.0100 \| 0.000728 \| 0.0100") | 0.00737 ("Fuel (g/sec) \| 0.00640 \| 0.00365 \| 0.00737") | 0.00581, u(calibration) ("Fuel (g/sec) \| 0.00581") | no fallback; the "transient" fuel row is the injector correlation's, never the meter's |
  | speed (u_input) | 1.000 rpm ("Speed (rpm) \| 0.998 \| - \| 0.0676 \| 1.000") | 0.302 ("Speed (rpm) \| 0.289 \| 0.0878 \| 0.302") | 1.197 ("Speed (rpm) \| 1.183 \| 0.178 \| 1.197") | 0.637, u(calibration) ("Speed (rpm) \| 0.637") | 1/√12 rpm, unsourced |
  | MAP (u_input) | none stated | none stated | 0.321 kPa ("Pressure (kPa) \| 0.321 \| 0.0053 \| 0.321") | none stated | 0.01/√12 kPa, unsourced |
  | IMT, ECT (u_input) | none stated | none stated | 0.593 K ("Temperature (deg C) \| 0.549 \| 0.225 \| 0.593") | none stated | 0.1/√12 K, unsourced |
  | spark (u_input) | none stated | none stated | none stated | none stated | the declared 0.1/√12 CAD, unsourced |
  | λ (u_input; u_D) | none stated | none stated | none stated | none stated | 0.01/√12, unsourced; u_D 0.012 (contract), unsourced |
  | TIT (u_D, common) | none stated | none stated | the generic "Temperature (deg C)" row, **not applied** | none stated | IEC 60584-1 class 2, 0.0075·\|t\|/√3, unsourced |

  **Left to the team:** whether the Ford Cell 9 report's generic "Temperature (deg C) \| 0.549 \| 0.225 \| 0.593", which names no sensor and no range, covers the turbine-inlet thermocouple at 490–900 °C. Applied, it would shrink the Ford Cell 9 rows' TIT u_D from 3.5 K at 800 °C to 0.593 K, so it is not applied without the team; on IMT and ECT it only widens u, and is applied. Also open: HD1's pins are below its u(signal) by a u(operation) its report prints for no mode, and a Final row's meter averages a shorter window than the steady average Table 8 reports. `calibrate_epa.SEEN_BEFORE_THE_FIT` takes `epa_stats.SOURCES_READ` (done 24 October 2026), and the two tests that expected the production table's meter and torque open, `test_validate_guards.ArmProofs.test_arm_refuses_while_a_pin_is_open` and `test_calibrate_epa.Order.test_t0_and_fit_refuse_while_a_pin_is_open`, now test the pins (23 October 2026, with the repin to version 5): the production table passes the pin check, and one report's torque pin or every meter pin taken away refuses, naming the term. **Corrected 24 October 2026** (the Run 1 review): the D3 summary columns open in production are the Honda's (`accord_2018.*`) as well as the Mazda's (`cx9_2016.*`); the Ford has none. Since the code is shared, t0 and fit now refuse on every engine while any engine's columns are open (`test_calibrate_epa.Order.test_the_pins_guard_reads_every_engines_d3_columns`), so Run 1 starts on no engine until both are pinned from a source, each read entered in `SEEN_BEFORE_THE_FIT`, before commit C.
- **No plant change is needed.** The identity check reads the baseline's λ and spark by wrapping one `BaselineECU` instance's `step` inside `k3_knee.neutral_run`; it edits no file and changes no class. If the implementer finds that a wrapped instance method does not see every call (`SupervisoryTunerEnv.step` calls `self.ecu.step` on the instance, `engine_env.py:1283`), the identity cannot be checked without a plant change, and that is stopped and reported, never patched in PLANT_CODE (B5).
- **Not settled here, and not WP3's:** the answers of Jad's column and Ghassan's own answers to decisions 73–77 and the readings of 23 October, version 5's two readings of decision 77 among them (version 4 had the first fit wait for them, MD §13; version 5 records Ghassan's order that it go ahead without them, MD §14); the four questions the seventh review left for a later contract version (MD §13); a documented λ-sensor floor (none opened).

## 12. The second fix (23 October 2026)

Four reviews (isolation, contract, fit, tests) after the integration; each change below cites its finding and has a control in the test named.

- **The seal** (§3.3; `test_calibrate_epa.Seal`): the contract, the tables and `epa_engine.json` refused in every computing phase and in every worker. Poison loads everything first and runs its reference, poisoned stages and full fit sealed. An open the audit refused is a coding defect even when the code that made it caught the refusal (`linecache` does): the invocation exits `EXIT_DEFECT` and later steps refuse; a worker reports such a refusal beside its opens (`REFUSED_TAG`).
- **The scans** (§3.2 N3, N8, N12; `test_epa_rows.Scans`): every private name of `epa_rows`; a Source's path attributes; the standard library's other readers and every re-export (`reexports`), so `epa_rows.split.load`, `epa_rows.common` and `epa_rows.io` resolve to the module they reach. `epa_freeze.read_json` reads a calibration record, a derived file or a top-level `run.json` only (`readable_record`).
- **Run once** (§5.8.4; `test_validate_guards.RunOnceMore`, `test_calibrate_epa.RunOnceAndTheCode`): `validate_epa.py run` writes `epa_started_<id>_<blob>` before its first held-out read and `epa_ended_<id>_<blob>` (every output's sha_text) after `run.json`, in the work tree's git directory, never removed, with an "ended" event in the invocation log; `refusals` reads both; `epa_freeze.held_out_started` refuses every refit while a marker exists.
- **Run 1's proofs**: `poison_problems` checks exact key sets (`epa_fit.POISON_RUN_KEYS`, `poison_run_stages`, `poison_tied_stages`); fit applies the audit guard, refuses a T0 whose code or plant is not the code it runs (`t0_code_problems`), and every subcommand compares Python, NumPy and SciPy with `requirements-lock.txt` and the run's earlier record (`version_problems`); arm lists every change since `t0.json`'s head and checks every `defects.json` entry by `defect_entry_problems`.
- **The contract's rows**: D1's torque target in u_D (`epa_stats.torque_target_shift`, `UncertaintyInputs.torque_target`; D1, L0 and L1 read torque's pin); u_num is SD/sqrt(n) for a mean; E4b on fewer than 2 enriched rows has no pooled u_stat and cannot certify; `reported_labels` takes `excluded_every`; E5 is reported without its flagged rows and coverage-restricted; L1's slope is a finite magnitude above 0 (`_R`, `tightening_problems`), and the tightenings' engine_sha and plant_sha are the B58's as built (`b58_identity`; the roads' sha waits for WP5 to name its record).
- **E6**: load-bearing is judged at the band (the bracket, or the fit's sigma), not at the probe, None with its reason for an ASSUMED constant (`probe_sizes`); row 9 probes every ASSUMED `[geometry]` and `[cycle]` field (`row9_fields`, from the spec's labels: the residual-fraction law, `n_poly`, the Honda's octane) and lists the CORRELATION ones it does not (`row9_not_probed`); E8 under row 1 is not applicable, and the readings of row 2's "E2" and of a law's exclusion across its fields and signs are written into `e6.json`; E3b's move under row 6 is reported as descriptive.
- **The fit**: S4's five starts at 1e-10 and a declared polish at 1e-12 (`TOLERANCES`' note holds the measurement); S2's start's departure from PLAN.md 5.4 declared in `fit_settings`; T0 as in §7.2; `RealT0` (`EPA_FIT_SLOW_T0`) and `RealT0OnSyntheticTables` (`CALIBRATE_EPA_SLOW`) run the real T0, opt-in.

**Left to the team before Run 1** (not WP3's to decide): FS4, whether lam_floor's invariant edge may bound S3b's depth (amend C1 and wrong claim 14, or make "the fitted depth breaks the invariant" a declared outcome); the in-sample E4b gate at T0's noise (a new contract version is allowed before the first fit, rule 0); torque's and the meter's u_D pins (decision 56), pinned 23 October 2026 from EPA's test reports (§11), with the Ford Cell 9's generic temperature row against the turbine-inlet thermocouple left to the team there.

## 13. The third fix (24 October 2026)

Four reviews (leak, contract, Run 1, tests) of the tree on version 5; each change cites its finding and has a control in the test named.

- **The seal over child processes** (§3.3; `test_calibrate_epa.Seal`, `Audit.test_the_seal_covers_git_and_child_processes`): the review's two planted leaks, `git show HEAD:<contract>` and a child interpreter reading a held-out cell, each crash the fit and the poison where they are planted, the command named in `refused_by_audit`; a worker's child is refused and reported; a spawn pool without the audit's initializer is refused while sealed, epa_fit's own pool runs. Another spelling of a sealed file (`\?\`, a hard link) is refused at once (`Audit.test_another_spelling_of_a_sealed_file_is_refused_at_once`).
- **The scans** (§3.2 N12 widened, N13; `test_epa_rows.Scans`): the review's sources (`import subprocess` in a stage, `epa_freeze.subprocess.run`, `epa_freeze._git` and `_read_json`, a raw `multiprocessing` pool, `ctypes`, `getattr(__import__(...), ...)`) are each flagged.
- **What was seen before the fit** (C13; `test_calibrate_epa.Pieces.test_seen_before_the_fit_carries_the_pin_authors_reads`): `SEEN_BEFORE_THE_FIT` carries `epa_stats.SOURCES_READ` entry by entry, read from `epa_stats` itself, and the four reviewers' and the fixer's reads of 24 October.
- **E4b's pair estimate** (the contract, section 4; `test_validate_guards.HeldOutAssembly.test_e4b_reads_the_initial_rows_for_its_pair_estimate`): the held-out run hands E4b the Initial rows beside the steady and Final ones (`validate_epa.rows_for`, used by `_Evals` and `HeldOutState.at`), so the Initial-to-Final pair estimate is computed; E4b's pooled value and u-terms do not move.
- **Decision 77's reading (b)** (`test_epa_stats.InSampleRule.test_a_line_that_fails_behind_a_worse_noisier_one_still_fails`): a quieter line that fails beyond its noise fails the statistic behind a worse, noisier line that neither blocks nor passes; the test review's mutation m1 (the worst line judged alone), which survived every test, is killed by it.
- **Run 1's code and plant** (`test_calibrate_epa.TheFreezesCodeAndPlant`; `test_validate_guards.ArmProofs.test_arm_refuses_a_step_after_the_freeze_on_other_code_or_plant`): t0 and fit require the plant's code and specs committed and clean; poison, e6 and complete require the step-2 code and the plant committed, clean and freeze.json's (`code`, `plant_sha`); arm checks that poison.json, the five refit variants and complete.json were written by freeze.json's code and plant from clean code (`validate_epa.after_freeze_problems`). No defects.json entry excuses a difference there: a change after the freeze is `fit --defect`, which re-runs from T0.
- **The pins across engines** (§11): t0 and fit refuse on every engine while any engine's D3 summary columns are open, the Honda's and the Mazda's today.
- **Other fixes**: a plain t0 refuses over an audited defect or crash in `run.json`; `t0 --defect` is refused once a fit has run (stage0.json, freeze.json, in_sample.json or the derived file present); in_sample.json records `noise` per form beside `failing` and `no_line`; `OPENBLAS_NUM_THREADS` must be unset or 1 (`_prelude`, `epa_fit.assert_one_blas_thread`); poison's `--scratch` and dry-load's `--out` are refused inside the work tree (dry-load writing nothing there); a `KeyboardInterrupt` or other `BaseException` leaves its `crash: <type>` entry in `run.json` and is raised again; `test_contract_pinned`'s "no later commit" half has its control; `test_d3_rows.Guard.test_a_scratch_file_is_not_refused` asserts; the on-tree Gate test fails before running the command line if `results/EPA_CALIBRATION/mazda_25t/` exists without STARTED, and removes what a regression would leave.

**The Run 1 procedure, as the code enforces it** (the Run 1 review; PLAN.md's WP4 block and `derived.py`'s `_maker` text, a plant file left frozen, list another order): `dry-load` (optional), `t0`, `fit`, `poison --scratch <outside the tree>` (`--full` on `mazda_25t`), `e6`, `complete`, `check --jobs <n>`, each with `--engine` and `--jobs`, `OMP_NUM_THREADS=1 MKL_NUM_THREADS=1` and `OPENBLAS_NUM_THREADS` unset or 1, `EPA_RUN1_GO=<id>` set by whoever starts it on the team's order. **No commit while a fit runs**: `freeze_record` refuses a HEAD that moved during the fit, after the whole ladder. **One `--jobs` for Run 1 and any reproduction**: `fit_<form>.json` records it, so freeze.json's `fits` hashes depend on it, and `provenance.versions.platform` records the OS build. **Commit E carries `run.json` again**: arm's `check` subprocess appends to it after `arm/calibration` required it committed. The Run 1 review measured, on synthetic tables only, about 43 minutes for the Ford's composition at 10 jobs (its scratch `lens_run1/ford_run1.log`) and estimated 1.25-1.5 hours per engine on the real tables at 10-12 jobs: plan uninterrupted multi-hour windows on AC power. Commit D's checklist is the Run 1 review's (its "What the freeze commit (D) must carry"): the records of §6, the re-runs of decision 48 (`check_premise.py`, `validate.py` with `validation_table.md` in the same commit if it moves, `test_reward.py` with its output in the message, `check_roads.py`), the three app suites, the lab pins, `verify_docs.py`, and HANDOFFS WP4.1's suites.

**Left, with the reason** (not quick, or not WP3's to decide):
- the D3 summary columns of the Honda and the Mazda are not pinned: a read of `CATALOGUE.md` or Argonne's documentation is a source read for whoever pins them, entered in `SEEN_BEFORE_THE_FIT` before commit C; until then t0 and fit refuse on every engine (fail-closed);
- caller attribution in the audit hook (only `epa_rows` may open the tables and the contract): the scans and the seal cover the reviewed paths; an in-process read before the seal by `calibrate_epa`'s own code stays the scans' to refuse;
- `epa_rows.read_held_out` requiring the arming's nonce and STARTED marker itself, and an exclusive (`O_EXCL`) started marker against two concurrent `validate_epa.py run`: both touch C6's re-execution rule (a STARTED alone after a killed process), which a lock left by a killed run would change; for the team;
- a check that every yield row's `(engine, test_cell)` is one of `epa_stats.REPORT_CELLS` before STARTED: on this tree the synthetic rows belong to no report, so the check would need its own fixture path; all ten tables' cells are in `REPORT_CELLS` today (the test review, booleans only);
- E6 row 1's E8 change reported as computed beside its reason, and T0's synthetic rows keeping EPA's measured cam phase (`epa_fit.t0_rows`): both change records or T0's input, and T0 must then be re-run before Run 1; for the team;
- the Ford and the Honda in the opt-in slow class `WholeRun1OnSyntheticTables` (the Run 1 review ran the Ford's composition once, passing). After this fix the class was run once on the synthetic Mazda (`CALIBRATE_EPA_SLOW=16`: 1 test, OK, 955 s), so the seal over child processes does not stop a real Run 1's pools; `RealT0OnSyntheticTables` was not re-run. Both are to be run with the WP3 suites just before commit C;
- for the team, unchanged: FS4 (§12); the in-sample E4b without a u_stat reading neither; the meter's and torque's u(calibration) applied per cluster; κ below 1 for a d row untested for want of a certifying line (a contract question before Run 2).

## 14. The fourth fix (24 October 2026)

Four reviews (leak, contract, Run 1, tests) of the tree on version 5 after the third fix; each change cites its finding and has a control in the test named. Nothing was fitted to EPA data, no plant ran on an EPA row and no statistic was computed on EPA outputs: every measurement below is of synthetic tables.

- **The sealed git shapes** (§3.3; the leak review's blocking item; `test_calibrate_epa.Audit.test_the_seal_covers_git_and_child_processes`, `Audit.test_the_step2_codes_own_git_runs_pass_sealed`, `Seal.test_a_planted_git_diff_crashes_in_the_fit`, `Seal.test_a_planted_glob_pathspec_crashes_in_the_fit`, `Seal.test_the_planted_log_and_config_forms_crash_in_the_poison`, `Seal.test_a_worker_refuses_every_planted_git_form_and_reports_it`): `calibrate_epa.SEALED_GIT_SHAPES`, the fifteen argv shapes the step-2 code runs, word for word, replaces the subcommand list. The review's eleven planted forms (`test_calibrate_epa.planted_git_forms`) are each refused sealed, as an argv list and as Windows' command line; planted, two crash the fit, four the poison, and all eleven are refused and reported in a pool worker, the command named; the controls are the step-2 code's own git helpers, called sealed in a synthetic repository, which run and refuse nothing, each argv they ran one of the shapes, and every other test of the file. A `-c` other than `core.safecrlf=false`, `--config-env`, `--exec-path` and a pager are refused sealed or not; unsealed (the loader's phase), diff prints contents unless `--quiet` and log with any patch flag or the pickaxe.
- **The audit's other doors** (the leak review's other items; `Seal.test_an_environment_change_and_a_link_are_refused`, `Audit.test_startfile_is_refused_while_sealed` and `Audit.test_the_long_prefix_is_stripped_before_any_comparison`, the last two the tests review's): the hook fails closed while sealed; `os.putenv` and `os.unsetenv` are refused while sealed; a link made while the audit is active is refused; every always-refused file is refused under another name by its identity (§3.3). §3.3 now says that the seal is the only control for a read of committed git objects.
- **The Run 1 inputs** (the Run 1 review's first blocking item; `TheFreezesCodeAndPlant.test_the_run1_inputs_outside_the_code_and_the_plant_are_bound`, `test_epa_freeze.Git.test_the_code_record_and_its_changes`): `epa_freeze.RUN1_INPUTS` (`evaluate.py`, `engine_specs/b58.toml`, `requirements-lock.txt`, the last the review's other item) join `CODE_HASHED`, so t0 and fit require them committed and clean, fit compares T0's, poison, e6 and complete compare the freeze's, and the arming lists every change (`validate_epa._arm_code`, `after_freeze_problems`); the held-out run's allowlist holds the lock file. `code_sha_text` and freeze.json's `code` grow by three paths; no record exists yet.
- **The machine** (the Run 1 review; `test_epa_freeze`'s version check): `epa_freeze.version_problems` compares `platform` with the run's earlier record (CLAUDE.md rule 3: one machine). An operating-system update between two subcommands of one engine's Run 1 now refuses the later one.
- **Run 1's recovery** (the Run 1 review's other items; `RunOneRecovery`): an invocation whose body did not end ok terminates its pools (`epa_fit.close_pools(terminate=True)`) instead of closing and joining them, so an interrupt while a worker lies dead still writes its `crash: KeyboardInterrupt` entry (the control, close and join as before, has not returned after 45 s); a `LoaderStop` is `refused: LoaderStop at <where>`, its message neither recorded nor printed, and holds no later step (an open the audit refused on the way stays a defect); `fit --defect` checks the environment before it moves the run.
- **The writing marker** (the leak review's other item; `test_validate_guards.RunOnceMore.test_a_finished_run_with_started_alone_left_does_not_run_again`, `test_a_cleaned_work_tree_does_not_run_again`): §5.8.5. A run killed after it began writing its outputs, every record but STARTED removed, no longer runs again on the normal route; the control, the marker and the log's event removed too, runs.
- **The poison's comparisons** (the tests review's blocking item; `Poison.test_each_comparison_fails_alone_when_its_input_moves`): each input of a poisoned or garbled Source moved alone -- S0's report, the view's hash, the yield's, the manifest's, engine_facts, the full form-A fit's frozen hash, the garbled contract's view and yield -- makes exactly its key false, all_equal false, the invocation a CompletionDefect crash, and e6 refuse. Each of the eight comparisons hard-wired to True in a scratch copy fails the test (the fixer's scratch `fix4/mut_poison.py`: 8 of 8).
- **C6's warnings in run's own process** (the tests review's blocking item; `test_validate_guards.RunOnce.test_a_warning_in_the_runs_own_process_is_a_crash`): a RuntimeWarning after the first held-out read is a crash, crash_1.txt written; the mutation to "ignore" fails the test (`fix4/mut_vg.py`).
- **E8's EPA lambda and the snap** (the tests review's blocking item; the contract review's mutants m26, m38, m44): `test_epa_stats.Kernel.test_epa_lambda_is_cell_referenced_by_the_rows_lambda_ref_and_never_snapped`, `E8Rows.test_e8_reads_epa_lambda_unsnapped_inside_the_band`, `E8Rows.test_e8_on_a_lambda_ref_099_table_through_the_kernel`, `LambdaAndInputs.test_the_snap_is_judged_against_the_rows_lambda_ref`. The contract review's other survivors (m18 D1's tie, m24 `mark_censored`, m30 a part's larger kappa, m31 the exclusion's strict edge) and the tests review's (decision 77's reading (a), `within_noise`'s edge, `mark_censored` on an Initial row) each have a hand test. Each of the eleven mutants is killed (`fix4/mut_stats.py`); test_epa_stats has 99 tests.
- **The seam** (the Run 1 review's other item; `test_validate_guards.RealCheck`): validate_epa's E6 readers (`_variant_values`, `Conventions(**...)`, `_per_field` for rows 5 and 6, row 9's sizes and records) read the complete.json and e6 files calibrate_epa wrote in that test.
- **Smaller**: `test_contract_pinned.Controls.test_the_data_guard_records_an_open_under_data_and_logs`; E4b's u-terms compared with and without the Initial rows (`HeldOutAssembly`); the on-tree Gate test fails when `gated()` regressed and skips by name beside a run.json holding only refused invocations; `SEEN_BEFORE_THE_FIT` carries the four reviewers' and the fixer's reads (`Pieces`).

**T0 on the synthetic Mazda: what the review found, what the fixer measured, and what is the team's before T0 runs at real inputs** (the Run 1 review's second blocking item; synthetic tables only):

- (a) The rehearsal failed on the fixture's synthetic R, through two paths. The in-sample stage: D1, a mean of |delta_D|, has a floor at T0_NOISE of about 0.8 sigma, 0.49 % at the truth itself (the review's `r1lens/t0_d1_at_truth.py`), above the fixture's 0.08 %; with D1's raised to 1.5 %, E1a's 0.05 % failed seeds 2 and 3 at their truth's form (the fixer's `fix4/realt0.log` and `fix4/t0_summary_d1.log`: seed 1 passed; seed 2 stopped at A+B, chi-square 406.0; seed 3 at A+B+C, chi-square 70.8). And the fit itself: `epa_fit._scales` sets S4's residual scales from the view's R (PLAN.md 5.1: E1a's for efficiency, E3a's for TIT), so the fixture's 0.05 % and 20 K scaled efficiency's residuals 76 times larger against TIT's than PLAN.md 5.1's 1.9 % and 10 K do (about 5800 times in the cost). `RealT0OnSyntheticTables` now sets the synthetic contract's R to `T0_REHEARSAL_R`, the synthetic view test_epa_stats types for its hand answers (E1a 1.9 %, E2a 4.0 %, E3a 10 K, as PLAN.md 5.1 states the scales). Result (`CALIBRATE_EPA_SLOW=9`, 270 s; `fix4/realt0_b.log`, with each form's outcomes in `fix4/t0_summary_rehearsal.log`): **T0 passes**. Seed 1 stops at A, chi-square 9.40 on 13; seed 2 at A, 7.15 on 13; seed 3 at A+B, 16.46 on 14 (99 % upper bounds 29.82 and 31.32), its form A failing on E3a; the out-of-form seed is detected (5233.6); D1-D3's four cases hold; nothing outside the allowlist, nothing refused.
- (b) Why S4 and its polish stopped on xtol at an optimality near 260, on the fixture's R (the fixer's `fix4/s4_diag.py`, logs `fix4/s4_diag2_seed1.log` and `seed2.log`: form A, dtheta 0.25). On seed 2 the five starts end with status 2 or 3 (ftol or xtol at 1e-10) after 20 to 40 evaluations, at costs 1711.4 to 1731.6, the gradient in scale units 9.7 to 81.6 by the forward-difference Jacobian; the polish from the lowest accepts no step (status 4, two Jacobians, last step 1.7e-12), because no step it tries lowers the cost. Along the covariance's largest-variance direction the cost rises by 29.5 within 0.02 scale units on one side and stays between 1709.9 and 1713.4 over 0.6 on the other: a kink and a ripple of the crank-step cycle, not a quadratic, which the Jacobian's FD_CAD of 0.5 CAD spans as a secant. So the reported optimality and the covariance describe the secant. Seed 2's S4 chi-square there read 405.3 on 9 parameters by the covariance (the Wald form amendment D11 uses), 341 of it along the covariance's smallest-variance direction, and 12.8 by the likelihood ratio on the same objective and residual variance, 2 (cost(truth) - cost(fit)) / s^2 (99 % upper bound on 9: 23.6); seed 1, 15.4 and 17.2. At the rehearsal's scales (a) the same seed reads 7.15 in all, so this did not bind there. WP3 changed neither the solver nor the criterion.
- (c) For the team, before T0 runs at real inputs (after STARTED either is a defect-route code change): whether amendment D11's chi-square stays the Wald form, which a fit at a kink of the cycle can fail while the likelihood ratio passes (shown at the fixture's scales only), and whether S4 must reach a stated optimality, which the forward-difference gradient at a kink does not measure. A reading for the team as well: under decision 77 a gating statistic built on absolute values (D1) keeps a noise floor that u_stat does not remove (u_stat falls as 1/sqrt(n), the floor does not); on the real contract's D1 R (above 1 % on all three engines, the review's booleans) it does not bind at T0_NOISE. The rehearsal's pass is on synthetic tables and synthetic R; T0 at the real rows' inputs is Run 1's.

**The whole Run 1 on synthetic tables under the new seal** (`WholeRun1OnSyntheticTables`, `CALIBRATE_EPA_SLOW=9`): 1 test, OK, in 1478.5 s, run beside the T0 rehearsal (the fixer's scratch `fix4/wholerun.log`): fit, poison with its full form-A fit, e6, complete and check each exited 0 with nothing outside its allowlist, and every comparison of the poison's three runs was equal, so the sealed shapes do not stop a real Run 1's own git, pools or records.

**Left, with the reason** (not quick, or not WP3's to decide):
- `epa_rows.read_held_out` requiring the arming's nonce and the started marker (the leak review): the nonce's path and hash are validate_epa's (`nonce_path`, `nonce_matches`); epa_rows may not import validate_epa (§3.1), and a second definition would be mistake 10. The run-once rule stays in `validate_epa.refusals`, rule N2's scan confining the callers; for the team.
- An exclusive STARTED against two concurrent `validate_epa.py run` (the leak review): unchanged from §13, for the team.
- FS4, lam_floor bounding S3b's depth (the leak review): the team's (§12).
- The contract's kappa at most 1 for an untested d row, the in-sample E4b without a u_stat, E6 row 1's E8, and the u_D pins' cluster reading (the contract review): unchanged, as §11 and §13 list them; before Run 1 if the team settles them in a contract version.
- The D3 summary columns of the Honda and the Mazda (the contract and Run 1 reviews): a source read for whoever pins them; t0 and fit refuse on every engine until then. In the commit that pins them, the three tests that assert today's unpinned production state -- `test_calibrate_epa.Order.test_t0_and_fit_refuse_while_a_pin_is_open` (its D3 half), `Order.test_the_pins_guard_reads_every_engines_d3_columns`, and `test_validate_guards.ArmProofs.test_arm_refuses_while_a_pin_is_open` (`PRODUCTION_UNPINNED_FOR`) -- take a patched `d3_rows.unpinned_for` for their refusal half (the tests review).
- The Accord's D3 header lines checked at arm, before STARTED (the tests review): whether C5 allows reading them is the team's.
- A test's child process in the real tree is not guarded by the test audits (the tests review, optional): no child of the WP3 suites read an EPA table in the review's logged run.
- The remaining boundary cases of the tests review's operator sweep (censoring at exactly 1e-9, the tightening's tie of equal magnitudes, an exact grid end, u_num with one member, E8's without-censored reading): float-edge equivalents or report-only branches; not added.
- No commit while a fit runs (the Run 1 review): procedural, as §13 says.
- PLAN.md's WP4 block (the Run 1 review) is superseded by §13's procedure, which the code enforces (t0 and poison included, `check --jobs`); PLAN.md, a dated plan, is not edited. The worktree reproduction it lists (`git worktree add $S/repro HEAD && ... && cmp`) is not in §13's procedure: it costs a second Run 1 per engine, needs `EPA_RUN1_GO` again (STARTED is absent in a worktree), and must be made before commit D, or the worktree holds the records and t0 refuses; whether it is required is the team's to decide before Run 1.

## 15. The D3 pins (24 October 2026)

The pins §11, §13 and §14 left open, closed in the commit "build step 2: the D3 channel pins, from the catalogue" under decisions 78–81 (`results/VALIDATION_DECISIONS.md` section H, adopted under Ghassan's delegation of 21 October; Jad's column open). Each pin carries its source in `d3_rows.py` (`SummarySpec.sources`, `Channel.source`, `FuelDensity.source`), and every read is in `d3_rows.SOURCES_READ`, and so in `calibrate_epa.SEEN_BEFORE_THE_FIT`. No D3 trace file was opened and no summary result value was read.

- **The summary columns** (decision 78, the header row of each workbook read): on both sheets `Test ID [#]`, `Cycle`, `Test Cell Temp [C]`, `Fuel used modal [gal]` and `Fuel Heating Value\n[BTU/lbm]` (a line break inside the cell), the heating value's factor 1.0. The heating value is a column of each row, not a cell at the sheet's top.
- **The modal fuel's grams** (decision 79): the gallons times an ASSUMED density, the midpoint of the union of six NVFEL-measured certification test fuels' densities (`D3_FUEL_DENSITIES`: three Tier 2, three Tier 3), half the union's width a uniform half-width whose u enters the Direct2 check's u_D (`channel_checks`, `ChannelChecks.u_modal_fuel`).
- **The rows** (decision 80): a test's values come from its base phase rows, its sum rows (`Ph 1+2`, `p3+4`) excluded (`sum_row`); a row whose test ID is not a number, and every row of a test the chain does not read, is skipped unconverted. `read_summary` takes the chain's tests (`tests`, no default), and `validate_epa._d3_chain` passes its files' IDs.
- **The Accord's channels** (decision 81): the converter-lock and A/C rules applied with `Trans_torque_converter_turbine_spd_AT__rpm` and `HVAC_AC_clutch_PGM`; `Time[s]_RawFacilities` and `Dyno_Spd__mph` pinned from the catalogue's column list.
- **The tests**: `test_d3_rows.Summary` (the pins and their sources, decision 80's rows, the density), `Checks.test_the_modal_fuels_density_u_enters_the_fuels_u_d` and `Segments.test_the_accords_converter_and_ac_rules_cut`. The three tests §14 named now assert the production state pinned and take a patched `d3_rows.unpinned_for` for their refusal half. Each of fourteen mutations of the new rules (the scratchpad's `d3pin5_scripts/mut_d3pins.py`) fails `test_d3_rows`.

With every pin set, `calibrate_epa.py t0` and `fit` no longer refuse at the pins guard; Run 1 still waits for `EPA_RUN1_GO` naming the engine.

## 16. After Run 1's first pass: defect D-1 and decisions 82–85 (29 October 2026)

Run 1's first pass (24 October 2026) froze the Mazda at A+B+C+D and stopped the Honda at T0 (`d2_gate`, seed 1); the Ford did not start. A read-only defect hunt found the Mazda's misses to be the model's form, and found D-1 and F-1 below. Ghassan answered on 29 October 2026 (`results/VALIDATION_DECISIONS.md` section H, decisions 82–85, and the notes on D-1 and the disclosure there). Contract version 5 does not change (rule 0): none of 82–85 is a contract rule. No held-out row was read, and `validate_epa.py run` was not run.

- **D-1, a coding defect in `calibrate_epa.valve_brackets`** (E6 row 9's brackets; the completion only): the Mazda's IVC and EVO got no bracket, for a reason that was false (that the Atkinson ratio is one of two effective compression ratios and the cam phases shifts from a base nobody can recover). EPA's ratio is the effective expansion stroke over the effective compression stroke, x(EVO0 + exhaust cam)/x(−(IVC0 + intake cam)), and its own rows recover the base timing exactly. The fix (`atkinson_events`, `ATKINSON_*`, `CAM_SIGN`): when the rows carry the ratio and both phases, least squares of IVC0, EVO0 and the rod over the half stroke from 27 starts, accepted only for an exact fit (largest |residual| below 1e-9, every exact start at one solution, the Jacobian of full rank, at least four distinct cam pairs); IVC is bracketed by IVC0 + the intake cam's range, EVO by EVO0 + the exhaust cam's; anything else gives no bracket with the reason. On the Mazda's 199 calibration steady and Final rows it gives IVC0 −80.000°, EVO0 120.000°, a rod of 3.684 half strokes, a largest residual of 2.0e-15, all 27 starts exact, and the brackets IVC [−154.27, −80.30]° and EVO [119.82, 168.61]° aTDC; the Honda's strokes and the Ford's phases-only reason are unchanged in what they give (`test_calibrate_epa.Pieces.test_valve_brackets_from_the_atkinson_ratio`, whose rows HEAD's code bracketed not at all, with three controls). `freeze.json` pins `calibrate_epa.py`, so the fix takes the defect route of §5.5.2: committed alone, then `fit --defect "<reason>" --fix-commit <sha>` on the Mazda, which moves the first outputs to `defect_1/`, appends to `defects.json` and re-runs from T0.
- **Decision 84, T0's `d2_gate` case widened to the data's resolution** (`epa_fit.d2_gate_case`, `D2_GATE_RULE`; `test_epa_fit.S3b.test_d2_gate_case_is_widened_to_the_neighbouring_final_rows`, and the T0 judge's test reading it through `t0_cases`): the case passes when the truth's gate lies within the fitted flat interval widened to the MAPs of the neighbouring calibration Final rows -- down to the highest Final MAP at or below the interval, up to the lowest above it, a side with no such row not widened -- or, as before, within the grid's 1 kPa of the interval. The detail records the widened interval, both neighbours and which reading held. For all three engines; a test fix, logged by the defect route (`t0 --defect`, `defects.json`); every engine's T0 re-runs on the final code. Read as written it does not reach below the lowest calibration Final row, so a seed whose fitted interval lies at or above that row while the truth lies below it still fails (the test's Honda-shaped control). The first pass's Honda seed 1 is such a seed, and its T0 rows and fit do not change: T0 places the truth's gate (123.43 kPa) between the highest steady MAP below the lowest Final MAP and that Final MAP, which the first pass's flat intervals put in (123.43, 124.86) kPa, below seed 1's interval [125, 125]; so its widened lower end is a Final MAP above the truth, and its d2_gate case fails again under decision 84 as worded. A wording that passes it reaches the truth's own interval below the lowest Final row (down to the highest steady MAP below it); that is the team's to choose.
- **Decision 83, the steady-only TIT reading** (F-1: Final and steady TIT are not the same temperature, mistake 23; `epa_stats.STEADY_TIT_ROWS`, `STEADY_TIT_READING`, `steady_tit_evals`, `steady_tit_reading`, `steady_tit_json`, `InSample.steady_tit`; `test_epa_stats.SteadyOnlyTit`, `test_calibrate_epa.Records.test_fit_writes_its_records_and_the_freeze`, `test_validate_guards.HeldOutRun.test_the_whole_run_writes_every_row_and_every_E6_row`, `SummaryOfThree`): declared before any held-out statistic. E3a, E4a, L0 and L1 with the High Load Final rows left out, and E4b with the Final rows left out of its reference line (its boosted lambda~1 rows; its enriched rows kept), by the same row functions, beside the primary (the contract's pooled hot population), which it never replaces. In-sample: `epa_stats.in_sample` attaches it to each form's `InSample`, and `in_sample.json` carries it per form as `steady_only_tit` (`reading`, `decides: false`, `rows`, `statistics`, each with its decision 77 judgement); the form's `passes`, `failing`, `noise` and `no_line`, the ladder and the freeze read the primary alone. Run 2: `validate_epa._Evals.steady_tit` labels each row with its u-terms from the same perturbed evaluations, `rows.json` carries it as `steady_only_tit`, and `summary.json` each engine's labels and E beside the primary's; section 7, `reported` and every label that decides are the primary's. E4a's population is the enriched hot rows, which are Final rows on these engines, so its steady-only reading may have no statistic, reported with its reason.
- **Decision 85, a probe below its numerical noise is not visible at R1** (`calibrate_epa.NOT_VISIBLE_AT_R1`, `NOISE_RULE`, `numerical_noise_k`, `probe_sizes(..., noise_k=)`; `epa_coefficients.median_resolution`, `climb_cell_resolution`; `validate_epa.not_visible_at_r1`, `level_exclusion`; `test_calibrate_epa.Pieces.test_a_probe_below_the_numerical_noise_is_not_visible_at_r1`, `Records.test_e6_complete_and_check`, `test_epa_coefficients.B58.test_the_climb_cells_resolution`, `MedianResolution`, `test_validate_guards.NotVisibleAtR1` and `HeldOutRun`): the numerical noise is measured, not typed. The climb cell is a median over `CLIMB_S`; a change smaller than the median's resolution (the gap to the next order statistic) may only reorder samples around it, so the noise of a probe's housing response is the housing equivalent of the gas's and the flow's resolutions at the frozen plant's climb (one more climb in the completion's pool, its medians checked equal to the coefficients' climb point), and a probe without a bracket is visible only when |h(+) - h(-)|/2 exceeds it. Otherwise it is reported not visible at R1, takes the contract's +-10 % (+-10 CAD for IVC and EVO), has no worth R1, and is `counted_excluded`, which `validate_epa`'s rows 5, 6 and 9 read to count it excluded for the level rows with its reason (its probe still run and reported; the d rows judged under the d probe as before). `complete.json`'s `e6_probes` gains `numerical_noise` and `not_visible_at_r1`, and each probe record `response_k`, `numerical_noise_k`, `visible_at_r1`, `not_visible_at_r1`, `worth_r1_why`, `counted_excluded` and `counted_excluded_why`. On the first pass's Mazda (the frozen plant's climb, model outputs only) the noise is 1.82e-4 K (the gas's resolution 1.33e-4 K, the flow's 9.6e-5 g/s): `exh_bp_min_kpa` (0.25 times the noise) and the four constants the climb does not see (`flame_floor`, `fres_map_min`, `fres_lo`, `fres_hi`, 0) are not visible; `ce_rich_slope` is visible by 2 % (1.02 times the noise), so it keeps its probe sized by R1, which the first pass put at 2.3e3 per unit on a slope of 0.43; every other probe is at least 2400 times the noise.
